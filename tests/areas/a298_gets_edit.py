"""Area 298: a statement edited from a GETs, LGETs or LPETs board (getsedit, 30 October 2026).

Adam, 30 October, by dialog: "Edit there too". Since cardedit a double-click on a statement card on the PETs board
edits its words on the card, and on the GETs, LGETs and LPETs boards it now does the same, the GETs boards' copy of
each participant updated by the server. The edit goes through the PETs board's route, `/api/edit-statement`, into the
participant's own workbook, and in the same request every copy follows: the participant's PETs boards at the
timepoint the statement's sheet is at, the GETs file's copy and each GETs board's card, and in a project of
timepoints the participant's LPETs and the project's LGETs, each copy left in, not Changed since it came in. History
is as the PETs board's edit leaves it, the board's own and the progress file's untouched. An agent does the same with
`turn write`, whose dry run writes nothing and whose write History names, the GETs board keeping a revision under his
request and marked changed in a conversation. In node, themes.js's own `thPointerUp` opens the editor on a GETs
statement card and writes the participant's own workbook, the Participants panel's copy and the board's version
following.

Every word invented: newcomers to a community choir in their first term, Hale and Brin, asked by Nell.
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
from pathlib import Path

from workbook import WorkbookError

from . import support
from .support import check as said_check, skip
from .a297_card_edit import STUBS as CARD_STUBS
import idiograph_routes


def check(name, ok, detail=""):
    said_check(name, ok, str(detail)[:700])


HALE = ("Nell: [00:00:03] What did you expect of the choir?\nHale: [00:00:09] I thought I would mime at the back.\n"
        "Nell: [00:00:40] And the first concert?\nHale: [00:12:30] My knees shook through the whole carol.\n")
BRIN = ("Nell: [00:00:03] Why join a choir?\nBrin: [00:00:07] To sing with people who do not mind a wrong note.\n")
HALE_T2 = ("Nell: [00:00:02] How is it now?\nHale: [00:00:06] I stand in the front row and sing out.\n")
TWO = [{"label": "T1", "description": "First rehearsal"}, {"label": "T2", "description": "After the concert"}]

# the page's api in area 297's stubs, answering here as each part of the scenario asks
API_WAS = ("  if (body && body.check) return { ready: true, copies: true };\n"
           "  return { text: String(body.text).trim(), old: body.old, changed: true, versions: [] };")

SCENARIO = r"""
(async () => {
const want = JSON.parse(process.env.GE_WANT);
const out = {};
const tick = () => new Promise((r) => setImmediate(r));
ELS['th-stage'] = new El('div', 'th-stage');
const went = [];
thToPassage = (key) => { went.push(['passage', key]); };
gtCardOpen = (key) => { went.push(['inspector', key]); };
thRender = () => {}; thDrawSel = () => {}; thPanelFollow = () => {}; thPanelDraw = () => {}; thPlace = () => {};
thSoon = () => {}; thNoteDone = () => {}; thStickyEditDone = () => {}; thMenuClose = () => {}; gtCasesDraw = () => {};
thFileBoxes = () => ({});
thInFile = () => false;
let copies = null;
globalThis.ANSWER = (path, body) => {
  if (body && body.check) return copies ? { ready: true, copies: true } : { ready: true };
  return { sheet: body.sheet, row: body.row, line: body.line, old: body.old, text: String(body.text).trim(), changed: true,
           versions: [{ id: 'b1', v: 'pets-board' }], copies };
};
const card = (key, text) => {
  const el = new El('div', 'th-card');
  el.dataset.key = key;
  const words = new El('p', 'th-text'); words.innerHTML = esc(text);
  el.appendChild(words);
  el.appendChild(new El('div', 'th-foot'));
  return el;
};
const es = want.key;
const ident = es.split('/es/')[1];
const fresh = () => {
  TH.mode = 'gets'; TH.live = true; TH.busy = false; TH.writing = false; TH.cardEdit = null; TH.path = want.page;
  TH.v = { cards: { [es]: { x: 0, y: 0, kind: 'es', case: want.kase, who: 'Hale', text: want.old, time: '0:09', sheet: want.sheet },
                    [want.pet]: { x: 210, y: 0, kind: 'pet', case: want.kase, who: 'Hale', text: 'Hiding at first' } },
           groups: [], discarded: [], stickies: [] };
  TH.removed = []; TH.sel = { cards: new Set(), groups: new Set(), stickies: new Set() }; TH.undo = []; TH.redo = [];
  TH.meta = { id: 'b1', name: 'Board 1', v: 'before' };
  TH.gets = { cases: [{ case: want.kase, who: 'Hale', path: want.book, lines: { [ident]: { text: want.old, sheet: want.sheet } } }] };
  TH.els = { cards: { [es]: card(es, want.old), [want.pet]: card(want.pet, 'Hiding at first') }, under: {}, labels: {}, frames: {},
             stickies: {}, rails: {} };
};
const press = (item) => {
  TH.press = { item, x0: 0, y0: 0, add: false, alt: false, kq: false };
  thPointerUp({ pointerId: 1, clientX: 0, clientY: 0 });
};
const twice = async (item) => { TH.lastClick = null; press(item); press(item); await tick(); await tick(); };
const writes = () => CALLS.filter(([p, b]) => p === '/api/edit-statement' && !b.check).map(([, b]) => b);

// ── 1. a server from before the copies: the double-click says to restart and opens nothing
fresh();
TH.canEdit = false; TH.canCopies = false;
SAID.length = 0;
await twice({ kind: 'card', id: es });
out.older = { said: SAID.slice(), editing: !!TH.cardEdit, writes: writes().length, went: went.slice() };

// ── 2. a statement card on a GETs board opens the PETs board's editor, and Enter writes its participant's workbook
copies = { gets: { cases: [want.kase], boards: [{ board: 'b1', name: 'Board 1', keys: [es] }],
                   versions: [{ id: 'b1', v: 'gets-after' }] },
           lpets: { cases: ['T1'], boards: [], versions: [{ id: 'b1', v: 'lpets-after' }] } };
fresh();
await twice({ kind: 'card', id: es });
const box = TH.cardEdit && TH.cardEdit.box;
out.open = { editing: TH.cardEdit ? TH.cardEdit.key : null, whole: !!box && box.value === want.old, went: went.slice(),
             hidden: TH.els.cards[es].querySelector('.th-text').hidden };
box.value = want.now;
box.fire('keydown', { key: 'Enter', isComposing: false });
await tick(); await tick();
out.saved = { writes: writes(), card: TH.v.cards[es].text, panel: TH.gets.cases[0].lines[ident].text, v: TH.meta.v,
              undo: TH.undo.map((u) => [u.what, u.edit && u.edit.key]), went: went.slice() };

// ── 3. a PET's card still opens the Inspector
went.length = 0;
await twice({ kind: 'card', id: want.pet });
out.pet = { went: went.slice(), editing: !!TH.cardEdit };

// ── 4. on LPETs the board's version comes from the LPETs' copy
fresh();
TH.lpets = true;
await twice({ kind: 'card', id: es });
TH.cardEdit.box.value = want.again;
TH.cardEdit.box.fire('keydown', { key: 'Enter', isComposing: false });
await tick(); await tick();
out.lpets = { v: TH.meta.v, card: TH.v.cards[es].text };
TH.lpets = false;

// ── 5. a card no longer in its participant's copy has no line to write
fresh();
TH.v.cards[es].gone = true;
SAID.length = 0;
const before = writes().length;
await twice({ kind: 'card', id: es });
out.gone = { said: SAID.slice(), editing: !!TH.cardEdit, writes: writes().length - before };
console.log(JSON.stringify(out));
})().catch((err) => { console.error(err && err.stack || String(err)); process.exit(1); });
"""


def test_gets_edit(scratch):
    print("\n298. A statement edited from a GETs, LGETs or LPETs board: the workbook, the PETs boards, the GETs' copy "
          "and every GETs board's card taking the words at once, the participant left in, History as the PETs "
          "board's edit leaves it, the same from LPETs in a project of timepoints, an agent's turn write doing the "
          "same with its dry run writing nothing, and in node the editor on a GETs card (Adam, 30 October)")
    import cli
    import gets as gets_mod
    import server as server_mod
    import themes
    import workbook as wb_mod

    b64 = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")
    base = scratch / "a298"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    cfg_file = scratch / "a298-config.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "Nell", "corpus": "", "gravity_reference": "",
                                    "corpus_exclude": []}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)

    def tree(at: Path) -> dict:
        return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*"))
                if p.is_file() and p.suffix != ".lock"}

    def row(name, text, who, interview, **more):
        return dict({"name": name, "data": b64(text), "pseudonym": who, "interview": interview,
                     "speakers": {"Nell": "interviewer", who: "participant"}}, **more)

    def said_rows(book: Path, sheet: str, who: str) -> list[int]:
        import openpyxl
        wb = openpyxl.load_workbook(book, read_only=True)
        try:
            return [r for r, values in enumerate(wb[sheet].iter_rows(min_row=2, max_col=1, values_only=True), start=2)
                    if str(values[0] or "").strip() == who]
        finally:
            wb.close()

    def statements(book: Path, sheet: str, at: int) -> list[str]:
        import openpyxl
        wb = openpyxl.load_workbook(book, read_only=True)
        try:
            ws = wb[sheet]
            col = wb_mod.detect_columns(ws)["es"]
            return wb_mod.split_entries(ws.cell(at, col).value)
        finally:
            wb.close()

    def call(route: str, body: dict) -> dict:
        with idiograph_routes.route_scope(route, body):
            return server_mod.ROUTES[route](body)

    def board_of(book: Path, tp, groups: list):
        """A PETs board, at a timepoint or none, each PET the cards at those places in the canvas's order."""
        body = {"workbook": str(book)} if tp is None else {"workbook": str(book), "timepoint": tp}
        st = call("/api/themes", body)
        keys = [c["key"] for c in st["cards"]]
        # each card with its words, as the page saves a board
        words = {c["key"]: c["text"] for c in st["cards"]}
        v = dict(st["version"], cards={k: {"x": 0, "y": 40 * i, "text": words[k]} for i, k in enumerate(keys)},
                 groups=[{"id": f"g{i + 1}", "label": label, "members": [keys[j] for j in at], "x": 300 * i, "y": -40}
                         for i, (label, at) in enumerate(groups)], discarded=[], picks={})
        call("/api/themes-save", dict(body, version=v))

    def board_with(answer: dict, extra: dict, label: str) -> dict:
        """A GETs board as the page saves it: every card where it lies, the statements' cards added with their
        words, and one GET over them all."""
        cards = {c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in answer["cards"]}
        cards.update({k: {"x": 700, "y": 60 * i, "text": t} for i, (k, t) in enumerate(extra.items())})
        return dict(answer["version"], cards=cards, groups=[{"id": "G1", "label": label, "members": list(cards),
                                                             "x": -20, "y": -60}], discarded=[], picks={}, notes=[])

    def pets_card(book: Path, key: str, tp=None) -> str:
        """A statement's card's words as the PETs file of its timepoint keeps them on its first board."""
        held = json.loads(themes.themes_path(book, tp).read_text(encoding="utf-8"))
        return str(((held["boards"][0].get("cards") or {}).get(key) or {}).get("text") or "")

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "a298-state.json", {"recent": []}

        # ── A. a project of one timepoint: the edit from a GETs board
        choir = base / "Choir term"
        choir.mkdir()
        made = idiograph_routes.api_new_project({"op": "make", "folder": str(choir), "name": "Choir term",
                                                 "research_question": "How do newcomers find their voice in a choir?",
                                                 "files": [row("hale.txt", HALE, "Hale", "Autumn"),
                                                           row("brin.txt", BRIN, "Brin", "Autumn")]})
        idiograph_routes.api_project({"root": made["project"]["id"], "agents": True})
        hale = choir / "P1 - Hale" / "P1 Hale - EN & ES.xlsx"
        brin = choir / "P2 - Brin" / "P2 Brin - EN & ES.xlsx"
        sheet = idiograph_routes.read_sheets(hale)[1][0]
        h, b = said_rows(hale, sheet, "Hale"), said_rows(brin, sheet, "Brin")
        wb_mod.save_turn(hale, sheet, h[0], "Expecting to hide\nMiming at the back", "", "")
        wb_mod.save_turn(hale, sheet, h[1], "Shaking through a carol", "", "")
        wb_mod.save_turn(brin, sheet, b[0], "Singing among the forgiving", "", "")
        board_of(hale, None, [("Hiding at first", [0, 1]), ("Nerves on stage", [2])])
        board_of(brin, None, [("A forgiving room", [0])])
        line = themes.card_key(sheet, h[0], 1)
        es_key = gets_mod.card_of("P1 - Hale", "es", line)
        brin_line = themes.card_key(sheet, b[0], 0)
        brin_key = gets_mod.card_of("P2 - Brin", "es", brin_line)
        g = call("/api/gets", {"workbook": str(hale)})
        call("/api/gets-save", {"workbook": str(hale), "version": board_with(
            g, {es_key: "Miming at the back", brin_key: "Singing among the forgiving"}, "Finding a voice")})
        call("/api/gets-ops", {"workbook": str(hale), "op": "duplicate", "id": "b1"})
        gfile = choir / gets_mod.FILE
        held = json.loads(gfile.read_text(encoding="utf-8"))
        hale_path = next(c["path"] for c in call("/api/gets", {"workbook": str(hale)})["cases"] if c["case"] == "P1 - Hale")
        progress = hale.parent / "Working" / f"{hale.stem}.progress.json"
        had_progress = progress.read_bytes() if progress.exists() else None
        histories = {b["id"]: len(b.get("history") or []) for b in held["boards"]}
        pets_history = len((themes.load(hale)["boards"][0]).get("history") or [])
        check("298: the GETs file holds Hale's copy and two boards with the statement's card on each",
              len(held["boards"]) == 2 and all(es_key in bd["cards"] for bd in held["boards"])
              and held["cases"]["P1 - Hale"]["lines"][line]["text"] == "Miming at the back", str(sorted(held)))

        # the page's own call: its participant's workbook as the Participants panel names it, the line its key names
        edited = call("/api/edit-statement", {"workbook": hale_path, "sheet": sheet, "row": h[0], "line": 1,
                                              "text": "  Miming,\nthen singing  ", "old": "Miming at the back"})
        now = json.loads(gfile.read_text(encoding="utf-8"))
        g2 = call("/api/gets", {"workbook": str(hale)})
        check("298: an edit from a GETs board lands in the participant's workbook, that line alone, one line",
              edited["changed"] and edited["text"] == "Miming, then singing"
              and statements(hale, sheet, h[0]) == ["Expecting to hide", "Miming, then singing"], str(edited))
        check("298: the GETs file's copy of the participant takes the words, and so does the card on every GETs board",
              now["cases"]["P1 - Hale"]["lines"][line]["text"] == "Miming, then singing"
              and [bd["cards"][es_key]["text"] for bd in now["boards"]] == ["Miming, then singing"] * 2
              and next(c for c in g2["cards"] if c["key"] == es_key)["text"] == "Miming, then singing",
              str([bd["cards"][es_key] for bd in now["boards"]]))
        check("298: the participant stays in, not Changed since it came in, and nothing waits on the stamp",
              {c["case"]: c["status"] for c in g2["cases"]} == {"P1 - Hale": "in", "P2 - Brin": "in"}
              and call("/api/stamp", {"workbook": str(hale), "gets": True})["cases"] == [],
              str([(c["case"], c["status"]) for c in g2["cases"]]))
        mine = next(v for v in edited["copies"]["gets"]["versions"] if v["id"] == g2["current"])
        saved = call("/api/gets-save", {"workbook": str(hale), "version": dict(board_with(
            g2, {}, "Finding a voice"), v=mine["v"])})
        check("298: the answer names the copy and the boards that took the words, and its version lets the page's "
              "next save go",
              edited["copies"]["gets"]["cases"] == ["P1 - Hale"]
              and [x["keys"] for x in edited["copies"]["gets"]["boards"]] == [[es_key], [es_key]]
              and saved.get("saved") is True, str(edited["copies"])[:400])
        check("298: the participant's PETs board takes the words, and the statements screen reads them",
              pets_card(hale, line) == "Miming, then singing"
              and "Miming, then singing" in json.dumps(idiograph_routes.case_payload(hale))
              and "Miming at the back" not in json.dumps(idiograph_routes.case_payload(hale)))
        after = json.loads(gfile.read_text(encoding="utf-8"))
        # since histreplace (30 October) the edit leaves one line on each board that holds the statement
        said = 'Hale\'s statement edited: "Miming at the back" to "Miming, then singing"'
        check("298: History as the PETs board's edit leaves it: the progress file as it was, and one line on each GETs "
              "board and the PETs board, the edit's",
              (progress.read_bytes() if progress.exists() else None) == had_progress
              and {bd["id"]: len(bd.get("history") or []) for bd in after["boards"]} == {k: n + 1 for k, n in histories.items()}
              and all(bd["history"][-1]["name"] == said for bd in after["boards"])
              and len((themes.load(hale)["boards"][0]).get("history") or []) == pets_history + 1
              and themes.load(hale)["boards"][0]["history"][-1]["name"] == said,
              str([bd.get("history", [{}])[-1].get("name") for bd in after["boards"]]))
        check("298: Brin's copy and card are as they were",
              after["cases"]["P2 - Brin"]["lines"][brin_line]["text"] == "Singing among the forgiving"
              and after["boards"][0]["cards"][brin_key]["text"] == "Singing among the forgiving")
        still = gfile.read_bytes()
        try:
            call("/api/edit-statement", {"workbook": hale_path, "sheet": sheet, "row": h[0], "line": 1,
                                         "text": "Anything", "old": "Miming at the back"})
            refused = ""
        except WorkbookError as exc:
            refused = str(exc)
        check("298: a line that reads otherwise now is refused with the PETs board's line, the GETs file untouched",
              refused == wb_mod.STATEMENT_MOVED and gfile.read_bytes() == still, refused)
        check("298: the route's check says it carries an edit to the GETs' copies, writing nothing",
              call("/api/edit-statement", {"workbook": hale_path, "check": True}) == {"ready": True, "copies": True}
              and gfile.read_bytes() == still)

        # ── B. an agent's turn write of Brin's statement, its dry run first
        def run(*args):
            code, text, err = cli.run(["--root", str(choir), "--config", str(cfg_file), *args, "--json"])
            return code, (support.plain(json.loads(text)) if text.strip() else {}), err

        spec = scratch / "a298-turn.json"
        code, shown, err = run("turn", "show", "Brin", sheet, str(b[0]))
        version = shown["turns"][0]["version"] if code == 0 and shown.get("turns") else None
        spec.write_text(json.dumps({"pairs": [{"statement": "Singing where a wrong note is forgiven", "quote": "",
                                               "key": brin_line}], "version": version,
                                    "request": "Say forgiven in Brin's statement"}), encoding="utf-8")
        whole = tree(choir)
        code, dry, err = run("turn", "write", "Brin", sheet, str(b[0]), "--from", str(spec), "--dry-run")
        check("298: an agent's turn write in a dry run says the GETs' copy and its cards would take the words, and "
              "writes nothing",
              code == 0 and dry.get("dry_run") is True and dry["copies"]["gets"]["cases"] == ["P2 - Brin"]
              and [x["keys"] for x in dry["copies"]["gets"]["boards"]] == [[brin_key], [brin_key]]
              and tree(choir) == whole, err or str(dry)[:500])
        code, wrote, err = run("turn", "write", "Brin", sheet, str(b[0]), "--from", str(spec), "--tool", "Claude Code")
        agent = json.loads(gfile.read_text(encoding="utf-8"))
        g3 = call("/api/gets", {"workbook": str(brin)})
        brin_progress = json.loads((brin.parent / "Working" / f"{brin.stem}.progress.json").read_text(encoding="utf-8"))
        check("298: the agent's write lands in the workbook, the GETs' copy and every GETs board's card, Brin still in",
              code == 0 and statements(brin, sheet, b[0]) == ["Singing where a wrong note is forgiven"]
              and agent["cases"]["P2 - Brin"]["lines"][brin_line]["text"] == "Singing where a wrong note is forgiven"
              and [bd["cards"][brin_key]["text"] for bd in agent["boards"]] == ["Singing where a wrong note is forgiven"] * 2
              and {c["case"]: c["status"] for c in g3["cases"]}["P2 - Brin"] == "in", err or str(wrote)[:500])
        check("298: History names it: each GETs board keeps itself first under his request, marked changed in a "
              "conversation by the agent, and the progress file records the write as the agent's",
              all(bd["history"][-1]["name"] == "Before: Say forgiven in Brin's statement" for bd in agent["boards"])
              and all(bd["changed"]["by"] == "agent" and bd["changed"]["tool"] == "Claude Code" for bd in agent["boards"])
              and brin_progress["edits"][-1]["by"] == "agent"
              and brin_progress["edits"][-1]["request"] == "Say forgiven in Brin's statement",
              str([bd.get("history", [{}])[-1].get("name") for bd in agent["boards"]]))

        # ── C. a project of two timepoints: the edit from Hale's LPETs board
        hall = base / "Choir year"
        hall.mkdir()
        made2 = idiograph_routes.api_new_project({"op": "make", "folder": str(hall), "name": "Choir year",
                                                  "research_question": "How do newcomers find their voice in a choir?",
                                                  "files": [row("hale-one.txt", HALE, "Hale", "Autumn")]})
        root2 = made2["project"]["id"]
        idiograph_routes.api_project({"root": root2, "timepoints": TWO})
        idiograph_routes.api_add_transcripts({"op": "add", "root": root2, "files": [
            row("hale-two.txt", HALE_T2, "Hale", "Spring", timepoint=2)]})
        lh = hall / "P1 - Hale" / "P1 Hale - EN & ES.xlsx"
        s1 = idiograph_routes.read_sheets(lh)[1][0]
        s2 = "Spring"
        r1, r2 = said_rows(lh, s1, "Hale"), said_rows(lh, s2, "Hale")
        wb_mod.save_turn(lh, s1, r1[0], "Expecting to hide", "", "")
        wb_mod.save_turn(lh, s2, r2[0], "Standing at the front", "", "")
        board_of(lh, 1, [("Hiding at first", [0])])
        board_of(lh, 2, [("Out in front", [0])])
        t2_line = themes.card_key(s2, r2[0], 0)
        lp_key = gets_mod.card_of("T2", "es", t2_line)
        lp = call("/api/gets", {"workbook": str(lh), "lpets": True})
        call("/api/gets-save", {"workbook": str(lh), "lpets": True, "version": board_with(
            lp, {lp_key: "Standing at the front"}, "From the back to the front")})
        lg_key = gets_mod.card_of("P1 - Hale", "es", t2_line)
        lg = call("/api/gets", {"workbook": str(lh)})
        call("/api/gets-save", {"workbook": str(lh), "version": board_with(lg, {lg_key: "Standing at the front"},
                                                                          "Finding a voice")})
        lpfile, lgfile = gets_mod.lpets_path(lh), hall / gets_mod.LGETS_FILE
        lp_path = next(c["path"] for c in lp["cases"] if c["case"] == "T2")
        edited2 = call("/api/edit-statement", {"workbook": lp_path, "sheet": s2, "row": r2[0], "line": 0,
                                               "text": "Standing in the front row", "old": "Standing at the front"})
        lpd = json.loads(lpfile.read_text(encoding="utf-8"))
        lgd = json.loads(lgfile.read_text(encoding="utf-8"))
        lp2 = call("/api/gets", {"workbook": str(lh), "lpets": True})
        lg2 = call("/api/gets", {"workbook": str(lh)})
        check("298: from an LPETs board a later timepoint's statement lands in the workbook and its timepoint's PETs "
              "board, the first timepoint's left alone",
              edited2["changed"] and statements(lh, s2, r2[0]) == ["Standing in the front row"]
              and pets_card(lh, t2_line, 2) == "Standing in the front row"
              and pets_card(lh, themes.card_key(s1, r1[0], 0), 1) == "Expecting to hide", str(edited2)[:300])
        check("298: the participant's LPETs copy and card take the words, and so do the project's LGETs copy and card",
              lpd["cases"]["T2"]["lines"][t2_line]["text"] == "Standing in the front row"
              and lpd["boards"][0]["cards"][lp_key]["text"] == "Standing in the front row"
              and lgd["cases"]["P1 - Hale"]["lines"][t2_line]["text"] == "Standing in the front row"
              and lgd["boards"][0]["cards"][lg_key]["text"] == "Standing in the front row"
              and sorted(edited2["copies"]) == ["lgets", "lpets"], str(sorted(edited2["copies"])))
        check("298: every timepoint stays in on the LPETs, and the participant on the LGETs",
              {c["case"]: c["status"] for c in lp2["cases"]} == {"T1": "in", "T2": "in"}
              and {c["case"]: c["status"] for c in lg2["cases"]} == {"P1 - Hale": "in"},
              str([(c["case"], c["status"]) for c in lp2["cases"] + lg2["cases"]]))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept

    # ── D. in node, themes.js's own double-click and write on a GETs board
    node = shutil.which("node")
    if not node:
        skip("298: the GETs card's editor in node", "node is not installed")
        return
    if API_WAS not in CARD_STUBS:
        check("298: area 297's page stubs carry the api this scenario answers through", False)
        return
    stubs = CARD_STUBS.replace(API_WAS, "  return globalThis.ANSWER(path, body);")
    js = support.text("apps/idiograph/static/themes.js")
    want = {"key": "P1 - Hale/es/Autumn:2:1", "kase": "P1 - Hale", "pet": "P1 - Hale/g1", "sheet": "Autumn",
            "book": "choir/P1 - Hale/P1 Hale - EN & ES.xlsx", "page": "choir/P2 - Brin/P2 Brin - EN & ES.xlsx",
            "old": "Miming at the back", "now": "Miming, then singing", "again": "Miming, then singing out"}
    path = scratch / "gets-edit-298.js"
    path.write_text(support.i18n_js() + stubs + js + SCENARIO, encoding="utf-8")
    run = subprocess.run([node, str(path)], capture_output=True, text=True, encoding="utf-8", timeout=120,
                         env=dict(os.environ, GE_WANT=json.dumps(want)))
    if run.returncode != 0:
        check("298: the GETs card's editor runs in node", False, run.stderr.strip()[:800])
        return
    o = json.loads(run.stdout)
    check("298: in node, in front of a server from before the copies a GETs statement card's double-click says to "
          "restart and opens nothing",
          o["older"]["editing"] is False and o["older"]["writes"] == 0 and len(o["older"]["said"]) == 1
          and o["older"]["went"] == [], o["older"])
    check("298: in node, a double-click on a statement card on a GETs board opens the PETs board's editor on the card, "
          "the whole statement in it, and never the passage",
          o["open"] == {"editing": want["key"], "whole": True, "went": [], "hidden": True}, o["open"])
    sv = o["saved"]
    check("298: in node, Enter writes the participant's own workbook at the line its key names, the card and the "
          "Participants panel's copy take the words, the board's version comes from the GETs' copy, one step of undo",
          sv["writes"] == [{"workbook": want["book"], "sheet": "Autumn", "row": 2, "line": 1, "text": want["now"],
                            "old": want["old"]}]
          and sv["card"] == want["now"] and sv["panel"] == want["now"] and sv["v"] == "gets-after"
          and sv["undo"] == [["Edited a statement", want["key"]]] and sv["went"] == [], sv)
    check("298: in node, a PET card's double-click still opens its Inspector",
          o["pet"] == {"went": [["inspector", want["pet"]]], "editing": False}, o["pet"])
    check("298: in node, on LPETs the board's version comes from the LPETs' copy",
          o["lpets"] == {"v": "lpets-after", "card": want["again"]}, o["lpets"])
    check("298: in node, a card no longer in its participant's copy says so and opens nothing",
          o["gone"]["editing"] is False and o["gone"]["writes"] == 0 and len(o["gone"]["said"]) == 1, o["gone"])
