from __future__ import annotations

import json

from .support import DEMO_QUESTION, check, demo_copy
import idiograph_routes


def test_review_rounds(scratch):
    print("\n70. A board's AI review rounds, revise thread and New AI board's mark from before 11 November 2026, when "
          "the three went (aiout): the board opens and saves as an ordinary one, and what they left stays in the file "
          "as it was, read by nothing")
    import gets as gets_mod
    import server as server_mod
    import themes as themes_mod

    root = scratch / "a070-root"
    work = demo_copy(root, "Wren", "Wren - EN & ES.xlsx")
    (root / "idiograph-project.json").write_text(json.dumps({"name": "Scratch", "research_question": DEMO_QUESTION}),
                                                 encoding="utf-8")
    read = themes_mod.read_cards(work)
    keys = [c["key"] for c in read["cards"]]

    # an invented board as a page before aiout left it: a review of two rounds, one question with its exchange and
    # one about a statement, a revise thread, the reasons a New AI board gave and its mark, odd shapes among them
    review = {"at": "2026-11-02T10:05:00", "model": "Haiku 4.5", "items": [
        {"about": "g1", "question": "Does the title reach every walk?", "rule": "5", "why": "Two walks are at dusk.",
         "state": "considered", "thread": [{"by": "analyst", "text": "Dusk counts.", "at": "2026-11-02T10:07:00"},
                                           {"by": "ai", "text": "Then the title holds.", "at": "2026-11-02T10:07:05",
                                            "model": "Haiku 4.5"}]},
        {"about": keys[3], "question": "Is this statement left out on purpose?", "rule": "4", "why": "It is alone.",
         "state": "open", "extra": "a field no reader knew"}],
        "earlier": [{"at": "2026-11-01T09:00:00", "model": "Haiku 4.5",
                     "items": [{"about": None, "question": "Are there more PETs than the case needs?", "rule": "1",
                                "why": "Six PETs.", "state": "dismissed"}]}] * 60}
    revise = [{"by": "analyst", "text": "Merge the two walk themes.", "at": "2026-11-03T11:00:00"},
              {"by": "ai", "text": "Merged them.", "at": "2026-11-03T11:00:09", "model": "Opus 5.5"}]
    board = themes_mod.blank_version(read["cards"])
    board["groups"] = [{"id": "g1", "label": "Walks at either end of the day", "members": [keys[0], keys[1]], "x": 0, "y": 0}]
    board.update(id="v1", name="Board 1", review=review, revise=revise,
                 ai={"discarded": {keys[2]: "It says nothing of the walks."}},
                 made={"by": "ai", "model": "Haiku 4.5", "from": "all statements", "at": "2026-11-01T08:00:00"},
                 note="Proposed by Haiku 4.5 from all statements on 1 November 2026 at 08:00, up to 5 PETs.")
    board["discarded"] = [keys[2]]
    path = themes_mod.themes_path(work)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema": 2, "case": "Wren", "workbook": work.name, "current": "v1", "boards": [board]},
                               ensure_ascii=False), encoding="utf-8")
    stored = lambda: json.loads(path.read_text(encoding="utf-8"))["boards"]

    kept = (server_mod.ROOT_OVERRIDE,)
    try:
        server_mod.ROOT_OVERRIDE = str(root)
        opened = idiograph_routes.api_themes({"workbook": str(work)})
        check("70: the board opens with no error, an ordinary board: its menu says nothing of an AI, and the screen gets "
              "no review or revise thread",
              opened["version"]["id"] == "v1" and "with_ai" not in opened["version"]
              and not any(b.get("with_ai") for b in opened["versions"])
              and "review" not in opened and "revise" not in opened
              and opened["discard_reasons"] == {keys[2]: "It says nothing of the walks."}, str(opened["version"]))
        body = {**opened["version"], "cards": {c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]}
                                               for c in opened["cards"]},
                "groups": [{"id": "g1", "label": "Walks at either end of the day", "members": [keys[0], keys[1], keys[4]],
                            "x": 0, "y": 0}],
                "discarded": [keys[2]], "picks": {}, "ai": {"discarded": {keys[2]: "It says nothing of the walks."}}}
        idiograph_routes.api_themes_save({"workbook": str(work), "version": body})
        saved = stored()[0]
        check("70: a save from the page, which sends neither, keeps the review rounds and the revise thread exactly as "
              "the file held them, all sixty-one rounds and the field no reader knew",
              saved["review"] == review and saved["revise"] == revise and len(saved["review"]["earlier"]) == 60
              and saved["groups"][0]["members"] == [keys[0], keys[1], keys[4]])
        check("70: New AI board's mark goes with that save, so the board stays an ordinary one",
              "made" not in saved and themes_mod.made_said(saved) is None)
        idiograph_routes.api_themes_versions({"workbook": str(work), "op": "duplicate", "id": "v1"})
        boards = stored()
        check("70: a duplicate carries neither, and the board it was made from keeps both",
              len(boards) == 2 and "review" not in boards[1] and "revise" not in boards[1]
              and boards[0]["review"] == review and boards[0]["revise"] == revise)
        trimmed = themes_mod.drop_cards(boards[0], [keys[3]])
        check("70: a statement taken off the board leaves the review as it was, its question about it too",
              trimmed["review"] == review and keys[3] not in trimmed["cards"])
    finally:
        (server_mod.ROOT_OVERRIDE,) = kept

    # the GETs file: the same keys on a GETs board pass through, and the limit New AI board kept is read as nothing
    data = {"settings": {"minimum": 2, "one_per_pet": False, "cap": 7}, "cases": {}, "boards": []}
    gets_board = {"id": "b1", "name": "Board 1", "cards": {}, "groups": [], "discarded": [], "picks": {},
                  "review": review, "revise": revise}
    normal = gets_mod.normal(gets_board, data)
    check("70: a GETs board passes its review and revise thread through untouched, and the GETs limit is read as nothing",
          normal["review"] == review and normal["revise"] == revise
          and gets_mod.settings_of(data) == {"minimum": 2, "one_per_pet": False})
