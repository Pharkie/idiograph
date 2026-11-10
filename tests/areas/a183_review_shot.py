"""Area 183: review shots that explain themselves (18 October, the reviewshot build, Adam's word of 17 and
18 October that a heading, Before and After side by side and the changed part marked are "so much more
helpful").

`packaging/review_shot.js` makes one PNG from shots on disk in the format Harbour's review-shot.ts makes: a
heading band with what changed and "Check:", Before and After side by side or stacked when a panel is wider
than twice its height, both at one scale and labelled, a dashed box round the changed part on each, the
heading 1/46 of the composite's width and never under 20 pixels, and `<name>.caption.json` beside it. Its
pack prints each shot's heading in order and refuses a shot with no caption. The layout maths, the caption,
the boxes and the pack run in node, and the drawing through AppKit on a Mac alone. Every picture here is
invented, flat colours and a white card.

Since 20 October (the shotlint build) the tool enforces the shot rules review checks kept finding broken:
a box within 8 pixels of its panel's edge, two boxes overlapping, a composite over 1,400 pixels wide, text
under 12 pixels with the composite shown 900 wide (from the capture's sidecar), a shot with no first line,
and a heading band too short for its wrapped lines. `packaging/shot_box.js` measures boxes and crops in the
page, here on a made-up page through a stand-in for the few DOM calls it makes. Since the shotlint2 build a
box keeps 8 pixels inside the edge of the menu, card, panel or section it sits in, or climbs to it, and the
composite refuses a sidecar whose box does not.
"""
from __future__ import annotations

import json
import math
import shutil
import struct
import subprocess
import sys
import zlib
from pathlib import Path

from . import support
from .support import check, skip

TOOL_JS = support.source("packaging/review_shot.js")
SHOT_BOX_JS = support.source("packaging/shot_box.js")
MARK = (0xE6, 0x00, 0x7E)

NODE_SCRIPT = r"""
const t = require(process.argv[2]);
const out = {};
const refusal = (f) => { try { f(); return null; } catch (e) { return e.message; } };
const L = (a, b, o) => t.layout(a, b, o);
const s = (w, h) => ({ width: w, height: h });
out.side = L(s(1280, 800), s(1280, 800));
out.stacked = L(s(1280, 300), s(1280, 300));
out.edge = [L(s(1200, 600), s(1200, 600)).arrangement, L(s(1201, 600), s(1201, 600)).arrangement];
out.forced = [L(s(1280, 800), s(1280, 800), { arrange: 'stacked' }).arrangement, L(s(1280, 300), s(1280, 300), { arrange: 'side' }).arrangement];
out.mixed = L(s(1280, 800), s(1000, 700));
out.retina = L(s(2560, 1600), s(2560, 1600), { scale: 2 });
out.single = L(s(360, 740), null);
out.sweep = [];
for (const w of [120, 200, 360, 400, 800, 919, 920, 1280, 1500, 2000, 2560, 4000, 6000]) {
  for (const before of [null, s(w, 600)]) {
    const l = L(s(w, 600), before);
    out.sweep.push({ w, arrangement: l.arrangement, headingPx: l.headingPx, width: l.width, gutter: l.gutter });
  }
}
out.badScale = refusal(() => L(s(10, 10), null, { scale: 0 }));
out.placeSide = t.place(out.side, 100);
out.placeStacked = t.place(out.stacked, 100);
out.placeSingle = t.place(out.single, 50);
out.placeHuge = t.place(L(s(20000, 1000), null, { scale: 2 }), 60);
const hand = (both, after) => ({ boxes: { both, before: [], after: after || [] } });
out.pad = t.handPad(out.side);
out.box = t.panelBoxes(hand([[100, 100, 200, 80]]), out.side, {});
out.boxPast = refusal(() => t.panelBoxes(hand([[1200, 100, 200, 80]]), out.side, {}));
out.boxEdge = refusal(() => t.panelBoxes(hand([[0, 0, 1280, 800]]), out.side, {}));
out.boxNear = [refusal(() => t.panelBoxes(hand([], [[100, 1, 200, 80]]), out.side, {})),
  refusal(() => t.panelBoxes(hand([], [[100, 8 + out.pad, 200, 80]]), out.side, {}))];
out.boxOverlap = refusal(() => t.panelBoxes(hand([[100, 100, 200, 80]], [[250, 150, 100, 100]]), out.side, {}));
const car = (boxes, extra) => t.parseSidecar(JSON.stringify(Object.assign({ tool: 'shot_box', scale: 2, crop: { x: 0, y: 0, w: 1280, h: 800 },
  boxes, minText: { px: 13, text: 'Wren' }, problems: [] }, extra || {})), 'a.shot.json');
out.carBox = t.panelBoxes(hand([]), out.side, { both: car([{ x: 8, y: 8, w: 100, h: 40, of: '#wren' }]) });
out.carEdge = refusal(() => t.panelBoxes(hand([]), out.side, { after: car([{ x: 7, y: 20, w: 100, h: 40, of: '#wren' }]) }));
out.carOverlap = refusal(() => t.panelBoxes(hand([]), out.side, { after: car([{ x: 20, y: 20, w: 100, h: 40, of: '#a' }, { x: 110, y: 50, w: 100, h: 40, of: '#b' }]) }));
out.sidecar = [
  car([{ x: 8, y: 8, w: 100, h: 40, of: '#wren' }]),
  refusal(() => t.parseSidecar('{nope', 'b.shot.json')),
  refusal(() => t.parseSidecar('{"boxes": []}', 'c.shot.json')),
  refusal(() => t.parseSidecar('{"crop": {"w": 10, "h": 10}, "boxes": [{"x": 1, "y": 1, "w": 0, "h": 4}]}', 'd.shot.json')),
  t.sidecarPath('/raw/notes-after.png'),
];
out.scales = [t.resolveScale(null, [car([])]), t.resolveScale(null, []), t.resolveScale(2, [car([])]),
  refusal(() => t.resolveScale(1, [car([])])),
  refusal(() => t.resolveScale(null, [car([]), Object.assign(car([]), { scale: 1, path: 'e.shot.json' })]))];
out.lint = [
  refusal(() => t.lintComposite(L(s(1400, 600), null), {})),
  refusal(() => t.lintComposite(L(s(1280, 800), s(1280, 800)), {})),
  refusal(() => t.lintComposite(L(s(1300, 300), null), { after: { px: 13, text: '3 sightings' } })),
  refusal(() => t.lintComposite(L(s(1000, 300), null), { after: { px: 15, text: 'x' } })),
  refusal(() => t.lintComposite(L(s(1300, 1600), null, { scale: 2 }), { after: { px: 9, text: '12:40' } })),
  refusal(() => t.lintComposite(L(s(1300, 1600), null, { scale: 2 }), { after: { px: 11, text: '12:40' } })),
];
out.parseBox = [t.parseBox('1, 2.5,3,4'), refusal(() => t.parseBox('1,2,3')), refusal(() => t.parseBox('1,2,0,4')), refusal(() => t.parseBox('a,b,c,d'))];
const r = { x: 10, y: 20, w: 300, h: 200 };
out.dashes = t.dashes(r, 6);
out.tiny = t.dashes({ x: 0, y: 0, w: 12, h: 12 }, 3);
out.caption = [
  t.normaliseCaption({ changed: '  Notes  column:\n wider ', check: 'Check:  the notes   wrap' }, true),
  t.normaliseCaption({ changed: null, shows: ' The card  at 360 ', check: 'the card fits' }, false),
  refusal(() => t.normaliseCaption({ changed: 'x', check: '  ' }, true)),
  refusal(() => t.normaliseCaption({ changed: '', check: 'y' }, true)),
  refusal(() => t.normaliseCaption({ changed: 'x', check: 'y' }, false)),
  refusal(() => t.normaliseCaption({ check: 'y' }, false)),
  refusal(() => t.normaliseCaption({ changed: 'x', shows: 'z', check: 'y' }, true)),
];
out.heading = [
  t.headingText({ changed: 'Notes column: wider', check: 'the notes wrap' }),
  t.headingText({ changed: 'Is it wider?', check: 'the notes wrap' }),
  t.headingText({ changed: null, check: 'the card fits' }),
  t.headingText({ changed: null, shows: 'The card at 360', check: 'the card fits' }),
];
out.captionPath = [t.captionPath('/a/b/01-notes.png'), t.captionPath('02.side.png')];
out.file = t.captionFile(out.caption[0], out.side, { before: ['1,2,3,4'], after: [] });
out.fileShows = t.captionFile(out.caption[1], out.single, { before: [], after: [] });
out.parse = [
  t.parseCaptionFile(JSON.stringify(out.file)),
  t.parseCaptionFile('{nope'),
  t.parseCaptionFile('[]'),
  t.parseCaptionFile('{"changed": null, "check": " "}'),
  t.parseCaptionFile('{"changed": null, "check": "x", "beforeAfter": true}'),
  t.parseCaptionFile('{"check": "x"}'),
  t.parseCaptionFile(JSON.stringify(out.fileShows)),
];
const files = {
  '02-bar.caption.json': '{"changed": "Bar: shorter", "check": "the buttons fit", "beforeAfter": true, "arrangement": "stacked"}',
  '01-card.caption.json': '{"changed": null, "check": "the card fits", "beforeAfter": false, "arrangement": "single"}',
  '04-bad.caption.json': '{"changed": null}',
  '05-gone.caption.json': '{"changed": null, "check": "x"}',
  '06-new.caption.json': '{"changed": null, "shows": "The card at 360", "check": "the card fits", "beforeAfter": false}',
};
const read = (n) => (n in files ? files[n] : null);
out.pack = t.pack(['02-bar.png', '03-raw.png', '01-card.png', '04-bad.png', 'raw', ...Object.keys(files).filter((n) => !n.startsWith('06'))], read);
out.packGood = t.pack(['02-bar.png', '01-card.png', '06-new.png', '01-card.caption.json', '02-bar.caption.json', '06-new.caption.json'], read);
out.packEmpty = t.pack(['raw', 'notes.txt'], read);
out.args = [
  t.parseArgs(['--out', 'o.png', '--before', 'b.png', '--after', 'a.png', '--changed', 'c', '--check', 'k', '--box', '1,2,3,4',
    '--box', '5,6,7,8', '--box-after', '9,9,9,9', '--stack', '--scale', '2']),
  t.parseArgs(['pack', 'review']),
  refusal(() => t.parseArgs(['--out', 'o.png', '--after', 'a.png', '--check', 'k', '--box-before', '1,2,3,4'])),
  refusal(() => t.parseArgs(['--out', 'o.png', '--after', 'a.png', '--check', 'k', '--side'])),
  refusal(() => t.parseArgs(['--out', 'o.jpg', '--after', 'a.png', '--check', 'k'])),
  refusal(() => t.parseArgs(['--out', 'o.png', '--after', 'a.png', '--colour', 'red'])),
  refusal(() => t.parseArgs(['--after', 'a.png', '--check', 'k'])),
  t.parseArgs(['--out', 'o.png', '--before', 'b.png', '--after', 'a.png', '--changed', 'c', '--check', 'k',
    '--boxes-from-before', 'b.shot.json', '--boxes-from-after', 'a.shot.json']),
  refusal(() => t.parseArgs(['--out', 'o.png', '--after', 'a.png', '--shows', 's', '--check', 'k', '--boxes-from-before', 'b.shot.json'])),
  refusal(() => t.parseArgs(['--out', 'o.png', '--after', 'a.png', '--shows', 's', '--check', 'k', '--boxes-from', 'a.shot.json', '--boxes-from', 'b.shot.json'])),
];
out.constants = [t.MIN_HEADING_PX, t.HEADING_RATIO, t.STACK_ASPECT, t.EDGE_CLEAR, t.MAX_COMPOSITE_PX, t.SHOWN_WIDTH, t.MIN_SHOWN_TEXT];
console.log(JSON.stringify(out));
"""


SHOT_BOX_SCRIPT = r"""
const sb = require(process.argv[2]);
const out = {};
// a made-up page, a bird-watching log: a stand-in for the few DOM calls shot_box.js makes
const style = (extra) => Object.assign({ display: 'block', visibility: 'visible', opacity: '1', fontSize: '13px', color: 'rgb(20, 20, 20)',
  backgroundColor: 'rgba(0, 0, 0, 0)' }, extra || {});
const line = { borderTopWidth: '1px', borderTopStyle: 'solid', borderTopColor: 'rgb(200, 200, 200)', borderRightWidth: '1px',
  borderRightStyle: 'solid', borderRightColor: 'rgb(200, 200, 200)', borderBottomWidth: '1px', borderBottomStyle: 'solid',
  borderBottomColor: 'rgb(200, 200, 200)', borderLeftWidth: '1px', borderLeftStyle: 'solid', borderLeftColor: 'rgb(200, 200, 200)' };
function El(tag, x, y, w, h, o) {
  o = o || {};
  return {
    nodeType: 1, tagName: tag.toUpperCase(), id: o.id || '', className: o.cls || '', attrs: o.attrs || {}, style: style(o.style),
    rect: { x, y, w, h }, offsetWidth: o.offsetWidth === undefined ? w : o.offsetWidth, childNodes: [], parentNode: null,
    getAttribute(n) { return n in this.attrs ? this.attrs[n] : null; },
    getBoundingClientRect() { const r = this.rect; return { left: r.x, top: r.y, right: r.x + r.w, bottom: r.y + r.h }; },
    contains(n) { for (let e = n; e; e = e.parentNode) if (e === this) return true; return false; },
  };
}
const Text = (value, rects) => ({ nodeType: 3, nodeValue: value, rects, parentNode: null });
const add = (parent, ...kids) => { for (const k of kids) { k.parentNode = parent; parent.childNodes.push(k); } return parent; };
const labelled = (el, value, x, y, w, h) => add(el, Text(value, [{ x, y, w, h }]));

const body = El('body', 0, 0, 1280, 800);
const backdrop = El('svg', 0, 0, 1280, 800, { cls: 'board-backdrop' });
const menu = El('div', 400, 100, 220, 130, { cls: 'row-menu', attrs: { role: 'menu' }, style: line });
const row1 = El('div', 401, 101, 218, 40, { cls: 'menu-row', attrs: { role: 'menuitem' } });
const group = labelled(El('button', 412, 110, 60, 22, { id: 'group' }), 'Group', 418, 114, 40, 14);
const key = labelled(El('span', 476, 114, 10, 14, { cls: 'key' }), 'G', 476, 114, 10, 14);
const row2 = labelled(El('div', 401, 141, 218, 40, { cls: 'menu-row', attrs: { role: 'menuitem' } }), 'Ungroup', 418, 150, 56, 14);
const row3 = labelled(El('div', 401, 181, 218, 40, { cls: 'menu-row', attrs: { role: 'menuitem' } }), 'Bin', 418, 190, 24, 14);
add(row1, group, key);
add(menu, row1, row2, row3);
const note = labelled(El('div', 600, 240, 200, 80, { cls: 'note-card', style: line }), 'Robin by the gate', 612, 252, 130, 14);
const bird = El('div', 40, 300, 240, 120, { cls: 'bird-card', style: line });
add(bird, labelled(El('h3', 56, 312, 120, 16), 'Wren at dawn', 56, 312, 120, 16),
  labelled(El('p', 56, 390, 80, 12, { id: 'count', style: { fontSize: '9px' } }), '3 sightings', 56, 390, 80, 12));
const lonely = labelled(El('button', 900, 600, 80, 30, { id: 'lonely' }), 'Add a bird', 910, 608, 60, 14);
const crowded = labelled(El('span', 700, 50, 40, 14, { id: 'crowded' }), 'Owl', 700, 50, 40, 14);
const board = El('div', 900, 300, 200, 100, { cls: 'board', offsetWidth: 400 });
add(board, labelled(El('span', 910, 310, 100, 10, { id: 'tiny', offsetWidth: 200 }), 'Heron 05:40', 910, 310, 100, 10));
board.childNodes[0].style.fontSize = '14px';
// a full-width status bar at the window's foot, its top border its only line
const bar = El('div', 0, 764, 1280, 36, { cls: 'status-bar', style: { borderTopWidth: '1px', borderTopStyle: 'solid', borderTopColor: 'rgb(200, 200, 200)' } });
add(bar, labelled(El('span', 12, 775, 60, 14), 'Wren log', 12, 775, 60, 14),
  labelled(El('button', 84, 771, 60, 22, { id: 'quotes' }), 'Quotes', 90, 775, 48, 14),
  labelled(El('button', 156, 771, 60, 22, { id: 'notes' }), 'Notes', 162, 775, 48, 14),
  labelled(El('span', 220, 775, 70, 14), '3 sightings', 220, 775, 70, 14));
// a tag menu drawn by its background and shadow alone, its rows flush with its edges (the shotlint2 build)
const tagMenu = El('div', 40, 460, 200, 88, { cls: 'tag-menu', attrs: { role: 'menu' },
  style: { backgroundColor: 'rgb(255, 255, 255)', boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)' } });
add(tagMenu, labelled(El('div', 40, 460, 200, 44, { id: 'rename', attrs: { role: 'menuitem' } }), 'Rename', 52, 474, 50, 14),
  labelled(El('div', 40, 504, 200, 44, { attrs: { role: 'menuitem' } }), 'Remove', 52, 518, 50, 14));
// a plant card whose button sits 15 pixels in from its border, its box 7 pixels in
const plant = El('div', 300, 460, 240, 140, { cls: 'plant-card', style: line });
add(plant, labelled(El('h3', 316, 472, 140, 16), 'Fern on the sill', 316, 472, 140, 16),
  labelled(El('button', 315, 540, 80, 28, { id: 'water' }), 'Water', 325, 547, 50, 14));
// a list section on a panel of its own colour, its divider at its foot 20 pixels under its button
const panel = El('div', 600, 440, 260, 200, { cls: 'side-panel', style: { backgroundColor: 'rgb(240, 240, 236)' } });
const section = El('div', 616, 456, 228, 96, { cls: 'seed-list', style: { borderBottomWidth: '1px', borderBottomStyle: 'solid',
  borderBottomColor: 'rgb(200, 200, 200)' } });
add(section, labelled(El('button', 640, 504, 80, 28, { id: 'sow' }), 'Sow', 660, 511, 40, 14));
add(panel, section);
add(body, backdrop, menu, note, bird, lonely, crowded, Text('near the owl', [{ x: 744, y: 50, w: 70, h: 14 }]), board, bar, tagMenu, plant, panel);

const find = (node, id) => {
  if (node.nodeType === 1 && node.id === id) return node;
  for (const c of node.childNodes || []) { const f = find(c, id); if (f) return f; }
  return null;
};
const document = {
  body,
  querySelector: (sel) => (sel[0] === '#' ? find(body, sel.slice(1)) : null),
  createRange: () => { let n = null; return { selectNodeContents(x) { n = x; }, getClientRects() { return n.rects.map((r) => ({ left: r.x, top: r.y, right: r.x + r.w, bottom: r.y + r.h })); } }; },
};
const window = { document, innerWidth: 1280, innerHeight: 800, devicePixelRatio: 2, getComputedStyle: (el) => el.style };
const opts = { window };

out.group = sb.shotBox('#group', opts);
out.lonely = sb.shotBox('#lonely', opts);
out.crowded = sb.shotBox('#crowded', opts);
out.missing = sb.shotBox('#heron', opts);
out.crop = sb.shotCrop([out.group], 24, opts);
out.edge = sb.shotCrop([{ x: 1242, y: 2, w: 41, h: 36, of: '#edge' }], 24, opts);
out.minMenu = sb.shotMinText(out.crop, opts);
out.minCard = sb.shotMinText({ x: 30, y: 290, w: 260, h: 140 }, opts);
out.minBoard = sb.shotMinText({ x: 890, y: 290, w: 220, h: 120 }, opts);
out.plan = sb.shotPlan(['#group'], opts);
out.planBad = sb.shotPlan(['#group', '#crowded'], opts);
out.quotes = sb.shotBox('#quotes', opts);
out.notes = sb.shotBox('#notes', opts);
out.barPlan = sb.shotPlan(['#quotes'], opts);
out.rename = sb.shotBox('#rename', opts);
out.water = sb.shotBox('#water', opts);
out.sow = sb.shotBox('#sow', opts);
out.waterPlan = sb.shotPlan(['#water'], opts);
out.sowPlan = sb.shotPlan(['#sow'], opts);
out.kinds = [sb.kindOf(menu), sb.kindOf(row1), sb.kindOf(note), sb.kindOf(El('button', 0, 0, 1, 1, { cls: 'card-close' })),
  sb.kindOf(El('div', 0, 0, 1, 1, { cls: 'rail' })), sb.kindOf(El('div', 0, 0, 1, 1, { attrs: { role: 'dialog' } }))];
console.log(JSON.stringify(out));
"""


def png(path: Path, w: int, h: int, rgb, rects=()) -> None:
    """An invented picture: a flat colour with flat rectangles on it, written with the standard library."""
    rows = []
    for y in range(h):
        row = bytearray()
        for x in range(w):
            c = rgb
            for (rx, ry, rw, rh, rc) in rects:
                if rx <= x < rx + rw and ry <= y < ry + rh:
                    c = rc
            row += bytes(c)
        rows.append(b"\x00" + bytes(row))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(b"".join(rows))) + chunk(b"IEND", b""))


def flat_png(path: Path, w: int, h: int, rgb) -> None:
    """An invented picture of one flat colour, quick at any size."""
    row = b"\x00" + bytes(rgb) * w

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(row * h)) + chunk(b"IEND", b""))


def read_png(path: Path):
    """Width, height and a pixel reader for an 8-bit RGB or RGBA PNG, as AppKit writes one."""
    data = path.read_bytes()
    pos, idat, w, h, bpp = 8, b"", 0, 0, 4
    while pos < len(data):
        n, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
            if depth != 8 or interlace or ctype not in (2, 6):
                raise ValueError(f"a PNG this reader does not read: depth {depth}, type {ctype}")
            bpp = 3 if ctype == 2 else 4
        elif kind == b"IDAT":
            idat += body
        pos += 12 + n
    raw = zlib.decompress(idat)
    stride = w * bpp
    rows, prev = [], bytearray(stride)
    for y in range(h):
        f = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if f == 1:
                line[i] = (line[i] + a) & 255
            elif f == 2:
                line[i] = (line[i] + b) & 255
            elif f == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(bytes(line))
        prev = line
    return w, h, lambda x, y: tuple(rows[y][x * bpp:x * bpp + 3])


def jround(v: float) -> int:
    """JavaScript's Math.round, a half always up, where Python's round takes it to the even number."""
    return math.floor(v + 0.5)


def test_review_shot(scratch):
    print("\n183. Review shots that explain themselves, 18 October: a heading band with what changed and Check:, "
          "Before and After side by side or stacked, at one scale and labelled, a dashed box round the changed part, "
          "the heading 1/46 of the width and never under 20 pixels, a caption file beside each, and the pack")

    node = shutil.which("node")
    folder = scratch / "a183"
    folder.mkdir(parents=True, exist_ok=True)
    if not node:
        skip("183: the layout maths, the captions, the boxes and the pack in node", "node is not installed")
        o = None
    else:
        script = folder / "maths.js"
        script.write_text(NODE_SCRIPT, encoding="utf-8")
        run = subprocess.run([node, str(script), str(TOOL_JS)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        o = json.loads(run.stdout) if run.returncode == 0 else None
        check("183: review_shot.js loads and runs in node", o is not None, run.stderr.strip()[:400])
    if o:
        maths_checks(o)
        pack_cli_checks(node, folder)
    plan = shot_box_checks(node, folder) if node else None
    if plan:
        sidecar_cli_checks(node, folder, plan)

    if sys.platform != "darwin" or not shutil.which("osascript"):
        skip("183: the shots drawn, their pixels and the refusals through osascript", "the drawing needs AppKit, which only a Mac has")
    else:
        mac_checks(folder, o)
        if plan:
            mac_sidecar_checks(folder)


def maths_checks(o: dict) -> None:
    side, stacked, single, mixed, retina = o["side"], o["stacked"], o["single"], o["mixed"], o["retina"]
    check("183: a panel wider than twice its height stacks, 1280 by 300, two gutters wide, and exactly twice its "
          "height stays side by side, 1200 by 600 beside 1201 by 600",
          stacked["arrangement"] == "stacked" and stacked["width"] == 1280 + 2 * stacked["gutter"]
          and o["edge"] == ["side", "stacked"], str(o["edge"]))
    check("183: --stack and --side override the rule either way", o["forced"] == ["stacked", "side"], str(o["forced"]))
    check("183: Before and After keep their own sizes at one scale, never stretched to each other, and shots taken "
          "at scale 2 are laid out at half their pixels",
          mixed["before"] == {"width": 1000, "height": 700} and mixed["after"] == {"width": 1280, "height": 800}
          and retina["after"] == {"width": 1280, "height": 800} and retina["headingPx"] == side["headingPx"]
          and o["placeSide"]["renderScale"] == 1, json.dumps([mixed["before"], retina["after"]]))
    check("183: a shot with no before is one panel, two gutters wide, its heading the 20 pixel least at 360 wide",
          single["arrangement"] == "single" and single["before"] is None and single["width"] == 360 + 2 * 16
          and single["headingPx"] == 20, json.dumps(single))
    bad = [s for s in o["sweep"] if s["headingPx"] != max(20, jround(s["width"] / 46)) or s["headingPx"] < 20
           or s["gutter"] != max(16, jround(s["headingPx"] * 0.6))]
    grows = [s["headingPx"] for s in o["sweep"] if s["arrangement"] == "side"]
    check("183: the heading's size rule across 26 layouts from 120 to 12,000 pixels of panels: always the composite's "
          "width over 46, rounded, never under 20, and growing with the width",
          not bad and len(o["sweep"]) == 26 and grows == sorted(grows) and grows[-1] > grows[0], json.dumps(bad[:3]))
    check("183: a scale of 0 is refused", o["badScale"] == "the scale must be above 0, not 0", str(o["badScale"]))

    huge = o["placeHuge"]
    check("183: a composite past 16,000 pixels a side is drawn at a smaller scale so it stays under",
          huge["renderScale"] < 2 and huge["width"] * huge["renderScale"] <= 16000, str(huge["renderScale"]))

    line, g = side["line"], side["gutter"]
    pad = line + max(2, jround(g / 6))
    box = o["box"]["after"][0]["r"]
    check("183: a box given by hand lands on both panels at its own coordinates, padded a little outside the part "
          "it marks", o["pad"] == pad and box == {"x": 100 - pad, "y": 100 - pad, "w": 200 + 2 * pad, "h": 80 + 2 * pad}
          and o["box"]["before"][0]["r"] == box and line == jround(58 / 7), json.dumps(box))
    check("183: a box running past its shot is refused with the shot's size",
          o["boxPast"] == "the box 1200,100,200,80 runs past the before shot, which is 1280 by 800 (at --scale 1)", str(o["boxPast"]))
    check("183: a box on or within 8 pixels of its panel's edge is refused, naming the edge, and one with exactly 8 "
          "clear is drawn (tonight's first fault: dashes on the frame's edge)",
          o["boxEdge"].startswith("the box 0,0,1280,800 on the before shot comes 0px from its left edge, under the 8 it needs")
          and o["boxNear"][0].startswith("the box 100,1,200,80 on the after shot comes 0px from its top edge")
          and o["boxNear"][1] is None and "shotCrop in packaging/shot_box.js" in o["boxEdge"], json.dumps(o["boxNear"]))
    check("183: two boxes overlapping on one panel are refused, naming both",
          o["boxOverlap"] == "the boxes 100,100,200,80 and 250,150,100,100 on the after shot overlap: box the row or card "
          "that holds both, once", str(o["boxOverlap"]))
    cb = o["carBox"]
    check("183: a sidecar's box is drawn where it says, its room already in it, on both panels with --boxes-from, and "
          "is held to the same rules: 7 pixels from the edge and two overlapping are refused, named by what they mark",
          cb["before"][0]["r"] == {"x": 8, "y": 8, "w": 100, "h": 40} and cb["after"][0]["pad"] == 0
          and o["carEdge"].startswith("the box round #wren on the after shot comes 7px from its left edge")
          and o["carOverlap"].startswith("the boxes round #a and round #b on the after shot overlap"),
          json.dumps([o["carEdge"], o["carOverlap"]]))
    sc = o["sidecar"]
    check("183: a sidecar reads as its crop, scale, smallest text, problems and boxes, sits beside its raw shot as "
          "<name>.shot.json, and one that is not JSON, has no crop or has a box with no width is refused",
          sc[0]["crop"] == {"w": 1280, "h": 800} and sc[0]["scale"] == 2 and sc[0]["minText"] == {"px": 13, "text": "Wren"}
          and sc[0]["boxes"] == [{"box": [8, 8, 100, 40], "of": "#wren", "edges": []}] and sc[4] == "/raw/notes-after.shot.json"
          and sc[1].startswith("b.shot.json is not JSON") and sc[2].startswith("c.shot.json has no crop")
          and sc[3].startswith("d.shot.json has no boxes"), json.dumps(sc[1:]))
    sl = o["scales"]
    check("183: the shots' scale is the sidecar's when --scale is left out, 1 with neither, and a --scale or a second "
          "sidecar that disagrees is refused",
          sl[:3] == [2, 1, 2] and sl[3].startswith("a.shot.json was shot at device scale 2, not the --scale 1 given")
          and "different device scales, 2 and 1" in sl[4], json.dumps(sl))
    li = o["lint"]
    check("183: a composite over 1,400 pixels wide is refused, with --stack offered for a pair side by side",
          li[0] == "the composite would be 1438 pixels wide, over 1,400: crop tighter"
          and li[1].startswith("the composite would be 2665 pixels wide") and li[1].endswith("or --stack the pair"), json.dumps(li[:2]))
    check("183: with a sidecar, text that would show under 12 pixels with the composite shown 900 wide is refused, "
          "naming the text, its size scaled by the device scale and the composite's width: 13 pixels in a 1,332 "
          "composite and 9 in a 682 at scale 2 are refused, 15 in a 1,032 and 11 in a 682 at scale 2 are not",
          li[2] == 'the smallest text in the after shot, 13px ("3 sightings"), would show at 8.8px with the composite '
          "shown 900 wide, under 12: crop tighter" and li[3] is None
          and li[4] is not None and li[4].startswith('the smallest text in the after shot, 9px ("12:40")') and li[5] is None,
          json.dumps(li[2:]))

    c = o["caption"]
    check("183: a caption collapses its spaces and takes off a Check: the caption gave, and a shot with no before "
          "keeps what it shows as its first line",
          c[0] == {"changed": "Notes column: wider", "check": "the notes wrap"}
          and c[1] == {"changed": None, "shows": "The card at 360", "check": "the card fits"}, json.dumps(c[:2]))
    check("183: a shot with no check, a Before and After with no changed or with a shows, a changed with no before "
          "and a shot with no before and no shows are each refused in plain words",
          c[2] == "a review shot needs --check, what to look at"
          and c[3] == "a Before and After needs --changed, what changed between them"
          and c[4] == "a shot with no --before says what it shows with --shows, not --changed"
          and c[5] == "a shot with no --before needs --shows, a line saying what it shows, then --check"
          and c[6] == "a Before and After says what changed with --changed, not --shows", json.dumps(c[2:]))
    check("183: the heading of a shot with no before leads with what it shows, then Check:",
          o["heading"][3] == "The card at 360. Check: the card fits", str(o["heading"]))
    check("183: the caption file sits beside its PNG under the same name",
          o["captionPath"] == ["/a/b/01-notes.caption.json", "02.side.caption.json"], str(o["captionPath"]))
    f = o["file"]
    check("183: the caption file holds Harbour's four fields, changed, check, beforeAfter and arrangement, and the "
          "boxes as given", f == {"changed": "Notes column: wider", "check": "the notes wrap", "beforeAfter": True,
                                  "arrangement": "side", "boxes": {"before": ["1,2,3,4"], "after": []}}, json.dumps(f))
    p = o["parse"]
    check("183: a caption file reads back as written, and one that is not JSON, not an object, has no check, or is a "
          "Before and After with no changed reads as why not",
          p[0] == {"changed": "Notes column: wider", "check": "the notes wrap", "beforeAfter": True, "arrangement": "side"}
          and p[1:6] == ["is not JSON", "is not an object", "has no check", "is a Before and After with no changed",
                        "has no changed (null when there is no before)"]
          and p[6]["shows"] == "The card at 360" and o["fileShows"]["shows"] == "The card at 360", json.dumps(p[1:]))
    pk_ = o["pack"]
    check("183: the pack lists each shot's heading in the order of their names, and refuses a shot with no caption, "
          "a caption that reads wrong and a caption with no shot, naming each",
          pk_["lines"] == ["01-card.png: Check: the card fits",
                           "02-bar.png: Bar: shorter. Check: the buttons fit"]
          and pk_["problems"] == [
              "03-raw.png has no heading (no 03-raw.caption.json): make it with packaging/review_shot.js",
              "04-bad.caption.json has no check: make the shot again with packaging/review_shot.js",
              "05-gone.caption.json has no shot beside it (no 05-gone.png)"], json.dumps(pk_))
    check("183: a folder whose every shot has its caption packs with no problem, a shot with no before listed with "
          "what it shows, and one with no shots is refused",
          o["packGood"]["problems"] == [] and len(o["packGood"]["lines"]) == 3
          and o["packGood"]["lines"][2] == "06-new.png: The card at 360. Check: the card fits"
          and o["packEmpty"] == {"lines": [], "problems": ["no shots (.png) in the folder"]}, json.dumps(o["packEmpty"]))
    args = o["args"]
    check("183: the command line takes several boxes for both panels and one panel's own, --stack and --scale, and "
          "pack with its folder",
          args[0]["boxes"] == {"both": [[1, 2, 3, 4], [5, 6, 7, 8]], "before": [], "after": [[9, 9, 9, 9]]}
          and args[0]["arrange"] == "stacked" and args[0]["scale"] == 2 and args[1] == {"mode": "pack", "folder": "review"},
          json.dumps(args[:2]))
    check("183: the command line refuses --box-before or --side with no before, an --out that is not a PNG, an "
          "option it does not know and a shot with no --out",
          args[2] == "--box-before needs a --before" and args[3] == "--stack and --side need a --before"
          and args[4] == "--out must be a .png, not o.jpg" and args[5].startswith("no option --colour")
          and args[6].startswith("usage:"), json.dumps(args[2:]))
    check("183: the command line takes a sidecar for each panel, and refuses --boxes-from-before with no before and "
          "a sidecar given twice for one panel",
          args[7]["boxesFrom"] == {"both": None, "before": "b.shot.json", "after": "a.shot.json"}
          and args[8] == "--boxes-from-before needs a --before"
          and args[9] == "--boxes-from is given twice: one sidecar a panel", json.dumps(args[7:]))


def pack_cli_checks(node: str, folder: Path) -> None:
    review = folder / "pack"
    review.mkdir(exist_ok=True)
    (review / "raw").mkdir(exist_ok=True)
    for name in ("01-card.png", "02-bar.png"):
        png(review / name, 4, 4, (200, 200, 200))
    (review / "01-card.caption.json").write_text(json.dumps({"changed": None, "check": "the card fits", "beforeAfter": False,
                                                             "arrangement": "single"}), encoding="utf-8")
    refused = subprocess.run([node, str(TOOL_JS), "pack", str(review)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    check("183: from the command line, the pack refuses a folder holding a shot with no caption, exit 1, naming it, "
          "and still prints the shots that have one",
          refused.returncode == 1 and "02-bar.png has no heading" in refused.stderr
          and refused.stdout == "01-card.png: Check: the card fits\n", f"{refused.returncode} {refused.stderr.strip()[:200]}")
    (review / "02-bar.caption.json").write_text(json.dumps({"changed": "Bar: shorter", "check": "the buttons fit",
                                                            "beforeAfter": True, "arrangement": "stacked"}), encoding="utf-8")
    good = subprocess.run([node, str(TOOL_JS), "pack", str(review)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    check("183: with every caption there the pack prints each heading in order, exit 0, the raw folder left out",
          good.returncode == 0 and good.stdout == "01-card.png: Check: the card fits\n"
          "02-bar.png: Bar: shorter. Check: the buttons fit\n" and good.stderr == "", f"{good.returncode} {good.stdout!r}")
    drawn = subprocess.run([node, str(TOOL_JS), "--out", str(folder / "x.png"), "--after", str(review / "01-card.png"),
                            "--shows", "The card", "--check", "the card fits"], capture_output=True, text=True, encoding="utf-8", timeout=60)
    check("183: in node a shot is refused, since AppKit draws it, and nothing is written",
          drawn.returncode == 1 and "osascript -l JavaScript on a Mac" in drawn.stderr and not (folder / "x.png").exists()
          and not (folder / "x.caption.json").exists(), drawn.stderr.strip()[:200])


def osa(*args):
    return subprocess.run(["osascript", "-l", "JavaScript", str(TOOL_JS), *map(str, args)], capture_output=True, text=True,
                          encoding="utf-8", timeout=120)


def mac_checks(folder: Path, o) -> None:
    raw = folder / "raw"
    review = folder / "review"
    raw.mkdir(exist_ok=True)
    review.mkdir(exist_ok=True)
    blue, white, cream, ink = (51, 102, 153), (250, 250, 250), (240, 240, 230), (20, 20, 20)
    png(raw / "card-before.png", 300, 200, blue, [(40, 50, 100, 60, white)])
    png(raw / "card-after.png", 300, 200, blue, [(40, 50, 160, 60, white)])
    png(raw / "bar-before.png", 500, 120, cream, [(20, 40, 120, 40, ink)])
    png(raw / "bar-after.png", 500, 120, cream, [(20, 40, 200, 40, ink)])
    png(raw / "phone.png", 180, 320, cream, [(10, 10, 160, 90, white)])

    side = osa("--out", review / "01-card.png", "--before", raw / "card-before.png", "--after", raw / "card-after.png",
               "--changed", "The white card: wider", "--check", "its right edge lines up with the rows under it",
               "--box", "40,50,160,60")
    stacked = osa("--out", review / "02-bar.png", "--before", raw / "bar-before.png", "--after", raw / "bar-after.png",
                  "--changed", "The dark bar: longer", "--check", "the bar ends where the row does",
                  "--box-before", "20,40,120,40", "--box-after", "20,40,200,40")
    single = osa("--out", review / "03-phone.png", "--after", raw / "phone.png", "--shows", "The card at a phone's width",
                 "--check", "the card fits at 180 wide")
    check("183: on a Mac the three shots draw through AppKit, side by side, stacked and one alone, each saying the line "
          "a report repeats",
          [r.returncode for r in (side, stacked, single)] == [0, 0, 0]
          and "(side, " in side.stdout and "(stacked, " in stacked.stdout and "(single, " in single.stdout
          and side.stdout.rstrip().endswith("01-card.png: The white card: wider. Check: its right edge lines up with the rows under it"),
          " | ".join((r.stderr or r.stdout).strip()[:160] for r in (side, stacked, single)))
    if any(r.returncode for r in (side, stacked, single)):
        return
    cap = json.loads((review / "01-card.caption.json").read_text(encoding="utf-8"))
    check("183: the caption file beside the shot holds what changed, the check, side and the box on both panels",
          cap == {"changed": "The white card: wider", "check": "its right edge lines up with the rows under it",
                  "beforeAfter": True, "arrangement": "side", "boxes": {"before": ["40,50,160,60"], "after": ["40,50,160,60"]}},
          json.dumps(cap))
    one = json.loads((review / "03-phone.caption.json").read_text(encoding="utf-8"))
    check("183: a shot with no before is captioned with what it shows and its check",
          one["changed"] is None and one["shows"] == "The card at a phone's width" and one["beforeAfter"] is False
          and one["arrangement"] == "single", json.dumps(one))

    w, h, px = read_png(review / "01-card.png")
    g = 16  # the gutter at the 20 pixel heading these small shots take
    x_after, y_top = g + 300 + g, h - g - 200
    check("183: both panels keep their pixels exactly, at one scale, Before's card 100 wide and After's 160",
          px(g + 10, y_top + 10) == blue and px(g + 40 + 50, y_top + 80) == white and px(g + 40 + 130, y_top + 80) == blue
          and px(x_after + 40 + 130, y_top + 80) == white and px(x_after + 299, y_top + 199) == blue,
          str([px(g + 40 + 130, y_top + 80), px(x_after + 40 + 130, y_top + 80)]))
    line = 3
    pad = line + max(2, jround(g / 6))
    check("183: the dashed box is drawn round the changed part on each panel, its corner in the mark's colour, padded "
          "outside the card",
          px(g + 40 - pad + 1, y_top + 50 - pad + 1) == MARK and px(x_after + 40 - pad + 1, y_top + 50 - pad + 1) == MARK
          and px(x_after + 40 + 160 + pad - 2, y_top + 50 + 60 + pad - 2) == MARK,
          str([px(g + 40 - pad + 1, y_top + 50 - pad + 1), px(x_after + 40 - pad + 1, y_top + 50 - pad + 1)]))

    # the band holds every wrapped line: a long first line and check over a narrow shot, and nothing of the
    # heading's ink at the band's foot or below it (fbboards2's 01 and 09 lost the Check line's last row there)
    words = "The heron's perch by the reed bed, moved to the left of the log so both birds show at once"
    # the check ends on a run of underscores, the lowest ink a line has, so a last line cut short loses it
    long = osa("--out", review / "04-long.png", "--after", raw / "phone.png", "--shows", words,
               "--check", "every word of this long check shows above the shot, the last line included, " + words + " ________")
    check("183: a long heading over a narrow shot draws", long.returncode == 0, long.stderr.strip()[:200])
    if long.returncode == 0:
        w4, h4, px4 = read_png(review / "04-long.png")
        band_ink = (0x1C, 0x27, 0x33)
        page = (0xE8, 0xEB, 0xEE)
        band = 0
        while band < h4 and px4(1, band) == band_ink:
            band += 1
        foot = [(x, y) for y in range(band - 8, band) for x in range(w4) if px4(x, y) != band_ink]
        below = [(x, y) for y in range(band, band + 14) for x in range(w4) if px4(x, y) != page]
        inked = [y for y in range(band) if any(px4(x, y) != band_ink for x in range(4, w4))]
        last = inked[-1] if inked else 0
        run = best = 0
        for x in range(w4):
            run = run + 1 if px4(x, last) != band_ink else 0
            best = max(best, run)
        check("183: the heading band fits every wrapped line, the last line's underscores whole at the foot of its ink, "
              "the band's last 8 rows and the gutter under it clear, nine lines and more over a 180 wide shot",
              band > 9 * 20 and not foot and not below and best >= 40,
              f"band {band}, last ink row {last} with a run of {best}, ink at the foot {foot[:3]}, below {below[:3]}")

    before_bytes = (raw / "card-after.png").read_bytes()
    over = osa("--out", raw / "card-after.png", "--after", raw / "card-after.png", "--shows", "x", "--check", "x")
    check("183: through osascript a shot written over its own raw shot is refused, exit 1, the raw shot unchanged (the "
          "other refusals are node's, above)",
          over.returncode == 1 and (raw / "card-after.png").read_bytes() == before_bytes, over.stderr.strip()[:120])


def shot_box_checks(node: str, folder: Path):
    """shot_box.js on a made-up page: the climb, the crop, the smallest text and the plan a capture writes."""
    script = folder / "shot_box_page.js"
    script.write_text(SHOT_BOX_SCRIPT, encoding="utf-8")
    run = subprocess.run([node, str(script), str(SHOT_BOX_JS)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    o = json.loads(run.stdout) if run.returncode == 0 else None
    check("183: shot_box.js loads in node and runs on a made-up page", o is not None, run.stderr.strip()[:400])
    if not o:
        return None
    g = o["group"]
    check("183: a box whose 8 pixels of room would touch the word beside it (Group's key) climbs past its row, whose "
          "room crosses the menu's border and the next row's word, to the menu, and says so",
          g == {"x": 392, "y": 92, "w": 236, "h": 146, "of": "#group", "chose": "menu", "element": "div.row-menu", "climbed": 2,
                "container": "menu div.row-menu (the room round button#group 2px from its top edge)", "edges": []},
          json.dumps(g))
    check("183: a button with room round it keeps its own box, its rectangle plus 8 on every side, a backdrop picture "
          "under the whole board not counted as touching it",
          o["lonely"] == {"x": 892, "y": 592, "w": 96, "h": 46, "of": "#lonely", "chose": "element", "element": "button#lonely",
                          "climbed": 0, "edges": []}, json.dumps(o["lonely"]))
    check("183: a box that clears nowhere short of the page, and a selector that matches nothing, each come back as a "
          "problem in plain words",
          o["crowded"]["problem"].startswith("no box round #crowded clears its neighbours")
          and 'would touch text "near the owl"' in o["crowded"]["problem"]
          and o["missing"] == {"of": "#heron", "problem": "nothing on the page matches #heron"},
          json.dumps([o["crowded"], o["missing"]]))
    c = o["crop"]
    check("183: the crop holds the box with 24 of room and grows to take in the card its edge would cut",
          {k: c[k] for k in "xywh"} == {"x": 368, "y": 68, "w": 432, "h": 252} and c["grown"] == ["card div.note-card"]
          and c["problems"] == [], json.dumps(c))
    check("183: a box past the window's corner leaves the crop no room, which the crop answers with a mat to ask for, "
          "16 or what the box lacks, not a problem",
          o["edge"]["problems"] == [] and o["edge"]["pad"] == 16
          and o["edge"]["notes"] == ["the box round #edge is flush with the window's edge (-3px of room): compose with --pad 16"],
          json.dumps(o["edge"]))
    check("183: the smallest text is read inside the crop alone, a 9 pixel count on a card and a 14 pixel label on a "
          "board drawn at half size reading 7",
          o["minMenu"]["px"] == 13 and o["minCard"]["px"] == 9 and o["minCard"]["text"] == "3 sightings"
          and o["minBoard"]["px"] == 7 and o["minBoard"]["text"] == "Heron 05:40",
          json.dumps([o["minMenu"], o["minCard"], o["minBoard"]]))
    plan = o["plan"]
    check("183: the plan a capture writes holds the device scale, the crop, each box in the crop's own coordinates "
          "with what it chose, the smallest text and no problem, and lists a box that clears nowhere as one",
          plan["scale"] == 2 and plan["crop"] == {"x": 368, "y": 68, "w": 432, "h": 252} and plan["problems"] == []
          and plan["boxes"] == [{"x": 24, "y": 24, "w": 236, "h": 146, "of": "#group", "chose": "menu", "element": "div.row-menu",
                                 "container": "menu div.row-menu (the room round button#group 2px from its top edge)", "edges": []}]
          and plan["minText"]["px"] == 13 and len(o["planBad"]["problems"]) == 1, json.dumps(plan))
    check("183: what a part is comes from its role or its class's last word: a menu, a menu row, a card, a close "
          "button that is no card, the top rail as a bar, a dialog",
          o["kinds"] == ["menu", "row", "card", "block", "bar", "dialog"], str(o["kinds"]))
    check("183: a button in a full-width bar at the window's foot keeps its own box, its rectangle plus 8, across "
          "the bar's own border and past the window, while it clears the bar's other buttons and words",
          o["quotes"] == {"x": 76, "y": 763, "w": 76, "h": 38, "of": "#quotes", "chose": "element", "element": "button#quotes",
                          "climbed": 0, "edges": []}, json.dumps(o["quotes"]))
    check("183: a button whose room would touch the bar's next word climbs to the bar",
          o["notes"].get("chose") == "bar" and o["notes"].get("element") == "div.status-bar", json.dumps(o["notes"]))
    bp = o["barPlan"]
    check("183: a box flush with the window's edge is no problem in the plan: it asks for --pad 16 and says why",
          bp["problems"] == [] and bp["pad"] == 16 and len(bp["notes"]) == 1
          and "#quotes is flush with the window's edge" in bp["notes"][0] and bp["notes"][0].endswith("compose with --pad 16")
          and plan["pad"] == 0, json.dumps(bp))
    r = o["rename"]
    check("183: a menu row flush with the edges of a menu drawn by its background and shadow alone, with no border, "
          "climbs to the menu, and the box says the menu's edge was why",
          {k: r.get(k) for k in ("x", "y", "w", "h", "chose", "element")} == {"x": 32, "y": 452, "w": 216, "h": 104, "chose": "menu",
                                                                            "element": "div.tag-menu"}
          and r.get("container", "").startswith("menu div.tag-menu (the room round div#rename -8px from its top edge"), json.dumps(r))
    w = o["water"]
    check("183: a button whose box would come 7 pixels inside a card's border, touching nothing, climbs to the card",
          {k: w.get(k) for k in ("x", "y", "w", "h", "chose", "element")} == {"x": 292, "y": 452, "w": 256, "h": 156, "chose": "card",
                                                                            "element": "div.plant-card"}
          and w.get("container") == "card div.plant-card (the room round button#water 7px from its left edge)", json.dumps(w))
    sw = o["sowPlan"]["boxes"][0] if o["sowPlan"]["boxes"] else {}
    check("183: a button 12 pixels clear of its section's divider and 32 inside its panel keeps its own box, and the "
          "plan lists both edges in the crop's coordinates, the section by its foot alone, the panel by its colour on "
          "every side",
          o["sow"].get("chose") == "element" and o["sowPlan"]["problems"] == []
          and sw.get("edges") == [{"x": 16, "y": 16, "w": 228, "h": 96, "of": "block div.seed-list", "sides": ["bottom"]},
                                  {"x": 0, "y": 0, "w": 260, "h": 200, "of": "card div.side-panel", "sides": ["top", "right", "bottom", "left"]}],
          json.dumps(o["sowPlan"]))
    raw = folder / "sidecar-raw"
    raw.mkdir(exist_ok=True)
    wp = o["waterPlan"]
    (raw / "water-after.shot.json").write_text(json.dumps(wp), encoding="utf-8")
    flat_png(raw / "water-after.png", int(wp["crop"]["w"] * 2), int(wp["crop"]["h"] * 2), (250, 248, 240))
    # the same capture with the button's own box put back by hand, the card's edge with it: the box the
    # climb refused, 7 pixels inside the card's left border
    hand = json.loads(json.dumps(wp))
    hand["boxes"] = [{"x": 39, "y": 104, "w": 96, "h": 44, "of": "#water", "chose": "element", "element": "button#water",
                      "edges": [{"x": 32, "y": 32, "w": 240, "h": 140, "of": "card div.plant-card", "sides": ["top", "right", "bottom", "left"]}]}]
    (raw / "water-hand.shot.json").write_text(json.dumps(hand), encoding="utf-8")
    flush = json.loads(json.dumps(wp))
    flush["boxes"] = [{"x": 12, "y": 12, "w": 216, "h": 60, "of": "#rename", "chose": "element", "element": "div#rename",
                       "edges": [{"x": 20, "y": 20, "w": 200, "h": 88, "of": "menu div.tag-menu", "sides": ["top", "right", "bottom", "left"]}]}]
    (raw / "rename-hand.shot.json").write_text(json.dumps(flush), encoding="utf-8")
    (raw / "menu-after.shot.json").write_text(json.dumps(plan), encoding="utf-8")
    (raw / "bar-after.shot.json").write_text(json.dumps(bp), encoding="utf-8")
    flat_png(raw / "bar-after.png", int(bp["crop"]["w"] * 2), int(bp["crop"]["h"] * 2), (250, 248, 240))
    (raw / "bad.shot.json").write_text(json.dumps(o["planBad"]), encoding="utf-8")
    flat_png(raw / "menu-after.png", 864, 504, (250, 248, 240))
    return plan


def sidecar_cli_checks(node: str, folder: Path, plan: dict) -> None:
    """review_shot.js reading a capture's sidecar from the command line, in node, which stops at the drawing."""
    raw = folder / "sidecar-raw"
    out = folder / "sidecar-review"
    out.mkdir(exist_ok=True)

    def shot(*args):
        return subprocess.run([node, str(TOOL_JS), "--out", str(out / "01.png"), *map(str, args)], capture_output=True,
                              text=True, encoding="utf-8", timeout=60)

    good = shot("--after", raw / "menu-after.png", "--shows", "The card's menu", "--check", "Group sits first",
                "--boxes-from", raw / "menu-after.shot.json")
    check("183: a shot boxed from its capture's sidecar, at the sidecar's device scale, passes every rule and stops "
          "only at the drawing in node, nothing written",
          good.returncode == 1 and "osascript -l JavaScript on a Mac" in good.stderr and not (out / "01.png").exists(),
          good.stderr.strip()[:300])
    bad = shot("--after", raw / "menu-after.png", "--shows", "x", "--check", "y", "--boxes-from", raw / "bad.shot.json")
    check("183: a sidecar listing the capture's problems is refused, exit 1, each problem named",
          bad.returncode == 1 and "lists the capture's problems: no box round #crowded" in bad.stderr, bad.stderr.strip()[:300])
    flat_png(raw / "small.png", 400, 300, (250, 248, 240))
    wrong = shot("--after", raw / "small.png", "--shows", "x", "--check", "y", "--boxes-from", raw / "menu-after.shot.json")
    check("183: a sidecar made for another crop is refused, naming both sizes",
          wrong.returncode == 1 and "was written for a 432 by 252 crop, but the after shot is 200 by 150 at scale 2" in wrong.stderr,
          wrong.stderr.strip()[:300])
    nopad = shot("--after", raw / "bar-after.png", "--shows", "The status bar", "--check", "Quotes",
                 "--boxes-from", raw / "bar-after.shot.json")
    padded = shot("--after", raw / "bar-after.png", "--shows", "The status bar", "--check", "Quotes",
                  "--boxes-from", raw / "bar-after.shot.json", "--pad", "16")
    check("183: a shot whose sidecar asks for a mat is refused without --pad 16, and with it the box, past the shot's "
          "own edge, counts its 8 pixels from the padded panel's edge and passes",
          nopad.returncode == 1 and "says a box sits flush with the window's edge: compose with --pad 16" in nopad.stderr
          and padded.returncode == 1 and "osascript -l JavaScript on a Mac" in padded.stderr,
          (nopad.stderr + " | " + padded.stderr).strip()[:400])
    climbed = shot("--after", raw / "water-after.png", "--shows", "The plant card", "--check", "Water",
                   "--boxes-from", raw / "water-after.shot.json")
    near = shot("--after", raw / "water-after.png", "--shows", "The plant card", "--check", "Water",
                "--boxes-from", raw / "water-hand.shot.json")
    on = shot("--after", raw / "water-after.png", "--shows", "The tag menu", "--check", "Rename",
              "--boxes-from", raw / "rename-hand.shot.json")
    check("183: the card's box shotBox climbed to passes, and the button's own box put back in the sidecar, 7 pixels "
          "inside the card's border, is refused, exit 1, as is a menu row's box on the menu's edge, each naming the edge",
          climbed.returncode == 1 and "osascript -l JavaScript on a Mac" in climbed.stderr
          and near.returncode == 1 and "the box round #water comes 7px inside the left edge of card div.plant-card, under the 8" in near.stderr
          and on.returncode == 1 and "the box round #rename comes -8px inside the top edge of menu div.tag-menu" in on.stderr,
          (climbed.stderr + " | " + near.stderr + " | " + on.stderr).strip()[:500])
    flat_png(raw / "wide.png", 1300, 300, (250, 248, 240))
    (raw / "wide.shot.json").write_text(json.dumps({"tool": "shot_box", "scale": 1, "crop": {"x": 0, "y": 0, "w": 1300, "h": 300},
                                                    "boxes": [], "minText": {"px": 13, "text": "05:40"}, "problems": []}), encoding="utf-8")
    small = shot("--after", raw / "wide.png", "--shows", "The log", "--check", "the times", "--box", "100,100,200,50")
    check("183: the sidecar beside a raw shot is read without being named, and its 13 pixel text in a 1,332 wide "
          "composite, 8.8 at 900, is refused",
          small.returncode == 1 and 'the smallest text in the after shot, 13px ("05:40"), would show at 8.8px' in small.stderr,
          small.stderr.strip()[:300])


def mac_sidecar_checks(folder: Path) -> None:
    """The sidecar's box drawn at device scale 2, where the page measured it."""
    raw = folder / "sidecar-raw"
    out = folder / "sidecar-review"
    drawn = osa("--out", out / "02-menu.png", "--after", raw / "menu-after.png", "--shows", "The card's menu",
                "--check", "Group sits first", "--boxes-from", raw / "menu-after.shot.json")
    check("183: on a Mac a shot boxed from its sidecar draws at the sidecar's scale", drawn.returncode == 0, drawn.stderr.strip()[:200])
    if drawn.returncode:
        return
    cap = json.loads((out / "02-menu.caption.json").read_text(encoding="utf-8"))
    w, h, px = read_png(out / "02-menu.png")
    g = 16
    band = 0
    while band < h and px(1, band) == (0x1C, 0x27, 0x33):
        band += 1
    top = band + 2 * g  # the panel, a gutter under the band, in the PNG's pixels at scale 2
    corner = (2 * g + 2 * 24 + 2, top + 2 * 24 + 2)
    bar = osa("--out", out / "03-bar.png", "--after", raw / "bar-after.png", "--shows", "The status bar", "--check", "Quotes",
              "--boxes-from", raw / "bar-after.shot.json", "--pad", "16")
    if bar.returncode == 0:
        bw, bh, bpx = read_png(out / "03-bar.png")
        bband = 0
        while bband < bh and bpx(1, bband) == (0x1C, 0x27, 0x33):
            bband += 1
        t = bband + 2 * g  # the padded panel's top, in pixels at scale 2
        shot_bottom = t + 2 * 16 + 2 * 61  # the shot's own foot: the 16 mat, then 61 of crop
        check("183: with --pad 16 the shot sits in a mat of the page's colour, its own edge drawn as a thin line, and "
              "the box's foot lies in the mat below the shot, where the window ended",
              bpx(2 * g + 4, t + 4) == (0xE8, 0xEB, 0xEE) and bpx(2 * (g + 16) - 1, t + 40) == (0xB7, 0xBE, 0xC6)
              and bpx(2 * (g + 16 + 24) + 2, shot_bottom) == MARK and bw == 2 * (124 + 2 * 16 + 2 * g),
              f"{bw} {bpx(2 * g + 4, t + 4)} {bpx(2 * (g + 16) - 1, t + 40)} {bpx(2 * (g + 16 + 24) + 2, shot_bottom)}")
    else:
        check("183: on a Mac a shot with --pad 16 draws", False, bar.stderr.strip()[:200])
    check("183: the composite is the crop at twice its CSS size with its gutters, and the dashed box's corner sits "
          "where the sidecar put it, with no pad added",
          w == 2 * (432 + 2 * g) and cap["boxes"] == {"before": [], "after": ["24,24,236,146"]} and px(*corner) == MARK
          and px(corner[0] - 6, corner[1] - 6) == (250, 248, 240), f"{w} {cap['boxes']} {px(*corner)}")
