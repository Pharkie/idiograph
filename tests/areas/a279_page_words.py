"""Area 279: Idiograph's page markup and its print views read their words from the catalogue (i18npage, the text
layer's second build, 28 October 2026). idiograph.html's words are {{page_idiograph.*}} markers, a run of words and
markup that is one sentence an _html message keeping the elements the scripts fill, and the table of PETs' and the
GETs' print views take theirs from page_print.json through i18n.t, counts by their plural forms and values by
named slots. What is checked is behaviour: the elements the scripts write into are still there once the page is
filled, the print views' counts and slots come out as the English always read, and an overlay's words reach a
print view drawn while it is the language."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from . import support
from .support import check


def test_page_words(scratch: Path):
    print("\n279. Idiograph's page markup and its print views read their words from the catalogue: the elements the "
          "scripts fill inside a moved sentence still there, the print views' plurals and slots, and an overlay "
          "reaching a print view (28 October 2026)")
    import i18n
    import themes_print as tp

    # ── the page: each sentence moved whole keeps the elements the scripts write into, by their ids
    # the page as served, the catalogue its scripts take inline left out
    page = re.sub(r"<script>var I18N = .*?</script>", "", support.page_text(), flags=re.S)
    ids = ["rail-who", "rail-speaker", "rail-unit", "rail-turn", "rail-turns", "rail-in-round", "rail-in-round-n",
           "rail-round-n", "round-bar", "round-fill", "rail-round", "rail-rounds", "note-hint", "set-min-n"]
    gone = [i for i in ids if len(re.findall(rf'\bid="{i}"', page)) != 1]
    check("279: the sentences moved whole keep each element the scripts fill, once, in the page as served",
          not gone and "{{" not in page and "page_idiograph." not in page, ", ".join(gone))
    check("279: the minimum's sentence keeps its number's element first and its words after, where distil.js writes "
          "the count's word into its last part",
          re.search(r'id="set-min-text"><b id="set-min-n">3</b> participants</span>', page) is not None)

    # ── the print views' counts and slots
    t = i18n.t
    check("279: the GETs print's counts pick their plural forms",
          t("page_print.gets.count", count=1, n=1, lang="en") == "1 of 1 participant"
          and t("page_print.gets.statements", n=1, lang="en") == "1 statement"
          and t("page_print.gets.statements", n=7, lang="en") == "7 statements"
          and t("page_print.gets.count", count=2, n=5, lang="en") == "2 of 5 participants")
    check("279: the page's title fills its slots",
          tp.title_of("P9 - Wren", "Board 3") == "P9 - Wren - Board 3 - PETs"
          and tp.title_of("P9 - Wren", "Board 3", sending=True) == "P9 - Wren")

    # ── an overlay's words reach a print view drawn while it is the language
    fx = scratch / "i18n-279"
    shutil.rmtree(fx, ignore_errors=True)
    (fx / "static" / "i18n" / "en-ZZ").mkdir(parents=True)
    (fx / "static" / "i18n" / "en-ZZ" / "page_print.json").write_text(json.dumps(
        {"page_print.tick.sending": "To send on", "page_print.pets.title": "{board} of {case}"}), encoding="utf-8")
    roots, language = i18n.ROOTS, i18n.LANGUAGE
    try:
        real = list(roots())
        i18n.ROOTS = lambda: [*real, fx]
        i18n.LANGUAGE = lambda: "en-ZZ"
        ticks = tp.include_ticks(False, False)
        title = tp.title_of("P9 - Wren", "Board 3")
    finally:
        i18n.ROOTS, i18n.LANGUAGE = roots, language
    check("279: a print view drawn in an overlay takes the overlay's words, its slots in the overlay's order, and "
          "English for the rest",
          "> To send on</label>" in ticks and "> Include not placed</label>" in ticks and title == "Board 3 of P9 - Wren",
          f"{title} {ticks[:200]}")
    shutil.rmtree(fx, ignore_errors=True)
