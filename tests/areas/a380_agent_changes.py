"""Area 380: the record of agents' changes and their runs' restore points (noholds, 13 November 2026, Adam: the holds
were "approvals theatre", so agents act at once, with "a safety net if they don't ... review afterwards", and by
dialog the actions undo cannot reach are the app's alone, and a restore point for each agent run).

What is checked, on an invented project about keeping bees in a city, Ada, Bryn and Cass. An agent's write kept once
in the project's change record with its run, op, target and a line of what changed, and never a participant's words.
A dry run and a read recording nothing. Two writes of one tool within 30 minutes one run, another tool's its own,
`--run` its own, and a write after 30 minutes a new run. A run undone putting every file it changed back byte for
byte as it was before its first write and taking a board it made away, its undo a run of its own that undoes it in
its turn, and a second undo refused. The undo refused whole, nothing written, naming the file when a later change
would be lost, and when the run renamed a participant's folder. A restore point copying only what changed since the
last. The ops only the app does refused with nothing written and logged as app_only, their dry runs answering. An
MCP connection one run and a second its own. And the actions that waited before approvals were removed dropped as
the project opens, their count noted once in the agent log. One change undone alone (agentreview2, 13 November):
each change keeping its files before and after it,  putting them back byte for byte, the
change before it kept, a second undo refused, a change whose file he changed since refused whole with nothing
written, and MCP's agent_undo_change doing the same."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from .support import check
from . import support

ASKED = "Tidy the labels before my supervision."


def digest(root: Path) -> dict:
    """Every workbook and JSON file of the project by its contents, the record and the store set aside."""
    out = {}
    for p in sorted(Path(root).rglob("*")):
        rel = p.relative_to(root).as_posix()
        if p.is_file() and not rel.startswith(".idiograph-restore") and p.suffix in (".xlsx", ".json") \
                and "_Archive" not in rel and p.name != "idiograph-history.json":
            out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def test_agent_changes(scratch: Path):
    print("\n380. The record of agents' changes and each run's restore point: a write kept once with its run, a dry "
          "run and a read none, runs by tool, --run and 30 minutes, a run undone whole and refused over a later "
          "change, the ops only the app does refused, an MCP connection one run, the old holds dropped (13 November)")
    import agent_changes
    import agent_log
    import cli
    import mcp_server
    import server as server_mod
    from .a351_team_board import make_workbook

    base = scratch / "agent-changes-380"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Bees in the city"
    root.mkdir(parents=True)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Bees in the city", "research_question": "How do people keep bees on a city roof?",
        "agents": {"allowed": True, "at": "2026-11-13T09:00:00+00:00"}}), encoding="utf-8")
    for n, who in enumerate(("Ada", "Bryn", "Cass"), 1):
        make_workbook(root, f"P{n} - {who}", who)
    # an action that waited before approvals were removed, and one answered
    (root / "idiograph-holds.json").write_text(json.dumps({"holds": [{"id": "h1", "status": "waiting"},
                                                                     {"id": "h2", "status": "approved"}]}),
                                               encoding="utf-8")
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Interviewer",
                                       "corpus": "", "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    log = base / "agent-log.json"
    kept = (agent_changes.ALL_OPS, agent_changes.NOW, os.environ.get(agent_log.PLACE), server_mod.CONFIG_PATH)
    agent_changes.ALL_OPS = None
    os.environ[agent_log.PLACE] = str(log)
    record = root / agent_changes.FILE
    store = root / agent_changes.STORE
    clock = {"at": datetime(2026, 11, 13, 10, 0).astimezone()}
    agent_changes.NOW = lambda: clock["at"]

    def run(*args, tool="Claude Code"):
        words = ["--config", str(config_file), "--root", str(root), "--json", *args]
        if tool is not None:
            words += ["--tool", tool]
        code, out, err = cli.run(words)
        return code, (support.plain(json.loads(out)) if out.strip() else {}), err + (out if code else "")

    def ask(*args, tool="Claude Code"):
        return run(*args, "--note", ASKED, tool=tool)

    def lines() -> list:
        return agent_changes.read(root)

    def runs() -> dict:
        return {r["id"]: r for r in agent_changes.all_runs(root)}

    try:
        # ── 1. the holds of before dropped as the project opens, counted once in the agent log
        run("cases", tool=None)
        run("cases", tool=None)
        agent_log.flush()
        notes = [e for e in agent_log.load(log)["entries"] if e.get("code") == "cleared"]
        check("380: the actions that waited are dropped as the project first opens, never applied, and their count "
              "said once in the agent log", not (root / "idiograph-holds.json").exists() and len(notes) == 1
              and notes[0]["line"] == "1 action that waited was cleared when approvals were removed."
              and notes[0]["project"] == "Bees in the city", json.dumps(notes))

        # ── 2. a dry run and a read keep nothing
        before = digest(root)
        run("participant", "set", "Ada", "--label", "First summer", "--note", ASKED, "--dry-run")
        run("agents", "changes", tool=None)
        check("380: a dry run and a read keep no record and no restore point", not record.exists()
              and not (store / "runs").exists() and digest(root) == before)

        # ── 3. writes: kept once each, a run by tool, never a participant's words
        start = digest(root)
        code1, got1, err1 = ask("participant", "set", "Ada", "--label", "First summer")
        clock["at"] += timedelta(minutes=10)
        code2, got2, err2 = ask("turn", "edit", "Ada", "Initial", "3", "--text",
                                "Quiet, a hum you feel through the glove more than you hear it.")
        clock["at"] += timedelta(minutes=10)
        code3, got3, err3 = ask("board", "fresh", "Ada", "--name", "Sketch")
        after_r1 = digest(root)
        got = lines()
        first = runs().get("r1") or {}
        check("380: three writes of one tool within 30 minutes are three lines of one run, r1, each with its op, its "
              "target by name and a line of what changed by the project's files",
              code1 == code2 == code3 == 0 and [e["run"] for e in got] == ["r1"] * 3
              and [e["op"] for e in got] == ["participant set", "turn edit", "board fresh"]
              and got[0]["target"] == {"case": "Ada"} and got[1]["target"].get("sheet") == "Initial"
              and str(got[1]["target"].get("row")) == "3" and "Made Ada's boards" in got[2]["what_changed"]
              and got[1]["what_changed"].startswith("Changed Ada's transcript") and got[0]["agent"] == "Claude Code"
              and got[0]["request"] == ASKED and first.get("changes") == 3, err1 + err2 + err3 + json.dumps(got)[:900])
        check("380: the record never holds a participant's words, the passage's new words nowhere in it",
              "a hum you feel" not in record.read_text(encoding="utf-8"))
        check("380: each line says how to undo it, the run's undo and the op's own where it has one",
              all(e["undo_with"]["command"] == "idiograph agents undo-run r1" for e in got), json.dumps(got)[:600])

        # another tool, --run, and a gap of over 30 minutes each start a run of their own
        clock["at"] += timedelta(minutes=5)
        ask("length", "20", tool="Codex")
        ask("length", "21", "--run", "tidy-session")
        clock["at"] += timedelta(minutes=31)
        ask("length", "22")
        got = lines()
        check("380: another tool's write is a run of its own, a --run its own, and a write over 30 minutes after the "
              "tool's last a new run", [e["run"] for e in got[3:]] == ["r2", "r3", "r4"]
              and runs()["r2"]["agent"] == "Codex", json.dumps([e["run"] for e in got]))

        # ── 4. a restore point copies only what changed since the last
        objects = len(list((store / "objects").iterdir()))
        files = len(agent_changes.tracked(root))
        check("380: the first restore point kept each file once, and the later ones only the files changed since",
              objects < 2 * files and objects >= files, f"{objects} copies for {files} files")

        # ── 5. a run undone: its dry run writes nothing, then every file back and the board it made taken away
        now_files = digest(root)
        code, dry, err = run("agents", "undo-run", "r4", "--dry-run", "--note", "Undo the last length")
        check("380: undo-run's dry run says what it would put back and writes nothing",
              code == 0 and dry.get("put_back") == 1 and digest(root) == now_files, err + json.dumps(dry))
        # r1's files changed since by r2 to r4? The project file did, so its undo is refused, naming it
        code, _x, err = run("agents", "undo-run", "r1", "--note", "Undo the tidy")
        check("380: a run whose file changed after it is refused whole, naming the file, nothing written",
              code != 0 and "the project's settings, changed after the run's last change" in err
              and digest(root) == now_files, err)
        for rid in ("r4", "r3", "r2"):
            run("agents", "undo-run", rid, "--note", "Undo the lengths")
        code, undone, err = run("agents", "undo-run", "r1", "--note", "Undo the tidy")
        check("380: once the later runs are undone, r1 is undone: every file it changed back byte for byte as it was "
              "before its first write, and the board it made taken away",
              code == 0 and digest(root) == start and undone.get("taken_away") == 2,
              err + json.dumps(undone)[:400] + json.dumps(sorted(k for k in set(start) | set(digest(root))
                                                                 if start.get(k) != digest(root).get(k))))
        again = run("agents", "undo-run", "r1", "--note", "Undo the tidy")
        undo_id = undone.get("undo_run", "")
        check("380: a run undone is marked so, the undo a run of its own and a line of the record, and a second undo "
              "of the run refused", runs()["r1"].get("undone", {}).get("run") == undo_id
              and runs()[undo_id].get("undoes") == "r1" and lines()[-1]["op"] == "agents undo-run"
              and again[0] != 0 and "undone already" in again[2], again[2])
        code, _x, err = run("agents", "undo-run", undo_id, "--note", "Put the tidy back")
        check("380: the undo undone in its turn puts the run's changes back, the board it made among them",
              code == 0 and digest(root) == after_r1, err)

        # ── 6. a later change of his own between the run's writes refuses its undo
        clock["at"] += timedelta(hours=2)
        ask("participant", "set", "Bryn", "--label", "The roof keeper")
        rid = lines()[-1]["run"]
        code, _x, err = cli.run(["--config", str(config_file), "--root", str(root), "participant", "set", "Bryn",
                                 "--label", "Roof keeper", "--note", "his own", "--tool", "Idiograph by hand"])
        clock["at"] += timedelta(minutes=1)
        ask("participant", "set", "Cass", "--label", "New to it")
        code, _x, err = run("agents", "undo-run", rid, "--note", "Undo it")
        check("380: a file changed by someone else between the run's writes refuses the undo, naming it",
              code != 0 and "changed by someone else between the run's changes" in err, err)

        # ── 7. a folder renamed refuses the undo until it is renamed back
        clock["at"] += timedelta(hours=2)
        ask("participant", "rename", "Cass", "Cara", "--folder")
        rid = lines()[-1]["run"]
        code, _x, err = run("agents", "undo-run", rid, "--note", "Undo the rename")
        check("380: a run that renamed a participant's folder is not undone whole, the folder to be renamed back first",
              code != 0 and "renamed a participant's folder" in err, err)

        # ── 8. the ops only the app does: refused, nothing written, logged as app_only, their dry runs answering
        before = digest(root)
        cfg_before = config_file.read_bytes()
        refused = {
            "settings": ask("settings", "--your-name", "A. Keeper"),
            "send": ask("project", "send", "--to", str(base / "out")),
            "names": ask("names", "remove", "1"),
            "invite": ask("team", "invite"),
        }
        dry_send = ask("project", "send", "--to", str(base / "out"), "--dry-run")
        agent_log.flush()
        app_only = [e for e in agent_log.load(log)["entries"] if e.get("code") == "app_only"]
        check("380: Settings, a send, a name off the list and Working together are refused for an agent in a line "
              "naming where in the app, nothing written, each logged as app_only",
              all(c != 0 and "Only the app" in e for c, _g, e in refused.values()) and digest(root) == before
              and config_file.read_bytes() == cfg_before and not (base / "out").exists() and len(app_only) == 4,
              json.dumps({k: v[2][:120] for k, v in refused.items()}))
        check("380: an op only the app does still answers its dry run", dry_send[0] == 0, dry_send[2])

        # ── 9. an MCP connection is one run, a second its own
        clock["at"] += timedelta(hours=2)
        n = len(lines())
        for _ in range(2):
            mcp = mcp_server.Server(root=str(root), config=str(config_file))
            mcp.client = "Claude Desktop"
            for words in (25, 26):
                mcp.call(mcp.by_name["statement_length_set"], {"words": words, "request": ASKED})
        got = lines()[n:]
        listed = mcp.call(mcp.by_name["agent_changes"], {"limit": 2})
        shown = support.plain(listed.get("structuredContent") or {})
        check("380: an MCP connection's writes are one run and a second connection's another, and agent_changes "
              "reads them newest first", len(got) == 4 and got[0]["run"] == got[1]["run"] != got[2]["run"] == got[3]["run"]
              and got[0]["via"] == "mcp" and got[0]["agent"] == "Claude Desktop"
              and [e["id"] for e in shown.get("changes") or []] == [got[3]["id"], got[2]["id"]],
              json.dumps([e["run"] for e in got]) + json.dumps(shown)[:300])

        # ── 10. one change undone alone (agentreview2): its files back as they were just before it, the rest kept
        clock["at"] += timedelta(hours=2)
        ask("participant", "set", "Ada", "--label", "Second summer")
        label_change = lines()[-1]["id"]
        before_board = digest(root)
        ask("board", "fresh", "Bryn", "--name", "Trial")
        board_change = lines()[-1]["id"]
        made_board = digest(root)
        step = (runs()[lines()[-1]["run"]].get("steps") or {}).get(board_change) or {}
        check("380: each change keeps its files as they stood before and after it, by their contents in the store",
              step and all((store / "objects" / s["after"]).is_file() and (s["before"] is None or
                                                                         (store / "objects" / s["before"]).is_file())
                           for s in step.values()), json.dumps(step)[:400])
        code, dry, err = run("agents", "undo-change", board_change, "--dry-run", "--note", "Undo the trial board")
        check("380: undo-change's dry run says what it would put back, nothing written",
              code == 0 and dry.get("changes") == [board_change] and digest(root) == made_board, err + json.dumps(dry))
        code, undone, err = run("agents", "undo-change", board_change, "--note", "Undo the trial board")
        check("380: a change undone alone puts every file it changed back byte for byte as it was just before it, the "
              "change before it in the same run kept", code == 0 and digest(root) == before_board
              and undone.get("undo_run") and lines()[-1]["op"] == "agents undo-change", err + json.dumps(undone)[:300])
        again = run("agents", "undo-change", board_change, "--note", "Undo the trial board")
        check("380: a change undone already is refused, naming the undo's run", again[0] != 0
              and "undone already" in again[2], again[2])
        # his own edit of the project file through the app's own call, outside the record, then the label's undo
        cfg_kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE)
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, None
        try:
            import idiograph_routes
            idiograph_routes.api_project({"root": idiograph_routes.project_id(root),
                                          "research_question": "How do people keep bees on a roof in a city?"})
        finally:
            server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_kept
        his = digest(root)
        code, _x, err = run("agents", "undo-change", label_change, "--note", "Undo the label")
        check("380: a change whose file he changed since is refused whole, naming the file, nothing written",
              code != 0 and "the project's settings, changed since" in err and digest(root) == his, err)
        # through MCP, one change undone in its turn
        mcp = mcp_server.Server(root=str(root), config=str(config_file))
        mcp.client = "Claude Desktop"
        mcp.call(mcp.by_name["board_fresh"], {"case": "Ada", "name": "Draft", "request": ASKED})
        last = lines()[-1]["id"]
        mcp.call(mcp.by_name["agent_undo_change"], {"changes": [last], "request": "Undo the draft board"})
        check("380: MCP's agent_undo_change undoes one change as the command line does",
              digest(root) == his and lines()[-1]["op"] == "agents undo-change"
              and lines()[-1]["target"] == {"changes": [last]}, json.dumps(lines()[-2:])[:500])
    finally:
        agent_changes.ALL_OPS, agent_changes.NOW = kept[0], kept[1]
        if kept[2] is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = kept[2]
        server_mod.CONFIG_PATH = kept[3]
