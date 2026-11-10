"""Area 314: several actions waiting for his yes answered together (holdbatchA, Adam's option A of 1 November 2026).

Adam, 1 November, after ten board deletes on one participant came to Review one at a time, each approved delete
refused the next once as changed (about 37 clicks): the card for several answers the ticked ones in one step. On an
invented copy of the demo: ten held deletes on one participant approved in one call, all done and none counted as
changed by the one before; a hold whose board another window changed since refused with its reason while the rest
go through; a list declined, the boards staying; a hold not in the list still waiting, and approved alone after
the others without being called changed; a single Approve after another the same; and an agent reading each
one's outcome with `hold show` of several ids and MCP's `hold_show` with ids, no command or tool answering one."""
from __future__ import annotations

import json
from pathlib import Path

from .support import check
from . import support
from .a276_agent_holds import make_project

ASKED = "Clear out the boards I tried and keep Board 1."


def test_holds_together(scratch: Path):
    print("\n314. Several actions waiting answered together: ten deletes on one participant approved in one call, "
          "a board changed elsewhere refused with its reason while the rest go through, a list declined, the "
          "rows not ticked still waiting, and agents reading each outcome (1 November)")
    import cli
    import holds
    import idiograph_cli
    import idiograph_routes as routes
    import mcp_server
    import server as server_mod
    import themes

    root = scratch / "holds-314" / "Dogs"
    make_project(root)
    config_file = scratch / "holds-314" / "config.json"
    config = {"projects": [{"root": str(root)}], "interviewer": "Adam", "corpus": "", "gravity_reference": "",
              "corpus_exclude": []}
    config_file.write_text(json.dumps(config), encoding="utf-8")
    kept = (holds.RUN_AT_ONCE, server_mod.CONFIG_PATH)

    def run(*args):
        return cli.run(["--config", str(config_file), "--root", str(root), *args])

    def answer(*args):
        code, out, err = run("--json", *args)
        return code, (support.plain(json.loads(out)) if out.strip() else {}), err

    def ask_delete(case: str, name: str) -> str:
        code, got, err = answer("board", "delete", case, name, "--note", ASKED, "--tool", "Claude Code")
        return (got.get("held") or {}).get("id") or f"refused: {err[:120]}"

    def names(case: str) -> list:
        data = themes.load(root / case / f"{case} - EN & ES.xlsx")
        return sorted((b["name"] for b in themes.boards_of(data)), key=lambda x: int(x.split()[-1]))

    def in_app(body: dict) -> dict:
        server_mod.CONFIG_PATH = config_file
        try:
            return routes.api_holds(body)
        finally:
            server_mod.CONFIG_PATH = kept[1]

    def listed(ids) -> list:
        return [{"root": str(root), "id": i} for i in ids]

    try:
        # boards of his to clear: Board 2 to Board 11 on Juno, Board 2 and 3 on Rowan and Mabel, made at once
        holds.RUN_AT_ONCE = True
        made = [run("board", "duplicate", "Juno", "Board 1", "--name", f"Board {n}", "--note", "Another try")
                for n in range(2, 12)]
        made += [run("board", "duplicate", case, "Board 1", "--name", f"Board {n}", "--note", "Another try")
                 for case, last in (("Rowan", 3), ("Mabel", 4)) for n in range(2, last + 1)]
        run("board", "canvas", "Juno", "Board 1", "--note", "Back to Board 1")
        holds.RUN_AT_ONCE = None
        check("314: the fixture's boards are made", all(c == 0 for c, _o, _e in made) and len(names("Juno")) == 11,
              str([e for _c, _o, e in made if _c]))

        # 1. ten deletes on one participant, held one by one as the agent asks, approved in one call
        ten = [ask_delete("Juno", f"Board {n}") for n in range(2, 12)]
        check("314: each of the ten deletes waits for his yes", all(i.startswith("h") for i in ten), str(ten))
        code, rep, err = answer("transcript", "replace", "--all", "--find", "dog", "--with", "hound", "--note",
                                "Say hound for dog", "--tool", "Claude Code")
        rid = (rep.get("held") or {}).get("id")
        check("314: a replace across every participant waits too, in the agent's own words",
              bool(rid) and "“dog” with “hound”" in rep["held"]["question"], err or json.dumps(rep)[:200])
        got = in_app({"op": "approve", "holds": listed(ten)})
        outcomes = [o["outcome"] for o in got["outcomes"]]
        check("314: ten deletes on one participant approved in one call are all done, in order, none called changed",
              outcomes == ["approved"] * 10 and [o["id"] for o in got["outcomes"]] == ten and got["done"] == 10
              and names("Juno") == ["Board 1"], json.dumps([outcomes, names("Juno")]))
        check("314: each done one's row has its words without Done. before them",
              all(o["hold"]["said"].startswith("Board ") and "is deleted" in o["hold"]["said"] for o in got["outcomes"]),
              json.dumps(got["outcomes"][0]["hold"])[:300])

        rep_now = in_app({"op": "approve", "holds": listed([rid])})["outcomes"][0]
        check("314: a replace across every participant, waiting while ten deletes were approved, is never called changed",
              rep_now["outcome"] == "approved", json.dumps(rep_now)[:300])

        # 2. a hold whose board another window changed since is refused with its reason, the rest go through
        r2, m2, m3, m4 = (ask_delete("Rowan", "Board 2"), ask_delete("Mabel", "Board 2"),
                          ask_delete("Mabel", "Board 3"), ask_delete("Mabel", "Board 4"))
        code, rep2, err = answer("transcript", "replace", "--all", "--find", "hound", "--with", "dog", "--note",
                                 "Say dog again", "--tool", "Claude Code")
        rid2 = (rep2.get("held") or {}).get("id")
        holds.RUN_AT_ONCE = True
        run("board", "note", "Rowan", "Board 3", "A note made in another window", "--note", "Note it")
        holds.RUN_AT_ONCE = None
        got = in_app({"op": "approve", "holds": listed([m2, r2, m3])})
        by = {o["id"]: o for o in got["outcomes"]}
        check("314: a board changed elsewhere is refused with its reason, nothing done, still waiting, while the rest "
              "go through",
              [o["id"] for o in got["outcomes"]] == [m2, r2, m3]
              and by[m2]["outcome"] == "approved" and by[m3]["outcome"] == "approved" and by[r2]["outcome"] == "changed"
              and by[r2]["reason"].startswith("Rowan's boards changed since Claude Code asked") and by[r2]["hold"]["status"] == "waiting"
              and names("Rowan") == ["Board 1", "Board 2", "Board 3"] and got["done"] == 2,
              json.dumps([[o["id"], o["outcome"], o.get("reason")] for o in got["outcomes"]]))

        looked2 = in_app({"op": "check", "holds": listed([rid2])})["checks"][0]
        check("314: a replace waiting through his deletes on Mabel and a change on Rowan's boards elsewhere names only Rowan's",
              looked2["changed"] is True and looked2["hold"]["changed_what"] == "Rowan's boards",
              json.dumps(looked2["hold"].get("changed_what")))
        in_app({"op": "decline", "holds": listed([rid2])})

        # 3. the row not ticked still waits, and approved alone afterwards it is not called changed
        waiting = {h["id"] for h in in_app({"op": "list"})["holds"]}
        check("314: the actions not in the list still wait", m4 in waiting and r2 in waiting and m2 not in waiting,
              str(sorted(waiting)))
        alone = in_app({"op": "approve", "root": str(root), "id": m4})
        check("314: one left unticked, approved alone after the others on its participant, is done, never changed",
              alone["changed"] is False and alone["hold"]["status"] == "approved" and names("Mabel") == ["Board 1"],
              json.dumps([alone.get("changed"), names("Mabel")]))
        # the one changed elsewhere runs once its row has been looked at again, as a single one does
        looked = in_app({"op": "check", "holds": listed([r2])})
        seen = in_app({"op": "approve", "holds": listed([r2])})
        check("314: the one changed elsewhere, once its row has been looked at again, is approved",
              [c["changed"] for c in looked["checks"]] == [False]
              and [o["outcome"] for o in seen["outcomes"]] == ["approved"] and names("Rowan") == ["Board 1", "Board 3"],
              json.dumps([looked, [o["outcome"] for o in seen["outcomes"]], names("Rowan")])[:400])

        # 4. a single Approve after another on the same participant, as before the card for several
        holds.RUN_AT_ONCE = True
        for n in (4, 5):
            run("board", "duplicate", "Juno", "Board 1", "--name", f"Board {n}", "--note", "Another try")
        holds.RUN_AT_ONCE = None
        a, b = ask_delete("Juno", "Board 4"), ask_delete("Juno", "Board 5")
        first = in_app({"op": "approve", "root": str(root), "id": a})
        second = in_app({"op": "approve", "root": str(root), "id": b})
        check("314: a single Approve after another on the same participant runs at once, never called changed",
              first["changed"] is False and second["changed"] is False and names("Juno") == ["Board 1"],
              json.dumps([first.get("changed"), second.get("changed"), names("Juno")]))

        # 5. a list declined: each declined in order, the boards staying, a History line each, the next not changed
        holds.RUN_AT_ONCE = True
        for n in (6, 7, 8):
            run("board", "duplicate", "Juno", "Board 1", "--name", f"Board {n}", "--note", "Another try")
        holds.RUN_AT_ONCE = None
        d6, d7, d8 = (ask_delete("Juno", f"Board {n}") for n in (6, 7, 8))
        no = in_app({"op": "decline", "holds": listed([d6, d7])})
        check("314: a list declined, each in order, the boards staying",
              [o["outcome"] for o in no["outcomes"]] == ["declined", "declined"]
              and names("Juno") == ["Board 1", "Board 6", "Board 7", "Board 8"],
              json.dumps([names("Juno")] + [o["outcome"] for o in no["outcomes"]]))
        last = in_app({"op": "approve", "holds": listed([d8])})
        check("314: a decline's History line on the participant's boards never makes the next one changed",
              [o["outcome"] for o in last["outcomes"]] == ["approved"] and "Board 8" not in names("Juno"))
        again = in_app({"op": "approve", "holds": listed([d6])})
        check("314: one answered already is passed over with its reason, never run twice",
              again["outcomes"][0]["outcome"] == "answered" and holds.ANSWERED in again["outcomes"][0]["reason"])

        # 6. the route refuses a list that names no action, or a project not the app's
        refused = []
        for body in ({"op": "approve", "holds": []}, {"op": "approve", "holds": [{"root": str(root)}]},
                     {"op": "approve", "holds": [{"root": str(scratch), "id": "h1"}]}):
            try:
                in_app(body)
                refused.append(False)
            except Exception:
                refused.append(True)
        check("314: a list naming no action, or a project not one of the app's, is refused", all(refused), str(refused))

        # 7. an agent reads each one's outcome in one call, and still nothing answers one but the app
        code, shown, err = answer("hold", "show", *ten[:3])
        srv = mcp_server.Server(str(root), config=str(config_file))
        res = srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                      "params": {"name": "hold_show", "arguments": {"ids": [r2, m3]}}}))["result"]
        raw = res["structuredContent"].get("holds") or []
        one = srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                      "params": {"name": "hold_show", "arguments": {"id": r2}}}))["result"]
        check("314: hold show of several ids and MCP's hold_show with ids read each outcome in the order given",
              code == 0 and [v["id"] for v in shown.get("holds") or []] == ten[:3]
              and all(v["status"] == "approved" for v in shown["holds"])
              and [v["id"] for v in raw] == [r2, m3] and all(v["status"] == "approved" for v in raw)
              and one["structuredContent"]["hold"]["id"] == r2, err or json.dumps(res)[:300])
        tools = {t["name"] for t in mcp_server.tools_for("idiograph")}
        check("314: still no command and no tool approves or declines, alone or in a list",
              not any(k[0] == "hold" and k[1] not in (None, "show") for k in idiograph_cli.COMMANDS)
              and not any("approve" in t or "decline" in t for t in tools))
    finally:
        holds.RUN_AT_ONCE, server_mod.CONFIG_PATH = kept
