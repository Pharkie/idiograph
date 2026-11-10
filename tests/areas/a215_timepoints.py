from __future__ import annotations

import base64
import json
import shutil
from pathlib import Path

from workbook import WorkbookError

from .support import check
from . import support
import idiograph_routes

# Every word invented: Kit asks newcomers to an allotment about their first year on it, before the
# season, at midsummer and after the harvest.
T1_TEXT = ("Kit: [00:00:03] What did you expect of the plot?\nWren: [00:00:08] Tidy rows, like the seed packets.\n"
           "Kit: [00:00:40] And the shed?\nWren: [00:00:44] I had not looked inside it yet.\n")
T2_TEXT = ("Kit: [00:00:02] How is it now?\nWren: [00:00:06] I ask the neighbours before I read the packet.\n"
           "Kit: [00:00:30] Why them?\nWren: [00:00:33] They know this soil.\n")
T3_TEXT = ("Kit: [00:00:05] And after the harvest?\nWren: [00:00:09] Too many courgettes, and a box for everyone.\n")
TANSY_TEXT = ("Kit: [00:00:04] What brought you here?\nTansy: [00:00:09] A doctor said to get outside more.\n")
TANSY_T2 = ("Kit: [00:00:03] Is it helping?\nTansy: [00:00:07] I sleep after a day of digging.\n")
THREE = [{"label": "T1", "description": "Before the season"}, {"label": "T2", "description": "Midsummer"},
         {"label": "T3", "description": "After the harvest"}]


def test_timepoints(scratch):
    print("\n215. Timepoints for a longitudinal study (Farr and Nizza 2019, 20 October): the project's number of "
          "timepoints set and refused, an interview added at T2 onto the same participant, where each timepoint "
          "stands, Statements complete per timepoint, a project of one exactly as before, and the API")
    import cli
    import rounds as rounds_mod
    import server as server_mod

    b64 = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")
    base = scratch / "a215"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    cfg_file = scratch / "a215-config.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "Kit"}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)

    def tree(at: Path) -> dict:
        return {p.relative_to(at).as_posix(): (p.read_bytes() if p.is_file() and p.suffix != ".lock" else None)
                for p in sorted(at.rglob("*"))}

    def row(name, text, who, interview, **more):
        return dict({"name": name, "data": b64(text), "pseudonym": who, "interview": interview,
                     "speakers": {"Kit": "interviewer", who: "participant"}}, **more)

    def card_of(case_label, project=None):
        listing = idiograph_routes.api_cases({})
        for section in listing["projects"]:
            if project is not None and section["id"] != project:
                continue
            for p in section["participants"]:
                if p["case"] == case_label:
                    return p
        return None

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "a215-state.json", {"recent": []}

        # ── A. a project of one timepoint, and every project from before, reads, opens and writes as before
        compost = base / "Compost study"
        compost.mkdir()
        made = idiograph_routes.api_new_project({"op": "make", "folder": str(compost), "name": "Compost study",
                                           "research_question": "How do people take to keeping compost?",
                                           "files": [row("first.txt", T1_TEXT, "Wren", "Interview")]})
        compost_id = made["project"]["id"]
        book = compost / "P1 - Wren" / "P1 Wren - EN & ES.xlsx"
        project_file = compost / server_mod.PROJECT_FILE
        on_disk = json.loads(project_file.read_text(encoding="utf-8"))
        before = tree(compost)
        payload = idiograph_routes.api_open({"path": str(book)})
        card = card_of("P1 - Wren", compost_id)
        read = idiograph_routes.api_project({"root": compost_id})["project"]
        check("215: a project of one timepoint writes nothing new: no timepoints key in its project file, nothing in "
              "the case's progress file, and reading, listing and opening it changes no byte",
              "timepoints" not in on_disk and not rounds_mod.progress_path(book).exists()
              and tree(compost) == before, str(sorted(on_disk)))
        check("215: and answers nothing longitudinal: its one timepoint T1, no timepoints on the card, the open "
              "case's summary or the import card's chooser",
              read["timepoints"] == [{"n": 1, "label": "T1", "description": ""}]
              and card is not None and "timepoints" not in card and "timepoints" not in payload["progress"],
              str(card and sorted(card)))
        idiograph_routes.api_complete({"workbook": str(book), "op": "mark"})
        progress = json.loads(rounds_mod.progress_path(book).read_text(encoding="utf-8"))
        check("215: Statements complete in a project of one is the complete key it always was, and nothing beside it",
              sorted(progress) == ["complete"] and rounds_mod.complete_of(book), str(progress))

        # ── B. Settings, Projects: three timepoints with a label and a description each, a dry run first
        garden = base / "Allotment year"
        garden.mkdir()
        made = idiograph_routes.api_new_project({"op": "make", "folder": str(garden), "name": "Allotment year",
                                           "research_question": "How do newcomers make sense of a first year on a plot?",
                                           "files": [row("before.txt", T1_TEXT, "Wren", "Before"),
                                                     row("tansy.txt", TANSY_TEXT, "Tansy", "Before")]})
        root_id = made["project"]["id"]
        gfile = garden / server_mod.PROJECT_FILE
        held = gfile.read_bytes()
        dry = idiograph_routes.api_project({"root": root_id, "timepoints": THREE, "dry_run": True})
        check("215: a dry run says what would change and writes nothing",
              gfile.read_bytes() == held and dry["dry_run"] is True and dry["changes"][0] == "Timepoints from 1 to 3."
              and [t["label"] for t in dry["project"]["timepoints"]] == ["T1", "T2", "T3"], str(dry["changes"]))
        saved = idiograph_routes.api_project({"root": root_id, "timepoints": THREE})
        data = json.loads(gfile.read_text(encoding="utf-8"))
        check("215: three timepoints are saved in the project file, each its label and description, every other key "
              "kept",
              data.get("timepoints") == THREE and data.get("name") == "Allotment year"
              and [t["description"] for t in saved["project"]["timepoints"]] == ["Before the season", "Midsummer",
                                                                                   "After the harvest"], str(data))
        try:
            idiograph_routes.api_project({"root": root_id, "timepoints": [{"label": "T1"}, {"label": "t1"}]})
            twice = "saved"
        except WorkbookError as exc:
            twice = str(exc)
        check("215: two timepoints with one label are refused, nothing saved",
              "both labelled" in twice and json.loads(gfile.read_text(encoding="utf-8")) == data, twice)
        one = idiograph_routes.api_project({"root": root_id, "timepoints": 1})
        check("215: back to one timepoint, with no interview beyond T1, takes the key away and the file is as it was",
              json.loads(gfile.read_text(encoding="utf-8")) == {k: v for k, v in data.items() if k != "timepoints"}
              and len(one["project"]["timepoints"]) == 1, gfile.read_text(encoding="utf-8")[:200])
        idiograph_routes.api_project({"root": root_id, "timepoints": THREE})
        idiograph_routes.api_project({"root": root_id, "agents": True})

        # ── C. an interview added at T2, months later, onto the same participant, through Add transcripts
        wren_book = garden / "P1 - Wren" / "P1 Wren - EN & ES.xlsx"
        asked = idiograph_routes.api_add_transcripts({"op": "project", "root": root_id})
        wren = next(c for c in asked["cases"] if c["pseudonym"] == "Wren")
        check("215: Add transcripts answers the project's timepoints, and the ones each participant has an interview at",
              [t["label"] for t in asked.get("timepoints") or []] == ["T1", "T2", "T3"] and wren.get("held") == [1],
              str(asked))
        added = idiograph_routes.api_add_transcripts({"op": "add", "root": root_id, "files": [
            row("midsummer.txt", T2_TEXT, "Wren", "Midsummer", timepoint=2)]})
        sheets = idiograph_routes.read_sheets(wren_book)[1]
        tags = rounds_mod.sheet_timepoints(rounds_mod.read_raw(wren_book))
        check("215: the T2 interview joins Wren's one workbook as a sheet at the end, placed at T2 in the progress file, "
              "no second participant made",
              added["joined"] == ["P1 - Wren"] and added["cases"] == [] and sheets == ["Before", "Midsummer"]
              and tags == {"Midsummer": 2}
              and sorted(p.name for p in garden.iterdir() if p.is_dir()) == ["P1 - Wren", "P2 - Tansy"], str(tags))
        try:
            idiograph_routes.api_add_transcripts({"op": "add", "root": root_id, "files": [
                row("late.txt", T3_TEXT, "Tansy", "Late", timepoint=4)]})
            fourth = "added"
        except WorkbookError as exc:
            fourth = str(exc)
        check("215: a timepoint the project has not got is refused", "no timepoint 4" in fourth, fourth)

        # ── D. where each participant's timepoints stand, on the home screen's card
        card = card_of("P1 - Wren", root_id)
        tps = (card or {}).get("timepoints") or []
        check("215: Wren's card has her three timepoints, T1 and T2 under way with their counts, T3 not interviewed",
              [t["state"] for t in tps] == ["progress", "progress", "none"]
              and [t["total"] for t in tps] == [2, 2, 0] and [t["sheets"] for t in tps] == [["Before"], ["Midsummer"], []]
              and tps[1]["description"] == "Midsummer", str(tps))
        tansy = (card_of("P2 - Tansy", root_id) or {}).get("timepoints") or []
        check("215: Tansy, interviewed at T1 alone, shows T2 and T3 not interviewed",
              [t["state"] for t in tansy] == ["progress", "none", "none"], str(tansy))

        # ── E. the import card's Timepoint chooser, a T3 transcript dropped into Wren's Source folder
        source = garden / "P1 - Wren" / "Source"
        (source / "harvest.txt").write_text(T3_TEXT, encoding="utf-8")
        seen = idiograph_routes.api_import({"path": str(source / "harvest.txt"), "op": "read", "timepoint": 3})
        check("215: the import card lists the timepoints, those Wren has an interview at marked, and says it joins her "
              "workbook as the sheet T3",
              [(t["label"], t["held"]) for t in seen["timepoints"]] == [("T1", True), ("T2", True), ("T3", False)]
              and seen["joins"].endswith("P1 Wren - EN & ES.xlsx") and seen["sheet"] == "T3" and not seen["said"],
              str({k: seen.get(k) for k in ("joins", "sheet", "said")}))
        madeit = idiograph_routes.api_import({"path": str(source / "harvest.txt"), "op": "make", "timepoint": 3})
        tags = rounds_mod.sheet_timepoints(rounds_mod.read_raw(wren_book))
        archive = list((garden / "P1 - Wren" / "_Archive").glob("*.xlsx"))
        check("215: Make adds the T3 transcript as a sheet at the end of Wren's workbook, at T3, a copy kept in _Archive",
              madeit.get("joined") and madeit.get("sheet") == "T3"
              and idiograph_routes.read_sheets(wren_book)[1] == ["Before", "Midsummer", "T3"]
              and tags == {"Midsummer": 2, "T3": 3} and len(archive) >= 2, str(tags))
        (compost / "P1 - Wren" / "Source" / "second.txt").write_text(T2_TEXT, encoding="utf-8")
        compost_seen = idiograph_routes.api_import({"path": str(compost / "P1 - Wren" / "Source" / "second.txt"), "op": "read"})
        check("215: in a project of one timepoint the import card has no chooser and joins nothing",
              compost_seen["timepoints"] == [] and compost_seen["joins"] == "" and compost_seen["sheet"] == "Transcript",
              str(compost_seen and compost_seen.get("timepoints")))

        # ── F. Statements complete per timepoint
        idiograph_routes.api_complete({"workbook": str(wren_book), "op": "mark", "timepoint": 2})
        raw = rounds_mod.read_raw(wren_book)
        payload = idiograph_routes.api_open({"path": str(wren_book)})
        summary = payload["progress"]["timepoints"]
        check("215: Statements complete at T2 marks T2 alone, kept by its place, T1's mark untouched",
              "2" in (raw.get("complete_timepoints") or {}) and "complete" not in raw
              and [t["state"] for t in summary] == ["progress", "complete", "progress"]
              and summary[1]["complete"] and not summary[0]["complete"], str(raw.get("complete_timepoints")))
        card = card_of("P1 - Wren", root_id)
        check("215: the card says T2's statements are complete", [t["state"] for t in card["timepoints"]][1] == "complete",
              str(card["timepoints"]))
        idiograph_routes.api_complete({"workbook": str(wren_book), "op": "mark", "timepoint": "T1"})
        idiograph_routes.api_complete({"workbook": str(wren_book), "op": "reopen", "timepoint": 2})
        raw = rounds_mod.read_raw(wren_book)
        check("215: T1 by its label is the complete key, and reopening T2 takes its mark away and nothing else",
              rounds_mod.complete_at(raw) and "complete_timepoints" not in raw and raw.get("timepoints") == tags,
              str(sorted(raw)))

        # ── G. lowering the number while a timepoint holds an interview is refused, naming the participant
        held = gfile.read_bytes()
        refusals = []
        for dry_run in (True, False):
            try:
                idiograph_routes.api_project({"root": root_id, "timepoints": THREE[:2], "dry_run": dry_run})
                refusals.append("saved")
            except WorkbookError as exc:
                refusals.append(str(exc))
        check("215: two timepoints while T3 holds Wren's interview are refused, dry run or not, naming her, nothing saved",
              all("T3" in r and "Wren" in r and "Tansy" not in r for r in refusals) and gfile.read_bytes() == held,
              str(refusals))

        # ── H. the API for agents: timepoints read and set, cases with each participant's, import --timepoint
        args = ["--root", str(garden), "--config", str(cfg_file)]
        code, said, err = cli.run(args + ["timepoints", "--json"])
        got = support.plain(json.loads(said)) if code == 0 else {}
        check("215: the command line's timepoints reads the project's three", code == 0
              and [t["label"] for t in got.get("timepoints") or []] == ["T1", "T2", "T3"], said[:200] + err[:200])
        spec = scratch / "a215-two.json"
        spec.write_text(json.dumps(THREE[:2]), encoding="utf-8")
        code, said, err = cli.run(args + ["timepoints", "--from", str(spec), "--dry-run"])
        check("215: and refuses the same lowering, naming Wren, with nothing written",
              code != 0 and "Wren" in (said + err) and gfile.read_bytes() == held, (said + err)[:300])
        renamed = [dict(THREE[0], description="Before the first dig"), THREE[1], THREE[2]]
        spec.write_text(json.dumps(renamed), encoding="utf-8")
        code, said, err = cli.run(args + ["timepoints", "--from", str(spec), "--note", "his words: rename T1", "--json"])
        check("215: a new description set through the command line lands in the project file",
              code == 0 and json.loads(gfile.read_text(encoding="utf-8"))["timepoints"][0]["description"] == "Before the first dig",
              (said + err)[:300])
        code, said, err = cli.run(args + ["cases", "--json"])
        rows = {r["case"]: r for r in (support.plain(json.loads(said))["cases"] if code == 0 else [])}
        check("215: cases answers each participant's timepoints and where each stands",
              [t["state"] for t in rows.get("P1 - Wren", {}).get("timepoints", [])] == ["complete", "progress", "progress"]
              and [t["state"] for t in rows.get("P2 - Tansy", {}).get("timepoints", [])] == ["progress", "none", "none"],
              said[:300] + err[:200])
        tansy_source = garden / "P2 - Tansy" / "Source"
        (tansy_source / "summer.txt").write_text(TANSY_T2, encoding="utf-8")
        code, said, err = cli.run(args + ["import", str(tansy_source / "summer.txt"), "--timepoint", "T2",
                                          "--speakers", "Kit=Interviewer,Tansy=Participant", "--note", "his T2 for Tansy"])
        tansy_book = garden / "P2 - Tansy" / "P2 Tansy - EN & ES.xlsx"
        check("215: import --timepoint T2 adds Tansy's midsummer interview to her workbook at T2",
              code == 0 and idiograph_routes.read_sheets(tansy_book)[1] == ["Before", "T2"]
              and rounds_mod.sheet_timepoints(rounds_mod.read_raw(tansy_book)) == {"T2": 2}, (said + err)[:300])
        import mcp_server
        project = {"root": str(garden), "demo": False, "config": str(cfg_file), "project": None}
        read_args = mcp_server.arguments(mcp_server.BY_NAME["timepoints"], {}, project, "Claude Code")
        set_args = mcp_server.arguments(mcp_server.BY_NAME["timepoints_set"], {
            "timepoints": THREE[:2], "request": "his words", "dry_run": True}, project, "Claude Code")
        read_got, _ = cli.perform(read_args)
        try:
            cli.perform(set_args)
            set_said = "allowed"
        except cli.Refused as exc:
            set_said = str(exc)
        check("215: the MCP's timepoints reads them and timepoints_set refuses the same lowering, with nothing written",
              len(read_got["timepoints"]) == 3 and "Wren" in set_said and gfile.read_bytes() != b"", set_said[:200])
        code, said, err = cli.run(["--root", str(compost), "--config", str(cfg_file), "timepoints", "--json"])
        check("215: a project of one answers one timepoint and nothing longitudinal, unread by agents until allowed",
              code != 0 or support.plain(json.loads(said)).get("longitudinal") is False, (said + err)[:200])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept
