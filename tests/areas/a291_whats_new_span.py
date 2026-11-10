"""Area 291: What's new across every version since the one last run (wnspan, 29 October 2026, Adam's yes by dialog to
the coordinator's recommendation, Sparkle's way on a Mac). Someone updating from 0.9.10 straight to 0.9.13 saw 0.9.13's
lines alone, so 0.9.12's were lost to them. Now the window tells the page `before`, the version that ran before the
update, beside `updated`, and the foot line's What's new shows every version the file holds newer than that and up to
the one running, newest first, each under its own heading and date, in one sheet that scrolls inside itself. Under the
last, Earlier versions adds the rest of the file below and goes. Settings, General and the Help menu show the running
version first, then Earlier versions, and Settings' What's new while an update waits shows the update's own notes, which
the window has from its manifest, before the running version's.

What is checked: in node on the shell's own functions, which versions show for a given before and running version (none
before, the same, one back, several back, a gap the file never had, 0.9.10 after 0.9.9 as numbers, an unknown running
version, a file out of order, a version going back) and what Earlier versions holds, then the sheet itself, with the
page's own wiring from boot, on invented versions with invented lines about a beekeeping club: the foot line's What's
new after an update from 0.9.10 showing 0.9.13 then 0.9.12 with Earlier versions, which adds 0.9.10 and older, goes and
takes the focus to the first of them, the window's `before` kept by the page after the window lets it go, Settings and
Help showing the running version then Earlier versions, Settings showing a waiting update's own notes first and Help
not, and a file of one version with no Earlier versions. On each app's served page, the sheet's scrolling body and the
button, and in the window's update.rs, `before` set from `ran` with `updated` and let go with it once seen."""
from __future__ import annotations

import json
import re
import shutil
import subprocess

from . import support
from .support import check, skip


def piece(script: str, name: str) -> str:
    """A whole top-level function of a page script by its name, async or not."""
    for lead in (f"\nasync function {name}(", f"\nfunction {name}("):
        if lead in script:
            return lead.lstrip("\n") + script.split(lead, 1)[1].split("\n}\n", 1)[0] + "\n}\n"
    return ""


# invented versions with invented lines about a beekeeping club's app, newest first, with no 0.9.11 as the real file has none
VERSIONS = [
    {"version": "0.9.13", "date": "29 October 2026", "lines": ["The hives' page lists every frame.", "Swarms have a map."]},
    {"version": "0.9.12", "date": "28 October 2026", "lines": ["Honey weights add up by the season."]},
    {"version": "0.9.10", "date": "27 October 2026", "lines": ["Queens carry their year's colour."]},
    {"version": "0.9.9", "date": "26 October 2026", "lines": ["Inspections keep the weather."]},
    {"version": "0.9.8", "date": "26 October 2026", "lines": ["Trace: the club's minutes open from Home."]},
]

SPAN_RUN = r"""
const [VERSIONS] = JSON.parse(process.argv[2]);
const v = (list) => list.map((x) => x.version);
const span = (versions, running, before) => { const s = wnSpan(versions, running, before); return [s.top, v(s.shown), v(s.earlier)]; };
const shuffled = [VERSIONS[3], VERSIONS[0], VERSIONS[4], VERSIONS[2], VERSIONS[1]];
console.log(JSON.stringify({
  none: span(VERSIONS, '0.9.13', ''),
  same: span(VERSIONS, '0.9.13', '0.9.13'),
  oneBack: span(VERSIONS, '0.9.13', '0.9.12'),
  several: span(VERSIONS, '0.9.13', '0.9.10'),
  gap: span(VERSIONS, '0.9.13', '0.9.11'),
  numbers: span(VERSIONS, '0.9.13', '0.9.9'),
  unknown: span(VERSIONS, '', ''),
  ahead: span(VERSIONS, '0.9.14', '0.9.12'),
  shuffled: span(shuffled, '0.9.13', '0.9.9'),
  back: span(VERSIONS, '0.9.12', '0.9.13'),
  empty: span([], '0.9.13', '0.9.10'),
  compare: [wnCompare('0.9.10', '0.9.9') > 0, wnCompare('1.0.0', '0.9.13') > 0, wnCompare('0.9.2-beta', '0.9.2') === 0],
}));
"""

SHEET_RUN = r"""
const [VERSIONS, WIRING, APP_NAME] = JSON.parse(process.argv[2]);
let focused = null;
function node(tag, id) {
  return { tag, id: id || '', hidden: false, className: '', tabIndex: 0, scrollTop: 40, children: [], _text: '',
    get textContent() { return this._text + this.children.map((c) => c.textContent).join(''); },
    set textContent(s) { this._text = String(s); this.children = []; },
    append(...cs) { for (const c of cs) this.children.push(typeof c === 'string' ? { textContent: c } : c); },
    appendChild(c) { this.children.push(c); return c; },
    querySelector(sel) { for (const c of this.children) { if (c.tag === sel) return c; const deep = c.querySelector && c.querySelector(sel); if (deep) return deep; } return null; },
    focus() { focused = this; } };
}
const els = {};
for (const id of ['whatsnew', 'whatsnew-title', 'whatsnew-date', 'whatsnew-notes', 'whatsnew-rest', 'whatsnew-earlier',
  'whatsnew-body', 'whatsnew-done', 'whatsnew-line', 'whatsnew-said', 'whatsnew-open', 'update-notes']) els[id] = node('div', id);
els.whatsnew.hidden = true;
els['whatsnew-line'].hidden = true;
const $ = (id) => { if (!els[id]) throw new Error('no #' + id); return els[id]; };
const show = (id) => { $(id).hidden = false; };
const hide = (id) => { $(id).hidden = true; };
const document = { createElement: (tag) => node(tag), body: { classList: { add() {}, remove() {} }, style: { setProperty() {} } } };
const window = { addEventListener() {}, removeEventListener() {} };
let FILE = VERSIONS;
const api = async (url) => { if (url !== '/api/whats-new') throw new Error('no route ' + url); return { versions: FILE }; };
// the window's side: `updated` and `before` until told the line was seen, then let go, as update.rs does
let WINDOW = null;
const UPD = { view: null };
const updAsk = async (op) => {
  if (op === 'seen') WINDOW = { ...WINDOW, updated: '', before: '' };
  UPD.view = WINDOW;
  return WINDOW;
};
const settle = () => new Promise((ok) => setTimeout(ok, 10));
const sheet = () => ({
  open: !els.whatsnew.hidden,
  heads: [els['whatsnew-title'].textContent, ...els['whatsnew-rest'].children.map((s) => s.children[0].textContent)],
  first: [els['whatsnew-date'].hidden ? null : els['whatsnew-date'].textContent, els['whatsnew-notes'].children.map((p) => p.textContent)],
  earlier: !els['whatsnew-earlier'].hidden,
  top: els['whatsnew-body'].scrollTop,
});
eval(WIRING);
const run = async () => {
  const out = {};
  const tryIt = async (name, f) => { try { out[name] = await f(); } catch (err) { out[name] = 'threw: ' + err.stack; } };
  const base = { here: true, running: '0.9.13', check: true, download: false, state: 'none', version: '', notes: '', date: '', later: false };
  await tryIt('foot', async () => {
    WINDOW = { ...base, updated: '0.9.13', before: '0.9.10' };
    UPD.view = WINDOW;
    wnFoot();
    await settle();
    const told = [els['whatsnew-said'].textContent, !els['whatsnew-line'].hidden, UPD.view.before];
    await els['whatsnew-open'].onclick();
    return [told, sheet(), focused && focused.id];
  });
  await tryIt('earlier', async () => {
    els['whatsnew-earlier'].onclick();
    return [sheet(), focused && focused.tag, focused && focused.textContent];
  });
  hide('whatsnew');
  await tryIt('settings', async () => { await els['update-notes'].onclick(); return sheet(); });
  await tryIt('help', async () => { await openWhatsNew(); return sheet(); });
  WINDOW = { ...base, state: 'ready', version: '0.9.14', date: '2026-10-30T09:00:00Z', notes: 'Bee bread is counted.\n\nWax has a column.\n' };
  UPD.view = WINDOW;
  await tryIt('waiting', async () => { await els['update-notes'].onclick(); return sheet(); });
  await tryIt('waitingHelp', async () => { await openWhatsNew(); return sheet(); });
  WINDOW = { ...base, state: 'ready', version: '0.9.13', notes: 'The same version.' };
  UPD.view = WINDOW;
  await tryIt('notNewer', async () => { await els['update-notes'].onclick(); return sheet(); });
  FILE = [VERSIONS[0]];
  UPD.view = { ...base };
  await tryIt('single', async () => { await els['update-notes'].onclick(); return sheet(); });
  console.log(JSON.stringify(out));
};
run();
"""


def test_whats_new_span(scratch):
    print("\n291. What's new across every version since the one last run: the versions after `before` up to the one "
          "running, newest first, Earlier versions with the rest, Settings and Help the running version first, a "
          "waiting update's own notes first from Settings, and the window's `before` (29 October 2026)")
    import boot
    import i18n

    # ── each app's served page: the versions in a body of their own that scrolls, Earlier versions under them
    for app in boot.APPS:
        page = support.page_text(app=app)
        sheet = page.split('<div class="overlay" id="whatsnew"', 1)[1].split('\n</div>\n', 1)[0] if 'id="whatsnew"' in page else ""
        body = sheet.split('id="whatsnew-body"', 1)[-1].split('<div class="card-actions">', 1)[0]
        check(f"291: {app}'s sheet holds its versions in a body of its own, the first's heading, date and lines, the rest "
              "after them and Earlier versions last, with Done outside the body",
              all(f'id="{i}"' in body for i in ("whatsnew-title", "whatsnew-date", "whatsnew-notes", "whatsnew-rest"))
              and re.search(r'id="whatsnew-earlier" hidden>' + re.escape(i18n.t("page.whatsnew.earlier")) + "</button>", body) is not None
              and 'id="whatsnew-done"' in sheet and 'id="whatsnew-done"' not in body, app)

    # ── the window's side: `before` from `ran` with `updated`, sent to the page and let go with it once seen
    rust = support.text("packaging/tauri/src-tauri/src/update.rs")
    begin = rust.split("pub fn begin(", 1)[-1].split("\n}\n", 1)[0]
    seen = rust.split('"seen" => {', 1)[-1].split('"relaunch"', 1)[0]
    view = rust.split("pub fn view(", 1)[-1].split("\n}\n", 1)[0]
    check("291: the window keeps the version that ran before as `before` with `updated`, tells the page both, and "
          "lets both go once the line has been seen",
          re.search(r"newer\(&running, &ran\) && seen != running \{[^}]*now\.updated = running\.clone\(\);\s*now\.before = ran\.clone\(\);", begin) is not None
          and '"before": now.before' in view and '"updated": now.updated' in view
          and "now.before.clear()" in seen and "std::mem::take(&mut now.updated)" in seen,
          begin[:300])

    node = shutil.which("node")
    if not node:
        skip("291: the span and the sheet in node", "node is not on this machine")
        return
    shell = support.text("family/static/shell.js")
    wn_line = next(ln for ln in shell.splitlines() if ln.startswith("const WN = ")) + "\n"
    fns = "".join(piece(shell, n) for n in ("wnNumbers", "wnCompare", "wnSpan", "wnIncoming", "wnFill", "wnSection",
                                            "openWhatsNew", "doneAtFoot", "wnEarlier", "wnFoot", "wnFootRoom", "wnFootClose"))

    # ── which versions show
    # from a file of its own, never node -e, since the catalogue runs past Windows's command line (area 76)
    harness = scratch / "a291-span.js"
    harness.write_text(support.i18n_js() + wn_line + fns + SPAN_RUN, encoding="utf-8")
    done = subprocess.run([node, str(harness), json.dumps([VERSIONS])], capture_output=True, text=True, encoding="utf-8", timeout=60)
    out = json.loads(done.stdout.strip().splitlines()[-1]) if done.returncode == 0 and done.stdout.strip() else {"error": done.stderr[-600:]}
    older = ["0.9.12", "0.9.10", "0.9.9", "0.9.8"]
    check("291: with no version before, or the same one, the sheet shows the running version alone and Earlier versions "
          "holds every older one, newest first",
          out.get("none") == ["0.9.13", ["0.9.13"], older] and out.get("same") == ["0.9.13", ["0.9.13"], older], str(out))
    check("291: one version back shows the running one alone, the one before it first under Earlier versions",
          out.get("oneBack") == ["0.9.13", ["0.9.13"], older], str(out.get("oneBack")))
    check("291: from 0.9.10 to 0.9.13 the sheet shows 0.9.13 then 0.9.12, the file having no 0.9.11, and Earlier "
          "versions starts at 0.9.10",
          out.get("several") == ["0.9.13", ["0.9.13", "0.9.12"], ["0.9.10", "0.9.9", "0.9.8"]], str(out.get("several")))
    check("291: from 0.9.11, a version the file never had, the sheet shows 0.9.13 and 0.9.12 and Earlier versions starts "
          "at 0.9.10",
          out.get("gap") == ["0.9.13", ["0.9.13", "0.9.12"], ["0.9.10", "0.9.9", "0.9.8"]], str(out.get("gap")))
    check("291: versions compare as numbers, so from 0.9.9 the sheet holds 0.9.10, and a file out of order shows newest "
          "first",
          out.get("numbers") == ["0.9.13", ["0.9.13", "0.9.12", "0.9.10"], ["0.9.9", "0.9.8"]]
          and out.get("shuffled") == out.get("numbers") and out.get("compare") == [True, True, True],
          str([out.get("numbers"), out.get("shuffled"), out.get("compare")]))
    check("291: with no running version known the file's newest shows alone, a running version the file lacks shows "
          "the versions up to it, a version going back shows the running one alone, and an empty file nothing",
          out.get("unknown") == ["0.9.13", ["0.9.13"], older]
          and out.get("ahead") == ["0.9.14", ["0.9.13"], older]
          and out.get("back") == ["0.9.12", ["0.9.12"], ["0.9.10", "0.9.9", "0.9.8"]]
          and out.get("empty") == ["0.9.13", [], []],
          str([out.get("unknown"), out.get("ahead"), out.get("back"), out.get("empty")]))

    # ── the sheet, with the page's own wiring from boot
    wiring = "\n".join(ln.strip() for ln in shell.splitlines()
                       if re.match(r"\s*\$\('(whatsnew-open|whatsnew-earlier|update-notes)'\)\.onclick = ", ln))
    harness = scratch / "a291-sheet.js"
    harness.write_text(support.i18n_js() + wn_line + fns + SHEET_RUN, encoding="utf-8")
    done = subprocess.run([node, str(harness), json.dumps([VERSIONS, wiring, "Idiograph"])], capture_output=True,
                          text=True, encoding="utf-8", timeout=60)
    out = json.loads(done.stdout.strip().splitlines()[-1]) if done.returncode == 0 and done.stdout.strip() else {"error": done.stderr[-600:]}
    heads = lambda *vs: ["Idiograph " + x for x in vs]  # noqa: E731
    foot = out.get("foot") or [[], {}, None]
    check("291: after an update from 0.9.10 the foot line says Updated to Idiograph 0.9.13., and its What's new opens "
          "0.9.13 then 0.9.12, the first's date and lines, Earlier versions under them, the sheet at its top, Done in focus",
          isinstance(foot, list) and foot[0][:2] == [i18n.t("shell.whatsnew.updated", app="Idiograph", version="0.9.13"), True]
          and foot[1].get("open") is True and foot[1].get("heads") == heads("0.9.13", "0.9.12")
          and foot[1].get("first") == ["29 October 2026", VERSIONS[0]["lines"]]
          and foot[1].get("earlier") is True and foot[1].get("top") == 0 and foot[2] == "whatsnew-done",
          str(foot))
    check("291: the page keeps the window's `before` for the line's sheet after the window lets it go once seen",
          isinstance(foot, list) and foot[0][2] == "" and foot[1].get("heads") == heads("0.9.13", "0.9.12"),
          str(foot[0] if isinstance(foot, list) else foot))
    earlier = out.get("earlier") or [{}, None, None]
    check("291: Earlier versions adds 0.9.10, 0.9.9 and 0.9.8 below, newest first, goes, and gives the first of them the focus",
          isinstance(earlier, list) and earlier[0].get("heads") == heads("0.9.13", "0.9.12", "0.9.10", "0.9.9", "0.9.8")
          and earlier[0].get("earlier") is False and earlier[1:] == ["h2", "Idiograph 0.9.10"], str(earlier))
    check("291: from Settings and the Help menu the sheet shows the running version first, then Earlier versions",
          (out.get("settings") or {}).get("heads") == heads("0.9.13") and (out.get("settings") or {}).get("earlier") is True
          and (out.get("help") or {}).get("heads") == heads("0.9.13") and (out.get("help") or {}).get("earlier") is True,
          str([out.get("settings"), out.get("help")]))
    waiting = out.get("waiting") or {}
    check("291: Settings' What's new while 0.9.14 waits shows its own notes first, a line each with its day, then 0.9.13 "
          "and Earlier versions, and the Help menu the running version alone",
          waiting.get("heads") == heads("0.9.14", "0.9.13")
          and waiting.get("first") == ["30 October 2026", ["Bee bread is counted.", "Wax has a column."]]
          and waiting.get("earlier") is True and (out.get("waitingHelp") or {}).get("heads") == heads("0.9.13"),
          str([waiting, out.get("waitingHelp")]))
    check("291: an update no newer than the running version adds nothing, and a file of one version has no Earlier versions",
          (out.get("notNewer") or {}).get("heads") == heads("0.9.13")
          and (out.get("single") or {}).get("heads") == heads("0.9.13") and (out.get("single") or {}).get("earlier") is False,
          str([out.get("notNewer"), out.get("single")]))
