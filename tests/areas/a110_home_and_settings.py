from __future__ import annotations

import csv
import json
import re
import shutil

from . import support
from .support import TOOL, check, demo_copy, json_strings, refusal_of, skip
import idiograph_routes


def test_home_and_settings(scratch):
    print("\n110. The home screen a picker of Distil and Sift literature review, a project's page, Settings from the "
          "home screen opening on General with AI features first, each screen's settings on its own part, and the "
          "second part in folder names gone (9 October)")
    import base64
    import subprocess
    import server as server_mod
    import sift_routes
    import sift
    import sift_ai

    page = support.every_page()
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    # Sift's parts of the shell, from app.js since the family codebase's third build (22 October 2026)
    sset = support.text("apps/sift/static/sift_settings.js")
    sjs = support.text("apps/sift/static/sift.js")
    ssjs = support.text("apps/sift/static/sift_search.js")
    tjs = support.text("apps/idiograph/static/themes.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: (("async " if f"async function {name}(" in src else "") + f"function {name}(" + fn(src, name) + "\n}")
    node = shutil.which("node")

    # ── B. a project's page: its head with the way back, its GETs, its rows and Add transcripts
    check("110: a reload keeps where he was: the home screen's place in this tab, and the screen in front kept as the page goes",
          "try { sessionStorage.setItem(HOME_KEY, S.home); }" in fn(app, "homeKeep") and "const HOME_KEY = 'idiograph-home';" in app
          and "S.home = homeHeld();" in app and app.index("S.home = homeHeld();") < app.index("const spot = spotTaken();")
          and "window.addEventListener('pagehide', () => { if (!SERVER.busy && !S.noSpot) spotKeep(); });" in app)

    # the picker, a card, its page, the way back, a case's way back and --root, in node, on the page's own code
    if not node:
        skip("110: the picker and a project's page in node", "node is not installed")
    else:
        lines = app.splitlines()
        const = lambda name: next(ln for ln in lines if ln.startswith(f"const {name} = "))
        pieces = [const("esc"), const("escAttr"), const("plural"), const("HOME_KEY"), const("DEMO_ID"), const("homeHover"),
                  const("SHARE_LINE"), const("HOME_PROJECTS"), const("DEMO_TA_ID"), const("isDemoId"), const("DEMOS_OPEN"),
                  const("DEMOS_SHUT")]
        pieces += [whole(app, n) for n in ("sectionsOf", "homeHeld", "homeKeep", "drawHome", "standLine", "cardGetsLine", "homeCardHtml",
                                           "drawPick", "openPage", "openPageNow", "closePage", "pageHead", "drawPage", "demoRows",
                                           "demoCards", "drawDemoPage", "loadLibrary", "windowPicks", "windowRecent",
                                           "homeMenuItems", "homeMenuRows", "homeMenuHtml", "projectMenuHtml", "projectMenuWord",
                                           "projectDotsHtml", "distilHomeDraw", "distilRecent",
                                           "recentNames", "demosOf", "demosFold")]
        # Idiograph's Home through its hooks, the family's since the fifth build
        pieces.append(support.distil_hooks(app))
        # Sift's section of Home, Sift's own script's since the family codebase's third build
        pieces += [whole(sset, n) for n in ("reviewDay", "reviewDecided", "reviewLine", "reviewLines", "drawSiftHome",
                                            "siftMenuItems", "siftMenuRows")]
        script = scratch / "home-110.js"
        script.write_text(support.i18n_js() + r"""
const APP = 'idiograph';
// each app's own Home section is its own script's (trace.js), none on Idiograph's
const FAMILY_APPS = {};
// a card opens its page through Back and Forward's way in (area 234), which takes it at once here
const navGo = (again, open) => open();
function loadFamily() {}
// a card's dots and their menu (areas 232 and 240), wired by the page and not this stand-in
const MAC = true;
function homeMenus() {}
// and Sift's cards' dots, the family's (projectMenus in shell.js, barsD), wired by the page too
function projectMenus() {}
const APP_NAME = 'Idiograph';
const RESTART_LINE = 'Restart the server to finish this update.';
const store = {};
const sessionStorage = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); } };
const window = { scrollTo() {} };
const calls = { cards: [], gets: [], head: [], fold: [], added: [], opened: [] };
const els = {};
function parsed(html, attr) {
  const out = [];
  const re = new RegExp(attr + '="([^"]*)"', 'g');
  let m;
  while ((m = re.exec(html))) out.push(m[1]);
  return out;
}
function mk(id) {
  const e = { id, hidden: false, textContent: '', onclick: null, focused: 0, _html: '', _kids: null, attrs: {}, classes: new Set() };
  e.classList = { toggle: (c, on) => (on ? e.classes.add(c) : e.classes.delete(c)), contains: (c) => e.classes.has(c) };
  e.setAttribute = (k, v) => { e.attrs[k] = v; };
  e.focus = () => { e.focused += 1; };
  Object.defineProperty(e, 'innerHTML', { get: () => e._html, set: (v) => { e._html = v; e._kids = null; } });
  e.querySelectorAll = (sel) => {
    if (!e._kids) {
      const attr = sel === '.home-card' ? 'data-id' : 'data-i';
      e._kids = parsed(e._html, attr).map((v) => ({ dataset: attr === 'data-id' ? { id: v } : { i: v }, onclick: null, focused: 0,
        focus() { this.focused += 1; } }));
    }
    return e._kids;
  };
  return e;
}
const $ = (id) => els[id] || (els[id] = mk(id));
const S = { home: null, lib: null, libConfig: null, chooseRoot: false, oneRun: false };
let libraryAsk = 0;
let reply = null;
async function api(path) { return JSON.parse(JSON.stringify(reply)); }
function aiPage() {}
function drawFeedback() {}
function loadDays() {}
function homeHoldsRead() {}
function foldable(section, head, id) { calls.fold.push(id); }
function shutIds() { return []; }
function keepFold() {}
function drawCards(list, cards, where) { calls.cards.push([list.id, cards.map((c) => c.case + (c.demo ? '*' : '')), where]); }
function drawGetsCard(box, gets) { calls.gets.push([box.id, gets ? gets.path : null]); }
function drawGetsHead(box, path, still) { calls.head.push([box.id, path, still()]); }
function openAddTranscripts(id) { calls.added.push(id); }
function rvOpen(folder) { calls.opened.push(folder); }
function trOpen(folder) { calls.opened.push(folder); }
function cardsFrom() { return []; }
""" + "\n".join(pieces) + r"""
const part = (c, done, total, pets) => ({ case: c, turns: { done, total }, pets_complete: pets ? { at: 'x' } : null });
const data = {
  config: {}, choose: true, one: false,
  projects: [
    { id: 'ROOT-SWIM', there: true, project: { name: 'Learning to swim', research_question: 'How do adults experience a first length?' },
      participants: [part('P1 - Fern', 10, 40, true), part('P2 - Moss', 20, 60, false)], gets: { path: 'swim/gets', done: null } },
    { id: 'ROOT-GONE', there: false, project: { name: 'Kite flying', research_question: '' }, participants: [], gets: null },
  ],
  demos: [{ path: 'demo/Juno' }, { path: 'demo/Rowan' }, { path: 'demo/Mabel' }],
  demo_participants: [part('Juno', 6, 39, false), part('Rowan', 30, 30, true), part('Mabel', 25, 25, true)],
  demo_project: { name: 'Living with a dog', research_question: 'How do people experience sharing a home with a dog?' },
  reviews: [{ name: 'Heron counts', where: 'reviews', folder: 'reviews/Heron counts', there: true, searches: false,
              stages: { ta: { decided: 1, records: 4, undecided: 3 }, ft: {} } }],
};
const shown = () => ({ pick: !$('home-pick').hidden, page: !$('home-project').hidden, home: S.home });
(async () => {
  const out = {};
  reply = data;
  await loadLibrary();
  out.picker = shown();
  out.cardsHtml = $('projects').innerHTML;
  out.demosHtml = $('demo-projects').innerHTML;
  out.demosShut = $('home-demos').classes.has('shut');
  out.siftHtml = $('sift-list').innerHTML;
  out.npHidden = $('np-line').hidden;
  out.folds = calls.fold.slice();
  out.lines = [standLine(data.projects[0].participants, data.projects[0].gets), standLine([], null), standLine([], null, false),
    standLine([{ case: 'x', boards: 2 }]), cardGetsLine(null), cardGetsLine({ done: null }), cardGetsLine({ done: null, themes: 4 }),
    cardGetsLine({ done: { at: 'x' }, themes: 4 }), cardGetsLine({ themes: 1 })];
  $('projects').querySelectorAll('.home-card')[0].onclick();
  out.page = shown();
  out.kept = store['idiograph-home'];
  out.head = [$('hp-name').textContent, $('hp-question').textContent, $('hp-question').hidden, $('hp-demo').hidden];
  out.pageParts = [calls.cards.slice(-1)[0], calls.gets.slice(-1)[0], $('hp-transcripts').hidden, $('demo-reset').hidden,
    $('hp-back').focused];
  $('hp-transcripts').onclick();
  out.added = calls.added.slice();
  closePage();
  out.back = shown();
  out.backFocus = $('projects').querySelectorAll('.home-card')[0].focused;
  openPage('ROOT-SWIM');
  await loadLibrary();
  out.caseBack = [shown(), $('hp-name').textContent];
  openPage('demo');
  out.demo = [shown(), $('hp-name').textContent, $('hp-demo').hidden, $('demo-reset').hidden, $('hp-transcripts').hidden,
    calls.cards.slice(-1)[0], calls.head.slice(-1)[0]];
  openPage('ROOT-GONE');
  out.gone = [$('hp-list').innerHTML, $('hp-transcripts').hidden];
  S.home = 'ROOT-NOT-THERE';
  drawHome();
  out.missing = shown();
  drawSiftHome(data);
  out.siftOwn = $('sift-list').innerHTML;
  $('sift-list').querySelectorAll('.sf-row-open')[0].onclick();
  out.siftOpened = calls.opened.slice();
  S.home = null;
  reply = Object.assign({}, data, { one: true });
  await loadLibrary();
  out.root = shown();
  closePage();
  await loadLibrary();
  out.rootBack = [shown(), $('np-line').hidden];
  out.held = homeHeld();
  console.log(JSON.stringify(out));
})();
""", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        if run.returncode != 0:
            check("110: the home screen runs in node", False, run.stderr.strip()[:500])
        else:
            o = json.loads(run.stdout)
            check("110: in node, the picker draws a card for each project in order and the demo's apart in Demo projects, "
                  "folded, with its IPA demo tag (demos, 3 November 2026), each with its question and its line, and on "
                  "Idiograph's page no Sift section (20 October)",
                  o["picker"] == {"pick": True, "page": False, "home": None}
                  and o["cardsHtml"].index("Learning to swim") < o["cardsHtml"].index("Kite flying")
                  and "Living with a dog" not in o["cardsHtml"] and "Living with a dog" in o["demosHtml"]
                  and o["cardsHtml"].count('class="home-card"') == 2 and o["demosHtml"].count('<span class="tag demo">IPA demo</span>') == 1
                  and o["demosShut"] is True
                  and "How do adults experience a first length?" in o["cardsHtml"] and "2 participants, 1 with PETs" in o["cardsHtml"]
                  and "GETs not started" in o["cardsHtml"] and o["cardsHtml"].count('class="pc-line hc-more"') == 1
                  and "Its folder is not there" in o["cardsHtml"] and "3 participants, 2 with PETs" in o["demosHtml"]
                  and o["siftHtml"] == "" and "Heron counts" in o["siftOwn"] and "1 of 4 records decided" in o["siftOwn"]
                  and o["npHidden"] is False and o["folds"] == ["analysis"], str(o["picker"]) + o["cardsHtml"][:300])
            check("110, updated 21 October (223, the split's pages): in node, a project's card counts its participants and those "
                  "with PETs, a board or PETs marked complete, then its GETs, not started, its group themes or complete, "
                  "and says when it has no participant",
                  o["lines"] == ["2 participants, 1 with PETs", "No participants yet", "Its folder is not there",
                                 "1 participant, 1 with PETs", "", "GETs not started", "GETs: 4 group themes",
                                 "GETs complete", "GETs: 1 group theme"], str(o["lines"]))
            check("110: in node, a card opens its project's page, kept in this tab, its head, GETs, rows and Add transcripts, "
                  "the way back focused",
                  o["page"] == {"pick": False, "page": True, "home": "ROOT-SWIM"} and o["kept"] == "ROOT-SWIM"
                  and o["head"] == ["Learning to swim", "How do adults experience a first length?", False, True]
                  and o["pageParts"][0] == ["hp-list", ["P1 - Fern", "P2 - Moss"], {"id": "ROOT-SWIM"}]
                  and o["pageParts"][1] == ["hp-gets", "swim/gets"] and o["pageParts"][2:4] == [False, True]
                  and o["pageParts"][4] >= 1 and o["added"] == ["ROOT-SWIM"], str(o["page"]) + str(o["pageParts"]))
            check("110: in node, the page's way back opens the picker with its card focused, and a case's way back lands on "
                  "its project's page",
                  o["back"] == {"pick": True, "page": False, "home": ""} and o["backFocus"] >= 1
                  and o["caseBack"] == [{"pick": False, "page": True, "home": "ROOT-SWIM"}, "Learning to swim"], str(o["caseBack"]))
            check("110: in node, the demo's card opens its page with the tag, its fixed rows, its GETs asked and Reset demo, "
                  "and no Add transcripts",
                  o["demo"][0] == {"pick": False, "page": True, "home": "demo"} and o["demo"][1] == "Living with a dog"
                  and o["demo"][2:5] == [False, False, True]
                  and o["demo"][5] == ["hp-list", ["Juno*", "Rowan*", "Mabel*"], {"fixed": True}]
                  and o["demo"][6] == ["hp-gets", "demo/Juno", True], str(o["demo"]))
            check("110: in node, a project whose folder is gone says so on its page with no Add transcripts, one gone from the "
                  "list is the picker again, and a Sift card opens its project",
                  o["gone"] == ['<li class="empty">Its folder is not there.</li>', True]
                  and o["missing"] == {"pick": True, "page": False, "home": ""}
                  and o["siftOpened"] == ["reviews/Heron counts"], str(o["gone"]) + str(o["missing"]))
            check("110: in node, a run with --root opens on its one project's page with New project hidden, and once he goes "
                  "back the home screen stays the picker",
                  o["root"] == {"pick": False, "page": True, "home": "ROOT-SWIM"}
                  and o["rootBack"] == [{"pick": True, "page": False, "home": ""}, True] and o["held"] == "", str(o["root"]))

    # ── C. Settings: General first with AI features and its warning, Distil's three parts, Sift and Projects
    card = page.split('<div class="overlay" id="settings"', 1)[1].split('<div class="overlay"', 1)[0]
    sift_pane = card.split('id="pane-sift"', 1)[1].split("</section>", 1)[0]
    every_id = re.findall(r'(?<![\w-])id="([^"]+)"', page)
    dupes = sorted({i for i in every_id if every_id.count(i) > 1})
    check("110: Sift's AI proposals in Settings follow the switch, the rest of Sift's part outside it, read only once the "
          "switch is on and saved only while it is, and no id twice in the page (9 October)",
          '<div id="sfa-block" data-ai-set>' in sift_pane
          and "data-ai" not in sift_pane.split('<div id="sfa-block"', 1)[0]
          and not dupes
          # each through Sift's own part of the shell (sift_settings.js) since the family codebase's third build
          and "if (FAMILY_APPS[APP] && FAMILY_APPS[APP].aiLoad) FAMILY_APPS[APP].aiLoad();" in fn(app, "aiSetLoad")
          and "aiLoad: sfaLoad" in sset and "sfaLoad" not in fn(app, "openSettings")
          and "if (a.settingsReset) a.settingsReset();" in fn(app, "openSettings") and "settingsReset: sfaReset" in sset
          and "if (own && own.settingsLoad) own.settingsLoad();" in fn(app, "openSettings") and "settingsLoad: sfpLoad" in sset
          and "if (!$('set-ai').checked) return [];" in fn(sset, "sfaSaves"), str(dupes))
    check("110: every screen's own settings open Settings on their part: the turn screen's cog, the PETs and GETs cogs "
          "on PETs (settingsplit), Sift's cog on Sift, the searches' cogs in place, the home screen's Settings, and the "
          "band's link Project settings",
          "$('btn-settings').onclick = () => openSettings();" in app
          and "$('th-settings').onclick = () => openSettings('pets');" in fn(tjs, "gtScreen")
          and "$('sf-settings').onclick = () => openSettings('sift');" in sjs and "sfSetOpen" not in sjs
          and ssjs.count("openSettings(") == 1 and "$('sfs-settings').onclick = () => openSettings('databases');" in ssjs
          and "openProjectSettings(project())" in app
          and "$('lib-settings').onclick = () => openSettings('general');" in app
          and "const PANE_OF = { proposals: 'sift' };" in app)
    check("110: Settings over Sift keeps its own keys, Sift's screen hearing none of them, and so does Send feedback's "
          "card since every bar carries the bug (16 October)",
          "if (!sfShown() || !$('settings').hidden || !$('feedback').hidden) return;" in fn(sjs, "sfKeyDown")
          and "if (!sfsShown() || ($('settings') && !$('settings').hidden) || ($('feedback') && !$('feedback').hidden)) return;"
          in fn(ssjs, "sfsKeyDown"))
    check("110: over the home screen Settings has no case, a project's page gives its project, and Settings holds the "
          "app's own settings alone, no Export, GETs or Projects (settingsplit)",
          "btn-export" not in app and "distilSettingsLast" not in app
          and "if (!$('library').hidden) {" in fn(app, "distilSettingsCase")
          and "const own = homeProject();" in fn(app, "distilSettingsCase")
          and "loadGetsPane(ta ? null : getsTarget(shown));" in fn(app, "openProjectSettings")
          and "if (overHome) { loadLibrary().catch((err) => say(err.message, 9000)); return; }" in fn(app, "saveSettings")
          and "if (S.data && (onScreen('work') || ctx.themes)) {" in fn(app, "distilSettingsAfter"))
    unnamed = []
    pages = [p for folder in support.static_folders() for kind in ("*.js", "*.html") for p in folder.glob(kind)]
    for path in sorted(pages + support.code_files("*.py")):
        for n, ln in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"chosen in [Ss]ettings(?!,)", ln) or re.search(r"Turn them on in (Settings|Sift's settings)\.", ln):
                unnamed.append(f"{path.name}:{n}")

    # the part each screen opens on, and the names a caller gives, in node
    if not node:
        skip("110: the category each screen opens on in node", "node is not installed")
    else:
        lines = app.splitlines()
        pieces = ["const APP = 'idiograph';", "const PANES_BY_APP = {" + app.split("const PANES_BY_APP = {", 1)[1].split("};", 1)[0] + "};",
                  next(ln for ln in lines if ln.startswith("const PANES_ALL = ")),
                  next(ln for ln in lines if ln.startswith("const PANES = ")), "let paneHeld = 'general';",
                  next(ln for ln in lines if ln.startswith("const onScreen = ")),
                  next(ln for ln in lines if ln.startswith("const PANE_OF = ")), whole(app, "screenPane"), whole(app, "showPane"),
                  # Idiograph's screens' categories through its hook (the fifth build)
                  "const FAMILY_APPS = {};", whole(app, "distilScreenPane"), support.distil_hooks(app)]
        script = scratch / "panes-110.js"
        script.write_text(support.i18n_js() +
            "const els = {};\n"
            "const $ = (id) => els[id] || (els[id] = { id, hidden: true, scrollTop: 5 });\n"
            "const tabs = ['general', 'formats', 'statements', 'pets', 'ai'].map((p) => ({ dataset: { pane: p }, cls: new Set(),\n"
            "  attrs: {}, tabIndex: -1, classList: { toggle(c, on) {} }, setAttribute(k, v) { this.attrs[k] = v; }, focus() {} }));\n"
            "const document = { querySelectorAll: () => tabs };\n"
            + "\n".join(pieces) + "\n"
            "const screens = ['library', 'work', 'themes', 'sift', 'sift-search'];\n"
            "const on = (id) => { for (const s of screens) $(s).hidden = s !== id; return screenPane(); };\n"
            "const opened = screens.map(on);\n"
            "for (const s of screens) $(s).hidden = s !== 'library';\n"
            "const named = ['databases', 'proposals', 'gets', 'ai', 'project', 'nonsense'].map((n) => { showPane(n);\n"
            "  return [paneHeld, PANES.filter((p) => !$('pane-' + p).hidden), tabs.filter((t) => t.attrs['aria-selected'] === 'true').map((t) => t.dataset.pane)]; });\n"
            "console.log(JSON.stringify({ opened, named }));\n", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        if run.returncode != 0:
            check("110: the categories run in node", False, run.stderr.strip()[:400])
        else:
            o = json.loads(run.stdout)
            check("110: in node, Settings opens on General over the home screen, Experiential statements over a case, PETs "
                  "over PETs, Projects over Sift and Databases over its searches",
                  o["opened"] == ["general", "statements", "pets", "sift", "databases"], str(o["opened"]))
            check("110: in node, on Idiograph's page another app's category opens General, ai AI features, a category "
                  "itself, and any other name the screen's own, GETs and Projects among them since they left Settings "
                  "(settingsplit), one pane and one tab shown each time",
                  [n[0] for n in o["named"]] == ["general", "general", "general", "ai", "general", "general"]
                  and all(n[1] == [n[0]] and n[2] == [n[0]] for n in o["named"]), str(o["named"]))

    # ── D. the server: the second part gone, a two-part folder still a case, --root, and Sift's AI settings read
    base = scratch / "home-110"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    cfg_file = scratch / "home-110-config.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "Kit", "ai_suggest": False}), encoding="utf-8")
    live_config = server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    talk = ("Kit: [00:00:03] What was the first length like?\nIvo Invented: [00:00:08] Long. I stopped twice.\n"
            "Kit: [00:00:40] And the second week?\nIvo Invented: [00:00:44] I stopped once, at the deep end.\n")
    file_of = lambda who, more=None: dict({"name": "lesson.txt", "data": base64.b64encode(talk.encode("utf-8")).decode("ascii"),
                                           "pseudonym": who, "interview": "Lesson", "interviewer": "Kit"}, **(more or {}))
    reed = "Re" + "ed"
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "home-110-state.json", {"recent": []}
        # New project, sent the two-part setting and a second part by a page from before: neither is taken
        pool = base / "Learning to swim"
        pool.mkdir()
        made = idiograph_routes.api_new_project({"op": "make", "folder": str(pool), "name": "Learning to swim",
                                           "research_question": "How do adults experience a first length?",
                                           "second_part": True, "files": [file_of("Fern", {"second": reed})]})
        held = json.loads((pool / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
        check("110: New project makes `P<n> - Pseudonym` and writes no second part, in the folder or the project file",
              sorted(p.name for p in pool.iterdir() if p.is_dir()) == ["P1 - Fern"] and made["cases"] == ["P1 - Fern"]
              and "second_part" not in held and set(held) == {"name", "research_question", "updated", "method"}
              and not any(reed in str(p) for p in pool.rglob("*")), str(sorted(held)))
        # his own folder with a second part, as GRAVITY's carry one, built here by concatenation
        two = pool / ("P2 - Moss" + "-" + reed)
        demo_copy(two, "P2 Moss - EN & ES.xlsx")
        root_id = made["project"]["id"]
        card = idiograph_routes.api_add_transcripts({"op": "project", "root": root_id})
        added = idiograph_routes.api_add_transcripts({"op": "add", "root": root_id,
                                                "files": [file_of("Heron", {"second": reed, "number": 3})]})
        check("110: Add transcripts asks no second part, makes `P<n> - Pseudonym` whatever a page from before sends, and "
              "lists a two-part folder by its label alone",
              "second_part" not in card and card["cases"] == [{"label": "P1 - Fern", "pseudonym": "Fern"},
                                                               {"label": "P2 - Moss", "pseudonym": "Moss"}]
              and added["cases"] == ["P3 - Heron"] and (pool / "P3 - Heron").is_dir()
              and not any(reed in p.name for p in pool.iterdir() if p.name != two.name), str(card))
        # a project file from before, holding the old key, read without error and the key passed over
        held["second_part"] = True
        (pool / server_mod.PROJECT_FILE).write_text(json.dumps(held), encoding="utf-8")
        project = idiograph_routes.read_project(pool)
        listed = idiograph_routes.api_cases({})
        section = next(s for s in listed["projects"] if s["id"] == root_id)
        moss = next(c for c in section["participants"] if c["case"] == "P2 - Moss")
        opened = idiograph_routes.api_open({"path": moss["path"]})
        shown = list(json_strings(listed, ("path", "suggested", "id", "root"))) + [opened["name"], opened["case"] if "case" in opened else ""]
        check("110: a project file holding second_part is read without error and the key ignored, and the two-part folder "
              "is listed, opened and shown by its pseudonym alone",
              "second_part" not in project and project["name"] == "Learning to swim"
              and [c["case"] for c in section["participants"]] == ["P1 - Fern", "P2 - Moss", "P3 - Heron"]
              and server_mod.display_case(two.name) == "P2 - Moss" and opened["sheets"]
              and not any(reed in s for s in shown), str([c["case"] for c in section["participants"]]))
        # --root: a run of one project, which the page opens on its page
        server_mod.ROOT_OVERRIDE = str(pool)
        one = idiograph_routes.api_cases({})
        server_mod.ROOT_OVERRIDE = None
        check("110: a run with --root says so to the page, its one project's section first and alone",
              one["one"] is True and len(one["projects"]) == 1 and one["projects"][0]["project"]["name"] == "Learning to swim",
              str(one["one"]))
        # Sift's AI proposals in Settings: each card names its newest screening, and its settings are read whatever the switch
        ponds = base / "Pond screening"
        ponds.mkdir()
        with open(ponds / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["rec_id", "title", "abstract"])
            w.writerow(["P001", "Moss on a garden pond edge", "Volunteers counted moss cushions over one summer."])
        server_mod.STATE_MEMORY = {"recent": [], "sift_reviews": [{"folder": str(ponds), "opened": 1}]}
        before = sorted(p.name for p in ponds.iterdir())
        rows = sift_routes.review_rows()
        read_off = sift_routes.api_sift({"op": "ai", "folder": str(ponds)})
        refused_off = refusal_of(lambda: sift_routes.api_sift({"op": "settings", "folder": str(ponds), "ai_proposals": True}))
        check("110: a Sift card carries its newest screening, and Settings reads its AI settings with the switch off, "
              "writing nothing, while a save waits for the switch",
              server_mod.same_folder(server_mod.abs_path(rows[0]["screening"]), ponds)
              and read_off["ai"]["on"] is False and read_off["ai"]["prompt"] == sift_ai.DEFAULT_PROMPT
              and read_off["ai"]["default"] == sift_ai.DEFAULT_PROMPT and read_off["ai"]["model_name"]
              and sorted(p.name for p in ponds.iterdir()) == before and refused_off == sift_ai.OFF, str(read_off))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept
    check("110: the live config.json is exactly as it was",
          (server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None) == live_config)
