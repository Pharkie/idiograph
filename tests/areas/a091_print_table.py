from __future__ import annotations

import re
import shutil

import openpyxl

import workbook as wb_mod

from .support import DEMO_SHEET, add_second_sheet, check, demo_copy


def test_print_table(scratch):
    print("\n91. The PETs print view as the book's table of Personal Experiential Themes, typeset, lettered and ordered "
          "as the Word document, on landscape A4, each statement a row with its reference on the left and its own quote "
          "on the right, the Word document portrait (206, 212)")
    import html
    import themes as themes_mod
    import themes_print
    import themes_word

    S, F = DEMO_SHEET, "Follow-up"
    K = lambda sheet, row, line=0: themes_mod.card_key(sheet, row, line)

    # ── A. the fixture: an invented case of two sheets, its statements and quotes paired in its cells,
    # the marks a workbook keeps round a quote in each spelling, "(no quote)" holding a place, and a
    # board of three PETs whose ids run against the canvas's order, a sub-theme, a cluster and a
    # fourth level, two notes, a pick, a line since gone, a statement not placed and a discard with
    # the reason an AI proposal gave
    root = scratch / "print-table-root"
    shutil.rmtree(root, ignore_errors=True)
    folder = root / "P{} - {}-{}".format(6, "Hazel", "Testname")
    book = demo_copy(folder, "P6 Hazel - EN & ES.xlsx")
    add_second_sheet(book, F, rows=4)
    cells = {15: ("Digging before the gates open\n\nThe spade kept by the shed", '"we were there before anyone"\n\n(no quote)'),
             17: ("Weeds as company, not a chore", "\u2018they kept me company, that is all\u2019"),
             19: ("The seed tin kept in the hall", "\u201cI never threw it away\u201d"),
             21: ("Nobody visits the plot now", "they stopped coming"),
             23: ("Waking at first light\n\nListening for the rain", '(No Quote)\n\n"still listening"'),
             25: ("Saying the plot is better left", None),
             27: ("A letter from the committee", '"a letter, and a mark on the gate"')}
    wb = openpyxl.load_workbook(book, rich_text=True)
    ws = wb[S]
    cols = wb_mod.detect_columns(ws)
    for r, (es, kq) in cells.items():
        ws.cell(r, cols["es"]).value = es
        ws.cell(r, cols["kq"]).value = kq
    wb.save(book)
    wb.close()
    read = themes_mod.read_cards(book)
    time = {c["key"]: c["time"] for c in read["cards"]}
    board = themes_mod.blank_version(read["cards"])
    spots = {K(S, 15): (0, 100), K(S, 15, 1): (0, 400), K(S, 23): (0, 700), K(S, 23, 1): (0, 1000),
             K(S, 25): (0, 1400), K(S, 17): (2000, 100), K(F, 2): (2000, 300), K(S, 19): (0, 3000), K(S, 21): (0, 3200)}
    for key, (x, y) in spots.items():
        board["cards"][key].update(x=x, y=y)
    gone = K(S, 999)
    board["cards"][gone] = {"x": 0, "y": 3400, "text": "A row since taken out of the workbook"}
    board["groups"] = [
        {"id": "g1", "label": "Weeds as company", "members": [K(S, 17), K(F, 2)], "x": 2000, "y": 40},
        {"id": "g2", "label": "What the plot keeps", "members": [K(S, 19), K(S, 21), gone], "x": 0, "y": 2940},
        {"id": "g3", "label": "Early mornings at the plot", "note": "Before the town is up.",
         "members": [K(S, 15), "g4", K(S, 25)], "x": 0, "y": 40},
        {"id": "g4", "label": "First light", "note": "Kept apart <for now> & on its own\nA second line.",
         "members": [K(S, 15, 1), "g5"], "x": 0, "y": 340},
        {"id": "g5", "label": "Listening", "members": [K(S, 23), "g6"], "x": 0, "y": 640},
        {"id": "g6", "label": "Rain on the roof", "members": [K(S, 23, 1)], "x": 0, "y": 940}]
    board["discarded"] = [K(S, 27)]
    board["ai"] = {"discarded": {K(S, 27): "It is about the committee"}}
    board["picks"] = {"g3": [K(S, 15)]}
    themes_mod.save(book, board, "P6 - Hazel")
    workbook_bytes = book.read_bytes()
    themes_bytes = themes_mod.themes_path(book).read_bytes()
    page = themes_print.page(book, "P6 - Hazel", auto=False, unplaced=True, binned=True)
    shown = themes_print.page(book, "P6 - Hazel", unplaced=True, binned=True)
    main = page.split("<main>", 1)[1].split("</main>", 1)[0]
    outline = themes_word.board_of(book)[0]
    word = themes_word.plain(themes_word.blocks("P6 - Hazel", outline, unplaced=True, binned=True))
    draft = themes_mod.draft_markdown(book, "P6 - Hazel")[0]
    item = lambda text, key: f'<div class="item"><p class="st">{text} <span class="ref">({key[0]}, {time[key[1]]})</span></p>'
    said = lambda text, key, quote: item(text, key) + f'<p class="kq">\u2018{quote}\u2019</p></div>'

    # ── B. the head and the PETs, lettered as the Word document letters them
    check("91: the participant heads the page, the book's Table of Personal Experiential Themes smaller under it",
          '<h1 class="case">P6 Hazel</h1>\n<p class="table-name">Table of Personal Experiential Themes</p>' in page
          and "<title>P6 - Hazel - Board 1 - PETs</title>" in page and "Testname" not in page)
    titles = [(html.unescape(a), html.unescape(b)) for a, b in re.findall(
        r'<h2 class="pet-title"><span class="number">(.*?)</span> <span class="title">(.*?)</span></h2>', main)]
    word_pets = [ln for ln in word if re.match(r"^[A-Z]+\. ", ln)]
    np_head, dc_head = f"<h2>Not placed ({len(outline['unplaced'])})</h2>", f"<h2>Experiential statements set aside ({len(outline['discarded'])})</h2>"
    check("91, 207, 208: the PETs lettered A to C in the order the canvas reads them, which their ids do not give, as the Word document has them",
          titles == [("A.", "Early mornings at the plot"), ("B.", "Weeds as company"), ("C.", "What the plot keeps")]
          and [t["id"] for t in outline["themes"]] == ["g3", "g1", "g2"]
          and word_pets == [f"{x} {t.upper()}" for x, t in titles], str(word_pets))
    check("91, 207, 208: the PET draft carries the same labels, a sub-theme, a group and a group inside it each under its own",
          all(f"\n## {x} {t}\n" in draft for x, t in titles) and "\n### A1. First light\n" in draft
          and "\n#### A1.1 Listening\n" in draft and "\n##### A1.1.1 Rain on the roof\n" in draft)

    # ── C. the statements, each a row, its reference on the left and its own quote on the right
    rest = main.split('<section class="rest">', 1)[1]
    check("91, 207: Not placed and Discarded at the end with their counts, each statement set out the same way, a discard with its reason",
          rest.index(np_head) < rest.index(dc_head) and dc_head == "<h2>Experiential statements set aside (1)</h2>"
          and said("A statement on row 3", (F, K(F, 3)), "a quote on row 3") in rest.split(dc_head, 1)[0]
          and said("A letter from the committee", (S, K(S, 27)), "a letter, and a mark on the gate")[:-6]
          + '<p class="why">It is about the committee</p></div>' in rest.split(dc_head, 1)[1]
          and "<h2>Unplaced</h2>" not in page)

    # ── D. the page agrees with the Word document line for line, under the book's letters and under 1 2 3,
    # a row's left column its statement's line and its right its quote's
    def as_lines(body: str) -> list[str]:
        out = []
        for m in re.finditer(r'<h2 class="pet-title"><span class="number">(.*?)</span> <span class="title">(.*?)</span></h2>'
                             r'|<h[3-6] class="(?:sub-title|group-title)">(.*?)</h[3-6]>|<p class="tnote">(.*?)</p>'
                             r'|<p class="st">(.*?)</p>|<p class="kq">(.*?)</p>|<h2>(.*?)</h2>', body, re.S):
            letter, title, sub, note, st, kq, plain_head = m.groups()
            if letter:
                out.append(f"{letter} {html.unescape(title).upper()}")
            elif note:
                out += [html.unescape(x) for x in note.splitlines()]
            elif st:
                out.append(html.unescape(re.sub(r"<[^>]+>", "", st)))
            elif kq:
                out.append("    " + html.unescape(kq))
            else:
                out.append(html.unescape(sub or plain_head))
        return out

    lines = as_lines(main)
    check("91: the print view and the Word document carry the same headings, notes, statements and quotes in the same order",
          lines == word[2:] and word[:2] == ["P6 Hazel", "Table of Personal Experiential Themes"] and len(lines) > 30, f"{len(lines)} and {len(word) - 2} lines")
    numbered = themes_print.page(book, "P6 - Hazel", auto=False, labels=themes_mod.NUMBERS, unplaced=True, binned=True)
    numbered_lines = as_lines(numbered.split("<main>", 1)[1].split("</main>", 1)[0])
    numbered_word = themes_word.plain(themes_word.blocks("P6 - Hazel", outline, themes_mod.NUMBERS, unplaced=True, binned=True))
    check("91, 212: under 1 2 3 too the landscape page and the Word document agree line for line, PET 1 and PET 1a in their place",
          numbered_lines == numbered_word[2:] and numbered_lines != lines and len(numbered_lines) == len(lines)
          and "PET 1. EARLY MORNINGS AT THE PLOT" in numbered_lines and "PET 1a. First light" in numbered_lines
          and "1a.1.1 Rain on the roof" in numbered_lines and "@page { size: A4 landscape;" in numbered,
          f"{len(numbered_lines)} and {len(numbered_word) - 2} lines")

    # ── G. the keep-whole limits for the landscape page and the narrower column
    check("91: the Board note tick, Print, and the dialog opening once the fonts have loaded stay",
          '<label class="tick"><input type="checkbox" id="board-note" disabled title="This board has no note."> Board note</label>' in page
          and '<button type="button" id="print">Print</button>' in page and "document.fonts.ready" in shown
          and "const AUTO = true;" in shown and "const AUTO = false;" in page)
    check("91: printing writes nothing, the workbook and the themes file as they were",
          book.read_bytes() == workbook_bytes and themes_mod.themes_path(book).read_bytes() == themes_bytes)
