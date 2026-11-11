from __future__ import annotations

import inspect
import json
import re
import shutil

from . import support
from .support import check, demo_copy
import idiograph_cli


def test_loose_ends_two(scratch):
    print("\n97. Seven loose ends: Export on the GETs screen, the empty Inspector's head once, the sidebars clear of the "
          "zoom bar below 900px, the tabs inside their row, and an "
          "agent's board naming the board it came from")
    import cli
    import server as server_mod
    import themes as themes_mod
    import themes_ai

    js = support.text("apps/idiograph/static/themes.js")
    css = support.text("apps/idiograph/static/themes.css")
    page = support.page_text()
    manual = support.source("docs/manual.md").read_text(encoding="utf-8")
    internals = support.source("docs/internals.md").read_text(encoding="utf-8")
    guide = support.source("docs/agents.md").read_text(encoding="utf-8")
    flat = lambda text: " ".join(str(text).split())
    para = lambda text, head: text.split(head, 1)[1].split("\n\n", 1)[0] if head in text else ""
    tip_of = lambda tag: (re.search(r'title="([^"]*)"', tag) or [None, ""])[1]

    def whole(src: str, head: str) -> str:
        at = src.index(head)
        return src[at:src.index("\n}\n", at) + 3]

    # ── 1. Export on the GETs screen, named as the PETs screen's Export is
    tip = js.split("const GT_EXPORT_TIP = '", 1)[1].split("';", 1)[0] if "const GT_EXPORT_TIP = '" in js else ""
    card = page.split('<div class="overlay" id="gt-print" hidden>', 1)[1].split('\n</div>', 1)[0]
    what = card.split('id="gt-print-what"', 1)[1].split("</div>", 1)[0]
    tips = {w: tip_of(t) for w, t in re.findall(r'(?s)data-what="(\w+)"(.*?)</button>', what)}
    trail = re.search(r'<button[^>]*id="gt-trail-print"[^>]*>([^<]*)</button>', page)
    check("97: 1, the audit trail's own button reads Print, with its tooltip",
          trail is not None and trail.group(1) == "Print" and "audit trail for print or PDF" in trail.group(0)
          and "$('gt-trail-print').onclick = () => { if (TH.trail) gtPrintOpen('trail', TH.trail.gid); };" in js)

    # ── 7. an agent's board names the board it came from, by the screen's own rule
    croot = scratch / "loose-two-root"
    shutil.rmtree(croot, ignore_errors=True)
    book = demo_copy(croot, "P5 - Fern", "P5 Fern - EN & ES.xlsx")
    (croot / server_mod.PROJECT_FILE).write_text(json.dumps(
        {"name": "Orchards, a scratch project", "research_question": "How do people tend a small orchard alone?",
         "agents": {"allowed": True, "at": "2026-10-07T18:00:00+01:00"}}), encoding="utf-8")
    cfg_file = scratch / "loose-two-config.json"
    cfg_file.write_text(json.dumps({"root": str(croot), "interviewer": "Adam"}), encoding="utf-8")
    spec = scratch / "loose-two-board.json"
    spec.write_text(json.dumps({"pets": [{"title": "An invented orchard kept in order", "members": ["S1", "S2"]}]}),
                    encoding="utf-8")
    saved = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        cmd = lambda *a: cli.run(["--root", str(croot), "--config", str(cfg_file), *a])
        code_1, out_1, err_1 = cmd("board", "new", "Fern", "--from", str(spec), "--note", "An invented first request",
                                   "--tool", "Claude Code", "--json")
        first = support.plain(json.loads(out_1)) if code_1 == 0 else {}
        code_d, out_d, _ = cmd("board", "new", "Fern", "--from", str(spec), "--dry-run", "--json")
        dry = support.plain(json.loads(out_d)) if code_d == 0 else {}
        code_2, out_2, err_2 = cmd("board", "new", "Fern", "--from", str(spec), "--note", "An invented second request",
                                   "--tool", "Claude Code", "--json")
        second = support.plain(json.loads(out_2)) if code_2 == 0 else {}
        stored = themes_mod.load(book) or {}
        boards = stored.get("boards") or []
        made = [(b.get("made") or {}) for b in boards]
        check("97: 7, the first board on a case with no file comes from all statements, as New AI board's from all statements does",
              code_1 == 0 and first.get("name") == "Board 1" and first.get("from") == themes_ai.FROM_ALL == "all statements"
              and made[:1] and made[0].get("from") == "all statements"
              and first["said"].startswith("Made Board 1 on ") and ", from all statements: " in first["said"],
              flat(first.get("said") or err_1)[:200])
        check("97: 7, the next comes from the board on the canvas, its dry run saying so, and keeps the tool and the request",
              code_2 == 0 and dry.get("from") == second.get("from") == "Board 1" and dry.get("name") == second.get("name") == "Board 2"
              and ", from Board 1: " in dry.get("said", "") and second["said"].startswith("Made Board 2 on ") and ", from Board 1: " in second["said"]
              and len(made) == 2 and made[1].get("from") == "Board 1" and made[1].get("tool") == "Claude Code"
              and made[1].get("request") == "An invented second request" and made[1].get("by") == "agent"
              and boards[1].get("note", "").startswith("Made by Claude Code in a conversation on "), flat(second.get("said") or err_2)[:200])
        said = [themes_mod.made_said(b) for b in boards]
        check("97: 7, the board menu names the tool and the board it came from, 'with AI' after its name, and New AI board's mark from before nothing (aiout)",
              [s and s["said"] for s in said] == ["Claude Code in a conversation, from all statements",
                                                  "Claude Code in a conversation, from Board 1"]
              and themes_mod.made_said({"made": {"by": "ai", "model": "An invented model", "from": "Board 1",
                                                 "at": "2026-10-07T18:00:00+01:00"}}) is None
              and [themes_mod.summary(b).get("with_ai", {}).get("said") for b in boards][1:] == ["Claude Code in a conversation, from Board 1"],
              str(said))
        check("97: 7, its name follows the one rule a new board on screen follows, Board N by themes.board_name",
              [b.get("name") for b in boards] == ["Board 1", "Board 2"]
              and "else themes.proposal_name(themes.boards_of(data))" in inspect.getsource(idiograph_cli.make_board)
              and "return board_name(versions)" in inspect.getsource(themes_mod.proposal_name)
              and "made_from = source_of(data)" in inspect.getsource(idiograph_cli.make_board)
              and idiograph_cli.source_of(None) == "all statements" and idiograph_cli.source_of({"boards": [{"id": "v1", "name": "Board 1"},
                                                                                       {"id": "v2", "name": "A board of his"}],
                                                                            "current": "v2"}) == "A board of his")
        old_changed = themes_mod.made_mark({"by": "agent", "tool": "Claude Code", "request": "An invented change",
                                            "at": "2026-10-07T18:00:00+01:00"})
        check("97: 7, a change an agent makes keeps no from, and a mark from before it reads as it did",
              old_changed is not None and "from" not in old_changed
              and "mark(args, when)" in inspect.getsource(idiograph_cli.cmd_board_apply)
              and themes_mod.made_said({"note": "Made by Claude Code in a conversation on 5 October 2026 at 19:02, for the request 'x'."})
              == {"by": "agent", "said": "Claude Code in a conversation", "edited": False})
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = saved

    # ── the words
    comments = lambda src: [c for c in re.findall(r"/\*.*?\*/|//[^\n]*|<!--.*?-->", src, flags=re.S)]
    block = lambda src, phrase: next((c for c in comments(src) if phrase in c), "")
    prose = [tip, *tips.values(), tip_of(trail.group(0)) if trail else "", inspect.getdoc(idiograph_cli.mark) or "",
             inspect.getdoc(idiograph_cli.source_of) or "",
             " ".join(comments(whole(js, "function thCorners(").split("stage.style.setProperty('--th-zoom-up'", 1)[1])),
             block(js, "Export on the GETs screen, in the board menu"),
             block(js, "Export, the GETs in print"),
             block(js, "With nothing to show it goes"),
             block(css, "and stops above its bottom corners"), block(css, "the Cases panel the same"),
             block(css, "With nothing selected the head goes"),
             block(page, "four choices, each a short name"), block(page, "Export on the GETs screen: the GET table"),
             block(page, "stopping\n       above the bin"),
             para(guide, "It is laid out the way the app lays out an AI board"),
             para(internals, "schema 2 on its next save. `made` and `changed`")]
    for line in ("named as Export is on PETs", "With nothing selected it has no head", "stopping above the bin and the",
                 "the tool and its source, the board on the canvas"):
        at = manual.find(line)
        prose.append(manual[manual.rfind("\n\n", 0, at):manual.find("\n\n", at)] if at >= 0 else "")
