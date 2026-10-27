"""Settings from the environment, validated once at start-up (twelve-factor). Keys and secrets come only from here."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


class SettingsError(ValueError):
    """An environment variable is missing or holds a value the program must refuse."""


@dataclass(frozen=True)
class Settings:
    """Everything the programs read from the environment."""

    provider_base_url: str
    provider_public_url: str
    secret_key: str
    publishable_key: str
    webhook_secret: str
    merchant_base_url: str
    naive_base_url: str
    database_path: Path
    naive_log_path: Path
    state_dir: Path
    evidence_dir: Path
    log_level: str


def _required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "")
    if not value:
        raise SettingsError(f"{name} is required")
    return value


def load_settings(env: Mapping[str, str]) -> Settings:
    """Validate and collect the settings. A live key is refused: this project is for test mode only."""
    secret, publishable = _required(env, "PROVIDER_SECRET_KEY"), _required(env, "PROVIDER_PUBLISHABLE_KEY")
    if not secret.startswith("sk_test_") or not publishable.startswith("pk_test_"):
        raise SettingsError("only test-mode keys (sk_test_..., pk_test_...) are accepted; never use a live key here")
    webhook = _required(env, "WEBHOOK_SECRET")
    if len(webhook) < 32:
        raise SettingsError("WEBHOOK_SECRET must be at least 32 characters")
    level = env.get("LOG_LEVEL", "INFO").upper()
    if level not in ("DEBUG", "INFO", "WARNING", "ERROR"):
        raise SettingsError(f"LOG_LEVEL must be DEBUG, INFO, WARNING or ERROR, got {level!r}")
    return Settings(
        provider_base_url=_required(env, "PROVIDER_BASE_URL").rstrip("/"),
        provider_public_url=env.get("PROVIDER_PUBLIC_URL", _required(env, "PROVIDER_BASE_URL")).rstrip("/"),
        secret_key=secret,
        publishable_key=publishable,
        webhook_secret=webhook,
        merchant_base_url=_required(env, "MERCHANT_BASE_URL").rstrip("/"),
        naive_base_url=env.get("NAIVE_BASE_URL", "http://127.0.0.1:5002").rstrip("/"),
        database_path=Path(env.get("DATABASE_PATH", "state/merchant.db")),
        naive_log_path=Path(env.get("NAIVE_LOG_PATH", "state/naive/requests.log")),
        state_dir=Path(env.get("STATE_DIR", "state")),
        evidence_dir=Path(env.get("EVIDENCE_DIR", "evidence")),
        log_level=level,
    )
