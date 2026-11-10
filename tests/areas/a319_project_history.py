"""Area 319: the project's own History (projhistory, 2 November 2026, Adam's yes by dialog that evening). A change
to the project or to a participant as a whole kept no History before: `project set` and Settings' save (the name,
the question, the PET labels, the timecodes, the privacy tick), `timepoints`, `length`, `participant rename`,
`participant complete` and its reopen, and `gets settings`. Each now adds one record to `idiograph-history.json` at
the project's root, under the project's lock: when, the op, what changed from what to what, and who asked, the app,
or an agent by its tool with his request, "approved in the app" or "without asking" where a hold applies.

What is checked: each op writes its record from the app's route and from the command line and MCP, with the
request. A dry run, a refusal and a change that changes nothing write none. A held rename approved in the app and
one run without asking say so. `project history` and MCP's `project_history` read it newest first, and a send never
carries it. None of these ops has an undo.

The fixture is invented: the demo's three dog owners, copied into a scratch project."""
from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

from .support import DEMO_SHIPPED, check
from . import support

ASKED = "Call the project Walking the dogs."


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
        "name": "Living with a dog", "agents": {"allowed": True, "at": "2026-11-02T09:00:00+00:00"}}),
        encoding="utf-8")


def test_project_history(scratch: Path):
    print("\n319. The project's own History: project set, timepoints, length, participant rename and complete, and "
          "gets settings each keep a record from the app and from an agent, with the request, none for a dry run "
          "or a refusal (2 November)")
    import cli
    import holds
    import idiograph_routes as routes
    import mcp_server
    import project_history
    import server as server_mod
    from workbook import WorkbookError

    base = scratch / "history-319"
    root = base / "Dogs"
    make_project(root)
    config_file = base / "config.json"
    config = {"projects": [{"root": str(root)}], "interviewer": "Adam", "corpus": "", "gravity_reference": "",
              "corpus_exclude": []}
    config_file.write_text(json.dumps(config), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, holds.RUN_AT_ONCE)
    hist = root / project_history.FILE

    def in_app(fn, body):
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, None
        server_mod.STATE_MEMORY = {"recent": []}
        try:
            return fn(body)
        finally:
            server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept[:3]

    def run(*args):
        return cli.run(["--config", str(config_file), "--root", str(root), *args])

    def answer(*args):
        code, out, err = run("--json", *args)
        got = support.plain(json.loads(out)) if out.strip() else {}
        return code, got, err + (got.get("error", "") if code != 0 else "")

    def ask(*args):
        return answer(*args, "--note", ASKED, "--tool", "Claude Code")

    def records() -> list:
        return project_history.load(root)

    def last() -> dict:
        return (records() or [{}])[-1]

    def by_agent(h: dict, tool: str = "Claude Code") -> bool:
        return h.get("by") == "agent" and h.get("tool") == tool and h.get("request") == ASKED

    pid = routes.project_id(root)
    try:
        # 1. project set: the app's save and the agent's, a dry run and a refusal writing none
        in_app(routes.api_project, {"root": pid, "name": "Dogs at home", "research_question": ""})
        app_set = last()
        check("319: Settings' save in the app keeps a record: when, the op, the change from what to what, by the app",
              app_set.get("op") == "project set" and app_set.get("by") == "app" and app_set.get("when")
              and app_set.get("changes") == ['Name from "Living with a dog" to "Dogs at home".']
              and "tool" not in app_set, json.dumps(app_set))
        n = len(records())
        code, _dry, err = answer("project", "set", "--name", "Walking the dogs", "--dry-run")
        code2, _no, err2 = answer("project", "set", "--name", "Walking the dogs")
        code3, _same, err3 = ask("project", "set", "--name", "Dogs at home")
        check("319: project set's dry run, its refusal without a request and a save that changes nothing write no record",
              code == 0 and code2 != 0 and code3 == 0 and len(records()) == n, err + err2 + err3)
        code, got, err = ask("project", "set", "--name", "Walking the dogs", "--timecodes", "75:12")
        h = last()
        check("319: project set keeps a record naming the agent's tool and his request, each change a line",
              code == 0 and len(records()) == n + 1 and h.get("op") == "project set" and by_agent(h)
              and h.get("changes") == ['Name from "Dogs at home" to "Walking the dogs".', "Timecodes from 1:15:12 to 75:12."],
              err + json.dumps(h))
        in_app(routes.api_project, {"root": pid, "agents": False})
        in_app(routes.api_project, {"root": pid, "agents": True})
        check("319: the privacy tick, the app's alone, keeps its record each way",
              [r["changes"] for r in records()[-2:]] == [["Allow AI agents to read this project unticked."],
                                                         ["Allow AI agents to read this project ticked."]],
              json.dumps(records()[-2:]))

        # 2. the GETs settings, from an agent and from the app, while the project has one timepoint
        n = len(records())
        code, _d, err = answer("gets", "settings", "--minimum", "2", "--dry-run")
        code2, _g, err2 = ask("gets", "settings", "--minimum", "2", "--out", "Mabel=Joined after the interviews")
        agent_gets = last()
        in_app(routes.api_gets_settings, {"root": pid, "op": "save", "one_per_pet": False})
        app_gets = last()
        check("319: the GETs settings keep a record from an agent and from the app, the dry run none",
              code == 0 and code2 == 0 and len(records()) == n + 2 and by_agent(agent_gets)
              and agent_gets.get("op") == "gets settings"
              and agent_gets.get("changes") == ["Participants needed for a GET from the usual number to 2.",
                                                "Mabel out of the study: Joined after the interviews."]
              and app_gets.get("by") == "app" and app_gets.get("changes") == ["One per PET from on to off."],
              err + err2 + json.dumps(records()[-2:]))

        # 3. timepoints and the statement length, from the app and from an agent
        n = len(records())
        in_app(routes.api_project, {"root": pid, "timepoints": [{"label": "T1"}, {"label": "T2", "description": "A year on"}]})
        app_tp = last()
        spec = base / "tps.json"
        spec.write_text(json.dumps({"timepoints": [{"label": "T1"}, {"label": "Later", "description": "A year on"}]}),
                        encoding="utf-8")
        code, _d, err = answer("timepoints", "--from", str(spec), "--dry-run")
        code2, _t, err2 = ask("timepoints", "--from", str(spec))
        agent_tp = last()
        check("319: timepoints keep a record from the app and from an agent, the dry run none",
              code == 0 and code2 == 0 and len(records()) == n + 2 and app_tp.get("op") == "timepoints"
              and app_tp.get("by") == "app" and "Timepoints from 1 to 2." in app_tp.get("changes", [])
              and agent_tp.get("op") == "timepoints" and by_agent(agent_tp)
              and agent_tp.get("changes") == ["Timepoint 2 now Later, A year on."], err + err2 + json.dumps(records()[-2:]))
        n = len(records())
        code, _d, err = answer("length", "20", "--dry-run")
        code2, _r, err2 = ask("length", "99")
        code3, _l, err3 = ask("length", "20")
        agent_len = last()
        in_app(routes.api_project, {"root": pid, "statement_words": 18})
        app_len = last()
        check("319: the statement length keeps a record from an agent and from the app, a dry run and a refusal none",
              code == 0 and code2 != 0 and code3 == 0 and len(records()) == n + 2 and by_agent(agent_len)
              and agent_len.get("changes") == ["Statement length from 15 to 20 words."]
              and app_len.get("by") == "app" and app_len.get("changes") == ["Statement length from 20 to 18 words."],
              err + err2 + err3)

        # 4. a participant's statements marked complete and reopened
        n = len(records())
        book = root / "Juno" / "Juno - EN & ES.xlsx"
        # the demo's Juno has her statements marked complete already
        code, _d, err = answer("participant", "complete", "Juno", "--reopen", "--dry-run")
        code2, _a, err2 = ask("participant", "complete", "Juno")
        code3, _c, err3 = ask("participant", "complete", "Juno", "--reopen")
        agent_reopen = last()
        in_app(routes.api_complete, {"workbook": str(book), "op": "mark"})
        app_mark = last()
        in_app(routes.api_complete, {"workbook": str(book), "op": "mark"})
        check("319: participant complete keeps a record from an agent, the app's mark its own, a dry run and a mark "
              "that changes nothing none",
              code == 0 and code2 == 0 and code3 == 0 and len(records()) == n + 2
              and agent_reopen.get("op") == "participant complete" and by_agent(agent_reopen)
              and agent_reopen["changes"][0].startswith("Juno's statements at T1 reopened, marked complete since ")
              and " at " in agent_reopen["changes"][0][-12:]
              and app_mark.get("by") == "app" and app_mark.get("changes") == ["Juno's statements at T1 marked complete."],
              err + err2 + err3 + json.dumps(records()[-2:]))

        # 5. a participant renamed, by the app and by an agent, the folder too through a hold approved in the app
        n = len(records())
        code, _d, err = answer("participant", "rename", "Rowan", "Rook", "--dry-run")
        code2, _r, err2 = ask("participant", "rename", "Rowan", "Rook")
        agent_rename = last()
        in_app(routes.api_rename, {"root": pid, "case": "Rook", "name": "Rowan", "op": "rename"})
        app_rename = last()
        check("319: participant rename keeps a record from an agent and from the app, with what it changed, the dry "
              "run none",
              code == 0 and code2 == 0 and len(records()) == n + 2 and by_agent(agent_rename)
              and agent_rename.get("op") == "participant rename" and agent_rename["changes"][0] == "Rowan renamed Rook."
              and len(agent_rename["changes"]) > 1 and app_rename.get("by") == "app"
              and app_rename["changes"][0] == "Rook renamed Rowan.", err + err2 + json.dumps(records()[-2:]))
        holds.RUN_AT_ONCE = None
        n = len(records())
        code, held, err = ask("participant", "rename", "Mabel", "Maple", "--folder")
        waiting = len(records()) == n and (root / "Mabel").is_dir()
        server_mod.CONFIG_PATH = config_file
        try:
            holds.approve(root, held.get("hold", {}).get("id") or held.get("id") or "h1")
        finally:
            server_mod.CONFIG_PATH = kept[0]
        approved = last()
        config["skip_permissions"] = True
        config_file.write_text(json.dumps(config), encoding="utf-8")
        code2, _s, err2 = ask("participant", "rename", "Maple", "Mabel", "--folder")
        skipped = last()
        check("319: a held rename writes no record while it waits, then one naming the agent \"approved in the app\", "
              "and with Dangerously skip permissions one \"without asking\"",
              code == 0 and waiting and len(records()) == n + 2
              and approved.get("tool") == "Claude Code, approved in the app" and approved.get("request") == ASKED
              and approved["changes"][0] == "Mabel renamed Maple, the folder too."
              and code2 == 0 and skipped.get("tool") == "Claude Code, without asking"
              and skipped["changes"][0] == "Maple renamed Mabel, the folder too.",
              err + err2 + json.dumps(held)[:300] + json.dumps(records()[-2:]))
        holds.RUN_AT_ONCE = kept[3]
        config.pop("skip_permissions")
        config_file.write_text(json.dumps(config), encoding="utf-8")

        # 6. MCP writes with the client as its tool, and reads the History as the command line does
        mcp = mcp_server.Server(root=str(root), config=str(config_file))
        n = len(records())
        res = mcp.call(mcp.by_name["project_set"], {"research_question": "How do people live with a dog?",
                                                    "request": ASKED})
        mcp_set = last()
        read = mcp.call(mcp.by_name["project_history"], {"limit": 2})
        code, got, err = answer("project", "history")
        _c, said, _e = run("project", "history", "--limit", "1")
        shown = support.plain(read.get("structuredContent") or {}).get("history") or []
        check("319: MCP's project_set keeps a record with his request, and project history and project_history read "
              "the records newest first",
              not res.get("isError") and len(records()) == n + 1 and mcp_set.get("by") == "agent"
              and mcp_set.get("request") == ASKED and mcp_set.get("tool")
              and code == 0 and got.get("total") == len(records()) and got["history"][0] == records()[-1]
              and len(shown) == 2 and shown[0] == records()[-1] and shown[1] == records()[-2]
              and "History, newest first" in said and "Research question from none to" in said,
              err + json.dumps({k: v for k, v in read.items() if k != "content"})[:900] + said[:300])

        # 7. a send never carries it
        out = base / "sent"
        out.mkdir(exist_ok=True)
        holds.RUN_AT_ONCE = True
        code, sent, err = answer("project", "send", "--to", str(out), "--note", "Send it to Curt")
        holds.RUN_AT_ONCE = kept[3]
        files = [p for p in out.iterdir() if p.suffix == ".idiograph"]
        names = zipfile.ZipFile(files[0]).namelist() if files else []
        check("319: a send never carries the project's History",
              code == 0 and names and not any(n.endswith(project_history.FILE) for n in names)
              and any(n.endswith("idiograph-project.json") for n in names), err + str(names[:8]))
    except WorkbookError as exc:
        check("319: the page's calls run", False, str(exc))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, holds.RUN_AT_ONCE = kept
