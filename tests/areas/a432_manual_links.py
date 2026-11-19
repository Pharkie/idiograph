"""Area 432: the app's links into the manual land on a heading the manual has (guidelinks, 19 November 2026, Adam's yes
of 18 November).

Each Guidance tab names at its foot the manual's terms it uses, each a link to /manual#<anchor> (distil.js's
GUIDE_TERMS and GUIDE_SCREENS), and a message with a way back carries "What this means", a link to its entry under
When something goes wrong (the page's own markup, and meansLink in the scripts). A later edit of the manual that renames
a heading would leave such a link dead, so this reads every anchor the page links, from the scripts and the markup, and
checks the app's own rendering of docs/manual.md has a heading with that id; that every screen's terms are terms
the page knows and every term has its words in the catalogue; that each screen of the Guidance tabs has terms; and that
the refusal the GETs' complete message carries is one of the family's codes."""
from __future__ import annotations

import json
import re

from . import support
from .support import check


def test_manual_links():
    print("\n432. Every link the app makes into the manual lands on one of its headings (guidelinks)")
    import server as server_mod

    text = support.source("docs/manual.md").read_text(encoding="utf-8")
    blocks, _contents = server_mod.manual_blocks(text)
    ids = set(re.findall(r'id="([^"]+)"', "".join(str(b) for b in blocks)))
    check("432: the app's rendering of the manual gives its headings ids", len(ids) > 40, str(len(ids)))

    static = support.source("apps/idiograph/static")
    distil = (static / "distil.js").read_text(encoding="utf-8")
    terms_block = re.search(r"const GUIDE_TERMS = \{(.*?)\n\};", distil, re.S).group(1)
    terms = dict(re.findall(r"'([a-z0-9-]+)': \(\) => t\('([a-z_.]+)'\)", terms_block))
    screens_block = re.search(r"const GUIDE_SCREENS = \{(.*?)\n\};", distil, re.S).group(1)
    screens = {name: re.findall(r"'([a-z0-9-]+)'", row)
               for name, row in re.findall(r"^\s+(\w+): \[(.*)\],$", screens_block, re.M)}
    check("432: the page reads its terms and its screens' lists", len(terms) >= 15 and len(screens) >= 9,
          f"{len(terms)} {len(screens)}")
    check("432: each Guidance screen names terms, each a term the page knows",
          all(v and set(v) <= set(terms) for v in screens.values()), str(screens))
    check("432: every term is a heading of the manual", set(terms) <= ids, str(sorted(set(terms) - ids)))
    catalogue = json.loads((static / "i18n/en/distil.json").read_text(encoding="utf-8"))
    check("432: every term has its words and the line its lead in the catalogue",
          all(k in catalogue for k in terms.values()) and "distil.manual.lead" in catalogue,
          str([k for k in terms.values() if k not in catalogue]))
    for screen in ("pets", "gets", "lpets", "lgets", "trajectories", "ta_themes", "codes", "statements_ipa",
                   "statements_ta"):
        check(f"432: {screen} has a Guidance foot", screen in screens)

    # every other anchor the page and its scripts link: "What this means" and any /manual# link
    anchors = set()
    for name in ("idiograph.html", "distil.js", "themes.js", "codes.js", "trajectories.js", "team.js", "team_board.js"):
        body = (static / name).read_text(encoding="utf-8")
        anchors |= set(re.findall(r"/manual#([a-z0-9-]+)", body))
        anchors |= set(re.findall(r"meansLink\('([a-z0-9-]+)'\)", body))
        anchors |= set(re.findall(r"vmeans = [^?]*\? '([a-z0-9-]+)'", body))
    check("432: the page links entries of When something goes wrong", len(anchors) >= 4, str(sorted(anchors)))
    check("432: every anchor the page links is a heading of the manual", anchors <= ids, str(sorted(anchors - ids)))
