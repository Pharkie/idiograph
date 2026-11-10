from __future__ import annotations

from . import support
from .support import check


def test_themes_panels():
    print("\n49. Themes, two panels, two scopes: the selection panel and the board panel, and New board "
          "without its bracket")
    js = support.text("apps/idiograph/static/themes.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0]

    # ── 109. the selection panel
    check("109, 114: a click, a lasso and a drag select and never open it, it follows the selection while open, and empty canvas leaves it open",
          "thPanelFollow();" in fn(js, "thPointerUp") and "thPanelFollow();" in fn(js, "thDragStart")
          and "thPanelFollow(true)" not in js and "thPanelFollow(false)" not in js
          and "if (!l.moved && !l.add) { thClearSel(); thPanelFollow(); }" in fn(js, "thPointerUp")
          and "thInspectorOpen" not in fn(js, "thPointerUp") + fn(js, "thDragStart") + fn(js, "thLassoMove")
          and "thSideOpen" not in fn(js, "thPointerUp") + fn(js, "thDragStart") + fn(js, "thLassoMove")
          and "if (!TH.panelOpen) return;" in fn(js, "thPanelFollow")
          and "thSideShut" not in fn(js, "thPointerUp") and "thSideShut" not in fn(js, "thPanelDrop")
          and fn(js, "thPanelDrop").strip().endswith("thPanelShow(null);"))

    # ── 109. the board panel
    door = fn(js, "thSideDoor")
    check("109, 115, 183: the sidebar button opens it on the tab it was left on, and a second press closes it",
          "if (TH.sideOpen) thSideShut();" in door and "else thSideOpen(TH.tab);" in door
          and "$('th-open-side').onclick = () => thSideDoor();" in js
          and "$('th-open-side').addEventListener('pointerdown', (e) => e.preventDefault());" in js
          and "b.setAttribute('aria-pressed', String(!!TH.sideOpen));" in fn(js, "thSideDraw"))
    check("109, 183: a switch keeps it open on the new board, and opening a case or leaving the screen closes it",
          "thSideShut" not in fn(js, "thLoad") and "if (TH.boardOpen) thBoardDraw();" in fn(js, "thRender")
          and "thSideShut(false);" in fn(js, "themesOpen") and "thSideShut(false);" in fn(js, "themesLeave"))
    keys = fn(js, "thKeyDown")
    check("109, 114, 183: Esc clears the selection and never closes the sidebar",
          "else if (TH.sel.cards.size || TH.sel.groups.size || TH.sel.stickies.size) { thClearSel(); thPanelFollow(); }" in keys
          and "thSideShut" not in keys and "TH.panelOpen" not in keys and "TH.sideOpen" not in keys)
