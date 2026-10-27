# The tests (shared)

## What it is

The pytest tests in `tests/shared`. Each function whose name starts with `test_` is one check; pytest finds and runs them. (Every term is explained where it first appears in the walkthrough below.)

## Why this repository uses it

The tests turn every rule, adapter and command of this repository into something that can fail. A rule without a test is only a claim.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/conftest.py` | 57 lines. Shared fakes: a provider and an order table in memory, and the repository root. |

## How it works underneath

pytest imports each `test_*.py` file, builds the fixtures a test asks for by parameter name, runs the function, and counts it as passed when no `assert` fails and nothing raises. A fixture such as `tmp_path` or `monkeypatch` is prepared fresh for each test, so tests do not affect each other.

## Walkthrough of this repository's use

### `tests/conftest.py`

`tests/conftest.py` lines 1 to 7:

```python
"""Shared fakes: a provider and an order table in memory, and the repository root."""

from __future__ import annotations

from pathlib import Path

from pci_scope.domain.payment import Intent, Order, PaymentError
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Shared fakes: a provider and an order table in memory, and the repository root.

Imports:

- From `__future__` it takes `annotations`.
- From `pathlib` it takes `Path`.
- From `pci_scope.domain.payment` it takes `Intent, Order, PaymentError`.

`tests/conftest.py` lines 9 to 10:

```python
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SECRET = "whsec_unit_test_secret_value_0123456789abcdef"
```

> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores `Path(__file__).resolve().parents[1]` in `REPOSITORY_ROOT`.
- Stores the text `'whsec_unit_test_secret_value_0123456789abcdef'` in `SECRET`.

`tests/conftest.py` lines 13 to 14:

```python
class FakeProvider:
    """Records calls and answers like a provider: intents succeed unless the method is marked declined."""
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.

**Class `FakeProvider`**. Records calls and answers like a provider: intents succeed unless the method is marked declined.

`tests/conftest.py` lines 16 to 20:

```python
    def __init__(self) -> None:
        self.intents: dict[str, Intent] = {}
        self.calls: list[tuple[str, tuple[object, ...]]] = []
        self.decline = False
        self.counter = 0
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Method `__init__` of class `FakeProvider`.**

It gives back a `None`.

Step by step:

- Declares `self.intents` as a `dict[str, Intent]` and stores the dictionary `{}` in it.
- Declares `self.calls` as a `list[tuple[str, tuple[object, ...]]]` and stores the list `[]` in it.
- Stores `False` in `self.decline`.
- Stores the number `0` in `self.counter`.

`tests/conftest.py` lines 22 to 24:

```python
    def _next(self, prefix: str) -> str:
        self.counter += 1
        return f"{prefix}_{self.counter:024d}"
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Method `_next` of class `FakeProvider`.**

It takes: `prefix` (a `str`).

It gives back a `str`.

Step by step:

- Adds the number `1` to `self.counter`.
- Gives back a text built with values filled in (`f'{prefix}_{self.counter:024d}'`).

`tests/conftest.py` lines 26 to 28:

```python
    def create_customer(self) -> str:
        self.calls.append(("create_customer", ()))
        return self._next("cus")
```

**Method `create_customer` of class `FakeProvider`.**

It gives back a `str`.

Step by step:

- Calls `self.calls.append(('create_customer', ()))`.
- Gives back the result of calling `self._next('cus')`.

`tests/conftest.py` lines 30 to 36:

```python
    def create_intent(self, amount_cents: int, currency: str, customer_id: str, save_card: bool) -> Intent:
        self.calls.append(("create_intent", (amount_cents, currency, customer_id, save_card)))
        intent = Intent(
            self._next("pi"), "requires_payment_method", amount_cents, currency, "secret_x", "", customer_id
        )
        self.intents[intent.id] = intent
        return intent
```

**Method `create_intent` of class `FakeProvider`.**

It takes: `amount_cents` (a `int`); `currency` (a `str`); `customer_id` (a `str`); `save_card` (a `bool`).

It gives back a `Intent`.

Step by step:

- Calls `self.calls.append(('create_intent', (amount_cents, currency, customer_id, save_card)))`.
- Stores the result of calling `Intent(self._next('pi'), 'requires_payment_method', amount_cents, currency, 'secret_x', '…` in `intent`.
- Stores `intent` in `self.intents[intent.id]`.
- Gives back `intent`.

`tests/conftest.py` lines 38 to 43:

```python
    def retrieve_intent(self, intent_id: str) -> Intent:
        self.calls.append(("retrieve_intent", (intent_id,)))
        intent = self.intents[intent_id]
        status = "requires_payment_method" if self.decline else "succeeded"
        method = "" if self.decline else "pm_" + "0" * 24
        return Intent(intent.id, status, intent.amount_cents, intent.currency, "", method, intent.customer_id)
```

> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.

**Method `retrieve_intent` of class `FakeProvider`.**

It takes: `intent_id` (a `str`).

It gives back a `Intent`.

Step by step:

- Calls `self.calls.append(('retrieve_intent', (intent_id,)))`.
- Stores `self.intents[intent_id]` in `intent`.
- Stores `'requires_payment_method'` if `self.decline`, otherwise `'succeeded'` in `status`.
- Stores `''` if `self.decline`, otherwise `'pm_' + '0' * 24` in `method`.
- Gives back the result of calling `Intent(intent.id, status, intent.amount_cents, intent.currency, '', method, intent.custom…`.

`tests/conftest.py` lines 45 to 51:

```python
    def charge_saved(self, customer_id: str, payment_method_id: str, amount_cents: int, currency: str) -> Intent:
        self.calls.append(("charge_saved", (customer_id, payment_method_id, amount_cents, currency)))
        if self.decline:
            raise PaymentError("Your card was declined.")
        intent = Intent(self._next("pi"), "succeeded", amount_cents, currency, "", payment_method_id, customer_id)
        self.intents[intent.id] = intent
        return intent
```

> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.

**Method `charge_saved` of class `FakeProvider`.**

It takes: `customer_id` (a `str`); `payment_method_id` (a `str`); `amount_cents` (a `int`); `currency` (a `str`).

It gives back a `Intent`.

Step by step:

- Calls `self.calls.append(('charge_saved', (customer_id, payment_method_id, amount_cents, currency)))`.
- If `self.decline`:
  - Stops here by raising `PaymentError('Your card was declined.')`.
- Stores the result of calling `Intent(self._next('pi'), 'succeeded', amount_cents, currency, '', payment_method_id, cust…` in `intent`.
- Stores `intent` in `self.intents[intent.id]`.
- Gives back `intent`.

`tests/conftest.py` lines 53 to 55:

```python
    def refund(self, intent_id: str) -> str:
        self.calls.append(("refund", (intent_id,)))
        return self._next("re")
```

**Method `refund` of class `FakeProvider`.**

It takes: `intent_id` (a `str`).

It gives back a `str`.

Step by step:

- Calls `self.calls.append(('refund', (intent_id,)))`.
- Gives back the result of calling `self._next('re')`.

`tests/conftest.py` lines 58 to 76:

```python
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
```

> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.

**Class `MemoryOrders`**. The order table in a dict.

Its methods, in order:

**Method `__init__` of class `MemoryOrders`.**

It gives back a `None`.

Step by step:

- Declares `self.rows` as a `dict[str, Order]` and stores the dictionary `{}` in it.

**Method `create` of class `MemoryOrders`.**

It takes: `intent_id` (a `str`); `amount_cents` (a `int`); `currency` (a `str`); `customer_id` (a `str`).

It gives back a `Order`.

Step by step:

- Stores the result of calling `Order(len(self.rows) + 1, intent_id, amount_cents, currency, 'pending', customer_id)` in `order`.
- Stores `order` in `self.rows[intent_id]`.
- Gives back `order`.

**Method `find` of class `MemoryOrders`.**

It takes: `intent_id` (a `str`).

It gives back a `Order | None`.

Step by step:

- Gives back the result of calling `self.rows.get(intent_id)`.

**Method `update` of class `MemoryOrders`.**

It takes: `intent_id` (a `str`); `status` (a `str`); `payment_method_id` (a `str`).

It gives back a `None`.

Step by step:

- Stores `self.rows[intent_id]` in `old`.
- Stores the result of calling `Order(old.id, old.payment_intent_id, old.amount_cents, old.currency, status, old.customer…` in `self.rows[intent_id]`.

## Try it yourself

```bash
.venv/bin/pytest -q tests
```
Prints a row of dots, one per passing test, and a summary line such as `N passed in 0.5s` (skipped tests show as `s`).

```bash
.venv/bin/mypy
```
Checks the whole project (the `files` setting in `pyproject.toml`), these files included. Prints `Success: no issues found in 46 source files`.

```bash
.venv/bin/ruff check tests/conftest.py
```
Prints `All checks passed!`.

## Mistakes people make

- Tests that depend on each other's order. Each test here builds its own data.
- Asserting only the happy path. These tests also break the input on purpose and check the exact rule that fails.
- Forgetting `test_` in a name, so the test never runs.

## Check yourself

1. What does the test `FakeProvider` check?
   **Answer:** Records calls and answers like a provider: intents succeed unless the method is marked declined.
2. What does the test `MemoryOrders` check?
   **Answer:** The order table in a dict.
3. What is a docstring?
   **Answer:** A text in triple quotes at the start of a module, class or function that describes it.
4. What does `frozen=True` do on a dataclass?
   **Answer:** It forbids changing a field after the object is created.
5. What does a type hint do at run time?
   **Answer:** Nothing; mypy reads hints before the program runs.

## Further reading

- pytest 9.1 documentation: <https://docs.pytest.org/en/stable/>
- How to use fixtures: <https://docs.pytest.org/en/stable/how-to/fixtures.html>
- `assert` rewriting: <https://docs.pytest.org/en/stable/how-to/assert.html>
