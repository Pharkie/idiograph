from __future__ import annotations

import json
import shutil

import openpyxl

import rounds as rounds_mod
import workbook as wb_mod

from . import support
from .support import DEMO_SHEET, check, copied_second_sheet, demo_copy, demo_sheet, skip
import idiograph_routes


def test_sheet_rounds_and_confetti(scratch):
    print("\n58. Rounds belong to a sheet, with a sheet-done card at a sheet's end (142), and the confetti in three levels (141)")
    import subprocess
    import server as server_mod

    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda name: js.split(f"function {name}(", 1)[1].split("\n}", 1)[0]
    whole = lambda name: f"function {name}(" + fn(name) + "\n}"

    # ── A. on_sheet and the count of rounds on each sheet, on the demo's sheet copied as a second one
    root = scratch / "sheet-rounds"
    two = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    _, her, him = demo_sheet(two)
    copied_second_sheet(two)
    case = wb_mod.read_case(two)
    rnds = rounds_mod.build_rounds(case["sheets"], 10, him)
    names = [s["name"] for s in case["sheets"]]
    per = {n: [r for r in rnds if r["sheet"] == n] for n in names}
    check("142: the fixture has two sheets cut into the same rounds",
          names == [DEMO_SHEET, "2d"] and len(per[DEMO_SHEET]) == len(per["2d"]) >= 2,
          f"{len(per[DEMO_SHEET])} and {len(per['2d'])} rounds")
    check("142: number stays unique across the case, sheet by sheet",
          [r["number"] for r in rnds] == list(range(1, len(rnds) + 1)), str([r["number"] for r in rnds]))
    check("142: each round carries on_sheet, its 1-based place on its sheet",
          all([r["on_sheet"] for r in per[n]] == list(range(1, len(per[n]) + 1)) for n in names),
          str([(r["number"], r["on_sheet"]) for r in rnds]))
    check("142: each round carries the count of rounds on its sheet, and sheet_counts gives each sheet's",
          all(r["sheet_rounds"] == len(per[r["sheet"]]) for r in rnds)
          and rounds_mod.sheet_counts(rnds) == {n: len(per[n]) for n in names}
          and list(rounds_mod.sheet_counts(rnds)) == names)
    k = len(per[DEMO_SHEET])

    # ── B. the summary's per-sheet and per-case figures
    def stops_of(rounds):
        return [rounds_mod.row_key(*s) for r in rounds for s in r["stops"]]

    def summary_with(decided, paced=True):
        progress = rounds_mod.load_progress(two)
        progress["rows"] = {key: rounds_mod.REVIEWED_EMPTY for key in decided}
        if paced:
            progress["rounds"] = {"1": {"seconds": 600, "completed": "2026-10-03T10:00:00"}}
        return rounds_mod.summary(case["sheets"], progress, rnds, him, 2)

    mid = summary_with(stops_of(per[DEMO_SHEET][:1]))
    sheets_mid = {e["sheet"]: e for e in mid["sheetRounds"]}
    check("142: the summary carries every sheet's rounds, done, left and minutes left at the pace",
          [e["sheet"] for e in mid["sheetRounds"]] == names
          and sheets_mid[DEMO_SHEET] == {"sheet": DEMO_SHEET, "rounds": k, "done": 1, "left": k - 1,
                                         "minutesLeft": 10 * (k - 1)}
          and sheets_mid["2d"] == {"sheet": "2d", "rounds": k, "done": 0, "left": k, "minutesLeft": 10 * k},
          str(mid["sheetRounds"]))
    check("142: and for the case the sheets done, the sheets left and the minutes left for the rest",
          mid["sheetsDone"] == 0 and mid["sheetsLeft"] == 2 and mid["minutesLeft"] == 10 * (2 * k - 1)
          and mid["roundsDone"] == [1] and mid["roundsLeft"] == 2 * k - 1)
    first_done = summary_with(stops_of(per[DEMO_SHEET]))
    check("142: a sheet with every round done counts as a sheet done",
          first_done["sheetsDone"] == 1 and first_done["sheetsLeft"] == 1
          and first_done["sheetRounds"][0]["left"] == 0 and first_done["sheetRounds"][0]["minutesLeft"] == 0
          and first_done["minutesLeft"] == 10 * k)
    unpaced = summary_with(stops_of(per[DEMO_SHEET][:1]), paced=False)
    check("142: with no pace measured the minutes on a sheet are none, as the case's are",
          all(e["minutesLeft"] is None for e in unpaced["sheetRounds"]) and unpaced["minutesLeft"] is None)
    all_done = summary_with(stops_of(rnds))
    second_first = summary_with(stops_of(per["2d"]))

    saved = (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_PATH = scratch / "sheet-rounds-state.json"
    server_mod.STATE_MEMORY = None
    try:
        payload = idiograph_routes.case_payload(two)
        cfg = server_mod.config()
        counts = rounds_mod.sheet_counts(rounds_mod.build_rounds(case["sheets"], cfg["round_minutes"], cfg["interviewer"]))
        check("142: the case the server sends carries on_sheet on every round and each sheet's count",
              all(isinstance(r.get("on_sheet"), int) and isinstance(r.get("sheet_rounds"), int) for r in payload["rounds"])
              and [s.get("rounds") for s in payload["sheets"]] == [counts.get(n, 0) for n in names])
        check("142: and its summary carries the sheets' figures, as refresh_summary does",
              [e["sheet"] for e in payload["progress"]["sheetRounds"]] == names
              and "sheetsDone" in payload["progress"] and "sheetsLeft" in payload["progress"]
              and idiograph_routes.refresh_summary(two)["sheetRounds"] == payload["progress"]["sheetRounds"])

        # ── C. a progress file written before this reads without change
        old = demo_copy(root, "Old", "Juno - EN & ES.xlsx")
        copied_second_sheet(old)
        ornds = rounds_mod.build_rounds(wb_mod.read_case(old)["sheets"], cfg["round_minutes"], cfg["interviewer"])
        on_second = next(r for r in ornds if r["sheet"] == "2d")
        legacy = {"version": 1, "rows": {rounds_mod.row_key(*s): "reviewed-empty" for s in on_second["stops"]},
                  "rounds": {"1": {"seconds": 420, "completed": "2026-10-01T09:00:00"}},
                  "days": {"2026-10-01": {"rounds": 1}}, "last": {"sheet": "2d", "row": on_second["stops"][-1][1]}}
        side = rounds_mod.progress_path(old)
        side.parent.mkdir(parents=True, exist_ok=True)
        side.write_text(json.dumps(legacy, indent=1), encoding="utf-8")
        before = side.read_bytes()
        opened = idiograph_routes.case_payload(old)
        check("142: a progress file written before this reads without change",
              side.read_bytes() == before and opened["progress"]["roundsDone"] == [on_second["number"]]
              and opened["progress"]["paceMinutes"] == 7.0)
        answer = idiograph_routes.api_round_complete({"path": str(old), "round": on_second["number"]})
        after = json.loads(side.read_text(encoding="utf-8"))
        check("142: round-complete keeps the case-wide number as the key of the record",
              answer["recorded"] and str(on_second["number"]) in after["rounds"] and "1" in after["rounds"]
              and after["rounds"]["1"] == legacy["rounds"]["1"] and on_second["on_sheet"] == 1
              and on_second["number"] > 1, f"round {on_second['number']}, first on the 2d sheet")

        # ── savespeed (11 November 2026): a save's counts come from the workbook it has just written, exactly
        # what reading the file again gives, on two sheets with another speaker's turn, and the file is not read again
        quick = demo_copy(root, "Counts", "Juno - EN & ES.xlsx")
        copied_second_sheet(quick)
        book = openpyxl.load_workbook(quick, rich_text=True)
        ws = book["2d"]
        ctx = ws.max_column + 1
        ws.cell(1, ctx).value = wb_mod.CONTEXT_HEADER
        theirs = [r for r in range(2, ws.max_row + 1) if ws.cell(r, 1).value == her]
        ws.cell(theirs[1], ctx).value = "Beekeeper next door"
        wb_mod._atomic_save(book, quick)
        book.close()
        reads, kept = [], wb_mod.read_case
        steps = ({"sheet": "2d", "row": theirs[0], "es": "Watching the hive door at dawn", "en": "", "kq": ""},
                 {"sheet": DEMO_SHEET, "row": theirs[2]},
                 {"sheet": "2d", "row": theirs[0], "es": "", "en": "", "kq": ""})
        apart = []
        for body in steps:
            wb_mod.read_case = lambda *a, **k: reads.append(a) or kept(*a, **k)
            try:
                said = idiograph_routes.api_commit(dict(body, path=str(quick)))
            finally:
                wb_mod.read_case = kept
            fresh = idiograph_routes.refresh_summary(quick)
            if said["progress"] != fresh:
                apart.append({k: (said["progress"].get(k), fresh.get(k)) for k in fresh
                              if said["progress"].get(k) != fresh.get(k)})
        wb = openpyxl.load_workbook(quick, rich_text=True)
        outline = wb_mod.outline_of(wb)
        wb.close()
        keys = ("sheet", "row", "name", "seconds", "es", "context")
        read = [{"name": s["name"], "rows": [{k: r[k] for k in keys} for r in s["rows"]]}
                for s in wb_mod.read_case(quick)["sheets"]]
        check("savespeed: a statement saved, a passage skipped and a statement cleared each answer the counts a fresh "
              "read of the workbook gives, another speaker's turn among them, without reading the workbook again",
              not apart and not reads and outline == read and any(r["context"] for s in read for r in s["rows"]),
              f"{json.dumps(apart)[:600]} {len(reads)} reads")
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = saved

    # ── D. a single-sheet case reads exactly as it did
    one = demo_copy(root, "One", "Juno - EN & ES.xlsx")
    ocase = wb_mod.read_case(one)
    ornds = rounds_mod.build_rounds(ocase["sheets"], 10, him)
    oprog = rounds_mod.load_progress(one)
    oprog["rows"] = {rounds_mod.row_key(*s): "reviewed-empty" for s in ornds[0]["stops"]}
    oprog["rounds"] = {"1": {"seconds": 600, "completed": "2026-10-03T10:00:00"}}
    single = rounds_mod.summary(ocase["sheets"], oprog, ornds, him, 2)
    check("142: on a single sheet on_sheet is the number and the sheet's count the case's",
          all(r["on_sheet"] == r["number"] and r["sheet_rounds"] == len(ornds) for r in ornds)
          and len(single["sheetRounds"]) == 1
          and single["sheetRounds"][0]["done"] == len(single["roundsDone"])
          and single["sheetRounds"][0]["left"] == single["roundsLeft"]
          and single["sheetRounds"][0]["minutesLeft"] == single["minutesLeft"])

    # ── E. the page: the bar, the round-done card, the sheet-done card and the case-complete card
    check("142: Next sheet goes the way the switcher goes, Enter presses it and Esc is Take a break",
          "toSheet(name)" in fn("nextSheet") and "$('done-sheet').onclick = () => nextSheet();" in js
          and "$('done-stop').onclick = () => stopHere();" in js
          and "if (!$('round-done').hidden && !$('done-sheet').hidden && e.key === 'Enter' && !MOD(e)) {\n      e.preventDefault(); nextSheet(); return;" in support.keydown_text(js)
          and "if (!$('round-done').hidden && !$('done-sheet').hidden) { e.preventDefault(); stopHere(); return true; }" in js)

    node = shutil.which("node")
    if not node:
        return skip("the cards and the confetti in node", "no node on this machine")
    lines_src = js.split("const LINES = [", 1)[1].split("];", 1)[0]
    months = support.i18n_js()
    day_line = next(line for line in js.splitlines() if line.startswith("const dayOf = "))
    wire = lambda rounds: [dict(r, rows=[{"sheet": a, "row": b} for a, b in r["rows"]],
                                stops=[{"sheet": a, "row": b} for a, b in r["stops"]]) for r in rounds]
    stale_rounds = [{k2: v for k2, v in r.items() if k2 not in ("on_sheet", "sheet_rounds")} for r in wire(rnds)]
    stale = {k2: v for k2, v in mid.items() if k2 not in ("sheetRounds", "sheetsDone", "sheetsLeft")}
    source = "\n".join([months, "const LINES = [" + lines_src + "];", whole("whenOf"), day_line]
                       + [ln for ln in js.splitlines() if ln.startswith(("function roundsOn(", "function roundsHere("))]
                       + [whole("drawDoneMark"), whole("formatMinutes"), whole("roundDone"), whole("nextSheet"),
                          whole("stopHere"), whole("roundPlace")])
    script = scratch / "sheet-cards.js"
    script.write_text(
        "const els = {};\n"
        "const $ = (id) => els[id] || (els[id] = { textContent: '', hidden: false, title: '',\n"
        "  classList: { on: new Set(), toggle(c, v) { if (v) this.on.add(c); else this.on.delete(c); } } });\n"
        "const S = { data: { progress: null, rounds: null, config: { work_in_rounds: true } } };\n"
        "const fired = []; const confetti = (level) => fired.push(level === undefined ? 1 : level);\n"
        "const show = (id) => { $(id).hidden = false; }; const hide = (id) => { $(id).hidden = true; };\n"
        "const said = []; const say = (t) => said.push(t); const focusEntry = () => {};\n"
        "const haulShow = () => {};\n"
        "const went = []; const toSheet = (name) => { went.push(name); return Promise.resolve(); };\n"
        + source + "\n"
        "const view = () => ({ kicker: $('done-kicker').textContent, line: $('done-line').textContent,\n"
        "  countLabel: $('done-count-label').textContent, leftLabel: $('done-left-label').textContent,\n"
        "  count: String($('done-count').textContent), left: String($('done-left').textContent),\n"
        "  eta: $('done-eta').textContent, etaHidden: $('done-eta-box').hidden, two: $('done-figures').classList.on.has('two'),\n"
        "  then: $('done-then').textContent, thenHidden: $('done-then').hidden, daily: $('done-daily').textContent,\n"
        "  next: $('done-next').hidden, sheet: $('done-sheet').hidden, library: $('done-library').hidden,\n"
        "  level: fired[fired.length - 1], nextSheet: S.nextSheet, doneSheet: S.doneSheet });\n"
        "const card = (rounds, progress, numbers) => { S.data.rounds = rounds; S.data.progress = progress;\n"
        "  roundDone(numbers, true); return view(); };\n"
        "const R = " + json.dumps(wire(rnds)) + ";\n"
        "const OLD_R = " + json.dumps(stale_rounds) + ";\n"
        "const ONE = " + json.dumps(wire(ornds)) + ";\n"
        "const out = {\n"
        "  mid: card(R, " + json.dumps(mid) + ", [1]),\n"
        "  sheet: card(R, " + json.dumps(first_done) + ", [" + str(k) + "]),\n"
        "  onSecond: card(R, " + json.dumps(summary_with(stops_of(per[DEMO_SHEET]) + stops_of(per["2d"][:1]))) + ", [" + str(k + 1) + "]),\n"
        "  wrap: card(R, " + json.dumps(second_first) + ", [" + str(2 * k) + "]),\n"
        "  finished: card(R, " + json.dumps(all_done) + ", [" + str(2 * k) + "]),\n"
        "  stale: card(OLD_R, " + json.dumps(stale) + ", [1]),\n"
        "  single: card(ONE, " + json.dumps(single) + ", [1]),\n"
        "};\n"
        "card(R, " + json.dumps(first_done) + ", [" + str(k) + "]); stopHere(); out.stopSheet = said[said.length - 1];\n"
        "card(R, " + json.dumps(mid) + ", [1]); stopHere(); out.stopRound = said[said.length - 1];\n"
        "card(R, " + json.dumps(first_done) + ", [" + str(k) + "]);\n"
        "nextSheet().then(() => {\n"
        "  out.went = went; out.hiddenAfter = $('round-done').hidden;\n"
        "  S.data.rounds = R; out.bar = [R[0], R[" + str(k) + "], R[" + str(2 * k - 1) + "]].map((r) => roundPlace({ round: r.number }, r));\n"
        "  S.data.rounds = ONE; out.barOne = roundPlace({ round: 1 }, ONE[0]);\n"
        "  S.data.rounds = OLD_R; out.barOld = roundPlace({ round: " + str(k + 1) + " }, OLD_R[" + str(k) + "]);\n"
        "  console.log(JSON.stringify(out));\n"
        "});\n", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("the cards run in node", False, run.stderr.strip()[:300])
    out = json.loads(run.stdout)
    m = out["mid"]
    check("142: the round-done card counts the sheet, rounds done and left on it and its time at the pace",
          m["countLabel"] == "Rounds done" and m["leftLabel"] == "Left on this sheet" and m["count"] == "1"
          and m["left"] == str(k - 1) and m["eta"] == f"{10 * (k - 1)} min" and m["kicker"] == "Round 1 done",
          str(m))
    s = out["sheet"]
    check("142: its figures are the rounds on the sheet, the sheets left and the time on the rest of the case",
          s["countLabel"] == "Rounds on this sheet" and s["count"] == str(k) and s["leftLabel"] == "Sheets left"
          and s["left"] == "1" and s["eta"] == f"{10 * k} min" and not s["etaHidden"] and not s["two"]
          and s["thenHidden"], str(s))
    check("142, 153: Next sheet hides the card and goes to the next sheet, and Take a break says the next is there when he is ready",
          out["went"] == ["2d"] and out["hiddenAfter"] is True
          and out["stopSheet"] == "A break at the end of a sheet. The next sheet is here when you are ready."
          and out["stopRound"] == "A break at a round end. The next round is here when you are ready.")
    o = out["onSecond"]
    check("142: on the next sheet the kicker is the sheet's own round and no line names a sheet done before",
          o["kicker"] == "Round 1 done" and o["count"] == "1" and o["left"] == str(k - 1) and o["thenHidden"]
          and o["level"] == 1, str(o))
    w = out["wrap"]
    check("142: a second sheet finished first points back to the first",
          w["line"] == f"The {DEMO_SHEET} sheet is next." and w["nextSheet"] == DEMO_SHEET
          and w["level"] == 2 and w["kicker"] == "2d sheet done", str(w))
    f = out["finished"]
    check("141: the case-complete path is level 3, its card as it was",
          f["level"] == 3 and f["line"] == "Participant complete." and f["kicker"] == f"Round {k} done"
          and f["countLabel"] == "Rounds done" and f["leftLabel"] == "Left for this participant"
          and f["count"] == str(2 * k) and f["left"] == "0" and f["etaHidden"] and f["two"]
          and f["next"] and f["sheet"] and not f["library"] and f["thenHidden"], str(f))
    st = out["stale"]
    check("142: a page in front of a server from before this draws the card as it always did",
          st["countLabel"] == "Rounds done" and st["leftLabel"] == "Left for this participant" and st["count"] == "1"
          and st["left"] == str(2 * k - 1) and st["eta"] == f"{10 * (2 * k - 1)} min" and st["thenHidden"]
          and st["level"] == 1 and st["kicker"] == "Round 1 done", str(st))
    one_view = out["single"]
    check("142: a single-sheet case reads exactly as it did, every number and every line",
          one_view["countLabel"] == "Rounds done" and one_view["leftLabel"] == "Left for this participant"
          and one_view["count"] == str(len(single["roundsDone"])) and one_view["left"] == str(single["roundsLeft"])
          and one_view["eta"] == f"{single['minutesLeft']} min" and one_view["thenHidden"]
          and one_view["kicker"] == "Round 1 done" and one_view["level"] == 1 and not one_view["next"]
          and one_view["sheet"], str(one_view))
    check("142: the bar numbers each sheet's rounds, with the case's in the tooltip",
          out["bar"] == [{"on": 1, "of": k, "title": f"round 1 of {2 * k} for this participant"},
                         {"on": 1, "of": k, "title": f"round {k + 1} of {2 * k} for this participant"},
                         {"on": k, "of": k, "title": f"round {2 * k} of {2 * k} for this participant"}], str(out["bar"]))
    check("142: a single sheet's bar is the case's numbers with no tooltip, and a server from before reads as before",
          out["barOne"] == {"on": 1, "of": len(ornds), "title": ""}
          and out["barOld"] == {"on": k + 1, "of": 2 * k, "title": ""}, f"{out['barOne']} {out['barOld']}")

    # ── F. the confetti: three levels, the cannons, and one canvas run
    consts = "const CONFETTI_LEVELS = {" + js.split("const CONFETTI_LEVELS = {", 1)[1].split("function confetti(level", 1)[0]
    script = scratch / "confetti-run.js"
    script.write_text(
        "let now = 1000; const performance = { now: () => now };\n"
        "let frames = []; const requestAnimationFrame = (cb) => { frames.push(cb); return frames.length; };\n"
        "const cancelAnimationFrame = () => {};\n"
        "let reduce = false; let innerWidth = 1200; let innerHeight = 800;\n"
        "const on = { window: {}, document: {} };\n"
        "const window = { devicePixelRatio: 2, matchMedia: () => ({ matches: reduce }),\n"
        "  addEventListener: (t, f) => { on.window[t] = f; }, removeEventListener: (t) => { delete on.window[t]; } };\n"
        "let cardUp = null;\n"
        "const document = { hidden: false, querySelector: () => cardUp,\n"
        "  addEventListener: (t, f) => { on.document[t] = f; }, removeEventListener: (t) => { delete on.document[t]; } };\n"
        "const ctx = { fills: 0, clips: [], setTransform() {}, clearRect() {}, save() {}, restore() {}, beginPath() {},\n"
        "  rect() {}, clip(rule) { this.clips.push(rule); }, fillRect() { this.fills += 1; } };\n"
        "const canvas = { width: 0, height: 0, style: {}, getContext: () => ctx,\n"
        "  classList: { set: new Set(), add(c) { this.set.add(c); }, remove(c) { this.set.delete(c); } } };\n"
        "let touched = 0; const $ = () => { touched += 1; return canvas; };\n"
        + "const FAMILY_APPS = {};\n" + support.distil_hooks(js) + consts + "\n" + whole("confetti") + "\n"
        "const step = (count) => { let most = 0; let n = 0;\n"
        "  while (frames.length && n < count) { const cb = frames.shift(); now += 1000 / 60; ctx.fills = 0; cb(now);\n"
        "    most = Math.max(most, ctx.fills); n += 1; }\n"
        "  return { most, n }; };\n"
        "const out = {};\n"
        "out.plans = [undefined, 1, 2, 3, 7].map((l) => confettiPlan(l, 1200, 800));\n"
        "out.alive = CONFETTI_ALIVE;\n"
        "for (const level of [1, 2, 3]) {\n"
        "  frames = []; ctx.clips = []; cardUp = null;\n"
        "  confetti(level); out['on' + level] = canvas.classList.set.has('on');\n"
        "  const ran = step(100000);\n"
        "  out['run' + level] = { frames: ran.n, most: ran.most, off: !canvas.classList.set.has('on'), size: [canvas.width, canvas.height] };\n"
        "}\n"
        "// a window too big for any piece to leave counts every piece thrown, up to the cap\n"
        "innerWidth = 1e7; innerHeight = 1e7;\n"
        "for (const level of [1, 2, 3]) { frames = []; confetti(level); out['thrown' + level] = step(100000).most; }\n"
        "innerWidth = 1200; innerHeight = 800;\n"
        "// a card on screen keeps its words clear, a resize mid-run sizes the canvas again\n"
        "frames = []; ctx.clips = []; cardUp = { getBoundingClientRect: () => ({ left: 320, top: 200, width: 560, height: 400 }) };\n"
        "confetti(1); step(30); innerWidth = 900; innerHeight = 700; on.window.resize(); step(1);\n"
        "out.card = { clips: ctx.clips.length, rule: ctx.clips[0], resized: [canvas.width, canvas.height] };\n"
        "innerWidth = 1200; innerHeight = 800; cardUp = null;\n"
        "// a level fired while one runs replaces it, and the old loop draws nothing more\n"
        "frames = []; confetti(1); step(30); const old = frames.slice(); frames = []; confetti(3);\n"
        "ctx.fills = 0; old.forEach((cb) => cb(now)); out.replaced = { oldDrew: ctx.fills, on: canvas.classList.set.has('on'), queued: frames.length };\n"
        "// a hidden tab ends the run quietly\n"
        "document.hidden = true; on.document.visibilitychange(); document.hidden = false;\n"
        "out.hidden = { off: !canvas.classList.set.has('on'), listeners: Object.keys(on.window).length + Object.keys(on.document).length };\n"
        "ctx.fills = 0; frames.forEach((cb) => cb(now)); out.hidden.drew = ctx.fills;\n"
        "// reduced motion draws nothing at all\n"
        "reduce = true; frames = []; touched = 0; ctx.fills = 0; confetti(3); step(100);\n"
        "out.reduced = { touched, fills: ctx.fills, frames: frames.length };\n"
        "console.log(JSON.stringify(out));\n", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("the confetti runs in node", False, run.stderr.strip()[:300])
    out = json.loads(run.stdout)

    check("141: reduced motion still draws nothing",
          out["reduced"] == {"touched": 0, "fills": 0, "frames": 0}
          and fn("confetti").index("prefers-reduced-motion: reduce") < fn("confetti").index("$('confetti')"),
          str(out["reduced"]))
