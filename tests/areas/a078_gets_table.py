from __future__ import annotations

import inspect
import json
import re
import shutil
from pathlib import Path

from workbook import WorkbookError

from . import support
from .support import check, skip
import idiograph_routes


def test_gets_table(scratch):
    print("\n78. GETs: the GET table and its rows, the audit trail, Open beside this one and the PDF exports")
    import hashlib
    import subprocess
    import gets as gets_mod
    import gets_print
    import server as server_mod
    import themes as themes_mod

    page = support.page_text()
    js = support.text("apps/idiograph/static/themes.js")
    print_src = support.source("apps/idiograph/gets_print.py").read_text(encoding="utf-8")
    fn = lambda text, name: text.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in text else ""

    def refused(call):
        try:
            call()
        except WorkbookError as exc:
            return str(exc)
        return ""

    # ── the fixture: the demo's three invented cases as ordinary cases of a scratch root, Juno with no
    # PETs, Rowan and Mabel with their marked boards, and a stand-in recording for Juno's sheet
    root = scratch / "gets-table-root"
    shutil.rmtree(root, ignore_errors=True)
    pristine = support.DEMO_PRISTINE
    for name in ("Juno", "Rowan", "Mabel"):
        (root / name / "Working").mkdir(parents=True)
        shutil.copy2(pristine / f"{name} - EN & ES.xlsx", root / name / f"{name} - EN & ES.xlsx")
        for side in sorted((pristine / "Working").glob(f"{name} - *")):
            shutil.copy2(side, root / name / "Working" / side.name)
    shutil.copy2(support.source("demo/idiograph-project.json"), root / "idiograph-project.json")
    recording = root / "Juno" / "Source" / "Initial" / "Source" / "Juno-Initial.m4a"
    recording.parent.mkdir(parents=True)
    recording.write_bytes(b"\x00" * 64)
    books = {name: root / name / f"{name} - EN & ES.xlsx" for name in ("Juno", "Rowan", "Mabel")}
    workbook_sha = lambda: {n: hashlib.sha256(p.read_bytes()).hexdigest() for n, p in books.items()}
    before_sha = workbook_sha()
    saved = (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_MEMORY = {"recent": []}
    any_book = str(books["Rowan"])
    gfile = gets_mod.gets_path(root)

    def snapshot_tree():
        return {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in sorted(root.rglob("*")) if p.is_file()}

    try:
        shown = idiograph_routes.api_gets({"workbook": any_book})
        cases = {c["case"]: c for c in shown["cases"]}
        juno_line = next(k for k, ln in cases["Juno"]["lines"].items() if ln["quotes"])
        mabel_line = next(k for k, ln in cases["Mabel"]["lines"].items() if ln["quotes"] and ln["pet"] not in ("g1", None))
        check("78: each case of the Cases panel carries the workbook and the board Open beside opens, and the answer the print view",
              all(c["path"] and Path(server_mod.abs_path(c["path"])).name.endswith(" - EN & ES.xlsx") for c in shown["cases"])
              and cases["Rowan"]["board"] == "v1" and cases["Juno"]["board"] == "" and "workbook" not in cases["Rowan"]
              and shown["gets_print"] == "/gets/print" and Path(server_mod.abs_path(shown["root"])).resolve() == root.resolve()
              and shown["rows"] == {})
        cards = {c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in shown["cards"]}
        cards.update({"Rowan/g1": {"x": 0, "y": 0}, "Mabel/g1": {"x": 240, "y": 0}, "Rowan/g2": {"x": 0, "y": 400},
                      f"Mabel/es/{mabel_line}": {"x": 480, "y": 0, "text": ""}, f"Juno/es/{juno_line}": {"x": 720, "y": 0, "text": ""},
                      "Rowan/g4": {"x": 1400, "y": 0}, "Juno/pn/1": {"x": 1640, "y": 0, "text": "Invented: she trained dogs once."}})
        groups = [{"id": "G1", "label": "Days given a shape", "note": "Mornings and evenings.",
                   "members": ["Rowan/g1", "Mabel/g1", f"Mabel/es/{mabel_line}", f"Juno/es/{juno_line}", "G3"], "x": 0, "y": -60},
                  {"id": "G3", "label": "Early starts", "members": ["Rowan/g2"], "x": 0, "y": 360},
                  {"id": "G2", "label": "Losing the dog", "members": ["Rowan/g4", "Juno/pn/1"], "x": 1400, "y": -60}]
        rows = {"G1": {"Mabel": {"quote": "", "note": "Her row, an invented note."}},
                "G2": {"Rowan": {"quote": "", "note": ""}}, "G9": {"Rowan": {"quote": "Initial:9:0", "note": "gone"}}}
        body = dict(shown["version"], cards=cards, groups=groups, discarded=[], picks={}, notes=[], rows=rows)
        idiograph_routes.api_gets_save({"workbook": any_book, "version": body})
        data = json.loads(gfile.read_text(encoding="utf-8"))
        board = data["boards"][0]
        check("78: the row note saved in the board's rows, a row with neither left out and a GET not on the board dropped",
              board["rows"] == {"G1": {"Mabel": {"quote": "", "note": "Her row, an invented note."}}})
        idiograph_routes.api_gets_save({"workbook": any_book, "version": {k: v for k, v in body.items() if k != "rows"}})
        check("78: a save from a page before the rows keeps the rows the file holds",
              json.loads(gfile.read_text(encoding="utf-8"))["boards"][0]["rows"] == board["rows"]
              and idiograph_routes.api_gets({"workbook": any_book})["rows"] == board["rows"])

        # ── A. the table: every case of the study in every GET, the empty ones saying so
        data = json.loads(gfile.read_text(encoding="utf-8"))
        table = gets_mod.table(data, data["boards"][0], ["Rowan", "Mabel", "Juno"])
        by = {g["id"]: g for g in table}
        check("78: each GET in canvas order, its sub-themes inside it, and a row for every case of the study in case order",
              [g["id"] for g in table] == ["G1", "G2"] and all([r["case"] for r in g["rows"]] == ["Juno", "Mabel", "Rowan"] for g in table)
              and by["G1"]["note"] == "Mornings and evenings." and by["G1"]["subs"] == ["Early starts"])
        g1 = {r["case"]: r for r in by["G1"]["rows"]}
        g2 = {r["case"]: r for r in by["G2"]["rows"]}
        check("78: a row holds the case's PETs, sub-themes and statements under the GET in the order the canvas reads, with sheet and timecode",
              [i["kind"] for i in g1["Rowan"]["items"]] == ["pet", "pet"] and g1["Rowan"]["items"][1]["within"] == ["Early starts"]
              and [i["kind"] for i in g1["Mabel"]["items"]] == ["pet", "es"] and g1["Mabel"]["items"][1]["sheet"] == "Initial"
              and g1["Mabel"]["items"][1]["time"] and g1["Mabel"]["items"][1]["quotes"] and "notes" in g1["Mabel"]["items"][1])
        check("78: a case with nothing under a GET has its row, empty, and a participant note alone never counts it",
              not g2["Mabel"]["counted"] and g2["Mabel"]["items"] == [] and not g2["Juno"]["counted"]
              and [i["kind"] for i in g2["Juno"]["items"]] == ["pn"] and by["G2"]["count"] == 1 and by["G1"]["count"] == 3
              and gets_mod.NOTHING == "Nothing under this GET" and "const GT_NOTHING = t('themes.gets.nothing_under');" in js)
        rowan = themes_mod.load(books["Rowan"])["boards"][0]["picks"]
        mabel_picks = themes_mod.load(books["Mabel"])["boards"][0]["picks"]
        check("78: the key quote starts as the first pick of the participant's highest PET there",
              g1["Rowan"]["quote"]["key"] == rowan["g1"][0] and g1["Mabel"]["quote"]["key"] == mabel_picks["g1"][0]
              and not g1["Rowan"]["chosen"] and g1["Juno"]["quote"]["key"].startswith(juno_line.rsplit(":", 1)[0] + ":"))
        ticked = cases["Mabel"]["lines"][mabel_line]
        tick_key = f"{ticked['sheet']}:{ticked['row']}:0"
        body["rows"] = {"G1": {"Mabel": {"quote": tick_key, "note": "Her row, an invented note."}, "Rowan": {"quote": "Initial:999:0", "note": ""}}}
        idiograph_routes.api_gets_save({"workbook": any_book, "version": body})
        data = json.loads(gfile.read_text(encoding="utf-8"))
        g1 = {r["case"]: r for r in gets_mod.table(data, data["boards"][0], ["Rowan", "Mabel", "Juno"])[0]["rows"]}
        check("78: a tick makes another quote the row's key quote, and a tick the copy no longer holds falls back",
              g1["Mabel"]["quote"]["key"] == tick_key and g1["Mabel"]["chosen"] and g1["Mabel"]["note"] == "Her row, an invented note."
              and g1["Rowan"]["quote"]["key"] == rowan["g1"][0] and not g1["Rowan"]["chosen"])

        # ── B. the audit trail's paths, and from here on nothing is written
        tree_before = snapshot_tree()
        recs = data["cases"]
        nodes = gets_print.tree(g1["Rowan"], recs["Rowan"], True, False)
        pet = nodes[0]
        under_pet = list(gets_print.walk([pet]))
        lines_of = gets_mod.pet_lines(recs["Rowan"], "g1")
        check("78: a PET draws its path through its statements and their quotes to their turns, a turn's statements together",
              pet["col"] == 3 and pet["kind"] == "pet" and pet["kids"] and all(k["col"] == 2 and k["kind"] == "es" for k in pet["kids"])
              and all(q["col"] == 1 and q["kids"][0]["col"] == 0 and q["kids"][0]["kind"] == "turn"
                      for k in pet["kids"] for q in k["kids"] if q["kind"] == "quote")
              and sum(len(n["statements"]) for n in under_pet if n["kind"] == "es") == len(lines_of)
              and len({(recs["Rowan"]["lines"][k]["sheet"], recs["Rowan"]["lines"][k]["row"]) for k in lines_of})
              == len([n for n in under_pet if n["kind"] == "es"]))
        check("78: a sub-theme draws its own path, in the PET column, naming the GET's sub-theme it sits in",
              nodes[1]["kind"] == "pet" and nodes[1]["within"] == ["Early starts"]
              and gets_print.tree({"items": [dict(g1["Rowan"]["items"][1], kind="sub")], "quote": None}, recs["Rowan"], True, False)[0]["kind"] == "sub"
              and 'Sub-theme' in gets_print.cell_html({"kind": "sub", "title": "A", "within": [], "col": 3}, 3, None))
        direct = gets_print.tree({"items": [g1["Mabel"]["items"][1]], "quote": None}, recs["Mabel"], True, False)
        rows_ = gets_print.flatten({"label": "G"}, direct)
        check("78: a statement draws its path through its quotes to its turn, its line crossing the PET column",
              direct[0]["col"] == 2 and direct[0]["kids"][0]["kind"] == "quote" and direct[0]["kids"][0]["kids"][0]["kind"] == "turn"
              and rows_[0]["cells"][3] == {"kind": "pass", "dashed": False} and rows_[0]["cells"][4]["kind"] == "get")
        pn_row = {"items": g2["Juno"]["items"], "quote": None}
        with_note = gets_print.tree(pn_row, recs.get("Juno") or {}, True, False)
        flat_pn = gets_print.flatten({"label": "G"}, with_note)
        check("78: a participant note stands in its block marked Not from the transcript, its line dashed, and only when asked for",
              [n["kind"] for n in with_note] == ["pn"] and gets_print.tree(pn_row, {}, False, False) == []
              and flat_pn[0]["cells"][2]["dashed"] and flat_pn[0]["cells"][3]["dashed"]
              and "Not from the transcript" in gets_print.cell_html(flat_pn[0]["cells"][2], 2, None)
              and gets_mod.NOT_FROM == "Not from the transcript")
        many = gets_print.flatten({"label": "G"}, nodes)
        span = lambda n: sum(span(k) for k in n["kids"]) if n.get("kids") else 1
        first_span = span(nodes[0])
        drawn = gets_print.rows_html(many, None)
        check("78: the lines are drawn from each row, an upright piece down from a first child, full between and up to a last",
              [r["spines"].get(4) for r in many[:first_span + 1]] == ["down"] + ["full"] * (first_span - 1) + ["up"]
              and all(4 not in r["spines"] for r in many[first_span + 1:]) and len(many) == first_span + span(nodes[1])
              and re.search(r'<div class="tr-c c4[^"]*"><span class="tr-title">G</span><i class="tr-sp b4 down"></i></div>', drawn)
              and drawn.count('<i class="tr-sp b4 ') == first_span + 1,
              drawn[:300])
        parts = gets_print.around("I went out at six. The stair was cold, every single morning. Then the park.", '"the stair was cold"')
        check("78: a turn shows the sentence round its quote, the quote in bold, and its opening words when the quote is not there",
              parts == [("… ", False), ("The stair was cold", True), (", every single morning.", False), (" …", False)]
              and gets_print.around("No match here at all.", '"elsewhere"') == [("No match here at all.", False)]
              and [p for p in gets_print.around("one two three four", '"one two … four"') if p[1]] == [("one two", True), ("four", True)])
        trail = idiograph_routes.api_gets_trail({"workbook": any_book, "get": "G1"})
        # each block's head carries the case's badge before the name since 16 October (157)
        juno_block = trail["html"].split('aria-hidden="true">J</span>Juno', 1)[1].split("</article>", 1)[0]
        check("78: the trail of a GET is a block per participant, five columns, the turn's words read from the workbook with the quote in bold",
              trail["html"].count('<article class="tr-block">') == 3 and trail["label"] == "Days given a shape"
              and trail["count"] == 3 and trail["total"] == 3 and not trail["under"]
              and '<div class="tr-cols" aria-hidden="true"><span>Transcript passage</span><span>Quote</span><span>Statement</span><span>PET</span><span>GET</span></div>' in trail["html"]
              and "<b>Five years of it never getting said</b>" in juno_block)
        check("78: a turn of a case with a recording carries its address, and one of a case without carries none",
              'data-audio="/audio?' in juno_block and "sheet=Initial" in juno_block
              and "data-audio" not in trail["html"].split('aria-hidden="true">R</span>Rowan', 1)[1]
              and "gtTrailPlay(turn)" in js and "player.currentTime = Number(turn.dataset.at) || 0;" in fn(js, "gtTrailPlay"))
        g2_trail = idiograph_routes.api_gets_trail({"workbook": any_book, "get": "G2"})
        nothing_lines = [g2_trail["html"].count(f'<p class="tr-none">{w}</p>') for w in (gets_mod.NOTHING, gets_mod.NOTHING_NO_PETS)]
        check("78, updated 17 October: on the screen the trail carries his participant notes, and a case with nothing "
              "there says so in one line, a case with no PETs in its own line with no mark beside its name",
              "Invented: she trained dogs once." in g2_trail["html"] and g2_trail["under"] and g2_trail["minimum"] == 3
              and sum(nothing_lines) == 2 and (nothing_lines[1] == 0 or gets_mod.NO_PETS not in g2_trail["html"]),
              str(nothing_lines))
        check("78: a GET not on the board has no trail",
              "no longer on the board" in refused(lambda: idiograph_routes.api_gets_trail({"workbook": any_book, "get": "G7"})))

        # ── C. the print view, for each what, Full and Selected, participant notes only when ticked
        pages = {}
        for what in ("table", "trail", "all"):
            for detail in ("full", "selected"):
                pages[(what, detail)] = idiograph_routes.gets_print_page({"root": str(root), "what": what, "detail": detail, "auto": "0"})
        noted = {what: idiograph_routes.gets_print_page({"root": str(root), "what": what, "notes": "1", "auto": "0"})[1]
                 for what in ("table", "trail", "all")}
        check("78: the print route answers for each what, Full and Selected, as a landscape A4 page",
              all(code == 200 and "@page { size: A4 landscape; margin: 14mm }" in html_ and "const AUTO = false;" in html_
                  for code, html_ in pages.values())
              and "GET table" in pages[("table", "full")][1].split("</header>", 1)[0]
              and "Audit trail" in pages[("trail", "full")][1].split("</header>", 1)[0]
              and "Group experiential themes" in pages[("all", "full")][1].split("</header>", 1)[0])
        head = pages[("table", "full")][1].split('<header class="head">', 1)[1].split("</header>", 1)[0]
        check("78: each header is the table of PETs' own, the document's name as its title and the project beside it, "
              "the board in the foot, a participant with no PETs yet named under it, and no minimum and no line of what each row "
              "shows (Adam, 1 November)",
              "<h1>Table of Group Experiential Themes</h1>" in head and "Living with a dog" in head
              and "Living with a dog (Board 1)" in pages[("table", "full")][1]
              and '<p class="date">' not in head
              and "Minimum" not in head and "No PETs yet: Juno" in head and "Every item" not in head
              and all('<header class="head">' in h for _c, h in pages.values()))
        full, selected = pages[("table", "full")][1], pages[("table", "selected")][1]
        check("78: Full sets out every item, Selected the key quote alone",
              "<th>Under this GET</th>" in full and "<th>Under this GET</th>" not in selected
              and '<span class="kind">PET</span>' in full and '<span class="kind">PET</span>' not in selected

              and selected.count('<td class="kqcell"><i>') == full.count('<td class="kqcell"><i>') > 0)
        check("78: participant notes appear in no export unless Include participant notes is ticked",
              all("Invented: she trained dogs once." not in h for _c, h in pages.values())
              and all("Invented: she trained dogs once." in h for h in noted.values()))
        everything = pages[("all", "full")][1]
        check("78: the full set opens on a contents page, then each case's PET table, the GET table and the trail",
              everything.index('<section class="contents">') < everything.index('id="pets"') < everything.index('id="table"')
              < everything.index('id="trail"') and everything.count('<section class="case">') == 3
              and 'id="pets-Rowan"' in everything and "Living on her timetable, in the dark at both ends" in everything)
        one = idiograph_routes.gets_print_page({"root": str(root), "what": "trail", "get": "G2", "auto": "0"})[1]
        check("78: from a GET's trail it prints that GET alone",
              one.count('<section class="tr-get') == 1 and 'id="trail-G2"' in one)
        outside = idiograph_routes.gets_print_page({"root": str(scratch), "auto": "0"})
        gone = idiograph_routes.gets_print_page({"root": str(root), "board": "b9", "auto": "0"})
        check("78: a folder that is not the case root, and a board the file does not hold, are refused as a page of one line",
              outside[0] == 403 and gone[0] == 409 and "nothing was printed" in gone[1])
        check("78: the print view, the trail and the table write nothing, no workbook, themes file or GETs file touched",
              snapshot_tree() == tree_before and workbook_sha() == before_sha
              and "load_workbook(workbook, read_only=True" in print_src and ".save(" not in print_src
              and "gets_mod.write" not in print_src and "write(" not in print_src.replace("write_text", ""))
        check("78: the print route sits beside the PETs one, the trail's route is in the table, and the Mac app carries the module",
              idiograph_routes.GETS_PRINT_PATH == "/gets/print"
              and server_mod.GET_PATHS.get(idiograph_routes.GETS_PRINT_PATH) is idiograph_routes.gets_print_view
              and server_mod.ROUTES.get("/api/gets-trail") is idiograph_routes.api_gets_trail
              and '"gets", "gets_print"' in support.source("packaging/build_mac.py").read_text(encoding="utf-8"))
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = saved

    # ── D. the page: the tick, the trail's card, the print card, the split
    check("78: a tick in the Inspector changes the row's key quote, a second tick takes it off, each one step of undo",
          "gtTickHtml(v, item.id, parents)" in fn(js, "gtPanelDraw") and "quote: stored === qkey ? '' : qkey" in fn(js, "gtTick")
          and "thDone(before," in fn(js, "gtTick") and "const before = thSnap(v, TH.removed);" in fn(js, "gtTick")
          and "data-gtick=" in fn(js, "gtTickHtml"))
    check("78: the rows ride in the undo snapshots and go with the board on a save, on the GETs screen alone",
          "rows: v.rows ? JSON.parse(JSON.stringify(v.rows)) : null," in fn(js, "thSnap")
          and "if (snap.rows) v.rows = JSON.parse(JSON.stringify(snap.rows));" in fn(js, "thPut")
          and "if (TH.mode === 'gets' && v.rows) out.rows = gtRowsKept(v);" in fn(js, "thBody"))
    check("78: the trail's card and the print card keep their own keys, and the canvas hears none while they are open",
          "if (gtKeys(e)) return;" in fn(js, "thKeyDown") and fn(js, "thKeyDown").index("gtKeys(e)") < fn(js, "thKeyDown").index("anyOverlayOpen()")
          and '<div class="overlay" id="gt-trail" hidden>' in page and '<div class="overlay" id="gt-print" hidden>' in page)
    card = page.split('<div class="overlay" id="gt-print" hidden>', 1)[1].split('\n</div>', 1)[0]
    check("78: the print card offers the table, the trail or the full set, Full or Selected, and Include participant notes unticked",
          all(f'data-what="{w}"' in card for w in ("table", "trail", "all")) and 'data-detail="full"' in card and 'data-detail="selected"' in card
          and '<input type="checkbox" id="gt-print-notes"> Include participant notes' in card
          and "$('gt-print-notes').checked = false;" in fn(js, "gtPrintOpen")
          and "if (notes) q.notes = '1';" in fn(js, "gtPrintUrl"))
    beside = fn(js, "gtBesideOpen")
    check("78: Open beside this one reads the other board through the PETs screen's open, read-only, and writes nothing",
          "await api('/api/themes', c.board ? { workbook: c.path, board: c.board, beside: true } : { workbook: c.path, beside: true });" in beside
          and "readonly: true" in beside
          and all(w not in fn(js, n) for n in ("gtBesideOpen", "gtBesideRender", "gtBesideShut", "gtBesidePan", "gtBesideWheel", "gtBesideFit")
                  for w in ("thSoon", "thDone", "thSave", "-save'", "gets-ops", "themes-versions")))

    node = shutil.which("node")
    if not node:
        skip("78: the table, the rows and the switcher in node", "no node on this machine")
    else:
        data = json.loads(gfile.read_text(encoding="utf-8"))
        python_rows = {g["id"]: {r["case"]: [r["counted"], (r["quote"] or {}).get("key"), r["chosen"], sorted(i["kind"] for i in r["items"])]
                                 for r in g["rows"]} for g in gets_mod.table(data, data["boards"][0], ["Rowan", "Mabel", "Juno"])}
        server_mod.ROOT_OVERRIDE = str(root)
        server_mod.STATE_MEMORY = {"recent": []}
        try:
            answer = idiograph_routes.api_gets({"workbook": any_book})
        finally:
            server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = saved
        app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js").splitlines()
        helpers = "\n".join(next(line for line in app if line.startswith(start)) for start in ("const esc = ", "const escAttr = "))
        script = scratch / "gets-table-model.js"
        script.write_text(support.i18n_js() + helpers + "\n" + js + "\nconst ANSWER = " + json.dumps(answer) + r""";
TH.mode = 'gets';
TH.layout = {};
TH.gets = { cases: ANSWER.cases, minimum: ANSWER.minimum, total: ANSWER.total, settings: ANSWER.settings };
const cards = {};
for (const c of ANSWER.cards) cards[c.key] = Object.assign({}, c);
const v = { cards, groups: ANSWER.groups.map((g) => Object.assign({}, g, { members: g.members.slice() })), discarded: ANSWER.discarded.slice(),
  picks: {}, stickies: [], rows: JSON.parse(JSON.stringify(ANSWER.rows)) };
const out = {};
out.table = Object.fromEntries(gtTable(v).map((g) => [g.id, Object.fromEntries(g.rows.map((r) => [r.kase,
  [r.counted, r.quote ? r.quote.key : null, r.chosen, r.items.map((i) => i.kind).sort()]]))]));
out.order = gtTable(v).map((g) => g.id);
const snap = thSnap(v, new Set());
gtRowSet(v, 'G2', 'Rowan', { note: 'Invented.' });
out.set = JSON.parse(JSON.stringify(v.rows.G2));
thPut(v, snap);
out.put = v.rows.G2 === undefined;
gtRowSet(v, 'G1', 'Mabel', { quote: '', note: '' });
out.cleared = v.rows.G1 === undefined || v.rows.G1.Mabel === undefined;
v.rows.G8 = { Rowan: { quote: 'Initial:9:0', note: '' } };
out.kept = gtRowsKept(v);
TH.mode = 'pets';
out.petsBody = 'rows' in thBody(v, { id: 'b1', name: 'Board 1' });
TH.mode = 'gets';
out.getsBody = thBody(v, { id: 'b1', name: 'Board 1' }).rows;
out.tabs = [thTabOf('table', 'gets'), thTabOf('guidance', 'gets'), thTabOf('history', 'gets')];
const els = {};
global.$ = (id) => els[id] || (els[id] = { innerHTML: '', style: {}, offsetWidth: 300, getBoundingClientRect: () => ({ left: 100, bottom: 46 }) });
global.window = { innerWidth: 1200 };
thCasemenuDraw([{ path: 'a', case: 'Juno', board_name: 'Board 1', chosen: false, current: true, table: '/t?a' },
  { path: 'b', case: 'Rowan', board_name: 'Board 1', chosen: true, current: false, table: '/t?b' },
  { path: 'c', case: 'Mabel', board_name: 'Board 1', chosen: true, current: false, table: '/t?c' }]);
out.switcher = $('th-casemenu').innerHTML;
console.log(JSON.stringify(out));
""", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0 or not run.stdout.strip():
            check("78: the table and the rows run in node", False, run.stderr.strip()[:400])
        else:
            o = json.loads(run.stdout.strip().splitlines()[-1])
            check("78: in node, the page's table matches the server's, row for row, the counts, the key quotes and the ticks",
                  o["table"] == python_rows and o["order"] == ["G1", "G2"], str(o["table"])[:400])
            check("78: in node, a row's note is set, undo puts the rows back, and a row left empty goes",
                  o["set"] == {"Rowan": {"quote": "", "note": "Invented."}} and o["put"] and o["cleared"])
            check("78: in node, a save sends the rows on the GETs screen alone, a GET gone from the board and an empty row left out",
                  not o["petsBody"] and "G8" not in o["getsBody"] and "G8" not in o["kept"] and o["tabs"] == ["inspector", "guidance", "history"])
            check("78: in node, the switcher offers Open beside this one on the other cases and never on this one",
                  o["switcher"].count(">Open beside this one</button>") == 2 and 'data-beside="0"' not in o["switcher"]
                  and 'data-beside="1"' in o["switcher"] and o["switcher"].count(">Open as table</button>") == 3)
