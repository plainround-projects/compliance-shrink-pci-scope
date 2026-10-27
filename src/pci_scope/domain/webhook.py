"""Webhook signatures: the provider signs the body with a shared secret and a timestamp; the merchant verifies both."""

from __future__ import annotations

import hashlib
import hmac

TOLERANCE_SECONDS = 300


def sign(secret: str, body: bytes, timestamp: int) -> str:
    """The header value `t=<timestamp>,v1=<hex hmac>` over `<timestamp>.<body>`."""
    signature = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={signature}"


def verify(secret: str, body: bytes, header: str | None, now: int, tolerance: int = TOLERANCE_SECONDS) -> bool:
    """True only for a signature made with the secret, over this body, no older (or newer) than the tolerance."""
    if not header:
        return False
    parts = dict(item.split("=", 1) for item in header.split(",") if "=" in item)
    if not parts.get("t", "").isdigit() or "v1" not in parts:
        return False
    timestamp = int(parts["t"])
    expected = sign(secret, body, timestamp).split("v1=", 1)[1]
    return hmac.compare_digest(parts["v1"], expected) and abs(now - timestamp) <= tolerance
