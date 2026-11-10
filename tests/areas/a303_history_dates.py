"""Area 303: a board's History in the order its revisions were made, each at the time it was made (histdate,
30 October 2026).

The page's timer keeps an automatic revision with a save, the board as the file held it before. It took the time
the board was last written, its `updated`, which a statement's edit does not move, nor a revision kept since, so
after an edit the first save filed an Automatic revision dated weeks back between two lines of today: Today, 28
September, Today. An automatic revision now carries the time of the save that kept it, on PETs boards and on GETs
boards (LPETs and LGETs save through the same code), and one a board saved with the fault already holds reads at
the time of the revision made before it, so History lists in order on open with nothing written, and the board's
next save keeps that time.

Each step runs on a clock of the check's own, so every time is known: the boards made on 28 September, an edit
followed by the page's save, an agent's `turn write` followed by the page's save, and an older board whose History
holds an Automatic revision the old way, dated by its unstamped `updated`.

Every word invented: first-time winter sea swimmers, Bryn and Ione, asked by Hale.
"""
from __future__ import annotations

import base64
import json
import shutil
from pathlib import Path

from . import support
from .support import check as said_check
import idiograph_routes


def check(name, ok, detail=""):
    said_check(name, ok, str(detail)[:700])


BRYN = ("Hale: [00:00:03] What was the first swim like?\nBryn: [00:00:08] The cold took my breath before my feet "
        "were wet.\nHale: [00:00:40] And after a month?\nBryn: [00:09:30] I look forward to the shock now.\n")
IONE = ("Hale: [00:00:03] Why the sea in winter?\nIone: [00:00:06] Nothing else makes my head go quiet.\n")
MADE = "2026-09-28T14:10:00+01:00"


def test_history_dates(scratch):
    print("\n303. A board's History in the order its revisions were made, each at the time it was made: an edit then "
          "the page's save, an agent's op then the page's save, and a board saved before with an Automatic revision "
          "dated by its unstamped updated, on PETs and GETs boards (30 October)")
    import cli
    import gets as gets_mod
    import idiograph_cli
    import server as server_mod
    import themes
    import workbook as wb_mod

    b64 = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")
    base = scratch / "a303"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    cfg_file = scratch / "a303-config.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "Hale", "corpus": "", "gravity_reference": "",
                                    "corpus_exclude": []}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    clocks = (themes.now_iso, idiograph_cli.now_iso)
    clock = {"now": MADE}

    def row(name, text, who, interview):
        return {"name": name, "data": b64(text), "pseudonym": who, "interview": interview,
                "speakers": {"Hale": "interviewer", who: "participant"}}

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

    def pets_page(book: Path) -> dict:
        """The PETs board as the page holds it after a read, to save back."""
        st = call("/api/themes", {"workbook": str(book)})
        return dict(st["version"], cards={c["key"]: dict({"x": c["x"], "y": c["y"], "text": c["text"]},
                                                         **({"loose": True} if c.get("loose") else {}))
                                          for c in st["cards"]},
                    groups=st["groups"], discarded=st["discarded"], picks=st["picks"])

    def gets_page(book: Path, board: str) -> dict:
        """A GETs board as the page holds it after a read, to save back."""
        g = call("/api/gets", {"workbook": str(book), "board": board})
        return dict(g["version"], cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in g["cards"]},
                    groups=g["groups"], discarded=g["discarded"], picks={}, notes=g.get("stickies") or [],
                    rows=g.get("rows") or {})

    def listed_pets(book: Path) -> list[dict]:
        return call("/api/themes", {"workbook": str(book)})["history"]

    def listed_gets(book: Path, board: str) -> list[dict]:
        return call("/api/gets", {"workbook": str(book), "board": board})["history"]

    def in_order(listed: list[dict]) -> bool:
        """Newest first, by when each was made, and by the order they were made."""
        times = [themes.iso_time(r["at"]) for r in listed]
        ids = [int(str(r["id"])[1:]) for r in listed]
        return None not in times and times == sorted(times, reverse=True) and ids == sorted(ids, reverse=True)

    def said(listed: list[dict]) -> list[tuple]:
        return [(r["at"], r["name"] or ("Automatic" if r["auto"] else "")) for r in listed]

    def edit(book: Path, sheet: str, at: int, line: int, old: str, new: str) -> dict:
        return call("/api/edit-statement", {"workbook": str(book), "sheet": sheet, "row": at, "line": line,
                                            "text": new, "old": old})

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "a303-state.json", {"recent": []}
        themes.now_iso = idiograph_cli.now_iso = lambda: clock["now"]

        # ── the boards, made on 28 September: Bryn's and Ione's PETs boards, GETs board 1 with Bryn's statements'
        # cards and GETs board 2 with Ione's
        shore = base / "Winter swimmers"
        shore.mkdir()
        made = idiograph_routes.api_new_project({"op": "make", "folder": str(shore), "name": "Winter swimmers",
                                                 "research_question": "How do new winter swimmers live with the cold?",
                                                 "files": [row("bryn.txt", BRYN, "Bryn", "January"),
                                                           row("ione.txt", IONE, "Ione", "January")]})
        idiograph_routes.api_project({"root": made["project"]["id"], "agents": True})
        bryn = shore / "P1 - Bryn" / "P1 Bryn - EN & ES.xlsx"
        ione = shore / "P2 - Ione" / "P2 Ione - EN & ES.xlsx"
        sheet = idiograph_routes.read_sheets(bryn)[1][0]
        b, i = said_rows(bryn, sheet, "Bryn"), said_rows(ione, sheet, "Ione")
        wb_mod.save_turn(bryn, sheet, b[0], "Breath taken by the cold", "", "")
        wb_mod.save_turn(bryn, sheet, b[1], "Looking forward to the shock", "", "")
        wb_mod.save_turn(ione, sheet, i[0], "A quiet head in the sea", "", "")
        for book in (bryn, ione):
            st = call("/api/themes", {"workbook": str(book)})
            keys = [c["key"] for c in st["cards"]]
            words = {c["key"]: c["text"] for c in st["cards"]}
            call("/api/themes-save", {"workbook": str(book), "version": dict(
                st["version"], cards={k: {"x": 0, "y": 40 * n, "text": words[k]} for n, k in enumerate(keys)},
                groups=[{"id": "g1", "label": "Meeting the cold", "members": keys, "x": 0, "y": -40}],
                discarded=[], picks={})})
        kb = [themes.card_key(sheet, b[0], 0), themes.card_key(sheet, b[1], 0)]
        ki = themes.card_key(sheet, i[0], 0)

        def with_cards(board: str, extra: dict) -> dict:
            page = gets_page(bryn, board)
            page["cards"].update({k: {"x": 700, "y": 60 * n, "text": t} for n, (k, t) in enumerate(extra.items())})
            page["groups"] = [{"id": "G1", "label": "Meeting the cold", "members": list(page["cards"]),
                               "x": -20, "y": -60}]
            return page

        call("/api/gets-save", {"workbook": str(bryn), "version": with_cards("b1", {
            gets_mod.card_of("P1 - Bryn", "es", kb[0]): "Breath taken by the cold",
            gets_mod.card_of("P1 - Bryn", "es", kb[1]): "Looking forward to the shock"})})
        call("/api/gets-ops", {"workbook": str(bryn), "op": "new"})
        call("/api/gets-save", {"workbook": str(bryn), "version": with_cards("b2", {
            gets_mod.card_of("P2 - Ione", "es", ki): "A quiet head in the sea"})})
        gfile = shore / gets_mod.FILE
        held = json.loads(gfile.read_text(encoding="utf-8"))
        check("303: two PETs boards and two GETs boards, all last written on 28 September, none with a History yet",
              themes.load(bryn)["boards"][0]["updated"] == MADE and themes.load(ione)["boards"][0]["updated"] == MADE
              and [x["updated"] for x in held["boards"]] == [MADE, MADE]
              and not any(x.get("history") for x in held["boards"] + themes.load(bryn)["boards"]),
              str([x.get("updated") for x in held["boards"]]))

        # ── 1. an edit, then the page's first save, which the timer asks to keep an automatic revision
        clock["now"] = "2026-10-30T09:00:00+00:00"
        edit(bryn, sheet, b[0], 0, "Breath taken by the cold", "Breath stolen by the cold")
        clock["now"] = "2026-10-30T09:00:05+00:00"
        saved = call("/api/themes-save", {"workbook": str(bryn), "version": pets_page(bryn), "revision": "auto"})
        line = 'Bryn\'s statement edited: "Breath taken by the cold" to "Breath stolen by the cold"'
        listed = listed_pets(bryn)
        check("303: on the PETs board the edit's save keeps its Automatic revision at the time of the save, not at the "
              "board's last write on 28 September, listed first",
              saved.get("revision", {}).get("auto") is True and saved["revision"]["at"] == "2026-10-30T09:00:05+00:00"
              and said(listed) == [("2026-10-30T09:00:05+00:00", "Automatic"), ("2026-10-30T09:00:00+00:00", line)]
              and in_order(listed) and saved["history"] == listed, str(said(listed)))
        clock["now"] = "2026-10-30T09:00:10+00:00"
        gsaved = call("/api/gets-save", {"workbook": str(bryn), "version": gets_page(bryn, "b1"), "revision": "auto"})
        glisted = listed_gets(bryn, "b1")
        check("303: and on the GETs board the same, the edit's line, then the save's Automatic revision at its own time",
              gsaved.get("revision", {}).get("at") == "2026-10-30T09:00:10+00:00"
              and said(glisted) == [("2026-10-30T09:00:10+00:00", "Automatic"), ("2026-10-30T09:00:00+00:00", line)]
              and in_order(glisted), str(said(glisted)))

        # ── 2. an agent's op, a `turn write` rewording Bryn's statement, then the page's save after Reload
        def run(*args):
            code, text, err = cli.run(["--root", str(shore), "--config", str(cfg_file), *args, "--json"])
            return code, (support.plain(json.loads(text)) if text.strip() else {}), err

        clock["now"] = "2026-10-30T09:30:00+00:00"
        code, shown, err = run("turn", "show", "Bryn", sheet, str(b[1]))
        version = shown["turns"][0]["version"] if code == 0 and shown.get("turns") else None
        spec = scratch / "a303-turn.json"
        spec.write_text(json.dumps({"pairs": [{"statement": "Looking forward to the shock of it", "quote": "",
                                               "key": kb[1]}],
                                    "version": version, "request": "Add of it to Bryn's statement"}), encoding="utf-8")
        code, wrote, err = run("turn", "write", "Bryn", sheet, str(b[1]), "--from", str(spec), "--tool", "Claude Code")
        agent = "Before: Add of it to Bryn's statement"
        clock["now"] = "2026-10-30T09:45:00+00:00"
        saved = call("/api/themes-save", {"workbook": str(bryn), "version": pets_page(bryn), "revision": "auto"})
        listed = listed_pets(bryn)
        check("303: after an agent's write the page's save keeps its Automatic revision at the save's time, not the "
              "agent's, every line in the order made",
              code == 0 and saved.get("revision", {}).get("at") == "2026-10-30T09:45:00+00:00"
              and said(listed)[:2] == [("2026-10-30T09:45:00+00:00", "Automatic"),
                                       ("2026-10-30T09:30:00+00:00", agent)]
              and len(listed) == 4 and in_order(listed), err or str(said(listed)))
        clock["now"] = "2026-10-30T09:45:05+00:00"
        gsaved = call("/api/gets-save", {"workbook": str(bryn), "version": gets_page(bryn, "b1"), "revision": "auto"})
        glisted = listed_gets(bryn, "b1")
        check("303: and on the GETs board the same",
              gsaved.get("revision", {}).get("at") == "2026-10-30T09:45:05+00:00"
              and said(glisted)[:2] == [("2026-10-30T09:45:05+00:00", "Automatic"),
                                        ("2026-10-30T09:30:00+00:00", agent)]
              and len(glisted) == 4 and in_order(glisted), str(said(glisted)))

        # ── 3. a board saved before the fix with the fault: an edit's line, then the Automatic revision the old save
        # kept, the board after that edit dated by its unstamped `updated`, then another edit's line (Today, 28
        # September, Today), as the files of a board saved then hold it
        def kept_the_old_way(board: dict) -> None:
            first, second = board["history"]
            board["history"] = [first, {"id": "r2", "at": board["updated"], "name": "", "auto": True,
                                        "state": second["state"]}, dict(second, id="r3")]

        clock["now"] = "2026-10-29T18:47:00+00:00"
        edit(ione, sheet, i[0], 0, "A quiet head in the sea", "A quiet head in the cold sea")
        clock["now"] = "2026-10-29T18:57:00+00:00"
        edit(ione, sheet, i[0], 0, "A quiet head in the cold sea", "A quiet head in the winter sea")
        pets = themes.load(ione)
        kept_the_old_way(pets["boards"][0])
        themes.write(ione, pets)
        g = gets_mod.load(shore)
        kept_the_old_way(next(x for x in g["boards"] if x["id"] == "b2"))
        gets_mod.write(shore, g)
        raw = lambda history: [(r["at"], r["auto"]) for r in history]
        first = 'Ione\'s statement edited: "A quiet head in the sea" to "A quiet head in the cold sea"'
        second = 'Ione\'s statement edited: "A quiet head in the cold sea" to "A quiet head in the winter sea"'
        faulty = [("2026-10-29T18:47:00+00:00", False), (MADE, True), ("2026-10-29T18:57:00+00:00", False)]
        pets_file = themes.themes_path(ione)
        check("303: Ione's PETs board and GETs board 2 hold the fault as the old save left it, the Automatic revision "
              "dated 28 September between two edits of 29 October",
              raw(themes.load(ione)["boards"][0]["history"]) == faulty
              and raw(next(x for x in json.loads(gfile.read_text(encoding="utf-8"))["boards"]
                           if x["id"] == "b2")["history"]) == faulty)
        clock["now"] = "2026-10-30T10:00:00+00:00"
        pets_bytes, gets_bytes = pets_file.read_bytes(), gfile.read_bytes()
        listed, glisted = listed_pets(ione), listed_gets(ione, "b2")
        healed = [("2026-10-29T18:57:00+00:00", second), ("2026-10-29T18:47:00+00:00", "Automatic"),
                  ("2026-10-29T18:47:00+00:00", first)]
        check("303: opened, each lists in the order made, the Automatic revision at the time of the edit made before "
              "it, the earliest it can have been made, never under 28 September",
              said(listed) == healed and said(glisted) == healed and in_order(listed) and in_order(glisted),
              str([said(listed), said(glisted)]))
        code, hist, err = run("board", "history", "Ione")
        gcode, ghist, gerr = run("gets", "history", "Board 2")
        check("303: an agent's board history and gets history list them the same, at the same times",
              code == 0 and gcode == 0 and said(hist.get("history") or []) == healed
              and said(ghist.get("history") or []) == healed, err or gerr or str([hist, ghist])[:500])
        check("303: and reading them, in the app or as an agent, writes nothing", pets_file.read_bytes() == pets_bytes
              and gfile.read_bytes() == gets_bytes)
        call("/api/themes-save", {"workbook": str(ione), "version": pets_page(ione)})
        call("/api/gets-save", {"workbook": str(ione), "version": gets_page(ione, "b2")})
        mended = [("2026-10-29T18:47:00+00:00", False), ("2026-10-29T18:47:00+00:00", True),
                  ("2026-10-29T18:57:00+00:00", False)]
        check("303: the board's next save writes that time into the file, on PETs and on GETs",
              raw(themes.load(ione)["boards"][0]["history"]) == mended
              and raw(next(x for x in json.loads(gfile.read_text(encoding="utf-8"))["boards"]
                           if x["id"] == "b2")["history"]) == mended)
    finally:
        themes.now_iso, idiograph_cli.now_iso = clocks
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept
