from __future__ import annotations

import json
import shutil
from pathlib import Path

import ai_suggest as ai_mod
import workbook as wb_mod

from . import support
from .support import DEMO_QUESTION, DEMO_SHEET, check, demo_copy, demo_sheet, skip
import idiograph_routes


def test_ai_revise(scratch):
    print("\n77. AI revise: a request in his own words on the board, answered with operations, a revision kept "
          "before the change, one step of undo, and the thread kept on the board (180)")
    import subprocess
    import server as server_mod
    import themes as themes_mod
    import themes_ai

    js = support.text("apps/idiograph/static/themes.js")
    fn = lambda name: js.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in js else ""
    flat = lambda text: " ".join(str(text).split())
    opus = ai_mod.model_name("claude-opus-5-5")

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
    texts = {c["key"]: c["text"] for c in read["cards"]}
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

    # ── B. the prompts
    system = themes_ai.revise_system(DEMO_QUESTION)
    said_system = flat(system)
    rules = themes_ai.guidance_items(themes_ai.RULES)
    check("180: the system prompt carries the research question, what a theme is, the rules for a theme and the task",
          themes_ai.REVISE_INTRO in system and flat(themes_ai.question_block(DEMO_QUESTION)) in said_system
          and flat(themes_ai.guidance_prose(themes_ai.WHAT_A_THEME))[:80] in said_system
          and all(f"{n}. {t}" in system for n, t in rules) and len(rules) >= 10
          and "You make the change he asks for and nothing else." in said_system)
    check("180: it carries the GETs-free part of the guidance alone, never the reviewer's questions",
          themes_ai.guidance_items(themes_ai.QUESTIONS)[0][1] not in system
          and "group experiential" not in system.lower() and "GET" not in system)
    check("180: it asks for operations and never a whole board, names each one, and keeps the bin and the words out",
          "Answer with operations on the board, never with a whole board." in said_system
          and all(f'"op": "{op}"' in system for op in themes_ai.REVISE_OPS)
          and "Never put a statement in the bin or take one out of it, never change a statement's words, and never "
              "name a statement that is not on the board." in said_system
          and "make no operation for that part, change nothing else in its place, and say why" in said_system
          and "Operations run in order, each on the board as the ones before it left it." in said_system)
    thread = [{"by": "analyst", "text": "Give the stair its own title", "at": "a"},
              {"by": "ai", "text": "Retitled 'Stairs' as 'Waiting on the stair'.", "at": "b", "model": opus}]
    request = "Retitle the house PET and give who gets up first a PET of its own"
    user = themes_ai.revise_user(themes_ai.revise_board(read, board), thread, request)
    check("180: the user prompt sets out each label by its id with its title, note, statements, quotes and picks, sub-themes nested",
          "Theme g1: Mornings that belong to the dog (1 sub-theme · 4 statements)" in user
          and "  Note: The early walks set the day." in user and "  Sub-theme g3: Waiting on the stair (2 statements)" in user
          and f"  - {keys[0]} ({DEMO_SHEET}, " in user and f"    - {keys[2]} ({DEMO_SHEET}, " in user
          and (not pick or (f"    quote {pick} " in user and f"  Picked to carry it: {pick}" in user))
          and user.index("Theme g1") < user.index("Sub-theme g3") < user.index("Not placed:"))
    check("180: then the statements not placed, the thread so far, oldest first, and his request last",
          f"- {keys[9]} ({DEMO_SHEET}, " in user.split("Not placed:", 1)[1]
          and "He asked: Give the stair its own title" in user
          and "The answer: Retitled 'Stairs' as 'Waiting on the stair'." in user
          and f"He asks now: {request}" in user and user.rstrip().endswith("Change the board.")
          and user.index("Not placed:") < user.index("He asked:") < user.index("He asks now:"))
    check("180: no sticky note, no statement in the bin and no interviewer's note goes in either prompt",
          "Sticky words stay on the canvas" not in system + user and texts[binned] not in system + user
          and binned not in user and "Pressed too soon" not in system + user)
    bare = themes_ai.revise_user(themes_ai.revise_board(read, themes_mod.blank_version(read["cards"])), [], "Group these")
    check("180: a board with no labels and no thread says so, and carries no thread part",
          "There are no labels yet." in bare and "His requests so far" not in bare)

    # ── C. the parser and the applier, on a plain board
    def run(ops, said="Done."):
        return themes_ai.parse_revise(json.dumps({"operations": ops, "said": said}), start)

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
          and not refusals["changed"] and "revised" not in refusals and refusals["applied"] == [], str(refusals["refused"]))
    whole = run([{"op": "move", "items": [keys[9], f"{DEMO_SHEET}:99:0"], "to": "g2"},
                 {"op": "retitle", "label": "g2", "title": "Five years of the unsaid"}])
    check("180: an operation is refused whole and the rest stand, and the answer says what changed and what was left out",
          groups_of(whole)["g2"]["members"] == quoted[:2] and groups_of(whole)["g2"]["label"] == "Five years of the unsaid"
          and whole["said"] == "Retitled 'A house that holds two' as 'Five years of the unsaid'. "
                               "Left out one change, which named a statement not on the board.", whole["said"])
    check("180: every operation left out says nothing was changed, with what was left out",
          refusals["said"].startswith("Nothing was changed. Left out nine changes: ")
          and "two named a statement not on the board" in refusals["said"] and ", " in refusals["said"]
          and themes_ai.refused_line([]) == "")
    kept = run([{"op": "retitle", "label": "g2", "title": "Five years of the unsaid"}],
               said="Retitled 'A house that holds two' as 'Five years of the unsaid' \u2014 nothing else; done.")
    declined = themes_ai.parse_revise(json.dumps({"operations": [], "said": "Statements keep their own words here."}), start)
    check("180: with every operation standing the answer's own words go, cleaned, and a request it declines changes nothing",
          kept["said"] == "Retitled 'A house that holds two' as 'Five years of the unsaid', nothing else, done."
          and declined == {"applied": [], "refused": [], "said": "Statements keep their own words here.", "changed": False})
    check("180: an answer that is not JSON, that ran out of room, or that carries no operations and no words is one line",
          themes_ai.parse_revise("Sure, here is the board.", start) == {"error": themes_ai.NOT_JSON}
          and themes_ai.parse_revise('{"operations": [', start, truncated=True) == {"error": ai_mod.TOO_LONG}
          and themes_ai.parse_revise(json.dumps({"groups": [{"label": "A whole board"}]}), start) == {"error": themes_ai.NO_CHANGES}
          and themes_ai.parse_revise("```json\n" + json.dumps({"operations": [], "said": "No change."}) + "\n```", start)["said"] == "No change.")
    long = "Please take the house theme and split it into the rooms and the garden, keeping the bed in the rooms"
    check("180: the revision kept before is named Before: and his request on one line, cut at a word",
          themes_ai.revision_name("  Retitle\nthe  house  ") == "Before: Retitle the house"
          and themes_ai.revision_name(long).startswith("Before: Please take the house theme")
          and themes_ai.revision_name(long).endswith("…") and len(themes_ai.revision_name(long)) <= 8 + 81)

    # ── D. the route, through a transport that stands in for the provider
    real = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, ai_mod.find_key, ai_mod.http_call)
    config_path = scratch / "ai-revise-config.json"
    path = themes_mod.themes_path(work)
    sent, replies = [], []

    def wire(method, url, headers, payload, timeout):
        sent.append(payload)
        reply = replies.pop(0) if replies else ""
        status, text = reply if isinstance(reply, tuple) else (200, reply)
        return status, json.dumps({"content": [{"type": "text", "text": text}], "stop_reason": "end_turn"})

    def settings(**extra):
        config_path.write_text(json.dumps({"ai_suggest": True, "ai_provider": "anthropic", "model": "claude-haiku-4-5",
                                           "pets_provider": "anthropic", "pets_model": "claude-opus-5-5", **extra}),
                               encoding="utf-8")

    def snapshot(folder):
        return {str(p): p.read_bytes() for p in sorted(Path(folder).rglob("*")) if p.is_file()}

    def ask(text):
        return idiograph_routes.api_themes_ai({"workbook": str(work), "op": "revise", "version": "v1", "text": text})

    def stored():
        return json.loads(path.read_text(encoding="utf-8"))["boards"][0]

    ops = [{"op": "retitle", "label": "g2", "title": "Five years of things left unsaid"},
           {"op": "move", "items": [quoted[2]], "to": "g2"},
           {"op": "make", "ref": "new1", "title": "Who gets up first", "inside": None, "members": [keys[9], keys[10]]},
           {"op": "move", "items": [keys[11]], "to": "new1"}]
    answer = "Retitled 'A house that holds two' as 'Five years of things left unsaid' and moved one statement into it."
    try:
        server_mod.CONFIG_PATH = config_path
        server_mod.ROOT_OVERRIDE = str(root)
        ai_mod.find_key = lambda *a, **kw: "k-test"
        ai_mod.http_call = wire
        settings()
        opened = idiograph_routes.api_themes({"workbook": str(work)})
        body = {**{k: x for k, x in opened["version"].items() if k != "v"}, "cards": board["cards"], "groups": board["groups"], "discarded": board["discarded"],
                "picks": board["picks"], "notes": board["notes"]}
        idiograph_routes.api_themes_save({"workbook": str(work), "version": body})
        check("180: /api/themes says a server takes a revise, and a board with no thread carries an empty one",
              opened.get("revisable") is True and opened.get("revise") == [])
        workbook_before = work.read_bytes()
        was = stored()
        replies[:] = [json.dumps({"operations": ops, "said": answer})]
        got = ask(request)
        call = sent[-1]
        call_user = call["messages"][0]["content"]
        check("180: Send asks the PETs model once, with the board as the file holds it and his request",
              len(sent) == 1 and call["model"] == "claude-opus-5-5" and themes_ai.REVISE_INTRO in call["system"]
              and f"He asks now: {request}" in call_user and "Theme g1: Mornings that belong to the dog" in call_user
              and "Sticky words stay on the canvas" not in call["system"] + call_user
              and "Pressed too soon" not in call["system"] + call_user and texts[binned] not in call_user)
        now = stored()
        rev = now["history"][-1] if now.get("history") else {}
        check("180: the board as it stood is kept first as a revision named Before: and his request, through add_revision",
              rev.get("name") == themes_ai.revision_name(request) and rev.get("auto") is False
              and rev["state"]["groups"] == was["groups"] and rev["state"]["picks"] == was["picks"]
              and got.get("revision", {}).get("name") == rev.get("name")
              and got.get("history", [{}])[0].get("name") == rev.get("name"))
        check("180: the server applies nothing to the board itself, the page lands the change, and the workbook is untouched",
              {k: now[k] for k in ("cards", "groups", "discarded", "picks", "notes")}
              == {k: was[k] for k in ("cards", "groups", "discarded", "picks", "notes")}
              and work.read_bytes() == workbook_before)
        revised = got.get("revised") or {}
        by_id = {g["id"]: g for g in revised.get("groups") or []}
        check("180: the answer carries the labels and picks afterwards, the new label made, and the answer's line",
              by_id.get("g2", {}).get("label") == "Five years of things left unsaid"
              and by_id["g2"]["members"] == quoted[:3] and by_id.get("g4", {}).get("members") == [keys[9], keys[10], keys[11]]
              and revised.get("made") == ["g4"] and got["refused"] == []
              and got["revise"]["by"] == "ai" and got["revise"]["text"] == answer and got["revise"]["model"] == opus)

        # the page lands it and saves the board with the thread, as Send does
        landed = dict(body, groups=[dict(g, x=0, y=0) for g in revised["groups"]], picks=revised["picks"],
                      revise=[{"by": "analyst", "text": request, "at": "2026-10-05T19:00:00+01:00"}, got["revise"]])
        idiograph_routes.api_themes_save({"workbook": str(work), "version": landed})
        reopened = idiograph_routes.api_themes({"workbook": str(work)})
        check("180: the thread is kept on the board as revise, saved with it, and an open hands it back",
              stored().get("revise") == reopened.get("revise") and [line["by"] for line in reopened["revise"]] == ["analyst", "ai"]
              and reopened["revise"][1]["model"] == opus and reopened["revise"][0]["text"] == request)
        idiograph_routes.api_themes_save({"workbook": str(work), "version": {k: v for k, v in landed.items() if k != "revise"}})
        check("180: a save from a page that sends no thread keeps the file's", stored().get("revise") == reopened["revise"])

        sent.clear()
        replies[:] = [json.dumps({"operations": [{"op": "retitle", "label": "g4", "title": "Cracking first, every morning"},
                                                 {"op": "merge", "label": "g7", "into": "g2"}],
                                  "said": "Retitled and merged."})]
        second = ask("Name the new one for who cracks first, and fold the stair into the house")
        second_user = sent[-1]["messages"][0]["content"]
        check("180: the next request sends the thread so far, and a second change keeps a second revision",
              "His requests so far on this board, oldest first, each with the answer." in second_user
              and f"He asked: {request}" in second_user and f"The answer: {answer}" in second_user
              and second.get("refused") == [themes_ai.UNKNOWN_LABEL]
              and second["revise"]["text"] == "Retitled 'Who gets up first' as 'Cracking first, every morning'. "
                                              "Left out one change, which named a label not on the board."
              and [r["name"] for r in stored()["history"]][-2:] == [themes_ai.revision_name(request),
                                                                   themes_ai.revision_name("Name the new one for who cracks first, and fold the stair into the house")])

        before = snapshot(root)
        replies[:] = [json.dumps({"operations": [], "said": "A statement keeps its own words, so nothing was changed."})]
        declined = ask("Rewrite the words of the first statement")
        check("180: a request it declines keeps no revision, carries no change and writes nothing",
              "revised" not in declined and declined["revise"]["text"] == "A statement keeps its own words, so nothing was changed."
              and snapshot(root) == before)
        replies[:] = [(500, "")]
        failed = ask("Retitle the house")
        replies[:] = ["Here is a new board for you."]
        unread = ask("Retitle the house")
        check("180: a failure, or an answer that cannot be read, is one line, keeps no revision and writes nothing",
              "error" in failed and unread == {"error": themes_ai.NOT_JSON} and snapshot(root) == before)
        empty = ask("   ")
        settings(ai_suggest=False)
        count = len(sent)
        off = ask("Retitle the house")
        check("180: an empty request and the switch off ask nothing", empty == {"error": themes_ai.NO_REQUEST}
              and off == {"error": themes_ai.OFF} and len(sent) == count and snapshot(root) == before)
        settings()
        asked = {"at": "2026-10-05T19:05:00+01:00", "model": opus, "items": [
            {"about": None, "question": "Does the board answer the research question?", "rule": "", "why": "w", "state": "open"}]}
        idiograph_routes.api_themes_save({"workbook": str(work), "version": dict(landed, review=asked)})
        case = server_mod.display_case(wb_mod.case_folder(work).name)
        dup = themes_mod.version_op(work, "duplicate", {"id": "v1"}, case)
        copy = json.loads(path.read_text(encoding="utf-8"))["boards"][1]
        check("180: a duplicate carries the thread, the board's own story, and leaves the review behind",
              dup["revise"] == reopened["revise"] and copy.get("revise") == reopened["revise"] and "review" not in copy
              and stored().get("review", {}).get("items") == asked["items"])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, ai_mod.find_key, ai_mod.http_call = real
    kept_lines = themes_mod.normalise({"revise": [{"by": "analyst", "text": f"line {n}"} for n in range(45)] + [{"by": "x", "text": "y"}]})
    check("180: normalise keeps forty lines of the thread, the oldest going past it, and a board with none carries none",
          [line["text"] for line in kept_lines["revise"]] == [f"line {n}" for n in range(5, 45)]
          and "revise" not in themes_mod.normalise({}) and "revise" not in themes_mod.STATE_KEYS)

    # ── E. the page: the tab, the box, Send and the landing
    drawn, send = fn("thReviseDraw"), fn("thReviseSend")
    check("180: with AI features off the tab is hidden and draws nothing (100)",
          drawn.index("if (thAiOn()) {") < drawn.index("th-revise-thread")
          and "Turn on AI suggestions" not in drawn and 'data-review-settings' not in drawn
          and "} else {" not in drawn and drawn.count("TH_SPARK_ICON") == 1)
    check("180: a failure is one line under the thread, his words kept in the box, and the box keeps its words as the tab redraws",
          "if (TH.reviseSaid) html += `<p class=\"th-names-note failed\">${esc(TH.reviseSaid)}</p>`;" in drawn
          and "${esc(TH.reviseText || '')}</textarea>" in drawn
          and "if (e.target && e.target.id === 'th-revise-box' && !TH.revising) TH.reviseText = e.target.value;" in js
          and "if (e.key === 'Enter' && MOD(e)) { e.preventDefault(); thReviseSend(); }" in js
          and "if (e.target.closest('[data-revise-send]')) { thReviseSend(); return; }" in js)
    check("180: Send saves first, asks through the route with op revise, and an old server gets the restart line and is asked nothing",
          send.index("await thFlush();") < send.index("api(thAiPath(), { workbook: path, op: 'revise', version: board, text: words })")
          and "if (!TH.revisable) { TH.reviseSaid = RESTART_LINE;" in send
          and send.index("if (!TH.revisable)") < send.index("api(thAiPath()")
          and "refusedAs(err, 'unknown_op') ? RESTART_LINE : err.message" in send
          and "TH.revisable = !!data.revisable;" in fn("themesOpen"))
    check("180: the change lands as a drop, one step of undo for the whole of it, the labels shown landing, then saved",
          send.index("const before = thSnap(v, TH.removed);") < send.index("thReviseTake(v, data.revised, thSize)")
          < send.index("thDone(before, t('themes.step.revised_ai'), { settle: landed.settle, stay: true, was, from, lifted: landed.lifted, labels: landed.labels });")
          and send.count("thDone(") == 1 and "thStep(" not in send
          and "if (Array.isArray(data.history)) TH.history = data.history;" in send
          and send.index("thDone(") < send.index("thReviseKeep(v, words, data.revise, at);") < send.index("thSoon();")
          and "TH.reviseText = '';" in send)
    check("180: the canvas waits while it is asked, and a failure changes nothing on it",
          "TH.busy = true;" in send and "TH.busy = false;" in send.split("finally", 1)[1]
          and send.index("if (said) {") < send.index("const before = thSnap(")
          and "thMakeWay(v, size, moving," in fn("thReviseTake"))
    check("180: the thread is saved with the board and read back on a load, and null from a server before it",
          "if (Array.isArray(v.revise) && v.revise.length) out.revise = JSON.parse(JSON.stringify(v.revise));" in fn("thBody")
          and "revise: Array.isArray(data.revise) ? JSON.parse(JSON.stringify(data.revise)) : null," in fn("thLoad")
          and "revise" not in fn("thSnap"))

    node = shutil.which("node")
    if not node:
        return skip("180: the landing in node", "no node on this machine")
    script = scratch / "ai-revise.js"
    script.write_text(support.i18n_js() + js + r"""
const size = (item) => (String(item).startsWith('g') ? { w: 120, h: 24 } : { w: 200, h: 80 });
const keep = (x) => JSON.parse(JSON.stringify(x));
const scene = () => {
  const v = { cards: {}, groups: [], discarded: ['a:10:0'], picks: {}, stickies: [] };
  for (const [k, x, y] of [['a:1:0', 0, 40], ['a:2:0', 210, 40], ['a:3:0', 0, 130], ['a:4:0', 600, 40], ['a:5:0', 810, 40],
    ['a:6:0', 0, 440], ['a:7:0', 210, 440], ['a:8:0', 1200, 40], ['a:9:0', 1200, 140], ['a:10:0', 1600, 40]]) v.cards[k] = { x, y, text: 't' };
  v.groups = [{ id: 'g1', label: 'One', members: ['a:1:0', 'a:2:0', 'a:3:0'], x: 0, y: 0 },
    { id: 'g2', label: 'Two', members: ['a:4:0', 'a:5:0'], x: 600, y: 0 },
    { id: 'g3', label: 'Three', members: ['a:6:0', 'a:7:0'], x: 0, y: 400 }];
  v.stickies = [{ id: 'n1', text: 'mine', colour: 'yellow', x: 820, y: 140, in: 'g2' }];
  thLayout(v, size, null);
  return v;
};
const out = {};
const inside = (a, b, m = 0) => a.x >= b.x + m && a.y >= b.y + m && a.x + a.w <= b.x + b.w - m && a.y + a.h <= b.y + b.h - m;
const box = (v, k) => ({ x: v.cards[k].x, y: v.cards[k].y, w: 200, h: 80 });
let v = scene();
out.clean = thClashes(v, size).length;
const g3 = keep(thGroup(v, 'g3'));
const before = thSnap(v, new Set());
const landed = thReviseTake(v, { groups: [
  { id: 'g1', label: 'One', members: ['a:1:0', 'a:3:0', 'a:8:0'] },
  { id: 'g3', label: 'Three, retitled', members: ['a:6:0', 'a:7:0'] },
  { id: 'g4', label: 'Four', members: ['a:9:0', 'a:5:0'] }], picks: {}, made: ['g4'], gone: { g2: null } }, size);
thSettle(v, size, landed.settle, {}, landed.labels, TH_PASSES, true);
let lay = thLayout(v, size, null);
out.labels = landed.labels;
out.cards = landed.cards.slice().sort();
out.lifted = [...landed.lifted].sort();
out.g3 = [thGroup(v, 'g3').x === g3.x && thGroup(v, 'g3').y === g3.y, v.cards['a:6:0'].x, v.cards['a:6:0'].y];
out.joined = inside(box(v, 'a:8:0'), lay.g1.frame);
out.under = v.cards['a:8:0'].y > v.cards['a:3:0'].y;
out.left = !thMeets(box(v, 'a:2:0'), lay.g1.frame, 0);
out.newClear = v.groups.filter((g) => g.id !== 'g4' && thParents(v)[g.id] === undefined).every((g) => !thMeets(lay.g4.frame, lay[g.id].frame, 0));
out.from = landed.from.g4 ? true : false;
out.sticky = v.stickies[0].in === undefined;
out.bin = keep([v.discarded, v.cards['a:10:0']]);
out.clashes = thClashes(v, size);
thPut(v, before);
out.undone = keep([v.groups.map((g) => [g.id, g.label, g.members]), v.cards['a:8:0'], v.stickies[0].in, v.cards['a:2:0']]);
v = scene();
const two = thReviseTake(v, { groups: [
  { id: 'g1', label: 'One', members: ['a:3:0', 'g5', 'a:4:0', 'a:5:0'] },
  { id: 'g3', label: 'Three', members: ['a:7:0'] },
  { id: 'g5', label: 'Five', members: ['a:1:0', 'a:2:0', 'a:6:0'] }], picks: { g1: ['a:4:0'] }, made: ['g5'], gone: { g2: 'g1' } }, size);
thSettle(v, size, two.settle, {}, two.labels, TH_PASSES, true);
lay = thLayout(v, size, null);
out.sub = [thParents(v).g5, inside(lay.g5.frame, lay.g1.frame), inside(box(v, 'a:4:0'), lay.g1.frame), v.stickies[0].in, keep(v.picks)];
out.subClashes = thClashes(v, size);
const tv = { revise: null };
for (let i = 0; i < 25; i += 1) thReviseKeep(tv, `ask ${i}`, { text: `answer ${i}`, at: 'b', model: 'M' }, 'a');
out.kept = [tv.revise.length, tv.revise[0].text, tv.revise[39], Object.keys(thBody(Object.assign(scene(), { revise: tv.revise }), { id: 'v1', name: 'B' })).includes('revise'),
  Object.keys(thBody(scene(), { id: 'v1', name: 'B' })).includes('revise')];
console.log(JSON.stringify(out));
""", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("180: the landing runs in node", False, run.stderr.strip()[:300])
    out = json.loads(run.stdout)
    check("180: in node, a label the answer kept stays where it stands, retitled in place, and the changed labels are named",
          out["clean"] == 0 and out["g3"] == [True, 0, 440] and out["labels"] == ["g1", "g3", "g4"], str(out["labels"]))
    check("180: in node, a statement moved into a PET lands under what it holds, inside its frame",
          out["joined"] and out["under"] and "a:8:0" in out["cards"])
    check("180: in node, a new PET's statements gather on a spot clear of every other PET, and what left slides clear",
          out["newClear"] and out["left"] and out["from"] and out["clashes"] == [], str(out["clashes"]))
    check("180: in node, a sticky note in a label taken away goes where its members went, and the bin stays as it was",
          out["sticky"] and out["bin"] == [["a:10:0"], {"x": 1600, "y": 40, "text": "t"}] and out["sub"][3] == "g1")
    check("180: in node, one undo puts every label, member, place and note back",
          out["undone"] == [[["g1", "One", ["a:1:0", "a:2:0", "a:3:0"]], ["g2", "Two", ["a:4:0", "a:5:0"]],
                             ["g3", "Three", ["a:6:0", "a:7:0"]]], {"x": 1200, "y": 40, "text": "t"}, "g2",
                            {"x": 210, "y": 40, "text": "t"}], str(out["undone"]))
    check("180: in node, a new sub-theme gathers inside its PET, a merge's members land in the PET, and nothing overlaps",
          out["sub"][0] == "g1" and out["sub"][1] and out["sub"][2] and out["sub"][4] == {"g1": ["a:4:0"]}
          and out["subClashes"] == [], str(out["sub"]))
    check("180: in node, the thread keeps forty lines, the oldest going, and a save sends it only when there is one",
          out["kept"][0] == 40 and out["kept"][1] == "ask 5" and out["kept"][2]["text"] == "answer 24"
          and out["kept"][3] is True and out["kept"][4] is False, str(out["kept"][:2]))
