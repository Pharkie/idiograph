"""Area 250: the workbook's quotes column is headed Quote (Adam's ruling of 22 October 2026). It was Key
quotes, and the statements CSV's last column was Key quote. A new workbook, one made from the template
among them, now carries Quote, and the CSV's header says Quote. A workbook made before then keeps its
Key quotes heading: every path reads and writes it as before, the app's reading, the command line's
statements and turn write, and the export, and nothing renames its heading by itself (area 257 holds
the op that renames it on his word).

The checks run on scratch copies of the demo's invented participants, Rowan's with its heading put back
to Key quotes, beside the copy as it ships.
"""
from __future__ import annotations

import csv
import io
import json
import shutil

import openpyxl

from . import support
from .support import check


def heading(path) -> list:
    wb = openpyxl.load_workbook(path, read_only=True)
    try:
        return [c for c in next(wb.worksheets[0].iter_rows(min_row=1, max_row=1, values_only=True))]
    finally:
        wb.close()


def cells(path) -> dict:
    wb = openpyxl.load_workbook(path, rich_text=True)
    try:
        return {(ws.title, c.coordinate): str(c.value) for ws in wb.worksheets for row in ws.iter_rows() for c in row}
    finally:
        wb.close()


def test_quote_header(scratch):
    print("\n250. The quotes column headed Quote, and a workbook headed Key quotes read and written as before (22 October)")
    import cli
    import export as export_mod
    import make_template
    import workbook as wb_mod

    # A. a new workbook, from a made-up source and from the template, carries Quote
    root = scratch / "quote-header-250"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    source = root / "Hazel - interview.xlsx"
    raw = openpyxl.Workbook()
    raw.active.title = "Initial"
    raw.active.append(["Name", "Timestamp", "Transcript"])
    raw.active.append(["Interviewer", "00:00:04", "How did the allotment go this year?"])
    raw.active.append(["Hazel", "00:00:09", "The beans came up in a week and the slugs had them in two."])
    raw.save(source)
    made = wb_mod.create_from_source(source, root / "Hazel - EN & ES.xlsx")
    from_template = wb_mod.create_from_source(make_template.TEMPLATE, root / "Template - EN & ES.xlsx")
    ws = openpyxl.load_workbook(made).worksheets[0]
    check("250: a new workbook and one made from the template head the quotes column Quote, found as the quotes",
          wb_mod.HEADER[-1] == "Quote" and heading(made)[5] == "Quote" and heading(from_template)[5] == "Quote"
          and wb_mod.detect_columns(ws).get("kq") == 6
          and not any("quote" in str(h).lower() for h in heading(make_template.TEMPLATE)),
          f"{heading(made)} {heading(from_template)}")
    for head in ("Key quotes", "Key quote", "Quote", "Quotes", "quote"):
        ws.cell(1, 6).value = head
        if wb_mod.detect_columns(ws).get("kq") != 6:
            break
    check("250: Key quotes, Key quote, Quote and Quotes each read as the quotes column", wb_mod.detect_columns(ws).get("kq") == 6, head)

    # B. Rowan's workbook with the old heading, beside the copy as it ships
    pristine = support.DEMO_PRISTINE
    for name in ("Rowan", "Mabel"):
        (root / name / "Working").mkdir(parents=True)
        shutil.copy2(pristine / f"{name} - EN & ES.xlsx", root / name / f"{name} - EN & ES.xlsx")
        for side in (pristine / "Working").glob(f"{name} - *"):
            shutil.copy2(side, root / name / "Working" / side.name)
    old = root / "Rowan" / "Rowan - EN & ES.xlsx"
    (root / "idiograph-project.json").write_text(json.dumps({
        "name": "Dogs, a scratch project", "agents": {"allowed": True, "at": "2026-10-22T10:00:00+01:00"}}), encoding="utf-8")
    config_file = scratch / "quote-header-250-config.json"
    config_file.write_text(json.dumps({"root": str(root), "interviewer": "Adam"}), encoding="utf-8")

    def run(*args):
        return cli.run(["--root", str(root), "--config", str(config_file), *args])

    code_new, out_new, _ = run("statements", "Rowan", "--json")
    book = openpyxl.load_workbook(old, rich_text=True)
    book.worksheets[0].cell(1, 6).value = "Key quotes"
    book.save(old)
    shipped = scratch / "quote-header-250-shipped.xlsx"
    shutil.copy2(pristine / "Rowan - EN & ES.xlsx", shipped)
    then, now = wb_mod.read_case(old), wb_mod.read_case(shipped)
    check("250: the workbook headed Key quotes reads as the one headed Quote, every passage's quotes and pairs alike",
          heading(old)[5] == "Key quotes" and heading(shipped)[5] == "Quote"
          and then["sheets"] == now["sheets"] and any(r["kq"] for s in then["sheets"] for r in s["rows"]))

    code, out, err = run("statements", "Rowan", "--json")
    rows = json.loads(out)["statements"] if code == 0 and out.strip() else []
    check("250: the command line's statements gives the same answer, quotes and all, under either heading",
          code == 0 and code_new == 0 and rows and any(r["quotes"] for r in rows)
          and json.loads(out) == json.loads(out_new), err)

    turn = next(r for s in then["sheets"] for r in s["rows"] if r["name"] == "Rowan" and len(r["text"].split()) > 6)
    words = " ".join(turn["text"].split()[:5])
    spec = scratch / "quote-header-250-turn.json"
    spec.write_text(json.dumps({"statements": ["A made-up statement about the lead by the door"],
                                "notes": ["A made-up note."], "quotes": [words],
                                "request": "Code a made-up turn"}), encoding="utf-8")
    before = cells(old)
    code, out, err = run("turn", "write", "Rowan", turn["sheet"], str(turn["row"]), "--from", str(spec))
    after = cells(old)
    changed = {k for k in after if after[k] != before.get(k)} | {k for k in before if k not in after}
    row = next(r for s in wb_mod.read_case(old)["sheets"] for r in s["rows"] if r["row"] == turn["row"])
    letters = {f"{c}{turn['row']}" for c in "CEF"}
    check("250: a turn written to the old heading's workbook lands its quote in that column, the heading kept as it was",
          code == 0 and heading(old)[5] == "Key quotes" and words in row["kq"]
          and row["pairs"][0]["es"] == "A made-up statement about the lead by the door"
          and {k[1] for k in changed} <= letters, err or str(sorted(changed)))

    # C. the statements CSV says Quote, from either heading
    out_old = export_mod.export(old, scratch / "quote-header-250-old.csv")
    out_new = export_mod.export(shipped, scratch / "quote-header-250-new.csv")
    old_rows = list(csv.reader(io.StringIO((scratch / "quote-header-250-old.csv").read_text(encoding="utf-8-sig"))))
    new_rows = list(csv.reader(io.StringIO((scratch / "quote-header-250-new.csv").read_text(encoding="utf-8-sig"))))
    check("250: the statements CSV's last column is headed Quote, and the old heading's workbook gives its quotes there",
          old_rows[0][-1] == "Quote" and new_rows[0][-1] == "Quote" and export_mod.HEADER[-1] == "Quote"
          and out_old["statements"] == len(old_rows) - 1 and any(words in r[-1] for r in old_rows[1:])
          and sum(1 for r in new_rows[1:] if r[-1]) >= 1, f"{old_rows[0]} {new_rows[0]}")
