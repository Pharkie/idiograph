from __future__ import annotations

import rounds as rounds_mod
import workbook as wb_mod

from .support import DEMO_WORKBOOK, check, compare_workbooks, demo_copy, demo_sheet


def test_progress(scratch):
    print("\n9. Progress, pace and the daily target")
    work = demo_copy(scratch, "progress", "Juno - EN & ES.xlsx")
    check("sidecar path is in the Working folder",
          rounds_mod.progress_path(work) == work.parent / "Working" / "Juno - EN & ES.progress.json",
          rounds_mod.progress_path(work).name)
    case = wb_mod.read_case(work)
    sheet, _, him = demo_sheet(work)
    filled = sum(1 for r in sheet["rows"] if r["es"].strip())
    progress = rounds_mod.load_progress(work)
    rnds = rounds_mod.build_rounds(case["sheets"], 10, him)
    summary = rounds_mod.summary(case["sheets"], progress, rnds, him, 2)
    check("statements already in the workbook count as done",
          sum(1 for v in summary["states"].values() if v == "has-content") == filled,
          f"{sum(1 for v in summary['states'].values() if v == 'has-content')} rows with content")
    check("pace is silent until a round is finished", summary["paceMinutes"] is None)

    import time
    now = time.time()
    rounds_mod.record_work(progress, 1, now)
    rounds_mod.record_work(progress, 1, now + 120)
    rounds_mod.record_work(progress, 1, now + 100000)      # a break, not work
    check("a long gap does not count toward the pace", progress["rounds"]["1"]["seconds"] == 120,
          f"{progress['rounds']['1']['seconds']} seconds measured")

    # the window he left is not work either: the browser counts those seconds and sends them
    away = {"version": 1, "rows": {}, "rounds": {}, "days": {}, "last": None, "flags": []}
    start = 1000.0
    rounds_mod.record_work(away, 2, start)
    rounds_mod.record_work(away, 2, start + 200, away=80)
    check("time away is taken off the gap", away["rounds"]["2"]["seconds"] == 120,
          f"{away['rounds']['2']['seconds']} seconds from a 200 second gap with 80 away")
    rounds_mod.record_work(away, 2, start + 260, away=60)
    check("a gap entirely spent away adds nothing", away["rounds"]["2"]["seconds"] == 120,
          f"{away['rounds']['2']['seconds']} seconds after a 60 second gap, 60 away")
    rounds_mod.record_work(away, 2, start + 320, away=400)
    check("more away than gap never goes backwards", away["rounds"]["2"]["seconds"] == 120,
          f"{away['rounds']['2']['seconds']} seconds")
    rounds_mod.record_work(away, 2, start + 900, away=400)
    check("away can bring a long gap back under the cap", away["rounds"]["2"]["seconds"] == 300,
          f"{away['rounds']['2']['seconds']} seconds from a 580 second gap with 400 away")
    rounds_mod.complete_round(progress, 1)
    check("the day tally goes up once", progress["days"][rounds_mod.today()]["rounds"] == 1)
    rounds_mod.complete_round(progress, 1)
    check("finishing the same round again does not count twice",
          progress["days"][rounds_mod.today()]["rounds"] == 1)
    check("pace now reported", rounds_mod.pace_minutes(progress) == 2.0, f"{rounds_mod.pace_minutes(progress)} min")
    rounds_mod.save_progress(work, progress)
    check("sidecar written and read back",
          rounds_mod.load_progress(work)["rounds"]["1"]["seconds"] == 120)
    check("nothing about progress is written into the workbook",
          not compare_workbooks(DEMO_WORKBOOK, work, allowed=set())[0],
          "the sidecar JSON is the only thing written")
