import json
from datetime import UTC, datetime

import pytest

from pci_scope.application.checkout import CURRENCY, PRICE_CENTS, CheckoutService
from pci_scope.application.pack import (
    render_index,
    render_page_controls,
    render_routes,
    render_token_storage,
    scope_documents,
)
from pci_scope.application.proof import run_scan
from pci_scope.domain.card import TEST_CARD
from pci_scope.domain.evidence import EvidenceSpec, Gap, ManifestEntry, Requirement
from pci_scope.domain.payment import PaymentError
from pci_scope.domain.webhook import sign
from pci_scope.infrastructure.catalog import load_inventory
from tests.conftest import REPOSITORY_ROOT, SECRET, FakeProvider, MemoryOrders


@pytest.fixture
def parts():
    provider, orders = FakeProvider(), MemoryOrders()
    return provider, orders, CheckoutService(provider, orders, SECRET)


def test_starting_a_checkout_creates_a_customer_and_an_intent_at_the_fixed_price(parts):
    provider, orders, checkout = parts
    started = checkout.start()
    assert started.client_secret == "secret_x"
    assert provider.calls[0][0] == "create_customer"
    assert provider.calls[1] == ("create_intent", (PRICE_CENTS, CURRENCY, "cus_" + "0" * 23 + "1", True))
    assert orders.find(started.intent_id).status == "pending"


def test_the_result_comes_from_the_provider_and_the_method_token_is_saved(parts):
    _, orders, checkout = parts
    started = checkout.start()
    order = checkout.complete(started.intent_id)
    assert (order.status, order.payment_method_id) == ("succeeded", "pm_" + "0" * 24)
    assert orders.find(started.intent_id).payment_method_id.startswith("pm_")


def test_a_declined_payment_is_recorded_as_failed(parts):
    provider, _, checkout = parts
    started = checkout.start()
    provider.decline = True
    assert checkout.complete(started.intent_id).status == "failed"


@pytest.mark.parametrize("bad", ["", TEST_CARD, "pi_short", "../etc/passwd", "pm_" + "a" * 24 + "' OR 1=1"])
def test_anything_that_is_not_a_token_is_refused_before_it_reaches_the_provider(parts, bad):
    provider, _, checkout = parts
    with pytest.raises(PaymentError, match="not a payment token"):
        checkout.complete(bad)
    assert provider.calls == []


def test_an_unknown_token_is_an_unknown_payment(parts):
    with pytest.raises(PaymentError, match="unknown payment"):
        parts[2].complete("pi_" + "9" * 24)


def test_a_repeat_charge_needs_only_the_customer_and_method_tokens(parts):
    provider, _, checkout = parts
    first = checkout.start()
    checkout.complete(first.intent_id)
    again = checkout.charge_again(first.intent_id)
    assert again.status == "succeeded"
    assert again.payment_intent_id != first.intent_id
    assert provider.calls[-1][0] == "charge_saved"
    assert provider.calls[-1][1][:2] == (again.customer_id, again.payment_method_id)


def test_a_repeat_charge_without_a_saved_method_is_refused(parts):
    _, _, checkout = parts
    first = checkout.start()
    with pytest.raises(PaymentError, match="no saved payment method"):
        checkout.charge_again(first.intent_id)


def test_a_declined_repeat_charge_surfaces_the_providers_message(parts):
    provider, _, checkout = parts
    first = checkout.start()
    checkout.complete(first.intent_id)
    provider.decline = True
    with pytest.raises(PaymentError, match="declined"):
        checkout.charge_again(first.intent_id)


def test_a_refund_needs_only_the_token(parts):
    provider, orders, checkout = parts
    first = checkout.start()
    checkout.complete(first.intent_id)
    assert checkout.refund(first.intent_id).startswith("re_")
    assert orders.find(first.intent_id).status == "refunded"
    assert provider.calls[-1] == ("refund", (first.intent_id,))


def event(kind, intent_id, **extra):
    return json.dumps({"type": kind, "data": {"object": {"id": intent_id, **extra}}}).encode()


def test_a_signed_event_updates_the_order_and_repeating_it_changes_nothing(parts):
    _, orders, checkout = parts
    started = checkout.start()
    body = event("payment_intent.succeeded", started.intent_id, payment_method="pm_" + "1" * 24)
    header = sign(SECRET, body, 5_000)
    assert checkout.handle_event(body, header, 5_000) == "applied: payment_intent.succeeded"
    assert checkout.handle_event(body, header, 5_001) == "applied: payment_intent.succeeded"
    assert (orders.find(started.intent_id).status, orders.find(started.intent_id).payment_method_id) == (
        "succeeded",
        "pm_" + "1" * 24,
    )


def test_a_failed_event_marks_the_order_failed(parts):
    started = parts[2].start()
    body = event("payment_intent.payment_failed", started.intent_id)
    assert parts[2].handle_event(body, sign(SECRET, body, 5_000), 5_000) == "applied: payment_intent.payment_failed"
    assert parts[1].find(started.intent_id).status == "failed"


def test_unknown_payments_and_other_event_types_are_ignored(parts):
    _, _, checkout = parts
    started = checkout.start()
    unknown = event("payment_intent.succeeded", "pi_" + "8" * 24)
    assert checkout.handle_event(unknown, sign(SECRET, unknown, 5_000), 5_000) == "ignored: unknown payment"
    other = event("charge.dispute.created", started.intent_id)
    assert checkout.handle_event(other, sign(SECRET, other, 5_000), 5_000) == "ignored: charge.dispute.created"


@pytest.mark.parametrize("header", [None, "t=5000,v1=deadbeef"])
def test_an_event_with_a_bad_signature_is_refused(parts, header):
    started = parts[2].start()
    with pytest.raises(PaymentError, match="signature"):
        parts[2].handle_event(event("payment_intent.succeeded", started.intent_id), header, 5_000)


class Reader:
    def __init__(self, items):
        self.items = items

    def artifacts(self):
        yield from self.items


def test_a_scan_reports_clean_places_and_the_exit_code():
    outcome = run_scan("scanning:", Reader([("a.log", "created payment pi_x"), ("b.sql", "INSERT 1")]))
    assert (
        outcome.text == "scanning:\n  a.log ... clean\n  b.sql ... clean\nscanned 2 artifact(s): 0 findings\nexit=0\n"
    )
    assert (outcome.exit_code, outcome.artifacts) == (0, 2)


def test_a_scan_that_finds_a_card_reports_a_masked_evidence_and_exits_1():
    outcome = run_scan("scanning:", Reader([("req.log", f"INFO payment request: {TEST_CARD}")]))
    assert "req.log:1 FOUND card number 424242******4242" in outcome.text
    assert TEST_CARD not in outcome.text
    assert outcome.exit_code == 1


def test_the_scope_documents_come_from_the_inventories():
    docs = scope_documents(
        load_inventory(REPOSITORY_ROOT / "scope" / "before.toml"),
        load_inventory(REPOSITORY_ROOT / "scope" / "after.toml"),
    )
    assert set(docs) == {"scope-before.md", "scope-after.md", "scope-change.md"}
    assert "**9 systems and 3 teams in scope**" in docs["scope-before.md"]
    assert "**3 systems and 2 teams in scope**" in docs["scope-after.md"]


def test_the_small_reports_render():
    assert render_routes([("POST", "/pay", 404)]).endswith("POST /pay -> 404\n")
    page = render_page_controls(
        "http://m/", 200, {"Content-Security-Policy": "script-src http://p"}, ["http://p/x.js", "/a.js"], "http://p", []
    )
    assert "content-security-policy: script-src http://p" in page
    assert "referrer-policy: (missing)" in page
    assert "script  http://p/x.js  (the provider's)" in page
    assert "script  /a.js  (ours)" in page
    assert page.rstrip().endswith("card input fields on the merchant's page: none")
    tokens = render_token_storage([("id", "INTEGER")], [(1, "pi_x")], [])
    assert "  id INTEGER" in tokens
    assert tokens.rstrip().endswith("card number columns: none")


def test_the_index_lists_each_file_with_its_requirement_and_the_gaps():
    when = datetime(2026, 10, 27, 9, 0, tzinfo=UTC)
    requirements = [
        Requirement(
            "P1", "t", (EvidenceSpec("a.txt", "scan_after", "proves a"), EvidenceSpec("b.txt", "routes", "proves b"))
        )
    ]
    manifest = {"a.txt": ManifestEntry("a.txt", "P1", when, "x" * 64)}
    index = render_index(requirements, manifest, [Gap("P7", "no attestation", "PCI-1", when.date())], when)
    assert "| a.txt | P1 | proves a | 2026-10-27 |" in index
    assert "| b.txt | P1 | proves b | not produced |" in index
    assert "- P7: no attestation Ticket PCI-1, due 2026-10-27." in index
    assert "None." in render_index(requirements, manifest, [], when)
