"""A problem a check found, with a code so a test and a reader can point at the rule."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    """One rule violation: the rule's code, what it is about, and what is wrong."""

    code: str
    subject: str
    message: str


def error(code: str, subject: str, message: str) -> Finding:
    """Build a finding."""
    return Finding(code, subject, message)
