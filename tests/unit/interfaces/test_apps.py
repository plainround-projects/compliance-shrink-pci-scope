import json
import logging
import time

import pytest

from pci_scope.application.checkout import CheckoutService
from pci_scope.domain.card import DECLINED_TEST_CARD, TEST_CARD
from pci_scope.domain.webhook import sign, verify
from pci_scope.interfaces.merchant_app import create_merchant_app
from pci_scope.interfaces.naive_app import create_naive_app
from pci_scope.interfaces.provider_app import ProviderState, create_provider_app
from tests.conftest import SECRET, FakeProvider, MemoryOrders

SK, PK = "sk_test_abc", "pk_test_abc"
PROVIDER_URL = "http://127.0.0.1:5001"


@pytest.fixture
def provider():
    delivered: list[tuple[str, bytes, str]] = []
    state = ProviderState(
        SK, PK, SECRET, "http://merchant/webhook", deliver=lambda url, body, sig: delivered.append((url, body, sig))
    )
    client = create_provider_app(state).test_client()
    client.delivered = delivered  # type: ignore[attr-defined]
    client.state = state  # type: ignore[attr-defined]
    return client


AUTH = {"Authorization": f"Bearer {SK}"}
KEY = {"X-Publishable-Key": PK}
CARD = {"card[number]": TEST_CARD, "card[exp_month]": "12", "card[exp_year]": "30", "card[cvc]": "123"}


def intent(provider, **extra):
    customer = provider.post("/v1/customers", headers=AUTH).get_json()["id"]
    return provider.post(
        "/v1/payment_intents", data={"amount": "1900", "currency": "eur", "customer": customer, **extra}, headers=AUTH
    ).get_json()


def pay(provider, card=CARD):
    made = intent(provider)
    method = provider.post("/v1/payment_methods", data=card, headers=KEY).get_json()
    result = provider.post(
        f"/v1/payment_intents/{made['id']}/confirm",
        data={"client_secret": made["client_secret"], "payment_method": method["id"]},
        headers=KEY,
    )
    return made, method, result


def test_a_payment_with_the_test_card_succeeds_and_the_provider_sends_a_signed_event(provider):
    _, method, result = pay(provider)
    assert result.status_code == 200
    assert result.get_json()["status"] == "succeeded"
    assert method["id"].startswith("pm_")
    url, body, signature = provider.delivered[0]
    assert url == "http://merchant/webhook"
    assert json.loads(body)["type"] == "payment_intent.succeeded"
    assert verify(SECRET, body, signature, int(time.time()))


def test_the_declined_test_card_fails_and_the_event_says_so(provider):
    _, _, result = pay(provider, {**CARD, "card[number]": DECLINED_TEST_CARD})
    assert result.status_code == 402
    assert result.get_json()["error"]["message"] == "Your card was declined."
    assert json.loads(provider.delivered[0][1])["type"] == "payment_intent.payment_failed"


def test_a_bad_card_number_or_a_missing_cvc_is_refused_by_the_provider(provider):
    assert (
        provider.post("/v1/payment_methods", data={**CARD, "card[number]": "4242424242424241"}, headers=KEY).status_code
        == 400
    )
    without_cvc = {key: value for key, value in CARD.items() if key != "card[cvc]"}
    assert provider.post("/v1/payment_methods", data=without_cvc, headers=KEY).status_code == 400


def test_every_endpoint_checks_its_key(provider):
    assert provider.post("/v1/customers").status_code == 401
    assert provider.post("/v1/payment_intents", data={"amount": "1", "currency": "eur"}).status_code == 401
    assert provider.get("/v1/payment_intents/pi_x").status_code == 401
    assert provider.post("/v1/payment_methods", data=CARD).status_code == 401
    assert provider.post("/v1/payment_intents/pi_x/confirm", data={}).status_code == 401
    assert provider.post("/v1/refunds", data={}).status_code == 401


def test_intent_validation_and_lookup(provider):
    assert (
        provider.post("/v1/payment_intents", data={"amount": "abc", "currency": "eur"}, headers=AUTH).status_code == 400
    )
    assert provider.get("/v1/payment_intents/pi_missing", headers=AUTH).status_code == 404
    made = intent(provider)
    assert (
        provider.get(f"/v1/payment_intents/{made['id']}", headers=AUTH).get_json()["status"]
        == "requires_payment_method"
    )


def test_confirming_needs_the_right_client_secret_and_a_payment_method(provider):
    made = intent(provider)
    path = f"/v1/payment_intents/{made['id']}/confirm"
    assert provider.post(path, data={"client_secret": "wrong"}, headers=KEY).status_code == 404
    assert provider.post(path, data={"client_secret": made["client_secret"]}, headers=KEY).status_code == 400


def test_a_saved_method_is_charged_off_session_and_a_missing_one_is_refused(provider):
    made, method, _ = pay(provider)
    customer = made["customer"]
    again = provider.post(
        "/v1/payment_intents",
        data={
            "amount": "1900",
            "currency": "eur",
            "customer": customer,
            "payment_method": method["id"],
            "off_session": "true",
            "confirm": "true",
        },
        headers=AUTH,
    )
    assert again.get_json()["status"] == "succeeded"
    refused = provider.post(
        "/v1/payment_intents",
        data={
            "amount": "1900",
            "currency": "eur",
            "customer": customer,
            "payment_method": "pm_nothing",
            "off_session": "true",
            "confirm": "true",
        },
        headers=AUTH,
    )
    assert refused.status_code == 400


def test_only_a_succeeded_payment_can_be_refunded(provider):
    made, _, _ = pay(provider)
    assert (
        provider.post("/v1/refunds", data={"payment_intent": made["id"]}, headers=AUTH)
        .get_json()["id"]
        .startswith("re_")
    )
    assert (
        provider.post("/v1/refunds", data={"payment_intent": intent(provider)["id"]}, headers=AUTH).status_code == 400
    )


def test_the_hosted_frame_and_script_are_served_by_the_provider(provider):
    frame = provider.get("/frame?origin=http://merchant&client_secret=pi_x_secret_y")
    assert b'id="number"' in frame.data
    assert b"pk_test_abc" in frame.data
    assert "frame-ancestors http://merchant" in frame.headers["Content-Security-Policy"]
    assert b"new URL(document.currentScript.src).origin" in provider.get("/v1/elements.js").data
    assert provider.get("/healthz").get_json() == {"status": "ok"}


def test_a_webhook_that_cannot_be_delivered_does_not_break_the_payment():
    def broken(url, body, signature):
        raise OSError("merchant is down")

    state = ProviderState(SK, PK, SECRET, "http://merchant/webhook", deliver=broken)
    client = create_provider_app(state).test_client()
    assert pay(client)[2].status_code == 200


@pytest.fixture
def merchant():
    provider, orders = FakeProvider(), MemoryOrders()
    app = create_merchant_app(CheckoutService(provider, orders, SECRET), PROVIDER_URL, PK)
    client = app.test_client()
    client.orders = orders  # type: ignore[attr-defined]
    return client


def test_the_checkout_page_has_no_card_field_and_its_policy_names_only_the_provider(merchant):
    page = merchant.get("/")
    text = page.get_data(as_text=True)
    assert "<input" not in text
    assert f'<script src="{PROVIDER_URL}/v1/elements.js">' in text
    policy = page.headers["Content-Security-Policy"]
    assert f"script-src 'self' {PROVIDER_URL}" in policy
    assert f"frame-src {PROVIDER_URL}" in policy
    assert "form-action 'self'" in policy
    assert page.headers["X-Content-Type-Options"] == "nosniff"
    assert page.headers["Cache-Control"] == "no-store"


def test_the_old_card_route_is_gone(merchant):
    assert merchant.post("/pay", data={"card_number": "x"}).status_code == 404
    assert merchant.get("/pay").status_code == 404


def test_the_script_the_page_loads_reads_the_key_from_the_page_and_posts_no_card(merchant):
    script = merchant.get("/static/checkout.js").get_data(as_text=True)
    assert "dataset.key" in script
    assert "card" not in script.lower().replace("#card", "")


def test_create_pay_done_charge_again_and_refund_round_trip(merchant):
    started = merchant.post("/create-payment").get_json()
    assert started["clientSecret"] == "secret_x"
    done = merchant.get(f"/done?payment_intent={started['id']}")
    assert (done.status_code, done.get_data(as_text=True)) == (200, f"payment {started['id']}: succeeded")
    again = merchant.post("/charge-again", json={"payment_intent": started["id"]}).get_json()
    assert again["status"] == "succeeded"
    assert (
        merchant.post("/refund", json={"payment_intent": again["payment_intent"]})
        .get_json()["refund"]
        .startswith("re_")
    )


def test_payment_errors_are_402_and_never_echo_a_card(merchant):
    assert merchant.get("/done?payment_intent=" + TEST_CARD).status_code == 402
    assert merchant.get("/done").status_code == 402
    assert merchant.post("/charge-again", json={}).status_code == 402


def test_the_webhook_needs_a_valid_signature(merchant):
    started = merchant.post("/create-payment").get_json()
    body = json.dumps(
        {
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": started["id"], "payment_method": "pm_" + "1" * 24}},
        }
    ).encode()
    assert merchant.post("/webhook", data=body).status_code == 402
    signed = merchant.post("/webhook", data=body, headers={"Provider-Signature": sign(SECRET, body, int(time.time()))})
    assert signed.get_json() == {"outcome": "applied: payment_intent.succeeded"}
    assert merchant.orders.find(started["id"]).status == "succeeded"


def test_oversized_bodies_and_unexpected_errors_get_json_answers(merchant):
    assert merchant.post("/webhook", data="x" * 20_000).status_code == 413

    class Broken(FakeProvider):
        def create_customer(self):
            raise RuntimeError("database password is hunter2")

    app = create_merchant_app(CheckoutService(Broken(), MemoryOrders(), SECRET), PROVIDER_URL, PK)
    app.testing = False
    response = app.test_client().post("/create-payment")
    assert (response.status_code, response.get_json()) == (500, {"error": "internal error"})


def test_the_merchant_never_logs_a_request_body(merchant, caplog):
    with caplog.at_level(logging.INFO, logger="merchant"):
        started = merchant.post("/create-payment", data={"card_number": TEST_CARD}).get_json()
        merchant.get(f"/done?payment_intent={started['id']}")
    assert TEST_CARD not in caplog.text
    assert "created payment" in caplog.text


def test_the_naive_checkout_logs_the_whole_form(tmp_path):
    log = tmp_path / "naive" / "requests.log"
    client = create_naive_app(log).test_client()
    assert b'name="card_number"' in client.get("/").data
    assert (
        client.post("/pay", data={"card_number": TEST_CARD, "expiry": "12/30", "cvv": "123"}).data
        == b"paid (simulated)"
    )
    assert "payment request: {'card_number': '4242424242424242', 'expiry': '12/30', 'cvv': '123'}" in log.read_text()
