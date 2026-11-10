from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from . import support
from .support import check, skip


def test_distil_steps(scratch):
    print("\n177. The way through Distil, 18 October, Adam's decision on a tester's feedback (Topic A of 17 October): "
          "Experiential statements, PETs and GETs as one row of steps on each of Distil's bars, the project's page in "
          "the order of the work, and New sticky note on the PETs and GETs bars. Since the test review of 18 October the "
          "steps' markup, words and widths are review shots, and what each step, P and Sticky note do stays")
    read = lambda path: Path(path).read_text(encoding="utf-8")
    app, tjs = support.text("family/static/shell.js", "apps/idiograph/static/distil.js"), support.text("apps/idiograph/static/themes.js")
    drive = read(support.source("packaging/tauri/drive_common.py"))
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: (("async " if f"async function {name}(" in src else "") + f"function {name}(" + fn(src, name) + "\n}")
    line = lambda src, start: start + src.split(start, 1)[1].split("\n", 1)[0] if start in src else ""
    node = shutil.which("node")
    # ── F. the handlers
    check("177: the statements bar's PETs and GETs steps call esStep, P does what the PETs step does, and the boards' "
          "three steps call thStepTo, the Tauri drive pressing the GETs step",
          "$('es-step-pets').onclick = () => esStep('pets');" in app and "$('es-step-gets').onclick = () => esStep('gets');" in app
          and "else if (key === 'p' && !$('work').hidden && S.data) { e.preventDefault(); esStep('pets'); }" in app
          and "for (const [id, step] of [['th-step-es', 'statements'], ['th-step-pets', 'pets'], ['th-step-lpets', 'lpets'], ['th-step-gets', 'gets'],\n    ['th-step-lgets', 'lgets'], ['th-step-trajectories', 'trajectories'], ['th-step-codes', 'codes']]) {" in tjs
          and "$(id).onclick = () => thStepTo(step);" in tjs
          and "document.getElementById('th-step-gets').click();" in drive and "th-gets'" not in drive)

    if not node:
        skip("177: the steps in node", "node is not on this machine")
    else:
        # ── G. the statements bar's steps in node
        harness = r"""
const calls = [];
const noop = () => {};
const els = {};
const $ = (id) => (els[id] = els[id] || { hidden: true, title: '', attrs: {}, pause() { calls.push(['pause']); },
  setAttribute(k, v) { this.attrs[k] = v; } });
const S = { data: { path: 'walks/P1 Ada/P1 Ada - EN & ES.xlsx', name: 'P1 Ada - EN & ES' }, backTo: null, dirty: false, recut: false,
  flat: [{ sheet: 'Initial', row: 3 }, { sheet: 'Initial', row: 7 }], stops: [0, 1], at: 1 };
const current = () => S.flat[S.stops[S.at]];
const tpList = () => null, tpHere = () => null;
let FAIL = false;
let NO_API = false;
let GETS_BACK = null;
const commit = async () => { calls.push(['commit']); S.dirty = FAIL; };
const toLibrary = () => calls.push(['back']);
const navGo = (again, open) => open();
const openThemes = (path, from, label) => calls.push(['pets', path, from, label]);
const openGets = (path, more) => { calls.push(['gets', path, more.to, more.label, typeof more.back]); GETS_BACK = more.back; };
const openCase = (path) => calls.push(['openCase', path]);
const closeFind = () => calls.push(['closeFind']);
const measureBand = noop, centreCurrent = noop;
const focusEntry = () => calls.push(['focus']);
const say = noop, unsay = noop, needsRestart = () => false;
const OPENING_LINE = 'Opening.', RESTART_LINE = 'Restart.';
const api = async (route, body) => { calls.push(['api', route, body.path]); if (NO_API) throw new Error('gone'); return { path: body.path }; };
const startCase = (data, opts) => calls.push(['case', data.path, opts.at || null]);
""" + "\n".join(whole(app, n) for n in ("esStep", "esToGets", "openStatements")) + r"""
(async () => {
  const out = {};
  const take = () => calls.splice(0);
  esStep('pets'); out.pets = take();
  S.backTo = { to: 'pets', back: noop }; esStep('pets'); out.petsBack = take();
  await esStep('gets'); await new Promise((r) => setTimeout(r, 0)); out.getsFromPetsCard = take();
  S.backTo = { to: 'gets', back: noop }; esStep('gets'); out.getsBack = take();
  S.backTo = null; S.dirty = true; FAIL = true; await esToGets(); out.unsaved = take();
  FAIL = false; await esToGets(); out.saved = take();
  $('work').hidden = true; GETS_BACK(); out.cameBack = [$('work').hidden, take()];
  const how = (to) => ({ to, leave: () => calls.push(['leave']), back: () => calls.push(['board']) });
  out.same = [await openStatements('walks/P1 Ada/P1 Ada - EN & ES.xlsx', how('pets')), take(), S.backTo.to];
  out.other = [await openStatements('walks/P2 Bo/P2 Bo - EN & ES.xlsx', how('gets')), take(), S.backTo.to];
  S.backTo = null; NO_API = true;
  out.refused = [await openStatements('walks/P3 Cy/P3 Cy - EN & ES.xlsx', how('pets')), take(), S.backTo];
  NO_API = false; const kept = S.data; S.data = null; esStep('pets'); out.none = take(); S.data = kept;
  console.log(JSON.stringify(out));
})().catch((e) => { console.error(String(e && e.stack || e)); process.exit(1); });
"""
        script = scratch / "statements-steps-177.js"
        script.write_text(support.i18n_js() + harness, encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        o = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
        book = "walks/P1 Ada/P1 Ada - EN & ES.xlsx"
        check("177: in node, PETs on the statements bar opens this case's PETs from the statements, and where the screen "
              "was opened from a PETs card it is the way back to that board",
              o.get("pets") == [["pets", book, "work", "P1 Ada - EN & ES"]] and o.get("petsBack") == [["back"]],
              (run.stdout + run.stderr)[:300])
        check("177: in node, GETs on the statements bar opens the project's GETs through this case with the way back to "
              "this passage, the way back where the screen came from a GETs card, nothing saved twice",
              o.get("getsFromPetsCard") == [["pause"], ["closeFind"], ["gets", book, "statements", "", "function"]]
              and o.get("getsBack") == [["back"]], str([o.get("getsFromPetsCard"), o.get("getsBack")]))
        check("177: in node, a passage typed into is saved first, a save that fails keeps him on the passage, and the "
              "way back from GETs shows the statements again with the caret in its field",
              o.get("unsaved") == [["commit"]] and o.get("saved") == [["commit"], ["pause"], ["closeFind"], ["gets", book, "statements", "", "function"]]
              and o.get("cameBack") == [False, [["focus"]]], str([o.get("unsaved"), o.get("saved"), o.get("cameBack")]))
        check("177: in node, Experiential statements from a board opens the case, puts the board away only once it has, "
              "lands on the passage it was on when the screen still holds that case and names the board for the way "
              "back, and a refusal leaves the board as it is",
              o.get("same") == [True, [["api", "/api/open", book], ["leave"], ["case", book, {"sheet": "Initial", "row": 7}]], "pets"]
              and o.get("other") == [True, [["api", "/api/open", "walks/P2 Bo/P2 Bo - EN & ES.xlsx"], ["leave"],
                                            ["case", "walks/P2 Bo/P2 Bo - EN & ES.xlsx", None]], "gets"]
              and o.get("refused") == [False, [["api", "/api/open", "walks/P3 Cy/P3 Cy - EN & ES.xlsx"]], None]
              and o.get("none") == [], str([o.get("same"), o.get("other"), o.get("refused")]))

        # ── H. the boards' steps, the way back's tooltip and New sticky note in node
        harness = r"""
const calls = [];
const noop = () => {};
const els = {};
const mk = () => ({ hidden: false, title: '', attrs: {}, offsetWidth: 0,
  setAttribute(k, v) { this.attrs[k] = v; }, removeAttribute(k) { delete this.attrs[k]; }, getBoundingClientRect: () => ({}) });
const $ = (id) => (els[id] = els[id] || mk());
let TH = {};
const fresh = (more) => Object.assign({ mode: 'pets', live: true, busy: false, dirty: false, path: 'walks/P1 Ada/P1 Ada - EN & ES.xlsx',
  label: 'P1 - Ada', back: () => calls.push(['home']), to: 'cases', meta: { id: 'v2' }, v: { cards: {} }, view: { x: 4, y: 5, z: 0.75 },
  lastPick: null, sel: { cards: new Set(['c1']), groups: new Set(), stickies: new Set() }, ask: 0,
  gets: { cases: [{ case: 'P1 - Ada', who: 'Ada', path: 'walks/P1 Ada/P1 Ada - EN & ES.xlsx' }] } }, more);
const thGets = () => TH.mode === 'gets';
const thTpDraw = noop, thPickerPlace = noop;
const say = (t) => calls.push(['say', t]);
const thTitleDone = noop, thNoteDone = noop, thViewEnd = noop, thVmenu = noop, thPile = noop, thXmenu = noop, thCasemenu = noop,
  thSideShut = noop, thAiCard = noop, thExported = noop, thMade = noop, thMenuClose = noop;
let DIRTY_AFTER = false;
const thFlush = async () => { if (DIRTY_AFTER) TH.dirty = true; };
const themesBack = () => calls.push(['themesBack']);
const navGo = (again, open) => open();
const themesOpen = (path, opts) => calls.push(['pets', path, opts.to, opts.label, opts.board || null, typeof opts.back, opts.restore ? opts.restore.view.z : null]);
const getsOpen = (path, opts) => calls.push(['gets', path, opts.to, opts.label, opts.board || null, typeof opts.back, opts.restore ? opts.restore.view.z : null]);
let HOW = null;
const openStatements = (path, how) => { HOW = how; calls.push(['statements', path, how.to]); };
let STAGE = { left: 0, top: 46, width: 1000, height: 700, right: 1000 };
const thStage = () => ({ getBoundingClientRect: () => STAGE });
const thStickyNew = (x, y, opts) => calls.push(['sticky', x, y, !!(opts && opts.free)]);
// the bar's tabs, each holding its name's button (dsTabsDraw in app.js, since 20 October)
const tab = (step, id) => ({ hidden: false, dataset: { step }, classList: { on: false, toggle(k, v) { this.on = v; } },
  querySelector: () => $(id) });
els['th-steps'] = Object.assign(mk(), { scrollLeft: 0, clientWidth: 0, scrollWidth: 0, classList: { toggle: noop },
  querySelectorAll: () => [tab('statements', 'th-step-es'), tab('pets', 'th-step-pets'), tab('gets', 'th-step-gets')] });
""" + "\n".join([line(tjs, "const TH_STEPS = "), line(tjs, "const thStageNow = "),
                   # the step case and where the steps open, gtStepCase and thStepAt (getsB, 26 October 2026)
                   "const thStepAt = " + tjs.split("const thStepAt = ", 1)[1].split("\n};", 1)[0] + "\n};", line(tjs, "const thWhere = "),
                   "const DS_STAGES = " + app.split("const DS_STAGES = ", 1)[1].split("];", 1)[0] + "];"]
                + [whole(app, n) for n in ("dsStages", "dsTabsDraw", "dsTabsFit")]
                + [whole(tjs, n) for n in ("gtStepCase", "thStepsDraw", "thStepTo", "gtFromPets", "gtToPets", "thToStatements", "thStickyBar")]) + r"""
(async () => {
  const out = {};
  const take = () => calls.splice(0);
  const settle = () => new Promise((r) => setTimeout(r, 0));
  const tips = () => ({ at: ['th-step-es', 'th-step-pets', 'th-step-gets'].filter((id) => $(id).attrs['aria-current'] === 'page'),
    es: $('th-step-es').title, pets: $('th-step-pets').title });
  // PETs opened from the statements: Experiential statements is the way back, PETs nothing, GETs from PETs
  TH = fresh({ to: 'statements' }); thStepsDraw(); out.petsTips = tips();
  thStepTo('statements'); thStepTo('pets'); await settle(); out.petsSteps = take();
  thStepTo('gets'); await settle(); out.petsToGets = take();
  // GETs opened from the case list: PETs and Experiential statements open the case the GETs came through
  TH = fresh({ mode: 'gets', to: 'cases', label: '' }); thStepsDraw(); out.getsTips = tips();
  thStepTo('pets'); await settle(); out.getsToPets = take();
  thStepTo('statements'); await settle(); out.getsToStatements = take();
  out.how = HOW && HOW.to;
  HOW.leave(); out.left = [TH.live, $('themes').hidden];
  HOW.back(); out.reopened = take();
  // GETs opened from PETs: PETs is the way back
  TH = fresh({ mode: 'gets', to: 'pets', label: '' });
  thStepTo('pets'); thStepTo('gets'); await settle(); out.getsBackToPets = take();
  // a canvas that cannot be saved stays, and a busy one does nothing
  TH = fresh({ to: 'cases' }); DIRTY_AFTER = true; thStepTo('statements'); await settle(); out.unsaved = take(); DIRTY_AFTER = false;
  TH = fresh({ busy: true }); thStepTo('gets'); thStepTo('statements'); await settle(); out.busy = take();
  // New sticky note: the middle of the canvas, clear of the Inspector lying over it and of the Cases panel at its left
  TH = fresh({}); thStickyBar(); out.middle = take();
  Object.assign($('th-side'), { hidden: false, offsetWidth: 360, getBoundingClientRect: () => ({ left: 640, right: 1000 }) });
  thStickyBar(); out.beside = take();
  Object.assign($('th-cpanel'), { hidden: false, offsetWidth: 300, getBoundingClientRect: () => ({ left: 0, right: 300 }) });
  thStickyBar(); out.between = take();
  // a sidebar beside the canvas at a desk width, which the canvas narrows for, leaves the middle where it is
  STAGE = { left: 300, top: 46, width: 340, height: 700, right: 640 };
  thStickyBar(); out.desk = take();
  TH = fresh({ live: false }); thStickyBar(); out.notLive = take();
  console.log(JSON.stringify(out));
})().catch((e) => { console.error(String(e && e.stack || e)); process.exit(1); });
"""
        script = scratch / "board-steps-177.js"
        script.write_text(support.i18n_js() + harness, encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        o = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
        book = "walks/P1 Ada/P1 Ada - EN & ES.xlsx"
        check("177: in node, on PETs opened from the statements PETs "
              "is marked, Experiential statements is the way back, PETs does nothing and GETs opens the project's GETs "
              "with the way back to this board",
              o.get("petsTips") == {"at": ["th-step-pets"], "es": "Experiential statements for this participant", "pets": "PETs for this participant"}
              and o.get("petsSteps") == [["themesBack"]]
              and o.get("petsToGets") == [["gets", book, "pets", "", None, "function", None]], (run.stdout + run.stderr)[:400])
        check("177: in node, on GETs opened from the case list GETs is marked and the other steps name the case they open, "
              "PETs opens its PETs with the way back to this GETs board, and Experiential statements opens its "
              "statements, the board put away as a passage puts it away, the way back reopening the board as he left it",
              o.get("getsTips") == {"at": ["th-step-gets"],
                                    "es": "Experiential statements for Ada", "pets": "PETs for Ada"}
              and o.get("getsToPets") == [["pets", book, "gets", "", None, "function", None]]
              and o.get("getsToStatements") == [["statements", book, "gets"]] and o.get("how") == "gets"
              and o.get("left") == [False, True] and o.get("reopened") == [["gets", book, "cases", "", "v2", "function", 0.75]],
              str([o.get("getsTips"), o.get("getsToPets"), o.get("getsToStatements"), o.get("reopened")]))
        check("177: in node, on GETs opened from PETs PETs is the way back, a canvas that "
              "cannot be saved stays open saying so, and a busy canvas does nothing",
              o.get("getsBackToPets") == [["themesBack"]]
              and o.get("unsaved") == [["say", "The canvas is not saved yet, so it stays open."]] and o.get("busy") == [],
              str([o.get("getsBackToPets"), o.get("unsaved"), o.get("busy")]))
        check("177: in node, New sticky note makes its note the canvas's own, in no PET, in the middle of the canvas in "
              "view, clear of the Inspector and the Cases panel where they lie over it, the middle left alone where the "
              "canvas narrows for them, and nothing while the board is not live",
              o.get("middle") == [["sticky", 500, 396, True]] and o.get("beside") == [["sticky", 320, 396, True]]
              and o.get("between") == [["sticky", 470, 396, True]] and o.get("desk") == [["sticky", 470, 396, True]]
              and "const gid = opts.free ? null : thFrameAt(v, TH.layout, at, null);" in fn(tjs, "thStickyNew")
              and o.get("notLive") == [], str([o.get("middle"), o.get("beside"), o.get("between"), o.get("desk")]))

