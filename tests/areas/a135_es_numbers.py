from __future__ import annotations

import json
import shutil

from . import support
from .support import check, skip


def test_es_numbers(scratch):
    print("\n135. The pairs numbered, 14 October: each pair of statement and key quote on the Experiential statements "
          "screen opens with its heading, Experiential statement 1 and on, numbered again on Add another, a removal and "
          "its undo, and the cross inside the statement's field gives way to the shared Remove at the heading's right, "
          "which draws a red line round the whole pair while it has the pointer or the focus. Since the test review of 18 "
          "October the markup, the red line and the words are review shots, and Remove, the numbers and their undo stay")
    import subprocess
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    line = lambda src, start: start + src.split(start, 1)[1].split("\n", 1)[0] if start in src else ""
    node = shutil.which("node")

    # ── A. Remove does what the cross did
    check("135: Remove does what the cross did, the same click and the same focus after, and since 18 October (186) Tab "
          "reaches the bin after its key quote, the fields of a hidden column passed over",
          "if (remove) removePair(remove.closest('.pair'));" in app
          and "const order = [...$('pairs').querySelectorAll('.pair-es, .pair-kq, .pair-remove'),\n      ...($('cx-list') ? $('cx-list').querySelectorAll('.cx-field') : []), $('en')]\n      .filter((el) => el.getClientRects().length);" in app
          and "if (next) next.querySelector('.pair-es').focus();" in fn(app, "removePair")
          and "undoPush({" in fn(app, "removePair"))

    # ── C. in node: the numbers after a turn drawn, Add another, a removal, its undo and redo, and one pair alone
    if not node:
        skip("135: the numbers in node", "no node on this machine")
    else:
        harness = r"""
let pairSeq = 0;
const PROMPT_FALLBACK = 'A prompt';
const S = { prompt: '', pairFocus: null, dirty: false };
const escAttr = (s) => String(s).replace(/"/g, '&quot;');
let focused = null;
const undos = [];
const said = [];
const grow = () => {};
const growPairs = () => {};
const drawWordCount = () => {};
const runNudges = () => {};
const drawAct = () => {};
const markKeyQuotes = () => {};
const current = () => ({ key: 'Initial:7' });
const undoPush = (e) => { undos.push(e); };
const say = (t) => { said.push(t); };
const fakeEl = (tag, attrs, text) => ({ tag, attrs, textContent: text, value: '', placeholder: '',
  setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; },
  focus() { focused = this; } });
const box = { list: [] };
function parse(html) {
  const starts = [...html.matchAll(/<div class="pair" data-pid="([^"]+)">/g)];
  return starts.map((m, i) => {
    const chunk = html.slice(m.index, i + 1 < starts.length ? starts[i + 1].index : html.length);
    const kids = {};
    for (const t of chunk.matchAll(/<(\w+)\b([^>]*)>([^<]*)/g)) {
      const attrs = {};
      for (const a of t[2].matchAll(/([\w-]+)="([^"]*)"/g)) attrs[a[1]] = a[2];
      const el = fakeEl(t[1], attrs, t[3]);
      for (const c of (attrs.class || '').split(/\s+/)) if (c && !kids['.' + c]) kids['.' + c] = el;
    }
    const pair = { dataset: { pid: m[1] }, chunk, querySelector: (sel) => kids[sel] || null,
      remove() { const at = box.list.indexOf(pair); if (at >= 0) box.list.splice(at, 1); },
      insertAdjacentHTML(where, h) { box.list.splice(box.list.indexOf(pair) + (where === 'beforebegin' ? 0 : 1), 0, ...parse(h)); } };
    return pair;
  });
}
Object.defineProperty(box, 'innerHTML', { set(h) { box.list = parse(h); } });
box.querySelectorAll = (sel) => (sel === '.pair' ? [...box.list] : []);
box.querySelector = (sel) => {
  const m = sel.match(/^\.pair\[data-pid="([^"]+)"\]$/);
  return m ? box.list.find((p) => p.dataset.pid === m[1]) || null : null;
};
box.insertAdjacentHTML = (where, h) => { if (where === 'beforeend') box.list.push(...parse(h)); };
const $ = (id) => (id === 'pairs' ? box : null);
"""
        pieces = [harness, "const MAC = true;\n" + "const keyName = " + app.split("const keyName = ", 1)[1].split(";\n", 1)[0] + ";\n" + line(app, "const PAIR_QUOTE_HINT = "), line(app, "const GRAMM_OFF = "),
                  line(app, "const pairEls = "), line(app, "const pairOf = "), line(app, "const pairsNow = "),
                  line(app, "const pairEmpty = ")] + [whole(app, n) for n in (
                      "pairHtml", "pairsDrawn", "drawPairs", "insertPair", "pairsChanged", "addAnother", "removePair", "pairPut")]
        scenario = r"""
const heads = () => box.list.map((p) => p.querySelector('.pair-num').textContent);
const names = () => box.list.map((p) => p.querySelector('.pair-remove').getAttribute('aria-label'));
const statements = () => box.list.map((p) => p.querySelector('.pair-es').value);
const out = {};
drawPairs([{ es: 'Calm comes with the hum of the hive', kq: '"the hum settles me"' },
           { es: 'Fear of the swarm gives way to care', kq: '"I used to run from them"' },
           { es: 'The bees set the pace of the morning', kq: '"they decide when I start"' }]);
out.drawn = { heads: heads(), names: names(),
  inHead: box.list[0].chunk.split('<div class="pair-qhead">')[1].split('</div>')[0].includes('pair-remove') };
const added = addAnother();
out.added = { heads: heads(), last: names()[3], focus: focused === added.querySelector('.pair-es') };
removePair(box.list[1]);
out.removed = { heads: heads(), names: names(), statements: statements(), undos: undos.length,
  focus: focused === box.list[1].querySelector('.pair-es') };
undos[0].undo(undos[0]);
out.undone = { heads: heads(), names: names(), statements: statements(), said: said[said.length - 1] };
undos[0].redo(undos[0]);
out.redone = { heads: heads(), statements: statements() };
drawPairs([{ es: 'Alone on the turn', kq: '' }]);
out.one = { heads: heads(), names: names() };
removePair(box.list[0]);
out.oneOut = { heads: heads(), statements: statements() };
drawPairs([]);
out.none = heads();
console.log(JSON.stringify(out));
"""
        script = scratch / "es-numbers-135.js"
        script.write_text(support.i18n_js() + "\n".join(pieces + [scenario]), encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("135: the numbers run in node", False, run.stderr.strip()[:300])
        else:
            out = json.loads(run.stdout)
            # the numbers alone since 17 October (172), the words Experiential statement in each field's name
            n = lambda k: [str(i) for i in range(1, k + 1)]
            # the bin named alike on every pair since 18 October (186), where each named its number
            named = lambda k: ["Remove this statement"] * k
            first, second, third = ("Calm comes with the hum of the hive", "Fear of the swarm gives way to care",
                                    "The bees set the pace of the morning")
            check("135: in node, a passage of three pairs reads 1, 2 and 3, each with its bin, off the line of its Key "
                  "quote label since 18 October (186)",
                  out["drawn"]["heads"] == n(3) and out["drawn"]["names"] == named(3) and not out["drawn"]["inHead"], str(out["drawn"]))
            check("135: in node, Add another adds a pair numbered 4 and gives its statement the caret",
                  out["added"]["heads"] == n(4) and out["added"]["last"] == named(4)[3] and out["added"]["focus"], str(out["added"]))
            check("135: in node, removing the second numbers the rest again at once, the third now 2, one step of undo, "
                  "the caret in the statement now in its place",
                  out["removed"]["heads"] == n(3) and out["removed"]["names"] == named(3)
                  and out["removed"]["statements"] == [first, third, ""] and out["removed"]["undos"] == 1
                  and out["removed"]["focus"], str(out["removed"]))
            check("135: in node, its undo puts it back as 2 and the rest follow, and redo takes it out again",
                  out["undone"]["heads"] == n(4) and out["undone"]["names"] == named(4)
                  and out["undone"]["statements"] == [first, second, third, ""] and bool(out["undone"]["said"])
                  and out["redone"]["heads"] == n(3) and out["redone"]["statements"] == [first, third, ""], str(out["undone"]))
            check("135: in node, one pair alone is still numbered 1, after a removal and on a passage with none",
                  out["one"]["heads"] == n(1) and out["one"]["names"] == named(1) and out["oneOut"]["heads"] == n(1)
                  and out["oneOut"]["statements"] == [""] and out["none"] == n(1), str(out["one"]))
