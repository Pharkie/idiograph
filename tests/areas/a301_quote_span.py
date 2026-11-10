"""Area 301: one quote across adjacent passages of the same speaker (quotespan, 30 October 2026, Adam: "Adjacent
passages may combine into one block quote with a timecode range (e.g. T2, 36:18–37:46) when order is preserved").

A statement's quote may take in the same speaker's passages next to its own, still one quote, kept in its
statement's own row as the words alone, its pieces in transcript order joined with an ellipsis, so its key holds and
an older Idiograph shows the same words. Which passages it takes in is found from its words each time it is read
(`workbook.quote_reach`, `quoteReach` in quote.js). Adjacent is the same speaker's passage just before or after with
nothing but the interviewer's turns between, so no participant passage, hers or another speaker's, is skipped.

What is checked, on an invented interview about a first spring of beekeeping, Wren and Hollis, a couple, and the
interviewer: a quote across three of Wren's passages with the interviewer between, saved through the page's own
write and read back with its key unchanged and its range, "00:10–00:52", on the quote and its statement's card; the
interviewer's words, Hollis's words, a passage of Wren's skipped and one across Hollis's passage all refused by
the rule; the range in the print view's table, the PDF made from it (a printer of the suite's own standing in for
the browser), the Word document and the GETs file's line; `turn write` taking such a quote with a dry run that
writes nothing and refusing each bad one with its line, nothing written; and on the page, in node over distil.js's
own functions, the wash laid on each passage the quote draws from, the pieces of another passage's quote naming
it, the quote being built across two passages, and the refusals of a piece in the interviewer's turn, in
Hollis's passage and in a passage further off."""
from __future__ import annotations

import datetime as dt
import json
import shutil
import zipfile
from pathlib import Path

import openpyxl

import workbook as wb_mod

from . import support
from .support import check, skip

SHEET = "Interview"
# row, speaker, timecode in seconds, words
TURNS = [
    (2, "Adam", 0, "Tell me about the bees in that first spring."),
    (3, "Wren", 10, "That spring the whole village wanted a piece of me, the shop, the choir, the new hives."),
    (4, "Adam", 40, "Mm."),
    (5, "Wren", 46, "I thought the bees would only be one more thing to do, another list on the fridge."),
    (6, "Adam", 50, "And was it?"),
    (7, "Wren", 52, "No. When the smoker puffed and the frames came up I felt 100% awake, the lists all gone."),
    (8, "Hollis", 80, "She stayed out there all afternoon with bees on her hat."),
    (9, "Wren", 91, "Not all afternoon. Twenty minutes or so, and they kept to my gloves."),
    (10, "Adam", 100, "What was that like?"),
    (11, "Wren", 105, "Hushed. Like a door closing on the noise."),
]
SPAN = '"the whole village wanted a piece … I thought the bees would only be one more thing to do … I felt 100% awake"'
STATEMENT = "The village pulling at her before the bees"


def whole(src: str, head: str) -> str:
    at = src.index(head)
    return src[at:src.index("\n}\n", at) + 3]


def line_of(src: str, start: str) -> str:
    at = src.index(start)
    return src[at:src.index("\n", at) + 1]


def make_book(path: Path) -> None:
    """The invented interview set out as a workbook the app makes, its six columns, every row a passage."""
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = SHEET
    ws.append(wb_mod.HEADER)
    for row, name, seconds, words in TURNS:
        ws.cell(row, 1).value = name
        ws.cell(row, 2).value = dt.time(0, seconds // 60, seconds % 60)
        ws.cell(row, 4).value = words
    ws.cell(11, 3).value = "A door closed on the noise"
    ws.cell(11, 6).value = '"Like a door closing on the noise."'
    wb.save(path)


def test_quote_span(scratch):
    print("\n301. One quote across adjacent passages of the same speaker (quotespan, 30 October 2026): saved and read "
          "back with its key and its range, the interviewer's and another speaker's words and a skipped passage refused, "
          "the range in the table, its PDF, Word and the GETs, turn write with a dry run, and the wash on each passage")
    import cli
    import gets as gets_mod
    import print_pdf
    import server as server_mod
    import themes as themes_mod
    import themes_print
    import themes_word

    root = scratch / "a301-root"
    shutil.rmtree(root, ignore_errors=True)
    book = root / "Wren" / "Wren - EN & ES.xlsx"
    make_book(book)
    (root / "idiograph-project.json").write_text(json.dumps({"name": "Bees, a scratch project",
                                                             "agents": {"allowed": True, "at": "2026-10-30T09:00:00"}}),
                                                 encoding="utf-8")
    config = scratch / "a301-config.json"
    config.write_text(json.dumps({"root": str(root), "interviewer": "Adam", "corpus": "", "gravity_reference": "",
                                  "corpus_exclude": []}), encoding="utf-8")
    key = themes_mod.card_key(SHEET, 3, 0)

    # ── A. the rule, on the sheet's rows as the readers take them
    rows = [{"name": name, "text": words, "row": row} for row, name, _, words in TURNS]
    took = lambda at, quote: sorted({rows[k]["row"] for k, _, _ in wb_mod.quote_turns(rows, at, quote, "Adam")})
    check("301: a quote of three pieces takes in Wren's three adjacent passages, the interviewer's turns between left "
          "out, and from its middle or last passage the same three",
          took(1, SPAN) == [3, 5, 7] and took(3, SPAN) == [3, 5, 7] and took(5, SPAN) == [3, 5, 7],
          str([took(1, SPAN), took(3, SPAN), took(5, SPAN)]))
    pieces = [rows[k]["text"][s:e] for k, s, e in wb_mod.quote_turns(rows, 1, SPAN, "Adam")]
    check("301: each piece is found verbatim where it stands",
          pieces == ["the whole village wanted a piece", "I thought the bees would only be one more thing to do",
                     "I felt 100% awake"], str(pieces))
    check("301: the interviewer's words, Hollis's words, a passage of Wren's skipped and one across Hollis's passage "
          "find nothing, and a quote of one piece never runs on",
          took(1, '"the whole village wanted a piece … And was it"') == []
          and took(5, '"I felt 100% awake … She stayed out there all afternoon"') == []
          and took(1, '"the whole village wanted a piece … I felt 100% awake"') == []
          and took(7, '"I felt 100% awake … Twenty minutes or so"') == []
          and took(1, '"I thought the bees would only be one more thing to do"') == [])

    # ── B. saved as the page saves it, and read back with its key and its range
    made = wb_mod.save_turn(book, SHEET, 3, None, None, None, pairs=[{"es": STATEMENT, "kq": SPAN}])
    case = wb_mod.read_case(book)
    row3 = next(r for s in case["sheets"] for r in s["rows"] if r["row"] == 3)
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = config, str(root), {"recent": []}
        read = themes_mod.read_cards(book)
        card = next(c for c in read["cards"] if c["key"] == key)
        quote = themes_mod.own_quote(read["quotes"], key)
        alone = next(c for c in read["cards"] if c["row"] == 11)
        check("301: the quote is saved whole in its statement's own row, the words alone, and read back with its key",
              made["changed"] and row3["pairs"] == [{"es": STATEMENT, "kq": SPAN}] and card["text"] == STATEMENT
              and quote is not None and quote["text"] == SPAN, json.dumps(row3["pairs"]))
        check("301: the quote and its statement's card carry the range from the first passage to the last, the rows it "
              "takes in and the seconds of both ends, the card its own passage's seconds to play from",
              card["time"] == "00:10–00:52" and card["span"] == [10, 52] and card["rows"] == [3, 5, 7]
              and card["seconds"] == 10 and quote["time"] == card["time"] and quote["rows"] == [3, 5, 7],
              json.dumps(card))
        check("301: a quote inside one passage keeps its one time and nothing more",
              alone["time"] == "01:45" and "span" not in alone and "rows" not in alone, json.dumps(alone))

        def run(*args):
            return cli.run(["--root", str(root), "--config", str(config), *args])

        def spec(name, value):
            path = scratch / f"a301-{name}.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            return str(path)

        # ── C. the range in the table, its PDF, the Word document and the GETs
        code, _, err = run("board", "new", "Wren", "--from", spec("board", {"pets": [{"title": "A crowded spring",
                                                                                       "members": [key]}]}),
                           "--note", "a301")
        page = themes_print.page(book, "Wren")
        check("301: the print view's table gives the statement the range, as the thesis writes it",
              code == 0 and f"{STATEMENT} <span class=\"ref\">(Interview, 00:10–00:52)</span>" in page,
              err.strip()[:300])
        printed = []
        held_typeset, print_pdf.typeset_pdf = support.typeset_words(printed)
        try:
            pdf = print_pdf.write(book, "Wren", replace=True)
        finally:
            print_pdf.typeset_pdf = held_typeset
        check("301: the PDF is typeset from the table with the range in it",
              Path(pdf["path"]).read_bytes().startswith(b"%PDF") and printed
              and support.squashed("(Interview, 00:10–00:52)") in printed[0])
        word = themes_word.write(book, "Wren")
        with zipfile.ZipFile(word["path"]) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        check("301: the Word document gives the statement the range", f"{STATEMENT} (Interview, 00:10–00:52)" in xml)
        snap = gets_mod.snapshot(book)
        line = dict(snap["lines"][key])
        gets_mod.retimed(line, "75:12")
        check("301: the GETs file's line keeps the two ends and is written as the range in the project's timecodes",
              snap["lines"][key].get("span") == [10, 52] and line["time"] == "00:10–00:52",
              json.dumps(snap["lines"][key]))

        # ── D. turn write: a dry run, the write, and the refusals
        before = book.read_bytes()
        wanted = {"pairs": [{"statement": "Bees as one more thing to do",
                             "quote": "I thought the bees would only be one more thing to do … I felt 100% awake"}],
                  "request": "a301 across"}
        code, text, err = run("turn", "write", "Wren", SHEET, "5", "--from", spec("across", wanted), "--dry-run")
        check("301: turn write's dry run takes a quote across her next passage, says its rows and range, and writes "
              "nothing", code == 0 and "would take in rows 5 and 7 of Interview, 00:46–00:52." in text
              and book.read_bytes() == before, (text + err).strip()[:400])
        code, out, _ = run("--json", "turn", "write", "Wren", SHEET, "5", "--from", spec("across", wanted), "--dry-run")
        answer = json.loads(out) if code == 0 else {}
        # the participant's words come back marked as data for an agent (area 274)
        bare = lambda v: v.get("untrusted_text") if isinstance(v, dict) else v
        spans = [dict(s, quote=bare(s.get("quote"))) for s in answer.get("spans") or []]
        check("301: and its answer lists it under spans",
              spans == [{"quote": '"I thought the bees would only be one more thing to do … I felt 100% awake"',
                         "rows": [5, 7], "time": "00:46–00:52"}], json.dumps(answer.get("spans"))[:400])
        code, text, err = run("turn", "write", "Wren", SHEET, "5", "--from", spec("across", wanted))
        case = wb_mod.read_case(book)
        row5 = next(r for s in case["sheets"] for r in s["rows"] if r["row"] == 5)
        check("301: the write takes it, in the passage's own row", code == 0 and "takes in rows 5 and 7" in text
              and row5["pairs"][0]["kq"] == '"I thought the bees would only be one more thing to do … I felt 100% awake"',
              (text + err).strip()[:400])
        before = book.read_bytes()
        bad = {
            "the interviewer's": ("5", "I thought the bees … And was it", "takes words from the interviewer's turn at row 6"),
            "Hollis's": ("7", "I felt 100% awake … She stayed out there all afternoon", "another speaker's passage at row 8"),
            "a skipped passage's": ("3", "the whole village wanted a piece … I felt 100% awake",
                                    "skips the passage at row 5"),
            "across Hollis's passage": ("9", "I felt 100% awake … Twenty minutes or so",
                                        "takes words from row 7, which is not next to this passage"),
        }
        for what, (at, said, line_said) in bad.items():
            code, _, err = run("turn", "write", "Wren", SHEET, at, "--from",
                               spec("bad", {"pairs": [{"statement": "Refused", "quote": said}], "request": "a301 bad"}))
            check(f"301: turn write refuses a quote taking {what} words with its line, nothing written",
                  code == 1 and line_said in err and "Nothing was written." in err and book.read_bytes() == before,
                  err.strip()[:400])
        code, text, _ = run("turn", "show", "Wren", SHEET, "3")
        check("301: turn show gives such a quote its rows and range",
              code == 0 and f"Quote: {SPAN}  (rows 3, 5 and 7, 00:10–00:52)" in text, text[:600])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    # ── E. the page, in node: the wash on each passage, the quote built across two, the refusals
    if not shutil.which("node"):
        skip("301: the page's marks and pieces in node", "no node on this machine")
        return
    app = support.text("apps/idiograph/static/distil.js")
    parts = [whole(app, f"function {name}(") for name in (
        "rowPairs", "livePairs", "quoteRun", "quoteTurns", "kqLayer", "kqFarKeys", "kqTitle", "kqFarTitle", "markedHtml",
        "piecesIn", "pendingRows", "besideRefusal")]
    consts = [line_of(app, start) for start in ("const KQ_NEAR", "const speakerKey", "const rowText", "const pendingQuote")]
    harness = support.i18n_js() + support.text("family/static/quote.js") + r"""
const esc = (s) => String(s);
const escAttr = (s) => String(s);
const DATA = __DATA__;
const S = { flat: [], stops: [], at: 0, pairsRow: null, pending: [] };
for (const sheet of DATA.sheets) for (const row of sheet.rows) S.flat.push(row);
S.flat.forEach((row, i) => { row.i = i; row.key = `${row.sheet}:${row.row}`; });
for (const row of S.flat) {
  row.stop = !!(row.name && row.name.trim().toLowerCase() !== 'adam');
  row.other = !!row.context;
  if (row.stop) { row.pos = S.stops.length; S.stops.push(row.i); }
}
const current = () => S.flat[S.stops[S.at]];
const pairsNow = () => [];
const at = (n) => S.flat.find((r) => r.row === n);
""" + "".join(consts) + "\n".join(parts) + r"""
const wash = (n) => kqLayer(at(n)).map((s) => ({ words: rowText(at(n)).slice(s.start, s.end), kq: s.kq, from: s.from === undefined ? null : S.flat[s.from].row }));
const marked = markedHtml(at(5).runs, kqLayer(at(5)));
// the quote being built on row 3, a piece there and one taken in row 5
const piece = (n, words) => { const s = rowText(at(n)).indexOf(words); return { key: at(n).key, start: s, end: s + words.length }; };
S.at = S.stops.indexOf(at(3).i);
S.pending = [piece(3, 'the whole village wanted a piece')];
const ok5 = besideRefusal(at(3), at(5));
const no7 = besideRefusal(at(3), at(7));
const no4 = besideRefusal(at(3), at(4));
const no8 = besideRefusal(at(3), at(8));
S.pending.push(piece(5, 'I thought the bees would only be one more thing to do'));
const ok7 = besideRefusal(at(3), at(7));
S.pending.push(piece(7, 'I felt 100% awake'));
console.log(JSON.stringify({ w3: wash(3), w5: wash(5), w7: wash(7), w9: wash(9), marked, quote: pendingQuote(),
  ok5, no7, no4, no8, ok7,
  reach: quoteReach(DATA.span, [3, 5, 7].map((n) => rowText(at(n))), 0) }));
"""
    data = dict(wb_mod.read_case(book), span=SPAN)
    ran = support.run_node(harness.replace("__DATA__", json.dumps(data)), scratch, "a301-page.js")
    if ran.returncode != 0:
        check("301: the page's pieces run in node", False, ran.stderr.strip()[:600])
        return
    got = json.loads(ran.stdout)
    # row 5's own quote, written above, runs on into row 7 too
    check("301: the wash lies on each passage the quote draws from, on its own passage as its statement's and on the "
          "next two as the statement of row 3's, beside row 5's own quote, which runs on into row 7",
          got["w3"] == [{"words": "the whole village wanted a piece", "kq": 0, "from": None}]
          and got["w5"] == [{"words": "I thought the bees would only be one more thing to do", "kq": 0, "from": 3},
                            {"words": "I thought the bees would only be one more thing to do", "kq": 0, "from": None}]
          and got["w7"] == [{"words": "I felt 100% awake", "kq": 0, "from": 3}, {"words": "I felt 100% awake", "kq": 0, "from": 5}],
          json.dumps({k: got[k] for k in ("w3", "w5", "w7")}))
    check("301: a piece of another passage's quote names that passage and place, in its statement's colour",
          'data-kq-far="' in got["marked"] and 'data-es-colour="0"' in got["marked"] and got["w9"] == [],
          got["marked"][:400])
    check("301: the quote built across three passages takes them in order, an ellipsis at every gap, the "
          "interviewer's words never in it",
          got["quote"] == SPAN, got["quote"])
    check("301: a piece in the next passage is taken, one in the interviewer's turn, in Hollis's passage or past the "
          "next is refused with its line, and one past the next is taken once the next holds a piece",
          got["ok5"] == "" and got["ok7"] == "" and got["no7"] == "A quote can take in only the passage just before or "
          "just after, with nothing but the interviewer between."
          and got["no4"] == "A quote holds the participant's words, never the interviewer's."
          and got["no8"] == "A quote holds one speaker's words, and these are another speaker's.",
          json.dumps({k: got[k] for k in ("ok5", "ok7", "no7", "no4", "no8")}))
    check("301: the page's rule finds the same pieces as the workbook's",
          [(p["turn"], p["start"], p["end"]) for p in got["reach"]]
          == [(t, s, e) for t, s, e in wb_mod.quote_reach(SPAN, [TURNS[i][3] for i in (1, 3, 5)], 0)], json.dumps(got["reach"]))
