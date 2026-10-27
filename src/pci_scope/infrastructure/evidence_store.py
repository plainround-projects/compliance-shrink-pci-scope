"""The evidence folder on disk, with a manifest of hashes."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from pci_scope.domain.evidence import ManifestEntry, digest

MANIFEST = "manifest.json"
_TIME = "%Y-%m-%dT%H:%M:%SZ"


class FileEvidenceStore:
    """Files directly inside one folder."""

    def __init__(self, directory: Path) -> None:
        self._dir = directory.resolve()

    def _path(self, name: str) -> Path:
        path = (self._dir / name).resolve()
        if path.parent != self._dir:
            raise ValueError(f"evidence files live directly in {self._dir.name}: {name}")
        return path

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

    def read_all(self) -> dict[str, str]:
        """Every file in the folder."""
        if not self._dir.is_dir():
            return {}
        return {path.name: path.read_text(encoding="utf-8") for path in sorted(self._dir.iterdir()) if path.is_file()}

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

    def _load(self) -> dict[str, dict[str, str]]:
        path = self._path(MANIFEST)
        if not path.is_file():
            return {}
        return {str(name): dict(item) for name, item in json.loads(path.read_text(encoding="utf-8")).items()}
