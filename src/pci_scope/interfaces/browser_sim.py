"""A scripted browser: it makes the requests a customer's browser makes during a checkout and records them as a HAR.

It does not run JavaScript. It reads the merchant's page, then makes the requests that page's scripts make: load the
provider's script, ask the merchant for a payment, load the provider's card frame, send the card to the provider,
confirm the payment, return to the merchant. Everything goes over real HTTP to real servers.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from pci_scope.domain.card import TEST_CARD, card_field_names
from pci_scope.domain.har import Exchange


@dataclass(frozen=True)
class Reply:
    """What came back."""

    status: int
    headers: dict[str, str]
    body: str


@dataclass
class PaymentRun:
    """The requests made, and what the page and the payment turned out to be."""

    exchanges: list[Exchange] = field(default_factory=list)
    intent_id: str = ""
    final_text: str = ""
    final_status: int = 0
    page_headers: dict[str, str] = field(default_factory=dict)
    page_card_fields: list[str] = field(default_factory=list)
    scripts: list[str] = field(default_factory=list)


class Browser:
    """Makes HTTP requests and keeps the log of them."""

    def __init__(self, timeout: float = 10.0) -> None:
        self._timeout = timeout
        self.exchanges: list[Exchange] = []

    def request(
        self,
        method: str,
        url: str,
        form: dict[str, str] | None = None,
        payload: Any = None,
        headers: dict[str, str] | None = None,
    ) -> Reply:
        """One request; HTTP errors are replies, not exceptions."""
        body: bytes | None = None
        sent = dict(headers or {})
        if form is not None:
            body = urllib.parse.urlencode(form).encode()
            sent["Content-Type"] = "application/x-www-form-urlencoded"
        elif payload is not None:
            body = json.dumps(payload).encode()
            sent["Content-Type"] = "application/json"
        elif method == "POST":
            body = b""
        http = urllib.request.Request(url, data=body, method=method, headers=sent)
        try:
            with urllib.request.urlopen(http, timeout=self._timeout) as response:
                reply = Reply(
                    response.status, dict(response.headers), response.read().decode("utf-8", errors="replace")
                )
        except urllib.error.HTTPError as problem:
            reply = Reply(problem.code, dict(problem.headers), problem.read().decode("utf-8", errors="replace"))
        self.exchanges.append(Exchange(method, url, reply.status, (body or b"").decode()))
        return reply


def pay_with_hosted_fields(
    browser: Browser, merchant: str, provider: str, publishable_key: str, card: str = TEST_CARD
) -> PaymentRun:
    """The redesigned checkout, start to finish, with the published test card typed into the provider's frame."""
    run = PaymentRun()
    page = browser.request("GET", f"{merchant}/")
    run.page_headers = page.headers
    run.page_card_fields = card_field_names(page.body)
    run.scripts = re.findall(r'<script src="([^"]+)"', page.body)
    browser.request("GET", f"{merchant}/static/checkout.js")
    browser.request("GET", f"{provider}/v1/elements.js")
    started = json.loads(browser.request("POST", f"{merchant}/create-payment").body)
    run.intent_id = started["id"]
    secret = urllib.parse.quote(started["clientSecret"])
    browser.request("GET", f"{provider}/frame?origin={urllib.parse.quote(merchant)}&client_secret={secret}")
    key = {"X-Publishable-Key": publishable_key}
    method = json.loads(
        browser.request(
            "POST",
            f"{provider}/v1/payment_methods",
            form={"card[number]": card, "card[exp_month]": "12", "card[exp_year]": "30", "card[cvc]": "123"},
            headers=key,
        ).body
    )
    browser.request(
        "POST", f"{provider}/v1/payment_intents/{run.intent_id}/confirm",
        form={"client_secret": started["clientSecret"], "payment_method": method["id"]}, headers=key,
    )  # fmt: skip
    final = browser.request("GET", f"{merchant}/done?payment_intent={run.intent_id}")
    run.final_text, run.final_status = final.body, final.status
    run.exchanges = list(browser.exchanges)
    return run


def pay_on_naive_checkout(browser: Browser, naive: str, card: str = TEST_CARD) -> Reply:
    """The "before": the card posted to the merchant's own server."""
    return browser.request("POST", f"{naive}/pay", form={"card_number": card, "expiry": "12/30", "cvv": "123"})
