"""Area 412: the copies follow a quote's span (spanfollow, 16 November 2026, found by timefix and its review).

A participant's copies of their statements (the GETs', the LPETs' at a timepoint, the LGETs') hold each line's time
and, where its quote takes in the same speaker's passages before its own row, its span. Two writes left a copy unlike
a fresh read, so the participant read changed until their changes were taken: a statement added by `turn write` or the
statements screen's save joined the copies at its own row's time without its quote's span, and `turn edit --time`
carried nothing to the copies. Now the added statement joins with the line a fresh read gives, a quote reworded takes
the span it now has, and one passage's timecode moves every copy's line and span end that belongs to its row, as
`turn shift-times` does (`gets.times_followed`).

What is checked, on a scratch copy of the longitudinal demo's Arlo with his LPETs and the LGETs: the dry runs of
`turn write` and `turn edit --time` say what would follow, counts and keys, and write nothing. A statement written on
a passage with none, whose quote takes in his passage before it, joins the LPETs' and the LGETs' copies with its span
and time, and every copy equals a fresh read, the participant still in. A timecode corrected on the row the span
starts on, then on the row it ends on, moves the copies' lines and span ends with it, each copy a fresh read and the
participant in. The quote reworded to its own passage alone takes the span off. The app's own save and its own
timecode edit do the same. Each agent's write is one line in the record, its undo putting every file back byte for
byte, and the run's undo putting the project back as it started."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import openpyxl

from .support import check
from . import support

ASKED = "Add the statement and correct the timecodes"


def digest(root: Path) -> dict:
    """Every file of the project by its contents, the lock files, the record and restore points of agents' changes
    and the workbooks' archive copies set aside."""
    import agent_changes
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if (not p.is_file() or p.name.endswith(".lock") or rel == agent_changes.FILE
                or rel.startswith(agent_changes.STORE) or "_Archive/" in rel):
            continue
        out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def lead(text: str) -> str:
    return " ".join(text.split()[:6]).rstrip(".,;:!?")


def test_span_follow(scratch: Path):
    print("\n412. The copies follow a quote's span: a statement added with one, a quote reworded, a timecode corrected "
          "where a span starts or ends, the dry runs, the app's own save and edit, and the undo (spanfollow, "
          "16 November)")
    import agent_changes
    import agent_log
    import cli
    import gets as gets_mod
    import idiograph_routes as routes
    import os
    import server as server_mod
    import themes

    base = scratch / "span-follow-412"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Allotment"
    (root / "Arlo" / "Working").mkdir(parents=True)
    lipa = support.source("demo/lipa")
    held = json.loads((lipa / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
    held["agents"] = {"allowed": True, "at": "2026-11-16T09:00:00+00:00"}
    (root / server_mod.PROJECT_FILE).write_text(json.dumps(held), encoding="utf-8")
    arlo = root / "Arlo" / "Arlo - EN & ES.xlsx"
    shutil.copy2(lipa / "pristine" / "Arlo - EN & ES.xlsx", arlo)
    for one in sorted((lipa / "pristine" / "Working").glob("Arlo - EN & ES.*")):
        shutil.copy2(one, root / "Arlo" / "Working" / one.name)
    shutil.copy2(lipa / "pristine" / "idiograph-lgets.json", root / "idiograph-lgets.json")
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Adam", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    log = base / "agent-log.json"
    kept = (agent_changes.ALL_OPS, os.environ.get(agent_log.PLACE))
    agent_changes.ALL_OPS = None
    os.environ[agent_log.PLACE] = str(log)

    def run(*args, tool="Claude Code"):
        given = ["--config", str(config_file), "--root", str(root), "--json", *args]
        if tool is not None:
            given += ["--tool", tool]
        code, out, err = cli.run(given)
        return code, (support.plain(json.loads(out)) if out.strip() else {}), err + (out if code else "")

    def page(fn):
        was = (server_mod.ROOT_OVERRIDE, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY)
        server_mod.ROOT_OVERRIDE, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY = str(root), config_file, {"recent": []}
        try:
            return fn()
        finally:
            server_mod.ROOT_OVERRIDE, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY = was

    def statuses(kind: str) -> dict:
        def read():
            with routes.copy_scope(kind, arlo, root):
                return {e["case"]: e["status"] for e in gets_mod.survey(routes.gets_books(root), gets_mod.load(root))}
        return page(read)

    def against_fresh(kind: str) -> tuple[bool, list]:
        """Whether every case of Arlo's in a file of copies is what a fresh read gives, lines and hash, and the keys
        whose time or span differ."""
        def read():
            with routes.copy_scope(kind, arlo, root):
                data = gets_mod.load(root)
                cases = data.get("cases") or {}
                same, off = True, []
                for b in routes.gets_books(root):
                    if Path(b["workbook"]).name != arlo.name or b["case"] not in cases or b.get("missing"):
                        continue
                    entry = dict({"case": b["case"], "workbook": arlo},
                                 **({"timepoint": b["timepoint"], "cite": b.get("cite") or ""}
                                    if b.get("timepoint") else {}))
                    fresh = gets_mod.fresh_of(entry)
                    rec = cases[b["case"]]
                    for k in set(fresh["lines"]) | set(rec.get("lines") or {}):
                        a = gets_mod.kept_time((rec.get("lines") or {}).get(k))
                        f = gets_mod.kept_time(fresh["lines"].get(k))
                        if not isinstance(a, dict) or not isinstance(f, dict) or \
                                (a.get("seconds"), a.get("span"), a.get("time")) != \
                                (f.get("seconds"), f.get("span"), f.get("time")):
                            off.append(f"{b['case']}/{k}")
                    same = same and gets_mod.snap_hash(fresh) == gets_mod.snap_hash(rec) == rec.get("hash")
                return same and not off, off
        return page(read)

    def copy_line(kind: str, key: str) -> dict | None:
        def read():
            with routes.copy_scope(kind, arlo, root):
                data = gets_mod.load(root)
            return next((rec["lines"][key] for rec in (data.get("cases") or {}).values()
                         if isinstance(rec, dict) and Path(str(rec.get("workbook") or arlo.name)).name == arlo.name
                         and key in (rec.get("lines") or {})), None)
        return page(read)

    def fresh_card(key: str) -> dict:
        def read():
            with themes.scoped(2):
                return next((c for c in themes.read_cards(arlo)["cards"] if c["key"] == key), {})
        return page(read)

    def all_in() -> bool:
        return set(statuses("lpets").values()) <= {"in"} and set(statuses("lgets").values()) <= {"in"}

    try:
        book = openpyxl.load_workbook(arlo, read_only=True)
        try:
            ws = book["T2"]
            words = {r: str(ws.cell(r, 4).value or "") for r in (7, 9, 27, 29)}
            secs = {r: int(sum(int(x) * m for x, m in zip(str(ws.cell(r, 2).value).split(":"), (3600, 60, 1))))
                    for r in (7, 9, 27, 29)}
            empty = {r: not ws.cell(r, 3).value for r in (9, 29)}
        finally:
            book.close()
        check("412: Arlo's T2 rows 9 and 29 hold no statement, each his passage after his own on rows 7 and 27 with "
              "only the interviewer's turn between",
              all(empty.values()) and all(len(w.split()) > 12 for w in words.values()), json.dumps(empty))
        start = digest(root)
        lp_in, lg_in = statuses("lpets"), statuses("lgets")
        ok_lp, off_lp = against_fresh("lpets")
        ok_lg, off_lg = against_fresh("lgets")
        check("412: before anything, Arlo reads in on his LPETs and the LGETs, every copy a fresh read",
              set(lp_in.values()) == {"in"} and set(lg_in.values()) == {"in"} and ok_lp and ok_lg,
              json.dumps([lp_in, lg_in, off_lp[:5], off_lg[:5]]))

        key = "T2:9:0"
        spec = base / "write-412.json"
        spec.write_text(json.dumps({"request": ASKED, "statements": ["His mornings at the plot run into the evenings."],
                                    "quotes": [f"{lead(words[7])} ... {lead(words[9])}"]}), encoding="utf-8")

        # ── 1. turn write's dry run: what would join the copies, keys alone, nothing written
        code, dry, err = run("turn", "write", "Arlo", "T2", "9", "--from", str(spec), "--dry-run", tool=None)
        followed = dry.get("copies_followed") or {}
        check("412: turn write's dry run says the statement would join the LPETs' and the LGETs' copies, by its key, "
              "and writes nothing",
              code == 0 and key in (followed.get("lpets") or {}).get("added", [])
              and key in (followed.get("lgets") or {}).get("added", []) and digest(root) == start,
              err[:300] + json.dumps(followed)[:300])

        # ── 2. the write: the statement joins with its span, every copy a fresh read
        code, done, err = run("turn", "write", "Arlo", "T2", "9", "--from", str(spec))
        card = fresh_card(key)
        lp, lg = copy_line("lpets", key), copy_line("lgets", key)
        ok_lp, off_lp = against_fresh("lpets")
        ok_lg, off_lg = against_fresh("lgets")
        check("412: a fresh read gives the statement on row 9 a span from row 7's time to row 9's",
              code == 0 and card.get("span") == [secs[7], secs[9]], err[:300] + json.dumps(card)[:300])
        check("412: the statement joins the LPETs' and the LGETs' copies with that span, every copy what a fresh read "
              "gives, time and span, and Arlo still reads in",
              (lp or {}).get("span") == card.get("span") and (lg or {}).get("span") == card.get("span")
              and ok_lp and ok_lg and all_in(),
              json.dumps([lp, lg, off_lp[:5], off_lg[:5], statuses("lpets"), statuses("lgets")])[:700])
        lines = agent_changes.read(root)
        check("412: the write is one line in the record of agents' changes",
              len(lines) == 1 and lines[0].get("op") == "turn write", json.dumps(lines)[:300])
        written = digest(root)

        # ── 3. its undo puts every file back byte for byte, and doing it again gives the same files
        code_u, _x, err_u = run("agents", "undo-change", lines[0]["id"], "--note", "Put it back")
        check("412: the write's undo puts every file of the project back byte for byte, the copies included",
              code_u == 0 and digest(root) == start, err_u[:300] + str(sorted(k for k in start if digest(root).get(k) != start[k])))
        code, done, err = run("turn", "write", "Arlo", "T2", "9", "--from", str(spec))
        ok_lp, _o = against_fresh("lpets")
        ok_lg, _o2 = against_fresh("lgets")
        check("412: and the same write again leaves every copy a fresh read",
              code == 0 and ok_lp and ok_lg and all_in(), err[:300])
        written = digest(root)

        # ── 4. turn edit --time on the row the span starts on: the dry run counts, writes nothing
        code, edry, err = run("turn", "edit", "Arlo", "T2", "7", "--time", "00:01:30", "--dry-run", tool=None)
        copies = edry.get("copies") or {}
        check("412: turn edit --time's dry run on row 7 counts the LPETs' and the LGETs' lines that would take the "
              "new time, row 7's and the span starting there, and writes nothing",
              code == 0 and (copies.get("lpets") or {}).get("lines", 0) >= 2
              and (copies.get("lgets") or {}).get("lines", 0) >= 2 and digest(root) == written,
              err[:300] + json.dumps(edry)[:400])
        code, _x, err = run("turn", "edit", "Arlo", "T2", "7", "--time", "00:01:30", "--note", ASKED)
        ok_lp, off_lp = against_fresh("lpets")
        ok_lg, off_lg = against_fresh("lgets")
        check("412: the timecode on row 7 moves the span's start with it in every copy, each a fresh read, and Arlo "
              "still reads in",
              code == 0 and (copy_line("lpets", key) or {}).get("span") == [90, secs[9]]
              and (copy_line("lgets", key) or {}).get("span") == [90, secs[9]]
              and fresh_card(key).get("span") == [90, secs[9]] and ok_lp and ok_lg and all_in(),
              err[:300] + json.dumps([off_lp[:5], off_lg[:5], copy_line("lpets", key)])[:500])
        before_end = digest(root)
        n_before = len(agent_changes.read(root))

        # ── 5. and on the row it ends on, the statement's own
        code, _x, err = run("turn", "edit", "Arlo", "T2", "9", "--time", "00:02:20", "--note", ASKED)
        ok_lp, off_lp = against_fresh("lpets")
        ok_lg, off_lg = against_fresh("lgets")
        lp = copy_line("lpets", key) or {}
        check("412: the timecode on row 9 moves the span's end and the statement's own time in every copy, each a "
              "fresh read, and Arlo still reads in",
              code == 0 and lp.get("span") == [90, 140] and lp.get("seconds") == 140
              and (copy_line("lgets", key) or {}).get("span") == [90, 140] and ok_lp and ok_lg and all_in(),
              err[:300] + json.dumps([off_lp[:5], off_lg[:5], lp])[:500])
        lines = agent_changes.read(root)
        check("412: each timecode corrected is one more line in the record",
              len(lines) == n_before + 1 and [x.get("op") for x in lines[-2:]] == ["turn edit", "turn edit"],
              json.dumps([x.get("op") for x in lines]))
        code_u, _x, err_u = run("agents", "undo-change", lines[-1]["id"], "--note", "Put it back")
        check("412: the edit's undo puts every file back byte for byte, the copies included",
              code_u == 0 and digest(root) == before_end,
              err_u[:300] + str(sorted(k for k in before_end if digest(root).get(k) != before_end[k])))

        # ── 6. the quote reworded to its own passage alone takes the span off
        spec2 = base / "requote-412.json"
        spec2.write_text(json.dumps({"request": ASKED, "statements": ["His mornings at the plot run into the evenings."],
                                     "quotes": [lead(words[9])]}), encoding="utf-8")
        code, _x, err = run("turn", "write", "Arlo", "T2", "9", "--from", str(spec2))
        ok_lp, off_lp = against_fresh("lpets")
        ok_lg, off_lg = against_fresh("lgets")
        check("412: a quote reworded to its own passage alone takes the span off every copy, each a fresh read, and "
              "Arlo still reads in",
              code == 0 and "span" not in (copy_line("lpets", key) or {"span": 1})
              and "span" not in (copy_line("lgets", key) or {"span": 1}) and not fresh_card(key).get("span")
              and ok_lp and ok_lg and all_in(), err[:300] + json.dumps([off_lp[:5], off_lg[:5]]))

        # ── 7. another agent's run, two timecodes and the quote taking in row 7 again, and the run's undo
        here = digest(root)
        steps = [run("turn", "edit", "Arlo", "T2", "7", "--time", "00:01:33", "--note", ASKED, tool="Another agent"),
                 run("turn", "edit", "Arlo", "T2", "9", "--time", "00:02:25", "--note", ASKED, tool="Another agent"),
                 run("turn", "write", "Arlo", "T2", "9", "--from", str(spec), tool="Another agent")]
        ok_lp, off_lp = against_fresh("lpets")
        ok_lg, off_lg = against_fresh("lgets")
        check("412: another agent's two timecodes and the quote taking in row 7 again leave every copy a fresh read, "
              "the span [93, 145], and Arlo in",
              all(c == 0 for c, _d, _e in steps) and (copy_line("lpets", key) or {}).get("span") == [93, 145]
              and ok_lp and ok_lg and all_in(), " ".join(e[:200] for _c, _d, e in steps) + json.dumps([off_lp, off_lg])[:300])
        rid = agent_changes.read(root)[-1]["run"]
        code_u, _x, err_u = run("agents", "undo-run", rid, "--note", "Put it all back")
        check("412: that run's undo puts every file of the project back byte for byte",
              code_u == 0 and digest(root) == here,
              err_u[:300] + str(sorted(k for k in here if digest(root).get(k) != here[k])))

        # ── 8. the app's own save and its own timecode edit go the same way
        key29 = "T2:29:0"
        body = {"path": str(arlo), "sheet": "T2", "row": 29,
                "pairs": [{"es": "The harvest talk runs on.", "kq": f"{lead(words[27])} ... {lead(words[29])}"}]}
        saved = page(lambda: routes.api_commit(body))
        ok_lp, off_lp = against_fresh("lpets")
        ok_lg, off_lg = against_fresh("lgets")
        check("412: the statements screen's save adds a statement whose quote takes in row 27 with its span, every copy "
              "a fresh read, and Arlo still reads in",
              not saved.get("error") and (copy_line("lpets", key29) or {}).get("span") == [secs[27], secs[29]]
              and ok_lp and ok_lg and all_in(), json.dumps([saved.get("error"), off_lp[:5], off_lg[:5]])[:500])
        edited = page(lambda: routes.api_edit_turn({"path": str(arlo), "sheet": "T2", "row": 27,
                                                    "text": words[27], "timecode": "00:07:59"}))
        ok_lp, off_lp = against_fresh("lpets")
        ok_lg, off_lg = against_fresh("lgets")
        check("412: the app's own timecode edit on row 27 moves the span's start in every copy, each a fresh read, and "
              "Arlo still reads in",
              edited.get("time_changed") and (copy_line("lpets", key29) or {}).get("span") == [479, secs[29]]
              and ok_lp and ok_lg and all_in(), json.dumps([edited.get("copies"), off_lp[:5], off_lg[:5]])[:500])

        # ── 9. a row given its first timecode gives it to the span end that is its row's (spanfix)
        run("turn", "write", "Arlo", "T2", "9", "--from", str(spec))
        # row 7's timecode is taken out of the scratch copy alone, and the copies made what a fresh read gives
        book = openpyxl.load_workbook(arlo)
        book["T2"].cell(7, 2).value = None
        book.save(arlo)
        book.close()

        def fresh_copies(kind):
            with routes.copy_scope(kind, arlo, root):
                data = gets_mod.load(root)
                for b in routes.gets_books(root):
                    if Path(b["workbook"]).name != arlo.name or b["case"] not in (data.get("cases") or {}):
                        continue
                    entry = dict({"case": b["case"], "workbook": arlo},
                                 **({"timepoint": b["timepoint"], "cite": b.get("cite") or ""}
                                    if b.get("timepoint") else {}))
                    fresh = gets_mod.fresh_of(entry)
                    data["cases"][b["case"]]["lines"] = fresh["lines"]
                    data["cases"][b["case"]]["hash"] = gets_mod.snap_hash(fresh)
                gets_mod.write(root, data)
        for kind in ("lpets", "lgets"):
            page(lambda kind=kind: fresh_copies(kind))
        pre = (copy_line("lpets", key) or {}).get("span")
        check("412: with row 7 untimed, the statement taking in row 7 has a span with no start in every copy, as a "
              "fresh read gives it",
              pre is not None and pre[0] is None and (copy_line("lgets", key) or {}).get("span") == pre, json.dumps(pre))
        code, _x, err = run("turn", "edit", "Arlo", "T2", "7", "--time", "00:01:41", "--note", ASKED)
        ok_lp, off_lp = against_fresh("lpets")
        ok_lg, off_lg = against_fresh("lgets")
        check("412: a timecode given to row 7 for the first time gives the span's start to every copy, each a fresh "
              "read",
              code == 0 and (copy_line("lpets", key) or {}).get("span") == [101, secs[9]]
              and (copy_line("lgets", key) or {}).get("span") == [101, secs[9]] and ok_lp and ok_lg,
              err[:300] + json.dumps([off_lp[:5], off_lg[:5], copy_line("lpets", key)])[:500])

        # ── 10. a copy that cannot follow: the timecode is saved, the others follow, the one that cannot is named
        lgets_file = root / "idiograph-lgets.json"
        good = lgets_file.read_bytes()
        lgets_file.write_bytes(b"{not json")
        before_bad = digest(root)
        code, dry_bad, err = run("turn", "edit", "Arlo", "T2", "9", "--time", "00:02:30", "--dry-run", tool=None)
        said = dry_bad.get("copies") or {}
        check("412: with the LGETs file malformed, the dry run of a timecode says the LPETs' lines would follow and "
              "names the LGETs as one that would not, and writes nothing",
              code == 0 and (said.get("lpets") or {}).get("lines", 0) >= 1 and "lgets" not in said
              and len(said.get("failed") or []) == 1 and "LGETs" in said["failed"][0] and digest(root) == before_bad,
              err[:300] + json.dumps(dry_bad)[:500])
        code, real_bad, err = run("turn", "edit", "Arlo", "T2", "9", "--time", "00:02:30", "--note", ASKED)
        said = real_bad.get("copies") or {}
        book = openpyxl.load_workbook(arlo, read_only=True)
        try:
            saved_time = str(book["T2"].cell(9, 2).value)
        finally:
            book.close()
        check("412: and the real edit saves the workbook, the LPETs' copy follows and the LGETs get one line under "
              "failed, the file as it was",
              code == 0 and saved_time.endswith("2:30") and (copy_line("lpets", key) or {}).get("span") == [101, 150]
              and len(said.get("failed") or []) == 1 and "LGETs" in said["failed"][0]
              and lgets_file.read_bytes() == b"{not json", err[:300] + json.dumps([real_bad, saved_time])[:500])
        lgets_file.write_bytes(good)

        # ── 11. Working together's GETs guard is the dry run's as it is the edit's, and shift-times keeps refusing
        guard_was, times_was = gets_mod.WRITE_GUARD, gets_mod.times_followed
        asked = []

        def with_gets(*a, **k):
            # the demo has no GETs file, so the first file asked, the GETs', is given one line to follow
            asked.append(1)
            return {"lines": 1, "cases": ["Arlo"]} if asked == [1] else times_was(*a, **k)

        def refuse(_root):
            raise server_mod.WorkbookError("This GETs board is another member's")
        try:
            gets_mod.WRITE_GUARD, gets_mod.times_followed = refuse, with_gets
            before_guard = digest(root)
            code, dry_g, err = run("turn", "edit", "Arlo", "T2", "9", "--time", "00:02:40", "--dry-run", tool=None)
            asked.clear()
            code2, _d, err2 = run("turn", "shift-times", "Arlo", "T2", "--by", "5", "--dry-run", tool=None)
        finally:
            gets_mod.WRITE_GUARD, gets_mod.times_followed = guard_was, times_was
        guard_fires = any("another member's" in x for x in (dry_g.get("copies") or {}).get("failed") or [])
        check("412: with a GETs guard that refuses, the timecode's dry run names it under failed and does not say the "
              "GETs would follow, and turn shift-times' dry run is refused, nothing written either way",
              code == 0 and guard_fires and "gets" not in (dry_g.get("copies") or {})
              and code2 != 0 and "another member's" in err2 and digest(root) == before_guard,
              json.dumps([dry_g.get("copies"), code2, err2[:200]])[:600])
    finally:
        agent_changes.ALL_OPS = kept[0]
        if kept[1] is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = kept[1]
        agent_log.flush()
