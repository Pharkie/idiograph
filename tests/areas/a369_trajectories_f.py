from __future__ import annotations

import base64
import json
import shutil
from pathlib import Path

from workbook import WorkbookError

from .support import check
from . import support
import idiograph_routes

# Every word invented: Kit asks newcomers to an allotment about their first year on it, before the season, at
# midsummer and after the harvest. Wren is interviewed at T1 and T2, Ash at all three.
WREN_T1 = ("Kit: [00:00:03] What did you expect of the plot?\nWren: [00:03:12] Tidy rows, like the seed packets.\n"
           "Kit: [00:00:40] And the shed?\nWren: [00:35:55] I had not looked inside it yet.\n")
WREN_T2 = ("Kit: [00:00:02] How is it now?\nWren: [00:00:06] The man next door just leaned on the fence and told me.\n"
           "Kit: [00:10:00] And the shed?\nWren: [00:14:02] Under the sacks there were forks older than me.\n")
ASH_T1 = "Kit: [00:00:03] Why a plot?\nAsh: [00:00:09] To grow what my grandmother grew.\n"
ASH_T2 = "Kit: [00:00:03] And now?\nAsh: [00:00:07] The beans failed and I asked next door.\n"
ASH_T3 = "Kit: [00:00:03] After the harvest?\nAsh: [00:00:05] I did the supper this year. Everyone came.\n"
THREE = [{"label": "T1", "description": "Before the season"}, {"label": "T2", "description": "Midsummer"},
         {"label": "T3", "description": "After the harvest"}]


def test_trajectories_f(scratch):
    print("\n369. Trajectories as his Freeform lays them out (trajbuild2, 10 November 2026): each LPET a row across "
          "the timepoints with its state, key quote and bold from the LPET table, the states moved from the LPETs' "
          "notes, a trajectory's sentence, colour and icon, a participant's label, tags, picture and order, an LPET "
          "hidden and its domain, each op with its dry run, through the route and the command line, and the board's "
          "own note (trajnote, 10 November 2026), and on the LPETs screen an LPET's domain and its key quote's bold "
          "(lpetmarks, 12 November 2026)")
    import cli
    import gets as gets_mod
    import mcp_server
    import server as server_mod
    import trajectories as traj_mod
    import workbook as wb_mod

    b64 = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")
    base = scratch / "a369"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    cfg_file = scratch / "a369-config.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "Kit", "corpus": "", "gravity_reference": "",
                                    "corpus_exclude": []}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)

    def row(name, text, who, interview, **more):
        return dict({"name": name, "data": b64(text), "pseudonym": who, "interview": interview,
                     "speakers": {"Kit": "interviewer", who: "participant"}}, **more)

    def said_rows(book: Path, sheet: str, who: str) -> list[int]:
        import openpyxl
        wb = openpyxl.load_workbook(book, read_only=True)
        try:
            return [r for r, values in enumerate(wb[sheet].iter_rows(min_row=2, max_col=1, values_only=True), start=2)
                    if str(values[0] or "").strip() == who]
        finally:
            wb.close()

    def call(route: str, body: dict) -> dict:
        with idiograph_routes.route_scope(route, body):
            return server_mod.ROUTES[route](body)

    def refused(body: dict) -> str:
        try:
            call("/api/trajectories-ops", body)
        except WorkbookError as exc:
            return str(exc)
        return "answered"

    def board_of(book: Path, tp: int, groups: list):
        st = call("/api/themes", {"workbook": str(book), "timepoint": tp})
        keys = [c["key"] for c in st["cards"]]
        v = dict(st["version"], cards={k: {"x": 0, "y": 40 * i} for i, k in enumerate(keys)},
                 groups=[{"id": f"g{i + 1}", "label": label, "members": [keys[j] for j in at], "x": 300 * i, "y": -40}
                         for i, (label, at) in enumerate(groups)], discarded=[], picks={})
        call("/api/themes-save", {"workbook": str(book), "timepoint": tp, "version": v})

    def lpets_of(book: Path, groups: list):
        lp = call("/api/gets", {"workbook": str(book), "lpets": True})
        pet = {c["text"]: c["key"] for c in lp["cards"] if c["kind"] == "pet"}
        lv = dict(lp["version"], cards={c["key"]: {"x": c["x"], "y": c["y"]} for c in lp["cards"]},
                  groups=[dict({"id": f"G{i + 1}", "label": label, "members": [pet[t] for t in titles], "x": 400 * i,
                                "y": -60}, **({"note": note} if note else {}))
                          for i, (label, titles, note) in enumerate(groups)], discarded=[], picks={}, notes=[])
        call("/api/gets-save", {"workbook": str(book), "lpets": True, "version": lv})

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "a369-state.json", {"recent": []}
        garden = base / "Allotment year"
        garden.mkdir()
        made = idiograph_routes.api_new_project({"op": "make", "folder": str(garden), "name": "Allotment year",
                                                 "research_question": "How do newcomers make sense of a first year on a plot?",
                                                 "files": [row("wren-before.txt", WREN_T1, "Wren", "Before"),
                                                           row("ash-before.txt", ASH_T1, "Ash", "Before")]})
        root_id = made["project"]["id"]
        idiograph_routes.api_project({"root": root_id, "timepoints": THREE})
        idiograph_routes.api_project({"root": root_id, "agents": True})
        idiograph_routes.api_add_transcripts({"op": "add", "root": root_id, "files": [
            row("wren-mid.txt", WREN_T2, "Wren", "Midsummer", timepoint=2),
            row("ash-mid.txt", ASH_T2, "Ash", "Midsummer", timepoint=2),
            row("ash-after.txt", ASH_T3, "Ash", "Harvest", timepoint=3)]})
        wren = garden / "P1 - Wren" / "P1 Wren - EN & ES.xlsx"
        ash = garden / "P2 - Ash" / "P2 Ash - EN & ES.xlsx"
        w1, w2 = said_rows(wren, "Before", "Wren"), said_rows(wren, "Midsummer", "Wren")
        wb_mod.save_turn(wren, "Before", w1[0], "Trusting the packet", "", "Tidy rows, like the seed packets.")
        # two Quote cells that keep their own inverted commas, straight and curly, as a workbook from Excel may (trajfix)
        wb_mod.save_turn(wren, "Before", w1[1], "Not yet inside the shed", "", '"I had not looked inside it yet."')
        wb_mod.save_turn(wren, "Midsummer", w2[0], "Told over the fence\nAsking next door", "",
                         "The man next door just leaned on the fence and told me.\nleaned on the fence")
        wb_mod.save_turn(wren, "Midsummer", w2[1], "Clearing the shed", "", "“Under the sacks there were forks older than me.”")
        wb_mod.save_turn(ash, "Before", said_rows(ash, "Before", "Ash")[0], "Growing a grandmother's plot", "",
                         "To grow what my grandmother grew.")
        wb_mod.save_turn(ash, "Midsummer", said_rows(ash, "Midsummer", "Ash")[0], "Failing, then asking", "",
                         "The beans failed and I asked next door.")
        wb_mod.save_turn(ash, "Harvest", said_rows(ash, "Harvest", "Ash")[0], "Feeding the family", "",
                         "I did the supper this year. Everyone came.")
        board_of(wren, 1, [("Order expected", [0]), ("A shed unopened", [1])])
        board_of(wren, 2, [("Learning from neighbours", [0, 1]), ("A room of her own", [2])])
        board_of(ash, 1, [("Carrying a family plot", [0])])
        board_of(ash, 2, [("Asking after a failure", [0])])
        board_of(ash, 3, [("Leading the supper", [0])])
        lpets_of(wren, [("Asking next door took the place of the packet", ["Order expected", "Learning from neighbours"],
                         "T1: Trusted seed packets over people.\nAsked no one.\n\nT2 (Midsummer): A failed bed sent her "
                         "to the neighbours.\n\nT3: Keeps a notebook of their advice."),
                        ("The shed became a room of her own", ["A shed unopened", "A room of her own"], "")])
        lpets_of(ash, [("The family's beans", ["Carrying a family plot", "Asking after a failure", "Leading the supper"],
                        "Before the season: Missed her grandmother.\nMidsummer: The beans failed.")])
        wren_lp = gets_mod.lpets_path(wren)
        tfile = garden / traj_mod.FILE
        books_before = {p: p.read_bytes() for p in (wren, ash)}

        # (a) each LPET a row across the timepoints, the first quote standing in
        b = call("/api/trajectories", {"workbook": str(wren)})
        wc = next(c for c in b["participants"] if c["case"] == "P1 - Wren")
        r1 = wc["rows"][0]
        check("369: each LPET of the participant is a row with a cell for each timepoint, the first quote standing in, "
              "no state yet, and a timepoint they were not interviewed at marked missing",
              [r["title"] for r in wc["rows"]] == ["Asking next door took the place of the packet",
                                                   "The shed became a room of her own"]
              and r1["cells"]["T1"]["quote"]["text"] == "Tidy rows, like the seed packets."
              and r1["cells"]["T1"]["chosen"] is False and r1["cells"]["T1"]["state"] == ""
              and r1["cells"]["T3"]["quote"] is None and r1["cells"]["T3"]["missing"] is True
              and len(r1["cells"]["T2"]["choices"]) == 2 and r1["shown"] is True and not tfile.exists(),
              str(wc["rows"])[:600])

        # (b) the states moved from the LPETs' notes, the dry run writing nothing
        lp_before = wren_lp.read_bytes()
        dry = call("/api/trajectories-ops", {"workbook": str(wren), "dry_run": True, "ops": [{"op": "states_from_notes"}]})
        check("369: the states' dry run lists each state it would move, by the timepoint's key or its label, and "
              "writes nothing", len(dry["changes"]) == 5 and wren_lp.read_bytes() == lp_before and not tfile.exists()
              and sum("Ash" in x for x in dry["changes"]) == 2, str(dry["changes"]))
        done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": [{"op": "states_from_notes"}]})
        held = json.loads(wren_lp.read_text(encoding="utf-8"))
        src = next(bd for bd in held["boards"] if bd["id"] == held.get("current"))
        g1 = next(g for g in src["groups"] if g["id"] == "G1")
        check("369: the states land in the LPET table's row notes, a paragraph of two lines kept whole, a head with "
              "its description in brackets read, T3's kept though she was not interviewed then, and the LPET's note "
              "left as it was",
              src["rows"]["G1"]["T1"]["note"] == "Trusted seed packets over people.\nAsked no one."
              and src["rows"]["G1"]["T2"]["note"] == "A failed bed sent her to the neighbours."
              and src["rows"]["G1"]["T3"]["note"] == "Keeps a notebook of their advice."
              and g1["note"].startswith("T1: Trusted seed packets")
              and next(c for c in done["participants"] if c["case"] == "P1 - Wren")["rows"][0]["cells"]["T2"]["state"]
              == "A failed bed sent her to the neighbours.", str(src.get("rows")))
        call("/api/trajectories-ops", {"workbook": str(wren), "ops": [
            {"op": "state", "participant": "Wren", "lpet": "G1", "timepoint": "T1", "state": "Trusted the packet."}]})
        again = call("/api/trajectories-ops", {"workbook": str(wren), "dry_run": True, "ops": [{"op": "states_from_notes"}]})
        check("369: run again it keeps a state he has changed since and moves nothing twice",
              again["changes"] == ["Wren's 'Asking next door took the place of the packet' at T1 has a state already, kept."],
              str(again["changes"]))

        # (c) the key quote ticked through the LPET table's row, and taken off again
        choices = next(c for c in call("/api/trajectories", {"workbook": str(wren)})["participants"]
                       if c["case"] == "P1 - Wren")["rows"][0]["cells"]["T2"]["choices"]
        second = choices[1]["key"]
        tick = [{"op": "quote", "participant": "Wren", "lpet": "Asking next door took the place of the packet",
                 "timepoint": "Midsummer", "quote": second}]
        lp_before = wren_lp.read_bytes()
        dry = call("/api/trajectories-ops", {"workbook": str(wren), "dry_run": True, "ops": tick})
        check("369: a key quote's dry run says so and writes nothing", wren_lp.read_bytes() == lp_before
              and dry["changes"] == ["Wren's 'Asking next door took the place of the packet' at T2: key quote ticked."],
              str(dry["changes"]))
        done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": tick})
        cell = next(c for c in done["participants"] if c["case"] == "P1 - Wren")["rows"][0]["cells"]["T2"]
        lt = call("/api/gets", {"workbook": str(wren), "lpets": True})
        check("369: the key quote is the LPET table's tick, the same on the LPETs screen's board",
              cell["chosen"] is True and cell["quote"]["key"] == second and lt["rows"]["G1"]["T2"]["quote"] == second,
              str(cell)[:300])
        said = refused({"workbook": str(wren), "ops": [dict(tick[0], quote="Before:2:0")]})
        check("369: a quote that is not one of that cell's is refused, nothing written", "not a quote of" in said, said)

        # (d) his bold on the quote standing in ticks it, and is kept on the row, never in the transcript
        bold = [{"op": "bold", "participant": "Wren", "lpet": "G1", "timepoint": "T1", "spans": [[0, 10], [5, 14]]}]
        done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": bold})
        cell = next(c for c in done["participants"] if c["case"] == "P1 - Wren")["rows"][0]["cells"]["T1"]
        check("369: bold on the quote standing in ticks it, its spans kept as one, the workbooks untouched",
              cell["chosen"] is True and cell["bold"] == [[0, 14]] and cell["quote"]["text"][0:14] == "Tidy rows, lik"
              and all(p.read_bytes() == v for p, v in books_before.items()), str(cell)[:300])
        said = refused({"workbook": str(wren), "ops": [dict(bold[0], spans=[[0, 999]])]})
        check("369: bold past the quote's end is refused", "Bold is a list" in said, said)
        # the LPETs screen's own save keeps the bold and the domain it does not edit
        call("/api/trajectories-ops", {"workbook": str(wren), "ops": [
            {"op": "domain", "participant": "Wren", "lpet": "G1", "domain": "Practical"}]})
        lp = call("/api/gets", {"workbook": str(wren), "lpets": True})
        version = dict(lp["version"], cards={c["key"]: {"x": c["x"], "y": c["y"]} for c in lp["cards"]},
                       groups=lp["groups"], rows=lp["rows"], discarded=[], picks={}, notes=[])
        call("/api/gets-save", {"workbook": str(wren), "lpets": True, "version": version})
        held = json.loads(wren_lp.read_text(encoding="utf-8"))
        src = next(bd for bd in held["boards"] if bd["id"] == held.get("current"))
        check("369: a save of the LPETs board keeps the domain on the LPET and the bold on its row",
              next(g for g in src["groups"] if g["id"] == "G1").get("domain") == "Practical"
              and src["rows"]["G1"]["T1"].get("bold") == [[0, 14]], str(src.get("rows")))

        # (e) the trajectory's and the participant's own, each op with its dry run
        ops = [{"op": "add", "title": "Positive"}, {"op": "add", "title": "Mixed"},
               {"op": "describe", "column": "Positive", "description": "The plot gave them a place among the neighbours."},
               {"op": "colour", "column": "Positive", "colour": "Green"}, {"op": "icon", "column": "c1", "icon": "rising"},
               {"op": "place", "participant": "Wren", "column": "Positive"},
               {"op": "place", "participant": "Ash", "column": "Positive", "at": 0},
               {"op": "title", "participant": "Wren", "title": "The late starter"},
               {"op": "tags", "participant": "Wren", "tags": ["Town", "First plot"]},
               {"op": "tags", "participant": "Ash", "tags": ["town", "Village"]}]
        t_before = tfile.read_bytes()
        dry = call("/api/trajectories-ops", {"workbook": str(wren), "dry_run": True, "ops": ops})
        check("369: the trajectory's and the participants' ops in a dry run say each change and write nothing",
              tfile.read_bytes() == t_before and len(dry["changes"]) == 10 and "Positive is Green now." in dry["changes"]
              and "Positive's icon is rising now." in dry["changes"], str(dry["changes"]))
        done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": ops})
        f = json.loads(tfile.read_text(encoding="utf-8"))
        pos = done["columns"][0]
        cards = {c["case"]: c for c in done["participants"]}
        check("369: saved: the sentence, colour and icon, Ash first by his order, Wren's label, and Town one tag "
              "with one colour on both, the domain's word given a colour too",
              pos["description"].startswith("The plot gave") and pos["colour"] == "good" and pos["icon"] == "rising"
              and pos["participants"] == ["P2 - Ash", "P1 - Wren"] and cards["P1 - Wren"]["title"] == "The late starter"
              and [t["word"] for t in cards["P2 - Ash"]["tags"]] == ["Town", "Village"]
              and cards["P2 - Ash"]["tags"][0]["colour"] == cards["P1 - Wren"]["tags"][0]["colour"]
              and set(f["tags"]) == {"Town", "First plot", "Village", "Practical"}
              and f["history"][-1]["changes"][0] == "Positive added.", str(f)[:600])
        town = cards["P1 - Wren"]["tags"][0]["colour"]
        done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": [{"op": "tag_colour", "tag": "TOWN", "colour": "Teal"}]})
        cards = {c["case"]: c for c in done["participants"]}
        check("369: a tag's colour changed once is changed on every participant with it",
              town != 5 and cards["P1 - Wren"]["tags"][0]["colour"] == 5 and cards["P2 - Ash"]["tags"][0]["colour"] == 5
              and done["changes"] == ["Town is Teal now, wherever it is used."], str(done["changes"]))
        said = refused({"workbook": str(wren), "ops": [{"op": "colour", "column": "Positive", "colour": "Mauve"}]})
        check("369: a colour not of the palette is refused", "not a trajectory's colour" in said, said)

        # (f) moves: by place, by order, and to another trajectory
        done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": [{"op": "order", "participant": "Wren", "at": 0}]})
        check("369: order moves a participant within their trajectory", done["columns"][0]["participants"]
              == ["P1 - Wren", "P2 - Ash"] and done["changes"] == ["Wren moved to place 1 in Positive."], str(done["changes"]))
        done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": [{"op": "place", "participant": "Ash", "column": "Mixed"}]})
        check("369: placed in another trajectory, they leave the first's order and keep their label and tags",
              done["columns"][0]["participants"] == ["P1 - Wren"] and done["columns"][1]["participants"] == ["P2 - Ash"]
              and [t["word"] for t in next(c for c in done["participants"] if c["case"] == "P2 - Ash")["tags"]] == ["Town", "Village"],
              str(done["columns"]))

        # (g) an LPET hidden and shown on this screen alone
        done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": [
            {"op": "hide", "participant": "Wren", "lpet": "The shed became a room of her own"}]})
        wc = next(c for c in done["participants"] if c["case"] == "P1 - Wren")
        check("369: hide leaves an LPET off Trajectories, kept in its file, the LPET itself untouched",
              [r["shown"] for r in wc["rows"]] == [True, False] and json.loads(tfile.read_text(encoding="utf-8"))["placed"]["P1 - Wren"]["hidden"] == ["G2"]
              and len(call("/api/gets", {"workbook": str(wren), "lpets": True})["groups"]) == 2, str(wc["hidden"]))
        done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": [{"op": "show", "participant": "Wren", "lpet": "G2"}]})
        check("369: and show puts it back", "hidden" not in json.loads(tfile.read_text(encoding="utf-8"))["placed"]["P1 - Wren"]
              and done["changes"] == ["Wren's LPET 'The shed became a room of her own' shown on Trajectories."], str(done["changes"]))

        # (h) a picture of his own kept in the project folder, scaled, the one before it kept in the archive
        w, h = 600, 400
        rgba = bytearray()
        for y in range(h):
            for x in range(w):
                rgba += bytes((x * 255 // w, y * 255 // h, 90, 255))
        png = traj_mod.png_write(w, h, rgba)
        source = base / "wren portrait.png"
        source.write_bytes(png)
        # the participant's own picture since pbiobuild, in the project's pictures folder, for every screen
        import participants as people_mod
        pics = people_mod.pictures_of(garden)
        dry = call("/api/trajectories-ops", {"workbook": str(wren), "dry_run": True, "ops": [
            {"op": "picture", "participant": "Wren", "from": str(source)}]})
        check("369: a picture's dry run writes no file", dry["changes"] == ["Wren's picture changed."] and not pics.exists(),
              str(dry["changes"]))
        done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": [{"op": "picture", "participant": "Wren", "from": str(source)}]})
        kept_pic = pics / "Wren.png"
        pw, ph, _ = traj_mod.png_read(kept_pic.read_bytes()) if kept_pic.exists() else (0, 0, b"")
        wc = next(c for c in done["participants"] if c["case"] == "P1 - Wren")
        check("369: his own picture is kept in the project's pictures folder, the participant's own, a square scaled to "
              "256, the source left where it was, the page given its address",
              (pw, ph) == (256, 256) and source.read_bytes() == png and wc["picture"] == "Wren.png"
              and wc["picture_url"].startswith("/participant-picture?"), f"{pw}x{ph} {wc.get('picture_url')}")
        done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": [{"op": "picture", "participant": "Wren", "set": "peep07"}]})
        wc = next(c for c in done["participants"] if c["case"] == "P1 - Wren")
        check("369: one of the set in its place, the picture before kept in the pictures' _Archive, never deleted",
              wc["picture"] == "set:peep07" and wc["picture_url"] == "/faces/peep07.svg" and not kept_pic.exists()
              and len(list((pics / "_Archive").glob("Wren *.png"))) == 1, str(wc["picture"]))
        small = traj_mod.png_write(2, 2, bytearray(b"\x10\x20\x30\xff" * 4))
        url = "data:image/png;base64," + base64.b64encode(small).decode("ascii")
        done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": [{"op": "picture", "participant": "Ash", "data": url}]})
        check("369: the window's picture comes as a data URL and is kept the same way",
              (pics / "Ash.png").is_file() and next(c for c in done["participants"] if c["case"] == "P2 - Ash")["picture"] == "Ash.png")
        (base / "not a picture.png").write_text("hello", encoding="utf-8")
        said = refused({"workbook": str(wren), "ops": [{"op": "picture", "participant": "Ash", "from": str(base / "not a picture.png")}]})
        check("369: a file that is no picture is refused", "PNG, a JPEG or an SVG" in said, said)
        done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": [{"op": "picture", "participant": "Ash"}]})
        check("369: a picture taken off goes to the archive too, the initial standing in",
              not (pics / "Ash.png").exists() and next(c for c in done["participants"] if c["case"] == "P2 - Ash")["picture"] == "",
              str(done["changes"]))

        # (i) the command line and MCP
        def run(*args):
            code, out, err = cli.run(["--root", str(garden), "--config", str(cfg_file), *args, "--json"])
            return code, (support.plain(json.loads(out)) if out.strip() else {}), err

        opsfile = scratch / "a369-ops.json"
        opsfile.write_text(json.dumps([{"op": "domain", "participant": "Ash", "lpet": "G1", "domain": "Family"},
                                       {"op": "describe", "column": "Mixed", "description": "Begun, then unsettled."}]),
                           encoding="utf-8")
        first = tfile.read_bytes()
        code, tdry, err = run("trajectories", "apply", "--ops", str(opsfile), "--dry-run")
        mid = tfile.read_bytes()
        code2, tdone, err2 = run("trajectories", "apply", "--ops", str(opsfile), "--note", "His domains and sentences")
        code3, tshow, err3 = run("trajectories", "show")
        ash_rows = next(c for c in tshow.get("participants") or [] if c["case"] == "P2 - Ash")["rows"] if code3 == 0 else []
        check("369: trajectories apply from the command line, its dry run first, then the domain on Ash's LPET and "
              "the sentence, which trajectories show reads with the rows",
              code == 0 and tdry.get("dry_run") is True and mid == first and code2 == 0 and code3 == 0
              and ash_rows and ash_rows[0]["domain"] == "Family" and [d["word"] for d in ash_rows[0]["domains"]] == ["Family"]
              and ash_rows[0]["domains"][0]["colour"] is not None
              and json.loads(tfile.read_text(encoding="utf-8"))["history"][-1].get("note") == "His domains and sentences",
              (err or "") + (err2 or "") + (err3 or ""))
        tool = next(t for t in mcp_server.TOOLS if t["name"] == "trajectories_apply")
        check("369: the MCP server's trajectories_apply names every new op",
              all(w in tool["description"] for w in ('"describe"', '"colour"', '"icon"', '"title"', '"tags"', '"tag_colour"',
                                                     '"picture"', '"hide"', '"state"', '"quote"', '"bold"', '"domain"',
                                                     '"states_from_notes"', '"order"', '"note_board"')))

        # (j) the board's own note (trajnote, 10 November 2026): its dry run, kept in the file, read again after a
        # reload, printed by trajectories show, and cleared
        said_note = [{"op": "note_board", "note": "  Pictures drawn by a friend of the allotment.\nThanks to the committee.  "}]
        t_before = tfile.read_bytes()
        dry = call("/api/trajectories-ops", {"workbook": str(wren), "dry_run": True, "ops": said_note})
        check("369: the board's note in a dry run says so and writes nothing",
              dry["changes"] == ["The board's note changed."] and tfile.read_bytes() == t_before
              and dry["note"].startswith("Pictures drawn"), str(dry["changes"]))
        call("/api/trajectories-ops", {"workbook": str(wren), "ops": said_note, "note": "His credit for the pictures"})
        f = json.loads(tfile.read_text(encoding="utf-8"))
        fresh_board = call("/api/trajectories", {"workbook": str(wren)})
        code, tshow, err = run("trajectories", "show")
        check("369: the board's note is kept in the trajectories file, trimmed, its lines kept, with its History line, "
              "and read again on a fresh open and by trajectories show",
              f.get("note") == "Pictures drawn by a friend of the allotment.\nThanks to the committee."
              and f["history"][-1]["changes"] == ["The board's note changed."]
              and fresh_board["note"] == f["note"] and code == 0 and tshow.get("note") == f["note"]
              and len(f["columns"]) == 2, (err or "") + str(fresh_board.get("note")))
        said = refused({"workbook": str(wren), "ops": [{"op": "note_board", "note": "x" * (traj_mod.NOTE_MAX + 1)}]})
        check("369: a board's note past its length is refused", "fewer" in said or str(traj_mod.NOTE_MAX) in said, said)
        done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": [{"op": "note_board", "note": ""}]})
        check("369: an empty note clears it from the file", done["changes"] == ["The board's note cleared."]
              and "note" not in json.loads(tfile.read_text(encoding="utf-8")) and done["note"] == "", str(done["changes"]))

        # (k) trajfix, 11 November 2026: a key quote whose Quote cell keeps its own marks shown once marked with his
        # bold on the same words, and an LPET in two domains given two pills, each its own colour
        def wren_row(answer: dict, gid: str) -> dict:
            return next(r for r in next(c for c in answer["participants"] if c["case"] == "P1 - Wren")["rows"] if r["id"] == gid)

        def kept_board() -> dict:
            held = json.loads(wren_lp.read_text(encoding="utf-8"))
            return held, next(bd for bd in held["boards"] if bd["id"] == held.get("current"))

        g2 = wren_row(call("/api/trajectories", {"workbook": str(wren)}), "G2")
        c1, c2 = g2["cells"]["T1"], g2["cells"]["T2"]
        check("369: a key quote whose Quote cell keeps its own straight or curly marks is given without them, in its "
              "cell and among the quotes it can take",
              c1["quote"]["text"] == "I had not looked inside it yet."
              and c2["quote"]["text"] == "Under the sacks there were forks older than me."
              and all(q["text"][:1] not in "\"“'" and q["text"][-1:] not in "\"”'" for q in c1["choices"] + c2["choices"])
              and c1["choices"] and c2["choices"], str(g2["cells"])[:600])
        wb_before = wren.read_bytes()
        done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": [
            {"op": "bold", "participant": "Wren", "lpet": "G2", "timepoint": "T1", "spans": [[0, 5]]}]})
        cell = wren_row(done, "G2")["cells"]["T1"]
        held, src = kept_board()
        raw = gets_mod.quote_at(held["cases"]["T1"], cell["quote"]["key"])["text"]
        kept_bold = src["rows"]["G2"]["T1"].get("bold")
        check("369: bold on the first words of a quote shown without its marks stays on those words: kept against the "
              "quote as the workbook keeps it, past its opening mark, and shown on them, the workbook untouched",
              raw.startswith('"I had') and cell["bold"] == [[0, 5]] and cell["quote"]["text"][0:5] == "I had"
              and kept_bold == [[1, 6]] and raw[1:6] == "I had" and wren.read_bytes() == wb_before,
              f"{cell} {kept_bold} {raw!r}")
        said = refused({"workbook": str(wren), "ops": [{"op": "bold", "participant": "Wren", "lpet": "G2", "timepoint": "T1",
                                                         "spans": [[0, len(raw)]]}]})
        check("369: bold is measured against the words without their marks, so a span to the end of the quote as the "
              "workbook keeps it is past them and refused", "Bold is a list" in said, said)
        # a bold kept against the marks, as one made before this fix was, read back on its words
        lp = call("/api/gets", {"workbook": str(wren), "lpets": True})
        raw2 = gets_mod.quote_at(held["cases"]["T2"], c2["quote"]["key"])["text"]
        rows = json.loads(json.dumps(lp["rows"]))
        rows.setdefault("G2", {})["T2"] = {"quote": c2["quote"]["key"], "note": "", "bold": [[0, 6], [len(raw2) - 1, len(raw2)]]}
        version = dict(lp["version"], cards={c["key"]: {"x": c["x"], "y": c["y"]} for c in lp["cards"]},
                       groups=lp["groups"], rows=rows, discarded=[], picks={}, notes=[])
        call("/api/gets-save", {"workbook": str(wren), "lpets": True, "version": version})
        cell = wren_row(call("/api/trajectories", {"workbook": str(wren)}), "G2")["cells"]["T2"]
        check("369: a bold kept against a quote's curly marks, the opening one and the closing one, shows on the word "
              "after the opening mark, and the span on the closing mark alone is left out",
              raw2[0] == "“" and raw2[0:6] == "“Under" and cell["bold"] == [[0, 5]]
              and cell["quote"]["text"][0:5] == "Under", f"{cell} {raw2!r}")

        f = json.loads(tfile.read_text(encoding="utf-8"))
        practical = f["tags"]["Practical"]
        t_before, lp_before = tfile.read_bytes(), wren_lp.read_bytes()
        dry = call("/api/trajectories-ops", {"workbook": str(wren), "dry_run": True, "ops": [
            {"op": "domain", "participant": "Wren", "lpet": "G2", "domain": "Neighbours, Practical"}]})
        check("369: a domain of two in a dry run writes nothing", tfile.read_bytes() == t_before
              and wren_lp.read_bytes() == lp_before
              and dry["changes"] == ["Wren's 'The shed became a room of her own' is Neighbours, Practical now."], str(dry["changes"]))
        done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": [
            {"op": "domain", "participant": "Wren", "lpet": "G2", "domain": "Neighbours, Practical"}]})
        f = json.loads(tfile.read_text(encoding="utf-8"))
        g1, g2 = wren_row(done, "G1"), wren_row(done, "G2")
        check("369: two domains separated by a comma are two pills, each with its own colour: Practical the one it has "
              "on Wren's other LPET, Neighbours given its own by the op and kept in the file, never the two as one word",
              g2["domain"] == "Neighbours, Practical"
              and [d["word"] for d in g2["domains"]] == ["Neighbours", "Practical"]
              and g2["domains"][1]["colour"] == practical == g1["domains"][0]["colour"]
              and g2["domains"][0]["colour"] == f["tags"].get("Neighbours") != practical
              and "Neighbours, Practical" not in f["tags"], f"{g2['domains']} {f['tags']}")
        shown = traj_mod.board({"columns": [], "placed": {}, "tags": {"Town": 3}},
                               [{"case": "P1 - Wren", "colour": 0, "lpets": [], "rows": [
                                   {"id": "G1", "title": "x", "domain": " Town ,, seeds , town", "cells": {}}]}])
        ds = shown["participants"][0]["rows"][0]["domains"]
        check("369: domains are read trimmed, an empty one and a repeat left out, and one no op has coloured yet shown in "
              "a colour of its own, nothing kept for it",
              [d["word"] for d in ds] == ["Town", "seeds"] and ds[0]["colour"] == 3 and ds[1]["colour"] not in (None, 3)
              and shown["tags"] == {"Town": 3}, str(ds))

        # (l) trajchoose, 11 November 2026: a key quote from anywhere in the interview, or a passage of any of the
        # participant's transcripts, ticked with nothing moved and no workbook written, and kept across a reload
        _choose_from_anywhere(call, refused, run, wren, ash, wren_lp, said_rows, kept_board, wren_row)

        # (m) renamefix, 11 November 2026: everything Wren has on Trajectories survives a rename, MCP's with the
        # folder kept, then the command line's with it ticked
        _survives_rename(call, run, garden, cfg_file, wren)

        # (n) lpetmarks, 12 November 2026: an LPET's domain the same on the LPETs screen and on Trajectories, set from
        # either, on the LPETs screen's own board too, and his bold in a key quote in the LPET table's exports
        _lpets_screen_marks(call, run, scratch, garden, ash)
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept
    _keys_in_browser()
    _lpets_marks_in_node(scratch)


def _lpets_screen_marks(call, run, scratch: Path, garden: Path, ash: Path):
    """An LPET's domain and its key quote's bold on the LPETs screen (lpetmarks, 12 November 2026): a domain set on
    Trajectories is the LPETs screen's LPET's, its pills in the same words and colours, and one set from the LPETs
    screen, Trajectories' own `domain` operation on the board on its canvas, is Trajectories', each with its dry run
    and its History; on a board LGETs do not take it changes that board alone, a board not there refused; and his bold
    reaches the LPET table's print view, its PDF's data and its PDF."""
    import gets as gets_mod
    import idiograph_routes as routes
    import trajectories as traj_mod

    ash_lp = gets_mod.lpets_path(ash)
    tfile = garden / traj_mod.FILE

    def ash_row(answer: dict) -> dict:
        return next(r for r in next(c for c in answer["participants"] if c["case"] == "P2 - Ash")["rows"] if r["id"] == "G1")

    def lpets(board: str | None = None) -> dict:
        return call("/api/gets", dict({"workbook": str(ash), "lpets": True}, **({"board": board} if board else {})))

    def refused(body: dict) -> str:
        try:
            call("/api/trajectories-ops", body)
        except WorkbookError as exc:
            return str(exc)
        return "answered"

    # set on Trajectories, shown on the LPETs screen's LPET
    done = call("/api/trajectories-ops", {"workbook": str(ash), "ops": [
        {"op": "domain", "participant": "Ash", "lpet": "G1", "domain": "Family, Neighbours"}]})
    lp = lpets()
    tags = json.loads(tfile.read_text(encoding="utf-8"))["tags"]
    check("369: a domain set on Trajectories shows on the LPETs screen's LPET, each of its domains a pill in the words "
          "and the colour Trajectories gives it, Neighbours in the one it has on Linnet's LPET",
          ash_row(done)["domains"] == lp["lpet_domains"].get("G1")
          and [d["word"] for d in lp["lpet_domains"]["G1"]] == ["Family", "Neighbours"]
          and lp["lpet_domains"]["G1"][1]["colour"] == tags["Neighbours"] and set(lp["lpet_domains"]) == {"G1"},
          str(lp.get("lpet_domains")))

    # set from the LPETs screen: the domain op on the board on its canvas, named as the screen names the participant
    b1, v_before = lp["version"]["id"], lp["version"]["v"]
    op = [{"op": "domain", "participant": lp["participant"], "lpet": "G1", "board": b1, "domain": "Seasons"}]
    lp_before, t_before = ash_lp.read_bytes(), tfile.read_bytes()
    dry = call("/api/trajectories-ops", {"workbook": str(ash), "dry_run": True, "ops": op})
    check("369: the LPETs screen's domain in a dry run says so and writes nothing",
          dry["changes"] == ["Ash's 'The family's beans' is Seasons now."] and ash_lp.read_bytes() == lp_before
          and tfile.read_bytes() == t_before, str(dry["changes"]))
    done = call("/api/trajectories-ops", {"workbook": str(ash), "ops": op})
    lp = lpets()
    f = json.loads(tfile.read_text(encoding="utf-8"))
    check("369: and set, it is the LPET's domain on Trajectories too, the word given its colour across the project and "
          "the change a line in the board's History, and the LPETs screen reads its new version",
          [d["word"] for d in ash_row(done)["domains"]] == ["Seasons"] and ash_row(done)["domains"] == lp["lpet_domains"]["G1"]
          and lp["lpet_domains"]["G1"][0]["colour"] == f["tags"]["Seasons"]
          and f["history"][-1]["changes"] == ["Ash's 'The family's beans' is Seasons now."]
          and lp["version"]["v"] != v_before and lp["version"]["id"] == b1,
          str(lp.get("lpet_domains")) + str(f["history"][-1]))

    # his bold on a key quote, then the LPET table's print view, its PDF's data and its PDF
    call("/api/trajectories-ops", {"workbook": str(ash), "ops": [
        {"op": "bold", "participant": "Ash", "lpet": "G1", "timepoint": "T2", "spans": [[4, 9]]}]})
    code, page = routes.gets_print_page({"workbook": str(ash), "lpets": "1", "board": b1, "what": "table", "auto": "0"})
    with routes.lpets_scope(ash):
        import gets_print
        data = gets_print.typst_data(garden, routes.gets_books(garden), routes.read_project(garden), b1, what="table")
    rows = {r["who"]: r for r in data["table"][0]["rows"]}
    pdf = scratch / "a369-lpets.pdf"
    pcode, made, err = run("gets", "export", b1, "--lpets", "Ash", "--out", str(pdf))
    check("369: his bold in a key quote reaches the LPET table's print view on its words, the quote's other words plain, "
          "and a quote with none is as it was",
          code == 200 and "<i>‘The <b>beans</b> failed and I asked next door.’</i>" in page
          and "<i>‘To grow what my grandmother grew.’</i>" in page, page[page.find('class="kqcell"'):][:400])
    check("369: and the PDF's data and the PDF made from it, the LPET table's Typst, carry it the same",
          rows["T2"]["quote"]["words"] == [["The ", False], ["beans", True], [" failed and I asked next door.", False]]
          and rows["T1"]["quote"]["words"] is None and pcode == 0 and pdf.is_file() and pdf.read_bytes()[:4] == b"%PDF",
          (err or "") + str(rows.get("T2", {}).get("quote")))

    # a board LGETs do not take: Board 1 chosen as the Current board, a copy on the canvas, the domain there alone
    call("/api/gets-ops", {"workbook": str(ash), "lpets": True, "op": "choose", "id": b1})
    copy = call("/api/gets-ops", {"workbook": str(ash), "lpets": True, "op": "duplicate", "id": b1})["version"]
    done = call("/api/trajectories-ops", {"workbook": str(ash), "ops": [
        {"op": "domain", "participant": "Ash", "lpet": "G1", "board": copy["name"], "domain": "Harvest"}]})
    held = json.loads(ash_lp.read_text(encoding="utf-8"))
    kept = {b["id"]: next(g for g in b["groups"] if g["id"] == "G1").get("domain") for b in held["boards"]}
    lp = lpets(copy["id"])
    check("369: on a board LGETs do not take, named by its name, the domain changes that board's LPET alone, "
          "Trajectories keeping the one LGETs take, and the LPETs screen on that board draws it",
          kept == {b1: "Seasons", copy["id"]: "Harvest"} and [d["word"] for d in ash_row(done)["domains"]] == ["Seasons"]
          and [d["word"] for d in lp["lpet_domains"]["G1"]] == ["Harvest"], str(kept))
    lp_before = ash_lp.read_bytes()
    said = refused({"workbook": str(ash), "ops": [{"op": "domain", "participant": "Ash", "lpet": "G1", "board": "Board 9",
                                                   "domain": "x"}]})
    check("369: a board the participant's LPETs do not have is refused, nothing written",
          "has no LPETs board Board 9" in said and ash_lp.read_bytes() == lp_before, said)


def _lpets_marks_in_node(scratch: Path):
    """The LPETs screen's part of it in node (lpetmarks): the canvas's undo never steps over an LPET's domain, so a
    save sends the one set through the op, while an LPET deleted and undone comes back with its own; the page takes
    the file's domains after the op; his bold drawn on a key quote's words; and an LPET's pills and Add domain on a
    top LPET of the LPETs board alone."""
    import shutil
    if not shutil.which("node"):
        support.skip("369: the LPETs screen's domain and bold in node", "no node on this computer")
        return
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js").splitlines()
    helpers = "\n".join(next(line for line in app if line.startswith(start)) for start in ("const esc = ", "const escAttr = "))
    script = support.i18n_js() + helpers + "\n" + support.text("apps/idiograph/static/themes.js") + r"""
const out = {};
TH.mode = 'gets';
TH.lpets = true;
TH.layout = {};
TH.lpetDomains = { G1: [{ word: 'Family', colour: 3 }, { word: 'Seasons', colour: 7 }] };
const v = { cards: {}, groups: [{ id: 'G1', label: 'The family\'s beans', members: ['G2'], x: 0, y: 0, domain: 'Old words' },
  { id: 'G2', label: 'Inside', members: [], x: 0, y: 40 }, { id: 'G3', label: 'Leading the supper', members: [], x: 400, y: 0, domain: 'Food' }],
  discarded: [], picks: {}, stickies: [], rows: { G1: { T2: { quote: 'Midsummer:3:0', note: '', bold: [[4, 9]] } } } };
TH.v = v;
TH.meta = { id: 'b1', v: 'old', updated: 'then' };
TH.boards = [{ id: 'b1', name: 'Board 1', updated: 'then', v: 'old' }];
TH.known = { b1: 'then' };
// a rename, then G3 deleted, each a step, then the op sets G1's domain and the page takes the file's back
const first = thSnap(v, new Set());
v.groups[0].label = 'Beans again';
const second = thSnap(v, new Set());
v.groups = v.groups.filter((g) => g.id !== 'G3');
gtDomainsTake({ version: { id: 'b1', v: 'new', updated: 'now' }, groups: [{ id: 'G1', domain: 'Family, Seasons' }, { id: 'G2' }],
  lpet_domains: TH.lpetDomains });
out.taken = [v.groups[0].domain, TH.meta.v, TH.known.b1];
thPut(v, second);
out.undoDelete = v.groups.map((g) => `${g.id}:${g.domain || ''}`);
thPut(v, first);
out.undoRename = [v.groups[0].label, v.groups[0].domain];
out.sent = thLabelOut(v.groups[0]);
out.pills = gtDomainPills(v, 'G1');
out.inner = gtDomainPills(v, 'G2');
out.menu = thMenuItems(v, { kind: 'group', id: 'G1' }).map((x) => x.act);
out.innerMenu = thMenuItems(v, { kind: 'group', id: 'G2' }).map((x) => x.act);
out.bold = gtBoldHtml('The beans failed & I asked.', [[21, 27], [4, 9]]);
TH.lpets = false;
out.getsPills = gtDomainPills(v, 'G1');
out.getsMenu = thMenuItems(v, { kind: 'group', id: 'G1' }).map((x) => x.act);
console.log(JSON.stringify(out));
"""
    ran = support.run_node(script, scratch, "a369-lpetmarks.js")
    try:
        out = json.loads(ran.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        check("369: the LPETs screen's domain and bold run in node", False, (ran.stderr or ran.stdout).strip()[:400])
        return
    check("369: in node, the page takes the file's domain and version after the op, an undo never steps back over "
          "it, so the save sends the one the op set, and an LPET deleted and undone comes back with its own",
          out["taken"] == ["Family, Seasons", "new", "now"] and out["undoDelete"] == ["G1:Family, Seasons", "G2:", "G3:Food"]
          and out["undoRename"] == ["The family's beans", "Family, Seasons"] and out["sent"].get("domain") == "Family, Seasons",
          str({k: out[k] for k in ("taken", "undoDelete", "undoRename")}))
    check("369: in node, a top LPET's label draws its pills as Trajectories does, each in its colour, an LPET inside "
          "another none, and none on a board that is not the LPETs",
          out["pills"].count('class="tf-pill case-3"') == 1 and ">Seasons</span>" in out["pills"]
          and 'case-7' in out["pills"] and out["inner"] == "" and out["getsPills"] == "", out["pills"])
    check("369: in node, Add domain is in a top LPET's menu on the LPETs board alone",
          "domain" in out["menu"] and "domain" not in out["innerMenu"] and "domain" not in out["getsMenu"],
          str(out["menu"]) + str(out["getsMenu"]))
    check("369: in node, his bold in a key quote is drawn on its words, the rest escaped plain",
          out["bold"] == "The <b>beans</b> failed &amp; I <b>asked.</b>", out["bold"])


def _choose_from_anywhere(call, refused, run, wren: Path, ash: Path, wren_lp: Path, said_rows, kept_board, wren_row):
    """A key quote from one of three places (trajchoose, 11 November 2026, Adam's ruling): the LPET's own, the
    participant's other quotes from that interview, and a passage of any of their transcripts, each ticked through
    the quote op with its dry run, kept across a reload and through a save of the LPETs board, bold on each, the
    refusals, trajectories show's choices with their source, and a passage whose words go falling back."""
    import mcp_server
    import workbook as wb_mod

    books = {p: p.read_bytes() for p in (wren, ash)}
    board = call("/api/trajectories", {"workbook": str(wren)})
    wc = next(c for c in board["participants"] if c["case"] == "P1 - Wren")
    g1, g2 = (next(r for r in wc["rows"] if r["id"] == g) for g in ("G1", "G2"))
    own1 = [q["key"] for q in g1["cells"]["T2"]["choices"]]
    own2 = [q["key"] for q in g2["cells"]["T2"]["choices"]]
    at_t2 = [q["key"] for q in wc["quotes"]["T2"]]
    check("369: the board gives each participant every quote of each interview, those of a cell's own LPET and of "
          "another's alike, in transcript order, and none where they were not interviewed",
          len(own1) == 2 and len(own2) == 1 and at_t2 == own1 + own2 and wc["quotes"]["T3"] == []
          and all(q["source"] == "lpet" for q in g1["cells"]["T2"]["choices"]), str(wc["quotes"])[:400])

    # an own quote ticked reads as from the LPET
    cell = g1["cells"]["T2"]
    check("369: a quote of the LPET's own ticked reads with its source, lpet", cell["chosen"] is True
          and cell["quote"]["source"] == "lpet", str(cell["quote"]))

    # the participant's other quote from that interview, a statement in another LPET
    other = own2[0]
    tick = [{"op": "quote", "participant": "Wren", "lpet": "G1", "timepoint": "T2", "quote": other}]
    lp_before = wren_lp.read_bytes()
    dry = call("/api/trajectories-ops", {"workbook": str(wren), "dry_run": True, "ops": tick})
    check("369: a quote from elsewhere in the interview in a dry run says so and writes nothing",
          dry["changes"] == ["Wren's 'Asking next door took the place of the packet' at T2: key quote ticked."]
          and wren_lp.read_bytes() == lp_before, str(dry["changes"]))
    call("/api/trajectories-ops", {"workbook": str(wren), "ops": tick})
    again = call("/api/trajectories", {"workbook": str(wren)})
    c1, c2 = wren_row(again, "G1")["cells"]["T2"], wren_row(again, "G2")["cells"]["T2"]
    lt = call("/api/gets", {"workbook": str(wren), "lpets": True})
    check("369: ticked, it is G1's key quote at T2 after a reload, shown as an own one without its marks, read "
          "from elsewhere in the interview, the LPETs screen's tick the same, and no statement moved: G1 and G2 offer "
          "the quotes they did, the workbooks untouched",
          c1["chosen"] is True and c1["quote"]["key"] == other and c1["quote"]["source"] == "interview"
          and c1["quote"]["text"] == "Under the sacks there were forks older than me."
          and lt["rows"]["G1"]["T2"]["quote"] == other
          and [q["key"] for q in c1["choices"]] == own1 and [q["key"] for q in c2["choices"]] == own2
          and all(p.read_bytes() == v for p, v in books.items()), str(c1)[:400])
    done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": [
        {"op": "bold", "participant": "Wren", "lpet": "G1", "timepoint": "T2", "spans": [[0, 5]]}]})
    c1 = wren_row(done, "G1")["cells"]["T2"]
    _held, src = kept_board()
    check("369: bold on a quote from elsewhere is kept on its words, against the quote as the workbook keeps it, "
          "the tick unchanged", c1["bold"] == [[0, 5]] and c1["quote"]["text"][0:5] == "Under"
          and c1["quote"]["key"] == other and src["rows"]["G1"]["T2"] == {"quote": other, "note": src["rows"]["G1"]["T2"]["note"],
                                                                        "bold": [[1, 6]]}, str(src["rows"].get("G1")))
    said = refused({"workbook": str(wren), "ops": [dict(tick[0], quote=g1["cells"]["T1"]["choices"][0]["key"])]})
    said2 = refused({"workbook": str(wren), "ops": [dict(tick[0], quote="Midsummer:99:0")]})
    check("369: a quote of another interview, or one not there, is refused, nothing written",
          "not a quote of Wren's interview at T2" in said and "not a quote of" in said2, said + " | " + said2)

    # a passage of the transcript: the participant's turns at an interview, the interviewer's left out
    turns = call("/api/trajectories-turns", {"workbook": str(wren), "participant": "Wren", "timepoint": "T1"})
    w1 = said_rows(wren, "Before", "Wren")
    shed = next(t for t in turns["turns"] if "looked inside" in t["text"])
    check("369: the turns route gives Wren's turns at T1 alone, each with its sheet and row, the interviewer's left "
          "out, and the interviews she has a transcript at",
          [t["turn"] for t in turns["turns"]] == [f"Before:{w1[0]}", f"Before:{w1[1]}"]
          and turns["interviews"] == ["T1", "T2"] and shed["text"].strip() == "I had not looked inside it yet.",
          str(turns)[:400])
    at = shed["text"].index("ooked")
    passage = {"interview": "Before the season", "turn": shed["turn"], "start": at, "end": at + len("ooked inside it")}
    take = [{"op": "quote", "participant": "Wren", "lpet": "G2", "timepoint": "T2", "passage": passage}]
    lp_before = wren_lp.read_bytes()
    dry = call("/api/trajectories-ops", {"workbook": str(wren), "dry_run": True, "ops": take})
    check("369: a passage of another interview in a dry run says where it comes from and writes nothing",
          dry["changes"] == [f"Wren's 'The shed became a room of her own' at T2: key quote ticked from the transcript, "
                             f"T1, {shed['time']}."] and wren_lp.read_bytes() == lp_before, str(dry["changes"]))
    call("/api/trajectories-ops", {"workbook": str(wren), "ops": take})
    again = call("/api/trajectories", {"workbook": str(wren)})
    c2 = wren_row(again, "G2")["cells"]["T2"]
    _held, src = kept_board()
    kept_row = src["rows"]["G2"]["T2"]
    check("369: taken, the passage is G2's key quote at T2 after a reload, widened to whole words, its time cited "
          "with T1 as it is another interview's, kept on the LPET table's row with its words, his bold of the quote "
          "before it gone, and no workbook written",
          c2["chosen"] is True and c2["quote"]["source"] == "transcript" and c2["quote"]["text"] == "looked inside it"
          and c2["quote"]["at"] == "T1" and c2["quote"]["time"] == f"T1, {shed['time']}" and c2["bold"] == []
          and c2["quote"]["passage"] == {"at": "T1", "turn": shed["turn"], "start": at - 1, "end": at - 1 + len("looked inside it")}
          and kept_row.get("quote") == "" and kept_row.get("passage", {}).get("text") == "looked inside it"
          and "bold" not in kept_row and all(p.read_bytes() == v for p, v in books.items()), f"{c2} {kept_row}")
    done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": [
        {"op": "bold", "participant": "Wren", "lpet": "G2", "timepoint": "T2", "spans": [[0, 6]]}]})
    c2 = wren_row(done, "G2")["cells"]["T2"]
    _held, src = kept_board()
    check("369: bold on a passage is kept on the row with the passage, which stays ticked",
          c2["bold"] == [[0, 6]] and c2["quote"]["source"] == "transcript" and src["rows"]["G2"]["T2"].get("bold") == [[0, 6]]
          and src["rows"]["G2"]["T2"].get("passage", {}).get("turn") == shed["turn"], str(src["rows"].get("G2")))
    # the LPETs screen's own save sends the rows back as it holds them, the passage with them
    lp = call("/api/gets", {"workbook": str(wren), "lpets": True})
    version = dict(lp["version"], cards={c["key"]: {"x": c["x"], "y": c["y"]} for c in lp["cards"]},
                   groups=lp["groups"], rows=lp["rows"], discarded=[], picks={}, notes=[])
    call("/api/gets-save", {"workbook": str(wren), "lpets": True, "version": version})
    c2 = wren_row(call("/api/trajectories", {"workbook": str(wren)}), "G2")["cells"]["T2"]
    check("369: a save of the LPETs board keeps the passage and its bold", c2["quote"]["source"] == "transcript"
          and c2["bold"] == [[0, 6]], str(c2)[:300])

    # the whole turn, the cell's own interview
    whole = [{"op": "quote", "participant": "Wren", "lpet": "G1", "timepoint": "T1",
              "passage": {"interview": "T1", "turn": f"Before:{w1[0]}"}}]
    done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": whole})
    c = wren_row(done, "G1")["cells"]["T1"]
    check("369: a whole turn of the cell's own interview taken without a start or an end, the bold before it gone",
          c["quote"]["text"] == "Tidy rows, like the seed packets." and c["quote"]["at"] == "T1" and c["bold"] == [], str(c))

    # the refusals, each writing nothing
    lp_before = wren_lp.read_bytes()
    said = {
        "T3": refused({"workbook": str(wren), "ops": [dict(take[0], passage=dict(passage, interview="T3"))]}),
        "T9": refused({"workbook": str(wren), "ops": [dict(take[0], passage=dict(passage, interview="T9"))]}),
        "turn": refused({"workbook": str(wren), "ops": [dict(take[0], passage=dict(passage, turn="Before:99"))]}),
        "other": refused({"workbook": str(wren), "ops": [dict(take[0], passage=dict(passage, turn="Midsummer:3"))]}),
        "span": refused({"workbook": str(wren), "ops": [dict(take[0], passage=dict(passage, start=0, end=999))]}),
        "blank": refused({"workbook": str(wren), "ops": [dict(take[0], passage=dict(passage, start=1, end=1))]}),
        "both": refused({"workbook": str(wren), "ops": [dict(take[0], quote=other)]}),
        "shape": refused({"workbook": str(wren), "ops": [dict(take[0], passage="T1")]}),
    }
    check("369: a passage at an interview she has no transcript at, a timepoint not there, a turn not in that "
          "interview, a span past the turn's words or with none, a quote and a passage at once, and a passage that is "
          "not one are each refused, nothing written",
          "Wren has no transcript at T3" in said["T3"] and "not one of the project's timepoints" in said["T9"]
          and "Before:99 is not a turn of Wren's transcript at T1" in said["turn"] and "is not a turn of" in said["other"]
          and "from 0 to" in said["span"] and "from 0 to" in said["blank"] and "not both" in said["both"]
          and "A passage is its interview" in said["shape"] and wren_lp.read_bytes() == lp_before, str(said))

    # the command line: trajectories show lists each cell's choices with their source, and the op's passage form
    code, shown, err = run("trajectories", "show")
    wrc = next((c for c in shown.get("participants") or [] if c["case"] == "P1 - Wren"), {})
    cg1 = next((r for r in wrc.get("rows") or [] if r["id"] == "G1"), {}).get("cells", {}).get("T2", {})
    sources = [(q["key"], q["source"], q.get("lpet")) for q in cg1.get("choices") or []]
    check("369: trajectories show gives each cell's choices, the LPET's own then the others of that interview with "
          "the LPET each sits in, and its key quote's source",
          code == 0 and sources == [(own1[0], "lpet", None), (own1[1], "lpet", None), (other, "interview", "G2")]
          and cg1["quote"]["source"] == "interview" and "quotes" not in wrc, (err or "") + str(sources))
    tool = next(t for t in mcp_server.TOOLS if t["name"] == "trajectories_apply")
    check("369: the MCP server's trajectories_apply names the passage form", '"passage"' in tool["description"]
          and "interview" in tool["description"])
    # a statement in no LPET: the shed's PET at T1 taken out of G2 on the LPETs board, its quote still offered
    lp = call("/api/gets", {"workbook": str(wren), "lpets": True})
    groups = [dict(g, members=[m for m in g["members"] if not (g["id"] == "G2" and m.startswith("T1/"))]) for g in lp["groups"]]
    version = dict(lp["version"], cards={c["key"]: {"x": c["x"], "y": c["y"]} for c in lp["cards"]},
                   groups=groups, rows=lp["rows"], discarded=[], picks={}, notes=[])
    call("/api/gets-save", {"workbook": str(wren), "lpets": True, "version": version})
    shed_key = next(q["key"] for q in wc["quotes"]["T1"] if "looked inside" in q["text"])
    code, shown, err = run("trajectories", "show")
    wrc = next((c for c in shown.get("participants") or [] if c["case"] == "P1 - Wren"), {})
    t1 = {r["id"]: r["cells"]["T1"] for r in wrc.get("rows") or []}
    tick_none = [{"op": "quote", "participant": "Wren", "lpet": "G1", "timepoint": "T1", "quote": shed_key}]
    done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": tick_none})
    c = wren_row(done, "G1")["cells"]["T1"]
    check("369: a statement's quote in no LPET is offered to every LPET's cell at that timepoint, its LPET none, and "
          "ticked from there, the passage before it put aside",
          code == 0 and "G2" in t1 and not [q for q in t1["G2"]["choices"] if q["source"] == "lpet"]
          and (shed_key, "interview", None) in [(q["key"], q["source"], q.get("lpet")) for q in t1.get("G1", {}).get("choices") or []]
          and c["chosen"] is True and c["quote"]["key"] == shed_key and c["quote"]["source"] == "interview",
          (err or "") + str(t1)[:400] + str(c)[:200])

    # an edit that moves the passage's words keeps them, and one that takes them away falls back to the first
    row = int(shed["turn"].rsplit(":", 1)[1])
    wb_mod.edit_turn(wren, "Before", row, "Honestly, I had not looked inside it yet.")
    c2 = wren_row(call("/api/trajectories", {"workbook": str(wren)}), "G2")["cells"]["T2"]
    moved = c2["quote"].get("passage") or {}
    wb_mod.edit_turn(wren, "Before", row, "I had not opened it yet.")
    c2b = wren_row(call("/api/trajectories", {"workbook": str(wren)}), "G2")["cells"]["T2"]
    check("369: a turn edited around the passage keeps it on the same words, and one whose words are gone falls "
          "back to the first quote standing in, as a lost quote does",
          c2["chosen"] is True and c2["quote"]["text"] == "looked inside it" and moved.get("start") == len("Honestly, I had not ")
          and c2b["chosen"] is False and c2b["quote"]["source"] == "lpet" and c2b["quote"]["key"] == own2[0]
          and c2b["bold"] == [], f"{c2} {c2b}")


def _survives_rename(call, run, garden: Path, cfg_file: Path, wren: Path):
    """Everything Wren has on Trajectories kept through a rename (renamefix, 11 November 2026, found by pbiodraw: the
    board keys a participant by their label and a rename left it behind): MCP's rename with the folder kept, then the
    command line's with it ticked, which moves her LPETs, her PETs boards at T2 and her picture with her workbook."""
    import gets as gets_mod
    import mcp_server
    import project_history as hist_mod
    import themes as themes_mod
    import trajectories as traj_mod

    import participants as people_mod
    pics = people_mod.pictures_of(garden)
    tfile = garden / traj_mod.FILE
    face = garden.parent / "a369-rename-face.png"
    face.write_bytes(traj_mod.png_write(2, 2, bytearray(b"\x40\x80\x20\xff" * 4)))
    call("/api/trajectories-ops", {"workbook": str(wren), "ops": [
        {"op": "picture", "participant": "Wren", "from": str(face)}, {"op": "hide", "participant": "Wren", "lpet": "G2"},
        {"op": "note", "participant": "Wren", "note": "Asks next door first"}]})

    def kept(book: Path, case: str) -> dict:
        """What a participant has on the board, by its meaning, their picture by its bytes."""
        board = call("/api/trajectories", {"workbook": str(book)})
        card = next(c for c in board["participants"] if c["case"] == case)
        col = next((c for c in board["columns"] if case in c["participants"]), None)
        pic = card["picture"]
        rows = [dict({k: r.get(k) for k in ("id", "title", "domain", "shown")},
                     cells={t: dict({k: c.get(k) for k in ("state", "chosen", "bold", "missing")},
                                    quote=(c.get("quote") or {}).get("text"), key=(c.get("quote") or {}).get("key"))
                            for t, c in r["cells"].items()})
                for r in card["rows"]]
        return dict({k: card.get(k) for k in ("column", "note", "title", "tags", "hidden", "colour", "lpets")},
                    picture=(pics / pic).read_bytes() if pic and not pic.startswith("set:") else pic, rows=rows,
                    at=col["participants"].index(case) if col else None, unplaced=case in board["unplaced"])

    before = kept(wren, "P1 - Wren")
    check("369: before the rename Wren has her own picture, a title, tags, a note, an LPET hidden and her rows with "
          "their states and key quotes", isinstance(before["picture"], bytes) and before["title"] and before["tags"]
          and before["note"] and before["hidden"] and any(c["state"] for r in before["rows"] for c in r["cells"].values()),
          str({k: v for k, v in before.items() if k != "picture"})[:400])

    # MCP's rename, the folder kept
    srv = mcp_server.Server(str(garden), config=str(cfg_file))
    srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                            "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))

    def tool(tool_name, **given):
        return srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                       "params": {"name": tool_name, "arguments": given}}))["result"]
    t_before = tfile.read_bytes()
    dry = tool("participant_rename", case="Wren", name="Robin", folder=False, dry_run=True, request="She chose a new pseudonym")
    dry_said = json.dumps(support.plain(dry.get("structuredContent") or {}))
    check("369: MCP's rename in a dry run lists the Trajectories board and writes nothing",
          not dry["isError"] and "The Trajectories board" in dry_said and tfile.read_bytes() == t_before, dry_said[:400])
    res = tool("participant_rename", case="Wren", name="Robin", folder=False, request="She chose a new pseudonym")
    after = kept(wren, "P1 - Robin")
    held = json.loads(tfile.read_text(encoding="utf-8"))
    check("369: renamed by MCP with the folder kept, everything Wren had on Trajectories is Robin's: her trajectory and "
          "her place in its order, her label, tags, note, picture, hidden LPET, colour and every row's state, key quote "
          "and bold, the file naming her old label nowhere",
          not res["isError"] and after == before and "P1 - Wren" not in json.dumps(held["placed"])
          and "P1 - Wren" not in json.dumps(held["columns"]),
          json.dumps(support.plain(res.get("structuredContent") or {}))[:300] + str(after == before))

    # the command line's, the folder ticked: her folder, workbook, LPETs, PETs boards and picture move
    t_before = tfile.read_bytes()
    code, dry, err = run("participant", "rename", "Robin", "Linnet", "--folder", "--dry-run")
    folder_said = " ".join(dry.get("folder_changes") or [])
    check("369: the command line's dry run with --folder lists the Trajectories board and her picture taking the new "
          "name, her workbook keeping its LPETs, and writes nothing",
          code == 0 and "The Trajectories board" in dry.get("changes", []) and "picture" in folder_said
          and "LPETs" in folder_said and tfile.read_bytes() == t_before and (garden / "P1 - Wren").is_dir(),
          (err or "") + str(dry)[:400])
    code, done, err = run("participant", "rename", "Robin", "Linnet", "--folder", "--note", "Her folder too")
    linnet = garden / "P1 - Linnet" / "P1 Linnet - EN & ES.xlsx"
    moved = kept(linnet, "P1 - Linnet") if code == 0 and linnet.is_file() else {}
    working = sorted(p.name for p in (linnet.parent / "Working").iterdir()) if linnet.is_file() else []
    check("369: renamed by the command line with --folder, everything is Linnet's still, her picture's file named "
          "after her now, her LPETs and her PETs boards at T2 moved with her workbook and nothing left under the old "
          "name",
          code == 0 and moved == before and not (garden / "P1 - Wren").exists()
          and (pics / "Linnet.png").is_file() and not (pics / "Wren.png").exists()
          and json.loads((garden / "idiograph-project.json").read_text(encoding="utf-8"))["participants"]["P1 - Linnet"]["picture"] == "Linnet.png"
          and gets_mod.lpets_path(linnet).is_file() and themes_mod.themes_path(linnet, 2).is_file()
          and not [n for n in working if n.startswith("P1 Wren")],
          (err or "") + str(working) + str({k: v for k, v in moved.items() if k != "picture"})[:300])
    record = hist_mod.load(garden)[-1]
    check("369: the project's History keeps the rename with its Trajectories line and its picture's",
          record["op"] == "participant rename" and "The Trajectories board." in record["changes"]
          and any("picture" in x for x in record["changes"]), str(record)[:400])


KEYS_DRIVER = r"""
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const say = () => {}; const SENT = [];
const pathProjectDraw = () => {}; const dsTabsDraw = () => {}; const dsTabsWatch = () => {};
const needsRestart = () => false; const RESTART_LINE = '';
const TURNS = { turns: [{ turn: 'Before:3', time: '03:12', text: 'I had tidy rows in my head and a shed I never opened.' },
  { turn: 'Before:5', time: '35:55', text: 'The neighbour told me the shed was mine.' }], interviews: ['T1', 'T2'] };
const ASKED = [];
const api = async (path, body) => {
  if (path === '/api/trajectories-turns') { ASKED.push(body); return JSON.parse(JSON.stringify(TURNS)); }
  SENT.push(body.ops || body); return JSON.parse(JSON.stringify(DATA));
};
const cell = (q, key, chosen, bold) => ({ state: 'A state', chosen, bold, missing: false,
  quote: q ? { key, text: q, time: 'T1, 03:12' } : null, choices: q ? [{ key, text: q, time: '03:12' }, { key: key + 'b', text: 'Another', time: '04:00' }] : [] });
const row = (id, title) => ({ id, title, domain: 'Practical, Town', domains: [{ word: 'Practical', colour: 3 }, { word: 'Town', colour: 5 }], shown: true,
  cells: { T1: cell('I had tidy rows in my head', 'Before:3:0', false, []), T2: cell('', '', false, []), T3: cell('I ask first', 'Harvest:2:0', true, [[0, 1]]) } });
const DATA = { project: null, demo: false, unplaced: [], note: 'A credit line', config: { traj_quotes: 'short', traj_notes: false },
  timepoints: [{ n: 1, label: 'T1', description: 'Before the season' }, { n: 2, label: 'T2', description: 'Midsummer' }, { n: 3, label: 'T3', description: 'After the harvest' }],
  palette: { good: 'Green' }, faces: ['peep01'],
  columns: [{ id: 'c1', title: 'Positive', colour: 'good', icon: 'rising', participants: ['P1 - Wren', 'P2 - Ash'] },
    { id: 'c2', title: 'Mixed', participants: ['P3 - Fern'] }],
  participants: [['P1 - Wren', 'Wren', 'c1'], ['P2 - Ash', 'Ash', 'c1'], ['P3 - Fern', 'Fern', 'c2']].map((p, i) => ({ case: p[0], who: p[1], colour: i,
    column: p[2], note: '', title: 'A label', tags: [{ word: 'Town', colour: 3 }], picture: '', picture_url: '', lpets: ['Asking next door'],
    rows: [row('G1', 'Asking next door')],
    // every quote of each interview, the cell's own and one from elsewhere (trajchoose)
    quotes: { T1: [{ key: 'Before:3:0', text: 'I had tidy rows in my head', time: 'T1, 03:12' }, { key: 'Before:7:0', text: 'A quote from elsewhere', time: 'T1, 07:40' }],
      T2: [], T3: [] } })) };
// Fern's key quote at T3 a passage of T1's transcript
DATA.participants[2].rows[0].cells.T3 = { state: '', chosen: true, bold: [], missing: false, choices: [],
  quote: { key: '', text: 'Everyone came', time: 'T1, 05:00', source: 'transcript', at: 'T1', passage: { at: 'T1', turn: 'Before:9', start: 0, end: 13 } } };
"""

KEYS_AFTER = r"""
const out = {};
const key = (el, k, more = {}) => el.dispatchEvent(new KeyboardEvent('keydown', Object.assign({ key: k, bubbles: true }, more)));
const settle = () => new Promise((r) => setTimeout(r, 50));
const run = async () => {
  document.getElementById('traj').hidden = false;
  TJ.path = 'x'; TJ.sideOpen = false;
  trajLoad(JSON.parse(JSON.stringify(DATA)));
  const p = (c) => document.querySelector(`.tf-pcell[data-case="${c}"]`);
  out.noteOff = document.getElementById('tj-board-note').hidden;
  out.bands = [...document.querySelectorAll('.tf-band')].map((b) => b.dataset.col);
  out.heads = [...document.querySelectorAll('.tf-band[data-col="c1"] .tf-th:not(.tf-th0)')].map((h) => h.textContent);
  out.auto = !!document.querySelector('.tf-q.tf-q-auto');
  out.noQuote = document.querySelectorAll('.tf-q-none').length;
  out.bold = document.querySelector('.tf-band[data-col="c1"] .tf-qtext b') ? document.querySelector('.tf-band[data-col="c1"] .tf-qtext b').textContent : '';
  out.domains = [...document.querySelector('.tf-lpet').querySelectorAll('.tf-pill')].map((el) => `${el.textContent} ${[...el.classList].find((c) => c.startsWith('case-'))}`);
  key(p('P2 - Ash'), 'ArrowUp'); await settle();
  key(p('P1 - Wren'), 'ArrowRight'); await settle();
  key(p('P3 - Fern'), 'Backspace'); await settle();
  // Cmd+B on 'tidy rows' of Wren's T1 quote, the first standing in
  const q = document.querySelector('.tf-qtext[data-qcell="P1 - Wren|G1|T1"]');
  const r = document.createRange(); r.setStart(q.firstChild, 6); r.setEnd(q.firstChild, 15);
  getSelection().removeAllRanges(); getSelection().addRange(r);
  key(q, 'b', { metaKey: true }); await settle();
  // the chooser: a click on the quote opens it, a tick sends the quote op
  document.querySelector('.tf-q[data-cell="P1 - Wren|G1|T1"]').click(); await settle();
  out.choices = document.querySelectorAll('.tf-choose .tf-choose-part:first-child .tf-choice').length;
  document.querySelectorAll('.tf-choose .tf-choice')[1].click(); await settle();
  key(document.querySelector('.tf-q[data-cell="P1 - Wren|G1|T3"]'), 'Enter'); await settle();
  out.chooserAgain = document.querySelectorAll('.tf-choose .tf-choose-part:first-child .tf-choice').length;
  document.querySelector('.tf-choose .tf-choice.on').click(); await settle();
  // the drop's place in a band: above Ash's middle is place 0
  const band = document.querySelector('.tf-band[data-col="c1"]');
  const ash = p('P2 - Ash').getBoundingClientRect();
  out.dropTop = trajDropAt(band, ash.top + 2, 'P3 - Fern');
  out.dropEnd = trajDropAt(band, ash.bottom + 400, 'P3 - Fern');
  // the board's note: shown once Notes is on, typed in place, Enter keeping it
  TJ.data.config.traj_notes = true; trajDraw();
  const note = document.getElementById('tj-board-note');
  out.noteOn = !note.hidden && note.value === 'A credit line' && note.getBoundingClientRect().height > 0;
  note.focus(); note.value = 'Pictures by a friend'; key(note, 'Enter'); await settle();
  // trajchoose: the chooser's three parts in his order, a quote from elsewhere ticked, and the passage picker
  TJ.data.config.traj_notes = false; trajDraw();
  const open = async (id) => { document.querySelector(`.tf-q[data-cell="${id}"]`).click(); await settle(); };
  await open('P1 - Wren|G1|T1');
  out.parts = [...document.querySelectorAll('.tf-choose .tf-choose-h')].map((h) => h.textContent);
  out.order = [...document.querySelectorAll('.tf-choose [data-qkey]')].map((b) => b.dataset.qkey);
  document.querySelector('.tf-choose [data-qkey="Before:7:0"]').click(); await settle();
  // a cell with no quote opens the chooser too, its transcript part alone
  await open('P2 - Ash|G1|T2');
  out.partsNone = [...document.querySelectorAll('.tf-choose .tf-choose-h')].map((h) => h.textContent);
  document.querySelector('.tf-q[data-cell="P2 - Ash|G1|T2"]').click(); await settle();
  // a passage of another interview shows its timepoint before its time, an own quote its time alone
  out.passTime = document.querySelector('.tf-q[data-cell="P3 - Fern|G1|T3"] .tf-time').textContent;
  out.ownTime = document.querySelector('.tf-q[data-cell="P1 - Wren|G1|T1"] .tf-time').textContent;
  // Choose a passage... opens the picker on the cell's own interview
  await open('P1 - Wren|G1|T1');
  document.querySelector('.tf-choose [data-passage-open]').click(); await settle(); await settle();
  out.asked = ASKED.slice();
  out.tabs = [...document.querySelectorAll('.tf-pass .tf-pass-tp')].map((b) => `${b.textContent}${b.getAttribute('aria-pressed') === 'true' ? '*' : ''}`);
  out.turns = document.querySelectorAll('.tf-pass .tf-turn').length;
  out.inRow = (() => { const p = document.querySelector('.tf-pass'); const q = document.querySelector('.tf-q[data-cell="P1 - Wren|G1|T1"]');
    return !!p && p.getBoundingClientRect().top > q.getBoundingClientRect().bottom; })();
  const find = document.querySelector('.tf-pass-find');
  find.value = 'NEIGHBOUR'; find.dispatchEvent(new Event('input', { bubbles: true })); await settle();
  out.found = [...document.querySelectorAll('.tf-pass .tf-turn-w')].map((w) => w.dataset.turnw);
  out.marked = [...document.querySelectorAll('.tf-pass mark.tf-found')].map((m) => m.textContent);
  out.findKept = document.activeElement === find || document.querySelector('.tf-pass-find') === find;
  find.value = ''; find.dispatchEvent(new Event('input', { bubbles: true })); await settle();
  out.takeOff = document.querySelector('[data-take-words]').disabled;
  const w = document.querySelector('.tf-turn-w[data-turnw="Before:5"]');
  const sel = document.createRange(); sel.setStart(w.firstChild, 4); sel.setEnd(w.firstChild, 13);
  getSelection().removeAllRanges(); getSelection().addRange(sel); await settle();
  out.takeOn = !document.querySelector('[data-take-words]').disabled;
  document.querySelector('[data-take-words]').click(); await settle();
  out.closed = !document.querySelector('.tf-pass');
  // the whole turn, from the other interview's tab
  await open('P2 - Ash|G1|T1');
  document.querySelector('.tf-choose [data-passage-open]').click(); await settle(); await settle();
  document.querySelector('.tf-pass [data-pass-at="T2"]').click(); await settle();
  document.querySelector('.tf-pass [data-whole="Before:3"]').click(); await settle();
  out.sent = SENT;
  document.getElementById('out').textContent = JSON.stringify(out);
};
document.addEventListener('DOMContentLoaded', run);
"""


def _keys_in_browser():
    """The screen's keys in the computer's own browser, the real markup, styles and trajectories.js with the
    server answered by a stand-in that records what is sent: Up moves a participant within their trajectory, Right
    to the next, Backspace to Not placed, Cmd+B on words of a quote standing in sends their spans, a click on a
    quote opens its chooser and a tick sends its key, a tick on the ticked one takes it off, and a drop above a
    participant's middle lands before them. Since trajchoose the chooser's three parts in order, No quote opening
    it, a passage's time cited with its interview, and the passage picker's interviews, find box and two takes."""
    import html as html_mod
    import subprocess
    import tempfile
    exe = support.browser()
    if exe is None:
        support.skip("369: the screen's keys in a real browser", "no Chrome, Chromium, Brave or Edge on this computer")
        return
    page = support.text("apps/idiograph/static/idiograph.html")
    traj = "<section id=\"traj\"" + page.split("<section id=\"traj\"", 1)[1].split("</section>", 1)[0] + "</section>"
    css = "\n".join(support.text(p) for p in ("family/static/tokens.css", "family/static/style.css", "family/static/frame.css",
                                              "apps/idiograph/static/distil.css", "apps/idiograph/static/themes.css"))
    js = support.text("apps/idiograph/static/trajectories.js")
    with tempfile.TemporaryDirectory(prefix="idiograph-369-") as tmp:
        doc = ("<!doctype html><html><head><meta charset=\"utf-8\"><style>" + css + "</style></head><body>" + traj
               + "<pre id=\"out\">none</pre><script>" + support.i18n_js("idiograph") + KEYS_DRIVER + js + KEYS_AFTER
               + "</script></body></html>")
        file = Path(tmp) / "keys.html"
        file.write_text(doc, encoding="utf-8")
        cmd = [str(exe), "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
               "--disable-extensions", "--disable-background-networking", "--password-store=basic", "--use-mock-keychain",
               f"--user-data-dir={Path(tmp) / 'profile'}", "--window-size=1280,1400", "--virtual-time-budget=4000",
               "--dump-dom", file.as_uri()]
        try:
            dumped = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=120).stdout
        except (OSError, subprocess.TimeoutExpired) as err:
            dumped = str(err)
    said = dumped.split('<pre id="out">', 1)[1].split("</pre>", 1)[0] if '<pre id="out">' in dumped else ""
    try:
        out = json.loads(html_mod.unescape(said))
    except ValueError:
        out = {}
    sent = [ops[0] for ops in out.get("sent") or [] if isinstance(ops, list) and ops]
    check("369: in a browser each trajectory is a band with T1, T2 and T3 headed by their descriptions, the quote standing "
          "in drawn fainter, No quote where there is none, and his bold drawn",
          out.get("bands") == ["c1", "c2"] and out.get("heads") == ["T1: Before the season", "T2: Midsummer", "T3: After the harvest"]
          and out.get("auto") is True and out.get("noQuote") == 3 and out.get("bold") == "I", str(out)[:600])
    check("369: in a browser an LPET in two domains shows two pills, each in its own colour (trajfix)",
          out.get("domains") == ["Practical case-3", "Town case-5"], str(out.get("domains")))
    check("369: Up moves a participant within their trajectory, Right to the next, Backspace to Not placed",
          sent[:3] == [{"op": "order", "participant": "P2 - Ash", "at": 0}, {"op": "place", "participant": "P1 - Wren", "column": "c2"},
                       {"op": "place", "participant": "P3 - Fern", "column": None}], str(sent[:3]))
    check("369: Cmd+B on words of the quote standing in sends their spans as its bold",
          len(sent) > 3 and sent[3] == {"op": "bold", "participant": "P1 - Wren", "lpet": "G1", "timepoint": "T1", "spans": [[6, 15]]},
          str(sent[3:4]))
    check("369: a click on a quote opens its chooser and a tick sends that quote's key, Enter opens another, and a tick "
          "on the ticked one takes it off",
          out.get("choices") == 2 and out.get("chooserAgain") == 2 and len(sent) > 5
          and sent[4] == {"op": "quote", "participant": "P1 - Wren", "lpet": "G1", "timepoint": "T1", "quote": "Before:3:0b"}
          and sent[5] == {"op": "quote", "participant": "P1 - Wren", "lpet": "G1", "timepoint": "T3", "quote": ""}, str(sent[4:6]))
    check("369: in a browser the board's note is hidden while Notes is off, shown with its words once it is on, and "
          "typed in place, Enter sending note_board",
          out.get("noteOff") is True and out.get("noteOn") is True and len(sent) > 6
          and sent[6] == {"op": "note_board", "note": "Pictures by a friend"}, str(out)[:300] + str(sent[6:7]))
    check("369: a participant dropped above another's middle goes before them, below every one at the end",
          out.get("dropTop") == 1 and out.get("dropEnd") == 2, str(out)[:300])
    # trajchoose, 11 November 2026
    check("369: in a browser the chooser's parts come in his order, In this LPET, Elsewhere in this interview, From "
          "the transcript, the LPET's own quotes first, and a tick on a quote from elsewhere sends its key",
          out.get("parts") == ["In this LPET", "Elsewhere in this interview", "From the transcript"]
          and out.get("order") == ["Before:3:0", "Before:3:0b", "Before:7:0"] and len(sent) > 7
          and sent[7] == {"op": "quote", "participant": "P1 - Wren", "lpet": "G1", "timepoint": "T1", "quote": "Before:7:0"},
          str(out.get("parts")) + str(out.get("order")) + str(sent[7:8]))
    check("369: a cell with no quote opens the chooser too, From the transcript alone, and a passage of another "
          "interview shows that interview before its time, an own quote its time alone",
          out.get("partsNone") == ["From the transcript"] and out.get("passTime") == "T1, 05:00"
          and out.get("ownTime") == "03:12", str({k: out.get(k) for k in ("partsNone", "passTime", "ownTime")}))
    check("369: Choose a passage opens the picker under the row on the cell's interview, its interviews to switch "
          "between, the find box keeping only the turns with the words and marking them, any case",
          out.get("asked", [{}])[0] == {"workbook": "x", "participant": "P1 - Wren", "timepoint": "T1"}
          and out.get("tabs") == ["T1*", "T2"] and out.get("turns") == 2 and out.get("inRow") is True
          and out.get("found") == ["Before:5"] and out.get("marked") == ["neighbour"] and out.get("findKept") is True,
          str({k: out.get(k) for k in ("asked", "tabs", "turns", "inRow", "found", "marked", "findKept")}))
    check("369: words selected in a turn are taken with Take the words selected, sending the passage's interview, "
          "turn and span, and Take the whole turn on another interview's tab sends the turn alone",
          out.get("takeOff") is True and out.get("takeOn") is True and out.get("closed") is True and len(sent) > 9
          and sent[8] == {"op": "quote", "participant": "P1 - Wren", "lpet": "G1", "timepoint": "T1",
                          "passage": {"interview": "T1", "turn": "Before:5", "start": 4, "end": 13}}
          and sent[9] == {"op": "quote", "participant": "P2 - Ash", "lpet": "G1", "timepoint": "T1",
                          "passage": {"interview": "T2", "turn": "Before:3"}},
          str({k: out.get(k) for k in ("takeOff", "takeOn", "closed")}) + str(sent[8:10]))
