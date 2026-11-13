from __future__ import annotations

import inspect
import json
import re
import shutil

import ai_suggest as ai_mod

from . import support
from .support import check, skip
import idiograph_routes


def test_ai_switch(scratch):
    print("\n100. AI features: one switch for every AI feature, off on a new install, its warning and its confirm, "
          "nothing of the AI anywhere with it off, and every feature as before with it on")
    import html.parser
    import subprocess
    import server as server_mod
    import themes_ai

    page = support.every_page()
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    tjs = support.text("apps/idiograph/static/themes.js")
    style = support.text("family/static/style.css", "apps/idiograph/static/distil.css")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    SPARKLES = 'M12 3.2c.95 4.2 2.65 5.9 6.85 6.85'
    AI_WORDS = re.compile(r"\bAI\b|\bagents?\b|Claude|Anthropic|Ollama|API key|\bMCP\b")

    # ── A. the key: off on a new install, a saved value kept, the old name still read
    real = (server_mod.CONFIG_PATH, server_mod.save_json, ai_mod.find_key, ai_mod.http_call)
    home = scratch / "ai-switch"
    home.mkdir(parents=True, exist_ok=True)
    sent = []

    def wire(method, url, headers, payload, timeout):
        sent.append(url)
        body = {"tags": ["lead"], "candidates": ["Walks before the town wakes"]}
        return 200, json.dumps({"content": [{"type": "text", "text": json.dumps(body)}], "stop_reason": "end_turn"})

    try:
        server_mod.CONFIG_PATH = home / "config.json"
        fresh = server_mod.config()
        check("100: a new install, with no settings file, starts with AI features off",
              server_mod.defaults()["ai_suggest"] is False and fresh["ai_suggest"] is False
              and server_mod.merge_config({})["ai_suggest"] is False and not server_mod.CONFIG_PATH.exists())
        server_mod.CONFIG_PATH.write_text(json.dumps({"ai_suggest": True, "interviewer": "Wren"}), encoding="utf-8")
        server_mod.api_settings({"interviewer": "Wren", "round_minutes": 10})
        kept_on = json.loads(server_mod.CONFIG_PATH.read_text(encoding="utf-8"))["ai_suggest"]
        server_mod.CONFIG_PATH.write_text(json.dumps({"ai_suggest": False}), encoding="utf-8")
        server_mod.api_settings({"interviewer": "Wren"})
        kept_off = json.loads(server_mod.CONFIG_PATH.read_text(encoding="utf-8"))["ai_suggest"]
        check("100: a saved settings file keeps the value it has, on or off, through a save that does not send it",
              kept_on is True and kept_off is False, str((kept_on, kept_off)))
        server_mod.CONFIG_PATH.write_text(json.dumps({"haiku": True}), encoding="utf-8")
        legacy = server_mod.config()["ai_suggest"]
        server_mod.api_settings({"haiku": False})
        written = json.loads(server_mod.CONFIG_PATH.read_text(encoding="utf-8"))
        check("100: the old `haiku` key is still read, never beats `ai_suggest`, and a save drops it",
              legacy is True and server_mod.merge_config({"haiku": True, "ai_suggest": False})["ai_suggest"] is False
              and written.get("ai_suggest") is False and "haiku" not in written, str(written.get("ai_suggest")))

        # ── B. the server asks no model with it off
        ai_mod.find_key = lambda *a, **kw: "k-invented"
        ai_mod.http_call = wire
        server_mod.CONFIG_PATH.write_text(json.dumps({"ai_suggest": False, "ai_provider": "anthropic"}), encoding="utf-8")
        turn = {"turn": "I walk the dog before anyone is up.", "prior": "And the mornings?", "path": str(server_mod.DEMO_WORKBOOK)}
        off = idiograph_routes.api_suggest(dict(turn))
        refused = not sent
        server_mod.CONFIG_PATH.write_text(json.dumps({"ai_suggest": True, "ai_provider": "anthropic"}), encoding="utf-8")
        on = idiograph_routes.api_suggest(dict(turn))
        check("100: AI suggest under the statement field is refused with the switch off, nothing sent, and answers with it on",
              off == {"error": themes_ai.OFF} and refused and on.get("candidates") == ["Walks before the town wakes"]
              and len(sent) == 2, str(off))
        guarded = [inspect.getsource(f) for f in (idiograph_routes.api_suggest, idiograph_routes.api_themes_ai, idiograph_routes.api_gets_ai)]
        check("100: every route the page asks a model through checks the switch first, and the line names AI features",
              all(re.search(r'if not srv\.ai_on\(cfg, "(statements|pets|gets)"\):\n        return \{"error": themes_ai.OFF\}', g) for g in guarded)
              and themes_ai.OFF == "AI features are off. Turn them on in Settings, AI features.")
    finally:
        server_mod.CONFIG_PATH, server_mod.save_json, ai_mod.find_key, ai_mod.http_call = real

    # ── C. the switch, its label and its warning
    keys = app.split("// AI features' confirm card over Settings", 1)[1].split("\n    if (e.key === 'Escape') {\n", 1)[0] if "AI features' confirm" in app else ""
    check("100: Enter and Esc keep it off unless I understand the risks has the focus, ahead of the Esc that closes every card, and the card counts as one",
          "if (e.key === 'Escape') { e.preventDefault(); aiConfirm(false); }" in keys
          and "else if (e.key === 'Enter') { e.preventDefault(); aiConfirm(e.target === $('ai-confirm-go')); }" in keys
          and "'settings', 'ai-confirm'," in app and "$('set-ai').onchange = () => aiSwitch();" in app
          and "$('ai-confirm-go').onclick = () => aiConfirm(true);" in app
          and "$('ai-confirm-cancel').onclick = () => aiConfirm(false);" in app)

    # ── D. the markup: every AI word and every sparkles icon sits in a part that follows the switch
    class Walk(html.parser.HTMLParser):
        VOID = {"input", "br", "img", "meta", "link", "hr", "source", "path", "circle", "rect", "line", "polyline"}

        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.stack, self.found, self.after_switch = [], [], False

        def routed(self):
            return any("data-ai" in a or "data-ai-set" in a for _t, a in self.stack)

        def where(self):
            return [a.get("id") or t for t, a in self.stack if a.get("id")]

        def note(self, what):
            self.found.append((what, self.routed(), self.where()))

        def handle_starttag(self, tag, attrs):
            a = dict(attrs)
            if tag not in self.VOID:
                self.stack.append((tag, a))
            said = " ".join(str(a.get(k) or "") for k in ("title", "aria-label", "placeholder", "value"))
            if AI_WORDS.search(said):
                self.note(said)
            if SPARKLES in str(a.get("d") or ""):
                self.note("sparkles")
            self.after_switch = tag == "input" and a.get("id") == "set-ai"

        handle_startendtag = handle_starttag

        def handle_endtag(self, tag):
            while self.stack:
                if self.stack.pop()[0] == tag:
                    break

        def handle_data(self, data):
            # a script's text is no word on screen: the catalogue the page carries inline for its scripts
            # (i18ncore, 28 October 2026) holds every message, each checked where its marker or script puts it
            if self.stack and self.stack[-1][0] in ("script", "style"):
                return
            if AI_WORDS.search(data):
                self.note("switch" if self.after_switch and data.strip() == "AI features" else data.strip())
            if data.strip():
                self.after_switch = False

    walk = Walk()
    walk.feed(re.sub(r"<!--.*?-->", "", page, flags=re.S))
    # the switch and its warning, and Sift's own "with AI", which records who proposed a decision and
    # which Sift's builder keeps, are the only AI words that show whatever the switch, with About's
    # acknowledgement of the model Idiograph was made with, a credit and no feature (20 October)
    # and AI features' own category, its tab and its title, where the switch stands (the split's third build)
    allowed = lambda what, ids: (what == "switch" or "ai-sub" in ids or "ai-warn" in ids or "ai-confirm" in ids
                                 or "tab-ai" in ids or (what.startswith("AI features") and ids[-1:] == ["pane-ai"])
                                 or "about" in ids
                                 # Using your own AI agent, at the end of AI features, shown whatever the switch
                                 # says, since an agent works without the app's own AI (Adam, 21 October 2026)
                                 or "agent-start" in ids
                                 # and the agent log's sheet, a record of agents shown whatever the switch, as
                                 # Using your own AI agents is (agentlog, 3 November 2026)
                                 or "agent-log-sheet" in ids
                                 # and Project history's By an agent, the record of who made a change (historyui)
                                 or "project-history" in ids
                                 # and the Support card's words on how the app is made, as About's credit is:
                                 # Contribute code's "by hand or with AI" and Fund it's Claude Code among the
                                 # costs, words about the code and the bills, no feature (supportcard2, 29 October)
                                 or "support" in ids
                                 or any(i == "sift" or i.startswith("sf-") for i in ids))
    loose = [(w, ids[-1:]) for w, routed, ids in walk.found if not routed and not allowed(w, ids)]
    check("100: every AI word, tooltip and label in the markup sits under data-ai or data-ai-set, the switch and its warning aside",
          len(walk.found) >= 30 and not loose, f"{len(walk.found)} found, loose: {loose[:4]}")
    sparkled = [ids for w, routed, ids in walk.found if w == "sparkles"]
    check("100: the sparkles in the markup are on the AI controls alone, each under data-ai or data-ai-set",
          len(sparkled) == 2 and all(routed for w, routed, _ids in walk.found if w == "sparkles")
          and page.count(SPARKLES) == 2 and SPARKLES not in app, str(sparkled))
    marked = {m.group(1): m.group(0) for m in re.finditer(r'<[a-z0-9]+[^>]*\bid="([\w-]+)"[^>]*\bdata-ai\b(?!-)[^>]*>', page)}
    check("100: data-ai marks the turn's AI block and the n row of the shortcuts, the two AI tabs and New AI board's card "
          "gone since aiout",
          {"ai-block"} <= set(marked) and "th-aicard" not in marked
          and 'data-tab="review"' not in page and 'data-tab="revise"' not in page
          and '<tr data-ai><td class="mono">N</td><td>AI suggest PET titles</td></tr>' in page, str(sorted(marked)))

    # ── E. the scripts: every line that shows an AI word or the sparkles answers to the switch
    # a key of the catalogue (i18ncore, 28 October 2026) read as the English it shows, so a word moved into the
    # catalogue is still found where the script puts it
    import i18n
    english = i18n.messages("en")

    def strings_of(line):
        line = re.sub(r"\$\('[\w-]+'\)", "", line)
        found = re.findall(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|`(?:[^`\\]|\\.)*`", line)
        found = [json.dumps(str(english[s[1:-1]])) if s[1:-1] in english else s for s in found]
        return " ".join(s for s in found if not re.fullmatch(r"['\"`][\w-]*['\"`]", s))

    def owners(src):
        src = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), src, flags=re.S)
        lines, out, name = src.split("\n"), {}, None
        for line in lines:
            m = re.match(r"^(?:async )?function (\w+)\(|^const (\w+) = |^let (\w+) = ", line)
            if m:
                name = next(g for g in m.groups() if g)
            code = re.sub(r"(^|\s)//.*$", "", line)
            if AI_WORDS.search(strings_of(code)) or "TH_SPARK_ICON" in code:
                out.setdefault(name, 0)
                out[name] += 1
        return out

    guard = lambda src, name: "thAiOn()" in fn(src, name) or "aiOn(" in fn(src, name)
    # each owner of an AI word in the scripts, and how it answers to the switch
    THEMES_MAP = {
        "thWithAi": "provenance",                 # "with AI" after a board's name, whatever the switch
        "TH_SPARK_ICON": "icon",
        # the GETs foot asked as the tab draws since tarail, so a thematic analysis project's names its own file
        "TH_GUIDANCE_FROM": "foot", "thGuidanceDraw": "foot",
        "thNamesHtml": "guard", "thSidHtml": "guard",
        "gtPanelDraw": "thNamesHtml",
    }
    APP_MAP = {
        "NUDGES": "advice",                       # the em dash nudge's example, writing advice, no feature
        "sfaShow": "set",                         # Sift's AI proposals' model line, under data-ai-set
        "PROVIDER_ROWS": "set",                   # the AI page's providers and their where lines, under data-ai-set (aipage)
        "AGENTS_LINE": "set", "agentsLine": "set", "drawAgents": "set", "agentsGuide": "set", "mcpShow": "set",
        "drawAgentStart": "own agent",            # Using your own AI agent's box, shown whatever the switch
        # an agent's action waiting for his yes, its line and its card, shown whatever the switch (holds)
        "holdAgent": "own agent", "holdFill": "own agent", "holdChangedLine": "own agent",
        # the card for several, its agent over it and its rows (holdbatchA, 1 November 2026)
        "hbAgent": "own agent", "hbDraw": "own agent", "hbChangedLine": "own agent",
        # the project's History names the agent that made a change, a record shown whatever the switch (historyui)
        "phRecord": "provenance", "phWho": "provenance", "phDraw": "provenance",
        # and By an agent's runs and Home's line of agents' changes, the record of what agents changed with its Undo,
        # shown whatever the switch, since an agent works without the app's own AI (agentreview2, 13 November 2026)
        "arHead": "provenance", "arWhy": "provenance", "arRun": "provenance", "arDraw": "provenance",
        "arMore": "provenance", "arUndo": "provenance", "homeAgentLines": "provenance",
        # a demo's card line and note say the demo was made with AI, a record of how it was made, shown
        # whatever the switch, no feature (demowarn, 12 November 2026)
        "demoWords": "provenance",
    }
    t_owners, a_owners = owners(tjs), owners(app)

    def answers(src, name, how):
        if how == "guard":
            return guard(src, name)
        if how == "foot":
            return "if (!thAiOn()) body.lastElementChild.textContent" in fn(tjs, "thGuidanceDraw")
        if how == "set":
            return "agents-block" in page and "pets-ai" in page
        if how == "thNamesHtml":
            return f"{name}(" in fn(tjs, how) or name in fn(tjs, how) or f"{how}(" in fn(tjs, name)
        if how == "own agent":
            return 'id="agent-start"' in page and 'id="agent-start" data-ai' not in page
        return how in ("provenance", "icon", "matched", "advice")

    stray = sorted(set(t_owners) - set(THEMES_MAP)) + sorted(set(a_owners) - set(APP_MAP))
    unanswered = [n for n, how in THEMES_MAP.items() if n in t_owners and not answers(tjs, n, how)] \
        + [n for n, how in APP_MAP.items() if n in a_owners and not answers(app, n, how)]
    check("100: every AI word and every sparkles icon in app.js and themes.js answers to the switch or is the record of AI work",
          not stray and not unanswered and len(t_owners) >= 4, f"stray {stray}, unanswered {unanswered} {sorted(t_owners)}")
    check("100: the turn screen's button and the page's class come from aiOn, and every settings answer puts it on the page",
          "$('btn-ai').hidden = !(S.data && aiFor(S.data.config, 'statements'));" in fn(app, "resetAI")
          and "return aiOn(cfg) && !off.includes(feature);" in fn(app, "aiFor")
          and "document.body.classList.toggle('ai-off', !aiOn(cfg));" in fn(app, "aiPage")
          and "aiPage(S.libConfig);" in fn(app, "loadLibrary") and "aiPage(data.config);" in fn(app, "startCase")
          and "if (data.config) aiPage(data.config);" in fn(app, "saveSettings")
          and "aiPage(TH.config);" in tjs and '<body class="ai-off">' in page
          and "body.ai-off [data-ai] { display: none !important; }" in style)

    # ── F. Settings: the provider, the key and the rest under the switch, hidden while it is off
    under = {}
    for wrap in ("ai-more", "es-ai", "pets-ai", "agents-block", "sfa-block"):
        at = page.find(f'<div id="{wrap}" data-ai-set>')
        depth, i = 0, at
        while at >= 0 and i < len(page):
            nxt = re.search(r"<div\b|</div>", page[i:])
            if not nxt:
                break
            depth += 1 if nxt.group(0) == "<div" else -1
            i += nxt.end()
            if depth == 0:
                break
        under[wrap] = page[at:i] if at >= 0 else ""
    wanted = {"ai-more": ["ai-restart", "set-provider", "set-model", "set-local-model", "set-key", "btn-key-check", "ai-features"],
              "es-ai": ["set-prompt", "btn-bench"],
              "pets-ai": ["set-pets-model", "pets-key-slot"],
              "agents-block": ["agents-sub", "set-agents", "agents-guide", "mcp-show", "mcp-card"],
              "sfa-block": ["sfa-ai", "sfa-prompt", "sfa-reset", "sfa-model", "sf-bench-rec", "sf-bench-try"]}
    check("100, 9 October: the provider, the model, the key, the prompt, the bench, the PETs model, the agents' block "
          "and Sift's AI proposals with their bench each sit under data-ai-set",
          all(f'id="{i}"' in under[w] for w, ids in wanted.items() for i in ids)
          and 'id="set-ai"' not in "".join(under.values()) and 'id="ai-warn"' not in "".join(under.values()),
          str({w: len(t) for w, t in under.items()}))
    check("100: Settings opened with the switch off asks the server nothing about the AI",
          "if (aiOn(c)) aiSetLoad();" in fn(app, "openSettings") and "keyStatus();" not in fn(app, "openSettings")
          and "aiSetDraw();" in fn(app, "openSettings")
          and all(f"{f}();" in fn(app, "aiSetLoad") for f in ("keyStatus", "loadModels"))
          # the test bench's passage Idiograph's own, asked through its part since the fifth build (23 October 2026)
          and "FAMILY_APPS[APP].aiLoad();" in fn(app, "aiSetLoad") and "aiLoad: () => loadSample()," in app)

    # ── G. in node: the switch, the confirm, Settings, and the PETs and GETs screens off and on
    node = shutil.which("node")
    if not node:
        return skip("100: AI features in node", "no node on this machine")
    pick = lambda src, start: next(line for line in src.splitlines() if line.startswith(start))
    helpers = "\n".join(["const APP = 'idiograph';", pick(app, "const AI_FEATURES = "), pick(app, "const AI_OFF_KEY = "),
                         pick(app, "const esc = "), pick(app, "const escAttr = "), pick(app, "const aiOn = ")]
                        + [f"function {n}(" + fn(app, n) + "\n}" for n in ("aiPage", "aiFor", "aiSetDraw", "aiSetLoad", "aiSwitch", "aiConfirm")])
    script = scratch / "ai-switch.js"
    script.write_text(support.i18n_js() + tjs + "\n" + helpers + r"""
const store = {};
globalThis.localStorage = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); } };
const els = {};
const el = (id) => {
  const e = { id, hidden: false, checked: false, title: '', textContent: '', innerHTML: '', className: '', scrollTop: 0,
    attrs: {}, cls: new Set(), focused: 0 };
  e.classList = { toggle: (c, v) => (v ? e.cls.add(c) : e.cls.delete(c)), add: (c) => e.cls.add(c), remove: (c) => e.cls.delete(c),
    contains: (c) => e.cls.has(c) };
  e.setAttribute = (k, v) => { e.attrs[k] = String(v); };
  e.querySelector = () => null;
  e.addEventListener = () => {};
  e.focus = () => { e.focused += 1; };
  e.pause = () => {};
  Object.defineProperty(e, 'lastElementChild', { get() {
    const foot = /<p class="th-guide-from">([^<]*)<\/p>$/;
    const kid = { said: (e.innerHTML.match(foot) || ['', ''])[1] };
    Object.defineProperty(kid, 'textContent', { get() { return kid.said; },
      set(v) { kid.said = v; e.innerHTML = e.innerHTML.replace(foot, `<p class="th-guide-from">${v}</p>`); } });
    return kid;
  } });
  return e;
};
globalThis.$ = (id) => (els[id] = els[id] || el(id));
const wraps = ['ai-more', 'pets-ai', 'agents-block'].map((id) => $(id));
globalThis.document = { activeElement: null, body: $('body'),
  querySelectorAll: (sel) => (sel === '#settings [data-ai-set]' ? wraps : []) };
globalThis.show = (id) => { $(id).hidden = false; };
globalThis.hide = (id) => { $(id).hidden = true; };
const loads = [];
globalThis.keyStatus = () => loads.push('key');
globalThis.loadModels = () => loads.push('models');
globalThis.loadSample = () => loads.push('sample');
globalThis.sfaLoad = () => loads.push('sift');
// each app's own part of the shell, Idiograph's bench passage on its own page (distil.js) and Sift's AI
// proposals asked on Sift's page alone (sift_settings.js)
globalThis.FAMILY_APPS = { idiograph: { aiLoad: () => loadSample() }, sift: { aiLoad: () => sfaLoad() } };
globalThis.S = { models: null };
globalThis.RESTART_LINE = 'Restart the server to finish this update.';
thPanelShow = (item) => { TH.panel = item || null; };
thPanelDraw = () => {};
thInspectorLeave = () => {};
const out = {};

// the page: aiPage puts the switch on the body, the old key read too
aiPage({ ai_suggest: false }); out.pageOff = document.body.cls.has('ai-off');
aiPage({ ai_suggest: true }); out.pageOn = !document.body.cls.has('ai-off');
aiPage({ haiku: true }); out.pageOld = !document.body.cls.has('ai-off');
aiPage(null); out.pageNone = document.body.cls.has('ai-off');

// Settings: the box unticked hides every part under it, and ticking it asks first
$('ai-confirm').hidden = true;
$('set-ai').checked = false; aiSetDraw(); out.setOff = wraps.map((w) => w.hidden);
$('set-ai').checked = true; aiSwitch();
out.asked = { box: $('set-ai').checked, card: !$('ai-confirm').hidden, focus: $('ai-confirm-cancel').focused, wraps: wraps.map((w) => w.hidden), loads: loads.length };
aiConfirm(false);
out.cancelled = { box: $('set-ai').checked, card: !$('ai-confirm').hidden, wraps: wraps.map((w) => w.hidden), loads: loads.length };
$('set-ai').checked = true; aiSwitch(); aiConfirm(true);
out.turnedOn = { box: $('set-ai').checked, card: !$('ai-confirm').hidden, wraps: wraps.map((w) => w.hidden), loads: loads.slice() };
$('set-ai').checked = false; aiSwitch();
out.unticked = { box: $('set-ai').checked, card: !$('ai-confirm').hidden, wraps: wraps.map((w) => w.hidden) };

// the PETs screen, its switch as the server sent it
const card = (x, y) => ({ x, y, text: 'Walks before the town wakes' });
TH.v = { cards: { 'S:1:0': card(0, 0), 'S:2:0': card(300, 0) }, groups: [], discarded: [], picks: {} };
const g = thMakeGroup(TH.v, ['S:2:0'], 'Early walks');
TH.live = true; TH.mode = 'pets'; TH.sids = { 'S:1:0': 'S1' };
TH.meta = { id: 'v1', name: 'Board 1' }; TH.boards = [{ id: 'v1', name: 'Board 1' }]; TH.chosen = null;
TH.guidance = [{ heading: 'Grouping', lines: ['Group by meaning.'] }];
const screen = () => {
  const o = {};
  o.tabs = thTabsOf('pets'); o.getsTabs = thTabsOf('gets');
  o.names = thNamesHtml({ kind: 'group', id: g });
  o.sid = thSidHtml('S:1:0');
  thGuidanceDraw(); o.foot = $('th-bpanel-body').lastElementChild.textContent;
  TH.mode = 'gets'; thGuidanceDraw(); o.getsFoot = $('th-bpanel-body').lastElementChild.textContent; TH.mode = 'pets';
  thVmenuDraw(); o.menu = $('th-vmenu').innerHTML;
  return o;
};
TH.ai = { on: false, model_name: '' }; out.off = screen();
TH.ai = { on: true, model_name: 'Haiku 4.5' }; out.on = screen();
// on, with the sidebar on Guidance, then the switch turned off: the tab stays, no tab being the AI's since aiout
thSideOpen('guidance'); out.onTab = TH.tab;
TH.ai = { on: false, model_name: '' }; thAiDraw(); out.offTab = [TH.tab, TH.sideOpen];
console.log(JSON.stringify(out));
""", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("100: AI features runs in node", False, run.stderr.strip()[:400])
    out = json.loads(run.stdout)
    check("100: in node, aiPage puts the switch on the page, off with no settings and the old key read",
          out["pageOff"] and out["pageOn"] and out["pageOld"] and out["pageNone"], str(out))
    check("100: in node, ticking AI features leaves it off and opens the card, Back to safety in focus, asking the server nothing yet",
          out["setOff"] == [True, True, True] and out["asked"] == {"box": False, "card": True, "focus": 1, "wraps": [True, True, True], "loads": 0},
          str(out["asked"]))
    check("100, 9 October: in node, Cancel leaves it off and hides what sits under it, and Turn on ticks it, shows it and "
          "loads the key, the models and the bench, Sift's AI proposals on Sift's page alone",
          out["cancelled"] == {"box": False, "card": False, "wraps": [True, True, True], "loads": 0}
          and out["turnedOn"] == {"box": True, "card": False, "wraps": [False, False, False], "loads": ["key", "models", "sample"]},
          str(out["cancelled"]) + str(out["turnedOn"]))
    check("100: in node, unticking asks nothing and hides the provider, the key, the PETs model and the agents' block at once",
          out["unticked"] == {"box": False, "card": False, "wraps": [True, True, True]}, str(out["unticked"]))
    off, on = out["off"], out["on"]
    check("100: in node, with it off the PETs and GETs screens show no AI tab, title, review, revise, short id or AI board",
          off["tabs"] == ["inspector", "guidance", "history"] and off["getsTabs"] == ["inspector", "guidance", "history"]
          and off["names"] == "" and off["sid"] == ""
          and "New AI board" not in off["menu"] and SPARKLES not in off["menu"] and "New board" in off["menu"],
          str({k: off[k] for k in ("tabs", "getsTabs", "names", "sid")}))
    check("100: in node, with it off Guidance's foot names its file and says nothing of the AI",
          off["foot"] == "From themes_guidance.md beside the app." and off["getsFoot"] == "From pet_guidance.md beside the app.",
          off["foot"] + " | " + off["getsFoot"])
    check("100: in node, with it on the titles and the short id show, the titles with the sparkles, and no AI tab or AI "
          "board since aiout",
          on["tabs"] == ["inspector", "guidance", "history"]
          and on["getsTabs"] == ["inspector", "guidance", "history"]
          and "AI suggest PET titles" in on["names"] and SPARKLES in on["names"]
          and "S1" in on["sid"] and "New AI board" not in on["menu"] and SPARKLES not in on["menu"]
          and on["foot"] == "From themes_guidance.md beside the app. The AI reads pet_guidance.md."
          and on["getsFoot"] == "From pet_guidance.md beside the app, the GETs sections the AI reads on this screen.",
          on["foot"])
    check("100: in node, the switch turned off leaves the sidebar on the tab it shows, none being the AI's",
          out["onTab"] == "guidance" and out["offTab"] == ["guidance", True], str(out["offTab"]))

    # ── H. the command line and MCP work whatever the switch
    check("100: the command line and the MCP server never read the switch, so they work whatever it says",
          "ai_suggest" not in inspect.getsource(__import__("cli")) and "ai_suggest" not in inspect.getsource(__import__("mcp_server")))
