from __future__ import annotations

import json
import re
import shutil

import openpyxl

import ai_suggest as ai_mod
import workbook as wb_mod

from . import support
from .support import DEMO_QUESTION, DEMO_SHEET, check, demo_copy, skip
import idiograph_routes


def test_gets_ai(scratch):
    print("\n83. AI help on GETs: New AI board from every participant's PETs or a board with the rows' key quotes, "
          "AI suggest GET titles, Review and Revise on a GETs board, the GETs section of the guidance, "
          "the bin his act (182), and names that are just names (184)")
    import subprocess
    import cli
    import gets as gets_mod
    import server as server_mod
    import themes as themes_mod
    import themes_ai

    js = support.text("apps/idiograph/static/themes.js")
    guidance = support.source("apps/idiograph/pet_guidance.md").read_text(encoding="utf-8")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""

    # ── A. the GETs section of the guidance, numbered as its sections are, and the PETs prompts as they were
    rules5, questions6 = themes_ai.guidance_items(5), themes_ai.guidance_items(6)
    section5 = guidance.split("## 5. Group experiential themes", 1)[1].split("\n## ", 1)[0] if "## 5. Group experiential themes" in guidance else ""
    section6 = guidance.split("## 6. Questions a reviewer asks of a GETs board", 1)[1].split("\n## ", 1)[0] if "## 6." in guidance else ""
    check("83: the guidance gains section 5, what a GET is and its rules, and section 6, the questions of a GETs board, with Sources after them",
          section5 and section6 and [n for n, _ in rules5] == list(range(1, 10)) and [n for n, _ in questions6] == list(range(1, 16))
          and guidance.index("## 4. Questions") < guidance.index("## 5. Group") < guidance.index("## 6. Questions") < guidance.index("## 7. Sources")
          and (themes_ai.GETS, themes_ai.GETS_QUESTIONS) == (5, 6)
          and (themes_ai.WHAT_A_THEME, themes_ai.RULES, themes_ai.QUESTIONS) == (1, 3, 4), str(len(rules5)))
    stripped = scratch / "guidance-pets-only.md"
    stripped.write_text(guidance.split("## 5. Group experiential themes", 1)[0] + "## 7. Sources\n", encoding="utf-8")
    held = themes_ai.GUIDANCE

    def pets_prompts():
        return (themes_ai.group_system(DEMO_QUESTION, 5), themes_ai.names_system(DEMO_QUESTION),
                themes_ai.review_system(DEMO_QUESTION, notes=True, asked=True), themes_ai.reply_system(DEMO_QUESTION, notes=True),
                themes_ai.revise_system(DEMO_QUESTION), themes_ai.picks_system(DEMO_QUESTION))
    now = pets_prompts()
    try:
        themes_ai.GUIDANCE = stripped
        without = pets_prompts()
    finally:
        themes_ai.GUIDANCE = held
    check("83: the PETs prompts carry exactly the sections they carried, the same with or without sections 5 and 6",
          now == without and not any(text in p for p in now for _, text in rules5 + questions6))

    # ── B. the fixture: three invented cases from the demo, one with no PETs yet
    root = scratch / "gets-ai-root"
    shutil.rmtree(root, ignore_errors=True)
    books = {name: demo_copy(root, name, f"{name} - EN & ES.xlsx") for name in ("Wren", "Ash", "Moss")}
    (root / "idiograph-project.json").write_text(json.dumps({"name": "Scratch", "research_question": DEMO_QUESTION}),
                                                 encoding="utf-8")
    read = themes_mod.read_cards(books["Wren"])
    keys = [c["key"] for c in read["cards"]]
    words = {c["key"]: c["text"] for c in read["cards"]}
    for name in ("Wren", "Ash"):
        book = openpyxl.load_workbook(books[name], rich_text=True)
        ws = book[DEMO_SHEET]
        cols = wb_mod.detect_columns(ws)
        row = read["cards"][0]["row"]
        ws.cell(row, cols["kq"]).value = '"the stair at six"\n\n"she is there first"' if name == "Wren" else '"a lead by the door"'
        book.save(books[name])
        book.close()
    first_row = f"{read['cards'][0]['sheet']}:{read['cards'][0]['row']}"

    def board(vid, name, groups):
        b = themes_mod.blank_version(themes_mod.read_cards(books["Wren"])["cards"])
        b.update(id=vid, name=name, groups=groups)
        return b

    wren_pets = [{"id": "g1", "label": "Mornings that start at the stair", "note": "An invented note on mornings.",
                  "members": keys[0:2] + ["g3"], "x": 0, "y": 0},
                 {"id": "g2", "label": "Walks that close the day", "members": keys[4:6], "x": 0, "y": 400},
                 {"id": "g3", "label": "Early light in the hall", "members": keys[2:4], "x": 0, "y": 200}]
    ash_pets = [{"id": "g1", "label": "A lead by the door", "members": keys[0:3], "x": 0, "y": 0},
                {"id": "g2", "label": "Evenings kept for two", "members": keys[6:8], "x": 0, "y": 300}]
    for name, groups in (("Wren", wren_pets), ("Ash", ash_pets)):
        themes_mod.write(books[name], {"schema": 2, "case": name, "workbook": books[name].name, "current": "v1",
                                       "chosen": "v1", "boards": [board("v1", "Board 1", groups)],
                                       "complete": {"at": "2026-10-05T10:00:00+01:00", "board": "v1", "name": "Board 1"}})
    saved = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, ai_mod.find_key, ai_mod.http_call)
    config_path = scratch / "gets-ai" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    settings = lambda **extra: config_path.write_text(json.dumps(
        {"ai_suggest": True, "ai_provider": "anthropic", "model": "claude-haiku-4-5",
         "pets_provider": "anthropic", "pets_model": "claude-opus-5-5", **extra}), encoding="utf-8")
    settings()
    sent, mode = [], {"group": "good", "picks": "good", "names": "good", "review": "good", "revise": "good"}
    book_sha = lambda: {n: p.read_bytes() for n, p in books.items()}
    themes_sha = lambda: {n: themes_mod.themes_path(p).read_bytes() for n, p in books.items() if themes_mod.themes_path(p).exists()}
    W, A = "Wren", "Ash"
    answers = {
        "good": {"gets": [{"label": "Mornings kept round the dog", "members": [f"{W}/g1", f"{A}/g1"]},
                          {"label": "  ", "members": [f"{W}/g2", f"{A}/g2"],
                           "groups": [{"label": "Light in the hall", "members": [f"{W}/g3"]}]}],
                 "left_out": [{"key": f"{A}/g9", "reason": "not in the study"}], "reason": ""},
        "left": {"gets": [{"label": "Mornings kept round the dog", "members": [f"{W}/g1", f"{A}/g1", "Nobody/g1"]}],
                 "left_out": [{"key": f"{W}/g2", "reason": "It stands apart from every other PET"}]},
    }

    def wire(method, url, headers, payload, timeout):
        system, user = payload["system"], payload["messages"][-1]["content"]
        sent.append({"system": system, "user": user, "model": payload["model"]})
        if themes_ai.GETS_PICKS_TASK in system:
            if mode["picks"] == "fail":
                return 529, '{"error": "overloaded"}'
            rows = re.findall(r"^Row (\S+/\S+),", user, re.M)
            qkeys = re.findall(r"^- (\S+:\d+:\d+) ", user, re.M)
            text = json.dumps({"picks": [{"id": rows[0], "quotes": [qkeys[0]]}, {"id": rows[0], "quotes": ["Nowhere:1:0"]},
                                         {"id": "G9/Nobody", "quotes": [qkeys[0]]}]}) if rows and qkeys else '{"picks": []}'
        elif "Offer three titles for the GET" in system:
            text = json.dumps({"names": ["Mornings that turn round the dog", "A day that starts at the stair",
                                         "Mornings that turn round the dog", "Light first, then the walk"]})
        elif themes_ai.GETS_REVIEW_TASK in system:
            text = json.dumps({"items": [{"about": "G1", "question": "Does the GET 'Mornings kept round the dog' show where the participants part?",
                                          "rule": "1", "why": "Both PETs under it read alike."},
                                         {"about": "Nowhere", "question": "Is the board ready?", "rule": "99", "why": "x"}]})
        elif themes_ai.GETS_REPLY_TASK in system:
            text = "The two PETs share the stair, and the board shows Ash's evenings apart from it."
        elif themes_ai.GETS_REVISE_TASK in system:
            rows = re.findall(r"quote (\S+/\S+:\d+:\d+)", user)
            text = json.dumps({"operations": [
                {"op": "retitle", "label": "G1", "title": "Mornings that turn round the dog"},
                {"op": "move", "items": [f"{A}/g2"], "to": None},
                {"op": "make", "ref": "new1", "title": "Evenings apart", "inside": None, "members": [f"{A}/g2"]},
                {"op": "pick", "label": "G1", "quotes": rows[:1]},
                {"op": "discard", "items": [f"{W}/g2"]},
                {"op": "move", "items": [f"{W}/pn/1"], "to": "G1"}], "said": "Retitled the first GET."}) if mode["revise"] == "good" \
                else json.dumps({"operations": [], "said": "Nothing to change."})
        else:
            text = json.dumps(answers[mode["group"]])
        return 200, json.dumps({"content": [{"type": "text", "text": text}], "stop_reason": "end_turn"})

    gfile = gets_mod.gets_path(root)
    gdata = lambda: json.loads(gfile.read_text(encoding="utf-8"))
    any_book = str(books["Wren"])
    try:
        server_mod.CONFIG_PATH = config_path
        server_mod.ROOT_OVERRIDE = str(root)
        server_mod.STATE_MEMORY = {"recent": []}
        ai_mod.find_key = lambda *a, **kw: "k-test"
        ai_mod.http_call = wire
        before_books, before_themes = book_sha(), themes_sha()

        # ── C. the switch off, and what the screen is told
        settings(ai_suggest=False)
        off = [idiograph_routes.api_gets_ai({"workbook": any_book, "op": op}) for op in ("group", "names", "review", "reply", "revise", "room")]
        opened = idiograph_routes.api_gets({"workbook": any_book})
        check("83: with the switch off every GETs AI op is one line, nothing sent and nothing written",
              off == [{"error": themes_ai.OFF}] * 6 and not sent and not gfile.exists() and opened["ai"]["on"] is False)
        settings()
        opened = idiograph_routes.api_gets({"workbook": any_book})
        check("83: /api/gets says the GETs AI is there, the switch, the PETs model, the GETs limit, and the Guidance tab's GETs sections",
              opened["gets_ai"] is True and opened["ai"]["on"] is True and opened["ai"]["model_name"] == "Opus 5.5"
              and opened["ai"]["cap"] == 5 and opened["from_all"] is True and opened["revisable"] is True
              and [g["heading"] for g in opened["guidance"]] == ["Group experiential themes", "Questions a reviewer asks of a GETs board"]
              and opened["guidance"][0]["lines"][0].startswith("A group experiential theme (GET) is a pattern")
              and len(opened["guidance"][0]["lines"]) == 10 and len(opened["guidance"][1]["lines"]) == 15 and not gfile.exists())

        # his own first board on GETs, with a participant note, a sticky note and a row note, none of which may go
        idiograph_routes.api_gets_save({"workbook": any_book, "version": dict(
            {k: x for k, x in opened["version"].items() if k != "v"}, cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in opened["cards"]}
            | {f"{W}/pn/1": {"x": 900, "y": 900, "text": "An invented participant note, private"}},
            groups=[{"id": "G1", "label": "His mornings", "note": "His invented note on the GET",
                     "members": [f"{W}/g1", f"{W}/pn/1"], "x": 0, "y": 0}],
            discarded=[f"{A}/g2"], picks={}, notes=[{"id": "n1", "text": "An invented sticky note, private", "colour": "yellow", "x": 50, "y": 50}],
            rows={"G1": {W: {"quote": "", "note": "An invented row note, private"}}})})
        mine = next(b for b in gdata()["boards"] if b["id"] == "b1")

        # ── D. New AI board from every participant's PETs
        sent.clear()
        made = idiograph_routes.api_gets_ai({"workbook": any_book, "op": "group", "version": "b1", "from": "all", "hint": "  fewer  GETs ", "cap": 3})
        data = gdata()
        new = data["boards"][-1]
        first, second = (sent + [{}, {}])[:2]
        user, system = first.get("user", ""), first.get("system", "")
        check("83: from every participant's PETs, every case of the study named by its pseudonym, each PET with its note, sub-themes and statements",
              all(w in user for w in (f"- PET {W}/g1: Mornings that start at the stair", f"{themes_ai.NOTE_NAMES} An invented note on mornings.",
                                       f"  - Sub-theme {W}/g3: Early light in the hall", f"- PET {A}/g1: A lead by the door",
                                       "Moss: no PETs yet.", f"({DEMO_SHEET}, ", words[keys[0]]))
              and user.index("Ash,") < user.index("Moss:") < user.index("Wren,") and "His GETs on the board" not in user, user[:300])
        check("83: the prompt carries the research question, the GETs section of the guidance, his minimum, his limit, One GET per PET and the hint",
              DEMO_QUESTION in system and all(f"{n}. {text}" in system for n, text in rules5)
              and not any(f"{n}. {text}" in system for n, text in themes_ai.guidance_items(3))
              and "His minimum is 3 of the 3 participants" in system and "His limit is 3 GETs. Make between 2 and 3 GETs." in system
              and "Place each PET and each sub-theme under one GET, or one of that GET's own sub-themes, at most." in system
              and "His hint for this arrangement, which comes before the general guidance: fewer GETs" in user
              and '"left_out": [{"key": "<PET or sub-theme key>", "reason": "..."}]' in system
              and "Nothing you answer puts a PET or a sub-theme in the bin." in system)
        everything = json.dumps(sent)
        check("83: participant notes, sticky notes and row notes never go to a model",
              "participant note, private" not in everything and "sticky note, private" not in everything
              and "row note, private" not in everything and "His invented note on the GET" not in everything)
        check("83: a new board made current, Board 2 as New board names one, the board it came from untouched, no workbook or themes file written",
              new["name"] == "Board 2" and data["current"] == new["id"] == made["current"] and new["id"] != "b1"
              and next(b for b in data["boards"] if b["id"] == "b1") == mine
              and book_sha() == before_books and themes_sha() == before_themes)
        groups = {g["id"]: g for g in new["groups"]}
        check("83: laid out as GETs, G1 on, a sub-theme inside its GET, a blank title Untitled, every participant's PETs on the board",
              sorted(groups) == ["G1", "G2", "G3"] and groups["G1"]["label"] == "Mornings kept round the dog"
              and groups["G2"]["label"] == "Untitled" and "G3" in groups["G2"]["members"]
              and groups["G3"]["members"] == [f"{W}/g3"] and set(groups["G1"]["members"]) == {f"{W}/g1", f"{A}/g1"}
              and {f"{W}/g1", f"{W}/g2", f"{A}/g1", f"{A}/g2", f"{W}/g3"} <= set(new["cards"]) and new["discarded"] == [], str(groups)[:200])
        drawn = themes_mod.layout_boxes(gets_mod.named(gets_mod.normal(new, data), data), gets_mod.card_height)
        boxes = list(drawn["cards"].items()) + list(drawn["labels"].items())
        parents = themes_mod.parents_of(new["groups"])
        inside = lambda a, b: a in themes_mod.cards_under({g["id"]: g for g in new["groups"]}, b) or parents.get(a) == b
        overlaps = [(a, b) for i, (a, ba) in enumerate(boxes) for b, bb in boxes[i + 1:]
                    if themes_mod.clash(ba, bb) and not inside(a, b) and not inside(b, a)]
        check("83: nothing on the new board lies over anything else", not overlaps, str(overlaps[:3]))
        check("83: the note and the canvas's line say what came back, from every participant's PETs, the hint and the limit",
              new["note"].startswith("Proposed by Opus 5.5 from every participant's PETs on ")
              and ", with the hint 'fewer GETs', up to 3 GETs. 2 GETs, 4 PETs and 1 sub-theme placed, 0 not placed." in new["note"]
              and made["made"]["from"] == "every participant's PETs" and made["made"]["source"] == "all"
              and made["made"]["themes"] == 2 and made["made"]["left"] == 0 and made["made"]["cap"] == 3, new["note"])
        check("83: 184, the board keeps who made it and from what, with the hash of the board as made, and the menu says with AI",
              new["made"]["by"] == "ai" and new["made"]["model"] == "Opus 5.5" and new["made"]["from"] == "every participant's PETs"
              and len(new["made"].get("hash") or "") == 64 and "edited" not in new["made"]
              and made["version"]["with_ai"] == {"by": "ai", "said": "Opus 5.5, from every participant's PETs", "edited": False}
              and "with_ai" not in next(v for v in made["versions"] if v["id"] == "b1"))

        # ── E. the key quote of each row, picked by a second call
        check("83: one second call for the rows, a GET and a case each, from the quotes of that case's items under the GET",
              len(sent) == 2 and themes_ai.GETS_PICKS_TASK in second["system"] and f"Row G1/{W}, Wren:" in second["user"]
              and f'- {first_row}:0 "the stair at six"' in second["user"] and f"Row G1/{A}, Ash:" in second["user"]
              and second["model"] == "claude-opus-5-5")
        check("83: the picks land in rows[G][case].quote, a key not the row's dropped, a row it skipped keeping the table's default",
              new["rows"] == {"G1": {A: {"quote": f"{first_row}:0", "note": ""}}} or new["rows"] == {"G1": {W: {"quote": f"{first_row}:0", "note": ""}}},
              str(new.get("rows")))
        check("83: the note counts the rows picked", "Quotes picked for 1 of " in new["note"] and made["made"]["picked"] == 1)
        mode["picks"] = "fail"
        failed = idiograph_routes.api_gets_ai({"workbook": any_book, "op": "group", "version": "b1", "from": "all"})
        check("83: when the rows' call fails the board is still made, every row keeping its default",
              gdata()["boards"][-1]["rows"] == {} and failed["made"]["unpicked"] is True and gdata()["boards"][-1]["name"] == "Board 3")
        mode["picks"] = "good"

        # ── F. from a board, and 182 on GETs: a PET left out stays in Not placed with its reason
        sent.clear()
        mode["group"] = "left"
        made = idiograph_routes.api_gets_ai({"workbook": any_book, "op": "group", "version": "b1", "from": "board"})
        new = gdata()["boards"][-1]
        user = sent[0]["user"]
        check("83: from a board, his GETs and placements go as the start, a PET in its bin not sent, his note on the GET his to weigh",
              "His GETs on the board now, each with the PETs and sub-themes under it." in user
              and f"- G1 His mornings: {W}/g1" in user and f"PET {A}/g2" not in user
              and themes_ai.NOTES_GETS in user and made["made"]["from"] == "Board 1" and made["made"]["source"] == "board")
        check("83, 193: 182 on GETs, a PET left out stays in Not placed with its reason, a sub-theme not named beside it, the bin holding only his own",
              new["discarded"] == [f"{A}/g2"] and not any(f"{W}/g2" in g["members"] for g in new["groups"])
              and f"{W}/g3" in new["cards"] and not any(f"{W}/g3" in g["members"] for g in new["groups"])
              and new["ai"] == {"discarded": {f"{W}/g2": "It stands apart from every other PET"}}
              and "2 not placed." in new["note"] and made["made"]["left"] == 2)
        shown = idiograph_routes.api_gets({"workbook": any_book})
        check("83: the screen gets the reason under the card, and the participant note stays on his board alone",
              shown["discard_reasons"] == {f"{W}/g2": "It stands apart from every other PET"}
              and not any(k.startswith(f"{W}/pn/") for k in new["cards"]))
        mode["group"] = "good"

        # ── G. the parser on its own
        units, ups = themes_ai.gets_units(gets_mod.ai_study(*gets_mod.assemble(root, idiograph_routes.gets_books(root), themes_mod.now_iso())[:2]))
        parse = lambda answer, **kw: themes_ai.parse_gets(json.dumps(answer), units, ups, **kw)
        good = parse({"gets": [{"label": "A", "members": [f"{W}/g1", "Nobody/g9", f"{A}/g1"]},
                               {"label": "B", "members": [f"{W}/g1", f"{W}/g3", f"{A}/g2"]}],
                      "left_out": [{"key": f"{W}/g1", "reason": "placed"}, {"key": f"{W}/g2", "reason": "apart; a dash \u2014 here"}]})
        check("83: read strictly, an unknown key dropped, a PET twice keeping its first place, a placed one never left out",
              [g["members"] for g in good["groups"]] == [[f"{W}/g1", f"{A}/g1"], [f"{W}/g3", f"{A}/g2"]]
              and good["unknown"] == 1 and good["repeated"] == 2 and good["placed"] == 4 and good["left"] == 1
              and good["left_out"] == [{"key": f"{W}/g2", "reason": "apart, a dash, here"}], str(good)[:300])
        many = parse({"gets": [{"label": "A", "members": [f"{W}/g1"]}, {"label": "B", "members": [f"{W}/g1", f"{W}/g1"]}]}, one_per_pet=False)
        check("83: with One GET per PET off a PET under a second GET takes a second card there, and twice under one GET keeps one",
              [g["members"] for g in many["groups"]] == [[f"{W}/g1"], [f"{W}/g1/2"]] and many["repeated"] == 1)
        same = parse({"gets": [{"label": "A", "members": [f"{W}/g1"], "groups": [{"label": "S", "members": [f"{W}/g3"]}]},
                               {"label": "B", "members": [f"{A}/g1"]}]})
        check("83, 193: a sub-theme is a card of its own, standing under the GET its PET sits under, and apart under another GET too",
              [g["members"] for g in same["groups"]] == [[f"{W}/g1"], [f"{A}/g1"]]
              and same["groups"][0]["groups"] == [{"label": "S", "members": [f"{W}/g3"]}] and same["subs"] == 1
              and parse({"gets": [{"label": "A", "members": [f"{W}/g1"]}, {"label": "B", "members": [f"{W}/g3"]}]})["groups"][1]["members"] == [f"{W}/g3"])
        check("83: a blank title Untitled, past the limit and one refused whole, nothing placed or no JSON one line, cut off says so",
              parse({"gets": [{"label": "", "members": [f"{W}/g1"]}]})["groups"][0]["label"] == "Untitled"
              and parse({"gets": [{"label": str(i), "members": [u]} for i, u in enumerate(units[:5])]}, cap=3)
              == {"error": "The answer proposed 5 GETs, more than one past the limit of 3, so no board was made."}
              and "error" not in parse({"gets": [{"label": str(i), "members": [u]} for i, u in enumerate(units[:4])]}, cap=3)
              and parse({"gets": [{"label": "A", "members": ["Nobody/g1"]}]}) == {"error": themes_ai.PLACED_NO_PETS}
              and themes_ai.parse_gets("no json", units) == {"error": themes_ai.NOT_JSON}
              and themes_ai.parse_gets('{"gets": [{"label"', units, truncated=True) == {"error": ai_mod.TOO_LONG})

        # ── H. the cut for room: statements' words go before any title
        study = gets_mod.ai_study(*gets_mod.assemble(root, idiograph_routes.gets_books(root), themes_mod.now_iso())[:2])
        full = themes_ai.gets_group_user(study, None)
        sys_ = themes_ai.gets_group_system(DEMO_QUESTION, 5, 3, 3)
        cut_user, bare = themes_ai.cut_words(sys_, lambda b: themes_ai.gets_group_user(study, None, "", b),
                                             themes_ai.cut_order(study), len(sys_) + len(full) - 200)
        titles = [p["title"] for c in study for p in c["pets"]]
        check("83: past the room the words of the lowest statements go first, every title stays, and the prompt says so",
              bare and len(sys_) + len(cut_user) <= len(sys_) + len(full) - 200 and all(t in cut_user for t in titles)
              and "left out here for room" in cut_user and "left out for room" in cut_user
              and themes_ai.gets_cut_line(3) == "To fit what the model can take, Idiograph left out the words of three statements, the lowest in their PETs.")
        order = [k for k, _ in themes_ai.cut_order(study)]
        every_pet = lambda p: [p] + [x for sub in p.get("subs") or [] for x in every_pet(sub)]
        lasts = {q["statements"][-1]["key"] for c in study for p in c["pets"] for q in every_pet(p) if q["statements"]}
        check("83: the cut takes the lowest statement of every PET before the next lowest of any", set(order[:len(lasts)]) == lasts)
        calls = len(sent)
        room = idiograph_routes.api_gets_ai({"workbook": any_book, "op": "room", "version": "b1"})
        check("83: the card's line learns the cut without a call, none on a provider's room for so small a study",
              room["room"] == {"all": 0, "board": 0} and len(sent) == calls, str(room))

        # ── I. AI suggest GET titles
        sent.clear()
        board_id = gdata()["boards"][1]["id"]
        named = idiograph_routes.api_gets_ai({"workbook": any_book, "op": "names", "version": board_id, "group": "G1"})
        user, system = sent[0]["user"], sent[0]["system"]
        check("83: three titles for a GET from what sits under it across the cases, the cases named, its count against the minimum",
              named["names"] == ["Mornings that turn round the dog", "A day that starts at the stair", "Light first, then the walk"]
              and "GET: Mornings kept round the dog" in user and f"- PET {W}/g1 (Wren): Mornings that start at the stair" in user
              and f"- PET {A}/g1 (Ash): A lead by the door" in user and "It holds material from 2 of the 3 participants, and his minimum is 3." in user
              and "Nothing under it from: Moss." in user and "- Untitled" not in user and named["model_name"] == "Opus 5.5")
        check("83: the other GETs' titles go so the three stay distinct, with the title rules of section 5 and no other",
              "The other GETs on the board, so the titles sit beside them:\n- Light in the hall" in user
              and all(f"{n}. {t}" in system for n, t in rules5 if n in (5, 6, 7, 8))
              and not any(f"{n}. {t}" in system for n, t in rules5 if n not in (5, 6, 7, 8))
              and "Offer three titles for the GET he has gathered" in system and "close to the participants' own words" in system)
        check("83: a GET no longer on the board, or with nothing under it, asks nothing",
              idiograph_routes.api_gets_ai({"workbook": any_book, "op": "names", "version": board_id, "group": "G9"}) == {"error": themes_ai.NO_SUCH_GET}
              and len(sent) == 1)

        # ── J. Review and Reply on a GETs board
        sent.clear()
        reviewed = idiograph_routes.api_gets_ai({"workbook": any_book, "op": "review", "version": board_id})
        user, system = sent[0]["user"], sent[0]["system"]
        check("83: a review asks up to three impersonal questions from the GETs section's questions, the board GET by GET",
              all(f"{n}. {t}" in system for n, t in questions6) and all(f"{n}. {t}" in system for n, t in rules5)
              and "Never write in the first person" in system and "Ask, never rule" in system
              and "GET G1: Mornings kept round the dog (2 of 3 participants, under his minimum)" in user
              and "Nothing under it from: Moss." in user and "Review this board." in user
              and reviewed["review"]["items"] == [{"about": "G1", "question": "Does the GET 'Mornings kept round the dog' show where the participants part?",
                                                   "rule": "1", "why": "Both PETs under it read alike.", "state": "open"},
                                                  {"about": None, "question": "Is the board ready?", "rule": "", "why": "x", "state": "open"}]
              and reviewed["asked"] == 0 and reviewed["model_name"] == "Opus 5.5", str(reviewed.get("review"))[:200])
        target = gdata()["boards"][1]
        target["review"] = reviewed["review"]
        idiograph_routes.api_gets_save({"workbook": any_book, "version": dict(target, cards={k: dict(c, text=c.get("text") or "") for k, c in target["cards"].items()})})
        check("83: the page keeps the round with the board, and the GETs file keeps it",
              gdata()["boards"][1].get("review", {}).get("items", [{}])[0].get("about") == "G1")
        sent.clear()
        replied = idiograph_routes.api_gets_ai({"workbook": any_book, "op": "reply", "version": board_id, "round": 0, "item": 0,
                                          "question": reviewed["review"]["items"][0]["question"], "text": "I think the stair holds both."})
        check("83: Reply sends the board, the question and his words, and answers in the same voice",
              replied["reply"]["text"].startswith("The two PETs share the stair") and replied["reply"]["by"] == "ai"
              and "He writes now: I think the stair holds both." in sent[0]["user"] and themes_ai.GETS_REPLY_TASK in sent[0]["system"])

        # ── K. Revise on a GETs board
        sent.clear()
        before = gdata()["boards"][1]
        revised = idiograph_routes.api_gets_ai({"workbook": any_book, "op": "revise", "version": board_id, "text": "Retitle the first GET"})
        after = gdata()["boards"][1]
        r = revised.get("revised") or {}
        check("83: revise runs the operations over the GETs board, a new GET numbered G on, the rows' key quote picked",
              [g["label"] for g in r.get("groups", []) if g["id"] == "G1"] == ["Mornings that turn round the dog"]
              and any(g["id"] == "G4" and g["label"] == "Evenings apart" and g["members"] == [f"{A}/g2"] for g in r.get("groups", []))
              and r.get("made") == ["G4"] and r.get("picks") == {} and list((r.get("rows") or {}).get("G1", {})) != [], str(r)[:300])
        check("83: never the bin and never a participant note, each refused and the rest standing",
              len(revised["refused"]) == 2 and themes_ai.NOT_DONE in revised["refused"]
              and revised["revise"]["text"].startswith("Retitled 'Mornings kept round the dog' as 'Mornings that turn round the dog'"))
        check("83: the board as it stood kept as a revision, Before: and his request, through the GETs file's own revisions",
              revised["revision"]["name"] == "Before: Retitle the first GET" and after["history"][-1]["name"] == "Before: Retitle the first GET"
              and after["groups"] == before["groups"] and themes_ai.GETS_REVISE_TASK in sent[0]["system"]
              and "participant note, private" not in json.dumps(sent))
        plain_board = {"items": [f"{W}/g1", f"{A}/g1"], "groups": [{"id": "G1", "label": "A", "members": [f"{W}/g1", f"{A}/g1"]}],
                       "picks": {}, "quotes": {}, "prefix": "G", "pick_max": 3, "unit": "card",
                       "card_quotes": {f"{W}/g1": [f"{W}/Initial:3:0"], f"{A}/g1": [f"{A}/Initial:5:0", f"{A}/Initial:3:0"]}}
        bare_pick = themes_ai.revise_ops(plain_board, [{"op": "pick", "label": "G1", "quotes": ["Initial:5:0"]},
                                                       {"op": "pick", "label": "G1", "quotes": ["Initial:3:0"]}])
        check("83: a pick on GETs naming a quote without its case takes the one case that has it, and two cases with it refuse it",
              bare_pick[0]["picks"] == {"G1": [f"{A}/Initial:5:0"]} and bare_pick[2] == [themes_ai.UNKNOWN_QUOTE])
        dup = gets_mod.ai_card(gdata()["cases"][W], f"{W}/g1", {"x": 0, "y": 0}, {})
        check("83: a PET's key quotes go once each, though several of its statements share a turn",
              len(dup["quotes"]) == len({q["key"] for q in dup["quotes"]}))
        mode["revise"] = "none"
        quiet = idiograph_routes.api_gets_ai({"workbook": any_book, "op": "revise", "version": board_id, "text": "Leave it"})
        check("83: a revise that changes nothing keeps no revision", "revised" not in quiet and len(gdata()["boards"][1]["history"]) == len(after["history"]))
        mode["revise"] = "good"

        # ── L. 184: edited by you since, after a changing save and never after one that changes nothing
        fresh = gdata()["boards"][1]
        page_copy = lambda b: dict(b, cards={k: dict(c, text=c.get("text") or "") for k, c in b["cards"].items()})
        idiograph_routes.api_gets_save({"workbook": any_book, "version": page_copy(fresh)})
        same = gdata()["boards"][1]
        moved = page_copy(same)
        moved["cards"][f"{W}/g2"] = dict(moved["cards"][f"{W}/g2"], x=moved["cards"][f"{W}/g2"]["x"] + 40)
        idiograph_routes.api_gets_save({"workbook": any_book, "version": moved})
        edited = gdata()["boards"][1]
        listed = idiograph_routes.api_gets({"workbook": any_book})["versions"][1]
        check("83: 184, a save that changes nothing leaves the mark, his first changing save adds edited by you since",
              "edited" not in same["made"] and edited["made"].get("edited") and listed["with_ai"]["edited"] is True)
        copy = idiograph_routes.api_gets_ops({"workbook": any_book, "op": "duplicate", "id": board_id})
        twin = gdata()["boards"][2]
        check("83: 184, a duplicate is his and carries no with AI",
              "made" not in twin and "with_ai" not in next(v for v in copy["versions"] if v["id"] == twin["id"]))
        plain = idiograph_routes.api_gets_ops({"workbook": any_book, "op": "new"})
        check("83: 184, New board on GETs names the next free number too",
              plain["version"]["name"] == f"Board {len(plain['versions'])}")
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, ai_mod.find_key, ai_mod.http_call = saved

    # ── M. 182 and 184 on the PETs screen
    proot = scratch / "gets-ai-pets"
    shutil.rmtree(proot, ignore_errors=True)
    work = demo_copy(proot, "Juno", "Juno - EN & ES.xlsx")
    (proot / "idiograph-project.json").write_text(json.dumps({"name": "Scratch", "research_question": DEMO_QUESTION,
                                                              "agents": {"allowed": True, "at": "2026-10-05T10:00:00+01:00"}}),
                                                  encoding="utf-8")
    pread = themes_mod.read_cards(work)
    pk = [c["key"] for c in pread["cards"]]
    old_board = themes_mod.blank_version(pread["cards"])
    old_board.update(id="v2", name="AI board 3", discarded=[pk[-1]], ai={"discarded": {pk[-1]: "about the weather"}},
                     note="Proposed by Haiku 4.5 from Board 1 on 2 October 2026 at 12:02, up to 5 PETs. 1 PET, 2 placed, 1 discarded, 0 unplaced.",
                     groups=[{"id": "g1", "label": "Mornings", "members": pk[:2], "x": 0, "y": 0}])
    agent_board = dict(themes_mod.blank_version(pread["cards"]), id="v3", name="Board 3",
                       made={"by": "agent", "tool": "Claude Code", "request": "one board", "at": "2026-10-05T11:00:00+01:00"})
    themes_mod.write(work, {"schema": 2, "case": "Juno", "workbook": work.name, "current": "v1",
                            "boards": [themes_mod.blank_version(pread["cards"]), old_board, agent_board]})
    old_kept = json.loads(json.dumps(themes_mod.load(work)["boards"][1]))
    psent = []

    def pwire(method, url, headers, payload, timeout):
        psent.append({"system": payload["system"], "user": payload["messages"][-1]["content"]})
        if themes_ai.PICKS_TASK in payload["system"]:
            text = '{"picks": []}'
        else:
            found = re.findall(r"^- (\S+:\d+:\d+) \(", payload["messages"][-1]["content"], re.M)
            text = json.dumps({"groups": [{"label": "Mornings that belong to the dog", "members": found[0:3]},
                                          {"label": "A house that holds two", "members": found[3:6]}],
                               "left_out": [{"key": found[6], "reason": "It is about the weather, not the dog"}],
                               "discarded": [{"key": found[7], "reason": "an older shape"}]})
        return 200, json.dumps({"content": [{"type": "text", "text": text}], "stop_reason": "end_turn"})

    pfile = lambda: json.loads(themes_mod.themes_path(work).read_text(encoding="utf-8"))
    try:
        server_mod.CONFIG_PATH = config_path
        server_mod.ROOT_OVERRIDE = str(proot)
        server_mod.STATE_MEMORY = {"recent": []}
        ai_mod.find_key = lambda *a, **kw: "k-test"
        ai_mod.http_call = pwire
        settings()
        opened = idiograph_routes.api_themes({"workbook": str(work)})
        listed = {v["name"]: v.get("with_ai") for v in opened["versions"]}
        check("83: 184, an old AI board keeps its name and carries with AI from its note, an agent's from its mark, his own nothing",
              listed == {"Board 1": None, "AI board 3": {"by": "ai", "said": "Haiku 4.5, from Board 1", "edited": False},
                         "Board 3": {"by": "agent", "said": "Claude Code in a conversation", "edited": False}}, str(listed))
        made = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "group", "version": "v1", "from": "all"})
        new = pfile()["boards"][-1]
        system = psent[0]["system"]
        check("83: 182, the prompt asks for statements left out with a reason and no longer for discards",
              '"left_out": [{"key": "<key>", "reason": "..."}]' in system and '"discarded"' not in system
              and "Nothing you answer puts a statement in the bin." in system
              and "Leave a statement out of every theme only where rule 4 would let it go" in system)
        placed = {m for g in new["groups"] for m in g["members"]}
        check("83: 182, New AI board leaves what it would have discarded in Not placed, nothing in the bin, each reason kept",
              new["discarded"] == [] and len(new["ai"]["discarded"]) == 2
              and not (set(new["ai"]["discarded"]) & placed)
              and sorted(new["ai"]["discarded"].values()) == ["It is about the weather, not the dog", "an older shape"]
              and made["made"]["left_out"] == 2 and made["made"]["discarded"] == 0, str(new.get("ai")))
        check("83: 182, the note and the line count what is not placed",
              f"2 PETs, 6 placed, {len(pk) - 6} not placed." in new["note"] and made["made"]["left"] == len(pk) - 6, new["note"])
        check("83: 184, the AI board is Board 4, the next free number, made by Opus 5.5 from all statements",
              new["name"] == "Board 4" and new["made"]["by"] == "ai" and new["made"]["from"] == "all statements"
              and made["version"]["with_ai"] == {"by": "ai", "said": "Opus 5.5, from all statements", "edited": False})
        check("83: 182, an old AI board's discards stay in its bin as they are",
              pfile()["boards"][1]["discarded"] == old_kept["discarded"] and pfile()["boards"][1]["ai"] == old_kept["ai"]
              and pfile()["boards"][1]["name"] == "AI board 3")
        laid = themes_ai.lay_out([{"label": "A", "members": pk[:3], "groups": []}], pread["cards"], [], why=set(pk[3:6]))
        tall = lambda k: themes_mod.card_height(laid["cards"][k]["text"]) + (themes_ai.WHY_H if k in pk[3:6] else 0)
        pile = [k for k in pk[3:] if k in laid["cards"]]
        boxes = [(laid["cards"][k]["x"], laid["cards"][k]["y"], themes_mod.CARD_W, tall(k)) for k in pile]
        check("83: 182, the pile leaves room under each card with a reason, so nothing lies over it",
              not any(themes_mod.clash(boxes[i], boxes[j]) for i in range(len(boxes)) for j in range(i + 1, len(boxes))))
        shown = idiograph_routes.api_themes({"workbook": str(work)})
        body = dict({k: x for k, x in shown["version"].items() if k != "v"}, cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in shown["cards"]},
                    groups=shown["groups"], discarded=shown["discarded"], picks=shown["picks"],
                    ai={"discarded": shown["discard_reasons"]}, notes=[])
        idiograph_routes.api_themes_save({"workbook": str(work), "version": body})
        still = pfile()["boards"][-1]
        moved = json.loads(json.dumps(body))
        first_key = next(iter(moved["cards"]))
        moved["cards"][first_key]["x"] += 60
        idiograph_routes.api_themes_save({"workbook": str(work), "version": moved})
        edited = pfile()["boards"][-1]
        after = idiograph_routes.api_themes({"workbook": str(work)})
        check("83: 184, a save that changes nothing leaves with AI alone, his first changing save adds edited by you since",
              "edited" not in still["made"] and edited["made"].get("edited")
              and after["version"]["with_ai"] == {"by": "ai", "said": "Opus 5.5, from all statements", "edited": True})
        twin = idiograph_routes.api_themes_versions({"workbook": str(work), "op": "duplicate"})
        fresh = idiograph_routes.api_themes_versions({"workbook": str(work), "op": "new"})
        check("83: 184, a duplicate is his with no with AI, and New board names the next free number",
              "with_ai" not in twin["version"] and "made" not in pfile()["boards"][-2] and fresh["version"]["name"] == "Board 6"
              and themes_mod.board_name([{"name": "Board 1"}, {"name": "Board 3"}]) == "Board 4"
              and themes_mod.board_name([{"name": "Board 2"}]) == "Board 3" and themes_mod.board_name([], "Mine") == "Mine")
        switch = idiograph_routes.api_themes_cases({"workbook": str(work)})
        check("83: 184, the case switcher lists the board's with AI after its name too",
              all("with_ai" in c or not c.get("board_name", "").startswith("Board 4") for c in switch["cases"]))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, ai_mod.find_key, ai_mod.http_call = saved

    # ── N. 184, the command line's board new makes Board N, with AI
    croot = scratch / "gets-ai-cli"
    shutil.rmtree(croot, ignore_errors=True)
    cbook = demo_copy(croot, "Juno", "Juno - EN & ES.xlsx")
    (croot / "idiograph-project.json").write_text(json.dumps({"name": "Scratch", "research_question": DEMO_QUESTION,
                                                              "agents": {"allowed": True, "at": "2026-10-05T10:00:00+01:00"}}),
                                                  encoding="utf-8")
    cfg_file = scratch / "gets-ai-cli-config.json"
    cfg_file.write_text(json.dumps({"root": str(croot), "interviewer": "Adam"}), encoding="utf-8")
    spec = scratch / "gets-ai-board.json"
    spec.write_text(json.dumps({"pets": [{"title": "Mornings at the stair", "members": ["S1", "S2"]}],
                                "not_placed": {"S3": "It fits no PET"}}), encoding="utf-8")
    code, out, err = cli.run(["--root", str(croot), "--config", str(cfg_file), "board", "new", "Juno", "--from", str(spec),
                              "--note", "One board", "--tool", "Claude Code"])
    stored = themes_mod.load(cbook)
    newest = stored["boards"][-1] if stored else {}
    check("83: 184, the command line's board new makes Board N with AI, an agent's mark carrying its hash, Board 1 "
          "on a case with no themes file (95)",
          code == 0 and out.startswith("Made Board 1 on Juno") and newest.get("name") == "Board 1"
          and len(stored["boards"]) == 1
          and newest["made"]["by"] == "agent" and len(newest["made"].get("hash") or "") == 64
          and themes_mod.summary(newest)["with_ai"]["said"] == "Claude Code in a conversation, from all statements", out + err)

    # ── O. the page
    callers = [name for name in ("thAutoGroup", "thNamesAsk", "thReviewAsk", "thReplySend", "thReviseSend")
               if "api(thAiPath()," in fn(js, name)]
    check("83: the five AI presses ask the PETs route or on GETs their own, through one helper, and nothing else calls it",
          callers == ["thAutoGroup", "thNamesAsk", "thReviewAsk", "thReplySend", "thReviseSend"]
          and "const thAiPath = () => (TH.mode === 'gets' ? '/api/gets-ai' : '/api/themes-ai');" in js
          and js.count("api(thAiPath(),") == 5 and js.count("'/api/gets-ai'") == 3)
    check("83: the old-server line, a GETs page in front of a server from before shows the controls from its own settings, and a press says to restart",
          "if (TH.mode === 'gets' && !data.gets_ai) TH.ai = { on: aiFor(TH.config, 'gets'), model_name: '', cap: 5 };" in fn(js, "themesOpen")
          and all("needsRestart(err)" in fn(js, n) and "RESTART_LINE" in fn(js, n) for n in callers))
    panel = fn(js, "gtPanelDraw")
    check("83: AI suggest GET titles in a GET's Inspector, the PETs control's words changed, its one step of undo the rename's",
          "thNamesHtml(item, { unit: owner !== undefined ? t('themes.unit.sub') : t('themes.unit.get') })" in panel
          and "thDone(before, t('themes.step.renamed')" in fn(js, "thNameApply") and "thLeftOutHtml(v, item.id, owner)" in panel)
    check("83: a revise on GETs lands the rows with the GETs before the one step of undo",
          fn(js, "thReviseSend").index("v.rows = JSON.parse(JSON.stringify(data.revised.rows))") < fn(js, "thReviseSend").index("thDone(before, t('themes.step.revised_ai')"))
    check("83: New AI board's card on GETs: from every participant's PETs, up to 5 GETs kept in the GETs file, the room line asked without a call",
          "if (TH.mode === 'gets') gtAiCardDraw();" in fn(js, "thAiCard") and "op: 'room'" in fn(js, "gtAiCardDraw")
          and "api('/api/gets-settings', { workbook: TH.path, op: 'save', cap: next })" in fn(js, "thCapStep")
          and "unit.textContent = ` ${TH.mode === 'gets' ? t('themes.unit.gets') : t('themes.unit.pets')}`;" in fn(js, "thCapDraw")
          and "t('themes.ai.head_left', { name, themes, left: thrown })" in fn(js, "thAutoGroup"))
    node = shutil.which("node")
    if not node:
        skip("83: the page's new parts in node", "no node on this machine")
    else:
        script = scratch / "gets-ai.js"
        script.write_text(support.i18n_js() + js + r"""
const els = {};
function $(id) { return els[id] || (els[id] = { id, hidden: true, textContent: '', title: '' }); }
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const out = {};
out.mark = [thWithAi(null), thWithAi({ said: 'Opus 5.5, from all statements', edited: false }),
  thWithAi({ said: 'Opus 5.5, from Board 2', edited: true })];
const v = { cards: { a: {}, b: {} }, groups: [], discarded: ['b'], ai: { discarded: { a: 'off the question', b: 'binned' } } };
out.why = [thWhyHtml(v, 'a', undefined), thWhyHtml(v, 'a', 'g1'), thWhyHtml(v, 'b', undefined)];
TH.mode = 'gets'; out.gets = thAiPath(); TH.mode = 'pets'; out.pets = thAiPath();
TH.mode = 'gets'; TH.meta = { id: 'b3', name: 'Board 3' }; TH.ai = { model_name: 'Haiku 4.5' }; TH.aiFrom = 'all';
TH.aiRoom = { all: 12, board: 0 }; gtAiFromDraw();
out.card = [$('th-aicard-title').textContent, $('th-from-all').textContent, $('th-aicard-line').textContent];
TH.aiFrom = 'board'; gtAiFromDraw(); out.board = [$('th-aicard-title').textContent, $('th-aicard-line').textContent];
TH.gets = { cases: [{ in: true, pets: [{ id: 'g1' }, { id: 'g2', parent: 'g1' }, { id: 'g3' }] }, { in: false, pets: [{ id: 'g1' }] }, { in: true, none: true, pets: [] }] };
out.count = gtAiCount(true);
console.log(JSON.stringify(out));
""", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        out = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
        check("83: in node, the reason under a card in Not placed, and none once placed or in the bin",
              out.get("why") == ['<p class="th-pile-why th-card-why">off the question</p>', "", ""], str(out.get("why")))
        check("83: in node, the GETs route on GETs and the PETs one on PETs, and the card's title, From and its room line",
              out.get("gets") == "/api/gets-ai" and out.get("pets") == "/api/themes-ai"
              and out.get("card") == ["New AI board from every participant's PETs", "Every participant's PETs",
                                      "A new board, made by Haiku 4.5. Board 3 is left as it is. To fit what the model can take, Idiograph left out the words of 12 statements, the lowest in their PETs."]
              and out.get("board") == ["New AI board from Board 3", "A new board, made by Haiku 4.5. Board 3 is left as it is."]
              and out.get("count") == {"pets": 2, "subs": 1}, str(out))
