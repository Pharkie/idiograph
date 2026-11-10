"""Area 257: the op that renames a workbook's quotes heading from Key quotes to Quote (Adam's ruling of 23
October 2026), for the workbooks made before 22 October. The command line's quote-heading, MCP's
quote_heading and the route /api/quote-heading all run `routes.rename_quote_heading`. Its dry run writes
nothing. The op renames the heading on every annotation sheet and touches no other cell, its value or its
style, records the rename in the progress file under edits, and a second run changes nothing. A workbook
open in Excel, or under another write, is refused and left as it was. With --all every participant's
workbook is its own write.

The fixtures are invented: a project on keeping an allotment, three made-up participants.
"""
from __future__ import annotations

import hashlib
import json
import shutil

import openpyxl

from .support import check
from . import support


def sha(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def headings(path) -> dict:
    wb = openpyxl.load_workbook(path, read_only=True)
    try:
        return {ws.title: [c for c in next(ws.iter_rows(min_row=1, max_row=1, values_only=True))] for ws in wb.worksheets}
    finally:
        wb.close()


def every_cell(path) -> dict:
    """Each cell's value and style, and each sheet's widths and heights, as openpyxl reads them."""
    wb = openpyxl.load_workbook(path, rich_text=True)
    try:
        out = {}
        for ws in wb.worksheets:
            for row in ws.iter_rows():
                for c in row:
                    out[(ws.title, c.coordinate)] = (repr(c.value), repr(c.font), repr(c.fill), repr(c.border),
                                                     repr(c.alignment), c.number_format, repr(c.protection))
            out[(ws.title, "widths")] = {k: d.width for k, d in ws.column_dimensions.items()}
            out[(ws.title, "heights")] = {k: d.height for k, d in ws.row_dimensions.items()}
            out[(ws.title, "freeze")] = ws.freeze_panes
        out["sheets"] = wb.sheetnames
        return out
    finally:
        wb.close()


def make_workbook(root, name: str, heading: str):
    """A made-up participant's workbook of two annotation sheets and a sheet of the analyst's own, its
    quotes column headed `heading`, with statements, notes, quotes and an Interviewer note in it."""
    import workbook as wb_mod
    folder = root / name
    (folder / "Source").mkdir(parents=True)
    raw = openpyxl.Workbook()
    first = raw.active
    first.title = "Initial"
    first.append(["Name", "Timestamp", "Transcript"])
    first.append(["Interviewer", "00:00:04", "How did the allotment go this year?"])
    first.append([name, "00:00:09", "The beans came up in a week and the slugs had them in two."])
    first.append(["Interviewer", "00:00:20", "What did you do then?"])
    first.append([name, "00:00:26", "I sowed them again under jars and sat out with a torch at night."])
    second = raw.create_sheet("Second")
    second.append(["Name", "Timestamp", "Transcript"])
    second.append(["Interviewer", "00:00:03", "And the autumn?"])
    second.append([name, "00:00:07", "The squash took over the path and I let it."])
    source = folder / "Source" / f"{name} - interview.xlsx"
    raw.save(source)
    book = wb_mod.create_from_source(source, folder / f"{name} - EN & ES.xlsx")
    wb = openpyxl.load_workbook(book, rich_text=True)
    for ws in wb.worksheets:
        cols = wb_mod.detect_columns(ws)
        ws.cell(1, cols["kq"]).value = heading
        ws.cell(3, cols["es"]).value = "Losing the first sowing to the slugs"
        ws.cell(3, cols["en"]).value = "A made-up note on patience."
        ws.cell(3, cols["kq"]).value = "“the slugs had them in two”"
    notes = wb.worksheets[0]
    notes.cell(1, 7).value, notes.cell(1, 7).font = wb_mod.NOTE_HEADER, wb_mod.HFONT
    notes.cell(2, 7).value = "I asked too broadly here."
    own = wb.create_sheet("My notes")
    own.append(["Key quotes", "kept for myself"])
    wb.save(book)
    return book


def test_quote_heading(scratch):
    print("\n257. The op that renames a workbook's Key quotes heading to Quote, its dry run, the History, a second run "
          "and a locked workbook (23 October)")
    import cli
    import idiograph_routes as routes
    import locks
    import mcp_server
    import rounds as rounds_mod
    import server as server_mod
    import workbook as wb_mod

    root = scratch / "quote-heading-257"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    (root / "idiograph-project.json").write_text(json.dumps({
        "name": "Allotments, a scratch project", "agents": {"allowed": True, "at": "2026-10-23T10:00:00+01:00"}}),
        encoding="utf-8")
    config_file = scratch / "quote-heading-257-config.json"
    config_file.write_text(json.dumps({"root": str(root), "interviewer": "Interviewer"}), encoding="utf-8")
    hazel = make_workbook(root, "Hazel", "Key quotes")
    ivy = make_workbook(root, "Ivy", "Key quotes")
    juniper = make_workbook(root, "Juniper", "Quote")

    def run(*args):
        code, out, err = cli.run(["--root", str(root), "--config", str(config_file), "--json", *args])
        got = support.plain(json.loads(out)) if out.strip() else {}
        # a refusal with --json is its line under error, written to the answer
        return code, (got if code == 0 else {}), err + (got.get("error", "") if code != 0 else "")

    def progress_edits(book):
        side = rounds_mod.progress_path(book)
        return json.loads(side.read_text(encoding="utf-8")).get("edits", []) if side.exists() else []

    def archived(book):
        folder = book.parent / "_Archive"
        return sorted(p.name for p in folder.iterdir()) if folder.is_dir() else []

    # 1. the dry run says per sheet what it would change and writes nothing
    before_sha, before_cells = sha(hazel), every_cell(hazel)
    code, dry, err = run("quote-heading", "Hazel", "--dry-run")
    sheets = {s["sheet"]: s for w in dry.get("workbooks", []) for s in w["sheets"]}
    check("257: the dry run names each annotation sheet's rename, and the workbook, its progress file and _Archive are as they were",
          code == 0 and dry.get("dry_run") is True and dry.get("renamed") == 2
          and set(sheets) == {"Initial", "Second"}
          and all(s["change"] == "rename" and s["was"] == "Key quotes" and s["now"] == "Quote" for s in sheets.values())
          and sha(hazel) == before_sha and not rounds_mod.progress_path(hazel).exists() and not archived(hazel),
          err or json.dumps(dry)[:400])

    # 2. the op renames every annotation sheet's heading, and nothing else
    code, done, err = run("quote-heading", "Hazel", "--note", "Head my old workbooks Quote", "--tool", "Claude Code")
    after_cells = every_cell(hazel)
    changed = sorted(str(k) for k in after_cells if after_cells[k] != before_cells.get(k))
    heads = headings(hazel)
    check("257: the heading reads Quote on both annotation sheets, and the analyst's own sheet keeps its Key quotes",
          code == 0 and done.get("renamed") == 2 and heads["Initial"][5] == "Quote" and heads["Second"][5] == "Quote"
          and heads["My notes"][0] == "Key quotes", err or str(heads))
    kq_style = lambda cells, sheet: cells[(sheet, "F1")][1:]
    check("257: no other cell changed, value or style, the headings kept their font and alignment, widths and heights the same",
          set(after_cells) == set(before_cells)
          and changed == ["('Initial', 'F1')", "('Second', 'F1')"]
          and all(kq_style(after_cells, s) == kq_style(before_cells, s) for s in ("Initial", "Second")),
          str(changed))
    edits = progress_edits(hazel)
    backups = archived(hazel)
    check("257: the progress file records each rename under edits, with the tool, his request and the copy kept in _Archive",
          [(e["sheet"], e["row"], e["old"], e["new"]) for e in edits] == [("Initial", 1, "Key quotes", "Quote"),
                                                                         ("Second", 1, "Key quotes", "Quote")]
          and all(e.get("heading") is True and e.get("by") == "agent" and e.get("tool") == "Claude Code"
                  and e.get("request") == "Head my old workbooks Quote" and e.get("backup") in backups for e in edits)
          and len({e["batch"] for e in edits}) == 1 and len(backups) == 1
          and headings(hazel.parent / "_Archive" / backups[0])["Initial"][5] == "Key quotes",
          json.dumps(edits)[:400])
    kept_root = server_mod.ROOT_OVERRIDE
    server_mod.ROOT_OVERRIDE = str(root)
    try:
        stamp = routes.api_stamp({"workbook": str(hazel)})
    finally:
        server_mod.ROOT_OVERRIDE = kept_root
    check("257: the turn screen does not take the rename for a passage written in a conversation",
          stamp["turns"]["count"] == 0, str(stamp["turns"]))

    # 3. a second run changes nothing
    again_sha = sha(hazel)
    code, again, err = run("quote-heading", "Hazel", "--note", "Again", "--tool", "Claude Code")
    check("257: a second run renames nothing and writes nothing, each sheet said to be headed Quote already",
          code == 0 and again.get("renamed") == 0 and sha(hazel) == again_sha and len(progress_edits(hazel)) == 2
          and len(archived(hazel)) == 1
          and all(s["change"] == "already" for w in again["workbooks"] for s in w["sheets"]), err or json.dumps(again)[:300])

    # 4. a workbook open in Excel, or under another write, is refused and left as it was
    ivy_sha = sha(ivy)
    excel = wb_mod.lock_file(ivy)
    excel.write_bytes(b"")
    try:
        code, _, err = run("quote-heading", "Ivy", "--note", "Head it Quote", "--tool", "Claude Code")
    finally:
        excel.unlink()
    check("257: a workbook open in Excel is refused, nothing written",
          code != 0 and "open in Excel" in err and sha(ivy) == ivy_sha and not progress_edits(ivy) and not archived(ivy), err)
    kept_wait = locks.WAIT
    locks.WAIT = 0.2
    try:
        with wb_mod.case_held(ivy, wait=1):
            code, _, err = run("quote-heading", "Ivy", "--note", "Head it Quote", "--tool", "Claude Code")
    finally:
        locks.WAIT = kept_wait
    check("257: a workbook under another write is refused, nothing written",
          code != 0 and locks.BUSY in err and sha(ivy) == ivy_sha and not progress_edits(ivy) and not archived(ivy), err)
    code, _, err = run("quote-heading", "--note", "Head it Quote")
    code2, _, err2 = run("quote-heading", "Ivy", "--all", "--note", "Head it Quote")
    code3, _, err3 = run("quote-heading", "Ivy")
    check("257: a participant or --all, never both or neither, and a write needs his request",
          code != 0 and code2 != 0 and "--all" in err and "not both" in err2 and code3 != 0 and "--note" in err3
          and sha(ivy) == ivy_sha, err + err2 + err3)

    # 5. the project-wide form: a dry run listing every participant, then each workbook its own write
    shas = {b: sha(b) for b in (hazel, ivy, juniper)}
    code, dry, err = run("quote-heading", "--all", "--dry-run")
    said = {w["case"]: sorted({s["change"] for s in w["sheets"]}) for w in dry.get("workbooks", [])}
    check("257: --all --dry-run lists every participant's sheets and writes nothing",
          code == 0 and said == {"Hazel": ["already"], "Ivy": ["rename"], "Juniper": ["already"]}
          and dry.get("renamed") == 2 and all(sha(b) == s for b, s in shas.items()), err or str(said))
    excel = wb_mod.lock_file(juniper)
    excel.write_bytes(b"")
    try:
        code, done, err = run("quote-heading", "--all", "--note", "Head every workbook Quote", "--tool", "Claude Code")
    finally:
        excel.unlink()
    check("257: --all renames Ivy's headings, leaves Hazel's as they are, and a workbook open in Excel is said and skipped",
          code == 0 and done.get("renamed") == 2 and headings(ivy)["Second"][5] == "Quote"
          and sha(hazel) == shas[hazel] and sha(juniper) == shas[juniper]
          and [r["case"] for r in done.get("refused", [])] == ["Juniper"] and len(progress_edits(ivy)) == 2,
          err or json.dumps(done)[:400])

    # 6. MCP's tool and the route run the same op
    lark = make_workbook(root, "Lark", "Key quotes")
    lark_sha = sha(lark)
    srv = mcp_server.Server(str(root), config=str(config_file))

    def call(**given):
        return srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                       "params": {"name": "quote_heading", "arguments": given}}))["result"]

    got = call(case="Lark", request="Head it Quote", dry_run=True)
    dry_ok = got["isError"] is False and support.plain(got["structuredContent"])["renamed"] == 2 and sha(lark) == lark_sha
    got = call(case="Lark", request="Head it Quote")
    check("257: MCP's quote_heading dry-runs and then renames, as the command line does",
          dry_ok and got["isError"] is False and headings(lark)["Initial"][5] == "Quote" and len(progress_edits(lark)) == 2,
          json.dumps(got)[:400])
    wren = make_workbook(root, "Wren", "Key quotes")
    wren_sha = sha(wren)
    kept_root = server_mod.ROOT_OVERRIDE
    server_mod.ROOT_OVERRIDE = str(root)
    try:
        answer = routes.api_quote_heading({"path": str(wren), "dry_run": True})
        ok = answer["dry_run"] is True and sha(wren) == wren_sha
        answer = routes.api_quote_heading({"path": str(wren)})
    finally:
        server_mod.ROOT_OVERRIDE = kept_root
    check("257: the route renames it too, with no agent's mark on the record",
          ok and answer["changed"] is True and headings(wren)["Second"][5] == "Quote"
          and all("by" not in e for e in progress_edits(wren)), json.dumps(answer)[:300])
