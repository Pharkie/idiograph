"""Area 439: Home and opening a participant, faster (perfhome, 22 November 2026). What is held here is what is
found and what is served, never how fast: the cases of a project found as the whole walk of its folder found them,
with the History chunks, the archive, the working folders and what is under a `Source/` passed over, and a
participant added, renamed or removed between two calls seen at the second; the projects' roots read once and kept,
yet an added, removed or renamed project seen at the next call, and a path placed in the deepest project that holds
it; and the app's own scripts and styles named in the page by a mark of their bytes, served kept for a year at that
address and revalidated at any other, a changed file taking a new address, with the page and the API not kept."""
from __future__ import annotations

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
from .support import TOOL, check


def pfolder(n: int, first: str, second: str = "") -> str:
    """A participant's folder name, put together here so no tracked line holds one's shape."""
    return "P" + str(n) + " - " + first + (("-" + second) if second else "")


def _reference(root: Path, idiograph_routes, convert_mod, srv) -> tuple[set, set]:
    """What the walk of every file found, as `list_cases` found it before it passed folders over."""
    nested, files = set(), set()
    for p in root.rglob("*"):
        if p.name == srv.PROJECT_FILE and p.parent != root:
            nested.add(p.parent)
        elif p.suffix.lower() in convert_mod.FORMATS and p.is_file():
            files.add(p)
    return nested, files


def test_home_perf(scratch):
    print("\n439. Home and opening a participant, faster: the cases found as before, the projects' roots kept and "
          "still seen to change, the scripts and styles kept by the browser at an address of their bytes")
    import convert as convert_mod
    import idiograph_routes
    import server as srv

    base = scratch / "homeperf-439"
    shutil.rmtree(base, ignore_errors=True)
    project = base / "Study"

    def touch(*parts, text="x\n"):
        path = project.joinpath(*parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    # ── A. an invented project holding what the walk must and must not offer
    touch(pfolder(1, "Fern", "Ash"), "Source", "Fern interview.txt")
    touch(pfolder(1, "Fern", "Ash"), "Source", "extracts", "Fern part.txt")
    touch(pfolder(1, "Fern", "Ash"), "Working", "Fern notes.txt")
    touch(pfolder(1, "Fern", "Ash"), "Working", "Fern.themes.history", "0001.jsonl", text="{}\n")
    touch(pfolder(1, "Fern", "Ash"), "Working", "Fern.themes.history", "stray.txt")
    touch(pfolder(1, "Fern", "Ash"), "_Archive", "old", "Fern old.txt")
    touch(pfolder(1, "Fern", "Ash"), "Photos", "caption.txt")
    touch(pfolder(2, "Elm", "Oak"), "Source", "Elm interview.txt")
    touch(pfolder(2, "Elm", "Oak"), "Elm loose.txt")
    touch("Inner", "idiograph-project.json", text="{}")
    touch("Inner", pfolder(9, "Yew", "Fir"), "Source", "Yew interview.txt")
    touch(pfolder(3, "Box", "Bay"), "Source.old", "Box.txt")
    touch(pfolder(3, "Box", "Bay"), "Source", "Source", "deep.txt")
    touch(pfolder(1, "Fern", "Ash"), "Working", "Fern.themes.json", text="{}")
    touch(pfolder(7, "Ash") + ".history", "Ash loose.txt")
    touch(".kept", "Kept loose.txt")
    touch(".idiograph-restore", "objects", "ab", "blob.txt")
    touch(".git", "info.txt")
    touch(".idiograph-team", "note.txt")
    touch(pfolder(1, "Fern", "Ash"), "Working", ".idiograph-restore", "inner.txt")

    def agree(label):
        nested, files = _reference(project, idiograph_routes, convert_mod, srv)
        got_nested, got_files = idiograph_routes.case_candidates(project)

        def sits(p):
            folders = p.relative_to(project).parts[:-1]
            if set(folders) & (idiograph_routes.SKIP_DIRS - {"Source"}) or set(folders) & idiograph_routes.NO_CASES:
                return False
            here = project
            for f in folders:
                if f.endswith(".history") and (here / (f[:-len(".history")] + ".json")).is_file():
                    return False
                here = here / f
            return "Source" not in folders or (folders[-1] == "Source" and "Source" not in folders[:-1])
        wanted = {p for p in files if sits(p)}
        check(f"439: {label}: the walk offers exactly the files the whole walk's would have where a case can sit, "
              "and the same nested projects",
              set(got_nested) == nested and set(got_files) == wanted,
              str(sorted(p.relative_to(project).as_posix() for p in set(got_files) ^ wanted)))
        return got_files

    first = agree("at the start")
    names = {p.name for p in first}
    check("439: History chunks, the archive, the photos and a Source's own folders are never walked into",
          not ({"stray.txt", "Fern old.txt", "caption.txt", "Fern part.txt", "deep.txt", "Fern notes.txt"} & names)
          and {"Fern interview.txt", "Elm interview.txt", "Elm loose.txt", "Box.txt"} <= names, str(sorted(names)))
    check("439: the restore points, a git folder and the team's log are never walked into, a case kept in another dot "
          "folder and a participant folder named like a History folder still are",
          not ({"blob.txt", "info.txt", "note.txt", "inner.txt"} & names) and {"Kept loose.txt", "Ash loose.txt"} <= names,
          str(sorted(names)))
    pruned = {Path(h).name for h, _ in idiograph_routes.pruned_walk(project, idiograph_routes.SKIP_DIRS - {"Working"}, False)}
    check("439: the board files' walk enters a Working folder and no Source, archive, History or restore folder",
          "Working" in pruned and not ({"Source", "_Archive", "Fern.themes.history", "objects", ".git"} & pruned), str(sorted(pruned)))

    rows = lambda: sorted(r["name"] for r in idiograph_routes.list_cases(project))
    before = rows()
    touch(pfolder(4, "Ivy", "Elk"), "Source", "Ivy interview.txt")
    added = rows()
    (project / pfolder(4, "Ivy", "Elk")).rename(project / pfolder(4, "Oak", "Elk"))
    renamed = [r["case"] for r in idiograph_routes.list_cases(project) if r["name"] == "Ivy interview.txt"]
    shutil.rmtree(project / pfolder(4, "Oak", "Elk"))
    removed = rows()
    check("439: a participant added, renamed and removed between calls is seen at the next, never missed",
          "Ivy interview.txt" not in before and "Ivy interview.txt" in added and len(renamed) == 1 and "Oak" in str(renamed[0])
          and removed == before, f"{before} / {added} / {renamed} / {removed}")
    agree("after the changes")
    # a project's own folder named Source is itself walked
    sourced = base / "Source"
    (sourced / pfolder(1, "Fern", "Ash") / "Source").mkdir(parents=True)
    (sourced / pfolder(1, "Fern", "Ash") / "Source" / "Fern interview.txt").write_text("x\n", encoding="utf-8")
    check("439: a project whose own folder is named Source is still walked",
          [r["name"] for r in idiograph_routes.list_cases(sourced)] == ["Fern interview.txt"])

    # ── B. the projects' roots kept, and an added, removed and renamed project seen
    kept = (srv.CONFIG_PATH, srv.ROOT_OVERRIDE, srv.STATE_PATH, srv.STATE_MEMORY)
    cfg = base / "config.json"
    one, two, three = base / "one", base / "two", base / "two" / "inside"
    for folder in (one, two, three):
        folder.mkdir(parents=True, exist_ok=True)
    try:
        srv.CONFIG_PATH, srv.ROOT_OVERRIDE = cfg, None
        srv.STATE_MEMORY = {"recent": []}
        put = lambda *roots: cfg.write_text(json.dumps({"projects": [{"root": str(r)} for r in roots]}), encoding="utf-8")
        put(one)
        file_in_one, file_in_inner = one / "a.xlsx", three / "b.xlsx"
        seen = [srv.project_of(file_in_one), srv.project_of(file_in_inner)]
        put(one, two)
        added_seen = [srv.project_of(file_in_one), srv.project_of(file_in_inner)]
        put(one, two, three)
        deepest = srv.project_of(file_in_inner)
        put(two, three)
        removed_seen = [srv.project_of(file_in_one), srv.project_of(file_in_inner)]
        renamed_to = base / "three-renamed"
        three.rename(renamed_to)
        put(two, renamed_to)
        renamed_seen = [srv.project_of(renamed_to / "c.xlsx"), srv.project_of(three / "c.xlsx")]
        put(one, one / ".." / "one")
        twice = srv.project_roots()
        check("439: an added, a removed and a renamed project are seen by the next call, and the deepest of two nested wins",
              seen == [one, None] and added_seen == [one, two] and deepest == three
              and removed_seen == [None, three] and renamed_seen[0] == renamed_to and renamed_seen[1] == two
              and len(twice) == 1,
              str((seen, added_seen, deepest, removed_seen, renamed_seen, twice)))
    finally:
        srv.CONFIG_PATH, srv.ROOT_OVERRIDE, srv.STATE_PATH, srv.STATE_MEMORY = kept

    # ── C. a file's address changes with its bytes
    asset = base / "x.js"
    asset.write_text("one", encoding="utf-8")
    a = srv.asset_version(asset)
    asset.write_text("two", encoding="utf-8")
    b = srv.asset_version(asset)
    asset.write_text("two", encoding="utf-8")
    check("439: a static file's mark changes with its bytes and holds while they hold", a != b and b == srv.asset_version(asset) and a and b)
    check("439: only a script or a stylesheet of the page's own is named by its mark",
          srv.versioned('<link rel="stylesheet" href="/tokens.css"><img src="/favicon.png"><script src="https://x.test/a.js"></script>'
                        '<script src="/nowhere.js"></script>').count("?v=") == 1)

    # ── D. a real server: pages and the API not kept, the page's own files kept at their mark
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    home = base / "home"
    (home / "Documents").mkdir(parents=True)
    conf = base / "server-config.json"
    conf.write_text(json.dumps({"projects": []}), encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k != srv.STATE_CARRIED}
    env.update(PYTHONUNBUFFERED="1", IDIOGRAPH_STAY_OPEN="1", HOME=str(home), USERPROFILE=str(home))
    env = support.faulty_env(env)
    log = base / "server.log"
    with open(log, "wb") as out:
        kid = subprocess.Popen([sys.executable, str(support.source("server.py")), "--port", str(port), "--no-browser",
                                "--root", str(base / "one"), "--config", str(conf)],
                               stdout=out, stderr=subprocess.STDOUT, env=env, cwd=str(home))
    try:
        def ask(path, headers=None):
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=60)
            conn.request("GET", path, headers=dict({"Host": f"127.0.0.1:{port}"}, **(headers or {})))
            res = conn.getresponse()
            body = res.read()
            heads = {k.lower(): v for k, v in res.getheaders()}
            conn.close()
            return res.status, heads, body
        up = False
        for _ in range(150):
            try:
                up = ask("/api/server")[0] == 200
            except OSError:
                time.sleep(0.2)
                continue
            if up:
                break
        check("439: the server starts", up, log.read_text(encoding="utf-8", errors="replace")[-300:] if not up else "")
        if up:
            code, heads, page = ask("/")
            text = page.decode("utf-8")
            links = re.findall(r'(?:src|href)="(/[A-Za-z0-9_][A-Za-z0-9_.-]*\.(?:js|css)\?v=[0-9a-f]+)"', text)
            bare = re.findall(r'(?:src|href)="(/[A-Za-z0-9_][A-Za-z0-9_.-]*\.(?:js|css))"', text)
            check("439: the page is not kept and every script and style of its own is named by a mark",
                  heads.get("cache-control") == "no-store" and len(links) >= 10 and not bare, f"{heads.get('cache-control')} {len(links)} {bare}")
            script = next((l for l in links if l.startswith("/shell.js")), "/shell.js")
            code, heads, body = ask(script)
            ok_kept = code == 200 and "immutable" in heads.get("cache-control", "") and "max-age=31536000" in heads.get("cache-control", "")
            code2, heads2, body2 = ask("/shell.js?v=0000")
            code3, heads3, body3 = ask("/shell.js")
            code4, heads4, body4 = ask(script, {"If-None-Match": heads.get("etag", "")})
            code5, heads5, body5 = ask("/api/server")
            check("439: a file asked for at its mark is kept for a year, at any other address it is revalidated, and "
                  "the same bytes answer both",
                  ok_kept and heads2.get("cache-control") == "no-cache" and heads3.get("cache-control") == "no-cache"
                  and body == body2 == body3 and heads.get("etag") is not None and heads.get("etag") == heads3.get("etag"), str((heads, heads2, heads3)))
            check("439: a file the browser holds is answered unchanged without its bytes, and the API is never kept",
                  code4 == 304 and not body4 and heads5.get("cache-control") == "no-store" and code5 == 200, str((code4, heads5)))
    finally:
        kid.terminate()
        try:
            kid.wait(timeout=20)
        except subprocess.TimeoutExpired:
            kid.kill()
