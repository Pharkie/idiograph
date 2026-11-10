from __future__ import annotations

import csv
import io
import json
import os
import re
import shutil

from . import support
from .support import check, grip_js, sift_words_js, skip


@support.as_app("sift")
def test_sift_review_two(scratch):
    print("\n118. Sift reviewed whole, round 2, 12 October: the research question on the card and Search strategy, a "
          "project renamed and removed as a Distil project is, PubMed, Europe PMC and OpenAlex by API at first, the "
          "databases one list, words on the title bar, plain publication types, Records screened every record, At title "
          "and abstract at full text, Undo at the foot, exclusion reasons in the plan, the PDFs looked for only past title "
          "and abstract, and Write the counts beside Export included records")
    import subprocess
    import server as server_mod
    import sift_routes
    import sift
    import sift_oa
    import sift_search as ss

    page = support.page_text()
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    # Sift's parts of the shell, from app.js since the family codebase's third build (22 October 2026)
    sset = support.text("apps/sift/static/sift_settings.js")
    sjs = support.text("apps/sift/static/sift.js")
    ssjs = support.text("apps/sift/static/sift_search.js")
    # the server's and, since the family codebase's third build, Sift's own routes
    server_src = "\n".join(support.source(p).read_text(encoding="utf-8") for p in ("server.py", "apps/sift/sift_routes.py"))
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: (("async " if f"async function {name}(" in src else "") + f"function {name}(" + fn(src, name) + "\n}")
    node = shutil.which("node")
    base = scratch / "sift-review-118"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)

    class Done:
        def __init__(self, code):
            self.returncode, self.stdout, self.stderr = code, "", ""

    def no_keys(argv, **_):
        """The keychain stood in for: every service holds no key, and nothing reaches the tool"""
        return Done(44)

    def tree(at: Path) -> dict:
        # each path with slashes on any system, and a lock file never read, since Windows refuses a
        # read of a file another holds locked (14 October)
        return {p.relative_to(at).as_posix(): (p.read_bytes() if p.is_file() and p.suffix != ".lock" else None)
                for p in sorted(at.rglob("*"))}

    # ── A. exclusion reasons in the plan, every name invented, on village kilns
    cleaned = ss.reasons_of({"ta": "E1 Not about kilns\nE2: No accounts of firing\n\n e1 again\nE3 - Not in English\nE4",
                             "ft": [{"code": "F1", "meaning": "No full text"}, {"code": "", "meaning": "lost"},
                                    {"code": "TOOLONGACODEHERE", "meaning": "x"}], "xx": "Z1 nothing"})
    check("118, updated 12 October, later (124): a plan's exclusion reasons, one list since 124, a plan of before's two "
          "stages read into it in the order typed, title and abstract first, a code first and its meaning after a space, a "
          "colon or a dash, a line with a code alone kept, a code held already and a row with no code let go, a code kept "
          "to twelve letters and no stage but the two",
          cleaned == [{"code": "E1", "meaning": "Not about kilns"}, {"code": "E2", "meaning": "No accounts of firing"},
                      {"code": "E3", "meaning": "Not in English"}, {"code": "E4", "meaning": ""},
                      {"code": "F1", "meaning": "No full text"}, {"code": "TOOLONGACODE", "meaning": "x"}]
          and ss.blank_plan()["reasons"] == [], str(cleaned))
    review = base / "Kiln review"
    review.mkdir()
    ss.new_plan(review, "Village kilns", "How do potters experience a shared kiln firing?")
    plan = {"databases": ["psycinfo"], "blocks": [{"name": "Kilns", "terms": "kiln*\npotter*"}],
            "reasons": {"ta": "E1 Not about kilns\nE2 No accounts of firing", "ft": "F1 No full text"}}
    ss.save(review, plan)
    kept_runner, kept_env = ss.RUNNER, os.environ.pop(ss.STUB_ENV, None)
    ss.RUNNER = no_keys
    try:
        done = ss.register(review)
        md = (review / ss.PLAN_MD).read_text(encoding="utf-8")
        data = ss.read_file(review)
        again = ss.save(review, dict(plan, reasons={"ta": ["E1 Not about kilns", "E2 No accounts of firing", ""],
                                                     "ft": [{"code": "F1", "meaning": "No full text"}]}))
        check("118: the reasons are part of the plan's version, registered with it and written into search_plan.md under "
              "Exclusion reasons, and the same reasons sent again in another form make no new version",
              # one list since 12 October, later (124)
              data["versions"][0]["plan"]["reasons"][-1] == {"code": "F1", "meaning": "No full text"}
              and "## Exclusion reasons\n\nOptional at title and abstract, and one is required for each report excluded at "
                  "full text.\n\n- E1: Not about kilns\n- E2: No accounts of firing\n- F1: No full text\n" in md
              and md.index("## Limits") < md.index("## Exclusion reasons") < md.index("## Search strings")
              and done["registered"] == 1 and len(again["versions"]) == 1, md[:400])
        ris = ("TY  - JOUR\nTI  - Firing the village kiln\nAU  - Clay, A\nPY  - 2021\nJO  - Invented Kiln Studies\n"
               "AB  - Ten potters spoke of the firing.\nER  - \n\nTY  - THES\nTI  - Smoke and glaze\nAU  - Glaze, B\nPY  - 2019\n"
               "AB  - A thesis on glazes.\nER  - \n").encode("utf-8")
        day = "2026-10-12"
        taken = ss.take_export(review, "psycinfo", ris, "psycinfo.ris", day=day, ctx=ss.Context(), listed=[])
        run_dir = review / "runs" / day
        written = (run_dir / sift.REASONS_NAME).read_text(encoding="utf-8")
        (run_dir / sift.REASONS_NAME).write_text("stage,code,meaning\nta,R9,The review's own\n", encoding="utf-8")
        ss.take_export(review, "psycinfo", ris, "psycinfo.ris", day=day, ctx=ss.Context(), listed=[])
        own_kept = (run_dir / sift.REASONS_NAME).read_text(encoding="utf-8")
        check("118: a new run with no reasons.csv takes the plan's, which the screening offers on Reject, and a run's own "
              "reasons.csv is never written over when the run is written again",
              taken["taken"]["records"] == 2
              # in the one-list form since 12 October, later (124)
              and written == "code,meaning\nE1,Not about kilns\nE2,No accounts of firing\nF1,No full text\n"
              and own_kept == "stage,code,meaning\nta,R9,The review's own\n", written)
        other = base / "Glaze review"
        other.mkdir()
        ss.new_plan(other, "Glazes")
        ss.save(other, plan)
        ss.register(other)
        (other / sift.REASONS_NAME).write_text("stage,code,meaning\nta,G1,The review session's own\n", encoding="utf-8")
        ss.take_export(other, "psycinfo", ris, "psycinfo.ris", day=day, ctx=ss.Context(), listed=[])
        master = (other / "runs" / day / sift.REASONS_NAME).read_text(encoding="utf-8")
        reasons_seen = sift.reasons(run_dir)
        check("118: a review folder's own reasons.csv, the review's own session's, still goes into its run as it always did, "
              "ahead of the plan's",
              master == "stage,code,meaning\nta,G1,The review session's own\n"
              and reasons_seen["ta"] == [{"code": "R9", "meaning": "The review's own"}], master)
    finally:
        ss.RUNNER = kept_runner
        if kept_env is not None:
            os.environ[ss.STUB_ENV] = kept_env
    check("118, updated 12 October (121): on a new install PubMed, Europe PMC and OpenAlex go by API, as they need no key, a "
          "list that names another choice keeps it, and every other database his list does not hold goes by its default, by "
          "export with no key saved",
          [ss.how_of(s, {}, []) for s in ("pubmed", "epmc", "openalex", "scopus", "psycinfo")] == ["api", "api", "api", "export", "export"]
          and ss.how_of("pubmed", {}, [{"source": "pubmed", "how": "export"}]) == "export"
          and ss.how_of("scopus", {"scopus": True}, [{"source": "scopus", "how": "api"}]) == "api"
          and "how: (SFS.catalog.keyless || []).includes(s) ? 'api' : 'export'" in fn(ssjs, "sfsAccRow"))

    # ── B. the research question, a project renamed and removed, through the server, its list in memory
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    cfg_file = base / "config.json"
    cfg_file.write_text(json.dumps({"projects": []}), encoding="utf-8")
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = cfg_file, None, {"recent": []}
        rv = sift_routes.api_sift_review
        (base / "kiln-new").mkdir()
        made = rv({"op": "new", "folder": str(base / "kiln-new"), "name": "Kiln firings", "question": "What is a firing like?"})
        folder = server_mod.abs_path(made["review"]["folder"])
        mark = tree(folder)
        renamed = rv({"op": "rename", "folder": made["review"]["folder"], "name": "Shared kilns",
                      "question": "How do potters live a shared firing?"})
        row = next(r for r in renamed["reviews"] if r["name"] == "Shared kilns")
        sift_routes.remember_review(folder, run="2026-10-12")
        after_open = sift_routes.review_view(folder)
        back = rv({"op": "rename", "folder": made["review"]["folder"], "name": "Kiln firings", "question": "What is a firing like?"})
        entry = sift_routes.kept_review(folder)
        check("118: a project's research question stands in its view and on its card, New project's from its plan, and one "
              "he gives in Settings with a name of his kept in the app's own list and never in the folder, kept through "
              "the opening of a run, and a name or question the same as the plan's own leaving the list without one",
              made["review"]["question"] == "What is a firing like?" and renamed["review"]["name"] == "Shared kilns"
              and renamed["review"]["question"] == "How do potters live a shared firing?"
              and row["question"] == "How do potters live a shared firing?" and tree(folder) == mark
              and after_open["question"] == "How do potters live a shared firing?" and after_open["name"] == "Shared kilns"
              and back["review"]["name"] == "Kiln firings" and back["review"]["question"] == "What is a firing like?"
              and "name" not in entry and "question" not in entry, str(entry))
        cleared = rv({"op": "rename", "folder": made["review"]["folder"], "question": ""})
        gone_dir = base / "kiln-gone"
        gone_dir.mkdir()
        gone = rv({"op": "new", "folder": str(gone_dir), "name": "Kiln gone", "question": ""})
        shutil.rmtree(gone_dir)
        forgot = rv({"op": "forget", "folder": gone["review"]["folder"]})
        forgot_kept = rv({"op": "forget", "folder": made["review"]["folder"]})
        refused = ""
        try:
            rv({"op": "forget", "folder": made["review"]["folder"]})
        except Exception as exc:
            refused = str(exc)
        check("118: a question cleared stands cleared, Remove from Idiograph takes a project out of the list, one whose "
              "folder is gone among them, its folder and every file in it left as they are, and one not in the list is "
              "refused in one line",
              cleared["review"]["question"] == "" and forgot["forgotten"] and forgot["name"] == "kiln-gone"
              and forgot_kept["name"] == "Kiln firings" and forgot_kept["reviews"] == [] and tree(folder) == mark
              and refused == sift_routes.REVIEW_NOT_OPENED, refused)
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
    own = page.split('id="sfp-own"', 1)[1].split('id="sfp-pdfs"', 1)[0] if 'id="sfp-own"' in page else ""
    check("118: under Projects in Sift's Settings each project has its Project part as an IPA project has, its "
          "name and question saved with Save, the folder and Remove from Sift, every project listed whose folder is "
          "there, one with no screening its Project part alone",
          'for="sfp-name">Project name</label>' in own and 'for="sfp-question">Research question</label>' in own
          and 'id="sfp-remove">Remove from Sift</button>' in own and 'id="sfp-root"' in own
          and ".filter((r) => r.there);" in fn(sset, "sfpLoad") and "r.screening || ''" in fn(sset, "sfpLoad")
          and "$('sfp-pdfs').hidden = !SFA.at;" in fn(sset, "sfpShow")
          and "out.push({ op: 'rename', folder: item.review, name, question });" in fn(sset, "sfpSaves")
          and "const sfpSendsAll = () => ({ ai: sfaSaves(), projects: sfpSaves() });" in sset
          and "await api('/api/sift-review', sent)" in fn(sset, "sfpSend")
          and "await askRemove(item.name || 'this project')" in fn(sset, "sfpRemove")
          and "{ op: 'forget', folder: item.review, trash: asked.trash, page: pageId() }" in fn(sset, "sfpRemove")
          and "$('sfp-remove').onclick = () => sfpRemove();" in sset)

    # ── C. the screening: the flow, Export included records, the finder, the kept At title and abstract filter
    scr = base / "kiln-screening"
    scr.mkdir()
    head = ["rec_id", "title", "authors", "year", "journal", "doi", "pub_type", "url", "sources", "abstract"]
    rows = [["K1", "Firing the village kiln", "Clay, A.; Ash, B.", "2021", "Invented Kiln Studies", "10.5555/kiln.1",
             "Journal Article", "", "PubMed", "Ten potters spoke of the firing."],
            ["K2", "Smoke and glaze", "Glaze, B.", "2019", "Invented University", "", "Dissertation", "https://example.org/k2",
             "PsycInfo", "A thesis on glazes."],
            ["K3", "Wood for the kiln", "Oak, C.", "2018", "Invented Kiln Studies", "", "research-article", "", "Europe PMC",
             "A survey of wood."],
            ["K4", "Cracks in the pots", "Pot, D.", "2017", "Invented Kiln Studies", "", "Journal Article", "", "PubMed",
             "Potters on cracked pots."]]
    with open(scr / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(head)
        w.writerows(rows)
    none_yet = sift.export_included(scr)
    oa_none = sift_oa.plan(scr)
    sift.decide(scr, "K1", "ta", "include")
    sift.decide(scr, "K2", "ta", "maybe")
    sift.decide(scr, "K3", "ta", "exclude")
    sift.decide(scr, "K1", "ft", "include")
    sift.decide(scr, "K2", "ft", "include")
    flow = sift.prisma_source(sift.counts(sift.load(scr)))
    screened = flow.split('screened["', 1)[1].split('"]', 1)[0] if 'screened["' in flow else ""
    check("118, updated 12 October (126): mid-screening the flow's Records screened is every record after duplicates, "
          "those still to screen and at maybe said inside it",
          screened == "Records screened<br/>(n = 4)<br/>To screen<br/>(n = 1)<br/>Maybe (n = 1)", screened)
    (scr / sift.PDF_DIR).mkdir()
    (scr / sift.PDF_DIR / "K2.pdf").write_bytes(b"%PDF-1.4 smoke")
    oa = sift_oa.plan(scr)
    check("118: Find open-access PDFs looks only for the records that passed title and abstract, accepted or kept at maybe, "
          "those with a PDF passed over, and says so when none has passed yet",
          oa == {"ids": ["K1"], "records": 4, "passed": 2, "have": 1}
          and oa_none == {"ids": [], "records": 4, "passed": 0, "have": 0}
          and "'No record has passed title and abstract yet.'" in fn(sjs, "sfOaRun")
          and "'Every record that passed title and abstract has a PDF.'" in fn(sjs, "sfOaRun")
          and "Looks up each record that passed title and abstract and has no PDF" in page, str(oa))
    included = sift.export_included(scr)
    ris_out = (scr / sift.INCLUDED_RIS).read_text(encoding="utf-8")
    csv_out = list(csv.reader(io.StringIO((scr / sift.INCLUDED_CSV).read_text(encoding="utf-8"))))
    check("118: Export included records writes the records accepted at full text beside the CSV as RIS and CSV, each "
          "record's type, title, authors as Last, First, year, journal, DOI and web address, abstract and its rec_id, the "
          "CSV the CSV's own cells, and with none accepted it writes nothing",
          none_yet == {"records": 0, "files": [sift.INCLUDED_RIS, sift.INCLUDED_CSV], "written": False}
          and included == {"records": 2, "files": ["screening.included.ris", "screening.included.csv"], "written": True}
          and ris_out.startswith("TY  - JOUR\nTI  - Firing the village kiln\nAU  - Clay, A.\nAU  - Ash, B.\nPY  - 2021\n"
                                 "JO  - Invented Kiln Studies\nDO  - 10.5555/kiln.1\nUR  - https://doi.org/10.5555/kiln.1\n"
                                 "AB  - Ten potters spoke of the firing.\nN1  - Sift: K1\nER  - ")
          and "TY  - THES\nTI  - Smoke and glaze\nAU  - Glaze, B.\nPY  - 2019\nJO  - Invented University\n"
              "UR  - https://example.org/k2\n" in ris_out and "Wood for the kiln" not in ris_out
          # updated 14 October (139): his key excerpts as text in a last column, empty for a record with none
          and csv_out[0] == list(sift.INCLUDED_COLUMNS) + ["excerpts"] and [r[0] for r in csv_out[1:]] == ["K1", "K2"]
          and [r[-1] for r in csv_out[1:]] == ["", ""]
          and csv_out[2][6] == "Dissertation", ris_out[:300])
    kept_view = sift.save_view(scr, filters={"tadec": ["maybe"], "nothing": ["x"]})
    check("118: the At title and abstract filter is kept in sift.json as every other filter, though Columns does not "
          "offer it, and a key the table has not is let go",
          kept_view["filters"] == {"tadec": ["maybe"]} and sift.table_settings(scr)["filters"] == {"tadec": ["maybe"]}
          and sift.STAGE_FILTERS == ("tadec", "bench", "formdone") and "tadec" not in [c["key"] for c in kept_view["columns"]],
          str(kept_view["filters"]))
    check("118, updated 12 October (121): the server writes the included records on its own op, and the item in Export's "
          "menu asks for it, off while no record is accepted at full text",
          'if op == "included":' in server_src and "return sift_mod.export_included(folder)" in server_src
          and "{ op: 'included', folder: SF.folder }" in fn(sjs, "sfIncluded")
          and "$('sf-included').disabled = !(ft && Number(ft.include));" in fn(sjs, "sfBar")
          and "$('sf-included').onclick = () => sfMenuTake(sfIncluded);" in sjs)

    # ── D. the title bar's words, Undo at the foot and the record's head
    bar = fn(sjs, "sfBar")
    check("118: Undo stands at the foot once there is a decision or a note to take back, taking back the newest as U does, "
          "the record and stage it takes back named on hover",
          '<button type="button" class="ghost small sf-undo" id="sf-undo" hidden>Undo</button>' in page
          and page.index('id="sf-count"') < page.index('id="sf-undo"') < page.index('id="sf-tally"')
          and "$('sf-undo').hidden = !u;" in bar and "'sift.undo.tip_ft', { rec: u.rec_id }" in bar
          and "$('sf-undo').onclick = () => sfUndo();" in sjs)

    # ── E. in node: plain publication types, At title and abstract at full text, Search strategy's one list and reasons
    block = sjs.split("/* ── the table's rows: its columns, sort and filter, worked out with no page ── */", 1)[-1].split(
        "/* ── the table, drawn ── */", 1)[0]
    block = support.table_js() + "\n" + block
    lead = app[app.index("const esc = "):app.index("// a line from the server with a command in backticks")]
    view = sift.screen(scr)
    drawn = [whole(sjs, n) for n in ("sfPillHtml", "sfPillSet", "sfTvCell", "sfStars", "sfLinked", "sfPdfUrl")]
    if node and "function sfTypeWord(" in block and "const sfCatPills = " in block:
        probe = base / "sift-review-two.js"
        probe.write_text("\n".join([block, lead, sift_words_js(sjs),
                                    "const SF = { filters: {}, facetsMore: new Set(), facetsFind: {}, stage: 'ft' };",
                                    "function sfMeaning(code) { return ''; }"] + drawn)
                         + "\nconst data = " + json.dumps({"records": view["records"], "table": view["table"]}) + ";\n" + r"""
SF.table = data.table;
const out = {};
out.words = ['Journal Article', 'research-article', 'Academic Journal', 'Peer Reviewed Journal', 'Dissertation', 'Thesis',
  'Systematic Review', 'Meta-Analysis', 'Review Article', 'book-chapter', 'Book', 'proceedings-article', 'Preprint',
  'posted-content', 'Report', 'Editorial', 'Letter', 'Comment', 'Erratum', 'Study Protocol', 'dataset', 'Clinical Trial',
  'reference-entry', 'other-thing', ''].map(sfTypeWord);
out.parts = sfTypeParts('Journal Article; research-article | Review');
out.pills = sfCatPills('Journal Article; Dissertation');
const rows = data.records;
const ta = sfStageCols([SF_ID, ...sfColumns(data.table)], 'ta').map((c) => c.key);
const ft = sfStageCols([SF_ID, ...sfColumns(data.table)], 'ft').map((c) => c.key);
out.ta = ta.includes('tadec');
out.after = ft[ft.indexOf('decision') + 1];
const cols = sfStageCols([SF_ID, ...sfColumns(data.table)], 'ft');
const g = sfGroups(rows, rows, cols, 'ft', [], {});
const tad = g.find((x) => x.key === 'tadec');
out.tadChoices = tad ? tad.choices.map((c) => [c.value, c.label]) : null;
out.tadCounts = tbFacetCounts(rows.filter((r) => ['K1', 'K2'].includes(r.rec_id)), g, {}, sfRead('ft')).tadec;
out.maybeOnly = tbFilterRows(['K1', 'K2'], new Map(rows.map((r) => [r.rec_id, r])), { tadec: ['maybe'] }, cols, sfRead('ft'));
const k2 = rows.find((r) => r.rec_id === 'K2');
out.cell = sfTvCell(k2, SF_TADEC);
out.typeGroup = g.find((x) => x.key === 'csv:pub_type').choices.map((c) => [c.value, c.label]);
console.log(JSON.stringify(out));
""", encoding="utf-8")
        ran = subprocess.run([node, str(probe)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        why = (ran.stderr or ran.stdout)[:400]
        check("118: in node, a publication type in plain words, the databases' words for one type one, Dissertation or "
              "thesis, Review, Book chapter and the rest, any other as written, a hyphened word parted",
              out.get("words") == ["Journal article", "Journal article", "Journal article", "Journal article",
                                   "Dissertation or thesis", "Dissertation or thesis", "Review", "Review", "Review",
                                   "Book chapter", "Book", "Conference paper", "Preprint", "Preprint", "Report", "Editorial",
                                   "Letter or comment", "Letter or comment", "Correction", "Protocol", "Dataset",
                                   "Clinical Trial", "Book chapter", "Other thing", ""]
              and out.get("parts") == ["Journal article", "Review"]
              and out.get("pills") == '<span class="sf-cat">Journal article</span><span class="sf-cat">Dissertation or thesis</span>',
              why or str(out.get("words")))
        check("118: in node, the filter's Publication type offers the plain words, Journal Article and research-article "
              "one choice",
              (out.get("typeGroup") or [])[:2] == [["journal article", "Journal article"], ["dissertation or thesis", "Dissertation or thesis"]]
              and len([c for c in out.get("typeGroup") or [] if c[0] == "journal article"]) == 1, str(out.get("typeGroup")))
        check("118, updated 12 October (126): in node, at full text the table and the filters have At title and abstract after Decision, Yes or "
              "Maybe as a pill and a filter, and at title and abstract they have none",
              out.get("ta") is False and out.get("after") == "tadec"
              and out.get("tadChoices") == [["include", "Yes"], ["maybe", "Maybe"]]
              and out.get("tadCounts") == {"include": 1, "maybe": 1} and out.get("maybeOnly") == ["K2"]
              and out.get("cell") == '<td class="sf-c-dec"><span class="sf-pill" data-decision="maybe">Maybe</span></td>',
              why or str(out))
    else:
        skip("118: publication types and At title and abstract in node", "no node on this machine")
    check("118: the CSV's pub_type is never changed, the plain words the page's alone",
          "Journal Article" in (scr / sift.CSV_NAME).read_text(encoding="utf-8")
          and "research-article" in (scr / sift.CSV_NAME).read_text(encoding="utf-8"))
    if node:
        script = base / "sift-review-two-search.js"
        harness = r"""
const els = {};
const mk = (id) => ({ id, setAttribute(k, v) { (this.attrs = this.attrs || {})[k] = v; }, innerHTML: '', value: '', hidden: false, textContent: '', disabled: false, title: '', dataset: {},
  onclick: null, focus() {}, click() { return this.onclick ? this.onclick() : undefined; },
  querySelectorAll: () => [], querySelector: () => null, matches: () => false, closest: () => null });
const $ = (id) => els[id] || (els[id] = mk(id));
$('settings').hidden = true;
$('feedback').hidden = true;
$('sfs-ask').hidden = true;
$('sfs-mark-card').hidden = true;
async function api() { return {}; }
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
        # the band's name drawn by the family's own (bandNameSet, barsD, 6 November 2026)
        body = (grip_js() + "\n" + support.table_js() + "\n" + whole(app, "bandNameSet") + "\n"
                + ssjs.rsplit("\nsfsBoot();", 1)[0])
        run = r"""
const out = {};
SFS.catalog = { sources: ['scopus', 'psycinfo', 'pubmed', 'epmc', 'openalex', 'other'],
  names: { scopus: 'Scopus', psycinfo: 'PsycInfo', pubmed: 'PubMed', epmc: 'Europe PMC', openalex: 'OpenAlex', other: 'Other database' },
  keyless: ['pubmed', 'epmc', 'openalex'], apis: ['scopus', 'pubmed', 'epmc', 'openalex'], scopes: [['tak', 'Title, abstract and keywords']],
  types: [], platformed: ['psycinfo'], platforms: [['ebsco', 'EBSCO']], sites: {}, platform_sites: {}, hosts: {} };
SFS.plan = { databases: ['pubmed', 'other'], others: { other: 'Kiln Index' }, platforms: {}, blocks: [], years: {}, types: [],
  reasons: [{ code: 'E1', meaning: 'Not about kilns' }], benchmark: [], benchmark_titles: {}, overrides: {} };
SFS.listed = [{ source: 'openalex', how: 'api' }, { source: 'other', name: 'Glaze Base', how: 'export' }];
SFS.how = { pubmed: 'api', epmc: 'api', openalex: 'api', scopus: 'export', psycinfo: 'export' };
out.rows = sfsRows().map((r) => [r.name, !!r.listed]);
out.shown = sfsShownOrder();
out.item = sfsDbItem(sfsRows().find((r) => r.s === 'openalex'));
out.plain = sfsDbItem(sfsRows().find((r) => r.s === 'scopus'));
out.acc = [sfsAccRow('epmc').how, sfsAccRow('scopus').how, sfsAccRow('openalex').how];
// the reasons one list of rows since 12 October, later (124)
sfsDrawReasons(true);
out.reasons = $('sfs-reasons').innerHTML;
out.lines = typeof sfsReasonLines;
rvHead('searches', { name: 'Kiln review', folder: 'k', searches: true, screening: null, question: 'How is a firing lived?' });
out.question = [$('sfs-question').textContent, $('sfs-question').hidden];
rvHead('searches', { name: 'Glaze review', folder: 'g', searches: true, screening: null, question: '' });
out.none = [$('sfs-question').textContent, $('sfs-question').hidden];
console.log(JSON.stringify(out));
"""
        script.write_text(harness + body + "\n" + run, encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60, env=dict(os.environ, TZ="UTC"))
        o = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        why = (ran.stderr or ran.stdout)[:400]
        check("118: in node, the databases are one list in the plan's own order, every one Sift knows, then each he named, "
              "his list's first, then the plan's own, each saying how it runs since 124 where In your list stood, no More "
              "fold, and the strings and runs in the same order",
              o.get("rows") == [["Scopus", False], ["PsycInfo", False], ["PubMed", False], ["Europe PMC", False],
                                ["OpenAlex", True], ["Glaze Base", True], ["Kiln Index", False]]
              and o.get("shown") == ["pubmed", "other"]
              and '<span class="sfs-tag api">By API</span>' in o.get("item", "") and "In your list" not in o.get("item", "")
              and '<span class="sfs-tag">By export</span>' in o.get("plain", "")
              and "sfs-mine" not in o.get("plain", "") and "sfs-more" not in ssjs and "More</summary>" not in ssjs,
              why or str(o.get("rows")))
        check("118: in node, a database's access with no row in his list reads By API for PubMed, Europe PMC and OpenAlex "
              "and By export for any other",
              o.get("acc") == ["api", "export", "api"], str(o.get("acc")))
        check("118, updated 12 October, later (124): in node, the exclusion reasons are drawn from the plan a row each, its "
              "code then its meaning, the lines of before gone",
              'value="E1" maxlength="12"' in o.get("reasons", "") and 'value="Not about kilns" maxlength="200"' in o.get("reasons", "")
              and o.get("lines") == "undefined", str(o))
        check("118: in node, Search strategy stands the project's research question under its name, and none when it has none",
              o.get("question") == ["How is a firing lived?", False] and o.get("none") == ["", True], str(o))
    else:
        skip("118: Search strategy's list, reasons and question in node", "no node on this machine")
    reasons_part = ssjs.split('id="sfs-h-reasons"', 1)[1].split("</section>", 1)[0] if 'id="sfs-h-reasons"' in ssjs else ""
    check("118, updated 12 October (123), and later (124): the plan's Exclusion reasons part stands last in the plan, after "
          "the benchmark papers and before Searches, one list of rows with Add a reason, each change written to reasons.csv",
          'Exclusion reasons</h3>' in reasons_part and '<div class="sfs-reasons" id="sfs-reasons"></div>' in reasons_part
          and 'id="sfs-reason-add">Add a reason</button>' in reasons_part and "sfs-reasons-ta" not in ssjs
          and ssjs.index('id="sfs-h-limits"') < ssjs.index('id="sfs-h-dbs"') < ssjs.index('id="sfs-h-bench"')
          < ssjs.index('id="sfs-h-reasons"') < ssjs.index('id="sfs-h-strings"')
          and "op: 'reasons', folder: SFS.folder, rows" in fn(ssjs, "sfsReasonsSave")
          and "sfsDrawReasons(true);" in fn(ssjs, "sfsDraw"))
