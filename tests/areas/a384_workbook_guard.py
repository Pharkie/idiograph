"""Area 384: a case's own workbook, a save that keeps the file, and a removal on the interviewer's turn (wbguard,
13 November 2026).

On 13 November a participant's workbook went from its folder during a run of agent writes and iCloud Drive left two
copies named `<stem> 2.xlsx` and `<stem> 3.xlsx` in its place. The app took the newest for the case, wrote into it
under a progress file of its own and found none of its boards. A save had put a temp file over the workbook with
`os.replace`, which gives the name a new file, the step iCloud kept apart.

What is checked, on invented cases copied from the demo's pristine copy: A, with the workbook gone and two numbered
copies in its place, `turn write`, `turn show` and `statements` refuse in one line naming the folder, the missing
workbook and the copies, nothing written and no progress file of a copy's made, `cases` and `validate` report it,
the page's row says it with nothing to open, and the server's reads, writes and request paths refuse it, never a
copy. Another workbook in its place is refused the same way, a case with its own workbook beside another, or with
no files of its own yet, is not, and the name put back opens it again. B, a save writes into the same file, its
inode and permissions kept and no file of its own left beside it, a write that fails part way puts the old bytes
back, a file not there yet is made whole, and a reader that meets a workbook half written while another writer holds
the case's lock reads it again until it is whole. C, `turn write` takes a statement off the interviewer's turn by its
key and a lone quote by its words, its card going from the board and the next card taking its place, his row's state
left as it was, and anything else there refused as before, with MCP's `turn_write` the same."""
from __future__ import annotations

import json
import os
import shutil
import stat
import threading
import time
from pathlib import Path

from . import support
from .support import DEMO_QUESTION, check


def ck(name: str, condition, detail="") -> None:
    """A check whose detail is said only when it fails."""
    check(name, bool(condition), "" if condition else str(detail)[:600])


def test_workbook_guard(scratch: Path):
    print("\n384. A case's own workbook, a save that keeps the file, and a removal on the interviewer's turn "
          "(wbguard, 13 November 2026)")
    import cli
    import i18n
    import idiograph_cli
    import idiograph_routes as routes
    import locks
    import rounds as rounds_mod
    import server as server_mod
    import themes as themes_mod
    import workbook as wb_mod
    from errors import WorkbookError

    pristine = support.DEMO_PRISTINE
    tail = " - EN & ES"

    def make_root(at: Path, names=("Juno", "Rowan", "Mabel")) -> Path:
        shutil.rmtree(at, ignore_errors=True)
        for name in names:
            case = at / name
            (case / "Working").mkdir(parents=True)
            shutil.copy2(pristine / f"{name}{tail}.xlsx", case / f"{name}{tail}.xlsx")
            for side in (pristine / "Working").glob(f"{name} - *"):
                shutil.copy2(side, case / "Working" / side.name)
        (at / server_mod.PROJECT_FILE).write_text(json.dumps({
            "name": "Dogs, a scratch project", "research_question": DEMO_QUESTION,
            "agents": {"allowed": True, "at": "2026-11-13T10:00:00+00:00"}}), encoding="utf-8")
        return at

    def files(at: Path) -> dict:
        return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*"))
                if p.is_file() and p.name != locks.NAME}

    def refused(fn, *args) -> str | None:
        try:
            fn(*args)
        except WorkbookError as exc:
            return str(exc)
        return None

    root = make_root(scratch / "wbguard-root")
    config_file = scratch / "wbguard-config.json"
    config_file.write_text(json.dumps({"root": str(root), "interviewer": "Adam"}), encoding="utf-8")

    def run(*args) -> tuple[int, str, str]:
        return cli.run(["--root", str(root), "--config", str(config_file), *args])

    def answer(*args):
        code, out, _err = run(*args, "--json")
        return code, support.plain(json.loads(out)) if out.strip() else {}

    def spec(name: str, value) -> str:
        path = scratch / f"wbguard-{name}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return str(path)

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, locks.WAIT)
    try:
        server_mod.CONFIG_PATH = config_file
        server_mod.ROOT_OVERRIDE = str(root)
        server_mod.STATE_MEMORY = {"recent": []}

        # ── A. the workbook gone, two numbered copies in its place
        folder = root / "Juno"
        book = folder / f"Juno{tail}.xlsx"
        two, three = folder / f"Juno{tail} 2.xlsx", folder / f"Juno{tail} 3.xlsx"
        shutil.copy2(book, three)
        book.rename(two)
        os.utime(three, (time.time() + 5, time.time() + 5))
        before = files(root)
        turn = {"pairs": [{"statement": "A walk she knows better than anyone",
                           "quote": "there are mornings where I genuinely think she is walking me"}],
                "request": "Code turn 15"}
        code, _out, err = run("turn", "write", "Juno", "Initial", "15", "--from", spec("turn", turn))
        said = wb_mod.displaced_said(wb_mod.displaced(three))
        ck("384: turn write refuses where the workbook is missing and two numbered copies stand, nothing written",
              code == 1 and said in err and files(root) == before
              and not (folder / "Working" / f"Juno{tail} 3.progress.json").exists()
              and not (folder / "_Archive").exists(), err)
        ck("384: the line names the folder, the missing workbook and the copies, never picking one",
              f"Juno{tail}.xlsx is missing from the folder Juno" in said and f"Juno{tail} 2.xlsx" in said
              and f"Juno{tail} 3.xlsx" in said, said)
        code_show, _out, err_show = run("turn", "show", "Juno", "Initial", "14")
        code_st, _out, err_st = run("statements", "Juno")
        ck("384: turn show and statements refuse with the same line",
              code_show == 1 and said in err_show and code_st == 1 and said in err_st, err_show + err_st)
        code, data = answer("cases")
        rows = {r["case"]: r for r in data.get("cases", [])}
        code_v, valid = answer("validate")
        ck("384: cases gives the participant by the missing workbook with the line, and validate counts it",
              code == 0 and rows.get("Juno", {}).get("workbook") == f"Juno{tail}.xlsx"
              and rows["Juno"].get("missing") == said and "missing" not in rows.get("Rowan", {})
              and valid.get("valid") is False and said in valid.get("problems", []), (rows, valid))
        cards = {c["case"]: c for c in routes.participants(root, routes.list_cases(root), [])}
        ck("384: the row on Home says it, with nothing to open",
              cards["Juno"].get("missing") == said and cards["Juno"]["path"] is None
              and "missing" not in cards["Rowan"] and cards["Rowan"]["path"])
        ck("384: the server's reads, writes and request paths refuse a copy and the missing workbook alike",
              refused(wb_mod.read_case, three) == said and refused(wb_mod.read_case, book) == said
              and refused(themes_mod.read_cards, two) == said
              and refused(lambda p: wb_mod.case_held(p).__enter__(), three) == said
              and refused(routes.case_path, str(two)) == said and files(root) == before)
        js = support.text("apps/idiograph/static/distil.js")
        ck("384: the row draws the server's line in place of its halves",
              "if (p.missing) {" in js and "esc(p.missing)" in js)

        # another workbook in the copies' place, and the cases that are not refused
        two.unlink()
        three.rename(folder / "Juno interview.xlsx")
        other = wb_mod.displaced(folder / "Juno interview.xlsx")
        ck("384: another workbook standing in its place is refused the same way",
              other is not None and other["copies"] is False and other["found"] == ["Juno interview.xlsx"]
              and refused(wb_mod.read_case, folder / "Juno interview.xlsx") == wb_mod.displaced_said(other))
        (folder / "Juno interview.xlsx").rename(book)
        rowan = root / "Rowan" / f"Rowan{tail}.xlsx"
        shutil.copy2(rowan, root / "Rowan" / "Rowan notes.xlsx")
        fresh = root / "Wren"
        fresh.mkdir()
        shutil.copy2(rowan, fresh / f"Wren{tail}.xlsx")
        ck("384: a case with its own workbook beside another, or with no files of its own yet, is not refused",
              wb_mod.displaced(rowan) is None and wb_mod.displaced(root / "Rowan" / "Rowan notes.xlsx") is None
              and wb_mod.displaced(fresh / f"Wren{tail}.xlsx") is None and wb_mod.displaced(book) is None)
        (root / "Rowan" / "Rowan notes.xlsx").unlink()
        shutil.rmtree(fresh)
        code, text, _ = run("turn", "show", "Juno", "Initial", "14")
        ck("384: the name put back, the participant opens again", code == 0 and "row 14" in text, text)

        # ── B. a save writes into the same file
        os.chmod(rowan, 0o640)
        ino = rowan.stat().st_ino
        wb_mod.save_turn(rowan, "Initial", 5, "A saved statement", None, None)
        left = [p.name for p in rowan.parent.iterdir() if p.name.startswith(".") and p.name != ".DS_Store"]
        row = next(r for s in wb_mod.read_case(rowan)["sheets"] for r in s["rows"] if r["row"] == 5)
        ck("384: a save writes into the same file, its permissions kept, no file of its own left beside it",
              rowan.stat().st_ino == ino and support.mode_is(rowan, 0o640) and not left
              and row["es"] == "A saved statement", (left, oct(stat.S_IMODE(rowan.stat().st_mode))))
        was = rowan.read_bytes()
        real_fsync = os.fsync

        def broken(_fd):
            raise OSError("the disk went away")

        os.fsync = broken
        try:
            failed = False
            try:
                locks.write_over(rowan, b"not a workbook" * 10)
            except OSError:
                failed = True
        finally:
            os.fsync = real_fsync
        ck("384: a write that fails part way puts the old bytes back and raises",
              failed and rowan.read_bytes() == was and rowan.stat().st_ino == ino)
        made = scratch / "wbguard-new" / "made.xlsx"
        shutil.rmtree(made.parent, ignore_errors=True)
        made.parent.mkdir()
        locks.write_over(made, was)
        ck("384: a file not there yet is made whole, nothing else left in its folder",
              made.read_bytes() == was and [p.name for p in made.parent.iterdir()] == ["made.xlsx"])
        rowan.write_bytes(was[: len(was) // 2])
        locks.WAIT = 5.0

        def mend():
            time.sleep(0.4)
            rowan.write_bytes(was)

        with wb_mod.case_held(rowan):
            mender = threading.Thread(target=mend)
            mender.start()
            got = wb_mod.whole(rowan).getvalue()
            mender.join()
        ck("384: a reader that meets the workbook half written while another writer holds the lock reads it whole",
              got == was)

        # ── C. a removal on the interviewer's turn
        juno = book
        wb_mod.save_turn(juno, "Initial", 14, None, None, None,
                         pairs=[{"es": "A stray statement", "kq": ""},
                                {"es": "Another stray one", "kq": '"is she walking me"'},
                                {"es": "", "kq": '"a lone line"'}])
        progress_before = json.loads(rounds_mod.progress_path(juno).read_text(encoding="utf-8"))["rows"].get("Initial:14")
        code, _out, err = run("board", "new", "Juno", "--from", spec("board", {
            "pets": [{"title": "Strays", "members": ["Initial:14:0", "Initial:14:1"]}]}), "--note", "strays")
        board = themes_mod.boards_of(themes_mod.load(juno))[-1]
        keys = lambda b: {k for g in b.get("groups") or [] for k in g.get("members") or [] if str(k).startswith("Initial:14")}
        ck("384: a board holds the two statements on the interviewer's turn", code == 0 and keys(board) == {
            "Initial:14:0", "Initial:14:1"}, (err, keys(board)))
        code, text, _ = run("turn", "show", "Juno", "Initial", "14")
        version = next(line.split(": ", 1)[1] for line in text.splitlines() if line.strip().startswith("Version:"))
        refusal = i18n.t("cli.turn_write.that_turn_is_the_interviewers_and")
        snap = files(root)
        code_add, _o, err_add = run("turn", "write", "Juno", "Initial", "14", "--from", spec("add", {
            "pairs": [{"statement": "A stray statement", "key": "Initial:14:0"}], "request": "x"}))
        code_mix, _o, err_mix = run("turn", "write", "Juno", "Initial", "14", "--from", spec("mix", {
            "remove": ["Initial:14:0"], "notes": ["A note"], "request": "x"}))
        code_far, _o, err_far = run("turn", "write", "Juno", "Initial", "14", "--from", spec("far", {
            "remove": ["Initial:14:7"], "request": "x"}))
        ck("384: anything but a removal on the interviewer's turn is refused as before, a key not there too",
              code_add == 1 and refusal in err_add and code_mix == 1 and refusal in err_mix
              and code_far == 1 and "Initial:14:7 " + idiograph_cli.NOT_THIS_LINE in err_far and files(root) == snap,
              err_add + err_mix + err_far)
        code, out, _ = run("turn", "write", "Juno", "Initial", "14", "--json", "--from", spec("off", {
            "remove": ["Initial:14:0"], "version": version, "request": "Take the stray statement off"}))
        done = json.loads(out) if out.strip() else {}
        row = next(r for s in wb_mod.read_case(juno)["sheets"] for r in s["rows"] if r["row"] == 14)
        board = next(b for b in themes_mod.boards_of(themes_mod.load(juno)) if b.get("id") == board.get("id"))
        progress = json.loads(rounds_mod.progress_path(juno).read_text(encoding="utf-8"))
        ck("384: a statement taken off the interviewer's turn by its key, with its own quote, the rest kept",
              code == 0 and row["es"] == "Another stray one" and row["pairs"] == [
                  {"es": "Another stray one", "kq": '"is she walking me"'}, {"es": "", "kq": '"a lone line"'}], (out, row))
        ck("384: its card goes from the board, the next card taking its key, his row's state as it was",
              keys(board) == {"Initial:14:0"} and progress["rows"].get("Initial:14") == progress_before
              and progress["edits"][-1]["row"] == 14 and done.get("backup"), (keys(board), progress["rows"].get("Initial:14")))
        code, _out, _err = run("turn", "write", "Juno", "Initial", "14", "--from", spec("lone", {
            "remove": ['"a lone line"'], "request": "Take the lone quote off"}))
        row = next(r for s in wb_mod.read_case(juno)["sheets"] for r in s["rows"] if r["row"] == 14)
        ck("384: a lone quote taken off the interviewer's turn by its words",
              code == 0 and row["pairs"] == [{"es": "Another stray one", "kq": '"is she walking me"'}], row)
        import idiograph_mcp
        tool = next(t for t in idiograph_mcp.TOOLS if t["name"] == "turn_write")
        ck("384: MCP's turn_write says remove takes a statement's key, the one write the interviewer's passage takes",
              "by its key" in tool["inputSchema"]["properties"]["remove"]["description"]
              and "interviewer's passage" in tool["inputSchema"]["properties"]["remove"]["description"])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, locks.WAIT = kept
