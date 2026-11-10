"""Area 203: Back and Forward on Distil's screens (19 October 2026, Adam in his Mac app: the mouse's back button
on a passage opened from a PETs card took him nowhere).

Every way in that gives a Distil screen its way back is an entry of its own in the browser's history, so the
browser's Back, a mouse's back button and Cmd + [ do what the bar's way back does, and the arrow is Back
itself. Forward after a Back takes the same way in again from the screen Back came to, and does nothing where
that screen is no longer the one it was taken from. The Mac app's window takes the mouse's buttons 3 and 4
before its web view, which gives the page no such buttons, and steps the page's history, and its page script
takes Cmd + [ and Cmd + ].

The checks hold behaviour, in node, on the page's own functions with the browser's history stubbed as a
browser has it, its popstate after the move: from a passage opened from a PETs card Back returns to that
board and its selection, saving what was typed, Forward opens the passage again, a GETs row's passage comes
back to GETs, the home screen's ways in come back home, a refused way back keeps the screen, and a Forward
from another screen does nothing. Invented cases about learning to swim as an adult.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from . import support
from .support import check, skip


def test_back_and_forward(scratch):
    print("\n203. Back and Forward on Distil's screens: Back from a passage opened from a PETs card or a GETs row comes back "
          "to that board as it was, what was typed saved, Forward opens the passage again, and the Mac app's window "
          "takes the mouse's back and forward buttons and Cmd + [ and Cmd + ] (19 October)")
    tauri = support.source("packaging/tauri")
    read = lambda path: Path(path).read_text(encoding="utf-8")
    app, tjs = support.text("family/static/shell.js", "apps/idiograph/static/distil.js"), support.text("apps/idiograph/static/themes.js")
    shell, window_js = read(tauri / "src-tauri" / "src" / "main.rs"), read(tauri / "window.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: (("async " if f"async function {name}(" in src else "") + f"function {name}(" + fn(src, name) + "\n}")
    line = lambda src, start: start + src.split(start, 1)[1].split("\n", 1)[0] if start in src else ""

    # ── the Mac app's window
    monitor = shell.split("pub fn mouse_buttons(", 1)[1].split("\n    }\n", 1)[0] if "pub fn mouse_buttons(" in shell else ""
    check("203: the Mac app takes a mouse's buttons 3 and 4 before its web view, as Back and Forward of the page's history "
          "in the window they are pressed over, every other button going on as it came, and it is set up as the app starts",
          "addLocalMonitorForEventsMatchingMask: OTHER_MOUSE" in monitor and '3 => "back",' in monitor
          and '4 => "forward",' in monitor and "_ => return event," in monitor
          and 'window.eval(format!("window.history.{step}()"))' in monitor
          and "let _ = handle.run_on_main_thread(move || mac::mouse_buttons(&buttons));" in shell)
    keys = window_js.split("// Back and Forward on a Mac", 1)[1].split("// the window's zoom", 1)[0] if "// Back and Forward on a Mac" in window_js else ""
    check("203: in the Mac app Cmd + [ is Back and Cmd + ] Forward, with no other key held, and only on a Mac",
          "os === 'macos' && e.metaKey && !e.ctrlKey && !e.altKey && !e.shiftKey" in keys
          and "win.history.back();" in keys and "win.history.forward();" in keys and "e.preventDefault();" in keys)

    node = shutil.which("node")
    if not node:
        skip("203: Back and Forward in node", "node is not on this machine")
        return
    nav = app[app.index("const NAV_KIND = "):app.index("function navHeld(")]
    pieces = [nav, line(app, "const navSame = "), line(app, "const openCaseIn = "), line(app, "const openThemesIn = "),
              line(app, "const openGetsIn = ")]
    pieces += [whole(app, n) for n in ("navHeld", "navHere", "navGo", "navBackNow", "navWayBack", "navSteps", "navPop",
                                       "navBack", "navForward", "toLibrary", "toLibraryNow", "esStep", "openThemes", "openGets")]
    pieces += [line(tjs, "const TH_NO_PASSAGE = "), line(tjs, "const TH_STEPS = "), line(tjs, "const thStageNow = "),
               line(tjs, "const thWhere = ")]
    pieces += [whole(tjs, n) for n in ("thIsStatement", "thLineOf", "thToPassage", "thBackFromPassage", "themesBack",
                                       "themesLeave", "getsOpen", "gtFromPets")]
    harness = r"""
const calls = [];
const noop = () => {};
const els = {};
const $ = (id) => (els[id] = els[id] || { id, hidden: true, title: '', pause: noop });
$('library').hidden = false;
// the browser's history as a browser keeps it, its popstate coming after the move
const H = { stack: [{ state: null }], at: 0 };
const copy = (v) => (v === null || v === undefined ? null : JSON.parse(JSON.stringify(v)));
const fire = () => setTimeout(() => navPop({ state: copy(H.stack[H.at].state) }), 0);
const history = {
  get state() { return copy(H.stack[H.at].state); },
  get length() { return H.stack.length; },
  pushState(st) { H.stack = H.stack.slice(0, H.at + 1); H.stack.push({ state: copy(st) }); H.at += 1; },
  replaceState(st) { H.stack[H.at].state = copy(st); },
  go(n) { const to = Math.max(0, Math.min(H.stack.length - 1, H.at + n)); if (to !== H.at) { H.at = to; fire(); } },
  back() { this.go(-1); },
  forward() { this.go(1); },
};
const tick = () => new Promise((r) => setTimeout(r, 5));
const settle = async () => { for (let k = 0; k < 6; k += 1) { await tick(); await NAV.chain; } };
const say = (t) => calls.push(['say', t]);
const S = { data: null, backTo: null, dirty: false, recut: false, home: null };
let ROW = null;
const current = () => ROW;
const tpList = () => null, tpHere = () => null;
const commit = async () => { calls.push(['commit']); S.dirty = false; };
const closeFind = noop, measureBand = noop, centreCurrent = noop, focusEntry = noop, needsRestart = () => false;
const loadLibrary = async () => { for (const id of ['work', 'themes']) $(id).hidden = true; $('library').hidden = false; S.backTo = null; calls.push(['home']); };
const openCase = async (path) => { await tick(); S.backTo = null; S.data = { path, name: path }; ROW = { sheet: 'Initial', row: 3 }; $('library').hidden = true; $('work').hidden = false; calls.push(['case', path]); };
const esToGets = async () => calls.push(['esToGets']);
// a passage opened from a board, as openPassage opens it
let GONE = false;
const openPassage = async (path, at, how) => {
  await tick();
  if (GONE) { say('gone'); return false; }
  how.leave();
  S.backTo = { back: how.back, to: how.to };
  S.data = { path, name: path };
  ROW = { sheet: at.sheet, row: at.row };
  $('work').hidden = false;
  calls.push(['passage', path, at.row]);
  return true;
};
// the boards: PETs of Wren's case, and the project's GETs, which hold Wren's and Ines's statements
const BOOK = 'swim/P1 Wren - EN & ES.xlsx';
const OTHER = 'swim/P2 Ines - EN & ES.xlsx';
const BOARDS = {
  pets: { cards: { 'Initial:5:0': { key: 'Initial:5:0' }, 'Initial:9:0': { key: 'Initial:9:0' } }, groups: [{ id: 'g1', members: [] }] },
  gets: { cards: { 'P1 - Wren/g1': { key: 'P1 - Wren/g1', kind: 'pet' } }, groups: [] },
};
const TH = { mode: 'pets', live: false, busy: false, dirty: false, path: '', label: '', back: null, to: 'cases', meta: null, v: null,
  view: { x: 0, y: 0, z: 1 }, lastPick: null, sel: { cards: new Set(), groups: new Set(), stickies: new Set() }, ask: 0 };
let REFUSE = false;
const thFlush = async () => { if (REFUSE) TH.dirty = true; };
const thTitleDone = noop, thNoteDone = noop, thVmenu = noop, thViewEnd = noop, thPile = noop, thXmenu = noop, thCasemenu = noop,
  thSideShut = noop, thAiCard = noop, thExported = noop, thMade = noop, thMenuClose = noop, thGets = () => TH.mode === 'gets';
const themesOpen = async (path, opts = {}) => {
  TH.mode = opts.gets ? 'gets' : 'pets';
  Object.assign(TH, { path, back: opts.back || null, label: opts.label || '', to: opts.to || 'cases', live: false, dirty: false });
  TH.sel = { cards: new Set(), groups: new Set(), stickies: new Set() };
  TH.view = { x: 0, y: 0, z: 1 };
  $('themes').hidden = false;
  calls.push([TH.mode, path, TH.to]);
  await tick();
  TH.live = true;
  TH.v = BOARDS[TH.mode];
  TH.meta = { id: 'v1' };
  if (opts.restore) thBackFromPassage(opts.restore);
};
const gtSplit = (key) => { const [kase, kind, ...rest] = key.split('/'); return { kase, kind, ident: rest.join('/') }; };
const gtCase = (name) => ({ 'P1 - Wren': { path: BOOK }, 'P2 - Ines': { path: OTHER } })[name] || null;
const thIsGroup = (v, id) => v.groups.some((g) => g.id === id);
const thIsSticky = () => false;
const thSelected = (item) => (item.kind === 'card' ? TH.sel.cards : TH.sel.groups).has(item.id);
const thDrawSel = noop, thPanelFollow = noop, thView = noop;
const thStage = () => ({ clientWidth: 1200, clientHeight: 700 });
const thSize = () => ({ w: 200, h: 60 });
"""
    scenario = r"""
window = { addEventListener: noop };
(async () => {
  const out = {};
  const here = () => { const h = navHere(); return [h.screen, h.path, H.at, H.stack.length]; };
  // PETs from the home screen, a way in with its entry
  await openThemesIn(BOOK, 'P1 - Wren');
  out.pets = here();
  // a card selected and the canvas moved, then its passage, as a double-click opens it
  TH.sel.cards = new Set(['Initial:5:0']);
  TH.view = { x: -80, y: 30, z: 0.7 };
  TH.lastPick = { kind: 'card', id: 'Initial:5:0' };
  await thToPassage('Initial:5:0');
  out.passage = [...here(), S.backTo && S.backTo.to, ROW && ROW.row];
  // typed into, then the mouse's back button: Back
  S.dirty = true;
  calls.splice(0);
  history.back(); await settle();
  out.back = [...here(), [...TH.sel.cards], TH.view, calls.filter((c) => c[0] === 'commit').length, TH.lastPick && TH.lastPick.id];
  // Forward: the same passage again, and nothing pushed
  history.forward(); await settle();
  out.forward = [...here(), S.backTo && S.backTo.to, ROW && ROW.row];
  // the bar's arrow is Back
  await toLibrary(); await settle();
  out.arrow = [...here(), [...TH.sel.cards]];
  // and the board's arrow, to the home screen it was opened from
  await themesBack(); await settle();
  out.home = here();
  // Forward from home opens the board again, and Forward again its passage
  history.forward(); await settle();
  out.homeForward = here();
  history.forward(); await settle();
  out.homeForward2 = [...here(), ROW && ROW.row];
  // two steps back at once, a long press on Back
  history.go(-2); await settle();
  out.twoBack = here();
  history.forward(); await settle();
  // a canvas that cannot be saved: Back keeps the board and its entry
  REFUSE = true; calls.splice(0);
  history.back(); await settle();
  out.refused = [...here(), calls.filter((c) => c[0] === 'say').length];
  REFUSE = false; TH.dirty = false;
  // Forward where the screen in front is no longer the one the way was taken from: nothing opens
  await thToPassage('Initial:5:0');
  history.back(); await settle();
  out.forwardHere = here();
  const keptPath = TH.path;
  TH.path = OTHER;
  calls.splice(0);
  history.forward(); await settle();
  out.forwardElsewhere = [...here(), calls.length];
  TH.path = keptPath;
  // GETs from the PETs bar, then a statement's row in its Cases panel
  await gtFromPets(); await settle();
  out.gets = [...here(), TH.to];
  TH.sel.cards = new Set(['P1 - Wren/g1']);
  await thToPassage('P2 - Ines/es/Initial:4:0');
  out.getsPassage = [...here(), S.backTo && S.backTo.to, ROW && ROW.row];
  history.back(); await settle();
  out.getsBack = [...here(), [...TH.sel.cards]];
  history.forward(); await settle();
  out.getsForward = [...here(), ROW && ROW.row];
  // a passage gone from the transcript: no entry and the board stays
  history.back(); await settle();
  GONE = true;
  const len = H.stack.length;
  await thToPassage('P2 - Ines/es/Initial:4:0');
  out.gone = [...here(), H.stack.length - len];
  GONE = false;
  // with no entry of its own the arrow is the way back at once
  H.stack[H.at].state = null; NAV.cur = null;
  await themesBack(); await settle();
  out.noEntry = here();
  console.log(JSON.stringify(out));
})().catch((e) => { console.error(String(e && e.stack || e)); process.exit(1); });
"""
    script = scratch / "back-and-forward-203.js"
    script.write_text(support.i18n_js() + harness + "\n".join(pieces) + scenario, encoding="utf-8")
    ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    o = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
    why = (ran.stderr or ran.stdout)[:500]
    book, other = "swim/P1 Wren - EN & ES.xlsx", "swim/P2 Ines - EN & ES.xlsx"
    check("203: in node, PETs from the home screen and a statement's passage from its card are each an entry of the "
          "browser's history, the passage's way back naming PETs",
          o.get("pets") == ["pets", book, 1, 2] and o.get("passage") == ["statements", book, 2, 3, "pets", 5], why + str(o)[:300])
    check("203: in node, Back from the passage returns to the PETs board with the card selected, the canvas where it was "
          "and the pick kept, saving what was typed on the way",
          o.get("back") == ["pets", book, 1, 3, ["Initial:5:0"], {"x": -80, "y": 30, "z": 0.7}, 1, "Initial:5:0"],
          str(o.get("back")))
    check("203: in node, Forward after Back opens the same passage again, on the entry it had, nothing pushed",
          o.get("forward") == ["statements", book, 2, 3, "pets", 5], str(o.get("forward")))
    check("203: in node, the bar's arrow is Back, the board's arrow returns to the home screen, and Forward from home opens "
          "the board again and Forward again its passage",
          o.get("arrow") == ["pets", book, 1, 3, ["Initial:5:0"]] and o.get("home") == ["home", "", 0, 3]
          and o.get("homeForward") == ["pets", book, 1, 3] and o.get("homeForward2") == ["statements", book, 2, 3, 5],
          str([o.get("arrow"), o.get("home"), o.get("homeForward"), o.get("homeForward2")]))
    check("203: in node, two steps of Back at once take the way back twice",
          o.get("twoBack") == ["home", "", 0, 3], str(o.get("twoBack")))
    check("203: in node, a canvas that cannot be saved keeps the board and its entry, saying why, and Forward from a screen "
          "that is no longer the one its way was taken from opens nothing",
          o.get("refused") == ["pets", book, 1, 2, 1] and o.get("forwardHere") == ["pets", book, 1, 3]
          and o.get("forwardElsewhere") == ["pets", other, 1, 3, 0],
          str([o.get("refused"), o.get("forwardHere"), o.get("forwardElsewhere")]))
    check("203: in node, GETs from the PETs bar is an entry, a statement's row from its Cases panel opens the passage in its "
          "own case's workbook, Back returns to the GETs board with its selection and Forward to the passage",
          o.get("gets", [None])[0] == "gets" and o.get("gets", [None] * 5)[4] == "pets"
          and o.get("getsPassage", [None])[0] == "statements" and o.get("getsPassage", [None] * 6)[1] == other
          and o.get("getsPassage", [None] * 6)[4:] == ["gets", 4]
          and o.get("getsBack", [None])[0] == "gets" and o.get("getsBack", [None] * 5)[4] == ["P1 - Wren/g1"]
          and o.get("getsForward", [None])[0] == "statements" and o.get("getsForward", [None] * 5)[4] == 4,
          str([o.get("gets"), o.get("getsPassage"), o.get("getsBack"), o.get("getsForward")]))
    check("203: in node, a passage gone from the transcript pushes no entry and leaves the board, and with no entry of its "
          "own the arrow takes the way back at once",
          o.get("gone", [None])[0] == "gets" and o.get("gone", [None] * 5)[4] == 0 and o.get("noEntry", [None])[0] == "pets",
          str([o.get("gone"), o.get("noEntry")]))
