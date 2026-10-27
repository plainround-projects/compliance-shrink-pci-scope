import json

import pytest

from pci_scope.domain.card import TEST_CARD, card_field_names, luhn_valid, mask, scan_text
from pci_scope.domain.har import Exchange, merchant_exposure, origin, parse_har, reaches_provider, summarize, to_har
from pci_scope.domain.payment import is_token
from pci_scope.domain.scope import (
    CONTROL,
    DATA,
    Edge,
    Inventory,
    System,
    compare_scope,
    compute_scope,
    render_mermaid,
    render_scope_report,
)
from pci_scope.domain.webhook import sign, verify
from pci_scope.infrastructure.catalog import load_inventory
from tests.conftest import REPOSITORY_ROOT, SECRET


@pytest.mark.parametrize("number", [TEST_CARD, "4000000000000002", "378282246310005", "5555555555554444"])
def test_published_test_numbers_pass_the_luhn_check(number):
    assert luhn_valid(number)


@pytest.mark.parametrize("number", ["4242424242424241", "1234567890123456", "abcd", ""])
def test_other_numbers_do_not(number):
    assert not luhn_valid(number)


def test_a_mask_keeps_six_and_four_digits_only():
    assert mask(TEST_CARD) == "424242******4242"


@pytest.mark.parametrize(
    "line",
    [
        "payment request: 4242424242424242",
        "card 4242 4242 4242 4242 ok",
        "card 4242-4242-4242-4242 ok",
        "{'card_number': '4242424242424242', 'expiry': '12/30', 'cvv': '123'}",
        "card%5Bnumber%5D=4242424242424242",
    ],
)
def test_a_card_number_in_any_common_form_is_found_and_only_its_mask_is_reported(line):
    findings = scan_text("log", line)
    assert any(f.kind == "card number" and f.evidence == "424242******4242" for f in findings)
    assert "4242424242424242" not in repr(findings)


@pytest.mark.parametrize(
    "line",
    [
        "created payment pi_3f9a1c0e7d2b4a5c6e8f0a1b amount=1900 eur",
        "order 1730000000000 shipped",
        "2026-10-27T00:40:19Z user=ada id=1",
        "phone 0044 7700 900123",
        "amount=4242",
    ],
)
def test_ordinary_log_lines_are_not_flagged(line):
    assert scan_text("log", line) == []


def test_card_fields_with_a_value_are_found_by_name_only():
    findings = scan_text("log", "form: cvv=123 and CVC: 456 and card_number=nothing")
    assert sorted(f.evidence for f in findings) == ["card_number", "cvc", "cvv"]
    assert all(f.kind == "card field" for f in findings)


def test_findings_say_the_line():
    assert scan_text("a.log", "ok\nnext\ncvv=1")[0].line == 3


def test_field_names_are_read_from_forms_pages_and_encoded_bodies():
    assert card_field_names('<input name="card_number"> <input name="cvv">') == ["card_number", "cvv"]
    assert card_field_names("card%5Bnumber%5D=x&card%5Bcvc%5D=y") == ["card[cvc]", "card[number]"]
    assert card_field_names("amount=1900&currency=eur") == []


def test_tokens_are_recognized_and_numbers_are_not():
    assert is_token("pi_" + "a" * 24)
    assert is_token("pm_" + "0" * 24)
    assert not is_token(TEST_CARD)
    assert not is_token("pm_short")
    assert not is_token("pm_" + "a" * 24 + "; DROP TABLE")


BEFORE = load_inventory(REPOSITORY_ROOT / "scope" / "before.toml")
AFTER = load_inventory(REPOSITORY_ROOT / "scope" / "after.toml")


def test_the_naive_checkout_puts_nine_systems_and_three_teams_in_scope():
    result = compute_scope(BEFORE)
    assert len(result.systems) == 9
    assert result.teams == ("developers", "operations", "support")
    assert "browser" not in result.ids


def test_every_system_the_card_touches_or_that_can_change_one_is_in_scope_with_a_reason():
    reasons = {system.id: why for system, why in compute_scope(BEFORE).systems}
    assert reasons["web"] == ("card data reaches it",)
    assert reasons["search"] == ("card data reaches it from Log shipping",)
    assert reasons["laptops"] == ("card data reaches it from Log search tool",)
    assert reasons["ci"] == ("can change Web server (naive.py)",)
    assert reasons["admin"] == ("can change Web server (naive.py)",)


def test_after_the_redesign_only_the_page_its_pipeline_and_its_admins_remain():
    result = compute_scope(AFTER)
    assert result.ids == {"web", "ci", "admin"}
    assert result.teams == ("developers", "operations")


def test_the_comparison_names_what_left_and_what_stays():
    text = compare_scope(compute_scope(BEFORE), compute_scope(AFTER))
    assert "Before: 9 systems and 3 teams in scope." in text
    assert "After: 3 systems and 2 teams in scope." in text
    left = "Request log, Log shipping, Log search tool, Order database, Backups, Developer laptops that read logs"
    assert f"Left scope: {left}." in text
    assert "Web server (serves the checkout page) (serves the page that loads the provider's script)" in text


def test_the_reports_and_the_diagram_render():
    report = render_scope_report(AFTER, compute_scope(AFTER))
    assert "**3 systems and 2 teams in scope**" in report
    assert "```mermaid" in report
    assert "Out of scope: Request log" in report
    diagram = render_mermaid(AFTER, compute_scope(AFTER))
    assert 'subgraph cde["In scope"]' in diagram
    assert "browser -->|card data| provider" in diagram
    assert "ci -.->|can change| web" in diagram
    assert "(provider)" in diagram


def test_cycles_terminate_and_an_empty_scope_renders():
    a, b = System("a", "A", "t", touches_card=True), System("b", "B", "t")
    loop = Inventory("loop", (a, b), (Edge("a", "b", DATA), Edge("b", "a", DATA), Edge("b", "a", CONTROL)))
    assert compute_scope(loop).ids == {"a", "b"}
    nothing = Inventory("none", (System("x", "X", "t"),), ())
    assert compute_scope(nothing).systems == ()
    assert "nothing" in render_mermaid(nothing, compute_scope(nothing))


def test_a_signature_made_with_the_secret_verifies_within_five_minutes():
    body = b'{"type":"payment_intent.succeeded"}'
    header = sign(SECRET, body, 1_000)
    assert header.startswith("t=1000,v1=")
    assert verify(SECRET, body, header, now=1_000 + 299)
    assert verify(SECRET, body, header, now=1_000 - 299)


@pytest.mark.parametrize(
    ("body", "header", "now"),
    [
        (b"{}", None, 1_000),
        (b"{}", "", 1_000),
        (b"{}", "garbage", 1_000),
        (b"{}", "t=abc,v1=00", 1_000),
        (b"{}", "t=1000", 1_000),
        (b"{ }", sign(SECRET, b"{}", 1_000), 1_000),
        (b"{}", sign(SECRET, b"{}", 1_000), 1_000 + 301),
        (b"{}", sign("another-secret-value-0123456789abcdef", b"{}", 1_000), 1_000),
    ],
)
def test_a_missing_forged_tampered_or_old_signature_is_refused(body, header, now):
    assert not verify(SECRET, body, header, now)


MERCHANT, PROVIDER = "http://127.0.0.1:5000", "http://127.0.0.1:5001"


def exchanges(card_to_merchant=False):
    return [
        Exchange("GET", f"{MERCHANT}/", 200, ""),
        Exchange("POST", f"{MERCHANT}/create-payment", 200, "card_number=4242424242424242" if card_to_merchant else ""),
        Exchange("POST", f"{PROVIDER}/v1/payment_methods", 200, f"card%5Bnumber%5D={TEST_CARD}&card%5Bcvc%5D=123"),
        Exchange("POST", f"{PROVIDER}/v1/payment_intents/pi_x/confirm", 200, "payment_method=pm_x"),
    ]


def test_origins_are_scheme_host_and_port():
    assert origin("http://127.0.0.1:5000/done?x=1") == MERCHANT


def test_the_har_keeps_field_names_sent_to_the_provider_and_drops_their_values():
    har = to_har(exchanges(), frozenset({PROVIDER}))
    assert TEST_CARD not in har
    assert "card%5Bnumber%5D=[redacted]" in har
    assert json.loads(har)["log"]["version"] == "1.2"
    parsed = parse_har(har)
    assert [item.status for item in parsed] == [200, 200, 200, 200]
    assert reaches_provider(parsed, PROVIDER)


def test_a_capture_where_the_card_stays_with_the_provider_has_no_exposure():
    assert merchant_exposure(exchanges(), MERCHANT) == []


def test_a_card_sent_to_the_merchant_is_reported():
    assert merchant_exposure(exchanges(card_to_merchant=True), MERCHANT) == [
        f"POST {MERCHANT}/create-payment carries card data"
    ]
    leaked_url = [Exchange("GET", f"{MERCHANT}/done?card={TEST_CARD}", 200, "")]
    assert len(merchant_exposure(leaked_url, MERCHANT)) == 1


def test_a_capture_with_no_card_at_the_provider_does_not_show_the_payment():
    assert not reaches_provider(exchanges()[:2], PROVIDER)


def test_the_summary_says_where_each_request_went():
    lines = summarize(exchanges(), MERCHANT, PROVIDER).splitlines()
    assert lines[0].endswith("body: (empty)  -> your server")
    assert "card fields: card[cvc], card[number]  -> the provider" in lines[2]
    assert lines[3].endswith("body: no card fields  -> the provider")
    assert (
        summarize([Exchange("GET", "http://other.example/", 200, "")], MERCHANT, PROVIDER)
        .strip()
        .endswith("-> elsewhere")
    )
