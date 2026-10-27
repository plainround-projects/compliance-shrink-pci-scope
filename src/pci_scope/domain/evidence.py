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

SUPPORT_FILES = frozenset({"INDEX.md", "manifest.json"})


@dataclass(frozen=True)
class EvidenceSpec:
    """One file that supports a requirement, and the kind of check its content gets."""

    file: str
    kind: str
    proves: str


@dataclass(frozen=True)
class Requirement:
    """A thing the redesign must show, with the evidence for it."""

    id: str
    text: str
    evidence: tuple[EvidenceSpec, ...]


@dataclass(frozen=True)
class Gap:
    """A requirement with no evidence yet, tracked on purpose."""

    requirement: str
    reason: str
    ticket: str
    due: date | None


@dataclass(frozen=True)
class ManifestEntry:
    """What the collector recorded about a file it wrote."""

    file: str
    requirement: str
    produced_at: datetime
    sha256: str


def digest(text: str) -> str:
    """SHA-256 of a file's text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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


def _scope(text: str) -> list[str]:
    problems = []
    if "```mermaid" not in text:
        problems.append("no diagram")
    if not re.search(r"\*\*\d+ systems and \d+ teams in scope\*\*", text):
        problems.append("no count of systems and teams")
    return problems


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


def _scan_before(text: str) -> list[str]:
    problems = []
    if "FOUND" not in text or "exit=1" not in text:
        problems.append(
            "the naive checkout must show the card number in its log (FOUND, exit=1): that is the problem being solved"
        )
    return problems


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


def _har_summary(text: str, merchant: str) -> list[str]:
    problems = [
        f"a request to your server lists card fields: {line}"
        for line in text.splitlines()
        if "-> your server" in line and "card fields" in line
    ]
    if "-> the provider" not in text or "-> your server" not in text:
        problems.append("the summary must show requests to both the merchant and the provider")
    return problems


def _routes(text: str) -> list[str]:
    return [
        f"expected '{line}' in the route check" for line in ("POST /pay -> 404", "GET /pay -> 404") if line not in text
    ]


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


def _tokens(text: str) -> list[str]:
    problems = []
    if "pm_" not in text and "pi_" not in text:
        problems.append("no token in the sample rows")
    if "card number columns: none" not in text:
        problems.append("the check for card-number columns is missing")
    return problems


def _responsibilities(text: str) -> list[str]:
    return [f"no '{label}' section" for label in ("## Now the provider's", "## Still ours") if label not in text]


def _attestation(text: str, tracked_gap: bool) -> list[str]:
    if "NOT OBTAINED" in text and not tracked_gap:
        return ["the provider's attestation has not been obtained and no gap is tracked"]
    return []
