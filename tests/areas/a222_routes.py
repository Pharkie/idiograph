"""Area 222: each app its own routes (the split's second build, 20 October 2026, Adam's plan accepted with
every lean). Every app answers the shared routes, each app its own, and another app's route answers 404
naming the app that has it. Idiograph answered Sift's and Trace's as before until the cutover (the family
codebase's sixth build, 23 October 2026), and refuses them by name since. A live review's calls, played on an
invented review, answer on Sift's own server and are refused on Idiograph's, which writes nothing."""
from __future__ import annotations

import base64
import http.client
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

from . import support
from .support import TOOL, check, skip
import idiograph_routes

# An invented review on rock-pool volunteers, its plan by export alone, so no run asks any database
PLAN = {"databases": ["psycinfo", "cinahl"],
        "blocks": [{"name": "Rock pools", "terms": "rockpool*\n\"tide pool\"", "scope": "tak"},
                   {"name": "Volunteers", "terms": ["volunteer*", "\"citizen science\""], "scope": "tak"}],
        "years": {"from": "2005", "to": 2026}, "types": ["article"],
        "reasons": [{"code": "E1", "meaning": "Not about rock pools"}, {"code": "E2", "meaning": "No volunteers"}]}
LISTED = [{"source": "psycinfo", "platform": "ebsco", "how": "export"},
          {"source": "cinahl", "platform": "ebsco", "how": "export"}]
PSYCINFO = ("TY  - JOUR\nTI  - Counting anemones at low tide\nAU  - Shore, A.\nPY  - 2018///\n"
            "JO  - Journal of Invented Shores\nAB  - Nine volunteers described the pools at dawn.\nKW  - rock pools\nER  - \n\n"
            "TY  - JOUR\nTI  - The patience of the tide pool\nAU  - Kelp, B.\nAU  - Wrack, C.\nPY  - 2021///\n"
            "JO  - Invented Coastal Studies\nAB  - Citizen scientists spoke of waiting for the water.\nER  - \n")
CINAHL = ("TY  - JOUR\nTI  - Volunteers on the rocks\nAU  - Limpet, D.\nPY  - 2015///\n"
          "JO  - Invented Nursing and the Sea\nAB  - Retired nurses joined a survey of the pools.\nER  - \n")
# What differs between two runs by nature, masked before the files are compared, and nothing else: a
# time to the second, the plan's `saved`, run.json's `started` and `finished` and each log line's `at`.
# No id differs, and no path is written into the review, so neither is masked.
MASKS = (("an ISO time", re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?")),)


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def asker(port: int):
    own = f"http://127.0.0.1:{port}"

    def ask(method: str, path: str, payload=None):
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=60)
        headers = {"Host": f"127.0.0.1:{port}", "Origin": own}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        conn.request(method, path, None if payload is None else json.dumps(payload), headers)
        res = conn.getresponse()
        raw = res.read()
        conn.close()
        try:
            return res.status, json.loads(raw or b"{}")
        except ValueError:
            return res.status, {"raw": raw[:80].decode("utf-8", "replace")}
    return ask


class Unanswered(Exception):
    """A server did not answer in up()'s window and was sent SIGABRT, so the calls that follow have nothing to ask."""


def up(ask, seconds: float = 30, watch: support.ChildWatch | None = None) -> dict | None:
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        try:
            code, said = ask("GET", "/api/server")
            if code == 200 and said.get("started"):
                if watch:
                    watch.answered()
                return said
        except OSError:
            pass
        time.sleep(0.2)
    if watch:
        watch.ran_out(f"up()'s {seconds:g} s ran out")
    return None


def masked(data: bytes) -> bytes:
    """A file's bytes with what differs by nature masked, each of MASKS."""
    text = data.decode("utf-8", "replace")
    for name, rx in MASKS:
        text = rx.sub(f"<{name}>", text)
    return text.encode("utf-8")


def tree(folder: Path) -> dict[str, bytes]:
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def test_routes(scratch):
    print("\n222. Each app its own routes, another's refused by name, Idiograph's Sift and Trace routes gone with the "
          "cutover, and a live review's calls on Sift's own server")
    import app_identity
    import server as server_mod
    import sift_routes
    import trace_routes

    # ── A. the table: every route placed once, the cutover one line
    placed = set(server_mod.ROUTE_APP)
    check("222: every route the server has has one owner in ROUTE_APP, the one table, the page's other paths with them",
          server_mod.unplaced_routes() == [] and set(server_mod.ROUTES) <= placed and server_mod.CLAIMED_TWICE == []
          and {"/audio", idiograph_routes.PRINT_PATH, idiograph_routes.GETS_PRINT_PATH, sift_routes.SIFT_PDF_PATH,
               trace_routes.TRACE_PDF_PATH, server_mod.MANUAL_PATH} <= placed
          and set(server_mod.ROUTE_APP.values()) == {"shared", *app_identity.APPS}
          and not hasattr(server_mod, "ROUTES_BY_APP") and "/api/sift" in server_mod.routes_of("sift"),
          str(server_mod.unplaced_routes()))
    check("222: app_identity's table of Sift's and Trace's routes, which a build without their modules names them by, "
          "is what their modules register",
          all(set(app_identity.ROUTES[a]) == set(server_mod.routes_of(a)) for a in ("sift", "trace")),
          str({a: sorted(set(server_mod.routes_of(a)) ^ set(app_identity.ROUTES[a])) for a in ("sift", "trace")}))
    kept_route_app = dict(server_mod.ROUTE_APP)
    try:
        for path in app_identity.ROUTES["sift"]:
            server_mod.ROUTE_APP.pop(path, None)
        named = server_mod.not_here("/api/sift", "idiograph")
    finally:
        server_mod.ROUTE_APP.clear()
        server_mod.ROUTE_APP.update(kept_route_app)
    check("222: with Sift's module unregistered, as in Idiograph's own build, Idiograph still refuses /api/sift naming Sift",
          bool(named) and named.get("app") == "sift" and "Sift's" in named.get("error", ""), str(named))
    check("222: since the cutover each app answers its own routes alone, Idiograph's no longer Sift's and Trace's",
          server_mod.SERVES_TOO == {"idiograph": (), "sift": (), "trace": ()}
          and server_mod.apps_served("idiograph") == ("idiograph",) and server_mod.apps_served("sift") == ("sift",))
    check("222: Sift's settings save General's keys and Sift's own, and leave Idiograph's as the file has them",
          server_mod.settings_for_app({"interviewer": "Wren", "databases": [], "ai_suggest": True, "minimap": "on"}, "sift")
          == {"databases": [], "ai_suggest": True}
          and server_mod.settings_for_app({"interviewer": "Wren", "databases": []}, "trace") == {}
          and server_mod.settings_for_app({"interviewer": "Wren", "databases": []}, "idiograph") == {"interviewer": "Wren"})

    # ── the suite's areas by app, --app sift running Sift's and the shared ones, the gate all of them
    import test_idiograph as runner
    tags = runner.AREAS
    sift_areas = runner.of_app("sift")
    check("222: each area tagged idiograph, sift, trace or shared, and --app sift running Sift's and the shared, in order",
          runner.areas_tagged(tags) == [] and set(tags.values()) == set(runner.AREA_APPS)
          and sift_areas == [n for n in tags if tags[n] in ("sift", "shared")] and "a104_sift_search" in sift_areas
          and "a222_routes" in sift_areas and "a039_themes" not in sift_areas and "a145_trace" not in sift_areas
          and "a145_trace" in runner.of_app("trace") and "a039_themes" in runner.of_app("idiograph"),
          f"{len(sift_areas)} of {len(tags)} areas for Sift")

    # ── B. three live servers, each its own folder, its own settings file and --root at an empty folder
    base = scratch / "routes-222"
    shutil.rmtree(base, ignore_errors=True)
    stub_hits: list[str] = []
    import http.server
    import threading

    class Stub(http.server.BaseHTTPRequestHandler):
        """Every request a run might send, answered empty on loopback and counted, none expected."""

        def log_message(self, *args):
            pass

        def do_GET(self):
            stub_hits.append(self.path)
            body = b'{"results": [], "meta": {"count": 0}}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        do_POST = do_GET

    stub = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=stub.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    env = {k: v for k, v in os.environ.items() if k != server_mod.STATE_CARRIED}
    env.update(PYTHONUNBUFFERED="1", IDIOGRAPH_STAY_OPEN="1",
               IDIOGRAPH_SEARCH_STUB=f"http://127.0.0.1:{stub.server_address[1]}")
    env = support.faulty_env(env)
    wt_files = [TOOL / n for n in ("state.json", "state.sift.json", "state.trace.json", "config.sift.json",
                                   "config.trace.json")]
    wt_before = {p.name: (p.read_bytes() if p.is_file() else None) for p in wt_files}
    kids, asks, places, watches, logs = {}, {}, {}, {}, {}
    try:
        for app in ("idiograph", "sift", "trace"):
            home = base / app
            (home / "root").mkdir(parents=True)
            cfg = home / app_identity.file_names(app)["config"]
            cfg.write_text(json.dumps({"corpus": "", "gravity_reference": "", "corpus_exclude": [], "projects": [],
                                       "databases": LISTED}), encoding="utf-8")
            port = free_port()
            # the output to a file beside the app's folder, which a failure below reads (cidiag, 7 November 2026)
            logs[app] = base / f"{app}-server.log"
            with open(logs[app], "wb") as log:
                kids[app] = subprocess.Popen([sys.executable, str(support.source("server.py")), "--app", app, "--port", str(port),
                                              "--no-browser", "--root", str(home / "root"), "--config", str(cfg)],
                                             stdout=log, stderr=subprocess.STDOUT, env=env, cwd=str(home))
            watches[app] = support.ChildWatch(kids[app], port)
            asks[app], places[app] = asker(port), {"home": home, "config": cfg}
        states = {app: up(ask, watch=watches[app]) for app, ask in asks.items()}
        answered = all(states.values()) and [s.get("app") for s in states.values()] == ["idiograph", "sift", "trace"]
        check("222: /api/server answers with the app on each of the three servers", answered,
              str([s and s.get("app") for s in states.values()]) if answered else "\n".join(
                  f"{app}: " + (f"answered, first {watches[app].first:.1f} s after the start" if states[app] else
                                watches[app].says(logs[app].read_text(encoding="utf-8", errors="replace")))
                  for app in states))
        if not all(states.values()):
            raise Unanswered

        # ── C. each app answers its own routes and the shared, and refuses another's by name
        said = {app: {path: ask("GET", path) for path in ("/api/whats-new", "/api/beat", "/api/cases",
                                                         "/api/sift", "/api/trace", "/sift/pdf", "/gets/print",
                                                         "/api/no-such")}
                for app, ask in asks.items()}
        posted = {app: ask("POST", "/api/trace-project", {"op": "read"}) for app, ask in asks.items()}
        refused = said["sift"]["/api/cases"]
        check("222: every app answers the shared routes", all(said[a]["/api/whats-new"][0] == 200
                                                             and said[a]["/api/beat"][0] == 200 for a in said),
              str({a: said[a]["/api/whats-new"][0] for a in said}))
        check("222: Sift refuses Idiograph's routes and Trace's with a 404 naming the app that has them, a GET and a POST",
              refused[0] == 404 and refused[1] == {"error": "That is Idiograph's, not Sift's.", "app": "idiograph", "port": 8765}
              and said["sift"]["/gets/print"][0] == 404 and said["sift"]["/gets/print"][1].get("app") == "idiograph"
              and said["sift"]["/api/trace"][1].get("app") == "trace" and posted["sift"][0] == 404
              and posted["sift"][1].get("app") == "trace", str(refused))
        check("222: Trace refuses Idiograph's and Sift's by name, its own PDF route not among them",
              said["trace"]["/api/cases"][1].get("app") == "idiograph" and said["trace"]["/api/sift"][1].get("app") == "sift"
              and said["trace"]["/sift/pdf"][1].get("app") == "sift" and posted["trace"][0] != 404,
              str({p: said["trace"][p][0] for p in said["trace"]}))
        check("222: Idiograph answers its own and refuses Sift's and Trace's by name since the cutover, a GET and a POST",
              said["idiograph"]["/api/cases"][0] == 200 and said["idiograph"]["/gets/print"][1].get("app") is None
              and said["idiograph"]["/api/sift"] == (404, {"error": "That is Sift's, not Idiograph's.", "app": "sift", "port": 8766})
              and said["idiograph"]["/sift/pdf"][1].get("app") == "sift"
              and said["idiograph"]["/api/trace"] == (404, {"error": "That is Trace's, not Idiograph's.", "app": "trace", "port": 8767})
              and posted["idiograph"][0] == 404 and posted["idiograph"][1].get("app") == "trace",
              str({p: said["idiograph"][p][0] for p in said["idiograph"]}))
        check("222: an unknown route is still No such endpoint on every app",
              all(said[a]["/api/no-such"] == (404, {"error": "No such endpoint.", "code": "no_endpoint"}) for a in said))
        searched = {app: ask("POST", "/api/search", {"q": "pool", "scope": "all"}) for app, ask in asks.items()}
        scoped = asks["sift"]("POST", "/api/search", {"q": "pool", "scope": "project", "root": "x"})
        check("222: Search on each app holds its own kinds, Everything on Sift Sift's alone, This project refused there by name",
              [p[0] for p in searched["sift"][1].get("parts", [])] == ["sift"]
              and set(searched["sift"][1].get("counts", {})) == {"record", "dnote", "field", "form", "excerpt", "term", "reason"}
              and [p[0] for p in searched["trace"][1].get("parts", [])] == ["trace"]
              and [p[0] for p in searched["idiograph"][1].get("parts", [])] == ["distil"]
              and scoped[0] == 404 and scoped[1].get("app") == "idiograph", str(scoped))

        # ── D. a live review's calls on an invented review, on Sift's own server, and on Idiograph's refused
        got = {}
        for app in ("idiograph", "sift"):
            ask, home, cfg = asks[app], places[app]["home"], places[app]["config"]
            review = home / "Rock pool review"
            review.mkdir()
            steps = {}
            steps["open"] = ask("POST", "/api/sift-review", {"op": "new", "folder": str(review), "name": "Rock pool review"})
            steps["save"] = ask("POST", "/api/sift-search", {"op": "save", "folder": str(review), "plan": PLAN})
            cli = lambda *words: subprocess.run([sys.executable, str(support.source("cli.py")), "--app", app, "sift", "search",
                                                 *words, "--config", str(cfg)], capture_output=True, encoding="utf-8",
                                                env=env, cwd=str(home), timeout=120)
            steps["strings"] = cli("strings", str(review))
            code, read = ask("POST", "/api/sift-search", {"op": "read", "folder": str(review)})
            today = read.get("today") or time.strftime("%Y-%m-%d")
            for source, name, words in (("psycinfo", "PsycInfo export.ris", PSYCINFO), ("cinahl", "CINAHL export.ris", CINAHL)):
                steps[f"drop {source}"] = ask("POST", "/api/sift-search", {
                    "op": "drop", "folder": str(review), "source": source, "name": name,
                    "data": base64.b64encode(words.encode()).decode()})
            steps["run"] = cli("run", str(review), "--draft", "--date", today, "--follows", "none")
            run_dir = str(review / "runs" / today)
            steps["read"] = ask("POST", "/api/sift", {"op": "read", "folder": run_dir})
            first = sorted(r.get("rec_id", "") for r in (steps["read"][1].get("records") or []))[:1]
            steps["decide"] = ask("POST", "/api/sift", {"op": "decide", "folder": run_dir, "rec_id": first[0] if first else "",
                                                        "stage": "ta", "decision": "exclude", "reason": "E1", "note": ""})
            steps["read again"] = ask("POST", "/api/sift", {"op": "read", "folder": run_dir})
            # a later run that day following the first by its folder's name, its exports not yet dropped
            steps["run follows"] = cli("run", str(review), "--draft", "--date", today, "--follows", today)
            got[app] = {"review": review, "steps": steps, "files": {k: masked(v) for k, v in tree(review).items()}}
        idio, sift_ = got["idiograph"], got["sift"]
        ok_steps = {app: {k: (v.returncode if hasattr(v, "returncode") else v[0]) for k, v in g["steps"].items()}
                    for app, g in got.items()}
        check("222: every call of a live review's answers on Sift's own server, the command line's too",
              set(ok_steps["sift"].values()) <= {0, 200},
              str(ok_steps["sift"]) + " " + " ".join(str(v.stderr)[:120] for v in sift_["steps"].values()
                                                      if hasattr(v, "stderr") and v.returncode))
        check("222: on Idiograph's server every call is refused naming Sift, the command line's too, and nothing is "
              "written in the review's folder",
              all(v[0] == 404 and v[1].get("app") == "sift" for v in idio["steps"].values() if not hasattr(v, "returncode"))
              and all(v.returncode == 1 and v.stderr.startswith("sift is Sift's, not Idiograph's. Run it as: sift search ")
                      for v in idio["steps"].values() if hasattr(v, "returncode"))
              and idio["files"] == {}, str(ok_steps["idiograph"]) + " " + str(sorted(idio["files"])[:6]))
        names = set(sift_["files"])
        wanted = {"screening.csv", "screening.log.jsonl", "reasons.csv", "log.csv", "run.json"}
        held = {Path(n).name for n in names}
        check("222: the review holds the files a live review's runs write, its plan, two runs, runs/numbers.json and "
              "screening.lock",
              wanted <= held and "runs/numbers.json" in names and "search_plan.json" in names
              and f"runs/{today}/screening.lock" in names and f"runs/{today}-2/run.json" in names,
              f"missing {sorted(wanted - held)}, {sorted(names)[:30]}")
        out_s = sift_["steps"]["strings"].stdout
        check("222: sift search strings answers through cli.py as Sift", out_s.startswith("The strings of version 1"), out_s[:120])
        check("222: no request left the machine, and none reached the stub", stub_hits == [], str(stub_hits[:3]))
    except Unanswered:
        skip("222: each app's routes, the refusals and a live review's calls", "a server did not answer, as the check above says")
    finally:
        for kid in kids.values():
            if kid.poll() is None:
                kid.kill()
            kid.wait(10)
        stub.shutdown()
        stub.server_close()
    wt_after = {p.name: (p.read_bytes() if p.is_file() else None) for p in wt_files}
    check("222: no file of the code's own folder written, state.json and the Sift and Trace files beside it among them",
          wt_after == wt_before, str([n for n in wt_after if wt_after[n] != wt_before[n]]))
