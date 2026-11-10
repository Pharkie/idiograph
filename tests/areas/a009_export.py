from __future__ import annotations

import io
import shutil
from pathlib import Path

import export as export_mod

from .support import DEMO_SHEET, NOWHERE, REFERENCE_WORKBOOK, check, local_parts, demo_copy, demo_sheet, skip


def test_export(scratch):
    print("\n8. Export to CSV")
    work = demo_copy(scratch, "export", "Juno - EN & ES.xlsx")
    sheet, _, _ = demo_sheet(work)
    written = sum(1 for r in sheet["rows"] for line in r["es"].splitlines() if line.strip())
    result = export_mod.export(work)
    out = Path(result["path"])
    check("written to the Working folder, named off the workbook",
          out.parent.name == "Working" and out.name == "Juno - All Experiential Statements.csv", out.name)
    lines = out.read_text(encoding="utf-8-sig").splitlines()
    check("header matches the reference file, the statement's own quote after its four columns (95)",
          lines[0] == "Interview,Timestamp,Experiential statement,Proposed PET (blank for you),Quote", lines[0])
    check("starts with a byte order mark", out.read_bytes().startswith(b"\xef\xbb\xbf"))
    check("timestamps as HH:MM:SS", lines[1].split(",")[1].count(":") == 2, lines[1][:60])
    check("one line per statement, and every statement in the workbook is there",
          result["statements"] == written and len(lines) == written + 1,
          f"{result['statements']} statements over {len(lines) - 1} lines")
    check("the sheet name opens every line", all(l.startswith(DEMO_SHEET + ",") for l in lines[1:]))

    # The reference export was written by hand before any of this, so a run against the workbook
    # it came from is what proves the format has not drifted.
    # The export's path beside the workbook is named in the local gate file, as the workbook is
    parts = local_parts("reference_export")
    reference = REFERENCE_WORKBOOK.parent.joinpath(*parts) if parts else NOWHERE
    if not (REFERENCE_WORKBOOK.exists() and reference.exists()):
        skip("export against the reference file", "no reference workbook and export under Main Data")
    else:
        # the quote fixes of 7 October moved three statements to the turns holding their words, so
        # the reference is checked against the workbook as it stood before them, kept in _Archive
        before = sorted(REFERENCE_WORKBOOK.parent.glob("_Archive/" + REFERENCE_WORKBOOK.stem + " (before quote fixes *).xlsx"))
        live = scratch / "export-reference" / REFERENCE_WORKBOOK.name
        live.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(before[0] if before else REFERENCE_WORKBOOK, live)
        import csv as csv_mod
        live_text = Path(export_mod.export(live)["path"]).read_text(encoding="utf-8-sig")
        ref_rows = list(csv_mod.reader(io.StringIO(reference.read_text(encoding="utf-8-sig"))))
        # the reference was written before the statement's own quote joined as a fifth column (95),
        # so the four columns it has are the ones compared
        ref_initial = [r[:4] for r in ref_rows[1:] if r and r[0] == "Initial"]
        new_initial = [r[:4] for r in list(csv_mod.reader(io.StringIO(live_text)))[1:] if r and r[0] == "Initial"]
        check("same Initial statements as the reference export", new_initial == ref_initial,
              f"{len(new_initial)} rows against {len(ref_initial)} in the reference")
    print(f"        {result['statements']} statements exported")
