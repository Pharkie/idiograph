from __future__ import annotations

import json
import re
import shutil

from . import support
from .support import check, skip


def test_sidebar(scratch):
    print("\n82. One sidebar at the right of the canvas with its tabs, the bug before the cog, the shortcuts "
          "in the zoom bar (183)")
    import subprocess

    page = support.page_text()
    js = support.text("apps/idiograph/static/themes.js")
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    manual = support.source("docs/manual.md").read_text(encoding="utf-8")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    flat = lambda text: " ".join(text.split())
    screen = page.split('<section id="themes"', 1)[1].split("</section>", 1)[0]
    th_bar = screen.split('<div class="rail ds-rail">', 1)[1].split('<div class="band" id="th-band"', 1)[0]
    work_bar = page.split('<section id="work"', 1)[1].split('<div class="rail ds-rail">', 1)[1].split('<div class="progress-strip"', 1)[0]

    # ── C. what opens it, and what never does
    up = fn(js, "thPointerUp")
    check("183: a click selects and never opens or switches the sidebar, nor a lasso or a drag, so another tab stays showing",
          "thSideOpen" not in up + fn(js, "thDragStart") + fn(js, "thLassoMove") + fn(js, "thPointerDown")
          and "thInspectorOpen" not in up + fn(js, "thDragStart") + fn(js, "thLassoMove")
          and "if (!TH.panelOpen) return;" in fn(js, "thPanelFollow"))
    check("183: i opens the sidebar on the Inspector and closes it while the Inspector shows, and the shortcuts card says so",
          "else if (e.key === 'i' || e.key === 'I') { e.preventDefault(); thInspectorKey(); }" in fn(js, "thKeyDown")
          and "if (TH.panelOpen) thSideShut();" in fn(js, "thInspectorKey") and "else thInspectorOpen();" in fn(js, "thInspectorKey")
          and '<tr><td class="mono">I</td><td>The Inspector, or close the sidebar</td></tr>' in page)
    check("183, 156, 297, 298: a double-click on a label opens its title for editing, on a statement card its statement "
          "for editing since 30 October, on GETs too, and on another card of GETs the Inspector",
          "else if (item.kind === 'group') thTitleOpen(item.id);" in up and "else thCardEditOpen(item.id);" in up
          and "thToPassage" not in up
          and "if (TH.mode === 'gets' && !thIsStatement(TH.v, key)) { gtCardOpen(key); return; }" in fn(js, "thCardEditOpen")
          and "thInspectorOpen({ kind: 'card', id: key });" in fn(js, "gtCardOpen"))
    check("183: every path that opened a panel on a tab opens the sidebar on that tab, and nothing of the two panels is left",
          "thInspectorOpen(item);" in fn(js, "thNamesAsk") and "thInspectorOpen({ kind: 'group', id });" in fn(js, "thNoteOpen")
          and "if (noted) thInspectorOpen({ kind: 'group', id: noted });" in fn(js, "thUndo")
          and "if (tab) thSideOpen(tab.dataset.tab);" in js
          and not re.search(r"thBoard(Open|Shut|Door|Restore|Keep|Stored)|thInspector(Shut|Door|Restore|Keep|Stored)|thDoorsDraw|thFront", js))

    # ── E. the bars
    check("183, 199, updated 16 October (160): the bug just before the cog on every screen, once in each bar, its "
          "handlers as they were, the PETs and GETs bar's naming whichever of the two it is",
          work_bar.count('id="btn-feedback"') == 1 and th_bar.count('id="th-feedback"') == 1
          and "$('th-feedback').onclick = () => openFeedback(TH.mode === 'gets' ? 'gets' : 'pets');" in js
          and "$('btn-feedback').onclick = () => openFeedback('statements');" in app)

    # ── F. the steps, and the figures measured again
    pets = manual.split("\n## PETs\n", 1)[1].split("\n## ", 1)[0]
    gets = manual.split("\n## GETs\n", 1)[1].split("\n## ", 1)[0]

    # ── G. the words
    was = re.sub(r"Until 5 October 2026 the (bar also carried|Inspector and a Board panel)[^.]*\.", "", flat(pets + gets))
    was = was.replace("the sidebar button in the place of the Inspector's, Board's and the shortcuts", "")

    # ── H. the sidebar's model, in node
    node = shutil.which("node")
    if not node:
        return skip("183: the sidebar's model in node", "no node on this machine")
    script = scratch / "sidebar.js"
    script.write_text(support.i18n_js() + js + r"""
const store = {};
globalThis.localStorage = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); } };
const els = {};
const el = () => {
  const e = { hidden: false, title: '', scrollTop: 0, attrs: {}, paused: false, cls: new Set() };
  e.classList = { toggle: (c, v) => (v ? e.cls.add(c) : e.cls.delete(c)) };
  e.setAttribute = (k, v) => { e.attrs[k] = String(v); };
  e.pause = () => { e.paused = true; };
  return e;
};
globalThis.$ = (id) => (els[id] = els[id] || el());
globalThis.document = { querySelectorAll: () => [] };
thPanelShow = (item) => { TH.panel = item || null; };
thBoardDraw = () => {};
thNoteDone = () => {};
const card = (x, y) => ({ x, y, text: 't' });
TH.v = { cards: { 'S:1:0': card(0, 0), 'S:2:0': card(300, 0) }, groups: [], discarded: [], picks: {} };
const g = thMakeGroup(TH.v, ['S:2:0'], 'Mornings');
TH.live = true; TH.mode = 'pets'; TH.ai = { on: true };
const state = () => ({ open: !!TH.sideOpen, tab: TH.tab, inspector: !!TH.panelOpen, board: !!TH.boardOpen,
  side: !$('th-side').hidden, panel: !$('th-panel').hidden, bpanel: !$('th-bpanel').hidden,
  title: $('th-open-side').title, pressed: $('th-open-side').attrs['aria-pressed'] });
const out = {};
thSideRestore(); out.fresh = state();
thSideDoor(); out.door = state(); out.doorShows = TH.panel;
TH.sel.cards.add('S:1:0'); TH.lastPick = { kind: 'card', id: 'S:1:0' }; thPanelFollow(); out.follow = TH.panel;
thSideOpen('history'); out.history = state(); out.paused = $('th-player').paused;
TH.sel.cards.clear(); TH.sel.groups.add(g); TH.lastPick = { kind: 'group', id: g }; thPanelFollow(); out.clicked = state();
thInspectorKey(); out.i = state(); out.iShows = TH.panel;
thInspectorKey(); out.iAgain = state();
thSideDoor(); out.reopen = state();
thSideOpen('table'); out.petsTable = state().tab;
thSideOpen('guidance'); thSideDoor(); out.kept = JSON.parse(store[thSideKey('pets')]);
TH.mode = 'gets';
thSideRestore(); out.getsFresh = state();
thSideOpen('table'); out.getsTable = state();
thSideOpen('guidance'); out.getsGuidance = state().tab;
thSideOpen('history'); thSideShut(false); out.leave = [state().open, JSON.parse(store[thSideKey('gets')])];
TH.mode = 'pets'; out.backOnPets = thSideStored();
TH.mode = 'gets'; out.backOnGets = thSideStored();
TH.mode = 'pets';
out.menuCard = thMenuItems(TH.v, { kind: 'card', id: 'S:1:0' }, true).map((x) => x.act);
out.menuLabel = thMenuItems(TH.v, { kind: 'group', id: g }, true).map((x) => x.act);
TH.v.readonly = true;
out.menuLocked = [thMenuItems(TH.v, { kind: 'card', id: 'S:1:0' }, true).map((x) => x.act),
  thMenuItems(TH.v, { kind: 'group', id: g }, true).map((x) => x.act)];
TH.v.readonly = false;
TH.live = false; thSideOpen('history'); thSideDoor(); thInspectorKey(); out.dead = state();
console.log(JSON.stringify(out));
""", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("183: the sidebar's model runs in node", False, run.stderr.strip()[:300])
    out = json.loads(run.stdout)
    closed = {"open": False, "inspector": False, "board": False, "side": False, "panel": False, "bpanel": False,
              "title": "Show Inspector (I)", "pressed": "false"}
    shows = lambda tab, board: {"open": True, "tab": tab, "inspector": not board, "board": board, "side": True,
                                "panel": not board, "bpanel": board, "title": "Hide Inspector (I)", "pressed": "true"}
    check("183: in node, closed at first on the Inspector, its button opens it there and says Hide Inspector, pressed in, "
          "where it said Hide the sidebar until 16 October",
          out["fresh"] == dict(closed, tab="inspector") and out["door"] == shows("inspector", False)
          and out["doorShows"] is None, str(out["fresh"]) + str(out["door"]))
    check("183: in node, the Inspector follows the selection while it shows, and another tab shows one at a time, its player paused",
          out["follow"] == {"kind": "card", "id": "S:1:0"} and out["history"] == shows("history", True) and out["paused"] is True,
          str(out["history"]))
    check("183: in node, a click with History showing leaves History showing",
          out["clicked"] == shows("history", True), str(out["clicked"]))
    check("183: in node, i opens the sidebar on the Inspector on the selection, and i again closes it",
          out["i"] == shows("inspector", False) and out["iShows"] == {"kind": "group", "id": "g1"}
          and out["iAgain"] == dict(closed, tab="inspector") and out["reopen"] == shows("inspector", False),
          str(out["i"]) + str(out["iAgain"]))
    check("183, updated 19 October (199): in node, Table is a tab on neither screen, and the tab left showing is kept for each screen apart",
          out["petsTable"] == "inspector" and out["kept"] == {"open": False, "tab": "guidance"}
          and out["getsFresh"] == dict(closed, tab="inspector") and out["getsTable"] == shows("inspector", False)
          and out["getsGuidance"] == "guidance" and out["leave"] == [False, {"open": True, "tab": "history"}]
          and out["backOnPets"] == {"open": False, "tab": "guidance"} and out["backOnGets"] == {"open": True, "tab": "history"},
          str({k: out[k] for k in ("petsTable", "kept", "leave", "backOnPets", "backOnGets")}))
    check("183, 156, 208: in node, Inspect comes first in a card's and a label's menu, Go to the passage after it on a card, "
          "New group inside after it on a label, and on a revision on view the card keeps the two and the label Inspect and the copy",
          out["menuCard"] == ["inspect", "passage", "groupsel", "discard"]
          and out["menuLabel"] == ["inspect", "inside", "arrange", "rename", "desc", "note", "copyto", "delete"]
          and out["menuLocked"] == [["inspect", "passage"], ["inspect", "copyto"]], str(out["menuCard"]) + str(out["menuLabel"]))
    check("183: in node, with the screen gone nothing opens it",
          out["dead"]["open"] is False, str(out["dead"]))
