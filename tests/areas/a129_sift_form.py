from __future__ import annotations

import csv
import json
import os
import shutil

from . import support
from .support import MINI_PAGE_JS, check, follow_stub, refusal_of, skip, urllib_path


def test_sift_form(scratch):
    print("\n129. Extract and appraise, 13 October, later: the stage after full text, its form his own columns extended, "
          "each field's place, type, Not reported, condition, section and Sift column, Set up the form and its op, the "
          "values saved and logged, carried and exported, the command line and MCP reading them, and apart from the "
          "form the plan's terms as filters of Screening")
    import datetime as dt
    import http.server
    import threading
    import argparse
    import subprocess
    import server as server_mod
    import sift_routes
    import sift
    import sift_search as ss
    import cli as cli_mod
    import sift_cli
    import mcp_server
    import sift_mcp

    app_src = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    sift_src = support.text("apps/sift/static/sift.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    node = shutil.which("node")
    base = scratch / "sift-form-129"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)

    # an invented review on kite flyers: three records included at full text, one at Maybe there, one left
    # out at title and abstract, and three benchmark papers, one left out, one undecided and one with no DOI
    review = base / "kite-review"
    review.mkdir()
    ss.new_plan(review, "Kite flyers", "How do kite flyers live with the wind?")
    ss.save(review, {"databases": ["psycinfo"], "blocks": [
        {"name": "Kites", "terms": ["kite*", '"box kite"', "TI(string W/2 line)", "spool"]},
        {"name": "Wind", "terms": ["gust*", "breeze"]}, {"name": "Empty", "terms": []}],
        "benchmark": ["10.5555/kite.6", "10.5555/kite.7", "10.5555/kite.8 Ripstop and patience"]})
    run = review / "runs" / "2031-06-01"
    run.mkdir(parents=True)
    rows = [("K1", "Flying a box kite on the cliff", "10.5555/kite.1", "Flyers spoke of the string line and the cliff."),
            ("K2", "Gusts on the hill", "10.5555/kite.2", "Twelve flyers spoke of the wind on the hill."),
            ("K3", "Tethered to the sky", "10.5555/kite.3", "A study of the Kités they flew, in Spanish and English."),
            ("K4", "The spool in the hand", "10.5555/kite.4", "Flyers and the reel."),
            ("K5", "Festivals of the air", "10.5555/kite.5", "Crowds at a festival."),
            ("K6", "A breeze that never came", "10.5555/kite.6", "Calm days."),
            ("K7", "Learning the bridle", "10.5555/kite.7", "The bridle and its knots."),
            ("K8", "Ripstop and patience", "", "Mending the sail.")]
    with open(run / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["rec_id", "title", "authors", "year", "journal", "doi", "sources", "abstract", "countries"])
        for i, (rec, title, doi, abstract) in enumerate(rows, 1):
            w.writerow([rec, title, "Reed, Ana; Holt, Ben", str(2020 + i), "Invented Kite Journal", doi, "Index A", abstract,
                        "GB; NZ" if i == 1 else ""])
    (run / "raw_psycinfo.json").write_text(json.dumps([{"doi": "10.5555/kite.2", "title": "Gusts on the hill",
                                                        "keywords": "breeze; open ground"}]), encoding="utf-8")
    for rec in ("K1", "K2", "K3", "K4", "K8"):
        sift.decide(run, rec, "ta", "include")
    for rec in ("K1", "K2", "K3"):
        sift.decide(run, rec, "ft", "include")
    sift.decide(run, "K4", "ft", "maybe")
    for rec in ("K5", "K6"):
        sift.decide(run, rec, "ta", "exclude")
    sift.column(run, "add", name="No. of analysts", kind="number")
    sift.set_field(run, "K1", "col_no_of_analysts", "2")
    lines = lambda: sift.read_lines(run)
    refusal = lambda f: refusal_of(f)

    # ── A. the stage's records, the benchmark papers and the name kept in one place
    got = sift.form_round(run)
    check("129: Extract and appraise lists the records included at full text alone, never one at Maybe there or left out "
          "before, and Benchmark papers the plan's benchmark papers whatever their decision, one with no DOI by its title",
          got["ids"] == ["K1", "K2", "K3"] and got["bench"] == ["K6", "K7", "K8"] and sift.screen(run)["bench"] == ["K6", "K7", "K8"],
          str(got))
    check("129: the list gives the form too, its sections and fields as the reading tools take them (13 October, evening)",
          {k: got[k] for k in ("stage", "sections", "fields")} == sift.form_of(run), str(got)[:300])

    # ── B. the form's fields: one definition, each type, its place, Not reported, its key
    add = lambda spec: sift.form_field(run, None, spec)
    added = add({"name": "Data collection", "type": "choice", "options": "Interviews\nFocus groups", "section": "Extraction"})
    add({"name": "Setting notes", "type": "long", "section": "Extraction"})
    add({"name": "Sample alike", "type": "yesno", "section": "Extraction"})
    add({"name": "Overall", "type": "choice", "options": ["Good", "Acceptable", "Unacceptable"], "section": "Appraisal"})
    add({"name": "Markers shown", "type": "multi", "options": "Narrative\nVoice\nDepth", "section": "Appraisal",
         "when": {"key": "overall", "values": ["Good"]}})
    add({"name": "Marker passages", "type": "passages", "section": "Appraisal", "when": {"key": "col_overall", "values": ["Good"]}})
    add({"name": "Citation", "from": "citation", "not_reported": False})
    add({"name": "Year taken", "type": "number", "from": "year"})
    add({"name": "Where", "from": "country"})
    t = sift.table_settings(run)
    by = {c["key"]: c for c in t["own"]}
    check("129: a field of the form is one of his columns, `col_` and its key, added after the CSV's last column, its "
          "type and choices kept, shown on the form, offering Not reported at first, in its section, the sections kept "
          "in his order",
          added["key"] == "col_data_collection" and sift.load(run).header[-1] == "col_where"
          and [by[k]["type"] for k in ("col_data_collection", "col_setting_notes", "col_sample_alike", "col_markers_shown",
                                        "col_marker_passages", "col_year_taken")] == ["choice", "long", "yesno", "multi", "passages", "number"]
          and by["col_markers_shown"]["options"] == ["Narrative", "Voice", "Depth"] and by["col_data_collection"]["where"] == "form"
          and by["col_data_collection"]["not_reported"] is True and by["col_citation"]["not_reported"] is False
          and t["sections"] == ["Extraction", "Appraisal"] and by["col_markers_shown"]["when"] == {"key": "col_overall", "values": ["Good"]}
          and by["col_no_of_analysts"]["where"] == "table" and by["col_no_of_analysts"]["not_reported"] is False
          and set(sift.OWN_KEYS) == set(by["col_overall"]), str({k: (c["type"], c["where"]) for k, c in by.items()}))
    check("129: a field of the form alone is offered as a column hidden at first, and a column on the screening's table "
          "shows there", {"key": "col_data_collection", "shown": False} in t["columns"]
          and {"key": "col_no_of_analysts", "shown": True} in t["columns"]
          and {"key": "col_where", "shown": False} in sift.default_columns(sift.load(run), t["own"])
          and {"key": "col_no_of_analysts", "shown": True} in sift.default_columns(sift.load(run), t["own"]), str(t["columns"][-4:]))
    added_line = [e for e in lines() if e.get("act") == "column" and e.get("change") == "add"][-1]
    check("129: each field set is a line of the log, act column, with the field whole",
          added_line["column"] == "col_where" and added_line["from"] == "country" and added_line["where"] == "form"
          and added_line["not_reported"] is True and "rec_id" not in added_line and "stage" not in added_line, str(added_line))

    # ── C. each type saved and logged, Not reported, a choice taken out of a list
    sift.set_field(run, "K1", "col_data_collection", "Interviews")
    sift.set_field(run, "K1", "col_setting_notes", "  On the cliff,\n  most days.  ")
    sift.set_field(run, "K1", "col_sample_alike", "Yes")
    sift.set_field(run, "K1", "col_overall", "Good")
    sift.set_field(run, "K1", "col_markers_shown", ["Depth", "Narrative"])
    sift.set_field(run, "K1", "col_marker_passages", [{"page": "4", "text": "The line sang."}, {"page": "", "text": "  "},
                                                      {"page": "9-10", "text": "We  ran\nwith it."}])
    sift.set_field(run, "K2", "col_data_collection", "not reported")
    sift.set_field(run, "K2", "col_sample_alike", "no")
    sift.set_field(run, "K2", "col_overall", "Acceptable")
    sc = sift.load(run)
    cell = lambda rec, key: sift.load(run).cell(rec, key)
    field_lines = [e for e in lines() if e.get("act") == "field"]
    check("129: each type is saved as the CSV keeps it, long text with its lines, yes or no in lower case, several "
          "choices in the list's order parted by a semicolon, passages as a JSON list each with its page, an empty one "
          "dropped, and Not reported as not reported",
          sc.cell("K1", "col_setting_notes") == "On the cliff,\n  most days." and sc.cell("K1", "col_sample_alike") == "yes"
          and sc.cell("K1", "col_markers_shown") == "Narrative; Depth"
          and json.loads(sc.cell("K1", "col_marker_passages")) == [{"page": "4", "text": "The line sang."},
                                                                    {"page": "9-10", "text": "We  ran\nwith it."}]
          and sc.cell("K2", "col_data_collection") == "not reported" and sc.cell("K2", "col_sample_alike") == "no",
          str([sc.cell("K1", k) for k in ("col_setting_notes", "col_markers_shown", "col_marker_passages")]))
    check("129: each value is one line of the log as his columns' values are, act field with the old value and the new",
          [e["field"] for e in field_lines][-9:] == ["col_data_collection", "col_setting_notes", "col_sample_alike", "col_overall",
                                                    "col_markers_shown", "col_marker_passages", "col_data_collection",
                                                    "col_sample_alike", "col_overall"]
          and field_lines[-3]["value"] == "not reported" and field_lines[-3]["was"] == ""
          and all(e["tool"] == "Sift" for e in field_lines), str(field_lines[-1]))
    wrong = [refusal(lambda: sift.set_field(run, "K3", "col_sample_alike", "maybe")),
             refusal(lambda: sift.set_field(run, "K3", "col_markers_shown", ["Narrative", "Colour"])),
             refusal(lambda: sift.set_field(run, "K3", "col_year_taken", "soon")),
             refusal(lambda: sift.set_field(run, "K3", "col_marker_passages", "a loose line")),
             refusal(lambda: sift.set_field(run, "K3", "col_citation", "Not reported") and "")]
    nr_text = cell("K3", "col_citation")
    check("129: a value its type cannot hold is refused and writes nothing, and on a field that offers no Not "
          "reported the words are the field's own text",
          all(wrong[:4]) and not cell("K3", "col_sample_alike") and not cell("K3", "col_markers_shown")
          and not cell("K3", "col_year_taken") and not cell("K3", "col_marker_passages")
          and nr_text == "Not reported", str(wrong) + nr_text)
    sift.form_field(run, "col_overall", {"options": ["Good", "Unacceptable"]})
    kept = cell("K2", "col_overall")
    unchanged = sift.set_field(run, "K2", "col_overall", "Acceptable")
    check("129: a choice taken out of a list leaves the value that held it in place, saving it again changes nothing, and "
          "a new value must be one of the list",
          kept == "Acceptable" and unchanged["changed"] is False
          and bool(refusal(lambda: sift.set_field(run, "K3", "col_overall", "Acceptable"))))
    sift.form_field(run, "col_overall", {"options": ["Good", "Acceptable", "Unacceptable"]})

    # ── D. conditions, done, the Sift columns a field starts from
    fields = sift.form_fields(sift.table_settings(run)["own"], sift.table_settings(run)["sections"])
    state = lambda rec: sift.form_state(sift.load(run), rec, fields)
    k1, k2 = state("K1"), state("K2")
    check("129: a field shown for another's values is shown while that field holds one of them and hidden otherwise, a "
          "Not reported holding none",
          "col_markers_shown" in k1["shown"] and "col_marker_passages" in k1["shown"]
          and "col_markers_shown" not in k2["shown"] and "col_marker_passages" not in k2["shown"], str(k2["shown"]))
    sift.set_field(run, "K1", "col_overall", "Unacceptable")
    hidden = state("K1")
    check("129: a hidden field keeps its value, never cleared, and goes back on show with it",
          "col_markers_shown" not in hidden["shown"] and cell("K1", "col_markers_shown") == "Narrative; Depth"
          and json.loads(cell("K1", "col_marker_passages"))[0]["page"] == "4")
    for key, value in (("col_citation", ""), ("col_year_taken", ""), ("col_where", ""), ("col_no_of_analysts", "")):
        pass
    k1_done = state("K1")["done"]
    sift.set_field(run, "K1", "col_overall", "Good")
    k1_shown_done = state("K1")["done"]
    check("129: a record is done when every field shown holds a value or Not reported, a hidden one counting for nothing, "
          "and a field taken from Sift holding Sift's value",
          k1_done is True and k1_shown_done is True and state("K2")["done"] is False and state("K3")["done"] is False,
          str((k1_done, k1_shown_done, state("K2"))))
    sc = sift.load(run)
    start = {c["key"]: sift.field_value(sc, "K1", c) for c in fields}
    check("129: a field that starts from a Sift column shows its value until he changes it, the citation, the year as a "
          "number and the countries by name, marked as Sift's",
          start["col_citation"] == ("Reed, Ana; Holt, Ben (2021). Flying a box kite on the cliff. Invented Kite Journal. "
                                    "https://doi.org/10.5555/kite.1", True)
          and start["col_year_taken"] == ("2021", True) and start["col_where"] == ("United Kingdom, New Zealand", True)
          and sift.field_value(sc, "K8", by["col_citation"])[0].endswith("Invented Kite Journal.")
          and state("K1")["sift"]["col_year_taken"] == "2021", str(start["col_citation"]))
    sift.set_field(run, "K1", "col_year_taken", "2019")
    check("129: his own value then stands in its place, and the Sift column's value is still given beside it",
          sift.field_value(sift.load(run), "K1", by["col_year_taken"]) == ("2019", False) and state("K1")["sift"]["col_year_taken"] == "2021")
    wrong = [refusal(lambda: add({"name": "Bad start", "type": "choice", "options": "A", "from": "title"})),
             refusal(lambda: add({"name": "Self", "when": {"key": "col_citation", "values": ["x"]}})),
             refusal(lambda: add({"name": "Loop", "type": "choice", "options": "A", "when": {"key": "col_overall", "values": ["Fair"]}})),
             refusal(lambda: sift.form_field(run, "col_overall", {"when": {"key": "col_markers_shown", "values": ["Depth"]}})),
             refusal(lambda: sift.form_field(run, "col_overall", {"type": "text"}))]
    check("129: a choice field starts from no Sift column, a condition names a field of choices and one of its values, two "
          "fields never wait on each other, and a field others wait on keeps its choices",
          len(wrong) == 5 and all(wrong), str(wrong))

    # ── E. keys, renaming, a column moved from the table to the form, removing
    renamed = sift.form_field(run, "col_data_collection", {"name": "How data were collected"})
    check("129: renaming a field keeps its values, its key following a name it came from",
          renamed["key"] == "col_how_data_were_collected" and cell("K1", "col_how_data_were_collected") == "Interviews"
          and cell("K2", "col_how_data_were_collected") == "not reported" and "col_data_collection" not in sift.load(run).header)
    keyed = sift.form_field(run, "col_how_data_were_collected", {"key": "data_collection"})
    again = sift.form_field(run, "col_data_collection", {"name": "Data gathered"})
    wrong = [refusal(lambda: sift.form_field(run, "col_data_collection", {"key": "overall"})),
             refusal(lambda: sift.form_field(run, "col_data_collection", {"key": "two words"})),
             refusal(lambda: sift.form_field(run, "col_data_collection", {"key": "study"})),
             refusal(lambda: sift.form_field(run, "col_data_collection", {"key": "OVERALL"}))]
    after = sift.table_settings(run)
    check("129: a key he edits renames the CSV's column with its values, a name changed after it leaves it, and a key "
          "taken, of other marks or the export's own is refused",
          keyed["key"] == "col_data_collection" and again["key"] == "col_data_collection"
          and cell("K1", "col_data_collection") == "Interviews"
          and next(c for c in after["own"] if c["key"] == "col_data_collection")["name"] == "Data gathered"
          and len(wrong) == 4 and all(wrong), str(wrong))
    moved = sift.form_field(run, "col_no_of_analysts", {"where": "both"})
    check("129: a column of his on the table moves to the form with its values, one definition, its place on the table kept",
          moved["changed"] and cell("K1", "col_no_of_analysts") == "2"
          and next(c for c in moved["table"]["own"] if c["key"] == "col_no_of_analysts")["where"] == "both"
          and {"key": "col_no_of_analysts", "shown": True} in moved["table"]["columns"]
          and "col_no_of_analysts" in [c["key"] for c in sift.form_fields(moved["table"]["own"], moved["table"]["sections"])])
    sift.form_field(run, "col_marker_passages", {"key": "passages_shown"})
    deps = {c["key"]: c for c in sift.table_settings(run)["own"]}
    sift.form_field(run, "col_overall", {"key": "overall_rating"})
    deps2 = {c["key"]: c for c in sift.table_settings(run)["own"]}
    check("129: a field shown for another's values follows that field's new key",
          deps2["col_markers_shown"]["when"]["key"] == "col_overall_rating" and deps2["col_passages_shown"]["when"]["key"] == "col_overall_rating"
          and cell("K1", "col_overall_rating") == "Good" and "col_passages_shown" in deps)
    add({"name": "Spare", "section": "Appraisal"})
    removed = sift.column(run, "remove", key="col_where")
    gone_line = lines()[-1]
    check("129: removing a field drops its column and keeps every value it held in the log's line",
          removed["changed"] and "col_where" not in sift.load(run).header and gone_line["change"] == "remove"
          and gone_line["column"] == "col_where" and gone_line["values"] == {}, str(gone_line))
    sift.set_field(run, "K2", "col_spare", "only here")
    sift.column(run, "remove", key="col_spare")
    check("129: a removed field with values keeps them in the log", lines()[-1]["values"] == {"K2": "only here"})

    # ── F. the order, the sections and the coordinator's op
    ordered = sift.order_form(run, [{"name": "", "fields": ["citation"]},
                                    {"name": "Appraisal", "fields": ["overall_rating", "markers_shown", "passages_shown"]},
                                    {"name": "Extraction", "fields": ["data_collection", "col_sample_alike"]}])
    t = ordered["table"]
    form_keys = [c["key"] for c in sift.form_fields(t["own"], t["sections"])]
    check("129: the form's order is set whole, sections and their fields, a field not named keeping its section after those "
          "named, and none of it a line of the log",
          t["sections"] == ["Appraisal", "Extraction"] and form_keys[:1] == ["col_citation"]
          and form_keys[form_keys.index("col_overall_rating"):form_keys.index("col_overall_rating") + 3]
          == ["col_overall_rating", "col_markers_shown", "col_passages_shown"]
          and form_keys.index("col_data_collection") > form_keys.index("col_passages_shown")
          and lines()[-1]["act"] == "column" and lines()[-1]["change"] == "remove", str(form_keys))
    wrong = [refusal(lambda: sift.order_form(run, [{"name": "A", "fields": ["nothing_here"]}])),
             refusal(lambda: sift.order_form(run, [{"name": "A", "fields": ["citation"]}, {"name": "A", "fields": []}])),
             refusal(lambda: sift.order_form(run, "Appraisal"))]
    check("129: an order naming a field he has not, a section twice or of another shape is refused",
          len(wrong) == 3 and all(wrong), str(wrong))
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"interviewer": "Adam"}), encoding="utf-8")
    try:
        server_mod.CONFIG_PATH = config_file
        server_mod.ROOT_OVERRIDE = str(base)
        server_mod.STATE_MEMORY = {"recent": []}
        sift_routes.api_sift_review({"op": "open", "folder": str(review)})
        api = lambda body: sift_routes.api_sift(dict(body, folder=str(run)))
        listed = api({"op": "form", "act": "list"})
        set_one = api({"op": "form", "act": "field", "field": {"name": "Software", "type": "choice", "options": ["None named", "A tool"],
                                                               "section": "Extraction", "key": "software"}})
        changed = api({"op": "form", "act": "field", "key": "software", "field": {"not_reported": False}})
        order = api({"op": "form", "act": "order", "sections": [{"name": "Extraction", "fields": ["software"]}]})
        listed_after = api({"op": "form", "act": "list"})
        read = api({"op": "form", "act": "read"})
        value = api({"op": "field", "rec_id": "K3", "field": "col_software", "value": "A tool"})
        dropped = api({"op": "form", "act": "remove", "key": "software"})
        bad = refusal(lambda: api({"op": "form", "act": "rename"}))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
    check("129: the form op the coordinator calls: list, a field set whole by one call with its key, a change of one part "
          "keeping the rest, the order by another, read, remove, a value through the field op, and any other act refused",
          listed["ids"] == ["K1", "K2", "K3"] and listed["bench"] == ["K6", "K7", "K8"] and set_one["key"] == "col_software"
          and "software" in [f["plain_key"] for f in listed_after["fields"]]
          and listed_after["sections"] == order["table"]["sections"]
          and next(c for c in changed["table"]["own"] if c["key"] == "col_software")["options"] == ["None named", "A tool"]
          and next(c for c in changed["table"]["own"] if c["key"] == "col_software")["not_reported"] is False
          and order["table"]["sections"][0] == "Extraction" and "software" in read["columns"]
          and value["record"]["fields"]["own"]["col_software"] == "A tool" and dropped["changed"]
          and bool(bad),
          str(order["table"]["sections"]))

    # ── G. the export and the reading tools
    sift.set_field(run, "K3", "col_sample_alike", "not reported")
    done = sift.export_form(run)
    with open(run / sift.FORM_CSV, encoding="utf-8", newline="") as fh:
        table = list(csv.reader(fh))
    head, body = table[0], {r[0]: dict(zip(table[0], r)) for r in table[1:]}
    check("129: Export the form writes screening.form.csv beside the screening, one row per record included at full text, "
          "rec_id and study first, then each field under its key in the form's order",
          done["written"] and done["records"] == 3 and done["file"] == "screening.form.csv"
          and head[:3] == ["rec_id", "study", "citation"] and list(body) == ["K1", "K2", "K3"]
          and "no_of_analysts" in head and "col_data_collection" not in head and "data_collection" in head, str(head))
    check("129: each cell as the export writes it: Not reported as not reported, several choices joined by a semicolon "
          "and a space, passages as p. N with the words in quotes joined by a bar, a field not shown left empty, Sift's "
          "value where he gave none",
          body["K1"]["markers_shown"] == "Narrative; Depth"
          and body["K1"]["passages_shown"] == 'p. 4: "The line sang." | p. 9-10: "We  ran\nwith it."'
          and body["K2"]["data_collection"] == "not reported" and body["K2"]["markers_shown"] == ""
          and body["K3"]["sample_alike"] == "not reported" and body["K2"]["year_taken"] == "2022"
          and body["K1"]["year_taken"] == "2019" and body["K1"]["no_of_analysts"] == "2" and body["K1"]["study"] == "", str(body["K1"]))
    nothing = sift.export_form(base / "kite-review" / "runs" / "2031-06-01", dry_run=True)
    check("129: a dry run counts and writes nothing", nothing["written"] is False and nothing["records"] == 3)
    snap = (sift.csv_path(run).read_bytes(), sift.log_path(run).read_bytes())
    shown = sift_cli.cmd_sift(argparse.Namespace(folder=str(run), act="show", rec_id="K1", stage="ft", search=False))[1]
    formed = sift_cli.cmd_sift(argparse.Namespace(folder=str(run), act="form", rec_id=None, stage=None, search=False))
    check("129: the command line reads the form and its values, `sift form` its fields under their sections and each "
          "record done or not, `show` a record's values and whether its form is done, and writes nothing",
          formed[1][0] == "Extract and appraise of 2031-06-01: 9 fields, 1 of 3 records included at full text done."
          and any(l.startswith("  passages_shown: Marker passages (passages, on the form, Not reported offered, shown when "
                               "Overall is Good)") for l in formed[1])
          and "K1  done  Flying a box kite on the cliff" in formed[1] and "Benchmark papers: K6, K7, K8." in formed[1]
          and "Form: done." in shown and 'Marker passages: p. 4: "The line sang." | p. 9-10: "We ran with it."' in shown
          and "Year taken: 2019" in shown and formed[0]["records"][0]["values"]["markers_shown"] == "Narrative; Depth"
          and (sift.csv_path(run).read_bytes(), sift.log_path(run).read_bytes()) == snap, "\n".join(formed[1][:6]))
    tool = next(t for t in sift_mcp.SIFT_TOOLS if t["name"] == "sift_form")
    check("129: MCP reads the form with sift_form, a tool that only reads, and no tool writes a field or a value",
          tool["command"] == ("sift", "form") and tool["annotations"]["readOnlyHint"] is True
          and not any("field" in t["inputSchema"]["properties"] or "value" in t["inputSchema"]["properties"]
                      for t in sift_mcp.SIFT_TOOLS)
          and "form" in sift_cli.SIFT_ACTS and (sift.csv_path(run).read_bytes(), sift.log_path(run).read_bytes()) == snap,
          str(tool["annotations"]))

    # ── H. carried into a later run that keeps the decisions
    kept_clock, kept_env, kept_runner = ss.CLOCK, os.environ.pop(ss.STUB_ENV, None), ss.RUNNER
    ss.CLOCK = lambda: dt.date(2031, 6, 3)
    ss.RUNNER = lambda argv, **_: ss.Done(44, "\n")
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), follow_stub({"phase": 1}))
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    stub = f"http://127.0.0.1:{httpd.server_address[1]}"
    ctx = lambda: ss.Context(base={s: stub + urllib_path(u) for s, u in ss.ENDPOINTS.items()}, pause=lambda s: None)
    try:
        later_review = base / "kite-search"
        later_review.mkdir()
        ss.save(later_review, {"databases": ["psycinfo"], "blocks": [{"name": "Kites", "terms": ["kite*"]}]})
        ss.register(later_review)
        d1, d2 = "2031-06-02", "2031-06-03"
        ris = lambda *recs: "".join(f"TY  - JOUR\nTI  - {t}\nPY  - {y}\nDO  - {d}\nAB  - Invented flyers and their kites.\nER  - \n\n"
                                    for t, y, d in recs).encode("utf-8")
        ss.take_export(later_review, "psycinfo", ris(("Flying a box kite", "2021", "10.5555/kite.11"),
                                                     ("Gusts on the hill", "2022", "10.5555/kite.12")), "p.ris", day=d1, ctx=ctx())
        ss.run(later_review, day=d1, ctx=ctx())
        f1 = later_review / "runs" / d1
        ids = {sift.load(f1).cell(r, "title"): r for r in sift.load(f1).ids}
        one = ids["Flying a box kite"]
        sift.decide(f1, one, "ta", "include")
        sift.decide(f1, one, "ft", "include")
        sift.form_field(f1, None, {"name": "Overall", "type": "choice", "options": ["Good", "Poor"], "section": "Appraisal"})
        sift.form_field(f1, None, {"name": "Extracts", "type": "passages", "section": "Appraisal"})
        sift.set_field(f1, one, "col_overall", "Good")
        sift.set_field(f1, one, "col_extracts", [{"page": "3", "text": "Up it went."}])
        before = sift.table_settings(f1)
        ss.take_export(later_review, "psycinfo", ris(("Flying a box kite", "2021", "10.5555/kite.11"),
                                                     ("Tails in the wind", "2023", "10.5555/kite.13")), "p.ris", day=d2, ctx=ctx())
        ss.run(later_review, day=d2, ctx=ctx(), follows=d1)
        f2 = later_review / "runs" / d2
        after = sift.table_settings(f2)
        sc2 = sift.load(f2)
        carried = {sc2.cell(r, "title"): r for r in sc2.ids}
        check("129: a later run that keeps the decisions carries the form, its sections and fields, and each value with "
              "its record, a carry line each, and the record stays included",
              after["own"] == before["own"] and after["sections"] == ["Appraisal"]
              and sc2.cell(carried["Flying a box kite"], "col_overall") == "Good"
              and json.loads(sc2.cell(carried["Flying a box kite"], "col_extracts")) == [{"page": "3", "text": "Up it went."}]
              and sift.form_round(f2)["ids"] == [carried["Flying a box kite"]]
              and any(e.get("act") == "carry" and e.get("field") == "col_extracts" for e in sift.read_lines(f2)), str(after["own"])[:200])
    finally:
        httpd.shutdown()
        ss.CLOCK, ss.RUNNER = kept_clock, kept_runner
        if kept_env is not None:
            os.environ[ss.STUB_ENV] = kept_env

    # the form's rules lifted from sift.js for node
    block = sift_src.split("/* ── Extract and appraise (13 October, later) ── */", 1)[-1].split("/* ── the plan's terms (13 October, later) ── */", 1)[0]
    rules = sift_src.split("/* ── the form's rules and the plan's terms, worked out with no page (13 October, later) ── */", 1)[-1].split(
        "/* every column the table can show", 1)[0]
    if not node:
        skip("129: the form's rules in node", "node is not installed")
    else:
        lead = app_src[app_src.index("const esc = "):app_src.index("// a line from the server with a command in backticks")]
        script = base / "form-129.js"
        script.write_text("\n".join([lead, whole(app_src, "gripHtml"), "const SF_BLANK_WORDS = { participants: 'Unknown' };",
                                     "const tbTicks = (f, k) => (Array.isArray((f || {})[k]) ? f[k] : []);", rules, block, MINI_PAGE_JS, r"""
const own = [
  { key: 'col_a', name: 'Overall', type: 'choice', options: ['Good', 'Fair'], where: 'form', not_reported: true, when: null, section: 'Appraisal', from: '' },
  { key: 'col_b', name: 'Markers', type: 'multi', options: ['One', 'Two'], where: 'form', not_reported: true, when: { key: 'col_a', values: ['Good'] }, section: 'Appraisal', from: '' },
  { key: 'col_c', name: 'Year', type: 'number', options: [], where: 'both', not_reported: false, when: null, section: '', from: 'year' },
  { key: 'col_d', name: 'Table only', type: 'text', options: [], where: 'table', not_reported: false, when: null, section: '', from: '' },
  { key: 'col_e', name: 'Passages', type: 'passages', options: [], where: 'form', not_reported: true, when: { key: 'col_b', values: ['Two'] }, section: 'Extraction', from: '' },
];
const SF = { table: { own, sections: ['Extraction', 'Appraisal'] }, filters: {}, form: true, roundIds: ['R1', 'R2', 'R3'],
  formInc: new Set(['R1', 'R2']), formBench: new Set(['R3']), psgAdd: {} };
const rec = (own2, sift) => ({ rec_id: 'R1', fields: { own: own2 }, form: { sift: sift || {} } });
const out = {};
out.order = sfFormFields().map((c) => c.key);
const r1 = rec({ col_a: 'Good', col_b: 'Two', col_e: '[{"page":"3","text":"Up it went."}]' }, { col_c: '2021' });
out.shown1 = [...sfShownKeys(r1, sfFormFields())];
out.done1 = sfFormDone(r1);
const r2 = rec({ col_a: 'Fair', col_b: 'Two' }, { col_c: '2021' });
out.shown2 = [...sfShownKeys(r2, sfFormFields())];
out.done2 = sfFormDone(r2);
out.done3 = sfFormDone(rec({ col_a: 'not reported' }, { col_c: '2021' }));
out.done4 = sfFormDone(rec({ col_a: 'not reported' }, {}));
out.value = sfFieldValue(r1, own[2]);
out.mine = sfFieldValue(rec({ col_c: '1999' }, { col_c: '2021' }), own[2]);
out.words = [sfFormWords(own[1], 'One; Two'), sfFormWords(own[4], r1.fields.own.col_e), sfFormWords(own[0], 'not reported')];
out.base = sfBaseIds();
SF.filters.bench = ['yes'];
out.bench = sfBaseIds();
const row = parse(sfFormRowHtml(own[1], r1, 'x-1'));
out.ticks = row.querySelectorAll('input').map((i) => [i.attrs.type, !!i.closest('label')]);
const prow = parse(sfFormRowHtml(own[4], r1, 'x-2'));
out.psg = [prow.querySelectorAll('textarea').length, prow.querySelectorAll('button').map((b) => b.attrs['data-act'])];
console.log(JSON.stringify(out));
"""]), encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        check("129: in node, the form's order puts the fields in no section first and then each section in his order, the "
              "table's own left out",
              out.get("order") == ["col_c", "col_e", "col_a", "col_b"], (ran.stderr or json.dumps(out))[:400])
        check("129: in node, a field shown for another's values follows it down a chain, a hidden field counting for nothing "
              "in done, and Not reported holding a value",
              out.get("shown1") == ["col_c", "col_e", "col_a", "col_b"] and out.get("done1") is True
              and out.get("shown2") == ["col_c", "col_a"] and out.get("done2") is True and out.get("done3") is True
              and out.get("done4") is False,
              json.dumps(out)[:300])
        check("129: in node, a field that starts from a Sift column shows Sift's value until his own, and each kind of value "
              "in the table's words",
              out.get("value") == {"value": "2021", "sift": True} and out.get("mine") == {"value": "1999", "sift": False}
              and out.get("words") == ["One, Two", "1 passage", "Not reported"], json.dumps(out)[:300])
        check("129: in node, the stage lists the records included at full text, or with Benchmark papers ticked the "
              "benchmark papers", out.get("base") == ["R1", "R2"] and out.get("bench") == ["R3"], json.dumps(out)[:200])
        check("129: in node, every tick of the form sits in a label, a passage has its box, its page and Remove, then Add "
              "a passage",
              out.get("ticks") == [["checkbox", True], ["checkbox", True], ["checkbox", True]]
              and out.get("psg") == [1, ["psg-remove", "psg-add"]], json.dumps(out)[:300])

    # ── J. apart from the form: the plan's terms as filters of Screening
    blocks = sift.blocks_view(sift.terms_of_plan(run))
    sc = sift.load(run)
    terms = {rec: sift.record_terms(sc, rec, sift.terms_of_plan(run)) for rec in sc.ids}
    check("129: each block of the plan with terms is a filter group named Block and its place with its name, its terms as "
          "he wrote them, a block with none left out",
          blocks == [{"key": "term:0", "label": "Block 1, Kites", "terms": ["kite*", '"box kite"', "TI(string W/2 line)", "spool"]},
                     {"key": "term:1", "label": "Block 2, Wind", "terms": ["gust*", "breeze"]}], str(blocks))
    check("129: a term is found in the title, the abstract and the keywords the run's raw files hold, case and accents "
          "folded, a phrase as a phrase, an asterisk as truncation, a bare word whole, and a term Sift cannot read by its "
          "plain words",
          terms["K1"] == {"term:0": ["kite*", '"box kite"', "TI(string W/2 line)"], "term:1": []}
          and terms["K2"] == {"term:0": [], "term:1": ["gust*", "breeze"]}
          and terms["K3"]["term:0"] == ["kite*"] and terms["K4"]["term:0"] == ["spool"] and terms["K5"] == {"term:0": [], "term:1": []},
          str(terms))
    patterns = [[p.pattern for p in sift.term_rule(t)] for t in ("spool", "TITLE-ABS-KEY(reel* W/3 line) AND sky")]
    check("129: a bare word is whole, so spool never finds spools, and NEAR and a field's name go before the plain words",
          not sift.term_rule("spool")[0].search("three spools") and patterns[1] == [r"(?<!\w)reel\w*(?!\w)", r"(?<!\w)line(?!\w)", r"(?<!\w)sky(?!\w)"],
          str(patterns))
    ss.save(review, {"databases": ["psycinfo"], "blocks": [{"name": "Kites", "terms": ["kite*", "festival*"]}]})
    after_edit = sift.screen(run)
    check("129: the terms follow an edit of the plan the next time the screening is read, and nothing is written to the CSV",
          # updated 14 October (133): each block with its lines, none here, and 14 October, later (137): a
          # record no database's fields explain stands under a field Sift cannot name, a line of its own
          after_edit["blocks"] == [{"key": "term:0", "label": "Block 1, Kites", "terms": ["kite*", "festival*"],
                                    "why": [{"value": "|none", "label": sift.MATCH_LINES["none"]}]}]
          and next(r for r in after_edit["records"] if r["rec_id"] == "K5")["terms"] == {"term:0": ["festival*"]}
          and not any(h.startswith("term") for h in sift.load(run).header), str(after_edit["blocks"]))
    kept_view = sift.save_view(run, filters={"term:0": ["kite*"], "term:9": ["x"], "bench": ["yes"], "nonsense": ["x"]},
                               find={"term:0": "kit"})
    check("129: a term group's ticks and find box are kept in sift.json as the other filters are, Benchmark papers too",
          kept_view["filters"] == {"term:0": ["kite*"], "term:9": ["x"], "bench": ["yes"]} and kept_view["find"] == {"term:0": "kit"},
          str(kept_view["filters"]))
    # updated 14 October, later (137): More than one after the terms and the block's lines last, None of its
    # terms now a field Sift cannot name among the lines, which the server words
    check("129: the command line's record names the terms of each block it holds",
          "Block 2, Wind: breeze" not in "\n".join(shown) and any(l.startswith("Block 1, Kites: ") for l in
              sift_cli.cmd_sift(argparse.Namespace(folder=str(run), act="show", rec_id="K5", stage="ta", search=False))[1]))

