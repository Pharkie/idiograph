from __future__ import annotations

import csv
import io
import json
import os
import re
import shutil
from pathlib import Path

from workbook import WorkbookError

from . import support
from .support import check, line_of_js, skip
import idiograph_routes


@support.as_app("sift")
def test_sift_reviews(scratch):
    print("\n109. Sift's reviews: one list of reviews on the home screen, New review and Open review, a review's steps "
          "in PRISMA's order, the two lists before it read into one, and opening that writes nothing")
    import subprocess
    import server as server_mod
    import sift_routes
    import sift
    import sift_search as ss
    import sift_second

    page = support.page_text()
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    # Sift's parts of the shell, from app.js since the family codebase's third build (22 October 2026)
    sset = support.text("apps/sift/static/sift_settings.js")
    sjs = support.text("apps/sift/static/sift.js")
    ssjs = support.text("apps/sift/static/sift_search.js")
    # Sift's styles as its page loads them, the frame it shares with Trace first (tracestyle, 30 October 2026)
    scss = support.text("family/static/frame.css", "apps/sift/static/sift.css")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    node = shutil.which("node")
    same = lambda a, b: bool(a) and Path(a).resolve() == Path(b).resolve()

    def view_is(v, folder, name, searches, shown, run=None) -> bool:
        """A review as the steps draw it: its folder, its name, its research question (12 October, 118),
        whether it has searches, the screening its Screening step opens and that run's folder name, the
        run's folder name and its name in words, its second screener settings, the defaults on a review
        that has none (12 October, 119), and nothing more (9 October)"""
        opens = Path(shown).name if shown is not None and Path(shown).parent.name == ss.RUNS_DIR else None
        return (isinstance(v, dict)
                and sorted(v) == ["folder", "label", "name", "opens", "question", "run", "screening", "searches", "second"]
                and isinstance(v["question"], str) and v["second"] == sift_second.DEFAULTS
                and same(v["folder"], folder) and v["name"] == name and v["searches"] is searches and v["run"] == run
                # a run named by its number and its day since 12 October, later (124)
                and v["opens"] == opens and v["label"] == (ss.run_said(run, folder) if run else None)
                and (v["screening"] is None if shown is None else same(v["screening"], shown)))

    # ── A. every folder and record invented, on urban beekeeping, mosses and ponds
    base = scratch / "sift-reviews-109"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)

    def tree(at: Path) -> dict:
        # each path with slashes on any system, and a lock file never read, since Windows refuses a
        # read of a file another holds locked (14 October)
        return {p.relative_to(at).as_posix(): (p.read_bytes() if p.is_file() and p.suffix != ".lock" else None)
                for p in sorted(at.rglob("*"))}

    def screening(at: Path, rows) -> Path:
        at.mkdir(parents=True, exist_ok=True)
        with open(at / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["rec_id", "title", "abstract"])
            w.writerows(rows)
        return at

    hives = [["B001", "Rooftop hives in a city", "Keepers on six roofs described their first summer."],
             ["B002", "Swarm calls and neighbours", "An invented survey of swarm calls in one town."],
             ["B003", "Wax and winter", "Notes on wintering colonies through a cold spring."]]
    ponds = [["P001", "Newts in garden ponds", "Twelve gardeners kept a diary of newts."],
             ["P002", "Dragonflies over still water", "An invented count of dragonflies."]]
    plan = {"databases": ["pubmed"], "blocks": [{"name": "Bees", "terms": "bee*\nhive*"}]}

    class Done:
        def __init__(self, code):
            self.returncode, self.stdout, self.stderr = code, "", ""

    asked_keys = []

    def no_keys(argv, **_):
        """The keychain stood in for: every service asked holds no key, and nothing reaches the tool"""
        asked_keys.append(argv[argv.index("-s") + 1] if "-s" in argv else "")
        return Done(44)

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
            server_mod.PICK_FOLDER, server_mod.PLATFORM, ss.RUNNER, os.environ.pop(ss.STUB_ENV, None))
    live_config = server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None
    state_file = scratch / "sift-reviews-109-state.json"
    cfg_file = base / "config.json"
    cfg_file.write_text(json.dumps({"projects": []}), encoding="utf-8")
    rows_seen = {}
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH = state_file
        ss.RUNNER = no_keys
        rv = sift_routes.api_sift_review
        row_of = lambda folder: next((r for r in sift_routes.review_rows() if same(r["folder"], folder)), {})

        def refused(call) -> str:
            before, held = tree(base), json.dumps(server_mod.STATE_MEMORY, sort_keys=True)
            try:
                call()
                return "done"
            except (WorkbookError, server_mod.OutsideRoot) as exc:
                untouched = tree(base) == before and json.dumps(server_mod.STATE_MEMORY, sort_keys=True) == held
                return str(exc) if untouched else "written: " + str(exc)

        # ── B. the two lists before it read into one, every folder kept once
        old = base / "old"
        meadow = old / "Meadow review"
        meadow.mkdir(parents=True)
        ss.write_file(meadow, {"versions": []})
        meadow_run = screening(meadow / "runs" / "2026-03-02", hives)
        pond_old = screening(old / "pond screening", ponds)
        heath = old / "heath review"
        heath.mkdir()
        gone = old / "gone screening"
        server_mod.STATE_MEMORY = {"recent": [], "sift": [
            {"folder": str(meadow_run), "opened": 500}, {"folder": str(pond_old), "opened": 300},
            {"folder": str(gone), "opened": 100}], "sift_searches": [
            {"folder": str(meadow), "opened": 200}, {"folder": str(heath), "opened": 400}]}
        listed = sift_routes.reviews_kept()
        rows = sift_routes.review_rows()
        check("109: the two lists before it are read into one, newest first, a run's screening as the review above it and "
              "each folder once, so every folder he opened stays",
              [Path(e["folder"]).resolve() for e in listed] == [p.resolve() for p in (meadow, heath, pond_old, gone)]
              and [e["opened"] for e in listed] == [500, 400, 300, 100]
              and [(r["name"], r["there"]) for r in rows] == [("Meadow review", True), ("heath review", True),
                                                              ("pond screening", True), ("gone screening", False)]
              and [r.get("searches") for r in rows] == [True, True, False, None], str([r["name"] for r in rows]))
        with server_mod._lock:
            sift_routes.remember_review(heath.resolve())
        held = server_mod.STATE_MEMORY
        check("109: the first write keeps the one list, sift_reviews, and takes the two before it away, every folder in it",
              "sift" not in held and "sift_searches" not in held and held["recent"] == []
              and [Path(e["folder"]).resolve() for e in held["sift_reviews"]] == [p.resolve() for p in (heath, meadow, pond_old, gone)],
              str(sorted(held)))
        many = {"recent": [], "sift": [{"folder": str(old / f"s{n}"), "opened": n} for n in range(8)],
                "sift_searches": [{"folder": str(old / f"r{n}"), "opened": 10 + n} for n in range(8)]}
        check("109: sixteen reviews are kept, so the two lists before it, eight each, come in whole",
              len(sift_routes.reviews_old(many)) == 16 == sift_routes.REVIEWS_KEPT
              and Path(sift_routes.reviews_old(many)[0]["folder"]).name == "r7")

        # ── C. New review: the dialog, the folder checked, the review made and its row
        server_mod.STATE_MEMORY = {"recent": []}
        empty = base / "Urban bees"
        empty.mkdir()
        asked = []
        server_mod.PLATFORM = "darwin"
        server_mod.PICK_FOLDER = lambda prompt: (asked.append(prompt), None)[1]
        cancelled = rv({"op": "folder", "mode": "new"})
        server_mod.PICK_FOLDER = lambda prompt: (asked.append(prompt), empty)[1]
        picked = rv({"op": "folder", "mode": "new"})
        server_mod.PLATFORM = "linux"
        no_dialog = refused(lambda: rv({"op": "folder", "mode": "new"}))
        typed = rv({"op": "folder", "mode": "new", "path": str(empty)})
        check("109, 9 October: Sift's New project folder comes from the Mac's dialog, its Cancel choosing nothing, or a typed "
              "path, and an empty folder offers its own name for it",
              cancelled == {"chosen": False} and picked["chosen"] and same(picked["folder"], empty)
              and picked["name"] == "Urban bees" and typed == picked and no_dialog == server_mod.NO_DIALOG
              and asked == [sift_routes.NEW_REVIEW_PROMPT] * 2 == ["Choose the folder for the new Sift project."] * 2, str(picked))
        made = rv({"op": "new", "folder": str(empty), "name": "Urban bees", "question": "How do keepers live with city hives?"})
        on_disk = json.loads((empty / ss.PLAN_NAME).read_text(encoding="utf-8"))
        rows = sift_routes.review_rows()
        rows_seen["new"] = row_of(empty)
        check("109: Create review writes a blank plan in the empty folder, its name and question and no version, and the "
              "review is the first row",
              made["made"] and view_is(made["review"], empty, "Urban bees", True, None)
              and on_disk == {"name": "Urban bees", "question": "How do keepers live with city hives?", "versions": []}
              and sorted(tree(empty)) == [ss.PLAN_NAME] and rows[0]["name"] == "Urban bees" and same(rows[0]["folder"], empty)
              and rows[0]["version"] is None and rows[0]["run"] is None, str(made))
        shelf = base / "Reviews"
        shelf.mkdir()
        (shelf / "reading list.txt").write_text("invented titles\n", encoding="utf-8")
        inside = rv({"op": "new", "folder": str(shelf), "name": "Heath bees: wild and kept?"})
        check("109: a folder that holds anything gets a new folder inside it, named for the review in letters a folder takes",
              inside["made"] and same(inside["review"]["folder"], shelf / "Heath bees wild and kept")
              and sorted(tree(shelf)) == ["Heath bees wild and kept", f"Heath bees wild and kept/{ss.PLAN_NAME}", "reading list.txt"]
              and inside["review"]["name"] == "Heath bees: wild and kept?", inside["review"]["folder"])

        # ── D. the refusals, each one line, each writing nothing, the list included
        moss = base / "kept" / "Moss review"
        moss.mkdir(parents=True)
        ss.new_plan(moss, "Mosses on old walls")
        ss.save(moss, plan)
        screening(moss / "runs" / "2026-04-01", hives[:2])
        newest_run = screening(moss / "runs" / "2026-05-01", hives)
        pond = screening(base / "kept" / "Pond screening", ponds)
        notes = base / "kept" / "Just notes"
        notes.mkdir()
        (notes / "notes.txt").write_text("nothing of a review\n", encoding="utf-8")
        broken = base / "kept" / "Broken plan"
        broken.mkdir()
        (broken / ss.PLAN_NAME).write_text("{", encoding="utf-8")
        (shelf / "Pond bees").mkdir()
        (shelf / "Pond bees" / "draft.txt").write_text("a draft\n", encoding="utf-8")
        new = lambda folder, name="Another review": rv({"op": "new", "folder": str(folder), "name": name})
        said = {"holds a review": refused(lambda: new(empty)), "holds a screening": refused(lambda: new(pond)),
                "runs folder": refused(lambda: new(moss / "runs")), "run folder": refused(lambda: new(newest_run)),
                "no name": refused(lambda: new(notes, " ")), "no folder": refused(lambda: rv({"op": "new", "name": "A"})),
                "not there": refused(lambda: new(base / "nowhere")),
                "named there": refused(lambda: new(shelf, "Pond bees")),
                "no letters": refused(lambda: new(shelf, "///")),
                "op": refused(lambda: rv({"op": "remove"}))}
        want = {"holds a review": "That folder holds a Sift project already.",
                "holds a screening": "That folder holds a screening already.",
                "runs folder": "That folder is part of a Sift project already.",
                "run folder": "That folder is part of a Sift project already.",
                "no name": "Name the project first.", "no folder": "Name the folder first.",
                "not there": "That folder is not there.", "named there": "There is a folder named Pond bees there already.",
                "no letters": "A folder cannot take that name, so give the project another.",
                "op": "The op is folder, new, open, read, rename, second, forget or reveal."}
        check("109, 9 October, updated 12 October (118, its ops rename and forget, and 119, second) and 6 November 2026 (330, "
              "reveal): Sift's New project refuses in one line a folder that holds a review or a screening or is part "
              "of one, a project with no name and a folder named for it there already, each in the word project, and each "
              "refusal writes nothing",
              said == want, str({k: v for k, v in said.items() if want.get(k) != v}))

        # ── E. Open review: a plan's folder, a screening alone, a run's folder, and nothing written into any of them
        opened = {}
        for key, folder in (("plan", moss), ("alone", pond), ("run", newest_run), ("runs", moss / "runs")):
            mark = (tree(moss), tree(pond), sorted(os.listdir(moss)), sorted(os.listdir(pond)))
            server_mod.PLATFORM = "darwin"
            server_mod.PICK_FOLDER = lambda prompt, f=folder: f
            chosen = rv({"op": "folder", "mode": "open"})
            got = rv({"op": "open", "folder": chosen["folder"], "name": chosen["name"]})
            back = rv({"op": "read", "folder": got["review"]["folder"]})
            home = server_mod.api_home({})["reviews"]
            if key != "alone":
                sift_routes.api_sift_search({"op": "read", "folder": got["review"]["folder"]})
            opened[key] = (chosen, got["review"], back["review"], home[0],
                           mark == (tree(moss), tree(pond), sorted(os.listdir(moss)), sorted(os.listdir(pond))))
        m_view = lambda v, run=None: view_is(v, moss, "Mosses on old walls", True, newest_run, run)
        check("109: Open review takes a folder holding search_plan.json, named by its plan, its Screening the newest run's",
              m_view(opened["plan"][1]) and m_view(opened["plan"][2]) and same(opened["plan"][0]["folder"], moss)
              and opened["plan"][0]["name"] == "Mosses on old walls" and opened["plan"][3]["name"] == "Mosses on old walls",
              str(opened["plan"][1]))
        check("109: and a folder holding screening.csv alone, a review with no searches whose Screening is its own",
              view_is(opened["alone"][1], pond, "Pond screening", False, pond)
              and opened["alone"][3]["searches"] is False and opened["alone"][3]["stages"]["ta"]["records"] == 2,
              str(opened["alone"][1]))
        check("109: a run's folder chosen by mistake opens its review, and so does its runs folder",
              m_view(opened["run"][1]) and m_view(opened["runs"][1]) and same(opened["run"][0]["folder"], moss),
              str(opened["run"][0]))
        check("109: opening writes no byte into the folder: every file's bytes and every listing the same after the "
              "dialog, the open, the review's read, the home screen and the searches' read",
              all(o[4] for o in opened.values()), str({k: o[4] for k, o in opened.items()}))
        server_mod.PLATFORM = "linux"
        others = {"other": refused(lambda: rv({"op": "open", "folder": str(notes)})),
                  "other, checked": refused(lambda: rv({"op": "folder", "mode": "open", "path": str(notes)})),
                  "empty": refused(lambda: rv({"op": "open", "folder": str(shelf / "Pond bees")})),
                  "broken": refused(lambda: rv({"op": "open", "folder": str(broken)})),
                  "gone": refused(lambda: rv({"op": "open", "folder": str(base / "nowhere")}))}
        check("109: any other folder is refused in one line saying what a review's folder holds, and writes nothing",
              others == {"other": sift_routes.NOT_A_REVIEW, "other, checked": sift_routes.NOT_A_REVIEW,
                         "empty": sift_routes.NOT_A_REVIEW,
                         "broken": "search_plan.json cannot be read, so it was left as it is.",
                         "gone": "That folder is not there."}
              and sift_routes.NOT_A_REVIEW == "A Sift project's folder holds search_plan.json or screening.csv, and that one holds neither.",
              str(others))
        # a project's top folder chosen in place of its review's: one review folder inside opens it at once
        project = base / "Wall study"
        (project / "interview notes").mkdir(parents=True)
        (project / "interview notes" / "notes.txt").write_text("invented notes\n", encoding="utf-8")
        lichen = screening(project / "Lichen screening", ponds)
        mark = (tree(project), sorted(os.listdir(project)))
        one_checked = rv({"op": "folder", "mode": "open", "path": str(project)})
        one_open = rv({"op": "open", "folder": str(project)})
        check("109: a folder that is no review but holds one review folder directly inside it opens that review at once, "
              "writing nothing in either",
              one_checked["chosen"] and same(one_checked["folder"], lichen) and one_checked["name"] == "Lichen screening"
              and view_is(one_open["review"], lichen, "Lichen screening", False, lichen)
              and (tree(project), sorted(os.listdir(project))) == mark, str(one_checked))
        # and several inside: a short choice by folder name, and Open review on the top folder refused
        shared = base / "Shared reviews"
        shared.mkdir()
        (shared / "b bees").mkdir()
        ss.new_plan(shared / "b bees", "Bees on balconies")
        screening(shared / "A ponds", ponds)
        (shared / "Z scans").mkdir()
        mark = (tree(shared), sorted(os.listdir(shared)))
        held_state = json.dumps(server_mod.STATE_MEMORY, sort_keys=True)
        several = rv({"op": "folder", "mode": "open", "path": str(shared)})
        several_open = refused(lambda: rv({"op": "open", "folder": str(shared)}))
        taken = rv({"op": "folder", "mode": "open", "path": several["choices"][1]["folder"]}) if len(several.get("choices") or []) == 2 else {}
        check("109: a folder holding several review folders offers each by its folder's name, in order, chooses none, and "
              "Open review on it is refused in one line, nothing written in any of them and the list untouched",
              several["chosen"] is False and same(several["folder"], shared)
              and [c["label"] for c in several["choices"]] == ["A ponds", "b bees"]
              and same(several["choices"][0]["folder"], shared / "A ponds")
              and several_open == sift_routes.SEVERAL_REVIEWS == "That folder holds more than one Sift project, so choose one of them."
              and taken.get("chosen") and same(taken["folder"], shared / "b bees") and taken["name"] == "Bees on balconies"
              and (tree(shared), sorted(os.listdir(shared))) == mark
              and json.dumps(server_mod.STATE_MEMORY, sort_keys=True) == held_state, str(several))
        plan_bytes = (moss / ss.PLAN_NAME).read_bytes()
        named = rv({"op": "open", "folder": str(moss), "name": "My moss review"})
        entry = sift_routes.kept_review(moss.resolve())
        rows = sift_routes.review_rows()
        renamed_back = rv({"op": "open", "folder": str(moss), "name": "Mosses on old walls"})
        check("109: a name he gives is kept in the app's list, never in the folder, and his own name given back clears it",
              named["review"]["name"] == "My moss review" and entry.get("name") == "My moss review"
              and rows[0]["name"] == "My moss review" and (moss / ss.PLAN_NAME).read_bytes() == plan_bytes
              and renamed_back["review"]["name"] == "Mosses on old walls" and "name" not in sift_routes.kept_review(moss.resolve()),
              str(entry))

        # ── F. the guards: every route on a review's files asks the list
        stray = screening(base / "elsewhere" / "stray screening", ponds)
        guards = {"stray screening": refused(lambda: sift_routes.api_sift({"op": "read", "folder": str(stray)})),
                  "searches of a screening alone": refused(lambda: sift_routes.api_sift_search({"op": "read", "folder": str(pond)})),
                  "searches never opened": refused(lambda: sift_routes.api_sift_search({"op": "read", "folder": str(notes)})),
                  "a review never opened": refused(lambda: rv({"op": "read", "folder": str(notes)}))}
        check("109: a screening whose review the list does not hold is refused, as is a folder never opened, and a screening "
              "alone never gains a plan from the searches' route",
              guards == {"stray screening": sift_routes.NOT_OPENED, "searches of a screening alone": sift_routes.NO_SEARCHES,
                         "searches never opened": sift_routes.REVIEW_NOT_OPENED, "a review never opened": sift_routes.REVIEW_NOT_OPENED}
              and not (pond / ss.PLAN_NAME).exists() and sift_routes.sift_pdf({"folder": str(stray), "rec": "P001"})[0] == 403,
              str(guards))
        old_run = sift_routes.api_sift({"op": "read", "folder": str(moss / "runs" / "2026-04-01")})
        alone = sift_routes.api_sift({"op": "read", "folder": str(pond)})
        run_of = sift_routes.api_sift_search({"op": "screening", "folder": str(moss), "date": "2026-04-01"})
        check("109: a run's screening reads by the review above it, its review sent for the steps with the run's day, "
              "Screening then opening that run, the one he opened last (9 October), and a screening alone its own, "
              "Screening alone",
              view_is(old_run["review"], moss, "Mosses on old walls", True, moss / "runs" / "2026-04-01", "2026-04-01")
              and len(old_run["records"]) == 2
              and view_is(alone["review"], pond, "Pond screening", False, pond)
              and same(run_of["folder"], moss / "runs" / "2026-04-01")
              and sift_routes.sift_pdf({"folder": str(newest_run), "rec": "B001"})[0] == 404, str(old_run["review"]))
        check("109: the route sits after /api/sift-search and takes a POST alone, and the old ways in are gone",
              server_mod.ROUTES.get("/api/sift-review") is sift_routes.api_sift_review and "/api/sift-review" in server_mod.POST_ONLY
              and list(server_mod.ROUTES).index("/api/sift-review") == list(server_mod.ROUTES).index("/api/sift-search") + 1
              and refused(lambda: sift_routes.api_sift({"op": "open", "path": str(pond)})) == "Name the folder first."
              and refused(lambda: sift_routes.api_sift_search({"op": "recent"})) == "Name the folder first."
              and not any(hasattr(server_mod, n) for n in ("remember_sift", "remember_search", "sift_entries", "search_entries",
                                                           "PICK_SCREENING", "PICK_REVIEW")))

        # ── G. where each review stands, a row at each step
        bees = empty.resolve()
        sift_routes.api_sift_search({"op": "save", "folder": str(bees), "plan": plan})
        rows_seen["draft"] = row_of(bees)
        # Mark as registered names the registry and its number since 12 October, later (area 124)
        sift_routes.api_sift_search({"op": "register", "folder": str(bees), "registry": "PROSPERO", "registration": "CRD42026000002"})
        rows_seen["registered"] = row_of(bees)
        after = json.loads((bees / ss.PLAN_NAME).read_text(encoding="utf-8"))
        check("109: the plan keeps its own name and question through a save and a register",
              after["name"] == "Urban bees" and after["question"] == "How do keepers live with city hives?"
              and after["versions"][0]["registered"] and list(after) == ["name", "question", "versions"], str(list(after)))
        june = bees / "runs" / "2026-06-01"
        june.mkdir(parents=True)
        (june / ss.RUN_FILE).write_text("{}", encoding="utf-8")
        rows_seen["run, no screening"] = row_of(bees)
        rows_seen["run, no screening, view"] = rv({"op": "read", "folder": str(bees)})["review"]
        screening(june, hives)
        rows_seen["run"] = row_of(bees)
        sift.decide(june, "B001", "ta", "include")
        rows_seen["run, one decided"] = row_of(bees)
        sift.decide(june, "B001", "ft", "include")
        rows_seen["full text"] = row_of(bees)
        rows_seen["alone"] = row_of(pond)
        sift.decide(pond, "P001", "ta", "include")
        rows_seen["alone, one decided"] = row_of(pond)
        sift.decide(pond, "P002", "ta", "exclude")
        rows_seen["alone, full text"] = row_of(pond)
        (moss / ss.PLAN_NAME).write_text("[", encoding="utf-8")
        rows_seen["unreadable"] = row_of(moss)
        (moss / ss.PLAN_NAME).write_bytes(plan_bytes)
        shutil.rmtree(pond)
        rows_seen["gone"] = row_of(pond)
        check("109: a run with no screening yet leaves Screening waiting, and a screening's first run opens it",
              rows_seen["run, no screening, view"]["screening"] is None and rows_seen["run, no screening"]["run"] == {
                  "date": "2026-06-01", "label": "Run 1, 1 June 2026", "screening": False} and rows_seen["run"]["run"]["screening"] is True,
              str(rows_seen["run, no screening"]))
        check("109: the list lives in memory for the whole area, so no state.json is read or written",
              not state_file.exists() and server_mod.STATE_PATH == state_file)
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
         server_mod.PICK_FOLDER, server_mod.PLATFORM, ss.RUNNER) = kept[:7]
        if kept[7] is not None:
            os.environ[ss.STUB_ENV] = kept[7]
    check("109: the live config.json is exactly as it was, and the keychain was only ever stood in for",
          (server_mod.CONFIG_PATH.read_bytes() if server_mod.CONFIG_PATH.exists() else None) == live_config
          and set(asked_keys) <= set(ss.SERVICES), str(sorted(set(asked_keys))))

    # ── H. the row's line and the step a review opens on, in node
    lines_want = {"new": "No search plan yet", "draft": "Version 1, a draft", "registered": "Version 1, registered",
                  # a run by its number and its day since 12 October, later (124)
                  "run, no screening": "Run 1, 1 June 2026, no screening yet", "run": "Run 1, 1 June 2026, 0 of 3 records decided",
                  "run, one decided": "Run 1, 1 June 2026, 1 of 3 records decided",
                  "full text": "Run 1, 1 June 2026, full text 1 of 1 decided", "alone": "0 of 2 records decided",
                  "alone, one decided": "1 of 2 records decided", "alone, full text": "Full text 0 of 1 decided",
                  "unreadable": "search_plan.json cannot be read, so it was left as it is.", "gone": "Not there now"}
    steps_js = (line_of_js(ssjs, "const RV_STEP_KEY = ") + "\nconst SFS = { runs: [] };\n" + whole(ssjs, "rvStepOf") + "\n"
                + line_of_js(ssjs, "const RV_TA_LATER = ") + "\n" + line_of_js(ssjs, "const RV_FT_LATER = ") + "\n"
                + line_of_js(ssjs, "const RV_FORM_NAME = ") + "\n" + line_of_js(ssjs, "const RV_EX_LATER = ") + "\n"
                + line_of_js(ssjs, "const RV_DRAWN = ") + "\n" + whole(ssjs, "rvStepsHtml") + "\n" + whole(ssjs, "rvStepsDraw") + "\n"
                # the chevrons' measure since 17 October, later (122)
                + line_of_js(ssjs, "const RV_WATCHED = ") + "\n" + whole(ssjs, "rvStepsSeps") + "\n" + whole(ssjs, "rvStepsWatch") + "\n")
    if not node:
        skip("109: the lines and the steps in node", "node is not installed")
    else:
        script = scratch / "sift-reviews-109.js"
        rows_in = {k: v for k, v in rows_seen.items() if k in lines_want}
        script.write_text(
            line_of_js(app, "const plural = ") + "\n" + whole(sset, "reviewDay") + "\n" + whole(sset, "reviewDecided") + "\n"
            + whole(sset, "reviewLine") + "\n" + steps_js
            + f"const rows = {json.dumps(rows_in)};\n"
            "const lines = {};\nfor (const k of Object.keys(rows)) lines[k] = reviewLine(rows[k]);\n"
            "const on = (r, kept) => rvStepOf(r, kept);\n"
            "const steps = [on({ searches: true, screening: null }), on({ searches: true, screening: 'r/1' }),"
            " on({ searches: true, screening: 'r/1' }, 'searches'), on({ searches: true, screening: null }, 'screening'),"
            " on({ searches: false, screening: 'p' }, 'searches'), on({ searches: true, screening: 'r/1' }, 'screening')];\n"
            "const box = () => ({ innerHTML: '', querySelectorAll: () => [] });\n"
            "const drawn = (review, step) => { const b = box(); rvStepsDraw(b, review, step, null); return b.innerHTML; };\n"
            "const html = { alone: drawn({ searches: false, screening: 'p' }, 'ta'),"
            " waiting: drawn({ searches: true, screening: null }, 'searches'),"
            " ready: drawn({ searches: true, screening: 'r/1' }, 'searches'),"
            " on: drawn({ searches: true, screening: 'r/1' }, 'ta') };\n"
            "console.log(JSON.stringify({ lines, steps, html }));\n", encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        if ran.returncode != 0:
            check("109: the lines and the steps run in node", False, ran.stderr.strip()[:400])
        else:
            o = json.loads(ran.stdout)
            check("109: in node, a row's line says the review's newest step alone: the plan's version and whether it is "
                  "registered, the newest run's day and how many of its records are decided, or the full text so far",
                  o["lines"] == lines_want, str({k: v for k, v in o["lines"].items() if lines_want.get(k) != v}))
            check("109: in node, a review opens on the step it was left on, else Search strategy until a run has a screening and "
                  "Screening after, and a review with no searches on Screening",
                  o["steps"] == ["searches", "screening", "searches", "searches", "screening", "screening"], str(o["steps"]))
            h = o["html"]
            # each step's words over their hidden bold copy since 6 November 2026 (barsD, area 330)
            check("109, updated 12 October (122, 123), 13 October, later (129), 14 October (143), 15 October (145) and 6 November "
                  "2026 (330): in node, a review with no searches shows its three stages alone, Check references gone to Trace, and "
                  "with searches Search strategy then Screen by title and abstract, the step shown marked and Screen by title and "
                  "abstract waiting for a screening",
                  "Search strategy" not in h["alone"] and h["alone"].count("<button") == 3 and 'aria-current="step"' in h["alone"]
                  and h["alone"].endswith('<button type="button" data-step="ex"><span class="tab-w" data-bold="Extract and appraise">'
                                          'Extract and appraise</span></button>')
                  and 'data-step="refs"' not in h["alone"] + h["waiting"] + h["ready"]
                  and h["waiting"].index(">Search strategy<") < h["waiting"].index("&#8250;")
                  < h["waiting"].index(">Screen by title and abstract<")
                  and 'data-step="ta" aria-disabled="true"' in h["waiting"] and 'data-step="ta" aria-disabled' not in h["ready"]
                  and 'data-step="searches" aria-current="step"' in h["ready"]
                  and 'data-step="ta" aria-current="step"' in h["on"], str(h))

    # ── I. the page: the section, the card, the steps on both screens, and their ways
    home = page.split('id="sift-home"', 1)[1].split("</section>", 1)[0]
    card = page.split('<div class="overlay" id="rv-card" hidden>', 1)[1].split("\n</div>\n", 1)[0] if 'id="rv-card"' in page else ""
    check("109: a folder holding several reviews offers them in the card under the folder, a button each by its "
          "folder's name, which takes that review",
          'id="rv-choices"' in card and ">Project</span>" in card and "rvChoices(data.choices || []);" in fn(app, "rvFolder")
          and "rvFolder(choices[Number(b.dataset.i)].folder)" in fn(app, "rvChoices") and "esc(c.label)" in fn(app, "rvChoices")
          and "rvChoices([]);" in fn(app, "openReviewCard") and ".rv-pick {" in scss)
    check("109, updated 12 October (117): Create project sends the folder, the name and the question and opens the "
          "project made, as Distil's does, and Open project folder opens the project on its step",
          "{ op: 'new', folder, name:" in fn(app, "rvMake") and "question: $('rv-question').value.trim()" in fn(app, "rvMake")
          and "{ op: 'open', folder, name:" in fn(app, "rvMake") and "if (own && own.made) own.made(got);" in fn(app, "rvMake")
          and "if (got.review) rvShow(got.review);" in fn(sset, "sfpMade") and "made: sfpMade" in sset
          and "else loadLibrary()" in fn(app, "rvMake") and "else loadLibrary()" in fn(sset, "sfpMade")
          and "op: 'folder', mode: RVC.mode" in fn(app, "rvFolder"))
    check("109: both screens carry the review's steps after its name, Sift's screen asking its own routes alone, its "
          "screening and Sync to Zotero",
          '<nav class="sf-steps" id="sf-steps" aria-label="Steps" hidden></nav>' in page and 'id="sf-name"' in page
          and '<nav class="sf-steps" id="sfs-steps" aria-label="Steps" hidden></nav>' in ssjs
          and "rvHead('screening', SF.review);" in fn(sjs, "sfTake") and "rvHead('searches', SFS.review);" in fn(ssjs, "sfsOpen")
          and set(re.findall(r"api\('(/api/[a-z-]+)'", sjs)) == {"/api/sift", "/api/zotero"}
          and set(re.findall(r"api\('(/api/[a-z-]+)'", fn(ssjs, "rvOpen") + fn(ssjs, "rvStep"))) == {"/api/sift-review"}
          and "sfLeave(() => sfsOpen(review.folder, home));" in fn(ssjs, "rvStep") and "sfLeave(() => loadLibrary()" in fn(sjs, "sfBack")
          and "rvKeepStep(review.folder, step);" in fn(ssjs, "rvHead") and "'idiograph-sift-step'" in ssjs)
    check("109: a restart on a review's searches comes back to them",
          "return { screen: 'searches', path: SFS.folder };" in fn(sset, "siftSpot")
          and "'searches', 'sift'].includes(spot.screen)" in fn(app, "spotTaken")
          and "const own = familyApp(spot.screen);" in fn(app, "comeBack") and "own.open(spot.path, home, spot.screen)" in fn(app, "comeBack")
          and "if (screen === 'searches') sfsOpen(path, home);" in fn(sset, "sfOpenOn"))
    shared = support.text("family/static/style.css", "apps/idiograph/static/distil.css")
    review_code = "\n".join([whole(sset, n) for n in ("reviewDay", "reviewDecided", "reviewLine", "drawSiftHome")]
                            + [whole(app, n) for n in ("openReviewCard", "rvSaid", "rvChoices", "rvFolder", "rvMake")]
                            + [whole(ssjs, n) for n in ("rvSteps", "rvKeepStep", "rvStepOf", "rvOpen", "rvShow", "rvHead",
                                                         "rvStepsHtml", "rvStepsDraw", "rvStageCounts", "rvStep")])
    check("109: no AI anywhere in it, the code, the section and the card alike",
          not re.search(r"\bai\b|AI|sparkle|data-ai", review_code + card + home))

    # ── K. Start again: a screening trialled and begun afresh, its log kept whole in _Archive
    import cli
    import sift_cli
    import locks
    import mcp_server
    hedge = base / "Hedge review"
    hedge.mkdir()
    ss.new_plan(hedge, "Hedgerows and birds")
    run = hedge / "runs" / "2026-07-01"
    run.mkdir(parents=True)
    head = ["rec_id", "title", "abstract", "proposed_decision", "proposed_reason", "grounds", "ai_proposed_decision",
            "ai_proposed_reason", "ai_grounds"]
    with open(run / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(head)
        w.writerow(["H001", "Wrens in a laid hedge", "Walkers counted wrens along one hedge.", "", "", "", "include", "", "wrens"])
        w.writerow(["H002", "Blackthorn in spring", "An invented survey of blackthorn flowers.", "", "", "", "exclude", "E1", ""])
        w.writerow(["H003", "Gaps and gates", "Farmers spoke of gaps left for gates.", "", "", "", "", "", ""])
    (run / sift.REASONS_NAME).write_text("stage,code,meaning\nta,E1,Not about hedges\nft,F1,No full text\n", encoding="utf-8")
    (run / ss.RUN_FILE).write_text(json.dumps({"version": 1}), encoding="utf-8")
    (run / sift.SEARCHES_NAME).write_text("date,source,interface,query,hits,records_saved,note\n", encoding="utf-8")
    sift.decide(run, "H001", "ta", "include", note="Clear fit")
    sift.decide(run, "H002", "ta", "exclude", "E1")
    sift.decide(run, "H001", "ft", "maybe")
    sift.note(run, "H002", "ta", "Check the year")
    sift.set_field(run, "H001", "rating", "4")
    sift.set_field(run, "H001", "notes", "A good hedge")
    sift.set_field(run, "H003", "participants", "12")
    sift.column(run, "add", name="Setting", kind="text")
    sift.set_field(run, "H003", "col_setting", "farm")
    sift.save_view(run, "table")
    sift.export(run)
    old_log = (run / sift.LOG_NAME).read_bytes()
    begun_before = ss.begun(run)
    kept_files = {n: (run / n).read_bytes() for n in (sift.REASONS_NAME, sift.SETTINGS_NAME, ss.RUN_FILE, sift.SEARCHES_NAME)}
    rows_before = list(csv.DictReader(io.StringIO((run / sift.CSV_NAME).read_text(encoding="utf-8"), newline="")))
    sift_said = {}
    with locks.held(sift.lock_path(run)):
        before = tree(run)
        try:
            sift.reset(run, wait=0.2)
            sift_said["busy"] = "reset"
        except WorkbookError as exc:
            sift_said["busy"] = str(exc) if tree(run) == before else "written: " + str(exc)
    before = tree(run)
    no_yes = cli.run(["sift", str(run), "reset"])
    dry = cli.run(["sift", str(run), "reset", "--dry-run", "--json"])
    check("109: the command line refuses a reset without --yes in one line, and its dry run and a reset while another "
          "writer holds the lock write nothing",
          no_yes[0] == 1 and no_yes[2].strip() == sift_cli.NO_YES and dry[0] == 0 and tree(run) == before
          and json.loads(dry[1])["decisions"] == 3 and json.loads(dry[1])["notes"] == 2
          and sift_said["busy"] == locks.BUSY and "reset" in sift_cli.SIFT_ACTS, no_yes[2] + dry[2])
    done = cli.run(["sift", str(run), "reset", "--yes", "--json"])
    got = json.loads(done[1]) if done[0] == 0 else {}
    archive = sorted((run / sift.ARCHIVE_DIR).iterdir()) if (run / sift.ARCHIVE_DIR).is_dir() else []
    rows_after = list(csv.DictReader(io.StringIO((run / sift.CSV_NAME).read_text(encoding="utf-8"), newline="")))
    check("109: Start again moves the log whole into _Archive as screening.log (<date-time>).jsonl, byte for byte",
          done[0] == 0 and len(archive) == 1 and archive[0].read_bytes() == old_log
          and re.fullmatch(r"screening\.log \(\d{4}-\d{2}-\d{2} \d{2}\.\d{2}\.\d{2}\)\.jsonl", archive[0].name) is not None
          and got["archive"] == f"{sift.ARCHIVE_DIR}/{archive[0].name}" and not (run / sift.LOG_NAME).exists()
          and got["decisions"] == 3 and got["notes"] == 2, done[2] or str(archive))
    cleared = ["decision", "reason", "ft_decision", "ft_reason", "participants", "participants_confirmed", "rating",
               "notes", "col_setting", "ai_proposed_decision", "ai_proposed_reason", "ai_grounds"]
    check("109: it clears the decisions at both stages, his own fields and columns, and Sift's own proposals",
          all(c in rows_before[0] for c in cleared) and any(r[c] for r in rows_before for c in cleared)
          and all(r[c] == "" for r in rows_after for c in cleared if c in r)
          and [list(r) for r in rows_after] == [list(r) for r in rows_before], str(rows_after[0]))
    keep = ("rec_id", "title", "abstract", "proposed_decision", "proposed_reason", "grounds")
    after_counts = sift.counts(sift.load(run))
    check("109: it leaves the record's own columns, the review's proposals, reasons.csv, sift.json, log.csv and run.json "
          "as they were, and the counts and prisma.md read afresh",
          [[r[c] for c in keep] for r in rows_after] == [[r[c] for c in keep] for r in rows_before]
          and all((run / n).read_bytes() == b for n, b in kept_files.items())
          and after_counts["stages"]["ta"]["decided"] == 0 and sift.counts(sift.load(run))["stages"]["ft"]["records"] == 0
          and (run / sift.PRISMA_NAME).read_text(encoding="utf-8") == sift.prisma_markdown(sift.prisma_source(after_counts))
          and (run / sift.COUNTS_NAME).read_text(encoding="utf-8") == sift.counts_csv(after_counts))
    (run / sift.PDF_DIR).mkdir()
    (run / sift.PDF_DIR / "H001.pdf").write_bytes(b"%PDF-1.4 invented\n")
    with_pdf = ss.begun(run)
    (run / sift.PDF_DIR / "H001.pdf").unlink()
    (run / sift.PDF_DIR).rmdir()
    carried = hedge / "runs" / "2026-08-01"
    shutil.copytree(run, carried, ignore=shutil.ignore_patterns(sift.ARCHIVE_DIR))
    (carried / ss.RUN_FILE).write_text(json.dumps({"version": 1, "carried": {"log": 2, "pdfs": {}, "csv": "invented"}}),
                                       encoding="utf-8")
    (carried / sift.LOG_NAME).write_text('{"n": 1, "act": "follow"}\n{"n": 2, "act": "carry"}\n', encoding="utf-8")
    carried_before = ss.begun(carried)
    sift.reset(carried)
    check("109: afterwards the run is no longer begun, so a rerun that day can rebuild it, a run that followed another "
          "too, while a PDF still holds it",
          bool(begun_before) and ss.begun(run) == "" and with_pdf == "PDFs" and bool(carried_before)
          and ss.begun(carried) == "", f"{begun_before} / {with_pdf} / {carried_before} / {ss.begun(carried)}")
    try:
        server_mod.STATE_MEMORY = {"recent": []}
        sift_routes.api_sift_review({"op": "open", "folder": str(hedge)})
        sift.decide(run, "H003", "ta", "maybe", note="Gates")
        asked = sift_routes.api_sift({"op": "reset", "folder": str(run), "dry_run": True})
        still = (run / sift.LOG_NAME).read_bytes()
        reset_done = sift_routes.api_sift({"op": "reset", "folder": str(run)})
        after_read = sift_routes.api_sift({"op": "read", "folder": str(run)})
    finally:
        server_mod.STATE_MEMORY = kept[3]
    check("109: through the route the dry run says what it clears and writes nothing, and the reset leaves the screen "
          "with nothing to undo and every record undecided",
          asked["decisions"] == 1 and asked["notes"] == 1 and asked["dry_run"] is True and still
          and reset_done["archive"].startswith(f"{sift.ARCHIVE_DIR}/screening.log (") and after_read["undo"] is None
          and after_read["counts"]["stages"]["ta"]["undecided"] == 3 and len(sorted((run / sift.ARCHIVE_DIR).iterdir())) == 2,
          str(asked))
    side = page.split('<aside class="sf-side" id="sf-side"', 1)[1].split("</aside>", 1)[0]
    reset_js = whole(sjs, "sfReset").replace("function sfReset(", "async function sfReset(", 1)
    check("109: Start again stands quiet under the PRISMA flow, outside the AI switch, asks once with what it clears and "
          "the copy kept, then starts again and reads the screening afresh",
          '<button type="button" class="quiet" id="sf-reset">Start again</button>' in side and "sf-settings" not in side
          and "op: 'reset', folder: SF.folder, dry_run: true" in reset_js and "sfAsk('Start again', line, 'Start again')" in reset_js
          and "'sift.reset.line'" in reset_js and reset_js.index("sfAsk(") < reset_js.index("{ op: 'reset', folder: SF.folder })")
          and "await sfRound(null);" in reset_js and "$('sf-reset').onclick = sfReset;" in sjs
          and not re.search(r"\bai\b|AI|sparkle", reset_js) and set(re.findall(r"api\('(/api/[a-z-]+)'", reset_js)) == {"/api/sift"}
          and set(re.findall(r"api\('(/api/[a-z-]+)'", sjs)) == {"/api/sift", "/api/zotero"})
    check("109: no MCP tool resets, and the server's instructions say so",
          not any(t["command"] == ("sift", "reset") or "reset" in t["name"] for t in mcp_server.TOOLS)
          and "No tool resets a screening." in mcp_server.instructions("sift"))

    # ── the folder dialog one at a time (feedback 241: slow to come up, clicked again, Finder windows stacked)
    ran = []
    real_run = server_mod.subprocess.run
    server_mod.subprocess.run = lambda *a, **k: ran.append(a) or subprocess.CompletedProcess(a, 0, "", "")
    try:
        held = server_mod.PICKING.acquire(blocking=False)
        busy = server_mod.pick_folder("A prompt")
        server_mod.PICKING.release()
        free = server_mod.pick_folder("A prompt")
    finally:
        server_mod.subprocess.run = real_run
    check("109: a second folder dialog asked while one is open opens none and answers as a Cancel, and the lock "
          "is let go after", held and busy is None and len(ran) == 1 and free is None
          and server_mod.PICKING.acquire(blocking=False) and (server_mod.PICKING.release() or True))
    check("109: Add project, New project's Choose and the review card's Choose each ask the dialog through picking(), "
          "and the pointer shows it on its way",
          "async function picking(ask, btn, says = '', files = false) {" in app and "if (PICKING) return { chosen: false };" in app
          and "picking((chosen) => api('/api/projects', { op: 'add', path: chosen }), btn, PICK_SAYS.project)" in app
          and "picking((chosen) => api('/api/new-project', { op: 'folder', path: chosen }), $('np-choose'), PICK_SAYS.newProject)" in app
          and "picking((chosen) => api(rvRoute(RVC.part), { op: 'folder', mode: RVC.mode, path: chosen }), $('rv-choose')," in app
          and "const rvRoute = (part) => FAMILY_APPS[part].route;" in app and "route: '/api/sift-review'" in sset
          and "if (btn) { btn.textContent = t('shell.pick.wait'); btn.disabled = true; }" in app
          and "body.picking, body.picking button { cursor: progress; }" in support.text("family/static/style.css", "apps/idiograph/static/distil.css"))
