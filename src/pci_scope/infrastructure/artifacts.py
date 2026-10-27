"""Where card data could end up on the merchant's side: log files, the database as SQL text, backups."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path


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


class NaiveArtifacts:
    """The naive app's request log."""

    def __init__(self, log: Path) -> None:
        self._log = log

    def artifacts(self) -> Iterator[tuple[str, str]]:
        """The log, if it exists."""
        if self._log.is_file():
            yield self._log.name, self._log.read_text(encoding="utf-8")


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
