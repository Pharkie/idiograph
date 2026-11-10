from __future__ import annotations

import json

import openpyxl

import ai_suggest as ai_mod

from .support import DEMO_SHEET, check
import idiograph_routes


def test_revise_room(scratch):
    print("\n140. AI revise held to its room, 14 October: past the route's room the PETs revise leaves out the key quotes "
          "of the statements lowest on the canvas first, then the thread's oldest lines, every statement, key, label and "
          "his request whole, and the answer's line in the thread says so, as the GETs revise's now does. Since the test "
          "review of 18 October the docs' words are review shots, and what is sent and what the thread keeps stay")
    import server as server_mod
    import themes as themes_mod
    import themes_ai

    question = "How do adults who take up dinghy sailing experience their first season on the water?"

    # ── A. an invented case on a made-up topic: Bryn, learning to sail a dinghy, eight turns, one
    # statement and its own key quote to each. The quotes run long, as in test 122, so leaving one
    # out saves more than the line saying so costs
    root = scratch / "revise-room"
    case = root / "Bryn"
    case.mkdir(parents=True, exist_ok=True)
    (root / "idiograph-project.json").write_text(json.dumps({"name": "First season", "research_question": question}),
                                                 encoding="utf-8")
    work = case / "Bryn - first season.xlsx"
    turns = [("00:01:10", "Rigging in the half light settles her before the club wakes",
              "I rig it before anyone else is up, the halyard cold in my hands and the club still dark, and by the time "
              "the others come down the slipway I am already somebody who knows what she is doing"),
             ("00:02:40", "The quiet of the slipway is hers alone for a while",
              "there is nobody on the slipway but me and the gulls, and the water is flat like it has not decided "
              "anything yet, and for half an hour nobody needs a single thing from me at all"),
             ("00:04:05", "She reads the wind on her face before any flag shows it",
              "my cheek knows before the burgee does, honestly, I feel it come round on the side of my face and I am "
              "already easing the sheet before anybody on the bank has seen the water darken"),
             ("00:05:30", "A gust is felt in the stomach first and then in the sheet",
              "it goes through my stomach first, a sort of drop, and only then do I feel it in the rope, and I have "
              "learnt to trust the stomach because the rope always tells me a second too late"),
             ("00:07:15", "The boat answers her weight like a second body",
              "it leans when I lean, it is like the boat has my back and my hips in it, and when I sit out it comes "
              "flat again under me as if we had agreed it between us before we ever left the beach"),
             ("00:08:50", "Trusting the hull came slower than trusting the sail",
              "the sail I trusted in a week but the hull took me months, I kept thinking the bottom of it was the "
              "only thing between me and the cold and it felt so thin under my feet for all of July"),
             ("00:10:20", "Capsizing once took the fear out of capsizing",
              "after the first swim it was fine, really, I came up laughing with the boat on its side next to me and "
              "the thing I had been dreading for a whole month was just cold water and a rope to pull on"),
             ("00:12:00", "Coming ashore she feels taller than when she left",
              "I walk up the beach a foot taller, wet to the knees and starving, and my husband says I look like "
              "somebody else entirely, and I think he is right, I think the sea has had a go at me")]
    book = openpyxl.Workbook()
    ws = book.active
    ws.title = DEMO_SHEET
    ws.append(["Name", "Timestamp", "Transcript", "Experiential statements", "Key quotes"])
    for at, statement, quote in turns:
        ws.append(["Bryn", at, f"Well, {quote}, and that is how the morning goes.", statement, f'"{quote}"'])
    book.save(work)
    book.close()
    read = themes_mod.read_cards(work)
    keys = [c["key"] for c in read["cards"]]
    texts = {c["key"]: c["text"] for c in read["cards"]}
    version = themes_mod.blank_version(read["cards"])
    spots = {keys[0]: (0, 40), keys[1]: (210, 40), keys[2]: (24, 170), keys[3]: (234, 170),
             keys[4]: (900, 40), keys[5]: (1110, 40), keys[6]: (1600, 40), keys[7]: (1600, 600)}
    for key, (x, y) in spots.items():
        version["cards"][key].update(x=x, y=y)
    version["groups"] = [
        {"id": "g1", "label": "Rigging before light", "members": [keys[0], keys[1], "g3"], "x": 0, "y": 0},
        {"id": "g2", "label": "A boat that answers", "members": [keys[4], keys[5]], "x": 900, "y": 0},
        {"id": "g3", "label": "Reading the wind", "members": [keys[2], keys[3]], "x": 24, "y": 130}]
    thread = [{"by": "analyst", "text": "Give the wind its own sub-theme", "at": "2026-10-14T09:00:00+01:00"},
              {"by": "ai", "text": "Made 'Reading the wind' inside 'Rigging before light'.", "at": "2026-10-14T09:01:00+01:00",
               "model": "stub-model on this machine"}]
    version["revise"] = thread
    request = "Move the capsize statement into the boat theme"
    own = "Retitled 'A boat that answers' as 'The boat as a second body'."
    answer = json.dumps({"operations": [{"op": "retitle", "label": "g2", "title": "The boat as a second body"}], "said": own})

    # a stub in place of the provider, never a real model: the local route's shape and Anthropic's
    sent = []

    def local_wire(method, url, headers, payload, timeout):
        sent.append({"url": url, "system": payload["messages"][0]["content"], "user": payload["messages"][1]["content"],
                     "max_tokens": (payload.get("options") or {}).get("num_predict")})
        return 200, json.dumps({"message": {"content": sent_reply[0]}, "done_reason": "stop"})

    def cloud_wire(method, url, headers, payload, timeout):
        sent.append({"url": url, "system": payload["system"], "user": payload["messages"][0]["content"],
                     "max_tokens": payload["max_tokens"]})
        return 200, json.dumps({"content": [{"type": "text", "text": sent_reply[0]}], "stop_reason": "end_turn"})

    sent_reply = [answer]
    local = {"provider": ai_mod.LOCAL, "model": "stub-model", "local_url": "http://127.0.0.1:8790"}
    board = themes_ai.revise_board(read, version)
    system = themes_ai.revise_system(question)
    whole = themes_ai.revise_user(board, thread, request)
    ys = {s["key"]: (s["x"], s["y"]) for s in themes_ai.board_statements(board)}
    check("140: the board a revise sends carries each statement's place on the canvas, placed or not",
          ys == spots and [s["key"] for s in themes_ai.board_statements(board)][-2:] == [keys[6], keys[7]], str(ys))

    # ── B. a small board goes whole
    got = themes_ai.revise(read, version, request, question, local, transport=local_wire)
    check("140: a small board goes whole on a local model's room, every quote with it, and the answer's line is its own words",
          len(sent) == 1 and sent[-1]["user"] == whole and sent[-1]["system"] == system
          and len(system) + len(whole) <= themes_ai.PROMPT_CEILING
          and all(f"quote {k} " in whole for k in keys) and "left out here for room" not in whole
          and got.get("said") == own and "trimmed" not in got and "dropped" not in got
          and sent[-1]["max_tokens"] == themes_ai.REVISE_MAX_TOKENS, str(got)[:200])

    # ── C. a forced ceiling: the lowest statement's quote first, then the next lowest
    one = themes_ai.revise_user(board, thread, request, frozenset({keys[7]}))
    ceiling = len(system) + len(one)
    sent.clear()
    cut = themes_ai.revise(read, version, request, question, local, transport=local_wire, ceiling=ceiling)
    user = sent[-1]["user"]
    check("140: past a forced ceiling the quote of the statement lowest on the canvas goes first, and the prompt says so",
          user == one and f"quote {keys[7]} " not in user and all(f"quote {k} " in user for k in keys[:7])
          and themes_ai.quotes_left(1) in user and user.index("Not placed:") < user.index(themes_ai.quotes_left(1)) < user.index("He asked:"))
    check("140: every statement, its key, the labels, the thread and his request still go, and the answer's line ends with the cut line",
          all(f"- {k} (" in user and texts[k] in user for k in keys)
          and all(t in user for t in ("Theme g1: Rigging before light", "Sub-theme g3: Reading the wind", "Theme g2: A boat that answers"))
          and "He asked: Give the wind its own sub-theme" in user and f"He asks now: {request}" in user
          and cut.get("said") == f"{own} {themes_ai.cut_line(1)}" and cut.get("trimmed") == 1 and "dropped" not in cut, str(cut)[:300])
    two = themes_ai.revise_user(board, thread, request, frozenset({keys[7], keys[3]}))
    sent.clear()
    cut_two = themes_ai.revise(read, version, request, question, local, transport=local_wire, ceiling=len(system) + len(two))
    user = sent[-1]["user"]
    check("140: the next to go is the next lowest on the canvas, the right of two at one height first, not the next in the prompt",
          user == two and f"quote {keys[3]} " not in user and f"quote {keys[2]} " in user and f"quote {keys[6]} " in user
          and cut_two.get("said", "").endswith(themes_ai.cut_line(2)) and cut_two.get("trimmed") == 2)

    # ── D. a ceiling no cut can meet: every statement bare and no thread, his request whole
    sent.clear()
    none_fit = themes_ai.revise(read, version, request, question, local, transport=local_wire, ceiling=1)
    user = sent[-1]["user"]
    check("140: a ceiling no cut can meet sends every statement bare, with its key, its words and his request, and no thread",
          "quote Initial:" not in user and all(f"- {k} (" in user and texts[k] in user for k in keys)
          and themes_ai.quotes_left(8) in user and "He asked:" not in user
          and "His requests so far on this board and their answers are left out here for room." in user
          and user.endswith(f"He asks now: {request}\n\nChange the board."))
    check("140: and the answer's line says both, the quotes and the thread",
          none_fit.get("said") == f"{own} {themes_ai.cut_line(8)} {themes_ai.thread_line(2)}"
          and none_fit.get("trimmed") == 8 and none_fit.get("dropped") == 2, str(none_fit)[:300])

    # ── E. a long thread passes the room alone: its oldest lines go, the newest kept
    long = [dict({"by": "analyst" if i % 2 == 0 else "ai", "at": "2026-10-14T10:00:00+01:00",
                  "text": f"Line {i}: " + "the jib, the mainsheet and the kicker once more " * 8},
                 **({"model": "stub-model on this machine"} if i % 2 else {})) for i in range(12)]
    target = themes_ai.revise_user(board, long, request, frozenset(keys), 5)
    sent.clear()
    trimmed = themes_ai.revise(read, dict(version, revise=long), request, question, local, transport=local_wire,
                               ceiling=len(system) + len(target))
    user = sent[-1]["user"]
    check("140: a thread past the room keeps its newest lines, the oldest going one at a time once the quotes are gone, and says so",
          user == target and "Line 4:" not in user and "Line 5:" in user and "Line 11:" in user
          and "The five oldest of these lines are left out here for room." in user and f"He asks now: {request}" in user
          and trimmed.get("dropped") == 5 and trimmed.get("trimmed") == 8
          and trimmed.get("said", "").endswith(" To fit what the model can take, Idiograph left out the five oldest messages in this conversation."))
    check("140: the thread's line counts in words, and one line is the oldest line",
          themes_ai.thread_line(1) == "To fit what the model can take, Idiograph left out the oldest message in this conversation."
          and themes_ai.thread_line(12) == "To fit what the model can take, Idiograph left out the 12 oldest messages in this conversation."
          and "The oldest of these lines is left out here for room." in themes_ai.thread_part(long, 1)
          and themes_ai.thread_part([], 3) == "")

    # ── F. the ceiling is the route's room, room_of with the revise's own answer room, thinking or not
    real = (themes_ai.PROMPT_CEILING, themes_ai.ANTHROPIC_CONTEXT)
    try:
        themes_ai.PROMPT_CEILING = ceiling
        sent.clear()
        by_local = themes_ai.revise(read, version, request, question, local, transport=local_wire)
        local_user = sent[-1]["user"]
        themes_ai.PROMPT_CEILING = real[0]
        haiku = {"provider": ai_mod.ANTHROPIC, "model": "claude-haiku-4-5", "key": "k-test"}
        opus = {"provider": ai_mod.ANTHROPIC, "model": "claude-opus-5-5", "key": "k-test"}
        themes_ai.ANTHROPIC_CONTEXT = (ceiling + 3) // 4 + themes_ai.REVISE_MAX_TOKENS
        sent.clear()
        by_haiku = themes_ai.revise(read, version, request, question, haiku, transport=cloud_wire)
        by_opus_short = themes_ai.revise(read, version, request, question, opus, transport=cloud_wire)
        themes_ai.ANTHROPIC_CONTEXT = (ceiling + 3) // 4 + ai_mod.THINKING_MAX_TOKENS
        by_opus = themes_ai.revise(read, version, request, question, opus, transport=cloud_wire)
        by_haiku_wide = themes_ai.revise(read, version, request, question, haiku, transport=cloud_wire)
        cloud = list(sent)
    finally:
        themes_ai.PROMPT_CEILING, themes_ai.ANTHROPIC_CONTEXT = real
    check("140: with no ceiling given a local model's room is PROMPT_CEILING, as a title's",
          local_user == one and by_local.get("trimmed") == 1)
    check("140: on Anthropic the room is its context less the revise's own answer room, more taken from a model that thinks",
          by_haiku.get("trimmed") == 1 and cloud[0]["user"] == one and cloud[0]["max_tokens"] == themes_ai.REVISE_MAX_TOKENS
          and by_opus_short.get("trimmed", 0) > 1 and by_opus.get("trimmed") == 1 and cloud[2]["user"] == one
          and cloud[2]["max_tokens"] == ai_mod.THINKING_MAX_TOKENS and "trimmed" not in by_haiku_wide and cloud[3]["user"] == whole,
          str([by_haiku.get("trimmed"), by_opus_short.get("trimmed"), by_opus.get("trimmed"), by_haiku_wide.get("trimmed")]))

    # ── G. the answer's line: the cut sentences always survive the length one line of a thread keeps
    capped = themes_ai.room_said({"said": "Moved " + "the jib across " * 300, "applied": []}, 3, themes_ai.cut_line, 2)
    tail = f"{themes_ai.cut_line(3)} {themes_ai.thread_line(2)}"
    check("140: a long answer is cut at a word so its line ends with what went, whole, and the thread keeps it so",
          len(capped["said"]) <= themes_mod.THREAD_TEXT and capped["said"].endswith(" " + tail)
          and capped["said"][:-len(tail) - 1].rsplit(" ", 1)[-1] in ("the", "jib", "across")
          and themes_mod.thread_of([{"by": "ai", "text": capped["said"]}])[0]["text"] == capped["said"])
    check("140: an error, or an answer from a prompt sent whole, is as it was",
          themes_ai.room_said({"error": "x"}, 3, themes_ai.cut_line, 2) == {"error": "x"}
          and themes_ai.room_said({"said": "a"}, 0, themes_ai.cut_line) == {"said": "a"})

    # ── H. through the route: the answer's line in the thread ends with the cut line
    real_route = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, ai_mod.find_key, ai_mod.http_call, themes_ai.ANTHROPIC_CONTEXT)
    config_path = scratch / "revise-room-config.json"
    try:
        server_mod.CONFIG_PATH = config_path
        server_mod.ROOT_OVERRIDE = str(root)
        ai_mod.find_key = lambda *a, **kw: "k-test"
        ai_mod.http_call = cloud_wire
        config_path.write_text(json.dumps({"ai_suggest": True, "ai_provider": "anthropic", "model": "claude-haiku-4-5",
                                           "pets_provider": "anthropic", "pets_model": "claude-haiku-4-5"}), encoding="utf-8")
        opened = idiograph_routes.api_themes({"workbook": str(work)})
        idiograph_routes.api_themes_save({"workbook": str(work), "version": {**opened["version"], "cards": version["cards"],
                                                                       "groups": version["groups"], "revise": thread}})
        saved = themes_mod.load(work)["boards"][0]
        routed_one = themes_ai.revise_user(themes_ai.revise_board(read, saved), thread, request, frozenset({keys[7]}))
        themes_ai.ANTHROPIC_CONTEXT = (len(system) + len(routed_one) + 3) // 4 + themes_ai.REVISE_MAX_TOKENS
        sent.clear()
        routed = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "revise", "version": opened["version"]["id"],
                                           "text": request})
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, ai_mod.find_key, ai_mod.http_call, themes_ai.ANTHROPIC_CONTEXT = real_route
    check("140: the route's answer line for the thread ends with the cut line, and the board's change still lands",
          sent and sent[-1]["user"] == routed_one
          and (routed.get("revise") or {}).get("text") == f"{own} {themes_ai.cut_line(1)}"
          and [g["label"] for g in (routed.get("revised") or {}).get("groups", []) if g["id"] == "g2"] == ["The boat as a second body"],
          str(routed)[:300])

    # ── I. the GETs revise: its cut line, once discarded, now ends its answer as the PETs one does
    def gstatement(case_name, k):
        return {"key": f"{case_name}/{k}", "sheet": DEMO_SHEET, "time": read["cards"][keys.index(k)]["time"], "text": texts[k]}

    gboard = {"themes": [{"id": "G1", "label": "Learning the wind by the body", "count": 2, "themes": [], "cards": [
        {"kind": "pet", "key": "Bryn/g1", "who": "Bryn", "title": "Rigging before light",
         "statements": [gstatement("Bryn", k) for k in keys[:4]], "quotes": [{"key": f"Bryn/{keys[0]}", "text": "I rig it before anyone else is up"}]},
        {"kind": "pet", "key": "Cai/g1", "who": "Cai", "title": "A body that leans with the boat",
         "statements": [gstatement("Cai", k) for k in keys[4:]], "quotes": [{"key": f"Cai/{keys[4]}", "text": "it leans when I lean"}]}]}],
        "unplaced": [], "discarded": [], "total": 2, "minimum": 2}
    gstart = {"items": ["Bryn/g1", "Cai/g1"], "groups": [{"id": "G1", "label": "Learning the wind by the body",
                                                          "members": ["Bryn/g1", "Cai/g1"]}],
              "picks": {}, "quotes": {}, "card_quotes": {"Bryn/g1": [f"Bryn/{keys[0]}"], "Cai/g1": [f"Cai/{keys[4]}"]},
              "prefix": "G", "pick_max": 2, "unit": "card"}
    gown = "Retitled 'Learning the wind by the body' as 'Reading the wind through the hands'."
    sent_reply[0] = json.dumps({"operations": [{"op": "retitle", "label": "G1", "title": "Reading the wind through the hands"}],
                                "said": gown})
    gsystem = themes_ai.gets_revise_system(question)
    gwhole = themes_ai.gets_revise_user(gboard, thread, request)
    sent.clear()
    gfull = themes_ai.gets_revise(gboard, gstart, thread, request, question, local, transport=local_wire)
    gcut = themes_ai.gets_revise(gboard, gstart, thread, request, question, local, transport=local_wire,
                                 ceiling=len(gsystem) + len(gwhole) - 40)
    gnone = themes_ai.gets_revise(gboard, gstart, thread, request, question, local, transport=local_wire, ceiling=1)
    check("140: a GETs revise sent whole answers in its own words, as before",
          sent[0]["user"] == gwhole and gfull.get("said") == gown and "trimmed" not in gfull)
    check("140: past its room the GETs revise's answer ends with gets_cut_line, the words that went counted",
          gcut.get("trimmed", 0) >= 1 and gcut.get("said") == f"{gown} {themes_ai.gets_cut_line(gcut['trimmed'])}"
          and "are left out here for room" in sent[1]["user"] and f"He asks now: {request}" in sent[1]["user"], str(gcut)[:300])
    check("140: and with no room the GETs revise leaves every statement's words and the thread, every PET title kept, and says both",
          gnone.get("said") == f"{gown} {themes_ai.gets_cut_line(8)} {themes_ai.thread_line(2)}"
          and all(t in sent[2]["user"] for t in ("Rigging before light", "A body that leans with the boat"))
          and not any(texts[k] in sent[2]["user"] for k in keys) and "He asked:" not in sent[2]["user"])
