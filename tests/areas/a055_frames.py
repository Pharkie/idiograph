from __future__ import annotations

import json
import shutil

from . import support
from .support import check, demo_copy, skip


def test_frames(scratch):
    print("\n55. Frames keep apart as cards do, inside a PET too, and the Alt tip names what it removes from")
    import subprocess
    import themes as themes_mod
    import themes_ai

    js = support.text("apps/idiograph/static/themes.js")
    th_src = support.source("apps/idiograph/themes.py").read_text(encoding="utf-8")

    # ── C. the server's estimates hold the page's, within a margin
    # the page's own sizes, measured on a Mac in the type it draws: a label's width and height by its
    # title, whether it is a label over labels, and its marks, and a card's height. Measured again on 17
    # October, later, with no count, which left the label for its frame's badge on 3 October, where the
    # table had kept the count's width and the line it took. Area 171 reads this table.
    measured = [("Untitled", False, 0, 138, 30), ("Nights alone", False, 0, 172, 30), ("Nights alone", False, 2, 212, 30),
                ("Walks", True, 0, 130, 36), ("Mornings with the dog", False, 1, 271, 30),
                ("Mornings that belong to the dog and to nobody else in the house", False, 0, 340, 53),
                ("A third theme about the garden", True, 0, 340, 63), ("iiiiiiiiiiiiiiiiiiiiiiii", False, 0, 198, 30),
                ("Understanding responsibilities, companionship and neighbourliness", False, 0, 340, 75)]
    over = [(themes_mod.label_size(t, u, m), (w, h)) for t, u, m, w, h in measured]
    check("a label's estimate is never under the page's, and its width is within a margin of it",
          all(ew >= w and eh >= h and ew - w <= themes_mod.MARGIN for (ew, eh), (w, h) in over), str(over))
    check("a label's height is the page's when it breaks into the same lines, a pixel over at most",
          sum(1 for (ew, eh), (w, h) in over if 0 <= eh - h <= 1) >= 7, str(over))
    cards = [("Five years of the unsaid", 59), ("Caught out by a tenderness never claimed before", 99),
             ("Twelve minutes standing for something much larger", 79), ("Anger taken off at the bottom of the stairs", 79)]
    heights = [(themes_mod.card_height(t), h) for t, h in cards]
    check("a card's estimate is the page's height and a pixel over",
          all(e - h == 1 for e, h in heights), str(heights))
    check("a label carries its marks, a note's and the picks', in the server's layout too",
          themes_mod.LABEL_CHROME == 73 and themes_mod.LABEL_MARK == 20
          and themes_mod.label_size("Short", False, 2)[0] == themes_mod.label_size("Short")[0] + 40)
    odd =themes_mod.pack_round([(201, 63), (233, 91), (175, 37), (311, 129), (199, 55)], themes_mod.MARGIN)
    sizes = [(201, 63), (233, 91), (175, 37), (311, 129), (199, 55)]
    boxes = [(x, y, w, h) for (x, y), (w, h) in zip(odd, sizes)]
    near = [(i, j) for i in range(5) for j in range(i + 1, 5) if themes_mod.clash(boxes[i], boxes[j], themes_mod.MARGIN)]
    check("every place in a round pack rounds the same way, so a pack of odd sizes keeps the whole margin between neighbours",
          not near and "math.floor(x - cx + 0.5), math.floor(y - cy + 0.5)" in th_src, str(near))

    # ── D. the server's layouts need no shift when the page draws them
    root = scratch / "frames-root"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    read = themes_mod.read_cards(work)
    k = [c["key"] for c in read["cards"]]

    def page_board(version):
        """The board as the page holds it, and the sizes the server gives each card and label."""
        drawn = themes_mod.layout_boxes(version)
        gone = set(version.get("discarded") or [])
        board = {"cards": {key: {"x": c["x"], "y": c["y"], "text": c["text"]} for key, c in version["cards"].items()},
                 "groups": [{"id": g["id"], "label": g["label"], "members": list(g["members"]), "x": g["x"], "y": g["y"]}
                            for g in version["groups"]],
                 "discarded": [key for key in version.get("discarded") or []], "picks": version.get("picks") or {}}
        size = {key: list(b[2:4]) for key, b in drawn["cards"].items() if key not in gone}
        size.update({gid: list(b[2:4]) for gid, b in drawn["labels"].items()})
        return board, size

    # a structure laid out whole, as an agent's board make lays one out (the AI's grouping went on 11 November 2026)
    proposal = {"groups": [
        {"label": "Mornings that belong to the dog and to nobody else in the house", "members": k[0:4], "groups": []},
        {"label": "A house that holds two", "members": [k[4]],
         "groups": [{"label": "Walks taken alone", "members": k[5:8]}, {"label": "Nights", "members": k[8:10]}]},
        {"label": "Short", "members": k[10:12], "groups": []}, {"label": "A fourth with one", "members": [k[12]], "groups": []}]}
    source = themes_mod.blank_version(read["cards"])
    merged = themes_mod.merge(read["cards"], source)
    laid = themes_ai.lay_out(proposal["groups"], merged["cards"], merged["discarded"])
    ai_board, ai_size = page_board(laid)
    # a copy: a theme with a sub-theme, a note and picks onto a board with a theme near its middle
    src = themes_mod.blank_version(read["cards"])
    src["groups"] = [{"id": "g1", "label": "Mornings", "note": "Why it holds", "members": [k[0], k[1], "g2"], "x": 0, "y": 0},
                     {"id": "g2", "label": "Inside it", "members": [k[2], k[3]], "x": 0, "y": 0}]
    src["picks"] = {"g1": [f"{k[0].rsplit(':', 1)[0]}:0"]}
    tgt = themes_mod.blank_version(read["cards"])
    tgt["id"] = "v2"
    tgt["groups"] = [{"id": "g1", "label": "Already there", "members": k[6:10], "x": 0, "y": 0}]
    for i, key in enumerate(k[6:10]):
        tgt["cards"][key].update(x=-1400 + (i % 2) * 210, y=(i // 2) * 130)
    copied, _ = themes_mod.copy_into(src, "g1", tgt)
    copy_board, copy_size = page_board(copied)
    # a new line read since the board was made, on a board whose theme sits over the middle
    held = themes_mod.blank_version([c for c in read["cards"] if c["key"] != k[-1]])
    held["groups"] = [{"id": "g1", "label": "Over the middle", "members": k[:12], "x": 0, "y": 0}]
    held["cards"] = {key: dict(c) for key, c in held["cards"].items()}
    for i, key in enumerate(k[:12]):
        held["cards"][key].update(x=-320 + (i % 3) * 210, y=-200 + (i // 3) * 110)
    fresh = themes_mod.merge(read["cards"], held)
    new_card = next(c for c in fresh["cards"] if c.get("new"))
    new_box = (new_card["x"], new_card["y"], themes_mod.CARD_W, themes_mod.card_height(new_card["text"]))
    held_drawn = themes_mod.layout_boxes(dict(held, cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]}
                                                           for c in fresh["cards"]}))
    check("125: a new line takes the nearest spot the margin clear of every frame, as of every card and label",
          not any(themes_mod.clash(new_box, f, themes_mod.MARGIN - 1) for f in held_drawn["frames"].values())
          and not any(themes_mod.clash(new_box, b, themes_mod.MARGIN - 1) for key, b in held_drawn["cards"].items() if key != new_card["key"]),
          str(new_box))

    node = shutil.which("node")
    if not node:
        return skip("the frames model in node", "no node on this machine")
    script = scratch / "frames.js"
    script.write_text(support.i18n_js() + js + "\nconst SERVER = " + json.dumps({"ai": [ai_board, ai_size], "copy": [copy_board, copy_size]})
                      + ";\n" + r"""
const size = (item) => (item.startsWith('g') ? { w: 120, h: 30 } : { w: 200, h: 80 });
const card = (x, y) => ({ x, y, text: 't' });
const keep = (x) => JSON.parse(JSON.stringify(x));
const gap = (a, b) => Math.max(b.x - (a.x + a.w), a.x - (b.x + b.w), b.y - (a.y + a.h), a.y - (b.y + b.h));
const at = (v, key) => [v.cards[key].x, v.cards[key].y];
const out = {};
// 125: a theme dropped over another's frame, the pointer outside it, settles clear by the margin, and
// the drag and the shift are one step: undo puts it where it was before the drag
{
  const v = { cards: { 'a:1:0': card(0, 0), 'a:2:0': card(210, 0), 'b:1:0': card(600, 0), 'b:2:0': card(810, 0) }, groups: [], discarded: [], picks: {} };
  const A = thMakeGroup(v, ['a:1:0', 'a:2:0'], 'A');
  const B = thMakeGroup(v, ['b:1:0', 'b:2:0'], 'B');
  const was = thLabelBoxes(thLayout(v, size, null));
  const before = thSnap(v, []);
  const moving = thMoving(v, new Set(), new Set([A]));
  thShift(v, [...moving], 170, 20);
  const hit = thLayout(v, size, moving);
  const inside = thFrameAt(v, hit, { x: thGroup(v, A).x + 10, y: thGroup(v, A).y + 10 }, moving);
  const drop = thDrop(v, moving, null, inside, false);
  const overlapped = thMeets(thLayout(v, size, null)[A].frame, thLayout(v, size, null)[B].frame, 0);
  const moved = thSettle(v, size, moving, was, []);
  const lay = thLayout(v, size, null);
  out.outside = { inside, drop, overlapped, moved, gap: gap(lay[A].frame, lay[B].frame), b: at(v, 'b:1:0'), clashes: thClashes(v, size) };
  thPut(v, before);
  out.undone = [at(v, 'a:1:0'), at(v, 'a:2:0')];
}
// 125: the same drop with the pointer inside the other frame joins it as a sub-theme, and 126: the
// theme's own cards keep clear of it
{
  const v = { cards: { 'a:1:0': card(0, 0), 'a:2:0': card(210, 0), 'b:1:0': card(600, 0), 'b:2:0': card(810, 0) }, groups: [], discarded: [], picks: {} };
  const A = thMakeGroup(v, ['a:1:0', 'a:2:0'], 'A');
  const B = thMakeGroup(v, ['b:1:0', 'b:2:0'], 'B');
  const was = thLabelBoxes(thLayout(v, size, null));
  const moving = thMoving(v, new Set(), new Set([A]));
  thShift(v, [...moving], 500, 30);
  const hit = thLayout(v, size, moving);
  const inside = thFrameAt(v, hit, { x: 620, y: 50 }, moving);
  const drop = thDrop(v, moving, null, inside, false);
  thSettle(v, size, moving, was, []);
  out.inside = { inside, drop, members: keep(thGroup(v, B).members), a: at(v, 'a:1:0'), clashes: thClashes(v, size) };
}
// 125: a card dropped in a theme at its edge: the frame grows, stays, and sends a free card and a
// neighbouring theme clear
{
  const v = { cards: { 'a:1:0': card(0, 0), 'x:1:0': card(0, 140), 'b:1:0': card(250, -200), 'b:2:0': card(250, -60), 'n:1:0': card(-300, 300) },
    groups: [], discarded: [], picks: {} };
  const A = thMakeGroup(v, ['a:1:0'], 'A');
  const B = thMakeGroup(v, ['b:1:0', 'b:2:0'], 'B');
  const clean = thClashes(v, size).length === 0;
  const was = thLabelBoxes(thLayout(v, size, null));
  const before = thSnap(v, []);
  const moving = thMoving(v, new Set(['n:1:0']), new Set());
  v.cards['n:1:0'].x = 60; v.cards['n:1:0'].y = 30;
  const drop = thDrop(v, moving, null, A, false);
  thSettle(v, size, moving, was, []);
  out.grew = { clean, drop, a: at(v, 'a:1:0'), n: at(v, 'n:1:0'), x: at(v, 'x:1:0'), b: [at(v, 'b:1:0'), at(v, 'b:2:0')], clashes: thClashes(v, size) };
  thPut(v, before);
  out.grewUndone = [at(v, 'x:1:0'), at(v, 'b:1:0'), at(v, 'n:1:0')];
}
// 125: a free card dropped over a frame, the pointer outside it, shifts clear, and the frame stays
{
  const v = { cards: { 'a:1:0': card(0, 0), 'a:2:0': card(210, 0), 'f:1:0': card(500, 0) }, groups: [], discarded: [], picks: {} };
  const A = thMakeGroup(v, ['a:1:0', 'a:2:0'], 'A');
  const was = thLabelBoxes(thLayout(v, size, null));
  const moving = thMoving(v, new Set(['f:1:0']), new Set());
  v.cards['f:1:0'].x = 415;
  thDrop(v, moving, null, null, false);
  thSettle(v, size, moving, was, []);
  out.free = { f: at(v, 'f:1:0'), a: at(v, 'a:2:0'), parent: thParents(v)['f:1:0'] === undefined, clashes: thClashes(v, size) };
}
// 125: a label renamed longer grows its frame into a neighbour, which shifts, and the theme stays
{
  const v = { cards: { 'a:1:0': card(0, 0), 'b:1:0': card(250, 0) }, groups: [], discarded: [], picks: {} };
  const A = thMakeGroup(v, ['a:1:0'], 'Short');
  const B = thMakeGroup(v, ['b:1:0'], 'B');
  const was = thLabelBoxes(thLayout(v, size, null));
  const long = (item) => (item === A ? { w: 300, h: 30 } : size(item));
  thSettle(v, long, [], was, [A]);
  const lay = thLayout(v, long, null);
  out.rename = { a: at(v, 'a:1:0'), b: at(v, 'b:1:0'), gap: gap(lay[A].frame, lay[B].frame) };
}
// 125: an arranged theme stays where its label is, and a neighbour its new frame reaches shifts
{
  const v = { cards: { 'c:1:0': card(0, 0), 'c:2:0': card(0, 300), 'c:3:0': card(0, 600), 'c:4:0': card(0, 900), 'f:1:0': card(250, 100) },
    groups: [], discarded: [], picks: {} };
  const T = thMakeGroup(v, ['c:1:0', 'c:2:0', 'c:3:0', 'c:4:0'], 'Tidy');
  const lay0 = thLayout(v, size, null);
  const was = thLabelBoxes(lay0);
  thArrange(v, T, size);
  thSettle(v, size, [], was, [T]);
  const lay = thLayout(v, size, null);
  out.arrange = { label: [lay[T].label.x - lay0[T].label.x, lay[T].label.y - lay0[T].label.y], f: at(v, 'f:1:0'),
    gap: gap(lay[T].frame, { x: v.cards['f:1:0'].x, y: v.cards['f:1:0'].y, w: 200, h: 80 }), clashes: thClashes(v, size) };
}
// 126: a sub-theme made among a theme's cards sends the theme's other cards clear, its own stay
{
  const v = { cards: {}, groups: [], discarded: [], picks: {} };
  const keys = [];
  for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) { const key = `d:${r * 3 + c}:0`; v.cards[key] = card(c * 210, r * 90); keys.push(key); }
  const T = thMakeGroup(v, keys, 'T');
  const was = thLabelBoxes(thLayout(v, size, null));
  const before = keep(v.cards);
  const S = thMakeGroup(v, ['d:4:0', 'd:5:0'], 'S');
  thSettle(v, size, [], was, [S]);
  const lay = thLayout(v, size, null);
  const others = keys.filter((key) => key !== 'd:4:0' && key !== 'd:5:0');
  out.sub = { parent: thParents(v)[S] === T, own: [at(v, 'd:4:0'), at(v, 'd:5:0')], before: [[before['d:4:0'].x, before['d:4:0'].y], [before['d:5:0'].x, before['d:5:0'].y]],
    clear: others.every((key) => !thMeets({ x: v.cards[key].x, y: v.cards[key].y, w: 200, h: 80 }, lay[S].frame, TH_MARGIN - 1)),
    moved: others.filter((key) => v.cards[key].x !== before[key].x || v.cards[key].y !== before[key].y).length, clashes: thClashes(v, size) };
}
// 126: a sub-theme dragged inside its theme stays where it is put, and sends a sibling sub-theme clear as a block
{
  const v = { cards: { 'e:1:0': card(0, 0), 'e:2:0': card(0, 90), 'e:3:0': card(400, 0), 'e:4:0': card(400, 90), 'e:5:0': card(0, 400) },
    groups: [], discarded: [], picks: {} };
  const T = thMakeGroup(v, ['e:1:0', 'e:2:0', 'e:3:0', 'e:4:0', 'e:5:0'], 'T');
  const S1 = thMakeGroup(v, ['e:1:0', 'e:2:0'], 'One');
  const S2 = thMakeGroup(v, ['e:3:0', 'e:4:0'], 'Two');
  const clean = thClashes(v, size).length === 0;
  const was = thLabelBoxes(thLayout(v, size, null));
  const moving = thMoving(v, new Set(), new Set([S1]));
  thShift(v, [...moving], 220, 0);
  const met = thMeets(thLayout(v, size, null)[S1].frame, thLayout(v, size, null)[S2].frame, 0);
  const drop = thDrop(v, moving, null, T, false);
  thSettle(v, size, moving, was, []);
  const lay = thLayout(v, size, null);
  out.sibling = { clean, met, drop, s1: at(v, 'e:1:0'), s2: at(v, 'e:3:0'), kept: v.cards['e:4:0'].y - v.cards['e:3:0'].y,
    gap: gap(lay[S1].frame, lay[S2].frame), members: keep(thGroup(v, T).members), clashes: thClashes(v, size) };
}
// 125: the pushes stop after the bound: a row of cards a margin apart, a frame grown into the first
{
  const v = { cards: { 'a:1:0': card(0, 0) }, groups: [], discarded: [], picks: {} };
  for (let i = 1; i <= 11; i++) v.cards[`c:${i}:0`] = card(224 + (i - 1) * 210, 0);
  const A = thMakeGroup(v, ['a:1:0'], 'A');
  const was = thLabelBoxes(thLayout(v, size, null));
  const wide = (item) => (item === A ? { w: 230, h: 30 } : size(item));
  const start = Array.from({ length: 11 }, (_, i) => v.cards[`c:${i + 1}:0`].x);
  thSettle(v, wide, [], was, [A]);
  const end = Array.from({ length: 11 }, (_, i) => v.cards[`c:${i + 1}:0`].x);
  out.bound = { passes: TH_PASSES, moved: end.map((x, i) => x !== start[i]), clashes: thClashes(v, wide) };
}
// 125: a card in no theme a push leaves inside a frame when the passes run out joins that theme
{
  const v = { cards: { 'a:1:0': card(0, 0), 'a:2:0': card(0, 300), 'x:1:0': card(224, 0), 'u:1:0': card(460, -30) }, groups: [], discarded: [], picks: {} };
  const A = thMakeGroup(v, ['a:1:0', 'a:2:0'], 'A');
  const U = thMakeGroup(v, ['u:1:0'], 'U');
  const clean = thClashes(v, size).length === 0;
  const was = thLabelBoxes(thLayout(v, size, null));
  const big = (item) => (item === A ? { w: 400, h: 200 } : size(item));
  const w = keep(v);
  thSettle(v, big, [], was, [A], 1);
  thSettle(w, big, [], was, [A]);
  out.joins = { clean, parent: thParents(v)['x:1:0'] || null, U, x: at(v, 'x:1:0'), passes: thParents(w)['x:1:0'] || null };
}
// a revision on view shifts nothing
{
  const v = { cards: { 'a:1:0': card(0, 0), 'a:2:0': card(100, 0) }, groups: [], discarded: [], picks: {}, readonly: true };
  out.locked = [thSettle(v, size, ['a:2:0'], {}, []), at(v, 'a:2:0')];
}
// the server's layouts, drawn by the page with the server's sizes: nothing to shift
for (const name of ['ai', 'copy']) {
  const [board, sizes] = SERVER[name];
  const bySize = (item) => ({ w: sizes[item][0], h: sizes[item][1] });
  out[name] = { clashes: thClashes(board, bySize), shifted: thSettle(board, bySize, Object.keys(board.cards).filter((key) => !board.discarded.includes(key)), thLabelBoxes(thLayout(board, bySize, null)), []) };
}
// 127: the tip's words, and what holds what is dragged
out.words = [thTipText(false, true), thTipText(false, false), thTipText(true, true), thTipText(false, true, 'sub-theme'),
  thTipText(true, false, 'sub-theme')];
{
  const v = { cards: { 'm:1:0': card(0, 0), 'm:2:0': card(0, 200), 'm:3:0': card(0, 400) }, groups: [], discarded: [], picks: {} };
  const P = thMakeGroup(v, ['m:1:0', 'm:2:0', 'm:3:0'], 'P');
  const S = thMakeGroup(v, ['m:2:0', 'm:3:0'], 'S');
  const unit = (cards, groups, picked) => thTipUnit(v, thMoving(v, new Set(cards), new Set(groups)), picked);
  out.unit = [unit(['m:1:0'], [], 'm:1:0'), unit(['m:3:0'], [], 'm:3:0'), unit([], [S], S), unit(['m:1:0', 'm:3:0'], [], 'm:3:0')];
}
console.log(JSON.stringify(out));
""", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("the frames model runs in node", False, run.stderr.strip()[:300])
    out = json.loads(run.stdout)
    o = out["outside"]
    check("125: a theme dropped overlapping a frame, the pointer outside it, shifts clear by at least the margin",
          o["inside"] is None and o["drop"] == {"joined": [], "left": [], "dest": None} and o["overlapped"] is True
          and o["moved"] is True and o["gap"] >= 10 and o["b"] == [600, 0] and o["clashes"] == [], str(o))
    check("125: the drag and the shift are one step: undo puts the theme back where it stood before the drag",
          out["undone"] == [[0, 0], [210, 0]], str(out["undone"]))
    i = out["inside"]
    check("125: dropped with the pointer inside the other frame it joins as a sub-theme, and that theme's cards keep clear",
          i["inside"] == "g2" and i["drop"] == {"joined": ["g1"], "left": [], "dest": "g2"}
          and i["members"] == ["b:1:0", "b:2:0", "g1"] and i["clashes"] == [], str(i))
    g = out["grew"]
    check("125: a frame grown by a joining card stays, and pushes a free card and a neighbouring theme clear",
          g["clean"] is True and g["drop"]["joined"] == ["n:1:0"] and g["a"] == [0, 0] and g["n"] == [60, 90]
          and g["x"] == [0, 192] and g["b"] == [[298, -200], [298, -60]] and g["clashes"] == [], str(g))
    check("125: undo puts back what the growth pushed, in the one step of the act",
          out["grewUndone"] == [[0, 140], [250, -200], [-300, 300]], str(out["grewUndone"]))
    f = out["free"]
    check("125: a free card dropped over a frame, the pointer outside it, shifts clear and stays free, the frame where it was",
          f["a"] == [210, 0] and f["parent"] is True and f["clashes"] == [] and f["f"][0] >= 210 + 200 + 14 + 10, str(f))
    r = out["rename"]
    check("125: a label renamed longer keeps its theme where it is and sends the neighbouring theme clear",
          r["a"] == [0, 0] and r["b"][0] > 250 and r["gap"] >= 10, str(r))
    a = out["arrange"]
    check("125: an arranged theme stays where its label is, and the free card its new frame reached shifts clear",
          a["label"] == [0, 0] and a["f"] != [250, 100] and a["gap"] >= 10 and a["clashes"] == [], str(a))
    s = out["sub"]
    check("126: a sub-theme made among a theme's cards sends the theme's other cards clear, its own staying put",
          s["parent"] is True and s["own"] == s["before"] and s["clear"] is True and s["moved"] >= 5 and s["clashes"] == [], str(s))
    sib = out["sibling"]
    check("126: a sub-theme dragged inside its theme stays where it is put, and a sibling shifts clear as a block",
          sib["clean"] is True and sib["met"] is True and sib["drop"] == {"joined": [], "left": [], "dest": "g1"}
          and sib["s1"] == [220, 0] and sib["s2"] != [400, 0] and sib["kept"] == 90 and sib["gap"] >= 10
          and sib["members"] == ["g2", "g3", "e:5:0"] and sib["clashes"] == [], str(sib))
    b = out["bound"]
    check("125: a push into a third pushes that one too, eight passes at most, and then it stops",
          b["passes"] == 8 and b["moved"] == [True] * 8 + [False] * 3 and len(b["clashes"]) == 1, str(b))
    j = out["joins"]
    check("125: a card in no theme a push leaves inside a frame, when the passes run out, joins that theme, and with passes left it does not",
          j["clean"] is True and j["parent"] == j["U"] and j["x"] == [424, 0] and j["passes"] is None, str(j))
    check("125: a revision on view shifts nothing", out["locked"] == [False, [100, 0]], str(out["locked"]))
    check("125: an AI proposal, drawn by the page, needs no shift: its frames and cards keep the law already",
          out["ai"] == {"clashes": [], "shifted": False}, str(out["ai"]))
    check("125: a copy, with its sub-theme, its note and its picks, needs no shift either",
          out["copy"] == {"clashes": [], "shifted": False}, str(out["copy"]))
    check("127: the tip says sub-theme when a sub-theme holds what is dragged, and PET for a card in a PET or a sub-theme itself",
          out["unit"] == ["PET", "sub-theme", "PET", "sub-theme"], str(out["unit"]))
