from __future__ import annotations

import csv
import inspect
import json
import re
import shutil

from . import support
from .support import check, sift_words_js, skip


def test_sift_suggestion(scratch):
    print("\n138. Sift's suggestion box, 14 October, by Adam's dialog: a title that says what made the suggestion and where "
          "it came from, the sparkles on an AI's alone, one by keyword rules or that says nothing shown with the AI switch "
          "off, Accept suggestion in the suggested decision's colour deciding as a press of that decision does, the log's "
          "agreement between the screener's decisions and the suggestions, the PRISMA flow counting it as his, and the "
          "toast centred at every width. Since the test review of 18 October the box's markup, colours, the toast and the "
          "words on screen are review shots, and what made a suggestion, what shows with the switch off, Accept suggestion "
          "deciding as a press, the log's agreement and the PRISMA counts stay")
    import argparse
    import subprocess
    import ai_suggest
    import mcp_server
    import sift
    import sift_ai
    import cli as cli_mod
    import sift_cli
    import server as server_mod
    import sift_routes

    app_src = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    sjs = support.text("apps/sift/static/sift.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    node = shutil.which("node")
    base = scratch / "sift-suggestion-138"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)

    # ── A. an invented review of lighthouse keepers' routines, its CSV's suggestions made by keyword rules, by a
    # model, by nothing said and by Sift's own AI
    review = base / "Lighthouse review"
    review.mkdir()
    head = ["rec_id", "title", "abstract", "proposed_decision", "proposed_reason", "grounds", "proposed_by",
            "ft_proposed_decision", "ft_proposed_reason", "ft_grounds", "ft_proposed_by",
            "ai_proposed_decision", "ai_proposed_reason", "ai_grounds", "ai_proposed_by"]
    rows = [["L1", "Lamps at dusk", "Keepers lit the lamps at dusk.", "exclude", "R7", "lamps", "keyword rules"] + [""] * 8,
            ["L2", "Fog and bells", "Keepers rang bells in fog.", "include", "", "bells", "model: Opus 5.5"] + [""] * 8,
            ["L3", "Logbooks", "Keepers kept logbooks.", "maybe", "", "", ""] + [""] * 8,
            ["L4", "Storm nights", "Keepers watched storms.", "exclude", "R7", "", "Keyword  rules", "", "", "", "",
             "include", "", "storms", "model: Opus 5.5"],
            ["L5", "Supply boats", "Boats came monthly.", "exclude", "", "", "keyword rules"] + [""] * 8,
            ["L6", "Oil stores", "Oil was stored below.", "include", "", "", "a person"] + [""] * 8,
            ["L7", "Relief keepers", "Keepers took turns.", "include", "", "", "Model:   Sonnet 5"] + [""] * 8,
            ["L8", "Gulls", "Gulls nested nearby.", "", "", "", ""] + [""] * 8]
    with open(review / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(head)
        w.writerows(rows)
    (review / sift.REASONS_NAME).write_text("code,meaning\nR3,Not keepers\nR7,Not about lighthouses\n", encoding="utf-8")
    sc = sift.load(review)
    props = {rec: sift.proposals_of(sc, rec, "ta") for rec in sc.ids}
    kinds = {rec: [(p["source"], p["kind"], p["by"], p["model"], p["ai"]) for p in props[rec]] for rec in sc.ids}
    check("138: what made each suggestion, from proposed_by: keyword rules, a model named after model:, nothing said, any "
          "other words taken as nothing said, and Sift's own AI with the model it recorded",
          kinds["L1"] == [("csv", "rules", "keyword rules", "", False)]
          and kinds["L2"] == [("csv", "model", "model: Opus 5.5", "Opus 5.5", True)]
          and kinds["L3"] == [("csv", "unstated", "", "", False)]
          and kinds["L4"] == [("csv", "rules", "keyword rules", "", False), ("sift", "sift_model", "model: Opus 5.5", "Opus 5.5", True)]
          and kinds["L6"] == [("csv", "unstated", "", "", False)]
          and kinds["L7"] == [("csv", "model", "model: Sonnet 5", "Sonnet 5", True)] and kinds["L8"] == []
          and sift.COLUMNS["ta"]["by"] == "proposed_by" and sift.COLUMNS["ft"]["by"] == "ft_proposed_by"
          and sift.made_by("sift", "")["by"] == "Sift's AI" and sift.made_by("sift", "")["kind"] == "sift", str(kinds))
    shown = lambda rec, on: [(p["source"], p["kind"]) for p in sift.suggestions_shown(sc, rec, "ta", on)]
    check("138: with the AI switch off a suggestion by keyword rules or that says nothing shows and an AI's does not, and "
          "with it on both show, two at most",
          shown("L1", False) == [("csv", "rules")] and shown("L3", False) == [("csv", "unstated")]
          and shown("L2", False) == [] and shown("L4", False) == [("csv", "rules")]
          and shown("L2", True) == [("csv", "model")] and shown("L4", True) == [("csv", "rules"), ("sift", "sift_model")])

    # the decisions through the server, as the screen sends them, the app's AI switch off and then on
    on_cfg, off_cfg = base / "config-on.json", base / "config-off.json"
    on_cfg.write_text(json.dumps({"interviewer": "Adam", "ai_suggest": True}), encoding="utf-8")
    off_cfg.write_text(json.dumps({"interviewer": "Adam", "ai_suggest": False}), encoding="utf-8")
    empty_root = base / "no-cases"
    empty_root.mkdir()
    twin = base / "Lighthouse twin"
    shutil.copytree(review, twin)
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    lines = lambda folder: [json.loads(l) for l in (folder / sift.LOG_NAME).read_text(encoding="utf-8").splitlines() if l.strip()]
    decide = lambda folder, rec, d, reason="": sift_routes.api_sift({"op": "decide", "folder": str(folder), "rec_id": rec,
                                                                    "stage": "ta", "decision": d, "reason": reason, "note": ""})
    header_before = (review / sift.CSV_NAME).read_text(encoding="utf-8").splitlines()[0]
    try:
        server_mod.ROOT_OVERRIDE = str(empty_root)
        server_mod.STATE_MEMORY = {"recent": []}
        server_mod.CONFIG_PATH = off_cfg
        sift_routes.api_sift_review({"op": "open", "folder": str(review)})
        sift_routes.api_sift_review({"op": "open", "folder": str(twin)})
        decide(review, "L1", "exclude", "R7")
        decide(review, "L2", "exclude", "R3")
        decide(review, "L5", "exclude", "")
        decide(review, "L8", "include")
        server_mod.CONFIG_PATH = on_cfg
        decide(review, "L2", "maybe")
        decide(review, "L4", "include")
        decide(review, "L3", "maybe")
        decide(review, "L7", "exclude", "R3")
        # the twin decides L1 as a press of No and R7 does, and as Accept suggestion does: the same op, the same line
        server_mod.CONFIG_PATH = off_cfg
        decide(twin, "L1", "exclude", "R7")
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY) = kept
    log = lines(review)
    by_rec = lambda rec, i=-1: [e for e in log if e["rec_id"] == rec][i]
    pick = lambda e: (e["matched_suggestion"], e["suggestion_source"], e["suggestion_by"])
    check("138: each decision's line says whether it matched the suggestion shown, its decision and reason the same, "
          "with its source and what made it, empty with none shown, an AI's not shown with the switch off",
          pick(by_rec("L1")) == ("yes", "csv", "keyword rules") and pick(by_rec("L2", 0)) == ("", "", "")
          and pick(by_rec("L5")) == ("yes", "csv", "keyword rules") and pick(by_rec("L8")) == ("", "", "")
          and pick(by_rec("L2", 1)) == ("no", "csv", "model: Opus 5.5") and pick(by_rec("L3")) == ("yes", "csv", "")
          and pick(by_rec("L7")) == ("no", "csv", "model: Sonnet 5")
          and "other_suggestion" not in by_rec("L1"), str([pick(e) for e in log]))
    check("138: with two shown, the one it matched first and the other's source, what made it and whether it matched",
          pick(by_rec("L4")) == ("yes", "sift", "model: Opus 5.5")
          and by_rec("L4")["other_suggestion"] == {"source": "csv", "by": "keyword rules", "matched": "no"}, str(by_rec("L4")))
    words = {rec: sift.suggestion_words(by_rec(rec)) for rec in ("L1", "L3", "L4", "L7", "L8")}
    words["L2"] = sift.suggestion_words(by_rec("L2", 1))
    check("138: the log's words, AI only where a model made it, and nothing with no suggestion shown",
          words == {"L1": "The screener's decision matched the suggestion (keyword rules, from the CSV)",
                    "L3": "The screener's decision matched the suggestion (from the CSV)",
                    "L4": "The screener's decision matched the AI suggestion (Opus 5.5, from Sift) and did not match the "
                          "suggestion (keyword rules, from the CSV)",
                    "L7": "The screener's decision did not match the AI suggestion (Sonnet 5, from the CSV)",
                    "L8": "", "L2": "The screener's decision did not match the AI suggestion (Opus 5.5, from the CSV)"}
          and sift.suggestion_label("sift", "Sift's AI") == "the AI suggestion (from Sift)", str(words))
    banned = re.compile(r"\btook\b|\baccepted\b|AI accepted|AI decision|\bauto|\bbutton\b|\bvia\b", re.I)
    twin_line = lines(twin)[-1]
    same = lambda e: {k: v for k, v in e.items() if k not in ("at",)}
    check("138: the log never records which control made a decision: the line Accept suggestion's op writes is the line a "
          "press of No and R7 writes, no key of it names a control, and no word of the log's says took or accepted",
          same(twin_line) == same(by_rec("L1")) and not banned.search(json.dumps(twin_line)) and not any(
              banned.search(k) for e in log for k in e)
          and not any(banned.search(w) for w in words.values()) and not banned.search(json.dumps(sift.SUGGESTION_SAID))
          and "matched_suggestion" in by_rec("L8") and "suggestion" not in json.dumps(
              [e for e in log if e["act"] != "decide"]), str(sorted(twin_line)))
    check("138: screening.csv takes no new column from it, proposed_by stays as the review wrote it, and propose leaves it",
          (review / sift.CSV_NAME).read_text(encoding="utf-8").splitlines()[0] == header_before + ",decision,reason"
          and sift.load(review).cell("L1", "proposed_by") == "keyword rules"
          and sift.propose_review(review, "ta", [{"rec_id": "L3", "decision": "include"}])["written"] == ["L3"]
          and sift.load(review).cell("L2", "proposed_by") == "model: Opus 5.5"
          and "proposed_by" not in inspect.getsource(sift.propose_review).split('"""', 2)[2], header_before)

    # ── B. PRISMA: a decision by Accept suggestion is his, counted as any decision of his
    c = sift.counts(sift.load(twin))
    flow = sift.prisma_source(c)
    rows_csv = sift.counts_csv(c)
    check("138: the PRISMA flow and the export count a decision Accept suggestion made as his, under Records excluded by its "
          "reason, with no automation line, and the counts never read the agreement",
          "Records excluded<br/>(n = 1)<br/>R7 (n = 1)" in flow and "title and abstract,exclude,1" in rows_csv
          and "title and abstract,exclude R7,1" in rows_csv and not re.search(r"automation|automat", flow + rows_csv, re.I)
          and all("matched_suggestion" not in inspect.getsource(f) and "suggestion_match" not in inspect.getsource(f)
                  for f in (sift.counts, sift.prisma_source, sift.count_rows, sift.flow_of, sift.listed)), flow[:300])

    # ── C. the command line and MCP say it, and Sift's own AI records its model
    shown_l4 = sift_cli.cmd_sift(argparse.Namespace(folder=str(review), act="show", rec_id="L4", stage="ta", search=False))[1]
    check("138: the command line's show words each decision's agreement after its line, and the proposals with what made them",
          any(l.endswith(", Sift. The screener's decision matched the AI suggestion (Opus 5.5, from Sift) and did not match "
                         "the suggestion (keyword rules, from the CSV).") for l in shown_l4)
          and "Title and abstract: Yes, proposed No R7 (csv, keyword rules); proposed Yes (sift, model: Opus 5.5)." in shown_l4
          and sift_cli.proposal_said({"decision": "maybe", "source": "csv", "by": ""}) == "proposed Maybe (csv)"
          and sift_cli.proposal_said({"decision": "maybe", "source": "sift", "by": "Sift's AI"}) == "proposed Maybe (sift)"
          and "never which control made the decision" in json.dumps(
              [t for t in mcp_server.TOOLS if t["name"] == "sift_show"]), "\n".join(shown_l4))
    ai_rec = base / "Lighthouse ai"
    shutil.copytree(review, ai_rec, ignore=shutil.ignore_patterns(sift.LOG_NAME))
    sift.write_ai(ai_rec, "L8", "ta", "maybe", "", "gulls", model="Opus 5.5")
    first_by = sift.load(ai_rec).cell("L8", "ai_proposed_by")
    sift.write_ai(ai_rec, "L8", "ta", "include", "", "gulls")
    check("138: Sift's own proposal records the model that answered in ai_proposed_by, emptied by one written without, the "
          "route's model named as the app names it, and Start again clears it",
          first_by == "model: Opus 5.5" and sift.load(ai_rec).cell("L8", "ai_proposed_by") == ""
          and sift_ai.route_model({"provider": "local", "model": "tiny"}) == "tiny on this machine"
          and sift_ai.route_model({"provider": "anthropic", "model": "claude-opus-5-5"}) == ai_suggest.model_name("claude-opus-5-5")
          and "model=route_model(route)" in inspect.getsource(sift_ai.propose)
          and "ai_proposed_by" in sift.RESET_COLUMNS and "proposed_by" not in sift.RESET_COLUMNS, first_by)

    # ── D. the page: Accept suggestion, the key and the switch
    check("138: Accept suggestion and Enter call sfTakeProposal, which decides as a press of the decision does",
          "$('sf-take').onclick = () => sfTakeProposal(0);" in fn(sjs, "sfBoot")
          and "$('sf-take-2').onclick = () => sfTakeProposal(1);" in fn(sjs, "sfBoot")
          and "else if (key === 'Enter') { e.preventDefault(); sfTakeProposal(); }" in fn(sjs, "sfKeyDown")
          and "api(" not in fn(sjs, "sfTakeProposal") and "sfDecide(" in fn(sjs, "sfTakeProposal"))
    if not node:
        skip("138: the box and Accept suggestion in node", "node is not installed")
    else:
        lead = app_src[app_src.index("const esc = "):app_src.index("const escAttr = ")]
        # the words and keys, then the titles with sfSuggestionOf and sfSuggestions after them
        consts = "\n".join([sift_words_js(sjs),
                            "const SF_SUGGESTION = " + sjs.split("const SF_SUGGESTION = ", 1)[1].split("\nconst SF_GROUNDS = ", 1)[0]])
        loop = "const props = sfSuggestions(st);" + fn(sjs, "sfDraw").split("const props = sfSuggestions(st);", 1)[1].split("sfAiDraw();", 1)[0]
        harness = r"""
const els = {};
const mk = (id) => ({ id, hidden: true, innerHTML: '', textContent: '', title: '', dataset: {} });
const $ = (id) => els[id] || (els[id] = mk(id));
const SF = { stage: 'ta', aiMaster: false, marksHidden: false, reasons: { ta: [{ code: 'R3' }, { code: 'R7' }], ft: [{ code: 'R3' }] } };
const sfPillHtml = (d) => `<pill ${d}>`;
const sfMeaning = (c) => ({ R7: 'Not about allotments' }[c] || '');
__REASON__
const sfReasonPill = (c) => `<rpill ${c}>`;
const sfGroundsLine = () => {};
const sfMarks = () => [];
const sfMarked = (t) => t;
const sfCodes = () => SF.reasons[SF.stage];
const said = [];
const say = (t) => said.push(t);
let decided = [];
const sfDecide = (...args) => decided.push(args);
let REC = null;
const sfRecord = () => REC;
const sfStage = (r) => r.stages[SF.stage];
function draw(st) {
  const r = { abstract: '' };
  __LOOP__
  const box = (s) => ({ shown: !$(`sf-proposal${s}`).hidden, edge: $(`sf-proposal${s}`).dataset.decision,
    spark: !$(`sf-prop-spark${s}`).hidden, title: $(`sf-prop-said${s}`).textContent, tip: $(`sf-prop-title${s}`).title,
    take: !$(`sf-take${s}`).hidden, colour: $(`sf-take${s}`).dataset.decision, says: $(`sf-take${s}`).title });
  return [box(''), box('-2')];
}
__TAKE__
const P = {
  rules: { decision: 'exclude', reason: 'R7', source: 'csv', kind: 'rules', by: 'keyword rules', model: '', ai: false },
  model: { decision: 'include', reason: '', source: 'csv', kind: 'model', by: 'model: Opus 5.5', model: 'Opus 5.5', ai: true },
  unstated: { decision: 'maybe', reason: '', source: 'csv', kind: 'unstated', by: '', model: '', ai: false },
  sift: { decision: 'include', reason: '', source: 'sift', kind: 'sift_model', by: 'model: Opus 5.5', model: 'Opus 5.5', ai: true },
  siftBare: { decision: 'maybe', reason: '', source: 'sift', kind: 'sift', by: "Sift's AI", model: '', ai: true },
  bare: { decision: 'exclude', reason: '', source: 'csv', kind: 'rules', by: 'keyword rules', model: '', ai: false },
  odd: { decision: 'later', reason: '', source: 'csv', kind: 'unstated', by: '', model: '', ai: false },
};
const out = {};
SF.aiMaster = true;
out.on = {};
for (const k of Object.keys(P)) out.on[k] = draw({ proposals: [P[k]] })[0];
out.two = draw({ proposals: [P.rules, P.sift] });
SF.aiMaster = false;
out.off = { model: draw({ proposals: [P.model] })[0], sift: draw({ proposals: [P.sift] })[0], rules: draw({ proposals: [P.rules] })[0],
  unstated: draw({ proposals: [P.unstated] })[0], two: draw({ proposals: [P.rules, P.sift] }) };
// Accept suggestion, each box's, and Enter, the first's, against a press of the decision and its reason
const take = (props, i, stage = 'ta', ai = true) => {
  SF.stage = stage; SF.aiMaster = ai; decided = [];
  REC = { stages: { [stage]: { proposals: props } } };
  sfTakeProposal(i);
  return decided;
};
out.take = {
  rules: take([P.rules], 0), include: take([P.model], 0), maybe: take([P.unstated], 0), second: take([P.rules, P.sift], 1),
  bareTa: take([P.bare], 0), bareFt: take([P.bare], 0, 'ft'), offModel: take([P.model], 0, 'ta', false),
  offRules: take([P.rules], 0, 'ta', false), odd: take([P.odd], 0), none: take([], 0),
};
out.said = said;
// a suggestion's reason, a code on an exclude its pill and anything else a sentence (17 October, later)
out.reasons = [{ decision: 'maybe', reason: 'Leaves open who was asked' }, { decision: 'exclude', reason: 'R7' },
  { decision: 'exclude', reason: 'R9' }, { decision: 'exclude', reason: 'Not about allotments at all' },
  { decision: 'include', reason: 'R7' }, { decision: 'maybe', reason: '' }].map(sfPropReasonHtml);
// and the sentence's full stop, given where its words end with none and never doubled (17 October, later)
out.stops = [{ decision: 'maybe', reason: 'Asks only about yields?' }, { decision: 'maybe', reason: 'Names the plot holders.' },
  { decision: 'maybe', reason: 'Leaves it open (who was asked)' }, { decision: 'maybe', reason: 'Says only ‘shared beds.’' },
  { decision: 'include', reason: 'Plot holders in their own words, ' }, { decision: 'maybe', reason: 'Wait and see…' },
  { decision: 'exclude', reason: 'R7' }].map(sfPropReasonHtml);
SF.stage = 'ta'; SF.aiMaster = false;
draw({ proposals: [Object.assign({}, P.unstated, { reason: 'Leaves open who was asked' })] });
out.drawnReason = [$('sf-prop-reason').innerHTML, $('sf-prop-reason').hidden];
console.log(JSON.stringify(out));
"""
        script = base / "suggestion-138.js"
        script.write_text("\n".join([lead, consts, harness.replace("__LOOP__", loop).replace("__TAKE__", whole(sjs, "sfTakeProposal"))
                                     .replace("__REASON__", whole(sjs, "sfPropReasonHtml") + "\n" + whole(sjs, "sfSentence"))]),
                          encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        why = (ran.stderr or json.dumps(out))[:600]
        on = out.get("on", {})
        title = lambda b: (b.get("spark"), b.get("title"), b.get("tip"))
        check("138: in node, each title says what made the suggestion, an AI's alone saying AI and carrying the sparkles, "
              "and its tooltip names the model",
              all(title(on.get(k, {}))[0] is False and "AI" not in (title(on.get(k, {}))[1] or "AI") for k in ("rules", "unstated"))
              and all(title(on.get(k, {}))[0] is True and "AI" in (title(on.get(k, {}))[1] or "") for k in ("model", "sift", "siftBare"))
              and "Opus 5.5" in (title(on.get("model", {}))[2] or "") and "keyword rules" in (title(on.get("rules", {}))[1] or ""), why)
        check("138: in node, Accept suggestion for each decision Sift knows at the stage and none for one it does not",
              [on.get(k, {}).get("take") for k in ("rules", "model", "unstated", "odd")] == [True, True, True, False]
              and on.get("odd", {}).get("shown") is True, why)
        two, off = out.get("two", [{}, {}]), out.get("off", {})
        check("138: in node, two suggestions each in a box of its own with its own Accept suggestion, and with the AI switch "
              "off an AI's box hidden and one by keyword rules or that says nothing shown",
              two[0].get("shown") and two[1].get("shown") and two[0].get("take") and two[1].get("take")
              and off.get("model", {}).get("shown") is False and off.get("sift", {}).get("shown") is False
              and off.get("rules", {}).get("shown") is True and off.get("unstated", {}).get("shown") is True
              and off.get("two", [{}, {}])[0].get("shown") is True and off.get("two", [{}, {}])[1].get("shown") is False, why)
        tk = out.get("take", {})
        check("138: in node, Accept suggestion decides exactly as a press of that decision and its reason does: No and R7 as "
              "the reasons' press sends it, Yes and Maybe as their buttons, the second box its own, No with no reason taking "
              "No reason at title and abstract and opening the reasons at full text, and nothing for what the record does not show",
              tk.get("rules") == [["exclude", "R7", True]] and tk.get("include") == [["include"]] and tk.get("maybe") == [["maybe"]]
              and tk.get("second") == [["include"]] and tk.get("bareTa") == [["exclude", "", True]] and tk.get("bareFt") == [["exclude"]]
              and tk.get("offModel") == [] and tk.get("offRules") == [["exclude", "R7", True]] and tk.get("odd") == []
              and tk.get("none") == [] and len(out.get("said") or []) == 3
              and "b.onclick = () => sfDecide('exclude', sfReasonChoices()[Number(b.dataset.i)].code, true);" in fn(sjs, "sfReasonsDraw")
              and "sfDecide(b.dataset.decision)" in fn(sjs, "sfBoot"), json.dumps(tk))
