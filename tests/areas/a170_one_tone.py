from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from . import support
from .support import check, skip


def test_one_tone(scratch):
    print("\n170. One failure tone and the orange kept to its places, what polish4a and polish4b left: every failure line "
          "in the amber, Sift's chart, slider, funnel, Active, a running database and the links off the orange, Set up "
          "the form's two Type selects alike, the counts in the ink, a key quote and the hover's time legible, one kind "
          "of quotation mark on paper, the refusal's page centred, the trail scrolling at 360, a drag never taking the "
          "question, the rename list naming a sheet as the bar does, and the map's line with no records. "
          "Since the test review of 18 October the tones, "
          "the contrast figures, the widths and the markup are review shots, and the failure a line is marked with, the "
          "map's line and the one mark on paper stay")
    import ai_suggest as ai_mod
    import gets_print as gp
    import themes_print as tp

    read = lambda path: Path(path).read_text(encoding="utf-8")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    app, sjs = support.text("family/static/shell.js", "apps/idiograph/static/distil.js"), support.text("apps/sift/static/sift.js")
    # Sift's parts of the shell, from app.js since the family codebase's third build (22 October 2026)
    sset = support.text("apps/sift/static/sift_settings.js")
    node = shutil.which("node")

    # the server marks a live list that failed, so its note is said in the amber, and the built-in list he chose
    # with no key is no failure
    answer = lambda status, body="": (lambda *a, **k: (status, body))
    failed = [ai_mod.anthropic_models("k", transport=answer(s, b)) for s, b in ((0, ""), (401, ""), (500, ""), (200, "not json"),
                                                                                (200, json.dumps({"data": [{"id": "x-none"}]})))]
    keyless = ai_mod.anthropic_models(None)
    live = ai_mod.anthropic_models("k", transport=answer(200, json.dumps({"data": [{"id": m["id"]} for m in ai_mod.ANTHROPIC_MODELS]})))
    check("170: a live list of models that failed, did not answer, refused the key, answered 500, could not be read or "
          "named none, comes back marked failed, the built-in list with no key and the live list not",
          all(f.get("failed") is True and f["source"] == "builtin" and ", because " in f["note"] for f in failed)
          and "failed" not in keyless and "failed" not in live and live["source"] == "live", str([f.get("note") for f in failed]))

    if not node:
        skip("170: the failure lines in node", "no node on this machine")
    else:
        harness = r"""
const mk = (id) => { const set = new Set(); return { id, hidden: false, textContent: '', innerHTML: '', value: '', placeholder: '',
  checked: false, disabled: false, focus() {}, querySelectorAll: () => [],
  classList: { toggle(c, on) { if (on === undefined ? !set.has(c) : on) set.add(c); else set.delete(c); }, add(c) { set.add(c); },
    remove(c) { set.delete(c); }, contains: (c) => set.has(c) }, set }; };
const els = {};
const $ = (id) => els[id] || (els[id] = mk(id));
const NO_ENDPOINT = 'That is not something this server does';
const needsRestart = (err) => String((err && err.message) || err || '').includes(NO_ENDPOINT);
const RESTART_LINE = 'Restart the server to finish this update.';
let answers = {};
async function api(route, body) {
  const key = body && body.op ? `${route}:${body.op}` : route;
  const a = answers[key];
  if (a instanceof Error) throw a;
  return a || {};
}
const S = { models: null };
const ZOT = { opened: null, saved: true, ask: 0 };
const stale = { key: false, models: false };
let modelsAsk = 0;
function drawRestart() {}
function zotDraw() {}
function zotNow() { return { library: 'user', group_id: '' }; }
function fillModels() {}
function fillPetsModels() {}
function drawProvider() {}
function keyHome() {}
// the providers the AI page has since aipage (8 November 2026), Anthropic's alone here
const PROVIDER_ROWS = { anthropic: { key: true } };
const providerNow = () => 'anthropic';
const keyAsk = () => ({ provider: 'anthropic' });
function drawOtherModels() {}
function drawPetsNote() {}
const withCode = (s) => s;
"""
        body = "\n".join([whole(app, "saidIn"), re.search(r"(?m)^const saidErr = .*$", app).group(0),
                          whole(sset, "zotCheck").replace("function zotCheck(", "async function zotCheck("),
                          whole(sset, "zotSaveKey").replace("function zotSaveKey(", "async function zotSaveKey("),
                          whole(app, "keyStatus").replace("function keyStatus(", "async function keyStatus("),
                          whole(app, "loadModels").replace("function loadModels(", "async function loadModels(")])
        # the declarations are async in app.js: the split keeps the word before `function`, so it is put back once
        body = body.replace("async async function", "async function")
        run = r"""
(async () => {
const out = {};
const state = (id) => [els[id].textContent, els[id].classList.contains('said-failed')];
answers['/api/zotero:check'] = { ok: false, said: 'Zotero did not take that key.' };
await zotCheck(); out.zotRefused = state('zot-said');
answers['/api/zotero:check'] = { ok: true, said: 'The key works with the library of Seed Club.' };
await zotCheck(); out.zotWorks = state('zot-said');
answers['/api/zotero:key'] = new Error('Zotero did not answer while checking the key. Check the connection and try again.');
$('zot-key').value = 'invented';
await zotSaveKey(); out.zotSaveFailed = state('zot-said');
answers['/api/zotero:key'] = new Error(NO_ENDPOINT);
$('zot-key').value = 'invented';
await zotSaveKey(); out.zotRestart = state('zot-said');
answers['/api/key-status'] = new Error('The keychain did not answer.');
await keyStatus(); out.keyFailed = state('key-said');
answers['/api/key-status'] = { set: true, source: 'keychain' };
await keyStatus(); out.keySaved = state('key-said');
answers['/api/models'] = { provider: 'anthropic', model: 'm', local_model: '', anthropic: { models: [], source: 'builtin', failed: true,
  note: 'The built-in list, because Anthropic did not answer.' }, local: { running: false, models: [], note: '' } };
await loadModels(); out.modelsFailed = state('model-note');
answers['/api/models'] = { provider: 'anthropic', model: 'm', local_model: '', anthropic: { models: [], source: 'builtin',
  note: 'The built-in list.' }, local: { running: false, models: [], note: '' } };
await loadModels(); out.modelsBuiltin = state('model-note');
answers['/api/models'] = new Error('Anthropic did not answer (HTTP 503).');
await loadModels(); out.modelsError = state('model-note');
console.log(JSON.stringify(out));
})().catch((e) => { console.error(e.stack || String(e)); process.exit(1); });
"""
        script = scratch / "settings-170.js"
        script.write_text(support.i18n_js() + harness + body + "\n" + run, encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        o = {}
        try:
            o = json.loads(ran.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            pass
        check("170: in node, Settings says Zotero's refusal, a key's Save that failed, a keychain that did not answer, a "
              "live list of models that failed and an error in the amber, and a key that works, a key saved, the built-in "
              "list with no key and a restart in the small print",
              o == {"zotRefused": ["Zotero did not take that key.", True],
                    "zotWorks": ["The key works with the library of Seed Club.", False],
                    "zotSaveFailed": ["Zotero did not answer while checking the key. Check the connection and try again.", True],
                    "zotRestart": ["Restart the server to finish this update.", False],
                    "keyFailed": ["The keychain did not answer.", True], "keySaved": ["Key saved.", False],
                    "modelsFailed": ["The built-in list, because Anthropic did not answer.", True],
                    "modelsBuiltin": ["The built-in list.", False],
                    "modelsError": ["Anthropic did not answer (HTTP 503).", True]},
              (ran.stdout + ran.stderr)[-600:])

        # Sift's Zotero card: a refusal, an error and a sync that left items out in the amber, its preview and its
        # done line in the soft ink
        sift_harness = r"""
const mk = (id) => { const set = new Set(); return { id, hidden: false, textContent: '', disabled: false, value: '',
  querySelectorAll: () => [], focus() {},
  classList: { toggle(c, on) { if (on === undefined ? !set.has(c) : on) set.add(c); else set.delete(c); }, contains: (c) => set.has(c) } }; };
const els = {};
const $ = (id) => els[id] || (els[id] = mk(id));
const NO_ENDPOINT = 'That is not something this server does';
const needsRestart = (err) => String((err && err.message) || err || '').includes(NO_ENDPOINT);
const RESTART_LINE = 'Restart the server to finish this update.';
let answer = null;
async function api() { if (answer instanceof Error) throw answer; return answer; }
const SF = { records: [], ids: [], folder: 'seed-review' };
const sfZotWhich = () => 'all';
const sfZotCounts = () => ({ included: 1, filter: 1, all: 1 });
"""
        sift_body = "\n".join([whole(sjs, "sfSaid"), whole(sjs, "sfZotDraw"),
                               whole(sjs, "sfZotPlan").replace("function sfZotPlan(", "async function sfZotPlan("),
                               whole(sjs, "sfMapLine")]).replace("async async function", "async function")
        sift_run = r"""
(async () => {
const out = {};
const state = () => [$('sf-zot-said').textContent, $('sf-zot-said').classList.contains('said-failed')];
SF.zot = { folder: 'seed-review', plan: null, running: false, said: '', ask: 0 };
answer = new Error('Zotero did not take that key.');
await sfZotPlan(); out.refused = state();
answer = { adds: 1, updates: 0, leaves: 0, pdfs: 0, said: 'Into the collection Seed review, which it makes: adds 1 item.' };
await sfZotPlan(); out.preview = state();
SF.zot.said = 'Added 1 item, updated 0 and left 0, and uploaded 0 PDFs, in the collection Seed review. Zotero refused 1 item, the first R2';
SF.zot.failed = true; sfZotDraw(); out.leftOut = state();
answer = new Error(NO_ENDPOINT);
await sfZotPlan(); out.restart = state();
out.map = [sfMapLine({ total: 0, blank: 0, unplaced: [] }), sfMapLine({ total: 4, blank: 0, unplaced: [] }),
  sfMapLine({ total: 4, blank: 1, unplaced: [] })];
console.log(JSON.stringify(out));
})().catch((e) => { console.error(e.stack || String(e)); process.exit(1); });
"""
        script = scratch / "sift-170.js"
        script.write_text(sift_harness + sift_body + "\n" + sift_run, encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        o = {}
        try:
            o = json.loads(ran.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            pass
        check("170: in node, Sift's Zotero card says a refusal and a sync that left items out in the amber, its preview and "
              "a restart in the soft ink",
              o.get("refused") == ["Zotero did not take that key.", True]
              and o.get("preview") == ["Into the collection Seed review, which it makes: adds 1 item.", False]
              and (o.get("leftOut") or [None, None])[1] is True and o.get("restart") == ["Restart the server to finish this update.", False],
              (ran.stdout + ran.stderr)[-600:])
        # ── item 6: the map's line with no records says what is true for none
        check("170: in node, the map's line with no records to stand on says so, \"No records to map.\", where it said "
              "\"Every one of 0 records has a country.\", and with records says as it did",
              o.get("map") == ["No records to map.", "Every one of 4 records has a country.", "No country for 1 of 4 records."],
              str(o.get("map")))

    # ── E. paper: one kind of mark for a key quote across every print view
    marks = [tp.quoted('"a lead that went slack"'), tp.quoted("“a lead that went slack”"), tp.quoted("'a lead that went slack'"),
             tp.quoted("a lead that went slack")]
    st = tp.statement_html({"text": "Walks in the rain", "quote": '"a lead that went slack"', "sheet": "Initial", "time": "01:02"})
    cell = gp.cell_html({"kind": "quote", "text": '"a lead that went slack"', "key": True}, 2, None)
    item = gp.item_html({"kind": "es", "text": "Walks in the rain", "time": "01:02", "sheet": "Initial", "gone": False,
                         "quotes": [{"text": "“a lead that went slack”"}], "notes": []}, False)
    row = gp.quote_html({"text": "a lead that went slack", "time": "01:02", "sheet": "Initial"})
    want = "‘a lead that went slack’"
    check("170: on paper a key quote stands in single curly quotation marks in every print view, the table of PETs, the "
          "GETs table's key quote and its items, and the trail, once whatever marks the workbook keeps, as the book's tables "
          "and the Word document set it, where the GETs table and the trail set straight double ones",
          set(marks) == {want} and f'<p class="kq">{want}</p>' in st and f'<span class="tr-q">{want}</span>' in cell
          and f'<p class="kq">{want}</p>' in item and row.startswith(f"<i>{want}</i>")
          and "th.quoted(" not in read(support.source("apps/idiograph/gets_print.py")), str((st, cell, item, row))[:500])
