"""Payment values the merchant keeps: tokens and order status. Never a card number."""

from __future__ import annotations

import re
from dataclasses import dataclass

TOKEN = re.compile(r"^(pi|pm|cus|re)_[A-Za-z0-9]{8,64}$")
PAYMENT_STATUSES = ("pending", "succeeded", "failed", "refunded")


class PaymentError(Exception):
    """A payment failed in a way the customer should hear about (declined, unknown token, provider down)."""


def is_token(value: str) -> bool:
    """True for a provider id such as `pi_...` or `pm_...`: the only payment values the merchant may store."""
    return bool(TOKEN.match(value))


@dataclass(frozen=True)
class Order:
    """An order. `payment_method_id` and `customer_id` are provider tokens; the card is the provider's."""

    id: int
    payment_intent_id: str
    amount_cents: int
    currency: str
    status: str
    customer_id: str = ""
    payment_method_id: str = ""


@dataclass(frozen=True)
class Intent:
    """A payment intent as the provider reports it."""

    id: str
    status: str
    amount_cents: int
    currency: str
    client_secret: str = ""
    payment_method_id: str = ""
    customer_id: str = ""
