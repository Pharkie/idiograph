"""Area 304: quotes on cards in three ways, Off, Short and Full (Adam, 30 October 2026: "the quotes button maybe has
three states: no quotes, two line quotes and then full quotes ... full quotes on each card without having to click
anything additional").

The status bar's Quotes takes the next of Off, Short and Full on each click (A), or with `TH_QUOTES_CONTROL` set to
'menu' opens a menu of the three (B). Short is the quote as before, three lines at most, its whole in its tooltip and
a click away. Full is the whole quote on its card, every piece, nothing to click. Full is kept as `card_quotes_full`
beside `card_quotes`, so an older file reads as Off or Short, and the canvas makes room for the taller cards as it
does for short quotes, a view the file never keeps.

The checks hold behaviour: what each way draws on a card, the cycle and the menu each saving the way in one write, the
way read back the same after a restart, Full kept only while the quotes are on, and the frames of a PET and its
sub-PET growing for Full as far as the tallest quote asks, nothing overlapping, and coming back for Short and Off, the
file's places never moving. Words, colour and the button's mark go to Adam as review shots. The fixtures are invented,
about keeping bees in a city garden.
"""
from __future__ import annotations

import json
import shutil
import subprocess

from . import support
from .support import check, skip
from .a205_card_quotes_and_by_participant import STUBS

SCENARIO = r"""
(async () => {
const out = {};
for (const id of ['th-quotes-btn', 'th-kqpop', 'th-qmenu', 'th-stage', 'th-status', 'th-status-counts']) ELS[id] = new El(id);
ELS['th-qmenu'].hidden = true;
ELS['th-kqpop'].hidden = true;
thPlayerDraw = () => {}; thPanelFollow = () => {}; thDrawSel = () => {}; thEase = () => {}; thSoon = () => {};
thMomentum = () => {}; thVmenu = () => {}; thCorners = () => {}; thMapPlace = () => {};
const edited = [];
thCardEditOpen = (key) => { edited.push(key); };
TH.live = true;
TH.mode = 'pets';
TH.sheets = ['Initial'];
const button = () => { const b = ELS['th-quotes-btn']; return [b.dataset.quotes, b.attrs['aria-pressed'], b.title]; };

// ── what each way draws on a card, a quote in two pieces
const card = (text, x, y) => ({ x, y, text, time: '3:10', sheet: 'Initial' });
const v = { cards: { 'Initial:4:0': card('Lifting the lid for the first time', 0, 0), 'Initial:6:0': card('Smoke and patience', 240, 0) },
            groups: [], discarded: [], stacks: {} };
const WORDS = 'the first time I lifted the lid I could feel them through the gloves … and I thought, they are going to decide whether I stay, not me, and that is still how it feels every spring when the hive wakes up';
TH.quotes = { 'Initial:4': { time: '3:10', seconds: 190, quotes: [{ key: 'Initial:4:0', text: `"${WORDS}"` }] } };
const drawn = (config) => { TH.config = config; return { way: thQuotesWay(), html: thKqHtml(v, 'Initial:4:0'), none: thKqHtml(v, 'Initial:6:0') }; };
out.drawn = {
  off: drawn({ card_quotes: false }),
  short: drawn({ card_quotes: true }),
  full: drawn({ card_quotes: true, card_quotes_full: true }),
  fullOff: drawn({ card_quotes: false, card_quotes_full: true }),
  whole: `‘${WORDS}’`,
};
// on GETs a PET unfolded in place shows its statements' quotes whole at Full too
TH.mode = 'gets';
TH.gets = { cases: [{ case: 'Ivo', pets: [{ id: 'g1', title: 'Learning the hive', statements: ['Initial:4:0'], subs: [] }],
  lines: { 'Initial:4:0': { text: 'Lifting the lid for the first time', sheet: 'Initial', time: '3:10', quotes: [`"${WORDS}"`] } } }] };
const pet = { kind: 'pet', case: 'Ivo', text: 'Learning the hive', x: 0, y: 0 };
TH.config = { card_quotes: true };
const unfoldShort = gtUnfoldHtml('Ivo/g1', pet);
TH.config = { card_quotes: true, card_quotes_full: true };
const unfoldFull = gtUnfoldHtml('Ivo/g1', pet);
out.unfold = { short: /class="gt-uq" title=/.test(unfoldShort) && !unfoldShort.includes('gt-uq-full'),
               full: unfoldFull.includes('class="gt-uq gt-uq-full"') && !/gt-uq-full" title=/.test(unfoldFull) && unfoldFull.includes(out.drawn.whole) };
TH.mode = 'pets';

// ── a click on the quote: Short shows it whole beside the card, Full is a click on the card, two of them editing
TH.v = v;
TH.els = { cards: { 'Initial:4:0': new El('c') }, under: {}, labels: {}, frames: {}, stickies: {}, rails: {} };
TH.config = { card_quotes: true };
TH.press = { item: { kind: 'card', id: 'Initial:4:0' }, x0: 0, y0: 0, add: false, alt: false, kq: true };
thPointerUp({ pointerId: 1, clientX: 0, clientY: 0 });
out.click = { shortPop: TH.kqpop, shortEdits: edited.length };
thKqClose();
TH.config = { card_quotes: true, card_quotes_full: true };
TH.lastClick = null;
for (let i = 0; i < 2; i += 1) {
  TH.press = { item: { kind: 'card', id: 'Initial:4:0' }, x0: 0, y0: 0, add: false, alt: false, kq: false };
  thPointerUp({ pointerId: 1, clientX: 0, clientY: 0 });
}
Object.assign(out.click, { fullPop: TH.kqpop, fullEdits: edited.slice(), selected: [...TH.sel.cards] });

// ── the button: each click the next way, saved at once in one write
TH.v = null;
SAVED.length = 0;
TH.config = { card_quotes: false };
thQuotesButton();
const states = [button()];
const menus = [];
for (let i = 0; i < 3; i += 1) { thQuotesToggle(); await Promise.resolve(); states.push(button()); menus.push(!ELS['th-qmenu'].hidden); }
out.cycle = { saved: SAVED.slice(), states, menus, control: TH_QUOTES_CONTROL };
thQuotesMenu(false);
// the menu, from a right click in A: the three, the one in use ticked, a choice kept at once and the menu still open
SAVED.length = 0;
TH.config = { card_quotes: true };
thQuotesMenu(true, 600, 760);
const menu = ELS['th-qmenu'];
const rows = (html) => [...html.matchAll(/data-qway="(\w+)"/g)].map((m) => m[1]);
const ticked = (html) => [...html.matchAll(/aria-checked="true" tabindex="-1" data-qway="(\w+)"/g)].map((m) => m[1]);
const was = { open: !menu.hidden, rows: rows(menu.innerHTML), ticked: ticked(menu.innerHTML) };
thQuotesSet('full');
await Promise.resolve();
out.menu = Object.assign(was, { saved: SAVED.slice(), after: ticked(menu.innerHTML), still: !menu.hidden, way: thQuotesWay() });
thQuotesMenu(false);
out.menu.closed = menu.hidden;
// Esc puts it away, through the canvas's own keys, which stop every key before the document hears it
for (const id of ['themes', 'th-confirm', 'th-aicard']) ELS[id] = new El(id);
ELS['th-confirm'].hidden = true;
ELS['th-aicard'].hidden = true;
if (typeof anyOverlayOpen === 'undefined') globalThis.anyOverlayOpen = () => false;
if (typeof REDO_Y === 'undefined') globalThis.REDO_Y = () => false;
thQuotesMenu(true);
const opened = !menu.hidden;
thKeyDown({ key: 'Escape', target: { closest: () => null }, preventDefault() {}, stopPropagation() {} });
out.menu.esc = { opened, after: !menu.hidden, state: TH.qmenu };

// ── the frames: a PET over a sub-PET of three side by side, a statement under the sub-PET and a card below the PET
const board = { cards: {
    'Initial:20:0': card('Bees on the bus home in a shoebox', 40, 60),
    'Initial:21:0': card('The neighbours asking about stings', 60, 220),
    'Initial:22:0': card('Watching the entrance after work', 300, 220),
    'Initial:23:0': card('Honey on the kitchen floor', 540, 220),
    'Initial:30:0': card('A second hive by the summer', 40, 440),
    'Initial:40:0': card('Giving jars away at Christmas', 0, 800) },
  groups: [{ id: 'g1', label: 'A colony on the roof', members: ['Initial:20:0', 'g2', 'Initial:30:0'], x: 20, y: 20 },
           { id: 'g2', label: 'Learning to be watched', members: ['Initial:21:0', 'Initial:22:0', 'Initial:23:0'], x: 40, y: 180 }],
  discarded: [], stacks: {} };
// each card 220 by 80 with no quote, and the quotes' share of it at Short and at Full as the page measures it
const EXTRA = { short: { 'Initial:21:0': 50, 'Initial:22:0': 50, 'Initial:23:0': 34 },
                full: { 'Initial:21:0': 50, 'Initial:22:0': 190, 'Initial:23:0': 120 } };
const measure = () => {
  TH.sizes = { g1: { w: 170, h: 26 }, g2: { w: 180, h: 26 } };
  for (const k of Object.keys(board.cards)) TH.sizes[k] = { w: 220, h: 80 };
  TH.qfull = {}; TH.qextra = {}; TH.baseH = {};
  const way = thQuotesWay();
  if (way === 'off') return;
  for (const [k, d] of Object.entries(EXTRA[way])) { TH.qfull[k] = 80 + d; TH.qextra[k] = d; TH.sizes[k] = { w: 220, h: 80 + d }; }
};
thRender = () => { measure(); thStacksRoom(); TH.layout = thLayout(TH.v, thSize, null); };
TH.v = JSON.parse(JSON.stringify(board));
TH.opened = new Set(); TH.shifts = []; TH.roomShown = null; TH.removed = new Set();
TH.els = { cards: {}, under: {}, labels: {}, frames: {}, stickies: {}, rails: {} };
const file = JSON.stringify(board.cards);
const look = () => {
  const l = thLayout(TH.v, thSize, null);
  const frame = (g) => [Math.round(l[g].frame.y), Math.round(l[g].frame.y + l[g].frame.h)];
  const kept = thUnshifted(TH.v);
  return { g1: frame('g1'), g2: frame('g2'), below: Math.round(TH.v.cards['Initial:30:0'].y), outside: Math.round(TH.v.cards['Initial:40:0'].y),
           clashes: thClashes(TH.v, thSize).length, file: JSON.stringify(kept.cards) === file };
};
const frames = {};
for (const way of ['off', 'short', 'full', 'short', 'off']) {
  TH.config = { card_quotes: way !== 'off', card_quotes_full: way === 'full' };
  thRender();
  frames[frames[way] ? `${way}Again` : way] = look();
}
out.frames = frames;
console.log(JSON.stringify(out));
})().catch((err) => { console.error(err && err.stack ? err.stack : String(err)); process.exit(1); });
"""

# the settings read back after a restart, each handed to the page as it opens: the way and the button
READBACK = r"""
(() => {
ELS['th-quotes-btn'] = new El('th-quotes-btn');
const out = [];
for (const config of CONFIGS) {
  TH.config = config;
  thQuotesButton();
  const b = ELS['th-quotes-btn'];
  out.push([thQuotesWay(), b.dataset.quotes, b.attrs['aria-pressed']]);
}
console.log(JSON.stringify(out));
})();
"""


def run_node(node, scratch, name, code):
    script = scratch / name
    script.write_text(code, encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=120)
    if run.returncode != 0:
        return None, run.stderr.strip()[:800]
    return support.plain(json.loads(run.stdout)), ""


def test_quotes_three_ways(scratch):
    print("\n304. Quotes on cards in three ways, Off, Short and Full: what each draws, the button's cycle and its menu, "
          "the way kept across a restart, and the frames growing for whole quotes and coming back (Adam, 30 October)")
    import server as server_mod

    # ── the setting: Off on a new install, Full kept beside the quotes on, anything but true read as false
    cfg = scratch / "quotes-three-config.json"
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Adam"}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, None
        server_mod.STATE_MEMORY = {"recent": []}
        fresh = server_mod.merge_config({})
        before = server_mod.merge_config({"card_quotes": True})
        odd = server_mod.merge_config({"card_quotes": True, "card_quotes_full": "yes"})
        check("304: Full is off on a new install, a settings file from before with the quotes on reads as Short, and "
              "anything but true reads as not Full",
              fresh["card_quotes"] is False and fresh["card_quotes_full"] is False and before["card_quotes"] is True
              and before["card_quotes_full"] is False and odd["card_quotes_full"] is False,
              str({"fresh": fresh.get("card_quotes_full"), "before": before.get("card_quotes_full"), "odd": odd.get("card_quotes_full")}))

        node = shutil.which("node")
        if not node:
            skip("304: the three ways in node", "node is not installed")
            return
        js = support.text("apps/idiograph/static/themes.js")
        o, err = run_node(node, scratch, "quotes-three-304.js", support.i18n_js() + STUBS + js + SCENARIO)
        if o is None:
            check("304: the three ways run in node", False, err)
            return
        d = o["drawn"]
        whole = d["whole"]
        check("304: in node, Off draws no quote, Short the quote clamped as before with its whole in its tooltip and a "
              "click away, and Full the whole quote, both pieces and the ellipsis it was saved with, with no tooltip "
              "and nothing to click, a card with no quote showing none in every way, and Full without the quotes on Off",
              d["off"] == {"way": "off", "html": "", "none": ""}
              and d["short"]["way"] == "short" and d["short"]["html"].startswith('<p class="th-kq" data-kq="1" title=')
              and whole in d["short"]["html"] and "th-kq-full" not in d["short"]["html"] and d["short"]["none"] == ""
              and d["full"]["way"] == "full" and d["full"]["html"] == f'<p class="th-kq th-kq-full">{whole}</p>'
              and d["full"]["none"] == "" and d["fullOff"] == {"way": "off", "html": "", "none": ""},
              json.dumps(d)[:600])
        css = support.text("apps/idiograph/static/themes.css")
        rule = css[css.index(".th-kq.th-kq-full {"):].split("}", 1)[0]
        short_rule = css[css.index(".th-kq {"):].split("}", 1)[0]
        check("304: the stylesheet clamps a Short quote and lifts the clamp for a Full one",
              "-webkit-line-clamp: 3" in short_rule and "-webkit-line-clamp: none" in rule and "display: block" in rule,
              rule)
        check("304: in node, on GETs a PET unfolded in place shows its statements' quotes clamped, and whole at Full",
              o["unfold"] == {"short": True, "full": True}, str(o["unfold"]))
        check("304: in node, at Short a click on the quote shows it whole beside the card, and at Full a click on it "
              "selects the card and two edit its statement, as on its words, with no quote shown beside it",
              o["click"] == {"shortPop": "Initial:4:0", "shortEdits": 0, "fullPop": None, "fullEdits": ["Initial:4:0"],
                             "selected": ["Initial:4:0"]}, str(o["click"]))
        c = o["cycle"]
        check("304: in node, each click on the button takes the next of Off, Short and Full and back to Off, each saved "
              "at once in one write of both settings, the button pressed in for Short and Full and its tooltip saying which",
              c["control"] == "cycle" and c["saved"] == [{"card_quotes_full": False, "card_quotes": True},
                                                         {"card_quotes_full": True, "card_quotes": True},
                                                         {"card_quotes_full": False, "card_quotes": False}]
              and c["states"] == [["off", "false", "Quotes: off"], ["short", "true", "Quotes: short"],
                                  ["full", "true", "Quotes: full"], ["off", "false", "Quotes: off"]], json.dumps(c))
        m = o["menu"]
        check("304: in node, the menu holds Off, Short and Full, the one in use ticked, a choice saved at once and "
              "ticked with the menu still open, it closes, and Esc on the canvas puts it away",
              m == {"open": True, "rows": ["off", "short", "full"], "ticked": ["short"],
                    "saved": [{"card_quotes_full": True, "card_quotes": True}], "after": ["full"], "still": True,
                    "way": "full", "closed": True, "esc": {"opened": True, "after": False, "state": False}}, json.dumps(m))

        # ── kept across a restart: each write the cycle made, saved as the server saves it and read back
        configs = []
        for body in c["saved"]:
            server_mod.api_settings(body)
            configs.append(server_mod.merge_config(json.loads(cfg.read_text(encoding="utf-8"))))
        back, err = run_node(node, scratch, "quotes-three-back-304.js", support.i18n_js() + STUBS + js
                             + f"\nconst CONFIGS = {json.dumps([{k: x[k] for k in ('card_quotes', 'card_quotes_full')} for x in configs])};\n"
                             + READBACK)
        check("304: each way the button saved is read back the same after a restart, the button drawn in it",
              back == [["short", "short", "true"], ["full", "full", "true"], ["off", "off", "false"]], str(back or err))

        # ── B: the button itself opens the menu
        way_b = js.replace("const TH_QUOTES_CONTROL = 'cycle';", "const TH_QUOTES_CONTROL = 'menu';", 1)
        ob, err = run_node(node, scratch, "quotes-three-b-304.js", support.i18n_js() + STUBS + way_b + SCENARIO)
        check("304: in node, with the control set to B a click on the button opens the menu and saves nothing, a "
              "second click closes it and a third opens it again, and in A a click never opens it",
              ob is not None and ob["cycle"]["control"] == "menu" and ob["cycle"]["saved"] == []
              and ob["cycle"]["menus"] == [True, False, True] and c["menus"] == [False, False, False],
              str(ob["cycle"] if ob else err))

        f = o["frames"]
        off, short, full = f["off"], f["short"], f["full"]
        check("304: in node, with the quotes off the board is the file's, nothing overlapping",
              off["clashes"] == 0 and off["file"], json.dumps(off))
        check("304: in node, at Short the sub-PET's frame grows by its tallest short quote, and the statement under it "
              "and the card below the PET move down as far, nothing overlapping, the file's places unmoved",
              short["g2"][1] - off["g2"][1] == 50 and short["below"] - off["below"] == 50
              and short["outside"] - off["outside"] == 50 and short["g1"][1] - off["g1"][1] == 50
              and short["clashes"] == 0 and short["file"], json.dumps(short))
        check("304: in node, at Full the frames grow by the tallest whole quote in the row, never the sum of them, "
              "what stands below moving as far, nothing overlapping, the file's places unmoved",
              full["g2"][1] - off["g2"][1] == 190 and full["below"] - off["below"] == 190
              and full["outside"] - off["outside"] == 190 and full["g1"][1] - off["g1"][1] == 190
              and full["g2"][0] == off["g2"][0] and full["clashes"] == 0 and full["file"], json.dumps(full))
        check("304: in node, back to Short and then Off the frames and the cards return to where they stood",
              f["shortAgain"] == short and f["offAgain"] == off, json.dumps(f))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
