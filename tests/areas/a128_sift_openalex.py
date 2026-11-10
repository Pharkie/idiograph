from __future__ import annotations

import csv
import io
import json
import os
import shutil

from . import support
from .support import check, refusal_of, sift_words_js, skip, urllib_path


def hive_stub(state: dict):
    """A stand-in OpenAlex and Crossref for area 128, on an invented topic, hive keepers: OpenAlex's
    /works by DOI and by search, and Crossref's works by DOI under /api.crossref.org/works, its notices
    and references among them, every query kept under `asked` with the host it came to. `refuse_select`
    makes Crossref refuse a `select` once, as a 400, and `crossref_down` makes it fail. The works OpenAlex
    knows carry their keywords and language since 14 October (133)."""
    import http.server
    import urllib.parse as up

    def who(aid, name, *codes, countries=()):
        return {"author": {"id": f"https://openalex.org/{aid}", "display_name": name},
                "institutions": [{"country_code": c} for c in codes], "countries": list(countries)}

    alex = {
        "10.5555/hive.1": {"cited_by_count": 12, "is_retracted": False, "open_access": {"is_oa": True, "oa_status": "green"},
                           "authorships": [who("A11", "Nell Ward", "GB"), who("A12", "Tunde Okafor", "NG", "GB"),
                                           who("A13", "Ada Pike", countries=("IE",))],
                           "referenced_works": ["https://openalex.org/W900", "https://openalex.org/W777"],
                           "keywords": [{"display_name": "Urban beekeeping", "score": 0.6}], "language": "en"},
        "10.5555/hive.2": {"cited_by_count": 0, "is_retracted": True, "open_access": {"is_oa": False, "oa_status": "closed"},
                           "authorships": [who("A11", "N. Ward", "GB")], "referenced_works": ["https://openalex.org/W777"],
                           "keywords": [{"display_name": "Hive health", "score": 0.5}], "language": "en"},
        "10.5555/hive.3": {"cited_by_count": 5, "is_retracted": False, "open_access": {"is_oa": True, "oa_status": "gold"},
                           "authorships": [who("A20", "Bo Lund", "SE")], "referenced_works": [],
                           "keywords": [{"display_name": "Roof gardens", "score": 0.4}], "language": "sv"},
        "10.5555/hive.5": {"cited_by_count": 3, "is_retracted": False, "open_access": {"is_oa": True, "oa_status": "hybrid"},
                           "authorships": [who("A20", "Bo Lund", "SE")], "referenced_works": ["https://openalex.org/W777"],
                           "keywords": [{"display_name": "Swarming", "score": 0.4}], "language": "en"},
    }
    cross = {
        "10.5555/hive.1": {"updated-by": [{"type": "correction", "DOI": "10.5555/HIVE.1.FIX", "label": "Correction",
                                           "updated": {"date-parts": [[2030, 3, 4]]}}],
                           "reference": [{"key": "r1", "unstructured": "Hart, M. (2015). Keeping bees by the book: Theory, "
                                                                        "method and practice. Comb Press."},
                                         {"key": "r2", "DOI": "10.5555/other", "year": "2011"}]},
        "10.5555/hive.2": {"updated-by": [{"type": "retraction", "DOI": "10.5555/hive.2.ret", "updated": {"date-parts": [[2031, 1, 9]]}},
                                          {"type": "expression_of_concern", "DOI": "10.5555/hive.2.eoc",
                                           "updated": {"date-parts": [[2030, 11]]}},
                                          {"type": "new_version", "DOI": "10.5555/hive.2.v2"}]},
        "10.5555/hive.3": {"reference": [{"key": "r1", "volume-title": "Keeping Bees by the Book", "year": "2024"}]},
        "10.5555/hive.4": {"reference": [{"key": "r1", "DOI": "10.5555/KW.DOI", "year": "2019"}]},
        "10.5555/hive.5": {"reference": [{"key": "r1", "article-title": "Smoke and mirrors", "year": "2001"}]},
    }
    found = [{"id": "https://openalex.org/W777", "doi": "https://doi.org/10.5555/review.of.book", "display_name": "Keeping bees by the book",
              "publication_year": 2017, "cited_by_count": 4100, "authorships": [{"author": {"display_name": "Rex Reviewer"}}]},
             {"id": "https://openalex.org/W778", "doi": None, "display_name": "Keeping bees by the book: notes for teachers",
              "publication_year": 2018, "cited_by_count": 9,
              "authorships": [{"author": {"display_name": n}} for n in ("Ann One", "Ben Two", "Cy Three", "Di Four", "Ed Five")]}]

    class Stub(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, body, status=200):
            data = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            url = up.urlparse(self.path)
            q = {k: v[0] for k, v in up.parse_qs(url.query).items()}
            state.setdefault("asked", []).append((url.path, q, self.headers.get("Host", "")))
            if url.path == "/api.crossref.org/works":
                if state.get("crossref_down"):
                    return self.send({"status": "failed"}, 503)
                if state.get("refuse_select") and "select" in q:
                    state["refuse_select"] = False
                    return self.send({"status": "failed", "message": [{"message": "select is refused"}]}, 400)
                dois = [p[4:] for p in q.get("filter", "").split(",") if p.startswith("doi:")]
                return self.send({"status": "ok", "message": {"items": [dict({"DOI": d.upper()}, **cross[d]) for d in dois if d in cross]}})
            if q.get("search"):
                return self.send({"results": [w for w in found if "keeping bees" in q["search"].lower()], "meta": {"count": 2}})
            dois = q.get("filter", "")[4:].split("|") if q.get("filter", "").startswith("doi:") else []
            return self.send({"results": [dict({"id": "https://openalex.org/W" + d[-1], "doi": "https://doi.org/" + d}, **alex[d])
                                          for d in dois if d in alex], "meta": {"count": 0}})

    return Stub


def test_sift_openalex(scratch):
    print("\n128. Sift's own columns from OpenAlex and Crossref, 13 October: Retracted or corrected, Open access, Country, "
          "Study with Sift's suggestions and his links, Cites key works by Crossref's references and OpenAlex's, the "
          "PRISMA flow's studies and reports, and Fill from OpenAlex for a screening made before")
    import datetime as dt
    import http.server
    import threading
    import server as server_mod
    import sift_routes
    import sift
    import sift_search as ss
    import argparse
    import subprocess
    import cli as cli_mod
    import sift_cli

    app_src = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    sift_src = support.text("apps/sift/static/sift.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    node = shutil.which("node")
    base = scratch / "sift-openalex-128"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)

    state = {}
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), hive_stub(state))
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    stub = f"http://127.0.0.1:{httpd.server_address[1]}"
    ctx = lambda email="": ss.Context(base={s: stub + urllib_path(u) for s, u in ss.ENDPOINTS.items()}, pause=lambda s: None,
                                      email=email)
    kept_runner, kept_env, kept_clock = ss.RUNNER, os.environ.pop(ss.STUB_ENV, None), ss.CLOCK
    ss.RUNNER = lambda argv, **_: ss.Done(44, "\n")
    ss.CLOCK = lambda: dt.date(2031, 6, 1)
    kw_a = {"id": "W777", "doi": "", "title": "Keeping bees by the book", "year": "2016"}
    kw_b = {"id": "", "doi": "", "title": "Keeping bees by the book", "year": "2024"}
    kw_c = {"id": "", "doi": "10.5555/kw.doi", "title": "Smoke signals", "year": "2019"}

    def hives(folder: Path) -> Path:
        """An invented screening on hive keepers made before 13 October: five records with a DOI and one with none."""
        folder.mkdir(parents=True, exist_ok=True)
        with open(folder / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["rec_id", "title", "authors", "year", "journal", "doi", "sources", "abstract"])
            for i in range(1, 7):
                w.writerow([f"H{i}", f"Keeping hives {i}", "Ward, Nell" if i < 3 else "Lund, Bo", str(2020 + i), "Invented Apiary",
                            f"10.5555/hive.{i}" if i < 6 else "", "Index A", f"Keepers spoke of hive {i}."])
        return folder

    try:
        # ── A. the run's fill, OpenAlex and Crossref in the same pass, and the new columns of its CSV
        rec = lambda doi, authors="Ward, N.": {"title": "T", "authors": authors, "year": "2020", "journal": "", "doi": doi,
                                               "abstract": "Kept.", "pub_type": "", "url": "", "sources": ["Index A"],
                                               "abstract_from": "Index A"}
        merged = [rec("10.5555/hive.1"), rec("10.5555/hive.2"), rec("10.5555/hive.3"), rec("10.5555/hive.4"), rec("")]
        got = ss.fill_from_openalex(ctx("keeper@example.org"), merged)
        oa_asks = [q for p, q, _ in state["asked"] if p == "/works"]
        cr_asks = [q for p, q, _ in state["asked"] if p == "/api.crossref.org/works"]
        check("128: a run asks OpenAlex for its new fields in the same batched request as the abstracts, authors and Cited by, "
              "and Crossref once for the same DOIs, comma-parted, its updates and references alone, in the polite pool",
              len(oa_asks) == 1 and oa_asks[0]["select"] == ss.FILL_FIELDS
              # updated 14 October (133): the keywords and the language asked in the same request
              and ss.FILL_FIELDS == ("id,doi,abstract_inverted_index,authorships,cited_by_count,is_retracted,open_access,"
                                     "referenced_works,keywords,language")
              and oa_asks[0]["filter"] == "doi:10.5555/hive.1|10.5555/hive.2|10.5555/hive.3|10.5555/hive.4"
              and len(cr_asks) == 1 and cr_asks[0]["filter"] == "doi:10.5555/hive.1,doi:10.5555/hive.2,doi:10.5555/hive.3,doi:10.5555/hive.4"
              and cr_asks[0]["select"] == "DOI,updated-by,reference" and cr_asks[0]["mailto"] == "keeper@example.org"
              and cr_asks[0]["rows"] == "4" and got == {"abstracts": 0, "authors": 1, "cited": 3, "openalex": 3, "crossref": 4, "said": ""},
              str(got) + str(cr_asks)[:300])
        m1, m2, m3, m4, m5 = merged
        check("128: each column is filled from the stub's answer, open access by its kind, the countries of the authors' "
              "institutions each once and an author's own where no institution names one, the authors with their IDs",
              m1["open_access"] == "green" and m2["open_access"] == "closed" and m1["countries"] == "GB; NG; IE"
              and m1["openalex_authors"] == "Nell Ward (A11); Tunde Okafor (A12); Ada Pike (A13)" and m1["cited_by"] == "12"
              and m2["cited_by"] == "0" and m1["openalex_date"] == "2031-06-01" and m4.get("openalex_date") is None
              and m4["crossref_date"] == "2031-06-01" and "open_access" not in m5 and "retraction" not in m5,
              str({k: m1.get(k) for k in sift.FILLED}))
        check("128: Retracted or corrected takes OpenAlex's is_retracted and Crossref's updated-by, each kind once in order, "
              "each notice with its DOI and date, an update of another kind passed over, and none once asked with none",
              m1["retraction"] == "corrected" and m2["retraction"] == "retracted; expression of concern"
              and m3["retraction"] == "none" and m4["retraction"] == "none"
              and json.loads(m1["retraction_notices"]) == [{"kind": "corrected", "doi": "10.5555/hive.1.fix", "date": "2030-03-04", "from": "Crossref"}]
              and [n["kind"] for n in json.loads(m2["retraction_notices"])] == ["retracted", "expression of concern"]
              and json.loads(m2["retraction_notices"])[1]["date"] == "2030-11" and m3["retraction_notices"] == "",
              m2.get("retraction_notices", "")[:300])
        check("128: each record's references are kept apart for screening.references.json, Crossref's folded with each title "
              "and year, OpenAlex's by ID",
              m1["references"]["openalex"] == ["W900", "W777"]
              and ["", "2015", "hartm2015keepingbeesbythebooktheorymethodandpracticecombpress"] in m1["references"]["crossref"]
              and m3["references"]["crossref"] == [["", "2024", "keepingbeesbythebook"]] and m2["references"]["crossref"] == []
              and m4["references"] == {"crossref": [["10.5555/kw.doi", "2019"]]}, str(m1["references"])[:300])
        text = ss.screening_text(ss.ordered([dict(m) for m in merged]))
        head = next(csv.reader(io.StringIO(text)))
        check("128: a run's screening.csv carries Sift's own columns after every column a run wrote before them, Cited by "
              "where it was, the study empty until he links",
              head[9:12] == ["abstract", "cited_by", "cited_by_date"]
              # updated 14 October (133): the language after them, at the end
              and head[-9:] == ["retraction", "retraction_notices", "open_access", "countries", "openalex_authors",
                                "openalex_date", "crossref_date", "study", "language"], str(head))
        state["asked"] = []
        state["refuse_select"] = True
        again = ss.fill_from_openalex(ctx(), [rec("10.5555/hive.3")])
        cr_again = [q for p, q, _ in state["asked"] if p == "/api.crossref.org/works"]
        check("128: Crossref refusing the select is asked again whole, and with no email no mailto goes",
              len(cr_again) == 2 and "select" in cr_again[0] and "select" not in cr_again[1] and "mailto" not in cr_again[1]
              and again["crossref"] == 1, str(cr_again))
        state["crossref_down"] = True
        down = [rec("10.5555/hive.1")]
        said = ss.fill_from_openalex(ctx(), down)
        state["crossref_down"] = False
        check("128: Crossref not answering leaves its part Unknown while OpenAlex's stands, and says why",
              down[0]["open_access"] == "green" and "crossref_date" not in down[0] and down[0]["retraction"] == "none"
              and "503" in said["said"] and said["openalex"] == 1 and said["crossref"] == 0, str(said))
        check("128: Crossref's address goes with OpenAlex's, the real one for the real OpenAlex and a stub's own for a stub, "
              "so nothing is sent anywhere but the stub",
              ss.crossref_for(ss.ENDPOINTS["openalex"]) == "https://api.crossref.org/works"
              and ss.crossref_for(stub + "/works") == stub + "/api.crossref.org/works" and ctx().crossref == stub + "/api.crossref.org/works"
              and all(host == f"127.0.0.1:{httpd.server_address[1]}" for _, _, host in state["asked"]))

        # ── B. Fill from OpenAlex for a screening made before, and the key works
        review = base / "hive-review"
        review.mkdir()
        ss.new_plan(review, "Hive keepers", "How do keepers live with the hive?")
        ss.save(review, {"databases": ["psycinfo"], "blocks": [{"name": "Hives", "terms": ["hive*"]}]})
        ss.register(review)
        versions = len(ss.read_file(review)["versions"])
        kept = ss.save_key_works(review, [kw_a, dict(kw_b, doi="not a doi"), kw_c, dict(kw_a, title="Again"),
                                          {"id": "https://openalex.org/W5", "title": ""}, {"title": "", "doi": ""}])
        check("128: the key works are kept beside the plan's versions, never in one, so a registered plan stays as it is, "
              "each once by its ID, its DOI or its title and year, an ID from its address and a DOI that is not one let go",
              kept["key_works"] == [kw_a, kw_b, kw_c, {"id": "W5", "doi": "", "title": "", "year": ""}]
              and len(ss.read_file(review)["versions"]) == versions and kept["current"]["registered"]
              and ss.key_works(review) == kept["key_works"] and "key_works" not in json.dumps(ss.read_file(review)["versions"])
              and "Keeping bees" not in (review / ss.PLAN_MD).read_text(encoding="utf-8"), str(kept["key_works"]))
        ss.save_key_works(review, [kw_a, kw_b, kw_c])
        ss.save(review, {"databases": ["psycinfo"], "blocks": [{"name": "Hives", "terms": ["hive*", "apiar*"]}]})
        check("128: a later edit of the plan keeps the key works", ss.key_works(review) == [kw_a, kw_b, kw_c])
        run = hives(review / "runs" / "2031-03-01")
        sift.decide(run, "H1", "ta", "include", note="A note kept.")
        original = sift.load(run).record("H1")
        plan = ss.fill_plan(run)
        state["asked"] = []
        first = ss.fill_columns(run, 0, ctx())
        after = sift.load(run)
        refs = sift.references(run)
        check("128: Fill from OpenAlex goes through every record with a DOI, fifty a request, asking OpenAlex for Sift's own "
              "fields alone and Crossref for the same, and writes Cited by with them, every other cell kept",
              plan == {"ids": ["H1", "H2", "H3", "H4", "H5"], "of": 5, "records": 6, "missing": 5}
              and first == {"at": 5, "of": 5, "records": 6, "asked": 5, "filled": 5, "said": ""}
              and [q.get("select") for p, q, _ in state["asked"] if p == "/works"] == [ss.OWN_FIELDS]
              # updated 14 October (133): with the keywords and the language of a record that lacks them
              and ss.OWN_FIELDS == "id,doi,authorships,cited_by_count,is_retracted,open_access,referenced_works,keywords,language"
              and [after.cell(r, "cited_by") for r in ("H1", "H2", "H4", "H6")] == ["12", "0", "", ""]
              and after.cell("H2", "retraction") == "retracted; expression of concern" and after.cell("H4", "crossref_date") == "2031-06-01"
              and all(after.cell("H1", k) == v for k, v in original.items()) and sorted(refs) == ["H1", "H2", "H3", "H4", "H5"],
              str(first))
        state["asked"] = []
        second = ss.fill_columns(run, 0, ctx())
        check("128: pressed again it asks only for what is still missing, OpenAlex for the record it does not know, and "
              "Crossref for none",
              ss.fill_plan(run)["missing"] == 1 and second["asked"] == 1
              and [p for p, _, _ in state["asked"]] == ["/works"] and state["asked"][0][1]["filter"] == "doi:10.5555/hive.4",
              str(state["asked"]))
        view = {r["rec_id"]: r for r in sift.screen(run)["records"]}
        works = sift.screen(run)["key_works"]
        check("128: the record carries each column as the screen draws it, Unknown for a record never asked, the countries "
              "named in plain English",
              view["H1"]["notices"]["kinds"] == ["corrected"] and view["H2"]["notices"]["kinds"] == ["retracted", "expression of concern"]
              and view["H3"]["notices"]["kinds"] == [] and view["H6"]["notices"]["kinds"] is None
              and view["H1"]["oa"] == "green" and view["H6"]["oa"] == "" and view["H1"]["countries"] == ["United Kingdom", "Nigeria", "Ireland"]
              and view["H6"]["countries"] == [] and view["H1"]["notices"]["list"][0]["doi"] == "10.5555/hive.1.fix"
              and all(k not in [m[0] for m in view["H1"]["more"]] for k in sift.FILLED), str(view["H1"]["more"]))
        check("128: a record cites a key work by Crossref's references when Crossref holds any, its title in any of the "
              "fields and its year within one, so two editions of one title are told apart, else by OpenAlex's by its ID, "
              "and by DOI, Unknown with neither",
              view["H1"]["cites"] == ["W777"] and view["H2"]["cites"] == ["W777"]
              and view["H3"]["cites"] == ["title:keepingbeesbythebook|2024"] and view["H4"]["cites"] == ["doi:10.5555/kw.doi"]
              and view["H5"]["cites"] == [] and view["H6"]["cites"] is None
              and [k["label"] for k in works] == ["Keeping bees by the book (2016)", "Keeping bees by the book (2024)", "Smoke signals (2019)"],
              str({r: view[r]["cites"] for r in view}))
        check("128: the year's tolerance is one either way, a book cited by its online or reprint year, and no more",
              sift.YEAR_SLACK == 1 and sift.ref_cites(kw_a, ["", "2017", "keepingbeesbythebook"])
              and not sift.ref_cites(kw_a, ["", "2018", "keepingbeesbythebook"]) and not sift.ref_cites(kw_a, ["", "", "keepingbeesbythebook"])
              and all(f in ss.REF_TITLES for f in ("series-title", "volume-title", "article-title", "journal-title", "unstructured")))
        oa_only = {"openalex": ["W9", "W10"]}
        check("128: with OpenAlex's references alone, a key work kept with no OpenAlex ID makes a record that cites none of "
              "the others Unknown, never none cited, and a found one still counts",
              sift.cites_of(oa_only, [kw_a]) == [] and sift.cites_of(oa_only, [kw_a, kw_b]) is None
              and sift.cites_of({"openalex": ["W777"]}, [kw_a, kw_b]) == ["W777"]
              and sift.cites_of({"crossref": [["", "2024", "keepingbeesbythebook"]], "openalex": []}, [kw_a, kw_b])
              == ["title:keepingbeesbythebook|2024"])
        kw_s = {"id": "", "doi": "", "title": "Keeping bees by the book: Hives, honey and harm", "year": "2016"}
        kw_t = {"id": "", "doi": "", "title": "Bees: Hives and harm", "year": "2016"}
        check("128: a key work cited with its subtitle garbled or its main title misspelt by two letters still counts when "
              "the subtitle's first word follows the main title, and a work sharing the main title alone does not",
              sift.ref_cites(kw_s, ["", "2016", "keepingbeesbythebookhivesharmandhoney"])
              and sift.ref_cites(kw_s, ["", "2017", "keepingbeasbythebookhiveshoneyandharm"])
              and sift.ref_cites(kw_s, ["", "2016", "wardn2016keepingbeesbythebookhivesharm"])
              and not sift.ref_cites(kw_s, ["", "2016", "keepingbeesbythebook"])
              and not sift.ref_cites(kw_s, ["", "2016", "keepingbeesbythebookapracticalguide"])
              and not sift.ref_cites(kw_s, ["", "2016", "introductiontokeepingbeesbythebook"])
              and not sift.ref_cites(kw_s, ["", "2019", "keepingbeesbythebookhives"])
              and sift.ref_cites(kw_t, ["", "2016", "beeshivesandhoney"]) and not sift.ref_cites(kw_t, ["", "2016", "beashives"])
              and sift.title_forms(kw_s["title"]) == ("keepingbeesbythebookhiveshoneyandharm", "keepingbeesbythebookhives"))
        found = ss.find_works("Keeping bees by the book", ctx())
        by_doi = ss.find_works("https://doi.org/10.5555/hive.3", ctx())
        check("128: Add a key work's lookup offers a title's first works to pick from, each its title, year, first authors "
              "and count of citations, and a DOI by itself, nothing written",
              [w["id"] for w in found["works"]] == ["W777", "W778"] and found["works"][0]["year"] == "2017"
              and found["works"][0]["cited"] == 4100 and found["works"][1]["authors"] == "Ann One, Ben Two, Cy Three and 2 more"
              and by_doi["works"][0]["id"] == "W3" and ss.find_works("", ctx())["said"] == "Give a DOI or a title.", str(found)[:300])

        # through the server, with the stub on loopback and the email Sift's settings keep
        kept_state = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
        config_file = base / "config.json"
        config_file.write_text(json.dumps({"interviewer": "Adam", "sift_email": "keeper@example.org"}), encoding="utf-8")
        os.environ[ss.STUB_ENV] = stub
        try:
            server_mod.CONFIG_PATH = config_file
            server_mod.ROOT_OVERRIDE = str(base)
            server_mod.STATE_MEMORY = {"recent": []}
            through = hives(base / "through")
            sift_routes.api_sift_review({"op": "open", "folder": str(through)})
            state["asked"] = []
            p_ = sift_routes.api_sift({"op": "fill_plan", "folder": str(through)})
            f_ = sift_routes.api_sift({"op": "fill", "folder": str(through), "at": 0})
            read_ = sift_routes.api_sift({"op": "read", "folder": str(through)})
            asked_through = list(state["asked"])
            sift_routes.api_sift_review({"op": "open", "folder": str(review)})
            w_ = sift_routes.api_sift_search({"op": "works", "folder": str(review), "text": "Keeping bees by the book"})
            k_ = sift_routes.api_sift_search({"op": "key_works", "folder": str(review), "rows": [kw_c]})
            r_ = sift_routes.api_sift_search({"op": "read", "folder": str(review)})
        finally:
            (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY) = kept_state
            os.environ.pop(ss.STUB_ENV, None)
        check("128: through the server, fill_plan and fill ask the stub on loopback, Crossref with the email kept in "
              "config.json, and the read carries the columns, and works and key_works answer the Plan",
              p_["missing"] == 5 and f_["filled"] == 5 and f_["at"] == 5
              and any(p == "/api.crossref.org/works" and q.get("mailto") == "keeper@example.org" for p, q, _ in asked_through)
              and {r["rec_id"]: r["oa"] for r in read_["records"]}["H3"] == "gold" and read_["key_works"] == []
              and [w["id"] for w in w_["works"]] == ["W777", "W778"] and k_["key_works"] == [kw_c] and r_["key_works"] == [kw_c],
              str(f_))
        ss.save_key_works(review, [kw_a, kw_b, kw_c])

        # ── C. the study suggestions, by the rule
        people = base / "studies"
        people.mkdir()
        with open(people / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["rec_id", "title", "authors", "year", "doi", "abstract", "openalex_authors"])
            w.writerows([
                ["S1", "Smoke and calm: keepers at the hive", "Ward, Nell; Okafor, Tunde; Pike, Ada", "2019", "", "Keepers (n = 11).", ""],
                ["S2", "Calm at the hive: a thesis", "Nell Ward", "2017", "", "A thesis with 11 participants.", ""],
                ["S3", "Swarms in spring", "Okafor T; Ward N", "2021", "", "Twelve keepers.", ""],
                ["S4", "Honey and grief", "Lund, Bo; Ruiz, Ana; Kim, Lo; Moss, Eve", "2020", "", "Nine keepers.", ""],
                ["S5", "Wax and weather", "Ruiz, Ana; Gale, Kit; Dunn, Sol; Rowe, Ivy", "2022", "", "Ten keepers.", ""],
                ["S6", "Queen rearing", "", "2022", "", "Six keepers.", ""],
                ["S7", "Drones at dusk", "Vale, Ida; Pell, Ray", "2018", "", "Five keepers.", "Ida Vale (A50); Ray Pell (A51)"],
                ["S8", "Dusk and drones", "Ida Vale-Moor; Sol Dunn", "2019", "", "Five keepers.", "Ida Vale-Moor (A50); Sol Dunn (A60)"],
                ["S9", "Pollen counts", "Pell, Ray; Moss, Eve", "2018", "", "Four keepers.", "Ray Pell (A70); Eve Moss (A71)"],
            ])
        sv = {r["rec_id"]: r for r in sift.screen(people)["records"]}
        pairs = lambda r: [s["rec_id"] for s in sv[r]["suggest"]]
        check("128: Sift suggests reports of one study by shared authors as sets, order ignored, two or more, or one who is "
              "at least half the shorter list, the reasons strongest first, and never a link by itself",
              pairs("S1") == ["S3", "S2"] and sv["S1"]["suggest"][0]["reasons"] == ["Shares 2 of 2 authors with S3 (Nell Ward and Tunde Okafor)",
                                                                                     "Years 2019 and 2021"]
              and sv["S1"]["suggest"][1]["reasons"] == ["Shares 1 of 1 author with S2 (Nell Ward)", "Both have 11 participants",
                                                        "Titles share calm and hive", "Years 2017 and 2019"]
              and "S5" not in pairs("S4") and pairs("S6") == [] and all(not sv[r]["study"] for r in sv),
              json.dumps({r: sv[r]["suggest"] for r in ("S1", "S4")})[:500])
        check("128: authors are matched by OpenAlex ID where both records have one, else by surname and first initial, "
              "accents and case folded, so one ID under two names matches and one name under two IDs does not",
              "S8" in pairs("S7") and "S9" not in pairs("S7") and "S7" not in pairs("S9")
              and sift.name_key("Gannet, Ida") == sift.name_key("Ida Gannet") == sift.name_key("GANNET IA") == sift.name_key("I. A. Gannet")
              == sift.name_key("Ída Gännet") == "gannet i" and sift.name_key("van der Berg, Jo") == sift.name_key("Jo van der Berg"),
              str(pairs("S7")) + str(pairs("S9")))
        one = sift.study(people, "link", "S1", "S2")
        two = sift.study(people, "link", "S3", "S1")
        three = sift.study(people, "link", "S4", "S9")
        four = sift.study(people, "link", "S9", "S2")
        same = sift.study(people, "link", "S2", "S4")
        held = sift.load(people)
        check("128: Same study links two records in a new study, a record joins a study the other is in, and two studies "
              "linked become the earlier, each answer naming every record it moved",
              one["changed"] and [(r["rec_id"], r["study"], r["study_with"]) for r in one["records"]] == [("S1", "Study 1", ["S2"]), ("S2", "Study 1", ["S1"])]
              and [r["rec_id"] for r in two["records"]] == ["S1", "S3"] and three["records"][0]["study"] == "Study 2"
              and sorted(r["rec_id"] for r in four["records"]) == ["S2", "S4", "S9"]
              and [held.cell(r, "study") for r in ("S1", "S2", "S3", "S4", "S9", "S5")] == ["Study 1"] * 5 + [""]
              and same["changed"] is False, str([r["rec_id"] for r in four["records"]]))
        out = sift.study(people, "unlink", "S9")
        sift.study(people, "link", "S5", "S6")
        last = sift.study(people, "unlink", "S6")
        held = sift.load(people)
        lines = [e for e in sift.read_lines(people) if e.get("act") == "study"]
        check("128: Unlink takes a record out of its study, and the last report left in a study goes with it, each a line "
              "of the log naming the records moved and their studies before, a study's label never given twice",
              [r["rec_id"] for r in out["records"]] == ["S9"] and held.cell("S9", "study") == "" and held.cell("S4", "study") == "Study 1"
              and held.cell("S5", "study") == held.cell("S6", "study") == "" and sorted(r["rec_id"] for r in last["records"]) == ["S5", "S6"]
              and lines[-2]["study"] == "Study 3" and lines[-1]["was"] == {"S6": "Study 3", "S5": "Study 3"}
              and lines[0]["change"] == "link" and lines[0]["with"] == "S2" and lines[0]["records"] == ["S1", "S2"]
              and sift.next_study(held, people) == "Study 4"
              and any(e.get("act") == "study" for e in sift.history(people, "S2")["history"]), json.dumps(lines[-1]))
        check("128: a link is refused in one line for a record the CSV lacks or the record itself, and the study is his, never "
              "a field a tool can set",
              refusal_of(lambda: sift.study(people, "link", "S1", "S99")) == "There is no record S99 in screening.csv."
              and refusal_of(lambda: sift.study(people, "link", "S1", "S1")) == "A record cannot be linked to itself."
              and refusal_of(lambda: sift.study(people, "join", "S1")) == "A study is linked or unlinked."
              and refusal_of(lambda: sift.set_field(people, "S1", "study", "Study 9")) == "study is not a field of yours, so nothing was written."
              and "study" in sift.OWN_COLUMNS and sift.is_own("study"))
        for r in ("S1", "S2", "S3", "S4", "S7"):
            sift.decide(people, r, "ta", "include")
            sift.decide(people, r, "ft", "include")
        c = sift.counts(sift.load(people))
        source = sift.prisma_source(c)
        rows = {(r[0], r[1]): r[2] for r in sift.count_rows(c)}
        check("128: the PRISMA flow counts the studies included and the reports of them, the reports he linked as one study "
              "once, and the counts' export says both",
              c["flow"]["studies"] == 2 and c["flow"]["reports"] == 5
              and 'included["Studies included<br/>in review (n = 2)<br/>Reports of included<br/>studies (n = 5)"]' in source
              and rows[("full text", "studies included")] == 2 and rows[("full text", "reports of included studies")] == 5, source[-400:])
        reset = base / "reset"
        shutil.copytree(people, reset)
        sift.reset(reset)
        check("128: Start again clears his studies with his other decisions, and keeps what OpenAlex and Crossref filled",
              all(not sift.load(reset).cell(r, "study") for r in sift.load(reset).ids)
              and sift.load(people).cell("S1", "study") == "Study 1")

        # ── D. links carried into a later run that keeps the decisions
        carry_review = base / "hive-carry"
        carry_review.mkdir()
        ss.save(carry_review, {"databases": ["psycinfo"], "blocks": [{"name": "Hives", "terms": ["hive*"]}]})
        ss.register(carry_review)
        d1, d2 = "2031-06-01", "2031-06-02"
        ris = lambda *recs: "".join(f"TY  - JOUR\nTI  - {t}\nAU  - {a}\nPY  - {y}\n" + (f"DO  - {d}\n" if d else "")
                                    + "AB  - An invented abstract on keepers and their hives.\nER  - \n\n" for t, a, y, d in recs).encode("utf-8")
        ss.take_export(carry_review, "psycinfo", ris(("Keeping hives 1", "Ward, Nell", "2021", "10.5555/hive.1"),
                                                     ("Keeping hives thesis", "Ward, Nell", "2019", ""),
                                                     ("Keeping hives 3", "Lund, Bo", "2023", "10.5555/hive.3")), "p.ris", day=d1, ctx=ctx())
        ss.run(carry_review, day=d1, ctx=ctx())
        r1 = carry_review / "runs" / d1
        sc1 = sift.load(r1)
        by_title = {sc1.cell(r, "title"): r for r in sc1.ids}
        sift.decide(r1, by_title["Keeping hives 1"], "ta", "include")
        sift.study(r1, "link", by_title["Keeping hives 1"], by_title["Keeping hives thesis"])
        meta1 = ss.read_run(r1)
        ss.take_export(carry_review, "psycinfo", ris(("Keeping Hives 1: a study", "Ward, Nell", "2021", "10.5555/hive.1"),
                                                     ("Keeping hives thesis", "Ward, Nell", "2019", ""),
                                                     ("Keeping hives 5", "Lund, Bo", "2024", "10.5555/hive.5")), "p.ris", day=d2, ctx=ctx())
        ss.run(carry_review, day=d2, ctx=ctx(), follows=d1)
        r2 = carry_review / "runs" / d2
        sc2 = sift.load(r2)
        studies2 = {sc2.cell(r, "title"): sc2.cell(r, "study") for r in sc2.ids}
        carried = [e for e in sift.read_lines(r2) if e.get("act") == "carry" and e.get("field") == "study"]
        refs2 = sift.references(r2)
        check("128: a run's own columns and references are written as it is made, and run.json counts them",
              sc1.cell(by_title["Keeping hives 1"], "open_access") == "green" and meta1["openalex_filled"] == 2
              and meta1["crossref_filled"] == 2 and sorted(sift.references(r1)) == sorted([by_title["Keeping hives 1"], by_title["Keeping hives 3"]])
              and any("from OpenAlex for 2 records, and from Crossref for 2" in line for line in ss.run_lines(ss.summary(r1))),
              str(meta1))
        check("128: his links come into a later run that keeps the decisions, the records matched by DOI under a new title "
              "and by title and year, each carried as a line of the log, and the references with them",
              studies2.get("Keeping hives 1") == "Study 1" and studies2.get("Keeping hives thesis") == "Study 1"
              and studies2.get("Keeping hives 3") == "" and studies2.get("Keeping hives 5") == "" and len(carried) == 2
              and all(e["value"] == "Study 1" and e["from"]["run"] == d1 and e["from"]["n"] for e in carried)
              and by_title["Keeping hives 1"] in refs2 and len(refs2) == 3, str(studies2) + str(carried)[:200])
    finally:
        httpd.shutdown()
        httpd.server_close()
        ss.RUNNER, ss.CLOCK = kept_runner, kept_clock
        if kept_env is not None:
            os.environ[ss.STUB_ENV] = kept_env

    # ── E. the screen: the columns, the filters and the sorts, in node
    check("128: the five columns take their place among the table's own, hidden at first, Set columns offering them",
          [k for k, shown in sift.TABLE_COLUMNS if k in ("retracted", "oa", "country", "study", "keyworks")]
          == ["study", "retracted", "oa", "country", "keyworks"]
          and not any(shown for k, shown in sift.TABLE_COLUMNS if k in ("retracted", "oa", "country", "study", "keyworks")))
    if not node:
        skip("128: the new columns in node", "node is not installed")
    else:
        view = sift.screen(run)
        lead = app_src[app_src.index("const esc = "):app_src.index("// a line from the server with a command in backticks")]
        block = sift_src.split("/* ── the table's rows: its columns, sort and filter, worked out with no page ── */", 1)[-1].split(
            "/* ── the table, drawn ── */", 1)[0]
        block = support.table_js() + "\n" + block
        parts = [lead, sift_words_js(sift_src), block, "function sfMeaning() { return ''; }",
                 "const SF = " + json.dumps({"stage": "ta", "filters": {}, "table": view["table"], "records": view["records"],
                                             "keyWorks": view["key_works"]}) + ";",
                 "SF.facetsMore = new Set();", "SF.facetsFind = {};"]
        parts += [whole(sift_src, name) for name in ("sfPillHtml", "sfLinked", "sfStars", "sfTvCell")]
        probe = base / "columns-128.js"
        probe.write_text("\n".join(parts) + r"""
const byId = new Map(SF.records.map((r) => [r.rec_id, r]));
const ids = SF.records.map((r) => r.rec_id);
const cols = sfAllCols();
const col = (k) => cols.find((c) => c.key === k);
const groups = sfGroups(SF.records, SF.records, cols, 'ta', [], {});
const g = (k) => { const x = groups.find((y) => y.key === k); return x ? x.choices.map((c) => [c.value, c.label]) : null; };
const counts = tbFacetCounts(SF.records, groups, {}, sfRead('ta'));
const sortBy = (key, dir) => tbSortRows(ids, byId, [{ key, dir }], cols, sfRead('ta'));
const pass = (key, f) => tbFilterRows(ids, byId, { [key]: f }, cols, sfRead('ta'));
byId.get('H2').study = 'Study 1'; byId.get('H5').study = 'Study 1'; byId.get('H3').study = 'Study 2';
console.log(JSON.stringify({
  notice: g('retracted'), oa: g('oa'), keyworks: g('keyworks'), country: g('country'),
  study: sfGroups(SF.records, SF.records, cols, 'ta', [], {}).find((y) => y.key === 'study').choices.map((c) => [c.value, c.label]),
  noticeCounts: counts.retracted, retractedFirst: sortBy('retracted', 'desc'), studyUp: sortBy('study', 'asc'),
  citesMost: sortBy('keyworks', 'desc'),
  open: pass('oa', ['open']), unknownOa: pass('oa', ['|none']), ireland: pass('country', ['ireland']),
  edition: pass('keyworks', ['title:keepingbeesbythebook|2024']), none: pass('keyworks', ['none']),
  questioned: pass('retracted', ['expression of concern']),
  kept: sfKeptRead({ retracted: ['retracted', 'gone'], oa: ['open'] }, groups),
  cells: ['retracted', 'oa', 'country', 'keyworks', 'study'].map((k) => sfTvCell(byId.get('H2'), col(k))),
  blank: ['retracted', 'oa', 'country', 'keyworks'].map((k) => sfTvCell(byId.get('H6'), col(k))),
  title: sfTvCell(byId.get('H2'), col('title')),
}));
""", encoding="utf-8")
        ran = subprocess.run([node, str(probe)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        # updated 14 October, later (137): Cites key works says Can't check where it said Unknown
        check("128: in node, each new column has its group in the filters, in plain words with Unknown for a record never "
              "asked, the countries by name as the journals are, and each key work by its title and year",
              out.get("notice") == [["retracted", "Retracted"], ["expression of concern", "Expression of concern"], ["corrected", "Corrected"],
                                    ["none", "None"], ["|none", "Unknown"]]
              and out.get("oa") == [["open", "Open"], ["closed", "Closed"], ["|none", "Unknown"]]
              and out.get("keyworks") == [["W777", "Keeping bees by the book (2016)"], ["title:keepingbeesbythebook|2024", "Keeping bees by the book (2024)"],
                                          ["doi:10.5555/kw.doi", "Smoke signals (2019)"], ["none", "None"], ["|none", "Can't check"]]
              and ["ireland", "Ireland"] in (out.get("country") or []) and (out.get("country") or [])[-1] == ["|none", "Unknown"]
              and out.get("study") == [["Study 1", "Study 1"], ["Study 2", "Study 2"], ["|none", "Not linked"]]
              and (out.get("noticeCounts") or {}).get("|none") == 1, (ran.stderr or json.dumps(out))[:600])
        check("128: in node, the new columns sort, a retraction first, linked reports together, and filter by each tick",
              out.get("retractedFirst", [])[:2] == ["H2", "H1"] and out.get("retractedFirst", [])[-1] == "H6"
              and out.get("studyUp") == ["H2", "H5", "H3", "H1", "H4", "H6"] and out.get("citesMost", [])[-1] == "H6"
              and out.get("open") == ["H1", "H3", "H5"] and out.get("unknownOa") == ["H4", "H6"] and out.get("ireland") == ["H1"]
              and out.get("edition") == ["H3"] and out.get("none") == ["H5"] and out.get("questioned") == ["H2"]
              and out.get("kept") == {"retracted": ["retracted"], "oa": ["open"]}, json.dumps(out)[:600])

    # ── F. the command line
    shown = sift_cli.cmd_sift(argparse.Namespace(folder=str(run), act="show", rec_id="H2", stage="ta", search=False))[1]
    listed = sift_cli.cmd_sift(argparse.Namespace(folder=str(people), act="list", stage="ta", round="all", search=False))[1]
    check("128: the command line's record says each column in plain lines, the study and Sift's suggestions, and a "
          "list's line its notices and study",
          "Retracted or corrected: retracted 9 January 2031, notice 10.5555/hive.2.ret and expression of concern November 2030, "
          "notice 10.5555/hive.2.eoc." in shown
          and "Open access: closed." in shown and "Country: United Kingdom." in shown
          and "Cites key works: Keeping bees by the book (2016)." in shown and "Study: not linked." in shown
          and any(line.startswith("S1  ") and line.endswith(", Study 1") for line in listed), "\n".join(shown[-8:]))
