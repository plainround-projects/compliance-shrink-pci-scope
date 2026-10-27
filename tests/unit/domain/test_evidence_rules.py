import json
from datetime import UTC, date, datetime

import pytest

from pci_scope.domain.evidence import EvidenceSpec, Gap, ManifestEntry, Requirement, digest, verify_pack

MERCHANT, PROVIDER = "http://m:5000", "http://p:5001"
NOW = datetime(2026, 10, 27, tzinfo=UTC)


def har(merchant_body="", provider_body="card%5Bnumber%5D=[redacted]", merchant_url=f"{MERCHANT}/"):
    entries = [
        {
            "request": {"method": "GET", "url": merchant_url, "postData": {"text": merchant_body}},
            "response": {"status": 200},
        },
        {
            "request": {"method": "POST", "url": f"{PROVIDER}/v1/payment_methods", "postData": {"text": provider_body}},
            "response": {"status": 200},
        },
    ]
    return json.dumps({"log": {"entries": entries}})


HAR_OK = har()
GOOD = {
    "scope": "```mermaid\nx\n```\n**9 systems and 3 teams in scope**",
    "scope_change": (
        "Before: 9 systems and 3 teams in scope.\nAfter: 3 systems and 2 teams in scope.\n"
        "Left scope: a.\nStill in scope: b."
    ),
    "scan_before": "x FOUND card number\nscanned 1 artifact(s): 1 findings\nexit=1",
    "scan_after": "scanned 3 artifact(s): 0 findings\nexit=0\n",
    "har": HAR_OK,
    "har_summary": (
        "GET http://m:5000/ body: (empty)  -> your server\n"
        "POST http://p:5001/x card fields: card[number]  -> the provider"
    ),
    "routes": "POST /pay -> 404\nGET /pay -> 404",
    "headers": "content-security-policy: script-src http://p:5001\nscript inventory (x):",
    "tokens": "  (1, 'pi_x', 'pm_y')\ncard number columns: none",
    "responsibilities": "## Now the provider's\n## Still ours",
    "attestation": "NOT OBTAINED",
}


def pack(overrides=None, gaps=None):
    files = {**GOOD, **(overrides or {})}
    requirements = [Requirement(f"R-{kind}", kind, (EvidenceSpec(f"{kind}.txt", kind, "proves"),)) for kind in files]
    texts = {f"{kind}.txt": text for kind, text in files.items()}
    manifest = {name: ManifestEntry(name, f"R-{name[:-4]}", NOW, digest(text)) for name, text in texts.items()}
    return (
        requirements,
        manifest,
        texts,
        gaps if gaps is not None else [Gap("R-attestation", "no real provider", "PCI-1", date(2026, 12, 1))],
    )


def codes(overrides=None, gaps=None, drop=None, manifest_edit=None):
    requirements, manifest, texts, gap_list = pack(overrides, gaps)
    if drop:
        del texts[drop]
    if manifest_edit:
        manifest_edit(manifest)
    return sorted({f.code for f in verify_pack(requirements, manifest, texts, gap_list, MERCHANT, PROVIDER)})


def test_a_complete_pack_passes():
    requirements, manifest, texts, gaps = pack()
    assert verify_pack(requirements, manifest, texts, gaps, MERCHANT, PROVIDER) == []


def test_a_requirement_with_no_evidence_needs_a_tracked_gap():
    requirements, manifest, texts, gaps = pack()
    requirements.append(Requirement("P9", "x", ()))
    assert [f.code for f in verify_pack(requirements, manifest, texts, gaps, MERCHANT, PROVIDER)] == ["EVP001"]
    gaps.append(Gap("P9", "later", "PCI-2", date(2026, 12, 1)))
    assert verify_pack(requirements, manifest, texts, gaps, MERCHANT, PROVIDER) == []


def test_missing_empty_unclaimed_and_edited_files_are_reported():
    assert codes(drop="routes.txt") == ["EVP002"]
    assert codes({"routes": "  \n"}) == ["EVP002"]
    requirements, manifest, texts, gaps = pack()
    texts["stray.txt"] = "x"
    assert {f.code for f in verify_pack(requirements, manifest, texts, gaps, MERCHANT, PROVIDER)} == {"EVP004"}
    requirements, manifest, texts, gaps = pack()
    texts["routes.txt"] += "edited"
    assert {f.code for f in verify_pack(requirements, manifest, texts, gaps, MERCHANT, PROVIDER)} == {"EVP003"}
    assert codes(manifest_edit=lambda m: m.pop("routes.txt")) == ["EVP003"]


def test_gaps_must_be_complete_and_real():
    assert "EVP008" in codes(gaps=[Gap("R-attestation", "", "PCI-1", date(2026, 12, 1))])
    assert "EVP008" in codes(
        gaps=[Gap("R-attestation", "x", "PCI-1", None), Gap("P99", "x", "PCI-3", date(2026, 12, 1))]
    )


@pytest.mark.parametrize(
    ("kind", "bad"),
    [
        ("scope", "no diagram, no count"),
        (
            "scope_change",
            "Before: 9 systems and 3 teams in scope.\nAfter: 9 systems and 3 teams in scope.\n"
            "Left scope: x\nStill in scope: y",
        ),
        ("scope_change", "nothing"),
        ("scan_before", "scanned 1 artifact(s): 0 findings\nexit=0"),
        ("scan_after", "x FOUND card number\nscanned 3 artifact(s): 1 findings\nexit=1"),
        ("scan_after", "scanned 1 artifact(s): 0 findings\nexit=0"),
        ("har", "not json"),
        (
            "har",
            HAR_OK.replace("[redacted]", "[redacted]").replace(
                '"url": "http://m:5000/", "postData": {"text": ""}',
                '"url": "http://m:5000/", "postData": {"text": "card_number=4242424242424242"}',
            ),
        ),
        ("har", HAR_OK.replace("card%5Bnumber%5D", "amount")),
        ("har", HAR_OK.replace("http://m:5000/", "http://other/")),
        ("har_summary", "GET x  card fields: card[number]  -> your server\nPOST y  -> the provider"),
        ("har_summary", "only your server -> your server"),
        ("routes", "POST /pay -> 200\nGET /pay -> 404"),
        ("headers", "script inventory"),
        ("headers", "content-security-policy: default-src 'self'\nscript inventory"),
        ("headers", "content-security-policy: script-src http://p:5001"),
        ("tokens", "card number columns: none"),
        ("tokens", "pm_x"),
        ("responsibilities", "## Now the provider's"),
    ],
)
def test_each_artifact_is_checked_for_what_it_must_say(kind, bad):
    assert "EVP007" in codes({kind: bad})


def test_an_attestation_that_is_not_obtained_needs_its_gap():
    assert codes(gaps=[]) == ["EVP007"]
    assert codes({"attestation": "Attestation of compliance: on file, dated 2026-01-01"}, gaps=[]) == []
