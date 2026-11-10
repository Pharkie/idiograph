from __future__ import annotations

import csv
import json
import os
import re
import shutil

from . import support
from .support import check, refusal_of, skip


@support.as_app("sift")
def test_sift_zotero(scratch):
    print("\n114. Sync to Zotero: the key in the keychain through the generalised functions, Check, a screening's records "
          "put in a collection with their PDFs in the API's three steps, tags, a second sync that updates and adds and never "
          "doubles or deletes, the preview's counts, versions and limits honoured, the command line's dry run, no MCP tool, "
          "and Sift's settings in one place (9 October)")
    import hashlib
    import http.server
    import subprocess
    import threading
    import time as time_mod
    import urllib.parse as up
    import cli
    import sift_cli
    import mcp_server
    import server as server_mod
    import sift_routes
    import sift
    import sift_search as ss
    import sift_zotero as zot

    page = support.page_text()
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    # Sift's parts of the shell, from app.js since the family codebase's third build (22 October 2026)
    sset = support.text("apps/sift/static/sift_settings.js")
    sjs = support.text("apps/sift/static/sift.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: (("async " if f"async function {name}(" in src else "") + f"function {name}(" + fn(src, name) + "\n}")
    node = shutil.which("node")
    secret = "zk-invented-0042-honeycomb"

    # ── a stub of Zotero's Web API v3 held in memory: a user library and a group, collections, items with
    # versions, attachments and their files, the three steps of an upload, Backoff, 429 and a 412 on demand,
    # and every request kept without its key header. It notes any DELETE, a key sent to the upload address and
    # any other host as a fault
    upload_url = "https://uploads.zotero.test/files"
    common = ["title", "creators", "abstractNote", "date", "language", "shortTitle", "url", "accessDate", "archive",
              "archiveLocation", "libraryCatalog", "callNumber", "rights", "extra", "tags", "collections", "relations"]
    own_fields = {"journalArticle": ["publicationTitle", "volume", "issue", "pages", "journalAbbreviation", "DOI", "ISSN"],
                  "preprint": ["genre", "repository", "archiveID", "place", "DOI"], "thesis": ["thesisType", "university", "place"],
                  "book": ["publisher", "place", "ISBN"], "bookSection": ["bookTitle", "publisher", "pages", "ISBN"],
                  "conferencePaper": ["proceedingsTitle", "conferenceName", "DOI"], "report": ["institution", "reportType"],
                  "webpage": ["websiteTitle"], "document": ["publisher"]}

    class Stub:
        def __init__(self, key, write=True):
            self.key, self.write, self.version, self.next = key, write, 10, 0
            self.collections, self.items, self.files, self.uploads, self.tokens = {}, {}, {}, {}, {}
            self.log, self.faults = [], []
            self.busy, self.backoff, self.conflict, self.race = 0, 0, False, False
            self.echo = False

        def reply(self, status, body=None, headers=None):
            data = b"" if body is None else json.dumps(body).encode("utf-8")
            return status, {k.lower(): str(v) for k, v in (headers or {}).items()}, data

        def bump(self):
            self.version += 1
            return self.version

        def made(self):
            # a key as Zotero gives one, eight letters and digits at random, so two libraries never share one
            self.next += 1
            return os.urandom(4).hex().upper()

        def obj(self, o):
            kids = sum(1 for i in self.items.values() if i["data"].get("parentItem") == o["key"])
            return {"key": o["key"], "version": o["version"], "meta": {"numChildren": kids},
                    "data": dict(o["data"], key=o["key"], version=o["version"])}

        def page(self, rows, q):
            start, limit = int(q.get("start", 0)), int(q.get("limit", 25))
            return self.reply(200, rows[start:start + limit], {"Total-Results": len(rows), "Last-Modified-Version": self.version})

        def __call__(self, method, url, headers, body):
            u = up.urlparse(url)
            q = {k: v[0] for k, v in up.parse_qs(u.query).items()}
            h = {k.lower(): v for k, v in (headers or {}).items()}
            self.log.append({"method": method, "host": u.netloc, "path": u.path, "query": q, "body": body or b"",
                             "headers": {k: v for k, v in h.items() if k != "zotero-api-key"}, "keyed": "zotero-api-key" in h})
            if method == "DELETE":
                self.faults.append("DELETE " + u.path)
                return self.reply(204)
            if url.startswith(upload_url):
                if "zotero-api-key" in h:
                    self.faults.append("the key went to the upload address")
                up_ = next((x for x in self.uploads.values() if body and body.startswith(x["prefix"].encode())), None)
                if up_ is None or not body.endswith(up_["suffix"].encode()):
                    return self.reply(400, {"error": "not the prefix, the file and the suffix"})
                up_["body"] = body[len(up_["prefix"]):len(body) - len(up_["suffix"])]
                return self.reply(201)
            if u.netloc != "api.zotero.org":
                self.faults.append("a request to " + u.netloc)
                return self.reply(404)
            if self.echo:
                return self.reply(500, {"error": f"Trouble with key {h.get('zotero-api-key')}"})
            if self.busy:
                self.busy -= 1
                return self.reply(429, {"error": "slow down"}, {"Retry-After": "2"})
            extra = {}
            if self.backoff:
                self.backoff -= 1
                extra["backoff"] = "3"
            if u.path == "/items/new":
                kind = q.get("itemType", "")
                return self.reply(200, {"itemType": kind, **{f: "" for f in common + own_fields.get(kind, [])}}) \
                    if kind in own_fields else self.reply(400, {"error": "no such type"})
            if h.get("zotero-api-key") != self.key:
                return self.reply(403, {"error": "Forbidden"})
            if u.path == "/keys/current":
                return self.reply(200, {"key": self.key, "userID": 4242, "username": "beekeeper", "access": {
                    "user": {"library": True, "files": True, "write": self.write}, "groups": {"777": {"library": True, "write": True}}}},
                    extra)
            if u.path == "/groups/777":
                return self.reply(200, {"id": 777, "version": 3, "data": {"name": "Hive readers"}})
            lib = "/groups/777" if u.path.startswith("/groups/777") else "/users/4242"
            if not u.path.startswith(lib):
                return self.reply(403, {"error": "Forbidden"})
            status, head, data = self.route(method, u.path[len(lib):], q, h, body)
            return status, dict(head, **extra), data

        def route(self, method, rest, q, h, body):
            if rest == "/collections" and method == "GET":
                return self.page([dict(c, data=dict(c["data"], key=c["key"])) for c in self.collections.values()], q)
            if rest == "/collections" and method == "POST":
                if self.race:
                    self.race = False
                    key = self.made()
                    self.collections[key] = {"key": key, "version": self.bump(), "data": {"name": "Bee keepers", "parentCollection": False}}
                if "if-unmodified-since-version" in h and int(h["if-unmodified-since-version"]) != self.version:
                    return self.reply(412, {"error": "Library has been modified since the specified version"})
                out = {"successful": {}, "success": {}, "unchanged": {}, "failed": {}}
                for n, c in enumerate(json.loads(body)):
                    key = self.made()
                    self.collections[key] = {"key": key, "version": self.bump(), "data": {"name": c["name"], "parentCollection": False}}
                    out["success"][str(n)] = key
                return self.reply(200, out, {"Last-Modified-Version": self.version})
            if rest.startswith("/collections/") and rest.endswith("/items/top"):
                ck = rest.split("/")[2]
                return self.page([self.obj(i) for i in self.items.values()
                                  if ck in i["data"].get("collections", []) and not i["data"].get("parentItem")], q)
            if rest == "/items" and method == "GET":
                return self.page([self.obj(self.items[k]) for k in q.get("itemKey", "").split(",") if k in self.items], q)
            if rest == "/items" and method == "POST":
                tok = h.get("zotero-write-token")
                if tok and tok in self.tokens:
                    return self.tokens[tok]
                out = {"successful": {}, "success": {}, "unchanged": {}, "failed": {}}
                for n, item in enumerate(json.loads(body)):
                    kind = item.get("itemType")
                    allowed = ({"itemType", "parentItem", "linkMode", "title", "contentType", "charset", "filename", "tags",
                                "relations"} if kind == "attachment" else set(["itemType"] + common + own_fields.get(kind, [])))
                    bad = [k for k in item if k not in allowed]
                    if bad:
                        out["failed"][str(n)] = {"code": 400, "message": f"'{bad[0]}' is not a valid field for type '{kind}'"}
                        continue
                    key = self.made()
                    self.items[key] = {"key": key, "version": self.bump(), "data": dict(item)}
                    out["success"][str(n)] = key
                answer = self.reply(200, out, {"Last-Modified-Version": self.version})
                if tok:
                    self.tokens[tok] = answer
                return answer
            if rest.startswith("/items/") and rest.endswith("/children"):
                pk = rest.split("/")[2]
                return self.reply(200, [self.obj(i) for i in self.items.values() if i["data"].get("parentItem") == pk])
            if rest.startswith("/items/") and rest.endswith("/file") and method == "POST":
                att = self.items.get(rest.split("/")[2])
                if att is None or h.get("if-none-match") != "*":
                    return self.reply(428 if att else 404, {"error": "If-None-Match: * wanted"})
                form = {k: v[0] for k, v in up.parse_qs((body or b"").decode()).items()}
                if "upload" in form:
                    held = self.uploads.get(form["upload"])
                    if not held or "body" not in held:
                        return self.reply(400, {"error": "no such upload"})
                    self.files[held["att"]] = held["body"]
                    att["data"].update(md5=held["md5"])
                    att["version"] = self.bump()
                    return self.reply(204, None, {"Last-Modified-Version": self.version})
                uk = f"UP{len(self.uploads) + 1}"
                self.uploads[uk] = {"att": rest.split("/")[2], "md5": form.get("md5"), "name": form.get("filename"),
                                    "size": form.get("filesize"), "mtime": form.get("mtime"), "prefix": f"[{uk}]", "suffix": f"[/{uk}]"}
                return self.reply(200, {"url": upload_url, "contentType": "application/pdf", "prefix": f"[{uk}]",
                                        "suffix": f"[/{uk}]", "uploadKey": uk})
            if rest.startswith("/items/") and rest.count("/") == 2:
                item = self.items.get(rest.split("/")[2])
                if item is None:
                    return self.reply(404)
                if method == "GET":
                    return self.reply(200, self.obj(item))
                if method == "PATCH":
                    if self.conflict:
                        self.conflict = False
                        item["data"]["tags"] = list(item["data"].get("tags", [])) + [{"tag": "to read in winter"}]
                        item["version"] = self.bump()
                        return self.reply(412, {"error": "Item has been modified since the specified version"})
                    if int(h.get("if-unmodified-since-version", "-1")) != item["version"]:
                        return self.reply(412, {"error": "Item has been modified since the specified version"})
                    item["data"].update(json.loads(body))
                    item["version"] = self.bump()
                    return self.reply(204, None, {"Last-Modified-Version": self.version})
            return self.reply(404, {"error": f"no route {method} {rest}"})

    def serve(stub):
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def go(self):
                n = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(n) if n else None
                host, _, rest = self.path.lstrip("/").partition("/")
                status, head, data = stub(self.command, f"https://{host}/{rest}", dict(self.headers.items()), body)
                self.send_response(status)
                for k, v in head.items():
                    self.send_header(k, v)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            do_GET = do_POST = do_PATCH = do_DELETE = go

        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
        return httpd

    # ── an invented review on urban beekeeping, its screening in a run's folder
    base = scratch / "sift-zotero-114"
    shutil.rmtree(base, ignore_errors=True)
    review = base / "Bee keepers"
    folder = review / "runs" / "2026-10-01"
    folder.mkdir(parents=True)
    (review / "search_plan.json").write_text(json.dumps({"name": "Bee keepers", "versions": []}), encoding="utf-8")
    head = ["rec_id", "title", "authors", "year", "journal", "doi", "pub_type", "url", "sources", "abstract"]
    rows = [["H01", "Keeping bees on city roofs", "Comb, A.; Drone, B.", "2020", "Invented Apiculture", "10.5555/hive.1",
             "article", "https://example.org/hive/1", "OpenAlex", "Twelve keepers spoke of roofs and wind."],
            ["H02", "Swarm season diaries", "Wax, C.", "2021", "Invented University", "10.5555/hive.2", "dissertation", "",
             "PQDT", "Diaries kept through a swarm season."],
            ["H03", "Queenless colonies and the keeper's worry", "Nectar Jones; Pollen Smith", "2019", "Bee Preprints",
             "10.5555/hive.3", "preprint", "", "OpenAlex", "Keepers worried for colonies with no queen."],
            ["H04", "A survey of honey prices", "Price, D.", "2018", "Invented Markets", "10.5555/hive.4", "Journal Article", "",
             "PubMed", "A survey with no interviews."],
            ["H05", "Hive inspections as care", "Frame, E.", "2022", "Invented Apiculture", "10.5555/hive.5", "article", "",
             "OpenAlex", "Nine keepers described inspections as a kind of care."],
            ["H06", "Bees in the classroom", "Teach, F.", "2023", "A Book of Bees", "", "book chapter", "", "OpenAlex",
             "A chapter on teaching with hives."]]
    with open(folder / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(head)
        w.writerows(rows)
    (folder / sift.REASONS_NAME).write_text("stage,code,meaning\nta,E2,Not qualitative\nft,F1,No lived experience\n", encoding="utf-8")
    (folder / sift.PDF_DIR).mkdir()
    pdf_one, pdf_two = b"%PDF-1.4 roofs and wind", b"%PDF-1.4 a swarm season"
    (folder / sift.PDF_DIR / "H01.pdf").write_bytes(pdf_one)
    (folder / sift.PDF_DIR / "H02.pdf").write_bytes(pdf_two)
    for rec in ("H01", "H02", "H03", "H05"):
        sift.decide(folder, rec, "ta", "include")
    for rec in ("H01", "H02", "H03"):
        sift.decide(folder, rec, "ft", "include")
    sift.decide(folder, "H04", "ta", "exclude", "E2")
    sift.decide(folder, "H06", "ta", "maybe")

    held = {}

    class Done:
        def __init__(self, code, out=""):
            self.returncode, self.stdout, self.stderr = code, out, ""

    def keychain(argv, **_):
        act, service = argv[1], argv[argv.index("-s") + 1]
        if act == "add-generic-password":
            held[service] = argv[argv.index("-w") + 1]
            return Done(0)
        if act == "delete-generic-password":
            return Done(0 if held.pop(service, None) else 44)
        return Done(0, held[service] + "\n") if service in held else Done(44)

    config_file = base / "config.json"
    config_file.write_text(json.dumps(server_mod.defaults()), encoding="utf-8")
    kept = (ss.RUNNER, os.environ.pop(ss.STUB_ENV, None), server_mod.CONFIG_PATH, dict(ss.STUB_KEYCHAIN.held),
            server_mod.STATE_MEMORY)
    ss.RUNNER = keychain
    server_mod.CONFIG_PATH = config_file
    answers = []
    sleeps = []
    try:
        # ── A. the settings and the key, through the generalised functions
        server_mod.api_settings({"zotero": {"library": "nowhere", "user_id": "42 42", "group_id": "x7y"}})
        stored = json.loads(config_file.read_text(encoding="utf-8"))["zotero"]
        server_mod.api_settings({"interviewer": "Adam"})
        still = json.loads(config_file.read_text(encoding="utf-8"))["zotero"]
        check("114, 12 October: the Zotero settings are the library, his own unless a group's is named, and the group's "
              "id, digits alone, a user id passed over since the key names its own, saved with Settings and left by a save "
              "that sends none",
              server_mod.defaults()["zotero"] == {"library": "user", "group_id": ""}
              and stored == {"library": "user", "group_id": "7"} and still == stored
              and zot.clean_settings({"library": "group", "group_id": "777"}) == {"library": "group", "group_id": "777"},
              str(stored))
        before = sift_routes.api_zotero({"op": "read"})
        saved = sift_routes.api_zotero({"op": "key", "key": secret})
        after = sift_routes.api_zotero({"op": "read"})
        answers += [before, saved, after]
        check("114: the key goes to the keychain under ZOTERO_API_KEY through sift_search's own save_key, and read says only "
              "Saved or Not set, never what it is",
              "ZOTERO_API_KEY" in ss.OTHER_SERVICES and "ZOTERO_API_KEY" not in ss.SERVICES and held.get("ZOTERO_API_KEY") == secret
              and before["saved"] is False and saved == {"saved": True} and after == {"settings": stored, "saved": True}
              and zot.key_saved() is True and refusal_of(lambda: ss.save_key("SOMETHING_ELSE", "x")) == "Sift keeps no key by that name.",
              str(after))

        # ── B. Check against the stub
        stub = Stub(secret)
        cfg = {"zotero": stored}
        ok = zot.check(cfg, call=stub)
        group = zot.check(cfg, {"library": "group", "group_id": "777"}, call=stub)
        old_user = zot.check(cfg, {"library": "user", "user_id": "99"}, call=stub)
        reader = zot.check(cfg, call=Stub(secret, write=False))
        refused = zot.check(cfg, call=Stub("another-key"))
        answers += [ok, group, old_user, reader, refused]
        check("114, 12 October: the check reads the key's own record and the library's name and says in one line whether "
              "the key works, his own library the key's owner's whatever user id an older config gives, never the key",
              ok == {"ok": True, "said": "The key works with the library of beekeeper."}
              and group["said"] == "The key works with the group library Hive readers." and group["ok"] is True
              and old_user == ok
              and reader["said"] == "The key reads the library of beekeeper but cannot write to it. Give it write access on zotero.org."
              and refused == {"ok": False, "said": "Zotero did not take that key."}
              and [e["path"] for e in stub.log] == ["/keys/current", "/keys/current", "/groups/777", "/keys/current"],
              str([ok, group, old_user]))

        # creators from every database's way of writing authors, invented names throughout
        names = lambda a: [(c.get("lastName") or c.get("name"), c.get("firstName", "")) for c in zot.creators_of(a)]
        shapes = {"Heron M.": [("Heron", "M.")], "La Moss J.T.": [("La Moss", "J. T.")],
                  "Birch JJ, Elm AR, Yew E, Rowan RA.": [("Birch", "J. J."), ("Elm", "A. R."), ("Yew", "E."), ("Rowan", "R. A.")],
                  "Rook Bara SF, Lark-Wing M, et al.": [("Rook Bara", "S. F."), ("Lark-Wing", "M.")],
                  "Pine, J; Fir, M; Gale, SL": [("Pine", "J."), ("Fir", "M."), ("Gale", "S. L.")],
                  "Ash, Nadia ; Vale-Dury, Jean": [("Ash", "Nadia"), ("Vale-Dury", "Jean")], "Baker, Michael": [("Baker", "Michael")],
                  "J Fern; AC Reed": [("Fern", "J."), ("Reed", "A. C.")], "Justin Oak": [("Oak", "Justin")],
                  "Ash, William J.": [("Ash", "William J.")], "Weir J.-P.": [("Weir", "J.-P.")], "Moss": [("Moss", "")]}
        got_shapes = {a: names(a) for a in shapes}

        class OneRecord:
            def __init__(self, authors):
                self.authors = authors

            def cell(self, rec, k):
                return {"authors": self.authors, "title": "Invented hive notes", "year": "2020"}.get(k, "")
        two = "Heron M.; Wren T.C."
        made_then = {"creators": zot.creators_before(two), "title": "Invented hive notes", "extra": "Sift: H01", "collections": ["C1"]}
        changed = dict(made_then, creators=[{"creatorType": "author", "lastName": "Heron", "firstName": "Mia"}])
        check("114, 12 October: a record's authors become Zotero's creators however the database wrote them, a surname "
              "and its initials, Europe PMC's list parted by commas, Last, First and First Last, initials as J. J., and et "
              "al. dropped, and a sync puts right creators exactly as a sync before wrote them, never ones changed since",
              got_shapes == shapes
              and zot.patch_of(made_then, OneRecord(two), "H01", "C1", [], True) == {"creators": [
                  {"creatorType": "author", "lastName": "Heron", "firstName": "M."},
                  {"creatorType": "author", "lastName": "Wren", "firstName": "T. C."}]}
              and zot.patch_of(changed, OneRecord(two), "H01", "C1", [], True) == {},
              str({a: g for a, g in got_shapes.items() if g != shapes[a]}))

        # ── C. the preview, nothing written
        csv_before = (folder / sift.CSV_NAME).read_bytes()
        preview = zot.sync(folder, cfg, dry_run=True, call=stub, sleep=sleeps.append)
        answers.append(preview)
        check("114: the preview says how many items Sync adds, updates and leaves and how many PDFs it uploads, into the "
              "collection named for the Sift project, made when it is not there, and writes nothing anywhere",
              preview == {"collection": "Bee keepers", "collection_there": False, "chosen": 3, "adds": 3, "updates": 0, "leaves": 0,
                          "pdfs": 2, "said": "Into the collection Bee keepers, which it makes: adds 3 items, updates 0 and leaves 0, "
                                             "and uploads 2 PDFs."}
              and not stub.collections and not stub.items and (folder / sift.CSV_NAME).read_bytes() == csv_before
              and all(e["method"] == "GET" for e in stub.log), str(preview))

        # ── D. the first sync
        stub.log.clear()
        first = zot.sync(folder, cfg, call=stub, sleep=sleeps.append)
        answers.append(first)
        items = {i["data"].get("extra", "").split("Sift: ")[-1]: i for i in stub.items.values() if i["data"]["itemType"] != "attachment"}
        sc = sift.load(folder)
        keys = {rec: sc.cell(rec, sift.ZOTERO_COLUMN) for rec in sc.ids}
        coll = next(iter(stub.collections))
        made_coll = next(e for e in stub.log if e["method"] == "POST" and e["path"].endswith("/collections"))
        check("114: the collection is made at the library's top, named for the Sift project, sent with the library's version",
              len(stub.collections) == 1 and stub.collections[coll]["data"] == {"name": "Bee keepers", "parentCollection": False}
              and made_coll["headers"].get("if-unmodified-since-version") == "10" and "zotero-write-token" in made_coll["headers"],
              str(made_coll["headers"]))
        one, two, three = items.get("H01", {}).get("data", {}), items.get("H02", {}).get("data", {}), items.get("H03", {}).get("data", {})
        check("114: each record accepted at full text becomes an item of its type with its fields mapped, a journal article, a "
              "thesis whose DOI goes in Extra since the type has no field for it, and a preprint",
              one.get("itemType") == "journalArticle" and one.get("title") == "Keeping bees on city roofs"
              and one.get("creators") == [{"creatorType": "author", "lastName": "Comb", "firstName": "A."},
                                          {"creatorType": "author", "lastName": "Drone", "firstName": "B."}]
              and one.get("date") == "2020" and one.get("publicationTitle") == "Invented Apiculture" and one.get("DOI") == "10.5555/hive.1"
              and one.get("url") == "https://example.org/hive/1" and one.get("abstractNote") == "Twelve keepers spoke of roofs and wind."
              and one.get("extra") == "Sift: H01" and one.get("collections") == [coll]
              and two.get("itemType") == "thesis" and two.get("university") == "Invented University" and "DOI" not in two
              and two.get("extra") == "DOI: 10.5555/hive.2\nSift: H02"
              and three.get("itemType") == "preprint" and three.get("repository") == "Bee Preprints"
              and three.get("creators")[0] == {"creatorType": "author", "lastName": "Jones", "firstName": "Nectar"},
              json.dumps([one, two, three])[:400])
        check("114: the item types follow the record's type, a journal article unless it names another, a book chapter never a book",
              [zot.item_type(t, j) for t, j in [("article", ""), ("Journal Article; Review", ""), ("dissertation", ""), ("Thesis", ""),
                                                ("posted-content", ""), ("book chapter", ""), ("Book", ""), ("Conference Paper", ""),
                                                ("report", ""), ("Case Reports", ""), ("web page", ""), ("", "Some Journal"), ("", "")]]
              == ["journalArticle", "journalArticle", "thesis", "thesis", "preprint", "bookSection", "book", "conferencePaper",
                  "report", "journalArticle", "webpage", "journalArticle", "document"])
        check("114: each item carries its decisions and a reject's reason as tags of Sift's own, and the CSV keeps each item's key "
              "in zotero_key, a column of its own",
              [t["tag"] for t in one.get("tags", [])] == ["sift:include-ta", "sift:include-ft"]
              and zot.tags_of(sc, sift.states(sift.read_log(folder)), "H04") == ["sift:exclude-ta", "sift:reason-E2"]
              and all(keys[r] == items[r]["key"] for r in ("H01", "H02", "H03")) and keys["H04"] == keys["H05"] == keys["H06"] == ""
              and sc.header[-1] == "zotero_key" and first["added"] == 3 and first["uploaded"] == 2
              and first["said"] == "Added 3 items, updated 0 and left 0, and uploaded 2 PDFs, in the collection Bee keepers.",
              str(keys))
        atts = [i for i in stub.items.values() if i["data"]["itemType"] == "attachment"]
        file_calls = [e for e in stub.log if e["path"].endswith("/file") or e["host"] == "uploads.zotero.test"]
        auth = file_calls[0]
        auth_form = {k: v[0] for k, v in up.parse_qs(auth["body"].decode()).items()}
        check("114: each PDF goes up as its item's attachment in the API's three steps, authorised with its MD5, name, size and "
              "time, uploaded with the prefix and suffix around it, never with the key, and registered",
              len(atts) == 2 and {a["data"]["parentItem"] for a in atts} == {items["H01"]["key"], items["H02"]["key"]}
              and all(a["data"]["linkMode"] == "imported_file" and a["data"]["contentType"] == "application/pdf" for a in atts)
              and [(e["method"], e["host"], "upload" in e["body"].decode("latin-1")[:7]) for e in file_calls[:3]]
              == [("POST", "api.zotero.org", False), ("POST", "uploads.zotero.test", False), ("POST", "api.zotero.org", True)]
              and auth["headers"].get("if-none-match") == "*" and auth_form["md5"] == hashlib.md5(pdf_one).hexdigest()
              and auth_form["filesize"] == str(len(pdf_one)) and auth_form["filename"] == "Comb 2020 Keeping bees on city roofs.pdf"
              and auth_form["mtime"].isdigit() and file_calls[1]["keyed"] is False
              and sorted(stub.files.values()) == sorted([pdf_one, pdf_two]) and not stub.faults,
              str([(e["method"], e["host"], e["path"]) for e in file_calls]))

        # ── E. the second sync: a decision changed and one added, nothing doubled, nothing deleted
        sift.decide(folder, "H03", "ft", "exclude", "F1")
        sift.decide(folder, "H05", "ft", "include")
        count_before = len(stub.items)
        again = zot.sync(folder, cfg, dry_run=True, call=stub, sleep=sleeps.append)
        second = zot.sync(folder, cfg, call=stub, sleep=sleeps.append)
        answers += [again, second]
        three_now = stub.items[items["H03"]["key"]]["data"]
        sc = sift.load(folder)
        check("114: a sync again adds what is new and updates what changed, matched by the key the CSV keeps, so nothing is "
              "doubled, and the preview said so first",
              again["adds"] == 1 and again["updates"] == 1 and again["leaves"] == 2 and again["pdfs"] == 0
              and again["said"] == "Into the collection Bee keepers: adds 1 item, updates 1 and leaves 2, and uploads 0 PDFs."
              and second["added"] == 1 and second["updated"] == 1 and second["left"] == 2 and len(stub.items) == count_before + 1
              and len(stub.collections) == 1 and sc.cell("H05", sift.ZOTERO_COLUMN) != "", str(again))
        check("114: a record no longer chosen keeps its item and loses only its tags of Sift's own, and Sift never deletes",
              items["H03"]["key"] in stub.items and [t["tag"] for t in three_now["tags"]] == []
              and three_now["title"] == "Queenless colonies and the keeper's worry"
              and not any(e["method"] == "DELETE" for e in stub.log) and not stub.faults, str(three_now["tags"]))
        patches = [e for e in stub.log if e["method"] == "PATCH"]
        check("114: every change of an item sends If-Unmodified-Since-Version with the version it was read at",
              patches and all(e["headers"].get("if-unmodified-since-version", "").isdigit() for e in patches), str(len(patches)))

        # ── F. a field he filled kept, the tags he added kept, a 412 read again, Backoff and 429 honoured
        stub.items[items["H01"]["key"]]["data"].update(title="Roof bees, as he corrected it", abstractNote="")
        stub.items[items["H01"]["key"]]["data"]["tags"].append({"tag": "chapter 2"})
        stub.items[items["H01"]["key"]]["version"] = stub.bump()
        stub.conflict, stub.busy, stub.backoff = True, 1, 1
        sleeps.clear()
        third = zot.sync(folder, cfg, which="all", call=stub, sleep=sleeps.append)
        answers.append(third)
        one_now = stub.items[items["H01"]["key"]]["data"]
        check("114: a field filled in Zotero is never written over, an empty one is filled, his own tags stay, and a change "
              "refused for a newer version is read again and tried once more",
              one_now["title"] == "Roof bees, as he corrected it" and one_now["abstractNote"] == "Twelve keepers spoke of roofs and wind."
              and [t["tag"] for t in one_now["tags"]].count("chapter 2") == 1
              and any("to read in winter" == t["tag"] for i in stub.items.values() for t in i["data"].get("tags", []))
              and third["said"].startswith("Added 2 items, updated 2 and left 2,") and not stub.faults, third["said"])
        check("114: a 429 waits its Retry-After and a Backoff header holds the next request back, in seconds",
              sleeps[:2] == [2.0, 3.0], str(sleeps))
        every = zot.sync(folder, cfg, which="all", dry_run=True, call=stub)
        some = zot.sync(folder, cfg, which="filter", ids=["H06", "H04", "H99"], dry_run=True, call=stub)
        check("114, updated 12 October (126): the records are those included at full text, the rows the table shows by "
              "their ids, or every record, and any other choice is refused",
              every["chosen"] == 6 and every["adds"] == 0 and some["chosen"] == 2
              and refusal_of(lambda: zot.sync(folder, cfg, which="some", dry_run=True, call=stub))
              == "The records are those included at full text, the table's rows, or every record.", str(every))

        # ── G. an item matched by its DOI when the CSV lost its key, and a collection made meanwhile found
        lost = folder / sift.CSV_NAME
        text = lost.read_text(encoding="utf-8").replace(items["H01"]["key"], "")
        lost.write_text(text, encoding="utf-8")
        relinked = zot.sync(folder, cfg, which="all", call=stub)
        check("114: an item the CSV lost the key of is found in the collection by its DOI and linked again, never made twice",
              relinked["added"] == 0 and sift.load(folder).cell("H01", sift.ZOTERO_COLUMN) == items["H01"]["key"]
              and len([i for i in stub.items.values() if i["data"].get("DOI") == "10.5555/hive.1"]) == 1, str(relinked))
        shutil.copytree(review, base / "Bee copy")
        racer = Stub(secret)
        racer.race = True
        raced = zot.sync(base / "Bee copy" / "runs" / "2026-10-01", cfg, which="all", call=racer)
        check("114: a collection of the same name made while Sync looked is found by the 412 the library's version brings, "
              "never made twice", len(racer.collections) == 1 and raced["added"] == 6, str(racer.collections))

        # ── H. errors in one plain line with the key scrubbed, and no key in any file or answer
        echo = Stub(secret)
        echo.echo = True
        said = refusal_of(lambda: zot.sync(folder, cfg, call=echo))
        none_said = ""
        held.pop("ZOTERO_API_KEY", None)
        none_said = refusal_of(lambda: zot.sync(folder, cfg, call=stub))
        held["ZOTERO_API_KEY"] = secret
        stub.log.clear()
        own = zot.sync(folder, {"zotero": {"library": "user", "user_id": "99"}}, dry_run=True, call=stub)
        own_paths = [e["path"] for e in stub.log]
        no_group = refusal_of(lambda: zot.sync(folder, {"zotero": {"library": "group"}}, call=stub))
        files = [p.read_bytes() for p in list(folder.rglob("*")) + [config_file] if p.is_file()]
        sent = [json.dumps({k: (v.decode("latin-1") if isinstance(v, bytes) else v) for k, v in e.items()}) for e in stub.log]
        check("114, 12 October: an error is one plain line, the key scrubbed from what Zotero said, with no key or no group id "
              "Sync says where to give it, and his own library is the key's owner's, read from the key first",
              said.startswith("Zotero answered 500 while checking the key:") and "[key]" in said and secret not in said
              and none_said == "There is no Zotero key saved. Give it in Settings, Sift."
              and no_group == "Give the group library's id in Settings, Sift."
              and own_paths[0] == "/keys/current" and all(p.startswith("/users/4242/") for p in own_paths[1:])
              and own["collection"] == preview["collection"], said)
        check("114: the key is never in an answer, a file of the screening or the settings, or a request but the API's own header",
              not any(secret in json.dumps(a) for a in answers) and not any(secret.encode() in b for b in files)
              and not any(secret in s for s in sent) and all(e["keyed"] for e in stub.log if e["host"] == "api.zotero.org"
                                                             and e["path"] != "/items/new"))
        with_key = ss.scrub(f"bad {secret} here", [secret])
        check("114: the lines a sync says pass through the same scrub as the searches'", with_key == "bad [key] here", with_key)

        # ── I. the route and the command line against the stub on a loopback port, the smoke run's own keychain
        shutil.copytree(review, base / "Bee readers")
        review, folder_main = base / "Bee readers", folder
        folder = review / "runs" / "2026-10-01"
        httpd = serve(Stub("stub-zotero_api_key"))
        os.environ[ss.STUB_ENV] = f"http://127.0.0.1:{httpd.server_address[1]}"
        try:
            ss.STUB_KEYCHAIN.held.pop("ZOTERO_API_KEY", None)
            server_mod.STATE_MEMORY = {"recent": []}
            sift_routes.api_sift_review({"op": "open", "folder": str(review)})
            plan = sift_routes.api_zotero({"op": "plan", "folder": str(folder), "which": "included"})
            started = sift_routes.api_zotero({"op": "sync", "folder": str(folder), "which": "included"})
            for _ in range(200):
                prog = sift_routes.api_zotero({"op": "progress", "folder": str(folder)})
                if not prog["running"]["running"]:
                    break
                time_mod.sleep(0.05)
            busy = refusal_of(lambda: sift_routes.api_zotero({"op": "nothing"}))
            check("114: the route previews, starts a sync on its own thread and says how it goes and what it did, and refuses an "
                  "op it does not know",
                  plan["adds"] == 3 and plan["collection"] == "Bee keepers" and started["started"] is True
                  and prog["running"]["result"]["added"] == 3 and prog["running"]["done"] == prog["running"]["of"]
                  and busy == "The op is read, key, clear, check, plan, sync or progress.", str(prog["running"])[:300])
            code, out, err = cli.run(["sift", "zotero", "sync", str(folder), "--dry-run", "--config", str(config_file)])
            code_j, out_j, _ = cli.run(["sift", "zotero", "sync", str(folder), "--all", "--dry-run", "--json", "--config", str(config_file)])
            wrong = cli.run(["sift", str(folder), "sync"])
            csv_now = (folder / sift.CSV_NAME).read_bytes()
            check("114: the command line's dry run says the same preview in one line, writes nothing and never prints the key, "
                  "and sync is an act of sift zotero alone",
                  code == 0 and out.strip().startswith("Into the collection Bee keepers: adds 0 items,") and err == ""
                  and code_j == 0 and json.loads(out_j)["chosen"] == 6 and json.loads(out_j)["which"] == "all"
                  and "stub-zotero_api_key" not in out + out_j and (folder / sift.CSV_NAME).read_bytes() == csv_now
                  and wrong[0] == 1 and "sync is an act of sift zotero: sift zotero sync <folder>." in wrong[2], out + wrong[2])
            code_s, out_s, _ = cli.run(["sift", "zotero", "sync", str(folder), "--all", "--config", str(config_file)])
            check("114: without the dry run the command line syncs and says what it did",
                  code_s == 0 and out_s.strip().startswith("Added 3 items,"), out_s)
        finally:
            del os.environ[ss.STUB_ENV]
            httpd.shutdown()
            httpd.server_close()
            folder = folder_main

        # ── J. Start again keeps the keys, and the record and the table leave the column out
        sift.reset(folder)
        sc = sift.load(folder)
        view = sift.record_view(sc, {}, "H01")
        check("114: Start again keeps each item's key, and the record's foot and the table's columns leave zotero_key out",
              sc.cell("H01", sift.ZOTERO_COLUMN) == items["H01"]["key"] and all(n != "zotero_key" for n, _ in view["more"])
              and "csv:zotero_key" not in sift.extra_columns(sc) and "zotero_key" not in sift.RESET_COLUMNS)
    finally:
        ss.RUNNER, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY = kept[0], kept[2], kept[4]
        if kept[1] is not None:
            os.environ[ss.STUB_ENV] = kept[1]
        ss.STUB_KEYCHAIN.held.clear()
        ss.STUB_KEYCHAIN.held.update(kept[3])

    # ── K. no MCP tool syncs or reads the key
    check("114: no MCP tool syncs to Zotero or takes a key, and the server's instructions name none",
          not any("zotero" in t["name"] or t["command"][1] in sift_cli.ZOTERO_ACTS for t in mcp_server.TOOLS)
          and not any({"key", "service"} & set(t["inputSchema"]["properties"]) for t in mcp_server.TOOLS)
          and "zotero" not in mcp_server.instructions("sift").lower())

    # ── L. the page: Export to Zotero in Export's menu (Sync to Zotero in the title bar until 12 October, area 121),
    # its card, and Zotero under Sift in Settings
    pane = page.split('id="pane-zotero"', 1)[1].split("</section>", 1)[0]
    zpart = pane.split('<div class="zot" id="zot-block">', 1)[1]
    check("114, 12 October: a choice of no records asks Zotero nothing and leaves Export off",
          "if (!sfZotCounts()[which]) return;" in fn(sjs, "sfZotPlan")
          and fn(sjs, "sfZotPlan").index("if (!sfZotCounts()[which]) return;") < fn(sjs, "sfZotPlan").index("await api(")
          and "!z.plan || !work;" in fn(sjs, "sfZotDraw"))
    check("114, updated 12 October (121): Export to Zotero in Export's menu opens its card, and a change of the records "
          "chosen asks the preview again",
          "$('sf-zotero').onclick = () => sfMenuTake(sfZotOpen);" in sjs
          and "$('sf-zot-which').addEventListener('change', sfZotPlan);" in sjs)
    go = fn(sjs, "sfZotGo")
    check("114: the card asks the preview as it opens and as the choice changes, the table's rows sent by their ids, then "
          "Export starts and is asked after until it ends, the card free to close, and Esc closes it",
          "sfZotPlan();" in fn(sjs, "sfZotOpen") and "op: 'plan', folder: z.folder, which, ids: which === 'filter' ? SF.ids.slice() : undefined" in fn(sjs, "sfZotPlan")
          and go.index("op: 'sync'") < go.index("op: 'progress'") and "'sift.zot.exporting_of'" in go
          and "if ($('sf-zot').hidden && z.said) say(z.said, 9000);" in go
          and "if (!$('sf-zot').hidden) {" in fn(sjs, "sfKeyDown") and "$('sf-zot').hidden = true;" in fn(sjs, "sfLeave")
          and not re.search(r"\b[Ss]top", fn(sjs, "sfZotGo") + fn(sjs, "sfZotDraw") + fn(sjs, "sfZotPlan")))
    check("114, 12 October: Zotero stands last under Sift in Settings outside the AI switch: the library, the group's id, "
          "the key showing only Saved or Not set with Save and Remove, checked as soon as it is saved or the library "
          "changes, and its one line, no user id and no Check",
          "data-ai" not in zpart and zpart.index('id="zot-library"') < zpart.index('id="zot-group"')
          < zpart.index('id="zot-key"') < zpart.index('id="zot-said"') and 'id="zot-user"' not in zpart and 'id="zot-check"' not in zpart
          and "zotCheck();" in fn(sset, "zotSaveKey") and "zotCheck();" in fn(sset, "zotBoot")
          and "$('zot-group').addEventListener('change', zotCheck);" in fn(sset, "zotBoot")
          and 'type="password"' in zpart.split('id="zot-key"', 1)[1].split(">", 1)[0]
          and "$('zot-key').value = '';" in fn(sset, "zotSaveKey") and fn(sset, "zotSaveKey").index("$('zot-key').value = '';") < fn(sset, "zotSaveKey").index("await api(")
          and "const now = zotNow();" in fn(sset, "zotCheck") and "op: 'check', settings: now" in fn(sset, "zotCheck")
          # opened after the AI's parts and sent with Save through Sift's own part of the shell (the third build)
          and "zotLoad();" in fn(sset, "sfpLater") and "if (own && own.settingsLater) own.settingsLater();" in fn(app, "openSettings")
          and "if (zot) body.zotero = zot;" in fn(sset, "sfpBody") and "if (a.settingsBody) a.settingsBody(body);" in fn(app, "saveSettings")
          and "key" not in fn(sset, "zotNow").lower())
    if not node:
        skip("114: in node, Save sends the library and the group's id only when they change, digits alone", "node is not installed")
    else:
        script = scratch / "sift-zotero-114.js"
        script.write_text(
            "const els = {};\nconst $ = (id) => (els[id] = els[id] || { value: '' });\nconst ZOT = { opened: null };\n"
            + whole(sset, "zotNow") + "\n" + whole(sset, "zotBody") + "\n"
            + "const out = [zotBody()];\nZOT.opened = { library: 'user', group_id: '' };\n"
            + "$('zot-library').value = 'user'; $('zot-group').value = '';\nout.push(zotBody());\n"
            + "$('zot-library').value = 'group'; $('zot-group').value = ' 7a77 ';\nout.push(zotBody());\n"
            + "console.log(JSON.stringify(out));\n", encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        check("114: in node, Save sends the library and the group's id only when they change, digits alone",
              ran.returncode == 0 and json.loads(ran.stdout or "null") == [None, None, {"library": "group", "group_id": "777"}],
              (ran.stdout or ran.stderr)[:200])

    # ── M. the app packs the module
    check("114: the Mac app packs the module",
          '"sift_zotero",' in support.source("packaging/build_mac.py").read_text(encoding="utf-8"))
