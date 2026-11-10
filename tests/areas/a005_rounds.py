from __future__ import annotations

import rounds as rounds_mod
import workbook as wb_mod

from .support import DEMO_WORKBOOK, REFERENCE_WORKBOOK, check, demo_sheet, skip


def test_rounds():
    print("\n4. Rounds")
    sheet, her, him = demo_sheet(DEMO_WORKBOOK)
    rnds = rounds_mod.build_rounds([sheet], 10, him)
    turns = len([r for r in sheet["rows"] if r["name"] == her])
    stops = sum(len(r["stops"]) for r in rnds)
    check("twenty two transcript-minutes come out as three rounds", len(rnds) == 3, f"{len(rnds)} rounds")
    check("every participant turn is a stop and nobody else's is", stops == turns,
          f"{stops} stops over {turns} of her turns")
    rows = sum(len(r["rows"]) for r in rnds)
    check("every row of the demo lands in exactly one round", rows == len(sheet["rows"]),
          f"{rows} rows over {len(sheet['rows'])}")
    seen = [k for r in rnds for k in r["rows"]]
    check("no demo turn is split or repeated", len(seen) == len(set(seen)))
    check("the rounds are numbered from one",
          [r["number"] for r in rnds] == list(range(1, len(rnds) + 1)), str([r["number"] for r in rnds]))
    print(f"        rounds: {[(rounds_mod_mmss(r['from']), rounds_mod_mmss(r['to']), len(r['stops'])) for r in rnds]}")

    # The reference workbook is three sheets and twice the length, which is what it adds here.
    if not REFERENCE_WORKBOOK.exists():
        return skip("rounds over three sheets", "no reference workbook under Main Data")
    case = wb_mod.read_case(REFERENCE_WORKBOOK)
    initial = [s for s in case["sheets"] if s["name"] == "Initial"]
    rnds = rounds_mod.build_rounds(initial, 10, "Adam")
    check("four rounds on Initial", len(rnds) == 4, f"{len(rnds)} rounds")
    stops = sum(len(r["stops"]) for r in rnds)
    check("123 participant turns, all of them stops", stops == 123, f"{stops} stops")
    rows = sum(len(r["rows"]) for r in rnds)
    check("every row lands in exactly one round", rows == len(initial[0]["rows"]),
          f"{rows} rows over {len(initial[0]['rows'])}")
    seen = [k for r in rnds for k in r["rows"]]
    check("no turn is split or repeated", len(seen) == len(set(seen)))
    spans = [(rounds_mod_mmss(r['from']), rounds_mod_mmss(r['to']), len(r['stops'])) for r in rnds]
    print(f"        rounds: {spans}")
    whole = rounds_mod.build_rounds(case["sheets"], 10, "Adam")
    check("rounds numbered across the whole case",
          [r["number"] for r in whole] == list(range(1, len(whole) + 1)), f"{len(whole)} rounds over 3 sheets")
    sheets_per_round = {r["number"]: r["sheet"] for r in whole}
    check("a round never spans two sheets", len(set(sheets_per_round.values())) == 3)

    two_in_a_row = [s for s in case["sheets"] if s["name"] == "2d"][0]["rows"]
    pairs = [(a, b) for a, b in zip(two_in_a_row, two_in_a_row[1:])
             if a["name"] == b["name"] != "Adam"]
    check("two participant turns in a row are two stops", len(pairs) > 0,
          f"{len(pairs)} such pairs on the 2d sheet, each counted separately")


def rounds_mod_mmss(seconds):
    return wb_mod.timecode(seconds, "75:12")
