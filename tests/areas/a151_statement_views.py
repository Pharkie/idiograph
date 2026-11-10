from __future__ import annotations

import inspect
import json
import shutil
from pathlib import Path

from . import support
from .support import check, skip
import idiograph_routes
import statement_prompts


def test_statement_views(scratch):
    print("\n151. The statements screen's view, 16 October, Adam's word from a tester's feedback: the exploratory notes "
          "right or left of each passage in the transcript column, as the IPA book lays them out, or under the "
          "statements, and the current passage larger or at the size of the rest, both in a View menu on the bar and "
          "in Settings, not hidden there, with the AI prompts saying passage and the bar's last leftovers. Since the "
          "test review of 18 October the menu's and Settings' markup, the grid, the band, the prompts' words and the docs "
          "are review shots, and the keys saved and read back, the menus, Settings' Save, the notes field's commit and "
          "the old routes stay")
    import subprocess
    import server as server_mod
    import ai_suggest as ai_mod

    read = lambda path: Path(path).read_text(encoding="utf-8")
    page, app = support.page_text(), support.text("family/static/shell.js", "apps/idiograph/static/distil.js")

    def whole(name):
        """A function of app.js whole, a one-line one included."""
        at = app.index(f"function {name}(")
        if app[max(0, at - 6):at] == "async ":
            at -= 6
        line = app[at:app.index("\n", at)]
        if line.rstrip().endswith("}") and line.count("{") == line.count("}"):
            return line
        return app[at:app.index("\n}", at) + 2]

    body = lambda name: whole(name).split("{", 1)[1]

    # the family's Settings asks Idiograph's part through its hooks since the fifth build (23 October 2026): the
    # card's opening and its Save read with the hooks they ask, in the order they ask them
    HOOKED = {"openSettings": ("openSettings", "distilSettingsOpen"),
              "saveSettings": ("saveSettings", "distilSettingsBody",
                               "distilSettingsSaved", "distilSettingsAfter")}
    body = (lambda one: lambda name: "\n".join(one(n) for n in HOOKED.get(name, (name,))))(body)
    const = lambda name: next(ln for ln in app.splitlines() if ln.startswith(f"const {name} = "))

    # ── A. the keys: their defaults, an absent or unknown key read as the default, saved and read back. Since 17
    # October (172) the three columns' order, `statements_columns`, in the place of the notes' place, `notes_place`,
    # which an old file reads as the order nearest the screen it drew
    check("151: statements_columns is the book's order and larger_passage on in the server's defaults and the Mac "
          "app's shipped settings, COLUMNS holds the three in the book's order, and the notes' place is no key now",
          server_mod.defaults().get("statements_columns") == ["statements", "transcript", "notes"]
          and server_mod.defaults().get("larger_passage") is True
          and server_mod.shipped_config()["statements_columns"] == ["statements", "transcript", "notes"]
          and server_mod.shipped_config()["larger_passage"] is True
          and idiograph_routes.COLUMNS == ("statements", "transcript", "notes")
          and idiograph_routes.NOTES_PLACES == ("right", "left", "under")
          and "notes_place" not in server_mod.defaults() and "notes_beside" not in server_mod.defaults())
    merge = server_mod.merge_config
    check("151: a settings file without the keys reads the book's order and on, one with them keeps them, an old notes' "
          "place reads the order nearest it, right and left the panel's at the right, under it beside the transcript, "
          "and an order the screen does not know reads the book's",
          merge({"interviewer": "Adam"})["statements_columns"] == ["statements", "transcript", "notes"]
          and merge({"interviewer": "Adam"})["larger_passage"] is True
          and merge({"statements_columns": ["notes", "transcript", "statements"], "larger_passage": False})["statements_columns"]
          == ["notes", "transcript", "statements"]
          and merge({"statements_columns": ["notes", "transcript", "statements"], "larger_passage": False})["larger_passage"] is False
          and merge({"notes_place": "right"})["statements_columns"] == ["transcript", "notes", "statements"]
          and merge({"notes_place": "left"})["statements_columns"] == ["notes", "transcript", "statements"]
          and merge({"notes_place": "under"})["statements_columns"] == ["transcript", "statements", "notes"]
          and merge({"notes_place": "middle"})["statements_columns"] == ["statements", "transcript", "notes"]
          and merge({"statements_columns": ["notes", "notes", "statements"]})["statements_columns"] == ["statements", "transcript", "notes"]
          and merge({"statements_columns": "notes"})["statements_columns"] == ["statements", "transcript", "notes"]
          and "notes_place" not in merge({"notes_place": "left"}))
    saved = server_mod.CONFIG_PATH
    server_mod.CONFIG_PATH = scratch / "views-151-config.json"
    try:
        server_mod.CONFIG_PATH.write_text(json.dumps({"interviewer": "Wren", "round_minutes": 12, "notes_place": "left"}),
                                          encoding="utf-8")
        before = server_mod.config()
        left = server_mod.api_settings({"statements_columns": ["transcript", "statements", "notes"]})["config"]
        left_disk = json.loads(server_mod.CONFIG_PATH.read_text(encoding="utf-8"))
        off = server_mod.api_settings({"larger_passage": False})["config"]
        kept = server_mod.api_settings({"interviewer": "Wren"})["config"]
        odd = server_mod.api_settings({"statements_columns": ["sideways"]})["config"]
        old = server_mod.api_settings({"notes_place": "under", "larger_passage": True})["config"]
        disk = json.loads(server_mod.CONFIG_PATH.read_text(encoding="utf-8"))
        back = server_mod.config()
    finally:
        server_mod.CONFIG_PATH = saved
    ts = ["transcript", "statements", "notes"]
    check("151: a save writes each key as sent, the menus' one key alone keeping every other, an order it does not know "
          "and an old page's notes' place leaving the file as it was, the old key leaving the file, and the file reads "
          "back the same",
          before["statements_columns"] == ["notes", "transcript", "statements"] and before["larger_passage"] is True
          and left["statements_columns"] == ts and left_disk["statements_columns"] == ts and left_disk["round_minutes"] == 12
          and left_disk["interviewer"] == "Wren" and "notes_place" not in left_disk
          and off["larger_passage"] is False and off["statements_columns"] == ts
          and kept["statements_columns"] == ts and kept["larger_passage"] is False
          and odd["statements_columns"] == ts
          and old["statements_columns"] == ts and old["larger_passage"] is True
          and disk["statements_columns"] == ts and disk["larger_passage"] is True and disk["round_minutes"] == 12
          and "notes_place" not in disk and back["statements_columns"] == ts and back["larger_passage"] is True,
          f"{left_disk.get('statements_columns')} {off.get('larger_passage')} {odd.get('statements_columns')} {disk.get('statements_columns')}")

    # ── C. the menu, Columns and Settings kept in step: the page's own functions, in node
    check("151: the menu opens and shuts from its button, a choice sends its one key, Esc and a press elsewhere shut it, "
          "Columns the same, and a case opening shuts both and draws the view",
          "const open = $('view-menu').hidden;\n    viewMenu(open);" in app
          and "if (e.target.id === 'view-larger') setView('larger_passage', $('view-larger').checked);" in app
          and "if (!$('view-menu').hidden && !e.target.closest('#view-menu, #btn-view')) viewMenu(false);" in app
          and "if (!$('view-menu').hidden) { e.preventDefault(); viewMenu(false); $('btn-view').focus(); return true; }" in app
          # Columns' ticks and choices since 18 October (186), where its six orders stood, and a press from the keyboard
          # taking the focus into it
          and "$('cols-pick').onclick = (e) => colsMenu($('cols-menu').hidden, e.detail === 0);" in app
          and "if (t.type === 'checkbox') setView('columns_hidden', colsTicked($('cols-show-statements'), $('cols-show-notes')));" in app
          and "else if (t.name === 'cols-stack' && t.checked) setView('columns_stacked', t.value === 'stacked');" in app
          and "name === 'view-columns'" not in app
          and "if (!$('cols-menu').hidden && !e.target.closest('#cols-menu, #cols-pick')) colsMenu(false);" in app
          and "if (!$('cols-menu').hidden) { e.preventDefault(); colsMenu(false); $('cols-pick').focus(); return true; }" in app
          and body("startCase").index("viewMenu(false);") < body("startCase").index("colsMenu(false);")
          < body("startCase").index("drawView();") < body("startCase").index("drawTurn("))
    check("151: Settings opens on the view the settings hold and Save sends a key only once it has moved since the card "
          "opened, the columns' order compared as it is written, then draws the screen and centres the passage",
          "fillColumnsSet(columnsLayout(c));" in body("openSettings")
          and "$('set-larger').checked = largerPassage(c);" in body("openSettings")
          and "S.viewOpened = viewChoice();" in body("openSettings")
          and "for (const key of Object.keys(view)) if (!S.viewOpened || said(view[key]) !== said(S.viewOpened[key])) body[key] = view[key];"
              in body("saveSettings")
          and body("saveSettings").index("S.data.config = data.config;") < body("saveSettings").index("drawView();")
          and "if (!ctx.themes && current()) centreCurrent(false);" in body("saveSettings"))
    node = shutil.which("node")
    if not node:
        skip("151: the view's functions in node", "node is not installed")
    else:
        # the minimap joined the view on 16 October (154), a choice of three since 17 October, later (169), so its
        # reading goes in and its drawing is left to areas 154 and 169, and the columns' drawing to area 172
        # and since 18 October (186) the columns shown and the stacking, which Settings reads and writes too
        names = ["columnsOf", "largerPassage", "minimapMode", "notesHtml", "statementsHtml", "colsVars", "drawView",
                 "viewMenu", "drawViewMenu", "setView", "turnHtml", "fillColumnsSet", "columnsHiddenOf", "stackSplitOf",
                 "columnsLayout", "colsStackRows", "stackedWords"]
        view_choice = app[app.index("const viewChoice = "):app.index("\n});", app.index("const viewChoice = ")) + 4]
        source = "\n".join([const("COLUMNS"), const("COLUMN_KEYS"), const("isColumns"), const("columnsSaid"),
                            const("HIDEABLE_COLUMNS"), const("STACK_SPLIT"), const("STACK_RANGE"), const("colsTicked"),
                            const("MINIMAP_MODES"), const("viewConfig"), view_choice]
                           + [app[app.index("const NOTES_PLACE_COLUMNS = "):app.index("};", app.index("const NOTES_PLACE_COLUMNS = ")) + 2]]
                           + [whole(n) for n in names])
        script = scratch / "views-151.js"
        script.write_text(support.i18n_js() + r"""
const els = {};
const cls = () => ({ on: new Set(), toggle(c, v) { if (v === undefined) v = !this.on.has(c); if (v) this.on.add(c); else this.on.delete(c); return v; },
  contains(c) { return this.on.has(c); } });
const mk = (id) => ({ id, checked: false, hidden: false, disabled: false, value: '', style: {}, classList: cls(), attrs: {}, innerHTML: '', options: [],
  setAttribute(k, v) { this.attrs[k] = v; }, getBoundingClientRect: () => ({ right: 900, bottom: 40 }), offsetWidth: 200,
  label: { classList: cls() }, closest() { return this.label; } });
const $ = (id) => els[id] || (els[id] = mk(id));
const window = { innerWidth: 1280 };
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const rowHtml = (row) => esc(row.text); const timeHtml = (row) => `<t>${row.time}</t>`; const noteMarkHtml = () => '';
const rowPairs = (row) => (row.pairs || []).map((p) => ({ es: p.es || '', kq: p.kq || '' }));
const sent = []; let answer = null;
const api = async (path, body) => { sent.push([path, body]); return answer || { config: Object.assign({}, S.data.config, body) }; };
const said = []; const say = (t) => said.push(t); const RESTART_LINE = 'Restart the server to finish this update.';
const needsRestart = () => false; const current = () => null; const centreCurrent = () => {};
const scheduleMinimap = () => {};
let placed = 0; const drawn = [];
const drawColumns = (lay) => { drawn.push(lay.order.join(',')); S.columns = lay.order; S.layout = lay; };
const cellsAgain = () => {};
const placeCard = () => { placed += 1; }; const placeNotes = () => { placed += 1; };
const S = { data: null, libConfig: null, flat: [] };
""" + source + r"""
const out = {};
(async () => {
  $('work').hidden = false;
  const draw = (cfg) => { S.data = { config: cfg }; drawView();
    return { order: drawn[drawn.length - 1], same: $('work').classList.contains('same-size'), larger: $('view-larger').checked }; };
  out.absent = draw({});
  out.left = draw({ notes_place: 'left', larger_passage: false });
  out.under = draw({ notes_place: 'under' });
  out.odd = draw({ notes_place: 'diagonal' });
  out.chosen = draw({ notes_place: 'left', statements_columns: ['transcript', 'statements', 'notes'] });
  out.placed = placed;
  // a choice of order: drawn at once, the one key sent, the settings' copy of the page in step
  S.data = { config: { statements_columns: COLUMNS.slice(), larger_passage: true, round_minutes: 10 } };
  S.libConfig = { statements_columns: COLUMNS.slice() };
  await setView('statements_columns', ['notes', 'transcript', 'statements']);
  out.sentOrder = sent.slice(); out.afterOrder = { cfg: S.data.config.statements_columns, lib: S.libConfig.statements_columns,
    drawn: drawn[drawn.length - 1] };
  // the notes hidden from Columns (18 October, 186), sent alone too
  await setView('columns_hidden', ['notes']);
  out.sentHidden = sent.slice(1);
  // Settings, opened now, reads what Columns chose, its ticks and rows read back as the choice, Stacked not
  // offered with a column hidden
  fillColumnsSet(columnsLayout(S.data.config));
  $('set-larger').checked = largerPassage(S.data.config);
  for (const m of MINIMAP_MODES) $(`set-minimap-${m}`).checked = minimapMode(S.data.config) === m;
  out.stackOffered = !$('set-stacked').disabled;
  out.settings = viewChoice();
  // a server from before the keys keeps neither, and the line says to restart
  answer = { config: { round_minutes: 10 } }; said.length = 0; sent.length = 0;
  await setView('larger_passage', false);
  out.oldServer = { said: said.slice(), sent: sent.slice() };
  answer = null;
  // the menu shuts and opens under its button
  viewMenu(true); out.open = { hidden: $('view-menu').hidden, expanded: $('btn-view').attrs['aria-expanded'], top: $('view-menu').style.top };
  viewMenu(false); out.shut = { hidden: $('view-menu').hidden, expanded: $('btn-view').attrs['aria-expanded'] };
  // the row: her passage carries its statements and its notes, escaped, and his carries neither
  out.hers = turnHtml({ i: 3, pos: 1, stop: true, name: 'Wren', time: '01:02', text: 'The kettle.', en: 'Tea as a <pause> & a door',
    pairs: [{ es: 'The kettle & its ritual', kq: '"The kettle."' }] });
  out.his = turnHtml({ i: 4, stop: false, name: 'Adam', time: '01:09', text: 'And then?', en: 'never shown', pairs: [{ es: 'never', kq: '' }] });
  out.empty = notesHtml({ en: '' });
  console.log(JSON.stringify(out));
})().catch((err) => { console.error(err.stack); process.exit(1); });
""", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
        if not out:
            check("151: the view's functions run in node", False, run.stderr.strip()[:400])
        else:
            check("151: with no keys the columns stand in the book's order and the current passage larger, the menu's "
                  "row saying so",
                  out["absent"] == {"order": "statements,transcript,notes", "same": False, "larger": True}, str(out["absent"]))
            check("151: an old notes' place draws the order nearest it, left the notes first and the statements last, under "
                  "the statements beside the transcript, larger off draws every passage at one size, an unknown place the "
                  "book's order, and an order kept wins over an old place, the card and the field placed each time",
                  out["left"] == {"order": "notes,transcript,statements", "same": True, "larger": False}
                  and out["under"] == {"order": "transcript,statements,notes", "same": False, "larger": True}
                  and out["odd"]["order"] == "statements,transcript,notes"
                  and out["chosen"]["order"] == "transcript,statements,notes" and out["placed"] == 10,
                  f"{out['left']} {out['under']} {out['placed']}")
            check("151: a choice of order is drawn at once and sends its one key alone to the settings, the page's copies "
                  "of the settings in step, and since 18 October (186) the notes hidden from Columns the same, Settings "
                  "opened after reading the columns shown and the stacking, Stacked not offered with a column hidden",
                  out["sentOrder"] == [["/api/settings", {"statements_columns": ["notes", "transcript", "statements"]}]]
                  and out["afterOrder"] == {"cfg": ["notes", "transcript", "statements"],
                                            "lib": ["notes", "transcript", "statements"], "drawn": "notes,transcript,statements"}
                  and out["sentHidden"] == [["/api/settings", {"columns_hidden": ["notes"]}]]
                  and out["settings"] == {"columns_hidden": ["notes"], "columns_stacked": False, "larger_passage": True,
                                          "minimap": "auto", "status_bar": False}
                  and out["stackOffered"] is False,
                  str(out["afterOrder"]) + " " + str(out.get("settings")))
            check("151: a server from before the keys answers without them, and the page says to restart",
                  out["oldServer"]["said"] == ["Restart the server to finish this update."]
                  and out["oldServer"]["sent"] == [["/api/settings", {"larger_passage": False}]], str(out["oldServer"]))
            check("151: the menu opens with aria-expanded true and shuts with it false",
                  {k: v for k, v in out["open"].items() if k != "top"} == {"hidden": False, "expanded": "true"}
                  and out["shut"] == {"hidden": True, "expanded": "false"}, f"{out['open']} {out['shut']}")
            check("151: each of her passages draws its statements cell and its notes cell after its words, read-only and "
                  "escaped, and the interviewer's draw neither",
                  '<div class="turn-text">The kettle.</div><div class="turn-es"><ol class="es-list"><li><button type="button" '
                  'tabindex="-1" class="es-go" data-es="0" title="Go to this statement"><span class="es-n" data-es-colour="0">1</span><span '
                  'class="es-words">The kettle &amp; its ritual</span></button></li></ol></div><div class="turn-notes"><div '
                  'class="turn-notes-text">Tea as a &lt;pause&gt; &amp; a door</div></div>' in out["hers"]
                  and "turn-notes" not in out["his"] and "turn-es" not in out["his"] and "never" not in out["his"]
                  and out["empty"] == '<div class="turn-notes-text"></div>', out["hers"][-200:])

    # ── D. the notes field: the same field and commit, and a click on the notes
    check("151: the notes stay one field, saved by the same commit as the statements",
          "en: $('en').value" in body("commit") and "row.en = $('en').value;" in body("commit")
          and app.count('id="en"') == 0 and page.count('id="en"') == 1)
    check("151: the column's click, mouse-up and right-click leave the current passage's notes to the field and its card "
          "to the card, and a click on another passage's notes goes there with the caret in them",
          "if (e.target.closest('.turn.current .turn-notes')) { if (e.target !== $('en')) $('en').focus(); return; }" in app
          and "if (e.target.closest('#es-card, #note-entry')) return;" in app
          and "e.target.closest('.turn.current .turn-notes, #es-card, #note-entry')) { S.selecting = false; return; }" in app
          and "|| e.target.closest('.turn.current .turn-notes, #es-card, #note-entry')) return;" in app
          and "if (toNotes) went.then(() => { if (!S.editing && !S.note && !guideHolds()) $('en').focus({ preventScroll: true }); });" in app)
    # ── F. the code keeps turn in its names, its routes and its request's key
    check("151: the code keeps turn in its names, the parameters, the routes and the request's key",
          "def user_message(turn: str," in inspect.getsource(statement_prompts) and "'/api/edit-turn'" in app
          and "def build_payload(turn: str," in inspect.getsource(statement_prompts)
          and "QUOTES_LEAD" in inspect.getsource(statement_prompts.user_message))
