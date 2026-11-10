from __future__ import annotations

import inspect
import re

import openpyxl
from openpyxl.cell.rich_text import TextBlock

import rounds as rounds_mod
import workbook as wb_mod

from . import support
from .support import check, skip, suite_text
import idiograph_routes


def test_demo(scratch):
    print("\n28. The bundled demo case")
    import make_demo
    import server as server_mod
    if not make_demo.SOURCE_CSV.exists():
        return skip("demo", f"no transcript at {make_demo.SOURCE_CSV.name}")

    # ── A. the transcript
    rows = make_demo.read_turns()
    text = " ".join(r["Transcript"] for r in rows)
    spoken = len([w for w in text.split() if any(c.isalnum() for c in w)])
    check("the demo CSV parses as a raw source",
          list(rows[0]) == ["Name", "Timestamp", "Transcript"]
          and wb_mod.is_raw_source({"name": 1, "ts": 2, "transcript": 3}),
          f"{len(rows)} turns, the three columns create_from_source reads")
    check("it is the length of a real interview",
          60 <= len(rows) <= 90 and 3800 <= spoken <= 4800,
          f"{len(rows)} turns, {spoken} spoken words")
    names = {r["Name"].strip() for r in rows}
    check("two speakers, the interviewer from config.json and the participant",
          names == {make_demo.interviewer(), make_demo.PARTICIPANT},
          f"{sorted(names)}")
    check("no em dash and no semicolon anywhere in it",
          "\u2014" not in text and ";" not in text and "\u2013" not in text,
          "the house style holds in the invented transcript too")
    seconds = [wb_mod.ts_seconds(r["Timestamp"]) for r in rows]
    check("the timecodes start at nothing and only ever go forward",
          seconds[0] == 0 and all(b > a for a, b in zip(seconds, seconds[1:])),
          f"ending at {wb_mod.timecode(seconds[-1])}, written from the measured clips")

    # The denylist is built here, from the pseudonyms the README, the two docs and this file already
    # carry. The real-name register is never read, by this or by anything else in the tool.
    readme = support.source("README.md").read_text(encoding="utf-8")
    manual = support.source("docs/manual.md").read_text(encoding="utf-8")
    internals = support.source("docs/internals.md").read_text(encoding="utf-8")
    denied = {m.group(1) for src in (readme, manual, internals, suite_text())
              for m in re.finditer(r"P\d+\s*-?\s*([A-Z][a-z]{2,})", src)}
    # `P<n> <Pseudonym>` is the shape itself, and `P9 - Nobody` is the invented folder the root
    # guard is tested against. Neither is anybody's pseudonym, and Nobody is an ordinary word.
    denied -= {"Pseudonym", "Nobody"}
    hits = sorted(n for n in denied if re.search(rf"\b{n}\b", text))
    check("no pseudonym from the real cases appears in the demo", not hits,
          f"{len(denied)} names checked" if not hits else f"found {hits}")

    # ── B. Juno's workbook, built in a scratch folder so the demo that ships is never opened for
    # writing, finished as the whole demo is since 26 October: every turn of hers annotated
    import shutil
    where = scratch / "demo"
    shutil.rmtree(where, ignore_errors=True)
    built = make_demo.build_written(make_demo.PARTICIPANT, where)["workbook"]
    case = wb_mod.read_case(built)
    sheet = case["sheets"][0]
    cols = sheet["columns"]
    check("the workbook builds from the CSV through create_from_source",
          built.exists() and len(sheet["rows"]) == len(rows)
          and {"name", "ts", "es", "transcript", "en", "kq"} <= set(cols),
          f"{len(sheet['rows'])} rows, Adam's six columns")
    made = sheet["rows"]
    hers = [r for r in made if r["name"] == make_demo.PARTICIPANT]
    check("every turn of hers carries statements, a note and a key quote, and none of the interviewer's does",
          hers and all(r["es"].strip() and r["en"].strip() and r["kq"].strip() for r in hers)
          and not any(r["es"].strip() or r["en"].strip() or r["kq"].strip() for r in made if r not in hers),
          f"{len(hers)} turns of hers")
    lengths = [len(line.split()) for r in hers for line in r["es"].splitlines() if line.strip()]
    check("her statements are in the register they are written in",
          lengths and all(2 <= n <= 10 for n in lengths) and not any('"' in r["es"] for r in hers),
          f"{len(lengths)} statements, {min(lengths)} to {max(lengths)} words")
    check("every key quote is verbatim from its turn, in inverted commas",
          all(q.startswith('"') and q.endswith('"') and q.strip('"') in r["text"]
              for r in hers for q in r["kq"].splitlines() if q.strip()),
          "the quote is in inverted commas and its words are in the turn")
    marked = [(r["row"], "".join(x["text"] for x in r["runs"] if x["crux"])) for r in made
              if any(x["crux"] for x in r["runs"])]
    wb = openpyxl.load_workbook(built, rich_text=True)
    ws = wb[make_demo.SHEET]
    runs = [b for row, _ in marked for b in ws.cell(row, cols["transcript"]).value
            if isinstance(b, TextBlock)]
    fills = [c.fill.fgColor.rgb for r in ws.iter_rows() for c in r
             if c.fill is not None and c.fill.fill_type]
    wb.close()
    by_row = {r["row"]: r for r in made}
    check("her highlights are stored as real orange runs",
          len(marked) >= 2 and all(phrase and phrase in by_row[row]["text"] for row, phrase in marked)
          and any(wb_mod.is_crux_font(b.font) for b in runs),
          f"theme {wb_mod.CRUX_THEME} runs on rows {[r for r, _ in marked]}")
    check("and no cell anywhere in the demo carries a fill", not fills,
          "the crux is a font run, the way it is everywhere else")
    flags = rounds_mod.load_progress(built).get("flags", [])
    check("no turn flagged in the sidecar, since the app has no flags", flags == [], repr(flags))

    # ── C. reset, byte for byte, from a pristine copy of the build
    pristine = where / "pristine"
    (pristine / "Working").mkdir(parents=True, exist_ok=True)
    side = rounds_mod.progress_path(built)
    shutil.copyfile(built, pristine / built.name)
    shutil.copyfile(side, pristine / "Working" / side.name)
    first = next(r["row"] for r in hers)
    wb_mod.save_turn(built, make_demo.SHEET, first, "A statement written on camera", None, None)
    progress = rounds_mod.load_progress(built)
    progress["rows"].pop(rounds_mod.row_key(make_demo.SHEET, hers[-1]["row"]), None)
    rounds_mod.save_progress(built, progress)
    changed = built.read_bytes() != (pristine / built.name).read_bytes()
    make_demo.reset(pristine, built)
    check("Reset demo puts the workbook and the sidecar back byte for byte",
          changed and built.read_bytes() == (pristine / built.name).read_bytes()
          and side.read_bytes() == (pristine / "Working" / side.name).read_bytes(),
          "the pristine copy is the only thing it reads")

    # ── D. the root guard
    demo_dir = server_mod.DEMO_DIR
    check("within_root accepts the demo folder and refuses everything around it",
          server_mod.within_root(demo_dir / "Juno" / "Juno - EN & ES.xlsx")
          and server_mod.within_root(demo_dir)
          and not server_mod.within_root(demo_dir.parent)
          and not server_mod.within_root(demo_dir.parent / "static" / "app.js")
          and not server_mod.within_root(demo_dir.parent / "config.json"),
          "one folder through, its parent and every sibling refused")
    saved_root = server_mod.ROOT_OVERRIDE
    server_mod.ROOT_OVERRIDE = str(scratch / "guard-root")
    try:
        refused = False
        try:
            idiograph_routes.case_path("Other Study/Data collection and analysis/Main Data/x.xlsx")
        except server_mod.OutsideRoot:
            refused = True
        check("a scratch root still cannot reach a live case", refused,
              "the demo folder is the only thing the guard added")
        check("and the demo is still reachable from a scratch root",
              idiograph_routes.case_path(str(server_mod.DEMO_WORKBOOK)) == server_mod.DEMO_WORKBOOK,
              "it travels with the app, not with the root")
    finally:
        server_mod.ROOT_OVERRIDE = saved_root
    check("the demo is kept out of the recent list",
          "if srv.is_demo(path):" in inspect.getsource(idiograph_routes.remember)
          and "or srv.is_demo(path):" in inspect.getsource(idiograph_routes.recent_entries)
          and "recent_entries(cases)" in inspect.getsource(idiograph_routes.api_cases),
          "remember writes no entry for it and api_cases drops one already there")

    # ── E. the landing page and the header
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    check("the reset asks first and says what goes",
          "await askSure(gone)" in js and "/api/reset-demo" in js
          and "/api/reset-demo" in inspect.getsource(idiograph_routes),
          "a confirm in front of it, and the endpoint behind it")
