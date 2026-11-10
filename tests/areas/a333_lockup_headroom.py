"""Area 333: the lockup's clear space and the app's name in the window's title (headroom, 6 November 2026, Adam).
Adam saw Home's lockup too close under the window's title bar and ruled that the lockup always has at least its mark's
height clear above it and to its left, measured above from the bottom of the title bar, the page's top in the app's
window. What is held here is what the page measures: in a real browser, Home's head puts the lockup's top at least its
mark's height under the page's top in each app and in the Preview Edition, at the app's two window sizes and at
Large (125%), and (Adam, margin 32 at every width) its left edge at least that far from the page's, on one edge
with the projects' column, the tools staying level with it, the bar's small lockup and About's keeping their own
room, and the
title of every screen in node, the app first and then the project, the participant as the screens show it and the
screen, with the Mac and Windows window taking that title as the page sets it. Nothing here pins a colour or a
word of the look."""
from __future__ import annotations

import html as html_mod
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import support
from .a167_window_menus import js_const, js_function
from .support import check, skip

# the widths a page is laid out at, in CSS pixels: the app's window at 1280, at 1050 and at its smallest, 720, the
# first and last again at Large (125%), where the same window holds 1024 and 576 CSS pixels of page, and 360 for the
# browser's own narrow tab. From 560 of page Home keeps its 32px margin (--home-edge), so the left space is measured
# at every width but 360
WIDTHS = (1280, 1050, 1024, 720, 576, 360)

MEASURE = r"""
const out = {};
const rect = (e) => { const b = e.getBoundingClientRect(); return { top: b.top, left: b.left, h: b.height, w: b.width }; };
for (const width of WIDTHS) {
  const frame = document.createElement('iframe');
  frame.style.cssText = `width:${width}px;height:900px;border:0;display:block`;
  document.body.appendChild(frame);
  const doc = frame.contentDocument;
  doc.open();
  doc.write(`<!doctype html><html data-app="idiograph"><head><meta charset="utf-8"><style>${CSS}</style></head><body>${BODY}</body></html>`);
  doc.close();
  const root = doc.documentElement;
  const at = {};
  for (const [name, app, edition] of [['preview', 'idiograph', 'preview'], ['idiograph', 'idiograph', ''], ['sift', 'sift', ''], ['trace', 'trace', '']]) {
    root.setAttribute('data-app', app);
    if (edition) root.setAttribute('data-edition', edition); else root.removeAttribute('data-edition');
    const lock = [...doc.querySelectorAll('.lib-head .wordmark svg.lockup')].find((e) => e.getClientRects().length);
    const tools = doc.querySelector('.lib-head .lib-tools');
    // the projects' column under the head, its first line, which stands on the head's own left edge
    at[name] = { lockup: rect(lock), tools: rect(tools), body: rect(doc.querySelector('.lib-body > p')), shown: lock.getAttribute('class') };
  }
  root.setAttribute('data-app', 'idiograph');
  root.removeAttribute('data-edition');
  // the bar's lockup from the bar's own top, which is the page's top on a screen
  const rail = rect(doc.querySelector('.rail'));
  const mark = rect(doc.querySelector('.rail .bar-brand svg.lockup'));
  const bar = { top: mark.top - rail.top, left: mark.left - rail.left, h: mark.h, rail: rail.h };
  // About's lockup in its card, measured from the card's edge, the Preview Edition's included
  root.setAttribute('data-edition', 'preview');
  const card = rect(doc.querySelector('.about-card'));
  const about = rect(doc.querySelector('.about-lockup svg.lockup'));
  at.bar = bar;
  at.about = { top: about.top - card.top, left: about.left - card.left, h: about.h };
  out[width] = at;
}
document.getElementById('out').textContent = JSON.stringify(out);
"""


def _clear_space(scratch: Path):
    """Home's head, a bar and About drawn by the page's own markup and stylesheets in the computer's own browser,
    headless, each width in a frame of its own so the width is the page's and not the window's least, and every app
    and edition set on the frame's root in turn"""
    exe = support.browser()
    if exe is None:
        skip("333: the lockup's clear space in a real browser", "no Chrome, Chromium, Brave or Edge on this computer")
        return None
    page = support.page_text()
    head = '<header class="lib-head">' + page.split('<header class="lib-head">', 1)[1].split("</header>", 1)[0] + "</header>"
    # Home's screen with its projects' column under the head, so the one left edge can be read
    home = f'<section id="library" class="screen">{head}<div class="lib-body"><p>Projects</p></div></section>'
    lockup = re.search(r'<svg class="lockup" viewBox.*?</svg>', head, re.S).group(0)
    # a bar with the app's lockup in its brand button, as barLockups draws it, and About's card with its lockup
    bar = f'<div class="screen"><header class="rail"><button type="button" class="bar-brand">{lockup}</button></header></div>'
    about = f'<div class="overlay"><div class="card about-card"><div class="about-lockup pe">{lockup}</div></div></div>'
    css = "\n".join(support.text(p) for p in ("family/static/tokens.css", "family/static/style.css"))
    script = ("const WIDTHS = " + json.dumps(WIDTHS) + ";\nconst CSS = " + json.dumps(css) + ";\nconst BODY = "
              + json.dumps(home + bar + about) + ";\n" + MEASURE).replace("</", "<\\/")
    doc = ('<!doctype html><html><head><meta charset="utf-8"></head><body><pre id="out">none</pre><script>'
           + script + "</script></body></html>")
    with tempfile.TemporaryDirectory(prefix="idiograph-333-") as tmp:
        page_file = Path(tmp) / "head.html"
        page_file.write_text(doc, encoding="utf-8")
        cmd = [str(exe), "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
               "--disable-background-networking", "--disable-component-update", "--disable-sync", "--disable-default-apps",
               "--password-store=basic", "--use-mock-keychain", f"--user-data-dir={Path(tmp) / 'profile'}",
               "--window-size=1400,1000", "--virtual-time-budget=3000", "--dump-dom", page_file.as_uri()]
        try:
            dumped = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=120).stdout
        except (OSError, subprocess.TimeoutExpired) as err:
            dumped = str(err)
    said = dumped.split('<pre id="out">', 1)[1].split("</pre>", 1)[0] if '<pre id="out">' in dumped else "{}"
    return json.loads(html_mod.unescape(said)) if said.startswith("{") else {}


TITLES = r"""
const bits = require('fs').readFileSync(process.argv[2], 'utf8');
function world(app) {
  const els = {};
  const el = (id) => (els[id] = { id, hidden: false, textContent: '', dataset: {} });
  ['work', 'themes', 'traj', 'codes-screen', 'sift', 'sift-search', 'trace', 'library', 'home-project', 'rail-project', 'rail-case',
   'th-project', 'th-case', 'tj-project', 'cd-project', 'sf-name', 'sfs-name', 'tr-name', 'hp-name'].forEach(el);
  const names = { idiograph: 'Idiograph', sift: 'Sift', trace: 'Trace' };
  const env = { $: (id) => els[id], els, APP: app, APP_NAME: names[app],
    TH: { mode: 'pets', lpets: false, lgets: false, project: null }, S: { data: null } };
  const fn = new Function(...Object.keys(env), bits + '\nreturn { pageTitle, FAMILY_APPS };');
  const got = fn(...Object.values(env));
  return Object.assign(env, got);
}
const w = world('idiograph');
const only = (id) => { ['work', 'themes', 'traj', 'codes-screen', 'sift', 'sift-search', 'trace', 'library'].forEach((s) => { w.els[s].hidden = s !== id; }); };
const say = (id, text) => { w.els[id].textContent = text; };
const out = {};
// Home, and a project's page
only('library'); w.els['home-project'].hidden = true; out.home = w.pageTitle();
w.els['home-project'].hidden = false; say('hp-name', 'Beach walks'); out.project = w.pageTitle();
// the statements screen: the participant as the screens show it, the dash between the number and the name gone
only('work'); say('rail-project', 'Beach walks'); say('rail-case', 'Wren'); w.S.data = { case: 'P2 - Wren' };
out.work = w.pageTitle();
w.S.data = null; out.workBare = w.pageTitle();
say('rail-project', ''); w.S.data = { case: 'P2 - Wren' }; out.workNoProject = w.pageTitle();
// PETs, a participant's LPETs, the GETs and the LGETs
only('themes'); say('th-project', 'Beach walks'); say('th-case', 'Wren'); w.els['th-case'].dataset.label = 'P2 - Wren';
out.pets = w.pageTitle();
w.TH.mode = 'gets'; w.TH.lpets = true; out.lpets = w.pageTitle();
w.TH.lpets = false; out.gets = w.pageTitle();
w.TH.lgets = true; out.lgets = w.pageTitle();
// the other screens of a project
only('traj'); say('tj-project', 'Beach walks'); out.traj = w.pageTitle();
only('codes-screen'); say('cd-project', 'Beach walks'); out.codes = w.pageTitle();
// Sift and Trace, each in its own page
const lone = (x, id) => { ['work', 'themes', 'traj', 'codes-screen', 'sift', 'sift-search', 'trace', 'library'].forEach((n) => { x.els[n].hidden = n !== id; }); return x; };
const s = lone(world('sift'), 'sift'); s.els['sf-name'].textContent = 'Hive review';
out.sift = s.pageTitle();
lone(s, 'sift-search'); s.els['sfs-name'].textContent = 'Hive review';
out.siftSearch = s.pageTitle();
lone(s, 'library'); s.els['home-project'].hidden = true; out.siftHome = s.pageTitle();
const r = lone(world('trace'), 'trace'); r.els['tr-name'].textContent = 'Hive claims';
out.trace = r.pageTitle();
console.log(JSON.stringify(out));
"""


def test_lockup_headroom(scratch: Path):
    print("\n333. The lockup's clear space (6 November, Adam): at least its mark's height under the title bar, measured "
          "in a real browser on Home's head in each app, the bar's and About's lockups too, and the window's title in "
          "the app's name first, then the project, the participant and the screen")
    app_js = support.text(*support.APP_JS)
    style = support.text("family/static/style.css")

    # ── A. the clear space, in a real browser
    got = _clear_space(scratch)
    if got is not None:
        homes = ("preview", "idiograph", "sift", "trace")
        short = [(w, k, round(got[str(w)][k]["lockup"]["top"], 2), got[str(w)][k]["lockup"]["h"])
                 for w in WIDTHS for k in homes if str(w) in got
                 and got[str(w)][k]["lockup"]["top"] < got[str(w)][k]["lockup"]["h"] - 0.5]
        check("333: on Home's head the lockup's top stands at least its mark's height under the page's top, in Idiograph's "
              "Preview Edition, Idiograph's plain lockup, Sift's and Trace's, at 1280 and 720, each at Large (125%) as "
              "1024 and 576 of page, and at a narrow tab's 360",
              len(got) == len(WIDTHS) and not short, f"{short} {str(got)[:300]}")
        check("333: the mark's height there is the lockup's own, 32 for the Preview Edition's and 24 for the others, so the "
              "space scales with the lockup",
              all(got[str(w)]["preview"]["lockup"]["h"] == 32 and all(got[str(w)][k]["lockup"]["h"] == 24 for k in homes[1:])
                  for w in WIDTHS if str(w) in got), str({k: v["preview"]["lockup"]["h"] for k, v in got.items()}))
        check("333: the tools stay level with the lockup as Home's head set them, their top the wordmark's 3 px above the "
              "lockup's, at every width and in each app",
              all(abs(got[str(w)][k]["lockup"]["top"] - got[str(w)][k]["tools"]["top"] - 3) < 0.5
                  for w in WIDTHS for k in homes if str(w) in got),
              str([(w, k, got[str(w)][k]["lockup"]["top"], got[str(w)][k]["tools"]["top"]) for w in WIDTHS for k in homes][:6]))
        # to the left (Adam, 6 November 2026, margin 32 at every width): from 560 of page the lockup, the projects' column
        # under it and so the preview box and the title stand 32px in, which is at least the mark's height, the Preview
        # Edition's 32 included, and on one edge. Below 560, a phone's tab, the page's 16px gutter stays
        wide = [w for w in WIDTHS if str(w) in got and w >= 560]
        lefts = [(w, k, got[str(w)][k]["lockup"]["left"], got[str(w)][k]["lockup"]["h"], got[str(w)][k]["body"]["left"])
                 for w in wide for k in homes if got[str(w)][k]["lockup"]["left"] < got[str(w)][k]["lockup"]["h"] - 0.5]
        check("333: on Home's head the lockup stands at least its mark's height from the page's left edge, the Preview "
              "Edition's 32 included, at 1280, 1050 and 720 and at Large's 1024 and 576, and the projects' column under "
              "it stands on the same edge",
              len(wide) == 5 and not lefts
              and all(abs(got[str(w)][k]["lockup"]["left"] - got[str(w)][k]["body"]["left"]) < 0.5 for w in wide for k in homes),
              f"{lefts} {[(w, got[str(w)]['preview']['lockup']['left'], got[str(w)]['preview']['body']['left']) for w in wide]}")
        check("333: a wide window is as it was, the column still 1048px wide at 1280 and centred, and a phone's tab "
              "keeps the page's 16px gutter",
              got["1280"]["preview"]["body"]["w"] == 1048 and got["360"]["preview"]["lockup"]["left"] == 16
              and got["1280"]["preview"]["lockup"]["left"] > 32,
              str((got["1280"]["preview"]["body"], got["360"]["preview"]["lockup"])))
        # the bar's lockup stands in the app's windows, 720 CSS pixels of page and wider: below that the bars show the
        # mark alone on a first row of its own, which is a mark and not a lockup (docs/design.md, Clear space)
        bars = [(w, got[str(w)]["bar"]) for w in WIDTHS if str(w) in got and w >= 720]
        check("333: the bar's small lockup keeps its mark's height above it by its own rule, centred in the bar with no "
              "room to spare: its top is no nearer the page's top than its height, and no nearer the left, at 1280, 1050, "
              "Large's 1024 and the smallest window, 720",
              len(bars) == 4 and all(b["top"] >= b["h"] - 0.5 and b["left"] >= b["h"] - 0.5 for _, b in bars), str(bars))
        abouts = [(w, got[str(w)]["about"]) for w in WIDTHS if str(w) in got]
        check("333: About's lockup stands at least its mark's height inside its card's edge, above and to the left",
              abouts and all(a["top"] >= a["h"] and a["left"] >= a["h"] for _, a in abouts), str(abouts))

    # ── B. the design's rule, written where the marks are
    design = support.text("docs/design.md")
    marks = design.split("\n## Marks\n", 1)[1].split("\n## Components\n", 1)[0]
    clear = " ".join((marks.split("### Clear space", 1)[1] if "### Clear space" in marks else "").split())
    check("333: the design system's Marks section holds a Clear space rule: at least the mark's height above and to the "
          "left, measured from the bottom of the window's title bar, scaling with the lockup, with a line for Home's head, "
          "the project page's head, About and the bars, the bars' case stated as its own rule",
          bool(clear) and "bottom of the window's title bar" in clear and "scales with the lockup" in clear
          and all(place in clear for place in ("Home's head", "project's page", "About", "The bars")), clear[:200])
    lockup_row = next((ln for ln in design.splitlines() if ln.startswith("| Lockup |")), "")
    check("333: the Components table's Lockup row names the clear space",
          "clear space" in lockup_row.lower(), lockup_row[:160])
    check("333: Home's head takes its top from the mark's height (--mark-h), 32px on the Preview Edition's Home and 24px "
          "elsewhere, and keeps no fixed 11 px",
          "--head-top: calc(var(--mark-h) - 3px);" in style and "--mark-h: 24px;" in style
          and 'html[data-app="idiograph"][data-edition="preview"] .lib-head { --mark-h: 32px; }' in style
          and "calc((46px - 24px) / 2)" not in style)

    # ── C. the title of each screen, in node
    node = shutil.which("node")
    if node:
        bits = "\n".join([support.i18n_js(), "const FAMILY_APPS = {};", support.distil_hooks(app_js),
                          js_const(app_js, "caseShown"), js_function(app_js, "distilTitle"), js_const(app_js, "titleShown"),
                          js_const(app_js, "titleText"), js_const(app_js, "titled"), js_function(app_js, "pageTitle")])
        bits_file = scratch / "titles-333-bits.js"
        bits_file.write_text(bits, encoding="utf-8")
        harness = scratch / "titles-333.js"
        harness.write_text(TITLES, encoding="utf-8")
        run = subprocess.run([node, str(harness), str(bits_file)], capture_output=True, text=True, encoding="utf-8")
        try:
            titles = json.loads(run.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            titles = {}
        check("333: Home's title is the app's name alone, and a project's page is the app and its project",
              titles.get("home") == "Idiograph" and titles.get("project") == "Idiograph - Beach walks", str(titles)[:300] + run.stderr[-300:])
        check("333: the statements screen's title is the app, the project, the participant as the screens show it, with "
              "the number and name joined by a space, and the screen, and a part the screen has none of leaves no dash behind",
              titles.get("work") == "Idiograph - Beach walks - P2 Wren - Experiential statements"
              and titles.get("workNoProject") == "Idiograph - P2 Wren - Experiential statements"
              and titles.get("workBare") == "Idiograph - Beach walks - Wren - Experiential statements", str(titles)[:400])
        check("333: PETs and a participant's LPETs name the participant, the GETs and the LGETs the project alone, each after "
              "the app and its project",
              titles.get("pets") == "Idiograph - Beach walks - P2 Wren - PETs"
              and titles.get("lpets") == "Idiograph - Beach walks - P2 Wren - LPETs"
              and titles.get("gets") == "Idiograph - Beach walks - GETs"
              and titles.get("lgets") == "Idiograph - Beach walks - LGETs", str(titles)[:400])
        check("333: Trajectories and the Code list follow the same order",
              titles.get("traj") == "Idiograph - Beach walks - Trajectories"
              and titles.get("codes") == "Idiograph - Beach walks - Code list", str(titles)[:300])
        check("333: Sift's and Trace's windows are the app and the project, and the app alone with none open",
              titles.get("sift") == "Sift - Hive review" and titles.get("siftSearch") == "Sift - Hive review"
              and titles.get("siftHome") == "Sift" and titles.get("trace") == "Trace - Hive claims", str(titles)[:300])
        check("333: no title has a dash left standing, doubled or at an end",
              all(v and not v.startswith("-") and not v.endswith("-") and " -  - " not in v and "- -" not in v
                  for v in titles.values()) and len(titles) >= 12, str(titles)[:300])
    else:
        skip("333: the title of each screen under node", "node is not on this machine")

    # ── D. the window takes the page's title as it stands, on a Mac and on Windows alike
    main_rs = support.text("packaging/tauri/src-tauri/src/main.rs")
    handlers = [m.start() for m in re.finditer(r"\.on_document_title_changed\(", main_rs)]
    check("333: every window of the app takes its title from the page's, set as the page changes it, so the Mac's and "
          "Windows's window titles follow `document.title` and need no word of their own",
          len(handlers) >= 3 and all("set_title(" in main_rs[h:h + 400] for h in handlers), str(len(handlers)))
