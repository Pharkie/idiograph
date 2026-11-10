"""Area 267: the boards' ops for agents (26 October 2026, parity's third group, Adam's principle of 19 and 24
October: one API, the app one way to call it and an agent another). The routes the PETs and GETs screens call
for a board's note, its History, Copy to board, the PET draft, the GETs board menu, a GETs board's History,
Add every sub-theme and the study's settings had no op on the command line or the MCP server. Each op calls
the route's own function, so each check runs the page's call on one project and the agent's op on its twin
and finds the same file written, the dry run writing nothing, and History recording the agent's change.

The fixtures are invented: a project on keeping an allotment at dawn, two made-up participants."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import openpyxl

from .support import check
from . import support

TIMES = ("updated", "created", "at", "made", "changed", "edited")


def make_workbook(root: Path, folder: str, speaker: str, lines: list[str]) -> Path:
    """A made-up participant's annotated workbook, one statement on each of three passages."""
    import workbook as wb_mod
    case = root / folder
    (case / "Source").mkdir(parents=True)
    raw = openpyxl.Workbook()
    first = raw.active
    first.title = "Initial"
    first.append(["Name", "Timestamp", "Transcript"])
    talk = ["The light comes up over the sheds and nobody else is there.",
            "The ground was hard with frost and the leeks stood up out of it.",
            "I go home with mud on my knees and the day has not started."]
    for n, said in enumerate(talk):
        first.append(["Interviewer", f"00:0{n}:04", "And then?"])
        first.append([speaker, f"00:0{n}:30", said])
    source = case / "Source" / f"{folder} - interview.xlsx"
    raw.save(source)
    book = wb_mod.create_from_source(source, case / f"{folder} - EN & ES.xlsx")
    wb = openpyxl.load_workbook(book, rich_text=True)
    ws = wb.worksheets[0]
    cols = wb_mod.detect_columns(ws)
    for row, text in zip((3, 5, 7), lines):
        ws.cell(row, cols["es"]).value = text
    wb.save(book)
    return book


def plain(value, drop=()):
    """A JSON value with every time and agent's mark set aside, and the keys `drop` names."""
    if isinstance(value, dict):
        return {k: plain(v, drop) for k, v in value.items() if k not in TIMES and k not in drop}
    if isinstance(value, list):
        return [plain(v, drop) for v in value]
    return value


def read(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_board_ops(scratch: Path):
    print("\n267. The boards' ops for agents: board note, history, revision, restore, copy and export --draft, the "
          "GETs board menu, their History, Add every sub-theme and the study's settings, each the page's own route, "
          "its dry run and its History (26 October)")
    import cli
    import gets as gets_mod
    import mcp_server
    import server as server_mod
    import idiograph_routes as routes
    from workbook import WorkbookError

    base = scratch / "board-ops-267"
    shutil.rmtree(base, ignore_errors=True)
    start, page, agent = base / "start" / "Dawn plots", base / "page" / "Dawn plots", base / "agent" / "Dawn plots"
    start.mkdir(parents=True)
    (start / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Dawn plots", "research_question": "How do people live keeping an allotment at dawn?",
        "agents": {"allowed": True, "at": "2026-10-26T09:00:00+00:00"}}), encoding="utf-8")
    hazel = make_workbook(start, "P1 - Hazel", "Hazel", ["Having the plots to herself", "Frost as the season's mark",
                                                          "Work done before the day begins"])
    make_workbook(start, "P2 - Corin", "Corin", ["Light as a summons", "The cold in the hands", "Mud as proof of the morning"])
    config_file = base / "config-267.json"
    config_file.write_text(json.dumps({"projects": [], "interviewer": "Interviewer", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    plan = base / "plan.json"
    plan.write_text(json.dumps({"pets": [{"title": "Dawn at the plot", "members": ["S1"],
                                          "subs": [{"title": "The first frost", "members": ["S2", "S3"]}]}]}),
                    encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)

    def run(root, *args):
        return cli.run(["--config", str(config_file), "--root", str(root), *args])

    def run_json(root, *args):
        code, out, err = run(root, "--json", *args)
        got = support.plain(json.loads(out)) if out.strip() else {}
        return code, (got if code == 0 else {}), err + (got.get("error", "") if code != 0 else "")

    def as_page(fn, body, root):
        """The page's call, on the server's settings, with the recent list in memory."""
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, str(root)
        server_mod.STATE_MEMORY = {"recent": []}
        try:
            return fn(body)
        finally:
            server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    def twin():
        """The page's project made the agent's again, so the next op starts both alike."""
        shutil.rmtree(page.parent, ignore_errors=True)
        shutil.copytree(agent.parent, page.parent)

    def themes_of(root):
        return read(root / "P1 - Hazel" / "Working" / f"{hazel.stem}.themes.json")

    def gets_of(root):
        return read(root / gets_mod.FILE)

    def book_of(root):
        return str(root / "P1 - Hazel" / hazel.name)

    def last(board: dict) -> dict:
        return (board.get("history") or [{}])[-1]

    def board_of(data: dict, name: str) -> dict:
        return next(b for b in data["boards"] if b["name"] == name)

    try:
        made = [run(start, "board", "new", who, "--from", str(plan), "--note", "His first board", "--tool", "Claude Code")
                for who in ("Hazel", "Corin")]
        made.append(run(start, "board", "fresh", "Hazel", "--note", "A second board", "--tool", "Claude Code"))
        made.append(run(start, "board", "canvas", "Hazel", "Board 1", "--note", "Back to board 1", "--tool", "Claude Code"))
        # the GETs file, made by the page's first act, a revision kept by hand, with one sub-theme's card taken
        # off for Add every sub-theme
        as_page(routes.api_gets_boards, {"root": str(start), "op": "revision", "name": "Start"}, start)
        held = gets_of(start)
        subs = [k for k, _ in gets_mod.subs_of("P1 - Hazel", held["cases"]["P1 - Hazel"])]
        for k in subs:
            held["boards"][0]["cards"].pop(k, None)
            for r in held["boards"][0].get("history") or []:
                r["state"]["cards"].pop(k, None)
        (start / gets_mod.FILE).write_text(json.dumps(held), encoding="utf-8")
        check("267: the fixture's boards are made, two on Hazel's canvas, and the GETs file with one sub-theme's card off",
              all(m[0] == 0 for m in made) and len(themes_of(start)["boards"]) == 2 and subs,
              json.dumps([[m[0], m[2]] for m in made]) + f" {len(themes_of(start)['boards'])} {subs}")
        shutil.copytree(start.parent, agent.parent)
        twin()

        # 1. board note, the board note on the PETs screen
        before = themes_of(agent)
        code, dry, err = run_json(agent, "board", "note", "Hazel", "Board 1", "Made after supervision", "--dry-run")
        check("267: board note's dry run says it and writes nothing", code == 0 and dry.get("dry_run") and themes_of(agent) == before, err)
        code, done, err = run_json(agent, "board", "note", "Hazel", "Board 1", "Made after supervision",
                                   "--note", "Note what supervision said", "--tool", "Claude Code")
        as_page(routes.api_themes_versions, {"workbook": book_of(page), "op": "note", "id": "v1",
                                             "note": "Made after supervision"}, page)
        a, p = themes_of(agent), themes_of(page)
        check("267: board note writes the note the page's note writes",
              code == 0 and plain(a, ("history",)) == plain(p, ("history",)) and board_of(a, "Board 1")["note"] == "Made after supervision",
              err)
        rev = last(board_of(a, "Board 1"))
        check("267: board note keeps the board first in its History, naming the tool and his request",
              rev.get("name") == "Board note changed: Note what supervision said"
              and (rev.get("made") or {}).get("tool") == "Claude Code", json.dumps(rev)[:200])
        twin()

        # 2. board revision, Save a revision
        before = themes_of(agent)
        code, _dry, err = run_json(agent, "board", "revision", "Hazel", "Board 1", "--name", "Before the walk", "--dry-run")
        check("267: board revision's dry run writes nothing", code == 0 and themes_of(agent) == before, err)
        code, done, err = run_json(agent, "board", "revision", "Hazel", "Board 1", "--name", "Before the walk",
                                   "--note", "Keep it as it is", "--tool", "Claude Code")
        as_page(routes.api_themes_boards, {"workbook": book_of(page), "op": "revision", "id": "v1",
                                           "name": "Before the walk"}, page)
        a, p = themes_of(agent), themes_of(page)
        check("267: board revision keeps the revision the page's Save a revision keeps, its History one longer",
              code == 0 and plain(a) == plain(p) and last(board_of(a, "Board 1"))["name"] == "Before the walk"
              and len(board_of(a, "Board 1")["history"]) == len(board_of(before, "Board 1").get("history") or []) + 1
              and (last(board_of(a, "Board 1")).get("made") or {}).get("request") == "Keep it as it is", err)
        twin()

        # 3. board copy, Copy to board
        before = themes_of(agent)
        code, _dry, err = run_json(agent, "board", "copy", "Hazel", "Board 1", "Dawn at the plot", "--to", "Board 2", "--dry-run")
        check("267: board copy's dry run writes nothing", code == 0 and themes_of(agent) == before, err)
        code, done, err = run_json(agent, "board", "copy", "Hazel", "Board 1", "Dawn at the plot", "--to", "Board 2",
                                   "--note", "Try the dawn PET on board 2", "--tool", "Claude Code")
        gid = next(g["id"] for g in board_of(before, "Board 1")["groups"] if g["label"] == "Dawn at the plot")
        as_page(routes.api_themes_boards, {"workbook": book_of(page), "op": "copy", "id": "v1", "group": gid, "to": "v2"}, page)
        a, p = themes_of(agent), themes_of(page)
        two = board_of(a, "Board 2")
        check("267: board copy copies the label as Copy to board does, Board 2 keeping a revision first and marked "
              "as changed in a conversation",
              code == 0 and plain(a) == plain(p) and any(g["label"] == "Dawn at the plot" for g in two["groups"])
              and last(two)["name"] == "Before Dawn at the plot copied from Board 1"
              and (two.get("changed") or {}).get("by") == "agent", err)
        code, _x, err = run(agent, "board", "copy", "Hazel", "Board 1", "No such PET", "--to", "Board 2", "--note", "x")
        check("267: a label the board does not have is refused, nothing written",
              code != 0 and "No label called No such PET" in err and themes_of(agent) == a, err)
        twin()

        # 4. board restore, the History tab's Restore
        before = themes_of(agent)
        rid = last(board_of(before, "Board 2"))["id"]
        code, _dry, err = run_json(agent, "board", "restore", "Hazel", "Board 2", rid, "--dry-run")
        check("267: board restore's dry run writes nothing", code == 0 and themes_of(agent) == before, err)
        code, done, err = run_json(agent, "board", "restore", "Hazel", "Board 2", rid, "--note", "Put board 2 back",
                                   "--tool", "Claude Code")
        as_page(routes.api_themes_boards, {"workbook": book_of(page), "op": "restore", "id": "v2", "revision": rid}, page)
        a, p = themes_of(agent), themes_of(page)
        two = board_of(a, "Board 2")
        check("267: board restore makes the revision the board as Restore does, the board kept first",
              code == 0 and plain(a) == plain(p) and not two["groups"] and last(two)["name"].startswith("Before restoring")
              and (last(two).get("made") or {}).get("request") == "Put board 2 back", err)
        code, _x, err = run(agent, "board", "restore", "Hazel", "Board 2", "r99", "--note", "x")
        check("267: a revision the History does not hold is refused in the route's words",
              code != 0 and "no longer in the board's history" in err, err)

        # 5. board history, read
        code, hist, err = run_json(agent, "board", "history", "Hazel", "Board 2")
        code2, one, err2 = run_json(agent, "board", "history", "Hazel", "Board 2", "--revision", rid)
        check("267: board history lists the revisions newest first, and one revision as board show sets a board out",
              code == 0 and code2 == 0 and [r["id"] for r in hist["history"]] == [r["id"] for r in reversed(two["history"])]
              and one.get("revision", {}).get("id") == rid and "themes" in one and themes_of(agent) == a, err + err2)
        twin()

        # 6. board export --draft, the PETs screen's Export
        working = agent / "P1 - Hazel" / "Working"
        listed = sorted(f.name for f in working.iterdir())
        code, dry, err = run_json(agent, "board", "export", "Hazel", "Board 1", "--draft", "--dry-run")
        check("267: board export --draft's dry run names the draft and the CSV and writes nothing",
              code == 0 and dry.get("markdown", "").endswith("PET draft (Board 1).md") and dry.get("csv", "").endswith(".csv")
              and sorted(f.name for f in working.iterdir()) == listed, err + json.dumps(dry))
        code, done, err = run_json(agent, "board", "export", "Hazel", "Board 1", "--draft")
        as_page(routes.api_themes_export, {"workbook": book_of(page), "version": "v1"}, page)
        names = [Path(done.get("markdown", "x")).name, Path(done.get("csv", "x")).name]
        check("267: board export --draft writes the draft and the CSV the page's Export writes, byte for byte",
              code == 0 and all((working / n).read_bytes() == (page / "P1 - Hazel" / "Working" / n).read_bytes() for n in names),
              err + str(names))
        code, _x, err = run(agent, "board", "export", "Hazel", "--draft", "--labels", "numbers")
        check("267: --draft with an option it does not take is refused", code != 0 and "--draft takes --stacked alone" in err, err)
        twin()

        # 7. the GETs board menu: new, rename, note, duplicate, canvas, current, delete
        def gets_step(label, agent_args, page_body, extra=lambda a, p: True, drop=()):
            before = gets_of(agent)
            code, _dry, err = run_json(agent, *agent_args, "--dry-run")
            dry_ok = code == 0 and gets_of(agent) == before
            code, done, err2 = run_json(agent, *agent_args, "--note", f"His request: {label}", "--tool", "Claude Code")
            if page_body is not None:
                as_page(routes.api_gets_ops, dict(page_body, root=str(page)), page)
            a, p = gets_of(agent), gets_of(page)
            check(f"267: gets {label}'s dry run writes nothing, and the op writes what the page's {page_body and page_body['op']} writes",
                  dry_ok and code == 0 and plain(a, ("history",) + drop) == plain(p, ("history",) + drop) and extra(a, p),
                  err + err2)
            twin()
            return a, done

        a, _ = gets_step("fresh", ["gets", "fresh", "--name", "Second try"], {"op": "new", "name": "Second try"})
        second = board_of(a, "Second try")["id"]
        a, _ = gets_step("rename", ["gets", "rename", "Second try", "By the sheds"],
                         {"op": "rename", "id": second, "name": "By the sheds"},
                         lambda a, p: last(board_of(a, "By the sheds"))["name"].startswith("Renamed from Second try: "))
        check("267: gets rename keeps the board first in its History, naming the tool",
              (last(board_of(a, "By the sheds")).get("made") or {}).get("tool") == "Claude Code")
        a, _ = gets_step("note", ["gets", "note", "By the sheds", "Grouped by where they stand"],
                         {"op": "note", "id": second, "note": "Grouped by where they stand"},
                         lambda a, p: last(board_of(a, "By the sheds"))["name"].startswith("Board note changed: "))
        a, done = gets_step("duplicate", ["gets", "duplicate", "By the sheds", "--name", "Sheds trial"],
                            {"op": "duplicate", "id": second, "name": "Sheds trial"},
                            lambda a, p: "Claude Code" in board_of(a, "Sheds trial")["note"], drop=("note",))
        trial = board_of(a, "Sheds trial")["id"]
        gets_step("canvas", ["gets", "canvas", "Board 1"], {"op": "switch", "id": "b1"},
                  lambda a, p: a["current"] == "b1")
        gets_step("current", ["gets", "current", "By the sheds"], {"op": "choose", "id": second},
                  lambda a, p: a.get("chosen") == second
                  and last(board_of(a, "By the sheds"))["name"].startswith("Marked the Current board: "))
        gets_step("delete", ["gets", "delete", "Sheds trial"], {"op": "delete", "id": trial},
                  lambda a, p: all(b["id"] != trial for b in a["boards"])
                  and any(f.name.startswith("idiograph-gets board Sheds trial") for f in (agent / "_Archive").iterdir()))
        code, _x, err = run(agent, "gets", "rename", "By the sheds", "Board 1", "--note", "x")
        check("267: a GETs board's name another board has is refused in the route's words",
              code != 0 and "Another board is called Board 1 already" in err, err)

        # 8. a GETs board's History: revision, restore, history, and Add every sub-theme
        before = gets_of(agent)
        code, _d, err = run_json(agent, "gets", "revision", "Board 1", "--name", "Before the frost", "--dry-run")
        dry_ok = code == 0 and gets_of(agent) == before
        code, _d, err2 = run_json(agent, "gets", "revision", "Board 1", "--name", "Before the frost", "--note", "Keep it",
                                  "--tool", "Claude Code")
        as_page(routes.api_gets_boards, {"root": str(page), "op": "revision", "id": "b1", "name": "Before the frost"}, page)
        a, p = gets_of(agent), gets_of(page)
        check("267: gets revision keeps the revision the page's Save a revision keeps, its dry run writing nothing",
              dry_ok and code == 0 and plain(a) == plain(p) and last(board_of(a, "Board 1"))["name"] == "Before the frost",
              err + err2)
        twin()
        rid = board_of(gets_of(agent), "Board 1")["history"][0]["id"]
        before = gets_of(agent)
        code, _d, err = run_json(agent, "gets", "restore", "Board 1", rid, "--dry-run")
        dry_ok = code == 0 and gets_of(agent) == before
        code, _d, err2 = run_json(agent, "gets", "restore", "Board 1", rid, "--note", "Back to the start",
                                  "--tool", "Claude Code")
        as_page(routes.api_gets_boards, {"root": str(page), "op": "restore", "id": "b1", "revision": rid}, page)
        a, p = gets_of(agent), gets_of(page)
        one = board_of(a, "Board 1")
        check("267: gets restore restores as Restore does, the board kept first and marked as changed in a conversation",
              dry_ok and code == 0 and plain(a) == plain(p) and last(one)["name"].startswith("Before restoring")
              and (one.get("changed") or {}).get("by") == "agent", err + err2)
        code, hist, err = run_json(agent, "gets", "history", "Board 1")
        code2, view, err2 = run_json(agent, "gets", "history", "Board 1", "--revision", rid)
        check("267: gets history lists the revisions, and one as gets show sets a board out",
              code == 0 and code2 == 0 and len(hist["history"]) == len(one["history"])
              and view.get("revision", {}).get("id") == rid and "themes" in view, err + err2)
        twin()
        before = gets_of(agent)
        code, dry, err = run_json(agent, "gets", "subs", "Board 1", "--dry-run")
        route = as_page(routes.api_gets_boards, {"root": str(page), "op": "subs", "id": "b1"}, page)
        dry_ok = code == 0 and gets_of(agent) == before and gets_of(page) == before
        code, done, err2 = run_json(agent, "gets", "subs", "Board 1", "--note", "Every sub-theme on", "--tool", "Claude Code")
        one = board_of(gets_of(agent), "Board 1")
        check("267: gets subs puts on the board each card the route's Add every sub-theme places, where it places it, "
              "the board kept first in its History",
              dry_ok and code == 0 and route["added"] and all(one["cards"].get(c["key"]) == {"x": c["x"], "y": c["y"]}
                                                                for c in route["added"])
              and last(one)["name"] == "Before: Every sub-theme on", err + err2 + json.dumps(dry)[:200])
        code, _x, err = run(agent, "gets", "subs", "Board 1", "--note", "Again")
        check("267: a second Add every sub-theme is refused in the route's words",
              code != 0 and "Every sub-theme has a card on this board already" in err, err)
        twin()

        # 9. GETs complete, refused while a participant waits, then marked and reopened
        code, _x, err = run(agent, "gets", "complete", "--dry-run")
        check("267: gets complete is refused while a participant's PETs are not complete, in the route's words",
              code != 0 and "GETs were not marked complete. Waiting on" in err, err)
        for who, folder in (("Hazel", "P1 - Hazel"), ("Corin", "P2 - Corin")):
            run(agent, "board", "current", who, "Board 1", "--note", "Go with board 1")
            book = next((agent / folder).glob("*EN & ES.xlsx"))
            as_page(routes.api_themes_versions, {"workbook": str(book), "op": "complete"}, agent)
            run(agent, "gets", "take", who, "--note", "Bring the marks in")
        twin()
        before = gets_of(agent)
        code, _d, err = run_json(agent, "gets", "complete", "--dry-run")
        dry_ok = code == 0 and gets_of(agent) == before
        code, done, err2 = run_json(agent, "gets", "complete", "--note", "GETs are done")
        as_page(routes.api_gets_ops, {"root": str(page), "op": "complete"}, page)
        a, p = gets_of(agent), gets_of(page)
        check("267: gets complete marks GETs complete as the page's GETs complete does, its dry run writing nothing",
              dry_ok and code == 0 and plain(a) == plain(p) and (a.get("complete") or {}).get("board"), err + err2)
        code, done, err = run_json(agent, "gets", "complete", "--reopen", "--note", "Not yet")
        as_page(routes.api_gets_ops, {"root": str(page), "op": "reopen"}, page)
        a, p = gets_of(agent), gets_of(page)
        check("267: gets complete --reopen takes the mark off as reopen does",
              code == 0 and plain(a) == plain(p) and not a.get("complete"), err)
        twin()

        # 10. the study's settings
        code, view, err = run_json(agent, "gets", "settings")
        check("267: gets settings reads the study's settings as Settings, GETs shows them, writing nothing",
              code == 0 and view.get("total") == 2 and len(view.get("study", [])) == 2, err)
        before = gets_of(agent)
        args = ["gets", "settings", "--minimum", "1", "--one-per-pet", "off", "--out", "Corin=Interviewed for the pilot alone"]
        code, dry, err = run_json(agent, *args, "--dry-run")
        check("267: gets settings' dry run says each change and writes nothing",
              code == 0 and len(dry.get("changes", [])) == 3 and gets_of(agent) == before, err + json.dumps(dry))
        code, done, err = run_json(agent, *args, "--note", "Pilot out")
        as_page(routes.api_gets_settings, {"root": str(page), "op": "save", "minimum": 1, "one_per_pet": False,
                                           "study": {"P2 - Corin": {"in": False, "reason": "Interviewed for the pilot alone"}}},
                page)
        a, p = gets_of(agent), gets_of(page)
        check("267: gets settings saves what the page's save saves",
              code == 0 and plain(a) == plain(p) and a["study"]["P2 - Corin"]["in"] is False, err)
        code, _x, err = run(agent, "gets", "settings", "--out", "Hazel", "--note", "No reason")
        check("267: a participant out with no reason is refused in the route's words",
              code != 0 and "Say in a line why Hazel is out of the study" in err, err)

        # 11. the MCP tools run the same ops
        mcp = mcp_server.Server(root=str(agent), config=str(config_file))
        names = {t["name"] for t in mcp.tools}
        wanted = {"board_note", "board_history", "board_revision", "board_restore", "board_copy", "gets_fresh",
                  "gets_duplicate", "gets_rename", "gets_note", "gets_canvas", "gets_current", "gets_delete",
                  "gets_complete", "gets_history", "gets_revision", "gets_restore", "gets_subs", "gets_settings",
                  "gets_settings_set"}
        before_t, before_g = themes_of(agent), gets_of(agent)
        said = lambda res: support.plain(res.get("structuredContent") or {}) if not res.get("isError") else {}
        r1 = said(mcp.call(mcp.by_name["board_note"], {"case": "Hazel", "board": "Board 1", "note": "From MCP",
                                                         "dry_run": True, "request": "Look first"}))
        r2 = said(mcp.call(mcp.by_name["board_history"], {"case": "Hazel", "board": "Board 2"}))
        r3 = said(mcp.call(mcp.by_name["gets_settings_set"], {"in": ["Corin"], "dry_run": True, "request": "Look first"}))
        r4 = said(mcp.call(mcp.by_name["gets_settings"], {}))
        r5 = said(mcp.call(mcp.by_name["board_export"], {"case": "Hazel", "format": "draft", "dry_run": True}))
        r6 = said(mcp.call(mcp.by_name["gets_fresh"], {"dry_run": True, "request": "Look first"}))
        check("267: MCP's tools run the same ops, each dry run writing nothing",
              wanted <= names and r1.get("dry_run") and r2.get("history") and r3.get("changes") == ["Corin back in the study."]
              and len(r4.get("study") or []) == 2 and r5.get("format") == "draft" and r6.get("dry_run")
              and themes_of(agent) == before_t and gets_of(agent) == before_g,
              json.dumps([r1, r2, r3, r4, r5, r6])[:600] + str(wanted - names))
    except WorkbookError as exc:
        check("267: the page's calls run", False, str(exc))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
