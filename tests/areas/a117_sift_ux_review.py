from __future__ import annotations

import csv
import json
import os
import re
import shutil

from . import support
from .support import check, grip_js, sift_words_js, skip


def test_sift_ux_review(scratch):
    print("\n117. Sift reviewed whole, 12 October: the plain fixes of the review, the way back named, New project's line "
          "cleared and the project made opened, No search plan yet, a run's line without its noughts, Screening has "
          "begun, Carry decisions from naming today's run Today, a block's Remove asking first, a decision taken read "
          "Accepted or Rejected, the note on the decision named and kept on the screen, no word selected by a "
          "double-click, the matched count only with proposals, AI propose for the round leaving the rest for later, "
          "the foot bar wrapping on a phone, and the year's and the participants' sliders moving bar by bar")
    import subprocess
    import sift

    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    sjs = support.text("apps/sift/static/sift.js")
    ssjs = support.text("apps/sift/static/sift_search.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: (("async " if f"async function {name}(" in src else "") + f"function {name}(" + fn(src, name) + "\n}")
    node = shutil.which("node")
    base = scratch / "sift-review-117"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)

    # ── B. New project: its line cleared as a field changes, and the project made opened
    check("117: New project's line goes as soon as the folder, the name or the question changes, and Create project opens "
          "the project it made on Search strategy, as Distil's New project does",
          "['rv-folder', 'rv-name', 'rv-question'].forEach((id) => $(id).addEventListener('input', () => rvSaid('')));" in app
          and "if (own && own.made) own.made(got);" in fn(app, "rvMake")
          and "if (got.review) rvShow(got.review);" in fn(support.text("apps/sift/static/sift_settings.js"), "sfpMade")
          and "if (open) rvShow" not in fn(app, "rvMake"))

    # ── C. the screening: the note kept on the screen, the double-click, the matched count, the batch's words, the foot
    note = fn(sjs, "sfNoteSave")
    check("117: a note left is held in its record at once, and its box given the note as kept once its answer lands, so "
          "an earlier act's answer drawn over it never leaves the box empty",
          "st.note = text.trim();" in note and note.index("st.note = text.trim();") < note.index("sfQueue(")
          and "$('sf-note').value = (sfStage(now) || {}).note || '';" in note
          and "document.activeElement !== $('sf-note')" in note)
    check("117: a double-click that opens a row selects no word of it, a drag still selecting text, and a cell of his "
          "still taking its own presses",
          "if (e.detail > 1 && !e.target.closest('.sf-cell-ed, input, textarea, td.sf-ed') && e.target.closest('tr[data-rec]')) "
          "e.preventDefault();" in fn(sjs, "sfTvBoot")
          and "addEventListener('mousedown'" in fn(sjs, "sfTvBoot") and "addEventListener('dblclick'" not in fn(sjs, "sfTvBoot"))
    check("117: the foot bar's matched and overruled show only once a decision meets a proposal",
          "(SF.aiMaster && n('matched') + n('overruled') ? `<span class=\"sf-against\">" in fn(sjs, "sfBar"))
    check("117: AI propose for the round says Proposing and how far, pressed again finishes the call under way and leaves "
          "the rest for later, as Find open-access PDFs does, and never speaks of stopping",
          "'sift.ai.proposing'" in fn(sjs, "sfAiDraw") and "'Finishing this one'" in fn(sjs, "sfAiDraw")
          and "'sift.ai.done_left'" in fn(sjs, "sfAiAll") and "Stop" not in fn(sjs, "sfAiDraw") + fn(sjs, "sfAiAll")
          and "if (SF.batch.stop) break;" in fn(sjs, "sfAiAll"))

    # ── D. a decision taken reads Accepted or Rejected, and a proposal keeps the verbs, in node
    block = sjs.split("/* ── the table's rows: its columns, sort and filter, worked out with no page ── */", 1)[-1].split(
        "/* ── the table, drawn ── */", 1)[0]
    block = support.table_js() + "\n" + block
    lead = app[app.index("const esc = "):app.index("// a line from the server with a command in backticks")]

    # ── E. the sliders bar by bar, in node, on an invented screening of community gardens
    folder = base / "gardens"
    folder.mkdir()
    head = ["rec_id", "title", "authors", "year", "journal", "doi", "sources", "abstract"]
    rows = [["G1", "Raised beds", "Bean, A.", "2012", "Invented Garden Review", "", "Scopus", "Twelve growers."],
            ["G2", "Compost talk", "Leek, B.", "2016", "Invented Garden Review", "", "Scopus", "Eight growers."],
            ["G3", "Seed swaps", "Kale, C.", "2023", "Invented Soil", "", "PsycInfo", "A survey of 640 gardeners."]]
    with open(folder / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(head)
        w.writerows(rows)
    for rec, n in (("G1", "3"), ("G2", "12"), ("G3", "640")):
        sift.set_field(folder, rec, "participants", n)
    sift.set_field(folder, "G1", "rating", "4")
    view = sift.screen(folder)
    drawn = [whole(sjs, name) for name in ("sfRangeEnds", "sfBarsHtml", "sfRangeHtml", "sfRangeMove",
                                            "sfHandleKey", "sfPillHtml", "sfPillSet")]
    if node and "function sfTrack(" in block and all(drawn):
        probe = base / "sift-review-sliders.js"
        probe.write_text("\n".join([block, lead, sift_words_js(sjs),
                                    "const SF = { filters: {}, facetsMore: new Set(), facetsFind: {}, records: [], stage: 'ta' };",
                                    "function sfMeaning(code) { return ''; }", "const sfRoundRows = () => [];",
                                    "const MOD = (e) => !!e.metaKey;", "const sets = [];",
                                    "function sfRangeSet(key, h) { sets.push([key, h.from, h.to]); }"] + drawn)
                         + "\nconst data = " + json.dumps({"records": view["records"], "table": view["table"]}) + ";\n" + r"""
SF.table = data.table;
const rows = data.records;
const cols = [SF_ID, ...sfColumns(data.table)];
const g0 = sfGroups(rows, rows, cols, 'ta', [], {});
const by = (key) => g0.find((g) => g.key === key);
const bars = sfRangeBars(rows, g0, {}, 'ta');
const out = {};
const runs = sfTrack('participants', bars.participants);
out.runs = runs;
out.ratingTrack = sfTrack('rating', bars.rating);
out.oneBar = sfTrack('year', [{ from: 2012, to: 2014 }]);
out.read = [sfTrackRead('3-5 6-10 11-15'), sfTrackRead(''), sfTrackRead('7-9')];
out.at = [sfTrackAt(runs, 3, 'from'), sfTrackAt(runs, 6, 'from'), sfTrackAt(runs, 10, 'to'), sfTrackAt(runs, 12, 'from'),
  sfTrackAt(runs, 12, 'to'), sfTrackAt(runs, 640, 'to'), sfTrackAt(runs, 51, 'from')];
out.snap = [sfTrackSnap(runs, 2.4, 'from'), sfTrackSnap(runs, 2.6, 'from'), sfTrackSnap(runs, 0.2, 'to'), sfTrackSnap(runs, 99, 'from'),
  sfTrackSnap(runs, 99, 'to')];
out.edge = [sfTrackEdge(runs, 0, 'from'), sfTrackEdge(runs, 2, 'from'), sfTrackEdge(runs, 2, 'to'), sfTrackEdge(runs, runs.length, 'to'),
  sfTrackEdge(runs, 10, 'from')];
out.step = [sfTrackStep(runs, 2, 'from', 1), sfTrackStep(runs, 2.4, 'from', 1), sfTrackStep(runs, 2.4, 'from', -1),
  sfTrackStep(runs, 0, 'from', -1), sfTrackStep(runs, runs.length, 'to', 1)];
// the slider drawn with a filter from 12 to 50
SF.filters = { participants: { from: 12, to: 50, none: false } };
const ranged = sfRangeBars(rows, g0, SF.filters, 'ta');
out.countHtml = sfRangeHtml(by('participants'), tbFacetCounts(rows, g0, SF.filters, sfRead('ta')).participants, 2, ranged.participants);
SF.filters = {};
out.ratingHtml = sfRangeHtml(by('rating'), tbFacetCounts(rows, g0, {}, sfRead('ta')).rating, 3, bars.rating);
// a fake of the drawn group, its boxes, its handles and its slider, for sfRangeMove and the keys
const fakeGroup = (key, low, high, track, from, to) => {
  const g = { dataset: { g: key, low: String(low), high: String(high), runs: track }, props: {} };
  const input = (kind, end, value) => ({ type: kind === 'sf-handle' ? 'range' : 'number', kind, dataset: { end }, value: String(value),
    attrs: {}, setAttribute(k, v) { this.attrs[k] = v; }, closest: () => g,
    classList: { contains: (c) => c === kind } });
  const rd = sfTrackRead(track);
  g.handles = { from: input('sf-handle', 'from', rd ? sfTrackAt(rd, from, 'from') : from), to: input('sf-handle', 'to', rd ? sfTrackAt(rd, to, 'to') : to) };
  g.boxes = { from: input('sf-rnum', 'from', from), to: input('sf-rnum', 'to', to) };
  g.slider = { style: { setProperty: (k, v) => { g.props[k] = v; } } };
  g.count = { textContent: '' };
  g.querySelector = (sel) => {
    const m = sel.match(/^\.sf-rnum\[data-end="(from|to)"\]$/);
    if (m) return g.boxes[m[1]];
    if (sel === '.sf-slider') return g.slider;
    if (sel === '.sf-rvals .sf-cn') return g.count;
    return null;
  };
  g.querySelectorAll = (sel) => {
    const m = sel.match(/^\.sf-rnum\[data-end="(from|to)"\]$/);
    if (m) return [g.boxes[m[1]]];
    if (sel === '.sf-handle[data-end]') return [g.handles.from, g.handles.to];
    return [];
  };
  return g;
};
const track = runs.map(([a, b]) => `${a}-${b}`).join(' ');
const state = (g) => [String(g.boxes.from.value), String(g.boxes.to.value), String(g.handles.from.value), String(g.handles.to.value),
  g.handles.from.attrs['aria-valuetext'] || '', g.props['--lo'] ? Number(Number(g.props['--lo']).toFixed(4)) : null];
// dragged to 2.4 the lower handle goes to the edge of the bar it is nearest, 11
let g = fakeGroup('participants', 3, 640, track, 3, 640);
g.handles.from.value = '2.4';
sfRangeMove(g.handles.from, false);
out.drag = state(g);
// dragged past the lower, the upper stops at the end of the lower's bar
g.handles.to.value = '0.3';
sfRangeMove(g.handles.to, false);
out.cross = state(g);
// let go, the filter is set
sfRangeMove(g.handles.to, true);
out.set = sets.slice(-1)[0];
// a number typed between two edges stands its handle inside its bar
g = fakeGroup('participants', 3, 640, track, 3, 640);
g.boxes.from.value = '13';
sfRangeMove(g.boxes.from, false);
out.typed = state(g);
// the arrows move a bar, from inside a bar to its own edge first, and Home to the first edge
const key = (el, k) => { const e = { target: el, key: k, metaKey: false, altKey: false, prevented: false, preventDefault() { this.prevented = true; } };
  return [sfHandleKey(e), e.prevented, sets.slice(-1)[0]]; };
g.handles.from.value = String(sfTrackAt(runs, 13, 'from'));
out.right = key(g.handles.from, 'ArrowRight');
g.handles.from.value = String(sfTrackAt(runs, 13, 'from'));
out.left = key(g.handles.from, 'ArrowLeft');
out.home = key(g.handles.from, 'Home');
out.letter = key(g.handles.from, 'a');
// the rating keeps a star a step, and its handles the browser's own keys
const r = fakeGroup('rating', 0, 5, '', 0, 5);
r.handles.from.value = '3.6';
sfRangeMove(r.handles.from, false);
out.rating = state(r);
out.ratingKey = key(r.handles.from, 'ArrowRight');
// the pills
out.pills = [sfPillHtml('include'), sfPillHtml('exclude', ''), sfPillHtml('maybe'), sfPillHtml(''), sfPillHtml('include', '', 'ft'),
  sfPillHtml('exclude', '', 'ft')];
console.log(JSON.stringify(out));
""", encoding="utf-8")
        ran = subprocess.run([node, str(probe)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        why = (ran.stderr or ran.stdout)[:400]
        check("117: in node, the year's and the participants' tracks go by bars when they have two or more, the rating's "
              "and one bar alone a whole number a step, and a group's runs read back from its data-runs",
              out.get("runs") == [[3, 5], [6, 10], [11, 15], [16, 20], [21, 25], [26, 30], [31, 35], [36, 40], [41, 45], [46, 50],
                                  [51, 100], [101, 200], [201, 500], [501, 640]]
              and out.get("ratingTrack") is None and out.get("oneBar") is None
              and out.get("read") == [[[3, 5], [6, 10], [11, 15]], None, None], why or str(out.get("runs")))
        check("117: in node, a number's place on the track: a bar's first number at its left edge and its last at its right, "
              "a number between two edges inside its bar, past 50 by bar and not by number",
              out.get("at") == [0, 1, 2, 2.2, 2.4, 14, 10], str(out.get("at")))
        check("117: in node, a handle goes to the edge it is nearest, the lower never past the last bar's start nor the upper "
              "before the first bar's end, and each edge gives its bar's first or last number",
              out.get("snap") == [2, 3, 1, 13, 14] and out.get("edge") == [3, 11, 10, 640, 51], str(out.get("snap")) + str(out.get("edge")))
        check("117: in node, a step goes a bar on or back, from inside a bar to its own edge first, and stops at the ends",
              out.get("step") == [3, 3, 2, 0, 14], str(out.get("step")))
        count_html = out.get("countHtml", "")
        check("117: in node, the participants' slider drawn on its bars: its handles from 0 to the number of bars, any place "
              "on them, each at its number's place with the number said, the stretch between them by bar, its runs on the "
              "group, and its boxes still any whole number from the lowest to the highest",
              '<input type="range" class="sf-handle sf-from" data-end="from" min="0" max="14" step="any" value="2.2" '
              'aria-valuetext="12"' in count_html
              and '<input type="range" class="sf-handle sf-to" data-end="to" min="0" max="14" step="any" value="10" '
              'aria-valuetext="50"' in count_html and 'style="--lo: 0.1571; --hi: 0.7143"' in count_html
              and 'data-runs="3-5 6-10 11-15 16-20 21-25 26-30 31-35 36-40 41-45 46-50 51-100 101-200 201-500 501-640"' in count_html
              and '<input type="number" class="sf-rnum" data-end="from" min="3" max="640" step="1" value="12"' in count_html,
              count_html[:500])
        rating_html = out.get("ratingHtml", "")
        check("117, updated 12 October (121): in node, My rating's slider is one to five stars a whole star a step, with no "
              "runs",
              '<input type="range" class="sf-handle sf-from" data-end="from" min="1" max="5" step="1" value="1"' in rating_html
              and "data-runs" not in rating_html and 'style="--lo: 0; --hi: 1"' in rating_html, rating_html[:300])
        check("117: in node, a lower handle dragged to 2.4 goes to the edge at 2, 11, its box, its place, its number said and "
              "the stretch following, and an upper dragged past it stops at the end of its bar, 15, and when let go the "
              "filter is set",
              out.get("drag") == ["11", "640", "2", "14", "11", 0.1429] and out.get("cross") == ["11", "15", "2", "3", "11", 0.1429]
              and out.get("set") == ["participants", 11, 15], why or str([out.get("drag"), out.get("cross"), out.get("set")]))
        check("117: in node, a number typed between two edges, 13, stands its handle at its place inside its bar",
              out.get("typed") == ["13", "640", "2.4", "14", "13", 0.1714], str(out.get("typed")))
        check("117: in node, the arrows move a handle a bar, from 13 on to 16 and back to 11, Home to the first edge, and any "
              "other key is left to the screen",
              out.get("right") == [True, True, ["participants", 16, 640]] and out.get("left") == [True, True, ["participants", 11, 640]]
              and out.get("home") == [True, True, ["participants", 3, 640]] and (out.get("letter") or [None])[0] is False,
              str([out.get("right"), out.get("left"), out.get("home")]))
        check("117: in node, the rating's handle dragged to 3.6 stands at 4 stars, a whole star a step, and its keys are the "
              "browser's own",
              out.get("rating") == ["4", "5", "4", "5", "", 0.8] and (out.get("ratingKey") or [None])[0] is False, str(out.get("rating")))
        check("117, updated 12 October (126): in node, a decision reads Yes, No, Maybe or To screen at title and abstract, "
              "and Include or Exclude at full text",
              out.get("pills") == ['<span class="sf-pill" data-decision="include">Yes</span>',
                                   '<span class="sf-pill" data-decision="exclude">No</span>',
                                   '<span class="sf-pill" data-decision="maybe">Maybe</span>',
                                   '<span class="sf-pill" data-decision="">To screen</span>',
                                   '<span class="sf-pill" data-decision="include">Include</span>',
                                   '<span class="sf-pill" data-decision="exclude">Exclude</span>'], str(out.get("pills")))
    else:
        skip("117: the sliders bar by bar and the pills in node", "no node on this machine")
    check("117: the keys reach a handle on a track by bars ahead of the screen's own, and the handles' drag snaps as it "
          "moves and sets the filter as it is let go",
          "if (sfHandleKey(e)) return;" in fn(sjs, "sfKeyDown")
          and fn(sjs, "sfKeyDown").index("if (sfHandleKey(e)) return;") < fn(sjs, "sfKeyDown").index("const typing = ")
          and "if (el.type === 'range' && el.dataset.end) sfRangeMove(el, false);" in sjs
          and "if (e.target.dataset && e.target.dataset.end) { sfRangeMove(e.target, true); return; }" in sjs)

    # ── F. Search strategy in node: the run's line, Screening has begun, Today in Carry decisions from, the plan not
    # yet written and a block's Remove asking first
    if node:
        script = base / "sift-review-search.js"
        harness = r"""
const els = {};
const mk = (id) => ({ id, setAttribute(k, v) { (this.attrs = this.attrs || {})[k] = v; }, innerHTML: '', value: '', hidden: false, textContent: '', disabled: false, title: '', dataset: {},
  onclick: null, focus() {}, click() { return this.onclick ? this.onclick() : undefined; },
  querySelectorAll: () => [], querySelector: () => null, matches: () => false, closest: () => null });
const $ = (id) => els[id] || (els[id] = mk(id));
$('settings').hidden = true;
$('feedback').hidden = true;
$('sfs-ask').hidden = true;
$('sfs-mark-card').hidden = true;
async function api() { return {}; }
const say = () => {};
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;
const grow = () => {};
const needsRestart = () => false;
const RESTART_LINE = 'Restart the server to finish this update.';
const document = { activeElement: null, querySelectorAll: () => [], createElement: () => mk('made'), body: { insertBefore() {} } };
const window = { addEventListener() {}, scrollTo() {} };
const localStorage = { getItem: () => null, setItem() {} };
function siftOpen() {}
function sfLeave(then) { then(); }
async function loadLibrary() {}
"""
        body = grip_js() + "\n" + support.table_js() + "\n" + ssjs.rsplit("\nsfsBoot();", 1)[0]
        run = r"""
(async () => {
const out = {};
SFS.today = '2026-10-12';
SFS.review = { opens: '2026-10-12', folder: 'r', searches: true, screening: 'r/runs/2026-10-12' };
const run = (o) => Object.assign({ screening: true, version: 1, draft: false, missed: [], benchmark: 0, decided: 0, rows: [],
  records: 40, merged: 32 }, o);
// each run numbered in the order made, as the server sends it, and its Details opened, since 12 October, later (124)
const second = run({ date: '2026-10-12-2', day: '2026-10-12', n: 2, number: 3, label: 'Run 3, 12 October 2026', filled: 2, authors_filled: 1, decided: 1 });
const first = run({ date: '2026-10-12', day: '2026-10-12', n: 1, number: 2, label: 'Run 2, 12 October 2026', filled: 0, authors_filled: 0, decided: 4,
  begun: 'its screening log' });
const older = run({ date: '2026-10-01', day: '2026-10-01', n: 1, number: 1, label: 'Run 1, 1 October 2026', filled: 1, authors_filled: null, decided: 2 });
SFS.runs = [second, first, older];
['2026-10-12-2', '2026-10-12', '2026-10-01', '2026-09-01'].forEach((d) => SFS.open.add(`run:${d}`));
out.both = sfsRunRow(second);
out.none = sfsRunRow(first);
out.old = sfsRunRow(older);
out.authors = sfsRunRow(run({ date: '2026-09-01', day: '2026-09-01', n: 1, label: '1 September 2026', filled: 0, authors_filled: 3 }));
SFS.follows = null;
sfsDrawFollows(null);
out.follows = $('sfs-follows').innerHTML;
SFS.data = { current: null, versions: [], problems: [] };
sfsDrawVersion();
out.version = [$('sfs-state').textContent, $('sfs-mark').disabled];
// a block's Remove: one holding terms asks first, No keeps it and Remove takes it, an empty one goes at once
SFS.catalog = { sources: ['pubmed'], names: { pubmed: 'PubMed' }, keyless: ['pubmed'], apis: ['pubmed'],
  scopes: [['tak', 'Title, abstract and keywords']], types: [], platformed: [], platforms: [], sites: {}, platform_sites: {}, hosts: {} };
SFS.plan = { databases: [], others: {}, platforms: {}, blocks: [{ name: 'Gardens', terms: ['garden*', 'allotment*', ''], scope: 'tak', scopes: {} },
  { name: '', terms: [''], scope: 'tak', scopes: {} }, { name: '', terms: ['one'], scope: 'tak', scopes: {} }], years: {}, types: [],
  benchmark: [], benchmark_titles: {}, overrides: {} };
SFS.data = { block_problems: [[], [], []], strings: [], problems: [] };
const field = () => ({ value: '', oninput: null, onchange: null, onclick: null });
const fake = (i) => { const parts = { '.sfs-bproblems': { innerHTML: '', hidden: true }, '.sfs-bname': field(), '.sfs-bscope': field(),
  '.sfs-terms': field(), '.sfs-bremove': field() };
  return { dataset: { i: String(i) }, parts, querySelector: (sel) => parts[sel] || null, querySelectorAll: () => [] }; };
let blocksEls = [fake(0), fake(1), fake(2)];
$('sfs-blocks').querySelectorAll = () => blocksEls;
sfsDrawBlocks();
const names = () => SFS.plan.blocks.map((b) => b.name || b.terms.join('|'));
let asking = blocksEls[0].parts['.sfs-bremove'].onclick();
out.ask = [$('sfs-ask').hidden, $('sfs-ask-head').textContent, $('sfs-ask-line').textContent, $('sfs-ask-yes').textContent];
SFS.askDone(false);
await asking;
out.kept = names();
// the elements drawn after a removal are the blocks left, so each press is taken from the one drawn before
const gardens = blocksEls[0];
blocksEls = [fake(0), fake(1)];
asking = gardens.parts['.sfs-bremove'].onclick();
SFS.askDone(true);
await asking;
out.taken = names();
const empty = blocksEls[0];
blocksEls = [fake(0)];
const quiet = empty.parts['.sfs-bremove'].onclick();
out.quiet = [SFS.askDone === null, names()];
await quiet;
asking = blocksEls[0].parts['.sfs-bremove'].onclick();
out.one = $('sfs-ask-line').textContent;
SFS.askDone(false);
await asking;
clearTimeout(SFS.saveTimer);
console.log(JSON.stringify(out));
})();
"""
        script.write_text(harness + body + "\n" + run, encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60, env=dict(os.environ, TZ="UTC"))
        o = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        why = (ran.stderr or ran.stdout)[:400]
        check("117, updated 12 October (123): in node, a run's row gives its records found and after duplicates, and its "
              "Details what OpenAlex filled only when it filled any, abstracts and authors together, the authors alone, a "
              "run from before counting none of them, and nothing at all when it filled nothing",
              "<li>2 abstracts and the authors of 1 record filled from OpenAlex</li>" in o.get("both", "")
              # the counts in the table's cells since 12 October, later (124)
              and '<td class="sfs-num" data-label="Records found">40</td><td class="sfs-num" data-label="After duplicates">32</td>' in o.get("none", "")
              and "OpenAlex" not in o.get("none", "x")
              and "<li>1 abstract filled from OpenAlex</li>" in o.get("old", "")
              and "<li>The authors of 3 records filled from OpenAlex</li>" in o.get("authors", "")
              and "0 abstracts" not in json.dumps(o), why or o.get("both", "")[:300])
        check("117, updated 12 October (123): in node, a run whose screening has begun says nothing of it, no Screening has "
              "begun and no riddle of its screening log, the run Screening has open marked Active and another Make "
              "active (124)",
              "Screening has begun" not in json.dumps(o) and "screening log" not in o.get("none", "")
              and '<span class="sfs-tag sfs-open-tag">Active</span>' in o.get("none", "")
              and ">Make active</button>" in o.get("both", ""), o.get("none", "")[-200:])
        check("117, updated 12 October (123), and later (124): in node, Keep the decisions from names each run as the runs "
              "list does, by its number in the order made and its day, never Today",
              o.get("follows") == '<option value="2026-10-12-2">Run 3, 12 October</option><option value="2026-10-12">Run 2, 12 October</option>'
              '<option value="2026-10-01">Run 1, 1 October</option><option value="none">No earlier run</option>'
              and 'class="sfs-run-name">Run 3, 12 October</th>' in o.get("both", ""), str(o.get("follows")))
        check("117, updated 12 October (123): in node, a project with no plan yet reads Draft, with no version, and nothing "
              "to register",
              o.get("version") == ["Draft", True], str(o.get("version")))
        check("117: in node, Remove on a block holding terms asks first, naming the block and its terms, No keeping it and "
              "Remove taking it, one with no terms going at once, and one term said as one",
              o.get("ask") == [False, "Remove the block Gardens", "Its 2 terms go with it.", "Remove"]
              and o.get("kept") == ["Gardens", "", "one"] and o.get("taken") == ["", "one"]
              and o.get("quiet") == [True, ["one"]] and o.get("one") == "Its one term goes with it.", why or str(o))
    else:
        skip("117: Search strategy's runs, Carry decisions from and Remove in node", "no node on this machine")
