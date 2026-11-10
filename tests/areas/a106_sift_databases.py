from __future__ import annotations

import contextlib
import inspect
import io
import json
import os
import shutil
import sys

import ai_suggest as ai_mod

from . import support
from .support import check, mode_is, refusal_of, urllib_path


@support.as_app("sift")
def test_sift_databases(scratch):
    print("\n106. Sift's databases: his own list under Projects in Settings, each key by its keychain service with "
          "Save, Remove and Check, four more databases with their strings, BibTeX, the plan by his list, the command "
          "line and MCP")
    import http.server
    import threading
    import urllib.parse as up
    import cli
    import sift_cli
    import mcp_server
    import sift_mcp
    import server as server_mod
    import sift_routes
    import sift_search as ss

    page = support.page_text()
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    sjs = support.text("apps/sift/static/sift_search.js")
    base = scratch / "sift-databases"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    secret, token, other = "pond-key-SECRET789", "pond-token-SECRET790", "pond-key-SECRET791"

    # the keychain stood in for, a service to a value, every call kept, never the real one
    class Done:
        def __init__(self, code, out=""):
            self.returncode, self.stdout, self.stderr = code, out, ""

    held, calls = {}, []

    def keychain(argv, **kw):
        calls.append(list(argv))
        act, service = argv[1], argv[argv.index("-s") + 1]
        if act == "add-generic-password":
            held[service] = argv[argv.index("-w") + 1]
            return Done(0)
        if act == "delete-generic-password":
            return Done(0 if held.pop(service, None) else 44)
        return Done(0, held[service] + "\n") if service in held else Done(44)

    # a stub of the four APIs Check asks, on an invented topic, ponds: each takes the keys in `good`
    # and refuses any other, saying the key it was sent back, as a careless server might
    stub_state = {"good": {secret, other, "stub-elsevier_api_key", "stub-clarivate_api_key"}, "asked": []}

    class Stub(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, code, body):
            data = json.dumps(body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            url = up.urlparse(self.path)
            q = {k: v[0] for k, v in up.parse_qs(url.query).items()}
            stub_state["asked"].append((url.path, q, {k.lower(): v for k, v in self.headers.items()}))
            key = (self.headers.get("X-ELS-APIKey") or self.headers.get("X-ApiKey") or q.get("api_key"))
            if key is not None and key not in stub_state["good"]:
                return self.send(401, {"error": f"Invalid key {key}"})
            if url.path.endswith("/esearch.fcgi"):
                return self.send(200, {"esearchresult": {"count": "1", "idlist": []}})
            if url.path.endswith("/works"):
                if q.get("filter", "").startswith("doi:"):
                    return self.send(200, {"meta": {"count": 0}, "results": []})
                return self.send(200, {"meta": {"count": 1, "next_cursor": None}, "results": [
                    {"id": "https://openalex.org/W9", "doi": "https://doi.org/10.5555/pond.9", "title": "Wild swimming in ponds",
                     "publication_year": 2021, "type": "article", "authorships": [{"author": {"display_name": "Ivy Reed"}}],
                     "primary_location": {"source": {"display_name": "Invented Water Review"}}}]})
            if url.path.endswith("/content/search/scopus"):
                return self.send(200, {"search-results": {"opensearch:totalResults": "1", "entry": []}})
            if url.path.endswith("/documents"):
                return self.send(200, {"metadata": {"total": 1}, "hits": []})
            return self.send(404, {"error": "no such path"})

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    stub = f"http://127.0.0.1:{httpd.server_address[1]}"
    base_urls = {s: stub + urllib_path(u) for s, u in ss.ENDPOINTS.items()}
    ctx = lambda: ss.Context(base=base_urls, pause=lambda s: None)
    kept = (ss.RUNNER, os.environ.pop(ss.STUB_ENV, None), ss.ENV_PATH, ai_mod.security_missing, server_mod.CONFIG_PATH,
            dict(ss.STUB_KEYCHAIN.held))
    ss.RUNNER = keychain
    try:
        # ── A. the list in config.json: empty on a new install, added to in order, a row removed
        config_file = base / "config.json"
        config_file.write_text(json.dumps(server_mod.defaults()), encoding="utf-8")
        server_mod.CONFIG_PATH = config_file
        check("106: a new install holds no databases, and a settings file from before the list reads as none",
              server_mod.defaults()["databases"] == [] and server_mod.merge_config({})["databases"] == []
              and ss.databases(server_mod.config()) == [] and ss.databases({}) == [])
        raw = [{"source": "openalex"}, {"source": "psycinfo", "platform": "ovid", "how": "api"},
               {"source": "other", "name": "  Pond   Index "}, {"source": "scopus", "how": "export"},
               {"source": "psycinfo", "platform": "proquest"}, {"source": "other", "name": "pond index"},
               {"source": "other", "name": ""}, {"source": "nowhere"}, {"source": "cinahl", "platform": "dialup"},
               {"source": "embase", "how": "api"}, "openalex"]
        rows = ss.clean_databases(raw)
        check("106: each row a database Sift knows or another by name, in his order, held once, a platform for PsycInfo "
              "and CINAHL, EBSCO unless another, and By API only where Sift has an API",
              rows == [{"source": "openalex", "how": "api"}, {"source": "psycinfo", "platform": "ovid", "how": "export"},
                       {"source": "other", "name": "Pond Index", "how": "export"}, {"source": "scopus", "how": "export"},
                       {"source": "cinahl", "platform": "ebsco", "how": "export"}, {"source": "embase", "how": "export"}],
              str(rows))
        server_mod.api_settings({"databases": rows})
        on_disk = json.loads(config_file.read_text(encoding="utf-8"))["databases"]
        server_mod.api_settings({"databases": [r for r in rows if r["source"] != "scopus"] + [{"source": "pubmed", "how": "api"}]})
        after = [r["source"] for r in json.loads(config_file.read_text(encoding="utf-8"))["databases"]]
        server_mod.api_settings({"interviewer": "Adam"})
        kept_list = [r["source"] for r in json.loads(config_file.read_text(encoding="utf-8"))["databases"]]
        check("106: Save keeps the list in config.json under databases in its order, a row removed and one added, and a "
              "save that sends no list leaves it",
              on_disk == rows and after == ["openalex", "psycinfo", "other", "cinahl", "embase", "pubmed"] and kept_list == after,
              str(after))

        # ── B. each platform's string for an invented plan, against strings written by hand
        blocks = [{"name": "Ponds", "terms": ["pond*", '"wild swimming"']}, {"name": "Calm", "terms": ["calm", '"mental health"']}]
        on = lambda p: {s["source"]: s for s in ss.strings(ss.clean_plan({
            "databases": ["psycinfo", "cinahl", "pqdt", "embase", "scholar"], "platforms": {"psycinfo": p, "cinahl": p},
            "blocks": blocks, "years": {"from": 2010, "to": 2026}}))}
        ebsco, ovid, proquest = on("ebsco"), on("ovid"), on("proquest")
        # ProQuest's own codes, TITLE, ABSTRACT and IF for keywords, joined by commas (see area 107)
        pq = 'TITLE,ABSTRACT,IF(pond* OR "wild swimming") AND TITLE,ABSTRACT,IF(calm OR "mental health")'
        want = {
            ("psycinfo", "EBSCO"): ('(TI (pond* OR "wild swimming") OR AB (pond* OR "wild swimming") OR KW (pond* OR "wild swimming")) '
                                   'AND (TI (calm OR "mental health") OR AB (calm OR "mental health") OR KW (calm OR "mental health"))'),
            ("cinahl", "EBSCO"): ('(TI (pond* OR "wild swimming") OR AB (pond* OR "wild swimming") OR SU (pond* OR "wild swimming")) '
                                 'AND (TI (calm OR "mental health") OR AB (calm OR "mental health") OR SU (calm OR "mental health"))'),
            ("psycinfo", "Ovid"): '(pond* OR "wild swimming").ti,ab,id. AND (calm OR "mental health").ti,ab,id.',
            ("cinahl", "Ovid"): '(pond* OR "wild swimming").ti,ab. AND (calm OR "mental health").ti,ab.',
            ("psycinfo", "ProQuest"): pq,
            ("cinahl", "ProQuest"): 'TITLE,ABSTRACT(pond* OR "wild swimming") AND TITLE,ABSTRACT(calm OR "mental health")',
        }
        got = {(s, d[s]["platform"]): d[s]["query"] for d in (ebsco, ovid, proquest) for s in ("psycinfo", "cinahl")}
        for k, w in want.items():
            check(f"106: {k[0]} on {k[1]}, as written by hand", got.get(k) == w, str(got.get(k)))
        check("106: ProQuest Dissertations & Theses in TITLE,ABSTRACT,IF(), Embase in its own syntax, :ti,ab,kw and single quotes",
              ebsco["pqdt"]["query"] == pq and ebsco["pqdt"]["platform"] == ""
              and ebsco["embase"]["query"] == "(pond* OR 'wild swimming'):ti,ab,kw AND (calm OR 'mental health'):ti,ab,kw",
              ebsco["embase"]["query"])
        check("106: Google Scholar a plain string, phrases quoted, no asterisk and no field, with the note on what it takes",
              ebsco["scholar"]["query"] == 'pond OR "wild swimming" calm OR "mental health"'
              and "Google Scholar takes only simple Boolean and about 256 characters, with no fields and no truncation, "
              "so the asterisks are left out." in ebsco["scholar"]["notes"]
              and ebsco["scholar"]["limits"] == "Set on the site: published 2010 to 2026.", str(ebsco["scholar"]))
        many = ss.clean_plan({"databases": ["scholar"], "blocks": [
            {"name": "Ponds", "terms": [f'"garden pond number {n}"' for n in range(20)]}, {"name": "Calm", "terms": ["calm", "rest"]}]})
        long_one = ss.strings(many)[0]
        check("106: a Google Scholar string past its length is kept within it, every block keeping a term, the terms left "
              "out named",
              len(long_one["query"]) <= ss.SCHOLAR_MOST and "calm OR rest" in long_one["query"]
              and '"garden pond number 0"' in long_one["query"] and '"garden pond number 19"' not in long_one["query"]
              and any(n.startswith("To keep within them, ") and '"garden pond number 19"' in n for n in long_one["notes"]),
              f"{len(long_one['query'])} characters")
        check("106: the notes say what stands in for keywords on each platform, and the plan keeps its platform",
              "PsycInfo on Ovid has no keywords field, so its Key Concepts, id, stand in." in ovid["psycinfo"]["notes"]
              and "CINAHL on EBSCO has no keywords field, so SU, its subject fields with their keywords, stands in."
              in ebsco["cinahl"]["notes"]
              and ss.clean_plan({"databases": ["cinahl"]})["platforms"] == {"cinahl": "ebsco"}
              and ss.clean_plan({"databases": ["scopus"], "platforms": {"psycinfo": "ovid"}})["platforms"] == {})
        plan_ovid = ss.clean_plan({"databases": ["psycinfo"], "platforms": {"psycinfo": "ovid"}, "blocks": blocks})
        md = ss.markdown({"versions": []}, {"version": 1, "registered": "2026-11-01T10:00:00+00:00", "plan": plan_ovid})
        check("106: the Markdown names the platform over its string, and log.csv names the platform PsycInfo was searched on",
              "### PsycInfo on Ovid\n" in md and ss.exported_said("psycinfo", plan_ovid) == "APA PsycInfo on Ovid, export"
              and ss.exported_said("psycinfo", ss.clean_plan({"databases": ["psycinfo"]})) == "APA PsycInfo on EBSCOhost, export")

        # ── C. the key fields per database, by the keychain services Adam's keys are under already
        fields = {s: [(f["service"], f["optional"]) for f in ss.KEY_FIELDS[s]] for s in ss.KEY_FIELDS}
        check("106: the key fields per database, by their keychain services, the optional ones marked",
              fields == {"scopus": [("ELSEVIER_API_KEY", False), ("ELSEVIER_INSTTOKEN", True)],
                         "wos": [("CLARIVATE_API_KEY", False)], "openalex": [("OPENALEX_API_KEY", True)],
                         "pubmed": [("NCBI_API_KEY", True)], "epmc": []}
              and set(ss.APIS) == set(ss.KEY_FIELDS) and set(ss.SERVICES) == {
                  "ELSEVIER_API_KEY", "ELSEVIER_INSTTOKEN", "CLARIVATE_API_KEY", "OPENALEX_API_KEY", "NCBI_API_KEY"}, str(fields))

        # ── D. save, status and remove through ai_suggest's own functions, the keychain stood in for
        saved = sift_routes.api_databases({"op": "key", "service": "OPENALEX_API_KEY", "key": secret})
        read1 = sift_routes.api_databases({"op": "read"})
        status = (ss.key_saved("OPENALEX_API_KEY"), ss.read_key("OPENALEX_API_KEY"))
        cleared = sift_routes.api_databases({"op": "clear", "service": "OPENALEX_API_KEY"})
        again = sift_routes.api_databases({"op": "clear", "service": "OPENALEX_API_KEY"})
        check("106: Save stores the key under its service through the keychain, the status says Saved, and Remove deletes it",
              saved == {"saved": True} and read1["saved"]["OPENALEX_API_KEY"] is True and read1["saved"]["NCBI_API_KEY"] is False
              and status == (True, secret) and cleared == {"cleared": True} and again == {"cleared": False}
              and ["security", "find-generic-password", "-s", "OPENALEX_API_KEY", "-w"] in calls
              and ["security", "delete-generic-password", "-s", "OPENALEX_API_KEY"] in calls
              and any(c[:2] == ["security", "add-generic-password"] and c[c.index("-s") + 1] == "OPENALEX_API_KEY" for c in calls),
              str(read1["saved"]))
        check("106: the four go through ai_suggest's own save, clear, status and read, each taking the service",
              "ai_suggest.save_key(" in inspect.getsource(ss.save_key) and "ai_suggest.clear_key(" in inspect.getsource(ss.clear_key)
              and "ai_suggest.key_status(" in inspect.getsource(ss.key_saved) and "ai_suggest.find_key(" in inspect.getsource(ss.read_key)
              and "service" in inspect.signature(ai_mod.key_status).parameters and "service" in inspect.signature(ai_mod.find_key).parameters
              and "service" in inspect.signature(ai_mod.store_in_env).parameters and "service" in inspect.signature(ai_mod.read_key).parameters)
        unknown = refusal_of(lambda: sift_routes.api_databases({"op": "key", "service": "ANTHROPIC_API_KEY", "key": secret}))
        bad_op = refusal_of(lambda: sift_routes.api_databases({"op": "show", "service": "OPENALEX_API_KEY"}))
        check("106: no other service is taken, the Anthropic key's least of all, and no op shows a key",
              unknown == "Sift keeps no key by that name." and "ANTHROPIC_API_KEY" not in held
              and bad_op == "The op is read, key, clear, check or save."
              and sift_routes.DATABASE_OPS == ("read", "key", "clear", "check", "save"))

        def raising(argv, **kw):
            raise OSError(f"could not run {' '.join(argv)}")

        ss.RUNNER = raising
        blew = sift_routes.api_databases({"op": "key", "service": "CLARIVATE_API_KEY", "key": secret})
        ss.RUNNER = keychain
        # off a Mac the key goes to .env at mode 0600 beside the Anthropic one, which stays
        env = base / ".env"
        env.write_text("ANTHROPIC_API_KEY=anthropic-stand-in\n", encoding="utf-8")
        ss.ENV_PATH = env
        ai_mod.security_missing = lambda runner=None: True
        file_saved = ss.save_key("NCBI_API_KEY", other)
        in_file = (env.read_text(encoding="utf-8"), "0o600" if mode_is(env, 0o600) else oct(env.stat().st_mode & 0o777), ss.key_saved("NCBI_API_KEY"), ss.read_key("NCBI_API_KEY"))
        file_cleared = ss.clear_key("NCBI_API_KEY")
        left = env.read_text(encoding="utf-8")
        ai_mod.security_missing = kept[3]
        ss.ENV_PATH = kept[2]
        check("106: an exception from below never carries the key out, and off a Mac the key goes to .env and back out of it",
              blew == {"error": "The keychain would not take the key."} and secret not in json.dumps(blew)
              and file_saved == {"saved": True} and in_file == (f"ANTHROPIC_API_KEY=anthropic-stand-in\nNCBI_API_KEY={other}\n", "0o600", True, other)
              and file_cleared == {"cleared": True} and left == "ANTHROPIC_API_KEY=anthropic-stand-in\n", str(in_file[:2]))

        # ── E. Check against the stub: one record asked with the key, one line back, the key scrubbed
        held.update(ELSEVIER_API_KEY=secret, ELSEVIER_INSTTOKEN=token, CLARIVATE_API_KEY="pond-key-WRONG000")
        stub_state["asked"].clear()
        c_scopus = ss.check("scopus", ctx=ctx())
        sent = stub_state["asked"][-1]
        c_wos = ss.check("wos", ctx=ctx())
        c_alex = ss.check("openalex", ctx=ctx())
        alex_q = stub_state["asked"][-1][1]
        held["NCBI_API_KEY"] = other
        c_pubmed = ss.check("pubmed", ctx=ctx())
        pubmed_q = stub_state["asked"][-1][1]
        held.pop("ELSEVIER_API_KEY")
        c_none = ss.check("scopus", ctx=ctx())
        c_epmc = refusal_of(lambda: ss.check("epmc", ctx=ctx()))
        check("106: Check sends one record's search with the key and its token, and says the database took it",
              c_scopus == {"ok": True, "said": "Scopus accepted the key."} and sent[0] == "/content/search/scopus"
              and sent[1]["count"] == "1" and sent[2].get("x-els-apikey") == secret and sent[2].get("x-els-insttoken") == token,
              str(c_scopus))
        check("106: a key refused is said in one line with its status in brackets, the key never in it",
              c_wos == {"ok": False, "said": "Web of Science refused the key (HTTP 401)."} and "WRONG000" not in json.dumps(c_wos),
              str(c_wos))
        check("106: an optional key absent, OpenAlex answers with none sent, and PubMed's key goes as api_key",
              c_alex == {"ok": True, "said": "OpenAlex answered, with no key."} and "api_key" not in alex_q
              and alex_q["per-page"] == "1" and c_pubmed == {"ok": True, "said": "PubMed accepted the key."}
              and pubmed_q.get("api_key") == other and pubmed_q["retmax"] == "1", str(alex_q))
        check("106: a required key absent sends nothing, and Europe PMC has no key to check",
              c_none == {"ok": False, "said": "There is no Scopus key to check."} and c_epmc == "Sift has no key to check for that database.")

        # the route in a smoke run: every key to the keychain in memory, none to the one stood in for here
        os.environ[ss.STUB_ENV] = stub
        calls.clear()
        ss.STUB_KEYCHAIN.held.clear()
        r_read = sift_routes.api_databases({"op": "read"})
        r_clear = sift_routes.api_databases({"op": "clear", "service": "CLARIVATE_API_KEY"})
        r_none = sift_routes.api_databases({"op": "check", "source": "wos"})
        r_save = sift_routes.api_databases({"op": "key", "service": "CLARIVATE_API_KEY", "key": secret})
        r_check = sift_routes.api_databases({"op": "check", "source": "wos"})
        r_after = sift_routes.api_databases({"op": "read"})
        del os.environ[ss.STUB_ENV]
        answers = json.dumps([r_read, r_clear, r_none, r_save, r_check, r_after])
        check("106: in a smoke run Save, Remove, the status and Check go to a keychain held in memory and the stub, and no "
              "real keychain is asked",
              r_read["saved"]["CLARIVATE_API_KEY"] is True and r_clear == {"cleared": True}
              and r_none == {"ok": False, "said": "There is no Web of Science key to check."} and r_save == {"saved": True}
              and r_check == {"ok": True, "said": "Web of Science accepted the key."} and r_after["saved"]["CLARIVATE_API_KEY"] is True
              and calls == [] and ss.STUB_KEYCHAIN.held["CLARIVATE_API_KEY"] == secret and secret not in answers, str(r_none))

        class Line:
            path, command = "/api/databases", "POST"

        argv, err = sys.argv, io.StringIO()
        sys.argv = argv + ["--verbose"]
        try:
            with contextlib.redirect_stderr(err):
                server_mod.Handler.log_message(Line(), '"%s" %s %s', "POST /api/databases HTTP/1.1", "200", "-")
        finally:
            sys.argv = argv
        check("106: the key is in no answer, no file the app writes and no log line, the route taking a POST alone",
              "/api/databases (the body is never logged)" in err.getvalue() and "/api/databases" in server_mod.POST_ONLY
              and server_mod.ROUTES["/api/databases"] is sift_routes.api_databases
              and not any(s.encode() in p.read_bytes() for p in base.rglob("*") if p.is_file() and p.name != ".env"
                          for s in (secret, token, other))
              and secret not in json.dumps(read1) and secret not in config_file.read_text(encoding="utf-8"), err.getvalue())

        # ── F. a BibTeX export: braces, accents, several authors, a DOI under doi or url
        bib = ("% an invented EBSCO export\n@article{Reed2021,\nAuthor = {Reed, Ivy and M{\\\"u}ller, J{\\o}rn and Garc\\'{\\i}a, Ana},\n"
               "Title = {Wild {Swimming} in {Ponds}: calm and cold---a study},\nJournal = {Invented Water Review},\nYear = {2021},\n"
               "Keywords = {ponds, wild swimming; calm},\nAbstract = {Nine swimmers \\& their {\\c{c}}lub spoke of calm.},\n"
               "DOI = {https://doi.org/10.5555/POND.1}\n}\n@comment{skipped}\n"
               "@phdthesis{Moss2019, title = \"Cold water and the self\", author = \"Moss, Cal\", date = {2019-06-01},\n"
               " url = {https://doi.org/10.5555/pond.2}}\n")
        kind, recs = ss.read_export(bib.encode("utf-8"), "pond export.bib", "CINAHL")
        check("106: a BibTeX export read, its braces and accents undone, several authors, the year or date, the DOI",
              kind == "bib" and [r["title"] for r in recs] == ["Wild Swimming in Ponds: calm and cold" + chr(0x2014) + "a study", "Cold water and the self"]
              and recs[0]["authors"] == "Reed, Ivy; Müller, Jørn; García, Ana" and recs[0]["year"] == "2021"
              and recs[0]["doi"] == "10.5555/pond.1" and recs[0]["journal"] == "Invented Water Review"
              and recs[0]["abstract"] == "Nine swimmers & their çlub spoke of calm." and recs[0]["keywords"] == "ponds; wild swimming; calm"
              and recs[0]["pub_type"] == "journal article" and recs[1]["year"] == "2019" and recs[1]["doi"] == "10.5555/pond.2"
              and recs[1]["pub_type"] == "dissertation" and ss.read_export(bib.encode("utf-8"), "x.txt", "C")[0] == "bib",
              str(recs)[:300])

        # ── G. a plan naming a database his list does not hold, or holds by export, runs it by export
        review = base / "pond-review"
        review.mkdir()
        ss.save(review, {"databases": ["pubmed", "openalex", "scholar"], "blocks": [{"name": "Ponds", "terms": ["pond*"]}]})
        ss.register(review)
        mine = [{"source": "openalex", "how": "api"}, {"source": "pubmed", "how": "export"}]
        dry = ss.run(review, day="2026-11-09", dry_run=True, listed=mine)
        none = ss.run(review, day="2026-11-09", dry_run=True, listed=[])
        unlisted = ss.run(review, day="2026-11-09", dry_run=True, listed=[{"source": "openalex", "how": "api"}])
        check("106, updated 12 October (118): by his list, a database held By API runs by API and one held By export by "
              "export, and one not held by export, but PubMed, Europe PMC and OpenAlex, which need no key, by API",
              [(s["source"], s["how"]) for s in dry["sources"]] == [("pubmed", "export"), ("openalex", "api"), ("scholar", "export")]
              and [s["how"] for s in none["sources"]] == ["api", "api", "export"] and unlisted["sources"][0]["how"] == "api"
              and [s["how"] for s in ss.run(review, day="2026-11-09", dry_run=True)["sources"]] == ["api", "api", "export"])
        taken = ss.take_export(review, "pubmed", bib.encode("utf-8"), "pubmed.bib", day="2026-11-09", ctx=ctx(), listed=mine)
        nope = refusal_of(lambda: ss.take_export(review, "openalex", bib.encode("utf-8"), "x.bib", day="2026-11-09", ctx=ctx(),
                                                 listed=mine))
        ran = ss.run(review, day="2026-11-09", ctx=ctx(), listed=mine)
        meta = json.loads((review / "runs" / "2026-11-09" / "run.json").read_text(encoding="utf-8"))
        check("106: PubMed held By export takes a BibTeX drop, kept as pubmed.bib, OpenAlex By API takes none, and the run "
              "searches OpenAlex alone",
              taken["taken"] == {"source": "pubmed", "records": 2, "file": "pubmed.bib"}
              and (review / "runs" / "2026-11-09" / "pubmed.bib").is_file()
              and nope == "Sift searches that database itself, so it takes no export."
              and meta["sources"]["pubmed"]["how"] == "export" and meta["sources"]["pubmed"]["state"] == "done"
              and meta["sources"]["openalex"]["how"] == "api" and meta["sources"]["scholar"]["state"] == "awaiting"
              and ran["merged"] == 3 and not any(p[0].endswith("esearch.fcgi") for p in stub_state["asked"][-3:]),
              str(meta["sources"])[:300])

        # ── H. the command line and MCP: the list and whether each key is saved, never the key
        mine_file = base / "mine.json"
        mine_file.write_text(json.dumps({"databases": [{"source": "scopus", "how": "api"}, {"source": "psycinfo", "platform": "ovid"},
                                                       {"source": "other", "name": "Pond Index"}]}), encoding="utf-8")
        held.update(ELSEVIER_API_KEY=secret)
        held.pop("ELSEVIER_INSTTOKEN", None)
        c_text = cli.run(["sift", "search", "databases", "--config", str(mine_file)])
        c_json = cli.run(["sift", "search", "databases", "--config", str(mine_file), "--json"])
        got_json = support.plain(json.loads(c_json[1]))
        check("106: sift search databases lists his databases, how each goes and whether each key is saved, never the key",
              c_text[0] == 0 and c_text[1].splitlines() == [
                  "Databases: 3.", "  Scopus: by API, ELSEVIER_API_KEY saved, ELSEVIER_INSTTOKEN not set.",
                  "  PsycInfo on Ovid: by export.", "  Pond Index: by export."]
              and [r["label"] for r in got_json["databases"]] == ["Scopus", "PsycInfo on Ovid", "Pond Index"]
              and got_json["databases"][0]["keys"][0] == {"service": "ELSEVIER_API_KEY", "label": "API key", "optional": False, "saved": True}
              and secret not in c_text[1] + c_json[1] and server_mod.CONFIG_PATH == config_file, c_text[1] + c_text[2])
        srv = mcp_server.Server(config=str(mine_file))
        m_list = srv.call(sift_mcp.DATABASES_TOOL, {})
        m_bad = srv.call(sift_mcp.DATABASES_TOOL, {"service": "ELSEVIER_API_KEY"})
        check("106: through MCP the same list only reads, and takes no input",
              m_list["isError"] is False and len(m_list["structuredContent"]["databases"]) == 3 and secret not in json.dumps(m_list)
              and sift_mcp.DATABASES_TOOL["annotations"]["readOnlyHint"] is True and m_bad["isError"] is True
              and sift_mcp.DATABASES_TOOL in mcp_server.TOOLS and mcp_server.BY_NAME["sift_search_databases"] is sift_mcp.DATABASES_TOOL)
        check("106: no command and no tool saves, removes or shows a key, and the server's instructions say so",
              not any({"key", "service", "value", "secret"} & set(t["inputSchema"]["properties"]) for t in mcp_server.TOOLS)
              and not {"key", "keys", "save-key"} & set(sift_cli.SEARCH_ACTS) and "no tool saves, removes or shows a key" in mcp_server.instructions("sift"))
    finally:
        ss.RUNNER, ss.ENV_PATH, ai_mod.security_missing, server_mod.CONFIG_PATH = kept[0], kept[2], kept[3], kept[4]
        ss.STUB_KEYCHAIN.held.clear()
        ss.STUB_KEYCHAIN.held.update(kept[5])
        os.environ.pop(ss.STUB_ENV, None)
        if kept[1] is not None:
            os.environ[ss.STUB_ENV] = kept[1]
        httpd.shutdown()
        httpd.server_close()

    # ── I. the page: Databases under Sift whatever the switch, its words, the plan screen, the docs
    pane = page.split('id="pane-databases"', 1)[1].split("</section>", 1)[0]
    block = pane.split('id="dbs-block"', 1)[1] if 'id="dbs-block"' in pane else ""
    check("106, 20 October: Databases is a category of its own in Sift's Settings, never marked as AI",
          '<h3 class="pane-title" id="dbs-sub">Databases</h3>' in block
          and "data-ai" not in block and 'id="dbs-pick"' in block and 'id="dbs-add">Add</button>' in block
          # asked for and sent with Save through Sift's own part of the shell since the family codebase's third build
          and "if (typeof dbsLoad === 'function') dbsLoad(false);" in support.text("apps/sift/static/sift_settings.js")
          and "if (dbs) body.databases = dbs;" in support.text("apps/sift/static/sift_settings.js")
          and "sift: ['general', 'formats', 'databases', 'sift', 'zotero', 'ai']" in app)
    check("106: a key's field is a password field, emptied once the key is sent, and shows only Saved or Not set",
          "type=\"password\"" in sjs and "field.value = '';" in sjs
          and "placeholder=\"${escAttr(st.saved[f.service] ? 'Saved' : 'Not set')}\"" in sjs)
