# Domain layer code

## What it is

The rules and values: plain Python that decides things and never touches a file, a network or a database. (Every term is explained where it first appears in the walkthrough below.)

## Why this repository uses it

This is where the repository's domain work happens. Reading it file by file, with every line explained, is how a reader sees the work that was done.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/__init__.py` | 2 lines. Shrinks the PCI scope of a checkout and proves that card data never reaches the merchant. |
| `src/pci_scope/domain/__init__.py` | 1 lines. Pure rules and values. Depends on the standard library only. |
| `src/pci_scope/domain/card.py` | 58 lines. Card data: how to recognize a card number or a card field in text, and the published test cards. |
| `src/pci_scope/domain/evidence.py` | 184 lines. The evidence pack for a reduced-scope assessment: each requirement maps to evidence, every file exists, says … |
| `src/pci_scope/domain/findings.py` | 12 lines. A problem a check found, with a code so a test and a reader can point at the rule. |
| `src/pci_scope/domain/har.py` | 87 lines. The traffic capture: who received what during one payment, summarized and checked. |
| `src/pci_scope/domain/payment.py` | 31 lines. Payment values the merchant keeps: tokens and order status. Never a card number. |
| `src/pci_scope/domain/scope.py` | 112 lines. PCI scope as a computation: which systems are in scope, why, and which teams carry the requirements. |
| `src/pci_scope/domain/webhook.py` | 19 lines. Webhook signatures: the provider signs the body with a shared secret and a timestamp; the merchant verifies b… |

## How it works underneath

The domain layer is the centre of the design. Because it imports nothing from the outer layers, every rule can be tested with plain values, fast, without setting anything up. import-linter fails the build if a domain file imports an outer layer.

## Walkthrough of this repository's use

### `src/pci_scope/__init__.py`

`src/pci_scope/__init__.py` lines 1 to 1:

```python
"""Shrinks the PCI scope of a checkout and proves that card data never reaches the merchant."""
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.

**Module description.** Shrinks the PCI scope of a checkout and proves that card data never reaches the merchant.

`src/pci_scope/__init__.py` lines 3 to 3:

```python
__version__ = "0.1.0"
```

These module-level lines:

- Stores the text `'0.1.0'` in `__version__`.

### `src/pci_scope/domain/__init__.py`

`src/pci_scope/domain/__init__.py` lines 1 to 1:

```python
"""Pure rules and values. Depends on the standard library only."""
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.

**Module description.** Pure rules and values. Depends on the standard library only.

### `src/pci_scope/domain/card.py`

`src/pci_scope/domain/card.py` lines 1 to 7:

```python
"""Card data: how to recognize a card number or a card field in text, and the published test cards."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import unquote_plus
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Card data: how to recognize a card number or a card field in text, and the published test cards.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `re`.
- From `dataclasses` it takes `dataclass`.
- From `urllib.parse` it takes `unquote_plus`.

`src/pci_scope/domain/card.py` lines 9 to 18:

```python
# Digits in groups, optionally separated by single spaces or dashes: 13 to 19 digits in all.
_CANDIDATE = re.compile(r"(?<![\d-])(?:\d[ -]?){12,18}\d(?![\d-])")
_CARD_FIELD = re.compile(
    r"""(?i)\b(cvv|cvc|cvv2|card[_\[\]-]*number|card_number|cardnumber|pan)\b["']?\s*[:=]\s*["']?[^\s&,"'}]+"""
)
_FIELD_NAME_ONLY = re.compile(r"(?i)card\[(number|cvc|exp_month|exp_year)\]")

TEST_CARD = "4242424242424242"
DECLINED_TEST_CARD = "4000000000000002"
TEST_CARDS = frozenset({TEST_CARD, DECLINED_TEST_CARD})
```

> **In plain words.** A **regular expression** is a short pattern for text, such as `^## (.+)$` for "a line starting with ## ". `re.compile` prepares it once; `.match` tries it at the start of a string and returns a match object or `None`.
> **In plain words.** A **set** `{a, b}` holds items without duplicates; `frozenset` is a set that cannot be changed.
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the result of calling `re.compile('(?<![\\d-])(?:\\d[ -]?){12,18}\\d(?![\\d-])')` in `_CANDIDATE`.
- Stores the result of calling `re.compile('(?i)\\b(cvv|cvc|cvv2|card[_\\[\\]-]*number|card_number|cardnumber|pan)\\b["\'…` in `_CARD_FIELD`.
- Stores the result of calling `re.compile('(?i)card\\[(number|cvc|exp_month|exp_year)\\]')` in `_FIELD_NAME_ONLY`.
- Stores the text `'4242424242424242'` in `TEST_CARD`.
- Stores the text `'4000000000000002'` in `DECLINED_TEST_CARD`.
- Stores the result of calling `frozenset({TEST_CARD, DECLINED_TEST_CARD})` in `TEST_CARDS`.

`src/pci_scope/domain/card.py` lines 21 to 33:

```python
def luhn_valid(digits: str) -> bool:
    """The Luhn check every card number passes."""
    if not digits.isdigit():
        return False
    total = 0
    for position, char in enumerate(reversed(digits)):
        value = int(char)
        if position % 2 == 1:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.

**Function `luhn_valid`.** The Luhn check every card number passes.

It takes: `digits` (a `str`).

It gives back a `bool`.

Step by step:

- If not (`digits.isdigit()`):
  - Gives back `False`.
- Stores the number `0` in `total`.
- For each `(position, char)` in the result of calling `enumerate(reversed(digits))`:
  - Stores the result of calling `int(char)` in `value`.
  - If `position % 2` equals `1`:
    - Multiplies the number `2` into/from `value`.
    - If `value` is more than `9`:
      - Subtracts the number `9` into/from `value`.
  - Adds `value` to `total`.
- Gives back whether `total % 10` equals `0`.

`src/pci_scope/domain/card.py` lines 36 to 38:

```python
def mask(digits: str) -> str:
    """The first six and last four digits, the rest as stars: enough to tell the card in a report, never the number."""
    return f"{digits[:6]}{'*' * (len(digits) - 10)}{digits[-4:]}"
```

> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.

**Function `mask`.** The first six and last four digits, the rest as stars: enough to tell the card in a report, never the number.

It takes: `digits` (a `str`).

It gives back a `str`.

Step by step:

- Gives back a text built with values filled in (`f"{digits[:6]}{'*' * (len(digits) - 10)}{digits[-4:]}"`).

`src/pci_scope/domain/card.py` lines 41 to 48:

```python
@dataclass(frozen=True)
class CardFinding:
    """Card data found in a place where it must not be."""

    source: str
    line: int
    kind: str
    evidence: str
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `CardFinding`**. Card data found in a place where it must not be. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `source`: a `str`.
- Field `line`: a `int`.
- Field `kind`: a `str`.
- Field `evidence`: a `str`.

`src/pci_scope/domain/card.py` lines 51 to 64:

```python
def scan_text(source: str, text: str) -> list[CardFinding]:
    """Card numbers (13 to 19 digits that pass the Luhn check, spaces or dashes allowed) and card fields with a value.

    The evidence is masked, so the report of a scan never becomes a new copy of the number.
    """
    found: list[CardFinding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in _CANDIDATE.finditer(line):
            digits = re.sub(r"[ -]", "", match.group(0))
            if 13 <= len(digits) <= 19 and luhn_valid(digits):
                found.append(CardFinding(source, line_number, "card number", mask(digits)))
        for field in _CARD_FIELD.finditer(unquote_plus(line)):
            found.append(CardFinding(source, line_number, "card field", field.group(1).lower()))
    return found
```

**Function `scan_text`.** Card numbers (13 to 19 digits that pass the Luhn check, spaces or dashes allowed) and card fields with a value. The evidence is masked, so the report of a scan never becomes a new copy of the number.

It takes: `source` (a `str`); `text` (a `str`).

It gives back a `list[CardFinding]`.

Step by step:

- Declares `found` as a `list[CardFinding]` and stores the list `[]` in it.
- For each `(line_number, line)` in the result of calling `enumerate(text.splitlines(), start=1)`:
  - For each `match` in the result of calling `_CANDIDATE.finditer(line)`:
    - Stores the result of calling `re.sub('[ -]', '', match.group(0))` in `digits`.
    - If `13` is at most `len(digits)` is at most `19` and `luhn_valid(digits)`:
      - Calls `found.append(CardFinding(source, line_number, 'card number', mask(digits)))`.
  - For each `field` in the result of calling `_CARD_FIELD.finditer(unquote_plus(line))`:
    - Calls `found.append(CardFinding(source, line_number, 'card field', field.group(1).lower()))`.
- Gives back `found`.

`src/pci_scope/domain/card.py` lines 67 to 75:

```python
def card_field_names(text: str) -> list[str]:
    """The names of card input fields present in a body or a page (`card[number]`, `cvc`, `card_number`, ...)."""
    decoded = unquote_plus(text)
    names = {match.group(0).lower() for match in _FIELD_NAME_ONLY.finditer(decoded)}
    names |= {
        name.lower()
        for name in re.findall(r"""(?i)name=["'](card_number|cardnumber|cvv|cvc|card-number)["']""", decoded)
    }
    return sorted(names)
```

> **In plain words.** A **set comprehension** `{x for ...}` builds a set (a collection with no duplicates) with a loop.

**Function `card_field_names`.** The names of card input fields present in a body or a page (`card[number]`, `cvc`, `card_number`, ...).

It takes: `text` (a `str`).

It gives back a `list[str]`.

Step by step:

- Stores the result of calling `unquote_plus(text)` in `decoded`.
- Stores a new set made by a loop (`{match.group(0).lower() for match in _FIELD_NAME_ONLY.finditer(decode…`) in `names`.
- Merges a new set made by a loop (`{name.lower() for name in re.findall('(?i)name=["\'](card_number|card…`) into/from `names`.
- Gives back the result of calling `sorted(names)`.

### `src/pci_scope/domain/evidence.py`

`src/pci_scope/domain/evidence.py` lines 1 to 13:

```python
"""The evidence pack for a reduced-scope assessment: each requirement maps to evidence, every file exists, says what it
should, and has not been edited. Some checks recompute the claim from the raw capture, not from a summary."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime

from pci_scope.domain.findings import Finding, error
from pci_scope.domain.har import merchant_exposure, origin, parse_har, reaches_provider
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The evidence pack for a reduced-scope assessment: each requirement maps to evidence, every file exists, says what it should, and has not been edited. Some checks recompute the claim from the raw capture, not from a summary.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `hashlib`.
- It imports module `re`.
- From `collections.abc` it takes `Callable, Mapping`.
- From `dataclasses` it takes `dataclass`.
- From `datetime` it takes `date, datetime`.
- From `pci_scope.domain.findings` it takes `Finding, error`.
- From `pci_scope.domain.har` it takes `merchant_exposure, origin, parse_har, reaches_provider`.

`src/pci_scope/domain/evidence.py` lines 15 to 15:

```python
SUPPORT_FILES = frozenset({"INDEX.md", "manifest.json"})
```

> **In plain words.** A **set** `{a, b}` holds items without duplicates; `frozenset` is a set that cannot be changed.
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the result of calling `frozenset({'INDEX.md', 'manifest.json'})` in `SUPPORT_FILES`.

`src/pci_scope/domain/evidence.py` lines 18 to 24:

```python
@dataclass(frozen=True)
class EvidenceSpec:
    """One file that supports a requirement, and the kind of check its content gets."""

    file: str
    kind: str
    proves: str
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `EvidenceSpec`**. One file that supports a requirement, and the kind of check its content gets. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `file`: a `str`.
- Field `kind`: a `str`.
- Field `proves`: a `str`.

`src/pci_scope/domain/evidence.py` lines 27 to 33:

```python
@dataclass(frozen=True)
class Requirement:
    """A thing the redesign must show, with the evidence for it."""

    id: str
    text: str
    evidence: tuple[EvidenceSpec, ...]
```

> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Class `Requirement`**. A thing the redesign must show, with the evidence for it. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `id`: a `str`.
- Field `text`: a `str`.
- Field `evidence`: a `tuple[EvidenceSpec, ...]`.

`src/pci_scope/domain/evidence.py` lines 36 to 43:

```python
@dataclass(frozen=True)
class Gap:
    """A requirement with no evidence yet, tracked on purpose."""

    requirement: str
    reason: str
    ticket: str
    due: date | None
```

> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.

**Class `Gap`**. A requirement with no evidence yet, tracked on purpose. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `requirement`: a `str`.
- Field `reason`: a `str`.
- Field `ticket`: a `str`.
- Field `due`: a `date | None`.

`src/pci_scope/domain/evidence.py` lines 46 to 53:

```python
@dataclass(frozen=True)
class ManifestEntry:
    """What the collector recorded about a file it wrote."""

    file: str
    requirement: str
    produced_at: datetime
    sha256: str
```

**Class `ManifestEntry`**. What the collector recorded about a file it wrote. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `file`: a `str`.
- Field `requirement`: a `str`.
- Field `produced_at`: a `datetime`.
- Field `sha256`: a `str`.

`src/pci_scope/domain/evidence.py` lines 56 to 58:

```python
def digest(text: str) -> str:
    """SHA-256 of a file's text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.

**Function `digest`.** SHA-256 of a file's text.

It takes: `text` (a `str`).

It gives back a `str`.

Step by step:

- Gives back the result of calling `hashlib.sha256(text.encode('utf-8')).hexdigest()`.

`src/pci_scope/domain/evidence.py` lines 61 to 88:

```python
def verify_pack(
    requirements: list[Requirement],
    manifest: Mapping[str, ManifestEntry],
    files: Mapping[str, str],
    gaps: list[Gap],
    merchant: str,
    provider: str,
) -> list[Finding]:
    """EVP001 to EVP008."""
    found: list[Finding] = []
    gap_ids = {gap.requirement for gap in gaps}
    claimed: set[str] = set()
    for requirement in requirements:
        if not requirement.evidence:
            if requirement.id not in gap_ids:
                found.append(error("EVP001", requirement.id, "no evidence and no tracked gap"))
            continue
        for spec in requirement.evidence:
            claimed.add(spec.file)
            found.extend(_check_file(requirement, spec, manifest, files, merchant, provider, gap_ids))
    for gap in gaps:
        if not gap.reason.strip() or not gap.ticket.strip() or gap.due is None:
            found.append(error("EVP008", gap.requirement, "a tracked gap needs a reason, a ticket and a due date"))
        if gap.requirement not in {requirement.id for requirement in requirements}:
            found.append(error("EVP008", gap.requirement, "the gap names a requirement that does not exist"))
    for name in sorted(set(files) - claimed - SUPPORT_FILES):
        found.append(error("EVP004", name, "an evidence file that no requirement claims"))
    return found
```

> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** A **set comprehension** `{x for ...}` builds a set (a collection with no duplicates) with a loop.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.

**Function `verify_pack`.** EVP001 to EVP008.

It takes: `requirements` (a `list[Requirement]`); `manifest` (a `Mapping[str, ManifestEntry]`); `files` (a `Mapping[str, str]`); `gaps` (a `list[Gap]`); `merchant` (a `str`); `provider` (a `str`).

It gives back a `list[Finding]`.

Step by step:

- Declares `found` as a `list[Finding]` and stores the list `[]` in it.
- Stores a new set made by a loop (`{gap.requirement for gap in gaps}`) in `gap_ids`.
- Declares `claimed` as a `set[str]` and stores the result of calling `set()` in it.
- For each `requirement` in `requirements`:
  - If not (`requirement.evidence`):
    - If `requirement.id` is not in `gap_ids`:
      - Calls `found.append(error('EVP001', requirement.id, 'no evidence and no tracked gap'))`.
    - Skips to the next item (`continue`).
  - For each `spec` in `requirement.evidence`:
    - Calls `claimed.add(spec.file)`.
    - Calls `found.extend(_check_file(requirement, spec, manifest, files, merchant, provider, gap_ids))`.
- For each `gap` in `gaps`:
  - If not (`gap.reason.strip()`) or not (`gap.ticket.strip()`) or `gap.due` is the same object as `None`:
    - Calls `found.append(error('EVP008', gap.requirement, 'a tracked gap needs a reason, a ticket and a due date'))`.
  - If `gap.requirement` is not in `{requirement.id for requirement in requirements}`:
    - Calls `found.append(error('EVP008', gap.requirement, 'the gap names a requirement that does not exist'))`.
- For each `name` in the result of calling `sorted(set(files) - claimed - SUPPORT_FILES)`:
  - Calls `found.append(error('EVP004', name, 'an evidence file that no requirement claims'))`.
- Gives back `found`.

`src/pci_scope/domain/evidence.py` lines 91 to 124:

```python
def _check_file(
    requirement: Requirement,
    spec: EvidenceSpec,
    manifest: Mapping[str, ManifestEntry],
    files: Mapping[str, str],
    merchant: str,
    provider: str,
    gap_ids: set[str],
) -> list[Finding]:
    subject = f"{requirement.id} {spec.file}"
    text = files.get(spec.file)
    if text is None or not text.strip():
        return [error("EVP002", subject, "the evidence file is missing or empty")]
    found: list[Finding] = []
    entry = manifest.get(spec.file)
    if entry is None or entry.sha256 != digest(text):
        found.append(
            error("EVP003", subject, "no manifest entry, or the file differs from the hash its collector recorded")
        )
    checks: dict[str, Callable[[str], list[str]]] = {
        "scope": _scope,
        "scope_change": _scope_change,
        "scan_before": _scan_before,
        "scan_after": _scan_after,
        "har": lambda t: _har(t, merchant, provider),
        "har_summary": lambda t: _har_summary(t, merchant),
        "routes": _routes,
        "headers": lambda t: _headers(t, provider),
        "tokens": _tokens,
        "responsibilities": _responsibilities,
        "attestation": lambda t: _attestation(t, requirement.id in gap_ids),
    }
    found.extend(error("EVP007", subject, problem) for problem in checks[spec.kind](text))
    return found
```

> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** A **lambda** is a small function written in one line: `lambda x: x + 1`.
> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.

**Function `_check_file`.**

It takes: `requirement` (a `Requirement`); `spec` (a `EvidenceSpec`); `manifest` (a `Mapping[str, ManifestEntry]`); `files` (a `Mapping[str, str]`); `merchant` (a `str`); `provider` (a `str`); `gap_ids` (a `set[str]`).

It gives back a `list[Finding]`.

Step by step:

- Stores a text built with values filled in (`f'{requirement.id} {spec.file}'`) in `subject`.
- Stores the result of calling `files.get(spec.file)` in `text`.
- If `text` is the same object as `None` or not (`text.strip()`):
  - Gives back the list `[error('EVP002', subject, 'the evidence file is missing or empty')]`.
- Declares `found` as a `list[Finding]` and stores the list `[]` in it.
- Stores the result of calling `manifest.get(spec.file)` in `entry`.
- If `entry` is the same object as `None` or `entry.sha256` is different from `digest(text)`:
  - Calls `found.append(error('EVP003', subject, 'no manifest entry, or the file differs from the hash its collector rec…`.
- Declares `checks` as a `dict[str, Callable[[str], list[str]]]` and stores the dictionary `{'scope': _scope, 'scope_change': _scope_change, 'scan_before': _scan…` in it.
- Calls `found.extend((error('EVP007', subject, problem) for problem in checks[spec.kind](text)))`.
- Gives back `found`.

`src/pci_scope/domain/evidence.py` lines 127 to 133:

````python
def _scope(text: str) -> list[str]:
    problems = []
    if "```mermaid" not in text:
        problems.append("no diagram")
    if not re.search(r"\*\*\d+ systems and \d+ teams in scope\*\*", text):
        problems.append("no count of systems and teams")
    return problems
````

> **In plain words.** A **regular expression** is a short pattern for text, such as `^## (.+)$` for "a line starting with ## ". `re.compile` prepares it once; `.match` tries it at the start of a string and returns a match object or `None`.

**Function `_scope`.**

It takes: `text` (a `str`).

It gives back a `list[str]`.

Step by step:

- Stores the list `[]` in `problems`.
- If `'```mermaid'` is not in `text`:
  - Calls `problems.append('no diagram')`.
- If not (`re.search('\\*\\*\\d+ systems and \\d+ teams in scope\\*\\*', text)`):
  - Calls `problems.append('no count of systems and teams')`.
- Gives back `problems`.

`src/pci_scope/domain/evidence.py` lines 136 to 146:

```python
def _scope_change(text: str) -> list[str]:
    before = re.search(r"Before: (\d+) systems and (\d+) teams", text)
    after = re.search(r"After: (\d+) systems and (\d+) teams", text)
    if not before or not after:
        return ["no before and after counts"]
    problems = []
    if int(after.group(1)) >= int(before.group(1)):
        problems.append("the scope did not shrink")
    if "Left scope:" not in text or "Still in scope:" not in text:
        problems.append("it must name what left scope and what stays")
    return problems
```

**Function `_scope_change`.**

It takes: `text` (a `str`).

It gives back a `list[str]`.

Step by step:

- Stores the result of calling `re.search('Before: (\\d+) systems and (\\d+) teams', text)` in `before`.
- Stores the result of calling `re.search('After: (\\d+) systems and (\\d+) teams', text)` in `after`.
- If not (`before`) or not (`after`):
  - Gives back the list `['no before and after counts']`.
- Stores the list `[]` in `problems`.
- If `int(after.group(1))` is at least `int(before.group(1))`:
  - Calls `problems.append('the scope did not shrink')`.
- If `'Left scope:'` is not in `text` or `'Still in scope:'` is not in `text`:
  - Calls `problems.append('it must name what left scope and what stays')`.
- Gives back `problems`.

`src/pci_scope/domain/evidence.py` lines 149 to 155:

```python
def _scan_before(text: str) -> list[str]:
    problems = []
    if "FOUND" not in text or "exit=1" not in text:
        problems.append(
            "the naive checkout must show the card number in its log (FOUND, exit=1): that is the problem being solved"
        )
    return problems
```

**Function `_scan_before`.**

It takes: `text` (a `str`).

It gives back a `list[str]`.

Step by step:

- Stores the list `[]` in `problems`.
- If `'FOUND'` is not in `text` or `'exit=1'` is not in `text`:
  - Calls `problems.append('the naive checkout must show the card number in its log (FOUND, exit=1): that is the problem…`.
- Gives back `problems`.

`src/pci_scope/domain/evidence.py` lines 158 to 167:

```python
def _scan_after(text: str) -> list[str]:
    problems = []
    if "exit=0" not in text or "0 findings" not in text:
        problems.append("the scan of the merchant's side must end with 0 findings and exit=0")
    if "FOUND" in text:
        problems.append("a scan finding is recorded in the proof")
    scanned = re.search(r"scanned (\d+) artifact", text)
    if not scanned or int(scanned.group(1)) < 3:
        problems.append("fewer than three artifacts were scanned (the log, the database and the backups at least)")
    return problems
```

**Function `_scan_after`.**

It takes: `text` (a `str`).

It gives back a `list[str]`.

Step by step:

- Stores the list `[]` in `problems`.
- If `'exit=0'` is not in `text` or `'0 findings'` is not in `text`:
  - Calls `problems.append("the scan of the merchant's side must end with 0 findings and exit=0")`.
- If `'FOUND'` is in `text`:
  - Calls `problems.append('a scan finding is recorded in the proof')`.
- Stores the result of calling `re.search('scanned (\\d+) artifact', text)` in `scanned`.
- If not (`scanned`) or `int(scanned.group(1))` is less than `3`:
  - Calls `problems.append('fewer than three artifacts were scanned (the log, the database and the backups at least)')`.
- Gives back `problems`.

`src/pci_scope/domain/evidence.py` lines 170 to 180:

```python
def _har(text: str, merchant: str, provider: str) -> list[str]:
    try:
        exchanges = parse_har(text)
    except (ValueError, KeyError):
        return ["not a HAR file"]
    problems = merchant_exposure(exchanges, merchant)
    if not reaches_provider(exchanges, provider):
        problems.append("no request to the provider carries the card fields: the capture does not show the payment")
    if not any(origin(item.url) == merchant for item in exchanges):
        problems.append("no request to the merchant: the capture is incomplete")
    return problems
```

> **In plain words.** A **`try` / `except` block** runs the steps under `try`. If an error of the named kind happens, Python jumps to the matching `except` steps instead of stopping the program. `finally` steps always run.

**Function `_har`.**

It takes: `text` (a `str`); `merchant` (a `str`); `provider` (a `str`).

It gives back a `list[str]`.

Step by step:

- Tries:
  - Stores the result of calling `parse_har(text)` in `exchanges`.
- If `(ValueError, KeyError)` happens:
  - Gives back the list `['not a HAR file']`.
- Stores the result of calling `merchant_exposure(exchanges, merchant)` in `problems`.
- If not (`reaches_provider(exchanges, provider)`):
  - Calls `problems.append('no request to the provider carries the card fields: the capture does not show the payment')`.
- If not (`any((origin(item.url) == merchant for item in exchanges))`):
  - Calls `problems.append('no request to the merchant: the capture is incomplete')`.
- Gives back `problems`.

`src/pci_scope/domain/evidence.py` lines 183 to 191:

```python
def _har_summary(text: str, merchant: str) -> list[str]:
    problems = [
        f"a request to your server lists card fields: {line}"
        for line in text.splitlines()
        if "-> your server" in line and "card fields" in line
    ]
    if "-> the provider" not in text or "-> your server" not in text:
        problems.append("the summary must show requests to both the merchant and the provider")
    return problems
```

> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.

**Function `_har_summary`.**

It takes: `text` (a `str`); `merchant` (a `str`).

It gives back a `list[str]`.

Step by step:

- Stores a new list made by a loop (`[f'a request to your server lists card fields: {line}' for line in te…`) in `problems`.
- If `'-> the provider'` is not in `text` or `'-> your server'` is not in `text`:
  - Calls `problems.append('the summary must show requests to both the merchant and the provider')`.
- Gives back `problems`.

`src/pci_scope/domain/evidence.py` lines 194 to 197:

```python
def _routes(text: str) -> list[str]:
    return [
        f"expected '{line}' in the route check" for line in ("POST /pay -> 404", "GET /pay -> 404") if line not in text
    ]
```

**Function `_routes`.**

It takes: `text` (a `str`).

It gives back a `list[str]`.

Step by step:

- Gives back a new list made by a loop (`[f"expected '{line}' in the route check" for line in ('POST /pay -> 4…`).

`src/pci_scope/domain/evidence.py` lines 200 to 209:

```python
def _headers(text: str, provider: str) -> list[str]:
    lowered = text.lower()
    problems = []
    if "content-security-policy:" not in lowered:
        problems.append("no content-security-policy header recorded")
    elif provider.lower() not in lowered:
        problems.append("the policy does not name the provider's origin")
    if "script inventory" not in lowered:
        problems.append("no inventory of the scripts and frames the page loads")
    return problems
```

**Function `_headers`.**

It takes: `text` (a `str`); `provider` (a `str`).

It gives back a `list[str]`.

Step by step:

- Stores the result of calling `text.lower()` in `lowered`.
- Stores the list `[]` in `problems`.
- If `'content-security-policy:'` is not in `lowered`:
  - Calls `problems.append('no content-security-policy header recorded')`.
- Otherwise, if `provider.lower()` is not in `lowered`:
  - Calls `problems.append("the policy does not name the provider's origin")`.
- If `'script inventory'` is not in `lowered`:
  - Calls `problems.append('no inventory of the scripts and frames the page loads')`.
- Gives back `problems`.

`src/pci_scope/domain/evidence.py` lines 212 to 218:

```python
def _tokens(text: str) -> list[str]:
    problems = []
    if "pm_" not in text and "pi_" not in text:
        problems.append("no token in the sample rows")
    if "card number columns: none" not in text:
        problems.append("the check for card-number columns is missing")
    return problems
```

**Function `_tokens`.**

It takes: `text` (a `str`).

It gives back a `list[str]`.

Step by step:

- Stores the list `[]` in `problems`.
- If `'pm_'` is not in `text` and `'pi_'` is not in `text`:
  - Calls `problems.append('no token in the sample rows')`.
- If `'card number columns: none'` is not in `text`:
  - Calls `problems.append('the check for card-number columns is missing')`.
- Gives back `problems`.

`src/pci_scope/domain/evidence.py` lines 221 to 222:

```python
def _responsibilities(text: str) -> list[str]:
    return [f"no '{label}' section" for label in ("## Now the provider's", "## Still ours") if label not in text]
```

**Function `_responsibilities`.**

It takes: `text` (a `str`).

It gives back a `list[str]`.

Step by step:

- Gives back a new list made by a loop (`[f"no '{label}' section" for label in ("## Now the provider's", '## S…`).

`src/pci_scope/domain/evidence.py` lines 225 to 228:

```python
def _attestation(text: str, tracked_gap: bool) -> list[str]:
    if "NOT OBTAINED" in text and not tracked_gap:
        return ["the provider's attestation has not been obtained and no gap is tracked"]
    return []
```

**Function `_attestation`.**

It takes: `text` (a `str`); `tracked_gap` (a `bool`).

It gives back a `list[str]`.

Step by step:

- If `'NOT OBTAINED'` is in `text` and not (`tracked_gap`):
  - Gives back the list `["the provider's attestation has not been obtained and no gap is trac…`.
- Gives back the list `[]`.

### `src/pci_scope/domain/findings.py`

`src/pci_scope/domain/findings.py` lines 1 to 5:

```python
"""A problem a check found, with a code so a test and a reader can point at the rule."""

from __future__ import annotations

from dataclasses import dataclass
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** A problem a check found, with a code so a test and a reader can point at the rule.

Imports:

- From `__future__` it takes `annotations`.
- From `dataclasses` it takes `dataclass`.

`src/pci_scope/domain/findings.py` lines 8 to 14:

```python
@dataclass(frozen=True)
class Finding:
    """One rule violation: the rule's code, what it is about, and what is wrong."""

    code: str
    subject: str
    message: str
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `Finding`**. One rule violation: the rule's code, what it is about, and what is wrong. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `code`: a `str`.
- Field `subject`: a `str`.
- Field `message`: a `str`.

`src/pci_scope/domain/findings.py` lines 17 to 19:

```python
def error(code: str, subject: str, message: str) -> Finding:
    """Build a finding."""
    return Finding(code, subject, message)
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.

**Function `error`.** Build a finding.

It takes: `code` (a `str`); `subject` (a `str`); `message` (a `str`).

It gives back a `Finding`.

Step by step:

- Gives back the result of calling `Finding(code, subject, message)`.

### `src/pci_scope/domain/har.py`

`src/pci_scope/domain/har.py` lines 1 to 9:

```python
"""The traffic capture: who received what during one payment, summarized and checked."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.parse import urlsplit

from pci_scope.domain.card import card_field_names, scan_text
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The traffic capture: who received what during one payment, summarized and checked.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `json`.
- From `dataclasses` it takes `dataclass`.
- From `urllib.parse` it takes `urlsplit`.
- From `pci_scope.domain.card` it takes `card_field_names, scan_text`.

`src/pci_scope/domain/har.py` lines 12 to 19:

```python
@dataclass(frozen=True)
class Exchange:
    """One request the browser made and the status that came back. `body` is what it sent."""

    method: str
    url: str
    status: int
    body: str
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `Exchange`**. One request the browser made and the status that came back. `body` is what it sent. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `method`: a `str`.
- Field `url`: a `str`.
- Field `status`: a `int`.
- Field `body`: a `str`.

`src/pci_scope/domain/har.py` lines 22 to 25:

```python
def origin(url: str) -> str:
    """scheme://host:port of a URL."""
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Function `origin`.** scheme://host:port of a URL.

It takes: `url` (a `str`).

It gives back a `str`.

Step by step:

- Stores the result of calling `urlsplit(url)` in `parts`.
- Gives back a text built with values filled in (`f'{parts.scheme}://{parts.netloc}'`).

`src/pci_scope/domain/har.py` lines 28 to 54:

```python
def to_har(exchanges: list[Exchange], redact_for: frozenset[str]) -> str:
    """HAR 1.2. Bodies sent to an origin in `redact_for` (the provider) keep their field names and lose the values, so
    the capture shows where the card fields went without becoming a new copy of the card."""
    entries = []
    for item in exchanges:
        body = item.body
        if origin(item.url) in redact_for and body:
            body = "&".join(f"{pair.split('=', 1)[0]}=[redacted]" for pair in body.split("&"))
        entries.append(
            {
                "request": {"method": item.method, "url": item.url, "postData": {"text": body}},
                "response": {"status": item.status},
            }
        )
    return (
        json.dumps(
            {
                "log": {
                    "version": "1.2",
                    "creator": {"name": "pci-scope browser simulator", "version": "0.1"},
                    "entries": entries,
                }
            },
            indent=2,
        )
        + "\n"
    )
```

> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.

**Function `to_har`.** HAR 1.2. Bodies sent to an origin in `redact_for` (the provider) keep their field names and lose the values, so the capture shows where the card fields went without becoming a new copy of the card.

It takes: `exchanges` (a `list[Exchange]`); `redact_for` (a `frozenset[str]`).

It gives back a `str`.

Step by step:

- Stores the list `[]` in `entries`.
- For each `item` in `exchanges`:
  - Stores `item.body` in `body`.
  - If `origin(item.url)` is in `redact_for` and `body`:
    - Stores the result of calling `'&'.join((f"{pair.split('=', 1)[0]}=[redacted]" for pair in body.split('&')))` in `body`.
  - Calls `entries.append({'request': {'method': item.method, 'url': item.url, 'postData': {'text': body}}, 'response': …`.
- Gives back `json.dumps({'log': {'version': '1.2', 'creator': {'name': 'pci-scope browser si…`.

`src/pci_scope/domain/har.py` lines 57 to 68:

```python
def parse_har(text: str) -> list[Exchange]:
    """The exchanges in a HAR file."""
    entries = json.loads(text)["log"]["entries"]
    return [
        Exchange(
            e["request"]["method"],
            e["request"]["url"],
            e["response"]["status"],
            e["request"].get("postData", {}).get("text", ""),
        )
        for e in entries
    ]
```

> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.

**Function `parse_har`.** The exchanges in a HAR file.

It takes: `text` (a `str`).

It gives back a `list[Exchange]`.

Step by step:

- Stores `json.loads(text)['log']['entries']` in `entries`.
- Gives back a new list made by a loop (`[Exchange(e['request']['method'], e['request']['url'], e['response'][…`).

`src/pci_scope/domain/har.py` lines 71 to 88:

```python
def summarize(exchanges: list[Exchange], merchant: str, provider: str) -> str:
    """The lesson's summary: one line per request, where it went, and what the body held."""
    lines = []
    for item in exchanges:
        destination = origin(item.url)
        target = (
            "your server" if destination == merchant else "the provider" if destination == provider else "elsewhere"
        )
        names = card_field_names(item.body)
        body = (
            f"card fields: {', '.join(names)}"
            if names
            else "body: (empty)"
            if not item.body
            else "body: no card fields"
        )
        lines.append(f"{item.method:4} {item.url}  {body}  -> {target}")
    return "\n".join(lines) + "\n"
```

> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.

**Function `summarize`.** The lesson's summary: one line per request, where it went, and what the body held.

It takes: `exchanges` (a `list[Exchange]`); `merchant` (a `str`); `provider` (a `str`).

It gives back a `str`.

Step by step:

- Stores the list `[]` in `lines`.
- For each `item` in `exchanges`:
  - Stores the result of calling `origin(item.url)` in `destination`.
  - Stores `'your server'` if `destination` equals `merchant`, otherwise `'the provider' if destination == provid…` in `target`.
  - Stores the result of calling `card_field_names(item.body)` in `names`.
  - Stores `f"card fields: {', '.join(names)}"` if `names`, otherwise `'body: (empty)' if not item.body else '…` in `body`.
  - Calls `lines.append(f'{item.method:4} {item.url} {body} -> {target}')`.
- Gives back `'\n'.join(lines) + '\n'`.

`src/pci_scope/domain/har.py` lines 91 to 100:

```python
def merchant_exposure(exchanges: list[Exchange], merchant: str) -> list[str]:
    """Problems: any request to the merchant whose body or URL holds a card field or a card number."""
    problems = []
    for item in exchanges:
        if origin(item.url) != merchant:
            continue
        text = f"{item.url}\n{item.body}"
        if card_field_names(text) or scan_text("har", text):
            problems.append(f"{item.method} {item.url} carries card data")
    return problems
```

**Function `merchant_exposure`.** Problems: any request to the merchant whose body or URL holds a card field or a card number.

It takes: `exchanges` (a `list[Exchange]`); `merchant` (a `str`).

It gives back a `list[str]`.

Step by step:

- Stores the list `[]` in `problems`.
- For each `item` in `exchanges`:
  - If `origin(item.url)` is different from `merchant`:
    - Skips to the next item (`continue`).
  - Stores a text built with values filled in (`f'{item.url}\n{item.body}'`) in `text`.
  - If `card_field_names(text)` or `scan_text('har', text)`:
    - Calls `problems.append(f'{item.method} {item.url} carries card data')`.
- Gives back `problems`.

`src/pci_scope/domain/har.py` lines 103 to 105:

```python
def reaches_provider(exchanges: list[Exchange], provider: str) -> bool:
    """True when at least one request to the provider carries the card fields (the card went where it should)."""
    return any(origin(item.url) == provider and card_field_names(item.body) for item in exchanges)
```

**Function `reaches_provider`.** True when at least one request to the provider carries the card fields (the card went where it should).

It takes: `exchanges` (a `list[Exchange]`); `provider` (a `str`).

It gives back a `bool`.

Step by step:

- Gives back the result of calling `any((origin(item.url) == provider and card_field_names(item.body) for item in exchanges))`.

### `src/pci_scope/domain/payment.py`

`src/pci_scope/domain/payment.py` lines 1 to 6:

```python
"""Payment values the merchant keeps: tokens and order status. Never a card number."""

from __future__ import annotations

import re
from dataclasses import dataclass
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Payment values the merchant keeps: tokens and order status. Never a card number.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `re`.
- From `dataclasses` it takes `dataclass`.

`src/pci_scope/domain/payment.py` lines 8 to 9:

```python
TOKEN = re.compile(r"^(pi|pm|cus|re)_[A-Za-z0-9]{8,64}$")
PAYMENT_STATUSES = ("pending", "succeeded", "failed", "refunded")
```

> **In plain words.** A **regular expression** is a short pattern for text, such as `^## (.+)$` for "a line starting with ## ". `re.compile` prepares it once; `.match` tries it at the start of a string and returns a match object or `None`.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the result of calling `re.compile('^(pi|pm|cus|re)_[A-Za-z0-9]{8,64}$')` in `TOKEN`.
- Stores the tuple `('pending', 'succeeded', 'failed', 'refunded')` in `PAYMENT_STATUSES`.

`src/pci_scope/domain/payment.py` lines 12 to 13:

```python
class PaymentError(Exception):
    """A payment failed in a way the customer should hear about (declined, unknown token, provider down)."""
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A class that inherits from `Exception` is a new kind of **error**. `raise` stops the current function with it, and a `try ... except` further up decides what to do.

**Class `PaymentError`**, a kind of `Exception`. A payment failed in a way the customer should hear about (declined, unknown token, provider down).

`src/pci_scope/domain/payment.py` lines 16 to 18:

```python
def is_token(value: str) -> bool:
    """True for a provider id such as `pi_...` or `pm_...`: the only payment values the merchant may store."""
    return bool(TOKEN.match(value))
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.

**Function `is_token`.** True for a provider id such as `pi_...` or `pm_...`: the only payment values the merchant may store.

It takes: `value` (a `str`).

It gives back a `bool`.

Step by step:

- Gives back the result of calling `bool(TOKEN.match(value))`.

`src/pci_scope/domain/payment.py` lines 21 to 31:

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

> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `Order`**. An order. `payment_method_id` and `customer_id` are provider tokens; the card is the provider's. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `id`: a `int`.
- Field `payment_intent_id`: a `str`.
- Field `amount_cents`: a `int`.
- Field `currency`: a `str`.
- Field `status`: a `str`.
- Field `customer_id`: a `str`, default `''`.
- Field `payment_method_id`: a `str`, default `''`.

`src/pci_scope/domain/payment.py` lines 34 to 44:

```python
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
```

**Class `Intent`**. A payment intent as the provider reports it. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `id`: a `str`.
- Field `status`: a `str`.
- Field `amount_cents`: a `int`.
- Field `currency`: a `str`.
- Field `client_secret`: a `str`, default `''`.
- Field `payment_method_id`: a `str`, default `''`.
- Field `customer_id`: a `str`, default `''`.

### `src/pci_scope/domain/scope.py`

`src/pci_scope/domain/scope.py` lines 1 to 5:

```python
"""PCI scope as a computation: which systems are in scope, why, and which teams carry the requirements."""

from __future__ import annotations

from dataclasses import dataclass
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** PCI scope as a computation: which systems are in scope, why, and which teams carry the requirements.

Imports:

- From `__future__` it takes `annotations`.
- From `dataclasses` it takes `dataclass`.

`src/pci_scope/domain/scope.py` lines 7 to 8:

```python
DATA = "data"
CONTROL = "control"
```

> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the text `'data'` in `DATA`.
- Stores the text `'control'` in `CONTROL`.

`src/pci_scope/domain/scope.py` lines 11 to 21:

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
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `System`**. A system of the merchant (or an outside one, when `external`). `touches_card`: card data reaches it directly; `serves_payment_page` means it serves the page that loads the provider's script. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `id`: a `str`.
- Field `name`: a `str`.
- Field `team`: a `str`.
- Field `touches_card`: a `bool`, default `False`.
- Field `serves_payment_page`: a `bool`, default `False`.
- Field `external`: a `bool`, default `False`.

`src/pci_scope/domain/scope.py` lines 24 to 30:

```python
@dataclass(frozen=True)
class Edge:
    """A `data` edge carries card data onward; a `control` edge means the source can change the target."""

    source: str
    target: str
    kind: str
```

**Class `Edge`**. A `data` edge carries card data onward; a `control` edge means the source can change the target. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `source`: a `str`.
- Field `target`: a `str`.
- Field `kind`: a `str`.

`src/pci_scope/domain/scope.py` lines 33 to 39:

```python
@dataclass(frozen=True)
class Inventory:
    """The systems and how they connect."""

    title: str
    systems: tuple[System, ...]
    edges: tuple[Edge, ...]
```

> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Class `Inventory`**. The systems and how they connect. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `title`: a `str`.
- Field `systems`: a `tuple[System, ...]`.
- Field `edges`: a `tuple[Edge, ...]`.

`src/pci_scope/domain/scope.py` lines 42 to 52:

```python
@dataclass(frozen=True)
class ScopeResult:
    """Each in-scope system with the reasons, in inventory order, and the teams that carry the requirements."""

    systems: tuple[tuple[System, tuple[str, ...]], ...]
    teams: tuple[str, ...]

    @property
    def ids(self) -> frozenset[str]:
        """The ids of the in-scope systems."""
        return frozenset(system.id for system, _ in self.systems)
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.

**Class `ScopeResult`**. Each in-scope system with the reasons, in inventory order, and the teams that carry the requirements. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `systems`: a `tuple[tuple[System, tuple[str, ...]], ...]`.
- Field `teams`: a `tuple[str, ...]`.

Its methods, in order:

**Method `ids` of class `ScopeResult`.** The ids of the in-scope systems.

It gives back a `frozenset[str]`.

Decorators: `@property`.

Step by step:

- Gives back the result of calling `frozenset((system.id for system, _ in self.systems))`.

`src/pci_scope/domain/scope.py` lines 55 to 58:

```python
def compute_scope(inventory: Inventory) -> ScopeResult:
    """Card data spreads along `data` edges from the systems that touch it; the page host is in scope for the page's
    integrity; anything that can change an in-scope system, directly or through others, is in scope too.
    """
```

**Function `compute_scope`.** Card data spreads along `data` edges from the systems that touch it; the page host is in scope for the page's integrity; anything that can change an in-scope system, directly or through others, is in scope too.

It takes: `inventory` (a `Inventory`).

It gives back a `ScopeResult`.

`src/pci_scope/domain/scope.py` lines 59 to 76:

```python
    by_id = {system.id: system for system in inventory.systems}
    reasons: dict[str, list[str]] = {}

    holders = {system.id for system in inventory.systems if system.touches_card and not system.external}
    reasons.update({sid: ["card data reaches it"] for sid in holders})
    changed = True
    while changed:
        changed = False
        for edge in inventory.edges:
            if (
                edge.kind == DATA
                and edge.source in holders
                and edge.target not in holders
                and not by_id[edge.target].external
            ):
                holders.add(edge.target)
                reasons[edge.target] = [f"card data reaches it from {by_id[edge.source].name}"]
                changed = True
```

> **In plain words.** A **dictionary comprehension** `{k: v for ...}` builds a dictionary with a loop written inside braces.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** A **set comprehension** `{x for ...}` builds a set (a collection with no duplicates) with a loop.
> **In plain words.** A **`while` loop** repeats its steps as long as its condition stays true.
> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**`compute_scope`, part 1 of 3.**

Step by step:

- Stores a new dictionary made by a loop (`{system.id: system for system in inventory.systems}`) in `by_id`.
- Declares `reasons` as a `dict[str, list[str]]` and stores the dictionary `{}` in it.
- Stores a new set made by a loop (`{system.id for system in inventory.systems if system.touches_card and…`) in `holders`.
- Calls `reasons.update({sid: ['card data reaches it'] for sid in holders})`.
- Stores `True` in `changed`.
- While `changed`:
  - Stores `False` in `changed`.
  - For each `edge` in `inventory.edges`:
    - If `edge.kind` equals `DATA` and `edge.source` is in `holders` and `edge.target` is not in `holders` and not (`by_id[edge.target].external`):
      - Calls `holders.add(edge.target)`.
      - Stores the list `[f'card data reaches it from {by_id[edge.source].name}']` in `reasons[edge.target]`.
      - Stores `True` in `changed`.

`src/pci_scope/domain/scope.py` lines 78 to 96:

```python
    scope = set(holders)
    for system in inventory.systems:
        if system.serves_payment_page and not system.external:
            scope.add(system.id)
            reasons.setdefault(system.id, []).append("serves the page that loads the provider's script")

    changed = True
    while changed:
        changed = False
        for edge in inventory.edges:
            if (
                edge.kind == CONTROL
                and edge.target in scope
                and edge.source not in scope
                and not by_id[edge.source].external
            ):
                scope.add(edge.source)
                reasons[edge.source] = [f"can change {by_id[edge.target].name}"]
                changed = True
```

**`compute_scope`, part 2 of 3.**

Step by step:

- Stores the result of calling `set(holders)` in `scope`.
- For each `system` in `inventory.systems`:
  - If `system.serves_payment_page` and not (`system.external`):
    - Calls `scope.add(system.id)`.
    - Calls `reasons.setdefault(system.id, []).append("serves the page that loads the provider's script")`.
- Stores `True` in `changed`.
- While `changed`:
  - Stores `False` in `changed`.
  - For each `edge` in `inventory.edges`:
    - If `edge.kind` equals `CONTROL` and `edge.target` is in `scope` and `edge.source` is not in `scope` and not (`by_id[edge.source].external`):
      - Calls `scope.add(edge.source)`.
      - Stores the list `[f'can change {by_id[edge.target].name}']` in `reasons[edge.source]`.
      - Stores `True` in `changed`.

`src/pci_scope/domain/scope.py` lines 98 to 100:

```python
    ordered = tuple((system, tuple(reasons[system.id])) for system in inventory.systems if system.id in scope)
    teams = tuple(sorted({system.team for system, _ in ordered}))
    return ScopeResult(ordered, teams)
```

**`compute_scope`, part 3 of 3.**

Step by step:

- Stores the result of calling `tuple(((system, tuple(reasons[system.id])) for system in inventory.systems if system.id i…` in `ordered`.
- Stores the result of calling `tuple(sorted({system.team for system, _ in ordered}))` in `teams`.
- Gives back the result of calling `ScopeResult(ordered, teams)`.

`src/pci_scope/domain/scope.py` lines 103 to 116:

```python
def render_mermaid(inventory: Inventory, result: ScopeResult) -> str:
    """The cardholder data environment as a Mermaid flowchart: in-scope systems inside a subgraph, the rest outside."""
    lines = ["flowchart LR"]
    inside = [system for system in inventory.systems if system.id in result.ids]
    outside = [system for system in inventory.systems if system.id not in result.ids]
    lines.append('    subgraph cde["In scope"]')
    lines += [f'        {system.id}["{system.name}"]' for system in inside] or ['        none["nothing"]']
    lines.append("    end")
    lines += [f'    {system.id}["{system.name}{" (provider)" if system.external else ""}"]' for system in outside]
    for edge in inventory.edges:
        arrow = "-->" if edge.kind == DATA else "-.->"
        label = "card data" if edge.kind == DATA else "can change"
        lines.append(f"    {edge.source} {arrow}|{label}| {edge.target}")
    return "\n".join(lines)
```

> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.
> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.

**Function `render_mermaid`.** The cardholder data environment as a Mermaid flowchart: in-scope systems inside a subgraph, the rest outside.

It takes: `inventory` (a `Inventory`); `result` (a `ScopeResult`).

It gives back a `str`.

Step by step:

- Stores the list `['flowchart LR']` in `lines`.
- Stores a new list made by a loop (`[system for system in inventory.systems if system.id in result.ids]`) in `inside`.
- Stores a new list made by a loop (`[system for system in inventory.systems if system.id not in result.id…`) in `outside`.
- Calls `lines.append(' subgraph cde["In scope"]')`.
- Adds whether `[f' {system.id}["{system.name}"]' for system in inside]` or `[' none["nothing"]']` to `lines`.
- Calls `lines.append(' end')`.
- Adds a new list made by a loop (`[f''' {system.id}["{system.name}{(' (provider)' if system.external el…`) to `lines`.
- For each `edge` in `inventory.edges`:
  - Stores `'-->'` if `edge.kind` equals `DATA`, otherwise `'-.->'` in `arrow`.
  - Stores `'card data'` if `edge.kind` equals `DATA`, otherwise `'can change'` in `label`.
  - Calls `lines.append(f' {edge.source} {arrow}|{label}| {edge.target}')`.
- Gives back the result of calling `'\n'.join(lines)`.

`src/pci_scope/domain/scope.py` lines 119 to 128:

````python
def render_scope_report(inventory: Inventory, result: ScopeResult) -> str:
    """Markdown: the diagram, then the list of in-scope systems with the reason for each, and the teams."""
    rows = "\n".join(f"| {system.name} | {system.team} | {'; '.join(why)} |" for system, why in result.systems)
    out = [system.name for system in inventory.systems if system.id not in result.ids and not system.external]
    return (
        f"# {inventory.title}\n\n```mermaid\n{render_mermaid(inventory, result)}\n```\n\n"
        f"**{len(result.systems)} systems and {len(result.teams)} teams in scope** ({', '.join(result.teams)}).\n\n"
        f"| System | Team | Why it is in scope |\n| --- | --- | --- |\n{rows}\n\n"
        f"Out of scope: {', '.join(out) if out else 'none'}.\n"
    )
````

**Function `render_scope_report`.** Markdown: the diagram, then the list of in-scope systems with the reason for each, and the teams.

It takes: `inventory` (a `Inventory`); `result` (a `ScopeResult`).

It gives back a `str`.

Step by step:

- Stores the result of calling `'\n'.join((f"| {system.name} | {system.team} | {'; '.join(why)} |" for system, why in res…` in `rows`.
- Stores a new list made by a loop (`[system.name for system in inventory.systems if system.id not in resu…`) in `out`.
- Gives back a text built with values filled in (`f"# {inventory.title}\n\n```mermaid\n{render_mermaid(inventory, resul…`).

`src/pci_scope/domain/scope.py` lines 131 to 140:

```python
def compare_scope(before: ScopeResult, after: ScopeResult) -> str:
    """The reduction in words: counts, the systems that left scope, and the ones that stay and why."""
    left = [system.name for system, _ in before.systems if system.id not in after.ids]
    stay = [f"{system.name} ({'; '.join(why)})" for system, why in after.systems]
    return (
        f"Before: {len(before.systems)} systems and {len(before.teams)} teams in scope.\n"
        f"After: {len(after.systems)} systems and {len(after.teams)} teams in scope.\n"
        f"Left scope: {', '.join(left) or 'nothing'}.\n"
        f"Still in scope: {'; '.join(stay) or 'nothing'}.\n"
    )
```

**Function `compare_scope`.** The reduction in words: counts, the systems that left scope, and the ones that stay and why.

It takes: `before` (a `ScopeResult`); `after` (a `ScopeResult`).

It gives back a `str`.

Step by step:

- Stores a new list made by a loop (`[system.name for system, _ in before.systems if system.id not in afte…`) in `left`.
- Stores a new list made by a loop (`[f"{system.name} ({'; '.join(why)})" for system, why in after.systems]`) in `stay`.
- Gives back a text built with values filled in (`f"Before: {len(before.systems)} systems and {len(before.teams)} teams…`).

### `src/pci_scope/domain/webhook.py`

`src/pci_scope/domain/webhook.py` lines 1 to 6:

```python
"""Webhook signatures: the provider signs the body with a shared secret and a timestamp; the merchant verifies both."""

from __future__ import annotations

import hashlib
import hmac
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Webhook signatures: the provider signs the body with a shared secret and a timestamp; the merchant verifies both.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `hashlib`.
- It imports module `hmac`.

`src/pci_scope/domain/webhook.py` lines 8 to 8:

```python
TOLERANCE_SECONDS = 300
```

> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the number `300` in `TOLERANCE_SECONDS`.

`src/pci_scope/domain/webhook.py` lines 11 to 14:

```python
def sign(secret: str, body: bytes, timestamp: int) -> str:
    """The header value `t=<timestamp>,v1=<hex hmac>` over `<timestamp>.<body>`."""
    signature = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={signature}"
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Function `sign`.** The header value `t=<timestamp>,v1=<hex hmac>` over `<timestamp>.<body>`.

It takes: `secret` (a `str`); `body` (a `bytes`); `timestamp` (a `int`).

It gives back a `str`.

Step by step:

- Stores the result of calling `hmac.new(secret.encode(), f'{timestamp}.'.encode() + body, hashlib.sha256).hexdigest()` in `signature`.
- Gives back a text built with values filled in (`f't={timestamp},v1={signature}'`).

`src/pci_scope/domain/webhook.py` lines 17 to 26:

```python
def verify(secret: str, body: bytes, header: str | None, now: int, tolerance: int = TOLERANCE_SECONDS) -> bool:
    """True only for a signature made with the secret, over this body, no older (or newer) than the tolerance."""
    if not header:
        return False
    parts = dict(item.split("=", 1) for item in header.split(",") if "=" in item)
    if not parts.get("t", "").isdigit() or "v1" not in parts:
        return False
    timestamp = int(parts["t"])
    expected = sign(secret, body, timestamp).split("v1=", 1)[1]
    return hmac.compare_digest(parts["v1"], expected) and abs(now - timestamp) <= tolerance
```

> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.
> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.

**Function `verify`.** True only for a signature made with the secret, over this body, no older (or newer) than the tolerance.

It takes: `secret` (a `str`); `body` (a `bytes`); `header` (a `str | None`); `now` (a `int`); `tolerance` (a `int`), default `TOLERANCE_SECONDS`.

It gives back a `bool`.

Step by step:

- If not (`header`):
  - Gives back `False`.
- Stores the result of calling `dict((item.split('=', 1) for item in header.split(',') if '=' in item))` in `parts`.
- If not (`parts.get('t', '').isdigit()`) or `'v1'` is not in `parts`:
  - Gives back `False`.
- Stores the result of calling `int(parts['t'])` in `timestamp`.
- Stores `sign(secret, body, timestamp).split('v1=', 1)[1]` in `expected`.
- Gives back whether `hmac.compare_digest(parts['v1'], expected)` and `abs(now - timestamp)` is at most `tolerance`.

## Try it yourself

```bash
.venv/bin/python -c "import pci_scope.domain.card; print(pci_scope.domain.card.__doc__)"
```
Prints the module's description: `Card data: how to recognize a card number or a card field in text, and the published test cards.`

```bash
.venv/bin/python -c "import pci_scope.domain.evidence; print(pci_scope.domain.evidence.__doc__)"
```
Prints the module's description: `The evidence pack for a reduced-scope assessment: each requirement maps to evidence, every file exists, says what it`

```bash
.venv/bin/mypy
```
Checks the whole project (the `files` setting in `pyproject.toml`), these files included. Prints `Success: no issues found in 46 source files`.

```bash
.venv/bin/ruff check src/pci_scope/__init__.py src/pci_scope/domain/__init__.py src/pci_scope/domain/card.py src/pci_scope/domain/evidence.py src/pci_scope/domain/findings.py src/pci_scope/domain/har.py
```
Prints `All checks passed!`.

```bash
grep -c "^def \|^class \|    def " src/pci_scope/domain/card.py
```
Counts the functions, methods and classes in `src/pci_scope/domain/card.py`.

## Mistakes people make

- Reading a file or printing from a domain function. Input and output belong to the outer layers.
- Importing a framework (Flask, psycopg) here; the contract in `pyproject.toml` forbids it.
- Changing a value in place. The domain uses frozen values, so a change makes a new value.

## Check yourself

1. What is `luhn_valid` for?
   **Answer:** The Luhn check every card number passes.
2. What is `mask` for?
   **Answer:** The first six and last four digits, the rest as stars: enough to tell the card in a report, never the number.
3. What is `CardFinding` for?
   **Answer:** Card data found in a place where it must not be.
4. What is `scan_text` for?
   **Answer:** Card numbers (13 to 19 digits that pass the Luhn check, spaces or dashes allowed) and card fields with a value.
5. What is `card_field_names` for?
   **Answer:** The names of card input fields present in a body or a page (`card[number]`, `cvc`, `card_number`, ...).

## Further reading

- Python 3.12 tutorial, classes: <https://docs.python.org/3.12/tutorial/classes.html>
- Python 3.12 language reference: <https://docs.python.org/3.12/reference/>
- Type hints: <https://docs.python.org/3.12/library/typing.html>
