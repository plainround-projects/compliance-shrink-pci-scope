"""The scope inventories, the requirements and the gaps, read from TOML files."""

from __future__ import annotations

import tomllib
from datetime import date
from pathlib import Path
from typing import Any

from pci_scope.domain.evidence import EvidenceSpec, Gap, Requirement
from pci_scope.domain.scope import CONTROL, DATA, Edge, Inventory, System


class CatalogError(ValueError):
    """A TOML file is missing, malformed, or holds an unknown value."""


def _load(path: Path) -> dict[str, Any]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as problem:
        raise CatalogError(f"{path}: {problem}") from None


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
