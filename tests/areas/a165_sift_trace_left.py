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
from .support import check, grip_js, skip


def test_sift_trace_left(scratch):
    print("\n165. What the night's checks of 16 to 17 October left in Sift, Trace and Settings, each a defect or a "
          "written rule broken: failures in one tone, the ticks off the crux, a shortcut a row an act, a search with "
          "nothing to copy, a problem beside its cause, a type that reads as a choice, an unreached stage that reads, "
          "a restart of a --root run that keeps its lists, the keys on one baseline and New project's fields aligned")
    import server as server_mod
    import sift_search as ss

    read = lambda path: Path(path).read_text(encoding="utf-8")
    sjs, ssjs = support.text("apps/sift/static/sift.js"), support.text("apps/sift/static/sift_search.js")

    # ── D. Search strategy with no term: Copy held, the problem beside its cause, and Start new run held with Mark as registered
    check("165: no block with a term is its own problem, said under Search terms as well as under Register, the plan's "
          "problems in their order as before",
          ss.terms_problems(ss.clean_plan({"blocks": []})) == [ss.NO_TERM]
          and ss.terms_problems(ss.clean_plan({"blocks": [{"name": "Seeds", "terms": ["seed*"]}]})) == []
          and ss.NO_TERM in ss.problems(ss.clean_plan({"blocks": [], "databases": []})))
    review = scratch / "seed-review-165"
    shutil.rmtree(review, ignore_errors=True)
    review.mkdir(parents=True)
    plan = ss.blank_plan()
    plan["databases"] = ["epmc"]
    empty_state = ss.save(review, plan)
    plan["blocks"] = [{"name": "Seeds", "terms": ["seed*"], "scope": "tak", "scopes": {}}]
    full_state = ss.save(review, plan)
    check("165: the plan's state carries terms_problems, the line while no block holds a term and none once one does",
          empty_state.get("terms_problems") == [ss.NO_TERM] and ss.NO_TERM in empty_state.get("problems", [])
          and full_state.get("terms_problems") == [] and ss.NO_TERM not in full_state.get("problems", []),
          str((empty_state.get("terms_problems"), full_state.get("terms_problems"))))

    node = shutil.which("node")
    if not node:
        skip("165: Search strategy and Settings' Check in node", "node is not installed")
    else:
        base = scratch / "sift-trace-165"
        shutil.rmtree(base, ignore_errors=True)
        base.mkdir(parents=True)
        harness = r"""
const els = {};
const mk = (id) => ({ id, setAttribute(k, v) { (this.attrs = this.attrs || {})[k] = v; }, innerHTML: '', value: '', hidden: false, textContent: '', disabled: false, title: '', dataset: {},
  className: '', onclick: null, focus() {}, click() { return this.onclick ? this.onclick() : undefined; },
  querySelectorAll: () => [], querySelector: () => null, matches: () => false, closest: () => null });
const $ = (id) => els[id] || (els[id] = mk(id));
$('settings').hidden = true;
$('feedback').hidden = true;
$('sfs-ask').hidden = true;
$('sfs-mark-card').hidden = true;
let answer = {};
async function api(path, body) { return body && body.op === 'check' ? answer : {}; }
const say = () => {};
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;
const grow = () => {};
const needsRestart = () => false;
const RESTART_LINE = 'Restart the server to finish this update.';
const document = { activeElement: null, querySelectorAll: () => [], createElement: () => mk('made'), body: { insertBefore() {} } };
const window = { addEventListener() {}, scrollTo() {} };
const localStorage = { getItem: () => null, setItem() {} };
function siftOpen() {}
function sfLeave(then) { then(); }
async function loadLibrary() {}
"""
        harness += "\n".join(["const SF_DB_COLOURS = " + sjs.split("const SF_DB_COLOURS = ", 1)[1].split("};", 1)[0] + "};",
                              re.search(r"(?m)^const SF_DB_PALETTE = \d+;$", sjs).group(0),
                              re.search(r"(?m)^const sfPickKey = .*$", sjs).group(0),
                              "function sfDbKey(" + sjs.split("function sfDbKey(", 1)[1].split("\n}", 1)[0] + "\n}",
                              re.search(r"(?m)^const sfDbPill = .*$", sjs).group(0)]) + "\n"
        body = grip_js() + "\n" + support.table_js() + "\n" + ssjs.rsplit("\nsfsBoot();", 1)[0]
        run = r"""
(async () => {
const out = {};
SFS.catalog = { sources: ['psycinfo', 'pubmed', 'scopus'], names: { psycinfo: 'PsycInfo', pubmed: 'PubMed', scopus: 'Scopus' },
  keyless: ['pubmed'], apis: ['pubmed', 'scopus'], scopes: [['tak', 'Title, abstract and keywords']], types: [], platformed: ['psycinfo'],
  platforms: [['ebsco', 'EBSCO']], sites: {}, platform_sites: { ebsco: 'https://search.ebscohost.com/' }, hosts: { ebsco: 'EBSCOhost' },
  fields: { scopus: [{ service: 'SEED_INDEX_KEY', label: 'API key' }] } };
SFS.folder = 'seed-review';
SFS.today = '2026-10-17';
SFS.how = { pubmed: 'api', psycinfo: 'export' };
SFS.listed = [];
SFS.plan = { databases: ['psycinfo', 'pubmed'], others: {}, platforms: { psycinfo: 'ebsco' }, blocks: [], years: {}, types: [],
  reasons: [], benchmark: [], benchmark_titles: {}, overrides: {} };
const strings = [
  { source: 'psycinfo', name: 'PsycInfo', platform: 'EBSCO', written: '', query: '', override: null, notes: [], limits: '' },
  { source: 'pubmed', name: 'PubMed', platform: '', written: '', query: '', override: null, notes: [], limits: '' }];
const line = 'Write at least one block with a term.';
SFS.data = { strings, current: { version: 1, registered: null }, versions: [{ version: 1, registered: null }], problems: [line],
  terms_problems: [line], block_problems: [], plan: SFS.plan };
SFS.runs = [];
SFS.review = { folder: 'seed-review', searches: true, screening: '' };
sfsDrawStrings();
out.empty = $('sfs-strings').innerHTML;
sfsDrawBlockProblems();
out.terms = [$('sfs-terms-said').innerHTML, $('sfs-terms-said').hidden];
sfsDrawRun();
out.heldRun = $('sfs-run').disabled;
sfsDrawVersion();
out.heldMark = $('sfs-mark').disabled;
strings[0].query = strings[0].written = 'TI seed*';
strings[1].query = strings[1].written = 'seed*[tiab]';
SFS.data = Object.assign({}, SFS.data, { problems: [], terms_problems: [] });
sfsDrawStrings();
out.full = $('sfs-strings').innerHTML;
sfsDrawBlockProblems();
out.termsAfter = [$('sfs-terms-said').innerHTML, $('sfs-terms-said').hidden];
sfsDrawRun();
out.freeRun = $('sfs-run').disabled;
// Check under a database's key in Settings: a failure in the warning tint, then an answer in the small print
const st = { catalog: SFS.catalog, saved: { SEED_INDEX_KEY: true }, said: {}, failed: {} };
const row = { source: 'scopus', how: 'api' };
answer = { ok: false, said: 'Scopus did not answer (HTTP 503).' };
await dbsCheck(st, 'scopus', { disabled: false }, () => {});
out.failed = dbsAccessParts(st, row, 'k', 'Scopus').keys;
answer = { ok: true, said: 'Scopus accepted the key.' };
await dbsCheck(st, 'scopus', { disabled: false }, () => {});
out.answered = dbsAccessParts(st, row, 'k', 'Scopus').keys;
out.older = dbsAccessParts({ catalog: SFS.catalog, saved: {}, said: { scopus: 'Key saved.' } }, row, 'k', 'Scopus').keys;
console.log(JSON.stringify(out));
})().catch((e) => { console.error(e.stack || String(e)); process.exit(1); });
"""
        script = base / "search-165.js"
        script.write_text(harness + body + "\n" + run, encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60,
                             env=dict(os.environ, TZ="UTC"))
        o, why = {}, ""
        try:
            o = json.loads(ran.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            why = (ran.stderr or ran.stdout).strip()[:500]
        empty = o.get("empty", "")
        check("165: in node, a search with no term yet holds Copy and Copy the search, which had nothing to copy, and "
              "both stand free once the plan writes a search",
              'sfs-src-copy" disabled>' in empty and 'sfs-copy" disabled>' in empty
              and 'sfs-src-copy">' in o.get("full", "") and 'sfs-copy">' in o.get("full", "")
              and " disabled>" not in o.get("full", "").split("sfs-copy", 1)[-1][:12],
              why or empty[:400])
        check("165: in node, no block with a term says so under Search terms, beside its cause, in the warning tint's "
              "problem box, and the line goes once a block holds one",
              o.get("terms") == ["<p>Write at least one block with a term.</p>", False] and o.get("termsAfter") == ["", True],
              why or str((o.get("terms"), o.get("termsAfter"))))
        check("165: in node, Start new run is held while something stands in the way of the plan, as Mark as registered is, "
              "where it stood filled and a press was refused in a toast, and is free once nothing does",
              o.get("heldRun") is True and o.get("heldMark") is True and o.get("freeRun") is False,
              why or str((o.get("heldRun"), o.get("heldMark"), o.get("freeRun"))))
    # ── H. a --root run's restart keeps its Sift and Trace lists, carried across in its environment
    held = {"recent": [], "sift_reviews": [{"folder": "seed-review", "opened": 1, "name": "Seed library"}],
            "trace_projects": [{"folder": "seed-paper", "opened": 1}]}
    kept = (server_mod.STATE_MEMORY, server_mod.RELAUNCH, server_mod.ARGV)
    try:
        server_mod.RELAUNCH = None
        server_mod.ARGV = [str(support.source("server.py")), "--root", str(review)]
        server_mod.STATE_MEMORY = json.loads(json.dumps(held))
        _, carried = server_mod.relaunch()
        server_mod.STATE_MEMORY = None
        _, plain = server_mod.relaunch()
        os.environ[server_mod.STATE_CARRIED] = "stale"
        _, inherited = server_mod.relaunch()
        os.environ.pop(server_mod.STATE_CARRIED, None)
    finally:
        server_mod.STATE_MEMORY, server_mod.RELAUNCH, server_mod.ARGV = kept
    env = {server_mod.STATE_CARRIED: json.dumps(held)}
    back = server_mod.carried_state(env)
    check("165: a restart of a --root run carries its list, Sift's reviews and Trace's projects with its recent cases, in its "
          "environment, which the run reads back and takes out, a run without --root carrying none and dropping any it "
          "inherited, and nothing readable reads as an empty list",
          json.loads(carried.get(server_mod.STATE_CARRIED, "{}")) == held and server_mod.STATE_CARRIED not in plain
          and server_mod.STATE_CARRIED not in inherited and back == held and server_mod.STATE_CARRIED not in env
          and server_mod.carried_state({server_mod.STATE_CARRIED: "not json"}) == {"recent": []}
          and server_mod.carried_state({server_mod.STATE_CARRIED: "[1, 2]"}) == {"recent": []}
          and server_mod.carried_state({server_mod.STATE_CARRIED: '{"sift_reviews": []}'}) == {"sift_reviews": [], "recent": []})

    # a real server with --root, its review and paper put in its list, restarted by Settings' own Restart
    if sys.platform.startswith("win"):
        skip("165: a real --root server restarted keeps its lists", "Windows starts a restart anew through its launcher")
        return
    root = scratch / "restart-165-root"
    root.mkdir(exist_ok=True)
    cfg = scratch / "restart-165.json"
    cfg.write_text(json.dumps({"interviewer": "Wren"}), encoding="utf-8")
    paper_place = scratch / "restart-165-paper"
    shutil.rmtree(paper_place, ignore_errors=True)
    paper_place.mkdir()
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    own = f"http://127.0.0.1:{port}"

    def ask(method, path, payload=None, origin=None):
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=20)
        headers = {"Host": f"127.0.0.1:{port}"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if origin:
            headers["Origin"] = origin
        conn.request(method, path, None if payload is None else json.dumps(payload), headers)
        res = conn.getresponse()
        raw = res.read()
        conn.close()
        try:
            return res.status, json.loads(raw or b"{}")
        except ValueError:
            return res.status, {}

    def started(watch, seconds=20, other=None):
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            try:
                code, said = ask("GET", "/api/server")
                if code == 200 and said.get("started") and said.get("started") != other:
                    watch.answered()
                    return said["started"]
            except OSError:
                pass
            time.sleep(0.2)
        watch.ran_out(f"started's {seconds} s ran out")
        return None

    envs = {k: v for k, v in os.environ.items() if k != server_mod.STATE_CARRIED}
    envs.update(PYTHONUNBUFFERED="1", IDIOGRAPH_STAY_OPEN="1")
    envs = support.faulty_env(envs)
    # since the cutover (the sixth build, 23 October 2026) each on its own app's server, Sift's and Trace's
    real, outs, watches = {}, {}, {}
    lists = {"sift": ("/api/sift-review", {"op": "open", "folder": str(review), "name": "Seed library"}, "reviews"),
             "trace": ("/api/trace-project", {"op": "new", "folder": str(paper_place), "name": "Seed paper"}, "traces")}
    for app, (route, body, key) in lists.items():
        kid = subprocess.Popen([sys.executable, str(support.source("server.py")), "--app", app, "--port", str(port),
                                "--no-browser", "--root", str(root), "--config", str(cfg)],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=envs)
        # what a failure says of the server (cidiag, 7 November 2026): a wait that runs out, or a connect that
        # fails, aborts it, and the check says what it saw instead of the area ending on a bare traceback
        watch = watches[app] = support.ChildWatch(kid, port)
        said = real[app] = {}
        try:
            first = started(watch)
            said["up"] = bool(first)
            said["made"] = ask("POST", route, body, own)[0]
            said["before"] = [r.get("name") for r in ask("GET", "/api/home")[1].get(key) or []]
            said["restart"] = ask("POST", "/api/server", {"op": "restart"}, own)[0]
            again = started(watch, 30, first)
            said["again"] = bool(again) and again != first
            said["after"] = [r.get("name") for r in ask("GET", "/api/home")[1].get(key) or []]
            said["quit"] = ask("POST", "/api/server", {"op": "quit"}, own)[0]
            try:
                kid.wait(20)
            except subprocess.TimeoutExpired:
                watch.ran_out("the wait for the quit ran out")
        except (OSError, http.client.HTTPException, ValueError) as err:
            said["failed call"] = f"{type(err).__name__}: {err}"
            watch.ran_out(f"a call failed ({said['failed call']})")
        finally:
            if kid.poll() is None:
                kid.kill()
                kid.wait(10)
        outs[app] = kid.stdout.read().decode("utf-8", errors="replace")
        kid.stdout.close()
    kept_lists = (all(s.get("up") and s.get("made") == 200 and s.get("restart") == 200 and s.get("again") for s in real.values())
                  and real["sift"].get("before") == ["Seed library"] and real["trace"].get("before") == ["Seed paper"]
                  and all(s.get("after") == s.get("before") for s in real.values())
                  and not any((root / n).exists() for n in ("state.json", "state.sift.json", "state.trace.json")))
    check("165: a real server started with --root, Sift's with a review and Trace's with a project in its list, "
          "restarted by Settings' Restart, lists it again, where it came back with none",
          kept_lists, str(real) if kept_lists else f"{real}\n" + "\n".join(
              f"{app}'s server: {watches[app].says(outs[app])}" for app in real))
