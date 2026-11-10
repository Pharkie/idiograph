from __future__ import annotations

import json
import shutil

import openpyxl

import rounds as rounds_mod
import workbook as wb_mod
from workbook import WorkbookError

from . import support
from .support import check, line_of_js, skip, slashed
import idiograph_routes


def test_transcript_import(scratch):
    print("\n72. Transcript import: VTT, SRT, plain text, CSV and Excel read into turns, the card, the raw source "
          "made beside the file, and the template")
    import datetime as dt
    import subprocess
    import convert
    import make_template
    import server as server_mod

    T = lambda turns: [tuple(t) for t in turns]

    # ── A. the readers, each on invented text
    teams = convert.read_vtt(IMPORT_TEAMS)
    check("72: a Teams VTT names its speakers by <v Name>, one speaker's cues in a row become one turn at the first cue",
          T(teams) == [("Sam Okafor", 1, "So how did the first week with the dog go?"),
                       ("Juno Example", 4, "Slower than I thought. She slept a lot. And I kept checking on her & listening."),
                       ("Sam Okafor", 62, "What did checking look like?")], str(teams))
    zoom = convert.read_vtt(IMPORT_ZOOM)
    check("72: a Zoom VTT names them by a leading Name:, a line of reported speech stays in its turn, and an hour counts",
          T(zoom) == [("Sam Okafor", 1, "So how did the first week go?"),
                      ("Juno", 5, "Slower than I thought. She slept a lot. And I said: let her be."),
                      ("Sam Okafor", 3723, "Why was that?")], str(zoom))
    srt = convert.read_srt(IMPORT_SRT)
    check("72: an SRT reads the same, its comma before the milliseconds, its tags dropped",
          T(srt) == [("Sam", 1, "Morning walks first?"), ("Juno", 5, "Always. Rain or not."), ("Sam", 8, "Even in snow?")],
          str(srt))
    bare = convert.read_vtt(IMPORT_BARE)
    check("72: a subtitle file that names nobody keeps every cue as a row of its own under Speaker",
          T(bare) == [("Speaker", 1, "The dog barked."), ("Speaker", 3, "Then it was quiet.")], str(bare))
    cues = convert.read_cues(IMPORT_TEAMS)
    check("72: the cue identifiers, the settings, the NOTE block and the end times are passed over",
          [c[1] for c in cues] == [1, 4, 9, 62] and not any("align" in c[2] or "-->" in c[2] or "note" in c[2] for c in cues))
    plain = convert.read_plain(IMPORT_PLAIN)
    check("72: plain text starts a turn at a label, carries it on line by line, and takes [00:00:05], 00:01:02 and 1:10 as times",
          T(plain) == [("Speaker", None, "Interview with Juno Recorded at home"), ("Sam", 5, "How was the first week?"),
                       ("Juno", 9, "Slower than I thought. She slept a lot. And I said: let her be."),
                       ("Sam", 62, "Why?"), ("Juno", 70, "Because she was tired.")], str(plain))
    untimed = convert.read_plain(IMPORT_PLAIN_UNTIMED)
    check("72: plain text with no times is allowed, every turn's time None",
          T(untimed) == [("Sam", None, "How was the first week?"), ("Juno", None, "Slower than I thought."),
                         ("Sam", None, "Why so?"), ("Juno", None, "She slept, mostly.")], str(untimed))
    check("72: plain text also reads a name with a time on its own line, as Word and Otter save it, and Name (time):",
          T(convert.read_plain(IMPORT_OTTER)) == [("Speaker 1", 3, "How was the first week?"),
                                                  ("Speaker 2", 9, "Slower than I thought."), ("Speaker 1", 62, "Why?")]
          and T(convert.read_plain(IMPORT_REV)) == [("Sam Okafor", 3, "How was the first week?"),
                                                    ("Juno", 9, "Slower than I thought.")])
    check("72: plain text with no label is a turn a paragraph under Speaker, with the time at its head",
          T(convert.read_plain("[00:00:03] First words.\n\n[00:00:09] Second words.")) == [
              ("Speaker", 3, "First words."), ("Speaker", 9, "Second words.")]
          and T(convert.read_plain("One line.\nAnother line.")) == [("Speaker", None, "One line."), ("Speaker", None, "Another line.")])
    check("72: a .txt that holds a VTT or an SRT is read as one",
          T(convert.read_plain(IMPORT_ZOOM)) == T(zoom) and T(convert.read_plain(IMPORT_SRT)) == T(srt))
    check("72: a label is a name of capitalised words, and a field of a document's head is not one",
          convert.label_of("Dr. Ana de Souza: hello") == ("Dr. Ana de Souza", None, "hello")
          and convert.label_of("And then she said: no") is None and convert.label_of("Date: 3 May") is None
          and convert.label_of("http://example.org") is None)
    check("72: times as Excel times, HH:MM:SS, MM:SS and seconds",
          [convert.seconds_of(v) for v in (dt.time(0, 1, 23), dt.datetime(1899, 12, 30, 1, 0, 5), dt.timedelta(seconds=90),
                                           "00:01:23", "01:23", "75:10", "83", 83.6, "[00:00:07.250]", "soon", None, "")]
          == [83, 3605, 90, 83, 83, 4510, 83, 83, 7, None, None, None])

    # ── B. tables: the CSV, the Excel file, the columns guessed and changed
    # the three roles these checks are about, the notes and statements columns are area 204's
    three = lambda m: {k: m.get(k) for k in ("name", "ts", "text")}
    root = scratch / "import-root"
    case = root / "P7 - Juno"
    source = case / "Source"
    source.mkdir(parents=True, exist_ok=True)
    csv_file = source / "walks.csv"
    csv_file.write_text(IMPORT_CSV, encoding="utf-8")
    read = convert.read_file(csv_file)
    check("72: a CSV with other headers and semicolons is read, Speaker, Start and Utterance taken, End time left",
          read["headers"] == ["Speaker", "Start", "End time", "Utterance"] and three(read["mapping"]) == {"name": 0, "ts": 1, "text": 3},
          str(read["mapping"]))
    check("72: its rows: the name carried down, seconds and MM:SS, a delimiter in the words kept, a leading = kept as text",
          T(read["turns"]) == [("Sam", 3, "How was the first week?"), ("Juno", 9, "Slower than I thought; she slept."),
                               ("Juno", 14, "And then more."), ("Sam", 62, "=Why?")], str(read["turns"]))
    xlsx = source / "walks two.xlsx"
    book = openpyxl.Workbook()
    ws = book.active
    ws.append(["Who", "When", "What was said"])
    ws.append(["Sam", dt.time(0, 0, 3), "How was the first week?"])
    ws.append(["Juno", dt.time(0, 0, 9), "Slower than I thought."])
    ws.append(["Sam", 62, "Why?"])
    book.save(xlsx)
    book.close()
    read_x = convert.read_file(xlsx)
    check("72: an Excel file with other headers is read, the time column found by what it holds",
          three(read_x["mapping"]) == {"name": 0, "ts": 1, "text": 2}
          and T(read_x["turns"]) == [("Sam", 3, "How was the first week?"), ("Juno", 9, "Slower than I thought."), ("Sam", 62, "Why?")],
          str(read_x))
    changed = convert.read_file(xlsx, {"name": "", "ts": 1, "text": 2})
    check("72: a mapping changed in the card is read as given, no Name column making every turn Speaker",
          three(changed["mapping"]) == {"name": None, "ts": 1, "text": 2} and {t[0] for t in changed["turns"]} == {"Speaker"})
    check("72: the column guess takes exact headings first, never an end time, and falls back on what the columns hold",
          three(convert.guess_columns(["Name", "Timestamp", "Transcript"], [["Sam", "00:01", "Hello there"]])) == {"name": 0, "ts": 1, "text": 2}
          and three(convert.guess_columns(["End time", "Start time", "Text", "Speaker"], [["1", "0", "Hi", "Sam"]])) == {"name": 3, "ts": 1, "text": 2}
          and three(convert.guess_columns(["Column 1", "Column 2", "Column 3"],
                                    [["Sam", "0:03", "How did the first week go, then?"], ["Juno", "0:09", "Slower than I thought it might be."]]))
          == {"name": 0, "ts": 1, "text": 2})
    check("72: a first row of data is not taken for headings",
          convert.is_header(["Name", "Time", "Text"]) and not convert.is_header(["Sam", "00:00:03", "Hello"])
          and convert.table_of_csv("Sam,00:00:03,Hello\nJuno,00:00:05,Hi\n")[0] == ["Column 1", "Column 2", "Column 3"])

    # ── C. speakers and the interviewer
    check("72: the speakers in the order they speak, with their turns",
          convert.speakers(zoom) == [{"name": "Sam Okafor", "turns": 2, "questions": 2}, {"name": "Juno", "turns": 1, "questions": 0}])
    check("72: the interviewer is Settings' name when a speaker carries it whole or by the first word, else the most questions",
          convert.guess_interviewer(zoom, "Juno") == "Juno" and convert.guess_interviewer(zoom, "Sam") == "Sam Okafor"
          and convert.guess_interviewer(zoom, "Adam") == "Sam Okafor" and convert.guess_interviewer(zoom, "") == "Sam Okafor")
    check("72: and nobody when one speaker is named or nobody asks",
          convert.guess_interviewer(bare, "Adam") is None
          and convert.guess_interviewer([("A", None, "Yes."), ("B", None, "No.")], "Adam") is None)
    check("72: the interviewer's turns go under Settings' name, unless a speaker already carries it",
          convert.written_as(zoom, "Adam") == {"Sam Okafor": "Adam", "Juno": "Adam"}
          and [t[0] for t in convert.as_interviewer(zoom, "Sam Okafor", "Adam")] == ["Adam", "Juno", "Adam"]
          and convert.written_as([("Adam", None, "Hi?"), ("Sam", None, "Hello")], "Adam") == {"Adam": None, "Sam": None}
          and convert.as_interviewer(zoom, "", "Adam") == list(zoom))

    # ── D. encodings, and the file the readers cannot make sense of
    enc = source / "encodings"
    enc.mkdir(exist_ok=True)
    words = "Sam: Café first?\nJuno: Naïve, maybe.\n"
    (enc / "bom.txt").write_bytes(b"\xef\xbb\xbf" + words.encode("utf-8"))
    (enc / "plain.txt").write_bytes(words.encode("utf-8"))
    (enc / "western.txt").write_bytes(words.encode("cp1252"))
    (enc / "wide.txt").write_bytes(words.encode("utf-16"))
    got = {p.name: T(convert.read_file(p)["turns"]) for p in sorted(enc.iterdir())}
    want = [("Sam", None, "Café first?"), ("Juno", None, "Naïve, maybe.")]
    check("72: UTF-8 with and without a byte order mark, Windows-1252 and UTF-16 read alike",
          all(v == want for v in got.values()) and len(got) == 4, str(got))
    shutil.rmtree(enc)
    lines = []
    for name, data in (("noise.txt", b"PK\x03\x04\x00\x00binary"), ("empty.vtt", b"WEBVTT\n\n"), ("blank.csv", b"\n\n")):
        (scratch / name).write_bytes(data)
        try:
            convert.read_file(scratch / name)
            lines.append(None)
        except convert.Unreadable as exc:
            lines.append(str(exc))
    check("72: a file the readers cannot make sense of gives one plain line",
          lines == [f"Idiograph could not read any passages from {n}." for n in ("noise.txt", "empty.vtt", "blank.csv")], str(lines))

    # ── E. the listing: offered, and not offered again
    (source / "interview.vtt").write_text(IMPORT_ZOOM, encoding="utf-8")
    (source / "notes.txt").write_text(IMPORT_PLAIN_UNTIMED, encoding="utf-8")
    raw = make_template.build(source / "typed.xlsx")
    (source / "done.srt").write_text(IMPORT_SRT, encoding="utf-8")
    shutil.copy2(raw, source / "done.xlsx")
    shutil.copy2(xlsx, source / f"other{convert.CONVERTED}.xlsx")
    for name in ("~$walks.csv", ".hidden.txt", "letter.docx", f"walks (pre-trim).csv"):
        (source / name).write_text("Sam: hello", encoding="utf-8")
    (source / "Initial" / "Source").mkdir(parents=True, exist_ok=True)
    (source / "Initial" / "Source" / "deep.txt").write_text(IMPORT_PLAIN, encoding="utf-8")
    (case / "loose.txt").write_text(IMPORT_PLAIN, encoding="utf-8")
    kept = (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY, server_mod.CONFIG_PATH)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_PATH = scratch / "import-state.json"
    server_mod.STATE_MEMORY = {"recent": []}
    server_mod.CONFIG_PATH = scratch / "import-config.json"
    server_mod.save_json(server_mod.CONFIG_PATH, dict(server_mod.defaults(), interviewer="Adam"))
    try:
        listed = {c["name"]: c for c in idiograph_routes.api_cases({})["cases"]}
        offered = sorted(n for n, c in listed.items() if c["kind"] == "transcript")
        check("72, 102: the case list offers each transcript for this participant's Source, an Excel file with no three columns "
              "and a Word file among them",
              offered == ["interview.vtt", "letter.docx", "notes.txt", "walks two.xlsx", "walks.csv"], str(sorted(listed)))
        check("72: and leaves out a file whose workbook is beside it, the app's own, a backup, a lock, a hidden file, "
              "anything deeper and anything outside Source",
              not any(n in listed for n in ("done.srt", f"other{convert.CONVERTED}", "~$walks.csv", ".hidden.txt",
                                            "walks (pre-trim).csv", "deep.txt", "loose.txt"))
              and listed["typed"]["kind"] == "raw" and listed["done"]["kind"] == "raw", str(sorted(listed)))
        row = listed["interview.vtt"]
        check("72: a transcript's row carries its case, no sheets, and the raw source it is made into as suggested",
              row["case"] == "P7 - Juno" and row["sheets"] == [] and slashed(row["suggested"]).endswith("P7 - Juno/Source/interview.xlsx")
              and row["board"] is None and not row["locked"], str(row))

        # ── F. the card's route: read, make, no overwrite, and on into a case
        vtt = source / "interview.vtt"
        seen = idiograph_routes.api_import({"path": str(vtt), "op": "read"})
        check("72: read answers the first turns as read, the count, the speakers and the interviewer guessed",
              [t["name"] for t in seen["turns"]] == ["Sam Okafor", "Juno", "Sam Okafor"] and seen["turns"][2]["time"] == "1:02:03"
              and seen["count"] == 3 and seen["speakers"] == [{"name": "Sam Okafor", "turns": 2}, {"name": "Juno", "turns": 1}]
              and seen["interviewer"] == "Sam Okafor" and seen["setting"] == "Adam" and seen["said"] is None
              and seen["out"] == "interview.xlsx" and seen["columns"] is None, str(seen))
        check("72: and the name each speaker's turns go under as the interviewer, for the card's line",
              seen["as"] == {"Sam Okafor": "Adam", "Juno": "Adam"})
        long = source / "long.txt"
        long.write_text("".join(f"Sam: Question {i}?\nJuno: Answer {i}.\n" for i in range(12)), encoding="utf-8")
        many = idiograph_routes.api_import({"path": str(long), "op": "read"})
        check("72: the card shows the first eight turns, and the count is the whole file's",
              len(many["turns"]) == convert.PREVIEW == 8 and many["count"] == 24)
        before = sorted(p.name for p in source.iterdir())
        out = idiograph_routes.api_import({"path": str(vtt), "op": "make", "interviewer": "Sam Okafor"})
        made = source / "interview.xlsx"
        check("72: make writes <file name>.xlsx beside the file and answers it as a raw source row",
              made.exists() and sorted(p.name for p in source.iterdir()) == sorted(before + ["interview.xlsx"])
              and out["source"]["kind"] == "raw" and out["source"]["name"] == "interview"
              and slashed(out["source"]["path"]).endswith("Source/interview.xlsx") and out["source"]["sheets"] == [convert.SHEET]
              and slashed(out["source"]["suggested"]).endswith("P7 - Juno/P7 Juno - EN & ES.xlsx"), str(out))
        written = openpyxl.load_workbook(made)
        sheet = written.active
        cols = wb_mod.detect_columns(sheet)
        values = [[c.value for c in r] for r in sheet.iter_rows(min_row=2)]
        check("72: the workbook written passes is_raw_source, its times Excel times, the interviewer under Settings' name",
              wb_mod.is_raw_source(cols) and [v[0] for v in values] == ["Adam", "Juno", "Adam"]
              and values[2][1] == dt.time(1, 2, 3) and sheet.cell(2, 2).number_format == "h:mm:ss"
              and not any(c.fill.fill_type for r in sheet.iter_rows() for c in r), str(values))
        written.close()
        stamp = made.read_bytes()
        try:
            idiograph_routes.api_import({"path": str(vtt), "op": "make", "interviewer": "Sam Okafor"})
            refused = ""
        except WorkbookError as exc:
            refused = str(exc)
        check("72: make never writes over a file there, and says so in one line",
              refused == "interview.xlsx is already there." and made.read_bytes() == stamp, refused)
        try:
            convert.write_source(zoom, made)
            guarded = False
        except FileExistsError:
            guarded = True
        check("72: write_source refuses a name already taken, whoever calls it", guarded and made.read_bytes() == stamp)
        again = {c["name"]: c["kind"] for c in idiograph_routes.api_cases({})["cases"]}
        check("72: the transcript is offered no more, and its raw source is, to create the annotated workbook from",
              "interview.vtt" not in again and again.get("interview") == "raw", str(sorted(again)))
        opened = idiograph_routes.api_create({"path": out["source"]["path"]})
        stops = [r for s in opened["sheets"] for r in s["rows"] if rounds_mod.is_stop(r, "Adam")]
        check("72: the create step after it builds a case that opens, the interviewer's turns context",
              opened["sheets"][0]["name"] == convert.SHEET and len(opened["sheets"][0]["rows"]) == 3
              and [r["name"] for r in stops] == ["Juno"] and (case / "P7 Juno - EN & ES.xlsx").exists())
        txt = source / "notes.txt"
        plain_out = idiograph_routes.api_import({"path": str(txt), "op": "make", "interviewer": "Sam"})
        untimed_case = wb_mod.read_case(source / "notes.xlsx")
        check("72: a plain text file with no times makes a workbook with no timestamps, which still reads as a case",
              plain_out["source"]["name"] == "notes"
              and [r["seconds"] for r in untimed_case["sheets"][0]["rows"]] == [None, None, None, None]
              and [r["name"] for r in untimed_case["sheets"][0]["rows"]] == ["Adam", "Juno", "Adam", "Juno"]
              and len(rounds_mod.build_rounds(untimed_case["sheets"], 10, "Adam")) == 1)
        table = idiograph_routes.api_import({"path": str(csv_file), "op": "read"})
        check("72: a CSV's read answers its headings and the mapping guessed",
              table["columns"] == ["Speaker", "Start", "End time", "Utterance"] and three(table["mapping"]) == {"name": 0, "ts": 1, "text": 3})
        quiet = source / "quiet.csv"
        quiet.write_text("Speaker,Start,Notes,Text\nSam,0:03,,How was it?\nJuno,0:09,,Slow.\n", encoding="utf-8")
        empty_map = idiograph_routes.api_import({"path": str(quiet), "op": "read", "columns": {"name": 0, "ts": 1, "text": 2}})
        check("72: a mapping that reads no words keeps the headings, says one line and leaves Make nothing to write",
              empty_map["said"] == "Idiograph could not read any passages from quiet.csv."
              and empty_map["columns"] == ["Speaker", "Start", "Notes", "Text"] and empty_map["count"] == 0
              and three(empty_map["mapping"]) == {"name": 0, "ts": 1, "text": 2})
        idiograph_routes.api_import({"path": str(xlsx), "op": "make", "columns": {"name": 0, "ts": 1, "text": 2}, "interviewer": "Sam"})
        check("72: an Excel file's raw source is <file name> (converted).xlsx, beside it",
              (source / f"walks two{convert.CONVERTED}.xlsx").exists() and xlsx.exists())
        bad = source / "noise.txt"
        bad.write_bytes(b"PK\x03\x04\x00\x00binary")
        said = idiograph_routes.api_import({"path": str(bad), "op": "read"})
        try:
            idiograph_routes.api_import({"path": str(bad), "op": "make"})
            nothing = False
        except WorkbookError as exc:
            nothing = str(exc) == said["said"]
        check("72: the unreadable file's card says its one line, and make writes nothing",
              said["said"] == "Idiograph could not read any passages from noise.txt." and said["turns"] == [] and nothing
              and not (source / "noise.xlsx").exists())
        try:
            idiograph_routes.api_import({"path": str(scratch / "noise.txt"), "op": "read"})
            outside = False
        except server_mod.OutsideRoot:
            outside = True
        check("72: a file outside the case root is refused", outside)
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY, server_mod.CONFIG_PATH = kept

    # ── G. the template
    shipped = support.source("template/Transcript template.xlsx")
    tbook = openpyxl.load_workbook(shipped)
    tws = tbook.active
    rows = [[c.value for c in r] for r in tws.iter_rows()]
    check("72: the template ships in the three-column shape with three invented rows, built by make_template.py",
          shipped.exists() and rows[0] == ["Name", "Timestamp", "Transcript"] and len(rows) == 4
          and [tuple(r) for r in rows[1:]] == [tuple(r) for r in make_template.ROWS]
          and wb_mod.is_raw_source(wb_mod.detect_columns(tws)) and tws.title == convert.SHEET, str(rows))
    check("72: its rows are the demo's world, its times Excel times, and no cell carries a fill",
          {r[0] for r in rows[1:]} == {"Interviewer", "Juno"} and all(isinstance(r[1], dt.time) for r in rows[1:])
          and not any(c.fill.fill_type for r in tws.iter_rows() for c in r))
    tbook.close()

    # ── H. the page
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda name: app.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in app else ""
    rows_fn = fn("renderFiles")
    check("72: a transcript's row is drawn as a raw source is, with make a workbook, and opens the import card",
          "const transcript = item.kind === 'transcript';" in rows_fn and "const raw = item.kind === 'raw' || transcript;" in rows_fn
          and "transcript ? t('distil.files.make_workbook') : t('distil.files.create_workbook')" in rows_fn
          and "transcript ? offerImport(item) : raw ? offerCreate(item) : openCaseIn(item.path)" in rows_fn
          and "if (!raw) {" in rows_fn)
    check("72: Esc closes it as every card, and its controls are bound",
          "'import'" in app.split("const OVERLAYS = ", 1)[1].split("\n", 1)[0]
          and "$('import-go').onclick = () => makeImport();" in app and "$('import-cancel').onclick = () => hide('import');" in app
          and "$('import-speakers').addEventListener('change'" in app
          and "$('import-map').addEventListener('change', (e) => { if (e.target.matches('select[data-col]')) readImport(); });" in app)
    check("72: the card reads through /api/import, and Make goes on into the create card with the list redrawn behind it",
          "api('/api/import', { path: IMPORT.item.path, op: 'read', ...importAsks() })" in fn("readImport")
          and "op: 'make'" in fn("makeImport") and "offerCreate(data.source" in fn("makeImport")
          and "loadLibrary()" in fn("makeImport") and fn("makeImport").index("hide('import')") < fn("makeImport").index("offerCreate")
          and "needsRestart(err) ? RESTART_LINE : err.message" in fn("readImport"))
    node = shutil.which("node")
    if not node:
        skip("72: the card in node", "node is not installed")
    else:
        run = subprocess.run([node, "--check", str(support.source("apps/idiograph/static/distil.js"))], capture_output=True, text=True, encoding="utf-8")
        check("72: app.js still parses", run.returncode == 0, run.stderr.strip()[:200])
        whole = lambda name: f"function {name}(" + fn(name) + "\n}"
        script = scratch / "import-card.js"
        script.write_text(support.i18n_js() +
            "const els = {};\n"
            "const $ = (id) => (els[id] = els[id] || { id, hidden: false, innerHTML: '', textContent: '', value: '', disabled: false,\n"
            "  querySelectorAll: () => [] });\n"
            "const S = { chooseRoot: false };\n"
            "const document = { activeElement: null };\n"
            "const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));\n"
            "const escAttr = (s) => esc(s).replace(/\"/g, '&quot;');\n"
            "const IMPORT = { item: null, read: null, busy: false, ask: 0, audio: '', picked: [] };\n"
            "const turnsWord = (n) => `${n} turn${n === 1 ? '' : 's'}`;\n"
            + line_of_js(support.text("family/static/shell.js", "apps/idiograph/static/distil.js"), "const importBrings = ") + "\n"
            + line_of_js(support.text("family/static/shell.js", "apps/idiograph/static/distil.js"), "const IMPORT_ROLES = ") + "\n"
            + line_of_js(support.text("family/static/shell.js", "apps/idiograph/static/distil.js"), "const importRole = ") + "\n"
            + line_of_js(support.text("family/static/shell.js", "apps/idiograph/static/distil.js"), "const SPEAKER_ROLES = ") + "\n"
            # the interviewer as the speakers' choosers have him, here read off the drawn choosers
            "const importInterviewer = () => (IMPORT.who !== undefined ? IMPORT.who\n"
            "  : ((els['import-speakers'].innerHTML.match(/data-speaker=\"([^\"]*)\"><option value=\"interviewer\" selected/) || [])[1] || ''));\n"
            + whole("importMapHtml") + "\n" + whole("importPreviewHtml") + "\n" + whole("speakerChoosersHtml") + "\n"
            + whole("importSaid") + "\n" + whole("drawImport") + "\n" + whole("drawImportAs") + "\n"
            + whole("drawImportTime") + "\n" + whole("drawImportAudio") + "\n"
            "const data = " + json.dumps(seen) + ";\n"
            "IMPORT.read = data; drawImport(data);\n"
            "const first = { who: importInterviewer(), as: $('import-as').textContent, asHidden: $('import-as').hidden,\n"
            "  map: $('import-map').hidden, rows: (els['import-turns'].innerHTML.match(/import-turn\"/g) || []).length,\n"
            "  count: els['import-turns'].innerHTML.includes('3 turns'), go: $('import-go').disabled };\n"
            "IMPORT.who = 'Juno'; drawImportAs(); delete IMPORT.who;\n"
            "const second = $('import-as').textContent;\n"
            "const tbl = " + json.dumps(table) + ";\n"
            "IMPORT.read = tbl; drawImport(tbl);\n"
            "const mapped = { map: $('import-map').hidden,\n"
            "  roles: [...$('import-map').innerHTML.matchAll(/<option value=\"(\\w*)\" selected>/g)].map((m) => m[1]),\n"
            "  leave: $('import-map').innerHTML.includes('Leave out'),\n"
            "  rows: ($('import-turns').innerHTML.match(/<td class=\"ip-text\"/g) || []).length, who: importInterviewer() };\n"
            "const e = " + json.dumps(empty_map) + ";\n"
            "IMPORT.read = e; drawImport(e);\n"
            "const empty = { said: $('import-said').textContent, hidden: $('import-said').hidden, go: $('import-go').disabled };\n"
            "console.log(JSON.stringify({ first, second, mapped, empty }));\n", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("72: the card draws in node", False, run.stderr.strip()[:400])
        else:
            o = json.loads(run.stdout)
            check("72: in node, the card presets the guessed interviewer and says his turns go under Settings' name",
                  o["first"] == {"who": "Sam Okafor", "as": "Written as Adam, the interviewer in Settings.", "asHidden": False,
                                 "map": True, "rows": 3, "count": True, "go": False}, str(o["first"]))
            check("72: in node, a CSV shows a chooser on each column as guessed, End time left out, its passages in the "
                  "preview, and its interviewer guessed",
                  o["mapped"] == {"map": False, "roles": ["name", "ts", "", "text"], "leave": True, "rows": 4, "who": "Sam"},
                  str(o["mapped"]))
            check("72: in node, a mapping with no words shows the line and leaves Make off",
                  o["empty"] == {"said": "Idiograph could not read any passages from quiet.csv.", "hidden": False, "go": True}, str(o["empty"]))



# The fixtures of area 72, every word invented: Juno and her dog, and Sam, who asks.
IMPORT_TEAMS = """WEBVTT

3b1c-ab/12-0
00:00:01.000 --> 00:00:04.200
<v Sam Okafor>So how did the first week with the dog go?</v>

3b1c-ab/13-0
00:00:04.800 --> 00:00:09.000 align:start position:10%
<v Juno Example>Slower than I thought. She slept a lot.</v>

3b1c-ab/13-1
00:00:09.100 --> 00:00:12.000
<v Juno Example>And I kept checking on her &amp; <c.loud>listening</c>.</v>

NOTE a note the reader passes over

00:01:02.500 --> 00:01:05.000
<v Sam Okafor>What did <i>checking</i> look like?</v>
"""
IMPORT_ZOOM = """WEBVTT

1
00:00:01.230 --> 00:00:04.560
Sam Okafor: So how did the first week go?

2
00:00:05.000 --> 00:00:08.000
Juno: Slower than I thought.

3
00:00:08.500 --> 00:00:10.000
Juno: She slept a lot.
And I said: let her be.

4
01:02:03.000 --> 01:02:05.000
Sam Okafor: Why was that?
"""
IMPORT_SRT = """1
00:00:01,230 --> 00:00:04,560
<i>Sam:</i> Morning walks first?

2
00:00:05,000 --> 00:00:08,000
Juno: Always. {\\an8}Rain or not.

3
00:00:08,100 --> 00:00:09,000
Sam: Even in snow?
"""
IMPORT_BARE = """WEBVTT

00:00:01.000 --> 00:00:02.000
The dog barked.

00:00:03.000 --> 00:00:04.000
Then it was quiet.
"""
IMPORT_PLAIN = """Interview with Juno
Recorded at home

[00:00:05] Sam: How was the first week?
Juno: [00:00:09] Slower than I thought.
She slept a lot.

And I said: let her be.
00:01:02 Sam: Why?
1:10 Juno: Because she was tired.
"""
IMPORT_PLAIN_UNTIMED = """Sam: How was the first week?
Juno: Slower than I thought.
Sam: Why so?
Juno: She slept, mostly.
"""
IMPORT_OTTER = """Speaker 1  0:03
How was the first week?

Speaker 2  0:09
Slower than I thought.

Speaker 1  1:02
Why?
"""
IMPORT_REV = """Sam Okafor (00:00:03):
How was the first week?

Juno (00:00:09):
Slower than I thought.
"""
IMPORT_CSV = ("Speaker;Start;End time;Utterance\nSam;00:00:03;00:00:05;How was the first week?\n"
              "Juno;9;12;Slower than I thought; she slept.\n;14;15;And then more.\nSam;01:02;01:05;=Why?\n")
