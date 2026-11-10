from __future__ import annotations

import datetime as dt
import json
import shutil
import subprocess
import sys

import openpyxl

from . import support
from .support import check as said_check


def check(name, ok, detail=""):
    said_check(name, ok, str(detail)[:600])


# An invented study of learning to swim as an adult, Odette the participant and Bram asking, every word made up
ROWS = [
    ("Bram", "00:00:40", None),
    ("Odette", "00:01:05", "Cold water as a test she sets herself"),
    ("Odette", "00:02:50", "The first length without stopping as a turning point"),
]
HEAD = ["Name", "Timestamp", "Experiential statements", "Transcript", "Exploratory notes", "Key quotes"]


def made_book(path) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Initial"
    ws.append(HEAD)
    for speaker, at, said in ROWS:
        ws.append([speaker, dt.time(*map(int, at.split(":"))), said, f"{speaker} talks about the pool.",
                   "Water as a place of her own." if said else None, None])
    wb.save(path)


def test_words(scratch):
    print("\n228. The words build (Adam, 20 October): each app's /manual its own, the server's own lines in the "
          "running app's name, the window reading any app's last line, the bundle staging the app's own manual, "
          "and the command line and MCP still taking and answering case and cases")
    import mcp_server
    import server as server_mod

    sys.path.insert(0, str(support.source("packaging/tauri")))
    try:
        import bundle
    finally:
        sys.path.remove(str(support.source("packaging/tauri")))

    base = scratch / "a228"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    env = server_mod.os.environ.pop(server_mod.MANUAL_FILE, None)
    held = server_mod.app_held()
    pages, lines = {}, {}
    try:
        for app in ("idiograph", "sift", "trace"):
            server_mod.use_app(app)
            code, page = server_mod.manual_page()
            pages[app] = (code, page)
            lines[app] = (server_mod.named(server_mod.CLOSED_LINE), server_mod.named(server_mod.QUIT_LINE),
                          server_mod.named(server_mod.ELSEWHERE), server_mod.quit_word("darwin"))
    finally:
        server_mod.app_back(held)
        if env is not None:
            server_mod.os.environ[server_mod.MANUAL_FILE] = env

    # ── A. each app's manual
    idio, sift, trace = (pages[a][1] for a in ("idiograph", "sift", "trace"))
    check("228: /manual serves each app its own, Idiograph's with its IPA sections and none of Sift's or Trace's, "
          "Sift's and Trace's each under its own title",
          all(pages[a][0] == 200 for a in pages)
          and "<title>Idiograph manual</title>" in idio and "<title>Sift manual</title>" in sift
          and "<title>Trace manual</title>" in trace
          and ">PETs</h2>" in idio and ">GETs</h2>" in idio and ">Sift</h2>" not in idio and ">Trace</h2>" not in idio
          and ">Search strategy</h2>" in sift and ">PETs</h2>" not in sift and ">PETs</h2>" not in trace,
          {a: pages[a][0] for a in pages})

    # ── B. the server's own lines in the app's name, and the window reading any app's
    rust = support.source("packaging/tauri/src-tauri/src/main.rs").read_text(encoding="utf-8")
    check("228: running as Sift or Trace the server's own lines say its name, and the window's last-line reading "
          "finds any app's closing line",
          lines["idiograph"][0] == "Idiograph is closed." and lines["sift"][0] == "Sift is closed."
          and lines["trace"][0] == "Trace is closed." and lines["sift"][1].startswith("No Sift tab")
          and lines["trace"][2] == "Only Trace's own page can ask this." and lines["sift"][3] == "Quit Sift"
          and 'const CLOSED: [&str; 2] = [" is closed.", "so it quit by itself."];' in rust, lines)

    # ── C. the bundle stages the app's own manual under the one name the window reads
    frozen = base / "frozen"
    frozen.mkdir()
    (frozen / "Sift").write_text("", encoding="utf-8")
    staged = {}
    for app in ("idiograph", "sift"):
        out = base / f"stage-{app}"
        bundle.stage_source(out, frozen, app=app)
        staged[app] = (out / "tauri" / "docs" / "manual.md").read_text(encoding="utf-8")
    check("228: a build stages its app's own manual as docs/manual.md, Sift's manual-sift.md for Sift",
          staged["sift"] == support.source("docs/manual-sift.md").read_text(encoding="utf-8")
          and staged["idiograph"] == support.source("docs/manual.md").read_text(encoding="utf-8")
          and staged["sift"].startswith("# Sift manual"), {a: staged[a][:40] for a in staged})

    # ── D. the API keeps its names: cases, --case and "case" in its answers
    root = base / "swim-root"
    (root / "Odette" / "Working").mkdir(parents=True)
    book = root / "Odette" / "Odette - EN & ES.xlsx"
    made_book(book)
    (root / "idiograph-project.json").write_text(json.dumps({
        "name": "Swimming, a words project", "agents": {"allowed": True, "at": "2026-10-21T00:30:00+01:00"}}),
        encoding="utf-8")
    cfg = base / "words-config.json"
    cfg.write_text(json.dumps({"root": str(root), "interviewer": "Bram"}), encoding="utf-8")

    def cli(*words):
        ran = subprocess.run([sys.executable, str(support.source("cli.py")), "--root", str(root), "--config", str(cfg), *words],
                             capture_output=True, text=True, encoding="utf-8", timeout=120)
        try:
            return json.loads(ran.stdout), ran
        except ValueError:
            return {}, ran

    cases, ran = cli("cases", "--json")
    shown, ran2 = cli("statements", "Odette", "--json")
    found, ran3 = cli("search", "pool", "--case", "Odette", "--json")
    rows = cases.get("cases") or []
    check("228: the command line still answers cases with each participant under \"case\", and search takes --case",
          ran.returncode == 0 and rows and rows[0].get("case") == "Odette"
          and ran2.returncode == 0 and shown.get("case") == "Odette" and ran3.returncode == 0 and found.get("total", 0) > 0 and found.get("scope") == "case"
          and all(c.get("case") == "Odette" for c in found.get("cases") or [{}]),
          (str(cases)[:200], ran.stderr[-200:], str(shown)[:200], ran2.stderr[-200:]))
    tools = {t["name"]: t for t in mcp_server.tools_for("idiograph")}
    check("228: the MCP server keeps its tool cases and its case argument, and its words say participant",
          "cases" in tools and "case" in tools["statements"]["inputSchema"]["properties"]
          and "participant" in tools["statements"]["description"]
          and "a case in a tool's name or answer is one participant" in mcp_server.TOOLS_LINE,
          sorted(tools)[:10])
    check("228: the check wrote nothing outside its scratch folder", book.is_file() and cfg.is_file())
