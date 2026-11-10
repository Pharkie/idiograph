from __future__ import annotations

import csv
import json
import shutil

from . import support
from .support import check, sift_words_js, skip


def test_sift_plain_words(scratch):
    print("\n137. Sift's words reworded, 14 October, later, by Adam's dialog: a block's lines under a heading of two "
          "lines in the filters, More than one among its terms, the databases joined A, B or C, one sentence for each "
          "block a record holds none of, on the record and the command line, the Matched in column in the filters' own "
          "words, and Cites key works saying Can't check where it said Unknown, with the record's reason. Since the test "
          "review of 18 October the sentences, the heading and the docs are review shots, and which databases a record's "
          "lines name, the filters' counts and a record that cannot be checked told from one that cites none stay")
    import subprocess
    import sift
    import sift_search as ss
    import cli as cli_mod
    import sift_cli

    app_src = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    sift_src = support.text("apps/sift/static/sift.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    node = shutil.which("node")
    base = scratch / "sift-words-137"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)

    # ── A. the words, on an invented review of canal boat dwellers: Europe PMC searches the first block in methods
    # sections, Scopus, Web of Science and PubMed their keyword fields, Google Scholar the full text, OpenAlex the
    # title and abstract alone
    review = base / "canal-review"
    review.mkdir()
    ss.new_plan(review, "Canal boat dwellers", "How do boaters live afloat?")
    dbs = ["scopus", "wos", "pubmed", "epmc", "openalex", "scholar"]
    ss.save(review, {"databases": dbs, "blocks": [
        {"name": "Boats", "terms": ["narrowboat*", "barge", "houseboat", "liveaboard*"], "scope": "tak", "scopes": {"epmc": "methods"}},
        {"name": "Living", "terms": ["home*"]}]})
    run = review / "runs" / "2031-08-01"
    run.mkdir(parents=True)
    (run / ss.RUN_FILE).write_text(json.dumps({"version": 1, "sources": {s: {"name": ss.NAMES[s]} for s in dbs}}),
                                   encoding="utf-8")
    rows = [("C1", "Locks and lives", "Families moved along the water.", "Europe PMC"),
            ("C2", "Mooring rights", "Owners spoke of fees.", "Scopus; Web of Science; PubMed"),
            ("C3", "Winter on the cut", "", "OpenAlex"),
            ("C4", "Towpath talk", "Neighbours met daily.", "Google Scholar"),
            ("C5", "Water and work", "Workers spoke of tides.", "OpenAlex"),
            ("C6", "A narrowboat home", "Living on a barge.", "Scopus"),
            ("C7", "Houseboat life", "Daily routines.", "Scopus; PubMed")]
    with open(run / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["rec_id", "title", "authors", "year", "journal", "doi", "sources", "abstract"])
        for i, (rec, title, abstract, sources) in enumerate(rows, 1):
            w.writerow([rec, title, "Lock, Wren", str(2020 + i), "Invented Waterways Journal", f"10.5555/canal.{i}", sources, abstract])
    view = sift.screen(run)
    rec = {r["rec_id"]: r for r in view["records"]}
    lines = lambda r, k="term:0": [w["label"] for w in rec[r]["matched"][k]["why"]]
    check("137: each line in Adam's words, from a stubbed record of each kind: Europe PMC methods sections, the keywords "
          "of the databases that found it, Google Scholar full text, the abstract, which Sift does not hold, and a field "
          "Sift cannot name",
          lines("C1") == ["Europe PMC methods sections"] and lines("C2") == ["Scopus, Web of Science or PubMed keywords"]
          and lines("C3") == ["the abstract, which Sift does not hold"] and lines("C4") == ["Google Scholar full text"]
          and lines("C5") == ["a field Sift cannot name"] and lines("C7", "term:1") == ["Scopus or PubMed keywords"]
          and lines("C1", "term:1") == ["Europe PMC keywords"], str([lines(r) for r in ("C1", "C2", "C3", "C4", "C5")]))
    check("137: the databases are joined A, B or C, or before the last, and naming only the databases that found the record",
          [sift.or_join(x) for x in ([], ["Scopus"], ["Scopus", "PubMed"], ["Scopus", "Web of Science", "PubMed"])]
          == ["", "Scopus", "Scopus or PubMed", "Scopus, Web of Science or PubMed"]
          and lines("C6", "term:1") == [] and rec["C6"]["terms"]["term:0"] == ["narrowboat*", "barge"]
          and view["blocks"][0]["why"] == [{"value": "|methods", "label": "Europe PMC methods sections"},
                                           {"value": "|keywords", "label": "Scopus, Web of Science or PubMed keywords"},
                                           {"value": "|fulltext", "label": "Google Scholar full text"},
                                           {"value": "|noabstract", "label": "the abstract, which Sift does not hold"},
                                           {"value": "|none", "label": "a field Sift cannot name"}], str(view["blocks"][0]["why"]))
    works = [{"key": "W1", "label": "Life afloat (2019)"}]
    facts = lambda cites: [x for x in sift_cli.facts_lines(dict(rec["C1"], cites=cites), works) if x.startswith("Cites key works")]
    check("137: the command line says why for key works Sift cannot check, the record's own sentence, none and the works "
          "it cites as before",
          facts(None) == ["Cites key works: Crossref holds no reference list for this record, so Sift cannot check."]
          and facts([]) == ["Cites key works: none."] and facts(["W1"]) == ["Cites key works: Life afloat (2019)."]
          and "Retracted or corrected: unknown." in sift_cli.facts_lines(dict(rec["C1"], cites=None), works), str(facts(None)))

    # ── B. the page: the filter, the record and the column, in node
    if not node:
        skip("137: the filter, the record and the column in node", "node is not installed")
    else:
        lead = app_src[app_src.index("const esc = "):app_src.index("// a line from the server with a command in backticks")]
        block = sift_src.split("/* ── the table's rows: its columns, sort and filter, worked out with no page ── */", 1)[-1].split(
            "/* ── the table, drawn ── */", 1)[0]
        block = support.table_js() + "\n" + block
        drawn = [whole(sift_src, n) for n in ("sfTvCell", "sfTermsDraw", "sfFactsDraw")]
        harness = r"""
const els = {};
const mk = () => ({ hidden: false, innerHTML: '', textContent: '', title: '', dataset: {}, style: {}, setAttribute() {} });
const $ = (id) => els[id] || (els[id] = mk());
const VIEW = __VIEW__;
// what OpenAlex and Crossref said, set here on the invented records: the key works one cites, none, or that
// Sift cannot check, and open access for two
const cites = { C1: ['W1'], C2: [], C3: null, C4: null, C5: [], C6: ['W1'], C7: null };
VIEW.records.forEach((r) => { r.cites = cites[r.rec_id]; r.oa = r.rec_id === 'C1' ? 'gold' : r.rec_id === 'C2' ? 'closed' : ''; });
const SF = { stage: 'ta', filters: {}, table: VIEW.table, records: VIEW.records, blocks: VIEW.blocks, matchHead: VIEW.match_head,
  keyWorks: [{ key: 'W1', label: 'Life afloat (2019)' }], reasons: { ta: [], ft: [] }, roundIds: VIEW.records.map((r) => r.rec_id),
  form: false, formBench: new Set(), formInc: new Set(), facetsMore: new Set(), facetsFind: {} };
SF.byId = new Map(SF.records.map((r) => [r.rec_id, r]));
const by = (ids) => ids.map((id) => SF.byId.get(id));
const cols = sfAllCols();
const out = {};
const drawn = (rows, filters) => {
  const groups = sfGroups(rows, SF.records, cols, 'ta', [], filters);
  const counts = tbFacetCounts(rows, groups, filters, sfRead('ta'));
  const g = groups.find((x) => x.key === 'term:0');
  g.choices = sfFacetOrder(g, counts['term:0']);
  SF.filters = filters;
  const html = tbGroupHtml(g, counts['term:0'], 0, SF);
  SF.filters = {};
  return { order: g.choices.map((c) => [c.value, c.label, counts['term:0'][c.value] || 0]), html, groups, counts };
};
const all = drawn(SF.records, {});
out.order = all.order;
out.html = all.html;
out.noLines = drawn(by(['C6', 'C7']), {}).html;
out.tickedNought = drawn(by(['C6', 'C7']), { 'term:0': ['|methods'] }).html;
out.some = drawn(by(['C1', 'C5', 'C6']), {});
out.some = { order: out.some.order, html: out.some.html };
SF.facetsMore.add('term:0');
out.whole = drawn(SF.records, {}).html;
SF.facetsMore.clear();
const kg = all.groups.find((x) => x.key === 'keyworks');
const og = all.groups.find((x) => x.key === 'oa');
out.keyworks = kg ? kg.choices.map((c) => [c.value, c.label]) : null;
out.oa = og ? og.choices.map((c) => [c.value, c.label]) : null;
out.cantCheck = tbFilterRows(SF.roundIds, SF.byId, { keyworks: ['|none'] }, cols, sfRead('ta'));
const kcol = cols.find((c) => c.key === 'keyworks');
out.kcell = ['C3', 'C2', 'C1'].map((id) => sfTvCell(SF.byId.get(id), kcol));
sfFactsDraw(SF.byId.get('C3'));
out.facts3 = $('sf-facts').innerHTML;
sfFactsDraw(SF.byId.get('C2'));
out.facts2 = $('sf-facts').innerHTML;
out.pane = {};
['C1', 'C3', 'C4', 'C5', 'C6', 'C7'].forEach((id) => { sfTermsDraw(SF.byId.get(id)); out.pane[id] = $('sf-terms').innerHTML; });
const mcol = cols.find((c) => c.key === 'matched');
out.col = ['C2', 'C3', 'C6', 'C7'].map((id) => sfValue(SF.byId.get(id), mcol, 'ta'));
out.cell = sfTvCell(SF.byId.get('C1'), mcol);
console.log(JSON.stringify(out));
"""
        script = base / "words-137.js"
        script.write_text("\n".join([lead, sift_words_js(sift_src), block, *drawn,
                                     harness.replace("__VIEW__", json.dumps(view))]), encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        why = (ran.stderr or json.dumps(out))[:600]
        check("137: in node, the block's group lists its terms by their counts, More than one, then the lines by their "
              "counts among themselves, a tie in the group's order",
              out.get("order") == [["narrowboat*", "narrowboat*", 1], ["barge", "barge", 1], ["houseboat", "houseboat", 1],
                                   ["liveaboard*", "liveaboard*", 0], ["|many", "More than one", 1],
                                   ["|methods", "Europe PMC methods sections", 1],
                                   ["|keywords", "Scopus, Web of Science or PubMed keywords", 1],
                                   ["|fulltext", "Google Scholar full text", 1],
                                   ["|noabstract", "the abstract, which Sift does not hold", 1],
                                   ["|none", "a field Sift cannot name", 1]], why)
        some = out.get("some", {})
        check("137: in node, the lines take the counts the filters leave, those at nought faint and last among the lines "
              "and not to be ticked, the heading kept while one holds a record",
              [c[0] for c in some.get("order", [])][-5:] == ["|methods", "|none", "|keywords", "|fulltext", "|noabstract"]
              and 'data-v="|fulltext" disabled>' in some.get("html", ""), json.dumps(some.get("order")))
        check("137: in node, Cites key works says Can't check in its filter and its column, Open access and the others keep "
              "Unknown, and the records that cannot be checked stand under it",
              out.get("keyworks") == [["W1", "Life afloat (2019)"], ["none", "None"], ["|none", "Can't check"]]
              and out.get("oa") == [["open", "Open"], ["closed", "Closed"], ["|none", "Unknown"]]
              and out.get("cantCheck") == ["C3", "C4", "C7"], why)
