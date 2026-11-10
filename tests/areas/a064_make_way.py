from __future__ import annotations

import json
import shutil

from . import support
from .support import MAKE_WAY_CHECK, check, skip


def test_make_way(scratch):
    print("\n64. Make way: what is inside the PET or sub-PET under the pointer makes room live for whatever is dragged, "
          "nothing else moving since design A (31 October), and the drop lands where it is let go (172)")
    import subprocess

    js = support.text("apps/idiograph/static/themes.js")
    fn = lambda name: js.split(f"function {name}(", 1)[1].split("\n}", 1)[0]

    # ── A. the page: the preview each move, the slides each frame, the drop, Esc and the save
    move, alt, end, start = fn("thDragMove"), fn("thDragAlt"), fn("thDragEnd"), fn("thDragStart")
    check("172: every move works out where the drop lands, then the neighbours make way, then the canvas is drawn",
          move.index("const hit = thTargetAt(e.clientX, e.clientY);") < move.index("thWay(d, hit);") < move.index("thPlace(d);")
          and alt.index("const hit = thTargetAt(") < alt.index("thWay(d, hit);") < alt.index("thPlace(d);")
          and "d.home = thWayHome(TH.v, d.moving, d.nest, hit, d.alt);" in fn("thWay")
          and "thPreview(TH.v, thSize, d, d.home);" in fn("thWay"))
    # since 18 October a drop is told by the title strip under the pointer, and by the body (area 188, area 312)
    check("172: a drop is told by the title strip or the body under the pointer, never by a card of a theme",
          "el.closest('.th-label')" in fn("thTargetAt") and "thFrameAt(" not in fn("thTargetAt")
          and "el.closest('.th-card')" not in fn("thTargetAt"))
    check("172: the drop lands where it is let go, the neighbours where they made way, and one step of undo for it all",
          end.index("thPreview(v, thSize, d, thWayHome(v, d.moving, d.nest, hit, d.alt));") < end.index("TH.drag = null;")
          and "thDone(d.before, what, { settle: d.moving, stay: true, was: d.was, from: shown, lifted, lean: d.lean });" in end
          and end.count("thDone(") == 3 and "thStep(" not in end
          and "thSettle(TH.v, thSize, opts.settle, was, opts.labels, TH_PASSES, !!opts.stay)" in fn("thDone")
          and "if (stay) yields.splice(0);" in fn("thSettle") and "before: lifted || thSnap(v, TH.removed)" in start)
    cancel = fn("thDragCancel")
    keys = fn("thKeyDown")
    check("172: Esc during a drag puts everything back, leaves no step of undo, and does nothing else",
          "if (e.key === 'Escape' && TH.drag) { e.preventDefault(); e.stopPropagation(); thDragCancel(); return; }" in keys
          and keys.index("thDragCancel();") < keys.index("if (TH.menu)") and keys.index("thDragCancel();") < keys.index("if (TH.vmenu)")
          and "thPreview(v, thSize, Object.assign({}, d, { dx: 0, dy: 0 }), null);" in cancel
          and "TH.press = null;" in cancel and "TH.drag = null;" in cancel and "cancelAnimationFrame(d.raf);" in cancel
          and "thDone(" not in cancel and "thStep(" not in cancel and "thEase(shown, d.moving, d.lean);" in cancel)
    check("172: a drag over the bin makes no way, and nothing the drag does writes the workbook or the file before the drop",
          "if (hit && (hit.discard || hit.stack)) return null;" in fn("thWayHome")
          and "if (TH.drag) { TH.dirty = true; return; }" in fn("thSaveOnce")
          and fn("thSaveOnce").index("if (TH.drag)") < fn("thSaveOnce").index("await api(")
          and "if (TH.dirty) thSoon();" in end and "if (TH.dirty) thSoon();" in cancel
          and not any("api(" in fn(n) for n in ("thWay", "thWayShow", "thWayTick", "thPreview", "thMakeWay", "thWayHome", "thDragCancel")))

    # ── B. the model in node
    node = shutil.which("node")
    if not node:
        skip("172: the make way model in node", "node is not installed")
    else:
        script = scratch / "make-way-model.js"
        script.write_text(support.i18n_js() + """
globalThis.$ = () => null;
globalThis.esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
globalThis.escAttr = (s) => esc(s).replace(/"/g, '&quot;');
globalThis.say = () => {};
""" + js + MAKE_WAY_CHECK, encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("172: the make way model runs in node", False, run.stderr.strip()[:400])
        else:
            o = json.loads(run.stdout)
            m = o["middle"]
            body = lambda g: {"group": g, "frame": True, "body": True}
            # design A (Adam, 31 October, after the drag audit): no PET or sub-PET moves out of the way, only the
            # statements and notes inside the one under the pointer make room, and every title stays where it stood
            check("172: in node, a card in no PET dragged into the middle of a PET of nine stands where it is, the nine "
                  "making room as cards while the PET and its title hold still (design A, 31 October)",
                  m["hit"] == body("g1") and m["home"] and m["cards"] and m["label"] and m["landed"] == [210, 90]
                  and m["near"] == 0, str(m))
            check("172: in node, a PET far from the drag and a card on the canvas stay where they are",
                  m["far"] is True, str(m))
            check("172: in node, the preview comes from the start layout, so each of the nine goes back when the drag moves "
                  "away, and on the open canvas nothing moves",
                  o["back"] == {"home": "", "all": True, "moved": [], "same": True, "again": True}, str(o["back"]))
            check("172: in node, the drop in the PET's body takes the card in where let go, and the nine stay where they made room",
                  o["drop"] == {"joined": ["f:1:0"], "landed": [210, 90], "stayed": True, "clashes": 0, "member": True}, str(o["drop"]))
            check("172: in node, the board as the drag began puts back what was dragged and everything that made room",
                  o["undo"] == {"cards": True, "loose": True}, str(o["undo"]))
            check("172: in node, between two cards of a PET's row and under one, the cards make room, the card stays put and "
                  "the PET's title holds still",
                  o["row"]["between"] == [True, 0, [105, 0], False, True] and o["row"]["under"] == [True, 0, [210, 50], False, True],
                  str(o["row"]))
            check("172: in node, a pushed neighbour pushes a third for eight passes at most, and then it stops",
                  o["passes"]["eight"] == [110, 320, 530, 740, 950, 1160, 1370, 1580, 1680, 1890]
                  and o["passes"]["nine"][8] == 1790 and o["passes"]["nine"][9] == 1890, str(o["passes"]))
            check("172: in node, Esc's preview puts everything back on its start, what was dragged too",
                  o["esc"] == {"shifted": True, "back": True}, str(o["esc"]))
            check("172: in node, a selection dragged as one keeps its arrangement and each member's box makes room",
                  o["selection"]["home"] and o["selection"]["landed"] == [[100, 20], [310, 20]]
                  and o["selection"]["near"] == 0 and o["selection"]["moved"] == ["k:1:0", "k:2:0", "k:3:0"], str(o["selection"]))
            check("172: in node, a PET dragged across the canvas moves nothing while it is dragged, and its drop sends a card and "
                  "another PET clear, that PET as one block",
                  o["pet"] == {"hit": None, "home": "", "moved": [], "still": True, "landed": [[100, 160], [100, 250]],
                               "clear": True, "block": True, "clashes": 0}, str(o["pet"]))
            check("172: in node, a sub-theme dragged inside its PET has the PET's own cards make room, a sibling sub-theme and "
                  "the canvas still, no Merge",
                  o["sub"]["nest"] and o["sub"]["hit"] == body("g3") and o["sub"]["home"] and o["sub"]["merge"] is False
                  and o["sub"]["near"] == 0 and o["sub"]["landed"] == [[100, 50], [310, 50]] and o["sub"]["canvas"]
                  and o["sub"]["sibling"] and o["sub"]["moved"], str(o["sub"]))
            g = o["merge"]
            check("172: in node, a PET beside another and inside its body has it hold still, since a PET goes into no body",
                  g["beside"] == "" and g["besideHeld"] and g["body"] == {"hit": None, "home": "", "held": True}, str(g))
            check("172: in node, over that PET's title strip it merges: the title holds still under the pointer, nothing "
                  "moves, and the drop nests with nothing overlapping",
                  g["strip"] == {"group": "g2", "onLabel": True} and g["home"] and g["title"] and g["into"] and g["still"]
                  and g["nested"] and g["clashes"] == 0, str(g))
            check("172: in node, with Alt nothing takes the card, its PET holds still, and the drop takes it out where let go",
                  o["alt"] == {"hit": None, "home": "", "moved": [], "still": True, "left": ["p:2:0"], "landed": [210, 40],
                               "clashes": 0, "out": True}, str(o["alt"]))
            check("172: in node, a card dragged into another PET's body shows leaving its own, that PET's cards make room while "
                  "the PET holds still, and the drop takes it in",
                  o["join"] == {"home": True, "hit": body("g1"), "moved": ["q:1:0", "q:2:0"], "out": True, "label": True,
                                "near": 0, "shrunk": True, "canvas": True, "joined": ["p:2:0"], "parent": True, "clashes": 0},
                  str(o["join"]))
            check("172: in node, a sticky note dragged into a PET's body has its cards make room by its own box, and goes in",
                  o["note"] == {"home": True, "moved": ["k:1:0", "k:2:0"], "landed": [180, 10], "near": 0, "inside": True},
                  str(o["note"]))
            check("172: in node, over the bin nothing makes way, and a revision on view makes none",
                  o["bin"] == [None, 0, [0, 0]] and o["locked"] == 0, str(o["bin"]))
            check("172: in node, a slide runs 160 ms eased out from where it shows, and with reduced motion is there at once",
                  o["slide"] == [0, True, 100, True, 100, True], str(o["slide"]))
