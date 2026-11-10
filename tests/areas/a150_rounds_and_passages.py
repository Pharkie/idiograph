from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import support
from .support import check, skip


def test_rounds_and_passages(scratch):
    print("\n150. Work in rounds, a setting off on a new install, and passage for turn, 15 October, Adam's word from a "
          "tester's feedback: rounds are a pace and not a step of IPA, and a passage is the IPA book's word for one "
          "person's stretch of talk. Since the test review of 18 October the bar's words and widths are review shots, "
          "and the setting, what a round's close does and the cards that still come stay")
    import subprocess
    import server as server_mod

    read = lambda path: Path(path).read_text(encoding="utf-8")
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")

    def whole(name):
        """A function of app.js whole, a one-line one included."""
        at = app.index(f"function {name}(")
        if app[max(0, at - 6):at] == "async ":
            at -= 6
        line = app[at:app.index("\n", at)]
        if line.rstrip().endswith("}") and line.count("{") == line.count("}"):
            return line
        return app[at:app.index("\n}", at) + 2]

    body = lambda name: whole(name).split("{", 1)[1]

    # the family's Settings asks Idiograph's part through its hooks since the fifth build (23 October 2026): the
    # card's opening and its Save read with the hooks they ask, in the order they ask them
    HOOKED = {"openSettings": ("openSettings", "distilSettingsOpen"),
              "saveSettings": ("saveSettings", "distilSettingsBody",
                               "distilSettingsSaved", "distilSettingsAfter")}
    body = (lambda one: lambda name: "\n".join(one(n) for n in HOOKED.get(name, (name,))))(body)
    const = lambda name: next(ln for ln in app.splitlines() if ln.startswith(f"const {name} = "))

    # ── A. the setting: off on a new install, an absent key off, saved and read back
    check("150: Work in rounds is work_in_rounds in the server's defaults, false, so a new install and the Mac app's "
          "shipped settings start with rounds off",
          server_mod.defaults().get("work_in_rounds") is False and server_mod.shipped_config()["work_in_rounds"] is False)
    check("150: a settings file without the key reads off, and one that has it keeps its value",
          server_mod.merge_config({"interviewer": "Adam", "round_minutes": 12})["work_in_rounds"] is False
          and server_mod.merge_config({"work_in_rounds": True})["work_in_rounds"] is True)
    saved = server_mod.CONFIG_PATH
    server_mod.CONFIG_PATH = scratch / "rounds-150-config.json"
    try:
        server_mod.CONFIG_PATH.write_text(json.dumps({"interviewer": "Adam", "round_minutes": 15}), encoding="utf-8")
        before = server_mod.config()["work_in_rounds"]
        on = server_mod.api_settings({"interviewer": "Adam", "work_in_rounds": True})["config"]
        on_disk = json.loads(server_mod.CONFIG_PATH.read_text(encoding="utf-8"))
        kept = server_mod.api_settings({"interviewer": "Adam"})["config"]
        off = server_mod.api_settings({"work_in_rounds": False})["config"]
        off_disk = json.loads(server_mod.CONFIG_PATH.read_text(encoding="utf-8"))
        read_back = server_mod.config()
    finally:
        server_mod.CONFIG_PATH = saved
    check("150: Save writes the tick as it stands and reads it back, a save without it keeping it, the rest of the file "
          "as it was",
          before is False and on["work_in_rounds"] is True and on_disk["work_in_rounds"] is True
          and kept["work_in_rounds"] is True and off["work_in_rounds"] is False and off_disk["work_in_rounds"] is False
          and read_back["work_in_rounds"] is False and off_disk["round_minutes"] == 15,
          f"{before} {on_disk.get('work_in_rounds')} {off_disk.get('work_in_rounds')} {off_disk.get('round_minutes')}")

    # ── B. Settings, Distil: the tick above its two fields, which show only while it is ticked
    check("150: the card ticks it from the settings, an absent key unticked, shows the two fields only while it is "
          "ticked and sends it with every Save",
          "$('set-rounds').checked = roundsOn(c);" in body("openSettings")
          and "$('rounds-fields').hidden = !$('set-rounds').checked;" in body("openSettings")
          and "$('set-rounds').onchange = () => {\n    $('rounds-fields').hidden = !$('set-rounds').checked;" in app
          and "work_in_rounds: $('set-rounds').checked," in body("saveSettings")
          and whole("roundsOn") == "function roundsOn(cfg) { return !!(cfg && cfg.work_in_rounds); }")
    check("150: a Save over the screen that turns it draws the bar, the markers and the count again in place, a "
          "field typed into saved first, and over PETs the case reopens on the way back",
          "const turned = paced !== roundsOn(data.config);" in body("saveSettings")
          and "if (ctx.themes) { if (recut || turned) S.recut = true; }" in body("saveSettings")
          and "if (S.dirty && current()) await commit(current(), false);" in body("saveSettings")
          and "drawRoundsShown();\n      drawTurn({ keepPlayer: true });" in body("saveSettings")
          and "say(roundsOn(data.config) ? t('distil.settings.rounds_reopening') : t('distil.settings.reopening'));" in body("saveSettings"))

    # ── D. in node: the bar, the markers, the count, the card, the close, the days and the haul
    node = shutil.which("node")
    if not node:
        skip("150: the page with rounds off and on, in node", "node is not installed")
    else:
        names = ["roundsOn", "roundsHere", "sheetPlace", "drawRoundsShown", "barNumbers", "currentRound", "roundPlace",
                 "drawRoundBar", "drawProgress", "whenOf", "drawMark", "sheetRound", "roundMarkState", "roundTarget",
                 "drawRoundMarks", "drawTranscript", "roundsToClose", "closeLeftRounds", "celebrate", "closeRounds",
                 "endsSheet", "roundDone", "drawDoneMark", "formatMinutes", "stopHere", "countWord", "closingOnMove",
                 "flashCount", "afterCommit", "haulTime", "haulLine", "loadDays", "cheerLine"]
        lines_src = "const LINES = [" + app.split("const LINES = [", 1)[1].split("];", 1)[0] + "];"
        source = "\n".join([support.i18n_js(), lines_src, const("dayOf"), const("share"), const("MARK_WORDS"),
                            const("current")] + [whole(n) for n in names])
        script = scratch / "rounds-150.js"
        script.write_text(r"""
const els = {};
const mk = (id) => ({ id, textContent: '', innerHTML: '', hidden: false, title: '', style: {}, dataset: {},
  classList: { on: new Set(), toggle(c, v) { if (v === undefined) v = !this.on.has(c); if (v) this.on.add(c); else this.on.delete(c); return v; },
    add(...c) { c.forEach((x) => this.on.add(x)); }, remove(...c) { c.forEach((x) => this.on.delete(x)); }, contains(c) { return this.on.has(c); } },
  querySelectorAll() { return []; } });
const $ = (id) => els[id] || (els[id] = mk(id));
const window = { matchMedia: () => ({ matches: false }) };
const esc = (s) => String(s);
const sound = () => {}; const cheerOn = () => true;
const fired = []; const confetti = (level) => fired.push(level);
const show = (id) => { $(id).hidden = false; }; const hide = (id) => { $(id).hidden = true; };
const said = []; const say = (t) => said.push(t);
const haulShow = () => {}; const focusEntry = () => {};
const marks = []; const roundMarkHtml = (r) => { marks.push(r.number); return '<m>'; };
const turnHtml = (row) => `<t${row.i}>`; const drawSheetLabel = () => {}; const parkNotes = () => {}; const parkCard = () => {}; const parkNote = () => {};
const drawDoneMarks = () => {};
const posted = []; let daysAsked = 0;
const api = async (path, body) => {
  if (path === '/api/days') { daysAsked += 1; return { days: {}, today: '2026-10-15', dailyTarget: 2 }; }
  posted.push(body.round);
  const p = S.data.progress;
  p.roundTurns = p.roundTurns.map((r) => (r.number === body.round ? Object.assign({}, r, { recorded: true }) : r));
  return { progress: p };
};
const drawn = []; let daysDrawn = 'unset'; const drawDays = (d) => { daysDrawn = d; };
let libraryAsk = 1;
const S = { data: null, flat: [], stops: [], at: 0, closing: new Set(), sheetDrawn: null, libConfig: null };
""" + source + r"""
const drawTurn = () => drawn.push(S.at);
const flashed = [];
// the case: Initial, two rounds of two participant passages each, and 2d, one round of three
const rows = [['Initial', 2, 'Adam', 1], ['Initial', 3, 'Juno', 1], ['Initial', 4, 'Juno', 1], ['Initial', 5, 'Adam', 2],
  ['Initial', 6, 'Juno', 2], ['Initial', 7, 'Juno', 2], ['2d', 2, 'Adam', 3], ['2d', 3, 'Juno', 3], ['2d', 4, 'Juno', 3], ['2d', 5, 'Juno', 3]];
function load(paced, decided, recorded = []) {
  S.flat = rows.map(([sheet, row, name, round], i) => ({ sheet, row, name, round, i, key: `${sheet}:${row}`, time: `00:0${i}`, stop: name !== 'Adam' }));
  S.stops = [];
  for (const r of S.flat) if (r.stop) { r.pos = S.stops.length; S.stops.push(r.i); }
  const rounds = [1, 2, 3].map((n) => {
    const of = S.flat.filter((r) => r.round === n);
    const sheet = of[0].sheet;
    return { number: n, sheet, on_sheet: n === 3 ? 1 : n, sheet_rounds: sheet === 'Initial' ? 2 : 1,
      rows: of.map((r) => ({ sheet: r.sheet, row: r.row })), stops: of.filter((r) => r.stop).map((r) => ({ sheet: r.sheet, row: r.row })) };
  });
  const states = {};
  for (const i of S.stops) states[S.flat[i].key] = decided.includes(S.flat[i].key) ? 'has-content' : 'unvisited';
  const done = rounds.filter((r) => r.stops.every((s) => states[`${s.sheet}:${s.row}`] !== 'unvisited')).map((r) => r.number);
  const sheetRounds = ['Initial', '2d'].map((sheet) => {
    const here = rounds.filter((r) => r.sheet === sheet);
    const d = here.filter((r) => done.includes(r.number)).length;
    return { sheet, rounds: here.length, done: d, left: here.length - d, minutesLeft: 10 * (here.length - d) };
  });
  S.data = { config: { work_in_rounds: paced }, rounds, progress: { states, roundsDone: done, roundsLeft: 3 - done.length,
    roundTurns: rounds.map((r) => ({ number: r.number, decided: r.stops.filter((s) => states[`${s.sheet}:${s.row}`] !== 'unvisited').length,
      total: r.stops.length, recorded: recorded.includes(r.number) })),
    sheetRounds, sheetsDone: sheetRounds.filter((x) => x.left === 0).length, sheetsLeft: sheetRounds.filter((x) => x.left > 0).length,
    turnsDone: Object.values(states).filter((v) => v !== 'unvisited').length, turnsTotal: S.stops.length,
    dailyTarget: 2, todayRounds: 1, streak: 3, minutesLeft: 10 * (3 - done.length), complete: null, todayTurns: 4, todaySeconds: 900 } };
  S.closing = new Set();
  for (const id of Object.keys(els)) delete els[id];
  fired.length = 0; said.length = 0; marks.length = 0; posted.length = 0; drawn.length = 0;
  $('round-done').hidden = true;
}
const keys = (...ks) => ks.map((k) => (k.includes(':') ? k : `Initial:${k}`));
const bar = () => ({ inRound: $('rail-in-round').hidden, inRoundN: $('rail-in-round-n').hidden, roundBar: $('round-bar').hidden, clock: $('rail-clock').hidden,
  clockSep: $('rail-clock-sep').hidden, reset: $('rail-clock-reset').hidden, unit: $('rail-unit').hidden,
  roundItem: $('rail-round-item').hidden, roundSep: $('rail-round-sep').hidden, daily: $('rail-daily').hidden,
  place: $('rail-place').hidden, strip: $('progress-strip').title, off: $('work').classList.contains('rounds-off') });
const card = () => ({ hidden: $('round-done').hidden, kicker: $('done-kicker').textContent, line: $('done-line').textContent,
  countLabel: $('done-count-label').textContent, count: String($('done-count').textContent),
  leftLabel: $('done-left-label').textContent, left: String($('done-left').textContent), eta: $('done-eta-box').hidden,
  two: $('done-figures').classList.contains('two'), daily: $('done-daily').textContent, dailyHidden: $('done-daily').hidden,
  then: $('done-then').hidden, next: $('done-next').hidden, sheet: $('done-sheet').hidden, library: $('done-library').hidden,
  mark: $('done-mark').hidden, level: fired[fired.length - 1] });
const out = {};
(async () => {
  // the bar with rounds off, then on
  load(false, keys('3'));
  S.at = 2; drawRoundsShown(); drawProgress(); out.barOff = bar();
  out.placeOff = sheetPlace(S.flat[S.stops[2]]); out.placeTwo = sheetPlace(S.flat[S.stops[5]]);
  load(true, keys('3'));
  S.at = 2; drawRoundsShown(); drawProgress(); out.barOn = bar();
  // a case of one sheet: no case figure in the tooltip
  load(false, []); S.flat = S.flat.filter((r) => r.sheet === 'Initial'); S.stops = S.stops.slice(0, 4);
  out.placeOne = sheetPlace(S.flat[S.stops[3]]);
  // the markers
  load(false, []); drawTranscript('Initial'); out.marksOff = marks.slice();
  load(true, []); drawTranscript('Initial'); out.marksOn = marks.slice();
  // the card: a round mid-sheet, the end of a sheet, the end of the case
  load(false, keys('3', '4')); roundDone([1], true); out.midOff = card();
  load(true, keys('3', '4')); roundDone([1], true); out.midOn = card();
  load(false, keys('3', '4', '6', '7')); roundDone([2], true); out.sheetOff = card();
  load(true, keys('3', '4', '6', '7')); roundDone([2], true); out.sheetOn = card();
  load(false, keys('3', '4', '6', '7', '2d:3', '2d:4', '2d:5')); roundDone([3], true); out.caseOff = card();
  stopHere(); out.stopCase = said[said.length - 1];
  load(true, keys('3', '4', '6', '7', '2d:3', '2d:4', '2d:5')); roundDone([3], true); out.caseOn = card();
  // the close: with rounds off it still goes to the server, with no card mid-sheet
  load(false, keys('3', '4'));
  await closeRounds([1], { advance: true }); out.closeMidOff = { posted: posted.slice(), card: $('round-done').hidden, fired: fired.length };
  load(false, keys('3', '4', '6', '7'), [1]);
  await closeRounds([2], {}); out.closeSheetOff = { posted: posted.slice(), card: $('round-done').hidden, level: fired[fired.length - 1] };
  load(true, keys('3', '4'));
  await closeRounds([1], {}); out.closeMidOn = { posted: posted.slice(), card: $('round-done').hidden, level: fired[fired.length - 1] };
  // the save of a round's last passage: moves on with rounds off, the card with them on
  load(false, keys('3', '4')); S.at = 1; afterCommit(S.flat[S.stops[1]]); await new Promise((r) => setTimeout(r, 0));
  out.saveOff = { at: S.at, drawn: drawn.slice(), card: $('round-done').hidden, posted: posted.slice() };
  load(true, keys('3', '4')); S.at = 1; afterCommit(S.flat[S.stops[1]]); await new Promise((r) => setTimeout(r, 0));
  out.saveOn = { at: S.at, drawn: drawn.slice(), card: $('round-done').hidden, posted: posted.slice() };
  // the count: the place on the sheet with rounds off, in the round with them on, and held back only for a card
  load(false, keys('3', '4')); S.at = 2; out.closingOff = closingOnMove(); flashCount(); out.flashOff = $('count-flash').innerHTML;
  load(true, keys('3', '4')); S.at = 2; out.closingOn = closingOnMove();
  load(true, keys('3', '4'), [1]); S.at = 2; flashCount(); out.flashOn = $('count-flash').innerHTML;
  load(false, keys('3', '4', '6', '7')); S.at = 4; out.closingSheetOff = closingOnMove();
  // the days and the haul
  load(false, []); S.libConfig = { work_in_rounds: false }; daysAsked = 0; await loadDays(1); out.daysOff = { asked: daysAsked, drawn: daysDrawn };
  S.libConfig = {}; daysDrawn = 'unset'; await loadDays(1); out.daysAbsent = { asked: daysAsked, drawn: daysDrawn };
  S.libConfig = { work_in_rounds: true }; await loadDays(1); out.daysOn = { asked: daysAsked, drawn: !!daysDrawn };
  load(false, []); out.haulOff = haulLine(S.data.progress);
  load(true, []); out.haulOn = haulLine(S.data.progress);
  out.cheerOff = cheerLine(false); out.cheerOn = cheerLine(true);
  console.log(JSON.stringify(out));
})().catch((err) => { console.error(err.stack); process.exit(1); });
""", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
        if not out:
            check("150: the page runs in node", False, run.stderr.strip()[:400])
        else:
            check("150: the place with rounds off is the passage among its sheet's participant passages, the case's "
                  "figure in the tooltip where the case has more than one sheet",
                  out["placeOff"] == {"on": 3, "of": 4, "title": "passage 3 of 4 on this sheet, 3 of 7 for this participant"}
                  and out["placeTwo"] == {"on": 2, "of": 3, "title": "passage 2 of 3 on this sheet, 6 of 7 for this participant"}
                  and out["placeOne"] == {"on": 4, "of": 4, "title": "passage 4 of 4"},
                  f"{out['placeOff']} {out['placeTwo']} {out['placeOne']}")
            check("150: with rounds off no round marker is drawn across the transcript, with them on one a round",
                  out["marksOff"] == [] and out["marksOn"] == [1, 2], f"{out['marksOff']} {out['marksOn']}")
            m = out["midOff"]
            check("150: with rounds off a round closing mid-sheet brings no card and no confetti",
                  m["hidden"] and m.get("level") is None, str(m))
            m = out["midOn"]
            check("150: with rounds on the round card comes as before, its round, its figures, its target and Next round",
                  not m["hidden"] and m["kicker"] == "Round 1 done" and m["countLabel"] == "Rounds done"
                  and m["leftLabel"] == "Left on this sheet" and not m["eta"] and not m["dailyHidden"]
                  and m["daily"] == "1 more round today meets the target." and not m["next"] and m["level"] == 1, str(m))
            s = out["sheetOff"]
            check("150: with rounds off the sheet's end still brings the sheet-done card, its passages and the sheets "
                  "left, with no round figure, pace, target or streak, Next sheet and level 2",
                  not s["hidden"] and s["kicker"] == "Initial sheet done" and s["line"] == "The 2d sheet is next."
                  and s["countLabel"] == "Passages on this sheet" and s["count"] == "4" and s["leftLabel"] == "Sheets left"
                  and s["left"] == "1" and s["eta"] and s["two"] and s["dailyHidden"] and s["daily"] == ""
                  and s["next"] and not s["sheet"] and s["level"] == 2, str(s))
            s = out["sheetOn"]
            check("150: with rounds on the sheet-done card is as it was",
                  not s["hidden"] and s["countLabel"] == "Rounds on this sheet" and s["count"] == "2" and not s["eta"]
                  and not s["dailyHidden"] and s["level"] == 2, str(s))
            c = out["caseOff"]
            check("150: with rounds off the case's end still brings the case-complete card, every passage decided, the "
                  "offer to mark the phase complete, no round figure, target or streak, and level 3",
                  not c["hidden"] and c["kicker"] == "Every passage decided" and c["line"] == "Participant complete."
                  and c["countLabel"] == "Passages decided" and c["count"] == "7" and c["leftLabel"] == "Sheets"
                  and c["left"] == "2" and c["eta"] and c["two"] and c["dailyHidden"] and not c["mark"]
                  and not c["library"] and c["next"] and c["level"] == 3
                  and out["stopCase"] == "A break at the end of the participant's transcript.", f"{c} {out['stopCase']}")
            c = out["caseOn"]
            check("150: with rounds on the case-complete card keeps its round, its figures and its target line",
                  c["kicker"] == "Round 1 done" and c["countLabel"] == "Rounds done" and c["left"] == "0"
                  and c["daily"].startswith("Every passage of this participant is decided. ") and not c["mark"] and c["level"] == 3, str(c))
            check("150: with rounds off a round still closes with the server, so the daily tally stays true, quietly "
                  "mid-sheet and with its card at the sheet's end, and with them on as before",
                  out["closeMidOff"] == {"posted": [1], "card": True, "fired": 0}
                  and out["closeSheetOff"]["posted"] == [2] and out["closeSheetOff"]["card"] is False
                  and out["closeSheetOff"]["level"] == 2
                  and out["closeMidOn"]["posted"] == [1] and out["closeMidOn"]["card"] is False and out["closeMidOn"]["level"] == 1,
                  f"{out['closeMidOff']} {out['closeSheetOff']} {out['closeMidOn']}")
            check("150: a save of a round's last passage moves straight on with rounds off and closes the round on the "
                  "way, and with them on stops for the card",
                  out["saveOff"]["at"] == 2 and out["saveOff"]["drawn"] == [2] and out["saveOff"]["card"] is True
                  and out["saveOff"]["posted"] == [1]
                  and out["saveOn"]["at"] == 1 and out["saveOn"]["drawn"] == [] and out["saveOn"]["card"] is False
                  and out["saveOn"]["posted"] == [1], f"{out['saveOff']} {out['saveOn']}")
            check("150: the count flashes the place on the sheet with rounds off and in the round with them on, held back "
                  "only for a move whose close brings a card",
                  out["closingOff"] is False and out["flashOff"] == '3<span class="count-of"> / 4</span>'
                  and out["closingOn"] is True and out["flashOn"] == '1<span class="count-of"> / 2</span>'
                  and out["closingSheetOff"] is True,
                  f"{out['closingOff']} {out['flashOff']} {out['closingOn']} {out['flashOn']} {out['closingSheetOff']}")
            check("150: with rounds off, or no key at all, the home screen asks nothing for the days and draws none, and "
                  "with them on it asks and draws them",
                  out["daysOff"] == {"asked": 0, "drawn": None} and out["daysAbsent"] == {"asked": 0, "drawn": None}
                  and out["daysOn"] == {"asked": 1, "drawn": True}, f"{out['daysOff']} {out['daysAbsent']} {out['daysOn']}")

