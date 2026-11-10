"""Area 340: a project written as a REFI-QDA project (.qdpx) for NVivo, ATLAS.ti, MAXQDA and QualCoder (qdpxout, 8
November 2026), and brought back by Idiograph's own import with the same statements, quotes and PETs.

The fixture is a copy of the demo, the IPA one and the thematic analysis one, its three invented participants, made a
project of its own in the scratch folder, and a made-up recording of a few bytes for one of them. The export runs on
the one API: the command line's `project export-qdpx`, the MCP tool and the page's route call `qdpx_export`. Checked:
the dry run writes nothing, the project's files are only read, a file there is never written over, the package is
valid against the standard's Project.xsd (a copy in tests/refi-qda/), and the round trip into a new project gives every
passage's words and speaker, its statements in their order and quotes, its exploratory notes and, in IPA, each
participant's PETs with their descriptions, notes, sub-PETs and statements, the statements set aside, and the GETs as
a GETs board, and in thematic analysis every code on every extract, the code list's descriptions and the themes as a
Themes board. Since qdpxround (9 November 2026) an invented project of two timepoints makes the trip too: an
interviewer note, a recording with an offset, each timepoint's PETs on its own board."""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from collections import Counter
from pathlib import Path

from . import support
from .support import check, skip


def tree(folder: Path) -> dict:
    return {p.relative_to(folder).as_posix(): hashlib.sha1(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file() and not p.name.endswith(".lock")}


def fold(text) -> str:
    import workbook as wb_mod
    return " ".join("".join(wb_mod._fold(c) for c in str(text)).split())


def quote_key(quote) -> str:
    """A quote as the round trip keeps it: its pieces as the transcript has them, the inverted commas and the case aside."""
    import workbook as wb_mod
    return " … ".join(fold(p) for p in wb_mod.quote_pieces(quote))


def passages_of(book: Path) -> list[dict]:
    """Each passage with words, its speaker's role kept apart from the interviewer's name, its time, its statements
    and quotes in their order, and its exploratory notes."""
    import workbook as wb_mod
    out = []
    for sheet in wb_mod.read_case(book)["sheets"]:
        for r in sheet["rows"]:
            if not " ".join(r["text"].split()):
                continue
            out.append({"name": r["name"], "words": " ".join(r["text"].split()), "seconds": r["seconds"],
                        "pairs": [(p["es"], quote_key(p["kq"])) for p in r["pairs"]],
                        "notes": [n for n in r["en"].split("\n") if n.strip()]})
    return out


def pets_of(book: Path, version: dict) -> tuple:
    """A board as the round trip keeps it: each PET in the canvas's order with its title, description and note, and
    inside it each sub-PET the same way and the words of each statement (a stacked one beside its top), and the
    words of every statement in the bin."""
    import themes
    read = themes.read_cards(book)
    v = themes.follow(version, read["cards"], read["quotes"])
    text = {c["key"]: c["text"] for c in read["cards"]}
    by = {g["id"]: g for g in v["groups"]}
    parents = themes.parents_of(v["groups"])
    stacks = v.get("stacks") or {}

    def label(gid):
        inside = []
        for m in by[gid]["members"]:
            if m in by:
                inside.append(label(m))
            else:
                inside += [text.get(k) for k in [m] + list(stacks.get(m) or [])]
        return (by[gid]["label"], themes.description_of(by[gid]), by[gid].get("note") or "",
                tuple(sorted(inside, key=str)))
    tops = themes.canvas_order([g for g in by if g not in parents], by)
    return [label(g) for g in tops], sorted(str(text.get(k)) for k in v.get("discarded") or [])


def project_board(root: Path) -> list:
    """The project's board on the canvas, GETs or Themes, as the round trip keeps it: each label with its title,
    description and note, its sub-labels the same way and its cards by participant, a PET's by its title and an
    extract's by its words."""
    import re
    import gets
    import themes
    data = gets.load(root)
    board = themes.current_version(data)
    by = {g["id"]: g for g in board["groups"]}
    parents = themes.parents_of(board["groups"])
    cases = data.get("cases") or {}

    def card(key):
        k = gets.split_key(key)
        rec = cases.get(k["case"]) or {}
        who = re.sub(r"^P\d+\s*-\s*", "", k["case"])
        if k["kind"] == "group":
            return who, next((p["title"] for p in rec.get("pets") or [] if p["id"] == k["ident"]), "")
        return who, ((rec.get("lines") or {}).get(k["ident"]) or {}).get("text", "")

    def label(gid):
        return (by[gid]["label"], themes.description_of(by[gid]), by[gid].get("note") or "",
                tuple(sorted((label(m) if m in by else card(m) for m in by[gid]["members"]), key=str)))
    return sorted((label(g) for g in by if g not in parents), key=str)


def test_qdpx_export(scratch):
    print("\n340. A project written as a REFI-QDA project (.qdpx), valid against the standard's schema, and brought back "
          "by Idiograph's own import with the same passages, statements, quotes, notes and PETs (8 November)")
    import cli
    import gets
    import make_demo
    import mcp_server
    import qdpx
    import themes

    shipped = support.source("demo")
    agents = {"allowed": True, "at": "2026-11-08T10:00:00+00:00"}

    def project(name: str, demo: Path, recording: bool = False) -> Path:
        root = scratch / name
        shutil.rmtree(root, ignore_errors=True)
        root.mkdir(parents=True)
        held = json.loads((demo / "idiograph-project.json").read_text(encoding="utf-8"))
        held["agents"] = agents
        (root / "idiograph-project.json").write_text(json.dumps(held), encoding="utf-8")
        make_demo.fill(demo / "pristine", root)
        if recording:
            folder = root / "Juno" / "Source" / "Initial" / "Source"
            folder.mkdir(parents=True)
            (folder / "Juno-Initial.m4a").write_bytes(b"an invented recording, not sound" * 64)
        return root

    def empty(name: str, method: str) -> Path:
        root = scratch / name
        shutil.rmtree(root, ignore_errors=True)
        (root / "Imports").mkdir(parents=True)
        (root / "idiograph-project.json").write_text(json.dumps({"name": "Back again", "method": method, "agents": agents}),
                                                     encoding="utf-8")
        return root

    config = scratch / "a340-config.json"
    config.write_text(json.dumps({"interviewer": "", "corpus": "", "gravity_reference": "", "corpus_exclude": []}),
                      encoding="utf-8")

    def run(root: Path, *argv):
        code, out, err = cli.run(["--root", str(root), "--config", str(config), *argv])
        return code, (support.plain(json.loads(out)) if "--json" in argv and out.strip() else out), err

    def trip(root: Path, back: Path, *more) -> tuple[dict, dict, dict]:
        """The export into `back`'s Imports, its dry run read back, and the import of each source as its participant."""
        code, done, err = run(root, "project", "export-qdpx", "--to", str(back / "Imports" / "trip.qdpx"), "--json", *more)
        if code:
            return {"error": err}, {}, {}
        code, dry, err = run(back, "qdpx", "Imports/trip.qdpx", "--dry-run", "--json")
        names = {s["source"]: s["name"].split(" - ")[0] for s in dry.get("sources", [])}
        spec = ",".join(f"{n}={who}" for n, who in names.items())
        code, made, err = run(back, "qdpx", "Imports/trip.qdpx", "--sources", spec, "--pets", "--note", "the round trip", "--json")
        return done, dry, (made if not code else {"error": err})

    def book_of(root: Path, who: str) -> Path:
        found = sorted(root.glob(f"{who}/*EN & ES.xlsx")) or sorted(root.glob(f"P* - {who}/*EN & ES.xlsx"))
        return found[0]

    # ── IPA: the dry run, the write, the refusals
    root = project("a340-ipa", shipped)
    before = tree(root)
    out = scratch / "a340-out"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir()
    code, dry, err = run(root, "project", "export-qdpx", "--dry-run", "--json")
    check("340: a dry run says what the file would hold, every participant, statement, PET and GET, and writes nothing",
          code == 0 and dry["dry_run"] is True and dry["participants"] == ["Juno", "Mabel", "Rowan"]
          and dry["counts"]["statements"] > 100 and dry["counts"]["pets"] == 15 and dry["counts"]["gets"] == 5
          and tree(root) == before and not list(out.iterdir()), err or str(dry)[:400])
    code, done, err = run(root, "project", "export-qdpx", "--to", str(out), "--json")
    package = out / "Living with a dog.qdpx"
    check("340: the export writes <Project name>.qdpx in the folder given and leaves every file of the project as it was",
          code == 0 and package.is_file() and done["path"] == str(package.resolve()) and tree(root) == before,
          err or str(done)[:300])
    code, said, _ = run(root, "project", "export-qdpx", "--to", str(package), "--json")
    check("340: a file there already is never written over", code == 1 and "already" in said.get("error", ""), str(said))
    code, said, _ = run(root, "project", "export-qdpx", "--to", str(out / "one.qdpx"), "--participant", "Nobody", "--json")
    check("340: a participant the project does not have is refused, nothing written",
          code == 1 and "Nobody" in said.get("error", "") and not (out / "one.qdpx").exists(), str(said))
    code, one, err = run(root, "project", "export-qdpx", "--to", str(out / "one"), "--participant", "Mabel", "--json")
    with zipfile.ZipFile(out / "one.qdpx") as z:
        one_sources = [n for n in z.namelist() if n.startswith("Sources/")]
    check("340: the participants named alone, the file named without .qdpx given it",
          code == 0 and one["participants"] == ["Mabel"] and len(one_sources) == 1, err or str(one)[:300])

    # the package as the standard sets it out, and as the reader takes it
    try:
        from lxml import etree
    except ImportError:
        etree = None
    with zipfile.ZipFile(package) as z:
        names = z.namelist()
        qde = z.read("project.qde")
    if etree is None:
        skip("340: the package is valid against Project.xsd", "lxml is not installed")
    else:
        schema = etree.XMLSchema(etree.parse(str(support.source("tests/refi-qda/Project.xsd"))))
        valid = schema.validate(etree.fromstring(qde))
        check("340: project.qde is valid against the REFI-QDA standard's Project.xsd",
              valid, "; ".join(str(e) for e in schema.error_log)[:600])
    read = qdpx.read_package(package)
    set_names = [s["name"] for s in read["sets"]]
    board = themes.current_version(themes.load(book_of(root, "Juno")))
    juno_pets = [g["label"] for g in themes.normalise(board)["groups"] if g["id"] not in themes.parents_of(themes.normalise(board)["groups"])]
    gets_board = themes.current_version(gets.load(root))
    check("340: each interview a text source in Sources, the participants cases, each PET and each GET a set",
          names[0] == "project.qde" and len([n for n in names if n.endswith(".txt")]) == 3
          and [c["name"] for c in read["cases"]] == ["Juno", "Mabel", "Rowan"]
          and set(juno_pets) <= set(set_names) and all(g["label"] in set_names for g in gets_board["groups"]
                                                       if g["id"] not in themes.parents_of(gets_board["groups"])),
          str(set_names)[:400])
    tops = [c for c in read["codes"].values() if c["parent"] is None]
    check("340: the codebook holds each participant as a code that cannot be coded, its PETs inside, each statement a "
          "code that can",
          [c["name"] for c in tops] == ["Juno", "Mabel", "Rowan"] and not any(c["codable"] for c in tops)
          and sum(1 for c in read["codes"].values() if c["codable"]) == done["counts"]["statements"], str(tops)[:300])

    # ── IPA round trip
    back = empty("a340-ipa-back", "ipa")
    done, dry, made = trip(root, back)
    check("340: Idiograph's own import reads its export as Idiograph's, every source one participant's interview",
          dry.get("package") == "Idiograph" and len(dry.get("sources", [])) == 3 and made.get("written")
          and len(made["written"]) == 3, str(made)[:300])
    same = {"words": True, "speakers": True, "times": True, "pairs": True, "notes": True, "pets": True}
    for who in ("Juno", "Mabel", "Rowan"):
        a, b = book_of(root, who), book_of(back, who)
        pa, pb = passages_of(a), passages_of(b)
        same["words"] &= [p["words"] for p in pa] == [p["words"] for p in pb]
        # the interviewer comes back under the name Settings gives him, so speakers are compared by their turns
        same["speakers"] &= sorted(Counter(p["name"] for p in pa).values()) == sorted(Counter(p["name"] for p in pb).values())
        same["times"] &= [p["seconds"] for p in pa] == [p["seconds"] for p in pb]
        same["pairs"] &= [p["pairs"] for p in pa] == [p["pairs"] for p in pb]
        same["notes"] &= [p["notes"] for p in pa] == [p["notes"] for p in pb]
        da, db = themes.load(a), themes.load(b)
        same["pets"] &= pets_of(a, gets.source_board(da)[0]) == pets_of(b, themes.current_version(db))
    check("340: the round trip gives every passage's words, speaker and time as they were", same["words"] and same["speakers"]
          and same["times"], str(same))
    check("340: and every experiential statement with its quote, a statement with no quote coming back with none",
          same["pairs"], str(same))
    check("340: and every exploratory note on its passage", same["notes"], str(same))
    check("340: and each participant's PETs, on a board From Idiograph, in the canvas's order, each with its "
          "description, its note and its statements, each sub-PET inside its PET the same way, and the statements set "
          "aside back in the bin (qdpxround)", same["pets"], str(same))
    check("340: and the GETs as a new board on the GETs canvas, each GET with its description and note holding the "
          "same PETs of the same participants (qdpxround)",
          project_board(back) == project_board(root) and len(project_board(back)) == 5,
          str(project_board(back))[:400])

    # ── a recording goes in when asked, and comes back to the player with the times
    root = project("a340-rec", shipped, recording=True)
    back = empty("a340-rec-back", "ipa")
    done, dry, made = trip(root, back, "--recordings")
    copied = list(back.glob("P* - Juno/Source/*/Source/*.m4a"))
    sent = root / "Juno" / "Source" / "Initial" / "Source" / "Juno-Initial.m4a"
    check("340: with the recordings asked for, an interview with a recording is an audio source holding its transcript, "
          "and the import copies the recording in with every passage's time",
          done.get("counts", {}).get("recordings") == 1 and len(copied) == 1 and copied[0].read_bytes() == sent.read_bytes()
          and [p["seconds"] for p in passages_of(book_of(root, "Juno"))] == [p["seconds"] for p in passages_of(book_of(back, "Juno"))],
          str(done)[:300] + str(copied))

    # ── the MCP tool, on the same function
    agent_out = scratch / "a340-mcp"
    shutil.rmtree(agent_out, ignore_errors=True)
    agent_out.mkdir()
    mcp = mcp_server.Server(root=str(root), config=str(config))
    tool = mcp.by_name.get("project_export_qdpx")
    res = mcp.call(tool, {"to": str(agent_out), "dry_run": True}) if tool else {"isError": True}
    said = support.plain(res.get("structuredContent") or {}) if not res.get("isError") else {}
    res2 = mcp.call(tool, {"to": str(agent_out), "participants": ["Rowan"]}) if tool else {"isError": True}
    check("340: the MCP tool project_export_qdpx runs the same export, its dry run writing nothing",
          tool is not None and said.get("dry_run") is True and not res2.get("isError")
          and [p.name for p in agent_out.iterdir()] == ["Living with a dog.qdpx"], str(res)[:300] + str(res2)[:300])

    # ── thematic analysis: codes once for the project, on every extract, the themes holding them
    root = project("a340-ta", shipped / "ta")
    back = empty("a340-ta-back", "ta")
    done, dry, made = trip(root, back)
    read = qdpx.read_package(back / "Imports" / "trip.qdpx")
    import codes as codes_mod
    listed = codes_mod.load(root)["codes"]
    themes_board = themes.current_version(gets.load(root))
    top_themes = [g["label"] for g in themes_board["groups"] if g["id"] not in themes.parents_of(themes_board["groups"])]
    codable = {c["name"] for c in read["codes"].values() if c["codable"]}
    check("340: in a thematic analysis project each code of the code list is one code, the themes codes holding them and "
          "each theme a set",
          codable == {c["name"] for c in listed} and [s["name"] for s in read["sets"]] == top_themes
          and done["counts"]["themes"] == len(top_themes), str(sorted(codable))[:300])
    ok = True
    for who in ("Juno", "Mabel", "Rowan"):
        pa, pb = passages_of(book_of(root, who)), passages_of(book_of(back, who))
        ok &= [p["words"] for p in pa] == [p["words"] for p in pb] and [p["pairs"] for p in pa] == [p["pairs"] for p in pb]
        ok &= [p["notes"] for p in pa] == [p["notes"] for p in pb]
    check("340: and the round trip gives every code on every extract, two extracts of one code on one passage kept two, "
          "and every note", ok and dry.get("groups") == top_themes, str(dry.get("groups")))
    came = codes_mod.load(back)
    check("340: and the code list with every code's description (qdpxround)",
          came is not None and {c["name"]: c["description"] for c in came["codes"]}
          == {c["name"]: c["description"] for c in listed}, str(came)[:300])
    check("340: and the themes as a new board on the Themes canvas, each theme with its description and note holding "
          "the same extracts, its sub-themes inside it (qdpxround)",
          project_board(back) == project_board(root) and len(project_board(back)) == len(top_themes),
          str(project_board(back))[:400])

    # ── a project of two timepoints, invented: an interviewer note, a recording with an offset, a sub-PET, a note on
    # a label and a statement set aside, each timepoint's PETs on a board of its own (qdpxround, 9 November 2026)
    trip_timepoints(scratch, agents)


# an invented study of two timepoints: Kit asks newcomers to an allotment about their first year on it
FERN_T1 = ("Kit: [00:00:04] What brought you to the allotment?\nFern: [00:00:10] A waiting list I forgot I was on.\n"
           "Kit: [00:00:41] And the first weeks?\nFern: [00:01:15] Bindweed everywhere, and nobody telling me what it was.\n"
           "Kit: [00:02:02] Did you think of stopping?\nFern: [00:02:30] I nearly gave the plot back in May.\n")
FERN_T2 = "Kit: [00:00:03] How is it now?\nFern: [00:00:09] The old man two plots down leaves me his spare seedlings.\n"
LINNET_T1 = "Kit: [00:00:05] Why a plot?\nLinnet: [00:00:12] My father grew leeks and I wanted to know why.\n"
LINNET_T2 = "Kit: [00:00:02] And this season?\nLinnet: [00:00:08] The leeks rotted and I laughed for the first time about it.\n"
TWO = [{"label": "T1", "description": "The first spring"}, {"label": "T2", "description": "The second autumn"}]


def trip_timepoints(scratch: Path, agents: dict) -> None:
    import base64

    import audio as audio_mod
    import cli
    import idiograph_routes as routes
    import server as srv
    import themes
    import workbook as wb_mod

    kept = (srv.CONFIG_PATH, srv.ROOT_OVERRIDE, srv.STATE_PATH, srv.STATE_MEMORY)
    cfg = scratch / "a340-tp-config.json"
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Kit", "corpus": "", "gravity_reference": "",
                               "corpus_exclude": []}), encoding="utf-8")

    def call(route: str, body: dict) -> dict:
        with routes.route_scope(route, body):
            return srv.ROUTES[route](body)

    def row(name, text, who, interview, **more):
        return dict({"name": name, "data": base64.b64encode(text.encode("utf-8")).decode("ascii"), "pseudonym": who,
                     "interview": interview, "speakers": {"Kit": "interviewer", who: "participant"}}, **more)

    def rows_of(path: Path, sheet: str, who: str) -> list[int]:
        return [r["row"] for s in wb_mod.read_case(path)["sheets"] if s["name"] == sheet for r in s["rows"]
                if r["name"] == who]

    def cli_run(root: Path, *argv):
        code, out, err = cli.run(["--root", str(root), "--config", str(cfg), *argv])
        return code, (support.plain(json.loads(out)) if "--json" in argv and out.strip().startswith("{") else out), err

    try:
        srv.CONFIG_PATH, srv.STATE_PATH, srv.STATE_MEMORY = cfg, scratch / "a340-tp-state.json", {"recent": []}
        srv.ROOT_OVERRIDE = None
        root = scratch / "a340-tp" / "Allotment year"
        shutil.rmtree(root.parent, ignore_errors=True)
        root.mkdir(parents=True)
        made = routes.api_new_project({"op": "make", "folder": str(root), "name": "Allotment year",
                                       "research_question": "How do newcomers make sense of a first year on an allotment?",
                                       "files": [row("fern-1.txt", FERN_T1, "Fern", "Spring"),
                                                 row("linnet-1.txt", LINNET_T1, "Linnet", "Spring")]})
        pid = made["project"]["id"]
        routes.api_project({"root": pid, "timepoints": TWO})
        routes.api_project({"root": pid, "agents": True})
        routes.api_add_transcripts({"op": "add", "root": pid, "files": [
            row("fern-2.txt", FERN_T2, "Fern", "Autumn", timepoint=2),
            row("linnet-2.txt", LINNET_T2, "Linnet", "Autumn", timepoint=2)]})
        fern = root / "P1 - Fern" / "P1 Fern - EN & ES.xlsx"
        linnet = root / "P2 - Linnet" / "P2 Linnet - EN & ES.xlsx"
        at = rows_of(fern, "Spring", "Fern")
        wb_mod.save_turn(fern, "Spring", at[0], "", "Luck, not a decision", "",
                         pairs=[{"es": "Arriving by accident", "kq": '"A waiting list I forgot"'},
                                {"es": "Not choosing the plot", "kq": ""}])
        wb_mod.save_turn(fern, "Spring", at[1], "", "Alone in the first weeks\nThe weed as the unknown", "",
                         pairs=[{"es": "Left to work it out alone", "kq": '"nobody telling me what it was"'}])
        wb_mod.save_turn(fern, "Spring", at[2], "", "", "",
                         pairs=[{"es": "Nearly giving up", "kq": '"nearly gave the plot back"'}])
        wb_mod.save_interviewer_note(fern, "Spring", rows_of(fern, "Spring", "Kit")[1], "I asked this too soon", "Kit")
        wb_mod.save_turn(fern, "Autumn", rows_of(fern, "Autumn", "Fern")[0], "", "", "",
                         pairs=[{"es": "Taken in by an older neighbour", "kq": '"leaves me his spare seedlings"'}])
        wb_mod.save_turn(linnet, "Spring", rows_of(linnet, "Spring", "Linnet")[0], "", "", "",
                         pairs=[{"es": "Following a father's leeks", "kq": '"My father grew leeks"'}])
        wb_mod.save_turn(linnet, "Autumn", rows_of(linnet, "Autumn", "Linnet")[0], "", "", "",
                         pairs=[{"es": "Laughing at a failed crop", "kq": '"I laughed for the first time"'}])
        # a made-up recording of a few bytes, a second and a half out from the transcript's times
        folder = audio_mod.source_folder(fern, "Spring")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "Fern-Spring.m4a").write_bytes(b"an invented recording, not sound" * 64)
        audio_mod.write_offset(folder, -1.5)

        def board(path: Path, tp: int, groups: list[dict], aside: list[str]) -> None:
            st = call("/api/themes", {"workbook": str(path), "timepoint": tp})
            key = {c["text"]: c["key"] for c in st["cards"]}
            v = dict(st["version"], cards={k: {"x": 0, "y": 60 * i} for i, k in enumerate(key.values())},
                     groups=[dict(g, members=[key.get(m, m) for m in g["members"]], x=300 * i, y=-60)
                             for i, g in enumerate(groups)], discarded=[key[t] for t in aside], picks={})
            call("/api/themes-save", {"workbook": str(path), "timepoint": tp, "version": v})

        board(fern, 1, [{"id": "g1", "label": "Finding a way in", "description": "A plot come by chance and nearly lost",
                         "note": "Read the bindweed against the waiting list", "members": ["Arriving by accident", "g2"]},
                        {"id": "g2", "label": "Alone with the weeds", "description": "Nobody to ask",
                         "note": "", "members": ["Left to work it out alone", "Nearly giving up"]}],
              ["Not choosing the plot"])
        board(fern, 2, [{"id": "g1", "label": "A neighbour's seedlings", "members": ["Taken in by an older neighbour"]}], [])
        board(linnet, 1, [{"id": "g1", "label": "A father's crop", "members": ["Following a father's leeks"]}], [])
        board(linnet, 2, [{"id": "g1", "label": "Laughing it off", "members": ["Laughing at a failed crop"]}], [])

        back = scratch / "a340-tp" / "Back again"
        (back / "Imports").mkdir(parents=True)
        (back / "idiograph-project.json").write_text(json.dumps({"name": "Back again", "method": "ipa", "agents": agents,
                                                                  "timepoints": TWO}), encoding="utf-8")
        code, done, err = cli_run(root, "project", "export-qdpx", "--to", str(back / "Imports" / "trip.qdpx"),
                                  "--recordings", "--json")
        code2, dry, err2 = cli_run(back, "qdpx", "Imports/trip.qdpx", "--dry-run", "--json")
        names = {s["source"]: s["name"] for s in dry.get("sources") or []}
        # each source named "P1 - Fern - Spring", the participant's label and the interview
        spec = ",".join("{}={}:{}:{}".format(n, name.split(" - ")[1], name[1], "T2" if name.endswith("Autumn") else "T1")
                        for n, name in names.items())
        code3, made, err3 = cli_run(back, "qdpx", "Imports/trip.qdpx", "--sources", spec, "--pets", "--note",
                                    "the round trip", "--json")
        check("340: a project of two timepoints goes out as one source an interview and comes back each interview at "
              "its timepoint", code == 0 and code2 == 0 and code3 == 0 and len(names) == 4
              and sorted(made.get("written") or []) == ["P1 - Fern", "P2 - Linnet"],
              str([err, err2, err3, made])[:400])
        same = {"words": True, "times": True, "pairs": True, "notes": True, "interviewer": True, "pets": True}
        for a, b in ((fern, back / "P1 - Fern" / "P1 Fern - EN & ES.xlsx"),
                     (linnet, back / "P2 - Linnet" / "P2 Linnet - EN & ES.xlsx")):
            ra, rb = wb_mod.read_case(a), wb_mod.read_case(b) if b.exists() else {"sheets": []}
            sheets = lambda r: {s["name"]: s["rows"] for s in r["sheets"]}
            sa, sb = sheets(ra), sheets(rb)
            for name, rows in sa.items():
                other = sb.get(name) or []
                pick = lambda rs, f: [f(r) for r in rs if " ".join(r["text"].split())]
                same["words"] &= pick(rows, lambda r: (r["name"], " ".join(r["text"].split()))) == pick(other, lambda r: (r["name"], " ".join(r["text"].split())))
                same["times"] &= pick(rows, lambda r: r["seconds"]) == pick(other, lambda r: r["seconds"])
                same["pairs"] &= pick(rows, lambda r: [(p["es"], quote_key(p["kq"])) for p in r["pairs"]]) == \
                    pick(other, lambda r: [(p["es"], quote_key(p["kq"])) for p in r["pairs"]])
                same["notes"] &= pick(rows, lambda r: r["en"]) == pick(other, lambda r: r["en"])
                same["interviewer"] &= pick(rows, lambda r: r["note"]) == pick(other, lambda r: r["note"])
            for tp in (1, 2):
                with themes.scoped(tp):
                    da = themes.load(a)
                    want = pets_of(a, themes.current_version(da))
                with themes.scoped(tp):
                    db = themes.load(b) if b.exists() else None
                    got = pets_of(b, themes.current_version(db)) if db else None
                same["pets"] &= want == got
        check("340: and every passage's words, speaker and time, every statement with its quote and every exploratory "
              "note as they were", same["words"] and same["times"] and same["pairs"] and same["notes"], str(same))
        check("340: and the interviewer's note on his own turn back in the interviewer notes column", same["interviewer"],
              str(same))
        check("340: and each timepoint's PETs on that timepoint's board, a sub-PET inside its PET, the label's "
              "description and note, and a statement set aside back in the bin", same["pets"], str(same))
        copied = audio_mod.for_sheet(back / "P1 - Fern" / "P1 Fern - EN & ES.xlsx", "Spring")
        check("340: and the recording copied in with its offset, the transcript's own times kept, so each passage plays "
              "where it did and shows the time it had",
              copied is not None and copied.read_bytes() == (folder / "Fern-Spring.m4a").read_bytes()
              and audio_mod.offset_in(copied.parent) == -1.5, str(copied))
    finally:
        srv.CONFIG_PATH, srv.ROOT_OVERRIDE, srv.STATE_PATH, srv.STATE_MEMORY = kept
