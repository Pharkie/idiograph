from __future__ import annotations

import json
import shutil
import subprocess

from . import support
from .support import check, skip


def test_bars_option_c(scratch):
    print("\n269. The bars of option C (Adam, 26 October 2026): the lockup and three tabs on the title bar, the path at "
          "the head of the research question's band in place of the back arrow, the sidebars' buttons at the toolbar's "
          "two ends, and Canvas and Table on the toolbar directly after Auto-saved, which Adam moved there from the status bar on "
          "26 October. What matters is what each does: the tabs open their stages, "
          "the lockup goes Home and the participant's chooser where it says (the path's Home and the project's link "
          "gone since option D, 6 November 2026, area 330), the buttons open and close their panels, and "
          "Canvas and Table switch. Their places, words and sizes are review shots")
    page = support.page_text()
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    tjs = support.text("apps/idiograph/static/themes.js")
    traj = support.text("apps/idiograph/static/trajectories.js")
    sift, sift_s, trace = (support.text("apps/sift/static/sift.js"), support.text("apps/sift/static/sift_search.js"),
                           support.text("apps/trace/static/trace.js"))
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: (("async " if f"async function {name}(" in src else "") + f"function {name}(" + fn(src, name) + "\n}")
    part = lambda sid: page.split(f'<section id="{sid}"', 1)[1].split("</section>", 1)[0]
    work, themes, tj = part("work"), part("themes"), part("traj")

    # ── A. the tabs open their stages, every screen's
    check("269: each bar's tabs open their stage, the statements screen's by esStep, the boards' by thStepTo and "
          "Trajectories' by trajStep",
          "$('es-step-pets').onclick = () => esStep('pets');" in app and "$('es-step-gets').onclick = () => esStep('gets');" in app
          and "$(id).onclick = () => thStepTo(step);" in tjs and "$(id).onclick = () => trajStep(step);" in traj)

    # ── B. the path: the project from every screen, the participant chooser where there is one, and since option D
    # (6 November 2026) no Home in it, the lockup being Home
    rail_of = lambda sec: sec.split('<div class="rail', 1)[1].split("\n  </div>", 1)[0]
    band_of = lambda sec: sec.split('<div class="band"', 1)[1].split("\n  </div>", 1)[0]
    check("269, updated 6 November 2026 (barsD): the back arrow is gone from Idiograph's, Sift's and Trace's bars, and "
          "each of Idiograph's bands opens with the path, the project, and on a participant's stages the participant's chooser",
          all(b not in page + sift_s + trace for b in ('id="to-library"', 'id="th-back"', 'id="tj-back"', 'id="sf-back"',
                                                        'id="sfs-back"', 'id="tr-back"'))
          and all('class="ds-path"' in band_of(sec) for sec in (work, themes, tj))
          and 'id="es-who"' in band_of(work) and 'id="th-cases"' in band_of(themes) and 'id="es-who"' not in rail_of(work)
          and 'id="th-cases"' not in rail_of(themes))
    check("269, updated 6 November 2026 (barsD, option D): the bars' lockup goes Home on every screen, Trajectories' "
          "by its own way home, the path has no Home of its own in any of the three apps, and Sift's and Trace's "
          "project's name opens its menu, as Idiograph's does (area 330)",
          "for (const id of ['es-home', 'th-home']) $(id).onclick = () => goHome();" in app
          and "$('tj-home').onclick = () => trajHome();" in traj
          and "$('cd-home').onclick = () => codesHome();" in support.text("apps/idiograph/static/codes.js")
          and "ds-path-home" not in page + sift_s + trace and "path-home" not in app + tjs + traj + sift + sift_s + trace
          and "$('sf-home').onclick = () => sfBack();" in sift
          and "bandMenuWire('sf-name', () => siftBandMenu());" in sift
          and "$('sfs-home').onclick = sfsBack;" in sift_s
          and "$('tr-home').onclick = () => goHome();" in trace
          and "bandMenuWire('tr-name', traceBandMenu);" in trace)

    # ── C. the toolbar holds the sidebars' buttons, the board, Auto-saved and then Canvas and Table (Adam, 26 October 2026:
    # the switch is not a status bar thing)
    dock = themes.split('<div class="th-dock" id="th-dock"', 1)[1].split("\n  </div>", 1)[0]
    status = themes.split('id="th-status"', 1)[1].split("\n    </div>", 1)[0]
    check("269: the left sidebar's button and the Inspector's stand at the toolbar's two ends with the board between, "
          "each still opening and closing its panel, and Canvas and Table stand on the toolbar directly after the board "
          "and Auto-saved, gone from the status bar, a click still switching",
          dock.index('id="th-open-cases"') < dock.index('id="th-board"') < dock.index('th-dock-end') < dock.index('id="th-open-side"')
          and 'id="th-open-cases"' not in rail_of(themes) and 'id="th-open-side"' not in rail_of(themes)
          and "$('th-open-cases').onclick = () => (TH.casesOpen ? gtCasesShut() : gtCasesOpen());" in tjs
          and "$('th-open-side').onclick = () => thSideDoor();" in tjs
          and dock.index('id="th-board"') < dock.index('id="th-save"') < dock.index('id="th-faces"') < dock.index('th-dock-end')
          # the save state under the board's name, the two in one column (barsD, 6 November 2026)
          and dock.index('class="th-boardname"') < dock.index('id="th-board"')
          and dock.index('id="th-faces"') < dock.index('id="th-board-sep"')
          and 'id="th-faces"' not in status and 'th-faces-sep' not in status and 'id="th-faces"' not in rail_of(themes)
          and "if (b && TH.live) thFace(b.dataset.face);" in tjs)

    node = shutil.which("node")
    if not node:
        skip("269: the bars in node", "node is not on this machine")
        return
    harness = r"""
const out = {};
const calls = [];
const els = {};
const mk = (id) => ({ id, hidden: false, title: '', textContent: '', dataset: {}, kids: [], parentElement: null, nextElementSibling: null,
  offsetHeight: 40, attrs: {}, classList: { set: new Set(), add(...n) { n.forEach((x) => this.set.add(x)); }, remove(...n) { n.forEach((x) => this.set.delete(x)); },
    contains(n) { return this.set.has(n); }, toggle(n, on) { if (on === undefined) on = !this.set.has(n); if (on) this.set.add(n); else this.set.delete(n); return on; } },
  setAttribute(k, v) { this.attrs[k] = String(v); }, style: { setProperty(k, v) { this[k] = v; } },
  querySelector(sel) { return sel === '.th-dock-end' ? els['th-dock-end'] || null : null; },
  appendChild(k) { this.place(k, null); }, insertBefore(k, before) { this.place(k, before); },
  place(k, before) { if (k.parentElement) k.parentElement.kids = k.parentElement.kids.filter((x) => x !== k); const at = before ? this.kids.indexOf(before) : -1;
    if (at < 0) this.kids.push(k); else this.kids.splice(at, 0, k); k.parentElement = this; this.kids.forEach((x, i) => { x.nextElementSibling = this.kids[i + 1] || null; }); },
  getBoundingClientRect: () => ({ top: 0, bottom: 0, left: 0 }), getClientRects: () => [] });
const $ = (id) => (els[id] = els[id] || mk(id));
const S = { homing: false, backTo: { to: 'pets' } };
const DEMO_ID = 'demo';
let HERE = { screen: 'pets', path: 'walks/P1 Ada/P1 Ada - EN & ES.xlsx' };
let LEAVES = true;
const searchWhere = () => HERE;
const searchLeaveFor = async (here) => { calls.push(['leave', here.screen]); return LEAVES; };
const homeKeep = (id) => calls.push(['keep', id]);
const loadLibrary = async () => calls.push(['library']);
const say = (t) => calls.push(['say', t]);
const window = { scrollTo: () => {} };
let TH = { lpets: false, mode: 'pets', lgets: false, config: {} };
const thGets = () => TH.mode === 'gets';
const thPaletteFit = () => {};
""" + "\n".join(["const whoName = " + app.split("const whoName = ", 1)[1].split("\n", 1)[0],
                 "const caseShown = " + app.split("const caseShown = ", 1)[1].split("\n", 1)[0],
                 "const TH_TOOLS = " + tjs.split("const TH_TOOLS = ", 1)[1].split("\n};", 1)[0] + "\n};",
                 "const thStageNow = " + tjs.split("const thStageNow = ", 1)[1].split("\n", 1)[0],
                 "const thDocked = " + tjs.split("const thDocked = ", 1)[1].split("\n", 1)[0],
                 "const thCaseLabel = " + tjs.split("const thCaseLabel = ", 1)[1].split("\n};", 1)[0] + "\n};",
                 whole(tjs, "thWhoDraw"), whole(tjs, "thPickerPlace"), whole(tjs, "thBandMeasure"), whole(tjs, "thPalettePlace"),
                 whole(tjs, "thPaletteHeld"), whole(tjs, "thPaletteRoom"), "const TH_PALETTE_HOME = { edge: 'left', y: 0.38 };"]) + r"""
(async () => {
  // the path's project is no longer a way to its page (option D, 6 November 2026): its "..." is area 330's
  // the participant's chooser on PETs and LPETs, none on GETs and LGETs, and LPETs naming the participant as PETs does
  const shown = {};
  for (const [name, t] of [['pets', { mode: 'pets' }], ['lpets', { mode: 'gets', lpets: true }], ['gets', { mode: 'gets' }],
    ['lgets', { mode: 'gets', lgets: true }]]) { TH = Object.assign({ config: {} }, t); thPickerPlace(); shown[name] = !$('th-cases').hidden; }
  out.chooser = shown;
  thWhoDraw('P1 - Wren');
  out.who = [$('th-case').textContent, $('th-case').title, thCaseLabel()];
  thWhoDraw('Mabel');
  out.plain = [$('th-case').textContent, thCaseLabel()];
  // the toolbar's dock stays with the band when the tools float, so the sidebars' buttons and the board stay
  const dock = $('th-dock'); const end = $('th-dock-end'); dock.appendChild($('th-open-cases')); dock.appendChild(end); dock.appendChild($('th-open-side'));
  const screen = $('themes'); screen.hidden = false; screen.querySelector = () => null;
  TH = { config: { palette_docked: false }, mode: 'pets' };
  $('th-stage').clientWidth = 0;
  thPalettePlace();
  out.floating = { dock: !dock.hidden, pal: $('th-palette').parentElement.id };
  TH = { config: {}, mode: 'pets' };
  thPalettePlace();
  out.docked = { dock: !dock.hidden, order: dock.kids.map((k) => k.id) };
  console.log(JSON.stringify(out));
})().catch((e) => { console.error(String(e && e.stack || e)); process.exit(1); });
"""
    script = scratch / "bars-269.js"
    script.write_text(support.i18n_js() + harness, encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    o = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
    check("269: in node, the participant's chooser shows on PETs and LPETs and not on GETs or LGETs, and names the "
          "participant by number and pseudonym on every stage, P1 Wren for P1 - Wren as the rows do since pbiobuild's "
          "layout A, the whole label in its tooltip and for what names the case",
          o.get("chooser") == {"pets": True, "lpets": True, "gets": False, "lgets": False}
          and o.get("who") == ["P1 Wren", "P1 - Wren", "P1 - Wren"] and o.get("plain") == ["Mabel", "Mabel"], str(o)[:400])
    check("269: in node, with the tools floating the toolbar's dock still shows, holding the sidebars' buttons, and "
          "docked again the tools stand between the board and the Inspector's button",
          o.get("floating") == {"dock": True, "pal": "th-stage"}
          and o.get("docked") == {"dock": True, "order": ["th-open-cases", "th-palette", "th-dock-end", "th-open-side"]}, str(o)[:400])

    _face_both_ways(scratch, node, tjs)

    # ── D. the status bar gives way with the counts last (Adam, 26 October 2026): in the computer's own browser,
    # headless, the page's own status bar, stylesheets and thCorners, at the canvas's width in a 1280 window with
    # Not placed open beside it and at the app's smallest window
    _bar_gives_way(scratch, node, page, tjs)

    # ── E. the toolbar holds Canvas and Table at 1280 and at 720, the app's smallest window, after Auto-saved
    _toolbar_holds_switch(page, tjs)


FACE = r"""
const calls = [];
const els = {};
const btn = (face) => ({ dataset: { face }, attrs: {}, cls: new Set(), classList: { toggle(n, on) { if (on) this.o.cls.add(n); else this.o.cls.delete(n); } },
  setAttribute(k, v) { this.attrs[k] = v; } });
const $ = (id) => {
  if (els[id]) return els[id];
  const e = { id, hidden: true, set: new Set(), classList: { toggle: (n, on) => (on ? e.set.add(n) : e.set.delete(n)) } };
  if (id === 'th-faces') { e.kids = [btn('canvas'), btn('table')]; e.kids.forEach((k) => { k.classList.o = k; }); e.querySelectorAll = () => e.kids; }
  return (els[id] = e);
};
let TH = { live: true, face: 'canvas', meta: { id: 'b1' }, mode: 'pets', path: 'bees.xlsx', v: {} };
for (const name of ['thTitleDone', 'thTableTitleDone', 'thMenuClose', 'thCountFit', 'thCorners', 'thTableDraw', 'thMeasure', 'thPlace',
  'thMapPlace', 'thPaletteFit']) globalThis[name] = () => calls.push(name);
const thFaceKeep = (mode, path, board, face) => calls.push('keep ' + face);
const seen = () => { const sw = $('th-faces'); return { shown: !sw.hidden, on: sw.kids.filter((k) => k.attrs['aria-checked'] === 'true').map((k) => k.dataset.face),
  table: $('themes').set.has('table-face'), tableShown: !$('th-table').hidden }; };
const out = {};
thFace('canvas', false); out.open = [seen(), calls.splice(0)];
thFace('table'); out.table = [seen(), calls.splice(0)];
thFace('canvas'); out.canvas = [seen(), calls.splice(0)];
console.log(JSON.stringify(out));
"""


def _face_both_ways(scratch, node, tjs):
    """thFace itself in node: the switch shown on the toolbar on a live board, in the table as on the canvas, and the
    toolbar's tools fitted again once when it first shows"""
    fn = "function thFace(" + tjs.split("function thFace(", 1)[1].split("\n}\n", 1)[0] + "\n}\n"
    script = scratch / "face-269.js"
    script.write_text(support.i18n_js() + fn + FACE, encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    o = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
    opened, table, canvas = o.get("open", [{}, []]), o.get("table", [{}, []]), o.get("canvas", [{}, []])
    check("269: in node, Canvas and Table switch both ways from the toolbar: the board opens on Canvas with the switch "
          "showing and the toolbar's tools fitted to it, Table shows the table with the switch still there to get back, "
          "and Canvas puts the canvas back, each choice kept for the board",
          opened[0] == {"shown": True, "on": ["canvas"], "table": False, "tableShown": False} and "thPaletteFit" in opened[1]
          and "keep canvas" not in opened[1]
          and table[0] == {"shown": True, "on": ["table"], "table": True, "tableShown": True} and "thTableDraw" in table[1]
          and "keep table" in table[1] and "thPaletteFit" not in table[1]
          and canvas[0] == {"shown": True, "on": ["canvas"], "table": False, "tableShown": False} and "keep canvas" in canvas[1],
          (run.stdout + run.stderr)[:600])


COUNTS = r"""
for (const id of ['th-status-counts', 'th-palette']) ELS[id] = new El(id);
ELS['th-stage'] = Object.assign(new El('th-stage'), { clientWidth: 1000, clientHeight: 600 });
ELS.bar = Object.assign(new El('bar'), { offsetHeight: 30 });
thCorners = () => {};
thMapPlace = () => {};
// an invented board about keeping bees, its numbers as long as a finished participant's: 118 in two PETs, 15
// stacked under tops in them, 12 set aside and 14 waiting in Not placed
const cards = {};
const groups = [{ id: 'P1', label: 'Learning the hive', members: [] }, { id: 'P2', label: 'Stings and patience', members: [] }];
const stacks = {};
const discarded = [];
for (let i = 0; i < 159; i++) {
  const k = 's' + i;
  cards[k] = { x: 0, y: 0, text: 'Bees ' + i, wait: i >= 145 };
  if (i < 118) groups[i % 2].members.push(k);
  else if (i < 133) stacks['s' + (i - 118)] = [k];
  else if (i < 145) discarded.push(k);
}
TH.v = { waits: true, cards, groups, discarded, stacks };
TH.mode = 'pets';
TH.config = { status_bar: true };
TH.sel = { cards: new Set(), groups: new Set(), stickies: new Set() };
thStatusDraw();
console.log(JSON.stringify({ html: ELS['th-status-counts'].innerHTML, text: ELS['th-status-counts'].textContent }));
"""

GIVE_WAY = r"""
const $ = (id) => document.getElementById(id);
const thPalettePlace = () => {};
const shows = (e) => !!e && e.getClientRects().length > 0 && getComputedStyle(e).display !== 'none';
const out = {};
for (const [name, w] of [['w1280', 980], ['w720', 720]]) {
  const stage = $('th-stage');
  stage.style.width = w + 'px';
  thCorners();
  const box = $('th-status-counts'), bar = $('th-status');
  out[name] = { cls: [...stage.classList].filter((c) => c.startsWith('th-status-') && c !== 'th-status-on'),
    total: shows(box.querySelector('.th-stat-total')),
    parts: [...box.querySelectorAll('.th-part')].filter(shows).map((e) => e.dataset.stat),
    pets: shows(box.querySelector('[data-stat="pets"]')),
    faces: !!$('th-faces'),
    words: [...bar.querySelectorAll('.th-fit-word, .th-btn-word, .th-help-word')].filter(shows).length,
    over: bar.scrollWidth > bar.clientWidth + 1, text: box.innerText.replace(/\s+/g, ' ').trim() };
}
document.getElementById('out').textContent = JSON.stringify(out);
"""


def _bar_gives_way(scratch, node, page, tjs):
    """The page's own status bar, its stylesheets and thCorners in the computer's own browser, headless, in a
    profile of its own thrown away after, the counts drawn by thStatusDraw in node on an invented board"""
    import html as html_mod
    import tempfile
    from pathlib import Path

    from .a201_status_bar_and_palette import STUBS
    exe = support.browser()
    if exe is None:
        skip("269: the status bar giving way in a real browser", "no Chrome, Chromium, Brave or Edge on this computer")
        return
    counts_js = scratch / "counts-269.js"
    counts_js.write_text(support.i18n_js() + STUBS + tjs + COUNTS, encoding="utf-8")
    run = subprocess.run([node, str(counts_js)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    if run.returncode != 0 or not run.stdout.strip():
        check("269: the status bar's counts drawn in node for the browser", False, run.stderr.strip()[:600])
        return
    drawn = json.loads(run.stdout.strip().splitlines()[-1])
    head = '<div class="th-ui th-zoomer" id="th-status"'
    bar = head + page.split(head, 1)[1].split("\n    </div>", 1)[0] + "\n    </div>"
    bar = bar.replace('<span class="th-status-counts" id="th-status-counts" role="status" aria-live="polite"></span>',
                      f'<span class="th-status-counts" id="th-status-counts" role="status">{drawn["html"]}</span>')
    bar = bar.replace('role="radiogroup" aria-label="View" hidden>', 'role="radiogroup" aria-label="View">')
    css = "\n".join(support.text(p) for p in ("family/static/tokens.css", "family/static/style.css",
                                              "apps/idiograph/static/distil.css", "apps/idiograph/static/themes.css"))
    corners = ("const TH_STATUS_STEPS = " + tjs.split("const TH_STATUS_STEPS = ", 1)[1].split(";\n", 1)[0] + ";\n"
               + "function thCorners(" + tjs.split("function thCorners(", 1)[1].split("\n}\n", 1)[0] + "\n}\n")
    doc = ('<!doctype html><html><head><meta charset="utf-8"><style>' + css + "</style></head><body>"
           '<div class="th-screen" style="display: flex; height: 300px;"><div class="th-stage th-status-on" id="th-stage" '
           'style="flex: none; height: 300px;">' + bar + '<div class="th-ui th-discard" id="th-discard"></div></div></div>'
           '<pre id="out">none</pre><script>' + support.i18n_js() + corners + GIVE_WAY + "</script></body></html>")
    with tempfile.TemporaryDirectory(prefix="idiograph-269-") as tmp:
        page_file = Path(tmp) / "bar.html"
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
    four = ["placed", "stacked", "binned", "unplaced"]
    wide, narrow = o.get("w1280", {}), o.get("w720", {})
    check("269: in a real browser, with the canvas as wide as a 1280 window leaves beside Not placed, the PETs status bar "
          "says the total and all four parts, \"159 ES: 118 in PETs, 15 stacked, 12 set aside, 14 not placed\", and the "
          "PETs, Canvas and Table gone from it to the toolbar, the tools' words giving way first and nothing overflowing",
          drawn["text"].startswith("159 ES: 118 in PETs, 15 stacked, 12 set aside, 14 not placed")
          and wide.get("total") is True and wide.get("parts") == four and wide.get("pets") is True and wide.get("faces") is False
          and wide.get("over") is False and not {"th-status-trim", "th-status-least", "th-status-bare"} & set(wide.get("cls", [])),
          str(o)[:700] + " " + drawn["text"][:120])
    check("269: in a real browser at the app's smallest window, 720, the total and its four parts still show, the "
          "tools and their words having given way before them, and nothing overflowing",
          narrow.get("total") is True and narrow.get("parts") == four and narrow.get("faces") is False
          and narrow.get("words") == 0 and narrow.get("over") is False
          and not {"th-status-least", "th-status-bare"} & set(narrow.get("cls", [])), str(o)[:700])


TOOLBAR = r"""
const $ = (id) => document.getElementById(id);
const shows = (e) => !!e && e.getClientRects().length > 0 && getComputedStyle(e).display !== 'none' && getComputedStyle(e).visibility !== 'hidden';
thPaletteFit();
const box = (id) => { const r = $(id).getBoundingClientRect(); return { l: r.left, r: r.right, t: r.top, b: r.bottom }; };
const dock = $('th-dock'), f = box('th-faces'), save = box('th-save'), board = box('th-board');
const tools = [...document.querySelectorAll('#th-palette .th-pal-btn')].filter(shows);
const words = [...document.querySelectorAll('#th-palette .th-pal-word')].filter(shows).map((e) => e.textContent.trim());
const res = ({ words, fits: [...document.querySelectorAll('#th-palette [data-align], #th-palette [data-spread]')].some(shows), more: shows($('th-pal-more')),
  faces: shows($('th-faces')) && [...$('th-faces').querySelectorAll('button')].every(shows), save: shows($('th-save')), board: shows($('th-board')),
  // Auto-saved under the board's name, the two one column, and Canvas and Table after both, level with the pair (barsD)
  under: save.t >= board.b - 1 && Math.abs(save.l - board.l) < 2, after: f.l >= Math.max(save.r, board.r),
  row: Math.abs((f.t + f.b) / 2 - (board.t + save.b) / 2) < 3,
  cut: [...document.querySelectorAll('#th-dock button')].filter(shows).some((e) => { const r = e.getBoundingClientRect(); return r.right > innerWidth + 0.5 || r.left < -0.5; }),
  over: dock.scrollWidth > dock.clientWidth + 1, palOver: $('th-palette').scrollWidth > $('th-palette').clientWidth + 1, tools: tools.length,
  steps: ['snug', 'terse', 'bare', 'fold'].filter((c) => $('th-palette').classList.contains(c)) });
"""

# The dots' menu in the same page (option B, Adam, 26 October 2026): the app's own thToolMenu, thAlignRows,
# thAlignMoreRows, thAlignMore, thMenuClose and thPaletteState, the dots and the eight buttons wired as the app
# wires them, and thAlignDo recording the plan thAlignPlan makes of an invented selection for the way it is given
MENU = r"""
const BOXES = [{ id: 'a', x: 40, y: 10, w: 200, h: 90 }, { id: 'b', x: 400, y: 160, w: 200, h: 120 }, { id: 'c', x: 90, y: 420, w: 200, h: 90 }];
let picked = 0;
const done = [];
var TH = { v: { readonly: false }, menu: null };
const thLocked = (v) => !!(v && v.readonly);
const thAlignIds = () => BOXES.slice(0, picked).map((b) => b.id);
const thAlignDo = (how) => done.push(JSON.stringify(thAlignPlan(BOXES.slice(0, picked), how)));
const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
const TH_TICK_ICON = '';
const thArrangeWay = () => 'grid';
const TH_WAY_ICONS = { grid: '' };
const TH_WAY_NAMES = { grid: 'Grid' };
$('th-pal-more').onclick = (e) => { e.stopPropagation(); if (TH.menu && TH.menu.button === e.currentTarget) thMenuClose(); else thAlignMore(); };
const eight = [...document.querySelectorAll('#th-palette [data-align], #th-palette [data-spread]')];
for (const b of eight) b.onclick = () => thAlignDo(b.dataset.align || b.dataset.spread);
const menuRows = () => {
  $('th-pal-more').click();
  const pop = document.querySelector('.th-tbmenu');
  const rows = pop ? [...pop.querySelectorAll('[data-tbpick]')] : [];
  return { pop, rows, heads: pop ? [...pop.querySelectorAll('.th-cmenu-head')].map((h) => h.textContent) : [],
    on: rows.filter((r) => !r.disabled).map((r) => r.textContent.trim()), icons: rows.every((r) => !!r.querySelector('svg')) };
};
const menu = {};
for (const [name, n, locked] of [['none', 0, false], ['one', 1, false], ['two', 2, false], ['three', 3, false], ['locked', 3, true]]) {
  picked = n; TH.v.readonly = locked; thPaletteState();
  const m = menuRows();
  menu[name] = { heads: m.heads, words: m.rows.map((r) => r.textContent.trim()), on: m.on, icons: m.icons,
    buttonsOn: eight.filter((b) => !b.disabled).length };
  thMenuClose();
}
picked = 3; TH.v.readonly = false; thPaletteState();
menu.same = eight.map((b) => {
  const word = b.querySelector('.th-pal-word').textContent.trim();
  done.length = 0;
  b.click();
  const m = menuRows();
  const row = m.rows.find((r) => r.textContent.trim() === word);
  if (row) row.click();
  const shut = !document.querySelector('.th-tbmenu');
  thMenuClose();
  return { word, button: done[0], menu: done[1], shut, same: !!done[0] && done[0] === done[1] };
});
res.menu = menu;
"""


def _toolbar_holds_switch(page, tjs):
    """The page's own toolbar, the tools docked in it as thPalettePlace puts them, its stylesheets and thPaletteFit, in
    the computer's own browser, headless, at 1280 and at 720 wide"""
    import html as html_mod
    import tempfile
    from pathlib import Path

    exe = support.browser()
    if exe is None:
        skip("269: the toolbar holding Canvas and Table in a real browser", "no Chrome, Chromium, Brave or Edge on this computer")
        return
    head = '<div class="th-dock" id="th-dock" hidden>'
    dock = head + page.split(head, 1)[1].split("\n  </div>", 1)[0] + "\n  </div>"
    pal_head = '<div class="th-ui th-palette" id="th-palette"'
    pal = pal_head + page.split(pal_head, 1)[1].split("\n    </div>", 1)[0] + "\n    </div>"
    pal = pal.replace('class="th-ui th-palette"', 'class="th-ui th-palette docked"', 1)
    end = '<span class="rail-sep th-dock-rule th-dock-end"'
    dock = dock.replace(end, pal + "\n    " + end, 1).replace(head, '<div class="th-dock" id="th-dock">', 1)
    dock = (dock.replace('id="th-open-cases" data-door="cases" aria-label="Participants"\n              aria-pressed="false" title="Show Participants" hidden>',
                         'id="th-open-cases" data-door="cases" aria-label="Statements"\n              aria-pressed="false" title="Show Statements">')
            .replace('<span class="bar-word" aria-hidden="true">Participants</span>', '<span class="bar-word" aria-hidden="true">Statements</span>')
            .replace('id="th-board" hidden', 'id="th-board"')
            .replace('<span class="th-vname" id="th-board-name"></span>', '<span class="th-vname" id="th-board-name">Board 1</span>')
            .replace('id="th-board-chosen" hidden', 'id="th-board-chosen"')
            .replace('<span class="th-save" id="th-save" role="status" aria-live="polite" hidden></span>',
                     '<span class="th-save done" id="th-save" role="status">Auto-saved</span>')
            .replace('role="radiogroup" aria-label="View" hidden>', 'role="radiogroup" aria-label="View">'))
    css = "\n".join(support.text(p) for p in ("family/static/tokens.css", "family/static/style.css",
                                              "apps/idiograph/static/distil.css", "apps/idiograph/static/themes.css"))
    fit = ("const TH_TOOLS = " + tjs.split("const TH_TOOLS = ", 1)[1].split("\n};", 1)[0] + "\n};\n"
           + "const TH_PAL_STEPS = " + tjs.split("const TH_PAL_STEPS = ", 1)[1].split(";\n", 1)[0] + ";\n"
           + "const TH_DOCK_STEPS = " + tjs.split("const TH_DOCK_STEPS = ", 1)[1].split(";\n", 1)[0] + ";\n"
           + "function thPaletteFit(" + tjs.split("function thPaletteFit(", 1)[1].split("\n}\n", 1)[0] + "\n}\n")
    take = lambda name: "function " + name + "(" + tjs.split("function " + name + "(", 1)[1].split("\n}\n", 1)[0] + "\n}\n"
    const = lambda name: "const " + name + " = " + tjs.split("const " + name + " = ", 1)[1].split(";\n", 1)[0] + ";\n"
    menu_js = ("".join(const(c) for c in ("TH_MARGIN", "TH_ALIGN_WAYS", "TH_SPREAD_WAYS", "TH_ALIGN_NAMES", "TH_ALIGN_WORDS"))
               + "".join(take(f) for f in ("thAlignPlan", "thPaletteState", "thToolMenu", "thAlignRows", "thAlignMoreRows",
                                           "thAlignMore", "thMenuClose")) + MENU)
    doc = ('<!doctype html><html><head><meta charset="utf-8"><style>' + css + "</style></head><body>"
           '<section id="themes" class="screen th-screen">' + dock + '</section><pre id="out">none</pre><script>' + support.i18n_js()
           + fit + TOOLBAR + menu_js + "document.getElementById('out').textContent = JSON.stringify(res);</script></body></html>")
    seen = {}
    with tempfile.TemporaryDirectory(prefix="idiograph-269t-") as tmp:
        page_file = Path(tmp) / "toolbar.html"
        page_file.write_text(doc, encoding="utf-8")
        for w in (1280, 720):
            cmd = [str(exe), "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
                   "--disable-background-networking", "--disable-component-update", "--disable-sync", "--disable-default-apps",
                   "--password-store=basic", "--use-mock-keychain", f"--user-data-dir={Path(tmp) / ('profile%d' % w)}",
                   f"--window-size={w},800", "--virtual-time-budget=3000", "--dump-dom", page_file.as_uri()]
            try:
                dumped = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=120).stdout
            except (OSError, subprocess.TimeoutExpired) as err:
                dumped = str(err)
            said = dumped.split('<pre id="out">', 1)[1].split("</pre>", 1)[0] if '<pre id="out">' in dumped else "{}"
            seen[w] = json.loads(html_mod.unescape(said)) if said.startswith("{") else {}
    for w in (1280, 720):
        o = seen[w]
        check(f"269, updated 6 November 2026 (barsD): in a real browser {w} wide, the toolbar shows Canvas and Table whole "
              "on the board's row directly after the board's name and Auto-saved under it, every tool in reach and nothing "
              "overflowing",
              o.get("faces") is True and o.get("save") is True and o.get("board") is True and o.get("under") is True
              and o.get("after") is True
              and o.get("row") is True and o.get("cut") is False and o.get("over") is False and o.get("palOver") is False
              and (o.get("tools") or 0) > 0, str(o)[:500])
    wide, narrow = seen[1280], seen[720]
    check("269: in a real browser 1280 wide, the docked toolbar keeps the words of Sticky note, Group, Auto-arrange, "
          "Undo and Redo, with Align and Spread under the dots in place of their eight buttons (option B, Adam, 26 "
          "October 2026), and at 720 the dots still hold them",
          all(w in (wide.get("words") or []) for w in ("Sticky note", "Group", "Auto-arrange", "Undo", "Redo"))
          and wide.get("fits") is False and wide.get("more") is True and "fold" in (wide.get("steps") or [])
          and "bare" not in (wide.get("steps") or []) and narrow.get("fits") is False and narrow.get("more") is True,
          str({w: {k: seen[w].get(k) for k in ("words", "fits", "more", "steps")} for w in seen})[:600])
    m = wide.get("menu") or {}
    align, spread = ["Left", "Centre", "Right", "Top", "Middle", "Bottom"], ["Across", "Down"]
    check("269: in a real browser, the dots open Align and Spread as two sections, each way with its icon and its word, "
          "every row faint with nothing or one card selected, Align's six with two and Spread's two only with three, "
          "and all faint on a revision on view, as the toolbar's buttons were",
          all(m.get(k, {}).get("heads") == ["Align", "Spread"] and m.get(k, {}).get("words") == align + spread
              and m.get(k, {}).get("icons") is True for k in ("none", "one", "two", "three", "locked"))
          and m.get("none", {}).get("on") == [] and m.get("one", {}).get("on") == [] and m.get("two", {}).get("on") == align
          and m.get("three", {}).get("on") == align + spread and m.get("locked", {}).get("on") == []
          and [m.get(k, {}).get("buttonsOn") for k in ("none", "one", "two", "three", "locked")] == [0, 0, 6, 8, 0],
          str({k: v for k, v in m.items() if k != "same"})[:700])
    same = m.get("same") or []
    check("269: in a real browser, each of the dots' eight rows does to a selection of three what its button did, the "
          "same places for every card, and the menu shuts once chosen",
          len(same) == 8 and all(r.get("same") and r.get("shut") for r in same), str(same)[:700])
