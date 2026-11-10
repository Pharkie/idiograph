from __future__ import annotations

import inspect
import json
import os
import re
import shutil
from pathlib import Path

import ai_suggest as ai_mod

from .a038_polish_items import test_polish_items
from . import support
from .support import (
    DEMO_QUESTION, DEMO_SHEET, GRAVITY_QUESTION, ISO_OFFSET, add_second_sheet, check, demo_copy, skip,
)
import idiograph_routes


def test_themes_review_print(scratch):
    print("\n46. Themes, the guidance file, the AI review and the print view")
    import html
    import http.server
    import subprocess
    import threading
    import urllib.error
    import urllib.request
    import server as server_mod
    import themes as themes_mod
    import themes_ai
    import themes_print
    import i18n

    # ── A. the guidance ships with the app, and the prompts read it
    shipped = support.source("apps/idiograph/pet_guidance.md")
    rules, questions = themes_ai.guidance_items(3), themes_ai.guidance_items(4)
    check("the guidance file ships beside the app, with its eleven rules and nineteen questions",
          shipped.is_file() and themes_ai.GUIDANCE == shipped.resolve()
          and [n for n, _ in rules] == list(range(1, 12)) and [n for n, _ in questions] == list(range(1, 20))
          and "## 3. Rules for a theme" in shipped.read_text(encoding="utf-8")
          and "## 4. Questions a reviewer asks of a grouping" in shipped.read_text(encoding="utf-8"))
    audit = inspect.getsource(test_polish_items)
    check("it is in the shipped-file audit, and so is the print view's module",
          'support.source("apps/idiograph/pet_guidance.md")' in audit and 'support.source("apps/idiograph/themes_print.py")' in audit)
    group_sys = themes_ai.group_system(DEMO_QUESTION, 5)
    check("the grouping prompt carries every rule of section 3 as the file words it",
          all(f"{n}. {text}" in group_sys for n, text in rules) and not any(text in group_sys for _, text in questions))
    names_sys = themes_ai.names_system(DEMO_QUESTION)
    check("122: the titles prompt carries rules 5, 6, 8 and 11, the title, its register, negative material and recurrence, and no other",
          all(f"{n}. {text}" in names_sys for n, text in rules if n in (5, 6, 8, 11))
          and not any(f"{n}. {text}" in names_sys for n, text in rules if n not in (5, 6, 8, 11)))
    check("the inline rules that said the same thing are gone, the limit, the reason and the discards kept",
          not hasattr(themes_ai, "LABEL_RULES") and not hasattr(themes_ai, "guidance")
          and "His limit is 5 themes. Make between 4 and 5 themes." in group_sys
          and '"left_out": [{"key": "<key>", "reason": "..."}], "reason": "..."' in group_sys)
    other = scratch / "guidance-edited.md"
    other.write_text("# Edited\n\n## 3. Rules\n\n1. Only one invented rule here.\n5. A title of four words.\n"
                     "   It runs on to a second line.\n\n## 4. Questions\n\n1. One invented question?\n", encoding="utf-8")
    held = themes_ai.GUIDANCE
    try:
        themes_ai.GUIDANCE = other
        edited = (themes_ai.group_system("", 5), themes_ai.names_system(""), themes_ai.review_system(""))
        themes_ai.GUIDANCE = scratch / "no-guidance-here.md"
        missing = [themes_ai.group([{"key": "S:1:0", "sheet": "S", "time": "", "text": "a"}], [], "", "",
                                   {"provider": "anthropic", "key": "k"}),
                   themes_ai.review({"themes": [{"id": "g1"}]}, "", {"provider": "anthropic", "key": "k"}),
                   themes_ai.names(["a"], "", [], "", {"provider": "anthropic", "key": "k"})]
    finally:
        themes_ai.GUIDANCE = held
    check("an edit to the file is what the next prompt says, read afresh on every call",
          "1. Only one invented rule here." in edited[0] and "5. A title of four words. It runs on to a second line." in edited[1]
          and "1. Only one invented rule here." not in edited[1] and "1. One invented question?" in edited[2])
    check("with no guidance file each call is one line and nothing is asked",
          missing == [{"error": themes_ai.NO_GUIDANCE}] * 3)

    # ── B. a board for the review and the print, on a case folder with a second name
    root = scratch / "review-root"
    # a case folder with a second name, assembled here so the sweep in area 12 finds none in this file
    work = demo_copy(root, "P9 - {}-{}".format("Wren", "Testname"), "P9 Wren - EN & ES.xlsx")
    (root / "idiograph-project.json").write_text(json.dumps(
        {"name": "Scratch", "research_question": GRAVITY_QUESTION}), encoding="utf-8")
    path = themes_mod.themes_path(work)
    read = themes_mod.read_cards(work)
    k = [c["key"] for c in read["cards"]]
    texts = {c["key"]: c["text"] for c in read["cards"]}
    quote = next(q for row in read["quotes"].values() for q in row["quotes"])
    qrow = quote["key"].rsplit(":", 1)[0]
    in_row = [key for key in k if key.startswith(qrow + ":")]
    rest = [key for key in k if key not in in_row]
    board = themes_mod.blank_version(read["cards"])
    for i, key in enumerate(in_row + rest[:2]):
        board["cards"][key].update(x=0, y=i * 100)
    for i, key in enumerate(rest[2:4]):
        board["cards"][key].update(x=0, y=600 + i * 100)
    for i, key in enumerate(rest[4:6]):
        board["cards"][key].update(x=900, y=i * 100)
    board["groups"] = [{"id": "g1", "label": "Mornings that belong to the dog", "members": in_row + rest[:2] + ["g3"], "x": 0, "y": -40},
                       {"id": "g2", "label": "A house that holds two", "members": rest[4:6], "x": 900, "y": -40},
                       {"id": "g3", "label": "Walks taken alone", "members": rest[2:4], "x": 0, "y": 560}]
    board["discarded"] = [rest[6]]
    board["ai"] = {"discarded": {rest[6]: "It is about the weather"}}
    board["picks"] = {"g1": [quote["key"]]}
    outline = themes_mod.outline(read, board)
    check("the outline sets the board out theme by theme, a sub-theme nested, the rest unplaced and discarded",
          [t["id"] for t in outline["themes"]] == ["g1", "g2"] and [s["id"] for s in outline["themes"][0]["themes"]] == ["g3"]
          and [s["key"] for s in outline["themes"][0]["statements"]] == in_row + rest[:2]
          and outline["themes"][0]["count"] == f"1 sub-theme · {len(in_row) + 4} statements"
          and outline["themes"][0]["picks"][0]["key"] == quote["key"]
          and [s["key"] for s in outline["unplaced"]] == rest[7:]
          and outline["discarded"] == [dict(outline["discarded"][0], key=rest[6], reason="It is about the weather")])

    # ── C. the review's prompt
    system = themes_ai.review_system(GRAVITY_QUESTION)
    user = themes_ai.review_user(outline)
    check("the review's system prompt carries the question, every rule, every reviewer's question and the shape",
          f"The study asks: {GRAVITY_QUESTION}" in system and all(f"{n}. {t}" in system for n, t in rules)
          and all(f"{n}. {t}" in system for n, t in questions)
          and '{"items": [{"about": "<group id or card key or null>", "question": "<one sentence, a question>", '
              '"rule": "<the rule number it rests on>", "why": "<one sentence grounding it in the board>"}]}' in system)
    check("the board goes theme by theme, ids and titles, statements by key, sheet and timecode, picks, unplaced and discarded",
          "Theme g1: Mornings that belong to the dog" in user and "  Sub-theme g3: Walks taken alone" in user
          and f"  - {in_row[0]} ({DEMO_SHEET}, " in user and themes_mod.quoted(quote["text"]) in user
          and user.index("Theme g1") < user.index("Theme g2") and user.index(f"- {in_row[0]} ") < user.index(f"- {rest[0]} ")
          and "Statements left unplaced:" in user and f"- {rest[7]} (" in user
          and "The reason given: It is about the weather" in user)

    # ── D. reading a review strictly
    known = themes_ai.board_keys(outline)
    item = lambda n, about="g1": {"about": about, "question": f"Does point {n} sit with its title?", "rule": "5",
                                  "why": "The title reads as a topic."}
    good = json.dumps({"items": [item(1), item(2, rest[0]), item(3, None)]})
    parsed = themes_ai.parse_review(good, known)
    check("a good answer reads as questions, each open, about a theme, a statement or the whole board",
          [i["about"] for i in parsed["items"]] == ["g1", rest[0], None]
          and all(i["state"] == "open" and i["rule"] == "5" for i in parsed["items"])
          and parsed["items"][0]["why"] == "The title reads as a topic.")
    check("a fenced answer, or one with words round it, reads the same",
          themes_ai.parse_review(f"```json\n{good}\n```", known) == parsed
          and themes_ai.parse_review(f"Here they are:\n{good}\nThat is all.", known) == parsed)
    many = themes_ai.parse_review(json.dumps({"items": [item(n) for n in range(15)]}), known)
    check("174: past three the first three stay", len(many["items"]) == 3
          and many["items"][-1]["question"] == "Does point 2 sit with its title?")
    odd = themes_ai.parse_review(json.dumps({"items": [
        item(1, "g99"), item(2, "Nowhere:1:0"), item(3, "Theme g2")]}), known)
    check("an about that names nothing on the board is the whole board, and Theme g2 is g2",
          [i["about"] for i in odd["items"]] == [None, None, "g2"])
    odd = themes_ai.parse_review(json.dumps({"items": [
        {"about": "g1", "question": "Is it seen \u2014 here; why?", "rule": "Rule 10", "why": "x"},
        item(1, "g2"), item(1, "g1"), {"about": "g1", "question": "   "}]}), known)
    check("a repeated or empty question goes, the rule is its number, and dashes and semicolons are cleaned",
          len(odd["items"]) == 2 and odd["items"][0]["question"] == "Is it seen, here, why?"
          and odd["items"][0]["rule"] == "10")
    check("a rule that is not one of the rules for a theme, a reviewer's question 14, is left blank",
          [i["rule"] for i in themes_ai.parse_review(json.dumps({"items": [dict(item(1), rule="14"), dict(item(2), rule="11")]}),
                                                      known, rules=range(1, 12))["items"]] == ["", "11"])
    check("an empty answer, one with no questions and one that is not JSON are each one line",
          themes_ai.parse_review('{"items": []}', known) == {"error": themes_ai.NO_QUESTIONS}
          and themes_ai.parse_review(json.dumps({"items": [{"question": ""}]}), known) == {"error": themes_ai.NO_QUESTIONS}
          and themes_ai.parse_review("", known) == {"error": themes_ai.NOT_JSON}
          and themes_ai.parse_review("no json here", known) == {"error": themes_ai.NOT_JSON})
    check("an answer cut off at its length limit says so",
          themes_ai.parse_review(good[:len(good) // 2], known, truncated=True) == {"error": ai_mod.TOO_LONG})

    # ── E. the route, through a transport that stands in for the provider
    real = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, ai_mod.find_key, ai_mod.http_call)
    config_path = scratch / "review" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    sent, replies = [], []

    def wire(method, url, headers, payload, timeout):
        sent.append({"url": url, "payload": payload, "timeout": timeout})
        text = replies[0](payload) if replies else ""
        return 200, json.dumps({"content": [{"type": "text", "text": text}], "stop_reason": "end_turn"})

    def settings(**extra):
        config_path.write_text(json.dumps({"ai_provider": "anthropic", "model": "claude-haiku-4-5", **extra}),
                               encoding="utf-8")

    def snapshot(folder):
        return {str(p): p.read_bytes() for p in sorted(Path(folder).rglob("*")) if p.is_file()}

    try:
        server_mod.CONFIG_PATH = config_path
        server_mod.ROOT_OVERRIDE = str(root)
        ai_mod.find_key = lambda *a, **kw: "k-test"
        ai_mod.http_call = wire
        opened = idiograph_routes.api_themes({"workbook": str(work)})
        body = {**{k: x for k, x in opened["version"].items() if k != "v"}, "cards": board["cards"], "groups": board["groups"],
                "discarded": board["discarded"], "picks": board["picks"], "ai": board["ai"]}
        idiograph_routes.api_themes_save({"workbook": str(work), "version": body})
        settings(ai_suggest=False)
        before = snapshot(root)
        off = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "review"})
        check("with the switch off a review is refused with one line, and nothing is sent or written",
              off == {"error": themes_ai.OFF} and not sent and snapshot(root) == before)
        settings(ai_suggest=True)
        replies[:] = [lambda p: json.dumps({"items": [item(1), item(2, rest[0]), item(3, None)]})]
        got = idiograph_routes.api_themes_ai({"workbook": str(work), "op": "review", "version": "v1"})
        call = sent[-1]
        asked = call["payload"]["messages"][0]["content"]
        check("one call, with the grouping's room and wait, carrying the rules, the questions and the board",
              len(sent) == 1 and call["payload"]["max_tokens"] == themes_ai.GROUP_MAX_TOKENS
              and call["timeout"] == themes_ai.GROUP_TIMEOUT and "Theme g1: Mornings that belong to the dog" in asked
              and all(f"{n}. {t}" in call["payload"]["system"] for n, t in rules + questions)
              and GRAVITY_QUESTION in call["payload"]["system"])
        check("the answer is the review, its time, its model and its questions, each open",
              set(got["review"]) == {"at", "model", "items"} and got["review"]["model"] == "Haiku 4.5"
              and ISO_OFFSET.match(got["review"]["at"]) is not None and len(got["review"]["items"]) == 3
              and got["board"] == "v1" and all(i["state"] == "open" for i in got["review"]["items"]))
        check("asking writes nothing, the workbook and the themes file as they were", snapshot(root) == before)
        sent.clear()
        empty_board = demo_copy(root, "Empty", "Juno - EN & ES.xlsx")
        none = idiograph_routes.api_themes_ai({"workbook": str(empty_board), "op": "review"})
        check("a board with no themes is one line and no call", none == {"error": themes_ai.NOTHING_TO_REVIEW} and not sent)

        # ── F. the review kept with the board, its states and all
        review = dict(got["review"], items=[dict(i) for i in got["review"]["items"]])
        review["items"][0]["state"] = "considered"
        review["items"][1]["state"] = "dismissed"
        idiograph_routes.api_themes_save({"workbook": str(work), "version": dict(body, review=review)})
        kept = json.loads(path.read_text(encoding="utf-8"))["boards"][0]["review"]
        check("the autosave writes the review into the board, under review, with each state",
              [i["state"] for i in kept["items"]] == ["considered", "dismissed", "open"]
              and kept["at"] == review["at"] and kept["model"] == "Haiku 4.5")
        reopened = idiograph_routes.api_themes({"workbook": str(work)})
        check("a reload hands it back as it was left", reopened["review"] == kept)
        idiograph_routes.api_themes_save({"workbook": str(work), "version": body})
        check("a save from a page that sends none leaves it as it was",
              json.loads(path.read_text(encoding="utf-8"))["boards"][0]["review"] == kept)
        tidy = themes_mod.normalise({"review": {"at": "x", "model": "m", "items": [
            {"about": "g1", "question": "Q?", "state": "maybe"}, {"question": "  "}]
            + [{"question": f"Q{n}?", "state": "dismissed"} for n in range(14)]}})["review"]
        check("normalise keeps twelve, an unknown state open, and drops a question with no words",
              len(tidy["items"]) == 12 and tidy["items"][0]["state"] == "open" and tidy["items"][1]["state"] == "dismissed"
              and "review" not in themes_mod.normalise({"review": {"items": [{"question": " "}]}}))
        check("a revision holds the board and not its review, so ticking keeps no revision",
              "review" not in themes_mod.board_state(json.loads(path.read_text(encoding="utf-8"))["boards"][0]))
        idiograph_routes.api_themes_versions({"workbook": str(work), "op": "duplicate", "id": "v1"})
        data = json.loads(path.read_text(encoding="utf-8"))
        check("a duplicate starts with no review of its own, and the board it came from keeps its",
              "review" not in data["boards"][1] and data["boards"][0]["review"] == kept)
        idiograph_routes.api_themes_versions({"workbook": str(work), "op": "switch", "id": "v1"})

        # ── G. the print view, over HTTP
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
        threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
        base = f"http://127.0.0.1:{httpd.server_address[1]}"

        def get(route, **query):
            from urllib.parse import urlencode
            try:
                with urllib.request.urlopen(f"{base}{route}?{urlencode(query)}", timeout=10) as r:
                    return r.status, r.headers.get("Content-Type"), r.read().decode("utf-8")
            except urllib.error.HTTPError as exc:
                return exc.code, exc.headers.get("Content-Type"), exc.read().decode("utf-8")

        two = demo_copy(root, "Two", "Juno - EN & ES.xlsx")
        add_second_sheet(two)
        read2 = themes_mod.read_cards(two)
        across = themes_mod.blank_version(read2["cards"])
        firsts = [next(c["key"] for c in read2["cards"] if c["sheet"] == name) for name in read2["sheets"]]
        across["groups"] = [{"id": "g1", "label": "Across the sheets", "members": firsts, "x": 0, "y": -40}]
        themes_mod.save(two, across, "Two")
        before = snapshot(root)
        try:
            code, kind, page = get("/themes/print", workbook=str(work), board="v1", unplaced="1", binned="1")
            auto = get("/themes/print", workbook=str(work))[2]
            shut = get("/themes/print", workbook=str(work), board="v1", auto="0")[2]
            outside = demo_copy(scratch, "review-elsewhere", "Juno - EN & ES.xlsx")
            far = get("/themes/print", workbook=str(outside))
            gone = get("/themes/print", workbook=str(work), board="v9")
            bare = get("/themes/print", workbook=str(empty_board), unplaced="1", binned="1")[2]
            sheets_page = get("/themes/print", workbook=str(two))[2]
        finally:
            httpd.shutdown()
            httpd.server_close()
        check("the print view is a page the server renders, by GET", code == 200 and kind.startswith("text/html"))
        main = page.split("<main>", 1)[1]
        g1, g3, g2 = (main.index(f"{label}</") for label in ("Mornings that belong to the dog", "Walks taken alone", "A house that holds two"))
        np_head = next(iter(re.findall(r"<h2>Not placed \(\d+\)</h2>", main)), "<h2>Not placed (?)</h2>")
        dc_head = next(iter(re.findall(r"<h2>Experiential statements set aside \(\d+\)</h2>", main)), "<h2>Experiential statements set aside (?)</h2>")
        check("206, 207, 208: theme by theme in canvas order, lettered, a sub-theme under its PET a heading level down in bold",
              g1 < g3 < g2 and '<h2 class="pet-title"><span class="number">A.</span> <span class="title">Mornings that belong to the dog</span></h2>' in main
              and '<h3 class="sub-title">A1. Walks taken alone</h3>' in main
              and '<h2 class="pet-title"><span class="number">B.</span> <span class="title">A house that holds two</span></h2>' in main
              and '<span class="count">' not in main)
        shown = {key: html.escape(text, quote=True) for key, text in texts.items()}
        spots = [main.index(f'<p class="st">{shown[key]} ') for key in in_row + rest[:2]]
        first_at = next(c["time"] for c in read["cards"] if c["key"] == in_row[0])
        check("206: each theme's statements in the order the canvas reads them, each with its sheet and timecode",
              spots == sorted(spots) and spots[-1] < g3
              and f'<p class="st">{shown[in_row[0]]} <span class="ref">({DEMO_SHEET}, {first_at})</span></p>' in main)
        own = html.escape(themes_print.bare(quote["text"]), quote=True)
        check("206: no picked quotes under the title, the picked quote shown once, as its statement's own",
              '<ul class="picks">' not in main and main.count(f'<p class="kq">\u2018{own}\u2019</p>') == 1
              and g1 < main.index(f'<p class="kq">\u2018{own}\u2019</p>') < g3, own)
        check("206, 207: Not placed and Discarded at the end with their counts, the discard with its reason",
              main.index(np_head) > g2 and main.index(dc_head) > main.index(np_head)
              and np_head == "<h2>Not placed (%d)</h2>" % main.split(np_head, 1)[1].split(dc_head, 1)[0].count('<div class="item">')
              and dc_head == "<h2>Experiential statements set aside (1)</h2>"
              and all(shown[key] in main.split(np_head, 1)[1].split(dc_head, 1)[0] for key in rest[7:])
              and shown[rest[6]] in main.split(dc_head, 1)[1] and '<p class="why">It is about the weather</p>' in main)
        head = page.split('<header class="head">', 1)[1].split("</header>", 1)[0]
        check("185, 206, 311: the head carries the case by its pseudonym, the table's name under it and the question, "
              "the date and the board in the foot since 31 October",
              '<h1 class="case">P9 Wren</h1>\n<p class="table-name">Table of Personal Experiential Themes</p>' in head
              and GRAVITY_QUESTION in head and "<title>P9 - Wren - Board 1 - PETs</title>" in page
              and 'class="stamp"' not in head and "P9 Wren (Board 1)" in page and themes_print.when_printed() in page)
        check("never the second part of the folder's name, anywhere on the page",
              "Testname" not in page + auto + shut + bare + sheets_page)
        check("the page opens the print dialog once the fonts have loaded, and auto=0 leaves it shut",
              "const AUTO = true;" in page and "document.fonts.ready" in page and "const AUTO = false;" in shut
              and "const AUTO = true;" in auto)
        check("a workbook outside the root is refused, and so is a board the file does not hold",
              far[0] == 403 and "outside the project folder" in far[2] and "<table" not in far[2]
              and gone[0] == 409 and themes_print.esc(i18n.t("page_print.pets.board_gone")) in gone[2])
        check("a board with no themes prints its header and the Not placed list",
              '<h1 class="case">Empty</h1>' in bare and "Empty (Board 1)" in bare
              and re.search(r"<h2>Not placed \(\d+\)</h2>", bare) and "<h2>Experiential statements set aside" not in bare and "<table" not in bare and '<ol class="summary">' not in bare
              and all(t in bare for t in shown.values()))
        check("185, 206: every statement carries its sheet in its reference, on a case of one sheet as on one of more",
              f'<span class="ref">({DEMO_SHEET}, ' in page and '<p class="st">A statement on row 2 <span class="ref">(2d, ' in sheets_page
              and '<th class="sheet">' not in page + sheets_page)
        check("printing writes nothing anywhere", snapshot(root) == before and not themes_mod.themes_path(outside).exists())
        check("the screen's state says where the print view is, which a server from before it does not",
              opened["print"] == "/themes/print" == idiograph_routes.PRINT_PATH)

        # ── H. a server from before the review
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
        threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{httpd.server_address[1]}/api/themes-ai",
                                         data=json.dumps({"workbook": str(work), "op": "review"}).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
            held_route = server_mod.ROUTES.pop("/api/themes-ai")
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    old = (r.status, json.loads(r.read()))
            except urllib.error.HTTPError as exc:
                old = (exc.code, json.loads(exc.read()))
            finally:
                server_mod.ROUTES["/api/themes-ai"] = held_route
        finally:
            httpd.shutdown()
            httpd.server_close()
        check("a server from before the help answers with the line the page turns into the restart line",
              old == (404, {"error": "No such endpoint.", "code": "no_endpoint"}))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, ai_mod.find_key, ai_mod.http_call = real

    # ── I. the page
    page = support.page_text()
    js = support.text("apps/idiograph/static/themes.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0]
    drawn = fn(js, "thReviewDraw")
    check("with AI features off the tab is hidden and draws nothing, so no line points at Settings (100)",
          # a thematic analysis project's own review under its own test since taaibuild (area 326)
          "if (thAiOn() || thTaAiOn()) {" in drawn and "Turn on AI suggestions" not in drawn and "data-review-settings" not in js)
    asker = fn(js, "thReviewAsk")
    check("a press saves the canvas first, asks once, keeps the list with the board and says to restart on an old server",
          asker.index("await thFlush();") < asker.index("op: 'review', version: board")
          and "v.review = thReviewNext(v.review, data.review);" in asker and "thSoon();" in asker
          and "needsRestart(err) || refusedAs(err, 'unknown_op') ? RESTART_LINE" in asker)
    marker = fn(js, "thReviewSet")
    check("a tick or a cross is saved with the board and is no step of undo, and nothing on the canvas moves",
          "thSoon();" in marker and not re.search(r"thStep|thDone|thRender|thPlace", marker + asker)
          and "out.review = JSON.parse(JSON.stringify(v.review));" in fn(js, "thBody")
          and "review: data.review ? JSON.parse(JSON.stringify(data.review)) : null," in fn(js, "thLoad"))
    shower = fn(js, "thReviewShow")
    check("a question's link selects what it is about and fits it in view, the sidebar left open on Review (114, 183)",
          "thSelectOnly({ kind: about.kind, id: about.id });" in shower and "thFitTo(" in shower
          and shower.index("thPanelFollow();") < shower.index("thFitTo(")
          and "thInspectorOpen" not in shower and "thPanelShow(" not in shower and "thSideOpen" not in shower
          and "thSideShut" not in shower and "thSideShut" not in fn(js, "thPanelDrop"))
    printer = fn(js, "thPrint")
    check("Print opens the print view of the board on the canvas in a tab of its own, its dialog at once since the table is read in the Table view (191), saved first",
          "`/themes/print?${new URLSearchParams({ workbook: TH.path, board: TH.meta.id, auto: '1', ...thIncludesSent(true), ...thWhere() })}`" in printer and "q.auto = '0';" in fn(js, "gtPrintUrl")
          and "window.open(" in printer and "await thFlush();" in printer
          and "if (!TH.printable) { say(RESTART_LINE, 6000); return; }" in printer
          and "TH.printable = !!data.print;" in fn(js, "themesOpen"))

    node = shutil.which("node")
    if not node:
        return skip("the review model in node", "no node on this machine")
    script = scratch / "themes-review.js"
    script.write_text(support.i18n_js() + js + r"""
const card = (row, text) => ({ sheet: 'S', row, line: 0, x: 0, y: 0, text, seconds: row, time: '' });
const v = { cards: { 'S:1:0': card(1, 'one two three four five six seven eight'), 'S:2:0': card(2, 'short words'),
  'S:3:0': card(3, 'gone') }, groups: [], discarded: ['S:3:0'], picks: {} };
const g1 = thMakeGroup(v, ['S:1:0', 'S:2:0'], 'Mornings first');
const review = { at: '2026-10-02T14:05:00+01:00', model: 'Haiku 4.5', items: [
  { about: g1, question: 'A?', state: 'open' }, { about: 'S:1:0', question: 'B?', state: 'open' }] };
const out = {};
out.abouts = [thReviewAbout(v, g1), thReviewAbout(v, 'S:1:0'), thReviewAbout(v, 'S:3:0'), thReviewAbout(v, 'g9'), thReviewAbout(v, null)];
out.marks = [thReviewMark(review, 0, 'considered'), thReviewMark(review, 0, 'considered'), thReviewMark(review, 1, 'dismissed'),
  thReviewMark(review, 1, 'considered'), thReviewMark(review, 5, 'considered'), thReviewMark(review, 0, 'deleted')];
out.states = review.items.map((i) => i.state);
out.made = [thReviewMade(review, new Date('2026-10-02T18:00:00+01:00')), thReviewMade(review, new Date('2026-10-05T09:00:00+01:00')),
  thReviewMade({ at: 'nonsense', model: 'Haiku 4.5' })];
console.log(JSON.stringify(out));
""", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, TZ="Europe/London"))
    if run.returncode != 0:
        return check("the review model runs in node", False, run.stderr.strip()[:300])
    out = json.loads(run.stdout)
    check("a question names a theme by its title, a statement by its first words, a discarded one so, and nothing else",
          out["abouts"][0] == {"kind": "group", "id": "g1", "name": "Mornings first"}
          and out["abouts"][1] == {"kind": "card", "id": "S:1:0", "name": "one two three four five six…", "discarded": False}
          and out["abouts"][2]["discarded"] is True and out["abouts"][3] is None and out["abouts"][4] is None, str(out["abouts"]))
    check("a tick considers, the same again opens it, a cross dismisses, and nothing else is a state",
          out["marks"] == ["considered", "open", "dismissed", "considered", None, None] and out["states"] == ["open", "considered"],
          str(out["marks"]))
