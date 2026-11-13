"""Area 226: a command and an MCP server per app (the split's fifth build, 20 October 2026). `sift` takes
what `idiograph sift` took at its top and `trace` what `idiograph trace` took, each refusing another app's
command by name. Each MCP server lists its own tools and the shared search alone. Until the cutover (the
family codebase's sixth build, 23 October 2026) `idiograph sift ...` and `idiograph trace ...` answered as
aliases and Idiograph's MCP server kept Sift's and Trace's tools, and since it each is refused by name. A
live review's commands, `search strings` and `search run --draft --date --follows`, run through `sift` on a
copy of one invented review, and through `idiograph sift` on another are refused, writing nothing."""
from __future__ import annotations

import argparse
import base64
import hashlib
import http.server
import json
import os
import shlex
import shutil
import subprocess
import sys
import threading
from datetime import date
from pathlib import Path

from . import support
from .support import TOOL, check

# An invented review on hedge-laying volunteers, its plan by export alone, so no run asks any database
PLAN = {"databases": ["psycinfo", "cinahl"],
        "blocks": [{"name": "Hedges", "terms": "hedgerow*\n\"hedge laying\"", "scope": "tak"},
                   {"name": "Volunteers", "terms": ["volunteer*", "\"conservation group\""], "scope": "tak"}],
        "years": {"from": "2008", "to": 2026}, "types": ["article"],
        "reasons": [{"code": "E1", "meaning": "Not about hedges"}, {"code": "E2", "meaning": "No volunteers"}]}
LISTED = [{"source": "psycinfo", "platform": "ebsco", "how": "export"},
          {"source": "cinahl", "platform": "ebsco", "how": "export"}]
PSYCINFO = ("TY  - JOUR\nTI  - Pleaching in the frost\nAU  - Thorn, A.\nPY  - 2017///\n"
            "JO  - Journal of Invented Hedges\nAB  - Eleven volunteers laid a hedge over a winter.\nKW  - hedgerows\nER  - \n\n"
            "TY  - JOUR\nTI  - The slow work of the billhook\nAU  - Hazel, B.\nAU  - Stake, C.\nPY  - 2022///\n"
            "JO  - Invented Rural Studies\nAB  - A conservation group spoke of patience with the stems.\nER  - \n")
CINAHL = ("TY  - JOUR\nTI  - Volunteers along the lane\nAU  - Binder, D.\nPY  - 2014///\n"
          "JO  - Invented Nursing Outdoors\nAB  - Retired nurses joined a hedge laying day.\nER  - \n")


def digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def test_app_commands(scratch):
    print("\n226. A command and an MCP server per app, another app's command refused by name, the aliases gone "
          "with the cutover, and a live review's commands through sift alone")
    import app_identity
    import cli
    import mcp_server
    import sift_mcp
    import server as server_mod
    import sift_routes
    from .a222_routes import masked, tree

    base = scratch / "app-commands-226"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    cfg = base / "config.json"
    cfg.write_text(json.dumps({"corpus": "", "gravity_reference": "", "corpus_exclude": [], "projects": [],
                               "databases": LISTED}), encoding="utf-8")
    wt_files = [TOOL / n for n in ("state.json", "config.json", "state.sift.json", "state.trace.json",
                                   "config.sift.json", "config.trace.json")]
    wt_before = {p.name: digest(p) for p in wt_files}
    cfg_before = digest(cfg)

    # ── A. the launchers: one per app beside idiograph's, each running cli.py as its app
    # The .bat's line endings are the checkout's, CRLF by .gitattributes, so the check reads the attribute
    # and the words: a copy written by git apply, or the gate's snapshot of one, holds the blob's LF
    attributes = support.source(".gitattributes").read_text(encoding="utf-8").splitlines()
    for app in ("sift", "trace"):
        sh = (TOOL / app).read_text(encoding="utf-8")
        bat = (TOOL / f"{app}.bat").read_bytes().replace(b"\r\n", b"\n")
        check(f"226: the {app} command and {app}.bat run cli.py as {app}, beside idiograph's, with their line endings set",
              os.access(TOOL / app, os.X_OK) and f'cli.py" --app {app} "$@"' in sh and '.venv/bin/python3' in sh
              and f"cli.py\" --app {app} %*".encode() in bat and bat.startswith(b"@echo off\n")
              and "*.bat text eol=crlf" in attributes and f"/{app} text eol=lf" in attributes
              and "\r" not in sh)

    # ── B. a screening and a Trace project, invented, and the review a live review session's commands run on
    import trace_claims
    project = base / "Hedge claims"
    trace_claims.make(project, "Hedge claims")
    review = base / "prep" / "Hedge review"
    review.mkdir(parents=True)
    held = (server_mod.CONFIG_PATH, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.STATE_MEMORY = cfg, {"recent": []}
        made = sift_routes.api_sift_review({"op": "new", "folder": str(review), "name": "Hedge review"})
        saved = sift_routes.api_sift_search({"op": "save", "folder": str(review), "plan": PLAN})
        dropped = [sift_routes.api_sift_search({"op": "drop", "folder": str(review), "source": source, "name": name,
                                               "data": base64.b64encode(words.encode()).decode()})
                   for source, name, words in (("psycinfo", "PsycInfo export.ris", PSYCINFO),
                                               ("cinahl", "CINAHL export.ris", CINAHL))]
    finally:
        server_mod.CONFIG_PATH, server_mod.STATE_MEMORY = held
    check("226: the invented review is made, its plan saved and both exports dropped, in-process",
          not made.get("error") and not saved.get("error") and not any(d.get("error") for d in dropped),
          str([made.get("error"), saved.get("error")] + [d.get("error") for d in dropped]))

    # a loopback stub any search would reach, none expected
    hits: list[str] = []

    class Stub(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            hits.append(self.path)
            body = b'{"results": [], "meta": {"count": 0}}'
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        do_POST = do_GET

    stub = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=stub.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    env = {k: v for k, v in os.environ.items() if k != server_mod.STATE_CARRIED}
    # the launchers find the venv beside them or two folders up, and else the python3 first on the path,
    # this run's own
    env.update(PYTHONUNBUFFERED="1", IDIOGRAPH_STAY_OPEN="1", PATH=f"{Path(sys.executable).parent}{os.pathsep}"
               f"{env.get('PATH', '')}", IDIOGRAPH_SEARCH_STUB=f"http://127.0.0.1:{stub.server_address[1]}")

    def launch(command: str, *words) -> subprocess.CompletedProcess:
        return subprocess.run(["sh", str(TOOL / command), *map(str, words)], capture_output=True, encoding="utf-8",
                              env=env, cwd=str(base), timeout=180)

    try:
        # ── C. a live review's commands through `sift`, and through `idiograph sift` refused, on two copies
        today = date.today().isoformat()
        copies = {}
        for side in ("idiograph", "sift"):
            copy = base / side / review.name
            shutil.copytree(review, copy)
            before = tree(copy)
            lead = ("idiograph", "sift") if side == "idiograph" else ("sift",)
            run = lambda *words: launch(lead[0], *lead[1:], "search", *words, "--config", cfg)
            steps = {"strings": run("strings", copy),
                     "run": run("run", copy, "--draft", "--date", today, "--follows", "none")}
            # the refusal through idiograph sift is one for every command, so a reading one and a writing one
            # show it (testspeed, 2 November 2026: four launches were two)
            if side == "sift":
                steps.update({"run follows": run("run", copy, "--draft", "--date", today, "--follows", today),
                              "runs": run("runs", copy)})
            copies[side] = {"steps": steps, "files": {k: masked(v) for k, v in tree(copy).items()}, "folder": copy,
                            "before": before}
        codes = {side: {k: v.returncode for k, v in c["steps"].items()} for side, c in copies.items()}
        check("226: every command of a live review's answers through sift, and each is refused through idiograph sift",
              set(codes["sift"].values()) == {0} and 0 not in codes["idiograph"].values(),
              str(codes) + " " + " ".join(v.stderr[:160] for v in copies["sift"]["steps"].values() if v.returncode))
        aliases = copies["idiograph"]
        # Idiograph names no other app since nosiftrace (12 November 2026): `sift` is no command of it
        check("226: idiograph sift is refused as no command of Idiograph's, naming no other app, and writes nothing",
              all("invalid choice: 'sift'" in v.stderr and "Sift" not in v.stderr for v in aliases["steps"].values())
              and tree(aliases["folder"]) == aliases["before"],
              " | ".join(v.stderr.strip()[:120] for v in aliases["steps"].values()))
        a = copies["sift"]["files"]
        wanted = {"screening.csv", "reasons.csv", "log.csv", "run.json"}
        check("226: sift's copy holds the runs' files and runs/numbers.json, two runs that day",
              wanted <= {Path(n).name for n in a} and "runs/numbers.json" in a and f"runs/{today}/run.json" in a
              and f"runs/{today}-2/run.json" in a and copies["sift"]["steps"]["strings"].stdout.strip(), str(sorted(a)[:20]))
        check("226: no request left the machine, and none reached the stub", hits == [], str(hits[:3]))

        # ── D. each command its app's own, another's refused by name, the aliases gone with the cutover
        screening = copies["sift"]["folder"] / "runs" / today
        counts = {"sift": launch("sift", screening, "counts", "--json", "--config", cfg),
                  "alias": launch("idiograph", "sift", screening, "counts", "--json", "--config", cfg),
                  "old form": launch("sift", "sift", screening, "counts", "--json", "--config", cfg)}
        check("226: sift <screening> counts answers, sift sift as it, and idiograph sift <screening> counts is refused "
              "as no command of Idiograph's, naming no other app",
              counts["sift"].returncode == 0 and counts["old form"].returncode == 0
              and json.loads(counts["sift"].stdout) == json.loads(counts["old form"].stdout)
              and counts["alias"].returncode != 0 and "invalid choice: 'sift'" in counts["alias"].stderr
              and "Sift" not in counts["alias"].stdout + counts["alias"].stderr,
              " ".join((c.stderr or c.stdout)[:120] for c in counts.values()))
        traced = {"trace": launch("trace", project, "--json", "--config", cfg),
                  "alias": launch("idiograph", "trace", project, "--config", cfg)}
        check("226: trace <project> answers, and idiograph trace <project> is refused as no command of Idiograph's, "
              "naming no other app",
              traced["trace"].returncode == 0 and json.loads(traced["trace"].stdout) and traced["alias"].returncode != 0
              and "invalid choice: 'trace'" in traced["alias"].stderr and "Trace" not in traced["alias"].stderr,
              " ".join(c.stderr[:120] for c in traced.values()))
        refusals = {"sift cases": launch("sift", "cases", "--config", cfg),
                    "sift trace": launch("sift", "trace", project),
                    "trace sift": launch("trace", "sift", screening, "counts"),
                    "trace board": launch("trace", "board", "list", "Wren"),
                    "sift search words": launch("sift", "search", "hedge", "--config", cfg)}
        check("226: each command refuses another app's by name, saying the command to run, and writes nothing",
              all(r.returncode == 1 for r in refusals.values())
              and refusals["sift cases"].stderr.startswith("cases is Idiograph's, not Sift's. Run it as: idiograph cases")
              and refusals["sift trace"].stderr.startswith(f"trace is Trace's, not Sift's. Run it as: trace {shlex.quote(str(project))}")
              and refusals["trace sift"].stderr.startswith("sift is Sift's, not Trace's. Run it as: sift ")
              and refusals["trace board"].stderr.startswith("board is Idiograph's, not Trace's.")
              and refusals["sift search words"].stderr.startswith("Sift's Search reads one project by its folder"),
              " | ".join(f"{k}: {r.returncode} {r.stderr.strip()[:90]}" for k, r in refusals.items()))
        found = {"sift": launch("sift", "search", "volunteers", "--folder", screening, "--json", "--config", cfg),
                 "alias": launch("idiograph", "search", "volunteers", "--folder", screening, "--json", "--config", cfg),
                 "sift on trace": launch("sift", "search", "hedge", "--folder", project, "--config", cfg),
                 "trace on sift": launch("trace", "search", "hedge", "--folder", screening, "--config", cfg)}
        hits_s = json.loads(found["sift"].stdout or "{}") if found["sift"].returncode == 0 else {}
        check("226: sift search --folder is Sift's Search, idiograph search takes no --folder and names no other app, "
              "and Sift's and Trace's Search refuse the other's folder by name",
              found["sift"].returncode == 0 and hits_s.get("scope") == "sift" and hits_s.get("total", 0) > 0
              and found["alias"].returncode != 0 and "unrecognized arguments: --folder" in found["alias"].stderr
              and "Sift" not in found["alias"].stdout + found["alias"].stderr
              and found["sift on trace"].returncode == 1
              and found["sift on trace"].stderr.startswith("That folder is Trace's, not Sift's.")
              and found["trace on sift"].stderr.startswith("That folder is Sift's, not Trace's."),
              " | ".join(f"{k}: {r.returncode} {(r.stderr or r.stdout).strip()[:90]}" for k, r in found.items()))
        helped = {app: launch(app, "--help", "--config", cfg) for app in ("sift", "trace")}
        check("226: sift --help and trace --help give each command's own arguments under its own name",
              helped["sift"].stdout.startswith("usage: sift") and "--follows" in helped["sift"].stdout
              and helped["trace"].stdout.startswith("usage: trace") and "document" in helped["trace"].stdout)
    finally:
        stub.shutdown()
        stub.server_close()

    # ── E. the guard under the parser: a command of Idiograph's never runs as Sift or Trace
    kept = server_mod.app_held()
    try:
        server_mod.use_app("sift")
        stopped = []
        for args in (argparse.Namespace(command="cases", act=None), argparse.Namespace(command="trace", act=None,
                                                                                         folder=str(project)),
                     argparse.Namespace(command="search", act=None, words=["hedge"], folder=None)):
            try:
                cli.perform(args)
                stopped.append(None)
            except cli.Refused as exc:
                stopped.append(exc.lines[0])
    finally:
        server_mod.app_back(kept)
    check("226: run as Sift, cases, trace and a Search of the cases are refused before anything is read",
          stopped[0] == "cases is Idiograph's, not Sift's." and stopped[1] == "trace is Trace's, not Sift's."
          and stopped[2].startswith("Sift's Search reads one project by its folder"), str(stopped))
    check("226: a run given --config, and every run of Idiograph, makes no first start",
          cli.first_start("sift", ["x", "--config", str(cfg)]) is False and cli.first_start("idiograph", []) is False)

    # ── F. each MCP server's tools, its instructions and its guide
    every = [t["name"] for t in mcp_server.TOOLS]
    lists = {app: [t["name"] for t in mcp_server.Server(app=app).tools_list({})["tools"]] for app in app_identity.APPS}
    distil = {t["name"] for t in mcp_server.TOOLS if mcp_server.tool_app(t) == "idiograph"} - {"search", "agent_log"}
    # and each app's own agent log last, the family's tool by the name Idiograph's has (siftlog, 3 November 2026)
    sift_names = (["search"] + [t["name"] for t in sift_mcp.SIFT_TOOLS + sift_mcp.SEARCH_TOOLS]
                  + ["sift_search_databases", "agent_log"])
    check("226: Idiograph's MCP server lists its own tools and search alone since the cutover, none of Sift's or Trace's",
          lists["idiograph"] == [n for n, t in zip(every, mcp_server.TOOLS) if mcp_server.tool_app(t) == "idiograph"]
          and "sift_list" in every and "trace_claims" in every and "cases" in lists["idiograph"]
          and not any(n.startswith(("sift_", "trace_")) for n in lists["idiograph"]), str(lists["idiograph"]))
    check("226: Sift's MCP server lists Sift's tools and search alone, today's names, no tool of a case or of Trace",
          lists["sift"] == sift_names and not distil & set(lists["sift"]) and "trace_claims" not in lists["sift"],
          str(lists["sift"]))
    check("226: Trace's MCP server lists search, trace_claims and its agent log alone",
          lists["trace"] == ["search", "trace_claims", "agent_log"], str(lists["trace"]))
    own = {app: next(t for t in mcp_server.tools_for(app) if t["name"] == "search") for app in ("sift", "trace")}
    check("226: Sift's and Trace's search takes a folder, which it needs, and no case or board",
          all(t["inputSchema"]["required"] == ["words", "folder"] and not {"case", "board"} & set(t["inputSchema"]["properties"])
              for t in own.values()))
    sift_server = mcp_server.Server(app="sift")
    refused = []
    for name in ("cases", "trace_claims", "no_such"):
        try:
            sift_server.tools_call({"name": name, "arguments": {}})
            refused.append(None)
        except mcp_server.RpcError as exc:
            refused.append(exc.message)
    check("226: Sift's MCP server refuses another app's tool by name, and an unknown one as before",
          refused == ["cases is Idiograph's, not Sift's.", "trace_claims is Trace's, not Sift's.", "Unknown tool: no_such"],
          str(refused))
    told = {app: mcp_server.instructions(app) for app in app_identity.APPS}
    check("226: each server's instructions stay within area 206's ceiling, Read this first within what a client keeps",
          all(len(t) <= 8288 and t.startswith("Read this first.") for t in told.values())
          and "sift://guide" in told["sift"][:mcp_server.CORE_LIMIT] and "trace://guide" in told["trace"][:mcp_server.CORE_LIMIT]
          and "cases" not in told["trace"] and "Call cases first" not in told["sift"],
          str({a: len(t) for a, t in told.items()}))
    res = {app: [r["uri"] for r in mcp_server.Server(app=app).resources_list({})["resources"]] for app in ("sift", "trace")}
    read = sift_server.resources_read({"uri": "sift://guide/sifts-searches"})["contents"][0]["text"]
    check("226: Sift's and Trace's guides are their own, whole, the sections agents.md held until the cutover among "
          "them, and no schema",
          res["sift"][0] == "sift://guide" and "sift://guide/sifts-searches" in res["sift"]
          and res["trace"][0] == "trace://guide" and "trace://guide/trace" in res["trace"]
          and not any("schemas" in u or "project" in u for u in res["sift"] + res["trace"])
          and read.startswith("## Sift's searches") and mcp_server.Server(app="sift").prompts_list({}) == {"prompts": []},
          str(res))
    for app in ("sift", "trace"):
        skill = (support.source("skills") / app / "SKILL.md").read_text(encoding="utf-8")
        check(f"226: the {app} skill carries its guide word for word, under its name",
              skill.startswith(f"---\nname: {app}\ndescription: ")
              and skill.split("\n---\n\n", 1)[1] == (support.source("docs") / f"agents-{app}.md").read_text(encoding="utf-8"))

    # one real Sift MCP server on standard input and output, initialize, tools/list and one call
    lines = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18",
                                                                           "clientInfo": {"name": "claude-code"}}},
             {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
             {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
              "params": {"name": "sift_counts", "arguments": {"folder": str(screening)}}},
             {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "statements",
                                                                            "arguments": {"case": "Wren"}}}]
    ran = subprocess.run([sys.executable, str(support.source("mcp_server.py")), "--app", "sift", "--config", str(cfg)],
                         input="".join(json.dumps(m) + "\n" for m in lines), capture_output=True, encoding="utf-8",
                         env=env, cwd=str(base), timeout=120)
    answers = {a.get("id"): a for a in (json.loads(x) for x in ran.stdout.splitlines() if x.strip())}
    with_cli = cli.run(["--app", "sift", str(screening), "counts", "--json", "--config", str(cfg)])
    check("226: mcp_server.py --app sift answers as Sift, its own tools listed, sift_counts as the command line gives "
          "it, and statements refused as Idiograph's",
          answers.get(1, {}).get("result", {}).get("serverInfo", {}).get("name") == "sift"
          and [t["name"] for t in answers.get(2, {}).get("result", {}).get("tools", [])] == sift_names
          and answers.get(3, {}).get("result", {}).get("structuredContent") == json.loads(with_cli[1] or "null")
          and answers.get(4, {}).get("error", {}).get("message") == "statements is Idiograph's, not Sift's.",
          ran.stderr[-300:] or str(answers)[:300])

    # ── G. the cutover: with Idiograph serving none, the aliases and its Sift and Trace tools gone
    after = cli.run(["sift", str(screening), "counts", "--config", str(cfg)])
    after_t = cli.run(["trace", str(project)])
    names = [t["name"] for t in mcp_server.tools_for("idiograph")]
    check("226: since the cutover idiograph sift and idiograph trace are refused, since nosiftrace as no command of "
          "Idiograph's, and Idiograph's MCP server and routes keep their own alone",
          app_identity.SERVES_TOO == {"idiograph": (), "sift": (), "trace": ()}
          and after[0] == 2 and "Sift" not in after[1] + after[2]
          and after_t[0] == 2 and "Trace" not in after_t[1] + after_t[2]
          and not any(n.startswith(("sift_", "trace_")) for n in names) and "cases" in names and "search" in names
          and server_mod.apps_served("idiograph") == ("idiograph",), f"{after[2][:120]} {after_t[2][:80]}")

    # a server made in this process's code, as area 219's version check makes one, never makes a first start
    kept = server_mod.app_held()
    try:
        mcp_server.Server(app="trace").app_version()
    finally:
        server_mod.app_back(kept)
    wt_after = {p.name: digest(p) for p in wt_files}
    check("226: no settings or recent-list file of the code's own folder written, nor the trial's settings",
          wt_after == wt_before and digest(cfg) == cfg_before,
          str([n for n in wt_after if wt_after[n] != wt_before[n]]))
