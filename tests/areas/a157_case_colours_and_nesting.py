from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import support
from .support import check, demo_copy, refusal_of, skip
import idiograph_routes


def test_case_colours_and_nesting(scratch):
    print("\n157. A colour for each participant on the GETs board, set from the Cases panel, with a badge of the "
          "participant's initial, and the Cases panel's statements nested under their PET and sub-theme, each level "
          "folding, 16 October, Adam's word on a tester's feedback. Since the test review of 18 October the palette, "
          "its contrasts, the badge's sizes and the panel's layout are review shots, and the colours saved and read back, "
          "the tree, the folds, the search and the clicks stay")
    import subprocess
    import gets as gets_mod
    import server as server_mod
    import themes as themes_mod

    read = lambda path: Path(path).read_text(encoding="utf-8")
    themes_js = support.text("apps/idiograph/static/themes.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: ("async " if f"async function {name}(" in src else "") + f"function {name}(" + fn(src, name) + "\n}"
    node = shutil.which("node")

    # ── A. an invented project: three allotment holders, every word of their workbooks the demo's invented ones
    base = scratch / "colours-157"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Allotment study"
    books = {name: demo_copy(root, name, f"{name} - EN & ES.xlsx") for name in ("Isla", "Ivo", "Tam")}
    cards = themes_mod.read_cards(books["Isla"])["cards"]
    keys = [c["key"] for c in cards]
    board = themes_mod.blank_version(cards)
    board.update(id="v1", name="Board 1", discarded=[keys[5]], groups=[
        {"id": "g1", "label": "Digging before work", "members": keys[0:2] + ["g3"], "x": 0, "y": 0},
        {"id": "g3", "label": "Frost on the beds", "members": [keys[2], "g5"], "x": 0, "y": 0},
        {"id": "g5", "label": "The first thaw", "members": [keys[3]], "x": 0, "y": 0},
        {"id": "g2", "label": "Sharing the shed", "members": [keys[4]], "x": 0, "y": 0}])
    themes_mod.write(books["Isla"], {"schema": 2, "case": "Isla", "workbook": books["Isla"].name, "current": "v1",
                                     "boards": [board]})
    other = themes_mod.blank_version(themes_mod.read_cards(books["Ivo"])["cards"])
    other.update(id="v1", name="Board 1", groups=[{"id": "g1", "label": "Watering at dusk", "members": keys[6:8], "x": 0, "y": 0}])
    themes_mod.write(books["Ivo"], {"schema": 2, "case": "Ivo", "workbook": books["Ivo"].name, "current": "v1", "boards": [other]})
    saved = (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_MEMORY = {"recent": []}
    any_book = str(books["Isla"])
    gfile = gets_mod.gets_path(root)
    try:
        shown = idiograph_routes.api_gets({"workbook": any_book})
        looks = {c["case"]: (c["colour"], c["default"], c["chosen"], c["badge"]) for c in shown["cases"]}
        check("157: each case takes its place in case order round the palette by default, its badge its initial, two "
              "letters where two cases share one, and opening writes nothing",
              [c["case"] for c in shown["cases"]] == ["Isla", "Ivo", "Tam"]
              and looks == {"Isla": (0, 0, False, "Is"), "Ivo": (1, 1, False, "Iv"), "Tam": (2, 2, False, "T")}
              and shown["colours"] == {} and not gfile.exists(), str(looks))
        answer = idiograph_routes.api_gets_cases({"workbook": any_book, "op": "colour", "case": "Tam", "colour": 6})
        on_disk = json.loads(gfile.read_text(encoding="utf-8"))
        again = idiograph_routes.api_gets({"workbook": any_book})
        tam = next(c for c in again["cases"] if c["case"] == "Tam")
        check("157: a colour set from a case's row is kept in the GETs file at once, by the case's label after the "
              "study, the first act taking every case in, and read back on the next open",
              on_disk.get("colours") == {"Tam": 6} and list(on_disk).index("colours") == list(on_disk).index("study") + 1
              and answer["op"] == "colour" and set(on_disk["cases"]) == {"Isla", "Ivo", "Tam"}
              and (tam["colour"], tam["default"], tam["chosen"], tam["badge"]) == (6, 2, True, "T")
              and again["colours"] == {"Tam": 6}, str(on_disk.get("colours")))
        body = dict(again["version"], cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in again["cards"]},
                    groups=[{"id": "G1", "label": "Early mornings", "members": ["Isla/g1", "Ivo/g1"], "x": 0, "y": -60}],
                    discarded=[], picks={}, notes=[])
        idiograph_routes.api_gets_save({"workbook": any_book, "version": body})
        listed = idiograph_routes.gets_books(root)
        gets_mod.settings_op(root, listed, {"study": {"Ivo": {"in": False, "reason": "a trial run"}}})
        kept = json.loads(gfile.read_text(encoding="utf-8"))
        gets_mod.settings_op(root, listed, {"study": {"Ivo": {"in": True}}})
        check("157: a board's save and Settings' save of the study keep the colours as they are",
              kept["colours"] == {"Tam": 6} and kept["study"]["Ivo"]["in"] is False and kept["boards"][0]["groups"][0]["id"] == "G1")
        before = gfile.read_bytes()
        said = [refusal_of(lambda c=c: idiograph_routes.api_gets_cases({"workbook": any_book, "op": "colour", "case": "Tam", "colour": c}))
                for c in (25, -1, "3", True, 2.0)]
        nobody = refusal_of(lambda: idiograph_routes.api_gets_cases({"workbook": any_book, "op": "colour", "case": "Nobody", "colour": 1}))
        check("157: a colour the palette does not hold, or a case the project does not have, is refused with nothing written",
              said == [gets_mod.NOT_A_COLOUR] * 5 and nobody == gets_mod.NOT_A_CASE and gfile.read_bytes() == before,
              str(said + [nobody]))
        idiograph_routes.api_gets_cases({"workbook": any_book, "op": "colour", "case": "Tam", "colour": None})
        cleared = json.loads(gfile.read_text(encoding="utf-8"))
        back = next(c for c in idiograph_routes.api_gets({"workbook": any_book})["cases"] if c["case"] == "Tam")
        check("157: Default takes his choice away, the file keeping no colours at all, the case back at its place in case order",
              "colours" not in cleared and (back["colour"], back["default"], back["chosen"]) == (2, 2, False))
        moved = idiograph_routes.relabel_all({"colours": {"Tam": 6, "Isla": 1}, "study": {"Tam": {"in": True}}}, "Tam", "Tor")
        check("157: Rename carries a case's colour to its new label, as it does every key naming the case",
              moved["colours"] == {"Tor": 6, "Isla": 1} and moved["study"] == {"Tor": {"in": True}})
        names = ("Ada", "Bo", "Cy", "Di", "Ed", "Flo", "Gus", "Hal", "Ivy", "Jo")
        many = gets_mod.looks([f"P{i} - {n}" for i, n in enumerate(names, 1)], None)
        check("157: past eight cases each takes the next of the 25, P9 Moss and P10 Spruce (21 October, More colours)",
              [many[f"P{i} - {n}"]["colour"] for i, n in enumerate(names, 1)] == list(range(10))
              and [many[f"P{i} - {n}"]["badge"] for i, n in enumerate(names, 1)] == [n[0] for n in names])
        pairs = gets_mod.badges([("a", "Jo"), ("b", "Jem"), ("c", "Jo"), ("d", "Kit")])
        check("157: two cases sharing an initial take two letters, and where those are shared too the initial and a number",
              pairs == {"a": "J1", "b": "Je", "c": "J2", "d": "K"}, str(pairs))
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = saved

    # ── C. in node: the looks, the cards, the tree, its folds kept, the search, the drag and the second click
    if not node:
        skip("157: the colours and the tree in node", "no node on this machine")
    else:
        stubs = r"""
const ELS = {};
const $ = (id) => ELS[id] || null;
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const SAID = [];
const say = (t) => SAID.push(t);
const STORE = {};
globalThis.localStorage = { getItem: (k) => (k in STORE ? STORE[k] : null), setItem: (k, v) => { STORE[k] = String(v); } };
"""
        scenario = r"""
class El {
  constructor() {
    this.cls = new Set();
    const self = this;
    this.classList = { add: (...n) => n.forEach((x) => self.cls.add(x)), remove: (n) => self.cls.delete(n),
      contains: (n) => self.cls.has(n), [Symbol.iterator]: () => self.cls[Symbol.iterator]() };
    this.innerHTML = '';
    this.title = '';
    this.scrollTop = 0;
  }
}
ELS['gt-cases'] = new El();
const line = (row, at, text, pet, extra) => Object.assign({ sheet: 'Initial', row, time: '00:10', text, quotes: [], notes: [], pet, discarded: false }, extra || {});
const lines = { 'Initial:3:0': line(3, 0, 'Digging in the dark', 'g1'), 'Initial:3:1': line(3, 1, 'A spade by the gate', 'g1'),
  'Initial:5:0': line(5, 0, 'White over the leeks', 'g3'),
  'Initial:5:1': line(5, 1, 'Thaw on the third day', 'g5', { quotes: ['"the ground gives a little"'] }),
  'Initial:7:0': line(7, 0, 'Two keys to the shed', 'g2'), 'Initial:9:0': line(9, 0, 'Rain on the roof', null),
  'Initial:9:1': line(9, 1, 'Lost the trowel', null, { discarded: true }) };
const pets = [{ id: 'g1', title: 'Digging before work', note: '', parent: null, subs: ['g3'], statements: ['Initial:3:0', 'Initial:3:1'] },
  { id: 'g3', title: 'Frost on the beds', note: '', parent: 'g1', subs: ['g5'], statements: ['Initial:5:0'] },
  { id: 'g5', title: 'The first thaw', note: '', parent: 'g3', subs: [], statements: ['Initial:5:1'] },
  { id: 'g2', title: 'Sharing the shed', note: '', parent: null, subs: [], statements: ['Initial:7:0'] }];
TH.mode = 'gets';
TH.live = true;
TH.root = 'Allotment study';
TH.sheets = ['Initial'];
TH.gets = { cases: [
  { case: 'Isla', who: 'Isla', in: true, complete: true, pets, lines, colour: 0, default: 0, chosen: false, badge: 'Is' },
  { case: 'Ivo', who: 'Ivo', in: true, complete: true, pets: [], lines: {}, colour: 5, default: 1, chosen: true, badge: 'Iv' },
  { case: 'Tam', who: 'Tam', in: true, none: true, pets: [], lines: { 'Initial:3:0': line(3, 0, 'Beans up the canes', null) } }],
  minimum: 2, total: 3, study: {}, settings: {} };
const card = (key, kind, kase, text) => ({ key, kind, case: kase, who: kase, text, x: 0, y: 0, time: '', sheet: 'Initial' });
TH.v = { cards: { 'Isla/g1': card('Isla/g1', 'pet', 'Isla', 'Digging before work'),
  'Isla/es/Initial:9:0': card('Isla/es/Initial:9:0', 'es', 'Isla', 'Rain on the roof'),
  'Ivo/pn/1': card('Ivo/pn/1', 'pn', 'Ivo', 'An invented note'), 'Tam/es/Initial:3:0': card('Tam/es/Initial:3:0', 'es', 'Tam', 'Beans up the canes') },
  groups: [], discarded: [], picks: {}, stickies: [], ai: { discarded: {} } };
const out = {};
out.looks = ['Isla', 'Ivo', 'Tam', 'P7 - Gone'].map((n) => { const l = gtLook(n); return [l.colour, l.default, l.chosen, l.badge]; });
const tree = gtTree(TH.gets.cases[0]);
out.tree = { tops: tree.tops.map((t) => [t.p.id, t.own, t.subs.map((s) => [s.p.id, s.lines])]), none: tree.none };
TH.els = { cards: Object.fromEntries(Object.keys(TH.v.cards).map((k) => [k, new El()])), frames: {}, labels: {} };
const dressed = () => Object.fromEntries(Object.entries(TH.els.cards).map(([k, el]) => {
  const m = /class="gt-badge case-(\d)" aria-hidden="true">([^<]*)<\/span>/.exec(el.innerHTML);
  return [k, [[...el.cls].filter((c) => c.startsWith('case-')).join(' '), m ? Number(m[1]) : null, m ? m[2] : null]];
}));
gtDress(TH.v);
out.cards = dressed();
TH.gets.cases[1].colour = 3;
gtDress(TH.v);
out.recoloured = dressed()['Ivo/pn/1'];
// the panel: every case shut, then each level folded open in turn
const seq = () => [...ELS['gt-cases'].innerHTML.matchAll(/data-gkind="(\w+)" data-gid="([^"]+)"|class="gt-none/g)]
  .map((m) => (m[1] ? `${m[1]}:${m[2]}` : 'none'));
TH.casesOpen = true;
TH.cfind = '';
gtFoldsRead();
gtCasesDraw();
out.shut = seq();
out.swatches = [...ELS['gt-cases'].innerHTML.matchAll(/class="gt-swatch case-(\d)"[^>]*aria-label="([^"]*)">([^<]*)</g)].map((m) => [Number(m[1]), m[2], m[3]]);
gtFold('Isla');
out.caseOpen = seq();
gtFold('Isla/g1');
out.petOpen = seq();
gtFold('Isla/g3');
gtFold('Isla/:none');
out.allOpen = seq();
const html = ELS['gt-cases'].innerHTML;
out.counts = [...html.matchAll(/class="gt-rn">(\d+)</g)].map((m) => Number(m[1]));
// a statement on no PET says "not placed", the word the bar and the manual use, its class kept (17 October)
out.where = [['placed', 'placed'], ['unplaced', 'not placed'], ['discarded', 'set aside']]
  .map(([k, w]) => html.includes(`gt-where ${k}">${w}`)).concat([!html.includes('">unplaced<')]);
out.kept = JSON.parse(STORE['idiograph-gets-folds'] || '{}');
TH.cfold = new Set();
TH.foldRoot = null;
TH.root = 'Another study';
gtFoldsRead();
out.otherFolds = [...TH.cfold];
TH.root = 'Allotment study';
gtFoldsRead();
out.readBack = [...TH.cfold].sort();
gtFold('Isla/g1');
out.petShut = seq();
gtFold('Isla/g1');
// the search: everything shut, then a quote found deep in a sub-theme's group
const kept = STORE['idiograph-gets-folds'];
TH.cfold = new Set();
TH.cfind = 'ground gives';
TH.cflip.clear();
gtCasesDraw();
out.found = seq();
gtFold('Isla/g3');
out.flipped = [seq(), [...TH.cflip], STORE['idiograph-gets-folds'] === kept];
TH.cflip.clear();
TH.cfind = 'sharing';
gtCasesDraw();
out.title = seq();
TH.cfind = 'frost';
gtCasesDraw();
out.sub = seq();
TH.cfind = 'tam';
gtCasesDraw();
out.name = seq();
TH.cfind = '';
// the drag: a row at any level makes its card
const entry = TH.gets.cases[0];
out.made = [gtCardFrom(entry, 'pet', 'g1'), gtCardFrom(entry, 'sub', 'g3'), gtCardFrom(entry, 'es', 'Initial:5:1')]
  .map((c) => [c.key, c.kind, c.statements === undefined ? null : c.statements]);
const press = (gkind, gid) => ({ target: { closest: (s) => (s === '.gt-row' ? { dataset: { gi: '0', gkind, gid } } : null) },
  button: 0, clientX: 10, clientY: 10, preventDefault: () => {} });
out.pulls = [['sub', 'g3'], ['es', 'Initial:5:1']].map(([k, id]) => { TH.pull = null; gtPullDown(press(k, id)); const p = TH.pull; return [p.i, p.kind, p.ident]; });
TH.pull = null;
// a second click on a statement's row opens its passage, on a PET's row it shows its card again
const calls = [];
thToPassage = (key) => calls.push(['passage', key]);
gtRowShow = (p) => calls.push(['show', p.ident]);
gtRowClick({ i: 0, kind: 'es', ident: 'Initial:5:1' });
gtRowClick({ i: 0, kind: 'es', ident: 'Initial:5:1' });
gtRowClick({ i: 0, kind: 'pet', ident: 'g1' });
gtRowClick({ i: 0, kind: 'pet', ident: 'g1' });
out.clicks = calls;
console.log(JSON.stringify(out));
"""
        script = scratch / "colours-157.js"
        script.write_text(support.i18n_js() + stubs + themes_js + scenario, encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("157: the colours and the tree run in node", False, run.stderr.strip()[:400])
        else:
            o = json.loads(run.stdout)
            check("157: in node, each case's look is the server's, and a server from before the colours gives the case its "
                  "place in case order and its initial",
                  o["looks"] == [[0, 0, False, "Is"], [5, 1, True, "Iv"], [2, 2, False, "T"], [0, 0, False, "G"]], str(o["looks"]))
            check("157: in node, every card of a case, a PET, a statement and a participant note, carries its case's colour "
                  "and its badge, and a colour changed leaves no old one on the card",
                  o["cards"] == {"Isla/g1": ["case-0", 0, "Is"], "Isla/es/Initial:9:0": ["case-0", 0, "Is"],
                                 "Ivo/pn/1": ["case-5", 5, "Iv"], "Tam/es/Initial:3:0": ["case-2", 2, "T"]}
                  and o["recoloured"] == ["case-3", 3, "Iv"], str([o["cards"], o["recoloured"]]))
            check("157: in node, a case's tree holds each PET's own statements, then its sub-themes with every statement "
                  "at any depth in them, and every statement in none last, unplaced and discarded",
                  o["tree"] == {"tops": [["g1", ["Initial:3:0", "Initial:3:1"], [["g3", ["Initial:5:0", "Initial:5:1"]]]],
                                         ["g2", ["Initial:7:0"], []]], "none": ["Initial:9:0", "Initial:9:1"]}, str(o["tree"]))
            check("157: in node, every case starts shut with its swatch, its badge in its colour and named for a screen "
                  "reader, and each level folds open on its own, statements under their PET and sub-theme and Not in a PET last",
                  o["shut"] == [] and o["swatches"] == [[0, "Isla's colour, Blue", "Is"], [3, "Ivo's colour, Brown", "Iv"],
                                                         [2, "Tam's colour, Plum", "T"]]
                  and o["caseOpen"] == ["pet:g1", "pet:g2", "none"]
                  and o["petOpen"] == ["pet:g1", "es:Initial:3:0", "es:Initial:3:1", "sub:g3", "pet:g2", "none"]
                  and o["allOpen"] == ["pet:g1", "es:Initial:3:0", "es:Initial:3:1", "sub:g3", "es:Initial:5:0",
                                       "es:Initial:5:1", "pet:g2", "none", "es:Initial:9:0", "es:Initial:9:1"]
                  and o["counts"] == [4, 2, 1, 2] and o["where"] == [True, True, True, True],
                  str([o["caseOpen"], o["petOpen"], o["allOpen"], o["where"]]))
            check("157: in node, the folds are kept in the browser by project, read back after a reload, another project's "
                  "its own, and a PET folded shut hides its rows and keeps its sub-theme's fold",
                  sorted(o["kept"].get("Allotment study", [])) == ["Isla", "Isla/:none", "Isla/g1", "Isla/g3"]
                  and o["otherFolds"] == [] and o["readBack"] == ["Isla", "Isla/:none", "Isla/g1", "Isla/g3"]
                  and o["petShut"] == ["pet:g1", "pet:g2", "none", "es:Initial:9:0", "es:Initial:9:1"], str(o["kept"]))
            check("157: in node, a search shows what it finds with the rows that hold it, opening them, a chevron during it "
                  "turning a row the other way without touching the kept folds, a PET's title showing that PET and a "
                  "case's name all of the case",
                  o["found"] == ["pet:g1", "sub:g3", "es:Initial:5:1"]
                  and o["flipped"] == [["pet:g1", "sub:g3"], ["Isla/g3"], True]
                  and o["title"] == ["pet:g2"] and o["sub"] == ["pet:g1", "sub:g3"] and o["name"] == ["none"],
                  str([o["found"], o["flipped"], o["title"], o["sub"], o["name"]]))
            check("157: in node, a row at every level drags as its card, a PET, a sub-theme and a statement in a sub-theme's "
                  "own group",
                  o["made"] == [["Isla/g1", "pet", 4], ["Isla/g3", "sub", 2], ["Isla/es/Initial:5:1", "es", None]]
                  and o["pulls"] == [[0, "sub", "g3"], [0, "es", "Initial:5:1"]], str([o["made"], o["pulls"]]))
            check("157: in node, a second click on a statement's row soon after the first opens its passage by its key, "
                  "and on a PET's row shows its card again",
                  o["clicks"] == [["show", "Initial:5:1"], ["passage", "Isla/es/Initial:5:1"], ["show", "g1"], ["show", "g1"]],
                  str(o["clicks"]))
        harness = r"""
const TH = { mode: 'gets', live: true, busy: false, dirty: false, path: 'allot/Isla/Isla - EN & ES.xlsx', label: '',
  back: 'HOME', to: 'cases', meta: { id: 'b2' }, view: { x: 5, y: 6, z: 0.7 }, lastPick: null,
  sel: { cards: new Set(), groups: new Set(), stickies: new Set() }, v: { cards: {}, groups: [], discarded: [] }, ask: 0, viewing: null };
const SAID = [];
const CALLS = [];
const say = (t) => SAID.push(t);
const $ = (id) => ({ hidden: false, textContent: '', style: {} });
const noop = () => {};
const thTitleDone = noop, thNoteDone = noop, thVmenu = noop, thViewEnd = noop, thPile = noop, thXmenu = noop,
  thCasemenu = noop, thSideShut = noop, thAiCard = noop, thExported = noop, thMade = noop, thMenuClose = noop;
const thFlush = async () => {};
const CASES = [{ case: 'Isla', path: 'allot/Isla/Isla - EN & ES.xlsx' }];
const gtCase = (name) => CASES.find((c) => c.case === name) || null;
let OPENED = null;
const openPassage = (book, at, how) => { OPENED = { book, at, to: how.to }; how.leave(); how.back(); return true; };
const navGo = (again, open) => open();
const getsOpen = (path, opts) => CALLS.push(['gets', path, opts.board, opts.restore.mode, opts.restore.view.z]);
const themesOpen = (path) => CALLS.push(['pets', path]);
"""
        pieces = [harness, "const TH_NO_PASSAGE = 'none';"] + [whole(themes_js, n) for n in ("gtSplit", "thIsStatement", "thLineOf", "thToPassage")]
        way = r"""
(async () => {
  await thToPassage('Isla/g1');
  const pet = OPENED;
  await thToPassage('Isla/es/Initial:5:1');
  console.log(JSON.stringify({ pet, opened: OPENED, live: TH.live, calls: CALLS }));
})().catch((err) => { console.error(String(err && err.stack || err)); process.exit(1); });
"""
        if node:
            script = scratch / "colours-157-passage.js"
            script.write_text(support.i18n_js() + "\n".join(pieces + [way]), encoding="utf-8")
            run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
            if run.returncode != 0:
                check("157: a statement row's passage runs in node", False, run.stderr.strip()[:300])
            else:
                o = json.loads(run.stdout)
                check("157: in node, a statement's row opens its passage in its case's workbook though its card is not on the "
                      "board, a PET's row none, and the way back reopens the GETs board it left with its view",
                      o["pet"] is None and o["opened"] == {"book": "allot/Isla/Isla - EN & ES.xlsx",
                                                           "at": {"sheet": "Initial", "row": 5, "line": 1}, "to": "gets"}
                      and o["live"] is False and o["calls"] == [["gets", "allot/Isla/Isla - EN & ES.xlsx", "b2", "gets", 0.7]],
                      str(o))

