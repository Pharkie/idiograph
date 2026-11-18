"""Area 426: the Trajectories' own mark complete (trajmark, 18 November 2026).

Every stage's complete is the researcher's own mark, and Trajectories had none. The ops `complete` and `reopen` of
`/api/trajectories-ops`, which the command line's and MCP's `trajectories apply` run as the same ops, keep `complete`
at the top of the trajectories file. What is checked, on a scratch copy of the longitudinal demo as a fresh clone has
it, agents allowed. A: with a participant in no trajectory `complete` is refused in one line naming them, by the
route, the command line and MCP, dry run and real, nothing written. B: with everyone placed, the dry runs of all
three write nothing, not a lock, and the answer says what the mark would be. C: the command line marks it, the
board and the project page's tile answer it with the time, a second `complete` keeps the first time and writes
nothing, and the agent's run, undone by `agents undo-run`, puts every file back byte for byte. D: the route sets and
clears it as one step of the screen's Undo each, byte for byte, and MCP's `trajectories_apply` marks and reopens it.
E: the page holds the button and the strings the catalogue keeps."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import support
from .a395_gets_first import as_cloned, tree, unlocked, whole
from .support import check as said_check


def check(name, ok, detail=""):
    said_check(name, bool(ok), "" if ok else str(detail)[:700])


def test_trajectories_complete(scratch: Path):
    print("\n426. Mark Trajectories complete: the ops complete and reopen through the route, the command line and MCP, "
          "refused with a participant unplaced, dry runs writing nothing, undone by the screen's Undo and by an "
          "agent's Undo (trajmark, 18 November)")
    import cli
    import gets as gets_mod
    import idiograph_routes
    import make_demo
    import mcp_server
    import server as server_mod
    import trajectories as traj_mod

    base = scratch / "a426"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    cfg_file = scratch / "a426-config.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "Adam", "corpus": "", "gravity_reference": "",
                                    "corpus_exclude": []}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)

    def run(root: Path, *args) -> tuple[int, str, str]:
        return cli.run(["--root", str(root), "--config", str(cfg_file), *args])

    def answer(root: Path, *args) -> tuple[int, dict]:
        code, out, err = run(root, *args, "--json")
        return code, (support.plain(json.loads(out)) if out.strip() else {"error": err})

    def spec(name: str, value) -> str:
        path = base / f"{name}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return str(path)

    def call(route: str, body: dict) -> dict:
        with idiograph_routes.route_scope(route, body):
            return server_mod.ROUTES[route](body)

    def refused(body: dict) -> str:
        try:
            call("/api/trajectories-ops", body)
        except server_mod.WorkbookError as exc:
            return str(exc)
        return "answered"

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "a426-state.json", {"recent": []}
        root = base / "lipa"
        shutil.copytree(support.source("demo/lipa"), root, ignore=as_cloned)
        make_demo.fill(root / "pristine", root)
        cfg_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Adam", "corpus": "",
                                        "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
        server_mod.ROOT_OVERRIDE = str(root)
        try:
            idiograph_routes.api_project({"root": str(root), "agents": True})
        finally:
            server_mod.ROOT_OVERRIDE = None
        unlocked(root)
        tjfile = traj_mod.path_of(root)
        book = next(p for p in sorted(root.glob("*/*.xlsx")) if p.parent.name not in ("pristine", "Source"))

        def ops(*given, **more) -> dict:
            return call("/api/trajectories-ops", dict({"workbook": str(book), "ops": list(given)}, **more))

        def board() -> dict:
            return call("/api/trajectories", {"workbook": str(book)})

        def head() -> dict:
            return call("/api/cases", {})["gets"]

        first = board()
        people = [p["case"] for p in first["participants"]]
        cols = [c["id"] for c in first["columns"]]
        # the demo's participants all placed, one then taken out of every trajectory
        for n, case in enumerate(people):
            if not next(p for p in board()["participants"] if p["case"] == case)["column"]:
                ops({"op": "place", "participant": case, "column": cols[n % len(cols)]})
        check("426: the scratch copy has its participants, each placed in a trajectory, and no mark",
              len(people) >= 2 and not board()["unplaced"] and board().get("complete") is None
              and "complete" not in json.loads(tjfile.read_text(encoding="utf-8")),
              [people, board().get("unplaced")])
        out_case = people[-1]
        ops({"op": "place", "participant": out_case, "column": None})
        who = traj_mod.who(out_case)
        lone = spec("complete", [{"op": "complete"}])

        # ── A. refused with a participant unplaced, nothing written
        was = whole(root)
        route_said = refused({"workbook": str(book), "ops": [{"op": "complete"}]})
        route_dry = refused({"workbook": str(book), "ops": [{"op": "complete"}], "dry_run": True})
        code, _o, err = run(root, "trajectories", "apply", "--ops", lone, "--note", "Mark it", "--tool", "Claude Code")
        code_dry, _o2, err_dry = run(root, "trajectories", "apply", "--ops", lone, "--dry-run")
        mcp = mcp_server.Server(root=str(root), config=str(cfg_file))
        r_mcp = mcp.call(mcp.by_name["trajectories_apply"], {"operations": [{"op": "complete"}], "request": "Mark it"})
        check("426: complete is refused with a participant in no trajectory, by the route, the command line and MCP, "
              "dry run or real, in one line naming them, nothing written",
              route_said != "answered" and who in route_said and "\n" not in route_said and route_dry == route_said
              and code != 0 and who in err and code_dry != 0 and who in err_dry
              and r_mcp.get("isError") and who in json.dumps(r_mcp) and whole(root) == was,
              [route_said, route_dry, err, err_dry, r_mcp])
        placed_with = refused({"workbook": str(book), "ops": [{"op": "place", "participant": out_case, "column": cols[0]},
                                                               {"op": "complete"}], "dry_run": True})
        check("426: placing them and marking in one change is allowed, a dry run of it writing nothing",
              placed_with == "answered" and whole(root) == was, placed_with)

        # ── B. everyone placed: the dry runs write nothing, not a lock
        ops({"op": "place", "participant": out_case, "column": cols[0]})
        unlocked(root)
        bare = whole(root)
        code, dry_cli = answer(root, "trajectories", "apply", "--ops", lone, "--dry-run")
        cli_clean = whole(root) == bare and not list(root.rglob(".idiograph.lock"))
        # the route's and MCP's own request lock is the server's, so their dry runs are compared without lock files
        bare = {k: v for k, v in whole(root).items() if not k.endswith(".lock")}
        dry_route = ops({"op": "complete"}, dry_run=True)
        r_dry = mcp.call(mcp.by_name["trajectories_apply"], {"operations": [{"op": "complete"}], "dry_run": True,
                                                              "request": "Look first"})
        check("426: the dry runs of the route, the command line and MCP say Trajectories would be marked complete and "
              "write nothing, the command line's leaving no lock",
              dry_route.get("changes") == ["Trajectories marked complete."] and dry_route.get("dry_run") is True
              and code == 0 and dry_cli.get("changes") == ["Trajectories marked complete."] and not r_dry.get("isError")
              and cli_clean and {k: v for k, v in whole(root).items() if not k.endswith(".lock")} == bare,
              [dry_route.get("changes"), dry_cli.get("changes"), r_dry.get("isError"), cli_clean,
               sorted(k for k, v in whole(root).items() if not k.endswith(".lock") and bare.get(k) != v)])

        # the hole in one call: marking, then unplacing, in one call is refused whole, nothing written
        held_before = whole(root)
        hole = refused({"workbook": str(book), "ops": [{"op": "complete"},
                                                       {"op": "place", "participant": people[0], "column": None}]})
        check("426: marking and then unplacing a participant in one call is refused whole, nothing written",
              hole != "answered" and traj_mod.who(people[0]) in hole and whole(root) == held_before
              and "complete" not in json.loads(tjfile.read_text(encoding="utf-8")), hole)
        # reopen, then mark, then unplace, in one call on a board marked before: the new mark is held to the rule too
        ops({"op": "complete"})
        marked_stood = whole(root)
        again_hole = refused({"workbook": str(book), "ops": [{"op": "reopen"}, {"op": "complete"},
                                                             {"op": "place", "participant": people[0], "column": None}]})
        check("426: reopen, complete and unplace in one call on a marked board is refused whole, nothing written",
              again_hole != "answered" and whole(root) == marked_stood, again_hole)
        ops({"op": "reopen"})
        # a project with no participant cannot be marked, in a plain sentence, nothing written
        bare_data = traj_mod.fresh("2026-11-18T10:00:00")
        try:
            traj_mod.apply(bare_data, [], [{"op": "complete"}], when="2026-11-18T10:00:00")
            nobody = "answered"
        except server_mod.WorkbookError as exc:
            nobody = str(exc)
        check("426: complete is refused when the project has no participant, in one plain sentence, nothing written",
              nobody != "answered" and "no participant" in nobody and "\n" not in nobody
              and "complete" not in bare_data, nobody)

        # ── C. the command line marks it, an agent's run undone byte for byte
        before = tree(root)
        code, done = answer(root, "trajectories", "apply", "--ops", lone, "--note", "Mark it", "--tool", "Claude Code")
        held = json.loads(tjfile.read_text(encoding="utf-8")).get("complete") or {}
        shown = board().get("complete") or {}
        tile = (head().get("trajectories") or {}).get("complete") or {}
        check("426: the command line marks them, the file keeps the time, and the board, trajectories show and the "
              "project page's tile answer it",
              code == 0 and done.get("changes") == ["Trajectories marked complete."] and held.get("at")
              and shown.get("at") == held["at"] and tile.get("at") == held["at"]
              and (done.get("complete") or {}).get("at") == held["at"],
              [code, done.get("changes"), done.get("complete"), held, shown, tile, sorted(head())])
        after = tree(root)
        code, again = answer(root, "trajectories", "apply", "--ops", lone, "--note", "Mark it again", "--tool", "Claude Code")
        check("426: marking again changes nothing and keeps the first time",
              code == 0 and not again.get("changes") and tree(root) == after
              and json.loads(tjfile.read_text(encoding="utf-8"))["complete"] == held, again)
        changes = answer(root, "agents", "changes")[1]
        runs = [r.get("run") for r in (changes.get("runs") or changes.get("changes") or []) if r.get("run")]
        run_id = runs[0] if runs else "r1"
        code_u, text_u, err_u = run(root, "agents", "undo-run", run_id, "--note", "Not yet")
        check("426: the agent's run, undone by agents undo-run, puts every file back byte for byte",
              code_u == 0 and tree(root) == before and "complete" not in json.loads(tjfile.read_text(encoding="utf-8")),
              [code_u, text_u, err_u, sorted(k for k in set(before) | set(tree(root)) if before.get(k) != tree(root).get(k))])

        # ── D. the route: set and clear, each one step of Undo, byte for byte; MCP marks and reopens
        start = tree(root)
        marked = ops({"op": "complete"}, step=True)
        mid = tree(root)
        cleared = ops({"op": "reopen"}, step=True)
        end = tree(root)
        check("426: the route marks and reopens, each one step of the screen's Undo",
              (marked.get("complete") or {}).get("at") and cleared.get("complete") is None
              and cleared.get("steps") == {"undo": True, "redo": False} and mid != start
              and "complete" not in json.loads(tjfile.read_text(encoding="utf-8")),
              [marked.get("complete"), cleared.get("complete"), cleared.get("steps")])
        back = call("/api/trajectories-undo", {"workbook": str(book)})
        check("426: Undo puts the mark back byte for byte, and Undo again takes it off byte for byte",
              (back.get("complete") or {}).get("at") and tree(root) == mid, back.get("complete"))
        call("/api/trajectories-undo", {"workbook": str(book)})
        check("426: and the file is as it was before the mark", tree(root) == start, sorted(k for k in set(start) | set(tree(root)) if start.get(k) != tree(root).get(k)))
        again = ops({"op": "reopen"})
        check("426: reopening Trajectories not marked changes nothing", not again.get("changes") and tree(root) == start,
              again.get("changes"))
        r_mark = mcp.call(mcp.by_name["trajectories_apply"], {"operations": [{"op": "complete"}], "request": "Mark them"})
        marked_now = board().get("complete") or {}
        r_open = mcp.call(mcp.by_name["trajectories_apply"], {"operations": [{"op": "reopen"}], "request": "Open them"})
        check("426: MCP's trajectories_apply marks them complete and reopens them",
              not r_mark.get("isError") and marked_now.get("at") and not r_open.get("isError")
              and board().get("complete") is None, [r_mark, r_open])

        # a marked board's complete writes nothing and is not refused, even with a participant unplaced since
        ops({"op": "complete"})
        ops({"op": "place", "participant": people[0], "column": None})
        stood = tree(root)
        again_marked = refused({"workbook": str(book), "ops": [{"op": "complete"}]})
        check("426: complete on a board already marked writes nothing and is not refused",
              again_marked == "answered" and tree(root) == stood
              and (board().get("complete") or {}).get("at"), again_marked)

        # ── E. the page and its catalogue
        static = Path(__file__).resolve().parents[2] / "apps" / "idiograph" / "static"
        js = (static / "trajectories.js").read_text(encoding="utf-8")
        html = (static / "idiograph.html").read_text(encoding="utf-8")
        cat = json.loads((static / "i18n" / "en" / "trajectories.json").read_text(encoding="utf-8"))
        check("426: the page holds Mark Trajectories complete in the toolbar and sends the ops, and the catalogue has its words",
              'id="tj-done"' in html and "op: mark ? 'complete' : 'reopen'" in js
              and cat.get("trajectories.done_mark") == "Mark Trajectories complete"
              and cat.get("trajectories.done_reopen") == "Reopen Trajectories", "")
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept
