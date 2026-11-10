from __future__ import annotations

import csv
import inspect
import io
import json
import os
import re
import shutil

from workbook import WorkbookError

from . import support
from .support import check, sift_words_js, skip, urllib_path


def polish_stub(state: dict):
    """A stand-in for Europe PMC and OpenAlex, for area 116 and a smoke run, on an invented topic,
    community orchards. `state["phase"]` 1 answers as an earlier run's search, 2 as a later one's,
    OpenAlex by DOI answers with each work's authors and abstract as the phase knows them, and every
    query asked is kept under `asked`."""
    import http.server
    import urllib.parse as up

    def inverted(text):
        out = {}
        for i, w in enumerate(text.split()):
            out.setdefault(w, []).append(i)
        return out

    def epmc(title, year, author, doi="", abstract="Volunteers spoke of the orchard through the year."):
        return {"id": title[:6], "source": "MED", "title": title, "authorString": author, "pubYear": year, "doi": doi,
                "abstractText": abstract, "journalInfo": {"journal": {"title": "Invented Orchard Review"}},
                "pubTypeList": {"pubType": ["Journal Article"]}}

    def work(doi, names, abstract=""):
        return {"id": "https://openalex.org/W" + doi[-2:], "doi": "https://doi.org/" + doi,
                "authorships": [{"author": {"display_name": n}} for n in names],
                "abstract_inverted_index": inverted(abstract) if abstract else None}

    found = {
        1: [epmc("Orchards and neighbours", "2019", "Lark P.", "10.5555/orch.11"),
            epmc("Cider and company", "2020", "Finch R.", "10.5555/orch.12"),
            epmc("Windfalls", "2021", "Tern S.")],
        2: [epmc("Orchards and neighbours", "2019", "Lark P.", "10.5555/orch.11"),
            epmc("Ladders at harvest", "2023", "Heron I.", "10.5555/orch.14")],
    }
    known = {
        1: {"10.5555/orch.12": work("10.5555/orch.12", ["Rae Finch", "Sol Plover"])},
        2: {"10.5555/orch.11": work("10.5555/orch.11", ["Pat Lark", "Ida Heron"]),
            "10.5555/orch.14": work("10.5555/orch.14", ["Ida Heron", "", "Pat Lark", "Rae Finch"])},
        3: {"10.5555/orch.1": work("10.5555/orch.1", ["Ann Pippin", "Ben Russet", "Cy Codlin"]),
            "10.5555/orch.3": work("10.5555/orch.3", ["Cy Codlin", "Di Bramley", "Ed Quince", "Fay Medlar"],
                                   "Growers kept a diary of the blossom."),
            "10.5555/orch.4": work("10.5555/orch.4", ["Gus Damson", "", "Hal Greengage"]),
            "10.5555/orch.5": work("10.5555/orch.5", ["Eve Quince"])},
    }

    class Stub(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, body):
            data = json.dumps(body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            url = up.urlparse(self.path)
            q = {k: v[0] for k, v in up.parse_qs(url.query).items()}
            state.setdefault("asked", []).append((url.path, q))
            phase = state.get("phase", 1)
            if url.path.endswith("/europepmc/webservices/rest/search"):
                rows = found.get(phase, [])
                return self.send({"hitCount": len(rows), "nextCursorMark": "*", "resultList": {"result": rows}})
            if url.path.endswith("/works") and q.get("filter", "").startswith("doi:"):
                rows = [known.get(phase, {})[d] for d in q["filter"][4:].split("|") if d in known.get(phase, {})]
                return self.send({"meta": {"count": len(rows)}, "results": rows})
            return self.send({"error": "no such path"})

    return Stub


def test_sift_polish(scratch):
    print("\n116. Sift's table finished, 12 October: the year's chart a bar for each five years and the participants' a "
          "bar for each five to 50 and wider past it, the filters' toggle saying how many are on while the sidebar is "
          "shut, the filters kept for each screening in sift.json, and the authors of a record that names one or none "
          "filled from OpenAlex by its DOI")
    import http.server
    import subprocess
    import threading
    import server as server_mod
    import sift_routes
    import sift
    import sift_search as ss

    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    sjs = support.text("apps/sift/static/sift.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    node = shutil.which("node")

    # ── A. an invented screening on community orchards, six records, years 2013 to 2026, counts 3 to 1200
    base = scratch / "sift-polish"
    shutil.rmtree(base, ignore_errors=True)
    folder = base / "orchards"
    folder.mkdir(parents=True)
    head = ["rec_id", "title", "authors", "year", "journal", "doi", "pub_type", "sources", "abstract", "access"]
    rows = [
        ["Q1", "Planting the first rows", "Pippin, A.", "2013", "Invented Orchard Review", "10.5555/orch.1", "Journal Article",
         "Scopus", "Volunteers planted a row of trees.", "open"],
        ["Q2", "Grafting days", "Russet, B.", "2016", "Invented Orchard Review", "", "Journal Article", "Scopus; PsycInfo",
         "Growers met to graft.", "closed"],
        ["Q3", "Blossom and belonging", "Codlin, C.", "2019", "Invented Fruit", "", "Journal Article", "PsycInfo",
         "Neighbours waited for the blossom.", "open"],
        ["Q4", "Harvest suppers", "Bramley, D.", "2020", "Invented Fruit", "", "Thesis", "Scopus",
         "A supper after the harvest.", "closed"],
        ["Q5", "Pruning in winter", "Quince, E.", "2024", "Invented Orchard Review", "", "Journal Article", "Web of Science",
         "A survey of winter pruners.", "open"],
        ["Q6", "An orchard for the ward", "Medlar, F.", "2026", "Invented Fruit", "", "Journal Article", "PsycInfo",
         "Patients tended a small orchard.", "closed"],
    ]
    with open(folder / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(head)
        w.writerows(rows)
    (folder / sift.REASONS_NAME).write_text("stage,code,meaning\nta,E1,Not about orchards\nta,E2,No accounts of experience\n",
                                            encoding="utf-8")
    sift.decide(folder, "Q2", "ta", "exclude", "E1")
    for rec, n in (("Q1", "3"), ("Q2", "8"), ("Q3", "30"), ("Q4", "75"), ("Q5", "1200")):
        sift.set_field(folder, rec, "participants", n)
    sift.set_field(folder, "Q1", "rating", "4")
    sift.column(folder, "add", name="Method", kind="choice", options="IPA\nThematic")
    sift.set_field(folder, "Q1", "col_method", "IPA")
    view = sift.screen(folder)

    # ── B. the charts, the toggle and the filters read back, in node, on the records as the server gives them
    block = sjs.split("/* ── the table's rows: its columns, sort and filter, worked out with no page ── */", 1)[-1].split(
        "/* ── the table, drawn ── */", 1)[0]
    block = support.table_js() + "\n" + block
    lead = app[app.index("const esc = "):app.index("// a line from the server with a command in backticks")]
    drawn = [f"function {name}(" + fn(sjs, name) + "\n}" for name in ("sfRangeEnds", "sfBarsHtml", "sfRangeHtml",
                                                                        "sfFacetsMark")]
    if node and "function sfBarSpans(" in block and "function sfKeptRead(" in block:
        probe = scratch / "sift-polish.js"
        probe.write_text("\n".join([block, lead, sift_words_js(sjs),
                                    "const SF = { filters: {}, facetsMore: new Set(), facetsFind: {} };",
                                    "const els = {};",
                                    "const $ = (id) => (els[id] = els[id] || { hidden: false, textContent: '', title: '', dataset: {},"
                                    " attrs: {}, setAttribute(k, v) { this.attrs[k] = v; } });",
                                    "function sfMeaning(code) { return ''; }"] + drawn)
                         + "\nconst data = " + json.dumps({"records": view["records"], "table": view["table"],
                                                           "codes": view["reasons"]["ta"]}) + ";\n" + r"""
const rows = data.records;
const cols = [SF_ID, ...sfColumns(data.table)];
const g0 = sfGroups(rows, rows, cols, 'ta', data.codes, {});
const by = (key) => g0.find((g) => g.key === key);
const bars = sfRangeBars(rows, g0, {}, 'ta');
const plain = (o) => JSON.parse(JSON.stringify(o));
const words = (list) => list.map((b) => [b.from, b.to, b.label]);
const mark = () => ({ title: $('sf-facets-toggle').title, label: $('sf-facets-toggle').attrs['aria-label'],
  count: $('sf-facets-toggle').dataset.count, word: $('sf-facets-word').textContent, clear: $('sf-facets-clear').hidden });
const out = {};
out.yearBars = plain(bars.year);
out.countBars = plain(bars.participants);
out.ratingBars = plain(bars.rating);
out.wideYears = sfBarSpans('year', 1800, 2026);
out.fives = words(sfBarSpans('participants', 3, 48));
out.wide = words(sfBarSpans('participants', 2, 1500));
out.mid = words(sfBarSpans('participants', 60, 180));
out.zero = words(sfBarSpans('participants', 0, 4));
out.stars = words(sfBarSpans('rating', 0, 5));
SF.filters = { participants: { from: 6, to: 50, none: false } };
const ranged = sfRangeBars(rows, g0, SF.filters, 'ta');
out.countHtml = sfRangeHtml(by('participants'), tbFacetCounts(rows, g0, SF.filters, sfRead('ta')).participants, 2, ranged.participants);
$('sf-facets').hidden = true;
SF.filters = {};
sfFacetsMark();
out.markNone = mark();
SF.filters = { year: { from: 2016, to: null, none: false }, decision: ['undecided', 'maybe'] };
sfFacetsMark();
out.markTwo = mark();
$('sf-facets').hidden = false;
sfFacetsMark();
out.markOpen = mark();
const kept = { found: ['scopus', 'embase'], decision: ['exclude:E1', 'exclude:E9'], col_method: ['IPA', 'Mixed'],
  'csv:access': ['open', 'shared'], 'csv:gone': ['x'], year: { from: 2016, to: 2024, none: true },
  participants: { from: 10, to: null, none: false }, journal: ['invented orchard review', 'invented cider'] };
out.keptRead = plain(sfKeptRead(kept, g0));
out.keptRows = tbFilterRows(rows.map((r) => r.rec_id), new Map(rows.map((r) => [r.rec_id, r])), out.keptRead, cols, sfRead('ta'));
out.findRead = sfFindRead({ journal: 'orchard', 'csv:gone': 'x', year: '2019', found: '  ' }, g0);
out.jsonSame = sfKeptJson({ b: ['1'], a: { from: 1, to: null, none: false } }, { j: ' two   words ' })
  === sfKeptJson({ a: { from: 1, to: null, none: false }, b: ['1'] }, { j: 'two words', k: '' });
out.json = sfKeptJson({ year: { from: 2016, to: null, none: false }, decision: ['undecided'] }, { journal: '  orchard  review ', found: '' });
console.log(JSON.stringify(out));
""", encoding="utf-8")
        ran = subprocess.run([node, str(probe)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        why = (ran.stderr or ran.stdout)[:400]
        check("116: in node, the year's chart has a bar for each five years from a year that ends in 0 or 5, the first and the "
              "last kept to the round's lowest and highest, each with its five years in words, every record in one bar",
              out.get("yearBars") == [{"from": 2013, "to": 2014, "label": "2010–2014", "n": 1},
                                      {"from": 2015, "to": 2019, "label": "2015–2019", "n": 2},
                                      {"from": 2020, "to": 2024, "label": "2020–2024", "n": 2},
                                      {"from": 2025, "to": 2026, "label": "2025–2029", "n": 1}], why or json.dumps(out.get("yearBars")))
        wide_years = out.get("wideYears") or []
        check("116: in node, a span of years that five would make more than 30 bars of takes ten years a bar, still from a "
              "year that ends in 0",
              len(wide_years) == 23 and wide_years[0]["label"] == "1800–1809" and wide_years[-1]["label"] == "2020–2029"
              and all(int(b["label"][:4]) % 10 == 0 for b in wide_years), str(wide_years[:2]))
        check("116: in node, the participants' chart has a bar for each five up to 50, 1 to 5, 6 to 10 and on to 46 to 50, "
              "each kept to the lowest and the highest",
              out.get("fives") == [[3, 5, "1–5"], [6, 10, "6–10"], [11, 15, "11–15"], [16, 20, "16–20"], [21, 25, "21–25"],
                                   [26, 30, "26–30"], [31, 35, "31–35"], [36, 40, "36–40"], [41, 45, "41–45"], [46, 48, "46–50"]]
              and out.get("zero") == [[0, 4, "0–5"]], str(out.get("fives")))
        check("116: in node, past 50 the participants' bars are wider, 51 to 100, 101 to 200, 201 to 500, 501 to 1000 and "
              "1001 and over, and a round that starts past 50 has only those it reaches",
              [w[2] for w in out.get("wide") or []] == ["1–5", "6–10", "11–15", "16–20", "21–25", "26–30", "31–35", "36–40",
                                                        "41–45", "46–50", "51–100", "101–200", "201–500", "501–1000",
                                                        "1001 and over"]
              and (out.get("wide") or [[0]])[-1] == [1001, 1500, "1001 and over"]
              and out.get("mid") == [[60, 100, "51–100"], [101, 180, "101–200"]], str(out.get("wide")))
        check("116: in node, the participants' bars counted, 3, 8, 30, 75 and 1200 each in its own bar and the record with "
              "none in none",
              [(b["label"], b["n"]) for b in out.get("countBars") or [] if b["n"]]
              == [("1–5", 1), ("6–10", 1), ("26–30", 1), ("51–100", 1), ("1001 and over", 1)]
              and sum(b["n"] for b in out.get("countBars") or []) == 5 and len(out.get("countBars") or []) == 15,
              str([(b["label"], b["n"]) for b in out.get("countBars") or []]))
        check("116, updated 12 October (121): in node, the rating keeps a bar for each star, one to five, a record not rated "
              "in none of them",
              out.get("stars") == [[i, i, str(i)] for i in range(6)]
              and [(b["from"], b["n"]) for b in out.get("ratingBars") or []] == [(1, 0), (2, 0), (3, 0), (4, 1), (5, 0)],
              str(out.get("ratingBars")))
        count_html = out.get("countHtml", "")
        check("116, updated 12 October (117, 122): the participants' boxes still take any whole number from the lowest to "
              "the highest, its handles stand on a track laid out by its bars, each at a bar's edge, and a bar whose whole "
              "run is in range in the accent, its run in words with its count of records for the tip",
              '<input type="range" class="sf-handle sf-from" data-end="from" min="0" max="15" step="any" value="1" '
              'aria-valuetext="6"' in count_html
              and '<input type="range" class="sf-handle sf-to" data-end="to" min="0" max="15" step="any" value="10" '
              'aria-valuetext="50"' in count_html and 'style="--lo: 0.0667; --hi: 0.6667"' in count_html
              and '<input type="number" class="sf-rnum" data-end="to" min="3" max="1200" step="1" value="50"' in count_html
              and re.findall(r'<span class="sf-bar( in)?" data-from="(\d+)"', count_html)[:3] == [("", "3"), (" in", "6"), (" in", "11")]
              and 'class="sf-bar" data-from="51"' in count_html and 'data-tip="1001 and over: 1 record"' in count_html
              and 'data-tip="6 to 10: 1 record"' in count_html, count_html[:400])
        check("116, updated 12 October (121): in node, the toggle says Filters while no filter is on, and Filters (2) in its "
              "word, its name and on hover while two groups are set, the sidebar open or shut, Clear all beside it then",
              out.get("markNone") == {"title": "Filters", "label": "Filters", "count": "false", "word": "Filters", "clear": True}
              and out.get("markTwo") == {"title": "Filters (2)", "label": "Filters (2)", "count": "true", "word": "Filters (2)",
                                         "clear": False}
              and out.get("markOpen") == out.get("markTwo"),
              why or json.dumps(out.get("markTwo")))
        check("116: in node, the filters sift.json keeps are read back as a screening opens, a database, a reason, a choice "
              "and a value no record carries let go with a column gone, the sliders as they were",
              out.get("keptRead") == {"found": ["scopus"], "year": {"from": 2016, "to": 2024, "none": True},
                                      "participants": {"from": 10, "to": None, "none": False}, "decision": ["exclude:E1"],
                                      "journal": ["invented orchard review"], "csv:access": ["open"], "col_method": ["IPA"]}
              and out.get("keptRows") == [], json.dumps(out.get("keptRead")))
        check("116: in node, the find boxes' words are read back for a group of ticks the screening has, and the words kept "
              "are one line whatever order the filters were set in",
              out.get("findRead") == {"journal": "orchard"} and out.get("jsonSame") is True
              and json.loads(out.get("json") or "{}") == {"filters": {"decision": ["undecided"], "year": {"from": 2016, "to": None, "none": False}},
                                                         "find": {"journal": "orchard review"}}, str(out.get("findRead")))
    else:
        skip("116: the charts, the toggle and the filters read back in node", "no node on this machine")

    # ── C. the filters kept in sift.json beside the table's columns, through sift.py and the server's route
    before = sift.table_settings(folder)
    saved = sift.save_view(folder, filters={"year": {"from": 2016, "to": None, "none": False}, "decision": ["undecided", "undecided"],
                                            "csv:gone": ["x"], "title": "words", "rating": ["4"], "found": {"from": 1},
                                            "col_method": ["IPA"], "csv:access": []},
                           find={"journal": "  invented   orchard ", "csv:gone": "x", "year": "2019", "found": ""})
    held = json.loads((folder / sift.SETTINGS_NAME).read_text(encoding="utf-8"))["table"]
    check("116: sift.json keeps the filters and the find boxes' words under table beside its columns, each on a column the "
          "table has and in its shape, a slider's ends or a list of ticks each once, the words on one line, and the rest let go",
          saved["filters"] == {"year": {"from": 2016, "to": None, "none": False}, "decision": ["undecided"], "col_method": ["IPA"]}
          and saved["find"] == {"journal": "invented orchard"} and held["filters"] == saved["filters"] and held["find"] == saved["find"]
          and saved["columns"] == before["columns"] and before["filters"] == {} and before["find"] == {}, json.dumps(held)[:300])
    cols_saved = sift.save_view(folder, columns=[{"key": "title", "shown": True}])
    read_back = sift.table_settings(folder)
    check("116: a change of columns keeps the filters, and the table's settings read them back as they were kept",
          cols_saved["filters"] == saved["filters"] and read_back["filters"] == saved["filters"]
          and read_back["find"] == saved["find"] and read_back["columns"][0]["key"] == "title", json.dumps(read_back["filters"]))
    sift.column(folder, "change", key="col_method", options="IPA\nThematic\nMixed")
    kept_choices = sift.table_settings(folder)["filters"].get("col_method")
    sift.column(folder, "change", key="col_method", name="Approach")
    renamed = sift.table_settings(folder)["filters"]
    sift.column(folder, "remove", key="col_approach")
    removed = sift.table_settings(folder)["filters"]
    removed_held = json.loads((folder / sift.SETTINGS_NAME).read_text(encoding="utf-8"))["table"]["filters"]
    check("116: a filter on his column stays when its choices change, follows it when it is renamed, and goes with it when "
          "it is removed, sift.json and all",
          kept_choices == ["IPA"] and renamed.get("col_approach") == ["IPA"] and "col_method" not in renamed
          and "col_approach" not in removed and "col_approach" not in removed_held and removed.get("decision") == ["undecided"],
          json.dumps(renamed))
    refused = []
    for bad in ({"filters": ["x"]}, {"find": "words"}):
        try:
            sift.save_view(folder, **bad)
        except sift.SiftError as exc:
            refused.append(str(exc))
    sift.save_view(folder, filters={}, find={})
    cleared = json.loads((folder / sift.SETTINGS_NAME).read_text(encoding="utf-8"))["table"]
    check("116: Clear all clears what is kept, sift.json holding no filters and no words, and a filter of another shape "
          "is refused in one line",
          "filters" not in cleared and "find" not in cleared and sift.table_settings(folder)["filters"] == {}
          and "columns" in cleared and refused == ["The filters are a record of each column's filter.",
                                                   "The find boxes' words are a record of each column's words."], str(refused))
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
        routed = sift_routes.api_sift({"op": "view", "folder": str(folder), "filters": {"csv:access": ["open"]},
                                      "find": {"journal": "fruit"}})
        opened = sift_routes.api_sift({"op": "read", "folder": str(folder)})
    except WorkbookError as exc:
        routed, opened = {"error": str(exc)}, {}
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept_state
    check("116: the server's view route keeps the filters and the words, and the screening read again carries them for the "
          "page to put back",
          (routed.get("table") or {}).get("filters") == {"csv:access": ["open"]}
          and ((opened.get("table") or {}).get("find") or {}) == {"journal": "fruit"}
          and (opened.get("table") or {}).get("filters") == {"csv:access": ["open"]}, str(routed)[:300])
    sift.save_view(folder, filters={}, find={})

    # ── D. the page: the toggle's count, the filters kept as they change, read as a screening opens, and kept as he leaves
    open_fn, keep_fn = fn(sjs, "siftOpen"), fn(sjs, "sfFiltersKeep")
    check("116: a screening opens on the filters and words sift.json keeps for it, read over every record, and each change "
          "is kept through the server's view route, a tick, a slider, a Clear, a round and a column at once, a word typed a "
          "moment after the last letter or as he leaves, and no request of its own beside the app's",
          "SF.filters = sfKeptRead(table.filters, groups);" in open_fn and "SF.facetsFind = sfFindRead(table.find, groups);" in open_fn
          and "sfGroups(SF.records, SF.records, sfAllCols(), SF.stage, sfCodes(), {})" in open_fn
          and "SF.kept = sfKeptJson(table.filters, table.find);" in open_fn
          and all("sfFiltersKeep();" in fn(sjs, f) for f in ("sfRefilter", "sfRound", "sfColumn"))
          and "sfFiltersKeep(false);" in fn(sjs, "sfFind") and "function sfFiltersKeep(now = true) {" in sjs
          and "if (held === SF.kept) return;" in keep_fn and "SF.keepTimer = setTimeout(send, SF_KEEP_WAIT);" in keep_fn
          and "sfQueue(() => api('/api/sift', Object.assign({ op: 'view', folder }, JSON.parse(held))));" in keep_fn
          and "const SF_KEEP_WAIT = 400;" in sjs and "if (SF.keepTimer) sfFiltersKeep();" in fn(sjs, "sfLeave")
          and "fetch(" not in sjs and "pagehide" not in sjs
          and 'body.get("filters"), body.get("find")' in inspect.getsource(sift_routes.api_sift))
    check("116: Clear all empties every find box with the filters, and shows while either holds anything",
          "SF.filters = {};\n    SF.facetsFind = {};" in fn(sjs, "sfClear")
          and "Object.values(SF.facetsFind || {}).some((w) => String(w).trim())" in fn(sjs, "sfFacetsMark"))

    # ── E. the authors of a record that names one or none filled from OpenAlex by its DOI, against a stub on loopback
    state = {"phase": 3}
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), polish_stub(state))
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    stub = f"http://127.0.0.1:{httpd.server_address[1]}"
    ctx = lambda: ss.Context(base={s: stub + urllib_path(u) for s, u in ss.ENDPOINTS.items()}, pause=lambda s: None)
    kept_runner, kept_env = ss.RUNNER, os.environ.pop(ss.STUB_ENV, None)

    def no_keys(argv, **_):
        return subprocess.CompletedProcess(argv, 44, "", "")

    ss.RUNNER = no_keys
    try:
        rec = lambda doi, authors, abstract="Kept as it was.": {"title": "T", "authors": authors, "year": "2020", "journal": "",
                                                               "doi": doi, "abstract": abstract, "pub_type": "", "url": "",
                                                               "sources": ["Scopus"], "abstract_from": "Scopus" if abstract else ""}
        merged = [rec("10.5555/orch.1", "Pippin A."), rec("", "Russet B."), rec("10.5555/orch.3", "Codlin, C.; Bramley, D.", ""),
                  rec("10.5555/orch.4", ""), rec("10.5555/orch.5", "Quince E."), rec("10.5555/orch.6", "Medlar F."),
                  rec("10.5555/orch.2", "Damson G.; Greengage H.")]
        state["asked"] = []
        counts = ss.fill_from_openalex(ctx(), merged)
        # updated 13 October (128): OpenAlex's requests alone, Crossref's going to the stub under a path of their own
        asks = [q for p, q in state["asked"] if p.endswith("/works") and "api.crossref.org" not in p]
        check("116: a record with a DOI that names one author, or none, takes OpenAlex's list by that DOI when it names more, "
              "joined as OpenAlex's own records join them, a name it leaves empty passed over",
              merged[0]["authors"] == "Ann Pippin; Ben Russet; Cy Codlin" and merged[3]["authors"] == "Gus Damson; Hal Greengage"
              and (counts["abstracts"], counts["authors"], counts["cited"]) == (1, 2, 0), str(counts) + str([m["authors"] for m in merged]))
        check("116: one with no DOI, one that names two, one OpenAlex names no more of and one OpenAlex does not know are left, "
              "the one that names two still given the abstract it lacked",
              merged[1]["authors"] == "Russet B." and merged[2]["authors"] == "Codlin, C.; Bramley, D."
              and merged[2]["abstract"] == "Growers kept a diary of the blossom." and merged[2]["abstract_from"] == "OpenAlex"
              and merged[4]["authors"] == "Quince E." and merged[5]["authors"] == "Medlar F."
              and merged[6]["authors"] == "Damson G.; Greengage H.", str([m["authors"] for m in merged]))
        check("116, updated 12 October (121): asked in the same batched way as the abstracts, one request for fifty DOIs, its "
              "select gaining authorships and the count of citations, so every record with a DOI is asked about, one with its "
              "abstract and two names among them",
              len(asks) == 1 and asks[0].get("select") == ss.FILL_FIELDS
              and ss.FILL_FIELDS.startswith("id,doi,abstract_inverted_index,authorships,cited_by_count")
              and asks[0].get("per-page") == "50"
              and asks[0].get("filter") == "doi:10.5555/orch.1|10.5555/orch.3|10.5555/orch.4|10.5555/orch.5|10.5555/orch.6|10.5555/orch.2",
              str(asks)[:300])

        # a run, then a later one that follows it, each said in words with what it filled
        review = base / "orchard review"
        review.mkdir()
        ss.save(review, {"databases": ["epmc"], "blocks": [{"name": "Orchards", "terms": ["orchard*"]}]})
        state["phase"] = 1
        first = ss.run(review, which="newest", day="2031-05-01", ctx=ctx())
        first_dir = review / "runs" / "2031-05-01"
        first_rows = {r["title"]: r for r in csv.DictReader(io.StringIO((first_dir / sift.CSV_NAME).read_text(encoding="utf-8"),
                                                                        newline=""))}
        first_meta = json.loads((first_dir / ss.RUN_FILE).read_text(encoding="utf-8"))
        check("116: in a run, after the merge, a record of one author with a DOI OpenAlex knows takes its list, run.json and "
              "the run's line say how many, and one with no DOI or one OpenAlex does not know keeps its own",
              first_rows["Cider and company"]["authors"] == "Rae Finch; Sol Plover"
              and first_rows["Orchards and neighbours"]["authors"] == "Lark P." and first_rows["Windfalls"]["authors"] == "Tern S."
              and first_meta["authors_filled"] == 1 and first["authors_filled"] == 1
              and any("3 records found, 3 after duplicates removed, 0 abstracts filled from OpenAlex, the authors of 1 record, "
                      "and the citation counts of 0 records." in line for line in ss.run_lines(first)), str(ss.run_lines(first))[:400])
        sift.decide(first_dir, first_rows["Orchards and neighbours"]["rec_id"], "ta", "include")
        state["phase"] = 2
        later = ss.run(review, which="newest", day="2031-05-02", ctx=ctx(), follows="2031-05-01")
        later_dir = review / "runs" / "2031-05-02"
        later_rows = {r["title"]: r for r in csv.DictReader(io.StringIO((later_dir / sift.CSV_NAME).read_text(encoding="utf-8"),
                                                                        newline=""))}
        later_asks = [q for p, q in state["asked"] if p.endswith("/works") and "api.crossref.org" not in p][-1:]
        check("116: a record of an earlier run carried into a later one is never changed or asked about, though OpenAlex now "
              "names more, and the later run's new record is filled and counted",
              later_rows["Orchards and neighbours"]["authors"] == "Lark P."
              and later_rows["Ladders at harvest"]["authors"] == "Ida Heron; Pat Lark; Rae Finch"
              and later_rows["Cider and company"]["authors"] == "Rae Finch; Sol Plover"
              and later["authors_filled"] == 1 and (later_asks or [{}])[0].get("filter") == "doi:10.5555/orch.14"
              and any("the authors of 1 record, and the citation counts of 0 records." in line for line in ss.run_lines(later)),
              str(later_rows)[:400])
        old = dict(later, authors_filled=None, cited_filled=None)
        check("116: a run made before authors were counted says its line as it always did",
              any(line.endswith("0 abstracts filled from OpenAlex.") for line in ss.run_lines(old))
              and not any("authors of" in line for line in ss.run_lines(old)), str(ss.run_lines(old)))
    finally:
        httpd.shutdown()
        httpd.server_close()
        ss.RUNNER = kept_runner
        if kept_env is not None:
            os.environ[ss.STUB_ENV] = kept_env
