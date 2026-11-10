from __future__ import annotations

import openpyxl
from openpyxl.cell.rich_text import TextBlock

import workbook as wb_mod
from workbook import WorkbookError

from .support import check, compare_workbooks, demo_copy, demo_sheet


def test_crux_ops(scratch):
    print("\n25. Adding and removing a highlight by the character, not by the whole run")
    keep = demo_copy(scratch, "ops", "untouched.xlsx")

    # a turn with a long plain stretch, so a run can be made inside it and then cut about, and
    # with orange runs of its own already, so those can be checked as untouched throughout
    initial, _, _ = demo_sheet(keep)
    long_plain = [r for r in initial["rows"]
                  if any(not x["crux"] and len(x["text"]) > 80 for x in r["runs"])]
    target = next((r for r in long_plain if any(x["crux"] for x in r["runs"])), long_plain[0])
    sheet, row = target["sheet"], target["row"]
    at = 0
    for part in target["runs"]:
        if not part["crux"] and len(part["text"]) > 80:
            break
        at += len(part["text"])
    base = at + 5
    text = target["text"]
    was = [x["text"] for x in target["runs"] if x["crux"]]

    def fresh(name):
        return demo_copy(scratch, "ops", f"{name}.xlsx")

    def orange(path):
        read = wb_mod.read_case(path)
        found = next(x for s in read["sheets"] if s["name"] == sheet
                     for x in s["rows"] if x["row"] == row)
        return [x["text"] for x in found["runs"] if x["crux"]]

    def crux(path, start, end, op=None):
        return wb_mod.save_crux(path, sheet, row, start, end, text[start:end], op=op)

    whole = text[base:base + 30]

    # 1. the run shortens at its start
    work = fresh("head")
    added = crux(work, base, base + 30, "add")
    check("a mark leaves the passage's words as they were, run for run",
          "".join(x["text"] for x in added["runs"]) == text, f"{len(text)} characters")
    result = crux(work, base, base + 10, "remove")
    check("a selection at the start of a run shortens it from the front",
          whole[10:] in orange(work) and whole not in orange(work)
          and result["op"] == "remove" and result["removed"] is True,
          repr(whole[10:][:30]))

    # 2. and at its end
    work = fresh("tail")
    crux(work, base, base + 30, "add")
    crux(work, base + 20, base + 30, "remove")
    check("a selection at the end of a run shortens it from the back",
          whole[:20] in orange(work) and whole not in orange(work), repr(whole[:20]))

    # 3. a selection in the middle splits it in two
    work = fresh("split")
    crux(work, base, base + 30, "add")
    crux(work, base + 10, base + 20, "remove")
    marks = orange(work)
    check("a selection in the middle of a run splits it into two",
          whole[:10] in marks and whole[20:30] in marks and whole[10:20] not in marks,
          f"{len(marks)} orange runs on the turn, {len(was)} before any of this")
    check("the runs the turn already carried are untouched by any of it",
          all(w in marks for w in was), f"{len(was)} existing runs")

    # 4. a selection that runs past a highlight adds to it
    work = fresh("union")
    crux(work, base, base + 20, "add")
    crux(work, base + 10, base + 40, "add")
    check("a selection that overlaps a run is added, so the two become one",
          text[base:base + 40] in orange(work),
          repr(text[base:base + 40][:40]))

    # 5. the old payload, with no op at all, toggles the way it always did
    work = fresh("toggle")
    crux(work, base, base + 30, "add")
    back = crux(work, base + 5, base + 10)
    check("a call with no op still clears the whole run, as the first version did",
          back["removed"] is True and whole not in orange(work) and orange(work) == was,
          "a page in front of a server that has not been restarted loses nothing")

    # 6. the storage, and the round trip an undo makes
    work = fresh("trip")
    crux(work, base, base + 30, "add")
    themes = []
    book = openpyxl.load_workbook(work, rich_text=True)
    cell = book[sheet].cell(row, 4)
    for block in cell.value:
        if isinstance(block, TextBlock):
            themes.append((block.font.color.theme, block.font.color.tint))
    fill = cell.fill.fill_type
    book.close()
    check("the new run is stored as a font run, theme 9 tint 0, and the cell takes no fill",
          (9, 0.0) in themes and fill is None, str(sorted(set(themes))))
    problems, checked = compare_workbooks(keep, work, allowed={(sheet, row, 4)})
    check("an op touches one cell and nothing else", not problems, f"{checked} cells compared")
    for p in problems[:3]:
        print(f"        {p}")

    crux(work, base + 10, base + 20, "remove")          # split it
    crux(work, base + 10, base + 20, "add")             # and close it up again
    check("a split run closed up again is one run", whole in orange(work), repr(whole[:30]))
    crux(work, base, base + 30, "remove")
    problems, checked = compare_workbooks(keep, work, allowed=set())
    check("mark, split, close and clear leaves the workbook exactly as it was", not problems,
          f"{checked} cells compared, {len(problems)} differences")
    for p in problems[:3]:
        print(f"        {p}")

    # a selection whose words are not the passage's is refused, as area 4 checked until 18 October
    try:
        wb_mod.save_crux(work, sheet, row, 0, 5, "not in this turn at all")
        check("refuses a selection that is not in the turn", False, "it accepted it")
    except WorkbookError as exc:
        check("refuses a selection that is not in the turn",
              "does not match the passage's words exactly" in str(exc), str(exc))
