from __future__ import annotations

import inspect
import json
import re
import shutil

from . import support
from .support import DEMO_QUESTION, check, demo_copy
import idiograph_routes


def test_pet_print(scratch):
    print("\n81. The PET document: the book's table in print, lettered as the Word document and the PET draft, the title, "
          "the case, the date, Not placed and Discarded only when full, the board note by choice (185, 206)")
    import html
    import server as server_mod
    import themes as themes_mod
    import themes_print

    # \u2500\u2500 A. the fixture: the demo's Rowan and Mabel, their marked boards copied from the pristine
    # demo into invented case folders, and a third case with every statement placed
    root = scratch / "pet-print"
    pristine = support.DEMO_PRISTINE
    books = {}
    # each case folder under an invented pseudonym of its own, so the demo's names stay the demo's
    for name, number, called in (("Rowan", 4, "Wren"), ("Mabel", 5, "Iris")):
        book = root / "P{} - {}-{}".format(number, called, "Testname") / f"{name} - EN & ES.xlsx"
        book.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pristine / book.name, book)
        themes_mod.themes_path(book).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pristine / "Working" / f"{book.stem}.themes.json", themes_mod.themes_path(book))
        books[name] = book
    whole = demo_copy(root, "Whole", "Whole - EN & ES.xlsx")
    read_whole = themes_mod.read_cards(whole)
    every = themes_mod.blank_version(read_whole["cards"])
    every["groups"] = [{"id": "g1", "label": "Everything in one", "members": [c["key"] for c in read_whole["cards"]],
                        "x": 0, "y": -40}]
    themes_mod.save(whole, every, "Whole")
    (root / "idiograph-project.json").write_text(json.dumps({"name": "Scratch", "research_question": DEMO_QUESTION}),
                                                 encoding="utf-8")
    NOTE = "Kept the walks apart from the flat for now."
    saved = (server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_MEMORY = {"recent": []}

    def snapshot():
        return {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in sorted(root.rglob("*")) if p.is_file()}

    try:
        idiograph_routes.api_themes_versions({"workbook": str(books["Rowan"]), "op": "note", "id": "v1", "note": NOTE})
        before = snapshot()
        printed = {}
        for name, book in (("Rowan", books["Rowan"]), ("Mabel", books["Mabel"]), ("Whole", whole)):
            printed[name] = idiograph_routes.themes_print_page({"workbook": str(book), "auto": "0", "unplaced": "1", "binned": "1"})
        noted = idiograph_routes.themes_print_page({"workbook": str(books["Rowan"]), "auto": "0", "note": "1"})
        drafts = {name: themes_mod.draft_markdown(book, server_mod.display_case(book.parent.name))[0]
                  for name, book in (("Rowan", books["Rowan"]), ("Mabel", books["Mabel"]), ("Whole", whole))}
        after = snapshot()
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = saved
    page = printed["Rowan"][1]
    head = page.split('<header class="head">', 1)[1].split("</header>", 1)[0]
    between = page.split("</header>", 1)[1].split("<main>", 1)[0]
    main = page.split("<main>", 1)[1]
    read = themes_mod.read_cards(books["Rowan"])
    outline = themes_mod.outline(read, themes_mod.normalise(themes_mod.pick_version(themes_mod.load(books["Rowan"]))))

    # ── B. the head
    check("185: every case prints, by GET's own function, with the dialog shut",
          all(code == 200 and "const AUTO = false;" in text for code, text in list(printed.values()) + [noted]))
    check("185: each case's page headed by its own participant, the case key's dash dropped, never the second name",
          '<h1 class="case">P4 Wren</h1>' in head and '<h1 class="case">P5 Iris</h1>' in printed["Mabel"][1]
          and '<h1 class="case">Whole</h1>' in printed["Whole"][1] and "P4 Wren" not in printed["Mabel"][1] and themes_print.case_title("Juno") == "Juno"
          and "Testname" not in page + noted[1] + printed["Mabel"][1] + "".join(drafts.values()))
    check("185: the research question kept in the head, after the case and the table's name",
          html.escape(DEMO_QUESTION, quote=True) in head and "Research question" in head
          and head.index('<h1 class="case">') < head.index('<p class="table-name">') < head.index(html.escape(DEMO_QUESTION, quote=True)))
    check("185: the PETs marked complete are not said on the printed page (Adam, 31 October)",
          "marked complete" not in page and 'class="done"' not in between)

    # ── C. the board note, out by default and in with note=1
    note_line = f'<p class="note"><span class="label">Board note</span>{NOTE}</p>'
    tick = '<label class="tick"><input type="checkbox" id="board-note"'
    check("185: the board note is out of the default print, and the tick beside Print is off",
          NOTE not in page and f"{tick}> Board note</label>" in page
          and page.index(tick) < page.index('<button type="button" id="print">Print</button>'))
    check("185, 206: with note=1 the note sits under the head, before the first PET, and the tick is on",
          note_line in noted[1].split("</header>", 1)[1].split("<main>", 1)[0]
          and f"{tick} checked> Board note</label>" in noted[1] and NOTE not in noted[1].split("</header>", 1)[0])
    check("185: on a board with no note the tick is greyed, and the tick draws the page again with the dialog shut",
          f'{tick} disabled title="This board has no note."> Board note</label>' in printed["Mabel"][1]
          and "url.searchParams.set('note', '1')" in themes_print.SCRIPT and "url.searchParams.delete('note')" in themes_print.SCRIPT
          and "url.searchParams.set('auto', '0')" in themes_print.SCRIPT and "window.location.replace(url.href)" in themes_print.SCRIPT
          and 'note=str(query.get("note") or "") == "1"' in inspect.getsource(idiograph_routes.themes_print_page))

    # ── D. no list at the head, the PETs numbered as the Word document numbers them
    import themes_word
    nums = themes_mod.pet_numbers(outline["themes"])
    expected = [(nums[t["id"]], t["label"]) for t in outline["themes"]]
    titles = [tuple(html.unescape(x) for x in m) for m in re.findall(
        r'<h2 class="pet-title"><span class="number">(.*?)\.</span> <span class="title">(.*?)</span></h2>', main)]
    check("206: no list of the PETs at the head, the page going from the head to the first PET",
          '<ol class="summary">' not in page and "<section" not in between and "PET 1" not in between
          and main.lstrip().startswith('<section class="block pet hue-'))
    word_pets = [p["runs"][0]["text"] for p in themes_word.blocks("P4 - Wren", outline, unplaced=True, binned=True) if p["style"] == 2][:len(titles)]
    check("206, 207, 208: each PET lettered A to E in canvas order, its title as he wrote it, as the Word document letters it",
          titles == expected and [x for x, _ in titles] == ["A", "B", "C", "D", "E"] and word_pets == [f"{x}. {t}" for x, t in titles],
          str(titles[:2]))

    # ── E. under each heading its note, then its statements, each with its reference and its own quote
    first = main.split('<section class="block pet', 2)[1]
    t0 = outline["themes"][0]
    check("206: a PET's note straight under its title, before its statements",
          re.search(r'</span></h2>\n<p class="tnote">' + re.escape(html.escape(t0["note"], quote=True))
                    + r'</p>\n<div class="item">', first) is not None)
    items = re.findall(r'<div class="item"><p class="st">(.*?) <span class="ref">\((.*?)\)</span></p>'
                       r'(?:<p class="kq">(.*?)</p>)?(?:<p class="why">.*?</p>)?</div>', page)
    every = [s for t in themes_word.walk(outline["themes"]) for s in t["statements"]] + outline["unplaced"] + outline["discarded"]
    check("206: every statement once, followed by its sheet and timecode in brackets",
          len(items) == len(every) == page.count('<div class="item">')
          and all(re.fullmatch(r"Initial, \d\d:\d\d", w) for _, w, _ in items), f"{len(items)} of {len(every)}")
    said = {html.unescape(st): html.unescape(q) for st, _, q in items}
    want = {s["text"]: (f"\u2018{themes_print.bare(s['quote'])}\u2019" if s["quote"] else "") for s in every}
    check("206, 212: each statement's own quote beside it in single curly marks, none where it has none",
          said == want and any(said.values()) and not all(said.values()))
    check("206: no picked quotes under any title, no table and no counts, every statement carrying its own quote",
          '<ul class="picks">' not in page and "<table" not in page and '<span class="count">' not in page
          and "Nothing in it yet." not in main)
    check("185, 311: on paper every page's foot names the participant and the table at the left and the page of how "
          "many at the right, the words escaped so they never close the style",
          re.search(r'@page \{ @bottom-left \{ content: "P4 Wren" " \(Board 1\)" "  ·  " [^;]*"Table of Personal Experiential Themes";', page)
          is not None and '@bottom-right { content: "Page " counter(page) " of " counter(pages) !important;' in page
          and 'content: "a\\22 b\\3C /style\\3E ";' in themes_print.page_foot('a"b</style>'))

    # ── F. the end: Not placed and Discarded only when they hold anything
    full = printed["Rowan"][1].split("</main>", 1)[0].split('<section class="rest">', 1)[-1]
    np_head, dc_head = f"<h2>Not placed ({len(outline['unplaced'])})</h2>", f"<h2>Experiential statements set aside ({len(outline['discarded'])})</h2>"
    check("206, 207: Not placed and Discarded at the end when they hold something, with their counts, set out as a PET's statements are",
          outline["unplaced"] and outline["discarded"] and np_head in full and dc_head in full
          and full.index(np_head) < full.index(dc_head)
          and all(f'<p class="st">{html.escape(s["text"], quote=True)} <span class="ref">(Initial, ' in full
                  for s in outline["unplaced"] + outline["discarded"])
          and "<h2>Unplaced</h2>" not in page)
    empty = printed["Whole"][1]
    check("185: and left out when empty, no heading and no None",
          "<h2>Not placed" not in empty and "<h2>Experiential statements set aside" not in empty and '<section class="rest">' not in empty
          and "None." not in empty and '<span class="number">A.</span>' in empty)

    # ── G. the PET draft, the same numbers
    draft = drafts["Rowan"]
    heads = [ln for ln in draft.splitlines() if ln.startswith("##")]
    subs = [themes_mod.numbered(nums[s["id"]], s["label"]) for t in outline["themes"] for s in t["themes"]]
    ends = [f"## Not placed ({len(outline['unplaced'])})", f"## Experiential statements set aside ({len(outline['discarded'])})"]
    lettered = [ln[3:] for ln in heads if ln.startswith("## ") and ln not in ends]
    check("185, 206, 207: the draft's headings carry the print's numbers and titles in its order, a sub-theme by its number",
          lettered == [f"{x}. {t}" for x, t in titles] and heads[-2:] == ends
          and [ln[4:] for ln in heads if ln.startswith("### ")] == subs
          and [ln.count("#") for ln in heads[:3]] == [2, 3, 2], str(heads[:3]))
    listing = []
    for (x, t), pet in zip(titles, outline["themes"]):
        listing.append(f"- {x}. {t} ({pet['count']})")
        listing += [f"  - {themes_mod.numbered(nums[s['id']], s['label'])} ({s['count']})" for s in pet["themes"]]
    check("185, 206, 207: the draft opens with the same numbered list, a sub-theme a step in under its number, with its count",
          draft.split("\n\n", 2)[1] == "\n".join(listing))
    body = draft.split(f"## A. {expected[0][1]}\n", 1)[1].split("\n### ", 1)[0]
    pick = outline["themes"][0]["picks"][0]
    check("185, 95: under a heading the note, then the statements, each with its sheet and timecode and its own quote "
          "under it, and no picked quote listed",
          body.index(outline["themes"][0]["note"]) < body.index("\n- ")
          and all(f"- {s['text']} ({s['sheet']}, {s['time']})" in body for s in outline["themes"][0]["statements"])
          and all(f"\n  \u2018{themes_mod.bare(s['quote'])}\u2019" in body for s in outline["themes"][0]["statements"] if s["quote"])
          and f"{themes_mod.quoted(pick['text'])} (" not in draft)

    def walked(items):
        for t in items:
            for kind, x in themes_mod.in_order(t):
                if kind == "statement":
                    yield x["text"]
                else:
                    yield from walked([x])

    listed = [ln[2:].rsplit(" (", 1)[0] for ln in draft.split("\n\n", 2)[2].splitlines() if ln.startswith("- ")]
    check("185, 95: the draft lists every statement in the print view's order, a sub-theme where its frame's top sits, "
          "Unplaced and Discarded alike",
          listed == list(walked(outline["themes"])) + [s["text"] for s in outline["unplaced"] + outline["discarded"]])
    check("185: the draft leaves the board note out, and an empty Unplaced or Discarded too",
          NOTE not in draft and "## Not placed" not in drafts["Whole"] and "## Discarded" not in drafts["Whole"]
          and "None." not in drafts["Whole"] and "continued" not in draft and "\nQuotes\n" not in draft)
    mabel = drafts["Mabel"]
    m_out = themes_mod.outline(themes_mod.read_cards(books["Mabel"]),
                               themes_mod.normalise(themes_mod.pick_version(themes_mod.load(books["Mabel"]))))
    second = next(t for t in m_out["themes"] if len(t["themes"]) >= 2)["themes"][1]
    two = themes_mod.numbered(themes_mod.pet_numbers(m_out["themes"])[second["id"]], second["label"])
    check("185, 206, 207: a second sub-theme sits under its PET by its number, b after a, in the draft and the print alike",
          f"\n### {two}\n" in mabel and f"\n  - {two} (" in mabel
          and f'<h3 class="sub-title">{html.escape(two, quote=True)}</h3>' in printed["Mabel"][1], two)
    check("206, 207, 208: the labels run A, A1, A1.1 by default, or PET 1, PET 1a to 1z and then 1aa, and 1a.1 on, from the one place the print, the Word document and the draft take them",
          themes_mod.pet_numbers([{"id": "a", "themes": [{"id": "b", "themes": [{"id": "c"}]}, {"id": "e"}]}, {"id": "d"}])
          == {"a": "A", "b": "A1", "c": "A1.1", "e": "A2", "d": "B"}
          and themes_mod.pet_numbers([{"id": "a", "themes": [{"id": "b", "themes": [{"id": "c"}]}, {"id": "e"}]}, {"id": "d"}], "numbers")
          == {"a": "PET 1", "b": "PET 1a", "c": "1a.1", "e": "PET 1b", "d": "PET 2"}
          and [themes_mod.sub_letter(n) for n in (1, 2, 26, 27)] == ["a", "b", "z", "aa"]
          and not hasattr(themes_mod, "pet_letters") and not hasattr(themes_word, "letter"))

    # ── H. nothing written, and the bars the GETs print keeps
    check("185: printing and drafting write nothing anywhere", before == after)
