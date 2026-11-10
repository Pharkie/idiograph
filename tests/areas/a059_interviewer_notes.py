from __future__ import annotations

import inspect
import json
import shutil

import openpyxl

import export as export_mod
import rounds as rounds_mod
import workbook as wb_mod
from workbook import WorkbookError

from . import support
from .support import (
    DEMO_SHEET, add_second_sheet, check, compare_workbooks, demo_copy, demo_sheet, skip, slashed,
)
import idiograph_routes


def column_g(path, sheet=DEMO_SHEET, col=7):
    """The rows of one column that hold anything, and the sheet's widest column."""
    book = openpyxl.load_workbook(path, rich_text=True)
    ws = book[sheet]
    # the width first, because asking openpyxl for a cell past it makes one
    width = ws.max_column
    held = [r for r in range(1, ws.max_row + 1) if col <= width and ws.cell(r, col).value is not None]
    book.close()
    return held, width


def test_interviewer_notes(scratch):
    print("\n59. Interviewer notes: a note on the interviewer's turns, in a column of its own (140)")
    import datetime as dt
    import subprocess
    import server as server_mod
    import themes as themes_mod

    page = support.page_text()
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    style = support.text("family/static/style.css", "apps/idiograph/static/distil.css")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0]

    # ── A. the column: added on first use, in the first empty header cell, found by its header after
    root = scratch / "interviewer-notes"
    untouched = demo_copy(root, "before", "Juno - EN & ES.xlsx")
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    sheet, her, him = demo_sheet(work)
    his = [r["row"] for r in sheet["rows"] if r["name"] == him]
    hers = [r["row"] for r in sheet["rows"] if r["name"] == her]
    first, second = his[1], his[3]
    case = wb_mod.read_case(work)
    check("140: a sheet with no Interviewer notes column reads every note as empty",
          all(r["note"] == "" for s in case["sheets"] for r in s["rows"])
          and "note" not in case["sheets"][0]["columns"])
    check("140: the role is found by a header that names interviewer notes, and by no other",
          wb_mod.ROLE_TESTS["note"]("interviewer notes") and wb_mod.ROLE_TESTS["note"]("my interviewer note")
          and not wb_mod.ROLE_TESTS["note"]("exploratory notes") and not wb_mod.ROLE_TESTS["note"]("notes")
          and "G" not in wb_mod.WIDTHS and wb_mod.HEADER[-1] == "Quote" and wb_mod.NOTE_WIDTH == 42.0)
    nothing = wb_mod.save_interviewer_note(work, DEMO_SHEET, first, "  \n ", him)
    check("140: an empty note on a sheet with no column writes nothing and adds no column",
          nothing["changed"] is False and work.read_bytes() == untouched.read_bytes())

    wrote = wb_mod.save_interviewer_note(work, DEMO_SHEET, first, "Moved her on too soon\n\n  ", him)
    book = openpyxl.load_workbook(work, rich_text=True)
    ws = book[DEMO_SHEET]
    head, cell = ws.cell(1, 7), ws.cell(first, 7)
    check("140: the first note adds the heading in the first empty header cell, G in the standard layout, in the header font",
          head.value == "Interviewer notes" and ws.max_column == 7 and head.font.b and head.font.name == "Calibri"
          and head.font.sz == 11 and ws.cell(1, 8).value is None)
    check("140: the column takes a width of 42",
          ws.column_dimensions["G"].width == 42.0 and ws.column_dimensions["G"].customWidth)
    check("140: the note lands in its row's cell in the body font, wrapped and top-aligned, its blank lines dropped",
          cell.value == "Moved her on too soon" and cell.font.name == "Calibri" and cell.font.sz == 11
          and not cell.font.b and cell.alignment.wrap_text and cell.alignment.vertical == "top"
          and wrote == {"row": first, "sheet": DEMO_SHEET, "text": "Moved her on too soon", "changed": True,
                    "old": ""})
    check("140: no cell anywhere gains a fill",
          all(c.fill is None or c.fill.fill_type is None for row in ws.iter_rows() for c in row))
    book.close()
    problems, checked = compare_workbooks(untouched, work, {(DEMO_SHEET, 1, 7), (DEMO_SHEET, first, 7)})
    others = [p for p in problems if not p.startswith((f"{DEMO_SHEET}: shape", f"{DEMO_SHEET}: column widths"))]
    a, b = openpyxl.load_workbook(untouched), openpyxl.load_workbook(work)
    widths_a = {k: v.width for k, v in a[DEMO_SHEET].column_dimensions.items()}
    widths_b = {k: v.width for k, v in b[DEMO_SHEET].column_dimensions.items()}
    same_frame = (a[DEMO_SHEET].freeze_panes == b[DEMO_SHEET].freeze_panes
                  and a[DEMO_SHEET].sheet_view.zoomScale == b[DEMO_SHEET].sheet_view.zoomScale
                  and a[DEMO_SHEET].max_row == b[DEMO_SHEET].max_row)
    a.close(); b.close()
    check("140: every other cell is as it was, by the cell-by-cell comparison, run by run",
          not others and checked > 400, f"{checked} cells compared, {len(others)} differences " + "; ".join(others[:2]))
    check("140: the widths, the freeze panes and the zoom are as they were, with G added at 42 and nothing else in G",
          widths_b == {**widths_a, "G": 42.0} and same_frame and column_g(work) == ([1, first], 7), str(widths_b))

    wb_mod.save_interviewer_note(work, DEMO_SHEET, second, "A question, not a lead\nShould have waited", him)
    case = wb_mod.read_case(work)
    rows = {r["row"]: r for r in case["sheets"][0]["rows"]}
    check("140: the next note finds the column by its header, and no second heading is added",
          column_g(work) == ([1, first, second], 7) and case["sheets"][0]["columns"].get("note") == 7)
    check("140: read_case carries the note on every row, its lines joined as the three fields' are",
          all("note" in r for r in rows.values()) and rows[first]["note"] == "Moved her on too soon"
          and rows[second]["note"] == "A question, not a lead\nShould have waited"
          and sum(1 for r in rows.values() if r["note"]) == 2)
    book = openpyxl.load_workbook(work, rich_text=True)
    stored = book[DEMO_SHEET].cell(second, 7).value
    book.close()
    check("140: a note of two lines is kept as two entries with a blank line between, as the three fields keep theirs",
          stored == "A question, not a lead\n\nShould have waited", repr(stored))
    held = work.read_bytes()
    same = wb_mod.save_interviewer_note(work, DEMO_SHEET, second, "  A question, not a lead \n\n\nShould have waited", him)
    check("140: the same text writes nothing at all, not one byte", same["changed"] is False and work.read_bytes() == held)
    gone = wb_mod.save_interviewer_note(work, DEMO_SHEET, second, "", him)
    check("140: an empty note clears the cell to nothing, and the heading stays",
          gone["changed"] is True and gone["text"] == "" and column_g(work) == ([1, first], 7))

    held = work.read_bytes()
    refusals = []
    for target, text in ((hers[0], "Not hers"), (1, "The header"), (900, "Past the end")):
        try:
            wb_mod.save_interviewer_note(work, DEMO_SHEET, target, text, him)
            refusals.append(None)
        except WorkbookError as exc:
            refusals.append(str(exc))
    check("140: a participant's row is refused with its line, and nothing is written",
          refusals[0] == "Interviewer notes belong to the interviewer's passages." and work.read_bytes() == held, str(refusals[0]))
    check("140: the header row is never edited, and a row past the end is refused too",
          refusals[1] == "The header row is never edited." and refusals[2] == wb_mod.NOT_INTERVIEWER
          and work.read_bytes() == held, str(refusals[1:]))
    lock = wb_mod.lock_file(work)
    lock.write_bytes(b"pretend Excel lock")
    try:
        wb_mod.save_interviewer_note(work, DEMO_SHEET, first, "While Excel has it", him)
        locked = None
    except WorkbookError as exc:
        locked = str(exc)
    lock.unlink()
    check("140: a workbook Excel has open is refused with the turn screen's line, and nothing is written",
          locked is not None and "Close it in Excel first" in locked and work.read_bytes() == held, str(locked))

    # a second sheet takes its own column on its first note, and a header already there is used
    two = demo_copy(root, "two", "Juno - EN & ES.xlsx")
    add_second_sheet(two, "2d")
    wb_mod.save_interviewer_note(two, DEMO_SHEET, first, "On the first sheet", him)
    check("140: a note on one sheet adds the column to that sheet alone",
          column_g(two) == ([1, first], 7) and column_g(two, "2d") == ([], 6))
    wb_mod.save_interviewer_note(two, "2d", 3, "On the second sheet", him)
    book = openpyxl.load_workbook(two, rich_text=True)
    second_head = book["2d"].cell(1, 7).value
    second_width = book["2d"].column_dimensions["G"].width
    book.close()
    check("140: a second sheet gets its own column on its first note, heading and width",
          column_g(two, "2d") == ([1, 3], 7) and second_head == "Interviewer notes" and second_width == 42.0
          and column_g(two) == ([1, first], 7))
    elsewhere = demo_copy(root, "elsewhere", "Juno - EN & ES.xlsx")
    book = openpyxl.load_workbook(elsewhere, rich_text=True)
    book[DEMO_SHEET].cell(1, 10).value = "Interviewer notes (Adam)"
    book.save(elsewhere)
    book.close()
    wb_mod.save_interviewer_note(elsewhere, DEMO_SHEET, first, "Where the header already was", him)
    check("140: a workbook that already carries the header elsewhere in the first twelve columns uses it",
          column_g(elsewhere, col=10) == ([1, first], 10) and column_g(elsewhere) == ([], 10)
          and wb_mod.read_case(elsewhere)["sheets"][0]["rows"][first - 2]["note"] == "Where the header already was")
    full = demo_copy(root, "full", "Juno - EN & ES.xlsx")
    book = openpyxl.load_workbook(full, rich_text=True)
    for c in range(7, 13):
        book[DEMO_SHEET].cell(1, c).value = f"Column {c}"
    book.save(full)
    book.close()
    held = full.read_bytes()
    try:
        wb_mod.save_interviewer_note(full, DEMO_SHEET, first, "No room", him)
        crowded = None
    except WorkbookError as exc:
        crowded = str(exc)
    check("140: a sheet whose first twelve headers are all used is refused rather than given a column no read finds",
          crowded is not None and "no room" in crowded and full.read_bytes() == held, str(crowded))

    # ── B. never a stop, never counted: the rounds, the states and the summary as they were
    plain = wb_mod.read_case(untouched)
    noted = wb_mod.read_case(work)
    progress = rounds_mod.load_progress(work)
    strip = lambda sheets: [[{k: v for k, v in r.items() if k != "note"} for r in s["rows"]] for s in sheets]
    rb = rounds_mod.build_rounds(plain["sheets"], 10, him)
    ra = rounds_mod.build_rounds(noted["sheets"], 10, him)
    noted_rows = [r for s in noted["sheets"] for r in s["rows"] if r["note"]]
    check("140: a turn carrying a note is never a stop",
          noted_rows and not any(rounds_mod.is_stop(r, him) for r in noted_rows))
    check("140: the rounds, the row states and the summary are the same with notes present",
          json.dumps(rb, default=str) == json.dumps(ra, default=str)
          and rounds_mod.row_states(plain["sheets"], progress, him) == rounds_mod.row_states(noted["sheets"], progress, him)
          and json.dumps(rounds_mod.summary(plain["sheets"], progress, rb, him, 2), default=str, sort_keys=True)
          == json.dumps(rounds_mod.summary(noted["sheets"], progress, ra, him, 2), default=str, sort_keys=True)
          and strip(plain["sheets"]) == strip(noted["sheets"]))

    # ── C. the route
    routed = demo_copy(root, "route", "Juno", "Juno - EN & ES.xlsx")
    rounds_mod.save_progress(routed, rounds_mod.load_progress(routed))
    side = rounds_mod.progress_path(routed)
    side_before = side.read_bytes()
    saved = (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_MEMORY = {"recent": []}
    try:
        check("140: the route is there, and takes the interviewer named in the settings",
              server_mod.ROUTES.get("/api/interviewer-note") is idiograph_routes.api_interviewer_note
              and server_mod.config()["interviewer"].strip().lower() == him.strip().lower()
              and 'config()["interviewer"]' in inspect.getsource(idiograph_routes.api_interviewer_note)
              and "with writing(path):" in inspect.getsource(idiograph_routes.api_interviewer_note))
        answer = idiograph_routes.api_interviewer_note({"path": str(routed), "sheet": DEMO_SHEET, "row": first,
                                                  "text": "Moved her on\nToo soon"})
        check("140: the answer carries the row, the sheet, the text as written and changed, and nothing else",
              answer == {"sheet": DEMO_SHEET, "row": first, "text": "Moved her on\nToo soon", "changed": True}, str(answer))
        check("140: nothing in the progress file changes", side.read_bytes() == side_before)
        try:
            idiograph_routes.api_interviewer_note({"path": str(routed), "sheet": DEMO_SHEET, "row": hers[0], "text": "x"})
            said = None
        except WorkbookError as exc:
            said = str(exc)
        check("140: the route refuses her passage with the line", said == "Interviewer notes belong to the interviewer's passages.")
        payload = idiograph_routes.case_payload(routed)
        carried = {r["row"]: r["note"] for s in payload["sheets"] for r in s["rows"]}
        check("140: the case the page opens carries the note on every row",
              carried[first] == "Moved her on\nToo soon" and all(k in r for s in payload["sheets"] for r in s["rows"] for k in ("note",)))

        # ── D. the export: the CSV unchanged, the notes file only with the tick
        notes_file = export_mod.notes_path(routed)
        plain_csv = idiograph_routes.api_export({"path": str(routed)})
        csv_path = export_mod.output_path(routed)
        csv_bytes = csv_path.read_bytes()
        check("140: with the tick off the export writes the CSV alone and its answer is as it was",
              not notes_file.exists() and "notes" not in plain_csv and "notes_path" not in plain_csv
              and set(plain_csv) == {"path", "statements"})
        ticked = idiograph_routes.api_export({"path": str(routed), "notes": True})
        check("140: with the tick the export also writes <stem> - Interviewer notes.md beside the CSV",
              notes_file.exists() and notes_file.name == "Juno - Interviewer notes.md" and notes_file.parent.name == "Working"
              and ticked["notes"] == 1 and slashed(ticked["notes_path"]).endswith("Working/Juno - Interviewer notes.md")
              and slashed(ticked["path"]).endswith("Working/Juno - All Experiential Statements.csv"), str(ticked))
        check("140: the CSV is the same with the tick as without, statements alone in the reference format",
              csv_path.read_bytes() == csv_bytes and b"Moved her on" not in csv_bytes
              and ticked["statements"] == plain_csv["statements"])
        when = next(r for r in wb_mod.read_case(routed)["sheets"][0]["rows"] if r["row"] == first)["seconds"]
        text = notes_file.read_text(encoding="utf-8")
        today = dt.date.today()
        check("140: the file is the heading, the date, then each note under its timecode as HH:MM:SS",
              text == (f"# Juno: interviewer notes\n\nExported on {today.day} {today.strftime('%B')} {today.year}.\n\n"
                       f"{wb_mod.hhmmss(when)}\nMoved her on\nToo soon\n"), repr(text))
        idiograph_routes.api_interviewer_note({"path": str(routed), "sheet": DEMO_SHEET, "row": second, "text": "A second"})
        made = export_mod.export_notes(routed, "Juno", out=root / "fixed.md", today=dt.date(2026, 10, 3))
        when2 = next(r for r in wb_mod.read_case(routed)["sheets"][0]["rows"] if r["row"] == second)["seconds"]
        check("140: the notes run in transcript order, one blank line between, no sheet heading in a one-sheet workbook",
              (root / "fixed.md").read_text(encoding="utf-8")
              == (f"# Juno: interviewer notes\n\nExported on 3 October 2026.\n\n{wb_mod.hhmmss(when)}\nMoved her on\nToo soon\n\n"
                  f"{wb_mod.hhmmss(when2)}\nA second\n") and made["notes"] == 2 and "## " not in text)
        add_second_sheet(routed, "2d")
        idiograph_routes.api_interviewer_note({"path": str(routed), "sheet": "2d", "row": 3, "text": "On 2d"})
        export_mod.export_notes(routed, "Juno", out=root / "two.md", today=dt.date(2026, 10, 3))
        both = (root / "two.md").read_text(encoding="utf-8")
        check("140: a workbook of more than one sheet heads each sheet's notes with its name, sheet by sheet",
              both.split("\n\n")[2:] == ["## Initial", f"{wb_mod.hhmmss(when)}\nMoved her on\nToo soon",
                                         f"{wb_mod.hhmmss(when2)}\nA second", "## 2d", "00:03:00\nOn 2d\n"], repr(both))
        bare = demo_copy(root, "bare", "Juno - EN & ES.xlsx")
        none = idiograph_routes.api_export({"path": str(bare), "notes": True})
        check("140: a case with no notes writes no file and says so",
              none["notes"] == 0 and none["notes_path"] is None and not export_mod.notes_path(bare).exists())
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = saved

    # ── E. never anywhere else: the CSV above, the cards, the PET draft and the model
    cards = json.dumps(themes_mod.read_cards(routed))
    draft, _ = themes_mod.draft_markdown(routed, "Juno")
    check("140: the notes are in none of the cards, the themes file's source, or the PET draft",
          "Moved her on" not in cards and "A second" not in cards and "Moved her on" not in draft and "On 2d" not in draft)
    check("140: nothing the page sends to a model carries a note",
          "note" not in fn(app, "suggestBody") and ".note" not in fn(app, "askAI") and "noteLines" not in fn(app, "askAI")
          and "interviewer-note" not in support.source("family/ai_suggest.py").read_text(encoding="utf-8")
          and "Interviewer notes" not in support.source("apps/idiograph/themes_ai.py").read_text(encoding="utf-8")
          and '"note"' not in inspect.getsource(themes_mod.read_cards))

    # ── F. the page
    click = app.split("$('transcript').addEventListener('click', (e) => {", 1)[1].split("\n  });", 1)[0]
    check("140: a plain click on one of his turns cues the recording, marks the row and opens the note",
          "cueAudio(row.seconds);\n    markTurn(row.i);" in click and "if (noteable(row)) { openNote(row); return; }" in click
          and click.index("markTurn(row.i);") < click.index("openNote(row)")
          and "row.stop" in fn(app, "noteable") and "row.note === undefined" in fn(app, "noteable"))
    keydown = support.keydown_text(app)
    check("140: Cmd + Enter and the button keep it, and the button reads Next with the tick, as on her turns",
          "const pressAct = () => (S.note ? keepNote(true) :" in app
          and "const act = S.note ? 'next' : turnAct();" in fn(app, "drawAct")
          and "const title = keyName(t('distil.act.title_keys', { title: S.note ? NOTE_ACT_TITLE : ACT[act].title }));" in fn(app, "drawAct")
          and "word: 'Keep'" not in app and 'data-for="keep"' not in page and 'data-act="keep"' not in style)
    check("140: Esc goes back to the three fields with nothing written",
          "if (S.note) { e.preventDefault(); discardNote(); return; }" in keydown
          and "api(" not in fn(app, "discardNote") and "closeNote();" in fn(app, "discardNote"))
    check("140: any move keeps it, and so does a click away, a field typed into saved on the way as before",
          "if (S.note) keepNote();" in fn(app, "goTo") and "if (S.note) keepNote();" in fn(app, "drawTurn")
          and "if (S.note && !e.target.closest('#note-entry, .turn.noting, #player-wrap, #btn-commit')" in app
          and "return commit(leaving, false)" in fn(app, "goTo"))
    check("140: keeping a note is one entry on the stack, its row and the old and the new text, reversed through the same route",
          "undo: (e) => noteBack(e.key, e.was)," in fn(app, "pushNoteUndo") and "redo: (e) => noteBack(e.key, e.now)," in fn(app, "pushNoteUndo")
          and "'/api/interviewer-note'" in fn(app, "noteApply") and "openNote(row, row.note || '');" in fn(app, "noteBack")
          and "el.id !== 'note'" in fn(app, "nativeUndoOwns") and "await keepBeforeUndo()" in fn(app, "undoStep")
          and "return await keepNote(true);" in fn(app, "keepBeforeUndo"))
    # since settingsplit (5 November 2026) the tick is under Markdown and CSV in the PETs board's Export menu, Settings'
    # Export pane gone
    board = support.text("apps/idiograph/static/themes.js")
    menu = page.split('id="th-xmenu"', 1)[1].split('<div class="th-body">', 1)[0]
    check("140: the PETs board's Export menu has the tick under Markdown and CSV, off by default and remembered under "
          "idiograph-export-notes, and Settings has no Export pane",
          'id="export-notes">' in menu and menu.index('data-xop="export"') < menu.index('id="export-notes"')
          and "checked" not in menu.split('id="export-notes"', 1)[1].split("</label>", 1)[0]
          and 'id="pane-export"' not in page
          and "const EXPORT_NOTES_KEY = 'idiograph-export-notes';" in app
          and "$('export-notes').checked = exportNotesStored();" in app
          and "export-notes" not in fn(app, "saveSettings") and "export-notes" not in fn(app, "openSettings"))
    check("140: Markdown and CSV asks for the notes only with the tick, the statements' own export first, and the notes "
          "file is named with the board's two",
          "!word && $('export-notes') && $('export-notes').checked" in fn(board, "thExport")
          and "await api('/api/export', { path: TH.path, notes: true })" in fn(board, "thExport")
          and fn(board, "thExport").index("'/api/export'") < fn(board, "thExport").index("'/api/themes-export'")
          and "shown.push(`Working/${fileOf(notes.notes_path)}`)" in fn(board, "thExport"))

    node = shutil.which("node")
    if not node:
        skip("140: the note's lines in node", "no node on this machine")
    else:
        script = scratch / "notes-check.js"
        script.write_text(support.i18n_js() +
            "const RESTART_LINE = 'Restart the server to finish this update.';\n"
            "const noteLines = " + app.split("const noteLines = ", 1)[1].split("\n", 1)[0] + "\n"
            "const out = {\n"
            "  lines: noteLines('  Moved her on \\n\\n\\n Too soon  '),\n"
            "  empty: noteLines(' \\n '),\n"
            "};\nconsole.log(JSON.stringify(out));\n", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("140: the note's lines run in node", False, run.stderr.strip()[:300])
        else:
            out = json.loads(run.stdout)
            check("140: in node, a note is compared by its lines, trimmed, the empty ones dropped",
                  out["lines"] == "Moved her on\nToo soon" and out["empty"] == "", str(out))
