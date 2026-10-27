"""The lesson's scenario against real local servers: the naive checkout, the redesign, the proof and the pack."""

from __future__ import annotations

import json
import shutil

import pytest

from pci_scope.domain.card import TEST_CARD
from pci_scope.infrastructure.settings import load_settings
from pci_scope.interfaces.cli import main
from pci_scope.interfaces.demo import run_demo
from pci_scope.interfaces.servers import free_port
from tests.conftest import REPOSITORY_ROOT

pytestmark = pytest.mark.e2e


@pytest.fixture
def settings(tmp_path):
    ports = [free_port() for _ in range(3)]
    env = {
        "PROVIDER_BASE_URL": f"http://127.0.0.1:{ports[0]}",
        "PROVIDER_SECRET_KEY": "sk_test_e2e",
        "PROVIDER_PUBLISHABLE_KEY": "pk_test_e2e",
        "WEBHOOK_SECRET": "w" * 32,
        "MERCHANT_BASE_URL": f"http://127.0.0.1:{ports[1]}",
        "NAIVE_BASE_URL": f"http://127.0.0.1:{ports[2]}",
        "DATABASE_PATH": str(tmp_path / "state" / "merchant.db"),
        "NAIVE_LOG_PATH": str(tmp_path / "state" / "naive" / "requests.log"),
        "STATE_DIR": str(tmp_path / "state"),
        "EVIDENCE_DIR": str(tmp_path / "evidence"),
    }
    return load_settings(env), env


def test_the_lessons_scenario_end_to_end(settings, monkeypatch, capsys):
    loaded, env = settings
    result = run_demo(loaded, REPOSITORY_ROOT)

    # Done when 1 and the problem: the naive checkout puts the card in its log.
    assert result.before.exit_code == 1
    assert "FOUND card number 424242******4242" in result.before.text

    # Done when 2: a test payment succeeds and the merchant's log, database and backup hold tokens only.
    assert result.run.final_status == 200
    assert result.run.final_text == f"payment {result.run.intent_id}: succeeded"
    assert result.after.exit_code == 0
    assert result.after.artifacts == 3
    assert set(result.order_statuses.values()) == {"succeeded", "refunded"}

    # Done when 3: the capture shows the card fields went to the provider only.
    pack = loaded.evidence_dir
    har = json.loads((pack / "payment.har").read_text())["log"]["entries"]
    to_merchant = [e for e in har if e["request"]["url"].startswith(loaded.merchant_base_url)]
    to_provider = [e for e in har if e["request"]["url"].startswith(loaded.provider_base_url)]
    assert to_merchant
    assert not any("card" in e["request"]["postData"]["text"].lower() for e in to_merchant)
    assert any("card%5Bnumber%5D=[redacted]" in e["request"]["postData"]["text"] for e in to_provider)
    assert TEST_CARD not in (pack / "payment.har").read_text()

    # Done when 5: the scope shrank, and the page and its pipeline stay in scope.
    change = (pack / "scope-change.md").read_text()
    assert "Before: 9 systems and 3 teams in scope." in change
    assert "After: 3 systems and 2 teams in scope." in change

    # The pack verifies; a hand edit and a card in the capture are caught.
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    assert main(["verify"]) == 0
    capsys.readouterr()
    (pack / "route-check.txt").write_text("edited by hand\n")
    assert main(["verify"]) == 1
    assert "EVP003" in capsys.readouterr().out


def test_a_card_sent_to_the_merchant_makes_the_capture_fail_verification(settings, monkeypatch, capsys):
    loaded, env = settings
    run_demo(loaded, REPOSITORY_ROOT)
    pack = loaded.evidence_dir
    har = json.loads((pack / "payment.har").read_text())
    har["log"]["entries"][0]["request"]["postData"]["text"] = "card_number=4242424242424242"
    tampered = json.dumps(har)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    shutil.copy(pack / "manifest.json", pack / "manifest.bak")
    (pack / "payment.har").write_text(tampered)
    manifest = json.loads((pack / "manifest.json").read_text())
    from pci_scope.domain.evidence import digest

    manifest["payment.har"]["sha256"] = digest(tampered)
    (pack / "manifest.json").write_text(json.dumps(manifest))
    (pack / "manifest.bak").unlink()
    assert main(["verify"]) == 1
    assert "carries card data" in capsys.readouterr().out
