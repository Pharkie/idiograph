from __future__ import annotations

import json
import shutil
from pathlib import Path

import openpyxl

import rounds as rounds_mod
import workbook as wb_mod

from . import support

from .support import DEMO_SHEET, add_second_sheet, check, demo_copy, demo_sheet, skip
import idiograph_routes


def blank_second_sheet(path: Path, name: str = "2d") -> Path:
    """The second sheet with every statement cleared, so nothing on it is decided until a check says."""
    add_second_sheet(path, name)
    book = openpyxl.load_workbook(path, rich_text=True)
    ws = book[name]
    for r in range(2, ws.max_row + 1):
        ws.cell(r, 3).value = None
    book.save(path)
    book.close()
    return path


def test_passed_and_bars(scratch):
    print("\n33. A turn moved past counts as decided, rounds close by themselves, and the two bars")
    import subprocess
    import server as server_mod

    # ── A. the passed state, derived sheet by sheet and never written
    work = blank_second_sheet(demo_copy(scratch, "passed", "Juno - EN & ES.xlsx"))
    case = wb_mod.read_case(work)
    _, her, him = demo_sheet(work)
    stops = {s["name"]: [r["row"] for r in s["rows"] if rounds_mod.is_stop(r, him)] for s in case["sheets"]}
    initial, second = stops[DEMO_SHEET], stops["2d"]
    filled = [r for s in case["sheets"] if s["name"] == DEMO_SHEET for r in s["rows"] if r["es"].strip()]
    head = max(r["row"] for r in filled)
    at = initial.index(head)
    skipped = initial[at + 4]             # three blank turns between the head start and this one
    progress = rounds_mod.load_progress(work)
    progress["rows"] = {f"{DEMO_SHEET}:{skipped}": "reviewed-empty"}
    progress["last"] = {"sheet": DEMO_SHEET, "row": skipped}
    states = rounds_mod.row_states(case["sheets"], progress, him)
    between = [f"{DEMO_SHEET}:{r}" for r in initial[at + 1:at + 4]]
    after = [f"{DEMO_SHEET}:{r}" for r in initial[at + 5:]]
    check("an unvisited turn before a decided one on its sheet is passed",
          all(states[k] == "passed" for k in between), f"{', '.join(between)}: {[states[k] for k in between]}")
    check("an unvisited turn after the furthest decided one is not",
          all(states[k] == "unvisited" for k in after), f"{len(after)} turns after {DEMO_SHEET}:{skipped}")
    check("the decided turns keep their own states",
          states[f"{DEMO_SHEET}:{skipped}"] == "reviewed-empty" and states[f"{DEMO_SHEET}:{head}"] == "has-content")
    check("a decision on one sheet passes nothing on the other",
          all(states[f"2d:{r}"] == "unvisited" for r in second), f"{len(second)} turns on the second sheet")

    progress["rows"][f"2d:{second[2]}"] = "reviewed-empty"
    states = rounds_mod.row_states(case["sheets"], progress, him)
    check("the second sheet passes its own turns before its own decision",
          [states[f"2d:{r}"] for r in second] == ["passed", "passed", "reviewed-empty", "unvisited", "unvisited"],
          str([states[f"2d:{r}"] for r in second]))
    check("and leaves the first sheet exactly as it was",
          all(states[k] == "passed" for k in between) and all(states[k] == "unvisited" for k in after))

    progress["last"] = {"sheet": DEMO_SHEET, "row": initial[at + 8]}
    states = rounds_mod.row_states(case["sheets"], progress, him)
    check("the last turn saved counts when it is further than any decided one",
          all(states[f"{DEMO_SHEET}:{r}"] == "passed" for r in initial[at + 5:at + 8])
          and states[f"{DEMO_SHEET}:{initial[at + 8]}"] == "unvisited"
          and states[f"{DEMO_SHEET}:{initial[at + 9]}"] == "unvisited",
          "the turns before it are passed, it and the ones after it are not")
    progress["last"] = {"sheet": "2d", "row": second[-1]}
    states = rounds_mod.row_states(case["sheets"], progress, him)
    check("a last turn on the other sheet passes nothing on this one",
          all(states[k] == "unvisited" for k in after)
          and [states[f"2d:{r}"] for r in second][:4] == ["passed", "passed", "reviewed-empty", "passed"])
    rounds_mod.save_progress(work, progress)
    on_disk = json.loads(rounds_mod.progress_path(work).read_text(encoding="utf-8"))
    check("passed is derived and never written", "passed" not in on_disk["rows"].values()
          and on_disk["rows"] == progress["rows"], f"{len(on_disk['rows'])} rows in the sidecar")

    # ── B. a round done through passed turns, and the summary
    progress["rows"] = {}
    progress["last"] = {"sheet": DEMO_SHEET, "row": head}
    rnds = rounds_mod.build_rounds(case["sheets"], 10, him)
    first = next(r for r in rnds if r["sheet"] == DEMO_SHEET)
    nxt = next(r for r in rnds if r["number"] == first["number"] + 1)
    before = rounds_mod.summary(case["sheets"], progress, rnds, him, 2)
    check("a round with blank turns after the last decided one is not done",
          first["number"] not in before["roundsDone"], str(before["roundsDone"]))
    progress["rows"][rounds_mod.row_key(*nxt["stops"][0])] = "reviewed-empty"
    s = rounds_mod.summary(case["sheets"], progress, rnds, him, 2)
    check("a decision in the next round passes the rest of the round before it, which is done",
          rounds_mod.round_done(first, s["states"]) and s["roundsDone"] == [first["number"]],
          f"round {first['number']}: {s['roundTurns'][0]}")
    total = sum(len(r["stops"]) for r in rnds)
    decided = len(first["stops"]) + 1
    check("the case line counts every participant turn and the decided ones",
          s["turnsTotal"] == total and s["turnsDone"] == decided,
          f"{s['turnsDone']} of {s['turnsTotal']} turns")
    tallies = {t["number"]: t for t in s["roundTurns"]}
    check("every round carries its decided and total turns",
          [t["number"] for t in s["roundTurns"]] == [r["number"] for r in rnds]
          and tallies[first["number"]]["decided"] == tallies[first["number"]]["total"] == len(first["stops"])
          and tallies[nxt["number"]]["decided"] == 1 and tallies[nxt["number"]]["total"] == len(nxt["stops"])
          and sum(t["decided"] for t in s["roundTurns"]) == s["turnsDone"],
          str([(t["number"], t["decided"], t["total"]) for t in s["roundTurns"]]))
    check("no round is recorded until the page records it",
          not any(t["recorded"] for t in s["roundTurns"]))
    # `flags` left the summary in 131: a page from before reads it with `|| []`, so its absence is safe
    old_keys = {"states", "roundsDone", "roundsTotal", "roundsLeft", "paceMinutes", "minutesLeft",
                "todayRounds", "dailyTarget", "streak"}
    check("every key a page loaded before this reads is still there", old_keys <= set(s),
          f"{len(old_keys)} keys kept, {len(set(s) - old_keys)} added")

    # ── C. the back-fill through the endpoint, and an open that writes nothing
    root = scratch / "backfill"
    saved_root, saved_state = server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH
    server_mod.ROOT_OVERRIDE = str(root)
    # the open remembers the case in the recent list, which goes to a scratch file here
    server_mod.STATE_PATH = scratch / "backfill-state.json"
    try:
        cfg = server_mod.config()
        fill = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
        fcase = wb_mod.read_case(fill)
        frnds = rounds_mod.build_rounds(fcase["sheets"], cfg["round_minutes"], cfg["interviewer"])
        one, two = frnds[0], frnds[1]
        fp = rounds_mod.load_progress(fill)
        fp["rows"] = {rounds_mod.row_key(*two["stops"][0]): "has-content"}
        fp["last"] = {"sheet": two["stops"][0][0], "row": two["stops"][0][1]}
        rounds_mod.save_progress(fill, fp)
        side = rounds_mod.progress_path(fill)
        raw, stamp = side.read_bytes(), side.stat().st_mtime_ns
        opened = idiograph_routes.api_open({"path": str(fill)})
        check("an open writes nothing to the sidecar",
              side.read_bytes() == raw and side.stat().st_mtime_ns == stamp,
              "the passed turns are worked out on the way to the page, not stored")
        check("and still answers with the passed turns and the round they close",
              one["number"] in opened["progress"]["roundsDone"]
              and "passed" in opened["progress"]["states"].values()
              and not opened["progress"]["roundTurns"][0]["recorded"],
              f"round {one['number']} done, not yet recorded")
        bare = demo_copy(root, "Bare", "Juno - EN & ES.xlsx")
        idiograph_routes.api_open({"path": str(bare)})
        check("an open with no sidecar creates none", not rounds_mod.progress_path(bare).exists())

        answer = idiograph_routes.api_round_complete({"path": str(fill), "round": one["number"]})
        after_side = json.loads(side.read_text(encoding="utf-8"))
        today = rounds_mod.today()
        completed = (after_side["rounds"].get(str(one["number"])) or {}).get("completed") or ""
        check("the back-fill records the round done through passed turns, dated today",
              answer["recorded"] and completed.startswith(today)
              and after_side["days"].get(today, {}).get("rounds") == 1,
              f"completed {completed}")
        check("and the answer says it is recorded, with today's count",
              answer["progress"]["roundTurns"][0]["recorded"] and answer["progress"]["todayRounds"] == 1)
        raw = side.read_bytes()
        again = idiograph_routes.api_round_complete({"path": str(fill), "round": one["number"]})
        check("a second call for the same round records nothing and writes nothing",
              not again["recorded"] and side.read_bytes() == raw and again["progress"]["todayRounds"] == 1)
        early = idiograph_routes.api_round_complete({"path": str(fill), "round": two["number"]})
        check("a round that is not done is left unrecorded",
              not early["recorded"] and side.read_bytes() == raw
              and early["progress"]["todayRounds"] == 1, f"round {two['number']}")
        check("the answer carries the progress the page redraws from",
              set(early["progress"]) >= old_keys | {"turnsDone", "turnsTotal", "roundTurns"})
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH = saved_root, saved_state

    # ── D. the two bars and the moves that close a round
    static = server_mod.HERE / "static"
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda name: js.split(f"function {name}(", 1)[1].split("\n}", 1)[0]
    check("every move closes the rounds left behind",
          fn("goTo").count("closeLeftRounds();") == 2 and "closeLeftRounds();" in fn("afterCommit")
          and "roundsToClose(row.round - 1)" in fn("closeLeftRounds"))
    check("a case opening closes every done and unrecorded round quietly",
          "closeRounds(roundsToClose(Infinity), { quiet: true });" in fn("startCase"))
    check("each round goes to the server once, oldest first, and the card shows the newest",
          "for (const n of todo)" in fn("closeRounds") and "'/api/round-complete'" in fn("closeRounds")
          and "S.closing" in fn("closeRounds") and "!r.recorded" in fn("roundsToClose")
          and "numbers[numbers.length - 1]" in fn("roundDone"))
    check("a save of a round's last turn still closes it at once and moves on from the card",
          "if (done && lastOfRound && !again && (roundsHere() || endsSheet(row.round))) { celebrate(row.round); return; }" in fn("afterCommit")
          and "{ advance: true }" in fn("celebrate") and "S.doneAdvance &&" in js)

    node = shutil.which("node")
    if not node:
        return skip("the bars' numbers in node", "no node on this machine")
    share_line = next(line for line in js.splitlines() if line.startswith("const share = "))
    source = "\n".join(["function barNumbers(" + fn("barNumbers") + "\n}",
                        "function roundsToClose(" + fn("roundsToClose") + "\n}", share_line])
    wire = [dict(r, stops=[{"sheet": a, "row": b} for a, b in r["stops"]]) for r in rnds]
    stale = {k: v for k, v in s.items() if k not in ("turnsDone", "turnsTotal", "roundTurns")}
    script = scratch / "bars-check.js"
    script.write_text(
        "const P = " + json.dumps(s) + ";\n"
        "const OLD = " + json.dumps(stale) + ";\n"
        "const R = " + json.dumps(wire) + ";\n"
        "const S = { data: { progress: P } };\n" + source + "\n"
        "const out = { now: barNumbers(P, R[1]), old: barNumbers(OLD, R[1]),\n"
        "  close: roundsToClose(Infinity), below: roundsToClose(" + str(first["number"] - 1) + "),\n"
        "  width: share(80, 108), none: share(0, 0) };\n"
        "S.data.progress = OLD; out.stale = roundsToClose(Infinity);\n"
        "console.log(JSON.stringify(out));\n", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("the bars' numbers run in node", False, run.stderr.strip()[:200])
    out = json.loads(run.stdout)
    want = {"caseDone": s["turnsDone"], "caseTotal": s["turnsTotal"], "roundDone": 1,
            "roundTotal": len(nxt["stops"])}
    check("the page's numbers are the summary's", out["now"] == want, str(out["now"]))
    check("a server that has not been restarted is answered from its states", out["old"] == want,
          str(out["old"]))
    check("the page closes the done and unrecorded round, and none below the first",
          out["close"] == [first["number"]] and out["below"] == [], f"{out['close']} {out['below']}")
    check("and closes nothing for a server that sends no round records", out["stale"] == [])
