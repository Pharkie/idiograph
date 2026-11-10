from __future__ import annotations

import csv
import os
import shutil

from . import support
from .support import check, search_stub, urllib_path


def test_sift_layout(scratch):
    print("\n105. Sift's layout and merge: the home screen's rows kept to their section on a long path, the Sift "
          "screen inside the window at every width, and two versions of one DOI merged as one record")
    import sift_search as ss

    # Sift's styles as its page loads them, the frame it shares with Trace first (tracestyle, 30 October 2026)
    scss = support.text("family/static/frame.css", "apps/sift/static/sift.css")
    rule = lambda css, sel: (css.split("\n" + sel + " {", 1)[1].split("}", 1)[0] if "\n" + sel + " {" in css else "")

    # ── A. the home screen's rows on a long path
    rows = rule(scss, ".sf-rows")

    # ── C. two versions of one DOI, an invented item on figshare and on Zenodo
    rec = lambda source, title, doi, abstract="": ss.record(source, "", title, "Inventa, A.", "2024", "Invented Data",
                                                             doi, abstract, "dataset")
    check("105: a DOI's version suffix is set aside for comparing, in any case and from a link, and nothing else is",
          ss.doi_key("https://doi.org/10.0000/Invented.Figshare.4242.V12") == "10.0000/invented.figshare.4242"
          and ss.doi_key("doi: 10.0000/invented.figshare.4242.v1") == "10.0000/invented.figshare.4242"
          and ss.doi_key("10.0000/invented.vintage") == "10.0000/invented.vintage"
          and ss.doi_key("10.0000/invented.v1a") == "10.0000/invented.v1a" and ss.doi_key("") == "")
    pair = ss.merge([rec("openalex", "Invented survey of allotment sheds, version 1", "10.0000/invented.figshare.4242.v1",
                         "An invented abstract."),
                     rec("epmc", "Data from: invented survey of allotment sheds", "https://doi.org/10.0000/INVENTED.figshare.4242")])
    check("105: a DOI and its .v1 are one record, its sources joined in the order of the run and the shorter DOI kept, "
          "whatever their titles",
          len(pair) == 1 and pair[0]["sources"] == ["openalex", "epmc"] and pair[0]["doi"] == "10.0000/invented.figshare.4242"
          and pair[0]["abstract"] == "An invented abstract." and pair[0]["abstract_from"] == "openalex", str(pair))
    back = ss.merge([rec("pubmed", "Invented survey of allotment sheds", "10.0000/invented.figshare.4242"),
                     rec("scopus", "Invented survey of allotment sheds", "10.0000/invented.figshare.4242.v1")])
    check("105: the shorter DOI stands when it came first too",
          len(back) == 1 and back[0]["sources"] == ["pubmed", "scopus"] and back[0]["doi"] == "10.0000/invented.figshare.4242",
          str(back))
    versions = ss.merge([rec("openalex", "Invented pond survey", "10.0000/invented.zenodo.77.v2"),
                         rec("wos", "Invented pond survey, revised", "10.0000/invented.zenodo.77.v3"),
                         rec("epmc", "Invented pond survey", "10.0000/invented.zenodo.77.v2")])
    check("105: a .v2 and a .v3 of one item are one record, each database named once",
          len(versions) == 1 and versions[0]["sources"] == ["openalex", "wos", "epmc"]
          and versions[0]["doi"] == "10.0000/invented.zenodo.77.v2", str(versions))
    apart = ss.merge([rec("openalex", "Invented hedge census", "10.0000/invented.hedge.1"),
                      rec("epmc", "Invented hedge census", "10.0000/invented.hedge.2"),
                      rec("pubmed", "Invented hedge census", "10.0000/invented.hedge.3.v1"),
                      rec("scopus", "Invented hedge census", "10.0000/invented.hedge.4.v1"),
                      rec("wos", "Invented hedge census", "")])
    check("105: two different DOIs still never merge on title and year, with or without a version suffix, and a record "
          "with no DOI joins the first of the same title and year",
          [m["doi"] for m in apart] == ["10.0000/invented.hedge.1", "10.0000/invented.hedge.2", "10.0000/invented.hedge.3.v1",
                                        "10.0000/invented.hedge.4.v1"]
          and apart[0]["sources"] == ["openalex", "wos"] and all(len(m["sources"]) == 1 for m in apart[1:]), str(apart))
    plan = {"benchmark": ["10.0000/invented.figshare.4242.v1", "10.0000/invented.hedge.9"]}
    missed, said = ss.benchmark_said(plan, {m["doi"] for m in pair})
    check("105: a benchmark DOI with a version suffix counts as found by the merged record that kept the shorter DOI",
          missed == ["10.0000/invented.hedge.9"] and said == "benchmark 1 of 2, missed 10.0000/invented.hedge.9", said)

    # ── D. OpenAlex's optional key, the keychain and the APIs stood in for, every key invented
    import http.server
    import threading
    import urllib.parse
    stub_state = {"keys": {"scopus": {"els-key-INVENTED1"}, "wos": set()}}

    class Echo(search_stub(stub_state)):
        """The stub, and at /echo/works an OpenAlex that refuses and says the key it was sent back."""

        def do_GET(self):
            if self.path.startswith("/echo/works"):
                q = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
                stub_state.setdefault("asked", []).append(("/echo/works", q))
                return self.send(401, f"Invalid api_key {q.get('api_key', '')} for this API")
            return super().do_GET()

    httpd =http.server.ThreadingHTTPServer(("127.0.0.1", 0), Echo)
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    stub = f"http://127.0.0.1:{httpd.server_address[1]}"
    held = {"ELSEVIER_API_KEY": "els-key-INVENTED1", "OPENALEX_API_KEY": "oa-key-INVENTED7"}
    asked = []

    class Done:
        def __init__(self, code, out):
            self.returncode, self.stdout, self.stderr = code, out, ""

    def keychain(argv, **kw):
        asked.append(list(argv))
        service = argv[argv.index("-s") + 1]
        return Done(0, held[service] + "\n") if service in held else Done(44, "")

    kept_runner, kept_env = ss.RUNNER, os.environ.pop(ss.STUB_ENV, None)
    ss.RUNNER = keychain
    base_urls = {s: stub + urllib_path(u) for s, u in ss.ENDPOINTS.items()}
    ctx = lambda **over: ss.Context(base=dict(base_urls, **over), pause=lambda s: None, page={"openalex": 2, "scopus": 1})
    review = scratch / "sift-layout" / "invented review"
    shutil.rmtree(review, ignore_errors=True)
    review.mkdir(parents=True)
    oa_read = ["security", "find-generic-password", "-s", "OPENALEX_API_KEY", "-w"]
    # updated 13 October (128): OpenAlex's requests alone, Crossref's to the same stub under a path of their own
    openalex_path = lambda p: p.endswith("/works") and "api.crossref.org" not in p
    works = lambda: [q for p, q in stub_state.get("asked", []) if openalex_path(p)]
    files = lambda day: [p for p in (review / "runs" / day).rglob("*") if p.is_file()]
    secrets = (b"oa-key-INVENTED7", b"els-key-INVENTED1")
    try:
        ss.save(review, {"databases": ["scopus", "openalex"], "blocks": [{"name": "Plots", "terms": ["allotment*"]}],
                         "years": {"from": 2000, "to": 2026}})
        keyed = ss.run(review, which="newest", day="2026-11-10", ctx=ctx())
        sent = works()
        searched = [q for q in sent if not q.get("filter", "").startswith("doi:")]
        filled = [q for q in sent if q.get("filter", "").startswith("doi:")]
        check("105: with OPENALEX_API_KEY in the keychain every OpenAlex request carries it as api_key, the search page by "
              "page and the abstract fill by DOI alike, the keychain read once for the run",
              len(searched) == 2 and len(filled) == 1 and all(q.get("api_key") == "oa-key-INVENTED7" for q in sent)
              and asked.count(oa_read) == 1 and keyed["filled"] == 1
              and not any(q.get("api_key") for p, q in stub_state["asked"] if not openalex_path(p)), str(sent)[:300])
        check("105: the key is in no file the run writes, raw_openalex.json, screening.csv, log.csv and run.json among them",
              {p.name for p in files("2026-11-10")} >= {"raw_openalex.json", "screening.csv", "log.csv", "run.json"}
              and not any(s in p.read_bytes() for p in files("2026-11-10") for s in secrets))
        held.pop("OPENALEX_API_KEY")
        stub_state["asked"].clear()
        bare = ss.run(review, which="newest", day="2026-11-11", ctx=ctx())
        sent = works()
        check("105: with no OpenAlex key a run sends no api_key and comes out exactly as the keyed one did",
              len(sent) == 3 and not any("api_key" in q for q in sent) and bare["merged"] == keyed["merged"]
              and (review / "runs" / "2026-11-11" / "screening.csv").read_bytes()
              == (review / "runs" / "2026-11-10" / "screening.csv").read_bytes(), str(sent)[:200])
        held["OPENALEX_API_KEY"] = "oa-key-INVENTED7"
        stub_state["asked"].clear()
        ss.run(review, which="newest", day="2026-11-12", ctx=ctx(openalex=stub + "/echo/works"))
        with open(review / "runs" / "2026-11-12" / "log.csv", encoding="utf-8", newline="") as fh:
            note = {r["source"]: r for r in csv.DictReader(fh)}["OpenAlex"]["note"]
        try:
            ss.run_openalex(ctx(openalex=stub + "/echo/works"), "invented")
            raised, detail = "", ""
        except ss.SearchError as exc:
            raised, detail = str(exc), exc.detail
        # the error says it in plain words on the screen since 17 October, later, its detail keeping the answer
        check("105: a refusal that says the key back is scrubbed before it reaches the log, run.json or the error",
              "failed: HTTP 401 from" in note and "Invalid api_key [key] for this API" in note
              and raised == "OpenAlex refused the key (HTTP 401)." and "Invalid api_key [key] for this API" in detail
              and "INVENTED7" not in note + raised + detail
              and any(q.get("api_key") == "oa-key-INVENTED7" for p, q in stub_state["asked"] if p == "/echo/works")
              and not any(s in p.read_bytes() for p in files("2026-11-12") for s in secrets), note)

        # ── E. an export from EBSCO's newer interface, no DOI and no journal, its dates written 20260803
        ebsco = ("title,publicationDate,authors,publisher,plink,abstract\n"
                 '"Growing Together on the Allotment",20190415,"Fern, Ann",Invented Press,'
                 "https://research.ebsco.example/plink/inv-1,Twelve invented plot holders.\n"
                 '"An invented diary of a dry summer",20260803,"Oak, Fay",Invented Press,'
                 "https://research.ebsco.example/plink/inv-2,Invented gardeners kept diaries.\n")
        kind, rows = ss.read_export(ebsco.encode("utf-8"), "ebsco.csv", "PsycInfo")
        ris = ss.read_ris("TY  - JOUR\nTI  - An invented dated note\nDA  - 20260803\nER  - \n", "PsycInfo")
        check("105: a year is read from a compact date and an ISO one, in a CSV's date column and a RIS date tag, and "
              "from nothing that is not a date",
              [ss.year_of(v) for v in ("20260803", "202608", "2026-08-03", "2026/08/03", "2019///", "Spring 2019", "12345678", "")]
              == ["2026", "2026", "2026", "2026", "2019", "2019", "", ""]
              and kind == "csv" and [r["year"] for r in rows] == ["2019", "2026"] and ris[0]["year"] == "2026", str(rows)[:200])
        check("105: EBSCO's columns are mapped, publicationDate as the year, its publisher never taken as a journal and plink "
              "as the record's url, its DOI left empty",
              rows[0]["journal"] == "" and rows[0]["url"] == "https://research.ebsco.example/plink/inv-1"
              and rows[0]["doi"] == "" and rows[1]["title"] == "An invented diary of a dry summer"
              and rows[1]["authors"] == "Oak, Fay", str(rows[0]))
        rec2 = lambda source, title, year, doi="": ss.record(source, "", title, "Inventa, A.", year, "", doi, "", "article")
        alone = ss.merge([rec2("PsycInfo", "Invented Shed-Keeping, a Study", ""),
                          rec2("Scopus", "Invented shed keeping: a study", "2019", "10.0000/invented.shed")])
        check("105: a record with no year joins the one record of its title, its database named in the run's order",
              len(alone) == 1 and alone[0]["sources"] == ["PsycInfo", "Scopus"] and alone[0]["year"] == "2019"
              and alone[0]["doi"] == "10.0000/invented.shed", str(alone))
        several = ss.merge([rec2("Scopus", "Invented pond notes", "2019"), rec2("OpenAlex", "Invented pond notes", "2021"),
                            rec2("PsycInfo", "Invented pond notes", "")])
        clash = ss.merge([rec2("Scopus", "Invented hedge notes", "2019", "10.0000/invented.h1"),
                          rec2("PsycInfo", "Invented hedge notes", "", "10.0000/invented.h2")])
        yearless = ss.merge([rec2("PsycInfo", "Invented wall notes", ""), rec2("Other", "Invented wall notes", "")])
        recA = lambda source, authors: ss.record(source, "", "Invented gate notes", authors, "2020", "", "10.0000/invented.gate", "", "article")
        fuller = ss.merge([recA("Scopus", "Heron M."), recA("Europe PMC", "Heron M, Wren TC, Birch JJ."),
                           recA("OpenAlex", "Mia Heron; Tom Wren")])
        check("105, 12 October: a merged record keeps the fullest list of authors its databases give, never one database's "
              "first author alone",
              len(fuller) == 1 and fuller[0]["authors"] == "Heron M, Wren TC, Birch JJ."
              and ss.author_names("Heron M, Wren TC, et al.") == ["Heron M", "Wren TC"]
              and ss.author_names("Baker, Michael") == ["Baker, Michael"], str(fuller[0]["authors"] if fuller else ""))
        recB = lambda source, title, journal, year, kind, abstract: ss.record(source, "", title, "Heron M.", year, journal,
                                                                             "10.0000/invented.lane", abstract, kind)
        best = ss.merge([recB("Scopus", "INVENTED LANE NOTES", "J Invent Lanes", "2021", "Article", "Short."),
                         recB("PsycInfo", "Invented lane notes: a study of verges", "Journal of Invented Lanes", "2020",
                              "Dissertation", "A longer abstract of the invented verges."),
                         recB("OpenAlex", "Invented lane notes", "Lane Repository", "2020", "article", "")])
        tie = ss.merge([recB("Scopus", "Invented kerb notes", "", "2022", "", ""), recB("OpenAlex", "Invented kerb notes", "", "2021", "", "")])
        b0 = best[0] if best else {}
        check("105, 12 October: a merged record takes each field at its best across its databases, the title not in "
              "capitals with its subtitle, the journal's full name over its abbreviation and never a repository's, the "
              "type that says most, the longest abstract and where it came from, and the year most give, the earliest on "
              "a tie",
              len(best) == 1 and b0["title"] == "Invented lane notes: a study of verges" and b0["journal"] == "Journal of Invented Lanes"
              and b0["pub_type"] == "Dissertation" and b0["abstract_from"] == "PsycInfo" and b0["year"] == "2020"
              and len(tie) == 1 and tie[0]["year"] == "2021", str({k: b0.get(k) for k in ("title", "journal", "pub_type", "year")}))
        check("105: a record with no year stands apart when several records carry its title or their DOIs differ, two "
              "dated records of one title two years apart stay apart, and two with no year join as before",
              [(m["year"], m["sources"]) for m in several] == [("2019", ["Scopus"]), ("2021", ["OpenAlex"]), ("", ["PsycInfo"])]
              and len(clash) == 2 and len(yearless) == 1 and yearless[0]["sources"] == ["PsycInfo", "Other"],
              str([(m["year"], m["sources"]) for m in several]))
        thesis = ss.merge([rec2("ProQuest", "Invented lives of lock keepers", "2020"),
                           rec2("PsycInfo", "Invented lives of lock keepers", "2021"),
                           rec2("Scopus", "Invented lives of lock keepers", "2019", "10.0000/invented.lock")])
        own_year = ss.merge([rec2("Scopus", "Invented bridge notes", "2020", "10.0000/invented.b1"),
                             rec2("OpenAlex", "Invented bridge notes", "2021", "10.0000/invented.b2"),
                             rec2("PsycInfo", "Invented bridge notes", "2021")])
        doi_clash = ss.merge([rec2("Scopus", "Invented weir notes", "2020", "10.0000/invented.w1"),
                              rec2("OpenAlex", "Invented weir notes", "2021", "10.0000/invented.w2")])
        check("105, 11 October: two records of one title a year apart join, as a thesis and its database record, a "
              "record's own year matched first, and two whose DOIs differ stay apart (12 October: three years, one each, "
              "give the earliest)",
              len(thesis) == 1 and thesis[0]["sources"] == ["ProQuest", "PsycInfo", "Scopus"] and thesis[0]["year"] == "2019"
              and [(m["year"], m["sources"]) for m in own_year] == [("2020", ["Scopus"]), ("2021", ["OpenAlex", "PsycInfo"])]
              and len(doi_clash) == 2 and ss.near_years("2020") == ["2020", "2019", "2021"] and ss.near_years("n.d.") == ["n.d."],
              str([(m["year"], m["sources"]) for m in thesis + own_year + doi_clash]))
        plan = {"benchmark": ["10.5555/allot.1", "10.5555/allot.9"]}
        every = [rec2("OpenAlex", "Growing together on the allotment", "2019", "10.5555/allot.1")]
        by_title = ss.source_benchmark(plan, rows, every + rows, export=True)
        no_match = ss.source_benchmark(plan, rows[1:], every + rows[1:], export=True)
        as_api = ss.source_benchmark(plan, rows[1:], every + rows[1:], export=False)
        check("105: a benchmark DOI counts as found by a record with no DOI that carries the title of one that has it, and "
              "an export with no DOIs that matches none says so in place of naming every benchmark missed",
              by_title == "benchmark 1 of 2, missed 10.5555/allot.9" and no_match == "No DOIs in this export"
              and ss.NO_DOIS == "No DOIs in this export" and as_api == "benchmark 0 of 2, missed 10.5555/allot.1, 10.5555/allot.9",
              f"{by_title} | {no_match} | {as_api}")
        shed = scratch / "sift-layout" / "invented ebsco review"
        shutil.rmtree(shed, ignore_errors=True)
        shed.mkdir(parents=True)
        ss.save(shed, {"databases": ["psycinfo", "openalex"], "blocks": [{"name": "Plots", "terms": ["allotment*"]}],
                       "benchmark": ["10.5555/allot.1", "10.5555/allot.9"]})
        ss.take_export(shed, "psycinfo", ebsco.encode("utf-8"), "ebsco.csv", day="2026-11-13", ctx=ctx())
        ss.run(shed, which="newest", day="2026-11-13", ctx=ctx())
        with open(shed / "runs" / "2026-11-13" / "log.csv", encoding="utf-8", newline="") as fh:
            shed_log = {r["source"]: r["note"] for r in csv.DictReader(fh)}
        with open(shed / "runs" / "2026-11-13" / "screening.csv", encoding="utf-8", newline="") as fh:
            shed_rows = list(csv.DictReader(fh))
        grown = [r for r in shed_rows if r["title"].lower() == "growing together on the allotment"]
        ss.take_export(shed, "psycinfo", ebsco.split("\n", 1)[0].encode() + b"\n" + ebsco.split("\n")[2].encode() + b"\n",
                       "ebsco.csv", day="2026-11-14", ctx=ctx())
        ss.run(shed, which="newest", day="2026-11-14", ctx=ctx())
        with open(shed / "runs" / "2026-11-14" / "log.csv", encoding="utf-8", newline="") as fh:
            bare_log = {r["source"]: r["note"] for r in csv.DictReader(fh)}
        check("105: in a run, the EBSCO export's line finds the benchmark by title, its record joins OpenAlex's with the "
              "DOI and keeps its link in a url column, and an export matching none says No DOIs in this export",
              "benchmark 1 of 2, missed 10.5555/allot.9" in shed_log.get("PsycInfo", "")
              and len(grown) == 1 and grown[0]["sources"] == "PsycInfo; OpenAlex" and grown[0]["doi"] == "10.5555/allot.1"
              and grown[0]["url"] == "https://research.ebsco.example/plink/inv-1"
              and any(r["year"] == "2026" and r["title"] == "An invented diary of a dry summer" for r in shed_rows)
              and bare_log.get("PsycInfo", "").endswith(", No DOIs in this export")
              and "benchmark 1 of 2" in bare_log.get("OpenAlex", ""), f"{shed_log} | {bare_log}")
    finally:
        ss.RUNNER = kept_runner
        if kept_env is not None:
            os.environ[ss.STUB_ENV] = kept_env
        httpd.shutdown()
        httpd.server_close()
