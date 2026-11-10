from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import openpyxl

import rounds as rounds_mod
import workbook as wb_mod
from workbook import WorkbookError

from . import support
from .support import (
    DEMO_SHEET, add_second_sheet, check, compare_workbooks, demo_copy, demo_sheet, max_row, row_cells,
    sheet_signature, skip,
)
import idiograph_routes


def full_sidecar(path):
    """Everything in the sidecar that names a row, the edit records whole, and the assignments."""
    p = rounds_mod.load_progress(path)
    return {"rows": p["rows"], "flags": p["flags"], "last": p["last"], "edits": p["edits"],
            "assignments": p["assignments"]}


def test_untrim(scratch):
    print("\n35. A trim undone and done again")
    import server as server_mod

    root = scratch / "untrim"
    saved_root = server_mod.ROOT_OVERRIDE
    server_mod.ROOT_OVERRIDE = str(root)
    try:
        _untrim_checks(scratch, root, server_mod)
    finally:
        server_mod.ROOT_OVERRIDE = saved_root


def _untrim_checks(scratch, root, server_mod):
    trim_api, rows_api = idiograph_routes.api_trim, idiograph_routes.api_rows

    # ── A. a cut at the front, and its undo, through the endpoints
    work = add_second_sheet(demo_copy(root, "front", "Juno - EN & ES.xlsx"))
    keep = root / "front" / "untouched.xlsx"
    shutil.copy2(work, keep)
    progress = rounds_mod.load_progress(work)
    progress["rows"] = {"Initial:3": "has-content", "Initial:5": "reviewed-empty", "Initial:9": "has-content",
                        "Initial:40": "reviewed-empty", "2d:5": "has-content"}
    progress["flags"] = ["Initial:40", "Initial:3", "2d:5", "Initial:9"]
    progress["last"] = {"sheet": DEMO_SHEET, "row": 5}
    rounds_mod.record_edit(progress, DEMO_SHEET, 3, "old words", "new words")
    rounds_mod.record_edit(progress, DEMO_SHEET, 40, "old", "new")
    rounds_mod.save_progress(work, progress)
    side_before = full_sidecar(work)
    sig_before = sheet_signature(keep, DEMO_SHEET)
    other_before = sheet_signature(keep, "2d")

    cut = trim_api({"path": str(work), "sheet": DEMO_SHEET, "row": 7, "direction": "before",
                    "current": {"sheet": DEMO_SHEET, "row": 9}})
    record = rounds_mod.load_progress(work)["trims"][-1]
    check("a trim answers with its record: an id, the sheet, the direction, the rows cut and the backup",
          bool(re.fullmatch(r"[0-9a-f]{12}", cut.get("id") or "")) and cut["id"] == record["id"]
          and (cut["sheet"], cut["direction"], cut["row"]) == (DEMO_SHEET, "before", 7)
          and (cut["first"], cut["last"], cut["count"], cut["removed"]) == (2, 7, 6, 6)
          and cut["backup"] == record["backup"] and "(pre-trim " in cut["backup"]
          and Path(server_mod.abs_path(cut["backup"])).exists(),
          f"rows {cut.get('first')} to {cut.get('last')}")
    check("the record says it is not undone, and keeps what the sidecar said to itself",
          cut["undone"] is False and record["undone"] is False and "sidecar" not in cut
          and record["sidecar"]["rows"] == {"Initial:3": "has-content", "Initial:5": "reviewed-empty"}
          and record["sidecar"]["last"] == {"sheet": DEMO_SHEET, "row": 5},
          str(sorted(k for k in cut if k != "land")))
    check("the page lands on the turn it was on, moved up with the rows", cut["land"] == {"sheet": DEMO_SHEET, "row": 3},
          str(cut["land"]))
    after_front = root / "front" / "after-trim.xlsx"
    shutil.copy2(work, after_front)

    back = rows_api({"op": "untrim", "path": str(work), "id": cut["id"],
                     "current": {"sheet": DEMO_SHEET, "row": 3}})
    problems, checked = compare_workbooks(keep, work, allowed=set())
    check("undo puts the cut rows back, identical under compare_workbooks", not problems,
          f"{checked} cells compared, {len(problems)} differences")
    for p in problems[:3]:
        print(f"        {p}")
    check("and the sheet as a whole: values, runs, fills, widths, heights, freeze pane and zoom",
          sheet_signature(work, DEMO_SHEET) == sig_before and sig_before[1] == [])
    check("the other sheet is untouched", sheet_signature(work, "2d") == other_before)
    check("the sidecar is back as it was: states, flags in their order, edit records and the last turn",
          full_sidecar(work) == side_before, str(full_sidecar(work)["flags"]))
    record = rounds_mod.load_progress(work)["trims"][-1]
    check("the trim record is kept and marked undone", record["undone"] is True and bool(record.get("undone_when")))
    check("undo lands on the turn the page is on, moved back down with the rows",
          back["land"] == {"sheet": DEMO_SHEET, "row": 9} and back["restored"] == 6, str(back["land"]))
    try:
        rows_api({"op": "untrim", "path": str(work), "id": cut["id"]})
        check("a trim is undone once", False, "it restored twice")
    except WorkbookError as exc:
        check("a trim is undone once", "already been undone" in str(exc), str(exc))
    try:
        rows_api({"op": "untrim", "path": str(work), "id": "000000000000"})
        check("an id the progress file does not hold is refused", False, "it restored")
    except WorkbookError as exc:
        check("an id the progress file does not hold is refused", "no record of that trim" in str(exc), str(exc))

    # redo is a fresh trim with the same sheet, row and direction, and a backup of its own
    again = trim_api({"path": str(work), "sheet": DEMO_SHEET, "row": 7, "direction": "before",
                      "current": {"sheet": DEMO_SHEET, "row": 9}})
    check("redo re-applies the trim: the workbook reads as it did after the first cut",
          not compare_workbooks(after_front, work, allowed=set())[0]
          and again["id"] != cut["id"] and again["backup"] != cut["backup"] and again["count"] == 6,
          Path(again["backup"]).name.split("(", 1)[1])
    rows_api({"op": "untrim", "path": str(work), "id": again["id"]})
    check("and undoing the redo puts the rows back again",
          not compare_workbooks(keep, work, allowed=set())[0] and full_sidecar(work) == side_before)

    # ── B. a statement written on a surviving row since the trim is kept
    since = demo_copy(root, "since", "Juno - EN & ES.xlsx")
    skeep = root / "since" / "untouched.xlsx"
    shutil.copy2(since, skeep)
    cut = trim_api({"path": str(since), "sheet": DEMO_SHEET, "row": 7, "direction": "before",
                    "current": {"sheet": DEMO_SHEET, "row": 3}})
    check("a turn that went with the cut lands on the first row left", cut["land"] == {"sheet": DEMO_SHEET, "row": 2},
          str(cut["land"]))
    had = row_cells(skeep, DEMO_SHEET, 11)[3][0]
    idiograph_routes.api_commit({"path": str(since), "sheet": DEMO_SHEET, "row": 5,
                           "es": "\n".join(had + ["A statement written after the cut"])})
    rows_api({"op": "untrim", "path": str(since), "id": cut["id"]})
    problems, _ = compare_workbooks(skeep, since, allowed={(DEMO_SHEET, 11, 3)})
    check("a statement saved on a surviving row since the trim stays on that row through the undo",
          row_cells(since, DEMO_SHEET, 11)[3][0] == had + ["A statement written after the cut"] and not problems,
          f"{len(problems)} other differences")
    side = rounds_mod.load_progress(since)
    check("and its state and the last turn saved move back down with it",
          side["rows"] == {"Initial:11": "has-content"} and side["last"] == {"sheet": DEMO_SHEET, "row": 11},
          f"{side['rows']} {side['last']}")

    # ── C. two cuts from the top, the way he made them, undone in order
    twice = demo_copy(root, "twice", "Juno - EN & ES.xlsx")
    tkeep = root / "twice" / "untouched.xlsx"
    shutil.copy2(twice, tkeep)
    progress = rounds_mod.load_progress(twice)
    progress["last"] = {"sheet": DEMO_SHEET, "row": 3}
    progress["rows"] = {"Initial:3": "has-content", "Initial:13": "has-content"}
    progress["flags"] = ["Initial:13", "Initial:5"]
    rounds_mod.save_progress(twice, progress)
    tside = full_sidecar(twice)
    one = trim_api({"path": str(twice), "sheet": DEMO_SHEET, "row": 3, "direction": "before",
                    "current": {"sheet": DEMO_SHEET, "row": 3}})
    after_one = root / "twice" / "after-one.xlsx"
    shutil.copy2(twice, after_one)
    two = trim_api({"path": str(twice), "sheet": DEMO_SHEET, "row": 5, "direction": "before",
                    "current": {"sheet": DEMO_SHEET, "row": 3}})
    after_two = root / "twice" / "after-two.xlsx"
    shutil.copy2(twice, after_two)
    check("two cuts from the top take 2 rows and then 4",
          (one["first"], one["last"], two["first"], two["last"]) == (2, 3, 2, 5)
          and max_row(twice, DEMO_SHEET) == max_row(tkeep, DEMO_SHEET) - 6)
    try:
        rows_api({"op": "untrim", "path": str(twice), "id": one["id"]})
        check("the first cut cannot be undone while the second stands", False, "it restored")
    except WorkbookError as exc:
        check("the first cut cannot be undone while the second stands, and nothing is written",
              "later trim on this sheet" in str(exc) and not compare_workbooks(after_two, twice, allowed=set())[0],
              str(exc))
    rows_api({"op": "untrim", "path": str(twice), "id": two["id"]})
    check("undoing the second cut leaves the sheet as the first cut left it",
          not compare_workbooks(after_one, twice, allowed=set())[0])
    rows_api({"op": "untrim", "path": str(twice), "id": one["id"]})
    problems, checked = compare_workbooks(tkeep, twice, allowed=set())
    check("undoing the first puts the sheet back identical", not problems,
          f"{checked} cells compared, {len(problems)} differences")
    check("and the sidecar with it", full_sidecar(twice) == tside, str(full_sidecar(twice)))
    first_again = trim_api({"path": str(twice), "sheet": DEMO_SHEET, "row": 3, "direction": "before"})
    second_again = trim_api({"path": str(twice), "sheet": DEMO_SHEET, "row": 5, "direction": "before"})
    check("redo re-applies both cuts in order",
          not compare_workbooks(after_two, twice, allowed=set())[0]
          and len({one["id"], two["id"], first_again["id"], second_again["id"]}) == 4)

    # ── D. a cut at the back, with an edit record on a row it takes
    tail = demo_copy(root, "tail", "Juno - EN & ES.xlsx")
    lkeep = root / "tail" / "untouched.xlsx"
    shutil.copy2(tail, lkeep)
    progress = rounds_mod.load_progress(tail)
    progress["rows"] = {"Initial:9": "has-content", "Initial:71": "reviewed-empty"}
    progress["flags"] = ["Initial:75", "Initial:9"]
    progress["last"] = {"sheet": DEMO_SHEET, "row": 77}
    rounds_mod.record_edit(progress, DEMO_SHEET, 72, "old words", "new words")
    rounds_mod.save_progress(tail, progress)
    lside = full_sidecar(tail)
    total = max_row(lkeep, DEMO_SHEET)
    back_cut = trim_api({"path": str(tail), "sheet": DEMO_SHEET, "row": 70, "direction": "after",
                         "current": {"sheet": DEMO_SHEET, "row": 77}})
    mid = rounds_mod.load_progress(tail)
    check("a cut at the back takes the turn and everything after it, and lands on the last turn left",
          (back_cut["first"], back_cut["last"], back_cut["count"]) == (70, total, total - 69)
          and back_cut["land"] == {"sheet": DEMO_SHEET, "row": 70} and mid["edits"][0].get("cut") is True,
          str(back_cut["land"]))
    rows_api({"op": "untrim", "path": str(tail), "id": back_cut["id"]})
    check("its undo puts the end of the sheet back identical, and the sidecar with it",
          not compare_workbooks(lkeep, tail, allowed=set())[0] and full_sidecar(tail) == lside
          and "cut" not in rounds_mod.load_progress(tail)["edits"][0], str(full_sidecar(tail)["edits"][0].get("row")))

    # ── E. an assignment and then a trim, undone newest first
    both = demo_copy(root, "both", "Juno - EN & ES.xlsx")
    bkeep = root / "both" / "untouched.xlsx"
    shutil.copy2(both, bkeep)
    _, her, him = demo_sheet(both)
    progress = rounds_mod.load_progress(both)
    progress["rows"] = {"Initial:13": "has-content", "Initial:15": "reviewed-empty"}
    progress["flags"] = ["Initial:15"]
    rounds_mod.save_progress(both, progress)
    bside = full_sidecar(both)
    given = rows_api({"op": "assign", "path": str(both), "sheet": DEMO_SHEET, "row": 13, "to": him})
    shaved = trim_api({"path": str(both), "sheet": DEMO_SHEET, "row": 3, "direction": "before"})
    rows_api({"op": "untrim", "path": str(both), "id": shaved["id"]})
    rows_api({"op": "restore", "path": str(both), "id": given["id"]})
    problems, _ = compare_workbooks(bkeep, both, allowed=set())
    check("an assignment made before a trim still undoes once the trim is undone",
          not problems, f"{given['kind']}, {len(problems)} differences")
    now = full_sidecar(both)
    check("and the sidecar comes back as it was, the assignment record marked undone",
          {k: v for k, v in now.items() if k != "assignments"} == {k: v for k, v in bside.items() if k != "assignments"}
          and [a["undone"] for a in now["assignments"]] == [True], str(now["rows"]))

    # ── F. refused when the rows beside the cut have changed some other way
    moved = demo_copy(root, "moved", "Juno - EN & ES.xlsx")
    cut = trim_api({"path": str(moved), "sheet": DEMO_SHEET, "row": 3, "direction": "before"})
    wb_mod.edit_turn(moved, DEMO_SHEET, 2, "Words typed into this row in Excel.")
    changed = root / "moved" / "changed.xlsx"
    shutil.copy2(moved, changed)
    try:
        rows_api({"op": "untrim", "path": str(moved), "id": cut["id"]})
        check("an undo beside rows changed some other way is refused", False, "it restored")
    except WorkbookError as exc:
        check("an undo beside rows changed some other way is refused, with nothing written",
              "changed since the trim" in str(exc) and not compare_workbooks(changed, moved, allowed=set())[0]
              and rounds_mod.load_progress(moved)["trims"][-1]["undone"] is False, str(exc))

    # ── G. heights, the lock, the header, and the one save path
    tall = root / "tall" / "heights.xlsx"
    tall.parent.mkdir(parents=True, exist_ok=True)
    book = openpyxl.Workbook()
    ws = book.active
    ws.title = DEMO_SHEET
    for col, head in zip("ABCDEF", wb_mod.HEADER):
        ws[f"{col}1"] = head
    for r in range(2, 10):
        ws.cell(r, 1, "Him" if r % 2 else "Her")
        ws.cell(r, 2, f"00:0{r}:00")
        ws.cell(r, 4, f"row {r}")
        ws.row_dimensions[r].height = 10 + r
    book.save(tall)
    book.close()
    hkeep = root / "tall" / "untouched.xlsx"
    shutil.copy2(tall, hkeep)
    done = wb_mod.trim_rows(tall, DEMO_SHEET, 4, "before")
    wb_mod.restore_trim(tall, DEMO_SHEET, done["first"], done["removed"], done["backup"])
    check("custom row heights come back on the rows they belong to",
          sheet_signature(tall, DEMO_SHEET) == sheet_signature(hkeep, DEMO_SHEET),
          str(sheet_signature(tall, DEMO_SHEET)[3]))
    done = wb_mod.trim_rows(tall, DEMO_SHEET, 6, "after")
    lock = wb_mod.lock_file(tall)
    lock.write_bytes(b"pretend Excel lock")
    try:
        wb_mod.restore_trim(tall, DEMO_SHEET, done["first"], done["removed"], done["backup"])
        check("an undo refuses a workbook Excel has open", False, "it wrote to it")
    except WorkbookError as exc:
        check("an undo refuses a workbook Excel has open", "Close it in Excel first" in str(exc), str(exc))
    lock.unlink()
    try:
        wb_mod.restore_trim(tall, DEMO_SHEET, 1, 2, done["backup"])
        check("a trim's undo never restores over the header row", False, "it did")
    except WorkbookError as exc:
        check("a trim's undo never restores over the header row", "header row" in str(exc), str(exc))
    wb_mod.restore_trim(tall, DEMO_SHEET, done["first"], done["removed"], done["backup"])
    check("a cut at the back of a sheet with heights comes back identical",
          sheet_signature(tall, DEMO_SHEET) == sheet_signature(hkeep, DEMO_SHEET))

    # ── H. the page
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")

    def fn(name):
        return js.split(f"function {name}(", 1)[1].split("\n}", 1)[0]

    runner, restorer = fn("runTrim"), fn("trimRestore")
    check("a trim pushes an undo entry and no longer clears the stack",
          "undoClear()" not in runner and "undoPush(entry);" in runner
          and "undo: (e) => trimRestore(e)," in runner and "redo: (e) => trimRedo(e)," in runner
          and "anywhere: true" in runner)
    check("Cmd + Z calls the restore and reopens the case in place, on the turn he was on",
          "op: 'untrim'" in restorer and "await reloadInPlace(land);" in restorer
          and "entry.here && here && here.key === entry.landed ? entry.here : data.land" in restorer)
    check("Cmd + Shift + Z re-applies the trim with a fresh call",
          "await trimApply(entry);" in fn("trimRedo") and "...entry.req" in fn("trimApply")
          and "'/api/trim'" in fn("trimApply"))
    check("a server without the restore op says restart and does nothing else",
          "if (!id) throw new Error(RESTART_LINE);" in restorer
          and restorer.index("throw new Error(RESTART_LINE)") < restorer.index("commit(")
          and "needsRestart(err) || refusedAs(err, 'unknown_op') ? RESTART_LINE : err.message" in restorer
          and "const RESTART_LINE = t('shell.restart_line');" in js)

    node = shutil.which("node")
    if not node:
        return skip("the trim lines in node", "no node on this machine")
    import subprocess
    script = scratch / "untrim-lines.js"
    # the key named by keyName since 17 October (area 158), as this machine names it
    script.write_text(support.i18n_js() +
        "const MAC = true;\n"
        + "const keyName = " + js.split("const keyName = ", 1)[1].split(";\n", 1)[0] + ";\n"
        + "\n".join(f"function {name}(" + fn(name) + "\n}" for name in ("trimLine", "trimShort", "trimmedLine"))
        + "\nconst spans = [\n"
        "  { direction: 'before', count: 4, from: '00:00', to: '01:35' },\n"
        "  { direction: 'after', count: 12, from: '13:12', to: '14:09' },\n"
        "  { direction: 'before', count: 2, from: '00:00', to: '00:14' },\n"
        "  { direction: 'after', count: 1, from: '22:21', to: '22:21' },\n"
        "];\n"
        "console.log(JSON.stringify({ lines: spans.map(trimLine), short: spans.map(trimShort),\n"
        "  said: [trimmedLine({ removed: 4, id: 'a' }), trimmedLine({ removed: 1, id: 'a' }), trimmedLine({ removed: 4 })] }));\n",
        encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("the trim lines run in node", False, run.stderr.strip()[:200])
    out = json.loads(run.stdout)
    check("the card says a cut before plainly",
          out["lines"][0] == "Cut 4 rows: this passage and the 3 before it, 00:00 to 01:35.", out["lines"][0])
    check("the card says a cut after plainly",
          out["lines"][1] == "Cut 12 rows: this passage and the 11 after it, 13:12 to 14:09.", out["lines"][1])
    check("the line after a trim names Cmd + Z, and only when the server can undo it",
          out["said"] == ["4 rows cut. Cmd + Z puts them back.", "1 row cut. Cmd + Z puts it back.", "4 rows cut."],
          str(out["said"]))
