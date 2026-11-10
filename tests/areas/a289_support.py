"""Area 289: Support Idiograph (supportcard, 28 October 2026, Adam's wording 1 of that day's Section 17). Each app's
Home has a quiet link after Ko-fi, "Other ways to help", and Settings one beside About, both opening a card in About's
look: under its heading the private preview's line, then Cite it, the APA citation with the version running and Copy,
Translate it, Send feedback, Contribute code, Fund it with its costs in pounds and Ko-fi, and Thanks (supportcard2,
29 October, Adam: a private alpha by invitation, code welcome, the costs in pounds), the private line's request
ending Home's preview note too. Its heading names the app, "Support Sift" in Sift. After the first Word export of
PETs ever, the note the export leaves gets one line, "Idiograph is free. If it helps your work, there are ways to
support it.", its link opening the card, shown once: the settings hold the day it first showed, `support_asked`,
written alone through /api/settings as the line shows, which an agent reads there too.

What is checked: on each app's served page, the card's parts in that order, the private line first and naming the
app, and Fund it's costs in pounds with no dollar left, and Idiograph's Home preview note ending on the card's own
request to keep it to yourself; in node on the shell's own functions against the ids the page holds, Home's link and
Settings' link open the card, its citation naming the app and the version running, Copy putting the plain citation
on the clipboard, the feedback links (Send feedback, ask me how) opening Send feedback, Contribute code linking the code on
GitHub (pubreadme, 10 November 2026), and Send feedback and the department's line left out where the build has no
collector; in Python
`support_asked` sent alone saved alone, the first day kept, anything not a day passed over, answered by the
settings' read op and kept by a whole Settings save; and in node on themes.js's own export, every settings call a
fresh Python process on a scratch settings file, the line on the first Word export of PETs alone, never on a later
one, a .md export or a GETs board's, nor in a page started again, nor in a note closed before the settings
answered. Fixtures are invented settings files in the scratch folder."""
from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

from . import support
from .support import check, skip


def piece(script: str, name: str) -> str:
    """A whole top-level function of a page script by its name, async or not."""
    for lead in (f"\nasync function {name}(", f"\nfunction {name}("):
        if lead in script:
            return lead.lstrip("\n") + script.split(lead, 1)[1].split("\n}\n", 1)[0] + "\n}\n"
    return ""


SHELL_RUN = r"""
const [APP, APP_NAME, VERSION, ids] = JSON.parse(process.argv[2]);
const listeners = {};
const els = {};
for (const id of ids) {
  els[id] = { id, hidden: id === 'support' || id === 'feedback', innerHTML: '', onclick: null, focused: false,
    focus() { this.focused = true; }, querySelector() { return null; },
    addEventListener(type, fn) { (listeners[id] = listeners[id] || []).push(fn); } };
}
const $ = (id) => { if (!els[id]) throw new Error(`no #${id} on ${APP}'s page`); return els[id]; };
const show = (id) => { $(id).hidden = false; };
const hide = (id) => { $(id).hidden = true; };
const said = [];
const say = (m) => said.push(m);
const FEEDBACK = { on: true };
let fed = null;
const openFeedback = (screen) => { fed = screen; show('feedback'); };
let UPD = { view: { running: VERSION } };
const S = { lib: { version: '0.0.1' } };
let clip = null;
// node has a navigator of its own, with no clipboard, held by a getter
Object.defineProperty(globalThis, 'navigator', { value: { clipboard: { writeText: async (text) => { clip = text; } } }, configurable: true });
const run = async () => {
  const out = {};
  const tryIt = async (f) => { try { return await f(); } catch (err) { return 'threw: ' + err.message; } };
  out.wired = await tryIt(() => { supportWire(); return true; });
  out.home = await tryIt(() => { $('lib-support').onclick(); return [!els.support.hidden, els['support-done'].focused, els['support-ref'].innerHTML]; });
  out.copy = await tryIt(async () => { await $('support-copy').onclick(); return [clip, said.slice(-1)[0]]; });
  hide('support');
  out.settings = await tryIt(() => { $('settings-support').onclick(); return !els.support.hidden; });
  out.feedback = await tryIt(() => {
    const e = { target: { closest: (sel) => (sel === '[data-support-feedback]' ? {} : null) }, prevented: false, preventDefault() { this.prevented = true; } };
    for (const fn of listeners.support || []) fn(e);
    return [els.support.hidden, !els.feedback.hidden, fed, e.prevented];
  });
  out.parts = [els['support-feedback'].hidden, els['support-code'].hidden, els['support-grant'].hidden];
  // a build with no collector: no Send feedback part and no way to ask
  FEEDBACK.on = false;
  hide('feedback');
  $('settings-support').onclick();
  out.off = [els['support-feedback'].hidden, els['support-code'].hidden, els['support-grant'].hidden];
  // a browser tab with no window: the server's version
  UPD = { view: null };
  out.server = await tryIt(async () => { await $('support-copy').onclick(); return clip; });
  out.done = await tryIt(() => { $('support-done').onclick(); return els.support.hidden; });
  console.log(JSON.stringify(out));
};
run();
"""

THEMES_RUN = r"""
const { execFileSync } = require('node:child_process');
const [PYTHON, HELPER, CONFIG] = JSON.parse(process.argv[2]);
const fresh = () => ({ id: '', hidden: true, innerHTML: '', textContent: '', className: '', children: [], parent: null,
  appendChild(c) { c.parent = this; this.children.push(c); }, remove() { if (this.parent) this.parent.children = this.parent.children.filter((c) => c !== this); } });
const els = {};
for (const id of ['th-exported', 'th-exported-head', 'th-exported-files', 'th-reveal']) els[id] = Object.assign(fresh(), { id });
const $ = (id) => els[id] || els['th-exported'].children.find((c) => c.id === id) || null;
const document = { createElement: () => fresh() };
const esc = (s) => String(s);
const fileOf = (p) => String(p).split('/').pop();
const say = () => {};
const needsRestart = () => false;
const RESTART_LINE = '';
const thMade = () => {};
const thTitleDone = () => {};
const thNoteDone = () => {};
const thFlush = async () => {};
const thIncludesSent = () => ({});
const TH = { live: true, busy: false, wordable: true, dirty: false, path: 'Rowan.xlsx', meta: { id: 'b1', name: 'Hedgerows' },
  mode: 'pets', platform: 'darwin', exported: null };
const settingsCalls = [];
// every settings call a fresh process of the server's own function on the scratch settings file, as after a restart
async function api(url, body) {
  if (url === '/api/themes-export') return { shown: [`Working/Hedgerows${body.op === 'word' ? '.docx' : '.md'}`], version: { name: 'Hedgerows' } };
  if (url !== '/api/settings') throw new Error('no route ' + url);
  settingsCalls.push(body);
  return JSON.parse(execFileSync(PYTHON, ['-I', HELPER, CONFIG, JSON.stringify(body)], { encoding: 'utf-8' }).trim().split('\n').pop());
}
const settle = () => new Promise((ok) => setTimeout(ok, 20));
const line = () => { const l = $('th-once'); return l ? l.innerHTML : null; };
const asked = () => { try { return JSON.parse(require('node:fs').readFileSync(CONFIG, 'utf-8')).support_asked || null; } catch { return null; } };
const run = async () => {
  const out = {};
  const step = async (name, f) => { try { await f(); await settle(); out[name] = [line(), asked(), !els['th-exported'].hidden]; } catch (err) { out[name] = 'threw: ' + err.message; } };
  if (process.argv[3] === 'again') {
    await step('again', () => thExport(true));
  } else {
    // a GETs board's Word export is not PETs
    TH.mode = 'gets';
    await step('gets', () => thExport(true));
    TH.mode = 'pets';
    // a note closed before the settings answer gets nothing
    await step('closed', () => { thExported({ shown: ['Working/Hedgerows.docx'], name: 'Hedgerows', reveal: true, word: true }); thExported(null); });
    await step('md', () => thExport(false));
    await step('first', () => thExport(true));
    out.closedAfter = (() => { thExported(null); return line(); })();
    await step('second', () => thExport(true));
  }
  out.calls = settingsCalls;
  console.log(JSON.stringify(out));
};
run();
"""

HELPER = """import json, sys
from pathlib import Path
sys.path.insert(0, %r)
import boot
boot.setup()
import server
server.CONFIG_PATH = Path(sys.argv[1])
print(json.dumps(server.api_settings(json.loads(sys.argv[2]))))
"""


def test_support(scratch: Path):
    print("\n289. Support Idiograph: Home's link and Settings' link opening the card, its citation with the app's name "
          "and the version running and Copy putting it on the clipboard, and the one-time line on the first Word "
          "export of PETs alone, never after it has shown, across a restart, `support_asked` read by agents "
          "(28 October 2026), and the card's parts in order, the private line first, on Home's preview note too, and "
          "the costs in pounds (29 October 2026)")
    import app_identity
    import boot
    import i18n
    import server

    # ── the served pages: the card and its two ways in on each, its heading the app's own name, nothing from outside
    pages = {app: support.page_text(app=app) for app in boot.APPS}
    for app, page in pages.items():
        card = page.split('<div class="overlay" id="support"', 1)[1].split('\n</div>\n', 1)[0] if 'id="support"' in page else ""
        heading = re.search(r'<h2 id="support-title">([^<]*)</h2>', card)
        check(f"289: {app}'s page holds Home's link inside Free's item after Ko-fi, Settings' link after About and the "
              f"card, the card and the Settings link naming {app.title()}",
              re.search(r'<li class="lp-free">.*?class="kofi"[^>]*>.*?</a><button [^>]*id="lib-support">[^<]+</button></li>', page) is not None
              and re.search(r'id="settings-about">.*?</button>\s*<button [^>]*id="settings-support">[^<]*' + app.title() + "<", page) is not None
              and heading is not None and app.title() in heading.group(1), app)
        outside = re.findall(r'<(?:script|iframe)\b|\bsrc="(?!/)[^"]*"', card)
        check(f"289: {app}'s card opens /translating, Ko-fi as Home's anchor does, Send feedback twice and the code on GitHub "
              "(pubreadme, 10 November 2026: the repository public, where it asked for access), and "
              "fetches nothing from outside the app",
              'href="/translating"' in card and card.count('href="https://ko-fi.com/X8X01NIXRB"') == 1
              and card.count("data-support-feedback") == 2 and card.count('href="https://github.com/Pharkie/idiograph"') == 1
              and not outside, str(outside))
        # the parts in order (supportcard2, 29 October): the private line first under the heading, then six parts
        heads = re.findall(r'<h3 class="section-label about-head">([^<]*)</h3>', card)
        want = [i18n.t(k) for k in ("page.support.cite", "page.support.translate", "page.feedback.title",
                                    "page.support.code", "page.support.fund", "page.support.thanks")]
        first = re.search(r'<div class="support-body">\s*<p class="support-private">([^<]*)</p>\s*<h3', card)
        check(f"289: {app}'s card has the private preview's line first under its heading, naming {app.title()}, then "
              "Cite it, Translate it, Send feedback, Contribute code, Fund it and Thanks in that order",
              heads == want and first is not None and app.title() in first.group(1)
              and first.group(1) == html.escape(i18n.t("page.support.private", app=app.title()), quote=False),
              str([heads, first and first.group(1)]))
        fund = card.split(f'<h3 class="section-label about-head">{want[4]}</h3>', 1)[-1].split("<h3", 1)[0]
        check(f"289: {app}'s Fund it gives its costs in pounds, none in dollars",
              len(re.findall(r"£\d", fund)) >= 3 and "$" not in fund, fund[:300])

    # Home's preview note ends on the card's own request to keep it private (Adam, 29 October), in Idiograph,
    # the one app with the Preview Edition
    note = re.search(r'<p class="pe-note" data-only="idiograph">.*?<span>([^<]*)</span></p>', pages["idiograph"], re.S)
    keep = i18n.t("page.support.private", app="Idiograph").split(". ", 1)[1]
    check("289: Idiograph's Home preview note ends asking, in the card's own words, to keep it to yourself for now",
          note is not None and note.group(1).endswith(" " + html.escape(keep, quote=False)),
          str([note and note.group(1)[-160:], keep]))

    node = shutil.which("node")
    if not node:
        skip("289: the card and the one-time line in node", "node is not on this machine")
    else:
        shell = support.text("family/static/shell.js")
        address = next(ln for ln in shell.splitlines() if ln.startswith("const SUPPORT_ADDRESS = ")) + "\n"
        escline = next(ln for ln in shell.splitlines() if ln.startswith("const esc = ")) + "\n"
        body = escline + address + "".join(piece(shell, n) for n in ("runningVersion", "supportCitation", "openSupport",
                                                                    "doneAtFoot", "supportCopy", "supportWire"))
        for app in boot.APPS:
            version = app_identity.version(app)
            ids = sorted(set(re.findall(r'\bid="([^"]+)"', pages[app])))
            # from a file of its own, never node -e, since the catalogue runs past Windows's command line (area 76)
            harness = scratch / f"a289-shell-{app}.js"
            harness.write_text(support.i18n_js(app) + body + SHELL_RUN, encoding="utf-8")
            ran = subprocess.run([node, str(harness), json.dumps([app, app.title(), version, ids])], capture_output=True,
                                 text=True, encoding="utf-8", timeout=60)
            out = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {"error": ran.stderr[-400:]}
            where = "https://idiograph.app"
            plain = f"Knowles, A. (2026). {app.title()} (Version {version}) [Computer software]. {where}"
            check(f"289: on {app}'s page Home's link opens the card, Done in focus, the citation naming {app.title()}, "
                  f"version {version} running, and its address",
                  out.get("wired") is True and (out.get("home") or [None])[:2] == [True, True]
                  and (out.get("home") or ["", "", ""])[2] == plain.replace(app.title() + " (", f"<i>{app.title()}</i> ("),
                  str(out.get("home") or out))
            check(f"289: on {app}'s page Copy puts the citation as plain text with the version running on the clipboard "
                  "and says Copied, and in a browser tab the server's version",
                  out.get("copy") == [plain, "Copied"]
                  and out.get("server") == plain.replace(f"Version {version}", "Version 0.0.1"), str([out.get("copy"), out.get("server")]))
            check(f"289: on {app}'s page Settings' link opens the card, its feedback links close it and open Send "
                  "feedback, Send feedback and the department's line left out where the build has no collector, Contribute "
                  "code kept since it links to GitHub (pubreadme), and Done closes it",
                  out.get("settings") is True and out.get("feedback") == [True, True, "support", True]
                  and out.get("parts") == [False, False, False] and out.get("off") == [True, False, True]
                  and out.get("done") is True,
                  str([out.get("settings"), out.get("feedback"), out.get("parts"), out.get("off"), out.get("done")]))

    # ── support_asked through the settings API, as the line and an agent use it
    saved_path = server.CONFIG_PATH
    config = scratch / "a289-config.json"
    seen = {}
    try:
        server.CONFIG_PATH = config
        config.write_text(json.dumps({"interviewer": "Ada", "appearance": "dark"}, indent=2), encoding="utf-8")
        server.api_settings({"support_asked": "soon"})
        server.api_settings({"support_asked": "2026-13-45"})
        server.api_settings({"support_asked": 5})
        seen["refused"] = json.loads(config.read_text(encoding="utf-8"))
        seen["unset"] = "support_asked" in server.api_settings({"op": "read"})["config"]
        server.api_settings({"support_asked": "2026-10-28"})
        seen["saved"] = json.loads(config.read_text(encoding="utf-8"))
        server.api_settings({"support_asked": "2026-11-02"})
        seen["again"] = json.loads(config.read_text(encoding="utf-8")).get("support_asked")
        seen["read"] = server.ROUTES["/api/settings"]({"op": "read"})["config"].get("support_asked")
        server.api_settings({"celebrations": False})
        seen["whole"] = json.loads(config.read_text(encoding="utf-8")).get("support_asked")
    finally:
        server.CONFIG_PATH = saved_path
    check("289: support_asked sent alone is saved alone, the rest of the settings file as it was, a value not a day "
          "passed over, and the first day kept",
          seen["refused"] == {"interviewer": "Ada", "appearance": "dark"} and seen["unset"] is False
          and seen["saved"] == {"interviewer": "Ada", "appearance": "dark", "support_asked": "2026-10-28"}
          and seen["again"] == "2026-10-28", str(seen))
    check("289: an agent reads support_asked through the settings' read op, and a whole Settings save keeps it",
          seen["read"] == "2026-10-28" and seen["whole"] == "2026-10-28", str([seen["read"], seen["whole"]]))

    # ── the one-time line, on themes.js's own export, every settings call a fresh process
    if not node:
        return
    themes = support.text("apps/idiograph/static/themes.js")
    helper = scratch / "a289-settings.py"
    helper.write_text(HELPER % str(support.TOOL), encoding="utf-8")
    once = scratch / "a289-once.json"
    once.write_text(json.dumps({"interviewer": "Ada"}, indent=2), encoding="utf-8")
    script = support.i18n_js() + "".join(piece(themes, n) for n in ("thExport", "thExported", "thSupportOnce")) + THEMES_RUN
    path = scratch / "a289-once.js"
    path.write_text(script, encoding="utf-8")
    args = json.dumps([sys.executable, str(helper), str(once)])
    ran = subprocess.run([node, str(path), args], capture_output=True, text=True, encoding="utf-8", timeout=300)
    out = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {"error": ran.stderr[-600:]}
    today = date.today().isoformat()
    words = 'Idiograph is free. If it helps your work, there are <a href="#">ways to support it</a>.'
    check("289: no line on a GETs board's Word export, a note closed before the settings answer, or a .md export, "
          "and nothing written",
          out.get("gets") == [None, None, True] and out.get("closed") == [None, None, False]
          and out.get("md") == [None, None, True], str([out.get("gets"), out.get("closed"), out.get("md"), out.get("error")]))
    check("289: the first Word export of PETs shows the line in its note and writes today's day alone as support_asked, "
          "and closing the note takes the line with it",
          out.get("first") == [words, today, True] and out.get("closedAfter") is None
          and {"support_asked": today} in (out.get("calls") or []), str([out.get("first"), out.get("closedAfter")]))
    check("289: a later Word export of PETs shows no line, the settings read afresh",
          out.get("second") == [None, today, True], str(out.get("second")))
    ran = subprocess.run([node, str(path), args, "again"], capture_output=True, text=True, encoding="utf-8", timeout=120)
    again = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {"error": ran.stderr[-600:]}
    check("289: after a restart, the page and the server started again on the same settings, a Word export of PETs "
          "shows no line and writes nothing",
          again.get("again") == [None, today, True] and again.get("calls") == [{"op": "read"}], str(again))
