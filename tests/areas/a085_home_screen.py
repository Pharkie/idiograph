from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import openpyxl

import rounds as rounds_mod
import workbook as wb_mod

from . import support
from .support import check, json_strings, line_of_js, skip
import idiograph_routes


def test_home_screen(scratch):
    print("\n85. The home screen, participant first (195): a card per case with its two halves, Start, Files, "
          "the GETs card and the days in the head, and no Continue (101)")
    import subprocess
    import time
    import gets as gets_mod
    import server as server_mod
    import themes as themes_mod

    pristine = support.DEMO_PRISTINE

    # ── A. an invented study under a scratch root: every name made up, no folder spelled out
    root = scratch / "home-root"
    shutil.rmtree(root, ignore_errors=True)
    folder = lambda n, who: root / "P{} - {}-{}".format(n, who, "Example")

    def case_from(name, case_dir, stem, sidecars=True):
        """A demo case's pristine workbook in a case folder under a new stem, with its sidecars, its
        themes file naming the case as the folder shows it."""
        case_dir.mkdir(parents=True, exist_ok=True)
        book = case_dir / f"{stem}.xlsx"
        shutil.copy2(pristine / f"{name} - EN & ES.xlsx", book)
        os.utime(book, (time.time(), time.time()))
        if sidecars:
            (case_dir / "Working").mkdir(exist_ok=True)
            for kind in (".progress.json", ".themes.json"):
                src = pristine / "Working" / f"{name} - EN & ES{kind}"
                if src.exists():
                    shutil.copy2(src, case_dir / "Working" / f"{stem}{kind}")
            board = themes_mod.themes_path(book)
            if board.exists():
                data = json.loads(board.read_text(encoding="utf-8"))
                data["case"] = server_mod.display_case(case_dir.name)
                board.write_text(json.dumps(data, indent=1), encoding="utf-8")
        return book

    def raw_at(path):
        path.parent.mkdir(parents=True, exist_ok=True)
        book = openpyxl.Workbook()
        book.active.title = "Initial"
        book.active.append(["Name", "Timestamp", "Transcript"])
        book.active.append(["Ada", "00:00:05", "An invented line."])
        book.save(path)
        return path

    ada = case_from("Rowan", folder(1, "Ada"), "P1 Ada - EN & ES")
    ada_raw = raw_at(folder(1, "Ada") / "Source" / "P1 - Ada v1.xlsx")
    bea_raw = raw_at(folder(2, "Bea") / "Source" / "P2 - Bea v1.xlsx")
    cal = case_from("Mabel", folder(3, "Cal"), "P3 Cal - EN & ES")
    cal_two = case_from("Juno", folder(3, "Cal"), "P3 Cal 2 - EN & ES")
    os.utime(cal, (time.time() - 3600, time.time() - 3600))
    # Cal's boards stay and none of them is the Current board
    cal_themes = themes_mod.themes_path(cal)
    held = json.loads(cal_themes.read_text(encoding="utf-8"))
    held.pop("chosen", None)
    held.pop("complete", None)
    cal_themes.write_text(json.dumps(held, indent=1), encoding="utf-8")
    vtt = folder(4, "Dee") / "Source" / "P4 - Dee.vtt"
    vtt.parent.mkdir(parents=True)
    vtt.write_text("WEBVTT\n\n00:00:01.000 --> 00:00:04.000\n<v Adam>How was the first week?\n\n"
                   "00:00:05.000 --> 00:00:09.000\n<v Dee>Quieter than I thought.\n", encoding="utf-8")
    eve = case_from("Juno", folder(10, "Eve"), "P10 Eve - EN & ES")
    wb_mod.lock_file(eve).write_text("open", encoding="utf-8")
    pilot = case_from("Mabel", root / "Pilot", "Pilot - EN & ES")
    loose = root / "Loose - EN & ES.xlsx"
    shutil.copy2(pristine / "Rowan - EN & ES.xlsx", loose)

    kept = (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_PATH = scratch / "home-state.json"
    server_mod.STATE_MEMORY = {"recent": []}
    rel = server_mod.rel_path
    try:
        # ── B. the cards from the server
        listed = idiograph_routes.api_cases({})
        cards = listed["participants"]
        by = {c["case"]: c for c in cards}
        check("85: a card for each case folder, in case order, P2 before P10, a folder with no P-number after them and "
              "a workbook in the root a card of its own, named by its stem",
              [c["case"] for c in cards] == ["P1 - Ada", "P2 - Bea", "P3 - Cal", "P4 - Dee", "P10 - Eve", "Pilot", "Loose - EN & ES"]
              and by["Loose - EN & ES"]["path"] == rel(loose) and by["Pilot"]["path"] == rel(pilot),
              str([c["case"] for c in cards]))
        leaks = [v for v in json_strings(json.loads(json.dumps(cards, default=str))) if "-Example" in v]
        check("85: a card's title is the P-number and pseudonym, and the second name never reaches the cards outside the paths",
              not leaks and by["P1 - Ada"]["case"] == "P1 - Ada", str(leaks[:3]))
        counted = {}
        for c in cards:
            if c["path"] and not c["locked"]:
                summary = idiograph_routes.case_payload(server_mod.abs_path(c["path"]))["progress"]
                counted[c["case"]] = (c["turns"], {"done": summary["turnsDone"], "total": summary["turnsTotal"]})
        check("85: the Statements half counts the turns decided of the turns there, as the case's own screen counts them",
              len(counted) == 4 and all(a == b for a, b in counted.values()), str(counted))
        a, e = by["P1 - Ada"], by["P10 - Eve"]
        check("85: in progress, the turns and no mark, and complete, the mark from the progress file",
              e["turns"]["done"] < e["turns"]["total"] and not e["complete"]
              and a["turns"]["done"] == a["turns"]["total"] and a["complete"], f"{e['turns']} {a['turns']}")
        check("85: the PETs half carries the Current board's name and the PETs mark, from the themes file",
              a["board"] == "Board 1" and a["boards"] >= 1 and a["pets_complete"] and a["pets_complete"]["at"], str(a["board"]))
        check("85: a case with no board at all, and no themes file",
              e["board"] is None and e["boards"] == 0 and not e["in_gets"] and not e["pets_complete"])
        check("85: a workbook open in Excel marks its card locked, and the server still counts it",
              e["locked"] is True and e["turns"]["total"] > 0 and not a["locked"])
        check("85: a case with no annotated workbook is Not started, Start taking its newest raw source, or else its transcript",
              by["P2 - Bea"]["path"] is None and by["P2 - Bea"]["start"]["path"] == rel(bea_raw)
              and by["P2 - Bea"]["start"]["kind"] == "raw"
              and by["P4 - Dee"]["path"] is None and by["P4 - Dee"]["start"]["kind"] == "transcript"
              and by["P4 - Dee"]["start"]["path"] == rel(vtt) and a["start"] is None)
        check("85: of two annotated workbooks with none opened, the card takes the newest, the other under Files",
              by["P3 - Cal"]["path"] == rel(cal_two) and [f["path"] for f in by["P3 - Cal"]["files"]] == [rel(cal_two), rel(cal)])
        under = sorted(f["path"] for c in cards for f in c["files"])
        check("85: Files holds every row the old list showed, each under its own case, the workbook first",
              under == sorted(r["path"] for r in listed["cases"]) and len(under) == len(set(under))
              and all(c["files"][0]["path"] == c["path"] for c in cards if c["path"])
              and [f["path"] for f in a["files"]] == [rel(ada), rel(ada_raw)]
              and listed["cases"] and listed["recent"] == [], f"{len(under)} files")

        # ── C. the recent list, with no Continue
        # Ada is complete in both phases, and opening her draws her row as any other. Her marks are
        # then taken off, and her row says so at once
        idiograph_routes.api_open({"path": str(ada)})
        done_both = next(c for c in idiograph_routes.api_cases({})["participants"] if c["case"] == "P1 - Ada")
        check("85, 101: a case complete in both phases, opened last, carries no continue field and keeps both marks",
              "continue" not in done_both and done_both["complete"] and done_both["pets_complete"])
        for side, key in ((rounds_mod.progress_path(ada), "complete"), (themes_mod.themes_path(ada), "complete")):
            data = json.loads(side.read_text(encoding="utf-8"))
            data.pop(key, None)
            side.write_text(json.dumps(data, indent=1), encoding="utf-8")
        server_mod.STATE_MEMORY = {"recent": []}
        idiograph_routes.api_open({"path": str(ada)})
        stored = server_mod.STATE_MEMORY["recent"]
        cards = idiograph_routes.api_cases({})["participants"]
        ada_card = next(c for c in cards if c["case"] == "P1 - Ada")
        check("85, 101: opening a case puts it at the head of the recent list with no screen, and no card carries continue",
              stored[0]["path"] == rel(ada) and sorted(stored[0]) == ["case", "name", "opened", "path"]
              and not any("continue" in c for c in cards) and not ada_card["complete"] and not ada_card["pets_complete"])
        idiograph_routes.api_themes({"workbook": str(ada)})
        stored = server_mod.STATE_MEMORY["recent"]
        check("85, 101: opening the PETs screen puts the case at the head as opening a case does, with no screen",
              [r["path"] for r in stored] == [rel(ada)] and not any("screen" in r for r in stored))
        idiograph_routes.api_themes({"workbook": str(cal), "beside": True})
        check("85: a board shown beside the GETs canvas is not an opening, and the recent list stands",
              [r["path"] for r in server_mod.STATE_MEMORY["recent"]] == [rel(ada)])
        idiograph_routes.api_open({"path": str(cal)})
        cards = idiograph_routes.api_cases({})["participants"]
        c3 = next(c for c in cards if c["case"] == "P3 - Cal")
        check("85: of two annotated workbooks the card takes the one opened last, though older, and the rows keep case order",
              c3["path"] == rel(cal) and [f["path"] for f in c3["files"]] == [rel(cal), rel(cal_two)]
              and not any("continue" in c for c in cards)
              and [c["case"] for c in cards][:3] == ["P1 - Ada", "P2 - Bea", "P3 - Cal"])
        check("85: a case with boards and none of them Current, its boards counted and no board named",
              c3["board"] is None and c3["boards"] >= 1 and not c3["pets_complete"], str(c3["boards"]) + " boards")
        if server_mod.DEMO_WORKBOOK.exists():
            idiograph_routes.api_open({"path": rel(server_mod.DEMO_WORKBOOK)})
        again = idiograph_routes.api_cases({})
        check("85: the demo's rows carry no continue field, opened or not, and the demo never enters the recent list",
              all("continue" not in c and c["demo"] for c in again["demo_participants"])
              and server_mod.STATE_MEMORY["recent"][0]["path"] == rel(cal)
              and not any("continue" in c for c in again["participants"]))
        check("85: the demo's cards are its three cases, built as the root's are",
              [c["case"] for c in again["demo_participants"]] == [r["case"] for r in again["demos"]]
              and all(c["turns"] and c["files"] for c in again["demo_participants"]))
        old_entry = {"path": rel(ada), "name": ada.stem, "case": "P1 - Ada", "opened": 1, "screen": "pets"}
        server_mod.STATE_MEMORY = {"recent": [old_entry]}
        drawn = idiograph_routes.api_cases({})["participants"]
        idiograph_routes.api_open({"path": str(pilot)})
        check("85, 101: an entry a build from before kept with its screen draws no continue, and loses the screen at the next open",
              not any("continue" in c for c in drawn)
              and [(r["path"], sorted(r)) for r in server_mod.STATE_MEMORY["recent"]]
              == [(rel(pilot), ["case", "name", "opened", "path"]), (rel(ada), ["case", "name", "opened", "path"])])

        # ── D. the GETs card's line
        head = idiograph_routes.api_cases({})["gets"]
        check("85: with no GETs file the GETs card counts none in and names no board",
              head["held"] == 0 and head["board"] is None and head["boards"] == 0 and head["cases"] >= 5, str(head))
        books = idiograph_routes.gets_books(root)
        when = themes_mod.now_iso()
        data, _cases, _disk, _taken = gets_mod.assemble(root, books, when)
        first = gets_mod.boards_of(data)[0]
        first["name"] = "Board 2"
        data["chosen"] = first["id"]
        out = sorted(books, key=lambda b: gets_mod.case_order(b["case"]))
        for b in out[3:]:
            data["cases"].pop(b["case"], None)
        gets_mod.write(root, gets_mod._file(data, when))
        listed = idiograph_routes.api_cases({})
        head = listed["gets"]
        cards = {c["case"]: c for c in listed["participants"]}
        check("85: the GETs card counts the cases the file holds of the cases of the study, and names its Current board",
              head["held"] == 3 and head["cases"] == len(books) and head["board"] == "Board 2" and head["boards"] == 1,
              f"{head['held']} of {head['cases']}, {head['board']}")
        check("85: a case the GETs file holds says in GETs on its PETs half, and one it does not hold says nothing of it",
              cards["P1 - Ada"]["in_gets"] and cards["P3 - Cal"]["in_gets"] and not cards["Pilot"]["in_gets"]
              and not cards["P10 - Eve"]["in_gets"])

        # ── E. the listing's speed: nothing unchanged is opened again
        opened = []
        real = server_mod.openpyxl.load_workbook
        server_mod.openpyxl.load_workbook = lambda *a, **k: (opened.append(a[0]), real(*a, **k))[1]
        try:
            began = time.perf_counter()
            idiograph_routes.api_cases({})
            took = time.perf_counter() - began
            ada.touch()
            idiograph_routes.api_cases({})
        finally:
            server_mod.openpyxl.load_workbook = real
        # a workbook is opened from its bytes read whole since wbguard (13 November 2026), which carry its path as `name`
        names = [Path(getattr(p, "name", p)).name for p in opened]
        check("85: a second listing opens no workbook that has not changed, and opens one that has, once",
              names == [ada.name], str(names))
        check("85: and lands at once for the demo and seven cases", took < 1.0, f"{took * 1000:.0f} ms")
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept

    # ── F. the page
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda name: js.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in js else ""
    whole = lambda name: f"function {name}(" + fn(name) + "\n}"
    draw = fn("drawCards")
    check("85: each half and Start do what the old rows did",
          "if (what === 'statements') openCaseIn(p.path);" in draw
          and "else if (what === 'pets') openThemesIn(p.path, p.case);" in draw
          and "(p.start.kind === 'transcript' ? offerImport(p.start) : offerCreate(p.start))" in draw)
    check("85: the dots hold Files, a short list under the card drawn by the old row's code, and Esc shuts the menu",
          "renderFiles(li.querySelector('.pc-files ul'), p.files || []);" in draw
          and "files.hidden = !files.hidden;" in draw and "menuKeys(e, menu, () => { shut(); dots.focus(); })" in draw
          and "transcript ? offerImport(item) : raw ? offerCreate(item) : openCaseIn(item.path)" in fn("renderFiles")
          and "&#8943;" in fn("cardHtml") and 'class="row-menu pc-menu" role="menu" hidden' in fn("cardHtml"))
    node = shutil.which("node")
    if not node:
        skip("85: the cards in node", "node is not installed")
    else:
        pieces = [line_of_js(js, "const esc = "), line_of_js(js, "const escAttr = "), line_of_js(js, "const plural = "),
                  whole("getsLine"), whole("esLine"), whole("petsLine"), whole("cardsFrom"), whole("gripHtml"), whole("cardHtml")]
        script = scratch / "home-cards.js"
        script.write_text(support.i18n_js() + "\n".join(pieces) + "\n" + r"""
const out = {};
out.es = [esLine({ turns: { done: 64, total: 207 } }), esLine({ turns: { done: 207, total: 207 }, complete: '2026-10-03' }),
  esLine({ turns: { done: 0, total: 1 } }), esLine({ sheets: ['Initial', '2d'] }), esLine({ sheets: ['Initial'], complete: 'x' })];
out.pets = [petsLine({ board: 'Mornings apart', boards: 2 }),
  petsLine({ board: 'Mornings apart', boards: 2, pets_complete: { at: 'x' }, in_gets: true }),
  petsLine({ board: null, boards: 3 }), petsLine({ board: null, boards: 3, in_gets: true }),
  petsLine({ board: null, boards: 0 }), petsLine({ board: null, boards: 0, in_gets: true }),
  petsLine({ board: 'Board 1' }), petsLine({ board: null })];
out.gets = [getsLine({ cases: 6, held: 3, board: 'Board 2', boards: 2 }), getsLine({ cases: 6, held: 6, board: 'Board 2', done: { at: 'x' } }),
  getsLine({ cases: 1, held: 0, board: null, boards: 0 }), getsLine({ cases: 4, held: 1, board: null, boards: 2 }),
  getsLine({ cases: 4, complete: 2 })];
const row = (o) => Object.assign({ kind: 'annotated', sheets: ['Initial'], modified: 1, locked: false }, o);
const rows = [row({ path: 'a1', name: 'Ada', case: 'P1 - Ada', modified: 5 }), row({ path: 'a2', name: 'Ada 2', case: 'P1 - Ada', modified: 9 }),
  row({ path: 'b1', name: 'Bea v1', case: 'P2 - Bea', kind: 'raw' }), row({ path: 'd1', name: 'Dee.vtt', case: 'P4 - Dee', kind: 'transcript' }),
  row({ path: 'c1', name: 'Cal', case: 'P3 - Cal', board: 'B', complete: 'x' })];
const fresh = cardsFrom(rows, []);
const back = cardsFrom(rows, [{ path: 'a1', screen: 'pets' }]);
out.old = { names: fresh.map((c) => c.case), adaFresh: fresh[0].path, adaBack: back[0].path, cont: back.map((c) => 'continue' in c),
  files: back[0].files.map((f) => f.path), bea: [fresh[1].path, fresh[1].start && fresh[1].start.path], dee: fresh[2].start.kind,
  plain: cardsFrom(rows, [{ path: 'c1' }]).map((c) => 'continue' in c), none: cardsFrom([], []).length };
const card = { case: 'P1 - Ada', path: 'a', turns: { done: 3, total: 9 }, board: 'Board 1', boards: 1, files: [] };
out.html = {
  plain: cardHtml(card),
  locked: cardHtml(Object.assign({}, card, { locked: true })),
  lockedGo: cardHtml(Object.assign({}, card, { locked: true, continue: 'statements' })),
  pets: cardHtml(Object.assign({}, card, { continue: 'pets' })),
  start: cardHtml({ case: 'P2 - Bea', path: null, start: { path: 'b', kind: 'raw' } }),
  demo: cardHtml(Object.assign({}, card, { demo: true, continue: 'statements' })),
};
console.log(JSON.stringify(out));
""", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("85: the cards run in node", False, run.stderr.strip()[:400])
        else:
            o = json.loads(run.stdout)
            check("85: the Statements half's line in each state, and the sheets from a server from before the counts",
                  o["es"] == ["64 of 207 passages", "207 of 207 passages · complete", "0 of 1 passage", "Initial, 2d", "Initial · complete"], str(o["es"]))
            check("85: the PETs half's line: the Current board, PETs complete, in GETs, No Current board and No PETs yet",
                  o["pets"] == ["Mornings apart", "Mornings apart · PETs complete · in GETs", "No Current board",
                                "No Current board · in GETs", "No PETs yet", "No PETs yet", "Board 1", ""], str(o["pets"]))
            check("85: the GETs card's line, and the cases alone from a server from before it",
                  o["gets"] == ["3 of 6 participants in · Board 2", "6 of 6 participants in · Board 2 · GETs complete", "0 of 1 participant in",
                                "1 of 4 participants in · No Current board", "4 participants"], str(o["gets"]))
            old = o["old"]
            check("85: in front of a server from before the cards, a card per case from the old rows, every case opening",
                  old["names"] == ["P1 - Ada", "P2 - Bea", "P4 - Dee", "P3 - Cal"] and old["adaFresh"] == "a2"
                  and old["adaBack"] == "a1" and old["files"] == ["a1", "a2"] and old["cont"] == [False] * 4
                  and old["bea"] == [None, "b1"] and old["dee"] == "transcript"
                  and old["plain"] == [False] * 4 and old["none"] == 0, str(old))
            h = o["html"]
            check("85: open in Excel, the tag on the card, the Statements half disabled and PETs still opening",
                  '<span class="tag locked">open in Excel</span>' in h["locked"]
                  and 'data-act="statements" disabled>' in h["locked"] and 'data-act="pets">' in h["locked"])
            check("85, 101: a continue from a server from before draws nothing, on a project's row, a locked one or the demo's",
                  h["pets"] == h["plain"] and h["lockedGo"] == h["locked"]
                  and not any("pc-continue" in v or "Continue" in v or 'data-act="continue"' in v for v in h.values())
                  and '<span class="tag demo">demo</span>' in h["demo"])
            check("85: a case not started reads Not started and carries Start experiential statements alone",
                  '<p class="pc-none">Not started</p>' in h["start"] and ">Start experiential statements</button>" in h["start"]
                  and "pc-half" not in h["start"])
