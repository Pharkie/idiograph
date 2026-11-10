"""Area 205: key quotes on cards, and Arrange by participant on GETs (Adam, 19 October 2026, from a tester's
reflection on IPA in ATLAS.ti, way A and way 2 of the drawings).

Quotes on cards is a button among the status bar's view tools, off on a new install and kept in the
settings: on, each statement card on the PETs and GETs boards shows its own key quote under its statement,
and a click on the quote shows it whole beside the card with Show in passage, which opens the card's passage
as its double-click does. The taller cards get room as a stack shown open gets it, a view the file never
keeps. Arrange by participant, on the GETs board, sets every PET and sub-theme card in no GET out in a row
for its participant, below the GETs, which stay where they are, one step of undo, and the command line and
the MCP server do the same as `{"op": "arrange", "by": "participant"}`, with a dry run.

The checks hold behaviour: the setting kept across a restart, the button's save, the quote's click opening
the passage, the room made and given back, a card let go below a quote staying where it was let go, the
rows and what they leave alone, undo, and the API's op and its dry run. Words, colour and layout go to Adam
as review shots. The node fixtures are invented, about learning to swim as an adult, and the command line's
is the demo, Living with a dog.
"""
from __future__ import annotations

import json
import shutil
import subprocess

from . import support
from .support import check, skip


def test_card_quotes_and_by_participant(scratch):
    print("\n205. Quotes on cards from the status bar, a click showing a quote whole with Show in passage, and "
          "Arrange by participant on GETs, in the app and through the API (Adam, 19 October)")
    import server as server_mod

    # ── the setting: off on a new install, kept across a restart
    cfg = scratch / "quotes-config.json"
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Adam"}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, None
        server_mod.STATE_MEMORY = {"recent": []}
        fresh = server_mod.merge_config({})
        server_mod.api_settings({"card_quotes": True})
        saved = json.loads(cfg.read_text(encoding="utf-8"))
        restarted = server_mod.merge_config(saved)
        server_mod.api_settings({"card_quotes": False})
        off = server_mod.merge_config(json.loads(cfg.read_text(encoding="utf-8")))
        odd = server_mod.merge_config({"card_quotes": "yes"})
        check("205: Quotes on cards is off on a new install, turned on is kept in the settings file beside the "
              "interviewer and read back on after a restart, turned off read back off, and anything but true reads as off",
              fresh["card_quotes"] is False and saved.get("card_quotes") is True and saved.get("interviewer") == "Adam"
              and restarted["card_quotes"] is True and off["card_quotes"] is False and odd["card_quotes"] is False,
              str({"fresh": fresh.get("card_quotes"), "saved": saved.get("card_quotes"), "off": off.get("card_quotes")}))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    by_participant_api(scratch)

    # ── in node: the button, the quote's click, the room, the rows and undo
    node = shutil.which("node")
    if not node:
        skip("205: the quotes and the rows in node", "node is not installed")
        return
    js = support.text("apps/idiograph/static/themes.js")
    script = scratch / "card-quotes-205.js"
    script.write_text(support.i18n_js() + STUBS + js + SCENARIO, encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=120)
    if run.returncode != 0:
        check("205: the quotes and the rows run in node", False, run.stderr.strip()[:800])
        return
    o = support.plain(json.loads(run.stdout))
    check("205: in node, the status bar's button turns the quotes on, saved at once as card_quotes, the button "
          "pressed in, then whole (area 304), and again off",
          o["toggle"] == {"saved": [{"card_quotes_full": False, "card_quotes": True}, {"card_quotes_full": True, "card_quotes": True},
                                    {"card_quotes_full": False, "card_quotes": False}],
                          "pressed": ["true", "true", "false"]}, str(o["toggle"]))
    check("205: in node, on a PETs card the quote shows under the statement, its inverted commas the card's own, a card "
          "with no key quote and the quotes off show none, and on GETs a statement card shows its case's copy's quote",
          o["html"]["pets"] and o["html"]["none"] == "" and o["html"]["off"] == "" and o["html"]["gets"]
          and o["html"]["pieces"], str(o["html"]))
    check("205: in node, a click on a card's quote selects the card and shows the quote whole beside it, and Show in "
          "passage opens that card's passage, the quote put away",
          o["click"] == {"open": "Initial:12:0", "selected": ["Initial:12:0"], "whole": True, "passage": ["Initial:12:0"],
                         "after": None, "hidden": True}, str(o["click"]))
    check("205: in node, a quote's room pushes down what stands below its card in its column, nothing overlaps, and "
          "the quotes off again put it all back where it stood",
          o["room"]["on"] == {"c": 190, "d": 140} and o["room"]["clashes"] == 0 and o["room"]["off"] == {"c": 140, "d": 140},
          str(o["room"]))
    check("205: in node, a card let go below a quote's card stays where it was let go, and the file keeps it where it "
          "stands with the quotes off",
          o["room"]["dropped"] == {"shown": 300, "kept": 250}, str(o["room"]))
    check("205: in node, Arrange by participant leaves a GET and its cards where they are, puts each case's PETs in a "
          "row of its own in the Cases panel's order below it, each PET then its own sub-themes, a sub-theme whose "
          "PET is in the GET at its row's end, a PET further off, "
          "a statement card in no GET where it was, nothing overlapping",
          o["rows"]["kept"] and o["rows"]["order"] == [["Petra/g1", "Petra/g2", "Petra/g4"], ["Ivo/g1", "Ivo/g2", "Ivo/g3"]]
          and o["rows"]["oneRow"] and o["rows"]["below"] and o["rows"]["gap"] == [14, 28] and o["rows"]["es"]
          and o["rows"]["clashes"] == 0, str(o["rows"]))
    check("205: in node, Arrange by participant is one step of undo, which puts every card back, and with every PET in "
          "a GET it moves nothing",
          o["undo"] == {"steps": 1, "back": True, "none": []}, str(o["undo"]))


def by_participant_api(scratch):
    """The API's op: the command line's gets apply, its dry run, a refused way, and the MCP server's tool."""
    import cli
    import gets as gets_mod
    import mcp_server
    import server as server_mod
    import themes

    pristine = support.DEMO_PRISTINE
    root = scratch / "by-participant-root"
    shutil.rmtree(root, ignore_errors=True)
    names = ("Juno", "Rowan", "Mabel")
    for name in names:
        case = root / name
        (case / "Working").mkdir(parents=True)
        shutil.copy2(pristine / f"{name} - EN & ES.xlsx", case / f"{name} - EN & ES.xlsx")
        for side in (pristine / "Working").glob(f"{name} - *"):
            shutil.copy2(side, case / "Working" / side.name)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Dogs, a scratch project", "agents": {"allowed": True, "at": "2026-10-19T10:00:00+01:00"}}), encoding="utf-8")
    config_file = scratch / "by-participant-config.json"
    config_file.write_text(json.dumps({"root": str(root), "interviewer": "Adam"}), encoding="utf-8")
    books = [{"case": n, "workbook": str(root / n / f"{n} - EN & ES.xlsx")} for n in names]
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        def answer(*args):
            code, out, err = cli.run(["--root", str(root), "--config", str(config_file), *args, "--json"])
            return code, (support.plain(json.loads(out)) if out.strip() else {}), err

        def ops(*operations) -> str:
            path = scratch / "by-participant-ops.json"
            path.write_text(json.dumps({"operations": list(operations)}), encoding="utf-8")
            return str(path)

        data, cases, _, _ = gets_mod.assemble(root, books, themes.now_iso())
        gets_mod.write(root, gets_mod._file(data, themes.now_iso()))
        order = [e["case"] for e in cases]
        keys = list(data["boards"][0]["cards"])
        rowan = [k for k in keys if k.startswith("Rowan/")]
        mabel = [k for k in keys if k.startswith("Mabel/")]
        answer("gets", "apply", "b1", "--ops", ops({"op": "make", "ref": "a", "title": "Walks at the edges of the day",
                                                    "inside": None, "members": [rowan[0], mabel[0]]}), "--note", "One GET")
        before = gets_mod.load(root)["boards"][0]
        held = {k: (before["cards"][k]["x"], before["cards"][k]["y"]) for k in (rowan[0], mabel[0])}
        raw = gets_mod.gets_path(root).read_bytes()
        code, dry, err = answer("gets", "apply", "b1", "--ops", ops({"op": "arrange", "by": "participant"}),
                                "--note", "Rows by participant", "--dry-run")
        dry_kept = gets_mod.gets_path(root).read_bytes() == raw
        code2, done, err2 = answer("gets", "apply", "b1", "--ops", ops({"op": "arrange", "by": "participant"}),
                                   "--note", "Rows by participant", "--tool", "Claude Code")
        after = gets_mod.load(root)["boards"][0]
        moved = done.get("arranged") or []
        rows = {}
        for k in moved:
            rows.setdefault(gets_mod.split_key(k)["case"], set()).add(after["cards"][k]["y"])
        drawn = themes.layout_boxes(themes.normalise(after), gets_mod.card_height)
        get_id = after["groups"][0]["id"]
        frame = drawn["frames"][get_id]
        ys = [min(ys_) for ys_ in rows.values()]
        check("205: gets apply arranges by participant: its dry run writes nothing and names the same cards, and then "
              "the cards in a GET stay where they were, each case's PETs and sub-themes in no GET a row of its own "
              "in the Cases panel's order, below the GET, one step in History",
              code == 0 and dry_kept and dry.get("arranged") == moved and code2 == 0 and moved
              and all(len(v) == 1 for v in rows.values())
              and [c for c in order if c in rows] == sorted(rows, key=lambda c: min(rows[c]))
              and all(y >= frame[1] + frame[3] for y in ys)
              and all((after["cards"][k]["x"], after["cards"][k]["y"]) == xy for k, xy in held.items())
              and len(after.get("history") or []) == 2 and rowan[0] not in moved,
              (err or err2 or json.dumps(done))[:300])
        # each row read left to right: PET by PET, each followed by its own sub-themes, and only after every
        # such PET the sub-themes whose PET stays in the GET (the demo's first PETs of Rowan and Mabel)
        recs = gets_mod.load(root)["cases"]
        bad, orphans = [], 0
        for kase in rows:
            parent = {p["id"]: p.get("parent") for p in recs[kase]["pets"]}
            seq = sorted((k for k in moved if gets_mod.split_key(k)["case"] == kase), key=lambda k: after["cards"][k]["x"])
            head, tail = None, False
            for k in seq:
                ident = gets_mod.split_key(k)["ident"]
                up = parent.get(ident)
                if up is None:
                    head = ident
                    if tail:
                        bad.append(k)
                elif up != head:
                    tail = True
                    orphans += 1
                    if f"{kase}/{up}" in moved:
                        bad.append(k)
            if seq and parent.get(gets_mod.split_key(seq[0])["ident"]) is not None:
                bad.append(seq[0])
        check("205: each participant's row reads PET by PET, each PET followed by its own sub-themes, and a sub-theme "
              "whose PET stays in a GET comes at the row's end, never first",
              not bad and orphans >= 1, str({"bad": bad, "orphans": orphans}))
        code, again, _ = answer("gets", "apply", "b1", "--ops", ops({"op": "arrange", "by": "participant"}),
                                "--note", "Again")
        code2, wrong, err = answer("gets", "apply", "b1", "--ops", ops({"op": "arrange", "by": "theme"}), "--note", "Odd")
        check("205: a second arrange changes nothing and writes nothing, and one by anything but participant is "
              "refused with nothing written",
              code == 0 and again.get("changed") is False and code2 != 0
              and len(gets_mod.load(root)["boards"][0].get("history") or []) == 2, err[:200])

        srv = mcp_server.Server(str(root), config=str(config_file))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))
        res = srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
            "name": "gets_apply", "arguments": {"board": "b1", "operations": [{"op": "arrange", "by": "participant"}],
                                                "request": "Rows", "dry_run": True}}}))["result"]
        check("205: through MCP gets_apply takes the same arrange, with a dry run",
              not res["isError"] and support.plain(res["structuredContent"]).get("changed") is False, json.dumps(res)[:300])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept


STUBS = r"""
// just enough page for the quotes and the rows: elements that keep what is written to them
const ELS = {};
class El {
  constructor(id) {
    this.id = id; this.cls = new Set(); this.attrs = {}; this.hidden = false; this.innerHTML = ''; this.title = '';
    this.dataset = {}; this.offsetWidth = 340; this.offsetHeight = 180;
    const self = this;
    this.style = { setProperty: () => {} };
    this.classList = { add: (...n) => n.forEach((x) => self.cls.add(x)), remove: (...n) => n.forEach((x) => self.cls.delete(x)),
      contains: (n) => self.cls.has(n),
      toggle: (n, on) => { if (on === undefined) on = !self.cls.has(n); if (on) self.cls.add(n); else self.cls.delete(n); return on; } };
  }
  get textContent() { return String(this.innerHTML).replace(/<[^>]*>/g, ''); }
  set textContent(v) { this.innerHTML = String(v); }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return this.attrs[k]; }
  getBoundingClientRect() { return { left: 100, top: 120, right: 300, bottom: 260, width: 200, height: 140 }; }
  querySelector() { return null; }
  querySelectorAll() { return []; }
  releasePointerCapture() {}
}
const $ = (id) => ELS[id] || null;
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const say = () => {};
const SAVED = [];
const api = async (path, body) => { SAVED.push(body); return { config: Object.assign({}, body) }; };
const needsRestart = () => false;
const RESTART_LINE = 'Restart';
const PLAY_GLYPH = '>';
const PAUSE_GLYPH = '||';
const MAC = true;
const MOD = (e) => e.metaKey;
globalThis.localStorage = { getItem: () => null, setItem: () => {} };
globalThis.window = { innerWidth: 1280, innerHeight: 800, matchMedia: () => ({ matches: false }) };
globalThis.requestAnimationFrame = () => 0;
globalThis.cancelAnimationFrame = () => {};
globalThis.setTimeout = () => 0;
globalThis.clearTimeout = () => {};
globalThis.document = { elementFromPoint: () => null, querySelectorAll: () => [] };
"""

SCENARIO = r"""
(async () => {
const out = {};
for (const id of ['th-quotes-btn', 'th-kqpop', 'th-stage', 'th-status-counts']) ELS[id] = new El(id);
thPlayerDraw = () => {};
thPanelFollow = () => {};
thDrawSel = () => {};
thRender = () => {};
thEase = () => {};
thSoon = () => {};
thMomentum = () => {};
thVmenu = () => {};
thCorners = () => {};
thMapPlace = () => {};
const passaged = [];
thToPassage = (key) => { passaged.push(key); };

// ── the button
TH.live = true;
TH.config = { card_quotes: false };
const pressed = [];
// since 30 October the button takes the next of Off, Short and Full (area 304)
for (let i = 0; i < 3; i += 1) { thQuotesToggle(); pressed.push(ELS['th-quotes-btn'].attrs['aria-pressed']); await Promise.resolve(); }
out.toggle = { saved: SAVED.slice(), pressed };

// ── the quote on a card, PETs and GETs
TH.mode = 'pets';
const card = (text, x, y) => ({ x, y, text, time: '4:12', sheet: 'Initial' });
const v = { cards: { 'Initial:12:0': card('Freezing at the edge of the pool', 0, 0), 'Initial:13:0': card('A childhood lesson', 210, 0),
                     'Initial:14:0': card('Counting lengths', 0, 120) },
            groups: [], discarded: [], stacks: {} };
TH.quotes = { 'Initial:12': { time: '4:12', seconds: 252, quotes: [{ key: 'Initial:12:0', text: '"my legs just would not go"' }] },
              'Initial:14': { time: '18:05', seconds: 1085, quotes: [{ key: 'Initial:14:0', text: 'I count, one, two, three … if I lose count that is when it gets me' }] } };
TH.config = { card_quotes: true };
const html = thKqHtml(v, 'Initial:12:0');
out.html = { pets: html.includes('‘my legs just would not go’') && !html.includes('"my'),
             none: thKqHtml(v, 'Initial:13:0'),
             pieces: thKqHtml(v, 'Initial:14:0').includes('three … if I lose'),
             off: (() => { TH.config = { card_quotes: false }; const h = thKqHtml(v, 'Initial:12:0'); TH.config = { card_quotes: true }; return h; })() };
TH.mode = 'gets';
TH.gets = { cases: [{ case: 'Ivo', lines: { 'Initial:5:0': { sheet: 'Initial', row: 5, time: '7:41', quotes: ['‘it was like the air had been punched out of me’'] } } }] };
const gv = { cards: { 'Ivo/es/Initial:5:0': { x: 0, y: 0, kind: 'es', case: 'Ivo', text: 'The first breath under water' } }, groups: [], discarded: [] };
out.html.gets = thKqHtml(gv, 'Ivo/es/Initial:5:0').includes('‘it was like the air had been punched out of me’');

// ── a click on the quote, then Show in passage
TH.mode = 'pets';
TH.v = v;
TH.els = { cards: { 'Initial:12:0': new El('c') }, under: {}, labels: {}, frames: {}, stickies: {}, rails: {} };
TH.press = { item: { kind: 'card', id: 'Initial:12:0' }, x0: 0, y0: 0, add: false, alt: false, kq: true };
thPointerUp({ pointerId: 1, clientX: 0, clientY: 0 });
const pop = ELS['th-kqpop'];
out.click = { open: TH.kqpop, selected: [...TH.sel.cards], whole: !pop.hidden && pop.innerHTML.includes('Show in passage')
  && pop.innerHTML.includes('‘my legs just would not go’') };
thKqGo();
Object.assign(out.click, { passage: passaged.slice(), after: TH.kqpop, hidden: pop.hidden });

// ── the room a quote takes, as a view
const r = { cards: { a: card('A', 0, 40), b: card('B', 210, 40), c: card('C', 0, 140), d: card('D', 210, 140) },
            groups: [{ id: 'g1', label: 'Fear held in the body', members: ['a', 'b', 'c', 'd'], x: 0, y: 0 }], discarded: [], stacks: {} };
TH.v = r;
TH.opened = new Set();
TH.shifts = [];
TH.roomShown = null;
TH.els = { cards: {}, under: {}, labels: {}, frames: {}, stickies: {}, rails: {} };
const base = () => { TH.sizes = { a: { w: 200, h: 90 }, b: { w: 200, h: 90 }, c: { w: 200, h: 90 }, d: { w: 200, h: 90 }, g1: { w: 160, h: 26 } }; };
base();
TH.qfull = { a: 140 }; TH.qextra = { a: 50 }; TH.sizes.a = { w: 200, h: 140 };
thStacksRoom();
out.room = { on: { c: r.cards.c.y, d: r.cards.d.y }, clashes: thClashes(r, thSize).length };
base(); TH.qfull = {}; TH.qextra = {};
thStacksRoom();
out.room.off = { c: r.cards.c.y, d: r.cards.d.y };
// on again, and D let go under C in the first column, where the quote's room stands
base(); TH.qfull = { a: 140 }; TH.qextra = { a: 50 }; TH.sizes.a = { w: 200, h: 140 };
thStacksRoom();
r.cards.d.x = 0; r.cards.d.y = 300;
base(); TH.qfull = { a: 140 }; TH.qextra = { a: 50 }; TH.sizes.a = { w: 200, h: 140 };
thStacksRoom();
out.room.dropped = { shown: r.cards.d.y, kept: thUnshifted(r).cards.d.y };

// ── Arrange by participant
TH.mode = 'gets';
TH.shifts = []; TH.roomShown = null; TH.qfull = {}; TH.qextra = {};
const pets = (list) => list.map(([id, parent]) => ({ id, parent, title: id }));
// Petra's first PET, g3, is in the GET, so its sub-theme g4 goes at the end of her row, after g1 and its g2
TH.gets = { cases: [{ case: 'Petra', pets: pets([['g3', null], ['g4', 'g3'], ['g1', null], ['g2', 'g1']]) },
                    { case: 'Ivo', pets: pets([['g1', null], ['g2', 'g1'], ['g3', null]]) }] };
const gc = (kind, kase, x, y) => ({ x, y, kind, case: kase, text: 'A theme' });
const w = { cards: { 'Ivo/g3': gc('pet', 'Ivo', 400, 500), 'Ivo/g2': gc('sub', 'Ivo', 700, 520), 'Ivo/g1': gc('pet', 'Ivo', 300, 700),
                     'Petra/g2': gc('sub', 'Petra', 900, 600), 'Petra/g1': gc('pet', 'Petra', 100, 650),
                     'Petra/g4': gc('sub', 'Petra', 20, 800),
                     'Petra/g3': gc('pet', 'Petra', 40, 60), 'Ivo/es/Initial:5:0': gc('es', 'Ivo', 260, 60),
                     'Ivo/es/Initial:9:0': gc('es', 'Ivo', 1400, 60) },
            groups: [{ id: 'G1', label: 'Water as threat', members: ['Petra/g3', 'Ivo/es/Initial:5:0'], x: 40, y: 30 }], discarded: [] };
TH.sizes = { G1: { w: 160, h: 26 } };
for (const k of Object.keys(w.cards)) TH.sizes[k] = { w: 200, h: 80 };
TH.v = w;
TH.removed = new Set();
TH.undo = []; TH.redo = [];
const was = JSON.parse(JSON.stringify(w.cards));
gtArrangeByParticipant();
const layout = thLayout(w, thSize, null);
const at = (k) => w.cards[k];
const rowOf = (kase) => Object.keys(w.cards).filter((k) => k.startsWith(`${kase}/g`) && k !== 'Petra/g3').sort((a, b) => at(a).x - at(b).x);
out.rows = {
  kept: ['Petra/g3', 'Ivo/es/Initial:5:0'].every((k) => at(k).x === was[k].x && at(k).y === was[k].y),
  order: [rowOf('Petra'), rowOf('Ivo')],
  oneRow: rowOf('Petra').every((k) => at(k).y === at('Petra/g1').y) && rowOf('Ivo').every((k) => at(k).y === at('Ivo/g1').y)
    && at('Petra/g1').y < at('Ivo/g1').y,
  below: at('Petra/g1').y >= layout.G1.frame.y + layout.G1.frame.h && at('Petra/g1').x === Math.min(layout.G1.frame.x, at('Ivo/es/Initial:9:0').x),
  gap: [at('Ivo/g2').x - at('Ivo/g1').x - 200, at('Ivo/g3').x - at('Ivo/g2').x - 200],
  es: at('Ivo/es/Initial:9:0').x === 1400 && at('Ivo/es/Initial:9:0').y === 60,
  clashes: thClashes(w, thSize).length,
};
const steps = TH.undo.length;
thUndo(true);
const back = Object.keys(was).every((k) => w.cards[k].x === was[k].x && w.cards[k].y === was[k].y);
const all = { cards: { 'Ivo/g1': gc('pet', 'Ivo', 0, 0) }, groups: [{ id: 'G2', label: 'All in', members: ['Ivo/g1'], x: 0, y: 0 }], discarded: [] };
out.undo = { steps, back, none: gtByParticipant(all, TH.gets.cases, thSize) };
console.log(JSON.stringify(out));
})().catch((err) => { console.error(err && err.stack ? err.stack : String(err)); process.exit(1); });
"""
