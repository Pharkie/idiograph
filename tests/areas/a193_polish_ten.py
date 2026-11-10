"""Area 193: the sweep's Wrong and Rough of 18 October, polish 10, what of it is behaviour.

Search in shows only where a screen offers more than one place to search, so the home screen, which
offers Everything alone, shows no drop-down of one. At a phone's width a heading in Search's filters
stands only over rows: one whose rows are all behind More is hidden with them. Run in node on the
functions themselves, every project and kind invented, on lighthouse keeping.
"""
from __future__ import annotations

import json
import shutil
import subprocess

from . import support
from .support import check, skip


def test_polish_ten(scratch):
    print("\n193. Polish 10, 18 October: Search in only where there is a choice, and a filter heading only over rows")
    sjs = support.text("family/static/search.js")
    node = shutil.which("node")

    def whole(name):
        """A function of search.js whole, or "" when there is none."""
        if f"function {name}(" not in sjs:
            return ""
        at = sjs.index(f"function {name}(")
        return sjs[at:sjs.index("\n}", at) + 2]

    scopes_line = next((ln for ln in sjs.splitlines() if ln.startswith("const SEARCH_SCOPES = {")), "")
    scopes_tail = sjs.split(scopes_line, 1)[1].split("\n", 2)[1] if scopes_line else ""
    if not node:
        skip("193: node is not on this machine, so the search card's checks did not run")
        return

    # ── Search in, only where there is a choice
    script = scratch / "search-in-193.js"
    script.write_text(scopes_line + "\n" + scopes_tail + "\n" + r"""
const el = () => ({ hidden: true, value: '', innerHTML: '', focus() {}, select() {}, closest() { return IN; } });
const IN = { hidden: false };
const els = {};
const $ = (id) => (els[id] = els[id] || el());
const SEARCH = { kinds: new Set(), cases: new Set(), sheets: new Set(), projects: new Set(), q: 'lamp', scope: '', context: '' };
const S = {};
let HERE = null;
const searchWhere = () => HERE;
const searchOpen = () => false;
const noop = () => {};
const [closeFind, closeEditor, closeTimeEdit, closeRowMenu, viewMenu, thVmenu, thXmenu, thCasemenu, thMenuClose, sfMenuOpen,
  searchPlace, searchBars, searchDraw, searchRun] = Array(14).fill(noop);
const document = { querySelector: () => null };
const window = { scrollBy: noop, scrollTo: noop };
// an app's own screen's menus put away by its own script (Sift's, sift_settings.js, since the family codebase's third build)
const familyApp = (screen) => (screen === 'sift' || screen === 'searches' ? { searchClear: noop } : null);
""" + whole("searchScopes") + "\n" + whole("openSearch") + r"""
const out = {};
for (const [name, here] of [['home', { screen: 'home' }], ['statements', { screen: 'statements', path: 'keeper.xlsx' }],
  ['project', { screen: 'project', root: '/lights' }], ['sift', { screen: 'sift', folder: '/lens review' }], ['trace', { screen: 'trace', folder: '/fog bell' }]]) {
  HERE = here;
  IN.hidden = name === 'home' ? false : true;
  openSearch();
  out[name] = { shown: !IN.hidden, options: (els['search-scope'].innerHTML.match(/<option/g) || []).length };
}
console.log(JSON.stringify(out));
""", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    got = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
    check("193: in node, Search in shows no drop-down on the home screen, where Everything is the one place to search, and "
          "shows on a case's screens, a project's page, Sift and Trace, where there is more than one",
          got.get("home") == {"shown": False, "options": 1}
          and got.get("statements") == {"shown": True, "options": 3} and got.get("project") == {"shown": True, "options": 2}
          and got.get("sift") == {"shown": True, "options": 2} and got.get("trace") == {"shown": True, "options": 2},
          run.stdout.strip()[:300] or run.stderr.strip()[:300])

    # ── a filter heading only over rows, below 700px
    script = scratch / "search-heads-193.js"
    script.write_text(r"""
// the filters' box at 360: four rows of 26px and three gaps of 2, from 200 down, so its foot is at 310
const BOX_TOP = 200, ROW = 28;
const item = (head, row, word) => ({ head, row, word, classes: new Set(head ? ['search-group'] : ['search-tick']),
  get classList() { const c = this.classes; return { contains: (k) => c.has(k), toggle: (k, on) => (on ? c.add(k) : c.delete(k)) }; },
  getBoundingClientRect() { const top = BOX_TOP + this.row * ROW; return { top, bottom: top + 26 }; } });
let ITEMS = [];
const box = { scrollHeight: 400, clientHeight: 110, style: { maxHeight: '' },
  classList: { toggle() {} },
  getBoundingClientRect: () => ({ top: BOX_TOP }),
  querySelectorAll: (sel) => (sel === '.search-group' ? ITEMS.filter((i) => i.head) : []) };
const linked = () => ITEMS.forEach((it, n) => { it.nextElementSibling = ITEMS[n + 1] || null; });
const more = { hidden: true, textContent: '', setAttribute() {} };
const side = { hidden: false };
const $ = (id) => ({ 'search-filters': box, 'search-more': more, 'search-side': side })[id];
let NARROW = true;
const window = { matchMedia: () => ({ matches: NARROW }) };
const getComputedStyle = () => ({ rowGap: '2px' });
const SEARCH = { all: false };
""" + whole("searchMore") + r"""
const hidden = () => ITEMS.filter((i) => i.head && i.classes.has('over-none')).map((i) => i.word);
const out = {};
// Distil's heading and its three kinds on the first rows, Project on the fourth, its one row behind More
ITEMS = [item(true, 0, 'Distil'), item(false, 1, 'Passage'), item(false, 2, 'Statement'), item(false, 2, 'Note'),
  item(true, 3, 'Project'), item(false, 4, 'Lighthouse keepers')]; linked();
searchMore(); out.narrow = hidden(); out.more = !more.hidden; out.cut = box.style.maxHeight;
SEARCH.all = true; searchMore(); out.all = hidden(); out.allCut = box.style.maxHeight;
SEARCH.all = false; NARROW = false; searchMore(); out.desk = hidden(); out.deskCut = box.style.maxHeight;
// a heading with its first row in the box keeps it, its other rows behind More
NARROW = true;
ITEMS = [item(true, 0, 'Sift'), item(false, 1, 'Record'), item(true, 2, 'Distil'), item(false, 3, 'Passage'), item(false, 4, 'Note')]; linked();
searchMore(); out.partly = hidden(); out.partlyCut = box.style.maxHeight;
console.log(JSON.stringify(out));
""", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    got = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
    check("193: in node, below 700px a filter heading whose rows are all behind More is hidden with them, Project at 360 "
          "among them, the box ending above it so its row takes no room, and shows again with every row open after More, at a desk width, and wherever its first row is in sight",
          got.get("narrow") == ["Project"] and got.get("more") is True and got.get("all") == [] and got.get("desk") == []
          and got.get("partly") == [] and got.get("cut") == "82px" and got.get("allCut") == ""
          and got.get("deskCut") == "" and got.get("partlyCut") == "", run.stdout.strip()[:300] or run.stderr.strip()[:300])
