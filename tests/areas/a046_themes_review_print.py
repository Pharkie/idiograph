from __future__ import annotations

import inspect
import json
import re
from pathlib import Path

import ai_suggest as ai_mod

from .a038_polish_items import test_polish_items
from . import support
from .support import (
    DEMO_QUESTION, DEMO_SHEET, GRAVITY_QUESTION, add_second_sheet, check, demo_copy,
)
import idiograph_routes


def test_themes_review_print(scratch):
    print("\n46. Themes, the guidance file and the print view (the AI review went on 11 November 2026, aiout)")
    import html
    import http.server
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
    rules = themes_ai.guidance_items(3)
    check("the guidance file ships beside the app, with its eleven rules, and the PETs reviewer's questions gone with the review",
          shipped.is_file() and themes_ai.GUIDANCE == shipped.resolve()
          and [n for n, _ in rules] == list(range(1, 12))
          and "## 3. Rules for a theme" in shipped.read_text(encoding="utf-8")
          and "Questions a reviewer asks of a grouping" not in shipped.read_text(encoding="utf-8"))
    audit = inspect.getsource(test_polish_items)
    check("it is in the shipped-file audit, and so is the print view's module",
          'support.source("apps/idiograph/pet_guidance.md")' in audit and 'support.source("apps/idiograph/themes_print.py")' in audit)
    names_sys = themes_ai.names_system(DEMO_QUESTION)
    check("122: the titles prompt carries rules 5, 6, 8 and 11, the title, its register, negative material and recurrence, and no other",
          all(f"{n}. {text}" in names_sys for n, text in rules if n in (5, 6, 8, 11))
          and not any(f"{n}. {text}" in names_sys for n, text in rules if n not in (5, 6, 8, 11)))
    other = scratch / "guidance-edited.md"
    other.write_text("# Edited\n\n## 3. Rules\n\n1. Only one invented rule here.\n5. A title of four words.\n"
                     "   It runs on to a second line.\n\n## 4. Questions\n\n1. One invented question?\n", encoding="utf-8")
    held = themes_ai.GUIDANCE
    try:
        themes_ai.GUIDANCE = other
        edited = themes_ai.names_system("")
        themes_ai.GUIDANCE = scratch / "no-guidance-here.md"
        missing = [themes_ai.names(["a"], "", [], "", {"provider": "anthropic", "key": "k"})]
    finally:
        themes_ai.GUIDANCE = held
    check("an edit to the file is what the next prompt says, read afresh on every call",
          "5. A title of four words. It runs on to a second line." in edited and "1. Only one invented rule here." not in edited)
    check("with no guidance file a call is one line and nothing is asked",
          missing == [{"error": themes_ai.NO_GUIDANCE}])

    # ── B. a board for the print, on a case folder with a second name
    root = scratch / "review-root"
    # a case folder with a second name, assembled here so the sweep in area 12 finds none in this file
    work = demo_copy(root, "P9 - {}-{}".format("Wren", "Testname"), "P9 Wren - EN & ES.xlsx")
    (root / "idiograph-project.json").write_text(json.dumps(
        {"name": "Scratch", "research_question": GRAVITY_QUESTION}), encoding="utf-8")
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

    # ── C. the board saved, then printed
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
        empty_board = demo_copy(root, "Empty", "Juno - EN & ES.xlsx")

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

    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, ai_mod.find_key, ai_mod.http_call = real

    # ── I. the page
    page = support.page_text()
    js = support.text("apps/idiograph/static/themes.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0]
    printer = fn(js, "thPrint")
    check("Print opens the print view of the board on the canvas in a tab of its own, its dialog at once since the table is read in the Table view (191), saved first",
          "`/themes/print?${new URLSearchParams({ workbook: TH.path, board: TH.meta.id, auto: '1', ...thIncludesSent(true), ...thWhere() })}`" in printer and "q.auto = '0';" in fn(js, "gtPrintUrl")
          and "window.open(" in printer and "await thFlush();" in printer
          and "if (!TH.printable) { say(RESTART_LINE, 6000); return; }" in printer
          and "TH.printable = !!data.print;" in fn(js, "themesOpen"))
