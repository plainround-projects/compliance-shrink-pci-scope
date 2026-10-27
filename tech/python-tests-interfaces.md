# The tests (interfaces)

## What it is

The pytest tests in `tests/unit/interfaces`. Each function whose name starts with `test_` is one check; pytest finds and runs them. (Every term is explained where it first appears in the walkthrough below.)

## Why this repository uses it

The tests turn every rule, adapter and command of this repository into something that can fail. A rule without a test is only a claim.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/unit/interfaces/test_apps.py` | 212 lines.  |
| `tests/unit/interfaces/test_cli.py` | 52 lines.  |

## How it works underneath

pytest imports each `test_*.py` file, builds the fixtures a test asks for by parameter name, runs the function, and counts it as passed when no `assert` fails and nothing raises. A fixture such as `tmp_path` or `monkeypatch` is prepared fresh for each test, so tests do not affect each other.

## Walkthrough of this repository's use

### `tests/unit/interfaces/test_apps.py`

`tests/unit/interfaces/test_apps.py` lines 1 to 13:

```python
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
```

> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.

Imports:

- It imports module `json`.
- It imports module `logging`.
- It imports module `time`.
- It imports module `pytest`.
- From `pci_scope.application.checkout` it takes `CheckoutService`.
- From `pci_scope.domain.card` it takes `DECLINED_TEST_CARD, TEST_CARD`.
- From `pci_scope.domain.webhook` it takes `sign, verify`.
- From `pci_scope.interfaces.merchant_app` it takes `create_merchant_app`.
- From `pci_scope.interfaces.naive_app` it takes `create_naive_app`.
- From `pci_scope.interfaces.provider_app` it takes `ProviderState, create_provider_app`.
- From `tests.conftest` it takes `SECRET, FakeProvider, MemoryOrders`.

`tests/unit/interfaces/test_apps.py` lines 15 to 16:

```python
SK, PK = "sk_test_abc", "pk_test_abc"
PROVIDER_URL = "http://127.0.0.1:5001"
```

> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Unpacks the tuple `('sk_test_abc', 'pk_test_abc')` into `(SK, PK)`.
- Stores the text `'http://127.0.0.1:5001'` in `PROVIDER_URL`.

`tests/unit/interfaces/test_apps.py` lines 19 to 28:

```python
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
```

> **In plain words.** A **fixture** is a helper function marked `@pytest.fixture`. A test that names it as a parameter receives its return value, prepared fresh for that test.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **lambda** is a small function written in one line: `lambda x: x + 1`.

**Function `provider`.**

Decorators: `@pytest.fixture`.

Step by step:

- Declares `delivered` as a `list[tuple[str, bytes, str]]` and stores the list `[]` in it.
- Stores the result of calling `ProviderState(SK, PK, SECRET, 'http://merchant/webhook', deliver=lambda url, body, sig: d…` in `state`.
- Stores the result of calling `create_provider_app(state).test_client()` in `client`.
- Stores `delivered` in `client.delivered`.
- Stores `state` in `client.state`.
- Gives back `client`.

`tests/unit/interfaces/test_apps.py` lines 31 to 33:

```python
AUTH = {"Authorization": f"Bearer {SK}"}
KEY = {"X-Publishable-Key": PK}
CARD = {"card[number]": TEST_CARD, "card[exp_month]": "12", "card[exp_year]": "30", "card[cvc]": "123"}
```

> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

These module-level lines:

- Stores the dictionary `{'Authorization': f'Bearer {SK}'}` in `AUTH`.
- Stores the dictionary `{'X-Publishable-Key': PK}` in `KEY`.
- Stores the dictionary `{'card[number]': TEST_CARD, 'card[exp_month]': '12', 'card[exp_year]'…` in `CARD`.

`tests/unit/interfaces/test_apps.py` lines 36 to 40:

```python
def intent(provider, **extra):
    customer = provider.post("/v1/customers", headers=AUTH).get_json()["id"]
    return provider.post(
        "/v1/payment_intents", data={"amount": "1900", "currency": "eur", "customer": customer, **extra}, headers=AUTH
    ).get_json()
```

**Function `intent`.**

It takes: `provider`; `**extra` (any extra named values).

Step by step:

- Stores `provider.post('/v1/customers', headers=AUTH).get_json()['id']` in `customer`.
- Gives back the result of calling `provider.post('/v1/payment_intents', data={'amount': '1900', 'currency': 'eur', 'customer…`.

`tests/unit/interfaces/test_apps.py` lines 43 to 51:

```python
def pay(provider, card=CARD):
    made = intent(provider)
    method = provider.post("/v1/payment_methods", data=card, headers=KEY).get_json()
    result = provider.post(
        f"/v1/payment_intents/{made['id']}/confirm",
        data={"client_secret": made["client_secret"], "payment_method": method["id"]},
        headers=KEY,
    )
    return made, method, result
```

**Function `pay`.**

It takes: `provider`; `card`, default `CARD`.

Step by step:

- Stores the result of calling `intent(provider)` in `made`.
- Stores the result of calling `provider.post('/v1/payment_methods', data=card, headers=KEY).get_json()` in `method`.
- Stores the result of calling `provider.post(f"/v1/payment_intents/{made['id']}/confirm", data={'client_secret': made['c…` in `result`.
- Gives back the tuple `(made, method, result)`.

`tests/unit/interfaces/test_apps.py` lines 54 to 62:

```python
def test_a_payment_with_the_test_card_succeeds_and_the_provider_sends_a_signed_event(provider):
    _, method, result = pay(provider)
    assert result.status_code == 200
    assert result.get_json()["status"] == "succeeded"
    assert method["id"].startswith("pm_")
    url, body, signature = provider.delivered[0]
    assert url == "http://merchant/webhook"
    assert json.loads(body)["type"] == "payment_intent.succeeded"
    assert verify(SECRET, body, signature, int(time.time()))
```

> **In plain words.** `assert condition` checks that something is true. In a test, a false condition fails the test and pytest shows both sides of the comparison.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** A **test** is a function whose name starts with `test_`. pytest finds it, runs it, and reports a pass when no `assert` fails and nothing raises.

**Test `test_a_payment_with_the_test_card_succeeds_and_the_provider_sends_a_signed_event`** checks: a payment with the test card succeeds and the provider sends a signed event.

It takes: `provider`.

Step by step:

- Unpacks the result of calling `pay(provider)` into `(_, method, result)`.
- Checks that `result.status_code` equals `200`; if not, the test fails.
- Checks that `result.get_json()['status']` equals `'succeeded'`; if not, the test fails.
- Checks that `method['id'].startswith('pm_')`; if not, the test fails.
- Unpacks `provider.delivered[0]` into `(url, body, signature)`.
- Checks that `url` equals `'http://merchant/webhook'`; if not, the test fails.
- Checks that `json.loads(body)['type']` equals `'payment_intent.succeeded'`; if not, the test fails.
- Checks that `verify(SECRET, body, signature, int(time.time()))`; if not, the test fails.

`tests/unit/interfaces/test_apps.py` lines 65 to 69:

```python
def test_the_declined_test_card_fails_and_the_event_says_so(provider):
    _, _, result = pay(provider, {**CARD, "card[number]": DECLINED_TEST_CARD})
    assert result.status_code == 402
    assert result.get_json()["error"]["message"] == "Your card was declined."
    assert json.loads(provider.delivered[0][1])["type"] == "payment_intent.payment_failed"
```

**Test `test_the_declined_test_card_fails_and_the_event_says_so`** checks: the declined test card fails and the event says so.

It takes: `provider`.

Step by step:

- Unpacks the result of calling `pay(provider, {**CARD, 'card[number]': DECLINED_TEST_CARD})` into `(_, _, result)`.
- Checks that `result.status_code` equals `402`; if not, the test fails.
- Checks that `result.get_json()['error']['message']` equals `'Your card was declined.'`; if not, the test fails.
- Checks that `json.loads(provider.delivered[0][1])['type']` equals `'payment_intent.payment_failed'`; if not, the test fails.

`tests/unit/interfaces/test_apps.py` lines 72 to 78:

```python
def test_a_bad_card_number_or_a_missing_cvc_is_refused_by_the_provider(provider):
    assert (
        provider.post("/v1/payment_methods", data={**CARD, "card[number]": "4242424242424241"}, headers=KEY).status_code
        == 400
    )
    without_cvc = {key: value for key, value in CARD.items() if key != "card[cvc]"}
    assert provider.post("/v1/payment_methods", data=without_cvc, headers=KEY).status_code == 400
```

> **In plain words.** A **dictionary comprehension** `{k: v for ...}` builds a dictionary with a loop written inside braces.

**Test `test_a_bad_card_number_or_a_missing_cvc_is_refused_by_the_provider`** checks: a bad card number or a missing cvc is refused by the provider.

It takes: `provider`.

Step by step:

- Checks that `provider.post('/v1/payment_methods', data={**CARD…` equals `400`; if not, the test fails.
- Stores a new dictionary made by a loop (`{key: value for key, value in CARD.items() if key != 'card[cvc]'}`) in `without_cvc`.
- Checks that `provider.post('/v1/payment_methods', data=without…` equals `400`; if not, the test fails.

`tests/unit/interfaces/test_apps.py` lines 81 to 87:

```python
def test_every_endpoint_checks_its_key(provider):
    assert provider.post("/v1/customers").status_code == 401
    assert provider.post("/v1/payment_intents", data={"amount": "1", "currency": "eur"}).status_code == 401
    assert provider.get("/v1/payment_intents/pi_x").status_code == 401
    assert provider.post("/v1/payment_methods", data=CARD).status_code == 401
    assert provider.post("/v1/payment_intents/pi_x/confirm", data={}).status_code == 401
    assert provider.post("/v1/refunds", data={}).status_code == 401
```

**Test `test_every_endpoint_checks_its_key`** checks: every endpoint checks its key.

It takes: `provider`.

Step by step:

- Checks that `provider.post('/v1/customers').status_code` equals `401`; if not, the test fails.
- Checks that `provider.post('/v1/payment_intents', data={'amoun…` equals `401`; if not, the test fails.
- Checks that `provider.get('/v1/payment_intents/pi_x').status_c…` equals `401`; if not, the test fails.
- Checks that `provider.post('/v1/payment_methods', data=CARD).s…` equals `401`; if not, the test fails.
- Checks that `provider.post('/v1/payment_intents/pi_x/confirm',…` equals `401`; if not, the test fails.
- Checks that `provider.post('/v1/refunds', data={}).status_code` equals `401`; if not, the test fails.

`tests/unit/interfaces/test_apps.py` lines 90 to 99:

```python
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
```

**Test `test_intent_validation_and_lookup`** checks: intent validation and lookup.

It takes: `provider`.

Step by step:

- Checks that `provider.post('/v1/payment_intents', data={'amoun…` equals `400`; if not, the test fails.
- Checks that `provider.get('/v1/payment_intents/pi_missing', he…` equals `404`; if not, the test fails.
- Stores the result of calling `intent(provider)` in `made`.
- Checks that `provider.get(f"/v1/payment_intents/{made['id']}",…` equals `'requires_payment_method'`; if not, the test fails.

`tests/unit/interfaces/test_apps.py` lines 102 to 106:

```python
def test_confirming_needs_the_right_client_secret_and_a_payment_method(provider):
    made = intent(provider)
    path = f"/v1/payment_intents/{made['id']}/confirm"
    assert provider.post(path, data={"client_secret": "wrong"}, headers=KEY).status_code == 404
    assert provider.post(path, data={"client_secret": made["client_secret"]}, headers=KEY).status_code == 400
```

**Test `test_confirming_needs_the_right_client_secret_and_a_payment_method`** checks: confirming needs the right client secret and a payment method.

It takes: `provider`.

Step by step:

- Stores the result of calling `intent(provider)` in `made`.
- Stores a text built with values filled in (`f"/v1/payment_intents/{made['id']}/confirm"`) in `path`.
- Checks that `provider.post(path, data={'client_secret': 'wrong…` equals `404`; if not, the test fails.
- Checks that `provider.post(path, data={'client_secret': made['…` equals `400`; if not, the test fails.

`tests/unit/interfaces/test_apps.py` lines 109 to 137:

```python
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
```

**Test `test_a_saved_method_is_charged_off_session_and_a_missing_one_is_refused`** checks: a saved method is charged off session and a missing one is refused.

It takes: `provider`.

Step by step:

- Unpacks the result of calling `pay(provider)` into `(made, method, _)`.
- Stores `made['customer']` in `customer`.
- Stores the result of calling `provider.post('/v1/payment_intents', data={'amount': '1900', 'currency': 'eur', 'customer…` in `again`.
- Checks that `again.get_json()['status']` equals `'succeeded'`; if not, the test fails.
- Stores the result of calling `provider.post('/v1/payment_intents', data={'amount': '1900', 'currency': 'eur', 'customer…` in `refused`.
- Checks that `refused.status_code` equals `400`; if not, the test fails.

`tests/unit/interfaces/test_apps.py` lines 140 to 149:

```python
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
```

**Test `test_only_a_succeeded_payment_can_be_refunded`** checks: only a succeeded payment can be refunded.

It takes: `provider`.

Step by step:

- Unpacks the result of calling `pay(provider)` into `(made, _, _)`.
- Checks that `provider.post('/v1/refunds', data={'payment_intent': made['id']}, hea…`; if not, the test fails.
- Checks that `provider.post('/v1/refunds', data={'payment_inten…` equals `400`; if not, the test fails.

`tests/unit/interfaces/test_apps.py` lines 152 to 158:

```python
def test_the_hosted_frame_and_script_are_served_by_the_provider(provider):
    frame = provider.get("/frame?origin=http://merchant&client_secret=pi_x_secret_y")
    assert b'id="number"' in frame.data
    assert b"pk_test_abc" in frame.data
    assert "frame-ancestors http://merchant" in frame.headers["Content-Security-Policy"]
    assert b"new URL(document.currentScript.src).origin" in provider.get("/v1/elements.js").data
    assert provider.get("/healthz").get_json() == {"status": "ok"}
```

**Test `test_the_hosted_frame_and_script_are_served_by_the_provider`** checks: the hosted frame and script are served by the provider.

It takes: `provider`.

Step by step:

- Stores the result of calling `provider.get('/frame?origin=http://merchant&client_secret=pi_x_secret_y')` in `frame`.
- Checks that `b'id="number"'` is in `frame.data`; if not, the test fails.
- Checks that `b'pk_test_abc'` is in `frame.data`; if not, the test fails.
- Checks that `'frame-ancestors http://merchant'` is in `frame.headers['Content-Security-Policy']`; if not, the test fails.
- Checks that `b'new URL(document.currentScript.src).origin'` is in `provider.get('/v1/elements.js').data`; if not, the test fails.
- Checks that `provider.get('/healthz').get_json()` equals `{'status': 'ok'}`; if not, the test fails.

`tests/unit/interfaces/test_apps.py` lines 161 to 167:

```python
def test_a_webhook_that_cannot_be_delivered_does_not_break_the_payment():
    def broken(url, body, signature):
        raise OSError("merchant is down")

    state = ProviderState(SK, PK, SECRET, "http://merchant/webhook", deliver=broken)
    client = create_provider_app(state).test_client()
    assert pay(client)[2].status_code == 200
```

> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.

**Test `test_a_webhook_that_cannot_be_delivered_does_not_break_the_payment`** checks: a webhook that cannot be delivered does not break the payment.

Step by step:

- Defines a helper function `broken(url, body, signature)`.
  - Stops here by raising `OSError('merchant is down')`.
- Stores the result of calling `ProviderState(SK, PK, SECRET, 'http://merchant/webhook', deliver=broken)` in `state`.
- Stores the result of calling `create_provider_app(state).test_client()` in `client`.
- Checks that `pay(client)[2].status_code` equals `200`; if not, the test fails.

`tests/unit/interfaces/test_apps.py` lines 170 to 176:

```python
@pytest.fixture
def merchant():
    provider, orders = FakeProvider(), MemoryOrders()
    app = create_merchant_app(CheckoutService(provider, orders, SECRET), PROVIDER_URL, PK)
    client = app.test_client()
    client.orders = orders  # type: ignore[attr-defined]
    return client
```

**Function `merchant`.**

Decorators: `@pytest.fixture`.

Step by step:

- Unpacks the tuple `(FakeProvider(), MemoryOrders())` into `(provider, orders)`.
- Stores the result of calling `create_merchant_app(CheckoutService(provider, orders, SECRET), PROVIDER_URL, PK)` in `app`.
- Stores the result of calling `app.test_client()` in `client`.
- Stores `orders` in `client.orders`.
- Gives back `client`.

`tests/unit/interfaces/test_apps.py` lines 179 to 189:

```python
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
```

**Test `test_the_checkout_page_has_no_card_field_and_its_policy_names_only_the_provider`** checks: the checkout page has no card field and its policy names only the provider.

It takes: `merchant`.

Step by step:

- Stores the result of calling `merchant.get('/')` in `page`.
- Stores the result of calling `page.get_data(as_text=True)` in `text`.
- Checks that `'<input'` is not in `text`; if not, the test fails.
- Checks that `f'<script src="{PROVIDER_URL}/v1/elements.js">'` is in `text`; if not, the test fails.
- Stores `page.headers['Content-Security-Policy']` in `policy`.
- Checks that `f"script-src 'self' {PROVIDER_URL}"` is in `policy`; if not, the test fails.
- Checks that `f'frame-src {PROVIDER_URL}'` is in `policy`; if not, the test fails.
- Checks that `"form-action 'self'"` is in `policy`; if not, the test fails.
- Checks that `page.headers['X-Content-Type-Options']` equals `'nosniff'`; if not, the test fails.
- Checks that `page.headers['Cache-Control']` equals `'no-store'`; if not, the test fails.

`tests/unit/interfaces/test_apps.py` lines 192 to 194:

```python
def test_the_old_card_route_is_gone(merchant):
    assert merchant.post("/pay", data={"card_number": "x"}).status_code == 404
    assert merchant.get("/pay").status_code == 404
```

**Test `test_the_old_card_route_is_gone`** checks: the old card route is gone.

It takes: `merchant`.

Step by step:

- Checks that `merchant.post('/pay', data={'card_number': 'x'}).…` equals `404`; if not, the test fails.
- Checks that `merchant.get('/pay').status_code` equals `404`; if not, the test fails.

`tests/unit/interfaces/test_apps.py` lines 197 to 200:

```python
def test_the_script_the_page_loads_reads_the_key_from_the_page_and_posts_no_card(merchant):
    script = merchant.get("/static/checkout.js").get_data(as_text=True)
    assert "dataset.key" in script
    assert "card" not in script.lower().replace("#card", "")
```

**Test `test_the_script_the_page_loads_reads_the_key_from_the_page_and_posts_no_card`** checks: the script the page loads reads the key from the page and posts no card.

It takes: `merchant`.

Step by step:

- Stores the result of calling `merchant.get('/static/checkout.js').get_data(as_text=True)` in `script`.
- Checks that `'dataset.key'` is in `script`; if not, the test fails.
- Checks that `'card'` is not in `script.lower().replace('#card', '')`; if not, the test fails.

`tests/unit/interfaces/test_apps.py` lines 203 to 214:

```python
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
```

**Test `test_create_pay_done_charge_again_and_refund_round_trip`** checks: create pay done charge again and refund round trip.

It takes: `merchant`.

Step by step:

- Stores the result of calling `merchant.post('/create-payment').get_json()` in `started`.
- Checks that `started['clientSecret']` equals `'secret_x'`; if not, the test fails.
- Stores the result of calling `merchant.get(f"/done?payment_intent={started['id']}")` in `done`.
- Checks that `(done.status_code, done.get_data(as_text=True))` equals `(200, f"payment {started['id']}: succeeded")`; if not, the test fails.
- Stores the result of calling `merchant.post('/charge-again', json={'payment_intent': started['id']}).get_json()` in `again`.
- Checks that `again['status']` equals `'succeeded'`; if not, the test fails.
- Checks that `merchant.post('/refund', json={'payment_intent': again['payment_inten…`; if not, the test fails.

`tests/unit/interfaces/test_apps.py` lines 217 to 220:

```python
def test_payment_errors_are_402_and_never_echo_a_card(merchant):
    assert merchant.get("/done?payment_intent=" + TEST_CARD).status_code == 402
    assert merchant.get("/done").status_code == 402
    assert merchant.post("/charge-again", json={}).status_code == 402
```

**Test `test_payment_errors_are_402_and_never_echo_a_card`** checks: payment errors are 402 and never echo a card.

It takes: `merchant`.

Step by step:

- Checks that `merchant.get('/done?payment_intent=' + TEST_CARD)…` equals `402`; if not, the test fails.
- Checks that `merchant.get('/done').status_code` equals `402`; if not, the test fails.
- Checks that `merchant.post('/charge-again', json={}).status_co…` equals `402`; if not, the test fails.

`tests/unit/interfaces/test_apps.py` lines 223 to 234:

```python
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
```

**Test `test_the_webhook_needs_a_valid_signature`** checks: the webhook needs a valid signature.

It takes: `merchant`.

Step by step:

- Stores the result of calling `merchant.post('/create-payment').get_json()` in `started`.
- Stores the result of calling `json.dumps({'type': 'payment_intent.succeeded', 'data': {'object': {'id': started['id'], …` in `body`.
- Checks that `merchant.post('/webhook', data=body).status_code` equals `402`; if not, the test fails.
- Stores the result of calling `merchant.post('/webhook', data=body, headers={'Provider-Signature': sign(SECRET, body, in…` in `signed`.
- Checks that `signed.get_json()` equals `{'outcome': 'applied: payment_intent.succeeded'}`; if not, the test fails.
- Checks that `merchant.orders.find(started['id']).status` equals `'succeeded'`; if not, the test fails.

`tests/unit/interfaces/test_apps.py` lines 237 to 247:

```python
def test_oversized_bodies_and_unexpected_errors_get_json_answers(merchant):
    assert merchant.post("/webhook", data="x" * 20_000).status_code == 413

    class Broken(FakeProvider):
        def create_customer(self):
            raise RuntimeError("database password is hunter2")

    app = create_merchant_app(CheckoutService(Broken(), MemoryOrders(), SECRET), PROVIDER_URL, PK)
    app.testing = False
    response = app.test_client().post("/create-payment")
    assert (response.status_code, response.get_json()) == (500, {"error": "internal error"})
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.

**Test `test_oversized_bodies_and_unexpected_errors_get_json_answers`** checks: oversized bodies and unexpected errors get json answers.

It takes: `merchant`.

Step by step:

- Checks that `merchant.post('/webhook', data='x' * 20000).statu…` equals `413`; if not, the test fails.
- Defines a class `Broken`.
- Stores the result of calling `create_merchant_app(CheckoutService(Broken(), MemoryOrders(), SECRET), PROVIDER_URL, PK)` in `app`.
- Stores `False` in `app.testing`.
- Stores the result of calling `app.test_client().post('/create-payment')` in `response`.
- Checks that `(response.status_code, response.get_json())` equals `(500, {'error': 'internal error'})`; if not, the test fails.

`tests/unit/interfaces/test_apps.py` lines 250 to 255:

```python
def test_the_merchant_never_logs_a_request_body(merchant, caplog):
    with caplog.at_level(logging.INFO, logger="merchant"):
        started = merchant.post("/create-payment", data={"card_number": TEST_CARD}).get_json()
        merchant.get(f"/done?payment_intent={started['id']}")
    assert TEST_CARD not in caplog.text
    assert "created payment" in caplog.text
```

> **In plain words.** A **`with` block** opens something (a file, a connection, a lock), runs the steps inside, and always closes it at the end, even if an error happens.

**Test `test_the_merchant_never_logs_a_request_body`** checks: the merchant never logs a request body.

It takes: `merchant`; `caplog`.

Step by step:

- Inside a `with` block that opens `caplog.at_level(logging.INFO, logger='merchant')`:
  - Stores the result of calling `merchant.post('/create-payment', data={'card_number': TEST_CARD}).get_json()` in `started`.
  - Calls `merchant.get(f"/done?payment_intent={started['id']}")`.
- Checks that `TEST_CARD` is not in `caplog.text`; if not, the test fails.
- Checks that `'created payment'` is in `caplog.text`; if not, the test fails.

`tests/unit/interfaces/test_apps.py` lines 258 to 266:

```python
def test_the_naive_checkout_logs_the_whole_form(tmp_path):
    log = tmp_path / "naive" / "requests.log"
    client = create_naive_app(log).test_client()
    assert b'name="card_number"' in client.get("/").data
    assert (
        client.post("/pay", data={"card_number": TEST_CARD, "expiry": "12/30", "cvv": "123"}).data
        == b"paid (simulated)"
    )
    assert "payment request: {'card_number': '4242424242424242', 'expiry': '12/30', 'cvv': '123'}" in log.read_text()
```

> **In plain words.** `tmp_path` is a built-in pytest fixture: a fresh, empty temporary folder (a `Path`) that is removed after the test.

**Test `test_the_naive_checkout_logs_the_whole_form`** checks: the naive checkout logs the whole form.

It takes: `tmp_path`.

Step by step:

- Stores `tmp_path / 'naive' / 'requests.log'` in `log`.
- Stores the result of calling `create_naive_app(log).test_client()` in `client`.
- Checks that `b'name="card_number"'` is in `client.get('/').data`; if not, the test fails.
- Checks that `client.post('/pay', data={'card_number': TEST_CAR…` equals `b'paid (simulated)'`; if not, the test fails.
- Checks that `"payment request: {'card_number': '42424242424242…` is in `log.read_text()`; if not, the test fails.

### `tests/unit/interfaces/test_cli.py`

`tests/unit/interfaces/test_cli.py` lines 1 to 4:

```python
import pytest

from pci_scope.domain.card import TEST_CARD
from pci_scope.interfaces.cli import build_parser, main
```

> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.

Imports:

- It imports module `pytest`.
- From `pci_scope.domain.card` it takes `TEST_CARD`.
- From `pci_scope.interfaces.cli` it takes `build_parser, main`.

`tests/unit/interfaces/test_cli.py` lines 6 to 12:

```python
ENV = {
    "PROVIDER_BASE_URL": "http://127.0.0.1:5001",
    "PROVIDER_SECRET_KEY": "sk_test_abc",
    "PROVIDER_PUBLISHABLE_KEY": "pk_test_abc",
    "WEBHOOK_SECRET": "w" * 32,
    "MERCHANT_BASE_URL": "http://127.0.0.1:5000",
}
```

> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the dictionary `{'PROVIDER_BASE_URL': 'http://127.0.0.1:5001', 'PROVIDER_SECRET_KEY':…` in `ENV`.

`tests/unit/interfaces/test_cli.py` lines 15 to 22:

```python
@pytest.fixture
def env(monkeypatch, tmp_path):
    for name, value in ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("EVIDENCE_DIR", str(tmp_path / "evidence"))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "m.db"))
    monkeypatch.setenv("STATE_DIR", str(tmp_path / "state"))
    return tmp_path
```

> **In plain words.** A **fixture** is a helper function marked `@pytest.fixture`. A test that names it as a parameter receives its return value, prepared fresh for that test.
> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** `tmp_path` is a built-in pytest fixture: a fresh, empty temporary folder (a `Path`) that is removed after the test.
> **In plain words.** `monkeypatch` is a built-in pytest fixture that changes something (an environment variable, an attribute) for this test only and undoes it afterwards.

**Function `env`.**

It takes: `monkeypatch`; `tmp_path`.

Decorators: `@pytest.fixture`.

Step by step:

- For each `(name, value)` in the result of calling `ENV.items()`:
  - Calls `monkeypatch.setenv(name, value)`.
- Calls `monkeypatch.setenv('EVIDENCE_DIR', str(tmp_path / 'evidence'))`.
- Calls `monkeypatch.setenv('DATABASE_PATH', str(tmp_path / 'm.db'))`.
- Calls `monkeypatch.setenv('STATE_DIR', str(tmp_path / 'state'))`.
- Gives back `tmp_path`.

`tests/unit/interfaces/test_cli.py` lines 25 to 30:

```python
def test_every_job_has_a_subcommand():
    parser = build_parser()
    for command in ("demo", "verify", "scope", "db"):
        assert parser.parse_args([command]).command == command
    assert parser.parse_args(["scan", "a", "b"]).paths[1].name == "b"
    assert parser.parse_args(["serve", "provider"]).app == "provider"
```

> **In plain words.** `assert condition` checks that something is true. In a test, a false condition fails the test and pytest shows both sides of the comparison.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **test** is a function whose name starts with `test_`. pytest finds it, runs it, and reports a pass when no `assert` fails and nothing raises.

**Test `test_every_job_has_a_subcommand`** checks: every job has a subcommand.

Step by step:

- Stores the result of calling `build_parser()` in `parser`.
- For each `command` in the tuple `('demo', 'verify', 'scope', 'db')`:
  - Checks that `parser.parse_args([command]).command` equals `command`; if not, the test fails.
- Checks that `parser.parse_args(['scan', 'a', 'b']).paths[1].na…` equals `'b'`; if not, the test fails.
- Checks that `parser.parse_args(['serve', 'provider']).app` equals `'provider'`; if not, the test fails.

`tests/unit/interfaces/test_cli.py` lines 33 to 36:

```python
def test_a_live_key_exits_2(env, monkeypatch, capsys):
    monkeypatch.setenv("PROVIDER_SECRET_KEY", "sk_live_abc")
    assert main(["scope"]) == 2
    assert "test-mode keys" in capsys.readouterr().err
```

> **In plain words.** `capsys` is a built-in pytest fixture that captures what the program prints, so the test can read it with `capsys.readouterr()`.

**Test `test_a_live_key_exits_2`** checks: a live key exits 2.

It takes: `env`; `monkeypatch`; `capsys`.

Step by step:

- Calls `monkeypatch.setenv('PROVIDER_SECRET_KEY', 'sk_live_abc')`.
- Checks that `main(['scope'])` equals `2`; if not, the test fails.
- Checks that `'test-mode keys'` is in `capsys.readouterr().err`; if not, the test fails.

`tests/unit/interfaces/test_cli.py` lines 39 to 44:

```python
def test_the_scope_command_prints_both_inventories_and_the_change(env, capsys):
    assert main(["scope"]) == 0
    out = capsys.readouterr().out
    assert "**9 systems and 3 teams in scope**" in out
    assert "**3 systems and 2 teams in scope**" in out
    assert "== scope-change.md" in out
```

**Test `test_the_scope_command_prints_both_inventories_and_the_change`** checks: the scope command prints both inventories and the change.

It takes: `env`; `capsys`.

Step by step:

- Checks that `main(['scope'])` equals `0`; if not, the test fails.
- Stores `capsys.readouterr().out` in `out`.
- Checks that `'**9 systems and 3 teams in scope**'` is in `out`; if not, the test fails.
- Checks that `'**3 systems and 2 teams in scope**'` is in `out`; if not, the test fails.
- Checks that `'== scope-change.md'` is in `out`; if not, the test fails.

`tests/unit/interfaces/test_cli.py` lines 47 to 55:

```python
def test_the_scan_command_exits_1_when_a_card_is_in_a_file_and_0_when_it_is_not(env, capsys):
    dirty, clean = env / "dirty.log", env / "clean.log"
    dirty.write_text(f"payment request: {TEST_CARD}\n")
    clean.write_text("created payment pi_x\n")
    assert main(["scan", str(clean)]) == 0
    assert main(["scan", str(dirty), str(clean)]) == 1
    out = capsys.readouterr().out
    assert "FOUND card number 424242******4242" in out
    assert TEST_CARD not in out
```

> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Test `test_the_scan_command_exits_1_when_a_card_is_in_a_file_and_0_when_it_is_not`** checks: the scan command exits 1 when a card is in a file and 0 when it is not.

It takes: `env`; `capsys`.

Step by step:

- Unpacks the tuple `(env / 'dirty.log', env / 'clean.log')` into `(dirty, clean)`.
- Calls `dirty.write_text(f'payment request: {TEST_CARD}\n')`.
- Calls `clean.write_text('created payment pi_x\n')`.
- Checks that `main(['scan', str(clean)])` equals `0`; if not, the test fails.
- Checks that `main(['scan', str(dirty), str(clean)])` equals `1`; if not, the test fails.
- Stores `capsys.readouterr().out` in `out`.
- Checks that `'FOUND card number 424242******4242'` is in `out`; if not, the test fails.
- Checks that `TEST_CARD` is not in `out`; if not, the test fails.

`tests/unit/interfaces/test_cli.py` lines 58 to 61:

```python
def test_the_db_command_creates_the_database_with_the_seed(env, capsys):
    assert main(["db"]) == 0
    assert (env / "m.db").is_file()
    assert "created" in capsys.readouterr().out
```

**Test `test_the_db_command_creates_the_database_with_the_seed`** checks: the db command creates the database with the seed.

It takes: `env`; `capsys`.

Step by step:

- Checks that `main(['db'])` equals `0`; if not, the test fails.
- Checks that `(env / 'm.db').is_file()`; if not, the test fails.
- Checks that `'created'` is in `capsys.readouterr().out`; if not, the test fails.

`tests/unit/interfaces/test_cli.py` lines 64 to 68:

```python
def test_verify_without_a_pack_fails_with_every_file_missing(env, capsys):
    assert main(["verify"]) == 1
    out = capsys.readouterr().out
    assert "EVP002 P1 payment.har" in out
    assert out.strip().splitlines()[-1].startswith("FAILED: 7 requirements, 0 files")
```

**Test `test_verify_without_a_pack_fails_with_every_file_missing`** checks: verify without a pack fails with every file missing.

It takes: `env`; `capsys`.

Step by step:

- Checks that `main(['verify'])` equals `1`; if not, the test fails.
- Stores `capsys.readouterr().out` in `out`.
- Checks that `'EVP002 P1 payment.har'` is in `out`; if not, the test fails.
- Checks that `out.strip().splitlines()[-1].startswith('FAILED: 7 requirements, 0 fi…`; if not, the test fails.

## Try it yourself

```bash
.venv/bin/pytest -q tests/unit/interfaces
```
Prints a row of dots, one per passing test, and a summary line such as `N passed in 0.5s` (skipped tests show as `s`).

```bash
.venv/bin/mypy
```
Checks the whole project (the `files` setting in `pyproject.toml`), these files included. Prints `Success: no issues found in 46 source files`.

```bash
.venv/bin/ruff check tests/unit/interfaces/test_apps.py tests/unit/interfaces/test_cli.py
```
Prints `All checks passed!`.

## Mistakes people make

- Tests that depend on each other's order. Each test here builds its own data.
- Asserting only the happy path. These tests also break the input on purpose and check the exact rule that fails.
- Forgetting `test_` in a name, so the test never runs.

## Check yourself

1. What does the test `test_a_payment_with_the_test_card_succeeds_and_the_provider_sends_a_signed_event` check?
   **Answer:** it checks: a payment with the test card succeeds and the provider sends a signed event.
2. What does the test `test_the_declined_test_card_fails_and_the_event_says_so` check?
   **Answer:** it checks: the declined test card fails and the event says so.
3. What does the test `test_a_bad_card_number_or_a_missing_cvc_is_refused_by_the_provider` check?
   **Answer:** it checks: a bad card number or a missing cvc is refused by the provider.
4. What does the test `test_every_endpoint_checks_its_key` check?
   **Answer:** it checks: every endpoint checks its key.
5. What does the test `test_intent_validation_and_lookup` check?
   **Answer:** it checks: intent validation and lookup.

## Further reading

- pytest 9.1 documentation: <https://docs.pytest.org/en/stable/>
- How to use fixtures: <https://docs.pytest.org/en/stable/how-to/fixtures.html>
- `assert` rewriting: <https://docs.pytest.org/en/stable/how-to/assert.html>
