"""Area 201: the PETs and GETs boards' status bar and palette (Adam, 19 October 2026, A of the drawings).

Adam, about 16:05, choosing A: one status bar along the foot of the PETs and GETs boards, its left the
board's counts in plain words, picked by a right click, its right the pointer and the hand, the zoom, Fit
all, the map's button and Shortcuts, on or off from View and from Settings, View, kept across a restart. A
vertical palette floating at the canvas's left edge, movable by its grip and its place kept: Sticky note and
Group, then Undo and Redo. The title bar keeps the rest.

The checks here hold behaviour: the settings file keeping the bar on or off, its counts and the palette's
place across a restart, the counts right after a stack, a move and a bin, in node, and the palette's place
where a drag lets go, and since 26 October 2026 the order the bar gives way in as it runs short, the counts last.
Words, layout and colour go to Adam as review shots, so nothing here pins them. The
fixture is an invented board about learning to swim as an adult.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess

from . import support
from .support import check, skip
import idiograph_routes


def test_status_bar_and_palette(scratch):
    print("\n201. The boards' status bar along the foot, its counts picked by a right click, and the palette of Sticky "
          "note, Group, Undo and Redo, both kept across a restart (Adam, 19 October)")
    import server as server_mod

    # ── the settings file: the bar on a new install, off and its counts and the palette's place kept
    cfg = scratch / "status-config.json"
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Adam"}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, None
        server_mod.STATE_MEMORY = {"recent": []}
        fresh = server_mod.merge_config({})
        check("201: on a new install the status bar is on with every count, and the palette has no place kept, which "
              "is its place at the left",
              fresh["status_bar"] is True and fresh["status_counts"] == ["pets", "placed", "stacked", "binned", "unplaced", "loose"]
              and fresh["palette_place"] is None, str({k: fresh[k] for k in ("status_bar", "status_counts", "palette_place")}))

        server_mod.api_settings({"status_bar": False})
        server_mod.api_settings({"status_counts": ["stacked", "unplaced", "placed", "unplaced", "nothing"]})
        server_mod.api_settings({"palette_place": {"edge": "right", "y": 0.62}})
        saved = json.loads(cfg.read_text(encoding="utf-8"))
        restarted = server_mod.merge_config(saved)
        check("201: the bar turned off, its counts picked and the palette moved are each kept in the settings file, "
              "the interviewer beside them, and read back so after a restart, the counts each once in the bar's order",
              saved.get("status_bar") is False and saved.get("interviewer") == "Adam"
              and restarted["status_bar"] is False and restarted["status_counts"] == ["placed", "stacked", "unplaced"]
              and restarted["palette_place"] == {"edge": "right", "y": 0.62}, str(saved))

        server_mod.api_settings({"status_bar": True, "palette_place": None})
        back = server_mod.merge_config(json.loads(cfg.read_text(encoding="utf-8")))
        odd = server_mod.merge_config({"status_bar": "no", "status_counts": "pets", "palette_place": {"edge": "top", "y": 2}})
        clamped = idiograph_routes.palette_place({"edge": "left", "y": 7})
        check("201: on again, and the palette's place given up, it is back at the left, and a settings file holding "
              "anything else reads as a new install's, a place past the foot held at the foot",
              back["status_bar"] is True and back["palette_place"] is None and back["status_counts"] == ["placed", "stacked", "unplaced"]
              and odd["status_bar"] is True and odd["status_counts"] == ["pets", "placed", "stacked", "binned", "unplaced", "loose"]
              and odd["palette_place"] is None and clamped == {"edge": "left", "y": 1.0}, f"{back} {odd} {clamped}")
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    # ── in node: the counts after a stack, a move and a bin, and where the palette lands
    node = shutil.which("node")
    if not node:
        skip("201: the counts and the palette in node", "node is not installed")
        return
    js = support.text("apps/idiograph/static/themes.js")
    script = scratch / "status-bar-201.js"
    script.write_text(support.i18n_js() + STUBS + js + SCENARIO, encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=120)
    if run.returncode != 0:
        check("201: the counts and the palette run in node", False, run.stderr.strip()[:600])
        return
    o = json.loads(run.stdout)
    check("201: in node, the PETs board's counts in words: the PETs at the top level, the statements in them, those "
          "stacked, set aside and not placed",
          o["start"] == ["2 PETs", "3 in PETs", "0 stacked", "0 set aside", "2 not placed"], str(o["start"]))
    check("201: in node, right after a stack the statement stacked leaves In PETs for Stacked, its top standing for it",
          o["stack"] == ["2 PETs", "2 in PETs", "1 stacked", "0 set aside", "2 not placed"], str(o["stack"]))
    check("201: in node, right after a move into a PET, one fewer not placed and one more in PETs",
          o["move"] == ["2 PETs", "3 in PETs", "1 stacked", "0 set aside", "1 not placed"], str(o["move"]))
    check("201: in node, right after a bin, the last not placed is binned",
          o["bin"] == ["2 PETs", "3 in PETs", "1 stacked", "1 set aside", "0 not placed"], str(o["bin"]))
    check("201: in node, the bar draws the counts the settings pick, in its order, with no total while a stacked "
          "statement is in no count picked (area 264), and with the bar off it shows none and the canvas loses its status class",
          o["drawn"] == ["sum", "placed", "binned"] and o["drawnText"] == "ES: 3 in PETs, 1 set aside"
          and o["off"] == {"text": "", "on": False}, str({k: o[k] for k in ("drawn", "drawnText", "off")}))
    check("201: in node, the GETs board counts GETs and the cards in them, a participant note never one, and has no "
          "stacked count",
          o["gets"] == ["1 GET", "1 in GETs", "0 set aside", "1 not placed"], str(o["gets"]))
    check("201: in node, a palette let go nearer the right edge settles against it, nearer the left against that, "
          "its top kept as a share of the room, held between the top and the foot",
          o["drop"] == [{"edge": "right", "y": 0.5}, {"edge": "left", "y": 0}, {"edge": "left", "y": 1}], str(o["drop"]))
    check("201: in node, a place kept in the settings is where it is drawn, and none puts it at the left",
          o["placed"] == {"right": True, "left": "", "rightPx": "16px", "top": "220px"}
          and o["home"]["right"] is False and o["home"]["left"] == "16px", str({k: o[k] for k in ("placed", "home")}))

    # ── the bar's steps as it runs short (Adam, 26 October 2026): the tools' words first, then any count beyond the
    # total and its parts, the tools, and the counts last, Canvas and Table never; area 269 sees it in a browser
    steps_src = js.split("const TH_STATUS_STEPS = ", 1)[1].split(";\n", 1)[0] if "const TH_STATUS_STEPS = " in js else ""
    steps = re.findall(r"'(th-status-[a-z]+)'", steps_src)
    hides = {}
    for head, decls, _at in support.css_rules(support.text("apps/idiograph/static/themes.css")):
        if not any(p == "display" and v == "none" for p, v, _ in decls):
            continue
        for sel in head.split(","):
            for step in re.findall(r"\.(th-status-[a-z]+)\b", sel):
                hides.setdefault(step, []).append(sel.strip())
    counted = lambda sel: any(k in sel for k in (".th-stat-total", ".th-part", 'data-stat="pets"', "th-stat-unit"))
    last = steps.index("th-status-trim") if "th-status-trim" in steps else -1
    check("201: the status bar gives way in Adam's order, the tools' words first, then the counts beyond the total and its "
          "parts, the tools, and only then the PETs and the total with its parts, no step before that hiding a count of "
          "the sentence, and none ever hiding Canvas and Table",
          steps[:2] == ["th-status-short", "th-status-opt"] and last > 2 and steps[last:] == ["th-status-trim", "th-status-least", "th-status-bare"]
          and not any(counted(sel) for step in steps[:last] for sel in hides.get(step, []))
          and not any("faces" in sel or "th-from" in sel for step in steps for sel in hides.get(step, []))
          and any("th-btn-word" in sel for sel in hides.get("th-status-short", []))
          and all(any(f'data-stat="{s}"' in sel for sel in hides.get("th-status-opt", [])) for s in ("selected", "close")),
          str({"steps": steps, "hides": {k: hides.get(k) for k in steps[:last]}})[:700])


STUBS = r"""
// just enough page for the status bar and the palette: elements that keep what is written to them
const ELS = {};
class El {
  constructor(id) {
    this.id = id; this.cls = new Set(); this.attrs = {}; this.hidden = false; this.innerHTML = ''; this.title = '';
    this.dataset = {}; this.offsetWidth = 40; this.offsetHeight = 160;
    const self = this;
    this.style = { setProperty: () => {} };
    this.classList = { add: (...n) => n.forEach((x) => self.cls.add(x)), remove: (...n) => n.forEach((x) => self.cls.delete(x)),
      contains: (n) => self.cls.has(n),
      toggle: (n, on) => { if (on === undefined) on = !self.cls.has(n); if (on) self.cls.add(n); else self.cls.delete(n); return on; } };
  }
  get textContent() { return String(this.innerHTML).replace(/<[^>]*>/g, ''); }
  set textContent(v) { this.innerHTML = String(v); }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  querySelector() { return ELS.bar; }
}
const $ = (id) => ELS[id] || null;
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const say = () => {};
globalThis.localStorage = { getItem: () => null, setItem: () => {} };
globalThis.window = { innerWidth: 1280, innerHeight: 800, matchMedia: () => ({ matches: false }) };
globalThis.requestAnimationFrame = () => 0;
globalThis.cancelAnimationFrame = () => {};
globalThis.setTimeout = () => 0;
globalThis.clearTimeout = () => {};
globalThis.document = { elementFromPoint: () => null };
"""

SCENARIO = r"""
const out = {};
for (const id of ['th-status-counts', 'th-palette']) ELS[id] = new El(id);
ELS['th-stage'] = Object.assign(new El('th-stage'), { clientWidth: 1000, clientHeight: 600 });
ELS.bar = Object.assign(new El('bar'), { offsetHeight: 30 });
thCorners = () => {};
thMapPlace = () => {};
const card = (text) => ({ x: 0, y: 0, text });
const v = { cards: { a: card('Floating at last'), b: card('Floating, finally'), c: card('The deep end'),
                     d: card('Week two'), e: card('Chlorine on the bus') },
            groups: [{ id: 'g1', label: 'Trusting the water', members: ['a', 'b'] },
                     { id: 'g2', label: 'Others watching', members: ['g3'] },
                     { id: 'g3', label: 'The oldest in the class', members: ['c'] }],
            discarded: [], stacks: {} };
TH.mode = 'pets';
const said = () => thStatusWords(thStatusNumbers(v, false), false).map((w) => w[1]);
out.start = said();
thStackOnto(v, ['b'], 'a'); out.stack = said();
thJoin(v, ['d'], 'g1'); out.move = said();
thDiscard(v, ['e']); out.bin = said();

TH.v = v;
TH.config = { status_bar: true, status_counts: ['binned', 'placed'] };
thStatusDraw();
const box = ELS['th-status-counts'];
out.drawn = [...box.innerHTML.matchAll(/data-stat="([a-z]+)"/g)].map((m) => m[1]);
out.drawnText = box.textContent;
TH.config.status_bar = false;
thStatusDraw();
out.off = { text: box.textContent, on: ELS['th-stage'].classList.contains('th-status-on') };

const g = { cards: { 'Ada/1': card('Routine kept'), 'Ada/2': card('A quiet house'), 'Ada/n': Object.assign(card('A note'), { kind: 'pn' }) },
            groups: [{ id: 'G1', label: 'Held by a routine', members: ['Ada/1', 'Ada/n'] }], discarded: [] };
out.gets = thStatusWords(thStatusNumbers(g, true), true).map((w) => w[1]);

const room = { top: 16, span: 400 };
out.drop = [thPaletteDrop(700, 216, 40, 1000, room), thPaletteDrop(100, 0, 40, 1000, room), thPaletteDrop(460, 900, 40, 1000, room)];
TH.config = { palette_place: { edge: 'right', y: 0.5 } };
thPalettePlace();
const pal = ELS['th-palette'];
out.placed = { right: pal.classList.contains('right'), left: pal.style.left, rightPx: pal.style.right, top: pal.style.top };
TH.config = {};
thPalettePlace();
out.home = { right: pal.classList.contains('right'), left: pal.style.left };
console.log(JSON.stringify(out));
"""
