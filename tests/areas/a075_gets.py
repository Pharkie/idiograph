from __future__ import annotations

import inspect
import json
import os
import shutil
from pathlib import Path

import openpyxl

import workbook as wb_mod
from workbook import WorkbookError

from . import support
from .support import DEMO_SHEET, check, copied_second_sheet, demo_copy, skip
import idiograph_routes


def test_gets(scratch):
    print("\n75. GETs: the file, what comes in, the canvas and the Cases panel, the count and the minimum, "
          "One GET per PET, Take the changes and Mark GETs complete")
    import hashlib
    import subprocess
    import time
    import gets as gets_mod
    import server as server_mod
    import themes as themes_mod

    page = support.page_text()
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    js = support.text("apps/idiograph/static/themes.js")
    gets_src = support.source("apps/idiograph/gets.py").read_text(encoding="utf-8")
    fn = lambda text, name: text.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in text else ""

    def refused(call):
        try:
            call()
        except WorkbookError as exc:
            return str(exc)
        return ""

    # ── the fixture: four invented cases built from the demo, none a real transcript
    root = scratch / "gets-root"
    shutil.rmtree(root, ignore_errors=True)
    books = {name: demo_copy(root, name, f"{name} - EN & ES.xlsx") for name in ("Wren", "Ash", "Moss", "Fern")}
    # Ash pools two sheets, and one row of Wren carries a key quote and an exploratory note
    copied_second_sheet(books["Ash"], "Follow-up", blank=False)
    read = themes_mod.read_cards(books["Wren"])
    keys = [c["key"] for c in read["cards"]]
    quoted_row = (read["cards"][0]["sheet"], read["cards"][0]["row"])
    book = openpyxl.load_workbook(books["Wren"], rich_text=True)
    ws = book[quoted_row[0]]
    cols = wb_mod.detect_columns(ws)
    ws.cell(quoted_row[1], cols["kq"]).value = '"the stair at six, every morning"'
    ws.cell(quoted_row[1], cols["en"]).value = "Presence felt before it is seen, an invented note."
    book.save(books["Wren"])
    book.close()
    workbook_sha = lambda: {n: hashlib.sha256(p.read_bytes()).hexdigest() for n, p in books.items()}

    def board(vid, name, groups, discarded=()):
        b = themes_mod.blank_version(themes_mod.read_cards(books["Wren"])["cards"])
        b.update(id=vid, name=name, groups=groups, discarded=list(discarded))
        return b

    def themes_file(name, boards, current, chosen=None, complete=None):
        data = {"schema": 2, "case": name, "workbook": books[name].name, "current": current, "boards": boards}
        if chosen:
            data["chosen"] = chosen
        if complete:
            data["complete"] = complete
        themes_mod.write(books[name], data)

    pets = [{"id": "g1", "label": "Mornings", "members": keys[0:2] + ["g3"], "x": 0, "y": 0},
            {"id": "g2", "label": "Walks", "members": keys[4:6], "x": 0, "y": 0},
            {"id": "g3", "label": "Early light", "members": keys[2:4], "x": 0, "y": 0}]
    # Wren: marked complete on Board 2, the board last open being Board 1
    themes_file("Wren", [board("v1", "Board 1", []), board("v2", "Board 2", pets, [keys[9]])], "v1", "v2",
                {"at": "2026-10-05T10:00:00+01:00", "board": "v2", "name": "Board 2"})
    # Ash: a Current board, not complete
    themes_file("Ash", [board("v1", "Board 1", [dict(p) for p in pets[:2]]), board("v2", "Board 2", [])], "v2", "v1")
    # Moss: no Current board, so the board last open
    themes_file("Moss", [board("v1", "Board 1", []), board("v2", "Board 2", [{"id": "g1", "label": "Company", "members": keys[6:8], "x": 0, "y": 0}])], "v2")
    # every file older than the time the cases come in, so the fast path can be seen
    old = time.time() - 30
    for p in list(books.values()) + [themes_mod.themes_path(b) for b in books.values() if themes_mod.themes_path(b).exists()]:
        os.utime(p, (old, old))
    before_sha = workbook_sha()
    saved = (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_MEMORY = {"recent": []}
    any_book = str(books["Wren"])
    gfile = gets_mod.gets_path(root)

    def snapshot_tree():
        return {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in sorted(root.rglob("*")) if p.is_file()}

    try:
        # ── A. what comes in, and opening writes nothing
        tree = snapshot_tree()
        shown = idiograph_routes.api_gets({"workbook": any_book})
        check("75: opening writes nothing, no GETs file and no other file touched",
              snapshot_tree() == tree and not gfile.exists() and shown["saved"] is False)
        cases = {c["case"]: c for c in shown["cases"]}
        check("75: the study is every case folder with an annotated workbook, by its pseudonym, in case order, each not yet in shown as it would come in",
              [c["case"] for c in shown["cases"]] == ["Ash", "Fern", "Moss", "Wren"] and all(c["status"] == "pending" for c in shown["cases"]))
        check("75: a case with PETs marked complete comes from the board the mark names",
              cases["Wren"]["complete"] and cases["Wren"]["board_name"] == "Board 2" and len(cases["Wren"]["pets"]) == 3)
        check("75: any other from its Current board, else the board last open",
              not cases["Ash"]["complete"] and cases["Ash"]["board_name"] == "Board 1"
              and not cases["Moss"]["complete"] and cases["Moss"]["board_name"] == "Board 2")
        check("75: a case with no themes file reads No PETs yet", cases["Fern"]["none"] and cases["Fern"]["pets"] == []
              and gets_mod.NO_PETS == "No PETs yet" and "const GT_NO_PETS = t('themes.gets.no_pets');" in js)
        cards = {c["key"]: c for c in shown["cards"]}
        check("75, 193: each case's PETs and sub-themes land in the pile as cards, a sub-theme a card of its own",
              set(cards) == {"Wren/g1", "Wren/g2", "Wren/g3", "Ash/g1", "Ash/g2", "Moss/g1"}
              and cards["Wren/g3"]["kind"] == "sub"
              and all(c["kind"] == "pet" for k, c in cards.items() if k != "Wren/g3"))
        check("75: a case whose PETs are not complete has its cards marked, PETs not complete",
              cards["Ash/g1"]["open"] and cards["Moss/g1"]["open"] and not cards["Wren/g1"]["open"]
              and "const GT_NOT_COMPLETE = t('themes.gets.not_complete');" in js)
        wren = cases["Wren"]
        sub = next(p for p in wren["pets"] if p["id"] == "g3")
        check("75: the copy holds each PET and sub-theme with its title, note, parent, sub-themes, statements and picks",
              set(sub) == {"id", "title", "note", "parent", "subs", "statements", "picks"} and sub["parent"] == "g1"
              and next(p for p in wren["pets"] if p["id"] == "g1")["subs"] == ["g3"])
        lines = wren["lines"]
        first = lines[keys[0]]
        check("75: every statement of the case is in lines, placed, unplaced or discarded, with sheet, timecode and words",
              len(lines) == len(keys) and lines[keys[9]]["discarded"] and lines[keys[0]]["pet"] == "g1"
              and lines[keys[12]]["pet"] is None and not lines[keys[12]]["discarded"]
              and {"sheet", "time", "text", "quotes", "notes"} <= set(first))
        check("75: a statement carries its row's key quotes and exploratory notes inside it",
              first["quotes"] == ['"the stair at six, every morning"']
              and first["notes"] == ["Presence felt before it is seen, an invented note."])
        sheets = {line["sheet"] for line in cases["Ash"]["lines"].values()}
        check("75: every sheet is pooled, the sheet named on each line",
              sheets == {DEMO_SHEET, "Follow-up"} and any(k.startswith("Follow-up:") for k in cases["Ash"]["lines"]))
        check("75: the count and the minimum come with the screen, Smith's band for four cases",
              shown["total"] == 4 and shown["minimum"] == 3 and shown["band"] is True)

        # ── B. the first act takes every case in
        body = dict(shown["version"], cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in shown["cards"]},
                    groups=[{"id": "G1", "label": "Starting the day", "members": ["Wren/g1", "Ash/g1"], "x": 0, "y": -60}],
                    discarded=[], picks={}, notes=[])
        idiograph_routes.api_gets_save({"workbook": any_book, "version": body})
        data = json.loads(gfile.read_text(encoding="utf-8"))
        check("75: the first act on the screen writes the file and takes every case in",
              set(data["cases"]) == {"Wren", "Ash", "Moss", "Fern"} and set(data["study"]) == set(data["cases"])
              and all(v == {"in": True} for v in data["study"].values()))
        check("75: the file is idiograph-gets.json at the case root, in the brief's shape and order",
              gfile.parent == root and gfile.name == "idiograph-gets.json"
              and list(data)[:4] == ["schema", "created", "updated", "current"] and data["schema"] == 1
              and list(data).index("complete") < list(data).index("settings") < list(data).index("study")
              < list(data).index("cases") < list(data).index("boards") and data["complete"] is None
              and data["settings"] == {"minimum": None, "one_per_pet": True})
        rec = data["cases"]["Wren"]
        check("75: a case in the file carries its workbook, board, name, complete, came, seen, hash, state, pets and lines",
              set(rec) == {"workbook", "board", "name", "complete", "came", "seen", "hash", "state", "pets", "lines"}
              and rec["workbook"] == books["Wren"].name and rec["board"] == "v2" and rec["state"] == "in"
              and data["cases"]["Fern"]["state"] == "none" and rec["came"][:2] == "20")
        snap = gets_mod.snapshot(books["Wren"])
        check("75: hash is the copy's hash as themes.state_hash makes one",
              rec["hash"] == themes_mod.state_hash({k: snap[k] for k in gets_mod.SNAP_KEYS}) == gets_mod.snap_hash(snap))
        b1 = data["boards"][0]
        check("75: a board keeps its cards by case and kind, a PET's card with no words while its case has it",
              b1["id"] == "b1" and b1["groups"][0]["members"] == ["Wren/g1", "Ash/g1"]
              and "text" not in b1["cards"]["Wren/g1"] and b1["rows"] == {} and data["current"] == "b1")
        check("75: the file is written to a temporary file and moved over the old one, and none is left",
              "os.replace(tmp, path)" in inspect.getsource(gets_mod.write) and ".tmp" in inspect.getsource(gets_mod.write)
              and not list(root.glob("*.tmp")))

        # ── C. the unchanged fast path, and the hash
        calls = []
        real = gets_mod.snapshot
        gets_mod.snapshot = lambda wb: calls.append(Path(wb).parent.name) or real(wb)
        try:
            again = idiograph_routes.api_gets({"workbook": any_book})
        finally:
            gets_mod.snapshot = real
        check("75: a case whose workbook and themes file are older than its came is unchanged without a read",
              calls == [] and all(c["status"] == "in" for c in again["cases"]))
        os.utime(books["Moss"], None)
        calls.clear()
        gets_mod.snapshot = lambda wb: calls.append(Path(wb).parent.name) or real(wb)
        try:
            touched = idiograph_routes.api_gets({"workbook": any_book})
        finally:
            gets_mod.snapshot = real
        check("75: any other is read again and compared, and the same copy reads as unchanged",
              calls == ["Moss"] and {c["case"]: c["status"] for c in touched["cases"]}["Moss"] == "in")

        # ── D. Changed since it came in, and Take the changes
        idiograph_routes.api_gets_ops({"workbook": any_book, "op": "new"})
        ash = themes_mod.load(books["Ash"])
        groups = ash["boards"][0]["groups"]
        groups[0]["label"] = "Mornings, early"                       # g1 retitled, its place by id
        walks = next(g for g in groups if g["id"] == "g2")
        walks["id"] = "g7"                                            # Walks again, under a new id: its place by title
        groups.append({"id": "g8", "label": "Losing her", "members": keys[10:12], "x": 0, "y": 0})   # a new PET
        themes_mod.write(books["Ash"], ash)
        changed = idiograph_routes.api_gets({"workbook": any_book, "board": "b1"})
        entry = {c["case"]: c for c in changed["cases"]}["Ash"]
        check("75: a difference marks the case Changed since it came in, and says what changed",
              entry["status"] == "changed" and entry["changes"]["added"] == ["Losing her"]
              and entry["changes"]["retitled"] == [["Mornings", "Mornings, early"]] and entry["changes"]["gone"] == []
              and any(m["to"] == "Losing her" for m in entry["changes"]["moved"]) and gets_mod.CHANGED == "Changed since it came in")
        check("75: the copy stands until Take the changes",
              {c["key"]: c["text"] for c in changed["cards"]}["Ash/g1"] == "Mornings" and "Ash/g8" not in {c["key"] for c in changed["cards"]})
        # a PET gone from the case: Moss's Company goes
        moss = themes_mod.load(books["Moss"])
        moss["boards"][1]["groups"] = []
        themes_mod.write(books["Moss"], moss)
        took = idiograph_routes.api_gets_cases({"workbook": any_book, "op": "take", "case": "Ash"})
        data = json.loads(gfile.read_text(encoding="utf-8"))
        b1, b2 = data["boards"][0], data["boards"][1]
        check("75: Take keeps a revision of each GET board first",
              all(b["history"][-1]["name"] == "Before Ash's changes came in" for b in (b1, b2)))
        check("75: each PET keeps its place by id, then by title, and new PETs come in unplaced",
              b1["groups"][0]["members"] == ["Wren/g1", "Ash/g1"] and "Ash/g7" in b1["cards"] and "Ash/g2" not in b1["cards"]
              and "Ash/g8" in b1["cards"] and not any("Ash/g8" in g["members"] for g in b1["groups"])
              and "Ash/g8" in b2["cards"] and took["op"] == "take")
        shown_cards = {c["key"]: c for c in took["cards"]}
        check("75: after Take the cards read the new copy, and the case is in again",
              shown_cards["Ash/g1"]["text"] == "Mornings, early" and shown_cards["Ash/g7"]["text"] == "Walks"
              and {c["case"]: c["status"] for c in took["cases"]}["Ash"] == "in")
        check("75: Take on a case that has not changed is refused, and nothing is written",
              "Nothing has changed" in refused(lambda: idiograph_routes.api_gets_cases({"workbook": any_book, "op": "take", "case": "Ash"})))
        # 196: a PET's card on a GETs board keeps no words, so the layout takes its title from its
        # case's copy, and new cards land clear of a long title's card, never on its lower lines
        long = "Reading every bee guide, yet the swarm overhead is still a hugely loud shock every summer"
        held = {"cases": {"Fen": {"pets": [{"id": "g1", "title": long, "parent": None}], "lines": {}}}}
        # Fen's card sits over the middle, a one-line card's height and the margin above where the pile goes
        lone = {"cards": {"Fen/g1": {"x": -100, "y": -247}}, "groups": [], "discarded": [], "picks": {}}
        bare = {"cards": {"Fen/g1": {"x": -100, "y": -247, "text": ""}}, "groups": [], "discarded": [], "picks": {}}
        comers = [("Gale/g%d" % n, "A personal failure to be sick") for n in range(1, 6)]
        gets_mod.lay_in(lone, comers, held)
        tall = gets_mod.card_height("Fen/g1", long)
        def apart(a, b, gap):
            return (a[0] + a[2] + gap <= b[0] or b[0] + b[2] + gap <= a[0]
                    or a[1] + a[3] + gap <= b[1] or b[1] + b[3] + gap <= a[1])
        fen = (-100, -247, themes_mod.CARD_W, tall)
        landed = [(c["x"], c["y"], themes_mod.CARD_W, gets_mod.card_height(k, t)) for (k, t), c in
                  ((e, lone["cards"][e[0]]) for e in comers)]
        blind = themes_mod.place_new([k for k, _ in comers], dict(comers), bare, gets_mod.card_height)
        check("196: cards taken in land the margin clear of a PET's card as tall as its title, where a blank title fell short",
              tall > gets_mod.card_height("Fen/g1", "") and all(apart(fen, b, themes_mod.MARGIN) for b in landed)
              and not all(apart(fen, (blind[k]["x"], blind[k]["y"], themes_mod.CARD_W, gets_mod.card_height(k, t)), themes_mod.MARGIN)
                          for k, t in comers),
              str(landed))
        idiograph_routes.api_gets_cases({"workbook": any_book, "op": "take", "case": "Moss"})
        data = json.loads(gfile.read_text(encoding="utf-8"))
        gone = {c["key"]: c for c in idiograph_routes.api_gets({"workbook": any_book, "board": "b1"})["cards"]}["Moss/g1"]
        check("75: a PET gone from its case stays where it is, its title kept, marked No longer in its PETs, never moved or binned",
              gone["gone"] and gone["text"] == "Company" and data["boards"][0]["cards"]["Moss/g1"]["text"] == "Company"
              and "Moss/g1" not in data["boards"][0]["discarded"]
              and "t('themes.gets.gone', { who: c.who })" in fn(js, "gtMarks"))
        moss = themes_mod.load(books["Moss"])
        moss["chosen"] = "v2"
        moss["complete"] = {"at": "2026-10-05T11:00:00+01:00", "board": "v2", "name": "Board 2"}
        themes_mod.write(books["Moss"], moss)
        marked = {c["case"]: c for c in idiograph_routes.api_gets({"workbook": any_book})["cases"]}["Moss"]
        check("75: a case marked complete since it came in offers its marked board the same way",
              marked["status"] == "changed" and marked["changes"]["marked"] and not marked["complete"])

        # ── E. the count, with sub-themes and statements, never a participant note
        countable = {"cards": {"Wren/g1": {}, "Ash/g3": {}, "Moss/es/Initial:3:0": {}, "Fern/pn/1": {}, "Ash/g1/2": {}},
                     "groups": [{"id": "G1", "label": "A", "members": ["Wren/g1", "G2", "Fern/pn/1"]},
                                {"id": "G2", "label": "B", "members": ["Ash/g3", "Moss/es/Initial:3:0", "Ash/g1/2"]}],
                     "discarded": []}
        inside = {"Wren", "Ash", "Moss", "Fern"}
        check("75: a GET counts the cases with a PET, sub-theme or statement anywhere under it, sub-themes included",
              gets_mod.count(countable, "G1", inside) == 3 and gets_mod.count(countable, "G2", inside) == 2)
        check("75: a participant note never counts, a second card counts its case once, and a case out of the study is left out",
              gets_mod.count(dict(countable, groups=[{"id": "G1", "label": "A", "members": ["Fern/pn/1"]}]), "G1", inside) == 0
              and gets_mod.count(countable, "G1", inside - {"Moss"}) == 2)

        # ── F. Smith's band and the minimum
        check("75: the band is every participant for three or fewer, three for four to eight, half rounded up beyond",
              [gets_mod.band(n) for n in (3, 6, 8, 10, 11)] == [3, 3, 3, 5, 6] and gets_mod.band(2) == 2)
        check("75: the minimum is the band while he has not changed it, and his number once he has",
              gets_mod.minimum_of({"minimum": None}, 10) == (5, True) and gets_mod.minimum_of({"minimum": 4}, 10) == (4, False))

        # ── G. Settings: the study, the switch and the minimum, in the GETs file
        view = idiograph_routes.api_gets_settings({"workbook": any_book})
        check("75: Settings reads the study, the switch and the band from the file, writing nothing",
              view["settings"] == {"minimum": None, "one_per_pet": True} and view["smith"] == 3
              and [s["case"] for s in view["study"]] == ["Ash", "Fern", "Moss", "Wren"])
        check("75: a case taken out of the study asks one line of reason",
              "Say in a line why Fern" in refused(lambda: idiograph_routes.api_gets_settings(
                  {"workbook": any_book, "op": "save", "study": {"Fern": {"in": False}}})))
        out = idiograph_routes.api_gets_settings({"workbook": any_book, "op": "save", "study": {"Fern": {"in": False, "reason": "a pilot"}},
                                            "one_per_pet": False, "minimum": 2})
        data = json.loads(gfile.read_text(encoding="utf-8"))
        check("75: saved, the case is out with its reason, the switch off and the minimum his",
              data["study"]["Fern"] == {"in": False, "reason": "a pilot"} and data["settings"] == {"minimum": 2, "one_per_pet": False}
              and out["total"] == 3 and out["minimum"] == 2 and out["band"] is False)

        # ── H. One GET per PET, on and off
        doubled = dict(idiograph_routes.api_gets({"workbook": any_book, "board": "b2"})["version"],
                       cards={"Wren/g1": {"x": 0, "y": 0}, "Wren/g1/2": {"x": 300, "y": 0}},
                       groups=[{"id": "G1", "label": "One", "members": ["Wren/g1"], "x": 0, "y": -40},
                               {"id": "G2", "label": "Two", "members": ["Wren/g1", "Wren/g1/2"], "x": 300, "y": -40}],
                       discarded=[], picks={}, notes=[])
        idiograph_routes.api_gets_save({"workbook": any_book, "version": doubled})
        held = json.loads(gfile.read_text(encoding="utf-8"))["boards"][1]
        check("75: a card sits under one GET at most, and a second card of a PET under another keeps its place",
              [g["members"] for g in held["groups"]] == [["Wren/g1"], ["Wren/g1/2"]]
              and set(held["cards"]) >= {"Wren/g1", "Wren/g1/2"})

        # ── I. Mark GETs complete
        why = refused(lambda: idiograph_routes.api_gets_ops({"workbook": any_book, "op": "complete"}))
        check("75: Mark GETs complete is refused, saying which cases, while one is not in from its marked board unchanged",
              why.startswith("GETs were not marked complete. Waiting on ") and "Ash (PETs not complete)" in why
              and "Moss (changed since it came in)" in why and "Fern" not in why
              and json.loads(gfile.read_text(encoding="utf-8"))["complete"] is None)
        ash = themes_mod.load(books["Ash"])
        ash["complete"] = {"at": "2026-10-05T12:00:00+01:00", "board": "v1", "name": "Board 1"}
        themes_mod.write(books["Ash"], ash)
        idiograph_routes.api_gets_cases({"workbook": any_book, "op": "take", "case": "Ash"})
        idiograph_routes.api_gets_cases({"workbook": any_book, "op": "take", "case": "Moss"})
        done = idiograph_routes.api_gets_ops({"workbook": any_book, "op": "complete"})
        data = json.loads(gfile.read_text(encoding="utf-8"))
        check("75: with every case in from its marked board and unchanged, and nothing more, it is marked",
              done["complete"] and set(data["complete"]) == {"at", "board", "name"} and data["complete"]["board"] == data["current"])
        reopened = idiograph_routes.api_gets_ops({"workbook": any_book, "op": "reopen"})
        check("75: Reopen GETs takes the mark off", reopened["complete"] is None
              and json.loads(gfile.read_text(encoding="utf-8"))["complete"] is None)
        check("75: the menu's foot reads Mark GETs complete or Reopen GETs, and the mark fires the third level of confetti",
              "${esc(t('themes.gets.done_mark'))}</button>" in fn(js, "gtMenuFoot") and "${esc(t('themes.gets.reopen'))}</button>" in fn(js, "gtMenuFoot")
              and "confetti(3);" in fn(js, "gtDone") and "if (TH.mode === 'gets') { await gtDone(mark); return; }" in fn(js, "thPetsDone")
              and "if (TH.mode === 'gets') html += gtMenuFoot();" in fn(js, "thVmenuDraw"))

        # ── J. the head row, the routes and the guard
        listed = idiograph_routes.api_cases({})
        check("75: the GETs card over the cards carries the project's GETs, the cases of the study, those with PETs complete and those in",
              listed["gets"]["cases"] == 3 and listed["gets"]["complete"] == 3 and listed["gets"]["done"] is None
              and listed["gets"]["held"] == 3
              and Path(server_mod.abs_path(listed["gets"]["path"])).parent.name == "Ash")
        demo_head = idiograph_routes.api_gets_head({"workbook": server_mod.rel_path(server_mod.DEMO_WORKBOOK)})["gets"]
        check("75: the demo is a project of its own, and its card is drawn through the same function",
              demo_head["cases"] >= 1 and demo_head["name"] == idiograph_routes.read_project(server_mod.DEMO_DIR)["name"]
              and "drawGetsHead($('hp-gets'), demo.rows[0].path, () => S.home === demo.id);" in fn(app, "drawDemoPage")
              and "drawGetsCard(box, data.gets);" in fn(app, "drawGetsHead")
              and "drawGetsCard($('hp-gets'), s.gets);" in fn(app, "drawPage")
              and "'distil.gets.card_name'" in fn(app, "drawGetsCard") and "getsLine(gets)" in fn(app, "drawGetsCard"))
        check("75: the GETs routes are in the table, beside the themes routes they mirror",
              all(server_mod.ROUTES.get(r) is f for r, f in (("/api/gets", idiograph_routes.api_gets), ("/api/gets-head", idiograph_routes.api_gets_head),
                  ("/api/gets-save", idiograph_routes.api_gets_save), ("/api/gets-ops", idiograph_routes.api_gets_ops),
                  ("/api/gets-boards", idiograph_routes.api_gets_boards), ("/api/gets-cases", idiograph_routes.api_gets_cases),
                  ("/api/gets-settings", idiograph_routes.api_gets_settings))))
        outside = False
        try:
            idiograph_routes.api_gets({"workbook": str(scratch / "elsewhere.xlsx")})
        except server_mod.OutsideRoot:
            outside = True
        check("75: a workbook outside the case root is refused", outside)
        revised = idiograph_routes.api_gets_boards({"workbook": any_book, "op": "revision", "id": "b1", "name": "Looked at"})
        viewed = idiograph_routes.api_gets_boards({"workbook": any_book, "op": "view", "id": "b1", "revision": revised["history"][0]["id"]})
        check("75: a GETs board keeps its history, and a revision is viewed without writing",
              revised["history"][0]["name"] == "Looked at" and "cards" in viewed and viewed["op"] == "view")
        check("75: the GETs screen never writes a workbook or a themes file's boards",
              workbook_sha() == before_sha and "openpyxl" not in gets_src and "themes.write(" not in gets_src
              and "save_turn" not in gets_src)
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = saved

    # ── K. the page: the same canvas in a GETs mode, never a fork
    check("75: GETs is the PETs canvas run in a GETs mode, opened through getsOpen, its routes beside the PETs ones",
          "TH.mode = opts.gets ? 'gets' : 'pets';" in fn(js, "themesOpen") and "mode: 'pets'," in js
          and "TH.mode === 'gets' ? await api('/api/gets', asked) : await api('/api/themes', asked);" in fn(js, "themesOpen")
          and "TH.mode === 'gets' ? await api('/api/gets-save', body) : await api('/api/themes-save', body);" in fn(js, "thSaveOnce")
          and "const GT_ROUTES = { '/api/themes-versions': '/api/gets-ops', '/api/themes-boards': '/api/gets-boards' };" in js
          and not any((folder / "gets.js").exists() for folder in support.static_folders()))
    check("75: the Cases panel sits at the left, with one search, and its rows drag onto the canvas",
          'id="th-cpanel"' in page and page.index('id="th-cpanel"') < page.index('id="th-stage"')
          and 'id="gt-find"' in page and "gtPullDrop(p.card, e.clientX, e.clientY, p.lean);" in fn(js, "gtPullUp")
          and "t('themes.gets.add_pn')" in fn(js, "gtCaseMenu") and "Take the changes" not in fn(js, "gtCaseMenu"))
    check("75: a page in front of a server from before GETs says to restart, on the canvas, in the menu and in Settings",
          "thNote(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err));" in fn(js, "themesOpen")
          and "thVsaid(needsRestart(err) ? RESTART_LINE : err.message);" in fn(js, "thBoardOp")
          and "needsRestart(err)) { $('gets-restart').hidden = false;" in fn(app, "loadGetsPane")
          and '<p class="fineprint restart-line" id="gets-restart" hidden>Restart the server to finish this update.</p>' in page)
    # in Settings, a category of its own, from 20 October until settingsplit (5 November 2026), and in the project's own
    # Project settings since
    sheet = page.split('<div class="overlay" id="projset"', 1)[1].split('<div class="overlay"', 1)[0]
    check("75: Project settings carries GETs under a heading of its own: the switch, the minimum with Smith's band, and the study",
          '<h4 class="pane-sub" id="gets-sub">GETs</h4>' in sheet and 'id="pane-gets"' not in page and 'id="set-one-per-pet"' in sheet
          and "<span class=\"fineprint gets-band\" id=\"set-min-band\">Smith's band</span>" in sheet
          and 'id="gets-study"' in sheet and "api('/api/gets-settings', gets)" in fn(app, "saveProjectSettings"))
    check("75, 83: no sparkles of the GETs mode's own, its AI controls the PETs screen's, and the screen told the real switch",
          "TH_SPARK_ICON" not in js.split("── GETs ── */", 1)[1].split("/* ── wiring ── */", 1)[0]
          and "config=cfg, ai=ai," in inspect.getsource(idiograph_routes.gets_reply))

    node = shutil.which("node")
    if not node:
        skip("75: the GETs mode in node", "no node on this machine")
    else:
        script = scratch / "gets-model.js"
        script.write_text(support.i18n_js() + js + r"""
const out = {};
out.petsUnit = thUnit({ groups: [{ id: 'g1', members: [] }], stickies: [] }, 'g1');
out.petsId = thNextId({ groups: [{ id: 'g2', members: [] }] });
TH.mode = 'gets';
TH.gets = { cases: [{ case: 'Wren', who: 'Wren', in: true }, { case: 'Ash', who: 'Ash', in: true }, { case: 'Fern', who: 'Fern', in: false }],
  settings: { one_per_pet: true }, minimum: 2, total: 2 };
const card = (key, kind, kase) => ({ key, kind, case: kase, who: kase, text: key, x: 0, y: 0 });
const v = { cards: { 'Wren/g1': card('Wren/g1', 'pet', 'Wren'), 'Ash/g3': card('Ash/g3', 'sub', 'Ash'),
  'Wren/pn/1': card('Wren/pn/1', 'pn', 'Wren'), 'Fern/g1': card('Fern/g1', 'pet', 'Fern'), 'Ash/g2': card('Ash/g2', 'pet', 'Ash') },
  groups: [{ id: 'G1', label: 'One', members: ['Wren/g1', 'G2', 'Wren/pn/1', 'Fern/g1'] }, { id: 'G2', label: 'Sub', members: ['Ash/g3'] }],
  discarded: [], picks: {}, stickies: [] };
out.getsUnit = [thUnit(v, 'G1'), thUnit(v, 'G2')];
out.getsId = thNextId(v);
out.count = [gtCount(v, 'G1'), gtCount(v, 'G2')];
out.left = gtLeft(v);
out.split = [gtSplit('P8 - Wren/es/Initial:12:0'), gtSplit('Wren/g1/2'), gtBase('Wren/g1/2')];
out.kicker = [gtKicker(v.cards['Wren/g1']), gtKicker(v.cards['Ash/g3']), gtKicker(v.cards['Wren/pn/1'])];
const one = gtMenuItems(v, { kind: 'card', id: 'Wren/g1' }, thMenuItems(v, { kind: 'card', id: 'Wren/g1' }, false)).map((i) => i.act);
TH.gets.settings.one_per_pet = false;
const many = gtMenuItems(v, { kind: 'card', id: 'Wren/g1' }, thMenuItems(v, { kind: 'card', id: 'Wren/g1' }, false)).map((i) => i.act);
const label = gtMenuItems(v, { kind: 'group', id: 'G1' }, thMenuItems(v, { kind: 'group', id: 'G1' }, false)).map((i) => i.act);
out.menus = [one, many, label];
out.also = gtAlsoTargets(v, 'Wren/g1').map((g) => g.id);
out.marks = [gtMarks({ kind: 'pet', who: 'Ash', gone: true }), gtMarks({ kind: 'es', gone: true }), gtMarks({ kind: 'pet', open: true }), gtMarks({ kind: 'pn' })];
console.log(JSON.stringify(out));
""", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("75: the GETs mode runs in node", False, run.stderr.strip()[:300])
        else:
            o = json.loads(run.stdout)
            check("75: in node, the PETs screen is as it was: a top label is a PET and a new one g2's next",
                  o["petsUnit"] == "PET" and o["petsId"] == "g3", str([o["petsUnit"], o["petsId"]]))
            check("75: in node, on the GETs canvas a label over cards is a GET, over labels a sub-theme, and a new one G3",
                  o["getsUnit"] == ["GET", "sub-theme"] and o["getsId"] == "G3", str([o["getsUnit"], o["getsId"]]))
            check("75: in node, the count takes PETs and sub-themes under it, never a participant note or a case out of the study",
                  o["count"] == [2, 1], str(o["count"]))
            check("75: in node, what is left is the PETs and sub-themes under no GET",
                  o["left"] == 1, str(o["left"]))
            check("75: in node, a card's key names its case and kind, and a second card its first",
                  o["split"][0] == {"kase": "P8 - Wren", "kind": "es", "ident": "Initial:12:0", "copy": None}
                  and o["split"][1] == {"kase": "Wren", "kind": "group", "ident": "g1", "copy": "2"} and o["split"][2] == "Wren/g1",
                  str(o["split"]))
            check("75: in node, a card's kicker names its kind and pseudonym",
                  o["kicker"] == ["PET · Wren", "Sub-theme · Ash", "Participant note · Wren"], str(o["kicker"]))
            check("75: in node, One GET per PET on offers no Place also under, off it does, and a label has no Copy to board",
                  "also" not in o["menus"][0] and "also" in o["menus"][1] and o["menus"][1].index("also") < o["menus"][1].index("discard")
                  and "copyto" not in o["menus"][2] and o["also"] == ["G2"], str(o["menus"]) + str(o["also"]))
            check("75: in node, the marks: no longer in its PETs, no longer in the workbook, PETs not complete, and none on a note",
                  o["marks"] == [["No longer in Ash's PETs"], ["No longer in the workbook"], ["PETs not complete"], []], str(o["marks"]))
