from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import support
from .support import check, skip


def test_on_screen_controls(scratch):
    print("\n155. On screen, not behind keys, 16 October, Adam's decisions on a tester's feedback: a toolbar by the "
          "selection with Key quote and Give to another speaker, the keyboard following the selection, Group and Undo "
          "on the boards' bars, a ⋯ on a selected card, the passage's menu always in view, keys in tooltips, "
          "Appearance into Settings, one rule for every title bar, each sidebar's toggle at its own side, and the "
          "last build's fixes. Since the test review of 18 October the toolbar's look and place, the tooltips, the bars' "
          "order, the toggles' words and the fixes' styles are review shots, and what the toolbar, Group, Undo, the dots "
          "and Appearance do stays")
    import subprocess
    read = lambda path: Path(path).read_text(encoding="utf-8")
    page, app, tjs = support.page_text(), support.text("family/static/shell.js", "apps/idiograph/static/distil.js"), support.text("apps/idiograph/static/themes.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    node = shutil.which("node")
    keydown = support.keydown_text(app)

    # ── A. the toolbar by the selection
    check("155: Key quote does what q and Quote do and Give to another speaker what c does, the press keeping the "
          "selection and the focus",
          "$('sel-quote').onclick = () => commitQuote();" in app and "$('sel-give').onclick = () => assignKey();" in app
          and "else if (key === 'q' && !$('work').hidden) { e.preventDefault(); commitQuote(); }" in keydown
          and "else if (key === 'c' && !$('work').hidden) { e.preventDefault(); assignKey(); }" in keydown
          # Quote under the fields went on 17 October (172), and Key quote does its work
          and "$('btn-quote')" not in app and 'id="btn-quote"' not in page
          and "$('sel-bar').addEventListener('mousedown', (e) => e.preventDefault());" in app)
    check("155: the keyboard follows the selection, the column focusable and the focus moved out of a field, so q and "
          "c are the transcript's and never type into a statement",
          '<div class="transcript" id="transcript" tabindex="-1">' in page
          and "$('transcript').focus({ preventScroll: true });" in fn(app, "selBarShow")
          and "/TEXTAREA|INPUT/.test(focus.tagName)" in fn(app, "selBarShow")
          and keydown.index("const typing = ") < keydown.index("if (typing || MOD(e) || e.altKey) return;")
          < keydown.index("key === 'q'"))
    if not node:
        skip("155: the toolbar's place in node", "node is not on this machine")
    else:
        harness = r"""
const S = { editing: null, timeEdit: null, rowMenu: null, flat: [{ i: 0, stop: true }, { i: 1, stop: false }] };
const FOCUSED = [];
let COL = { top: 100, bottom: 700, left: 50, right: 550 };
let RECTS = [];
let ROW = 0;
const bar = { hidden: true, offsetHeight: 36, style: {},
  get offsetWidth() { const most = parseInt(this.style.maxWidth, 10); return most >= 0 && most < 300 ? most : 300; } };
const els = { work: { hidden: false }, 'sel-bar': bar, 'cols-head': { querySelector: () => null },
  transcript: { getBoundingClientRect: () => COL, tagName: 'DIV', focus() { FOCUSED.push('transcript'); document.activeElement = this; } } };
const $ = (id) => els[id];
const document = { body: { tagName: 'BODY' }, activeElement: null };
const window = { getSelection: () => ({ getRangeAt: () => ({ getClientRects: () => RECTS }) }) };
// the passage holding the selection, with no notes beside its words here (area 158 places it beside them)
const selectionTurns = () => [{ box: { closest: () => ({ dataset: { i: String(ROW) }, querySelector: () => null }) } }];
// the lines beside the selection, none here: area 182 holds the toolbar over whole lines
const selBarLines = () => [];
"""
        code = harness + "\n".join(whole(app, n) for n in ("selBarPick", "selBarRoom", "selBarSpeaker", "selBarCut", "selBarWhole", "selBarPlace", "selBarShow")) + "\n" + r"""
const r = (left, top, w, h) => ({ left, top, right: left + w, bottom: top + h, width: w, height: h });
const place = () => ({ hidden: bar.hidden, top: parseInt(bar.style.top, 10), left: parseInt(bar.style.left, 10) });
const covers = (p) => !p.hidden && RECTS.some((x) => p.left < x.right && p.left + 300 > x.left && p.top < x.bottom && p.top + 36 > x.top);
const out = {};
document.activeElement = { tagName: 'TEXTAREA' };
RECTS = [r(120, 300, 200, 24), r(60, 324, 180, 24)];
selBarShow(); out.above = place(); out.aboveCovers = covers(out.above); out.focus = FOCUSED.slice();
RECTS = [r(120, 120, 200, 24), r(60, 144, 180, 24)];
selBarShow(); out.below = place(); out.belowCovers = covers(out.below);
RECTS = [r(500, 300, 40, 24)];
selBarShow(); out.clamped = place();
COL = { top: 100, bottom: 200, left: 50, right: 550 };
RECTS = [r(120, 110, 200, 24), r(60, 134, 180, 24), r(60, 158, 180, 24)];
selBarShow(); out.nowhere = place();
COL = { top: 100, bottom: 700, left: 50, right: 550 };
RECTS = [r(120, 300, 200, 24)];
FOCUSED.length = 0; document.activeElement = document.body;
selBarShow(); out.bodyFocus = FOCUSED.slice();
ROW = 1; FOCUSED.length = 0; document.activeElement = { tagName: 'TEXTAREA' };
selBarShow(); out.aside = { hidden: bar.hidden, focus: FOCUSED.slice() };
ROW = 0; S.rowMenu = { el: {} };
selBarShow(); out.menu = bar.hidden;
S.rowMenu = null; bar.style.left = '200px';
COL = { top: 100, bottom: 700, left: 16, right: 314 };
RECTS = [r(140, 446, 160, 24)];
selBarShow(); out.narrow = { ...place(), most: bar.style.maxWidth, right: parseInt(bar.style.left, 10) + bar.offsetWidth };
console.log(JSON.stringify(out));
"""
        script = scratch / "selection-toolbar-155.js"
        script.write_text(support.i18n_js() + code, encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        if run.returncode != 0:
            check("155: the toolbar's place runs in node", False, run.stderr.strip()[:300])
        else:
            o = json.loads(run.stdout)
            check("155: in node, the toolbar shows with a selection, never over the words, and the focus leaves the "
                  "statement for the transcript",
                  o["above"]["hidden"] is False and o["aboveCovers"] is False and o["belowCovers"] is False
                  and o["focus"] == ["transcript"], str(o["above"]))
            check("155: in node, with room neither above nor below it stays away rather than cover the words",
                  o["nowhere"]["hidden"] is True, str(o["nowhere"]))
            check("155: in node, focus elsewhere is left alone, an interviewer's passage brings no toolbar and moves "
                  "nothing, and the row's menu open keeps it away",
                  o["bodyFocus"] == [] and o["aside"] == {"hidden": True, "focus": []} and o["menu"] is True, str(o))

    # ── B. on the boards: Group, Undo and the ⋯
    thkeys = fn(tjs, "thKeyDown")
    check("155: Group does what g does and Undo what Cmd + Z does, the focus left on the canvas, the keys still theirs",
          "$('th-group').onclick = () => { if (TH.live && !TH.busy) thGroupKey(); };" in tjs
          and "$('th-undo').onclick = () => thUndo(true);" in tjs
          and "if (e.key === 'g' || e.key === 'G') { e.preventDefault(); thGroupKey(); }" in thkeys
          and "if ((MOD(e) && (e.key === 'z' || e.key === 'Z')) || REDO_Y(e)) { e.preventDefault(); thUndo(!e.shiftKey && !REDO_Y(e)); return; }" in thkeys
          and "if (TH.busy) return;" in thkeys
          and "for (const id of ['th-group', 'th-undo']) $(id).addEventListener('pointerdown', (e) => e.preventDefault());" in tjs)
    world = tjs.split("$('th-world').addEventListener('click', (e) => {", 1)[1].split("\n  });", 1)[0]
    check("155: a ⋯ on a selected card's corner and on a label opens what its right-click menu offers, the same menu "
          "for the same item, and a press on it never starts a drag or a lasso",
          "const TH_MORE = `<button type=\"button\" class=\"th-more\" tabindex=\"-1\" title=\"${TH_MORE_WORD}\" aria-label=\"${TH_MORE_WORD}\">&#8943;</button>`;" in tjs
          and "thWhyHtml(v, key, owner) + TH_MORE;" in fn(tjs, "thRender") and fn(tjs, "thRender").count("TH_MORE") == 2
          and "if (hit && TH.live && !TH.busy) thMenuOpen(thItemOf(hit), at.left, at.bottom);" in world
          and "thMenuOpen(hit ? thItemOf(hit) : { kind: 'group', id: frame }, e.clientX, e.clientY);" in fn(tjs, "thContextMenu")
          and "'.th-del, .th-arr, .th-more, .th-sticky-del, .th-strip, .th-stackn, .th-restack, .gt-unfold'" in fn(tjs, "thPointerDown"))

    # ── D. Appearance kept under its setting
    if not node:
        skip("155: Appearance in node", "node is not on this machine")
    else:
        code = r"""
const store = {};
const localStorage = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = v; } };
const SENT = [];
const document = { documentElement: { dataset: {} }, dispatchEvent: (e) => SENT.push(e.detail) };
class CustomEvent { constructor(type, opts) { this.type = type; this.detail = opts.detail; } }
const rows = { light: { checked: false }, dark: { checked: false }, system: { checked: false } };
const $ = (id) => rows[id.replace('set-appearance-', '')];
""" + "\n".join(["const THEMES = ['system', 'light', 'dark'];", whole(app, "storedTheme"), whole(app, "theme"),
                 whole(app, "drawAppearance")]) + r"""
const out = { fresh: storedTheme() };
theme('dark');
out.dark = [document.documentElement.dataset.theme, store['idiograph-theme'], rows.dark.checked, rows.light.checked, SENT.slice()];
theme('light');
out.light = [document.documentElement.dataset.theme, rows.light.checked, rows.dark.checked];
theme('system');
out.system = [store['idiograph-theme'], rows.system.checked];
store['idiograph-theme'] = 'auto';
out.odd = storedTheme();
console.log(JSON.stringify(out));
"""
        script = scratch / "appearance-155.js"
        script.write_text(support.i18n_js() + code, encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        o = json.loads(run.stdout) if run.returncode == 0 else {}
        check("155: in node, Same as this computer first, each choice applied and kept under idiograph-theme, its row "
              "ticked and the others not, the flow told, and a value of no state read as the computer's",
              o.get("fresh") == "system" and o.get("dark") == ["dark", "dark", True, False, ["dark"]]
              and o.get("light") == ["light", True, False] and o.get("system") == ["system", True] and o.get("odd") == "system",
              run.stdout + run.stderr[:200])
