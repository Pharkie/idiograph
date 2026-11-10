"""Area 282: the server's words through the text layer (i18nserver, 28 October 2026, the text layer's fifth build).
The refusals and lines Idiograph's Python sends the page (apps/idiograph/static/i18n/en/server.json), the family
server's (family/static/i18n/en/errors.json), the headings of the exports (exports.json) and the window's menus
and messages (family/static/i18n/en/menus.json, read by the window's words.rs).

What is checked: a count the server says picks its plural form, a refusal a module keeps as a constant and other
modules name is read in the run's language when it is raised, not when the module was loaded, and so are the
family's and the statements CSV's headings, and a language with no message of its own reads English. Fixtures are
invented: an overlay language `zz` whose messages are about garden birds."""
from __future__ import annotations

import json
from pathlib import Path

from .support import check


def test_server_words(scratch: Path):
    print("\n282. The server's words through the text layer: plurals and slots the server fills, a module's refusal "
          "read in the run's language when raised, the CSV's headings, English where a language has none "
          "(28 October 2026)")
    import i18n
    import idiograph_routes as routes
    import export as export_mod
    import locks
    import themes
    from errors import WorkbookError

    def refused(fn, *args):
        try:
            fn(*args)
        except WorkbookError as exc:
            return str(exc)
        return None

    one = [{"n": 1, "label": "T1"}]
    three = [{"n": i, "label": f"T{i}"} for i in (1, 2, 3)]
    check("282: a count the server says picks its form, one timepoint and three",
          refused(routes.timepoint_asked, "2", one) == "This project has 1 timepoint, so there is no timepoint 2."
          and refused(routes.timepoint_asked, "5", three) == "This project has 3 timepoints, so there is no timepoint 5.",
          str([refused(routes.timepoint_asked, "2", one), refused(routes.timepoint_asked, "5", three)]))
    came = lambda n, a, r=0, x=0, o=0: {"statements": n, "as_sent": a, "reworded": r, "removed": x, "own": o}
    said = [routes.board_in_note("Curt's", "6 Nov", came(1, 1)), routes.board_in_note("Curt's", "6 Nov", came(46, 46)),
            routes.board_in_note("Curt's", "6 Nov", came(1, 0, 1)),
            routes.board_in_note("Curt's", "6 Nov", came(105, 63, 37, 5)), routes.board_in_note("Curt's", "6 Nov", came(68, 63, 0, 5)),
            routes.carries_line({"es": 1, "kq": 2}, True), routes.carries_line({"en": 1}, False)]
    check("282: the lines a board brought in and a merged passage show, each count in its form",
          said == ["Curt's copy, sent 6 Nov: 1 statement as sent.",
                   "Curt's copy, sent 6 Nov: 46 statements as sent.",
                   "Curt's copy, sent 6 Nov: 1 reworded since.",
                   "Curt's copy, sent 6 Nov: 63 statements as sent, 37 reworded since, 5 removed since.",
                   "Curt's copy, sent 6 Nov: 63 statements as sent, 5 removed since.",
                   "The merged passage carries 1 statement and 2 quotes across.",
                   "The passage keeps its 1 note."], str(said))

    # an invented overlay language, two of the app's messages and one of the family's in it
    root = scratch / "a282"
    for name, data in (("server.json", {"server.board_longer_themes_file_nothing": "The robin flew off the board."}),
                       ("exports.json", {"exports.csv_quote": "Song"}),
                       ("errors.json", {"errors.another_write_these_files_under": "Another wren is in the nest."})):
        folder = root / "static" / "i18n" / "zz"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / name).write_text(json.dumps(data), encoding="utf-8")
    was_language, was_roots = i18n.LANGUAGE, i18n.ROOTS
    english = (themes.GONE, locks.BUSY, export_mod.HEADER)
    try:
        i18n.ROOTS = lambda: [*was_roots(), root]
        i18n.LANGUAGE = lambda: "zz"
        there = (themes.GONE, locks.BUSY, export_mod.header()[-1], export_mod.header()[0])
    finally:
        i18n.LANGUAGE, i18n.ROOTS = was_language, was_roots
    back = (themes.GONE, locks.BUSY, export_mod.HEADER)
    check("282: a refusal kept as a module's constant, the family's lock refusal and the CSV's headings read in the "
          "run's language when asked for, English for a heading the language lacks, and English again after",
          there == ("The robin flew off the board.", "Another wren is in the nest.", "Song", "Interview")
          and back == english and english[0] == "That board is no longer in the themes file, so nothing was written."
          and english[2][-1] == "Quote", str([there, english[:2]]))
