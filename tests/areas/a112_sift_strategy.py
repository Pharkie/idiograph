from __future__ import annotations

import inspect
import json
import os
import re
import shutil

from . import support
from .support import check, grip_js, skip


def test_sift_strategy(scratch):
    print("\n112. Sift's Search strategy: the screen says what it is and goes in order, Years and the benchmark "
          "explained, each database's cog, Add database, Edit manually, Register said plainly, and the runs a part "
          "of their own that never put an empty screening in place of the one he works in")
    import subprocess
    import server as server_mod
    import sift_routes
    import sift_search as ss

    sjs = support.text("apps/sift/static/sift_search.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    node = shutil.which("node")
    base = scratch / "sift-strategy"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)

    # ── B. the plan: databases he names, the benchmark's titles, the strings edited manually
    plan = ss.clean_plan({
        "databases": ["other2", "scopus", "other", "other3", "nowhere"], "others": {"other": "Garden Index", "other2": "Pond Index"},
        "blocks": [{"name": "Hedges", "terms": ["hedgerow*", "\"laid hedge\""], "scopes": {"other2": "fulltext", "nowhere": "fulltext"}}],
        "benchmark": "10.5555/HEDGE.1 Hedges as homes, for wrens\nhttps://doi.org/10.5555/hedge.2, 10.5555/hedge.3\n\n10.5555/hedge.1",
        "overrides": {"other2": {"query": "hedge*", "reason": ""}}})
    strings = {s["source"]: s for s in ss.strings(plan)}
    check("112: a plan names several databases of its own, each by its name and in the order added, after Sift's own",
          plan["databases"] == ["scopus", "other", "other2", "other3"] and plan["others"] == {"other": "Garden Index", "other2": "Pond Index"}
          and strings["other"]["name"] == "Garden Index" and strings["other2"]["name"] == "Pond Index"
          and strings["other"]["query"] == '(hedgerow* OR "laid hedge")' and strings["other2"]["query"] == "hedge*"
          and plan["blocks"][0]["scopes"] == {"other2": "fulltext"}
          and "Name the other database." in ss.problems(plan) and "Pond Index's edited string needs its reason." in ss.problems(plan)
          and ss.clean_plan({"databases": ["other"], "other_name": "Old Index"})["others"] == {"other": "Old Index"}, str(plan["databases"]))
    check("112: the benchmark takes a title typed after a DOI, several DOIs on a line, and each DOI once",
          plan["benchmark"] == ["10.5555/hedge.1", "10.5555/hedge.2", "10.5555/hedge.3"]
          and plan["benchmark_titles"] == {"10.5555/hedge.1": "Hedges as homes, for wrens"}
          and ss.clean_plan(dict(plan, benchmark=plan["benchmark"]))["benchmark_titles"] == plan["benchmark_titles"]
          and ss.clean_plan(dict(plan, benchmark=["10.5555/hedge.1"], benchmark_titles={}))["benchmark_titles"] == {},
          str(plan["benchmark_titles"]))
    review = base / "hedge-review"
    review.mkdir()
    first = {"databases": ["psycinfo", "other", "other2"], "others": {"other": "Garden Index", "other2": "Pond Index"},
             "blocks": [{"name": "Hedges", "terms": ["hedgerow*"]}],
             "benchmark": ["10.5555/hedge.1 Hedges as homes", "10.5555/hedge.9"]}
    ss.save(review, first)
    done = ss.register(review)
    check("112: Register's search_plan.md names each database by its name and each benchmark DOI with its title, and "
          "says Edited manually where a string was",
          "PsycInfo (by export), Garden Index (by export), Pond Index (by export)." in done["markdown"]
          and "A run must find 10.5555/hedge.1 (Hedges as homes), 10.5555/hedge.9." in done["markdown"]
          and "Edited manually: Kept short." in ss.markdown({"versions": []}, {"version": 1, "registered": None, "plan": dict(
              first, overrides={"psycinfo": {"query": "TI hedge*", "reason": "Kept short"}})}), done["markdown"][:300])

    # every key the runs and the route ask for is read from the smoke's keychain in memory, never the login
    # keychain, and no request is made, every database here being searched by export
    kept_env = os.environ.get(ss.STUB_ENV)
    os.environ[ss.STUB_ENV] = "http://127.0.0.1:9"
    try:
        # ── C. the runs: one that brings no records makes no screening, and the screening before it stays the one opened
        ris = lambda *recs: "".join(f"TY  - JOUR\nTI  - {t}\nPY  - {y}\nDO  - {d}\nAB  - An invented abstract on hedges.\nER  - \n\n"
                                    for t, y, d in recs).encode("utf-8")
        ctx = lambda: ss.Context(base={}, pause=lambda s: None)
        d1, d2, d3 = "2026-07-01", "2026-07-08", "2026-07-15"
        ss.take_export(review, "psycinfo", ris(("Wrens in a laid hedge", "2019", "10.5555/hedge.9"),
                                              ("Hedges as homes", "2018", "10.5555/hedge.1")), "p.ris", day=d1, ctx=ctx())
        one = ss.run(review, day=d1, ctx=ctx())
        empty = ss.run(review, day=d2, ctx=ctx())
        shown = sift_routes.newest_screening(review)
        titles = ss.benchmark_titles(review)
        check("112: a run that brings no records writes no screening, says no records, and Screening still opens the run before",
              one["merged"] == 2 and (review / "runs" / d1 / "screening.csv").is_file()
              and not (review / "runs" / d2 / "screening.csv").exists() and (review / "runs" / d2 / "log.csv").is_file()
              and empty["records"] == 0 and empty["screening"] is False and shown is not None and shown.name == d1
              and [r["date"] for r in ss.runs(review)] == [d2, d1], str(empty)[:200])
        check("112: each benchmark DOI's title comes from the plan, else from a run's records",
              titles == {"10.5555/hedge.1": "Hedges as homes", "10.5555/hedge.9": "Wrens in a laid hedge"}
              and ss.state(review, with_runs=True)["titles"] == titles, str(titles))
        following = ss.run(review, day=d3, ctx=ctx(), follows=d1)
        meta = json.loads((review / "runs" / d3 / "run.json").read_text(encoding="utf-8"))
        waited = (not (review / "runs" / d3 / "screening.csv").exists(), meta.get("follows"), sift_routes.newest_screening(review).name)
        taken = ss.take_export(review, "other2", ris(("Hedges in winter", "2021", "10.5555/hedge.5")), "pond.ris", day=d3, ctx=ctx())
        check("112: a run following an earlier one that brings no records carries nothing yet, and an export dropped later "
              "carries the earlier screening into a screening of its own, which is then the newest",
              following["records"] == 0 and waited == (True, {"date": d1}, d1)
              and taken["screening"] is True and taken["follows"]["carried"] == 2 and taken["follows"]["new"] == 1
              and sift_routes.newest_screening(review).name == d3 and ss.known("other2") and not ss.known("other21"),
              str(waited))

        # ── D. the route: the list written at once, the catalogue's sites, the titles after a run
        kept = server_mod.CONFIG_PATH
        config_file = base / "config.json"
        config_file.write_text(json.dumps(dict(server_mod.defaults(), interviewer="Tester", databases=[{"source": "pubmed", "how": "api"}])),
                               encoding="utf-8")
        try:
            server_mod.CONFIG_PATH = config_file
            wrote = sift_routes.api_databases({"op": "save", "rows": [
                {"source": "pubmed", "how": "api"}, {"source": "psycinfo", "platform": "ovid", "how": "api"},
                {"source": "other", "name": "  Garden   Index "}, {"source": "other", "name": "garden index"}, {"source": "nowhere"}]})
            read = sift_routes.api_databases({"op": "read"})
            on_disk = json.loads(config_file.read_text(encoding="utf-8"))
        finally:
            server_mod.CONFIG_PATH = kept
        want_rows = [{"source": "pubmed", "how": "api"}, {"source": "psycinfo", "platform": "ovid", "how": "export"},
                     {"source": "other", "name": "Garden Index", "how": "export"}]
        check("112: the list a cog or Add database changes is written at once, cleaned as Settings cleans it, the rest of the "
              "settings left as they were, and Settings reads the same list",
              wrote == {"rows": want_rows} and read["rows"] == want_rows and on_disk["databases"] == want_rows
              and on_disk["interviewer"] == "Tester" and "save" in sift_routes.DATABASE_OPS, str(wrote))
        cat = sift_routes.search_catalog()
        src = inspect.getsource(sift_routes.api_sift_search)
        check("112: the catalogue gives each database's own search page and each platform's, and the screen hears the titles "
              "with the runs",
              set(cat["sites"]) | set(ss.PLATFORMED) | {"other"} == set(ss.SOURCES)
              and all(u.startswith("https://") for u in list(cat["sites"].values()) + list(cat["platform_sites"].values()))
              and cat["hosts"]["ebsco"] == "EBSCOhost" and '"titles": search_mod.benchmark_titles(folder) if done else None' in src
              and "titles=search_mod.benchmark_titles(folder)" in src)
    finally:
        os.environ.pop(ss.STUB_ENV, None)
        if kept_env is not None:
            os.environ[ss.STUB_ENV] = kept_env

    # ── E. the screen in node: the cog, Add database by button and by Enter, Remove, the strings, the runs
    if not node:
        skip("112: the screen's parts in node", "node is not installed")
    else:
        catalog = json.dumps(cat)
        script = base / "strategy-112.js"
        harness = r"""
const els = {};
const mk = (id) => ({ id, setAttribute(k, v) { (this.attrs = this.attrs || {})[k] = v; }, innerHTML: '', value: '', hidden: false, textContent: '', disabled: false, title: '', dataset: {},
  onclick: null, focus() { this.focused = true; }, click() { return this.onclick ? this.onclick() : undefined; },
  querySelectorAll: () => [], querySelector: () => null, matches: (sel) => sel.split(',').some((x) => x.trim() === '#' + id),
  closest: () => null, scrollIntoView() {} });
const $ = (id) => els[id] || (els[id] = mk(id));
$('settings').hidden = true;
$('feedback').hidden = true;
$('sfs-ask').hidden = true;
$('sfs-mark-card').hidden = true;
const calls = [];
const said = [];
let listed = [{ source: 'pubmed', how: 'api' }, { source: 'psycinfo', platform: 'ebsco', how: 'export' }];
async function api(path, body) {
  calls.push([path, JSON.parse(JSON.stringify(body))]);
  if (path === '/api/databases' && body.op === 'save') { listed = body.rows.map((r) => Object.assign({}, r)); return { rows: listed }; }
  if (path === '/api/sift-search' && body.op === 'read') return { how: { pubmed: 'api', psycinfo: 'export' }, listed };
  if (path === '/api/sift-search' && body.op === 'save') return {};
  return {};
}
const say = (m) => said.push(m);
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;
const grow = () => {};
const needsRestart = () => false;
const RESTART_LINE = 'Restart the server to finish this update.';
const document = { activeElement: null, querySelectorAll: () => [], createElement: () => mk('made'), body: { insertBefore() {} } };
const window = { addEventListener() {}, scrollTo() {} };
const localStorage = { getItem: () => null, setItem() {} };
function siftOpen() { calls.push(['siftOpen']); }
function sfLeave(then) { then(); }
async function loadLibrary() {}
const settle = () => new Promise((r) => setTimeout(r, 30));
"""
        # the runs' rows name each database as sift.js's pill in its colour (12 October), so the harness takes that part
        sift_src = support.text("apps/sift/static/sift.js")
        harness += "\n".join(["const SF_DB_COLOURS = " + sift_src.split("const SF_DB_COLOURS = ", 1)[1].split("};", 1)[0] + "};",
                              re.search(r"(?m)^const SF_DB_PALETTE = \d+;$", sift_src).group(0),
                              re.search(r"(?m)^const sfPickKey = .*$", sift_src).group(0),
                              "function sfDbKey(" + sift_src.split("function sfDbKey(", 1)[1].split("\n}", 1)[0] + "\n}",
                              re.search(r"(?m)^const sfDbPill = .*$", sift_src).group(0)]) + "\n"
        body = grip_js() + "\n" + support.table_js() + "\n" + sjs.rsplit("\nsfsBoot();", 1)[0]
        run = r"""
(async () => {
  SFS.catalog = CATALOG;
  SFS.folder = 'hedge-review';
  SFS.listed = listed;
  SFS.how = { pubmed: 'api', psycinfo: 'export' };
  SFS.plan = { databases: ['psycinfo', 'pubmed'], others: {}, platforms: { psycinfo: 'ebsco' }, blocks: [{ name: 'Hedges', terms: ['hedgerow*'], scope: 'tak', scopes: {} }],
    years: { from: null, to: null }, types: [], benchmark: [], benchmark_titles: {}, overrides: {} };
  SFS.data = { strings: [], current: { version: 1, registered: null }, problems: [], versions: [], plan: SFS.plan };
  SFS.runs = [];
  $('sfs-db-go').onclick = sfsAddDb;
  const out = {};
  // Add database by Enter, by its button, a name Sift knows, and a name already there
  $('sfs-db-name').value = 'Garden Index';
  sfsKeyDown({ key: 'Enter', target: $('sfs-db-name'), stopPropagation() {}, preventDefault() {} });
  await settle();
  $('sfs-db-name').value = 'Pond Index';
  await $('sfs-db-go').click();
  await settle();
  $('sfs-db-name').value = 'embase';
  await $('sfs-db-go').click();
  await settle();
  $('sfs-db-name').value = 'garden index';
  await $('sfs-db-go').click();
  await settle();
  out.added = { databases: SFS.plan.databases.slice(), others: Object.assign({}, SFS.plan.others),
    listed: listed.map((r) => r.name || r.source), field: $('sfs-db-name').value, said: said.slice() };
  const garden = sfsRows().find((r) => r.named && r.name === 'Garden Index');
  await sfsRemoveNamed(garden);
  await settle();
  out.removed = { databases: SFS.plan.databases.slice(), others: Object.assign({}, SFS.plan.others), listed: listed.map((r) => r.name || r.source) };
  // Enter in a key field saves the key through its own Save
  let pressed = 0;
  const save = { click() { pressed += 1; } };
  sfsKeyDown({ key: 'Enter', target: { id: 'k', matches: () => true, parentElement: { querySelector: () => save } }, stopPropagation() {}, preventDefault() {} });
  out.keyEnter = pressed;
  // the cog: its access as Settings draws it, and a platform changed there goes to the list and the plan
  SFS.acc = { saved: { ELSEVIER_API_KEY: true }, catalog: SFS.catalog, said: {} };
  listed.push({ source: 'scopus', how: 'api' });
  SFS.listed = listed;
  out.scopus = sfsAccHtml('scopus');
  out.psycinfo = sfsAccHtml('psycinfo');
  const plat = { value: 'ovid', onchange: null };
  const el = { querySelector: (sel) => (sel === '.dbs-plat' ? plat : null), querySelectorAll: () => [] };
  sfsBindAcc(el, 'psycinfo');
  await plat.onchange();
  await settle();
  const saves = calls.filter(([p, b]) => p === '/api/databases' && b.op === 'save');
  out.cog = { platform: SFS.plan.platforms.psycinfo, row: saves[saves.length - 1][1].rows.find((r) => r.source === 'psycinfo') };
  out.dbItem = sfsDbItem(sfsRows().find((r) => r.s === 'scopus'));
  // the strings, Edit manually and Revert to automatic, in the order the databases stand
  SFS.data.strings = [
    { source: 'psycinfo', name: 'PsycInfo', platform: 'Ovid', written: 'a', query: 'b', override: { query: 'b', reason: 'Kept short' }, notes: [], limits: '' },
    { source: 'pubmed', name: 'PubMed', platform: '', written: 'c', query: 'c', override: null, notes: [], limits: '' }];
  sfsDrawStrings();
  out.strings = $('sfs-strings').innerHTML;
  // updated 12 October (123): the cog on a database's row under Searches, its access opened under its name
  SFS.accOpen = 'pubmed';
  sfsDrawStrings();
  out.cogOpen = $('sfs-strings').innerHTML;
  SFS.accOpen = null;
  // each database's row under Searches says how it runs, an export's steps in order, and New run lists each
  SFS.plan.databases = ['psycinfo', 'pubmed', 'scholar', 'other2'];
  SFS.plan.platforms = { psycinfo: 'ebsco' };
  SFS.plan.others = { other2: 'Pond Index' };
  SFS.how = { pubmed: 'api', psycinfo: 'export', scholar: 'export' };
  SFS.today = '2026-10-09';
  SFS.data.current = { version: 2, registered: null };
  SFS.data.strings = ['psycinfo', 'pubmed', 'scholar', 'other2'].map((s) => ({ source: s, name: sfsName(s), platform: '',
    written: 'q', query: 'q', override: null, notes: [], limits: '' }));
  sfsDrawStrings();
  out.searchRows = $('sfs-strings').innerHTML;
  sfsDrawRun();
  out.sources = $('sfs-sources').innerHTML;
  out.newWhat = $('sfs-new-what').textContent;
  // a run that brought no records, and the run Screening has open
  SFS.titles = { '10.5555/hedge.9': 'Wrens in a laid hedge' };
  SFS.runs = [{ date: '2026-10-09', screening: false, records: 0, merged: 0, version: 2, draft: true, missed: [], benchmark: 2, rows: [] },
    { date: '2026-10-01', screening: true, records: 5, merged: 4, filled: 0, version: 1, missed: ['10.5555/hedge.9'], benchmark: 2, rows: [] }];
  out.none = sfsRunRow(SFS.runs[0]);
  // a run's Details opens with its button since 12 October, later (124)
  SFS.open.add('run:2026-10-01');
  out.before = sfsRunRow(SFS.runs[1]);
  out.registerLine = typeof sfsRegisterLine;
  SFS.data = Object.assign({}, SFS.data, { current: { version: 1, registered: '2026-10-01T10:00:00' }, versions: [{ version: 1, registered: '2026-10-01T10:00:00' }], problems: [] });
  sfsDrawVersion();
  out.version = [$('sfs-state').textContent, $('sfs-reg-when').innerHTML, $('sfs-reg-draft').hidden, $('sfs-reg-next').hidden];
  SFS.plan.benchmark = ['10.5555/hedge.1', '10.5555/hedge.9'];
  SFS.plan.benchmark_titles = { '10.5555/hedge.1': 'Hedges as homes' };
  SFS.titles = { '10.5555/hedge.1': 'Hedges as homes', '10.5555/hedge.9': 'Wrens in a laid hedge' };
  sfsDrawBench(true);
  out.bench = [$('sfs-bench-rows').innerHTML, $('sfs-bench-rows').hidden];
  out.opened = calls.filter((c) => c[0] === 'siftOpen').length;
  console.log(JSON.stringify(out));
})().catch((e) => { console.error(e && e.stack || e); process.exit(1); });
"""
        script.write_text(harness + body + "\nconst CATALOG = " + catalog + ";\n" + run, encoding="utf-8")
        # the days as a line says them, read in one zone wherever the suite runs
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60, env=dict(os.environ, TZ="UTC"))
        if ran.returncode != 0:
            check("112: the screen's parts run in node", False, ran.stderr.strip()[:500])
        else:
            o = json.loads(ran.stdout)
            check("112: in node, Add database adds by Enter and by its button, several to his list and the plan, a name "
                  "Sift knows its own row, a name there already once, the field emptied for the next",
                  o["added"]["databases"] == ["psycinfo", "pubmed", "embase", "other", "other2"]
                  and o["added"]["others"] == {"other": "Garden Index", "other2": "Pond Index"}
                  and o["added"]["listed"] == ["pubmed", "psycinfo", "Garden Index", "Pond Index", "embase"]
                  and o["added"]["field"] == "" and o["added"]["said"] == ["garden index is in the list already."], str(o["added"]))
            check("112: in node, Remove takes a database he named out of his list and out of the plan, the others staying",
                  o["removed"]["databases"] == ["psycinfo", "pubmed", "embase", "other2"] and o["removed"]["others"] == {"other2": "Pond Index"}
                  and o["removed"]["listed"] == ["pubmed", "psycinfo", "Pond Index", "embase"] and o["keyEnter"] == 1, str(o["removed"]))
            check("112, updated 12 October (123): in node, a database's cog, on its row under Searches and no longer in the "
                  "plan's list, opens its own access in place, By API or By export, its keys Saved or Not set with Save and "
                  "Remove, and Check, PsycInfo its platform, and a platform chosen goes to his list and the plan",
                  'class="sfs-cog"' not in o["dbItem"] and 'aria-label="PubMed\'s access"' in o["cogOpen"]
                  and 'class="sfs-acc"' in o["cogOpen"] and 'aria-expanded="true"' in o["cogOpen"]
                  and "Searched <select class=\"dbs-how\"" in o["scopus"] and '<option value="api" selected>By API</option>' in o["scopus"]
                  and 'placeholder="Saved"' in o["scopus"] and 'placeholder="Not set"' in o["scopus"]
                  and "Institution token, optional" in o["scopus"] and ">Check</button>" in o["scopus"] and ">Remove</button>" in o["scopus"]
                  and "Platform <select class=\"dbs-plat\"" in o["psycinfo"] and "Platform" not in o["scopus"]
                  and o["cog"] == {"platform": "ovid", "row": {"source": "psycinfo", "platform": "ovid", "how": "export"}}, str(o["cog"]))
    check("112: a run's screening opens only when he chooses it, from Open the screening or the Screening step, never when "
          "a run or a drop ends",
          sjs.count("siftOpen(") == 3 and "siftOpen(" in fn(sjs, "rvShow") and "siftOpen(" in fn(sjs, "rvStep")
          and "siftOpen(" in fn(sjs, "sfsBindOpen")
          and not any("siftOpen(" in fn(sjs, n) for n in ("sfsPoll", "sfsRun", "sfsDropFile", "sfsDrawRun")))
