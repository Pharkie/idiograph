"""Area 401: a statement added reaches every copy of its participant's statements (copiesadd, 16 November 2026).

Found by the session that runs Adam's longitudinal study: a statement added with `turn write` never reached the
participant's LPETs copy, so a Trajectories cell could not take its quote ("is not a quote of ... interview at T2"),
and `copies refresh` brought in line only the statements a copy already held. What is checked, on a scratch copy of
the longitudinal demo as a fresh clone has it. A: a statement added by `turn write` at T2 is refused as a Trajectories
quote before the write; the write's dry run names its key under the LPETs' and the LGETs' copies and writes nothing;
the write puts it in the LPETs' T2 copy and the LGETs' copy unplaced, in no LPET, the row's other statements taking
its quote in its place alone, and Trajectories then takes its quote; the run's undo takes it back out of both. B: a
statement added by the app's save of the statements screen reaches the LPETs' copy the same way and its quote is
ticked as a Trajectories cell's key quote. C: a statement written past the copies, as before this build, is counted by
`copies refresh`'s dry run by participant and timepoint, keys alone, nothing written; the refresh adds it; and the
refresh run's undo takes it back out.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from . import support
from .a394_lipa_demo import as_cloned
from .support import check as said_check


def check(name, ok, detail=""):
    said_check(name, bool(ok), "" if ok else str(detail)[:700])


def test_copies_added(scratch: Path):
    print("\n401. A statement added by turn write or the app's save reaches the LPETs' and the LGETs' copies, unplaced, "
          "its quote one Trajectories takes, copies refresh adds one a copy lacks, and undo takes each back out "
          "(copiesadd, 16 November)")
    import agent_changes
    import agent_log
    import cli
    import gets as gets_mod
    import idiograph_routes as routes
    import make_demo_lipa as lipa
    import server as server_mod
    import themes
    import workbook as wb_mod

    fresh = scratch / "a401-clone"
    shutil.rmtree(fresh, ignore_errors=True)
    shutil.copytree(support.source("demo"), fresh, ignore=as_cloned)
    cfg_file = scratch / "a401-config.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "", "corpus": "", "gravity_reference": "",
                                    "corpus_exclude": []}), encoding="utf-8")
    log = scratch / "a401-agent-log.json"
    kept = (server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO, server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE,
            server_mod.STATE_PATH, server_mod.STATE_MEMORY, agent_changes.ALL_OPS, os.environ.get(agent_log.PLACE))

    def tree(at: Path) -> dict:
        return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*"))
                if p.is_file() and p.suffix != ".lock" and ".idiograph-restore" not in p.parts
                and p.name != "idiograph-agent-changes.jsonl"}

    def read(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    try:
        server_mod.DEMO_DIR = server_mod.SHIPPED_DEMO = fresh
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "a401-state.json", {"recent": []}
        agent_changes.ALL_OPS = None
        os.environ[agent_log.PLACE] = str(log)
        routes.fill_demo()
        # the demo filled as the server's start fills it, then copied out to a project of his own, since the demo
        # itself is fixed and keeps no restore points
        root = scratch / "a401" / "First year"
        shutil.rmtree(root.parent, ignore_errors=True)
        shutil.copytree(server_mod.demo_lipa_dir(), root, ignore=shutil.ignore_patterns("pristine", "source"))
        cfg_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "", "corpus": "",
                                        "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
        # agents allowed on it, as he allows them in Project settings
        project = root / server_mod.PROJECT_FILE
        project.write_text(json.dumps(dict(read(project), agents={"allowed": True, "at": "2026-11-16T09:00:00+00:00"})),
                           encoding="utf-8")
        case = lipa.CASES[0]
        book = root / case / f"{case} - EN & ES.xlsx"
        s2 = next(s for s, n in themes.placed_sheets(book).items() if n == 2)
        with themes.scoped(2):
            rows = list(dict.fromkeys(c["row"] for c in themes.read_cards(book)["cards"] if c["sheet"] == s2))
        lpfile, lgfile = gets_mod.lpets_path(book), root / "idiograph-lgets.json"

        def run(*args, as_json=True):
            code, text, err = cli.run(["--root", str(root), "--config", str(cfg_file), *args]
                                      + (["--json"] if as_json else []))
            if not as_json:
                return code, text, err
            return code, (support.plain(json.loads(text)) if text.strip() else {}), err + (text if code else "")

        def lpet_lines(tkey: str = "T2") -> dict:
            return read(lpfile)["cases"][tkey]["lines"]

        def lgets_lines() -> dict:
            return read(lgfile)["cases"][case]["lines"]

        def in_lpets(key: str) -> list[str]:
            """The LPETs on the participant's LPETs board holding the statement, by its own card."""
            board, _ = gets_mod.source_board(read(lpfile))
            return [g["id"] for g in board.get("groups") or []
                    if gets_mod.card_of("T2", "es", key) in (g.get("members") or [])]

        def shown(row: int) -> dict:
            code, said, err = run("turn", "show", case, s2, str(row))
            return said["turns"][0] if code == 0 else {}

        def pairs_with(turn: dict, statement: str, words: int) -> tuple[list[dict], str]:
            """The turn's pairs by key, and a new statement with a quote of the turn's own last words after them."""
            quote = " ".join(str(turn["text"]).split()[-words:])
            return ([{"statement": p["statement"], "quote": p["quote"], "key": p["key"]} for p in turn["pairs"]]
                    + [{"statement": statement, "quote": quote}]), quote

        code, traj, err = run("trajectories", "show")
        lpet = next(p for p in traj["participants"] if p["case"] == case)["rows"][0]["id"]

        def tick(key: str, dry: bool, run_id: str) -> tuple:
            ops = scratch / "a401-tick.json"
            ops.write_text(json.dumps([{"op": "quote", "participant": case, "lpet": lpet, "timepoint": "T2",
                                        "quote": key}]), encoding="utf-8")
            return run("trajectories", "apply", "--ops", str(ops), *(["--dry-run"] if dry else
                       ["--note", "Tick the new quote", "--tool", "Claude Code", "--run", run_id]))

        # ── A. turn write
        row_a = rows[0]
        turn = shown(row_a)
        pairs, quote = pairs_with(turn, "Finding a new rhythm on the plot", 6)
        new_a = themes.card_key(s2, row_a, len(turn["pairs"]))
        code, said, err = tick(new_a, True, "")
        check("401: before the write a Trajectories cell refuses the quote the statement will have, as it did",
              code != 0 and "is not a quote" in err, err)
        spec = scratch / "a401-write.json"
        spec.write_text(json.dumps({"pairs": pairs, "version": turn["version"],
                                    "request": "Add a statement at midsummer"}), encoding="utf-8")
        # a quote change the copy holds back on the row's first statement, as a requote waiting to be taken leaves it
        mate = themes.card_key(s2, row_a, 0)
        held_back = read(lpfile)
        held_back["cases"]["T2"]["lines"][mate]["quotes"][0] = "a quote the copy holds back"
        lpfile.write_text(json.dumps(held_back, ensure_ascii=False, indent=1), encoding="utf-8")
        whole = tree(root)
        code, dry, err = run("turn", "write", case, s2, str(row_a), "--from", str(spec), "--dry-run")
        followed = dry.get("copies_followed") or {}
        check("401: turn write's dry run names the new statement's key under the LPETs' and the LGETs' copies and "
              "writes nothing",
              code == 0 and (followed.get("lpets") or {}).get("added") == [new_a]
              and (followed.get("lgets") or {}).get("added") == [new_a] and tree(root) == whole, err or str(followed))
        lp_before, lg_before = lpfile.read_bytes(), lgfile.read_bytes()
        code, text, err = run("turn", "write", case, s2, str(row_a), "--from", str(spec), "--tool", "Claude Code",
                              "--run", "a401-write", as_json=False)
        lines, lg = lpet_lines(), lgets_lines()
        row_mates = [k for k in lines if themes.split_card_key(k)[:2] == (s2, row_a)]
        at = len(turn["pairs"])
        with themes.scoped(2):
            snap = gets_mod.snapshot(book)["lines"][new_a]
        check("401: the write puts the statement in the LPETs' T2 copy and the LGETs' copy, in no PET and in no LPET, "
              "its quote with it, as a full read of the workbook has it, and says so by key",
              code == 0 and new_a in lines and lines[new_a]["pet"] is None and not lines[new_a]["discarded"]
              and new_a in lg and not in_lpets(new_a) and len(row_mates) == at + 1
              and {k: v for k, v in lines[new_a].items() if k != "time"} == {k: v for k, v in snap.items()
                                                                            if k not in ("time", "span")}
              and lines[new_a]["time"] == lines[mate]["time"].split(", ")[0] + ", " + snap["time"]
              and themes.quote_words(lines[new_a]["quotes"][at]) == themes.quote_words(quote)
              and f"added 1 new, not placed ({new_a})" in text, err or text[-600:] + str(lines.get(new_a)) + str(snap))
        check("401: the row's other statements take the new quote in its own place alone, a quote the copy holds back "
              "kept as it was",
              lines[mate]["quotes"][0] == "a quote the copy holds back"
              and all(len(lines[k]["quotes"]) > at and lines[k]["quotes"][at] == lines[new_a]["quotes"][at]
                      for k in row_mates), str({k: lines[k]["quotes"] for k in row_mates})[:600])
        code, said, err = tick(new_a, True, "")
        check("401: Trajectories now takes the new statement's quote as the cell's key quote (its dry run)",
              code == 0, err)
        code, valid, err = run("validate")
        check("401: idiograph validate is clean after the write", code == 0, err)
        runs = [r for r in agent_changes.all_runs(root) if r.get("key") == "run:a401-write"]
        code, undone, err = run("agents", "undo-run", runs[0]["id"] if runs else "r0", "--note", "Take it back",
                                "--tool", "Claude Code")
        check("401: the write's undo takes the statement back out of the LPETs' and the LGETs' copies, both files as "
              "they were", code == 0 and new_a not in lpet_lines() and new_a not in lgets_lines()
              and lpfile.read_bytes() == lp_before and lgfile.read_bytes() == lg_before, err)

        # ── B. the app's save on the statements screen
        row_b = rows[1] if len(rows) > 1 else rows[0]
        turn = shown(row_b)
        pairs, quote = pairs_with(turn, "Keeping the plot going through the heat", 5)
        new_b = themes.card_key(s2, row_b, len(turn["pairs"]))
        body = {"path": str(book), "sheet": s2, "row": row_b, "v": turn["version"],
                "pairs": [{"es": p["statement"], "kq": p["quote"]} for p in pairs]}
        with routes.route_scope("/api/commit", body):
            saved = server_mod.ROUTES["/api/commit"](body)
        lines = lpet_lines()
        check("401: the app's save of a new statement puts it in the LPETs' T2 copy and the LGETs' copy, unplaced",
              "error" not in saved and new_b in lines and lines[new_b]["pet"] is None and new_b in lgets_lines()
              and not in_lpets(new_b), str(saved)[:400])
        code, said, err = tick(new_b, False, "a401-tick")
        code2, traj, err2 = run("trajectories", "show")
        cell = next(r for r in next(p for p in traj["participants"] if p["case"] == case)["rows"]
                    if r["id"] == lpet)["cells"]["T2"]
        check("401: and Trajectories ticks its quote as the cell's key quote",
              code == 0 and code2 == 0 and (cell.get("quote") or {}).get("key") == new_b and cell.get("chosen"),
              err or err2 or str(cell)[:400])

        # ── C. a statement written past the copies, as before this build: copies refresh catches up
        row_c = rows[2] if len(rows) > 2 else rows[-1]
        turn = shown(row_c)
        pairs, quote = pairs_with(turn, "Watering before the sun is up", 4)
        new_c = themes.card_key(s2, row_c, len(turn["pairs"]))
        wb_mod.save_turn(book, s2, row_c, None, None, None,
                         pairs=[{"es": p["statement"], "kq": p["quote"]} for p in pairs])
        check("401: a statement written past the copies stands in the workbook and in no copy",
              new_c in gets_mod.workbook_lines(book) and new_c not in lpet_lines() and new_c not in lgets_lines())
        whole = tree(root)
        code, dry, err = run("copies", "refresh", "--case", case, "--dry-run")
        files = {f["file"]: f for x in dry.get("participants") or [] if x["case"] == case for f in x["files"]}
        check("401: copies refresh's dry run counts it by participant and timepoint, keys alone, and writes nothing",
              code == 0 and dry.get("added") == 1
              and (files.get("lpets") or {}).get("added") == [{"case": "T2", "keys": [new_c]}]
              and (files.get("lgets") or {}).get("added") == [{"case": case, "keys": [new_c]}]
              and quote not in json.dumps(dry) and tree(root) == whole, err or json.dumps(dry)[:600])
        lp_before, lg_before = lpfile.read_bytes(), lgfile.read_bytes()
        code, done, err = run("copies", "refresh", "--case", case, "--note", "Catch the copies up",
                              "--tool", "Claude Code", "--run", "a401-refresh")
        lines = lpet_lines()
        check("401: the refresh adds it to the LPETs' T2 copy and the LGETs' copy, unplaced",
              code == 0 and done.get("added") == 1 and new_c in lines and lines[new_c]["pet"] is None
              and new_c in lgets_lines() and not in_lpets(new_c), err or json.dumps(done)[:500])
        code, again, err = run("copies", "refresh", "--case", case, "--dry-run")
        check("401: a second refresh finds nothing more to add", code == 0 and not again.get("added"), err)
        runs = [r for r in agent_changes.all_runs(root) if r.get("key") == "run:a401-refresh"]
        code, undone, err = run("agents", "undo-run", runs[0]["id"] if runs else "r0", "--note", "Take it back",
                                "--tool", "Claude Code")
        check("401: the refresh's undo takes it back out of both copies, both files as they were",
              code == 0 and new_c not in lpet_lines() and new_c not in lgets_lines()
              and lpfile.read_bytes() == lp_before and lgfile.read_bytes() == lg_before, err)

        # ── C2. a copy an old row op left behind takes nothing (copiesfix, 16 November 2026): a run of two passages
        # shifted, the copy holding the second's statements at the first's keys and the first's at keys the workbook
        # no longer holds, as a turn split before row ops followed the copies left it
        r1, r2 = rows[-2], rows[-1]
        gone_row = max(rows) + 1000
        lp_was, lg_was = lpfile.read_bytes(), lgfile.read_bytes()

        def shifted(lines: dict) -> dict:
            out = {}
            for k, v in lines.items():
                sheet, row, at = themes.split_card_key(k)
                if sheet == s2 and row == r1:
                    out[themes.card_key(s2, gone_row, at)] = dict(v, row=gone_row)
                elif sheet == s2 and row == r2:
                    out[themes.card_key(s2, r1, at)] = dict(v, row=r1)
                else:
                    out[k] = v
            return out

        for f, tkey in ((lpfile, "T2"), (lgfile, case)):
            data = read(f)
            data["cases"][tkey]["lines"] = shifted(data["cases"][tkey]["lines"])
            f.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        behind = sorted((k for k in lpet_lines() if themes.split_card_key(k)[1] == gone_row), key=themes._order)
        keys_lp, keys_lg = set(lpet_lines()), set(lgets_lines())
        whole = tree(root)
        code, dry, err = run("copies", "refresh", "--case", case, "--dry-run")
        files = {f["file"]: f for x in dry.get("participants") or [] if x["case"] == case for f in x["files"]}
        code2, said_text, err2 = run("copies", "refresh", "--case", case, "--dry-run", as_json=False)
        check("401: copies refresh's dry run adds nothing to a copy holding keys the workbook no longer holds, lists "
              "it by those keys and says to run copies rekey first, writing nothing",
              code == 0 and behind and not (files.get("lpets") or {}).get("added")
              and (files.get("lpets") or {}).get("rekey") == [{"case": "T2", "keys": [], "rekey": behind}]
              and not (files.get("lgets") or {}).get("added")
              and dry.get("rekey") and code2 == 0 and "copies rekey, then copies prune, then copies refresh" in said_text and tree(root) == whole,
              err or err2 or json.dumps(dry)[:700] + said_text[-400:])
        rspec = scratch / "a401-rekey.json"
        rturn = shown(rows[0])
        rspec.write_text(json.dumps({"pairs": [{"statement": p["statement"], "quote": p["quote"], "key": p["key"]}
                                               for p in rturn["pairs"]] + [{"statement": "Weeding in the rain",
                                                                            "quote": ""}],
                                     "version": rturn["version"], "request": "Add one"}), encoding="utf-8")
        code, wdry, err = run("turn", "write", case, s2, str(rows[0]), "--from", str(rspec), "--dry-run")
        followed = wdry.get("copies_followed") or {}
        check("401: turn write's dry run adds nothing to that copy and names its keys left behind",
              code == 0 and (followed.get("lpets") or {}).get("rekey") == behind
              and not (followed.get("lpets") or {}).get("added") and tree(root) == whole,
              err or str(followed)[:600])
        lp_held, lg_held = lpfile.read_bytes(), lgfile.read_bytes()
        code, text, err = run("turn", "write", case, s2, str(rows[0]), "--from", str(rspec), "--tool", "Claude Code",
                              "--run", "a401-rekey-write", as_json=False)
        check("401: the write itself leaves that copy as it was, the LPETs' and the LGETs' files byte for byte, and "
              "says to run copies rekey, then copies prune, then copies refresh",
              code == 0 and lpfile.read_bytes() == lp_held and lgfile.read_bytes() == lg_held
              and "copies rekey, then copies prune, then copies refresh" in text, err or text[-600:])
        code, done, err = run("copies", "refresh", "--case", case, "--note", "Catch the copies up",
                              "--tool", "Claude Code", "--run", "a401-rekey")
        files = {f["file"]: f for x in done.get("participants") or [] if x["case"] == case for f in x["files"]}
        check("401: the refresh adds nothing either, so no statement is copied twice, the copy listed the "
              "same as by the dry run, and the dry run's count of additions is the real run's",
              code == 0 and set(lpet_lines()) == keys_lp and set(lgets_lines()) == keys_lg
              and done.get("added") == dry.get("added") == 0
              and (files.get("lpets") or {}).get("rekey") == [{"case": "T2", "keys": [], "rekey": behind}],
              err or json.dumps(done)[:700])
        lpfile.write_bytes(lp_was)
        lgfile.write_bytes(lg_was)

        # ── D. a statement put in before the passage's first: the dry run names it at the first key
        row_d = rows[3] if len(rows) > 3 else rows[-1]
        turn = shown(row_d)
        spec = scratch / "a401-before.json"
        spec.write_text(json.dumps({"pairs": [{"statement": "Starting the day at the gate", "quote": " ".join(
            str(turn["text"]).split()[:4])}] + [{"statement": p["statement"], "quote": p["quote"], "key": p["key"]}
                                                for p in turn["pairs"]],
            "version": turn["version"], "request": "Add a statement first"}), encoding="utf-8")
        code, dry, err = run("turn", "write", case, s2, str(row_d), "--from", str(spec), "--dry-run")
        followed = dry.get("copies_followed") or {}
        first = themes.card_key(s2, row_d, 0)
        check("401: a statement put in before the passage's first is named at the first key by the dry run, the others "
              "moving one on",
              code == 0 and (followed.get("lpets") or {}).get("added") == [first]
              and (followed.get("lgets") or {}).get("added") == [first]
              and first in ((followed.get("lpets") or {}).get("moved") or []), err or str(followed)[:600])

        # ── E. an addition that cannot be read leaves what the write moved standing and said
        old = [p["statement"] for p in turn["pairs"]]
        new = ["Starting the day at the gate"] + old
        moves = themes.passage_lines(old, new)
        real_add = gets_mod.copies_added

        def unreadable(*args, **kwargs):
            raise wb_mod.WorkbookError("the workbook is open elsewhere")

        try:
            gets_mod.copies_added = unreadable
            with routes.writing(root=root):
                done = routes.passage_follow(book, s2, row_d, old, new, moves)
        finally:
            gets_mod.copies_added = real_add
        lines = lpet_lines()
        check("401: when the new statement cannot be read, the copies still move the passage's statements and say so, "
              "and the addition alone is reported as not made",
              (done.get("lpets") or {}).get("moved") and themes.card_key(s2, row_d, len(old)) in lines
              and first not in lines and done.get("failed")
              and all("does not hold it yet" in f for f in done["failed"]), str(done)[:600])

        # ── F. a thematic analysis project: refresh adds nothing, its GETs keeping a code's extracts by its code list
        ta = scratch / "a401-ta" / "Dogs coded"
        shutil.rmtree(ta.parent, ignore_errors=True)
        shutil.copytree(server_mod.demo_ta_dir(), ta, ignore=shutil.ignore_patterns("pristine", "source"))
        cfg_file.write_text(json.dumps({"projects": [{"root": str(root)}, {"root": str(ta)}], "interviewer": "",
                                        "corpus": "", "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
        tbook = sorted(ta.glob("*/*.xlsx"))[0]
        tcard = themes.read_cards(tbook)["cards"][0]
        twb = gets_mod.workbook_lines(tbook)
        held_es = [twb[k]["text"] for k in sorted(twb, key=themes._order)
                   if themes.split_card_key(k)[:2] == (tcard["sheet"], tcard["row"])]
        wb_mod.save_turn(tbook, tcard["sheet"], tcard["row"], "\n".join(held_es + ["Barking at the door"]), None, None)
        tkey = themes.card_key(tcard["sheet"], tcard["row"], len(held_es))
        would = gets_mod.copies_added(ta, tbook, dry=True)
        refreshed = routes.refresh_copies(tbook, dry=True)
        check("401: in a thematic analysis project copies refresh adds no extract to the GETs, which a project of IPA "
              "would take",
              (ta / "idiograph-gets.json").is_file() and tkey in gets_mod.workbook_lines(tbook)
              and any(tkey in w["keys"] for w in would)
              and not any(c.get("added") for c in refreshed["copies"].values()) and not refreshed["failed"],
              str(would)[:300] + str(refreshed)[:400])
    finally:
        (server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO, server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE,
         server_mod.STATE_PATH, server_mod.STATE_MEMORY, agent_changes.ALL_OPS) = kept[:7]
        if kept[7] is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = kept[7]
        agent_log.flush()
