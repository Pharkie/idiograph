from __future__ import annotations

import json
import re
import shutil

import openpyxl

import workbook as wb_mod

from . import support
from .support import DEMO_SHEET, check, demo_copy, skip
import idiograph_routes
import idiograph_cli


def test_loose_ends(scratch):
    print("\n95. Four loose ends: each statement's own quote in the PET draft and the statements CSV, the GETs print's "
          "PET tables as the table of PETs, the page back where it was after a restart, and board new's Board 1 on a "
          "case with no themes file")
    import csv
    import html
    import inspect as inspect_mod
    import subprocess
    import cli
    import export as export_mod
    import gets_print
    import server as server_mod
    import themes as themes_mod
    import themes_print

    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    js = support.text("apps/idiograph/static/themes.js")
    flat = lambda text: " ".join(str(text).split())
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    S = DEMO_SHEET
    K = lambda row, line=0: themes_mod.card_key(S, row, line)
    un = html.unescape

    # ── A. the fixture: an invented project of two cases, each a scratch copy of the demo's workbook with
    # statements and quotes of its own, the marks a workbook keeps round a quote in each spelling, "(no
    # quote)" holding a place, a statement with no quote, a sub-theme between a PET's statements in one
    # case and after them in the other, a group, a note, picks, a statement not placed and a discard
    root = scratch / "loose-root"
    shutil.rmtree(root, ignore_errors=True)
    (root).mkdir(parents=True)
    (root / "idiograph-project.json").write_text(json.dumps(
        {"name": "Gardens, a scratch project", "research_question": "How do people keep an allotment going alone?"}),
        encoding="utf-8")

    def make_case(folder: str, stem: str, cells: dict) -> Path:
        book = demo_copy(root, folder, f"{stem} - EN & ES.xlsx")
        wb = openpyxl.load_workbook(book, rich_text=True)
        ws = wb[S]
        cols = wb_mod.detect_columns(ws)
        for r, (es, kq) in cells.items():
            ws.cell(r, cols["es"]).value = es
            ws.cell(r, cols["kq"]).value = kq
        wb.save(book)
        wb.close()
        return book

    wren = make_case("P1 - Wren", "P1 Wren", {
        15: ("Out before the gates open\n\nThe fork left by the water butt", '"we beat the wardens to it"\n\n(no quote)'),
        17: ("Bindweed as company", "‘it kept me company, that is all’"),
        19: ("The seed tin by the back door", "“I never threw it out”"),
        21: ("Nobody comes by the plot now", "they stopped coming"),
        23: ("Waking before the alarm", None),
        25: ("A notice pinned to the shed", '"a notice, and a padlock"')})
    hazel = make_case("P2 - Hazel", "P2 Hazel", {
        15: ("Rain on the polytunnel roof", '"like gravel on a tin"'),
        17: ("Saving seed from the best plants", "‘the best ones, only the best’"),
        19: ("A row left for her brother", None),
        21: ("Talking to the beans", '"I tell them they are doing well"')})

    def board_of(book, spots, groups, picks=None, discarded=()):
        read = themes_mod.read_cards(book)
        board = themes_mod.blank_version(read["cards"])
        for key, (x, y) in spots.items():
            board["cards"][key].update(x=x, y=y)
        board["groups"] = groups
        board["picks"] = picks or {}
        board["discarded"] = list(discarded)
        return board

    # Wren: a PET whose sub-theme's frame sits between its statements, the sub-theme holding a group
    themes_mod.save(wren, board_of(wren, {K(15): (0, 100), K(23): (0, 400), K(19): (0, 700), K(15, 1): (0, 1300),
                                          K(17): (2000, 100), K(21): (2000, 300)}, [
        {"id": "g1", "label": "Early at the plot", "note": "Before anyone else is up.",
         "members": [K(15), "g2", K(15, 1)], "x": 0, "y": 40},
        {"id": "g2", "label": "Waking for it", "members": [K(23), "g3"], "x": 0, "y": 340},
        {"id": "g3", "label": "The tin", "members": [K(19)], "x": 0, "y": 640},
        {"id": "g4", "label": "Company of a kind", "members": [K(17), K(21)], "x": 2000, "y": 40}],
        picks={"g1": [K(15)], "g4": [K(17)]}, discarded=[K(25)]), "P1 - Wren")
    # Hazel: a PET with a sub-theme after its own statements, as the GETs copy keeps them
    themes_mod.save(hazel, board_of(hazel, {K(15): (0, 100), K(17): (0, 300), K(19): (0, 700), K(21): (2000, 100)}, [
        {"id": "g1", "label": "Keeping the plot", "members": [K(15), K(17), "g2"], "x": 0, "y": 40},
        {"id": "g2", "label": "For someone else", "members": [K(19)], "x": 0, "y": 640},
        {"id": "g3", "label": "Talking to it", "members": [K(21)], "x": 2000, "y": 40}],
        picks={"g1": [K(17)], "g3": [K(21)]}), "P2 - Hazel")
    before = {p: p.read_bytes() for p in (wren, hazel, themes_mod.themes_path(wren), themes_mod.themes_path(hazel))}

    item_re = re.compile(r'<h2 class="pet-title"><span class="number">(.*?)</span> <span class="title">(.*?)</span></h2>'
                         r'|<h\d class="(?:sub|group)-title">(.*?)</h\d>|<h2>((?:Not placed|Experiential statements set aside) \(\d+\))</h2>'
                         r'|<div class="item"><p class="st">(.*?)</p>(?:<p class="kq">(.*?)</p>)?(?:<p class="why">.*?</p>)?</div>')

    def table_tokens(part: str) -> list:
        """The headings and the rows of a table of PETs in the order they stand, a row as its words,
        its reference and its quote."""
        out = []
        for m in item_re.finditer(part):
            if m.group(1) is not None:
                out.append(("h", f"{un(m.group(1))} {un(m.group(2))}"))
            elif m.group(3) is not None:
                out.append(("h", un(m.group(3))))
            elif m.group(4):
                # the bin heads the table and the PET draft alike, as its tick names it (19 October)
                out.append(("h", m.group(4)))
            else:
                st = m.group(5)
                ref = re.search(r' <span class="ref">\((.*?)\)</span>$', st)
                said = un(m.group(6) or "")
                out.append(("s", un(st[:ref.start()] if ref else st), un(ref.group(1)) if ref else "",
                            said[1:-1] if said.startswith("‘") and said.endswith("’") else said))
        return out

    def md_tokens(draft: str) -> tuple[list, list]:
        """The same from the PET draft, from its first heading on, and the quote lines not in the shape."""
        lines = draft.splitlines()
        at = next(i for i, ln in enumerate(lines) if ln.startswith("## "))
        out, odd = [], []
        for i in range(at, len(lines)):
            ln = lines[i]
            if ln.startswith("#"):
                out.append(("h", ln.lstrip("#").strip()))
            elif ln.startswith("- "):
                m = re.match(r"^- (.*) \(([^()]*)\)(\\?)$", ln)
                if not m:
                    odd.append(ln)
                    continue
                said = ""
                if m.group(3):
                    nxt = lines[i + 1] if i + 1 < len(lines) else ""
                    if nxt.startswith("  ‘") and nxt.endswith("’"):
                        said = nxt[3:-1]
                    else:
                        odd.append(nxt)
                out.append(("s", m.group(1), m.group(2), said))
        return out, odd

    def main_of(page: str) -> str:
        return page.split("<main>", 1)[1].split("</main>", 1)[0]

    # ── B. 1, the PET draft and the CSV agree with the table under both label schemes
    csv_out = scratch / "loose-wren.csv"
    export_mod.export(wren, csv_out, themes=(themes_mod.themes_path(wren), None), guard=False)
    with open(csv_out, encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    for labels in (themes_mod.LETTERS, themes_mod.NUMBERS):
        page = themes_print.page(wren, "P1 - Wren", auto=False, labels=labels, unplaced=True, binned=True)
        table = table_tokens(main_of(page))
        draft = themes_mod.draft_markdown(wren, "P1 - Wren", labels=labels)[0]
        drafted, odd = md_tokens(draft)
        check(f"95: 1, the PET draft's headings and rows are the table's, in its order, each statement with its reference "
              f"and its own quote, under {labels}",
              drafted == table and not odd and len([t for t in table if t[0] == "s"]) == 25, str(odd)[:200])
        check(f"95: 1, the statements CSV's rows and their quotes are the table's, in its order, under {labels}",
              [(r[2], r[4]) for r in rows[1:]] == [(t[1], t[3]) for t in table if t[0] == "s"])
    heads = [t[1] for t in table_tokens(main_of(themes_print.page(wren, "P1 - Wren", auto=False, unplaced=True, binned=True)))
             if t[0] == "h"]
    numbered = [t[1] for t in table_tokens(main_of(themes_print.page(wren, "P1 - Wren", auto=False,
                                                                     labels=themes_mod.NUMBERS))) if t[0] == "h"]
    check("95: 1, the headings lettered the book's way, A, A1, A1.1, or numbered PET 1, PET 1a, 1a.1 as the project says, "
          "a sub-theme in its place between its PET's statements",
          heads[:4] == ["A. Early at the plot", "A1. Waking for it", "A1.1 The tin", "B. Company of a kind"]
          and numbered[:4] == ["PET 1. Early at the plot", "PET 1a. Waking for it", "1a.1 The tin", "PET 2. Company of a kind"]
          and heads[4].startswith("Not placed (") and heads[5] == "Experiential statements set aside (1)", str(heads))
    draft = themes_mod.draft_markdown(wren, "P1 - Wren")[0]
    section = draft.split("\n## A. Early at the plot\n", 1)[1].split("\n## B.", 1)[0]
    check("95: 1, the draft's lines: a statement and its reference, a break, then its quote set in, in single curly marks, "
          "the workbook's own marks never doubled",
          "- Out before the gates open (Initial, " in section and "\\\n  ‘we beat the wardens to it’\n" in draft
          and "\n  ‘it kept me company, that is all’\n" in draft and "\n  ‘I never threw it out’\n" in draft
          and "‘‘" not in draft and '‘"' not in draft and "‘“" not in draft)
    check("95: 1, a statement with no quote of its own, and one whose place holds (no quote), has no quote line and no break",
          re.search(r"\n- Waking before the alarm \(Initial, [0-9:]+\)\n", draft) is not None
          and re.search(r"\n- The fork left by the water butt \(Initial, [0-9:]+\)\n", draft) is not None
          and "(no quote)" not in draft.lower())
    check("95: 1, the draft lists no picked quotes, every statement carrying its own, and keeps the PET's note",
          not re.search(r'^["“‘]', draft, flags=re.M) and draft.count("we beat the wardens to it") == 1
          and "\nBefore anyone else is up.\n" in section
          and section.index("- Out before the gates open") < section.index("### A1. Waking for it")
          < section.index("#### A1.1 The tin") < section.index("- The fork left by the water butt"))
    check("95: 1, the CSV keeps its four columns in their order and adds the statement's own quote at the end, empty for none",
          rows[0] == ["Interview", "Timestamp", "Experiential statement", "Proposed PET (blank for you)", "Quote"]
          and export_mod.HEADER[:4] == ["Interview", "Timestamp", "Experiential statement", "Proposed PET (blank for you)"]
          and all(len(r) == 5 for r in rows)
          and {r[2]: r[4] for r in rows[1:]}["Waking before the alarm"] == ""
          and {r[2]: r[4] for r in rows[1:]}["The fork left by the water butt"] == ""
          and {r[2]: r[4] for r in rows[1:]}["The seed tin by the back door"] == "I never threw it out"
          and {r[2]: r[3] for r in rows[1:]}["The seed tin by the back door"] == "Early at the plot / Waking for it / The tin")
    plain_out = scratch / "loose-plain.csv"
    export_mod.export(hazel, plain_out, guard=False)
    with open(plain_out, encoding="utf-8-sig", newline="") as handle:
        plain = list(csv.reader(handle))
    check("95: 1, with no board named the CSV still carries the quote column, the PET column empty, transcript order kept",
          plain[0] == export_mod.HEADER and all(len(r) == 5 and r[3] == "" for r in plain[1:])
          and {r[2]: r[4] for r in plain[1:]}["Saving seed from the best plants"] == "the best ones, only the best"
          and {r[2]: r[4] for r in plain[1:]}["A row left for her brother"] == "")

    # ── C. 2, the GETs print's PET tables are the table of PETs, shared code, the bars gone
    books = idiograph_routes.gets_books(root)
    project = idiograph_routes.read_project(root)
    pages = {}
    for labels in (themes_mod.LETTERS, themes_mod.NUMBERS):
        for detail in ("full", "selected"):
            pages[(labels, detail)] = gets_print.page(root, books, dict(project, pet_labels=labels), what="all",
                                                      detail=detail, auto=False)
    pets_part = lambda page: page.split('<section class="part first pets" id="pets">', 1)[1].split('id="table"', 1)[0] \
        if '<section class="part first pets" id="pets">' in page else ""
    case_part = lambda page, who: pets_part(page).split(f'id="pets-{who}"', 1)[1].split('<section class="case">', 1)[0] \
        if f'id="pets-{who}"' in pets_part(page) else ""
    for labels in (themes_mod.LETTERS, themes_mod.NUMBERS):
        full = pages[(labels, "full")]
        placed = main_of(themes_print.page(hazel, "P2 - Hazel", auto=False, labels=labels, unplaced=True, binned=True)).split('<section class="rest">', 1)[0]
        wren_placed = main_of(themes_print.page(wren, "P1 - Wren", auto=False, labels=labels, unplaced=True, binned=True)).split('<section class="rest">', 1)[0]
        check(f"95: 2, a case's PET table in the GETs Full set is the print view's table of PETs, its headings and rows the same, "
              f"under {labels}",
              table_tokens(case_part(full, "Hazel")) == table_tokens(placed) and len(table_tokens(placed)) == 7
              and sorted(table_tokens(case_part(full, "Wren"))) == sorted(table_tokens(wren_placed)),
              str(table_tokens(case_part(full, "Hazel")))[:300])
    full = pages[(themes_mod.LETTERS, "full")]
    part = pets_part(full)
    check("95: 2, the PET tables hold the new rows, a statement and its reference left and its quote right, and no old bars",
          part.count('<div class="item">') == 10 and '<h2 class="pet-title"><span class="number">A.</span>' in part
          and '<p class="kq">‘like gravel on a tin’</p>' in part and 'class="theme' not in part
          and 'class="bar"' not in part and '<table class="statements">' not in part and 'class="picks"' not in part
          and "Nothing in it yet." not in part)
    numbers = pets_part(pages[(themes_mod.NUMBERS, "full")])
    check("95: 2, the PET tables labelled the project's way, PET 1 and PET 1a when it says numbers",
          '<span class="number">PET 1.</span>' in numbers and '<h3 class="sub-title">PET 1a. For someone else</h3>' in numbers
          and '<h3 class="sub-title">A1. For someone else</h3>' in part)
    chosen = pets_part(pages[(themes_mod.LETTERS, "selected")])
    check("95: 2, Selected keeps a row for each PET's picks alone, the statement whose quote it is on the left",
          chosen.count('<div class="item">') == 4 and "Rain on the polytunnel roof" not in chosen
          and table_tokens(case_part(pages[(themes_mod.LETTERS, "selected")], "Hazel"))[1][1] == "Saving seed from the best plants"
          and table_tokens(case_part(pages[(themes_mod.LETTERS, "selected")], "Hazel"))[1][3] == "the best ones, only the best"
          and "Nothing in it yet." not in chosen)
    check("95: 1, 2, nothing was written to either workbook or themes file",
          all(p.read_bytes() == b for p, b in before.items()))

    # ── D. 3, after a restart the page comes back where it was
    op = fn(app, "serverOp")
    boot = app.split("function boot(", 1)[1].split("\nboot();", 1)[0]
    check("95: 3, Restart keeps where the page is before it asks, after the save, and a refused restart keeps nothing",
          "if (op === 'restart') spotKeep();" in op
          and op.index("await savePending()") < op.index("spotKeep();") < op.index("await api('/api/server', { op })")
          and "spotDrop();" in op.split("} catch (err) {", 1)[1] and "location.reload(); return;" in fn(app, "serverBack"))
    page_html = support.page_text()
    check("95: 3, the page's start takes the place once, draws the home screen out of sight meanwhile, and comes back to it "
          "once every script is in, the PETs screen's coming after this one",
          page_html.index('<script src="/shell.js">') < page_html.index('<script src="/distil.js">')
          < page_html.index('<script src="/themes.js">') and
          "const spot = spotTaken();" in boot and "if (spot) $('library').hidden = true;" in boot
          and "loadLibrary(!spot).then(" in boot and "const back = () => comeBack(spot).then(languageAgain, languageAgain)" in boot
          and "if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', back, { once: true });" in boot
          and boot.index("loadLibrary(!spot)") < boot.index("const back = () => comeBack(spot)")
          and boot.rstrip().endswith("else back();\n  }\n}")
          and "async function loadLibrary(show = true) {\n  if (show) {" in app
          and "for (const id of ['work', 'themes', 'traj', 'codes-screen', 'sift', 'sift-search', 'trace']) if ($(id)) $(id).hidden = true;\n    $('library').hidden = false;\n  }" in app)
    check("95: 3, the case opens on the turn it was on, and PETs and GETs on the board, a gone case or board going home",
          "if (!inPlace && opts.at && opts.at.sheet) S.at = stopNear(opts.at.sheet, Number(opts.at.row), S.at);" in fn(app, "startCase")
          and "themesOpen(path, Object.assign({ back, label, to: from === 'work' ? 'statements' : 'cases' }, more));" in app
          and "label: '', to: 'cases' }, more));" in fn(app, "openGets")
          and "if (opts.gone) { $('themes').hidden = true; opts.gone(); return; }" in fn(js, "themesOpen")
          and "const asked = Object.assign(opts.board ? { workbook: path, board: opts.board } : { workbook: path }, TH.scope || {});" in fn(js, "themesOpen")
          and "await api('/api/gets', asked) : await api('/api/themes', asked);" in fn(js, "themesOpen")
          and "if (opts.gone && opts.board && String((data.version || {}).id) !== String(opts.board)) {" in fn(js, "themesOpen")
          and fn(js, "themesOpen").index("if (opts.gone) {") < fn(js, "themesOpen").index("thNote(needsRestart(err)"))
    node = shutil.which("node")
    if not node:
        skip("95: 3, the place kept and the way back in node", "no node on this machine")
    else:
        def whole(head: str) -> str:
            at = app.index(head)
            return app[at:app.index("\n}\n", at) + 3]
        pieces = [app[app.index("const RETURN_KEY = "):app.index("function spotNow(")]]
        pieces += [whole(h) for h in ("function spotNow(", "function spotKeep(", "function spotDrop(", "function spotTaken(",
                                      "async function comeBack(")]
        # Idiograph's screens kept and come back to by its own part since the fifth build (23 October 2026),
        # registered with the family as the page registers it
        pieces += [app[app.index("const familyApp = "):app.index("\n\n", app.index("const familyApp = "))] + "\n",
                   support.distil_hooks(app), whole("function distilSpot("), whole("async function distilComeBack(")]
        script = scratch / "loose-restart.js"
        script.write_text(r"""
const store = new Map();
globalThis.sessionStorage = { getItem: (k) => (store.has(k) ? store.get(k) : null), setItem: (k, v) => store.set(k, String(v)),
  removeItem: (k) => store.delete(k) };
const els = { work: { hidden: true }, themes: { hidden: true }, library: { hidden: false } };
const $ = (id) => els[id];
const S = { data: null, flat: [], stops: [], at: 0 };
const current = () => S.flat[S.stops[S.at]];
// each app's own screen registered by its own script, Idiograph's alone in this piece of the page
const FAMILY_APPS = {};
let TH = { live: false };
let calls = [];
let fails = false;
async function api(route, body) { calls.push(['api', route, body.path]); if (fails) throw new Error('No such case'); return { path: body.path }; }
function startCase(data, opts) { calls.push(['case', data.path, opts.at]); }
function openThemes(path, from, label, more) { calls.push(['pets', path, from, label, more.board, typeof more.gone]); more.gone(); }
function openGets(path, more) { calls.push(['gets', path, more.board, typeof more.gone]); }
function loadLibrary(show) { calls.push(['home', show === undefined ? 'shown' : show]); return Promise.resolve(); }
function say() {}
""" + "\n".join(pieces) + r"""
const out = {};
const book = 'Gardens/P1 - Wren/P1 Wren - EN & ES.xlsx';
// the home screen keeps nothing, and clears what an earlier press kept
store.set(RETURN_KEY, 'stale');
out.home = [spotNow(), (spotKeep(), store.has(RETURN_KEY))];
// the turn screen, on the second of two turns
Object.assign(els.work, { hidden: false });
Object.assign(S, { data: { path: book }, flat: [{ sheet: 'Initial', row: 3 }, { sheet: 'Initial', row: 5 }], stops: [0, 1], at: 1 });
out.work = spotNow();
// PETs from the case list, then from the turn screen, then GETs, and a screen not yet answered
els.work.hidden = true;
els.themes.hidden = false;
TH = { live: true, path: book, meta: { id: 'v3' }, mode: 'pets', label: 'P1 - Wren' };
out.pets = spotNow();
// where its way back goes, TH.to, since the way back's word went on 18 October (area 177)
TH.to = 'statements';
out.under = spotNow();
TH = { live: true, path: 'Gardens/P2 - Hazel/P2 Hazel - EN & ES.xlsx', meta: { id: 'b2' }, mode: 'gets', label: '' };
out.gets = spotNow();
TH = { live: false, path: book, meta: null, mode: 'pets' };
out.dead = spotNow();
// kept, then taken once, and not a second time
TH = { live: true, path: book, meta: { id: 'v3' }, mode: 'pets', label: 'P1 - Wren', to: 'statements' };
spotKeep();
const kept = JSON.parse(store.get(RETURN_KEY));
out.kept = [typeof kept.at, Math.abs(Date.now() - kept.at) < 5000, kept.screen, kept.board, kept.under && kept.under.row];
out.taken = [spotTaken(), spotTaken(), store.has(RETURN_KEY)];
// one older than ten minutes, one of another shape and words that are not JSON are none, and taken away
store.set(RETURN_KEY, JSON.stringify(Object.assign({}, kept, { at: Date.now() - 11 * 60 * 1000 })));
const old = spotTaken();
store.set(RETURN_KEY, JSON.stringify(Object.assign({}, kept, { screen: 'settings' })));
const shape = spotTaken();
store.set(RETURN_KEY, '{not json');
const broken = spotTaken();
out.refused = [old, shape, broken, store.has(RETURN_KEY), RETURN_FOR];
(async () => {
  calls = []; await comeBack({ screen: 'work', path: book, sheet: 'Initial', row: 5 }); out.backWork = calls;
  calls = []; fails = true; await comeBack({ screen: 'work', path: book, sheet: 'Initial', row: 5 }); out.goneCase = calls; fails = false;
  calls = []; await comeBack({ screen: 'pets', path: book, board: 'v3', label: 'P1 - Wren', under: { screen: 'work', path: book, sheet: 'Initial', row: 5 } });
  out.backUnder = calls;
  calls = []; await comeBack({ screen: 'pets', path: book, board: 'v3', label: 'P1 - Wren', under: null }); out.backPets = calls;
  calls = []; await comeBack({ screen: 'gets', path: book, board: 'b2' }); out.backGets = calls;
  calls = []; fails = true; await comeBack({ screen: 'pets', path: book, board: 'v3', under: { screen: 'work', path: book } }); out.goneUnder = calls;
  console.log(JSON.stringify(out));
})();
""", encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = support.plain(json.loads(ran.stdout)) if ran.returncode == 0 and ran.stdout.strip() else {}
        book = "Gardens/P1 - Wren/P1 Wren - EN & ES.xlsx"
        check("95: 3, the place kept is the screen, the case and its turn, PETs' board and the way back to the turn screen, "
              "or GETs' board, and the home screen keeps nothing",
              out.get("home") == [None, False]
              and out.get("work") == {"screen": "work", "path": book, "sheet": "Initial", "row": 5}
              and out.get("pets") == {"screen": "pets", "path": book, "board": "v3", "label": "P1 - Wren", "under": None}
              and (out.get("under") or {}).get("under") == {"screen": "work", "path": book, "sheet": "Initial", "row": 5}
              and out.get("gets") == {"screen": "gets", "path": "Gardens/P2 - Hazel/P2 Hazel - EN & ES.xlsx", "board": "b2"}
              and out.get("dead") is None, (ran.stderr or json.dumps(out))[:400])
        check("95: 3, it is kept in this tab with the time, taken once, and none when it is old, of another shape or broken",
              out.get("kept") == ["number", True, "pets", "v3", 5]
              and (out.get("taken") or [None])[0] and (out.get("taken") or [None])[0]["board"] == "v3"
              and (out.get("taken") or [0, 0, 0])[1:] == [None, False]
              and out.get("refused") == [None, None, None, False, 600000], json.dumps(out.get("refused")))
        check("95: 3, coming back opens the case on its turn, PETs over the case or from the list on the board, GETs on the board, "
              "and a case gone is the home screen",
              out.get("backWork") == [["api", "/api/open", book], ["case", book, {"sheet": "Initial", "row": 5}]]
              and out.get("goneCase") == [["api", "/api/open", book], ["home", "shown"]]
              and out.get("backUnder") == [["api", "/api/open", book], ["case", book, {"sheet": "Initial", "row": 5}],
                                           ["pets", book, "work", "P1 - Wren", "v3", "function"], ["home", "shown"]]
              and out.get("backPets") == [["pets", book, "library", "P1 - Wren", "v3", "function"], ["home", "shown"]]
              and out.get("backGets") == [["gets", book, "b2", "function"]]
              and out.get("goneUnder") == [["api", "/api/open", book], ["home", "shown"]], json.dumps(out)[:600])

    # ── E. 4, board new on a case with no themes file makes Board 1, its dry run and its real run agreeing
    croot = scratch / "loose-cli-root"
    shutil.rmtree(croot, ignore_errors=True)
    ash = demo_copy(croot, "P3 - Ash", "P3 Ash - EN & ES.xlsx")
    (croot / "idiograph-project.json").write_text(json.dumps(
        {"name": "Gardens, a scratch project", "research_question": "How do people keep an allotment going alone?",
         "agents": {"allowed": True, "at": "2026-10-07T10:00:00+01:00"}}), encoding="utf-8")
    cfg_file = scratch / "loose-cli-config.json"
    cfg_file.write_text(json.dumps({"root": str(croot), "interviewer": "Adam"}), encoding="utf-8")
    spec = scratch / "loose-board.json"
    spec.write_text(json.dumps({"pets": [{"title": "The stair before light", "members": ["S1", "S2"]}],
                                "not_placed": {"S3": "An invented reason it fits no PET"}}), encoding="utf-8")
    side = themes_mod.themes_path(ash)
    saved = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        cmd = lambda *a: cli.run(["--root", str(croot), "--config", str(cfg_file), *a])
        code_d, out_d, err_d = cmd("board", "new", "Ash", "--from", str(spec), "--dry-run", "--json")
        dry = support.plain(json.loads(out_d)) if code_d == 0 else {}
        check("95: 4, the dry run on a case with no themes file names Board 1 and writes nothing",
              code_d == 0 and dry.get("name") == "Board 1" and not side.exists(), flat(out_d + err_d)[:200])
        code_r, out_r, err_r = cmd("board", "new", "Ash", "--from", str(spec), "--note", "One board", "--tool", "Claude Code",
                                   "--json")
        made = support.plain(json.loads(out_r)) if code_r == 0 else {}
        stored = themes_mod.load(ash) or {}
        boards = stored.get("boards") or []
        check("95: 4, the real run writes the board asked for as Board 1, the file's only board, with no empty seed before it, "
              "as its dry run said",
              code_r == 0 and made.get("name") == dry.get("name") == "Board 1" and made.get("id") == "v1"
              and [b.get("name") for b in boards] == ["Board 1"] and stored.get("current") == "v1"
              and len(boards[0].get("groups") or []) == 1 and made["said"].startswith("Made Board 1 on ")
              and made["said"].endswith("nothing else changed."), flat(made.get("said") or err_r)[:200])
        code_2, out_2, _ = cmd("board", "new", "Ash", "--from", str(spec), "--dry-run", "--json")
        code_3, out_3, _ = cmd("board", "new", "Ash", "--from", str(spec), "--note", "Another", "--tool", "Claude Code", "--json")
        check("95: 4, on a case with a file the next board is Board 2, the dry run and the real run agreeing again",
              code_2 == 0 and code_3 == 0 and support.plain(json.loads(out_2))["name"] == support.plain(json.loads(out_3))["name"] == "Board 2"
              and [b.get("name") for b in themes_mod.load(ash)["boards"]] == ["Board 1", "Board 2"])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = saved
    page_book = demo_copy(croot, "P4 - Elm", "P4 Elm - EN & ES.xlsx")
    read = themes_mod.read_cards(page_book)
    proposed = themes_mod.blank_version(read["cards"])
    themes_mod.version_op(page_book, themes_mod.PROPOSE, {"version": proposed, "note": "From the page"}, "P4 - Elm")
    check("95: 4, the page's own AI board on a case with no file keeps the board it shows as Board 1, only the command line "
          "asks for none",
          [b.get("name") for b in themes_mod.load(page_book)["boards"]] == ["Board 1", "Board 2"]
          and '"seed": False' in inspect_mod.getsource(idiograph_cli.make_board)
          and 'body.get("seed") is False' in inspect_mod.getsource(themes_mod.version_op))
