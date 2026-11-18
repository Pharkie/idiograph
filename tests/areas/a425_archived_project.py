"""Area 425: a project is archived by the researcher, never by the app (archiveset, Adam, 18 November 2026: finishing
the GETs is not the end of a project while he writes up).

Project settings has one tick, Archive this project, kept in the project file as `archived: true` only while it is
ticked. Home lists an archived project in its own folded section, Archived projects, between Projects and Demo projects.
An archived project still opens and can be changed. A demo cannot be archived. Agents tick it through the route Project
settings saves (`/api/project`), the command line's `project set --archive on|off` and MCP's project_set `archived`,
recorded in the record of agents' changes and undone with the run like any other setting.

What is checked, on a scratch project made here (invented): the route archives and unarchives it, the key leaving the file
when it is unticked, every other key kept; a dry run writes nothing and leaves no record line; the command line and MCP do
the same through the same route, one record line each, a run undone putting the project file back byte for byte;
something other than on or off is refused with nothing written; a demo is refused; a project archived can still be
changed; a copy sent leaves the sender's archive tick out; Home's data carries the tick on each project; and the page
lists the section between Projects and Demo projects and draws a card into it by the tick."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import zipfile
from pathlib import Path

from . import support
from .support import check

ASKED = "Archive it while the write-up goes on"


def files(root: Path) -> dict:
    """Every file of the project by its contents, the locks, the record of agents' changes and its store and archive
    copies set aside."""
    import agent_changes
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if (not p.is_file() or p.name.endswith(".lock") or rel == agent_changes.FILE or rel.startswith(agent_changes.STORE)
                or "_Archive/" in rel or rel in agent_changes.NEVER or rel.startswith(".history")):
            continue
        out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def test_archived_project(scratch: Path):
    print("\n425. A project archived by the researcher, in Project settings, Home's sections and for agents (archiveset)")
    import agent_changes
    import agent_log
    import cli
    import idiograph_routes as routes
    import mcp_server
    import project_pack as pack_mod
    import server as server_mod
    from workbook import WorkbookError

    base = scratch / "archived-425"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Kite flying"
    root.mkdir(parents=True)
    other = base / "Beekeeping"
    other.mkdir()
    for folder, name in ((root, "Kite flying"), (other, "Beekeeping")):
        server_mod.save_json(folder / server_mod.PROJECT_FILE, {
            "name": name, "research_question": "How do people live with it?",
            "agents": {"allowed": True, "at": "2026-11-18T09:00:00+00:00"}})
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}, {"root": str(other)}], "interviewer": "Kit",
                                       "corpus": "", "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    log = base / "agent-log.json"
    kept = (agent_changes.ALL_OPS, os.environ.get(agent_log.PLACE), server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE,
            server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    agent_changes.ALL_OPS = None
    os.environ[agent_log.PLACE] = str(log)
    server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, None
    server_mod.STATE_PATH, server_mod.STATE_MEMORY = base / "state.json", {"recent": []}

    def run(*args, tool="Claude Code", at=root):
        given = ["--config", str(config_file), "--root", str(at), "--json", *args]
        if tool is not None:
            given += ["--tool", tool]
        code, out, err = cli.run(given)
        got = support.plain(json.loads(out)) if out.strip() else {}
        return code, got, err

    def held(at=root) -> dict:
        return json.loads((at / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))

    def refused(body) -> str:
        try:
            routes.api_project(body)
        except WorkbookError as exc:
            return str(exc)
        return ""

    try:
        start = files(root)
        check("425: a project nobody has archived reads archived false and its file holds no such key",
              routes.read_project(root)["archived"] is False and "archived" not in held() and files(root) == start, "")

        # ── the route Project settings saves
        dry = routes.api_project({"root": str(root), "archived": True, "dry_run": True})
        check("425: the route's dry run says Archive this project ticked and writes nothing, no record line",
              dry["project"]["archived"] is True and dry["dry_run"] is True
              and dry["changes"] == ["Archive this project ticked."] and files(root) == start
              and not agent_changes.read(root), json.dumps(dry)[:300])
        done = routes.api_project({"root": str(root), "archived": True})
        check("425: the route archives it, the key in the file, every other key kept, the change in its History",
              done["project"]["archived"] is True and held().get("archived") is True
              and held().get("name") == "Kite flying" and done["changes"] == ["Archive this project ticked."],
              json.dumps(done)[:300])
        again = routes.api_project({"root": str(root), "archived": True})
        check("425: archiving an archived project changes nothing", again["changes"] == [], json.dumps(again)[:200])
        routes.api_project({"root": str(other), "archived": True})
        changed = routes.api_project({"root": str(other), "name": "Beekeeping", "research_question": "Changed while archived?"})
        check("425: an archived project can still be changed, and stays archived",
              held(other).get("research_question") == "Changed while archived?" and held(other).get("archived") is True
              and changed["project"]["archived"] is True, "")
        routes.api_project({"root": str(other), "archived": False})
        off = routes.api_project({"root": str(root), "archived": False})
        check("425: the route unarchives it, the key leaving the file as it was before",
              off["project"]["archived"] is False and "archived" not in held() and files(root) == start
              and off["changes"] == ["Archive this project unticked."], json.dumps(off)[:300])

        # ── refusals, nothing written
        said = [refused({"root": str(root), "archived": bad}) for bad in ("yes", 1, None, "true")]
        check("425: anything but true or false is refused in one line, nothing written",
              all(said) and files(root) == start and len(set(said)) == 1, str(said))
        check("425: a call refused for one field writes none of them: a name beside a bad tick",
              refused({"root": str(root), "name": "Other name", "research_question": "Q?", "archived": "yes"})
              and files(root) == start, "")

        # ── the command line
        code, got, err = run("project", "set", "--archive", "on", "--dry-run")
        check("425: the command line's dry run says the change and writes nothing, no record line",
              code == 0 and got.get("dry_run") is True and got.get("changes") == ["Archive this project ticked."]
              and files(root) == start and not agent_changes.read(root), err[:300] + json.dumps(got)[:300])
        code, got, err = run("project", "set", "--archive", "on")
        check("425: a set without the researcher's request is refused, nothing written",
              code != 0 and files(root) == start, err[:200])
        code, got, err = run("project", "set", "--archive", "on", "--note", ASKED)
        lines = agent_changes.read(root)
        check("425: project set --archive on archives it, one record line",
              code == 0 and held().get("archived") is True and len(lines) == 1 and lines[0].get("op") == "project set"
              and got.get("project", {}).get("archived") is True, err[:300] + json.dumps(lines)[:300])
        code, shown, err = run("project", "show", tool=None)
        check("425: project show says it is archived", code == 0 and shown.get("project", {}).get("archived") is True,
              err[:200] + json.dumps(shown)[:200])
        if lines:
            code, _, err = run("agents", "undo-run", lines[0]["run"], "--note", "Put it back")
            check("425: undoing the run puts every file back byte for byte", code == 0 and files(root) == start,
                  err[:300])
        try:
            code, got, err = run("project", "set", "--archive", "maybe", "--note", ASKED)
        except SystemExit as exc:
            code = exc.code or 2
        check("425: --archive takes on or off alone, nothing written", code != 0 and files(root) == start, "")
        code, got, err = run("project", "set")
        check("425: project set with nothing to set still says what to set", code != 0 and "--archive" in json.dumps(got) + err, err[:200] + json.dumps(got)[:300])

        # ── MCP
        mcp = mcp_server.Server(str(root), config=str(config_file))
        mcp.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))

        def call(n, name, arguments):
            return mcp.receive(json.dumps({"jsonrpc": "2.0", "id": n, "method": "tools/call",
                                           "params": {"name": name, "arguments": arguments}}))["result"]

        before_mcp = len(agent_changes.read(root))
        res = call(2, "project_set", {"archived": True, "dry_run": True, "request": ASKED})
        check("425: MCP's project_set in a dry run writes nothing and leaves no record line",
              not res["isError"] and files(root) == start and len(agent_changes.read(root)) == before_mcp,
              json.dumps(res)[:300])
        res = call(3, "project_set", {"archived": True, "request": ASKED})
        shown = call(4, "project_show", {})
        lines = agent_changes.read(root)
        check("425: MCP's project_set archives it, one more record line, and project_show reads it back",
              not res["isError"] and held().get("archived") is True and len(lines) == before_mcp + 1
              and shown["structuredContent"]["project"]["archived"] is True, json.dumps(res)[:300])
        res = call(5, "project_set", {"archived": "yes", "request": ASKED})
        check("425: MCP refuses a tick that is not true or false, nothing more written",
              res["isError"] and held().get("archived") is True and len(agent_changes.read(root)) == len(lines),
              json.dumps(res)[:300])
        if lines:
            code, _, err = run("agents", "undo-run", lines[-1]["run"], "--note", "Put it back")
            check("425: undoing MCP's run puts every file back byte for byte", code == 0 and files(root) == start, err[:300])

        # ── Home's data and a copy sent
        routes.api_project({"root": str(root), "archived": True})
        sections = {s["project"]["name"]: s["project"] for s in routes.api_cases({})["projects"] if s.get("project")}
        check("425: Home's data carries the tick on each project, the archived one and the other",
              sections.get("Kite flying", {}).get("archived") is True and sections.get("Beekeeping", {}).get("archived") is False,
              json.dumps({k: v.get("archived") for k, v in sections.items()}))
        sent = base / "kites.idiograph"
        server_mod.CONFIG_PATH = config_file
        routes.send_project(root, sent)
        with zipfile.ZipFile(sent) as z:
            sent_project = json.loads(z.read(pack_mod.TOP + server_mod.PROJECT_FILE).decode("utf-8"))
        check("425: a copy sent leaves the sender's archive tick out, every other key kept, his own file keeping it",
              "archived" not in sent_project and sent_project.get("name") == "Kite flying" and held().get("archived") is True,
              json.dumps(sorted(sent_project)))
        routes.api_project({"root": str(root), "archived": False})

        # ── a demo is refused, whatever the client
        demo = routes.read_project(Path(server_mod.DEMO_DIR))
        check("425: a demo reads archived false", demo.get("archived") is False, str(demo.get("archived")))
        check("425: a demo cannot be archived, the route refusing it in the demo's own line",
              refused({"root": routes.project_id(Path(server_mod.DEMO_DIR)), "archived": True}) == "The demo's project is fixed.",
              refused({"root": routes.project_id(Path(server_mod.DEMO_DIR)), "archived": True}))

        # ── the page: the section between Projects and Demo projects, a card drawn into it by the tick
        html = support.text("apps/idiograph/static/idiograph.html")
        js = support.text("apps/idiograph/static/distil.js")
        order = [html.find(f'id="{name}"') for name in ("home-analysis", "home-archived", "home-demos")]
        check("425: Home lists Projects, then Archived projects, then Demo projects at the bottom",
              all(i > 0 for i in order) and order == sorted(order), str(order))
        check("425: the page draws a card into Archived projects by the project's archived tick, folded until opened",
              "const isArchived" in js and "archived.map((c) =>" in js and "live.map((c) =>" in js
              and "function archivedFold" in js and "draw(!held.includes(ARCHIVED_OPEN))" in js, "")
        check("425: Project settings has the tick, saved with Save in the call that carries the name",
              'id="set-archived"' in html and "body.archived = archive.checked" in js, "")
    finally:
        agent_changes.ALL_OPS = kept[0]
        if kept[1] is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = kept[1]
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY) = kept[2:]
