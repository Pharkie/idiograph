#!/usr/bin/env python3
"""Live flags on a draft statement, taken from the checks in `ipa_annotation_audit.py`.

These are soft. Nothing here blocks a commit, nothing is scored, and a statement that trips a flag
is often the right statement. They exist so a habit shows itself while the statement is still on
screen rather than in an audit run days later. Each check can be switched off in settings.
"""
from __future__ import annotations

import re

WORD = re.compile(r"[A-Za-z0-9']+")
QUOTE = re.compile(r"['‘’\"“”]")
TELL = re.compile(r"\b(reads?|casts?|recasts?)\s+.{0,40}?\sas\b", re.I)
ARROW = re.compile(r"[→⇒➔➡]|\s>\s|->")
FIRST = re.compile(r"\s*([A-Za-z']+)")
NOUN_LED = {"she", "her", "the", "it", "his", "they", "a", "an", "he"}

# Corpus norms, from the census of 1,560 statements: median 10 words, 78% in the 7 to 15 band.
# No minimum (Adam, 21 September 2026): a fifth of his own statements run to six words or fewer.
# HIGH is the default, and a project sets its own (Adam, 20 October 2026: `statement_words` in its file).
HIGH = 15

CHECKS = ("length", "lead", "quote", "semicolon", "emdash", "arrow", "readsas")

LABELS = {
    "length": "word count past 15",
    "lead": "opens with The, She, Her, A or An",
    "quote": "carries a quoted fragment",
    "semicolon": "carries a semicolon",
    "emdash": "carries an em dash",
    "arrow": "carries an arrow",
    "readsas": "the reads-as construction",
}


def words(text: str) -> int:
    return len(WORD.findall(text))


def first_word(text: str) -> str:
    m = FIRST.match(text)
    return m.group(1).lower() if m else ""


def check_statement(text: str, enabled=CHECKS, high: int = HIGH) -> list[dict]:
    """Flags for one statement. Each is {check, note}. `high` is the length past which the length nudge
    speaks, the project's own, 15 by default."""
    flags: list[dict] = []
    stripped = text.strip()
    if not stripped:
        return flags
    n = words(stripped)

    def add(check, note):
        if check in enabled:
            flags.append({"check": check, "note": note})

    if n > high:
        add("length", f"over {high} words. Tighten it, or split out a second idea.")
    if first_word(stripped) in NOUN_LED:
        add("lead", "opens with The, She, Her or A. The corpus drops the subject.")
    if QUOTE.search(stripped):
        add("quote", "a quoted fragment. One statement in seven, and a single crux word.")
    if ";" in stripped:
        add("semicolon", "a semicolon. Use a comma or a full stop.")
    if "\u2014" in stripped:          # the em dash, kept as an escape so it stays out of the source
        add("emdash", "an em dash. Use a comma or restructure.")
    if ARROW.search(stripped):
        add("arrow", "an arrow. Use to, vs, = or a comma.")
    if TELL.search(stripped):
        add("readsas", "the reads-as construction. Say it with a plain verb.")
    return flags


def check_field(text: str, enabled=CHECKS, high: int = HIGH) -> list[dict]:
    """Flags for every statement in the entry field, one entry per line, the length nudge at `high`."""
    out = []
    for i, line in enumerate((text or "").splitlines()):
        if not line.strip():
            continue
        flags = check_statement(line, enabled, high)
        if flags:
            out.append({"line": i, "text": line.strip(), "flags": flags})
    return out
