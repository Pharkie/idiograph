"""Area 375: participants' demographics, set per project (demobuild, 12 November 2026, Adam's option A of
demodraw's proposal, with B's Edit the table). The categories are kept once in the project file under
`demographics`, each a list or free words with its values and their colours, and each participant's values in their
own set under `participants`. One route changes the categories, /api/demographics, which Project settings,
`demographics apply` and MCP's `demographics_apply` all run, and one changes a participant's values,
/api/participant with `values`, which the profile's fields, Edit the table, `participant set --value` and MCP's
`participant_set` all run, each with a dry run and a History record. A value not in a list is refused, nothing
written. Categories renamed, reordered and removed carry or take their values, a removal copying the project file to
_Archive first. Trajectories' old tags move into a Tags category of free words, a dry run first, losslessly, each word
keeping its colour and the colour map LPETs' domains share kept whole. The participants table carries a column for
each category ticked, or In sum the counts, and the PETs' pen portrait line their words. REFI-QDA carries them out
as variables and brings them back in.

The fixtures are invented: a project on taking up rowing after sixty, three made-up participants, Bram, Liesl and
Cato, an interviewer called Nell, and a made-up name for the list of names to replace."""
from __future__ import annotations

import base64
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

from workbook import WorkbookError

from . import support
from .support import check

BRAM = ("Nell: [00:00:03] What brought you to the river?\nBram: [00:00:08] My knees gave up on running, and the "
        "club had a beginners' eight on Saturdays.\n")
LIESL = ("Nell: [00:00:03] How was the first outing?\nLiesl: [00:00:07] Cold, and I caught a crab in the first "
         "minute and laughed so hard the cox stopped us.\n")
CATO = ("Nell: [00:00:03] What does the boat give you?\nCato: [00:00:09] A reason to be up at six, and six people "
        "who notice when I am not.\n")
CATO_T2 = "Nell: [00:00:03] A year on?\nCato: [00:00:06] I steer now, and the new ones look to me at the start.\n"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def test_demographics(scratch):
    print("\n375. Participants' demographics (demobuild): categories set per project, a list or free words, values "
          "per participant by the profile's road and the table's, a fixed list refusing a value outside it, Trajectories' "
          "tags moved into Tags losslessly, the participants table's columns and In sum, and REFI-QDA's variables out "
          "and back in")
    import cli
    import demographics as demo_mod
    import gets_print
    import gets_word
    import mcp_server
    import names as names_mod
    import participants as people_mod
    import project_history as hist_mod
    import server as server_mod
    import trajectories as traj_mod
    import idiograph_routes as routes

    b64 = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")
    base = scratch / "a375"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    cfg_file = scratch / "a375-config.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "Nell", "corpus": "", "gravity_reference": "",
                                    "corpus_exclude": []}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)

    def row(name, text, who, interview, **more):
        return dict({"name": name, "data": b64(text), "pseudonym": who, "interview": interview,
                     "speakers": {"Nell": "interviewer", who: "participant"}}, **more)

    def refused(fn, body: dict) -> str:
        try:
            fn(body)
        except WorkbookError as exc:
            return str(exc)
        return "answered"

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "a375-state.json", {"recent": []}
        river = base / "Rowing late"
        river.mkdir()
        made = routes.api_new_project({"op": "make", "folder": str(river), "name": "Rowing late",
                                       "research_question": "How do people who take up rowing after sixty make sense "
                                                            "of it?",
                                       "files": [row("bram.txt", BRAM, "Bram", "First"),
                                                 row("liesl.txt", LIESL, "Liesl", "First"),
                                                 row("cato.txt", CATO, "Cato", "First")]})
        rid = made["project"]["id"]
        routes.api_project({"root": rid, "agents": True})
        routes.api_participant({"root": rid, "case": "Bram", "label": "Saturday's eight",
                                "portrait": "Sixty-four, a retired surveyor. Came to the river when running stopped."})
        pfile = river / server_mod.PROJECT_FILE
        held_before = json.loads(pfile.read_text(encoding="utf-8"))

        # (a) categories: a dry run writes nothing, then they are saved in the project file, every other key kept,
        # with one History record
        ops = [{"op": "add", "name": "Gender", "kind": "list", "values": ["Female", "Male", "Non-binary"]},
               {"op": "add", "name": "Age range", "kind": "list",
                "values": ["60 to 64", "65 to 69", "70 and over"]},
               {"op": "add", "name": "Nationality", "kind": "words"},
               {"op": "add", "name": "First language", "show": False}]
        before, records = sha(pfile), len(hist_mod.load(river))
        dry = routes.api_demographics({"root": rid, "op": "apply", "ops": ops, "dry_run": True})
        check("375: a dry run of the categories says each change, answers them as they would be and writes nothing",
              dry["dry_run"] is True and sha(pfile) == before and len(hist_mod.load(river)) == records
              and dry["changes"] == ["Gender added, a list: Female, Male, Non-binary.",
                                     "Age range added, a list: 60 to 64, 65 to 69, 70 and over.",
                                     "Nationality added, free words.", "First language added, free words."]
              and [c["name"] for c in dry["demographics"]] == ["Gender", "Age range", "Nationality", "First language"],
              str(dry["changes"]))
        done = routes.api_demographics({"root": rid, "op": "apply", "ops": ops})
        held = json.loads(pfile.read_text(encoding="utf-8"))
        record = hist_mod.load(river)[-1]
        colours = [v["colour"] for c in held["demographics"] for v in c["values"]]
        check("375: saved in the project file under demographics in his order, each value with a colour of its own, "
              "every other key as it was, and one History record",
              [(c["name"], c["kind"], c["show"]) for c in held["demographics"]]
              == [("Gender", "list", True), ("Age range", "list", True), ("Nationality", "words", True),
                  ("First language", "words", False)]
              and len(set(colours)) == len(colours) == 6
              and {k: v for k, v in held.items() if k != "demographics"} == held_before
              and record["op"] == "demographics" and record["changes"] == done["changes"], str(held)[:500])

        # (b) values per participant: the profile's fields and Edit the table both send /api/participant's values
        dry = routes.api_participant({"root": rid, "case": "Bram", "dry_run": True,
                                      "values": {"Gender": "male", "Age range": "60 to 64", "Nationality": "Dutch, British"}})
        check("375: a participant's values in a dry run: a list's value as the list spells it, free words joining "
              "their category, nothing written",
              sha(pfile) == sha(pfile) and dry["dry_run"] is True
              and dry["person"]["values"] == {"Gender": "Male", "Age range": "60 to 64", "Nationality": ["Dutch", "British"]}
              and dry["changes"] == ["Bram's Gender is Male now.", "Bram's Age range is 60 to 64 now.",
                                     "Bram's Nationality is Dutch and British now."]
              and json.loads(pfile.read_text(encoding="utf-8")) == held, str(dry["changes"]))
        for case, values in (("Bram", {"Gender": "Male", "Age range": "60 to 64", "Nationality": "Dutch, British"}),
                             ("Liesl", {"Gender": "Female", "Age range": "70 and over", "Nationality": ["German"],
                                        "First language": ["German"]}),
                             ("Cato", {"Gender": "Male", "Age range": "65 to 69", "Nationality": ["British"],
                                       "First language": ["English"]})):
            done = routes.api_participant({"root": rid, "case": case, "values": values})
        held = json.loads(pfile.read_text(encoding="utf-8"))
        nat = next(c for c in held["demographics"] if c["name"] == "Nationality")
        bram = held["participants"]["P1 - Bram"]
        check("375: saved in each participant's own set by category, Bram's label and pen portrait kept, a list's "
              "value a string and free words a list, each free word in its category once with its colour, and the "
              "rows' answer carries the pills of the categories shown, First language's not",
              bram["values"] == {"Gender": "Male", "Age range": "60 to 64", "Nationality": ["Dutch", "British"]}
              and bram["label"] == "Saturday's eight"
              and [v["word"] for v in nat["values"]] == ["Dutch", "British", "German"]
              and done["person"]["pills"] == [
                  {"category": "Gender", "word": "Male", "colour": held["demographics"][0]["values"][1]["colour"]},
                  {"category": "Age range", "word": "65 to 69", "colour": held["demographics"][1]["values"][1]["colour"]},
                  {"category": "Nationality", "word": "British", "colour": nat["values"][1]["colour"]}],
              str(held["participants"])[:500])

        # (c) refused whole, nothing written: a value not in a list, two for a list, a category the project lacks, a
        # real name in a free word, a name taken, and the demo's
        names_mod.save_at(river, [{"real": ["Hendrika Vos"], "to": "Liesl", "for": "Liesl", "case": False}])
        before = sha(pfile)
        not_in = refused(routes.api_participant, {"root": rid, "case": "Cato", "values": {"Age range": "25 to 34"}})
        two = refused(routes.api_participant, {"root": rid, "case": "Cato", "values": {"Gender": ["Male", "Female"]}})
        lacks = refused(routes.api_participant, {"root": rid, "case": "Cato", "values": {"Height": "Tall"}})
        real = refused(routes.api_participant, {"root": rid, "case": "Liesl", "values": {"Nationality": "Hendrika Vos"}})
        taken = refused(routes.api_demographics, {"root": rid, "ops": [{"op": "add", "name": "gender"}]})
        mixed = refused(routes.api_demographics, {"root": rid, "ops": [
            {"op": "show", "category": "Gender", "show": False}, {"op": "value_colour", "category": "Gender",
                                                                   "value": "Female", "colour": "Mauve"}]})
        demo = refused(routes.api_demographics, {"root": "demo", "ops": [{"op": "add", "name": "Gender"}]})
        check("375: a value not in a list is refused naming the list's values, and two for a list, a category the "
              "project lacks, a name from the list of names to replace (by its entry, never the name), a category's "
              "name taken, a colour not in the palette and the demo's are each refused, nothing written",
              not_in == "Age range has no value 25 to 34. Its values are 60 to 64, 65 to 69 and 70 and over, so "
                        "nothing was changed."
              and "one value for each participant" in two and "There is no category Height" in lacks
              and "entry 1" in real and "Hendrika" not in real and "There is a category Gender already" in taken
              and "Mauve" in mixed and demo == "The demo's project is fixed." and sha(pfile) == before,
              " | ".join([not_in, two, lacks, real, taken, mixed, demo]))

        # (d) renamed, reordered, a kind changed, a pill hidden: the values follow
        done = routes.api_demographics({"root": rid, "ops": [
            {"op": "rename", "category": "Age range", "name": "Age"},
            {"op": "value_rename", "category": "Age", "value": "60 to 64", "to": "60 to 65"},
            {"op": "move", "category": "Nationality", "at": 0},
            {"op": "value_move", "category": "Age", "value": "70 and over", "at": 0},
            {"op": "show", "category": "Gender", "show": False}]})
        held = json.loads(pfile.read_text(encoding="utf-8"))
        two_words = refused(routes.api_demographics, {"root": rid, "ops": [
            {"op": "kind", "category": "Nationality", "kind": "list"}]})
        check("375: a category renamed carries everyone's values, a value renamed is renamed on everyone with it, a "
              "category and a value move to their places, and a list cannot be made of free words while someone has two",
              [c["name"] for c in held["demographics"]] == ["Nationality", "Gender", "Age", "First language"]
              and [v["word"] for v in held["demographics"][2]["values"]] == ["70 and over", "60 to 65", "65 to 69"]
              and held["participants"]["P1 - Bram"]["values"]["Age"] == "60 to 65"
              and held["participants"]["P3 - Cato"]["values"]["Age"] == "65 to 69"
              and held["demographics"][1]["show"] is False
              and "Age's 60 to 64 renamed 60 to 65, on 1 participant." in done["changes"]
              and "Nationality cannot be a list while Bram has more than one word" in two_words,
              str(done["changes"]) + two_words)

        # (e) removed: a value off everyone who had it, a category with its values, the file to _Archive first and
        # the History line naming what went
        done = routes.api_demographics({"root": rid, "ops": [
            {"op": "value_remove", "category": "Nationality", "value": "Dutch"},
            {"op": "remove", "category": "First language"}]})
        held = json.loads(pfile.read_text(encoding="utf-8"))
        archived = [p.name for p in (river / "_Archive").glob("idiograph-project (pre-demographics *.json")]
        record = hist_mod.load(river)[-1]
        check("375: a value removed comes off everyone who had it, a category removed takes its values, the project "
              "file copied to _Archive first, and the History record keeps what went",
              held["participants"]["P1 - Bram"]["values"]["Nationality"] == ["British"]
              and "First language" not in json.dumps(held)
              and archived and record["changes"] == ["Nationality's Dutch removed, from Bram.",
                                                     "First language removed, with Liesl's German and Cato's English."],
              str(record["changes"]) + str(archived))

        # (f) the command line and MCP run the same routes
        def run(*args):
            code, out, err = cli.run(["--root", str(river), "--config", str(cfg_file), *args, "--json"])
            return code, (support.plain(json.loads(out)) if out.strip() else {}), err

        spec = base / "cats.json"
        spec.write_text(json.dumps([{"op": "value_add", "category": "Gender", "value": "Prefers not to say",
                                     "colour": "Slate"}]), encoding="utf-8")
        before = sha(pfile)
        code, dry, err = run("demographics", "apply", "--ops", str(spec), "--dry-run")
        code2, done, err2 = run("demographics", "apply", "--ops", str(spec), "--note", "Add his fourth answer",
                                "--tool", "a375")
        code3, shown, err3 = run("demographics", "show")
        code4, setp, err4 = run("participant", "set", "Liesl", "--value", "Gender=Prefers not to say", "--value",
                                "Nationality=", "--note", "Her own words", "--tool", "a375")
        code5, bad, err5 = run("participant", "set", "Liesl", "--value", "Age=25 to 34", "--note", "x")
        code6, cases, err6 = run("cases")
        liesl_row = next((r for r in cases.get("cases") or [] if r["case"] == "P2 - Liesl"), {})
        check("375: demographics apply's dry run writes nothing, then it saves, demographics show reads the categories "
              "and each participant's values, participant set --value sets and clears them, a value not in the list "
              "is refused, and cases answers each participant's values",
              code == 0 and dry["dry_run"] is True and code2 == 0 and code3 == 0 and code4 == 0 and code6 == 0
              and code5 != 0 and "Age has no value 25 to 34" in (err5 or "") + json.dumps(bad)
              and [v["word"] for v in shown["demographics"][1]["values"]][-1] == "Prefers not to say"
              and shown["demographics"][1]["values"][-1]["colour"] == demo_mod.COLOURS.index("Slate")
              and setp["participant"]["values"] == {"Gender": "Prefers not to say", "Age": "70 and over"}
              and liesl_row.get("values") == {"Gender": "Prefers not to say", "Age": "70 and over"}
              and hist_mod.load(river)[-1]["tool"] == "a375",
              (err or "") + (err2 or "") + (err3 or "") + (err4 or "") + (err6 or "") + str(setp)[:300])
        srv = mcp_server.Server(str(river), config=str(cfg_file))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))

        def tool(name, **given):
            return srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                           "params": {"name": name, "arguments": given}}))["result"]
        res = tool("participant_set", case="Liesl", values={"Nationality": ["German", "Austrian"]},
                   request="Liesl holds two passports")
        res2 = tool("demographics_apply", operations=[{"op": "value_colour", "category": "Nationality", "value": "Austrian",
                                                       "colour": "Teal"}], request="Austrian in teal")
        got = support.plain(tool("demographics_show").get("structuredContent") or {})
        check("375: MCP's participant_set takes values and demographics_apply the categories' operations, and "
              "demographics_show reads them",
              not res["isError"] and not res2["isError"]
              and next(p for p in got["participants"] if p["who"] == "Liesl")["values"]["Nationality"] == ["German", "Austrian"]
              and next(v for v in got["demographics"][0]["values"] if v["word"] == "Austrian")["colour"] == 5,
              json.dumps(support.plain(res.get("structuredContent") or {}))[:300])

        # (g) the participants table: a column for each category ticked after the label, the pen portrait on a
        # line of its own, or In sum the counts, and the PETs' pen portrait line, as the print card and the
        # project's choices say
        routes.api_demographics({"root": rid, "ops": [{"op": "export", "category": "Gender", "export": True}]})
        people = routes.people_printed(river, {"participants": True})
        table = people_mod.table_of(people, ["P1 - Bram", "P2 - Liesl", "P3 - Cato"])
        page = gets_print.people_section(table)
        check("375: one row each: a column for each category ticked, Gender ticked though it shows no pill, the pen "
              "portrait on a line of its own under the row, in the print view's page too",
              table["columns"] is True and table["heads"] == ["Number", "Pseudonym", "Label", "Nationality", "Gender", "Age"]
              and table["rows"][0]["values"] == ["British", "Male", "60 to 65"]
              and table["rows"][1]["values"] == ["German, Austrian", "Prefers not to say", "70 and over"]
              and "<th>Nationality</th><th>Gender</th><th>Age</th>" in page and 'class="pt-line"' in page
              and "Sixty-four, a retired surveyor" in page, str(table)[:500])
        routes.api_demographics({"root": rid, "ops": [{"op": "table", "how": "sum"},
                                                      {"op": "export", "category": "Nationality", "export": False}]})
        people = routes.people_printed(river, {"participants": True})
        table = people_mod.table_of(people, ["P1 - Bram", "P2 - Liesl", "P3 - Cato"])
        blocks = gets_word.people_blocks(table)
        check("375: In sum: the participants table as before, then each category ticked with its values counted, "
              "Nationality unticked left out, in the Word document too",
              table["columns"] is False and table["rows"][0].get("values") == []
              and table["sums"] == [{"name": "Gender", "counts": "Male (2), Prefers not to say (1)"},
                                    {"name": "Age", "counts": "70 and over (1), 60 to 65 (1), 65 to 69 (1)"}]
              and any(b.get("rows") == [["Gender", "Male (2), Prefers not to say (1)"],
                                         ["Age", "70 and over (1), 60 to 65 (1), 65 to 69 (1)"]] for b in blocks),
              str(table["sums"]) + str(blocks)[:300])
        bram_book = next(river.glob("P1 - Bram/*.xlsx"))
        who = routes.portrait_printed(bram_book, {"portrait": True})
        check("375: the PETs' Pen portrait tick puts the categories ticked on a line under the label",
              who.get("values") == "Male, 60 to 65" and who.get("label") == "Saturday's eight", str(who))

        # (h) Trajectories' tags from before move into a Tags category of free words: read merged and nothing
        # written, a dry run listing them, then moved losslessly with their colours, the colour map kept whole
        routes.api_project({"root": rid, "timepoints": [{"label": "T1", "description": "First season"},
                                                        {"label": "T2", "description": "A year on"}]})
        routes.api_add_transcripts({"op": "add", "root": rid, "files": [
            row("cato-later.txt", CATO_T2, "Cato", "Later", timepoint=2)]})
        tfile = river / traj_mod.FILE
        traj_mod.write(river, {"schema": 1, "created": "2026-11-01T10:00:00+00:00", "updated": "2026-11-01T10:00:00+00:00",
                               "columns": [{"id": "c1", "title": "Settled", "order": ["P3 - Cato"]}],
                               "placed": {"P1 - Bram": {"column": None, "note": "", "tags": ["Novice", "Coxless"]},
                                          "P3 - Cato": {"column": "c1", "note": "Steers the novices now",
                                                        "tags": ["novice", "Steers"]}},
                               "tags": {"Novice": 7, "Coxless": 9, "Steers": 3, "Practical": 1}, "history": []})
        t_before, p_before = sha(tfile), sha(pfile)
        shown = routes.api_demographics({"root": rid, "op": "show"})
        tags_cat = next((c for c in shown["demographics"] if c["name"] == "Tags"), {})
        dry = routes.api_demographics({"root": rid, "op": "move_tags", "dry_run": True})
        check("375: before the move every read shows Trajectories' tags as a Tags category with their colours, the move "
              "waiting, and a dry run lists whose tags would move, nothing written",
              shown["pending"] is True and [(v["word"], v["colour"]) for v in tags_cat.get("values") or []]
              == [("Novice", 7), ("Coxless", 9), ("Steers", 3)]
              and dry["changes"] == ["Bram: Novice, Coxless.", "Cato: novice, Steers.",
                                     "Tags of 2 participants moved from Trajectories to the Tags category."]
              and sha(tfile) == t_before and sha(pfile) == p_before, str(dry["changes"]) + str(tags_cat))
        code, moved, err = run("demographics", "move-tags", "--note", "Move my tags", "--tool", "a375")
        held = json.loads(pfile.read_text(encoding="utf-8"))
        after = json.loads(tfile.read_text(encoding="utf-8"))
        archived = sorted(p.name for p in (river / "_Archive").glob("* (pre-demographics *.json"))
        tags_cat = next(c for c in held["demographics"] if c["name"] == "Tags")
        check("375: moved: each participant's tags their values in Tags, each word keeping its colour, Tags shown as a "
              "pill, the tags gone from placed with everything else there kept, the colour map LPETs' domains share "
              "kept whole, both files copied to _Archive first, and one History line",
              code == 0 and tags_cat == {"name": "Tags", "kind": "words", "show": True,
                                         "values": [{"word": "Novice", "colour": 7}, {"word": "Coxless", "colour": 9},
                                                    {"word": "Steers", "colour": 3}]}
              and held["participants"]["P1 - Bram"]["values"]["Tags"] == ["Novice", "Coxless"]
              and held["participants"]["P3 - Cato"]["values"]["Tags"] == ["Novice", "Steers"]
              and held["participants"]["P1 - Bram"]["label"] == "Saturday's eight"
              and after["placed"]["P3 - Cato"] == {"column": "c1", "note": "Steers the novices now"}
              and after["tags"] == {"Novice": 7, "Coxless": 9, "Steers": 3, "Practical": 1}
              and any(n.startswith("idiograph-trajectories (pre-demographics") for n in archived)
              and hist_mod.load(river)[-1]["changes"] == ["Tags of 2 participants moved from Trajectories to the Tags "
                                                          "category."],
              (err or "") + str(moved)[:300] + str(archived))
        moved_once = (sha(tfile), sha(pfile))
        routes.api_cases({})
        cato_book = next(river.glob("P3 - Cato/*.xlsx"))
        board = routes.api_trajectories({"workbook": str(cato_book)})
        cards = {c["case"]: c for c in board["participants"]}
        check("375: once moved, the project page's listing writes nothing, and Trajectories shows each participant's "
              "pills of the categories shown in place of its tags, its tags read from Tags",
              (sha(tfile), sha(pfile)) == moved_once
              and [(p["category"], p["word"]) for p in cards["P1 - Bram"]["pills"]]
              == [("Nationality", "British"), ("Age", "60 to 65"), ("Tags", "Novice"), ("Tags", "Coxless")]
              and cards["P3 - Cato"]["tags"] == [{"word": "Novice", "colour": 7}, {"word": "Steers", "colour": 3}],
              str(cards["P1 - Bram"].get("pills")))
        done = routes.api_trajectories_ops({"workbook": str(cato_book), "ops": [
            {"op": "tags", "participant": "Liesl", "tags": ["Coxless", "Masters"]},
            {"op": "tag_colour", "tag": "COXLESS", "colour": "Olive"}]})
        held = json.loads(pfile.read_text(encoding="utf-8"))
        tags_cat = next(c for c in held["demographics"] if c["name"] == "Tags")
        check("375: Trajectories' tags and tag_colour ops still work, as a participant's values in Tags and a value's "
              "colour, the board's file keeping no tags",
              held["participants"]["P2 - Liesl"]["values"]["Tags"] == ["Coxless", "Masters"]
              and next(v for v in tags_cat["values"] if v["word"] == "Coxless")["colour"] == 1
              and "tags" not in json.dumps(json.loads(tfile.read_text(encoding="utf-8"))["placed"])
              and done["changes"] == ["Liesl's Tags is Coxless and Masters now.", "Tags' Coxless is Olive now."],
              str(done["changes"]))
        done = routes.api_demographics({"root": rid, "ops": [
            {"op": "add", "name": "Experience", "kind": "list", "values": ["Novice", "Rowed before"]},
            {"op": "value_to", "category": "Tags", "value": "Novice", "to": "Experience"}]})
        held = json.loads(pfile.read_text(encoding="utf-8"))
        check("375: Move to puts a Tags word and everyone who has it into another category, joining its value there",
              held["participants"]["P1 - Bram"]["values"]["Experience"] == "Novice"
              and held["participants"]["P3 - Cato"]["values"]["Tags"] == ["Steers"]
              and "Novice" not in [v["word"] for v in next(c for c in held["demographics"] if c["name"] == "Tags")["values"]]
              and done["changes"][-1] == "Novice moved from Tags to Experience, with Bram and Cato.", str(done["changes"]))

        # (i) REFI-QDA: the categories go out as variables, each participant's values on their case, and come back in
        # Idiograph's own import with the lists in their order
        copy = base / "Rowing copy"
        copy.mkdir()
        made2 = routes.api_new_project({"op": "make", "folder": str(copy), "name": "Rowing copy",
                                        "files": [row("wynn.txt", BRAM.replace("Bram", "Wynn"), "Wynn", "First")]})
        cfile = copy / server_mod.PROJECT_FILE
        routes.api_project({"root": made2["project"]["id"], "agents": True})
        dest = copy / "Rowing late.qdpx"
        routes.qdpx_export(river, dest, participants=["Bram", "Liesl"])
        with zipfile.ZipFile(dest) as z:
            qde = z.read("project.qde").decode("utf-8")
        bram_xml = qde.split('name="P1 - Bram"', 1)[-1].split("</Case>", 1)[0]
        check("375: Export as REFI-QDA writes a Variables element after the code book, a Text variable for each "
              "category, a list's values in its description, and each participant's values on their case after its "
              "description and before its sources",
              qde.index("<Variables>") > qde.index("<CodeBook>") and qde.index("<Variables>") < qde.index("<Cases>")
              and 'name="Age" typeOfVariable="Text"' in qde
              and "A list, one value for each participant:\n70 and over\n60 to 65\n65 to 69" in qde
              and bram_xml.index("<Description>") < bram_xml.index("<VariableValue>") < bram_xml.index("<SourceRef")
              and "<TextValue>British</TextValue>" in bram_xml and "<TextValue>Male</TextValue>" in bram_xml,
              bram_xml[:600])

        def run2(*args):
            code, out, err = cli.run(["--root", str(copy), "--config", str(cfg_file), *args, "--json"])
            return code, (support.plain(json.loads(out)) if out.strip() else {}), err

        code, dry, err = run2("qdpx", str(dest), "--sources", "1=Bram,2=Liesl", "--dry-run")
        before = sha(cfile)
        code2, done, err2 = run2("qdpx", str(dest), "--sources", "1=Bram,2=Liesl", "--note", "Bring the copy back")
        got = json.loads(cfile.read_text(encoding="utf-8"))
        cats = {c["name"]: c for c in got.get("demographics") or []}
        code3, off, err3 = run2("qdpx", str(dest), "--sources", "1=Bram,2=Liesl", "--no-demographics", "--dry-run")
        check("375: Idiograph's own import of its package lists each category with its kind and who has what in its dry "
              "run, then brings them back, each list's values in their order, free words split, each participant's "
              "values theirs, and --no-demographics leaves them out with the line saying so",
              code == 0 and code2 == 0 and code3 == 0 and made2["project"]["id"]
              and any(l.startswith("Demographics, Age, a list: 60 to 65 for Bram and 70 and over for Liesl")
                      for l in dry["lines"])
              and [v["word"] for v in cats["Age"]["values"]] == ["70 and over", "60 to 65", "65 to 69"]
              and [v["word"] for v in cats["Gender"]["values"]] == ["Female", "Male", "Non-binary", "Prefers not to say"]
              and cats["Nationality"]["kind"] == "words"
              and got["participants"]["P2 - Bram"]["values"]["Gender"] == "Male"
              and got["participants"]["P3 - Liesl"]["values"]["Nationality"] == ["German", "Austrian"]
              and any("2 variables left out" in l or "variables left out" in l for l in off["lines"]),
              (err or "") + (err2 or "") + str(dry.get("lines"))[:600] + str(got.get("participants"))[:300])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept
    pdfs(scratch)


def pdfs(scratch: Path) -> None:
    """The participants table's PDF, through the print card's route, on a copy of the demo given demographics of its
    own: a column for each category after the label and the pen portrait under the row, then In sum's counts."""
    import gets as gets_mod
    import pdftext
    import server as server_mod
    import themes as th_mod
    import idiograph_routes as routes
    from .a373_participant_set import FLAT, demo_copy

    base = scratch / "a375x"
    ipa = demo_copy(support.DEMO_SHIPPED, support.source("demo/idiograph-project.json"), base / "ipa", "Mabel")
    cfg_file = scratch / "a375x-config.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "Kit", "corpus": "", "gravity_reference": "",
                                    "corpus_exclude": []}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, str(ipa)
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "a375x-state.json", {"recent": []}
        # the demo brings Gender, Age range and Lives with (demodemo), so the copy adds a fourth category of its own,
        # and Mabel's values, whose set this copy has taken out, are given again as the demo has them
        routes.api_demographics({"root": str(ipa), "ops": [{"op": "add", "name": "Nationality", "kind": "words"}]})
        for case, values in (("Juno", {"Nationality": "Spanish"}),
                             ("Mabel", {"Gender": "Female", "Age range": "70 and over", "Lives with": "Alone",
                                        "Nationality": "British"}),
                             ("Rowan", {"Nationality": "Irish"})):
            routes.api_participant({"root": str(ipa), "case": case, "values": values})
        current = th_mod.current_version(gets_mod.load(ipa))["id"]
        each = routes.api_gets_boards({"root": str(ipa), "board": current, "op": "pdf", "what": "table",
                                       "participants": True})
        first = FLAT(pdftext.pages_text(Path(each["path"]).read_bytes())[0])
        routes.api_demographics({"root": str(ipa), "ops": [{"op": "table", "how": "sum"}]})
        summed = routes.api_gets_boards({"root": str(ipa), "board": current, "op": "pdf", "what": "table",
                                         "participants": True, "replace": True})
        sum_first = FLAT(pdftext.pages_text(Path(summed["path"]).read_bytes())[0])
        juno = json.loads((ipa / "idiograph-project.json").read_text(encoding="utf-8"))["participants"]["Juno"]
        check("375: the GET table's PDF with Participants table: a column for each category after the label and the pen "
              "portrait on its own line under the row, and In sum the counts in a short table after it",
              all(FLAT(w) in first for w in ("Gender", "Age range", "Lives with", "Nationality", "40 to 49", "Partner", "Spanish",
                                      juno["portrait"]))
              and FLAT("Pen portrait") not in first
              and all(FLAT(w) in sum_first for w in ("Pen portrait", "In sum", "Female (2), Male (1)",
                                                      "30 to 39 (1), 40 to 49 (1), 70 and over (1)")),
              first[:300] + " | " + sum_first[:300])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept
