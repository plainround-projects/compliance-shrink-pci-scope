"""The traffic capture: who received what during one payment, summarized and checked."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.parse import urlsplit

from pci_scope.domain.card import card_field_names, scan_text


@dataclass(frozen=True)
class Exchange:
    """One request the browser made and the status that came back. `body` is what it sent."""

    method: str
    url: str
    status: int
    body: str


def origin(url: str) -> str:
    """scheme://host:port of a URL."""
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


def to_har(exchanges: list[Exchange], redact_for: frozenset[str]) -> str:
    """HAR 1.2. Bodies sent to an origin in `redact_for` (the provider) keep their field names and lose the values, so
    the capture shows where the card fields went without becoming a new copy of the card."""
    entries = []
    for item in exchanges:
        body = item.body
        if origin(item.url) in redact_for and body:
            body = "&".join(f"{pair.split('=', 1)[0]}=[redacted]" for pair in body.split("&"))
        entries.append(
            {
                "request": {"method": item.method, "url": item.url, "postData": {"text": body}},
                "response": {"status": item.status},
            }
        )
    return (
        json.dumps(
            {
                "log": {
                    "version": "1.2",
                    "creator": {"name": "pci-scope browser simulator", "version": "0.1"},
                    "entries": entries,
                }
            },
            indent=2,
        )
        + "\n"
    )


def parse_har(text: str) -> list[Exchange]:
    """The exchanges in a HAR file."""
    entries = json.loads(text)["log"]["entries"]
    return [
        Exchange(
            e["request"]["method"],
            e["request"]["url"],
            e["response"]["status"],
            e["request"].get("postData", {}).get("text", ""),
        )
        for e in entries
    ]


def summarize(exchanges: list[Exchange], merchant: str, provider: str) -> str:
    """The lesson's summary: one line per request, where it went, and what the body held."""
    lines = []
    for item in exchanges:
        destination = origin(item.url)
        target = (
            "your server" if destination == merchant else "the provider" if destination == provider else "elsewhere"
        )
        names = card_field_names(item.body)
        body = (
            f"card fields: {', '.join(names)}"
            if names
            else "body: (empty)"
            if not item.body
            else "body: no card fields"
        )
        lines.append(f"{item.method:4} {item.url}  {body}  -> {target}")
    return "\n".join(lines) + "\n"


def merchant_exposure(exchanges: list[Exchange], merchant: str) -> list[str]:
    """Problems: any request to the merchant whose body or URL holds a card field or a card number."""
    problems = []
    for item in exchanges:
        if origin(item.url) != merchant:
            continue
        text = f"{item.url}\n{item.body}"
        if card_field_names(text) or scan_text("har", text):
            problems.append(f"{item.method} {item.url} carries card data")
    return problems


def reaches_provider(exchanges: list[Exchange], provider: str) -> bool:
    """True when at least one request to the provider carries the card fields (the card went where it should)."""
    return any(origin(item.url) == provider and card_field_names(item.body) for item in exchanges)
