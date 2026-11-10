from __future__ import annotations

import inspect
import json
import shutil
from pathlib import Path

import openpyxl
from openpyxl.cell.rich_text import CellRichText, TextBlock

import rounds as rounds_mod
import workbook as wb_mod
from workbook import WorkbookError

from . import support
from .support import (
    DEMO_SHEET, cell_face, check, compare_workbooks, demo_copy, demo_sheet, max_row, row_cells,
    sheet_signature,
)
import idiograph_routes


def crux_blocks(path, sheet, row):
    """The orange runs of one transcript cell, each with everything its font carries."""
    wb = openpyxl.load_workbook(path, rich_text=True)
    value = wb[sheet].cell(row, 4).value
    wb.close()
    if not isinstance(value, CellRichText):
        return []
    return [(b.text, wb_mod.font_key(b.font)) for b in value
            if isinstance(b, TextBlock) and wb_mod.is_crux_font(b.font)]


def sidecar_view(path):
    """The parts of the sidecar that name rows, which an assignment moves and an undo moves back."""
    p = rounds_mod.load_progress(path)
    return {"rows": p["rows"], "flags": p["flags"], "last": p["last"],
            "edits": [(e["sheet"], e["row"]) for e in p["edits"]]}


def test_assign(scratch):
    print("\n29. Assigning words to another speaker")
    import datetime as dt
    import server as server_mod

    root = scratch / "assign"
    saved_root = server_mod.ROOT_OVERRIDE
    server_mod.ROOT_OVERRIDE = str(root)
    try:
        _assign_checks(scratch, root, server_mod, dt)
    finally:
        server_mod.ROOT_OVERRIDE = saved_root


def _assign_checks(scratch, root, server_mod, dt):
    rows_api = idiograph_routes.api_rows

    # ── A. three rows out of one, with an orange run across the cut
    work = demo_copy(root, "three", "Juno - EN & ES.xlsx")
    keep = root / "three" / "untouched.xlsx"
    shutil.copy2(work, keep)
    initial, her, him = demo_sheet(work)
    src = next(r for r in initial["rows"] if r["name"] == her and any(x["crux"] for x in r["runs"])
               and r["es"].strip() and not r["runs"][-1]["crux"])
    r0, text = src["row"], src["text"]
    phrase = next(x["text"] for x in src["runs"] if x["crux"])
    at = text.index(phrase)
    # from the middle of the word before the highlight to the middle of a word inside it
    sel_start, sel_end = at - 6, at + phrase.index(" ", 8) - 2
    blocks_before = crux_blocks(keep, DEMO_SHEET, r0)
    progress = rounds_mod.load_progress(work)
    progress["rows"] = {f"Initial:{r0}": "has-content", f"Initial:{r0 + 6}": "reviewed-empty"}
    progress["flags"] = [f"Initial:{r0}", f"Initial:{r0 + 6}"]
    progress["last"] = {"sheet": DEMO_SHEET, "row": r0 + 6}
    rounds_mod.record_edit(progress, DEMO_SHEET, r0 + 6, "old words", "new words")
    rounds_mod.save_progress(work, progress)
    side_before = sidecar_view(work)
    sig_before = sheet_signature(keep, DEMO_SHEET)
    total_before = max_row(keep, DEMO_SHEET)

    answer = rows_api({"op": "assign", "path": str(work), "sheet": DEMO_SHEET, "row": r0, "to": him,
                       "start": sel_start, "end": sel_end, "current": {"sheet": DEMO_SHEET, "row": r0 + 6}})
    snapped = wb_mod.snap_words(text, sel_start, sel_end)
    check("the selection snaps outward to whole words",
          (answer["start"], answer["end"]) == snapped and text[snapped[0] - 1] == " "
          and text[snapped[1]] == " ", repr(text[snapped[0]:snapped[1]]))
    check("a cut inside a turn makes three rows: hers, his, hers",
          answer["kind"] == "assign" and answer["block"]["first"] == r0
          and answer["block"]["before"] == 1 and answer["block"]["after"] == 3
          and [row_cells(work, DEMO_SHEET, r)[0] for r in (r0, r0 + 1, r0 + 2)] == [her, him, her]
          and max_row(work, DEMO_SHEET) == total_before + 2, f"rows {r0} to {r0 + 2}")
    pre, mid, post = (row_cells(work, DEMO_SHEET, r)[2] for r in (r0, r0 + 1, r0 + 2))
    check("the cut falls at the snapped edges, spaces trimmed and nothing invented",
          pre == text[:snapped[0]].rstrip() and mid == text[snapped[0]:snapped[1]]
          and post == text[snapped[1]:].lstrip() and f"{pre} {mid} {post}" == text,
          f"{len(pre)} + {len(mid)} + {len(post)} characters")
    blocks_after = crux_blocks(work, DEMO_SHEET, r0 + 1) + crux_blocks(work, DEMO_SHEET, r0 + 2)
    check("the orange run is cut at the boundary and stays on the words it was on",
          " ".join(t for t, _ in blocks_after) == phrase and len(blocks_after) == 2
          and mid.endswith(blocks_after[0][0]) and post.startswith(blocks_after[1][0]),
          f"{blocks_after[0][0]!r} | {blocks_after[1][0]!r}")
    check("every other attribute of the run's font survives the cut",
          all(key == blocks_before[0][1] for _, key in blocks_after), str(blocks_before[0][1]))
    kept = row_cells(work, DEMO_SHEET, r0)[3]
    check("the statements, notes and quotes stay with the first row that keeps her",
          kept == row_cells(keep, DEMO_SHEET, r0)[3] and any(kept)
          and row_cells(work, DEMO_SHEET, r0 + 1)[3] == [[], [], []]
          and row_cells(work, DEMO_SHEET, r0 + 2)[3] == [[], [], []])
    t0, t_mid, t_post, t_next = (wb_mod.ts_seconds(row_cells(work, DEMO_SHEET, r)[1])
                                 for r in (r0, r0 + 1, r0 + 2, r0 + 3))
    want = t0 + round((t_next - t0) * snapped[0] / len(text))
    check("the new row's timecode is shared out by where the cut falls",
          t_mid == want and t0 <= t_mid <= t_post <= t_next,
          f"{wb_mod.timecode(t0)} {wb_mod.timecode(t_mid)} {wb_mod.timecode(t_post)} {wb_mod.timecode(t_next)}")
    check("and it is written the way its neighbours hold a timecode",
          isinstance(row_cells(work, DEMO_SHEET, r0 + 1)[1], dt.time)
          and isinstance(row_cells(keep, DEMO_SHEET, r0)[1], dt.time),
          "datetime.time, as the column holds it")
    check("the new rows take the style of the row they were cut from",
          all(cell_face(work, DEMO_SHEET, r, c) == cell_face(keep, DEMO_SHEET, r0, c)
              for r in (r0 + 1, r0 + 2) for c in range(1, 7)),
          "font, alignment and number format, cell by cell")
    sig_after = sheet_signature(work, DEMO_SHEET)
    check("the header row is never touched", sig_after[0][0] == sig_before[0][0])
    check("the rows below come through unchanged, two further down",
          sig_after[0][r0 + 2:] == sig_before[0][r0:], f"{len(sig_after[0]) - r0 - 2} rows compared")
    check("widths, freeze pane and zoom are kept, and no cell anywhere gains a fill",
          sig_after[2] == sig_before[2] and sig_after[1] == [] and sig_before[1] == [],
          str(sig_after[2][1:]))
    backup = Path(answer["block"]["backup"])
    check("the workbook was copied to _Archive before a row moved",
          backup.exists() and backup.parent.name == "_Archive" and "(pre-assign " in backup.name
          and not compare_workbooks(keep, backup, allowed=set())[0], backup.name)
    side = rounds_mod.load_progress(work)
    record = side["assignments"][-1]
    check("the sidecar moves with the rows: her state and flag stay, the rows below move down two",
          side["rows"] == {f"Initial:{r0}": "has-content", f"Initial:{r0 + 8}": "reviewed-empty"}
          and side["flags"] == [f"Initial:{r0}", f"Initial:{r0 + 8}"]
          and side["last"] == {"sheet": DEMO_SHEET, "row": r0 + 8}
          and side["edits"][0]["row"] == r0 + 8, str(side["flags"]))
    check("the assignment is recorded beside the edits and the trims",
          record["kind"] == "assign" and record["sheet"] == DEMO_SHEET and record["row"] == r0
          and (record["start"], record["end"]) == snapped and record["from"] == her
          and record["to"] == him and record["before"] == [text] and record["after"] == [pre, mid, post]
          and record["backup"] and record["when"] and record["undone"] is False,
          f"id {record['id']}")
    check("the page lands on the turn it was on, wherever that has moved to",
          answer["land"] == {"sheet": DEMO_SHEET, "row": r0 + 8}, str(answer["land"]))

    # ── B. undo, from the backup, byte for byte where it matters
    back = rows_api({"op": "restore", "path": str(work), "id": answer["id"]})
    problems, checked = compare_workbooks(keep, work, allowed=set())
    check("undo puts the rows back identical under compare_workbooks", not problems,
          f"{checked} cells compared, {len(problems)} differences")
    for p in problems[:3]:
        print(f"        {p}")
    check("and the sheet as a whole, fills, widths, heights and all",
          sheet_signature(work, DEMO_SHEET) == sig_before)
    check("the sidecar is back as it was", sidecar_view(work) == side_before, str(sidecar_view(work)["flags"]))
    record = rounds_mod.load_progress(work)["assignments"][-1]
    check("the record is kept and marked undone", record["undone"] is True and record.get("undone_when"))
    check("undo lands back on the turn the page was on when the assignment was made",
          back["land"] == {"sheet": DEMO_SHEET, "row": r0 + 6}, str(back["land"]))
    record = rounds_mod.load_progress(work)["assignments"][-1]
    check("the record keeps the turn the page was on when it was made",
          record.get("current") == r0 + 6, str(record.get("current")))
    try:
        rows_api({"op": "restore", "path": str(work), "id": answer["id"]})
        check("an assignment is undone once", False, "it restored twice")
    except WorkbookError as exc:
        check("an assignment is undone once", "already been undone" in str(exc), str(exc))

    # redo re-applies from the recorded offsets, and a statement written since survives the undo
    again = rows_api({"op": "assign", "path": str(work), "sheet": DEMO_SHEET, "row": r0, "to": him,
                      "start": answer["start"], "end": answer["end"]})
    check("redo re-applies the same assignment from the offsets it recorded",
          [row_cells(work, DEMO_SHEET, r)[2] for r in (r0, r0 + 1, r0 + 2)] == [pre, mid, post]
          and again["id"] != answer["id"])
    wb_mod.save_turn(work, DEMO_SHEET, r0 + 1, "A statement written on the new row", None, None)
    rows_api({"op": "restore", "path": str(work), "id": again["id"]})
    cells = row_cells(work, DEMO_SHEET, r0)
    check("a statement written into a row the assignment made is appended to the restored row",
          cells[3][0] == row_cells(keep, DEMO_SHEET, r0)[3][0] + ["A statement written on the new row"]
          and max_row(work, DEMO_SHEET) == total_before, str(len(cells[3][0])))

    # ── C. at the start and at the end of a turn
    edges = demo_copy(root, "edges", "Juno - EN & ES.xlsx")
    rows = {r["row"]: r for r in demo_sheet(edges)[0]["rows"]}
    last = max(rows)
    first = rows[2]
    n_first = len(first["text"].split()[0]) + 1 + len(first["text"].split()[1])
    wb_mod.assign_rows(edges, DEMO_SHEET, 2, her, 0, n_first)
    a, b = row_cells(edges, DEMO_SHEET, 2), row_cells(edges, DEMO_SHEET, 3)
    check("words that start the first turn become two rows, the words first",
          a[0] == her and b[0] == him and a[2] == first["text"][:n_first]
          and b[2] == first["text"][n_first:].lstrip()
          and max_row(edges, DEMO_SHEET) == last + 1)
    check("the first of the two keeps the turn's own timecode, the rest takes the estimate",
          wb_mod.ts_seconds(a[1]) == first["seconds"]
          and first["seconds"] <= wb_mod.ts_seconds(b[1]) <= rows[3]["seconds"],
          f"{wb_mod.timecode(wb_mod.ts_seconds(a[1]))} and {wb_mod.timecode(wb_mod.ts_seconds(b[1]))}")

    tail = rows[last]
    words = tail["text"].split()
    cut = tail["text"].rindex(words[-3])
    before_last = max_row(edges, DEMO_SHEET)
    wb_mod.assign_rows(edges, DEMO_SHEET, before_last, her if tail["name"] == him else him, cut, len(tail["text"]))
    x, y = row_cells(edges, DEMO_SHEET, before_last), row_cells(edges, DEMO_SHEET, before_last + 1)
    span = math_ceil(0.4 * len(words))
    want = tail["seconds"] + round(span * cut / len(tail["text"]))
    check("words that end the last turn of a sheet become two rows, the words last",
          y[2] == tail["text"][cut:] and x[2] == tail["text"][:cut].rstrip()
          and max_row(edges, DEMO_SHEET) == before_last + 1)
    check("the last row of a sheet is taken to run 0.4 seconds a word",
          wb_mod.ts_seconds(y[1]) == want and want <= tail["seconds"] + span,
          f"{len(words)} words, the cut at {wb_mod.timecode(want)}")

    # the words at the start of her turn belong to his turn before it, so they join it
    mid_row = next(r for r in sorted(rows) if r > 6 and rows[r]["name"] == her and rows[r - 1]["name"] == him)
    hers, his_before = row_cells(edges, DEMO_SHEET, mid_row + 1), row_cells(edges, DEMO_SHEET, mid_row)
    sentence_end = hers[2].index(". ") + 1
    count_before = max_row(edges, DEMO_SHEET)
    joined = wb_mod.assign_rows(edges, DEMO_SHEET, mid_row + 1, him, 0, sentence_end)
    after_his, after_hers = row_cells(edges, DEMO_SHEET, mid_row), row_cells(edges, DEMO_SHEET, mid_row + 1)
    check("words at the start of a turn join the turn before when that speaker is theirs",
          joined["kind"] == "merge" and max_row(edges, DEMO_SHEET) == count_before
          and after_his[2] == his_before[2] + " " + hers[2][:sentence_end]
          and after_hers[2] == hers[2][sentence_end:].lstrip() and after_hers[0] == her,
          "two rows, nothing inserted")
    check("the turn before keeps its own timecode, the rest of hers moves on",
          after_his[1] == his_before[1]
          and wb_mod.ts_seconds(after_hers[1]) >= wb_mod.ts_seconds(hers[1]))

    # ── D. a whole turn, merged both sides, with annotations appended and a flag kept
    whole = demo_copy(root, "whole", "Juno - EN & ES.xlsx")
    wkeep = root / "whole" / "untouched.xlsx"
    rows = {r["row"]: r for r in demo_sheet(whole)[0]["rows"]}
    target = next(r for r in sorted(rows) if rows[r]["name"] == her and rows[r]["es"].strip()
                  and r > 3 and not any(x["crux"] for x in rows[r]["runs"]))
    wb_mod.save_turn(whole, DEMO_SHEET, target - 1, "His statement", "His note", None)
    wb_mod.save_turn(whole, DEMO_SHEET, target + 1, None, None, '"his quote"')
    shutil.copy2(whole, wkeep)
    progress = rounds_mod.load_progress(whole)
    progress["flags"] = [f"Initial:{target}"]
    progress["rows"] = {f"Initial:{target}": "has-content", f"Initial:{target + 4}": "has-content"}
    rounds_mod.save_progress(whole, progress)
    wside = sidecar_view(whole)
    preview = rows_api({"op": "preview", "path": str(whole), "sheet": DEMO_SHEET, "row": target, "to": him})
    check("the confirm card names the merge it will make",
          preview["line"] == f"{him} {rows[target - 1]['time']} and {him} {rows[target + 1]['time']} "
                             f"become one passage, with {her} {rows[target]['time']} between them assigned to {him}.",
          preview["line"])
    check("and what it carries across, naming no flag though the row holds one from before",
          "flagged" not in preview and "flag" not in preview["carries"] and "statement" in preview["carries"],
          preview["carries"])
    check("a preview writes nothing", not compare_workbooks(wkeep, whole, allowed=set())[0])
    merged = rows_api({"op": "assign", "path": str(whole), "sheet": DEMO_SHEET, "row": target, "to": him,
                       "current": {"sheet": DEMO_SHEET, "row": target}})
    one = row_cells(whole, DEMO_SHEET, target - 1)
    parts = [rows[target - 1]["text"], rows[target]["text"], rows[target + 1]["text"]]
    check("a whole turn given to him merges with his turns either side into one row",
          merged["kind"] == "merge" and merged["merged"] == 2 and one[0] == him
          and one[2] == " ".join(p.strip() for p in parts)
          and max_row(whole, DEMO_SHEET) == max(rows) - 2, "three rows become one")
    check("the first row's timecode stands", one[1] == row_cells(wkeep, DEMO_SHEET, target - 1)[1])
    k_prev, k_mid, k_next = (row_cells(wkeep, DEMO_SHEET, r)[3] for r in (target - 1, target, target + 1))
    # each row's quotes stay with its own statements, "(no quote)" holding a place, and a quote past
    # its row's statements goes after them all (198)
    placed = [q for k in (k_prev, k_mid, k_next)
              for q in (k[2] + [wb_mod.NO_QUOTE] * len(k[0]))[:len(k[0])]]
    loose = [q for k in (k_prev, k_mid, k_next) for q in k[2][len(k[0]):]]
    check("the statements, notes and quotes are appended line by line in sheet order, each quote kept with its statement",
          one[3][:2] == [k_prev[i] + k_mid[i] + k_next[i] for i in range(2)] and one[3][0][0] == "His statement"
          and one[3][2] == placed + loose and one[3][2][0] == wb_mod.NO_QUOTE and one[3][2][-1] == '"his quote"',
          f"{len(one[3][0])} statements, {len(one[3][1])} notes, {len(one[3][2])} quotes")
    side = rounds_mod.load_progress(whole)
    check("the flag is kept, on the merged row, and the rows below move up two",
          side["flags"] == [f"Initial:{target - 1}"]
          and side["rows"] == {f"Initial:{target - 1}": "has-content", f"Initial:{target + 2}": "has-content"},
          str(side["flags"]))
    check("the page lands on the merged turn", merged["land"] == {"sheet": DEMO_SHEET, "row": target - 1})
    elsewhere = rows_api({"op": "restore", "path": str(whole), "id": merged["id"],
                          "current": {"sheet": DEMO_SHEET, "row": target + 5}})
    check("an undo keeps the page on the turn it is on, moved back with the rows",
          elsewhere["land"] == {"sheet": DEMO_SHEET, "row": target + 7}, str(elsewhere["land"]))
    check("undoing a merge puts all three rows back as they were, and the sidecar with them",
          not compare_workbooks(wkeep, whole, allowed=set())[0] and sidecar_view(whole) == wside)

    # the first row of a sheet has one neighbour, and merges with that one
    rows_api({"op": "assign", "path": str(whole), "sheet": DEMO_SHEET, "row": 2, "to": her})
    top = row_cells(whole, DEMO_SHEET, 2)
    check("a merge at the first row joins the one neighbour it has",
          top[0] == her and top[2] == rows[2]["text"].strip() + " " + rows[3]["text"].strip()
          and top[1] == row_cells(wkeep, DEMO_SHEET, 2)[1]
          and max_row(whole, DEMO_SHEET) == max(rows) - 1
          and crux_blocks(whole, DEMO_SHEET, 2) == crux_blocks(wkeep, DEMO_SHEET, 3),
          "and every run of the turn after it comes with it")
    check("the header row is still the header row",
          sheet_signature(whole, DEMO_SHEET)[0][0] == sheet_signature(wkeep, DEMO_SHEET)[0][0])

    # ── E. any number of speakers
    many = demo_copy(root, "many", "Juno - EN & ES.xlsx")
    book = openpyxl.load_workbook(many, rich_text=True)
    ws = book[DEMO_SHEET]
    ws.cell(7, 1).value = "Rowan"
    ws.cell(11, 1).value = "Rowan"
    book.save(many)
    book.close()
    wb = openpyxl.load_workbook(many, rich_text=True)
    speakers = wb_mod.sheet_speakers(wb[DEMO_SHEET], wb_mod.detect_columns(wb[DEMO_SHEET]))
    wb.close()
    check("the speakers of a sheet are its distinct names in order of first appearance",
          speakers == [him, her, "Rowan"], str(speakers))
    lone = rows_api({"op": "preview", "path": str(many), "sheet": DEMO_SHEET, "row": 7, "to": "Wren"})
    check("a turn whose neighbours are someone else's merges with nothing, and the card says so",
          lone["merges"] == [] and "Nothing merges" in lone["line"], lone["line"])
    size = max_row(many, DEMO_SHEET)
    new_name = rows_api({"op": "assign", "path": str(many), "sheet": DEMO_SHEET, "row": 7, "to": "Wren"})
    check("a whole turn can go to a speaker the sheet has never had, and only the name changes",
          new_name["kind"] == "assign" and row_cells(many, DEMO_SHEET, 7)[0] == "Wren"
          and max_row(many, DEMO_SHEET) == size)
    spelled = rows_api({"op": "assign", "path": str(many), "sheet": DEMO_SHEET, "row": 7, "to": "rowan"})
    check("a name already on the sheet is taken as it is spelled there",
          spelled["to"] == "Rowan" and row_cells(many, DEMO_SHEET, 7)[0] == "Rowan")
    try:
        rows_api({"op": "assign", "path": str(many), "sheet": DEMO_SHEET, "row": 7, "to": "ROWAN"})
        check("a turn is never assigned to its own speaker", False, "it did")
    except WorkbookError as exc:
        check("a turn is never assigned to its own speaker", "already" in str(exc), str(exc))
    space = row_cells(many, DEMO_SHEET, 7)[2].index(" ")
    for label, start, end in (("a selection with no words in it", space, space + 1),
                              ("a selection outside the turn", 0, 10 ** 6)):
        try:
            rows_api({"op": "assign", "path": str(many), "sheet": DEMO_SHEET, "row": 7, "to": her,
                      "start": start, "end": end})
            check(f"{label} is refused", False, "it went through")
        except WorkbookError as exc:
            check(f"{label} is refused", "selection" in str(exc), str(exc))

    # ── F. the one re-key, for rows inserted and rows deleted
    base = {"rows": {"Initial:3": "reviewed-empty", "Initial:4": "has-content", "Initial:5": "unvisited",
                     "Initial:9": "has-content", "2d:4": "has-content"},
            "flags": ["Initial:5", "Initial:9", "2d:4"], "last": {"sheet": DEMO_SHEET, "row": 5},
            "edits": [{"sheet": DEMO_SHEET, "row": 9, "old": "a", "new": "b"}]}
    ins = json.loads(json.dumps(base))
    rounds_mod.rekey_rows(ins, DEMO_SHEET, 4, 2, inserted=True)
    check("rows inserted at r, count n: every row from r down moves down n, other sheets stay",
          ins["rows"] == {"Initial:3": "reviewed-empty", "Initial:6": "has-content", "Initial:7": "unvisited",
                          "Initial:11": "has-content", "2d:4": "has-content"}
          and ins["flags"] == ["Initial:7", "Initial:11", "2d:4"]
          and ins["last"] == {"sheet": DEMO_SHEET, "row": 7} and ins["edits"][0]["row"] == 11)
    dele = json.loads(json.dumps(base))
    rounds_mod.rekey_rows(dele, DEMO_SHEET, 4, 2, inserted=False, into=3)
    check("rows deleted at r, count n into a row: their state and flag fold into it, the rest move up",
          dele["rows"] == {"Initial:3": "has-content", "Initial:7": "has-content", "2d:4": "has-content"}
          and dele["flags"] == ["Initial:3", "Initial:7", "2d:4"]
          and dele["last"] == {"sheet": DEMO_SHEET, "row": 3} and dele["edits"][0]["row"] == 7)
    cut = json.loads(json.dumps(base))
    rounds_mod.rekey_rows(cut, DEMO_SHEET, 5, None, inserted=False)
    check("rows deleted to the end go, and their edit records stay, marked cut",
          cut["rows"] == {"Initial:3": "reviewed-empty", "Initial:4": "has-content", "2d:4": "has-content"}
          and cut["flags"] == ["2d:4"] and cut["last"] is None and cut["edits"][0].get("cut") is True)
    check("the trim's re-key is the same one, front and back",
          rounds_mod.moved_key("Initial:9", DEMO_SHEET, "before", 4) == "Initial:6"
          and rounds_mod.moved_key("Initial:4", DEMO_SHEET, "before", 4) is None
          and rounds_mod.moved_key("Initial:9", DEMO_SHEET, "after", 9) is None
          and rounds_mod.moved_key("Initial:8", DEMO_SHEET, "after", 9) == "Initial:8"
          and "rekey_rows(" in inspect.getsource(rounds_mod.rekey_after_trim))
    heights = root / "heights.xlsx"
    book = openpyxl.Workbook()
    ws = book.active
    ws.title = DEMO_SHEET
    for col, head in zip("ABCDEF", wb_mod.HEADER):
        ws[f"{col}1"] = head
    for r in range(2, 8):
        ws.cell(r, 1, him if r % 2 == 0 else her)
        ws.cell(r, 2, dt.time(0, r, 0))
        ws.cell(r, 4, f"row {r} has a few words in it for the cut to fall between")
        ws.row_dimensions[r].height = 16.0 * (r - 1)
    book.save(heights)
    book.close()
    wb_mod.assign_rows(heights, DEMO_SHEET, 3, him, 6, 11)
    hs = sheet_signature(heights, DEMO_SHEET)[3]
    check("custom row heights move down with their rows, and new rows get a share of the height",
          hs[2] == 16.0 and hs[3] == 32.0 and hs[6] == 48.0 and hs[7] == 64.0 and hs[8] == 80.0
          and hs[9] == 96.0 and hs[4] == 16.0 and hs[5] == 32.0, str(hs))

    # ── G. the lock guard and the header
    lock = wb_mod.lock_file(work)
    lock.write_bytes(b"pretend Excel lock")
    shutil.copy2(work, root / "three" / "locked-before.xlsx")
    for name, call in (("an assignment", lambda: wb_mod.assign_rows(work, DEMO_SHEET, r0, him)),
                       ("an undo", lambda: wb_mod.restore_rows(work, DEMO_SHEET, r0, 1, 3, backup, r0))):
        try:
            call()
            check(f"{name} refuses a workbook Excel has open", False, "it wrote to it")
        except WorkbookError as exc:
            check(f"{name} refuses a workbook Excel has open", "Close it in Excel first" in str(exc), str(exc))
    lock.unlink()
    check("and nothing was written while it was open",
          not compare_workbooks(root / "three" / "locked-before.xlsx", work, allowed=set())[0])
    for name, call in (("assigned", lambda: wb_mod.assign_rows(work, DEMO_SHEET, 1, him)),
                       ("restored over", lambda: wb_mod.restore_rows(work, DEMO_SHEET, 1, 1, 1, backup, 2))):
        try:
            call()
            check(f"the header row is never {name}", False, "it was")
        except WorkbookError as exc:
            check(f"the header row is never {name}", "header row" in str(exc), str(exc))
    try:
        rows_api({"op": "shuffle", "path": str(work), "sheet": DEMO_SHEET, "row": r0})
        check("the endpoint takes assign, preview and restore, nothing else", False)
    except WorkbookError as exc:
        check("the endpoint takes assign, preview and restore, nothing else", "nothing else" in str(exc))
    check("/api/rows is served", server_mod.ROUTES.get("/api/rows") is idiograph_routes.api_rows)

    # ── H. the timecode box, through /api/edit-turn
    timed = demo_copy(root, "timed", "Juno - EN & ES.xlsx")
    tkeep = root / "timed" / "untouched.xlsx"
    shutil.copy2(timed, tkeep)
    t_row = demo_sheet(timed)[0]["rows"][4]
    out = idiograph_routes.api_edit_turn({"path": str(timed), "sheet": DEMO_SHEET, "row": t_row["row"],
                                    "text": t_row["text"], "timecode": "1:02:03"})
    cell = row_cells(timed, DEMO_SHEET, t_row["row"])
    check("a timecode typed in the editor is written in the cell's own representation",
          out["changed"] and out["seconds"] == 3723 and out["time"] == "1:02:03"
          and cell[1] == dt.time(1, 2, 3) and cell[2] == t_row["text"], repr(cell[1]))
    record = rounds_mod.load_progress(timed)["edits"][-1]
    check("the timecode change is recorded beside the text in the edits record",
          record["old_time"] == t_row["time"] and record["new_time"] == "1:02:03"
          and record["old"] == record["new"] == t_row["text"], f"{record['old_time']} to {record['new_time']}")
    problems, _ = compare_workbooks(tkeep, timed, allowed={(DEMO_SHEET, t_row["row"], 2)})
    check("only the timestamp cell moved", not problems, f"{len(problems)} differences")
    shutil.copy2(timed, root / "timed" / "before-bad.xlsx")
    try:
        idiograph_routes.api_edit_turn({"path": str(timed), "sheet": DEMO_SHEET, "row": t_row["row"],
                                  "text": t_row["text"] + " and more", "timecode": "1:2x"})
        check("an unparseable timecode is refused", False, "it went through")
    except WorkbookError as exc:
        check("an unparseable timecode is refused, with a line and nothing written",
              "MM:SS or H:MM:SS" in str(exc)
              and not compare_workbooks(root / "timed" / "before-bad.xlsx", timed, allowed=set())[0], str(exc))
    check("the box reads MM:SS, H:MM:SS and the hours flattened into the minutes",
          wb_mod.parse_timecode("17:09") == 1029 and wb_mod.parse_timecode("1:02:03") == 3723
          and wb_mod.parse_timecode("75:10") == 4510 and wb_mod.parse_timecode("17:60") is None
          and wb_mod.parse_timecode("") is None and wb_mod.parse_timecode("a:bc") is None)
    check("a timecode is written the way its neighbours hold one",
          wb_mod.timecode_like(dt.time(0, 1, 2), 1029) == dt.time(0, 17, 9)
          and wb_mod.timecode_like("00:01:02", 1029) == "00:17:09"
          and wb_mod.timecode_like("0:01:02", 1029) == "0:17:09"
          and wb_mod.timecode_like("01:02", 4510) == "75:10"
          and wb_mod.ts_seconds(wb_mod.timecode_like(0.001, 1029)) == 1029,
          "a time, a string of the same shape, or a fraction of a day")

    # ── I. the page
    page = support.page_text()
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    keys = support.keydown_text(js)
    check("c works outside the fields and outside the turn editor, like h and q",
          "else if (key === 'c' && !$('work').hidden) { e.preventDefault(); assignKey(); }" in keys
          and keys.index("if (typing || MOD(e) || e.altKey) return;") < keys.index("assignKey()")
          and "if (!S.data || S.editing || S.assignBusy) return;" in js)
    check("on a sheet of two speakers c goes to the other one at once, and on more it opens the row's menu with the assignments alone",
          "sheetSpeakers(row.sheet).length === 2 && others.length === 1" in js
          and "openRowMenu(row, { pick, at: pick ? selectionAnchor() : null, only: 'assign' });" in js)
    check("a selection across two turns, or one with no words, is refused with a line",
          "t('distil.assign.two_passages')" in js and "t('distil.assign.no_words')" in js
          and "if (pick && pick.refuse) { say(pick.refuse); return; }" in js)
    check("a selection goes straight through, and a whole turn shows the card first",
          "runAssign({ sheet: pick.row.sheet, row: pick.row.row, to, start: pick.start, end: pick.end });" in js
          and "show('assign');" in js and 'id="assign"' in page
          and "'assign'" in js.split("const OVERLAYS = ", 1)[1].split("\n", 1)[0]
          and "if (!$('assign').hidden && e.key === 'Enter' && !MOD(e)) { e.preventDefault(); runAssignTurn(); return true; }" in js)
    check("a server from before this build says restart and does nothing else",
          js.count("needsRestart(err) ? RESTART_LINE : err.message") >= 4
          and "'/api/rows'" in js
          and "await api('/api/rows', { ...body, op: 'preview' });" in js.split("async function assignApply(", 1)[1],
          "the preview is asked before a dirty field is saved, so a 404 leaves everything alone")
    ctx = js.split("$('transcript').addEventListener('contextmenu'", 1)[1].split("\n  });", 1)[0]
    check("one right-click handler opens the row's menu, the margin and the text alike",
          "openRowMenu(row, { pick: inThis ? pick : null, at: { x: e.clientX, y: e.clientY } });" in ctx
          and ".turn-gutter" not in ctx and "openTrim(" not in js and "openCruxPop(" not in ctx
          and "if (e.shiftKey) return;" in ctx)
    check("Esc puts the menu away before anything else",
          "if (S.rowMenu) { e.preventDefault(); closeRowMenu(); return; }" in keys
          and keys.index("closeRowMenu()") < keys.index("closeTimeEdit()") and "closeCruxPop()" not in keys)
    check("the case reloads in place, on the turn he was on, the player untouched",
          "startCase(await api('/api/open', { path: S.data.path }), { land });" in js
          and "if (!inPlace) S.audioSheet = null;" in js and "drawTurn({ keepPlayer: inPlace });" in js
          and "if (opts && opts.keepPlayer && S.audioSheet === row.sheet) {" in js
          and "markListening();" in js.split("function drawTurn(", 1)[1].split("\n}", 1)[0])
    check("an assignment is one step of undo and redo",
          "anywhere: true" in js and "undo: (e) => assignRestore(e)," in js
          and "redo: (e) => assignRedo(e)," in js and "op: 'restore'" in js)
    saver = js.split("async function saveEdit(", 1)[1].split("\n}", 1)[0]
    check("the turn editor's save sends the text alone",
          "await editApply(row.key, after);" in saver and "timecode" not in saver.lower()
          and "if (timecode !== undefined) body.timecode = timecode;" in js)

    # ── J. the legacy haiku key
    # the settings a new install writes, never the tool folder's own config.json, which a downloaded
    # copy and the gate's snapshot do not have (14 October)
    config_file = server_mod.shipped_config()
    check("config.json no longer carries the haiku key", "haiku" not in config_file)
    saved_path = server_mod.CONFIG_PATH
    scratch_config = root / "config.json"
    scratch_config.write_text(json.dumps({"interviewer": "Adam", "haiku": True}), encoding="utf-8")
    server_mod.CONFIG_PATH = scratch_config
    try:
        wrote = server_mod.api_settings({"round_minutes": 10})["config"]
        on_disk = json.loads(scratch_config.read_text(encoding="utf-8"))
    finally:
        server_mod.CONFIG_PATH = saved_path
    check("an old config still loads with its switch, and a save drops the old key from the file",
          wrote["ai_suggest"] is True and "haiku" not in wrote and "haiku" not in on_disk
          and on_disk["ai_suggest"] is True, "merge_config reads it, api_settings never writes it")


def math_ceil(x: float) -> int:
    import math
    return math.ceil(x)
