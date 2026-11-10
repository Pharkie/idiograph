from __future__ import annotations

import json
import shutil

from workbook import WorkbookError

from . import support
from .support import DEMO_QUESTION, check, demo_copy, skip
import idiograph_routes


def test_gets_sub_cards(scratch):
    print("\n86. GETs: a card for every PET and every sub-theme (193), New board, a case coming in, Take the "
          "changes, Add every sub-theme, New AI board, the count, the table, gets show and the MCP tool")
    import subprocess
    import cli
    import gets as gets_mod
    import mcp_server
    import server as server_mod
    import themes as themes_mod
    import themes_ai

    js = support.text("apps/idiograph/static/themes.js")
    guidance = support.source("apps/idiograph/pet_guidance.md").read_text(encoding="utf-8")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    flat = lambda text: " ".join(str(text).split())
    pristine = support.DEMO_PRISTINE

    def refused(call):
        try:
            call()
        except WorkbookError as exc:
            return str(exc)
        return ""

    def apart(a, b, gap):
        return (a[0] + a[2] + gap <= b[0] or b[0] + b[2] + gap <= a[0]
                or a[1] + a[3] + gap <= b[1] or b[1] + b[3] + gap <= a[1])

    def overlaps(board, data):
        """The pairs of cards in no GET that lie over one another on a stored board, as the page draws them."""
        drawn = themes_mod.layout_boxes(gets_mod.named(gets_mod.normal(board, data), data), gets_mod.card_height)
        boxes = list(drawn["cards"].items())
        return [(a, b) for i, (a, ba) in enumerate(boxes) for b, bb in boxes[i + 1:] if themes_mod.clash(ba, bb)]

    # \u2500\u2500 the fixture: Rowan and Mabel from the demo's pristine copy, each with sub-themes, and Wren,
    # invented on the demo's words, a sub-theme inside a sub-theme
    root = scratch / "gets-subs-root"
    shutil.rmtree(root, ignore_errors=True)
    for name in ("Rowan", "Mabel"):
        case = root / name
        (case / "Working").mkdir(parents=True)
        shutil.copy2(pristine / f"{name} - EN & ES.xlsx", case / f"{name} - EN & ES.xlsx")
        for side in (pristine / "Working").glob(f"{name} - *"):
            shutil.copy2(side, case / "Working" / side.name)
    wren = demo_copy(root, "Wren", "Wren - EN & ES.xlsx")
    keys = [c["key"] for c in themes_mod.read_cards(wren)["cards"]]

    def themes_file(book, name, groups):
        b = themes_mod.blank_version(themes_mod.read_cards(book)["cards"])
        b.update(id="v1", name="Board 1", groups=groups)
        themes_mod.write(book, {"schema": 2, "case": name, "workbook": book.name, "current": "v1", "chosen": "v1", "boards": [b]})

    nest = [{"id": "g1", "label": "Mornings that start at the stair", "members": keys[0:2] + ["g3"], "x": 0, "y": 0},
            {"id": "g2", "label": "Walks that close the day", "members": keys[4:6], "x": 0, "y": 700},
            {"id": "g3", "label": "Early light in the hall", "members": keys[2:3] + ["g4"], "x": 0, "y": 250},
            {"id": "g4", "label": "The first sound on the stair", "members": [keys[3], keys[6]], "x": 0, "y": 450}]
    themes_file(wren, "Wren", nest)
    (root / "idiograph-project.json").write_text(json.dumps(
        {"name": "Dogs, a scratch project", "research_question": DEMO_QUESTION,
         "agents": {"allowed": True, "at": "2026-10-06T10:00:00+01:00"}}), encoding="utf-8")
    config_file = scratch / "gets-subs-config.json"
    config_file.write_text(json.dumps({"root": str(root), "interviewer": "Adam"}), encoding="utf-8")
    saved = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    gfile = gets_mod.gets_path(root)
    any_book = str(wren)
    # Wren's g4 sits inside the sub-theme g3, a group, which rides inside g3's card (207)
    subs = {"Wren/g3", "Rowan/g6", "Rowan/g7", "Rowan/g8", "Mabel/g6", "Mabel/g7", "Mabel/g8", "Mabel/g9"}
    out_node = {}
    try:
        server_mod.CONFIG_PATH = config_file
        server_mod.ROOT_OVERRIDE = str(root)
        server_mod.STATE_MEMORY = {"recent": []}

        # \u2500\u2500 A. opening: a card for every PET and every sub-theme, in the pile as before, nothing written
        shown = idiograph_routes.api_gets({"workbook": any_book})
        cards = {c["key"]: c for c in shown["cards"]}
        panel = {c["case"]: c for c in shown["cases"]}
        depth = {c: gets_mod.depths({"pets": e["pets"]}) for c, e in panel.items()}
        every = {f"{c}/{p['id']}" for c, e in panel.items() for p in e["pets"] if depth[c][p["id"]] <= 1}
        found = {f"{c}/{p['id']}" for c, e in panel.items() for p in e["pets"] if depth[c][p["id"]] == 1}
        check("86, 207: opening, a card for every PET and every sub-theme of each case, each a card of its own in no GET, a group none",
              set(cards) == every and found == subs and len(every) == 20 and "Wren/g4" not in cards
              and all(cards[k]["kind"] == "sub" for k in subs) and all(cards[k]["kind"] == "pet" for k in every - subs)
              and shown["groups"] == [] and not gfile.exists(), str(sorted(set(cards) ^ every)))
        check("86, 207: a sub-theme's card names its words and counts its statements at any depth, its group's among them, as a PET's does",
              cards["Wren/g3"]["text"] == "Early light in the hall" and cards["Wren/g3"]["statements"] == 3
              and cards["Wren/g1"]["statements"] == 5 and cards["Wren/g3"]["who"] == "Wren")
        data, _cases, _disk, _taken = gets_mod.assemble(root, idiograph_routes.gets_books(root), themes_mod.now_iso())
        entries = [e for c in sorted(data["cases"], key=gets_mod.case_order) for e in gets_mod.cards_of(c, data["cases"][c])]
        check("86: in one round pile in an order seeded from the keys, as before, and no card over another",
              {k: {"x": c["x"], "y": c["y"]} for k, c in cards.items()} == gets_mod.pile(entries)
              and not overlaps(data["boards"][0], data)
              and [k for k, _ in gets_mod.cards_of("Wren", data["cases"]["Wren"])] == ["Wren/g1", "Wren/g3", "Wren/g2"]
              and [k for k, _ in gets_mod.cards_of("Wren", data["cases"]["Wren"], {"g3"})] == ["Wren/g3"])

        # \u2500\u2500 B. the first act writes them, then New board gives every one again, and gets show lists them
        body = dict(shown["version"], cards={k: {"x": c["x"], "y": c["y"]} for k, c in cards.items()},
                    groups=[], discarded=[], picks={}, notes=[])
        idiograph_routes.api_gets_save({"workbook": any_book, "version": body})
        made = idiograph_routes.api_gets_ops({"workbook": any_book, "op": "new"})
        new_cards = {c["key"]: c for c in made["cards"]}
        held = json.loads(gfile.read_text(encoding="utf-8"))
        check("86: New board lays every PET and every sub-theme of the study in the pile afresh, in no GET",
              set(new_cards) == every and made["groups"] == [] and made["version"]["name"] == "Board 2"
              and set(held["boards"][0]["cards"]) == set(held["boards"][1]["cards"]) == every
              and not overlaps(held["boards"][1], held))
        code, text, _ = cli.run(["--root", str(root), "--config", str(config_file), "gets", "show", "b2"])
        check("86: gets show on a new board lists the sub-themes in Not placed, each by its kind, case, words and key",
              code == 0 and "Not placed (20)" in text and "   Sub-theme Wren: Early light in the hall  [Wren/g3]" in text
              and "[Wren/g4]" not in text and "   PET Wren: Mornings that start at the stair  [Wren/g1]" in text
              and all(f"[{k}]" in text for k in subs), flat(text)[:200])
        srv = mcp_server.Server(str(root), config=str(config_file))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}}))
        tool = srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                       "params": {"name": "gets_show", "arguments": {"board": "b2"}}}))["result"]
        check("86: the MCP tool gets_show gives the same cards, its words the command line's",
              tool["isError"] is False and support.unfenced(tool["content"][0]["text"]).rstrip("\n") == text.rstrip("\n")
              and {c["key"] for c in support.plain(tool["structuredContent"])["unplaced"] if c["kind"] == "sub"} == subs)

        # \u2500\u2500 C. a case coming in, the page's board drawn before it, lands in the pile of every board
        fern = demo_copy(root, "Fern", "Fern - EN & ES.xlsx")
        themes_file(fern, "Fern", [{"id": "g1", "label": "A lead by the door", "members": keys[0:2] + ["g2"], "x": 0, "y": 0},
                                   {"id": "g2", "label": "Waiting at the gate", "members": keys[2:4], "x": 0, "y": 300}])
        page = dict(made["version"], cards={k: {"x": c["x"], "y": c["y"]} for k, c in new_cards.items()},
                    groups=[], discarded=[], picks={}, notes=[])
        # the autosave holds the study for a few seconds, and Fern is found once that has passed
        idiograph_routes._gets_books.clear()
        idiograph_routes.api_gets_save({"workbook": any_book, "version": page})
        held = json.loads(gfile.read_text(encoding="utf-8"))
        check("86: a case coming in, by a save or on its own, brings a card for its PET and its sub-theme into every board, clear of the rest",
              all({"Fern/g1", "Fern/g2"} <= set(b["cards"]) for b in held["boards"])
              and not any(overlaps(b, held) for b in held["boards"]) and len(held["boards"]) == 2,
              str([(b["id"], sorted(k for k in b["cards"] if k.startswith("Fern")), overlaps(b, held)[:2]) for b in held["boards"]]))

        # \u2500\u2500 D. Take the changes: a sub-theme new to the case comes in, one the board never held does not
        when = themes_mod.now_iso()
        tops = [e for c in sorted(held["cases"], key=gets_mod.case_order) for e in gets_mod.tops(c, held["cases"][c])]
        old = gets_mod.blank_board(held, "b3", "Board 3", when)
        old["cards"] = gets_mod.pile(tops)
        old["cards"]["Mabel/g6"] = {"x": -2000, "y": -2000}
        old["discarded"] = ["Mabel/g6"]
        old["groups"] = [{"id": "G1", "label": "Days given their shape by the dog", "members": ["Rowan/g1", "Mabel/g1"], "x": 0, "y": 0}]
        old["notes"] = [{"id": "n1", "text": "An invented sticky note in the middle", "colour": "yellow", "x": -60, "y": -40}]
        held["boards"].append(old)
        gets_mod.write(root, held)
        nest[1]["members"] = keys[4:5] + ["g5"]
        themes_file(wren, "Wren", nest + [{"id": "g5", "label": "The long way round the park", "members": [keys[5], keys[7]], "x": 0, "y": 900}])
        took = idiograph_routes.api_gets_cases({"workbook": any_book, "op": "take", "case": "Wren"})
        held = json.loads(gfile.read_text(encoding="utf-8"))
        b1, b2, b3 = held["boards"]
        check("86: Take brings a sub-theme new to the case into every board, in no GET and clear of the rest",
              took["op"] == "take" and all("Wren/g5" in b["cards"] for b in (b1, b2, b3))
              and not any("Wren/g5" in g["members"] for b in (b1, b2, b3) for g in b["groups"])
              and not any(overlaps(b, held) for b in (b1, b2, b3)))
        check("86: and never a sub-theme the case had and a board made before never held",
              "Wren/g3" not in b3["cards"] and "Wren/g4" not in b3["cards"] and "Rowan/g6" not in b3["cards"]
              and "Wren/g3" in b1["cards"] and "Wren/g4" not in b1["cards"] and b3["discarded"] == ["Mabel/g6"])

        # \u2500\u2500 E. Add every sub-theme on the board made before
        before = gfile.read_bytes()
        res = idiograph_routes.api_gets_boards({"workbook": any_book, "op": "subs", "id": "b3"})
        added = {c["key"]: c for c in res["added"]}
        want = {k for k in subs | {"Fern/g2", "Wren/g5"} if not gets_mod.has_card(b3, k)}
        check("86: Add every sub-theme answers a card for each sub-theme of the study with none on the board, a binned one counting as one",
              set(added) == want and "Mabel/g6" not in added and "Wren/g5" not in added and {"Wren/g3", "Fern/g2"} <= set(added) and "Wren/g4" not in added
              and all(c["kind"] == "sub" and c["text"] for c in added.values()) and res["op"] == "subs" and res["board"] == "b3",
              str(sorted(set(added) ^ want)))
        drawn = themes_mod.layout_boxes(gets_mod.named(gets_mod.normal(b3, held), held), gets_mod.card_height)
        others = (list(drawn["cards"].values()) + list(drawn["labels"].values()) + list(drawn["frames"].values())
                  + list(drawn["notes"].values()))
        landed = [(c["x"], c["y"], themes_mod.CARD_W, gets_mod.card_height(k, c["text"])) for k, c in added.items()]
        check("86: each in the nearest free spot the margin clear of every card, label, frame and sticky note there, and of each other",
              drawn["labels"] and drawn["notes"] and all(apart(a, o, themes_mod.MARGIN) for a in landed for o in others)
              and all(apart(a, b, 0) for i, a in enumerate(landed) for b in landed[i + 1:]))
        check("86: nothing is written, the page landing the cards as one step of undo",
              gfile.read_bytes() == before and "data-vop=\"subs\"" in js)
        b3_page = dict(idiograph_routes.api_gets({"workbook": any_book, "board": "b3"})["version"],
                       cards={**{k: dict(c) for k, c in b3["cards"].items()}, **{k: {"x": c["x"], "y": c["y"]} for k, c in added.items()}},
                       groups=b3["groups"], discarded=b3["discarded"], picks={}, notes=b3["notes"])
        idiograph_routes.api_gets_ops({"workbook": any_book, "op": "switch", "id": "b3"})
        idiograph_routes.api_gets_save({"workbook": any_book, "version": b3_page})
        check("86: with none to add it is refused with one line, and nothing is written",
              refused(lambda: idiograph_routes.api_gets_boards({"workbook": any_book, "op": "subs", "id": "b3"})) == gets_mod.NO_SUBS
              == "Every sub-theme has a card on this board already, so nothing was added."
              and subs <= set(json.loads(gfile.read_text(encoding="utf-8"))["boards"][2]["cards"]))

        # \u2500\u2500 F. New AI board works from the same cards: each sub-theme an item it may place under any GET
        held = json.loads(gfile.read_text(encoding="utf-8"))
        data, cases, _disk, _taken = gets_mod.assemble(root, idiograph_routes.gets_books(root), themes_mod.now_iso())
        study = gets_mod.ai_study(data, cases)
        units, ups = themes_ai.gets_units(study)
        system = themes_ai.gets_group_system(DEMO_QUESTION, 5, 3, 4)
        loose = themes_ai.gets_group_system(DEMO_QUESTION, 5, 3, 4, one_per_pet=False)
        user = themes_ai.gets_group_user(study, None)
        section5 = guidance.split("## 5. Group experiential themes", 1)[1].split("\n## ", 1)[0]
        rule3 = next(t for n, t in themes_ai.guidance_items(5) if n == 3)
        check("86, 207: the AI board's input sends each sub-theme by its own key, an item to place, its group riding inside it",
              subs <= set(units) and "Wren/g4" not in units and ups["Wren/g3"] == "Wren/g1"
              and "  - Sub-theme Wren/g3: Early light in the hall" in user and "Wren/g4" not in user
              and "each an item of its own to place" in user and "Group the PETs and sub-themes into GETs." in user)
        check("86: the prompt says a GET can draw on a PET or on one of its sub-themes, the guidance's own words, with One GET per PET on and off",
              all("A GET can draw on a PET or on one of its sub-themes" in t for t in (system, loose, rule3, section5))
              and "(Smith et al., 2022, ch. 5, Step 7)" in rule3 and themes_ai.SUBS_AS_ITEMS in system and themes_ai.SUBS_AS_ITEMS in loose
              and "Placing a PET does not place its sub-themes" in system and "<PET or sub-theme key>" in system
              and "Place every PET and sub-theme that belongs under a GET" in system)
        answer = {"gets": [{"label": "Mornings", "members": ["Wren/g1", "Wren/g3", "Rowan/g1"]},
                           {"label": "First sounds", "members": ["Rowan/g7", "Mabel/g1"], "groups": [{"label": "Gates", "members": ["Fern/g2"]}]}],
                  "left_out": [{"key": "Rowan/g6", "reason": "It stands apart"}]}
        parsed = themes_ai.parse_gets(json.dumps(answer), units, ups)
        check("86: its parser takes a sub-theme under any GET, with its PET or apart from it, at any depth",
              [g["members"] for g in parsed["groups"]] == [["Wren/g1", "Wren/g3", "Rowan/g1"], ["Rowan/g7", "Mabel/g1"]]
              and parsed["groups"][1]["groups"] == [{"label": "Gates", "members": ["Fern/g2"]}]
              and parsed["placed"] == 6 and parsed["subs"] == 3 and parsed["left"] == len(units) - 6 and parsed["repeated"] == 0
              and parsed["left_out"] == [{"key": "Rowan/g6", "reason": "It stands apart"}], str(parsed)[:300])
        cards_ai, thrown = gets_mod.ai_cards(data, study, parsed)
        laid = themes_ai.gets_ids(themes_ai.lay_out(parsed["groups"], cards_ai, thrown, size=gets_mod.card_height))
        under = {m for g in laid["groups"] for m in g["members"]}
        check("86: the new AI board holds a card for every PET and sub-theme, each it left out in Not placed",
              {c["key"] for c in cards_ai} == set(units) and thrown == [] and set(laid["cards"]) == set(units)
              and "Rowan/g6" not in under and "Mabel/g7" not in under and "Wren/g3" in under)
        check("86: its note counts the sub-themes placed apart from the PETs",
              "2 GETs, 3 PETs and 3 sub-themes placed, " in themes_ai.gets_note("Haiku 4.5", "every participant's PETs", "", parsed, cap=5)
              and "1 PET placed, 0 not placed." in themes_ai.gets_note("Haiku 4.5", "x", "", {"groups": [{}], "placed": 1, "left": 0}))
        skipped = themes_ai.gets_group_user(study, None, "", frozenset(), frozenset({"Wren/g1"}))
        sunits, _ups = themes_ai.gets_units(study, frozenset({"Wren/g1"}))
        check("86: from a board, a PET in its bin is not sent, and its sub-themes still are, items of their own",
              "PET Wren/g1:" not in skipped and "Sub-theme Wren/g3: Early light in the hall" in skipped
              and "Wren/g1" not in sunits and "Wren/g3" in sunits and "Wren/g4" not in sunits)

        # \u2500\u2500 G. the count and the table, a PET under one GET and its sub-theme under another
        split = {"id": "bx", "name": "Split", "cards": {k: {"x": 0, "y": 0} for k in ("Wren/g1", "Wren/g3", "Rowan/g1", "Rowan/g6")},
                 "groups": [{"id": "G1", "label": "Mornings", "members": ["Wren/g1", "Rowan/g1", "Rowan/g6"], "x": 0, "y": -40},
                            {"id": "G2", "label": "Light", "members": ["Wren/g3"], "x": 600, "y": -40}],
                 "discarded": [], "picks": {}, "rows": {}}
        split["cards"]["Wren/g3"] = {"x": 600, "y": 0}
        split["cards"]["Rowan/g6"] = {"x": 300, "y": 0}
        inside = ["Fern", "Mabel", "Rowan", "Wren"]
        check("86: a PET under one GET and its sub-theme under another count the case once under each, a PET with its sub-theme once",
              gets_mod.count(split, "G1", set(inside)) == 2 and gets_mod.count(split, "G2", set(inside)) == 1)
        tab = {g["id"]: {r["case"]: r for r in g["rows"]} for g in gets_mod.table(data, split, inside)}
        wren_rec = data["cases"]["Wren"]
        check("86: the GET table lists a sub-theme's row as it lists a dragged one",
              tab["G2"]["Wren"]["items"] == [gets_mod.item_of(wren_rec, "Wren/g3", {})] and tab["G2"]["Wren"]["counted"]
              and tab["G2"]["Wren"]["items"][0]["kind"] == "sub" and tab["G2"]["Wren"]["items"][0]["statements"] == 3
              and [it["kind"] for it in tab["G1"]["Rowan"]["items"]] == ["pet", "sub"] and not tab["G2"]["Rowan"]["counted"])
        outline = gets_mod.ai_outline(data, split, inside, 3)
        start = gets_mod.revise_start(split, data, inside)
        board_text = "\n".join(themes_ai.gets_board_parts(outline))
        target = themes_ai.gets_names_target(outline, "G2")
        check("86: Review, Revise and AI suggest GET titles read a sub-theme's card as a dragged one",
              outline["themes"][1]["cards"][0]["kind"] == "sub" and outline["themes"][1]["cards"][0]["title"] == "Early light in the hall"
              and "Wren/g3" in start["items"] and "- Sub-theme Wren/g3 (Wren): Early light in the hall" in board_text
              and "Sub-theme Wren/g3 (Wren): Early light in the hall" in themes_ai.gets_names_user(target), board_text[:300])

        # \u2500\u2500 H. the page: the menu, the drag's card, the AI's count and one step of undo, in node
        panel = {c["case"]: c for c in idiograph_routes.api_gets({"workbook": any_book})["cases"]}
        node = shutil.which("node")
        if not node:
            skip("86: the page's parts in node", "no node on this machine")
        else:
            script = scratch / "gets-subs.js"
            script.write_text(support.i18n_js() + js + "\nconst ENTRY = " + json.dumps(panel["Wren"]) + ";\nconst SERVED = " + json.dumps(cards["Wren/g3"])
                              + ";\nconst ADDED = " + json.dumps(list(added.values())[:2]) + ";\n" + r"""
const els = {};
function $(id) { return els[id] || (els[id] = { id, hidden: true, textContent: '', title: '' }); }
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const RESTART_LINE = 'Restart the server to finish this update.';
const needsRestart = () => false;
""" + next(l for l in support.text("family/static/shell.js").splitlines() if l.startswith("const refusedAs = ")) + r"""
const said = [];
function say(line) { said.push(line); }
let reply = null;
let asked = null;
async function api(route, body) { asked = [route, body]; if (reply instanceof Error) throw reply; return reply; }
thFlush = async () => {};
thVmenu = () => {};
thDone = (before, what) => { thStep(before, what); };
const out = {};
const drag = gtCardFrom(ENTRY, 'sub', 'g3');
out.drag = [drag.key, drag.kind, drag.text, drag.statements, gtKicker(drag), gtKicker(SERVED)];
out.grouping = [gtGrouping({ pets: 6, subs: 3 }), gtGrouping({ pets: 1, subs: 1 }), gtGrouping({ pets: 2, subs: 0 })];
TH.gets = { cases: [ENTRY] };
out.count = gtAiCount(true);
(async () => {
  TH.mode = 'gets'; TH.live = true; TH.busy = false; TH.dirty = false; TH.path = 'Wren.xlsx';
  TH.meta = { id: 'b3', name: 'Board 3' };
  TH.v = { cards: { 'Wren/g1': { key: 'Wren/g1', kind: 'pet', x: 0, y: 0 } }, groups: [], discarded: [], picks: {}, stickies: [], rows: {} };
  TH.removed = new Set(); TH.z = ['Wren/g1']; TH.undo = []; TH.redo = [];
  reply = { op: 'subs', board: 'b3', added: ADDED };
  await gtAddSubs();
  const step = TH.undo[0] || {};
  out.add = { asked, n: TH.undo.length, what: step.what, before: Object.keys((step.before || {}).cards || {}),
    after: Object.keys((step.after || {}).cards || {}), removed: (step.before || {}).removed, z: TH.z, said: said.slice() };
  reply = new Error('Every sub-theme has a card on this board already, so nothing was added.');
  said.length = 0; TH.undo = [];
  await gtAddSubs();
  out.none = [said.slice(), TH.undo.length];
  reply = Object.assign(new Error('That is not something a board can do, so nothing was changed.'), { code: 'unknown_op' });
  said.length = 0;
  await gtAddSubs();
  out.old = said.slice();
  console.log(JSON.stringify(out));
})();
""", encoding="utf-8")
            run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
            out_node = support.plain(json.loads(run.stdout)) if run.returncode == 0 and run.stdout.strip() else {}
            check("86: in node, a sub-theme's card is the one the Cases panel's drag makes, its kicker Sub-theme and the case",
                  out_node.get("drag") == ["Wren/g3", "sub", "Early light in the hall", 3, "Sub-theme \u00b7 Wren", "Sub-theme \u00b7 Wren"],
                  run.stderr.strip()[:300] or str(out_node.get("drag")))
            check("86, 207: in node, New AI board counts the PETs and the sub-themes it sends, a group riding inside its sub-theme, and says both while it groups",
                  out_node.get("count") == {"pets": 2, "subs": 2}
                  and out_node.get("grouping") == ["Grouping 6 PETs and 3 sub-themes", "Grouping one PET and one sub-theme", "Grouping 2 PETs"],
                  str(out_node.get("count")) + str(out_node.get("grouping")))
            keys2 = [c["key"] for c in list(added.values())[:2]]
            got = out_node.get("add") or {}
            check("86: in node, Add every sub-theme asks the server and lands its cards as one step of undo",
                  got.get("asked") == ["/api/gets-boards", {"workbook": "Wren.xlsx", "op": "subs", "id": "b3"}]
                  and got.get("n") == 1 and got.get("what") == "Added 2 sub-themes" and got.get("before") == ["Wren/g1"]
                  and got.get("after") == ["Wren/g1"] + keys2 and set(keys2) <= set(got.get("removed") or [])
                  and got.get("z") == ["Wren/g1"] + keys2 and got.get("said") == ["Added 2 sub-themes."], str(got))
            check("86: in node, none to add is the server's one line and no step, and a server from before asks for a restart",
                  out_node.get("none") == [["Every sub-theme has a card on this board already, so nothing was added."], 0]
                  and out_node.get("old") == ["Restart the server to finish this update."], str(out_node.get("none")) + str(out_node.get("old")))
        menu = fn(js, "thVmenuDraw")
        button = next((ln for ln in menu.splitlines() if 'data-vop="subs"' in ln), "")
        check("86: Add every sub-theme sits in the GETs board menu alone, not a thematic analysis project's, a plain label without the sparkles, routed to its act",
              "TH.mode === 'gets' && !thTa() ?" in button and "${esc(t('themes.board.subs'))}</button>" in button and "SPARK" not in button
              and "else if (what === 'subs') gtAddSubs();" in js and "'/api/gets-boards', { workbook: TH.path, op: 'subs', id }" in fn(js, "gtAddSubs")
              and fn(js, "gtAddSubs").count("thDone(") == 1 and "SPARK" not in fn(js, "gtAddSubs"))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = saved
