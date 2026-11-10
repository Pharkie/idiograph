from __future__ import annotations

import json
import shutil

from . import support
from .support import check, skip


def test_sift_columns_drag(scratch):
    print("\n125. One handle for every list in his order, 12 October: the home rows' handle shared by Set columns and the "
          "exclusion reasons, their arrow buttons gone, Alt and an arrow moving a row, a heading dragged left or right "
          "moving its column and saved as Set columns saves, a click on a heading still sorting, and no column "
          "resizing, by design")
    import subprocess

    app_src = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    sift_src = support.text("apps/sift/static/sift.js")
    ssjs = support.text("apps/sift/static/sift_search.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    node = shutil.which("node")
    base = scratch / "sift-cols-125"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)

    # ── B. in node: the handle on the home rows, Set columns, the headings and the reasons
    if not node:
        skip("125: the handle, the headings and the reasons in node", "node is not installed")
    else:
        line = lambda src, start: next(l for l in src.splitlines() if l.startswith(start))
        pieces = [line(app_src, "const esc = "), line(app_src, "const escAttr = "),
                  whole(app_src, "gripHtml"), whole(app_src, "gripDrag"), whole(app_src, "gripKeys"),
                  "const SF_COLS = " + sift_src.split("const SF_COLS = ", 1)[1].split("};", 1)[0] + "};",
                  line(sift_src, "const SF_EXTRA = "), line(sift_src, "const SF_ID = "), line(sift_src, "const SF_TADEC = "),
                  "const sfStageCols = " + sift_src.split("const sfStageCols = ", 1)[1].split("\n};", 1)[0] + "\n};",
                  whole(sift_src, "sfColumns"), whole(sift_src, "sfColsDraw"), whole(sift_src, "sfColsGrip"),
                  whole(sift_src, "sfColsMoved"), whole(sift_src, "sfColsSave"), whole(sift_src, "sfColsKey"),
                  whole(sift_src, "sfColMoved"), whole(support.table_js(), "tbTvHeadHtml"), line(support.table_js(), "const tbHeadKind = "),
                  line(sift_src, "const sfHeadKind = "), whole(sift_src, "sfTvHeadDraw"),
                  whole(sift_src, "sfThClick"),
                  line(sift_src, "const SF_TH_TRAVEL = "), line(sift_src, "const SF_TH_EDGE = "), line(sift_src, "const SF_TH_STEP = "),
                  line(sift_src, "const sfThMoves = "), whole(sift_src, "sfThGaps"), whole(sift_src, "sfThMark"),
                  whole(sift_src, "sfThPress"),
                  whole(ssjs, "sfsReasonRows"), whole(ssjs, "sfsDrawReasons"), whole(ssjs, "sfsReasonGrip"),
                  whole(ssjs, "sfsReasonsMoved"), whole(ssjs, "sfsReasonSaid"), whole(ssjs, "sfsKeyDown"),
                  "function sfsReasonsChanged(" + fn(ssjs, "sfsReasonsChanged") + "\n}", whole(ssjs, "sfsReasonsSave")]
        harness = r"""
const calls = [];
async function api(path, body) { calls.push([path, JSON.parse(JSON.stringify(body))]); return {}; }
const said = [];
function say(t) { said.push(t); }
const needsRestart = () => false;
const RESTART_LINE = 'restart';
const sfExtraLabel = (name) => name;
const document = { activeElement: null };
const window = { on: {}, addEventListener(t, f) { (this.on[t] = this.on[t] || []).push(f); },
  removeEventListener(t, f) { this.on[t] = (this.on[t] || []).filter((g) => g !== f); },
  fire(t, ev) { for (const f of (this.on[t] || []).slice()) f(Object.assign({ type: t }, ev)); } };
const listening = () => Object.values(window.on).reduce((n, l) => n + l.length, 0);
function classes() { const set = new Set(); return { set, add: (...c) => c.forEach((x) => set.add(x)), remove: (...c) => c.forEach((x) => set.delete(x)),
  contains: (c) => set.has(c), toggle: (c, on) => (on ? set.add(c) : set.delete(c)) }; }
function plain(id) { return { id, innerHTML: '', textContent: '', hidden: false, classList: classes(), focus() {}, scrollLeft: 0,
  getBoundingClientRect: () => ({ left: 0, right: 700, top: 0, height: 400 }), querySelectorAll: () => [], querySelector: () => null }; }
// a list whose rows are built from the markup it is given, as a page builds them
function makeList(id, rowRe, data) {
  const list = plain(id);
  let html = '';
  list.rows = [];
  Object.defineProperty(list, 'innerHTML', { get: () => html, set: (h) => { html = h; list.rows = [...h.matchAll(rowRe)].map((m) => row(m)); } });
  function row(m) {
    const li = { dataset: data(m), classList: classes(), html: m[0], others: {} };
    li.grip = { focused: 0, disabled: false, focus() { this.focused += 1; document.activeElement = this; },
      // Search's card holds no row, which Search strategy's keys ask first since 18 October (area 178)
      closest: (sel) => (sel.includes('pc-grip') ? li.grip : sel === '.search-card' ? null : li) };
    li.querySelector = (sel) => (sel.includes('pc-grip') || sel.includes('data-act="grip"') ? li.grip : (li.others[sel] = li.others[sel] || {}));
    li.getBoundingClientRect = () => ({ top: list.rows.indexOf(li) * 30, height: 26 });
    Object.defineProperty(li, 'nextElementSibling', { get: () => list.rows[list.rows.indexOf(li) + 1] || null });
    return li;
  }
  list.querySelectorAll = (sel) => (sel.includes('pc-grip') ? list.rows.map((r) => r.grip) : list.rows.slice());
  list.insertBefore = (li, ref) => { list.rows = list.rows.filter((r) => r !== li); const at = ref ? list.rows.indexOf(ref) : -1;
    list.rows.splice(at < 0 ? list.rows.length : at, 0, li); };
  list.appendChild = (li) => list.insertBefore(li, null);
  Object.defineProperty(list, 'lastElementChild', { get: () => list.rows[list.rows.length - 1] || null });
  return list;
}
// the headings, each a cell a hundred pixels wide with its button, built from the markup
function makeHead() {
  const head = plain('sf-thead');
  let html = '';
  head.ths = [];
  Object.defineProperty(head, 'innerHTML', { get: () => html, set: (h) => {
    html = h;
    head.ths = [...h.matchAll(/<th scope="col" class="([^"]+)"[^>]*><button type="button" class="sf-th" data-sort="([^"]+)">/g)].map((m, i) => {
      const th = { classList: classes(), kind: m[1], left: i * 100 };
      th.btn = { dataset: { sort: m[2] }, closest: (sel) => (sel === 'th' ? th : th.btn) };
      th.querySelector = () => th.btn;
      th.getBoundingClientRect = () => ({ left: th.left, right: th.left + 100 });
      return th;
    });
  } });
  head.querySelectorAll = (sel) => (sel === 'th.dragging' ? head.ths.filter((t) => t.classList.contains('dragging')) : head.ths.slice());
  return head;
}
const els = {
  'sf-cols-list': makeList('sf-cols-list', /<li class="sf-col" data-key="([^"]+)"[^>]*>/g, (m) => ({ key: m[1] })),
  'sfs-reasons': makeList('sfs-reasons', /<div class="sfs-reason" data-i="(\d+)">/g, (m) => ({ i: m[1] })),
  'sf-thead': makeHead(),
};
const $ = (id) => els[id] || (els[id] = plain(id));
$('sfs-ask').hidden = true;
$('sfs-mark-card').hidden = true;
$('settings').hidden = true;
$('feedback').hidden = true;
const sfsShown = () => true;
let closed = 0;
function sfColsClose() { closed += 1; }
const sorted = [];
function sfSortBy(key, add) { sorted.push([key, add]); }
const SF = { folder: 'kiln-review', stage: 'ft', sort: [], thDragged: false,
  table: { columns: [{ key: 'title', shown: true }, { key: 'authors', shown: true }, { key: 'year', shown: true },
                     { key: 'abstract', shown: false }, { key: 'decision', shown: true }, { key: 'col_glaze', shown: true }],
           own: [{ key: 'col_glaze', name: 'Glaze', type: 'text' }] } };
const shownCols = () => sfStageCols([SF_ID, ...sfColumns(SF.table).filter((c) => c.shown)], SF.stage);
let refilters = 0;
function sfRefilter() { refilters += 1; sfTvHeadDraw(shownCols()); }
function sfQueue(f) { return f(); }
const SFS = { folder: 'kiln-review', chain: Promise.resolve(), saveTimer: null, reasonTimer: null, plan: { reasons: [] },
  data: { runs: [], reasons_file: { reasons: [{ code: 'K1', meaning: 'Not about kilns' }, { code: 'K2', meaning: 'No firing' },
    { code: 'K3', meaning: 'No glaze' }], said: '' } } };
function sfsSave() {}
function sfsDrawAnswer() {}
const key = (k, target, alt = true) => ({ altKey: alt, key: k, target, prevented: false, stopped: false,
  preventDefault() { this.prevented = true; }, stopPropagation() { this.stopped = true; } });
const order = () => SF.table.columns.map((c) => c.key);
const views = () => calls.filter((c) => c[1].op === 'view').map((c) => c[1].columns.map((x) => x.key));
""" + "\n".join(pieces) + r"""
(async () => {
const out = {};
// the home rows' handle, the markup it had
out.home = gripHtml('P1 Ada');
// Set columns: a handle at each row's left, no arrows
sfColsDraw();
const list = $('sf-cols-list');
out.colsHtml = list.innerHTML;
// Alt and Up on Year's handle moves it above Authors, says its place, keeps the focus and saves the order
const k1 = key('ArrowUp', list.rows[2].grip);
sfColsKey(k1);
out.keyMove = { order: order(), said: $('sf-cols-said').textContent, prevented: k1.prevented, views: views(),
  focused: list.rows.map((r) => r.grip.focused), refilters };
// a plain arrow on a handle moves nothing, and Esc on it closes the card as anywhere in it
const k2 = key('ArrowUp', list.rows[1].grip, false);
sfColsKey(k2);
sfColsKey(key('Escape', list.rows[1].grip, false));
out.plainKey = { order: order(), prevented: k2.prevented, closed, views: views().length };
// a drag by Title's handle past Year's middle drops it after Year, and saves once on the let go
document.activeElement = null;
const title = list.rows[0];
gripDrag({ button: 0, pointerId: 5, preventDefault() {} }, title, list, sfColsGrip());
out.dragging = title.classList.contains('dragging');
window.fire('pointermove', { pointerId: 5, clientY: 50 });
out.midDrag = list.rows.map((r) => r.dataset.key);
window.fire('pointerup', { pointerId: 5 });
out.dragMove = { order: order(), views: views(), listening: listening() };
// a drag let go where it began saves nothing
gripDrag({ button: 0, pointerId: 6, preventDefault() {} }, list.rows[0], list, sfColsGrip());
window.fire('pointerup', { pointerId: 6 });
out.dragStill = { views: views().length, listening: listening() };
// the headings: the places a heading can go, the ID and At title and abstract none of them
const head = $('sf-thead');
sfTvHeadDraw(shownCols());
out.heads = head.ths.map((t) => t.btn.dataset.sort);
out.gaps = sfThGaps().map((g) => [g.before, g.side, g.x]);
const th = (k) => head.ths.find((t) => t.btn.dataset.sort === k);
const press = (k, x, id, button = 0) => sfThPress({ target: { closest: () => th(k).btn }, button, pointerId: id, clientX: x, clientY: 10 });
// Authors dragged left to the place before Year: no drag under four pixels, then the marker, then saved as Set columns saves
press('authors', 350, 9);
window.fire('pointermove', { pointerId: 9, clientX: 352, clientY: 11 });
out.still = { dragging: th('authors').classList.contains('dragging'), table: $('sf-tbl').classList.contains('sf-th-dragging') };
window.fire('pointermove', { pointerId: 9, clientX: 130, clientY: 12 });
out.marked = { dragging: th('authors').classList.contains('dragging'), table: $('sf-tbl').classList.contains('sf-th-dragging'),
  marks: head.ths.map((t) => [t.btn.dataset.sort, [...t.classList.set].join(' ')]).filter((m) => m[1]) };
window.fire('pointerup', { pointerId: 9 });
out.headMove = { order: order(), views: views().slice(-1), heads: head.ths.map((t) => t.btn.dataset.sort), listening: listening(),
  marks: head.ths.filter((t) => t.classList.set.size).length, table: $('sf-tbl').classList.contains('sf-th-dragging') };
// the click that ends the drag sorts nothing, and the next click on a heading sorts
sfThClick({ target: { closest: () => th('authors').btn }, shiftKey: false });
out.clickAfterDrag = sorted.length;
await new Promise((r) => setTimeout(r, 0));
// Year dragged to the right end goes after the last column shown, the hidden Abstract keeping its place
press('year', 250, 10);
window.fire('pointermove', { pointerId: 10, clientX: 690, clientY: 10 });
out.endMark = head.ths.filter((t) => t.classList.contains('sf-drop-after')).map((t) => t.btn.dataset.sort);
window.fire('pointerup', { pointerId: 10 });
out.endMove = order();
await new Promise((r) => setTimeout(r, 0));
// a press that stays put is a click, and sorts, Shift adding a key, with nothing saved
const before = views().length;
press('title', 250, 11);
window.fire('pointermove', { pointerId: 11, clientX: 252, clientY: 10 });
window.fire('pointerup', { pointerId: 11 });
sfThClick({ target: { closest: () => th('title').btn }, shiftKey: true });
out.click = { sorted: sorted.slice(), saved: views().length - before, listening: listening() };
// the ID's heading and a right button start no drag, and a drag cancelled saves nothing
press('rec_id', 50, 12);
press('title', 250, 13, 2);
out.fixed = listening();
press('title', 250, 14);
window.fire('pointermove', { pointerId: 14, clientX: 120, clientY: 10 });
window.fire('pointercancel', { pointerId: 14 });
out.cancel = { saved: views().length - before, listening: listening(), marks: head.ths.filter((t) => t.classList.set.size).length };
await new Promise((r) => setTimeout(r, 0));
// the exclusion reasons: a handle at each row's left, no arrows
const reasons = $('sfs-reasons');
sfsDrawReasons(true);
out.reasonsHtml = reasons.innerHTML;
// Alt and Down on K1's handle, through Search strategy's own keys, moves it below K2 and writes the list at once
const k3 = key('ArrowDown', reasons.rows[0].grip);
sfsKeyDown(k3);
await SFS.chain;
out.reasonKey = { codes: SFS.reasons.map((r) => r.code), said: $('sfs-reasons-moved').textContent, prevented: k3.prevented,
  sent: calls.filter((c) => c[1].op === 'reasons').map((c) => c[1].rows.map((r) => r.code)),
  focused: reasons.rows.map((r) => r.grip.focused) };
// a drag by K3's handle to the top, written once on the let go
document.activeElement = null;
gripDrag({ button: 0, pointerId: 15, preventDefault() {} }, reasons.rows[2], reasons, sfsReasonGrip());
window.fire('pointermove', { pointerId: 15, clientY: 2 });
window.fire('pointerup', { pointerId: 15 });
await SFS.chain;
out.reasonDrag = { codes: SFS.reasons.map((r) => r.code), sent: calls.filter((c) => c[1].op === 'reasons').map((c) => c[1].rows.map((r) => r.code)),
  html: reasons.innerHTML.split('<div class="sfs-reason"').length - 1, listening: listening() };
console.log(JSON.stringify(out));
})().catch((e) => { console.error(e && e.stack || e); process.exit(1); });
"""
        script = base / "cols-125.js"
        script.write_text(harness, encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        o = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        why = "" if o else (ran.stderr or ran.stdout)[:500]
        km = o.get("keyMove", {})
        check("125: in node, Alt and Up on a row's handle moves it one place, says its new place, keeps the focus on its "
              "handle and saves the whole order through the view op",
              km.get("order") == ["title", "year", "authors", "abstract", "decision", "col_glaze"] and km.get("said") == "Year, 2 of 6"
              and km.get("prevented") is True and km.get("views") == [km.get("order")] and km.get("focused", [0, 0])[1] == 1
              and km.get("refilters") == 1, why or str(km))
        pk = o.get("plainKey", {})
        check("125: in node, a plain arrow on a handle moves nothing, and Esc on it still closes the card",
              pk == {"order": km.get("order"), "prevented": False, "closed": 1, "views": 1}, why or str(pk))
        dm = o.get("dragMove", {})
        check("125: in node, a drag by a row's handle carries it past the next row's middle, and the let go saves the new "
              "order once, the same view op, and lets the pointer go",
              o.get("dragging") is True and o.get("midDrag") == ["year", "title", "authors", "abstract", "decision", "col_glaze"]
              and dm.get("order") == o.get("midDrag") and dm.get("views", [])[-1:] == [o.get("midDrag")] and len(dm.get("views", [])) == 2
              and dm.get("listening") == 0 and o.get("dragStill") == {"views": 2, "listening": 0}, why or str([o.get("midDrag"), dm]))
        check("125, updated 13 October (127): in node, the places a heading can go are the moving headings' left edges and "
              "the last heading's right, never before the ID or between Decision and At title and abstract",
              o.get("heads") == ["rec_id", "year", "title", "authors", "decision", "tadec", "col_glaze"]
              and o.get("gaps") == [["year", "before", 100], ["title", "before", 200], ["authors", "before", 300],
                                     ["decision", "before", 400], ["col_glaze", "before", 600], [None, "after", 700]],
              why or str(o.get("gaps")))
        hm = o.get("headMove", {})
        check("125: in node, a heading moved under four pixels is no drag, then dragged it is marked and a bar marks the "
              "place before Year, and let go its column moves there, saved exactly as Set columns saves, the headings drawn "
              "in the new order and the marks gone",
              o.get("still") == {"dragging": False, "table": False}
              and o.get("marked", {}).get("dragging") is True and o.get("marked", {}).get("table") is True
              and o.get("marked", {}).get("marks") == [["year", "sf-drop-before"], ["authors", "dragging"]]
              and hm.get("order") == ["authors", "year", "title", "abstract", "decision", "col_glaze"]
              and hm.get("views") == [hm.get("order")] and hm.get("heads") == ["rec_id", "authors", "year", "title", "decision", "tadec", "col_glaze"]
              and hm.get("listening") == 0 and hm.get("marks") == 0 and hm.get("table") is False, why or str([o.get("marked"), hm]))
        check("125: in node, a heading let go at the right end goes after the last column shown, the hidden Abstract kept "
              "in its place among the rest",
              o.get("endMark") == ["col_glaze"] and o.get("endMove") == ["authors", "title", "abstract", "decision", "col_glaze", "year"],
              why or str([o.get("endMark"), o.get("endMove")]))
        ck = o.get("click", {})
        check("125: in node, the click that ends a drag sorts nothing, and a press that stays put is a click that sorts, "
              "Shift adding a key, with nothing saved",
              o.get("clickAfterDrag") == 0 and ck == {"sorted": [["title", True]], "saved": 0, "listening": 0}, why or str([o.get("clickAfterDrag"), ck]))
        check("125, updated 13 October (127): in node, the ID's heading and a right button start no drag, and a drag "
              "cancelled saves nothing and leaves no mark",
              o.get("fixed") == 0 and o.get("cancel") == {"saved": 0, "listening": 0, "marks": 0}, why or str([o.get("fixed"), o.get("cancel")]))
        rk = o.get("reasonKey", {})
        check("125: in node, Alt and Down on a reason's handle, heard by Search strategy's own keys, moves it one place, "
              "says its new place, keeps the focus and writes the list at once through the reasons op",
              rk.get("codes") == ["K2", "K1", "K3"] and rk.get("said") == "K1, 2 of 3" and rk.get("prevented") is True
              and rk.get("sent") == [["K2", "K1", "K3"]] and rk.get("focused", [0, 0])[1] == 1, why or str(rk))
        rd = o.get("reasonDrag", {})
        check("125: in node, a drag by a reason's handle to the top reorders the reasons and writes them once on the let go",
              rd.get("codes") == ["K3", "K2", "K1"] and rd.get("sent") == [["K2", "K1", "K3"], ["K3", "K2", "K1"]]
              and rd.get("html") == 3 and rd.get("listening") == 0, why or str(rd))

