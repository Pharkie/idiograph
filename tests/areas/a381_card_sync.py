"""Area 381: every copy of a statement follows the workbook, and copies refresh brings a stale one back (cardsync,
13 November 2026).

Found by the GRAVITY session in a longitudinal project: after a pass that requoted about a thousand statements, a
participant's LPETs held the old quote for most of them, since `turn write` carried a statement's new wording into
the copies and never its new quote, and a write that went astray left cards on old wording that `board show`, which
prints the workbook's words by key, could not show. What is checked, on an invented project of two timepoints. A
`turn write` that rewords a statement and requotes it and its sibling carries the words to the PETs board's card and
both into the LPETs' and the LGETs' copies, the row's quotes as the workbook holds them, its dry run writing nothing
and naming the quotes, the timepoint left in. A clean project's `copies refresh --dry-run` reports nothing. Cards, a
pick's quote and copies' lines made stale by hand are marked card stale by `board show` and named by key, never by
their words, in the dry run, which writes nothing. The refresh brings each back, one History step on each board it
changes, marked changed by the agent, a card whose statement is gone listed and left, and the app reads the card
afresh, not changed.

Every word invented: an adult learning to sail over a year, Tove, asked by Ines.
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


TOVE_T1 = ("Ines: [00:00:03] What did the first lesson feel like?\n"
           "Tove: [00:00:09] I clung to the rail and watched the water rush past the hull.\n"
           "Ines: [00:00:40] And the second week?\n"
           "Tove: [00:02:30] I took the tiller and the boat turned when I asked it to.\n")
TOVE_T2 = ("Ines: [00:00:02] How is it now?\n"
           "Tove: [00:00:06] I read the wind on the water before I leave the jetty.\n")
TWO = [{"label": "T1", "description": "First lessons"}, {"label": "T2", "description": "After the season"}]


def test_card_sync(scratch):
    print("\n381. Every copy of a statement follows the workbook: a turn write's new wording and new quote reach the "
          "PETs board, the LPETs and the LGETs, a clean project's refresh reports nothing, stale cards, a pick's quote "
          "and copies made by hand are marked card stale and named by key in the dry run, and copies refresh brings "
          "them back with one History step a board, a gone statement's card listed and left (cardsync, 13 November)")
    import cli
    import gets as gets_mod
    import server as server_mod
    import themes
    import workbook as wb_mod

    b64 = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")
    base = scratch / "a381"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    cfg_file = scratch / "a381-config.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "Ines", "corpus": "", "gravity_reference": "",
                                    "corpus_exclude": []}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)

    def tree(at: Path) -> dict:
        return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*"))
                if p.is_file() and p.suffix != ".lock"}

    def row(name, text, who, interview, **more):
        return dict({"name": name, "data": b64(text), "pseudonym": who, "interview": interview,
                     "speakers": {"Ines": "interviewer", who: "participant"}}, **more)

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

    def board_of(book: Path, tp: int, groups: list, picks: dict | None = None):
        """A PETs board at a timepoint, each PET the cards at those places in the canvas's order, with picks by PET."""
        body = {"workbook": str(book), "timepoint": tp}
        st = call("/api/themes", body)
        keys = [c["key"] for c in st["cards"]]
        words = {c["key"]: c["text"] for c in st["cards"]}
        v = dict(st["version"], cards={k: {"x": 0, "y": 40 * i, "text": words[k]} for i, k in enumerate(keys)},
                 groups=[{"id": f"g{i + 1}", "label": label, "members": [keys[j] for j in at], "x": 300 * i, "y": -40}
                         for i, (label, at) in enumerate(groups)], discarded=[], picks=picks or {})
        call("/api/themes-save", dict(body, version=v))

    def board_with(answer: dict, extra: dict, label: str) -> dict:
        """A GETs board as the page saves it, the statements' cards added with their words, one GET over them all."""
        cards = {c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in answer["cards"]}
        cards.update({k: {"x": 700, "y": 60 * i, "text": t} for i, (k, t) in enumerate(extra.items())})
        return dict(answer["version"], cards=cards, groups=[{"id": "G1", "label": label, "members": list(cards),
                                                             "x": -20, "y": -60}], discarded=[], picks={}, notes=[])

    def read(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def write(path: Path, data: dict) -> None:
        # a write gone astray, made by hand: the file left as a stale copy would leave it
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "a381-state.json", {"recent": []}

        # ── a project of two timepoints, Tove at each, a PETs board at each, an LPETs and an LGETs board
        sail = base / "Sailing year"
        sail.mkdir()
        made = idiograph_routes.api_new_project({"op": "make", "folder": str(sail), "name": "Sailing year",
                                                 "research_question": "How do adults find their feet learning to sail?",
                                                 "files": [row("tove-one.txt", TOVE_T1, "Tove", "Spring")]})
        root = made["project"]["id"]
        idiograph_routes.api_project({"root": root, "timepoints": TWO})
        idiograph_routes.api_project({"root": root, "agents": True})
        idiograph_routes.api_add_transcripts({"op": "add", "root": root, "files": [
            row("tove-two.txt", TOVE_T2, "Tove", "Autumn", timepoint=2)]})
        book = sail / "P1 - Tove" / "P1 Tove - EN & ES.xlsx"
        s1 = idiograph_routes.read_sheets(book)[1][0]
        s2 = "Autumn"
        r1, r2 = said_rows(book, s1, "Tove"), said_rows(book, s2, "Tove")
        wb_mod.save_turn(book, s1, r1[0], None, "", None, pairs=[
            {"es": "Clinging on at first", "kq": "I clung to the rail"},
            {"es": "Watching the water", "kq": "watched the water rush past the hull"}])
        wb_mod.save_turn(book, s1, r1[1], None, "", None, pairs=[
            {"es": "Steering for the first time", "kq": "I took the tiller"}])
        wb_mod.save_turn(book, s2, r2[0], None, "", None, pairs=[
            {"es": "Reading the wind", "kq": "I read the wind on the water"}])
        k0, k1, k2 = (themes.card_key(s1, r1[0], 0), themes.card_key(s1, r1[0], 1), themes.card_key(s1, r1[1], 0))
        k3 = themes.card_key(s2, r2[0], 0)
        board_of(book, 1, [("Holding on", [0, 1]), ("At the helm", [2])], picks={"g2": [k2]})
        board_of(book, 2, [("Reading the water", [0])])
        lp = call("/api/gets", {"workbook": str(book), "lpets": True})
        call("/api/gets-save", {"workbook": str(book), "lpets": True, "version": board_with(
            lp, {gets_mod.card_of("T1", "es", k0): "Clinging on at first",
                 gets_mod.card_of("T1", "es", k2): "Steering for the first time"}, "From the rail to the helm")})
        lg = call("/api/gets", {"workbook": str(book)})
        call("/api/gets-save", {"workbook": str(book), "version": board_with(
            lg, {gets_mod.card_of("P1 - Tove", "es", k3): "Reading the wind"}, "Finding their feet")})
        lpfile, lgfile = gets_mod.lpets_path(book), sail / gets_mod.LGETS_FILE
        pets1 = themes.themes_path(book, 1)
        check("381: the project holds Tove's PETs boards at both timepoints, her LPETs' copy and the LGETs' copy",
              pets1.is_file() and themes.themes_path(book, 2).is_file() and lpfile.is_file() and lgfile.is_file()
              and read(lpfile)["cases"]["T1"]["lines"][k1]["quotes"] == ["I clung to the rail",
                                                                         "watched the water rush past the hull"],
              str(sorted(read(lpfile).get("cases") or {})))

        def run(*args, as_json=True):
            code, text, err = cli.run(["--root", str(sail), "--config", str(cfg_file), *args]
                                      + (["--json"] if as_json else []))
            if not as_json:
                return code, text, err
            return code, (support.plain(json.loads(text)) if text.strip() else {}), err

        # ── A. a turn write that rewords one statement and requotes it and its sibling
        code, shown, err = run("turn", "show", "Tove", s1, str(r1[0]))
        version = shown["turns"][0]["version"] if code == 0 and shown.get("turns") else None
        spec = scratch / "a381-turn.json"
        spec.write_text(json.dumps({"pairs": [
            {"statement": "Clinging to the rail at first", "quote": "I clung to the rail and watched the water", "key": k0},
            {"statement": "Watching the water", "quote": "the water rush past the hull", "key": k1}],
            "version": version, "request": "Tighten Tove's two quotes"}), encoding="utf-8")
        whole = tree(sail)
        code, dry, err = run("turn", "write", "Tove", s1, str(r1[0]), "--from", str(spec), "--dry-run")
        lp_dry = (dry.get("copies") or {}).get("lpets") or {}
        check("381: the write's dry run says the LPETs' copy would take the reworded statement's words and both "
              "statements' quotes, and writes nothing",
              code == 0 and dry.get("dry_run") is True and lp_dry.get("words") == [k0]
              and lp_dry.get("quotes") == [k0, k1] and tree(sail) == whole, err or str(dry)[:600])
        code, text, err = run("turn", "write", "Tove", s1, str(r1[0]), "--from", str(spec), "--tool", "Claude Code",
                              as_json=False)
        read_now = themes.read_cards(book)
        cells = [q["text"] for q in read_now["quotes"][themes.row_key(s1, r1[0])]["quotes"]]
        lpd, lgd = read(lpfile), read(lgfile)
        t1 = lpd["cases"]["T1"]["lines"]
        lg_lines = lgd["cases"]["P1 - Tove"]["lines"]
        check("381: the workbook holds the new statement and both new quotes",
              code == 0 and cells == ['"I clung to the rail and watched the water"', '"the water rush past the hull"']
              and next(c["text"] for c in read_now["cards"] if c["key"] == k0) == "Clinging to the rail at first",
              err or str(cells))
        check("381: the PETs board's card takes the new wording",
              themes.load(book)["boards"][0]["cards"][k0]["text"] == "Clinging to the rail at first",
              str(themes.load(book)["boards"][0]["cards"].get(k0)))
        check("381: the LPETs' copy takes the new wording and the row's new quotes on both statements, as the workbook "
              "holds them, its card the wording too",
              t1[k0]["text"] == "Clinging to the rail at first" and t1[k0]["quotes"] == cells and t1[k1]["quotes"] == cells
              and lpd["boards"][0]["cards"][gets_mod.card_of("T1", "es", k0)]["text"] == "Clinging to the rail at first",
              str([t1[k0], t1[k1]])[:600])
        check("381: the LGETs' copy takes them too", lg_lines[k0]["text"] == "Clinging to the rail at first"
              and lg_lines[k0]["quotes"] == cells and lg_lines[k1]["quotes"] == cells, str(lg_lines.get(k0)))
        check("381: the write says the LPETs' copy took the new words and quotes",
              "The LPETs' copy of the participant took the new words and quotes" in text, text[-600:])
        lp_after = call("/api/gets", {"workbook": str(book), "lpets": True})
        check("381: the timepoint stays in on the LPETs, not changed since it came in",
              {c["case"]: c["status"] for c in lp_after["cases"]}.get("T1") == "in",
              str([(c["case"], c["status"]) for c in lp_after["cases"]]))

        # ── B. a clean project: the refresh's dry run reports nothing
        whole = tree(sail)
        code, clean, err = run("copies", "refresh", "--dry-run")
        check("381: on a project whose copies all follow the workbook, copies refresh's dry run reports nothing and "
              "writes nothing",
              code == 0 and clean.get("participants") == [] and (clean["cards"], clean["statements"], clean["quotes"])
              == (0, 0, 0) and clean["said"].startswith("Every board's cards") and tree(sail) == whole,
              err or str(clean)[:600])

        # ── C. copies made stale by hand, as a write gone astray leaves them
        held = read(pets1)
        board = held["boards"][0]
        board["cards"][k2]["text"] = "Steering at first"
        board["quoted"][k2] = "I took hold of the tiller"
        gone = themes.card_key(s1, 99, 0)
        board["cards"][gone] = {"x": 0, "y": 400, "text": "A statement since removed"}
        write(pets1, held)
        lpd = read(lpfile)
        lpd["cases"]["T1"]["lines"][k2]["quotes"] = ["I took hold of the tiller"]
        lp_card = gets_mod.card_of("T1", "es", k2)
        lpd["boards"][0]["cards"][lp_card]["text"] = "Steering at first"
        write(lpfile, lpd)
        lgd = read(lgfile)
        lgd["cases"]["P1 - Tove"]["lines"][k3]["text"] = "Reading the weather"
        write(lgfile, lgd)

        code, shown, err = run("board", "show", "Tove")
        stale = [s for t in shown.get("themes") or [] for s in t["statements"] if s.get("card_stale")]
        code2, shown_text, _ = run("board", "show", "Tove", as_json=False)
        check("381: board show marks the stale card with the card's own words, lists it, and its text says card stale",
              code == 0 and [s["key"] for s in stale] == [k2] and stale[0]["card_text"] == "Steering at first"
              and stale[0]["text"] == "Steering for the first time" and shown.get("stale_cards") == [k2]
              and code2 == 0 and 'card stale: the card reads "Steering at first"' in shown_text,
              err or str(stale)[:400])

        whole = tree(sail)
        code, dry, err = run("copies", "refresh", "--case", "Tove", "--dry-run")
        code_t, dry_text, _ = run("copies", "refresh", "--case", "Tove", "--dry-run", as_json=False)
        files = {(f["file"], f.get("timepoint")): f for p in dry.get("participants") or [] for f in p["files"]}
        pets_f, lp_f, lg_f = files.get(("pets", "T1")) or {}, files.get(("lpets", None)) or {}, files.get(("lgets", None)) or {}
        check("381: the refresh's dry run names, for the participant and each file, the card, the pick and the copies' "
              "lines and card that would change, and the gone statement's card, by key, and writes nothing",
              code == 0 and [p["case"] for p in dry["participants"]] == ["P1 - Tove"]
              and pets_f.get("cards") == [k2] and pets_f.get("quotes") == [k2] and pets_f.get("missing") == [gone]
              and lp_f.get("quotes") == [k2] and lp_f.get("statements") == []
              and [b["cards"] for b in lp_f.get("boards") or []] == [[lp_card]]
              and lg_f.get("statements") == [k3] and lg_f.get("quotes") == []
              and (dry["cards"], dry["statements"], dry["quotes"], dry["missing"]) == (2, 1, 2, 1)
              and tree(sail) == whole, err or str(dry)[:700])
        check("381: the dry run's lines name keys and never the words, and say the workbook wins over a card marked "
              "changed",
              code_t == 0 and k2 in dry_text and gone in dry_text
              and not any(w in dry_text for w in ("Steering", "tiller", "Reading the", "since removed"))
              and "so the workbook wins" in dry_text, dry_text[:700])
        code, refused, err = run("copies", "refresh", "--case", "Tove")
        check("381: a refresh with no request is refused, nothing written", code != 0 and tree(sail) == whole,
              str(refused)[:300] + err)

        history_was = {"pets": len(read(pets1)["boards"][0].get("history") or []),
                       "lpets": len(read(lpfile)["boards"][0].get("history") or [])}
        code, done, err = run("copies", "refresh", "--case", "Tove", "--note", "Bring Tove's copies back in line",
                              "--tool", "Claude Code")
        after = read(pets1)["boards"][0]
        lpd, lgd = read(lpfile), read(lgfile)
        check("381: the refresh brings the card's words and the pick's quote back on the PETs board, the gone "
              "statement's card left on it",
              code == 0 and after["cards"][k2]["text"] == "Steering for the first time"
              and after["quoted"][k2] == "I took the tiller" and after["picks"].get("g2") == [k2]
              and after["cards"].get(gone, {}).get("text") == "A statement since removed", err or str(done)[:500])
        check("381: and the LPETs' line's quotes and card, and the LGETs' line's words",
              lpd["cases"]["T1"]["lines"][k2]["quotes"] == ["I took the tiller"]
              and lpd["boards"][0]["cards"][lp_card]["text"] == "Steering for the first time"
              and lgd["cases"]["P1 - Tove"]["lines"][k3]["text"] == "Reading the wind",
              str(lpd["cases"]["T1"]["lines"][k2])[:300])
        check("381: one History step on each board it changed, under his request, marked changed by the agent",
              len(after.get("history") or []) == history_was["pets"] + 1
              and after["history"][-1]["name"] == "Before: Bring Tove's copies back in line"
              and after["changed"]["by"] == "agent" and after["changed"]["tool"] == "Claude Code"
              and len(lpd["boards"][0].get("history") or []) == history_was["lpets"] + 1
              and lpd["boards"][0]["changed"]["by"] == "agent", str(after.get("history", [{}])[-1].get("name")))
        st = call("/api/themes", {"workbook": str(book), "timepoint": 1})
        card = next((c for c in st["cards"] if c["key"] == k2), {})
        code, again, err = run("copies", "refresh", "--case", "Tove", "--dry-run")
        code2, shown, _ = run("board", "show", "Tove")
        check("381: the app reads the card as the workbook does, not changed, the pick kept, board show marks no card "
              "stale, and a dry run after lists the gone statement's card alone",
              card.get("text") == "Steering for the first time" and not card.get("changed")
              and st["picks"].get("g2") == [k2] and "stale_cards" not in shown
              and code == 0 and (again["cards"], again["statements"], again["quotes"], again["missing"]) == (0, 0, 0, 1),
              str(again)[:500])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept
