"""Area 430: a statement reworded on the statements screen reaches every board's card and stays there (cardsync2, 18
November 2026, from the GRAVITY session: Adam's edits on the statements screen reached the workbook, and the cards on
his boards and in the GETs kept the old words. Adam: "I thought cards on the boards automatically use the new wording
from any experiential statements, they're meant to be a live link").

The statements screen's save had kept a History line on each board and left the cards' words, so a board showed the
card changed and the GETs, `board show` and the exports read the old wording until `copies refresh`. Now the save
carries the words as an edit on a board's card does: every PETs board of the participant and every copy (the GETs')
takes the new words, each board keeping itself first in its History under the edit's line. And a board page left open
since before the edit, still holding the old words, saves over the board as if nothing had happened, its move kept and
the new words kept with it, the page told which cards kept them. A real conflict, another window's save since, is
refused as ever, and a save from a page that sends no version never puts the old words back either. An open GETs page
reloads for an edit once and then rests, also after the board changes in place.

In a thematic analysis project a recode, on the Coding screen, from a code's card on the Themes board or by an agent's
turn write, lands on the Themes board in the same save, under its code's card and in that code's theme (cardsync3,
Adam, 18 November 2026, "yes"), with one History line on each board, and a Themes page open since before it is
refused. Since cardsync4 (Adam, about 22:00 that day, "yes") every change to an extract's codes lands at the save: a
code added, one of two taken off, one taken off and another put on in two saves, the command line's `codes add` and
`codes remove` and an agent's turn write adding a code. The recoded card never leads its new code, also when that code
has one extract and the old code's theme reads first, Restore of the recode's line and an Overwrite from a page open
since before it leave each code in one theme, a code new to the board comes in clear of every card, a board with no
card of either code keeps no line, and an agent's dry run says which boards would take it.

Every word invented: new kite fliers in their first spring, Corin and Elspa, asked by Brann."""
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


CORIN = ("Brann: [00:00:03] What was the first flight like?\nCorin: [00:00:09] The line pulled so hard I thought it "
         "would lift me.\nBrann: [00:00:40] And after?\nCorin: [00:01:30] I learnt to let the kite have the wind.\n")
ELSPA = ("Brann: [00:00:03] Why kites?\nElspa: [00:00:07] To stand on a hill and do nothing else.\n")


def test_cards_follow_edits(scratch):
    print("\n430. A statement reworded on the statements screen reaches every board's card and the GETs, and a board "
          "page open since before the edit never puts the old words back (cardsync2)")
    import gets as gets_mod
    import server as server_mod
    import themes
    import workbook as wb_mod

    b64 = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")
    base = scratch / "a430"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    cfg_file = scratch / "a430-config.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "Brann", "corpus": "", "gravity_reference": "",
                                    "corpus_exclude": []}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)

    def row(name, text, who):
        return {"name": name, "data": b64(text), "pseudonym": who, "interview": "Spring",
                "speakers": {"Brann": "interviewer", who: "participant"}}

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

    def page_body(st: dict, groups=None, move=None) -> dict:
        """The board as an open page saves it: its version as the page read it, every card with the words the page
        holds, a card moved by `move` (key, dx)."""
        cards = {c["key"]: {"x": c.get("x", 0), "y": c.get("y", 0), "text": c["text"]} for c in st["cards"]}
        for k, c in (st["version"].get("cards") or {}).items():
            if k in cards:
                cards[k].update(x=c.get("x", 0), y=c.get("y", 0))
        if move:
            cards[move[0]]["x"] += move[1]
        v = dict(st["version"], cards=cards, discarded=[], picks={})
        v["groups"] = groups if groups is not None else st["version"].get("groups") or []
        return v

    def pets_cards(book: Path) -> dict:
        """Each PETs board's card words by board id and key, as the file keeps them."""
        held = support.board_file(themes.themes_path(book))
        return {b["id"]: {k: c.get("text") for k, c in b["cards"].items()} for b in held["boards"]}

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "a430-state.json", {"recent": []}

        hill = base / "First spring"
        hill.mkdir()
        idiograph_routes.api_new_project({"op": "make", "folder": str(hill), "name": "First spring",
                                          "research_question": "How do new kite fliers learn the wind?",
                                          "files": [row("corin.txt", CORIN, "Corin"), row("elspa.txt", ELSPA, "Elspa")]})
        corin = hill / "P1 - Corin" / "P1 Corin - EN & ES.xlsx"
        sheet = idiograph_routes.read_sheets(corin)[1][0]
        o = said_rows(corin, sheet, "Corin")
        wb_mod.save_turn(corin, sheet, o[0], "Pulled by the line\nAfraid of being lifted", "", "")
        wb_mod.save_turn(corin, sheet, o[1], "Letting the kite have the wind", "", "")
        k0, k1, k2 = (themes.card_key(sheet, o[0], 0), themes.card_key(sheet, o[0], 1),
                      themes.card_key(sheet, o[1], 0))
        # two PETs boards on Corin, each one PET over the three statements
        st = call("/api/themes", {"workbook": str(corin)})
        pet = [{"id": "g1", "label": "The pull of the line", "members": [k0, k1, k2], "x": 0, "y": -40}]
        laid = page_body(st, groups=pet)
        for i, k in enumerate([k0, k1, k2]):
            laid["cards"][k].update(x=0, y=60 * i)
        call("/api/themes-save", {"workbook": str(corin), "version": laid})
        first = themes.load(corin)["boards"][0]["id"]
        call("/api/themes-versions", {"workbook": str(corin), "op": "duplicate", "id": first})
        boards = [b["id"] for b in themes.load(corin)["boards"]]
        # a GETs board holding Corin's statements' cards
        g = call("/api/gets", {"workbook": str(corin)})
        es = {k: gets_mod.card_of("P1 - Corin", "es", k) for k in (k0, k1, k2)}
        cards = {c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in g["cards"]}
        cards.update({es[k0]: {"x": 700, "y": 0, "text": "Pulled by the line"},
                      es[k1]: {"x": 700, "y": 60, "text": "Afraid of being lifted"},
                      es[k2]: {"x": 700, "y": 120, "text": "Letting the kite have the wind"}})
        call("/api/gets-save", {"workbook": str(corin), "version": dict(
            g["version"], cards=cards, groups=[{"id": "G1", "label": "Learning the wind", "members": list(cards),
                                                "x": -20, "y": -60}], discarded=[], picks={}, notes=[])})
        gfile = hill / gets_mod.FILE
        check("430: two PETs boards on Corin and a GETs board, each with a card of every statement of his",
              len(boards) == 2 and all(set(c) >= {k0, k1, k2} for c in pets_cards(corin).values())
              and all(es[k] in support.board_file(gfile)["boards"][0]["cards"] for k in (k0, k1, k2)),
              str(pets_cards(corin)))

        # a board page and a GETs page open since before the edit, holding the old words
        page = call("/api/themes", {"workbook": str(corin), "board": first})
        gpage = call("/api/gets", {"workbook": str(corin)})
        history_was = {b["id"]: len(b.get("history") or []) for b in support.board_file(themes.themes_path(corin))["boards"]}

        # the statements screen's save rewords the second statement of the first passage
        saved = call("/api/commit", {"path": str(corin), "sheet": sheet, "row": o[0], "en": "",
                                     "pairs": [{"es": "Pulled by the line", "kq": ""},
                                               {"es": "Afraid the line would lift him", "kq": ""}]})
        new = "Afraid the line would lift him"
        now = pets_cards(corin)
        check("430: the save goes through as ever",
              saved.get("changed") is True and "error" not in saved, str(sorted(saved)))
        check("430: every PETs board's card of the statement takes the new words, the others keep theirs",
              all(c[k1] == new and c[k0] == "Pulled by the line" and c[k2] == "Letting the kite have the wind"
                  for c in now.values()), str(now))
        gheld = support.board_file(gfile)
        check("430: the GETs' copy of the statement and the GETs board's card take the new words",
              gheld["cases"]["P1 - Corin"]["lines"][k1]["text"] == new
              and gheld["boards"][0]["cards"][es[k1]]["text"] == new,
              str([gheld["cases"]["P1 - Corin"]["lines"][k1]["text"], gheld["boards"][0]["cards"][es[k1]].get("text")]))
        pheld = support.board_file(themes.themes_path(corin))["boards"]
        check("430: each PETs board keeps one line in its History, the board as it stood with the old words",
              all(len(b.get("history") or []) == history_was[b["id"]] + 1 for b in pheld)
              and all(b["history"][-1]["state"]["cards"][k1]["text"] == "Afraid of being lifted" for b in pheld),
              str([(b["id"], len(b.get("history") or [])) for b in pheld]))
        st_now = call("/api/themes", {"workbook": str(corin), "board": first})
        status = {c["case"]: c["status"] for c in call("/api/gets", {"workbook": str(corin)})["cases"]}
        check("430: the PETs board opens with no card marked changed, and Corin stays in on the GETs",
              not [c for c in st_now["cards"] if c.get("changed")] and status.get("P1 - Corin") == "in",
              str([status, [c["key"] for c in st_now["cards"] if c.get("changed")]]))

        # the page open since before the edit saves a move, its old words and its old version with it
        moved = call("/api/themes-save", {"workbook": str(corin), "version": page_body(page, move=(k2, 40))})
        after = support.board_file(themes.themes_path(corin))["boards"]
        on = next(b for b in after if b["id"] == first)
        check("430: the open page's save goes through, not refused as stale",
              moved.get("saved") is True and moved.get("status") != 409, str(moved)[:300])
        check("430: the board keeps the new words and takes the page's move, and the page is told the card it kept",
              on["cards"][k1]["text"] == new and on["cards"][k2]["x"] == page_body(page)["cards"][k2]["x"] + 40
              and moved.get("followed") == {k1: new}, str([on["cards"][k1], moved.get("followed")]))
        check("430: the other PETs board keeps the new words too",
              all(b["cards"][k1]["text"] == new for b in after), str([b["cards"][k1]["text"] for b in after]))

        # a GETs page open in another window learns of the edit by its stamp, the board stamped by this app
        stamp = call("/api/stamp", {"workbook": str(corin), "gets": True})
        here = next((b for b in stamp["boards"] if b["id"] == gpage["version"]["id"]), {})
        reread = call("/api/gets", {"workbook": str(corin)})
        check("430: the GETs stamp names the version the edit left the board in, not the open page's, and the one a "
              "fresh read gives, so the page takes it in once and then rests",
              here.get("followed") and here.get("followed") != gpage["version"].get("v")
              and here.get("followed") == reread["version"].get("v") and stamp["outside"] is False,
              str([here.get("followed"), gpage["version"].get("v"), reread["version"].get("v"), stamp.get("outside")]))

        # the GETs page open since before the edit saves too
        gsaved = call("/api/gets-save", {"workbook": str(corin), "version": dict(
            gpage["version"], cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c.get("text", "")}
                                     for c in gpage["cards"]},
            groups=gpage["version"].get("groups") or [], discarded=[], picks={}, notes=[])})
        gnow = support.board_file(gfile)
        check("430: the GETs page open since before the edit saves, and the GETs card keeps the new words",
              gsaved.get("saved") is True and gnow["boards"][0]["cards"][es[k1]]["text"] == new,
              str([gsaved.get("error"), gnow["boards"][0]["cards"][es[k1]].get("text")]))

        # a real conflict: another window saved the board since this page read it, so it is refused as ever
        one = call("/api/themes", {"workbook": str(corin), "board": first})
        two = call("/api/themes", {"workbook": str(corin), "board": first})
        call("/api/themes-save", {"workbook": str(corin), "version": page_body(one, move=(k0, 20))})
        refused = call("/api/themes-save", {"workbook": str(corin), "version": page_body(two, move=(k2, 20))})
        check("430: a page that read the board before another window's save is still refused as stale",
              refused.get("status") == 409 and refused.get("stale"), str(refused)[:300])

        # an edit, then a save from a page that sends no version at all with the old words: the new words stay
        back = call("/api/themes", {"workbook": str(corin), "board": first})
        call("/api/commit", {"path": str(corin), "sheet": sheet, "row": o[1], "en": "",
                             "pairs": [{"es": "Letting the kite take the wind", "kq": ""}]})
        bare = page_body(back)
        bare.pop("v", None)
        call("/api/themes-save", {"workbook": str(corin), "version": bare})
        check("430: a save with no version and the old words never puts them back",
              all(c[k2] == "Letting the kite take the wind" for c in pets_cards(corin).values())
              and support.board_file(gfile)["boards"][0]["cards"][es[k2]]["text"] == "Letting the kite take the wind",
              str(pets_cards(corin)))

        # and a card the page took the workbook's words onto is saved as it was sent
        took = call("/api/themes", {"workbook": str(corin), "board": first})
        body = page_body(took)
        body["cards"][k0]["text"] = "Pulled by the line"
        call("/api/themes-save", {"workbook": str(corin), "version": body})
        check("430: a card already in step is left as it is",
              pets_cards(corin)[first][k0] == "Pulled by the line", str(pets_cards(corin)[first]))

        # an open GETs page rests once the board changes in place after an edit: a reword with a new quote leaves
        # Corin changed, which the page takes by itself, and from then on the stamp names no version to reload for
        call("/api/commit", {"path": str(corin), "sheet": sheet, "row": o[1], "en": "",
                             "pairs": [{"es": "Letting the kite have all the wind", "kq": "let the kite have the wind"}]})
        gid = support.board_file(gfile)["boards"][0]["id"]
        live = next((b for b in call("/api/stamp", {"workbook": str(corin), "gets": True})["boards"]
                     if b["id"] == gid), {})
        call("/api/gets-cases", {"workbook": str(corin), "op": "take", "case": "P1 - Corin"})
        ticks = [next((b for b in call("/api/stamp", {"workbook": str(corin), "gets": True})["boards"]
                       if b["id"] == gid), {}) for _ in range(2)]
        mark = support.board_file(gfile)["boards"][0].get(themes.FOLLOWED) or {}
        check("430: after a Take the changes moves the board on from an edit, the stamp names no followed version, "
              "so an open GETs page stops reloading",
              live.get("followed") and mark.get("to") and not any(t.get("followed") for t in ticks),
              str([live.get("followed"), mark.get("to"), [t.get("followed") for t in ticks]]))

        longitudinal(base, cfg_file, call, page_body, row, said_rows)
        thematic(base, cfg_file, call, b64, said_rows)
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept


CORIN_T2 = ("Brann: [00:00:02] How is it now?\nCorin: [00:00:06] I let the line run and the kite climbs.\n")
TWO = [{"label": "T1", "description": "First spring"}, {"label": "T2", "description": "The autumn after"}]


def longitudinal(base: Path, cfg_file: Path, call, page_body, row, said_rows):
    """A project of two timepoints: an LPETs page and an LGETs page open since before a statements screen's save keep
    the new words when they save."""
    import gets as gets_mod
    import themes
    import workbook as wb_mod

    year = base / "Two seasons"
    year.mkdir()
    made = idiograph_routes.api_new_project({"op": "make", "folder": str(year), "name": "Two seasons",
                                             "research_question": "How do new kite fliers learn the wind?",
                                             "files": [row("corin-one.txt", CORIN, "Corin")]})
    root = made["project"]["id"]
    support.make_lipa(root)
    idiograph_routes.api_project({"root": root, "timepoints": TWO})
    idiograph_routes.api_add_transcripts({"op": "add", "root": root, "files": [
        dict(row("corin-two.txt", CORIN_T2, "Corin"), interview="Autumn", timepoint=2)]})
    lo = year / "P1 - Corin" / "P1 Corin - EN & ES.xlsx"
    s1 = idiograph_routes.read_sheets(lo)[1][0]
    r1, r2 = said_rows(lo, s1, "Corin"), said_rows(lo, "Autumn", "Corin")
    wb_mod.save_turn(lo, s1, r1[0], "Pulled by the line", "", "")
    wb_mod.save_turn(lo, "Autumn", r2[0], "Letting the line run", "", "")
    for tp in (1, 2):
        st = call("/api/themes", {"workbook": str(lo), "timepoint": tp})
        keys = [c["key"] for c in st["cards"]]
        body = page_body(st, groups=[{"id": "g1", "label": "The line", "members": keys, "x": 0, "y": -40}])
        call("/api/themes-save", {"workbook": str(lo), "timepoint": tp, "version": body})
    k1, k2 = themes.card_key(s1, r1[0], 0), themes.card_key("Autumn", r2[0], 0)

    def board_with(answer, extra, label):
        cards = {c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in answer["cards"]}
        cards.update({k: {"x": 700, "y": 60 * i, "text": t} for i, (k, t) in enumerate(extra.items())})
        return dict(answer["version"], cards=cards, groups=[{"id": "G1", "label": label, "members": list(cards),
                                                             "x": -20, "y": -60}], discarded=[], picks={}, notes=[])

    lp = call("/api/gets", {"workbook": str(lo), "lpets": True})
    lp_card = gets_mod.card_of("T1", "es", k1)
    call("/api/gets-save", {"workbook": str(lo), "lpets": True, "version": board_with(
        lp, {lp_card: "Pulled by the line", gets_mod.card_of("T2", "es", k2): "Letting the line run"}, "Learning to let go")})
    lg = call("/api/gets", {"workbook": str(lo)})
    lg_card = gets_mod.card_of("P1 - Corin", "es", k1)
    call("/api/gets-save", {"workbook": str(lo), "version": board_with(
        lg, {lg_card: "Pulled by the line", gets_mod.card_of("P1 - Corin", "es", k2): "Letting the line run"},
        "Learning to let go")})
    lpfile, lgfile = gets_mod.lpets_path(lo), year / gets_mod.LGETS_FILE
    # the LPETs page and the LGETs page, open since before the edit
    lp_page = call("/api/gets", {"workbook": str(lo), "lpets": True})
    lg_page = call("/api/gets", {"workbook": str(lo)})
    call("/api/commit", {"path": str(lo), "sheet": s1, "row": r1[0], "en": "",
                         "pairs": [{"es": "Pulled hard by the line", "kq": ""}]})
    new = "Pulled hard by the line"
    lpd, lgd = support.board_file(lpfile), support.board_file(lgfile)
    check("430: on two timepoints the LPETs' and the LGETs' copies and their cards take the new words",
          lpd["cases"]["T1"]["lines"][k1]["text"] == new and lpd["boards"][0]["cards"][lp_card]["text"] == new
          and lgd["cases"]["P1 - Corin"]["lines"][k1]["text"] == new and lgd["boards"][0]["cards"][lg_card]["text"] == new,
          str([lpd["boards"][0]["cards"][lp_card].get("text"), lgd["boards"][0]["cards"][lg_card].get("text")]))

    def old_save(page, lpets):
        body = dict(page["version"], cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c.get("text", "")}
                                            for c in page["cards"]},
                    groups=page["version"].get("groups") or [], discarded=[], picks={}, notes=[])
        return call("/api/gets-save", dict({"workbook": str(lo), "version": body}, **({"lpets": True} if lpets else {})))

    lp_saved, lg_saved = old_save(lp_page, True), old_save(lg_page, False)
    lpd, lgd = support.board_file(lpfile), support.board_file(lgfile)
    check("430: an LPETs page and an LGETs page open since before the edit save, and their cards keep the new words",
          lp_saved.get("saved") is True and lg_saved.get("saved") is True
          and lpd["boards"][0]["cards"][lp_card]["text"] == new and lgd["boards"][0]["cards"][lg_card]["text"] == new,
          str([lp_saved.get("error"), lg_saved.get("error"), lpd["boards"][0]["cards"][lp_card].get("text"),
               lgd["boards"][0]["cards"][lg_card].get("text")]))


TA_CORIN = ("Brann: [00:00:03] What was the first flight like?\nCorin: [00:00:09] The line pulled so hard I thought it "
            "would lift me.\nBrann: [00:00:40] And after?\nCorin: [00:01:30] I learnt to let the kite have the wind.\n"
            "Brann: [00:02:00] And now?\nCorin: [00:02:10] I still hold on too hard.\n")


def thematic(base: Path, cfg_file: Path, call, b64, said_rows):
    """A thematic analysis project: a code typed over on one extract is a recode, and every recode, on the Coding
    screen, from the code's card on a Themes board or by an agent's turn write, lands on the Themes board in the same
    save, under its code's card and in that code's theme (cardsync3, Adam, 18 November 2026, "yes"), so the code never
    stands in two themes and nothing waits for Take the changes. Each board keeps itself first in its History, and
    Restore puts it back. A Themes page open since before the recode is refused, so its old board never moves the
    code back. An agent's dry run writes nothing."""
    import cli
    import gets as gets_mod
    import themes

    def made(name: str, ease: int = 2) -> dict:
        """A project with Theme of fear holding the first extract, coded Fear, and Theme of ease holding the code
        Ease, the second and third extracts, or with `ease` of 1 the second alone, the third coded Hold and on no
        board, and a Themes page open on it. Theme of fear reads first, at the left."""
        hill = base / name
        hill.mkdir()
        project = idiograph_routes.api_new_project({
            "op": "make", "folder": str(hill), "name": name, "method": "ta",
            "research_question": "How do new kite fliers learn the wind?",
            "files": [{"name": "corin.txt", "data": b64(TA_CORIN), "pseudonym": "Corin", "interview": "Spring",
                       "speakers": {"Brann": "interviewer", "Corin": "participant"}}]})
        idiograph_routes.api_project({"root": project["project"]["id"], "agents": True})
        book = next(hill.glob("P1*/*.xlsx"))
        sheet = idiograph_routes.read_sheets(book)[1][0]
        o = said_rows(book, sheet, "Corin")

        def commit(r, es, kq):
            return call("/api/commit", {"path": str(book), "sheet": sheet, "row": r, "en": "",
                                        "pairs": [{"es": es, "kq": kq}]})

        commit(o[0], "Fear", "thought it would lift me")
        commit(o[1], "Ease", "let the kite have the wind")
        commit(o[2], "Ease" if ease == 2 else "Hold", "hold on too hard")
        g = call("/api/gets", {"workbook": str(book)})
        case = g["cases"][0]["case"]
        k = [gets_mod.card_of(case, "es", themes.card_key(sheet, r, 0)) for r in o]
        cards = {c["key"]: {"x": c["x"], "y": c["y"], "text": c.get("text", "")} for c in g["cards"]}
        cards[k[0]] = {"x": 0, "y": 0, "text": "Fear"}
        cards[k[1]] = {"x": 600, "y": 0, "text": "Ease"}
        call("/api/gets-save", {"workbook": str(book), "version": dict(
            g["version"], cards=cards,
            groups=[{"id": "G1", "label": "Theme of fear", "members": [k[0]], "x": -20, "y": -60},
                    {"id": "G2", "label": "Theme of ease", "members": [k[1]], "x": 580, "y": -60}],
            discarded=[], picks={}, notes=[])})
        gfile = hill / gets_mod.FILE
        status = {c["case"]: c["status"] for c in call("/api/gets", {"workbook": str(book)})["cases"]}
        held = support.board_file(gfile)
        b = held["boards"][0]
        check(f"430 ({name}): Theme of fear holds Fear's extract and Theme of ease the code Ease, its two extracts, "
              "with the participant in",
              status.get(case) == "in" and {x["label"]: x["members"] for x in b["groups"]}.get("Theme of fear") == [k[0]]
              and k[1] in {x["label"]: x["members"] for x in b["groups"]}.get("Theme of ease", []),
              str([status, [(x["label"], x["members"]) for x in b["groups"]]]))
        page = call("/api/gets", {"workbook": str(book)})
        return {"hill": hill, "book": book, "sheet": sheet, "o": o, "case": case, "k": k, "gfile": gfile,
                "was": held, "page": page, "commit": commit, "ease": k[:3] if ease == 2 else k[:2]}

    def landed(tag: str, p: dict, history: int | None = None) -> None:
        """The recode landed: the first extract under the Ease card in Theme of ease, each code in one theme, the
        participant in, one more History line per board holding the board as it stood, and Restore puts it back."""
        held = support.board_file(p["gfile"])
        b, b0 = held["boards"][0], p["was"]["boards"][0]
        k = p["k"]
        lines = held["cases"][p["case"]]["lines"]
        by_code: dict = {}
        for key in p["ease"]:
            code = lines[gets_mod.split_key(key)["ident"]]["text"]
            by_code.setdefault(code, set()).update(x["label"] for x in b["groups"] if key in x["members"])
        g = call("/api/gets", {"workbook": str(p["book"])})
        status = {c["case"]: c["status"] for c in g["cases"]}
        shown = {c["key"]: c.get("text") for c in g["cards"]}
        in_ease = next((x["members"] for x in g["groups"] if x["label"] == "Theme of ease"), [])
        in_fear = next((x["members"] for x in g["groups"] if x["label"] == "Theme of fear"), [])
        check(f"430: a recode {tag} lands the extract under the Ease card in Theme of ease, at the save",
              lines[gets_mod.split_key(k[0])["ident"]]["text"] == "Ease"
              and all(key in next(x["members"] for x in b["groups"] if x["label"] == "Theme of ease") for key in p["ease"])
              and not next(x["members"] for x in b["groups"] if x["label"] == "Theme of fear"),
              str([(x["label"], x["members"]) for x in b["groups"]]))
        check(f"430: after a recode {tag} the file holds each code in one theme, the board shows one Ease card in "
              "Theme of ease and none in Theme of fear, and the participant is in",
              by_code == {"Ease": {"Theme of ease"}} and status.get(p["case"]) == "in"
              and [shown.get(x) for x in in_ease if x in shown] == ["Ease"] and not in_fear,
              str([by_code, status, in_ease, in_fear]))
        revs = b.get("history") or []
        before = len(b0.get("history") or [])
        check(f"430: a recode {tag} keeps one line in the board's History, the board as it stood",
              len(revs) == before + 1 and {x["label"]: x["members"] for x in revs[-1]["state"]["groups"]}
              == {x["label"]: x["members"] for x in b0["groups"]}
              and (history is None or revs[-1].get("name") == history),
              str([len(revs), before, revs[-1].get("name") if revs else None]))
        # an old page open since before the recode saves its board: refused, the code left where it now stands
        old = p["page"]
        refused = call("/api/gets-save", {"workbook": str(p["book"]), "version": dict(
            old["version"], cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c.get("text", "")} for c in old["cards"]},
            groups=old["version"].get("groups") or [], discarded=[], picks={}, notes=[])})
        after = support.board_file(p["gfile"])["boards"][0]
        check(f"430: a Themes page open since before a recode {tag} is refused, and the code stays in Theme of ease",
              refused.get("status") == 409 and after["groups"] == b["groups"] and after["cards"] == b["cards"],
              str(refused)[:300])
        # and its Overwrite, the same board with no version, never moves the code (cardsync4)
        over = call("/api/gets-save", {"workbook": str(p["book"]), "version": dict(
            {a: v for a, v in old["version"].items() if a != "v"},
            cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c.get("text", "")} for c in old["cards"]},
            groups=old["groups"], discarded=[], picks={}, notes=[])})
        after = support.board_file(p["gfile"])
        check(f"430: an Overwrite from a Themes page open since before a recode {tag} saves and leaves the code Ease "
              "in Theme of ease alone",
              over.get("saved") and places(after, p["case"]).get("ease") == {("Theme of ease", False)},
              str([over.get("error"), places(after, p["case"])]))
        # Restore of that History line puts the board as it stood back, and the code its extract has now is gathered
        # where that code stands, each code in one theme (cardsync4)
        back = call("/api/gets-boards", {"workbook": str(p["book"]), "op": "restore", "id": str(b["id"]),
                                         "revision": str(revs[-1]["id"])})
        now = support.board_file(p["gfile"])
        check(f"430: Restore of the recode's History line {tag} leaves each code in one theme, Ease in Theme of ease",
              "error" not in back and all(len(v) == 1 for v in places(now, p["case"]).values())
              and places(now, p["case"]).get("ease") == {("Theme of ease", False)},
              str([back.get("error"), places(now, p["case"])]))

    # the Coding screen: the first extract's code typed over, Fear to Ease, the History line naming the code
    p = made("Kites TA coding")
    import i18n
    with i18n.in_method("ta"):
        line = themes.edit_line("Corin", "Fear", "Ease")
    check("430: a recode's History line in a thematic analysis project names the code", "code edited" in line, line)
    saved = p["commit"](p["o"][0], "Ease", "thought it would lift me")
    check("430: the Coding screen's recode saves", saved.get("changed") is True and "error" not in saved,
          str(sorted(saved)))
    landed("on the Coding screen", p, history=line)

    # a card on the Themes board: the code edited from the first extract's card
    p = made("Kites TA card")
    out = call("/api/edit-statement", {"workbook": str(p["book"]), "sheet": p["sheet"], "row": p["o"][0], "line": 0,
                                       "text": "Ease", "old": "Fear"})
    check("430: the code edited from its card on the Themes board saves, and the page is told to read the board back",
          out.get("changed") is True and out.get("recoded") is True and (out.get("copies") or {}).get("gets"),
          str({a: out.get(a) for a in ("changed", "recoded", "error")}))
    landed("from a card on the Themes board", p, history=line)

    # Ease with one extract, in Theme of ease, Theme of fear reading first: the recoded card never leads Ease into
    # Theme of fear (cardsync4), on the Coding screen and from the card
    p = made("Kites TA one", ease=1)
    p["commit"](p["o"][0], "Ease", "thought it would lift me")
    landed("to a code of one extract on the Coding screen", p, history=line)
    p = made("Kites TA one card", ease=1)
    call("/api/edit-statement", {"workbook": str(p["book"]), "sheet": p["sheet"], "row": p["o"][0], "line": 0,
                                 "text": "Ease", "old": "Fear"})
    landed("to a code of one extract from its card", p, history=line)

    # a code whose recoded extracts leave the old code no card on the board keeps the old code's place, its theme or
    # Set aside, since nothing is left there for the new card to lie on (cardsync5): typed over on the Coding screen
    # (A1), retitled from its card (D1), set aside and then retitled (D2), and a code of two extracts retyped one
    # extract after the other, which ends in its theme (A1b)
    p = made("Kites TA typo", ease=1)
    p["commit"](p["o"][0], "Dread", "thought it would lift me")
    held = support.board_file(p["gfile"])
    check("430: a code of one extract typed over on the Coding screen stays in its theme under its new words",
          places(held, p["case"]).get("dread") == {("Theme of fear", False)} and status_of(call, p) == "in",
          str([status_of(call, p), places(held, p["case"])]))
    p = made("Kites TA retitle", ease=1)
    call("/api/edit-statement", {"workbook": str(p["book"]), "sheet": p["sheet"], "row": p["o"][0], "line": 0,
                                 "text": "Dread", "old": "Fear"})
    held = support.board_file(p["gfile"])
    check("430: a code of one extract retitled from its card on the Themes board stays in its theme",
          places(held, p["case"]).get("dread") == {("Theme of fear", False)} and status_of(call, p) == "in",
          str([status_of(call, p), places(held, p["case"])]))
    p = made("Kites TA aside", ease=1)
    g = call("/api/gets", {"workbook": str(p["book"])})
    cards = {c["key"]: {"x": c["x"], "y": c["y"], "text": c.get("text", "")} for c in g["cards"]}
    cards[p["k"][0]] = {"x": 0, "y": 400, "text": "Fear"}
    call("/api/gets-save", {"workbook": str(p["book"]), "version": dict(
        g["version"], cards=cards, groups=[dict(x, members=[m for m in x["members"] if m != p["k"][0]])
                                           for x in g["groups"]],
        discarded=[p["k"][0]], picks={}, notes=[])})
    call("/api/edit-statement", {"workbook": str(p["book"]), "sheet": p["sheet"], "row": p["o"][0], "line": 0,
                                 "text": "Dread", "old": "Fear"})
    held = support.board_file(p["gfile"])
    check("430: a code of one extract set aside and then retitled from its card stays set aside",
          places(held, p["case"]).get("dread") == {(None, True)} and status_of(call, p) == "in",
          str([status_of(call, p), places(held, p["case"])]))
    p = made("Kites TA retype")
    p["commit"](p["o"][1], "Calm", "let the kite have the wind")
    first = places(support.board_file(p["gfile"]), p["case"])
    p["commit"](p["o"][2], "Calm", "hold on too hard")
    held = support.board_file(p["gfile"])
    check("430: a code of two extracts retyped one extract after the other stays in its theme at each step, clear of "
          "the old code's card",
          first.get("calm") == {("Theme of ease", False)} and first.get("ease") == {("Theme of ease", False)}
          and places(held, p["case"]) == {"fear": {("Theme of fear", False)}, "calm": {("Theme of ease", False)}}
          and len(members(held["boards"][0], "Theme of ease")) == 2 and status_of(call, p) == "in",
          str([first, places(held, p["case"])]))

    # a code of two extracts set aside, one extract retyped as a code new to the study: the new code comes in loose,
    # seen and not counted decided, and the old code stays set aside; the second retyped too joins it loose
    # (cardsync7, recheck6 A1)
    p = made("Kites TA aside two")
    g = call("/api/gets", {"workbook": str(p["book"])})
    cards = {c["key"]: {"x": c["x"], "y": c["y"], "text": c.get("text", "")} for c in g["cards"]}
    eases = [k for k in cards if k in p["k"][1:3]]
    for n, k in enumerate(eases):
        cards[k] = {"x": 1800 + 400 * n, "y": 900, "text": "Ease"}
    call("/api/gets-save", {"workbook": str(p["book"]), "version": dict(
        g["version"], cards=cards, groups=[dict(x, members=[m for m in x["members"] if m not in eases])
                                           for x in g["groups"]],
        discarded=eases, picks={}, notes=[])})
    was = places(support.board_file(p["gfile"]), p["case"])
    p["commit"](p["o"][1], "Calm", "let the kite have the wind")
    first = places(support.board_file(p["gfile"]), p["case"])
    p["commit"](p["o"][2], "Calm", "hold on too hard")
    held = support.board_file(p["gfile"])
    check("430: a code split off a code set aside comes in loose, never set aside unseen, and the old code stays set "
          "aside",
          was.get("ease") == {(None, True)} and first.get("calm") == {(None, False)}
          and first.get("ease") == {(None, True)} and status_of(call, p) == "in", str([was, first]))
    check("430: a code of two extracts set aside, retyped one extract after the other, ends loose and seen",
          places(held, p["case"]) == {"fear": {("Theme of fear", False)}, "calm": {(None, False)}}
          and status_of(call, p) == "in", str(places(held, p["case"])))

    # a turn in one passage, [Fear, Dread] typed over as [Dread, Awe], Dread in a theme of its own: Dread's card
    # follows its words and Awe takes no place, so the History line names Fear taken off alone (cardsync7, recheck6
    # Low 2)
    p = made("Kites TA turn")
    call("/api/commit", {"path": str(p["book"]), "sheet": p["sheet"], "row": p["o"][0], "en": "",
                         "pairs": [{"es": "Fear", "kq": "thought it would lift me"},
                                   {"es": "Dread", "kq": "The line pulled so hard"}]})
    g = call("/api/gets", {"workbook": str(p["book"])})
    cards = {c["key"]: {"x": c["x"], "y": c["y"], "text": c.get("text", "")} for c in g["cards"]}
    k1 = gets_mod.card_of(p["case"], "es", themes.card_key(p["sheet"], p["o"][0], 1))
    cards[k1] = {"x": 1200, "y": 0, "text": "Dread"}
    call("/api/gets-save", {"workbook": str(p["book"]), "version": dict(
        g["version"], cards=cards, groups=[dict(x, members=[m for m in x["members"] if m != k1]) for x in g["groups"]]
        + [{"id": "G9", "label": "Theme of dread", "members": [k1], "x": 1180, "y": -60}],
        discarded=[], picks={}, notes=[])})
    turned = call("/api/commit", {"path": str(p["book"]), "sheet": p["sheet"], "row": p["o"][0], "en": "",
                                  "pairs": [{"es": "Dread", "kq": "thought it would lift me"},
                                            {"es": "Awe", "kq": "The line pulled so hard"}]})
    held = support.board_file(p["gfile"])
    named = str(((held["boards"][0].get("history") or [{}])[-1]).get("name") or "")
    check("430: a turn typing [Fear, Dread] over as [Dread, Awe] keeps Dread in its theme, and its History line names "
          "only Fear taken off, never Awe, which took no place",
          "error" not in turned and places(held, p["case"]).get("dread") == {("Theme of dread", False)}
          and "awe" not in places(held, p["case"]) and "Fear" in named and "taken off" in named and "Awe" not in named,
          str([places(held, p["case"]), named]))

    # [Dread] typed over as [Awe, Dread], Awe a code new to the study that takes no place on the board: the History
    # line names Awe added, as a one-code add does, never Dread changed (smallfix19)
    p = made("Kites TA new code first")
    call("/api/commit", {"path": str(p["book"]), "sheet": p["sheet"], "row": p["o"][0], "en": "",
                         "pairs": [{"es": "Dread", "kq": "thought it would lift me"}]})
    turned = call("/api/commit", {"path": str(p["book"]), "sheet": p["sheet"], "row": p["o"][0], "en": "",
                                  "pairs": [{"es": "Awe", "kq": "thought it would lift me"},
                                            {"es": "Dread", "kq": "The line pulled so hard"}]})
    held = support.board_file(p["gfile"])
    named = str(((held["boards"][0].get("history") or [{}])[-1]).get("name") or "")
    check("430: a turn typing [Dread] over as [Awe, Dread], Awe new to the study, has a History line naming Awe as "
          "added, never Dread as changed",
          "error" not in turned and "Awe" in named and "added" in named and "Dread" not in named
          and "changed" not in named, named)

    # a turn in one passage, [Fear, Ease] typed over as [Ease, Hold], Hold a code of the study waiting in the
    # Unplaced panel: the extract that leaves the board joins Hold there, and the History line still names Hold
    # (cardsync7, recheck5 B8)
    p = made("Kites TA turn panel", ease=1)
    call("/api/commit", {"path": str(p["book"]), "sheet": p["sheet"], "row": p["o"][0], "en": "",
                         "pairs": [{"es": "Fear", "kq": "thought it would lift me"},
                                   {"es": "Ease", "kq": "The line pulled so hard"}]})
    turned = call("/api/commit", {"path": str(p["book"]), "sheet": p["sheet"], "row": p["o"][0], "en": "",
                                  "pairs": [{"es": "Ease", "kq": "thought it would lift me"},
                                            {"es": "Hold", "kq": "The line pulled so hard"}]})
    held = support.board_file(p["gfile"])
    named = str(((held["boards"][0].get("history") or [{}])[-1]).get("name") or "")
    check("430: a turn whose extract leaves the board to join a code waiting in the Unplaced panel names that code in "
          "its History line",
          "error" not in turned and "hold" not in places(held, p["case"]) and "Hold" in named and "Fear" in named,
          str([places(held, p["case"]), named]))

    # two one-extract codes swapped by two recodes, then an Overwrite from a page open since before both: each code
    # stands where that page drew it (cardsync5)
    p = made("Kites TA swap", ease=1)
    old = p["page"]
    p["commit"](p["o"][0], "Ease", "thought it would lift me")
    p["commit"](p["o"][1], "Fear", "let the kite have the wind")
    ver = {a: v for a, v in old["version"].items() if a != "v"}
    over = call("/api/gets-save", {"workbook": str(p["book"]), "version": dict(
        ver, cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c.get("text", "")} for c in old["cards"]},
        groups=old["groups"], discarded=[], picks={}, notes=[])})
    held = support.board_file(p["gfile"])
    check("430: an Overwrite from a page open since before two recodes swapped two codes keeps each code where that "
          "page drew it",
          over.get("saved") is True and places(held, p["case"]) == {"fear": {("Theme of fear", False)},
                                                                     "ease": {("Theme of ease", False)}},
          str([over.get("error"), places(held, p["case"])]))

    # a recode to a code in the Unplaced panel, with no card on the board, joins it there (cardsync5)
    p = made("Kites TA panel", ease=1)
    p["commit"](p["o"][2], "Fear", "hold on too hard")
    g = call("/api/gets", {"workbook": str(p["book"])})
    cards = {c["key"]: {"x": c["x"], "y": c["y"], "text": c.get("text", "")} for c in g["cards"]
             if str(c.get("text") or "").casefold() != "ease"}
    call("/api/gets-save", {"workbook": str(p["book"]), "version": dict(
        g["version"], cards=cards, groups=[dict(x, members=[m for m in x["members"] if m in cards]) for x in g["groups"]],
        discarded=[], picks={}, notes=[])})
    p["commit"](p["o"][0], "Ease", "thought it would lift me")
    held = support.board_file(p["gfile"])
    check("430: a recode to a code in the Unplaced panel takes the extract off the board to join it there",
          "ease" not in places(held, p["case"]) and places(held, p["case"]).get("fear") == {("Theme of fear", False)}
          and status_of(call, p) == "in", str([status_of(call, p), places(held, p["case"])]))

    # a recode into a code the study already holds joins that code where it stands and never leads it, loose on the
    # canvas or in the Unplaced panel, whatever theme or Set aside the extract left (cardsync6, recheck5 Q1, Q2, Q5,
    # P2, Q6)
    def arrange(p: dict, fear: str, ease: str) -> None:
        """Fear's extract and Ease's cards put in a theme, set aside, loose on the canvas or in the Unplaced panel."""
        g = call("/api/gets", {"workbook": str(p["book"])})
        cards = {c["key"]: {"x": c["x"], "y": c["y"], "text": c.get("text", "")} for c in g["cards"]}
        ease_keys = [k for k, c in cards.items() if str(c.get("text") or "").casefold() == "ease"]
        if ease == "panel":
            for k in ease_keys:
                cards.pop(k)
        elif ease == "loose":
            for k in ease_keys:
                cards[k].update(x=1400, y=600)
        if fear == "aside":
            cards[p["k"][0]] = {"x": 0, "y": 900, "text": "Fear"}
        put = {p["k"][0]} if fear != "theme" else set()
        put |= set(ease_keys) if ease != "theme" else set()
        call("/api/gets-save", {"workbook": str(p["book"]), "version": dict(
            g["version"], cards=cards, groups=[dict(x, members=[m for m in x["members"] if m in cards and m not in put])
                                               for x in g["groups"]],
            discarded=[p["k"][0]] if fear == "aside" else [], picks={}, notes=[])})

    for tag, fear, ease, want in (
            ("Q1", "aside", "loose", {"ease": {(None, False)}}),
            ("Q2", "theme", "loose", {"ease": {(None, False)}}),
            ("Q5", "aside", "panel", {}),
            ("P2", "theme", "panel", {})):
        p = made(f"Kites TA {tag}")
        arrange(p, fear, ease)
        before = places(support.board_file(p["gfile"]), p["case"])
        p["commit"](p["o"][0], "Ease", "thought it would lift me")
        held = support.board_file(p["gfile"])
        check(f"430 ({tag}): Fear's one extract, {'set aside' if fear == 'aside' else 'in Theme of fear'}, recoded to "
              f"Ease {'loose on the canvas' if ease == 'loose' else 'in the Unplaced panel'} joins Ease there and never "
              "moves Ease",
              places(held, p["case"]) == want and not members(held["boards"][0], "Theme of fear")
              and not (held["boards"][0].get("discarded") or []) and status_of(call, p) == "in",
              str([before, places(held, p["case"]), status_of(call, p)]))
    p = made("Kites TA Q6", ease=1)
    p["commit"](p["o"][2], "Fear", "hold on too hard")
    arrange(p, "theme", "panel")
    p["commit"](p["o"][0], "Ease", "thought it would lift me")
    first = places(support.board_file(p["gfile"]), p["case"])
    p["commit"](p["o"][2], "Ease", "hold on too hard")
    held = support.board_file(p["gfile"])
    check("430 (Q6): a code of two extracts recoded one by one to a code in the Unplaced panel sends each to the panel, "
          "never bringing that code into its theme",
          first == {"fear": {("Theme of fear", False)}} and places(held, p["case"]) == {}
          and status_of(call, p) == "in", str([first, places(held, p["case"])]))

    # two extracts of one code in one passage, both typed over as two new codes in one save: the first keeps the
    # spot, the second takes a free spot in the same theme (cardsync6, recheck5 P3)
    p = made("Kites TA P3")
    call("/api/commit", {"path": str(p["book"]), "sheet": p["sheet"], "row": p["o"][0], "en": "",
                         "pairs": [{"es": "Fear", "kq": "thought it would lift me"},
                                   {"es": "Fear", "kq": "The line pulled so hard"}]})
    both = call("/api/commit", {"path": str(p["book"]), "sheet": p["sheet"], "row": p["o"][0], "en": "",
                                "pairs": [{"es": "Dread", "kq": "thought it would lift me"},
                                          {"es": "Awe", "kq": "The line pulled so hard"}]})
    held = support.board_file(p["gfile"])
    b = held["boards"][0]
    # a code's rows share its spot, so each spot is counted once a code
    lines = held["cases"][p["case"]]["lines"]
    spots = list({str(lines[k.partition("/es/")[2]]["text"]).casefold(): (round(c.get("x", 0)), round(c.get("y", 0)))
                  for k, c in b["cards"].items()}.values())
    named = str(((b.get("history") or [{}])[-1]).get("name") or "")
    check("430 (P3): two extracts of one code typed over as two new codes in one save both stay in its theme, never "
          "on one spot, and the History line names them",
          "error" not in both and places(held, p["case"]).get("dread") == {("Theme of fear", False)}
          and places(held, p["case"]).get("awe") == {("Theme of fear", False)} and len(set(spots)) == len(spots)
          and "Dread" in named and "Awe" in named, str([places(held, p["case"]), spots, named]))

    # every other change to an extract's codes lands at the save too (cardsync4)
    p = made("Kites TA chips")
    off = call("/api/commit", {"path": str(p["book"]), "sheet": p["sheet"], "row": p["o"][0], "en": "", "pairs": []})
    held = support.board_file(p["gfile"])
    named = str(((held["boards"][0].get("history") or [{}])[-1]).get("name") or "")
    check("430: the History line of a code taken off on the Coding screen names the code",
          "Fear" in named and "taken off" in named, named)
    check("430: a code taken off an extract leaves the board at the save, its card gone, Fear's theme empty",
          "error" not in off and p["k"][0] not in held["boards"][0]["cards"]
          and status_of(call, p) == "in" and not members(held["boards"][0], "Theme of fear"),
          str([status_of(call, p), [(x["label"], x["members"]) for x in held["boards"][0]["groups"]]]))
    p["commit"](p["o"][0], "Ease", "thought it would lift me")
    held = support.board_file(p["gfile"])
    check("430: a code put on that extract in a second save joins Ease in Theme of ease at the save",
          places(held, p["case"]) == {"ease": {("Theme of ease", False)}} and status_of(call, p) == "in",
          str([status_of(call, p), places(held, p["case"])]))

    p = made("Kites TA second")
    two = call("/api/commit", {"path": str(p["book"]), "sheet": p["sheet"], "row": p["o"][0], "en": "",
                               "pairs": [{"es": "Fear", "kq": "thought it would lift me"},
                                         {"es": "Ease", "kq": "thought it would lift me"}]})
    held = support.board_file(p["gfile"])
    check("430: a second code put on an extract lands under its code in Theme of ease, the first staying in Theme of "
          "fear, at the save",
          "error" not in two and places(held, p["case"]) == {"fear": {("Theme of fear", False)},
                                                             "ease": {("Theme of ease", False)}}
          and status_of(call, p) == "in", str([status_of(call, p), places(held, p["case"])]))
    one = call("/api/commit", {"path": str(p["book"]), "sheet": p["sheet"], "row": p["o"][0], "en": "",
                               "pairs": [{"es": "Ease", "kq": "thought it would lift me"}]})
    held = support.board_file(p["gfile"])
    check("430: one of two codes taken off an extract leaves the other in its theme and the board at the save",
          "error" not in one and places(held, p["case"]) == {"ease": {("Theme of ease", False)}}
          and not members(held["boards"][0], "Theme of fear") and status_of(call, p) == "in",
          str([status_of(call, p), places(held, p["case"])]))

    # the command line's codes remove and codes add, an agent's recode in two steps, each landing at its write, its
    # dry run saying which board would take it and writing nothing
    p = made("Kites TA codes")
    was_files = files_of(p["hill"])
    code, dry, err = run_cli(cfg_file, p, "codes", "remove", "Corin", p["sheet"], str(p["o"][0]), "Fear", "--extract",
                             "thought it would lift me", "--tool", "Claude Code", "--note", "Take Fear off", "--dry-run")
    check("430: an agent's dry run of codes remove says the Themes board would take it, and writes nothing",
          code == 0 and files_of(p["hill"]) == was_files
          and ((dry.get("themes") or {}).get("gets") or {}).get("boards") == ["b1"], err or str(dry.get("themes"))[:300])
    code, out, err = run_cli(cfg_file, p, "codes", "remove", "Corin", p["sheet"], str(p["o"][0]), "Fear", "--extract",
                             "thought it would lift me", "--tool", "Claude Code", "--note", "Take Fear off")
    code2, out2, err2 = run_cli(cfg_file, p, "codes", "add", "Corin", p["sheet"], str(p["o"][0]), "Ease", "--extract",
                                "thought it would lift me", "--tool", "Claude Code", "--note", "Put Ease on")
    held = support.board_file(p["gfile"])
    b = held["boards"][0]
    check("430: the command line's codes remove then codes add land on the Themes board at each write, Ease in one "
          "theme, the board marked changed and its History naming an agent's change",
          code == 0 and code2 == 0 and places(held, p["case"]) == {"ease": {("Theme of ease", False)}}
          and status_of(call, p) == "in" and (b.get("changed") or {}).get("tool") == "Claude Code"
          and (b.get("history") or [{}])[-1].get("name") == "Before an agent's change",
          (err or "") + (err2 or "") + str([places(held, p["case"]), (b.get("history") or [{}])[-1].get("name")]))

    # an agent's turn write adding a code to an extract
    p = made("Kites TA turn add")
    key = themes.card_key(p["sheet"], p["o"][0], 0)
    code, shown, err = run_cli(cfg_file, p, "turn", "show", "Corin", p["sheet"], str(p["o"][0]))
    spec = base / "a430-ta-add.json"
    spec.write_text(json.dumps({"pairs": [{"statement": "Fear", "quote": "thought it would lift me", "key": key},
                                          {"statement": "Ease", "quote": "thought it would lift me"}],
                                "version": shown["turns"][0]["version"] if code == 0 and shown.get("turns") else None,
                                "request": "Code the first extract Ease too"}), encoding="utf-8")
    was_files = files_of(p["hill"])
    code, dry, err = run_cli(cfg_file, p, "turn", "write", "Corin", p["sheet"], str(p["o"][0]), "--from", str(spec),
                             "--tool", "Claude Code", "--dry-run")
    check("430: an agent's dry run of a turn write adding a code says the Themes board would take it, and writes "
          "nothing", code == 0 and files_of(p["hill"]) == was_files
          and (dry.get("recoded") or {}).get("boards") == ["b1"], err or str(dry.get("recoded"))[:300])
    code, wrote, err = run_cli(cfg_file, p, "turn", "write", "Corin", p["sheet"], str(p["o"][0]), "--from", str(spec),
                               "--tool", "Claude Code")
    held = support.board_file(p["gfile"])
    check("430: an agent's turn write adding a code lands it under Ease in Theme of ease at the write",
          code == 0 and places(held, p["case"]) == {"fear": {("Theme of fear", False)}, "ease": {("Theme of ease", False)}}
          and status_of(call, p) == "in", err or str(places(held, p["case"])))

    # a code new to the study, while the code its extract left keeps a card, stays in its theme clear of every card,
    # never on the card it left, and a second board with no card of either code keeps no History line
    p = made("Kites TA new code")
    other = call("/api/gets-ops", {"workbook": str(p["book"]), "op": "new"})
    held = support.board_file(p["gfile"])
    lines_before = {str(x["id"]): len(x.get("history") or []) for x in held["boards"]}
    p["commit"](p["o"][1], "Joy", "let the kite have the wind")
    held = support.board_file(p["gfile"])
    b = held["boards"][0]
    joy = b["cards"].get(p["k"][1]) or {}
    clear = all((abs(joy.get("x", 0) - c.get("x", 0)) > 1 or abs(joy.get("y", 0) - c.get("y", 0)) > 1)
                for key, c in b["cards"].items() if key != p["k"][1])
    check("430: a recode to a code new to the study, while the old code keeps a card, stays in its theme clear of "
          "every card",
          bool(joy) and clear and k_in(b, p["k"][1], "Theme of ease") and k_in(b, p["k"][2], "Theme of ease"),
          str([joy, [(x["label"], x["members"]) for x in b["groups"]]]))
    check("430: a board with no card of the old or the new code keeps no History line for the recode",
          "error" not in other and len(held["boards"]) == 2
          and {str(x["id"]): len(x.get("history") or []) for x in held["boards"]}
          == {str(held["boards"][0]["id"]): lines_before[str(held["boards"][0]["id"])] + 1,
              str(held["boards"][1]["id"]): lines_before[str(held["boards"][1]["id"])]},
          str([lines_before, {str(x["id"]): len(x.get("history") or []) for x in held["boards"]}, other.get("error")]))

    # an agent's turn write: its dry run writes nothing, then the write lands as the app's do
    p = made("Kites TA agent")

    def run(*args):
        return run_cli(cfg_file, p, *args)

    key = themes.card_key(p["sheet"], p["o"][0], 0)
    code, shown, err = run("turn", "show", "Corin", p["sheet"], str(p["o"][0]))
    version = shown["turns"][0]["version"] if code == 0 and shown.get("turns") else None
    spec = base / "a430-ta-turn.json"
    spec.write_text(json.dumps({"pairs": [{"statement": "Ease", "quote": "thought it would lift me", "key": key}],
                                "version": version, "request": "Code the first extract Ease"}), encoding="utf-8")
    files = lambda: {str(f.relative_to(p["hill"])): f.read_bytes() for f in sorted(p["hill"].rglob("*"))  # noqa: E731
                     if f.is_file()}
    was_files = files()
    code, dry, err = run("turn", "write", "Corin", p["sheet"], str(p["o"][0]), "--from", str(spec), "--tool",
                         "Claude Code", "--dry-run")
    check("430: an agent's dry run of the recode writes nothing", code == 0 and files() == was_files,
          err or str(sorted(set(files()) ^ set(was_files))))
    code, wrote, err = run("turn", "write", "Corin", p["sheet"], str(p["o"][0]), "--from", str(spec), "--tool",
                           "Claude Code")
    check("430: the agent's turn write of the recode goes through and says the change was brought in",
          code == 0 and (wrote.get("recoded") or {}).get("case") == p["case"], err or str(sorted(wrote)))
    marked = support.board_file(p["gfile"])["boards"][0].get("changed") or {}
    check("430: the agent's recode marks the Themes board changed in a conversation", marked.get("tool") == "Claude Code",
          str(marked)[:200])
    landed("by an agent's turn write", p)

    # and the agent's run undone puts the Themes file back byte for byte, the code back in Theme of fear
    import agent_changes
    p = made("Kites TA undo")
    code, shown, err = run("turn", "show", "Corin", p["sheet"], str(p["o"][0]))
    spec.write_text(json.dumps({"pairs": [{"statement": "Ease", "quote": "thought it would lift me", "key": key}],
                                "version": shown["turns"][0]["version"] if code == 0 and shown.get("turns") else None,
                                "request": "Code the first extract Ease"}), encoding="utf-8")
    themes_was = p["gfile"].read_bytes()
    code, wrote, err = run("turn", "write", "Corin", p["sheet"], str(p["o"][0]), "--from", str(spec), "--tool",
                           "Claude Code")
    took = support.board_file(p["gfile"])["boards"][0]
    runs = agent_changes.read(p["hill"])
    code2, _, err2 = (run("agents", "undo-run", runs[-1]["run"], "--note", "Put it back") if runs
                      else (1, {}, "no run recorded"))
    check("430: undoing the agent's recode run puts the Themes file back byte for byte",
          code == 0 and k_in(took, p["k"][0], "Theme of ease") and code2 == 0
          and p["gfile"].read_bytes() == themes_was, (err or "") + (err2 or ""))

    # a Code list rename made before the project had a Themes file, the board made after it, then codes undo and
    # codes redo: the workbook put back is taken at once, so nothing waits for Take (cardsync5)
    hill = base / "Kites TA born"
    hill.mkdir()
    project = idiograph_routes.api_new_project({
        "op": "make", "folder": str(hill), "name": "Kites TA born", "method": "ta",
        "research_question": "How do new kite fliers learn the wind?",
        "files": [{"name": "corin.txt", "data": b64(TA_CORIN), "pseudonym": "Corin", "interview": "Spring",
                   "speakers": {"Brann": "interviewer", "Corin": "participant"}}]})
    idiograph_routes.api_project({"root": project["project"]["id"], "agents": True})
    book = next(hill.glob("P1*/*.xlsx"))
    sheet = idiograph_routes.read_sheets(book)[1][0]
    o = said_rows(book, sheet, "Corin")
    for r, es, kq in ((o[0], "Fear", "thought it would lift me"), (o[1], "Ease", "let the kite have the wind")):
        call("/api/commit", {"path": str(book), "sheet": sheet, "row": r, "en": "", "pairs": [{"es": es, "kq": kq}]})
    gfile = hill / gets_mod.FILE
    born = {"hill": hill, "book": book}
    code, _, err = run_cli(cfg_file, born, "codes", "rename", "Fear", "Dread", "--note", "Rename it")
    no_file = not gfile.exists()
    g = call("/api/gets", {"workbook": str(book)})
    case = g["cases"][0]["case"]
    k0 = gets_mod.card_of(case, "es", themes.card_key(sheet, o[0], 0))
    call("/api/gets-save", {"workbook": str(book), "version": dict(
        g["version"], cards={k0: {"x": 0, "y": 0, "text": "Dread"}},
        groups=[{"id": "G1", "label": "Theme of dread", "members": [k0], "x": -20, "y": -60}],
        discarded=[], picks={}, notes=[])})
    code2, _, err2 = run_cli(cfg_file, born, "codes", "undo", "--note", "Undo it")
    held = support.board_file(gfile)
    born.update(case=case)
    check("430: codes undo of a step made before the Themes file existed takes the workbook it put back at once, the "
          "code in its theme under its old name",
          code == 0 and no_file and code2 == 0 and status_of(call, born) == "in"
          and places(held, case).get("fear") == {("Theme of dread", False)} and "dread" not in places(held, case),
          (err or "") + (err2 or "") + str([no_file, status_of(call, born), places(held, case)]))
    code3, _, err3 = run_cli(cfg_file, born, "codes", "redo", "--note", "Redo it")
    held = support.board_file(gfile)
    check("430: codes redo of that step takes the workbook at once too",
          code3 == 0 and status_of(call, born) == "in"
          and places(held, case).get("dread") == {("Theme of dread", False)} and "fear" not in places(held, case),
          (err3 or "") + str([status_of(call, born), places(held, case)]))


def run_cli(cfg_file: Path, p: dict, *args):
    import cli
    code, text, err = cli.run(["--root", str(p["hill"]), "--config", str(cfg_file), *args, "--json"])
    return code, (support.plain(json.loads(text)) if text.strip() else {}), err


def files_of(hill: Path) -> dict:
    return {str(f.relative_to(hill)): f.read_bytes() for f in sorted(hill.rglob("*")) if f.is_file()}


def status_of(call, p: dict) -> str:
    return {c["case"]: c["status"] for c in call("/api/gets", {"workbook": str(p["book"])})["cases"]}.get(p["case"])


def members(board: dict, label: str) -> list:
    return next((x["members"] for x in board.get("groups") or [] if x.get("label") == label), [])


def places(held: dict, case: str) -> dict:
    """Where each code of the participant stands on the first board, by its code: the themes holding a card of it and
    whether set aside, a code on no card left out."""
    b = held["boards"][0]
    lines = held["cases"][case]["lines"]
    aside = set(b.get("discarded") or [])
    out: dict = {}
    for key in b.get("cards") or {}:
        ident = key.split("/es/", 1)[1] if "/es/" in key else None
        line = lines.get(ident) if ident else None
        if not isinstance(line, dict) or not str(line.get("text") or "").strip():
            continue
        where = next((x["label"] for x in b.get("groups") or [] if key in x.get("members") or []), None)
        out.setdefault(" ".join(str(line["text"]).split()).casefold(), set()).add((where, key in aside))
    return out


def k_in(board: dict, key: str, label: str) -> bool:
    """Whether a board's label `label` holds the card `key`."""
    return any(key in g.get("members") or [] for g in board.get("groups") or [] if g.get("label") == label)
