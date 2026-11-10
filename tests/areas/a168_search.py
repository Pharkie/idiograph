from __future__ import annotations

import hashlib
import http.server
import inspect
import json
import os
import re
import shutil
import subprocess
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from . import support
from .support import DEMO_SHEET, add_second_sheet, check, demo_copy, demo_sheet, skip
import idiograph_routes
import idiograph_find


def test_search(scratch):
    print("\n168. Search across Distil, build 1 of 2: one field over a case's passages, interviewer notes, statements, key "
          "quotes and exploratory notes, its PETs, sub-themes, their notes, sticky notes and board notes, and with This "
          "project every case, the GETs and their notes, the participant notes, the cases and the research question, "
          "This case on the statements screen and PETs and This project on a project's page and GETs, Cmd + F in Find's "
          "place, read-only, 17 October, Adam's word")
    import app_search
    import gets as gets_mod
    import server as server_mod
    import themes as themes_mod
    import workbook as wb_mod

    read = lambda path: Path(path).read_text(encoding="utf-8")
    app, sjs, siftjs = support.text("family/static/shell.js", "apps/idiograph/static/distil.js"), support.text("family/static/search.js"), support.text("apps/sift/static/sift.js")
    source = read(support.source("family/app_search.py"))
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: ("async " if f"async function {name}(" in src else "") + f"function {name}(" + fn(src, name) + "\n}"
    line_of = lambda src, start: next((ln for ln in src.splitlines() if ln.startswith(start)), "")
    node = shutil.which("node")

    # ── A. matching: every word, in any order, case and accents aside, as Sift's find boxes match
    fold, words_of, matches = app_search.fold, app_search.words_of, app_search.matches
    check("168: a word folds as tbFindMatch folds it, its accents off and in lower case, and every word typed is found "
          "in any order, one missing finding nothing",
          fold("Café Crème") == "cafe creme" and words_of("  Walk  DOG walk ") == ["walk", "dog"]
          and matches(fold("The dog's early walk"), words_of("walk dog")) and matches(fold("Naïve façade"), words_of("FACADE naive"))
          and not matches(fold("The dog's early walk"), words_of("walk cat")) and not matches(fold("anything"), [])
          and matches(fold("Mornings"), words_of("morn")))
    long_text = "Before. " + "word " * 80 + "the plot at first light " + "more " * 80
    cut = app_search.snippet(long_text, words_of("plot"))
    check("168: a long passage is cut to a window round the first word found, an ellipsis at each end it was cut at, and a "
          "short one stands whole",
          cut.startswith("…") and cut.endswith("…") and "the plot at first light" in cut
          and len(cut) <= app_search.SNIPPET + 2 and app_search.snippet("A short line", ["short"]) == "A short line", cut)

    # ── B. an invented project: three allotment holders, every word of their workbooks the demo's invented ones
    base = scratch / "search-168"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Allotment study"
    books = {name: demo_copy(root, name, f"{name} - EN & ES.xlsx") for name in ("Isla", "Ivo", "Tam")}
    add_second_sheet(books["Tam"], "2d", rows=6)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Allotment study",
        "research_question": "How do people experience keeping an allotment through the seasons?"}), encoding="utf-8")
    sheet, her, him = demo_sheet(books["Isla"])
    asked = next(r for r in sheet["rows"] if r["name"] == him)
    wb_mod.save_interviewer_note(books["Isla"], DEMO_SHEET, asked["row"], "Asked too soon about the frost", him)
    cards = themes_mod.read_cards(books["Isla"])["cards"]
    keys = [c["key"] for c in cards]
    board = themes_mod.blank_version(cards)
    board.update(id="v1", name="Board 1", note="Beds before breakfast", groups=[
        {"id": "g1", "label": "Digging before work", "members": keys[0:2] + ["g3"], "x": 0, "y": 0,
         "note": "Kneeling in the wet soil"},
        {"id": "g3", "label": "Frost on the beds", "members": [keys[2]], "x": 0, "y": 200},
        {"id": "g2", "label": "Sharing the shed", "members": [keys[4]], "x": 3000, "y": 0}],
        notes=[{"id": "n1", "text": "Ask about the frost again", "colour": "yellow", "x": 0, "y": -400, "in": "g1"}])
    themes_mod.write(books["Isla"], {"schema": 2, "case": "Isla", "workbook": books["Isla"].name, "current": "v1",
                                     "boards": [board]})
    other = themes_mod.blank_version(themes_mod.read_cards(books["Ivo"])["cards"])
    other.update(id="v1", name="Board 1", groups=[{"id": "g1", "label": "Watering at dusk", "members": keys[6:8], "x": 0, "y": 0}])
    themes_mod.write(books["Ivo"], {"schema": 2, "case": "Ivo", "workbook": books["Ivo"].name, "current": "v1", "boards": [other]})
    saved = (server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_MEMORY = {"recent": []}
    isla = str(books["Isla"])
    try:
        shown = idiograph_routes.api_gets({"workbook": isla})
        gcards = {c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in shown["cards"]}
        gcards["Tam/pn/1"] = {"x": 1400, "y": 0, "text": "Keeps a notebook of first frosts"}
        body = dict(shown["version"], cards=gcards, discarded=[], picks={},
                    groups=[{"id": "G1", "label": "Mornings among the beds", "members": ["Isla/g1", "Ivo/g1"], "x": 0, "y": -60,
                             "note": "Each holder's day starts at the plot"}],
                    notes=[{"id": "n9", "text": "Is the plot a duty or a refuge?", "colour": "pink", "x": 1400, "y": 400}],
                    rows={"G1": {"Ivo": {"note": "His dusk is her dawn"}}})
        idiograph_routes.api_gets_save({"workbook": isla, "version": body})
        idiograph_routes.api_gets_ops({"workbook": isla, "op": "note", "id": shown["version"]["id"], "note": "A first pass across the plots"})
        gfile = gets_mod.gets_path(root)

        # ── C. scope
        one = server_mod.api_search({"q": "frost", "scope": "case", "path": isla})
        all_ = server_mod.api_search({"q": "frost", "scope": "project", "path": isla})
        by_root = server_mod.api_search({"q": "frost", "scope": "project", "root": str(root)})
        check("168: This case reaches the case's workbook and themes file alone, its kinds the case's ten, and no case or "
              "sheet filters",
              set(one["counts"]) == set(idiograph_find.CASE_KINDS) and one["scope"] == "case"
              and {r["kind"] for r in one["results"]} == {"inote", "sub", "sticky"} and not one["cases"] and not one["sheets"]
              and all(r["case"] == "Isla" for r in one["results"]), str([(r["kind"], r["text"]) for r in one["results"]]))
        check("168: This project reaches every case, the GETs file and the project, through a case's path or the project's "
              "id alike, the cases in case order with their counts",
              set(all_["counts"]) == set(idiograph_find.KINDS)
              and {r["kind"] for r in all_["results"]} == {"inote", "sub", "sticky", "pnote"}
              and [c["name"] for c in all_["cases"]] == ["Isla", "Ivo", "Tam"]
              and json.dumps(all_["results"]) == json.dumps(by_root["results"]), str(all_["counts"]))
        refused = {}
        for name, call in (("no scope", {"q": "x", "path": isla}), ("case without path", {"q": "x", "scope": "case", "root": str(root)}),
                           ("nothing", {"q": "x", "scope": "project"})):
            try:
                server_mod.api_search(call)
            except Exception as exc:
                refused[name] = type(exc).__name__
        try:
            server_mod.api_search({"q": "x", "scope": "case", "path": str(base / "elsewhere.xlsx")})
        except server_mod.OutsideRoot:
            refused["outside"] = "OutsideRoot"
        check("168: a search that names no scope, a case search with no case, one with no project, and a workbook outside "
              "every root are refused, nothing searched",
              refused == {"no scope": "WorkbookError", "case without path": "WorkbookError", "nothing": "WorkbookError",
                          "outside": "OutsideRoot"}, str(refused))

        # ── D. every kind found, where it is and where a click lands
        statement = cards[0]
        quote = next(q for row in themes_mod.read_cards(books["Isla"])["quotes"].values() for q in row["quotes"])
        enote = next(r for r in sheet["rows"] if r["en"].strip())
        passage = next(r for r in sheet["rows"] if r["name"] == her and len(r["text"].split()) > 8)
        asks = {"passage": passage["text"], "inote": "too soon frost", "statement": statement["text"],
                "quote": quote["text"], "enote": enote["en"].split("\n")[0], "pet": "digging work",
                "sub": "frost beds", "petnote": "kneeling soil", "sticky": "frost again", "boardnote": "beds breakfast",
                "get": "mornings beds", "getnote": "holder's plot", "rownote": "dusk dawn", "pnote": "notebook frosts",
                "case": "tam", "question": "allotment seasons"}
        found = {}
        for kind, q in asks.items():
            got = server_mod.api_search({"q": q, "scope": "project", "path": isla, "kinds": [kind]})
            found[kind] = got["results"][0] if got["results"] else None
        missing = [k for k, r in found.items() if not r or r["kind"] != k]
        check("168: each of the sixteen kinds is found, a passage, an interviewer note, a statement, a key quote, an "
              "exploratory note, a PET, a sub-theme, a PET note, a sticky note, a board note, a GET, its note, a row note, a "
              "participant note, a case and the research question", not missing and set(asks) == set(idiograph_find.KINDS),
              str(missing))
        go = {k: (r or {}).get("go", {}) for k, r in found.items()}
        check("168: a workbook's result lands on the statements screen at its sheet and row, in its field and line: the "
              "passage, the interviewer's note, the statement's and the quote's pair and the notes",
              all(go[k]["screen"] == "statements" and go[k]["sheet"] == DEMO_SHEET and go[k]["path"] for k in idiograph_find.SHEET_KINDS)
              and go["statement"]["row"] == statement["row"] and go["statement"]["line"] == statement["line"]
              and go["statement"]["field"] == "es" and go["quote"]["field"] == "kq" and go["enote"]["field"] == "en"
              and go["inote"]["field"] == "note" and go["inote"]["row"] == asked["row"] and go["passage"]["field"] == "passage"
              and found["statement"]["where"].startswith(f"{DEMO_SHEET} ") and found["passage"]["case"] in ("Isla", "Ivo", "Tam"),
              str(go["statement"]))
        check("168: a board's result lands on PETs on its board with its PET, sub-theme or sticky note to select, where it "
              "is named by the board and the PET's mark as the print view gives it, \"Board 1 · PET A\"",
              go["pet"] == {"screen": "pets", "board": "v1", "item": "group", "id": "g1", "path": go["pet"]["path"]}
              and found["pet"]["where"] == "Board 1 · PET A" and found["sub"]["where"] == "Board 1 · A1"
              and go["sub"]["id"] == "g3" and go["petnote"]["id"] == "g1" and go["sticky"]["item"] == "sticky"
              and go["sticky"]["id"] == "n1" and found["sticky"]["where"] == "Board 1 · PET A"
              and go["boardnote"]["item"] == "board" and found["boardnote"]["where"] == "Board 1"
              and server_mod.abs_path(go["pet"]["path"]).resolve() == books["Isla"].resolve(), str(go["pet"]))
        check("168: a GETs result lands on GETs on its board with the GET or the participant note's card to select, GETs and "
              "the board named where it is, and a case or the research question on the project's page",
              go["get"]["screen"] == "gets" and go["get"]["item"] == "group" and go["get"]["id"] == "G1"
              and found["get"]["where"] == "GETs · Board 1" and found["getnote"]["where"] == "GETs · Board 1 · Mornings among the beds"
              and go["rownote"]["id"] == "G1" and found["rownote"]["case"] == "Ivo"
              and go["pnote"] == dict(go["pnote"], item="card", id="Tam/pn/1") and found["pnote"]["case"] == "Tam"
              and go["case"] == {"screen": "project", "id": idiograph_routes.project_id(root), "case": "Tam"}
              and go["question"]["screen"] == "project" and found["question"]["where"] == "Allotment study", str(go["pnote"]))

        # ── E. the filters: a group's ticks narrow the results, its own counts kept, the others' counted with them
        # a letter on its own, found inside longer words, so Whole word, which the route has on unless told, is off here
        part = {"q": "e", "scope": "project", "path": isla, "whole_word": False}
        wide = server_mod.api_search(dict(part))
        kinds = server_mod.api_search(dict(part, kinds=["statement"]))
        tam = server_mod.api_search(dict(part, cases=["Tam"]))
        second = server_mod.api_search(dict(part, sheets=["2d"]))
        check("168: a kind ticked shows that kind alone and leaves the kinds' counts as they were, a case ticked counts the "
              "kinds of that case, a sheet ticked the sheet's, and the first 200 stand in the list with the total beside",
              {r["kind"] for r in kinds["results"]} == {"statement"} and kinds["counts"] == wide["counts"]
              and kinds["total"] == wide["counts"]["statement"]
              and {r["case"] for r in tam["results"]} == {"Tam"} and sum(tam["counts"].values()) == tam["total"]
              and {r["sheet"] for r in second["results"]} == {"2d"} and [s["name"] for s in wide["sheets"]] == [DEMO_SHEET, "2d"]
              and len(wide["results"]) == min(wide["total"], app_search.LIMIT) and wide["total"] > app_search.LIMIT,
              f"{wide['total']} {kinds['total']} {tam['total']} {second['total']}")
        empty = server_mod.api_search({"q": "   ", "scope": "project", "path": isla})
        none = server_mod.api_search({"q": "zzzqqq", "scope": "case", "path": isla})
        check("168: nothing typed finds nothing, and words found nowhere answer with none and every count at nought",
              not empty["results"] and not empty["total"] and not none["results"] and not any(none["counts"].values()))

        # ── F. read-only, held in memory against each file's time and size
        def snapshot():
            return {str(p.relative_to(base)): (p.stat().st_mtime_ns, p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())
                    for p in sorted(base.rglob("*")) if p.is_file()}

        before = snapshot()
        app_search.HELD.clear()
        calls = []
        real = idiograph_find.workbook_items
        idiograph_find.workbook_items = lambda path: (calls.append(Path(path).name), real(path))[1]
        try:
            server_mod.api_search({"q": "frost", "scope": "project", "path": isla})
            first = len(calls)
            server_mod.api_search({"q": "beds", "scope": "project", "path": isla, "kinds": ["pet"]})
            again = len(calls) - first
            t = books["Ivo"].stat()
            os.utime(books["Ivo"], ns=(t.st_atime_ns, t.st_mtime_ns + 1_000_000_000))
            server_mod.api_search({"q": "beds", "scope": "project", "path": isla})
            touched = calls[first + again:]
        finally:
            idiograph_find.workbook_items = real
        os.utime(books["Ivo"], ns=(t.st_atime_ns, t.st_mtime_ns))
        check("168: each workbook is read once and held against its time and size, the next search reading none, and one "
              "that changed read again alone", first == 3 and again == 0 and touched == [books["Ivo"].name],
              f"{first} {again} {touched}")
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
        threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
        port = httpd.server_address[1]
        got = {}
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/api/search", method="POST",
                                         data=json.dumps({"q": "frost", "scope": "project", "path": isla}).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=20) as r:
                got["post"] = (r.status, json.loads(r.read().decode("utf-8")))
            query = urllib.parse.urlencode({"q": "frost", "scope": "case", "path": isla})
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/search?{query}", timeout=20) as r:
                got["get"] = (r.status, json.loads(r.read().decode("utf-8")))
            far = urllib.request.Request(f"http://127.0.0.1:{port}/api/search", method="POST",
                                         data=json.dumps({"q": "frost", "scope": "case", "path": str(base / "x.xlsx")}).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
            try:
                urllib.request.urlopen(far, timeout=20)
            except urllib.error.HTTPError as exc:
                got["far"] = exc.code
        finally:
            httpd.shutdown()
            httpd.server_close()
        after = snapshot()
        check("168: over HTTP the route answers a POST and a GET alike, a workbook outside every root refused with 403, "
              "and every search writes nothing, no file of the project changed and none added, no index on disk, and the "
              "recent list untouched",
              got.get("post", (0, {}))[0] == 200 and len(got["post"][1]["results"]) == len(all_["results"])
              and got.get("get", (0, {}))[0] == 200 and got["get"][1]["scope"] == "case" and got.get("far") == 403
              and before == after and server_mod.STATE_MEMORY == {"recent": []} and gfile.exists()
              and not re.search(r"\.write|json\.dump\(|save_json|open\([^)]*['\"]w", source)
              and not re.search(r"remember\(|save_json|\.write|writing\(",
                                inspect.getsource(server_mod.api_search) + inspect.getsource(idiograph_routes.search_cases)),
              str({k: v if not isinstance(v, tuple) else v[0] for k, v in got.items()}))
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = saved

    # ── G. the page: the keys in the results
    walk = sjs.split("$('search').addEventListener('keydown', (e) => {", 1)[1].split("\n  });", 1)[0]
    check("168: the arrows walk the results, Enter opens the one in focus, Esc closes the card, and a click outside it or "
          "on Search again puts it away",
          "searchStep(1)" in walk and "searchStep(-1)" in walk and "searchGo(SEARCH.at)" in walk and "closeSearch(); return;" in walk
          and "if (searchOpen()) closeSearch(); else openSearch();" in sjs
          # a click on a result goes no further, so the screen never takes it for a click away from a note it opened
          and "e.stopPropagation();\n    searchGo(Number(hit.dataset.n));" in sjs
          and "e.target.closest(`#search, ${SEARCH_BUTTONS.map((id) => `#${id}`).join(', ')}`)" in sjs
          and "const SEARCH_BUTTONS = ['btn-search', 'th-search', 'tj-search', 'cd-search', 'lib-search', 'sf-search', 'sfs-search', 'tr-search'];" in sjs)

    # ── H. in node: the key, the scopes, the marks and the match beside Sift's
    if not node:
        skip("168: Search in node", "node is not on this machine")
    else:
        esc_line = line_of(app, "const esc = ")
        code = "\n".join([
            "let MAC = true;", "const MOD = (e) => (MAC ? e.metaKey : e.ctrlKey);", esc_line,
            "const els = { work: { hidden: true }, themes: { hidden: true }, library: { hidden: false }, 'home-project': { hidden: true }, 'home-pick': { hidden: false }, search: { hidden: true } };",
            "const $ = (id) => els[id];", "let S = { data: null, home: '' };", "let TH = { path: '', mode: 'pets' };",
            "const SF = { folder: '' };", "const SFS = { folder: '' };", "const TR = { folder: '' };",
            # each app's own screen registered by its own script, Idiograph's alone in this piece of the page, its
            # screens told by its own part since the fifth build (23 October 2026)
            "const FAMILY_APPS = {};", support.distil_hooks(app), whole(app, "distilSearchWhere"),
            "const document = { querySelectorAll: () => [] };",
            "let overlay = false;", "const anyOverlayOpen = () => overlay;", "let opened = 0;", "function openSearch() { opened += 1; return true; }",
            "function closeSearch() {}", line_of(sjs, "const searchOpen = "), line_of(sjs, "const searchShown = "),
            line_of(sjs, "const searchPlain = "), line_of(sjs, "const searchFold = "), line_of(sjs, "const SEARCH_ALNUM = "),
            line_of(sjs, "const searchCovered = "),
            whole(sjs, "searchScopes"), whole(sjs, "searchWhere"), whole(sjs, "searchKey"), whole(sjs, "searchMarked"),
            whole(support.table_js(), "tbFindMatch"),
        ]) + r"""
function press(m) {
  const e = { key: 'f', code: 'KeyF', metaKey: !!m.meta, ctrlKey: !!m.ctrl, shiftKey: !!m.shift, altKey: !!m.alt,
    defaultPrevented: false, preventDefault() { this.defaultPrevented = true; }, stopPropagation() {} };
  searchKey(e);
  return e.defaultPrevented;
}
const out = {};
out.picker = press({ meta: true });
els['home-project'].hidden = false; S.home = 'p1'; out.project = press({ meta: true });
els.library.hidden = true; els.work.hidden = false; S.data = { path: 'x' };
out.statements = press({ meta: true }); out.shift = press({ meta: true, shift: true }); out.alt = press({ meta: true, alt: true });
overlay = true; out.overlay = press({ meta: true }); overlay = false;
els.work.hidden = true; els.themes.hidden = false; TH.path = 'x'; out.pets = press({ meta: true });
TH.mode = 'gets'; out.gets = press({ meta: true });
els.themes.hidden = true; out.elsewhere = press({ meta: true });
MAC = false; els.work.hidden = false; out.ctrl = press({ ctrl: true }); out.metaOff = press({ meta: true });
out.opened = opened;
out.scopes = ['statements', 'pets', 'gets', 'project'].map((screen) => searchScopes({ screen }));
out.marked = searchMarked('Café walks & dogs, the WALK', 'cafe walk');
out.folds = ['Café Crème', 'Naïve façade', 'ÀÉÎÕÜ'].map(searchFold);
const pairs = [['The dog\'s early walk', 'walk dog'], ['Naïve façade', 'FACADE naive'], ['The early walk', 'walk cat'], ['x', '']];
out.match = pairs.map(([w, q]) => tbFindMatch(w, q));
console.log(JSON.stringify(out));
"""
        script = scratch / "search-168.js"
        script.write_text(code, encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        o = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
        check("168, updated 18 October (178): in node, Cmd + F opens Search on the picker, the statements screen, PETs, GETs "
              "and a project's page, Ctrl + F off a Mac, and the browser keeps its own with no screen in front, under a card "
              "of the app's own, with Shift or Alt held and Cmd off a Mac",
              o.get("picker") is True and o.get("project") is True and o.get("statements") is True and o.get("shift") is False
              and o.get("alt") is False and o.get("overlay") is False and o.get("pets") is True and o.get("gets") is True
              and o.get("elsewhere") is False and o.get("ctrl") is True and o.get("metaOff") is False and o.get("opened") == 6,
              run.stdout + run.stderr[:300])
        check("168, updated 18 October (178): in node, This case, This project and Everything on the statements screen and "
              "PETs, This project and Everything on GETs and a project's page",
              o.get("scopes") == [["case", "project", "all"], ["case", "project", "all"], ["project", "all"], ["project", "all"]],
              str(o.get("scopes")))
        check("168: in node, every word typed is under the wash wherever it stands, case and accents aside, the words set as "
              "written and escaped",
              o.get("marked") == '<mark class="search-mark">Café</mark> <mark class="search-mark">walk</mark>s &amp; dogs, '
                                 'the <mark class="search-mark">WALK</mark>', str(o.get("marked")))
        py_match = [matches(fold(w), words_of(q)) for w, q in (("The dog's early walk", "walk dog"), ("Naïve façade", "FACADE naive"),
                                                                 ("The early walk", "walk cat"), ("x", ""))]
        check("168: in node, the page folds as the server does, and the server matches as Sift's find boxes match",
              o.get("folds") == [fold(s) for s in ("Café Crème", "Naïve façade", "ÀÉÎÕÜ")] and o.get("match")[:3] == py_match[:3],
              f"{o.get('folds')} {o.get('match')} {py_match}")

    # ── I. the builds ship the module
    check("168: the Mac build ships app_search, the module Search runs on",
          all("app_search" in support.build_mac().modules(app) for app in ("idiograph", "sift", "trace")))
