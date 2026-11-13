"""Area 266: the project's ops for agents (26 October 2026, parity's second group, Adam's principle of 19 and
24 October: one API, the app one way to call it and an agent another). Four routes the page calls had no op
on the command line or the MCP server: Settings' save (`/api/project`), New project (`/api/new-project`),
Rename on a participant's menu (`/api/rename`) and Mark complete (`/api/complete`). Each op calls the route's
own function, so each check runs the page's call on one project and the agent's op on its twin and finds the
same files written, History included, the dry run writing nothing, and the refusals the route's own.

The fixtures are invented: a project on swimming in a lake at night, two made-up participants."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import openpyxl

from .support import check
from . import support

TRANSCRIPT = ("Sam: [00:00:03] What is the water like after dark?\n"
              "Tamsin Example: [00:00:08] Black and warm, warmer than the air.\n"
              "Sam: [00:00:20] And going in?\n"
              "Tamsin Example: [00:00:26] I stop thinking. The cold takes the day off me.\n")


def make_workbook(root: Path, folder: str, speaker: str) -> Path:
    """A made-up participant's annotated workbook with two statements, one to a row."""
    import workbook as wb_mod
    case = root / folder
    (case / "Source").mkdir(parents=True)
    raw = openpyxl.Workbook()
    first = raw.active
    first.title = "Initial"
    first.append(["Name", "Timestamp", "Transcript"])
    first.append(["Interviewer", "00:00:04", "What brings you to the lake at night?"])
    first.append([speaker, "00:00:09", "The quiet. Nobody watches you swim in the dark."])
    first.append(["Interviewer", "00:00:20", "And when you are out in the middle?"])
    first.append([speaker, "00:00:26", "I float and the stars and the water are one thing."])
    source = case / "Source" / f"{folder} - interview.xlsx"
    raw.save(source)
    book = wb_mod.create_from_source(source, case / f"{folder} - EN & ES.xlsx")
    wb = openpyxl.load_workbook(book, rich_text=True)
    ws = wb.worksheets[0]
    cols = wb_mod.detect_columns(ws)
    ws.cell(3, cols["es"]).value = "Swimming unseen as a freedom"
    ws.cell(5, cols["es"]).value = "Losing the edge between water and sky"
    wb.save(book)
    return book


STAMPS = re.compile(r"\d{8}-\d{4}(-\d+)?")
TIMES = ("updated", "at", "opened", "made", "saved", "last", "changed")


def plain(value):
    """A JSON value with every time in it set aside, so two writes a moment apart compare alike."""
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items() if k not in TIMES}
    if isinstance(value, list):
        return [plain(v) for v in value]
    return value


def files(at: Path) -> dict:
    """Every file under a folder by its path, a workbook by its cells, a JSON file with its times set
    aside, an archive copy's stamp too, and a lock file never read."""
    import locks
    out = {}
    for p in sorted(at.rglob("*")):
        if not p.is_file() or p.name == locks.NAME or p.suffix == ".lock":
            continue
        # the project's own History names who asked, the app on one twin and the agent on the other (area 319)
        if p.name == "idiograph-history.json":
            continue
        # and the record of agents' changes and a run's restore point, the agent's own bookkeeping, which the
        # page never makes (noholds, 13 November 2026)
        if p.name == "idiograph-agent-changes.jsonl" or ".idiograph-restore" in p.relative_to(at).parts:
            continue
        rel = STAMPS.sub("<stamp>", p.relative_to(at).as_posix())
        if p.suffix == ".xlsx":
            wb = openpyxl.load_workbook(p)
            out[rel] = {ws.title: [[str(c.value) for c in row] for row in ws.iter_rows()] for ws in wb.worksheets}
            wb.close()
        elif p.suffix == ".json":
            out[rel] = plain(json.loads(p.read_text(encoding="utf-8")))
        else:
            out[rel] = p.read_bytes()
    return out


def test_project_ops(scratch: Path):
    print("\n266. The project's ops for agents: project set, project new, participant rename and participant "
          "complete, each the page's own route, its dry run and its History (26 October)")
    import cli
    import mcp_server
    import rounds as rounds_mod
    import server as server_mod
    import idiograph_routes as routes
    from workbook import WorkbookError

    base = scratch / "project-ops-266"
    shutil.rmtree(base, ignore_errors=True)
    page, agent = base / "page" / "Night swimming", base / "agent" / "Night swimming"
    page.mkdir(parents=True)
    project_json = {"name": "Night swimming", "research_question": "How do people live swimming in a lake at night?",
                    "agents": {"allowed": True, "at": "2026-10-26T09:00:00+00:00"}}
    (page / server_mod.PROJECT_FILE).write_text(json.dumps(project_json), encoding="utf-8")
    make_workbook(page, "P1 - Tamsin", "Tamsin")
    make_workbook(page, "P2 - Orrin", "Orrin")
    config_file = base / "config-266.json"
    config_file.write_text(json.dumps({"projects": [], "interviewer": "Interviewer", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    plan = base / "plan.json"
    plan.write_text(json.dumps({"pets": [{"title": "Unseen in the dark", "members": ["S1"]},
                                         {"title": "One with the water", "members": ["S2"]}]}), encoding="utf-8")

    def run(*args):
        return cli.run(["--config", str(config_file), *args])

    def run_json(*args):
        code, out, err = run("--json", *args)
        got = support.plain(json.loads(out)) if out.strip() else {}
        return code, (got if code == 0 else {}), err + (got.get("error", "") if code != 0 else "")

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)

    def as_page(fn, body, root=None):
        """The page's call, on the server's settings, with the recent list in memory."""
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, (str(root) if root else None)
        server_mod.STATE_MEMORY = {"recent": []}
        try:
            return fn(body)
        finally:
            server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    try:
        code, _, err = run("--root", str(page), "board", "new", "Tamsin", "--from", str(plan), "--note", "His first board",
                           "--tool", "Claude Code")
        code, study, err2 = run_json("--root", str(page), "cases")
        board_id = next((b["id"] for r in study.get("cases", []) if r["case"] == "P1 - Tamsin" for b in r["boards"]), "")
        code2, _, err3 = run("--root", str(page), "board", "rename", "Tamsin", str(board_id), "Lake board",
                             "--note", "Name the board", "--tool", "Claude Code")
        check("266: his board is made on Tamsin's canvas for the fixture and renamed, so its History holds a revision",
              code == 0 and code2 == 0 and board_id, err + err2 + err3)
        shutil.copytree(page, agent)
        check("266: the twin projects start alike", files(page) == files(agent))

        # 1. project set: Settings' save, the dry run first
        before = files(agent)
        code, dry, err = run_json("--root", str(agent), "project", "set", "--name", "Swimming at night",
                                  "--question", "How do people live night swimming?", "--pet-labels", "numbers",
                                  "--dry-run")
        check("266: project set's dry run says each change and writes nothing",
              code == 0 and files(agent) == before and dry.get("dry_run") is True and len(dry.get("changes", [])) == 3
              and dry["project"] == {"name": "Swimming at night", "research_question": "How do people live night swimming?",
                                     "pet_labels": "numbers", "timecodes": "1:15:12"}, err + json.dumps(dry))
        code, done, err = run_json("--root", str(agent), "project", "set", "--name", "Swimming at night",
                                   "--question", "How do people live night swimming?", "--pet-labels", "numbers",
                                   "--note", "Rename the project", "--tool", "Claude Code")
        as_page(routes.api_project, {"root": str(page), "name": "Swimming at night",
                                     "research_question": "How do people live night swimming?"}, page)
        as_page(routes.api_project, {"root": str(page), "pet_labels": "numbers"}, page)
        check("266: project set writes the project file as Settings' save does, and nothing else",
              code == 0 and files(agent) == files(page) and files(agent) != before
              and {k: v for k, v in files(agent).items() if k != server_mod.PROJECT_FILE}
              == {k: v for k, v in before.items() if k != server_mod.PROJECT_FILE}, err + json.dumps(done))
        code, done, err = run_json("--root", str(agent), "project", "set", "--question", "How is a lake lived at night?",
                                   "--note", "Only the question")
        held = json.loads((agent / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
        check("266: a question alone keeps the name as it is",
              code == 0 and held["name"] == "Swimming at night" and held["research_question"] == "How is a lake lived at night?"
              and len(done.get("changes", [])) == 1, err + json.dumps(done))
        as_page(routes.api_project, {"root": str(page), "name": "Swimming at night",
                                     "research_question": "How is a lake lived at night?"}, page)
        code, _, err = run("--demo", "project", "set", "--name", "Mine", "--note", "Try the demo")
        check("266: the demo's project is refused as the route refuses it", code != 0 and "The demo's project is fixed." in err, err)
        code, _, err = run("--root", str(agent), "project", "set", "--name", "Mine")
        check("266: a write without his request is refused", code != 0 and "--note" in err, err)

        # 2. participant complete: Mark complete on the statements screen
        before = files(agent)
        code, dry, err = run_json("--root", str(agent), "participant", "complete", "Orrin", "--dry-run")
        check("266: participant complete's dry run says it would mark and writes nothing",
              code == 0 and files(agent) == before and dry.get("changed") is True and dry.get("complete") is None, err)
        code, done, err = run_json("--root", str(agent), "participant", "complete", "Orrin", "--note", "Orrin is done")
        as_page(routes.api_complete, {"workbook": str(page / "P2 - Orrin" / "P2 - Orrin - EN & ES.xlsx"), "op": "mark"}, page)
        agent_book = agent / "P2 - Orrin" / "P2 - Orrin - EN & ES.xlsx"
        check("266: participant complete writes the mark as Mark complete does, and nothing else",
              code == 0 and files(agent) == files(page) and files(agent) != before and rounds_mod.complete_of(agent_book)
              and done.get("changed") is True, err + json.dumps(done))
        at = rounds_mod.complete_of(agent_book)
        code, again, err = run_json("--root", str(agent), "participant", "complete", "Orrin", "--note", "Again")
        check("266: a second mark keeps the first time and changes nothing",
              code == 0 and again.get("changed") is False and rounds_mod.complete_of(agent_book) == at, err)
        code, done, err = run_json("--root", str(agent), "participant", "complete", "Orrin", "--reopen", "--note", "Reopen him")
        as_page(routes.api_complete, {"workbook": str(page / "P2 - Orrin" / "P2 - Orrin - EN & ES.xlsx"), "op": "reopen"}, page)
        check("266: --reopen takes the mark off as the route's reopen does",
              code == 0 and rounds_mod.complete_of(agent_book) is None and files(agent) == files(page), err)

        # 3. participant rename: Rename on a participant's menu, with the folder
        before = files(agent)
        code, dry, err = run_json("--root", str(agent), "participant", "rename", "Tamsin", "Wenna", "--folder", "--dry-run")
        check("266: participant rename's dry run lists each change and writes nothing",
              code == 0 and files(agent) == before and dry.get("new") == "Wenna" and dry.get("changes")
              and dry.get("folder_changes"), err + json.dumps(dry))
        code, _, err = run("--root", str(agent), "participant", "rename", "Tamsin", "Orrin", "--dry-run")
        check("266: another participant's name is refused in the dry run as the rename refuses it",
              code != 0 and "Orrin is another participant's name in this project" in err and files(agent) == before, err)
        code, done, err = run_json("--root", str(agent), "participant", "rename", "Tamsin", "Wenna", "--folder",
                                   "--note", "Call her Wenna")
        as_page(routes.api_rename, {"root": str(page), "case": "P1 - Tamsin", "name": "Wenna", "folder": True,
                                    "op": "rename"}, page)
        renamed = agent / "P1 - Wenna" / "P1 - Wenna - EN & ES.xlsx"
        boards = json.loads((renamed.parent / "Working" / f"{renamed.stem}.themes.json").read_text(encoding="utf-8"))
        old_boards = before["P1 - Tamsin/Working/P1 - Tamsin - EN & ES.themes.json"]
        check("266: participant rename writes what the page's rename writes, its folder, files, archive copies and boards",
              code == 0 and done.get("label") == "P1 - Wenna" and renamed.is_file() and not (agent / "P1 - Tamsin").exists()
              and files(agent) == files(page) and any("_Archive/" in k for k in files(agent)), err + json.dumps(done))
        check("266: each board keeps its History through the rename, as the page's rename keeps it",
              [plain(b.get("history")) for b in boards["boards"]] == [b.get("history") for b in old_boards["boards"]]
              and all(b.get("history") for b in boards["boards"]) and boards.get("case") == "P1 - Wenna",
              json.dumps([b.get("history") for b in boards["boards"]])[:300] + str(boards.get("case")))

        # 4. project new: New project on Home
        talk = base / "lake talk.txt"
        talk.write_text(TRANSCRIPT, encoding="utf-8")
        new_page, new_agent = base / "new-page", base / "new-agent"
        new_page.mkdir()
        new_agent.mkdir()
        settings = config_file.read_bytes()
        code, dry, err = run_json("project", "new", str(new_agent), "--name", "Lake at night", "--question",
                                  "How is a lake lived at night?", "--transcript", str(talk), "--pseudonym", "Kestrel",
                                  "--dry-run")
        cases = dry.get("cases") or [{}]
        check("266: project new's dry run names each participant, its interview and speakers, and writes nothing",
              code == 0 and not list(new_agent.iterdir()) and config_file.read_bytes() == settings
              and cases[0].get("label") == "P1 - Kestrel" and cases[0]["interviews"][0]["interview"] == "Interview"
              and cases[0]["interviews"][0]["speakers"] == {"Sam": "interviewer", "Tamsin Example": "participant"},
              err + json.dumps(dry))
        code, made, err = run_json("project", "new", str(new_agent), "--name", "Lake at night", "--question",
                                   "How is a lake lived at night?", "--transcript", str(talk), "--pseudonym", "Kestrel",
                                   "--note", "A project for the lake study")
        import base64
        data = base64.b64encode(talk.read_bytes()).decode("ascii")
        read = as_page(routes.api_new_project, {"op": "read", "name": talk.name, "data": data})
        as_page(routes.api_new_project, {"op": "make", "folder": str(new_page), "name": "Lake at night",
                                         "research_question": "How is a lake lived at night?",
                                         "files": [{"name": talk.name, "data": data, "pseudonym": "Kestrel",
                                                    "interview": read["interview"], "speakers": read["speaker_roles"]}]})
        roots = [Path(e["root"]).name for e in json.loads(config_file.read_text(encoding="utf-8"))["projects"]]
        check("266: project new makes the folder a project as New project does, and adds it to Idiograph's projects",
              code == 0 and made.get("cases") == ["P1 - Kestrel"] and files(new_agent) == files(new_page)
              and (new_agent / "P1 - Kestrel" / "P1 Kestrel - EN & ES.xlsx").is_file()
              and roots == ["new-agent", "new-page"],
              err + str(roots) + str([k for k in set(files(new_agent)) | set(files(new_page))
                                      if files(new_agent).get(k) != files(new_page).get(k)]))
        settings = config_file.read_bytes()
        code, _, err = run("project", "new", str(new_agent), "--transcript", str(talk), "--pseudonym", "Linnet",
                           "--note", "Again")
        check("266: a folder that is a project already is refused as New project refuses it, nothing written",
              code != 0 and "a project already" in err and config_file.read_bytes() == settings, err)
        other = base / "new-other"
        other.mkdir()
        code, _, err = run("project", "new", str(other), "--transcript", str(talk), "--pseudonym", "kestrel", "--dry-run")
        check("266: a pseudonym that is not one capitalised word is refused in the card's words",
              code != 0 and "one capitalised word" in err and not list(other.iterdir()), err)

        # 5. the MCP tools answer as the command line does
        mcp = mcp_server.Server(root=str(agent), config=str(config_file))
        names = {t["name"] for t in mcp.tools}
        res = mcp.call(mcp.by_name["participant_complete"], {"case": "Orrin", "dry_run": True, "request": "Look first"})
        said = support.plain(res.get("structuredContent") or {}) if not res.get("isError") else {}
        res2 = mcp.call(mcp.by_name["project_set"], {"name": "Lake swims", "dry_run": True, "request": "Look first"})
        said2 = support.plain(res2.get("structuredContent") or {}) if not res2.get("isError") else {}
        res3 = mcp.call(mcp.by_name["participant_rename"], {"case": "Wenna", "name": "Ffion", "dry_run": True,
                                                            "request": "Look first"})
        said3 = support.plain(res3.get("structuredContent") or {}) if not res3.get("isError") else {}
        res4 = mcp.call(mcp.by_name["project_new"], {"folder": str(other), "transcripts": [{"file": str(talk), "pseudonym": "Linnet"}],
                                                     "dry_run": True, "request": "Look first"})
        said4 = support.plain(res4.get("structuredContent") or {}) if not res4.get("isError") else {}
        check("266: MCP's project_set, project_new, participant_rename and participant_complete run the same ops",
              {"project_set", "project_new", "participant_rename", "participant_complete"} <= names
              and said.get("changed") is True and said2.get("project", {}).get("name") == "Lake swims"
              and len(said2.get("changes", [])) == 1
              and said3.get("new") == "Ffion" and (said4.get("cases") or [{}])[0].get("label") == "P1 - Linnet"
              and not list(other.iterdir()), json.dumps([res, res2, res3, res4])[:600])
    except WorkbookError as exc:
        check("266: the page's calls run", False, str(exc))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
