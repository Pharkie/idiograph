"""Area 330: the band of option D, the statements screen's toolbar, the tabs that keep their width and Edit's Find and
Find and Replace (barsD, Adam, 6 November 2026, on barsrethink's drawings, after a tester found the lockup and the
path's Home doing the same thing).

What matters is what each does: the band reads the project's name, the participant's chooser and the question, with
no Home in any of the three apps, the name a button with a chevron (Adam, about 18:00 the same day, in place of a
"..." after it) that opens the menu the project's card has on Home, by the family's code, Remove from Idiograph from
inside leaving the screen and ending on Home, and Sift's and Trace's projects the same menu on their cards and their
names. The statements screen's toolbar's buttons do what their keys do and its place is kept across a restart, every
tab keeps its width whichever is in front, and Edit's two items press the page's own keys, Find and Replace greyed
where it has no card. Words,
places and sizes go to Adam as review shots. Every fixture is invented, a project on keeping bees."""
from __future__ import annotations

import html as html_mod
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import support
from .support import check, skip


def whole(src: str, head: str) -> str:
    at = src.index(head)
    return src[at:src.index("\n}\n", at) + 3]


def line_of(src: str, start: str) -> str:
    return next(ln for ln in src.splitlines() if ln.startswith(start))


def block(src: str, head: str) -> str:
    """a `const NAME = {` object written over several lines, to its closing `};`"""
    at = src.index(head)
    return src[at:src.index("\n};", at) + 3]


def test_bars_option_d(scratch: Path):
    print("\n330. The band of option D (Adam, 6 November 2026): no Home in the path, the project's name a button opening "
          "its card's menu from Home in Idiograph, Sift and Trace, the statements screen's own toolbar, the tabs keeping "
          "their width, and Edit's Find and Find and Replace")
    page = support.page_text()
    sift_page = support.page_text(app="sift")
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    tjs = support.text("apps/idiograph/static/themes.js")
    sift_s, trace = support.text("apps/sift/static/sift_search.js"), support.text("apps/trace/static/trace.js")
    part = lambda sid: page.split(f'<section id="{sid}"', 1)[1].split("</section>", 1)[0]
    path_of = lambda sec: sec.split('<nav class="ds-path"', 1)[1].split("</nav>", 1)[0]

    # ── A. the band's order on every kind of screen, the name a button with a chevron, and no Home in any app's path
    def order(sec, ids):
        p = path_of(part(sec))
        at = [p.find(f'id="{i}"') for i in ids]
        return all(a >= 0 for a in at) and at == sorted(at)
    work, themes = part("work"), part("themes")
    name_button = lambda i: f'<button type="button" class="ds-proj" id="{i}" aria-haspopup="true" aria-expanded="false"><span class="ds-proj-name"></span><svg class="ds-chevron"'
    check("330, updated about 18:00 (the name its menu's button): the statements screen's band reads the project's name, "
          "its tag in the demo, the participant's chooser and the timepoint's, then the rule, Research question and the question",
          order("work", ["rail-project", "rail-demo", "es-who", "tp-pick"])
          and work.index('class="ds-path-rule"') > work.index('id="tp-pick"')
          and work.index('id="band-question"') > work.index('class="ds-path-rule"'))
    check("330: the boards' band reads the project's name, then the participant's chooser on PETs and LPETs, and "
          "Trajectories' and the code list's the project's name alone, then the question",
          order("themes", ["th-project", "th-demo", "th-cases", "th-tp-pick"])
          and order("traj", ["tj-project", "tj-demo"]) and order("codes-screen", ["cd-project"])
          and "ds-who" not in path_of(part("traj")) + path_of(part("codes-screen")))
    check("330: no Home in the path in Idiograph, Sift or Trace, the lockup being Home, the project's name in every band "
          "of the three apps a button with a chevron that says it opens a menu, as the participant's chooser does, no "
          "\"...\" after it and no link to the project's page",
          "ds-path-home" not in page + sift_page + sift_s + trace and "path-home" not in js + tjs + sift_s + trace
          and all(name_button(i) in page for i in ("rail-project", "th-project", "tj-project", "cd-project"))
          and name_button("sf-name") in sift_page and name_button("sfs-name") in sift_s and name_button("tr-name") in trace
          and "ds-path-more" not in page + js + sift_page + sift_s + trace
          and "distilToProject" not in js + tjs + support.text("apps/idiograph/static/trajectories.js", "apps/idiograph/static/codes.js"))

    node = shutil.which("node")
    if not node:
        skip("330: the band's menu, the toolbar and Edit's items in node", "node is not installed")
        return

    # ── B. the name opens the card's own menu, by the family's code, and Remove from inside ends on Home
    pieces = [line_of(js, "const esc = "), line_of(js, "const escAttr = "), line_of(js, "const SHARE_LINE = "),
              line_of(js, "const trashWhere = "), line_of(js, "const pageId = "), whole(js, "function removedSaid("),
              line_of(js, "const PATH_NAMES = "), line_of(js, "const BAND_MENU = "),
              whole(js, "function projectMenuHtml("), whole(js, "function projectMenuWord("),
              whole(js, "function homeMenuItems("), whole(js, "function homeMenuRows("), whole(js, "function homeMenuHtml("),
              whole(js, "function homeMenuDo("), whole(js, "async function homeRemove("),
              whole(js, "function projectSettingsFor("),
              whole(js, "function pathProject("), whole(js, "function pathMenu("), whole(js, "function bandMenuShut("),
              whole(js, "function bandMenuOpen("), whole(js, "function bandMenuWire("), whole(js, "function menuItems("),
              whole(js, "function menuKeys("), whole(js, "function bandMenuBoot(")]
    harness = support.i18n_js() + r"""
const MAC = true;
const MOD = (e) => (MAC ? e.metaKey : e.ctrlKey);
const APP_NAME = 'Idiograph';
const DEMO_ID = 'demo';
let inWindow = true;
const windowPicks = () => inWindow;
const calls = [];
let LEAVES = true;
const S = { oneRun: false, home: '', data: { project: { id: 'ROOT-BEES', name: 'Keeping bees' }, demo: false } };
const HOME_PROJECTS = new Map();
const listeners = {};
const document = { activeElement: null, addEventListener: (n, f) => { listeners[n] = f; } };
const items = (html) => [...html.matchAll(/data-act="([a-z]+)"/g)].map((m) => ({ act: m[1], closest: () => null, getClientRects: () => [1],
  focus() { document.activeElement = this; calls.push(['focus', m[1]]); } }));
const els = {};
const el = (id) => els[id] || (els[id] = { id, hidden: id !== 'work', _html: '', kids: [], attrs: {}, style: {}, offsetWidth: 180,
  set innerHTML(v) { this._html = v; this.kids = items(v); }, get innerHTML() { return this._html; },
  setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return this.attrs[k]; },
  focus() { document.activeElement = this; calls.push(['focus', id]); }, contains: (x) => x === els[id],
  getBoundingClientRect: () => ({ left: 120, bottom: 90 }),
  querySelector() { return this.kids[0] || null; }, querySelectorAll() { return this.kids; } });
const $ = (id) => el(id);
const window = { innerWidth: 1280, idiographPageId: 'PAGE-330', addEventListener() {} };
// Remove's card (removetrash) stood in, answering Remove with the tick off as he would
const askRemove = async (name) => { calls.push(['confirm', name]); return { trash: false }; };
const sendProject = (id, name) => calls.push(['share', id, name]);
const showProjectFolder = (id) => calls.push(['show', id]);
const openProjectHistory = (id, name) => calls.push(['history', id, name]);
const openProjectSettings = (p) => calls.push(['settings', p.id, !!p.demo]);
const goHome = async () => { calls.push(['home']); return LEAVES; };
const api = async (route, body) => { calls.push(['api', route, body.op, body.root]); return { name: 'Keeping bees' }; };
const loadLibrary = async () => { calls.push(['library']); };
const say = (t) => calls.push(['say', t]);
const needsRestart = () => false;
const RESTART_LINE = '';
""" + "\n".join(pieces) + r"""
(async () => {
  const out = {};
  bandMenuBoot();
  for (const id of PATH_NAMES) bandMenuWire(id, pathMenu);
  const name = el('rail-project');
  const menu = el('path-menu');
  const acts = () => menu.kids.map((k) => k.act);
  name.onclick({ stopPropagation() {} });
  out.window = { shown: !menu.hidden, acts: acts(), card: homeMenuItems({ demo: false }, { window: true, mac: true, oneRun: false }),
    html: menu.innerHTML === homeMenuHtml(homeMenuItems({}, { window: true, mac: true, oneRun: false }), { window: true, mac: true, oneRun: false }),
    expanded: name.attrs['aria-expanded'], focus: document.activeElement && document.activeElement.act };
  // Down and Up move through the items, round from the last to the first, and Esc shuts it with the focus on the name
  const key = (k) => menu.onkeydown({ key: k, preventDefault() {}, stopPropagation() {} });
  key('ArrowDown'); const down = document.activeElement.act;
  key('ArrowUp'); key('ArrowUp'); const round = document.activeElement.act;
  key('Escape');
  out.keys = { down, round, shut: menu.hidden, back: document.activeElement === name, expanded: name.attrs['aria-expanded'] };
  // a second press on the name shuts what the first opened
  name.onclick({ stopPropagation() {} }); name.onclick({ stopPropagation() {} });
  out.twice = menu.hidden;
  inWindow = false;
  name.onclick({ stopPropagation() {} });
  out.browser = acts();
  bandMenuShut();
  S.oneRun = true;
  name.onclick({ stopPropagation() {} });
  out.oneRun = acts();
  bandMenuShut();
  S.oneRun = false;
  // the demo's band: Project settings alone, as its card, and it opens the demo's own sheet
  S.data = { project: { name: 'Living with a dog' }, demo: true };
  name.onclick({ stopPropagation() {} });
  out.demo = acts();
  calls.length = 0;
  menu.onclick({ stopPropagation() {}, target: { closest: () => ({ dataset: { act: 'settings' } }) } });
  out.demoSettings = calls.filter((c) => c[0] === 'settings');
  // each item does its card's job for the project in front
  S.data = { project: { id: 'ROOT-BEES', name: 'Keeping bees' }, demo: false };
  const run = async (act) => {
    calls.length = 0;
    name.onclick({ stopPropagation() {} });
    menu.onclick({ stopPropagation() {}, target: { closest: () => ({ dataset: { act } }) } });
    await new Promise((r) => setTimeout(r, 10));
    return calls.filter((c) => c[0] !== 'focus');
  };
  out.share = await run('share');
  out.history = await run('history');
  out.settings = await run('settings');
  // Remove from inside: asked first, the screen left as Home leaves it, then removed, then Home drawn without it
  out.remove = await run('remove');
  LEAVES = false;
  out.kept = await run('remove');
  LEAVES = true;
  // and from Home's card, no screen to leave
  calls.length = 0;
  await homeMenuDo('remove', 'ROOT-BEES', 'Keeping bees', null);
  await new Promise((r) => setTimeout(r, 10));
  out.card = calls.slice();
  console.log(JSON.stringify(out));
})().catch((e) => { console.error(String(e && e.stack || e)); process.exit(1); });
"""
    run = support.run_node(harness, scratch, "band-330.js", timeout=60)
    o = json.loads(run.stdout.strip().splitlines()[-1]) if run.returncode == 0 and run.stdout.strip() else {}
    why = (run.stdout + run.stderr)[-600:]
    w = o.get("window", {})
    check("330: in node, the band's name opens the menu the project's card has on Home, drawn by the family's code from "
          "the card's items: Share a copy, Show in Finder in Idiograph's own window, Project settings, Project history and "
          "Remove from Idiograph, the name marked open and the first item given the focus, and a second press shuts it",
          w.get("shown") is True and w.get("acts") == ["share", "qdpx", "show", "settings", "history", "remove"] == w.get("card")
          and w.get("html") is True and w.get("expanded") == "true" and w.get("focus") == "share" and o.get("twice") is True
          and o.get("browser") == ["share", "qdpx", "settings", "history", "remove"]
          and o.get("oneRun") == ["share", "qdpx", "settings", "history"], why)
    check("330: in node, the name's menu takes the participant chooser's keys: Down and Up move through its items, round "
          "from the first to the last, and Esc shuts it with the focus back on the name",
          o.get("keys") == {"down": "qdpx", "round": "remove", "shut": True, "back": True, "expanded": "false"}, why)
    check("330: in node, the demo's band menu holds Project settings alone, as its card, opening the demo's own sheet",
          o.get("demo") == ["settings"] and o.get("demoSettings") == [["settings", "demo", True]], why)
    check("330: in node, each item does its card's job for the project in front: Share a copy, Project history and "
          "Project settings for that project",
          o.get("share") == [["share", "ROOT-BEES", "Keeping bees"]] and o.get("history") == [["history", "ROOT-BEES", "Keeping bees"]]
          and o.get("settings") == [["settings", "ROOT-BEES", False]], why)
    removed = o.get("remove") or []
    check("330: in node, Remove from Idiograph from inside asks first, leaves the screen as Home does, then takes the "
          "project off Idiograph's list and draws Home without it, and a save that fails on the way out keeps him there "
          "with the project kept, and from Home's card there is no screen to leave",
          [c[0] for c in removed] == ["confirm", "home", "api", "say", "library"]
          and removed[2][1:] == ["/api/projects", "remove", "ROOT-BEES"]
          and [c[0] for c in o.get("kept") or []] == ["confirm", "home"]
          and [c[0] for c in o.get("card") or []] == ["confirm", "api", "say", "library"], why)

    _sift_trace_menus(scratch, js)
    _remove_a_copy(scratch, js)
    _remove_to_trash(scratch)

    # ── C. the statements screen's toolbar: each button does what its key does, and it docks and floats
    tool_pieces = [block(tjs, "const TH_TOOLS = {"), line_of(tjs, "const thDocked = "), line_of(tjs, "const TH_PALETTE_HOME = "),
                   line_of(tjs, "const TH_PAL_STEPS = "), line_of(tjs, "const TH_DOCK_STEPS = "),
                   whole(tjs, "function thPaletteHeld("), whole(tjs, "function thPaletteRoom("), whole(tjs, "function thPalettePlace("),
                   whole(tjs, "function thPaletteFit("), block(js, "const ES_TOOLS = {"), whole(js, "async function esToolsSave("),
                   whole(js, "function esUndoTool("), whole(js, "function esToolsBoot(")]
    tool = support.i18n_js() + r"""
const calls = [];
const els = {};
class El {
  constructor(id) { this.id = id; this.kids = []; this.parentElement = null; this.cls = new Set(); this.attrs = {}; this.hidden = false;
    this.style = { setProperty() {} }; this.offsetWidth = 140; this.offsetHeight = 300; this.clientWidth = 1000; this.clientHeight = 600;
    this.on = {}; const self = this;
    this.classList = { add: (...n) => n.forEach((x) => self.cls.add(x)), remove: (...n) => n.forEach((x) => self.cls.delete(x)),
      contains: (n) => self.cls.has(n), toggle: (n, v) => { if (v === undefined) v = !self.cls.has(n); if (v) self.cls.add(n); else self.cls.delete(n); return v; } }; }
  appendChild(k) { if (k.parentElement) k.parentElement.kids = k.parentElement.kids.filter((x) => x !== k); this.kids.push(k); k.parentElement = this; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  querySelector() { return null; }
  addEventListener(type, f) { (this.on[type] = this.on[type] || []).push(f); }
  getClientRects() { return []; }
  click() { if (this.onclick) this.onclick({}); }
}
const $ = (id) => els[id] || (els[id] = new El(id));
$('work').hidden = false;
const S = { data: { path: 'bees.xlsx', config: {} }, libConfig: null };
let TH;
let typing = false;
const openFind = () => calls.push('find');
const move = (d) => calls.push('move ' + d);
const undoStep = (back) => calls.push(back ? 'undo' : 'redo');
const nativeUndoOwns = () => typing;
const document = { execCommand: (c) => calls.push('field ' + c), fonts: null };
const window = {};
const measureBand = () => calls.push('measure');
const thPaletteGrab = (e, spec) => calls.push('grab ' + spec.pal);
const api = async (route, body) => { calls.push(['api', route, body]); return { config: body }; };
const say = () => {};
const needsRestart = () => false;
const RESTART_LINE = '';
""" + "\n".join(tool_pieces) + r"""
(async () => {
  const out = {};
  esToolsBoot();
  for (const id of ['es-find', 'es-prev', 'es-next', 'es-undo', 'es-redo']) $(id).click();
  typing = true;
  $('es-undo').click(); $('es-redo').click();
  $('es-palette-grip').on.pointerdown[0]({ button: 0 });
  out.buttons = calls.filter((c) => typeof c === 'string' && c !== 'measure');
  out.keeps = $('es-palette').on.pointerdown.length === 1;
  // docked under the band by default, floating on the columns when the settings say so, its row gone, and docked again
  $('es-stage').appendChild($('es-palette'));
  thPalettePlace(undefined, ES_TOOLS);
  out.fresh = { in: $('es-palette').parentElement.id, docked: $('es-palette').cls.has('docked'), dock: !$('es-dock').hidden };
  S.data.config = { es_palette_docked: false, es_palette_place: { edge: 'right', y: 0.5 } };
  thPalettePlace(undefined, ES_TOOLS);
  out.floating = { in: $('es-palette').parentElement.id, docked: $('es-palette').cls.has('docked'), dock: !$('es-dock').hidden,
    right: $('es-palette').cls.has('right') };
  calls.length = 0;
  await esToolsSave('es_palette_docked', true);
  out.saved = { in: $('es-palette').parentElement.id, dock: !$('es-dock').hidden, sent: calls.filter((c) => Array.isArray(c)).map((c) => c[2]) };
  // the boards' toolbar keeps its own settings and its dock beside the statements screen's
  TH = { config: { palette_docked: false } };
  out.apart = { es: thDocked(ES_TOOLS), board: thDocked() };
  console.log(JSON.stringify(out));
})().catch((e) => { console.error(String(e && e.stack || e)); process.exit(1); });
"""
    run = support.run_node(tool, scratch, "toolbar-330.js", timeout=60)
    t = json.loads(run.stdout.strip().splitlines()[-1]) if run.returncode == 0 and run.stdout.strip() else {}
    why = (run.stdout + run.stderr)[-600:]
    check("330: in node, the statements screen's toolbar does what its keys do: Find and replace opens its card as Cmd + "
          "Shift + F, the previous and the next passage move as Cmd + J and K, Undo and Redo are the screen's own as Cmd + "
          "Z and Shift + Cmd + Z, a field's own while its typing is the newer, and the grip moves it by the boards' code, "
          "a press on a tool leaving the focus where it was",
          t.get("buttons") == ["find", "move -1", "move 1", "undo", "redo", "field undo", "field redo", "grab es-palette"]
          and t.get("keeps") is True, why)
    check("330: in node, the statements screen's toolbar stands docked under the band by default, floats on the columns "
          "against its edge when the settings say so with its row under the band gone, docks again when kept so, and "
          "keeps its own settings apart from the boards'",
          t.get("fresh") == {"in": "es-dock", "docked": True, "dock": True}
          and t.get("floating") == {"in": "es-stage", "docked": False, "dock": False, "right": True}
          and t.get("saved") == {"in": "es-dock", "dock": True, "sent": [{"es_palette_docked": True}]}
          and t.get("apart") == {"es": True, "board": False}, why)

    # its place kept in the settings file across a restart, as the boards' is
    import idiograph_routes
    import server as server_mod
    cfg = scratch / "config-330.json"
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Sam"}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, None
        server_mod.STATE_MEMORY = {"recent": []}
        fresh = server_mod.merge_config({})
        server_mod.api_settings({"es_palette_docked": False, "es_palette_place": {"edge": "left", "y": 0.3}})
        saved = json.loads(cfg.read_text(encoding="utf-8"))
        back = server_mod.merge_config(saved)
        odd = server_mod.merge_config({"es_palette_docked": "no", "es_palette_place": {"edge": "up", "y": 1}})
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
    check("330: the statements screen's toolbar is docked with no place on a new install, and pulled off and placed it "
          "is kept so in the settings file across a restart, the boards' toolbar's own left as it was, and anything "
          "else read as docked at no place",
          fresh["es_palette_docked"] is True and fresh["es_palette_place"] is None
          and back["es_palette_docked"] is False and back["es_palette_place"] == {"edge": "left", "y": 0.3}
          and back["palette_docked"] is True and back["palette_place"] is None and saved.get("interviewer") == "Sam"
          and odd["es_palette_docked"] is True and odd["es_palette_place"] is None
          and idiograph_routes.palette_place({"edge": "right", "y": -2}) == {"edge": "right", "y": 0.0}, str(saved))

    # ── D. Edit's Find and Find and Replace, in the shell's menus and through window.js in node
    src = support.TOOL / "packaging" / "tauri"
    menu_rs = (src / "src-tauri" / "src" / "menu.rs").read_text(encoding="utf-8")
    main_rs = (src / "src-tauri" / "src" / "main.rs").read_text(encoding="utf-8")
    words = json.loads((support.TOOL / "family" / "static" / "i18n" / "en" / "menus.json").read_text(encoding="utf-8"))
    mac = menu_rs.split("pub fn build(", 1)[1].split("\n}\n", 1)[0]
    win = menu_rs.split("fn build_bar(", 1)[1].split("\n}\n", 1)[0]
    edit_mac = mac.split('t("menus.edit")', 1)[1].split("])?;", 1)[0]
    edit_win = win.split('t("menus.win_edit")', 1)[1].split("])?;", 1)[0]
    handled = main_rs.split("fn menu_event(", 1)[1].split("\n}\n", 1)[0]
    check("330: Edit holds Find… on Cmd+F and Find and Replace… on Cmd+Shift+F after Select All on a Mac, and &Find… and "
          "Find and R&eplace… on Windows naming Ctrl+F and Ctrl+Shift+F, apart from &Redo's R, each handed to the page, Find and Replace "
          "greyed by the page's word as Project History is",
          edit_mac.index('"menus.select_all"') < edit_mac.index('item(app, "find", &t("menus.find"), Some("CmdOrCtrl+F"))')
          < edit_mac.index("&replace")
          and 'let replace = item(app, "find-replace", &t("menus.find_replace"), Some("CmdOrCtrl+Shift+F"))?;' in mac
          and edit_win.index('"menus.win_select_all"') < edit_win.index('keyed(app, "find", &t("menus.win_find"), "Ctrl+F")') < edit_win.index("&replace")
          and 'let replace = keyed(app, "find-replace", &t("menus.win_find_replace"), "Ctrl+Shift+F")?;' in win
          and words["menus.find"] == "Find…" and words["menus.find_replace"] == "Find and Replace…"
          and words["menus.win_find"] == "&Find…\tCtrl+F" and words["menus.win_find_replace"] == "Find and R&eplace…\tCtrl+Shift+F"
          and '"find" | "find-replace"' in handled and "pub fn set_history(on: bool, settings: bool, replace: bool)" in menu_rs
          and "menu::set_history(on, settings.unwrap_or(on), replace.unwrap_or(false));" in main_rs)
    window_js = (src / "window.js").read_text(encoding="utf-8")
    shell = r"""
const src = require('fs').readFileSync(process.argv[2], 'utf8');
class Ev { constructor(type, o) { this.type = type; Object.assign(this, o || {}); this.defaultPrevented = false; } preventDefault() { if (this.cancelable) this.defaultPrevented = true; } stopPropagation() {} }
class Storage { constructor() { this.m = new Map(); } get length() { return this.m.size; } key(i) { return [...this.m.keys()][i] || null; }
  getItem(k) { return this.m.has(k) ? this.m.get(k) : null; } setItem(k, v) { this.m.set(k, String(v)); } removeItem(k) { this.m.delete(k); } }
function load(os, replace) {
  const t = { invoked: [], keys: [], on: {}, ticks: [] };
  const field = { dispatchEvent: (e) => { t.keys.push({ type: e.type, key: e.key, meta: !!e.metaKey, ctrl: !!e.ctrlKey, shift: !!e.shiftKey }); return true; } };
  const win = { __IDIOGRAPH_OS__: os, __IDIOGRAPH_SEED__: { local: {} }, Storage, localStorage: new Storage(), sessionStorage: new Storage(),
    Event: Ev, KeyboardEvent: Ev, PageTransitionEvent: Ev, location: {}, addEventListener: (n, f) => { (t.on[n] = t.on[n] || []).push(f); },
    dispatchEvent: () => true, btoa: (s) => Buffer.from(s, 'latin1').toString('base64'), setInterval: (f) => t.ticks.push(f),
    idiographProjectNow: () => true, idiographProjectSettingsNow: () => true, idiographReplaceNow: () => replace,
    __TAURI_INTERNALS__: { invoke: (cmd, args) => { t.invoked.push([cmd, args]); return Promise.resolve(null); } } };
  const document = { activeElement: field, body: field, getElementById: () => null };
  global.Event = Ev; global.KeyboardEvent = Ev; global.PageTransitionEvent = Ev; global.document = document;
  new Function('window', 'document', src)(win, document);
  t.win = win;
  return t;
}
const out = {};
const m = load('macos', true);
m.win.__idiographMenu('find'); m.win.__idiographMenu('find-replace');
m.ticks.forEach((f) => f());
out.mac = { keys: m.keys, told: m.invoked.filter((c) => c[0] === 'project_now').map((c) => c[1]) };
const w = load('windows', false);
w.win.__idiographMenu('find'); w.win.__idiographMenu('find-replace');
w.ticks.forEach((f) => f());
out.win = { keys: w.keys, told: w.invoked.filter((c) => c[0] === 'project_now').map((c) => c[1]) };
console.log(JSON.stringify(out));
"""
    harness_file = scratch / "window-330.js"
    harness_file.write_text(shell, encoding="utf-8")
    js_file = scratch / "window-330-src.js"
    js_file.write_text(window_js, encoding="utf-8")
    ran = subprocess.run([node, str(harness_file), str(js_file)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    e = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {}
    key = lambda meta, ctrl, shift: {"type": "keydown", "key": "f", "meta": meta, "ctrl": ctrl, "shift": shift}
    check("330: in node, Edit's Find and Find and Replace press the page's own keys where the focus is, Cmd+F and "
          "Cmd+Shift+F on a Mac, Ctrl+F and Ctrl+Shift+F on Windows, and the page tells the shell whether the statements "
          "screen is in front, for Find and Replace's grey",
          (e.get("mac") or {}).get("keys") == [key(True, False, False), key(True, False, True)]
          and (e.get("win") or {}).get("keys") == [key(False, True, False), key(False, True, True)]
          and (e.get("mac") or {}).get("told") == [{"on": True, "settings": True, "replace": True}]
          and (e.get("win") or {}).get("told") == [{"on": True, "settings": True, "replace": False}],
          (ran.stdout + ran.stderr)[-600:])
    check("330: the page says Find and Replace applies while the statements screen is in front with a participant open",
          "window.idiographReplaceNow = () => !!S.data && !$('work').hidden;" in js)

    # ── E. every tab keeps its width whichever is in front, in a real browser, Idiograph's and Sift's
    _tabs_keep_width(scratch, node, page)


TABS = r"""
const out = {};
const measure = (nav) => [...nav.querySelectorAll(':scope > *')].filter((e) => e.getClientRects().length && getComputedStyle(e).display !== 'none')
  .map((e) => { const r = e.getBoundingClientRect(); return [Math.round(r.left * 10) / 10, Math.round(r.width * 10) / 10]; });
for (const id of ['es-steps', 'th-steps']) {
  const nav = document.getElementById(id);
  const tabs = [...nav.querySelectorAll('.ds-tab:not([hidden])')];
  out[id] = tabs.map((on) => { tabs.forEach((t) => t.classList.toggle('on', t === on)); return measure(nav); });
  out[id + '-first'] = Math.round(tabs[0].getBoundingClientRect().left * 10) / 10;
  out[id + '-bold'] = getComputedStyle(nav.querySelector('.ds-tab.on .ds-tab-name')).fontWeight;
}
const sift = document.getElementById('sf-steps');
const steps = [...sift.querySelectorAll('button')];
out.sift = steps.map((on) => { steps.forEach((b) => (b === on ? b.setAttribute('aria-current', 'step') : b.removeAttribute('aria-current'))); return measure(sift); });
out.siftBold = getComputedStyle(sift.querySelector('[aria-current]')).fontWeight;
document.getElementById('out').textContent = JSON.stringify(out);
"""


def _tabs_keep_width(scratch, node, page):
    """The page's own bars of tabs and Sift's steps as rvStepsHtml draws them, with the stylesheets, in the computer's
    own browser, headless, at 1280: every tab measured with each in front in turn"""
    exe = support.browser()
    if exe is None:
        skip("330: the tabs keeping their width in a real browser", "no Chrome, Chromium, Brave or Edge on this computer")
        return
    rail = lambda sid: page.split(f'<section id="{sid}"', 1)[1].split('<div class="rail', 1)[1].split("\n  </div>", 1)[0]
    ssjs = support.text("apps/sift/static/sift_search.js")
    steps_js = support.i18n_js("sift") + "\n".join([
        "const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));",
        line_of(ssjs, "const RV_TA_LATER = "), line_of(ssjs, "const RV_FT_LATER = "), line_of(ssjs, "const RV_FORM_NAME = "),
        line_of(ssjs, "const RV_EX_LATER = "), "const SFS = { runs: [] };", whole(ssjs, "function rvStepsHtml(")]) + r"""
const c = (n) => ({ records: n, include: n });
console.log(JSON.stringify(rvStepsHtml({ searches: true, screening: 'r/1' }, 'ta', { ta: c(58), ft: c(7), ex: c(3) })));
"""
    ran = support.run_node(steps_js, scratch, "steps-330.js", timeout=60)
    steps = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else ""
    css = "\n".join(support.text(p) for p in ("family/static/tokens.css", "family/static/style.css", "family/static/frame.css",
                                              "apps/idiograph/static/distil.css", "apps/idiograph/static/themes.css",
                                              "apps/sift/static/sift.css"))
    doc = ('<!doctype html><html><head><meta charset="utf-8"><style>' + css + "</style></head><body>"
           '<section id="work" class="screen"><div class="rail' + rail("work") + "\n  </div></section>"
           '<section id="themes" class="screen th-screen"><div class="rail' + rail("themes") + "\n  </div></section>"
           '<section id="sift" class="screen sf-screen"><div class="rail sf-rail"><nav class="sf-steps" id="sf-steps">' + steps
           + '</nav><span class="rail-grow"></span></div></section><pre id="out">none</pre><script>' + TABS + "</script></body></html>")
    with tempfile.TemporaryDirectory(prefix="idiograph-330-") as tmp:
        page_file = Path(tmp) / "tabs.html"
        page_file.write_text(doc, encoding="utf-8")
        cmd = [str(exe), "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
               "--disable-background-networking", "--disable-component-update", "--disable-sync", "--disable-default-apps",
               "--password-store=basic", "--use-mock-keychain", f"--user-data-dir={Path(tmp) / 'profile'}",
               "--window-size=1280,800", "--virtual-time-budget=3000", "--dump-dom", page_file.as_uri()]
        try:
            dumped = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=120).stdout
        except (OSError, subprocess.TimeoutExpired) as err:
            dumped = str(err)
    said = dumped.split('<pre id="out">', 1)[1].split("</pre>", 1)[0] if '<pre id="out">' in dumped else "{}"
    o = json.loads(html_mod.unescape(said)) if said.startswith("{") else {}
    same = lambda runs: bool(runs) and len(runs[0]) > 1 and all(r == runs[0] for r in runs)
    check("330: in a real browser at 1280, every tab of the statements bar and of the boards' bar stands in the same "
          "place at the same width whichever tab is in front, the one in front still bold, and the boards' bar starts its "
          "tabs where the statements bar does",
          same(o.get("es-steps")) and same(o.get("th-steps")) and o.get("es-steps-first") == o.get("th-steps-first")
          and o.get("es-steps-bold") == "600" and o.get("th-steps-bold") == "600", str(o)[:700])
    check("330: in a real browser at 1280, Sift's steps keep their places and widths whichever is in front, the step in "
          "front still bold", "tab-w" in steps and same(o.get("sift")) and o.get("siftBold") == "600", str(o)[:500] + str(steps)[:200])


REMOVE_HOME = r"""
const MAC = true;
const LINUX = false;
const APP_NAME = 'Idiograph';
let inWindow = true;
const windowPicks = () => inWindow;
const calls = [];
let refuse = '';
const S = { oneRun: false };
const HOME_PROJECTS = new Map();
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const document = { querySelectorAll: () => [], addEventListener() {} };
const window = { idiographPageId: 'PAGE-330', confirm: (q) => { calls.push(['browser confirm', q]); return true; } };
/* Remove's card as page.html draws it, its kicker, title, line, tick and two buttons, shown and hidden as the
   family's show and hide do */
const els = {};
const $ = (id) => els[id] || (els[id] = { id, hidden: true, textContent: '', checked: false });
els['remove-card'] = { id: 'remove-card', hidden: true };
const show = (id) => { $(id).hidden = false; calls.push(['card', $('rm-project').textContent, $('rm-title').textContent,
  $('rm-line').textContent, $('rm-trash-word').textContent, $('rm-trash').checked]); };
const hide = (id) => { $(id).hidden = true; };
const sendProject = (id, name) => calls.push(['share', id, name]);
const exportQdpx = (id, name) => calls.push(['qdpx', id, name]);
const showProjectFolder = (id) => calls.push(['show', id]);
const openProjectHistory = (id, name) => calls.push(['history', id, name]);
const projectSettingsFor = (p) => calls.push(['settings', p && p.id]);
const goHome = async () => { calls.push(['home']); return true; };
const api = async (route, body) => {
  calls.push(['api', route, body.op, body.root, body.trash, body.page]);
  if (refuse) throw new Error(refuse);
  const name = body.root === 'ROOT-COPY' ? 'Keeping bees' : 'Hive notes';
  return body.trash ? { name, trash: true, where: 'Bin' } : { name };
};
const loadLibrary = async () => { calls.push(['library']); };
const say = (t) => calls.push(['say', t]);
const menuKeys = () => {};
const needsRestart = () => false;
const RESTART_LINE = '';
""" + "%s" + r"""
rmWire();
/* Home's list as the page draws it, homeCardHtml's cards, each card an element with its dots, its menu and its items */
function cardOf(html) {
  const id = /data-id="([^"]*)"/.exec(html)[1];
  const name = /<span class="hc-name">([^<]*)<\/span>/.exec(html)[1];
  const acts = [...html.matchAll(/data-act="([a-z]+)"/g)].map((m) => m[1]);
  const buttons = acts.map((act) => ({ dataset: { act }, closest: () => ({ dataset: { act } }), focus() {} }));
  const menu = { hidden: true, querySelector: () => buttons[0], querySelectorAll: () => buttons };
  const dots = { attrs: {}, setAttribute(k, v) { this.attrs[k] = String(v); }, focus() {} };
  const parts = { '.hc-dots': dots, '.hc-menu': menu, '.home-card': { dataset: { id } }, '.hc-name': { textContent: name } };
  return { acts, menu, dots, copy: html.includes('class="tag copy"'), querySelector: (sel) => parts[sel] || null };
}
const cards = [{ id: 'ROOT-BEES', name: 'Hive notes', question: '', line: '' },
               { id: 'ROOT-COPY', name: 'Keeping bees', question: '', line: '', copy: true }].map((c) => cardOf(homeCardHtml(c)));
const list = { querySelectorAll: (sel) => (sel === '.home-card-li.has-menu' ? cards : []) };
homeMenus(list);
/* a press on the card's dots, then on Remove from Idiograph in its menu, then on the card: `answer` 'go', 'tick'
   (the tick, then Remove), 'cancel' or 'esc' */
const press = async (card, answer) => {
  calls.length = 0;
  card.dots.onclick({ stopPropagation() {} });
  const opened = !card.menu.hidden;
  card.menu.onclick({ stopPropagation() {}, target: { closest: () => ({ dataset: { act: 'remove' } }) } });
  await new Promise((r) => setTimeout(r, 5));
  const shown = !$('remove-card').hidden;
  if (answer === 'tick') {
    $('rm-trash').checked = true;
    $('rm-trash').onchange();
    calls.push(['line', $('rm-line').textContent]);
  }
  if (answer === 'go' || answer === 'tick') $('rm-go').onclick();
  else if (answer === 'cancel') $('rm-cancel').onclick();
  else rmAnswer(false);
  await new Promise((r) => setTimeout(r, 10));
  return { opened, shown, shut: card.menu.hidden, gone: $('remove-card').hidden, calls: calls.slice() };
};
(async () => {
  const out = { acts: cards.map((c) => c.acts), copy: cards.map((c) => c.copy) };
  const [plain, copy] = cards;
  out.copyOk = await press(copy, 'go');
  out.copyCancel = await press(copy, 'cancel');
  out.copyEsc = await press(copy, 'esc');
  out.plainOk = await press(plain, 'go');
  out.ticked = await press(copy, 'tick');
  // the tick starts off again the next time
  out.again = await press(copy, 'cancel');
  // the server's refusal said at the foot, never swallowed
  refuse = 'Its folder is open in another window, so nothing was moved to the Bin or removed.';
  out.refused = await press(copy, 'tick');
  refuse = '';
  // no page of the three apps asks Remove in a system's box any more: the browser's confirm is never called
  inWindow = false;
  out.browser = await press(copy, 'go');
  console.log(JSON.stringify(out));
})().catch((e) => { console.error(String(e && e.stack || e)); process.exit(1); });
"""


def _remove_a_copy(scratch, js):
    """Remove from Idiograph on a shared copy's card (removefix, Adam, 9 November 2026, about 22:15: on Home, the card
    of a project marked COPY, its menu's Remove from Idiograph did nothing when clicked, twice, in his app). The Mac's web
    view answers window.confirm with Cancel and shows no box, so every Remove in the app's window stopped at its first
    line. Since removetrash (10 November 2026) Remove asks in the page's own card, which carries the tick to move the
    folder to the Trash as well, so no system's box is asked. In node, from the card's own handler, then through the
    route on an invented project and its shared copy."""
    import server as server_mod
    import idiograph_routes
    import project_pack  # noqa: F401  the copy's file, as Share a copy writes it
    node = shutil.which("node")
    if not node:
        skip("330: Remove from Idiograph on a copy's card in node", "node is not installed")
    else:
        pieces = [line_of(js, "const SHARE_LINE = "), line_of(js, "const RM = "), line_of(js, "const trashWhere = "),
                  line_of(js, "const pageId = "), whole(js, "function askRemove("), whole(js, "function rmLine("),
                  whole(js, "function rmAnswer("), whole(js, "function rmWire("), whole(js, "function removedSaid("),
                  whole(js, "function projectMenuHtml("), whole(js, "function projectMenuWord("),
                  whole(js, "function projectDotsHtml("), whole(js, "function shutProjectMenus("),
                  whole(js, "function projectMenus("), whole(js, "function homeMenuItems("), whole(js, "function homeMenuRows("),
                  whole(js, "function homeCardHtml("), whole(js, "function homeMenus("), whole(js, "function homeMenuDo("),
                  whole(js, "async function homeRemove(")]
        ran = support.run_node(support.i18n_js() + REMOVE_HOME % "\n".join(pieces), scratch, "remove-330.js", timeout=60)
        o = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {}
        why = (ran.stdout + ran.stderr)[-600:]
        card = ["card", "Keeping bees", "Remove from Idiograph", "Its folder and files stay as they are.",
                "Move its folder to the Bin too", False]
        kinds = lambda run: [c[0] for c in (run or {}).get("calls", [])]
        ok = o.get("copyOk") or {}
        check("330: in node, a shared copy's card on Home has Remove from Idiograph in its menu as any project's has, and "
              "pressing it asks in Remove's own card, the project's name, its folder kept and the tick off, then Remove "
              "takes the copy off the list with its folder kept, names the page asking, says so and draws Home again",
              o.get("copy") == [False, True] and o.get("acts") == [["share", "qdpx", "show", "settings", "history", "remove"]] * 2
              and ok.get("opened") is True and ok.get("shut") is True and ok.get("shown") is True and ok.get("gone") is True
              and ok.get("calls") == [card, ["api", "/api/projects", "remove", "ROOT-COPY", False, "PAGE-330"],
                                      ["say", "Removed Keeping bees."], ["library"]], why)
        check("330: in node, Cancel on Remove's card, or Esc, removes nothing",
              kinds(o.get("copyCancel")) == ["card"] and kinds(o.get("copyEsc")) == ["card"]
              and (o.get("copyCancel") or {}).get("gone") is True, why)
        check("330: in node, an ordinary project's card asks and removes the same way",
              kinds(o.get("plainOk")) == ["card", "api", "say", "library"]
              and o["plainOk"]["calls"][1][3] == "ROOT-BEES", why)
        ticked = (o.get("ticked") or {}).get("calls", [])
        check("330: in node, the card's tick says the folder goes to the Bin, and Remove with it ticked asks the server to "
              "move the folder to the Trash, the foot saying where it went, and the tick is off again the next time",
              kinds(o.get("ticked")) == ["card", "line", "api", "say", "library"]
              and ticked[1] == ["line", "Its folder and every file in it go to the Bin."]
              and ticked[2] == ["api", "/api/projects", "remove", "ROOT-COPY", True, "PAGE-330"]
              and ticked[3] == ["say", "Removed Keeping bees. Its folder is in the Bin."]
              and (o.get("again") or {}).get("calls", [[]])[0] == card, why)
        refused = (o.get("refused") or {}).get("calls", [])
        check("330: in node, a Remove the server refuses says why at the foot, never silent, and draws nothing again",
              kinds(o.get("refused")) == ["card", "line", "api", "say"]
              and refused[-1] == ["say", "Its folder is open in another window, so nothing was moved to the Bin or removed."], why)
        check("330: in node, a browser's page asks in the same card, never the browser's own confirm",
              kinds(o.get("browser")) == ["card", "api", "say", "library"], why)
    # the window's side: the page's ask reaches the window's confirm command, a message box with OK and Cancel
    window_js = support.text("packaging/tauri/window.js")
    main_rs = support.text("packaging/tauri/src-tauri/src/main.rs")
    command = main_rs.split("async fn confirm(", 1)[1].split("\n}\n", 1)[0] if "async fn confirm(" in main_rs else ""
    check("330: the app's window answers the page's confirm with its own message box, OK and Cancel in the app's words, "
          "true for OK alone",
          "win.idiographConfirm = function (message) {" in window_js and "ask('confirm', { message: String(message || '') })" in window_js
          and "ok === true" in window_js and "rfd::MessageButtons::OkCancelCustom(ok.clone(), words::t(\"menus.cancel\"))" in command
          and ".set_parent(&window)" in command, command[:300])
    plain_js = support.text("apps/idiograph/static/distil.js", "apps/idiograph/static/team.js", "apps/sift/static/sift_settings.js",
                            "apps/trace/static/trace.js")
    check("330: no page of the three apps asks window.confirm itself, every confirm going through askSure, and Remove "
          "from Idiograph, from Sift and from Trace through Remove's own card in every place it is offered",
          "window.confirm(" not in plain_js and plain_js.count("await askSure(") >= 5
          and plain_js.count("await askRemove(") == 6, str([plain_js.count("await askSure("), plain_js.count("await askRemove(")]))

    # through the route: an invented project shared, its copy opened, then each removed, files untouched
    base = scratch / "remove-330"
    shutil.rmtree(base, ignore_errors=True)
    root, out, into = base / "Keeping bees", base / "out", base / "into"
    (root / "P1 - Wren").mkdir(parents=True)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({"name": "Keeping bees", "research_question":
                                                            "How do beekeepers live through a cold spring?",
                                                            "uid": "a330beef0000cafe"}), encoding="utf-8")
    (root / "P1 - Wren" / "P1 Wren - EN & ES.xlsx").write_bytes(b"PK\x03\x04 a workbook stands in here")
    out.mkdir()
    into.mkdir()
    config_file = base / "config-330.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Sam", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    files = lambda at: {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*")) if p.is_file()}
    live = server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = config_file, None, {"recent": []}
        ids = {p["name"]: p["id"] for p in idiograph_routes.projects_view()["projects"]}
        idiograph_routes.api_send_project({"root": ids["Keeping bees"], "to": str(out / "Keeping bees")})
        idiograph_routes.api_open_sent({"file": str(out / "Keeping bees.idiograph"), "into": str(into)})
        copy = into / "Keeping bees"
        listed = idiograph_routes.projects_view()["projects"]
        copy_id = next((p["id"] for p in listed if p.get("copy")), None)
        original, held = files(root), files(copy)
        answer = idiograph_routes.api_projects({"op": "remove", "root": copy_id})
        after = [(p["name"], bool(p.get("copy"))) for p in answer["projects"]]
        check("330: Remove from Idiograph on the shared copy takes the copy off the list, the project it came from kept, "
              "and leaves the copy's folder and every file in it as they were",
              copy_id is not None and answer.get("removed") is True and answer.get("name") == "Keeping bees"
              and after == [("Keeping bees", False)] and files(copy) == held and files(root) == original,
              f"{[(p['name'], p.get('copy')) for p in listed]} {after}")
        answer = idiograph_routes.api_projects({"op": "remove", "root": ids["Keeping bees"]})
        check("330: Remove from Idiograph on the ordinary project leaves the list empty and its files as they were",
              answer.get("removed") is True and answer["projects"] == [] and files(root) == original, str(answer)[:300])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
    check("330: the live settings file is exactly as it was after Remove's checks",
          (server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None) == live)


def _remove_to_trash(scratch):
    """Remove from Idiograph, from Sift and from Trace with the card's tick (removetrash, Adam, 10 November 2026, about
    10:58, after removing a duplicate shared copy: "there should be a possibility ... I would have chosen to delete
    files and folders"): off by default the folder stays, ticked it goes to the system's Trash, here a stand-in folder
    of the suite's own and never the real Trash, each guard refuses with nothing moved or removed, a move the system
    refuses keeps the project in the list, the app's own record notes each removal, and an agent's `project remove
    --trash` runs at once since approvals were removed (noholds, 13 November 2026), the move recorded in the project's
    record of agents' changes, which goes to the Trash with the folder. Every fixture is invented, projects on keeping
    bees."""
    import os
    import cli
    import idiograph_mcp
    import idiograph_routes as routes
    import locks
    import server as server_mod
    import sift_routes
    import trace_routes
    import trash

    base = scratch / "trash-330"
    shutil.rmtree(base, ignore_errors=True)
    bin_dir = base / "stand-in bin"
    bin_dir.mkdir(parents=True)
    moved = []

    def stand_in(folder):
        """the system's Trash stood in for: the folder renamed into the suite's own bin, never deleted"""
        moved.append(Path(folder).name)
        os.rename(folder, bin_dir / Path(folder).name)
        return trash.where()

    def made(name, *, folder=None):
        root = folder or base / name
        (root / "P1 - Wren").mkdir(parents=True)
        (root / server_mod.PROJECT_FILE).write_text(json.dumps({
            "name": name, "research_question": "How do beekeepers live through a cold spring?",
            "agents": {"allowed": True, "at": "2026-11-10T09:00:00+00:00"}}), encoding="utf-8")
        (root / "P1 - Wren" / "notes.txt").write_text("Hive inspection, a calm colony.", encoding="utf-8")
        return root

    # every file of a folder by its contents, the locks set aside, which hold nothing
    files = lambda at: {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(Path(at).rglob("*"))
                        if p.is_file() and not p.name.endswith(".lock")}
    bees, swarm, apiary = made("Keeping bees"), made("Swarm season"), made("Apiary")
    hives = made("Apiary hives", folder=base / "Apiary" / "hives")
    held_files = files(bees)
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(p)} for p in (bees, swarm, apiary, hives)],
                                       "interviewer": "Sam", "corpus": "", "gravity_reference": "",
                                       "corpus_exclude": []}), encoding="utf-8")
    live = server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
            trash.TRASH, dict(server_mod.PAGES))
    refused = _refusal
    where = trash.where()
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = base / "state.json", {"recent": []}
        trash.TRASH = stand_in
        server_mod.PAGES.clear()
        ids = {p["name"]: p["id"] for p in routes.projects_view()["projects"]}
        names = lambda: [p["name"] for p in routes.projects_view()["projects"]]

        dry = routes.api_projects({"op": "remove", "root": ids["Keeping bees"], "trash": True, "dry_run": True})
        check("330: Remove's dry run with the tick names the project's folder and where it would go, and moves and "
              "removes nothing",
              dry.get("dry_run") is True and dry.get("removed") is False and Path(dry.get("folder", "")) == bees.resolve()
              and dry.get("where") == where and bees.is_dir() and "Keeping bees" in names() and not moved, str(dry)[:300])

        # another window in front of the project: refused, the page asking itself passed over
        server_mod.api_beat({"page": "OTHER", "at": ids["Keeping bees"]})
        other = refused(lambda: routes.api_projects({"op": "remove", "root": ids["Keeping bees"], "trash": True,
                                                     "page": "MINE"}))
        own = routes.api_projects({"op": "remove", "root": ids["Keeping bees"], "trash": True, "page": "OTHER",
                                   "dry_run": True})
        server_mod.api_beat({"page": "OTHER", "gone": True})
        check("330: a project open in another window is never moved to the Trash, the refusal plain and nothing removed, "
              "and the window asking is not counted as another",
              other == f"Keeping bees is open in another window, so nothing was moved to the {where} or removed. "
                       "Close it there and try again." and own.get("dry_run") is True
              and bees.is_dir() and "Keeping bees" in names() and "OTHER" not in server_mod.PAGES, other)

        # a writer holding the project's lock
        with locks.root(bees):
            busy = refused(lambda: routes.api_projects({"op": "remove", "root": ids["Keeping bees"], "trash": True}))
        check("330: a project being saved, its lock held, is never moved to the Trash, and nothing is removed",
              busy.startswith("Keeping bees is being saved right now") and bees.is_dir() and "Keeping bees" in names(), busy)

        # the system refusing the move
        def no_move(folder):
            raise OSError("The volume is read-only.")
        trash.TRASH = no_move
        failed = refused(lambda: routes.api_projects({"op": "remove", "root": ids["Keeping bees"], "trash": True}))
        trash.TRASH = stand_in
        check("330: a move the system refuses is said in a plain sentence of its own, the system's words to the log "
              "alone, and the project stays in the list with its folder where it was",
              failed == f"Its folder could not be moved to the {where}, so Keeping bees stays in the list."
              and bees.is_dir() and "Keeping bees" in names(), failed)

        # a folder holding another project
        nested = refused(lambda: routes.api_projects({"op": "remove", "root": ids["Apiary"], "trash": True}))
        check("330: a project whose folder holds another project is never moved to the Trash, naming the other",
              nested == f"Its folder holds another project, hives, so nothing was moved to the {where} or removed."
              and apiary.is_dir() and hives.is_dir() and "Apiary" in names(), nested)

        gone = routes.api_projects({"op": "remove", "root": ids["Keeping bees"], "trash": True, "page": "MINE"})
        check("330: Remove with the tick moves the project's folder to the Trash, every file in it as it was, takes the "
              "project off the list and answers where it went",
              gone.get("removed") is True and gone.get("trash") is True and gone.get("where") == where
              and not bees.exists() and files(bin_dir / "Keeping bees") == held_files and moved == ["Keeping bees"]
              and "Keeping bees" not in names(), str(gone)[:300])
        kept_answer = routes.api_projects({"op": "remove", "root": ids["Swarm season"]})
        check("330: Remove without the tick, the default, leaves the folder and every file in it as they were",
              kept_answer.get("removed") is True and kept_answer.get("trash") is False and swarm.is_dir()
              and moved == ["Keeping bees"] and "Swarm season" not in names(), str(kept_answer)[:300])
        record = trash.records(config_file)
        check("330: the app's own record beside its settings notes each removal, the project, its folder and whether "
              "the folder went to the Trash, and nothing of it is written in a project",
              [(r["name"], r["trash"], r["by"]) for r in record] == [("Keeping bees", True, "app"), ("Swarm season", False, "app")]
              and Path(record[0]["folder"]) == bees and trash.record_path(config_file).parent == base
              and not any(p.name.endswith(trash.RECORD_SUFFIX) for p in bin_dir.rglob("*")), str(record)[:300])

        # each guard of the folder, in one line, nothing moved
        home = base / "home"
        (home / "Documents").mkdir(parents=True)
        cloud = home / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
        cloud.mkdir(parents=True)
        app = base / "app"
        app.mkdir()
        (app / "config.json").write_text("{}", encoding="utf-8")
        guard = lambda folder, **kw: refused(lambda: trash.guard(folder, name="Hive", home=home, **kw))
        link = base / "link to swarm"
        try:
            link.symlink_to(swarm, target_is_directory=True)
            linked = guard(link)
        except (OSError, NotImplementedError):
            linked = "link"
        said = {"drive": guard(Path(Path.cwd().anchor)), "home": guard(home), "documents": guard(home / "Documents"),
                "cloud": guard(cloud), "app": guard(app, keep=[app / "config.json"]), "gone": guard(base / "nowhere"),
                "link": linked}
        check("330: the Trash's guard refuses a drive's top folder, the home folder and its own folders, a cloud drive's "
              "top folder, a folder holding the app's settings, one not there and a link, each in a plain line",
              said["drive"].startswith("Its folder is a whole drive") and said["home"].startswith("Its folder is, or holds, your home folder")
              and said["documents"] == said["home"] and said["cloud"].startswith("Its folder is a whole cloud drive")
              and said["app"].startswith("Its folder holds the app's own files") and said["gone"].startswith("Its folder is not there")
              and bool(said["link"]) and swarm.is_dir() and home.is_dir() and app.is_dir(), str(said))

        # Sift's and Trace's Remove the same way
        (base / "hedges").mkdir()
        (base / "pond").mkdir()
        review = sift_routes.api_sift_review({"op": "new", "folder": str(base / "hedges"), "name": "Hedge notes"})["review"]["folder"]
        project = trace_routes.api_trace_project({"op": "new", "folder": str(base / "pond"), "name": "Pond paper"})["project"]["folder"]
        sift_gone = sift_routes.api_sift_review({"op": "forget", "folder": review, "trash": True})
        trace_gone = trace_routes.api_trace_project({"op": "forget", "folder": project, "trash": True})
        check("330: Sift's and Trace's Remove with the tick move the project's folder to the Trash and take it off the "
              "list, saying where it went",
              sift_gone.get("trash") is True and sift_gone.get("where") == where and not Path(review).exists()
              and trace_gone.get("trash") is True and not Path(project).exists() and moved[-2:] == ["hedges", "pond"]
              and sift_gone["reviews"] == [] and trace_gone["traces"] == [], str([sift_gone, trace_gone])[:300])

        # an agent: project remove keeps the folder at once, and with --trash moves it to the Trash at once
        server_mod.PAGES.clear()
        hive = made("Hive diary")
        cfg = json.loads(config_file.read_text(encoding="utf-8"))
        cfg["projects"].append({"root": str(hive)})
        config_file.write_text(json.dumps(cfg), encoding="utf-8")

        def agent(*args):
            code, out, err = cli.run(["--config", str(config_file), "--json", "project", "remove", "--project",
                                      "Hive diary", *args])
            server_mod.CONFIG_PATH, server_mod.STATE_MEMORY = config_file, {"recent": []}
            return code, (support.plain(json.loads(out)) if out.strip() else {}), err

        code, plan, err = agent("--trash", "--dry-run")
        check("330: an agent's project remove --trash --dry-run names the folder and where it would go, moving nothing",
              code == 0 and plan.get("dry_run") is True and Path(plan.get("folder", "")) == hive.resolve()
              and plan.get("where") == where and hive.is_dir(), str([code, plan, err])[:300])
        code, gone, err = agent("--trash", "--note", "Clear out the duplicate diary", "--tool", "Claude Code")
        binned = bin_dir / "Hive diary" / "idiograph-agent-changes.jsonl"
        lines = [json.loads(x) for x in binned.read_text(encoding="utf-8").splitlines()] if binned.exists() else []
        check("330: an agent's project remove --trash moves the folder to the Trash at once and takes the project off "
              "the list, the app's record naming the agent, and the project's record of agents' changes, in the "
              "folder in the Trash, naming the move",
              code == 0 and gone.get("trash") is True and not hive.exists() and "Hive diary" in moved
              and "Hive diary" not in names()
              and trash.records(config_file)[-1]["by"].startswith("Claude Code")
              and [x.get("op") for x in lines] == ["project remove"] and lines[0]["undo_with"].get("trash") is True,
              str([code, gone, err, lines])[:400])
        tool = next((t for t in idiograph_mcp.TOOLS if t["name"] == "project_remove"), {})
        check("330: MCP's project_remove takes trash, the same op, and writes",
              tool.get("command") == ("project", "remove") and "trash" in tool["inputSchema"]["properties"]
              and tool["annotations"]["readOnlyHint"] is False, str(tool)[:300])
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
         trash.TRASH, pages) = kept
        server_mod.PAGES.clear()
        server_mod.PAGES.update(pages)
    check("330: the live settings file is exactly as it was after the Trash's checks",
          (server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None) == live)


def _sift_trace_menus(scratch, js):
    """Sift's and Trace's project menus (Adam, 6 November 2026, about 18:00, "Add a menu to both"): their cards' "..."
    and their band's name, on the family's code, the items that apply to them, and Show in Finder through each app's
    route, in node and through the routes on invented projects"""
    sset, trace = support.text("apps/sift/static/sift_settings.js"), support.text("apps/trace/static/trace.js")
    common = [whole(js, "function projectMenuHtml("), whole(js, "function projectMenuWord("), whole(js, "function projectDotsHtml("),
              line_of(js, "const trashWhere = "), line_of(js, "const pageId = "), whole(js, "function removedSaid(")]
    harness = support.i18n_js() + r"""
const MAC = true;
let APP_NAME = 'Sift';
let inWindow = true;
const windowPicks = () => inWindow;
const calls = [];
let LEAVES = true;
let screen = '';
const onScreen = (id) => id === screen;
const S = { lib: null };
const SFA = { want: null };
const TRP = { want: null };
let SF = { review: { folder: '/x/hedges', name: 'Hedge notes' } };
let SFS = { review: null };
let TR = { folder: '/x/pond', project: { name: 'Pond paper' } };
const TR_ROUTE = '/api/trace-project';
const $ = () => ({ title: '' });
const LINUX = false;
const window = { idiographPageId: 'PAGE-330' };
// Remove's card (removetrash) stood in, answering Remove with the tick off as he would
const askRemove = async (name) => { calls.push(['confirm', name]); return { trash: false }; };
const openSettings = (pane) => calls.push(['settings', pane, SFA.want || TRP.want]);
const goHome = async () => { calls.push(['home']); return LEAVES; };
const api = async (route, body) => { calls.push(['api', route, body.op, body.folder]); return { name: 'it' }; };
const loadLibrary = async () => { calls.push(['library']); };
const say = (t) => calls.push(['say', t]);
const needsRestart = () => false;
const RESTART_LINE = '';
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
""" + "\n".join(common + [whole(sset, "function siftMenuItems("), whole(sset, "function siftMenuRows("), whole(sset, "function siftMenuDo("),
                          whole(sset, "async function siftShowFolder("), whole(sset, "async function siftRemove("),
                          whole(sset, "function siftBandMenu("), whole(trace, "function traceMenuItems("),
                          whole(trace, "function traceMenuRows("), whole(trace, "function traceMenuDo("),
                          whole(trace, "async function traceShowFolder("), whole(trace, "async function traceRemove("),
                          whole(trace, "function traceBandMenu(")]) + r"""
(async () => {
  const out = {};
  const where = { window: true, mac: true };
  const words = (rows) => rows.map((r) => r.word);
  out.sift = { there: siftMenuItems({ folder: '/x/hedges', there: true }, where), browser: siftMenuItems({ folder: '/x/hedges', there: true }, { window: false }),
    gone: siftMenuItems({ folder: '/x/old', there: false }, where), words: words(siftMenuRows(['show', 'settings', 'remove'], where)),
    dots: projectDotsHtml('Hedge notes', siftMenuRows(['settings', 'remove'], where)) };
  const each = async (fn) => { calls.length = 0; await fn(); await new Promise((r) => setTimeout(r, 10)); return calls.slice(); };
  out.siftShow = await each(() => siftMenuDo('show', { folder: '/x/hedges', name: 'Hedge notes' }));
  out.siftSettings = await each(() => siftMenuDo('settings', { folder: '/x/hedges', name: 'Hedge notes' }));
  SFA.want = null;
  out.siftCard = await each(() => siftMenuDo('remove', { folder: '/x/hedges', name: 'Hedge notes' }));
  screen = 'sift';
  const band = siftBandMenu();
  out.siftBand = band && band.rows.map((r) => r.act);
  out.siftInside = await each(() => band.pick('remove'));
  screen = 'sift-search'; SFS = { review: null };
  out.siftNone = siftBandMenu();
  APP_NAME = 'Trace';
  out.trace = { there: traceMenuItems({ folder: '/x/pond', there: true }, where), gone: traceMenuItems({ folder: '/x/old', there: false }, where),
    words: words(traceMenuRows(['show', 'settings', 'remove'], { window: true, mac: false })) };
  screen = 'trace';
  const tband = traceBandMenu();
  out.traceBand = tband && tband.rows.map((r) => r.act);
  out.traceSettings = await each(() => tband.pick('settings'));
  TRP.want = null;
  LEAVES = false;
  out.traceKept = await each(() => tband.pick('remove'));
  LEAVES = true;
  out.traceShow = await each(() => traceMenuDo('show', { folder: '/x/pond', name: 'Pond paper' }));
  console.log(JSON.stringify(out));
})().catch((e) => { console.error(String(e && e.stack || e)); process.exit(1); });
"""
    run = support.run_node(harness, scratch, "sift-trace-330.js", timeout=60)
    o = json.loads(run.stdout.strip().splitlines()[-1]) if run.returncode == 0 and run.stdout.strip() else {}
    why = (run.stdout + run.stderr)[-600:]
    sift, tr = o.get("sift") or {}, o.get("trace") or {}
    check("330: in node, a Sift and a Trace project's menu holds Show in Finder in the app's own window, Project settings "
          "and Remove from Sift or Trace, Remove alone where the folder is gone, and no Share a copy or History, which "
          "neither app has, on a card's \"...\" by the family's code",
          sift.get("there") == ["show", "settings", "remove"] and sift.get("browser") == ["settings", "remove"]
          and sift.get("gone") == ["remove"] and sift.get("words") == ["Show in Finder", "Project settings", "Remove from Sift…"]
          and 'class="pc-dots hc-dots"' in sift.get("dots", "") and 'aria-label="More for Hedge notes"' in sift.get("dots", "")
          and tr.get("there") == ["show", "settings", "remove"] and tr.get("gone") == ["remove"]
          and tr.get("words") == ["Show in Explorer", "Project settings", "Remove from Trace…"], why)
    check("330: in node, Sift's and Trace's items do their jobs: Show in Finder asks the app's own route, Project settings "
          "opens Settings on Projects with that project in front, and Remove asks first, then takes it out of the list "
          "and draws Home, from the band leaving the screen as Home does first, a save that fails keeping it",
          o.get("siftShow") == [["api", "/api/sift-review", "reveal", "/x/hedges"]]
          and o.get("siftSettings") == [["settings", "sift", "/x/hedges"]]
          and [c[0] for c in o.get("siftCard") or []] == ["confirm", "api", "say", "library"]
          and o.get("siftBand") == ["show", "settings", "remove"]
          and [c[0] for c in o.get("siftInside") or []] == ["confirm", "home", "api", "say", "library"]
          and (o.get("siftInside") or [[]] * 3)[2][1:] == ["/api/sift-review", "forget", "/x/hedges"]
          and o.get("siftNone") is None and o.get("traceBand") == ["show", "settings", "remove"]
          and o.get("traceSettings") == [["settings", "trace", "/x/pond"]]
          and [c[0] for c in o.get("traceKept") or []] == ["confirm", "home"]
          and o.get("traceShow") == [["api", "/api/trace-project", "reveal", "/x/pond"]], why)
    check("330: Sift's and Trace's band names open their menus, wired by the family's bandMenuWire",
          "bandMenuWire('sf-name', () => siftBandMenu());" in support.text("apps/sift/static/sift.js")
          and "bandMenuWire('sfs-name', () => siftBandMenu());" in support.text("apps/sift/static/sift_search.js")
          and "bandMenuWire('tr-name', traceBandMenu);" in trace
          and "projectMenus(list, (act, li) => siftMenuDo(act," in sset and "projectMenus(list, (act, li) => traceMenuDo(act," in trace)

    # Show in Finder through Sift's and Trace's own routes, on invented projects, the Finder stood in for
    import server as server_mod
    import sift_routes
    import trace_routes
    base = scratch / "reveal-330"
    shutil.rmtree(base, ignore_errors=True)
    (base / "hedges").mkdir(parents=True)
    (base / "pond").mkdir()
    (base / "elsewhere").mkdir()
    cfg_file = base / "config.json"
    cfg_file.write_text(json.dumps({"projects": []}), encoding="utf-8")
    shown = []
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
            server_mod.PLATFORM, server_mod.SHOW_IN_FOLDER)
    refused = _refusal
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = base / "state.json", {"recent": []}
        server_mod.SHOW_IN_FOLDER = lambda folder: shown.append(Path(folder).name)
        server_mod.PLATFORM = "darwin"
        review = sift_routes.api_sift_review({"op": "new", "folder": str(base / "hedges"), "name": "Hedge notes"})["review"]["folder"]
        project = trace_routes.api_trace_project({"op": "new", "folder": str(base / "pond"), "name": "Pond paper"})["project"]["folder"]
        before = sorted(p.name for p in base.rglob("*"))
        sift_said = sift_routes.api_sift_review({"op": "reveal", "folder": review})
        trace_said = trace_routes.api_trace_project({"op": "reveal", "folder": project})
        strangers = [refused(lambda: sift_routes.api_sift_review({"op": "reveal", "folder": str(base / "elsewhere")})),
                     refused(lambda: trace_routes.api_trace_project({"op": "reveal", "folder": str(base / "elsewhere")}))]
        server_mod.PLATFORM = "freebsd"
        elsewhere = refused(lambda: sift_routes.api_sift_review({"op": "reveal", "folder": review}))
        after = sorted(p.name for p in base.rglob("*"))
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
         server_mod.PLATFORM, server_mod.SHOW_IN_FOLDER) = kept
    check("330: Show in Finder on a Sift and a Trace project shows its folder through the app's own route and writes "
          "nothing, a folder the list does not hold refused, and a machine that is neither a Mac nor Windows refused in "
          "one line",
          sift_said == {"revealed": True} and trace_said == {"revealed": True} and shown == ["hedges", "pond"]
          and all(strangers) and elsewhere == "Show in Finder is there on a Mac or Windows only." and before == after,
          str([sift_said, trace_said, shown, strangers, elsewhere]))


def _refusal(fn) -> str:
    """the line a refused request answers, or "" where it was not refused"""
    from workbook import WorkbookError
    import server as server_mod
    try:
        fn()
    except (WorkbookError, server_mod.OutsideRoot) as exc:
        return str(exc)
    return ""
