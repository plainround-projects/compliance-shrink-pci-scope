import json
import socket
import sqlite3
import threading
from contextlib import closing
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from pci_scope.domain.card import TEST_CARD
from pci_scope.domain.payment import PaymentError
from pci_scope.infrastructure.artifacts import MerchantArtifacts, NaiveArtifacts, PathArtifacts
from pci_scope.infrastructure.catalog import CatalogError, load_inventory, load_requirements
from pci_scope.infrastructure.evidence_store import FileEvidenceStore
from pci_scope.infrastructure.logging_setup import JsonFormatter
from pci_scope.infrastructure.provider_http import HttpProvider
from pci_scope.infrastructure.settings import SettingsError, load_settings
from pci_scope.infrastructure.sqlite_orders import SqliteOrders
from pci_scope.interfaces.provider_app import ProviderState, create_provider_app
from pci_scope.interfaces.servers import LocalServer, free_port
from tests.conftest import REPOSITORY_ROOT

ENV = {
    "PROVIDER_BASE_URL": "http://127.0.0.1:5001/",
    "PROVIDER_SECRET_KEY": "sk_test_abc",
    "PROVIDER_PUBLISHABLE_KEY": "pk_test_abc",
    "WEBHOOK_SECRET": "w" * 32,
    "MERCHANT_BASE_URL": "http://127.0.0.1:5000",
}


def test_settings_strip_trailing_slashes_and_apply_defaults():
    settings = load_settings(ENV)
    assert settings.provider_base_url == "http://127.0.0.1:5001"
    assert settings.naive_base_url == "http://127.0.0.1:5002"
    assert str(settings.database_path) == "state/merchant.db"


@pytest.mark.parametrize(
    "env",
    [
        {},
        {**ENV, "PROVIDER_SECRET_KEY": "sk_live_abc"},
        {**ENV, "PROVIDER_PUBLISHABLE_KEY": "pk_live_abc"},
        {**ENV, "WEBHOOK_SECRET": "short"},
        {**ENV, "LOG_LEVEL": "LOUD"},
        {key: value for key, value in ENV.items() if key != "MERCHANT_BASE_URL"},
    ],
)
def test_live_keys_and_missing_values_are_refused(env):
    with pytest.raises(SettingsError):
        load_settings(env)


def test_the_order_table_holds_tokens_and_refuses_a_card_number(tmp_path):
    orders = SqliteOrders(tmp_path / "m.db")
    orders.initialize((REPOSITORY_ROOT / "sql" / "001_schema.sql").read_text())
    created = orders.create("pi_" + "a" * 24, 1900, "eur", "cus_" + "b" * 24)
    assert (created.status, created.id) == ("pending", 1)
    orders.update(created.payment_intent_id, "succeeded", "pm_" + "c" * 24)
    found = orders.find(created.payment_intent_id)
    assert found is not None
    assert (found.status, found.payment_method_id) == ("succeeded", "pm_" + "c" * 24)
    assert orders.find("pi_" + "z" * 24) is None
    with pytest.raises(sqlite3.IntegrityError):
        orders.update(created.payment_intent_id, "succeeded", TEST_CARD)
    with pytest.raises(sqlite3.IntegrityError):
        orders.create(TEST_CARD, 1900, "eur", "")
    with pytest.raises(ValueError, match="unknown status"):
        orders.update(created.payment_intent_id, "paid-ish", "")


def test_the_order_table_reports_its_columns_rows_and_dump(tmp_path):
    orders = SqliteOrders(tmp_path / "m.db")
    orders.initialize(
        (REPOSITORY_ROOT / "sql" / "001_schema.sql").read_text()
        + (REPOSITORY_ROOT / "sql" / "002_seed.sql").read_text()
    )
    names = [name for name, _ in orders.columns()]
    assert names[:3] == ["id", "payment_intent_id", "amount_cents"]
    assert names[-2:] == ["payment_method_id", "created_at"]
    assert len(orders.rows()) == 2
    assert "pm_0123456789abcdef01234567" in orders.dump()


def test_the_merchant_artifacts_cover_logs_backups_and_the_database_dump_but_skip_named_folders(tmp_path):
    (tmp_path / "merchant").mkdir()
    (tmp_path / "merchant" / "app.log").write_text("created payment")
    (tmp_path / "backups").mkdir()
    (tmp_path / "backups" / "b.sql").write_text("INSERT")
    (tmp_path / "naive").mkdir()
    (tmp_path / "naive" / "requests.log").write_text(TEST_CARD)
    (tmp_path / "m.db").write_bytes(b"binary")
    names = [
        name for name, _ in MerchantArtifacts(tmp_path, lambda: "DUMP", tmp_path / "m.db", skip=("naive",)).artifacts()
    ]
    assert names == ["m.db (SQL dump)", "backups/b.sql", "merchant/app.log"]
    assert "naive/requests.log" in [name for name, _ in MerchantArtifacts(tmp_path).artifacts()]


def test_the_naive_and_path_artifacts(tmp_path):
    log = tmp_path / "requests.log"
    assert list(NaiveArtifacts(log).artifacts()) == []
    log.write_text("x")
    assert list(NaiveArtifacts(log).artifacts()) == [("requests.log", "x")]
    folder = tmp_path / "f"
    folder.mkdir()
    (folder / "a.txt").write_text("a")
    assert [text for _, text in PathArtifacts([folder, log]).artifacts()] == ["a", "x"]


def test_the_evidence_store_writes_reads_and_records_hashes(tmp_path):
    from datetime import UTC, datetime

    store = FileEvidenceStore(tmp_path / "evidence")
    now = datetime(2026, 10, 27, tzinfo=UTC)
    store.write("a.txt", "hello\n", "P1", now)
    assert store.read_all() == {"a.txt": "hello\n", "manifest.json": store.read_all()["manifest.json"]}
    entry = store.manifest()["a.txt"]
    assert (entry.requirement, entry.produced_at, len(entry.sha256)) == ("P1", now, 64)
    assert FileEvidenceStore(tmp_path / "none").read_all() == {}
    with pytest.raises(ValueError, match="directly in"):
        store.write("../x", "x", "P1", now)


def test_the_catalogs_load_and_reject_bad_files(tmp_path):
    assert len(load_inventory(REPOSITORY_ROOT / "scope" / "before.toml").systems) == 10
    requirements, gaps = load_requirements(REPOSITORY_ROOT / "controls" / "requirements.toml")
    assert [r.id for r in requirements] == ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]
    assert gaps[0].requirement == "P7"
    assert gaps[0].due is not None
    bad = tmp_path / "bad.toml"
    bad.write_text(
        'title = "x"\n[[system]]\nid = "a"\nname = "A"\nteam = "t"\n[[edge]]\nfrom = "a"\nto = "ghost"\nkind = "data"\n'
    )
    with pytest.raises(CatalogError, match="bad edge"):
        load_inventory(bad)
    bad.write_text("[[system]]\nid = 'a'\n")
    with pytest.raises(CatalogError, match="missing"):
        load_inventory(bad)
    with pytest.raises(CatalogError):
        load_requirements(tmp_path / "nothing.toml")


def test_the_json_formatter_keeps_only_whitelisted_fields():
    import logging

    record = logging.LogRecord("merchant", logging.INFO, "f", 1, "payment %s", ("pi_x",), None)
    record.status = 200
    record.card_number = "never"
    document = json.loads(JsonFormatter().format(record))
    assert document["message"] == "payment pi_x"
    assert document["status"] == 200
    assert "card_number" not in document


@pytest.fixture
def provider():
    state = ProviderState(
        "sk_test_abc", "pk_test_abc", "w" * 32, "http://127.0.0.1:1/webhook", deliver=lambda url, body, sig: None
    )
    with LocalServer(create_provider_app(state), free_port()) as server:
        yield server.url, state


def test_the_http_provider_creates_charges_and_refunds_against_the_stand_in(provider):
    url, state = provider
    client = HttpProvider(url, "sk_test_abc")
    customer = client.create_customer()
    intent = client.create_intent(1900, "eur", customer, save_card=True)
    assert (intent.status, intent.amount_cents, intent.customer_id) == ("requires_payment_method", 1900, customer)
    assert intent.client_secret.startswith(intent.id + "_secret_")
    assert client.retrieve_intent(intent.id).id == intent.id
    state.methods["pm_" + "a" * 24] = {"brand": "visa", "last4": "4242", "decline": False}
    again = client.charge_saved(customer, "pm_" + "a" * 24, 1900, "eur")
    assert again.status == "succeeded"
    assert client.refund(again.id).startswith("re_")


def test_a_4xx_is_the_providers_message_and_a_wrong_key_is_refused(provider):
    url, _ = provider
    with pytest.raises(PaymentError, match="Invalid secret key"):
        HttpProvider(url, "sk_test_wrong").create_customer()
    with pytest.raises(PaymentError, match="No such payment_intent"):
        HttpProvider(url, "sk_test_abc").retrieve_intent("pi_" + "0" * 24)
    with pytest.raises(PaymentError, match="only a succeeded payment"):
        HttpProvider(url, "sk_test_abc").refund("pi_" + "0" * 24)


def test_a_server_that_fails_is_retried_then_reported_and_an_unreachable_one_too():
    hits: list[int] = []

    class Failing(BaseHTTPRequestHandler):
        def do_POST(self):
            hits.append(1)
            self.send_response(503)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Failing)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    sleeps: list[float] = []
    try:
        with pytest.raises(PaymentError, match="failing"):
            HttpProvider(f"http://127.0.0.1:{server.server_port}", "sk_test_abc", sleep=sleeps.append).create_customer()
    finally:
        server.shutdown()
        server.server_close()
    assert len(hits) == 3
    assert sleeps == [0.2, 0.4]
    with pytest.raises(PaymentError, match="unreachable"):
        HttpProvider("http://127.0.0.1:1", "sk_test_abc", timeout=1, sleep=lambda s: None).create_customer()


def test_a_local_server_stops_when_the_context_exits():
    from flask import Flask

    app = Flask(__name__)
    port = free_port()
    with LocalServer(app, port) as server:
        assert server.url == f"http://127.0.0.1:{port}"
    with closing(socket.socket()) as probe:
        assert probe.connect_ex(("127.0.0.1", port)) != 0
