# Infrastructure layer code

## What it is

The adapters: the code that really reads files, talks to a database or a network, and reads the environment. (Every term is explained where it first appears in the walkthrough below.)

## Why this repository uses it

This is where the repository's infrastructure work happens. Reading it file by file, with every line explained, is how a reader sees the work that was done.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/infrastructure/__init__.py` | 1 lines. Adapters: the provider over HTTP, SQLite, the file system, the environment. Depends on application and domain. |
| `src/pci_scope/infrastructure/artifacts.py` | 45 lines. Where card data could end up on the merchant's side: log files, the database as SQL text, backups. |
| `src/pci_scope/infrastructure/catalog.py` | 58 lines. The scope inventories, the requirements and the gaps, read from TOML files. |
| `src/pci_scope/infrastructure/evidence_store.py` | 49 lines. The evidence folder on disk, with a manifest of hashes. |
| `src/pci_scope/infrastructure/logging_setup.py` | 26 lines. Structured JSON logs on standard output: level, time, logger, message and a few safe fields. No secrets. |
| `src/pci_scope/infrastructure/provider_http.py` | 82 lines. The payment provider over HTTP: a form-encoded payment-intents style API, with a timeout and retries on each … |
| `src/pci_scope/infrastructure/settings.py` | 52 lines. Settings from the environment, validated once at start-up (twelve-factor). Keys and secrets come only from he… |
| `src/pci_scope/infrastructure/sqlite_orders.py` | 68 lines. Orders in SQLite. The schema has no column that could hold a card number, only provider tokens. |

## How it works underneath

Each adapter implements a port from the application layer using a real technology (the file system, SQLite or PostgreSQL, HTTP, the environment). They are kept thin, so that swapping one changes nothing above. Tests exercise them on real temporary files or a real database.

## Walkthrough of this repository's use

### `src/pci_scope/infrastructure/__init__.py`

`src/pci_scope/infrastructure/__init__.py` lines 1 to 1:

```python
"""Adapters: the provider over HTTP, SQLite, the file system, the environment. Depends on application and domain."""
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.

**Module description.** Adapters: the provider over HTTP, SQLite, the file system, the environment. Depends on application and domain.

### `src/pci_scope/infrastructure/artifacts.py`

`src/pci_scope/infrastructure/artifacts.py` lines 1 to 6:

```python
"""Where card data could end up on the merchant's side: log files, the database as SQL text, backups."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Where card data could end up on the merchant's side: log files, the database as SQL text, backups.

Imports:

- From `__future__` it takes `annotations`.
- From `collections.abc` it takes `Callable, Iterator`.
- From `pathlib` it takes `Path`.

`src/pci_scope/infrastructure/artifacts.py` lines 9 to 33:

```python
class MerchantArtifacts:
    """Reads every log, database and backup under the state folder, except the folders named in `skip`."""

    def __init__(
        self,
        root: Path,
        dump_database: Callable[[], str] | None = None,
        database: Path | None = None,
        skip: tuple[str, ...] = (),
    ) -> None:
        self._root = root
        self._skip = skip
        self._dump = dump_database
        self._database = database

    def artifacts(self) -> Iterator[tuple[str, str]]:
        """(name, text), skipping the SQLite file itself: it is scanned through its SQL dump."""
        if self._dump is not None and self._database is not None:
            yield f"{self._database.name} (SQL dump)", self._dump()
        for path in sorted(self._root.rglob("*")):
            if not path.is_file() or path == self._database or path.suffix in (".db", ".db-journal"):
                continue
            if path.relative_to(self._root).parts[0] in self._skip:
                continue
            yield str(path.relative_to(self._root)), path.read_bytes().decode("utf-8", errors="replace")
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** `yield` makes a function a **generator**: calling it returns an iterator that hands out one value at a time and remembers where it stopped.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).

**Class `MerchantArtifacts`**. Reads every log, database and backup under the state folder, except the folders named in `skip`.

Its methods, in order:

**Method `__init__` of class `MerchantArtifacts`.**

It takes: `root` (a `Path`); `dump_database` (a `Callable[[], str] | None`), default `None`; `database` (a `Path | None`), default `None`; `skip` (a `tuple[str, ...]`), default `()`.

It gives back a `None`.

Step by step:

- Stores `root` in `self._root`.
- Stores `skip` in `self._skip`.
- Stores `dump_database` in `self._dump`.
- Stores `database` in `self._database`.

**Method `artifacts` of class `MerchantArtifacts`.** (name, text), skipping the SQLite file itself: it is scanned through its SQL dump.

It gives back a `Iterator[tuple[str, str]]`.

Step by step:

- If `self._dump` is not the same object as `None` and `self._database` is not the same object as `None`:
  - Hands out the tuple `(f'{self._database.name} (SQL dump)', self._dump())` to the caller (`yield`).
- For each `path` in the result of calling `sorted(self._root.rglob('*'))`:
  - If not (`path.is_file()`) or `path` equals `self._database` or `path.suffix` is in `('.db', '.db-journal')`:
    - Skips to the next item (`continue`).
  - If `path.relative_to(self._root).parts[0]` is in `self._skip`:
    - Skips to the next item (`continue`).
  - Hands out the tuple `(str(path.relative_to(self._root)), path.read_bytes().decode('utf-8',…` to the caller (`yield`).

`src/pci_scope/infrastructure/artifacts.py` lines 36 to 45:

```python
class NaiveArtifacts:
    """The naive app's request log."""

    def __init__(self, log: Path) -> None:
        self._log = log

    def artifacts(self) -> Iterator[tuple[str, str]]:
        """The log, if it exists."""
        if self._log.is_file():
            yield self._log.name, self._log.read_text(encoding="utf-8")
```

**Class `NaiveArtifacts`**. The naive app's request log.

Its methods, in order:

**Method `__init__` of class `NaiveArtifacts`.**

It takes: `log` (a `Path`).

It gives back a `None`.

Step by step:

- Stores `log` in `self._log`.

**Method `artifacts` of class `NaiveArtifacts`.** The log, if it exists.

It gives back a `Iterator[tuple[str, str]]`.

Step by step:

- If `self._log.is_file()`:
  - Hands out the tuple `(self._log.name, self._log.read_text(encoding='utf-8'))` to the caller (`yield`).

`src/pci_scope/infrastructure/artifacts.py` lines 48 to 59:

```python
class PathArtifacts:
    """Every file under the given paths (a file is itself; a folder is searched), for `pci-scope scan`."""

    def __init__(self, paths: list[Path]) -> None:
        self._paths = paths

    def artifacts(self) -> Iterator[tuple[str, str]]:
        """(name, text), reading bytes leniently so a binary file is scanned too."""
        for root in self._paths:
            files = [root] if root.is_file() else sorted(path for path in root.rglob("*") if path.is_file())
            for path in files:
                yield str(path), path.read_bytes().decode("utf-8", errors="replace")
```

> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.
> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.

**Class `PathArtifacts`**. Every file under the given paths (a file is itself; a folder is searched), for `pci-scope scan`.

Its methods, in order:

**Method `__init__` of class `PathArtifacts`.**

It takes: `paths` (a `list[Path]`).

It gives back a `None`.

Step by step:

- Stores `paths` in `self._paths`.

**Method `artifacts` of class `PathArtifacts`.** (name, text), reading bytes leniently so a binary file is scanned too.

It gives back a `Iterator[tuple[str, str]]`.

Step by step:

- For each `root` in `self._paths`:
  - Stores `[root]` if `root.is_file()`, otherwise `sorted((path for path in root.rglob('*'…` in `files`.
  - For each `path` in `files`:
    - Hands out the tuple `(str(path), path.read_bytes().decode('utf-8', errors='replace'))` to the caller (`yield`).

### `src/pci_scope/infrastructure/catalog.py`

`src/pci_scope/infrastructure/catalog.py` lines 1 to 11:

```python
"""The scope inventories, the requirements and the gaps, read from TOML files."""

from __future__ import annotations

import tomllib
from datetime import date
from pathlib import Path
from typing import Any

from pci_scope.domain.evidence import EvidenceSpec, Gap, Requirement
from pci_scope.domain.scope import CONTROL, DATA, Edge, Inventory, System
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The scope inventories, the requirements and the gaps, read from TOML files.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `tomllib`.
- From `datetime` it takes `date`.
- From `pathlib` it takes `Path`.
- From `typing` it takes `Any`.
- From `pci_scope.domain.evidence` it takes `EvidenceSpec, Gap, Requirement`.
- From `pci_scope.domain.scope` it takes `CONTROL, DATA, Edge, Inventory, System`.

`src/pci_scope/infrastructure/catalog.py` lines 14 to 15:

```python
class CatalogError(ValueError):
    """A TOML file is missing, malformed, or holds an unknown value."""
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A class that inherits from `Exception` is a new kind of **error**. `raise` stops the current function with it, and a `try ... except` further up decides what to do.

**Class `CatalogError`**, a kind of `ValueError`. A TOML file is missing, malformed, or holds an unknown value.

`src/pci_scope/infrastructure/catalog.py` lines 18 to 22:

```python
def _load(path: Path) -> dict[str, Any]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as problem:
        raise CatalogError(f"{path}: {problem}") from None
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A **`try` / `except` block** runs the steps under `try`. If an error of the named kind happens, Python jumps to the matching `except` steps instead of stopping the program. `finally` steps always run.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Function `_load`.**

It takes: `path` (a `Path`).

It gives back a `dict[str, Any]`.

Step by step:

- Tries:
  - Gives back the result of calling `tomllib.loads(path.read_text(encoding='utf-8'))`.
- If `(OSError, tomllib.TOMLDecodeError)` happens (named `problem`):
  - Stops here by raising `CatalogError(f'{path}: {problem}')` (`from None` hides the earlier error).

`src/pci_scope/infrastructure/catalog.py` lines 25 to 44:

```python
def load_inventory(path: Path) -> Inventory:
    """Read `scope/before.toml` or `scope/after.toml`."""
    data = _load(path)
    try:
        systems = tuple(
            System(
                item["id"], item["name"], item["team"], item.get("touches_card", False),
                item.get("serves_payment_page", False), item.get("external", False),
            )
            for item in data.get("system", [])
        )  # fmt: skip
        edges = tuple(Edge(item["from"], item["to"], item["kind"]) for item in data.get("edge", []))
        title = data["title"]
    except KeyError as missing:
        raise CatalogError(f"{path}: missing {missing}") from None
    ids = {system.id for system in systems}
    for edge in edges:
        if edge.kind not in (DATA, CONTROL) or edge.source not in ids or edge.target not in ids:
            raise CatalogError(f"{path}: bad edge {edge.source} -> {edge.target} ({edge.kind})")
    return Inventory(title, systems, edges)
```

> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** A **set comprehension** `{x for ...}` builds a set (a collection with no duplicates) with a loop.
> **In plain words.** A **generator expression** `(x for x in items)` is like a list comprehension, but it hands out one value at a time instead of building the whole list; here it is passed straight to a function such as `tuple(...)` or `sum(...)`.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.

**Function `load_inventory`.** Read `scope/before.toml` or `scope/after.toml`.

It takes: `path` (a `Path`).

It gives back a `Inventory`.

Step by step:

- Stores the result of calling `_load(path)` in `data`.
- Tries:
  - Stores the result of calling `tuple((System(item['id'], item['name'], item['team'], item.get('touches_card', False), it…` in `systems`.
  - Stores the result of calling `tuple((Edge(item['from'], item['to'], item['kind']) for item in data.get('edge', [])))` in `edges`.
  - Stores `data['title']` in `title`.
- If `KeyError` happens (named `missing`):
  - Stops here by raising `CatalogError(f'{path}: missing {missing}')` (`from None` hides the earlier error).
- Stores a new set made by a loop (`{system.id for system in systems}`) in `ids`.
- For each `edge` in `edges`:
  - If `edge.kind` is not in `(DATA, CONTROL)` or `edge.source` is not in `ids` or `edge.target` is not in `ids`:
    - Stops here by raising `CatalogError(f'{path}: bad edge {edge.source} -> {edge.target} ({edge.kind})')`.
- Gives back the result of calling `Inventory(title, systems, edges)`.

`src/pci_scope/infrastructure/catalog.py` lines 47 to 69:

```python
def load_requirements(path: Path) -> tuple[list[Requirement], list[Gap]]:
    """Read `controls/requirements.toml`: the requirements with their evidence, and the tracked gaps."""
    data = _load(path)
    try:
        requirements = [
            Requirement(
                item["id"], item["text"],
                tuple(EvidenceSpec(e["file"], e["kind"], e["proves"]) for e in item.get("evidence", [])),
            )
            for item in data.get("requirement", [])
        ]  # fmt: skip
        gaps = [
            Gap(
                g["requirement"],
                g.get("reason", ""),
                g.get("ticket", ""),
                g.get("due") if isinstance(g.get("due"), date) else None,
            )
            for g in data.get("gap", [])
        ]
    except KeyError as missing:
        raise CatalogError(f"{path}: missing {missing}") from None
    return requirements, gaps
```

> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.
> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.

**Function `load_requirements`.** Read `controls/requirements.toml`: the requirements with their evidence, and the tracked gaps.

It takes: `path` (a `Path`).

It gives back a `tuple[list[Requirement], list[Gap]]`.

Step by step:

- Stores the result of calling `_load(path)` in `data`.
- Tries:
  - Stores a new list made by a loop (`[Requirement(item['id'], item['text'], tuple((EvidenceSpec(e['file'],…`) in `requirements`.
  - Stores a new list made by a loop (`[Gap(g['requirement'], g.get('reason', ''), g.get('ticket', ''), g.ge…`) in `gaps`.
- If `KeyError` happens (named `missing`):
  - Stops here by raising `CatalogError(f'{path}: missing {missing}')` (`from None` hides the earlier error).
- Gives back the tuple `(requirements, gaps)`.

### `src/pci_scope/infrastructure/evidence_store.py`

`src/pci_scope/infrastructure/evidence_store.py` lines 1 to 9:

```python
"""The evidence folder on disk, with a manifest of hashes."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from pci_scope.domain.evidence import ManifestEntry, digest
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The evidence folder on disk, with a manifest of hashes.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `json`.
- From `datetime` it takes `UTC, datetime`.
- From `pathlib` it takes `Path`.
- From `pci_scope.domain.evidence` it takes `ManifestEntry, digest`.

`src/pci_scope/infrastructure/evidence_store.py` lines 11 to 12:

```python
MANIFEST = "manifest.json"
_TIME = "%Y-%m-%dT%H:%M:%SZ"
```

> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the text `'manifest.json'` in `MANIFEST`.
- Stores the text `'%Y-%m-%dT%H:%M:%SZ'` in `_TIME`.

`src/pci_scope/infrastructure/evidence_store.py` lines 15 to 16:

```python
class FileEvidenceStore:
    """Files directly inside one folder."""
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.

**Class `FileEvidenceStore`**. Files directly inside one folder.

`src/pci_scope/infrastructure/evidence_store.py` lines 18 to 19:

```python
    def __init__(self, directory: Path) -> None:
        self._dir = directory.resolve()
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.

**Method `__init__` of class `FileEvidenceStore`.**

It takes: `directory` (a `Path`).

It gives back a `None`.

Step by step:

- Stores the result of calling `directory.resolve()` in `self._dir`.

`src/pci_scope/infrastructure/evidence_store.py` lines 21 to 25:

```python
    def _path(self, name: str) -> Path:
        path = (self._dir / name).resolve()
        if path.parent != self._dir:
            raise ValueError(f"evidence files live directly in {self._dir.name}: {name}")
        return path
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Method `_path` of class `FileEvidenceStore`.**

It takes: `name` (a `str`).

It gives back a `Path`.

Step by step:

- Stores the result of calling `(self._dir / name).resolve()` in `path`.
- If `path.parent` is different from `self._dir`:
  - Stops here by raising `ValueError(f'evidence files live directly in {self._dir.name}: {name}')`.
- Gives back `path`.

`src/pci_scope/infrastructure/evidence_store.py` lines 27 to 37:

```python
    def write(self, name: str, text: str, requirement: str, produced_at: datetime) -> None:
        """Write the file and record it in the manifest."""
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path(name).write_text(text, encoding="utf-8")
        entries = self._load()
        entries[name] = {
            "requirement": requirement,
            "produced_at": produced_at.astimezone(UTC).strftime(_TIME),
            "sha256": digest(text),
        }
        self._path(MANIFEST).write_text(json.dumps(entries, indent=2, sort_keys=True) + "\n", encoding="utf-8")
```

> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.

**Method `write` of class `FileEvidenceStore`.** Write the file and record it in the manifest.

It takes: `name` (a `str`); `text` (a `str`); `requirement` (a `str`); `produced_at` (a `datetime`).

It gives back a `None`.

Step by step:

- Calls `self._dir.mkdir(parents=True, exist_ok=True)`.
- Calls `self._path(name).write_text(text, encoding='utf-8')`.
- Stores the result of calling `self._load()` in `entries`.
- Stores the dictionary `{'requirement': requirement, 'produced_at': produced_at.astimezone(UT…` in `entries[name]`.
- Calls `self._path(MANIFEST).write_text(json.dumps(entries, indent=2, sort_keys=True) + '\n', encoding='utf-8')`.

`src/pci_scope/infrastructure/evidence_store.py` lines 39 to 43:

```python
    def read_all(self) -> dict[str, str]:
        """Every file in the folder."""
        if not self._dir.is_dir():
            return {}
        return {path.name: path.read_text(encoding="utf-8") for path in sorted(self._dir.iterdir()) if path.is_file()}
```

> **In plain words.** A **dictionary comprehension** `{k: v for ...}` builds a dictionary with a loop written inside braces.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Method `read_all` of class `FileEvidenceStore`.** Every file in the folder.

It gives back a `dict[str, str]`.

Step by step:

- If not (`self._dir.is_dir()`):
  - Gives back the dictionary `{}`.
- Gives back a new dictionary made by a loop (`{path.name: path.read_text(encoding='utf-8') for path in sorted(self.…`).

`src/pci_scope/infrastructure/evidence_store.py` lines 45 to 55:

```python
    def manifest(self) -> dict[str, ManifestEntry]:
        """The manifest entries by file name."""
        return {
            name: ManifestEntry(
                name,
                item["requirement"],
                datetime.strptime(item["produced_at"], _TIME).replace(tzinfo=UTC),
                item["sha256"],
            )
            for name, item in self._load().items()
        }
```

**Method `manifest` of class `FileEvidenceStore`.** The manifest entries by file name.

It gives back a `dict[str, ManifestEntry]`.

Step by step:

- Gives back a new dictionary made by a loop (`{name: ManifestEntry(name, item['requirement'], datetime.strptime(ite…`).

`src/pci_scope/infrastructure/evidence_store.py` lines 57 to 61:

```python
    def _load(self) -> dict[str, dict[str, str]]:
        path = self._path(MANIFEST)
        if not path.is_file():
            return {}
        return {str(name): dict(item) for name, item in json.loads(path.read_text(encoding="utf-8")).items()}
```

**Method `_load` of class `FileEvidenceStore`.**

It gives back a `dict[str, dict[str, str]]`.

Step by step:

- Stores the result of calling `self._path(MANIFEST)` in `path`.
- If not (`path.is_file()`):
  - Gives back the dictionary `{}`.
- Gives back a new dictionary made by a loop (`{str(name): dict(item) for name, item in json.loads(path.read_text(en…`).

### `src/pci_scope/infrastructure/logging_setup.py`

`src/pci_scope/infrastructure/logging_setup.py` lines 1 to 8:

```python
"""Structured JSON logs on standard output: level, time, logger, message and a few safe fields. No secrets."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Structured JSON logs on standard output: level, time, logger, message and a few safe fields. No secrets.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `json`.
- It imports module `logging`.
- It imports module `sys`.
- From `datetime` it takes `UTC, datetime`.

`src/pci_scope/infrastructure/logging_setup.py` lines 10 to 10:

```python
_SAFE_FIELDS = ("method", "path", "status", "duration_ms")
```

> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the tuple `('method', 'path', 'status', 'duration_ms')` in `_SAFE_FIELDS`.

`src/pci_scope/infrastructure/logging_setup.py` lines 13 to 25:

```python
class JsonFormatter(logging.Formatter):
    """One JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        """Render a record; only the whitelisted extra fields are included."""
        document = {
            "time": datetime.fromtimestamp(record.created, UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        document.update({name: getattr(record, name) for name in _SAFE_FIELDS if hasattr(record, name)})
        return json.dumps(document)
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.
> **In plain words.** A **dictionary comprehension** `{k: v for ...}` builds a dictionary with a loop written inside braces.

**Class `JsonFormatter`**, a kind of `logging.Formatter`. One JSON object per line.

Its methods, in order:

**Method `format` of class `JsonFormatter`.** Render a record; only the whitelisted extra fields are included.

It takes: `record` (a `logging.LogRecord`).

It gives back a `str`.

Step by step:

- Stores the dictionary `{'time': datetime.fromtimestamp(record.created, UTC).strftime('%Y-%m-…` in `document`.
- Calls `document.update({name: getattr(record, name) for name in _SAFE_FIELDS if hasattr(record, name)})`.
- Gives back the result of calling `json.dumps(document)`.

`src/pci_scope/infrastructure/logging_setup.py` lines 28 to 34:

```python
def configure_logging(level: str) -> None:
    """Send JSON logs to stdout at the given level."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
```

> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **slice** such as `text[:7]` or `items[1:]` takes part of a sequence: `[:7]` the first seven items, `[1:]` everything after the first.

**Function `configure_logging`.** Send JSON logs to stdout at the given level.

It takes: `level` (a `str`).

It gives back a `None`.

Step by step:

- Stores the result of calling `logging.StreamHandler(sys.stdout)` in `handler`.
- Calls `handler.setFormatter(JsonFormatter())`.
- Stores the result of calling `logging.getLogger()` in `root`.
- Stores the list `[handler]` in `root.handlers[:]`.
- Calls `root.setLevel(level)`.

### `src/pci_scope/infrastructure/provider_http.py`

`src/pci_scope/infrastructure/provider_http.py` lines 1 to 13:

```python
"""The payment provider over HTTP: a form-encoded payment-intents style API, with a timeout and retries on each call."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any

from pci_scope.domain.payment import Intent, PaymentError
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** The payment provider over HTTP: a form-encoded payment-intents style API, with a timeout and retries on each call.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `json`.
- It imports module `time`.
- It imports module `urllib.error`.
- It imports module `urllib.parse`.
- It imports module `urllib.request`.
- From `collections.abc` it takes `Callable`.
- From `typing` it takes `Any`.
- From `pci_scope.domain.payment` it takes `Intent, PaymentError`.

`src/pci_scope/infrastructure/provider_http.py` lines 15 to 15:

```python
ATTEMPTS = 3
```

> **In plain words.** A name written in CAPITAL letters is a **constant** by convention: a value set once, not changed later.

These module-level lines:

- Stores the number `3` in `ATTEMPTS`.

`src/pci_scope/infrastructure/provider_http.py` lines 18 to 19:

```python
class HttpProvider:
    """Calls the provider's server-side API with the secret key. Retries network errors and 5xx; a 4xx is the answer."""
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.

**Class `HttpProvider`**. Calls the provider's server-side API with the secret key. Retries network errors and 5xx; a 4xx is the answer.

`src/pci_scope/infrastructure/provider_http.py` lines 21 to 27:

```python
    def __init__(
        self, base_url: str, secret_key: str, timeout: float = 10.0, sleep: Callable[[float], None] = time.sleep
    ) -> None:
        self._base = base_url
        self._key = secret_key
        self._timeout = timeout
        self._sleep = sleep
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Method `__init__` of class `HttpProvider`.**

It takes: `base_url` (a `str`); `secret_key` (a `str`); `timeout` (a `float`), default `10.0`; `sleep` (a `Callable[[float], None]`), default `time.sleep`.

It gives back a `None`.

Step by step:

- Stores `base_url` in `self._base`.
- Stores `secret_key` in `self._key`.
- Stores `timeout` in `self._timeout`.
- Stores `sleep` in `self._sleep`.

`src/pci_scope/infrastructure/provider_http.py` lines 29 to 31:

```python
    def create_customer(self) -> str:
        """POST /v1/customers."""
        return str(self._post("/v1/customers", {})["id"])
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **dictionary** `{key: value}` maps keys to values.

**Method `create_customer` of class `HttpProvider`.** POST /v1/customers.

It gives back a `str`.

Step by step:

- Gives back the result of calling `str(self._post('/v1/customers', {})['id'])`.

`src/pci_scope/infrastructure/provider_http.py` lines 33 to 38:

```python
    def create_intent(self, amount_cents: int, currency: str, customer_id: str, save_card: bool) -> Intent:
        """POST /v1/payment_intents; with `save_card` the provider keeps the method for later off-session charges."""
        fields = {"amount": amount_cents, "currency": currency, "customer": customer_id}
        if save_card:
            fields["setup_future_usage"] = "off_session"
        return _intent(self._post("/v1/payment_intents", fields))
```

**Method `create_intent` of class `HttpProvider`.** POST /v1/payment_intents; with `save_card` the provider keeps the method for later off-session charges.

It takes: `amount_cents` (a `int`); `currency` (a `str`); `customer_id` (a `str`); `save_card` (a `bool`).

It gives back a `Intent`.

Step by step:

- Stores the dictionary `{'amount': amount_cents, 'currency': currency, 'customer': customer_i…` in `fields`.
- If `save_card`:
  - Stores the text `'off_session'` in `fields['setup_future_usage']`.
- Gives back the result of calling `_intent(self._post('/v1/payment_intents', fields))`.

`src/pci_scope/infrastructure/provider_http.py` lines 40 to 42:

```python
    def retrieve_intent(self, intent_id: str) -> Intent:
        """GET /v1/payment_intents/<id>."""
        return _intent(self._call("GET", f"/v1/payment_intents/{urllib.parse.quote(intent_id)}", None))
```

> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Method `retrieve_intent` of class `HttpProvider`.** GET /v1/payment_intents/<id>.

It takes: `intent_id` (a `str`).

It gives back a `Intent`.

Step by step:

- Gives back the result of calling `_intent(self._call('GET', f'/v1/payment_intents/{urllib.parse.quote(intent_id)}', None))`.

`src/pci_scope/infrastructure/provider_http.py` lines 44 to 50:

```python
    def charge_saved(self, customer_id: str, payment_method_id: str, amount_cents: int, currency: str) -> Intent:
        """POST /v1/payment_intents with confirm and off_session, from the tokens alone."""
        fields = {
            "amount": amount_cents, "currency": currency, "customer": customer_id,
            "payment_method": payment_method_id, "off_session": "true", "confirm": "true",
        }  # fmt: skip
        return _intent(self._post("/v1/payment_intents", fields))
```

**Method `charge_saved` of class `HttpProvider`.** POST /v1/payment_intents with confirm and off_session, from the tokens alone.

It takes: `customer_id` (a `str`); `payment_method_id` (a `str`); `amount_cents` (a `int`); `currency` (a `str`).

It gives back a `Intent`.

Step by step:

- Stores the dictionary `{'amount': amount_cents, 'currency': currency, 'customer': customer_i…` in `fields`.
- Gives back the result of calling `_intent(self._post('/v1/payment_intents', fields))`.

`src/pci_scope/infrastructure/provider_http.py` lines 52 to 54:

```python
    def refund(self, intent_id: str) -> str:
        """POST /v1/refunds."""
        return str(self._post("/v1/refunds", {"payment_intent": intent_id})["id"])
```

**Method `refund` of class `HttpProvider`.** POST /v1/refunds.

It takes: `intent_id` (a `str`).

It gives back a `str`.

Step by step:

- Gives back the result of calling `str(self._post('/v1/refunds', {'payment_intent': intent_id})['id'])`.

`src/pci_scope/infrastructure/provider_http.py` lines 56 to 57:

```python
    def _post(self, path: str, fields: dict[str, Any]) -> dict[str, Any]:
        return self._call("POST", path, urllib.parse.urlencode(fields).encode())
```

**Method `_post` of class `HttpProvider`.**

It takes: `path` (a `str`); `fields` (a `dict[str, Any]`).

It gives back a `dict[str, Any]`.

Step by step:

- Gives back the result of calling `self._call('POST', path, urllib.parse.urlencode(fields).encode())`.

`src/pci_scope/infrastructure/provider_http.py` lines 59 to 81:

```python
    def _call(self, method: str, path: str, body: bytes | None) -> dict[str, Any]:
        request = urllib.request.Request(
            self._base + path,
            data=body,
            method=method,
            headers={"Authorization": f"Bearer {self._key}", "Content-Type": "application/x-www-form-urlencoded"},
        )
        delay = 0.2
        for attempt in range(1, ATTEMPTS + 1):
            try:
                with urllib.request.urlopen(request, timeout=self._timeout) as response:
                    return dict(json.loads(response.read()))
            except urllib.error.HTTPError as problem:
                if problem.code < 500:
                    raise PaymentError(_message(problem)) from None
                if attempt == ATTEMPTS:
                    raise PaymentError("the payment provider is failing") from None
            except (urllib.error.URLError, TimeoutError, OSError):
                if attempt == ATTEMPTS:
                    raise PaymentError("the payment provider is unreachable") from None
            self._sleep(delay)
            delay *= 2
        raise AssertionError("unreachable")  # pragma: no cover
```

> **In plain words.** A **`for` loop** repeats its steps once for each item of a collection. `range(n)` counts from 0 to n-1.
> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **`try` / `except` block** runs the steps under `try`. If an error of the named kind happens, Python jumps to the matching `except` steps instead of stopping the program. `finally` steps always run.
> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.
> **In plain words.** A **`with` block** opens something (a file, a connection, a lock), runs the steps inside, and always closes it at the end, even if an error happens.
> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.

**Method `_call` of class `HttpProvider`.**

It takes: `method` (a `str`); `path` (a `str`); `body` (a `bytes | None`).

It gives back a `dict[str, Any]`.

Step by step:

- Stores the result of calling `urllib.request.Request(self._base + path, data=body, method=method, headers={'Authorizati…` in `request`.
- Stores the number `0.2` in `delay`.
- For each `attempt` in the result of calling `range(1, ATTEMPTS + 1)`:
  - Tries:
    - Inside a `with` block that opens `urllib.request.urlopen(request, timeout=self._timeout)` (named `response`):
      - Gives back the result of calling `dict(json.loads(response.read()))`.
  - If `urllib.error.HTTPError` happens (named `problem`):
    - If `problem.code` is less than `500`:
      - Stops here by raising `PaymentError(_message(problem))` (`from None` hides the earlier error).
    - If `attempt` equals `ATTEMPTS`:
      - Stops here by raising `PaymentError('the payment provider is failing')` (`from None` hides the earlier error).
  - If `(urllib.error.URLError, TimeoutError, OSError)` happens:
    - If `attempt` equals `ATTEMPTS`:
      - Stops here by raising `PaymentError('the payment provider is unreachable')` (`from None` hides the earlier error).
  - Calls `self._sleep(delay)`.
  - Multiplies the number `2` into/from `delay`.
- Stops here by raising `AssertionError('unreachable')`.

`src/pci_scope/infrastructure/provider_http.py` lines 84 to 88:

```python
def _message(problem: urllib.error.HTTPError) -> str:
    try:
        return str(json.loads(problem.read())["error"]["message"])
    except (ValueError, KeyError, TypeError):
        return f"the provider refused the request ({problem.code})"
```

**Function `_message`.**

It takes: `problem` (a `urllib.error.HTTPError`).

It gives back a `str`.

Step by step:

- Tries:
  - Gives back the result of calling `str(json.loads(problem.read())['error']['message'])`.
- If `(ValueError, KeyError, TypeError)` happens:
  - Gives back a text built with values filled in (`f'the provider refused the request ({problem.code})'`).

`src/pci_scope/infrastructure/provider_http.py` lines 91 to 100:

```python
def _intent(data: dict[str, Any]) -> Intent:
    return Intent(
        id=data["id"],
        status=data["status"],
        amount_cents=int(data["amount"]),
        currency=data["currency"],
        client_secret=data.get("client_secret", ""),
        payment_method_id=data.get("payment_method") or "",
        customer_id=data.get("customer") or "",
    )
```

**Function `_intent`.**

It takes: `data` (a `dict[str, Any]`).

It gives back a `Intent`.

Step by step:

- Gives back the result of calling `Intent(id=data['id'], status=data['status'], amount_cents=int(data['amount']), currency=d…`.

### `src/pci_scope/infrastructure/settings.py`

`src/pci_scope/infrastructure/settings.py` lines 1 to 7:

```python
"""Settings from the environment, validated once at start-up (twelve-factor). Keys and secrets come only from here."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Settings from the environment, validated once at start-up (twelve-factor). Keys and secrets come only from here.

Imports:

- From `__future__` it takes `annotations`.
- From `collections.abc` it takes `Mapping`.
- From `dataclasses` it takes `dataclass`.
- From `pathlib` it takes `Path`.

`src/pci_scope/infrastructure/settings.py` lines 10 to 11:

```python
class SettingsError(ValueError):
    """An environment variable is missing or holds a value the program must refuse."""
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.
> **In plain words.** A class that inherits from `Exception` is a new kind of **error**. `raise` stops the current function with it, and a `try ... except` further up decides what to do.

**Class `SettingsError`**, a kind of `ValueError`. An environment variable is missing or holds a value the program must refuse.

`src/pci_scope/infrastructure/settings.py` lines 14 to 29:

```python
@dataclass(frozen=True)
class Settings:
    """Everything the programs read from the environment."""

    provider_base_url: str
    provider_public_url: str
    secret_key: str
    publishable_key: str
    webhook_secret: str
    merchant_base_url: str
    naive_base_url: str
    database_path: Path
    naive_log_path: Path
    state_dir: Path
    evidence_dir: Path
    log_level: str
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **dataclass** is a class that mainly holds data. `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you from the annotated fields; `frozen=True` forbids changing a field after the object is created.

**Class `Settings`**. Everything the programs read from the environment. Decorators: `@dataclass(frozen=True)`.

Its parts:

- Field `provider_base_url`: a `str`.
- Field `provider_public_url`: a `str`.
- Field `secret_key`: a `str`.
- Field `publishable_key`: a `str`.
- Field `webhook_secret`: a `str`.
- Field `merchant_base_url`: a `str`.
- Field `naive_base_url`: a `str`.
- Field `database_path`: a `Path`.
- Field `naive_log_path`: a `Path`.
- Field `state_dir`: a `Path`.
- Field `evidence_dir`: a `Path`.
- Field `log_level`: a `str`.

`src/pci_scope/infrastructure/settings.py` lines 32 to 36:

```python
def _required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "")
    if not value:
        raise SettingsError(f"{name} is required")
    return value
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.
> **In plain words.** `obj[key]` looks a value up by key or position.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Function `_required`.**

It takes: `env` (a `Mapping[str, str]`); `name` (a `str`).

It gives back a `str`.

Step by step:

- Stores the result of calling `env.get(name, '')` in `value`.
- If not (`value`):
  - Stops here by raising `SettingsError(f'{name} is required')`.
- Gives back `value`.

`src/pci_scope/infrastructure/settings.py` lines 39 to 63:

```python
def load_settings(env: Mapping[str, str]) -> Settings:
    """Validate and collect the settings. A live key is refused: this project is for test mode only."""
    secret, publishable = _required(env, "PROVIDER_SECRET_KEY"), _required(env, "PROVIDER_PUBLISHABLE_KEY")
    if not secret.startswith("sk_test_") or not publishable.startswith("pk_test_"):
        raise SettingsError("only test-mode keys (sk_test_..., pk_test_...) are accepted; never use a live key here")
    webhook = _required(env, "WEBHOOK_SECRET")
    if len(webhook) < 32:
        raise SettingsError("WEBHOOK_SECRET must be at least 32 characters")
    level = env.get("LOG_LEVEL", "INFO").upper()
    if level not in ("DEBUG", "INFO", "WARNING", "ERROR"):
        raise SettingsError(f"LOG_LEVEL must be DEBUG, INFO, WARNING or ERROR, got {level!r}")
    return Settings(
        provider_base_url=_required(env, "PROVIDER_BASE_URL").rstrip("/"),
        provider_public_url=env.get("PROVIDER_PUBLIC_URL", _required(env, "PROVIDER_BASE_URL")).rstrip("/"),
        secret_key=secret,
        publishable_key=publishable,
        webhook_secret=webhook,
        merchant_base_url=_required(env, "MERCHANT_BASE_URL").rstrip("/"),
        naive_base_url=env.get("NAIVE_BASE_URL", "http://127.0.0.1:5002").rstrip("/"),
        database_path=Path(env.get("DATABASE_PATH", "state/merchant.db")),
        naive_log_path=Path(env.get("NAIVE_LOG_PATH", "state/naive/requests.log")),
        state_dir=Path(env.get("STATE_DIR", "state")),
        evidence_dir=Path(env.get("EVIDENCE_DIR", "evidence")),
        log_level=level,
    )
```

> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.

**Function `load_settings`.** Validate and collect the settings. A live key is refused: this project is for test mode only.

It takes: `env` (a `Mapping[str, str]`).

It gives back a `Settings`.

Step by step:

- Unpacks the tuple `(_required(env, 'PROVIDER_SECRET_KEY'), _required(env, 'PROVIDER_PUBL…` into `(secret, publishable)`.
- If not (`secret.startswith('sk_test_')`) or not (`publishable.startswith('pk_test_')`):
  - Stops here by raising `SettingsError('only test-mode keys (sk_test_..., pk_test_...) are accepted; never use a live key he…`.
- Stores the result of calling `_required(env, 'WEBHOOK_SECRET')` in `webhook`.
- If `len(webhook)` is less than `32`:
  - Stops here by raising `SettingsError('WEBHOOK_SECRET must be at least 32 characters')`.
- Stores the result of calling `env.get('LOG_LEVEL', 'INFO').upper()` in `level`.
- If `level` is not in `('DEBUG', 'INFO', 'WARNING', 'ERROR')`:
  - Stops here by raising `SettingsError(f'LOG_LEVEL must be DEBUG, INFO, WARNING or ERROR, got {level!r}')`.
- Gives back the result of calling `Settings(provider_base_url=_required(env, 'PROVIDER_BASE_URL').rstrip('/'), provider_publ…`.

### `src/pci_scope/infrastructure/sqlite_orders.py`

`src/pci_scope/infrastructure/sqlite_orders.py` lines 1 to 11:

```python
"""Orders in SQLite. The schema has no column that could hold a card number, only provider tokens."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from datetime import datetime
from pathlib import Path

from pci_scope.domain.payment import PAYMENT_STATUSES, Order
```

> **In plain words.** A **docstring** is a text in triple quotes as the first thing in a module, class or function. Python keeps it as the thing's description, and ruff requires one on public code.
> **In plain words.** An **import** brings a name from another file or from Python's standard library into this file, so this file can use it.
> **In plain words.** `from __future__ import annotations` makes every type hint in the file lazy text. Python no longer evaluates a hint when the file loads, so a hint may name a class defined further down.

**Module description.** Orders in SQLite. The schema has no column that could hold a card number, only provider tokens.

Imports:

- From `__future__` it takes `annotations`.
- It imports module `sqlite3`.
- From `collections.abc` it takes `Iterator`.
- From `contextlib` it takes `closing, contextmanager`.
- From `datetime` it takes `datetime`.
- From `pathlib` it takes `Path`.
- From `pci_scope.domain.payment` it takes `PAYMENT_STATUSES, Order`.

`src/pci_scope/infrastructure/sqlite_orders.py` lines 14 to 15:

```python
class SqliteOrders:
    """The merchant's order table (sql/001_schema.sql)."""
```

> **In plain words.** A **class** is a blueprint for objects that bundle data with the functions that work on it. `class B(A)` means B is a kind of A and starts with everything A has.

**Class `SqliteOrders`**. The merchant's order table (sql/001_schema.sql).

`src/pci_scope/infrastructure/sqlite_orders.py` lines 17 to 19:

```python
    def __init__(self, path: Path, now: type[datetime] = datetime) -> None:
        self._path = path
        self._now = now
```

> **In plain words.** A **type hint** such as `x: int` or `-> str` says what kind of value a name holds or a function gives back. Python does not enforce hints when the program runs; the type checker mypy reads them before.
> **In plain words.** `obj[key]` looks a value up by key or position.

**Method `__init__` of class `SqliteOrders`.**

It takes: `path` (a `Path`); `now` (a `type[datetime]`), default `datetime`.

It gives back a `None`.

Step by step:

- Stores `path` in `self._path`.
- Stores `now` in `self._now`.

`src/pci_scope/infrastructure/sqlite_orders.py` lines 21 to 28:

```python
    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._path, timeout=5)
        try:
            with connection:
                yield connection
        finally:
            connection.close()
```

> **In plain words.** A **`try` / `except` block** runs the steps under `try`. If an error of the named kind happens, Python jumps to the matching `except` steps instead of stopping the program. `finally` steps always run.
> **In plain words.** A call such as `f(a, key=value)` passes `a` by position and `key` by name (a **keyword argument**).
> **In plain words.** A **`with` block** opens something (a file, a connection, a lock), runs the steps inside, and always closes it at the end, even if an error happens.
> **In plain words.** `yield` makes a function a **generator**: calling it returns an iterator that hands out one value at a time and remembers where it stopped.

**Method `_connect` of class `SqliteOrders`.**

It gives back a `Iterator[sqlite3.Connection]`.

Decorators: `@contextmanager`.

Step by step:

- Stores the result of calling `sqlite3.connect(self._path, timeout=5)` in `connection`.
- Tries:
  - Inside a `with` block that opens `connection`:
    - Hands out `connection` to the caller (`yield`).
- Always, at the end:
  - Calls `connection.close()`.

`src/pci_scope/infrastructure/sqlite_orders.py` lines 30 to 34:

```python
    def initialize(self, schema: str) -> None:
        """Create the table from the schema script."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self._path)) as connection:
            connection.executescript(schema)
```

**Method `initialize` of class `SqliteOrders`.** Create the table from the schema script.

It takes: `schema` (a `str`).

It gives back a `None`.

Step by step:

- Calls `self._path.parent.mkdir(parents=True, exist_ok=True)`.
- Inside a `with` block that opens `closing(sqlite3.connect(self._path))` (named `connection`):
  - Calls `connection.executescript(schema)`.

`src/pci_scope/infrastructure/sqlite_orders.py` lines 36 to 44:

```python
    def create(self, intent_id: str, amount_cents: int, currency: str, customer_id: str) -> Order:
        """Insert a pending order."""
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO orders (payment_intent_id, amount_cents, currency, status, customer_id, created_at) "
                "VALUES (?, ?, ?, 'pending', ?, ?)",
                (intent_id, amount_cents, currency, customer_id, self._now.now().strftime("%Y-%m-%dT%H:%M:%SZ")),
            )
        return Order(int(cursor.lastrowid or 0), intent_id, amount_cents, currency, "pending", customer_id)
```

> **In plain words.** `return value` ends the function and gives the value back to whoever called it.
> **In plain words.** A **tuple** `(a, b)` is a fixed list of values that cannot be changed.

**Method `create` of class `SqliteOrders`.** Insert a pending order.

It takes: `intent_id` (a `str`); `amount_cents` (a `int`); `currency` (a `str`); `customer_id` (a `str`).

It gives back a `Order`.

Step by step:

- Inside a `with` block that opens `self._connect()` (named `connection`):
  - Stores the result of calling `connection.execute("INSERT INTO orders (payment_intent_id, amount_cents, currency, status…` in `cursor`.
- Gives back the result of calling `Order(int(cursor.lastrowid or 0), intent_id, amount_cents, currency, 'pending', customer_…`.

`src/pci_scope/infrastructure/sqlite_orders.py` lines 46 to 54:

```python
    def find(self, intent_id: str) -> Order | None:
        """The order for a payment intent."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, payment_intent_id, amount_cents, currency, status, customer_id, payment_method_id "
                "FROM orders WHERE payment_intent_id = ?",
                (intent_id,),
            ).fetchone()
        return Order(*row) if row else None
```

> **In plain words.** `A | B` in a type hint means "either A or B". `X | None` means a value that may be missing.
> **In plain words.** `A if test else B` is a **conditional expression**: its value is A when the test is true, otherwise B.
> **In plain words.** `*items` **unpacks** a sequence into separate values; `**options` does the same for a dictionary's keys and values.

**Method `find` of class `SqliteOrders`.** The order for a payment intent.

It takes: `intent_id` (a `str`).

It gives back a `Order | None`.

Step by step:

- Inside a `with` block that opens `self._connect()` (named `connection`):
  - Stores the result of calling `connection.execute('SELECT id, payment_intent_id, amount_cents, currency, status, custome…` in `row`.
- Gives back `Order(*row)` if `row`, otherwise `None`.

`src/pci_scope/infrastructure/sqlite_orders.py` lines 56 to 64:

```python
    def update(self, intent_id: str, status: str, payment_method_id: str) -> None:
        """Set the status and the saved payment-method token."""
        if status not in PAYMENT_STATUSES:
            raise ValueError(f"unknown status {status!r}")
        with self._connect() as connection:
            connection.execute(
                "UPDATE orders SET status = ?, payment_method_id = ? WHERE payment_intent_id = ?",
                (status, payment_method_id, intent_id),
            )
```

> **In plain words.** `==` tests equality, `is` tests that two names are the very same object (used for `None` and enum members), `in` tests membership.
> **In plain words.** `raise Error(...)` stops the current function by signalling an error. `raise ... from None` hides the earlier error, so the user sees only the new, clearer message.
> **In plain words.** An **f-string** `f"...{value}..."` is text with Python expressions in braces; Python replaces each by its value. `{x!r}` shows the value the way Python would write it, with quotes.

**Method `update` of class `SqliteOrders`.** Set the status and the saved payment-method token.

It takes: `intent_id` (a `str`); `status` (a `str`); `payment_method_id` (a `str`).

It gives back a `None`.

Step by step:

- If `status` is not in `PAYMENT_STATUSES`:
  - Stops here by raising `ValueError(f'unknown status {status!r}')`.
- Inside a `with` block that opens `self._connect()` (named `connection`):
  - Calls `connection.execute('UPDATE orders SET status = ?, payment_method_id = ? WHERE payment_intent_id = ?', (status…`.

`src/pci_scope/infrastructure/sqlite_orders.py` lines 66 to 69:

```python
    def dump(self) -> str:
        """The whole database as SQL text, for the scan and the backup."""
        with closing(sqlite3.connect(self._path)) as connection:
            return "\n".join(connection.iterdump())
```

**Method `dump` of class `SqliteOrders`.** The whole database as SQL text, for the scan and the backup.

It gives back a `str`.

Step by step:

- Inside a `with` block that opens `closing(sqlite3.connect(self._path))` (named `connection`):
  - Gives back the result of calling `'\n'.join(connection.iterdump())`.

`src/pci_scope/infrastructure/sqlite_orders.py` lines 71 to 74:

```python
    def columns(self) -> list[tuple[str, str]]:
        """(name, type) of every column in the orders table."""
        with closing(sqlite3.connect(self._path)) as connection:
            return [(row[1], row[2]) for row in connection.execute("PRAGMA table_info(orders)")]
```

> **In plain words.** A **list comprehension** `[x for x in items if test]` is a loop written inside brackets: it builds a new list from the items that pass the test.

**Method `columns` of class `SqliteOrders`.** (name, type) of every column in the orders table.

It gives back a `list[tuple[str, str]]`.

Step by step:

- Inside a `with` block that opens `closing(sqlite3.connect(self._path))` (named `connection`):
  - Gives back a new list made by a loop (`[(row[1], row[2]) for row in connection.execute('PRAGMA table_info(or…`).

`src/pci_scope/infrastructure/sqlite_orders.py` lines 76 to 82:

```python
    def rows(self, limit: int = 5) -> list[tuple[object, ...]]:
        """The first rows, for the evidence."""
        with closing(sqlite3.connect(self._path)) as connection:
            return connection.execute(
                "SELECT id, payment_intent_id, status, customer_id, payment_method_id FROM orders ORDER BY id LIMIT ?",
                (limit,),
            ).fetchall()
```

**Method `rows` of class `SqliteOrders`.** The first rows, for the evidence.

It takes: `limit` (a `int`), default `5`.

It gives back a `list[tuple[object, ...]]`.

Step by step:

- Inside a `with` block that opens `closing(sqlite3.connect(self._path))` (named `connection`):
  - Gives back the result of calling `connection.execute('SELECT id, payment_intent_id, status, customer_id, payment_method_id …`.

## Try it yourself

```bash
.venv/bin/python -c "import pci_scope.infrastructure.artifacts; print(pci_scope.infrastructure.artifacts.__doc__)"
```
Prints the module's description: `Where card data could end up on the merchant's side: log files, the database as SQL text, backups.`

```bash
.venv/bin/python -c "import pci_scope.infrastructure.catalog; print(pci_scope.infrastructure.catalog.__doc__)"
```
Prints the module's description: `The scope inventories, the requirements and the gaps, read from TOML files.`

```bash
.venv/bin/mypy
```
Checks the whole project (the `files` setting in `pyproject.toml`), these files included. Prints `Success: no issues found in 46 source files`.

```bash
.venv/bin/ruff check src/pci_scope/infrastructure/__init__.py src/pci_scope/infrastructure/artifacts.py src/pci_scope/infrastructure/catalog.py src/pci_scope/infrastructure/evidence_store.py src/pci_scope/infrastructure/logging_setup.py src/pci_scope/infrastructure/provider_http.py
```
Prints `All checks passed!`.

```bash
grep -c "^def \|^class \|    def " src/pci_scope/infrastructure/artifacts.py
```
Counts the functions, methods and classes in `src/pci_scope/infrastructure/artifacts.py`.

## Mistakes people make

- Putting a business rule in an adapter, where the domain tests cannot see it.
- Forgetting to close a connection or file. The adapters use `with` blocks and context managers.
- Trusting input from outside. Adapters check paths, shapes and ranges before handing values inward.

## Check yourself

1. What is `MerchantArtifacts` for?
   **Answer:** Reads every log, database and backup under the state folder, except the folders named in `skip`.
2. What is `NaiveArtifacts` for?
   **Answer:** The naive app's request log.
3. What is `PathArtifacts` for?
   **Answer:** Every file under the given paths (a file is itself; a folder is searched), for `pci-scope scan`.
4. What is `CatalogError` for?
   **Answer:** A TOML file is missing, malformed, or holds an unknown value.
5. What is `load_inventory` for?
   **Answer:** Read `scope/before.toml` or `scope/after.toml`.

## Further reading

- Python 3.12 tutorial, classes: <https://docs.python.org/3.12/tutorial/classes.html>
- Python 3.12 language reference: <https://docs.python.org/3.12/reference/>
- Type hints: <https://docs.python.org/3.12/library/typing.html>
