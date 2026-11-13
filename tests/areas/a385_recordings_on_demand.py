"""Area 385: the demo's recordings downloaded the first time one is played (recdemand, 13 November 2026).

Adam, 13 November, by dialog: "Text in, recordings on demand". The installers carry the demo's text and no recording.
The player offers the download with its size, fetches the recordings from a GitHub release of their own, checks each
against the manifest the app ships and keeps them where the app keeps its demo.

What is checked, on the demo's own committed files and a copy of its text standing in for the installed app's, with
a stand-in server on this machine's loopback in place of GitHub, never the network. A: the manifest names each
participant's recording for the transcript as it stands with the size and sha256 of the committed file, and the
licence's, at the release's address. B: a build stages the text and the manifest and no recording nor the licence,
on the Mac's and Windows's lists alike, and a stage holding one stops the build. C: with none on this computer the
player is offered the download with the size of what is to come, Download fetches the licence and the three
recordings, checks each and puts it where the player finds it, the licence beside each and nothing half written
left, and the player then plays it and asks for nothing again, Reset demo leaving them. D: the 48 kbps encoding of
the same transcript plays as it is, and a recording of another size is not played and is offered again. E: a file
that does not match its sha256 is refused and never kept, offline says so in its own line, and Cancel stops it with
nothing left. F: only the app's window downloads, and no command line or MCP op reaches it. G (rechttps): the
download takes HTTPS to GitHub's own hosts alone, the first address and every redirect, a stand-in redirecting to
http, another host, a look-alike or another port refused with nothing kept, and the stand-in let through only when
the smoke run hands it, never in the installed app."""
from __future__ import annotations

import hashlib
import http.server
import inspect
import json
import os
import shutil
import socket
import threading
import time
from pathlib import Path

import audio as audio_mod

from . import support
from .support import check


def ck(name: str, condition, detail="") -> None:
    """A check whose detail is said only when it fails."""
    check(name, bool(condition), "" if condition else str(detail)[:600])


class Stand(http.server.BaseHTTPRequestHandler):
    """GitHub's release downloads stood in for on loopback: each path a file's bytes, every request kept, and slow
    sends a block at a time so Cancel has a download to stop."""
    files: dict = {}
    asked: list = []
    slow = False

    def do_GET(self):
        Stand.asked.append(self.path)
        data = Stand.files.get(self.path)
        if data is None:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        step = 64 * 1024
        try:
            for at in range(0, len(data), step):
                self.wfile.write(data[at:at + step])
                if Stand.slow:
                    self.wfile.flush()
                    time.sleep(0.05)
        except OSError:
            return

    def log_message(self, *args):
        pass


def closed_port() -> int:
    """A loopback port nothing listens on."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_recordings_on_demand(scratch: Path):
    print("\n385. The demo's recordings downloaded the first time one is played (recdemand)")
    import demo_recordings as demo_rec
    import make_demo
    import server as server_mod
    import idiograph_routes as routes

    folder = support.source("packaging/recording")
    manifest = json.loads(support.source("demo/recordings.json").read_text(encoding="utf-8"))

    # ── A. the manifest follows the committed files
    rows = {r["file"]: r for r in manifest["recordings"]}
    named = {n: make_demo.committed(n) for n in make_demo.CASES}
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    licence = folder / make_demo.AUDIO_LICENCE
    ck("385: the manifest names each participant's recording for the transcript as it stands, with the size and "
       "sha256 of the committed file, and the licence's, at the demo-recordings-1 release's address",
       # the IPA demo's three, the longitudinal demo's nine beside them (lipabuild, area 394)
       sorted(set(rows) - set(__import__("make_demo_lipa").recording_names())) == sorted(p.name for p in named.values())
       and all(rows[p.name]["size"] == p.stat().st_size and rows[p.name]["sha256"] == sha(p) for p in named.values())
       and manifest["licence"] == {"file": "LICENSE-audio.md", "size": licence.stat().st_size, "sha256": sha(licence)}
       and manifest["url"] == "https://github.com/Pharkie/idiograph/releases/download/demo-recordings-1/"
       and manifest["release"] == demo_rec.RELEASE, json.dumps(manifest)[:500])

    # ── B. no build stages a recording
    import importlib.util
    spec = importlib.util.spec_from_file_location("idiograph_build_mac_385", support.source("packaging/build_mac.py"))
    build_mac = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build_mac)
    audio_like = lambda name: Path(name).suffix.lower() in audio_mod.CONTENT_TYPES or Path(name).name == "LICENSE-audio.md"
    listed = [d for d, _ in build_mac.listing("idiograph")] + [d for d, _ in build_mac.listing("idiograph", windows=True)]
    stage = scratch / "rec-385" / "stage"
    shutil.rmtree(stage.parent, ignore_errors=True)
    demo = build_mac.stage_cases(stage)
    line = build_mac.demo_line(demo)
    stray = demo / "Juno" / "Source" / "Initial" / "Source" / "Juno-Initial.m4a"
    stray.parent.mkdir(parents=True)
    stray.write_bytes(b"a recording that must not ship")
    try:
        build_mac.demo_line(demo)
        stopped = False
    except SystemExit:
        stopped = True
    ck("385: a build stages the demo's text and its manifest and no recording nor their licence, on the Mac's and "
       "Windows's lists alike, and a stage holding one stops the build",
       not [d for d in listed if audio_like(d)] and "demo/recordings.json" in listed
       and (demo / "recordings.json").read_bytes() == support.source("demo/recordings.json").read_bytes()
       and "to download" in line and stopped, [d for d in listed if audio_like(d)] or line)

    # ── C. the installed app: none on this computer, offered, downloaded, checked, played
    base = scratch / "rec-385"
    shipped, work, root = base / "shipped", base / "work", base / "root"
    leave = shutil.ignore_patterns("*.m4a", "Working", "_Archive", "ta", "idiograph-gets.json")
    shutil.copytree(support.source("demo"), shipped, ignore=leave)
    shutil.copytree(support.source("demo/pristine/Working"), shipped / "pristine" / "Working")
    shutil.copytree(shipped, work)
    root.mkdir()
    release = "/github/Pharkie/idiograph/releases/download/demo-recordings-1/"
    Stand.files = {release + p.name: p.read_bytes() for p in list(named.values()) + [licence]}
    Stand.asked, Stand.slow = [], False
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Stand)
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    stub = f"http://127.0.0.1:{httpd.server_address[1]}"
    kept = (server_mod.DEMO_DIR, server_mod.DEMO_CASE, server_mod.DEMO_WORKBOOK, server_mod.SHIPPED_DEMO,
            server_mod.DEMO_PROJECT, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    kept_env = os.environ.get("IDIOGRAPH_SEARCH_STUB")
    kept_fetches = dict(demo_rec.FETCHES)

    def wait():
        running = demo_rec.current(routes.DEMO_RECORDINGS)
        if running is not None:
            running.thread.join(timeout=60)
        return routes.api_demo_recordings({})

    def hidden():
        """Any file a download left half written beside its place."""
        return sorted(p.name for p in work.rglob(".*") if p.is_file() and p.name.endswith(".downloading"))

    try:
        server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO = work, shipped
        server_mod.DEMO_CASE = work / "Juno"
        server_mod.DEMO_WORKBOOK = server_mod.DEMO_CASE / "Juno - EN & ES.xlsx"
        server_mod.DEMO_PROJECT = work / "idiograph-project.json"
        server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = str(root), {"recent": []}
        os.environ["IDIOGRAPH_SEARCH_STUB"] = stub
        demo_rec.FETCHES.clear()
        books = {n: work / n / f"{n} - EN & ES.xlsx" for n in make_demo.CASES}
        places = {n: make_demo.recording(n, work) for n in make_demo.CASES}
        offered = routes.api_audio({"path": str(books["Juno"]), "sheet": "Initial"})
        whole = sum(p.stat().st_size for p in named.values()) + licence.stat().st_size
        ck("385: with none on this computer the player is offered the download, the size of the three recordings "
           "and their licence, and nothing has been fetched",
           offered["found"] is False and offered["download"]["bytes"] == whole
           and offered["download"]["size"].endswith(" MB") and offered["download"]["state"] == "idle"
           and not Stand.asked, json.dumps(offered))

        started = routes.api_demo_recordings({"op": "download"})
        done = wait()
        played = {n: routes.api_audio({"path": str(b), "sheet": "Initial"}) for n, b in books.items()}
        ck("385: Download fetches the licence and the three recordings from the release, checks each and puts it "
           "where the player finds it, the licence beside each and nothing half written left, and the player plays it",
           started["state"] == "downloading" and done["state"] == "done"
           and all(places[n].read_bytes() == named[n].read_bytes() for n in make_demo.CASES)
           and all((places[n].parent / "LICENSE-audio.md").read_bytes() == licence.read_bytes() for n in make_demo.CASES)
           and all(played[n]["found"] and played[n]["name"] == f"{n}-Initial.m4a"
                   and audio_mod.for_sheet(books[n], "Initial") == places[n] for n in make_demo.CASES)
           and sorted(Stand.asked) == sorted(Stand.files) and not hidden(), f"{done} {Stand.asked} {hidden()}")

        Stand.asked = []
        again = routes.api_audio({"path": str(books["Mabel"]), "sheet": "Initial"})
        routes.api_reset_demo({})
        ck("385: once they are here the player asks for nothing again, and Reset demo leaves them in place",
           again["found"] and not Stand.asked and routes.api_demo_recordings({"op": "download"})["state"] == "done"
           and all(places[n].read_bytes() == named[n].read_bytes() for n in make_demo.CASES), str(Stand.asked))

        # ── D. an earlier encoding of the same transcript plays, a recording of another size does not
        entry = rows[named["Mabel"].name]
        places["Mabel"].write_bytes(b"\0" * entry["earlier"][0])
        earlier = routes.api_audio({"path": str(books["Mabel"]), "sheet": "Initial"})
        places["Rowan"].write_bytes(b"an older recording of his, in the say voices")
        other = routes.api_audio({"path": str(books["Rowan"]), "sheet": "Initial"})
        ck("385: the 48 kbps encoding of the same transcript plays as it is, and a recording of another size, an "
           "earlier version's, is not played and its download is offered, his alone",
           earlier["found"] is True and other["found"] is False
           and other["download"]["bytes"] == rows[named["Rowan"].name]["size"] + licence.stat().st_size,
           f"{earlier} {other}")
        shutil.copyfile(named["Mabel"], places["Mabel"])

        # ── E. a file that does not match is refused, offline is said, Cancel leaves nothing
        Stand.asked = []
        good = Stand.files[release + named["Rowan"].name]
        Stand.files[release + named["Rowan"].name] = good[:-1] + bytes([good[-1] ^ 1])
        refused = (routes.api_demo_recordings({"op": "download"}), wait())[1]
        ck("385: a recording that comes down other than its sha256 is refused and never kept, the line saying so "
           "and the demo going on without sound",
           refused["state"] == "failed" and refused["line"] == routes.i18n.t("server.demo_recordings.checksum")
           and places["Rowan"].read_bytes() == b"an older recording of his, in the say voices" and not hidden()
           and routes.api_audio({"path": str(books["Rowan"]), "sheet": "Initial"})["found"] is False,
           f"{refused} {hidden()}")
        Stand.files[release + named["Rowan"].name] = good
        places["Rowan"].unlink()

        os.environ["IDIOGRAPH_SEARCH_STUB"] = f"http://127.0.0.1:{closed_port()}"
        offline = (routes.api_demo_recordings({"op": "download"}), wait())[1]
        ck("385: with no connection the download says so in its own line, nothing is kept and Download is offered "
           "again",
           offline["state"] == "failed" and offline["line"] == routes.i18n.t("server.demo_recordings.offline")
           and not places["Rowan"].exists() and not hidden()
           and routes.api_audio({"path": str(books["Rowan"]), "sheet": "Initial"})["download"]["state"] == "failed",
           json.dumps(offline))

        os.environ["IDIOGRAPH_SEARCH_STUB"] = stub
        for name in ("Juno", "Mabel"):
            places[name].unlink()
        Stand.slow = True
        routes.api_demo_recordings({"op": "download"})
        moving = time.time() + 20
        while time.time() < moving and routes.api_demo_recordings({})["got"] < 200 * 1024:
            time.sleep(0.05)
        stopped = routes.api_demo_recordings({"op": "cancel"})
        Stand.slow = False
        ck("385: Cancel stops the download part way, nothing half written is left and no recording it had not "
           "finished is in place",
           stopped["state"] == "cancelled" and not hidden()
           and not any(places[n].exists() for n in ("Juno", "Rowan")), f"{stopped} {hidden()}")
    finally:
        httpd.shutdown()
        httpd.server_close()
        (server_mod.DEMO_DIR, server_mod.DEMO_CASE, server_mod.DEMO_WORKBOOK, server_mod.SHIPPED_DEMO,
         server_mod.DEMO_PROJECT, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY) = kept
        if kept_env is None:
            os.environ.pop("IDIOGRAPH_SEARCH_STUB", None)
        else:
            os.environ["IDIOGRAPH_SEARCH_STUB"] = kept_env
        demo_rec.FETCHES.clear()
        demo_rec.FETCHES.update(kept_fetches)

    # ── G. HTTPS to GitHub's own hosts alone, first address and every redirect (rechttps, 13 November 2026)
    import sys
    import urllib.request
    good_urls = ["https://github.com/Pharkie/idiograph/releases/download/demo-recordings-1/x.m4a",
                 "https://release-assets.githubusercontent.com/github-production-release-asset/1/2?sig=a",
                 "https://objects.githubusercontent.com/github-production-release-asset-2e65be/3",
                 "https://GitHub.com:443/Pharkie/idiograph/releases/download/demo-recordings-1/x.m4a"]
    bad_urls = ["http://github.com/Pharkie/idiograph/releases/download/demo-recordings-1/x.m4a",
                "https://github.com:8443/x", "https://user@github.com/x", "https://github.com@evil.example/x",
                "https://github.com.evil.example/x", "https://evilgithub.com/x", "https://notgithub.com/x",
                "https://objects.githubusercontent.com.evil.example/x", "https://evil.example/x",
                "ftp://github.com/x", "file:///etc/passwd", "https://127.0.0.1/x", "http://127.0.0.1:9/x", "",
                "https://github.com:99999/x"]
    req = urllib.request.Request("https://github.com/Pharkie/idiograph/releases/download/demo-recordings-1/x.m4a")
    onward = demo_rec.Guard().redirect_request(req, None, 302, "Found", {}, good_urls[1])
    ck("385: the download takes HTTPS to github.com and GitHub's two download hosts on 443, a redirect to one of "
       "them followed, and refuses http, another host, a look-alike, a user in the address, another port and loopback",
       all(demo_rec.allowed(u) for u in good_urls) and not any(demo_rec.allowed(u) for u in bad_urls)
       and onward is not None and onward.full_url == good_urls[1],
       [u for u in good_urls if not demo_rec.allowed(u)] + [u for u in bad_urls if demo_rec.allowed(u)])

    class Bounce(http.server.BaseHTTPRequestHandler):
        """A stand-in whose every path redirects where `to` says, the paths kept; `/file` the bytes themselves."""
        to: dict = {}
        asked: list = []

        def do_GET(self):
            Bounce.asked.append(self.path)
            if self.path == "/file":
                self.send_response(200)
                self.send_header("Content-Length", "5")
                self.end_headers()
                self.wfile.write(b"bytes")
                return
            self.send_response(302)
            self.send_header("Location", Bounce.to.get(self.path, "/file"))
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *args):
            pass

    bounce = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Bounce)
    other = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Bounce)
    for srv in (bounce, other):
        threading.Thread(target=srv.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    here = f"http://127.0.0.1:{bounce.server_address[1]}"
    there = f"http://127.0.0.1:{other.server_address[1]}"
    Bounce.to = {"/to-http": "http://github.com/x", "/to-host": "https://evil.example/x",
                 "/to-lookalike": "https://release-assets.githubusercontent.com.evil.example/x",
                 "/to-user": "https://github.com@evil.example/x", "/to-port": f"{there}/file", "/ok": "/file"}
    sha5 = hashlib.sha256(b"bytes").hexdigest()
    land = scratch / "rec-385" / "guard"
    shutil.rmtree(land, ignore_errors=True)

    def fetched(path, stub, place=""):
        target = land / (place or path.strip("/")) / "file.m4a"
        run = demo_rec.Fetch([{"url": f"{here}{path}", "size": 5, "sha256": sha5, "targets": [target]}], stub)
        run.run()
        left = sorted(p.name for p in target.parent.iterdir()) if target.parent.exists() else []
        return run.view(), target, left

    kept_frozen = getattr(sys, "frozen", None)
    try:
        refused = {p: fetched(p, here) for p in ("/to-http", "/to-host", "/to-lookalike", "/to-user", "/to-port")}
        other_asked = [a for a in Bounce.asked if a == "/file"]
        Bounce.asked = []
        through = fetched("/ok", here)
        Bounce.asked = []
        no_stub = fetched("/ok", "", "no-stub")
        unasked = not Bounce.asked
        sys.frozen = True
        frozen = fetched("/ok", here, "frozen")
        frozen_unasked = not Bounce.asked
    finally:
        if kept_frozen is None:
            del sys.frozen
        else:
            sys.frozen = kept_frozen
        for srv in (bounce, other):
            srv.shutdown()
            srv.server_close()
    ck("385: a stand-in whose redirect goes to http, to another host, to a look-alike of GitHub's, through a user in "
       "the address or to another port on this machine is refused, the download failed with nothing kept and "
       "nothing asked of where it pointed",
       all(v["state"] == "failed" and v["why"] == "failed" and not t.exists() and not left
           for v, t, left in refused.values()) and not other_asked,
       {p: (v, left) for p, (v, t, left) in refused.items()})
    ck("385: the stand-in handed by the smoke run still downloads through its own redirect, and with none handed, "
       "or in the installed app, a loopback address is refused before anything is asked of it",
       through[0]["state"] == "done" and through[1].read_bytes() == b"bytes" and through[2] == ["file.m4a"]
       and no_stub[0]["state"] == "failed" and not no_stub[1].exists() and not no_stub[2] and unasked
       and frozen[0]["state"] == "failed" and not frozen[1].exists() and not frozen[2] and frozen_unasked,
       f"{through} {no_stub} {frozen}")

    # ── F. only the window downloads, and no agent op reaches it
    import idiograph_cli
    import idiograph_mcp
    agents = inspect.getsource(idiograph_cli) + inspect.getsource(idiograph_mcp)
    ck("385: only the app's own window downloads the demo's recordings, how far it has got read by anyone, and no "
       "command line or MCP op reaches it",
       server_mod.window_only("/api/demo-recordings", {"op": "download"})
       and server_mod.window_only("/api/demo-recordings", {"op": "cancel"})
       and not server_mod.window_only("/api/demo-recordings", {})
       and "demo-recordings" not in agents and "demo_recordings" not in agents)
