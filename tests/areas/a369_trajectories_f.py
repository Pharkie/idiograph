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
          "own note (trajnote, 10 November 2026)")
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
        wb_mod.save_turn(wren, "Before", w1[1], "Not yet inside the shed", "", "I had not looked inside it yet.")
        wb_mod.save_turn(wren, "Midsummer", w2[0], "Told over the fence\nAsking next door", "",
                         "The man next door just leaned on the fence and told me.\nleaned on the fence")
        wb_mod.save_turn(wren, "Midsummer", w2[1], "Clearing the shed", "", "Under the sacks there were forks older than me.")
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
        pics = traj_mod.pictures_of(garden)
        dry = call("/api/trajectories-ops", {"workbook": str(wren), "dry_run": True, "ops": [
            {"op": "picture", "participant": "Wren", "from": str(source)}]})
        check("369: a picture's dry run writes no file", dry["changes"] == ["Wren's picture changed."] and not pics.exists(),
              str(dry["changes"]))
        done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": [{"op": "picture", "participant": "Wren", "from": str(source)}]})
        kept_pic = pics / "Wren.png"
        pw, ph, _ = traj_mod.png_read(kept_pic.read_bytes()) if kept_pic.exists() else (0, 0, b"")
        wc = next(c for c in done["participants"] if c["case"] == "P1 - Wren")
        check("369: his own picture is kept in the project's trajectories/pictures, a square scaled to 256, the "
              "source left where it was, the page given its address",
              (pw, ph) == (256, 256) and source.read_bytes() == png and wc["picture"] == "Wren.png"
              and wc["picture_url"].startswith("/traj-picture?"), f"{pw}x{ph} {wc.get('picture_url')}")
        done = call("/api/trajectories-ops", {"workbook": str(wren), "ops": [{"op": "picture", "participant": "Wren", "set": "face07"}]})
        wc = next(c for c in done["participants"] if c["case"] == "P1 - Wren")
        check("369: one of the set in its place, the picture before kept in the pictures' _Archive, never deleted",
              wc["picture"] == "set:face07" and wc["picture_url"] == "/faces/face07.svg" and not kept_pic.exists()
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
              and ash_rows and ash_rows[0]["domain"] == "Family" and ash_rows[0]["domain_colour"] is not None
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
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept
    _keys_in_browser()


KEYS_DRIVER = r"""
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const escAttr = (s) => esc(s).replace(/"/g, '&quot;');
const say = () => {}; const SENT = [];
const pathProjectDraw = () => {}; const dsTabsDraw = () => {}; const dsTabsWatch = () => {};
const needsRestart = () => false; const RESTART_LINE = '';
const api = async (path, body) => { SENT.push(body.ops || body); return JSON.parse(JSON.stringify(DATA)); };
const cell = (q, key, chosen, bold) => ({ state: 'A state', chosen, bold, missing: false,
  quote: q ? { key, text: q, time: 'T1, 03:12' } : null, choices: q ? [{ key, text: q, time: '03:12' }, { key: key + 'b', text: 'Another', time: '04:00' }] : [] });
const row = (id, title) => ({ id, title, domain: 'Practical', domain_colour: 3, shown: true,
  cells: { T1: cell('I had tidy rows in my head', 'Before:3:0', false, []), T2: cell('', '', false, []), T3: cell('I ask first', 'Harvest:2:0', true, [[0, 1]]) } });
const DATA = { project: null, demo: false, unplaced: [], note: 'A credit line', config: { traj_quotes: 'short', traj_notes: false },
  timepoints: [{ n: 1, label: 'T1', description: 'Before the season' }, { n: 2, label: 'T2', description: 'Midsummer' }, { n: 3, label: 'T3', description: 'After the harvest' }],
  palette: { good: 'Green' }, faces: ['face01'],
  columns: [{ id: 'c1', title: 'Positive', colour: 'good', icon: 'rising', participants: ['P1 - Wren', 'P2 - Ash'] },
    { id: 'c2', title: 'Mixed', participants: ['P3 - Fern'] }],
  participants: [['P1 - Wren', 'Wren', 'c1'], ['P2 - Ash', 'Ash', 'c1'], ['P3 - Fern', 'Fern', 'c2']].map((p, i) => ({ case: p[0], who: p[1], colour: i,
    column: p[2], note: '', title: 'A label', tags: [{ word: 'Town', colour: 3 }], picture: '', picture_url: '', lpets: ['Asking next door'],
    rows: [row('G1', 'Asking next door')] })) };
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
  out.choices = document.querySelectorAll('.tf-choose .tf-choice').length;
  document.querySelectorAll('.tf-choose .tf-choice')[1].click(); await settle();
  key(document.querySelector('.tf-q[data-cell="P1 - Wren|G1|T3"]'), 'Enter'); await settle();
  out.chooserAgain = document.querySelectorAll('.tf-choose .tf-choice').length;
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
    participant's middle lands before them."""
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
