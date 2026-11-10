"""Area 295: each app's own page loads what its screens are built from (tracestyle, 30 October 2026).

Trace's own app showed its screen unstyled from the cutover (the family codebase's sixth build, 23 October 2026)
until 30 October: its screen wears the frame it shares with Sift, the bars, the table and its filters, the record,
the PDF beside it, the pills and the foot, whose rules stood in sift.css, and since the cutover each app's page holds
its own parts alone, so Trace's page never loaded them. The frame is the family's since, `family/static/frame.css`,
which Sift's and Trace's parts of the page link before their own.

What is checked: on each app's page as the server serves it to that app, every stylesheet and script it links is a
file that app's run serves; every class that app's own markup and scripts put on an element, and the family's table's
where its scripts draw through it, that any stylesheet in the codebase styles, is styled by a stylesheet its page links,
and that this would have seen the fault. Until 2 November (testspeed) a headless browser also read each part of Sift's and
Trace's screens styled beyond the family's tokens.css and style.css: a check of styles, which review shots hold, and the
links and classes above hold the fault it was written for."""
from __future__ import annotations

import re

from . import support
from .support import check

# A class an app's markup carries that another app's stylesheet styles, each for its reason
ELSEWHERE = {
    # Idiograph's own rule for its bars' lockup button (distil.css): Sift's and Trace's bars carry the class too and
    # take the family's .bar-brand from style.css, as the bars of option C were shot and approved (26 October 2026)
    "rail-home": "distil.css",
    # Mermaid's word inside Sift's PRISMA flow, which sift.css styles there alone, Idiograph's .label being its own
    "label": "sift.css",
}


def _blanked(text: str, pattern: str) -> str:
    return re.sub(pattern, lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)


def styled(css: str) -> set:
    """Every class a stylesheet's selectors name."""
    css = _blanked(css, r"/\*.*?\*/")
    css = _blanked(_blanked(css, r"\{[^{}]*\}"), r"\{[^{}]*\}")
    return set(re.findall(r"\.(-?[A-Za-z_][\w-]*)", css))


def classes_of(text: str, script: bool) -> set:
    """The classes a file of the page puts on its elements: its class attributes, in markup or in a script's
    templates, what a ${...} fills set aside, and the names a script adds, toggles or sets as they are written."""
    text = _blanked(text, r"<!--.*?-->")
    if script:
        text = re.sub(r"(?m)^\s*//.*$", "", _blanked(text, r"/\*.*?\*/"))
    out = set()
    for m in re.finditer(r'class=\\?"([^"]*)"', text):
        out |= set(re.sub(r"\$\{[^}]*\}", " ", m.group(1)).replace("\\", " ").split())
    for m in re.finditer(r"classList\.(?:add|toggle|remove)\(([^)]*)\)", text):
        out |= set(re.findall(r"'([\w-]+)'", m.group(1)))
    for m in re.finditer(r"className\s*=\s*([^;\n]*)", text):
        for s in re.findall(r"'([^']*)'", m.group(1)):
            out |= set(s.split())
    return {c for c in out if re.fullmatch(r"-?[A-Za-z_][\w-]*", c)}


def links(page: str) -> tuple[list, list]:
    """The stylesheets and the scripts a page links, by their names."""
    return (re.findall(r'<link rel="stylesheet" href="/([^"]+)"', page), re.findall(r'<script src="/([^"]+)"', page))


def test_frame_styles(scratch):
    print("\n295. Each app's own page loads what its screens are built from: its stylesheets and scripts served by its "
          "own run, every class its markup carries styled by what it links, Sift's and Trace's by the frame they "
          "share, the family's frame.css")
    import app_identity
    import server

    page = support.text("family/static/page.html")
    served = {app: server.own_page(server.assembled(page, app), app) for app in app_identity.APPS}

    # ── A. what each page links, its app's run serves
    unserved = {app: [n for n in sum(links(served[app]), []) if server.static_file(n, app) is None] for app in served}
    check("295: every stylesheet and script each app's page links is a file that app's own run serves, as its bundle "
          "carries it", not any(unserved.values()), str(unserved))
    sheets = {app: links(served[app])[0] for app in served}
    check("295: Sift's and Trace's pages link the family's frame.css before their own stylesheet, and Idiograph's, "
          "which draws no such screen, does not",
          sheets["sift"].index("frame.css") < sheets["sift"].index("sift.css")
          and sheets["trace"].index("frame.css") < sheets["trace"].index("trace.css")
          and "frame.css" not in sheets["idiograph"], str(sheets))

    # ── B. every class an app's markup carries, styled somewhere, is styled by what its page links
    root = support.TOOL
    every: dict = {}
    for css in sorted((root / "family/static").glob("*.css")) + sorted((root / "apps").glob("*/static/*.css")):
        for c in styled(css.read_text(encoding="utf-8")):
            every.setdefault(c, set()).add(css.name)
    table = support.text("family/static/table.js")

    def unstyled(app: str, left_out: str = "") -> dict:
        """The classes `app`'s own markup and scripts carry, and the family's table's where its scripts draw through
        it, that a stylesheet styles and none its page links does, `left_out` taken from what it links"""
        have = set()
        for name in sheets[app]:
            if name != left_out:
                have |= styled(server.static_file(name, app).read_text(encoding="utf-8"))
        own, scripts = set(), ""
        folder = root / "apps" / app / "static"
        for f in sorted(folder.glob("*.js")) + sorted(folder.glob("*.html")):
            text = f.read_text(encoding="utf-8")
            own |= classes_of(text, f.suffix == ".js")
            scripts += text if f.suffix == ".js" else ""
        if re.search(r"\btb[A-Z]\w*\(", scripts):
            own |= classes_of(table, True)
        return {c: sorted(every[c]) for c in own if c in every and c not in have and ELSEWHERE.get(c) not in every[c]}

    missing = {app: unstyled(app) for app in app_identity.APPS}
    check("295: every class each app's own markup and scripts put on an element, and the family's table's where it "
          "draws through it, that a stylesheet styles, is styled by a stylesheet its own page links",
          not any(missing.values()), str(missing)[:900])
    without = unstyled("trace", "frame.css")
    check("295: and that would have seen the fault: Trace's page without the frame leaves its table, filters, record "
          "and decisions unstyled, their rules in frame.css",
          all("frame.css" in without.get(c, []) for c in ("sf-tbl", "sf-facets", "sf-record", "sf-acts")), str(without)[:400])
