"""What the use cases need from the outside world."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from typing import Protocol

from pci_scope.domain.evidence import ManifestEntry
from pci_scope.domain.payment import Intent, Order


class Clock(Protocol):
    """The current time, injected so tests are deterministic."""

    def now(self) -> datetime:
        """The current moment, timezone aware."""
        ...


class PaymentProvider(Protocol):
    """The payment provider's server-side API. Card numbers never pass through it: the browser sends them elsewhere."""

    def create_customer(self) -> str:
        """A customer token (`cus_...`)."""
        ...

    def create_intent(self, amount_cents: int, currency: str, customer_id: str, save_card: bool) -> Intent:
        """A payment intent whose client secret the browser confirms with the provider."""
        ...

    def retrieve_intent(self, intent_id: str) -> Intent:
        """The intent as the provider now has it."""
        ...

    def charge_saved(self, customer_id: str, payment_method_id: str, amount_cents: int, currency: str) -> Intent:
        """Charge a saved payment method off-session, from tokens alone."""
        ...

    def refund(self, intent_id: str) -> str:
        """Refund a payment; returns the refund token (`re_...`)."""
        ...


class OrderRepository(Protocol):
    """Orders, holding provider tokens and never card data."""

    def create(self, intent_id: str, amount_cents: int, currency: str, customer_id: str) -> Order:
        """Store a pending order."""
        ...

    def find(self, intent_id: str) -> Order | None:
        """The order for a payment intent."""
        ...

    def update(self, intent_id: str, status: str, payment_method_id: str) -> None:
        """Set the status and the saved payment-method token."""
        ...


class ArtifactReader(Protocol):
    """Yields the text of each place on the merchant's side where card data could end up."""

    def artifacts(self) -> Iterator[tuple[str, str]]:
        """(name, text) for each log file, database dump and backup."""
        ...


class EvidenceStore(Protocol):
    """The evidence folder and its manifest."""

    def write(self, name: str, text: str, requirement: str, produced_at: datetime) -> None:
        """Write a file and record it in the manifest."""
        ...

    def read_all(self) -> dict[str, str]:
        """Every file in the folder."""
        ...

    def manifest(self) -> dict[str, ManifestEntry]:
        """The manifest entries by file name."""
        ...
