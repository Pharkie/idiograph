from __future__ import annotations

import inspect
import json
import re
import shutil
import sys
from pathlib import Path

import ai_suggest as ai_mod
from workbook import WorkbookError

from . import support
from .support import GRAVITY_QUESTION, check, demo_copy, skip
import idiograph_routes


def test_themes_feedback(scratch):
    print("\n42. Themes, the first feedback: the wheel, no overlaps, the bin, frames, tints, the limit and Finder")
    import subprocess
    import server as server_mod
    import themes as themes_mod
    import themes_ai

    root = scratch / "themes-fb-root"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    (root / "idiograph-project.json").write_text(json.dumps(
        {"name": "Scratch", "research_question": GRAVITY_QUESTION}), encoding="utf-8")
    read = themes_mod.read_cards(work)
    k = [c["key"] for c in read["cards"]]

    # ── A. nothing overlaps: a shift clear by the margin, a block kept together, a new card's place
    gap = themes_mod.MARGIN
    dropped = [(260, 20, 200, 80)]
    others = [(0, 0, 200, 80), (250, 0, 200, 80), (500, 0, 200, 80)]
    dx, dy = themes_mod.free_offset(dropped, others, gap)
    landed = (260 + dx, 20 + dy, 200, 80)
    check("a card dropped over another shifts to the nearest spot the margin clear of everything",
          not any(themes_mod.clash(landed, o, gap - 1) for o in others) and abs(dx) + abs(dy) <= 150,
          f"shifted by {dx}, {dy}")
    block = [(100, 10, 200, 80), (400, 40, 200, 80)]
    bx, by = themes_mod.free_offset(block, [(0, 0, 200, 80)], gap)
    moved_block = [(b[0] + bx, b[1] + by, b[2], b[3]) for b in block]
    check("a block shifts as one, keeping its own arrangement",
          moved_block[1][0] - moved_block[0][0] == 300 and moved_block[1][1] - moved_block[0][1] == 30
          and not themes_mod.clash(moved_block[0], (0, 0, 200, 80), gap - 1), f"{bx}, {by}")
    check("a block clear already stays where it landed", themes_mod.free_offset([(900, 900, 200, 80)], others, gap) == (0, 0))

    # ── B. the limit on the themes, in config.json under `themes`, through the settings
    real = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.PLATFORM, idiograph_routes.REVEAL,
            ai_mod.find_key, ai_mod.http_call)
    config_path = scratch / "themes-fb" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps({"ai_suggest": True, "ai_provider": "anthropic", "model": "claude-haiku-4-5"}),
                           encoding="utf-8")
    sent, replies, revealed = [], [], []

    def wire(method, url, headers, payload, timeout):
        sent.append(payload)
        return 200, json.dumps({"content": [{"type": "text", "text": replies[0](payload) if replies else ""}],
                                "stop_reason": "end_turn"})

    def keys_in(payload):
        return re.findall(r"^- (\S+:\d+:\d+) \(", payload["messages"][-1]["content"], re.M)

    try:
        server_mod.CONFIG_PATH = config_path
        server_mod.ROOT_OVERRIDE = str(root)
        ai_mod.find_key = lambda *a, **kw: "k-test"
        ai_mod.http_call = wire
        idiograph_routes.REVEAL = lambda target: revealed.append(Path(target))
        opened = idiograph_routes.api_themes({"workbook": str(work)})
        check("with nothing saved the limit is five, and /api/themes carries it with the model's plain name",
              opened["ai"]["cap"] == 5 and opened["ai"]["model_name"] == "Haiku 4.5"
              and server_mod.config()["themes"] == {"cap": 5})
        server_mod.api_settings({"themes": {"cap": 3}})
        stored = json.loads(config_path.read_text(encoding="utf-8"))
        check("the stepper's limit is written under themes and read back",
              stored["themes"] == {"cap": 3} and idiograph_routes.api_themes({"workbook": str(work)})["ai"]["cap"] == 3
              and stored["ai_suggest"] is True and stored["model"] == "claude-haiku-4-5")
        server_mod.api_settings({"interviewer": "Adam"})
        kept = json.loads(config_path.read_text(encoding="utf-8"))["themes"]
        server_mod.api_settings({"themes": {"cap": 14}})
        high = json.loads(config_path.read_text(encoding="utf-8"))["themes"]["cap"]
        server_mod.api_settings({"themes": {"cap": "one"}})
        check("a save from Settings keeps the limit, and the limit stays between two and nine",
              kept == {"cap": 3} and high == 9 and server_mod.config()["themes"]["cap"] == 5
              and themes_ai.clean_cap(1) == 2 and themes_ai.clean_cap(9.4) == 9)
        check("the server says which platform it runs on, so Show in Finder shows on a Mac alone",
              opened["platform"] == sys.platform)

        # ── C. the prompt asks for between one fewer and the limit, with the IPA guidance
        system = themes_ai.group_system(GRAVITY_QUESTION, 3)
        check("the prompt carries the limit: one fewer to the limit, one more only with a reason",
              "His limit is 3 themes. Make between 2 and 3 themes. Make 4 only when" in system
              and 'say why in "reason"' in system and '"reason": "..."' in system)

        # ── D. the parser takes `reason` and what is left out, an older answer's `discarded` the same, and refuses past the limit and one
        answer = {"groups": [{"label": f"Theme {i}", "members": [k[i]]} for i in range(4)],
                  "discarded": [{"key": k[5], "reason": "It is about the weather; not the dog \u2014 at all"},
                                {"key": k[0], "reason": "placed already"}, {"key": "Initial:999:0", "reason": "no"},
                                k[6]],
                  "reason": "Walks stand apart from the mornings"}
        parsed = themes_ai.parse_grouping(json.dumps(answer), k, cap=3)
        check("the parser takes the reason and each one left out with why, a key placed or unknown left out of it (182)",
              parsed["reason"] == "Walks stand apart from the mornings"
              and parsed["left_out"] == [{"key": k[5], "reason": "It is about the weather, not the dog, at all"},
                                         {"key": k[6], "reason": ""}]
              and parsed["placed"] == 4 and parsed["left"] == len(k) - 4 and parsed["repeated"] == 1
              and parsed["unknown"] == 1, str(parsed)[:200])
        over = dict(answer, groups=[{"label": f"Theme {i}", "members": [k[i]]} for i in range(5)])
        check("a proposal of more PETs than the limit and one is refused with a line",
              themes_ai.parse_grouping(json.dumps(over), k, cap=3)
              == {"error": "The answer proposed 5 PETs, more than one past the limit of 3, so no board was made."}
              and "error" not in themes_ai.parse_grouping(json.dumps(over), k, cap=4))

        replies[:] = [lambda p: json.dumps({"groups": [
            {"label": "Mornings that belong to the dog", "members": keys_in(p)[0:5]},
            {"label": "A house that holds two", "members": keys_in(p)[5:9]},
            {"label": "Walks taken alone", "members": keys_in(p)[9:12]},
            {"label": "The evenings that close the day", "members": keys_in(p)[12:15]}],
            "discarded": [{"key": keys_in(p)[15], "reason": "a line about the weather"}],
            "reason": "Walks are apart from the house"})]
        made = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "group", "cap": 3})
        data = json.loads(themes_mod.themes_path(work).read_text(encoding="utf-8"))
        new = data["boards"][-1]
        thrown = keys_in(sent[-1])[15]
        check("the request carries the limit asked for, and what the answer left out stays in Not placed, never the bin (182)",
              "His limit is 3 themes." in sent[-1]["system"] and made["made"]["cap"] == 3
              and made["made"]["themes"] == 4 and made["made"]["left_out"] == 1 and thrown not in new["discarded"]
              and not any(thrown in g["members"] for g in new["groups"]))
        check("the note is one line, with the model's reason as a second sentence, and no reason for what was left out in it",
              "up to 3 PETs. 4 PETs, 15 placed, 3 not placed. Quotes picked for 0 of 4 PETs. "
              "Its reason: Walks are apart from the house." in new["note"]
              and "\n" not in new["note"] and "a line about the weather" not in new["note"], new["note"])
        check("why each statement was left out goes into the board under ai, for its card in Not placed",
              new["ai"] == {"discarded": {thrown: "a line about the weather"}}, str(new.get("ai")))
        before = themes_mod.themes_path(work).read_bytes()
        replies[:] = [lambda p: json.dumps({"groups": [{"label": f"T{i}", "members": [keys_in(p)[i]]} for i in range(6)]})]
        refused = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "group", "cap": 3})
        check("a proposal past the limit and one makes no board", set(refused) == {"error"}
              and "more than one past the limit of 3" in refused["error"]
              and themes_mod.themes_path(work).read_bytes() == before)
        replies[:] = [lambda p: json.dumps({"groups": [{"label": "One", "members": keys_in(p)[:3]}]})]
        idiograph_routes.api_themes_ai({"workbook": str(work), "op": "group"})
        check("with no limit sent, the one in the settings goes", "His limit is 5 themes." in sent[-1]["system"])

        # ── E. the export names its files the case's way, and Show in Finder
        out = idiograph_routes.api_themes_export({"workbook": str(work)})
        name = out["version"]["name"]
        check("the export names both files as the case holds them, Working/<file>",
              out["shown"] == [f"Working/Juno - PET draft ({name}).md", "Working/Juno - All Experiential Statements.csv"])
        server_mod.PLATFORM = "darwin"
        shown = idiograph_routes.api_themes_export({"workbook": str(work), "op": "reveal", "file": out["shown"][0]})
        mine = idiograph_routes.api_themes_export({"workbook": str(work), "op": "reveal"})
        check("on a Mac, reveal runs the Finder on the markdown draft and writes nothing",
              shown == {"revealed": out["shown"][0]} and mine == shown
              and revealed == [(work.parent / "Working" / f"Juno - PET draft ({name}).md").resolve()] * 2)
        refusals = []
        outside = demo_copy(scratch, "themes-fb-elsewhere", "Juno - EN & ES.xlsx")
        (outside.parent / "Working").mkdir(parents=True, exist_ok=True)
        (outside.parent / "Working" / "Juno - PET draft (Board 1).md").write_text("# a draft\n", encoding="utf-8")
        for body in ({"workbook": str(work), "op": "reveal", "file": "../../themes-fb-elsewhere/Working/Juno - PET draft (Board 1).md"},
                     {"workbook": str(work), "op": "reveal", "file": "Juno - EN & ES.xlsx"},
                     {"workbook": str(outside), "op": "reveal", "file": "Working/Juno - PET draft (Board 1).md"}):
            try:
                idiograph_routes.api_themes_export(body)
                refusals.append(False)
            except server_mod.OutsideRoot:
                refusals.append(True)
        try:
            idiograph_routes.api_themes_export({"workbook": str(work), "op": "reveal", "file": "Working/nothing here.md"})
            gone = False
        except WorkbookError:
            gone = True
        server_mod.PLATFORM = "linux"
        try:
            idiograph_routes.api_themes_export({"workbook": str(work), "op": "reveal"})
            elsewhere = False
        except WorkbookError as exc:
            elsewhere = "Mac" in str(exc)
        check("reveal refuses a file outside the case root or its Working folder, one not there, and any machine but a Mac",
              refusals == [True, True, True] and gone and elsewhere and len(revealed) == 2, str(refusals))
        check("reveal goes through open -R and nothing else",
              '["open", "-R", str(target)]' in inspect.getsource(real[3]))
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.PLATFORM, idiograph_routes.REVEAL,
         ai_mod.find_key, ai_mod.http_call) = real

    # ── F. counts, read the same way here and on the page
    check("a label's count reads as a count", themes_mod.count_text(3) == "3 statements"
          and themes_mod.count_text(1) == "1 statement" and themes_mod.count_text(7, 2) == "2 sub-themes · 7 statements"
          and themes_mod.count_text(1, 1) == "1 sub-theme · 1 statement")

    # ── G. the page
    js = support.text("apps/idiograph/static/themes.js")
    fn = lambda text, name: text.split(f"function {name}(", 1)[1].split("\n}", 1)[0]
    wheel = fn(js, "thWheel")
    check("the wheel zooms about the pointer, a sideways wheel or Shift pans sideways and Alt up and down, and panning is also Space with a drag or the middle button (188)",
          "thZoomAt(" in wheel and "e.clientX, e.clientY" in wheel
          and "if (!e.ctrlKey && (e.altKey || e.shiftKey || Math.abs(dx) > Math.abs(dy))) {" in wheel
          and "if (e.altKey) TH.view.y -= dy || dx;" in wheel and "else TH.view.x -= dx || dy;" in wheel
          and "e.button === 1 || (e.button === 0 && (TH.space || TH.hand))" in fn(js, "thPointerDown"))
    check("Backspace on a card takes it out of its theme, on a label deletes the label, one step of undo",
          "thLeaveThemes(cards)" in fn(js, "thDeleteKey") and "for (const id of labels) thDelete(v, id);" in fn(js, "thDeleteKey")
          and "for (const id of live) thLeave(v, id);" in fn(js, "thLeaveThemes") and "thDone(before, what" in fn(js, "thLeaveThemes"))
    check("the panel offers Take out of PET, or of sub-theme, for a card or a sub-theme in one (Remove from until 20 October)",
          "`${esc(thLeaveLabel(v, owner))}</button>`" in fn(js, "thLeaveHtml") and "thLeaveHtml(v, item.id, owner)" in fn(js, "thPanelDraw")
          and "thLeaveThemes([leave.dataset.leave])" in js)
    check("every move settles so nothing overlaps, a drop where it is let go and a put back shifting clear",
          "thSettle(TH.v, thSize, opts.settle, was, opts.labels, TH_PASSES, !!opts.stay)" in fn(js, "thDone")
          and "{ settle: d.moving, stay: true, was: d.was, from: shown, lifted, lean: d.lean }" in fn(js, "thDragEnd")
          and "{ settle: [key] }" in fn(js, "thPutBack"))

    node = shutil.which("node")
    if not node:
        return skip("the feedback's model in node", "no node on this machine")
    script = scratch / "themes-feedback.js"
    script.write_text(support.i18n_js() + js + r"""
const size = (item) => (item.startsWith('g') ? { w: 120, h: 30 } : { w: 200, h: 80 });
const card = (x, y) => ({ x, y, text: 't' });
const keep = (x) => JSON.parse(JSON.stringify(x));
const boxes = (v) => Object.keys(v.cards).filter((k) => thOnCanvas(v, k)).map((k) => ({ x: v.cards[k].x, y: v.cards[k].y, w: 200, h: 80 }));
const near = (list, gap) => { let n = 0; for (let i = 0; i < list.length; i++) for (let j = i + 1; j < list.length; j++) if (thMeets(list[i], list[j], gap)) n++; return n; };
const out = {};
// a card dropped on another shifts clear by the margin
const v = { cards: { 'a:1:0': card(0, 0), 'a:2:0': card(250, 0), 'a:3:0': card(500, 0), 'a:4:0': card(260, 20) }, groups: [], discarded: [], picks: {} };
out.shifted = [thSettle(v, size, ['a:4:0'], {}, []), keep(v.cards['a:4:0']), near(boxes(v), TH_MARGIN - 1)];
// a selection dropped as one keeps its arrangement
const w = { cards: { 'b:1:0': card(0, 0), 'b:2:0': card(100, 10), 'b:3:0': card(400, 40) }, groups: [], discarded: [], picks: {} };
thSettle(w, size, new Set(['b:2:0', 'b:3:0']), {}, []);
out.block = [w.cards['b:3:0'].x - w.cards['b:2:0'].x, w.cards['b:3:0'].y - w.cards['b:2:0'].y, near(boxes(w), 0)];
// a label made over a card lands on the card above it, which goes clear
const l = { cards: { 'e:1:0': card(0, 0), 'e:2:0': card(0, -70) }, groups: [], discarded: [], picks: {} };
const lid = thMakeGroup(l, ['e:1:0'], 'Over');
thSettle(l, size, [], {}, [lid]);
const llay = thLayout(l, size, null);
out.label = [thMeets(llay[lid].label, { x: l.cards['e:2:0'].x, y: l.cards['e:2:0'].y, w: 200, h: 80 }), keep(l.cards['e:1:0'])];
// frames: a member dragged far stays, a drop in another frame moves it, Backspace's leave takes it out
const u = { cards: { 'c:1:0': card(0, 0), 'c:2:0': card(250, 0), 'c:3:0': card(0, 600), 'c:4:0': card(250, 600) }, groups: [], discarded: [], picks: {} };
const g1 = thMakeGroup(u, ['c:1:0', 'c:2:0'], 'One');
const g2 = thMakeGroup(u, ['c:3:0', 'c:4:0'], 'Two');
const moving = thMoving(u, new Set(['c:1:0']), new Set());
u.cards['c:1:0'].x = 4000;
let lay = thLayout(u, size, moving);
out.far = [keep(thDrop(u, moving, null, thFrameAt(u, lay, { x: 4100, y: 40 }, moving))), keep(thGroup(u, g1).members)];
const all = thLayout(u, size, null);
out.frame = [all[g1].frame.x <= 250 && all[g1].frame.x + all[g1].frame.w >= 4200, thPad(all[g1].all).w === all[g1].frame.w];
u.cards['c:1:0'].x = 30; u.cards['c:1:0'].y = 640;
lay = thLayout(u, size, moving);
const inside = thFrameAt(u, lay, { x: 60, y: 660 }, moving);
out.moved = [inside, keep(thDrop(u, moving, null, inside)), keep(thGroup(u, g1).members), keep(thGroup(u, g2).members)];
thLeave(u, 'c:1:0');
out.left = [keep(thGroup(u, g2).members), thParents(u)['c:1:0'] === undefined, keep(u.cards['c:1:0'])];
// a label dropped in another theme's frame joins it as a sub-theme
const lm = thMoving(u, new Set(), new Set([g1]));
lay = thLayout(u, size, lm);
const f2 = lay[g2].frame;
out.sub = [keep(thDrop(u, lm, null, thFrameAt(u, lay, { x: f2.x + 30, y: f2.y + 30 }, lm))), keep(thGroup(u, g2).members)];
// tints: twelve themes, none repeating, grey past eight, a sub-theme a step lighter
const tv = { cards: {}, groups: [], discarded: [], picks: {} };
for (let i = 0; i < 12; i++) { tv.cards[`d:${i}:0`] = card(i * 300, 0); thMakeGroup(tv, [`d:${i}:0`], `T${i}`); }
const inner = thMakeGroup(tv, ['d:0:0'], 'Inner');
const tints = thTints(tv);
out.tints = Object.keys(tints).map((id) => [id, tints[id].hue, tints[id].step]);
out.tintClass = [thTintClass(tints.g1), thTintClass(tints[inner]), thTintClass(tints.g12)];
// counts
out.count = [thCountText(u, g2), thCountText(tv, 'g2'), thCountText(tv, 'g1')];
console.log(JSON.stringify(out));
""", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("the feedback's model runs in node", False, run.stderr.strip()[:300])
    out = json.loads(run.stdout)
    check("in the page too, a card dropped over another shifts clear by the margin, recorded where it lands",
          out["shifted"][0] is True and out["shifted"][2] == 0 and out["shifted"][1] == {"x": 260, "y": 90, "text": "t"},
          str(out["shifted"]))
    check("a selection dropped on something shifts as a block, keeping its own arrangement",
          out["block"] == [300, 30, 0], str(out["block"]))
    check("a label that comes to sit on a card sends the card clear, and the label's own card stays",
          out["label"] == [False, {"x": 0, "y": 0, "text": "t"}], str(out["label"]))
    check("a member dragged far stays a member, and its theme's frame follows it there",
          out["far"] == [{"joined": [], "left": [], "dest": None}, ["c:1:0", "c:2:0"]] and out["frame"] == [True, True],
          str(out["far"]))
    check("a card dropped inside another theme's frame moves to that theme",
          out["moved"] == ["g2", {"joined": ["c:1:0"], "left": [], "dest": "g2"}, ["c:2:0"], ["c:3:0", "c:4:0", "c:1:0"]],
          str(out["moved"]))
    check("taken out of its theme a card stays where it stands, in none",
          out["left"] == [["c:3:0", "c:4:0"], True, {"x": 30, "y": 640, "text": "t"}], str(out["left"]))
    check("a label dropped inside another theme's frame joins it as a sub-theme",
          out["sub"] == [{"joined": ["g1"], "left": [], "dest": "g2"}, ["c:3:0", "c:4:0", "g1"]], str(out["sub"]))
    check("the count reads in statements, and on a label over labels the sub-themes and the statements",
          out["count"] == ["1 sub-theme · 3 statements", "1 statement", "1 sub-theme · 1 statement"], str(out["count"]))
