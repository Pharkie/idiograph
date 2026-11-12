"""A page that draws a workbook's sheet as a spreadsheet shows it, from the file itself, for the Screenshots page's
clip of the workbook (siteclips, 12 November 2026). It reads the cells, the column widths, the fonts, the wrap and
the frozen panes with openpyxl, read only, and writes one HTML page: the file's name over the grid, the column
letters and the row numbers, the frozen header row and columns kept in place while the rest scrolls, and the sheet's
tabs at the foot. Nothing in it is typed by hand: what the grid holds is what the file holds. It is never a capture
of a spreadsheet program's window, and it carries no program's name or marks.

usage: python3 packaging/motion/clips/sheet.py <workbook.xlsx> <out.html> [--sheet Initial] [--zoom 100]
"""
import argparse
import html
from pathlib import Path

import openpyxl
from openpyxl.utils import get_column_letter, column_index_from_string


def px(width_chars: float, zoom: float) -> int:
    # a column's width in characters of the default font, as a spreadsheet turns it into pixels (seven a
    # character of an 11 point Calibri, five more for the cell's margins), at the zoom
    return round((width_chars * 7 + 5) * zoom)


def page(book: Path, sheet: str | None, zoom: float) -> str:
    wb = openpyxl.load_workbook(book, read_only=False)
    ws = wb[sheet] if sheet else wb.worksheets[0]
    used = ws.max_column
    # and a few empty columns past the last, as a spreadsheet goes on to the right
    cols = used + 3
    widths = [px((ws.column_dimensions[get_column_letter(c)].width if c <= used else None) or 8.43, zoom)
              for c in range(1, cols + 1)]
    frozen_row, frozen_col = 0, 0
    if ws.freeze_panes:
        letters = "".join(ch for ch in ws.freeze_panes if ch.isalpha())
        frozen_col = column_index_from_string(letters) - 1
        frozen_row = int("".join(ch for ch in ws.freeze_panes if ch.isdigit())) - 1
    rows = []
    for r, row in enumerate(ws.iter_rows(min_row=1, max_row=ws.max_row), start=1):
        cells = []
        for c, cell in enumerate(row, start=1):
            v = cell.value
            text = "" if v is None else str(v)
            f = cell.font
            style = []
            if f is not None and f.b:
                style.append("font-weight:700")
            if f is not None and f.i:
                style.append("font-style:italic")
            cls = []
            if c <= frozen_col:
                cls.append("fc")
            if c == frozen_col:
                cls.append("fe")
            cells.append(f'<td class="{" ".join(cls)}" style="{";".join(style)}">{html.escape(text)}</td>')
        cells.extend("<td></td>" for _ in range(cols - used))
        rcls = ' class="fr"' if r <= frozen_row else ""
        rows.append(f'<tr{rcls}><th class="rn">{r}</th>{"".join(cells)}</tr>')
    font = ws["A1"].font
    family = (font.name if font is not None and font.name else "Calibri")
    size = (font.sz if font is not None and font.sz else 11) * zoom
    head = "".join(f'<th class="cl{" fc" if c <= frozen_col else ""}{" fe" if c == frozen_col else ""}">{get_column_letter(c)}</th>'
                   for c in range(1, cols + 1))
    colgroup = '<col style="width:44px">' + "".join(f'<col style="width:{w}px">' for w in widths)
    tabs = "".join(f'<span class="tab{" on" if s.title == ws.title else ""}">{html.escape(s.title)}</span>' for s in wb.worksheets)
    # each frozen column's left edge, past the row numbers, for its sticky place
    lefts, x = [], 44
    for w in widths[:frozen_col]:
        lefts.append(x)
        x += w
    sticky = "".join(f"tr > :nth-child({i + 2}).fc {{ left: {left}px; }}\n" for i, left in enumerate(lefts))
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(book.name)}</title><style>
html, body {{ margin: 0; height: 100%; background: #fff; }}
body {{ display: flex; flex-direction: column; font: {size:.2f}pt "{family}", Carlito, "Helvetica Neue", Arial, sans-serif; color: #000; }}
.name {{ flex: none; height: 34px; display: flex; align-items: center; justify-content: center; background: #f3f3f3;
  border-bottom: 1px solid #d0d0d0; font: 600 13px -apple-system, "Helvetica Neue", Arial, sans-serif; color: #333; }}
.grid {{ flex: 1; overflow: auto; position: relative; }}
table {{ border-collapse: separate; border-spacing: 0; table-layout: fixed; width: max-content; }}
td, th {{ border-right: 1px solid #dadada; border-bottom: 1px solid #dadada; padding: 2px 4px 3px; vertical-align: top;
  white-space: pre-wrap; overflow-wrap: anywhere; line-height: 1.22; background: #fff; }}
thead th {{ position: sticky; top: 0; z-index: 3; background: #f0f0f0; color: #555; font: 12px/16px -apple-system, "Helvetica Neue", Arial, sans-serif;
  text-align: center; padding: 3px 0; border-color: #cfcfcf; height: 22px; box-sizing: border-box; }}
th.rn {{ position: sticky; left: 0; z-index: 2; background: #f0f0f0; color: #555; font: 12px -apple-system, "Helvetica Neue", Arial, sans-serif;
  text-align: center; padding: 3px 0; border-color: #cfcfcf; }}
thead th.rn {{ z-index: 5; }}
tr.fr td, tr.fr th.rn {{ position: sticky; top: 22px; z-index: 2; }}
tr.fr th.rn {{ z-index: 4; }}
.fc {{ position: sticky; z-index: 1; }}
tr.fr .fc {{ z-index: 4; }}
thead .fc {{ z-index: 4; }}
{sticky}
tr.fr td {{ border-bottom: 1.5px solid #9a9a9a; }}
.fe {{ border-right: 1.5px solid #9a9a9a !important; }}
.tabs {{ flex: none; height: 30px; display: flex; align-items: stretch; background: #f3f3f3; border-top: 1px solid #d0d0d0;
  padding-left: 52px; font: 13px -apple-system, "Helvetica Neue", Arial, sans-serif; }}
.tab {{ display: flex; align-items: center; padding: 0 18px; color: #444; }}
.tab.on {{ background: #fff; font-weight: 600; color: #111; box-shadow: inset 0 -2px 0 #555; }}
</style></head><body>
<div class="name">{html.escape(book.name)}</div>
<div class="grid"><table><colgroup>{colgroup}</colgroup><thead><tr><th class="rn"></th>{head}</tr></thead><tbody>
{"".join(rows)}
</tbody></table></div>
<div class="tabs">{tabs}</div>
</body></html>"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("book", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--sheet", default=None)
    ap.add_argument("--zoom", type=float, default=100)
    a = ap.parse_args()
    a.out.write_text(page(a.book, a.sheet, a.zoom / 100), encoding="utf-8")
    print(a.out)


if __name__ == "__main__":
    main()
