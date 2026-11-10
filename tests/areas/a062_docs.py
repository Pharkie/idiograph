from __future__ import annotations

import re

from . import support
from .support import check


def test_docs():
    print("\n62. The README under 1,000 words, and every relative link in it and the two docs resolving (138)")
    readme = support.source("README.md").read_text(encoding="utf-8")
    manual_path, internals_path = support.source("docs/manual.md"), support.source("docs/internals.md")

    # ── A. the README: short, in order, for someone who has never seen the app
    words = len(readme.split())
    check("138: the README is under 1,000 words", words < 1000, f"{words} words")

    # ── B. the two docs, their headings and their links
    broken = []
    for name, path in (("README.md", support.source("README.md")), ("docs/manual.md", manual_path), ("docs/internals.md", internals_path)):
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        for target in re.findall(r"\]\(([^)\s]+)\)", text):
            if re.match(r"[a-z]+:", target):
                continue
            if not (path.parent / target.split("#", 1)[0]).exists():
                broken.append(f"{name} -> {target}")
    check("138: every relative link in the three files resolves", not broken, ", ".join(broken) or "all resolve")
