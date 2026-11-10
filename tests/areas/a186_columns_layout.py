"""Area 186: the statements screen's columns shown, hidden or stacked (18 October 2026, Adam's drawing of four
layouts and one menu, "as drawn"). Columns' menu holds Show, a tick for the experiential statements and one
for the exploratory notes, the transcript always shown, Statements and notes, Side by side or Stacked, notes
under statements, offered while both are shown, and Order, Back to the book's order, where it listed the six
orders. Hidden is never deleted. Stacked puts the current passage's statements above its notes in one column
beside the transcript, each half scrolling on its own and the divider between them his to move. Every choice
is kept in config.json beside `statements_columns`, and a file with none of them reads as the three side by
side. The same day the pair's Remove on the statement card became a bin alone at its top right.

The checks hold behaviour alone, by the Checks rule of 18 October: what is saved and read back on the next
start, where the card and the notes field stand and what they keep, what a tick, a choice, a key and the
divider do. The words, the colours and the layout are in the build's review shots.

Every fixture here is invented, on a made-up topic (a beekeeper and her hives).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess

from . import support
from .support import check, skip
import idiograph_routes


def test_columns_layout(scratch):
    print("\n186. The statements screen's columns shown, hidden or stacked, 18 October, Adam's drawing: Columns' menu "
          "of Show's two ticks, Side by side or Stacked and Back to the book's order, the six orders gone from it, hidden "
          "never deleted, the notes stacked under the statements in one column beside the transcript with a divider "
          "kept where he leaves it, every choice kept beside the order and an old file read as the three side by side, "
          "today's narrow rules for whatever is shown, every tick, choice and the divider from the keyboard, and the "
          "pair's Remove a bin alone at its top right, its look in the review shots")
    import server as server_mod

    read = lambda path: path.read_text(encoding="utf-8")
    page, app = support.page_text(), support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    after = lambda src, a, b: src.split(a, 1)[1].split(b, 1)[0] if a in src and b in src.split(a, 1)[1] else ""
    node = shutil.which("node")

    def whole(name):
        """A function of app.js whole."""
        at = app.index(f"function {name}(")
        return app[at:app.index("\n}", at) + 2]

    body = lambda name: whole(name).split("{", 1)[1]
    line = lambda start: start + app.split(start, 1)[1].split("\n", 1)[0] if start in app else ""

    def run_node(name, code):
        script = scratch / name
        script.write_text(support.i18n_js() + code, encoding="utf-8")
        done = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        try:
            return json.loads(done.stdout.strip().splitlines()[-1]), done
        except (ValueError, IndexError):
            return {}, done

    # ── A. the server: the three keys beside the order, cleaned, kept, and an old file read as today
    merge = server_mod.merge_config
    hidden, split = idiograph_routes.columns_hidden, idiograph_routes.stack_split
    check("186: the server keeps the columns hidden, the stacking and the divider beside the order, none hidden, side by "
          "side and at half on a new install and as the Mac app ships, and an old file with none of them, its notes' "
          "place among them, reads as the three side by side",
          server_mod.defaults()["columns_hidden"] == [] and server_mod.defaults()["columns_stacked"] is False
          and server_mod.defaults()["stack_split"] == 0.5
          and list(server_mod.defaults()).index("statements_columns") + 1 == list(server_mod.defaults()).index("columns_hidden")
          and all(server_mod.shipped_config()[k] == v for k, v in (("columns_hidden", []), ("columns_stacked", False),
                                                                   ("stack_split", 0.5)))
          and {k: merge({})[k] for k in ("columns_hidden", "columns_stacked", "stack_split")}
          == {"columns_hidden": [], "columns_stacked": False, "stack_split": 0.5}
          and {k: merge({"notes_place": "under", "interviewer": "Wren"})[k]
               for k in ("statements_columns", "columns_hidden", "columns_stacked", "stack_split")}
          == {"statements_columns": ["transcript", "statements", "notes"], "columns_hidden": [], "columns_stacked": False,
              "stack_split": 0.5})
    check("186: a list of hidden columns is the statements, the notes or both, each once in the book's order, never the "
          "transcript, and the divider a share between a fifth and four fifths to a thousandth, anything else refused",
          hidden(["notes"]) == ["notes"] and hidden(["notes", "statements", "notes"]) == ["statements", "notes"]
          and hidden([]) == [] and hidden(["transcript"]) is None and hidden(["notes", "transcript"]) is None
          and hidden("notes") is None and hidden([1]) is None and hidden(None) is None
          and split(0.5) == 0.5 and split(0.1) == 0.2 and split(0.95) == 0.8 and split(1 / 3) == 0.333 and split(0.4) == 0.4
          and split(True) is None and split("0.5") is None and split(float("nan")) is None and split(None) is None
          and merge({"columns_hidden": ["transcript"], "columns_stacked": "yes", "stack_split": 3})["columns_hidden"] == []
          and merge({"columns_stacked": "yes"})["columns_stacked"] is False and merge({"stack_split": 3})["stack_split"] == 0.8
          and merge({"stack_split": "x"})["stack_split"] == 0.5)
    saved = server_mod.CONFIG_PATH
    server_mod.CONFIG_PATH = scratch / "columns-186-config.json"
    try:
        server_mod.CONFIG_PATH.write_text(json.dumps({"interviewer": "Wren", "minimap": "on",
                                                      "statements_columns": ["notes", "statements", "transcript"]}),
                                          encoding="utf-8")
        before = server_mod.config()
        one = server_mod.api_settings({"columns_hidden": ["notes"]})["config"]
        two = server_mod.api_settings({"columns_stacked": True, "stack_split": 0.35})["config"]
        odd = server_mod.api_settings({"columns_hidden": ["transcript"], "columns_stacked": "on", "stack_split": "half"})["config"]
        back = server_mod.api_settings({"columns_hidden": []})["config"]
        disk = json.loads(server_mod.CONFIG_PATH.read_text(encoding="utf-8"))
        again = server_mod.config()
    finally:
        server_mod.CONFIG_PATH = saved
    check("186: a file with none of the keys opens as the three side by side, a column hidden, the stacking and the "
          "divider are written and read back on the next start, a value that is none of them leaves the file as it was, "
          "showing the column again keeps the rest, and every other key and the order stay",
          (before["columns_hidden"], before["columns_stacked"], before["stack_split"]) == ([], False, 0.5)
          and one["columns_hidden"] == ["notes"] and two["columns_stacked"] is True and two["stack_split"] == 0.35
          and (odd["columns_hidden"], odd["columns_stacked"], odd["stack_split"]) == (["notes"], True, 0.35)
          and back["columns_hidden"] == [] and back["columns_stacked"] is True
          and (disk["columns_hidden"], disk["columns_stacked"], disk["stack_split"]) == ([], True, 0.35)
          and (again["columns_hidden"], again["columns_stacked"], again["stack_split"]) == ([], True, 0.35)
          and disk["statements_columns"] == ["notes", "statements", "transcript"]
          and disk["interviewer"] == "Wren" and disk["minimap"] == "on", str(disk))

    # ── B. the six orders gone from the menu and from Settings, the order a grip's to make
    check("186: the six orders are gone from Columns' menu and from Settings, each order a grip's to make, and a change "
          "in the menu or Settings' ticks reaches the page's handlers",
          "COLUMN_ORDERS" not in app and 'name="view-columns"' not in app + page and 'id="cols-rows"' not in page
          and 'id="set-columns"' not in page
          and "$('view-set').addEventListener('change', () => colsSetTicked());" in app)

    # ── D. the page's functions in node: the layouts read, the places, the card and the field, the menu and its keys,
    # the divider, the book's order, Settings
    if not node:
        skip("186: the layouts in node", "node is not on this machine")
    else:
        pure = "\n".join([line("const COLUMNS = "), line("const COLUMN_WORDS = "), line("const COLUMN_KEYS = "),
                          app[app.index("const NOTES_PLACE_COLUMNS = {"):app.index("};", app.index("const NOTES_PLACE_COLUMNS = {")) + 2],
                          line("const isColumns = "), line("const columnsSaid = "), line("const HIDEABLE_COLUMNS = "),
                          line("const STACK_SPLIT = "), line("const STACK_RANGE = "), line("const colsHidden = "),
                          line("const colsNarrow = "), line("const stackedNow = "), line("const colsTicked = "),
                          line("const STACK_STEP = "), line("const stackClamp = ")]
                         + [whole(n) for n in ("columnsOf", "columnsHiddenOf", "stackSplitOf", "columnsLayout",
                                                "columnsShownSaid", "colsVars", "statementsHtml", "notesHtml", "placeCard",
                                                "cardCell", "notesCell", "parkCard", "placeNotes", "parkNotes", "cellsAgain",
                                                "drawStack", "colsStackRows", "drawColsMenu", "colsMenuKeys", "colsBookOrder",
                                                "stackSplitKeep", "stackDividerKeys", "fillColumnsSet", "colsSetTicked")])
        code = r"""
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const rowPairs = (row) => (row.pairs || []).map((p) => ({ es: p.es || '', kq: p.kq || '' }));
const MOD = (e) => !!(e.metaKey || e.ctrlKey);
let NARROW = false;
const matchMedia = (q) => ({ matches: q === '(max-width: 800px)' ? NARROW : false });
// a few elements, enough for the card and the notes field to move between the rows, the stack and the park
const mk = (cls, extra = {}) => Object.assign({ cls: new Set(cls.split(' ').filter(Boolean)), children: [], parentElement: null,
  html: '', dataset: {}, id: '', style: { props: {}, setProperty(k, v) { this.props[k] = v; } }, attrs: {},
  setAttribute(k, v) { this.attrs[k] = String(v); },
  appendChild(c) { if (c.parentElement) c.parentElement.children.splice(c.parentElement.children.indexOf(c), 1); c.parentElement = this; this.children.push(c); return c; },
  prepend(c) { if (c.parentElement) c.parentElement.children.splice(c.parentElement.children.indexOf(c), 1); c.parentElement = this; this.children.unshift(c); return c; },
  replaceChildren(...cs) { for (const k of this.children) k.parentElement = null; this.children = []; this.html = ''; cs.forEach((c) => this.appendChild(c)); },
  set innerHTML(h) { for (const k of this.children) k.parentElement = null; this.children = []; this.html = h; }, get innerHTML() { return this.html; },
  contains(x) { let e = x; while (e) { if (e === this) return true; e = e.parentElement; } return false; },
  closest(sel) { for (const one of sel.split(',').map((s) => s.trim().slice(1))) { let e = this; while (e) { if (e.cls.has(one)) return e; e = e.parentElement; } } return null; },
  querySelector(sel) { const c = sel.slice(1).split(':')[0]; const walk = (e) => { for (const k of e.children) { if (k.cls.has(c) && !(sel.includes(':not(.note-cell)') && k.cls.has('note-cell'))) return k; const f = walk(k); if (f) return f; } return null; }; return walk(this); } }, extra);
const park = mk('es-park'); const card = mk('es-card'); const en = mk(''); park.appendChild(card); park.appendChild(en);
// the card holds what was written, which never moves with it
card.appendChild(mk('pairs')).html = 'Waiting at the hive as a kind of faith';
en.value = 'She slows her voice when the bees come up';
const stackEs = mk('stack-half stack-es'); stackEs.id = 'stack-es'; const stackEn = mk('stack-cell'); stackEn.id = 'stack-en-cell';
const rows = [0, 1, 2].map((i) => { const r = mk('turn'); r.dataset.i = String(i); r.es = r.appendChild(mk('turn-es')); r.en = r.appendChild(mk('turn-notes')); return r; });
const els = { 'es-park': park, 'es-card': card, en, 'stack-es': stackEs, 'stack-en-cell': stackEn, stack: mk('stack'), 'stack-divider': mk(''),
  'transcript-rows': { querySelector: (sel) => { const r = rows.find((x) => x.cls.has('current'));
    return !r ? null : sel === '.turn.current .turn-es' ? r.es : sel === '.turn.current .turn-notes' ? r.en : null; },
    querySelectorAll: () => rows } };
// Columns' menu and Settings' view, each input in its label
const input = (type) => { const label = { cls: new Set(), classList: { toggle(c, on) { if (on) label.cls.add(c); else label.cls.delete(c); } } };
  return { type, checked: false, disabled: false, label, closest: () => label, focus() { document.activeElement = this; } }; };
for (const id of ['cols-show-statements', 'cols-show-notes', 'set-show-statements', 'set-show-notes']) els[id] = input('checkbox');
for (const id of ['cols-side', 'cols-stacked', 'set-side', 'set-stacked']) els[id] = input('radio');
els['cols-book'] = { type: 'button', disabled: false, focus() { document.activeElement = this; } };
els['cols-pick'] = { focus() { document.activeElement = this; } };
els['cols-menu'] = { hidden: false, querySelectorAll: (sel) => {
  const all = [els['cols-show-statements'], els['cols-show-notes'], els['cols-side'], els['cols-stacked'], els['cols-book']];
  if (sel === 'input[type="radio"]:not(:disabled)') return all.filter((x) => x.type === 'radio' && !x.disabled);
  return all; } };
const document = { activeElement: null };
const $ = (id) => els[id];
let grown = 0; const growPairs = () => { grown += 1; }; const growNotes = () => {}; const footStuck = () => {};
const sent = []; const setView = (k, v) => { sent.push([k, v]); };
let menuOpen = true; const colsMenu = (open) => { menuOpen = !!open; };
const S = { flat: [
  { i: 0, stop: true, en: 'A note on the smoke', pairs: [{ es: 'The smoke as a calming hand', kq: '"it settles them"' }] },
  { i: 1, stop: true, en: '', pairs: [{ es: 'Stings as the price of closeness', kq: '' }] },
  { i: 2, stop: true, en: 'Later', pairs: [] }], columns: null, layout: null, data: { config: { stack_split: 0.5 } } };
""" + pure + r"""
const out = {};
const where = () => ({ card: card.parentElement === park ? 'park' : card.parentElement === stackEs ? 'stack' : card.parentElement === rows[0].es ? 'row' : '?',
  en: en.parentElement === park ? 'park' : en.parentElement === stackEn ? 'stack' : en.parentElement === rows[0].en ? 'row' : '?' });
const as = (cfg) => { S.layout = columnsLayout(cfg); S.columns = S.layout.order; cellsAgain(); placeCard(); placeNotes(); return where(); };
// the layouts read as the server reads them
out.read = {
  none: columnsLayout(null), old: columnsLayout({ notes_place: 'under' }),
  odd: columnsLayout({ columns_hidden: ['transcript'], columns_stacked: 'yes', stack_split: 7 }),
  both: columnsLayout({ columns_hidden: ['notes', 'statements'] }),
  stackedHidden: columnsLayout({ columns_hidden: ['notes'], columns_stacked: true }),
  stacked: columnsLayout({ columns_stacked: true, stack_split: 0.35 }) };
// the places with columns hidden
out.vars = {
  notes: colsVars(COLUMNS, ['notes']), statements: colsVars(['notes', 'transcript', 'statements'], ['statements']),
  both: colsVars(COLUMNS, ['statements', 'notes']), none: colsVars(['transcript', 'statements', 'notes']) };
out.said = { three: columnsShownSaid(columnsLayout({})), notes: columnsShownSaid(columnsLayout({ columns_hidden: ['notes'] })),
  stacked: columnsShownSaid(columnsLayout({ columns_stacked: true })) };
// the card and the field through the layouts, the words they hold kept
rows[0].cls.add('current');
out.place = {
  three: as({}), esHidden: as({ columns_hidden: ['statements'] }), enHidden: as({ columns_hidden: ['notes'] }),
  both: as({ columns_hidden: ['statements', 'notes'] }), stacked: as({ columns_stacked: true }) };
NARROW = true; out.place.stackedNarrow = as({ columns_stacked: true }); NARROW = false;
out.place.stackedWide = as({ columns_stacked: true });
// saved while it stood in the stack, then back beside the words: every row drawn again from what is saved
S.flat[1].pairs = [{ es: 'Stings as the price of closeness', kq: '' }, { es: 'Saved while stacked', kq: '' }];
S.flat[2].en = 'Written while stacked';
out.place.back = as({});
out.cells = { one: rows[1].es.html, twoNotes: rows[2].en.html, kept: card.children.length === 1 && card.children[0].html, en: en.value };
// the menu as the layout stands
const menuNow = () => ({ es: els['cols-show-statements'].checked, en: els['cols-show-notes'].checked,
  stacked: els['cols-stacked'].checked, offered: !els['cols-stacked'].disabled, faint: els['cols-stacked'].label.cls.has('row-off'),
  book: !els['cols-book'].disabled });
S.layout = columnsLayout({ columns_stacked: true }); S.columns = S.layout.order; drawColsMenu(); out.menuStacked = menuNow();
S.layout = columnsLayout({ columns_hidden: ['statements'], statements_columns: ['transcript', 'notes', 'statements'] }); S.columns = S.layout.order;
drawColsMenu(); out.menuHidden = menuNow();
out.ticked = { none: colsTicked(input('checkbox'), input('checkbox')),
  notes: colsTicked(Object.assign(input('checkbox'), { checked: true }), input('checkbox')) };
// Tab keeps to the menu: the two ticks, the one choice checked, and the action while it is offered
const tab = (shift) => { const e = { key: 'Tab', shiftKey: shift, prevented: false, preventDefault() { this.prevented = true; }, stopPropagation() {} };
  colsMenuKeys(e); return e.prevented; };
const name = () => Object.keys(els).find((k) => els[k] === document.activeElement);
document.activeElement = els['cols-show-statements'];
const walk = [];
for (let k = 0; k < 4; k += 1) { tab(false); walk.push(name()); }
document.activeElement = els['cols-show-statements']; tab(true); walk.push(name());
out.tabHidden = walk;
S.layout = columnsLayout({ columns_stacked: true }); S.columns = S.layout.order; drawColsMenu();
document.activeElement = els['cols-show-notes']; tab(false); out.tabStacked = [name()]; tab(false); out.tabStacked.push(name());
out.otherKey = (() => { const e = { key: 'a', prevented: false, preventDefault() { this.prevented = true; } }; colsMenuKeys(e); return e.prevented; })();
// Back to the book's order: the menu closed, the focus on Columns, the order the book's, and nothing sent on it
S.columns = ['transcript', 'notes', 'statements']; menuOpen = true; sent.length = 0;
colsBookOrder(); out.book = { open: menuOpen, focus: name(), sent: sent.slice() };
S.columns = COLUMNS.slice(); sent.length = 0; colsBookOrder(); out.bookSame = sent.slice();
// the divider: the arrows a twentieth at a time, Home and End to either end, each kept, and the place drawn
const key = (k, extra = {}) => { const e = Object.assign({ key: k, prevented: false, preventDefault() { this.prevented = true; }, stopPropagation() {} }, extra);
  stackDividerKeys(e); return e.prevented; };
S.layout = columnsLayout({ columns_stacked: true }); sent.length = 0;
out.divider = { up: [key('ArrowUp'), S.layout.split], up2: [key('ArrowUp'), S.layout.split], end: [key('End'), S.layout.split],
  down: [key('ArrowDown'), S.layout.split], home: [key('Home'), S.layout.split], left: key('ArrowLeft'), mod: key('ArrowUp', { metaKey: true }),
  vars: [els.stack.style.props['--stack-a'], els.stack.style.props['--stack-b'], els['stack-divider'].attrs['aria-valuenow']] };
out.divider.sent = sent.map((s) => s[1]);
S.data.config.stack_split = 0.2; sent.length = 0; stackSplitKeep(0.05); out.divider.same = sent.slice();
// Settings' view: read from the layout, Stacked offered as the ticks change
fillColumnsSet(columnsLayout({ columns_hidden: ['notes'], columns_stacked: true }));
out.settings = { es: els['set-show-statements'].checked, en: els['set-show-notes'].checked, stacked: els['set-stacked'].checked,
  offered: !els['set-stacked'].disabled };
els['set-show-notes'].checked = true; colsSetTicked(); out.settings.again = { stacked: els['set-stacked'].checked, offered: !els['set-stacked'].disabled };
console.log(JSON.stringify(out));
"""
        o, done = run_node("columns-186.js", code)
        if not o:
            check("186: the layouts run in node", False, (done.stderr or done.stdout).strip()[:500])
        else:
            r = o["read"]
            check("186: in node, the page reads the layouts as the server does: none hidden and side by side with no keys "
                  "or an old notes' place, anything odd as none, both hidden, Stacked holding only while both are shown, "
                  "the choice kept, and the divider kept to its range",
                  r["none"] == {"order": ["statements", "transcript", "notes"], "hidden": [], "chose": False, "stacked": False, "split": 0.5,
                                 "top": "statements"}
                  and r["old"]["order"] == ["transcript", "statements", "notes"] and r["old"]["hidden"] == [] and not r["old"]["stacked"]
                  and r["odd"] == {"order": ["statements", "transcript", "notes"], "hidden": [], "chose": False, "stacked": False, "split": 0.8,
                                "top": "statements"}
                  and r["both"]["hidden"] == ["statements", "notes"]
                  and r["stackedHidden"]["chose"] is True and r["stackedHidden"]["stacked"] is False
                  and r["stacked"]["stacked"] is True and r["stacked"]["split"] == 0.35, str(r)[:400])
            v = o["vars"]
            check("186: in node, a hidden column takes no track and stands at the first place, the others' places among "
                  "those shown, the transcript alone one track, and the stacked column's track in the statements' place",
                  v["notes"]["--cols"] == "var(--es-track) var(--tx-track)" and v["notes"]["--en-col"] == "1"
                  and (v["notes"]["--es-col"], v["notes"]["--tx-col"]) == ("1", "2")
                  and v["statements"]["--cols"] == "var(--en-track) var(--tx-track)"
                  and (v["statements"]["--en-col"], v["statements"]["--tx-col"], v["statements"]["--es-col"]) == ("1", "2", "1")
                  and v["statements"]["--cols2"] == "var(--tx-track)"
                  and v["both"]["--cols"] == "var(--tx-track)" and v["both"]["--tx-col"] == "1"
                  and v["notes"]["--stk-cols"] == "var(--st-track) var(--tx-track)"
                  and v["none"]["--stk-cols"] == "var(--tx-track) var(--st-track)"
                  and v["none"]["--cols"] == "var(--tx-track) var(--es-track) var(--en-track)", str(v)[:400])
            p = o["place"]
            check("186: in node, the card and the notes field stand in the current passage's row side by side, in the park "
                  "with their column hidden, in the stacked column's halves while stacked above 800px, back beside the "
                  "words at 800px and below, and back in the row once side by side again",
                  p["three"] == {"card": "row", "en": "row"} and p["esHidden"] == {"card": "park", "en": "row"}
                  and p["enHidden"] == {"card": "row", "en": "park"} and p["both"] == {"card": "park", "en": "park"}
                  and p["stacked"] == {"card": "stack", "en": "stack"} and p["stackedNarrow"] == {"card": "row", "en": "row"}
                  and p["stackedWide"] == {"card": "stack", "en": "stack"} and p["back"] == {"card": "row", "en": "row"}, str(p))
            c = o["cells"]
            check("186: in node, hiding and showing keeps the words: the card and the field carry what was written through "
                  "every layout, and a passage saved while the card stood in the stack shows its statements and notes as "
                  "saved once beside the words again",
                  c["kept"] == "Waiting at the hive as a kind of faith" and c["en"] == "She slows her voice when the bees come up"
                  # the number carries its statement's colour since 18 October (187), so any attributes on it
                  and re.search(r'class="es-n"[^>]*>2</span><span class="es-words">Saved while stacked</span>', c["one"])
                  and c["twoNotes"] == '<div class="turn-notes-text">Written while stacked</div>', str(c)[:300])
            check("186: in node, the menu ticks the columns shown, checks Stacked as chosen and offers it with both shown, "
                  "faint and not offered with one hidden, offers the book's order off it, and the ticks give the columns "
                  "hidden",
                  o["menuStacked"] == {"es": True, "en": True, "stacked": True, "offered": True, "faint": False, "book": False}
                  and o["menuHidden"] == {"es": False, "en": True, "stacked": False, "offered": False, "faint": True, "book": True}
                  and o["ticked"] == {"none": ["statements", "notes"], "notes": ["notes"]},
                  str(o["menuStacked"]) + str(o["menuHidden"]))
            check("186: in node, Tab keeps to the menu round the two ticks, the one checked choice and the action, passing "
                  "what is not offered, Shift + Tab back, and other keys left alone",
                  o["tabHidden"] == ["cols-show-notes", "cols-book", "cols-show-statements", "cols-show-notes", "cols-book"]
                  and o["tabStacked"] == ["cols-stacked", "cols-show-statements"] and o["otherKey"] is False,
                  str(o["tabHidden"]) + str(o["tabStacked"]))
            check("186: in node, Back to the book's order closes the menu, puts the focus on Columns and keeps the book's "
                  "order, sending nothing while it is the book's already",
                  o["book"] == {"open": False, "focus": "cols-pick", "sent": [["statements_columns", ["statements", "transcript", "notes"]]]}
                  and o["bookSame"] == [], str(o["book"]))
            d = o["divider"]
            check("186: in node, the divider moves a twentieth on the up and down arrows, to either end on Home and End, "
                  "each kept and drawn as the halves' shares and its value, the left arrow and a modifier left to the page, "
                  "and a place already kept sent again never",
                  d["up"] == [True, 0.45] and d["up2"] == [True, 0.4] and d["end"] == [True, 0.8] and d["down"] == [True, 0.8]
                  and d["home"] == [True, 0.2] and d["left"] is False and d["mod"] is False
                  and d["vars"] == ["200fr", "800fr", "20"] and d["sent"] == [0.45, 0.4, 0.8, 0.8, 0.2] and d["same"] == [], str(d))
            check("186: in node, Settings' View reads the columns shown and the stacking, Stacked not offered while a tick is "
                  "off and offered again as it is ticked, the choice kept",
                  o["settings"] == {"es": True, "en": False, "stacked": True, "offered": False, "again": {"stacked": True, "offered": True}},
                  str(o["settings"]))

    # ── E. the wiring and the keyboard
    check("186: the menu's ticks and choices are kept as they change, the menu placed again under Columns and staying "
          "open, a press on Columns from the keyboard puts the focus on its first tick, and Back to the book's order "
          "and the menu's keys are wired",
          "$('cols-pick').onclick = (e) => colsMenu($('cols-menu').hidden, e.detail === 0);" in app
          and "if (keys) $('cols-show-statements').focus();" in body("colsMenu")
          and "if (t.type === 'checkbox') setView('columns_hidden', colsTicked($('cols-show-statements'), $('cols-show-notes')));" in app
          and "else if (t.name === 'cols-stack' && t.checked) setView('columns_stacked', t.value === 'stacked');" in app
          and "$('cols-menu').addEventListener('keydown', colsMenuKeys);" in app and "$('cols-book').onclick = () => colsBookOrder();" in app
          and "if (!$('cols-menu').hidden) { e.preventDefault(); colsMenu(false); $('cols-pick').focus(); return true; }" in app)
    check("186: the divider follows a drag and keeps its place on the let go, takes its keys, goes back to half on a double "
          "click, and the card's foot in its half keeps to the half's foot as it scrolls",
          "$('stack-divider').addEventListener('pointerdown', stackDividerDown);" in app
          and "$('stack-divider').addEventListener('keydown', stackDividerKeys);" in app
          and "$('stack-divider').ondblclick = () => stackSplitKeep(STACK_SPLIT);" in app
          and 'role="separator" tabindex="0"' in page
          and "stackSplitKeep(ev.type === 'pointerup' ? split : (S.layout ? S.layout.split : STACK_SPLIT));" in body("stackDividerDown")
          and "drawStack(split);" in body("stackDividerDown")
          and "$('stack-es').addEventListener('scroll', footStuck, { passive: true });" in app
          and "card.closest('.turn-es, .stack-es')" in body("footStuck"))
    tab = after(app, "const onBin = ", "\n      return;\n    }")
    check("186: Tab in the card runs a statement, its key quote and its bin, then the notes, each only while its column "
          "is shown, the bin itself in the order, and with the statements hidden the caret goes into the notes",
          "document.activeElement.closest('.pair-remove')" in tab
          and "if (e.key === 'Tab' && (typing || onBin) && !$('work').hidden) {" in tab
          and "[...$('pairs').querySelectorAll('.pair-es, .pair-kq, .pair-remove'),\n"
          "      ...($('cx-list') ? $('cx-list').querySelectorAll('.cx-field') : []), $('en')]" in tab
          and ".filter((el) => el.getClientRects().length);" in tab
          and "else if (colsHidden('statements') && !colsHidden('notes')) $('en').focus({ preventScroll: true });" in body("focusEntry"), tab[:200])
    check("186: across 800px the card and the field go where today's rules put them, every row drawn again first, and the "
          "screen drawn again on a choice redraws the rows' cells before placing the card",
          "matchMedia('(max-width: 800px)').addEventListener('change', () => {" in app
          and body("drawView").index("cellsAgain();") < body("drawView").index("placeCard();")
          and "if (field.closest('#stack')) { field.style.height = ''; return; }" in body("growNotes"))
