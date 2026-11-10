"""Area 270: PETs marked complete, and reopened, by an agent (26 October 2026, petsdone, the last gap of the
parity check in area 261). The PETs screen's Mark PETs complete and Reopen PETs call `/api/themes-versions`
with `complete` and `reopen`, and `board complete` (with `--reopen`) and MCP's `board_complete` call the
route's own function, `themes.version_op`. Each check runs the page's call on one project and the agent's op
on its twin and finds the same file written, the dry run writing nothing, History left alone, and complete
refused in the route's words while no board is marked current.

The fixtures are invented: a project on mending nets on a harbour wall, one made-up participant."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from .a267_board_ops import make_workbook, plain, read
from .support import check
from . import support


def test_pets_complete_op(scratch: Path):
    print("\n270. PETs marked complete and reopened by an agent: board complete and --reopen, the page's own route, "
          "the dry run, History left alone and the refusal while no board is current (26 October)")
    import cli
    import mcp_server
    import server as server_mod
    import idiograph_routes as routes
    import themes as themes_mod
    from workbook import WorkbookError

    base = scratch / "pets-complete-270"
    shutil.rmtree(base, ignore_errors=True)
    start, page, agent = base / "start" / "Net menders", base / "page" / "Net menders", base / "agent" / "Net menders"
    start.mkdir(parents=True)
    (start / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Net menders", "research_question": "How do people live mending nets on a harbour wall?",
        "agents": {"allowed": True, "at": "2026-10-26T09:00:00+00:00"}}), encoding="utf-8")
    book = make_workbook(start, "P1 - Bram", "Bram", ["The wall as a place of his own", "Cold that slows the hands",
                                                       "A net made whole before the boats"])
    config_file = base / "config-270.json"
    config_file.write_text(json.dumps({"projects": [], "interviewer": "Interviewer", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    plan = base / "plan.json"
    plan.write_text(json.dumps({"pets": [{"title": "The wall at first light", "members": ["S1"],
                                          "subs": [{"title": "Hands in the cold", "members": ["S2", "S3"]}]}]}),
                    encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)

    def run(root, *args):
        return cli.run(["--config", str(config_file), "--root", str(root), *args])

    def run_json(root, *args):
        code, out, err = run(root, "--json", *args)
        got = support.plain(json.loads(out)) if out.strip() else {}
        return code, (got if code == 0 else {}), err + (got.get("error", "") if code != 0 else "")

    def as_page(body, root):
        """The page's call to /api/themes-versions, on the server's settings, with the recent list in memory."""
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, str(root)
        server_mod.STATE_MEMORY = {"recent": []}
        try:
            return routes.api_themes_versions(dict(body, workbook=str(root / "P1 - Bram" / book.name)))
        finally:
            server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    def twin():
        shutil.rmtree(page.parent, ignore_errors=True)
        shutil.copytree(agent.parent, page.parent)

    def themes_of(root):
        return read(root / "P1 - Bram" / "Working" / f"{book.stem}.themes.json")

    def histories(data):
        return {b["id"]: b.get("history") or [] for b in data["boards"]}

    try:
        made = [run(start, "board", "new", "Bram", "--from", str(plan), "--note", "His first board", "--tool", "Claude Code"),
                run(start, "board", "fresh", "Bram", "--note", "A second board", "--tool", "Claude Code")]
        check("270: the fixture's two boards are made, neither marked current",
              all(m[0] == 0 for m in made) and len(themes_of(start)["boards"]) == 2
              and themes_mod.chosen_of(themes_of(start)) is None, json.dumps([[m[0], m[2]] for m in made]))
        shutil.copytree(start.parent, agent.parent)
        twin()

        # 1. no board marked current: refused in the route's words, the dry run too, nothing written
        before = themes_of(agent)
        code, _x, err = run(agent, "board", "complete", "Bram", "--dry-run")
        code2, _y, err2 = run(agent, "board", "complete", "Bram", "--note", "Her PETs are done", "--tool", "Claude Code")
        try:
            as_page({"op": "complete"}, page)
            said = ""
        except WorkbookError as exc:
            said = str(exc)
        check("270: complete with no Current board is refused with the route's line, its dry run too, nothing written",
              code != 0 and code2 != 0 and said == themes_mod.NO_CURRENT and themes_mod.NO_CURRENT in err
              and themes_mod.NO_CURRENT in err2 and themes_of(agent) == before and themes_of(page) == before,
              f"{err} | {err2} | {said}")

        code, _x, err = run(agent, "board", "current", "Bram", "Board 1", "--note", "Go with board 1", "--tool", "Claude Code")
        check("270: Board 1 marked current for the rest", code == 0 and themes_mod.chosen_of(themes_of(agent)) == "v1", err)
        twin()

        # 2. complete: the dry run writes nothing, then the mark the page's call makes, History alone
        before = themes_of(agent)
        code, dry, err = run_json(agent, "board", "complete", "Bram", "--dry-run")
        check("270: board complete's dry run says it, names the Current board and writes nothing",
              code == 0 and dry.get("dry_run") and "Board 1" in dry.get("said", "") and themes_of(agent) == before, err)
        code, done, err = run_json(agent, "board", "complete", "Bram", "--note", "Her PETs are done", "--tool", "Claude Code")
        as_page({"op": "complete"}, page)
        a, p = themes_of(agent), themes_of(page)
        check("270: board complete marks the Current board as the page's call does, History left as it was",
              code == 0 and done.get("changed") and plain(a) == plain(p)
              and (themes_mod.complete_of(a) or {}).get("board") == "v1"
              and (themes_mod.complete_of(a) or {}).get("name") == "Board 1"
              and histories(a) == histories(before), err)
        marked = themes_of(agent)
        code, again, err = run_json(agent, "board", "complete", "Bram", "--note", "Mark them again", "--tool", "Claude Code")
        check("270: complete on PETs marked already writes nothing and keeps the first time",
              code == 0 and again.get("changed") is False and themes_of(agent) == marked, err)
        twin()

        # 3. reopen: the dry run writes nothing, then the mark taken off as the page's call takes it
        code, dry, err = run_json(agent, "board", "complete", "Bram", "--reopen", "--dry-run")
        check("270: board complete --reopen's dry run says it and writes nothing",
              code == 0 and dry.get("dry_run") and themes_of(agent) == marked, err)
        code, done, err = run_json(agent, "board", "complete", "Bram", "--reopen", "--note", "One more pass",
                                   "--tool", "Claude Code")
        as_page({"op": "reopen"}, page)
        a, p = themes_of(agent), themes_of(page)
        check("270: board complete --reopen takes the mark off as the page's call does, History left as it was",
              code == 0 and done.get("changed") and plain(a) == plain(p) and "complete" not in a
              and histories(a) == histories(marked), err)
        code, again, err = run_json(agent, "board", "complete", "Bram", "--reopen", "--note", "Reopen again",
                                    "--tool", "Claude Code")
        check("270: reopen with no mark writes nothing", code == 0 and again.get("changed") is False and themes_of(agent) == a, err)

        # 4. MCP's board_complete runs the same op
        mcp = mcp_server.Server(root=str(agent), config=str(config_file))
        said = lambda res: support.plain(res.get("structuredContent") or {}) if not res.get("isError") else {}
        r1 = said(mcp.call(mcp.by_name["board_complete"], {"case": "Bram", "dry_run": True, "request": "Look first"}))
        unchanged = themes_of(agent) == a
        r2 = said(mcp.call(mcp.by_name["board_complete"], {"case": "Bram", "request": "Her PETs are done"}))
        r3 = said(mcp.call(mcp.by_name["board_complete"], {"case": "Bram", "reopen": True, "request": "One more pass"}))
        check("270: MCP's board_complete marks and reopens through the same op, its dry run writing nothing",
              r1.get("dry_run") and unchanged and r2.get("changed") and (r2.get("complete") or {}).get("board") == "v1"
              and r3.get("changed") and "complete" not in themes_of(agent), json.dumps([r1, r2, r3])[:600])
    except WorkbookError as exc:
        check("270: the page's calls run", False, str(exc))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
