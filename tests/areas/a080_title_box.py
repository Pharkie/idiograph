"""Area 80: a label's title opens in a box in place (186), and since subpetjump (10 November 2026) nothing on the
board moves while it is open. A label sits on what it holds, its foot fixed (thLayout), and the title's and the
description's boxes, taller than the title, had made the label taller, so it rose, a sub-PET's over the sub-PET
above it, and dropped back when the edit ended. Now the boxes lie over the label, the title's words where the
title's stood, and the label keeps its size.

The browser check runs the page's own thTitleOpen, thTitleDone, thMeasure, thPlace and thLayout with the page's
stylesheets in headless Chrome, at 1280 and 720, on an invented PETs board about learning to swim as an adult: a
PET holding three sub-PETs, titles of one and two lines, one with a description. Each label is opened in turn and
its box's inside must sit over its title within 2 px, wrap into as many lines, and every label, card and frame stay
where it stood while the box is open and after Enter and after Esc.
"""
from __future__ import annotations

import html as html_mod
import json
import subprocess
import tempfile
from pathlib import Path

from . import support
from .support import check, skip


def test_title_box(scratch):
    print("\n80. A label's title opens in a box that keeps its width and wraps, as tall as its words (186), and nothing "
          "on the board moves while it is open (subpetjump)")
    js = support.text("apps/idiograph/static/themes.js")
    src = js.split("function thTitleOpen(", 1)[1].split("\n}\n", 1)[0]
    # since 21 October the description's box stands under the title's, and since 22 October Enter in either box
    # keeps both, Tab or Shift + Enter in the title going to it (area 252)
    check("80: a line break typed or pasted becomes a space, Enter in the description keeps and Esc leaves it",
          "box.value.replace(/[\\r\\n]+/g, ' ')" in src
          and "else if (e.key === 'Enter' || e.key === 'Tab') { e.preventDefault(); thTitleDone(true); }" in src
          and "else if (e.key === 'Escape') { e.preventDefault(); thTitleDone(false); }" in src
          and "if (e.isComposing) return;" in src)
    _in_place(js)


def _cut(js: str, head: str) -> str:
    at = js.index(head)
    return js[at:js.index("\n}\n", at) + 3]


def _line(js: str, head: str) -> str:
    at = js.index(head)
    return js[at:js.index("\n", at) + 1]


# The board, every word invented: a PET of three sub-PETs, the middle one described, each over two cards
BOARD = r"""
const card = (x, y, text) => ({ x, y, text, time: '04:10', sheet: 'Initial' });
TH.v = { discarded: [], stickies: [], picks: {},
  cards: { a1: card(60, 120, 'Floating for the first time with a hand under her back'),
           a2: card(290, 120, 'The teacher letting go without saying so'),
           b1: card(60, 330, 'Counting the tiles on the bottom to stop looking at the depth'),
           b2: card(290, 330, 'Swimming a width and only then noticing where she was'),
           c1: card(60, 560, 'Laughing under water and coming up coughing'),
           c2: card(290, 560, 'A cap and goggles that make her feel like a swimmer') },
  groups: [{ id: 'P', label: 'Water that holds you up, once you stop fighting it', members: ['A', 'B', 'C'], x: 0, y: 0 },
           { id: 'A', label: 'Trusting the water at last', members: ['a1', 'a2'], x: 0, y: 0 },
           { id: 'B', label: 'Afraid of the deep end, and going in anyway because the others did', members: ['b1', 'b2'], x: 0, y: 0,
             description: 'She swims towards the fear and not round it, and finds the deep end is only water, the same as the shallow end' },
           { id: 'C', label: 'Play', members: ['c1', 'c2'], x: 0, y: 0 }] };
"""

DRIVER = r"""
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const TH = { face: 'canvas', mode: 'pets', sizes: {}, els: { cards: {}, labels: {}, frames: {}, stickies: {}, under: {}, rails: {} },
  layout: {}, removed: [], editing: null, sel: { cards: new Set(), groups: new Set(), stickies: new Set() } };
const thTopOf = () => null, thWaiting = () => false, thRefuse = () => false, thNoteDone = () => {}, thTableTitleOpen = () => {};
const thSnap = () => ({}), thLabelBoxes = () => ({}), thUnit = () => 'sub-PET', thCardEditDone = () => {}, thStickyEditDone = () => {};
const thStacksRoom = () => {}, thRoomFollow = () => {}, thBadgeSpots = () => ({}), thUnderPlace = () => {}, thLinksDraw = () => {};
const thMapMoved = () => {}, thTableSoon = () => {}, thDragLayout = () => ({}), thLeavers = () => new Set();
const thDone = () => thRender(), thLocked = () => false;
const faults = [];
window.addEventListener("error", (e) => faults.push(String(e.message)));
/* the labels' and the cards' markup as thRender draws it */
function thRender() {
  const v = TH.v, world = $('th-world');
  world.innerHTML = '<div class="th-frames"></div><div class="th-cards"></div><div class="th-labels"></div>';
  const [frames, cards, labels] = world.children;
  TH.els = { cards: {}, labels: {}, frames: {}, stickies: {}, under: {}, rails: {} };
  for (const [key, c] of Object.entries(v.cards)) {
    const el = document.createElement('div');
    el.className = 'th-card in';
    el.innerHTML = `<p class="th-text">${esc(c.text)}</p><div class="th-foot"><span class="th-time">${esc(c.time)}</span></div>`;
    cards.appendChild(el);
    TH.els.cards[key] = el;
  }
  for (const g of v.groups) {
    const el = document.createElement('div');
    const upper = g.members.some((m) => thIsGroup(v, m));
    const desc = thDescOf(g);
    el.className = 'th-label' + (upper ? ' upper' : '') + (desc ? ' described' : '');
    el.innerHTML = '<span class="th-swatch" aria-hidden="true"></span><span class="th-words"><span class="th-title">'
      + esc(thLabelShown(g.label)) + '</span>' + (desc ? `<span class="th-desc">${esc(desc)}</span>` : '') + '</span>'
      + '<button type="button" class="th-arr"></button><button type="button" class="th-del"></button>';
    labels.appendChild(el);
    TH.els.labels[g.id] = el;
    const f = document.createElement('div');
    f.className = 'th-frame';
    frames.appendChild(f);
    TH.els.frames[g.id] = f;
  }
  thMeasure();
  thPlace();
}
"""

AFTER = r"""
const rect = (el) => { const r = el.getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map((n) => Math.round(n * 10) / 10); };
const all = () => { const o = {};
  for (const [k, el] of Object.entries(TH.els.labels)) o['label ' + k] = rect(el);
  for (const [k, el] of Object.entries(TH.els.cards)) o['card ' + k] = rect(el);
  for (const [k, el] of Object.entries(TH.els.frames)) o['frame ' + k] = rect(el);
  return o; };
const moved = (a, b) => Object.keys(a).filter((k) => !b[k] || a[k].some((n, i) => Math.abs(n - b[k][i]) > 0.5));
const lines = (el) => { const r = document.createRange(); r.selectNodeContents(el); return new Set([...r.getClientRects()].map((q) => Math.round(q.top))).size; };
// the line each word stands on, in a run of text: the title's own, or the box's words laid out in a copy with its font
const wordLines = (node) => { const text = node.firstChild, r = document.createRange(), out = [], tops = [];
  for (const m of text.nodeValue.matchAll(/\S+/g)) { r.setStart(text, m.index); r.setEnd(text, m.index + m[0].length);
    const top = Math.round(r.getClientRects()[0].top); if (!tops.length || Math.abs(top - tops[tops.length - 1]) > 2) tops.push(top); out.push(tops.length); }
  return out.join(''); };
const boxLines = (box, width) => { const cs = getComputedStyle(box), d = document.createElement('div');
  for (const k of ['fontFamily', 'fontSize', 'fontWeight', 'fontStyle', 'lineHeight', 'letterSpacing', 'wordSpacing', 'overflowWrap'])
    d.style[k] = cs[k];
  Object.assign(d.style, { position: 'absolute', left: '0', top: '0', width: width + 'px', whiteSpace: 'pre-wrap', visibility: 'hidden' });
  d.textContent = box.value; document.body.appendChild(d); const said = wordLines(d); d.remove(); return said; };
const press = (key) => document.activeElement.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true }));
const run = () => { const out = { labels: {} }; try {
  thRender();
  for (const g of TH.v.groups) {
    for (const key of ['Enter', 'Escape']) {
      const before = all();
      const title = TH.els.labels[g.id].querySelector('.th-title');
      const t = title.getBoundingClientRect();
      const tl = lines(title);
      thTitleOpen(g.id);
      const box = document.querySelector('.th-title-box');
      const cs = getComputedStyle(box);
      const b = box.getBoundingClientRect();
      // the box's inside, its border and padding off
      const inX = b.x + parseFloat(cs.borderLeftWidth) + parseFloat(cs.paddingLeft);
      const inY = b.y + parseFloat(cs.borderTopWidth) + parseFloat(cs.paddingTop);
      const inW = b.width - parseFloat(cs.borderLeftWidth) - parseFloat(cs.paddingLeft) - parseFloat(cs.borderRightWidth) - parseFloat(cs.paddingRight);
      const bl = Math.round((box.scrollHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom)) / parseFloat(cs.lineHeight));
      const open = all();
      const focused = document.activeElement === box;
      const column = title.parentElement.getBoundingClientRect();
      const desc = document.querySelector('.th-desc-box');
      const d = desc.getBoundingClientRect();
      const seen = document.elementFromPoint(d.x + 12, d.bottom - 5);
      const words = [wordLines(title), boxLines(box, inW)];
      // a short title's box keeps 180px to type in, the icons stepping aside
      const ends = b.right <= column.right + 4 || b.width <= 180.5;
      const descWhole = desc.scrollHeight <= desc.clientHeight + 1 && (seen === desc || desc.contains(seen));
      press(key);
      const after = all();
      out.labels[g.id + ' ' + key] = { dx: Math.abs(inX - t.x), dy: Math.abs(inY - t.y), wide: inW + 0.5 >= title.parentElement.getBoundingClientRect().width,
        lines: [tl, bl], words, ends, descWhole, open: moved(before, open), after: moved(before, after), focused, shut: !TH.editing && !document.querySelector('.th-title-box') };
    }
  }
  out.stacked = TH.layout.B.label.y > TH.layout.A.label.y + TH.layout.A.label.h;
  if (faults.length) out.err = faults.join(" / ").slice(0, 400);
} catch (err) { out.err = String(err && err.stack || err).slice(0, 400); }
  document.getElementById('out').textContent = JSON.stringify(out); };
document.addEventListener('DOMContentLoaded', run);
"""


def _in_place(js: str):
    """In headless Chrome on the page's own functions and stylesheets, each label's box opened over its title, and
    nothing on the board moving while it is open or after Enter or Esc."""
    exe = support.browser()
    if exe is None:
        skip("80: a label's title box opens in place in a real browser", "no Chrome, Chromium, Brave or Edge on this computer")
        return
    names = ["const TH_GAP", "const TH_FRAME_X", "const TH_FRAME_Y", "const TH_UNTITLED_SAVED", "const TH_UNTITLED = ",
             "const thUntitled = ", "const thLabelKept = ", "const thLabelShown = ", "const thIsGroup = ", "const thOnCanvas = ",
             "const thExists = ", "const thStickies = ", "const thSticky = ", "const thIsSticky = ", "const thUnitHead = ",
             "const thDescOf = ", "const thDescStep = ", "const TH_STICKY = ", "const TH_CARD = ", "const TH_LABEL = ",
             "const TH_LABEL_W = ", "const TH_TITLE_INSET = ", "const TH_TITLE_RIGHT = ", "const thPad = ", "function thGroup("]
    fns = ["function thSetDesc(", "function thSize(", "function thUnion(", "function thLayout(",
           "function thLabelsWiden(", "function thMeasure(", "function thPlace(", "function thTitleOpen(", "function thTitleDone("]
    try:
        pieces = "".join(_line(js, n) for n in names) + "\n".join(_cut(js, f) for f in fns)
    except ValueError as err:
        check("80: the page's title box, measure and layout are in themes.js", False, str(err))
        return
    css = "\n".join(support.text(p) for p in ("family/static/tokens.css", "family/static/style.css",
                                              "apps/idiograph/static/themes.css"))
    results = {}
    with tempfile.TemporaryDirectory(prefix="idiograph-080-") as tmp:
        for width in (1280, 720):
            doc = ('<!doctype html><html><head><meta charset="utf-8"><style>' + css
                   + '\n#th-world { position: absolute; left: 0; top: 0; }</style></head>'
                   + '<body><div id="th-world"></div><pre id="out">none</pre><script>'
                   + support.i18n_js("idiograph") + DRIVER + pieces + BOARD + AFTER + "</script></body></html>")
            file = Path(tmp) / f"titles-{width}.html"
            file.write_text(doc, encoding="utf-8")
            cmd = [str(exe), "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                   "--disable-extensions", "--disable-background-networking", "--password-store=basic",
                   "--use-mock-keychain", f"--user-data-dir={Path(tmp) / f'profile-{width}'}", f"--window-size={width},900",
                   "--virtual-time-budget=3000", "--dump-dom", file.as_uri()]
            try:
                dumped = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=120).stdout
            except (OSError, subprocess.TimeoutExpired) as err:
                dumped = str(err)
            said = dumped.split('<pre id="out">', 1)[1].split("</pre>", 1)[0] if '<pre id="out">' in dumped else ""
            try:
                results[width] = json.loads(html_mod.unescape(said))
            except ValueError:
                results[width] = {"err": said[:300] or dumped[-300:]}
    for width in (1280, 720):
        got = results.get(width, {})
        labels = got.get("labels", {})
        check(f"80: at {width}, the board drawn, each sub-PET under the one above it, every label opened with Enter and Esc",
              not got.get("err") and got.get("stacked") is True and len(labels) == 8, str(got)[:400])
        check(f"80: at {width}, each title's box opens over its title, its inside within 2 px of it, as wide as its column, "
              "wrapping into as many lines, the focus in it",
              bool(labels) and all(o["dx"] <= 2 and o["dy"] <= 2 and o["wide"] and o["lines"][0] == o["lines"][1]
                                   and o["focused"] for o in labels.values()), str(labels)[:600])
        check(f"80: at {width}, each title's box wraps at the same words as its title and ends where its column ends, short of "
              "the label's icons, and the description's box shows its words whole, nothing over them",
              bool(labels) and all(o["words"][0] and o["words"][0] == o["words"][1] and o["ends"] and o["descWhole"] for o in labels.values()),
              str({k: (o["words"], o["ends"], o["descWhole"]) for k, o in labels.items()})[:600])
        check(f"80: at {width}, no label, card or frame moves while a title's box is open, a sub-PET's under another included",
              bool(labels) and all(not o["open"] for o in labels.values()),
              str({k: o["open"] for k, o in labels.items()})[:600])
        check(f"80: at {width}, after Enter and after Esc the box is gone and everything stands where it stood",
              bool(labels) and all(not o["after"] and o["shut"] for o in labels.values()),
              str({k: (o["after"], o["shut"]) for k, o in labels.items()})[:600])
