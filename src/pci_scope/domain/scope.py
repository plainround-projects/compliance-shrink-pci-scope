"""PCI scope as a computation: which systems are in scope, why, and which teams carry the requirements."""

from __future__ import annotations

from dataclasses import dataclass

DATA = "data"
CONTROL = "control"


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
    edges: tuple[Edge, ...]


@dataclass(frozen=True)
class ScopeResult:
    """Each in-scope system with the reasons, in inventory order, and the teams that carry the requirements."""

    systems: tuple[tuple[System, tuple[str, ...]], ...]
    teams: tuple[str, ...]

    @property
    def ids(self) -> frozenset[str]:
        """The ids of the in-scope systems."""
        return frozenset(system.id for system, _ in self.systems)


def compute_scope(inventory: Inventory) -> ScopeResult:
    """Card data spreads along `data` edges from the systems that touch it; the page host is in scope for the page's
    integrity; anything that can change an in-scope system, directly or through others, is in scope too.
    """
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

    ordered = tuple((system, tuple(reasons[system.id])) for system in inventory.systems if system.id in scope)
    teams = tuple(sorted({system.team for system, _ in ordered}))
    return ScopeResult(ordered, teams)


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
