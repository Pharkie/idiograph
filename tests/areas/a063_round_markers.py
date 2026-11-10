from __future__ import annotations

import json
import shutil

import rounds as rounds_mod
import workbook as wb_mod

from . import support
from .support import DEMO_SHEET, check, copied_second_sheet, demo_copy, demo_sheet, skip


def test_round_markers(scratch):
    print("\n63. Round markers in the transcript (155), the clock made a round clock (156), and the count flashed "
          "on every step (157)")
    import subprocess

    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda name: js.split(f"function {name}(", 1)[1].split("\n}", 1)[0]
    whole = lambda name: f"function {name}(" + fn(name) + "\n}"

    # ── C. the fixture: the demo's sheet and a second sheet, as the server sends them
    root = scratch / "round-markers"
    two = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    _, her, him = demo_sheet(two)
    copied_second_sheet(two)
    case = wb_mod.read_case(two)
    rnds = rounds_mod.build_rounds(case["sheets"], 10, him)
    wire = [dict(r, rows=[{"sheet": a, "row": b} for a, b in r["rows"]],
                 stops=[{"sheet": a, "row": b} for a, b in r["stops"]]) for r in rnds]
    on_first = [r for r in rnds if r["sheet"] == DEMO_SHEET]
    k = len(on_first)

    def summary_with(decided):
        progress = rounds_mod.load_progress(two)
        progress["rows"] = {key: rounds_mod.REVIEWED_EMPTY for key in decided}
        return rounds_mod.summary(case["sheets"], progress, rnds, him, 2)

    keys = lambda r: [rounds_mod.row_key(*s) for s in r["stops"]]
    fresh = summary_with([])
    first_done = summary_with(keys(on_first[0]))
    second_part = summary_with(keys(on_first[0]) + keys(on_first[1])[:2])
    all_first = summary_with([key for r in on_first for key in keys(r)])
    rows_of = {r["number"]: [x for s in case["sheets"] for x in s["rows"] if (x["sheet"], x["row"]) in set(r["rows"])]
               for r in rnds}

    def tip(number, go):
        rows = rows_of[number]
        timed = [x for x in rows if x["time"]]
        rnd = next(r for r in rnds if r["number"] == number)
        n = len(rnd["stops"])
        return (f"Round {rnd['on_sheet']}, {n} passage{'' if n == 1 else 's'}, {timed[0]['time']} to {timed[-1]['time']}."
                + (f" Go to its first {go}passage." if n else ""))

    node = shutil.which("node")
    if not node:
        return skip("155 to 157: the markers, the clock and the count in node", "no node on this machine")

    # ── D. the markers in node: placement, the three states, the tooltip and the click target
    tick = next(line for line in js.splitlines() if line.startswith("const MARK_TICK = "))
    words = next(line for line in js.splitlines() if line.startswith("const MARK_WORDS = "))
    source = "\n".join([tick, words] + [ln for ln in js.splitlines() if ln.startswith(("function roundsOn(", "function roundsHere("))]
                       + [whole(n) for n in ("sheetRound", "clockTitle", "roundMarkHtml", "roundMarkState", "roundTarget",
                                             "drawRoundMarks", "toRound", "drawTranscript")])
    script = scratch / "round-markers.js"
    script.write_text(support.i18n_js() +
        "const box = { innerHTML: '', marks: [], querySelectorAll() { return this.marks; } };\n"
        "const $ = (id) => box;\n"
        "const esc = (s) => String(s);\n"
        "const turnHtml = (row) => `<article class=\"turn\" data-i=\"${row.i}\"></article>`;\n"
        "const drawSheetLabel = () => {};\n"
        "const parkNotes = () => {}; const parkCard = () => {}; const parkNote = () => {};\n"
        "const drawDoneMarks = () => {};\n"
        "const went = []; const goTo = (...a) => { went.push(a); return Promise.resolve(); };\n"
        "const cued = []; const cueAudio = (s) => cued.push(s);\n"
        "const SHEETS = " + json.dumps(case["sheets"]) + ";\n"
        "const S = { data: null, flat: [], stops: [], at: 0 };\n"
        "const current = () => S.flat[S.stops[S.at]];\n"
        "function open(rounds, progress) {\n"
        "  S.data = { rounds, progress, config: { work_in_rounds: true } }; S.flat = []; S.stops = [];\n"
        "  for (const sheet of SHEETS) for (const row of sheet.rows) S.flat.push(Object.assign({}, row));\n"
        "  const roundOf = {};\n"
        "  for (const r of rounds) for (const k of r.rows) roundOf[`${k.sheet}:${k.row}`] = r.number;\n"
        "  S.flat.forEach((row, i) => { row.i = i; row.key = `${row.sheet}:${row.row}`; row.round = roundOf[row.key]; });\n"
        "  for (const row of S.flat) { row.stop = !!(row.name && row.name.trim().toLowerCase() !== " + json.dumps(him.lower()) + ");\n"
        "    if (row.stop) { row.pos = S.stops.length; S.stops.push(row.i); } }\n"
        "}\n"
        "const order = (html) => [...html.matchAll(/data-round=\"(\\d+)\"|data-i=\"(\\d+)\"/g)]\n"
        "  .map((m) => (m[1] ? 'm' + m[1] : Number(m[2])));\n"
        "const labels = (html) => [...html.matchAll(/<span class=\"round-mark-name\">([^<]+)<\\/span>/g)].map((m) => m[1]);\n"
        "function fakeMarks(html) {\n"
        "  box.marks = [...html.matchAll(/data-round=\"(\\d+)\"/g)].map((m) => {\n"
        "    const word = { textContent: '' };\n"
        "    const set = new Set(['round-mark']);\n"
        "    return { dataset: { round: m[1] }, title: '', word,\n"
        "      classList: { set, contains: (c) => set.has(c), add: (c) => set.add(c), remove: (...c) => c.forEach((x) => set.delete(x)) },\n"
        "      querySelector: (sel) => (sel === '.round-mark-word' ? word : null) };\n"
        "  });\n"
        "}\n"
        "const states = () => box.marks.map((m) => [Number(m.dataset.round), [...m.classList.set].filter((c) => c !== 'round-mark').join(' '), m.word.textContent]);\n"
        + source + "\n"
        "const R = " + json.dumps(wire) + ";\n"
        "const out = {};\n"
        "open(R, " + json.dumps(fresh) + ");\n"
        "drawTranscript(" + json.dumps(DEMO_SHEET) + "); out.order = order(box.innerHTML); out.labels = labels(box.innerHTML);\n"
        "fakeMarks(box.innerHTML); const before = box.innerHTML;\n"
        "S.at = 0; drawRoundMarks(); out.fresh = states(); out.freshTips = box.marks.map((m) => m.title);\n"
        "const firstOf = (n) => S.stops.findIndex((i) => S.flat[i].round === n);\n"
        "S.data.progress = " + json.dumps(first_done) + "; drawRoundMarks(); out.closedHere = states();\n"
        "S.at = firstOf(R[1].number); drawRoundMarks(); out.moved = states(); out.untouched = box.innerHTML === before;\n"
        "out.tips = box.marks.map((m) => m.title);\n"
        "S.data.progress = " + json.dumps(second_part) + "; drawRoundMarks(); out.partTips = box.marks.map((m) => m.title);\n"
        "out.targets = R.slice(0, " + str(k) + ").map((r) => roundTarget(r.number).pos);\n"
        "out.firstStops = R.slice(0, " + str(k) + ").map((r) => firstOf(r.number));\n"
        "toRound(R[2].number); out.went = went.slice(); out.cuedAway = cued.length;\n"
        "S.at = roundTarget(R[1].number).pos; toRound(R[1].number); out.cuedHere = cued.length; out.wentHere = went[went.length - 1];\n"
        "S.data.progress = " + json.dumps(all_first) + "; drawRoundMarks(); out.allDone = states(); out.allTips = box.marks.map((m) => m.title);\n"
        "out.allTargets = R.slice(0, " + str(k) + ").map((r) => roundTarget(r.number).pos);\n"
        "// the second sheet numbers its own rounds from 1, the case's numbers kept underneath\n"
        "S.data.progress = " + json.dumps(fresh) + "; drawTranscript('2d'); out.second = order(box.innerHTML).filter((x) => typeof x === 'string');\n"
        "out.secondLabels = labels(box.innerHTML);\n"
        "// a server from before on_sheet: the place among the sheet's rounds\n"
        "const OLD = R.map((r) => { const c = Object.assign({}, r); delete c.on_sheet; delete c.sheet_rounds; return c; });\n"
        "open(OLD, " + json.dumps(fresh) + "); drawTranscript('2d'); out.oldLabels = labels(box.innerHTML);\n"
        "out.clockTitles = [clockTitle(R[" + str(k) + "]), clockTitle(R[1]), clockTitle(undefined)];\n"
        "// a server that sends no rounds: no markers, and nothing raises\n"
        "open([], " + json.dumps(fresh) + "); drawTranscript(" + json.dumps(DEMO_SHEET) + ");\n"
        "out.none = order(box.innerHTML).filter((x) => typeof x === 'string').length;\n"
        "fakeMarks(box.innerHTML); drawRoundMarks(); out.noneRaised = true;\n"
        "console.log(JSON.stringify(out));\n", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("155: the markers run in node", False, run.stderr.strip()[:400])
    out = json.loads(run.stdout)
    order = out["order"]
    starts = {}
    for at, item in enumerate(order):
        if isinstance(item, int):
            continue
        starts[int(item[1:])] = at
    flat_round = {}
    for s in case["sheets"]:
        for x in s["rows"]:
            flat_round[(x["sheet"], x["row"])] = next(r["number"] for r in rnds if (x["sheet"], x["row"]) in set(r["rows"]))
    index_of = {}
    for i, x in enumerate(x for s in case["sheets"] for x in s["rows"]):
        index_of[i] = flat_round[(x["sheet"], x["row"])]
    marker_ok = all(isinstance(order[at + 1], int) and index_of[order[at + 1]] == n
                    and all(index_of[o] != n for o in order[:at] if isinstance(o, int))
                    for n, at in starts.items())
    check("155: a marker before each round's first row on the sheet, round 1 at the top, and none mid-round",
          sorted(starts) == [r["number"] for r in on_first] and order[0] == f"m{on_first[0]['number']}"
          and sum(1 for o in order if isinstance(o, str)) == k and marker_ok
          and sum(1 for o in order if isinstance(o, int)) == len(case["sheets"][0]["rows"]),
          f"{k} markers among {len(order)} items")
    check("155: each marker names the round by its number on the sheet",
          out["labels"] == [f"Round {n}" for n in range(1, k + 1)]
          and out["secondLabels"] == [f"Round {n}" for n in range(1, k + 1)]
          and out["second"] == [f"m{r['number']}" for r in rnds if r["sheet"] == "2d"]
          and out["oldLabels"] == [f"Round {n}" for n in range(1, k + 1)], str(out["labels"] + out["secondLabels"]))
    nums = [r["number"] for r in on_first]
    check("155: on opening, round 1 reads now and the rest to do",
          out["fresh"] == [[nums[0], "now", "now"]] + [[n, "todo", "to do"] for n in nums[1:]], str(out["fresh"]))
    check("155: a round closed while it still holds the current turn reads done",
          out["closedHere"][0] == [nums[0], "done", "done"], str(out["closedHere"]))
    check("155: a move into the next round turns its marker to now, the closed one staying done, in place",
          out["moved"] == [[nums[0], "done", "done"], [nums[1], "now", "now"]] + [[n, "todo", "to do"] for n in nums[2:]]
          and out["untouched"], str(out["moved"]))
    check("155: the tooltip gives the participant turns, the first and last rows' times and where a click goes",
          out["freshTips"] == [tip(n, "open ") for n in nums]
          and out["tips"] == [tip(nums[0], "")] + [tip(n, "open ") for n in nums[1:]], str(out["tips"]))
    check("155: a click goes to the round's first undecided turn, or its first turn when all are decided",
          out["targets"][0] == out["firstStops"][0] and out["targets"][1] == out["firstStops"][1] + 2
          and out["targets"][2] == out["firstStops"][2]
          and out["allTargets"] == out["firstStops"][:k],
          f"{out['targets']} against {out['firstStops']}")
    check("155: the click goes by goTo alone with no count, and cues the recording on the turn he is on",
          out["went"] == [[out["firstStops"][2]]] and out["cuedAway"] == 0
          and out["cuedHere"] == 1 and out["wentHere"] == [out["targets"][1]], str(out["went"]))
    check("155: with every round of the sheet closed, every marker reads done",
          all(s[1:] == ["done", "done"] for s in out["allDone"]), str(out["allDone"]))
    check("155: a server that sends no rounds draws no markers, and nothing raises",
          out["none"] == 0 and out["noneRaised"] is True)

    # ── E. the round clock in node: one count per round, zero on a first entry, resumed on a return
    away = support.section(js, "away time")
    script = scratch / "round-clock.js"
    script.write_text(support.i18n_js() +
        "let NOW = 5000000;\nDate.now = () => NOW;\nconst el = { textContent: '' };\nconst $ = () => el;\n"
        + away + "\n"
        "const out = {};\n"
        "clockClear(); clockRound(1);\n"
        "NOW += 30000; out.r1 = clockSeconds();\n"
        "clockRound(2); out.r2first = clockSeconds(); drawClock(); out.r2drawn = el.textContent;\n"
        "NOW += 20000; out.r2 = clockSeconds();\n"
        "clockRound(1); out.r1back = clockSeconds(); NOW += 5000; out.r1more = clockSeconds();\n"
        "clockRound(1); NOW += 1000; out.same = clockSeconds();\n"
        "clockRound(2); out.r2back = clockSeconds();\n"
        "awayStart(); NOW += 60000; out.r2away = clockSeconds(); awayStop(); out.pace = awayTally();\n"
        "NOW += 2000; clockReset(); out.r2reset = clockSeconds(); NOW += 3000; out.r2run = clockSeconds();\n"
        "clockRound(1); out.r1kept = clockSeconds(); clockRound(2); out.r2kept = clockSeconds(); out.paceKept = awayTally();\n"
        "clockRound(3); out.r3 = clockSeconds();\n"
        "awayReset(); out.paceSaved = awayTally(); clockRound(1); out.r1afterSave = clockSeconds();\n"
        "clockClear(); clockRound(1); out.cleared1 = clockSeconds(); clockRound(2); out.cleared2 = clockSeconds();\n"
        "console.log(JSON.stringify(out));\n", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        check("156: the round clock runs in node", False, run.stderr.strip()[:300])
    else:
        c = json.loads(run.stdout)
        check("156: in node, a round entered for the first time shows 00:00",
              c["r1"] == 30 and c["r2first"] == 0 and c["r2drawn"] == "00:00" and c["r2"] == 20 and c["r3"] == 0, str(c))
        check("156: in node, going back to an earlier round resumes its count, and going on resumes the other's",
              c["r1back"] == 30 and c["r1more"] == 35 and c["same"] == 36 and c["r2back"] == 20, str(c))
        check("156: in node, the time away is left out of the round's count, exactly as before",
              c["r2away"] == 20 and c["pace"] == 60, str(c))
        check("156: in node, the reset sets the current round to zero and leaves every other round and the pace",
              c["r2reset"] == 0 and c["r2run"] == 3 and c["r1kept"] == 36 and c["r2kept"] == 3 and c["paceKept"] == 60, str(c))
        check("156: in node, a save's reset of the pace leaves the round counts, and opening a case clears them all",
              c["paceSaved"] == 0 and c["r1afterSave"] == 36 and c["cleared1"] == 0 and c["cleared2"] == 0, str(c))

    # ── F. the count in node: forward decided moves only, Halfway and Last one, none on a close
    flash_src = "\n".join([ln for ln in js.splitlines() if ln.startswith(("function roundsOn(", "function roundsHere("))]
                          + [whole(n) for n in ("countWord", "closingOnMove", "flashCount", "roundsToClose", "afterCommit", "goTo")])
    move_line = next(line for line in js.splitlines() if line.startswith("const move = "))
    script = scratch / "count-flash.js"
    script.write_text(support.i18n_js() +
        "let reduce = false;\n"
        "const window = { matchMedia: () => ({ matches: reduce }) };\n"
        "const mk = () => { const set = new Set(); const ops = [];\n"
        "  return { innerHTML: '', offsetWidth: 1, ops, set, classList: { add: (c) => { set.add(c); ops.push('+' + c); },\n"
        "    remove: (c) => { set.delete(c); ops.push('-' + c); } } }; };\n"
        "const els = { 'count-flash': mk(), 'rail-turn': mk() };\n"
        "const $ = (id) => els[id];\n"
        "const esc = (s) => String(s);\n"
        "const cheerOn = () => true; const sound = () => {};\n"
        "const STOPS = " + json.dumps([[r["number"], [rounds_mod.row_key(*s) for s in r["stops"]]] for r in on_first]) + ";\n"
        "const S = { data: null, flat: [], stops: [], at: 0, dirty: false, note: null, editing: null, closing: new Set() };\n"
        "for (const [n, keys] of STOPS) for (const key of keys) {\n"
        "  const i = S.flat.length; const [sheet, row] = key.split(':');\n"
        "  S.flat.push({ i, key, sheet, row: Number(row), round: n, stop: true, pos: S.stops.length }); S.stops.push(i); }\n"
        "const ROUNDS = STOPS.map(([n, keys]) => ({ number: n, stops: keys.map((k) => ({ sheet: k.split(':')[0], row: Number(k.split(':')[1]) })) }));\n"
        "const current = () => S.flat[S.stops[S.at]];\n"
        "const currentRound = () => { const r = current(); return r ? S.data.rounds.find((x) => x.number === r.round) : null; };\n"
        "const log = []; const drawTurn = () => log.push('draw'); const closeLeftRounds = () => log.push('close');\n"
        "const celebrate = (n) => log.push('card ' + n); const say = (t) => log.push(t);\n"
        "const keepNote = () => {}; const centreCurrent = () => {}; const focusEntry = () => {};\n"
        "const commit = () => { S.dirty = false; return Promise.resolve(); };\n"
        + flash_src + "\n" + move_line + "\n"
        "const shown = () => (els['count-flash'].set.has('on') ? els['count-flash'].innerHTML.replace(/<[^>]+>/g, '') : null);\n"
        "const clear = () => { for (const e of Object.values(els)) { e.set.clear(); e.ops.length = 0; e.innerHTML = ''; } };\n"
        "const progress = (done, states, recorded) => ({ roundsDone: done, states: states || {}, complete: null,\n"
        "  roundTurns: ROUNDS.map((r) => ({ number: r.number, decided: 0, total: r.stops.length, recorded: (recorded || []).includes(r.number) })) });\n"
        "S.data = { rounds: ROUNDS, progress: progress([]), config: { work_in_rounds: true } };\n"
        "const n1 = ROUNDS[0].stops.length;\n"
        "const out = {};\n"
        "(async () => {\n"
        "  out.words = [[8, 20], [10, 20], [9, 20], [20, 20], [11, 21], [10, 21], [1, 20], [1, 1], [1, 2], [2, 2], [2, 4], [0, 5], [6, 5]]\n"
        "    .map(([p, t]) => countWord(p, t));\n"
        "  // Next after a save, and Skip, on the first turn: the second place, the bar's numeral brightened too\n"
        "  clear(); S.at = 0; afterCommit(current()); out.next = shown(); out.tick = els['rail-turn'].set.has('tick');\n"
        "  out.restart = els['count-flash'].ops.slice();\n"
        "  // a second at once replaces the first, taken off and put back\n"
        "  afterCommit(current()); out.again = shown(); out.againOps = els['count-flash'].ops.slice();\n"
        "  clear(); S.at = Math.ceil(n1 / 2) - 2; afterCommit(current()); out.half = shown();\n"
        "  clear(); S.at = n1 - 2; afterCommit(current()); out.last = shown();\n"
        "  // the save of the round's last turn closes it: the card, and no flash\n"
        "  clear(); S.data.progress = progress([ROUNDS[0].number]); S.at = n1 - 1; log.length = 0; afterCommit(current());\n"
        "  out.closing = { flash: shown(), card: log.includes('card ' + ROUNDS[0].number), at: S.at };\n"
        "  // a move landing past a round done and unrecorded closes it on the way: no flash\n"
        "  clear(); S.at = n1 - 1; S.data.progress = progress([ROUNDS[0].number], {}, [ROUNDS[0].number]);\n"
        "  S.data.progress.complete = '2026-10-03T14:05:00';\n"
        "  afterCommit(current()); out.recordedOn = shown();\n"
        "  clear(); S.data.progress = progress([ROUNDS[0].number]); S.at = n1 - 1; await goTo(n1, { count: true }); out.passClosing = shown();\n"
        "  // Cmd + K over a blank turn is a pass: flash. Previous and Cmd + J: none\n"
        "  clear(); S.data.progress = progress([]); S.at = 3; await move(1); out.pass = shown();\n"
        "  clear(); await move(-1); out.back = shown();\n"
        "  // Cmd + K over a turn already decided decides nothing: none. With words typed it saves on the way: flash\n"
        "  clear(); S.data.progress = progress([], { [current().key]: 'reviewed' }); await move(1); out.decidedSkip = shown();\n"
        "  clear(); S.data.progress = progress([], { [current().key]: 'reviewed' }); S.dirty = true; await move(1); out.savedOn = shown();\n"
        "  // a click on to a later turn passes the one it leaves, a click back raises nothing\n"
        "  clear(); S.data.progress = progress([]); await goTo(S.at + 3, { count: true }); out.clickOn = shown();\n"
        "  clear(); await goTo(S.at - 2, { count: true }); out.clickBack = shown();\n"
        "  // a marker's click, the sheet switcher and undo go without the count\n"
        "  clear(); await goTo(S.at + 2); out.plain = shown();\n"
        "  // reduced motion: nothing at all, neither the flash nor the bar\n"
        "  clear(); reduce = true; S.at = 0; afterCommit(current()); out.reduced = [shown(), els['rail-turn'].set.has('tick'), els['count-flash'].ops.length];\n"
        "  reduce = false;\n"
        "  // a page in front of a server with no rounds raises nothing\n"
        "  clear(); S.data.rounds = []; S.at = 0; afterCommit(current()); out.noRounds = shown();\n"
        "  console.log(JSON.stringify(out));\n"
        "})();\n", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("157: the count runs in node", False, run.stderr.strip()[:400])
    f = json.loads(run.stdout)
    n1 = len(on_first[0]["stops"])
    check("157: in node, the count reads the place out of the round, Halfway at the first place at or past half, Last one at the end",
          f["words"] == ["8 / 20", "Halfway", "9 / 20", "Last one", "Halfway", "10 / 21", "1 / 20", "1 / 1", "1 / 2",
                         "Last one", "Halfway", "", ""], str(f["words"]))
    check("157: in node, Next or Skip on the first turn flashes the second place, and the bar's numeral brightens with it",
          f["next"] == f"2 / {n1}" and f["tick"] and f["restart"] == ["-on", "+on"], str(f))
    check("157: in node, a new flash replaces one still showing, taken off and put back",
          f["again"] == f"3 / {n1}" and f["againOps"] == ["-on", "+on", "-on", "+on"], str(f["againOps"]))
    check("157: in node, the midpoint turn reads Halfway and the round's last turn Last one",
          f["half"] == "Halfway" and f["last"] == "Last one", f"{f['half']} {f['last']}")
    check("157: in node, the move that closes a round raises no flash, the card has the moment",
          f["closing"]["flash"] is None and f["closing"]["card"] and f["passClosing"] is None, str(f["closing"]))
    check("157: in node, a save on the last turn of a round already recorded moves on and flashes the next round's first place",
          f["recordedOn"] == f"1 / {len(on_first[1]['stops'])}", str(f["recordedOn"]))
    check("157: in node, a pass with Cmd + K flashes, Previous and Cmd + J raise nothing",
          f["pass"] == f"5 / {n1}" and f["back"] is None, f"{f['pass']} {f['back']}")
    check("157: in node, a step over a turn already decided raises nothing, a save on the way flashes",
          f["decidedSkip"] is None and f["savedOn"] is not None, f"{f['decidedSkip']} {f['savedOn']}")
    check("157: in node, a click on to a later turn flashes, a click back and a move without the count raise nothing",
          f["clickOn"] is not None and f["clickBack"] is None and f["plain"] is None, str(f))
    check("157: in node, nothing at all under reduced motion, and nothing with no rounds",
          f["reduced"] == [None, False, 0] and f["noRounds"] is None, str(f["reduced"]))
