"""Area 268: the statements CSV for agents (26 October 2026, parity's fourth group, Adam's principle of 19
and 24 October: one API, the app one way to call it and an agent another). Export in Settings
(`/api/export`) had no op on the command line or the MCP server. `participant export` calls the route's own
function, so each check runs the page's call on one project and the agent's op on its twin and finds the
same files written, the dry run writing nothing, no History kept by either, and the refusals the route's own.

The fixtures are invented: a project on keeping an allotment through winter, two made-up participants."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import openpyxl

from .support import check
from . import support


def make_workbook(root: Path, folder: str, speaker: str, note: str = "") -> Path:
    """A made-up participant's annotated workbook with two statements, one to a row, and an interviewer
    note when one is given."""
    import workbook as wb_mod
    case = root / folder
    (case / "Source").mkdir(parents=True)
    raw = openpyxl.Workbook()
    first = raw.active
    first.title = "Initial"
    first.append(["Name", "Timestamp", "Transcript"])
    first.append(["Interviewer", "00:00:04", "What takes you to the allotment in January?"])
    first.append([speaker, "00:00:09", "The frost on the leeks. Nobody else is there."])
    first.append(["Interviewer", "00:00:20", "And what do you do there?"])
    first.append([speaker, "00:00:26", "Mostly I stand and look at the bare beds and plan."])
    source = case / "Source" / f"{folder} - interview.xlsx"
    raw.save(source)
    book = wb_mod.create_from_source(source, case / f"{folder} - EN & ES.xlsx")
    wb = openpyxl.load_workbook(book, rich_text=True)
    ws = wb.worksheets[0]
    cols = wb_mod.detect_columns(ws)
    ws.cell(3, cols["es"]).value = "Winter's plot as a place of one's own"
    ws.cell(5, cols["es"]).value = "Planning as a way of hoping"
    wb.save(book)
    if note:
        # the statements screen's own write of a note on the interviewer's turn
        wb_mod.save_interviewer_note(book, "Initial", 4, note, "Interviewer")
    return book


def files(at: Path) -> dict:
    """Every file under a folder by its path and its bytes, a lock file never read."""
    import locks
    return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*"))
            if p.is_file() and p.name != locks.NAME and p.suffix != ".lock"}


def test_export_op(scratch: Path):
    print("\n268. The statements CSV for agents: participant export, the page's own route, its dry run, no "
          "History kept (26 October)")
    import cli
    import mcp_server
    import server as server_mod
    import idiograph_routes as routes
    from workbook import WorkbookError

    base = scratch / "export-op-268"
    shutil.rmtree(base, ignore_errors=True)
    page, agent = base / "page" / "Winter allotments", base / "agent" / "Winter allotments"
    page.mkdir(parents=True)
    project_json = {"name": "Winter allotments", "research_question": "How do people live an allotment in winter?",
                    "agents": {"allowed": True, "at": "2026-10-26T09:00:00+00:00"}}
    (page / server_mod.PROJECT_FILE).write_text(json.dumps(project_json), encoding="utf-8")
    make_workbook(page, "P1 - Hollis", "Hollis", note="He laughed at the leeks.")
    make_workbook(page, "P2 - Bryony", "Bryony")
    config_file = base / "config-268.json"
    config_file.write_text(json.dumps({"projects": [], "interviewer": "Interviewer", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    plan = base / "plan.json"
    plan.write_text(json.dumps({"pets": [{"title": "A plot of one's own", "members": ["S1"]},
                                         {"title": "Hoping by planning", "members": ["S2"]}]}), encoding="utf-8")

    def run(*args):
        return cli.run(["--config", str(config_file), *args])

    def run_json(*args):
        code, out, err = run("--json", *args)
        got = support.plain(json.loads(out)) if out.strip() else {}
        return code, (got if code == 0 else {}), err + (got.get("error", "") if code != 0 else "")

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)

    def as_page(fn, body, root):
        """The page's call, on the server's settings, with the recent list in memory."""
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, str(root)
        server_mod.STATE_MEMORY = {"recent": []}
        try:
            return fn(body)
        finally:
            server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    hollis = Path("P1 - Hollis") / "P1 - Hollis - EN & ES.xlsx"
    csv_rel = "P1 - Hollis/Working/P1 - Hollis - All Experiential Statements.csv"
    notes_rel = "P1 - Hollis/Working/P1 - Hollis - Interviewer notes.md"
    try:
        code, _, err = run("--root", str(page), "board", "new", "Hollis", "--from", str(plan), "--note", "His first board",
                           "--tool", "Claude Code")
        check("268: his board is made on Hollis's canvas for the fixture", code == 0, err)
        shutil.copytree(page, agent)
        check("268: the twin projects start alike", files(page) == files(agent))

        # 1. the dry run: what it would write, nothing written
        before = files(agent)
        code, dry, err = run_json("--root", str(agent), "participant", "export", "Hollis", "--notes", "--dry-run")
        check("268: participant export's dry run names the CSV and the notes file and writes nothing",
              code == 0 and files(agent) == before and dry.get("dry_run") is True and dry.get("statements") == 2
              and dry.get("file", "").endswith("P1 - Hollis - All Experiential Statements.csv")
              and dry.get("notes") == 1 and str(dry.get("notes_file", "")).endswith("P1 - Hollis - Interviewer notes.md")
              and dry.get("replaced") is False, err + json.dumps(dry))
        answer = as_page(routes.api_export, {"path": str(page / hollis), "notes": True, "dry_run": True}, page)
        check("268: the route's own dry run writes nothing either",
              answer.get("dry_run") is True and answer.get("statements") == 2 and files(page) == before, json.dumps(answer))

        # 2. the export: the same files as the page's, and nothing else changed, no History
        code, done, err = run_json("--root", str(agent), "participant", "export", "Hollis", "--notes")
        as_page(routes.api_export, {"path": str(page / hollis), "notes": True}, page)
        after = files(agent)
        rows = after.get(csv_rel, b"").decode("utf-8-sig").splitlines()
        check("268: participant export writes the CSV and the notes file the page's Export writes, byte for byte",
              code == 0 and after == files(page) and csv_rel in after and notes_rel in after
              and done.get("statements") == 2 and done.get("dry_run") is False
              and len(rows) == 3 and "A plot of one's own" in rows[1] and "Hoping by planning" in rows[2]
              and b"He laughed at the leeks." in after[notes_rel], err + json.dumps(done) + str(rows))
        check("268: nothing else changes, the progress file and the boards and their History as they were, as the page's "
              "export keeps none",
              {k: v for k, v in after.items() if k not in (csv_rel, notes_rel)} == before, err)
        code, again, err = run_json("--root", str(agent), "participant", "export", "Hollis")
        check("268: a second export takes the place of the CSV there and says so, the notes left as they were",
              code == 0 and again.get("replaced") is True and files(agent) == after and "notes" not in again, err)

        # 3. a participant with no notes, and the refusals
        code, out, err = run("--root", str(agent), "participant", "export", "Bryony", "--notes", "--dry-run")
        check("268: a participant with no interviewer notes is told so, and no notes file is written",
              code == 0 and "has no interviewer notes" in out
              and not (agent / "P2 - Bryony" / "Working" / "P2 - Bryony - Interviewer notes.md").exists(), out + err)
        excel = agent / "P2 - Bryony" / "~$P2 - Bryony - EN & ES.xlsx"
        excel.write_text("", encoding="utf-8")
        (page / "P2 - Bryony" / excel.name).write_text("", encoding="utf-8")
        before = files(agent)
        code, _, err = run("--root", str(agent), "participant", "export", "Bryony", "--dry-run")
        code2, _, err2 = run("--root", str(agent), "participant", "export", "Bryony")
        refused = ""
        try:
            as_page(routes.api_export, {"path": str(page / "P2 - Bryony" / "P2 - Bryony - EN & ES.xlsx")}, page)
        except WorkbookError as exc:
            refused = str(exc)
        (page / "P2 - Bryony" / "~$P2 - Bryony - EN & ES.xlsx").unlink(missing_ok=True)
        check("268: a workbook open in Excel is refused in the route's words, the dry run too, nothing written",
              code != 0 and code2 != 0 and "is open in Excel" in err and "is open in Excel" in err2
              and "is open in Excel" in refused and files(agent) == before, err + err2 + refused)
        excel.unlink()

        # 4. the MCP tool answers as the command line does, with no request
        mcp = mcp_server.Server(root=str(agent), config=str(config_file))
        tool = mcp.by_name.get("participant_export")
        before = files(agent)
        res = mcp.call(tool, {"case": "Bryony", "dry_run": True}) if tool else {"isError": True}
        said = support.plain(res.get("structuredContent") or {}) if not res.get("isError") else {}
        res2 = mcp.call(tool, {"case": "Bryony", "notes": True}) if tool else {"isError": True}
        said2 = support.plain(res2.get("structuredContent") or {}) if not res2.get("isError") else {}
        check("268: MCP's participant_export runs the same op, its dry run writing nothing, and needs no request",
              tool is not None and "request" not in tool["inputSchema"]["properties"]
              and said.get("dry_run") is True and said.get("statements") == 2
              and said2.get("dry_run") is False and said2.get("notes") == 0 and said2.get("notes_file") is None
              and (agent / "P2 - Bryony" / "Working" / "P2 - Bryony - All Experiential Statements.csv").is_file()
              and {k for k in files(agent) if k not in before}
              == {"P2 - Bryony/Working/P2 - Bryony - All Experiential Statements.csv"},
              json.dumps([res, res2])[:600])
    except WorkbookError as exc:
        check("268: the page's calls run", False, str(exc))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
