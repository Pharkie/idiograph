from __future__ import annotations

import io
import zipfile
from xml.sax.saxutils import escape

import openpyxl

import workbook as wb_mod

from .support import check
import idiograph_routes

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _para(text: str) -> str:
    return f'<w:p><w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'


def _cell(lines) -> str:
    lines = [lines] if isinstance(lines, str) else list(lines)
    return "<w:tc>" + "".join(_para(ln) for ln in (lines or [""])) + "</w:tc>"


def _table(rows) -> str:
    return "<w:tbl>" + "".join("<w:tr>" + "".join(_cell(c) for c in row) + "</w:tr>" for row in rows) + "</w:tbl>"


def _docx(body: str) -> bytes:
    document = (f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{W}"><w:body>{body}'
                '<w:sectPr/></w:body></w:document>')
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types '
                   'xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr("word/document.xml", document)
    return out.getvalue()


# an invented interview on keeping bees, a new row at each change of speaker, the notes beside the
# words they are about, a dot holding a note's level as a Word table often has one
WORDS = [
    "Sam: [00:00:04] How did the first hive settle?",
    ["Wren: [00:00:09] Slowly. The bees were cross for days.", "I wore the veil even to water the plants."],
    "00:01:10 And then one morning they were calm.",
    "Sam: Why then, do you think?",
    "Wren: I think I had stopped hovering over them.",
]
NOTES = [
    [],
    ["cross: anger lent to the bees", ".", "veil as armour, even for small tasks"],
    ["calm arrives, it is not made"],
    ["asks for a reason"],
    ["self as the disturbance?", "hovering, over-attending"],
]
TURNS = [("Sam", 4, "How did the first hive settle?"),
         ("Wren", 9, "Slowly. The bees were cross for days. I wore the veil even to water the plants."),
         ("Wren", 70, "And then one morning they were calm."),
         ("Sam", None, "Why then, do you think?"),
         ("Wren", None, "I think I had stopped hovering over them.")]
EN = ["", "cross: anger lent to the bees\nveil as armour, even for small tasks", "calm arrives, it is not made",
      "asks for a reason", "self as the disturbance?\nhovering, over-attending"]
STATEMENTS = [[], ["Feeling the hive's mood as her own"], [], [], ["Seeing herself as what unsettled them", "Stepping back"]]
ES = ["", "Feeling the hive's mood as her own", "", "", "Seeing herself as what unsettled them\nStepping back"]


def test_word_table_notes(scratch):
    print("\n204. A Word table of transcript and exploratory notes comes in whole: a row a passage, the notes "
          "beside it as its exploratory notes, statements by a heading, the columns found by heading or by content, and every column of a Word table, "
          "an Excel file or a CSV matched to a role on the card, his to change")
    import convert
    import server as server_mod

    T = lambda turns: [tuple(t) for t in turns]
    read = lambda body, name="hive.docx": convert.read_data(name, _docx(body))
    en_of = lambda r: [n["en"] for n in r["notes"]]
    es_of = lambda r: [n["es"] for n in r["notes"]]

    # ── A. two columns, transcript then notes, with a heading row and without
    for label, head in (("with", [["Transcript", "Exploratory notes"]]), ("without", [])):
        got = read(_table(head + [[w, n] for w, n in zip(WORDS, NOTES)]))
        check(f"204: a two-column table {label} a heading is a row a passage, a Name: and a time at a row's head "
              "taken, a row with no name carrying on the speaker before it",
              T(got["turns"]) == TURNS, str(got["turns"]))
        check(f"204: {label} a heading each passage carries its row's notes, a cell's lines kept, a dot passed over",
              en_of(got) == EN and got["left"] == [], str(got.get("notes")) + str(got.get("left")))
        check(f"204: the import card's line says what the table brings, {label} a heading",
              bool(idiograph_routes.turns_view(got, "")["brings"]))

    # ── B. the notes left of the transcript, no heading: the transcript is found by what it holds
    got = read(_table([[n, w] for w, n in zip(WORDS, NOTES)]))
    check("204: notes left of the transcript come in the same, the transcript found by its speakers' names",
          T(got["turns"]) == TURNS and en_of(got) == EN, str(got["turns"]))
    plain = [[ln.split(": ", 1)[-1].split("] ", 1)[-1] for ln in ([w] if isinstance(w, str) else w)] for w in WORDS]
    plain = [[p.replace("00:01:10 ", "") for p in w] for w in plain]
    long_notes = [n or ["short"] for n in NOTES]
    got = read(_table([[n, w] for w, n in zip(plain, long_notes)]))
    check("204: with no names at all the transcript is the column whose lines run longest, every passage Speaker",
          [t[2] for t in got["turns"]] == [t[2] for t in TURNS] and {t[0] for t in got["turns"]} == {convert.SPEAKER},
          str(got["turns"]))

    # ── C. three columns: statements by a heading, a third column left out without one
    rows = [[s, w, n] for s, w, n in zip(STATEMENTS, WORDS, NOTES)]
    got = read(_table([["Experiential statements", "Transcript", "Exploratory notes"]] + rows))
    check("204: a third column headed as experiential statements comes in as statements, the notes as notes",
          T(got["turns"]) == TURNS and en_of(got) == EN and es_of(got) == ES and got["left"] == [],
          str(got.get("notes")) + str(got.get("left")))
    got = read(_table(rows))
    check("204: with no heading the third column is left out, the notes taken from the fullest of the other two, "
          "and the card's line names the column left out",
          T(got["turns"]) == TURNS and en_of(got) == EN and not any(es_of(got)) and len(got["left"]) == 1,
          str(got.get("left")))
    got = read(_table([["Transcript", "Notes", "Codes"]] + [[w, n, ["a code"]] for w, n in zip(WORDS, NOTES)]))
    check("204: a third column whose heading names neither is left out, and said",
          en_of(got) == EN and not any(es_of(got)) and len(got["left"]) == 1 and "Codes" in got["left"][0],
          str(got.get("left")))

    # ── D. a row of notes with no words adds them to the passage before it, never a passage of its own
    got = read(_table([[w, n] for w, n in zip(WORDS, NOTES)] + [[[], ["a late thought on hovering"]]]))
    check("204: a row with notes and no words adds its notes to the passage before it",
          len(got["turns"]) == 5 and got["notes"][-1]["en"] == EN[-1] + "\na late thought on hovering", str(got["notes"]))

    # ── E. a Word file with no table, or with a small table among its paragraphs, is read as before
    paragraphs = "".join(_para(w if isinstance(w, str) else " ".join(w)) for w in WORDS)
    as_text = "\n".join(w if isinstance(w, str) else " ".join(w) for w in WORDS)
    for label, body, text in (("no table", paragraphs, as_text),
                              ("a small table", _table([["Date", "Place"], ["Spring", "Garden"]]) + paragraphs,
                               "Date\nPlace\nSpring\nGarden\n" + as_text)):
        got = read(body)
        check(f"204: a Word file with {label} is read a paragraph a line, as plain text is",
              T(got["turns"]) == T(convert.read_plain(text)) and not got.get("notes") and not convert.brings(got),
              str(got["turns"]))

    # ── F. what is written: the raw source carries the notes, stays raw, and the annotated workbook made
    # from it holds them where the statements screen writes them, the interviewer's in Interviewer notes
    got = read(_table([["Experiential statements", "Transcript", "Exploratory notes"]] + rows))
    raw = scratch / "a204" / "Source" / "P1 Wren - transcript.xlsx"
    raw.parent.mkdir(parents=True)
    convert.write_sheets([("Interview", got["turns"], got["notes"], "Sam")], raw)
    src = openpyxl.load_workbook(raw)
    cols = wb_mod.detect_columns(src.active)
    src.close()
    check("204: the raw source made from a Word table is still a raw source", wb_mod.is_raw_source(cols), str(cols))
    book = wb_mod.create_from_source(raw, scratch / "a204" / "P1 Wren.xlsx")
    case = wb_mod.read_case(book)
    rows_read = case["sheets"][0]["rows"]
    check("204: the annotated workbook holds each participant passage's notes and statements, a line an entry",
          [r["en"] for r in rows_read] == ["", EN[1], EN[2], "", EN[4]]
          and [r["es"] for r in rows_read] == ES, str([(r["en"], r["es"]) for r in rows_read]))
    check("204: the interviewer's notes go to his Interviewer notes, as the statements screen keeps them",
          [r["note"] for r in rows_read] == ["", "", "", EN[3], ""], str([r["note"] for r in rows_read]))
    loaded = openpyxl.load_workbook(book)
    ws = loaded.active
    check("204: an entry per line, a blank line between, as a typed note is saved",
          ws.cell(3, 5).value == EN[1].replace("\n", "\n\n") and ws.cell(1, 7).value == wb_mod.NOTE_HEADER,
          repr(ws.cell(3, 5).value))
    loaded.close()

    # a further interview added to the case takes the same path
    convert.add_sheets([("Follow-up", got["turns"], got["notes"], "")], raw)
    wb_mod.add_from_source(raw, ["Follow-up"], book)
    later = wb_mod.read_case(book)["sheets"][1]["rows"]
    check("204: Add transcripts takes a Word table's notes the same, every row's in Exploratory notes with no "
          "interviewer chosen", [r["en"] for r in later] == EN and [r["note"] for r in later] == [""] * 5,
          str([r["en"] for r in later]))

    # New project and Add transcripts write a case's sheet through one helper, the notes and the
    # interviewer's name from Settings when he was chosen
    kept = server_mod.config
    try:
        server_mod.config = lambda: {"interviewer": "Sam"}
        sheet = idiograph_routes.case_sheet({"interview": "Interview", "read": got, "interviewer": "Sam"}, "Sam", "Wren")
        none = idiograph_routes.case_sheet({"interview": "Interview", "read": got, "interviewer": ""}, "Sam", "Wren")
    finally:
        server_mod.config = kept
    check("204: a case's sheet carries the notes and the interviewer's Settings name only when he was chosen",
          sheet[2] == got["notes"] and sheet[3] == "Sam" and none[3] == "" and sheet[1][0][0] == "Sam"
          and sheet[1][1][0] == "Wren", str(sheet[1][:2]))

    # ── G. column matching (19 October, Adam: "let them check that it's correctly detected the
    # columns"): every column of a Word table, an Excel file or a CSV given a role, guessed by its
    # heading or by what it holds, his to change, a change reading the file again
    import base64
    from workbook import WorkbookError

    times = ["00:00:04", "00:00:09", "00:01:10", "00:01:31", "00:01:40"]
    who = ["Sam", "Wren", "Wren", "Sam", "Wren"]
    said = [w if isinstance(w, str) else " ".join(w) for w in WORDS]
    said = [s.split(": ", 1)[-1].split("] ", 1)[-1].replace("00:01:10 ", "") for s in said]
    four = [[w, t, s, n] for w, t, s, n in zip(who, times, said, NOTES)]
    timed = [(w, convert.seconds_of(t), s) for w, t, s in zip(who, times, said)]
    for label, head in (("with", [["Speaker", "Time", "Transcript", "Notes"]]), ("without", [])):
        got = read(_table(head + four))
        check(f"204: a four-column Word table {label} headings has its Speaker and Time columns matched, never left out",
              got["roles"] == ["name", "ts", "text", "en"] and T(got["turns"]) == timed and en_of(got) == EN
              and got["left"] == [] and got["said"] is None, str(got.get("roles")) + str(got["turns"][:2]))
    got = read(_table([[n, w] for w, n in zip(WORDS, NOTES)]))
    check("204: notes left of the transcript are guessed as Exploratory notes, the transcript as Transcript",
          got["roles"] == ["en", "text"] and got["headers"] == ["Column 1", "Column 2"], str(got.get("roles")))

    # an Excel file and a CSV with notes and statements columns, guessed by their headings
    book = openpyxl.Workbook()
    ws = book.active
    ws.append(["Speaker", "Time", "Transcript", "Exploratory notes", "Experiential statements", "Coder"])
    for w, t, s, en, es in zip(who, times, said, EN, ES):
        ws.append([w, t, s, en or None, es or None, "AB"])
    xlsx_bytes = io.BytesIO()
    book.save(xlsx_bytes)
    book.close()
    xlsx_bytes = xlsx_bytes.getvalue()
    got = convert.read_data("hive.xlsx", xlsx_bytes)
    check("204: an Excel file's notes and statements columns are guessed by their headings, a column no role "
          "takes said to be left out",
          got["roles"] == ["name", "ts", "text", "en", "es", ""] and T(got["turns"]) == timed and en_of(got) == EN
          and es_of(got) == ES and got["left"] == ["The column headed Coder is left out."], str(got.get("roles")) + str(got["left"]))
    rows_csv = ["Name,Timestamp,Text,Comments,Statements"] + [
        f'{w},{t},"{s}","{en}","{es}"' for w, t, s, en, es in zip(who, times, said, EN, ES)]
    got = convert.read_data("hive.csv", "\n".join(rows_csv).encode("utf-8"))
    check("204: a CSV's Comments and Statements columns come in as notes and statements, their lines kept",
          got["roles"] == ["name", "ts", "text", "en", "es"] and en_of(got) == EN and es_of(got) == ES,
          str(got.get("roles")) + str(got.get("notes"))[:200])

    # a changed choice reads the file again and lands each column where it was chosen
    swapped = convert.read_data("hive.xlsx", xlsx_bytes, ["name", "ts", "text", "es", "en", "en"])
    check("204: two columns on one role are refused in one line, read by the first meanwhile",
          swapped["said"] == "Two columns are set to Exploratory notes. Choose one." and es_of(swapped) == EN,
          str(swapped["said"]))
    swapped = convert.read_data("hive.xlsx", xlsx_bytes, ["name", "ts", "text", "es", "en", ""])
    check("204: a changed choice is read as given, the notes column as statements and the statements as notes",
          swapped["said"] is None and en_of(swapped) == ES and es_of(swapped) == EN
          and swapped["roles"] == ["name", "ts", "text", "es", "en", ""], str(swapped.get("roles")))
    got = read(_table([["Speaker", "Time", "Transcript", "Notes"]] + four))
    left = convert.read_data("hive.docx", _docx(_table([["Speaker", "Time", "Transcript", "Notes"]] + four)), ["name", "", "text", ""])
    check("204: in a Word table a column set to Leave out brings nothing and is said to be left out",
          [t[1] for t in left["turns"]] == [None] * 5 and not any(en_of(left))
          and left["left"] == ["The column headed Time is left out.", "The column headed Notes is left out."], str(left["left"]))
    none = convert.read_data("hive.docx", _docx(_table([["Speaker", "Time", "Transcript", "Notes"]] + four)), ["name", "ts", "", "en"])
    check("204: with no column set to Transcript nothing is read and the card says to choose one",
          none["turns"] == [] and none["said"] == convert.NO_TRANSCRIPT and none["headers"] == ["Speaker", "Time", "Transcript", "Notes"])

    root = scratch / "a204-cols"
    source = root / "P3 - Wren" / "Source"
    source.mkdir(parents=True)
    (source / "hive.xlsx").write_bytes(xlsx_bytes)
    (source / "hive table.docx").write_bytes(_docx(_table([["Speaker", "Time", "Transcript", "Notes"]] + four)))
    kept = (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY, server_mod.CONFIG_PATH)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_PATH = scratch / "a204-state.json"
    server_mod.STATE_MEMORY = {"recent": []}
    server_mod.CONFIG_PATH = scratch / "a204-config.json"
    server_mod.save_json(server_mod.CONFIG_PATH, dict(server_mod.defaults(), interviewer="Sam"))
    try:
        seen = idiograph_routes.api_import({"path": str(source / "hive table.docx"), "op": "read"})
        check("204: the card's read of a Word table answers its columns, the role of each, and the preview's columns "
              "with the notes beside their words",
              seen["columns"] == ["Speaker", "Time", "Transcript", "Notes"] and seen["roles"] == ["name", "ts", "text", "en"]
              and seen["shown"] == ["name", "ts", "text", "en"] and [t["en"] for t in seen["turns"]] == EN, str(seen)[:300])
        twice = idiograph_routes.api_import({"path": str(source / "hive.xlsx"), "op": "read", "columns": ["name", "ts", "text", "text", "es", ""]})
        try:
            idiograph_routes.api_import({"path": str(source / "hive.xlsx"), "op": "make", "columns": ["name", "ts", "text", "text", "es", ""],
                                   "interviewer": "Sam"})
            refused = None
        except WorkbookError as exc:
            refused = str(exc)
        check("204: Make refuses two columns on one role, the card's line, and writes nothing",
              twice["said"] == "Two columns are set to Transcript. Choose one." and refused == twice["said"]
              and not (source / f"hive{convert.CONVERTED}.xlsx").exists(), str(refused))
        made = idiograph_routes.api_import({"path": str(source / "hive.xlsx"), "op": "make", "interviewer": "Sam",
                                      "columns": ["name", "ts", "text", "es", "en", ""]})
        raw = source / f"hive{convert.CONVERTED}.xlsx"
        check("204: Make answers the raw source it wrote", made["source"]["name"] == raw.stem and raw.exists(), str(made))
        book = wb_mod.create_from_source(raw, scratch / "a204-cols" / "P3 Wren.xlsx")
        rows_read = wb_mod.read_case(book)["sheets"][0]["rows"]
        check("204: Make lands each column where it was chosen, the statements column as notes and the notes as "
              "statements, the interviewer's notes in his own place",
              [r["en"] for r in rows_read] == [ES[i] if who[i] == "Wren" else "" for i in range(5)]
              and [r["es"] for r in rows_read] == EN
              and [r["note"] for r in rows_read] == [ES[i] if who[i] == "Sam" else "" for i in range(5)],
              str([(r["en"], r["es"], r["note"]) for r in rows_read]))
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY, server_mod.CONFIG_PATH = kept

    # New project and Add transcripts take the same choice, and refuse the same
    entry = {"name": "hive.xlsx", "data": base64.b64encode(xlsx_bytes).decode(), "pseudonym": "Wren",
             "interview": "Interview", "columns": ["name", "ts", "text", "en", "en", ""]}
    try:
        idiograph_routes.new_cases(scratch / "a204-np", {"files": [entry]}, "Sam")
        refused = None
    except WorkbookError as exc:
        refused = str(exc)
    check("204: New project refuses a file with two columns on one role, naming the file",
          refused == "hive.xlsx: Two columns are set to Exploratory notes. Choose one.", str(refused))
    two = read(_table([["Transcript", "Exploratory notes"]] + [[w, n] for w, n in zip(WORDS, NOTES)]))
    check("204: a two-column table's preview shows the speakers and times its rows name, beside the words and notes",
          idiograph_routes.turns_view(two, "")["shown"] == ["name", "ts", "text", "en"], str(idiograph_routes.turns_view(two, "")["shown"]))
    check("204: the preview cuts a long passage at a whole word, never mid-word",
          idiograph_routes.preview_words("word " * 100).endswith("word…") and len(idiograph_routes.preview_words("word " * 100)) <= 241)
