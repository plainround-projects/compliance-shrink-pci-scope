# tomllib (reading the scope inventories and the requirements)

## What it is

`tomllib` is the standard Python module that reads TOML text (see `toml.md`). `tomllib.loads(text)` returns nested dictionaries and
lists. It can only read TOML, not write it.

## Why this repository uses it

The scope is **computed from data**: two inventories of systems and links, one for the naive checkout and one for the redesign. The
requirements and the evidence that proves each are data too. Keeping them in TOML lets the calculator and the verifier read the same
files a human reviews.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/infrastructure/catalog.py` | `load_inventory`, `load_requirements`. |
| `scope/before.toml`, `scope/after.toml` | The inventories. |
| `controls/requirements.toml` | The requirements, their evidence and the gaps. |

## How it works underneath

`tomllib.loads` parses the text into dictionaries. Each `[[system]]` block appends one table to the list under `system`; `[[edge]]` does
the same for links. A syntax error raises `tomllib.TOMLDecodeError`. TOML checks syntax only, so the catalog checks meaning.

## Walkthrough of this repository's use

`src/pci_scope/infrastructure/catalog.py`:

```python
def _load(path: Path) -> dict[str, Any]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as problem:
        raise CatalogError(f"{path}: {problem}") from None
```

Either an unreadable file (`OSError`) or bad TOML becomes the program's own `CatalogError`; `from None` hides the library's traceback.

`src/pci_scope/infrastructure/catalog.py`:

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

- A **generator expression** inside `tuple(...)` builds one `System` per `[[system]]` table; `item.get("touches_card", False)` reads an
  optional flag with a default.
- `Edge(item["from"], item["to"], item["kind"])` builds each link; a missing key raises `KeyError`, reported as `missing 'key'`.
- The last loop checks **meaning**: every edge must be `data` or `control` and must connect systems that exist. A typo in an id is an
  error, not a silently missing arrow.

`src/pci_scope/infrastructure/catalog.py`:

```python
def load_requirements(path: Path) -> tuple[list[Requirement], list[Gap]]:
    """Read `controls/requirements.toml`: the requirements with their evidence, and the tracked gaps."""
    data = _load(path)
    try:
        requirements = [
            Requirement(
                item["id"], item["text"],
                tuple(EvidenceSpec(e["file"], e["kind"], e["proves"]) for e in item.get("evidence", [])),
```

Each `[[requirement]]` carries nested `[[requirement.evidence]]` items (the files that prove it). The `[[gap]]` tables are known gaps tracked on purpose.

## Try it yourself

```bash
.venv/bin/python -c "import tomllib; d = tomllib.load(open('scope/after.toml','rb')); print(d['title']); print([s['id'] for s in d['system']])"
```
Prints the title of the redesigned inventory and the system ids.

```bash
make scope | head -20
```
Prints the scope before the redesign: a Mermaid diagram and a table (needs no server).

```bash
.venv/bin/python -c "import tomllib; print(tomllib.loads('[[x]]\na = 1\n[[x]]\na = 2'))"
```
Prints `{'x': [{'a': 1}, {'a': 2}]}`.

```bash
.venv/bin/python -c "import tomllib; tomllib.loads('x = ')" 2>&1 | tail -1
```
Prints a `TOMLDecodeError`.

## Mistakes people make

- **Opening the file in text mode** for `tomllib.load`: it needs binary. This code uses `loads` on text.
- **Trusting the data.** The catalog rejects unknown edge kinds and unknown system ids.
- **Letting the inventory drift from the real system.** The scope is only as true as its inventory, which is why the lesson also measures
  real traffic.

## Check yourself

1. What does `[[system]]` do?
   **Answer:** Adds one table to a list named `system`.
2. Why are edge ids checked against the systems?
   **Answer:** A typo would otherwise silently drop an arrow.
3. What is `tomllib.TOMLDecodeError`?
   **Answer:** The error for invalid TOML syntax.
4. Why wrap errors in `CatalogError`?
   **Answer:** The command line turns it into one message and exit code 2.
5. What does `item.get("external", False)` do?
   **Answer:** Reads an optional flag with a default.

## Further reading

- `tomllib` (Python 3.12): <https://docs.python.org/3.12/library/tomllib.html>
- TOML 1.0.0: <https://toml.io/en/v1.0.0>
