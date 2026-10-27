"""The checkout: the merchant creates the payment and later learns the result, and never sees a card."""

from __future__ import annotations

import json
from dataclasses import dataclass

from pci_scope.application.ports import OrderRepository, PaymentProvider
from pci_scope.domain.payment import Intent, Order, PaymentError, is_token
from pci_scope.domain.webhook import verify

PRICE_CENTS = 1900
CURRENCY = "eur"


@dataclass(frozen=True)
class Started:
    """What the browser needs to pay: the secret for this intent, and the intent's id."""

    client_secret: str
    intent_id: str


class CheckoutService:
    """Create a payment, learn its result from the provider, charge again from tokens, refund."""

    def __init__(self, provider: PaymentProvider, orders: OrderRepository, webhook_secret: str) -> None:
        self._provider = provider
        self._orders = orders
        self._webhook_secret = webhook_secret

    def start(self) -> Started:
        """Create a customer and an intent for the fixed price. The price comes from here, not from the browser."""
        customer = self._provider.create_customer()
        intent = self._provider.create_intent(PRICE_CENTS, CURRENCY, customer, save_card=True)
        self._orders.create(intent.id, PRICE_CENTS, CURRENCY, customer)
        return Started(intent.client_secret, intent.id)

    def complete(self, intent_id: str) -> Order:
        """Ask the provider what happened to this intent and record it. The browser's word is not used."""
        self._known(intent_id)
        return self._record(self._provider.retrieve_intent(intent_id))

    def charge_again(self, intent_id: str) -> Order:
        """Take a second payment from the saved payment method, using only the customer and method tokens."""
        order = self._known(intent_id)
        if not order.payment_method_id or not order.customer_id:
            raise PaymentError("no saved payment method for this order")
        intent = self._provider.charge_saved(
            order.customer_id, order.payment_method_id, order.amount_cents, order.currency
        )
        self._orders.create(intent.id, order.amount_cents, order.currency, order.customer_id)
        self._orders.update(intent.id, _status(intent), order.payment_method_id)
        return self._known(intent.id)

    def refund(self, intent_id: str) -> str:
        """Refund a payment by its token; no card data is needed."""
        order = self._known(intent_id)
        refund_id = self._provider.refund(order.payment_intent_id)
        self._orders.update(order.payment_intent_id, "refunded", order.payment_method_id)
        return refund_id

    def handle_event(self, body: bytes, signature: str | None, now: int) -> str:
        """Apply a provider event after checking its signature. Repeating an event changes nothing."""
        if not verify(self._webhook_secret, body, signature, now):
            raise PaymentError("webhook signature is not valid")
        event = json.loads(body)
        intent = event["data"]["object"]
        order = self._orders.find(intent["id"])
        if order is None:
            return "ignored: unknown payment"
        status = {"payment_intent.succeeded": "succeeded", "payment_intent.payment_failed": "failed"}.get(event["type"])
        if status is None:
            return f"ignored: {event['type']}"
        self._orders.update(order.payment_intent_id, status, intent.get("payment_method", order.payment_method_id))
        return f"applied: {event['type']}"

    def _record(self, intent: Intent) -> Order:
        order = self._known(intent.id)
        if intent.payment_method_id and not is_token(intent.payment_method_id):
            raise PaymentError("the provider returned something that is not a token")
        self._orders.update(intent.id, _status(intent), intent.payment_method_id or order.payment_method_id)
        return self._known(intent.id)

    def _known(self, intent_id: str) -> Order:
        _require_token(intent_id)
        order = self._orders.find(intent_id)
        if order is None:
            raise PaymentError("unknown payment")
        return order


def _require_token(value: str) -> None:
    if not is_token(value):
        raise PaymentError("not a payment token")


def _status(intent: Intent) -> str:
    return (
        "succeeded"
        if intent.status == "succeeded"
        else "failed"
        if intent.status in ("requires_payment_method", "canceled")
        else "pending"
    )
