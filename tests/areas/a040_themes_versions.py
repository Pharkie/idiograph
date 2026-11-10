from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import export as export_mod
import rounds as rounds_mod
import workbook as wb_mod
from workbook import WorkbookError

from . import support
from .support import DEMO_SHEET, check, demo_copy, json_strings, skip, slashed
import idiograph_routes


def test_themes_versions(scratch):
    print("\n40. Themes, stage 2: boards, picks, the quotes panel, the export and Reset demo")
    import csv
    import http.server
    import subprocess
    import threading
    import urllib.error
    import urllib.request
    import make_demo
    import server as server_mod
    import themes as themes_mod

    root = scratch / "versions-root"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    path = themes_mod.themes_path(work)
    rows = {r["row"]: r for r in wb_mod.read_case(work)["sheets"][0]["rows"]}
    # key quotes on two more turns, taken word for word from them, so a label has more than one
    quoted = {3: ["\"she is sat on the second stair\"", "\"Bramble is just there, all the time.\""],
              9: ["\"the first thing that happens in our house every single day\""]}
    for n, quotes in quoted.items():
        wb_mod.save_turn(work, DEMO_SHEET, n, rows[n]["es"], rows[n]["en"], "\n".join(quotes))
    read = themes_mod.read_cards(work)
    k = [c["key"] for c in read["cards"]]
    by_row = {}
    for c in read["cards"]:
        by_row.setdefault(c["row"], []).append(c["key"])
    last = max(by_row)

    # ── A. the key quotes each row carries, for the panel
    check("every row with key quotes is read, each quote keyed by sheet, row and its place there",
          sorted(read["quotes"]) == sorted(f"{DEMO_SHEET}:{n}" for n in (3, 9, last))
          and [q["key"] for q in read["quotes"][f"{DEMO_SHEET}:3"]["quotes"]] == [f"{DEMO_SHEET}:3:0", f"{DEMO_SHEET}:3:1"]
          and [q["text"] for q in read["quotes"][f"{DEMO_SHEET}:3"]["quotes"]] == quoted[3],
          ", ".join(sorted(read["quotes"])))
    check("a row's quotes carry its timecode, the way the player's clock writes it",
          read["quotes"][f"{DEMO_SHEET}:3"]["seconds"] == rows[3]["seconds"]
          and read["quotes"][f"{DEMO_SHEET}:3"]["time"] == rows[3]["time"]
          and read["quotes"][f"{DEMO_SHEET}:9"]["time"] == rows[9]["time"])

    saved_root = server_mod.ROOT_OVERRIDE
    server_mod.ROOT_OVERRIDE = str(root)
    try:
        first = idiograph_routes.api_themes({"workbook": str(work)})
        check("/api/themes sends the quotes and the picks, an empty set on a fresh case",
              first["quotes"] == read["quotes"] and first["picks"] == {} and not path.exists())

        def body(state, groups, discarded=(), picks=None, **meta):
            # no version, as a page from before versions: these saves reuse one read, and area 198
            # holds what a stale version does
            return {**{k: x for k, x in state["version"].items() if k != "v"}, **meta,
                    "cards": {c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in state["cards"]},
                    "groups": groups, "discarded": list(discarded), "picks": picks or {}}

        q3, q31, q9, qlast = (f"{DEMO_SHEET}:3:0", f"{DEMO_SHEET}:3:1", f"{DEMO_SHEET}:9:0", f"{DEMO_SHEET}:{last}:0")
        # the grouped cards in columns, so the canvas reads each theme in transcript order and the
        # two sub-themes side by side, Mornings on the left
        laid = {by_row[3][0]: (0, 100), by_row[9][0]: (0, 200), by_row[9][1]: (0, 300),
                by_row[last][0]: (600, 100), by_row[last][1]: (600, 200), by_row[7][0]: (1400, -600)}
        for c in first["cards"]:
            if c["key"] in laid:
                c["x"], c["y"] = laid[c["key"]]
        groups = [{"id": "g1", "label": "Mornings", "members": [by_row[3][0], by_row[9][0], by_row[9][1]], "x": 0, "y": 40},
                  {"id": "g2", "label": "The unsaid", "members": [by_row[last][0], by_row[last][1]], "x": 300, "y": 52},
                  {"id": "g3", "label": "Home life", "members": ["g1", "g2"], "x": 0, "y": 0},
                  {"id": "g4", "label": "Standing apart", "members": [by_row[7][0]], "x": 600, "y": -400}]
        picks = {"g1": [q9, q3, q3, f"{DEMO_SHEET}:3:7", qlast, 5], "g3": [qlast], "g4": [q3], "g9": [q3],
                 "g2": "not a list"}
        idiograph_routes.api_themes_save({"workbook": str(work), "version": body(
            first, groups, [by_row[5][2]], picks, note="Mornings first")})
        stored = json.loads(path.read_text(encoding="utf-8"))["boards"][0]

        # ── B. picks, normalised on the way in
        check("picks are kept per label, once each, in the order ticked",
              stored["picks"]["g1"] == [q9, q3] and stored["picks"]["g3"] == [qlast], str(stored["picks"]))
        check("a pick of a quote the row does not have, or of a row with no card under the label, is dropped",
              f"{DEMO_SHEET}:3:7" not in stored["picks"]["g1"] and qlast not in stored["picks"]["g1"]
              and "g4" not in stored["picks"])
        check("a pick for a label that is not there, or that is not a list, is dropped",
              set(stored["picks"]) == {"g1", "g3"})
        check("a label over labels picks from every card under it, at any depth", stored["picks"]["g3"] == [qlast])
        check("the first save takes the name and the note the page sent",
              stored["name"] == "Board 1" and stored["note"] == "Mornings first")

        idiograph_routes.api_themes_save({"workbook": str(work), "version": body(
            first, groups, [by_row[5][2]], {"g1": [q9, q3, q31], "g3": [qlast]})})
        # the second quote of row 3 goes from the workbook, so the pick of it has nothing to point at
        wb_mod.save_turn(work, DEMO_SHEET, 3, rows[3]["es"], rows[3]["en"], quoted[3][0])
        again = idiograph_routes.api_themes({"workbook": str(work)})
        check("a pick whose quote has gone from the workbook is dropped when the case is read",
              json.loads(path.read_text(encoding="utf-8"))["boards"][0]["picks"]["g1"] == [q9, q3, q31]
              and again["picks"]["g1"] == [q9, q3] and len(again["quotes"][f"{DEMO_SHEET}:3"]["quotes"]) == 1,
              str(again["picks"]))
        idiograph_routes.api_themes_save({"workbook": str(work), "version": body(again, again["groups"],
                                    again["discarded"], {"g1": [q9, q31], "g3": [qlast]})})
        check("and when the board is saved: the file never keeps a pick of a quote that is not there",
              json.loads(path.read_text(encoding="utf-8"))["boards"][0]["picks"] == {"g1": [q9], "g3": [qlast]})
        wb_mod.save_turn(work, DEMO_SHEET, 3, rows[3]["es"], rows[3]["en"], "\n".join(quoted[3]))
        saved = idiograph_routes.api_themes_save({"workbook": str(work), "version": body(
            again, again["groups"], again["discarded"], {"g1": [q9, q3], "g3": [qlast]},
            name="A name sent late", note="A note sent late")})
        held = json.loads(path.read_text(encoding="utf-8"))["boards"][0]
        check("a save from the canvas keeps the name and the note the file holds, which belong to the boards",
              held["name"] == "Board 1" and held["note"] == "Mornings first" and saved["version"]["name"] == "Board 1")

        # ── C. the boards, through the file
        def op(what, **extra):
            return idiograph_routes.api_themes_versions({"workbook": str(work), "op": what, **extra})

        def file():
            return json.loads(path.read_text(encoding="utf-8"))

        def refused(call):
            before = path.read_bytes()
            try:
                call()
            except WorkbookError as exc:
                return str(exc) if path.read_bytes() == before else ""
            return ""

        v1 = file()["boards"][0]
        made = op("new")
        data = file()
        fresh = data["boards"][1]
        check("New adds an empty board, current, with every card back in the pile",
              made["current"] == "v2" == data["current"] and fresh["name"] == "Board 2"
              and fresh["groups"] == [] and fresh["discarded"] == [] and fresh["picks"] == {} and fresh["note"] == ""
              and {key: (c["x"], c["y"]) for key, c in fresh["cards"].items()}
              == {key: (p["x"], p["y"]) for key, p in themes_mod.pile(read["cards"]).items()},
              f"{len(fresh['cards'])} cards")
        check("New leaves the board it came from as it was",
              data["boards"][0] == v1 and made["groups"] == [] and made["version"]["id"] == "v2"
              and [v["id"] for v in made["versions"]] == ["v1", "v2"])
        copy = op("duplicate", id="v1")
        data = file()
        twin = data["boards"][1]
        check("Duplicate copies a board under a new name, beside it, and makes the copy current",
              copy["current"] == "v3" == data["current"] and [v["id"] for v in data["boards"]] == ["v1", "v3", "v2"]
              and twin["name"] == "Board 1 copy" and twin["groups"] == v1["groups"]
              and twin["cards"] == v1["cards"] and twin["picks"] == v1["picks"] and twin["discarded"] == v1["discarded"])
        check("the copy starts with a note of its own, empty", twin["note"] == "" and v1["note"] == "Mornings first")
        check("a second copy of the same board takes the next free name",
              op("duplicate", id="v1")["version"]["name"] == "Board 1 copy 2")
        op("delete", id="v4")
        renamed = op("rename", id="v3", name="  Mornings   apart ")
        check("Rename changes the name alone, its spaces tidied",
              [v["name"] for v in file()["boards"]] == ["Board 1", "Mornings apart", "Board 2"]
              and [v["name"] for v in renamed["versions"] if v["id"] == "v3"] == ["Mornings apart"]
              and file()["boards"][1]["groups"] == v1["groups"] and renamed["current"] == file()["current"])
        check("a name another board has is refused, whatever its case, and so is no name",
              "called" in refused(lambda: op("rename", id="v2", name="mornings APART"))
              and "needs a name" in refused(lambda: op("rename", id="v2", name="   ")))
        op("note", id="v3", note="Trying the mornings as a theme of their own.\nAnd the stairs apart.")
        check("Note keeps a few lines on why, on that board alone",
              file()["boards"][1]["note"] == "Trying the mornings as a theme of their own.\nAnd the stairs apart."
              and file()["boards"][0]["note"] == "Mornings first")
        before = {v["id"]: v for v in file()["boards"]}
        switched = op("switch", id="v1")
        check("Switch makes another board current and changes nothing in any of them",
              file()["current"] == "v1" and {v["id"]: v for v in file()["boards"]} == before
              and switched["version"]["name"] == "Board 1" and switched["picks"] == {"g1": [q9, q3], "g3": [qlast]}
              and [g["id"] for g in switched["groups"]] == ["g1", "g2", "g3", "g4"])
        op("switch", id="v2")
        gone = op("delete", id="v2")
        check("Delete takes a board out, and the one before it becomes current when it was",
              [v["id"] for v in file()["boards"]] == ["v1", "v3"] and file()["current"] == "v3" == gone["current"])
        op("delete", id="v3")
        check("the last board is refused, and so is a board the file does not hold",
              "last board" in refused(lambda: op("delete", id="v1"))
              and "no longer" in refused(lambda: op("switch", id="v9"))
              and "no longer" in refused(lambda: op("rename", id="v9", name="Nine"))
              and [v["id"] for v in file()["boards"]] == ["v1"])
        check("an op the boards do not have is refused and writes nothing",
              "not something" in refused(lambda: op("merge", id="v1")))
        check("a save against a board the file does not hold is refused, and the file is left as it was",
              "no longer" in refused(lambda: idiograph_routes.api_themes_save(
                  {"workbook": str(work), "version": body(switched, [], id="v3")})))
        bare = demo_copy(root, "Bare", "Juno - EN & ES.xlsx")
        offered = idiograph_routes.api_themes({"workbook": str(bare)})
        try:
            idiograph_routes.api_themes_save({"workbook": str(bare), "version": body(offered, [], id="v2")})
            stray = True
        except WorkbookError:
            stray = False
        check("with no file yet, only the board an open offers is taken",
              not stray and not themes_mod.themes_path(bare).exists())
        op_bare = idiograph_routes.api_themes_versions({"workbook": str(bare), "op": "duplicate"})
        check("an op on a case with no file gives it its first board, then acts",
              [v["name"] for v in op_bare["versions"]] == ["Board 1", "Board 1 copy"]
              and op_bare["current"] == "v2" and op_bare["case"] == "Bare" and op_bare["demo"] is False)
        check("an op answers with the screen's state, the way /api/themes does",
              {"cards", "groups", "discarded", "picks", "quotes", "versions", "version", "current", "sheets"}
              <= set(op_bare))

        # ── D. the markdown draft, with a label over labels
        op("rename", id="v1", name="By the day")
        state = idiograph_routes.api_themes({"workbook": str(work)})
        text, version = themes_mod.draft_markdown(work, "Juno")
        lines = text.splitlines()
        cards = {c["key"]: c for c in state["cards"]}
        line = lambda key: f"- {cards[key]['text']} ({DEMO_SHEET}, {cards[key]['time']})"
        fresh = themes_mod.read_cards(work)
        own = lambda key: (themes_mod.own_quote(fresh["quotes"], key) or {}).get("text") or ""
        said = lambda key: line(key) + (f"\\\n  \u2018{themes_mod.bare(own(key))}\u2019" if own(key) else "")
        check("the draft opens with the case by its pseudonym and the board's name, and leaves the board's note out (185)",
              lines[0] == "# Juno: PET grouping draft (By the day)" and "Mornings first" not in text, lines[0])
        heads = [l for l in lines if l.startswith("#")]
        check("theme by theme in canvas order, lettered as the book letters them, a sub-theme a heading under its PET by its reference, the lists at the end counted (185, 206, 207, 208)",
              heads == ["# Juno: PET grouping draft (By the day)", "## A. Standing apart", "## B. Home life",
                        "### B1. Mornings", "### B2. The unsaid", "## Not placed (11)", "## Experiential statements set aside (1)"], " | ".join(heads))
        mornings = text.split("### B1. Mornings\n", 1)[1].split("\n### ", 1)[0]
        check("each statement on its own line with its sheet and timecode, in transcript order, its own quote under it (95)",
              mornings.strip() == "\n".join(said(key) for key in (by_row[3][0], by_row[9][0], by_row[9][1]))
              and own(by_row[3][0]) and own(by_row[9][0]) and not own(by_row[9][1])
              and re.search(r"\(Initial, \d\d:\d\d\)$", line(by_row[3][0])), mornings[:200])
        check("no picked quote is listed under a heading, every statement carrying its own, as in the table of PETs (95)",
              not any(l.startswith(('"', "\u201c")) for l in lines) and text.count(quoted[9][0].strip('"')) == 1
              and "\nQuotes\n" not in text)
        home = text.split("## B. Home life\n", 1)[1].split("\n### ", 1)[0]
        check("a label over labels with no statement of its own goes straight to its sub-themes, its picks not listed (95)",
              home.strip() == "")
        quote_lines = [l for l in lines if l.startswith("  \u2018")]
        check("no quote line reads as a markdown list, each set in under its statement after a break, none quoted twice",
              quote_lines and all(l.endswith("\u2019") and not l.startswith("  \u2018\u2018") and '\u2018"' not in l
                                  and lines[lines.index(l) - 1].endswith("\\") for l in quote_lines))
        unplaced = text.split("## Not placed (11)\n", 1)[1].split("\n## ", 1)[0]
        placed = {by_row[3][0], by_row[9][0], by_row[9][1], by_row[last][0], by_row[last][1], by_row[7][0]}
        rest = [key for key in k if key not in placed and key != by_row[5][2]]
        check("the unplaced statements listed at the end, and the discarded under their own heading",
              unplaced.strip() == "\n".join(said(key) for key in rest)
              and text.rstrip().endswith("## Experiential statements set aside (1)\n\n" + said(by_row[5][2])))
        check("no em dash, no semicolon, and the timecodes as the clock writes them",
              "\u2014" not in text and ";" not in text
              and all(re.search(r", (\d\d:\d\d|\d:\d\d:\d\d)\)\\?$", l) for l in lines
                      if l.startswith("- ") and not re.match(r"- ([A-Z]+|PET \d+)\. ", l)))
        written = themes_mod.write_draft(work, "Juno")
        check("the draft is written beside the progress file, named for the workbook and the board",
              Path(written["path"]) == work.parent / "Working" / "Juno - PET draft (By the day).md"
              and Path(written["path"]).read_text(encoding="utf-8") == text)
        check("a board name a file name cannot carry is made safe",
              themes_mod.draft_path(work, 'A/B: "c"').name == "Juno - PET draft (A-B- -c-).md")
        check("canvas order reads a row left to right, labels within a card's height of one another sharing it",
              themes_mod.canvas_order(["a", "b", "c"], {"a": {"x": 400, "y": 12}, "b": {"x": 0, "y": 40},
                                                        "c": {"x": 0, "y": 300}}) == ["b", "a", "c"])

        # ── E. the CSV's Proposed PET column, from the same board
        out = export_mod.export(work, themes=(path, None))
        csv_rows = list(csv.reader(Path(out["path"]).read_text(encoding="utf-8-sig").splitlines()))
        pet = {row[2]: row[3] for row in csv_rows[1:]}
        check("the header keeps its name, and every statement keeps its line",
              csv_rows[0] == export_mod.HEADER and out["statements"] == len(k) == len(csv_rows) - 1)
        check("a statement in a sub-theme carries the theme and the sub-theme, top-most first",
              pet[cards[by_row[3][0]]["text"]] == "Home life / Mornings"
              and pet[cards[by_row[last][0]]["text"]] == "Home life / The unsaid"
              and pet[cards[by_row[7][0]]["text"]] == "Standing apart")
        check("a discarded statement says so, and an unplaced one is left blank",
              pet[cards[by_row[5][2]]["text"]] == "Set aside" and all(pet[cards[key]["text"]] == "" for key in rest))
        named = export_mod.export(work, themes=(path, "v1"))
        check("a board named by its id fills the column the same way", named["statements"] == out["statements"])
        try:
            export_mod.export(work, themes=(path, "v9"))
            unknown = False
        except WorkbookError:
            unknown = True
        none = export_mod.export(bare, themes=(root / "nowhere.themes.json", None))
        blank = Path(none["path"]).read_text(encoding="utf-8-sig").splitlines()
        check("a board the file lacks is refused, and with no themes file the column stays empty",
              unknown and all(r[3] == "" for r in csv.reader(blank[1:])))
        settings = idiograph_routes.api_export({"path": str(work)})
        filled = Path(work.parent / "Working" / "Juno - All Experiential Statements.csv").read_text(encoding="utf-8-sig")
        check("the export in Settings fills the column from the current board when the case has a themes file",
              "Home life / Mornings" in filled and settings["statements"] == len(k)
              and "Proposed PET (blank for you)" in filled.splitlines()[0])
        plain = demo_copy(root, "Plain", "Juno - EN & ES.xlsx")
        idiograph_routes.api_export({"path": str(plain)})
        check("and leaves it empty, as it always did, when there is none",
              all(r[3] == "" for r in csv.reader((plain.parent / "Working" / "Juno - All Experiential Statements.csv")
                                                  .read_text(encoding="utf-8-sig").splitlines()[1:])))

        book = work.read_bytes()
        lock = wb_mod.lock_file(work)
        lock.write_text("", encoding="utf-8")
        try:
            both = idiograph_routes.api_themes_export({"workbook": str(work), "version": "v1"})
        finally:
            lock.unlink()
        check("/api/themes-export writes the draft and the CSV, and reports both, with Excel's lock no bar",
              slashed(both["markdown"]).endswith("Juno/Working/Juno - PET draft (By the day).md")
              and slashed(both["csv"]).endswith("Juno/Working/Juno - All Experiential Statements.csv")
              and both["paths"] == [both["markdown"], both["csv"]] and both["statements"] == len(k)
              and both["version"]["name"] == "By the day", both["markdown"])
        check("the export never writes the workbook", work.read_bytes() == book)
        current_only = idiograph_routes.api_themes_export({"workbook": str(work)})
        check("with no board named, the current one goes", current_only["version"]["id"] == file()["current"])

        folder = "P9 - {}-{}".format("Alpha", "Beta")
        gravity = demo_copy(root, folder, "P9 Alpha - EN & ES.xlsx")
        shown = idiograph_routes.api_themes({"workbook": str(gravity)})
        idiograph_routes.api_themes_save({"workbook": str(gravity), "version": body(shown, [
            {"id": "g1", "label": "One theme", "members": [shown["cards"][0]["key"]], "x": 0, "y": 0}])})
        result = idiograph_routes.api_themes_export({"workbook": str(gravity)})
        draft = (gravity.parent / "Working" / "P9 Alpha - PET draft (Board 1).md").read_text(encoding="utf-8")
        check("a GRAVITY case's draft is named for its pseudonym, and the second part of the folder name is nowhere",
              draft.startswith("# P9 - Alpha: PET grouping draft (Board 1)") and "Beta" not in draft
              and not any("Beta" in s for s in json_strings(result, skip_keys=())), result["markdown"])
        versioned = idiograph_routes.api_themes_versions({"workbook": str(gravity), "op": "new"})
        check("and so is an op's answer", not any("Beta" in s for s in json_strings(versioned, skip_keys=("path",)))
              and versioned["case"] == "P9 - Alpha")

        # ── F. the two routes over HTTP, the root guard and a server from before them
        outside = demo_copy(scratch, "versions-elsewhere", "Juno - EN & ES.xlsx")
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
        threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()

        def post(route, payload):
            req = urllib.request.Request(f"http://127.0.0.1:{httpd.server_address[1]}{route}",
                                         data=json.dumps(payload).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    return r.status, json.loads(r.read())
            except urllib.error.HTTPError as exc:
                return exc.code, json.loads(exc.read())

        new_routes = ("/api/themes-versions", "/api/themes-export")
        held_routes = {r: server_mod.ROUTES.pop(r) for r in new_routes}
        try:
            old = [post(r, {"workbook": str(work), "op": "new"}) for r in new_routes]
        finally:
            server_mod.ROUTES.update(held_routes)
        try:
            ok = post("/api/themes-versions", {"workbook": str(work), "op": "switch", "id": "v1"})
            far = [post(r, {"workbook": str(outside), "op": "new"})[0] for r in new_routes]
            last_one = post("/api/themes-versions", {"workbook": str(work), "op": "delete", "id": "v1"})
        finally:
            httpd.shutdown()
            httpd.server_close()
        check("over HTTP the boards answer, a refusal is a 409 with its line, and outside the root is a 403",
              ok[0] == 200 and ok[1]["current"] == "v1" and far == [403, 403]
              and last_one[0] == 409 and "last board" in last_one[1]["error"]
              and not themes_mod.themes_path(outside).exists())
        check("a server from before them answers with the line the page turns into the restart line",
              all(code == 404 and answer == {"error": "No such endpoint.", "code": "no_endpoint"} for code, answer in old))
        check("both routes are in the dispatch table",
              server_mod.ROUTES.get("/api/themes-versions") is idiograph_routes.api_themes_versions
              and server_mod.ROUTES.get("/api/themes-export") is idiograph_routes.api_themes_export)
    finally:
        server_mod.ROOT_OVERRIDE = saved_root

    # ── G. Reset demo takes away a themes file the pristine copy holds none for, on the suite's fixture
    # in a pristine copy's shape, Juno's with no board (support.DEMO_PRISTINE)
    where = scratch / "versions-demo"
    kept = (make_demo.CASE, make_demo.WORKBOOK, make_demo.PRISTINE)
    shutil.copytree(support.DEMO_PRISTINE, where / "pristine")
    make_demo.CASE = where / "Juno"
    make_demo.WORKBOOK = make_demo.CASE / "Juno - EN & ES.xlsx"
    make_demo.PRISTINE = where / "pristine"
    try:
        demo_copy(where, "Juno", "Juno - EN & ES.xlsx")
        held_file = themes_mod.themes_path(make_demo.WORKBOOK)
        held_file.parent.mkdir(parents=True, exist_ok=True)
        held_file.write_text('{"schema": 1, "versions": []}\n', encoding="utf-8")
        other = held_file.parent / "Juno - PET draft (Board 1).md"
        other.write_text("# a draft\n", encoding="utf-8")
        make_demo.reset()
        side = rounds_mod.progress_path(make_demo.WORKBOOK)
        check("Reset demo removes a themes file the pristine copy holds none for, so the canvas opens on the pile again",
              not held_file.exists() and not list(held_file.parent.glob("*.themes.json")))
        check("and puts back the workbook and the progress file as before, leaving the rest of Working alone",
              side.read_bytes() == (make_demo.PRISTINE / "Working" / side.name).read_bytes()
              and make_demo.WORKBOOK.read_bytes() == (make_demo.PRISTINE / make_demo.WORKBOOK.name).read_bytes()
              and other.exists())
    finally:
        make_demo.CASE, make_demo.WORKBOOK, make_demo.PRISTINE = kept

    # ── H. the page
    static = server_mod.HERE / "static"
    page = support.page_text()
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    js = support.text("apps/idiograph/static/themes.js")
    fn = lambda text, name: text.split(f"function {name}(", 1)[1].split("\n}", 1)[0]
    menu = fn(js, "thVmenuDraw")
    check("the last board's Delete is disabled, and a delete asks first on a card in the trim card's style",
          "one ? ` disabled" in menu and '<div class="overlay" id="th-confirm" hidden>' in page
          and 'class="trim-line" id="th-confirm-line"' in page and "'th-confirm'" in app.split("const OVERLAYS = ", 1)[1].split("\n", 1)[0]
          and "thDeleteGo();" in fn(js, "thKeyDown") and "hide('th-confirm');" in fn(js, "thKeyDown"))
    check("every board op saves the canvas first, and a server from before them gets the restart line",
          "await thFlush();" in fn(js, "thBoardOp") and "needsRestart(err) ? RESTART_LINE : err.message" in fn(js, "thBoardOp")
          and "needsRestart(err) ? RESTART_LINE : err.message" in fn(js, "thExport"))
    check("each board keeps its own undo and redo while the case is open",
          "TH.stacks[TH.undoBoard] = { undo: TH.undo, redo: TH.redo };" in fn(js, "thUseStacks")
          and "thUseStacks(TH.meta.id);" in fn(js, "thLoad"))
    check("a quote's play button cues its row's timecode, and the same button again pauses",
          "if (TH.seekKey === key && TH.audioSheet === sheet && player.getAttribute('src')) { thPlayToggle(); return; }"
          in fn(js, "thPlayQuote") and "player.currentTime = at;" in fn(js, "thPlayQuote"))
    check("the panel keeps the focus off its buttons, so the canvas keys still work, and Esc clears the selection and leaves it open (114)",
          "panel.addEventListener('pointerdown', (e) => { if (e.target.closest('button')) e.preventDefault(); });" in js
          and "board.addEventListener('pointerdown', (e) => { if (e.target.closest('button')) e.preventDefault(); });" in js
          and "{ thClearSel(); thPanelFollow(); }" in fn(js, "thKeyDown")
          and "e.key === 'v' || e.key === 'V'" in fn(js, "thKeyDown"))

    node = shutil.which("node")
    if not node:
        return skip("the picks model in node", "no node on this machine")
    script = scratch / "themes-picks.js"
    script.write_text(support.i18n_js() + js + r"""
const card = (sheet, row, line, x) => ({ sheet, row, line, x, y: 0, text: `${row}.${line}`, seconds: row * 10, time: '' });
const v = { cards: { 'S:3:0': card('S', 3, 0, 0), 'S:3:1': card('S', 3, 1, 1), 'S:9:0': card('S', 9, 0, 2),
  'T:2:0': card('T', 2, 0, 3) }, groups: [], discarded: [], picks: {} };
const keep = (x) => JSON.parse(JSON.stringify(x));
const out = {};
const g1 = thMakeGroup(v, ['S:9:0', 'S:3:1'], 'One');
const g2 = thMakeGroup(v, ['T:2:0'], 'Two');
const g3 = thMakeGroup(v, [g1, g2], 'Over');
out.on = [thTogglePick(v, g1, 'S:3:0'), thTogglePick(v, g1, 'S:9:0'), thTogglePick(v, g3, 'T:2:0')];
out.off = thTogglePick(v, g1, 'S:9:0');
out.picks = keep(v.picks);
out.rowsUnder = thRowsUnder(v, g3);
const quotes = { 'S:3': { seconds: 31, time: '00:31', quotes: [{ key: 'S:3:0', text: 'a' }, { key: 'S:3:1', text: 'b' }] },
  'T:2': { seconds: 5, time: '00:05', quotes: [{ key: 'T:2:0', text: 'c' }] } };
out.panel = thPanelRows(v, { kind: 'group', id: g3 }, quotes, ['S', 'T']).map((r) => [r.row, r.cards, r.quotes.length, r.seconds]);
out.card = thPanelRows(v, { kind: 'card', id: 'S:9:0' }, quotes, ['S', 'T']).map((r) => [r.row, r.quotes.length, r.seconds]);
const snap = thSnap(v, new Set());
thLeave(v, 'S:3:1');
thPrunePicks(v);
out.left = keep(v.picks);
thPut(v, snap);
out.back = keep(v.picks);
thDelete(v, g3);
thPrunePicks(v);
out.deleted = keep(v.picks);
out.body = thBody(v, { id: 'v1', name: 'V', note: '', created: 'c', updated: 'u' }).picks;
console.log(JSON.stringify(out));
""", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("the picks model runs in node", False, run.stderr.strip()[:300])
    out = json.loads(run.stdout)
    check("a tick goes on and comes off, one label's picks apart from another's",
          out["on"] == [True, True, True] and out["off"] is False
          and out["picks"] == {"g1": ["S:3:0"], "g3": ["T:2:0"]}, str(out["picks"]))
    check("a label over labels reaches the rows of every card under it", out["rowsUnder"] == ["S:9", "S:3", "T:2"])
    check("the panel lists a label's rows in transcript order, each with its cards and their own quotes (198)",
          out["panel"] == [["S:3", ["S:3:1"], 1, 31], ["S:9", ["S:9:0"], 0, 90], ["T:2", ["T:2:0"], 1, 5]]
          and out["card"] == [["S:9", 0, 90]], str(out["panel"]))
    check("a card that leaves takes its row's picks with it, and undo puts them back",
          out["left"] == {"g3": ["T:2:0"]} and out["back"] == {"g1": ["S:3:0"], "g3": ["T:2:0"]},
          f"{out['left']} {out['back']}")
    check("a label deleted takes its own picks, and the board body carries the picks",
          out["deleted"] == {"g1": ["S:3:0"]} and out["body"] == {"g1": ["S:3:0"]})
