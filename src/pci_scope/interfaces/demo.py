"""The lesson's scenario against real local servers, ending in the evidence pack.

1. The naive checkout takes a test payment and logs the card number: the problem, measured.
2. The redesigned checkout takes a test payment through the provider's hosted fields: the card goes only there.
3. A repeat charge from tokens, a refund and a webhook, to show the merchant needs no card for any of them.
4. The merchant's log, database and backup are scanned, the old route is probed, and everything is written to the pack.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from pci_scope.application.checkout import CheckoutService
from pci_scope.application.pack import (
    render_index,
    render_page_controls,
    render_routes,
    render_token_storage,
    scope_documents,
)
from pci_scope.application.proof import ScanOutcome, run_scan
from pci_scope.domain.har import summarize, to_har
from pci_scope.infrastructure.artifacts import MerchantArtifacts, NaiveArtifacts
from pci_scope.infrastructure.catalog import load_inventory, load_requirements
from pci_scope.infrastructure.evidence_store import FileEvidenceStore
from pci_scope.infrastructure.provider_http import HttpProvider
from pci_scope.infrastructure.settings import Settings
from pci_scope.infrastructure.sqlite_orders import SqliteOrders
from pci_scope.interfaces.browser_sim import Browser, PaymentRun, pay_on_naive_checkout, pay_with_hosted_fields
from pci_scope.interfaces.merchant_app import create_merchant_app
from pci_scope.interfaces.naive_app import create_naive_app
from pci_scope.interfaces.provider_app import ProviderState, create_provider_app
from pci_scope.interfaces.servers import LocalServer

GREP_PAN = r"4242[ -]?4242[ -]?4242[ -]?4242"
GREP_FIELDS = "cvv|cvc|card_number"


@dataclass(frozen=True)
class DemoResult:
    """What the scenario produced, for the command line to report."""

    before: ScanOutcome
    after: ScanOutcome
    run: PaymentRun
    order_statuses: dict[str, str]
    pack_files: tuple[str, ...]


def _port(url: str) -> int:
    return urlsplit(url).port or 80


def run_demo(settings: Settings, root: Path = Path()) -> DemoResult:
    """Run the whole scenario and write the evidence pack to `settings.evidence_dir`."""
    state = settings.state_dir
    shutil.rmtree(state, ignore_errors=True)
    shutil.rmtree(settings.evidence_dir, ignore_errors=True)
    (state / "merchant").mkdir(parents=True)
    (state / "backups").mkdir()
    app_log = state / "merchant" / "app.log"
    handler = logging.FileHandler(app_log, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    merchant_logger = logging.getLogger("merchant")
    merchant_logger.setLevel(logging.INFO)
    merchant_logger.handlers[:] = [handler]
    merchant_logger.propagate = False

    orders = SqliteOrders(settings.database_path)
    orders.initialize((root / "sql" / "001_schema.sql").read_text(encoding="utf-8"))
    provider_state = ProviderState(
        settings.secret_key, settings.publishable_key, settings.webhook_secret, f"{settings.merchant_base_url}/webhook"
    )
    checkout = CheckoutService(
        HttpProvider(settings.provider_base_url, settings.secret_key), orders, settings.webhook_secret
    )
    provider_app = create_provider_app(provider_state)
    merchant_app = create_merchant_app(checkout, settings.provider_public_url, settings.publishable_key)
    naive_app = create_naive_app(settings.naive_log_path)

    try:
        with (
            LocalServer(provider_app, _port(settings.provider_base_url)),
            LocalServer(merchant_app, _port(settings.merchant_base_url)),
            LocalServer(naive_app, _port(settings.naive_base_url)),
        ):
            pay_on_naive_checkout(Browser(), settings.naive_base_url)
            browser = Browser()
            run = pay_with_hosted_fields(
                browser, settings.merchant_base_url, settings.provider_base_url, settings.publishable_key
            )
            again = json.loads(
                Browser()
                .request(
                    "POST", f"{settings.merchant_base_url}/charge-again", payload={"payment_intent": run.intent_id}
                )
                .body
            )
            Browser().request(
                "POST", f"{settings.merchant_base_url}/refund", payload={"payment_intent": again["payment_intent"]}
            )
            probe = Browser()
            routes = [
                ("POST", "/pay", probe.request("POST", f"{settings.merchant_base_url}/pay").status),
                ("GET", "/pay", probe.request("GET", f"{settings.merchant_base_url}/pay").status),
            ]
    finally:
        handler.close()

    (state / "backups" / "merchant-backup.sql").write_text(orders.dump(), encoding="utf-8")
    before = run_scan("scanning the naive checkout after one test payment:", NaiveArtifacts(settings.naive_log_path))
    artifacts = MerchantArtifacts(state, orders.dump, settings.database_path, skip=("naive",))
    after = run_scan("scanning the merchant's side after the same payment, a repeat charge and a refund:", artifacts)
    statuses: dict[str, str] = {}
    for intent_id in (run.intent_id, again["payment_intent"]):
        found = orders.find(intent_id)
        if found is not None:
            statuses[intent_id] = found.status
    _write_pack(settings, run, before, after, routes, orders, root)
    return DemoResult(
        before, after, run, statuses, tuple(sorted(path.name for path in settings.evidence_dir.iterdir()))
    )


def _grep(label: str, pattern: str, ignore_case: bool, paths: list[Path]) -> str:
    command = ["grep", "-rnaE", *(["-i"] if ignore_case else []), pattern, *map(str, paths)]
    done = subprocess.run(command, capture_output=True, text=True, check=False, timeout=60)
    shown = f"$ grep -rnaE{' -i' if ignore_case else ''} '{pattern}' {' '.join(path.name for path in paths)}"
    return f"{shown}\n{'' if done.returncode == 1 else done.stdout}exit={done.returncode}  ({label})\n"


def _write_pack(
    settings: Settings,
    run: PaymentRun,
    before: ScanOutcome,
    after: ScanOutcome,
    routes: list[tuple[str, str, int]],
    orders: SqliteOrders,
    root: Path,
) -> None:
    store = FileEvidenceStore(settings.evidence_dir)
    now = datetime.now(UTC)
    inventories = scope_documents(
        load_inventory(root / "scope" / "before.toml"), load_inventory(root / "scope" / "after.toml")
    )
    for name, text in inventories.items():
        store.write(name, text, "P3", now)
    store.write("proof-before.txt", before.text, "P4", now)
    merchant_paths = [settings.database_path, settings.state_dir / "merchant", settings.state_dir / "backups"]
    greps = _grep("no card number found", GREP_PAN, False, merchant_paths) + _grep(
        "no card field found", GREP_FIELDS, True, merchant_paths
    )
    store.write(
        "proof-after.txt",
        after.text
        + "\nthe lesson's own checks, on the same places (grep exits 1 when nothing is found; -a reads SQLite too):\n"
        + greps,
        "P1",
        now,
    )
    redact = frozenset({settings.provider_base_url})
    store.write("payment.har", to_har(run.exchanges, redact), "P1", now)
    store.write(
        "payment-summary.txt",
        summarize(run.exchanges, settings.merchant_base_url, settings.provider_base_url),
        "P1",
        now,
    )
    store.write("route-check.txt", render_routes(routes), "P2", now)
    digit_columns = [
        name
        for name, kind in orders.columns()
        if kind.upper() in ("REAL",) or name in ("card_number", "cvv", "cvc", "pan")
    ]
    store.write("token-storage.txt", render_token_storage(orders.columns(), orders.rows(), digit_columns), "P5", now)
    store.write(
        "checkout-page-controls.txt",
        render_page_controls(
            f"{settings.merchant_base_url}/",
            200,
            run.page_headers,
            run.scripts,
            settings.provider_base_url,
            run.page_card_fields,
        ),
        "P6",
        now,
    )
    for name, requirement in (("responsibilities.md", "P6"), ("provider-attestation.md", "P7")):
        store.write(
            name,
            (root / "docs" / name).read_text(encoding="utf-8"),
            requirement,
            now,
        )
    requirements, gaps = load_requirements(root / "controls" / "requirements.toml")
    store.write("INDEX.md", render_index(requirements, store.manifest(), gaps, now), "-", now)
