from __future__ import annotations

import csv
import inspect
import json
import os
import re
import shutil
from pathlib import Path

from . import support
from .support import check, grip_js, refusal_of, skip


def test_sift_plan(scratch):
    print("\n123. Search strategy in one column from Adam's use, 12 October: Plan under one tag, Searches a row a "
          "database with how it runs and its search, Register saying what it does, Runs newest first with Trial or "
          "Registered search and Screen this run, New run under them, the steps named with their verbs, and a PDF "
          "carried by its paper from an earlier run")
    import subprocess
    import socket
    import server as server_mod
    import sift_routes
    import sift
    import sift_search as ss

    ssjs = support.text("apps/sift/static/sift_search.js")
    sift_src = support.text("apps/sift/static/sift.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    node = shutil.which("node")
    base = scratch / "sift-plan-123"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    build = fn(ssjs, "sfsBuild")

    # ── B. the plan's one tag, the version only with more than one, Register's words and its place
    check("123, updated 12 October, later (124): Open search_plan.md opens its file through the open op, reasons.csv "
          "never opened",
          "$('sfs-reg-open').onclick = () => sfsOpenFile('plan');" in ssjs
          and "sfsOpenFile('reasons')" not in ssjs
          and "await api('/api/sift-search', { op: 'open', folder: SFS.folder, file });" in fn(ssjs, "sfsOpenFile"))

    # ── C. the screen in node
    if not node:
        skip("123: the screen in node", "node is not installed")
    else:
        script = base / "plan-123.js"
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
const calls = [];
async function api(path, body) {
  calls.push([path, JSON.parse(JSON.stringify(body))]);
  if (body.op === 'screening') return { folder: `kiln-review/runs/${body.date}` };
  return {};
}
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
function siftOpen(folder) { calls.push(['siftOpen', folder]); }
function sfLeave(then) { then(); }
async function loadLibrary() {}
"""
        harness += "\n".join(["const SF_DB_COLOURS = " + sift_src.split("const SF_DB_COLOURS = ", 1)[1].split("};", 1)[0] + "};",
                              re.search(r"(?m)^const SF_DB_PALETTE = \d+;$", sift_src).group(0),
                              re.search(r"(?m)^const sfPickKey = .*$", sift_src).group(0),
                              "function sfDbKey(" + sift_src.split("function sfDbKey(", 1)[1].split("\n}", 1)[0] + "\n}",
                              re.search(r"(?m)^const sfDbPill = .*$", sift_src).group(0)]) + "\n"
        body = grip_js() + "\n" + support.table_js() + "\n" + ssjs.rsplit("\nsfsBoot();", 1)[0]
        run = r"""
(async () => {
const out = {};
SFS.catalog = { sources: ['psycinfo', 'pubmed', 'other'], names: { psycinfo: 'PsycInfo', pubmed: 'PubMed', other: 'Other database' },
  keyless: ['pubmed'], apis: ['pubmed'], scopes: [['tak', 'Title, abstract and keywords']], types: [], platformed: ['psycinfo'],
  platforms: [['ebsco', 'EBSCO']], sites: {}, platform_sites: { ebsco: 'https://search.ebscohost.com/' }, hosts: { ebsco: 'EBSCOhost' } };
SFS.folder = 'kiln-review';
SFS.today = '2026-10-12';
SFS.how = { pubmed: 'api', psycinfo: 'export' };
SFS.listed = [];
SFS.plan = { databases: ['psycinfo', 'pubmed'], others: {}, platforms: { psycinfo: 'ebsco' }, blocks: [], years: {}, types: [],
  reasons: { ta: [], ft: [] }, benchmark: [], benchmark_titles: {}, overrides: {} };
const strings = [
  { source: 'psycinfo', name: 'PsycInfo', platform: 'EBSCO', written: 'TI kiln*', query: 'TI kiln*', override: null, notes: [], limits: '' },
  { source: 'pubmed', name: 'PubMed', platform: '', written: 'kiln*[tiab]', query: 'kiln*[tiab]', override: null, notes: [], limits: '' }];
const tagOf = () => [$('sfs-state').textContent, $('sfs-state').className];
SFS.data = { strings, current: { version: 1, registered: null }, versions: [{ version: 1, registered: null }], problems: [], plan: SFS.plan };
sfsDrawVersion();
// Mark as registered where Register this plan stood, and Open search_plan.md shown once the file is there (124)
out.draft = { tag: tagOf(), versions: $('sfs-versions').hidden, regDraft: $('sfs-reg-draft').hidden, when: $('sfs-reg-when').hidden,
  next: $('sfs-reg-next').hidden, file: $('sfs-reg-open').hidden, button: $('sfs-mark').disabled };
SFS.data = Object.assign({}, SFS.data, { current: { version: 1, registered: '2026-10-12T09:00:00' },
  versions: [{ version: 1, registered: '2026-10-12T09:00:00' }], markdown: '# Search plan, version 1', plan_file: true });
sfsDrawVersion();
out.registered = { tag: tagOf(), when: $('sfs-reg-when').innerHTML, regDraft: $('sfs-reg-draft').hidden, next: $('sfs-reg-next').hidden,
  file: $('sfs-reg-open').hidden, line: $('sfs-reg-steps').hidden, open: $('sfs-reg-open').hidden, versions: $('sfs-versions').hidden };
SFS.data = Object.assign({}, SFS.data, { current: { version: 2, registered: null, reason: '' },
  versions: [{ version: 1, registered: '2026-10-12T09:00:00', reason: '', text: '# Search plan, version 1\n\nRegistered 12 October 2026.' },
    { version: 2, registered: null, reason: '' }], problems: ['Version 2 needs the reason for its changes.'] });
SFS.open.add('versions');
sfsDrawVersion();
out.second = { tag: tagOf(), versions: $('sfs-versions').hidden, list: $('sfs-version-list').innerHTML, why: $('sfs-why-line').hidden,
  problems: $('sfs-problems').innerHTML, button: $('sfs-mark').disabled, line: $('sfs-reg-steps').hidden,
  regDraft: $('sfs-reg-draft').hidden };
// the reasons from the review's own file, then the plan's own, one list of rows since 124
SFS.data.reasons_file = { reasons: [{ code: 'K1', meaning: 'Not about kilns' }], staged: false, said: '' };
sfsDrawReasons(true);
out.fileReasons = $('sfs-reasons').innerHTML;
SFS.data.reasons_file = null;
SFS.plan.reasons = [{ code: 'E1', meaning: 'Not about firing' }];
sfsDrawReasons(true);
out.ownReasons = $('sfs-reasons').innerHTML;
// Searches, a row for each database of the plan
sfsDrawStrings();
out.searches = $('sfs-strings').innerHTML;
// the runs, newest first as the server lists them, and New run
SFS.review = { opens: '2026-10-05', folder: 'kiln-review', searches: true, screening: 'kiln-review/runs/2026-10-05' };
// each run with its number in the order made, as the server sends it since 12 October, later (124)
SFS.runs = [
  { date: '2026-10-12-2', day: '2026-10-12', n: 2, number: 3, screening: false, records: 3, merged: 3, version: 2, draft: false, missed: [], benchmark: 0,
    decided: 0, rows: [{ source: 'psycinfo', name: 'PsycInfo', how: 'export', state: 'awaiting', note: 'awaiting the export' },
      { source: 'pubmed', name: 'PubMed', how: 'api', state: 'done', hits: 3, saved: 3, note: '' }] },
  { date: '2026-10-12', day: '2026-10-12', n: 1, number: 2, screening: true, records: 9, merged: 7, version: 1, draft: false, missed: [], benchmark: 2,
    decided: 0, rows: [] },
  { date: '2026-10-05', day: '2026-10-05', n: 1, number: 1, screening: true, records: 8, merged: 6, version: 1, draft: true, missed: ['10.5555/kiln.9'],
    benchmark: 2, decided: 3, rows: [] }];
SFS.data.current = { version: 2, registered: '2026-10-12T11:00:00' };
SFS.data.versions = [{ version: 1, registered: '2026-10-12T09:00:00' }, { version: 2, registered: '2026-10-12T11:00:00' }];
// version 2 registered, its reason given, so nothing stands in the way of a run (165 holds Start new run while something does)
SFS.data.problems = [];
sfsDrawRun();
out.runs = $('sfs-runs').innerHTML;
out.runsHidden = $('sfs-runs-table').hidden;
out.newWhat = $('sfs-new-what').textContent;
out.sources = $('sfs-sources').innerHTML;
out.follows = $('sfs-follows').innerHTML;
out.runButton = $('sfs-run').disabled;
SFS.data.current = { version: 3, registered: null };
sfsDrawRun();
out.trialWhat = $('sfs-new-what').textContent;
// a plan that names no database says nothing over the empty list (17 October, later)
const named = SFS.plan.databases;
SFS.plan.databases = [];
sfsDrawRun();
out.noneWhat = [$('sfs-new-what').textContent, $('sfs-new-what').hidden, $('sfs-sources').innerHTML];
SFS.plan.databases = named;
sfsDrawRun();
out.backWhat = [$('sfs-new-what').textContent, $('sfs-new-what').hidden];
// Make active opens that run in Screening, through the screening op, only when pressed
const pressed = [{ dataset: { date: '2026-10-12' }, onclick: null }];
const before = calls.length;
$('sfs-runs').querySelectorAll = (sel) => (sel === '.sfs-open-run' ? pressed : []);
sfsBindOpen($('sfs-runs'));
const quiet = calls.length === before;
await pressed[0].onclick();
out.opened = { quiet, calls: calls.slice(before), hidden: $('sift-search').hidden };
// Open search_plan.md, the one file the screen opens
await sfsOpenFile('plan');
out.files = calls.filter((c) => c[1] && c[1].op === 'open').map((c) => c[1]);
console.log(JSON.stringify(out));
})().catch((e) => { console.error(e && e.stack || e); process.exit(1); });
"""
        script.write_text(harness + body + "\n" + run, encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60, env=dict(os.environ, TZ="UTC"))
        o = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        why = (ran.stderr or ran.stdout)[:500]
        check("123, updated 12 October, later (124): in node, a plan of one version reads Draft and then Registered with its "
              "day, one tag and no version, Earlier versions hidden, Mark as registered while a draft, and once registered "
              "the day, Open search_plan.md, the steps gone and that the next edit starts a new draft",
              o.get("draft", {}).get("tag") == ["Draft", "sfs-tag sfs-state draft"] and o["draft"]["versions"] is True
              and o["draft"]["regDraft"] is False and o["draft"]["when"] is True and o["draft"]["next"] is True
              and o["draft"]["file"] is True and o["draft"]["button"] is False
              and o.get("registered", {}).get("tag") == ["Registered 12 October 2026", "sfs-tag sfs-state api"]
              and o["registered"]["when"] == "Registered on 12 October 2026." and o["registered"]["regDraft"] is True
              and o["registered"]["next"] is False and o["registered"]["file"] is False and o["registered"]["open"] is False
              and o["registered"]["line"] is True and o["registered"]["versions"] is True, why or str(o.get("registered")))
        check("123, updated 12 October, later (124): in node, with a second version the tag reads Version 2, draft, the "
              "first under Earlier versions once its button opens them, with its plan, the reason asked and Mark as "
              "registered held until it is given, the steps to register shown",
              o.get("second", {}).get("tag") == ["Version 2, draft", "sfs-tag sfs-state draft"] and o["second"]["versions"] is False
              and '<p class="sfs-ver-head">Version 1, registered 12 October 2026</p>' in o["second"]["list"]
              and "# Search plan, version 1" in o["second"]["list"] and o["second"]["why"] is False
              and o["second"]["problems"] == "<p>Version 2 needs the reason for its changes.</p>" and o["second"]["button"] is True
              and o["second"]["line"] is False and o["second"]["regDraft"] is False,
              why or str(o.get("second")))
        check("123, updated 12 October, later (124): in node, reasons from the review's reasons.csv are rows to edit, and a "
              "project with no such file edits the plan's own the same way",
              'value="K1" maxlength="12"' in o.get("fileReasons", "") and 'value="E1" maxlength="12"' in o.get("ownReasons", "")
              and "sfs-from-file" not in build
              and "Offered with No at title and abstract, where a reason is optional, and with Exclude at full text, where one is required." in build,
              why or str(o.get("fileReasons")))
        rows = {re.search(r'data-s="([a-z]+)"', r).group(1): r for r in o.get("searches", "").split('<div class="sfs-str"')[1:]}
        psy, pub = rows.get("psycinfo", ""), rows.get("pubmed", "")
        steps = [psy.find(w) for w in ("Copy the search", ">Open EBSCOhost</a> in a new tab", "Run the search there",
                                       "Export the records as RIS, CSV or BibTeX", "Drop the file here, or choose it")]
        check("123: in node, Searches has one row for each database of the plan, its name, how it runs, its cog, and its "
              "search beside it written from the plan, By export with its steps in order and By API with Copy, each with "
              "Edit manually",
              list(rows) == ["psycinfo", "pubmed"]
              and psy.index("sfs-str-how") < psy.index('<span class="sfs-str-name">PsycInfo on EBSCO</span><span class="sfs-tag">By export</span>')
              < psy.index('class="sfs-cog"') < psy.index("sfs-str-text") < psy.index('<pre class="sfs-q">TI kiln*</pre>')
              and all(i >= 0 for i in steps) and steps == sorted(steps) and ">Copy</button>" not in psy
              and '<span class="sfs-tag api">By API</span>' in pub and '<pre class="sfs-q">kiln*[tiab]</pre>' in pub
              and ">Copy</button>" in pub and "sfs-todo" not in pub and 'aria-label="PubMed\'s access"' in pub
              and all(">Edit manually</button>" in r for r in (psy, pub)), why or str(steps))
        run_rows = o.get("runs", "").split('<tr class="sfs-run"')[1:]
        name = lambda h: h.split('class="sfs-run-name">', 1)[1].split("</th>", 1)[0] if "sfs-run-name" in h else ""
        check("123, updated 12 October, later (124): in node, Search runs lists the runs newest first, a row each, by its "
              "number in the order made and its date, Trial or Registered search, the records found, those after "
              "duplicates and the benchmark papers found",
              [name(r) for r in run_rows] == ["Run 3, 12 October", "Run 2, 12 October", "Run 1, 5 October"] and o.get("runsHidden") is False
              and '<span class="sfs-tag api">Registered search</span>' in run_rows[1] and '<span class="sfs-tag draft">Trial</span>' in run_rows[2]
              and 'data-label="Records found">9</td><td class="sfs-num" data-label="After duplicates">7</td>' in run_rows[1]
              and 'data-label="Benchmark papers found"><span>2 of 2</span></td>' in run_rows[1]
              and '<span class="sfs-missed">1 of 2</span>' in run_rows[2], why or str([name(r) for r in run_rows]))
        check("123, updated 12 October, later (124): in node, the run Screening has open is marked Active, each other run "
              "with a screening has Make active, which opens it in Screening through the screening op only when pressed, "
              "and a run with none has neither",
              '<span class="sfs-tag sfs-open-tag">Active</span>' in run_rows[2] and "Make active" not in run_rows[2]
              and '<button type="button" class="ghost small sfs-open-run" data-date="2026-10-12">Make active</button>' in run_rows[1]
              and "Make active" not in run_rows[0] and "sfs-open-tag" not in run_rows[0]
              and o.get("opened", {}).get("quiet") is True
              and o["opened"]["calls"] == [["/api/sift-search", {"op": "screening", "folder": "kiln-review", "date": "2026-10-12"}],
                                           ["siftOpen", "kiln-review/runs/2026-10-12"]] and o["opened"]["hidden"] is True,
              why or str(o.get("opened")))
        check("123: in node, a run awaiting an export says which database it waits for and takes the drop on its own row, "
              "named for that run",
              '<div class="sfs-run-wait"><span>Waiting for the PsycInfo export</span><label class="sfs-drop" data-s="psycinfo" '
              'data-run="2026-10-12-2">' in run_rows[0] and "Waiting for the PubMed" not in run_rows[0], why or run_rows[0][:300])
        news = {re.search(r'data-s="([a-z]+)"', r).group(1): r for r in o.get("sources", "").split('<li class="sfs-src')[1:]}
        check("123, updated 12 October, later (124): in node, New run says what the next run is, the registered search or "
              "a trial, names each database it searches and how, before Start new run, and Keep the decisions from offers "
              "the runs with decisions by their names and No earlier run",
              o.get("newWhat") == "The registered search. It searches these databases:"
              and o.get("trialWhat") == "A trial, since the plan is not registered. It searches these databases:"
              and list(news) == ["psycinfo", "pubmed"] and '<span class="sfs-src-how">By export</span>' in news["psycinfo"]
              and '<span class="sfs-src-how">By API</span>' in news["pubmed"] and o.get("runButton") is False
              and o.get("follows") == '<option value="2026-10-05">Run 1, 5 October</option><option value="none">No earlier run</option>',
              why or str(o.get("follows")))
        check("123, 17 October, later: in node, New run says nothing while the plan names no database, its line hidden over "
              "the empty list, where it said It searches these databases: over nothing, and says it again once one is named",
              o.get("noneWhat") == ["", True, ""]
              and o.get("backWhat") == ["A trial, since the plan is not registered. It searches these databases:", False],
              why or str(o.get("noneWhat")))
        check("123, updated 12 October, later (124): in node, Open search_plan.md asks the open op for plan, and nothing "
              "asks for reasons",
              o.get("files") == [{"op": "open", "folder": "kiln-review", "file": "plan"}], why or str(o.get("files")))

    # ── D. the server: the open op, plan_file and each earlier version's plan
    kept_state = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.OPEN_FILE)
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"interviewer": "Adam"}), encoding="utf-8")
    review = base / "Kiln review"
    review.mkdir()
    opened = []
    try:
        server_mod.CONFIG_PATH = config_file
        server_mod.ROOT_OVERRIDE = str(base)
        server_mod.STATE_MEMORY = {"recent": []}
        server_mod.OPEN_FILE = lambda p: opened.append(Path(p))
        ss.new_plan(review, "Kiln review", "How is a firing lived?")
        ss.save(review, {"databases": ["psycinfo"], "blocks": [{"name": "Kilns", "terms": ["kiln*"]}]})
        sift_routes.api_sift_review({"op": "open", "folder": str(review)})
        first = sift_routes.api_sift_search({"op": "read", "folder": str(review)})
        no_plan = refusal_of(lambda: sift_routes.api_sift_search({"op": "open", "folder": str(review), "file": "plan"}))
        ss.register(review)
        (review / sift.REASONS_NAME).write_text("stage,code,meaning\nta,K1,Not about kilns\n", encoding="utf-8")
        ss.save(review, {"databases": ["psycinfo", "pubmed"], "blocks": [{"name": "Kilns", "terms": ["kiln*"]}]}, reason="PubMed added")
        listing = lambda: sorted((p.relative_to(review).as_posix(), p.stat().st_size, p.stat().st_mtime_ns)
                                 for p in review.rglob("*") if p.is_file())
        held = listing()
        got = sift_routes.api_sift_search({"op": "read", "folder": str(review)})
        # reasons.csv is edited on the screen and never opened since 12 October, later (124)
        a = refusal_of(lambda: sift_routes.api_sift_search({"op": "open", "folder": str(review), "file": "reasons"}))
        b = sift_routes.api_sift_search({"op": "open", "folder": str(review), "file": "plan"})
        other = refusal_of(lambda: sift_routes.api_sift_search({"op": "open", "folder": str(review), "file": "../config.json"}))
        check("123, updated 12 October, later (124): the open op opens search_plan.md of the review's folder in the "
              "computer's own app, refuses reasons.csv, any other file and one not there, and writes nothing",
              a == "The file is plan." and b == {"opened": "search_plan.md"}
              and [p.resolve() for p in opened] == [(review / "search_plan.md").resolve()]
              and other == "The file is plan."
              and no_plan == "There is no search_plan.md in the review's folder." and listing() == held
              and sift_routes.SEARCH_FILES == {"plan": "search_plan.md"}, str([a, b, other, no_plan]))
        heads = got["versions"]
        check("123: the read says whether search_plan.md is there, and each version before the newest carries its plan as "
              "search_plan.md writes it, the newest none",
              first["plan_file"] is False and got["plan_file"] is True and len(heads) == 2
              and heads[0]["text"].startswith("# Search plan, version 1") and "Registered " in heads[0]["text"]
              and "text" not in heads[1] and got["reasons_file"]["reasons"] == [{"code": "K1", "meaning": "Not about kilns"}],
              str([h.keys() for h in heads]))
        check("123: on a machine other than a Mac the file opens with the system's own opener, by a name the suite stands in "
              "for, and a Mac uses open",
              'subprocess.run(["open", str(target)]' in inspect.getsource(kept_state[3])
              and "xdg-open" in inspect.getsource(kept_state[3]) and "os.startfile(str(target))" in inspect.getsource(kept_state[3])
              and "OPEN_FILE = open_with_default" in inspect.getsource(server_mod))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.OPEN_FILE = kept_state

    # ── E. a PDF belongs to the paper: carried from an earlier run by DOI, else by title and year
    def screening(folder: Path, rows: list[tuple]) -> Path:
        """An invented run's screening on kiln firings, each row rec_id, title, year and DOI."""
        folder.mkdir(parents=True, exist_ok=True)
        with open(folder / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["rec_id", "title", "authors", "year", "doi", "abstract"])
            for rec, title, year, doi in rows:
                w.writerow([rec, title, "Potter, Q.", year, doi, f"The firing of {title.lower()}."])
        return folder

    def pdf(folder: Path, rec: str, words: str) -> bytes:
        data = f"%PDF-1.4\n% {words}\n%%EOF\n".encode("utf-8")
        (folder / sift.PDF_DIR).mkdir(exist_ok=True)
        (folder / sift.PDF_DIR / f"{rec}.pdf").write_bytes(data)
        return data

    kilns = base / "Kiln carry"
    runs = kilns / ss.RUNS_DIR
    older = screening(runs / "2026-03-01", [("R001", "Smoke over the kiln", "2019", "10.5555/KILN.1"),
                                            ("R002", "Glaze and the long night", "2020", ""),
                                            ("R003", "Ash on the shelf", "2021", "10.5555/kiln.3"),
                                            ("R004", "Two kilns, one firing", "2022", "10.5555/kiln.4a"),
                                            ("R005", "Two kilns, one firing", "2022", "10.5555/kiln.4b"),
                                            ("R006", "Cones that bend", "2018", "10.5555/kiln.6")])
    by_doi = pdf(older, "R001", "smoke")
    by_title = pdf(older, "R002", "glaze")
    pdf(older, "R003", "ash, the older run's")
    pdf(older, "R004", "two kilns a")
    pdf(older, "R005", "two kilns b")
    newer = screening(runs / "2026-03-08", [("R001", "Ash on the shelf", "2021", "10.5555/kiln.3"),
                                            ("R002", "Smoke over the kiln", "2019", "https://doi.org/10.5555/kiln.1"),
                                            ("R003", "Glaze and the long night.", "2020", ""),
                                            ("R004", "Two kilns, one firing", "2022", ""),
                                            ("R005", "Cones that bend", "2018", "10.5555/kiln.6"),
                                            ("R/6", "Smoke over the kiln", "2019", "10.5555/kiln.1")])
    own = pdf(newer, "R001", "ash, his own in the newer run")
    first_run = screening(runs / "2026-02-01", [("R001", "Smoke over the kiln", "2019", "10.5555/kiln.1")])
    alone = screening(base / "Kiln alone", [("R001", "Smoke over the kiln", "2019", "10.5555/kiln.1")])
    took = sift.gather_pdfs(newer)
    got = lambda folder, rec: (folder / sift.PDF_DIR / f"{rec}.pdf").read_bytes() if (folder / sift.PDF_DIR / f"{rec}.pdf").is_file() else None
    found = sift.found_pdfs(newer)
    check("123: a run's record takes the PDF an earlier run holds for its paper by DOI, its case and its address set aside, "
          "and a record with no DOI by its title and year, each a plain copy of the bytes",
          took == 2 and got(newer, "R002") == by_doi and got(newer, "R003") == by_title
          and not (newer / sift.PDF_DIR / "R002.pdf").is_symlink() and os.stat(newer / sift.PDF_DIR / "R002.pdf").st_nlink == 1
          and found.get("R002.pdf", {}).get("from") == "2026-03-01/R001.pdf" and found.get("R003.pdf", {}).get("size") == len(by_title),
          str(found))
    check("123: a PDF already there is kept, a title and year matching two papers in a run takes nothing, a record whose "
          "earlier run holds no PDF takes none, a rec_id that cannot name a file takes none, and nothing lands outside pdfs/",
          got(newer, "R001") == own and got(newer, "R004") is None and got(newer, "R005") is None
          and sorted(p.name for p in (newer / sift.PDF_DIR).iterdir()) == [".found.json", "R001.pdf", "R002.pdf", "R003.pdf"]
          # the screening's lock, as every act takes it, taken once there is a PDF to copy
          and sorted(p.name for p in newer.iterdir()) == sorted([sift.CSV_NAME, sift.PDF_DIR, sift.LOCK_NAME]),
          str(sorted(p.name for p in newer.rglob("*"))))
    check("123: only earlier runs give, so a run made before takes nothing from a later one, and a screening that is no "
          "run's takes nothing",
          sift.gather_pdfs(first_run) == 0 and not (first_run / sift.PDF_DIR).exists() and sift.gather_pdfs(alone) == 0
          and sorted(p.name for p in first_run.iterdir()) == [sift.CSV_NAME] == sorted(p.name for p in alone.iterdir())
          and [p.name for p in sift.earlier_runs(newer)] == ["2026-03-01"] and sift.earlier_runs(alone) == [])
    check("123: a PDF found in an earlier run is no work on the screening: begun says nothing of it, a PDF of his own "
          "still counts, and one he replaces is his",
          sift.own_pdfs(newer) == {"R001.pdf": len(own)} and ss.begun(newer) == "PDFs"
          and (lambda: ((newer / sift.PDF_DIR / "R001.pdf").unlink(), ss.begun(newer))[1])() == ""
          and sift.save_pdf(newer, "R002", b"%PDF-1.4\n% his own copy\n", replace=True)["saved"] is True
          and "R002.pdf" not in sift.found_pdfs(newer) and ss.begun(newer) == "PDFs")
    # a PDF added to the older run later reaches the newer one when Screening opens it
    kept_state = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH = config_file
        server_mod.ROOT_OVERRIDE = str(base)
        server_mod.STATE_MEMORY = {"recent": []}
        ss.new_plan(kilns, "Kiln carry")
        sift_routes.api_sift_review({"op": "open", "folder": str(kilns)})
        cones = pdf(older, "R006", "cones, added later")
        before = got(newer, "R005")
        read = sift_routes.api_sift({"op": "read", "folder": str(newer)})
        pdf_seen = next((r for r in read.get("records", []) if r.get("rec_id") == "R005"), {}).get("pdf")
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept_state
    check("123: a PDF added to the older run later reaches the newer run when Screening opens it, before the screen is "
          "drawn",
          before is None and got(newer, "R005") == cones and sift.found_pdfs(newer).get("R005.pdf", {}).get("from") == "2026-03-01/R006.pdf"
          and pdf_seen is True
          and inspect.getsource(sift_routes.api_sift).index("sift_mod.gather_pdfs(folder)")
          < inspect.getsource(sift_routes.api_sift).index("sift_mod.refresh_prisma(folder)"), str(pdf_seen))

    # a run made by a dropped export takes the PDFs as its screening is written, and a second drop writes it afresh
    plan_dir = base / "Kiln drops"
    (plan_dir / ss.RUNS_DIR).mkdir(parents=True)
    shutil.copytree(older, plan_dir / ss.RUNS_DIR / "2026-03-01")
    ss.save(plan_dir, {"databases": ["psycinfo"], "blocks": [{"name": "Kilns", "terms": ["kiln*"]}]})
    ris = ("TY  - JOUR\nTI  - Smoke over the kiln\nAU  - Potter, Q.\nPY  - 2019\nDO  - 10.5555/kiln.1\nER  - \n"
           "TY  - JOUR\nTI  - Glaze and the long night\nAU  - Potter, Q.\nPY  - 2020\nER  - \n")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        closed = sock.getsockname()[1]
    ctx = ss.Context(base={"openalex": f"http://127.0.0.1:{closed}/works"}, pause=lambda s: None)
    kept_runner, kept_env = ss.RUNNER, os.environ.pop(ss.STUB_ENV, None)
    ss.RUNNER = lambda argv, **_: subprocess.CompletedProcess(argv, 44, "", "")
    try:
        dropped = ss.take_export(plan_dir, "psycinfo", ris.encode("utf-8"), "kilns.ris", day="2026-03-15", ctx=ctx)
        run_dir = plan_dir / ss.RUNS_DIR / "2026-03-15"
        ids = {r["title"]: r["rec_id"] for r in csv.DictReader(open(run_dir / sift.CSV_NAME, encoding="utf-8"))}
        first_pdfs = sorted(p.name for p in (run_dir / sift.PDF_DIR).iterdir()) if (run_dir / sift.PDF_DIR).is_dir() else []
        again = ss.take_export(plan_dir, "psycinfo", ris.encode("utf-8"), "kilns again.ris", day="2026-03-15", ctx=ctx)
        second_pdfs = sorted(p.name for p in (run_dir / sift.PDF_DIR).iterdir())
    finally:
        ss.RUNNER = kept_runner
        if kept_env is not None:
            os.environ[ss.STUB_ENV] = kept_env
    smoke, glaze = ids.get("Smoke over the kiln", "?"), ids.get("Glaze and the long night", "?")
    check("123: a run takes the PDFs of its papers from the earlier runs as its screening is written, which leaves it "
          "unbegun, so a second export dropped on it writes it afresh and takes them again, the run's other files as before",
          dropped["taken"]["records"] == 2 and again["taken"]["records"] == 2
          and first_pdfs == second_pdfs == sorted([".found.json", f"{smoke}.pdf", f"{glaze}.pdf"])
          and got(run_dir, smoke) == by_doi and got(run_dir, glaze) == by_title and ss.begun(run_dir) == ""
          and sorted(p.name for p in run_dir.iterdir() if p.is_file()) == sorted(["log.csv", "psycinfo.ris", "raw_psycinfo.json",
                                                                                     "run.json", "screening.csv", sift.LOCK_NAME]),
          str(first_pdfs) + str(sorted(p.name for p in run_dir.iterdir())))
    check("123: a run calls the sweep once its screening is written, after taking away what it found before, since the "
          "records are numbered afresh",
          inspect.getsource(ss.assemble).index("sift.clear_found(run_dir)") < inspect.getsource(ss.assemble).index("sift.gather_pdfs(run_dir")
          and "if sift.own_pdfs(run_dir):" in inspect.getsource(ss.begun)
          and "sift.own_pdfs(run_dir) != (carried.get(\"pdfs\") or {})" in inspect.getsource(ss.changed_since)
          and "forget_found(folder, target.name)" in inspect.getsource(sift.save_pdf))
