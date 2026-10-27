# The tests (application)

## What it is

The pytest tests in `tests/unit/application`. Each function whose name starts with `test_` is one check; pytest finds and runs them. (Every term is explained where it first appears in the walkthrough below.)

## Why this repository uses it

The tests turn every rule, adapter and command of this repository into something that can fail. A rule without a test is only a claim.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/unit/application/test_checkout_proof_pack.py` | 157 lines.  |

## How it works underneath

pytest imports each `test_*.py` file, builds the fixtures a test asks for by parameter name, runs the function, and counts it as passed when no `assert` fails and nothing raises. A fixture such as `tmp_path` or `monkeypatch` is prepared fresh for each test, so tests do not affect each other.

## Walkthrough of this repository's use

### `tests/unit/application/test_checkout_proof_pack.py`

`tests/unit/application/test_checkout_proof_pack.py` lines 1 to 20:

```python
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
```

> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.

Imports:

- It imports module `json`.
- From `datetime` it takes `UTC, datetime`.
- It imports module `pytest`.
- From `pci_scope.application.checkout` it takes `CURRENCY, PRICE_CENTS, CheckoutService`.
- From `pci_scope.application.pack` it takes `render_index, render_page_controls, render_routes, render_token_storage, scope_documents`.
- From `pci_scope.application.proof` it takes `run_scan`.
- From `pci_scope.domain.card` it takes `TEST_CARD`.
- From `pci_scope.domain.evidence` it takes `EvidenceSpec, Gap, ManifestEntry, Requirement`.
- From `pci_scope.domain.payment` it takes `PaymentError`.
- From `pci_scope.domain.webhook` it takes `sign`.
- From `pci_scope.infrastructure.catalog` it takes `load_inventory`.
- From `tests.conftest` it takes `REPOSITORY_ROOT, SECRET, FakeProvider, MemoryOrders`.

`tests/unit/application/test_checkout_proof_pack.py` lines 23 to 26:

```python
@pytest.fixture
def parts():
    provider, orders = FakeProvider(), MemoryOrders()
    return provider, orders, CheckoutService(provider, orders, SECRET)
```

> **In plain words.** A **fixture** is a helper function marked `@pytest.fixture`. A test that names it as a parameter receives its return value, prepared fresh for that test.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Function `parts`.**

Decorators: `@pytest.fixture`.

Step by step:

- Unpacks the tuple `(FakeProvider(), MemoryOrders())` into `(provider, orders)`.
- Gives back the tuple `(provider, orders, CheckoutService(provider, orders, SECRET))`.

`tests/unit/application/test_checkout_proof_pack.py` lines 29 to 35:

```python
def test_starting_a_checkout_creates_a_customer_and_an_intent_at_the_fixed_price(parts):
    provider, orders, checkout = parts
    started = checkout.start()
    assert started.client_secret == "secret_x"
    assert provider.calls[0][0] == "create_customer"
    assert provider.calls[1] == ("create_intent", (PRICE_CENTS, CURRENCY, "cus_" + "0" * 23 + "1", True))
    assert orders.find(started.intent_id).status == "pending"
```

> **In plain words.** `assert condition` checks that something is true. In a test, a false condition fails the test and pytest shows both sides of the comparison.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **test** is a function whose name starts with `test_`. pytest finds it, runs it, and reports a pass when no `assert` fails and nothing raises.

**Test `test_starting_a_checkout_creates_a_customer_and_an_intent_at_the_fixed_price`** checks: starting a checkout creates a customer and an intent at the fixed price.

It takes: `parts`.

Step by step:

- Unpacks `parts` into `(provider, orders, checkout)`.
- Stores the result of calling `checkout.start()` in `started`.
- Checks that `started.client_secret` equals `'secret_x'`; if not, the test fails.
- Checks that `provider.calls[0][0]` equals `'create_customer'`; if not, the test fails.
- Checks that `provider.calls[1]` equals `('create_intent', (PRICE_CENTS, CURRENCY, 'cus_' …`; if not, the test fails.
- Checks that `orders.find(started.intent_id).status` equals `'pending'`; if not, the test fails.

`tests/unit/application/test_checkout_proof_pack.py` lines 38 to 43:

```python
def test_the_result_comes_from_the_provider_and_the_method_token_is_saved(parts):
    _, orders, checkout = parts
    started = checkout.start()
    order = checkout.complete(started.intent_id)
    assert (order.status, order.payment_method_id) == ("succeeded", "pm_" + "0" * 24)
    assert orders.find(started.intent_id).payment_method_id.startswith("pm_")
```

**Test `test_the_result_comes_from_the_provider_and_the_method_token_is_saved`** checks: the result comes from the provider and the method token is saved.

It takes: `parts`.

Step by step:

- Unpacks `parts` into `(_, orders, checkout)`.
- Stores the result of calling `checkout.start()` in `started`.
- Stores the result of calling `checkout.complete(started.intent_id)` in `order`.
- Checks that `(order.status, order.payment_method_id)` equals `('succeeded', 'pm_' + '0' * 24)`; if not, the test fails.
- Checks that `orders.find(started.intent_id).payment_method_id.startswith('pm_')`; if not, the test fails.

`tests/unit/application/test_checkout_proof_pack.py` lines 46 to 50:

```python
def test_a_declined_payment_is_recorded_as_failed(parts):
    provider, _, checkout = parts
    started = checkout.start()
    provider.decline = True
    assert checkout.complete(started.intent_id).status == "failed"
```

**Test `test_a_declined_payment_is_recorded_as_failed`** checks: a declined payment is recorded as failed.

It takes: `parts`.

Step by step:

- Unpacks `parts` into `(provider, _, checkout)`.
- Stores the result of calling `checkout.start()` in `started`.
- Stores `True` in `provider.decline`.
- Checks that `checkout.complete(started.intent_id).status` equals `'failed'`; if not, the test fails.

`tests/unit/application/test_checkout_proof_pack.py` lines 53 to 58:

```python
@pytest.mark.parametrize("bad", ["", TEST_CARD, "pi_short", "../etc/passwd", "pm_" + "a" * 24 + "' OR 1=1"])
def test_anything_that_is_not_a_token_is_refused_before_it_reaches_the_provider(parts, bad):
    provider, _, checkout = parts
    with pytest.raises(PaymentError, match="not a payment token"):
        checkout.complete(bad)
    assert provider.calls == []
```

> **In plain words.** `@pytest.mark.parametrize` runs the same test function once for each row of data given; a failure names the row that broke.
> **In plain words.** `with pytest.raises(Error):` expects the code inside to raise that error; the test fails if it does not.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).

**Test `test_anything_that_is_not_a_token_is_refused_before_it_reaches_the_provider`** checks: anything that is not a token is refused before it reaches the provider.

It takes: `parts`; `bad`.

Decorators: `@pytest.mark.parametrize('bad', ['', TEST_CARD, 'pi_short', '../etc/pa…`.

Step by step:

- Unpacks `parts` into `(provider, _, checkout)`.
- Expects the steps inside to raise the error in `pytest.raises(PaymentError, match='not a payment token')`:
  - Calls `checkout.complete(bad)`.
- Checks that `provider.calls` equals `[]`; if not, the test fails.

`tests/unit/application/test_checkout_proof_pack.py` lines 61 to 63:

```python
def test_an_unknown_token_is_an_unknown_payment(parts):
    with pytest.raises(PaymentError, match="unknown payment"):
        parts[2].complete("pi_" + "9" * 24)
```

**Test `test_an_unknown_token_is_an_unknown_payment`** checks: an unknown token is an unknown payment.

It takes: `parts`.

Step by step:

- Expects the steps inside to raise the error in `pytest.raises(PaymentError, match='unknown payment')`:
  - Calls `parts[2].complete('pi_' + '9' * 24)`.

`tests/unit/application/test_checkout_proof_pack.py` lines 66 to 74:

```python
def test_a_repeat_charge_needs_only_the_customer_and_method_tokens(parts):
    provider, _, checkout = parts
    first = checkout.start()
    checkout.complete(first.intent_id)
    again = checkout.charge_again(first.intent_id)
    assert again.status == "succeeded"
    assert again.payment_intent_id != first.intent_id
    assert provider.calls[-1][0] == "charge_saved"
    assert provider.calls[-1][1][:2] == (again.customer_id, again.payment_method_id)
```

> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.

**Test `test_a_repeat_charge_needs_only_the_customer_and_method_tokens`** checks: a repeat charge needs only the customer and method tokens.

It takes: `parts`.

Step by step:

- Unpacks `parts` into `(provider, _, checkout)`.
- Stores the result of calling `checkout.start()` in `first`.
- Calls `checkout.complete(first.intent_id)`.
- Stores the result of calling `checkout.charge_again(first.intent_id)` in `again`.
- Checks that `again.status` equals `'succeeded'`; if not, the test fails.
- Checks that `again.payment_intent_id` is different from `first.intent_id`; if not, the test fails.
- Checks that `provider.calls[-1][0]` equals `'charge_saved'`; if not, the test fails.
- Checks that `provider.calls[-1][1][:2]` equals `(again.customer_id, again.payment_method_id)`; if not, the test fails.

`tests/unit/application/test_checkout_proof_pack.py` lines 77 to 81:

```python
def test_a_repeat_charge_without_a_saved_method_is_refused(parts):
    _, _, checkout = parts
    first = checkout.start()
    with pytest.raises(PaymentError, match="no saved payment method"):
        checkout.charge_again(first.intent_id)
```

**Test `test_a_repeat_charge_without_a_saved_method_is_refused`** checks: a repeat charge without a saved method is refused.

It takes: `parts`.

Step by step:

- Unpacks `parts` into `(_, _, checkout)`.
- Stores the result of calling `checkout.start()` in `first`.
- Expects the steps inside to raise the error in `pytest.raises(PaymentError, match='no saved payment method')`:
  - Calls `checkout.charge_again(first.intent_id)`.

`tests/unit/application/test_checkout_proof_pack.py` lines 84 to 90:

```python
def test_a_declined_repeat_charge_surfaces_the_providers_message(parts):
    provider, _, checkout = parts
    first = checkout.start()
    checkout.complete(first.intent_id)
    provider.decline = True
    with pytest.raises(PaymentError, match="declined"):
        checkout.charge_again(first.intent_id)
```

**Test `test_a_declined_repeat_charge_surfaces_the_providers_message`** checks: a declined repeat charge surfaces the providers message.

It takes: `parts`.

Step by step:

- Unpacks `parts` into `(provider, _, checkout)`.
- Stores the result of calling `checkout.start()` in `first`.
- Calls `checkout.complete(first.intent_id)`.
- Stores `True` in `provider.decline`.
- Expects the steps inside to raise the error in `pytest.raises(PaymentError, match='declined')`:
  - Calls `checkout.charge_again(first.intent_id)`.

`tests/unit/application/test_checkout_proof_pack.py` lines 93 to 99:

```python
def test_a_refund_needs_only_the_token(parts):
    provider, orders, checkout = parts
    first = checkout.start()
    checkout.complete(first.intent_id)
    assert checkout.refund(first.intent_id).startswith("re_")
    assert orders.find(first.intent_id).status == "refunded"
    assert provider.calls[-1] == ("refund", (first.intent_id,))
```

**Test `test_a_refund_needs_only_the_token`** checks: a refund needs only the token.

It takes: `parts`.

Step by step:

- Unpacks `parts` into `(provider, orders, checkout)`.
- Stores the result of calling `checkout.start()` in `first`.
- Calls `checkout.complete(first.intent_id)`.
- Checks that `checkout.refund(first.intent_id).startswith('re_')`; if not, the test fails.
- Checks that `orders.find(first.intent_id).status` equals `'refunded'`; if not, the test fails.
- Checks that `provider.calls[-1]` equals `('refund', (first.intent_id,))`; if not, the test fails.

`tests/unit/application/test_checkout_proof_pack.py` lines 102 to 103:

```python
def event(kind, intent_id, **extra):
    return json.dumps({"type": kind, "data": {"object": {"id": intent_id, **extra}}}).encode()
```

> **In plain words.** A **dictionary** `{key: value}` maps keys to values.

**Function `event`.**

It takes: `kind`; `intent_id`; `**extra` (any extra named values).

Step by step:

- Gives back the result of calling `json.dumps({'type': kind, 'data': {'object': {'id': intent_id, **extra}}}).encode()`.

`tests/unit/application/test_checkout_proof_pack.py` lines 106 to 116:

```python
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
```

**Test `test_a_signed_event_updates_the_order_and_repeating_it_changes_nothing`** checks: a signed event updates the order and repeating it changes nothing.

It takes: `parts`.

Step by step:

- Unpacks `parts` into `(_, orders, checkout)`.
- Stores the result of calling `checkout.start()` in `started`.
- Stores the result of calling `event('payment_intent.succeeded', started.intent_id, payment_method='pm_' + '1' * 24)` in `body`.
- Stores the result of calling `sign(SECRET, body, 5000)` in `header`.
- Checks that `checkout.handle_event(body, header, 5000)` equals `'applied: payment_intent.succeeded'`; if not, the test fails.
- Checks that `checkout.handle_event(body, header, 5001)` equals `'applied: payment_intent.succeeded'`; if not, the test fails.
- Checks that `(orders.find(started.intent_id).status, orders.fi…` equals `('succeeded', 'pm_' + '1' * 24)`; if not, the test fails.

`tests/unit/application/test_checkout_proof_pack.py` lines 119 to 123:

```python
def test_a_failed_event_marks_the_order_failed(parts):
    started = parts[2].start()
    body = event("payment_intent.payment_failed", started.intent_id)
    assert parts[2].handle_event(body, sign(SECRET, body, 5_000), 5_000) == "applied: payment_intent.payment_failed"
    assert parts[1].find(started.intent_id).status == "failed"
```

**Test `test_a_failed_event_marks_the_order_failed`** checks: a failed event marks the order failed.

It takes: `parts`.

Step by step:

- Stores the result of calling `parts[2].start()` in `started`.
- Stores the result of calling `event('payment_intent.payment_failed', started.intent_id)` in `body`.
- Checks that `parts[2].handle_event(body, sign(SECRET, body, 50…` equals `'applied: payment_intent.payment_failed'`; if not, the test fails.
- Checks that `parts[1].find(started.intent_id).status` equals `'failed'`; if not, the test fails.

`tests/unit/application/test_checkout_proof_pack.py` lines 126 to 132:

```python
def test_unknown_payments_and_other_event_types_are_ignored(parts):
    _, _, checkout = parts
    started = checkout.start()
    unknown = event("payment_intent.succeeded", "pi_" + "8" * 24)
    assert checkout.handle_event(unknown, sign(SECRET, unknown, 5_000), 5_000) == "ignored: unknown payment"
    other = event("charge.dispute.created", started.intent_id)
    assert checkout.handle_event(other, sign(SECRET, other, 5_000), 5_000) == "ignored: charge.dispute.created"
```

**Test `test_unknown_payments_and_other_event_types_are_ignored`** checks: unknown payments and other event types are ignored.

It takes: `parts`.

Step by step:

- Unpacks `parts` into `(_, _, checkout)`.
- Stores the result of calling `checkout.start()` in `started`.
- Stores the result of calling `event('payment_intent.succeeded', 'pi_' + '8' * 24)` in `unknown`.
- Checks that `checkout.handle_event(unknown, sign(SECRET, unkno…` equals `'ignored: unknown payment'`; if not, the test fails.
- Stores the result of calling `event('charge.dispute.created', started.intent_id)` in `other`.
- Checks that `checkout.handle_event(other, sign(SECRET, other, …` equals `'ignored: charge.dispute.created'`; if not, the test fails.

`tests/unit/application/test_checkout_proof_pack.py` lines 135 to 139:

```python
@pytest.mark.parametrize("header", [None, "t=5000,v1=deadbeef"])
def test_an_event_with_a_bad_signature_is_refused(parts, header):
    started = parts[2].start()
    with pytest.raises(PaymentError, match="signature"):
        parts[2].handle_event(event("payment_intent.succeeded", started.intent_id), header, 5_000)
```

**Test `test_an_event_with_a_bad_signature_is_refused`** checks: an event with a bad signature is refused.

It takes: `parts`; `header`.

Decorators: `@pytest.mark.parametrize('header', [None, 't=5000,v1=deadbeef'])`.

Step by step:

- Stores the result of calling `parts[2].start()` in `started`.
- Expects the steps inside to raise the error in `pytest.raises(PaymentError, match='signature')`:
  - Calls `parts[2].handle_event(event('payment_intent.succeeded', started.intent_id), header, 5000)`.

`tests/unit/application/test_checkout_proof_pack.py` lines 142 to 147:

```python
class Reader:
    def __init__(self, items):
        self.items = items

    def artifacts(self):
        yield from self.items
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** `yield` makes a function a **generator**: calling it returns an iterator that hands out one value at a time and remembers where it stopped.

**Class `Reader`**.

Its methods, in order:

**Method `__init__` of class `Reader`.**

It takes: `items`.

Step by step:

- Stores `items` in `self.items`.

**Method `artifacts` of class `Reader`.**

Step by step:

- Evaluates `(yield from self.items)`.

`tests/unit/application/test_checkout_proof_pack.py` lines 150 to 155:

```python
def test_a_scan_reports_clean_places_and_the_exit_code():
    outcome = run_scan("scanning:", Reader([("a.log", "created payment pi_x"), ("b.sql", "INSERT 1")]))
    assert (
        outcome.text == "scanning:\n  a.log ... clean\n  b.sql ... clean\nscanned 2 artifact(s): 0 findings\nexit=0\n"
    )
    assert (outcome.exit_code, outcome.artifacts) == (0, 2)
```

**Test `test_a_scan_reports_clean_places_and_the_exit_code`** checks: a scan reports clean places and the exit code.

Step by step:

- Stores the result of calling `run_scan('scanning:', Reader([('a.log', 'created payment pi_x'), ('b.sql', 'INSERT 1')]))` in `outcome`.
- Checks that `outcome.text` equals `'scanning:\n a.log ... clean\n b.sql ... clean\ns…`; if not, the test fails.
- Checks that `(outcome.exit_code, outcome.artifacts)` equals `(0, 2)`; if not, the test fails.

`tests/unit/application/test_checkout_proof_pack.py` lines 158 to 162:

```python
def test_a_scan_that_finds_a_card_reports_a_masked_evidence_and_exits_1():
    outcome = run_scan("scanning:", Reader([("req.log", f"INFO payment request: {TEST_CARD}")]))
    assert "req.log:1 FOUND card number 424242******4242" in outcome.text
    assert TEST_CARD not in outcome.text
    assert outcome.exit_code == 1
```

> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Test `test_a_scan_that_finds_a_card_reports_a_masked_evidence_and_exits_1`** checks: a scan that finds a card reports a masked evidence and exits 1.

Step by step:

- Stores the result of calling `run_scan('scanning:', Reader([('req.log', f'INFO payment request: {TEST_CARD}')]))` in `outcome`.
- Checks that `'req.log:1 FOUND card number 424242******4242'` is in `outcome.text`; if not, the test fails.
- Checks that `TEST_CARD` is not in `outcome.text`; if not, the test fails.
- Checks that `outcome.exit_code` equals `1`; if not, the test fails.

`tests/unit/application/test_checkout_proof_pack.py` lines 165 to 172:

```python
def test_the_scope_documents_come_from_the_inventories():
    docs = scope_documents(
        load_inventory(REPOSITORY_ROOT / "scope" / "before.toml"),
        load_inventory(REPOSITORY_ROOT / "scope" / "after.toml"),
    )
    assert set(docs) == {"scope-before.md", "scope-after.md", "scope-change.md"}
    assert "**9 systems and 3 teams in scope**" in docs["scope-before.md"]
    assert "**3 systems and 2 teams in scope**" in docs["scope-after.md"]
```

> **In plain words.** A **set** `{a, b}` holds items without duplicates; `frozenset` is a set that cannot be changed.

**Test `test_the_scope_documents_come_from_the_inventories`** checks: the scope documents come from the inventories.

Step by step:

- Stores the result of calling `scope_documents(load_inventory(REPOSITORY_ROOT / 'scope' / 'before.toml'), load_inventory…` in `docs`.
- Checks that `set(docs)` equals `{'scope-before.md', 'scope-after.md', 'scope-chan…`; if not, the test fails.
- Checks that `'**9 systems and 3 teams in scope**'` is in `docs['scope-before.md']`; if not, the test fails.
- Checks that `'**3 systems and 2 teams in scope**'` is in `docs['scope-after.md']`; if not, the test fails.

`tests/unit/application/test_checkout_proof_pack.py` lines 175 to 187:

```python
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
```

**Test `test_the_small_reports_render`** checks: the small reports render.

Step by step:

- Checks that `render_routes([('POST', '/pay', 404)]).endswith('POST /pay -> 404\n')`; if not, the test fails.
- Stores the result of calling `render_page_controls('http://m/', 200, {'Content-Security-Policy': 'script-src http://p'}…` in `page`.
- Checks that `'content-security-policy: script-src http://p'` is in `page`; if not, the test fails.
- Checks that `'referrer-policy: (missing)'` is in `page`; if not, the test fails.
- Checks that `"script http://p/x.js (the provider's)"` is in `page`; if not, the test fails.
- Checks that `'script /a.js (ours)'` is in `page`; if not, the test fails.
- Checks that `page.rstrip().endswith("card input fields on the merchant's page: non…`; if not, the test fails.
- Stores the result of calling `render_token_storage([('id', 'INTEGER')], [(1, 'pi_x')], [])` in `tokens`.
- Checks that `' id INTEGER'` is in `tokens`; if not, the test fails.
- Checks that `tokens.rstrip().endswith('card number columns: none')`; if not, the test fails.

`tests/unit/application/test_checkout_proof_pack.py` lines 190 to 202:

```python
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
```

**Test `test_the_index_lists_each_file_with_its_requirement_and_the_gaps`** checks: the index lists each file with its requirement and the gaps.

Step by step:

- Stores the result of calling `datetime(2026, 10, 27, 9, 0, tzinfo=UTC)` in `when`.
- Stores the list `[Requirement('P1', 't', (EvidenceSpec('a.txt', 'scan_after', 'proves …` in `requirements`.
- Stores the dictionary `{'a.txt': ManifestEntry('a.txt', 'P1', when, 'x' * 64)}` in `manifest`.
- Stores the result of calling `render_index(requirements, manifest, [Gap('P7', 'no attestation', 'PCI-1', when.date())],…` in `index`.
- Checks that `'| a.txt | P1 | proves a | 2026-10-27 |'` is in `index`; if not, the test fails.
- Checks that `'| b.txt | P1 | proves b | not produced |'` is in `index`; if not, the test fails.
- Checks that `'- P7: no attestation Ticket PCI-1, due 2026-10-2…` is in `index`; if not, the test fails.
- Checks that `'None.'` is in `render_index(requirements, manifest, [], when)`; if not, the test fails.

## Try it yourself

```bash
.venv/bin/pytest -q tests/unit/application
```
Prints a row of dots, one per passing test, and a summary line such as `N passed in 0.5s` (skipped tests show as `s`).

```bash
.venv/bin/mypy
```
Checks the whole project (the `files` setting in `pyproject.toml`), these files included. Prints `Success: no issues found in 46 source files`.

```bash
.venv/bin/ruff check tests/unit/application/test_checkout_proof_pack.py
```
Prints `All checks passed!`.

## Mistakes people make

- Tests that depend on each other's order. Each test here builds its own data.
- Asserting only the happy path. These tests also break the input on purpose and check the exact rule that fails.
- Forgetting `test_` in a name, so the test never runs.

## Check yourself

1. What does the test `test_starting_a_checkout_creates_a_customer_and_an_intent_at_the_fixed_price` check?
   **Answer:** it checks: starting a checkout creates a customer and an intent at the fixed price.
2. What does the test `test_the_result_comes_from_the_provider_and_the_method_token_is_saved` check?
   **Answer:** it checks: the result comes from the provider and the method token is saved.
3. What does the test `test_a_declined_payment_is_recorded_as_failed` check?
   **Answer:** it checks: a declined payment is recorded as failed.
4. What does the test `test_anything_that_is_not_a_token_is_refused_before_it_reaches_the_provider` check?
   **Answer:** it checks: anything that is not a token is refused before it reaches the provider.
5. What does the test `test_an_unknown_token_is_an_unknown_payment` check?
   **Answer:** it checks: an unknown token is an unknown payment.

## Further reading

- pytest 9.1 documentation: <https://docs.pytest.org/en/stable/>
- How to use fixtures: <https://docs.pytest.org/en/stable/how-to/fixtures.html>
- `assert` rewriting: <https://docs.pytest.org/en/stable/how-to/assert.html>
