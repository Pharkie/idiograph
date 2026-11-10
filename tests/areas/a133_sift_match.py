from __future__ import annotations

import csv
import json
import os
import shutil

from . import support
from .support import check, sift_words_js, skip, urllib_path


def test_sift_match(scratch):
    print("\n133. Sift's terms, 14 October: how a record matched a block when none of its terms is in what Sift holds, "
          "from the databases that found it and the fields each searched, Matched in on the record and as a column, and "
          "the keywords PubMed, Europe PMC and OpenAlex give kept in the run, its screening and Fill from OpenAlex, and "
          "each record's language from its sources, a Language group and column")
    import datetime as dt
    import http.server
    import threading
    import argparse
    import subprocess
    import urllib.parse as up
    import sift
    import sift_search as ss
    import cli as cli_mod
    import sift_cli

    app_src = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    sift_src = support.text("apps/sift/static/sift.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    node = shutil.which("node")
    base = scratch / "sift-match-133"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    # updated 14 October, later (137): the lines in Adam's new words, a field Sift cannot name where None of its
    # terms stood, the databases joined A, B or C
    methods, keywords_line, no_abstract = ("{} methods sections", "{} keywords", "the abstract, which Sift does not hold")
    none_line = "a field Sift cannot name"

    # ── A. the lines, on an invented review of bell ringers: Europe PMC searches the first block in methods
    # sections, Scopus, PubMed and Europe PMC elsewhere in title, abstract and keywords, OpenAlex in title and
    # abstract alone
    review = base / "bell-review"
    review.mkdir()
    ss.new_plan(review, "Bell ringers", "How do ringers live with the tower?")
    dbs = ["scopus", "pubmed", "epmc", "openalex"]
    ss.save(review, {"databases": dbs, "blocks": [
        {"name": "Bells", "terms": ["bell*", '"change ringing"'], "scope": "tak", "scopes": {"epmc": "methods"}},
        {"name": "Towers", "terms": ["tower*"]}]})
    run = review / "runs" / "2031-07-01"
    run.mkdir(parents=True)
    (run / ss.RUN_FILE).write_text(json.dumps({"version": 1, "sources": {s: {"name": ss.NAMES[s]} for s in dbs}}),
                                   encoding="utf-8")
    rows = [("B1", "Ropes in the ringing chamber", "Ringers spoke of the rope and the count.", "Europe PMC", ""),
            ("B2", "Sunday service rotas", "Volunteers kept the rota.", "Scopus", ""),
            ("B3", "Practice nights", "Learners met weekly in the tower.", "Scopus; PubMed", ""),
            ("B4", "Quarter peals", "", "OpenAlex", ""),
            ("B5", "Learning to handle", "", "Europe PMC; Scopus", ""),
            ("B6", "Weekly practice and friendship", "Friends met each week.", "OpenAlex", ""),
            ("B7", "The bells of the market town", "Change ringing as a craft.", "Scopus", ""),
            ("B8", "Learning the methods", "Novices learnt by rote.", "Scopus", "bellringing; heritage"),
            ("B9", "Captains of the band", "Captains led the band.", "Index Z", "")]

    # and each record's language as the review's own side writes it at the end of the header, a code among them
    languages = ["English", "English", "English; Spanish", "Portuguese", "", "English", "", "English", "fr"]

    def write_run(folder: Path, with_keywords: bool) -> None:
        with open(folder / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["rec_id", "title", "authors", "year", "journal", "doi", "sources", "abstract"]
                       + (["keywords", "language"] if with_keywords else []))
            for i, (rec, title, abstract, sources, kws) in enumerate(rows, 1):
                w.writerow([rec, title, "Peal, Quin", str(2020 + i), "Invented Belfry Journal", f"10.5555/bell.{i}", sources,
                            abstract] + ([kws, languages[i - 1]] if with_keywords else []))

    write_run(run, True)
    view = sift.screen(run)
    rec = {r["rec_id"]: r for r in view["records"]}
    why = lambda r, k="term:0": [w["label"] for w in rec[r]["matched"][k]["why"]]
    check("133: a record found by Europe PMC alone, which searched the block in methods sections, with none of its terms "
          "in its title, abstract or keywords, says Europe PMC methods sections",
          why("B1") == [methods.format("Europe PMC")] and rec["B1"]["terms"]["term:0"] == [], str(rec["B1"]["matched"]))
    check("133: one found by databases that search their own keyword or index fields says their keywords, naming those "
          "of its databases joined by or, Europe PMC there for a block it searched in title, abstract and keywords",
          why("B2") == [keywords_line.format("Scopus")] and why("B3") == [keywords_line.format("Scopus or PubMed")]
          and why("B1", "term:1") == [keywords_line.format("Europe PMC")], str([why("B2"), why("B3")]))
    check("133: an empty abstract says the abstract, which Sift does not hold, a record that fits all three shows each, "
          "and one no database's fields explain stands under a field Sift cannot name",
          why("B4") == [no_abstract]
          and why("B5") == [methods.format("Europe PMC"), keywords_line.format("Scopus"), no_abstract]
          and why("B6") == [none_line] and why("B9") == [none_line]
          and rec["B6"]["terms"]["term:0"] == [] and rec["B9"]["terms"]["term:0"] == [],
          str([why("B4"), why("B5"), why("B6")]))
    check("133: a record holding the block's terms keeps its term lines, with where they were found, Title, Abstract or "
          "Keywords, and no line of why",
          rec["B7"]["terms"]["term:0"] == ["bell*", '"change ringing"'] and rec["B7"]["matched"]["term:0"] == {"in": ["Title", "Abstract"], "why": []}
          and rec["B3"]["matched"]["term:1"] == {"in": ["Abstract"], "why": []}
          and rec["B9"]["matched"]["term:1"]["in"] == [] and rec["B9"]["terms"]["term:1"] == [],
          str(rec["B7"]["matched"]))
    check("133: a term found in the new keywords column moves a record out of the lines, matched in Keywords",
          rec["B8"]["terms"]["term:0"] == ["bell*"] and rec["B8"]["matched"]["term:0"] == {"in": ["Keywords"], "why": []},
          str(rec["B8"]["matched"]))
    check("133: the block's group carries each line with the databases of every record under it, in the plan's order, "
          "the methods, the keywords, no abstract and a field Sift cannot name",
          view["blocks"][0]["why"] == [{"value": "|methods", "label": methods.format("Europe PMC")},
                                       {"value": "|keywords", "label": keywords_line.format("Scopus or PubMed")},
                                       {"value": "|noabstract", "label": no_abstract}, {"value": "|none", "label": none_line}]
          and view["blocks"][1]["label"] == "Block 2, Towers", str(view["blocks"]))
    beyond = {(s, p): ss.beyond_text({"scope": "tak", "scopes": {}}, s, {"platforms": {s: p}} if p else {})
              for s, p in (("scopus", ""), ("wos", ""), ("pubmed", ""), ("epmc", ""), ("openalex", ""), ("psycinfo", "ovid"),
                           ("cinahl", "ebsco"), ("cinahl", "ovid"), ("cinahl", "proquest"), ("embase", ""), ("scholar", ""))}
    check("133: what each database searched beyond the title and abstract: keyword or index fields for all but OpenAlex "
          "and CINAHL on Ovid or ProQuest, methods sections where asked of Europe PMC, and Google Scholar's whole text, which "
          "the full-text line names since 14 October (134)",
          [k for k, v in beyond.items() if v == "keywords"] == [("scopus", ""), ("wos", ""), ("pubmed", ""), ("epmc", ""),
                                                               ("psycinfo", "ovid"), ("cinahl", "ebsco"), ("embase", "")]
          and beyond[("openalex", "")] == "" and beyond[("cinahl", "ovid")] == "" and beyond[("scholar", "")] == "fulltext"
          and ss.beyond_text({"scope": "tak", "scopes": {"epmc": "methods"}}, "epmc", {}) == "methods"
          and ss.beyond_text({"scope": "methods", "scopes": {}}, "scopus", {}) == "keywords", str(beyond))
    shown = sift_cli.cmd_sift(argparse.Namespace(folder=str(run), act="show", rec_id="B5", stage="ta", search=False))[1]
    shown7 = sift_cli.cmd_sift(argparse.Namespace(folder=str(run), act="show", rec_id="B7", stage="ta", search=False))[1]
    # updated 14 October, later (137): the record's sentence for each block holding none of its terms
    check("133: the command line's show says each line, and Matched in for a block whose terms it holds",
          "Block 1, Bells: none in the title or abstract. Europe PMC matched at least one in its methods sections, which "
          "Sift does not hold, so Sift cannot say which. Scopus matched at least one in its keywords, which Sift does not "
          "hold, so Sift cannot say which. The database matched at least one in the abstract, which Sift does not hold."
          in shown and 'Block 1, Bells: bell*, "change ringing". Matched in Title, Abstract.' in shown7
          and "Block 2, Towers: none in the title or abstract. Scopus matched at least one in its keywords, which Sift "
          "does not hold, so Sift cannot say which." in shown7, "\n".join(shown + shown7))
    cols = sift.table_settings(run)["columns"]
    check("133: Matched in is a column of Set columns, hidden at first, after Cites key works",
          ("matched", False) in sift.TABLE_COLUMNS and {"key": "matched", "shown": False} in cols
          and [c["key"] for c in cols].index("matched") == [c["key"] for c in cols].index("keyworks") + 1, str(cols))
    check("133: a language column the review's own side wrote is read and kept as written, each record's languages "
          "by their English names, a code among them, and Language a column of Set columns after Country, hidden at "
          "first, never a second column of the review's",
          rec["B3"]["language"] == ["English", "Spanish"] and rec["B9"]["language"] == ["French"] and rec["B5"]["language"] == []
          and sift.load(run).cell("B9", "language") == "fr" and ("language", False) in sift.TABLE_COLUMNS
          and [c["key"] for c in cols].index("language") == [c["key"] for c in cols].index("country") + 1
          and {"key": "language", "shown": False} in cols and "csv:language" not in [c["key"] for c in cols]
          and ["language", "French"] in rec["B9"]["more"],
          str([rec[r]["language"] for r in ("B3", "B9", "B5")]))
    check("133: the codes of each source become English names by Sift's own map, ISO 639-1 and 639-2 alike, an "
          "unknown code kept as given, undetermined as none, several parted as several choices are",
          [sift.language_name(c) for c in ("eng", "en", "por", "pt", "spa", "es", "fre", "fra", "fr", "ger", "deu", "de",
                                           "ita", "it", "dut", "nld", "nl", "english", "qqx", "und")]
          == ["English"] * 2 + ["Portuguese"] * 2 + ["Spanish"] * 2 + ["French"] * 3 + ["German"] * 3 + ["Italian"] * 2
          + ["Dutch"] * 3 + ["English", "qqx", ""]
          and sift.language_cell(["eng", "spa", "en"]) == "English; Spanish" and sift.language_cell("") == "")

    # an old run, made before the column, still read: its raw files' keywords as before, and a record whose
    # keywords neither holds stands under its databases' lines
    old = review / "runs" / "2031-07-02"
    old.mkdir(parents=True)
    write_run(old, False)
    view_old = {r["rec_id"]: r for r in sift.screen(old)["records"]}
    (old / "raw_scopus.json").write_text(json.dumps([{"doi": "10.5555/bell.8", "title": "Learning the methods",
                                                      "keywords": "bellringing; heritage"}]), encoding="utf-8")
    view_raw = {r["rec_id"]: r for r in sift.screen(old)["records"]}
    check("133: an old run with no keywords column and no run.json is still read, a record found by Scopus under the "
          "keywords line until the raw files give its keywords, then matched in Keywords",
          "keywords" not in sift.load(old).header
          and [w["label"] for w in view_old["B8"]["matched"]["term:0"]["why"]] == [keywords_line.format("Scopus")]
          and view_raw["B8"]["matched"]["term:0"] == {"in": ["Keywords"], "why": []}
          and [w["label"] for w in view_raw["B1"]["matched"]["term:0"]["why"]] == [methods.format("Europe PMC")],
          str(view_old["B8"]["matched"]))

    # ── B. the page: the group's counts and order, the record and the column, in node
    if not node:
        skip("133: the group, the record and the column in node", "node is not installed")
    else:
        lead = app_src[app_src.index("const esc = "):app_src.index("// a line from the server with a command in backticks")]
        block = sift_src.split("/* ── the table's rows: its columns, sort and filter, worked out with no page ── */", 1)[-1].split(
            "/* ── the table, drawn ── */", 1)[0]
        block = support.table_js() + "\n" + block
        harness = r"""
const els = {};
const mk = () => ({ hidden: false, innerHTML: '', textContent: '', title: '', dataset: {}, style: {}, setAttribute() {} });
const $ = (id) => els[id] || (els[id] = mk());
const VIEW = __VIEW__;
const SF = { stage: 'ta', filters: {}, table: VIEW.table, records: VIEW.records, blocks: VIEW.blocks, keyWorks: [],
  reasons: { ta: [], ft: [] }, roundIds: VIEW.records.map((r) => r.rec_id), form: false, formBench: new Set(), formInc: new Set() };
SF.byId = new Map(SF.records.map((r) => [r.rec_id, r]));
const cols = sfAllCols();
const groups = sfGroups(SF.records, SF.records, cols, 'ta', [], {});
const counts = tbFacetCounts(SF.records, groups, {}, sfRead('ta'));
const g = groups.find((x) => x.key === 'term:0');
const out = {};
out.order = sfFacetOrder(g, counts['term:0']).map((c) => [c.value, c.label, counts['term:0'][c.value] || 0]);
out.keywords = tbFilterRows(SF.roundIds, SF.byId, { 'term:0': ['|keywords'] }, cols, sfRead('ta'));
out.none = tbFilterRows(SF.roundIds, SF.byId, { 'term:0': ['|none'] }, cols, sfRead('ta'));
const lg = groups.find((x) => x.key === 'language');
out.language = lg ? sfFacetOrder(lg, counts.language).map((c) => [c.value, c.label, counts.language[c.value] || 0]) : null;
out.spanish = tbFilterRows(SF.roundIds, SF.byId, { language: ['spanish'] }, cols, sfRead('ta'));
const lcol = cols.find((c) => c.key === 'language');
out.langCol = lcol ? [lcol.label, lcol.shown, sfTvCell(SF.byId.get('B3'), lcol), sfTvCell(SF.byId.get('B5'), lcol)] : null;
out.pane = {};
['B5', 'B7', 'B9'].forEach((id) => { sfTermsDraw(SF.byId.get(id)); out.pane[id] = $('sf-terms').innerHTML; });
const col = cols.find((c) => c.key === 'matched');
out.col = col ? [col.label, col.shown, sfPickable(col, SF.records)] : null;
out.cell = sfTvCell(SF.byId.get('B7'), col);
out.value = ['B7', 'B5', 'B9'].map((id) => sfValue(SF.byId.get(id), col, 'ta'));
SF.blocks = [VIEW.blocks[0]];
out.one = ['B7', 'B5', 'B9'].map((id) => sfValue(SF.byId.get(id), col, 'ta'));
SF.blocks = [];
out.noPlan = [sfValue(SF.byId.get('B7'), col, 'ta'), sfTvCell(SF.byId.get('B7'), col)];
console.log(JSON.stringify(out));
"""
        script = base / "match-133.js"
        script.write_text("\n".join([lead, sift_words_js(sift_src), block, whole(sift_src, "sfTvCell"),
                                     whole(sift_src, "sfTermsDraw"), harness.replace("__VIEW__", json.dumps(view))]),
                          encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        said = (ran.stderr or json.dumps(out))[:500]
        # updated 14 October, later (137): the terms by their counts, then More than one, then the lines by their
        # counts among themselves, a field Sift cannot name among them where None of its terms stood
        check("133: in node, the block's group shows its terms by their counts, then More than one, then the lines with "
              "their counts, the keywords line at 3 first among them, a tie in the group's order, a field Sift cannot "
              "name at 2 among them",
              out.get("order") == [["bell*", "bell*", 2], ['"change ringing"', '"change ringing"', 1], ["|many", "More than one", 1],
                                   ["|keywords", keywords_line.format("Scopus or PubMed"), 3],
                                   ["|methods", methods.format("Europe PMC"), 2], ["|noabstract", no_abstract, 2],
                                   ["|none", none_line, 2]], said)
        check("133: in node, a line ticked keeps the records under it, a record fitting two under each, and a field Sift "
              "cannot name the rest",
              out.get("keywords") == ["B2", "B3", "B5"] and out.get("none") == ["B6", "B9"], said)
        dot = " · "
        check("133: in node, Matched in is a column hidden at first that no filter group takes, each block's words on its "
              "own line after its name with several blocks, the filters' own words parted by a middle dot, the words "
              "alone with one, and nothing with no plan",
              out.get("col") == ["Matched in", False, False]
              and out.get("value") == ["Block 1, Bells: Title, Abstract\nBlock 2, Towers: " + keywords_line.format("Scopus"),
                                       "Block 1, Bells: " + dot.join([methods.format("Europe PMC"), keywords_line.format("Scopus"),
                                                                      no_abstract])
                                       + "\nBlock 2, Towers: " + dot.join([keywords_line.format("Scopus or Europe PMC"), no_abstract]),
                                       f"Block 1, Bells: {none_line}\nBlock 2, Towers: {none_line}"]
              and out.get("one") == ["Title, Abstract", dot.join([methods.format("Europe PMC"), keywords_line.format("Scopus"),
                                                                   no_abstract]), none_line]
              and out.get("noPlan") == ["", '<td class="sf-c-long sf-c-matched"></td>']
              and 'class="sf-c-long sf-c-matched">Block 1, Bells: Title, Abstract' in out.get("cell", ""), said)
        check("133: in node, Language is a group of the filters by its counts, English at 5 first, Unknown at 2, then "
              "French, Portuguese and Spanish at 1 each, a record of two languages under each, and a column hidden at "
              "first, Unknown faint where no source gave one",
              out.get("language") == [["english", "English", 5], ["|none", "Unknown", 2], ["french", "French", 1],
                                      ["portuguese", "Portuguese", 1], ["spanish", "Spanish", 1]]
              and out.get("spanish") == ["B3"]
              and out.get("langCol") == ["Language", False, '<td class="sf-c-language">English, Spanish</td>',
                                         '<td class="sf-c-language"><span class="sf-blank">Unknown</span></td>'], said)

    # ── C. the keywords and the language each database gives, kept in the run, its screening and Fill from OpenAlex
    state = {"asked": []}
    pubmed_xml = {
        "7001": ("Ringing the changes", "10.5555/bell.11", "<KeywordList Owner=\"NOTNLM\"><Keyword>bell ringing</Keyword>"
                 "<Keyword>volunteering</Keyword></KeywordList>", "<MeshHeadingList><MeshHeading><DescriptorName UI=\"D1\">Music"
                 "</DescriptorName></MeshHeading><MeshHeading><DescriptorName UI=\"D2\">Volunteers</DescriptorName><QualifierName>"
                 "psychology</QualifierName></MeshHeading><MeshHeading><DescriptorName UI=\"D3\">volunteering</DescriptorName>"
                 "</MeshHeading></MeshHeadingList>", "<Language>eng</Language><Language>spa</Language>"),
        "7002": ("Belfry stairs", "10.5555/bell.13", "", "", "<Language>por</Language>"),
    }
    epmc = [{"id": "71", "source": "MED", "title": "Ringing the changes", "authorString": "Peal Q.", "pubYear": "2021",
             "doi": "10.5555/bell.11", "abstractText": "Ringers spoke of the rope.", "keywordList": {"keyword": ["bell ringing", "towers"]},
             "language": "eng"},
            {"id": "72", "source": "MED", "title": "Handbells at home", "authorString": "Peal Q.", "pubYear": "2022",
             "doi": "10.5555/bell.12", "abstractText": "Families rang at home.", "keywordList": {"keyword": ["handbells"]},
             "language": "fre"}]
    # OpenAlex detects English for the paper Europe PMC says is French
    alex = [{"id": "https://openalex.org/W12", "doi": "https://doi.org/10.5555/bell.12", "title": "Handbells at home",
             "publication_year": 2022, "type": "article", "authorships": [{"author": {"display_name": "Quin Peal"}}],
             "primary_location": {"source": {"display_name": "Invented Belfry Journal"}}, "language": "en",
             "keywords": [{"id": "https://openalex.org/keywords/handbell-ringing", "display_name": "Handbell ringing", "score": 0.7},
                          {"display_name": "Music education", "score": 0.4}, {"display_name": "Home", "score": 0.3}]}]
    by_doi = {"10.5555/bell.11": {"keywords": [{"display_name": "Never written over"}], "language": "de"},
              "10.5555/bell.13": {"keywords": [{"display_name": "Church towers"}, {"display_name": "Heritage"}], "language": "en"}}

    class Stub(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, body, ctype="application/json"):
            data = body.encode("utf-8") if isinstance(body, str) else json.dumps(body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            url = up.urlparse(self.path)
            q = {k: v[0] for k, v in up.parse_qs(url.query).items()}
            state["asked"].append((url.path, q))
            if url.path.endswith("/esearch.fcgi"):
                return self.send({"esearchresult": {"count": "2", "idlist": sorted(pubmed_xml)}})
            if url.path.endswith("/efetch.fcgi"):
                parts = []
                for pmid in q.get("id", "").split(","):
                    title, doi, kws, mesh, langs = pubmed_xml[pmid]
                    parts.append(f"<PubmedArticle><MedlineCitation><PMID>{pmid}</PMID><Article><Journal><JournalIssue><PubDate>"
                                 "<Year>2021</Year></PubDate></JournalIssue><Title>Invented Belfry Journal</Title></Journal>"
                                 f"<ArticleTitle>{title}</ArticleTitle><Abstract><AbstractText>Ringers spoke of the rope."
                                 "</AbstractText></Abstract><AuthorList><Author><LastName>Peal</LastName><Initials>Q</Initials>"
                                 f"</Author></AuthorList>{langs}</Article>{mesh}{kws}</MedlineCitation><PubmedData><ArticleIdList>"
                                 f"<ArticleId IdType=\"doi\">{doi}</ArticleId></ArticleIdList></PubmedData></PubmedArticle>")
                return self.send("<PubmedArticleSet>" + "".join(parts) + "</PubmedArticleSet>", "text/xml")
            if url.path.endswith("/europepmc/webservices/rest/search"):
                return self.send({"hitCount": len(epmc), "nextCursorMark": "*", "resultList": {"result": epmc}})
            if url.path == "/api.crossref.org/works":
                return self.send({"status": "ok", "message": {"items": []}})
            if url.path == "/works" and q.get("filter", "").startswith("doi:"):
                found = [{"id": "https://openalex.org/W" + d[-2:], "doi": "https://doi.org/" + d, **by_doi[d]}
                         for d in q["filter"][4:].split("|") if d in by_doi]
                return self.send({"meta": {"count": len(found)}, "results": found})
            if url.path == "/works":
                return self.send({"meta": {"count": len(alex), "next_cursor": None}, "results": alex})
            return self.send({})

    kept_clock, kept_env, kept_runner = ss.CLOCK, os.environ.pop(ss.STUB_ENV, None), ss.RUNNER
    ss.CLOCK = lambda: dt.date(2031, 7, 3)
    ss.RUNNER = lambda argv, **_: ss.Done(44, "\n")
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    stub = f"http://127.0.0.1:{httpd.server_address[1]}"
    ctx = lambda: ss.Context(base={s: stub + urllib_path(u) for s, u in ss.ENDPOINTS.items()}, pause=lambda s: None)
    try:
        searched = base / "belfry-review"
        searched.mkdir()
        ss.new_plan(searched, "Belfries", "How do ringers live with the belfry?")
        ss.save(searched, {"databases": ["pubmed", "epmc", "openalex"],
                           "blocks": [{"name": "Bells", "terms": ["bell*", "ring*"]}, {"name": "Towers", "terms": ["tower*"]}]})
        ss.register(searched)
        ss.run(searched, day="2031-07-03", ctx=ctx())
        made = searched / "runs" / "2031-07-03"
        raw = {s: json.loads((made / f"raw_{s}.json").read_text(encoding="utf-8")) for s in ("pubmed", "epmc", "openalex")}
        check("133: the keywords are kept in the run's raw records from each database's stubbed answer: PubMed's "
              "KeywordList and its MeSH headings, each once, Europe PMC's keywordList and OpenAlex's keywords by their names",
              raw["pubmed"][0]["keywords"] == "bell ringing; volunteering; Music; Volunteers" and raw["pubmed"][1]["keywords"] == ""
              and raw["epmc"][0]["keywords"] == "bell ringing; towers" and raw["epmc"][1]["keywords"] == "handbells"
              and raw["openalex"][0]["keywords"] == "Handbell ringing; Music education; Home", str(raw["pubmed"])[:300])
        sc = sift.load(made)
        kw = {sc.cell(r, "doi"): sc.cell(r, "keywords") for r in sc.ids}
        asked = [q for p, q in state["asked"] if p == "/works"]
        check("133: screening.csv holds a keywords column after the screening's own, the fullest list across the databases "
              "kept on merge as for authors, a record with none filled from OpenAlex, one with some never written over",
              sc.header[sc.header.index("ft_reason") + 1] == "keywords"
              and kw == {"10.5555/bell.11": "bell ringing; volunteering; Music; Volunteers",
                         "10.5555/bell.12": "Handbell ringing; Music education; Home", "10.5555/bell.13": "Church towers; Heritage"}
              and asked[0].get("select") == ss.OPENALEX_FIELDS and "keywords" in ss.OPENALEX_FIELDS.split(",")
              and any(q.get("select") == ss.FILL_FIELDS for q in asked) and "keywords" in ss.FILL_FIELDS.split(",")
              and "keywords" in ss.OWN_FIELDS.split(","), str(kw))
        sv = {r["doi"]: r for r in sift.screen(made)["records"]}
        check("133: the terms read the column, Belfry stairs matched in Keywords by OpenAlex's Church towers, and the "
              "record shows its keywords",
              sv["10.5555/bell.13"]["matched"]["term:1"] == {"in": ["Keywords"], "why": []}
              and ["keywords", "Church towers; Heritage"] in sv["10.5555/bell.13"]["more"], str(sv["10.5555/bell.13"]["matched"]))
        lang = {sc.cell(r, "doi"): sc.cell(r, "language") for r in sc.ids}
        check("133: the language is kept in the raw records from each source's own field by its English name, PubMed's "
              "two Language elements both, and screening.csv holds it at the end of the header, a record's own metadata "
              "kept over OpenAlex's detection and OpenAlex's fill by DOI only where no database gave one",
              raw["pubmed"][0]["language"] == "English; Spanish" and raw["pubmed"][1]["language"] == "Portuguese"
              and raw["epmc"][1]["language"] == "French" and raw["openalex"][0]["language"] == "English"
              and sc.header[-1] == "language" and sv["10.5555/bell.11"]["language"] == ["English", "Spanish"]
              and lang == {"10.5555/bell.11": "English; Spanish", "10.5555/bell.12": "French", "10.5555/bell.13": "Portuguese"}
              and all("language" in f.split(",") for f in (ss.OPENALEX_FIELDS, ss.FILL_FIELDS, ss.OWN_FIELDS)), str(lang))
        one = lambda source, language: ss.record(source, "", "Bells abroad", "", "2030", "", "10.5555/bell.20", "", "",
                                                 language=language)
        orders = [ss.merge([one("Europe PMC", "fre"), one("PubMed", "eng")])[0]["language"],
                  ss.merge([one("OpenAlex", "en"), one("Scopus", ""), one("PsycInfo", "ger")])[0]["language"],
                  ss.merge([one("Scopus", "ita"), one("Web of Science", "spa")])[0]["language"],
                  ss.merge([one("OpenAlex", "en"), one("Embase", "dut")])[0]["language"],
                  ss.merge([one("OpenAlex", "en"), one("Scopus", "")])[0]["language"]]
        # an earlier run's record a later run follows: its language kept, or one it lacks taken by the same order
        anchor = dict({k: "" for k in ("authors", "journal", "abstract", "pub_type", "abstract_from", "url", "keywords",
                                       "language")}, title="Bells abroad", year="2030", doi="10.5555/bell.20", rec_id="R001",
                      sources=["Index Z"])
        orders += [ss.merge([one("OpenAlex", "en"), one("PubMed", "por")], anchors=[anchor])[0]["language"],
                   ss.merge([one("PubMed", "por")], anchors=[dict(anchor, language="Welsh")])[0]["language"]]
        check("133: a merged record's language follows PubMed, Europe PMC, PsycInfo, Web of Science, then Scopus, any "
              "other database after them and OpenAlex's detection last, whatever order the run found them in, and a "
              "record carried from an earlier run keeps its own",
              orders == ["English", "German", "Spanish", "Dutch", "English", "Portuguese", "Welsh"]
              and ss.LANGUAGE_ORDER == ("PubMed", "Europe PMC", "PsycInfo", "Web of Science", "Scopus"), str(orders))
        exported = [ss.read_ris("TY  - JOUR\nTI  - Bells abroad\nLA  - spa\nER  - \n", "PsycInfo")[0]["language"],
                    ss.read_csv_export("Title,Language\nBells abroad,Portuguese\n", "CINAHL")[0]["language"],
                    ss.read_csv_export("Title,LA\nBells abroad,ger\n", "Web of Science")[0]["language"],
                    ss.read_csv_export("Title,Language of Original Document\nBells abroad,English\n", "Scopus")[0]["language"],
                    ss.read_bib("@article{k1, title={Bells abroad}, language={italian}}", "Index Z")[0]["language"]]
        check("133: an export's language is read from a RIS export's LA, a CSV export's language or la column and a "
              "BibTeX language field",
              exported == ["Spanish", "Portuguese", "German", "English", "Italian"], str(exported))

        # Fill from OpenAlex for a screening made before the column: Sift's own columns there, only the keywords lacking
        before = base / "belfry-before"
        before.mkdir()
        with open(before / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["rec_id", "title", "authors", "year", "journal", "doi", "sources", "abstract", "cited_by",
                        "cited_by_date", "openalex_date", "crossref_date"])
            w.writerow(["F1", "Belfry stairs", "Peal, Quin", "2021", "Invented Belfry Journal", "10.5555/bell.13", "PubMed",
                        "Ringers spoke of the rope.", "4", "2031-07-01", "2031-07-01", "2031-07-01"])
            w.writerow(["F2", "Clappers", "Peal, Quin", "2022", "Invented Belfry Journal", "10.5555/bell.14", "PubMed",
                        "Clappers wear.", "1", "2031-07-01", "2031-07-01", "2031-07-01"])
        sift.write_references(before, {"F1": {"crossref": [], "openalex": []}, "F2": {"crossref": [], "openalex": []}})
        plan_before = ss.fill_plan(before)
        state["asked"] = []
        filled = ss.fill_columns(before, 0, ctx())
        after = sift.load(before)
        check("133: Fill from OpenAlex fills the keywords of a record that lacks them, the column added, asking OpenAlex "
              "alone, a record OpenAlex gives none for asked again next time",
              plan_before["missing"] == 2 and filled["asked"] == 2 and filled["filled"] == 1
              and after.cell("F1", "keywords") == "Church towers; Heritage" and after.cell("F2", "keywords") == ""
              and [p for p, _ in state["asked"]] == ["/works"] and ss.fill_plan(before)["missing"] == 1, str(filled))
        sift.write_filled(before, {"F1": {"keywords": "Something else", "language": "Welsh"}})
        check("133: a fill never writes over keywords or a language a record holds, and adds the language column at the "
              "end of the header with OpenAlex's English",
              sift.load(before).cell("F1", "keywords") == "Church towers; Heritage" and sift.load(before).cell("F1", "language") == "English"
              and sift.load(before).header[-1] == "language", str(sift.load(before).header[-3:]))

        # a screening whose language column the review's own side wrote, in its own place: kept where it is, a value
        # there kept, and only the empty cell filled
        side = base / "belfry-side"
        side.mkdir()
        with open(side / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["rec_id", "title", "authors", "year", "journal", "doi", "sources", "abstract", "language", "cited_by",
                        "cited_by_date", "openalex_date", "crossref_date"])
            w.writerow(["S1", "Belfry stairs", "Peal, Quin", "2021", "Invented Belfry Journal", "10.5555/bell.13", "PubMed",
                        "Ringers spoke of the rope.", "", "4", "2031-07-01", "2031-07-01", "2031-07-01"])
            w.writerow(["S2", "Ringing the changes", "Peal, Quin", "2021", "Invented Belfry Journal", "10.5555/bell.11", "PubMed",
                        "Ringers spoke of the rope.", "Spanish", "1", "2031-07-01", "2031-07-01", "2031-07-01"])
        sift.write_references(side, {"S1": {"crossref": [], "openalex": []}, "S2": {"crossref": [], "openalex": []}})
        ss.fill_columns(side, 0, ctx())
        kept_side = sift.load(side)
        check("133: a language column the review's own side wrote stays in its place, its values kept, and Fill from "
              "OpenAlex fills only its empty cell",
              kept_side.header.index("language") == 8 and kept_side.header.count("language") == 1
              and kept_side.cell("S2", "language") == "Spanish" and kept_side.cell("S1", "language") == "English",
              str(kept_side.header))
    finally:
        httpd.shutdown()
        ss.CLOCK, ss.RUNNER = kept_clock, kept_runner
        if kept_env is not None:
            os.environ[ss.STUB_ENV] = kept_env

