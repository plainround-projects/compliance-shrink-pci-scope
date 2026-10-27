# pathlib and file access

## What it is

`pathlib.Path` is the standard Python way to work with file and folder names. A `Path` object knows how to join
names with `/`, ask whether something exists, read and write text, and list a folder. It works the same on macOS,
Linux and Windows.

## Why this repository uses it

The program reads the repository's documents and writes a report. All file access goes through one small class
(`FileSystemStore`), which also refuses paths that escape the root folder.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/pci_scope/infrastructure/evidence_store.py` | `FileEvidenceStore`: writes the pack and its manifest. |
| `src/pci_scope/infrastructure/artifacts.py` | `MerchantArtifacts`, `NaiveArtifacts`, `PathArtifacts`: what the card scanner reads. |
| `src/pci_scope/interfaces/naive_app.py` | The naive app's log file. |
| `src/pci_scope/infrastructure/settings.py` | Turns folder settings into `Path` values. |

## How it works underneath

- A `Path` is only a name until you use it. `Path("docs") / "adr"` builds `docs/adr` without touching the disk.
- `.read_text(encoding="utf-8")` opens the file, reads all of it as text using that encoding, and closes it.
- `.resolve()` makes a path absolute and follows `..` and symbolic links. Comparing resolved paths is the safe way to
  test "is this inside that folder".
- `.parents` is the chain of containing folders.

## Walkthrough of this repository's use

`src/pci_scope/infrastructure/evidence_store.py`:

```python
class FileEvidenceStore:
    """Files directly inside one folder."""

    def __init__(self, directory: Path) -> None:
        self._dir = directory.resolve()

    def _path(self, name: str) -> Path:
        path = (self._dir / name).resolve()
        if path.parent != self._dir:
            raise ValueError(f"evidence files live directly in {self._dir.name}: {name}")
        return path
```

`_path` joins a name to the evidence folder, resolves it, and refuses any name that is not directly inside (`path.parent != self._dir`).

`src/pci_scope/infrastructure/artifacts.py`:

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

`PathArtifacts` lets the user scan any file or folder: `[root] if root.is_file() else sorted(path for path in root.rglob("*") if
path.is_file())`. `rglob("*")` walks a folder **recursively**. `read_bytes().decode("utf-8", errors="replace")` reads the raw bytes and
decodes them, replacing bytes that are not valid text, so a **binary file is scanned too** and nothing crashes. The method is a
**generator** (`yield`): it hands out one `(name, text)` pair at a time.

`src/pci_scope/infrastructure/artifacts.py`:

```python
    def artifacts(self) -> Iterator[tuple[str, str]]:
        """(name, text), skipping the SQLite file itself: it is scanned through its SQL dump."""
        if self._dump is not None and self._database is not None:
            yield f"{self._database.name} (SQL dump)", self._dump()
        for path in sorted(self._root.rglob("*")):
            if not path.is_file() or path == self._database or path.suffix in (".db", ".db-journal"):
                continue
            if path.relative_to(self._root).parts[0] in self._skip:
```

The merchant scan walks every file under the state folder, skips the SQLite file itself (it is scanned through its SQL dump, which is
text), and skips folders named in `skip`. `path.relative_to(self._root).parts[0]` is the first folder name of the relative path.

`src/pci_scope/interfaces/naive_app.py`:

```python
    log_path.parent.mkdir(parents=True, exist_ok=True)
```

Creates the log folder if it is missing before the file handler opens the log.

## Try it yourself

```bash
ls evidence
```
Lists the pack: `INDEX.md`, `manifest.json`, `payment.har`, `payment-summary.txt`, `proof-before.txt`, `proof-after.txt`, `route-check.txt`,
`scope-*.md`, `token-storage.txt`, `checkout-page-controls.txt`, `responsibilities.md`, `provider-attestation.md`.

```bash
.venv/bin/python -c "from pathlib import Path; p = Path('evidence') / 'payment.har'; print(p, p.exists(), p.suffix, p.parent)"
```
Prints `evidence/payment.har True .har evidence`.

```bash
.venv/bin/python -c "from pathlib import Path; from pci_scope.infrastructure.evidence_store import FileEvidenceStore; FileEvidenceStore(Path('evidence'))._path('../x')" 2>&1 | tail -1
```
Prints `ValueError: evidence files live directly in evidence: ../x`.

```bash
.venv/bin/python -c "from pathlib import Path; print(sorted(p.name for p in Path('scope').rglob('*.toml')))"
```
Prints `['after.toml', 'before.toml']`.

## Mistakes people make

- **Joining paths with `+`** and a slash character. Use `/`.
- **Forgetting the encoding** on Windows, where the default is not UTF-8.
- **Comparing unresolved paths**, so `docs/../x` looks like it is inside `docs`.
- **Letting user-supplied names reach the disk unchecked.** The store checks every path.

## Check yourself

1. What does `rglob("*")` do?
   **Answer:** Lists every path under a folder, recursively.
2. Why decode with `errors="replace"`?
   **Answer:** So a binary file can be scanned without an error.
3. What does `path.parent != self._dir` protect against?
   **Answer:** A name that would put the file outside the evidence folder.
4. What is a generator?
   **Answer:** A function with `yield` that produces its values one at a time.
5. Why does the scanner read the SQLite file through its SQL dump?
   **Answer:** The dump is text a pattern can search; the binary file is not.

## Further reading

- `pathlib` (Python 3.12): <https://docs.python.org/3.12/library/pathlib.html>
