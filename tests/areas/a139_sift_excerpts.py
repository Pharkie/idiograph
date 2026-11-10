from __future__ import annotations

import csv
import inspect
import json
import shutil

from . import support
from .support import check, refusal_of, sift_words_js, skip


@support.as_app("sift")
def test_sift_excerpts(scratch):
    print("\n139. Sift's key excerpts, 14 October, Adam's words: words of a record's title or abstract selected and kept "
          "with H, Cmd or Ctrl adding a piece, joined in the text's order with an ellipsis by quote.js as q does on "
          "Experiential statements, several to a record under the note with Remove, Undo taking back the last, their "
          "marks drawn again from the offsets kept in a column of Sift's own, the export, show and MCP reading them. Since the test review of 18 October the card's markup, "
          "the colours and the words are review shots, and what H, Remove and Undo do and what is saved stay")
    import argparse
    import subprocess
    import mcp_server
    import sift
    import cli as cli_mod
    import sift_cli
    import server as server_mod
    import sift_routes

    app_src = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    quote_src = support.text("family/static/quote.js")
    sjs = support.text("apps/sift/static/sift.js")
    # the server's and, since the family codebase's third build, Sift's own routes
    server_src = "\n".join(support.source(p).read_text(encoding="utf-8") for p in ("server.py", "apps/sift/sift_routes.py"))
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    node = shutil.which("node")
    base = scratch / "sift-excerpts-139"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)

    # ── A. an invented review of community orchard volunteers, its CSV holding the review's proposals and Sift's own
    review = base / "Orchard review"
    review.mkdir()
    title1 = "Harvest days in a community orchard"
    abstract1 = ("Volunteers picked apples on Saturdays. Some came for recreational picking, others for the cider.\n"
                 "Older volunteers taught pruning.")
    head = ["rec_id", "title", "abstract", "proposed_decision", "proposed_reason", "grounds", "proposed_by",
            "ai_proposed_decision", "ai_proposed_reason", "ai_grounds", "ai_proposed_by"]
    rows = [["O1", title1, abstract1, "exclude", "R2", "recreational picking", "keyword rules", "maybe", "", "cider", ""],
            ["O2", "Grafting old varieties", "Members grafted rare pears.", "include", "", "", "", "", "", "", ""],
            ["O3", "Café at the orchard gate", "Visitors bought juice.", "", "", "", "", "", "", "", ""]]
    with open(review / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(head)
        w.writerows(rows)
    (review / sift.REASONS_NAME).write_text("code,meaning\nR2,Not volunteering\n", encoding="utf-8")
    proposal_cols = list(sift.PROPOSAL_COLUMNS) + list(sift.AI_PROPOSAL_COLUMNS)
    proposals = lambda: {rec: [sift.load(review).cell(rec, c) for c in proposal_cols] for rec in ("O1", "O2", "O3")}
    before_props = proposals()
    at = lambda words, text=abstract1: (text.index(words), text.index(words) + len(words))
    pc = at("recreational picking")
    cider = at("for the cider")
    harvest = at("Harvest days", title1)
    cfg = base / "config.json"
    cfg.write_text(json.dumps({"interviewer": "Adam", "ai_suggest": False}), encoding="utf-8")
    empty_root = base / "no-cases"
    empty_root.mkdir()
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    call = lambda body: sift_routes.api_sift(dict(body, folder=str(review)))
    log = lambda: [json.loads(l) for l in (review / sift.LOG_NAME).read_text(encoding="utf-8").splitlines() if l.strip()]
    refused = lambda body: refusal_of(lambda: call(body))
    try:
        server_mod.ROOT_OVERRIDE = str(empty_root)
        server_mod.STATE_MEMORY = {"recent": []}
        server_mod.CONFIG_PATH = cfg
        sift_routes.api_sift_review({"op": "open", "folder": str(review)})
        counts_before = sift.counts(sift.load(review))
        one = call({"op": "excerpt", "act": "add", "rec_id": "O1", "stage": "ta",
                    "pieces": [{"in": "abstract", "start": pc[0], "end": pc[1]}]})
        two = call({"op": "excerpt", "act": "add", "rec_id": "O1", "stage": "ta",
                    "pieces": [{"in": "title", "start": harvest[0], "end": harvest[1]},
                               {"in": "abstract", "start": cider[0], "end": cider[1]}]})
        cell_two = sift.load(review).cell("O1", sift.EXCERPTS_COLUMN)
        counts_two = sift.counts(sift.load(review))
        call({"op": "decide", "rec_id": "O1", "stage": "ta", "decision": "include", "reason": "", "note": ""})
        out_of_order = refused({"op": "excerpt", "act": "add", "rec_id": "O1", "stage": "ta",
                                "pieces": [{"in": "abstract", "start": cider[0], "end": cider[1]},
                                           {"in": "title", "start": harvest[0], "end": harvest[1]}]})
        beyond = refused({"op": "excerpt", "act": "add", "rec_id": "O1", "stage": "ta",
                          "pieces": [{"in": "abstract", "start": 5, "end": 999}]})
        elsewhere = refused({"op": "excerpt", "act": "add", "rec_id": "O1", "stage": "ta",
                             "pieces": [{"in": "authors", "start": 0, "end": 3}]})
        not_ft = refused({"op": "excerpt", "act": "add", "rec_id": "O2", "stage": "ft",
                          "pieces": [{"in": "abstract", "start": 0, "end": 7}]})
        stale = refused({"op": "excerpt", "act": "remove", "rec_id": "O1", "at": 0, "text": "words never kept"})
        removed = call({"op": "excerpt", "act": "remove", "rec_id": "O1", "at": 0, "text": "recreational picking"})
        undo_said = removed["undo"]
        u1 = call({"op": "undo"})
        after_u1 = sift.excerpts_of(sift.load(review).cell("O1", sift.EXCERPTS_COLUMN))
        u2 = call({"op": "undo"})
        u3 = call({"op": "undo"})
        after_u3 = sift.excerpts_of(sift.load(review).cell("O1", sift.EXCERPTS_COLUMN))
        # the two put back, as he left them, for what follows
        call({"op": "excerpt", "act": "add", "rec_id": "O1", "stage": "ta",
              "pieces": [{"in": "title", "start": harvest[0], "end": harvest[1]},
                         {"in": "abstract", "start": cider[0], "end": cider[1]}]})
        call({"op": "decide", "rec_id": "O1", "stage": "ta", "decision": "include", "reason": "", "note": ""})
        call({"op": "decide", "rec_id": "O1", "stage": "ft", "decision": "include", "reason": "", "note": ""})
        call({"op": "excerpt", "act": "add", "rec_id": "O1", "stage": "ft",
              "pieces": [{"in": "abstract", "start": abstract1.index("Older"), "end": abstract1.index("pruning") + 7}]})
        read = sift_routes.api_sift({"op": "read", "folder": str(review)})
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY) = kept
    ex_one = one["record"]["excerpts"]
    ex_two = two["record"]["excerpts"]
    check("139: H's excerpt kept through the server, one piece, its words verbatim, the stage it was made at and its "
          "piece's offsets in the abstract",
          ex_one == [{"stage": "ta", "text": "recreational picking", "pieces": [{"in": "abstract", "start": pc[0], "end": pc[1]}]}],
          json.dumps(ex_one))
    check("139: an excerpt of a title piece and an abstract piece, the title's first, joined with an ellipsis, and several "
          "to a record in the order made",
          [x["text"] for x in ex_two] == ["recreational picking", "Harvest days … for the cider"]
          and ex_two[1]["pieces"] == [{"in": "title", "start": harvest[0], "end": harvest[1]},
                                      {"in": "abstract", "start": cider[0], "end": cider[1]}], json.dumps(ex_two))
    check("139: the cell is JSON in ASCII alone, the ellipsis escaped, so Excel's reading or saving never changes it, and "
          "the record's excerpts read back from it",
          all(ord(c) < 128 for c in cell_two) and "\\u2026" in cell_two and cell_two.startswith("[{")
          and sift.excerpts_of(cell_two) == ex_two and sift.excerpts_cell(ex_two) == cell_two and sift.excerpts_cell([]) == ""
          and sift.excerpts_of("not json") == [] and sift.excerpts_of('[{"stage":"xx","text":"a","pieces":[]}, 4]') == []
          and sift.excerpts_of('{"stage":"ta"}') == [], cell_two[:120])
    lines = log()
    ex_lines = [e for e in lines if e.get("act") == "excerpt"]
    check("139: each excerpt kept or removed is a line of the log, act excerpt, field excerpts, its change, the excerpt and "
          "the cell before and after, and no stage of its own, so no decision reads it and the counts never move",
          [e["change"] for e in ex_lines[:3]] == ["add", "add", "remove"] and all("stage" not in e for e in ex_lines)
          and all(e["field"] == "excerpts" and e["tool"] == "Sift" for e in ex_lines)
          and ex_lines[1]["was"] == ex_lines[0]["value"] and ex_lines[1]["value"] == cell_two
          and ex_lines[2]["excerpt"]["text"] == "recreational picking"
          and not any(e.get("act") == "excerpt" for e in sift.read_log(review))
          and counts_before == counts_two, json.dumps(ex_lines[:1])[:300])
    check("139: a piece out of the text's order, beyond its text or outside the title and abstract is refused, an "
          "excerpt at full text only for a record that went on to it, and a Remove of words no longer there refused, "
          "none of them a line of the log",
          all([out_of_order, beyond, elsewhere, not_ft, stale]) and len(ex_lines) >= 3
          and [e["change"] for e in ex_lines[:3]] == ["add", "add", "remove"], str([out_of_order, beyond, not_ft, stale]))
    check("139: Remove takes out the excerpt named, and Undo, the screen's own, takes back the newest act, the Remove, then "
          "the decision, then the excerpt kept before it, each by a line of its own",
          [x["text"] for x in removed["record"]["excerpts"]] == ["Harvest days … for the cider"]
          and undo_said == {"rec_id": "O1", "stage": "ta", "n": removed["undo"]["n"], "what": "excerpt"}
          and u1["undone"]["what"] == "excerpt" and u1["undone"]["change"] == "remove"
          and [x["text"] for x in after_u1] == ["recreational picking", "Harvest days … for the cider"]
          and "what" not in u2["undone"] and u2["record"]["stages"]["ta"]["decision"] == ""
          and u3["undone"]["change"] == "add" and u3["undone"]["excerpt"]["text"] == "Harvest days … for the cider"
          and [x["text"] for x in after_u3] == ["recreational picking"]
          and [e["act"] for e in lines].count("undo") == 3
          and all("stage" not in e for e in lines if e.get("act") == "undo" and e.get("field") == "excerpts"),
          json.dumps([u1["undone"], u2["undone"], u3["undone"]])[:400])
    check("139: nothing is written to the review's proposal columns or Sift's own, and the excerpts column stands with "
          "Sift's own, a column of his that Start again clears and a new record may never carry",
          proposals() == before_props and sift.is_own("excerpts") and "excerpts" in sift.OWN_COLUMNS
          and "excerpts" not in sift.PROPOSAL_COLUMNS + sift.AI_PROPOSAL_COLUMNS
          and "his own in Sift" in refusal_of(lambda: sift.add_records(review, [{"title": "x", "excerpts": "[]"}], dry_run=True))
          and "proposed_decision" not in inspect.getsource(sift.excerpt), str(proposals()))
    rec_read = next(r for r in read["records"] if r["rec_id"] == "O1")
    check("139: the screening read again gives each record its excerpts with their offsets, so the marks come back",
          [x["text"] for x in rec_read["excerpts"]] == ["recreational picking", "Harvest days … for the cider", "Older volunteers taught pruning"]
          and rec_read["excerpts"][2]["stage"] == "ft" and rec_read["title"] == title1 and rec_read["abstract"] == abstract1,
          json.dumps(rec_read["excerpts"])[:300])

    # ── B. the export, the command line's show and MCP's record view
    done = sift.export_included(review)
    with open(review / sift.INCLUDED_CSV, encoding="utf-8", newline="") as fh:
        got = list(csv.reader(fh))
    ris = (review / sift.INCLUDED_RIS).read_text(encoding="utf-8")
    check("139: Export included records writes the excerpts as text in a last column, each in quotation marks with the "
          "stage it was made at, one a line, and the RIS as it was",
          done["records"] == 1 and got[0][-1] == "excerpts" and got[0][:-1] == list(sift.INCLUDED_COLUMNS)
          and got[1][-1] == '"recreational picking" (title and abstract)\n"Harvest days … for the cider" (title and abstract)\n'
                            '"Older volunteers taught pruning" (full text)'
          and "excerpt" not in ris.lower(), json.dumps(got)[:400])
    shown = sift_cli.cmd_sift(argparse.Namespace(folder=str(review), act="show", rec_id="O1", stage="ta", search=False))
    said = shown[1]
    check("139: the command line's show lists the excerpts with their stages and words each line of the log on them",
          'Key excerpt at title and abstract: "recreational picking"' in said
          and 'Key excerpt at full text: "Older volunteers taught pruning"' in said
          and any(l.endswith('key excerpt removed at title and abstract, "recreational picking", Sift') for l in said)
          and any(l.endswith('undo of a key excerpt removed at title and abstract, "recreational picking", Sift') for l in said)
          and any('key excerpt kept at title and abstract, "Harvest days … for the cider"' in l for l in said)
          and shown[0]["record"]["excerpts"] == rec_read["excerpts"], "\n".join(said))
    tool_show = next(t for t in mcp_server.TOOLS if t["name"] == "sift_show")
    check("139: MCP's record view gives the excerpts to read, and no command and no tool writes one",
          "key excerpts" in tool_show["description"] and "sift_show his key excerpts too, and no tool writes any of them" in mcp_server.instructions("sift")
          and "excerpt" not in sift_cli.SIFT_ACTS and not any("excerpt" in t["name"] for t in mcp_server.TOOLS)
          and all("sift_mod.excerpt(" not in support.source(p).read_text(encoding="utf-8")
                  for p in ("cli.py", "mcp_server.py", "apps/sift/sift_cli.py", "apps/sift/sift_mcp.py"))
          and 'if op == "excerpt":' in server_src and "sift_mod.excerpt(folder, body.get(\"act\")" in server_src)

    # ── C. not AI: the excerpts' code calls no model and sits under no AI switch
    section = sjs.split("/* ── key excerpts ── */", 1)[1].split("/* ── keys ── */", 1)[0] if "/* ── key excerpts ── */" in sjs else ""
    check("139: not AI: no sparkles, no AI switch and no model anywhere in the excerpts' code",
          section and "TB_SPARKS" not in section and "aiOn" not in section and "data-ai" not in section
          and "sfAiReady" not in section)

    # ── D. in node: the pieces in any order joined in the text's order, the marks from the offsets, H, Remove, the list,
    # the keys and Undo
    if not node:
        skip("139: the excerpts in node", "node is not installed")
    else:
        lead = app_src[app_src.index("const esc = "):app_src.index("const escAttr = ")]
        quote = quote_src.split("if (typeof module", 1)[0]
        harness = r"""
const els = {};
const mk = (id) => ({ id, hidden: true, innerHTML: '', textContent: '', title: '', dataset: {}, value: '' });
const $ = (id) => els[id] || (els[id] = mk(id));
const SF = { stage: 'ta', view: 'record', form: false, picking: false, marksHidden: false, pieces: [], piecesFor: null,
  folder: 'f', ids: ['O1', 'O2'], at: 0 };
const said = [];
const say = (t) => said.push(t);
const sent = [];
const api = async (url, body) => { sent.push(body); return {}; };
const sfQueue = (work) => work();
const sfLand = () => {};
const sfReload = async () => {};
const needsRestart = () => false;
const RESTART_LINE = '';
let drawn = 0;
const sfDraw = () => { drawn += 1; };
const restoreSelection = () => {};
let SELECTION = null;
const window = { getSelection: () => SELECTION || { rangeCount: 0, isCollapsed: true, removeAllRanges() {} } };
const sfSuggestions = () => [];
const sfMarks = () => [];
const sfStage = (r) => r.stages[SF.stage];
const TITLE = __TITLE__;
const ABSTRACT = __ABSTRACT__;
let REC = { rec_id: 'O1', title: TITLE, abstract: ABSTRACT, excerpts: [], stages: { ta: {}, ft: {} } };
const sfRecord = () => REC;
__MARKED__
__SECTION__
const at = (w, t = ABSTRACT) => ({ start: t.indexOf(w), end: t.indexOf(w) + w.length });
const P = (place, w) => ({ in: place, ...at(w, place === 'title' ? TITLE : ABSTRACT) });
const out = {};
// Cmd pieces in any order, an overlap and a gap of spaces joined, the title's before the abstract's
const pieces = [P('abstract', 'for the cider'), P('abstract', 'recreational'), P('title', 'Harvest'), P('abstract', 'recreational picking'),
  P('abstract', 'picking,')];
out.merged = sfExMerged(REC, pieces);
out.words = sfExWords(REC, pieces);
out.edge = sfExWords(REC, [{ in: 'title', start: TITLE.length - 7, end: TITLE.length }, { in: 'abstract', start: 0, end: 10 }]);
out.spaced = sfExWords(REC, [P('abstract', 'the cider.'), P('abstract', 'Older volunteers')]);
// H with the pieces built, then a second with one plain piece, then Remove of the first
SF.pieces = pieces.map((p) => ({ ...p }));
sfExKeep();
out.afterKeep = { excerpts: JSON.parse(JSON.stringify(REC.excerpts)), pieces: SF.pieces, sent: sent.slice(), said: said.slice() };
SF.pieces = [P('abstract', 'Saturdays')];
sfExKeep();
out.several = REC.excerpts.map((x) => x.text);
// nothing selected, or a selection outside the title and abstract: a plain line and nothing sent
const n = sent.length;
sfExKeep();
out.nothing = { said: said[said.length - 1], sent: sent.length - n };
// the marks from the offsets as the record comes back, grounds beside them, a mark under two carrying both classes
REC.excerpts = __KEPT__;
out.abstractHtml = sfAbstractHtml(REC, [[ABSTRACT.indexOf('recreational picking'), ABSTRACT.indexOf('recreational picking') + 20]]);
out.titleHtml = sfTitleHtml(REC);
SF.marksHidden = true;
SF.pieces = [P('abstract', 'apples')];
out.hiddenHtml = sfAbstractHtml(REC, []);
SF.marksHidden = false;
SF.pieces = [];
// an excerpt whose words no longer stand at its offsets draws no mark
REC.excerpts = [{ stage: 'ta', text: 'something else', pieces: [P('abstract', 'apples')] }];
out.staleHtml = sfAbstractHtml(REC, []);
out.staleShown = sfExShown(REC).length;
// the list, the other stage's named, and Remove sending the place and the words
REC.excerpts = __KEPT__;
SF.stage = 'ta';
sfExList(REC);
out.list = $('sf-ex-list').innerHTML;
out.listHidden = $('sf-ex-list').hidden;
sent.length = 0;
sfExRemove(0);
out.removed = { left: REC.excerpts.map((x) => x.text), sent: sent.slice() };
REC.excerpts = [];
sfExList(REC);
out.emptyHidden = $('sf-ex-list').hidden;
console.log(JSON.stringify(out));
"""
        kept_json = json.dumps(rec_read["excerpts"])
        marked = whole(sjs, "sfMarked")
        script = base / "excerpts-139.js"
        script.write_text("\n".join([lead, quote, harness.replace("__TITLE__", json.dumps(title1))
                                     .replace("__ABSTRACT__", json.dumps(abstract1)).replace("__KEPT__", kept_json)
                                     .replace("__MARKED__", marked).replace("__SECTION__", section)]), encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        why = (ran.stderr or json.dumps(out))[:700]
        pick = lambda w, t=abstract1: {"in": "title" if t is title1 else "abstract", "start": t.index(w), "end": t.index(w) + len(w)}
        check("139: in node, Cmd pieces in any order come out in the text's order, the title's first, an overlap and a gap of "
              "spaces joined, and their words joined with an ellipsis, never rearranged",
              out.get("merged") == [pick("Harvest", title1),
                                    {"in": "abstract", "start": abstract1.index("recreational"), "end": abstract1.index("picking,") + 8},
                                    pick("for the cider")]
              and out.get("words") == "Harvest … recreational picking, … for the cider"
              and out.get("edge") == "orchard … Volunteers" and out.get("spaced") == "the cider. Older volunteers", why)
        keep = out.get("afterKeep", {})
        check("139: in node, H keeps the pieces as one excerpt made at the stage, drawn at once and sent as add with its "
              "pieces, the pieces let go, several to a record in the order made, and with nothing selected a plain line",
              keep.get("excerpts") == [{"stage": "ta", "text": "Harvest … recreational picking, … for the cider",
                                        "pieces": out.get("merged")}]
              and keep.get("pieces") == [] and keep.get("sent") == [{"op": "excerpt", "folder": "f", "act": "add", "rec_id": "O1",
                                                                     "stage": "ta", "pieces": out.get("merged")}]
              and len(keep.get("said") or []) == 1
              and out.get("several") == ["Harvest … recreational picking, … for the cider", "Saturdays"]
              and bool(out.get("nothing", {}).get("said")) and out.get("nothing", {}).get("sent") == 0, why)
        rp = abstract1.index("recreational picking")
        check("139: in node, the marks drawn again from the offsets, each excerpt in a mark of its own beside the grounds', a "
              "word under both carrying both, the title's piece in the title, Hide taking the excerpts' marks with the "
              "grounds' and leaving the pieces being built, and words no longer at their offsets left unmarked",
              out.get("abstractHtml", "").count('<mark class="sf-ground sf-excerpt">recreational picking</mark>') == 1
              and '<mark class="sf-excerpt">for the cider</mark>' in out.get("abstractHtml", "")
              and '<mark class="sf-excerpt">Older volunteers taught pruning</mark>' in out.get("abstractHtml", "")
              and out.get("titleHtml") == '<mark class="sf-excerpt">Harvest days</mark> in a community orchard'
              and "sf-excerpt" not in out.get("hiddenHtml", "x") and '<mark class="sf-piece">apples</mark>' in out.get("hiddenHtml", "")
              and "<mark" not in out.get("staleHtml", "<mark") and out.get("staleShown") == 0 and rp > 0, why)
        listed = out.get("list", "")
        check("139: in node, the list holds each excerpt in quotation marks in the order made with the shared Remove, the "
              "stage named beside one made at the other, and Remove sends its place and words",
              listed.count('<li class="sf-ex">') == 3 and '<q class="sf-ex-words">recreational picking</q>' in listed
              and listed.index("recreational picking") < listed.index("Harvest days") < listed.index("Older volunteers")
              and listed.count('<span class="sf-ex-stage">At full text</span>') == 1 and out.get("listHidden") is False
              and out.get("removed") == {"left": ["Harvest days … for the cider", "Older volunteers taught pruning"],
                                         "sent": [{"op": "excerpt", "folder": "f", "act": "remove", "rec_id": "O1", "at": 0,
                                                   "text": "recreational picking"}]}
              and out.get("emptyHidden") is True, why)

        # the keys: H on a record, never in the note or a field, on the table or while the reasons stand open
        keys = r"""
const els = {};
const mk = (id) => ({ id, hidden: true, value: '', dataset: {}, classList: { contains: () => false } });
const $ = (id) => els[id] || (els[id] = mk(id));
$('sift').hidden = false;
const sfShown = () => true;
const sfMenuKey = () => false;
const sfHandleKey = () => false;
const sfEdgeKey = () => false;
const MAC = true;
const MOD = (e) => e.metaKey;
const sfNarrow = () => false;
const SF = { view: 'record', picking: false, form: false, stage: 'ta', pieces: [], reasons: { ta: [{ code: 'R2' }] } };
const sfCodes = () => SF.reasons.ta;
const sfReasonChoices = () => [{ code: '' }, ...sfCodes()];
const calls = [];
const log = (name) => (...a) => calls.push([name, ...a]);
const sfExKeep = log('keep');
const sfExClear = log('clear');
const sfDecide = log('decide');
const sfPicking = log('picking');
const sfUndo = log('undo');
const sfToTable = log('table');
const sfMove = log('move');
const sfTakeProposal = log('take');
const sfOpenRecord = log('open');
const sfKeysOpen = log('keys');
const sfPdfShut = log('pdf');
const sfReasonsDraw = () => {};
const sfFlowOpen = () => {};
const sfFacetsOpen = () => {};
const sfStudyAs = () => {};
const sfFind = () => {};
__WORDS__
__DOWN__
const plain = { tagName: 'DIV', id: '', dataset: {}, classList: { contains: () => false }, closest: () => null, blur() {} };
const note = Object.assign($('sf-note'), { tagName: 'TEXTAREA', closest: (s) => (s.startsWith('textarea') ? note : null), blur() {} });
const field = { tagName: 'INPUT', id: 'sf-f-x', dataset: {}, classList: { contains: (c) => c === 'sf-field' }, closest: (s) => (s.startsWith('textarea') ? field : null), blur() {} };
const press = (key, target = plain, mods = {}) => {
  calls.length = 0;
  let prevented = false;
  sfKeyDown({ key, target, preventDefault() { prevented = true; }, stopPropagation() {}, metaKey: false, ctrlKey: false,
    altKey: false, shiftKey: false, ...mods });
  return { calls: calls.map((c) => c[0]), prevented };
};
const out = {};
out.record = press('h');
out.upper = press('H', plain, { shiftKey: true });
out.note = press('h', note);
out.field = press('h', field);
SF.view = 'table';
out.table = press('h');
SF.view = 'record';
SF.picking = true;
out.picking = press('h');
SF.picking = false;
SF.form = true;
out.form = press('h');
SF.form = false;
out.cmd = press('h', plain, { metaKey: true });
SF.pieces = [{ in: 'abstract', start: 0, end: 3 }];
out.escPieces = press('Escape');
SF.pieces = [];
out.escNone = press('Escape');
out.y = press('y');
out.z = press('z', plain, { metaKey: true });
console.log(JSON.stringify(out));
"""
        kscript = base / "excerpt-keys-139.js"
        kscript.write_text(keys.replace("__WORDS__", sift_words_js(sjs)).replace("__DOWN__", whole(sjs, "sfKeyDown")), encoding="utf-8")
        ran = subprocess.run([node, str(kscript)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        kout = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        why = (ran.stderr or json.dumps(kout))[:700]
        check("139: in node, H keeps an excerpt on a record, shifted or not, and never in the note or a field, on the table, "
              "while the reasons stand open, at Extract and appraise or with Cmd, Esc letting the pieces go before it "
              "goes back to the table, and Y and Cmd + Z as they were",
              kout.get("record") == {"calls": ["keep"], "prevented": True} and kout.get("upper") == {"calls": ["keep"], "prevented": True}
              and kout.get("note", {}).get("calls") == [] and kout.get("field", {}).get("calls") == []
              and kout.get("table", {}).get("calls") == [] and kout.get("picking", {}).get("calls") == []
              and kout.get("form") == {"calls": [], "prevented": True} and kout.get("cmd", {}).get("calls") == []
              and kout.get("escPieces", {}).get("calls") == ["clear"] and kout.get("escNone", {}).get("calls") == ["table"]
              and kout.get("y", {}).get("calls") == ["decide"] and kout.get("z", {}).get("calls") == ["undo"], why)

        # Undo through the screen's own undo: an excerpt kept taken out leaves its words marked, one removed comes back
        undo = r"""
const els = {};
const $ = (id) => els[id] || (els[id] = { hidden: true });
const SF = { stage: 'ft', view: 'record', ids: ['O1', 'O2'], at: 1, pieces: [], piecesFor: null, picking: true, tvReveal: false, folder: 'f' };
const said = [];
const say = (t) => said.push(t);
let answer = null;
const api = async () => answer;
let last = null;
const sfQueue = (work) => (last = work());
const sfLand = () => {};
const sfDraw = () => {};
__UNDO__
const out = {};
(async () => {
  answer = { undone: { rec_id: 'O1', stage: 'ta', n: 4, what: 'excerpt', change: 'add',
    excerpt: { stage: 'ta', text: 'apples', pieces: [{ in: 'abstract', start: 20, end: 26 }] } } };
  sfUndo();
  await last;
  out.add = { at: SF.at, pieces: SF.pieces, for: SF.piecesFor, said: said.slice() };
  said.length = 0;
  SF.at = 1;
  answer = { undone: { rec_id: 'O1', stage: 'ta', n: 5, what: 'excerpt', change: 'remove', excerpt: { stage: 'ta', text: 'x', pieces: [] } } };
  sfUndo();
  await last;
  out.remove = { at: SF.at, pieces: SF.pieces, said: said.slice() };
  said.length = 0;
  SF.at = 1;
  answer = { undone: { rec_id: 'O1', stage: 'ta', n: 6 } };
  sfUndo();
  await last;
  out.decision = { at: SF.at, said: said.slice() };
  console.log(JSON.stringify(out));
})();
"""
        uscript = base / "excerpt-undo-139.js"
        uscript.write_text(undo.replace("__UNDO__", whole(sjs, "sfUndo")), encoding="utf-8")
        ran = subprocess.run([node, str(uscript)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        uout = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        why = (ran.stderr or json.dumps(uout))[:700]
        check("139: in node, Undo of an excerpt kept goes to its record at either stage and leaves its words marked so H keeps "
              "it again, Undo of one removed brings it back, and a decision's undo at the other stage stays as it was",
              {k: v for k, v in uout.get("add", {}).items() if k != "said"}
              == {"at": 0, "pieces": [{"in": "abstract", "start": 20, "end": 26}], "for": "O1"}
              and uout.get("remove", {}).get("at") == 0 and uout.get("remove", {}).get("pieces") == []
              and uout.get("decision", {}).get("at") == 1
              and all(len(uout.get(k, {}).get("said") or []) == 1 for k in ("add", "remove", "decision")), why)
