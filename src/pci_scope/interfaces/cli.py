"""`pci-scope`: the scenario, the scope, the scanner, the verification. Exit codes: 0 ok, 1 findings, 2 bad input."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import urlsplit

from werkzeug.serving import run_simple

from pci_scope.application.checkout import CheckoutService
from pci_scope.application.pack import scope_documents
from pci_scope.application.proof import run_scan
from pci_scope.domain.evidence import verify_pack
from pci_scope.infrastructure.artifacts import PathArtifacts
from pci_scope.infrastructure.catalog import CatalogError, load_inventory, load_requirements
from pci_scope.infrastructure.evidence_store import FileEvidenceStore
from pci_scope.infrastructure.logging_setup import configure_logging
from pci_scope.infrastructure.provider_http import HttpProvider
from pci_scope.infrastructure.settings import Settings, SettingsError, load_settings
from pci_scope.infrastructure.sqlite_orders import SqliteOrders
from pci_scope.interfaces.demo import run_demo
from pci_scope.interfaces.merchant_app import create_merchant_app
from pci_scope.interfaces.naive_app import create_naive_app
from pci_scope.interfaces.provider_app import ProviderState, create_provider_app

ROOT = Path()


def build_parser() -> argparse.ArgumentParser:
    """One subcommand per job."""
    parser = argparse.ArgumentParser(prog="pci-scope", description="Shrink the PCI scope of a checkout and prove it.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="run the whole scenario and write the evidence pack")
    commands.add_parser(
        "verify", help="check that every requirement maps to evidence and every file says what it should"
    )
    commands.add_parser("scope", help="print the scope before and after, and what changed")
    scan = commands.add_parser(
        "scan", help="search files and folders for card numbers and card fields; exit 1 if any are found"
    )
    scan.add_argument("paths", nargs="+", type=Path)
    serve = commands.add_parser("serve", help="run one app on its configured port")
    serve.add_argument("app", choices=("provider", "merchant", "naive"))
    commands.add_parser("db", help="create the merchant's database from sql/001_schema.sql and 002_seed.sql")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run one command and return the exit code."""
    args = build_parser().parse_args(argv)
    try:
        settings = load_settings(os.environ)
        configure_logging(settings.log_level)
        return _run(args, settings)
    except (SettingsError, CatalogError) as problem:
        print(f"configuration error: {problem}", file=sys.stderr)
        return 2
    except OSError as problem:
        print(f"error: {problem}", file=sys.stderr)
        return 2


def _run(args: argparse.Namespace, settings: Settings) -> int:
    if args.command == "demo":
        result = run_demo(settings, ROOT)
        print(result.before.text, end="")
        print(result.after.text, end="")
        print(f"order statuses: {result.order_statuses}")
        print(f"evidence pack: {', '.join(result.pack_files)}")
        return _verify(settings)
    if args.command == "verify":
        return _verify(settings)
    if args.command == "scope":
        before, after = load_inventory(ROOT / "scope" / "before.toml"), load_inventory(ROOT / "scope" / "after.toml")
        for name, text in scope_documents(before, after).items():
            print(f"== {name}\n{text}")
        return 0
    if args.command == "scan":
        outcome = run_scan("scanning:", PathArtifacts(args.paths))
        print(outcome.text, end="")
        return outcome.exit_code
    if args.command == "db":
        orders = SqliteOrders(settings.database_path)
        schema = (ROOT / "sql" / "001_schema.sql").read_text(encoding="utf-8")
        orders.initialize(schema + (ROOT / "sql" / "002_seed.sql").read_text(encoding="utf-8"))
        print(f"created {settings.database_path}")
        return 0
    return _serve(args.app, settings)


def _verify(settings: Settings) -> int:
    requirements, gaps = load_requirements(ROOT / "controls" / "requirements.toml")
    store = FileEvidenceStore(settings.evidence_dir)
    findings = verify_pack(
        requirements, store.manifest(), store.read_all(), gaps, settings.merchant_base_url, settings.provider_base_url
    )
    for finding in findings:
        print(f"{finding.code} {finding.subject}: {finding.message}")
    verdict = "OK" if not findings else "FAILED"
    print(f"{verdict}: {len(requirements)} requirements, {len(store.read_all())} files, {len(findings)} problem(s)")
    return 0 if not findings else 1


def _serve(app: str, settings: Settings) -> int:
    if app == "provider":
        state = ProviderState(
            settings.secret_key,
            settings.publishable_key,
            settings.webhook_secret,
            f"{settings.merchant_base_url}/webhook",
        )
        flask_app, url = create_provider_app(state), settings.provider_base_url
    elif app == "merchant":
        orders = SqliteOrders(settings.database_path)
        orders.initialize((ROOT / "sql" / "001_schema.sql").read_text(encoding="utf-8"))
        checkout = CheckoutService(
            HttpProvider(settings.provider_base_url, settings.secret_key), orders, settings.webhook_secret
        )
        flask_app, url = (
            create_merchant_app(checkout, settings.provider_public_url, settings.publishable_key),
            settings.merchant_base_url,
        )
    else:
        flask_app, url = create_naive_app(settings.naive_log_path), settings.naive_base_url
    parts = urlsplit(url)
    run_simple(parts.hostname or "127.0.0.1", parts.port or 80, flask_app, threaded=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
