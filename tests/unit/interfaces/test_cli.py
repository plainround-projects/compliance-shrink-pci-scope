import pytest

from pci_scope.domain.card import TEST_CARD
from pci_scope.interfaces.cli import build_parser, main

ENV = {
    "PROVIDER_BASE_URL": "http://127.0.0.1:5001",
    "PROVIDER_SECRET_KEY": "sk_test_abc",
    "PROVIDER_PUBLISHABLE_KEY": "pk_test_abc",
    "WEBHOOK_SECRET": "w" * 32,
    "MERCHANT_BASE_URL": "http://127.0.0.1:5000",
}


@pytest.fixture
def env(monkeypatch, tmp_path):
    for name, value in ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("EVIDENCE_DIR", str(tmp_path / "evidence"))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "m.db"))
    monkeypatch.setenv("STATE_DIR", str(tmp_path / "state"))
    return tmp_path


def test_every_job_has_a_subcommand():
    parser = build_parser()
    for command in ("demo", "verify", "scope", "db"):
        assert parser.parse_args([command]).command == command
    assert parser.parse_args(["scan", "a", "b"]).paths[1].name == "b"
    assert parser.parse_args(["serve", "provider"]).app == "provider"


def test_a_live_key_exits_2(env, monkeypatch, capsys):
    monkeypatch.setenv("PROVIDER_SECRET_KEY", "sk_live_abc")
    assert main(["scope"]) == 2
    assert "test-mode keys" in capsys.readouterr().err


def test_the_scope_command_prints_both_inventories_and_the_change(env, capsys):
    assert main(["scope"]) == 0
    out = capsys.readouterr().out
    assert "**9 systems and 3 teams in scope**" in out
    assert "**3 systems and 2 teams in scope**" in out
    assert "== scope-change.md" in out


def test_the_scan_command_exits_1_when_a_card_is_in_a_file_and_0_when_it_is_not(env, capsys):
    dirty, clean = env / "dirty.log", env / "clean.log"
    dirty.write_text(f"payment request: {TEST_CARD}\n")
    clean.write_text("created payment pi_x\n")
    assert main(["scan", str(clean)]) == 0
    assert main(["scan", str(dirty), str(clean)]) == 1
    out = capsys.readouterr().out
    assert "FOUND card number 424242******4242" in out
    assert TEST_CARD not in out


def test_the_db_command_creates_the_database_with_the_seed(env, capsys):
    assert main(["db"]) == 0
    assert (env / "m.db").is_file()
    assert "created" in capsys.readouterr().out


def test_verify_without_a_pack_fails_with_every_file_missing(env, capsys):
    assert main(["verify"]) == 1
    out = capsys.readouterr().out
    assert "EVP002 P1 payment.har" in out
    assert out.strip().splitlines()[-1].startswith("FAILED: 7 requirements, 0 files")
