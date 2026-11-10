from __future__ import annotations

import csv
import inspect
import io
import json
import re
import shutil

from workbook import WorkbookError

from . import support
from .support import check, sift_words_js, skip


@support.as_app("sift")
def test_sift_table(scratch):
    print("\n103. Sift, round 3: the table, sorted, filtered and found by the browser, deciding from it, his own fields "
          "and columns under the lock and in the log, the participant guess, sift.json keeping the view, and the tools "
          "reading the fields and writing none")
    import subprocess
    import cli
    import sift_cli
    import locks
    import mcp_server
    import sift_mcp
    import server as server_mod
    import sift_routes
    import sift
    import sift_ai

    sjs = support.text("apps/sift/static/sift.js")
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    node = shutil.which("node")

    # ── A. an invented screening on village bakeries, every answer counted by hand
    base = scratch / "sift-table"
    shutil.rmtree(base, ignore_errors=True)
    folder = base / "bakeries"
    folder.mkdir(parents=True)
    head = ["rec_id", "title", "authors", "year", "journal", "doi", "pub_type", "sources", "abstract", "proposed_decision",
            "proposed_reason", "grounds", "decision", "reason"]
    long_abstract = " ".join(f"crumb{i}" for i in range(130))
    records = [
        ["K01", "Bread at dawn", "Rye, A.; Malt, B.", "2021", "Invented Crafts", "10.0000/bake.1", "article", "Index A; Index B",
         "Semi-structured interviews with 12 participants explored the first hours of a baker's day.", "include", "", "", "", ""],
        ["K02", "Ovens and heat", "Spelt, C.", "2019", "Invented Heat", "", "article", "Index A",
         "A trial of 40 ovens measured heat lost overnight.", "exclude", "E2", "A trial of 40 ovens", "", ""],
        ["K03", "The night shift", "Durum, D.", "2023", "Invented Crafts", "", "article", "Index B; Index C; Index A",
         "Eight adults who bake through the night described their sleep.", "", "", "", "", ""],
        ["K04", "Keeping a starter", "Emmer, E.", "2020", "", "", "thesis", "Index C",
         "N=6 home bakers were interviewed about keeping a starter alive.", "", "", "", "", ""],
        ["K05", "Flour prices since 1990", "Farro, F.", "1999", "Invented Prices", "", "report", "Index A",
         "Prices were counted by county.", "exclude", "E1", "", "", ""],
        ["K06", "Leaving the bakery", "Grist, G.", "2022", "", "", "article", "Index B",
         "Six men and four women told of the day they left.", "maybe", "", "", "", ""],
        ["K07", "The bakery as a home", "Hull, H.", "2024", "", "", "article", "citation chasing",
         "Twenty-three interviewees spoke of the bakery as a second home.", "", "", "", "", ""],
        ["K08", "Queues at the counter", "Ingot, I.", "2018", "", "", "article", "Index A; Index C", "", "", "", "", "", ""],
        ["K09", "Apprentices", "Jute, J.", "2021", "", "", "article", "Index B",
         "We report a sample of 14. Apprentices kept diaries for a month.", "", "", "", "", ""],
        ["K10", "ovens II", "Kiln, K.", "", "", "", "article", "Index A",
         "Of the 15 participants, nine were new to baking.", "", "", "", "", ""],
        ["K11", "A long account", "Loaf, L.", "2017", "", "", "article", "Index C", long_abstract, "", "", "", "", ""],
    ]
    csv_file = folder / sift.CSV_NAME
    with open(csv_file, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(head)
        w.writerows(records)
    original = csv_file.read_bytes()
    (folder / sift.REASONS_NAME).write_text("stage,code,meaning\nta,E1,Not about lived experience\nta,E2,Not qualitative\n",
                                            encoding="utf-8")

    def rows_of() -> list[dict]:
        with open(csv_file, encoding="utf-8-sig", newline="") as fh:
            return list(csv.DictReader(fh))

    def review_bytes(raw: bytes | None = None) -> bytes:
        """The CSV with every column Sift writes taken out, his fields and columns and the decisions, written as the
        review wrote it, to set against the same of the bytes the review wrote."""
        got = list(csv.reader(io.StringIO((raw if raw is not None else csv_file.read_bytes()).decode("utf-8-sig"), newline="")))
        keep = [i for i, name in enumerate(got[0]) if not sift.is_own(name) and name not in sift.DECISION_COLUMNS]
        out = io.StringIO(newline="")
        csv.writer(out).writerows([[row[i] for i in keep] for row in got])
        return out.getvalue().encode("utf-8")

    log = folder / sift.LOG_NAME
    lines = lambda: [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x.strip()] if log.exists() else []

    # ── B. the participant guess, a dozen invented abstracts, each answer counted by hand, none when unsure
    guesses = [
        ("Semi-structured interviews were held with 12 participants who keep bees.", 12),
        ("A purposive sample (N=8) of hobby beekeepers took part.", 8),
        ("Ten interviewees, n = 10, described a first swarm.", 10),
        ("Eight adults who had kept hives for a decade took part.", 8),
        ("Twenty-three interviewees spoke of swarms.", 23),
        ("forty-two nurses kept a diary", 42),
        ("Of the 15 participants, nine were new to bees.", 15),
        ("We report a sample of 14.", 14),
        ("Eight 13-year-old students kept bees at school.", 8),
        ("Over 1,200 respondents answered.", 1200),
        ("Six men and four women (n = 10) described a first swarm.", 10),
        ("We interviewed twelve beekeepers about their first winter.", None),
        ("In 2019 participants in a national survey were asked about honey.", None),
        ("A field trial of 400 hives measured honey yields.", None),
        ("Six men and four women described their first swarm.", None),
        ("Three themes were developed from the accounts.", None),
        ("Fifty-one participants answered.", None),
        ("Two or more participants shared a hive.", None),
        ("178 patient experiences were gathered.", None),
        ("p < .05 across groups, n = 1.5 on average", None),
        ("", None),
    ]
    got_guesses = [(sift.guess_participants(text), want) for text, want in guesses]
    check("103: the participant guess reads the counts a dozen abstracts give, digits, n = and N=, words to fifty, a word or "
          "two between the count and the people, and the first plausible one",
          all(g == w for g, w in got_guesses[:11]), str([(t[:30], g) for (t, _), (g, w) in zip(guesses, got_guesses) if g != w]))
    check("103: and gives none when unsure: a count of people it does not know, a year, other things counted, a count split "
          "by kind with no whole, themes, words past fifty, one patient's experiences, a mean and an empty abstract",
          all(g is None for g, _ in got_guesses[11:]), str([(t[:30], g) for (t, _), (g, _) in zip(guesses[11:], got_guesses[11:]) if g]))
    view = {r["rec_id"]: r for r in sift.screen(folder)["records"]}
    check("103: on reading, each record carries its guess and the searches that found it, and nothing is written",
          [view[k]["fields"]["guess"] for k in ("K01", "K02", "K03", "K04", "K06", "K07", "K09", "K10")]
          == [12, None, 8, 6, None, 23, 14, 15] and view["K03"]["found"] == ["Index B", "Index C", "Index A"]
          and view["K01"]["fields"]["confirmed"] is False and view["K01"]["fields"]["rating"] is None
          and csv_file.read_bytes() == original and not log.exists() and not (folder / sift.SETTINGS_NAME).exists())

    # ── C. the table's settings, its first columns and their order, kept in sift.json
    first = sift.table_settings(folder)
    check("103, updated 12 October (121) and 13 October (127): the table's first columns, in order: Database, Title, "
          "Authors, Year, Cited by, Participants, PDF, the decision and My rating shown, Abstract after Cited by and DOI "
          "after Participants hidden at first, Notes, Digest, Critique and Journal hidden, then the review's other columns, "
          "and the ID in none of them, since it stands first always",
          first["view"] == "record" and [(c["key"], c["shown"]) for c in first["columns"]]
          == [("found", True), ("title", True), ("authors", True), ("year", True), ("cited", True), ("abstract", False),
              ("participants", True), ("doi", False), ("pdf", True), ("decision", True), ("study", False), ("rating", True),
              ("notes", False), ("digest", False), ("critique", False), ("journal", False), ("retracted", False), ("oa", False),
              ("country", False), ("language", False), ("keyworks", False), ("matched", False), ("csv:pub_type", False)]
          # updated 13 October (128): Study after the decision, and the four columns from OpenAlex and Crossref after
          # Journal, each hidden at first, and 14 October (133): Language after Country and Matched in after Cites key
          # works, hidden at first
          and first["own"] == [], str(first["columns"]))
    js_cols = re.findall(r"^  (\w+): \{ label: '([^']+)', kind: '(\w+)'(, on: true)?", sjs, flags=re.M)
    check("103, updated 12 October (121): the page's columns are the same keys with the same headings shown at first, "
          "Database, Cited by and My rating sorting the larger first",
          [(k, bool(on)) for k, _l, _k, on in js_cols] == [(k, s) for k, s in sift.TABLE_COLUMNS]
          and dict((k, l) for k, l, _k, _o in js_cols)["found"] == "Database" and dict((k, l) for k, l, _k, _o in js_cols)["doi"] == "DOI"
          and "found: { label: 'Database', kind: 'found', on: true, first: 'desc' }," in sjs
          and "cited: { label: 'Cited by', kind: 'number', on: true, first: 'desc' }," in sjs
          and "rating: { label: 'My rating', kind: 'number', on: true, first: 'desc' }," in sjs, str(js_cols))
    sift_ai.save_settings(folder, prompt="Judge {stage} by {codes}.")
    saved = sift.save_view(folder, "table", [{"key": "notes", "shown": True}, {"key": "found", "shown": True},
                                             {"key": "abstract", "shown": False}])
    held = json.loads((folder / sift.SETTINGS_NAME).read_text(encoding="utf-8"))
    # Set columns' Reset to default (12 October, later): the columns as they first stand, given with the
    # settings and put back after a reorder, tried on a copy so the checks below keep the reorder
    twin = scratch / "sift-reset-103"
    shutil.rmtree(twin, ignore_errors=True)
    shutil.copytree(folder, twin)
    moved = sift.table_settings(twin)
    sift.save_view(twin, columns=moved["defaults"])
    back = sift.table_settings(twin)
    page_src = support.page_text()
    check("103, added 12 October (Reset to default): the settings give the columns as they first stand, Set columns' "
          "Reset to default puts them back after a reorder, and the button waits while they stand so",
          first["defaults"] == first["columns"] and [c["key"] for c in moved["columns"]][:2] == ["notes", "found"]
          and moved["defaults"] == first["defaults"] and back["columns"] == first["columns"]
          and '<button class="ghost small" id="sf-cols-reset" type="button">Reset to default</button>' in page_src
          and "$('sf-cols-reset').onclick = () => sfColsSave(((SF.table && SF.table.defaults) || [])" in sjs
          and "$('sf-cols-reset').disabled = !first || first === cols.map(" in sjs, str(back["columns"][:3]))
    shutil.rmtree(twin, ignore_errors=True)
    sift_ai.save_settings(folder, ai_proposals=False)
    kept = json.loads((folder / sift.SETTINGS_NAME).read_text(encoding="utf-8"))
    refused_view = ""
    try:
        sift.save_view(folder, "grid")
    except sift.SiftError as exc:
        refused_view = str(exc)
    try:
        sift.save_view(folder, columns=[{"key": "colour", "shown": True}])
    except sift.SiftError as exc:
        refused_view += " | " + str(exc)
    check("103: sift.json keeps the view and the columns in his order, those he left out after them, beside the AI "
          "switch and prompt, and the AI settings keep the table in turn",
          saved["view"] == "table" and [c["key"] for c in saved["columns"][:4]] == ["notes", "found", "abstract", "title"]
          and saved["columns"][2]["shown"] is False and held["prompt"] == "Judge {stage} by {codes}." and held["table"]["view"] == "table"
          and kept["table"] == held["table"] and sift.table_settings(folder)["view"] == "table"
          and refused_view == "The view is record or table. | The table has no column colour.", refused_view)
    before_pdf = json.loads((folder / sift.SETTINGS_NAME).read_text(encoding="utf-8"))
    before_pdf["table"]["columns"] = [c for c in before_pdf["table"]["columns"] if c["key"] != "pdf"]
    (folder / sift.SETTINGS_NAME).write_text(json.dumps(before_pdf), encoding="utf-8")
    placed = [c["key"] for c in sift.table_settings(folder)["columns"]]
    check("103, 12 October: a column of the table's own added since he placed his, PDF, goes after the one before it in "
          "the first order, wherever he moved that one, and shows",
          placed[:5] == ["notes", "found", "abstract", "title", "authors"] and placed[placed.index("doi") + 1] == "pdf"
          and [c for c in sift.table_settings(folder)["columns"] if c["key"] == "pdf"][0]["shown"] is True, str(placed))
    sift.save_view(folder, "record", [{"key": k, "shown": s} for k, s in sift.TABLE_COLUMNS])

    # ── D. his own fields: each under the lock, a line in the log with the old value and the new, the CSV written whole
    a = sift.set_field(folder, "K01", "rating", "5")
    b = sift.set_field(folder, "K03", "rating", 3)
    same = sift.set_field(folder, "K03", "rating", "3")
    sift.set_field(folder, "K07", "rating", "4")
    notes = sift.set_field(folder, "K01", "notes", "  Seed paper.\r\nRead it twice.  ")
    sift.set_field(folder, "K01", "digest", "Twelve bakers, the first hours.")
    sift.set_field(folder, "K01", "critique", "Small sample, rich accounts.")
    written = lines()
    check("103: a rating, notes, a digest and a critique are each one line in the log, act field, the field, the old value "
          "and the new, and a change that changes nothing writes nothing",
          [e["field"] for e in written] == ["rating", "rating", "rating", "notes", "digest", "critique"]
          and all(e["act"] == "field" and "stage" not in e and e["tool"] == "Sift" for e in written)
          and (written[0]["rec_id"], written[0]["was"], written[0]["value"]) == ("K01", "", "5")
          and [e["n"] for e in written] == [1, 2, 3, 4, 5, 6] and same["changed"] is False and a["changed"] and b["changed"]
          and notes["record"]["fields"]["notes"] == "Seed paper.\nRead it twice." and a["record"]["fields"]["rating"] == 5,
          str(written[:2]))
    now = {r["rec_id"]: r for r in rows_of()}
    check("103: they are columns of Sift's own after the last column, the review's columns and rows untouched byte for byte",
          list(now["K01"].keys())[len(head):] == ["rating", "notes", "digest", "critique"]
          and (now["K01"]["rating"], now["K03"]["rating"], now["K02"]["rating"]) == ("5", "3", "")
          and now["K01"]["notes"] == "Seed paper.\nRead it twice." and review_bytes() == review_bytes(original)
          and len(original.split(b"\r\n")) == len(csv_file.read_bytes().split(b"\r\n"))
          and all(new.startswith(old) for old, new in zip(original.split(b"\r\n"), csv_file.read_bytes().split(b"\r\n"))),
          str(list(now["K01"].keys())))
    guessed = sift.screen(folder)["records"][0]["fields"]
    check("103: a guess is never written, not on reading and not by another field's change",
          guessed["guess"] == 12 and guessed["confirmed"] is False and "participants" not in now["K01"]
          and all(e["field"] != "participants" for e in lines()))
    confirmed = sift.set_field(folder, "K01", "participants", "12")
    typed = sift.set_field(folder, "K03", "participants", " 9 ")
    entry = lines()[-2]
    now = {r["rec_id"]: r for r in rows_of()}
    check("103: confirming the guess or typing his own writes participants and participants_confirmed, the log naming the "
          "guess he saw, and the guess goes",
          (now["K01"]["participants"], now["K01"]["participants_confirmed"]) == ("12", "yes")
          and (now["K03"]["participants"], now["K03"]["participants_confirmed"]) == ("9", "yes")
          and (entry["field"], entry["was"], entry["value"], entry["guess"], entry["was_confirmed"]) == ("participants", "", "12", 12, False)
          and confirmed["record"]["fields"] == dict(confirmed["record"]["fields"], participants="12", confirmed=True, guess=None)
          and typed["record"]["fields"]["participants"] == "9" and now["K04"]["participants"] == "" and review_bytes() == review_bytes(original),
          str(entry))
    refusals = []
    for field, value in (("rating", "6"), ("rating", "four"), ("participants", "twelve"), ("title", "A new title"),
                         ("decision", "include"), ("proposed_decision", "include"), ("col_none", "x")):
        try:
            sift.set_field(folder, "K02", field, value)
            refusals.append("")
        except sift.SiftError as exc:
            refusals.append(str(exc))
    try:
        sift.set_field(folder, "K99", "rating", "2")
    except sift.SiftError as exc:
        refusals.append(str(exc))
    check("103: a rating past 5, a participant count in words, a review column, a decision, a proposal or a column he "
          "never added is refused in one line and nothing written",
          refusals[:3] == ["A rating is 1 to 5 stars, or none.", "A rating is 1 to 5 stars, or none.",
                           "Participants is a whole number, or none."]
          and all(r.endswith("is not a field of yours, so nothing was written.") for r in refusals[3:7])
          and refusals[7] == "There is no record K99 in screening.csv." and review_bytes() == review_bytes(original), str(refusals))
    before, held_log = csv_file.read_bytes(), log.read_bytes()
    busy = []
    with locks.held(sift.lock_path(folder)):
        for act in (lambda: sift.set_field(folder, "K02", "rating", "2", wait=0.2),
                    lambda: sift.column(folder, "add", name="Busy", wait=0.2),
                    lambda: sift.save_view(folder, "table", wait=0.2)):
            try:
                act()
                busy.append("")
            except WorkbookError as exc:
                busy.append(str(exc))
    check("103: each field, column and view change takes screening.lock, and while another writer holds it says so and "
          "writes nothing",
          busy == [locks.BUSY] * 3 and csv_file.read_bytes() == before and log.read_bytes() == held_log
          and all("locks.held(lock_path(folder), wait)" in inspect.getsource(f) for f in (sift.set_field, sift.column, sift.save_view)),
          str(busy))
    cleared = sift.set_field(folder, "K03", "rating", "")
    check("103: a rating is cleared by none, logged as the old value and an empty new one",
          cleared["record"]["fields"]["rating"] is None and (lines()[-1]["was"], lines()[-1]["value"]) == ("3", ""))
    sift.set_field(folder, "K03", "rating", "3")

    # ── E. his columns: added, renamed, their choices changed and removed, each a line of the log
    added = sift.column(folder, "add", name="Method", kind="choice", options="IPA\nThematic\nIPA\n")
    sift.column(folder, "add", name="Setting", kind="text")
    sift.set_field(folder, "K01", "col_method", "IPA")
    sift.set_field(folder, "K03", "col_method", "Thematic")
    sift.set_field(folder, "K07", "col_method", "IPA")
    sift.set_field(folder, "K01", "col_setting", "  a village  bakery ")
    wrong = []
    for act in (lambda: sift.set_field(folder, "K02", "col_method", "Survey"),
                lambda: sift.column(folder, "add", name="method"), lambda: sift.column(folder, "add", name="!!"),
                lambda: sift.column(folder, "add", name="Kind", kind="choice", options=""),
                lambda: sift.column(folder, "remove", key="title"), lambda: sift.column(folder, "change", key="col_none", name="X")):
        try:
            act()
            wrong.append("")
        except sift.SiftError as exc:
            wrong.append(str(exc))
    now = {r["rec_id"]: r for r in rows_of()}
    settings = sift.table_settings(folder)
    check("103: a column he adds is col_ and its name after the last column, shown in the table, a choice list keeping each "
          "choice once, a value of a choice one of them, a text value one line",
          added["key"] == "col_method" and list(now["K01"].keys())[-2:] == ["col_method", "col_setting"]
          and settings["own"] == [dict(c, where="table", not_reported=False, when=None, section="", **{"from": ""}) for c in
                                  ({"key": "col_method", "name": "Method", "type": "choice", "options": ["IPA", "Thematic"]},
                                   {"key": "col_setting", "name": "Setting", "type": "text", "options": []})]
          and {"key": "col_method", "shown": True} in settings["columns"] and now["K01"]["col_setting"] == "a village bakery"
          and (now["K01"]["col_method"], now["K03"]["col_method"]) == ("IPA", "Thematic") and review_bytes() == review_bytes(original),
          str(settings["own"]))
    check("103: a choice not on the list, a name taken or with no letter, a choice list with no choice, a review column and a "
          "column he never added are refused in one line",
          wrong == ["Survey is not one of the choices of Method.", "There is a column method already.",
                    "A column's name needs a letter or a number.", "A choice list needs at least one choice.",
                    "There is no column of yours title.", "There is no column of yours col_none."], str(wrong))
    renamed = sift.column(folder, "change", key="col_method", name="Design")
    sift.column(folder, "change", key="col_design", options="IPA\nThematic\nNarrative")
    unchanged = sift.column(folder, "change", key="col_design", name="Design")
    now = {r["rec_id"]: r for r in rows_of()}
    col_lines = [e for e in lines() if e["act"] == "column"]
    check("103: a new name renames its column in the CSV, the values kept, a change of choices is kept, a change that "
          "changes nothing writes nothing, and each is a line of the log",
          renamed["key"] == "col_design" and "col_method" not in now["K01"] and now["K01"]["col_design"] == "IPA"
          and sift.table_settings(folder)["own"][0] == {"key": "col_design", "name": "Design", "type": "choice",
                                                        "options": ["IPA", "Thematic", "Narrative"], "where": "table",
                                                        "not_reported": False, "when": None, "section": "", "from": ""}
          and unchanged["changed"] is False and [e["change"] for e in col_lines] == ["add", "add", "change", "change"]
          and (col_lines[2]["column"], col_lines[2]["to"], col_lines[2]["was"]["name"]) == ("col_method", "col_design", "Method")
          and all("rec_id" not in e and "stage" not in e for e in col_lines) and review_bytes() == review_bytes(original), str(col_lines[-1]))
    sift.column(folder, "add", name="Spare", kind="text")
    sift.set_field(folder, "K05", "col_spare", "only here")
    removed = sift.column(folder, "remove", key="col_spare")
    gone = lines()[-1]
    check("103: a removal drops the column from the CSV and sift.json and keeps every value it held in its line of the log",
          "col_spare" not in rows_of()[0] and all(c["key"] != "col_spare" for c in removed["table"]["own"] + removed["table"]["columns"])
          and (gone["act"], gone["change"], gone["column"], gone["name"], gone["values"]) == ("column", "remove", "col_spare", "Spare",
                                                                                             {"K05": "only here"})
          and review_bytes() == review_bytes(original), str(gone))
    check("103: the log's new lines are passed over by the decisions, the rounds and undo, and the history of a record "
          "names its field changes",
          sift.read_log(folder) == [] and sift.undo_target(sift.read_log(folder)) is None
          and [e["field"] for e in sift.history(folder, "K01")["history"]][:4] == ["rating", "notes", "digest", "critique"])

    # ── F. a decision from the table: the same act, its note kept when the table sends none, then undo
    sift.decide(folder, "K02", "ta", "exclude", "E2", note="Ovens only")
    md_before = (folder / sift.PRISMA_NAME).read_text(encoding="utf-8")
    from_table = sift.decide(folder, "K05", "ta", "reject", "E1")
    sift.decide(folder, "K02", "ta", "exclude", "E1")
    sift.decide(folder, "K01", "ta", "include")
    sift.decide(folder, "K06", "ta", "maybe")
    md_after = (folder / sift.PRISMA_NAME).read_text(encoding="utf-8")
    decisions = [e for e in lines() if e["act"] == "decide"]
    now = {r["rec_id"]: r for r in rows_of()}
    check("103: a decision from the table is Sift's own act: one line in the log, the CSV's decision written, the flow moved, "
          "and with no note sent the note stands",
          from_table["changed"] and decisions[1]["rec_id"] == "K05" and (now["K05"]["decision"], now["K05"]["reason"]) == ("exclude", "E1")
          and decisions[2]["note"] == "Ovens only" and md_after != md_before and "Records excluded<br/>(n = 2)" in md_after
          and "rating" in now["K05"] and now["K01"]["rating"] == "5")
    undone = sift.undo(folder)
    check("103: undo from the table takes back the newest decision, by a line of its own, the fields untouched",
          undone["undone"]["rec_id"] == "K06" and lines()[-1]["act"] == "undo" and rows_of()[5]["decision"] == ""
          and {r["rec_id"]: r for r in rows_of()}["K01"]["rating"] == "5")
    sift.decide(folder, "K06", "ta", "maybe")
    check("103: and in the page a decision from the table sends no note, so the note stands, and moves on as on the record "
          "screen",
          "const note = SF.view === 'table' ? undefined : $('sf-note').value;" in fn(sjs, "sfDecide")
          and "if (SF.at < SF.ids.length - 1) SF.at += 1;" in fn(sjs, "sfDecide") and "SF.tvReveal = true;" in fn(sjs, "sfUndo"))

    # ── G. sort and filter, in node, on the records as the server gives them
    screen = sift.screen(folder)
    block = sjs.split("/* ── the table's rows: its columns, sort and filter, worked out with no page ── */", 1)[-1].split(
        "/* ── the table, drawn ── */", 1)[0]
    # the family's table ahead of it, which sorts and filters Sift's records through Sift's reader, sfRead
    block = support.table_js() + "\n" + block
    if node and "const sfRead = " in block:
        probe = scratch / "sift-table.js"
        probe.write_text(block + "\nconst data = " + json.dumps({"records": screen["records"], "table": screen["table"]}) + ";\n" + r"""
data.records.forEach((r) => { r.pdf = ['K03', 'K07'].includes(r.rec_id); });
const byId = new Map(data.records.map((r) => [r.rec_id, r]));
const ids = data.records.map((r) => r.rec_id);
const cols = [SF_ID, ...sfColumns(data.table)];
const sorted = (sort) => tbSortRows(ids, byId, sort, cols, sfRead('ta'));
const kept = (filters) => tbFilterRows(ids, byId, filters, cols, sfRead('ta'));
console.log(JSON.stringify({
  cols: cols.filter((c) => c.shown).map((c) => c.key),
  own: cols.filter((c) => c.own).map((c) => [c.key, c.kind, c.label]),
  title: sorted([{ key: 'title', dir: 'asc' }]),
  yearDesc: sorted([{ key: 'year', dir: 'desc' }]),
  found: sorted([{ key: 'found', dir: 'desc' }]),
  foundYear: sorted([{ key: 'found', dir: 'desc' }, { key: 'year', dir: 'asc' }]),
  decision: sorted([{ key: 'decision', dir: 'asc' }]),
  rating: sorted([{ key: 'rating', dir: 'desc' }]),
  participants: sorted([{ key: 'participants', dir: 'asc' }]),
  design: sorted([{ key: 'col_design', dir: 'asc' }]),
  id: sorted([{ key: 'rec_id', dir: 'desc' }]),
  oven: kept({ title: 'OVEN' }).length,
  years: kept({ year: { from: 2020, to: 2022 } }),
  rated: kept({ rating: { from: 4, to: null } }),
  people: kept({ participants: { from: 11, to: 50 } }),
  noYear: kept({ year: { from: null, to: null, none: true } }),
  yearOrNone: kept({ year: { from: 2023, to: null, none: true } }),
  many: kept({ found: ['|many'] }),
  indexC: kept({ found: ['index c'] }),
  undecided: kept({ decision: ['undecided'] }),
  rejected: kept({ decision: ['exclude'] }),
  e1: kept({ decision: ['exclude:E1'] }),
  ipa: kept({ col_design: ['IPA'] }),
  setting: kept({ found: ['index c', '|many'] }),
  both: kept({ found: ['|many'], year: { from: 2020, to: null } }),
  none: kept({ title: '  ', year: { from: '', to: '' } }).length,
  words: sfFirstWords(byId.get('K11').abstract, 100),
  pdfAsc: sorted([{ key: 'pdf', dir: 'asc' }]),
  pdfDesc: sorted([{ key: 'pdf', dir: 'desc' }]),
  withPdf: kept({ pdf: ['yes'] }),
  noPdf: kept({ pdf: ['no'] }),
  names: ['pub_type', 'abstract_from', 'url', 'pilot_id'].map(sfExtraLabel),
}));
""", encoding="utf-8")
        ran = subprocess.run([node, str(probe)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        check("103, updated 12 October (121) and 13 October (127): in node, the shown columns in his order after the ID, "
              "Abstract and DOI hidden at first, Cited by after Year, and his own columns by his names and kinds",
              out.get("cols") == ["rec_id", "found", "title", "authors", "year", "cited", "participants", "pdf", "decision", "rating",
                                  "col_design", "col_setting"]
              and out.get("own") == [["col_design", "choice", "Design"], ["col_setting", "text", "Setting"]],
              (ran.stderr or ran.stdout)[:300])
        check("103: sorting text ignores case and runs numbers naturally, a number the larger first, the empty last either way",
              out.get("title") == ["K11", "K09", "K01", "K05", "K04", "K06", "K02", "K10", "K08", "K07", "K03"]
              and out.get("yearDesc") == ["K07", "K03", "K06", "K01", "K09", "K04", "K02", "K08", "K11", "K05", "K10"]
              and out.get("id") == ["K11", "K10", "K09", "K08", "K07", "K06", "K05", "K04", "K03", "K02", "K01"], str(out.get("title")))
        check("103: by the found-by count the records more than one search found come first, a tie in the CSV's order, and a "
              "second key orders each tie",
              out.get("found") == ["K03", "K01", "K08", "K02", "K04", "K05", "K06", "K07", "K09", "K10", "K11"]
              and out.get("foundYear") == ["K03", "K08", "K01", "K05", "K11", "K02", "K04", "K09", "K06", "K07", "K10"],
              str(out.get("foundYear")))
        check("103: by decision accept, maybe, then rejects by reason, the undecided last, by rating the most stars first, by "
              "participants the count or the guess, and by a choice column in the order of its choices",
              out.get("decision") == ["K01", "K06", "K02", "K05", "K03", "K04", "K07", "K08", "K09", "K10", "K11"]
              and out.get("rating") == ["K01", "K07", "K03", "K02", "K04", "K05", "K06", "K08", "K09", "K10", "K11"]
              and out.get("participants") == ["K04", "K03", "K01", "K09", "K10", "K07", "K02", "K05", "K06", "K08", "K11"]
              and out.get("design") == ["K01", "K07", "K03", "K02", "K04", "K05", "K06", "K08", "K09", "K10", "K11"],
              json.dumps({k: out.get(k) for k in ("decision", "rating", "participants", "design")}))
        check("103, 12 October: every kind of filter: a slider's two ends on the years, the stars and the participants, None "
              "under a slider alone or beside its range, more than one search or one by name, a decision or a reject's reason, a "
              "choice, two ticks in a group widening, two groups narrowing, and words or an older form passing all, since the "
              "browser's find finds words",
              out.get("oven") == 11 and out.get("years") == ["K01", "K04", "K06", "K09"]
              and out.get("rated") == ["K01", "K07"] and out.get("people") == ["K01", "K07", "K09", "K10"]
              and out.get("many") == ["K01", "K03", "K08"] and out.get("indexC") == ["K03", "K04", "K08", "K11"]
              and out.get("undecided") == ["K03", "K04", "K07", "K08", "K09", "K10", "K11"] and out.get("rejected") == ["K02", "K05"]
              and out.get("e1") == ["K02", "K05"] and out.get("ipa") == ["K01", "K07"]
              and out.get("setting") == ["K01", "K03", "K04", "K08", "K11"]
              and out.get("both") == ["K01", "K03"] and out.get("none") == 11
              and out.get("noYear") == ["K10"] and out.get("yearOrNone") == ["K03", "K07", "K10"], json.dumps(out)[:400])
        check("103, 12 October: the PDF column sorts the records without one first or last, a tie in the CSV's order, and "
              "filters to those with a PDF or without",
              out.get("pdfAsc") == ["K01", "K02", "K04", "K05", "K06", "K08", "K09", "K10", "K11", "K03", "K07"]
              and out.get("pdfDesc") == ["K03", "K07", "K01", "K02", "K04", "K05", "K06", "K08", "K09", "K10", "K11"]
              and out.get("withPdf") == ["K03", "K07"] and len(out.get("noPdf") or []) == 9, json.dumps({k: out.get(k) for k in ("pdfAsc", "withPdf")}))
        check("103: the abstract's first hundred words, and whether there were more",
              (out.get("words") or {}).get("cut") is True and len((out.get("words") or {}).get("text", "").split()) == 100)
    else:
        skip("103: sort and filter in node", "no node on this machine")

    # every row drawn as text, in node, with the app's own escaping
    if node:
        lead = app[app.index("const esc = "):app.index("// a line from the server with a command in backticks")]
        parts = [block, lead, sift_words_js(sjs),
                 "const SF = { stage: 'ta', folder: '/r/s', pdfAt: {} };", "function sfMeaning(code) { return code === 'E1' ? 'Not about lived experience' : ''; }"]
        parts += [f"function {name}(" + fn(sjs, name) + "\n}" for name in ("sfStars", "sfPillHtml", "sfLinked", "sfPdfUrl", "sfTvCell", "sfTvRowHtml")]
        probe = scratch / "sift-rows.js"
        probe.write_text("\n".join(parts) + "\nconst data = " + json.dumps({"records": screen["records"], "table": screen["table"]})
                         + ";\ndata.records.forEach((r) => { r.pdf = r.rec_id === 'K03'; });\n"
                         + "const cols = sfColumns(data.table).map((c) => (['abstract', 'doi'].includes(c.key) ? Object.assign({}, c, { shown: true }) : c))"
                         + ".filter((c) => c.shown);\n"
                         + "console.log(JSON.stringify(data.records.map((r) => sfTvRowHtml(r, cols))));\n", encoding="utf-8")
        ran = subprocess.run([node, str(probe)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        rows = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else []
        by = dict(zip([r["rec_id"] for r in screen["records"]], rows))
        check("103, updated 12 October (121): in node, a guess shows with its question mark as a button that confirms it, a "
              "confirmed count as text, and a record with neither reads Unknown, never an empty cell taken for none",
              '<button type="button" class="sf-guess" data-confirm="23" title="Confirm">23?</button>' in by["K07"]
              and '<td class="sf-c-num sf-ed" data-edit="participants">12</td>' in by["K01"]
              and '<td class="sf-c-num sf-ed" data-edit="participants"><span class="sf-blank">Unknown</span></td>' in by["K02"],
              by["K07"][:200])
    else:
        skip("103: the rows in node", "no node on this machine")

    # ── H. the server's routes for the table, and the view kept per screening
    kept_state = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    empty_root = base / "no-cases"
    empty_root.mkdir(exist_ok=True)
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"interviewer": "Adam"}), encoding="utf-8")
    try:
        server_mod.CONFIG_PATH = config_file
        server_mod.ROOT_OVERRIDE = str(empty_root)
        server_mod.STATE_MEMORY = {"recent": []}
        sift_routes.api_sift_review({"op": "open", "folder": str(folder)})
        viewed = sift_routes.api_sift({"op": "view", "folder": str(folder), "view": "table"})
        read = sift_routes.api_sift({"op": "read", "folder": str(folder)})
        rated = sift_routes.api_sift({"op": "field", "folder": str(folder), "rec_id": "K09", "field": "rating", "value": "2"})
        col = sift_routes.api_sift({"op": "column", "folder": str(folder), "act": "add", "name": "Country", "type": "text"})
        try:
            sift_routes.api_sift({"op": "field", "folder": str(folder), "rec_id": "K09", "field": "abstract", "value": "x"})
            bad = ""
        except WorkbookError as exc:
            bad = str(exc)
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY) = kept_state
    check("103: the route keeps the view, reads the table with every record's fields, writes a field and adds a column, and "
          "refuses a review column",
          viewed["table"]["view"] == "table" and read["table"]["view"] == "table" and "fields" in read["records"][0]
          and rated["record"]["fields"]["rating"] == 2 and rated["counts"]["records"] == 11 and col["key"] == "col_country"
          and bad == "abstract is not a field of yours, so nothing was written." and review_bytes() == review_bytes(original), bad)

    # ── I. the command line and MCP read the fields and write none
    def snapshot(at: Path) -> dict:
        return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*")) if p.is_file() and p.name != sift.LOCK_NAME}

    srv = mcp_server.Server(str(empty_root), app="sift")
    srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"clientInfo": {"name": "claude-ai"}}}))

    def tool_call(name, **given):
        return support.plain_result(srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                       "params": {"name": name, "arguments": given}}))["result"])

    held_files = snapshot(folder)
    listed = tool_call("sift_list", folder=str(folder), round="all")
    shown = tool_call("sift_show", folder=str(folder), rec_id="K01")
    k01 = next((r for r in listed["structuredContent"]["records"] if r["rec_id"] == "K01"), {})
    check("103: sift_list and sift_show give the found-by searches, his own fields and his columns, and write nothing",
          listed["isError"] is False and shown["isError"] is False and snapshot(folder) == held_files
          and k01.get("found") == ["Index A", "Index B"] and k01["fields"]["rating"] == 5 and k01["fields"]["participants"] == "12"
          and k01["fields"]["own"]["col_design"] == "IPA" and k01["fields"]["notes"] == "Seed paper.\nRead it twice."
          and [c["key"] for c in listed["structuredContent"]["columns"]] == ["col_design", "col_setting", "col_country"]
          and shown["structuredContent"]["record"]["fields"]["digest"] == "Twelve bakers, the first hours."
          and "My rating: 5 of 5." in shown["content"][0]["text"] and "Design: IPA" in shown["content"][0]["text"]
          and "rating 5" in shown["content"][0]["text"], shown["content"][0]["text"][:300])
    for_add = tool_call("sift_add", folder=str(folder), records=[{"title": "A rated record", "rating": "5", "col_design": "IPA"}])
    check("103: no tool writes a field or column of his: sift_add refuses them, and no tool takes a field or a value",
          for_add["isError"] and "col_design, rating are his own in Sift, never a new record's." in for_add["content"][0]["text"]
          and snapshot(folder) == held_files
          and not any({"field", "value", "rating", "notes", "digest", "critique", "participants"} & set(t["inputSchema"]["properties"])
                      for t in sift_mcp.SIFT_TOOLS)
          and "no tool writes any of them." in mcp_server.instructions("sift") and not ({"field", "column", "view"} & set(sift_cli.SIFT_ACTS)),
          for_add["content"][0]["text"])
    proposed = tool_call("sift_propose", folder=str(folder), stage="ta",
                         proposals=[{"rec_id": "K09", "decision": "include", "grounds": "Apprentices kept diaries"}])
    after = {r["rec_id"]: r for r in rows_of()}
    check("103: the review's proposals change none of his fields",
          proposed["isError"] is False and after["K09"]["proposed_decision"] == "include" and after["K09"]["rating"] == "2"
          and after["K01"]["col_design"] == "IPA")
    code, text, _ = cli.run(["sift", str(folder), "list", "--round", "all"])
    code_s, said, _ = cli.run(["sift", str(folder), "show", "K07"])
    check("103: the command line's list names a rating, the participants and a record found by more than one search, and "
          "show the guess as a guess",
          code == 0 and "K01  Yes  Bread at dawn (2021), proposed Yes (csv), found by 2, rated 5, 12 participants" in text
          and code_s == 0 and "Participants: 23?, a guess." in said and "Database: citation chasing." in said, text[:300])

    # ── J. the page
    down = fn(sjs, "sfKeyDown")
    check("103: the browser's find is never taken on the table: Cmd or Ctrl with any key but Z passes untouched before any key "
          "of the table, and no key of Sift's is F",
          down.index("if (MOD(e) || e.altKey || e.ctrlKey) return;") < down.index("if (!SF.picking && SF.view === 'table') {")
          and "key === 'f'" not in sjs and "'f'" not in down
          and "find" not in down.replace("browser's own find", "").replace("a find box", "").replace("dataset.act === 'find'", "")
          .replace("sfFind(", "")
          and "e.key === 'z' || e.key === 'Z'" in down)
    check("103, updated 12 October (122) and 6 November 2026 (330, the path's name its project's menu): the arrows move the "
          "row, Enter opens it as a record, Esc and the way back return "
          "to the table at its row and scroll, by the browser's Back where the record has its entry, and since Sift always "
          "opens on the table the view is kept nowhere",
          "sfMove(key === 'ArrowDown' ? 1 : -1)" in down and "sfOpenRecord();" in down
          and "SF.view === 'record' && key === 'Escape') { e.preventDefault(); sfToTable();" in down
          and "bandMenuWire('sf-name', () => siftBandMenu());" in fn(sjs, "sfBoot") and "sfSetView('table');" in fn(sjs, "sfToTable")
          and "$('sf-tv-box').scrollTop = SF.tvScroll;" in fn(sjs, "sfSetView")
          and "op: 'view', folder: SF.folder, view }" not in fn(sjs, "sfSetView") and "SF.savedView" not in sjs
          and "SF.view = 'table';" in fn(sjs, "siftOpen"))
    check("103, updated 12 October (121): the table's new parts ask Sift's own route alone, Export to Zotero its own, and "
          "send nothing to any model",
          set(re.findall(r"api\('(/api/[a-z-]+)'", sjs)) == {"/api/sift", "/api/zotero"}
          and set(re.findall(r"api\('(/api/[a-z-]+)'", sjs.split("/* ── Export to Zotero ── */", 1)[0])) == {"/api/sift"}
          and "op: 'field'" in fn(sjs, "sfFieldSave")
          and "op: 'column'" in fn(sjs, "sfColumn") and "propose" not in fn(sjs, "sfFieldSave") + fn(sjs, "sfColumn"))

    # ── K. the words
    said = lambda src: " ".join(re.findall(r'"""(.*?)"""', src, flags=re.S)) + " ".join(re.findall(r"(?m)^\s*#[^\n]*", src))
