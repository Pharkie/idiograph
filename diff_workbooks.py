#!/usr/bin/env python3
"""Diff two EN & ES workbooks cell by cell with rich text kept, and report by column.

    diff_workbooks.py BEFORE.xlsx AFTER.xlsx [--crux-ok]

Reports every cell whose plain text or font runs differ, grouped by column, plus a check that
every orange run (theme 9) present in BEFORE is still present, run for run, in AFTER, unless the
row is one where the after-file has a different set of crux runs (a crux added or cleared in the
app). Column widths, freeze panes and zoom are compared too. Exit 0 on a clean report, 1 otherwise.
"""
import sys
import openpyxl
from openpyxl.cell.rich_text import CellRichText, TextBlock

def runs(value):
    if isinstance(value, CellRichText):
        out = []
        for part in value:
            if isinstance(part, TextBlock):
                f = part.font
                col = getattr(getattr(f, "color", None), "theme", None) if f is not None else None
                tint = getattr(getattr(f, "color", None), "tint", None) if f is not None else None
                out.append((str(part.text), col, tint, getattr(f, "b", None), getattr(f, "i", None)))
            else:
                out.append((str(part), None, None, None, None))
        return out
    return [(str(value if value is not None else ""), None, None, None, None)]

def text(value):
    return "".join(r[0] for r in runs(value))

def orange(value):
    return [r for r in runs(value) if r[1] == 9]

def main(a_path, b_path):
    a = openpyxl.load_workbook(a_path, rich_text=True)
    b = openpyxl.load_workbook(b_path, rich_text=True)
    bad = 0
    if a.sheetnames != b.sheetnames:
        print("SHEETS differ", a.sheetnames, b.sheetnames); bad += 1
    for name in a.sheetnames:
        wa, wb_ = a[name], b[name]
        by_col = {}
        for r in range(1, max(wa.max_row, wb_.max_row) + 1):
            for c in range(1, 7):
                va, vb = wa.cell(r, c).value, wb_.cell(r, c).value
                if runs(va) != runs(vb):
                    by_col.setdefault(c, []).append(r)
        for c in sorted(by_col):
            rows = by_col[c]
            print(f"{name} col {'ABCDEF'[c-1]}: {len(rows)} cells differ, rows {rows[:40]}{' ...' if len(rows) > 40 else ''}")
        # orange survival, row by row, on rows whose D text is unchanged
        lost = []
        for r in range(2, wa.max_row + 1):
            va, vb = wa.cell(r, 4).value, wb_.cell(r, 4).value
            if text(va) != text(vb):
                print(f"{name} row {r}: TRANSCRIPT TEXT CHANGED"); bad += 1
                continue
            oa, ob = orange(va), orange(vb)
            if oa and oa != ob:
                # a crux edit adds or removes runs; a lost run is one from BEFORE missing in AFTER
                missing = [x for x in oa if x not in ob]
                if missing:
                    lost.append((r, [m[0] for m in missing]))
        if lost:
            print(f"{name}: orange runs LOST on {len(lost)} rows: {lost[:10]}"); bad += 1
        else:
            print(f"{name}: every orange run from BEFORE survives")
        for col in "ABCDEF":
            if wa.column_dimensions[col].width != wb_.column_dimensions[col].width:
                print(f"{name}: width {col} changed"); bad += 1
        if wa.freeze_panes != wb_.freeze_panes or wa.sheet_view.zoomScale != wb_.sheet_view.zoomScale:
            print(f"{name}: freeze/zoom changed"); bad += 1
        fills = [(r, c) for r in range(1, wb_.max_row + 1) for c in range(1, 7) if wb_.cell(r, c).fill.fill_type]
        if fills:
            print(f"{name}: CELL FILLS present {fills[:5]}"); bad += 1
    print("RESULT", "clean" if bad == 0 else f"{bad} problem(s)")
    return 0 if bad == 0 else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
