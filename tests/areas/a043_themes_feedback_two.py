from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import export as export_mod

from . import support
from .support import GRAVITY_QUESTION, check, css_block, demo_copy, skip
import idiograph_routes


def test_themes_feedback_two(scratch):
    print("\n43. Themes, the second feedback: the margin, the hand, Cmd, arrange, order, Settings, the note, "
          "the band, the frame, leaving, the menu, the card, the bar, motion")
    import csv
    import subprocess
    import server as server_mod
    import themes as themes_mod

    root = scratch / "themes-fb2-root"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    (root / "idiograph-project.json").write_text(json.dumps(
        {"name": "Scratch", "research_question": GRAVITY_QUESTION}), encoding="utf-8")
    read = themes_mod.read_cards(work)
    k = [c["key"] for c in read["cards"]]
    text = {c["key"]: c["text"] for c in read["cards"]}
    page = support.page_text()
    js = support.text("apps/idiograph/static/themes.js")
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    css = support.text("apps/idiograph/static/themes.css")
    style = support.text("family/static/style.css", "apps/idiograph/static/distil.css")
    manual = support.source("docs/manual.md").read_text(encoding="utf-8")
    section = manual.split("## PETs", 1)[1].split("\n## ", 1)[0]
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0]
    screen = page.split('<section id="themes"', 1)[1].split("</section>", 1)[0]

    # ── 80. one margin, small, used everywhere
    th_src = support.source("apps/idiograph/themes.py").read_text(encoding="utf-8")
    ai_src = support.source("apps/idiograph/themes_ai.py").read_text(encoding="utf-8")
    check("80: one margin, a twentieth of a card's width, the same number in the server and the page",
          themes_mod.MARGIN == themes_mod.CARD_W // 20 == 10 and "const TH_MARGIN = 10;" in js
          and "TH_SPACE" not in js and not re.search(r"\bGAP\b", th_src + ai_src))

    # ── 85. the draft and the CSV list a theme by where its statements sit
    check("85: the canvas reads top to bottom, then left to right along a row of tops within half a card",
          themes_mod.read_order({"a": (300, 4), "b": (0, 30), "c": (0, 200), "d": (500, 0)}) == ["b", "a", "d", "c"]
          and themes_mod.ROW_BAND == themes_mod.CARD_H // 2 and "const TH_ROW = 40;" in js)
    first = themes_mod.state(work, "Juno")
    cards = {c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in first["cards"]}
    a1, a2, a3, s1, b1, b2, gone = k[0], k[1], k[2], k[3], k[4], k[5], k[6]
    for key, (x, y) in {a2: (2000, 100), s1: (2000, 260), a1: (2000, 500), a3: (2300, 505),
                        b1: (3000, 120), b2: (3000, 40)}.items():
        cards[key].update(x=x, y=y)
    version = dict({k: x for k, x in first["version"].items() if k != "v"}, cards=cards, discarded=[gone], picks={}, groups=[
        {"id": "g1", "label": "Mornings", "members": [a1, a3, "g2", a2], "x": 2000, "y": 60},
        {"id": "g2", "label": "Small hours", "members": [s1], "x": 2000, "y": 230},
        {"id": "g3", "label": "Walks", "members": [b1, b2], "x": 3000, "y": 0}])
    themes_mod.save(work, version, "Juno")
    check("85: a theme's members as the canvas reads them, a sub-theme where its frame's top sits",
          themes_mod.theme_order(themes_mod.normalise(version), "g1") == [a2, "g2", a1, a3]
          and themes_mod.placed_order(version) == [a2, s1, a1, a3, b2, b1], str(themes_mod.placed_order(version)))
    draft, _ = themes_mod.draft_markdown(work, "Juno")
    body = draft.split("## A. Mornings\n", 1)[1]
    line = lambda key: f"- {text[key]} ("
    order = [body.index(line(a2)), body.index("### A1. Small hours"), body.index(line(s1)),
             body.index(line(a1)), body.index(line(a3))]
    check("85, 185, 206, 207, 208, 95: the draft lists a theme's statements by place, a sub-theme where its frame's top sits, "
          "as the table does, its PETs lettered",
          order == sorted(order) and draft.index("## A. Mornings\n") < draft.index("## B. Walks\n")
          and "continued" not in draft
          and draft.split("## B. Walks\n", 1)[1].index(line(b2)) < draft.split("## B. Walks\n", 1)[1].index(line(b1)),
          draft[:400])
    out = export_mod.export(work, themes=(themes_mod.themes_path(work), None), guard=False)
    rows = list(csv.reader(Path(out["path"]).read_text(encoding="utf-8-sig").splitlines()))[1:]
    said = [r[2] for r in rows]
    placed = [text[key] for key in (a2, s1, a1, a3, b2, b1)]
    rest = [text[key] for key in k if key not in (a1, a2, a3, s1, b1, b2, gone)]
    check("85: the CSV goes theme by theme in the same order, then the unplaced, then the discarded",
          said == placed + rest + [text[gone]] and rows[0][3] == "Mornings" and rows[1][3] == "Mornings / Small hours"
          and rows[-1][3] == "Set aside" and len(rows) == len(k), " | ".join(said[:6]))
    plain = demo_copy(root, "Plain", "Juno - EN & ES.xlsx")
    bare = list(csv.reader(Path(export_mod.export(plain)["path"]).read_text(encoding="utf-8-sig").splitlines()))[1:]
    check("85: with no themes file the CSV keeps transcript order", [r[2] for r in bare] == [text[key] for key in k])

    # ── 88. the reasons for what was left out, in the board (an agent's since the AI board went, aiout)
    kept = themes_mod.normalise(dict(version, ai={"discarded": {a1: "  off   the question ", "Initial:999:0": "gone",
                                                                a2: "", a3: None}}))
    check("88: normalise keeps a reason for a card the board holds, and nothing when there is none",
          kept["ai"] == {"discarded": {a1: "off the question"}} and "ai" not in themes_mod.normalise(version))
    themes_mod.save(work, dict(version, ai={"discarded": {gone: "about the weather"}}), "Juno")
    themes_mod.save(work, version, "Juno")
    held = themes_mod.current_version(themes_mod.load(work))
    check("88: a save from a page that sends no reasons leaves the file's as they were, and the screen gets them",
          held["ai"] == {"discarded": {gone: "about the weather"}}
          and themes_mod.state(work, "Juno")["discard_reasons"] == {gone: "about the weather"})

    # ── 87 and 89. the cog, the link, the band and what the routes carry
    real = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE)
    config_path = scratch / "themes-fb2" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps({"ai_suggest": True, "ai_provider": "anthropic", "model": "claude-haiku-4-5"}),
                           encoding="utf-8")
    try:
        server_mod.CONFIG_PATH = config_path
        server_mod.ROOT_OVERRIDE = str(root)
        opened = idiograph_routes.api_themes({"workbook": str(work)})
        check("89: /api/themes carries the project as /api/open does, and the settings",
              opened["project"]["research_question"] == GRAVITY_QUESTION and opened["project"]["demo"] is False
              and opened["config"]["model"] == "claude-haiku-4-5" and "key" not in json.dumps(opened["config"]).lower())
        saved = server_mod.api_settings({"model": "claude-sonnet-4-5"})
        check("87: a save from Settings answers with the bar's AI state beside the settings",
              saved["ai"]["model_name"] != "Haiku 4.5" and saved["ai"]["on"] is True and "cap" not in saved["ai"]
              and set(saved) == {"config", "ai"}, str(saved["ai"]))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = real
    check("87: Settings over this screen takes its case, and a save there refreshes the bar",
          "if (!$('themes').hidden && typeof TH !== 'undefined' && TH.path)" in fn(app, "distilSettingsCase")
          and "a.settingsOpen(ctx, c)" in fn(app, "openSettings")
          and "if (sends && sends.ctx.themes && typeof thSettingsSaved === 'function') thSettingsSaved(data, sends.saved);" in fn(app, "distilSettingsSaved")
          and "if (data && data.ai) TH.ai = data.ai;" in fn(js, "thSettingsSaved") and "thAiDraw();" in fn(js, "thSettingsSaved")
          and "body.path = ctx.path;" in fn(app, "projectBody"))

    # ── 82. the bin is never emptied
    check("82: nothing on the Themes screen empties the bin, and Remove is for a missing card alone",
          not re.search(r"[Ee]mpty the", screen + js) and "Empty bin" not in screen + js
          and fn(js, "thPileList").count("'remove', t('themes.pile.remove')") == 1 and "gone.map((key) => row(key, v.cards[key], 'remove'" in fn(js, "thPileList")
          and "Set aside is never emptied" in section)

    # ── 81, 83, 91 and 92: the pointer
    down = fn(js, "thPointerDown")
    check("81: H toggles the hand, V and Esc give back the pointer, and in it a plain drag pans",
          "if (e.key === 'h' || e.key === 'H') { e.preventDefault(); thHand(!TH.hand); return; }" in fn(js, "thKeyDown")
          and "if ((e.key === 'v' || e.key === 'V') && TH.hand) { e.preventDefault(); thHand(false); return; }" in fn(js, "thKeyDown")
          and "else if (TH.hand) thHand(false);" in fn(js, "thKeyDown")
          and "e.button === 1 || (e.button === 0 && (TH.space || TH.hand))" in down
          and "cursor: grab" in css_block(css, ".th-stage.th-grab, .th-stage.th-hand"))
    check("83: Cmd as well as Shift, Ctrl on Windows and Linux: a click adds or takes away, a drag adds a lasso",
          "const add = e.shiftKey || MOD(e);" in down and "cards: add ? [...TH.sel.cards] : []" in down
          and "if (add) { thToggle(item); TH.lastPick = thSelected(item) ? item : null; thPanelFollow(); return; }" in fn(js, "thPointerUp")
          and "if (!p.add) { TH.sel.cards.clear(); TH.sel.groups.clear(); }" in fn(js, "thDragStart")
          and "const MOD = (e) => (MAC ? e.metaKey : e.ctrlKey);" in app)
    check("91: a drag from the empty space in a frame takes the theme, and a click there selects it",
          "const frame = add ? null : thFrameAt(TH.v, TH.layout, thToWorld(e.clientX, e.clientY), null);" in down
          and "item: { kind: 'group', id: frame }" in down and "frame: true" in down
          and "const named = item.kind === 'card' || item.kind === 'sticky' || (item.kind === 'group' && !frame);" in fn(js, "thPointerUp"))
    check("92: Alt at the drop takes what is dragged out of its theme, and Alt in the drag shows it first",
          "d.alt = !!(e.altKey || d.alt);" in fn(js, "thDragEnd") and "const alt = d.alt;" in fn(js, "thDragEnd")
          and "hit && hit.frame ? hit.group : null, alt);" in fn(js, "thDragEnd")
          and "if (e.key === 'Alt' && TH.drag) { e.preventDefault(); thDragAlt(true); return; }" in fn(js, "thKeyDown")
          and "if (e.key === 'Alt' && TH.drag) { thDragAlt(false); return; }" in fn(js, "thKeyUp")
          and "el.classList.toggle('leaving', leaving.has(id));" in fn(js, "thPlace")
          and "background: var(--card)" in css_block(css, ".th-card.in.leaving"))
    check("92: a right-click on a card or a label opens its menu, in the row menu's paper, and Esc closes it",
          "stage.addEventListener('contextmenu', thContextMenu);" in js and "pop.className = 'row-menu th-cmenu';" in fn(js, "thMenuOpen")
          and "if (TH.menu) { if (e.key === 'Escape') { e.preventDefault(); thMenuClose(); return; } thMenuClose(); }" in fn(js, "thKeyDown")
          and "position: fixed" in css_block(css, ".th-cmenu"))
    # a drop is told by the title strip, or for statements the body, under the pointer since 18 and 19 October (area 188)
    check("95: a drag draws the frames reaching out to what is dragged",
          "TH.layout = drag ? thDragLayout(v, thSize, moving, out, drag.from && drag.from.groups) : thLayout(v, thSize, null);"
          in fn(js, "thPlace"))
    check("84: arrange sits beside the cross on a label, in the panel and in the menu, one step of undo",
          '<button type="button" class="th-arr"' in fn(js, "thRender")
          and fn(js, "thRender").index('class="th-arr"') < fn(js, "thRender").index('class="th-del"')
          and "thArrangeHtml(g.id)" in fn(js, "thPanelDraw") and "thArrangeGroup(arrange.dataset.arrange)" in js
          and "if (del.classList.contains('th-arr')) thArrangeGroup(label.dataset.group);" in js
          and fn(js, "thArrangeGroup").count("thDone(") == 1 and "const before = thSnap(v, TH.removed);" in fn(js, "thArrangeGroup"))

    # ── 98. motion, and reduced motion honoured
    reduced = css.split("@media (prefers-reduced-motion: reduce)", 1)[1].split("\n}", 1)[0] if "prefers-reduced-motion" in css else ""
    check("98: reduced motion takes it all away, the transitions, the lift, the lean and the easing",
          "scale: none !important; rotate: none !important;" in reduced
          and "* { animation: none !important; transition: none !important; }" in style
          and "if (!from || !TH.v || thCalm()) return;" in fn(js, "thEase") and "if (!d || thCalm()) return;" in fn(js, "thLean")
          and "matchMedia('(prefers-reduced-motion: reduce)')" in js)

    # ── the model, in node
    node = shutil.which("node")
    if not node:
        return skip("the second feedback's model in node", "no node on this machine")
    script = scratch / "themes-feedback-two.js"
    script.write_text(support.i18n_js() + js + r"""
const size = (item) => (item.startsWith('g') ? { w: 120, h: 30 } : { w: 200, h: 80 });
const card = (x, y) => ({ x, y, text: 't' });
const keep = (x) => JSON.parse(JSON.stringify(x));
const box = (v, key) => ({ x: v.cards[key].x, y: v.cards[key].y, w: 200, h: 80 });
const out = {};
// 80: a card brought inside another's margin, not on it, settles clear by the margin, and undo puts it back
const m = { cards: { 'a:1:0': card(0, 0), 'a:2:0': card(205, 0) }, groups: [], discarded: [], picks: {} };
const before = thSnap(m, []);
out.margin = [thSettle(m, size, ['a:2:0'], {}, []), keep(m.cards['a:2:0'])];
thPut(m, before);
out.undone = keep(m.cards['a:2:0']);
// 80: a label made just over a card, inside its margin, nudges that card clear by the margin
const l = { cards: { 'e:1:0': card(0, 0), 'e:2:0': card(0, -123) }, groups: [], discarded: [], picks: {} };
const lid = thMakeGroup(l, ['e:1:0'], 'Over');
thSettle(l, size, [], {}, [lid]);
const llay = thLayout(l, size, null);
out.nudge = [thMeets(llay[lid].label, box(l, 'e:2:0'), TH_MARGIN - 1), keep(l.cards['e:1:0'])];
// 84: arrange keeps the reading order, makes a compact block under the label, and the label stays
const a = { cards: { 'c:1:0': card(500, 0), 'c:2:0': card(0, 300), 'c:3:0': card(250, 10), 'c:4:0': card(0, 600), 'c:5:0': card(300, 290) },
  groups: [], discarded: [], picks: {} };
const ga = thMakeGroup(a, ['c:1:0', 'c:2:0', 'c:3:0', 'c:4:0', 'c:5:0'], 'Tidy');
const alay = thLayout(a, size, null);
const order = thThemeOrder(a, ga, alay);
const asnap = thSnap(a, []);
out.arranged = [thArrange(a, ga, size), order, thThemeOrder(a, ga, thLayout(a, size, null)),
  ['c:3:0', 'c:1:0', 'c:2:0', 'c:5:0', 'c:4:0'].map((key) => [a.cards[key].x, a.cards[key].y]),
  [alay[ga].label.x, alay[ga].label.y], [thLayout(a, size, null)[ga].label.x, thLayout(a, size, null)[ga].label.y]];
thPut(a, asnap);
out.arrangeUndone = keep(a.cards['c:1:0']);
// 84: a sub-theme is arranged inside its own frame, then set in the block as one piece
const s = { cards: { 'd:1:0': card(0, 0), 'd:2:0': card(0, 900), 'd:3:0': card(600, 300), 'd:4:0': card(900, 300) }, groups: [], discarded: [], picks: {} };
const gs = thMakeGroup(s, ['d:1:0', 'd:2:0', 'd:3:0', 'd:4:0'], 'Outer');
const sub = thMakeGroup(s, ['d:3:0', 'd:4:0'], 'Inner');
thArrange(s, gs, size);
const slay = thLayout(s, size, null);
const inside = (b, f) => b.x >= f.x && b.y >= f.y && b.x + b.w <= f.x + f.w && b.y + b.h <= f.y + f.h;
const clear = ['d:1:0', 'd:2:0'].every((key) => !thMeets(box(s, key), slay[sub].frame, TH_MARGIN - 1));
out.sub = [inside(box(s, 'd:3:0'), slay[sub].frame) && inside(box(s, 'd:4:0'), slay[sub].frame), clear,
  thThemeOrder(s, gs, slay)];
// 84: an arranged theme that lands on another settles clear as a block
const tv = { cards: { 'f:1:0': card(0, 0), 'f:2:0': card(0, 400), 'f:3:0': card(215, 0) }, groups: [], discarded: [], picks: {} };
const gt = thMakeGroup(tv, ['f:1:0', 'f:2:0'], 'Lands');
thArrange(tv, gt, size);
thSettle(tv, size, [gt], {}, []);
out.landed = ['f:1:0', 'f:2:0'].every((key) => !thMeets(box(tv, key), box(tv, 'f:3:0'), TH_MARGIN - 1));
// 95: the frame reaches out to a card dragged far, and with Alt held lets go of it
const u = { cards: { 'h:1:0': card(0, 0), 'h:2:0': card(250, 0), 'h:3:0': card(0, 600) }, groups: [], discarded: [], picks: {} };
const gu = thMakeGroup(u, ['h:1:0', 'h:2:0'], 'Stretch');
const gv = thMakeGroup(u, ['h:3:0'], 'Other');
const moving = thMoving(u, new Set(['h:1:0']), new Set());
u.cards['h:1:0'].x = 4000;
const live = thDragLayout(u, size, moving, false)[gu].frame;
const alt = thDragLayout(u, size, moving, true)[gu].frame;
out.frame = [live.x + live.w >= 4200, alt.x + alt.w < 1000, [...thLeavers(u, moving)]];
// 92: Alt at the drop takes it out where it lands, in its own frame too, and another theme takes it in
out.leave = [keep(thDrop(u, moving, null, null, true)), thParents(u)['h:1:0'] === undefined, keep(u.cards['h:1:0'])];
thJoin(u, ['h:1:0'], gu);
out.leaveOwn = keep(thDrop(u, moving, null, gu, true));
thJoin(u, ['h:1:0'], gu);
out.joinOther = [keep(thDrop(u, moving, null, gv, true)), keep(thGroup(u, gv).members)];
// 95: a sub-theme dragged inside its theme stretches that theme's frame live
const p = { cards: { 'i:1:0': card(0, 0), 'i:2:0': card(0, 200) }, groups: [], discarded: [], picks: {} };
const gp = thMakeGroup(p, ['i:1:0', 'i:2:0'], 'Parent');
const gq = thMakeGroup(p, ['i:2:0'], 'Child');
const pm = thMoving(p, new Set(), new Set([gq]));
p.cards['i:2:0'].y = 3000;
thLayout(p, size, null);
out.subFrame = [thGroup(p, gq).members.length, thDragLayout(p, size, pm, false)[gp].frame.y + thDragLayout(p, size, pm, false)[gp].frame.h >= 3080,
  thLayout(p, size, pm)[gp].frame.y + thLayout(p, size, pm)[gp].frame.h < 3000];
// 91: the empty space inside a frame is the theme's, for a drag or a click to take
const f = { cards: { 'j:1:0': card(0, 0), 'j:2:0': card(600, 300) }, groups: [], discarded: [], picks: {} };
const gf = thMakeGroup(f, ['j:1:0', 'j:2:0'], 'Wide');
const flay = thLayout(f, size, null);
out.frameAt = [thFrameAt(f, flay, { x: 400, y: 150 }, null), thFrameAt(f, flay, { x: 2000, y: 150 }, null)];
// 92: the right-click menu's entries for a card in a theme, a card in none, a theme and a sub-theme
const r = { cards: { 'k:1:0': card(0, 0), 'k:2:0': card(0, 300), 'k:3:0': card(900, 0) }, groups: [], discarded: [], picks: {} };
const gr = thMakeGroup(r, ['k:1:0', 'k:2:0'], 'Menu');
const gsub = thMakeGroup(r, ['k:2:0'], 'Sub');
const labels = (item) => thMenuItems(r, item).map((it) => it.label);
out.menu = [labels({ kind: 'card', id: 'k:1:0' }), labels({ kind: 'card', id: 'k:3:0' }),
  labels({ kind: 'group', id: gr }), labels({ kind: 'group', id: gsub })];
// 88: the board's reasons go back to the file as they came, and the pile reads them by key
const w = { cards: { 'l:1:0': card(0, 0) }, groups: [], discarded: ['l:1:0'], picks: {}, ai: { discarded: { 'l:1:0': 'off the question' } } };
out.why = [thWhy(w, 'l:1:0'), thWhy(w, 'l:2:0'), keep(thBody(w, { id: 'v1', name: 'V' }).ai),
  'ai' in thBody({ cards: {}, groups: [], discarded: [], picks: {} }, { id: 'v1', name: 'V' })];
// 85: the reading order the page arranges by
out.read = thReadOrder([{ id: 'a', x: 300, y: 4 }, { id: 'b', x: 0, y: 30 }, { id: 'c', x: 0, y: 200 }, { id: 'd', x: 500, y: 0 }]);
console.log(JSON.stringify(out));
""", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("the second feedback's model runs in node", False, run.stderr.strip()[:300])
    out = json.loads(run.stdout)
    check("80: a card brought inside another's margin settles clear by exactly the margin, and undo puts it back",
          out["margin"] == [True, {"x": 210, "y": 0, "text": "t"}] and out["undone"] == {"x": 205, "y": 0, "text": "t"},
          str(out["margin"]))
    check("80: a label made inside a card's margin nudges the card clear by the margin, its own card staying",
          out["nudge"] == [False, {"x": 0, "y": 0, "text": "t"}], str(out["nudge"]))
    arranged = out["arranged"]
    check("84: arrange keeps the order the theme read in, top to bottom with ties broken left to right",
          arranged[0] is True and arranged[1] == ["c:3:0", "c:1:0", "c:2:0", "c:5:0", "c:4:0"] and arranged[2] == arranged[1],
          str(arranged[1:3]))
    check("84: in a compact block the margin apart, under a label that stays where it stood",
          arranged[3] == [[0, 0], [210, 0], [420, 0], [0, 90], [210, 90]] and arranged[4] == arranged[5]
          and out["arrangeUndone"] == {"x": 500, "y": 0, "text": "t"}, str(arranged[3:]))
    check("84: a sub-theme arranged inside its own frame and set in the block as one piece, the margin clear",
          out["sub"][0] is True and out["sub"][1] is True and out["sub"][2][0] == "d:1:0", str(out["sub"]))
    check("84: an arranged theme that lands on another card settles clear of it", out["landed"] is True)
    check("95: while a member is dragged far its frame reaches out to it, and with Alt held lets go of it",
          out["frame"] == [True, True, ["h:1:0"]], str(out["frame"]))
    check("92: Alt at the drop takes the card out of its theme, where it lands",
          out["leave"][0] == {"joined": [], "left": ["h:1:0"], "dest": None} and out["leave"][1] is True
          and out["leave"][2] == {"x": 4000, "y": 0, "text": "t"}, str(out["leave"]))
    check("92: inside its own theme's frame with Alt it leaves too, and inside another's it joins that one",
          out["leaveOwn"] == {"joined": [], "left": ["h:1:0"], "dest": "g1"}
          and out["joinOther"] == [{"joined": ["h:1:0"], "left": [], "dest": "g2"}, ["h:3:0", "h:1:0"]], str(out["joinOther"]))
    check("95: a sub-theme dragged inside its theme stretches that theme's frame live, and a drop still reads the rest",
          out["subFrame"] == [1, True, True], str(out["subFrame"]))
    check("91: the empty space inside a frame is the theme's, and outside it nothing's",
          out["frameAt"] == ["g1", None], str(out["frameAt"]))
    check("92, 183, 156, 208: the right-click menu offers what applies, in the brief's order, Inspect first, Go to the passage "
          "after it on a card since 16 October, Copy to board on a label, and New group inside after Inspect on a label since 20 October",
          out["menu"] == [["Inspect", "Go to the passage", "Group", "Take out of PET", "Set aside"], ["Inspect", "Go to the passage", "Group", "Set aside"],
                          ["Inspect", "New group inside", "Auto-arrange", "Rename", "Add description", "Note", "Copy to board\u2026",
                           "Delete this label"],
                          ["Inspect", "New group inside", "Take out of PET", "Auto-arrange", "Rename", "Add description", "Note",
                           "Copy to board\u2026", "Delete this label"]],
          str(out["menu"]))
    check("88: the page sends the reasons back as they came and reads one by its card",
          out["why"] == ["off the question", "", {"discarded": {"l:1:0": "off the question"}}, False], str(out["why"]))
    check("85: the page reads a theme the way the export does", out["read"] == ["b", "a", "d", "c"])
