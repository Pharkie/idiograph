from __future__ import annotations

import shutil

import rounds as rounds_mod
import workbook as wb_mod
from workbook import WorkbookError

from . import support

from .support import DEMO_SHEET, cell_face, check, compare_workbooks, demo_copy, demo_sheet, orange_runs


def test_edit_turn(scratch):
    print("\n24. Correcting a turn in place, the quote candidate and the disclosures")
    import server as server_mod

    # ── A. the endpoint, on a scratch copy of the demo workbook
    work = demo_copy(scratch, "edit", "Juno - EN & ES.xlsx")
    initial, _, _ = demo_sheet(work)
    target = next(r for r in initial["rows"]
                  if any(x["crux"] for x in r["runs"]) and len(r["text"]) > 120)
    # a second highlight on the same turn, so one dropped by an edit can be told from the rest
    plain = next(x for x in target["runs"] if not x["crux"] and len(x["text"]) > 60)
    second = plain["text"][10:44]
    where = target["text"].index(second)
    wb_mod.save_crux(work, DEMO_SHEET, target["row"], where, where + len(second), second)
    keep = scratch / "edit" / "untouched.xlsx"
    shutil.copy2(work, keep)

    read = wb_mod.read_case(work)
    initial = next(s for s in read["sheets"] if s["name"] == DEMO_SHEET)
    target = next(r for r in initial["rows"] if r["row"] == target["row"])
    marks = [x["text"] for x in target["runs"] if x["crux"]]
    phrase = marks[0]
    original = target["text"]
    face = cell_face(keep, DEMO_SHEET, target["row"])

    lead = "Well, "
    result = wb_mod.edit_turn(work, DEMO_SHEET, target["row"], lead + original)
    check("the corrected text is in the cell",
          result["changed"] and result["text"] == lead + original,
          f"{len(original)} characters to {len(result['text'])}")
    runs = result["runs"]
    first = next(i for i, r in enumerate(runs) if r["crux"])
    at = sum(len(r["text"]) for r in runs[:first])
    check("every highlight is found again, the first one at its new position",
          [r["text"] for r in runs if r["crux"]] == marks
          and at == original.index(phrase) + len(lead),
          f"{len(marks)} runs, the first now at {at}")
    check("nothing was dropped and nothing is reported", result["dropped"] == [])
    check("the cell keeps its style and takes no fill",
          cell_face(work, DEMO_SHEET, target["row"]) == face and face[-1] is None,
          str(face))
    allowed = {(DEMO_SHEET, target["row"], 4)}
    problems, checked = compare_workbooks(keep, work, allowed=allowed)
    check("an edit touches one cell and nothing else", not problems,
          f"{checked} cells compared")
    for p in problems[:3]:
        print(f"        {p}")

    gone = (lead + original).replace(phrase, "words that carry no mark now")
    lost = wb_mod.edit_turn(work, DEMO_SHEET, target["row"], gone)
    check("a highlight whose phrase has gone is dropped and named",
          lost["dropped"] == [phrase]
          and phrase not in [r["text"] for r in lost["runs"] if r["crux"]],
          repr(phrase[:40]))
    check("the highlights whose phrases survived are still there",
          [r["text"] for r in lost["runs"] if r["crux"]] == marks[1:],
          f"{len(marks) - 1} left of {len(marks)}")

    # the round trip undo makes: the same endpoint, with the text it had before
    undo = scratch / "edit" / "undo.xlsx"
    shutil.copy2(keep, undo)
    wb_mod.edit_turn(undo, DEMO_SHEET, target["row"], lead + original)
    back = wb_mod.edit_turn(undo, DEMO_SHEET, target["row"], original)
    check("undo puts the original text back, byte for byte",
          back["text"] == original and back["text"] is not original)
    check("the highlights come back with it, in the fonts they carried",
          [r["text"] for r in back["runs"] if r["crux"]] == marks
          and orange_runs(undo, DEMO_SHEET) == orange_runs(keep, DEMO_SHEET),
          f"{len(orange_runs(undo, DEMO_SHEET))} orange runs on the sheet")
    problems, _ = compare_workbooks(keep, undo, allowed=allowed)
    check("an edit and its undo leave every other cell as it was", not problems,
          f"{len(problems)} differences")

    unchanged = wb_mod.edit_turn(undo, DEMO_SHEET, target["row"], original)
    check("text that has not changed writes nothing at all", unchanged["changed"] is False)

    try:
        wb_mod.edit_turn(work, DEMO_SHEET, target["row"], "   ")
        check("refuses to leave a turn with no text", False, "it emptied it")
    except WorkbookError as exc:
        check("refuses to leave a turn with no text", "no text" in str(exc), str(exc))
    try:
        wb_mod.edit_turn(work, DEMO_SHEET, 1, "Transcript")
        check("the header row is never edited", False, "it edited it")
    except WorkbookError as exc:
        check("the header row is never edited", "header row" in str(exc), str(exc))
    lock = wb_mod.lock_file(work)
    lock.write_bytes(b"pretend Excel lock")
    try:
        wb_mod.edit_turn(work, DEMO_SHEET, target["row"], "anything at all")
        check("refuses a workbook Excel has open", False, "it wrote to it")
    except WorkbookError as exc:
        check("refuses a workbook Excel has open", "Close it in Excel first" in str(exc), str(exc))
    lock.unlink()

    # the sidecar, written by the endpoint the way a trim is written
    progress = rounds_mod.load_progress(work)
    check("a sidecar written before this loads with an empty edits list",
          progress["edits"] == [], str(progress["edits"]))
    rounds_mod.record_edit(progress, DEMO_SHEET, target["row"], original, lead + original)
    rounds_mod.save_progress(work, progress)
    record = rounds_mod.load_progress(work)["edits"][0]
    check("the edit is recorded with both texts and the time it was made",
          record["sheet"] == DEMO_SHEET and record["row"] == target["row"]
          and record["old"] == original and record["new"] == lead + original
          and record["when"],
          f"row {record['row']} at {record['when']}")

    static = server_mod.HERE / "static"
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")

    # ── B. the quote candidate
    check("a plain click that selects nothing clears the pieces and the preview",
          "if (!took && !held && !dragged) clearPending(true);" in js
          and "const dragged = pressMoved(e);" in js,
          "no drag and no modifier, or the selection is his")
    # the page's own handler, not the one the editor's box keeps to itself
    esc = support.keydown_text(js).split("if (typing", 1)[0]
    check("Esc clears the candidate before its other jobs, and only when there is something to clear",
          "if (S.pending.length) { e.preventDefault(); clearPending(true); return; }" in esc
          and esc.index("clearPending(") < esc.index("if (anyOverlayOpen()) {")
          and esc.index("if (anyOverlayOpen()) {") < esc.index("back-to-turn")
          and esc.index("back-to-turn") < esc.index("blur()"))

    # ── C. editing a turn
    opener = js.split("function openEditor(", 1)[1].split("\n}", 1)[0]
    check("e opens the turn being worked on and a double-click opens any turn",
          "else if (key === 'e' && !$('work').hidden)" in js and "openEditor(current())" in js
          and "addEventListener('dblclick'" in js and "openEditor(row)" in js,
          "the interviewer's turns as well as hers")
    check("Cmd + Enter saves and Esc cancels, without either reaching the page behind",
          "(e.metaKey || e.ctrlKey) && e.key === 'Enter'" in opener
          and "e.stopPropagation()" in opener and "saveEdit()" in opener
          and "if (S.editing) { e.preventDefault(); closeEditor(); return; }" in esc)
    check("a double-click no longer feeds the quote builder",
          "if (e.detail >= 2) { S.selecting = false; return; }" in js
          and "sel.removeAllRanges();" in js.split("$('transcript-rows').addEventListener('dblclick'", 1)[1].split("});", 1)[0],
          "the word the browser picked is dropped on the way into the editor")
    check("one turn is open at a time, and a move out cancels it",
          "if (S.editing) closeEditor();" in opener
          and "if (S.editing) closeEditor();" in js.split("function drawTurn(", 1)[1].split("\n}", 1)[0])
    saver = js.split("async function saveEdit(", 1)[1].split("\n}", 1)[0]
    pusher = js.split("function pushEditUndo(", 1)[1].split("\n}", 1)[0]
    check("saving goes through the new endpoint and joins the undo stack",
          "'/api/edit-turn'" in js and "pushEditUndo(row, { text: before }, { text: after });" in saver
          and "undoPush({" in pusher
          and "undo: (e) => editApply(e.key, e.was.text, e.was.time)," in pusher
          and "redo: (e) => editApply(e.key, e.now.text, e.now.time)," in pusher,
          "the same endpoint both ways, so the highlights are re-keyed again")
    check("an undo on one of Adam's turns does not try to go to it",
          "if (row && row.stop && (!current() || current().key !== entry.key)) await goTo(row.pos);" in js,
          "his turns are not stops and have no position to go to")
    check("a server that has not been restarted says so and loses nothing",
          "needsRestart(err) ? RESTART_LINE" in saver and "return;" in saver,
          "the box stays open with his text in it")
