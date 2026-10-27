"""Card data: how to recognize a card number or a card field in text, and the published test cards."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import unquote_plus

# Digits in groups, optionally separated by single spaces or dashes: 13 to 19 digits in all.
_CANDIDATE = re.compile(r"(?<![\d-])(?:\d[ -]?){12,18}\d(?![\d-])")
_CARD_FIELD = re.compile(
    r"""(?i)\b(cvv|cvc|cvv2|card[_\[\]-]*number|card_number|cardnumber|pan)\b["']?\s*[:=]\s*["']?[^\s&,"'}]+"""
)
_FIELD_NAME_ONLY = re.compile(r"(?i)card\[(number|cvc|exp_month|exp_year)\]")

TEST_CARD = "4242424242424242"
DECLINED_TEST_CARD = "4000000000000002"
TEST_CARDS = frozenset({TEST_CARD, DECLINED_TEST_CARD})


def luhn_valid(digits: str) -> bool:
    """The Luhn check every card number passes."""
    if not digits.isdigit():
        return False
    total = 0
    for position, char in enumerate(reversed(digits)):
        value = int(char)
        if position % 2 == 1:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def mask(digits: str) -> str:
    """The first six and last four digits, the rest as stars: enough to tell the card in a report, never the number."""
    return f"{digits[:6]}{'*' * (len(digits) - 10)}{digits[-4:]}"


@dataclass(frozen=True)
class CardFinding:
    """Card data found in a place where it must not be."""

    source: str
    line: int
    kind: str
    evidence: str


def scan_text(source: str, text: str) -> list[CardFinding]:
    """Card numbers (13 to 19 digits that pass the Luhn check, spaces or dashes allowed) and card fields with a value.

    The evidence is masked, so the report of a scan never becomes a new copy of the number.
    """
    found: list[CardFinding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in _CANDIDATE.finditer(line):
            digits = re.sub(r"[ -]", "", match.group(0))
            if 13 <= len(digits) <= 19 and luhn_valid(digits):
                found.append(CardFinding(source, line_number, "card number", mask(digits)))
        for field in _CARD_FIELD.finditer(unquote_plus(line)):
            found.append(CardFinding(source, line_number, "card field", field.group(1).lower()))
    return found


def card_field_names(text: str) -> list[str]:
    """The names of card input fields present in a body or a page (`card[number]`, `cvc`, `card_number`, ...)."""
    decoded = unquote_plus(text)
    names = {match.group(0).lower() for match in _FIELD_NAME_ONLY.finditer(decoded)}
    names |= {
        name.lower()
        for name in re.findall(r"""(?i)name=["'](card_number|cardnumber|cvv|cvc|card-number)["']""", decoded)
    }
    return sorted(names)
