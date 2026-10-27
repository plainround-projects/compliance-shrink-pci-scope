"""Shared fakes: a provider and an order table in memory, and the repository root."""

from __future__ import annotations

from pathlib import Path

from pci_scope.domain.payment import Intent, Order, PaymentError

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SECRET = "whsec_unit_test_secret_value_0123456789abcdef"


class FakeProvider:
    """Records calls and answers like a provider: intents succeed unless the method is marked declined."""

    def __init__(self) -> None:
        self.intents: dict[str, Intent] = {}
        self.calls: list[tuple[str, tuple[object, ...]]] = []
        self.decline = False
        self.counter = 0

    def _next(self, prefix: str) -> str:
        self.counter += 1
        return f"{prefix}_{self.counter:024d}"

    def create_customer(self) -> str:
        self.calls.append(("create_customer", ()))
        return self._next("cus")

    def create_intent(self, amount_cents: int, currency: str, customer_id: str, save_card: bool) -> Intent:
        self.calls.append(("create_intent", (amount_cents, currency, customer_id, save_card)))
        intent = Intent(
            self._next("pi"), "requires_payment_method", amount_cents, currency, "secret_x", "", customer_id
        )
        self.intents[intent.id] = intent
        return intent

    def retrieve_intent(self, intent_id: str) -> Intent:
        self.calls.append(("retrieve_intent", (intent_id,)))
        intent = self.intents[intent_id]
        status = "requires_payment_method" if self.decline else "succeeded"
        method = "" if self.decline else "pm_" + "0" * 24
        return Intent(intent.id, status, intent.amount_cents, intent.currency, "", method, intent.customer_id)

    def charge_saved(self, customer_id: str, payment_method_id: str, amount_cents: int, currency: str) -> Intent:
        self.calls.append(("charge_saved", (customer_id, payment_method_id, amount_cents, currency)))
        if self.decline:
            raise PaymentError("Your card was declined.")
        intent = Intent(self._next("pi"), "succeeded", amount_cents, currency, "", payment_method_id, customer_id)
        self.intents[intent.id] = intent
        return intent

    def refund(self, intent_id: str) -> str:
        self.calls.append(("refund", (intent_id,)))
        return self._next("re")


class MemoryOrders:
    """The order table in a dict."""

    def __init__(self) -> None:
        self.rows: dict[str, Order] = {}

    def create(self, intent_id: str, amount_cents: int, currency: str, customer_id: str) -> Order:
        order = Order(len(self.rows) + 1, intent_id, amount_cents, currency, "pending", customer_id)
        self.rows[intent_id] = order
        return order

    def find(self, intent_id: str) -> Order | None:
        return self.rows.get(intent_id)

    def update(self, intent_id: str, status: str, payment_method_id: str) -> None:
        old = self.rows[intent_id]
        self.rows[intent_id] = Order(
            old.id, old.payment_intent_id, old.amount_cents, old.currency, status, old.customer_id, payment_method_id
        )
