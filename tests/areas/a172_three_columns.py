from __future__ import annotations

import json
import re
import shutil

from . import support
from .support import check, skip
import idiograph_routes


def test_three_columns(scratch):
    print("\n172. The statements screen in the book's three columns, 17 October, Adam's decision on a tester's J-way "
          "(Smith, Flowers and Larkin 2022, Box 5.4): experiential statements, the transcript and exploratory notes side "
          "by side, each passage a row across the three, the order his from a heading's grip or Columns, the current "
          "passage's statements a card in its row with Next at its foot, every other passage's read-only beside it, a "
          "click on one going to it, the panel, Previous and Quote gone, three columns down to 801px, two below and one "
          "at a phone's width. Since the test review of 18 October the headings, the card, the widths and the words are "
          "review shots, and the order kept and read back, the grips, the card's move and a click on a statement stay")
    import subprocess
    import server as server_mod

    read = lambda path: path.read_text(encoding="utf-8")
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    node = shutil.which("node")

    def whole(name):
        """A function of app.js whole."""
        at = app.index(f"function {name}(")
        if app[max(0, at - 6):at] == "async ":
            at -= 6
        return app[at:app.index("\n}", at) + 2]

    body = lambda name: whole(name).split("{", 1)[1]
    line = lambda start: start + app.split(start, 1)[1].split("\n", 1)[0] if start in app else ""
    block = lambda start, end: app[app.index(start):app.index(end, app.index(start)) + len(end)] if start in app else ""

    # ── A. the orders: the key, the six, the book's first, an old notes' place read as the nearest
    merge = server_mod.merge_config
    check("172: the server keeps the three columns' order as statements_columns, the book's on a new install and as the "
          "Mac app ships, an order kept as written, an old notes' place read as the order nearest it, and anything else "
          "the book's",
          server_mod.defaults()["statements_columns"] == ["statements", "transcript", "notes"]
          and server_mod.shipped_config()["statements_columns"] == ["statements", "transcript", "notes"]
          and merge({})["statements_columns"] == ["statements", "transcript", "notes"]
          and merge({"statements_columns": ["notes", "statements", "transcript"]})["statements_columns"] == ["notes", "statements", "transcript"]
          and [merge({"notes_place": p})["statements_columns"] for p in ("right", "left", "under")]
          == [["transcript", "notes", "statements"], ["notes", "transcript", "statements"], ["transcript", "statements", "notes"]]
          and merge({"statements_columns": ["notes", "statements"]})["statements_columns"] == ["statements", "transcript", "notes"]
          and idiograph_routes.statements_columns(["a", "b", "c"]) is None and idiograph_routes.statements_columns(None, "right")
          == ["transcript", "notes", "statements"])
    saved = server_mod.CONFIG_PATH
    server_mod.CONFIG_PATH = scratch / "columns-172-config.json"
    try:
        server_mod.CONFIG_PATH.write_text(json.dumps({"interviewer": "Wren", "notes_place": "under", "minimap": "on"}),
                                          encoding="utf-8")
        first = server_mod.config()["statements_columns"]
        moved = server_mod.api_settings({"statements_columns": ["statements", "notes", "transcript"]})["config"]
        odd = server_mod.api_settings({"statements_columns": ["statements", "statements", "notes"]})["config"]
        disk = json.loads(server_mod.CONFIG_PATH.read_text(encoding="utf-8"))
    finally:
        server_mod.CONFIG_PATH = saved
    check("172: a settings file with the notes under the statements opens on transcript, statements, notes, a moved "
          "order is written and read back, a list that is not the three names leaves the file as it was, and the old "
          "key leaves the file on the save, every other key kept",
          first == ["transcript", "statements", "notes"] and moved["statements_columns"] == ["statements", "notes", "transcript"]
          and odd["statements_columns"] == ["statements", "notes", "transcript"]
          and disk["statements_columns"] == ["statements", "notes", "transcript"] and "notes_place" not in disk
          and disk["interviewer"] == "Wren" and disk["minimap"] == "on", str(disk.get("statements_columns")))

    # ── B. the grips
    check("172: a grip moves its column by a drag or by Alt and the left or "
          "right arrow, each kept as Columns keeps a choice, and a press on Columns opens its menu, its choice kept too",
          "$('cols-head').addEventListener('pointerdown', colGripDown);" in app
          and "$('cols-head').addEventListener('keydown', colGripKeys);" in app
          # since 21 October (236) the drop's settings from colsDropped, an order alone kept as before
          and "const change = colsDropped(" in body("colGripDown")
          and "setView('statements_columns', change.statements_columns);" in body("colGripDown")
          and "if (!grip || !e.altKey || (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight')) return;" in body("colGripKeys")
          and "setView('statements_columns', next);" in body("colGripKeys")
          and "if (t.type === 'checkbox') setView('columns_hidden', colsTicked($('cols-show-statements'), $('cols-show-notes')));" in app)

    # ── C. a field grown to its prompt
    check("172: an empty field grows to its prompt, measured in a twin out of sight, never by writing into the field",
          "hintTwin.value = field.placeholder;" in body("growField") and "field.value =" not in body("growField")
          and "hintTwin.remove();" in body("growField") and "growField(field);" in app)

    # ── D. the read-only cells, and a click on one
    check("172: each of her passages carries a statements cell and a notes cell after its words, the interviewer's "
          "neither, and a click on one of the statements goes to it with the caret in it, a click in the card or an "
          "interviewer note keeping its own",
          "const cells = row.stop\n    ? `<div class=\"turn-es\">${statementsHtml(row)}</div><div class=\"turn-notes\">${notesHtml(row)}</div>` : '';" in app
          and "const said = e.target.closest('.turn-es .es-go');" in app
          and "if (said && row.stop) { toStatement(row, Number(said.dataset.es)); return; }" in app
          and "if (e.target.closest('#es-card, #note-entry')) return;" in app
          and "el.querySelector('.pair-es').focus({ preventScroll: true });" in body("toStatement"))
    if not node:
        skip("172: the columns in node", "node is not on this machine")
    else:
        # since 18 October (186) the six orders listed nowhere, and the layout's helpers in: where the card and the
        # notes field stand, and Columns' menu of ticks and choices
        pure = "\n".join([line("const COLUMNS = "), line("const COLUMN_WORDS = "), line("const COLUMN_KEYS = "),
                          block("const NOTES_PLACE_COLUMNS = {", "};"),
                          line("const isColumns = "), line("const columnsSaid = "), line("const HIDEABLE_COLUMNS = "),
                          line("const STACK_SPLIT = "), line("const STACK_RANGE = "), line("const colsHidden = "),
                          line("const colsNarrow = "), line("const stackedNow = ")]
                         + [whole(n) for n in ("columnsOf", "columnsHiddenOf", "stackSplitOf", "columnsLayout",
                                                "columnsShownSaid", "colsVars", "colsMoved", "colsStep", "statementsHtml",
                                                "notesHtml", "placeCard", "cardCell", "notesCell", "parkCard", "placeNotes",
                                                "parkNotes", "colsStackRows", "drawColsMenu", "toStatement")])
        script = scratch / "columns-172.js"
        script.write_text(support.i18n_js() + r"""
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const rowPairs = (row) => (row.pairs || []).map((p) => ({ es: p.es || '', kq: p.kq || '' }));
// a few elements, enough for the card and the notes field to move between rows and the park
const mk = (cls, extra = {}) => Object.assign({ cls: new Set(cls.split(' ').filter(Boolean)), children: [], parentElement: null,
  html: '', dataset: {},
  appendChild(c) { if (c.parentElement) c.parentElement.children.splice(c.parentElement.children.indexOf(c), 1); c.parentElement = this; this.children.push(c); return c; },
  prepend(c) { if (c.parentElement) c.parentElement.children.splice(c.parentElement.children.indexOf(c), 1); c.parentElement = this; this.children.unshift(c); return c; },
  replaceChildren(...cs) { for (const k of this.children) k.parentElement = null; this.children = []; this.html = ''; cs.forEach((c) => this.appendChild(c)); },
  set innerHTML(h) { for (const k of this.children) k.parentElement = null; this.children = []; this.html = h; }, get innerHTML() { return this.html; },
  closest(sel) { const c = sel.slice(1); let e = this; while (e) { if (e.cls.has(c)) return e; e = e.parentElement; } return null; } }, extra);
const park = mk('es-park'); const card = mk('es-card'); const en = mk(''); park.appendChild(card); park.appendChild(en);
const rows = [0, 1, 2].map((i) => { const r = mk('turn'); r.dataset.i = String(i); r.es = r.appendChild(mk('turn-es')); r.en = r.appendChild(mk('turn-notes')); return r; });
const els = { 'es-park': park, 'es-card': card, en,
  'transcript-rows': { querySelector: (sel) => { const r = rows.find((x) => x.cls.has('current'));
    return !r ? null : sel === '.turn.current .turn-es' ? r.es : sel === '.turn.current .turn-notes' ? r.en : null; } },
  'stack-es': mk('stack-es'), 'stack-en-cell': mk('stack-en-cell') };
// Columns' menu, its two ticks, its two choices in their labels and its one action (18 October, 186)
const input = () => { const label = { cls: new Set(), classList: { toggle(c, on) { if (on) label.cls.add(c); else label.cls.delete(c); } } };
  return { checked: false, disabled: false, label, closest: () => label }; };
for (const id of ['cols-show-statements', 'cols-show-notes', 'cols-side', 'cols-stacked']) els[id] = input();
els['cols-book'] = { disabled: false };
const $ = (id) => els[id];
let grown = 0; const growPairs = () => { grown += 1; }; const growNotes = () => {}; const footStuck = () => {};
const S = { flat: [
  { i: 0, stop: true, pos: 0, en: 'A first note', pairs: [{ es: 'Waiting as a kind of faith', kq: '"have to trust"' }] },
  { i: 1, stop: true, pos: 1, en: '', pairs: [{ es: 'One', kq: '"a"' }, { es: '', kq: '"b only"' }, { es: '', kq: '' }, { es: 'Four & <more>', kq: '' }] },
  { i: 2, stop: true, pos: 2, en: '', pairs: [] }], at: 0, columns: null, editing: null, timeEdit: null, note: null, pairFocus: null };
""" + pure + r"""
const out = {};
// every order a grip can make from the book's, a drag before any heading or after the last, then again
const made = new Set();
for (const a of COLUMNS) for (const at of [null, ...COLUMNS]) { const once = colsMoved(COLUMNS, a, at);
  made.add(once.join(',')); for (const b of COLUMNS) for (const at2 of [null, ...COLUMNS]) made.add(colsMoved(once, b, at2).join(',')); }
out.orders = [...made].sort();
out.read = { none: columnsOf(null).join(), kept: columnsOf({ statements_columns: ['notes', 'statements', 'transcript'] }).join(),
  left: columnsOf({ notes_place: 'left' }).join(), odd: columnsOf({ statements_columns: ['notes'] }).join(),
  both: columnsOf({ statements_columns: ['transcript', 'notes', 'statements'], notes_place: 'under' }).join() };
// the six orders written out here, since the page lists them nowhere now
const ORDERS = [['statements', 'transcript', 'notes'], ['statements', 'notes', 'transcript'], ['transcript', 'statements', 'notes'],
  ['transcript', 'notes', 'statements'], ['notes', 'statements', 'transcript'], ['notes', 'transcript', 'statements']];
out.vars = Object.fromEntries(ORDERS.map((o) => [o.join(','), colsVars(o)]));
out.moved = {
  endOfThree: colsMoved(COLUMNS, 'statements', null).join(),
  beforeTranscript: colsMoved(['transcript', 'notes', 'statements'], 'statements', 'transcript').join(),
  endOfTwo: colsMoved(['statements', 'transcript', 'notes'], 'statements', null, ['statements', 'transcript']).join(),
  onItself: colsMoved(COLUMNS, 'transcript', 'transcript').join() };
out.step = {
  right: (colsStep(COLUMNS, 'statements', 1) || []).join(), left: (colsStep(COLUMNS, 'notes', -1) || []).join(),
  edge: colsStep(COLUMNS, 'statements', -1), end: colsStep(COLUMNS, 'notes', 1),
  twoLeft: (colsStep(['transcript', 'notes', 'statements'], 'statements', -1, ['transcript', 'statements']) || []).join() };
out.said = { one: statementsHtml(S.flat[0]), four: statementsHtml(S.flat[1]), none: statementsHtml(S.flat[2]) };
out.words = { said: columnsSaid(COLUMNS), shown: columnsShownSaid(columnsLayout({ columns_hidden: ['notes'] })),
  alone: columnsShownSaid(columnsLayout({ columns_hidden: ['statements', 'notes'] })),
  stacked: columnsShownSaid(columnsLayout({ statements_columns: ['transcript', 'statements', 'notes'], columns_stacked: true })) };
// the card and the notes field into the current row, then on to the next, the row left showing its words
rows[0].cls.add('current');
placeCard(); placeNotes();
out.first = { card: card.parentElement === rows[0].es, en: en.parentElement === rows[0].en, grown };
rows[0].cls.delete('current'); rows[1].cls.add('current');
S.flat[0].pairs = [{ es: 'Waiting as a kind of faith', kq: '"have to trust"' }, { es: 'Saved on the way out', kq: '' }];
placeCard(); placeNotes();
out.moved2 = { card: card.parentElement === rows[1].es, en: en.parentElement === rows[1].en, left: rows[0].es.html, leftNotes: rows[0].en.html };
rows[1].cls.delete('current');
placeCard(); placeNotes();
out.parked = { card: card.parentElement === park, en: en.parentElement === park, left: rows[1].es.html.includes('es-list') };
// the menu: its ticks as shown, its two choices as chosen and offered with both shown, and the book's order
// offered off it (18 October, 186)
const menuNow = () => ({ es: els['cols-show-statements'].checked, en: els['cols-show-notes'].checked,
  stacked: els['cols-stacked'].checked, side: els['cols-side'].checked, offered: !els['cols-stacked'].disabled,
  faint: els['cols-stacked'].label.cls.has('row-off'), book: !els['cols-book'].disabled });
S.layout = columnsLayout({ statements_columns: ['transcript', 'statements', 'notes'], columns_stacked: true });
S.columns = S.layout.order;
drawColsMenu();
out.menu = { stacked: menuNow() };
S.layout = columnsLayout({ columns_hidden: ['notes'], columns_stacked: true });
S.columns = S.layout.order;
drawColsMenu();
out.menu.hidden = menuNow();
S.layout = null; S.columns = null;
// a click on a statement of another passage: the move there, then the caret in that statement
const focused = [];
const pairEls = () => [0, 1, 2].map((n) => ({ dataset: { pid: `p${n}` }, querySelector: () => ({ focus: (o) => focused.push([n, o]) }) }));
const keepNote = () => {}; const current = () => S.flat[S.at]; const pairIntoView = () => {};
const goTo = (pos) => { S.at = pos; return Promise.resolve(); };
(async () => {
  await toStatement(S.flat[2], 1);
  await toStatement(S.flat[2], 0);
  out.toStatement = { at: S.at, focused, pair: S.pairFocus };
  console.log(JSON.stringify(out));
})();
""", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
        if not out:
            check("172: the columns run in node", False, (run.stderr or run.stdout).strip()[:400])
        else:
            # the six a grip's to make since 18 October (186), where the page listed them
            check("172, 18 October: in node, the six orders each a grip's to make from the book's, by a drag or two",
                  out["orders"] == sorted(["statements,transcript,notes", "statements,notes,transcript", "transcript,statements,notes",
                                           "transcript,notes,statements", "notes,statements,transcript", "notes,transcript,statements"]),
                  str(out["orders"]))
            check("172: in node, the page reads the book's order with no key, an order kept, an old place's nearest, an "
                  "odd list as the book's, and an order kept over an old place",
                  out["read"] == {"none": "statements,transcript,notes", "kept": "notes,statements,transcript",
                                  "left": "notes,transcript,statements", "odd": "statements,transcript,notes",
                                  "both": "transcript,notes,statements"}, str(out["read"]))
            v = out["vars"]
            good = all(
                [int(v[o]["--es-col"]), int(v[o]["--tx-col"]), int(v[o]["--en-col"])]
                == [o.split(",").index(c) + 1 for c in ("statements", "transcript", "notes")]
                and v[o]["--cols"] == " ".join(f"var(--{ {'statements': 'es', 'transcript': 'tx', 'notes': 'en'}[c]}-track)" for c in o.split(","))
                and [int(v[o]["--es-col2"]), int(v[o]["--tx-col2"])]
                == [[c for c in o.split(",") if c != "notes"].index(c) + 1 for c in ("statements", "transcript")]
                and sorted([int(v[o]["--es-ord"]), int(v[o]["--en-ord"])]) == [2, 3]
                and (int(v[o]["--es-ord"]) < int(v[o]["--en-ord"])) == (o.index("statements") < o.index("notes"))
                for o in v)
            check("172: in node, every order he chooses gives each column its place among three, among two with the notes "
                  "under the words, and at a phone's width the statements and the notes after the words in their order",
                  good and v["notes,transcript,statements"]["--cols"] == "var(--en-track) var(--tx-track) var(--es-track)"
                  and v["notes,transcript,statements"]["--cols2"] == "var(--tx-track) var(--es-track)", str(v.get("notes,transcript,statements")))
            check("172: in node, a drag moves a column before the heading it is let go at, or after the last on screen, the "
                  "notes out of sight keeping their place at two columns, and a let go on itself changes nothing",
                  out["moved"] == {"endOfThree": "transcript,notes,statements", "beforeTranscript": "statements,transcript,notes",
                                   "endOfTwo": "transcript,statements,notes", "onItself": "statements,transcript,notes"}, str(out["moved"]))
            check("172: in node, Alt and an arrow moves a column one place, nothing at either end, and at two columns among "
                  "those on screen",
                  out["step"] == {"right": "transcript,statements,notes", "left": "statements,notes,transcript", "edge": None,
                                  "end": None, "twoLeft": "statements,notes,transcript"}, str(out["step"]))
            one, four = out["said"]["one"], out["said"]["four"]
            check("172: in node, a passage's statements read-only, each numbered by its pair's place, a statement still to "
                  "write showing its key quote, an empty pair skipped with its number kept, escaped, and none at all for a "
                  "passage with none",
                  one == '<ol class="es-list"><li><button type="button" tabindex="-1" class="es-go" data-es="0" '
                         'title="Go to this statement"><span class="es-n" data-es-colour="0">1</span><span class="es-words">Waiting as a kind of '
                         'faith</span></button></li></ol>'
                  and re.findall(r'data-es="(\d)"', four) == ["0", "1", "3"]
                  and re.findall(r'class="es-n" data-es-colour="(\d)">(\d)<', four) == [("0", "1"), ("1", "2"), ("3", "4")]
                  and '<span class="es-quote">"b only"</span>' in four and "Four &amp; &lt;more&gt;" in four
                  and out["said"]["none"] == "", four[:200])
            check("172: in node, the card and the notes field go into the current passage's row, on to the next as it "
                  "becomes current, the row left showing its statements as saved and its notes as text, and back to the "
                  "park with no current passage",
                  out["first"] == {"card": True, "en": True, "grown": 1}
                  and out["moved2"]["card"] and out["moved2"]["en"]
                  and 'class="es-n" data-es-colour="1">2</span><span class="es-words">Saved on the way out</span>' in out["moved2"]["left"]
                  and out["moved2"]["leftNotes"] == '<div class="turn-notes-text">A first note</div>'
                  and out["parked"] == {"card": True, "en": True, "left": True}, str(out["moved2"])[:300])
            # the ticks and the choices since 18 October (186), where it drew the six orders
            check("172, 18 October: in node, Columns' menu ticks the columns shown, checks Stacked as chosen and offers it "
                  "with both shown, faint and kept with one hidden, offers the book's order off it, and its tooltip says "
                  "the columns shown",
                  out["menu"]["stacked"] == {"es": True, "en": True, "stacked": True, "side": False, "offered": True,
                                             "faint": False, "book": True}
                  and out["menu"]["hidden"] == {"es": True, "en": False, "stacked": True, "side": False, "offered": False,
                                                "faint": True, "book": False}
                  and out["words"] == {"said": "statements, transcript, notes", "shown": "statements, transcript",
                                       "alone": "transcript", "stacked": "transcript, statements over notes"},
                  str(out["menu"]) + str(out["words"]))
            check("172: in node, a click on another passage's second statement goes there and puts the caret in that "
                  "statement with no scroll of its own, and on the passage it is on goes straight to the statement",
                  out["toStatement"]["at"] == 2 and out["toStatement"]["focused"] == [[1, {"preventScroll": True}], [0, {"preventScroll": True}]]
                  and out["toStatement"]["pair"] == "p0", str(out["toStatement"]))
