from __future__ import annotations

import csv
import json
from pathlib import Path

import export as export_mod
import rounds as rounds_mod
import workbook as wb_mod

from .support import DEMO_SHEET, check, demo_copy
import idiograph_routes


def test_themes_follow(scratch):
    print("\n48. Themes follow the rows and the words: a trim and its undo, an assignment and its undo,"
          " a line or a quote moved in its cell")
    import server as server_mod
    import themes as themes_mod

    root = scratch / "follow-root"
    saved_root = server_mod.ROOT_OVERRIDE
    server_mod.ROOT_OVERRIDE = str(root)
    try:
        _follow_checks(scratch, root, server_mod, themes_mod)
    finally:
        server_mod.ROOT_OVERRIDE = saved_root


def _follow_checks(scratch, root, server_mod, themes_mod):
    S = DEMO_SHEET
    Q1, Q2, Q9 = '"the second stair"', '"quiet and never empty"', '"twenty past six"'
    trim_api, rows_api = idiograph_routes.api_trim, idiograph_routes.api_rows

    def file(work):
        return json.loads(themes_mod.themes_path(work).read_text(encoding="utf-8"))

    def board(work, bid="v1"):
        return next(b for b in file(work)["boards"] if b["id"] == bid)

    def states(work):
        """Every board's state as a revision holds it, its review, and every revision's state."""
        out = {}
        for b in file(work)["boards"]:
            out[b["id"]] = (themes_mod.board_state(b), themes_mod.normalise(b).get("review"),
                            [r["state"] for r in b.get("history") or []])
        return out

    def texts_of(work):
        return {c["key"]: c["text"] for c in themes_mod.read_cards(work)["cards"]}

    def agree(work):
        """Every board and every revision holds each card on a key the workbook holds with its
        words, on the rows the progress file has as written, and nothing on any other row."""
        live = texts_of(work)
        done = {k for k, v in rounds_mod.load_progress(work)["rows"].items() if v == "has-content"}
        problems = []
        for b in file(work)["boards"]:
            for at, state in [(b["id"], b)] + [(f"{b['id']}/{r['id']}", r["state"]) for r in b.get("history") or []]:
                wrong = [k for k, c in state["cards"].items() if live.get(k) != c["text"]]
                rows = {themes_mod.row_key(*themes_mod.split_card_key(k)[:2]) for k in state["cards"]}
                if wrong or rows != done:
                    problems.append(f"{at}: {wrong[:3]} {sorted(rows ^ done)[:3]}")
        return not problems, "; ".join(problems[:3])

    def page_body(shown):
        """The board as the page sends it back after an open, the way `thBody` builds it."""
        cards = {}
        for c in shown["cards"]:
            card = {"x": c["x"], "y": c["y"], "text": c["stored"] if c.get("changed") else c["text"]}
            if c.get("changed"):
                card["live"] = c["text"]
            cards[c["key"]] = card
        meta = shown["version"]
        out = {"id": meta["id"], "name": meta["name"], "note": meta["note"], "created": meta["created"],
               "updated": meta["updated"], "cards": cards,
               "groups": [dict(g, members=list(g["members"])) for g in shown["groups"]],
               "discarded": list(shown["discarded"]), "picks": json.loads(json.dumps(shown["picks"]))}
        if shown.get("discard_reasons"):
            out["ai"] = {"discarded": dict(shown["discard_reasons"])}
        if shown.get("review"):
            out["review"] = json.loads(json.dumps(shown["review"]))
        return out

    def setup(name, themes=True):
        """A scratch case: two key quotes on row 3 and one on row 9, the progress file with every
        written turn done, and a board with themes, a sub-theme, a discard and its reason, picks, a
        review, a revision and a second board beside it."""
        work = demo_copy(root, name, "Juno - EN & ES.xlsx")
        wb_mod.save_turn(work, S, 3, None, None, f"{Q1}\n{Q2}")
        wb_mod.save_turn(work, S, 9, None, None, Q9)
        progress = rounds_mod.load_progress(work)
        progress["rows"] = {f"{S}:{r}": "has-content" for r in (3, 5, 7, 9, 11, 13)}
        progress["flags"] = [f"{S}:9", f"{S}:3"]
        rounds_mod.save_progress(work, progress)
        if not themes:
            return work
        read = themes_mod.read_cards(work)
        raw = themes_mod.blank_version(read["cards"])
        raw["groups"] = [{"id": "g1", "label": "Mornings", "members": [f"{S}:3:0", f"{S}:3:1", f"{S}:3:2", f"{S}:9:0"],
                          "x": 0, "y": -400},
                         {"id": "g2", "label": "Won over", "members": [f"{S}:7:0", f"{S}:7:1", "g3"], "x": 900, "y": -400},
                         {"id": "g3", "label": "The yard", "members": [f"{S}:11:0"], "x": 900, "y": 0}]
        raw["discarded"] = [f"{S}:5:2"]
        raw["picks"] = {"g1": [f"{S}:3:1", f"{S}:9:0"]}
        raw["ai"] = {"discarded": {f"{S}:5:2": "off the question"}}
        raw["review"] = {"at": "2026-10-02T12:00:00+01:00", "model": "Haiku 4.5", "items": [
            {"about": f"{S}:3:0", "question": "Does the stair belong with the mornings?", "rule": "3", "why": "w", "state": "open"},
            {"about": f"{S}:11:0", "question": "Does the yard stand apart from the rest?", "rule": "4", "why": "w", "state": "considered"},
            {"about": "g1", "question": "Do the mornings read as one experience?", "rule": "5", "why": "w", "state": "open"},
            {"about": None, "question": "Does the board answer the question?", "rule": "", "why": "w", "state": "open"}]}
        idiograph_routes.api_themes_save({"workbook": str(work), "version": raw})
        idiograph_routes.api_themes_boards({"workbook": str(work), "op": "revision", "name": "Kept by hand"})
        idiograph_routes.api_themes_versions({"workbook": str(work), "op": "duplicate", "id": "v1"})
        idiograph_routes.api_themes_versions({"workbook": str(work), "op": "switch", "id": "v1"})
        return work

    # ── A. what a save keeps: the words of the picks, and in a revision too
    work = setup("words")
    held = board(work)
    check("a save writes `quoted`, the words of every quote the picks name, from the workbook",
          held.get("quoted") == {f"{S}:3:1": Q2, f"{S}:9:0": Q9} and board(work, "v2").get("quoted") == held["quoted"],
          str(held.get("quoted")))
    check("a revision keeps the picks' words, and a page that never sends them loses none",
          held["history"][0]["state"].get("quoted") == {f"{S}:3:1": Q2, f"{S}:9:0": Q9}
          and "quoted" not in page_body(idiograph_routes.api_themes({"workbook": str(work)})))
    idiograph_routes.api_themes_versions({"workbook": str(work), "op": "new"})
    idiograph_routes.api_themes_boards({"workbook": str(work), "op": "copy", "id": "v1", "group": "g1", "to": "v3"})
    copied = board(work, "v3")
    check("Copy to board carries the picks' words with the theme",
          copied.get("quoted") == {f"{S}:3:1": Q2, f"{S}:9:0": Q9}
          and sorted(k for ks in copied["picks"].values() for k in ks) == [f"{S}:3:1", f"{S}:9:0"], str(copied.get("quoted")))
    idiograph_routes.api_themes_versions({"workbook": str(work), "op": "delete", "id": "v3"})
    idiograph_routes.api_themes_versions({"workbook": str(work), "op": "switch", "id": "v1"})

    # ── B. words before index: a line inserted at the top of a cell
    before = board(work)
    row3 = [before["cards"][f"{S}:3:{i}"]["text"] for i in range(3)]
    wb_mod.save_turn(work, S, 3, "A line written above the others\n" + "\n".join(row3), None, None)
    bytes_before = themes_mod.themes_path(work).read_bytes()
    shown = idiograph_routes.api_themes({"workbook": str(work)})
    cards = {c["key"]: c for c in shown["cards"]}
    g1 = next(g for g in shown["groups"] if g["id"] == "g1")
    moved = all(cards[f"{S}:3:{i + 1}"]["text"] == row3[i]
                and (cards[f"{S}:3:{i + 1}"]["x"], cards[f"{S}:3:{i + 1}"]["y"])
                == (before["cards"][f"{S}:3:{i}"]["x"], before["cards"][f"{S}:3:{i}"]["y"]) for i in range(3))
    check("a line inserted at the top of a cell keeps every card in its theme, its place and unmarked",
          moved and g1["members"] == [f"{S}:3:1", f"{S}:3:2", f"{S}:3:3", f"{S}:9:0"]
          and not any(cards[f"{S}:3:{i}"].get(f) for i in (1, 2, 3) for f in ("new", "changed", "missing")),
          str(g1["members"]))
    check("and the new line is a new card, and nothing else is new, changed or missing",
          cards[f"{S}:3:0"].get("new") is True
          and [k for k, c in cards.items() if c.get("new") or c.get("changed") or c.get("missing")] == [f"{S}:3:0"])
    check("opening writes nothing: the moved keys are held in memory",
          themes_mod.themes_path(work).read_bytes() == bytes_before)
    idiograph_routes.api_themes_save({"workbook": str(work), "version": page_body(shown)})
    check("and the next save writes them",
          board(work)["groups"][0]["members"] == [f"{S}:3:1", f"{S}:3:2", f"{S}:3:3", f"{S}:9:0"]
          and board(work)["cards"][f"{S}:3:1"]["text"] == row3[0])
    out = export_mod.export(work, themes=(themes_mod.themes_path(work), None))
    lines = Path(out["path"]).read_text(encoding="utf-8-sig").splitlines()
    check("the CSV's PET column follows the words too",
          all(any(r[2] == row3[i] and r[3] == "Mornings" for r in csv.reader(lines)) for i in range(3)))

    # ── C. a line taken out of the middle of a cell, and one reworded in place
    row5 = [board(work)["cards"][f"{S}:5:{i}"]["text"] for i in range(3)]
    spot5 = {i: (board(work)["cards"][f"{S}:5:{i}"]["x"], board(work)["cards"][f"{S}:5:{i}"]["y"]) for i in range(3)}
    raw = page_body(idiograph_routes.api_themes({"workbook": str(work)}))
    raw["groups"].append({"id": "g4", "label": "Caught", "members": [f"{S}:5:0", f"{S}:5:1"], "x": 0, "y": 900})
    raw["discarded"] = []
    idiograph_routes.api_themes_save({"workbook": str(work), "version": raw})
    wb_mod.save_turn(work, S, 5, f"{row5[0]}\n{row5[2]}", None, None)
    shown = idiograph_routes.api_themes({"workbook": str(work)})
    cards = {c["key"]: c for c in shown["cards"]}
    g4 = next(g for g in shown["groups"] if g["id"] == "g4")
    gone = [c for c in shown["cards"] if c["text"] == row5[1]]
    check("a line removed from the middle of a cell keeps the others in their themes, their places and unmarked",
          cards[f"{S}:5:0"]["text"] == row5[0] and cards[f"{S}:5:1"]["text"] == row5[2]
          and (cards[f"{S}:5:1"]["x"], cards[f"{S}:5:1"]["y"]) == spot5[2]
          and not any(cards[f"{S}:5:{i}"].get(f) for i in (0, 1) for f in ("new", "changed", "missing")),
          str([(k, c["text"][:20]) for k, c in cards.items() if k.startswith(f"{S}:5:")]))
    check("and the card of the line removed is missing, in its theme and its place, under a key of its own",
          len(gone) == 1 and gone[0].get("missing") is True and gone[0]["key"] in g4["members"]
          and gone[0]["key"] not in (f"{S}:5:0", f"{S}:5:1") and (gone[0]["x"], gone[0]["y"]) == spot5[1]
          and f"{S}:5:0" in g4["members"], str(g4["members"]))
    row7 = [c["text"] for c in shown["cards"] if c["row"] == 7]
    wb_mod.save_turn(work, S, 7, f"{row7[0]}\nWon over in the end by the lean\n{row7[2]}", None, None)
    shown = idiograph_routes.api_themes({"workbook": str(work)})
    cards = {c["key"]: c for c in shown["cards"]}
    check("a line reworded in place is changed, with its stored text, and stays in its theme",
          cards[f"{S}:7:1"].get("changed") is True and cards[f"{S}:7:1"]["stored"] == row7[1]
          and cards[f"{S}:7:1"]["text"] == "Won over in the end by the lean"
          and f"{S}:7:1" in next(g for g in shown["groups"] if g["id"] == "g2")["members"]
          and not cards[f"{S}:7:0"].get("changed") and not cards[f"{S}:7:2"].get("changed"))

    # ── D. picks follow their quotes' words
    wb_mod.save_turn(work, S, 3, None, None, Q2)
    shown = idiograph_routes.api_themes({"workbook": str(work)})
    check("a quote removed before a picked one keeps the pick on the same words",
          shown["picks"]["g1"] == [f"{S}:3:0", f"{S}:9:0"]
          and shown["quotes"][f"{S}:3"]["quotes"] == [{"key": f"{S}:3:0", "text": Q2}], str(shown["picks"]))
    idiograph_routes.api_themes_save({"workbook": str(work), "version": page_body(shown)})
    check("and the next save writes the moved pick with its words",
          board(work)["picks"]["g1"] == [f"{S}:3:0", f"{S}:9:0"]
          and board(work)["quoted"] == {f"{S}:3:0": Q2, f"{S}:9:0": Q9}, str(board(work).get("quoted")))
    wb_mod.save_turn(work, S, 9, None, None, '"twenty to seven"')
    shown = idiograph_routes.api_themes({"workbook": str(work)})
    check("a quote reworded drops the pick", shown["picks"]["g1"] == [f"{S}:3:0"], str(shown["picks"]))
    legacy = page_body(shown)
    legacy["picks"]["g1"] = [f"{S}:3:0"]
    check("a pick with no words kept, from a file before them, is judged by its key as before",
          themes_mod.merge(themes_mod.read_cards(work)["cards"], dict(legacy, picks={"g1": [f"{S}:3:0", f"{S}:3:5"]}),
                           themes_mod.read_cards(work)["quotes"])["picks"] == {"g1": [f"{S}:3:0"]})

    # ── E. a trim at the front, through the endpoint, and its undo
    work = setup("trim")
    was = states(work)
    first_rev = board(work)["history"][0]["id"]
    cut = trim_api({"path": str(work), "sheet": S, "row": 6, "direction": "before", "current": {"sheet": S, "row": 9}})
    after = {b["id"]: b for b in file(work)["boards"]}
    shift = lambda key: f"{S}:{int(key.split(':')[1]) - 5}:{key.split(':')[2]}"
    kept = sorted((k for k in was["v1"][0]["cards"] if int(k.split(":")[1]) > 6), key=themes_mod._order)
    expect = sorted(shift(k) for k in kept)
    check("a trim at the front renumbers the cards of every board and of every revision",
          all(sorted(after[b]["cards"]) == expect for b in ("v1", "v2"))
          and sorted(after["v1"]["history"][0]["state"]["cards"]) == expect
          and all(after["v1"]["cards"][shift(k)]["text"] == was["v1"][0]["cards"][k]["text"] for k in kept),
          str(sorted(after["v1"]["cards"])[:4]))
    check("its themes, picks and the picks' words move with them",
          [g["members"] for g in after["v1"]["groups"]] == [[f"{S}:4:0"], [f"{S}:2:0", f"{S}:2:1", "g3"], [f"{S}:6:0"]]
          and after["v1"]["picks"] == {"g1": [f"{S}:4:0"]} and after["v1"]["quoted"] == {f"{S}:4:0": Q9}
          and after["v2"]["groups"] == after["v1"]["groups"],
          str([g["members"] for g in after["v1"]["groups"]]))
    check("aiout: a review from before stays as the file held it, its about never moved",
          after["v1"]["review"] == was["v1"][1] and [i["about"] for i in after["v1"]["review"]["items"]] == [f"{S}:3:0", f"{S}:11:0", "g1", None],
          str([i["about"] for i in after["v1"]["review"]["items"]]))
    record = after["v1"].get("cut") or [{}]
    check("the cards on cut rows go under cut, with the trim's id, their themes, their discard, their picks and the reasons",
          len(record) == 1 and record[0]["trim"] == cut["id"]
          and sorted(record[0]["cards"]) == [f"{S}:{r}:{i}" for r in (3, 5) for i in range(3)]
          and record[0]["cards"][f"{S}:3:0"] == was["v1"][0]["cards"][f"{S}:3:0"]
          and record[0]["members"] == {"g1": [f"{S}:3:0", f"{S}:3:1", f"{S}:3:2"]}
          and record[0]["discarded"] == [f"{S}:5:2"] and record[0]["picks"] == {"g1": [f"{S}:3:1"]}
          and record[0]["quoted"] == {f"{S}:3:1": Q2} and record[0]["ai"] == {f"{S}:5:2": "off the question"}
          and after["v2"]["cut"] == record and after["v1"]["history"][0]["state"]["cut"][0]["trim"] == cut["id"],
          json.dumps(record)[:200])
    ok, said = agree(work)
    check("after the trim the progress file and the themes file agree, row for row", ok, said)
    shown = idiograph_routes.api_themes({"workbook": str(work)})
    check("the screen opens on the surviving rows with nothing new, changed or missing, and the pick in place",
          not any(c.get("new") or c.get("changed") or c.get("missing") for c in shown["cards"])
          and shown["picks"] == {"g1": [f"{S}:4:0"]} and "cut" not in shown and "quoted" not in shown)
    view = idiograph_routes.api_themes_boards({"workbook": str(work), "op": "view", "id": "v1", "revision": first_rev})
    check("a revision viewed after a trim shows live keys",
          sorted(c["key"] for c in view["cards"]) == sorted(texts_of(work))
          and not any(c.get("new") or c.get("missing") for c in view["cards"]))

    back = rows_api({"op": "untrim", "path": str(work), "id": cut["id"], "current": {"sheet": S, "row": 4}})
    now = states(work)
    check("the untrim puts the cut cards back in their themes, with their places, discards, picks and reasons",
          now["v1"][0] == was["v1"][0] and now["v2"][0] == was["v2"][0] and "cut" not in board(work)
          and "themes" not in back, str(sorted(set(now["v1"][0]) ^ set(was["v1"][0]))))
    check("and every revision as it was, and the review as it was",
          now["v1"][2] == was["v1"][2] and now["v1"][1] == was["v1"][1] and now["v2"][1] == was["v2"][1])
    ok, said = agree(work)
    check("after the untrim the progress file and the themes file agree", ok, said)

    # a trim at the back, and an untrim the themes file has no record of
    cut = trim_api({"path": str(work), "sheet": S, "row": 12, "direction": "after"})
    check("a trim at the back keeps the cut cards the same way, the rest unmoved",
          sorted(board(work)["cut"][0]["cards"]) == [f"{S}:13:{i}" for i in range(3)]
          and sorted(board(work)["cards"]) == sorted(k for k in was["v1"][0]["cards"] if int(k.split(":")[1]) < 12))
    ok, said = agree(work)
    check("and the two files agree after it", ok, said)
    data = file(work)
    for b in data["boards"]:
        b.pop("cut", None)
        for r in b.get("history") or []:
            r["state"].pop("cut", None)
    themes_mod.themes_path(work).write_text(json.dumps(data), encoding="utf-8")
    rows_api({"op": "untrim", "path": str(work), "id": cut["id"]})
    shown = idiograph_routes.api_themes({"workbook": str(work)})
    check("an untrim whose id the file does not know restores nothing, and the rows come back as new cards",
          sorted(c["key"] for c in shown["cards"] if c.get("new")) == [f"{S}:13:{i}" for i in range(3)]
          and f"{S}:13:0" not in board(work)["cards"])

    # ── F. an assignment that merges three turns into one, and its undo, then a split and its undo
    work = setup("assign")
    was = states(work)
    case = wb_mod.read_case(work)
    her = case["sheets"][0]["rows"][1]["name"]
    merged = rows_api({"op": "assign", "path": str(work), "sheet": S, "row": 4, "to": her,
                       "current": {"sheet": S, "row": 9}})
    live = texts_of(work)
    cards = board(work)["cards"]
    check("a whole turn merging its neighbours carries their cards onto the one row, in sheet order",
          merged["kind"] == "merge" and [cards[f"{S}:3:{i}"]["text"] for i in range(6)]
          == [was["v1"][0]["cards"][f"{S}:{r}:{i}"]["text"] for r in (3, 5) for i in range(3)]
          and all(live.get(k) == c["text"] for k, c in cards.items()), str(sorted(cards)[:7]))
    check("the rows below move up with the cards, their themes and their picks",
          board(work)["groups"][0]["members"] == [f"{S}:3:0", f"{S}:3:1", f"{S}:3:2", f"{S}:7:0"]
          and board(work)["picks"] == {"g1": [f"{S}:3:1", f"{S}:7:0"]} and board(work)["discarded"] == [f"{S}:3:5"]
          and board(work)["ai"] == {"discarded": {f"{S}:3:5": "off the question"}}
          and "themes" not in merged, str(board(work)["groups"][0]["members"]))
    ok, said = agree(work)
    check("after the assignment the progress file and the themes file agree", ok, said)
    rows_api({"op": "restore", "path": str(work), "id": merged["id"], "current": {"sheet": S, "row": 7}})
    check("its undo puts every card back on its own row, every board and revision as it was",
          states(work) == was, str(sorted(board(work)["cards"])[:7]))
    ok, said = agree(work)
    check("after the undo the two files agree", ok, said)

    text9 = next(r["text"] for r in case["sheets"][0]["rows"] if r["row"] == 9)
    words9 = text9.split(" ")
    start = len(" ".join(words9[:4])) + 1
    end = start + len(" ".join(words9[4:7]))
    him = next(r["name"] for r in case["sheets"][0]["rows"] if r["name"] != her)
    split = rows_api({"op": "assign", "path": str(work), "sheet": S, "row": 9, "to": him, "start": start, "end": end,
                      "current": {"sheet": S, "row": 9}})
    cards = board(work)["cards"]
    check("words assigned out of the middle of a turn leave its cards on it and move the rows below by two",
          split["block"]["after"] == 3 and all(f"{S}:9:{i}" in cards for i in range(3))
          and sorted(k for k in cards if int(k.split(":")[1]) > 9) == [f"{S}:{r}:{i}" for r in (13, 15) for i in range(3)]
          and board(work)["groups"][2]["members"] == [f"{S}:13:0"])
    ok, said = agree(work)
    check("and the two files agree after it", ok, said)
    rows_api({"op": "restore", "path": str(work), "id": split["id"]})
    check("and its undo puts everything back", states(work) == was)

    # ── G. no themes file, and one that cannot be read
    work = setup("none", themes=False)
    trim_api({"path": str(work), "sheet": S, "row": 4, "direction": "before"})
    check("a trim on a case with no themes file writes none", not themes_mod.themes_path(work).exists())
    work = setup("broken")
    themes_mod.themes_path(work).write_text("{ not json", encoding="utf-8")
    cut = trim_api({"path": str(work), "sheet": S, "row": 4, "direction": "before"})
    check("a themes file that cannot be read is left as it is, and the answer says so in one line",
          themes_mod.themes_path(work).read_text(encoding="utf-8") == "{ not json"
          and "could not be read" in cut.get("themes", "") and "\n" not in cut.get("themes", "")
          and rounds_mod.load_progress(work)["trims"][-1]["id"] == cut["id"], cut.get("themes", ""))
