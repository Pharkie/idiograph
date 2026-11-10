"""Area 276: an agent's action that waits for his yes in the app (holdsbuild, 27 October 2026, Adam's ruling of
Section 13, "build it as drawn", on his words of 26 October: agent actions that delete boards or replace across a
project wait for the yes in the app, with "Dangerously skip permissions" in the AI settings to skip it).

Each op of `holds.HELD`, asked by an agent with the setting off, writes nothing and answers held, its dry run's
lines with it, the JSON through the marking of area 274. An op of the same command that takes nothing off runs at
once. Approve in the app runs the op as the agent asked it, its History naming the agent "approved in the app",
and Decline writes nothing but History's line. With the setting on the op runs at once, History saying "without
asking". The route that answers is the page's own, never an agent's op. A hold whose board changed since says so,
and Approve runs its dry run again first, running nothing when it differs.

The fixture is invented: the demo's three dog owners, copied into a scratch project."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from .support import DEMO_SHIPPED, check
from . import support

ASKED = "Tidy up the boards, keep only the one I am using."


def files_of(root: Path) -> dict:
    """Every file of the project with its contents' hash, the holds file and the locks set aside."""
    out = {}
    for path in sorted(Path(root).rglob("*")):
        if path.is_file() and path.name not in ("idiograph-holds.json", ".idiograph-holds.lock", ".idiograph.lock"):
            out[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def make_project(root: Path) -> None:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    for name in ("Juno", "Rowan", "Mabel"):
        case = root / name
        (case / "Working").mkdir(parents=True)
        shutil.copy2(DEMO_SHIPPED / f"{name} - EN & ES.xlsx", case / f"{name} - EN & ES.xlsx")
        for kind in ("progress", "themes"):
            side = DEMO_SHIPPED / "Working" / f"{name} - EN & ES.{kind}.json"
            if side.exists():
                shutil.copy2(side, case / "Working" / side.name)
    shutil.copy2(DEMO_SHIPPED / "idiograph-gets.json", root / "idiograph-gets.json")
    (root / "idiograph-project.json").write_text(json.dumps({
        "name": "Living with a dog, a scratch copy", "agents": {"allowed": True, "at": "2026-10-27T09:00:00+00:00"}}),
        encoding="utf-8")


def test_agent_holds(scratch: Path):
    print("\n276. An agent's action that waits for his yes in the app: each held op writes nothing and answers "
          "held, Approve runs it and History says so, Decline writes nothing but History's line, Dangerously skip "
          "permissions runs it at once, the route the page's own, a changed board re-run first (27 October)")
    import cli
    import holds
    import idiograph_cli
    import idiograph_routes as routes
    import mcp_server
    import server as server_mod
    import themes

    root = scratch / "holds-276" / "Dogs"
    make_project(root)
    config_file = scratch / "holds-276" / "config.json"
    config = {"projects": [{"root": str(root)}], "interviewer": "Adam", "corpus": "", "gravity_reference": "",
              "corpus_exclude": []}
    config_file.write_text(json.dumps(config), encoding="utf-8")
    kept = (holds.RUN_AT_ONCE, server_mod.CONFIG_PATH)
    holds.RUN_AT_ONCE = None

    def run(*args):
        return cli.run(["--config", str(config_file), "--root", str(root), *args])

    def answer(*args):
        code, out, err = run("--json", *args)
        return code, (support.plain(json.loads(out)) if out.strip() else {}), err

    def ask(*args):
        return answer(*args, "--note", ASKED, "--tool", "Claude Code")

    def spec(name: str, value) -> str:
        path = scratch / "holds-276" / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return str(path)

    def board(case: str) -> dict:
        data = themes.load(root / case / f"{case} - EN & ES.xlsx")
        return {str(b["id"]): b for b in themes.boards_of(data)}

    def in_app(fn, *a):
        server_mod.CONFIG_PATH = config_file
        try:
            return fn(*a)
        finally:
            server_mod.CONFIG_PATH = kept[1]

    try:
        # boards of his to work on: a second board on each of two participants, a revision to restore, a second
        # GETs board, all made at once as before holds
        holds.RUN_AT_ONCE = True
        made = [run("board", "duplicate", "Juno", "Board 1", "--name", "Board 2", "--note", "A second board"),
                run("board", "duplicate", "Rowan", "Board 1", "--name", "Board 2", "--note", "A second board"),
                run("board", "revision", "Rowan", "Board 1", "--note", "Keep this one"),
                run("gets", "duplicate", "Board 1", "--name", "Board 2", "--note", "A second GETs board"),
                run("gets", "revision", "Board 1", "--note", "Keep the GETs")]
        holds.RUN_AT_ONCE = None
        check("276: the fixture's boards and revisions are made", all(c == 0 for c, _o, _e in made),
              str([e for _c, _o, e in made]))
        to = scratch / "holds-276" / "sent"
        to.mkdir(exist_ok=True)

        # 1. each held op, setting off: nothing written, held, its dry run's lines with it
        before = files_of(root)
        asks = {
            "board delete": ask("board", "delete", "Juno", "Board 2"),
            "board restore": ask("board", "restore", "Rowan", "Board 1", "r1"),
            "board apply": ask("board", "apply", "Rowan", "Board 1", "--ops",
                               spec("merge.json", {"operations": [{"op": "merge", "label": "g2", "into": "g1"}]})),
            "gets delete": ask("gets", "delete", "Board 2"),
            "gets restore": ask("gets", "restore", "Board 1", "r1"),
            "gets apply": ask("gets", "apply", "Board 1", "--ops",
                              spec("gmerge.json", {"operations": [{"op": "merge", "label": "G2", "into": "G1"}]})),
            "transcript replace": ask("transcript", "replace", "--all", "--find", "dog", "--with", "hound"),
            "turn trim": ask("turn", "trim", "Mabel", "Initial", "3", "--before"),
            "turn write": ask("turn", "write", "Rowan", "Initial", "7", "--from", spec("turn.json", {"statements": []})),
            "participant rename": ask("participant", "rename", "Mabel", "Maple", "--folder"),
            "project send": ask("project", "send", "--to", str(to)),
        }
        held = {op: got for op, (code, got, _e) in asks.items() if code == 0 and got.get("held", {}).get("status") == "waiting"}
        check("276: each held op with the setting off answers held, waiting, with what it would do from its dry run",
              set(held) == set(asks) and all(g["held"]["would_do"] and g["held"]["op"] == op for op, g in held.items()),
              json.dumps({op: [c, e[:160]] for op, (c, g, e) in asks.items() if op not in held}))
        # what it would do, as Adam's drawing says a delete (holdsfix, 27 October): what goes with its counts,
        # where its copy is kept, and the board that stays the Current board
        import idiograph_cli as icli
        b2 = next(b for b in themes.boards_of(icli.load_board_file(root / "Juno" / "Juno - EN & ES.xlsx"))
                  if b["name"] == "Board 2")
        counts = holds.pets_counts(b2)
        would = held["board delete"]["held"]["would_do"]
        check("276: a delete's hold says the board with its PETs and statements placed, its copy, and the Current board",
              would == [f"Board 2 of Juno, {counts}, is deleted.", "A copy is kept in Juno's Archive folder.",
                        "Board 1 stays the Current board."] and counts.split()[0] != "0" and " PETs and " in counts,
              json.dumps(would))
        check("276: and each wrote nothing in the project, nor sent a file", files_of(root) == before and not any(to.iterdir()))
        listed = holds.load(root)["holds"]
        check("276: the holds are kept in the project's own holds file at its root, with an id each, never in a workbook",
              (root / holds.FILE).is_file() and len({h["id"] for h in listed}) == len(asks), str(len(listed)))

        # the same commands run at once where they take nothing off: one participant's replace, a board apply
        # that only retitles, a send of one participant into the project's folder
        once = [ask("transcript", "replace", "Juno", "--find", "zzqx", "--with", "y"),
                ask("board", "apply", "Rowan", "Board 2", "--ops",
                    spec("retitle.json", {"operations": [{"op": "retitle", "label": "g1", "title": "Mornings"}]})),
                ask("project", "send", "--participant", "Rowan", "--to", str(root))]
        check("276: an op that takes nothing off runs at once, never held",
              all(c == 0 and "held" not in g for c, g, _e in once), str([e for _c, _g, e in once]))
        for leftover in root.glob("*.idiograph"):
            leftover.unlink()

        # 2. an agent asks after its action, on the command line and through MCP, the words marked
        hid = held["board delete"]["held"]["id"]
        code, shown_hold, _ = answer("hold", "show", hid)
        code_all, every, _ = answer("hold")
        srv = mcp_server.Server(str(root), config=str(config_file))
        got = srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                      "params": {"name": "hold_show", "arguments": {"id": hid}}}))["result"]
        raw = got["structuredContent"]["hold"]
        check("276: hold show and hold read a waiting action, and MCP's hold_show its words marked, its id and status plain",
              code == 0 and shown_hold["hold"]["status"] == "waiting" and code_all == 0
              and len(every.get("holds") or []) == len(asks) and raw["status"] == "waiting" and raw["id"] == hid
              and isinstance(raw["question"], dict) and "untrusted_text" in raw["question"], json.dumps(raw)[:300])
        tools = {t["name"] for t in mcp_server.tools_for("idiograph")}
        check("276: no command and no tool approves or declines: hold and hold_show only read",
              {"hold", "hold_show"} <= tools and not any(k[0] == "hold" and k[1] not in (None, "show")
                                                        for k in idiograph_cli.COMMANDS)
              and not any("approve" in t or "decline" in t for t in tools))

        # 3. Approve runs it as the agent asked, History naming the agent and "approved in the app"
        # as the page does: the card's look first, which takes in the retitle made on Rowan since, then Approve
        rid = held["board restore"]["held"]["id"]
        in_app(routes.api_holds, {"op": "check", "root": str(root), "id": rid})
        done = in_app(routes.api_holds, {"op": "approve", "root": str(root), "id": rid})
        history = themes.history_of(board("Rowan")["v1"])
        stamped = [r for r in history if (r.get("made") or {}).get("tool") == f"Claude Code, {holds.APPROVED}"]
        check("276: Approve runs the restore, the board kept first in History naming the agent, approved in the app",
              done["hold"]["status"] == "approved" and done["hold"]["line"].startswith("Done.") and stamped,
              json.dumps([done["hold"]["status"], done.get("changed")] + [r.get("made") for r in history])[:300])
        in_app(routes.api_holds, {"op": "check", "root": str(root), "id": hid})
        dl = in_app(routes.api_holds, {"op": "approve", "root": str(root), "id": hid})
        archived = list((root / "Juno" / "_Archive").glob("*Board 2*.json"))
        check("276: Approve runs the delete, the board gone and its copy in _Archive, and the agent reads it approved",
              dl["hold"]["status"] == "approved" and len(board("Juno")) == 1 and archived
              and answer("hold", "show", hid)[1]["hold"]["status"] == "approved", json.dumps(dl)[:300])
        try:
            in_app(routes.api_holds, {"op": "approve", "root": str(root), "id": hid})
            again = False
        except Exception as exc:
            again = holds.ANSWERED in str(exc)
        check("276: an action answered already is refused, never run twice", again)

        # 4. Decline writes nothing but History's line
        gid = held["gets delete"]["held"]["id"]
        before = files_of(root)
        no = in_app(routes.api_holds, {"op": "decline", "root": str(root), "id": gid})
        after = files_of(root)
        gets_file = json.loads((root / "idiograph-gets.json").read_text(encoding="utf-8"))
        b2 = next(b for b in gets_file["boards"] if b["name"] == "Board 2")
        check("276: Decline writes nothing but History's line: the GETs board stays, a revision named for the decline",
              no["hold"]["status"] == "declined" and no["hold"]["line"].startswith("Declined.")
              and {k for k in after if after[k] != before.get(k)} | {k for k in before if k not in after} == {"idiograph-gets.json"}
              and any(str(r.get("name", "")).startswith("Declined in the app") for r in themes.history_of(b2)),
              json.dumps([r.get("name") for r in themes.history_of(b2)]))
        before = files_of(root)
        in_app(routes.api_holds, {"op": "decline", "root": str(root), "id": held["transcript replace"]["held"]["id"]})
        check("276: declining a replace across every participant writes nothing at all", files_of(root) == before)

        # 5. a hold whose board changed since says so, and Approve runs nothing until it is seen
        code, again_held, _ = ask("board", "delete", "Rowan", "Board 2")
        sid = again_held["held"]["id"]
        holds.RUN_AT_ONCE = True
        run("board", "note", "Rowan", "Board 2", "A note made since", "--note", "Note it")
        holds.RUN_AT_ONCE = None
        stale = in_app(routes.api_holds, {"op": "approve", "root": str(root), "id": sid})
        still = "v2" in board("Rowan")
        looked = in_app(routes.api_holds, {"op": "check", "root": str(root), "id": sid})
        ran = in_app(routes.api_holds, {"op": "approve", "root": str(root), "id": sid})
        check("276: a board changed since the hold: Approve re-runs the dry run, runs nothing and says it changed, and "
              "once the card has the new dry run Approve runs it",
              stale["changed"] is True and stale["hold"]["status"] == "waiting" and still
              and looked["changed"] is False and ran["changed"] is False and "v2" not in board("Rowan"),
              json.dumps([stale.get("changed"), looked.get("changed"), ran.get("changed")]))

        # 6. Dangerously skip permissions on: the op runs at once, History saying "without asking"
        config_file.write_text(json.dumps(dict(config, skip_permissions=True)), encoding="utf-8")
        code, at_once, err = ask("board", "restore", "Rowan", "Board 1", "r1")
        history = themes.history_of(board("Rowan")["v1"])
        check("276: with Dangerously skip permissions on, the restore runs at once, its History saying without asking",
              code == 0 and "held" not in at_once
              and any((r.get("made") or {}).get("tool") == f"Claude Code, {holds.WITHOUT}" for r in history), err)
        config_file.write_text(json.dumps(config), encoding="utf-8")
        server_mod.CONFIG_PATH = config_file
        try:
            saved = server_mod.api_settings({"skip_permissions": True})
            off = server_mod.api_settings({"skip_permissions": "yes"})
        finally:
            server_mod.CONFIG_PATH = kept[1]
        check("276: the setting saves from Settings, off by default and on only when the page sends it ticked",
              saved["config"].get("skip_permissions") is True and off["config"].get("skip_permissions") is False
              and routes.OWN_DEFAULTS.get("skip_permissions") is False)
        config_file.write_text(json.dumps(config), encoding="utf-8")

        # 7. the route that answers is the page's own: a POST from the server's own page alone
        check("276: /api/holds answers a POST from the server's own page alone, as the page's other write routes",
              "/api/holds" in server_mod.POST_ONLY and "/api/holds" in server_mod.OWN_PAGE
              and not server_mod.own_origin({"Host": "127.0.0.1:8765", "Origin": "http://elsewhere.example"},
                                            ("127.0.0.1", 8765)))
        try:
            in_app(routes.api_holds, {"op": "approve", "root": str(scratch), "id": "h1"})
            outside = False
        except Exception as exc:
            outside = "not one of Idiograph's" in str(exc)
        check("276: an action is answered only in one of the app's projects", outside)
        waiting = in_app(routes.api_holds, {"op": "list"})["holds"]
        check("276: the page's list holds every action still waiting, each with its project and its words",
              waiting and all(w["root"] == str(root) and w["status"] == "waiting" and w["waiting"] for w in waiting)
              and len(waiting) == len([h for h in holds.load(root)["holds"] if h["status"] == "waiting"]))
    finally:
        holds.RUN_AT_ONCE, server_mod.CONFIG_PATH = kept
