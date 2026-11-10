from __future__ import annotations

import csv
import json
import os
import shutil

from . import support
from .support import check, refusal_of, sift_words_js, skip, urllib_path


@support.as_app("sift")
def test_sift_terms(scratch):
    print("\n134. Sift's truncation safeguards, 14 October: a phrase holding truncation refused at entry, save and run, the "
          "dry run's truncation check with Adam's two flags and dry_run_terms.csv when a run follows, the rewrites beside "
          "each string, and Found in the full text among the match lines")
    import argparse
    import datetime as dt
    import http.server
    import subprocess
    import threading
    import time
    import urllib.parse as up
    import cli as cli_mod
    import sift_cli
    import mcp_server
    import sift_mcp
    import server as server_mod
    import sift_routes
    import sift
    import sift_search as ss

    app_src = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    sjs = support.text("apps/sift/static/sift_search.js")
    sift_src = support.text("apps/sift/static/sift.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    node = shutil.which("node")
    base = scratch / "sift-terms-134"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    line = ("Truncation inside a phrase works in Scopus and PubMed but not in Europe PMC or OpenAlex. "
            "Write each form of the phrase as its own term.")

    # ── A. entry: a phrase holding truncation refused, a word keeping its asterisk, on an invented review of garden sheds
    said = {t: ss.parse_term(t) for t in ('"garden shed*"', "garden shed*", '"pott?ng bench"', "shed*", "pott?ng", '"garden shed"')}
    check("134: a quoted phrase or one of several words holding * or ? is refused with Adam's line after the term, and a "
          "single word keeps its asterisk or question mark",
          ss.PHRASE_TRUNCATION == line and said['"garden shed*"'] == (None, f'"garden shed*": {line}')
          and said["garden shed*"] == (None, f"garden shed*: {line}") and said['"pott?ng bench"'][1].endswith(line)
          and said["shed*"] == ({"text": "shed*", "phrase": False}, "") and said["pott?ng"][0] == {"text": "pott?ng", "phrase": False}
          and said['"garden shed"'] == ({"text": "garden shed", "phrase": True}, ""), str(said))
    bad = {"databases": ["scopus", "pubmed", "epmc", "openalex"],
           "blocks": [{"name": "Sheds", "terms": ["shed*", '"garden shed*"']}, {"name": "Solitude", "terms": ["solitud*"]}]}
    good = dict(bad, blocks=[{"name": "Sheds", "terms": ["shed*", '"garden shed"', '"garden sheds"']},
                             {"name": "Solitude", "terms": ["solitud*", "quiet"], "scopes": {"epmc": "methods"}}],
                years={"from": 2010}, types=["article"])
    cleaned = ss.clean_plan(bad)
    check("134: the plan's problems name the term by its block, under the block as well, and the plan keeps it as typed",
          f'Sheds: "garden shed*": {line}' in ss.problems(cleaned) and ss.block_problems(cleaned)[0] == [f'"garden shed*": {line}']
          and ss.phrase_problems(cleaned) == [f'Sheds: "garden shed*": {line}'] and cleaned["blocks"][0]["terms"][1] == '"garden shed*"'
          and "garden shed" not in ss.written(cleaned, "scopus")["query"], str(ss.problems(cleaned)))
    review = base / "shed-review"
    review.mkdir()
    ss.new_plan(review, "Garden sheds", "How do gardeners live with their sheds?")
    before = (review / ss.PLAN_NAME).read_bytes()
    try:
        ss.save(review, bad)
        refused = None
    except ss.Unsaved as exc:
        refused = exc
    check("134: a save of a plan holding such a phrase is refused and nothing is written, the refusal carrying what the "
          "screen draws",
          refused is not None and str(refused) == f'Sheds: "garden shed*": {line}' and refused.lines == [str(refused)]
          and refused.view["block_problems"][0] == [f'"garden shed*": {line}'] and isinstance(refused, ss.SearchError)
          and (review / ss.PLAN_NAME).read_bytes() == before, str(refused))
    saved = ss.save(review, good)
    check("134: written in full, each form its own term, the plan saves, with no problem left",
          saved["problems"] == [] and saved["current"]["version"] == 1 and saved["plan"]["blocks"][0]["terms"][1:] == [
              '"garden shed"', '"garden sheds"'] and saved["truncated"] == 2, str(saved["problems"]))

    # a plan saved before the rule, holding such a phrase, is neither registered nor run, on any route
    old = base / "old-shed-review"
    old.mkdir()
    ss.new_plan(old, "Old sheds")
    data = json.loads((old / ss.PLAN_NAME).read_text(encoding="utf-8"))
    data["versions"] = [{"version": 1, "saved": "2031-06-01T10:00:00+01:00", "registered": "2031-06-01T11:00:00+01:00",
                         "reason": "", "plan": ss.clean_plan(bad)}]
    (old / ss.PLAN_NAME).write_text(json.dumps(data), encoding="utf-8")
    old_bytes = (old / ss.PLAN_NAME).read_bytes()
    reg = refusal_of(lambda: ss.register(old))
    ran = refusal_of(lambda: ss.run(old, ctx=ss.Context(base={}, pause=lambda s: None), dry_run=True))
    c_run = cli_mod.run(["sift", "search", "run", str(old), "--dry-run"])
    c_plan = cli_mod.run(["sift", "search", "plan", str(old)])
    run_tool = next(t for t in sift_mcp.SEARCH_TOOLS if t["name"] == "sift_search_run")
    m_run = mcp_server.Server(app="sift").call(run_tool, {"folder": str(old), "dry_run": True})
    reasons = ss.save_reasons(old, [{"code": "E1", "meaning": "Not about sheds"}])
    check("134: a plan holding such a phrase from before is refused at register and at run, on the command line and "
          "through MCP in the same line, sift search plan names it, and an edit of the reasons keeps them in their file",
          reg == "Version 1 is registered and unchanged since." and ran == f'Sheds: "garden shed*": {line}'
          and c_run[0] == 1 and c_run[2].strip() == f'Sheds: "garden shed*": {line}'
          and f'Sheds: "garden shed*": {line}' in c_plan[1].splitlines()
          and m_run["isError"] is True and line in m_run["content"][0]["text"]
          and reasons["unsaved"] == [f'Sheds: "garden shed*": {line}'] and (old / ss.PLAN_NAME).read_bytes() == old_bytes
          and "E1,Not about sheds" in (old / sift.REASONS_NAME).read_text(encoding="utf-8"), c_run[2] + str(reasons.get("unsaved")))
    data["versions"][0]["registered"] = None
    (old / ss.PLAN_NAME).write_text(json.dumps(data), encoding="utf-8")
    check("134: and a draft holding one is not registered either",
          refusal_of(lambda: ss.register(old)) == f'Sheds: "garden shed*": {line}')

    # ── B. the dry run's truncation check, against a stub of the databases' counts
    counts = {("scopus", "shed*"): 120, ("scopus", "shed"): 90, ("pubmed", "shed*"): 40, ("pubmed", "shed"): 31,
              ("epmc", "shed*"): 55, ("epmc", "shed"): 55, ("scopus", "solitud*"): 12, ("scopus", "solitud"): 0,
              ("pubmed", "solitud*"): 7, ("pubmed", "solitud"): 0, ("epmc", "solitud*"): 0, ("epmc", "solitud"): 0}
    state = {"asked": [], "fail": ""}
    term_of = lambda q: next((t for t in ("shed*", "shed", "solitud*", "solitud") if t in q), "")
    one = {"title": "Sheds and solitude", "doi": "10.5555/shed.1", "year": "2021"}

    class Stub(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, body, code=200, ctype="application/json"):
            data = body.encode("utf-8") if isinstance(body, str) else json.dumps(body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            url = up.urlparse(self.path)
            q = {k: v[0] for k, v in up.parse_qs(url.query).items()}
            state["asked"].append((url.path, q))
            if url.path.endswith("/esearch.fcgi"):
                if q.get("retmax") == "0":
                    return self.send({"esearchresult": {"count": str(counts[("pubmed", term_of(q["term"]))])}})
                return self.send({"esearchresult": {"count": "1", "idlist": ["5001"]}})
            if url.path.endswith("/efetch.fcgi"):
                return self.send("<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>5001</PMID><Article><Journal>"
                                 "<JournalIssue><PubDate><Year>2021</Year></PubDate></JournalIssue><Title>Invented Shed "
                                 f"Review</Title></Journal><ArticleTitle>{one['title']}</ArticleTitle></Article></MedlineCitation>"
                                 f"<PubmedData><ArticleIdList><ArticleId IdType=\"doi\">{one['doi']}</ArticleId></ArticleIdList>"
                                 "</PubmedData></PubmedArticle></PubmedArticleSet>", ctype="text/xml")
            if url.path.endswith("/europepmc/webservices/rest/search"):
                if state["fail"] == "epmc":
                    return self.send({"error": "bad query"}, 400)
                if q.get("resultType") == "idlist":
                    return self.send({"hitCount": counts[("epmc", term_of(q["query"]))]})
                return self.send({"hitCount": 1, "resultList": {"result": [{"id": "1", "source": "MED", "title": one["title"],
                                                                             "pubYear": "2021", "doi": one["doi"]}]}})
            if url.path.endswith("/content/search/scopus"):
                if q.get("count") == "1":
                    return self.send({"search-results": {"opensearch:totalResults": str(counts[("scopus", term_of(q["query"]))])}})
                return self.send({"search-results": {"opensearch:totalResults": "1", "entry": [
                    {"eid": "2-s2.0-5", "dc:title": one["title"], "prism:coverDate": "2021-01-01", "prism:doi": one["doi"]}]}})
            if url.path == "/api.crossref.org/works":
                return self.send({"status": "ok", "message": {"items": []}})
            if url.path.endswith("/works") and q.get("filter", "").startswith("doi:"):
                return self.send({"meta": {"count": 0}, "results": []})
            if url.path.endswith("/works"):
                return self.send({"meta": {"count": 1, "next_cursor": None}, "results": [
                    {"id": "https://openalex.org/W5", "doi": "https://doi.org/" + one["doi"], "title": one["title"],
                     "publication_year": 2021, "type": "article"}]})
            return self.send({}, 404)

    kept_clock, kept_env = ss.CLOCK, os.environ.pop(ss.STUB_ENV, None)
    ss.CLOCK = lambda: dt.date(2031, 7, 5)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    stub = f"http://127.0.0.1:{httpd.server_address[1]}"
    paused = []
    ctx = lambda: ss.Context(base={s: stub + urllib_path(u) for s, u in ss.ENDPOINTS.items()}, pause=paused.append)
    kept_server = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.PICK_FOLDER,
                   server_mod.PLATFORM)
    kept_pause = dict(ss.PAUSE)
    try:
        # every key from the smoke's keychain in memory, every request to the stub on loopback
        os.environ[ss.STUB_ENV] = stub
        ss.save(review, dict(good, databases=["scopus", "psycinfo", "pubmed", "epmc", "openalex"]))
        ss.register(review)
        listed = [{"source": s, "how": "api"} for s in ("scopus", "pubmed", "epmc", "openalex")] + [
            {"source": "psycinfo", "platform": "ebsco", "how": "export"}]
        plain = ss.run(review, day="2031-07-05", ctx=ctx(), dry_run=True, listed=listed)
        asked_plain = len(state["asked"])
        dry = ss.run(review, day="2031-07-05", ctx=ctx(), dry_run=True, listed=listed, check_terms=True)
        table = dry["terms"]
        rows = {(r["source"], r["term"]): r for r in table["rows"]}
        check("134: a dry run asked for the check counts each truncated term alone in each database searched by API that "
              "takes truncation, Scopus, PubMed and Europe PMC in Sift's order, never OpenAlex or a database by export, and "
              "writes no run folder, and without it sends nothing",
              "terms" not in plain and asked_plain == 0 and table["sources"] == ["Scopus", "PubMed", "Europe PMC"]
              and [(r["source"], r["term"]) for r in table["rows"]] == [(s, t) for s in ("scopus", "pubmed", "epmc")
                                                                        for t in ("shed*", "solitud*")]
              and not any("/works" in p for p, _ in state["asked"]) and len(state["asked"]) == 12
              and not (review / "runs").exists(), str([(r["source"], r["term"]) for r in table["rows"]]))
        check("134: each count is of the term alone in its block's fields with the plan's years and types, with and without "
              "its asterisk, as each database's writer writes it",
              rows[("scopus", "shed*")]["query"] == "TITLE-ABS-KEY(shed*) AND PUBYEAR > 2009 AND DOCTYPE(ar)"
              and rows[("scopus", "shed*")]["query_without"] == "TITLE-ABS-KEY(shed) AND PUBYEAR > 2009 AND DOCTYPE(ar)"
              and rows[("pubmed", "solitud*")]["query"] == '(solitud*[tiab]) AND 2010:3000[dp] AND "journal article"[pt]'
              and rows[("epmc", "solitud*")]["query"] == '(METHODS:solitud*) AND PUB_YEAR:[2010 TO 2031] AND PUB_TYPE:"journal article"'
              and rows[("epmc", "shed*")]["query_without"] == '(TITLE_ABS:shed OR KW:shed) AND PUB_YEAR:[2010 TO 2031] AND '
                                                              'PUB_TYPE:"journal article"', rows[("epmc", "solitud*")]["query"])
        check("134: the counts from the stub, and Adam's two flags: equal counts where another database's differ, and no "
              "hits where another has some",
              [(rows[k]["with"], rows[k]["without"]) for k in sorted(rows)] == [
                  (55, 55), (0, 0), (40, 31), (7, 0), (120, 90), (12, 0)]
              and rows[("epmc", "shed*")]["flag"] == "Europe PMC reads shed* as shed"
              and rows[("epmc", "solitud*")]["flag"] == "No hits in Europe PMC: syntax or coverage?"
              and not any(rows[k]["flag"] for k in rows if k[0] != "epmc")
              and table["flags"] == ["Europe PMC reads shed* as shed", "No hits in Europe PMC for solitud*: syntax or coverage?"],
              str(table["flags"]))
        check("134: Sift's usual pause between one request and the next to a database, PubMed's 0.4 seconds keeping under "
              "three a second with no key, and none before a database's first",
              paused == [ss.PAUSE["scopus"]] * 3 + [ss.PAUSE["pubmed"]] * 3 + [ss.PAUSE["epmc"]] * 3
              and ss.PAUSE["pubmed"] >= 1 / 3, str(paused))
        lone = ss.clean_plan(dict(good, databases=["scopus", "epmc"]))
        flagged = []
        for a, b, c, d in ((10, 8, 10, 10), (10, 8, 0, 0), (10, 10, 4, 4), (0, 0, 5, 3)):
            rs = [{"i": 0, "term": "kiln*", "bare": "kiln", "name": n, "with": w, "without": wo, "flag": ""}
                  for n, w, wo in (("Scopus", a, b), ("Europe PMC", c, d))]
            ss.flag_rows(rs)
            flagged.append([r["flag"] for r in rs])
        check("134: the flags worked out across the databases: equal counts flagged only where another differs, no hits "
              "only where another has some, and nothing when every database agrees",
              flagged == [["", "Europe PMC reads kiln* as kiln"], ["", "No hits in Europe PMC: syntax or coverage?"], ["", ""],
                          ["No hits in Scopus: syntax or coverage?", ""]] and lone["blocks"], str(flagged))
        state["fail"] = "epmc"
        state["asked"].clear()
        failed = ss.run(review, day="2031-07-05", ctx=ctx(), dry_run=True, listed=listed, check_terms=True)["terms"]
        state["fail"] = ""
        epmc_rows = [r for r in failed["rows"] if r["source"] == "epmc"]
        check("134: a database that refuses a count is said on its rows and asked no more, with no flag of its own, in "
              "plain words for the screen and in full for the run's file (17 October, later)",
              len(epmc_rows) == 2 and all(r["with"] is None and r["said"] == "Europe PMC refused the request (HTTP 400)."
                                          and r["detail"].startswith("HTTP 400") for r in epmc_rows)
              and sum(1 for p, _ in state["asked"] if p.endswith("/rest/search")) == 1 and not any(r["flag"] for r in epmc_rows)
              and failed["flags"] == [], str(epmc_rows[0]["said"]))
        lines = ss.terms_lines(table)
        check("134: the command line says the table, each term with its counts in each database, then each flag",
              lines == ["Truncation, each term alone with and without its asterisk:",
                        "  shed*, Sheds: Scopus 120 and 90, PubMed 40 and 31, Europe PMC 55 and 55.",
                        "  solitud*, Solitude: Scopus 12 and 0, PubMed 7 and 0, Europe PMC 0 and 0.",
                        "  Europe PMC reads shed* as shed.", "  No hits in Europe PMC for solitud*: syntax or coverage?"],
              "\n".join(lines))
        cfg = base / "shed-config.json"
        cfg.write_text(json.dumps({"databases": listed}), encoding="utf-8")
        # the command line's and MCP's dry runs with no pause between requests to the stub, the pause itself
        # checked above (testspeed, 2 November 2026: their real pauses took six seconds)
        ss.PAUSE.update({k: 0 for k in ss.PAUSE})
        c_dry = cli_mod.run(["sift", "search", "run", str(review), "--date", "2031-07-05", "--dry-run", "--config", str(cfg)])
        m_dry = mcp_server.Server(config=str(cfg)).call(run_tool, {"folder": str(review), "dry_run": True})
        check("134: sift search run --dry-run and MCP's dry run give the table and its flags, and write no run folder",
              c_dry[0] == 0 and "\n".join(lines) in c_dry[1] and m_dry["isError"] is False
              and support.plain(m_dry["structuredContent"])["terms"]["flags"] == table["flags"] and not (review / "runs").exists(),
              c_dry[1][-400:] + c_dry[2])

        # a run that follows the check keeps its table in the run folder
        heard = []
        done = ss.run(review, day="2031-07-05", ctx=ctx(), listed=listed, check_terms=True,
                      progress=lambda s, said: heard.append((s, said["state"])))
        run_dir = review / "runs" / "2031-07-05"
        with open(run_dir / ss.TERMS_NAME, encoding="utf-8", newline="") as fh:
            got = list(csv.reader(fh))
        meta = json.loads((run_dir / ss.RUN_FILE).read_text(encoding="utf-8"))
        check("134: a run checks first, each database heard checking before it runs, and keeps the table as "
              "dry_run_terms.csv, a row a term in each database, its flags in run.json",
              got[0] == ss.TERMS_COLUMNS == ["block", "term", "database", "with_asterisk", "without_asterisk", "flag", "query",
                                             "query_without"]
              and got[1][:6] == ["Sheds", "shed*", "Scopus", "120", "90", ""]
              and got[5][:6] == ["Sheds", "shed*", "Europe PMC", "55", "55", "Europe PMC reads shed* as shed"]
              and got[6][:6] == ["Solitude", "solitud*", "Europe PMC", "0", "0", "No hits in Europe PMC: syntax or coverage?"]
              and len(got) == 7 and meta["terms"] == {"file": ss.TERMS_NAME, "rows": 6, "flags": table["flags"]}
              and heard.index(("scopus", "checking")) < heard.index(("scopus", "running"))
              and ("epmc", "checking") in heard and ("openalex", "checking") not in heard
              and done["terms"]["flags"] == table["flags"] and done["merged"] == 1, str(got[:2]) + str(heard[:6]))
        said_run = ss.run_lines(done)
        check("134: the run's lines on the command line say its flags",
              "  Europe PMC reads shed* as shed." in said_run
              and "  No hits in Europe PMC for solitud*: syntax or coverage?" in said_run, "\n".join(said_run))
        bare_run = ss.run(review, day="2031-07-05", ctx=ctx(), listed=listed)
        check("134: a run that does not check writes no table, and a dry run never does",
              not (review / "runs" / bare_run["date"] / ss.TERMS_NAME).exists() and bare_run["terms"] is None
              and bare_run["date"] == "2031-07-05-2")

        # ── the route: the save refused for the screen, Check truncation and a run on its thread, with no pause
        # between requests to the stub, the pause itself checked above (sped up 18 October, testreview3), set to
        # none before the command line's dry run
        config_file = base / "config.json"
        config_file.write_text(json.dumps(dict(server_mod.defaults(), databases=listed)), encoding="utf-8")
        server_mod.CONFIG_PATH = config_file
        server_mod.ROOT_OVERRIDE = str(base)
        server_mod.STATE_MEMORY = {"recent": []}
        fresh = base / "shed-route"
        fresh.mkdir()
        server_mod.PLATFORM = "darwin"
        server_mod.PICK_FOLDER = lambda prompt: fresh
        chosen = sift_routes.api_sift_review({"op": "folder", "mode": "new"})
        picked = sift_routes.api_sift_review({"op": "new", "folder": chosen["folder"], "name": "Shed route"})["review"]
        first = sift_routes.api_sift_search({"op": "save", "folder": picked["folder"],
                                            "plan": dict(good, databases=["scopus", "pubmed", "epmc"])})
        held = (fresh / ss.PLAN_NAME).read_bytes()
        no = sift_routes.api_sift_search({"op": "save", "folder": picked["folder"], "plan": bad})
        check("134: through the route a save holding such a phrase writes nothing and answers the plan as it stands with "
              "unsaved and the problems of the plan sent, and a save that goes through answers unsaved empty",
              first["unsaved"] == [] and no["unsaved"] == [f'Sheds: "garden shed*": {line}']
              and no["block_problems"][0] == [f'"garden shed*": {line}'] and f'Sheds: "garden shed*": {line}' in no["problems"]
              and no["current"]["version"] == 1 and (fresh / ss.PLAN_NAME).read_bytes() == held
              and no["plan"]["blocks"][0]["terms"][1] == '"garden shed"', str(no.get("unsaved")))
        sift_routes.api_sift_search({"op": "register", "folder": picked["folder"], "registry": "OSF",
                                    "registration": "https://osf.io/shed1"})
        read = sift_routes.api_sift_search({"op": "read", "folder": picked["folder"]})
        checked = sift_routes.api_sift_search({"op": "terms", "folder": picked["folder"]})
        check("134: the screen's catalogue names the databases that take truncation, the plan its truncated words, and "
              "Check truncation's route answers the table of the newest version and writes nothing",
              read["catalog"]["truncates"] == ["scopus", "wos", "pubmed", "epmc"] and read["truncated"] == 2
              and checked["version"] == 1 and checked["flags"] == table["flags"] and not (fresh / "runs").exists(),
              str(checked.get("flags")))
        sift_routes.api_sift_search({"op": "run", "folder": picked["folder"]})
        for _ in range(600):
            prog = sift_routes.api_sift_search({"op": "progress", "folder": picked["folder"]})
            if not prog["running"]["running"]:
                break
            time.sleep(0.05)
        made = (prog.get("runs") or [{}])[0]
        check("134: a run started on the screen checks first and keeps dry_run_terms.csv in its folder, its flags in the "
              "runs the screen draws",
              made.get("date") == "2031-07-05" and (fresh / "runs" / "2031-07-05" / ss.TERMS_NAME).is_file()
              and (made.get("terms") or {}).get("flags") == table["flags"], str(prog.get("running", {}).get("error")))
    finally:
        httpd.shutdown()
        httpd.server_close()
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.PICK_FOLDER,
         server_mod.PLATFORM) = kept_server
        ss.CLOCK = kept_clock
        ss.PAUSE.update(kept_pause)
        os.environ.pop(ss.STUB_ENV, None)
        if kept_env is not None:
            os.environ[ss.STUB_ENV] = kept_env

    # ── C. the rewrites beside each string
    plan = ss.clean_plan({"databases": ["scopus", "wos", "psycinfo", "cinahl", "pubmed", "epmc", "openalex", "embase",
                                        "scholar", "other"], "others": {"other": "Shed Index"},
                          # PubMed among them, its years and type in its own words
                          "blocks": [{"name": "Sheds", "terms": ["shed*", '"garden shed"']},
                                     {"name": "Method", "terms": ["interview*"], "scopes": {"epmc": "methods", "scopus": "methods"}},
                                     {"name": "", "terms": ["diary"], "scope": "fulltext"}],
                          "years": {"from": 2010, "to": 2030}, "types": ["article", "dissertation"],
                          "overrides": {"wos": {"query": "TS=(shed*)", "reason": "Kept to the sheds alone"}}})
    rw = {s["source"]: s["rewrites"] for s in ss.strings(plan)}
    queries = {s["source"]: s["query"] for s in ss.strings(plan)}
    check("134: each database's rewrites in plain words: a block in other fields, the asterisks OpenAlex leaves out, the "
          "years and types in its own words, a type it lacks, and an edited string's reason alone",
          rw["epmc"][:2] == ["the Method block in the METHODS field", "Block 3 in the TITLE_ABS, KW and BODY fields"]
          and "PUB_YEAR:[2010 TO 2030] from the plan's years" in rw["epmc"]
          and rw["openalex"] == ["Block 3 in the fulltext.search field", "title and abstract alone, with no keywords field",
                                 "asterisks removed, OpenAlex stems", "publication_year:2010-2030 from the plan's years",
                                 "type:article|dissertation from the plan's types"]
          and rw["scopus"] == ["the Method block in the TITLE-ABS-KEY field", "Block 3 in the TITLE-ABS-KEY field",
                               "PUBYEAR > 2009 AND PUBYEAR < 2031 from the plan's years", "DOCTYPE(ar) from the plan's types",
                               "the dissertation type left out"]
          and rw["wos"] == ["Kept to the sheds alone"] and rw["psycinfo"] == ["Block 3 in the TX field"]
          and rw["cinahl"] == ["Block 3 in the TX field", "SU, the subject fields, in place of keywords"]
          and rw["embase"] == ["Block 3 in the ti, ab and kw fields", "phrases in single quotes"]
          and rw["scholar"] == ["asterisks removed, Google Scholar has no truncation"] and rw["other"] == [], str(rw))
    clauses = [(s, w.rsplit(" from the plan's ", 1)[0]) for s, ws in rw.items() for w in ws if " from the plan's " in w]
    check("134: every year and type a rewrite names stands in its database's string word for word",
          len(clauses) == 8 and all(c in queries[s] for s, c in clauses), str(clauses))
    st = sift_cli.cmd_sift_search(argparse.Namespace(act="strings", folder=str(review), search=True, version=None, json=False))[1]
    text = "\n".join(st)
    check("134: the command line's strings gives the rewrites under each string, an edited one its reason alone",
          "OpenAlex:\n  title_and_abstract.search:" in text and "  Rewrites:\n    title and abstract alone, with no keywords field\n"
          "    asterisks removed, OpenAlex stems\n" in text and "Europe PMC:\n  " in text
          and "    the Solitude block in the METHODS field" in text, text[:600])

    # ── D. Found in the full text, a fourth match line
    kilns = base / "kiln-review"
    kilns.mkdir()
    ss.new_plan(kilns, "Kilns")
    dbs = ["scopus", "epmc", "openalex", "scholar"]
    ss.save(kilns, {"databases": dbs, "blocks": [{"name": "Kilns", "terms": ["kiln*"], "scopes": {"epmc": "fulltext"}}]})
    krun = kilns / "runs" / "2031-07-06"
    krun.mkdir(parents=True)
    (krun / ss.RUN_FILE).write_text(json.dumps({"version": 1, "sources": {s: {"name": ss.NAMES[s]} for s in dbs}}),
                                    encoding="utf-8")
    with open(krun / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["rec_id", "title", "authors", "year", "journal", "doi", "sources", "abstract"])
        for i, (rec, title, src) in enumerate((("K1", "Firing pottery at home", "Europe PMC"),
                                               ("K2", "Glazes and patience", "OpenAlex"),
                                               ("K3", "Clay studios", "Europe PMC; Scopus"),
                                               ("K4", "Smoke and ash", "Google Scholar"),
                                               ("K5", "The kiln shed", "OpenAlex")), 1):
            w.writerow([rec, title, "Fire, Ash", str(2020 + i), "Invented Clay Journal", f"10.5555/kiln.{i}", src,
                        "Potters spoke of the long wait."])
    view = sift.screen(krun)
    by = {r["rec_id"]: r for r in view["records"]}
    why = lambda r: [w["label"] for w in by[r]["matched"]["term:0"]["why"]]
    # updated 14 October, later (137): Adam's new words, the full-text line as "<databases> full text", the
    # databases joined A, B or C, and a field Sift cannot name where None of its terms stood
    check("134: a record found only through a database that searched the block's full text says its full text, "
          "naming those databases, Google Scholar among them, and none of them stands under a field Sift cannot name",
          why("K1") == ["Europe PMC full text"] and why("K4") == ["Google Scholar full text"]
          and why("K3") == ["Scopus keywords", "Europe PMC full text"]
          and why("K2") == ["a field Sift cannot name"] and by["K5"]["terms"]["term:0"] == ["kiln*"]
          and view["blocks"][0]["why"] == [{"value": "|keywords", "label": "Scopus keywords"},
                                           {"value": "|fulltext", "label": "Europe PMC or Google Scholar full text"},
                                           {"value": "|none", "label": "a field Sift cannot name"}],
          str(view["blocks"][0]["why"]))
    shown = sift_cli.cmd_sift(argparse.Namespace(folder=str(krun), act="show", rec_id="K1", stage="ta", search=False))[1]
    check("134: the command line's show says the full-text line in the record's sentence",
          "Block 1, Kilns: none in the title or abstract. Europe PMC matched at least one in its full text, which Sift "
          "does not hold, so Sift cannot say which." in shown, "\n".join(shown))
    if not node:
        skip("134: the filter, the column and the screen's parts in node", "node is not installed")
    else:
        lead = app_src[app_src.index("const esc = "):app_src.index("// a line from the server with a command in backticks")]
        block = sift_src.split("/* ── the table's rows: its columns, sort and filter, worked out with no page ── */", 1)[-1].split(
            "/* ── the table, drawn ── */", 1)[0]
        block = support.table_js() + "\n" + block
        harness = r"""
const els = {};
const mk = () => ({ hidden: false, innerHTML: '', textContent: '', title: '', disabled: false, className: '', dataset: {}, style: {}, setAttribute() {} });
const $ = (id) => els[id] || (els[id] = mk());
const VIEW = __VIEW__;
const SF = { stage: 'ta', filters: {}, table: VIEW.table, records: VIEW.records, blocks: VIEW.blocks, keyWorks: [],
  reasons: { ta: [], ft: [] }, roundIds: VIEW.records.map((r) => r.rec_id), form: false, formBench: new Set(), formInc: new Set() };
SF.byId = new Map(SF.records.map((r) => [r.rec_id, r]));
const cols = sfAllCols();
const groups = sfGroups(SF.records, SF.records, cols, 'ta', [], {});
const counts = tbFacetCounts(SF.records, groups, {}, sfRead('ta'));
const out = {};
out.fulltext = tbFilterRows(SF.roundIds, SF.byId, { 'term:0': ['|fulltext'] }, cols, sfRead('ta'));
out.none = tbFilterRows(SF.roundIds, SF.byId, { 'term:0': ['|none'] }, cols, sfRead('ta'));
out.count = counts['term:0']['|fulltext'];
const col = cols.find((c) => c.key === 'matched');
out.value = sfValue(SF.byId.get('K1'), col, 'ta');
console.log(JSON.stringify(out));
"""
        script = base / "terms-134.js"
        script.write_text("\n".join([lead, sift_words_js(sift_src), block, whole(sift_src, "sfTvCell"),
                                     whole(sift_src, "sfTermsDraw"), harness.replace("__VIEW__", json.dumps(view))]),
                          encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        # updated 14 October, later (137): the column in Adam's new words
        check("134: in node, the fourth line is a choice of the block's group like the other three, its records under it and "
              "not under a field Sift cannot name, and the Matched in column says it",
              out.get("fulltext") == ["K1", "K3", "K4"] and out.get("none") == ["K2"] and out.get("count") == 3
              and out.get("value") == "Europe PMC full text", (ran.stderr or json.dumps(out))[:400])

        # the Search strategy screen's own parts: Rewrites, Not saved, Check truncation and its table
        parts = "\n".join(whole(sjs, n) for n in ("sfsRewritesHtml", "sfsCheckable", "sfsDrawCheck", "sfsExported"))
        unsaved = sjs.split("const sfsUnsaved = ", 1)[1].split("\n", 1)[0]
        page = r"""
const els = {};
const mk = () => ({ hidden: false, innerHTML: '', textContent: '', disabled: false, className: '', dataset: {}, style: {} });
const $ = (id) => els[id] || (els[id] = mk());
const sfsIsOther = (s) => /^other(?:[2-9]|1\d|20)?$/.test(String(s || ''));
const sfsUnsaved = __UNSAVED__
const SFS = { data: { current: { version: 1 }, truncated: 2, unsaved: [] }, plan: { databases: ['scopus', 'epmc', 'openalex'] },
  catalog: { truncates: ['scopus', 'wos', 'pubmed', 'epmc'], keyless: ['pubmed', 'epmc', 'openalex'], apis: ['scopus', 'wos', 'pubmed', 'epmc', 'openalex'] },
  how: { scopus: 'api', epmc: 'api', openalex: 'api' }, terms: null, checking: false };
__PARTS__
const out = {};
out.rw = [sfsRewritesHtml({ rewrites: ['the Method block in the METHODS field', 'asterisks <b>'] }), sfsRewritesHtml({ rewrites: [] })];
sfsDrawCheck(null);
out.shown = [$('sfs-check-go').hidden, $('sfs-check-go').textContent, $('sfs-check').hidden];
SFS.terms = { rows: [{ term: 'shed*', name: 'Europe PMC', with: 1550, without: 1550, flag: 'Europe PMC reads shed* as shed', said: '' },
  { term: 'shed*', name: 'Scopus', with: null, without: null, flag: '', said: 'Scopus refused the key (HTTP 401).' }] };
SFS.checking = true;
sfsDrawCheck(null);
out.table = $('sfs-check').innerHTML;
out.busy = [$('sfs-check-go').disabled, $('sfs-check-go').textContent];
SFS.checking = false;
SFS.data.unsaved = ['Sheds: "garden shed*": Truncation inside a phrase'];
sfsDrawCheck(null);
out.unsaved = [$('sfs-check-go').disabled, sfsUnsaved()];
SFS.data.unsaved = [];
SFS.how.scopus = 'export';
SFS.how.epmc = 'export';
sfsDrawCheck(null);
out.none = [$('sfs-check-go').hidden, $('sfs-check').hidden];
console.log(JSON.stringify(out));
"""
        script2 = base / "check-134.js"
        script2.write_text(support.i18n_js() + lead + "\n" + page.replace("__UNSAVED__", unsaved).replace("__PARTS__", parts), encoding="utf-8")
        ran2 = subprocess.run([node, str(script2)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        o = json.loads(ran2.stdout) if ran2.returncode == 0 and ran2.stdout.strip() else {}
        table_html = o.get("table", "")
        check("134: in node, Check truncation shows when a database that takes truncation goes by API and the plan holds a "
              "truncated word, its table each word's counts in each database, the flag and a failure said, held while it "
              "asks and while the plan is unsaved, and gone when nothing is there to count",
              o.get("shown", [None])[0] is False and o.get("shown", [None] * 3)[2] is True
              and ">1,550<" in table_html and "Europe PMC reads shed* as shed" in table_html
              and "Scopus refused the key (HTTP 401)." in table_html
              and o.get("busy", [None])[0] is True and o.get("unsaved") == [True, True] and o.get("none") == [True, True],
              (ran2.stderr or table_html)[:400])
