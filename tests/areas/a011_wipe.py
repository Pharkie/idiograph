from __future__ import annotations

import contextlib
import io
import shutil
import sys

import openpyxl

from .support import (
    DEMO_SHEET, add_second_sheet, check, compare_workbooks, count_rich, demo_copy, demo_sheet,
)


def wipe_cli(args):
    """wipe_draft.py run as its command line runs it, in this process: its exit code and what it printed.
    A second Python for each run took a second apiece (18 October)."""
    import wipe_draft
    out, held = io.StringIO(), sys.argv
    sys.argv = ["wipe_draft.py", *args]
    try:
        with contextlib.redirect_stdout(out):
            wipe_draft.main()
        code = 0
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
    finally:
        sys.argv = held
    return code, out.getvalue()


def test_wipe(scratch):
    print("\n10. Wipe utility on a scratch copy of the demo workbook")
    work = demo_copy(scratch, "wipe", "Juno - EN & ES.xlsx")
    sheet, her, _ = demo_sheet(work)

    # A draft to clear: the demo ships with a head start on the first six of her turns, and the
    # utility is pointed past it, so everything the suite writes below the boundary is its own. The
    # drafts go in with one save, where a save a passage took a second in all (18 October).
    boundary = max(r["row"] for r in sheet["rows"] if r["es"].strip())
    drafted = [r for r in sheet["rows"] if r["name"] == her and r["row"] > boundary]
    book = openpyxl.load_workbook(work, rich_text=True)
    for row in drafted:
        n = row["row"]
        for col, said in ((3, f"A draft statement on row {n}"), (5, f"A draft note on row {n}"),
                          (6, f'"a draft quote on row {n}"')):
            book[DEMO_SHEET].cell(n, col).value = said
    book.save(work)
    book.close()
    add_second_sheet(work)
    untouched = scratch / "wipe" / "untouched.xlsx"
    shutil.copy2(work, untouched)
    before = openpyxl.load_workbook(work)
    kept = [(r, before[DEMO_SHEET].cell(r, 3).value) for r in range(2, boundary + 1)
            if before[DEMO_SHEET].cell(r, 3).value]
    before.close()

    cmd = ["--workbook", str(work), "--sheet", DEMO_SHEET, "--after-row", str(boundary),
           "--all-sheets-except", DEMO_SHEET]
    dry_code, dry_said = wipe_cli(cmd + ["--dry-run"])
    listed = [l for l in dry_said.splitlines() if l.startswith(f"  {DEMO_SHEET} ") or l.startswith("  2d ")]
    check("dry run prints a table and writes nothing",
          "Dry run" in dry_said and dry_code == 0 and len(listed) > 20,
          f"{len(listed)} rows listed, {len(drafted)} of them drafted past the boundary")
    check("dry run left the workbook alone", not compare_workbooks(untouched, work, allowed=set())[0])

    real_code, real_said = wipe_cli(cmd)
    check("real run reports what it cleared", "Cleared" in real_said and real_code == 0,
          real_said.strip().splitlines()[-1] if real_said.strip() else "nothing said")
    after = openpyxl.load_workbook(work, rich_text=True)
    check("rows up to the boundary untouched",
          all(after[DEMO_SHEET].cell(r, 3).value == v for r, v in kept), f"{len(kept)} rows kept")
    check("nothing left past the boundary on the first sheet",
          all(after[DEMO_SHEET].cell(r, c).value is None
              for r in range(boundary + 1, after[DEMO_SHEET].max_row + 1) for c in (3, 5, 6)))
    check("the other sheet cleared in full",
          all(after["2d"].cell(r, c).value is None
              for r in range(2, after["2d"].max_row + 1) for c in (3, 5, 6)))
    check("the transcript column survives",
          all(after[DEMO_SHEET].cell(r, 4).value for r in range(2, after[DEMO_SHEET].max_row + 1)))
    rich_after = count_rich(work)
    after.close()
    check("orange crux runs in the transcript survive the wipe", rich_after == count_rich(untouched),
          f"{rich_after} cells")
    archived = sorted((work.parent / "_Archive").glob("*pre-wipe*.xlsx"))
    check("archived before clearing", len(archived) == 1, archived[0].name if archived else "none")
    check("the archive is the workbook as it was",
          bool(archived) and not compare_workbooks(untouched, archived[0], allowed=set())[0])
