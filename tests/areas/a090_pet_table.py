from __future__ import annotations

import re
import shutil

import openpyxl

import workbook as wb_mod

from .support import DEMO_SHEET, add_second_sheet, check, demo_copy


def test_pet_table(scratch):
    print("\n90. The PETs in Word as the book's table of Personal Experiential Themes, each statement with its own "
          "quote on the next line, and the print view's quote under each statement (205)")
    import xml.etree.ElementTree as ET
    import zipfile
    from datetime import datetime
    import themes as themes_mod
    import themes_print
    import themes_word

    W = themes_word.W
    tag = lambda name: f"{{{W}}}{name}"
    S, F = DEMO_SHEET, "Follow-up"
    K = lambda sheet, row, line=0: themes_mod.card_key(sheet, row, line)

    # ── A. the fixture: an invented case of two sheets, statements and quotes paired in its cells, the
    # marks a workbook keeps round a quote in each spelling, "(no quote)" holding a place, and a board
    # of three PETs whose ids run against the canvas's order, a sub-theme, a cluster and a fourth level
    root = scratch / "table-root"
    shutil.rmtree(root, ignore_errors=True)
    folder = root / "P{} - {}-{}".format(7, "Alder", "Testname")
    book = demo_copy(folder, "P7 Alder - EN & ES.xlsx")
    add_second_sheet(book, F, rows=4)
    cells = {15: ("Walking out before light\n\nThe lead by the door", '"we went before anyone"\n\n(no quote)'),
             17: ("A frightened dog, not a bad one", "\u2018she was frightened, that is all\u2019"),
             19: ("The bowl kept under the sink", "\u201cI could not throw it out\u201d"),
             21: ("Nobody asks any more", "they stopped asking"),
             23: ("Waking at quarter past five\n\nListening for other dogs", '(No Quote)\n\n"still listening"'),
             25: ("Saying she is better off", None),
             27: ("A note through the door", '"a note, and a mark on the frame"')}
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
    board["cards"][gone] = {"x": 0, "y": 3400, "text": "A line since taken out of the workbook"}
    board["groups"] = [
        {"id": "g1", "label": "A dog who was frightened", "members": [K(S, 17), K(F, 2)], "x": 2000, "y": 40},
        {"id": "g2", "label": "What he keeps", "members": [K(S, 19), K(S, 21), gone], "x": 0, "y": 2940},
        {"id": "g3", "label": "Home life before light", "note": "Before the street wakes.",
         "members": [K(S, 15), "g4", K(S, 25)], "x": 0, "y": 40},
        {"id": "g4", "label": "Mornings", "note": "Kept apart <for now> & on its own\nA second line.",
         "members": [K(S, 15, 1), "g5"], "x": 0, "y": 340},
        {"id": "g5", "label": "Listening", "members": [K(S, 23), "g6"], "x": 0, "y": 640},
        {"id": "g6", "label": "Quarter past five", "members": [K(S, 23, 1)], "x": 0, "y": 940}]
    board["discarded"] = [K(S, 27)]
    board["picks"] = {"g3": [K(S, 15)]}
    themes_mod.save(book, board, "P7 - Alder")
    outline = themes_word.board_of(book)[0]
    np_head, dc_head = f"Not placed ({len(outline['unplaced'])})", f"Experiential statements set aside ({len(outline['discarded'])})"
    made = themes_word.write(book, "P7 - Alder", now=datetime(2026, 10, 6, 15, 0).astimezone(), unplaced=True, binned=True)
    with zipfile.ZipFile(folder / made["name"]) as z:
        parts = {n: z.read(n).decode("utf-8") for n in z.namelist()}
    doc = []
    for p in ET.fromstring(parts["word/document.xml"]).iter(tag("p")):
        style, ind = p.find(f"{tag('pPr')}/{tag('pStyle')}"), p.find(f"{tag('pPr')}/{tag('ind')}")
        runs = [dict({k: r.find(f"{tag('rPr')}/{tag(k)}") is not None for k in ("b", "i", "caps")},
                     text="".join(t.text or "" for t in r.iter(tag("t")))) for r in p.iter(tag("r"))]
        doc.append({"style": style.get(tag("val")) if style is not None else "Normal",
                    "set_in": ind.get(tag("left")) if ind is not None else "",
                    "keep": p.find(f"{tag('pPr')}/{tag('keepNext')}") is not None,
                    "text": "".join(r["text"] for r in runs), "runs": runs})
    texts = [p["text"] for p in doc]
    at = lambda text: doc[texts.index(text)] if text in texts else {}
    nxt = lambda text: doc[texts.index(text) + 1] if text in texts and texts.index(text) + 1 < len(doc) else {}
    said = lambda sheet, row, line=0: f" ({sheet}, {time[K(sheet, row, line)]})"
    walking, lead = "Walking out before light" + said(S, 15), "The lead by the door" + said(S, 15, 1)
    waking, listening = "Waking at quarter past five" + said(S, 23), "Listening for other dogs" + said(S, 23, 1)
    better, scared = "Saying she is better off" + said(S, 25), "A frightened dog, not a bad one" + said(S, 17)
    bowl, nobody, row2 = "The bowl kept under the sink" + said(S, 19), "Nobody asks any more" + said(S, 21), f"A statement on row 2 ({F}, 02:00)"
    missing = "A line since taken out of the workbook (Initial, no longer in the workbook)"
    flags = lambda p: [(r["b"], r["i"], r["caps"]) for r in p.get("runs") or []]

    # ── B. the head and the PETs
    check("90: the participant heads the document under Heading 1, the book's table's name under it as its subtitle",
          doc[0]["style"] == "Heading1" and texts[0] == "P7 Alder"
          and doc[1]["style"] == "Subtitle" and texts[1] == "Table of Personal Experiential Themes"
          and "<dc:title>P7 Alder, Table of Personal Experiential Themes</dc:title>" in parts["docProps/core.xml"]
          and made["name"] == "P7 Alder - PETs (Board 1).docx" and "Testname" not in made["name"] + "".join(parts.values()),
          texts[0])
    pets = [(p["style"], p["text"]) for p in doc if p["style"] == "Heading2"]
    check("90, 207, 208: the PETs lettered A to C in the order the canvas reads them, which their ids do not give, the lists counted",
          pets == [("Heading2", "A. Home life before light"), ("Heading2", "B. A dog who was frightened"),
                   ("Heading2", "C. What he keeps"), ("Heading2", np_head), ("Heading2", dc_head)]
          and [t["id"] for t in outline["themes"]] == ["g3", "g1", "g2"] and dc_head == "Experiential statements set aside (1)", str(pets[:3]))
    check("90: a PET's run bold in All caps, its text kept in his casing, so a copy keeps it, shown in capitals",
          all(flags(at(t)) == [(True, False, True)] for t in ("A. Home life before light", "B. A dog who was frightened"))
          and "<w:b/><w:bCs/><w:caps/>" in parts["word/document.xml"]
          and "A. HOME LIFE BEFORE LIGHT" in themes_word.plain(themes_word.blocks("P7 - Alder", outline, unplaced=True, binned=True))
          and "HOME LIFE" not in parts["word/document.xml"]
          and flags(at(np_head)) == [(False, False, False)] and flags(at(dc_head)) == [(False, False, False)],
          str(flags(at("A. Home life before light"))))
    check("90, 207, 208: a sub-theme in bold a heading down, under its reference, A1",
          at("A1. Mornings").get("style") == "Heading3" and flags(at("A1. Mornings")) == [(True, False, False)])
    check("90, 207, 208: a group, a label inside a sub-theme, in bold italic, A1.1, and a group inside it a heading further down, A1.1.1",
          at("A1.1 Listening").get("style") == "Heading4" and flags(at("A1.1 Listening")) == [(True, True, False)]
          and at("A1.1.1 Quarter past five").get("style") == "Heading5" and flags(at("A1.1.1 Quarter past five")) == [(True, True, False)]
          and '<w:i/><w:iCs/>' in parts["word/styles.xml"].split('w:styleId="Heading4"', 1)[1].split("</w:style>", 1)[0]
          and '<w:i/><w:iCs/>' in parts["word/styles.xml"].split('w:styleId="Heading5"', 1)[1].split("</w:style>", 1)[0])
    check("90: a PET's note and a sub-theme's in italics under their headings, his marks kept as written",
          nxt("A. Home life before light").get("text") == "Before the street wakes."
          and flags(nxt("A. Home life before light")) == [(False, True, False)]
          and [p["text"] for p in doc[texts.index("A1. Mornings") + 1:texts.index("A1. Mornings") + 3]]
          == ["Kept apart <for now> & on its own", "A second line."]
          and all(flags(p) == [(False, True, False)] for p in doc[texts.index("A1. Mornings") + 1:texts.index("A1. Mornings") + 3])
          and "Kept apart &lt;for now&gt; &amp; on its own" in parts["word/document.xml"])

    # ── C. the statements, each with where it is and its own quote on the next line
    refs = [t for p, t in zip(doc, texts) if p["style"] == "Normal" and not p["set_in"] and not flags(p)[0][1]]
    check("90: each statement followed by its sheet's name and its timecode, the second sheet's by its own name",
          all(t in texts for t in (walking, lead, waking, listening, better, scared, bowl, nobody, row2))
          and all(re.search(r" \((Initial|Follow-up), (\d+:)?\d\d:\d\d\)$|, no longer in the workbook\)$", t) for t in refs)
          and len(refs) == len(read["cards"]) + 1, f"{len(refs)} statements")
    quote_lines = {t: nxt(t).get("text") for t in (walking, scared, bowl, nobody, listening, row2)}
    check("90: each statement's own quote on the next line in single curly marks, never doubled whatever marks the workbook kept",
          quote_lines == {walking: "\u2018we went before anyone\u2019", scared: "\u2018she was frightened, that is all\u2019",
                          bowl: "\u2018I could not throw it out\u2019", nobody: "\u2018they stopped asking\u2019",
                          listening: "\u2018still listening\u2019", row2: "\u2018a quote on row 2\u2019"}
          and not any(c in t for t in texts for c in ('"', "\u201c", "\u201d", "\u2018\u2018", "\u2019\u2019")), str(quote_lines))
    check("90: a statement with no quote of its own has no quote line, whether its place holds \"(no quote)\" or nothing",
          nxt(lead).get("text") == "A1.1 Listening" and nxt(waking).get("text") == "A1.1.1 Quarter past five"
          and nxt(better).get("text") == "B. A dog who was frightened"
          and not any(at(t).get("keep") for t in (lead, waking, better))
          and [s["quote"] for s in outline["themes"][0]["statements"]] == ['"we went before anyone"', ""])
    check("90: \"(no quote)\" never printed, in any spelling",
          "no quote" not in "\n".join(texts).lower() and "no quote" not in parts["word/document.xml"].lower())
    check("90: a sub-theme takes its place among the cards where its frame's top sits, the outline giving the order",
          texts.index(walking) < texts.index("A1. Mornings") < texts.index("A1.1.1 Quarter past five") < texts.index(better)
          < texts.index("B. A dog who was frightened")
          and outline["themes"][0]["order"] == [K(S, 15), "g4", K(S, 25)]
          and outline["themes"][0]["themes"][0]["order"] == [K(S, 15, 1), "g5"])
    check("90: no Draft PETs list, no Quotes heading, no picked-quotes list and no key line, the picked quote once as its own",
          not any(t.startswith(("Draft PETs", "Key:", "A first go")) or t == "Quotes" for t in texts)
          and sum("we went before anyone" in t for t in texts) == 1 and "(#" not in "".join(texts))
    rest = texts[texts.index(np_head) + 1:texts.index(dc_head)]
    check("90, 207: Not placed and Discarded under plain headings with their counts at the end, their statements with references and quotes the same way",
          rest[:2] != [] and f"A statement on row 3 ({F}, 03:00)" in rest
          and rest[rest.index(f"A statement on row 3 ({F}, 03:00)") + 1] == "\u2018a quote on row 3\u2019"
          and texts[texts.index(dc_head) + 1:] == ["A note through the door" + said(S, 27), "\u2018a note, and a mark on the frame\u2019"])
    check("90: a statement no longer in the workbook keeps its reference with no longer in the workbook, and no quote",
          missing in texts and nxt(missing).get("text") == np_head
          and [s["quote"] for s in outline["themes"][2]["statements"] if s["missing"]] == [""], missing)

    # ── D. the package
    formed = []
    for text in parts.values():
        try:
            ET.fromstring(text.encode("utf-8"))
            formed.append(True)
        except ET.ParseError:
            formed.append(False)
    styles = parts["word/styles.xml"]
    check("90: every part well formed, no colour, fill, shading, list or table, the participant large, the table's name smaller, the PET headings at the body's size",
          all(formed) and len(parts) == 7
          and not any(w in text for text in parts.values() for w in ("w:color", "w:shd", "w:fill", "w:highlight", "themeColor",
                                                                  "w:tbl", "w:numPr", "numbering"))
          and all('<w:sz w:val="22"/>' in styles.split(f'w:styleId="Heading{n}"', 1)[1].split("</w:style>", 1)[0] for n in (2, 3, 4))
          and '<w:sz w:val="40"/>' in styles.split('w:styleId="Heading1"', 1)[1].split("</w:style>", 1)[0]
          and '<w:sz w:val="28"/>' in styles.split('w:styleId="Subtitle"', 1)[1].split("</w:style>", 1)[0])

    # ── E. the print view: each statement's own quote under it, and in the lists at the end
    page = themes_print.page(book, "P7 - Alder", auto=False, unplaced=True, binned=True)
    item = lambda text, key, quote: (f'<div class="item"><p class="st">{text} <span class="ref">({S}, {time[key]})</span></p>'
                                     f'<p class="kq">‘{quote}’</p></div>')
    quoted_all = [s for t in themes_word.walk(outline["themes"]) for s in t["statements"]] + outline["unplaced"] + outline["discarded"]
    check("90, 206, 212: the print view sets each statement's own quote beside it in single curly marks, once",
          all(item(t, key, q) in page for t, key, q in (("Walking out before light", K(S, 15), "we went before anyone"),
                                                       ("A frightened dog, not a bad one", K(S, 17), "she was frightened, that is all"),
                                                       ("The bowl kept under the sink", K(S, 19), "I could not throw it out"),
                                                       ("Listening for other dogs", K(S, 23, 1), "still listening")))
          and page.count('<p class="kq">') == sum(1 for s in quoted_all if s["quote"])
          and f'The lead by the door <span class="ref">({S}, {time[K(S, 15, 1)]})</span></p></div>' in page
          and "no quote" not in page.lower() and "&quot;" not in page.split("<main>", 1)[1]
          and "‘‘" not in page and "’’" not in page)
    check("90, 206: no picks under any title, and the lists at the end carry each statement's quote the same way",
          '<ul class="picks">' not in page and page.count("we went before anyone") == 1
          and '<p class="kq">‘a quote on row 3’</p>' in page.split(f"<h2>{np_head}</h2>", 1)[1].split(f"<h2>{dc_head}</h2>", 1)[0]
          and '<p class="kq">‘a note, and a mark on the frame’</p>' in page.split(f"<h2>{dc_head}</h2>", 1)[1])
