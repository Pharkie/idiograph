"""Area 242: a description under a PET's, sub-PET's or GET's title (Adam, 21 October 2026, his ruling on the
drawings): a short title for the scan and a longer description shown as a secondary heading, on the board, in
the Table view, the print view and the Word table, so the ladder of abstraction shows.

It is a field of its own, `description` on a label, apart from the label's note, written on the board and in
the Inspector, and for an agent through `board apply`'s and `gets apply`'s `describe` operation, `board new`
and `board show`. The print view carries a Descriptions tick, on on a new install, and the Word table follows
it. A board with no descriptions reads, writes and prints as it did.

The checks hold what is saved and what the exports make: the description written and read back in the board's
file and the GETs file, the operation's dry run writing nothing, "" taking it off, the AI's revise never writing
one, the print view and the Word table with the tick on and off, and a board without descriptions the same in
its file and its print view. Words, sizes and colour go to Adam as review shots. The fixtures are the demo's
invented participants and a made-up title and description on its topic, living with a dog.
"""
from __future__ import annotations

import json
import re
import shutil
import zipfile

from . import support
from .support import check
import idiograph_routes

PET_DESC = "Out in the dark at both ends of the day, and happiest with her there"
SUB_DESC = "A watchfulness he noticed only once she had gone"
GET_DESC = "Days that begin and end with the dog, for both of them"


def test_descriptions(scratch):
    print("\n242. A description under a PET's, sub-PET's or GET's title, on the board, in the Table view, the print "
          "view and the Word table (Adam, 21 October)")
    import cli
    import gets as gets_mod
    import gets_print
    import server as server_mod
    import themes
    import themes_print
    import themes_word

    pristine = support.DEMO_PRISTINE
    root = scratch / "descriptions-242-root"
    shutil.rmtree(root, ignore_errors=True)
    for name in ("Juno", "Rowan", "Mabel"):
        case = root / name
        (case / "Working").mkdir(parents=True)
        shutil.copy2(pristine / f"{name} - EN & ES.xlsx", case / f"{name} - EN & ES.xlsx")
        for side in (pristine / "Working").glob(f"{name} - *"):
            shutil.copy2(side, case / "Working" / side.name)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Dogs, a scratch project", "agents": {"allowed": True, "at": "2026-10-21T10:00:00+01:00"}}), encoding="utf-8")
    config_file = scratch / "descriptions-242-config.json"
    config_file.write_text(json.dumps({"root": str(root), "interviewer": "Adam"}), encoding="utf-8")
    book = root / "Rowan" / "Rowan - EN & ES.xlsx"
    themes_file = themes.themes_path(book)
    books = [{"case": n, "workbook": str(root / n / f"{n} - EN & ES.xlsx")} for n in ("Juno", "Rowan", "Mabel")]

    def answer(*args):
        code, out, err = cli.run(["--root", str(root), "--config", str(config_file), *args, "--json"])
        return code, (support.plain(json.loads(out)) if out.strip() else {}), err

    def ops(*operations) -> str:
        path = scratch / "descriptions-242-ops.json"
        path.write_text(json.dumps({"operations": list(operations)}), encoding="utf-8")
        return str(path)

    def board(vid="v1") -> dict:
        return next(b for b in json.loads(themes_file.read_text(encoding="utf-8"))["boards"] if b["id"] == vid)

    def groups_of(b: dict) -> dict:
        return {g["id"]: g for g in b["groups"]}

    start = board()
    first = themes_file.read_bytes()
    parents = themes.parents_of(start["groups"])
    sub = next(g["id"] for g in start["groups"] if g["id"] in parents)
    pet = parents[sub]
    print_off = lambda **kw: themes_print.page(book, "Rowan", "v1", auto=False, **kw)
    plain_page = print_off(descriptions=True)

    # ── A. a board with none: no description anywhere in its file, and its print view the same with the tick on or off
    check("242: a board with no descriptions carries none in its file, normalised and written again it is the same, "
          "and its print view is the same with Descriptions ticked or not but for the tick itself",
          b'"description"' not in first and themes.normalise(start)["groups"] == themes.normalise(support.plain(json.loads(json.dumps(start))))["groups"]
          and not any("description" in g for g in themes.normalise(start)["groups"])
          and plain_page.replace('id="include-descriptions" checked', 'id="include-descriptions"') == print_off(descriptions=False),
          "")
    # since 31 October (labeldesc) six lines at most, where two, and a label with one runs as wide as what it holds
    check("242: a label's size on the board is as before with no description, and taller with one, six lines at most, "
          "and over a body wider than a label runs it runs as wide as the body and no deeper, never wider",
          themes.label_size("Living on her timetable") == themes.label_size("Living on her timetable", description="")
          and themes.label_size("Living on her timetable", description=PET_DESC)[1] > themes.label_size("Living on her timetable")[1]
          and themes.label_size("x", description=PET_DESC * 20)[1] == themes.label_size("x", description=PET_DESC * 12)[1]
          > themes.label_size("x", description=PET_DESC * 2)[1]
          and themes.label_size("Living on her timetable", body=900) == themes.label_size("Living on her timetable")
          and themes.label_size("x", description=PET_DESC * 3, body=200) == themes.label_size("x", description=PET_DESC * 3)
          and themes.label_size("x", description=PET_DESC * 3, body=900)[0] == 900
          and themes.label_size("x", description=PET_DESC * 3, body=900)[1] < themes.label_size("x", description=PET_DESC * 3)[1],
          f"{themes.label_size('Living on her timetable')} {themes.label_size('Living on her timetable', description=PET_DESC)} "
          f"{themes.label_size('x', description=PET_DESC * 3)} {themes.label_size('x', description=PET_DESC * 3, body=900)}")

    # ── B. board apply's describe: a dry run writes nothing, then each saved in the file, History keeping the step
    change = ops({"op": "describe", "label": pet, "description": "  " + PET_DESC + "\n"},
                 {"op": "describe", "label": sub, "description": SUB_DESC})
    code, dry, err = answer("board", "apply", "Rowan", "v1", "--ops", change, "--note", "Describe two", "--dry-run")
    check("242: board apply's describe has a dry run that says what it would do and writes nothing",
          code == 0 and dry.get("dry_run") is True and "wrote the description under" in dry.get("said", "")
          and themes_file.read_bytes() == first, dry.get("said", "") + err)
    history = len(start.get("history") or [])
    code, done, err = answer("board", "apply", "Rowan", "v1", "--ops", change, "--note", "Describe two",
                             "--tool", "Claude Code")
    after = board()
    by = groups_of(after)
    check("242: board apply writes each description on its own line in the board's file, beside its title and apart "
          "from its note, the board marked as changed by the tool, one revision kept first in its History",
          code == 0 and by[pet].get("description") == PET_DESC and by[sub].get("description") == SUB_DESC
          and by[pet].get("note") == groups_of(start)[pet].get("note") and by[pet]["label"] == groups_of(start)[pet]["label"]
          and after["changed"]["tool"] == "Claude Code" and len(after.get("history") or []) == history + 1,
          done.get("said", "") + err)
    code, shown, err = answer("board", "show", "Rowan", "v1")
    top = next(t for t in shown.get("themes", []) if t["id"] == pet)
    inner = next(t for t in top["themes"] if t["id"] == sub)
    code_t, text_out, _ = cli.run(["--root", str(root), "--config", str(config_file), "board", "show", "Rowan", "v1"])
    check("242: board show gives each label's description, in its answer and its lines",
          code == 0 and top.get("description") == PET_DESC and inner.get("description") == SUB_DESC
          and f"Description: {PET_DESC}" in text_out, err)
    again = answer("board", "apply", "Rowan", "v1", "--ops", change, "--note", "Describe two again")
    check("242: the same descriptions again change nothing and write nothing",
          again[0] == 0 and again[1].get("changed") is False and board() == after, again[1].get("said", ""))

    # ── C. refusals: one with no description given, or on a label not on the board (the AI's revise, which was refused
    # one, went on 11 November 2026, aiout, and the applier now serves board apply and gets apply alone)
    held = themes_file.read_bytes()
    bad = answer("board", "apply", "Rowan", "v1", "--ops", ops({"op": "describe", "label": pet}), "--note", "x")
    unknown = answer("board", "apply", "Rowan", "v1", "--ops", ops({"op": "describe", "label": "g999", "description": "x"}),
                     "--note", "x")
    check("242: a describe with no description, or on a label not on the board, is refused whole with nothing written",
          bad[0] != 0 and unknown[0] != 0 and themes_file.read_bytes() == held, f"{bad[2]} {unknown[2]}")

    # ── D. the print view and the Word table, with the tick on and off
    on = print_off(descriptions=True)
    off = print_off(descriptions=False)
    check("242: the print view sets each description under its title in the heading, with the Descriptions tick "
          "ticked, and leaves them out with it unticked",
          PET_DESC in on and SUB_DESC in on and f'<span class="desc">{PET_DESC}</span>' in on
          and 'id="include-descriptions" checked' in on and PET_DESC not in off and SUB_DESC not in off
          and 'id="include-descriptions" checked' not in off, "")
    board_ = themes.outline(themes.read_cards(book), themes.pick_version(themes.load(book), "v1"))
    lines_on = themes_word.plain(themes_word.blocks("Rowan", themes.descriptions_shown(board_, True)))
    lines_off = themes_word.plain(themes_word.blocks("Rowan", themes.descriptions_shown(board_, False)))
    top_line = next(i for i, x in enumerate(lines_on) if x.upper().endswith(groups_of(after)[pet]["label"].upper()))
    made = themes_word.write(book, "Rowan", "v1", descriptions=True)
    with zipfile.ZipFile(made["path"]) as z:
        xml_on = z.read("word/document.xml").decode("utf-8")
    made_off = themes_word.write(book, "Rowan", "v1", descriptions=False)
    with zipfile.ZipFile(made_off["path"]) as z:
        xml_off = z.read("word/document.xml").decode("utf-8")
    desc_run = re.search(r"<w:r><w:rPr>([^<]|<(?!/w:rPr>))*</w:rPr><w:br/><w:t[^>]*>" + re.escape(PET_DESC), xml_on)
    check("242: the Word table puts each description as a second line of its heading, plain, smaller and grey, with "
          "the tick on, and none with it off",
          lines_on[top_line + 1] == PET_DESC and SUB_DESC in lines_on and PET_DESC not in lines_off
          and desc_run is not None and '<w:b w:val="0"/>' in desc_run.group(0) and "595959" in desc_run.group(0)
          and PET_DESC not in xml_off, str(lines_on[top_line:top_line + 2]))
    saved_cfg = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    cfg = scratch / "descriptions-242-settings.json"
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Adam"}), encoding="utf-8")
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, None
        server_mod.STATE_MEMORY = {"recent": []}
        fresh = idiograph_routes.export_descriptions({})
        server_mod.api_settings({"export_descriptions": False})
        kept = json.loads(cfg.read_text(encoding="utf-8")).get("export_descriptions")
        check("242: Descriptions is ticked on a new install, unticked it is kept in the settings, and an export that "
              "says nothing follows the settings, one that says follows what it says",
              fresh is True and kept is False and idiograph_routes.export_descriptions({}) is False
              and idiograph_routes.export_descriptions({"descriptions": "1"}) is True
              and server_mod.merge_config({})["export_descriptions"] is True, str(kept))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = saved_cfg

    # ── E. taken off with "": the board as it was, no description left in the file
    code, off_done, err = answer("board", "apply", "Rowan", "v1", "--ops", ops(
        {"op": "describe", "label": pet, "description": ""}, {"op": "describe", "label": sub, "description": None}),
        "--note", "Take them off")
    cleared = board()
    # where things stand is laid out afresh round a label that grew, so its words, members and cards are compared
    words = lambda b: [{k: v for k, v in g.items() if k not in ("x", "y")} for g in b["groups"]]
    texts = lambda b: {k: c.get("text") for k, c in b["cards"].items()}
    check("242: a describe with \"\" or null takes the description off, and the board's labels and cards are as they "
          "were before any, with no description left in its file",
          code == 0 and "took the description off" in off_done.get("said", "")
          and words(cleared) == words(start) and texts(cleared) == texts(start)
          and '"description"' not in json.dumps(cleared["groups"]), off_done.get("said", "") + err)

    # ── F. board new takes a description on a PET and a sub-PET
    keys = [c["key"] for c in themes.read_cards(book)["cards"]]
    spec = scratch / "descriptions-242-new.json"
    spec.write_text(json.dumps({"pets": [{"title": "Living on her timetable", "description": PET_DESC, "members": keys[:2],
                                          "subs": [{"title": "Still listening for other dogs", "description": SUB_DESC,
                                                    "members": keys[2:4]}]}]}), encoding="utf-8")
    code, new, err = answer("board", "new", "Rowan", "--from", str(spec), "--note", "A board with descriptions",
                            "--tool", "Claude Code", "--layout", "fresh")
    made_board = board(new.get("id") or new.get("board") or "") if code == 0 else {}
    by_title = {g["label"]: g for g in made_board.get("groups") or []}
    check("242: board new takes a description on each PET and sub-PET and keeps it on the label it makes",
          code == 0 and by_title.get("Living on her timetable", {}).get("description") == PET_DESC
          and by_title.get("Still listening for other dogs", {}).get("description") == SUB_DESC, err + json.dumps(new)[:300])

    # ── G. GETs: a GET's description through gets apply, saved and read back, in its print, and a PET's carried
    describe_pet = answer("board", "apply", "Rowan", "v1", "--ops", ops({"op": "describe", "label": pet, "description": PET_DESC}),
                          "--note", "Describe the PET")
    data_g, _, _, _ = gets_mod.assemble(root, books, themes.now_iso())
    gets_mod.write(root, gets_mod._file(data_g, themes.now_iso()))
    gfile = gets_mod.gets_path(root)
    copy_pet = next(p for p in data_g["cases"]["Rowan"]["pets"] if p["id"] == pet)
    no_desc = [p for c in data_g["cases"].values() for p in c.get("pets") or [] if p["id"] != pet and "description" in p]
    rowan = [k for k in data_g["boards"][0]["cards"] if k.startswith("Rowan/")]
    code, made_get, err = answer("gets", "apply", "b1", "--ops", ops(
        {"op": "make", "ref": "a", "title": "A day given its shape by the dog", "inside": None, "members": rowan[:1]}),
        "--note", "One GET")
    gid = (made_get.get("made") or [""])[0]
    raw = gfile.read_bytes()
    code_d, dry_g, _ = answer("gets", "apply", "b1", "--ops", ops({"op": "describe", "label": gid, "description": GET_DESC}),
                              "--note", "Describe the GET", "--dry-run")
    dry_kept = gfile.read_bytes() == raw
    code_g, done_g, err_g = answer("gets", "apply", "b1", "--ops", ops({"op": "describe", "label": gid, "description": GET_DESC}),
                                   "--note", "Describe the GET", "--tool", "Claude Code")
    stored = json.loads(gfile.read_text(encoding="utf-8"))
    get = next(g for g in stored["boards"][0]["groups"] if g["id"] == gid)
    code_s, shown_g, _ = answer("gets", "show", "b1")
    shown_get = next((t for t in shown_g.get("themes") or [] if t["id"] == gid), {})
    check("242: the PETs' copy in the GETs carries a PET's description and no other, and gets apply's describe, after "
          "a dry run that writes nothing, keeps a GET's in the GETs file, which gets show gives back",
          describe_pet[0] == 0 and copy_pet.get("description") == PET_DESC and not no_desc
          and code == 0 and gid and code_d == 0 and dry_kept and code_g == 0
          and get.get("description") == GET_DESC and shown_get.get("description") == GET_DESC,
          f"{err} {err_g} {done_g.get('said', '')}")
    project = idiograph_routes.read_project(root)
    page_on = gets_print.page(root, books, project, "b1", what="all", auto=False, descriptions=True)
    page_off = gets_print.page(root, books, project, "b1", what="all", auto=False, descriptions=False)
    cards = gets_mod.cards_shown(gets_mod.normal(stored["boards"][0], stored), stored)
    pet_card = next((c for c in cards if c["key"] == f"Rowan/{pet}"), {})
    check("242: the GETs print sets a GET's description under its title and a PET's under its own in the PET tables, "
          "and neither with the tick off, and a PET's card on the GETs board carries its description",
          f'<span class="gdesc">{GET_DESC}</span>' in page_on and PET_DESC in page_on
          and GET_DESC not in page_off and PET_DESC not in page_off
          and pet_card.get("description") == PET_DESC,
          str(pet_card)[:200])
    code_r, gone_g, _ = answer("gets", "apply", "b1", "--ops", ops({"op": "describe", "label": gid, "description": ""}),
                               "--note", "Take it off")
    check("242: on a GETs board too \"\" takes the description off, none left in the GETs board",
          code_r == 0 and "description" not in next(g for g in json.loads(gfile.read_text(encoding="utf-8"))["boards"][0]["groups"]
                                                    if g["id"] == gid), gone_g.get("said", ""))
