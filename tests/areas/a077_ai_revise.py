from __future__ import annotations

import json

import workbook as wb_mod

from .support import DEMO_QUESTION, DEMO_SHEET, check, demo_copy, demo_sheet, skip


def test_ai_revise(scratch):
    print("\n77. The board's applier, the operations board apply and gets apply run, which AI revise ran until it went "
          "on 11 November 2026 (aiout): each operation read strictly and applied in order to a plain board (180)")
    import themes as themes_mod
    import themes_ai

    # ── A. the fixture: an invented board on a copy of the demo, with a sticky note, a statement in
    # the bin, a pick, a PET's note and an interviewer's note in the workbook
    root = scratch / "ai-revise"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    (root / "idiograph-project.json").write_text(json.dumps({"name": "Scratch", "research_question": DEMO_QUESTION}),
                                                 encoding="utf-8")
    sheet, her, him = demo_sheet(work)
    his = [r["row"] for r in sheet["rows"] if r["name"] == him]
    wb_mod.save_interviewer_note(work, DEMO_SHEET, his[1], "Pressed too soon on the walk question", him)
    read = themes_mod.read_cards(work)
    keys = [c["key"] for c in read["cards"]]
    quoted = [k for k in keys if k.startswith(f"{DEMO_SHEET}:13:")]
    pick = read["quotes"][f"{DEMO_SHEET}:13"]["quotes"][0]["key"] if f"{DEMO_SHEET}:13" in read["quotes"] else ""
    binned = keys[8]
    board = themes_mod.blank_version(read["cards"])
    spots = {keys[0]: (0, 40), keys[1]: (210, 40), keys[2]: (24, 170), keys[3]: (234, 170),
             quoted[0]: (900, 40), quoted[1]: (1110, 40)}
    for i, key in enumerate(k for k in keys if k not in spots):
        spots[key] = (1600 + (i % 3) * 210, 40 + (i // 3) * 100)
    for key, (x, y) in spots.items():
        board["cards"][key].update(x=x, y=y)
    board["groups"] = [
        {"id": "g1", "label": "Mornings that belong to the dog", "note": "The early walks set the day.",
         "members": [keys[0], keys[1], "g3"], "x": 0, "y": 0},
        {"id": "g2", "label": "A house that holds two", "members": quoted[:2], "x": 900, "y": 0},
        {"id": "g3", "label": "Waiting on the stair", "members": [keys[2], keys[3]], "x": 24, "y": 130}]
    board["discarded"] = [binned]
    board["picks"] = {"g2": [pick]} if pick else {}
    board["notes"] = [{"id": "n1", "text": "Sticky words stay on the canvas", "colour": "pink", "x": 1120, "y": 140, "in": "g2"}]
    start = themes_ai.revise_start(read, board)

    # ── B. the applier, on a plain board
    def run(ops):
        after, applied, refused, info = themes_ai.revise_ops(start, ops)
        return {"revised": dict(after, made=info["made"], gone=info["gone"]), "applied": applied, "refused": refused,
                "changed": themes_ai._structure(after) != themes_ai._structure(start)}

    def groups_of(result):
        return {g["id"]: g for g in (result.get("revised") or {}).get("groups") or []}

    titled = run([{"op": "retitle", "label": "g2", "title": "Five years \u2014 unsaid; still"}])
    noted = run([{"op": "note", "label": "g3", "note": "Waiting\nis the point;  the stair is where"}])
    check("180: retitle gives a label a title as the canvas keeps one, note writes its note afresh",
          groups_of(titled)["g2"]["label"] == "Five years, unsaid, still" and titled["changed"]
          and groups_of(noted)["g3"]["note"] == "Waiting is the point, the stair is where"
          and groups_of(noted)["g1"]["note"] == "The early walks set the day.")
    moved = run([{"op": "move", "items": [keys[9], keys[10]], "to": "g2"}])
    lifted = run([{"op": "move", "items": ["g3"], "to": "g2"}])
    out = run([{"op": "move", "items": [keys[0], "g3"], "to": None}])
    check("180: move takes statements into a label, a label in as a sub-theme, and either out to Not placed",
          groups_of(moved)["g2"]["members"] == quoted[:2] + [keys[9], keys[10]]
          and "g3" in groups_of(lifted)["g2"]["members"] and "g3" not in groups_of(lifted)["g1"]["members"]
          and groups_of(out)["g1"]["members"] == [keys[1]] and "g3" in groups_of(out)
          and not any("g3" in g["members"] for g in groups_of(out).values()))
    made = run([{"op": "make", "ref": "new1", "title": "Who gets up first", "inside": None, "members": [keys[9], keys[10]]},
                {"op": "move", "items": [keys[11]], "to": "new1"},
                {"op": "make", "title": "Cracking first", "inside": "g1", "members": [keys[1]]}])
    check("180: make makes a PET with its members, a later operation names it by its ref, and a sub-theme sits inside its PET",
          groups_of(made)["g4"]["label"] == "Who gets up first" and groups_of(made)["g4"]["members"] == [keys[9], keys[10], keys[11]]
          and groups_of(made)["g5"]["members"] == [keys[1]] and "g5" in groups_of(made)["g1"]["members"]
          and keys[1] not in groups_of(made)["g1"]["members"] and made["revised"]["made"] == ["g4", "g5"])
    merged = run([{"op": "merge", "label": "g3", "into": "g2"}])
    check("180: merge moves every member into the other label, takes the first away and says where its members went",
          "g3" not in groups_of(merged) and groups_of(merged)["g2"]["members"] == quoted[:2] + [keys[2], keys[3]]
          and "g3" not in groups_of(merged)["g1"]["members"] and merged["revised"]["gone"] == {"g3": "g2"})
    apart = run([{"op": "apart", "label": "g3", "to": "parent"}])
    loose = run([{"op": "apart", "label": "g3", "to": "unplaced"}])
    check("180: apart gives a sub-theme's members to its PET in its place, or with unplaced to Not placed",
          groups_of(apart)["g1"]["members"] == [keys[0], keys[1], keys[2], keys[3]] and apart["revised"]["gone"] == {"g3": "g1"}
          and groups_of(loose)["g1"]["members"] == [keys[0], keys[1]] and loose["revised"]["gone"] == {"g3": None}
          and not any(keys[2] in g["members"] for g in groups_of(loose).values()))
    if pick:
        # the quote is its first statement's own, so it goes with that statement (198)
        picked = run([{"op": "move", "items": [quoted[0]], "to": "g1"}, {"op": "pick", "label": "g1", "quotes": [pick]}])
        wrong = run([{"op": "pick", "label": "g3", "quotes": [pick]}])
        other = run([{"op": "move", "items": [quoted[2]], "to": "g1"}, {"op": "pick", "label": "g1", "quotes": [pick]}])
        check("180: pick sets the quote that carries a label from the quotes of the statements under it, and no other",
              picked["revised"]["picks"]["g1"] == [pick] and picked["revised"]["picks"]["g2"] == [pick]
              and wrong["refused"] == [themes_ai.UNKNOWN_QUOTE] and not wrong["changed"])
        check("198: a label's quotes to pick are its statements' own, so another statement's quote on the row is refused",
              other["refused"] == [themes_ai.UNKNOWN_QUOTE] and "g1" not in other["revised"]["picks"],
              str(other["refused"]))
    else:
        skip("180: pick", "the demo has no key quote on row 13")
    refusals = run([{"op": "move", "items": [f"{DEMO_SHEET}:99:0"], "to": "g1"},
                    {"op": "retitle", "label": "g9", "title": "Nowhere"},
                    {"op": "move", "items": [binned], "to": "g1"},
                    {"op": "discard", "items": [keys[0]]},
                    {"op": "edit", "key": keys[0], "text": "New words"},
                    {"op": "move", "items": ["n1"], "to": "g2"},
                    {"op": "move", "items": ["g1"], "to": "g3"},
                    "retitle g1",
                    {"op": "retitle", "label": "g1", "title": ""}])
    check("180: an operation naming a key, a label or a sticky note not on the board, the bin, a statement's words, a loop or nonsense is refused",
          refusals["refused"] == [themes_ai.UNKNOWN_STATEMENT, themes_ai.UNKNOWN_LABEL, themes_ai.UNKNOWN_STATEMENT,
                                  themes_ai.NOT_DONE, themes_ai.NOT_DONE, themes_ai.UNKNOWN_LABEL, themes_ai.INSIDE_ITSELF,
                                  themes_ai.UNREADABLE, themes_ai.UNREADABLE]
          and not refusals["changed"] and refusals["applied"] == [], str(refusals["refused"]))
    whole = run([{"op": "move", "items": [keys[9], f"{DEMO_SHEET}:99:0"], "to": "g2"},
                 {"op": "retitle", "label": "g2", "title": "Five years of the unsaid"}])
    check("180: an operation is refused whole and the rest stand, and the change says plainly what it did",
          groups_of(whole)["g2"]["members"] == quoted[:2] and groups_of(whole)["g2"]["label"] == "Five years of the unsaid"
          and whole["refused"] == [themes_ai.UNKNOWN_STATEMENT]
          and themes_ai.change_line(whole["applied"], start) == "Retitled 'A house that holds two' as 'Five years of the unsaid'.",
          themes_ai.change_line(whole["applied"], start))
    check("180: a change that applies nothing says nothing was changed", themes_ai.change_line([], start) == themes_ai.NOTHING_CHANGED)
    long = "Please take the house theme and split it into the rooms and the garden, keeping the bed in the rooms"
    check("180: the revision kept before is named Before: and his request on one line, cut at a word",
          themes_ai.revision_name("  Retitle\nthe  house  ") == "Before: Retitle the house"
          and themes_ai.revision_name(long).startswith("Before: Please take the house theme")
          and themes_ai.revision_name(long).endswith("…") and len(themes_ai.revision_name(long)) <= 8 + 81)
