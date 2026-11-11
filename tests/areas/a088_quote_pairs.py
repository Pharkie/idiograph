from __future__ import annotations

import json
import shutil

import openpyxl

import export as export_mod
import rounds as rounds_mod
import workbook as wb_mod
from workbook import WorkbookError

from . import support
from .support import DEMO_QUESTION, DEMO_SHEET, check, skip
import idiograph_routes
import idiograph_cli


def test_quote_pairs(scratch):
    print("\n88. A statement and its own key quote: pairs on the turn screen, by place in the workbook, old turns "
          "by order, Quotes to pair, and each statement's own quote downstream (198)")
    import subprocess
    import cli
    import gets as gets_mod
    import locks
    import mcp_server
    import server as server_mod
    import themes as themes_mod
    import themes_ai
    import themes_print

    page = support.page_text()
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    th_js = support.text("apps/idiograph/static/themes.js")
    css = support.text("family/static/style.css", "apps/idiograph/static/distil.css")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    node = shutil.which("node")
    pristine = support.DEMO_PRISTINE

    # an invented project: Juno's pristine copy, its sidecars, and the agents' tick on
    root = scratch / "pairs-root"
    shutil.rmtree(root, ignore_errors=True)
    (root / "Juno" / "Working").mkdir(parents=True)
    book = root / "Juno" / "Juno - EN & ES.xlsx"
    shutil.copy2(pristine / "Juno - EN & ES.xlsx", book)
    for side in (pristine / "Working").glob("Juno - *"):
        shutil.copy2(side, root / "Juno" / "Working" / side.name)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Dogs, a pairs project", "research_question": DEMO_QUESTION,
        "agents": {"allowed": True, "at": "2026-10-06T12:00:00+01:00"}}), encoding="utf-8")
    config_file = scratch / "pairs-config.json"
    config_file.write_text(json.dumps({"root": str(root), "interviewer": "Adam"}), encoding="utf-8")

    # ── A. the old shapes, written into the cells as Excel holds them, and read by order
    shapes = {15: ("Alone and unquoted", None), 17: ("One and one", '"q17"'), 19: ("One with two", '"q19a"\n\n"q19b"'),
              21: ("Two with one\n\nThe second of two", '"q21"'), 23: ("Two with none\n\nThe second with none", None),
              25: (None, '"q25"'), 27: ("Placed first\n\nPlaced second", '(No Quote)\n\n"q27"')}
    wb = openpyxl.load_workbook(book, rich_text=True)
    ws = wb[DEMO_SHEET]
    cols = wb_mod.detect_columns(ws)
    for r, (es, kq) in shapes.items():
        ws.cell(r, cols["es"]).value = es
        ws.cell(r, cols["kq"]).value = kq
    wb.save(book)
    wb.close()
    shutil.copy2(book, scratch / "pairs-shapes.xlsx")

    def turns() -> dict:
        return {r["row"]: r for r in wb_mod.read_case(book)["sheets"][0]["rows"]}

    def cells(r: int) -> tuple:
        held = openpyxl.load_workbook(book, read_only=True)
        try:
            row = next(held[DEMO_SHEET].iter_rows(min_row=r, max_row=r, values_only=True))
            return row[cols["es"] - 1], row[cols["kq"] - 1]
        finally:
            held.close()

    rows = turns()
    P = lambda r: [(p["es"], p["kq"]) for p in rows[r]["pairs"]]
    check("88: a turn's pairs come from its two cells by order, the first quote with the first statement",
          P(17) == [("One and one", '"q17"')] and P(21) == [("Two with one", '"q21"'), ("The second of two", "")]
          and rows[21]["es"] == "Two with one\nThe second of two" and rows[21]["kq"] == '"q21"', str(P(21)))
    check("88: the six old shapes: one with no quote, one and one, one with two, two with one, two with none, a quote alone",
          P(15) == [("Alone and unquoted", "")] and P(17) == [("One and one", '"q17"')]
          and P(19) == [("One with two", '"q19a"'), ("", '"q19b"')]
          and P(21) == [("Two with one", '"q21"'), ("The second of two", "")]
          and P(23) == [("Two with none", ""), ("The second with none", "")] and P(25) == [("", '"q25"')],
          str([P(r) for r in (19, 25)]))
    read = themes_mod.read_cards(book)
    held27 = read["quotes"].get(f"{DEMO_SHEET}:27") or {}
    check('88: "(no quote)" reads as empty and keeps its place, however Excel spells it',
          P(27) == [("Placed first", ""), ("Placed second", '"q27"')] and rows[27]["kq"] == '"q27"'
          and not rows[27]["unpaired"] and [q["key"] for q in held27.get("quotes") or []] == [f"{DEMO_SHEET}:27:1"]
          and wb_mod.quote_entries("(no quote)\n\n x \n\n(No  Quote)") == ["", "x", ""]
          and wb_mod.no_quote(wb_mod.NO_QUOTE) and themes_mod.own_quote(read["quotes"], f"{DEMO_SHEET}:27:0") is None
          and themes_mod.own_quote(read["quotes"], f"{DEMO_SHEET}:27:1")["text"] == '"q27"')
    check("88: Quotes to pair names exactly the turns with a quote whose count differs from the statements'",
          sorted(r for r, x in rows.items() if x["unpaired"]) == [13, 19, 21, 25]
          and not any(rows[r]["unpaired"] for r in (15, 17, 23, 27)),
          str(sorted(r for r, x in rows.items() if x["unpaired"])))
    check("88: an old turn writes nothing until it is edited",
          cells(21) == ("Two with one\n\nThe second of two", '"q21"') and cells(27)[1] == '(No Quote)\n\n"q27"')

    # ── B. a save writes one entry a statement once any quote is there, and an empty cell with none
    saved = wb_mod.save_turn(book, DEMO_SHEET, 21, None, None, None,
                             pairs=[{"es": "Two with one", "kq": '"q21"'}, {"es": "The second of two", "kq": ""}])
    check("88: a save of a turn with a quote writes one entry a statement, \"(no quote)\" for one with none",
          cells(21) == ("Two with one\n\nThe second of two", '"q21"\n\n(no quote)') and saved["changed"]
          and saved["unpaired"] is False and saved["pairs"] == [{"es": "Two with one", "kq": '"q21"'},
                                                                {"es": "The second of two", "kq": ""}])
    rows = turns()
    check("88: saving the turn writes it paired, so it leaves Quotes to pair, and the others stay",
          not rows[21]["unpaired"] and sorted(r for r, x in rows.items() if x["unpaired"]) == [13, 19, 25])
    wb_mod.save_turn(book, DEMO_SHEET, 17, None, None, None, pairs=[{"es": "One and one", "kq": ""}])
    quiet = wb_mod.save_turn(book, DEMO_SHEET, 23, None, None, None,
                             pairs=[{"es": "Two with none", "kq": ""}, {"es": "The second with none", "kq": ""}])
    check("88: a turn with no quote keeps its cell empty, and one whose last quote goes has it emptied",
          cells(23) == ("Two with none\n\nThe second with none", None) and quiet["changed"] is False
          and cells(17) == ("One and one", None))
    same = wb_mod.save_turn(book, DEMO_SHEET, 27, None, None, None,
                            pairs=[{"es": "Placed first", "kq": ""}, {"es": "Placed second", "kq": '"q27"'}])
    check("88: a cell that reads the same, Excel's \"(No Quote)\" included, is left exactly as it was",
          same["changed"] is False and cells(27)[1] == '(No Quote)\n\n"q27"')
    twice = wb_mod.save_turn(book, DEMO_SHEET, 23, None, None, None,
                             pairs=[{"es": "Two with none", "kq": '"the same words"'},
                                    {"es": "The second with none", "kq": '"the same words"'}])
    read = themes_mod.read_cards(book)
    check("88: the same words may be the quote of two pairs, each its own statement's",
          cells(23)[1] == '"the same words"\n\n"the same words"' and twice["unpaired"] is False
          and [q["key"] for q in read["quotes"][f"{DEMO_SHEET}:23"]["quotes"]] == [f"{DEMO_SHEET}:23:0", f"{DEMO_SHEET}:23:1"])
    loose = wb_mod.save_turn(book, DEMO_SHEET, 25, None, None, None,
                             pairs=[{"es": "", "kq": '"q25"'}, {"es": "A statement at last", "kq": ""}])
    check("88: a quote with no statement is kept, after the pairs that have one, and the turn stays to pair",
          cells(25) == ("A statement at last", '(no quote)\n\n"q25"') and loose["unpaired"] is True
          and loose["pairs"] == [{"es": "A statement at last", "kq": ""}, {"es": "", "kq": '"q25"'}])
    check("88: the cell rule in one place: pairs_to_cells, quote_entries and pairs_of",
          wb_mod.pairs_to_cells([("a", ""), ("b", "x")]) == ("a\n\nb", "(no quote)\n\nx")
          and wb_mod.pairs_to_cells([("a", ""), ("", "")]) == ("a", None)
          and wb_mod.pairs_to_cells([]) == (None, None)
          and wb_mod.pairs_of("a\n\nb", "(no quote)\n\nx") == [{"es": "a", "kq": ""}, {"es": "b", "kq": "x"}])

    # the save through the page's own route, with the pairs and with the old fields
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, locks.WAIT)
    try:
        server_mod.CONFIG_PATH = config_file
        server_mod.ROOT_OVERRIDE = str(root)
        server_mod.STATE_MEMORY = {"recent": []}
        through = idiograph_routes.api_commit({"path": str(book), "sheet": DEMO_SHEET, "row": 19, "en": "",
                                         "pairs": [{"es": "One with two", "kq": '"q19a"'},
                                                   {"es": "A second for the second", "kq": '"q19b"'}]})
        old_page = idiograph_routes.api_commit({"path": str(book), "sheet": DEMO_SHEET, "row": 15, "en": "",
                                          "es": "Alone and unquoted", "kq": ""})
        check("88: /api/commit writes the pairs and answers them as they now read, with unpaired",
              through["unpaired"] is False and through["pairs"][1] == {"es": "A second for the second", "kq": '"q19b"'}
              and cells(19) == ("One with two\n\nA second for the second", '"q19a"\n\n"q19b"')
              and through["state"] == rounds_mod.HAS_CONTENT)
        check("88: a page from before the pairs still saves its two fields as text",
              old_page["changed"] is False and cells(15) == ("Alone and unquoted", None))
        try:
            idiograph_routes.api_commit({"path": str(book), "sheet": DEMO_SHEET, "row": 19, "pairs": "a, b"})
            bad = False
        except WorkbookError as exc:
            bad = "pairs" in str(exc)
        check("88: pairs that are not a list of pairs are refused with a line", bad)
        opened = idiograph_routes.api_open({"path": str(book)})
        orow = next(r for s in opened["sheets"] for r in s["rows"] if r["row"] == 25)
        check("88: the case the page opens carries each turn's pairs and whether it is to pair",
              orow["pairs"] == [{"es": "A statement at last", "kq": ""}, {"es": "", "kq": '"q25"'}] and orow["unpaired"] is True)
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, locks.WAIT = kept

    # ── C. the turn screen: a field a statement with its key quote under it
    pair_html = fn(app, "pairHtml")
    # the current passage's card since 17 October (172), where the pairs stood in the panel, `section.desk`
    desk = page.split('<div class="es-card" id="es-card">', 1)[1].split('<textarea id="en"', 1)[0]
    add_btn = desk.split('id="pair-add"', 1)[1].split("</button>", 1)[0]
    check("88: Add another, at the card's foot under the last pair, adds an empty pair and gives its statement the caret",
          # in a thematic analysis project it takes the selected words as a new extract (codes, 2 November 2026)
          add_btn.endswith("Add another")
          and "$('pair-add').onclick = () => (typeof cxOn === 'function' && cxOn() ? commitQuote() : addAnother());" in app
          and "insertPair({ es: '', kq: '' });" in fn(app, "addAnother")
          and "el.querySelector('.pair-es').focus();" in fn(app, "addAnother")
          and desk.index('id="pairs"') < desk.index('id="ai-block"') < desk.index('id="pair-add"'))
    remove = fn(app, "removePair")
    check("88: Remove on a pair, the cross until 14 October (135), a bin since 18 October (186), removes it, one step "
          "of undo that puts it back where it stood, and a turn keeps one pair",
          '''<button type="button" class="pair-remove" data-remove="${id}" title="${escAttr(t('distil.pair.remove'))}" aria-label="${escAttr(t('distil.pair.remove'))}">''' in pair_html
          and "const PAIR_CROSS" not in app
          and "if (remove) removePair(remove.closest('.pair'));" in app and "undoPush({" in remove
          and "if (!pairEls().length) insertPair({ es: '', kq: '' });" in remove
          and "insertPair(entry.held, entry.place);" in fn(app, "pairPut") and ".pair-remove" in css)
    check("88: the pair being worked on is the one whose statement or quote last had the focus, else the last",
          "if (el) S.pairFocus = el.dataset.pid;" in app
          and "return els.find((el) => el.dataset.pid === S.pairFocus) || els[els.length - 1] || null;" in fn(app, "workingPair")
          and "S.pairFocus = null;" in fn(app, "drawTurn"))
    check("88: q, and Cmd for another piece, go into the pair being worked on while its key quote is empty, and else "
          "into a pair of their own under the last, as until 14 October, where from then to 16 October a quote there "
          "was replaced in place (136, 153)",
          "quoteTarget(pairsNow(), workingPlace())" in fn(app, "commitQuote")
          # the pieces kept for undo each with its passage, since a quote may take in her passages next to it (301)
          and "S.pending.map((p) => ({ ...p, key: p.key || row.key }))" in fn(app, "commitQuote")
          and "insertPair({ es: '', kq: quote })" in fn(app, "commitQuote")
          and "quoteOut(pairsNow(), entry.place, entry.quote)" in fn(app, "quotePut"))
    check("88: a candidate taken fills the empty statement of the pair being worked on, or comes in as a pair",
          "candidateTarget(pairsNow(), workingPlace())" in fn(app, "takeCandidate")
          and "insertPair({ es: text, kq: '' })" in fn(app, "takeCandidate"))
    check("88: Cmd + Enter saves the pairs, and the old fields go beside them for a server from before",
          "pairs, es: cells.es, en: $('en').value, kq: cells.kq" in fn(app, "commit")
          and "row.unpaired = !!data.unpaired;" in fn(app, "commit") and "drawToPair();" in fn(app, "commit")
          and "if (MOD(e) && e.key === 'Enter') { e.preventDefault(); pressAct(); return; }" in app)
    check("88: Enter goes from a statement to its key quote and on, never breaking a line in a pair",
          "pairEnter(e.target);" in app and "el.querySelector('.pair-kq').focus();" in fn(app, "pairEnter")
          and "else addAnother();" in fn(app, "pairEnter"))
    find_card = page.split('id="find"', 1)[1].split("</section>", 1)[0]
    check("88: Quotes to pair stands under Find, each turn a line that opens it, and only while it holds one",
          '<h3 class="section-label">Quotes to pair</h3>' in find_card and 'id="find-pair-list"' in find_card
          and "return S.flat.filter((r) => r.stop && r.unpaired);" in fn(app, "toPairRows")
          and "$('find-pair').hidden = !rows.length;" in fn(app, "drawToPair")
          and "goTo(row.pos)" in fn(app, "openToPair") and "drawToPair();" in fn(app, "openFind"))

    # the rules the page runs, in node, against the server's own
    if not node:
        skip("88: the pair rules in node", "no node on this machine")
    else:
        cases = [[{"es": "a", "kq": ""}, {"es": "b", "kq": "x"}], [{"es": "a", "kq": ""}], [{"es": "", "kq": "y"}],
                 [{"es": "a", "kq": "(No quote)"}, {"es": "", "kq": ""}, {"es": "b", "kq": "z"}],
                 [{"es": "", "kq": "w"}, {"es": "c", "kq": ""}]]
        olds = [[["Alone"], []], [["One"], ["q"]], [["One"], ["q1", "q2"]], [["One", "Two"], ["q"]], [["One", "Two"], []],
                [[], ["q"]], [["One", "Two"], ["(no quote)", "q"]]]
        script = scratch / "pairs-check.js"
        script.write_text(
            "const q = require(process.argv[2]);\n"
            f"const cases = {json.dumps(cases)};\nconst olds = {json.dumps(olds)};\n"
            "const out = {};\n"
            "out.cells = cases.map((c) => q.pairsToCells(c));\n"
            "out.olds = olds.map(([s, k]) => q.pairsByOrder(s, k));\n"
            "const two = [{ es: 'a', kq: '' }, { es: 'b', kq: '' }];\n"
            "out.focus = q.quoteTarget(two, 0);\n"
            "out.last = q.quoteTarget(two, -1);\n"
            "out.full = q.quoteTarget([{ es: 'a', kq: 'x' }, { es: 'b', kq: 'y' }], 0);\n"
            "out.same = q.quoteTarget([{ es: 'a', kq: '\"same\"' }, { es: 'b', kq: '' }], 1);\n"
            "out.fill = q.candidateTarget([{ es: 'a', kq: '' }, { es: '', kq: 'x' }], 1);\n"
            "out.add = q.candidateTarget([{ es: 'a', kq: '' }], 0);\n"
            "console.log(JSON.stringify(out));\n", encoding="utf-8")
        ran = subprocess.run([node, str(script), str(support.source("family/static/quote.js"))], capture_output=True, text=True, encoding="utf-8")
        if ran.returncode != 0:
            check("88: the pair rules run in node", False, ran.stderr.strip()[:300])
        else:
            out = json.loads(ran.stdout)
            # the page joins a field's entries one a line, the cell one a blank line
            expect = []
            for c in cases:
                es, kq = wb_mod.pairs_to_cells([(p["es"], p["kq"]) for p in c])
                expect.append({"es": (es or "").replace("\n\n", "\n"), "kq": (kq or "").replace("\n\n", "\n")})
            check("88: in node, the page writes the cells as the server does, pair for pair",
                  out["cells"] == expect, f"{out['cells']} {expect}")
            check("88: in node, the old shapes pair by order as the server pairs them",
                  out["olds"] == [wb_mod.pair_entries(s, wb_mod.quote_entries("\n\n".join(k)) if k else [])
                                  for s, k in olds], str(out["olds"]))
            check("88: in node, q goes into the pair with the focus, else the last, and a pair with a quote gets one of "
                  "its own under the last, as until 14 October and again since 16 October (136, 153)",
                  out["focus"] == {"place": 0, "added": False, "old": ""}
                  and out["last"] == {"place": 1, "added": False, "old": ""}
                  and out["full"] == {"place": 2, "added": True, "old": ""}, str([out["focus"], out["full"]]))
            check("88: in node, the same words go into a second pair as its own quote",
                  out["same"] == {"place": 1, "added": False, "old": ""})
            check("88: in node, a candidate fills an empty statement of the pair being worked on, or adds a pair",
                  out["fill"] == {"place": 1, "added": False} and out["add"] == {"place": 1, "added": True})

    # ── D. downstream: a statement's own quote, a PET's picks from its statements' own, an old pick kept
    read = themes_mod.read_cards(book)
    board = themes_mod.blank_version(read["cards"])
    k13 = [f"{DEMO_SHEET}:13:{i}" for i in range(3)]
    board.update(groups=[{"id": "g1", "label": "Kept apart", "members": [f"{DEMO_SHEET}:21:1", f"{DEMO_SHEET}:27:1"], "x": 0, "y": 0},
                         {"id": "g2", "label": "The first of two", "members": [f"{DEMO_SHEET}:21:0", k13[1]], "x": 900, "y": 0}],
                 picks={"g1": [f"{DEMO_SHEET}:21:0", f"{DEMO_SHEET}:27:1"]})
    kept_picks = themes_mod.normalise(board, themes_mod.quote_keys(read["quotes"]))["picks"]
    check("88: a quote picked already stays picked when its statement sits under another PET, never dropped by itself",
          kept_picks["g1"] == [f"{DEMO_SHEET}:21:0", f"{DEMO_SHEET}:27:1"])
    target = themes_ai.names_target(read, board, "g1")
    user = themes_ai.pet_user(target)
    check("88: a statement sent to the AI with its quote sends its own, and a picked one stays marked",
          user.count('"q27"') == 1 and '"q21"' not in user and "(picked)" in user
          and user.index("Placed second") < user.index('"q27"'), f"{user.count('(picked)')} picked")
    themes_mod.save(book, board, "Juno")
    html = themes_print.page(book, "Juno", auto=False)
    check("88: the print view carries the picked quotes and never the mark",
          "q27" in html and "q21" in html and "no quote" not in html.lower())
    out_csv = scratch / "pairs-export.csv"
    export_mod.export(book, out_csv, themes=(themes_mod.themes_path(book), None), guard=False)
    csv_text = out_csv.read_text(encoding="utf-8-sig")
    check("88: the CSV export lists each statement once and never the mark",
          csv_text.count("Placed second") == 1 and csv_text.count("A second for the second") == 1
          and "no quote" not in csv_text.lower())

    # the GETs card's quote: a statement's own, a PET's picks resolved by key, a copy's "(no quote)" as none
    snap = gets_mod.snapshot(book)
    es_card = lambda key: gets_mod.item_of(snap, f"Juno/es/{key}", {})
    pet = gets_mod.item_of(snap, "Juno/g1", {})
    check("88: on the GETs screen a statement's card carries its own quote",
          [q["key"] for q in es_card(f"{DEMO_SHEET}:21:0")["quotes"]] == [f"{DEMO_SHEET}:21:0"]
          and es_card(f"{DEMO_SHEET}:21:1")["quotes"] == [] and es_card(k13[1])["quotes"] == []
          and snap["lines"][f"{DEMO_SHEET}:21:1"]["quotes"] == ['"q21"'])
    check("88: a PET's card keeps its picks, one of another PET's statement's quote too, and a row starts with an own quote",
          [q["key"] for q in pet["picks"]] == [f"{DEMO_SHEET}:21:0", f"{DEMO_SHEET}:27:1"]
          and gets_mod.first_quote([es_card(f"{DEMO_SHEET}:21:1"), es_card(f"{DEMO_SHEET}:21:0")], snap)["key"] == f"{DEMO_SHEET}:21:0")
    copy_line = {"sheet": "S", "row": 3, "time": "00:31", "seconds": 31, "quotes": ["(no quote)", '"b"']}
    check("88: a GETs copy kept before the pairs reads \"(no quote)\" as none, and a statement takes its own place",
          gets_mod.line_quotes(copy_line, "S:3:0") == [] and [q["key"] for q in gets_mod.line_quotes(copy_line, "S:3:1")] == ["S:3:1"]
          and [q["key"] for q in gets_mod.line_quotes(copy_line)] == ["S:3:1"])

    # a board follows a pair removed on the turn screen, its cards and its picks by their words
    wb_mod.save_turn(book, DEMO_SHEET, 27, None, None, None, pairs=[{"es": "Placed second", "kq": '"q27"'}])
    stored = themes_mod.current_version(themes_mod.load(book))
    again = themes_mod.read_cards(book)
    followed = themes_mod.follow(stored, again["cards"], again["quotes"])
    g1 = next(g for g in followed["groups"] if g["id"] == "g1")
    check("88: a board follows a pair removed on its turn, the card and its pick taking the place the words moved to",
          f"{DEMO_SHEET}:27:0" in g1["members"] and f"{DEMO_SHEET}:27:1" not in g1["members"]
          and followed["picks"]["g1"] == [f"{DEMO_SHEET}:21:0", f"{DEMO_SHEET}:27:0"], str(followed["picks"]))

    # the Inspector, in node: a card shows its own quote, a label its statements' own and its picks
    if node:
        script = scratch / "pairs-panel.js"
        script.write_text(support.i18n_js() + th_js + r"""
const card = (sheet, row, line) => ({ sheet, row, line, x: 0, y: 0, text: `${row}.${line}`, seconds: row * 10, time: '' });
const v = { cards: { 'S:3:0': card('S', 3, 0), 'S:3:1': card('S', 3, 1), 'S:5:0': card('S', 5, 0) },
  groups: [], discarded: [], picks: {} };
const g1 = thMakeGroup(v, ['S:3:1', 'S:5:0'], 'One');
const g2 = thMakeGroup(v, ['S:3:0'], 'Two');
thTogglePick(v, g1, 'S:3:0');
const quotes = { 'S:3': { seconds: 30, time: '00:30', quotes: [{ key: 'S:3:0', text: 'zero' }, { key: 'S:3:1', text: 'one' }] } };
const out = {};
out.card = thPanelRows(v, { kind: 'card', id: 'S:3:1' }, quotes, ['S']).map((r) => r.quotes.map((q) => q.key));
out.none = thPanelRows(v, { kind: 'card', id: 'S:5:0' }, quotes, ['S']).map((r) => r.quotes.length);
out.label = thPanelRows(v, { kind: 'group', id: g1 }, quotes, ['S']).map((r) => r.quotes.map((q) => q.key));
out.other = thPanelRows(v, { kind: 'group', id: g2 }, quotes, ['S']).map((r) => r.quotes.map((q) => q.key));
const line = { sheet: 'S', row: 3, time: '00:30', seconds: 30, quotes: ['', '(no quote)', 'two'] };
out.gt = [gtLineQuotes(line).map((q) => q.key), gtLineQuotes(line, 'S:3:2').map((q) => q.key), gtLineQuotes(line, 'S:3:0').length];
out.at = gtQuoteAt({ lines: { 'S:3:0': line, 'S:3:2': line } }, 'S:3:2').text;
console.log(JSON.stringify(out));
""", encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if ran.returncode != 0:
            check("88: the Inspector's quotes run in node", False, ran.stderr.strip()[:300])
        else:
            out = json.loads(ran.stdout)
            check("88: in node, a card's Inspector shows its own quote alone, and none when it has none",
                  out["card"] == [["S:3:1"]] and out["none"] == [0], str(out))
            check("88: in node, a label shows its statements' own quotes with its picks, another statement's pick kept in sight",
                  out["label"] == [["S:3:0", "S:3:1"], []] and out["other"] == [["S:3:0"]], str(out))
            check("88: in node, the GETs screen reads a copy by place, \"(no quote)\" and an empty place as none",
                  out["gt"] == [["S:3:2"], ["S:3:2"], 0] and out["at"] == "two", str(out["gt"]))
    else:
        skip("88: the Inspector's quotes in node", "no node on this machine")

    # ── E. the command line and the MCP tool
    def run(*args) -> tuple[int, str, str]:
        return cli.run(["--root", str(root), "--config", str(config_file), *args])

    def spec(name: str, value) -> str:
        path = scratch / f"pairs-{name}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return str(path)

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, locks.WAIT)
    try:
        server_mod.CONFIG_PATH = config_file
        server_mod.ROOT_OVERRIDE = str(root)
        server_mod.STATE_MEMORY = {"recent": []}
        code, text, _ = run("turn", "show", "Juno", DEMO_SHEET, "19-25")
        check("88: turn show prints each statement with its own quote under it, and a quote with no statement on its own",
              code == 0 and (f'Statement: One with two  ({DEMO_SHEET}:19:0)\n    Quote: "q19a"\n'
                             f'  Statement: A second for the second  ({DEMO_SHEET}:19:1)\n    Quote: "q19b"') in text
              and (f'  Statement: Two with one  ({DEMO_SHEET}:21:0)\n    Quote: "q21"\n'
                   f'  Statement: The second of two  ({DEMO_SHEET}:21:1)\n') in text
              and 'Quote, with no statement: "q25"' in text, f"{text.count('Quote')} quotes shown")
        code, text, _ = run("statements", "Juno")
        check("88: statements gives each its own key quote under it",
              code == 0 and f'  Quote {DEMO_SHEET}:21:0: "q21"' in text and f"Quote {DEMO_SHEET}:25:1, with no statement" in text)
        words = turns()[29]["text"].split()
        said = " ".join(words[:5]).strip(" ,.")
        code, text, err = run("turn", "write", "Juno", DEMO_SHEET, "29", "--from", spec("pairs", {
            "pairs": [{"statement": "An invented first", "quote": said}, {"statement": "An invented second", "quote": ""}]}),
                              "--note", "Pair turn 29", "--tool", "Claude Code")
        check("88: turn write takes pairs, writing the cell one quote a statement as the turn screen does",
              code == 0 and cells(29) == ("An invented first\n\nAn invented second", f'"{said}"\n\n(no quote)'), err.strip()[:200])
        before = book.read_bytes()
        code, _, err = run("turn", "write", "Juno", DEMO_SHEET, "29", "--from", spec("uneven", {
            "statements": ["An invented first", "An invented second"], "quotes": [said]}), "--note", "Uneven")
        check("88: quote and statement lists of different lengths are refused, nothing written",
              code == 1 and "1 quote for 2 statements" in err and "send pairs" in err and book.read_bytes() == before, err)
        code, _, err = run("turn", "write", "Juno", DEMO_SHEET, "29", "--from", spec("placed", {
            "statements": ["An invented first", "An invented second"], "quotes": ["", said]}), "--note", "Placed")
        check("88: unless every quote is placed, an empty one for a statement with none",
              code == 0 and cells(29)[1] == f'(no quote)\n\n"{said}"', err)
        code, _, err = run("turn", "write", "Juno", DEMO_SHEET, "29", "--from", spec("both", {
            "pairs": [{"statement": "x", "quote": ""}], "statements": ["x"]}), "--note", "Both")
        check("88: pairs with the two lists beside them is refused", code == 1 and idiograph_cli.PAIRS_OR_LISTS in err, err)
        srv = mcp_server.Server(str(root), config=str(config_file))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                           "clientInfo": {"name": "claude-ai", "version": "0.1.0"}}}))
        listed = srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))
        tool =next(t for t in listed["result"]["tools"] if t["name"] == "turn_write")
        written = srv.receive(json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "turn_write", "arguments": {"case": "Juno", "sheet": DEMO_SHEET, "row": 31, "request": "Pair turn 31",
                                                "pairs": [{"statement": "An invented third", "quote": ""}]}}}))
        check("88: the MCP tool turn_write takes pairs and says so",
              "pairs" in tool["inputSchema"]["properties"] and "send pairs" in tool["description"]
              and written["result"]["isError"] is False and cells(31)[0] == "An invented third", str(written)[:300])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, locks.WAIT = kept
