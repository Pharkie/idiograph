from __future__ import annotations

import http.server
import json
import os
import socket
import threading
from datetime import date
from pathlib import Path

from .support import check, urllib_path


def test_sweep_cards(scratch):
    print("\n163. The cards, the print views, the reference page and the empty and error states, swept against the "
          "written rules on 17 October: each break measured in a shot of invented data and mended, nothing for taste. "
          "Since the test review of 18 October its colours, contrasts and layouts are review shots, and the failures "
          "said in plain words stay")
    plain_errors(scratch)


def plain_errors(scratch):
    """17 October, later (fixes7): a failed request of Sift's said in plain words on the screen, which database,
    what happened and its status in brackets, never the address, the query or the key, and the run's own log
    keeping the detail, all against a stub of invented answers on loopback."""
    import sift
    import sift_search as ss

    secret = "INVENTEDKEY77"

    class Down(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path.endswith("/works"):
                body, code = b"this is not json", 200
            elif path.endswith("/content/search/scopus"):
                body, code = f'{{"error": "key {self.headers.get("X-ELS-APIKey")} refused"}}'.encode(), 401
            else:
                body, code = b'{"error": "unavailable at /internal/route"}', 503
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Down)
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    stub = f"http://127.0.0.1:{httpd.server_address[1]}"
    ctx = lambda: ss.Context(base={s: stub + urllib_path(u) for s, u in ss.ENDPOINTS.items()}, pause=lambda s: None)
    # a loopback port with nothing listening on it, for a database that does not answer
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        shut = s.getsockname()[1]

    def raised(fn):
        try:
            fn()
        except ss.SearchError as e:
            return e
        return ss.SearchError("no failure")

    kept_clock, kept_env = ss.CLOCK, os.environ.pop(ss.STUB_ENV, None)
    try:
        # every key from the smoke's keychain in memory, every request to the stub on loopback
        os.environ[ss.STUB_ENV] = stub
        c = ctx()
        down = raised(lambda: ss.get(c, c.base["pubmed"] + "esearch.fcgi", {"db": "pubmed", "term": "garden ponds"}))
        unread = raised(lambda: ss.get(c, c.base["openalex"], {"search": "garden ponds"}))
        c.keep(secret)
        refused = raised(lambda: ss.get(c, c.base["scopus"], {"query": "garden ponds"}, {"X-ELS-APIKey": secret}, tries=1))
        closed = ss.Context(base={"epmc": f"http://127.0.0.1:{shut}/europepmc/webservices/rest/search"}, pause=lambda s: None)
        gone = raised(lambda: ss.get(closed, closed.base["epmc"], {"query": "garden ponds"}, tries=1))
        said = [str(e) for e in (down, unread, refused, gone)]
        check("163: a request of Sift's that fails says on the screen in plain words which database and what happened, its "
              "status in brackets, never the address, the query or what the server's answer held, which its detail keeps "
              "for the run's log, scrubbed of the key",
              said == ["PubMed did not answer (HTTP 503).", "OpenAlex sent something Sift could not read.",
                       "Scopus refused the key (HTTP 401).", "Europe PMC did not answer."]
              and down.status == 503 and refused.status == 401 and gone.status == 0
              and down.detail.startswith("HTTP 503 from 127.0.0.1:") and "unavailable at /internal/route" in down.detail
              and "not JSON" in unread.detail and "[key]" in refused.detail and secret not in refused.detail + str(refused)
              and gone.detail.startswith(f"No answer from 127.0.0.1:{shut}")
              and not any(w in s for s in said for w in ("127.0.0.1", "http", "{", "ponds", "esearch", "/")), str(said))

        # a run of an invented review whose one database fails: the screen's row in plain words, its log in full
        ss.CLOCK = lambda: date(2031, 7, 5)
        review = Path(scratch) / "fixes7-ponds"
        review.mkdir(parents=True, exist_ok=True)
        if not (review / ss.PLAN_NAME).exists():
            ss.new_plan(review, "Garden ponds", "How do people live beside a garden pond?")
        ss.save(review, {"databases": ["pubmed"], "blocks": [{"name": "Ponds", "terms": ["pond"]}]})
        ran = ss.run(review, which="newest", day="2031-07-05", ctx=ctx(), listed=[{"source": "pubmed", "how": "api"}])
        row = (ran.get("rows") or [{}])[0]
        run_dir = review / ss.RUNS_DIR / ran["date"]
        meta = json.loads((run_dir / ss.RUN_FILE).read_text(encoding="utf-8"))
        log = (run_dir / sift.SEARCHES_NAME).read_text(encoding="utf-8")
        check("163: a run's database that failed is said on the screen in plain words, `said`, where its run.json and its "
              "log.csv, the search log PRISMA-S asks for, keep the status, the address and the start of the answer",
              row.get("state") == "failed" and row.get("said") == "PubMed did not answer (HTTP 503)."
              and meta["sources"]["pubmed"]["note"].startswith("HTTP 503 from 127.0.0.1:")
              and "unavailable at /internal/route" in meta["sources"]["pubmed"]["note"]
              and meta["sources"]["pubmed"]["said"] == "PubMed did not answer (HTTP 503)."
              and "failed: HTTP 503 from 127.0.0.1:" in log and "failed: HTTP 503 from 127.0.0.1:" in row.get("note", ""),
              str(row)[:300])
        del meta["sources"]["pubmed"]["said"]
        (run_dir / ss.RUN_FILE).write_text(json.dumps(meta), encoding="utf-8")
        older = ss.summary(run_dir)["rows"][0]
        check("163: a run made before 17 October, later, whose run.json keeps the full note alone, is said in the same "
              "plain words, and a note already in plain words stands as it is",
              older["said"] == "PubMed did not answer (HTTP 503)."
              and [ss.note_said("Scopus", "scopus", "HTTP 401 from 127.0.0.1:1/content/search/scopus: Invalid key [key]"),
                   ss.note_said("OpenAlex", "openalex", "No answer from 127.0.0.1:1: timed out"),
                   ss.note_said("PubMed", "pubmed", "KeyError: 'esearchresult'"),
                   ss.note_said("Europe PMC", "epmc", "127.0.0.1:1 answered with something that is not JSON."),
                   ss.note_said("Scopus", "scopus", "There is no ELSEVIER_API_KEY in the keychain.")]
              == ["Scopus refused the key (HTTP 401).", "OpenAlex did not answer.", "PubMed sent something Sift could not read.",
                  "Europe PMC sent something Sift could not read.", "There is no ELSEVIER_API_KEY in the keychain."],
              str(older)[:300])
    finally:
        ss.CLOCK = kept_clock
        os.environ.pop(ss.STUB_ENV, None)
        if kept_env is not None:
            os.environ[ss.STUB_ENV] = kept_env
        httpd.shutdown()
        httpd.server_close()

