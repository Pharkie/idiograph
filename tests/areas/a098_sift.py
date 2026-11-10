from __future__ import annotations

import csv
import inspect
import json
import os
import re
import shutil

from workbook import WorkbookError

from . import support
from .support import check, mode_is, skip
import idiograph_routes
import idiograph_cli


@support.as_app("sift")
def test_sift(scratch):
    print("\n98. Sift, screening for a systematic review: the CSV and its log, the decisions written from the log by "
          "rec_id, undo, the lock, the reasons, the grounds, the rounds, the counts on the screen and the command line, "
          "the PDF, the home screen and the page")
    import http.server
    import subprocess
    import threading
    import urllib.error
    import urllib.parse
    import urllib.request
    import cli
    import locks
    import mcp_server
    import server as server_mod
    import sift_routes
    import sift

    page = support.page_text()
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    sjs = support.text("apps/sift/static/sift.js")
    flat = lambda text: " ".join(str(text).split())
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    node = shutil.which("node")

    # ── A. an invented screening, five records on allotment gardening, written as the search tool writes them
    base = scratch / "sift"
    shutil.rmtree(base, ignore_errors=True)
    folder = base / "allotments"
    folder.mkdir(parents=True)
    head = ["rec_id", "pilot_id", "title", "authors", "year", "journal", "doi", "pub_type", "sources", "abstract_from",
            "abstract", "proposed_decision", "proposed_reason", "grounds", "decision", "reason"]
    records = [
        ["G001", "", "Growing together on the allotment", "Fern, A.; Reed, B.", "2019", "Journal of Invented Gardens",
         "10.0000/inv.1", "article", "Index One; Index Two", "Index One",
         "<h4>Background</h4>Twelve plot holders described   growing food\ntogether across one season.", "include", "",
         "growing food together", "", ""],
        ["G002", "7", "Yields of winter brassicas", "Moss, C.", "2020", "Invented Soil Science", "", "article", "Index One",
         "Index One", "A field trial of 400 plots measured yields under three regimes.", "exclude", "E2",
         "A field trial of 400 plots", "", ""],
        ["G003", "", "Sheds as meeting places", "Birch, D.", "2021", "", "https://doi.org/10.0000/inv.3", "dissertation",
         "Index Two", "", "Interviews with shed builders on the meanings of making.", "maybe", "",
         "words this abstract never holds", "", ""],
        ["G004", "", "A history of the allotment acts", "Ash, E.", "1999", "Invented History", "", "book", "Index Two", "",
         "", "", "", "", "", ""],
        ["G005", "", "Water butts and neighbours", "Oak, F.", "2022", "Invented Gardens", "", "article", "Index One",
         "Index One", "Gardeners spoke of sharing water, and of quarrels over hoses in a dry July.", "exclude", "E1",
         "sharing water ... quarrels over hoses", "", ""],
    ]
    csv_file = folder / sift.CSV_NAME

    def write_csv(rows, at=csv_file, header=head):
        with open(at, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(header)
            w.writerows(rows)

    def rows_of(path=csv_file) -> list[dict]:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            return list(csv.DictReader(fh))

    write_csv(records)
    os.chmod(csv_file, 0o640)
    (folder / sift.REASONS_NAME).write_text("stage,code,meaning\nta,E1,Not about lived experience\nta,E2,Not qualitative\n"
                                            "ft,F1,No full text found\n,X9,A duplicate record\n", encoding="utf-8")
    original = rows_of()
    sc = sift.load(folder)
    view = {r["rec_id"]: r for r in sift.screen(folder)["records"]}
    check("98: the CSV is read with its header and every record in its own order, by rec_id",
          sc.ids == ["G001", "G002", "G003", "G004", "G005"] and sc.header == head and sc.newline == "\r\n" and not sc.bom)
    check("98: the head shows title, authors, year, journal, the DOI as a link and the sources, and any other column that "
          "holds something stands after it, never a decision or a proposal column",
          view["G001"]["title"] == "Growing together on the allotment" and view["G001"]["link"] == "https://doi.org/10.0000/inv.1"
          and view["G003"]["link"] == "https://doi.org/10.0000/inv.3" and view["G001"]["sources"] == "Index One; Index Two"
          and dict(view["G002"]["more"]) == {"pilot_id": "7", "pub_type": "article", "abstract_from": "Index One"}
          and not any(k in dict(v["more"]) for v in view.values() for k in sift.PROPOSAL_COLUMNS + sift.DECISION_COLUMNS),
          str(view["G002"]["more"]))
    check("98: the abstract is plain text, a source's heading a line of its own and its spacing tidied",
          view["G001"]["abstract"] == "Background\nTwelve plot holders described growing food\ntogether across one season."
          and sift.plain("p &lt; .05 and <i>in vivo</i> x<y") == "p < .05 and in vivo x<y", view["G001"]["abstract"])

    def refused(rows, header=head) -> str:
        bad = base / "bad"
        shutil.rmtree(bad, ignore_errors=True)
        bad.mkdir()
        write_csv(rows, bad / sift.CSV_NAME, header)
        try:
            sift.load(bad)
        except sift.SiftError as exc:
            return str(exc)
        return ""

    no_abstract = [h for h in head if h != "abstract"]
    check("98: rec_id, title and abstract are required, and a record with no rec_id or one twice is refused in one line",
          refused([r[:10] + r[11:] for r in records], no_abstract) == "screening.csv needs the columns abstract, so it was not opened."
          and "has no rec_id" in refused([[""] + records[0][1:]]) and "G001 is in screening.csv twice" in refused([records[0], records[0]])
          and refused([["G9", "a title", "an abstract"]], ["rec_id", "title", "abstract"]) == ""
          and not sift.is_screening(base) and isinstance(sift.SiftError("x"), WorkbookError))

    # ── B. the grounds, marked where the abstract holds them word for word, whitespace set aside
    ta = {k: v["stages"]["ta"]["proposal"] for k, v in view.items()}
    a, b = (ta["G001"]["marks"] or [[0, 0]])[0]
    check("98: grounds found are marked across the abstract's own spacing and line breaks",
          ta["G001"]["found"] is True and flat(view["G001"]["abstract"][a:b]) == "growing food together", str(ta["G001"]))
    check("98: grounds the abstract does not hold are not found, and the screen shows them under the proposal",
          ta["G003"]["found"] is False and ta["G003"]["marks"] == [] and ta["G003"]["grounds"] == "words this abstract never holds"
          and "sift.grounds_lost_html" in fn(sjs, "sfDraw") and "prop.found === false" in fn(sjs, "sfDraw"))
    check("98: pieces joined by an ellipsis are each found, and a record with no grounds has none to find",
          len(ta["G005"]["marks"]) == 2 and ta["G005"]["found"] is True and ta["G004"]["found"] is None
          and sift.ground_spans("one two  three", "two\nthree") == ([[4, 14]], True), str(ta["G005"]))
    # case set aside, and nothing looser (17 October, later)
    opening = "Twelve plot holders described growing food"
    cased = [sift.ground_spans(opening, "twelve plot holders described"), sift.ground_spans(opening, "TWELVE PLOT ... FOOD"),
             sift.ground_spans("İstanbul allotments", "allotments"), sift.ground_spans(opening, "twelve plot-holders"),
             sift.ground_spans(opening, "twelve plots holders")]
    check("98, 17 October: grounds are found whatever their case, \"twelve plot holders described\" in an abstract that "
          "opens \"Twelve plot holders described\", a letter whose lower case is two letters kept as it is so the offsets "
          "hold, and nothing looser, a hyphen or a letter more still not found",
          cased[0] == ([[0, 29]], True) and cased[1] == ([[0, 11], [38, 42]], True) and cased[2] == ([[9, 19]], True)
          and cased[3][1] is False and cased[4][1] is False and sift.case_free("İ") == "İ" and sift.case_free("Q") == "q",
          str(cased))

    # ── C. the reasons file, its order, a row for both stages, and its absence
    reasons = sift.reasons(folder, sc)
    check("98: reasons.csv gives each stage its codes in the file's order, and a row with no stage serves both",
          [r["code"] for r in reasons["ta"]] == ["E1", "E2", "X9"] and [r["code"] for r in reasons["ft"]] == ["F1", "X9"]
          and reasons["ta"][1]["meaning"] == "Not qualitative" and reasons["file"] and not reasons["said"], str(reasons))
    bare = base / "bare"
    shutil.rmtree(bare, ignore_errors=True)
    bare.mkdir()
    write_csv(records + [["G010"] + records[1][1:11] + ["exclude", "E10", "", "", ""]], bare / sift.CSV_NAME)
    none = sift.reasons(bare, sift.load(bare))
    (bare / sift.REASONS_NAME).write_text("stage;code;meaning\n", encoding="utf-8")
    broken = sift.reasons(bare, sift.load(bare))
    check("98: with no reasons file the proposals' codes stand bare, E2 before E10, and a file with no code column says so",
          not none["file"] and [(r["code"], r["meaning"]) for r in none["ta"]] == [("E1", ""), ("E2", ""), ("E10", "")]
          and broken["file"] and "needs the columns code and meaning" in broken["said"]
          and [r["code"] for r in broken["ta"]] == ["E1", "E2", "E10"], str(none["ta"]))
    worded = base / "worded"
    shutil.rmtree(worded, ignore_errors=True)
    worded.mkdir()
    write_csv(records + [["G011"] + records[1][1:11] + ["maybe", "Leaves open who was asked", "", "", ""],
                         ["G012"] + records[1][1:11] + ["include", "Plainly about sharing plots", "", "", ""]], worded / sift.CSV_NAME)
    offered = [r["code"] for r in sift.reasons(worded, sift.load(worded))["ta"]]
    check("98, 17 October: a reason the CSV gives a Maybe or a Yes, the review's own words, is no reason to exclude and is "
          "never offered with No, an exclude's bare code still is",
          offered == ["E1", "E2"], str(offered))

    # ── D. the acts: each one line in the log, the CSV's decision columns written afresh, the proposal never
    log = folder / sift.LOG_NAME
    lines = lambda: log.read_bytes() if log.exists() else b""
    seen = [lines()]
    got = sift.decide(folder, "G001", "ta", "accept")
    entry = json.loads(lines().decode("utf-8").splitlines()[-1])
    check("98: a decision is one JSON line in the log with the time, record, stage, decision, reason, note, the proposal "
          "with its source, where it stood before and the tool",
          entry["n"] == 1 and entry["act"] == "decide" and entry["rec_id"] == "G001" and entry["stage"] == "title and abstract"
          and entry["decision"] == "include" and entry["reason"] == "" and entry["note"] == ""
          and entry["proposal"] == {"decision": "include", "reason": "", "source": "csv"}
          and entry["was"] == {"decision": "", "reason": "", "note": ""} and entry["tool"] == "Sift" and entry["at"]
          and got["changed"] and got["record"]["stages"]["ta"]["decision"] == "include", str(entry))
    check("98: and the CSV's decision column says include for it, the files' word for accept",
          rows_of()[0]["decision"] == "include" and sift.decision_word("Reject") == "exclude" and sift.decision_word("x") == "")
    seen.append(lines())
    before = csv_file.read_bytes()
    no_reason = wrong_code = ""
    # at full text a reject takes a reason, and at title and abstract one is optional (12 October, later, area 124)
    try:
        sift.decide(folder, "G001", "ft", "reject")
    except sift.SiftError as exc:
        no_reason = str(exc)
    try:
        sift.decide(folder, "G002", "ta", "reject", "F1")
    except sift.SiftError as exc:
        wrong_code = str(exc)
    check("98, updated 12 October (126): No or Exclude takes a reason of its stage, refused at full text with none or with one of the other stage, nothing written",
          no_reason == "Exclude at full text takes a reason, one of F1, X9." and wrong_code == "F1 is not a reason code at title and abstract."
          and csv_file.read_bytes() == before and lines() == seen[-1], f"{no_reason} | {wrong_code}")
    sift.decide(folder, "G002", "ta", "exclude", "E2", note="A trial, no voices")
    sift.decide(folder, "G003", "ta", "maybe")
    sift.decide(folder, "G005", "ta", "reject", "E2")
    same = sift.decide(folder, "G005", "ta", "reject", "E2")
    seen.append(lines())
    after = rows_of()
    keep = [h for h in head if h not in ("decision", "reason")]
    check("98: the log is only ever added to, each state of it the start of the next, and a decision that changes "
          "nothing writes nothing",
          all(seen[i + 1].startswith(seen[i]) for i in range(len(seen) - 1)) and len(seen[-1].splitlines()) == 4
          and same["changed"] is False)
    check("98: the proposal columns and every other column are untouched, the rows in their order",
          [[r[h] for h in keep] for r in after] == [[r[h] for h in keep] for r in original]
          and [(r["decision"], r["reason"]) for r in after]
          == [("include", ""), ("exclude", "E2"), ("maybe", ""), ("", ""), ("exclude", "E2")], str([(r["decision"], r["reason"]) for r in after]))
    check("98: the CSV is written whole through a temporary file and os.replace, its permissions kept, its lines as they were",
          mode_is(csv_file, 0o640) and not [p for p in folder.iterdir() if p.suffix == ".tmp"]
          and "os.replace(tmp, path)" in inspect.getsource(sift.write_atomic) and "mkstemp(dir=str(path.parent)" in inspect.getsource(sift.write_atomic)
          and "write_atomic(csv_path(sc.folder), after)" in inspect.getsource(sift.rebuild) and b"\r\n" in csv_file.read_bytes())

    # full text: the records accepted or left at maybe, its columns added when missing
    check("98: before any full text decision the CSV has no ft_ columns, and full text holds the records accepted or at maybe",
          "ft_decision" not in rows_of()[0] and sift.listed(sift.load(folder), sift.read_log(folder), "ft", "all") == ["G001", "G003"])
    try:
        sift.decide(folder, "G002", "full text", "accept")
        outside = ""
    except sift.SiftError as exc:
        outside = str(exc)
    sift.decide(folder, "G001", "ft", "exclude", "F1")
    ft = rows_of()
    check("98, updated 12 October (126): a full text decision adds ft_decision and ft_reason after the last column, and a "
          "record with No at title and abstract has none",
          list(ft[0].keys())[-2:] == ["ft_decision", "ft_reason"] and (ft[0]["ft_decision"], ft[0]["ft_reason"]) == ("exclude", "F1")
          and ft[1]["ft_decision"] == "" and outside == "G002 did not go on to full text, so it has no full text decision.", outside)

    # a note, then undo by lines of its own
    sift.note(folder, "G003", "ta", "Read the whole thesis")
    seen.append(lines())
    count = len(seen[-1].splitlines())
    first = sift.undo(folder)
    second = sift.undo(folder)
    seen.append(lines())
    tail = [json.loads(x) for x in seen[-1].decode("utf-8").splitlines()[-2:]]
    check("98: undo appends a line putting the record back as it stood, the note first, then the full text decision before it",
          first["undone"] == {"rec_id": "G003", "stage": "ta", "n": count} and second["undone"]["rec_id"] == "G001"
          and second["undone"]["stage"] == "ft" and [t["act"] for t in tail] == ["undo", "undo"]
          and tail[0]["undoes"] == count and tail[1]["undoes"] == count - 1 and tail[0]["note"] == ""
          and tail[0]["decision"] == "maybe" and seen[-1].startswith(seen[-2]) and len(seen[-1].splitlines()) == count + 2
          and rows_of()[0]["ft_decision"] == "" and rows_of()[0]["decision"] == "include", str(tail))
    empty = base / "fresh"
    shutil.rmtree(empty, ignore_errors=True)
    empty.mkdir()
    write_csv(records[:2], empty / sift.CSV_NAME)
    nothing = sift.undo(empty)
    with open(empty / sift.LOG_NAME, "w", encoding="utf-8") as fh:
        fh.write('{"n": 1, "rec_id": "G001", "stage": "title and abs')
    sift.decide(empty, "G001", "ta", "maybe")
    check("98: undo with nothing to undo writes nothing, and a line a crash cut short is passed over, the next act on a "
          "line of its own",
          nothing["undone"] is None and len(sift.read_log(empty)) == 1
          and (empty / sift.LOG_NAME).read_text(encoding="utf-8").count("\n") == 2 and rows_of(empty / sift.CSV_NAME)[0]["decision"] == "maybe")

    # ── E. another writer: records added and proposals filled under the lock, the rows found by rec_id
    def outside_write(rows):
        """As the agents' guide asks of another writer: under the lock, the whole file, a temporary file, a rename."""
        tmp = folder / "outside.tmp"
        with open(tmp, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, csv_file)

    with locks.held(sift.lock_path(folder)):
        rows = rows_of()
        rows[3]["proposed_decision"], rows[3]["proposed_reason"], rows[3]["decision"] = "exclude", "E1", "maybe"
        rows.append(dict(rows[2], rec_id="G006", title="Seed swaps by post", sources="citation chasing", decision="", reason="",
                         proposed_decision="", proposed_reason="", grounds=""))
        rows.reverse()
        outside_write(rows)
    sift.decide(folder, "G006", "ta", "include")
    outside_rows = {r["rec_id"]: r for r in rows_of()}
    check("98: a record another writer added at the foot is read, and the decisions land by rec_id, its order and its "
          "proposals kept, and a decision the CSV held before the log names the record is kept",
          [r["rec_id"] for r in rows_of()] == ["G006", "G005", "G004", "G003", "G002", "G001"]
          and outside_rows["G006"]["decision"] == "include" and outside_rows["G001"]["decision"] == "include"
          and outside_rows["G002"]["reason"] == "E2" and outside_rows["G004"]["decision"] == "maybe"
          and outside_rows["G004"]["proposed_decision"] == "exclude", str([(r["rec_id"], r["decision"]) for r in rows_of()]))

    # ── F. the lock: screening.lock beside the CSV, every act refused while another writer holds it
    before, held_log = csv_file.read_bytes(), lines()
    busy = ""
    with locks.held(folder / "screening.lock"):
        try:
            sift.decide(folder, "G004", "ta", "accept", wait=0.2)
        except WorkbookError as exc:
            busy = str(exc)
    check("98: screening.lock beside the CSV is the lock, and an act while another writer holds it says so and writes nothing",
          sift.LOCK_NAME == "screening.lock" and sift.lock_path(folder) == folder / "screening.lock" and busy == locks.BUSY
          and csv_file.read_bytes() == before and lines() == held_log
          and all("locks.held(lock_path(folder), wait)" in inspect.getsource(f) for f in (sift.decide, sift.note, sift.undo, sift.export))
          and inspect.getsource(sift.decide).index("locks.held(") < inspect.getsource(sift.decide).index("sc = load(folder)"), busy)

    # ── G. rounds and counts, against the proposal he saw
    entries = sift.read_log(folder)
    sc = sift.load(folder)
    rounds = {k: sift.listed(sc, entries, "ta", k) for k in sift.FILTERS}
    check("98: the rounds, undecided, maybe, accepted, rejected, all and those differing from the proposal, in the CSV's order",
          rounds == {"undecided": [], "maybe": ["G004", "G003"], "accepted": ["G006", "G001"], "rejected": ["G005", "G002"],
                     "all": ["G006", "G005", "G004", "G003", "G002", "G001"], "differs": ["G004"]}, str(rounds))
    c = sift.counts(sc, entries)["stages"]["ta"]
    check("98: the counts: each decision, the rejects by reason, matched and overruled against the proposal, a reject's "
          "reason differing, the decisions with no proposal, and all of it by the proposal's source",
          (c["records"], c["decided"], c["undecided"], c["include"], c["maybe"], c["exclude"]) == (6, 6, 0, 2, 2, 2)
          and c["reasons"] == {"E2": 2} and (c["proposed"], c["matched"], c["overruled"], c["reason_differs"], c["unproposed"])
          == (5, 4, 1, 1, 1) and c["table"]["exclude"]["maybe"] == 1 and c["table"]["exclude"]["exclude"] == 2
          and list(c["sources"]) == ["csv"] and c["sources"]["csv"]["overruled"] == 1 and c["overruled"] == len(rounds["differs"]), str(c))
    with locks.held(sift.lock_path(folder)):
        rows = rows_of()
        for r in rows:
            if r["rec_id"] == "G002":
                r["proposed_decision"] = "include"
        outside_write(rows)
    still = sift.counts(sift.load(folder))["stages"]["ta"]
    check("98: a proposal changed after he decided moves neither the counts nor the round of those that differ",
          (still["matched"], still["overruled"]) == (c["matched"], c["overruled"])
          and sift.listed(sift.load(folder), sift.read_log(folder), "ta", "differs") == ["G004"], str(still))
    (folder / sift.SEARCHES_NAME).write_text("date,source,interface,query,hits,records_saved,note\n"
                                             "inv,index-one,Invented index,allotment*,40,30,\n"
                                             "inv,index-two,Invented index,allotment*,25,20,\ninv,index-one,Invented index,shed*,5,x,\n",
                                             encoding="utf-8")
    searched = sift.counts(sift.load(folder))["searches"]
    check("98: log.csv beside the CSV gives the searches, hits and records saved summed by source and in all",
          searched["file"] and searched["hits"] == 70 and searched["saved"] == 50
          and searched["sources"] == {"index-one": {"hits": 45, "saved": 30}, "index-two": {"hits": 25, "saved": 20}}, str(searched))

    # ── H. the server: open, the list of reviews, the guard, the counts and export beside the command line, the PDF
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.PICK_FOLDER, server_mod.PLATFORM)
    same = lambda a, b: server_mod.same_folder(server_mod.abs_path(a), server_mod.abs_path(b))
    empty_root = base / "no-cases"
    empty_root.mkdir(exist_ok=True)
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"interviewer": "Adam"}), encoding="utf-8")
    try:
        server_mod.CONFIG_PATH = config_file
        server_mod.ROOT_OVERRIDE = str(empty_root)
        server_mod.STATE_MEMORY = {"recent": []}
        never = ""
        try:
            sift_routes.api_sift({"op": "read", "folder": str(folder)})
        except server_mod.OutsideRoot as exc:
            never = str(exc)
        opened = sift_routes.api_sift_review({"op": "open", "folder": str(folder)})
        home = server_mod.api_home({})
        row = (home.get("reviews") or [{}])[0]
        check("98: a screening is opened as a review of its own, kept in the list of reviews, and the home screen's Sift row "
              "names it with its counts, the cases' list untouched",
              never == sift_routes.NOT_OPENED and opened["opened"]
              and same(server_mod.STATE_MEMORY["sift_reviews"][0]["folder"], opened["review"]["folder"])
              and row.get("name") == "allotments" and row.get("there") and row["stages"]["ta"] == {"records": 6, "decided": 6, "undecided": 0}
              and "recent" not in home and server_mod.STATE_MEMORY["recent"] == [], str(row))
        try:
            sift_routes.api_sift_review({"op": "open", "folder": str(empty_root)})
            no_csv = ""
        except WorkbookError as exc:
            no_csv = str(exc)
        server_mod.PLATFORM = "darwin"
        server_mod.PICK_FOLDER = lambda prompt: None
        cancelled = sift_routes.api_sift_review({"op": "folder", "mode": "open"})
        server_mod.PICK_FOLDER = lambda prompt: bare
        chosen = sift_routes.api_sift_review({"op": "folder", "mode": "open"})
        chosen = sift_routes.api_sift_review({"op": "open", "folder": chosen["folder"]})
        server_mod.PLATFORM = "linux"
        try:
            sift_routes.api_sift_review({"op": "folder", "mode": "open"})
            typed = ""
        except WorkbookError as exc:
            typed = str(exc)
        check("98: Open review takes the Mac's folder dialog, its Cancel choosing nothing, or off a Mac the path typed, and a "
              "folder with no screening.csv and no plan is refused",
              no_csv == sift_routes.NOT_A_REVIEW and cancelled == {"chosen": False} and chosen["opened"]
              and same(server_mod.STATE_MEMORY["sift_reviews"][0]["folder"], chosen["review"]["folder"]) and typed == server_mod.NO_DIALOG
              and "/api/sift" in server_mod.POST_ONLY and server_mod.ROUTES.get("/api/sift") is sift_routes.api_sift)
        for n in range(17):
            extra = base / f"extra-{n}"
            extra.mkdir(exist_ok=True)
            write_csv(records[:1], extra / sift.CSV_NAME)
            sift_routes.api_sift_review({"op": "open", "folder": str(extra)})
        check("98: the list of reviews keeps the newest sixteen", len(server_mod.STATE_MEMORY["sift_reviews"]) == 16
              and server_mod.STATE_MEMORY["sift_reviews"][0]["folder"].endswith("extra-16"))
        sift_routes.api_sift_review({"op": "open", "folder": str(folder)})
        api_counts = sift_routes.api_sift({"op": "counts", "folder": str(folder)})
        code, out, err = cli.run(["sift", str(folder), "counts", "--json"])
        by_cli = support.plain(json.loads(out)) if out.strip() else {}
        code_t, text, _ = cli.run(["sift", str(folder), "counts"])
        check("98, updated 12 October (126): the counts the screen's API gives and the command line's agree, figure for "
              "figure and row for row, the lines in the stage's words",
              code == 0 and by_cli.get("counts") == api_counts["counts"] and by_cli.get("rows") == api_counts["rows"]
              and code_t == 0 and "Title and abstract: 6 records, 6 decided, 0 to screen." in text
              and "With a proposal 5: matched 4, overruled 1" in text, (err or text)[:300])
        counts_file = folder / sift.COUNTS_NAME
        dry = cli.run(["sift", str(folder), "export", "--dry-run"])
        made_dry = counts_file.exists()
        sift_routes.api_sift({"op": "export", "folder": str(folder)})
        by_api = counts_file.read_text(encoding="utf-8")
        counts_file.unlink()
        code_e, said, _ = cli.run(["sift", str(folder), "export"])
        by_line = counts_file.read_text(encoding="utf-8") if counts_file.exists() else ""
        check("98: export writes screening.counts.csv beside the CSV, the same from the screen and the command line, and a "
              "dry run writes nothing",
              dry[0] == 0 and not made_dry and by_api == by_line and by_api.startswith("stage,measure,count\n")
              and "title and abstract,overruled the proposal from csv,1" in by_api and code_e == 0
              and said.startswith("Wrote screening.counts.csv beside screening.csv"), by_api[:200])
        nope = cli.run(["sift", str(base), "counts"])
        check("98, 99: the command line refuses a folder with no screening.csv in one line, and sift is no project command, "
              "its MCP tools a set of their own",
              nope[0] == 1 and nope[2].strip() == "That folder holds no screening.csv." and ("sift", None) not in idiograph_cli.COMMANDS
              and all(t["command"][0] == "sift" for t in mcp_server.TOOLS if "sift" in t["name"]), nope[2])

        # the PDF, from the screening's own pdfs folder and nowhere else
        (folder / "pdfs").mkdir(exist_ok=True)
        pdf = b"%PDF-1.4\n% an invented report on seed swaps\n%%EOF\n"
        (folder / "pdfs" / "G001.pdf").write_bytes(pdf)
        secret = base / "secret.pdf"
        secret.write_bytes(b"%PDF-1.4 not his\n")
        try:
            os.symlink(secret, folder / "pdfs" / "G003.pdf")
        except (OSError, NotImplementedError):
            # Windows makes a link only for an account allowed to, so a link none can be made of is a file with no
            # PDF there: still refused, and the rest of the check stands
            pass
        (base / "G004.pdf").write_bytes(b"%PDF-1.4 beside the folder\n")
        served = sift_routes.sift_pdf({"folder": str(folder), "rec": "G001"})
        check("98: a record's PDF is served from pdfs/<rec_id>.pdf beside the CSV, and the screen knows which records have one",
              served == (200, pdf, "application/pdf") and sift.record_view(sift.load(folder), {}, "G001")["pdf"]
              and not sift.record_view(sift.load(folder), {}, "G002")["pdf"])
        outside_codes = [sift_routes.sift_pdf({"folder": str(folder), "rec": rec})[0] for rec in ("G002", "G003", "../G004", "G999")]
        check("98: nothing escapes pdfs/: a record with none, a link that leads outside, a path for a rec_id and a record the "
              "CSV lacks are all refused, and a folder never opened gets a 403",
              outside_codes == [404, 404, 404, 404] and sift.pdf_path(folder, "../G004") is None and sift.pdf_path(folder, "G003") is None
              and sift.pdf_path(folder, "pdfs/G001") is None and sift.pdf_path(folder, "G001") == (folder / "pdfs" / "G001.pdf").resolve()
              and sift_routes.sift_pdf({"folder": str(empty), "rec": "G001"})[0] == 403, str(outside_codes))

        # the same over HTTP, from the page's own address
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
        threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
        where = f"http://127.0.0.1:{httpd.server_address[1]}"

        def ask(route, body=None):
            data = None if body is None else json.dumps(body).encode("utf-8")
            req = urllib.request.Request(where + route, data=data, headers={"Content-Type": "application/json"} if data else {})
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    return r.status, r.headers.get("Content-Type", ""), r.read()
            except urllib.error.HTTPError as exc:
                return exc.code, exc.headers.get("Content-Type", ""), exc.read()

        try:
            got_pdf = ask("/sift/pdf?" + urllib.parse.urlencode({"folder": str(folder), "rec": "G001"}))
            read = ask("/api/sift", {"op": "read", "folder": str(folder)})
            as_get = ask("/api/sift?" + urllib.parse.urlencode({"op": "read", "folder": str(folder)}))
            decided = ask("/api/sift", {"op": "decide", "folder": str(folder), "rec_id": "G004", "stage": "ta",
                                        "decision": "exclude", "reason": "E1", "note": ""})
        finally:
            httpd.shutdown()
            httpd.server_close()
        answer = json.loads(decided[2]) if decided[0] == 200 else {}
        check("98: over HTTP the pane's PDF comes as application/pdf, the screening reads, a GET is refused, and a decision "
              "answers the record as it now stands with the counts",
              got_pdf[0] == 200 and got_pdf[1] == "application/pdf" and got_pdf[2] == pdf and read[0] == 200
              and len(json.loads(read[2])["records"]) == 6 and as_get[0] == 405 and answer.get("record", {}).get("rec_id") == "G004"
              and answer["stages"]["ta"]["decision"] == "exclude" and answer["counts"]["stages"]["ta"]["exclude"] == 3,
              str(decided)[:300])
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.PICK_FOLDER,
         server_mod.PLATFORM) = kept

    # ── I. the page
    home = page.split('id="sift-home"', 1)[1].split("</section>", 1)[0] if 'id="sift-home"' in page else ""
    down = fn(sjs, "sfKeyDown")
    check("98: the keys act on the Sift screen alone, ahead of the others, and never while he types in the note, where Esc "
          "leaves it",
          "if (!sfShown() || !$('settings').hidden || !$('feedback').hidden) return;" in down and "e.stopPropagation();" in down
          and down.index("if (typing) {") < down.index("if (MOD(e) && (e.key === 'z'")
          and all(f"key === '{k}'" in down for k in ("Enter", "ArrowLeft", "ArrowRight", "u", "t", "p", "?"))
          and "const decision = sfKeyDecision(key, SF.stage);" in down
          and "window.addEventListener('keydown', sfKeyDown, true);" in sjs and "/^[1-9]$/.test(key)" in down)
    routes = set(re.findall(r"api\('(/api/[a-z-]+)'", sjs))
    check("98: Sift asks its own routes alone, and Sync to Zotero its own since 9 October, and no model",
          # updated 13 October (128): Sift's suggestions of one study's reports, `suggest`, ask no model and no route
          routes == {"/api/sift", "/api/zotero"} and "/api/suggest" not in sjs and "op: 'suggest'" not in sjs, str(routes))
    # the screen kept and opened again through Sift's own part of the shell (sift_settings.js), since the family
    # codebase's third build
    sset = support.text("apps/sift/static/sift_settings.js")
    check("98: a restart comes back to the screening, and the home screen's rows open it",
          "return { screen: 'sift', path: SF.folder };" in fn(sset, "siftSpot") and "spot: siftSpot" in sset
          and "'sift'].includes(spot.screen)" in fn(app, "spotTaken")
          and "const own = familyApp(spot.screen);" in fn(app, "comeBack") and "own.open(spot.path, home, spot.screen)" in fn(app, "comeBack")
          and "siftOpen(path, home)" in fn(sset, "sfOpenOn"))
    if node:
        script = scratch / "sift-marks.js"
        lead = app[app.index("const esc = "):app.index("const escAttr = ")]
        script.write_text(lead + "\nfunction sfMarked(" + fn(sjs, "sfMarked").split("function sfMarked(", 1)[-1] + "\n}\n"
                          + "console.log(JSON.stringify([sfMarked('a <b> grows here', [[6, 11]]), sfMarked('plain', [])]));\n",
                          encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        check("98: in node, the abstract is escaped and the grounds marked",
              ran.returncode == 0 and json.loads(ran.stdout or "null") == ['a &lt;b&gt; <mark class="sf-ground">grows</mark> here', "plain"],
              (ran.stdout or ran.stderr).strip()[:200])
    else:
        skip("98: the marks in node", "no node on this machine")

    # ── J. the words
    said = lambda src: " ".join(re.findall(r'"""(.*?)"""', src, flags=re.S)) + " ".join(re.findall(r"(?m)^\s*#[^\n]*", src))
