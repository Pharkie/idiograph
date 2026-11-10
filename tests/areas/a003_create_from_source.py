from __future__ import annotations

import shutil

import openpyxl

import workbook as wb_mod
from workbook import WorkbookError

from . import support
from .support import DEMO_SHEET, REFERENCE_SOURCE, REFERENCE_WORKBOOK, check, skip


DEMO_SOURCE_CSV = support.source("demo/source/Juno - interview.csv")


def test_create_from_source(scratch):
    print("\n2. Create from a raw source workbook")
    if not DEMO_SOURCE_CSV.exists():
        return skip("create from source", "no demo transcript to build a raw source from")
    import make_demo

    # The raw source is built here, in scratch, from the demo transcript: three columns, the
    # timestamps as times, and a second sheet, which is the shape a transcribed source carries.
    rows = make_demo.read_turns()
    case_dir = scratch / "P9 - Nobody"
    (case_dir / "Source").mkdir(parents=True, exist_ok=True)
    src = make_demo.written_source(rows, case_dir / "Source" / "P9 - Nobody v2.xlsx")
    book = openpyxl.load_workbook(src)
    second = book.create_sheet("2d")
    second.append(["Name", "Timestamp", "Transcript"])
    for r, row in enumerate(rows[:12], start=2):
        second.cell(r, 1, row["Name"].strip())
        cell = second.cell(r, 2, make_demo.as_time(row["Timestamp"]))
        cell.number_format = "h:mm:ss"
        second.cell(r, 3, row["Transcript"])
    book.save(src)
    book.close()

    out = wb_mod.suggested_output(src)
    check("output path follows the naming convention", out.name == "P9 Nobody - EN & ES.xlsx", out.name)
    check("output sits in the case folder, never in Source", out.parent.name == "P9 - Nobody", str(out.parent.name))

    wb_mod.create_from_source(src, out)
    made = openpyxl.load_workbook(out, rich_text=True)
    ws = made[DEMO_SHEET]
    check("the six headers are written in Adam's order",
          [ws.cell(1, c).value for c in range(1, 7)] == wb_mod.HEADER,
          str([ws.cell(1, c).value for c in range(1, 7)]))
    widths = {k: v.width for k, v in ws.column_dimensions.items()}
    check("the column widths are the ones the app writes", widths == wb_mod.WIDTHS, str(widths))
    check("the sheet opens frozen under the header and at the reading zoom",
          ws.freeze_panes == "C2" and ws.sheet_view.zoomScale == 160,
          f"{ws.freeze_panes} at {ws.sheet_view.zoomScale}%")
    check("annotation columns are empty", all(ws.cell(r, c).value is None
          for r in range(2, ws.max_row + 1) for c in (3, 5, 6)))

    source = openpyxl.load_workbook(src, rich_text=True)
    ss = source[DEMO_SHEET]
    same = all(str(ss.cell(r, 3).value) == str(ws.cell(r, 4).value) and ss.cell(r, 1).value == ws.cell(r, 1).value
               and ss.cell(r, 2).value == ws.cell(r, 2).value for r in range(2, ss.max_row + 1))
    check("transcript, names and timestamps copied unchanged", same, f"{ss.max_row - 1} rows on the first sheet")
    check("every sheet carried over", made.sheetnames == source.sheetnames, str(made.sheetnames))
    check("the timestamp format comes across with the value",
          made["2d"].cell(2, 2).number_format == source["2d"].cell(2, 2).number_format,
          made["2d"].cell(2, 2).number_format)
    made.close(); source.close()

    try:
        wb_mod.create_from_source(src, src.parent / "nope - EN & ES.xlsx")
        check("refuses to write into a Source folder", False, "it wrote the file")
    except WorkbookError as exc:
        check("refuses to write into a Source folder", "Source folder" in str(exc), str(exc))

    # The reference workbook is what the headers and widths above were taken from, so when it is
    # on the machine the constants are checked against it rather than against themselves.
    if not REFERENCE_WORKBOOK.exists():
        skip("create from source: the reference workbook", "no reference workbook under Main Data")
    else:
        ref = openpyxl.load_workbook(REFERENCE_WORKBOOK, rich_text=True)
        rs = ref["Initial"]
        # its quotes column keeps the Key quotes heading it was made with, and a new one says Quote (250)
        check("the headers are the reference workbook's headers, its quotes column found as a new one's",
              wb_mod.HEADER[:5] == [rs.cell(1, c).value for c in range(1, 6)]
              and wb_mod.detect_columns(rs).get("kq") == 6 and wb_mod.HEADER[5] == "Quote",
              str(wb_mod.HEADER))
        check("the widths are the reference workbook's widths",
              wb_mod.WIDTHS == {k: v.width for k, v in rs.column_dimensions.items()},
              str(wb_mod.WIDTHS))
        ref.close()

    # A source written by the transcription pipeline, which is the shape the one above imitates.
    if not REFERENCE_SOURCE.exists():
        skip("create from source: a source from the transcription pipeline", "no raw source under Main Data")
    else:
        live_dir = scratch / "pipeline-source"
        (live_dir / "Source").mkdir(parents=True, exist_ok=True)
        live_src = live_dir / "Source" / REFERENCE_SOURCE.name
        shutil.copy2(REFERENCE_SOURCE, live_src)
        live_out = wb_mod.create_from_source(live_src, live_dir / "from the pipeline - EN & ES.xlsx")
        built = openpyxl.load_workbook(live_out, rich_text=True)
        raw = openpyxl.load_workbook(live_src, rich_text=True)
        check("the three columns of a pipeline source are found by their headers",
              built.sheetnames == raw.sheetnames and len(built.sheetnames) > 1,
              f"{len(raw.sheetnames)} sheets carried over")
        carried = all(str(raw[name].cell(r, 3).value) == str(built[name].cell(r, 4).value)
                      for name in raw.sheetnames
                      for r in range(2, raw[name].max_row + 1))
        check("every turn of a pipeline source copies through unchanged", carried,
              f"{sum(raw[n].max_row - 1 for n in raw.sheetnames)} rows")
        built.close(); raw.close()
