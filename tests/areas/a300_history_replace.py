"""Area 300: a History line for every statement edit, and Find and replace reaching the LPETs and LGETs (histreplace,
30 October 2026).

Adam, 30 October, by dialog: "Add a History line". A statement he edited, on the PETs board's card, in the Inspector,
on the statements screen or from a GETs board, left no line in any board's History, while an agent's `turn write` left
one. Now each edit of his leaves one line in the History of each board that holds a card of the statement, the
participant's PETs boards at the sheet's timepoint and every GETs, LPETs and LGETs board, the board kept as it stood
before, named for the participant and the statement's words before and after, "Osric's statement edited: "..." to
"..."", a long statement shown round its change. One line a board an edit, none for a save that rewords nothing. An
agent's write keeps its own line, "Before: " and his request, one a board it changes, and no second line.

And "Fix it": a replace, its dry run and its undo, the agents' and the app's Replace all alike, reached the GETs' copy
of a participant and no further, so on a project of timepoints the participant's LPETs and the project's LGETs kept
the old words. They follow now, each copy and its cards, the participant still in on both, the dry run writing
nothing and the undo putting them back.

Every word invented: new beekeepers in their first season, Osric and Wenna, asked by Pell.
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


OSRIC = ("Pell: [00:00:03] What did you expect of the bees?\nOsric: [00:00:09] I thought they would sting me every day.\n"
         "Pell: [00:00:40] And the first inspection?\nOsric: [00:12:30] My hands shook lifting the frame out of the hive.\n")
WENNA = ("Pell: [00:00:03] Why keep bees?\nWenna: [00:00:07] To slow down for an hour on a Sunday.\n")
OSRIC_T2 = ("Pell: [00:00:02] How is it now?\nOsric: [00:00:06] I open the hive without gloves and talk to them.\n")
TWO = [{"label": "T1", "description": "First hive"}, {"label": "T2", "description": "After the winter"}]
LONG_OLD = ("Bracing for a sting each time the lid came off, as if the whole colony had been waiting all week for "
            "him to make one wrong move")
LONG_NEW = ("Bracing for a sting each time the lid came off, as if the whole colony had been waiting all week for "
            "him to make one careless move")


def test_history_replace(scratch):
    print("\n300. A History line for every statement edit, on each board that holds the statement, from the PETs board, "
          "the statements screen and a GETs board, an agent's write keeping its own, and Find and replace, its dry run "
          "and its undo reaching the LPETs and LGETs (Adam, 30 October)")
    import cli
    import gets as gets_mod
    import server as server_mod
    import themes
    import workbook as wb_mod

    b64 = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")
    base = scratch / "a300"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    cfg_file = scratch / "a300-config.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "Pell", "corpus": "", "gravity_reference": "",
                                    "corpus_exclude": []}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)

    def tree(at: Path) -> dict:
        return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*"))
                if p.is_file() and p.suffix != ".lock"}

    def row(name, text, who, interview, **more):
        return dict({"name": name, "data": b64(text), "pseudonym": who, "interview": interview,
                     "speakers": {"Pell": "interviewer", who: "participant"}}, **more)

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

    def board_of(book: Path, tp, groups: list):
        """A PETs board, at a timepoint or none, each PET the cards at those places in the canvas's order."""
        body = {"workbook": str(book)} if tp is None else {"workbook": str(book), "timepoint": tp}
        st = call("/api/themes", body)
        keys = [c["key"] for c in st["cards"]]
        words = {c["key"]: c["text"] for c in st["cards"]}
        v = dict(st["version"], cards={k: {"x": 0, "y": 40 * i, "text": words[k]} for i, k in enumerate(keys)},
                 groups=[{"id": f"g{i + 1}", "label": label, "members": [keys[j] for j in at], "x": 300 * i, "y": -40}
                         for i, (label, at) in enumerate(groups)], discarded=[], picks={})
        call("/api/themes-save", dict(body, version=v))

    def board_with(answer: dict, extra: dict, label: str) -> dict:
        """A GETs board as the page saves it, the statements' cards added with their words, one GET over them all."""
        cards = {c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in answer["cards"]}
        cards.update({k: {"x": 700, "y": 60 * i, "text": t} for i, (k, t) in enumerate(extra.items())})
        return dict(answer["version"], cards=cards, groups=[{"id": "G1", "label": label, "members": list(cards),
                                                             "x": -20, "y": -60}], discarded=[], picks={}, notes=[])

    def pets_lines(book: Path, tp=None) -> dict:
        """Each PETs board's History names, by its id, at a timepoint or the first."""
        held = json.loads(themes.themes_path(book, tp).read_text(encoding="utf-8"))
        return {b["id"]: [r.get("name") for r in b.get("history") or []] for b in held["boards"]}

    def file_lines(path: Path) -> dict:
        """Each board's History names in a GETs, LPETs or LGETs file, by its id."""
        held = json.loads(path.read_text(encoding="utf-8"))
        return {b["id"]: [r.get("name") for r in b.get("history") or []] for b in held["boards"]}

    def added(before: dict, after: dict) -> dict:
        """The lines each board gained, by its id."""
        return {k: after[k][len(before.get(k) or []):] for k in after}

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "a300-state.json", {"recent": []}

        # ── A. a project of one timepoint: two PETs boards on Osric, three GETs boards, two with his statements' cards
        apiary = base / "First season"
        apiary.mkdir()
        made = idiograph_routes.api_new_project({"op": "make", "folder": str(apiary), "name": "First season",
                                                 "research_question": "How do new beekeepers live with the risk of a sting?",
                                                 "files": [row("osric.txt", OSRIC, "Osric", "Summer"),
                                                           row("wenna.txt", WENNA, "Wenna", "Summer")]})
        idiograph_routes.api_project({"root": made["project"]["id"], "agents": True})
        osric = apiary / "P1 - Osric" / "P1 Osric - EN & ES.xlsx"
        wenna = apiary / "P2 - Wenna" / "P2 Wenna - EN & ES.xlsx"
        sheet = idiograph_routes.read_sheets(osric)[1][0]
        o, w = said_rows(osric, sheet, "Osric"), said_rows(wenna, sheet, "Wenna")
        wb_mod.save_turn(osric, sheet, o[0], "Expecting a sting\nWaiting to be hurt", "", "")
        wb_mod.save_turn(osric, sheet, o[1], f"Shaking at the first frame\n{LONG_OLD}", "", "")
        wb_mod.save_turn(wenna, sheet, w[0], "An hour of slowness", "", "")
        board_of(osric, None, [("Fear of the sting", [0, 1]), ("Hands that shake", [2, 3])])
        board_of(wenna, None, [("Slowing down", [0])])
        first = themes.load(osric)["boards"][0]["id"]
        call("/api/themes-versions", {"workbook": str(osric), "op": "duplicate", "id": first})
        lines_of = {i: themes.card_key(sheet, o[0], i) for i in range(2)}
        later = {i: themes.card_key(sheet, o[1], i) for i in range(2)}
        es = {k: gets_mod.card_of("P1 - Osric", "es", k) for k in list(lines_of.values()) + list(later.values())}
        g = call("/api/gets", {"workbook": str(osric)})
        call("/api/gets-save", {"workbook": str(osric), "version": board_with(g, {
            es[lines_of[0]]: "Expecting a sting", es[lines_of[1]]: "Waiting to be hurt",
            es[later[0]]: "Shaking at the first frame", es[later[1]]: LONG_OLD}, "Living with the sting")})
        call("/api/gets-ops", {"workbook": str(osric), "op": "duplicate", "id": "b1"})
        call("/api/gets-ops", {"workbook": str(osric), "op": "new"})
        gfile = apiary / gets_mod.FILE
        held = json.loads(gfile.read_text(encoding="utf-8"))
        osric_path = next(c["path"] for c in call("/api/gets", {"workbook": str(osric)})["cases"]
                          if c["case"] == "P1 - Osric")
        check("300: two PETs boards on Osric and three GETs boards, two with his statements' cards",
              len(themes.load(osric)["boards"]) == 2 and len(held["boards"]) == 3
              and [es[lines_of[1]] in b["cards"] for b in held["boards"]] == [True, True, False],
              str([sorted(b["cards"])[:3] for b in held["boards"]]))

        # 1. from the PETs board: the card's editor and the Inspector write through /api/edit-statement
        pets_was, gets_was, wenna_was = pets_lines(osric), file_lines(gfile), pets_lines(wenna)
        edited = call("/api/edit-statement", {"workbook": str(osric), "sheet": sheet, "row": o[0], "line": 1,
                                              "text": "Waiting to be stung", "old": "Waiting to be hurt"})
        line = 'Osric\'s statement edited: "Waiting to be hurt" to "Waiting to be stung"'
        pets_now, gets_now = pets_lines(osric), file_lines(gfile)
        check("300: an edit from the PETs board leaves one line on each of Osric's PETs boards, naming him and the "
              "statement's words before and after",
              edited["changed"] and all(v == [line] for v in added(pets_was, pets_now).values()),
              str(added(pets_was, pets_now)))
        check("300: and one on each GETs board that holds a card of it, none on the board without one, none on Wenna's",
              added(gets_was, gets_now) == {"b1": [line], "b2": [line], "b3": []}
              and pets_lines(wenna) == wenna_was, str(added(gets_was, gets_now)))
        stood = json.loads(themes.themes_path(osric).read_text(encoding="utf-8"))["boards"][0]["history"][-1]["state"]
        kept_g = json.loads(gfile.read_text(encoding="utf-8"))["boards"][0]["history"][-1]["state"]
        check("300: each line keeps the board as it stood before the edit, the old words on its card, and the board "
              "itself takes the new",
              stood["cards"][lines_of[1]]["text"] == "Waiting to be hurt"
              and kept_g["cards"][es[lines_of[1]]]["text"] == "Waiting to be hurt"
              and themes.load(osric)["boards"][0]["cards"][lines_of[1]]["text"] == "Waiting to be stung"
              and json.loads(gfile.read_text(encoding="utf-8"))["boards"][0]["cards"][es[lines_of[1]]]["text"]
              == "Waiting to be stung", str(stood["cards"].get(lines_of[1])))
        check("300: the answer gives each board's History as the tab lists it, the new line first, the PETs boards' "
              "and the GETs boards' with the copy",
              all(h[0]["name"] == line for h in edited["histories"].values()) and len(edited["histories"]) == 2
              and sorted(edited["copies"]["gets"]["histories"]) == ["b1", "b2"]
              and all(h[0]["name"] == line for h in edited["copies"]["gets"]["histories"].values()),
              str(edited.get("histories"))[:400])
        st = call("/api/themes", {"workbook": str(osric)})
        check("300: the PETs screen opens on it with the line in History and no card marked changed",
              st["history"][0]["name"] == line and not [c for c in st["cards"] if c.get("changed")],
              str(st["history"][:1]))

        # 2. a long statement: the line shows the words round the change
        pets_was, gets_was = pets_lines(osric), file_lines(gfile)
        call("/api/edit-statement", {"workbook": str(osric), "sheet": sheet, "row": o[1], "line": 1,
                                     "text": LONG_NEW, "old": LONG_OLD})
        long_line = added(pets_was, pets_lines(osric))[first]
        check("300: a long statement's line shows the words round the change, the rest cut with an ellipsis",
              len(long_line) == 1 and long_line[0] == ('Osric\'s statement edited: "…to make one wrong move" to '
                                                       '"…to make one careless move"')
              and added(gets_was, file_lines(gfile)) == {"b1": long_line, "b2": long_line, "b3": []}, str(long_line))

        # 3. from a GETs board, the participant's own workbook as the Participants panel names it
        pets_was, gets_was = pets_lines(osric), file_lines(gfile)
        from_gets = call("/api/edit-statement", {"workbook": osric_path, "sheet": sheet, "row": o[1], "line": 0,
                                                 "text": "Shaking over the first frame",
                                                 "old": "Shaking at the first frame"})
        line3 = 'Osric\'s statement edited: "Shaking at the first frame" to "Shaking over the first frame"'
        check("300: an edit from a GETs board leaves the same one line on each PETs board and each GETs board holding it",
              from_gets["changed"] and all(v == [line3] for v in added(pets_was, pets_lines(osric)).values())
              and added(gets_was, file_lines(gfile)) == {"b1": [line3], "b2": [line3], "b3": []},
              str(added(gets_was, file_lines(gfile))))
        status = {c["case"]: c["status"] for c in call("/api/gets", {"workbook": str(osric)})["cases"]}
        check("300: Osric stays in on the GETs, his copy following the edits", status == {"P1 - Osric": "in",
                                                                                          "P2 - Wenna": "in"}, str(status))

        # 4. an agent's turn write keeps its own line, one a board, and no second
        def run(*args):
            code, text, err = cli.run(["--root", str(apiary), "--config", str(cfg_file), *args, "--json"])
            return code, (support.plain(json.loads(text)) if text.strip() else {}), err

        code, shown, err = run("turn", "show", "Osric", sheet, str(o[0]))
        version = shown["turns"][0]["version"] if code == 0 and shown.get("turns") else None
        spec = scratch / "a300-turn.json"
        spec.write_text(json.dumps({"pairs": [{"statement": "Expecting a sting", "quote": "", "key": lines_of[0]},
                                              {"statement": "Waiting, braced, to be stung", "quote": "",
                                               "key": lines_of[1]}],
                                    "version": version, "request": "Say braced in Osric's statement"}), encoding="utf-8")
        pets_was, gets_was = pets_lines(osric), file_lines(gfile)
        code, wrote, err = run("turn", "write", "Osric", sheet, str(o[0]), "--from", str(spec), "--tool", "Claude Code")
        agent = "Before: Say braced in Osric's statement"
        check("300: an agent's turn write leaves its own one line on each PETs board and each GETs board holding the "
              "statement, Before: and his request, and no statement-edit line beside it",
              code == 0 and all(v == [agent] for v in added(pets_was, pets_lines(osric)).values())
              and added(gets_was, file_lines(gfile)) == {"b1": [agent], "b2": [agent], "b3": []},
              err or str([added(pets_was, pets_lines(osric)), added(gets_was, file_lines(gfile))]))

        # 5. the statements screen's save: one line a statement reworded, none for a save that rewords nothing
        def commit(pairs: list[str]) -> dict:
            return call("/api/commit", {"path": str(osric), "sheet": sheet, "row": o[0],
                                        "pairs": [{"es": s, "kq": ""} for s in pairs], "en": ""})

        pets_was, gets_was = pets_lines(osric), file_lines(gfile)
        commit(["Expecting a sting", "Waiting, braced, to be stung"])
        check("300: a save on the statements screen that rewords nothing leaves no line anywhere",
              pets_lines(osric) == pets_was and file_lines(gfile) == gets_was)
        saved = commit(["Expecting a sting on the first day", "Waiting, braced, to be stung"])
        line5 = 'Osric\'s statement edited: "Expecting a sting" to "Expecting a sting on the first day"'
        check("300: a statement reworded on the statements screen leaves one line on each PETs board and each GETs board "
              "holding it, and the answer is the save's as ever",
              all(v == [line5] for v in added(pets_was, pets_lines(osric)).values())
              and added(gets_was, file_lines(gfile)) == {"b1": [line5], "b2": [line5], "b3": []}
              and "statements" not in saved and saved.get("changed") is True,
              str([added(pets_was, pets_lines(osric)), added(gets_was, file_lines(gfile)), sorted(saved)]))
        st = call("/api/themes", {"workbook": str(osric)})
        g5 = call("/api/gets", {"workbook": str(osric)})
        check("300: the boards' cards keep their words, so the PETs board shows the card changed and the GETs say Osric "
              "changed since he came in, as ever",
              [c.get("stored") for c in st["cards"] if c.get("changed")] == ["Expecting a sting"]
              and {c["case"]: c["status"] for c in g5["cases"]}["P1 - Osric"] == "changed",
              str([(c["key"], c.get("stored")) for c in st["cards"] if c.get("changed")]))

        # ── B. a project of two timepoints: Osric at both, his LPETs and the project's LGETs
        year = base / "Second season"
        year.mkdir()
        made2 = idiograph_routes.api_new_project({"op": "make", "folder": str(year), "name": "Second season",
                                                  "research_question": "How do new beekeepers live with the risk of a sting?",
                                                  "files": [row("osric-one.txt", OSRIC, "Osric", "Summer")]})
        root2 = made2["project"]["id"]
        idiograph_routes.api_project({"root": root2, "timepoints": TWO})
        idiograph_routes.api_project({"root": root2, "agents": True})
        idiograph_routes.api_add_transcripts({"op": "add", "root": root2, "files": [
            row("osric-two.txt", OSRIC_T2, "Osric", "Spring", timepoint=2)]})
        lo = year / "P1 - Osric" / "P1 Osric - EN & ES.xlsx"
        s1 = idiograph_routes.read_sheets(lo)[1][0]
        s2 = "Spring"
        r1, r2 = said_rows(lo, s1, "Osric"), said_rows(lo, s2, "Osric")
        wb_mod.save_turn(lo, s1, r1[1], "Shaking over the open hive", "", "")
        wb_mod.save_turn(lo, s2, r2[0], "Calm at the open hive", "", "")
        board_of(lo, 1, [("Fear at first", [0])])
        board_of(lo, 2, [("Calm later", [0])])
        k1, k2 = themes.card_key(s1, r1[1], 0), themes.card_key(s2, r2[0], 0)
        lp = call("/api/gets", {"workbook": str(lo), "lpets": True})
        call("/api/gets-save", {"workbook": str(lo), "lpets": True, "version": board_with(
            lp, {gets_mod.card_of("T1", "es", k1): "Shaking over the open hive",
                 gets_mod.card_of("T2", "es", k2): "Calm at the open hive"}, "From fear to calm")})
        lg = call("/api/gets", {"workbook": str(lo)})
        call("/api/gets-save", {"workbook": str(lo), "version": board_with(lg, {
            gets_mod.card_of("P1 - Osric", "es", k1): "Shaking over the open hive",
            gets_mod.card_of("P1 - Osric", "es", k2): "Calm at the open hive"}, "Living with the sting")})
        lpfile, lgfile = gets_mod.lpets_path(lo), year / gets_mod.LGETS_FILE

        def copies() -> dict:
            """Osric's statements as the LPETs and the LGETs keep them, each copy's words and each board's card."""
            lpd, lgd = json.loads(lpfile.read_text(encoding="utf-8")), json.loads(lgfile.read_text(encoding="utf-8"))
            return {"lpets": [lpd["cases"]["T1"]["lines"][k1]["text"], lpd["cases"]["T2"]["lines"][k2]["text"]],
                    "lpets_cards": [lpd["boards"][0]["cards"][gets_mod.card_of(t, "es", k)]["text"]
                                    for t, k in (("T1", k1), ("T2", k2))],
                    "lgets": [lgd["cases"]["P1 - Osric"]["lines"][k]["text"] for k in (k1, k2)],
                    "lgets_cards": [lgd["boards"][0]["cards"][gets_mod.card_of("P1 - Osric", "es", k)]["text"]
                                    for k in (k1, k2)]}

        def statuses() -> dict:
            lp_now = call("/api/gets", {"workbook": str(lo), "lpets": True})
            lg_now = call("/api/gets", {"workbook": str(lo)})
            return {"lpets": {c["case"]: c["status"] for c in lp_now["cases"]},
                    "lgets": {c["case"]: c["status"] for c in lg_now["cases"]}}

        was_copies = copies()
        all_in = {"lpets": {"T1": "in", "T2": "in"}, "lgets": {"P1 - Osric": "in"}}
        check("300: Osric's LPETs and the LGETs hold both timepoints' statements, cards on their boards, all in",
              was_copies == {"lpets": ["Shaking over the open hive", "Calm at the open hive"],
                             "lpets_cards": ["Shaking over the open hive", "Calm at the open hive"],
                             "lgets": ["Shaking over the open hive", "Calm at the open hive"],
                             "lgets_cards": ["Shaking over the open hive", "Calm at the open hive"]}
              and statuses() == all_in, str([was_copies, statuses()]))

        def run2(*args):
            code, text, err = cli.run(["--root", str(year), "--config", str(cfg_file), *args, "--json"])
            return code, (support.plain(json.loads(text)) if text.strip() else {}), err

        # 6. an edit from the LPETs board: one line on its timepoint's PETs board, the LPETs board and the LGETs board
        lp_path = next(c["path"] for c in lp["cases"] if c["case"] == "T2")
        p2_was, lp_was, lg_was = pets_lines(lo, 2), file_lines(lpfile), file_lines(lgfile)
        p1_was = pets_lines(lo, 1)
        call("/api/edit-statement", {"workbook": lp_path, "sheet": s2, "row": r2[0], "line": 0,
                                     "text": "Calm at the open hive now", "old": "Calm at the open hive"})
        line6 = 'Osric\'s statement edited: "Calm at the open hive" to "Calm at the open hive now"'
        check("300: an edit from the LPETs board leaves one line on the later timepoint's PETs board, the LPETs board "
              "and the LGETs board, the first timepoint's board none",
              all(v == [line6] for v in added(p2_was, pets_lines(lo, 2)).values())
              and all(v == [line6] for v in added(lp_was, file_lines(lpfile)).values())
              and all(v == [line6] for v in added(lg_was, file_lines(lgfile)).values())
              and pets_lines(lo, 1) == p1_was,
              str([added(lp_was, file_lines(lpfile)), added(lg_was, file_lines(lgfile))]))
        call("/api/edit-statement", {"workbook": lp_path, "sheet": s2, "row": r2[0], "line": 0,
                                     "text": "Calm at the open hive", "old": "Calm at the open hive now"})
        was_copies, was_files = copies(), tree(year)

        # 7. the agents' replace: its dry run writes nothing, then the LPETs' and the LGETs' copies take the words
        code, dry, err = run2("transcript", "replace", "Osric", "--find", "hive", "--with", "colony", "--dry-run")
        check("300: a replace's dry run on a project of timepoints counts the places and writes nothing",
              code == 0 and dry.get("dry_run") is True and dry.get("replaced", 0) >= 3 and tree(year) == was_files,
              err or str(dry)[:400])
        code, done, err = run2("transcript", "replace", "Osric", "--find", "hive", "--with", "colony",
                               "--note", "Say colony for hive", "--tool", "Claude Code")
        now = copies()
        check("300: the replace reaches Osric's LPETs, both timepoints' copies and the board's cards, and the LGETs' "
              "copy and cards",
              code == 0 and now == {k: [t.replace("hive", "colony") for t in v] for k, v in was_copies.items()},
              err or str(now))
        part = (done.get("participants") or [{}])[0]
        check("300: the answer counts each copy's statements, the LPETs' and the LGETs' beside the GETs'",
              part.get("lpets") == 2 and part.get("lgets") == 2 and part.get("gets") == 0, str(part))
        check("300: Osric stays in on the LPETs at both timepoints and on the LGETs, the replace alone changing nothing "
              "there", statuses() == all_in, str(statuses()))
        code, back, err = run2("transcript", "replace-undo", done.get("batch") or "none", "--note", "Back to hive",
                               "--tool", "Claude Code")
        check("300: the undo puts the LPETs' and the LGETs' copies and cards back, Osric still in",
              code == 0 and copies() == was_copies and statuses() == all_in, err or str([copies(), statuses()]))

        # 8. the app's own Replace all, the same code
        page = idiograph_routes.api_replace({"path": str(lo), "find": "hive", "replace": "colony"})
        took = copies()
        idiograph_routes.api_replace_undo({"path": str(lo), "batch": page["batch"]})
        check("300: the app's Replace all reaches the LPETs and the LGETs too, and its undo puts them back",
              took["lpets"] == ["Shaking over the open colony", "Calm at the open colony"]
              and took["lgets_cards"] == ["Shaking over the open colony", "Calm at the open colony"]
              and page.get("lpets") and page.get("lgets") and copies() == was_copies and statuses() == all_in,
              str([took, sorted(page)]))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept
