"""Area 265: the statements screen's own writes for agents (26 October 2026, parity with the page, group 1).
Each route the statements screen calls with no op for an agent until now has its op on the command line and
the MCP server, each calling the route itself: `turn edit` (/api/edit-turn), `turn interviewer-note`
(/api/interviewer-note), `turn assign` and `turn assign-undo` (/api/rows), `turn trim` (/api/trim) and
`turn trim-undo` (/api/rows), and `project add-transcripts` (/api/add-transcripts). For each, the op changes
what the page's call changes, cell for cell on a twin workbook the route writes as the page asks it, its dry
run writes nothing, and the progress file's History records the agent's write, by whom and for which request.

The fixtures are invented: the demo's dog owner, copied into a scratch project, and a made-up beekeeper.
"""
from __future__ import annotations

import hashlib
import json
import shutil

import openpyxl

from .support import DEMO_WORKBOOK, check
from . import support

TEXT = ("Adam: How did the hives come through the winter?\n\n"
        "Wren: Better than I feared. Two colonies made it, and the third went quiet in February.\n\n"
        "Adam: What was that like, opening it?\n\n"
        "Wren: I knew before I lifted the lid. There is a smell to a dead hive, sweet and wrong.\n")
SUMMER = ("Adam: And now the summer is here?\n\n"
          "Wren: Now I count them coming home in the evening, and I lose count on purpose.\n")


def sha(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def cells(path) -> dict:
    """Every cell's text, by sheet, row and column, the way two workbooks written alike compare."""
    import workbook as wb_mod
    wb = openpyxl.load_workbook(path, rich_text=True)
    try:
        return {(ws.title, c.row, c.column): wb_mod.plain_text(c.value)
                for ws in wb.worksheets for row in ws.iter_rows() for c in row if c.value not in (None, "")}
    finally:
        wb.close()


def files_under(folder) -> list:
    return sorted(str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file())


def test_statements_ops(scratch):
    print("\n265. The statements screen's writes for agents: turn edit, interviewer-note, assign and its undo, trim and its "
          "undo, and project add-transcripts, each the route's own call, its dry run and its History (26 October)")
    import cli
    import idiograph_routes as routes
    import mcp_server
    import rounds as rounds_mod
    import server as server_mod

    root = scratch / "statements-ops-265"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    (root / "idiograph-project.json").write_text(json.dumps({
        "name": "Living with a dog, a scratch copy", "agents": {"allowed": True, "at": "2026-10-26T09:00:00+00:00"}}),
        encoding="utf-8")
    config_file = scratch / "statements-ops-265-config.json"
    config_file.write_text(json.dumps({"root": str(root), "interviewer": "Adam", "projects": []}), encoding="utf-8")
    demo = DEMO_WORKBOOK
    (root / "P1 - Juno").mkdir()
    book = root / "P1 - Juno" / "Juno - EN & ES.xlsx"
    shutil.copy2(demo, book)
    # the twin the route writes as the page asks it, outside every project the command line reads
    page_root = scratch / "statements-ops-265-page"
    shutil.rmtree(page_root, ignore_errors=True)
    (page_root / "P1 - Juno").mkdir(parents=True)
    twin = page_root / "P1 - Juno" / "Juno - EN & ES.xlsx"
    shutil.copy2(demo, twin)
    (page_root / "idiograph-project.json").write_text(json.dumps({"name": "The page's twin"}), encoding="utf-8")

    def run(*args):
        code, out, err = cli.run(["--root", str(root), "--config", str(config_file), "--json", *args])
        got = support.plain(json.loads(out)) if out.strip() else {}
        return code, (got if code == 0 else {}), err + (got.get("error", "") if code != 0 else "")

    def page(route, body, at=page_root):
        kept = (server_mod.ROOT_OVERRIDE, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY)
        server_mod.ROOT_OVERRIDE, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY = str(at), config_file, {"recent": []}
        try:
            return route(body)
        finally:
            server_mod.ROOT_OVERRIDE, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY = kept

    def progress(path) -> dict:
        side = rounds_mod.progress_path(path)
        return json.loads(side.read_text(encoding="utf-8")) if side.exists() else {}

    def untouched(fn):
        """The workbook, its progress file and its folder's files before and after a call, and the call's answer."""
        before = (sha(book), sha(rounds_mod.progress_path(book)), files_under(root))
        got = fn()
        return got, before == (sha(book), sha(rounds_mod.progress_path(book)), files_under(root))

    def by_agent(record, request) -> bool:
        return record.get("by") == "agent" and record.get("tool") == "Claude Code" and record.get("request") == request

    # 1. turn edit: the words corrected and the timecode, as Edit does
    original = cells(book)
    words = original[("Initial", 3, 4)]
    fixed = words.replace("Erm. ", "", 1)
    (code, dry, err), clean = untouched(lambda: run("turn", "edit", "Juno", "Initial", "3", "--text", fixed,
                                                   "--time", "00:00:15", "--dry-run"))
    check("265: turn edit's dry run says the words and the timecode would change, and writes nothing",
          code == 0 and clean and dry.get("dry_run") is True and dry.get("changed") is True and dry.get("old") == words
          and dry.get("old_time") == "00:21" and dry.get("time") == "00:15", err or json.dumps(dry)[:300])
    ask = "Take the Erm out of Juno's first answer"
    code, done, err = run("turn", "edit", "Juno", "Initial", "3", "--text", fixed, "--time", "00:00:15",
                          "--note", ask, "--tool", "Claude Code")
    page(routes.api_edit_turn, {"path": str(twin), "sheet": "Initial", "row": 3, "text": fixed, "timecode": "00:00:15"})
    record = (progress(book).get("edits") or [{}])[-1]
    check("265: turn edit changes what the page's Edit changes, cell for cell, and History records the old words and "
          "the new as the agent's",
          code == 0 and done.get("changed") is True and cells(book) == cells(twin) and cells(book) != original
          and record.get("old") == words and record.get("new") == fixed and record.get("new_time") == "00:15"
          and by_agent(record, ask) and "by" not in (progress(twin).get("edits") or [{}])[-1],
          err or json.dumps(record)[:300])

    # 2. turn interviewer-note: his note on his own passage, the passage staying context
    rows_before = progress(book).get("rows")
    (code, dry, err), clean = untouched(lambda: run("turn", "interviewer-note", "Juno", "Initial", "2",
                                                   "--text", "Opened too wide", "--dry-run"))
    check("265: turn interviewer-note's dry run says the note would be written, and writes nothing",
          code == 0 and clean and dry.get("dry_run") is True and dry.get("changed") is True and dry.get("old") == "",
          err or json.dumps(dry)[:300])
    ask = "Note that I opened too wide"
    code, done, err = run("turn", "interviewer-note", "Juno", "Initial", "2", "--text", "Opened too wide",
                          "--note", ask, "--tool", "Claude Code")
    twin_side = sha(rounds_mod.progress_path(twin))
    page(routes.api_interviewer_note, {"path": str(twin), "sheet": "Initial", "row": 2, "text": "Opened too wide"})
    record = (progress(book).get("edits") or [{}])[-1]
    code3, _, refused = run("turn", "interviewer-note", "Juno", "Initial", "3", "--text", "Not his", "--note", ask)
    check("265: turn interviewer-note writes what the page writes, History keeps the agent's note, and the rows' states "
          "are as they were, a participant's passage refused with the route's line",
          code == 0 and done.get("changed") is True and cells(book) == cells(twin)
          and record.get("interviewer_note") is True and record.get("after") == {"note": "Opened too wide"}
          and by_agent(record, ask) and progress(book).get("rows") == rows_before
          and sha(rounds_mod.progress_path(twin)) == twin_side
          and code3 != 0 and "belong to the interviewer's passages" in refused, err or refused or json.dumps(record)[:300])

    # 3. turn assign and turn assign-undo: words given to another speaker, and put back
    before_assign = cells(book)
    (code, dry, err), clean = untouched(lambda: run("turn", "assign", "Juno", "Initial", "5", "--to", "Adam",
                                                   "--words", "It is like being caught.", "--dry-run"))
    check("265: turn assign's dry run answers the confirm card's lines, and writes nothing, no copy in _Archive either",
          code == 0 and clean and dry.get("dry_run") is True and dry.get("line") and dry.get("to") == "Adam",
          err or json.dumps(dry)[:300])
    ask = "That first sentence was mine"
    code, done, err = run("turn", "assign", "Juno", "Initial", "5", "--to", "Adam", "--words", "It is like being caught.",
                          "--note", ask, "--tool", "Claude Code")
    text5 = cells(twin)[("Initial", 5, 4)]
    at = text5.index("It is like being caught.")
    mine = page(routes.api_rows, {"op": "assign", "path": str(twin), "sheet": "Initial", "row": 5, "to": "Adam",
                                  "start": at, "end": at + len("It is like being caught.")})
    record = (progress(book).get("assignments") or [{}])[-1]
    check("265: turn assign changes what the page's Assign changes, cell for cell, and History records the agent's "
          "assignment",
          code == 0 and done.get("id") and cells(book) == cells(twin) and cells(book) != before_assign
          and record.get("id") == done["id"] and by_agent(record, ask), err or json.dumps(done)[:300])
    (code, dry, err), clean = untouched(lambda: run("turn", "assign-undo", "Juno", done.get("id", ""), "--dry-run"))
    dry_ok = code == 0 and clean and dry.get("dry_run") is True and dry.get("id") == done.get("id")
    ask = "Put that sentence back"
    code, back, err = run("turn", "assign-undo", "Juno", done.get("id", ""), "--note", ask, "--tool", "Claude Code")
    page(routes.api_rows, {"op": "restore", "path": str(twin), "id": mine["id"]})
    record = (progress(book).get("assignments") or [{}])[-1]
    code2, _, again = run("turn", "assign-undo", "Juno", done.get("id", ""), "--note", ask)
    check("265: turn assign-undo's dry run writes nothing, the undo puts the rows back as the page's does, History "
          "names the agent's undo, and a second undo is refused with the route's line",
          dry_ok and code == 0 and cells(book) == cells(twin) == before_assign and record.get("undone") is True
          and record.get("undone_by") == "agent" and record.get("undone_request") == ask
          and code2 != 0 and "already been undone" in again, err or again or json.dumps(record)[:300])

    # 4. turn trim and turn trim-undo: the opening cut off the front, and put back
    before_trim = cells(book)
    (code, dry, err), clean = untouched(lambda: run("turn", "trim", "Juno", "Initial", "3", "--before", "--dry-run"))
    check("265: turn trim's dry run answers the rows it would cut, and writes nothing, no copy in _Archive either",
          code == 0 and clean and dry.get("dry_run") is True and (dry.get("first"), dry.get("last"), dry.get("count")) == (2, 3, 2),
          err or json.dumps(dry)[:300])
    ask = "Cut the consent talk"
    code, cut, err = run("turn", "trim", "Juno", "Initial", "3", "--before", "--note", ask, "--tool", "Claude Code")
    theirs = page(routes.api_trim, {"path": str(twin), "sheet": "Initial", "row": 3, "direction": "before"})
    record = (progress(book).get("trims") or [{}])[-1]
    check("265: turn trim cuts what the page's trim cuts, cell for cell, and History records the agent's trim",
          code == 0 and cut.get("removed") == 2 and cells(book) == cells(twin) and cells(book) != before_trim
          and record.get("id") == cut.get("id") and by_agent(record, ask), err or json.dumps(cut)[:300])
    (code, dry, err), clean = untouched(lambda: run("turn", "trim-undo", "Juno", cut.get("id", ""), "--dry-run"))
    dry_ok = code == 0 and clean and dry.get("dry_run") is True and (dry.get("first"), dry.get("last")) == (2, 3)
    ask = "Put the opening back"
    code, back, err = run("turn", "trim-undo", "Juno", cut.get("id", ""), "--note", ask, "--tool", "Claude Code")
    page(routes.api_rows, {"op": "untrim", "path": str(twin), "id": theirs["id"]})
    record = (progress(book).get("trims") or [{}])[-1]
    check("265: turn trim-undo's dry run writes nothing, the undo puts the rows back as the page's does, and History "
          "names the agent's undo",
          dry_ok and code == 0 and back.get("restored") == 2 and cells(book) == cells(twin) == before_trim
          and record.get("undone") is True and record.get("undone_by") == "agent" and record.get("undone_request") == ask,
          err or json.dumps(back)[:300])
    code, _, said = run("turn", "trim", "Juno", "Initial", "3", "--dry-run")
    check("265: a trim with no side is refused in one line", code != 0 and "--before" in said, said)

    # 5. project add-transcripts: a new participant, then a further interview of theirs
    spring, summer = scratch / "statements-ops-265-spring.txt", scratch / "statements-ops-265-summer.txt"
    spring.write_text(TEXT, encoding="utf-8")
    summer.write_text(SUMMER, encoding="utf-8")
    spec = scratch / "statements-ops-265-add.json"
    spec.write_text(json.dumps([{"file": str(spring), "pseudonym": "Wren", "interview": "Spring"}]), encoding="utf-8")
    there = files_under(root)
    code, dry, err = run("project", "add-transcripts", "--from", str(spec), "--dry-run")
    plan = (dry.get("plan") or [{}])[0]
    check("265: project add-transcripts' dry run answers the participant it would make, its interview, passages and "
          "speakers, and writes nothing",
          code == 0 and dry.get("dry_run") is True and dry.get("cases") == ["P2 - Wren"] and plan.get("joins") is False
          and plan["interviews"][0]["passages"] == 4
          and {s["name"]: s["role"] for s in plan["interviews"][0]["speakers"]} == {"Adam": "Interviewer", "Wren": "Participant"}
          and files_under(root) == there, err or json.dumps(dry)[:400])
    ask = "Add Wren's spring interview"
    code, done, err = run("project", "add-transcripts", "--from", str(spec), "--note", ask, "--tool", "Claude Code")
    data = __import__("base64").b64encode(spring.read_bytes()).decode("ascii")
    page(routes.api_add_transcripts, {"op": "add", "root": routes.project_id(page_root),
                                      "files": [{"name": spring.name, "data": data, "pseudonym": "Wren", "interview": "Spring",
                                                 "speakers": {"Adam": "interviewer", "Wren": "participant"}}]})
    made = root / "P2 - Wren" / "P2 Wren - EN & ES.xlsx"
    theirs = page_root / "P2 - Wren" / "P2 Wren - EN & ES.xlsx"
    record = (progress(made).get("imports") or [{}])[-1]
    described = openpyxl.load_workbook(made, read_only=True).properties.description or ""
    check("265: project add-transcripts makes what the page's Add makes, cell for cell, the workbook naming who made it "
          "for which request, and History recording the agent's Add",
          code == 0 and done.get("cases") == ["P2 - Wren"] and made.exists() and cells(made) == cells(theirs)
          and [f for f in files_under(root / "P2 - Wren") if not f.endswith(".progress.json")]
          == files_under(page_root / "P2 - Wren")
          and "Claude Code" in described and ask in described and record.get("sheets") == ["Spring"]
          and by_agent(record, ask) and not progress(theirs).get("imports"),
          err or json.dumps(done)[:300] + " " + json.dumps(files_under(root / "P2 - Wren")))
    spec.write_text(json.dumps({"files": [{"file": str(summer), "pseudonym": "Wren", "interview": "Summer"}]}), encoding="utf-8")
    code, joined, err = run("project", "add-transcripts", "--from", str(spec), "--note", "And her summer one",
                            "--tool", "Claude Code")
    sheets = openpyxl.load_workbook(made, read_only=True).sheetnames
    check("265: a further interview joins its participant, a sheet at the end of the workbook, History recording it too",
          code == 0 and joined.get("joined") == ["P2 - Wren"] and sheets == ["Spring", "Summer"]
          and [r.get("sheets") for r in progress(made).get("imports", [])] == [["Spring"], ["Summer"]],
          err or json.dumps(joined)[:300])
    spec.write_text(json.dumps([{"file": str(spring), "pseudonym": "wren"}]), encoding="utf-8")
    there = files_under(root)
    code, _, said = run("project", "add-transcripts", "--from", str(spec), "--note", ask)
    check("265: a refusal is the route's own line, nothing written",
          code != 0 and "one capitalised word" in said and files_under(root) == there, said)

    # 6. the MCP server's tools run the same ops, and list among Idiograph's
    srv = mcp_server.Server(str(root), config=str(config_file))

    def call(name, **given):
        return srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                       "params": {"name": name, "arguments": given}}))["result"]

    names = {t["name"] for t in mcp_server.tools_for("idiograph")}
    got, clean = untouched(lambda: call("turn_trim", case="Juno", sheet="Initial", row=3, direction="after",
                                        request="Cut the goodbyes", dry_run=True))
    ok = got["isError"] is False and clean and support.plain(got["structuredContent"])["first"] == 3
    got = call("turn_interviewer_note", case="Juno", sheet="Initial", row=2, text="", request="Clear my note")
    check("265: MCP lists the seven tools, its turn_trim dry-runs writing nothing, and turn_interviewer_note clears the note",
          {"turn_edit", "turn_interviewer_note", "turn_assign", "turn_assign_undo", "turn_trim", "turn_trim_undo",
           "project_add_transcripts"} <= names and ok and got["isError"] is False
          and ("Initial", 2, 7) not in cells(book), json.dumps(got)[:300])
