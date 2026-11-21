"""Area 284: the long texts per language (i18nguide, 28 October 2026, the text layer's sixth build). The guidance
rails (guidance.md, themes_guidance.md) and What's new (docs/whats-new.md) are whole files, not catalogue keys, so
a language's own sits beside the English one with its tag before the suffix (`guidance.es.md`), the app reading
the run's language's and falling back to English when there is none. None is shipped yet: English only, and a language's file keeps the markers `{less}`, `{more}` and `{placeholders}` (langready, 21 November 2026).

What is checked, in a scratch copy and never in the repo: a language with no file reads the English one, one with
a file reads it, the most specific tag wins and a less specific one is the fallback, the rail's lines and What's
new follow the run's language, and nothing in the repo is changed. Fixtures are invented: a made-up language `zz`
and a two-line file about garden birds."""
from __future__ import annotations

import os
from pathlib import Path

from . import support
from .support import check


def test_long_texts(scratch: Path):
    print("\n284. The long texts per language: the guidance rail and What's new read the chosen language's file, "
          "English where there is none (28 October 2026)")
    import boot
    import i18n
    import idiograph_routes as routes
    import server

    docs = scratch / "long" / "docs"
    docs.mkdir(parents=True)
    (docs / "whats-new.md").write_text("# What's new\n\n## 9.9.9, 1 January 2026\n\nThe rooks came back.\n", encoding="utf-8")
    guide = scratch / "long" / "guidance.md"
    guide.write_text("# Guidance\n\n- Name the bird.\n- Name its branch.\n", encoding="utf-8")
    saved = (i18n.LANGUAGE, boot.resource, os.environ.get(server.MANUAL_FILE))
    try:
        os.environ[server.MANUAL_FILE] = str(docs / "manual.md")
        boot.resource = lambda p: guide if str(p) == "guidance.md" else saved[1](p)

        def in_language(tag):
            i18n.LANGUAGE = lambda: tag
            return (server.whats_new_source().name, routes.guidance_lines(), i18n.long_text(guide).name)

        none = in_language("zz")
        check("284: a language with no file reads English, What's new and the rail alike",
              none == ("whats-new.md", ["Name the bird.", "Name its branch."], "guidance.md"), str(none))

        (docs / "whats-new.zz.md").write_text("# What's new\n\n## 9.9.9, 1 January 2026\n\nZz rooks.\n", encoding="utf-8")
        (scratch / "long" / "guidance.zz.md").write_text("# Guidance\n\n- Zz bird.\n- Zz branch.\n", encoding="utf-8")
        has = in_language("zz")
        notes = server.api_whats_new({})["versions"]
        check("284: a language with a file reads it, What's new and the rail alike",
              has == ("whats-new.zz.md", ["Zz bird.", "Zz branch."], "guidance.zz.md")
              and notes[0]["lines"] == ["Zz rooks."], str([has, notes]))

        regional = in_language("zz-QQ")
        (scratch / "long" / "guidance.zz-QQ.md").write_text("# Guidance\n\n- Qq bird.\n", encoding="utf-8")
        specific = in_language("zz-QQ")
        check("284: a regional tag falls back to its language's file, and its own file wins when there is one",
              regional[2] == "guidance.zz.md" and specific[1] == ["Qq bird."], str([regional, specific]))

        english = in_language("en")
        british = in_language("en-GB")
        check("284: English reads the file itself, and no language is named without one",
              english == british == ("whats-new.md", ["Name the bird.", "Name its branch."], "guidance.md")
              and i18n.long_text(guide, "").name == "guidance.md", str([english, british]))
    finally:
        i18n.LANGUAGE, boot.resource = saved[0], saved[1]
        if saved[2] is None:
            os.environ.pop(server.MANUAL_FILE, None)
        else:
            os.environ[server.MANUAL_FILE] = saved[2]

    shipped = [p.name for d in ("docs", "apps/idiograph") for p in support.source(d).iterdir()]
    check("284: no language's long text is shipped yet, English only",
          not [n for n in shipped if n.endswith(".md") and n.count(".") == 2], str(shipped))

    # langready (21 November 2026): a language's guidance file is read by its markers, so it keeps `{less}`, `{more}` and
    # `{placeholders}` and says the rest in its own words, and the reviewed mark, not a file's being there, decides which
    # language "Same as this computer" picks
    marked = scratch / "long" / "guidance.md"
    marked.write_text("# Guidance\n\n## Craft\n\nFraming.\n\n- Name the bird.\n  - {less} Bird\n  - {more} A rook at dawn\n\n"
                      "## Prompts {placeholders}\n\n* What is it?\n", encoding="utf-8")
    (scratch / "long" / "guidance.zz.md").write_text(
        "# Guia\n\n## Oficio\n\nMarco.\n\n- Nombra el ave.\n  - {less} Ave\n  - {more} Una corneja al alba\n\n"
        "## Frases {placeholders}\n\n* Que es?\n", encoding="utf-8")
    kept = i18n.LANGUAGE, boot.resource
    try:
        boot.resource = lambda p: marked if str(p) == "guidance.md" else kept[1](p)
        i18n.LANGUAGE = lambda: "zz"
        spoken = (routes.guidance_lines(), routes.guidance_examples(), routes.guidance_framing(), routes.placeholder_prompts())
        i18n.LANGUAGE = lambda: "en"
        english = (routes.guidance_lines(), routes.guidance_examples(), routes.guidance_framing(), routes.placeholder_prompts())
    finally:
        i18n.LANGUAGE, boot.resource = kept
    check("284: a language's guidance file is read by markers: its rail, examples, framing and prompts, in its own words",
          spoken == (["Nombra el ave."], [{"less": "Ave", "more": "Una corneja al alba"}], "Marco.", ["Que es?"])
          and english == (["Name the bird."], [{"less": "Bird", "more": "A rook at dawn"}], "Framing.", ["What is it?"]),
          str([spoken, english]))
