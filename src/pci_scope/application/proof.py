"""The proof that card data is not on the merchant's side: scan every place it could be, say what was scanned."""

from __future__ import annotations

from dataclasses import dataclass

from pci_scope.application.ports import ArtifactReader
from pci_scope.domain.card import CardFinding, scan_text


@dataclass(frozen=True)
class ScanOutcome:
    """The text of the proof, the findings behind it, and the exit code a shell would see."""

    text: str
    findings: tuple[CardFinding, ...]
    artifacts: int

    @property
    def exit_code(self) -> int:
        """1 when anything was found, 0 when the scan is clean."""
        return 1 if self.findings else 0


def run_scan(title: str, reader: ArtifactReader) -> ScanOutcome:
    """Scan each artifact for card numbers and card fields and write the report, with masked evidence only."""
    lines = [title]
    findings: list[CardFinding] = []
    count = 0
    for name, text in reader.artifacts():
        count += 1
        found = scan_text(name, text)
        findings.extend(found)
        if found:
            lines.extend(f"  {item.source}:{item.line} FOUND {item.kind} {item.evidence}" for item in found)
        else:
            lines.append(f"  {name} ... clean")
    lines.append(f"scanned {count} artifact(s): {len(findings)} findings")
    lines.append(f"exit={1 if findings else 0}")
    return ScanOutcome("\n".join(lines) + "\n", tuple(findings), count)
