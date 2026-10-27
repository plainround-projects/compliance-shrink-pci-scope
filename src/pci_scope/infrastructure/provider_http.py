"""The payment provider over HTTP: a form-encoded payment-intents style API, with a timeout and retries on each call."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any

from pci_scope.domain.payment import Intent, PaymentError

ATTEMPTS = 3


class HttpProvider:
    """Calls the provider's server-side API with the secret key. Retries network errors and 5xx; a 4xx is the answer."""

    def __init__(
        self, base_url: str, secret_key: str, timeout: float = 10.0, sleep: Callable[[float], None] = time.sleep
    ) -> None:
        self._base = base_url
        self._key = secret_key
        self._timeout = timeout
        self._sleep = sleep

    def create_customer(self) -> str:
        """POST /v1/customers."""
        return str(self._post("/v1/customers", {})["id"])

    def create_intent(self, amount_cents: int, currency: str, customer_id: str, save_card: bool) -> Intent:
        """POST /v1/payment_intents; with `save_card` the provider keeps the method for later off-session charges."""
        fields = {"amount": amount_cents, "currency": currency, "customer": customer_id}
        if save_card:
            fields["setup_future_usage"] = "off_session"
        return _intent(self._post("/v1/payment_intents", fields))

    def retrieve_intent(self, intent_id: str) -> Intent:
        """GET /v1/payment_intents/<id>."""
        return _intent(self._call("GET", f"/v1/payment_intents/{urllib.parse.quote(intent_id)}", None))

    def charge_saved(self, customer_id: str, payment_method_id: str, amount_cents: int, currency: str) -> Intent:
        """POST /v1/payment_intents with confirm and off_session, from the tokens alone."""
        fields = {
            "amount": amount_cents, "currency": currency, "customer": customer_id,
            "payment_method": payment_method_id, "off_session": "true", "confirm": "true",
        }  # fmt: skip
        return _intent(self._post("/v1/payment_intents", fields))

    def refund(self, intent_id: str) -> str:
        """POST /v1/refunds."""
        return str(self._post("/v1/refunds", {"payment_intent": intent_id})["id"])

    def _post(self, path: str, fields: dict[str, Any]) -> dict[str, Any]:
        return self._call("POST", path, urllib.parse.urlencode(fields).encode())

    def _call(self, method: str, path: str, body: bytes | None) -> dict[str, Any]:
        request = urllib.request.Request(
            self._base + path,
            data=body,
            method=method,
            headers={"Authorization": f"Bearer {self._key}", "Content-Type": "application/x-www-form-urlencoded"},
        )
        delay = 0.2
        for attempt in range(1, ATTEMPTS + 1):
            try:
                with urllib.request.urlopen(request, timeout=self._timeout) as response:
                    return dict(json.loads(response.read()))
            except urllib.error.HTTPError as problem:
                if problem.code < 500:
                    raise PaymentError(_message(problem)) from None
                if attempt == ATTEMPTS:
                    raise PaymentError("the payment provider is failing") from None
            except (urllib.error.URLError, TimeoutError, OSError):
                if attempt == ATTEMPTS:
                    raise PaymentError("the payment provider is unreachable") from None
            self._sleep(delay)
            delay *= 2
        raise AssertionError("unreachable")  # pragma: no cover


def _message(problem: urllib.error.HTTPError) -> str:
    try:
        return str(json.loads(problem.read())["error"]["message"])
    except (ValueError, KeyError, TypeError):
        return f"the provider refused the request ({problem.code})"


def _intent(data: dict[str, Any]) -> Intent:
    return Intent(
        id=data["id"],
        status=data["status"],
        amount_cents=int(data["amount"]),
        currency=data["currency"],
        client_secret=data.get("client_secret", ""),
        payment_method_id=data.get("payment_method") or "",
        customer_id=data.get("customer") or "",
    )
