# Application layer code

## What it is

The use cases: the steps that join domain rules to the outside world through small interfaces (ports). (Every term is explained where it first appears in the walkthrough below.)

## Why this repository uses it

This is where the repository's application work happens. Reading it file by file, with every line explained, is how a reader sees the work that was done.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/application/__init__.py` | 1 lines. Use cases and the ports they need. Depends on the domain only. |
| `src/pci_scope/application/checkout.py` | 84 lines. The checkout: the merchant creates the payment and later learns the result, and never sees a card. |
| `src/pci_scope/application/pack.py` | 73 lines. Text for the evidence pack: the scope documents, the route check, the page controls, the token storage, the i… |
| `src/pci_scope/application/ports.py` | 56 lines. What the use cases need from the outside world. |
| `src/pci_scope/application/proof.py` | 31 lines. The proof that card data is not on the merchant's side: scan every place it could be, say what was scanned. |

## How it works underneath

The application layer says *what* happens in what order (check every document, export a person's data, collect the evidence) and asks the outside world for what it needs only through `ports.py`, a list of `Protocol` classes. It imports the domain and nothing outer.

## Walkthrough of this repository's use

### `src/pci_scope/application/__init__.py`

`src/pci_scope/application/__init__.py` lines 1 to 1:

```python
"""Use cases and the ports they need. Depends on the domain only."""
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.

**Module description.** Use cases and the ports they need. Depends on the domain only.

### `src/pci_scope/application/checkout.py`

`src/pci_scope/application/checkout.py` lines 1 to 10:

```python
"""The checkout: the merchant creates the payment and later learns the result, and never sees a card."""

from __future__ import annotations

import json
from dataclasses import dataclass

from pci_scope.application.ports import OrderRepository, PaymentProvider
from pci_scope.domain.payment import Intent, Order, PaymentError, is_token
from pci_scope.domain.webhook import verify
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The checkout: the merchant creates the payment and later learns the result, and never sees a card.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `json`.
- From `dataclasses` it takes `dataclass`.
- From `pci_scope.application.ports` it takes `OrderRepository, PaymentProvider`.
- From `pci_scope.domain.payment` it takes `Intent, Order, PaymentError, is_token`.
- From `pci_scope.domain.webhook` it takes `verify`.

`src/pci_scope/application/checkout.py` lines 12 to 13:

```python
PRICE_CENTS = 1900
CURRENCY = "eur"
```

> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the number `1900` in `PRICE_CENTS`.
- Stores the text `'eur'` in `CURRENCY`.

`src/pci_scope/application/checkout.py` lines 16 to 21:

```python
@dataclass(frozen=True)
class Started:
    """What the browser needs to pay: the secret for this intent, and the intent's id."""

    client_secret: str
    intent_id: str
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `Started`**. What the browser needs to pay: the secret for this intent, and the intent's id. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `client_secret`: a `str`.
- Field `intent_id`: a `str`.

`src/pci_scope/application/checkout.py` lines 24 to 25:

```python
class CheckoutService:
    """Create a payment, learn its result from the provider, charge again from tokens, refund."""
```

**Class `CheckoutService`**. Create a payment, learn its result from the provider, charge again from tokens, refund.

`src/pci_scope/application/checkout.py` lines 27 to 30:

```python
    def __init__(self, provider: PaymentProvider, orders: OrderRepository, webhook_secret: str) -> None:
        self._provider = provider
        self._orders = orders
        self._webhook_secret = webhook_secret
```

**Method `__init__` of class `CheckoutService`.**

It takes: `provider` (a `PaymentProvider`); `orders` (a `OrderRepository`); `webhook_secret` (a `str`).

It gives back a `None`.

Step by step:

- Stores `provider` in `self._provider`.
- Stores `orders` in `self._orders`.
- Stores `webhook_secret` in `self._webhook_secret`.

`src/pci_scope/application/checkout.py` lines 32 to 37:

```python
    def start(self) -> Started:
        """Create a customer and an intent for the fixed price. The price comes from here, not from the browser."""
        customer = self._provider.create_customer()
        intent = self._provider.create_intent(PRICE_CENTS, CURRENCY, customer, save_card=True)
        self._orders.create(intent.id, PRICE_CENTS, CURRENCY, customer)
        return Started(intent.client_secret, intent.id)
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.

**Method `start` of class `CheckoutService`.** Create a customer and an intent for the fixed price. The price comes from here, not from the browser.

It gives back a `Started`.

Step by step:

- Stores the result of calling `self._provider.create_customer()` in `customer`.
- Stores the result of calling `self._provider.create_intent(PRICE_CENTS, CURRENCY, customer, save_card=True)` in `intent`.
- Calls `self._orders.create(intent.id, PRICE_CENTS, CURRENCY, customer)`.
- Gives back the result of calling `Started(intent.client_secret, intent.id)`.

`src/pci_scope/application/checkout.py` lines 39 to 42:

```python
    def complete(self, intent_id: str) -> Order:
        """Ask the provider what happened to this intent and record it. The browser's word is not used."""
        self._known(intent_id)
        return self._record(self._provider.retrieve_intent(intent_id))
```

**Method `complete` of class `CheckoutService`.** Ask the provider what happened to this intent and record it. The browser's word is not used.

It takes: `intent_id` (a `str`).

It gives back a `Order`.

Step by step:

- Calls `self._known(intent_id)`.
- Gives back the result of calling `self._record(self._provider.retrieve_intent(intent_id))`.

`src/pci_scope/application/checkout.py` lines 44 to 54:

```python
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
```

> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.

**Method `charge_again` of class `CheckoutService`.** Take a second payment from the saved payment method, using only the customer and method tokens.

It takes: `intent_id` (a `str`).

It gives back a `Order`.

Step by step:

- Stores the result of calling `self._known(intent_id)` in `order`.
- If not (`order.payment_method_id`) or not (`order.customer_id`):
  - Stops here by raising `PaymentError('no saved payment method for this order')`.
- Stores the result of calling `self._provider.charge_saved(order.customer_id, order.payment_method_id, order.amount_cent…` in `intent`.
- Calls `self._orders.create(intent.id, order.amount_cents, order.currency, order.customer_id)`.
- Calls `self._orders.update(intent.id, _status(intent), order.payment_method_id)`.
- Gives back the result of calling `self._known(intent.id)`.

`src/pci_scope/application/checkout.py` lines 56 to 61:

```python
    def refund(self, intent_id: str) -> str:
        """Refund a payment by its token; no card data is needed."""
        order = self._known(intent_id)
        refund_id = self._provider.refund(order.payment_intent_id)
        self._orders.update(order.payment_intent_id, "refunded", order.payment_method_id)
        return refund_id
```

**Method `refund` of class `CheckoutService`.** Refund a payment by its token; no card data is needed.

It takes: `intent_id` (a `str`).

It gives back a `str`.

Step by step:

- Stores the result of calling `self._known(intent_id)` in `order`.
- Stores the result of calling `self._provider.refund(order.payment_intent_id)` in `refund_id`.
- Calls `self._orders.update(order.payment_intent_id, 'refunded', order.payment_method_id)`.
- Gives back `refund_id`.

`src/pci_scope/application/checkout.py` lines 63 to 76:

```python
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
```

> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.

**Method `handle_event` of class `CheckoutService`.** Apply a provider event after checking its signature. Repeating an event changes nothing.

It takes: `body` (a `bytes`); `signature` (a `str | None`); `now` (a `int`).

It gives back a `str`.

Step by step:

- If not (`verify(self._webhook_secret, body, signature, now)`):
  - Stops here by raising `PaymentError('webhook signature is not valid')`.
- Stores the result of calling `json.loads(body)` in `event`.
- Stores `event['data']['object']` in `intent`.
- Stores the result of calling `self._orders.find(intent['id'])` in `order`.
- If `order` is the same object as `None`:
  - Gives back the text `'ignored: unknown payment'`.
- Stores the result of calling `{'payment_intent.succeeded': 'succeeded', 'payment_intent.payment_failed': 'failed'}.get(…` in `status`.
- If `status` is the same object as `None`:
  - Gives back a text built with values filled in (`f"ignored: {event['type']}"`).
- Calls `self._orders.update(order.payment_intent_id, status, intent.get('payment_method', order.payment_method_id))`.
- Gives back a text built with values filled in (`f"applied: {event['type']}"`).

`src/pci_scope/application/checkout.py` lines 78 to 83:

```python
    def _record(self, intent: Intent) -> Order:
        order = self._known(intent.id)
        if intent.payment_method_id and not is_token(intent.payment_method_id):
            raise PaymentError("the provider returned something that is not a token")
        self._orders.update(intent.id, _status(intent), intent.payment_method_id or order.payment_method_id)
        return self._known(intent.id)
```

**Method `_record` of class `CheckoutService`.**

It takes: `intent` (a `Intent`).

It gives back a `Order`.

Step by step:

- Stores the result of calling `self._known(intent.id)` in `order`.
- If `intent.payment_method_id` and not (`is_token(intent.payment_method_id)`):
  - Stops here by raising `PaymentError('the provider returned something that is not a token')`.
- Calls `self._orders.update(intent.id, _status(intent), intent.payment_method_id or order.payment_method_id)`.
- Gives back the result of calling `self._known(intent.id)`.

`src/pci_scope/application/checkout.py` lines 85 to 90:

```python
    def _known(self, intent_id: str) -> Order:
        _require_token(intent_id)
        order = self._orders.find(intent_id)
        if order is None:
            raise PaymentError("unknown payment")
        return order
```

**Method `_known` of class `CheckoutService`.**

It takes: `intent_id` (a `str`).

It gives back a `Order`.

Step by step:

- Calls `_require_token(intent_id)`.
- Stores the result of calling `self._orders.find(intent_id)` in `order`.
- If `order` is the same object as `None`:
  - Stops here by raising `PaymentError('unknown payment')`.
- Gives back `order`.

`src/pci_scope/application/checkout.py` lines 93 to 95:

```python
def _require_token(value: str) -> None:
    if not is_token(value):
        raise PaymentError("not a payment token")
```

**Function `_require_token`.**

It takes: `value` (a `str`).

It gives back a `None`.

Step by step:

- If not (`is_token(value)`):
  - Stops here by raising `PaymentError('not a payment token')`.

`src/pci_scope/application/checkout.py` lines 98 to 105:

```python
def _status(intent: Intent) -> str:
    return (
        "succeeded"
        if intent.status == "succeeded"
        else "failed"
        if intent.status in ("requires_payment_method", "canceled")
        else "pending"
    )
```

> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Function `_status`.**

It takes: `intent` (a `Intent`).

It gives back a `str`.

Step by step:

- Gives back `'succeeded'` if `intent.status` equals `'succeeded'`, otherwise `'failed' if intent.status in ('requires…`.

### `src/pci_scope/application/pack.py`

`src/pci_scope/application/pack.py` lines 1 to 9:

```python
"""Text for the evidence pack: the scope documents, the route check, the page controls, the token storage, the index."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from pci_scope.domain.evidence import Gap, ManifestEntry, Requirement
from pci_scope.domain.scope import Inventory, compare_scope, compute_scope, render_scope_report
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Text for the evidence pack: the scope documents, the route check, the page controls, the token storage, the index.

Imports:

- From `__future__` it takes `annotations`.
- From `collections.abc` it takes `Mapping`.
- From `datetime` it takes `datetime`.
- From `pci_scope.domain.evidence` it takes `Gap, ManifestEntry, Requirement`.
- From `pci_scope.domain.scope` it takes `Inventory, compare_scope, compute_scope, render_scope_report`.

`src/pci_scope/application/pack.py` lines 12 to 19:

```python
def scope_documents(before: Inventory, after: Inventory) -> dict[str, str]:
    """scope-before.md, scope-after.md and scope-change.md, computed from the two inventories."""
    before_result, after_result = compute_scope(before), compute_scope(after)
    return {
        "scope-before.md": render_scope_report(before, before_result),
        "scope-after.md": render_scope_report(after, after_result),
        "scope-change.md": "# What changed in scope\n\n" + compare_scope(before_result, after_result),
    }
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.

**Function `scope_documents`.** scope-before.md, scope-after.md and scope-change.md, computed from the two inventories.

It takes: `before` (a `Inventory`); `after` (a `Inventory`).

It gives back a `dict[str, str]`.

Step by step:

- Unpacks the tuple `(compute_scope(before), compute_scope(after))` into `(before_result, after_result)`.
- Gives back the dictionary `{'scope-before.md': render_scope_report(before, before_result), 'scop…`.

`src/pci_scope/application/pack.py` lines 22 to 26:

```python
def render_routes(results: list[tuple[str, str, int]]) -> str:
    """`POST /pay -> 404`, one line per probe, for routes that must not exist."""
    return "routes that accepted card details in the naive checkout, probed on the merchant:\n" + "".join(
        f"{method} {path} -> {status}\n" for method, path, status in results
    )
```

> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Function `render_routes`.** `POST /pay -> 404`, one line per probe, for routes that must not exist.

It takes: `results` (a `list[tuple[str, str, int]]`).

It gives back a `str`.

Step by step:

- Gives back `'routes that accepted card details in the naive checkout, probed on the merchan…`.

`src/pci_scope/application/pack.py` lines 29 to 43:

```python
def render_page_controls(
    url: str, status: int, headers: Mapping[str, str], scripts: list[str], provider: str, card_fields: list[str]
) -> str:
    """The payment page's security headers and the inventory of what it loads."""
    wanted = ("Content-Security-Policy", "X-Content-Type-Options", "Referrer-Policy", "Cache-Control")
    lines = [f"payment page controls: GET {url} -> {status}"]
    lines += [f"{name.lower()}: {headers.get(name, '(missing)')}" for name in wanted]
    lines.append("")
    lines.append("script inventory (the scripts and frames the page loads):")
    for src in scripts:
        owner = "the provider's" if src.startswith(provider) else "ours"
        lines.append(f"  script  {src}  ({owner})")
    lines.append(f"  frame   {provider}/frame  (created by the provider's script, served by the provider)")
    lines.append(f"card input fields on the merchant's page: {', '.join(card_fields) or 'none'}")
    return "\n".join(lines) + "\n"
```

> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.
> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.

**Function `render_page_controls`.** The payment page's security headers and the inventory of what it loads.

It takes: `url` (a `str`); `status` (a `int`); `headers` (a `Mapping[str, str]`); `scripts` (a `list[str]`); `provider` (a `str`); `card_fields` (a `list[str]`).

It gives back a `str`.

Step by step:

- Stores the tuple `('Content-Security-Policy', 'X-Content-Type-Options', 'Referrer-Polic…` in `wanted`.
- Stores the list `[f'payment page controls: GET {url} -> {status}']` in `lines`.
- Adds a new list made by a loop (`[f"{name.lower()}: {headers.get(name, '(missing)')}" for name in want…`) to `lines`.
- Calls `lines.append('')`.
- Calls `lines.append('script inventory (the scripts and frames the page loads):')`.
- For each `src` in `scripts`:
  - Stores `"the provider's"` if `src.startswith(provider)`, otherwise `'ours'` in `owner`.
  - Calls `lines.append(f' script {src} ({owner})')`.
- Calls `lines.append(f" frame {provider}/frame (created by the provider's script, served by the provider)")`.
- Calls `lines.append(f"card input fields on the merchant's page: {', '.join(card_fields) or 'none'}")`.
- Gives back `'\n'.join(lines) + '\n'`.

`src/pci_scope/application/pack.py` lines 46 to 55:

```python
def render_token_storage(
    columns: list[tuple[str, str]], rows: list[tuple[object, ...]], digit_columns: list[str]
) -> str:
    """The order table's shape, sample rows, and the result of looking for card-number columns."""
    lines = ["order table columns:"]
    lines += [f"  {name} {kind}" for name, kind in columns]
    lines.append("sample rows (id, payment intent, status, customer, payment method):")
    lines += [f"  {row}" for row in rows]
    lines.append(f"card number columns: {', '.join(digit_columns) or 'none'}")
    return "\n".join(lines) + "\n"
```

**Function `render_token_storage`.** The order table's shape, sample rows, and the result of looking for card-number columns.

It takes: `columns` (a `list[tuple[str, str]]`); `rows` (a `list[tuple[object, ...]]`); `digit_columns` (a `list[str]`).

It gives back a `str`.

Step by step:

- Stores the list `['order table columns:']` in `lines`.
- Adds a new list made by a loop (`[f' {name} {kind}' for name, kind in columns]`) to `lines`.
- Calls `lines.append('sample rows (id, payment intent, status, customer, payment method):')`.
- Adds a new list made by a loop (`[f' {row}' for row in rows]`) to `lines`.
- Calls `lines.append(f"card number columns: {', '.join(digit_columns) or 'none'}")`.
- Gives back `'\n'.join(lines) + '\n'`.

`src/pci_scope/application/pack.py` lines 58 to 86:

```python
def render_index(
    requirements: list[Requirement], manifest: Mapping[str, ManifestEntry], gaps: list[Gap], when: datetime
) -> str:
    """INDEX.md: one line per file with the requirement it supports, what it proves and when it was made."""
    lines = [
        "# Evidence pack index",
        "",
        f"Pack date: {when.strftime('%Y-%m-%dT%H:%M:%SZ')}. Every file was produced by `make run` (`pci-scope demo`); "
        "`manifest.json` records its hash, so a hand edit fails `make verify`.",
        "",
        "| File | Requirement | Proves | Date |",
        "| --- | --- | --- | --- |",
    ]
    for requirement in requirements:
        for spec in requirement.evidence:
            entry = manifest.get(spec.file)
            date_text = entry.produced_at.strftime("%Y-%m-%d") if entry else "not produced"
            lines.append(f"| {spec.file} | {requirement.id} | {spec.proves} | {date_text} |")
    lines += ["", "## Tracked gaps", ""]
    lines += [f"- {gap.requirement}: {gap.reason} Ticket {gap.ticket}, due {gap.due}." for gap in gaps] or ["None."]
    lines += [
        "",
        "## What the merchant still does",
        "",
        "See `responsibilities.md`: the payment page and its pipeline, the content security policy, "
        "no logging of bodies, the provider's attestation, the questionnaire for the merchant level.",
        "",
    ]
    return "\n".join(lines)
```

**Function `render_index`.** INDEX.md: one line per file with the requirement it supports, what it proves and when it was made.

It takes: `requirements` (a `list[Requirement]`); `manifest` (a `Mapping[str, ManifestEntry]`); `gaps` (a `list[Gap]`); `when` (a `datetime`).

It gives back a `str`.

Step by step:

- Stores the list `['# Evidence pack index', '', f"Pack date: {when.strftime('%Y-%m-%dT%…` in `lines`.
- For each `requirement` in `requirements`:
  - For each `spec` in `requirement.evidence`:
    - Stores the result of calling `manifest.get(spec.file)` in `entry`.
    - Stores `entry.produced_at.strftime('%Y-%m-%d')` if `entry`, otherwise `'not produced'` in `date_text`.
    - Calls `lines.append(f'| {spec.file} | {requirement.id} | {spec.proves} | {date_text} |')`.
- Adds the list `['', '## Tracked gaps', '']` to `lines`.
- Adds whether `[f'- {gap.requirement}: {gap.reason} Ticket {gap.ticket}, due {gap.du…` or `['None.']` to `lines`.
- Adds the list `['', '## What the merchant still does', '', "See `responsibilities.md…` to `lines`.
- Gives back the result of calling `'\n'.join(lines)`.

### `src/pci_scope/application/ports.py`

`src/pci_scope/application/ports.py` lines 1 to 10:

```python
"""What the use cases need from the outside world."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from typing import Protocol

from pci_scope.domain.evidence import ManifestEntry
from pci_scope.domain.payment import Intent, Order
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** What the use cases need from the outside world.

Imports:

- From `__future__` it takes `annotations`.
- From `collections.abc` it takes `Iterator`.
- From `datetime` it takes `datetime`.
- From `typing` it takes `Protocol`.
- From `pci_scope.domain.evidence` it takes `ManifestEntry`.
- From `pci_scope.domain.payment` it takes `Intent, Order`.

`src/pci_scope/application/ports.py` lines 13 to 18:

```python
class Clock(Protocol):
    """The current time, injected so tests are deterministic."""

    def now(self) -> datetime:
        """The current moment, timezone aware."""
        ...
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **Protocol** describes the methods an object must have, without requiring inheritance. Any class with those methods fits. A body of `...` means "no code here, only the shape".
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.

**Class `Clock`**, a kind of `Protocol`. The current time, injected so tests are deterministic.

Its methods, in order:

**Method `now` of class `Clock`.** The current moment, timezone aware.

It gives back a `datetime`.

`src/pci_scope/application/ports.py` lines 21 to 42:

```python
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
```

**Class `PaymentProvider`**, a kind of `Protocol`. The payment provider's server-side API. Card numbers never pass through it: the browser sends them elsewhere.

Its methods, in order:

**Method `create_customer` of class `PaymentProvider`.** A customer token (`cus_...`).

It gives back a `str`.

**Method `create_intent` of class `PaymentProvider`.** A payment intent whose client secret the browser confirms with the provider.

It takes: `amount_cents` (a `int`); `currency` (a `str`); `customer_id` (a `str`); `save_card` (a `bool`).

It gives back a `Intent`.

**Method `retrieve_intent` of class `PaymentProvider`.** The intent as the provider now has it.

It takes: `intent_id` (a `str`).

It gives back a `Intent`.

**Method `charge_saved` of class `PaymentProvider`.** Charge a saved payment method off-session, from tokens alone.

It takes: `customer_id` (a `str`); `payment_method_id` (a `str`); `amount_cents` (a `int`); `currency` (a `str`).

It gives back a `Intent`.

**Method `refund` of class `PaymentProvider`.** Refund a payment; returns the refund token (`re_...`).

It takes: `intent_id` (a `str`).

It gives back a `str`.

`src/pci_scope/application/ports.py` lines 45 to 58:

```python
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
```

> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.

**Class `OrderRepository`**, a kind of `Protocol`. Orders, holding provider tokens and never card data.

Its methods, in order:

**Method `create` of class `OrderRepository`.** Store a pending order.

It takes: `intent_id` (a `str`); `amount_cents` (a `int`); `currency` (a `str`); `customer_id` (a `str`).

It gives back a `Order`.

**Method `find` of class `OrderRepository`.** The order for a payment intent.

It takes: `intent_id` (a `str`).

It gives back a `Order | None`.

**Method `update` of class `OrderRepository`.** Set the status and the saved payment-method token.

It takes: `intent_id` (a `str`); `status` (a `str`); `payment_method_id` (a `str`).

It gives back a `None`.

`src/pci_scope/application/ports.py` lines 61 to 66:

```python
class ArtifactReader(Protocol):
    """Yields the text of each place on the merchant's side where card data could end up."""

    def artifacts(self) -> Iterator[tuple[str, str]]:
        """(name, text) for each log file, database dump and backup."""
        ...
```

> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Class `ArtifactReader`**, a kind of `Protocol`. Yields the text of each place on the merchant's side where card data could end up.

Its methods, in order:

**Method `artifacts` of class `ArtifactReader`.** (name, text) for each log file, database dump and backup.

It gives back a `Iterator[tuple[str, str]]`.

`src/pci_scope/application/ports.py` lines 69 to 82:

```python
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
```

**Class `EvidenceStore`**, a kind of `Protocol`. The evidence folder and its manifest.

Its methods, in order:

**Method `write` of class `EvidenceStore`.** Write a file and record it in the manifest.

It takes: `name` (a `str`); `text` (a `str`); `requirement` (a `str`); `produced_at` (a `datetime`).

It gives back a `None`.

**Method `read_all` of class `EvidenceStore`.** Every file in the folder.

It gives back a `dict[str, str]`.

**Method `manifest` of class `EvidenceStore`.** The manifest entries by file name.

It gives back a `dict[str, ManifestEntry]`.

### `src/pci_scope/application/proof.py`

`src/pci_scope/application/proof.py` lines 1 to 8:

```python
"""The proof that card data is not on the merchant's side: scan every place it could be, say what was scanned."""

from __future__ import annotations

from dataclasses import dataclass

from pci_scope.application.ports import ArtifactReader
from pci_scope.domain.card import CardFinding, scan_text
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The proof that card data is not on the merchant's side: scan every place it could be, say what was scanned.

Imports:

- From `__future__` it takes `annotations`.
- From `dataclasses` it takes `dataclass`.
- From `pci_scope.application.ports` it takes `ArtifactReader`.
- From `pci_scope.domain.card` it takes `CardFinding, scan_text`.

`src/pci_scope/application/proof.py` lines 11 to 22:

```python
@dataclass(frozen=True)
class ScanOutcome:
    """The text of the proof, the findings behind it, and the exit code a shell would see."""

    text: str
    findings: tuple[CardFinding, ...]
    artifacts: int

    @property
    def exit_code(self) -> int:
        """1 when anything was found, 0 when the scan is clean."""
        return 1 if self.findings else 0
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `ScanOutcome`**. The text of the proof, the findings behind it, and the exit code a shell would see. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `text`: a `str`.
- Field `findings`: a `tuple[CardFinding, ...]`.
- Field `artifacts`: a `int`.

Its methods, in order:

**Method `exit_code` of class `ScanOutcome`.** 1 when anything was found, 0 when the scan is clean.

It gives back a `int`.

Decorators: `@property`.

Step by step:

- Gives back `1` if `self.findings`, otherwise `0`.

`src/pci_scope/application/proof.py` lines 25 to 40:

```python
def run_scan(title: str, reader: ArtifactReader) -> ScanOutcome:
    """Scan each artifact for card numbers and card fields and write the report, with masked evidence only."""
    lines = [title]
    findings: list[CardFinding] = []
    count = 0
    for name, text in reader.artifacts():
        count += 1
        found = scan_text(name, text)
        findings.extend(found)
        if found:
            lines.extend(f"  {item.source}:{item.line} FOUND {item.kind} {item.evidence}" for item in found)
        else:
            lines.append(f"  {name} ... clean")
    lines.append(f"scanned {count} artifact(s): {len(findings)} findings")
    lines.append(f"exit={1 if findings else 0}")
    return ScanOutcome("\n".join(lines) + "\n", tuple(findings), count)
```

> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.

**Function `run_scan`.** Scan each artifact for card numbers and card fields and write the report, with masked evidence only.

It takes: `title` (a `str`); `reader` (a `ArtifactReader`).

It gives back a `ScanOutcome`.

Step by step:

- Stores the list `[title]` in `lines`.
- Declares `findings` as a `list[CardFinding]` and stores the list `[]` in it.
- Stores the number `0` in `count`.
- For each `(name, text)` in the result of calling `reader.artifacts()`:
  - Adds the number `1` to `count`.
  - Stores the result of calling `scan_text(name, text)` in `found`.
  - Calls `findings.extend(found)`.
  - If `found`:
    - Calls `lines.extend((f' {item.source}:{item.line} FOUND {item.kind} {item.evidence}' for item in found))`.
  - Otherwise:
    - Calls `lines.append(f' {name} ... clean')`.
- Calls `lines.append(f'scanned {count} artifact(s): {len(findings)} findings')`.
- Calls `lines.append(f'exit={(1 if findings else 0)}')`.
- Gives back the result of calling `ScanOutcome('\n'.join(lines) + '\n', tuple(findings), count)`.

## Try it yourself

```bash
.venv/bin/python -c "import pci_scope.application.checkout; print(pci_scope.application.checkout.__doc__)"
```
Prints the module's description: `The checkout: the merchant creates the payment and later learns the result, and never sees a card.`

```bash
.venv/bin/python -c "import pci_scope.application.pack; print(pci_scope.application.pack.__doc__)"
```
Prints the module's description: `Text for the evidence pack: the scope documents, the route check, the page controls, the token storage, the index.`

```bash
.venv/bin/mypy
```
Checks the whole project (the `files` setting in `pyproject.toml`), these files included. Prints `Success: no issues found in 46 source files`.

```bash
.venv/bin/ruff check src/pci_scope/application/__init__.py src/pci_scope/application/checkout.py src/pci_scope/application/pack.py src/pci_scope/application/ports.py src/pci_scope/application/proof.py
```
Prints `All checks passed!`.

```bash
grep -c "^def \|^class \|    def " src/pci_scope/application/checkout.py
```
Counts the functions, methods and classes in `src/pci_scope/application/checkout.py`.

## Mistakes people make

- Importing an adapter directly. Use the port; the adapter is passed in from the outside.
- Putting a rule here that belongs in the domain, where it can be tested without any setup.
- Catching an error too early. Use cases let named errors travel up to the interfaces layer.

## Check yourself

1. What is `Started` for?
   **Answer:** What the browser needs to pay: the secret for this intent, and the intent's id.
2. What is `CheckoutService` for?
   **Answer:** Create a payment, learn its result from the provider, charge again from tokens, refund.
3. What is `scope_documents` for?
   **Answer:** scope-before.md, scope-after.md and scope-change.md, computed from the two inventories.
4. What is `render_routes` for?
   **Answer:** `POST /pay -> 404`, one line per probe, for routes that must not exist.
5. What is `render_page_controls` for?
   **Answer:** The payment page's security headers and the inventory of what it loads.

## Further reading

- Python 3.12 tutorial, classes: <https://docs.python.org/3.12/tutorial/classes.html>
- Python 3.12 language reference: <https://docs.python.org/3.12/reference/>
- Type hints: <https://docs.python.org/3.12/library/typing.html>
