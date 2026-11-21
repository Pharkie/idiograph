"""Area 400: a board's History out of its board file, in chunks beside it (historybuild, 16 November 2026, Adam's
rulings: chunks of about 256 KB per board in a folder beside the board file, existing projects moved over on first
open, no backwards compatibility).

What is checked, on the demo's three participants made a project, each board's History put inside its file as every
project held it before: the first open moves Juno's PETs file and the GETs file over, a copy of each in the _Archive
first, every revision kept (the census before and after the same, revision for revision), each board's version
unchanged, the board file holding no History and a head, and the chunks sealed at their size. A move left half done,
chunks written and the file still holding its History, is moved again from the file, the chunks it left swept once
old. A chunk evicted (iCloud's placeholder) or missing: History shows not here yet, a revision that needs it and a
restore are refused with nothing written, a drop's save still saves the board and makes no revision, and one evicted
by Optimize Mac Storage is fetched as it is read (historyfix). A stale chunk from a second Mac never reads as the
History, a crash between the chunks and the board file leaves every file the board file names whole, a rekey moves
every revision in one write or, with a chunk away, the board alone, a find and replace writes no chunk and a revision
restored takes today's words, a move that cannot be checked leaves the file as it was, and Working together carries the
chunks the heads name and nothing else, the receiver taking away only what its old file named. A board
deleted takes its chunks to the _Archive and a new board given its id has no History. Restore by id with a hash that
is not the revision's is refused, with the right one restored. An agent's change after the move is undone, the run
and the one change, every chunk and the board file back byte for byte. The poll never opens a chunk. And no module
but the adapter reads a board's `history` itself. Since historyfix2: a burst of revisions in one write across a
chunk's end writes every chunk it changes, readable after a restart; a superseded chunk is put aside, read from there
by a board file that still names it, brought back by the next write and taken away a week on with no copy; a fetch
waits once and never under a lock, a failed one remembered; the GETs' keys read with a chunk away and their revisions
following keys by words; a card marked changed in a revision keeps its words when restored."""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import shutil
from pathlib import Path

from .support import check
from . import support

ASKED = "Keep a revision of the board before I change it."


class _Stat:
    """A file's stat as `os.stat` gives it, with `st_flags` carrying the flag given."""

    def __init__(self, st, flags: int):
        self._st, self.st_flags = st, flags

    def __getattr__(self, name):
        return getattr(self._st, name)


class _FlaggedOs:
    """`os` as board_history sees it, one file's stat carrying a flag: Windows' Python has no `os.chflags` and its
    stats no `st_flags`, so there an evicted chunk is stood in for where board_history reads it (winfix2)."""

    def __init__(self, path: Path, flags: int):
        st = os.stat(path)
        # the file by its identity, so a short name (RUNNER~1) or another spelling of its path is the same file
        self._file, self._flags = (st.st_dev, st.st_ino), flags

    def __getattr__(self, name):
        return getattr(os, name)

    def stat(self, path, *args, **kwargs):
        st = os.stat(path, *args, **kwargs)
        return _Stat(st, self._flags) if st.st_ino and (st.st_dev, st.st_ino) == self._file else st


@contextlib.contextmanager
def evicted(bh, path: Path, flags: int):
    """A chunk marked as iCloud's Optimize Mac Storage marks one evicted, `flags` in its stat's `st_flags`, for as long
    as the block runs: by `os.chflags` where the system has it (the Mac), else by board_history's `os` stood in for."""
    if hasattr(os, "chflags"):
        os.chflags(path, flags)
        try:
            yield
        finally:
            os.chflags(path, 0)
        return
    real = bh.os
    bh.os = _FlaggedOs(path, flags)
    try:
        yield
    finally:
        bh.os = real


def digest(root: Path) -> dict:
    """Every file of the project by its contents, the lock files, the agents' store and the record set aside."""
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file() and not p.name.endswith(".lock")
            and ".idiograph-restore" not in p.parts and not p.name.startswith("idiograph-agent-changes")}


def boards_files(root: Path) -> dict:
    """The board files and the chunks of their History folders alone, by contents, the chunks put aside as
    superseded left out (they are no part of any History, see `board_history.SUPERSEDED`)."""
    return {k: v for k, v in digest(root).items() if (".history/" in k and "/superseded/" not in k)
            or k.endswith((".themes.json", "gets.json"))}


def test_history_chunks(scratch: Path):
    print("\n400. Board History out of the board files: the move on first open and its census, a half-done move "
          "redone, a chunk evicted or missing (nothing written), a board's id taken again after a delete, Restore by "
          "id checking its hash, an agent's change undone after the move, the poll, and the adapter "
          "(historybuild, 16 November)")
    import stat

    import agent_changes
    import agent_log
    import board_history as bh
    import cli
    import gets as gets_mod
    import history_census as hc
    import idiograph_routes as routes
    import server as server_mod
    import themes
    from workbook import WorkbookError

    base = scratch / "history-chunks-400"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Dogs at home"
    root.mkdir(parents=True)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Dogs at home", "research_question": support.DEMO_QUESTION,
        "agents": {"allowed": True, "at": "2026-11-16T09:00:00+00:00"}}), encoding="utf-8")
    shipped = support.DEMO_SHIPPED
    for book in sorted(shipped.glob("*.xlsx")):
        who = book.name.split(" - ")[0]
        (root / who / "Working").mkdir(parents=True)
        shutil.copy2(book, root / who / book.name)
        for side in sorted((shipped / "Working").glob(f"{book.stem}.*")):
            shutil.copy2(side, root / who / "Working" / side.name)
    shutil.copy2(shipped / "idiograph-gets.json", root / "idiograph-gets.json")
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Interviewer",
                                       "corpus": "", "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    log = base / "agent-log.json"
    kept = (agent_changes.ALL_OPS, os.environ.get(agent_log.PLACE), bh.CHUNK)
    agent_changes.ALL_OPS = None
    os.environ[agent_log.PLACE] = str(log)
    # small chunks, so a board's History runs to several here as it does at his scale
    bh.CHUNK = 6 * 1024

    def run(*args, tool="Claude Code"):
        given = ["--config", str(config_file), "--root", str(root), "--json", *args]
        if tool is not None:
            given += ["--tool", tool]
        code, out, err = cli.run(given)
        return code, (support.plain(json.loads(out)) if out.strip() else {}), err + (out if code else "")

    juno = root / "Juno" / "Juno - EN & ES.xlsx"
    tf = themes.themes_path(juno)
    folder = bh.folder_of(tf)
    gf = root / "idiograph-gets.json"
    try:
        # ── History inside the files, as before: Juno's PETs file given a second board and 12 revisions each, and
        # the GETs board 5
        data = json.loads(tf.read_text(encoding="utf-8"))
        first = data["boards"][0]
        second = json.loads(json.dumps(first))
        second.update(id="v2", name="Board 2", created="2026-11-02T10:00:00+00:00")
        data["boards"].append(second)
        for b in data["boards"]:
            b["history"] = []
            for r in range(12):
                st = themes.board_state(b)
                key = sorted(st["cards"])[r % len(st["cards"])]
                st["cards"] = dict(st["cards"], **{key: dict(st["cards"][key], x=r * 7)})
                b["history"].append({"id": f"r{r + 1}", "at": f"2026-11-0{1 + r % 9}T10:{r:02d}:00+00:00",
                                     "name": "kept" if r % 4 == 0 else "", "auto": r % 4 != 0, "state": st})
        tf.write_text(themes.render(data) + "\n", encoding="utf-8")
        gd = json.loads(gf.read_text(encoding="utf-8"))
        gd["boards"][0]["history"] = [{"id": f"r{r + 1}", "at": f"2026-11-0{1 + r}T09:00:00+00:00", "name": "",
                                       "auto": True, "state": themes.board_state(gd["boards"][0])} for r in range(5)]
        gf.write_text(themes.render(gd) + "\n", encoding="utf-8")
        census_before = hc.census(root)
        versions_before = {b["id"]: themes.board_version(b) for b in data["boards"]}

        # ── 1. the move on first open, and its census
        opened = themes.load(juno)
        on_file = json.loads(tf.read_text(encoding="utf-8"))
        chunks = sorted(p.name for p in folder.iterdir()) if folder.is_dir() else []
        archive = sorted(p.name for p in (root / "Juno" / "_Archive").iterdir())
        check("400: the first open moves Juno's PETs file over: no History inside it, each board a head, its chunks "
              "beside it, several a board at their size, and a copy of the file as it was in her _Archive",
              not bh.embedded(on_file) and all(bh.head_of(b) for b in on_file["boards"])
              and len(chunks) >= 4 and len({c.split(".")[0] for c in chunks}) == 2
              and all((folder / c).stat().st_size < bh.CHUNK + 4096 for c in chunks)
              and len(archive) == 1 and archive[0].startswith("Juno - EN & ES.themes (pre-history-move "),
              str(chunks) + str(archive))
        gets_mod.load(root)
        check("400: the GETs file is moved the same way on its first open, its chunks in idiograph-gets.history",
              not bh.embedded(json.loads(gf.read_text(encoding="utf-8")))
              and (root / "idiograph-gets.history").is_dir() and any((root / "_Archive").glob("idiograph-gets (pre-history-move *")),
              str(list((root / "_Archive").iterdir())))
        census_after = hc.census(root)
        check("400: the census before and after the move is the same, revision for revision, 29 in all",
              census_before["total"] == 29 and not hc.same(census_before, census_after), str(hc.same(census_before, census_after)))
        check("400: each board's version is unchanged by the move, and History lists all 12 of each board",
              {b["id"]: themes.board_version(b) for b in opened["boards"]} == versions_before
              and all(len(themes.history_list(b)) == 12 for b in themes.boards_of(themes.load(juno))),
              "")

        # ── 2. a move left half done is moved again from the file; the chunks it left, which no file names, stay
        # until they are ORPHAN_SECONDS old, then go to the _Archive
        tf.write_text((root / "Juno" / "_Archive" / archive[0]).read_text(encoding="utf-8"), encoding="utf-8")
        for f in folder.iterdir():
            shutil.rmtree(f) if f.is_dir() else f.unlink()
        bh.write_chunks(folder, "0123456789abcdef", data["boards"][0]["history"][:3], None)
        themes.load(juno)
        named_now = {n for b in json.loads(tf.read_text(encoding="utf-8"))["boards"] for n in bh.names_of(bh.head_of(b))}
        orphans = [p for p in folder.iterdir() if p.name.startswith("0123456789abcdef")]
        check("400: a half-done move (chunks written, the file still holding its History) is moved again from the "
              "file: the census the same, and the half-done move's chunks, which no head names, left as they are",
              not hc.same(census_before, hc.census(root)) and orphans and not any(p.name in named_now for p in orphans),
              str(len(orphans)))
        for p in orphans:
            os.utime(p, (1, 1))
        themes.board_op(juno, "revision", {"id": "v2", "name": "sweeps"}, "Juno")
        check("400: once older than ORPHAN_SECONDS a write sweeps them, a copy of each in the _Archive",
              not any(p.name.startswith("0123456789abcdef") for p in folder.iterdir())
              and any(p.name.startswith("Juno - EN & ES.themes history (unnamed ")
                      for p in (root / "Juno" / "_Archive").iterdir()), "")
        census_before = hc.census(root)

        # ── 3. a chunk evicted, then missing: nothing written that needs it, nothing lost
        board = themes.boards_of(themes.load(juno))[0]
        head = bh.head_of(board)
        uid = head["uid"]
        last = folder / bh.chunk_name(uid, *head["chunks"][-1])
        placeholder = last.with_name("." + last.name + ".icloud")
        last.rename(placeholder)
        held = boards_files(root)
        board = themes.boards_of(themes.load(juno))[0]
        try:
            themes.board_op(juno, "revision", {"id": "v1", "name": "now"}, "Juno")
            code = "written"
        except bh.HistoryAway as exc:
            code = exc.code
        check("400: its last chunk iCloud evicted: History shows not here yet, and Save a revision is refused as "
              "history_away with nothing written", themes.history_away(board) and themes.history_list(board) == []
              and code == "history_away" and boards_files(root) == held, code)
        page = {k: v for k, v in board.items() if k not in ("history", bh.HEAD)}
        page["v"] = themes.board_version(board)
        page["cards"] = {k: dict(c, x=c.get("x", 0) + 3) for k, c in page["cards"].items()}
        out = themes.save(juno, page, "Juno", revision="auto")
        after_save = boards_files(root)
        check("400: and a drop's save with the timer saves the board but makes no revision, the chunks untouched",
              out.get("saved") and "revision" not in out
              and all(after_save.get(k) == v for k, v in held.items() if ".history/" in k), json.dumps(out)[:200])
        placeholder.rename(last)
        first_chunk = folder / bh.chunk_name(uid, *bh.head_of(themes.boards_of(themes.load(juno))[0])["chunks"][0])
        first_bytes = first_chunk.read_bytes()
        first_chunk.rename(first_chunk.with_name("." + first_chunk.name + ".icloud"))
        added = themes.board_op(juno, "revision", {"id": "v1", "name": "on the end"}, "Juno")["revision"]
        check("400: an earlier chunk evicted: a revision still goes on the end, its last chunk alone read and written, "
              "the evicted one never touched", added["id"] == "r13" and not first_chunk.exists(), json.dumps(added))
        first_chunk.with_name("." + first_chunk.name + ".icloud").rename(first_chunk)
        check("400: and once it is back History lists every revision, the new one among them",
              len(themes.history_list(themes.boards_of(themes.load(juno))[0])) == 13
              and first_chunk.read_bytes() == first_bytes, "")
        first_chunk.unlink()
        held = boards_files(root)
        try:
            themes.board_op(juno, "restore", {"id": "v1", "revision": "r12"}, "Juno")
            code = "written"
        except bh.HistoryAway as exc:
            code = exc.code
        check("400: a chunk missing altogether: Restore is refused whole as history_away, nothing written",
              code == "history_away" and boards_files(root) == held, code)
        first_chunk.write_bytes(first_bytes)

        # ── 3b. an evicted chunk (SF_DATALESS) is read, which fetches it, and one that will not come refuses whole
        flags = (bh.SF_DATALESS, bh._fetch)
        fetched = []

        def fetch(path):
            fetched.append(path)
            return flags[1](path)
        bh.SF_DATALESS, bh._fetch = stat.UF_NODUMP, fetch
        gone_chunk = evicted(bh, first_chunk, stat.UF_NODUMP)
        gone_chunk.__enter__()
        try:
            bh._BYTES.clear()
            bh._MEMO.clear()
            listed = themes.history_list(themes.boards_of(themes.load(juno))[0])
            check("400: a chunk Optimize Mac Storage evicted is fetched as it is read, and History lists every revision",
                  len(listed) == 13 and fetched, str(len(fetched)))
            bh._BYTES.clear()
            bh._MEMO.clear()
            bh._fetch = lambda path: (_ for _ in ()).throw(bh.away())
            held = boards_files(root)
            try:
                themes.board_op(juno, "restore", {"id": "v1", "revision": "r2"}, "Juno")
                code = "written"
            except bh.HistoryAway as exc:
                code = exc.code
            check("400: one that does not come in time (no connection): Restore refused whole, nothing written",
                  code == "history_away" and boards_files(root) == held, code)
        finally:
            bh.SF_DATALESS, bh._fetch = flags
            gone_chunk.__exit__(None, None, None)
            bh._BYTES.clear()
            bh._MEMO.clear()

        # ── 3c. an older copy of a chunk (iCloud's last write from a second Mac) never reads as the History
        snap = bh.snapshot(tf)
        file_then = tf.read_bytes()
        themes.board_op(juno, "revision", {"id": "v1", "name": "on this Mac"}, "Juno")
        themes.board_op(juno, "revision", {"id": "v1", "name": "and again"}, "Juno")
        file_now, snap_now = tf.read_bytes(), bh.snapshot(tf)
        bh.put_back(snap)
        board = themes.boards_of(themes.load(juno))[0]
        try:
            themes.board_op(juno, "revision", {"id": "v1", "name": "stale"}, "Juno")
            code = "written"
        except bh.HistoryAway as exc:
            code = exc.code
        check("400: the board file of now with its chunks as they were before two revisions (a second Mac's stale "
              "copies): History is not here yet and a revision is refused, never written over the stale chunk",
              themes.history_away(board) and code == "history_away" and tf.read_bytes() == file_now, code)
        bh.put_back(snap_now)
        check("400: and once the chunks of now come, History lists all 15, nothing lost",
              len(themes.history_list(themes.boards_of(themes.load(juno))[0])) == 15 and file_then != file_now, "")

        # ── 3d. a crash part way: the chunks written, the board file not; the files it names are whole
        census_mid = hc.census(root)
        named_mid = boards_files(root)
        real_replace = themes.os.replace

        def crash(src, dst):
            if str(dst).endswith(".themes.json"):
                raise OSError("power cut")
            return real_replace(src, dst)
        themes.os.replace = crash
        try:
            themes.board_op(juno, "revision", {"id": "v1", "name": "lost to the crash"}, "Juno")
            code = "written"
        except OSError:
            code = "crashed"
        finally:
            themes.os.replace = real_replace
        with contextlib.suppress(OSError):
            tf.with_name(tf.name + ".tmp").unlink()
        left = {k: v for k, v in boards_files(root).items() if k in named_mid}
        check("400: a crash after the chunks are written and before the board file is: the board file and every "
              "chunk it names exactly as they were, the census the same",
              code == "crashed" and left == named_mid and not hc.same(census_mid, hc.census(root)), code)

        # ── 3e. a trim's rekey is all or nothing: every revision moves with the board in one write; with a chunk
        # away the board moves alone and its History is left whole for Restore to follow
        board = themes.boards_of(themes.load(juno))[0]
        key = sorted(board["cards"])[0]
        sheet, row, _line = themes.split_card_key(key)
        cut_row = themes.row_key(sheet, row)
        mapper = lambda k: None if k == cut_row else k  # noqa: E731
        before_chunks = {k for k in boards_files(root) if ".history/" in k}
        themes.rekey(juno, mapper, cut="t-test")
        board = themes.boards_of(themes.load(juno))[0]
        revs = themes.history_of(board)
        check("400: a rekey with every chunk here moves the board and every revision in one write",
              key not in board["cards"] and all(key not in r["state"]["cards"] for r in revs)
              and {k for k in boards_files(root) if ".history/" in k} != before_chunks, str(len(revs)))
        v2b = next(b for b in themes.boards_of(themes.load(juno)) if b["id"] == "v2")
        key2 = sorted(v2b["cards"])[1]
        sheet2, row2, _l = themes.split_card_key(key2)
        cut2 = themes.row_key(sheet2, row2)
        gone_chunk = folder / bh.chunk_name(bh.head_of(v2b)["uid"], *bh.head_of(v2b)["chunks"][0])
        gone_bytes = gone_chunk.read_bytes()
        gone_chunk.unlink()
        held_chunks = {k: v for k, v in boards_files(root).items() if ".history/" in k and bh.head_of(v2b)["uid"] in k}
        try:
            themes.rekey(juno, lambda k: None if k == cut2 else k, cut="t-test2")
            code = "moved"
        except Exception as exc:  # noqa: BLE001
            code = repr(exc)
        v2b = next(b for b in themes.boards_of(themes.load(juno)) if b["id"] == "v2")
        check("400: with one of a board's chunks missing the rekey still moves the board itself, never refused after "
              "the workbook moved, and its History's chunks are left exactly as they were",
              code == "moved" and key2 not in v2b["cards"]
              and {k: v for k, v in boards_files(root).items() if ".history/" in k and bh.head_of(v2b)["uid"] in k}
              == held_chunks, code)
        gone_chunk.write_bytes(gone_bytes)

        # ── 3f. lazy word-following: a find and replace writes no chunk, and a revision restored takes today's words
        board = themes.boards_of(themes.load(juno))[0]
        card_key = next(k for k in sorted(board["cards"]) if len(max(board["cards"][k]["text"].split(), key=len)) > 6)
        word = max(board["cards"][card_key]["text"].split(), key=len).strip(".,;:!?\"'")
        chunks_before = {k: v for k, v in boards_files(root).items() if ".history/" in k}
        server_kept = server_mod.ROOT_OVERRIDE
        server_mod.ROOT_OVERRIDE = str(root)
        try:
            replaced = routes.api_replace({"path": str(juno), "find": word, "replace": "Zebrafinch", "case": True})
        finally:
            server_mod.ROOT_OVERRIDE = server_kept
        chunks_after = {k: v for k, v in boards_files(root).items() if ".history/" in k}
        board = themes.boards_of(themes.load(juno))[0]
        old = next(r for r in themes.history_of(board) if card_key in r["state"]["cards"])
        check("400: a find and replace changes the board's card and writes no chunk, the revisions keeping the "
              "words they were kept with",
              "Zebrafinch" in board["cards"][card_key]["text"] and word in old["state"]["cards"][card_key]["text"]
              and chunks_after == chunks_before, json.dumps(replaced)[:200])
        done = themes.board_op(juno, "restore", {"id": "v1", "revision": old["id"]}, "Juno")
        board = themes.boards_of(themes.load(juno))[0]
        shown = themes.board_op(juno, "view", {"id": "v1", "revision": old["id"]}, "Juno")
        seen = next((c for c in shown.get("cards") or [] if c.get("key") == card_key), {})
        check("400: the revision restored takes the words of today, and shown, it shows them, no card marked changed",
              done.get("restored", {}).get("id") == old["id"] and "Zebrafinch" in board["cards"][card_key]["text"]
              and "Zebrafinch" in str(seen.get("text")) and not seen.get("changed"), json.dumps(seen)[:200])

        # ── 3g. a move that cannot be checked leaves the file as it was and its boards open
        moved_file = json.loads(tf.read_text(encoding="utf-8"))
        inside = support.board_file(tf)
        tf.write_text(themes.render(inside) + "\n", encoding="utf-8")
        raw = tf.read_bytes()
        real_read_head = bh.read_head

        def broken(folder_, head_):
            raise WorkbookError("the read back differs")
        bh.read_head = broken
        try:
            opened = themes.load(juno)
        finally:
            bh.read_head = real_read_head
        check("400: a move whose read back fails leaves the file byte for byte as it was, and the boards open with "
              "their History inside", tf.read_bytes() == raw and bh.embedded(opened)
              and len(themes.history_list(themes.boards_of(opened)[0])) == len(inside["boards"][0]["history"]),
              str(len(moved_file["boards"])))
        themes.load(juno)
        check("400: and the next open moves it", not bh.embedded(json.loads(tf.read_text(encoding="utf-8"))), "")

        # ── 3h. Working together: a version carries the chunks the heads name alone, waits while one is away, and
        # the receiving copy takes away only the chunks its old file named and the new one does not
        import team_sync
        named_all = bh.named_files(tf)
        stray = folder / bh.chunk_name("fedcba9876543210", 1, "0" * 12)
        stray.write_bytes(b"{}\n")
        listed = [rel for _p, rel in team_sync.participant_files(root / "Juno", juno, False)]
        check("400: a participant's version lists every chunk its boards name and no other",
              sum(1 for r in listed if ".history/" in r) == len(named_all) and not any(stray.name in r for r in listed),
              str(len(listed)))
        hidden = named_all[0].with_name("." + named_all[0].name + ".icloud")
        named_all[0].rename(hidden)
        try:
            team_sync.participant_files(root / "Juno", juno, False)
            code = "listed"
        except bh.HistoryAway as exc:
            code = exc.code
        hidden.rename(named_all[0])
        check("400: and with one of them not here, the version waits (history_away), never sent in part",
              code == "history_away", code)
        base_b = base / "receiver"
        shutil.copytree(root / "Juno", base_b / "Juno")
        rtf = base_b / "Juno" / "Working" / tf.name
        rfolder = bh.folder_of(rtf)
        themes.board_op(juno, "revision", {"id": "v1", "name": "sent on"}, "Juno")
        sent = {rel: p.read_bytes() for p, rel in team_sync.participant_files(root / "Juno", juno, False)}
        old_named = {p.name for p in bh.named_files(rtf)}
        team_sync.place(sent, base_b / "Juno")
        new_named = {p.name for p in bh.named_files(rtf)}
        check("400: the receiving copy takes the new chunks, takes away those its old file named alone, and keeps a "
              "chunk no file named",
              all((rfolder / n).exists() for n in new_named) and not any((rfolder / n).exists() for n in old_named - new_named)
              and (rfolder / stray.name).exists() and len(themes.history_list(themes.boards_of(
                  support.board_file(rtf))[0])) == len(themes.history_list(themes.boards_of(themes.load(juno))[0])), "")
        stray.unlink()
        shutil.rmtree(base_b, ignore_errors=True)

        # ── 3i. a burst of revisions in one write across a chunk's end: every chunk whose bytes changed written,
        # every revision readable after and after a restart (historyfix2, review 2, 1)
        data = themes.load(juno)
        board = themes.boards_of(data)[0]
        head0 = dict(bh.head_of(board))
        stale_file = tf.read_bytes()
        last0 = bh.chunk_name(head0["uid"], *head0["chunks"][-1])
        count0 = themes.revision_count(board)
        # chunks of about three revisions here, so the burst grows the last chunk before it begins the next ones
        small_chunk = bh.CHUNK
        bh.CHUNK = (folder / last0).stat().st_size * 3
        for i in range(8):
            st = themes.board_state(board)
            k = sorted(st["cards"])[i % len(st["cards"])]
            st["cards"] = dict(st["cards"], **{k: dict(st["cards"][k], x=1000 + i)})
            themes.add_revision(board, name=f"burst {i}", state=st)
        waiting = len(bh.pending(board))
        themes.write_path(tf, data)
        burst_file = tf.read_bytes()
        head1 = bh.head_of(themes.boards_of(themes.load(juno))[0])
        named1 = [bh.chunk_name(head1["uid"], n, h) for n, h in head1["chunks"]]
        check("400: eight revisions added in one write across a chunk's end: every chunk the head names written, "
              "History listing every one",
              waiting == 8 and len(head1["chunks"]) > len(head0["chunks"]) and last0 not in named1
              and all((folder / n).is_file() for n in named1)
              and len(themes.history_list(themes.boards_of(themes.load(juno))[0])) == count0 + 8,
              f"{waiting} {len(head0['chunks'])}->{len(head1['chunks'])}")
        bh._BYTES.clear()
        bh._MEMO.clear()
        revs = themes.history_of(themes.boards_of(themes.load(juno))[0])
        check("400: and after a restart (nothing kept in memory) every revision reads from its chunks, ids distinct",
              len(revs) == count0 + 8 and len({r["id"] for r in revs}) == len(revs)
              and [r["name"] for r in revs[-8:]] == [f"burst {i}" for i in range(8)], str(len(revs)))

        # ── 3j. a chunk a write supersedes is put aside, never taken away at once: a board file another Mac wrote
        # before it saw the write still reads whole, the next write brings it back, and a week on it goes, no copy
        aside = folder / bh.SUPERSEDED
        check("400: the chunk the burst grew is put aside in superseded/, out of the History folder's own chunks",
              not (folder / last0).exists() and (aside / last0).is_file(), last0)
        tf.write_bytes(stale_file)
        stale = themes.boards_of(themes.load(juno))[0]
        check("400: the board file of before the burst (a second Mac's, winning in iCloud) reads whole, its last chunk "
              "read from where it was put aside", not themes.history_away(stale)
              and len(themes.history_list(stale)) == count0, str(len(themes.history_list(stale))))
        page = {k: v for k, v in stale.items() if k not in ("history", bh.HEAD)}
        page["v"] = themes.board_version(stale)
        page["cards"] = {k: dict(c, x=c.get("x", 0) + 1) for k, c in page["cards"].items()}
        themes.save(juno, page, "Juno")
        check("400: and the next write brings it back beside the file it is named by",
              (folder / last0).is_file() and not (aside / last0).exists(), "")
        tf.write_bytes(burst_file)
        archived_before = sorted(p.name for p in (root / "Juno" / "_Archive").iterdir())
        for f in aside.iterdir():
            os.utime(f, (1, 1))
        old_aside = sorted(p.name for p in aside.iterdir())
        themes.board_op(juno, "revision", {"id": "v1", "name": "a week on"}, "Juno")
        check("400: once SUPERSEDED_SECONDS old the chunks put aside are taken away by a write, with no _Archive copy",
              old_aside and not any((aside / n).exists() or (folder / n).exists() for n in old_aside
                                    if n not in {p.name for p in bh.named_files(tf)})
              and sorted(p.name for p in (root / "Juno" / "_Archive").iterdir()) == archived_before,
              str(len(old_aside)))
        check("400: History lists every revision after", len(themes.history_list(
              themes.boards_of(themes.load(juno))[0])) == count0 + 9, "")
        # no send or copy carries a chunk put aside, and anything inside a History folder is History (review 3, M2)
        import project_pack
        from pathlib import PurePosixPath
        aside.mkdir(exist_ok=True)
        (aside / "0123456789abcdef.1.0123456789ab.jsonl").write_bytes(b"{}\n")
        aside_now = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()
                           and "/superseded/" in p.relative_to(root).as_posix())
        packed = [rel for _p, rel in project_pack.project_files(root)]
        gaside = ("idiograph-gets.history", "superseded", "0123456789abcdef.1.0123456789ab.jsonl")
        check("400: a project's files for any send or copy leave out every chunk put aside, a PETs one in a History "
              "folder classed as the PETs' and a GETs one as the GETs'",
              aside_now and not any("/superseded/" in r for r in packed)
              and any(".themes.history/" in r for r in packed)
              and project_pack.kind_in_case(PurePosixPath("Working/x.themes.history/superseded/" + gaside[2])) == "pets"
              and project_pack.gets_part(gaside) and project_pack.superseded_chunk(gaside)
              and project_pack.left_out(PurePosixPath("/".join(gaside))), str(len(aside_now)))
        # one the board file still names but found put aside (a second Mac's file, or one put back by hand, before
        # any read brought it back) goes at its place beside the file, the same bytes, and nothing in the project
        # moves (historyfix3, review 4 L-a)
        named_now = bh.named_files(tf)
        moved = named_now[0]
        os.replace(moved, aside / moved.name)
        live_rel = moved.relative_to(root).as_posix()
        packed = dict((rel, p) for p, rel in project_pack.project_files(root))
        check("400: a chunk its board file names, found put aside, goes in a send at its place beside the file and no "
              "other chunk put aside goes",
              live_rel in packed and packed[live_rel] == aside / moved.name and not moved.exists()
              and (aside / moved.name).is_file() and not any("/superseded/" in r for r in packed)
              and not any(r.endswith("0123456789abcdef.1.0123456789ab.jsonl") for r in packed), live_rel)
        os.replace(aside / moved.name, moved)
        # a folder of his own whose name ends .history is his, never the app's History (review 4 L-b)
        own = root / "Juno" / "Working" / "Oral.history"
        (own / "superseded").mkdir(parents=True)
        (own / "superseded" / "0123456789abcdef.1.0123456789ab.jsonl").write_bytes(b"{}\n")
        (root / "Oral.history").mkdir()
        (root / "Oral.history" / "notes.txt").write_text("his", encoding="utf-8")
        packed = [rel for _p, rel in project_pack.project_files(root)]
        check("400: a folder of his own ending .history goes in a send and is his notes, never the PETs' or the GETs' "
              "History, inside a participant's Working or at the root",
              "Juno/Working/Oral.history/superseded/0123456789abcdef.1.0123456789ab.jsonl" in packed
              and "Oral.history/notes.txt" in packed
              and project_pack.kind_in_case(PurePosixPath("Working/Oral.history/notes.txt")) == "notes"
              and not project_pack.in_history(("Oral.history", "notes.txt"))
              and project_pack.in_history(("Juno", "Working", "Juno - EN & ES.themes.history", "x.jsonl"))
              and project_pack.in_history(("idiograph-lgets.history", "superseded", "x.jsonl")), "")
        shutil.rmtree(own)
        shutil.rmtree(root / "Oral.history")
        bh.CHUNK = small_chunk

        # ── 3k. a fetch that does not come waits once, never again while it goes on, never under a lock, and one
        # that failed is remembered a while (review 2, 4)
        import locks
        import threading
        import time as time_mod
        probe = bh.named_files(tf)[0]
        key = str(probe)
        bh._BYTES.clear()
        bh._FETCHING[key] = {"data": None, "error": None, "done": threading.Event(),
                             "began": time_mod.monotonic() - bh.FETCH_SECONDS - 1, "ended": 0.0}
        flags = bh.SF_DATALESS
        bh.SF_DATALESS = stat.UF_NODUMP
        gone_probe = evicted(bh, probe, stat.UF_NODUMP)
        gone_probe.__enter__()
        try:
            began = time_mod.monotonic()
            try:
                bh.read_chunk(probe)
                code = "read"
            except bh.HistoryAway as exc:
                code = exc.code
            check("400: a read while a fetch past its time goes on is away at once, never a second wait",
                  code == "history_away" and time_mod.monotonic() - began < 2, code)
            bh._FETCHING[key]["began"] = time_mod.monotonic()
            began = time_mod.monotonic()
            with locks.held(probe.parent.parent / "probe.lock"):
                try:
                    bh.read_chunk(probe)
                    code = "read"
                except bh.HistoryAway as exc:
                    code = exc.code
            check("400: under a lock a read never waits for a fetch, however young",
                  code == "history_away" and time_mod.monotonic() - began < 2, code)
            calls = []
            real_fetch = bh._fetch
            bh._fetch = lambda path: calls.append(path) or real_fetch(path)
            try:
                b0 = themes.boards_of(themes.load(juno))[0]
                bh._MEMO.clear()
                away_now = themes.history_away(b0)
            finally:
                bh._fetch = real_fetch
            check("400: History's not-here-yet mark is a stat of each chunk, an evicted one away, with no fetch",
                  away_now and not calls, str(len(calls)))
            gone = threading.Event()
            gone.set()
            bh._FETCHING[key] = {"data": None, "error": OSError("offline"), "done": gone,
                                 "began": time_mod.monotonic(), "ended": time_mod.monotonic()}
            try:
                bh.read_chunk(probe)
                code = "read"
            except bh.HistoryAway as exc:
                code = exc.code
            check("400: a fetch that failed is remembered, a read soon after away at once", code == "history_away", code)
            bh._FETCHING[key]["ended"] = time_mod.monotonic() - bh.FAILED_SECONDS - 1
            check("400: and tried again once FAILED_SECONDS have passed, the chunk read",
                  bool(bh.read_chunk(probe)) and key not in bh._FETCHING, "")
        finally:
            bh.SF_DATALESS = flags
            gone_probe.__exit__(None, None, None)
            bh._FETCHING.pop(key, None)
            bh._BYTES.clear()
            bh._MEMO.clear()
            with contextlib.suppress(OSError):
                (probe.parent.parent / "probe.lock").unlink()

        # ── 3l. the GETs: a History not here never stops a follower, and their revisions follow keys by words when
        # restored or shown, as the PETs' do (review 2, 5)
        gdata = gets_mod.load(root)
        gboard = gets_mod.boards_of(gdata)[0]
        ghead = bh.head_of(gboard)
        gchunk = root / "idiograph-gets.history" / bh.chunk_name(ghead["uid"], *ghead["chunks"][0])
        gbytes = gchunk.read_bytes()
        gchunk.unlink()
        try:
            statements, _quotes = gets_mod.case_keys(gets_mod.load(root), "Juno")
            code = "listed"
        except bh.HistoryAway as exc:
            statements, code = set(), exc.code
        gchunk.write_bytes(gbytes)
        check("400: with a GETs chunk missing the keys a trim moves are still read, the board's and the copy's",
              code == "listed" and statements, code)
        lines = gdata["cases"]["Juno"]["lines"]
        sheet0 = themes.split_card_key(sorted(lines)[0])[0]
        on_sheet = sorted((i for i in lines if themes.split_card_key(i)[0] == sheet0), key=themes._order)
        i0, i1 = on_sheet[0], on_sheet[1]
        far = themes.card_key(sheet0, 999, 0)
        # the review's shifted case: a trim moved A from i1 to i0 and B from far to i1, the revision kept with the
        # keys before and its GET on A
        state = {"cards": {f"Juno/es/{i1}": {"x": 1, "y": 2, "text": lines[i0]["text"]},
                           f"Juno/es/{far}": {"x": 3, "y": 4, "text": lines[i1]["text"]}},
                 "groups": [{"id": "G1", "title": "t", "members": [f"Juno/es/{i1}"]}], "discarded": []}
        out = gets_mod.followed(state, gdata)
        check("400: a GETs revision whose keys shifted (one key now holding another statement) follows by words, as "
              "a PETs revision does: each card to its own line and its GET's members with it",
              out["cards"].get(f"Juno/es/{i0}", {}).get("text") == lines[i0]["text"]
              and out["cards"].get(f"Juno/es/{i1}", {}).get("text") == lines[i1]["text"]
              and out["groups"][0]["members"] == [f"Juno/es/{i0}"]
              and f"Juno/es/{i1}" in state["cards"], json.dumps(sorted(out["cards"])))
        state = {"cards": {f"Juno/es/{i0}": {"x": 0, "y": 0, "text": lines[i0]["text"]},
                           f"Juno/es/{far}": {"x": 1, "y": 1, "text": lines[i0]["text"]},
                           "Juno/es/" + themes.card_key(sheet0, 998, 0): {"x": 3, "y": 4, "text": "words no line has"}},
                 "groups": [], "discarded": []}
        out = gets_mod.followed(state, gdata)
        check("400: a card stays while its key holds its words, never onto a line another card holds, and one with "
              "no line of its words keeps its key",
              f"Juno/es/{far}" in out["cards"] and f"Juno/es/{i0}" in out["cards"]
              and "Juno/es/" + themes.card_key(sheet0, 998, 0) in out["cards"], json.dumps(sorted(out["cards"])))

        # ── 3l2. review 4's probe as the app makes it: a GETs board of PET cards with the table's quote ticked, a
        # revision kept, a trim while that board's History is away, then the revision shown and restored. The tick is
        # no part of a revision, so it lives on the board alone, which the trim moves whatever its History: shown and
        # restored, the table keeps the same quote at its new key (historyfix3)
        gbooks = routes.gets_books(root)

        def ticked() -> tuple:
            d = gets_mod.load(root)
            b = gets_mod.boards_of(d)[0]
            for cases in (b.get("rows") or {}).values():
                row = (cases or {}).get("Juno") or {}
                if row.get("quote"):
                    return row["quote"], (gets_mod.quote_at(d["cases"]["Juno"], row["quote"]) or {}).get("text")
            return None, None

        qkey, qwords = ticked()
        qsheet, qrow, qn = themes.split_card_key(qkey or "")
        gb = gets_mod.boards_of(gets_mod.load(root))[0]
        kept_rev = gets_mod.board_op(root, gbooks, "revision", {"id": str(gb["id"]), "name": "before the trim"})["revision"]
        ghead = bh.head_of(gets_mod.boards_of(gets_mod.load(root))[0])
        held_chunks = {c: c.read_bytes() for c in (root / "idiograph-gets.history" / bh.chunk_name(ghead["uid"], n, h)
                                                    for n, h in bh.named(ghead))}
        for c in held_chunks:
            c.unlink()
        bh._BYTES.clear()
        bh._MEMO.clear()

        def trim(rk: str):
            # the row before the ticked one cut, every later row of its sheet one up
            sheet, _, number = rk.rpartition(":")
            if sheet != qsheet or not number.isdigit() or int(number) < qrow - 1:
                return rk
            return None if int(number) == qrow - 1 else f"{sheet}:{int(number) - 1}"

        away_now = not bh.here(gets_mod.boards_of(gets_mod.load(root))[0])
        gets_mod.rows_moved(root, juno, trim)
        for c, kept_bytes in held_chunks.items():
            c.write_bytes(kept_bytes)
        bh._BYTES.clear()
        bh._MEMO.clear()
        moved_key, moved_words = ticked()
        viewed = gets_mod.board_op(root, gbooks, "view", {"id": str(gb["id"]), "revision": kept_rev["id"]})
        gets_mod.board_op(root, gbooks, "restore", {"id": str(gb["id"]), "revision": kept_rev["id"]})
        back_key, back_words = ticked()
        check("400: a GETs board of PET cards with its table's quote ticked, trimmed while its History is away, keeps "
              "the same quote at its new key, the revision shown has no tick of its own and restored leaves it there "
              "(review 4)",
              bool(qwords) and qrow > 1 and away_now and moved_key == themes.card_key(qsheet, qrow - 1, qn)
              and moved_words == qwords and "rows" not in viewed and back_key == moved_key and back_words == qwords,
              f"{qkey} -> {moved_key} -> {back_key}, away {away_now}")

        # ── 3m. a restored revision's card marked changed when it was kept keeps its words, so it comes back marked
        # changed; one that was not takes today's words (lazy word-following, review 2, 9)
        board = themes.boards_of(themes.load(juno))[0]
        k1, k2 = sorted(board["cards"])[:2]
        read = {"cards": [{"key": k1, "text": "today one"}, {"key": k2, "text": "today two"}], "quotes": {}}
        st = {"cards": {k1: {"x": 0, "y": 0, "text": "then one", "live": "then live"},
                        k2: {"x": 0, "y": 0, "text": "then two"}}, "groups": [], "discarded": []}
        up = themes.brought_up(json.loads(json.dumps(st)), read)
        check("400: a card marked changed in the revision keeps its words and its mark, the other takes today's",
              up["cards"][k1]["text"] == "then one" and up["cards"][k1].get("live") == "today one"
              and up["cards"][k2]["text"] == "today two", json.dumps(up["cards"]))
        census_before = hc.census(root)

        # ── 4. Restore by id checks the hash
        made = themes.board_op(juno, "revision", {"id": "v1", "name": "by hand"}, "Juno")["revision"]
        held = boards_files(root)
        try:
            themes.board_op(juno, "restore", {"id": "v1", "revision": made["id"], "hash": "0" * 16}, "Juno")
            said = ""
        except Exception as exc:  # noqa: BLE001
            said = str(exc)
        check("400: Restore by id with a hash that is not the revision's is refused, nothing written",
              said and boards_files(root) == held and len(made.get("hash") or "") == 16, said)
        done = themes.board_op(juno, "restore", {"id": "v1", "revision": made["id"], "hash": made["hash"]}, "Juno")
        check("400: with the revision's own hash it restores, a Before restoring revision kept first",
              done.get("restored", {}).get("id") == made["id"] and done["revision"]["id"] != made["id"], "")

        # ── 5. a board deleted takes its chunks to the _Archive, and its id taken again has no History
        v2 = next(b for b in themes.boards_of(themes.load(juno)) if b["id"] == "v2")
        uid2 = bh.head_of(v2)["uid"]
        themes.version_op(juno, "delete", {"id": "v2"}, "Juno")
        archived = [p for p in (root / "Juno" / "_Archive").glob("Juno - EN & ES.themes history (deleted board *)/*")
                    if p.name.startswith(uid2)]
        check("400: deleting Board 2 takes its chunks out of the folder, a copy of each in the _Archive",
              not any(p.name.startswith(uid2) for p in folder.iterdir()) and len(archived) >= 2, str(len(archived)))
        made = themes.version_op(juno, "new", {"name": "Board 2"}, "Juno")
        fresh = next(b for b in themes.boards_of(themes.load(juno)) if b["name"] == "Board 2")
        check("400: a new board given the deleted one's id, v2, has no History and no head",
              fresh["id"] == "v2" and bh.head_of(fresh) is None and themes.history_list(fresh) == [], fresh["id"])
        added = themes.board_op(juno, "revision", {"id": "v2", "name": "its own"}, "Juno")["revision"]
        check("400: and its first revision starts its own History under a new uid, r1",
              added["id"] == "r1" and bh.head_of(next(b for b in themes.boards_of(themes.load(juno))
                                                      if b["id"] == "v2"))["uid"] not in (uid, uid2), json.dumps(added))

        # ── 6. an agent's change after the move, undone: the run, then one change alone
        start = boards_files(root)
        code, out, err = run("board", "revision", "Juno", "Board 1", "--note", ASKED)
        lines = agent_changes.read(root)
        check("400: an agent's Save a revision after the move writes a chunk, is one line in the record naming "
              "Juno's boards, and its undo carries the revision's hash",
              code == 0 and boards_files(root) != start and len(lines) == 1
              and (lines[0].get("undo_with") or {}).get("hash") == (out.get("revision") or {}).get("hash"),
              err + json.dumps(lines)[:400])
        code, undone, err = run("agents", "undo-run", lines[0]["run"], "--note", "Put it back")
        check("400: the run's undo puts every chunk and the board file back byte for byte",
              code == 0 and boards_files(root) == start, err + json.dumps(undone)[:300])
        before_two = boards_files(root)
        code, out1, err1 = run("board", "revision", "Juno", "Board 1", "--note", ASKED)
        mid = boards_files(root)
        code2, out2, err2 = run("board", "revision", "Juno", "Board 2", "--note", ASKED)
        lines = agent_changes.read(root)
        first_change = lines[-2]["id"]
        code3, undone, err3 = run("agents", "undo-change", str(first_change), "--note", "Only the first")
        check("400: the first of two changes is refused alone while the later one changed the same files since, "
              "nothing written", code3 != 0 and boards_files(root) != before_two, err3[:300])
        code4, undone, err4 = run("agents", "undo-change", str(lines[-1]["id"]), "--note", "Only the second")
        check("400: the later change undone alone puts its chunks and the board file back as they were before it",
              code4 == 0 and boards_files(root) == mid, err4[:300] + json.dumps(undone)[:300])

        # ── 6b. an agent's turn write that only rewords (turnwrite, 21 November 2026): every line keeps its key, so no
        # revision is moved and no chunk is written but the one "kept first"; a restore then takes today's words, and
        # the run's undo takes the words back
        pbd = themes.boards_of(themes.load(juno))
        pcard = next((k for k in sorted(pbd[0]["cards"]) if themes.split_card_key(k)[2] >= 1), sorted(pbd[0]["cards"])[0])
        psheet, prow, pline = themes.split_card_key(pcard)
        code, shown, err = run("turn", "show", "Juno", psheet, str(prow), tool=None)
        turn_v = shown["turns"][0]["version"]
        pairs = [{"statement": t, "quote": "", "key": themes.card_key(psheet, prow, i)}
                 for i, t in enumerate(shown["turns"][0]["statements"])]
        was_text = pairs[pline]["statement"]
        pairs[pline] = dict(pairs[pline], statement=was_text + " in the quiet")
        spec_file = base / "turnwrite-400.json"
        spec_file.write_text(json.dumps({"pairs": pairs, "version": turn_v, "request": "Add three words"}),
                             encoding="utf-8")
        revisions_before = {b["id"]: [r["id"] for r in themes.history_of(b)] for b in pbd}
        chunk_files_before = {k: v for k, v in boards_files(root).items() if ".history/" in k}
        code, wrote, err = run("turn", "write", "Juno", psheet, str(prow), "--from", str(spec_file))
        chunk_files_after = {k: v for k, v in boards_files(root).items() if ".history/" in k}
        pafter = themes.boards_of(themes.load(juno))
        # only a board's last chunk may change, the kept-first revision going on its end; every earlier one is
        # byte for byte as it was
        part = lambda k: k.rsplit("/", 1)[1].split(".")
        last_of = {}
        for k in chunk_files_before:
            last_of[part(k)[0]] = max(last_of.get(part(k)[0], 0), int(part(k)[1]))
        changed_chunks = [k for k, v in chunk_files_before.items()
                          if chunk_files_after.get(k) != v and int(part(k)[1]) != last_of[part(k)[0]]]
        check("400: an agent's turn write that only rewords a line changes no chunk it had: every old revision is "
              "where it was, and a board gains the one kept-first revision at most",
              code == 0 and not changed_chunks
              and all([r["id"] for r in themes.history_of(b)][:len(revisions_before[b["id"]])]
                      == revisions_before[b["id"]]
                      and len(themes.history_of(b)) - len(revisions_before[b["id"]]) <= 1 for b in pafter)
              and all(b["cards"][pcard]["text"].endswith(" in the quiet") for b in pafter if pcard in b["cards"]),
              err + str(changed_chunks[:3]))
        board_a = pafter[0]
        old_rev = next(r for r in themes.history_of(board_a)[:len(revisions_before[board_a["id"]])]
                       if pcard in r["state"]["cards"])
        check("400: the revisions it left keep the words they were kept with",
              not old_rev["state"]["cards"][pcard]["text"].endswith(" in the quiet"), "")
        themes.board_op(juno, "restore", {"id": board_a["id"], "revision": old_rev["id"]}, "Juno")
        restored = next(b for b in themes.boards_of(themes.load(juno)) if b["id"] == board_a["id"])
        shown_rev = themes.board_op(juno, "view", {"id": board_a["id"], "revision": old_rev["id"]}, "Juno")
        seen = next((c for c in shown_rev.get("cards") or [] if c.get("key") == pcard), {})
        check("400: restoring or showing such a revision gives today's words on the line the agent reworded",
              restored["cards"][pcard]["text"].endswith(" in the quiet")
              and str(seen.get("text")).endswith(" in the quiet"), str(restored["cards"][pcard]["text"]))
        # a second reword, then its run's undo: the line reads as it did before that run, today's words again
        reworded_text = restored["cards"][pcard]["text"]
        code, shown, err = run("turn", "show", "Juno", psheet, str(prow), tool=None)
        pairs[pline] = dict(pairs[pline], statement=reworded_text + " again")
        spec_file.write_text(json.dumps({"pairs": pairs, "version": shown["turns"][0]["version"],
                                         "request": "Add one more word"}), encoding="utf-8")
        code, wrote, err = run("turn", "write", "Juno", psheet, str(prow), "--from", str(spec_file))
        second = next(b for b in themes.boards_of(themes.load(juno)) if b["id"] == board_a["id"])
        wrote_run = agent_changes.read(root)[-1]["id"]
        code2, undone, err2 = run("agents", "undo-change", str(wrote_run), "--note", "Put it back")
        board_undone = next(b for b in themes.boards_of(themes.load(juno)) if b["id"] == board_a["id"])
        check("400: a second reword's change, undone, takes the words back: the line reads as it did before it",
              code == 0 and second["cards"][pcard]["text"].endswith(" again") and code2 == 0
              and board_undone["cards"][pcard]["text"] == reworded_text, err + err2 + json.dumps(undone)[:200])
        # a write that moves a key (the passage's first two statements swapped) still moves the revisions with it
        code, shown, err = run("turn", "show", "Juno", psheet, str(prow), tool=None)
        now_pairs = [{"statement": t, "quote": "", "key": themes.card_key(psheet, prow, i)}
                     for i, t in enumerate(shown["turns"][0]["statements"])]
        if len(now_pairs) >= 2:
            spec_file.write_text(json.dumps({"pairs": [now_pairs[1], now_pairs[0]] + now_pairs[2:],
                                             "version": shown["turns"][0]["version"], "request": "Swap two"}),
                                 encoding="utf-8")
            chunk_files_before = {k: v for k, v in boards_files(root).items() if ".history/" in k}
            code, wrote, err = run("turn", "write", "Juno", psheet, str(prow), "--from", str(spec_file))
            chunk_files_after = {k: v for k, v in boards_files(root).items() if ".history/" in k}
            check("400: a turn write that moves a key still moves the revisions: chunks that held the card change",
                  code == 0 and any(chunk_files_after.get(k) != v for k, v in chunk_files_before.items()),
                  err + json.dumps(wrote)[:200])

        # ── 7. the poll never opens a chunk
        real = bh.read_chunk
        opened_chunks = []

        def counted(path):
            opened_chunks.append(path)
            return real(path)
        bh.read_chunk = counted
        server_kept = server_mod.ROOT_OVERRIDE
        try:
            server_mod.ROOT_OVERRIDE = str(root)
            stamp = routes.api_stamp({"workbook": str(juno)})
            stamp2 = routes.api_stamp({"workbook": str(juno)})
        finally:
            bh.read_chunk = real
            server_mod.ROOT_OVERRIDE = server_kept
        check("400: the 4-second poll reads the board file alone, never a chunk, and answers each board",
              not opened_chunks and len(stamp.get("boards") or []) == 2 and stamp2 == stamp, str(len(opened_chunks)))

        # ── 8. no module but the adapter reads a board's `history` itself
        src = Path(bh.__file__).parent
        allowed = {"board_history.py", "codes.py", "trajectories.py", "participants.py", "demographics.py",
                   "project_history.py"}
        own = {("themes.py", 'if isinstance(was.get("history"), list):'), ("themes.py", 'kept["history"] = was["history"]'),
               ("themes.py", 'board["history"] = history'),
               ("themes.py", 'if auto and head is not None and not isinstance(board.get("history"), list) \\')}
        found = []
        for f in sorted(src.glob("*.py")):
            if f.name in allowed:
                continue
            for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if re.search(r'\.get\("history"\)|\["history"\]', line) and (f.name, line.strip()) not in own:
                    found.append(f"{f.name}:{n}")
        check("400: no module but the adapter (board_history) reads or writes a board's history key itself",
              not found, str(found))
    finally:
        bh.CHUNK = kept[2]
        agent_changes.ALL_OPS = kept[0]
        if kept[1] is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = kept[1]
        agent_log.flush()
