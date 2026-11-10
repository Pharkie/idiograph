from __future__ import annotations

import csv
import json
import os
import shutil

from . import support
from .support import check, refusal_of, search_stub, urllib_path


@support.as_app("sift")
def test_sift_search(scratch):
    print("\n104. Sift's searches: the plan, each database's string, the register, the runs against a stub of "
          "every API, the export dropped, the merge, the screen, the command line and MCP")
    import http.server
    import threading
    import time
    import cli
    import mcp_server
    import sift_mcp
    import server as server_mod
    import sift_routes
    import sift
    import sift_search as ss

    page = support.page_text()
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    sjs = support.text("apps/sift/static/sift_search.js")
    base = scratch / "sift-search"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)

    # ── A. each database's string from an invented plan, against strings written by hand
    # updated 14 October (134): each phrase written in full, since a phrase holds no truncation
    plan = ss.clean_plan({
        "databases": ["openalex", "pubmed", "scopus", "wos", "epmc", "psycinfo", "other"], "other_name": "Garden Index",
        "blocks": [{"name": "Allotments", "terms": "allotment*\ncommunity garden\n\"plot holders\"", "scope": "tak"},
                   {"name": "Wellbeing", "terms": ["wellbeing", "\"mental health\""], "scope": "tak",
                    "scopes": {"epmc": "methods", "scopus": "methods"}},
                   {"name": "Talk", "terms": ["interview*"], "scope": "fulltext"}],
        "years": {"from": "2000", "to": 2026}, "types": ["dissertation", "review", "article"]})
    got = {s["source"]: s for s in ss.strings(plan)}
    want = {
        "scopus": 'TITLE-ABS-KEY(allotment* OR "community garden" OR "plot holders") AND TITLE-ABS-KEY(wellbeing OR '
                  '"mental health") AND TITLE-ABS-KEY(interview*) AND PUBYEAR > 1999 AND PUBYEAR < 2027 AND '
                  '(DOCTYPE(ar) OR DOCTYPE(re))',
        "wos": 'TS=(allotment* OR "community garden" OR "plot holders") AND TS=(wellbeing OR "mental health") AND '
               'TS=(interview*) AND PY=(2000-2026) AND DT=(Article OR Review)',
        "psycinfo": '(TI (allotment* OR "community garden" OR "plot holders") OR AB (allotment* OR "community garden" OR '
                    '"plot holders") OR KW (allotment* OR "community garden" OR "plot holders")) AND (TI (wellbeing OR '
                    '"mental health") OR AB (wellbeing OR "mental health") OR KW (wellbeing OR "mental health")) AND '
                    'TX (interview*)',
        "pubmed": '(allotment*[tiab] OR "community garden"[tiab] OR "plot holders"[tiab]) AND (wellbeing[tiab] OR '
                  '"mental health"[tiab]) AND (interview*[tiab]) AND 2000:2026[dp] AND ("journal article"[pt] OR review[pt])',
        "epmc": '(TITLE_ABS:allotment* OR KW:allotment* OR TITLE_ABS:"community garden" OR KW:"community garden" OR '
                'TITLE_ABS:"plot holders" OR KW:"plot holders") AND (METHODS:wellbeing OR METHODS:"mental health") AND '
                '(TITLE_ABS:interview* OR KW:interview* OR BODY:interview*) AND PUB_YEAR:[2000 TO 2026] AND '
                '(PUB_TYPE:"journal article" OR PUB_TYPE:"review")',
        "openalex": 'title_and_abstract.search:(allotment OR "community garden" OR "plot holders") AND (wellbeing OR '
                    '"mental health"),fulltext.search:(interview),publication_year:2000-2026,type:article|review|dissertation',
        "other": '(allotment* OR "community garden" OR "plot holders") AND (wellbeing OR "mental health") AND (interview*)',
    }
    check("104: the databases stand in Sift's order, a phrase of two words is quoted, and the years are whole numbers",
          plan["databases"] == ["scopus", "wos", "psycinfo", "pubmed", "epmc", "openalex", "other"]
          and plan["blocks"][0]["terms"] == ["allotment*", '"community garden"', '"plot holders"']
          and plan["years"] == {"from": 2000, "to": 2026} and plan["types"] == ["article", "review", "dissertation"],
          str(plan["blocks"][0]["terms"]))
    for s in want:
        check(f"104: {ss.NAMES[s]}'s string, truncation, phrases, the fields, the years and the types, as written by hand",
              got[s]["query"] == want[s] and got[s]["written"] == want[s], got[s]["query"])
    check("104: Scopus has no methods or full-text field, so those blocks fall back to title, abstract and keywords, "
          "said in a note, and a type it lacks is said",
          got["scopus"]["notes"] == ["Scopus has no methods sections field, so Wellbeing is searched in title, abstract and keywords.",
                                     "Scopus has no full text field, so Talk is searched in title, abstract and keywords.",
                                     "Scopus has no dissertation type to limit by."], str(got["scopus"]["notes"]))
    check("104: OpenAlex stems, so its asterisks are left out and a note says so, and the export databases name the limiters",
          "*" not in got["openalex"]["query"]
          and "OpenAlex's search stems words and takes no truncation, so the asterisks are left out."
          in got["openalex"]["notes"]
          and got["psycinfo"]["limits"] == "Set on the site: published 2000 to 2026, journal article, review and dissertation."
          and got["other"]["name"] == "Garden Index" and not got["pubmed"]["limits"])
    open_end = {s["source"]: s["query"] for s in ss.strings(ss.clean_plan(dict(plan, years={"from": 2010}, types=["article"])))}
    to_only = {s["source"]: s["query"] for s in ss.strings(ss.clean_plan(dict(plan, years={"to": 2015}, types=[])))}
    check("104: a year from alone and a year to alone, each database in its own way, and one type with no brackets",
          open_end["scopus"].endswith("AND PUBYEAR > 2009 AND DOCTYPE(ar)") and f"PY=(2010-{ss.this_year()})" in open_end["wos"]
          and "2010:3000[dp]" in open_end["pubmed"] and f"PUB_YEAR:[2010 TO {ss.this_year()}]" in open_end["epmc"]
          and open_end["openalex"].endswith(",publication_year:>2009,type:article")
          and to_only["scopus"].endswith("AND PUBYEAR < 2016") and to_only["openalex"].endswith(",publication_year:<2016")
          and "1000:2015[dp]" in to_only["pubmed"] and "DT=" not in to_only["wos"], open_end["scopus"])
    bad = {t: ss.parse_term(t)[1] for t in ("garden AND shed", "(garden)", "*garden", "gar*den", "plot:holder", "")}
    check("104: a term with an operator, a database's syntax or a leading asterisk is refused in one line, and an empty one is nothing",
          bad["garden AND shed"].endswith("holds an operator. Put each term on a line of its own.")
          and "a mark a database reads as its own syntax" in bad["(garden)"] and bad["*garden"].endswith("an asterisk ends a word.")
          and bad["gar*den"] and bad["plot:holder"] and bad[""] == ""
          and ss.parse_term('"garden AND shed"')[0] == {"text": "garden AND shed", "phrase": True}, str(bad))
    over = ss.clean_plan(dict(plan, overrides={"wos": {"query": "TS=(allotment*)", "reason": ""}}))
    check("104: a string edited manually stands in place of Sift's, and without a reason it holds up the plan",
          ss.strings(over)[1]["query"] == "TS=(allotment*)" and ss.strings(over)[1]["written"] == want["wos"]
          and "Web of Science's edited string needs its reason." in ss.problems(over))

    # ── B. the plan file: a draft, register, an edit that makes the next draft, its reason
    review = base / "allotment-review"
    review.mkdir()
    (review / "reasons.csv").write_text("stage,code,meaning\nta,E1,Not about gardening\n", encoding="utf-8")
    first = {"databases": ["scopus", "wos", "psycinfo", "pubmed", "epmc", "openalex"],
             "blocks": [{"name": "Allotments", "terms": ["allotment*"]}, {"name": "Wellbeing", "terms": ["wellbeing"]}],
             "years": {"from": 2000, "to": 2026}, "benchmark": ["https://doi.org/10.5555/ALLOT.1", "10.5555/allot.9"]}
    st = ss.save(review, first)
    st = ss.save(review, dict(first, overrides={"wos": {"query": "TS=(allotment*) AND TS=(wellbeing)", "reason": "Kept short"}}))
    data = json.loads((review / ss.PLAN_NAME).read_text(encoding="utf-8"))
    check("104: a first save is version 1, a draft, saved whole with the hand-written string and its reason",
          [v["version"] for v in data["versions"]] == [1] and data["versions"][0]["registered"] is None
          and data["versions"][0]["plan"]["overrides"]["wos"] == {"query": "TS=(allotment*) AND TS=(wellbeing)", "reason": "Kept short"}
          and data["versions"][0]["plan"]["benchmark"] == ["10.5555/allot.1", "10.5555/allot.9"] and st["problems"] == [])
    done = ss.register(review)
    md = (review / ss.PLAN_MD).read_text(encoding="utf-8")
    check("104: Register freezes version 1 with its date and writes search_plan.md, its strings, the edited one's "
          "reason and the language line",
          done["registered"] == 1 and json.loads((review / ss.PLAN_NAME).read_text(encoding="utf-8"))["versions"][0]["registered"]
          and md == done["markdown"] and md.startswith("# Search plan, version 1\n\nRegistered ")
          and "No language limit: language is applied at screening." in md and "```\nTS=(allotment*) AND TS=(wellbeing)\n```" in md
          and "Edited manually: Kept short." in md and "A run must find 10.5555/allot.1, 10.5555/allot.9." in md
          and "PsycInfo (by export)" in md and chr(0x2014) not in md and ";" not in md, md[:200])
    try:
        ss.register(review)
        again = ""
    except ss.SearchError as exc:
        again = str(exc)
    st2 = ss.save(review, dict(first, years={"from": 2001, "to": 2026}))
    try:
        ss.register(review)
        needs = ""
    except ss.SearchError as exc:
        needs = str(exc)
    v1 = json.loads((review / ss.PLAN_NAME).read_text(encoding="utf-8"))["versions"][0]
    check("104: registered and unchanged is refused, and an edit after it makes version 2, a draft, version 1 left whole",
          again == "Version 1 is registered and unchanged since."
          # the head carries when it was saved and, since 12 October, later, its registry and registration too (area 124)
          and {k: st2["current"][k] for k in ("version", "registered", "reason", "registry", "registration")}
          == {"version": 2, "registered": None, "reason": "", "registry": "", "registration": ""}
          and v1["plan"]["years"] == {"from": 2000, "to": 2026} and v1["registered"] and st2["registered"] == 1)
    try:
        ss.run(review, which="draft", ctx=ss.Context(base={}, pause=lambda s: None), day="2026-11-01")
        unrun = ""
    except ss.SearchError as exc:
        unrun = str(exc)
    check("104: version 2 needs its reason before it is registered or run",
          needs == "Version 2 needs the reason for its changes." and unrun == needs, needs + " | " + unrun)
    back = ss.save(review, dict(first, overrides={"wos": {"query": "TS=(allotment*) AND TS=(wellbeing)", "reason": "Kept short"}}))
    check("104: an edit that puts the plan back as registered drops the draft",
          back["current"]["version"] == 1 and back["current"]["registered"] and len(back["versions"]) == 1)
    ss.save(review, dict(first, years={"from": 2001, "to": 2026}), reason="A later start")
    two = ss.register(review)
    check("104: with its reason version 2 is registered, and its Markdown says what changed and names version 1",
          two["registered"] == 2 and "Changed from version 1: A later start." in two["markdown"]
          and "## Earlier versions" in two["markdown"] and "Version 1, registered " in two["markdown"])
    ss.save(review, dict(first, overrides={"wos": {"query": "TS=(allotment*) AND TS=(wellbeing)", "reason": "Kept short"}}),
            reason="Back to 2000")
    ss.register(review)

    # ── C. a run against a stub of every API, the keychain stood in for
    stub_state = {"keys": {"scopus": {"els-key-SECRET123", "stub-elsevier_api_key"},
                           "wos": {"wos-key-SECRET456", "stub-clarivate_api_key"}}}
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), search_stub(stub_state))
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    stub = f"http://127.0.0.1:{httpd.server_address[1]}"
    asked = []

    class Done:
        def __init__(self, code, out):
            self.returncode, self.stdout, self.stderr = code, out, ""

    held = {"ELSEVIER_API_KEY": "els-key-SECRET123", "CLARIVATE_API_KEY": "wos-key-SECRET456"}

    def keychain(argv, **kw):
        asked.append(list(argv))
        service = argv[argv.index("-s") + 1]
        return Done(0, held[service] + "\n") if service in held else Done(44, "")

    kept_runner, kept_env = ss.RUNNER, os.environ.pop(ss.STUB_ENV, None)
    ss.RUNNER = keychain
    base_urls = {s: stub + urllib_path(u) for s, u in ss.ENDPOINTS.items()}
    small = {"pubmed": 1, "epmc": 1, "openalex": 2, "scopus": 1, "wos": 1}
    ctx = lambda: ss.Context(base=base_urls, pause=lambda s: None, page=small)
    day = "2026-11-03"
    run_dir = review / "runs" / day
    # a run the command line, MCP or the route makes waits for nothing between pages or before a retry, since
    # every request goes to the stub on loopback
    real_init = ss.Context.__init__
    ss.Context.__init__ = lambda self, base=None, pause=None, page=None, email="": real_init(
        self, base, pause if pause is not None else (lambda seconds: None), page, email)
    try:
        ris = ("TY  - JOUR\nTI  - Growing together on the allotment\nAU  - Fern, A.\nAU  - Reed, B.\nPY  - 2019///\n"
               "JO  - Journal of Invented Gardens\nDO  - https://doi.org/10.5555/ALLOT.1\nAB  - Twelve plot holders described "
               "growing food together.\nKW  - allotments\nKW  - wellbeing\nER  - \n\n"
               "TY  - CHAP\nT1  - Digging in: older gardeners\nA1  - Moss, C.\nY1  - 2017\nT2  - Invented Essays on Soil\n"
               "AB  - Older gardeners spoke of the plot as a second home,\n  and of the seasons as company.\nKW  - ageing\nER  - \n")
        dropped = ss.take_export(review, "psycinfo", ris.encode("utf-8"), "PsycInfo export.ris", day=day, ctx=ctx())
        check("104: a RIS export dropped before the run begins the day's run folder, kept as psycinfo.ris and read",
              (run_dir / "psycinfo.ris").read_bytes() == ris.encode("utf-8") and dropped["taken"] == {
                  "source": "psycinfo", "records": 2, "file": "psycinfo.ris"} and dropped["version"] == 3, str(dropped)[:200])
        raw = json.loads((run_dir / "raw_psycinfo.json").read_text(encoding="utf-8"))
        check("104: the RIS tags read, TY, TI or T1, AU or A1, PY or Y1, AB with its wrapped line, DO as an address, JO or T2, KW",
              [r["title"] for r in raw] == ["Growing together on the allotment", "Digging in: older gardeners"]
              and raw[0]["authors"] == "Fern, A.; Reed, B." and raw[0]["year"] == "2019" and raw[0]["doi"] == "10.5555/allot.1"
              and raw[0]["journal"] == "Journal of Invented Gardens" and raw[0]["keywords"] == "allotments; wellbeing"
              and raw[0]["pub_type"] == "journal article" and raw[1]["authors"] == "Moss, C." and raw[1]["year"] == "2017"
              and raw[1]["journal"] == "Invented Essays on Soil" and raw[1]["pub_type"] == "book chapter"
              and raw[1]["abstract"] == "Older gardeners spoke of the plot as a second home, and of the seasons as company."
              and all(r["source"] == "PsycInfo" for r in raw), str(raw)[:300])
        heard = []
        result = ss.run(review, day=day, ctx=ctx(), progress=lambda s, said: heard.append((s, said["state"])))
        files = sorted(p.name for p in run_dir.iterdir())
        check("104: the run writes raw_<source>.json for each database, log.csv, screening.csv, reasons.csv and run.json",
              # updated 13 October (128): each record's references beside the screening, and 23 October (256): the
              # screening's lock, which a run now holds before it removes anything in its folder
              files == sorted(["log.csv", "psycinfo.ris", "raw_epmc.json", "raw_openalex.json", "raw_psycinfo.json", "raw_pubmed.json",
                               "raw_scopus.json", "raw_wos.json", "reasons.csv", "run.json", "screening.csv", "screening.lock",
                               "screening.references.json"])
              and (run_dir / "reasons.csv").read_text(encoding="utf-8") == (review / "reasons.csv").read_text(encoding="utf-8"),
              ", ".join(files))
        check("104: the keychain is read through keychain_key for each key, with the security tool's own words",
              ["security", "find-generic-password", "-s", "ELSEVIER_API_KEY", "-w"] in asked
              and ["security", "find-generic-password", "-s", "ELSEVIER_INSTTOKEN", "-w"] in asked
              and ["security", "find-generic-password", "-s", "CLARIVATE_API_KEY", "-w"] in asked, str(asked[:3]))
        calls = stub_state["calls"]
        check("104, updated 12 October (121): every API is asked page by page, PubMed, Europe PMC, OpenAlex, Scopus and Web "
              "of Science, OpenAlex's fill asked about every record with a DOI, a fourth request to /works",
              calls.get("/entrez/eutils/esearch.fcgi") == 2 and calls.get("/entrez/eutils/efetch.fcgi") == 1
              and calls.get("/europepmc/webservices/rest/search") == 2 and calls.get("/content/search/scopus") == 2
              and calls.get("/apis/wos-starter/v1/documents") == 2 and calls.get("/works") == 4, str(calls))
        check("104: progress hears each API database run and end, and the export taken",
              ("pubmed", "running") in heard and ("pubmed", "done") in heard and ("wos", "done") in heard
              and ("psycinfo", "done") in heard and ("psycinfo", "running") not in heard, str(heard))
        with open(run_dir / "log.csv", encoding="utf-8", newline="") as fh:
            log_rows = list(csv.reader(fh))
        logs = {r[1]: dict(zip(log_rows[0], r)) for r in log_rows[1:]}
        check("104: log.csv has exactly date, source, interface, query, hits, records_saved and note, a row a database",
              log_rows[0] == ["date", "source", "interface", "query", "hits", "records_saved", "note"]
              and list(logs) == ["Scopus", "Web of Science", "PsycInfo", "PubMed", "Europe PMC", "OpenAlex"]
              and all(r["date"] == day for r in logs.values()), str(log_rows[0]))
        check("104: each row gives the interface, the exact query, the hits and the records saved, and its note the version",
              logs["PubMed"]["query"] == "(allotment*[tiab]) AND (wellbeing[tiab]) AND 2000:2026[dp]"
              and logs["PubMed"]["interface"] == "PubMed via NCBI E-utilities" and logs["PubMed"]["hits"] == "2"
              and logs["PubMed"]["records_saved"] == "2" and logs["PubMed"]["note"].startswith("plan version 3, translation: stub translation")
              and logs["Web of Science"]["query"] == "TS=(allotment*) AND TS=(wellbeing)"
              and logs["PsycInfo"]["interface"] == "APA PsycInfo on EBSCOhost, export" and logs["PsycInfo"]["hits"] == "2"
              and "RIS export (psycinfo.ris), hits = records in it" in logs["PsycInfo"]["note"]
              and logs["OpenAlex"]["note"].startswith("plan version 3, stemmed, no truncation"), str(logs["PubMed"]))
        check("104: a missed benchmark DOI is named in each database's note and in the run",
              all("benchmark 1 of 2, missed 10.5555/allot.9" in logs[n]["note"] for n in ("Scopus", "PsycInfo", "PubMed", "OpenAlex"))
              and "benchmark 0 of 2, missed 10.5555/allot.1, 10.5555/allot.9" in logs["Web of Science"]["note"]
              and result["missed"] == ["10.5555/allot.9"] and result["benchmark"] == 2, logs["Scopus"]["note"])
        with open(run_dir / "screening.csv", encoding="utf-8", newline="") as fh:
            rows = list(csv.reader(fh))
        recs = [dict(zip(rows[0], r)) for r in rows[1:]]
        by = {r["rec_id"]: r for r in recs}
        check("104, updated 12 October (121): screening.csv has exactly the screening's columns, Cited by and its date after "
              "the abstract, its proposal and decision columns empty",
              # updated 13 October (128): Sift's own columns of 13 October after them, and 14 October (133): the
              # record's keywords after the screening's own columns, before them, and its language at the end
              rows[0] == ["rec_id", "title", "authors", "year", "journal", "doi", "pub_type", "sources", "abstract_from", "abstract",
                          "cited_by", "cited_by_date", "proposed_decision", "proposed_reason", "grounds", "decision", "reason",
                          "ft_proposed_decision", "ft_proposed_reason", "ft_grounds", "ft_decision", "ft_reason", "keywords"]
              + ss.OWN_AFTER + ["language"]
              and all(not r[c] for r in recs for c in rows[0][12:22]) and (run_dir / "screening.csv").read_bytes().count(b"\r\n") == 8,
              str(rows[0]))
        check("104: rec_id R001 up in year and title order, two records of one title told apart by their DOIs",
              [(r["rec_id"], r["year"], r["title"]) for r in recs] == [
                  ("R001", "2017", "Digging in: older gardeners"),
                  ("R002", "2018", "Plot holders' wellbeing across a season"),
                  ("R003", "2018", "Plot holders' wellbeing across a season"),
                  ("R004", "2019", "Growing together on the allotment"),
                  ("R005", "2020", "Water butts and neighbours"),
                  ("R006", "2021", "Sheds, soil and solitude"),
                  ("R007", "2022", "Allotment waiting lists and wellbeing")]
              and by["R002"]["doi"] == "10.5555/allot.4" and by["R003"]["doi"] == "10.5555/allot.6",
              str([(r["rec_id"], r["title"][:20]) for r in recs]))
        check("104: deduplicated by the DOI, its case and address set aside, sources joined in the run's order",
              by["R004"]["sources"] == "Scopus; PsycInfo; PubMed; Europe PMC; OpenAlex" and by["R004"]["doi"] == "10.5555/allot.1"
              and by["R006"]["sources"] == "Scopus; Web of Science" and by["R002"]["sources"] == "PubMed"
              and result["records"] == 13 and result["merged"] == 7, str(result["records"]))
        check("104: and by the title and year, a record with no DOI joined to one with, the DOI taken from it",
              by["R005"]["sources"] == "Europe PMC; OpenAlex" and by["R005"]["doi"] == "10.5555/allot.3"
              and by["R005"]["abstract"] == "Gardeners spoke of sharing water in a dry July.", str(by["R005"]))
        fill_asks = [q for p, q in stub_state["asked"] if p == "/works" and q.get("filter", "").startswith("doi:")]
        check("104, updated 12 October (116, 121): an abstract a database lacks is filled from OpenAlex by DOI, and "
              "abstract_from says where each came from, the same request asking for the authors of a record that names one "
              "and for every record's count of citations, a record with its abstract and two names among them",
              by["R006"]["abstract"] == "Nine gardeners talked about their sheds as places to be alone."
              and by["R006"]["abstract_from"] == "OpenAlex" and by["R004"]["abstract_from"] == "Scopus"
              and by["R001"]["abstract_from"] == "PsycInfo" and by["R002"]["abstract_from"] == "PubMed"
              and by["R007"]["abstract"] == "" and by["R007"]["abstract_from"] == "" and result["filled"] == 1
              and any(q.get("select") == ss.FILL_FIELDS and q.get("per-page") == "50"
                      and {"10.5555/allot.2", "10.5555/allot.5", "10.5555/allot.4", "10.5555/allot.1"}
                      <= set(q["filter"][4:].split("|")) for q in fill_asks),
              str(by["R006"])[:200] + str(fill_asks)[:300])
        check("104: a source's markup is taken out of an abstract and PubMed's parts joined",
              by["R002"]["abstract"] == "To hear plot holders. Eight plot holders kept diaries."
              and json.loads((run_dir / "raw_epmc.json").read_text(encoding="utf-8"))[0]["abstract"].startswith("Twelve plot holders"))
        meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        check("104: run.json records the version it ran, each database's state and how, and the export with its version",
              meta["version"] == 3 and meta["draft"] is False and meta["sources"]["scopus"]["how"] == "api"
              and meta["sources"]["psycinfo"]["how"] == "export" and meta["exports"]["psycinfo"]["version"] == 3
              and meta["missed"] == ["10.5555/allot.9"], str(meta["sources"])[:200])
        opened = sift.load(run_dir)
        counted = sift.counts(opened)
        check("104: Sift opens the run's screening as it is, and log.csv gives its records identified",
              opened.ids == [f"R00{i}" for i in range(1, 8)] and counted["searches"]["saved"] == 13
              and counted["searches"]["sources"]["PubMed"] == {"hits": 2, "saved": 2} and counted["flow"]["duplicates"] == 6)
        secrets = [b"els-key-SECRET123", b"wos-key-SECRET456"]
        check("104: no key is written to any file of the run or the plan",
              not any(s in p.read_bytes() for p in list(run_dir.iterdir()) + [review / ss.PLAN_NAME, review / ss.PLAN_MD]
                      for s in secrets))

        # the rerun, 9 October: every run kept, a second run that day beside the first, and a run once begun
        # never written
        (run_dir / "raw_stale.json").write_text("[]", encoding="utf-8")
        first_files = {p.name: p.read_bytes() for p in run_dir.iterdir() if p.is_file()}
        second = ss.run(review, day=day, ctx=ctx())
        run2 = review / "runs" / f"{day}-2"
        check("104, 9 October: a rerun on the same day makes the day's second run beside the first, the first kept byte for "
              "byte, and the export dropped in the first awaited again in the second",
              # named by its number in the order the runs were made since 12 October, later (area 124), the newest run
              second["date"] == f"{day}-2" and second["label"] == f"Run {len(ss.run_dirs(review))}, 3 November 2026" and run2.is_dir()
              and {p.name: p.read_bytes() for p in run_dir.iterdir() if p.is_file()} == first_files
              and len(sift.load(run_dir).ids) == 7 and not (run2 / "psycinfo.ris").exists()
              and json.loads((run2 / "run.json").read_text(encoding="utf-8"))["sources"]["psycinfo"]["state"] == "awaiting",
              str(second.get("date")))
        sift.decide(run_dir, "R004", "ta", "include")

        def refusal(fn):
            try:
                fn()
            except ss.SearchError as exc:
                return str(exc)
            return ""

        third = ss.run(review, day=day, ctx=ctx())
        run3 = review / "runs" / f"{day}-3"
        sift.decide(run3, sift.load(run3).ids[0], "ta", "include")
        drop_said = refusal(lambda: ss.take_export(review, "psycinfo", ris.encode(), "x.ris", day=day, ctx=ctx()))
        (run3 / sift.LOG_NAME).rename(run3 / "kept.jsonl")
        decided = refusal(lambda: ss.take_export(review, "psycinfo", ris.encode(), "x.ris", day=day, ctx=ctx()))
        check("104: a run whose screening has begun is never written: a rerun makes the day's next run, and a drop on the day's "
              "newest run once begun is refused in one line that no longer says to run on another day, nothing touched",
              third["date"] == f"{day}-3" and sift.load(run_dir).cell("R004", "decision") == "include"
              and drop_said == "The run of 3 November 2026, run 3 holds its screening log, so it was left as it is. Run makes a new run."
              and decided.startswith("The run of 3 November 2026, run 3 holds screening decisions") and "\n" not in decided
              and "another day" not in drop_said + decided and not (run3 / "psycinfo.ris").exists(), drop_said)

        # a key echoed back by a refusing server never reaches the log, and Scopus falls back to STANDARD
        stub_state.update(wos_fails=True, scopus_standard_only=True)
        failed = ss.run(review, day="2026-11-04", ctx=ctx())
        with open(review / "runs" / "2026-11-04" / "log.csv", encoding="utf-8", newline="") as fh:
            flog = {r["source"]: r for r in csv.DictReader(fh)}
        wos_note = flog["Web of Science"]["note"]
        check("104: an error is scrubbed of the key before it reaches the log, the run going on without that database",
              "failed: HTTP 401 from" in wos_note and "Invalid key [key] for this API" in wos_note and "SECRET456" not in wos_note
              and flog["Web of Science"]["hits"] == "" and failed["merged"] == 5
              and not any(b"SECRET" in p.read_bytes() for p in (review / "runs" / "2026-11-04").iterdir()), wos_note)
        check("104: a refused COMPLETE view falls back to STANDARD, which gives no abstracts, and says so",
              "COMPLETE view refused, STANDARD used, with no abstracts" in flog["Scopus"]["note"]
              and json.loads((review / "runs" / "2026-11-04" / "raw_scopus.json").read_text(encoding="utf-8"))[0]["abstract"] == "")
        stub_state.update(wos_fails=False, scopus_standard_only=False)
        csv_export = ("Authors,Title,Year,Source title,DOI,Abstract,Author Keywords,Document Type\n"
                      '"Ash E.","Sheds, soil and solitude",2021,Invented Soil Review,10.5555/allot.2,"Nine gardeners, alone.",sheds,Article\n')
        kind, from_csv = ss.read_export(("﻿" + csv_export).encode("utf-8"), "scopus.csv", "Scopus")
        check("104: a CSV export is read by the names its columns go by",
              kind == "csv" and from_csv[0]["title"] == "Sheds, soil and solitude" and from_csv[0]["doi"] == "10.5555/allot.2"
              and from_csv[0]["journal"] == "Invented Soil Review" and from_csv[0]["abstract"] == "Nine gardeners, alone."
              and from_csv[0]["pub_type"] == "Article", str(from_csv)[:200])
        runs_now = ss.runs(review)
        check("104: the runs, newest first in the order they were made, each with its rows, its counts, its missed benchmark "
              "and whether screening began",
              [r["date"] for r in runs_now] == ["2026-11-04", f"{day}-3", f"{day}-2", day]
              and runs_now[1]["begun"] == "screening decisions" and runs_now[3]["begun"] == "its screening log"
              and runs_now[0]["missed"] == ["10.5555/allot.9"] and runs_now[0]["rows"][1]["state"] == "failed"
              and runs_now[3]["merged"] == 7 and runs_now[3]["screening"], str([r["begun"] for r in runs_now]))
        dry = ss.run(review, day="2026-11-05", ctx=ctx(), dry_run=True)
        check("104: a dry run says how each database would go and sends nothing",
              [(s["source"], s["how"]) for s in dry["sources"]] == [("scopus", "api"), ("wos", "api"), ("psycinfo", "export"),
                                                                   ("pubmed", "api"), ("epmc", "api"), ("openalex", "api")]
              and not (review / "runs" / "2026-11-05").exists())
        held.clear()
        no_keys = ss.run(review, day="2026-11-05", ctx=ctx(), dry_run=True)
        check("104: with no key in the keychain Scopus and Web of Science go by export",
              [s["how"] for s in no_keys["sources"]][:2] == ["export", "export"] and ss.keys_set() == {"scopus": False, "wos": False})
        held.update({"ELSEVIER_API_KEY": "els-key-SECRET123", "CLARIVATE_API_KEY": "wos-key-SECRET456"})
        os.environ[ss.STUB_ENV] = "http://192.0.2.1:9"
        elsewhere = ss.stub_base()
        os.environ[ss.STUB_ENV] = stub
        loop = (ss.stub_base(), ss.endpoints()["scopus"], ss.read_key("CLARIVATE_API_KEY"))
        del os.environ[ss.STUB_ENV]
        check("104: the smoke run's stub is taken on a loopback address alone, and then no keychain is read",
              elsewhere == "" and loop == (stub, stub + "/content/search/scopus", "stub-clarivate_api_key")
              and ss.endpoints() == ss.ENDPOINTS)

        # ── D. the command line
        js = lambda argv: (lambda r: (r[0], support.plain(json.loads(r[1])) if r[1].strip().startswith("{") else r[1], r[2]))(cli.run(argv + ["--json"]))
        c_plan = js(["sift", "search", "plan", str(review)])
        c_strings = cli.run(["sift", "search", "strings", str(review), "--version", "1"])
        c_runs = js(["sift", "search", "runs", str(review)])
        c_text = cli.run(["sift", "search", "plan", str(review)])
        check("104: sift search plan, strings and runs read the plan, a version's strings and the runs",
              c_plan[0] == 0 and c_plan[1]["current"]["version"] == 3 and c_plan[1]["plan"]["benchmark"] == ["10.5555/allot.1", "10.5555/allot.9"]
              and c_strings[0] == 0 and "Web of Science:\n  TS=(allotment*) AND TS=(wellbeing)\n  Edited manually: Kept short" in c_strings[1]
              and c_runs[0] == 0 and [r["date"] for r in c_runs[1]["runs"]] == ["2026-11-04", f"{day}-3", f"{day}-2", day]
              and c_text[1].startswith(f"Search plan in {review.name}, version 3, registered "), c_text[1][:120])
        c_reg = cli.run(["sift", "search", "register", str(review)])
        c_wrong = cli.run(["sift", str(review), "plan"])
        c_none = cli.run(["sift", "search", "plan", str(base)])
        check("104: on the command line register refuses a registered plan, an act of search needs search, and a folder with no plan says so",
              c_reg[0] == 1 and c_reg[2].strip() == "Version 3 is registered and unchanged since."
              and c_wrong[2].strip() == "plan is an act of sift search: sift search plan <folder>."
              and c_none[2].strip() == "There is no search plan in that folder yet.", c_wrong[2])
        os.environ[ss.STUB_ENV] = stub
        # his own list of databases, every one Sift has an API for by API (see area 106)
        all_api = base / "all-api-config.json"
        all_api.write_text(json.dumps({"databases": [{"source": s, "how": "api"} for s in ss.APIS]}), encoding="utf-8")
        c_run = js(["sift", "search", "run", str(review), "--date", "2026-11-06", "--config", str(all_api), "--follows", "none"])
        c_dry = cli.run(["sift", "search", "run", str(review), "--date", "2026-11-07", "--dry-run", "--config", str(all_api)])
        del os.environ[ss.STUB_ENV]
        check("104: sift search run runs the newest registered version, and --dry-run says how it would go",
              c_run[0] == 0 and c_run[1]["version"] == 3 and c_run[1]["merged"] == 6
              and (review / "runs" / "2026-11-06" / "screening.csv").is_file()
              and c_dry[0] == 0 and "It would run version 3 into runs/2026-11-07:" in c_dry[1]
              and "PsycInfo: by export, none dropped yet." in c_dry[1] and not (review / "runs" / "2026-11-07").exists(),
              c_dry[1][:200])

        # ── E. MCP: three tools read, one runs the registered plan, none registers or edits
        by_name = {t["name"]: t for t in sift_mcp.SEARCH_TOOLS}
        props = lambda n: set(by_name[n]["inputSchema"]["properties"])
        check("104: four MCP tools for a review's searches, three only reading, the run reaching beyond the machine",
              list(by_name) == ["sift_search_plan", "sift_search_strings", "sift_search_runs", "sift_search_run"]
              and all(t in mcp_server.TOOLS for t in sift_mcp.SEARCH_TOOLS)
              and all(by_name[n]["annotations"]["readOnlyHint"] is True and by_name[n]["annotations"]["openWorldHint"] is False
                      for n in ("sift_search_plan", "sift_search_strings", "sift_search_runs"))
              and by_name["sift_search_run"]["annotations"]["readOnlyHint"] is False
              and by_name["sift_search_run"]["annotations"]["openWorldHint"] is True
              and by_name["sift_search_run"]["annotations"]["destructiveHint"] is False
              and props("sift_search_run") == {"folder", "dry_run", "follows"} and props("sift_search_strings") == {"folder", "version"}
              and all("folder" in t["inputSchema"]["required"] for t in sift_mcp.SEARCH_TOOLS)
              and all(chr(0x2014) not in t["description"] and ";" not in t["description"] for t in sift_mcp.SEARCH_TOOLS))
        # reworded 14 October (134) on Adam's ruling: no tool writes or registers a plan, and a draft carrying
        # his decision is written through Sift's own save
        check("104: no tool registers or edits a plan, and the server's words say so",
              not any(t["command"][1] in ("register", "save") for t in mcp_server.TOOLS)
              and not any({"plan", "blocks", "reason", "databases", "terms", "overrides"} & set(t["inputSchema"]["properties"])
                          for t in sift_mcp.SEARCH_TOOLS)
              and "No tool registers or writes a plan." in mcp_server.instructions("sift")
              and "written through Sift's own save" in mcp_server.instructions("sift")
              and "never register a version, which is his" in mcp_server.instructions("sift"))
        srv = mcp_server.Server(app="sift")
        m_strings = srv.call(by_name["sift_search_strings"], {"folder": str(review), "version": 2})
        m_runs = srv.call(by_name["sift_search_runs"], {"folder": str(review)})
        # the dry run checks truncation since 14 October (134), its counts sent to the stub alone
        os.environ[ss.STUB_ENV] = stub
        m_dry = srv.call(by_name["sift_search_run"], {"folder": str(review), "dry_run": True})
        del os.environ[ss.STUB_ENV]
        m_bad = srv.call(by_name["sift_search_plan"], {"folder": str(review), "plan": {}})
        check("104: through MCP the strings, the runs and a dry run answer as the command line does, and an input it lacks is refused",
              m_strings["isError"] is False and m_strings["structuredContent"]["version"] == 2
              and "PY=(2001-2026)" in m_strings["content"][0]["text"]
              and [r["date"] for r in m_runs["structuredContent"]["runs"]][:2] == ["2026-11-06", "2026-11-04"]
              and m_dry["isError"] is False and m_dry["structuredContent"]["dry_run"] is True
              and m_dry["structuredContent"]["version"] == 3 and m_bad["isError"] is True, str(m_dry)[:200])
        args = mcp_server.arguments(by_name["sift_search_run"], {"folder": str(review)}, {}, "Claude Code")
        check("104: the MCP run is of the newest registered version, never a draft and never a register",
              args.search is True and args.draft is False and args.reason is None and args.act == "run")

        # ── F. the route: New review, read, save, register, run on its thread, progress, a drop and the screening
        kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.PICK_FOLDER,
                server_mod.PLATFORM)
        config_file = base / "config.json"
        config_file.write_text(json.dumps(dict(server_mod.defaults(), databases=[{"source": s, "how": "api"} for s in ss.APIS])),
                               encoding="utf-8")
        try:
            server_mod.CONFIG_PATH = config_file
            server_mod.ROOT_OVERRIDE = str(base)
            server_mod.STATE_MEMORY = {"recent": []}
            fresh = base / "pond-review"
            fresh.mkdir()
            try:
                sift_routes.api_sift_search({"op": "read", "folder": str(fresh)})
                guarded = ""
            except server_mod.OutsideRoot as exc:
                guarded = str(exc)
            server_mod.PLATFORM = "darwin"
            server_mod.PICK_FOLDER = lambda prompt: None
            cancelled = sift_routes.api_sift_review({"op": "folder", "mode": "new"})
            server_mod.PICK_FOLDER = lambda prompt: fresh
            chosen = sift_routes.api_sift_review({"op": "folder", "mode": "new"})
            picked = sift_routes.api_sift_review({"op": "new", "folder": chosen["folder"], "name": "Pond review"})["review"]
            os.environ[ss.STUB_ENV] = stub
            read = sift_routes.api_sift_search({"op": "read", "folder": picked["folder"]})
            check("104: a review is made by New review in the folder from the dialog or a typed path, kept in the list of "
                  "reviews, and none other is read",
                  guarded == sift_routes.REVIEW_NOT_OPENED and cancelled == {"chosen": False} and chosen["chosen"]
                  and server_mod.same_folder(server_mod.abs_path(server_mod.STATE_MEMORY["sift_reviews"][0]["folder"]),
                                             server_mod.abs_path(picked["folder"])) and read["review"]["name"] == "Pond review"
                  and read["current"] is None and read["how"]["scopus"] == "api" and read["how"]["psycinfo"] == "export"
                  and read["catalog"]["scopes"][0] == ["tak", "Title, abstract and keywords"] and read["runs"] == []
                  and "/api/sift-search" in server_mod.POST_ONLY and server_mod.ROUTES["/api/sift-search"] is sift_routes.api_sift_search)
            saved = sift_routes.api_sift_search({"op": "save", "folder": picked["folder"], "plan": {
                "databases": ["pubmed", "openalex", "psycinfo"], "blocks": [{"name": "Ponds", "terms": "pond*\nwild swimming"}]}})
            # Mark as registered names the registry and its number since 12 October, later (area 124)
            reg = sift_routes.api_sift_search({"op": "register", "folder": picked["folder"], "registry": "OSF",
                                              "registration": "https://osf.io/pond1"})
            started = sift_routes.api_sift_search({"op": "run", "folder": picked["folder"]})
            for _ in range(300):
                prog = sift_routes.api_sift_search({"op": "progress", "folder": picked["folder"]})
                if not prog["running"]["running"]:
                    break
                time.sleep(0.05)
            check("104: through the route a plan is saved, registered and run on its own thread, its progress asked after",
                  {s["source"]: s for s in saved["strings"]}["pubmed"]["query"] == '(pond*[tiab] OR "wild swimming"[tiab])' and reg["registered"] == 1
                  and started["started"] and set(started["running"]["sources"]) == {"pubmed", "openalex", "psycinfo"}
                  and prog["running"]["running"] is False and prog["running"]["result"]["merged"] == 4
                  and prog["running"]["sources"]["psycinfo"]["state"] == "awaiting" and prog["runs"][0]["screening"],
                  str(prog)[:300])
            today = read["today"]
            b64 = __import__("base64").b64encode(ris.encode("utf-8")).decode("ascii")
            drop = sift_routes.api_sift_search({"op": "drop", "folder": picked["folder"], "source": "psycinfo", "name": "p.ris", "data": b64})
            nope = refusal_of(lambda: sift_routes.api_sift_search({"op": "drop", "folder": picked["folder"], "source": "pubmed",
                                                                 "name": "p.ris", "data": b64}))
            opened = sift_routes.api_sift_search({"op": "screening", "folder": picked["folder"], "date": today})
            in_sift = sift_routes.api_sift({"op": "read", "folder": opened["folder"]})
            home = sift_routes.review_rows()
            check("104: a drop takes the export into today's run, a keyless database takes none, and the screening opens in Sift",
                  drop["taken"]["records"] == 2 and drop["merged"] == 5 and drop["runs"][0]["date"] == today
                  and nope == "Sift searches that database itself, so it takes no export."
                  and in_sift["review"]["run"] == today and opened["folder"].endswith(today)
                  and home[0]["name"] == "Pond review" and home[0]["version"] == 1 and home[0]["run"]["date"] == today
                  and home[0]["run"]["screening"] is True, str(home)[:200])
        finally:
            os.environ.pop(ss.STUB_ENV, None)
            (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.PICK_FOLDER,
             server_mod.PLATFORM) = kept
    finally:
        ss.Context.__init__ = real_init
        ss.RUNNER = kept_runner
        if kept_env is not None:
            os.environ[ss.STUB_ENV] = kept_env
        httpd.shutdown()
        httpd.server_close()

    # ── G. the page: the way in, the screen's own files, and its words
    check("104: the page loads the screen's own script and styles, and the screen is a review's Search strategy step, its row on "
          "the home screen opening it",
          '<script src="/sift.js"></script>\n<script src="/sift_search.js"></script>' in page
          and '<link rel="stylesheet" href="/sift_search.css">' in page and "else sfsOpen(review.folder);" in sjs
          and "rvOpen(rows[Number(btn.dataset.i)].folder)" in support.text("apps/sift/static/sift_settings.js"))
    check("104: the screen keeps its keys to itself and takes a dropped file on a database's row alone",
          "window.addEventListener('keydown', sfsKeyDown, true)" in sjs and "e.stopPropagation();" in sjs
          and "closest('.sfs-drop')" in sjs)
    check("104: the Mac app packs the module",
          "sift_search" in support.build_mac().modules("sift") and "sift_search" not in support.build_mac().modules("idiograph"))
