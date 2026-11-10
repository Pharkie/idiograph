from __future__ import annotations

import inspect
import json
import re
import shutil

import ai_suggest as ai_mod
from workbook import WorkbookError

from . import support
from .support import DEMO_SHEET, GRAVITY_QUESTION, check, demo_copy, skip
import idiograph_routes


def test_themes_ai(scratch):
    print("\n41. Themes, stage 3: the AI's grouping and its titles")
    import http.server
    import subprocess
    import threading
    import urllib.error
    import urllib.request
    import server as server_mod
    import themes as themes_mod
    import themes_ai

    root = scratch / "themes-ai-root"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    (root / "idiograph-project.json").write_text(json.dumps(
        {"name": "Scratch", "research_question": GRAVITY_QUESTION}), encoding="utf-8")
    read = themes_mod.read_cards(work)
    k = [c["key"] for c in read["cards"]]
    line_of = lambda key: f"- {key} ("

    # ── A. what a new AI proposal sends
    mine = themes_mod.blank_version(read["cards"])
    mine["groups"] = [{"id": "g1", "label": "Mornings first", "members": [k[0], k[1]], "x": 0, "y": 0},
                      {"id": "g2", "label": "Over the mornings", "members": ["g1"], "x": 0, "y": -40}]
    mine["discarded"] = [k[2]]
    merged = themes_mod.merge(read["cards"], mine)
    statements = themes_ai.statements_of(merged)
    labels = themes_ai.labels_of(merged)
    system = themes_ai.group_system(GRAVITY_QUESTION)
    user = themes_ai.group_user(statements, labels, "  fewer   groups ")
    cards = {c["key"]: c for c in read["cards"]}
    check("every card on the canvas goes by its key, sheet, timecode and words, and a discarded one does not",
          len(statements) == len(k) - 1 and all(line_of(key) in user for key in k if key != k[2])
          and line_of(k[2]) not in user
          and f"- {k[0]} ({DEMO_SHEET}, {cards[k[0]]['time']}) {cards[k[0]]['text']}" in user,
          f"{len(statements)} statements")
    check("his labels go as context, nested as they sit, with the keys under each, his to keep, merge or replace",
          "- Over the mornings" in user and f"  - Mornings first: {k[0]}, {k[1]}" in user
          and "keep any that hold, merge them or replace them" in user)
    check("the hint goes when there is one, tidied, and the line about labels says when there are none",
          "His hint for this arrangement, which comes before the general guidance: fewer groups" in user
          and "There are no labels on the canvas yet." in themes_ai.group_user(statements, [], "")
          and "His hint" not in themes_ai.group_user(statements, [], "   "))
    title_rule = dict(themes_ai.guidance_items(3)).get(5, "")
    check("the system prompt carries the study's question, the title rules from the guidance file and the JSON shape",
          f"The study asks: {GRAVITY_QUESTION}" in system
          and title_rule and f"5. {title_rule}" in system and "jargon" in system and '{"groups": [{"label": "...", "members"' in system
          and "Interpretative Phenomenological Analysis" in system
          and "The study asks" not in themes_ai.group_system(""))

    # ── B. reading a grouping strictly
    good = json.dumps({"groups": [
        {"label": "Mornings that belong to the dog", "members": [k[0], k[1]]},
        {"label": "A house that holds two", "members": [k[3]],
         "groups": [{"label": "Walks taken alone", "members": [k[4], k[5]]}]}]})
    parsed = themes_ai.parse_grouping(good, k)
    check("a good answer reads as themes, a sub-theme one level down, and the counts",
          [g["label"] for g in parsed["groups"]] == ["Mornings that belong to the dog", "A house that holds two"]
          and parsed["groups"][1]["groups"] == [{"label": "Walks taken alone", "members": [k[4], k[5]]}]
          and parsed["placed"] == 5 and parsed["left"] == len(k) - 5 and parsed["unknown"] == 0, str(parsed)[:120])
    check("a fenced answer, or one with words round it, reads the same",
          themes_ai.parse_grouping(f"```json\n{good}\n```", k) == parsed
          and themes_ai.parse_grouping(f"Here it is:\n{good}\nI hope it helps.", k) == parsed
          and themes_ai.parse_grouping(json.dumps(json.loads(good)["groups"]), k) == parsed)
    twice = themes_ai.parse_grouping(json.dumps({"groups": [{"label": "A", "members": [k[0], k[1]]},
                                                            {"label": "B", "members": [k[1], k[3]]}]}), k)
    check("a key in two groups keeps the first",
          [g["members"] for g in twice["groups"]] == [[k[0], k[1]], [k[3]]] and twice["repeated"] == 1)
    unknown = themes_ai.parse_grouping(json.dumps({"groups": [{"label": "A", "members": [
        k[0], "Initial:999:0", "Nowhere:1:0"]}]}), k)
    check("a key the case does not have is left out, and counted",
          unknown["groups"][0]["members"] == [k[0]] and unknown["unknown"] == 2 and unknown["placed"] == 1)
    check("an empty answer, one with no groups and one that places nothing are each one line",
          themes_ai.parse_grouping("", k) == {"error": themes_ai.NOT_JSON}
          and themes_ai.parse_grouping('{"groups": []}', k) == {"error": themes_ai.PLACED_NOTHING}
          and themes_ai.parse_grouping(json.dumps({"groups": [{"label": "A", "members": ["Initial:999:0"]}]}), k)
          == {"error": themes_ai.PLACED_NOTHING}
          and themes_ai.parse_grouping("no json here", k) == {"error": themes_ai.NOT_JSON})
    check("an answer cut off at its length limit says so",
          themes_ai.parse_grouping(good[:len(good) // 2], k, truncated=True) == {"error": ai_mod.TOO_LONG}
          and themes_ai.parse_grouping(good[:len(good) // 2], k) == {"error": themes_ai.NOT_JSON})
    deep = themes_ai.parse_grouping(json.dumps({"groups": [{"label": "Top", "members": [k[0]], "groups": [
        {"label": "Middle", "members": [k[1]], "groups": [{"label": "Deep", "members": [k[3]],
                                                           "groups": [{"label": "Deeper", "members": [k[4]]}]}]}]}]}), k)
    check("a nest deeper than one level is folded into the sub-theme above it",
          deep["groups"] == [{"label": "Top", "members": [k[0]],
                              "groups": [{"label": "Middle", "members": [k[1], k[3], k[4]]}]}], str(deep["groups"]))
    tidy = themes_ai.parse_grouping(json.dumps({"groups": [
        {"label": "   ", "members": [k[0]], "groups": [{"label": "Empty", "members": []},
                                                      {"label": "Gone", "members": ["Initial:999:0"]}]},
        {"label": "Nothing in it", "members": []},
        {"label": "\u201cA label \u2014 with a dash; and more\u201d", "members": [k[1]]}]}), k)
    check("a blank label is Untitled, a sub-theme with no members goes, and so does an empty theme",
          [(g["label"], g["groups"]) for g in tidy["groups"]][0] == ("Untitled", []) and len(tidy["groups"]) == 2)
    check("a label loses inverted commas round the whole of it, its em dash and its semicolon",
          tidy["groups"][1]["label"] == "A label, with a dash, and more", tidy["groups"][1]["label"])

    # ── C. the layout: a round blob for each theme, the rest in a pile
    proposal = themes_ai.parse_grouping(json.dumps({"groups": [
        {"label": "Mornings that belong to the dog and to nobody else in the house", "members": k[0:4]},
        {"label": "A house that holds two", "members": [k[4]],
         "groups": [{"label": "Walks taken alone", "members": k[5:8]}, {"label": "Nights", "members": k[8:10]}]},
        {"label": "A third theme", "members": k[10:13]}]}), k)
    source = themes_mod.blank_version(read["cards"])
    source["discarded"] = [k[-1]]
    source["cards"][k[-1]].update(x=77, y=88)
    m2 = themes_mod.merge(read["cards"], source)
    laid = themes_ai.lay_out(proposal["groups"], m2["cards"], m2["discarded"])
    by_id = {g["id"]: g for g in laid["groups"]}
    parents = {m: g["id"] for g in laid["groups"] for m in g["members"]}
    pos = laid["cards"]
    check("every card of the board is laid out, and the discarded one stays discarded where it was",
          set(pos) == set(k) and laid["discarded"] == [k[-1]] and (pos[k[-1]]["x"], pos[k[-1]]["y"]) == (77, 88)
          and laid["picks"] == {} and all(pos[key]["text"] == cards[key]["text"] for key in k))
    check("the themes are g1 on, the sub-themes after them inside their theme",
          [g["id"] for g in laid["groups"]] == ["g1", "g2", "g3", "g4", "g5"]
          and by_id["g2"]["members"] == [k[4], "g4", "g5"] and parents["g4"] == "g2" and parents["g5"] == "g2"
          and [by_id[g]["label"] for g in ("g4", "g5")] == ["Walks taken alone", "Nights"])
    drawn_at = themes_mod.layout_boxes(laid)
    frames, label_boxes, card_boxes = drawn_at["frames"], drawn_at["labels"], drawn_at["cards"]
    within = lambda a, b: b[0] <= a[0] and b[1] <= a[1] and a[0] + a[2] <= b[0] + b[2] and a[1] + a[3] <= b[1] + b[3]
    inside = all(within(card_boxes[m] if m in card_boxes else frames[m], frames[g["id"]])
                 for g in laid["groups"] for m in g["members"])
    check("every member lies inside its theme's frame, and each sub-theme's frame inside its theme's",
          inside and within(frames["g4"], frames["g2"]) and within(frames["g5"], frames["g2"]))
    check("each label stands where the page sets it, above what it holds, its left edge on theirs",
          all((g["x"], g["y"]) == tuple(label_boxes[g["id"]][:2]) for g in laid["groups"])
          and all(label_boxes[g["id"]][1] < min(card_boxes[m][1] for m in g["members"] if m in card_boxes)
                  for g in laid["groups"] if any(m in card_boxes for m in g["members"])))
    top_frames = [frames[g] for g in ("g1", "g2", "g3")]
    check("the themes are blobs on the plane, their frames apart with clear gaps",
          not any(themes_mod.clash(top_frames[i], top_frames[j], themes_ai.THEME_GAP - 1) for i in range(3) for j in range(i + 1, 3))
          and themes_ai.THEME_GAP == 2 * themes_mod.MARGIN)
    shape = [frames[g][2] / frames[g][3] for g in ("g1", "g3")]
    check("a theme's own cards fill a roughly round blob, not a column",
          all(0.5 <= r <= 2.2 for r in shape), ", ".join(f"{r:.2f}" for r in shape))
    under_of = {}
    for g in laid["groups"]:
        under_of[g["id"]] = set(g["members"])
    for g in laid["groups"]:
        for m in list(under_of[g["id"]]):
            under_of[g["id"]] |= under_of.get(m, set())
    items = [(key, box) for key, box in card_boxes.items()] + [(gid, box) for gid, box in label_boxes.items()]
    overlaps = [(a, b) for i, (a, ba) in enumerate(items) for b, bb in items[i + 1:]
                if themes_mod.clash(ba, bb) and b not in under_of.get(a, ()) and a not in under_of.get(b, ())]
    check("no card or label over another card or label",
          not overlaps, ", ".join(f"{a}/{b}" for a, b in overlaps[:4]) or f"{len(items)} cards and labels")
    drawn = [key for key in k if key not in laid["discarded"]]
    left = [key for key in drawn if key not in parents]
    edge = max(f[0] + f[2] for f in frames.values())
    check("the cards left out lie in a pile to the right of the themes, in transcript order",
          left and all(pos[key]["x"] > edge for key in left)
          and [key for key in sorted(left, key=lambda key: (pos[key]["y"], pos[key]["x"]))] == left,
          f"{len(left)} unplaced")
    check("the layout survives the file's own tidying unchanged",
          themes_mod.normalise(laid)["groups"] == [dict(g) for g in laid["groups"]])

    # ── D. the route, through a transport that stands in for the provider
    real = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, ai_mod.find_key, ai_mod.http_call)
    config_path = scratch / "themes-ai" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    sent, replies, looked = [], [], []

    def wire(method, url, headers, payload, timeout):
        sent.append({"url": url, "payload": payload, "timeout": timeout, "headers": headers})
        text = replies[0](payload) if replies else ""
        if "/api/chat" in url:
            return 200, json.dumps({"message": {"content": text}, "done_reason": "stop"})
        return 200, json.dumps({"content": [{"type": "text", "text": text}], "stop_reason": "end_turn"})

    def grouping(payload):
        found = re.findall(r"^- (\S+:\d+:\d+) \(", payload["messages"][-1]["content"], re.M)
        return json.dumps({"groups": [
            {"label": "Mornings that belong to the dog", "members": found[:3]},
            {"label": "A house that holds two", "members": found[3:6],
             "groups": [{"label": "Walks taken alone", "members": found[6:8]}]}]})

    def settings(**extra):
        config_path.write_text(json.dumps({"ai_provider": "anthropic", "model": "claude-haiku-4-5", **extra}),
                               encoding="utf-8")

    path = themes_mod.themes_path(work)
    file = lambda: json.loads(path.read_text(encoding="utf-8"))
    try:
        server_mod.CONFIG_PATH = config_path
        server_mod.ROOT_OVERRIDE = str(root)
        ai_mod.find_key = lambda *a, **kw: looked.append(1) or "k-test"
        ai_mod.http_call = wire
        settings(ai_suggest=False)
        off = [idiograph_routes.api_themes_ai({"workbook": str(work), "op": "group"}),
               idiograph_routes.api_themes_ai({"workbook": str(work), "op": "names", "statements": ["x"]})]
        check("with the switch off both are refused with one line, and nothing is sent or written",
              off == [{"error": themes_ai.OFF}] * 2 and not sent and not looked and not path.exists())
        opened = idiograph_routes.api_themes({"workbook": str(work)})
        check("/api/themes says whether the switch is on and which model answers, never the key",
              opened["ai"] == {"on": False, "provider": "anthropic", "model_name": "Haiku 4.5", "cap": 5} and not looked)
        settings(ai_suggest=True)
        opened = idiograph_routes.api_themes({"workbook": str(work)})
        check("and says so when it is on", opened["ai"]["on"] is True and not looked)

        body = {**opened["version"], "cards": {c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]}
                                               for c in opened["cards"]},
                "groups": [{"id": "g1", "label": "Mornings first", "members": [k[0], k[1]], "x": 0, "y": 0}],
                "discarded": [k[2]], "picks": {}}
        idiograph_routes.api_themes_save({"workbook": str(work), "version": body})
        v1 = file()["boards"][0]
        book = work.read_bytes()
        replies[:] = [grouping]
        made = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "group", "version": "v1", "hint": ""})
        data = file()
        new = data["boards"][-1]
        check("a press makes Board 2, a board of its own after the rest, named as New board names one (184), and makes it current",
              made["version"]["name"] == "Board 2" and [v["name"] for v in data["boards"]]
              == ["Board 1", "Board 2"] and data["current"] == new["id"] == made["current"] == "v2")
        check("the board it was made from is exactly as it was", data["boards"][0] == v1)
        check("the note names the model, the board it came from and the time",
              new["note"].startswith("Proposed by Haiku 4.5 from Board 1 on ")
              and re.search(r" on \d{1,2} [A-Z][a-z]+ \d{4} at \d\d:\d\d[.,]", new["note"]) is not None
              and "hint" not in new["note"] and "2 PETs, 8 placed" in new["note"], new["note"])
        call = sent[-1]
        check("one call to the Messages API, with room for a long answer and time to write it",
              len(sent) == 1 and call["url"] == ai_mod.ENDPOINT and call["payload"]["model"] == "claude-haiku-4-5"
              and call["payload"]["max_tokens"] == themes_ai.GROUP_MAX_TOKENS
              and call["timeout"] == themes_ai.GROUP_TIMEOUT and set(call["payload"]) == {"model", "max_tokens", "system", "messages"})
        asked = call["payload"]["messages"][0]["content"]
        check("it carries every card not discarded, his label, and the project's question",
              all(line_of(key) in asked for key in k if key != k[2]) and line_of(k[2]) not in asked
              and f"- Mornings first: {k[0]}, {k[1]}" in asked and GRAVITY_QUESTION in call["payload"]["system"])
        top = [g for g in new["groups"] if g["id"] in ("g1", "g2")]
        check("the grouping lands as labels over the cards, a sub-theme inside its theme, the discard kept",
              [g["label"] for g in new["groups"]] == ["Mornings that belong to the dog", "A house that holds two",
                                                      "Walks taken alone"]
              and top[1]["members"][-1] == "g3" and new["discarded"] == [k[2]] and new["picks"] == {}
              and set(new["cards"]) == set(v1["cards"]))
        check("the answer is the screen's state with what was made and from what",
              {"cards", "groups", "versions", "version", "current", "made", "ai"} <= set(made)
              and made["made"]["name"] == "Board 2" and made["made"]["from"] == "Board 1"
              and made["made"]["themes"] == 2 and made["made"]["placed"] == 8 and made["made"]["model_name"] == "Haiku 4.5")
        check("the key rides in the request's header and nowhere else",
              call["headers"].get("x-api-key") == "k-test" and "k-test" not in json.dumps(made)
              and "k-test" not in path.read_text(encoding="utf-8") and "k-test" not in json.dumps(call["payload"]))
        check("the workbook is never written", work.read_bytes() == book)

        sent.clear()
        again = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "group", "version": made["current"],
                                          "hint": "  fewer   groups "})
        data = file()
        rerolled = data["boards"][-1]
        asked = sent[-1]["payload"]["messages"][0]["content"]
        check("a re-roll makes Board 3 from the proposal on the canvas, its labels sent as context",
              again["version"]["name"] == "Board 3" and data["current"] == again["current"] == "v3"
              and "- Mornings that belong to the dog: " in asked and "  - Walks taken alone: " in asked
              and data["boards"][1] == new)
        check("the hint rides in the request, the note and the answer",
              "His hint for this arrangement, which comes before the general guidance: fewer groups" in asked and "from Board 2" in rerolled["note"]
              and "with the hint 'fewer groups'" in rerolled["note"] and again["made"]["hint"] == "fewer groups")
        idiograph_routes.api_themes_versions({"workbook": str(work), "op": "delete", "id": "v2"})
        third = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "group"})
        check("the names run on as New board names them, the next free number, and no board is named twice (184)",
              third["version"]["name"] == "Board 4"
              and [v["name"] for v in file()["boards"]] == ["Board 1", "Board 3", "Board 4"]
              and themes_mod.proposal_name([{"name": "AI board 9"}, {"name": "ai board 12"}]) == "Board 3")

        outcomes = []
        for reply in ('{"groups": []}', "not json at all", json.dumps({"groups": [{"label": "A", "members": ["Initial:999:0"]}]})):
            replies[:] = [lambda p, r=reply: r]
            before = path.read_bytes()
            out = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "group"})
            outcomes.append(set(out) == {"error"} and path.read_bytes() == before)
        check("an answer that places nothing, or cannot be read, is one line and makes no board",
              outcomes == [True, True, True])

        def cut(method, url, headers, payload, timeout):
            return 200, json.dumps({"content": [{"type": "text", "text": '{"groups": [{"label": "A", "members": ["Ini'}],
                                    "stop_reason": "max_tokens"})

        def failing(method, url, headers, payload, timeout):
            return 529, '{"error": "do not print me"}'

        before = path.read_bytes()
        ai_mod.http_call = cut
        truncated = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "group"})
        ai_mod.http_call = failing
        failed = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "group"})
        ai_mod.http_call = wire
        check("an answer cut off at its length limit says so, and an API error says its status and nothing else",
              truncated == {"error": ai_mod.TOO_LONG} and failed == {"error": "Anthropic did not answer (HTTP 529)."}
              and path.read_bytes() == before)
        ai_mod.find_key = lambda *a, **kw: None
        sent.clear()
        keyless = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "group"})
        ai_mod.find_key = lambda *a, **kw: "k-test"
        check("no key is one line and no call", keyless == {"error": ai_mod.NO_KEY} and not sent)
        refused = []
        for call_body, route in ((dict(op="group", version="v9"), idiograph_routes.api_themes_ai),
                                 (dict(op="propose", version={"cards": {}}), idiograph_routes.api_themes_versions)):
            try:
                route({"workbook": str(work), **call_body})
            except WorkbookError as exc:
                refused.append(str(exc))
        check("a board the file does not hold is refused, and the boards route never takes a proposal",
              len(refused) == 2 and "no longer" in refused[0] and "not something a board can do" in refused[1]
              and path.read_bytes() == before)
        check("an op the help does not have is one line",
              "error" in idiograph_routes.api_themes_ai({"workbook": str(work), "op": "write"}))
        outside = demo_copy(scratch, "themes-ai-elsewhere", "Juno - EN & ES.xlsx")
        try:
            idiograph_routes.api_themes_ai({"workbook": str(outside), "op": "group"})
            stray = True
        except server_mod.OutsideRoot:
            stray = False
        check("a workbook outside the root is refused", not stray and not themes_mod.themes_path(outside).exists())

        # the names
        sent.clear()
        replies[:] = [lambda p: json.dumps({"names": ["Mornings that belong to the dog",
                                                      "A walk before the house wakes",
                                                      "mornings that belong to the dog"]})]
        before = path.read_bytes()
        named = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "names",
                                          "statements": ["Waking before the house does", "The lead by the door"],
                                          "label": "Mornings first", "others": ["A house that holds two"]})
        asked = sent[-1]["payload"]["messages"][0]["content"]
        check("names come back tidied and each once, with the model that gave them",
              named["names"] == ["Mornings that belong to the dog", "A walk before the house wakes"]
              and named["model_name"] == "Haiku 4.5" and isinstance(named["seconds"], float), str(named))
        check("the request carries the statements, the title it has, the other labels and the question",
              "- Waking before the house does" in asked and "Its title now: Mornings first" in asked
              and "- A house that holds two" in asked and "Three titles" in asked
              and GRAVITY_QUESTION in sent[-1]["payload"]["system"] and '{"names"' in sent[-1]["payload"]["system"]
              and sent[-1]["payload"]["max_tokens"] == themes_ai.NAMES_MAX_TOKENS)
        check("asking for names writes nothing", path.read_bytes() == before and work.read_bytes() == book)
        check("a selection with no statements is one line and no call",
              idiograph_routes.api_themes_ai({"workbook": str(work), "op": "names", "statements": ["  "]})
              == {"error": themes_ai.NOTHING_TO_NAME} and len(sent) == 1)

        # Local: the same help through Ollama, with the room asked for and no key looked up
        settings(ai_suggest=True, ai_provider="local", local_model="llama3.1:8b")
        sent.clear()
        looked.clear()
        replies[:] = [grouping]
        local = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "group"})
        options = sent[-1]["payload"].get("options", {})
        check("through Local the grouping goes to Ollama with room for the answer, and no key is looked up",
              sent[-1]["url"].endswith("/api/chat") and options.get("num_predict") == themes_ai.GROUP_MAX_TOKENS
              and options.get("num_ctx") == ai_mod.LOCAL_CONTEXT and not looked
              and local["made"]["model_name"] == "llama3.1:8b on this machine"
              and file()["boards"][-1]["note"].startswith("Proposed by llama3.1:8b on this machine from "))
        check("a suggestion's own request is as it was, with no ceiling of its own",
              "options" not in ai_mod.local_payload("s", "u", "m")
              and ai_mod.anthropic_payload("s", "u", "claude-haiku-4-5")["max_tokens"] == ai_mod.MAX_TOKENS)

        # over HTTP, and a server from before the help
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
        threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()

        def post(route, payload):
            req = urllib.request.Request(f"http://127.0.0.1:{httpd.server_address[1]}{route}",
                                         data=json.dumps(payload).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    return r.status, json.loads(r.read())
            except urllib.error.HTTPError as exc:
                return exc.code, json.loads(exc.read())

        held = server_mod.ROUTES.pop("/api/themes-ai")
        try:
            old = post("/api/themes-ai", {"workbook": str(work), "op": "group"})
        finally:
            server_mod.ROUTES["/api/themes-ai"] = held
        try:
            far = post("/api/themes-ai", {"workbook": str(outside), "op": "group"})
        finally:
            httpd.shutdown()
            httpd.server_close()
        check("a server from before the help answers with the line the page turns into the restart line",
              old == (404, {"error": "No such endpoint.", "code": "no_endpoint"}) and far[0] == 403)
        check("the route is in the dispatch table and goes through ai_route, by way of the PETs route",
              server_mod.ROUTES.get("/api/themes-ai") is idiograph_routes.api_themes_ai
              and "pets_route(cfg" in inspect.getsource(idiograph_routes.api_themes_ai)
              and "ai_route(cfg" in inspect.getsource(idiograph_routes.pets_route))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, ai_mod.find_key, ai_mod.http_call = real

    # ── E. the names, read
    check("three titles come back as three, a fourth dropped",
          themes_ai.parse_names(json.dumps({"names": ["One title", "Two titles", "Three titles", "Four"]}))
          == {"names": ["One title", "Two titles", "Three titles"]})
    check("two come back as two, a fenced answer read and a repeat dropped",
          themes_ai.parse_names('```json\n{"names": ["A walk", "a walk", "The door"]}\n```')
          == {"names": ["A walk", "The door"]})
    check("none is one line, and so is an answer that is not JSON or was cut off",
          themes_ai.parse_names('{"names": []}') == {"error": themes_ai.NO_TITLES}
          and themes_ai.parse_names('{"names": ["  "]}') == {"error": themes_ai.NO_TITLES}
          and themes_ai.parse_names("nothing") == {"error": themes_ai.NOT_JSON}
          and themes_ai.parse_names('{"names": ["A', truncated=True) == {"error": ai_mod.TOO_LONG})
    check("a label with no title, or Untitled, is sent as having none",
          "It has no title yet." in themes_ai.names_user(["a"], "") and "It has no title yet." in themes_ai.names_user(["a"], "Untitled"))

    # ── F. the page
    js = support.text("apps/idiograph/static/themes.js")
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda text, name: text.split(f"function {name}(", 1)[1].split("\n}", 1)[0]
    check("both are drawn only with the switch on, and n asks only then",
          "(thAiOn() ?" in fn(js, "thVmenuDraw") and 'data-vop="ai"' in fn(js, "thVmenuDraw")
          and "if (!TH.live || TH.busy || !thAiOn() || !TH.meta) return;" in fn(js, "thAiCard")
          and "if (!thAiOn() || !item || item.kind !== 'group') return '';" in fn(js, "thNamesHtml")
          and "&& thAiOn()) { e.preventDefault(); thNamesAsk(); }" in fn(js, "thKeyDown")
          and "t('themes.names.pets')" in fn(js, "thNamesHtml"))
    group_fn = fn(js, "thAutoGroup")
    check("a new AI proposal saves the canvas first, asks once with the board and the hint, waits, and switches",
          group_fn.index("await thFlush();") < group_fn.index("op: 'group', version: TH.meta.id, hint")
          and "TH.busy = true;" in group_fn and "thAiBusy(true, n);" in group_fn
          and "thLoad(data, { fit: true });" in group_fn
          and "'themes.ai.line'" in group_fn)
    apply = fn(js, "thNameApply")
    check("a name picked is one step of undo, a rename on its label, Edit to type over it, and no label made over a selection (123)",
          "thDone(before, t('themes.step.renamed')" in apply and "thDone(before, t('themes.step.made_theme')" not in apply
          and "thMakeGroup(" not in apply
          and "thTitleOpen(g.id, { value: name });" in apply
          and "opts.value !== undefined ? opts.value" in fn(js, "thTitleOpen"))
    keys = fn(js, "thKeyDown")
    check("the hint box keeps its keys from the canvas, Enter in the card is Make and Esc is Cancel (118)",
          ".th-ai-hint')) return;" in keys and "if (!$('th-aicard').hidden) {" in keys
          and "e.preventDefault(); e.stopPropagation(); thAutoGroup();" in keys
          and "if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); thAiCard(false); }" in keys
          and keys.index("if (!$('th-aicard').hidden) {") < keys.index("if (anyOverlayOpen()) return;")
          and "'th-aicard'" in app.split("const OVERLAYS = ", 1)[1].split("\n", 1)[0])

    node = shutil.which("node")
    if not node:
        return skip("the names model in node", "no node on this machine")
    run = subprocess.run([node, "--check", str(support.source("apps/idiograph/static/themes.js"))], capture_output=True, text=True, encoding="utf-8")
    run = subprocess.run([node, "--check", str(support.source("apps/idiograph/static/distil.js"))], capture_output=True, text=True, encoding="utf-8")
    script = scratch / "themes-names.js"
    script.write_text(support.i18n_js() + js + r"""
const card = (row, text) => ({ sheet: 'S', row, line: 0, x: 0, y: 0, text, seconds: row, time: '' });
const v = { cards: { 'S:1:0': card(1, 'one'), 'S:2:0': card(2, 'two'), 'S:3:0': card(3, 'three'),
  'S:4:0': card(4, 'four') }, groups: [], discarded: [], picks: {} };
const g1 = thMakeGroup(v, ['S:1:0', 'S:2:0'], 'First');
const g2 = thMakeGroup(v, ['S:3:0'], '');
const g3 = thMakeGroup(v, [g1], 'Over');
const none = { cards: new Set(), groups: new Set() };
const out = {};
out.label = thNamesTarget(v, { cards: new Set(), groups: new Set([g1]) }, null);
out.labelAndOwnCard = thNamesTarget(v, { cards: new Set(['S:1:0']), groups: new Set([g1]) }, null);
out.bare = thNamesTarget(v, { cards: new Set(['S:4:0', 'S:3:0']), groups: new Set() }, null);
out.panelCard = thNamesTarget(v, none, { kind: 'card', id: 'S:4:0' });
out.panelLabel = thNamesTarget(v, none, { kind: 'group', id: g2 });
out.nothing = thNamesTarget(v, none, null);
out.body = thNamesBody(v, { kind: 'group', id: g1 });
out.keys = [thNamesKey({ kind: 'group', id: g1 }), thPanelKey({ kind: 'group', id: g1 }), thPanelKey({ kind: 'card', id: 'S:4:0' })];
out.rows = thPanelRows(v, { kind: 'group', id: g3 }, {}, ['S']).map((r) => r.row);
out.selCards = typeof thSelCards;
console.log(JSON.stringify(out));
""", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("the names model runs in node", False, run.stderr.strip()[:300])
    out = json.loads(run.stdout)
    check("one label selected is that label to rename, its own card beside it changes nothing",
          out["label"] == {"kind": "group", "id": "g1"} and out["labelAndOwnCard"] == {"kind": "group", "id": "g1"})
    check("123: cards selected with no label say to group them first, and with nothing selected only the panel's label is a target",
          out["bare"] == {"kind": "cards"} and out["panelCard"] is None
          and out["panelLabel"] == {"kind": "group", "id": "g2"} and out["nothing"] is None)
    check("122: a label sends its id and its board, and beside them the old shape a server from before reads",
          out["body"] == {"version": None, "group": "g1", "statements": ["one", "two"], "label": "First", "others": ["Over"]})
    check("the names show beside the label they were asked for, and the bare selection's keys are gone (123)",
          out["keys"] == ["g:g1", "g:g1", "s:S:4:0"] and out["selCards"] == "undefined")
    check("a label over labels lists the rows of every card under it, in transcript order",
          out["rows"] == ["S:1", "S:2"])
