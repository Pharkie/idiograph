from __future__ import annotations

import json
import shutil

from . import support
from .support import check
import idiograph_routes

# An invented interview about keeping bees, its headings the ones an analyst might give the notes
# column in a spreadsheet made elsewhere. Every word made up.
ROWS = [
    ["Ivo", "00:00:05", "What did the first hive feel like to open?", "x"],
    ["Wren", "00:00:14", "My hands shook. The hum came up through the lid and I felt it in my chest.",
     "the hum as something felt before heard"],
    ["Ivo", "00:00:40", "And now?", ""],
]
NOTE_HEADINGS = ("Thoughts", "Memo", "Memos", "Reflections", "Reflexive notes", "Comments", "Analyst notes")


def test_loose_ends(scratch):
    print("\n213. Loose ends of 20 October: the notes column guessed under an analyst's other words for it, "
          "and a demo's pristine copy never read as a case wherever cases are listed")
    import convert
    import make_demo
    import server as server_mod

    # ── the import card's guess: a notes column under any of these headings is Exploratory notes
    for heading in NOTE_HEADINGS:
        found = convert.guess_columns(["Speaker", "Time", "Transcript", heading], ROWS)
        check(f"a column headed {heading!r} is guessed as Exploratory notes, not Leave out",
              found["en"] == 3 and found["text"] == 2, json.dumps(found))
        check(f"a Word table's heading {heading!r} names the notes",
              convert._head_role(convert._header_key(heading)) == "en")
    found = convert.guess_columns(["Speaker", "Time", "Transcript", "Extra"], ROWS)
    check("a heading of no notes word is still left out", found["en"] is None, json.dumps(found))
    found = convert.guess_columns(["Speaker", "Time", "Transcript", "Reflections", "Experiential statements"],
                                  [r + [""] for r in ROWS])
    check("the statements column beside a Reflections column stays the statements",
          found["en"] == 3 and found["es"] == 4, json.dumps(found))

    # ── a copy of the demo folder added as a project, its pristine copy beside the cases
    root = scratch / "a213-democopy"
    shutil.rmtree(root, ignore_errors=True)
    shutil.copytree(support.source("demo"), root)
    # each case's progress file and board put beside it from the pristine copy, as a first start does
    make_demo.fill(root / "pristine", root)
    # a folder of his own named pristine, with no case folder of its name beside it, is a case
    other = scratch / "a213-own"
    shutil.rmtree(other, ignore_errors=True)
    (other / "pristine").mkdir(parents=True)
    shutil.copy2(support.DEMO_WORKBOOK, other / "pristine" / "Hester - EN & ES.xlsx")
    config = scratch / "a213-config.json"
    config.write_text(json.dumps({"projects": [{"root": str(root)}, {"root": str(other)}], "corpus": "",
                                  "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.STATE_PATH)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config, None
        server_mod.STATE_MEMORY, server_mod.STATE_PATH = {"recent": []}, scratch / "a213-state.json"
        rows = idiograph_routes.list_cases(root)
        listed = [r["path"] for r in rows]
        check("the case list of a demo copy holds its three cases and nothing from its pristine copy",
              sorted(r["case"] for r in rows) == ["Juno", "Mabel", "Rowan"]
              and not any("pristine" in p for p in listed), json.dumps(listed))
        books = idiograph_routes.gets_books(root)
        check("the GETs board's study of a demo copy names each case once",
              sorted(b["case"] for b in books) == ["Juno", "Mabel", "Rowan"], json.dumps([b["case"] for b in books]))
        switcher = idiograph_routes.themes_cases(root / "Juno" / "Juno - EN & ES.xlsx")
        check("the PETs screen's case switcher lists no pristine workbook",
              not any("pristine" in c["path"] for c in switcher)
              and sorted(c["case"] for c in switcher) == ["Juno", "Mabel", "Rowan"],
              json.dumps([c["path"] for c in switcher]))
        own = idiograph_routes.list_cases(other)
        check("a folder of his own named pristine, with no case folder of its name beside it, still holds a case",
              [r["case"] for r in own] == ["pristine"] and own[0]["kind"] == "annotated", json.dumps(own, default=str))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.STATE_PATH = kept
