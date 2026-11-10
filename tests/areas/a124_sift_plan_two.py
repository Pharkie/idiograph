from __future__ import annotations

import inspect
import json
import os
import re
import shutil

from . import support
from .support import check, grip_js, refusal_of, skip


def test_sift_plan_two(scratch):
    print("\n124. Search strategy a second round from Adam's use, 12 October: Block 1 and Block 2 with Search in, Search "
          "in, by database shut with a line for each database that differs, one red Remove with its bin across the app, "
          "no In your list, a benchmark paper a row with its title found from its DOI, one list of exclusion reasons "
          "kept in reasons.csv, optional at title and abstract and required at full text, Export search_plan.md and "
          "Mark as registered, Limits and restrictions, Search runs numbered in a table, and Start new run")
    import http.server
    import subprocess
    import threading
    import server as server_mod
    import sift_routes
    import sift
    import sift_search as ss

    ssjs = support.text("apps/sift/static/sift_search.js")
    sift_src = support.text("apps/sift/static/sift.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    node = shutil.which("node")
    base = scratch / "sift-plan-124"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    build = fn(ssjs, "sfsBuild")

    # ── A. the screen's words: the old ones gone, the new ones in their places
    check("124: Mark as registered is held until the registry and its number are given, and sends both with the register op",
          "!sfsMarkRegistry() || !$('sfs-registration').value.trim()" in fn(ssjs, "sfsMarkReady")
          and "op: 'register', folder: SFS.folder, reason: SFS.reason, registry, registration" in fn(ssjs, "sfsMarkGo"))

    # ── C. the screen in node
    if not node:
        skip("124: the screen in node", "node is not installed")
    else:
        script = base / "plan-124.js"
        harness = r"""
const els = {};
const mk = (id) => ({ id, innerHTML: '', value: '', hidden: false, textContent: '', disabled: false, title: '', dataset: {},
  className: '', checked: false, attrs: {}, onclick: null, focus() {}, setAttribute(k, v) { this.attrs[k] = v; },
  click() { return this.onclick ? this.onclick() : undefined; },
  querySelectorAll: () => [], querySelector: () => null, matches: () => false, closest: () => null });
const $ = (id) => els[id] || (els[id] = mk(id));
$('settings').hidden = true;
$('feedback').hidden = true;
$('sfs-ask').hidden = true;
$('sfs-mark-card').hidden = true;
const calls = [];
async function api(path, body) {
  calls.push([path, JSON.parse(JSON.stringify(body))]);
  if (body.op === 'title') return { doi: body.doi, title: body.doi === '10.5555/kiln.7' ? 'Firing the anagama kiln' : '', said: 'OpenAlex does not know that DOI.' };
  if (body.op === 'reasons') return { plan: { reasons: body.rows }, current: { version: 1, registered: null } };
  if (body.op === 'export') return { exported: '# Search plan, version 1', plan_file: true, current: { version: 1, registered: null } };
  if (body.op === 'register') return { current: { version: 1, registered: '2026-10-12T10:00:00', registry: body.registry, registration: body.registration },
    versions: [{ version: 1, registered: '2026-10-12T10:00:00', registry: body.registry, registration: body.registration }], problems: [] };
  return {};
}
const said = [];
const say = (t) => said.push(t);
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
SFS.catalog = { sources: ['scopus', 'psycinfo', 'pubmed', 'epmc', 'other'],
  names: { scopus: 'Scopus', psycinfo: 'PsycInfo', pubmed: 'PubMed', epmc: 'Europe PMC', other: 'Other database' },
  keyless: ['pubmed', 'epmc'], apis: ['scopus', 'pubmed', 'epmc'], keyed: { scopus: 'ELSEVIER_API_KEY' },
  scopes: [['tak', 'Title, abstract and keywords'], ['methods', 'Methods sections'], ['fulltext', 'Full text']], types: [],
  platformed: ['psycinfo'], platforms: [['ebsco', 'EBSCO']], sites: {}, platform_sites: {}, hosts: {} };
SFS.folder = 'kiln-review';
SFS.today = '2026-10-12';
SFS.how = { scopus: 'export', pubmed: 'api', epmc: 'api', psycinfo: 'export' };
SFS.listed = [{ source: 'scopus', how: 'api' }, { source: 'pubmed', how: 'api' }];
SFS.keys = { scopus: false };
SFS.plan = { databases: ['scopus', 'psycinfo', 'pubmed', 'epmc'], others: {}, platforms: { psycinfo: 'ebsco' },
  blocks: [{ name: 'Kilns', terms: ['kiln*'], scope: 'tak', scopes: { epmc: 'methods' } },
           { name: 'Firing', terms: ['firing'], scope: 'tak', scopes: {} }],
  years: {}, types: [], reasons: [], benchmark: ['10.5555/kiln.1', 'not-a-doi'], benchmark_titles: { '10.5555/kiln.1': 'Smoke over the kiln' }, overrides: {} };
SFS.data = { strings: [], current: { version: 1, registered: null }, versions: [{ version: 1, registered: null }], problems: [], plan: SFS.plan,
  reasons_file: { reasons: [{ code: 'K1', meaning: 'Not about kilns' }, { code: 'K2', meaning: 'No firing' }], staged: false, said: '' } };
sfsDrawBlocks();
out.blocks = $('sfs-blocks').innerHTML;
SFS.ownOpen.add(SFS.plan.blocks[0]);
sfsDrawBlocks();
out.blocksOpen = $('sfs-blocks').innerHTML;
sfsDrawDatabases();
out.dbs = $('sfs-dbs').innerHTML;
sfsDrawBench(true);
out.bench = $('sfs-bench-rows').innerHTML;
out.benchHidden = $('sfs-bench-rows').hidden;
// a DOI entered asks the title op, and the title found is kept in the plan and saved
SFS.benchRows.push('https://doi.org/10.5555/KILN.7');
sfsBenchSync();
await sfsFindTitle('10.5555/kiln.7');
await SFS.chain;
out.found = { titles: SFS.plan.benchmark_titles, benchmark: SFS.plan.benchmark, asked: calls.filter((c) => c[1].op === 'title').map((c) => c[1]) };
await sfsFindTitle('10.5555/kiln.8');
out.notFound = sfsPaperWords('10.5555/kiln.8');
// Remove on a paper's row and the plan's benchmark after it
SFS.benchRows.splice(1, 1);
sfsBenchSync();
out.afterRemove = SFS.plan.benchmark;
sfsDrawReasons(true);
out.reasons = $('sfs-reasons').innerHTML;
SFS.reasons.push({ code: 'k1', meaning: 'Again' });
sfsReasonSaid();
out.twice = $('sfs-reasons-said').innerHTML;
SFS.reasons.pop();
await sfsReasonsSave();
out.reasonsSent = calls.filter((c) => c[1].op === 'reasons').map((c) => c[1]);
// Register: a draft, then an export, then Mark as registered with its registry and its number
sfsDrawVersion();
out.draft = { mark: $('sfs-mark').disabled, exportOff: $('sfs-export').disabled, steps: $('sfs-reg-steps').hidden, open: $('sfs-reg-open').hidden,
  copy: $('sfs-md-copy').hidden, when: $('sfs-reg-when').hidden, regDraft: $('sfs-reg-draft').hidden };
await sfsExport();
out.exported = { open: $('sfs-reg-open').hidden, copy: $('sfs-md-copy').hidden, said: said.slice(-1)[0], current: SFS.data.current.registered };
$('sfs-reg-prospero').checked = true;
$('sfs-registration').value = '';
sfsMarkReady();
out.markHeld = $('sfs-mark-yes').disabled;
$('sfs-registration').value = 'CRD42026000001';
sfsMarkReady();
out.markReady = $('sfs-mark-yes').disabled;
await sfsMarkGo();
out.marked = { when: $('sfs-reg-when').innerHTML, tag: $('sfs-state').textContent, regDraft: $('sfs-reg-draft').hidden, next: $('sfs-reg-next').hidden,
  sent: calls.filter((c) => c[1].op === 'register').map((c) => c[1]) };
SFS.data.current = { version: 2, registered: '2026-10-12T11:00:00', registry: 'OSF', registration: 'https://osf.io/kiln7' };
sfsDrawVersion();
out.link = $('sfs-reg-when').innerHTML;
// the runs, numbered in the order made, newest first
SFS.review = { opens: '2026-10-12-2', folder: 'kiln-review', searches: true, screening: 'kiln-review/runs/2026-10-12-2' };
SFS.runs = [
  { date: '2026-10-12-2', day: '2026-10-12', n: 2, number: 3, screening: true, records: 9, merged: 7, version: 2, draft: false, missed: [], benchmark: 2, decided: 0, rows: [] },
  { date: '2026-10-12', day: '2026-10-12', n: 1, number: 2, screening: true, records: 8, merged: 6, version: 1, draft: true, missed: ['10.5555/kiln.1'], benchmark: 2, decided: 2, rows: [] },
  { date: '2025-10-08', day: '2025-10-08', n: 1, number: 1, screening: false, records: null, merged: null, version: 1, draft: true, missed: [], benchmark: 0, decided: 0,
    rows: [{ source: 'psycinfo', name: 'PsycInfo', how: 'export', state: 'waiting', note: 'not run yet' }] }];
sfsDrawRun();
out.runs = $('sfs-runs').innerHTML;
out.table = $('sfs-runs-table').hidden;
out.follows = $('sfs-follows').innerHTML;
console.log(JSON.stringify(out));
})().catch((e) => { console.error(e && e.stack || e); process.exit(1); });
"""
        script.write_text(harness + body + "\n" + run, encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60, env=dict(os.environ, TZ="UTC"))
        o = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        why = (ran.stderr or ran.stdout)[:500]
        blocks = o.get("blocks", "").split('<div class="sfs-block"')[1:]
        check("124: in node, each block is headed Block 1, Block 2 with its name beside it, and Search in is labelled and "
              "stands with the block's terms, over them",
              len(blocks) == 2 and '<span class="sfs-bnum">Block 1</span><input class="sfs-bname" type="text" value="Kilns"' in blocks[0]
              and '<span class="sfs-bnum">Block 2</span><input class="sfs-bname" type="text" value="Firing"' in blocks[1]
              and 'aria-label="Block 1\'s name"' in blocks[0]
              and '<label class="sfs-label" for="sfs-scope-0">Search in</label><select class="sfs-select sfs-bscope" id="sfs-scope-0">' in blocks[0]
              and blocks[0].find("sfs-search-in") < blocks[0].find("sfs-terms") < blocks[0].find("sfs-own-toggle"), why or blocks[0][:400])
        check("124: in node, Search in, by database is a chevron button with its words, shut on every block at first, and "
              "while shut a line names each database that differs, Europe PMC: methods sections, and none on a block that "
              "differs nowhere",
              all('aria-expanded="false"' in b and "sfs-chev" in b and "Search in, by database</button>" in b for b in blocks)
              and "sfs-own-rows" not in o.get("blocks", "")
              and '<p class="sfs-own-said">Europe PMC: methods sections</p>' in blocks[0] and "sfs-own-said" not in blocks[1]
              and "<details" not in o.get("blocks", "") and "<summary" not in o.get("blocks", ""), why or blocks[0][-500:])
        opened = o.get("blocksOpen", "").split('<div class="sfs-block"')[1:]
        check("124: in node, opened, the block's choice for each database reads Same as the block, the differing line gone "
              "while the choices show, and the other block stays shut",
              len(opened) == 2 and 'aria-expanded="true"' in opened[0] and "sfs-own-rows" in opened[0]
              and '<option value="">Same as the block</option>' in opened[0] and "sfs-own-said" not in opened[0]
              and 'aria-expanded="false"' in opened[1], why or opened[0][-400:] if opened else why)
        dbs = {re.search(r'data-key="([a-z]+)"', r).group(1): r for r in o.get("dbs", "").split('<div class="sfs-db"')[1:]}
        check("124: in node, each database's row says how it runs, By API or By export, and Access not set for one his list "
              "sends by API whose key is not saved, with no In your list",
              '<span class="sfs-tag">By export</span><span class="sfs-tag draft">Access not set</span>' in dbs.get("scopus", "")
              and '<span class="sfs-tag api">By API</span>' in dbs.get("pubmed", "") and "Access not set" not in dbs.get("pubmed", "")
              and '<span class="sfs-tag">By export</span>' in dbs.get("psycinfo", "") and "In your list" not in o.get("dbs", "")
              and "sfs-mine" not in o.get("dbs", ""), why or str(list(dbs)))
        papers = o.get("bench", "").split('<div class="sfs-paper"')[1:]
        check("124: in node, each benchmark paper is a row, its DOI in a box, its title beside it, Remove on the row, a box "
              "that holds no DOI saying so, and no textarea and no second list",
              len(papers) == 2 and o.get("benchHidden") is False
              and '<input class="sfs-doi" type="text" value="10.5555/kiln.1"' in papers[0]
              and '<span class="sfs-paper-title"><span class="sfs-paper-name">Smoke over the kiln</span></span>' in papers[0]
              and 'class="ghost small btn-remove sfs-paper-remove" aria-label="Remove paper 1">Remove</button>' in papers[0]
              and '<span class="sfs-paper-not">Not a DOI</span>' in papers[1]
              and '<button type="button" class="ghost small" id="sfs-bench-add">Add a paper</button>' in build
              and "<textarea" not in build.split('id="sfs-h-bench"', 1)[1].split('id="sfs-h-reasons"', 1)[0]
              and "sfs-bench-list" not in ssjs, why or o.get("bench", "")[:400])
        found = o.get("found", {})
        check("124: in node, a DOI entered asks the title op for that DOI alone, as the plan keeps it, the title found kept "
              "in the plan's titles, Title not found for one OpenAlex does not know, and Remove takes the paper out",
              found.get("asked", [None])[0] == {"op": "title", "folder": "kiln-review", "doi": "10.5555/kiln.7"}
              and found.get("titles", {}).get("10.5555/kiln.7") == "Firing the anagama kiln"
              and found.get("benchmark") == ["10.5555/kiln.1", "not-a-doi", "10.5555/kiln.7"]
              and o.get("notFound") == '<span class="sfs-dim">Title not found</span>'
              and o.get("afterRemove") == ["10.5555/kiln.1", "10.5555/kiln.7"]
              and "say('That paper is in the list already.');" in fn(ssjs, "sfsDrawBench"), why or str(found))
        rows = o.get("reasons", "").split('<div class="sfs-reason"')[1:]
        check("124, updated 12 October (125): in node, the exclusion reasons are one list edited here, a row each with the "
              "shared handle, its code, what it means and Remove, Add a reason under them, a code held twice said, and an "
              "edit sent to the reasons op",
              len(rows) == 2 and 'value="K1" maxlength="12" placeholder="Code"' in rows[0]
              and 'value="Not about kilns" maxlength="200" placeholder="What it means"' in rows[0]
              and 'aria-label="Move reason 1, Alt and an arrow" title="Drag to move"' in rows[0]
              and 'aria-label="Move reason 2, Alt and an arrow"' in rows[1] and "Move reason 1 up" not in rows[0]
              and "btn-remove sfs-rremove" in rows[0]
              and '<button type="button" class="ghost small" id="sfs-reason-add">Add a reason</button>' in build
              and o.get("twice") == "<p>k1 is there twice, so only the first is kept.</p>"
              and o.get("reasonsSent") == [{"op": "reasons", "folder": "kiln-review",
                                            "rows": [{"code": "K1", "meaning": "Not about kilns"}, {"code": "K2", "meaning": "No firing"}],
                                            "seen": None}]
              and "Offered with No at title and abstract, where a reason is optional, and with Exclude at full text, where one is required." in build,
              why or o.get("reasons", "")[:400])
        d, ex, mk = o.get("draft", {}), o.get("exported", {}), o.get("marked", {})
        check("124: in node, a draft has Export ready, the steps and Mark as registered, Open and Copy hidden until "
              "search_plan.md is written, and Export writes it at any time without freezing the plan",
              d == {"mark": False, "exportOff": False, "steps": False, "open": True, "copy": True, "when": True, "regDraft": False}
              and ex == {"open": False, "copy": False, "said": "search_plan.md is in the review's folder.", "current": None},
              why or str([d, ex]))
        check("124: in node, Mark as registered is held until the registry and its number are given, then freezes the "
              "version through the register op with both, and the part says when and where, Export still there",
              o.get("markHeld") is True and o.get("markReady") is False
              and mk.get("sent") == [{"op": "register", "folder": "kiln-review", "reason": "", "registry": "PROSPERO",
                                      "registration": "CRD42026000001"}]
              and mk.get("when") == "Registered on 12 October 2026 with PROSPERO, CRD42026000001."
              and mk.get("tag") == "Registered 12 October 2026" and mk.get("regDraft") is True and mk.get("next") is False
              and o.get("link") == 'Registered on 12 October 2026 with OSF, <a href="https://osf.io/kiln7" target="_blank" '
                                   'rel="noopener noreferrer">https://osf.io/kiln7</a>.', why or str(mk))
        trs = o.get("runs", "").split('<tr class="sfs-run"')[1:]
        name = lambda h: h.split('class="sfs-run-name">', 1)[1].split("</th>", 1)[0] if "sfs-run-name" in h else ""
        check("124: in node, Search runs is a table, a run a row numbered in the order made with its day, the year only when "
              "it is not this year's, Trial or Registered search, the records found, after duplicates and the benchmark papers found",
              [name(t) for t in trs] == ["Run 3, 12 October", "Run 2, 12 October", "Run 1, 8 October 2025"] and o.get("table") is False
              and '<td class="sfs-run-kind" data-label="Search"><span class="sfs-tag api">Registered search</span></td>' in trs[0]
              and '<td class="sfs-num" data-label="Records found">9</td><td class="sfs-num" data-label="After duplicates">7</td>' in trs[0]
              and '<td class="sfs-num" data-label="Benchmark papers found"><span>2 of 2</span></td>' in trs[0]
              and '<span class="sfs-missed">1 of 2</span>' in trs[1] and '<span class="sfs-tag draft">Trial</span>' in trs[1]
              and 'data-label="Records found">Not run yet</td>' in trs[2], why or str([name(t) for t in trs]))
        check("124: in node, the run Screening has open reads Active, another run with a screening has Make active, a run "
              "with none neither, each run's Details a button with its chevron, and Keep the decisions from names a run by "
              "its number",
              '<span class="sfs-tag sfs-open-tag">Active</span>' in trs[0] and "Make active" not in trs[0]
              and '<button type="button" class="ghost small sfs-open-run" data-date="2026-10-12">Make active</button>' in trs[1]
              and "sfs-open-tag" not in trs[2] and "Make active" not in trs[2]
              and '<button data-date="2026-10-12" type="button" class="ghost small sfs-toggle sfs-details-toggle" aria-expanded="false">' in o.get("runs", "")
              and o.get("follows") == '<option value="2026-10-12">Run 2, 12 October</option><option value="none">No earlier run</option>',
              why or o.get("runs", "")[:500])
        # Screening's reasons at each stage: No reason first at title and abstract, key 0, the codes alone at full text
        pick = base / "pick-124.js"
        pick.write_text("const SF = { stage: 'ta', reasons: { ta: [{ code: 'K1', meaning: 'Not about kilns' }], ft: [{ code: 'K1', meaning: 'Not about kilns' }] } };\n"
                        "const sfCodes = () => SF.reasons[SF.stage] || [];\n"
                        + re.search(r"(?m)^const sfReasonChoices = .*$", sift_src).group(0) + "\n"
                        "const ta = sfReasonChoices().map((c) => c.code + '|' + c.meaning);\nSF.stage = 'ft';\n"
                        "console.log(JSON.stringify({ ta, ft: sfReasonChoices().map((c) => c.code + '|' + c.meaning) }));\n", encoding="utf-8")
        ran = subprocess.run([node, str(pick)], capture_output=True, text=True, encoding="utf-8", timeout=30)
        p = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        check("124: in node, Screening's reasons offer No reason first at title and abstract, key 0, and at full text the "
              "codes alone, a reason chosen there going straight to the decision",
              p == {"ta": ["|No reason", "K1|Not about kilns"], "ft": ["K1|Not about kilns"]}
              and "if (key === '0' && choices.length > codes.length) { e.preventDefault(); sfDecide('exclude', '', true); return; }" in sift_src
              and "if (decision === 'exclude' && !reason && !chosen && sfCodes().length) { sfPicking(true); return; }" in fn(sift_src, "sfDecide"),
              (ran.stderr or ran.stdout)[:300])

    # ── D. the server: the reasons in one list, the title from a stub, export, Mark as registered, the run numbers
    review = base / "Kiln review"
    review.mkdir()
    ss.new_plan(review, "Kiln review", "How is a firing lived?")
    ss.save(review, {"databases": ["psycinfo"], "blocks": [{"name": "Kilns", "terms": ["kiln*"]}],
                     "reasons": {"ta": ["K1 Not about kilns"], "ft": ["K2 No account of firing"]}})
    old_plan = ss.state(review)["plan"]["reasons"]
    check("124: a plan of before, its reasons a list for each stage, reads as one list, title and abstract first, and "
          "blank_plan holds an empty list",
          old_plan == [{"code": "K1", "meaning": "Not about kilns"}, {"code": "K2", "meaning": "No account of firing"}]
          and ss.blank_plan()["reasons"] == [] and ss.reasons_of("K3: Glaze only\n\nk3 again") == [{"code": "K3", "meaning": "Glaze only"}])
    twice = "stage,code,meaning\n" + "".join(f"{s},{c},{m}\n" for s in ("ta", "ft") for c, m in (("G1", "Not about glaze"), ("G2", "No kiln")))
    (review / sift.REASONS_NAME).write_text(twice, encoding="utf-8")
    held_twice = ss.file_reasons(review)
    read_twice = sift.reasons(review)
    still = (review / sift.REASONS_NAME).read_text(encoding="utf-8")
    check("124: a file of before listing the same codes and meanings under both stages reads as one list, no code twice, "
          "each offered at both stages, and reading it writes nothing",
          held_twice == {"reasons": [{"code": "G1", "meaning": "Not about glaze"}, {"code": "G2", "meaning": "No kiln"}],
                         "staged": False, "said": ""}
          and [r["code"] for r in read_twice["ta"]] == ["G1", "G2"] == [r["code"] for r in read_twice["ft"]]
          and still == twice and ss.state(review)["reasons_file"]["reasons"] == held_twice["reasons"], str(held_twice))
    (review / sift.REASONS_NAME).write_text("stage,code,meaning\nta,T1,Not about kilns\nft,F1,No account of firing\n", encoding="utf-8")
    staged = ss.file_reasons(review)
    staged_read = sift.reasons(review)
    check("124: a file of before with a code at each stage is still read, each code offered at its own stage, and the "
          "editor shows one list",
          staged == {"reasons": [{"code": "T1", "meaning": "Not about kilns"}, {"code": "F1", "meaning": "No account of firing"}],
                     "staged": True, "said": ""}
          and [r["code"] for r in staged_read["ta"]] == ["T1"] and [r["code"] for r in staged_read["ft"]] == ["F1"], str(staged))
    # a run whose screening has not begun takes the edit, and a run begun keeps its copy
    runs = review / ss.RUNS_DIR
    fresh = runs / "2026-10-08"
    begun_run = runs / "2026-10-09"
    for folder in (fresh, begun_run):
        folder.mkdir(parents=True)
        (folder / sift.CSV_NAME).write_text("rec_id,title,abstract,decision,reason\nR001,Smoke over the kiln,Kilns.,,\n", encoding="utf-8")
        (folder / sift.REASONS_NAME).write_text("stage,code,meaning\nta,T1,Not about kilns\n", encoding="utf-8")
    (begun_run / sift.CSV_NAME).write_text("rec_id,title,abstract,decision,reason\nR001,Smoke over the kiln,Kilns.,include,\n", encoding="utf-8")
    edited = ss.save_reasons(review, [{"code": "T1", "meaning": "Not about kilns"}, {"code": "F2", "meaning": "No firing"},
                                      {"code": "t1", "meaning": "Again"}, {"code": "", "meaning": "No code"}])
    one_list = "code,meaning\nT1,Not about kilns\nF2,No firing\n"
    check("124: the reasons op writes the review's reasons.csv in the one-list form once he edits, a code held twice kept "
          "once, a row with no code let go, the plan taking them, a run not begun taking the new file and a run begun "
          "keeping the copy it was made with",
          (review / sift.REASONS_NAME).read_text(encoding="utf-8") == one_list
          and edited["plan"]["reasons"] == [{"code": "T1", "meaning": "Not about kilns"}, {"code": "F2", "meaning": "No firing"}]
          and edited["reasons_file"]["staged"] is False
          and (fresh / sift.REASONS_NAME).read_text(encoding="utf-8") == one_list
          and (begun_run / sift.REASONS_NAME).read_text(encoding="utf-8") == "stage,code,meaning\nta,T1,Not about kilns\n"
          and ss.reasons_csv({"reasons": []}) == "" and ss.reasons_text([]) == "code,meaning\n"
          and [r["code"] for r in sift.reasons(review)["ta"]] == ["T1", "F2"] == [r["code"] for r in sift.reasons(review)["ft"]],
          (review / sift.REASONS_NAME).read_text(encoding="utf-8"))
    # a reason optional at title and abstract and required at full text
    screen = base / "Kiln screening"
    screen.mkdir()
    (screen / sift.CSV_NAME).write_text("rec_id,title,abstract\nR001,Smoke over the kiln,On kilns.\nR002,Glaze and ash,On glaze.\n"
                                        "R003,Cones that bend,On cones.\n", encoding="utf-8")
    (screen / sift.REASONS_NAME).write_text(one_list, encoding="utf-8")
    bare_ta = sift.decide(screen, "R001", "ta", "exclude", "")
    sift.decide(screen, "R002", "ta", "include")
    bare_ft = refusal_of(lambda: sift.decide(screen, "R002", "ft", "exclude", ""))
    coded_ft = sift.decide(screen, "R002", "ft", "exclude", "F2")
    wrong_ta = refusal_of(lambda: sift.decide(screen, "R003", "ta", "exclude", "Z9"))
    proposed = sift.propose_review(screen, "ta", [{"rec_id": "R003", "decision": "exclude", "reason": "", "grounds": ""}])
    check("124: a reject takes no reason at title and abstract and must take one at full text, a reason given is a code, "
          "and the review's proposals follow the same rule",
          bare_ta["stages"]["ta"]["decision"] == "exclude" and bare_ta["stages"]["ta"]["reason"] == ""
          and bare_ft == "Exclude at full text takes a reason, one of T1, F2."
          and coded_ft["stages"]["ft"]["reason"] == "F2" and wrong_ta == "Z9 is not a reason code at title and abstract."
          and bool(proposed) and sift.reason_problem("ft", "", []) == "" and sift.reason_problem("ta", "", ["T1"]) == "",
          str([bare_ft, wrong_ta]))

    # the title from a stub of OpenAlex on loopback, never a real request
    seen = []

    class Stub(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append(self.path)
            known = "10.5555/kiln.7" in urllib_query(self.path)
            payload = {"results": [{"id": "W1", "doi": "https://doi.org/10.5555/kiln.7", "display_name": "Firing the <i>anagama</i> kiln"}]
                       if known else []}
            data = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    stub = http.server.HTTPServer(("127.0.0.1", 0), Stub)
    port = stub.server_address[1]
    threading.Thread(target=stub.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    kept_env = os.environ.get(ss.STUB_ENV)
    kept_state = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.OPEN_FILE)
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"interviewer": "Adam"}), encoding="utf-8")
    try:
        os.environ[ss.STUB_ENV] = f"http://127.0.0.1:{port}"
        ctx = ss.Context(pause=lambda s: None)
        got = ss.paper_title("https://doi.org/10.5555/KILN.7", ctx)
        missing = ss.paper_title("10.5555/kiln.8", ctx)
        not_doi = ss.paper_title("kiln seven")
        server_mod.CONFIG_PATH = config_file
        server_mod.ROOT_OVERRIDE = str(base)
        server_mod.STATE_MEMORY = {"recent": []}
        server_mod.OPEN_FILE = lambda p: None
        sift_routes.api_sift_review({"op": "open", "folder": str(review)})
        by_op = sift_routes.api_sift_search({"op": "title", "folder": str(review), "doi": "10.5555/kiln.7"})
        listing = sorted(p.relative_to(review).as_posix() for p in review.rglob("*") if p.is_file())
        # Export at any time, a draft or not, and Mark as registered with its registry and number
        no_where = refusal_of(lambda: sift_routes.api_sift_search({"op": "register", "folder": str(review), "registry": "OSF"}))
        exported = sift_routes.api_sift_search({"op": "export", "folder": str(review)})
        written = (review / ss.PLAN_MD).read_text(encoding="utf-8")
        marked = sift_routes.api_sift_search({"op": "register", "folder": str(review), "registry": "PROSPERO",
                                             "registration": "CRD42026000001"})
        after = (review / ss.PLAN_MD).read_text(encoding="utf-8")
        again = sift_routes.api_sift_search({"op": "export", "folder": str(review)})
        ss.save(review, {"databases": ["psycinfo", "pubmed"], "blocks": [{"name": "Kilns", "terms": ["kiln*"]}]}, reason="PubMed added")
        second = ss.state(review)
        reasons_op = sift_routes.api_sift_search({"op": "reasons", "folder": str(review), "rows": [{"code": "T1", "meaning": "Not about kilns"}]})
        bad_rows = refusal_of(lambda: sift_routes.api_sift_search({"op": "reasons", "folder": str(review), "rows": "T1"}))
        no_reasons_file = refusal_of(lambda: sift_routes.api_sift_search({"op": "open", "folder": str(review), "file": "reasons"}))
    finally:
        stub.shutdown()
        stub.server_close()
        if kept_env is None:
            os.environ.pop(ss.STUB_ENV, None)
        else:
            os.environ[ss.STUB_ENV] = kept_env
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.OPEN_FILE = kept_state
    check("124: a benchmark paper's title comes from OpenAlex by its DOI, a stub on loopback here, the DOI alone sent, the "
          "title in plain words, one it does not know saying so, and the title op answers it writing nothing",
          got == {"doi": "10.5555/kiln.7", "title": "Firing the anagama kiln", "said": ""}
          and missing == {"doi": "10.5555/kiln.8", "title": "", "said": "OpenAlex does not know that DOI."}
          and not_doi["title"] == "" and not_doi["said"].endswith("is not a DOI.") and by_op["title"] == "Firing the anagama kiln"
          and len(seen) == 3 and all(s.startswith("/works?") and "filter=doi%3A10.5555%2Fkiln." in s for s in seen)
          and "search_plan.md" not in listing, str(seen))
    check("124: Export writes search_plan.md at any time, a draft not frozen, and Mark as registered needs the registry and "
          "its number or link, freezes the version, keeps both and writes search_plan.md again to say so",
          no_where == "Say where the plan is registered and its registration number or link."
          and exported["current"]["registered"] is None and exported["file"] == "search_plan.md"
          and written.startswith("# Search plan, version 1\n\nNot yet registered.") and exported["exported"] == written
          and "## Limits and restrictions" in written and "## Exclusion reasons" in written
          and marked["current"]["registry"] == "PROSPERO" and marked["current"]["registration"] == "CRD42026000001"
          and bool(marked["current"]["registered"])
          and re.search(r"Registered \d+ \w+ \d{4} with PROSPERO, CRD42026000001\.", after) is not None
          and again["current"]["registered"] == marked["current"]["registered"]
          and second["current"]["version"] == 2 and second["current"]["registered"] is None
          and second["versions"][0]["registry"] == "PROSPERO" and "with PROSPERO, CRD42026000001" in second["versions"][0]["text"],
          str([no_where, after[:120]]))
    check("124: the reasons op saves the plan with the reasons, a list refused when it is none, and reasons.csv is never "
          "opened, the open op holding search_plan.md alone",
          reasons_op["plan"]["reasons"] == [{"code": "T1", "meaning": "Not about kilns"}]
          and bad_rows == "The reasons are a list, each a code and its meaning." and no_reasons_file == "The file is plan."
          and sift_routes.SEARCH_FILES == {"plan": "search_plan.md"}, str([bad_rows, no_reasons_file]))

    # each run numbered in the order made, the number kept when an earlier run is removed by hand
    numbered = base / "Kiln numbers"
    for name_ in ("2026-10-08", "2026-10-12", "2026-10-12-2"):
        (numbered / ss.RUNS_DIR / name_).mkdir(parents=True)
    before_keep = ss.run_numbers(numbered)
    labels = [r["label"] for r in ss.runs(numbered)]
    ss.keep_numbers(numbered)
    kept_file = json.loads((numbered / ss.RUNS_DIR / ss.NUMBERS_NAME).read_text(encoding="utf-8"))
    shutil.rmtree(numbered / ss.RUNS_DIR / "2026-10-08")
    (numbered / ss.RUNS_DIR / "2026-10-13").mkdir()
    after_remove = [(r["date"], r["number"], r["label"]) for r in ss.runs(numbered)]
    check("124: each run is numbered in the order made, Run 1, 8 October 2026 up, the screens naming it so and the command "
          "line by its day, the numbers kept in runs/numbers.json, so a run removed by hand moves no other run's number",
          before_keep == {"2026-10-08": 1, "2026-10-12": 2, "2026-10-12-2": 3}
          and labels == ["Run 3, 12 October 2026", "Run 2, 12 October 2026", "Run 1, 8 October 2026"]
          and kept_file == before_keep
          and after_remove == [("2026-10-13", 4, "Run 4, 13 October 2026"), ("2026-10-12-2", 3, "Run 3, 12 October 2026"),
                               ("2026-10-12", 2, "Run 2, 12 October 2026")]
          and ss.run_said("2026-10-12-2") == "12 October 2026, run 2" and ss.run_said("2026-10-14", numbered) == "Run 5, 14 October 2026"
          and "keep_numbers(folder)" in inspect.getsource(ss.run) and "keep_numbers(folder)" in inspect.getsource(ss.take_export),
          str(after_remove))



def urllib_query(path: str) -> str:
    from urllib.parse import unquote
    return unquote(path)
