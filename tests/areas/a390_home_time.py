"""Area 390: Home shows the projects soon after the app opens and at once on the way back (perfreview, 13 November 2026).

Adam, 13 November: "you open the home screen and there's a clear two or three second delay before the projects
appear", where it used to be quick. Home draws nothing until its case list, /api/cases, comes back. On the first visit
after the app starts that list opens every participant's workbook and raw source, and on every visit it read each
participant's themes file twice, for the Current board's name and the PETs mark. A themes file keeps every board's
History whole, four to seven megabytes on his own study, which cost him about 260 ms a visit and three parses of each
on the first. Now a raw source's rows are never walked, only an annotated workbook's turns being counted, and the
board's name, the PETs mark and the board count are read from one parse and kept until the file changes.
Here, on two invented projects at the scale of his two, a study of six participants learning to garden late in life,
each a workbook and a raw source of 1,700 to 2,700 rows and a PETs board of 105 cards, and a study of eight learning to
sail over three timepoints, each workbook three sheets of 700 rows, with Work in rounds on: in the suite's own process
the first case list walks no raw source's rows, and a second opens no workbook and reads no themes file again, and in
WebKit, the Mac window's engine, at 1587 by 1234, the first open with nothing read shows the projects within 2 s and
a reload within half a second, tried once more when the machine's load starves the window.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import date, timedelta
from pathlib import Path

import openpyxl

from . import support
from .support import check, skip

OPEN = ["The first bed I dug", "My hands in the soil", "The smell after rain", "The frost on the leeks",
        "The seedlings on the sill", "Lifting the compost", "The cold in February", "Learning the names",
        "My back the day after", "The slugs in the lettuce", "The first tomato", "My son at the gate",
        "The quiet of the allotment", "Being the slowest in the class", "The rain on the shed roof", "Talking to the plants"]
TAIL = ["felt like being let into a secret nobody had told me about, and I kept it close for weeks.",
        "made me clumsy at first and then, slowly, less so, until my hands knew what to do before I did.",
        "was the part of the week I kept for myself and told nobody about, not even my sister.",
        "showed me how much I had stopped trying new things since the shop closed and the house went quiet."]
ASK = ["And then?", "What was that like?", "Say more about that.", "How did that feel?"]
PLAN = [("Becoming someone who grows things", 3, [10, 6, 4]), ("The plot as a place of her own", 2, [8, 5, 7, 3]),
        ("A body that learns slowly", 4, [9, 2]), ("Fear, and going back anyway", 0, [6, 6, 5]),
        ("Who she is among the others", 5, [4, 3]), ("Time measured by the seasons", 1, [7, 5])]
GARDENERS = ["Hazel", "Ines", "Bram", "Tove", "Lark", "Wren"]
SAILORS = ["Tamsin", "Ivo", "Nell", "Fern", "Odile", "Pip", "Quill", "Pim"]

# when the first project card is in the page and the frame after it drawn, from the navigation's start
HOME_INIT = r"""
(() => {
  const hm = { inDom: null, shown: null };
  window.__hm = hm;
  new MutationObserver(() => {
    if (hm.inDom === null && document.querySelector('#projects .home-card')) {
      hm.inDom = performance.now();
      requestAnimationFrame(() => requestAnimationFrame(() => { hm.shown = Math.round(performance.now()); }));
    }
  }).observe(document, { subtree: true, childList: true });
})();
"""
WAIT = ("new Promise((r) => { const t0 = Date.now(); const f = () => (window.__hm && window.__hm.shown) || Date.now() - t0 > 15000 "
        "? r({ shown: window.__hm && window.__hm.shown, cards: document.querySelectorAll('#projects .home-card').length }) "
        ": setTimeout(f, 20); f(); })")


def said(n: int) -> str:
    return f"{OPEN[n % len(OPEN)]} {TAIL[(n // len(OPEN)) % len(TAIL)]}"


def stamp(k: int) -> str:
    s = 4 + k * 9
    return f"{s // 3600:02d}:{(s // 60) % 60:02d}:{s % 60:02d}"


def make_case(root: Path, folder: str, speaker: str, sheets: list, per_sheet: int, places: dict | None = None) -> Path:
    """A participant's raw source and workbook, a statement on every eighth turn of each sheet up to `per_sheet`, and a
    progress file with eight weeks of rounds and each later sheet's timepoint."""
    import workbook as wb_mod
    case = root / folder
    (case / "Source").mkdir(parents=True)
    raw = openpyxl.Workbook()
    raw.remove(raw.active)
    for name, rows in sheets:
        ws = raw.create_sheet(name)
        ws.append(["Name", "Timestamp", "Transcript"])
        for k in range(rows // 2):
            ws.append(["Interviewer", stamp(2 * k), ASK[k % len(ASK)]])
            ws.append([speaker, stamp(2 * k + 1), said(k)])
    source = case / "Source" / f"{folder} - interview.xlsx"
    raw.save(source)
    book = wb_mod.create_from_source(source, case / f"{folder} - EN & ES.xlsx")
    wb = openpyxl.load_workbook(book, rich_text=True)
    rows_kept, n = {}, 0
    for ws, (name, _rows) in zip(wb.worksheets, sheets):
        cols = wb_mod.detect_columns(ws)
        for j in range(per_sheet):
            r = 3 + 8 * j
            ws.cell(r, cols["es"]).value = " ".join(said(n).split()[:5 + 5 * (n % 4)])
            rows_kept[f"{name}:{r}"] = "has-content"
            n += 1
    wb.save(book)
    today = date(2026, 11, 13)
    days = {(today - timedelta(days=d)).isoformat(): {"rounds": 1 + d % 4} for d in range(0, 56, 2)}
    progress = {"version": 1, "rows": rows_kept, "rounds": {}, "days": days, "last": None, "flags": [], "trims": []}
    if places:
        progress["timepoints"] = places
    (case / "Working").mkdir(exist_ok=True)
    (case / "Working" / f"{book.stem}.progress.json").write_text(json.dumps(progress), encoding="utf-8")
    return book


def test_home_time(scratch: Path):
    print("\n390. Home shows the projects soon after the app opens and at once on the way back, 13 November: two "
          "projects at the scale of Adam's, the first list walking no raw source's rows, a second reading nothing "
          "again, and in WebKit the projects within 2 s of a first open and half a second of a reload")
    import platform
    import threading
    from http.server import ThreadingHTTPServer
    import cli
    import idiograph_routes
    import locks
    import server as server_mod
    import themes
    import workbook as wb_mod

    base = scratch / "home-time-390"
    shutil.rmtree(base, ignore_errors=True)
    gardens, tides = base / "Gardens", base / "Tides"
    config_file = base / "config-390.json"
    for root, name, q in ((gardens, "Gardens", "How do adults experience learning to garden late in life?"),
                          (tides, "Tides", "How does learning to sail change over a year?")):
        root.mkdir(parents=True)
        (root / server_mod.PROJECT_FILE).write_text(json.dumps({"name": name, "research_question": q,
            "agents": {"allowed": True, "at": "2026-11-13T09:00:00+00:00"}}), encoding="utf-8")
    config_file.write_text(json.dumps({"projects": [{"root": str(gardens)}, {"root": str(tides)}], "interviewer": "Interviewer",
                                       "corpus": "", "gravity_reference": "", "corpus_exclude": [], "card_quotes": True,
                                       "work_in_rounds": True}), encoding="utf-8")

    def run(root: Path, *args):
        return cli.run(["--config", str(config_file), "--root", str(root), *args])

    failed = []
    for i, who in enumerate(GARDENERS, start=1):
        make_case(gardens, f"P{i} - {who}", who, [("Initial", 1500 + 200 * i)], 112)
        failed.append(run(gardens, "board", "fresh", who, "--start", "empty", "--note", "A board", "--tool", "Claude Code"))
        f = next((gardens / f"P{i} - {who}" / "Working").glob("* - EN & ES.themes.json"))
        name = themes.current_version(json.loads(f.read_text(encoding="utf-8")))["name"]
        ids = iter(range(1, 113))
        ops = []
        for p, (title, own, subs) in enumerate(PLAN, start=1):
            ops.append({"op": "make", "ref": f"p{p}", "title": title, "inside": None, "members": [f"S{next(ids)}" for _ in range(own)]})
            ops += [{"op": "make", "ref": f"p{p}s{s}", "title": f"Part {s}", "inside": f"p{p}",
                     "members": [f"S{next(ids)}" for _ in range(size)]} for s, size in enumerate(subs, start=1)]
        ops += [{"op": "stack", "items": [f"S{k}"], "under": u} for k, u in zip(range(106, 113), ["S5", "S20", "S33", "S48", "S61", "S77", "S90"])]
        spec = base / "ops.json"
        spec.write_text(json.dumps({"operations": ops}), encoding="utf-8")
        failed.append(run(gardens, "board", "apply", who, name, "--ops", str(spec), "--note", "Build", "--tool", "Claude Code"))
    tps = base / "tp.json"
    tps.write_text(json.dumps([{"label": "Before", "description": "Before the first season"},
                               {"label": "Six months", "description": "After the summer"},
                               {"label": "A year", "description": "A year on"}]), encoding="utf-8")
    failed.append(run(tides, "timepoints", "--from", str(tps), "--note", "Three", "--tool", "Claude Code"))
    for i, who in enumerate(SAILORS, start=1):
        make_case(tides, f"P{i} - {who}", who, [("Before", 700), ("Six months", 700), ("A year", 700)], 38,
                  {"Six months": 2, "A year": 3})
        failed.append(run(tides, "board", "fresh", who, "--start", "empty", "--note", "A board", "--tool", "Claude Code"))
    bad = [r for r in failed if r[0] != 0]
    if bad:
        check("390: the two invented projects are built through the command line", False, (bad[0][1] + bad[0][2])[-400:])
        return

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY, locks.WAIT)
    caches = (idiograph_routes.BOOKS, idiograph_routes.TURNS, idiograph_routes.BOARDS, getattr(idiograph_routes, "THEMES_HEADS", {}),
              idiograph_routes.GETS_FILES)

    def cold():
        for c in caches:
            c.clear()

    def swap():
        server_mod.CONFIG_PATH = config_file
        server_mod.ROOT_OVERRIDE = None
        server_mod.STATE_PATH = base / "state-390.json"
        server_mod.STATE_MEMORY = {"recent": []}

    # in the suite's own process: what the first case list and a second one read
    opened, walked, themes_read = [], [], []
    real_open, real_whole, real_text = openpyxl.load_workbook, wb_mod.whole, Path.read_text
    from openpyxl.worksheet._read_only import ReadOnlyWorksheet
    real_rows = ReadOnlyWorksheet.iter_rows
    reading = {"path": None}

    def whole(path):
        reading["path"] = Path(path)
        return real_whole(path)

    def load_workbook(*a, **k):
        what = a[0] if a else k.get("filename")
        opened.append(Path(what if isinstance(what, (str, Path)) else getattr(what, "name", "") or ""))
        return real_open(*a, **k)

    # every row read, by the workbook it is read from: a raw source's heading rows alone, one a sheet, read for its
    # columns, and none of its turns
    def iter_rows(self, *a, **k):
        for row in real_rows(self, *a, **k):
            walked.append(reading["path"])
            yield row

    def read_text(self, *a, **k):
        if self.name.endswith(".themes.json"):
            themes_read.append(self)
        return real_text(self, *a, **k)

    try:
        swap()
        cold()
        openpyxl.load_workbook, wb_mod.whole, ReadOnlyWorksheet.iter_rows, Path.read_text = load_workbook, whole, iter_rows, read_text
        first = idiograph_routes.api_cases({})
        here = str(base.resolve())
        mine = lambda paths: [q for q in paths if q is not None and str(q) and str(Path(q).resolve()).startswith(here)]
        raw_walked = [q for q in mine(walked) if "Source" in q.parts]
        first_opened = len(mine(opened))
        opened.clear(), walked.clear(), themes_read.clear()
        second = idiograph_routes.api_cases({})
    finally:
        openpyxl.load_workbook, wb_mod.whole, ReadOnlyWorksheet.iter_rows, Path.read_text = real_open, real_whole, real_rows, real_text
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY, locks.WAIT = kept
    rows = [len(s["participants"]) for s in first.get("projects", [])]
    check("390: the first case list of two projects, six participants and eight, opens each workbook and raw source once "
          "and reads no more of a raw source than each sheet's heading", rows == [6, 8] and first_opened == 28
          and len(raw_walked) <= 6 + 8 * 3, f"rows {rows}, opened {first_opened}, raw sources' rows read {len(raw_walked)}")
    check("390: a second case list, nothing changed, opens no workbook and reads no themes file again, and answers the "
          "same", not mine(opened) and not mine(themes_read) and json.dumps(second["projects"], sort_keys=True, default=str)
          == json.dumps(first["projects"], sort_keys=True, default=str),
          f"workbooks {len(mine(opened))}, themes files {len(mine(themes_read))}")

    # in WebKit: the first open with nothing read, then a reload
    swiftc = shutil.which("swiftc")
    if platform.system() != "Darwin" or not swiftc:
        skip("390: Home's time to its projects in the Mac's own window engine", "WebKit's window engine is the Mac's alone")
        return
    tool = next((p for p in (scratch / "a378-wk_shot", scratch / "a376-wk_shot", scratch / "a192-wk_shot") if p.exists()), None)
    if tool is None:
        tool = scratch / "a390-wk_shot"
        compiled = subprocess.run([swiftc, "-O", str(support.source("packaging/wk_shot.swift")), "-o", str(tool)],
                                  capture_output=True, text=True, encoding="utf-8", timeout=600)
        if compiled.returncode != 0:
            check("390: wk_shot builds for the WebKit check", False, compiled.stderr[-400:])
            return
    steps_file = base / "steps.json"

    def drive():
        cold()
        httpd = None
        try:
            swap()
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
            threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
            url = f"http://127.0.0.1:{httpd.server_address[1]}/"
            steps_file.write_text(json.dumps([{"js": WAIT, "wait": 50}, {"load": url}, {"js": WAIT, "wait": 50}]), encoding="utf-8")
            ran = subprocess.run([str(tool), "--url", url, "--out", str(base / "wk"), "--steps", str(steps_file), "--width", "1587",
                                  "--height", "1234", "--scale", "1", "--no-still", "--init", HOME_INIT, "--timeout", "120"],
                                 capture_output=True, text=True, encoding="utf-8", timeout=180)
        finally:
            if httpd:
                httpd.shutdown()
                httpd.server_close()
            server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY, locks.WAIT = kept
        got = {}
        for line in ran.stdout.splitlines():
            if line.startswith("js ") and ": " in line:
                try:
                    got[int(line[3:line.index(":")])] = json.loads(line[line.index(":") + 2:])
                except ValueError:
                    pass
        return ran, got

    def quick(got: dict) -> bool:
        a, b = got.get(0) or {}, got.get(2) or {}
        return (a.get("cards", 0) >= 2 and b.get("cards", 0) >= 2 and (a.get("shown") or 99999) <= 2000
                and (b.get("shown") or 99999) <= 500)

    ran, got = drive()
    # under a full gate's load the offscreen window can be starved, which says nothing of the page: once more
    if ran.returncode != 0 or not quick(got):
        ran, got = drive()
    check("390: in WebKit at 1587 by 1234, Home's first open with nothing read shows the two projects within 2 s of the "
          "navigation and a reload within half a second", ran.returncode == 0 and quick(got),
          f"first {got.get(0)}, reload {got.get(2)} {ran.stderr[-300:]}")
