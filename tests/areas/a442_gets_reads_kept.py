"""Area 442: what the GETs screen reads, and what a save writes, only when something changed (perfgets, 22 November
2026). Each participant's cards and quotes are kept against the marks of the files they come from (the workbook, the
themes file and the progress file, by modification time, size and inode), so an open and a poll with nothing changed
load no workbook, and a change to any one file is seen at the next poll: a save in the app, an agent's write, an
outside edit, a file put back by a copy coming in with its old time, and the progress file's placing of a sheet at a
later timepoint. A save that changes nothing leaves the progress file untouched, one that changes something writes it,
and a corrected passage hands the sheet it saved to the read of the copies' spans that follows, so the workbook is
loaded the once."""
from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

import openpyxl

from . import support
from .support import check, demo_copy
import idiograph_routes


def test_gets_reads_kept(scratch):
    print("\n442. GETs: each participant read against the marks of their files, and a save writing only what changed")
    import gets as gets_mod
    import rounds as rounds_mod
    import server as server_mod
    import themes as themes_mod
    import workbook as wb_mod

    root = scratch / "gets-kept"
    shutil.rmtree(root, ignore_errors=True)
    books = {name: demo_copy(root, name, f"{name} - EN & ES.xlsx") for name in ("Wren", "Ash", "Moss")}
    old = time.time() - 60
    for path in books.values():
        os.utime(path, (old, old))
    saved = (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_MEMORY = {"recent": []}
    any_book = str(books["Wren"])
    reads, loads = [], []
    real_read, real_load = themes_mod.read_cards, openpyxl.load_workbook

    def counted_read(workbook, *a, **k):
        reads.append(Path(workbook).parent.name)
        return real_read(workbook, *a, **k)

    def counted_load(*a, **k):
        loads.append(1)
        return real_load(*a, **k)

    def watching(fn):
        reads.clear()
        loads.clear()
        themes_mod.read_cards, openpyxl.load_workbook = counted_read, counted_load
        try:
            return fn()
        finally:
            themes_mod.read_cards, openpyxl.load_workbook = real_read, real_load

    def poll():
        return idiograph_routes.api_gets({"workbook": any_book})

    try:
        # ── A. nothing changed: no workbook is loaded, on the first open's repeat, after the first act and on every poll
        first = watching(poll)
        check("442: the first open reads each participant's workbook", sorted(set(reads)) == ["Ash", "Moss", "Wren"])
        again = watching(poll)
        check("442: an open again with nothing changed loads no workbook and reads no participant",
              not loads and not reads)
        check("442: and answers what the first answered", [c["case"] for c in again["cases"]] == [c["case"] for c in first["cases"]]
              and {c["case"]: c["lines"] for c in again["cases"]} == {c["case"]: c["lines"] for c in first["cases"]})
        body = dict(first["version"], cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in first["cards"]},
                    groups=first["groups"], discarded=[], picks={}, notes=[])
        watching(lambda: idiograph_routes.api_gets_save({"workbook": any_book, "version": body}))
        for _ in range(3):
            watching(poll)
            check("442: a poll after no change loads no workbook", not loads and not reads)

        # ── B. every kind of change is seen at the next poll, by the one participant it is of
        def seen_as_changed(who: str) -> bool:
            watching(poll)
            return reads == [who]

        # a save in the app
        sheet, row = None, None
        read = real_read(books["Wren"])
        card = read["cards"][0]
        sheet, row = card["sheet"], card["row"]
        changed = idiograph_routes.api_commit({"path": any_book, "sheet": sheet, "row": row,
                                               "es": card["text"] + " and the stair again", "en": None, "kq": None})
        check("442: a passage saved in the app is read again at the next poll, that participant alone",
              not changed.get("error") and seen_as_changed("Wren"))
        watching(poll)
        check("442: and, read once, is kept again", not reads and not loads)
        words = {c["case"]: c for c in watching(poll)["cases"]}["Wren"]["lines"]
        check("442: the poll shows the new words", any("and the stair again" in str(v.get("text")) for v in words.values()))

        # an agent's write of the participant's themes file
        data = themes_mod.load(books["Ash"]) or {}
        data.setdefault("boards", [])
        themes_mod.write(books["Ash"], dict(data, schema=2, case="Ash", workbook=books["Ash"].name,
                                            current="v1", boards=[themes_mod.blank_version(real_read(books["Ash"])["cards"])
                                                                  | {"id": "v1", "name": "Board 1"}]))
        check("442: a themes file written is read again at the next poll", seen_as_changed("Ash"))
        watching(poll)
        check("442: and kept again", not reads)

        # an outside edit of a workbook, as Excel saves one
        book = openpyxl.load_workbook(books["Moss"], rich_text=True)
        ws = book[card["sheet"]]
        cols = wb_mod.detect_columns(ws)
        ws.cell(card["row"], cols["es"]).value = "An outside edit, in Excel."
        book.save(books["Moss"])
        book.close()
        check("442: a workbook edited outside is read again at the next poll", seen_as_changed("Moss"))
        watching(poll)

        # a file put back by a copy coming in, the same words with their old time and size in a new file: the inode is the mark
        was = books["Ash"].stat()
        twin = root / "twin.xlsx"
        shutil.copy2(books["Ash"], twin)
        os.replace(twin, books["Ash"])
        put_back = books["Ash"].stat()
        check("442: a file put back keeps its old time and size and is a new file",
              put_back.st_mtime_ns == was.st_mtime_ns and put_back.st_size == was.st_size and put_back.st_ino != was.st_ino)
        check("442: a file put back is read again at the next poll", seen_as_changed("Ash"))
        watching(poll)

        # the progress file placing a sheet at a later timepoint
        progress = rounds_mod.load_progress(books["Wren"])
        progress["timepoints"] = {"No such sheet": 2}
        rounds_mod.save_progress(books["Wren"], progress)
        check("442: the progress file's change is read again at the next poll", seen_as_changed("Wren"))
        watching(poll)
        check("442: and the poll after that loads no workbook", not reads and not loads)

        # ── C. a save that changes nothing writes nothing, one that changes something writes
        progress_file = rounds_mod.progress_path(books["Wren"])
        rounds_mod.save_progress(books["Wren"], rounds_mod.load_progress(books["Wren"]))

        def stamp(path):
            st = path.stat()
            return st.st_mtime_ns, st.st_ino, st.st_size

        was = stamp(progress_file)
        time.sleep(0.02)
        rounds_mod.save_progress(books["Wren"], rounds_mod.load_progress(books["Wren"]))
        check("442: progress saved with the very words it holds is left untouched", stamp(progress_file) == was)
        text = card["text"] + " and the stair again"
        same = {"path": any_book, "sheet": sheet, "row": row, "es": text, "en": None, "kq": None}
        idiograph_routes.api_commit(same)
        was = stamp(progress_file)
        time.sleep(0.02)
        idiograph_routes.api_commit(same)
        check("442: a passage saved again with no change leaves the progress file untouched", stamp(progress_file) == was)
        other = next(c for c in real_read(books["Wren"])["cards"] if (c["sheet"], c["row"]) != (sheet, row))
        time.sleep(0.02)
        idiograph_routes.api_commit({"path": any_book, "sheet": other["sheet"], "row": other["row"],
                                     "es": other["text"], "en": None, "kq": None})
        check("442: a passage saved that changes what the file says, the last passage, writes it", stamp(progress_file) != was)
        was = stamp(progress_file)
        time.sleep(0.02)
        progress = rounds_mod.load_progress(books["Wren"])
        progress["flags"] = progress["flags"] + [{"sheet": sheet, "row": row, "note": "kept"}]
        rounds_mod.save_progress(books["Wren"], progress)
        check("442: a real change to the progress file writes it, and it reads back", stamp(progress_file) != was
              and rounds_mod.load_progress(books["Wren"])["flags"][-1]["note"] == "kept")
        check("442: a file that is not there is written", not progress_file.with_name("none.progress.json").exists()
              and (rounds_mod.save_progress(books["Ash"], {"version": 1}) or True)
              and rounds_mod.progress_path(books["Ash"]).exists())

        # ── D. a corrected passage loads the workbook the once: the sheet it saved is handed on
        cols = wb_mod.detect_columns(real_load(books["Wren"])[sheet])
        now = wb_mod.plain_text(real_load(books["Wren"], rich_text=True)[sheet].cell(row, cols["transcript"]).value)
        watching(lambda: idiograph_routes.api_edit_turn({"path": any_book, "sheet": sheet, "row": row, "text": now + " Said again."}))
        check("442: a passage corrected loads the workbook once", len(loads) == 1)
        handed = themes_mod.sheet_spreads(books["Wren"], sheet, [row, other["row"]], "mm:ss")
        held = dict(themes_mod.SHEET_HELD)
        none_loaded = watching(lambda: themes_mod.sheet_spreads(books["Wren"], sheet, [row, other["row"]], "mm:ss"))
        check("442: and the read that follows it takes the held sheet, loading none", not loads and none_loaded == handed)
        themes_mod.SHEET_HELD.clear()
        fresh = themes_mod.sheet_spreads(books["Wren"], sheet, [row, other["row"]], "mm:ss")
        check("442: the held sheet gives what a fresh read of the file gives", fresh == handed and held)
        check("442: a correction that changes nothing writes nothing, loading the workbook once",
              (lambda before: (watching(lambda: idiograph_routes.api_edit_turn(
                  {"path": any_book, "sheet": sheet, "row": row, "text": now + " Said again."})),
                  len(loads) == 1 and books["Wren"].stat().st_mtime_ns == before)[1])(books["Wren"].stat().st_mtime_ns))

        # ── E. the member's own boards file, and who owns the participant, are marked too (Working together)
        watching(poll)
        mine = root / "own-boards" / "Wren" / themes_mod.themes_path(books["Wren"]).name
        real_own = themes_mod.OWN_FILE
        themes_mod.OWN_FILE = lambda wb: mine if Path(wb).parent.name == "Wren" else None
        try:
            check("442: the owner changing, so his own boards file being read, is read again at the next poll",
                  seen_as_changed("Wren"))
            watching(poll)
            check("442: and kept again", not reads)
            blank = themes_mod.blank_version(real_read(books["Wren"])["cards"])
            themes_mod.write_path(mine, {"schema": 2, "current": "o1", "boards": [dict(blank, id="o1", name="Mine")]})
            check("442: his own boards file written is read again at the next poll", seen_as_changed("Wren"))
            watching(poll)
            check("442: and kept again after that", not reads)
        finally:
            themes_mod.OWN_FILE = real_own
        check("442: the owner changing back is read again at the next poll", seen_as_changed("Wren"))
        watching(poll)

        # ── F. the timepoint and the timecodes are part of what a case is kept under
        with themes_mod.scoped(2):
            watching(lambda: gets_mod.snapshot(books["Wren"]))
            check("442: a case read at another timepoint is read again", reads == ["Wren"])
            watching(lambda: gets_mod.snapshot(books["Wren"]))
            check("442: and kept at that timepoint", not reads)
        watching(lambda: gets_mod.snapshot(books["Wren"]))
        check("442: the first timepoint's is still kept", not reads)
        project_file = root / server_mod.PROJECT_FILE
        project_file.write_text('{"timecodes": "75:12"}', encoding="utf-8")
        times = lambda: {c["case"]: [v["time"] for v in c["lines"].values()] for c in poll()["cases"]}
        first_times = watching(times)
        project_file.write_text('{"timecodes": "01:15:12"}', encoding="utf-8")
        second_times = watching(times)
        check("442: a change of the project's timecodes is read again at the next poll, in the new timecodes",
              sorted(set(reads)) == ["Ash", "Moss", "Wren"] and second_times != first_times)
        project_file.unlink()

        # ── G. polls at once all answer, with room for one case only
        import threading
        failed, answers = [], []
        gets_mod.SNAPSHOTS_HELD = 1

        def hammer():
            try:
                for _ in range(6):
                    answers.append(len(poll()["cases"]))
            except Exception as exc:  # noqa: BLE001
                failed.append(repr(exc))

        crowd = [threading.Thread(target=hammer) for _ in range(6)]
        for th in crowd:
            th.start()
        for th in crowd:
            th.join()
        gets_mod.SNAPSHOTS_HELD = 256
        check("442: polls at once, with room for one case, all answer", not failed and len(answers) == 36
              and len(set(answers)) == 1, str(failed[:1]))

        # ── H. a sheet that cannot be handed on never fails the correction, and a formula reads as a file's does
        real_hold = themes_mod.hold_sheet

        def broken(*a, **k):
            raise RuntimeError("no")
        themes_mod.hold_sheet = broken
        try:
            out = idiograph_routes.api_edit_turn({"path": any_book, "sheet": sheet, "row": row, "text": now + " Said once more."})
        finally:
            themes_mod.hold_sheet = real_hold
        check("442: a seed that fails leaves the correction standing and answered", not out.get("error") and out["changed"]
              and wb_mod.plain_text(real_load(books["Wren"], rich_text=True)[sheet].cell(row, cols["transcript"]).value).endswith("Said once more."))
        sheet_mem = openpyxl.Workbook().active
        sheet_mem.append(["Speaker", "Time", "Transcript", "Statements"])
        sheet_mem.append(["A", "00:05", "words", "=1+1"])
        got = themes_mod.sheet_cells(sheet_mem, {"name": 1, "ts": 2, "transcript": 3, "es": 4}, saved=True)
        check("442: a formula cell in a sheet held from memory reads as nothing, as a file's value does", got[2][2][0] is None)
    finally:
        themes_mod.read_cards, openpyxl.load_workbook = real_read, real_load
        server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = saved
