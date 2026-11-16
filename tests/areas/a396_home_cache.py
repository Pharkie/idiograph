"""Area 396: Home's read cache kept across a restart (homecache, 16 November 2026).

Home's case list keeps what it read of each workbook, progress file and themes file in memory, and since homecache
writes it to `home-cache.json` beside the app's state, so the first list after a restart opens no file that has not
changed. What is checked, on an invented project of three participants, each a copy of the demo's workbook, one with a
board. The cache is written beside the state file and nowhere in the project, and a list after a restart answers the
same as one that reads everything, opening no workbook and no themes file. A file changed while the app was closed is
never shown from the cache: a workbook given a statement, a board renamed, and a progress file put back the same size
with its old time, each read again and answering what a list with no cache answers. A corrupt cache file, one in
another shape, and one from another version of the app are each ignored, the list answering as with none, and the
next write replacing it. A run of one project (--root) and a state file inside a project's folder write no cache.
"""
from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path

from . import support
from .support import check


def test_home_cache(scratch: Path):
    print("\n396. Home's read cache across a restart: written beside the state, the first list after a restart "
          "opening nothing unchanged and answering the same, a changed workbook, board or progress file never "
          "shown from it, a corrupt or foreign cache ignored, none for a run of one project (16 November)")
    import openpyxl
    import cli
    import idiograph_routes as routes
    import home_cache
    import server as server_mod
    import workbook as wb_mod

    base = scratch / "home-cache-396"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Learning to sail"
    root.mkdir(parents=True)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({"name": "Learning to sail", "research_question": "How?",
        "agents": {"allowed": True, "at": "2026-11-16T09:00:00+00:00"}}), encoding="utf-8")
    books = {}
    for n, who in enumerate(("Dara", "Ezra", "Fen"), 1):
        books[who] = support.demo_copy(root, f"P{n} - {who}", f"P{n} - {who} - EN & ES.xlsx")
    _sheet, her, him = support.demo_sheet(books["Dara"])
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": him, "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    code = cli.run(["--config", str(config_file), "--root", str(root), "board", "fresh", "Ezra", "--name", "Sketch",
                    "--start", "empty", "--note", "A board", "--tool", "Claude Code"])[0]
    code = code or cli.run(["--config", str(config_file), "--root", str(root), "board", "current", "Ezra", "Sketch",
                            "--note", "Current", "--tool", "Claude Code"])[0]
    check("396: the invented project, three participants and a board, is made", code == 0, str(code))
    if code != 0:
        return
    state = base / "state.json"
    cache = base / home_cache.NAME
    tables = (routes.BOOKS, routes.TURNS, routes.THEMES_HEADS, routes.BOARDS, routes.GETS_FILES, routes.NAMES_HELD)
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
            routes.HOME_CACHE_AFTER)
    here = str(base.resolve())
    opened, themes_read = [], []
    real_whole, real_text = wb_mod.whole, Path.read_text

    def whole(path):
        opened.append(str(Path(path).resolve()))
        return real_whole(path)

    def read_text(self, *a, **k):
        if self.name.endswith(".themes.json") and self.exists():
            themes_read.append(str(self.resolve()))
        return real_text(self, *a, **k)

    def mine(paths):
        return [p for p in paths if p.startswith(here)]

    def start(path):
        """A restart: the tables empty, as a new process has them, and the cache at `path` read (None, none)."""
        for t in tables:
            t.clear()
        routes.home_cache_open(path)
        routes.home_cache_wait()

    def listed():
        opened.clear(), themes_read.clear()
        got = routes.api_cases({})
        return json.dumps(got["projects"], sort_keys=True, default=str)

    def boards(text):
        """Every Current board's name the list gives its participants."""
        out = set()

        def walk(v):
            if isinstance(v, dict):
                if isinstance(v.get("board"), str) and v.get("board"):
                    out.add(v["board"])
                for x in v.values():
                    walk(x)
            elif isinstance(v, list):
                for x in v:
                    walk(x)
        walk(json.loads(text))
        return out

    def settle():
        """The background write after a list finished."""
        t0 = time.time()
        while routes.HOME_CACHE.get("timer") is not None and time.time() - t0 < 15:
            time.sleep(0.02)

    def truth():
        """The list as it reads with no cache at all."""
        start(None)
        return listed()

    def restarted():
        start(cache)
        out = listed()
        settle()
        return out

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = state, {"recent": []}
        routes.HOME_CACHE_AFTER = 0.05
        wb_mod.whole, Path.read_text = whole, read_text

        # ── 1. written beside the state, nowhere in the project, and the list after a restart reads nothing
        first = truth()
        start(cache)
        listed()
        settle()
        inside = [p for p in root.rglob("*") if home_cache.NAME in p.name]
        check("396: after a list the cache is written beside the state file, nothing of it in the project",
              cache.is_file() and not inside and not list(base.glob(f"{home_cache.NAME}.*.tmp")),
              f"cache {cache.is_file()}, in the project {len(inside)}")
        again = restarted()
        check("396: the first list after a restart answers as a full read does and opens no workbook and no themes "
              "file of the project", again == first and not mine(opened) and not mine(themes_read),
              f"same {again == first}, workbooks {len(mine(opened))}, themes files {len(mine(themes_read))}")

        # ── 2. a workbook given a statement while the app was closed
        wb = openpyxl.load_workbook(books["Fen"], rich_text=True)
        ws = wb[support.DEMO_SHEET]
        cols = wb_mod.detect_columns(ws)
        row = next(r for r in range(2, ws.max_row + 1) if ws.cell(r, cols["name"]).value == her
                   and not str(ws.cell(r, cols["es"]).value or "").strip())
        ws.cell(row, cols["es"]).value = "A first time at the helm"
        wb.save(books["Fen"])
        after = restarted()
        reread = str(books["Fen"].resolve()) in opened and str(books["Dara"].resolve()) not in opened
        fresh = truth()
        check("396: a workbook given a statement while the app was closed is read again, never shown from the cache",
              after == fresh and after != first and reread,
              f"same as a full read {after == fresh}, changed {after != first}")

        # ── 3. a board renamed while the app was closed
        start(cache)
        listed()
        settle()
        code = cli.run(["--config", str(config_file), "--root", str(root), "board", "rename", "Ezra", "Sketch",
                        "First sketch", "--note", "Rename", "--tool", "Claude Code"])[0]
        after = restarted()
        fresh = truth()
        check("396: a board renamed while the app was closed is read again, never shown from the cache",
              code == 0 and after == fresh and boards(after) == {"First sketch"},
              f"code {code}, same as a full read {after == fresh}, boards {sorted(boards(after))}")

        # ── 4. a progress file put back the same size with its old time: its inode is new
        start(cache)
        listed()
        settle()
        turns = routes.read_book(books["Dara"])["turns"][support.DEMO_SHEET]
        last = max(r for r, speaker, _has in turns if speaker and speaker.lower() != him.lower())
        progress = routes.rounds_mod.progress_path(books["Dara"])
        progress.parent.mkdir(exist_ok=True)
        body = {"version": 1, "rows": {f"{support.DEMO_SHEET}:{last}": "reviewed-empty"}, "rounds": {}, "days": {},
                "last": None, "flags": [], "trims": []}
        progress.write_text(json.dumps(body), encoding="utf-8")
        start(cache)
        before_swap = listed()
        settle()
        st = progress.stat()
        swapped = json.dumps(dict(body, rows={f"{support.DEMO_SHEET}:{last}": "unvisited-zzzz"}))
        tmp = progress.with_name("swap.tmp")
        tmp.write_text(swapped, encoding="utf-8")
        os.replace(tmp, progress)
        os.utime(progress, ns=(st.st_atime_ns, st.st_mtime_ns))
        same = progress.stat()
        after = restarted()
        fresh = truth()
        check("396: a progress file put back the same size with its old time is read again, never shown from the "
              "cache", (same.st_size, same.st_mtime_ns) == (st.st_size, st.st_mtime_ns) and after == fresh
              and after != before_swap, f"same as a full read {after == fresh}, changed {after != before_swap}")

        # ── 5. a corrupt cache, one in another shape and one from another version: each ignored, then replaced
        start(cache)
        listed()
        settle()
        good = json.loads(cache.read_text(encoding="utf-8"))
        key = str(books["Dara"])
        lie = {"kind": "annotated", "sheets": ["Nowhere"], "names": ["Nowhere"], "turns": {"Nowhere": []}}
        mark = list(routes.file_mark(books["Dara"]))
        foreign = dict(good, stamp=dict(good["stamp"], version="0.0.1"))
        foreign["tables"] = dict(good["tables"], books=[[key, mark, lie]])
        shapeless = dict(good, tables=dict(good["tables"], books=[[key, mark, dict(lie, turns="all of them")]],
                                           turns="none", heads=[[key, "a mark", ["x", 3]]]))
        truth_now = truth()
        results = {}
        for name, text in (("corrupt", '{"stamp": {"format": 1, "tab'), ("bytes", "\x00\xff garbage"),
                           ("another shape", json.dumps(shapeless)), ("another version", json.dumps(foreign)),
                           ("a list", "[1, 2, 3]")):
            cache.write_text(text, encoding="utf-8", errors="surrogateescape")
            got = restarted()
            try:
                rewritten = json.loads(cache.read_text(encoding="utf-8")).get("stamp") == good["stamp"]
            except ValueError:
                rewritten = False
            results[name] = (got == truth_now, "Nowhere" not in got, rewritten)
        check("396: a corrupt cache file, one in another shape and one from another version of the app are each "
              "ignored, the list answering as a full read does, and the next write replacing it",
              all(all(v) for v in results.values()), json.dumps(results))

        # ── 6. a run of one project, and a state file inside a project's folder, write no cache
        cache.unlink()
        start(None)
        listed()
        settle()
        none_for_root = not cache.exists()
        server_mod.STATE_PATH = root / "state.json"
        start(root / home_cache.NAME)
        listed()
        settle()
        check("396: a run of one project (--root) writes no cache, and nor does one whose state sits in a project's "
              "folder", none_for_root and not (root / home_cache.NAME).exists() and routes.HOME_CACHE["path"] is None,
              f"--root {none_for_root}, in the project {(root / home_cache.NAME).exists()}")
    finally:
        wb_mod.whole, Path.read_text = real_whole, real_text
        routes.home_cache_open(None)
        for t in tables:
            t.clear()
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
         routes.HOME_CACHE_AFTER) = kept
