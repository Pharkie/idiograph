"""Area 389: Project history's By an agent and Home's line of agents' changes (agentreview2, 13 November 2026, Adam
by dialog on agentreview's drawings: "C, with A's Home line").

What is checked, on an invented project about learning to sail late, Dara, Ezra and Fen. Home's count of the changes
agents made since he last looked, read from the store's tally and never from the record, a project with no record
answering none, and its time on a record of 5,000 changes. By an agent's read through `/api/agent-changes`, as
`agents changes` reads the record: the runs newest first, each with its agent, count, request and New, each change
with its line and where, the change he edited since saying so with which files and when, and the run's Undo the
changes that can be undone. The first read marking every change seen, so New and Home's line go, kept in the
project's store across a restart. Undo of one change through the page's route putting back its files byte for byte
as they were before it, as `agents undo-change` does, and Undo of a change he edited since refused with its lines,
nothing written.

The fixture is invented: a scratch project, its agents' changes made through the command line as agents make them,
and his own edit through the app's own call, outside the record."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path

from .support import check

ASKED = "Give each participant a label and Ezra a sketch board."


def files_of(root: Path) -> dict:
    out = {}
    for p in sorted(Path(root).rglob("*")):
        rel = p.relative_to(root).as_posix()
        if p.is_file() and p.suffix in (".xlsx", ".json") and not rel.startswith(".idiograph-restore") \
                and "_Archive" not in rel and p.name != "idiograph-history.json":
            out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def test_agent_review(scratch: Path):
    print("\n389. Project history's By an agent and Home's line: the count from the tally alone, the runs with their "
          "changes, New and what can be undone, the first read marking them seen, Undo of one change and its "
          "refusal over his own edit (13 November)")
    import agent_changes
    import cli
    import idiograph_cli as icli
    import idiograph_routes as routes
    import server as server_mod
    from .a351_team_board import make_workbook

    base = scratch / "agent-review-389"
    shutil.rmtree(base, ignore_errors=True)
    root, bare = base / "Learning to sail", base / "Rowing"
    root.mkdir(parents=True)
    bare.mkdir(parents=True)
    for one, name in ((root, "Learning to sail"), (bare, "Rowing")):
        (one / server_mod.PROJECT_FILE).write_text(json.dumps({
            "name": name, "research_question": "How do adults come to it late?",
            "agents": {"allowed": True, "at": "2026-11-13T07:00:00+00:00"}}), encoding="utf-8")
    for n, who in enumerate(("Dara", "Ezra", "Fen"), 1):
        make_workbook(root, f"P{n} - {who}", who)
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}, {"root": str(bare)}],
                                       "interviewer": "Interviewer", "corpus": "", "gravity_reference": "",
                                       "corpus_exclude": []}), encoding="utf-8")
    kept = (agent_changes.NOW, agent_changes.read, server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE,
            server_mod.STATE_MEMORY)
    clock = {"at": datetime(2026, 11, 13, 8, 12).astimezone()}
    agent_changes.NOW = lambda: clock["at"]

    def ask(*args, tool="Claude Code"):
        code, out, err = cli.run(["--config", str(config_file), "--root", str(root), "--json", *args, "--tool", tool,
                                  "--note", ASKED])
        return code, err

    def in_app(route, body):
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, None
        server_mod.STATE_MEMORY = {"recent": []}
        try:
            return route(body)
        finally:
            server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept[2], kept[3], kept[4]

    try:
        pid = routes.project_id(root)
        # ── 1. two runs of agents' changes, and his own edit of Ezra's board after the first
        codes = [ask("participant", "set", "Dara", "--label", "Late starter")[0]]
        clock["at"] += timedelta(minutes=5)
        codes.append(ask("board", "fresh", "Ezra", "--name", "Sketch")[0])
        clock["at"] += timedelta(minutes=5)
        codes.append(ask("board", "note", "Ezra", "Sketch", "A first try")[0])
        clock["at"] += timedelta(minutes=40)
        codes.append(ask("board", "fresh", "Fen", "--name", "Sketch", tool="Codex")[0])
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, str(root)
        try:
            p = icli.Project(root, False)
            his = argparse.Namespace(command="board", act="note", json=True, project=None, root=None, demo=False,
                                     config=None, dry_run=False, note="his own", tool="", case="Ezra", board="Sketch",
                                     text="My own note", timepoint=None, lpets=None)
            icli.run_scoped(icli.COMMANDS[("board", "note")], p, his)
        finally:
            server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = kept[2], kept[3]
        check("389: four changes by agents in two runs, and his own edit through the app outside the record",
              codes == [0, 0, 0, 0] and len(agent_changes.read(root)) == 4, str(codes))

        # ── 2. Home's count, from the tally alone
        unseen = in_app(routes.api_agent_unseen, {})
        check("389: Home's line counts the changes agents made since he last looked, a project with no record none",
              unseen == {"unseen": {pid: 4}}, json.dumps(unseen))

        def broken(_root):
            raise AssertionError("the record was read")
        agent_changes.read = broken
        try:
            without = in_app(routes.api_agent_unseen, {})
        finally:
            agent_changes.read = kept[1]
        check("389: Home's count never reads the record, only the store's tally and what he has seen",
              without == {"unseen": {pid: 4}}, json.dumps(without))

        # ── 3. By an agent: the runs, each change's line and state, and what each run's Undo undoes
        got = in_app(routes.api_agent_changes, {"root": pid, "mark": True})
        runs = {r["id"]: r for r in got.get("runs", [])}
        first = runs.get("r1", {})
        by_id = {c["id"]: c for c in first.get("changes", [])}
        check("389: By an agent answers the runs newest first, each with its agent, count, request and New, and the "
              "count of changes new since he last looked",
              [r["id"] for r in got.get("runs", [])] == ["r2", "r1"] and runs["r2"]["agent"] == "Codex"
              and first.get("count") == 3 and first.get("request") == ASKED and all(r["new"] for r in got["runs"])
              and got.get("new") == 4 and got.get("new_runs") == 2 and got.get("total") == 4, json.dumps(got)[:900])
        check("389: each change is a line of what and where, and the change he edited since says so, with which "
              "files and when, the run's Undo taking the others alone",
              by_id.get("c3", {}).get("state") == "yours" and by_id["c3"].get("what") == "Ezra's boards"
              and by_id["c3"].get("changed_at") and by_id.get("c2", {}).get("state") == "yours"
              and by_id.get("c1", {}).get("state") == "ok" and by_id["c1"]["line"] == "Changed a participant's details"
              and by_id["c3"]["where"] == "Ezra, PETs" and first.get("undo") == "changes"
              and first.get("undo_ids") == ["c1"] and first.get("whole") is False
              and runs["r2"].get("undo_ids") == ["c4"] and runs["r2"].get("whole") is True, json.dumps(first)[:900])

        # ── 4. the first read marked them seen: New and Home's line go, kept in the store
        again = in_app(routes.api_agent_changes, {"root": pid})
        check("389: once By an agent has been read, no run is New and Home's line is gone, the seen mark kept in "
              "the project's store", not any(r["new"] for r in again["runs"]) and again.get("new") == 0
              and in_app(routes.api_agent_unseen, {}) == {"unseen": {}}
              and (root / agent_changes.STORE / agent_changes.SEEN).is_file(), json.dumps(again)[:400])

        # ── 5. Undo of one change, as agents undo-change does it, and its refusal over his own edit
        before = files_of(root)
        refused = in_app(routes.api_agent_changes, {"root": pid, "op": "undo", "ids": ["c3"]})
        check("389: Undo of a change he edited since is refused with its lines, naming the files, nothing written",
              refused.get("refused") and any("Ezra's boards" in x for x in refused["refused"])
              and files_of(root) == before, json.dumps(refused))
        fen = next((root / "P3 - Fen" / "Working").glob("*.themes.json"))
        done = in_app(routes.api_agent_changes, {"root": pid, "op": "undo", "ids": ["c4"]})
        after = in_app(routes.api_agent_changes, {"root": pid})
        r2 = {r["id"]: r for r in after["runs"]}["r2"]
        check("389: Undo of one change takes away the board it made, kept first, the rest as it was, and the change "
              "reads undone with no Undo left on its run",
              done.get("done", {}).get("changes") == ["c4"] and not fen.exists()
              and {k: v for k, v in files_of(root).items() if "Fen" not in k}
              == {k: v for k, v in before.items() if "Fen" not in k}
              and r2["changes"][0]["state"] == "undone" and r2.get("undo") is None, json.dumps([done, r2])[:900])

        # ── 6. Home's count on a record of 5,000 changes: two small files, timed
        big = base / "Big"
        shutil.copytree(bare, big)
        lines = "".join(json.dumps({"id": f"c{n}", "at": "2026-11-13T08:00:00+00:00", "run": "r1", "via": "mcp",
                                    "agent": "Claude Code", "request": ASKED, "op": "board apply",
                                    "target": {"case": "Dara"}, "what_changed": "Changed Dara's boards.",
                                    "files": 1}) + "\n" for n in range(1, 5001))
        (big / agent_changes.FILE).write_text(lines, encoding="utf-8")
        agent_changes.unseen(big)
        start = time.perf_counter()
        for _ in range(20):
            n = agent_changes.unseen(big)
        took = (time.perf_counter() - start) / 20 * 1000
        check("389: Home's count on a project with 5,000 recorded changes reads its tally alone, under 20 ms a "
              "project", n == 5000 and took < 20, f"{took:.3f} ms a project")
    finally:
        agent_changes.NOW, agent_changes.read = kept[0], kept[1]
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept[2], kept[3], kept[4]
