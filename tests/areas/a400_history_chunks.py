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
        # revisions as they were kept before a revision held the GET table (getshistory): the board alone
        gd["boards"][0]["history"] = [{"id": f"r{r + 1}", "at": f"2026-11-0{1 + r}T09:00:00+00:00", "name": "",
                                       "auto": True, "state": themes.board_state(gd["boards"][0], table=False)}
                                      for r in range(5)]
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
        # past the sweep's gate, as a write ten minutes on is
        bh.reset()
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
            made = themes.board_op(juno, "revision", {"id": "v1", "name": "now"}, "Juno")["revision"]
            code = "written"
        except bh.HistoryAway as exc:
            made, code = None, exc.code
        board = themes.boards_of(themes.load(juno))[0]
        fresh = {k: v for k, v in boards_files(root).items() if k not in held and ".history/" in k}
        # a last chunk away (smallfix, 22 November 2026): a revision goes on the end in a chunk of its own after it,
        # the head still naming the one away, so History says not here yet while it is away and no chunk is touched
        check("400: its last chunk iCloud evicted: Save a revision still goes on the end, in a chunk of its own after it, "
              "every chunk there before byte for byte as it was, and History shows not here yet until the chunk is back",
              code == "written" and made["id"] == "r13" and len(fresh) == 1
              and all(boards_files(root).get(k) == v for k, v in held.items() if ".history/" in k)
              and themes.history_away(board) and themes.history_list(board) == []
              and bh.named(bh.head_of(board))[-2][0] == head["chunks"][-1][0] and not last.exists(), code)
        # the timer keeps the board as the file held it, so the first save after a revision keeps none (the state is the
        # last revision's) and the second keeps the state the first wrote
        outs = []
        for shift in (3, 6):
            board = themes.boards_of(themes.load(juno))[0]
            page = {k: v for k, v in board.items() if k not in ("history", bh.HEAD)}
            page["v"] = themes.board_version(board)
            page["cards"] = {k: dict(c, x=c.get("x", 0) + shift) for k, c in board["cards"].items()}
            outs.append(themes.save(juno, page, "Juno", revision="auto"))
        check("400: and a drop's save with the timer keeps its revision too, the board saved, the chunk away untouched",
              all(o.get("saved") for o in outs) and "revision" not in outs[0]
              and outs[1].get("revision", {}).get("id") == "r14" and not last.exists(), json.dumps(outs[1])[:200])
        # a board at its automatic revisions' cap prunes, which needs the whole History in memory: with the last chunk
        # away the timer's revision goes on the end all the same and nothing is pruned, where it took none (smallfix)
        at_cap = int(bh.head_of(themes.boards_of(themes.load(juno))[0]).get("autos") or 0) or 1
        was_keep, themes.AUTO_KEEP = themes.AUTO_KEEP, at_cap
        try:
            outs = []
            for shift in (9, 12):
                board = themes.boards_of(themes.load(juno))[0]
                page = {k: v for k, v in board.items() if k not in ("history", bh.HEAD)}
                page["v"] = themes.board_version(board)
                page["cards"] = {k: dict(c, x=c.get("x", 0) + shift) for k, c in board["cards"].items()}
                outs.append(themes.save(juno, page, "Juno", revision="auto"))
        finally:
            themes.AUTO_KEEP = was_keep
        check("400: a board at its cap of automatic revisions with its last chunk away still keeps the timer's revision, "
              "on the end, nothing pruned",
              all(o.get("saved") for o in outs) and [o.get("revision", {}).get("id") for o in outs] == ["r15", "r16"] and not last.exists(),
              json.dumps(outs[1])[:200])
        placeholder.rename(last)
        first_chunk = folder / bh.chunk_name(uid, *bh.head_of(themes.boards_of(themes.load(juno))[0])["chunks"][0])
        first_bytes = first_chunk.read_bytes()
        first_chunk.rename(first_chunk.with_name("." + first_chunk.name + ".icloud"))
        added = themes.board_op(juno, "revision", {"id": "v1", "name": "on the end"}, "Juno")["revision"]
        check("400: an earlier chunk evicted: a revision still goes on the end in a chunk of its own, "
              "the evicted one never touched", added["id"] == "r17" and not first_chunk.exists(), json.dumps(added))
        first_chunk.with_name("." + first_chunk.name + ".icloud").rename(first_chunk)
        check("400: and once it is back History lists every revision, the new one among them",
              len(themes.history_list(themes.boards_of(themes.load(juno))[0])) == 17
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
            bh.reset()
            listed = themes.history_list(themes.boards_of(themes.load(juno))[0])
            check("400: a chunk Optimize Mac Storage evicted is fetched as it is read, and History lists every revision",
                  len(listed) == 17 and fetched, str(len(fetched)))
            bh.reset()
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
            bh.reset()

        # ── 3c. an older copy of a chunk (iCloud's last write from a second Mac) never reads as the History
        snap = bh.snapshot(tf)
        file_then = tf.read_bytes()
        themes.board_op(juno, "revision", {"id": "v1", "name": "on this Mac"}, "Juno")
        themes.board_op(juno, "revision", {"id": "v1", "name": "and again"}, "Juno")
        file_now, snap_now = tf.read_bytes(), bh.snapshot(tf)
        bh.put_back(snap)
        board = themes.boards_of(themes.load(juno))[0]
        stale = {k: v for k, v in boards_files(root).items() if ".history/" in k}
        try:
            themes.board_op(juno, "revision", {"id": "v1", "name": "stale"}, "Juno")
            code = "written"
        except bh.HistoryAway as exc:
            code = exc.code
        # the chunks the board file names are not here, so History is not here yet; a revision goes on the end in a
        # chunk of its own after them and never over the stale chunks, which stay byte for byte as they were
        after = {k: v for k, v in boards_files(root).items() if ".history/" in k}
        check("400: the board file of now with its chunks as they were before two revisions (a second Mac's stale "
              "copies): History is not here yet, and a revision goes on the end in a chunk of its own, never written "
              "over the stale chunk",
              themes.history_away(board) and code == "written" and len(after) == len(stale) + 1
              and all(after.get(k) == v for k, v in stale.items()), code)
        # the chunks of now come (iCloud brings them beside the one this Mac wrote), and History lists all of it
        for name, data in snap_now["files"].items():
            if not (folder / name).exists():
                (folder / name).write_bytes(data)
        bh.reset()
        check("400: and once the chunks of now come, History lists all 20, the revision written meanwhile first, nothing lost",
              "stale" in [r["name"] for r in themes.history_list(themes.boards_of(themes.load(juno))[0])]
              and len(themes.history_list(themes.boards_of(themes.load(juno))[0])) == 20 and file_then != file_now, "")

        # past twice the cap with a chunk away the timer keeps none, however many saves (smallfix, review)
        first_autos = int(bh.head_of(themes.boards_of(themes.load(juno))[0]).get("autos") or 0)
        held_chunk = folder / bh.chunk_name(uid, *bh.head_of(themes.boards_of(themes.load(juno))[0])["chunks"][-1])
        away_chunk = held_chunk.with_name("." + held_chunk.name + ".icloud")
        held_chunk.rename(away_chunk)
        was_keep, themes.AUTO_KEEP = themes.AUTO_KEEP, max(1, first_autos)
        made_ids = []
        try:
            for i in range(200):
                board = themes.boards_of(themes.load(juno))[0]
                page = {k: v for k, v in board.items() if k not in ("history", bh.HEAD)}
                page["v"] = themes.board_version(board)
                page["cards"] = {k: dict(c, x=c.get("x", 0) + 20 + i) for k, c in board["cards"].items()}
                got = themes.save(juno, page, "Juno", revision="auto")
                if got.get("revision"):
                    made_ids.append(got["revision"]["id"])
            head_autos = int(bh.head_of(themes.boards_of(themes.load(juno))[0]).get("autos") or 0)
            by_hand = themes.board_op(juno, "revision", {"id": "v1", "name": "by hand past the bound"}, "Juno")["revision"]
        finally:
            themes.AUTO_KEEP = was_keep
            away_chunk.rename(held_chunk)
        check("400: 200 timer saves with a chunk away stop at twice the cap, and a revision asked for still goes on",
              0 < len(made_ids) <= max(1, first_autos) and head_autos <= 2 * max(1, first_autos) and by_hand["id"],
              f"{len(made_ids)} {first_autos} {head_autos}")
        # a head naming its chunks in no good shape is away as ever: the timer's revision is kept by none, the board saves
        board = themes.boards_of(themes.load(juno))[0]
        saved_chunks = bh.head_of(board)["chunks"]
        bh.head_of(board)["chunks"] = "damaged"
        try:
            bh.can_append(board)
            damaged = "appended"
        except bh.HistoryAway:
            damaged = "away"
        bh.head_of(board)["chunks"] = saved_chunks
        check("400: a head with its chunks misshapen is away for a revision, never appended to", damaged == "away", damaged)

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

        # ── 3i. a burst of revisions in one write: one chunk of their own, open, nothing else touched (perfhist); and
        # a burst past CHUNK folds, every chunk whose bytes changed written, every revision readable after and after
        # a restart (historyfix2, review 2, 1)
        data = themes.load(juno)
        board = themes.boards_of(data)[0]
        count0 = themes.revision_count(board)
        head_a = dict(bh.head_of(board))
        named_a = {bh.chunk_name(head_a["uid"], n, h): (folder / bh.chunk_name(head_a["uid"], n, h)).read_bytes()
                   for n, h in head_a["chunks"]}
        small_chunk = bh.CHUNK
        bh.CHUNK = 64 * 1024 * 1024

        def burst(b: dict, n: int, tag: str) -> int:
            for i in range(n):
                st = themes.board_state(b)
                k = sorted(st["cards"])[i % len(st["cards"])]
                st["cards"] = dict(st["cards"], **{k: dict(st["cards"][k], x=1000 + i)})
                themes.add_revision(b, name=f"{tag} {i}", state=st)
            return len(bh.pending(b))
        waiting = burst(board, 4, "open")
        themes.write_path(tf, data)
        head0 = dict(bh.head_of(themes.boards_of(themes.load(juno))[0]))
        named0 = [bh.chunk_name(head0["uid"], n, h) for n, h in head0["chunks"]]
        last0 = named0[-1]
        check("400: four revisions added in one write go into one chunk of their own, open, every chunk named before "
              "still named and byte for byte as it was, nothing put aside",
              waiting == 4 and named0[:-1] == list(named_a) and last0 not in named_a
              and all((folder / n).read_bytes() == v for n, v in named_a.items())
              and bh.open_of(head0) == bh.open_of(head_a) + 1 and len(bh.lines_in((folder / last0).read_bytes())) == 4
              and not any((folder / bh.SUPERSEDED / n).exists() for n in named_a),
              f"{len(named_a)}->{len(named0)} open {bh.open_of(head_a)}->{bh.open_of(head0)}")
        stale_file = tf.read_bytes()
        count_b = count0 + 4
        k0 = bh.open_of(head0)
        open_bytes = b"".join((folder / n).read_bytes() for n in named0[len(named0) - k0:])
        tail0 = named0[:len(named0) - k0]
        # a chunk takes no new line past one byte here, so the burst is past CHUNK and folds, the tail left as it is
        bh.CHUNK = 1
        data = themes.load(juno)
        board = themes.boards_of(data)[0]
        waiting = burst(board, 8, "burst")
        themes.write_path(tf, data)
        burst_file = tf.read_bytes()
        head1 = bh.head_of(themes.boards_of(themes.load(juno))[0])
        named1 = [bh.chunk_name(head1["uid"], n, h) for n, h in head1["chunks"]]
        after_tail = b"".join((folder / n).read_bytes() for n in named1[len(tail0):])
        bh.CHUNK = 64 * 1024 * 1024
        check("400: eight revisions added in one write past CHUNK fold the open chunks with them: every chunk the "
              "head names written, the folded lines byte for byte as they were, none open, History listing every one",
              waiting == 8 and named1[:len(tail0)] == tail0 and last0 not in named1 and bh.open_of(head1) == 0
              and after_tail.startswith(open_bytes) and len(bh.lines_in(after_tail)) == len(bh.lines_in(open_bytes)) + 8
              and all((folder / n).is_file() for n in named1)
              and len(themes.history_list(themes.boards_of(themes.load(juno))[0])) == count_b + 8,
              f"{waiting} {len(head0['chunks'])}->{len(head1['chunks'])} open {bh.open_of(head1)}")
        bh.reset()
        revs = themes.history_of(themes.boards_of(themes.load(juno))[0])
        check("400: and after a restart (nothing kept in memory) every revision reads from its chunks, ids distinct",
              len(revs) == count_b + 8 and len({r["id"] for r in revs}) == len(revs)
              and [r["name"] for r in revs[-12:]] == [f"open {i}" for i in range(4)] + [f"burst {i}" for i in range(8)],
              str(len(revs)))

        # ── 3j. a chunk a write supersedes is put aside, never taken away at once: a board file another Mac wrote
        # before it saw the write still reads whole, the next write brings it back, and a week on it goes, no copy
        aside = folder / bh.SUPERSEDED
        check("400: the open chunk the burst folded is put aside in superseded/, out of the History folder's own chunks",
              not (folder / last0).exists() and (aside / last0).is_file(), last0)
        tf.write_bytes(stale_file)
        stale = themes.boards_of(themes.load(juno))[0]
        check("400: the board file of before the burst (a second Mac's, winning in iCloud) reads whole, its last chunk "
              "read from where it was put aside", not themes.history_away(stale)
              and len(themes.history_list(stale)) == count_b, str(len(themes.history_list(stale))))
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
        # past the sweep's gate, as a write ten minutes on is
        bh.reset()
        themes.board_op(juno, "revision", {"id": "v1", "name": "a week on"}, "Juno")
        check("400: once SUPERSEDED_SECONDS old the chunks put aside are taken away by a write, with no _Archive copy",
              old_aside and not any((aside / n).exists() or (folder / n).exists() for n in old_aside
                                    if n not in {p.name for p in bh.named_files(tf)})
              and sorted(p.name for p in (root / "Juno" / "_Archive").iterdir()) == archived_before,
              str(len(old_aside)))
        check("400: History lists every revision after", len(themes.history_list(
              themes.boards_of(themes.load(juno))[0])) == count_b + 9, "")
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
            bh.reset()
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
        bh.reset()

        def trim(rk: str):
            # the row before the ticked one cut, every later row of its sheet one up
            sheet, _, number = rk.rpartition(":")
            if sheet != qsheet or not number.isdigit() or int(number) < qrow - 1:
                return rk
            return None if int(number) == qrow - 1 else f"{sheet}:{int(number) - 1}"

        away_now = not bh.here(gets_mod.boards_of(gets_mod.load(root))[0])
        gets_mod.rows_moved(root, juno, trim)
        for c, kept_bytes in held_chunks.items():
            # a History folder left empty goes with the write (`out_of`'s finish), so it is made again here
            c.parent.mkdir(parents=True, exist_ok=True)
            c.write_bytes(kept_bytes)
        bh.reset()
        moved_key, moved_words = ticked()
        viewed = gets_mod.board_op(root, gbooks, "view", {"id": str(gb["id"]), "revision": kept_rev["id"]})
        gets_mod.board_op(root, gbooks, "restore", {"id": str(gb["id"]), "revision": kept_rev["id"]})
        back_key, back_words = ticked()
        # since getshistory a revision holds its table, its ticked quote's words kept beside it, so shown and restored
        # the quote the trim moved while the revision could not follow is found by its words at its new key
        # the row ticked() reads, the first with a quote of hers, as the revision shows it
        seen_keys = {next((((c or {}).get("Juno") or {}).get("quote") for c in (viewed.get("rows") or {}).values()
                           if ((c or {}).get("Juno") or {}).get("quote")), None)}
        held_rev = next(r for r in themes.history_of(gets_mod.boards_of(gets_mod.load(root))[0]) if r["id"] == kept_rev["id"])
        old_kept = next((((c or {}).get("Juno") or {}).get("quote") for c in held_rev["state"]["rows"].values()
                         if ((c or {}).get("Juno") or {}).get("quote")), None) == qkey
        check("400: a GETs board of PET cards with its table's quote ticked, trimmed while its History is away, keeps "
              "the same quote at its new key, and the revision, whose table still names the old key, shows and "
              "restores the tick on that quote by its words (review 4, getshistory)",
              bool(qwords) and qrow > 1 and away_now and moved_key == themes.card_key(qsheet, qrow - 1, qn)
              and moved_words == qwords and old_kept and seen_keys == {moved_key} and back_key == moved_key
              and back_words == qwords, f"{qkey} -> {moved_key} -> {back_key}, shown {seen_keys}, away {away_now}")

        # ── 3l3. a GETs revision keeps its table (getshistory, 21 November 2026, Adam's yes by dialog): a revision
        # holds the table's rows and its ticked quotes' words beside them, History shows them, Restore puts the board
        # and its table back together and keeps both first, an agent's restore is undone byte for byte, a revision
        # from before holds none and restores as before, and a shared copy carries it
        def gboard() -> dict:
            return gets_mod.boards_of(gets_mod.load(root))[0]

        def table_of_board(b: dict) -> dict:
            return json.loads(json.dumps(gets_mod.rows_of(b)))

        gb = gboard()
        gid_board = str(gb["id"])
        rows_then = table_of_board(gb)
        ticked_rows = [(gid, case) for gid, cases in rows_then.items() for case, row in cases.items() if row.get("quote")]
        made_then = gets_mod.board_op(root, gbooks, "revision", {"id": gid_board, "name": "with its table"})["revision"]
        kept_then = next(r for r in themes.history_of(gboard()) if r["id"] == made_then["id"])
        marks_ok = all(str(kept_then.get(gets_mod.TABLE, {}).get(gid, {}).get(case)).partition(":")[0]
                       == gets_mod.quote_mark(gets_mod.quote_at(gets_mod.load(root)["cases"][case],
                                                                rows_then[gid][case]["quote"])["text"])
                       for gid, case in ticked_rows)
        check("400: a GETs revision holds the table's rows in its state and each ticked quote's words beside it, its "
              "hash the state's as before",
              bool(ticked_rows) and kept_then["state"].get("rows") == rows_then and marks_ok
              and made_then["hash"] == themes.state_hash(kept_then["state"])[:themes.HASH_SAID],
              f"{len(ticked_rows)} ticked, marks {marks_ok}")
        # the table changed on the page: one tick taken off and a note written, saved as the page saves
        changed = json.loads(json.dumps(gboard()))
        g0, c0 = ticked_rows[0]
        changed["rows"][g0][c0].pop("quote", None)
        changed["rows"][g0][c0].pop("bold", None)
        changed["rows"][g0][c0]["note"] = "A note written after the revision."
        for key in (bh.HEAD, "history"):
            changed.pop(key, None)
        gets_mod.save(root, gbooks, changed, revision="auto")
        count_then = len(themes.history_of(gboard()))
        # the timer's next save keeps the board as the file holds it, which differs from the last revision in its
        # table alone
        again = json.loads(json.dumps(gboard()))
        for key in (bh.HEAD, "history"):
            again.pop(key, None)
        gets_mod.save(root, gbooks, again, revision="auto")
        rows_now = table_of_board(gboard())
        held_now = themes.history_of(gboard())
        check("400: a change to the table alone is a change the timer keeps: its automatic revision holds the table "
              "with the tick taken off and the note",
              rows_now != rows_then and rows_now[g0][c0].get("note") and not rows_now[g0][c0].get("quote")
              and len(held_now) == count_then + 1 and held_now[-1].get("auto")
              and held_now[-1]["state"].get("rows") == rows_now, json.dumps(rows_now.get(g0, {}))[:200])
        viewed = gets_mod.board_op(root, gbooks, "view", {"id": gid_board, "revision": made_then["id"]})
        check("400: History shows the revision's own table, its tick and its notes, where the board's today differs",
              viewed.get("rows") == rows_then, json.dumps(viewed.get("rows"))[:200])
        done = gets_mod.board_op(root, gbooks, "restore", {"id": gid_board, "revision": made_then["id"]})
        after = gboard()
        before_kept = next(r for r in themes.history_of(after) if r["id"] == done["revision"]["id"])
        check("400: Restore puts back the board and its table together, and keeps the board and the table as they "
              "stood first, Before restoring",
              table_of_board(after) == rows_then and done["rows"] == rows_then
              and before_kept["state"].get("rows") == rows_now and before_kept.get("kind") == "before_restoring",
              json.dumps(table_of_board(after).get(g0, {}))[:200])
        gets_mod.board_op(root, gbooks, "restore", {"id": gid_board, "revision": before_kept["id"]})
        check("400: restoring Before restoring, the Undo of a Restore, puts back the table as it stood before it",
              table_of_board(gboard()) == rows_now, json.dumps(table_of_board(gboard()).get(g0, {}))[:200])
        # an agent's restore, then its run's undo: every file back byte for byte
        start_agent = boards_files(root)
        log_before = len(agent_changes.read(root))
        code, out, err = run("gets", "restore", gid_board, made_then["id"], "--note", ASKED)
        restored_rows = table_of_board(gboard())
        lines_now = agent_changes.read(root)
        code2, undone, err2 = run("agents", "undo-run", lines_now[-1]["run"], "--note", "Put it back")
        check("400: an agent's restore of a GETs revision puts its table back, and its run's undo puts the GETs file "
              "and every chunk back byte for byte",
              code == 0 and restored_rows == rows_then and len(lines_now) == log_before + 1 and code2 == 0
              and boards_files(root) == start_agent, err + err2)
        # a revision from before revisions held the table: shown, no table of its own; restored, the table as it stands
        old_rev = themes.history_of(gboard())[0]
        old_shown = gets_mod.board_op(root, gbooks, "view", {"id": gid_board, "revision": old_rev["id"]})
        old_done = gets_mod.board_op(root, gbooks, "restore", {"id": gid_board, "revision": old_rev["id"]})
        check("400: a revision from before holds no table: shown, it gives none, and restored, the table stays as it "
              "stands, nothing new said",
              "rows" not in old_rev["state"] and gets_mod.TABLE not in old_rev and "rows" not in old_shown
              and table_of_board(gboard()) == rows_now and set(old_done) == set(done), str(sorted(old_done)))
        # a shared copy: every file a send or a copy takes, placed in another folder, carries the revision's table
        import project_pack
        shared = base / "shared-copy" / root.name
        shutil.rmtree(shared.parent, ignore_errors=True)
        for p, rel in project_pack.project_files(root):
            (shared / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, shared / rel)
        bh._MEMO.clear()
        sdata = gets_mod.load(shared)
        sboard = gets_mod.boards_of(sdata)[0]
        srev = next((r for r in themes.history_of(sboard) if r["id"] == made_then["id"]), None)
        sshown = gets_mod.board_op(shared, routes.gets_books(shared), "view", {"id": gid_board, "revision": made_then["id"]})
        check("400: a shared copy carries the revision with its table and its quotes' words, and shows the same table",
              srev is not None and srev["state"].get("rows") == rows_then and srev.get(gets_mod.TABLE) == kept_then.get(gets_mod.TABLE)
              and sshown.get("rows") == rows_then, str(srev is not None))
        shutil.rmtree(shared.parent, ignore_errors=True)
        # the same follows on a quote reworded where it stands, and a quote gone: the tick stays, then goes, the note kept
        state_r = json.loads(json.dumps(kept_then))
        g1, c1 = ticked_rows[0]
        state_r[gets_mod.TABLE][g1][c1] = gets_mod.quote_mark("words no quote of theirs has")
        state_r["state"]["rows"][g1][c1]["bold"] = [[0, 4]]
        state_r["state"]["rows"][g1]["Nobody"] = {"quote": "", "note": "a participant the file no longer holds"}
        stays = gets_mod.table_followed(state_r, gets_mod.load(root))
        # review-getshistory L1: the quote's row kept its statements' words and its old words are another quote of
        # hers now: a find and replace reworded this one in place, so the tick does not move there
        cur = gets_mod.load(root)
        qk1 = rows_then[g1][c1]["quote"]
        other = next(q for line in cur["cases"][c1]["lines"].values() for q in gets_mod.line_quotes(line)
                     if q["key"] != qk1 and gets_mod.quote_mark(q["text"]) != gets_mod.quote_mark(
                         gets_mod.quote_at(cur["cases"][c1], qk1)["text"]))
        state_l1 = json.loads(json.dumps(kept_then))
        state_l1[gets_mod.TABLE][g1][c1] = gets_mod.quote_mark(other["text"]) + ":" + gets_mod.row_mark(cur["cases"][c1], qk1)
        in_place = gets_mod.table_followed(state_l1, cur)
        # and with its row's statements another row's now (the keys moved), the same words are followed there
        state_l1[gets_mod.TABLE][g1][c1] = gets_mod.quote_mark(other["text"]) + ":" + gets_mod.quote_mark("another row")
        followed_on = gets_mod.table_followed(state_l1, cur)
        check("400: a tick whose quote was reworded where it stands stays though its old words are another quote of "
              "hers, and goes to that quote when its row's statements show the keys moved, its bold measured on the "
              "old words dropped when it stays, and a row of a participant the file no longer holds left out",
              in_place[g1][c1].get("quote") == qk1 and followed_on[g1][c1].get("quote") == other["key"]
              and "bold" not in stays[g1][c1] and "Nobody" not in stays[g1], json.dumps(stays[g1])[:200])
        # review-getshistory M: the timer keeps no automatic revision that differs from the last, kept before
        # revisions held the table, only by the table now being held, on the end of the History or with it attached
        fast_board = gboard()
        old_style = {"id": "r900", "at": themes.now_iso(), "name": "", "auto": True,
                     "state": themes.board_state(fast_board, table=False)}
        bh.append(fast_board, old_style)
        none_fast = themes.auto_revision(fast_board)
        slow_board = gboard()
        slow_board["history"] = themes.history_of(slow_board) + [dict(old_style)]
        none_slow = themes.auto_revision(slow_board)
        moved_card = sorted(slow_board["cards"])[0]
        slow_board["cards"][moved_card]["x"] = float(slow_board["cards"][moved_card].get("x") or 0) + 50
        made_slow = themes.auto_revision(slow_board)
        check("400: after a revision from before, a timer save of the same board keeps no new line, and one that moved "
              "a card keeps one holding the table",
              none_fast is None and none_slow is None and made_slow is not None
              and made_slow["state"].get("rows") == rows_now,
              f"{none_fast} {none_slow} {made_slow and made_slow['id']}")
        state_r["state"]["rows"][g1][c1]["quote"] = themes.card_key("Initial", 9999, 0)
        state_r["state"]["rows"][g1][c1]["note"] = "kept"
        goes = gets_mod.table_followed(state_r, gets_mod.load(root))
        check("400: a ticked quote reworded where it stands keeps its tick, and one whose key holds no quote loses its "
              "tick and keeps its note",
              stays[g1][c1].get("quote") == rows_then[g1][c1]["quote"]
              and "quote" not in goes[g1][c1] and goes[g1][c1].get("note") == "kept", json.dumps(goes[g1][c1]))

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

        # ── 3n. a card whose own key still names a line stays on that line with today's words, and only a card whose
        # key holds no line follows its words to another row (followfix, 21 November 2026)
        def fline(key, text):
            s, r, n = themes.split_card_key(key)
            return {"key": key, "sheet": s, "row": r, "line": n, "text": text}

        def fstate(**held):
            return {"cards": {kk: {"x": 0, "y": 0, "text": tt} for kk, tt in held.items()}, "groups": [],
                    "discarded": []}

        ka, kb, kz = (themes.card_key("S", 5, 0), themes.card_key("S", 5, 1), themes.card_key("S", 9, 0))
        up1 = themes.brought_up(fstate(**{ka: "Feeling alone"}),
                                {"cards": [fline(ka, "Feeling lonely"), fline(kz, "Feeling alone")], "quotes": {}})
        check("400: a revision's card whose line was reworded stays on it with the new words when another row reads "
              "its old words and holds no card",
              list(up1["cards"]) == [ka] and up1["cards"][ka]["text"] == "Feeling lonely", json.dumps(up1["cards"]))
        kc = themes.card_key("S", 5, 2)
        up2 = themes.brought_up(fstate(**{ka: "Alpha one", kb: "Beta two", kc: "Gamma three"}),
                                {"cards": [fline(ka, "Beta two"), fline(kb, "Gamma three")], "quotes": {}})
        check("400: a line deleted from a cell leaves the cards after it following their words and the deleted "
              "line's card is the one missing, none left showing another card's words",
              up2["cards"][ka]["text"] == "Beta two" and up2["cards"][kb]["text"] == "Gamma three"
              and "Alpha one" in [c["text"] for c in up2["cards"].values()] and len(up2["cards"]) == 3,
              json.dumps(up2["cards"]))
        r5, r6, r7 = (themes.card_key("S", n, 0) for n in (5, 6, 7))
        up2b = themes.brought_up(fstate(**{r5: "Alpha one", r6: "Beta two", r7: "Gamma three"}),
                                 {"cards": [fline(r5, "Beta two"), fline(r6, "Gamma three")], "quotes": {}})
        check("400: a row trimmed away leaves the cards of the rows after it following their words to the rows "
              "that moved up",
              up2b["cards"][r5]["text"] == "Beta two" and up2b["cards"][r6]["text"] == "Gamma three"
              and "Alpha one" in [c["text"] for c in up2b["cards"].values()] and len(up2b["cards"]) == 3,
              json.dumps(up2b["cards"]))
        up3 = themes.brought_up(fstate(**{themes.card_key("S", 5, 3): "Feeling alone"}),
                                {"cards": [fline(ka, "Something new"), fline(kz, "Feeling alone")], "quotes": {}})
        check("400: a card whose line went follows its words to another row",
              list(up3["cards"]) == [kz], json.dumps(up3["cards"]))

        # the notes for older revisions are replayed only into a revision numbered at or below the write, and a copy
        # sent to someone leaves them behind with the History (histfollow, 21 November 2026)
        import project_pack
        held_log = {themes.REWORDS: [{"n": 3, "key": ka, "was": "Alpha one", "now": "x"}]}
        replayed = themes.rewords_replayed(fstate(**{ka: "Alpha one", kb: "Beta two"}), held_log, 2)
        later = themes.rewords_replayed(fstate(**{ka: "Alpha one", kb: "Beta two"}), held_log, 4)
        check("400: the notes of a reword change a card's words only in a revision older than the write",
              replayed["cards"][ka]["text"] == "x" and later["cards"][ka]["text"] == "Alpha one",
              json.dumps(replayed["cards"]))
        sent, _board, _n = project_pack.current_board_only({"boards": [dict(id="v1", name="B", cards={}, **held_log)]})
        check("400: Share a copy leaves a board's notes for its revisions behind with its History",
              themes.REWORDS not in sent["boards"][0], json.dumps(sent)[:200])

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
        # the record's lines before it, the GETs restore and its undo of 3l3 among them
        earlier = len(agent_changes.read(root))
        code, out, err = run("board", "revision", "Juno", "Board 1", "--note", ASKED)
        lines = agent_changes.read(root)[earlier:]
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

        # ── 6c. a keyed reword that hands a line another's old words, and a write that appends lines at a passage's end
        # (histfollow, 21 November 2026): every key stays, so no revision is moved and no chunk but each board's last
        # is written, and a revision shown or restored follows the keys first
        code, shown, err = run("turn", "show", "Juno", psheet, str(prow), tool=None)
        base_pairs = [{"statement": t, "quote": "", "key": themes.card_key(psheet, prow, i)}
                      for i, t in enumerate(shown["turns"][0]["statements"])]
        if len(base_pairs) >= 2:
            k0, k1 = themes.card_key(psheet, prow, 0), themes.card_key(psheet, prow, 1)
            board_b = themes.boards_of(themes.load(juno))[0]
            anchor = themes.board_op(juno, "revision", {"id": board_b["id"], "name": "before shape two"},
                                     "Juno")["revision"]
            texts_then = {k: c["text"] for k, c in next(r for r in themes.history_of(
                next(b for b in themes.boards_of(themes.load(juno)) if b["id"] == board_b["id"]))
                if r["id"] == anchor["id"])["state"]["cards"].items()}
            first_words = base_pairs[0]["statement"]
            two = [dict(base_pairs[0], statement="A brand new opening line"),
                   dict(base_pairs[1], statement=first_words)] + base_pairs[2:]
            spec_file.write_text(json.dumps({"pairs": two, "version": shown["turns"][0]["version"],
                                             "request": "Reword two lines"}), encoding="utf-8")
            chunk_files_before = {k: v for k, v in boards_files(root).items() if ".history/" in k}
            code, wrote, err = run("turn", "write", "Juno", psheet, str(prow), "--from", str(spec_file))
            chunk_files_after = {k: v for k, v in boards_files(root).items() if ".history/" in k}
            last_of = {}
            for k in chunk_files_before:
                last_of[part(k)[0]] = max(last_of.get(part(k)[0], 0), int(part(k)[1]))
            changed_chunks = [k for k, v in chunk_files_before.items()
                              if chunk_files_after.get(k) != v and int(part(k)[1]) != last_of[part(k)[0]]]
            check("400: a keyed reword that gives a line another's old words writes no chunk but each board's last",
                  code == 0 and not changed_chunks, err + str(changed_chunks[:3]))
            now_board = next(b for b in themes.boards_of(themes.load(juno)) if b["id"] == board_b["id"])
            check("400: and the board notes what changed for its older revisions, no revision of its own moved",
                  any(e.get("key") == k0 for e in now_board.get(themes.REWORDS) or []), str(now_board.get("rewords")))
            seen_rev = themes.board_op(juno, "view", {"id": board_b["id"], "revision": anchor["id"]}, "Juno")
            seen_cards = {c.get("key"): c for c in seen_rev.get("cards") or []}
            check("400: the revision shown follows the keys: the first line reads its new words, the second the first's "
                  "old words, and no card is missing",
                  themes.words(seen_cards[k0]["text"]) == themes.words("A brand new opening line")
                  and themes.words(seen_cards[k1]["text"]) == themes.words(first_words)
                  and not seen_cards[k0].get("missing") and not seen_cards[k1].get("missing"),
                  json.dumps({k: (c.get("text"), c.get("missing")) for k, c in seen_cards.items() if k in (k0, k1)}))
            themes.board_op(juno, "restore", {"id": board_b["id"], "revision": anchor["id"]}, "Juno")
            back = next(b for b in themes.boards_of(themes.load(juno)) if b["id"] == board_b["id"])
            check("400: the revision restored has both cards at their keys with today's words, none moved away",
                  themes.words(back["cards"][k0]["text"]) == themes.words("A brand new opening line")
                  and themes.words(back["cards"][k1]["text"]) == themes.words(first_words)
                  and set(texts_then) <= set(back["cards"]), str(sorted(back["cards"])[:4]))

            # an append: every old line keeps its key and place, a line follows them
            code, shown, err = run("turn", "show", "Juno", psheet, str(prow), tool=None)
            cur = [{"statement": t, "quote": "", "key": themes.card_key(psheet, prow, i)}
                   for i, t in enumerate(shown["turns"][0]["statements"])]
            board_c = themes.boards_of(themes.load(juno))[0]
            anchor2 = themes.board_op(juno, "revision", {"id": board_c["id"], "name": "before an append"},
                                      "Juno")["revision"]
            spec_file.write_text(json.dumps({"pairs": cur + [{"statement": "A line added at the very end", "quote": ""}],
                                             "version": shown["turns"][0]["version"], "request": "Add a line"}),
                                 encoding="utf-8")
            chunk_files_before = {k: v for k, v in boards_files(root).items() if ".history/" in k}
            code, wrote, err = run("turn", "write", "Juno", psheet, str(prow), "--from", str(spec_file))
            chunk_files_after = {k: v for k, v in boards_files(root).items() if ".history/" in k}
            last_of = {}
            for k in chunk_files_before:
                last_of[part(k)[0]] = max(last_of.get(part(k)[0], 0), int(part(k)[1]))
            changed_chunks = [k for k, v in chunk_files_before.items()
                              if chunk_files_after.get(k) != v and int(part(k)[1]) != last_of[part(k)[0]]]
            check("400: a turn write that appends lines at a passage's end changes no chunk but each board's last",
                  code == 0 and not changed_chunks, err + str(changed_chunks[:3]) + json.dumps(wrote)[:200])
            after_board = next(b for b in themes.boards_of(themes.load(juno)) if b["id"] == board_c["id"])
            restored_before = {k: c["text"] for k, c in after_board["cards"].items()}
            themes.board_op(juno, "restore", {"id": board_c["id"], "revision": anchor2["id"]}, "Juno")
            back2 = next(b for b in themes.boards_of(themes.load(juno)) if b["id"] == board_c["id"])
            check("400: the revision from before the append restores with every card where it was",
                  {k: c["text"] for k, c in back2["cards"].items() if k in restored_before} == restored_before,
                  str(len(back2["cards"])))

        # ── 3o. open chunks and the fold (perfhist, 22 November 2026): a write's revisions go into a chunk of their
        # own and nothing written is touched; FOLD of them fold at the next write, onto the tail when it is here and
        # they fit, else after it; one that cannot be read now never refuses a revision
        import project_pack
        import team_sync
        kept_fold = (bh.FOLD, bh.CHUNK, themes.AUTO_KEEP)
        bh.FOLD, bh.CHUNK = 4, 64 * 1024 * 1024
        bh.reset()
        aside = folder / bh.SUPERSEDED

        def file_head(bid: str = "v2") -> dict:
            return bh.head_of(next(b for b in json.loads(tf.read_text(encoding="utf-8"))["boards"] if b["id"] == bid))

        def names(head: dict) -> list[str]:
            return [bh.chunk_name(head["uid"], n, h) for n, h in head["chunks"]]

        def set_open(value, bid: str = "v2") -> None:
            raw = json.loads(tf.read_text(encoding="utf-8"))
            for b in raw["boards"]:
                if b["id"] == bid:
                    if value is Ellipsis:
                        b[bh.HEAD].pop(bh.OPEN, None)
                    else:
                        b[bh.HEAD][bh.OPEN] = value
            tf.write_text(themes.render(raw) + "\n", encoding="utf-8", newline="\n")

        def keep(name: str, bid: str = "v2") -> dict:
            return themes.board_op(juno, "revision", {"id": bid, "name": name}, "Juno")

        def listed(bid: str = "v2") -> list:
            return themes.history_list(next(b for b in themes.boards_of(themes.load(juno)) if b["id"] == bid))

        def aside_names() -> set:
            return {p.name for p in aside.iterdir()} if aside.is_dir() else set()

        def chunk_set() -> set:
            return {p.name for p in folder.iterdir() if p.is_file()}

        def lines_of(ns: list[str]) -> bytes:
            return b"".join((folder / n).read_bytes() for n in ns)

        try:
            # a head from before, with no `open`, and a plain append
            set_open(Ellipsis)
            before = file_head()
            bytes_before = {n: (folder / n).read_bytes() for n in names(before)}
            aside_before = aside_names()
            count_v2 = len(listed())
            keep("open 1")
            h1 = file_head()
            check("400: a head from before (no open) takes a revision as one chunk of its own: every chunk it named "
                  "byte for byte as it was and still named, nothing put aside, one open",
                  names(h1)[:-1] == names(before) and bh.open_of(h1) == 1
                  and all((folder / n).read_bytes() == v for n, v in bytes_before.items())
                  and aside_names() == aside_before and len(listed()) == count_v2 + 1,
                  f"{len(names(before))}->{len(names(h1))} open {h1.get(bh.OPEN)}")
            bh.reset()
            check("400: and after a restart History lists every revision, the new one among them",
                  len(listed()) == count_v2 + 1, str(len(listed())))

            # the FOLD-th: the tail small, so one chunk under the tail's number
            for i in range(3):
                keep(f"open {i + 2}")
            h4 = file_head()
            k, n4 = bh.open_of(h4), names(h4)
            tail_bytes, open_bytes = (folder / n4[-k - 1]).read_bytes(), lines_of(n4[-k:])
            census_a = bh.census(tf)["boards"]
            keep("folds")
            h5 = file_head()
            n5 = names(h5)
            new_tail = (folder / n5[-1]).read_bytes()
            census_b = bh.census(tf)["boards"]
            check("400: at FOLD open chunks the next write folds: the tail, the open chunks and its revision in one chunk "
                  "under the tail's number, every line byte for byte, none open, the folded chunks put aside",
                  k == 4 and bh.open_of(h5) == 0 and n5[:-1] == n4[:-k - 1]
                  and h5["chunks"][-1][0] == h4["chunks"][-k - 1][0] and new_tail.startswith(tail_bytes + open_bytes)
                  and len(bh.lines_in(new_tail)) == len(bh.lines_in(tail_bytes + open_bytes)) + 1
                  and all((aside / n).is_file() and not (folder / n).exists() for n in n4[-k - 1:]),
                  f"open {k} -> {bh.open_of(h5)}, {len(n4)} -> {len(n5)}")
            check("400: and the census is the same, revision for revision, with the new one on the end",
                  census_b["v2"][:-1] == census_a["v2"] and census_b["v1"] == census_a["v1"]
                  and len(census_b["v2"]) == count_v2 + 5, "")

            # the tail full: the fold goes after it, the tail as it is
            tail_name = n5[-1]
            bh.CHUNK = (folder / tail_name).stat().st_size
            for i in range(4):
                keep(f"fill {i}")
            h6 = file_head()
            k, n6 = bh.open_of(h6), names(h6)
            open_bytes = lines_of(n6[-k:])
            keep("folds after")
            h7 = file_head()
            n7 = names(h7)
            bh.CHUNK = 64 * 1024 * 1024
            check("400: with the tail full the fold makes chunks of its own after it, the tail named and as it was",
                  k == 4 and bh.open_of(h7) == 0 and n7[:len(n6) - k] == n6[:len(n6) - k] and n6[-k - 1] == tail_name
                  and (folder / tail_name).read_bytes() == new_tail
                  and h7["chunks"][len(n6) - k][0] == h6["chunks"][-k - 1][0] + 1
                  and lines_of(n7[len(n6) - k:]).startswith(open_bytes), f"{len(n6)} -> {len(n7)}")

            # the tail evicted: the fold goes after it, never waiting for it; an open chunk evicted: one more open chunk
            for i in range(4):
                keep(f"evict {i}")
            h8 = file_head()
            k, n8 = bh.open_of(h8), names(h8)
            tail8 = folder / n8[-k - 1]
            tbytes = tail8.read_bytes()
            flags = (bh.SF_DATALESS, bh._fetch)
            bh.SF_DATALESS = stat.UF_NODUMP
            bh._fetch = lambda path: (_ for _ in ()).throw(bh.away())
            gone = evicted(bh, tail8, stat.UF_NODUMP)
            gone.__enter__()
            try:
                keep("tail evicted")
            finally:
                gone.__exit__(None, None, None)
                bh.SF_DATALESS, bh._fetch = flags
            h9 = file_head()
            n9 = names(h9)
            check("400: a fold with the tail evicted folds without it: the open chunks and the revision after the tail, "
                  "the tail untouched, none open",
                  k == 4 and bh.open_of(h9) == 0 and n9[:len(n8) - k] == n8[:len(n8) - k] and tail8.read_bytes() == tbytes
                  and h9["chunks"][len(n8) - k][0] == h8["chunks"][-k - 1][0] + 1, f"{len(n8)} -> {len(n9)}")
            for i in range(4):
                keep(f"open away {i}")
            h10 = file_head()
            far = folder / names(h10)[-1]
            bh.reset()
            bh.SF_DATALESS = stat.UF_NODUMP
            bh._fetch = lambda path: (_ for _ in ()).throw(bh.away())
            gone = evicted(bh, far, stat.UF_NODUMP)
            gone.__enter__()
            try:
                keep("an open one evicted")
            finally:
                gone.__exit__(None, None, None)
                bh.SF_DATALESS, bh._fetch = flags
            h11 = file_head()
            check("400: a fold with an open chunk evicted writes one more open chunk instead, nothing refused, nothing "
                  "put aside", bh.open_of(h11) == 5 and names(h11)[:-1] == names(h10), str(h11.get(bh.OPEN)))
            keep("back")
            h12 = file_head()
            check("400: and the next write, the chunk back, folds", bh.open_of(h12) == 0
                  and len(listed()) == count_v2 + 21, f"{h12.get(bh.OPEN)} {len(listed())}")

            # `open` in any other shape reads whole and appends
            shapes = []
            for value in (-3, "2", True, 999, None, [1]):
                set_open(value)
                was = len(listed())
                keep(f"shape {value!r}")
                bh.reset()
                h = file_head()
                shapes.append(len(listed()) == was + 1 and 0 <= bh.open_of(h) <= len(h["chunks"])
                              and isinstance(h.get(bh.OPEN), int))
            check("400: a head whose open is negative, a string, True, past its chunks, null or a list reads whole and "
                  "takes a revision", all(shapes), str(shapes))

            # a whole-History write (a prune past AUTO_KEEP) keeps the open chunks open by the rule
            keep("before the prune")
            keep("and again")
            base_h = file_head()
            kb = bh.open_of(base_h)
            tail_n = base_h["chunks"][-kb - 1][0] if kb < len(base_h["chunks"]) else 0
            board = next(b for b in themes.boards_of(themes.load(juno)) if b["id"] == "v2")
            themes.AUTO_KEEP = int(base_h.get("autos") or 0)
            page = {k: v for k, v in board.items() if k not in ("history", bh.HEAD)}
            page["v"] = themes.board_version(board)
            page["cards"] = {k: dict(c, x=c.get("x", 0) + 11) for k, c in page["cards"].items()}
            themes.save(juno, page, "Juno")
            board = next(b for b in themes.boards_of(themes.load(juno)) if b["id"] == "v2")
            page = {k: v for k, v in board.items() if k not in ("history", bh.HEAD)}
            page["v"] = themes.board_version(board)
            page["cards"] = {k: dict(c, x=c.get("x", 0) + 1) for k, c in page["cards"].items()}
            out = themes.save(juno, page, "Juno", revision="auto")
            ph = file_head()
            trailing = 0
            for n, _h in reversed(ph["chunks"]):
                if n <= tail_n:
                    break
                trailing += 1
            themes.AUTO_KEEP = kept_fold[2]
            check("400: a prune past AUTO_KEEP writes the whole History and keeps open the chunks past the last folded "
                  "one, the oldest automatic revision gone",
                  out.get("revision") and kb >= 1 and bh.open_of(ph) == trailing and trailing >= 1
                  and int(ph.get("autos") or 0) == int(base_h.get("autos") or 0), f"{kb} {ph.get(bh.OPEN)} {trailing}")
            spare = base / "spare.history"
            uid = "fedcba9876543210"
            far_head = {"uid": uid, "count": 1, "next": 2, "chunks": [[1, "0" * 12]], bh.OPEN: 1}
            got = bh.write_chunks(spare, uid, [{"id": "r1", "at": "", "name": "", "auto": False, "state": {}}], far_head)
            check("400: a whole-History write from memory whose base will not read starts with none open",
                  got.get(bh.OPEN) == 0 and len(got["chunks"]) == 1, str(got.get(bh.OPEN)))
            shutil.rmtree(spare, ignore_errors=True)

            # crashes: after a plain append's chunk and before the board file; and inside a fold, before the file
            named_mid = boards_files(root)
            files_mid = chunk_set()
            real_replace = themes.os.replace

            def crash(src, dst):
                if str(dst).endswith(".themes.json"):
                    raise OSError("power cut")
                return real_replace(src, dst)
            themes.os.replace = crash
            try:
                keep("lost to the crash")
                code = "written"
            except OSError:
                code = "crashed"
            finally:
                themes.os.replace = real_replace
            with contextlib.suppress(OSError):
                tf.with_name(tf.name + ".tmp").unlink()
            orphan = sorted(chunk_set() - files_mid)
            check("400: a crash between a plain append's chunk and the board file: the board file and every chunk it "
                  "names as they were, the new chunk named by none",
                  code == "crashed" and {k: v for k, v in boards_files(root).items() if k in named_mid} == named_mid
                  and len(orphan) == 1 and len(listed()) == len(bh.census(tf)["boards"]["v2"]), code)
            for n in orphan:
                os.utime(folder / n, (1, 1))
            unnamed_before = len([p for p in (root / "Juno" / "_Archive").iterdir() if " history (unnamed " in p.name])
            bh.reset()
            keep("after the crash")
            check("400: and a week on the write past the sweep's gate takes it away, a copy in the _Archive",
                  not any((folder / n).exists() for n in orphan)
                  and len([p for p in (root / "Juno" / "_Archive").iterdir() if " history (unnamed " in p.name])
                  == unnamed_before + 1, "")
            set_open(bh.FOLD)
            named_mid = boards_files(root)
            files_mid = chunk_set()

            def refuse(_out):
                raise WorkbookError("checked out")
            token = bh.CHECK.set(refuse)
            try:
                keep("fold that stops")
                code = "written"
            except WorkbookError:
                code = "stopped"
            finally:
                bh.CHECK.reset(token)
            check("400: a fold that stops before the board file takes away every chunk it wrote: the board file and "
                  "its chunks as they were, nothing new in the folder",
                  code == "stopped" and boards_files(root) == named_mid and chunk_set() == files_mid, code)

            # History's list from the light cache: only a new chunk parsed, no state kept, the same list
            bh.reset()
            full = listed()
            keep("light")
            new_name = names(file_head())[-1]
            bh._MEMO.clear()
            bh._LIGHT.pop(str(folder / new_name), None)
            real_parse = bh.parse
            parsed = []

            def counting(data):
                parsed.append(len(data))
                return real_parse(data)
            bh.parse = counting
            try:
                again = listed()
            finally:
                bh.parse = real_parse
            board = next(b for b in themes.boards_of(themes.load(juno)) if b["id"] == "v2")
            fresh = [themes.revision_summary(r, hashed=False) for r in reversed(themes.history_from(bh.revisions(board)))]
            check("400: after a revision History's list parses its new chunk alone, every other chunk's revisions kept "
                  "without their states, and the list is the one the chunks give read afresh",
                  len(parsed) == 1 and len(again) == len(full) + 1 and again == fresh
                  and all(r.get("state", bh.UNREAD) is bh.UNREAD for _key, held in bh._LIGHT.values() for r in held),
                  f"{len(parsed)} parsed, {len(again)} vs {len(fresh)}")
            calls = []
            for f in sorted(Path(bh.__file__).parent.glob("*.py")) + sorted(Path(server_mod.__file__).parent.glob("*.py")):
                for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                    if re.search(r"\bmemo\(", line) and "def memo(" not in line:
                        calls.append((f.name, line.strip()))
            check("400: memo, whose revisions carry no state, is called by History's list and here's count alone",
                  sorted(c[0] for c in calls) == ["board_history.py", "themes.py"]
                  and any("board_history.memo(board, \"list\"" in c[1] for c in calls)
                  and any("memo(board, \"count\", len)" in c[1] for c in calls), str(calls))

            # the sweep's gate
            aside.mkdir(exist_ok=True)
            old_aside = aside / "0123456789abcdef.9.0123456789ab.jsonl"
            old_aside.write_bytes(b"{}\n")
            os.utime(old_aside, (1, 1))
            keep("within the gate")
            within = old_aside.exists()
            bh._SWEPT.clear()
            keep("past the gate")
            check("400: a chunk put aside more than a week ago stays through writes within the sweep's gate and goes "
                  "at the first past it", within and not old_aside.exists(), str(within))

            # an agent's run that folds, undone whole, and the fold undone as one change
            set_open(bh.FOLD)
            start = boards_files(root)
            code, out, err = run("board", "revision", "Juno", "Board 2", "--note", ASKED, tool="Codex")
            folded_now = bh.open_of(file_head()) == 0
            lines = agent_changes.read(root)
            code2, undone, err2 = run("agents", "undo-run", lines[-1]["run"], "--note", "Put it back", tool="Codex")
            check("400: an agent's revision that folds, its run undone: every chunk and the board file back byte for byte",
                  code == 0 and folded_now and code2 == 0 and boards_files(root) == start,
                  err + err2 + json.dumps(undone)[:300])
            set_open(bh.FOLD)
            mid = boards_files(root)
            code, out, err = run("board", "revision", "Juno", "Board 2", "--note", ASKED, tool="Cursor")
            folded_now = bh.open_of(file_head()) == 0
            lines = agent_changes.read(root)
            code2, undone, err2 = run("agents", "undo-change", str(lines[-1]["id"]), "--note", "Only this", tool="Cursor")
            check("400: and the fold undone as one change: its chunks and the board file back as they were before it",
                  code == 0 and folded_now and code2 == 0 and boards_files(root) == mid,
                  err + err2 + json.dumps(undone)[:300])

            # the review's fixes (perfhist2)
            # a board at AUTO_KEEP: every timer revision writes the whole History, and `open` stays bounded
            set_open(0)
            bh.reset()
            board = next(b for b in themes.boards_of(themes.load(juno)) if b["id"] == "v2")
            one = len(bh.line_of(bh.revisions(board)[-1])) + 1
            # a chunk full with one revision, so every chunk a prune writes is full, and room for 3 * FOLD of them
            bh.CHUNK = max(1, one // 2)
            themes.AUTO_KEEP = int(file_head().get("autos") or 0) + 3 * bh.FOLD
            opens, kept_count = [], len(listed()) + 3 * bh.FOLD
            for i in range(200):
                data = themes.load(juno)
                board = next(b for b in themes.boards_of(data) if b["id"] == "v2")
                st = themes.board_state(board)
                k = sorted(st["cards"])[i % len(st["cards"])]
                st["cards"] = dict(st["cards"], **{k: dict(st["cards"][k], x=5000 + i)})
                themes.add_revision(board, auto=True, state=st)
                themes.write_path(tf, data)
                opens.append(bh.open_of(file_head()))
            th = file_head()
            themes.AUTO_KEEP = kept_fold[2]
            bh.CHUNK = 64 * 1024 * 1024
            bh.reset()
            check("400: 200 timer revisions on a board at AUTO_KEEP, each writing the whole History, keep open at most "
                  "FOLD, no full chunk counted open, History whole and its count kept",
                  max(opens) <= bh.FOLD and len(listed()) == kept_count and int(th.get("count") or 0) == kept_count
                  and len(th["chunks"]) > 3 * bh.FOLD, f"open max {max(opens)}, {len(th['chunks'])} chunks")

            # an open chunk lost for good: the writes retry the fold to 2 * FOLD, then fold past it, files bounded
            set_open(0)
            keep("before the loss")
            keep("and one after it")
            lost = folder / names(file_head())[-2]
            lost_bytes = lost.read_bytes()
            lost.unlink()
            bh.reset()
            sizes, named_counts = [], []
            for i in range(6 * bh.FOLD):
                keep(f"after the loss {i}")
                h = file_head()
                sizes.append(bh.open_of(h))
                named_counts.append(len(h["chunks"]))
            h = file_head()
            lost.write_bytes(lost_bytes)
            bh.reset()
            check("400: with an open chunk lost for good the writes go on, open never past 2 * FOLD and the files named "
                  "bounded, the lost chunk left where it is, and once it is back History reads whole",
                  max(sizes) <= 2 * bh.FOLD and 0 in sizes[2 * bh.FOLD:] and lost.name in names(h)
                  and max(named_counts) - min(named_counts) <= 2 * bh.FOLD + 1
                  and len(listed()) == int(h.get("count") or 0), f"{sizes} {named_counts}")

            # a fold's count is against what the chunks hold, parsed: a line parse reads as none is away
            set_open(0)
            keep("odd line")
            raw = json.loads(tf.read_text(encoding="utf-8"))
            vb = next(b for b in raw["boards"] if b["id"] == "v2")
            n_last, h_last = vb[bh.HEAD]["chunks"][-1]
            odd = (folder / bh.chunk_name(vb[bh.HEAD]["uid"], n_last, h_last)).read_bytes() + "\u00a0\n".encode("utf-8")
            odd_name = bh.chunk_name(vb[bh.HEAD]["uid"], n_last, bh.digest(odd))
            (folder / odd_name).write_bytes(odd)
            vb[bh.HEAD]["chunks"][-1] = [n_last, bh.digest(odd)]
            vb[bh.HEAD][bh.OPEN] = bh.FOLD
            tf.write_text(themes.render(raw) + "\n", encoding="utf-8", newline="\n")
            bh.reset()
            held_odd = boards_files(root)
            files_odd = chunk_set()
            try:
                keep("fold the odd line")
                code = "written"
            except WorkbookError as exc:
                code = getattr(exc, "code", "refused")
            check("400: a fold whose lines are not the revisions its chunks hold, parsed, is refused as away, the board "
                  "file and its chunks as they were", code == "history_away" and boards_files(root) == held_odd
                  and chunk_set() == files_odd, code)
            vb[bh.HEAD]["chunks"][-1] = [n_last, h_last]
            vb[bh.HEAD][bh.OPEN] = 0
            tf.write_text(themes.render(raw) + "\n", encoding="utf-8", newline="\n")
            (folder / odd_name).unlink()
            bh.reset()

            # reset forgets the fetches and iCloud's asks too
            bh._FETCHING["probe"] = {"done": None}
            bh._ASKED["probe"] = None
            bh.reset()
            check("400: reset forgets the fetches under way and the files asked of iCloud, as a restart does",
                  not bh._FETCHING and not bh._ASKED, "")

            # memo's revisions carry no state, and a caller that reads one fails at once
            board = next(b for b in themes.boards_of(themes.load(juno)) if b["id"] == "v2")
            tries = []
            for reader in (lambda revs: revs[-1]["state"].get("cards"), lambda revs: len(revs[-1]["state"]),
                           lambda revs: themes.state_hash(revs[-1]["state"]), lambda revs: json.dumps(revs[-1])):
                bh._MEMO.clear()
                try:
                    bh.memo(board, "probe", reader)
                    tries.append("read")
                except RuntimeError:
                    tries.append("raised")
            bh._MEMO.clear()
            check("400: a caller of memo that reads a revision's state, its keys, its size, its hash or its JSON, fails "
                  "at once, and History's list still lists every revision",
                  tries == ["raised"] * 4 and len(listed()) == int(file_head().get("count") or 0), str(tries))

            # Working together and Share a copy carry every open chunk and nothing put aside
            set_open(0)
            keep("carried 1")
            keep("carried 2")
            heads = [bh.head_of(b) for b in json.loads(tf.read_text(encoding="utf-8"))["boards"]]
            want = {f"Working/{folder.name}/{n}" for h in heads for n in names(h)}
            sent = {rel for _p, rel in team_sync.participant_files(root / "Juno", juno, False) if ".history/" in rel}
            packed = {rel for _p, rel in project_pack.project_files(root) if rel.startswith("Juno/Working/")
                      and ".themes.history/" in rel}
            # a send carries the History folder's chunks whole (an earlier crash's orphans among them), never one aside
            check("400: a participant's version and a project's send carry every chunk the heads name, the open ones "
                  "among them, and none put aside",
                  bh.open_of(file_head()) == 2 and sent == want and {"Juno/" + w for w in want} <= packed
                  and not any("/superseded/" in r for r in packed),
                  f"{bh.open_of(file_head())} {sorted(sent ^ want)[:4]} {sorted(packed ^ {'Juno/' + w for w in want})[:4]}")
        finally:
            bh.FOLD, bh.CHUNK, themes.AUTO_KEEP = kept_fold
            bh.reset()

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
