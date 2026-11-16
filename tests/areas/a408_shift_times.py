"""Area 408: a sheet's timecodes shifted, for an agent (timeshift, 16 November 2026, Adam's ruling via the GRAVITY
session: a sheet that runs ahead of its recording through the whole sheet has its timecodes shifted, rather than an
offset set, and `turn edit --time` row by row would have been some 265 writes, each archiving the workbook).

What is checked, on a scratch copy of the demo made a project with its GETs, and on one participant of the
longitudinal demo with their LPETs and the LGETs: the dry run of `turn shift-times` gives the rows it would shift and
the first and last times before and after and writes nothing, no record, no restore point, no lock, no archive copy.
A shift that would take any timecode below 0:00 is refused whole in one line naming the rows, nothing written, dry run
or not. The shift moves every timecode in range by the seconds given, each cell in its own form, and nothing else of
the workbook, in one save with one copy in _Archive and one line in the record of agents' changes, which holds counts
and never a word. A range shift touches its rows alone. A shift and its opposite give the workbook back part for part
(its last-changed time alone, which every save sets, apart). The GETs', LPETs' and LGETs' copies take the new times, so
no participant reads as changed for it. The change's undo puts the workbook and the copies back byte for byte. MCP's
turn_shift_times runs the same op."""
from __future__ import annotations

import hashlib
import io
import json
import re
import shutil
import zipfile
from pathlib import Path

import openpyxl

from .support import check
from . import support

ASKED = "The transcript runs ahead of the recording, move its times"


def digest(root: Path) -> dict:
    """Every file of the project by its contents, the lock files set aside."""
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file() and not p.name.endswith(".lock")}


def parts(book: Path) -> dict:
    """A workbook's parts by name, the core properties' last-changed time, which every save sets, taken out."""
    with zipfile.ZipFile(io.BytesIO(book.read_bytes())) as z:
        out = {n: z.read(n) for n in z.namelist()}
    if "docProps/core.xml" in out:
        out["docProps/core.xml"] = re.sub(rb"<dcterms:modified[^>]*>[^<]*</dcterms:modified>", b"",
                                          out["docProps/core.xml"])
    return out


def sheet_cells(book: Path, sheet: str) -> tuple[dict, dict]:
    """A sheet's timecodes as seconds by row, and every other cell of the workbook by its place, as the suite's
    comparison reads it."""
    import workbook as wb_mod
    wb = openpyxl.load_workbook(book, rich_text=True)
    try:
        times, rest = {}, {}
        for ws in wb.worksheets:
            cols = wb_mod.detect_columns(ws)
            for row in ws.iter_rows():
                for c in row:
                    if ws.title == sheet and c.column == cols.get("ts") and c.row >= 2:
                        times[c.row] = wb_mod.ts_seconds(c.value)
                    else:
                        rest[(ws.title, c.coordinate)] = repr(support.cell_signature(c))
        return times, rest
    finally:
        wb.close()


def said_words(book: Path) -> list[str]:
    """The first twenty characters of every passage, statement, quote and note of a workbook, to look for."""
    import workbook as wb_mod
    wb = openpyxl.load_workbook(book, rich_text=True)
    try:
        out = []
        for ws, cols in wb_mod._transcript_sheets(wb):
            for r in range(2, ws.max_row + 1):
                for role in ("transcript", "es", "kq", "en"):
                    if role in cols:
                        text = wb_mod.plain_text(ws.cell(r, cols[role]).value)
                        if len(text) >= 20:
                            out.append(text[:20])
        return out
    finally:
        wb.close()


def make(root: Path) -> Path:
    """The demo's three participants as a project at `root`, with their GETs. Answers Juno's workbook."""
    import server as server_mod
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
    for one in sorted(shipped.glob("idiograph-*.json")):
        shutil.copy2(one, root / one.name)
    return root / "Juno" / "Juno - EN & ES.xlsx"


def test_shift_times(scratch: Path):
    print("\n408. A sheet's timecodes shifted for an agent: the dry run's rows and times and nothing written, the "
          "refusal below 0:00, one save, one archive copy and one line, a range alone, a shift and its opposite, the "
          "copies following, the undo, and MCP (timeshift, 16 November)")
    import agent_changes
    import agent_log
    import cli
    import gets as gets_mod
    import idiograph_routes as routes
    import mcp_server
    import os
    import server as server_mod

    base = scratch / "shift-times-408"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Dogs at home"
    juno = make(root)
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Adam",
                                       "corpus": "", "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    log = base / "agent-log.json"
    kept = (agent_changes.ALL_OPS, os.environ.get(agent_log.PLACE))
    agent_changes.ALL_OPS = None
    os.environ[agent_log.PLACE] = str(log)

    def run(*args, at=root, tool="Claude Code"):
        given = ["--config", str(config_file), "--root", str(at), "--json", *args]
        if tool is not None:
            given += ["--tool", tool]
        code, out, err = cli.run(given)
        return code, (support.plain(json.loads(out)) if out.strip() else {}), err + (out if code else "")

    def refusal(err: str) -> list:
        try:
            return json.loads(err[err.index("{"):]).get("lines") or []
        except ValueError:
            return [err]

    def page(fn, at):
        held = (server_mod.ROOT_OVERRIDE, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY)
        server_mod.ROOT_OVERRIDE, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY = str(at), config_file, {"recent": []}
        try:
            return fn()
        finally:
            server_mod.ROOT_OVERRIDE, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY = held

    def statuses(book: Path, at: Path, kind: str) -> dict:
        """Each case of a file of copies and whether it reads in or changed, as the GETs, LPETs and LGETs read it."""
        def read():
            with routes.copy_scope(kind, book, at):
                return {e["case"]: e["status"] for e in gets_mod.survey(routes.gets_books(at), gets_mod.load(at))}
        return page(read, at)

    def copy_times(at: Path, kind: str, book: Path, sheet: str) -> dict:
        """Every line of a sheet in a file of copies by its key, its seconds, span and time."""
        def read():
            with routes.copy_scope(kind, book, at):
                data = gets_mod.load(at)
            return {f"{c}/{k}": (v.get("seconds"), v.get("span"), v.get("time"))
                    for c, rec in (data.get("cases") or {}).items() for k, v in (rec.get("lines") or {}).items()
                    if isinstance(v, dict) and v.get("sheet") == sheet and Path(str(rec.get("workbook"))).name == book.name}
        return page(read, at)

    def archived(book: Path) -> list:
        folder = book.parent / "_Archive"
        return sorted(p.name for p in folder.glob("*pre-shift*")) if folder.is_dir() else []

    try:
        start = digest(root)
        times0, rest0 = sheet_cells(juno, "Initial")
        parts0 = parts(juno)
        timed = sorted(r for r, s in times0.items() if s is not None)
        gets0 = copy_times(root, "gets", juno, "Initial")
        check("408: the scratch copy's GETs hold Juno's statements with their times, every participant in",
              len(gets0) > 5 and set(statuses(juno, root, "gets").values()) == {"in"}, json.dumps(statuses(juno, root, "gets")))

        # ── 1. the dry run: the rows, the first and last times, nothing written
        code, dry, err = run("turn", "shift-times", "Juno", "Initial", "--by", "30", "--dry-run", tool=None)
        check("408: the dry run of +30 on the whole sheet says the rows it would shift and the first and last times "
              "before and after, rows and times alone",
              code == 0 and dry.get("dry_run") is True and dry.get("count") == len(timed)
              and dry["first"] == {"row": timed[0], "before": "00:00", "after": "00:30"}
              and dry["last"]["row"] == timed[-1] and dry.get("changed") is True
              and dry.get("copies", {}).get("gets", {}).get("lines") == len(gets0), err + json.dumps(dry)[:500])
        check("408: the dry run writes nothing: no record, no restore point, no lock, no archive copy",
              digest(root) == start and not (root / agent_changes.FILE).exists()
              and not (root / agent_changes.STORE).exists() and not archived(juno),
              str(sorted(set(digest(root)) ^ set(start))))

        # ── 2. below 0:00 refused whole, dry run or not, nothing written
        low = [r for r in timed if times0[r] < 30]
        for extra in (("--dry-run",), ("--note", ASKED)):
            code, _x, err = run("turn", "shift-times", "Juno", "Initial", "--by", "-30", *extra)
            check(f"408: a shift of -30 would take rows {low} below 0:00, so it is refused whole in one line naming "
                  f"them{' (dry run)' if extra[0] == '--dry-run' else ''}, nothing written",
                  code != 0 and len(refusal(err)) == 1 and "below 0:00" in refusal(err)[0]
                  and all(str(r) in refusal(err)[0] for r in low) and digest(root) == start and not archived(juno),
                  err[:300])
        code, _x, err = run("turn", "shift-times", "Juno", "Initial", "--by", "1.5", "--note", ASKED)
        check("408: a fraction of a second is refused, nothing written", code != 0 and digest(root) == start, err[:300])
        code, _x, err = run("turn", "shift-times", "Juno", "Initial", "--by", "30")
        check("408: a write with no request is refused, nothing written", code != 0 and digest(root) == start, err[:300])

        # ── 3. the shift: every timecode moved, nothing else, one save, one copy, one line
        code, done, err = run("turn", "shift-times", "Juno", "Initial", "--by", "30", "--note", ASKED)
        times1, rest1 = sheet_cells(juno, "Initial")
        check("408: +30 moves every timecode of the sheet by 30 seconds and leaves every other cell as it was",
              code == 0 and done.get("count") == len(timed)
              and all(times1[r] == times0[r] + 30 for r in timed) and rest1 == rest0, err + json.dumps(done)[:300])
        check("408: one copy of the workbook in _Archive, as it was before the shift",
              len(archived(juno)) == 1
              and hashlib.sha256((juno.parent / "_Archive" / archived(juno)[0]).read_bytes()).hexdigest()
              == start["Juno/Juno - EN & ES.xlsx"], str(archived(juno)))
        lines = agent_changes.read(root)
        line = lines[0] if lines else {}
        words = said_words(juno)
        check("408: one line in the record of agents' changes, its counts and no word of the workbook",
              len(lines) == 1 and line.get("op") == "turn shift-times" and line.get("request") == ASKED
              and line.get("shift") == {"by": 30, "from_row": 2, "to_row": max(times0), "rows": len(timed)}
              and line.get("target", {}).get("case") == "Juno" and line.get("target", {}).get("sheet") == "Initial"
              and line.get("undo_with", {}).get("copy") == archived(juno)[0]
              and len(words) > 20 and not any(w in json.dumps(line, ensure_ascii=False) for w in words),
              json.dumps(line)[:600])
        gets1 = copy_times(root, "gets", juno, "Initial")
        check("408: the GETs' copy takes the new times, and no participant reads as changed for it",
              all(gets1[k][0] == gets0[k][0] + 30 for k in gets0 if gets0[k][0] is not None)
              and all(gets1[k][2] != gets0[k][2] for k in gets0 if gets0[k][0] is not None)
              and set(statuses(juno, root, "gets").values()) == {"in"}, json.dumps(statuses(juno, root, "gets")))
        others = {k: v for k, v in start.items() if not k.startswith("Juno/") and k != "idiograph-gets.json"}
        check("408: no other participant's file changes", all(digest(root).get(k) == v for k, v in others.items()), "")

        # ── 4. the opposite shift gives the workbook back part for part, and the copy its times
        code, back, err = run("turn", "shift-times", "Juno", "Initial", "--by", "-30", "--note", ASKED)
        check("408: -30 after +30 gives the workbook back part for part, the save's last-changed time alone apart",
              code == 0 and parts(juno) == parts0, err[:300])
        check("408: and the GETs' copy its times as they were",
              copy_times(root, "gets", juno, "Initial") == gets0 and set(statuses(juno, root, "gets").values()) == {"in"},
              "")

        # ── 5. a range touches its rows alone, and its opposite gives it back
        lo, hi = timed[5], timed[15]
        code, ranged, err = run("turn", "shift-times", "Juno", "Initial", "--by", "-5", "--from-row", str(lo),
                                "--to-row", str(hi), "--note", ASKED)
        times2, rest2 = sheet_cells(juno, "Initial")
        check("408: a range shift of -5 moves rows {lo} to {hi} alone".format(lo=lo, hi=hi),
              code == 0 and ranged.get("count") == len([r for r in timed if lo <= r <= hi])
              and all(times2[r] == times0[r] - 5 if lo <= r <= hi else times2[r] == times0[r] for r in times0)
              and rest2 == rest0, err + json.dumps(ranged)[:300])
        code, _x, err = run("turn", "shift-times", "Juno", "Initial", "--by", "+5", "--from-row", str(lo),
                            "--to-row", str(hi), "--note", ASKED)
        check("408: and +5 on the same range gives the workbook back part for part",
              code == 0 and parts(juno) == parts0 and copy_times(root, "gets", juno, "Initial") == gets0, err[:300])

        # ── 6. the change's undo puts the workbook and the copy back byte for byte
        before = digest(root)
        code, done, err = run("turn", "shift-times", "Juno", "Initial", "--by", "121", "--note", ASKED,
                              tool="Another agent")
        changed = digest(root)
        cid = agent_changes.read(root)[-1]["id"]
        code_u, undone, err_u = run("agents", "undo-change", cid, "--note", "Put the times back")
        after = digest(root)
        check("408: the shift's undo puts the workbook and the GETs file back byte for byte",
              code == 0 and code_u == 0 and changed["Juno/Juno - EN & ES.xlsx"] != before["Juno/Juno - EN & ES.xlsx"]
              and changed["idiograph-gets.json"] != before["idiograph-gets.json"]
              and after["Juno/Juno - EN & ES.xlsx"] == before["Juno/Juno - EN & ES.xlsx"]
              and after["idiograph-gets.json"] == before["idiograph-gets.json"], err + err_u + json.dumps(undone)[:300])

        # ── 7. a longitudinal participant: their LPETs and the LGETs take the new times
        lroot = base / "Allotment"
        (lroot / "Arlo" / "Working").mkdir(parents=True)
        lipa = support.source("demo/lipa")
        held = json.loads((lipa / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
        held["agents"] = {"allowed": True, "at": "2026-11-16T09:00:00+00:00"}
        (lroot / server_mod.PROJECT_FILE).write_text(json.dumps(held), encoding="utf-8")
        arlo = lroot / "Arlo" / "Arlo - EN & ES.xlsx"
        shutil.copy2(lipa / "pristine" / "Arlo - EN & ES.xlsx", arlo)
        for one in sorted((lipa / "pristine" / "Working").glob("Arlo - EN & ES.*")):
            shutil.copy2(one, lroot / "Arlo" / "Working" / one.name)
        shutil.copy2(lipa / "pristine" / "idiograph-lgets.json", lroot / "idiograph-lgets.json")
        config_file.write_text(json.dumps({"projects": [{"root": str(root)}, {"root": str(lroot)}], "interviewer": "Adam",
                                           "corpus": "", "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
        lstart = digest(lroot)
        lp0, lg0 = copy_times(lroot, "lpets", arlo, "T2"), copy_times(lroot, "lgets", arlo, "T2")
        lp_in, lg_in = statuses(arlo, lroot, "lpets"), statuses(arlo, lroot, "lgets")
        code, ldry, err = run("turn", "shift-times", "Arlo", "T2", "--by", "7", "--dry-run", at=lroot, tool=None)
        check("408: on a participant of timepoints the dry run counts the LPETs' and the LGETs' lines that would "
              "follow, and writes nothing",
              code == 0 and ldry.get("copies", {}).get("lpets", {}).get("lines") == len(lp0) > 0
              and ldry.get("copies", {}).get("lgets", {}).get("lines") == len([k for k in lg0 if lg0[k][0] is not None])
              and digest(lroot) == lstart, err + json.dumps(ldry)[:500])
        code, ldone, err = run("turn", "shift-times", "Arlo", "T2", "--by", "7", "--note", ASKED, at=lroot)
        lp1, lg1 = copy_times(lroot, "lpets", arlo, "T2"), copy_times(lroot, "lgets", arlo, "T2")
        check("408: the LPETs' and the LGETs' copies of that timepoint take the new times, spans with them, and the "
              "participant reads in, as before",
              code == 0 and all(lp1[k][0] == lp0[k][0] + 7 for k in lp0 if lp0[k][0] is not None)
              and all(lg1[k][0] == lg0[k][0] + 7 for k in lg0 if lg0[k][0] is not None)
              and all(lp1[k][1] == [t + 7 for t in lp0[k][1]] for k in lp0 if isinstance(lp0[k][1], list))
              and statuses(arlo, lroot, "lpets") == lp_in and statuses(arlo, lroot, "lgets") == lg_in,
              err + json.dumps({"in": [lp_in, lg_in], "now": [statuses(arlo, lroot, "lpets"), statuses(arlo, lroot, "lgets")]})[:500])
        rid = agent_changes.read(lroot)[-1]["run"]
        code, _x, err = run("agents", "undo-run", rid, "--note", "Put the times back", at=lroot)
        check("408: the run's undo puts every file of the longitudinal project back byte for byte",
              code == 0 and {k: v for k, v in digest(lroot).items() if not k.startswith(agent_changes.STORE)
                             and k != agent_changes.FILE and "_Archive/" not in k} == lstart, err[:300])

        # ── 8. turn edit says what changes alone: the timecode, the words or both (the GRAVITY session's find, 16
        # November 2026: a timecode alone was said as words corrected)
        def said(*args) -> tuple:
            code, out, err = cli.run(["--config", str(config_file), "--root", str(root), *args, "--tool", "Claude Code"])
            return code, out + err

        held_book = hashlib.sha256(juno.read_bytes()).hexdigest()
        code_t, time_dry = said("turn", "edit", "Juno", "Initial", "3", "--time", "00:25", "--dry-run")
        words_now = said_words(juno)
        code_w, words_dry = said("turn", "edit", "Juno", "Initial", "3", "--text", "Fixed words of the passage.", "--dry-run")
        code_b, both_dry = said("turn", "edit", "Juno", "Initial", "3", "--text", "Fixed words of the passage.",
                                "--time", "00:25", "--dry-run")
        check("408: turn edit's dry run says the timecode alone when only the timecode changes, the words alone when "
              "only they change, and both when both do, nothing written",
              code_t == code_w == code_b == 0
              and "timecode would go from" in time_dry and "words would be corrected" not in time_dry
              and "words would be corrected" in words_dry and "timecode go from" not in words_dry
              and "words would be corrected" in both_dry and "timecode go from" in both_dry
              and hashlib.sha256(juno.read_bytes()).hexdigest() == held_book and said_words(juno) == words_now,
              time_dry + words_dry + both_dry)
        code_t, time_done = said("turn", "edit", "Juno", "Initial", "3", "--time", "00:25", "--note", ASKED)
        check("408: and turn edit with --time alone says it corrected the timecode, never the words",
              code_t == 0 and "Corrected the timecode of" in time_done and "words of" not in time_done
              and said_words(juno) == words_now, time_done)

        # ── 10. quote spans (timefix, the review's high finding): a quote may take in the same speaker's passage
        # before its own row, so each end of its span follows the row it belongs to. No demo copy holds a span, so one
        # is made here through the app's own write: a statement on Juno's row 15 whose quote takes in her row 13 too.
        import themes
        wbk = openpyxl.load_workbook(juno, read_only=True)
        try:
            ws = wbk["Initial"]
            said13, said15 = (str(ws.cell(r, 4).value or "") for r in (13, 15))
        finally:
            wbk.close()

        def lead(text: str) -> str:
            return " ".join(text.split()[:6]).rstrip(".,;:!?")

        spec = base / "span-408.json"
        spec.write_text(json.dumps({"request": ASKED, "statements": ["Her cross mornings run into the walk."],
                                    "quotes": [f"{lead(said13)} ... {lead(said15)}"]}), encoding="utf-8")
        code, _x, err = run("turn", "write", "Juno", "Initial", "15", "--from", str(spec))
        # a write's new statement joins the copy at its own passage's time; taking Juno's changes into the GETs gives
        # the copy the span a fresh read gives
        code_t, _x, err_t = run("gets", "take", "Juno", "--note", ASKED)
        code, err = code or code_t, err + err_t

        def fresh_span() -> dict:
            read = page(lambda: themes.read_cards(juno), root)
            return {c["key"]: c.get("span") for c in read["cards"] if c["sheet"] == "Initial" and c["row"] == 15}

        def gets_json() -> dict:
            out = json.loads((root / "idiograph-gets.json").read_text(encoding="utf-8"))
            out.pop("updated", None)
            return out

        spans = fresh_span()
        key15 = next(iter(spans), "")

        def copy_span():
            return next((v[1] for k, v in copy_times(root, "gets", juno, "Initial").items()
                         if k.endswith("/" + key15)), None)

        s0 = spans.get(key15)
        check("408: a statement written on row 15 whose quote takes in row 13 too has a span from row 13's time to "
              "row 15's, which the GETs' copy holds, the participant in",
              code == 0 and s0 == [times0[13], times0[15]] and copy_span() == s0
              and set(statuses(juno, root, "gets").values()) == {"in"}, err[:300] + json.dumps([spans, copy_span()]))
        book_span0, gets_span0 = parts(juno), gets_json()
        code, _x, err = run("turn", "shift-times", "Juno", "Initial", "--by", "40", "--note", ASKED)
        check("408: a whole-sheet shift moves both ends of the span, as a fresh read of the workbook gives them, and "
              "the participant still reads in",
              code == 0 and copy_span() == fresh_span().get(key15) == [s0[0] + 40, s0[1] + 40]
              and set(statuses(juno, root, "gets").values()) == {"in"}, err[:300] + json.dumps([copy_span(), fresh_span()]))
        code, _x, err = run("turn", "shift-times", "Juno", "Initial", "--by", "-40", "--note", ASKED)
        check("408: and its opposite gives the workbook back part for part and the GETs file as it was, its updated "
              "time alone apart",
              code == 0 and parts(juno) == book_span0 and gets_json() == gets_span0, err[:300])
        code, _x, err = run("turn", "shift-times", "Juno", "Initial", "--by", "3", "--from-row", "13", "--to-row", "13",
                            "--note", ASKED)
        check("408: a range shift of row 13 alone, the span's first row and not the statement's, moves the span's "
              "start and nothing else, as a fresh read gives it, and the participant still reads in",
              code == 0 and copy_span() == fresh_span().get(key15) == [s0[0] + 3, s0[1]]
              and set(statuses(juno, root, "gets").values()) == {"in"}, err[:300] + json.dumps([copy_span(), fresh_span()]))
        code, _x, err = run("turn", "shift-times", "Juno", "Initial", "--by", "-3", "--from-row", "13", "--to-row", "13",
                            "--note", ASKED)
        check("408: and -3 on row 13 gives the workbook and the GETs file back",
              code == 0 and parts(juno) == book_span0 and gets_json() == gets_span0, err[:300])

        # ── 11. the hour (timefix): a text timecode crossing it takes the sheet's form on its new side, hours folded
        # into the minutes where the sheet has none there, and the dry run counts those that cross
        import workbook as wb_mod

        def shifted(cells: list, cell: str, by: int) -> str:
            return wb_mod.shifted_like(cell, wb_mod.ts_seconds(cell) + by, wb_mod.shift_style(cells))

        forms = {"10:02 -121 among 9:58": shifted(["9:58", "10:02"], "10:02", -121),
                 "10:02 -121 among 09:58": shifted(["09:58", "10:02"], "10:02", -121),
                 "100:05 -121": shifted(["100:05"], "100:05", -121),
                 "05:12 +30": shifted(["00:00", "05:12"], "05:12", 30),
                 "59:30 +121, no cell past the hour": shifted(["58:29", "59:30"], "59:30", 121),
                 "59:30 +121 among 1:02:00": shifted(["58:29", "59:30", "1:02:00"], "59:30", 121),
                 "1:00:30 -121 among 58:29": shifted(["58:29", "1:00:30"], "1:00:30", -121),
                 "1:00:30 -121, no cell below the hour": shifted(["1:00:30", "1:20:00"], "1:00:30", -121)}
        check("408: a text timecode's first part is padded only where the sheet pads it, and one crossing the hour "
              "takes the sheet's form on its new side, MM:SS where the sheet has none there",
              forms == {"10:02 -121 among 9:58": "8:01", "10:02 -121 among 09:58": "08:01", "100:05 -121": "98:04",
                        "05:12 +30": "05:42", "59:30 +121, no cell past the hour": "61:31",
                        "59:30 +121 among 1:02:00": "1:01:31", "1:00:30 -121 among 58:29": "58:29",
                        "1:00:30 -121, no cell below the hour": "58:29"}, json.dumps(forms))
        mid = timed[len(timed) // 2]
        by_hour = 3600 - times0[mid]
        code, hdry, err = run("turn", "shift-times", "Juno", "Initial", "--by", str(by_hour), "--dry-run", tool=None)
        check("408: the dry run counts the timecodes that would cross the hour",
              code == 0 and hdry.get("crossed") == len([r for r in timed if times0[r] + by_hour >= 3600]) > 0,
              err[:300] + json.dumps(hdry)[:300])

        # ── 12. the order of writes (timefix): a copy that cannot follow refuses the whole shift with nothing written,
        # and a copy's write failing after the workbook's save is said in one line, the change's undo putting both back
        held_follow, held_write = gets_mod.times_followed, gets_mod.write
        before = digest(root)

        def broken(*a, **k):
            raise KeyError("lines")

        gets_mod.times_followed = broken
        try:
            code, _x, err = run("turn", "shift-times", "Juno", "Initial", "--by", "9", "--note", ASKED)
        finally:
            gets_mod.times_followed = held_follow
        check("408: a copy that cannot follow refuses the whole shift in one line, nothing written, the workbook "
              "neither saved nor archived",
              code != 0 and len(refusal(err)) == 1 and digest(root) == before, err[:300])

        def failing(*a, **k):
            raise OSError("disk full")

        gets_mod.write = failing
        try:
            code, half, err = run("turn", "shift-times", "Juno", "Initial", "--by", "9", "--note", ASKED)
        finally:
            gets_mod.write = held_write
        failed = (half.get("copies") or {}).get("failed") or []
        now = statuses(juno, root, "gets")
        check("408: a copy's write failing after the save leaves the workbook shifted, says so in one line, and the "
              "participant reads changed",
              code == 0 and len(failed) == 1 and "undo" in failed[0] and "gets" not in (half.get("copies") or {})
              and digest(root)["Juno/Juno - EN & ES.xlsx"] != before["Juno/Juno - EN & ES.xlsx"]
              and digest(root)["idiograph-gets.json"] == before["idiograph-gets.json"]
              and sorted(now.values()) != ["in"] * len(now),
              err[:300] + json.dumps(half)[:400] + json.dumps(now))
        cid = agent_changes.read(root)[-1]["id"]
        code, _x, err = run("agents", "undo-change", cid, "--note", "Put the times back")
        check("408: and the change's undo puts the workbook and the GETs file back byte for byte",
              code == 0 and digest(root)["Juno/Juno - EN & ES.xlsx"] == before["Juno/Juno - EN & ES.xlsx"]
              and digest(root)["idiograph-gets.json"] == before["idiograph-gets.json"]
              and set(statuses(juno, root, "gets").values()) == {"in"}, err[:300])

        # ── 13. a dry run on a project whose History has not been moved out of its board files yet writes nothing
        # (timefix, the review's sixth finding): the copies are read without the move
        import board_history as bh
        eroot = base / "Not moved"
        make(eroot)
        config_file.write_text(json.dumps({"projects": [{"root": str(root)}, {"root": str(lroot)}, {"root": str(eroot)}],
                                           "interviewer": "Adam", "corpus": "", "gravity_reference": "",
                                           "corpus_exclude": []}), encoding="utf-8")
        gf = eroot / "idiograph-gets.json"
        gd = json.loads(gf.read_text(encoding="utf-8"))
        gd["boards"][0].pop("history_head", None)
        gd["boards"][0]["history"] = [{"id": f"r{r + 1}", "at": f"2026-11-0{1 + r}T09:00:00+00:00", "name": "",
                                       "auto": True, "state": themes.board_state(gd["boards"][0])} for r in range(3)]
        gf.write_text(themes.render(gd) + "\n", encoding="utf-8")
        estart = digest(eroot)
        code, edry, err = run("turn", "shift-times", "Juno", "Initial", "--by", "30", "--dry-run", at=eroot, tool=None)
        check("408: on a project whose GETs board still holds its History inside the file, the dry run counts the "
              "copy's lines and writes nothing, the History left inside",
              code == 0 and (edry.get("copies") or {}).get("gets", {}).get("lines", 0) > 0 and digest(eroot) == estart
              and bh.embedded(json.loads(gf.read_text(encoding="utf-8"))) and not (eroot / "idiograph-gets.history").exists(),
              err[:300] + json.dumps(edry)[:300] + str(sorted(set(digest(eroot)) ^ set(estart))))

        # ── 9. MCP's turn_shift_times runs the same op
        tools = {t["name"]: t for t in mcp_server.tools_for("idiograph")}
        t = tools.get("turn_shift_times")
        args = mcp_server.arguments(dict(t, command=("turn", "shift-times")) if t else {"command": ("turn", "shift-times")},
                                    {"case": "Juno", "sheet": "Initial", "by": -121, "from_row": 4, "to_row": 9,
                                     "request": ASKED, "dry_run": True}, {"root": str(root)}, "Claude Desktop")
        check("408: MCP's turn_shift_times writes, takes the participant, sheet, by, from_row, to_row and dry_run, "
              "and maps to turn shift-times",
              t is not None and not t["annotations"]["readOnlyHint"] and t["command"] == ("turn", "shift-times")
              and {"case", "sheet", "by", "from_row", "to_row", "dry_run", "request"} <= set(t["inputSchema"]["properties"])
              and args.by == "-121" and args.from_row == 4 and args.to_row == 9 and args.case == "Juno",
              json.dumps(t)[:300] if t else "")
    finally:
        agent_changes.ALL_OPS = kept[0]
        if kept[1] is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = kept[1]
        agent_log.flush()
