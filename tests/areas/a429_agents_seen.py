"""Area 429: the cross on Home's bar of agents' changes marks them seen without the review (homecardbuild, Adam's
direction E, 18 November 2026).

The bar at the foot of a project's card says "Agents made 2 changes since you last looked." with Review and a cross. The
cross marks every change so far seen through the route By an agent reads (`/api/agent-changes`, op `seen`), which runs
the command line's own `agents seen` as the app's, calling `agent_changes.mark_seen`, so the bar goes. Its command line
and MCP twin (agent_seen) are there for the parity check, and only the app does it: an agent's call is refused in one
line, nothing written, and kept in the agent log as app_only, its dry run saying how many it would mark.

What is checked, on a scratch project made here (invented): two changes an agent makes are counted unseen; the route's
dry run says 2 and writes nothing; the route marks them seen, the seen mark recorded with its time, the changes still in
the record, and the count 0; a second time marks none; the command line and MCP, as an agent, are refused with nothing
written and logged as app_only, and their dry runs answer the count; a new change counts again; a demo's route answers
nothing marked."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from . import support
from .support import check

ASKED = "Mark them all seen"


def store_files(root: Path) -> dict:
    """The record of agents' changes and its store, every file by its contents."""
    import agent_changes
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if p.is_file() and not p.name.endswith(".lock") and (rel == agent_changes.FILE or rel.startswith(agent_changes.STORE)):
            out[rel] = p.read_bytes()
    return out


def test_agents_seen(scratch: Path):
    print("\n429. The cross on Home's bar of agents' changes marks them seen, the app's alone (homecardbuild)")
    import agent_changes
    import agent_log
    import cli
    import idiograph_routes as routes
    import mcp_server
    import server as server_mod

    base = scratch / "seen-429"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Kite flying"
    root.mkdir(parents=True)
    server_mod.save_json(root / server_mod.PROJECT_FILE, {
        "name": "Kite flying", "research_question": "How do people learn to fly a kite?",
        "agents": {"allowed": True, "at": "2026-11-18T09:00:00+00:00"}})
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Kit", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    log = base / "agent-log.json"
    kept = (agent_changes.ALL_OPS, os.environ.get(agent_log.PLACE), server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE,
            server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    agent_changes.ALL_OPS = None
    os.environ[agent_log.PLACE] = str(log)
    server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, None
    server_mod.STATE_PATH, server_mod.STATE_MEMORY = base / "state.json", {"recent": []}

    def run(*args, tool="Claude Code"):
        given = ["--config", str(config_file), "--root", str(root), "--json", *args]
        if tool is not None:
            given += ["--tool", tool]
        code, out, err = cli.run(given)
        got = support.plain(json.loads(out)) if out.strip() else {}
        return code, got, err

    pid = routes.project_id(root)

    try:
        # two changes by an agent, so Home's bar would say 2
        for question in ("How do people learn to fly a kite on a windy hill?", "How do adults learn to fly a kite?"):
            code, _, err = run("project", "set", "--question", question, "--note", "Reword the question")
        unseen = routes.api_agent_unseen({})["unseen"]
        check("429: two changes an agent made are counted unseen for Home's bar", code == 0 and unseen.get(pid) == 2,
              f"{code} {err[:200]} {unseen}")

        # the route's dry run, the cross's twin: the count, nothing written
        start = store_files(root)
        dry = routes.api_agent_changes({"op": "seen", "root": pid, "dry_run": True})
        check("429: the route's dry run says 2 would be marked and writes nothing",
              dry.get("done", {}).get("unseen") == 2 and store_files(root) == start
              and routes.api_agent_unseen({})["unseen"].get(pid) == 2, json.dumps(dry)[:300])

        # the cross: every change so far seen, the mark recorded with its time, the changes kept
        lines_before = agent_changes.read(root)
        done = routes.api_agent_changes({"op": "seen", "root": pid})
        seen = json.loads((root / agent_changes.STORE / agent_changes.SEEN).read_text(encoding="utf-8"))
        check("429: the route marks them seen, the seen mark recorded with its time, the changes still in the record",
              done.get("done", {}).get("marked") == 2 and pid not in routes.api_agent_unseen({})["unseen"]
              and seen.get("agents") == 2 and bool(seen.get("at")) and agent_changes.read(root) == lines_before,
              json.dumps(done)[:300] + json.dumps(seen))
        review = routes.api_agent_changes({"op": "read", "root": pid})
        check("429: By an agent still lists both changes, neither of them New",
              review["total"] == 2 and review["new"] == 0, json.dumps(review)[:300])
        again = routes.api_agent_changes({"op": "seen", "root": pid})
        check("429: a second press marks none", again.get("done", {}).get("marked") == 0, json.dumps(again)[:300])

        # a new change counts again
        run("project", "set", "--question", "How do adults learn to fly a kite at the coast?", "--note", "Reword it")
        check("429: a change made since counts unseen again", routes.api_agent_unseen({})["unseen"].get(pid) == 1,
              str(routes.api_agent_unseen({})))

        # an agent, by the command line and MCP: refused, nothing written, logged as app_only, the dry run answering
        start = store_files(root)
        code, got, err = run("agents", "seen", "--note", ASKED)
        code_dry, got_dry, _ = run("agents", "seen", "--dry-run", "--note", ASKED)
        mcp = mcp_server.Server(str(root), config=str(config_file))
        mcp.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))

        def call(n, name, arguments):
            return mcp.receive(json.dumps({"jsonrpc": "2.0", "id": n, "method": "tools/call",
                                           "params": {"name": name, "arguments": arguments}}))["result"]

        res = call(2, "agent_seen", {"request": ASKED})
        res_dry = call(3, "agent_seen", {"request": ASKED, "dry_run": True})
        agent_log.flush()
        app_only = [e for e in agent_log.load(log)["entries"] if e.get("code") == "app_only"]
        check("429: an agent's agents seen, by the command line and MCP, is refused in one line, nothing written, each "
              "kept in the agent log as app_only",
              code != 0 and "Only the researcher" in err + json.dumps(got) and res["isError"] and store_files(root) == start
              and routes.api_agent_unseen({})["unseen"].get(pid) == 1 and len(app_only) == 2,
              f"{code} {err[:200]} {json.dumps(res)[:200]} {len(app_only)}")
        check("429: its dry run, by the command line and MCP, says how many it would mark and writes nothing",
              code_dry == 0 and got_dry.get("unseen") == 1 and not res_dry["isError"]
              and store_files(root) == start, f"{json.dumps(got_dry)[:200]} {json.dumps(res_dry)[:200]}")

        # a demo keeps no record: nothing marked, nothing refused
        demo = routes.api_agent_changes({"op": "seen", "path": "demo/Juno/Juno - EN & ES.xlsx"})
        check("429: a demo's route answers nothing marked", demo.get("done", {}).get("marked") == 0, json.dumps(demo)[:200])
    finally:
        agent_changes.ALL_OPS = kept[0]
        if kept[1] is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = kept[1]
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY) = kept[2:]
