# The tests (domain)

## What it is

The pytest tests in `tests/unit/domain`. Each function whose name starts with `test_` is one check; pytest finds and runs them. (Every term is explained where it first appears in the walkthrough below.)

## Why this repository uses it

The tests turn every rule, adapter and command of this repository into something that can fail. A rule without a test is only a claim.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/unit/domain/test_card_scope_webhook_har.py` | 170 lines.  |
| `tests/unit/domain/test_evidence_rules.py` | 119 lines.  |

## How it works underneath

pytest imports each `test_*.py` file, builds the fixtures a test asks for by parameter name, runs the function, and counts it as passed when no `assert` fails and nothing raises. A fixture such as `tmp_path` or `monkeypatch` is prepared fresh for each test, so tests do not affect each other.

## Walkthrough of this repository's use

### `tests/unit/domain/test_card_scope_webhook_har.py`

`tests/unit/domain/test_card_scope_webhook_har.py` lines 1 to 21:

```python
import json

import pytest

from pci_scope.domain.card import TEST_CARD, card_field_names, luhn_valid, mask, scan_text
from pci_scope.domain.har import Exchange, merchant_exposure, origin, parse_har, reaches_provider, summarize, to_har
from pci_scope.domain.payment import is_token
from pci_scope.domain.scope import (
    CONTROL,
    DATA,
    Edge,
    Inventory,
    System,
    compare_scope,
    compute_scope,
    render_mermaid,
    render_scope_report,
)
from pci_scope.domain.webhook import sign, verify
from pci_scope.infrastructure.catalog import load_inventory
from tests.conftest import REPOSITORY_ROOT, SECRET
```

> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.

Imports:

- It imports module `json`.
- It imports module `pytest`.
- From `pci_scope.domain.card` it takes `TEST_CARD, card_field_names, luhn_valid, mask, scan_text`.
- From `pci_scope.domain.har` it takes `Exchange, merchant_exposure, origin, parse_har, reaches_provider, summarize, to_har`.
- From `pci_scope.domain.payment` it takes `is_token`.
- From `pci_scope.domain.scope` it takes `CONTROL, DATA, Edge, Inventory, System, compare_scope, compute_scope, render_mermaid, render_scope_report`.
- From `pci_scope.domain.webhook` it takes `sign, verify`.
- From `pci_scope.infrastructure.catalog` it takes `load_inventory`.
- From `tests.conftest` it takes `REPOSITORY_ROOT, SECRET`.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 24 to 26:

```python
@pytest.mark.parametrize("number", [TEST_CARD, "4000000000000002", "378282246310005", "5555555555554444"])
def test_published_test_numbers_pass_the_luhn_check(number):
    assert luhn_valid(number)
```

> **In plain words.** `@pytest.mark.parametrize` runs the same test function once for each row of data given; a failure names the row that broke.
> **In plain words.** `assert condition` checks that something is true. In a test, a false condition fails the test and pytest shows both sides of the comparison.
> **In plain words.** A **test** is a function whose name starts with `test_`. pytest finds it, runs it, and reports a pass when no `assert` fails and nothing raises.

**Test `test_published_test_numbers_pass_the_luhn_check`** checks: published test numbers pass the luhn check.

It takes: `number`.

Decorators: `@pytest.mark.parametrize('number', [TEST_CARD, '4000000000000002', '37…`.

Step by step:

- Checks that `luhn_valid(number)`; if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 29 to 31:

```python
@pytest.mark.parametrize("number", ["4242424242424241", "1234567890123456", "abcd", ""])
def test_other_numbers_do_not(number):
    assert not luhn_valid(number)
```

**Test `test_other_numbers_do_not`** checks: other numbers do not.

It takes: `number`.

Decorators: `@pytest.mark.parametrize('number', ['4242424242424241', '1234567890123…`.

Step by step:

- Checks that not (`luhn_valid(number)`); if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 34 to 35:

```python
def test_a_mask_keeps_six_and_four_digits_only():
    assert mask(TEST_CARD) == "424242******4242"
```

> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.

**Test `test_a_mask_keeps_six_and_four_digits_only`** checks: a mask keeps six and four digits only.

Step by step:

- Checks that `mask(TEST_CARD)` equals `'424242******4242'`; if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 38 to 51:

```python
@pytest.mark.parametrize(
    "line",
    [
        "payment request: 4242424242424242",
        "card 4242 4242 4242 4242 ok",
        "card 4242-4242-4242-4242 ok",
        "{'card_number': '4242424242424242', 'expiry': '12/30', 'cvv': '123'}",
        "card%5Bnumber%5D=4242424242424242",
    ],
)
def test_a_card_number_in_any_common_form_is_found_and_only_its_mask_is_reported(line):
    findings = scan_text("log", line)
    assert any(f.kind == "card number" and f.evidence == "424242******4242" for f in findings)
    assert "4242424242424242" not in repr(findings)
```

> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.

**Test `test_a_card_number_in_any_common_form_is_found_and_only_its_mask_is_reported`** checks: a card number in any common form is found and only its mask is reported.

It takes: `line`.

Decorators: `@pytest.mark.parametrize('line', ['payment request: 4242424242424242',…`.

Step by step:

- Stores the result of calling `scan_text('log', line)` in `findings`.
- Checks that `any((f.kind == 'card number' and f.evidence == '424242******4242' for…`; if not, the test fails.
- Checks that `'4242424242424242'` is not in `repr(findings)`; if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 54 to 65:

```python
@pytest.mark.parametrize(
    "line",
    [
        "created payment pi_3f9a1c0e7d2b4a5c6e8f0a1b amount=1900 eur",
        "order 1730000000000 shipped",
        "2026-10-27T00:40:19Z user=ada id=1",
        "phone 0044 7700 900123",
        "amount=4242",
    ],
)
def test_ordinary_log_lines_are_not_flagged(line):
    assert scan_text("log", line) == []
```

**Test `test_ordinary_log_lines_are_not_flagged`** checks: ordinary log lines are not flagged.

It takes: `line`.

Decorators: `@pytest.mark.parametrize('line', ['created payment pi_3f9a1c0e7d2b4a5c…`.

Step by step:

- Checks that `scan_text('log', line)` equals `[]`; if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 68 to 71:

```python
def test_card_fields_with_a_value_are_found_by_name_only():
    findings = scan_text("log", "form: cvv=123 and CVC: 456 and card_number=nothing")
    assert sorted(f.evidence for f in findings) == ["card_number", "cvc", "cvv"]
    assert all(f.kind == "card field" for f in findings)
```

**Test `test_card_fields_with_a_value_are_found_by_name_only`** checks: card fields with a value are found by name only.

Step by step:

- Stores the result of calling `scan_text('log', 'form: cvv=123 and CVC: 456 and card_number=nothing')` in `findings`.
- Checks that `sorted((f.evidence for f in findings))` equals `['card_number', 'cvc', 'cvv']`; if not, the test fails.
- Checks that `all((f.kind == 'card field' for f in findings))`; if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 74 to 75:

```python
def test_findings_say_the_line():
    assert scan_text("a.log", "ok\nnext\ncvv=1")[0].line == 3
```

> **In plain words.** `obj[key]` looks a value up by key or position.

**Test `test_findings_say_the_line`** checks: findings say the line.

Step by step:

- Checks that `scan_text('a.log', 'ok\nnext\ncvv=1')[0].line` equals `3`; if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 78 to 81:

```python
def test_field_names_are_read_from_forms_pages_and_encoded_bodies():
    assert card_field_names('<input name="card_number"> <input name="cvv">') == ["card_number", "cvv"]
    assert card_field_names("card%5Bnumber%5D=x&card%5Bcvc%5D=y") == ["card[cvc]", "card[number]"]
    assert card_field_names("amount=1900&currency=eur") == []
```

**Test `test_field_names_are_read_from_forms_pages_and_encoded_bodies`** checks: field names are read from forms pages and encoded bodies.

Step by step:

- Checks that `card_field_names('<input name="card_number"> <inp…` equals `['card_number', 'cvv']`; if not, the test fails.
- Checks that `card_field_names('card%5Bnumber%5D=x&card%5Bcvc%5…` equals `['card[cvc]', 'card[number]']`; if not, the test fails.
- Checks that `card_field_names('amount=1900&currency=eur')` equals `[]`; if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 84 to 89:

```python
def test_tokens_are_recognized_and_numbers_are_not():
    assert is_token("pi_" + "a" * 24)
    assert is_token("pm_" + "0" * 24)
    assert not is_token(TEST_CARD)
    assert not is_token("pm_short")
    assert not is_token("pm_" + "a" * 24 + "; DROP TABLE")
```

**Test `test_tokens_are_recognized_and_numbers_are_not`** checks: tokens are recognized and numbers are not.

Step by step:

- Checks that `is_token('pi_' + 'a' * 24)`; if not, the test fails.
- Checks that `is_token('pm_' + '0' * 24)`; if not, the test fails.
- Checks that not (`is_token(TEST_CARD)`); if not, the test fails.
- Checks that not (`is_token('pm_short')`); if not, the test fails.
- Checks that not (`is_token('pm_' + 'a' * 24 + '; DROP TABLE')`); if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 92 to 93:

```python
BEFORE = load_inventory(REPOSITORY_ROOT / "scope" / "before.toml")
AFTER = load_inventory(REPOSITORY_ROOT / "scope" / "after.toml")
```

> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the result of calling `load_inventory(REPOSITORY_ROOT / 'scope' / 'before.toml')` in `BEFORE`.
- Stores the result of calling `load_inventory(REPOSITORY_ROOT / 'scope' / 'after.toml')` in `AFTER`.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 96 to 100:

```python
def test_the_naive_checkout_puts_nine_systems_and_three_teams_in_scope():
    result = compute_scope(BEFORE)
    assert len(result.systems) == 9
    assert result.teams == ("developers", "operations", "support")
    assert "browser" not in result.ids
```

> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Test `test_the_naive_checkout_puts_nine_systems_and_three_teams_in_scope`** checks: the naive checkout puts nine systems and three teams in scope.

Step by step:

- Stores the result of calling `compute_scope(BEFORE)` in `result`.
- Checks that `len(result.systems)` equals `9`; if not, the test fails.
- Checks that `result.teams` equals `('developers', 'operations', 'support')`; if not, the test fails.
- Checks that `'browser'` is not in `result.ids`; if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 103 to 109:

```python
def test_every_system_the_card_touches_or_that_can_change_one_is_in_scope_with_a_reason():
    reasons = {system.id: why for system, why in compute_scope(BEFORE).systems}
    assert reasons["web"] == ("card data reaches it",)
    assert reasons["search"] == ("card data reaches it from Log shipping",)
    assert reasons["laptops"] == ("card data reaches it from Log search tool",)
    assert reasons["ci"] == ("can change Web server (naive.py)",)
    assert reasons["admin"] == ("can change Web server (naive.py)",)
```

> **In plain words.** A **dictionary comprehension** `{k: v for ...}` builds a dictionary with a loop written inside braces.

**Test `test_every_system_the_card_touches_or_that_can_change_one_is_in_scope_with_a_reason`** checks: every system the card touches or that can change one is in scope with a reason.

Step by step:

- Stores a new dictionary made by a loop (`{system.id: why for system, why in compute_scope(BEFORE).systems}`) in `reasons`.
- Checks that `reasons['web']` equals `('card data reaches it',)`; if not, the test fails.
- Checks that `reasons['search']` equals `('card data reaches it from Log shipping',)`; if not, the test fails.
- Checks that `reasons['laptops']` equals `('card data reaches it from Log search tool',)`; if not, the test fails.
- Checks that `reasons['ci']` equals `('can change Web server (naive.py)',)`; if not, the test fails.
- Checks that `reasons['admin']` equals `('can change Web server (naive.py)',)`; if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 112 to 115:

```python
def test_after_the_redesign_only_the_page_its_pipeline_and_its_admins_remain():
    result = compute_scope(AFTER)
    assert result.ids == {"web", "ci", "admin"}
    assert result.teams == ("developers", "operations")
```

> **In plain words.** A **set** `{a, b}` holds items without duplicates; `frozenset` is a set that cannot be changed.

**Test `test_after_the_redesign_only_the_page_its_pipeline_and_its_admins_remain`** checks: after the redesign only the page its pipeline and its admins remain.

Step by step:

- Stores the result of calling `compute_scope(AFTER)` in `result`.
- Checks that `result.ids` equals `{'web', 'ci', 'admin'}`; if not, the test fails.
- Checks that `result.teams` equals `('developers', 'operations')`; if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 118 to 124:

```python
def test_the_comparison_names_what_left_and_what_stays():
    text = compare_scope(compute_scope(BEFORE), compute_scope(AFTER))
    assert "Before: 9 systems and 3 teams in scope." in text
    assert "After: 3 systems and 2 teams in scope." in text
    left = "Request log, Log shipping, Log search tool, Order database, Backups, Developer laptops that read logs"
    assert f"Left scope: {left}." in text
    assert "Web server (serves the checkout page) (serves the page that loads the provider's script)" in text
```

> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Test `test_the_comparison_names_what_left_and_what_stays`** checks: the comparison names what left and what stays.

Step by step:

- Stores the result of calling `compare_scope(compute_scope(BEFORE), compute_scope(AFTER))` in `text`.
- Checks that `'Before: 9 systems and 3 teams in scope.'` is in `text`; if not, the test fails.
- Checks that `'After: 3 systems and 2 teams in scope.'` is in `text`; if not, the test fails.
- Stores the text `'Request log, Log shipping, Log search tool, Order database…` in `left`.
- Checks that `f'Left scope: {left}.'` is in `text`; if not, the test fails.
- Checks that `"Web server (serves the checkout page) (serves th…` is in `text`; if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 127 to 136:

````python
def test_the_reports_and_the_diagram_render():
    report = render_scope_report(AFTER, compute_scope(AFTER))
    assert "**3 systems and 2 teams in scope**" in report
    assert "```mermaid" in report
    assert "Out of scope: Request log" in report
    diagram = render_mermaid(AFTER, compute_scope(AFTER))
    assert 'subgraph cde["In scope"]' in diagram
    assert "browser -->|card data| provider" in diagram
    assert "ci -.->|can change| web" in diagram
    assert "(provider)" in diagram
````

**Test `test_the_reports_and_the_diagram_render`** checks: the reports and the diagram render.

Step by step:

- Stores the result of calling `render_scope_report(AFTER, compute_scope(AFTER))` in `report`.
- Checks that `'**3 systems and 2 teams in scope**'` is in `report`; if not, the test fails.
- Checks that `'```mermaid'` is in `report`; if not, the test fails.
- Checks that `'Out of scope: Request log'` is in `report`; if not, the test fails.
- Stores the result of calling `render_mermaid(AFTER, compute_scope(AFTER))` in `diagram`.
- Checks that `'subgraph cde["In scope"]'` is in `diagram`; if not, the test fails.
- Checks that `'browser -->|card data| provider'` is in `diagram`; if not, the test fails.
- Checks that `'ci -.->|can change| web'` is in `diagram`; if not, the test fails.
- Checks that `'(provider)'` is in `diagram`; if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 139 to 145:

```python
def test_cycles_terminate_and_an_empty_scope_renders():
    a, b = System("a", "A", "t", touches_card=True), System("b", "B", "t")
    loop = Inventory("loop", (a, b), (Edge("a", "b", DATA), Edge("b", "a", DATA), Edge("b", "a", CONTROL)))
    assert compute_scope(loop).ids == {"a", "b"}
    nothing = Inventory("none", (System("x", "X", "t"),), ())
    assert compute_scope(nothing).systems == ()
    assert "nothing" in render_mermaid(nothing, compute_scope(nothing))
```

> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).

**Test `test_cycles_terminate_and_an_empty_scope_renders`** checks: cycles terminate and an empty scope renders.

Step by step:

- Unpacks the tuple `(System('a', 'A', 't', touches_card=True), System('b', 'B', 't'))` into `(a, b)`.
- Stores the result of calling `Inventory('loop', (a, b), (Edge('a', 'b', DATA), Edge('b', 'a', DATA), Edge('b', 'a', CON…` in `loop`.
- Checks that `compute_scope(loop).ids` equals `{'a', 'b'}`; if not, the test fails.
- Stores the result of calling `Inventory('none', (System('x', 'X', 't'),), ())` in `nothing`.
- Checks that `compute_scope(nothing).systems` equals `()`; if not, the test fails.
- Checks that `'nothing'` is in `render_mermaid(nothing, compute_scope(nothing))`; if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 148 to 153:

```python
def test_a_signature_made_with_the_secret_verifies_within_five_minutes():
    body = b'{"type":"payment_intent.succeeded"}'
    header = sign(SECRET, body, 1_000)
    assert header.startswith("t=1000,v1=")
    assert verify(SECRET, body, header, now=1_000 + 299)
    assert verify(SECRET, body, header, now=1_000 - 299)
```

**Test `test_a_signature_made_with_the_secret_verifies_within_five_minutes`** checks: a signature made with the secret verifies within five minutes.

Step by step:

- Stores the number `b'{"type":"payment_intent.succeeded"}'` in `body`.
- Stores the result of calling `sign(SECRET, body, 1000)` in `header`.
- Checks that `header.startswith('t=1000,v1=')`; if not, the test fails.
- Checks that `verify(SECRET, body, header, now=1000 + 299)`; if not, the test fails.
- Checks that `verify(SECRET, body, header, now=1000 - 299)`; if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 156 to 170:

```python
@pytest.mark.parametrize(
    ("body", "header", "now"),
    [
        (b"{}", None, 1_000),
        (b"{}", "", 1_000),
        (b"{}", "garbage", 1_000),
        (b"{}", "t=abc,v1=00", 1_000),
        (b"{}", "t=1000", 1_000),
        (b"{ }", sign(SECRET, b"{}", 1_000), 1_000),
        (b"{}", sign(SECRET, b"{}", 1_000), 1_000 + 301),
        (b"{}", sign("another-secret-value-0123456789abcdef", b"{}", 1_000), 1_000),
    ],
)
def test_a_missing_forged_tampered_or_old_signature_is_refused(body, header, now):
    assert not verify(SECRET, body, header, now)
```

**Test `test_a_missing_forged_tampered_or_old_signature_is_refused`** checks: a missing forged tampered or old signature is refused.

It takes: `body`; `header`; `now`.

Decorators: `@pytest.mark.parametrize(('body', 'header', 'now'), [(b'{}', None, 100…`.

Step by step:

- Checks that not (`verify(SECRET, body, header, now)`); if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 173 to 173:

```python
MERCHANT, PROVIDER = "http://127.0.0.1:5000", "http://127.0.0.1:5001"
```

These module-level lines:

- Unpacks the tuple `('http://127.0.0.1:5000', 'http://127.0.0.1:5001')` into `(MERCHANT, PROVIDER)`.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 176 to 182:

```python
def exchanges(card_to_merchant=False):
    return [
        Exchange("GET", f"{MERCHANT}/", 200, ""),
        Exchange("POST", f"{MERCHANT}/create-payment", 200, "card_number=4242424242424242" if card_to_merchant else ""),
        Exchange("POST", f"{PROVIDER}/v1/payment_methods", 200, f"card%5Bnumber%5D={TEST_CARD}&card%5Bcvc%5D=123"),
        Exchange("POST", f"{PROVIDER}/v1/payment_intents/pi_x/confirm", 200, "payment_method=pm_x"),
    ]
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.

**Function `exchanges`.**

It takes: `card_to_merchant`, default `False`.

Step by step:

- Gives back the list `[Exchange('GET', f'{MERCHANT}/', 200, ''), Exchange('POST', f'{MERCHA…`.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 185 to 186:

```python
def test_origins_are_scheme_host_and_port():
    assert origin("http://127.0.0.1:5000/done?x=1") == MERCHANT
```

**Test `test_origins_are_scheme_host_and_port`** checks: origins are scheme host and port.

Step by step:

- Checks that `origin('http://127.0.0.1:5000/done?x=1')` equals `MERCHANT`; if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 189 to 196:

```python
def test_the_har_keeps_field_names_sent_to_the_provider_and_drops_their_values():
    har = to_har(exchanges(), frozenset({PROVIDER}))
    assert TEST_CARD not in har
    assert "card%5Bnumber%5D=[redacted]" in har
    assert json.loads(har)["log"]["version"] == "1.2"
    parsed = parse_har(har)
    assert [item.status for item in parsed] == [200, 200, 200, 200]
    assert reaches_provider(parsed, PROVIDER)
```

> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.

**Test `test_the_har_keeps_field_names_sent_to_the_provider_and_drops_their_values`** checks: the har keeps field names sent to the provider and drops their values.

Step by step:

- Stores the result of calling `to_har(exchanges(), frozenset({PROVIDER}))` in `har`.
- Checks that `TEST_CARD` is not in `har`; if not, the test fails.
- Checks that `'card%5Bnumber%5D=[redacted]'` is in `har`; if not, the test fails.
- Checks that `json.loads(har)['log']['version']` equals `'1.2'`; if not, the test fails.
- Stores the result of calling `parse_har(har)` in `parsed`.
- Checks that `[item.status for item in parsed]` equals `[200, 200, 200, 200]`; if not, the test fails.
- Checks that `reaches_provider(parsed, PROVIDER)`; if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 199 to 200:

```python
def test_a_capture_where_the_card_stays_with_the_provider_has_no_exposure():
    assert merchant_exposure(exchanges(), MERCHANT) == []
```

**Test `test_a_capture_where_the_card_stays_with_the_provider_has_no_exposure`** checks: a capture where the card stays with the provider has no exposure.

Step by step:

- Checks that `merchant_exposure(exchanges(), MERCHANT)` equals `[]`; if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 203 to 208:

```python
def test_a_card_sent_to_the_merchant_is_reported():
    assert merchant_exposure(exchanges(card_to_merchant=True), MERCHANT) == [
        f"POST {MERCHANT}/create-payment carries card data"
    ]
    leaked_url = [Exchange("GET", f"{MERCHANT}/done?card={TEST_CARD}", 200, "")]
    assert len(merchant_exposure(leaked_url, MERCHANT)) == 1
```

**Test `test_a_card_sent_to_the_merchant_is_reported`** checks: a card sent to the merchant is reported.

Step by step:

- Checks that `merchant_exposure(exchanges(card_to_merchant=True…` equals `[f'POST {MERCHANT}/create-payment carries card da…`; if not, the test fails.
- Stores the list `[Exchange('GET', f'{MERCHANT}/done?card={TEST_CARD}', 200, '')]` in `leaked_url`.
- Checks that `len(merchant_exposure(leaked_url, MERCHANT))` equals `1`; if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 211 to 212:

```python
def test_a_capture_with_no_card_at_the_provider_does_not_show_the_payment():
    assert not reaches_provider(exchanges()[:2], PROVIDER)
```

> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.

**Test `test_a_capture_with_no_card_at_the_provider_does_not_show_the_payment`** checks: a capture with no card at the provider does not show the payment.

Step by step:

- Checks that not (`reaches_provider(exchanges()[:2], PROVIDER)`); if not, the test fails.

`tests/unit/domain/test_card_scope_webhook_har.py` lines 215 to 224:

```python
def test_the_summary_says_where_each_request_went():
    lines = summarize(exchanges(), MERCHANT, PROVIDER).splitlines()
    assert lines[0].endswith("body: (empty)  -> your server")
    assert "card fields: card[cvc], card[number]  -> the provider" in lines[2]
    assert lines[3].endswith("body: no card fields  -> the provider")
    assert (
        summarize([Exchange("GET", "http://other.example/", 200, "")], MERCHANT, PROVIDER)
        .strip()
        .endswith("-> elsewhere")
    )
```

**Test `test_the_summary_says_where_each_request_went`** checks: the summary says where each request went.

Step by step:

- Stores the result of calling `summarize(exchanges(), MERCHANT, PROVIDER).splitlines()` in `lines`.
- Checks that `lines[0].endswith('body: (empty) -> your server')`; if not, the test fails.
- Checks that `'card fields: card[cvc], card[number] -> the prov…` is in `lines[2]`; if not, the test fails.
- Checks that `lines[3].endswith('body: no card fields -> the provider')`; if not, the test fails.
- Checks that `summarize([Exchange('GET', 'http://other.example/', 200, '')], MERCHA…`; if not, the test fails.

### `tests/unit/domain/test_evidence_rules.py`

`tests/unit/domain/test_evidence_rules.py` lines 1 to 6:

```python
import json
from datetime import UTC, date, datetime

import pytest

from pci_scope.domain.evidence import EvidenceSpec, Gap, ManifestEntry, Requirement, digest, verify_pack
```

> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.

Imports:

- It imports module `json`.
- From `datetime` it takes `UTC, date, datetime`.
- It imports module `pytest`.
- From `pci_scope.domain.evidence` it takes `EvidenceSpec, Gap, ManifestEntry, Requirement, digest, verify_pack`.

`tests/unit/domain/test_evidence_rules.py` lines 8 to 9:

```python
MERCHANT, PROVIDER = "http://m:5000", "http://p:5001"
NOW = datetime(2026, 10, 27, tzinfo=UTC)
```

> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Unpacks the tuple `('http://m:5000', 'http://p:5001')` into `(MERCHANT, PROVIDER)`.
- Stores the result of calling `datetime(2026, 10, 27, tzinfo=UTC)` in `NOW`.

`tests/unit/domain/test_evidence_rules.py` lines 12 to 23:

```python
def har(merchant_body="", provider_body="card%5Bnumber%5D=[redacted]", merchant_url=f"{MERCHANT}/"):
    entries = [
        {
            "request": {"method": "GET", "url": merchant_url, "postData": {"text": merchant_body}},
            "response": {"status": 200},
        },
        {
            "request": {"method": "POST", "url": f"{PROVIDER}/v1/payment_methods", "postData": {"text": provider_body}},
            "response": {"status": 200},
        },
    ]
    return json.dumps({"log": {"entries": entries}})
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.

**Function `har`.**

It takes: `merchant_body`, default `''`; `provider_body`, default `'card%5Bnumber%5D=[redacted]'`; `merchant_url`, default `f'{MERCHANT}/'`.

Step by step:

- Stores the list `[{'request': {'method': 'GET', 'url': merchant_url, 'postData': {'tex…` in `entries`.
- Gives back the result of calling `json.dumps({'log': {'entries': entries}})`.

`tests/unit/domain/test_evidence_rules.py` lines 26 to 45:

````python
HAR_OK = har()
GOOD = {
    "scope": "```mermaid\nx\n```\n**9 systems and 3 teams in scope**",
    "scope_change": (
        "Before: 9 systems and 3 teams in scope.\nAfter: 3 systems and 2 teams in scope.\n"
        "Left scope: a.\nStill in scope: b."
    ),
    "scan_before": "x FOUND card number\nscanned 1 artifact(s): 1 findings\nexit=1",
    "scan_after": "scanned 3 artifact(s): 0 findings\nexit=0\n",
    "har": HAR_OK,
    "har_summary": (
        "GET http://m:5000/ body: (empty)  -> your server\n"
        "POST http://p:5001/x card fields: card[number]  -> the provider"
    ),
    "routes": "POST /pay -> 404\nGET /pay -> 404",
    "headers": "content-security-policy: script-src http://p:5001\nscript inventory (x):",
    "tokens": "  (1, 'pi_x', 'pm_y')\ncard number columns: none",
    "responsibilities": "## Now the provider's\n## Still ours",
    "attestation": "NOT OBTAINED",
}
````

These module-level lines:

- Stores the result of calling `har()` in `HAR_OK`.
- Stores the dictionary `{'scope': '```mermaid\nx\n```\n**9 systems and 3 teams in scope**', '…` in `GOOD`.

`tests/unit/domain/test_evidence_rules.py` lines 48 to 58:

```python
def pack(overrides=None, gaps=None):
    files = {**GOOD, **(overrides or {})}
    requirements = [Requirement(f"R-{kind}", kind, (EvidenceSpec(f"{kind}.txt", kind, "proves"),)) for kind in files]
    texts = {f"{kind}.txt": text for kind, text in files.items()}
    manifest = {name: ManifestEntry(name, f"R-{name[:-4]}", NOW, digest(text)) for name, text in texts.items()}
    return (
        requirements,
        manifest,
        texts,
        gaps if gaps is not None else [Gap("R-attestation", "no real provider", "PCI-1", date(2026, 12, 1))],
    )
```

> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.
> **In plain words.** A **dictionary comprehension** `{k: v for ...}` builds a dictionary with a loop written inside braces.
> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.

**Function `pack`.**

It takes: `overrides`, default `None`; `gaps`, default `None`.

Step by step:

- Stores the dictionary `{**GOOD, **(overrides or {})}` in `files`.
- Stores a new list made by a loop (`[Requirement(f'R-{kind}', kind, (EvidenceSpec(f'{kind}.txt', kind, 'p…`) in `requirements`.
- Stores a new dictionary made by a loop (`{f'{kind}.txt': text for kind, text in files.items()}`) in `texts`.
- Stores a new dictionary made by a loop (`{name: ManifestEntry(name, f'R-{name[:-4]}', NOW, digest(text)) for n…`) in `manifest`.
- Gives back the tuple `(requirements, manifest, texts, gaps if gaps is not None else [Gap('R…`.

`tests/unit/domain/test_evidence_rules.py` lines 61 to 67:

```python
def codes(overrides=None, gaps=None, drop=None, manifest_edit=None):
    requirements, manifest, texts, gap_list = pack(overrides, gaps)
    if drop:
        del texts[drop]
    if manifest_edit:
        manifest_edit(manifest)
    return sorted({f.code for f in verify_pack(requirements, manifest, texts, gap_list, MERCHANT, PROVIDER)})
```

> **In plain words.** A **set comprehension** `{x for ...}` builds a set (a collection with no duplicates) with a loop.

**Function `codes`.**

It takes: `overrides`, default `None`; `gaps`, default `None`; `drop`, default `None`; `manifest_edit`, default `None`.

Step by step:

- Unpacks the result of calling `pack(overrides, gaps)` into `(requirements, manifest, texts, gap_list)`.
- If `drop`:
  - Removes `texts[drop]`.
- If `manifest_edit`:
  - Calls `manifest_edit(manifest)`.
- Gives back the result of calling `sorted({f.code for f in verify_pack(requirements, manifest, texts, gap_list, MERCHANT, PR…`.

`tests/unit/domain/test_evidence_rules.py` lines 70 to 72:

```python
def test_a_complete_pack_passes():
    requirements, manifest, texts, gaps = pack()
    assert verify_pack(requirements, manifest, texts, gaps, MERCHANT, PROVIDER) == []
```

> **In plain words.** `assert condition` checks that something is true. In a test, a false condition fails the test and pytest shows both sides of the comparison.
> **In plain words.** A **test** is a function whose name starts with `test_`. pytest finds it, runs it, and reports a pass when no `assert` fails and nothing raises.

**Test `test_a_complete_pack_passes`** checks: a complete pack passes.

Step by step:

- Unpacks the result of calling `pack()` into `(requirements, manifest, texts, gaps)`.
- Checks that `verify_pack(requirements, manifest, texts, gaps, …` equals `[]`; if not, the test fails.

`tests/unit/domain/test_evidence_rules.py` lines 75 to 80:

```python
def test_a_requirement_with_no_evidence_needs_a_tracked_gap():
    requirements, manifest, texts, gaps = pack()
    requirements.append(Requirement("P9", "x", ()))
    assert [f.code for f in verify_pack(requirements, manifest, texts, gaps, MERCHANT, PROVIDER)] == ["EVP001"]
    gaps.append(Gap("P9", "later", "PCI-2", date(2026, 12, 1)))
    assert verify_pack(requirements, manifest, texts, gaps, MERCHANT, PROVIDER) == []
```

**Test `test_a_requirement_with_no_evidence_needs_a_tracked_gap`** checks: a requirement with no evidence needs a tracked gap.

Step by step:

- Unpacks the result of calling `pack()` into `(requirements, manifest, texts, gaps)`.
- Calls `requirements.append(Requirement('P9', 'x', ()))`.
- Checks that `[f.code for f in verify_pack(requirements, manife…` equals `['EVP001']`; if not, the test fails.
- Calls `gaps.append(Gap('P9', 'later', 'PCI-2', date(2026, 12, 1)))`.
- Checks that `verify_pack(requirements, manifest, texts, gaps, …` equals `[]`; if not, the test fails.

`tests/unit/domain/test_evidence_rules.py` lines 83 to 92:

```python
def test_missing_empty_unclaimed_and_edited_files_are_reported():
    assert codes(drop="routes.txt") == ["EVP002"]
    assert codes({"routes": "  \n"}) == ["EVP002"]
    requirements, manifest, texts, gaps = pack()
    texts["stray.txt"] = "x"
    assert {f.code for f in verify_pack(requirements, manifest, texts, gaps, MERCHANT, PROVIDER)} == {"EVP004"}
    requirements, manifest, texts, gaps = pack()
    texts["routes.txt"] += "edited"
    assert {f.code for f in verify_pack(requirements, manifest, texts, gaps, MERCHANT, PROVIDER)} == {"EVP003"}
    assert codes(manifest_edit=lambda m: m.pop("routes.txt")) == ["EVP003"]
```

> **In plain words.** A **set** `{a, b}` holds items without duplicates; `frozenset` is a set that cannot be changed.
> **In plain words.** A **lambda** is a small function written in one line: `lambda x: x + 1`.

**Test `test_missing_empty_unclaimed_and_edited_files_are_reported`** checks: missing empty unclaimed and edited files are reported.

Step by step:

- Checks that `codes(drop='routes.txt')` equals `['EVP002']`; if not, the test fails.
- Checks that `codes({'routes': ' \n'})` equals `['EVP002']`; if not, the test fails.
- Unpacks the result of calling `pack()` into `(requirements, manifest, texts, gaps)`.
- Stores the text `'x'` in `texts['stray.txt']`.
- Checks that `{f.code for f in verify_pack(requirements, manife…` equals `{'EVP004'}`; if not, the test fails.
- Unpacks the result of calling `pack()` into `(requirements, manifest, texts, gaps)`.
- Adds the text `'edited'` to `texts['routes.txt']`.
- Checks that `{f.code for f in verify_pack(requirements, manife…` equals `{'EVP003'}`; if not, the test fails.
- Checks that `codes(manifest_edit=lambda m: m.pop('routes.txt'))` equals `['EVP003']`; if not, the test fails.

`tests/unit/domain/test_evidence_rules.py` lines 95 to 99:

```python
def test_gaps_must_be_complete_and_real():
    assert "EVP008" in codes(gaps=[Gap("R-attestation", "", "PCI-1", date(2026, 12, 1))])
    assert "EVP008" in codes(
        gaps=[Gap("R-attestation", "x", "PCI-1", None), Gap("P99", "x", "PCI-3", date(2026, 12, 1))]
    )
```

**Test `test_gaps_must_be_complete_and_real`** checks: gaps must be complete and real.

Step by step:

- Checks that `'EVP008'` is in `codes(gaps=[Gap('R-attestation', '', 'PCI-1', dat…`; if not, the test fails.
- Checks that `'EVP008'` is in `codes(gaps=[Gap('R-attestation', 'x', 'PCI-1', No…`; if not, the test fails.

`tests/unit/domain/test_evidence_rules.py` lines 102 to 137:

```python
@pytest.mark.parametrize(
    ("kind", "bad"),
    [
        ("scope", "no diagram, no count"),
        (
            "scope_change",
            "Before: 9 systems and 3 teams in scope.\nAfter: 9 systems and 3 teams in scope.\n"
            "Left scope: x\nStill in scope: y",
        ),
        ("scope_change", "nothing"),
        ("scan_before", "scanned 1 artifact(s): 0 findings\nexit=0"),
        ("scan_after", "x FOUND card number\nscanned 3 artifact(s): 1 findings\nexit=1"),
        ("scan_after", "scanned 1 artifact(s): 0 findings\nexit=0"),
        ("har", "not json"),
        (
            "har",
            HAR_OK.replace("[redacted]", "[redacted]").replace(
                '"url": "http://m:5000/", "postData": {"text": ""}',
                '"url": "http://m:5000/", "postData": {"text": "card_number=4242424242424242"}',
            ),
        ),
        ("har", HAR_OK.replace("card%5Bnumber%5D", "amount")),
        ("har", HAR_OK.replace("http://m:5000/", "http://other/")),
        ("har_summary", "GET x  card fields: card[number]  -> your server\nPOST y  -> the provider"),
        ("har_summary", "only your server -> your server"),
        ("routes", "POST /pay -> 200\nGET /pay -> 404"),
        ("headers", "script inventory"),
        ("headers", "content-security-policy: default-src 'self'\nscript inventory"),
        ("headers", "content-security-policy: script-src http://p:5001"),
        ("tokens", "card number columns: none"),
        ("tokens", "pm_x"),
        ("responsibilities", "## Now the provider's"),
    ],
)
def test_each_artifact_is_checked_for_what_it_must_say(kind, bad):
    assert "EVP007" in codes({kind: bad})
```

> **In plain words.** `@pytest.mark.parametrize` runs the same test function once for each row of data given; a failure names the row that broke.

**Test `test_each_artifact_is_checked_for_what_it_must_say`** checks: each artifact is checked for what it must say.

It takes: `kind`; `bad`.

Decorators: `@pytest.mark.parametrize(('kind', 'bad'), [('scope', 'no diagram, no c…`.

Step by step:

- Checks that `'EVP007'` is in `codes({kind: bad})`; if not, the test fails.

`tests/unit/domain/test_evidence_rules.py` lines 140 to 142:

```python
def test_an_attestation_that_is_not_obtained_needs_its_gap():
    assert codes(gaps=[]) == ["EVP007"]
    assert codes({"attestation": "Attestation of compliance: on file, dated 2026-01-01"}, gaps=[]) == []
```

**Test `test_an_attestation_that_is_not_obtained_needs_its_gap`** checks: an attestation that is not obtained needs its gap.

Step by step:

- Checks that `codes(gaps=[])` equals `['EVP007']`; if not, the test fails.
- Checks that `codes({'attestation': 'Attestation of compliance:…` equals `[]`; if not, the test fails.

## Try it yourself

```bash
.venv/bin/pytest -q tests/unit/domain
```
Prints a row of dots, one per passing test, and a summary line such as `N passed in 0.5s` (skipped tests show as `s`).

```bash
.venv/bin/mypy
```
Checks the whole project (the `files` setting in `pyproject.toml`), these files included. Prints `Success: no issues found in 46 source files`.

```bash
.venv/bin/ruff check tests/unit/domain/test_card_scope_webhook_har.py tests/unit/domain/test_evidence_rules.py
```
Prints `All checks passed!`.

## Mistakes people make

- Tests that depend on each other's order. Each test here builds its own data.
- Asserting only the happy path. These tests also break the input on purpose and check the exact rule that fails.
- Forgetting `test_` in a name, so the test never runs.

## Check yourself

1. What does the test `test_published_test_numbers_pass_the_luhn_check` check?
   **Answer:** it checks: published test numbers pass the luhn check.
2. What does the test `test_other_numbers_do_not` check?
   **Answer:** it checks: other numbers do not.
3. What does the test `test_a_mask_keeps_six_and_four_digits_only` check?
   **Answer:** it checks: a mask keeps six and four digits only.
4. What does the test `test_a_card_number_in_any_common_form_is_found_and_only_its_mask_is_reported` check?
   **Answer:** it checks: a card number in any common form is found and only its mask is reported.
5. What does the test `test_ordinary_log_lines_are_not_flagged` check?
   **Answer:** it checks: ordinary log lines are not flagged.

## Further reading

- pytest 9.1 documentation: <https://docs.pytest.org/en/stable/>
- How to use fixtures: <https://docs.pytest.org/en/stable/how-to/fixtures.html>
- `assert` rewriting: <https://docs.pytest.org/en/stable/how-to/assert.html>
