"""Application factories for gunicorn: `gunicorn "pci_scope.interfaces.factories:merchant()"`."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask

from pci_scope.application.checkout import CheckoutService
from pci_scope.infrastructure.logging_setup import configure_logging
from pci_scope.infrastructure.provider_http import HttpProvider
from pci_scope.infrastructure.settings import load_settings
from pci_scope.infrastructure.sqlite_orders import SqliteOrders
from pci_scope.interfaces.merchant_app import create_merchant_app
from pci_scope.interfaces.naive_app import create_naive_app
from pci_scope.interfaces.provider_app import ProviderState, create_provider_app

SCHEMA = Path("sql/001_schema.sql")


def provider() -> Flask:
    """The local payment provider. State is in memory, so run it with one worker."""
    settings = load_settings(os.environ)
    configure_logging(settings.log_level)
    state = ProviderState(
        settings.secret_key, settings.publishable_key, settings.webhook_secret, f"{settings.merchant_base_url}/webhook"
    )
    return create_provider_app(state)


def merchant() -> Flask:
    """The redesigned merchant."""
    settings = load_settings(os.environ)
    configure_logging(settings.log_level)
    orders = SqliteOrders(settings.database_path)
    orders.initialize(SCHEMA.read_text(encoding="utf-8"))
    checkout = CheckoutService(
        HttpProvider(settings.provider_base_url, settings.secret_key), orders, settings.webhook_secret
    )
    return create_merchant_app(checkout, settings.provider_public_url, settings.publishable_key)


def naive() -> Flask:
    """The naive checkout, only to be measured."""
    settings = load_settings(os.environ)
    return create_naive_app(settings.naive_log_path)
