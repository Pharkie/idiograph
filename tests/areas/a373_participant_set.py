"""Area 373: each participant's picture, label and pen portrait (pbiobuild, 11 November 2026, Adam's layout A of
pbiodraw's proposal). The set is kept once for the project, in its file under `participants`, every other key kept,
and one route changes it, /api/participant, which the app's row, `participant set` and MCP's `participant_set` all
run, with a dry run and a History record. A label or a pen portrait holding a name from the project's list of names
to replace is refused, nothing written, the refusal naming the entry and never the name. His own picture is kept in
`pictures/`, square and small, the one it replaces archived. The page's answers carry each participant's set. And
a Trajectories board from before, its labels and pictures on `placed`, opens with them as before, every read merged
and none writing, until the project page's listing moves them into the participants' own, losslessly, both files
copied to `_Archive/` first.

The fixtures are invented: a project on learning to swim as an adult, two made-up participants, Orla and Piers,
an interviewer called Kit, and a made-up name for the list of names to replace."""
from __future__ import annotations

import base64
import hashlib
import json
import shutil
from pathlib import Path

from workbook import WorkbookError

from . import support
from .support import check

ORLA = ("Kit: [00:00:03] What did the first lesson feel like?\nOrla: [00:00:09] I held the rail the whole hour "
        "and the teacher let me.\nKit: [00:00:40] And now?\nOrla: [00:01:12] Now I float on my back and count the tiles.\n")
PIERS = ("Kit: [00:00:03] Why learn now?\nPiers: [00:00:08] My granddaughter swims and I wanted to be in the water "
         "with her.\n")
PIERS_T2 = "Kit: [00:00:03] A year on?\nPiers: [00:00:06] We race two lengths on a Sunday and she lets me win.\n"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def test_participant_set(scratch):
    print("\n373. Each participant's picture, label and pen portrait (pbiobuild): kept once for the project in its "
          "file, one route for the app, the command line and MCP, a dry run and History, a real name refused, his own "
          "picture kept square, the answers carrying the set, and Trajectories' labels and pictures moved over "
          "losslessly")
    import cli
    import mcp_server
    import names as names_mod
    import participants as people_mod
    import project_history as hist_mod
    import server as server_mod
    import trajectories as traj_mod
    import idiograph_routes as routes

    b64 = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")
    base = scratch / "a373"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    cfg_file = scratch / "a373-config.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "Kit", "corpus": "", "gravity_reference": "",
                                    "corpus_exclude": []}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)

    def row(name, text, who, interview, **more):
        return dict({"name": name, "data": b64(text), "pseudonym": who, "interview": interview,
                     "speakers": {"Kit": "interviewer", who: "participant"}}, **more)

    def refused(body: dict) -> str:
        try:
            routes.api_participant(body)
        except WorkbookError as exc:
            return str(exc)
        return "answered"

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "a373-state.json", {"recent": []}
        pool = base / "Swimming late"
        pool.mkdir()
        made = routes.api_new_project({"op": "make", "folder": str(pool), "name": "Swimming late",
                                       "research_question": "How do adults make sense of learning to swim?",
                                       "files": [row("orla.txt", ORLA, "Orla", "First"),
                                                 row("piers.txt", PIERS, "Piers", "First")]})
        rid = made["project"]["id"]
        routes.api_project({"root": rid, "agents": True})
        pfile = pool / server_mod.PROJECT_FILE
        held_before = json.loads(pfile.read_text(encoding="utf-8"))

        # (a) the route: a dry run writes nothing, a save writes the set and keeps every other key, one History record
        before, records = sha(pfile), len(hist_mod.load(pool))
        dry = routes.api_participant({"root": rid, "case": "Orla", "label": "Holding the rail",
                                      "portrait": "Forty-one, a nurse.\nLearnt with her son's class.",
                                      "picture": "set:face07", "dry_run": True})
        check("373: a dry run says each change, answers the set as it would be and writes nothing",
              dry["dry_run"] is True and sha(pfile) == before and len(hist_mod.load(pool)) == records
              and dry["person"]["label"] == "Holding the rail" and dry["person"]["picture"] == "set:face07"
              and dry["changes"] == ["Orla's label is Holding the rail now.", "Orla's pen portrait written.",
                                     "Orla's picture changed."], str(dry["changes"]))
        done = routes.api_participant({"root": rid, "case": "Orla", "label": "Holding the rail",
                                       "portrait": "Forty-one, a nurse.\nLearnt with her son's class.",
                                       "picture": "set:face07"})
        held = json.loads(pfile.read_text(encoding="utf-8"))
        record = hist_mod.load(pool)[-1]
        check("373: saved in the project file under participants by the participant's label, the portrait's line "
              "breaks folded, every other key as it was, and one record in the project's History",
              held["participants"] == {"P1 - Orla": {"label": "Holding the rail",
                                                     "portrait": "Forty-one, a nurse. Learnt with her son's class.",
                                                     "picture": "set:face07"}}
              and {k: v for k, v in held.items() if k != "participants"} == held_before
              and record["op"] == "participant set" and record["changes"] == done["changes"]
              and done["person"]["picture_url"] == "/faces/face07.svg", str(held)[:400])
        done = routes.api_participant({"root": rid, "case": "P1 - Orla", "label": "Holding the rail"})
        check("373: a save that changes nothing writes no record", done["changes"] == []
              and len(hist_mod.load(pool)) == records + 1, str(done["changes"]))
        done = routes.api_participant({"root": rid, "case": "orla", "portrait": ""})
        check("373: an empty field clears it, the others kept, and a participant goes by their pseudonym in any case",
              json.loads(pfile.read_text(encoding="utf-8"))["participants"]["P1 - Orla"]
              == {"label": "Holding the rail", "picture": "set:face07"}
              and done["changes"] == ["Orla's pen portrait cleared."], str(done["changes"]))

        # (b) refusals, nothing written: a real name from the list, a field over its limit, a face not of the set,
        # a participant not of the project
        names_mod.save_at(pool, [{"real": ["Gwendolyn Marsh"], "to": "Orla", "for": "Orla", "case": False},
                                 {"real": ["Barnaby"], "to": "Piers", "for": "Piers", "case": False}])
        before = sha(pfile)
        said_label = refused({"root": rid, "case": "Piers", "label": "gwendolyn  marsh's friend"})
        said_portrait = refused({"root": rid, "case": "Orla", "label": "Floating now",
                                 "portrait": "Learnt beside Barnaby at the leisure centre."})
        long_label = refused({"root": rid, "case": "Orla", "label": "x" * 61})
        long_portrait = refused({"root": rid, "case": "Orla", "portrait": "y" * 801})
        no_face = refused({"root": rid, "case": "Orla", "picture": "set:face99"})
        nobody = refused({"root": rid, "case": "Quentin", "label": "Nobody"})
        check("373: a label or a pen portrait holding a name from the list of names to replace, whoever its entry is "
              "for, is refused naming the entry by its number and never the name, nothing written",
              said_label == "The label holds a name from the project's list of names to replace, entry 1, so nothing "
                            "was changed."
              and said_portrait.startswith("The pen portrait holds a name") and "entry 2" in said_portrait
              and "Barnaby" not in said_portrait and "Gwendolyn" not in said_label and sha(pfile) == before,
              said_label + " | " + said_portrait)
        check("373: a label over 60 characters, a pen portrait over 800, a face not of the set and a participant not "
              "of the project are each refused, nothing written",
              "60 characters" in long_label and "800 characters" in long_portrait and "face99" in no_face
              and "Quentin is not a participant" in nobody and sha(pfile) == before,
              " | ".join([long_label, long_portrait, no_face, nobody]))

        # (c) his own picture: square and small in pictures/, the source left, the one replaced archived
        w, h = 500, 300
        rgba = bytearray()
        for y in range(h):
            for x in range(w):
                rgba += bytes((x * 255 // w, 120, y * 255 // h, 255))
        png = traj_mod.png_write(w, h, rgba)
        source = base / "piers at the pool.png"
        source.write_bytes(png)
        pics = people_mod.pictures_of(pool)
        done = routes.api_participant({"root": rid, "case": "Piers", "from": str(source)})
        kept_pic = pics / "Piers.png"
        pw, ph, _ = traj_mod.png_read(kept_pic.read_bytes()) if kept_pic.exists() else (0, 0, b"")
        check("373: his own picture is kept in the project's pictures folder, a square of 256 at its middle, the "
              "source left where it was, the page given its address",
              (pw, ph) == (256, 256) and source.read_bytes() == png and done["person"]["picture"] == "Piers.png"
              and done["person"]["picture_url"].startswith("/participant-picture?"), f"{pw}x{ph} {done['person']}")
        small = traj_mod.png_write(2, 2, bytearray(b"\x10\x20\x30\xff" * 4))
        done = routes.api_participant({"root": rid, "case": "Piers",
                                       "data": "data:image/png;base64," + base64.b64encode(small).decode("ascii")})
        check("373: a picture from the page's own Change picture... replaces it, the one before kept in the "
              "pictures' _Archive, never deleted",
              done["person"]["picture"] in ("Piers.png", "Piers-2.png") and (pics / done["person"]["picture"]).is_file()
              and len(list((pics / "_Archive").glob("Piers *.png"))) == 1, str(done["person"]))
        done = routes.api_participant({"root": rid, "case": "Piers", "picture": ""})
        check("373: Remove takes the picture off, its file archived too, the initial standing in",
              done["person"]["picture"] == "" and done["person"]["picture_url"] == ""
              and not list(pics.glob("Piers*.png")) and done["changes"] == ["Piers's picture taken off."],
              str(done["changes"]))

        # (d) the command line and MCP run the same route
        def run(*args):
            code, out, err = cli.run(["--root", str(pool), "--config", str(cfg_file), *args, "--json"])
            return code, (support.plain(json.loads(out)) if out.strip() else {}), err

        before = sha(pfile)
        code, dry, err = run("participant", "set", "Piers", "--label", "Racing on Sundays", "--picture", "set:face12",
                             "--dry-run")
        code2, done, err2 = run("participant", "set", "Piers", "--label", "Racing on Sundays", "--portrait",
                                "Seventy, retired. Learnt for his granddaughter.", "--picture", "set:face12",
                                "--note", "His words for Piers", "--tool", "a373")
        code3, shown, err3 = run("participant", "show", "Piers")
        code4, every, err4 = run("participant", "show")
        code5, cases, err5 = run("cases")
        record = hist_mod.load(pool)[-1]
        piers_row = next((r for r in cases.get("cases") or [] if r["case"] == "P2 - Piers"), {})
        check("373: participant set's dry run writes nothing, then it saves with his request and the tool in History, "
              "participant show reads one or every participant, and cases answers each one's set",
              code == 0 and dry.get("dry_run") is True and code2 == 0 and code3 == 0 and code4 == 0 and code5 == 0
              and shown["participant"] == {"case": "P2 - Piers", "who": "Piers", "label": "Racing on Sundays",
                                           "portrait": "Seventy, retired. Learnt for his granddaughter.",
                                           "picture": "set:face12"}
              and [p["case"] for p in every["participants"]] == ["P1 - Orla", "P2 - Piers"]
              and piers_row.get("label") == "Racing on Sundays" and piers_row.get("picture") == "set:face12"
              and record.get("by") == "agent" and record.get("tool") == "a373"
              and record.get("request") == "His words for Piers",
              (err or "") + (err2 or "") + (err3 or "") + (err4 or "") + (err5 or "") + str(record)[:200])
        code, _out, err = run("participant", "set", "Piers", "--portrait", "Learnt beside Barnaby.", "--note", "x")
        said = (err or "") + json.dumps(_out)
        check("373: the command line refuses a real name as the route does, nothing written",
              code != 0 and "entry 2" in said and "Barnaby" not in said, f"{code} {said[:300]}")
        srv = mcp_server.Server(str(pool), config=str(cfg_file))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))

        def tool(name, **given):
            return srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                           "params": {"name": name, "arguments": given}}))["result"]
        res = tool("participant_set", case="Orla", label="", picture="", request="Clear Orla's label and picture")
        got = tool("participant_show", case="Orla")
        got_set = support.plain(got.get("structuredContent") or {}).get("participant") or {}
        check("373: MCP's participant_set clears with empty strings, and participant_show reads the set",
              not res["isError"] and not got["isError"] and got_set.get("label") == "" and got_set.get("picture") == ""
              and "P1 - Orla" not in (json.loads(pfile.read_text(encoding="utf-8")).get("participants") or {}),
              json.dumps(support.plain(res.get("structuredContent") or {}))[:300])

        # (e) the page's answers carry the set: the project page's rows, the picker, the statements screen (New
        # project put the project in the settings' list)
        home = routes.api_cases({})
        rows = {c["case"]: c.get("person") or {} for c in home["projects"][0]["participants"]}
        piers = pool / "P2 - Piers" / "P2 Piers - EN & ES.xlsx"
        picker = routes.api_participants({"workbook": str(piers)})
        opened = routes.api_open({"path": str(piers)})
        demo_sets = [people_mod.own_of(json.loads(support.source(f).read_text(encoding="utf-8")))
                     for f in ("demo/idiograph-project.json", "demo/ta/idiograph-project.json")]
        check("373: the project page's rows, the participant picker and the statements screen each carry the "
              "participant's set with their colour, and the demo's three carry theirs in both demos",
              rows["P2 - Piers"].get("label") == "Racing on Sundays" and rows["P1 - Orla"].get("label") == ""
              and isinstance(rows["P1 - Orla"].get("colour"), int)
              and {p["case"]: (p.get("person") or {}).get("label") for p in picker["participants"]}
              == {"P1 - Orla": "", "P2 - Piers": "Racing on Sundays"}
              and opened["person"]["portrait"] == "Seventy, retired. Learnt for his granddaughter."
              and all(set(d) == {"Juno", "Mabel", "Rowan"} and all(len(v) == 3 for v in d.values()) for d in demo_sets),
              str([rows, demo_sets])[:400])
        import zipfile
        dest = base / "Swimming late.qdpx"
        routes.qdpx_export(pool, dest)
        with zipfile.ZipFile(dest) as z:
            qde = z.read("project.qde").decode("utf-8")
        case_xml = qde.split("<Cases>", 1)[-1].split('name="P2 - Piers"', 1)[-1].split("</Case>", 1)[0]
        check("373: Export as REFI-QDA gives each participant's pen portrait as their case's description, first in the "
              "case, and no picture",
              "<Description>Seventy, retired. Learnt for his granddaughter.</Description>" in case_xml
              and case_xml.index("<Description>") < case_xml.index("<SourceRef") and "face12" not in qde,
              qde.split("<Cases>", 1)[-1].split("</Cases>", 1)[0][:700])
        demo_said = refused({"root": "demo", "case": "Juno", "label": "Changed"})
        check("373: the demo's are fixed", demo_said == "The demo's project is fixed.", demo_said)

        # (f) a Trajectories board from before keeps its labels and pictures on placed: every read merges them in
        # and writes nothing, and the project page's listing moves them into the participants' own, losslessly
        routes.api_project({"root": rid, "timepoints": [{"label": "T1", "description": "First lessons"},
                                                        {"label": "T2", "description": "A year on"}]})
        routes.api_add_transcripts({"op": "add", "root": rid, "files": [
            row("piers-later.txt", PIERS_T2, "Piers", "Later", timepoint=2)]})
        tpics = traj_mod.pictures_of(pool)
        tpics.mkdir(parents=True)
        (tpics / "Orla.png").write_bytes(small)
        tfile = pool / traj_mod.FILE
        traj_mod.write(pool, {"schema": 1, "created": "2026-11-01T10:00:00+00:00", "updated": "2026-11-01T10:00:00+00:00",
                              "columns": [{"id": "c1", "title": "Settling in", "order": ["P1 - Orla"]}],
                              "placed": {"P1 - Orla": {"column": "c1", "note": "Trusts the rail less each week",
                                                       "title": "The rail holder", "picture": "Orla.png",
                                                       "tags": ["Pool"]},
                                         "P2 - Piers": {"column": None, "note": "", "title": "A Sunday racer",
                                                        "picture": "set:face03"}},
                              "tags": {"Pool": 2}, "history": []})
        t_before, p_before = sha(tfile), sha(pfile)
        board = routes.api_trajectories({"workbook": str(piers)})
        cards = {c["case"]: c for c in board["participants"]}
        shown = routes.api_participant({"root": rid, "case": "Orla", "op": "show"})["person"]
        check("373: an old Trajectories file opens with its labels and pictures, the participant's own label kept over "
              "the board's, every screen reading them merged, and no read writes either file",
              cards["P1 - Orla"]["title"] == "The rail holder" and cards["P1 - Orla"]["picture_url"].startswith("/traj-picture?")
              and cards["P2 - Piers"]["title"] == "Racing on Sundays" and cards["P2 - Piers"]["picture"] == "set:face12"
              and shown["label"] == "The rail holder" and shown["picture"] == "Orla.png"
              and sha(tfile) == t_before and sha(pfile) == p_before, str([cards["P1 - Orla"].get("title"), shown])[:300])
        routes.api_cases({})
        t_after = json.loads(tfile.read_text(encoding="utf-8"))
        sets = json.loads(pfile.read_text(encoding="utf-8"))["participants"]
        archive = sorted(p.name for p in (pool / "_Archive").iterdir()) if (pool / "_Archive").is_dir() else []
        record = hist_mod.load(pool)[-1]
        check("373: the project page's listing moves them over: Orla's label and her picture's file copied into "
              "pictures/ (the original left), Piers's own label kept, the board's labels and pictures gone from "
              "placed with everything else there kept, both files copied to _Archive first, one History line",
              sets["P1 - Orla"] == {"label": "The rail holder", "picture": "Orla.png"}
              and (people_mod.pictures_of(pool) / "Orla.png").read_bytes() == small and (tpics / "Orla.png").is_file()
              and sets["P2 - Piers"]["label"] == "Racing on Sundays" and sets["P2 - Piers"]["picture"] == "set:face12"
              and t_after["placed"]["P1 - Orla"] == {"column": "c1", "note": "Trusts the rail less each week", "tags": ["Pool"]}
              and "title" not in json.dumps(t_after["placed"]) and "picture" not in json.dumps(t_after["placed"])
              and any(n.startswith("idiograph-trajectories (pre-participants ") for n in archive)
              and any(n.startswith("idiograph-project (pre-participants ") for n in archive)
              and record["changes"] == ["Labels and pictures of 2 participants moved from Trajectories to the "
                                        "participants' own."], str([sets, archive, record])[:600])
        moved_once = sha(tfile)
        routes.api_cases({})
        board = routes.api_trajectories({"workbook": str(piers)})
        cards = {c["case"]: c for c in board["participants"]}
        check("373: once moved, a second listing writes nothing, and the board shows the same label and picture, read "
              "from the participant's own",
              sha(tfile) == moved_once and cards["P1 - Orla"]["title"] == "The rail holder"
              and cards["P1 - Orla"]["picture_url"].startswith("/participant-picture?"), str(cards["P1 - Orla"])[:300])
        done = routes.api_trajectories_ops({"workbook": str(piers), "ops": [
            {"op": "title", "participant": "Orla", "title": "Floating now"}, {"op": "picture", "participant": "Orla",
                                                                              "set": "face09"}]})
        sets = json.loads(pfile.read_text(encoding="utf-8"))["participants"]
        check("373: Trajectories' title and picture ops set the participant's own, the board's file keeping neither",
              sets["P1 - Orla"] == {"label": "Floating now", "picture": "set:face09"}
              and "title" not in json.dumps(json.loads(tfile.read_text(encoding="utf-8"))["placed"])
              and done["changes"] == ["Orla's label from The rail holder to Floating now.", "Orla's picture changed."],
              str(done["changes"]))

        # (g) a rename carries the set, its picture's file named after them moving with the folder ticked
        routes.api_participant({"root": rid, "case": "Piers", "data": "data:image/png;base64,"
                                + base64.b64encode(small).decode("ascii")})
        plan = routes.api_rename({"op": "plan", "root": rid, "case": "P2 - Piers", "name": "Rupert", "folder": True})
        routes.api_rename({"op": "rename", "root": rid, "case": "P2 - Piers", "name": "Rupert", "folder": True})
        sets = json.loads(pfile.read_text(encoding="utf-8"))["participants"]
        check("373: a rename carries the set to the new label and, ticked, its picture's file to the new name",
              "Their picture, label and pen portrait in the project" in plan["lines"]
              and "Their picture in the project's pictures folder takes the new name" in plan["folder_lines"]
              and "P2 - Piers" not in sets and sets["P2 - Rupert"]["label"] == "Racing on Sundays"
              and sets["P2 - Rupert"]["picture"] == "Rupert.png" and (people_mod.pictures_of(pool) / "Rupert.png").is_file()
              and not (people_mod.pictures_of(pool) / "Piers.png").exists(), str([plan["lines"], sets])[:500])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept
