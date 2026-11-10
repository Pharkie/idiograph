from __future__ import annotations

import base64
import json
import shutil

import openpyxl

from .a244_qdpx import atlas
from .support import check
import idiograph_routes

# The import card's .qdpx (21 October): the file sent by the page, held by the server under a key,
# read again with the card's choices, and brought in by New project's make or Add's. The package is
# the suite's own ATLAS.ti flavour, on keeping an allotment, with invented people.


def test_qdpx_card(scratch):
    print("\n245. The import card for a project from ATLAS.ti, NVivo or MAXQDA: the file the page sends held, the "
          "card's choices reaching the import as chosen, a read writing nothing, New project and Add bringing it in "
          "(21 October)")
    import server as server_mod
    import themes
    import workbook as wb_mod
    from server import WorkbookError

    base = scratch / "a245-qdpx-card"
    shutil.rmtree(base, ignore_errors=True)
    folder = base / "Allotment study"
    folder.mkdir(parents=True)
    cfg = scratch / "a245-config.json"
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Quill"}), encoding="utf-8")
    package = atlas()
    data = base64.b64encode(package).decode("ascii")

    def tree(at_):
        return {p.relative_to(at_).as_posix(): (p.read_bytes() if p.is_file() and p.suffix != ".lock" else None)
                for p in sorted(at_.rglob("*"))}

    def rows_of(book, sheet):
        wb = openpyxl.load_workbook(book)
        try:
            return [list(r) for r in wb[sheet].iter_rows(values_only=True)]
        finally:
            wb.close()

    def refused(call, body):
        try:
            call(body)
            return "made"
        except WorkbookError as exc:
            return str(exc)

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "a245-state.json", {"recent": []}

        # -- A. the page's file held, read before a folder is chosen, nothing written
        before, settings = tree(folder), cfg.read_bytes()
        first = idiograph_routes.api_qdpx({"op": "read", "name": "Allotments.qdpx", "data": data})
        held = idiograph_routes.qdpx_held(first["held"])
        check("245: a .qdpx the card sends is held by the server under a key, read as an agent's dry run reads one, "
              "each source with its guessed interview, and nothing written in the folder or the settings",
              held.read_bytes() == package and first["package"] == "ATLAS.ti" and first["said"] == idiograph_routes.QDPX_NAME_SOURCES
              and first["sources"][0]["interview"] == "Interview" and len(first["sources"][0]["passages"]) == 6
              and tree(folder) == before and cfg.read_bytes() == settings, str(first)[:400])
        check("245: a file whose name does not end .qdpx is refused, and one no longer held says so",
              refused(idiograph_routes.api_qdpx, {"op": "read", "name": "notes.txt", "data": data}) == idiograph_routes.NOT_A_QDPX
              and refused(idiograph_routes.api_qdpx, {"op": "read", "held": "gone"}) == idiograph_routes.QDPX_GONE)

        # -- B. the card's choices reach the import as chosen, a read writing nothing
        key = first["held"]
        again = idiograph_routes.api_qdpx({"op": "read", "held": key, "folder": str(folder), "codes": "notes",
                                     "comments": "statements", "loose": "leave",
                                     "sources": [{"source": 1, "pseudonym": "Wren", "number": 2}]})
        passage = again["sources"][0]["passages"][1]
        check("245: a read with the card's choices answers as they set it, codes as notes, comments as statements, "
              "quotations with no code left out, and the participant it would make, writing nothing",
              again["held"] == key and again["said"] is None
              and again["choices"]["codes"] == "notes" and again["choices"]["loose"] == "leave"
              and passage["notes"] == ["Overwhelmed by the plot"]
              and passage["statements"] == [{"statement": "the neglect, all at once", "quote": '"Brambles everywhere."'}]
              and [p["label"] for p in again["participants"]] == ["P2 - Wren"]
              and any("1 quotation with no code or comment left out" in line for line in again["lines"])
              and tree(folder) == before and cfg.read_bytes() == settings, str(again)[:600])
        blank = idiograph_routes.api_qdpx({"op": "read", "held": key, "sources": [{"source": 1, "pseudonym": ""}]})
        check("245: a source still without its pseudonym counts as a participant of its own in the lines",
              blank["lines"][0].startswith("From Allotments.qdpx (ATLAS.ti): 1 participant, 6 passages"), str(blank["lines"]))

        # -- C. New project's make refuses before it writes
        no_name = refused(idiograph_routes.api_new_project, {"op": "make", "folder": str(folder), "name": "Allotment study",
                                                       "files": [], "qdpx": {"held": key, "sources": [{"source": 1}]}})
        check("245: New project's make with a source given no pseudonym is refused, nothing written and the file still held",
              "pseudonym" in no_name and tree(folder) == before and cfg.read_bytes() == settings
              and idiograph_routes.qdpx_held(key).is_file(), no_name)

        # -- D. New project's make brings the project in with the card's choices
        made = idiograph_routes.api_new_project({"op": "make", "folder": str(folder), "name": "Allotment study",
                                           "research_question": "", "files": [],
                                           "qdpx": {"held": key, "codes": "notes", "comments": "statements", "loose": "leave",
                                                    "sources": [{"source": 1, "pseudonym": "Wren", "number": 2}]}})
        book = folder / "P2 - Wren" / "P2 Wren - EN & ES.xlsx"
        wren = rows_of(book, "Interview")[2] if book.is_file() else [None] * 6
        check("245: Create project with a .qdpx makes the project and its participant, with the choices the card sent",
              made["made"] is True and made["cases"] == ["P2 - Wren"] and made["project"]["name"] == "Allotment study"
              and wb_mod.pairs_of(wren[2], wren[5]) == [{"es": "the neglect, all at once", "kq": '"Brambles everywhere."'}]
              and "Overwhelmed by the plot" in str(wren[4])
              and (folder / "P2 - Wren" / "Source" / "Interview" / "P2-Interview.qdpx").read_bytes() == package,
              str(wren))
        check("245: the held copy is taken away once its participants are made",
              refused(idiograph_routes.api_qdpx, {"op": "read", "held": key}) == idiograph_routes.QDPX_GONE and not held.exists())

        # -- E. Add brings it in to the project there, at Adam's defaults, with the PET draft
        pid = made["project"]["id"]
        key2 = idiograph_routes.api_qdpx({"op": "read", "name": "Allotments.qdpx", "data": data, "root": pid})["held"]
        check("245: the card's make with no project named is refused",
              refused(idiograph_routes.api_qdpx, {"op": "make", "held": key2, "sources": [{"source": 1, "pseudonym": "Ash"}]})
              == "Name the project to add the participants to.")
        done = idiograph_routes.api_qdpx({"op": "make", "held": key2, "root": pid, "pets": True,
                                    "sources": [{"source": 1, "pseudonym": "Ash"}]})
        ash = folder / "P3 - Ash" / "P3 Ash - EN & ES.xlsx"
        row = rows_of(ash, "Interview")[2] if ash.is_file() else [None] * 6
        data_ = themes.load(ash) if ash.is_file() else None
        board = themes.current_version(data_) if data_ else {}
        check("245: Add with a .qdpx makes the participant at the next number, codes as statements and a quotation with "
              "no code a quote to pair, and with the PET draft ticked a board From ATLAS.ti",
              done["made"] == ["P3 - Ash"]
              and wb_mod.pairs_of(row[2], row[5]) == [{"es": "Overwhelmed by the plot", "kq": '"Brambles everywhere."'},
                                                      {"es": "", "kq": '"I could not see the shed at all."'}]
              and (board or {}).get("name") == "From ATLAS.ti", str(row))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept
        idiograph_routes.qdpx_let_all_go()
