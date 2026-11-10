"""Sift's words for a person, from the text layer's catalogue (siftlang, 1 November 2026): `t` is the family's
`i18n.t` with Sift's own folder always among the folders it reads, `apps/sift/static/i18n/`, whichever app the run
serves, so a command, a check or another app's run that calls a Sift module reads Sift's sentences, never their
keys. The run's language and method are the family's, as for every other message (see docs/internals.md, The text
layer)."""
from __future__ import annotations

from pathlib import Path

import i18n

SIFT = Path(__file__).resolve().parent


def roots() -> list:
    """The folders the run's catalogue is read from, Sift's own first where the run left it out."""
    held = list(i18n.ROOTS())
    return held if any(Path(r).resolve() == SIFT for r in held) else [SIFT, *held]


def t(key: str, vals: dict | None = None, **slots) -> str:
    """A Sift message in the run's language, its slots filled, as `i18n.t` gives one."""
    return i18n.t(key, vals, roots=roots(), **slots)
