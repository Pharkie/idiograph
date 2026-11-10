from __future__ import annotations

import csv
import io
import json
import os
import shutil

from . import support
from .support import SPARKLES, check, refusal_of, sift_words_js, skip, urllib_path


def lantern_stub(state: dict):
    """A stand-in OpenAlex for area 121, on an invented topic, lighthouse keepers: /works by DOI answers
    each DOI it knows with its abstract, authors and count of citations, and every query is kept under
    `asked`."""
    import http.server
    import urllib.parse as up

    known = {"10.5555/lamp.1": {"cited_by_count": 0, "authorships": [{"author": {"display_name": "Ida Gannet"}},
                                                                      {"author": {"display_name": "Ned Tern"}}]},
             "10.5555/lamp.2": {"cited_by_count": 41},
             "10.5555/lamp.3": {"cited_by_count": 1250, "abstract_inverted_index": {"Keepers": [0], "wrote": [1], "logs.": [2]}}}

    class Stub(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            url = up.urlparse(self.path)
            q = {k: v[0] for k, v in up.parse_qs(url.query).items()}
            state.setdefault("asked", []).append((url.path, q))
            dois = q.get("filter", "")[4:].split("|") if q.get("filter", "").startswith("doi:") else []
            results = [dict({"id": "https://openalex.org/W" + d[-1], "doi": "https://doi.org/" + d}, **known[d])
                       for d in dois if d in known]
            body = json.dumps({"results": results, "meta": {"count": len(results)}}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Stub


@support.as_app("sift")
def test_sift_from_use(scratch):
    print("\n121. Sift's screening from use, 12 October: one Export menu, Filters and Columns off the bar, one decision "
          "filter, the screening stage, Unknown not none, Database, My rating, the columns at first, the sidebar's width, "
          "Cited by from OpenAlex, reasons in one place, and a run's databases and drops")
    import http.server
    import subprocess
    import threading
    import server as server_mod
    import sift_routes
    import sift
    import sift_search as ss

    page = support.page_text()
    sjs = support.text("apps/sift/static/sift.js")
    ssjs = support.text("apps/sift/static/sift_search.js")
    # Sift's styles as its page loads them, the frame it shares with Trace first (tracestyle, 30 October 2026)
    scss = support.text("family/static/frame.css", "apps/sift/static/sift.css")
    sscss = support.text("apps/sift/static/sift_search.css")
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    # the server's and, since the family codebase's third build, Sift's own routes
    server_src = "\n".join(support.source(p).read_text(encoding="utf-8") for p in ("server.py", "apps/sift/sift_routes.py"))
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    node = shutil.which("node")
    base = scratch / "sift-from-use-121"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    rail = page.split('<div class="rail sf-rail">', 1)[1].split('<div class="sf-main"', 1)[0]
    screen = page.split('<section id="sift"', 1)[1].split("</section>", 1)[0]

    def keepers(folder: Path, n: int = 8) -> Path:
        """An invented screening on lighthouse keepers: years, a missing one, DOIs, counts of citations
        and the review's proposals."""
        folder.mkdir(parents=True, exist_ok=True)
        with open(folder / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["rec_id", "title", "authors", "year", "journal", "doi", "sources", "abstract", "proposed_decision",
                        "proposed_reason", "grounds"])
            for i in range(1, n + 1):
                w.writerow([f"L{i:02d}", f"Keeping the light {i}", "Gannet, I.", "" if i == 4 else str(2010 + i),
                            "Invented Lamp Review" if i % 2 else "Invented Quarterly of Remarkably Long Names in Coastal Life",
                            f"10.5555/lamp.{i}", "Index A; Index B" if i % 3 == 0 else "Index A",
                            f"Keepers spoke of the lamp {i}.", "include" if i % 2 else "exclude", "" if i % 2 else "K1", ""])
        (folder / sift.REASONS_NAME).write_text("stage,code,meaning\nta,K1,Not about keepers\n", encoding="utf-8")
        return folder

    # ── A. one Export menu on the title bar, its three items, and the counts it writes
    check("121: the menu opens under its button, its first item that can be pressed taking the focus, the arrows, Home and "
          "End move in it, Esc and Tab shut it, a press beside it shuts it, and each item shuts it as its work starts",
          "menu.style.top = `${Math.round(at.bottom + 4)}px`;" in fn(sjs, "sfMenuOpen") and "if (first) first.focus();" in fn(sjs, "sfMenuOpen")
          and "btn.setAttribute('aria-expanded', 'true');" in fn(sjs, "sfMenuOpen")
          and all(f"e.key === '{k}'" in fn(sjs, "sfMenuKey") for k in ("ArrowDown", "ArrowUp", "Home", "End", "Escape", "Tab"))
          and "if (sfMenuKey(e)) return;" in fn(sjs, "sfKeyDown")
          and fn(sjs, "sfKeyDown").index("if (sfMenuKey(e)) return;") < fn(sjs, "sfKeyDown").index("if (!$('sf-keys').hidden)")
          and "$('sf-counts').onclick = () => sfMenuTake(sfExport);" in sjs and "$('sf-zotero').onclick = () => sfMenuTake(sfZotOpen);" in sjs
          and "!e.target.closest('#sf-export-menu, #sf-export')" in sjs and "sfMenuOpen(false, false);" in fn(sjs, "sfMenuTake")
          and ".filter((b) => !b.disabled)" in sjs)
    check("121: Export PRISMA counts writes the flow's numbers as screening.counts.csv through the export op, Export "
          "included records stays off with none accepted at full text, and Export to Zotero keeps its card and work, "
          "its name and its words Export and Exporting alone changed",
          "{ op: 'export', folder: SF.folder }" in fn(sjs, "sfExport") and "$('sf-included').disabled = !(ft && Number(ft.include));" in fn(sjs, "sfBar")
          and '<h2 id="sf-zot-head">Export to Zotero</h2>' in page and "z.running ? 'Exporting' : 'Export'" in fn(sjs, "sfZotDraw")
          and "op: 'sync'" in fn(sjs, "sfZotGo")
          # the Zotero sync's words in Sift's catalogue since siftlang (1 November 2026)
          and "Export again." in support.text("apps/sift/static/i18n/en/sift_server.json")
          and "Sync again" not in support.text("apps/sift/sift_zotero.py", "apps/sift/static/i18n/en/sift_server.json"))
    counted = keepers(base / "counted")
    sift.decide(counted, "L01", "ta", "include")
    wrote = sift.export(counted)
    rows = list(csv.reader(io.StringIO((counted / sift.COUNTS_NAME).read_text(encoding="utf-8"))))
    check("121: in a screening, Export PRISMA counts writes screening.counts.csv beside it, a row a measure",
          wrote["written"] and rows[0] == ["stage", "measure", "count"] and ["title and abstract", "include", "1"] in rows, str(rows[:3]))

    # ── C. one decision filter: the round dropdown gone, Differs and Where we differ ticks, an old round read in
    marks = keepers(base / "marks")
    sift.decide(marks, "L01", "ta", "exclude", "K1")
    sift.decide(marks, "L02", "ta", "exclude", "K1")
    view = sift.screen(marks)
    by = {r["rec_id"]: r for r in view["records"]}
    check("121: the server marks a record whose decision differs from the proposal it stood against, at each stage, and "
          "one that agrees or is undecided not",
          by["L01"]["stages"]["ta"]["differs"] is True and by["L02"]["stages"]["ta"]["differs"] is False
          and by["L03"]["stages"]["ta"]["differs"] is False and by["L01"]["stages"]["ft"]["differs"] is False)
    check("121: the round's dropdown is gone from the page, its script and its styles, the screen asks list for every "
          "record of the stage, and the old round this browser kept is read once into the Decision filter",
          'id="sf-round"' not in page and "SF_ROUNDS" not in sjs and "sfRounds" not in sjs and ".sf-round" not in scss
          and "{ op: 'list', folder: SF.folder, stage: SF.stage, round: 'all' }" in fn(sjs, "sfRound")
          and "const SF_ROUND_TICKS = { undecided: 'undecided', maybe: 'maybe', accepted: 'include', rejected: 'exclude',"
          in sjs and "differs: 'differs', apart: 'apart' };" in sjs
          and "if (tick && !SF.filters.decision && decision && decision.choices.some((c) => c.value === tick)) SF.filters.decision = [tick];"
          in fn(sjs, "siftOpen") and "round:" not in fn(sjs, "sfKeepPlace")
          and "SF.filters.decision = [SF_APART];" in sjs)
    block = sjs.split("/* ── the table's rows: its columns, sort and filter, worked out with no page ── */", 1)[-1].split(
        "/* ── the table, drawn ── */", 1)[0]
    block = support.table_js() + "\n" + block
    lead = app[app.index("const esc = "):app.index("// a line from the server with a command in backticks")]
    if node and "function sfGroups(" in block:
        probe = scratch / "sift-from-use-121.js"
        probe.write_text("\n".join([block, lead, sift_words_js(sjs), "const SF = { filters: {} };",
                                    "function sfMeaning() { return ''; }"])
                         + "\nconst data = " + json.dumps({"records": view["records"], "table": view["table"],
                                                           "codes": view["reasons"]["ta"]}) + ";\n" + r"""
const rows = data.records;
const cols = sfColumns(data.table);
const dec = (list) => (sfGroups(list, list, cols, 'ta', data.codes, {}).find((g) => g.key === 'decision') || { choices: [] }).choices.map((c) => c.value);
const plainRows = JSON.parse(JSON.stringify(rows));
const offered = dec(plainRows);
rows.forEach((r) => { r.stages.ta.proposed = (r.stages.ta.proposals || []).length > 0; r.stages.ta.apart = r.rec_id === 'L02'; });
const withMarks = dec(rows);
const byId = new Map(rows.map((r) => [r.rec_id, r]));
const ids = rows.map((r) => r.rec_id);
const kept = (f) => tbFilterRows(ids, byId, f, cols, sfRead('ta'));
const out = {
  offered, withMarks,
  differs: kept({ decision: ['differs'] }), apart: kept({ decision: ['apart'] }),
  rejectedOrDiffers: kept({ decision: ['exclude', 'differs'] }),
  picked: sfPicked(byId.get('L01'), cols.find((c) => c.key === 'decision'), 'ta'),
  bars: sfBarSpans('cited', 0, 1250).map((b) => b.label),
  citedGroup: (sfGroups(rows, rows, cols, 'ta', [], {}).find((g) => g.key === 'cited') || {}),
  ratingGroup: (sfGroups(rows, rows, cols, 'ta', [], {}).find((g) => g.key === 'rating') || {}),
  yearGroup: (sfGroups(rows, rows, cols, 'ta', [], {}).find((g) => g.key === 'year') || {}),
  noCount: kept({ cited: { from: null, to: null, none: true } }),
  blank: ['year', 'participants', 'rating', 'cited'].map(sfBlankHtml),
  day: tbDayWords('2026-10-12'),
  title: sfCitedTitle({ cited_date: '2026-10-12' }),
  cols: cols.filter((c) => c.shown).map((c) => [c.key, c.label]),
};
out.citedGroup = { low: out.citedGroup.low, high: out.citedGroup.high, choices: out.citedGroup.choices };
out.ratingGroup = { low: out.ratingGroup.low, high: out.ratingGroup.high, choices: out.ratingGroup.choices };
out.yearGroup = { choices: out.yearGroup.choices };
console.log(JSON.stringify(out));
""", encoding="utf-8")
        ran = subprocess.run([node, str(probe)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        why = (ran.stderr or ran.stdout)[:300]
        check("121: in node, Decision offers To screen and the stage's three decisions and the reasons, with Differs from the "
              "proposal only while a record shows a proposal and Where we differ only while the second screener's side holds "
              "a difference",
              out.get("offered") == ["undecided", "include", "maybe", "exclude", "exclude:K1"]
              and out.get("withMarks") == ["undecided", "include", "maybe", "exclude", "exclude:K1", "differs", "apart"], why)
        check("121: in node, the ticks pass the records whose decision differs from the proposal, those where the screeners "
              "differ, and widen with No as any two ticks of one group do",
              out.get("differs") == ["L01"] and out.get("apart") == ["L02"] and out.get("rejectedOrDiffers") == ["L01", "L02"]
              and out.get("picked") == ["exclude", "exclude:K1", "differs"], why)
        check("121: in node, Cited by is a slider from the lowest count to the highest, nought among them, with No count under "
              "it, its bars nought, 1 to 5, 6 to 10, 11 to 25 and wider to 1001 and over",
              out.get("citedGroup") == {"low": None, "high": None, "choices": [{"value": "|none", "label": "No count"}]}
              and out.get("bars") == ["0", "1–5", "6–10", "11–25", "26–50", "51–100", "101–250", "251–500", "501–1000", "1001 and over"]
              and len(out.get("noCount") or []) == 8, why)
        check("121: in node, a record with nothing reads No year, Unknown, Not rated or No count, in the faint ink, and My "
              "rating runs from one star to five with Not rated under it",
              out.get("blank") == ['<span class="sf-blank">No year</span>', '<span class="sf-blank">Unknown</span>',
                                   '<span class="sf-blank">Not rated</span>', '<span class="sf-blank">No count</span>']
              and out.get("ratingGroup") == {"low": 1, "high": 5, "choices": [{"value": "|none", "label": "Not rated"}]}
              and out.get("yearGroup") == {"choices": [{"value": "|none", "label": "No year"}]}, why)
        check("121: in node, the columns at first read Database, Title, Authors, Year, Cited by, No. of participants, PDF, "
              "Decision and My rating, Abstract and DOI hidden, and a count's day reads in words on hover",
              out.get("cols") == [["found", "Database"], ["title", "Title"], ["authors", "Authors"], ["year", "Year"],
                                  ["cited", "Cited by"], ["participants", "No. of participants"], ["pdf", "PDF"],
                                  ["decision", "Decision"], ["rating", "My rating"]]
              and out.get("day") == "12 October 2026" and out.get("title") == ' title="From OpenAlex, 12 October 2026"', why)
    else:
        skip("121: the decision filter and the sliders in node", "no node on this machine")
    check("121: the marks the filters read are set on every record as the screening is read and as each answer lands, "
          "proposed only with the app's AI switch on",
          "sfMarkAll();" in fn(sjs, "sfTake") and "if (data.second) sfMarkAll();" in fn(sjs, "sfLand")
          and "else if (data.record) sfMark(data.record);" in fn(sjs, "sfLand") and "sfMark(r);" in fn(sjs, "sfLandProposal")
          and "SF.aiMaster" not in block and "sfTwoOn" not in block)

    # ── D. the screening stage, labelled, Full text once a record has passed
    check("121, updated 12 October (122): the stages stand in the review's steps, the words Screening stage gone, each "
          "with its count, and Full text greyed until a record has passed title and abstract, a screening opening at "
          "title and abstract while none has",
          "Screening stage" not in rail and 'id="sf-steps"' in rail and "sfFtOn" in fn(sjs, "sfStageTo")
          and "rvStepsDraw($('sf-steps'), SF.review, SF.form ? 'ex' : SF.stage, all);" in fn(sjs, "sfBar")
          and "SF.stage = SF.form || ((stage || kept.stage) === 'ft' && sfFtOn()) ? 'ft' : 'ta';" in fn(sjs, "siftOpen")
          and "const ft = step === 'ft' || step === 'ex' || (ta && n('ft') > 0);" in ssjs)

    # ── E. Unknown is not none: nought kept, a blank shown as Unknown
    zero = keepers(base / "zero")
    sift.set_field(zero, "L01", "participants", "0")
    sift.set_field(zero, "L02", "participants", "")
    zf = {r["rec_id"]: r["fields"] for r in sift.screen(zero)["records"]}
    check("121: nought participants is a count of its own, written as 0 and confirmed, and a count left blank is no count, "
          "which the screen reads as Unknown",
          zf["L01"]["participants"] == "0" and zf["L01"]["confirmed"] is True and zf["L02"]["participants"] == ""
          and zf["L02"]["confirmed"] is True and refusal_of(lambda: sift.set_field(zero, "L03", "participants", "-2"))
          == "Participants is a whole number, or none.", str(zf["L01"]))

    # ── H. the columns at first, and columns placed before them
    first = [(c["key"], c["shown"]) for c in sift.table_settings(zero)["columns"]][:10]
    old = keepers(base / "old")
    (old / sift.SETTINGS_NAME).write_text(json.dumps({"table": {"columns": [{"key": "title", "shown": True},
                                                                            {"key": "abstract", "shown": True},
                                                                            {"key": "doi", "shown": True}]}}), encoding="utf-8")
    hidden_once = {c["key"]: c["shown"] for c in sift.table_settings(old)["columns"]}
    sift.save_view(old, columns=[{"key": "abstract", "shown": True}])
    shown_again = {c["key"]: c["shown"] for c in sift.table_settings(old)["columns"]}
    held = json.loads((old / sift.SETTINGS_NAME).read_text(encoding="utf-8"))["table"]
    check("121: the abstract and the DOI are hidden at first, Cited by shown after Year, and both stay in Columns and on "
          "the record",
          first[:6] == [("found", True), ("title", True), ("authors", True), ("year", True), ("cited", True), ("abstract", False)]
          and ("doi", False) in first and "doi: { label: 'DOI', kind: 'text' }," in sjs
          and "if (r.doi) links.push(" in fn(sjs, "sfDraw"), str(first))
    check("121: a screening whose columns were placed before 12 October takes the abstract and the DOI off once, and "
          "what he shows after that stands, sift.json marking the columns placed now",
          hidden_once["abstract"] is False and hidden_once["doi"] is False and hidden_once["title"] is True
          and shown_again["abstract"] is True and shown_again["doi"] is False and held.get("first") == sift.FIRST == 2,
          str(held))

    # ── I. the sidebar: a name whole on hover, its edge dragged, its width kept per screening
    kept_w = sift.save_view(zero, sidebar=333.6)
    wide = sift.save_view(zero, sidebar=9000)
    check("121: the sidebar's width is kept in sift.json per screening, a whole number within 180 and 560 pixels, and "
          "anything but a number refused",
          kept_w["sidebar"] == 334 and wide["sidebar"] == 560 and sift.table_settings(old)["sidebar"] is None
          and refusal_of(lambda: sift.save_view(zero, sidebar="wide")) == "The sidebar's width is a number of pixels."
          and json.loads((zero / sift.SETTINGS_NAME).read_text(encoding="utf-8"))["table"]["sidebar"] == 560)
    check("121, updated 12 October (122): the sidebar's right edge drags wider or narrower and moves by the arrows, by the "
          "code the flow's edge shares, its width kept through the view op and put back as a screening opens",
          'id="sf-facets-edge" role="separator" aria-orientation="vertical" aria-controls="sf-facets"' in screen
          and "edge.setPointerCapture(e.pointerId);" in fn(sjs, "sfEdgeBoot")
          and "sfQueue(() => api('/api/sift', { op: 'view', folder, sidebar: { [s.op]: width } }));" in fn(sjs, "sfEdgeKeep")
          and "if (width) box.style.setProperty(s.prop, `${width}px`);" in fn(sjs, "sfEdgeWidth") and "prop: '--sf-facets-w'" in sjs
          and "if (sfEdgeKey(e)) return;" in fn(sjs, "sfKeyDown") and "sfEdgeWidth('facets', table.sidebar);" in fn(sjs, "siftOpen")
          and "sidebar=body.get(\"sidebar\")" in server_src)

    # ── J. Cited by from OpenAlex, at a run and for a screening made before, against a stub on loopback
    state = {}
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), lantern_stub(state))
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    stub = f"http://127.0.0.1:{httpd.server_address[1]}"
    ctx = lambda: ss.Context(base={s: stub + urllib_path(u) for s, u in ss.ENDPOINTS.items()}, pause=lambda s: None)
    kept_runner, kept_env, kept_clock = ss.RUNNER, os.environ.pop(ss.STUB_ENV, None), ss.CLOCK

    def no_keys(argv, **_):
        return subprocess.CompletedProcess(argv, 44, "", "")

    ss.RUNNER = no_keys
    ss.CLOCK = lambda: __import__("datetime").date(2031, 6, 1)
    try:
        rec = lambda doi, authors="Gannet, I.", abstract="Kept.": {"title": "T", "authors": authors, "year": "2020", "journal": "",
                                                                    "doi": doi, "abstract": abstract, "pub_type": "", "url": "",
                                                                    "sources": ["Index A"], "abstract_from": "Index A"}
        merged = [rec("10.5555/lamp.1"), rec("10.5555/lamp.2", "Gannet, I.; Tern, N."), rec("10.5555/lamp.3", abstract=""),
                  rec(""), rec("10.5555/lamp.9")]
        filled = ss.fill_from_openalex(ctx(), merged)
        # updated 13 October (128): Crossref's requests go to the same stub under a path of their own, and the
        # fill answers its counts by name, the columns of 13 October joining the same select
        asks = [q for p, q in state.get("asked", []) if p == "/works"]
        check("121, updated 13 October (128): a run asks OpenAlex for every record with a DOI in the same batched request "
              "as the abstracts and the authors, its select gaining cited_by_count, and writes each count with the day it "
              "was asked, nought among them",
              (filled["abstracts"], filled["authors"], filled["cited"]) == (1, 1, 3) and len(asks) == 1
              and asks[0].get("select") == ss.FILL_FIELDS
              and ss.FILL_FIELDS.startswith("id,doi,abstract_inverted_index,authorships,cited_by_count")
              and asks[0].get("filter") == "doi:10.5555/lamp.1|10.5555/lamp.2|10.5555/lamp.3|10.5555/lamp.9"
              and [m.get("cited_by") for m in merged] == ["0", "41", "1250", None, None]
              and merged[0].get("cited_by_date") == "2031-06-01" and merged[2]["abstract"] == "Keepers wrote logs."
              and merged[0]["authors"] == "Ida Gannet; Ned Tern", str(filled) + str(asks)[:300])
        text = ss.screening_text(ss.ordered(merged))
        head = next(csv.reader(io.StringIO(text)))
        check("121: a run's screening.csv gains Cited by and its date after the abstract, Sift's own two columns",
              head[9:12] == ["abstract", "cited_by", "cited_by_date"] and "1250,2031-06-01" in text, str(head))
        r = {"date": "2031-06-01", "rows": [], "records": 5, "merged": 5, "filled": 1, "authors_filled": 1, "cited_filled": 3}
        check("121: the run's line says how many counts of citations were filled, and run.json keeps them as cited_filled",
              any(line.endswith("1 abstract filled from OpenAlex, the authors of 1 record, and the citation counts of 3 records.")
                  for line in ss.run_lines(r))
              and "cited_filled=cited" in support.source("apps/sift/sift_search.py").read_text(encoding="utf-8")
              and "cited ? t('sift_search.filled.cited', { n: cited }) : ''" in fn(ssjs, "sfsFilled"), str(ss.run_lines(r)))
        before = keepers(base / "before")
        sift.decide(before, "L02", "ta", "include", note="A note kept.")
        original = {k: v for k, v in sift.load(before).record("L02").items()}
        plan = ss.citation_plan(before)
        state["asked"] = []
        first_batch = ss.find_citations(before, 0, ctx())
        after = sift.load(before)
        check("121: Find citation counts asks for every record with a DOI, fifty a request, and writes each count found with "
              "the day into Sift's own cited_by and cited_by_date, every other cell kept",
              plan == {"ids": [f"L{i:02d}" for i in range(1, 9)], "of": 8, "records": 8}
              and first_batch == {"at": 8, "of": 8, "records": 8, "asked": 8, "filled": 3, "said": ""}
              and [after.cell(k, "cited_by") for k in ("L01", "L02", "L03", "L04")] == ["0", "41", "1250", ""]
              and after.cell("L03", "cited_by_date") == "2031-06-01"
              and all(after.cell("L02", k) == v for k, v in original.items())
              and state["asked"][0][1].get("select") == "id,doi,cited_by_count", str(first_batch))
        done = ss.find_citations(before, 8, ctx())
        view_c = {r["rec_id"]: r for r in sift.screen(before)["records"]}
        check("121: a batch past the last asks nothing, and the record carries its count and day as Cited by, the review's "
              "columns and the log untouched",
              done["asked"] == 0 and done["filled"] == 0 and view_c["L03"]["cited"] == 1250 and view_c["L01"]["cited"] == 0
              and view_c["L04"]["cited"] is None and view_c["L03"]["cited_date"] == "2031-06-01"
              and not any(e.get("act") == "field" for e in sift.read_lines(before))
              and all(name not in [m[0] for m in view_c["L03"]["more"]] for name in ("cited_by", "cited_by_date")))
        kept_state = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
        config_file = base / "config.json"
        config_file.write_text(json.dumps({"interviewer": "Adam"}), encoding="utf-8")
        os.environ[ss.STUB_ENV] = stub
        try:
            server_mod.CONFIG_PATH = config_file
            server_mod.ROOT_OVERRIDE = str(base)
            server_mod.STATE_MEMORY = {"recent": []}
            through = keepers(base / "through")
            sift_routes.api_sift_review({"op": "open", "folder": str(through)})
            p_ = sift_routes.api_sift({"op": "cited_plan", "folder": str(through)})
            c_ = sift_routes.api_sift({"op": "cited", "folder": str(through), "at": 0})
            v_ = sift_routes.api_sift({"op": "view", "folder": str(through), "sidebar": 250})
        finally:
            (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY) = kept_state
            os.environ.pop(ss.STUB_ENV, None)
        check("121: through the server, cited_plan names the records with a DOI and cited asks the stub on loopback and "
              "writes their counts, and view keeps the sidebar's width",
              p_["of"] == 8 and c_["filled"] == 3 and c_["at"] == 8 and sift.load(through).cell("L02", "cited_by") == "41"
              and v_["table"]["sidebar"] == 250, str(c_))
        drops = base / "drops"
        drops.mkdir()
        ss.save(drops, {"databases": ["psycinfo"], "blocks": [{"name": "Keepers", "terms": ["keeper*"]}]})
        day = "2031-06-02"
        for name in (day, f"{day}-2"):
            (drops / "runs" / name).mkdir(parents=True)
            (drops / "runs" / name / ss.RUN_FILE).write_text(json.dumps({"version": 1, "date": day, "sources": {
                "psycinfo": {"name": "PsycInfo", "state": "awaiting", "how": "export"}}}), encoding="utf-8")
        ris = "TY  - JOUR\nTI  - Lamps at dusk\nPY  - 2020\nDO  - 10.5555/lamp.40\nER  - \n"
        took2 = ss.take_export(drops, "psycinfo", ris.encode(), "p.ris", day=day, run=f"{day}-2", ctx=ctx())
        stale = refusal_of(lambda: ss.take_export(drops, "psycinfo", ris.encode(), "p.ris", day=day, run=day,
                                                  ctx=ctx()))
        check("121: a drop goes into the run the screen shows, the second of the day, never the first, and a drop that names "
              "an earlier run of the day than the newest is refused in one line, nothing written there",
              took2["date"] == f"{day}-2" and (drops / "runs" / f"{day}-2" / "psycinfo.ris").is_file()
              and not (drops / "runs" / day / "psycinfo.ris").exists()
              and stale == "The run of 2 June 2031, run 2 came after the run of 2 June 2031, so the export was not kept. Drop it "
                           "again on the newest run.", stale)
    finally:
        httpd.shutdown()
        httpd.server_close()
        ss.RUNNER, ss.CLOCK = kept_runner, kept_clock
        if kept_env is not None:
            os.environ[ss.STUB_ENV] = kept_env
    check("121, updated 13 October (128): Find citation counts, Fill from OpenAlex since 13 October, stands beside Find "
          "open-access PDFs under Sift in Settings, outside the AI switch, its button counting as it goes and a second "
          "press leaving the rest for later, the cited op kept",
          'id="sf-fill-go" type="button"><span id="sf-fill-word">Fill from OpenAlex</span></button>' in page
          and page.index('id="sf-oa-go"') < page.index('id="sf-fill-go"') < page.index('id="sfa-block"')
          and "data-ai" not in page.split('id="sfp-pdfs"', 1)[1].split('id="sfa-block"', 1)[0]
          and "{ op: 'fill', folder, at: run.done }" in fn(sjs, "sfFillRun") and "if (SF.fill) { SF.fill.stop = true; return; }" in fn(sjs, "sfFillRun")
          and "t('sift.fill.filling', { done: run.done, of: run.of })" in fn(sjs, "sfFillDraw") and SPARKLES not in fn(sjs, "sfFillRun")
          and 'if op == "cited":' in server_src and "keep=keep_cited" in server_src and "keep=keep_filled" in server_src)

    # ── K. reasons in one place
    review = base / "review"
    review.mkdir()
    ss.new_plan(review, "Keepers of the light", "How do keepers experience the night watch?")
    ss.save(review, {"databases": ["pubmed"], "blocks": [{"name": "Keepers", "terms": ["keeper*"]}],
                     "reasons": {"ta": ["X1 The plan's own"], "ft": []}})
    own = ss.state(review)
    (review / sift.REASONS_NAME).write_text("stage,code,meaning\nta,K1,Not about keepers\nft,K9,No account of the watch\n",
                                            encoding="utf-8")
    took = ss.state(review)
    ss.save(review, {"databases": ["pubmed"], "blocks": [{"name": "Keepers", "terms": ["keeper*", "lighthouse*"]}],
                     "reasons": {"ta": ["X1 The plan's own"], "ft": []}})
    reg = ss.register(review)
    md = (review / ss.PLAN_MD).read_text(encoding="utf-8")
    check("121, updated 12 October, later (124): with no reasons.csv of its own a review keeps the plan's reasons as "
          "before, and with one the screen is given the file's as one list, which saving and registering take into the "
          "plan, so search_plan.md says what the file says",
          own["reasons_file"] is None and own["plan"]["reasons"] == [{"code": "X1", "meaning": "The plan's own"}]
          and took["reasons_file"]["reasons"] == [{"code": "K1", "meaning": "Not about keepers"},
                                                  {"code": "K9", "meaning": "No account of the watch"}]
          and took["reasons_file"]["staged"] is True
          and reg["plan"]["reasons"] == [{"code": "K1", "meaning": "Not about keepers"},
                                         {"code": "K9", "meaning": "No account of the watch"}]
          and "- K1: Not about keepers" in md and "- K9: No account of the watch" in md and "X1" not in md, md[-400:])
    check("121, updated 12 October (123), and later (124): the Reasons part edits the file's reasons as one list, the "
          "app keeping the file, with no line about the file and no Open the file",
          "sfs-from-file" not in ssjs and "Open the file" not in ssjs and "sfs-reasons-file" not in ssjs
          and "const held = file ? file.reasons : SFS.plan.reasons;" in fn(ssjs, "sfsReasonRows")
          and "if (fill || !SFS.reasons) SFS.reasons = sfsReasonRows();" in fn(ssjs, "sfsDrawReasons")
          and "#sfs-reasons-own[hidden]" not in sscss)

    # ── L. a run's databases and drops (the review's session, 12 October)
    check("121: with the user's list empty every database goes by Sift's default, by API when keyless or its key is "
          "saved, a database the list does not hold the same, and a row of the list decides for its own",
          ss.how_of("scopus", {"scopus": True}, []) == "api" and ss.how_of("scopus", {}, []) == "export"
          and ss.how_of("pubmed", {}, []) == "api" and ss.how_of("wos", {"wos": True}, [{"source": "scopus", "how": "export"}]) == "api"
          and ss.how_of("scopus", {"scopus": True}, [{"source": "scopus", "how": "export"}]) == "export"
          and ss.how_of("scopus", {}, [{"source": "scopus", "how": "api"}]) == "export"
          and ss.how_of("psycinfo", {}, None) == "export")
    check("121: the screen names the run it shows with each drop, today's newest, and draws the runs afresh after a "
          "refusal, the server passing it on",
          "run: shown ? shown.date : undefined" in fn(ssjs, "sfsDropFile")
          # updated 12 October (123): a drop on a run waiting for its export goes to that run
          and "const shown = (run && SFS.runs.find((r) => r.date === run)) || SFS.runs.find((r) => (r.day || r.date) === SFS.today) || null;"
          in fn(ssjs, "sfsDropFile")
          and "{ op: 'runs', folder: SFS.folder }" in fn(ssjs, "sfsDropFile")
          and 'run=str(body.get("run") or "") or None' in server_src and "run_dir = drop_target(folder, day, run)" in
          support.source("apps/sift/sift_search.py").read_text(encoding="utf-8"))
