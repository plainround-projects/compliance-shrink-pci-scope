# dataclasses

## What it is

A **dataclass** is a class that mainly holds data. You list the fields with their types, and Python writes the
boring methods for you: `__init__` (to create the object), `__repr__` (to print it) and `__eq__` (to compare two
objects by their fields). The decorator `@dataclass` does the work. `frozen=True` makes the object read-only after it
is created.

## Why this repository uses it

Everything the program passes around is a value: a finding, a report, a parsed record, a set of settings. Frozen
values cannot be changed behind your back, are easy to compare in tests, and print readably when a test fails.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/domain/findings.py` | `Finding`. |
| `src/pci_scope/domain/payment.py` | `Order`, `Intent`. |
| `src/pci_scope/domain/scope.py` | `System`, `Edge`, `Inventory`, `ScopeResult`. |
| `src/pci_scope/domain/har.py` | `Exchange`. |
| `src/pci_scope/interfaces/provider_app.py` | `ProviderState`: the one non-frozen dataclass, the provider's in-memory state. |
| `src/pci_scope/interfaces/browser_sim.py` | `Reply`, `PaymentRun`. |

## How it works underneath

At import time, `@dataclass` looks at the class's annotated fields and **generates source code** for `__init__`,
`__repr__` and `__eq__` and attaches it to the class. With `frozen=True` it also generates `__setattr__` and
`__delattr__` methods that raise `FrozenInstanceError`, and a `__hash__`, so frozen objects can be dictionary keys or
set members. The fields are stored in the object like ordinary attributes.

## Walkthrough of this repository's use

`src/pci_scope/domain/payment.py`:

```python
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
```

- `@dataclass(frozen=True)` writes `__init__`, `__repr__` and `__eq__` and forbids changing fields afterwards. An `Order` holds only
  tokens and status: **no field could hold a card number**.
- `customer_id: str = ""` is a field with a **default**; fields with defaults come last.

`src/pci_scope/domain/scope.py`:

```python
@dataclass(frozen=True)
class System:
    """A system of the merchant (or an outside one, when `external`). `touches_card`: card data reaches it directly;
    `serves_payment_page` means it serves the page that loads the provider's script."""

    id: str
    name: str
    team: str
    touches_card: bool = False
    serves_payment_page: bool = False
    external: bool = False


@dataclass(frozen=True)
class Edge:
    """A `data` edge carries card data onward; a `control` edge means the source can change the target."""

    source: str
    target: str
    kind: str


@dataclass(frozen=True)
class Inventory:
    """The systems and how they connect."""

    title: str
    systems: tuple[System, ...]
```

`System`, `Edge` and `Inventory` are the vocabulary of the scope calculator: a system (with flags such as `touches_card`), a link
between two systems (`data` or `control`), and the whole picture. Immutable values are easy to compare in tests and to reason about.

`src/pci_scope/interfaces/provider_app.py`:

```python
@dataclass
class ProviderState:
    """Everything the provider holds. A real one holds the card; this one keeps only brand and last four digits."""

    secret_key: str
    publishable_key: str
    webhook_secret: str
    webhook_url: str
    deliver: Deliver = deliver_over_http
    intents: dict[str, dict[str, Any]] = field(default_factory=dict)
    methods: dict[str, dict[str, Any]] = field(default_factory=dict)
    customers: set[str] = field(default_factory=set)
    refunds: dict[str, str] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
```

This one is **not frozen**: the provider's state changes while it runs (intents, methods, events). `field(default_factory=dict)`
gives every `ProviderState` its own new dictionary; a plain `= {}` would be shared and Python refuses it. `lock:
threading.Lock = field(default_factory=threading.Lock)` creates a lock per state object (see `threads-and-sockets.md`).

`src/pci_scope/interfaces/browser_sim.py`:

```python
class PaymentRun:
    """The requests made, and what the page and the payment turned out to be."""

    exchanges: list[Exchange] = field(default_factory=list)
    intent_id: str = ""
    final_text: str = ""
    final_status: int = 0
    page_headers: dict[str, str] = field(default_factory=dict)
    page_card_fields: list[str] = field(default_factory=list)
```

A result record with defaults for everything, filled in as the scripted browser makes its requests.

## Try it yourself

```bash
.venv/bin/python - <<'EOF'
from pci_scope.domain.payment import Order
o = Order(1, "pi_abcdefgh1234", 1900, "eur", "pending")
print(o)
try:
    o.status = "succeeded"
except Exception as e:
    print(type(e).__name__)
EOF
```
Prints the `Order(...)` with `customer_id=''` and `payment_method_id=''`, then `FrozenInstanceError`.

```bash
.venv/bin/python -c "from dataclasses import fields; from pci_scope.domain.payment import Order; print([f.name for f in fields(Order)])"
```
Prints the seven field names: no card number among them.

```bash
.venv/bin/python -c "from dataclasses import replace; from pci_scope.domain.payment import Order; o = Order(1, 'pi_abcdefgh1234', 1900, 'eur', 'pending'); print(replace(o, status='failed').status, o.status)"
```
Prints `failed pending`: a copy with one field changed.

```bash
grep -rn "@dataclass" src | wc -l
```
Counts the dataclasses in the code.

## Mistakes people make

- **A mutable default** such as `items: list = []`. Dataclasses reject it; use `field(default_factory=list)` or an
  immutable tuple.
- **Forgetting `frozen=True`** and letting values change by accident.
- **Assuming frozen means deeply frozen.** A frozen dataclass holding a list can still have the list changed. These
  classes hold tuples.
- **Comparing floats by `==`** in a dataclass field. Use a tolerance in tests.

## Check yourself

1. What does `@dataclass` write for you?
   **Answer:** `__init__`, `__repr__` and `__eq__` (and more, with options).
2. What does `frozen=True` do?
   **Answer:** It makes assigning to a field after creation raise `FrozenInstanceError`.
3. How do you change one field of a frozen object?
   **Answer:** Make a copy with `dataclasses.replace(obj, field=value)`.
4. Why use `tuple[str, ...]` rather than `list[str]` in a frozen class?
   **Answer:** A tuple cannot be changed, so the object stays unchangeable.
5. When does `__post_init__` run?
   **Answer:** Right after the generated `__init__`, to validate the fields.

## Further reading

- `dataclasses` (Python 3.12): <https://docs.python.org/3.12/library/dataclasses.html>
