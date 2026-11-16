"""Area 409: the thematic analysis demo plays the IPA demo's recordings (tademoaudio, 16 November 2026).

Adam, 16 November 2026, in his installed 0.9.28: the thematic analysis demo's Coding screen had neither the
download nor the player, "No recording found for Initial", where the IPA demo had both. The thematic analysis demo
codes the same three interviews from the same transcripts, so it plays the IPA demo's recordings, one download for
both, kept in the IPA demo.

What is checked, on a scratch copy of the demos standing as the installed app's, nothing on this computer yet and
GitHub's release stood in for on loopback: A, a thematic analysis demo participant's player is offered the same
download as the IPA demo's, by the same key and size, and nothing is fetched; B, that download, started from the
thematic analysis demo's offer, fetches each file once and puts it in the IPA demo alone, and then each of the three
thematic analysis demo participants' players finds its own interview's recording, the IPA demo's same file, and
/audio streams its bytes; C, an offset set from the thematic analysis demo's player is the recording's, read the same
from both demos."""
from __future__ import annotations

import http.server
import io
import json
import os
import shutil
import threading
from pathlib import Path

from . import support
from .support import check


def ck(name: str, condition, detail="") -> None:
    check(name, bool(condition), "" if condition else str(detail)[:600])


class Stand(http.server.BaseHTTPRequestHandler):
    """GitHub's release downloads stood in for on loopback, each path a file's bytes."""
    files: dict = {}
    asked: list = []

    def do_GET(self):
        Stand.asked.append(self.path)
        data = Stand.files.get(self.path)
        self.send_response(200 if data is not None else 404)
        self.send_header("Content-Length", str(len(data or b"")))
        self.end_headers()
        if data:
            self.wfile.write(data)

    def log_message(self, *args):
        pass


class Handler:
    """Enough of a request handler for /audio: the headers it reads and what it sends."""

    def __init__(self):
        self.headers = {}
        self.code = None
        self.wfile = io.BytesIO()

    def send_response(self, code):
        self.code = code

    def send_header(self, *args):
        pass

    def end_headers(self):
        pass

    def _send(self, code, body, kind):
        self.code = code
        self.wfile.write(body)


def test_ta_demo_recordings(scratch: Path):
    print("\n409. The thematic analysis demo plays the IPA demo's recordings (tademoaudio)")
    import demo_recordings as demo_rec
    import make_demo
    import server as server_mod
    import idiograph_routes as routes

    folder = support.source("packaging/recording")
    named = {n: make_demo.committed(n) for n in make_demo.CASES}
    licence = folder / make_demo.AUDIO_LICENCE
    if not all(p.is_file() for p in named.values()) or not licence.is_file():
        support.skip("409: the thematic analysis demo plays the IPA demo's recordings",
                     "this checkout does not hold the IPA demo's committed recordings")
        return

    base = scratch / "ta-rec-409"
    shutil.rmtree(base, ignore_errors=True)
    shipped, work, proj = base / "shipped", base / "work", base / "root"
    shutil.copytree(support.source("demo"), shipped,
                    ignore=shutil.ignore_patterns("*.m4a", "LICENSE-audio.md", "Working", "Source", "_Archive",
                                                  "lipa", "idiograph-gets.json", "idiograph-codes.json"))
    shutil.copytree(support.source("demo/pristine/Working"), shipped / "pristine" / "Working")
    shutil.copytree(support.source("demo/ta/pristine/Working"), shipped / "ta" / "pristine" / "Working")
    shutil.copytree(shipped, work)
    proj.mkdir()
    release = "/github/Pharkie/idiograph/releases/download/demo-recordings-1/"
    Stand.files = {release + p.name: p.read_bytes() for p in list(named.values()) + [licence]}
    Stand.asked = []
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Stand)
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    kept = (server_mod.DEMO_DIR, server_mod.DEMO_CASE, server_mod.DEMO_WORKBOOK, server_mod.SHIPPED_DEMO,
            server_mod.DEMO_PROJECT, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    kept_env = os.environ.get("IDIOGRAPH_SEARCH_STUB")
    kept_fetches = dict(demo_rec.FETCHES)
    try:
        server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO = work, shipped
        server_mod.DEMO_CASE = work / "Juno"
        server_mod.DEMO_WORKBOOK = server_mod.DEMO_CASE / "Juno - EN & ES.xlsx"
        server_mod.DEMO_PROJECT = work / "idiograph-project.json"
        server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = str(proj), {"recent": []}
        os.environ["IDIOGRAPH_SEARCH_STUB"] = f"http://127.0.0.1:{httpd.server_address[1]}"
        demo_rec.FETCHES.clear()
        routes.fill_demo()
        ipa_books = dict(zip(routes.DEMO_CASES, routes.demo_workbooks()))
        ta_books = dict(zip(routes.DEMO_CASES, routes.demo_workbooks(server_mod.demo_ta_dir())))
        places = {n: make_demo.recording(n, work) for n in make_demo.CASES}

        # ── A. offered as the IPA demo's is
        ta_offer = routes.api_audio({"path": str(ta_books["Rowan"]), "sheet": "Initial"})
        ipa_offer = routes.api_audio({"path": str(ipa_books["Rowan"]), "sheet": "Initial"})
        whole = sum(p.stat().st_size for p in named.values()) + licence.stat().st_size
        ck("409: with none on this computer a thematic analysis demo participant's player is offered the IPA demo's "
           "download, the same key and size, and nothing is fetched",
           all(ta_books[n].is_file() for n in ta_books)
           and ta_offer["found"] is False and "download" in ta_offer
           and ta_offer["download"] == ipa_offer["download"] and ta_offer["download"]["demo"] == "ipa"
           and ta_offer["download"]["bytes"] == whole and not Stand.asked,
           json.dumps([ta_offer, ipa_offer]))

        # ── B. one download, kept in the IPA demo, plays in both
        routes.api_demo_recordings({"op": "download", "demo": ta_offer["download"]["demo"]})
        running = demo_rec.current(routes.DEMO_RECORDINGS)
        if running is not None:
            running.thread.join(timeout=60)
        done = routes.api_demo_recordings({"demo": "ipa"})
        played = {n: routes.api_audio({"path": str(b), "sheet": "Initial"}) for n, b in ta_books.items()}
        heard = {}
        for n, b in ta_books.items():
            handler = Handler()
            routes.stream_audio(handler, {"path": str(b), "sheet": "Initial"})
            heard[n] = (handler.code, handler.wfile.getvalue())
        in_ta = sorted(str(p.relative_to(work)) for p in (work / "ta").rglob("*")
                       if p.suffix == ".m4a" or p.name == "LICENSE-audio.md")
        ck("409: that download fetches each file once and keeps them in the IPA demo alone, and each thematic analysis "
           "demo participant then plays their own interview's recording, the IPA demo's file, streamed whole",
           done["state"] == "done" and sorted(Stand.asked) == sorted(Stand.files) and not in_ta
           and all(places[n].read_bytes() == named[n].read_bytes() for n in make_demo.CASES)
           and all(played[n]["found"] and played[n]["name"] == f"{n}-Initial.m4a" for n in make_demo.CASES)
           and all(heard[n] == (200, named[n].read_bytes()) for n in make_demo.CASES)
           and routes.api_audio({"path": str(ipa_books["Juno"]), "sheet": "Initial"})["found"],
           f"{done} {Stand.asked} {in_ta} {[(n, played[n]) for n in played]} {[(n, heard[n][0]) for n in heard]}")

        Stand.asked = []
        again = routes.api_audio({"path": str(ta_books["Mabel"]), "sheet": "Initial"})
        ck("409: once they are here neither demo asks for them again",
           again["found"] and not Stand.asked
           and routes.api_demo_recordings({"op": "download"})["state"] == "done", str(Stand.asked))

        # ── C. an offset is the recording's, whichever demo sets it
        dry = routes.set_audio_offset(ta_books["Juno"], "Initial", 1.5, dry_run=True)
        unset = routes.api_audio({"path": str(ipa_books["Juno"]), "sheet": "Initial"})["offset"]
        routes.set_audio_offset(ta_books["Juno"], "Initial", 1.5)
        ck("409: an offset set from the thematic analysis demo's player is the recording's, read the same from both "
           "demos, and its dry run writes nothing",
           dry["recording"] == "Juno-Initial.m4a" and unset == 0.0
           and routes.api_audio({"path": str(ipa_books["Juno"]), "sheet": "Initial"})["offset"] == 1.5
           and routes.api_audio({"path": str(ta_books["Juno"]), "sheet": "Initial"})["offset"] == 1.5
           and not (work / "ta" / "Juno" / "Source").exists(), json.dumps(dry))

        # ── D. the command line and MCP answer the offset of a thematic analysis demo participant, whose offset file
        # is the IPA demo's, outside its own root, with that file given from the demos' top folder (tademofix)
        import cli
        import mcp_server
        argv = ["--config", str(base / "cli-config.json"), "--demo", "ta"]

        def held() -> dict:
            return {str(q.relative_to(work)): q.read_bytes() for q in sorted(work.rglob("*")) if q.is_file()}

        asked = ["offset", "Juno", "Initial", "2"]
        before = held()
        code, out, err = cli.run(argv + ["--json"] + asked + ["--dry-run"])
        dry_said = support.plain(json.loads(out)) if out.strip().startswith("{") else {}
        ck("409: the command line's offset dry run for a thematic analysis demo participant answers, writes nothing "
           "and names the offset file from the demos' top folder",
           code == 0 and dry_said.get("dry_run") is True and dry_said.get("offset") == 2.0
           and dry_said.get("file", "").startswith("ta/") is False and "Juno" in dry_said.get("file", "")
           and not dry_said.get("file", "/").startswith("..") and not os.path.isabs(dry_said.get("file", ""))
           and held() == before, f"{code} {out} {err}")
        code, out, err = cli.run(argv + ["--json"] + asked)
        real_said = support.plain(json.loads(out)) if out.strip().startswith("{") else {}
        ck("409: the real run answers with no crash, the same file, and the offset reads back from both demos",
           code == 0 and real_said.get("offset") == 2.0 and real_said.get("file") == dry_said.get("file")
           and (work / real_said["file"]).is_file()
           and routes.api_audio({"path": str(ipa_books["Juno"]), "sheet": "Initial"})["offset"] == 2.0
           and routes.api_audio({"path": str(ta_books["Juno"]), "sheet": "Initial"})["offset"] == 2.0,
           f"{code} {out} {err}")
        mcp = mcp_server.Server(None, demo="ta", config=str(base / "cli-config.json"))

        def tool(**given):
            return mcp.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                           "params": {"name": "audio_offset", "arguments": given}}))["result"]
        again = tool(case="Juno", sheet="Initial", seconds=3, request="Set the offset", dry_run=True)
        offered = support.plain(again.get("structuredContent") or {})
        ck("409: MCP's audio_offset for the same participant answers the same file, its dry run writing nothing, and "
           "then the real call writes the offset",
           not again.get("isError") and offered.get("file") == real_said.get("file") and offered.get("offset") == 3.0
           and routes.api_audio({"path": str(ta_books["Juno"]), "sheet": "Initial"})["offset"] == 2.0
           and not tool(case="Juno", sheet="Initial", seconds=3, request="Set the offset").get("isError")
           and routes.api_audio({"path": str(ta_books["Juno"]), "sheet": "Initial"})["offset"] == 3.0,
           json.dumps(again)[:500])
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
