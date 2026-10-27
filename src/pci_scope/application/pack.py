"""Text for the evidence pack: the scope documents, the route check, the page controls, the token storage, the index."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from pci_scope.domain.evidence import Gap, ManifestEntry, Requirement
from pci_scope.domain.scope import Inventory, compare_scope, compute_scope, render_scope_report


def scope_documents(before: Inventory, after: Inventory) -> dict[str, str]:
    """scope-before.md, scope-after.md and scope-change.md, computed from the two inventories."""
    before_result, after_result = compute_scope(before), compute_scope(after)
    return {
        "scope-before.md": render_scope_report(before, before_result),
        "scope-after.md": render_scope_report(after, after_result),
        "scope-change.md": "# What changed in scope\n\n" + compare_scope(before_result, after_result),
    }


def render_routes(results: list[tuple[str, str, int]]) -> str:
    """`POST /pay -> 404`, one line per probe, for routes that must not exist."""
    return "routes that accepted card details in the naive checkout, probed on the merchant:\n" + "".join(
        f"{method} {path} -> {status}\n" for method, path, status in results
    )


def render_page_controls(
    url: str, status: int, headers: Mapping[str, str], scripts: list[str], provider: str, card_fields: list[str]
) -> str:
    """The payment page's security headers and the inventory of what it loads."""
    wanted = ("Content-Security-Policy", "X-Content-Type-Options", "Referrer-Policy", "Cache-Control")
    lines = [f"payment page controls: GET {url} -> {status}"]
    lines += [f"{name.lower()}: {headers.get(name, '(missing)')}" for name in wanted]
    lines.append("")
    lines.append("script inventory (the scripts and frames the page loads):")
    for src in scripts:
        owner = "the provider's" if src.startswith(provider) else "ours"
        lines.append(f"  script  {src}  ({owner})")
    lines.append(f"  frame   {provider}/frame  (created by the provider's script, served by the provider)")
    lines.append(f"card input fields on the merchant's page: {', '.join(card_fields) or 'none'}")
    return "\n".join(lines) + "\n"


def render_token_storage(
    columns: list[tuple[str, str]], rows: list[tuple[object, ...]], digit_columns: list[str]
) -> str:
    """The order table's shape, sample rows, and the result of looking for card-number columns."""
    lines = ["order table columns:"]
    lines += [f"  {name} {kind}" for name, kind in columns]
    lines.append("sample rows (id, payment intent, status, customer, payment method):")
    lines += [f"  {row}" for row in rows]
    lines.append(f"card number columns: {', '.join(digit_columns) or 'none'}")
    return "\n".join(lines) + "\n"


def render_index(
    requirements: list[Requirement], manifest: Mapping[str, ManifestEntry], gaps: list[Gap], when: datetime
) -> str:
    """INDEX.md: one line per file with the requirement it supports, what it proves and when it was made."""
    lines = [
        "# Evidence pack index",
        "",
        f"Pack date: {when.strftime('%Y-%m-%dT%H:%M:%SZ')}. Every file was produced by `make run` (`pci-scope demo`); "
        "`manifest.json` records its hash, so a hand edit fails `make verify`.",
        "",
        "| File | Requirement | Proves | Date |",
        "| --- | --- | --- | --- |",
    ]
    for requirement in requirements:
        for spec in requirement.evidence:
            entry = manifest.get(spec.file)
            date_text = entry.produced_at.strftime("%Y-%m-%d") if entry else "not produced"
            lines.append(f"| {spec.file} | {requirement.id} | {spec.proves} | {date_text} |")
    lines += ["", "## Tracked gaps", ""]
    lines += [f"- {gap.requirement}: {gap.reason} Ticket {gap.ticket}, due {gap.due}." for gap in gaps] or ["None."]
    lines += [
        "",
        "## What the merchant still does",
        "",
        "See `responsibilities.md`: the payment page and its pipeline, the content security policy, "
        "no logging of bodies, the provider's attestation, the questionnaire for the merchant level.",
        "",
    ]
    return "\n".join(lines)
