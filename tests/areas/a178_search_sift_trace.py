from __future__ import annotations

import csv
import hashlib
import http.server
import io
import json
import os
import re
import shutil
import subprocess
import threading
import urllib.request
from pathlib import Path

from . import support
from .support import check, demo_copy, skip
import idiograph_routes
import idiograph_find

PLAN = {"databases": ["openalex"],
        "blocks": [{"name": "Ponds", "terms": ["pond*", "\"village pond\"", "mere"]},
                   {"name": "", "terms": ["volunteer*", "stewardship"]}],
        "reasons": [{"code": "E1", "meaning": "Not about a pond"}]}
RECORDS = [
    ("R001", "Pond dipping on the village green", "Marsh, A.", "Journal of Pond Life",
     "Volunteers who lead pond dipping describe the pond as a place of patience and small surprises."),
    ("R002", "Newts at dusk", "Reed, B.", "Amphibian Notes", "Counting newts by torchlight along the bank."),
    ("R003", "Frogspawn in spring", "Marsh, A.", "Spring Studies", "Frogspawn appears in March in most parishes."),
    ("R004", "Clearing the duckweed", "Okoro, T.", "Community Ecology Review", "A year with one pond group."),
]
PROTOCOL = """# A protocol on seed libraries

## Background

Seed libraries lend seeds to gardeners each spring (Okafor, 2019). Some keep paper records only (Vance & Ito, 2021).

## References

Okafor, N. (2019). *The first seed library*. Garden Press.

Vance, R., & Ito, K. (2021). Paper records in small libraries. *Library Notes*, 9, 20–31.

Zeller, P. (2015). Seed swaps at the parish fete. *Notes on Gardens*, 1, 1–4.
"""
SECOND = """# A second draft

## Aims

Libraries began in school halls (Okafor, 2019).

## References

Okafor, N. (2019). *The first seed library*. Garden Press.
"""


def test_search_sift_trace(scratch):
    print("\n178. Search across the app, build 2 of 2: Sift's records, decision notes, fields, form answers, key excerpts, "
          "search terms and exclusion reasons, Trace's claims, references and claim notes, Everything on the home screen "
          "with the kinds under their parts, Cmd + F on Sift's, Search strategy's and Trace's bars and the picker, "
          "read-only, 18 October")
    import app_search
    import sift_find
    import trace_find
    import server as server_mod
    import sift
    import trace_claims as tr

    read = lambda path: Path(path).read_text(encoding="utf-8")
    sjs, app = support.text("family/static/search.js"), support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    sift_js, ssjs = support.text("apps/sift/static/sift.js"), support.text("apps/sift/static/sift_search.js")
    trjs = support.text("apps/trace/static/trace.js")
    source = read(support.source("family/app_search.py"))
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: ("async " if f"async function {name}(" in src else "") + f"function {name}(" + fn(src, name) + "\n}"
    line_of = lambda src, start: next((ln for ln in src.splitlines() if ln.startswith(start)), "")
    node = shutil.which("node")

    # ── A. an invented Sift project on village ponds, an invented Trace project on seed libraries, and a Distil project
    base = scratch / "search-178"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Allotments"
    demo_copy(root, "Ivo", "Ivo - EN & ES.xlsx")
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({"name": "Allotments", "research_question": "How is a plot kept?"}),
                                                encoding="utf-8")
    review = base / "Pond review"
    run = review / "runs" / "2026-10-01"
    run.mkdir(parents=True)
    (review / "search_plan.json").write_text(json.dumps({"name": "Pond review", "versions": [
        {"version": 1, "saved": "2026-10-01T09:00:00+01:00", "registered": None, "reason": "", "plan": PLAN}]}), encoding="utf-8")
    (review / "reasons.csv").write_text("code,meaning\nE1,Not about a pond\nE2,Not a primary study\n", encoding="utf-8")
    buf = io.StringIO()
    out = csv.writer(buf, lineterminator="\n")
    out.writerow(["rec_id", "title", "authors", "year", "journal", "doi", "abstract"])
    for n, r in enumerate(RECORDS):
        out.writerow([r[0], r[1], r[2], "2020", r[3], f"10.5555/pond.{n}", r[4]])
    (run / "screening.csv").write_text(buf.getvalue(), encoding="utf-8")
    sift.decide(run, "R001", "ta", "include", note="Patience at the bank")
    sift.decide(run, "R001", "ft", "include")
    sift.decide(run, "R002", "ta", "maybe")
    sift.note(run, "R002", "ft", "Check the torch counts")
    sift.set_field(run, "R004", "digest", "A year of duckweed clearing")
    sift.form_field(run, None, {"name": "Setting", "type": "text", "where": "form"})
    sift.column(run, "add", name="Pond type", kind="text")
    sift.set_field(run, "R001", "col_setting", "A village green with a willow")
    sift.set_field(run, "R003", "col_pond_type", "a garden mere")
    words = "the pond as a place of patience"
    at = RECORDS[0][4].find(words)
    sift.excerpt(run, "add", "R001", "ta", [{"in": "abstract", "start": at, "end": at + len(words)}])
    sift.excerpt(run, "add", "R002", "ft", [{"in": "abstract", "start": 0, "end": 14}])
    seeds = base / "Seed check"
    tr.make(seeds, "Seed check")
    drafts = base / "Drafts"
    drafts.mkdir()
    (drafts / "seed protocol.md").write_text(PROTOCOL, encoding="utf-8")
    (drafts / "second draft.md").write_text(SECOND, encoding="utf-8")
    listing = base / "List only"
    tr.make(listing, "List only")
    (drafts / "refs.ris").write_text("TY  - BOOK\nAU  - Ober, Lena\nPY  - 2018\nTI  - Winter seed\nPB  - Hedge Press\nER  - \n",
                                     encoding="utf-8")
    saved = (server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_MEMORY = {"recent": [], "sift_reviews": [{"folder": str(review), "opened": 2}],
                               "trace_projects": [{"folder": str(seeds), "opened": 3}, {"folder": str(listing), "opened": 1}]}
    try:
        protocol = tr.add(seeds, drafts / "seed protocol.md")["doc"]
        second = tr.add(seeds, drafts / "second draft.md")["doc"]
        tr.set_list(listing, drafts / "refs.ris")
        claims = tr.rows(seeds, protocol)["rows"]
        okafor = next(r for r in claims if r["ref"] == "okafor2019" and r["kind"] == "claim")
        tr.act(seeds, protocol, okafor["key"], "note", "Check the lending dates")
        app_search.HELD.clear()
        def searched(body):
            """A search on the server of the app whose scope it is, Sift's, Trace's or for This case, This project and
            Everything Idiograph's, as each app's own page asks its own since the cutover (23 October 2026)."""
            with support.as_app(server_mod.SEARCH_SCOPE_APP.get(body.get("scope")) or "idiograph"):
                return server_mod.api_search(body)

        ask = lambda q, scope, **more: searched(dict({"q": q, "scope": scope}, **more))

        def every_app(q, **more):
            """Everything over all three apps' projects at once, the engine merging the parts in a study's order, as
            Idiograph's server answered it until the cutover, where each app's own answers its own part alone."""
            parts = {part: server_mod.SEARCH_ROWS[app]() for part, app in server_mod.SEARCH_PART_APP.items()}
            return app_search.search_all(q, kinds=more.get("kinds") or [], projects=more.get("projects") or [], **parts)
        first = lambda got, kind: next((r for r in got["results"] if r["kind"] == kind), None)
        sift_rev = ask("pond", "sift", folder=str(review))
        sift_run = ask("pond", "sift", folder=str(run))

        # ── B. Sift's kinds, where each is and where a click lands
        check("178: This Sift project reaches the screening its Screening step opens and its plan, from the review's folder "
              "and from the run's alike, its kinds Sift's seven",
              set(sift_rev["counts"]) == set(sift_find.SIFT_KINDS) and sift_rev["scope"] == "sift"
              and json.dumps(sift_rev["results"]) == json.dumps(sift_run["results"])
              and not sift_rev["cases"] and not sift_rev["sheets"] and "projects" not in sift_rev, str(sift_rev["counts"]))
        found = {kind: first(ask(q, "sift", folder=str(review), kinds=[kind]), kind) for kind, q in (
            ("record", "torchlight"), ("dnote", "torch counts"), ("field", "duckweed clearing"), ("form", "willow"),
            ("excerpt", "patience"), ("term", "stewardship"), ("reason", "primary study"))}
        check("178: each of Sift's seven kinds is found, a record by its abstract, a decision note, a field, a form's "
              "answer, a key excerpt, a search term and an exclusion reason", all(found.values()),
              str({k: bool(v) for k, v in found.items()}))
        go = {k: (v or {}).get("go", {}) for k, v in found.items()}
        screening_id = server_mod.rel_path(run.resolve())
        check("178: a record lands on Sift's screen at its stage with its part, R002 at full text since it has Maybe at "
              "title and abstract, named by its ID and the part, \"R002 · Abstract\", the screening named as the page names it",
              go["record"] == {"screen": "sift", "rec": "R002", "stage": "ft", "field": "abstract", "folder": screening_id}
              and found["record"]["where"] == "R002 · Abstract", str(go["record"]))
        by_id = ask("r003", "sift", folder=str(review))
        check("178: a record's ID is searched with its title, so \"r003\" finds R003's title alone",
              [(r["kind"], r["where"]) for r in by_id["results"]] == [("record", "R003 · Title")], str(by_id["results"]))
        check("178: a decision note lands at the stage it was made at with the caret in the note, a field on the record at "
              "its stage, a column on the table as a field and one on the form as a form's answer at Extract and appraise "
              "while the record is one of its papers",
              go["dnote"] == dict(go["dnote"], rec="R002", stage="ft", field="note") and found["dnote"]["where"] == "R002 · Full text"
              and go["field"] == dict(go["field"], rec="R004", stage="ta", field="digest") and found["field"]["where"] == "R004 · Digest"
              and go["form"] == dict(go["form"], rec="R001", stage="ex", field="col_setting", form=True)
              and found["form"]["where"] == "R001 · Setting"
              and first(ask("garden mere", "sift", folder=str(review)), "field")["go"]["field"] == "col_pond_type",
              str([go["dnote"], go["form"]]))
        check("178: a key excerpt lands at the stage it was made at, marked by its place in the record's list, named by "
              "that stage",
              go["excerpt"] == dict(go["excerpt"], rec="R001", stage="ta", field="excerpt", line=0)
              and found["excerpt"]["where"] == "R001 · Title and abstract"
              and first(ask("counting newts", "sift", folder=str(review), kinds=["excerpt"]), "excerpt")["go"]["stage"] == "ft",
              str(go["excerpt"]))
        review_id = server_mod.rel_path(review.resolve())
        check("178: a search term lands on Search strategy at its block and line, named by the block, and an exclusion "
              "reason by its code, read from the review's own reasons.csv",
              go["term"] == {"screen": "searches", "block": 1, "line": 1, "folder": review_id}
              and found["term"]["where"] == "Search strategy · Block 2"
              and first(ask("mere", "sift", folder=str(review), kinds=["term"]), "term")["where"] == "Search strategy · Block 1 · Ponds"
              and go["reason"] == {"screen": "searches", "reason": 1, "folder": review_id}
              and found["reason"]["where"] == "Search strategy · E2" and ask("e1", "sift", folder=str(review))["counts"]["reason"] == 1,
              str([go["term"], go["reason"]]))

        # ── C. Trace's kinds
        trace = ask("seed", "trace", folder=str(seeds))
        check("178: This Trace project reaches each manuscript's claims and references, its kinds Trace's three",
              set(trace["counts"]) == set(trace_find.TRACE_KINDS) and trace["counts"]["claim"] >= 1, str(trace["counts"]))
        claim = first(ask("paper records", "trace", folder=str(seeds)), "claim")
        note = first(ask("lending dates", "trace", folder=str(seeds)), "cnote")
        refs = [r for r in ask("first seed library", "trace", folder=str(seeds))["results"] if r["kind"] == "reference"]
        never = first(ask("parish fete", "trace", folder=str(seeds)), "reference")
        check("178: a claim lands on its row, named by the manuscript, the section and the reference as it cites it, and a "
              "claim note on the same row with the caret in the note",
              claim["go"] == {"screen": "trace", "doc": protocol, "key": claim["go"]["key"], "folder": str(seeds)}
              and claim["go"]["key"].startswith("vance2021~") and claim["where"] == "seed protocol.md · Background · Vance & Ito, 2021"
              and note["go"] == dict(note["go"], key=okafor["key"], field="note"), str([claim, note]))
        # the manuscripts in the project's order, which the day and time each was added sets, then the name
        lead = tr.docs(seeds)[0]["doc"]
        cites = next(r["key"] for r in tr.rows(seeds, lead)["rows"] if r["ref"] == "okafor2019" and r["kind"] == "claim")
        check("178: a reference lands at the first claim that cites it, one never cited at its own row, and a reference two "
              "manuscripts share is found once, at the first in the project's order",
              len(refs) == 1 and refs[0]["go"]["key"] == cites and refs[0]["go"]["doc"] == lead
              and never["go"]["key"] == "zeller2015", str([refs, never]))
        alone = ask("winter seed", "trace", folder=str(listing))
        check("178: a project with a reference list alone finds its references, each landing at its own row",
              [(r["kind"], r["go"]["doc"], r["go"]["key"]) for r in alone["results"]] == [("reference", "", "ober2018")],
              str(alone["results"]))

        # ── D. Everything
        every = every_app("seed")
        demo_there = bool(idiograph_routes.demo_workbooks())
        # and the thematic analysis demo after it while its workbooks are there (demos, 3 November 2026)
        ta_there = any(b.is_file() for b in idiograph_routes.demo_workbooks(server_mod.demo_ta_dir()))
        # and the longitudinal demo after that (lipabuild, 13 November 2026)
        lipa_there = any(b.is_file() for b in idiograph_routes.demo_workbooks(server_mod.demo_lipa_dir()))
        keys = [p["key"] for p in every["projects"]]
        demos = ((["distil:demo"] if demo_there else []) + (["distil:demo-ta"] if ta_there else [])
                 + (["distil:demo-lipa"] if lipa_there else []))
        check("178: Everything lists every project the home screen lists, Sift's, then Distil's with the demos last while "
              "their workbooks are there, then Trace's, the parts in a study's order with their kinds",
              [p["part"] for p in every["projects"]] == ["sift", "distil"] + ["distil"] * len(demos) + ["trace", "trace"]
              and keys[2:2 + len(demos)] == demos
              and every["parts"] == [["sift", list(sift_find.SIFT_KINDS)], ["distil", list(idiograph_find.KINDS)],
                                     ["trace", list(trace_find.TRACE_KINDS)]]
              and list(every["counts"]) == list(app_search.ALL_KINDS), str(every["projects"]))
        mixed = every_app("pond")
        parts = [r["part"] for r in mixed["results"]]
        check("178: with Everything each result names its project and its part, the parts in a study's order, Sift's first",
              parts and parts == sorted(parts, key=["sift", "distil", "trace"].index)
              and all(r["project"] for r in mixed["results"]) and mixed["results"][0]["project"] == "Pond review",
              str(parts[:6]))
        trace_key = next(p["key"] for p in every["projects"] if p["name"] == "Seed check")
        narrowed = every_app("seed", projects=[trace_key])
        own_all = {}
        for app in ("sift", "idiograph", "trace"):
            with support.as_app(app):
                own_all[app] = server_mod.api_search({"q": "seed", "scope": "all"})
        check("178: each app's own Everything holds its own part alone, its projects' results and counts its own",
              {app: [p[0] for p in got["parts"]] for app, got in own_all.items()}
              == {"sift": ["sift"], "idiograph": ["distil"], "trace": ["trace"]}
              and {p["part"] for p in own_all["trace"]["projects"]} == {"trace"}
              and set(own_all["sift"]["counts"]) <= set(sift_find.SIFT_KINDS), str({a: g.get("parts") for a, g in own_all.items()}))
        check("178: a project ticked shows its results alone, the projects counted with the other groups' ticks and the "
              "kinds with this one's",
              {r["project"] for r in narrowed["results"]} == {"Seed check"}
              and [p["count"] for p in narrowed["projects"]] == [p["count"] for p in every["projects"]]
              and sum(narrowed["counts"].values()) == narrowed["total"], str(narrowed["projects"]))
        refused = {}
        for name, call in (("sift without folder", {"q": "x", "scope": "sift"}), ("trace without folder", {"q": "x", "scope": "trace"}),
                           ("no scope", {"q": "x", "scope": "everything"})):
            try:
                searched(call)
            except Exception as exc:
                refused[name] = type(exc).__name__
        for name, call in (("sift elsewhere", {"q": "x", "scope": "sift", "folder": str(drafts)}),
                           ("trace elsewhere", {"q": "x", "scope": "trace", "folder": str(drafts)})):
            try:
                searched(call)
            except server_mod.OutsideRoot:
                refused[name] = "OutsideRoot"
            except Exception as exc:
                refused[name] = type(exc).__name__
        check("178: a Sift or Trace search with no folder, a scope that is none, and a folder in no list of projects are "
              "refused, nothing searched",
              refused == {"sift without folder": "WorkbookError", "trace without folder": "WorkbookError",
                          "no scope": "WorkbookError", "sift elsewhere": "WorkbookError", "trace elsewhere": "OutsideRoot"},
              str(refused))

        # ── E. read-only, held in memory against each file's time and size
        def snapshot():
            return {str(p.relative_to(base)): (p.stat().st_mtime_ns, p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())
                    for p in sorted(base.rglob("*")) if p.is_file()}

        before = snapshot()
        app_search.HELD.clear()
        calls = []
        real_s, real_m = sift_find.screening_items, trace_find.manuscript_items
        sift_find.screening_items = lambda folder: (calls.append("screening"), real_s(folder))[1]
        trace_find.manuscript_items = lambda folder, entry: (calls.append(entry["doc"]), real_m(folder, entry))[1]
        try:
            every_app("pond")
            once = list(calls)
            every_app("seed")
            again = calls[len(once):]
            log = sift.log_path(run)
            t = log.stat()
            os.utime(log, ns=(t.st_atime_ns, t.st_mtime_ns + 1_000_000_000))
            ask("pond", "sift", folder=str(review))
            touched = calls[len(once) + len(again):]
            os.utime(log, ns=(t.st_atime_ns, t.st_mtime_ns))
        finally:
            sift_find.screening_items, trace_find.manuscript_items = real_s, real_m
        check("178: a screening and each manuscript are read once and held against their files' time and size, the next "
              "search reading none, and a screening whose log changed read again",
              sorted(once) == sorted(["screening", protocol, second]) and again == [] and touched == ["screening"],
              f"{once} {again} {touched}")
        state_before = json.dumps(server_mod.STATE_MEMORY, sort_keys=True)
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
        threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
        got = {}
        try:
            serving = support.as_app("trace")
            serving.__enter__()
            req = urllib.request.Request(f"http://127.0.0.1:{httpd.server_address[1]}/api/search", method="POST",
                                         data=json.dumps({"q": "seed", "scope": "all"}).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                got = json.loads(r.read().decode("utf-8"))
        finally:
            serving.__exit__(None, None, None)
            httpd.shutdown()
            httpd.server_close()
        check("178: over HTTP Trace's Everything answers as the call does, and no search writes a file, adds one or touches "
              "the lists of projects",
              got.get("total") == own_all["trace"]["total"] and snapshot() == before
              and json.dumps(server_mod.STATE_MEMORY, sort_keys=True) == state_before
              and not re.search(r"\.write|json\.dump\(|save_json|open\([^)]*['\"]w|write_atomic|append\(folder", source),
              str(got.get("total")))
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = saved

    # ── F. the page: the keys, and what a result does to the screen it leaves
    guard = "if (e.target && e.target.closest && e.target.closest('.search-card')) return;\n  e.stopPropagation();"
    check("178: Sift's, Search strategy's and Trace's keys leave the card's own to it, Esc, the arrows and Enter, before "
          "they stop a key going further",
          guard in fn(sift_js, "sfKeyDown") and guard in fn(ssjs, "sfsKeyDown") and guard in fn(trjs, "trKeyDown"))
    leave = fn(sjs, "searchLeave")
    # Trace's leaving is its own, registered from trace.js (the family codebase's second build, 22 October 2026), and
    # Sift's from its screens' scripts through sift_settings.js (the third build)
    tr_leave = fn(trjs, "trSearchLeave")
    sset = support.text("apps/sift/static/sift_settings.js")
    check("178: a result on another part's screen leaves the screen in front as its own way out does, Sift's acts first, "
          "Search strategy's last change saved, Trace's note kept",
          "await new Promise((done) => sfLeave(done));" in fn(sift_js, "sfSearchLeave") and "await sfsFlush();" in fn(ssjs, "sfsSearchLeave")
          and "(here.screen === 'searches' ? sfsSearchLeave() : sfSearchLeave())" in sset and "searchLeave: siftSearchLeave" in sset
          and "familyApp(here.screen).searchLeave(here)" in leave and "searchLeave: trSearchLeave" in trjs
          and "await trLeaving();" in tr_leave and "$('trace').hidden = true;" in tr_leave)

    # ── G. in node: every screen's Search, its scopes, where a result is
    if not node:
        skip("178: Search in node", "node is not on this machine")
    else:
        esc_line = line_of(app, "const esc = ")
        code = "\n".join([
            "let MAC = true;", "const MOD = (e) => (MAC ? e.metaKey : e.ctrlKey);", esc_line,
            "const els = { work: { hidden: true }, themes: { hidden: true }, library: { hidden: false }, 'home-project': { hidden: true },"
            " 'home-pick': { hidden: false }, sift: { hidden: true }, 'sift-search': { hidden: true }, trace: { hidden: true }, search: { hidden: true } };",
            "const $ = (id) => els[id];", "let S = { data: null, home: '' };", "let TH = { path: '', mode: 'pets' };",
            "const SF = { folder: 'Pond review/runs/2026-10-01' };", "const SFS = { folder: 'Pond review' };", "const TR = { folder: 'Seed check' };",
            "let overlays = [];", "const document = { querySelectorAll: () => overlays };",
            "const anyOverlayOpen = () => false;", "let opened = 0;", "function openSearch() { opened += 1; return true; }",
            "function closeSearch() {}", line_of(sjs, "const searchOpen = "), line_of(sjs, "const searchShown = "),
            # Sift's and Trace's places for Search, registered from their scripts as the page registers them
            line_of(sift_js, "const sfSearchWhere = "), line_of(ssjs, "const sfsSearchWhere = "),
            line_of(sset, "const siftSearchWhere = "), line_of(trjs, "const trSearchWhere = "),
            "const FAMILY_APPS = { sift: { screen: 'sift', screens: ['sift', 'searches'], searchWhere: siftSearchWhere },"
            " trace: { screen: 'trace', searchWhere: trSearchWhere } };",
            line_of(sjs, "const searchCovered = "), whole(sjs, "searchScopes"), whole(sjs, "searchWhere"), whole(sjs, "searchKey"),
            "let SEARCH = { scope: 'all' };", whole(sjs, "searchWhereLine"),
        ]) + r"""
function press() {
  const e = { key: 'f', code: 'KeyF', metaKey: true, ctrlKey: false, shiftKey: false, altKey: false,
    defaultPrevented: false, preventDefault() { this.defaultPrevented = true; }, stopPropagation() {} };
  searchKey(e);
  return e.defaultPrevented;
}
const out = { where: {}, keys: {} };
out.where.home = searchWhere(); out.keys.home = press();
els.library.hidden = true;
for (const [id, name] of [['sift', 'sift'], ['sift-search', 'searches'], ['trace', 'trace']]) {
  els[id].hidden = false; out.where[name] = searchWhere(); out.keys[name] = press(); els[id].hidden = true;
}
els.trace.hidden = false; overlays = [{ hidden: false }]; out.keys.covered = press(); overlays = [{ hidden: true }];
out.keys.uncovered = press(); els.trace.hidden = true;
out.scopes = ['sift', 'searches', 'trace', 'home'].map((screen) => searchScopes({ screen }));
out.lines = [
  searchWhereLine({ kind: 'record', project: 'Pond review', where: 'R002 · Abstract', case: '' }),
  searchWhereLine({ kind: 'passage', project: 'Allotments', case: 'Ivo', where: 'Initial 03:55' }),
  searchWhereLine({ kind: 'question', project: 'Allotments', case: '', where: 'Allotments' }),
];
SEARCH.scope = 'sift'; out.lines.push(searchWhereLine({ kind: 'record', project: '', where: 'R002 · Abstract', case: '' }));
out.opened = opened;
console.log(JSON.stringify(out));
"""
        script = scratch / "search-178.js"
        script.write_text(code, encoding="utf-8")
        run_js = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        o = json.loads(run_js.stdout) if run_js.returncode == 0 and run_js.stdout.strip() else {}
        check("178: in node, the picker, Sift's screening, its Search strategy and Trace are each a screen Search knows, by "
              "its folder, and Cmd + F opens Search on each, the browser keeping its own under any card of the app's own",
              o.get("where") == {"home": {"screen": "home"}, "sift": {"screen": "sift", "folder": "Pond review/runs/2026-10-01"},
                                 "searches": {"screen": "searches", "folder": "Pond review"},
                                 "trace": {"screen": "trace", "folder": "Seed check"}}
              and o.get("keys") == {"home": True, "sift": True, "searches": True, "trace": True, "covered": False, "uncovered": True}
              and o.get("opened") == 5, run_js.stdout + run_js.stderr[:300])
        check("178: in node, This Sift project and Everything on Sift's two screens, This Trace project and Everything on "
              "Trace's, Everything alone on the picker",
              o.get("scopes") == [["sift", "all"], ["sift", "all"], ["trace", "all"], ["all"]], str(o.get("scopes")))
        check("178: in node, with Everything a result's place names its project first, then its case, the project's name "
              "said once, and in This Sift project the record's ID and part alone",
              o.get("lines") == ["Pond review · R002 · Abstract", "Allotments · Ivo · Initial 03:55", "Allotments", "R002 · Abstract"],
              str(o.get("lines")))

