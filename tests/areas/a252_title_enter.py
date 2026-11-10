"""Area 252: one Enter keeps a label's title (22 October 2026). Since the description's box came under the
title's on 21 October, Enter in the title went to the description, so a PET made with G and named was kept only
on a second Enter. Now Enter keeps the title and the description and ends the edit in one press, from either box,
Tab or Shift + Enter goes from the title to the description, Shift + Tab back, and Esc leaves both as they were.

The checks run the page's own thTitleOpen and thTitleDone in node, with the canvas around them stubbed, on a
board with one label on a made-up topic, living with a dog: a new label named with one Enter, a rename, a
description reached by Tab and by Shift + Enter and kept with Enter, and Esc.
"""
from __future__ import annotations

import json
import shutil
import subprocess

from . import support
from .support import TOOL, check, skip

HARNESS = r"""
const fs = require('fs');
const js = fs.readFileSync(process.argv[2], 'utf8');
const cut = (head) => { const at = js.indexOf(head); return js.slice(at, js.indexOf('\n}\n', at) + 3); };
const line = (head) => { const at = js.indexOf(head); return js.slice(at, js.indexOf('\n', at) + 1); };
const src = [line('const TH_UNTITLED_SAVED'), line('const TH_UNTITLED = '), line('const thUntitled = '),
  line('const thLabelKept = '), line('const thLabelShown = '), line('function thGroup('), line('const thDescOf'), cut('function thSetDesc('),
  line('const thDescStep'), line('const TH_TITLE_INSET'), line('const TH_TITLE_RIGHT'), cut('function thTitleOpen('), cut('function thTitleDone(')].join('\n');

const doc = { activeElement: null };
function node(tag) {
  const on = {};
  const n = { tag, value: '', hidden: false, style: {}, scrollHeight: 20, offsetWidth: 200, kids: [],
    classList: { add() {}, remove() {} }, setAttribute() {}, setSelectionRange() {}, select() {},
    addEventListener: (type, fn) => { (on[type] = on[type] || []).push(fn); },
    appendChild(k) { this.kids.push(k); },
    fire(type, e) { (on[type] || []).forEach((fn) => fn(e)); },
    focus() { const was = doc.activeElement; if (was === this) return; doc.activeElement = this;
      if (was) was.fire('blur', { relatedTarget: this }); },
  };
  return n;
}
function key(box, k, mods) {
  const e = Object.assign({ key: k, shiftKey: false, altKey: false, metaKey: false, ctrlKey: false, isComposing: false,
    defaultPrevented: false, preventDefault() { this.defaultPrevented = true; }, stopPropagation() {} }, mods || {});
  box.fire('keydown', e);
}

function run(script) {
  const steps = [];
  doc.activeElement = null;
  const label = node('label');
  const parts = { '.th-title': node('div'), '.th-words': node('div'), '.th-desc': node('p') };
  label.querySelector = (sel) => parts[sel] || null;
  const TH = { face: 'canvas', v: { groups: [{ id: 'g1', label: 'Walks at dawn' }] }, removed: [], layout: {},
    els: { labels: { g1: label } }, editing: null };
  const stubs = {
    TH, document: { createElement: (t) => node(t) },
    thRefuse: () => false, thNoteDone() {}, thUnitHead: () => 'PET', thUnit: () => 'pet', thSnap: () => ({}),
    thLabelBoxes: () => ({}), thMeasure() {}, thPlace() {}, thLocked: () => false, thCardEditDone() {},
    thStickyEditDone() {}, thRender() { steps.push('render'); }, thDone: (b, what) => steps.push(what),
    thTableTitleOpen() {},
  };
  const names = Object.keys(stubs);
  const api = new Function(...names, src + '\nreturn { thTitleOpen, thTitleDone };')(...names.map((n) => stubs[n]));
  // the two boxes, in the layer laid over the label since subpetjump (10 November)
  const boxes = () => (parts['.th-words'].kids[0] || { kids: [] }).kids;
  script({ api, boxes, TH, doc });
  const g = TH.v.groups[0];
  return { label: g.label, description: g.description || null, open: !!TH.editing,
    focus: doc.activeElement === boxes()[1] ? 'description' : doc.activeElement === boxes()[0] ? 'title' : null, steps };
}

const out = {};
// a new label from G, its box empty, named and kept with one Enter
out.fresh = run(({ api, boxes }) => {
  api.thTitleOpen('g1', { fresh: true });
  boxes()[0].value = 'Out in all weathers';
  key(boxes()[0], 'Enter');
});
// a rename, one Enter
out.rename = run(({ api, boxes }) => {
  api.thTitleOpen('g1');
  boxes()[0].value = 'Walks at dawn and dusk';
  key(boxes()[0], 'Enter');
});
// Tab goes to the description, Enter there keeps both
out.tab = run(({ api, boxes }) => {
  api.thTitleOpen('g1');
  boxes()[0].value = 'Out in all weathers';
  key(boxes()[0], 'Tab');
  boxes()[1].value = 'The walks that set the shape of every day';
  key(boxes()[1], 'Enter');
});
out.tabMid = run(({ api, boxes }) => { api.thTitleOpen('g1'); key(boxes()[0], 'Tab'); });
// Shift + Enter goes to the description too
out.shiftMid = run(({ api, boxes }) => { api.thTitleOpen('g1'); key(boxes()[0], 'Enter', { shiftKey: true }); });
// Shift + Tab from the description goes back to the title
out.backMid = run(({ api, boxes }) => {
  api.thTitleOpen('g1'); key(boxes()[0], 'Tab'); key(boxes()[1], 'Tab', { shiftKey: true });
});
// Esc leaves both as they were
out.esc = run(({ api, boxes }) => {
  api.thTitleOpen('g1');
  boxes()[0].value = 'Something else';
  key(boxes()[0], 'Tab');
  boxes()[1].value = 'Not this';
  key(boxes()[1], 'Escape');
});
console.log(JSON.stringify(out));
"""


def test_title_enter(scratch):
    print("\n252. One Enter keeps a label's title and ends the edit, Tab or Shift + Enter goes to its description "
          "(22 October)")
    node = shutil.which("node")
    if not node:
        skip("252: the title's keys", "no node on this machine")
        return
    harness = scratch / "title-enter-252.js"
    harness.write_text(support.i18n_js() + "globalThis.t = t;\n" + HARNESS, encoding="utf-8")
    run = subprocess.run([node, str(harness), str(support.source("apps/idiograph/static/themes.js"))], capture_output=True, text=True,
                         encoding="utf-8", timeout=60)
    if run.returncode:
        check("252: the harness runs", False, run.stderr[-600:])
        return
    out = json.loads(run.stdout)
    fresh = out["fresh"]
    check("252: a new label named with one Enter keeps its name and the edit ends, one step of undo",
          fresh["label"] == "Out in all weathers" and not fresh["open"] and fresh["steps"] == ["Made a theme"]
          and fresh["description"] is None, json.dumps(fresh))
    rename = out["rename"]
    check("252: a rename kept with one Enter",
          rename["label"] == "Walks at dawn and dusk" and not rename["open"] and rename["steps"] == ["Renamed a label"],
          json.dumps(rename))
    check("252: Tab and Shift + Enter in the title go to the description, the edit still open",
          out["tabMid"]["open"] and out["tabMid"]["focus"] == "description"
          and out["shiftMid"]["open"] and out["shiftMid"]["focus"] == "description", json.dumps([out["tabMid"], out["shiftMid"]]))
    check("252: Shift + Tab in the description goes back to the title",
          out["backMid"]["open"] and out["backMid"]["focus"] == "title", json.dumps(out["backMid"]))
    tab = out["tab"]
    check("252: a description reached by Tab is kept with Enter, the title with it, in one step",
          tab["label"] == "Out in all weathers" and tab["description"] == "The walks that set the shape of every day"
          and not tab["open"] and tab["steps"] == ["Renamed a label and its description"], json.dumps(tab))
    esc = out["esc"]
    check("252: Esc leaves the title and the description as they were",
          esc["label"] == "Walks at dawn" and esc["description"] is None and not esc["open"], json.dumps(esc))
