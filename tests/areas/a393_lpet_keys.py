"""Area 393: the LPETs' copy of a participant follows every row op and every removed or merged statement, and the
two repair ops put back copies left behind (lpetkeys and lpetdrop, 13 November 2026).

Found by the GRAVITY session on a longitudinal project: a passage split with `turn assign` moved the PETs boards'
keys with the rows and left a participant's LPETs on the old row numbers, one row off from the split down, and a
statement removed stayed on the LPETs. What is checked, on an invented project of two timepoints. A split before an
LPET's statements leaves every LPET card and the copy's every line on its own statement, and so does its undo. A
removed statement goes from the copy and the LPET, its sibling's card moving to its new key. Two statements merged on
the same LPET become one card there, never two. With a split left behind by hand, as before this build, `copies
rekey` lists each move by keys, by the words or by an offset, its dry runs writing nothing, and puts every key back.
With a removal left behind, `copies prune`'s dry run names the copy and the LPET it would leave with no statement at
T1, writes nothing, and the prune takes the copy and the card off.

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
           "Tove: [00:02:30] I took the tiller and the boat turned when I asked it to.\n"
           "Ines: [00:03:00] And when the wind went?\n"
           "Tove: [00:03:30] The wind dropped and we drifted for an hour, and I laughed about it.\n")
TOVE_T2 = ("Ines: [00:00:02] How is it now?\n"
           "Tove: [00:00:06] I read the wind on the water before I leave the jetty.\n")
TWO = [{"label": "T1", "description": "First lessons"}, {"label": "T2", "description": "After the season"}]


def test_lpet_keys(scratch):
    print("\n393. The LPETs' copy follows a split, its undo, a removed statement and a merge, and copies rekey and "
          "copies prune put back copies a row op left behind, their dry runs naming keys and writing nothing "
          "(lpetkeys, 13 November)")
    import cli
    import gets as gets_mod
    import server as server_mod
    import themes
    import workbook as wb_mod

    b64 = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")
    base = scratch / "a393"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    cfg_file = scratch / "a393-config.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "Ines", "corpus": "", "gravity_reference": "",
                                    "corpus_exclude": []}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)

    def tree(at: Path) -> dict:
        return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*"))
                if p.is_file() and p.suffix != ".lock" and ".idiograph-restore" not in p.parts
                and p.name != "idiograph-agent-changes.jsonl"}

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

    def read(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "a393-state.json", {"recent": []}
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
        r1 = said_rows(book, s1, "Tove")
        wb_mod.save_turn(book, s1, r1[0], None, "", None, pairs=[
            {"es": "Clinging on at first", "kq": "I clung to the rail"},
            {"es": "Watching the water", "kq": "watched the water rush past the hull"}])
        wb_mod.save_turn(book, s1, r1[1], None, "", None, pairs=[
            {"es": "Steering for the first time", "kq": "I took the tiller"}])
        wb_mod.save_turn(book, s1, r1[2], None, "", None, pairs=[
            {"es": "Drifting without wind", "kq": "we drifted for an hour"},
            {"es": "Laughing at the stillness", "kq": "I laughed about it"}])
        key = lambda r, n: themes.card_key(s1, r, n)
        card = lambda k: gets_mod.card_of("T1", "es", k)
        st = call("/api/themes", {"workbook": str(book), "timepoint": 1})
        keys = [c["key"] for c in st["cards"]]
        words = {c["key"]: c["text"] for c in st["cards"]}
        call("/api/themes-save", {"workbook": str(book), "timepoint": 1, "version": dict(
            st["version"], cards={k: {"x": 0, "y": 40 * i, "text": words[k]} for i, k in enumerate(keys)},
            groups=[{"id": "g1", "label": "Holding on", "members": keys, "x": 0, "y": -40}], discarded=[], picks={})})
        lp = call("/api/gets", {"workbook": str(book), "lpets": True})
        # two LPETs of T1 statements: one over four of them, one over the last statement alone
        main = [key(r1[0], 0), key(r1[0], 1), key(r1[1], 0), key(r1[2], 0)]
        lonely = [key(r1[2], 1)]
        cards = {c["key"]: {"x": c["x"], "y": c["y"]} for c in lp["cards"]}
        cards.update({card(k): {"x": 700, "y": 60 * i, "text": words[k]} for i, k in enumerate(main + lonely)})
        call("/api/gets-save", {"workbook": str(book), "lpets": True, "version": dict(
            lp["version"], cards=cards, groups=[
                {"id": "G1", "label": "From the rail to the helm", "members": [card(k) for k in main], "x": -20, "y": -60},
                {"id": "G2", "label": "Laughing it off", "members": [card(k) for k in lonely], "x": 900, "y": -60}],
            discarded=[], picks={}, notes=[])})
        lpfile = gets_mod.lpets_path(book)

        def aligned() -> list[str]:
            """Every line of the LPETs' T1 copy and every T1 statement card on its boards that does not stand on its
            own statement in the workbook: the copy's words at its key, the card's key a line of the copy."""
            truth = gets_mod.workbook_lines(book)
            d = read(lpfile)
            lines = d["cases"]["T1"]["lines"]
            off = [k for k, v in lines.items() if themes.words((truth.get(k) or {}).get("text")) != themes.words(v["text"])]
            for b in d["boards"]:
                for ck, c in b["cards"].items():
                    s = gets_mod.split_key(ck)
                    if s["case"] == "T1" and s["kind"] == "es" and (s["ident"] not in lines or themes.words(
                            (truth.get(s["ident"]) or {}).get("text")) != themes.words(c.get("text"))):
                        off.append(ck)
            return off

        def members(gid: str) -> list[str]:
            return next(g["members"] for g in read(lpfile)["boards"][0]["groups"] if g["id"] == gid)

        check("393: the project holds Tove's LPETs, two LPETs over five T1 statements, each on its statement",
              lpfile.is_file() and len(members("G1")) == 4 and aligned() == [], str(aligned()))

        def run(*args, as_json=True):
            code, text, err = cli.run(["--root", str(sail), "--config", str(cfg_file), *args]
                                      + (["--json"] if as_json else []))
            if not as_json:
                return code, text, err
            return code, (support.plain(json.loads(text)) if text.strip() else {}), err

        # ── A. a split before the LPETs' statements, and its undo
        code, done, err = run("turn", "assign", "Tove", s1, str(r1[0]), "--to", "Ines", "--words", "and watched",
                              "--note", "Split Tove's first answer", "--tool", "Claude Code")
        r_now = said_rows(book, s1, "Tove")
        check("393: a split of Tove's first answer moves the rows below it, and every LPET card and line of the copy "
              "stays on its own statement",
              code == 0 and r_now[-1] > r1[-1] and aligned() == [] and len(members("G1")) == 4, err or str(aligned()))
        code, undone, err = run("turn", "assign-undo", "Tove", done.get("id", ""), "--note", "Put it back",
                                "--tool", "Claude Code")
        check("393: its undo puts the rows back, and the LPETs with them",
              code == 0 and said_rows(book, s1, "Tove") == r1 and aligned() == []
              and members("G1") == [card(k) for k in main], err or str(aligned()))

        # ── B. a removed statement leaves the copy and its LPET, its sibling moving to its new key
        code, shown, err = run("turn", "show", "Tove", s1, str(r1[2]))
        spec = scratch / "a393-remove.json"
        spec.write_text(json.dumps({"remove": [key(r1[2], 0)], "version": shown["turns"][0]["version"],
                                    "request": "Take off the drifting statement"}), encoding="utf-8")
        whole = tree(sail)
        code, dry, err = run("turn", "write", "Tove", s1, str(r1[2]), "--from", str(spec), "--dry-run")
        check("393: the write's dry run says the LPETs' copy would take the statement off and move its sibling, and "
              "writes nothing",
              code == 0 and (dry.get("copies_followed") or {}).get("lpets", {}).get("removed") == [key(r1[2], 0)]
              and (dry.get("copies_followed") or {}).get("lpets", {}).get("moved") == [key(r1[2], 1)]
              and tree(sail) == whole, err or str(dry.get("copies_followed"))[:500])
        before_drop = lpfile.read_bytes()
        code, text, err = run("turn", "write", "Tove", s1, str(r1[2]), "--from", str(spec), "--tool", "Claude Code",
                              as_json=False)
        d = read(lpfile)
        check("393: the removed statement is gone from the copy and the LPET, the sibling's card on its new key under "
              "its LPET, and the write says so by keys",
              code == 0 and aligned() == [] and card(key(r1[2], 0)) not in members("G1")
              and members("G2") == [card(key(r1[2], 0))] and d["cases"]["T1"]["lines"][key(r1[2], 0)]["text"]
              == "Laughing at the stillness" and key(r1[2], 1) not in d["cases"]["T1"]["lines"]
              and "took off 1 removed" in text, err or text[-500:])

        # ── C. two statements on one LPET merged into one: one card there, never two
        code, shown, err = run("turn", "show", "Tove", s1, str(r1[0]))
        spec = scratch / "a393-merge.json"
        spec.write_text(json.dumps({"pairs": [{"statement": "Clinging on and watching the water", "key": key(r1[0], 0),
                                               "quote": "I clung to the rail"}],
                                    "version": shown["turns"][0]["version"], "request": "Merge Tove's two"}),
                        encoding="utf-8")
        code, text, err = run("turn", "write", "Tove", s1, str(r1[0]), "--from", str(spec), "--tool", "Claude Code",
                              as_json=False)
        g1 = members("G1")
        check("393: the merged statement's card follows the one it joined, once on the LPET, its own line gone",
              code == 0 and g1.count(card(key(r1[0], 0))) == 1 and card(key(r1[0], 1)) not in g1 and len(g1) == 2
              and key(r1[0], 1) not in read(lpfile)["cases"]["T1"]["lines"] and "merged" in text, err or str(g1))

        # ── D. a split left behind, as before this build: copies rekey puts the keys back
        held = lpfile.read_bytes()
        code, done, err = run("turn", "assign", "Tove", s1, str(r1[1]), "--to", "Ines", "--words", "and the boat",
                              "--note", "Split Tove's second answer", "--tool", "Claude Code")
        lpfile.write_bytes(held)
        r_now = said_rows(book, s1, "Tove")
        shift = r_now[-1] - r1[2]
        off = aligned()
        check("393: with the LPETs left on the old rows, the last answer's card and line are off their statement",
              code == 0 and shift > 0 and card(key(r1[2], 0)) in off, str(off))
        whole = tree(sail)
        code, by_words, err = run("copies", "rekey", "--case", "Tove", "--dry-run")
        code2, by_offset, err2 = run("copies", "rekey", "--case", "Tove", "--timepoint", "T1", "--from-row",
                                     str(r1[1] + 1), "--shift", str(shift), "--dry-run")
        code3, text, _ = run("copies", "rekey", "--case", "Tove", "--dry-run", as_json=False)
        moves = lambda a: [(m["timepoint"], m["from"], m["to"]) for x in a.get("participants") or [] for f in x["files"]
                           if f["file"] == "lpets" for m in f.get("moves") or []]
        lpets_named = [m["lpets"] for x in by_words.get("participants") or [] for f in x["files"]
                       for m in f.get("moves") or [] if f["file"] == "lpets"]
        check("393: rekey's dry runs, by the words and by an offset, list the same move, from and to by key, with the "
              "LPET holding it, and write nothing, never the words",
              code == 0 and code2 == 0 and moves(by_words) == [("T1", key(r1[2], 0), key(r_now[-1], 0))]
              and moves(by_offset) == moves(by_words) and lpets_named == [[{"id": "G2", "title": "Laughing it off"}]]
              and key(r1[2], 0) in text and "stillness" not in text and tree(sail) == whole,
              (err or err2) + str(by_words)[:500])
        code, refused, err = run("copies", "rekey", "--case", "Tove", "--from-row", "5", "--note", "x")
        check("393: an offset without its shift is refused, nothing written", code != 0 and tree(sail) == whole, err)
        code, done, err = run("copies", "rekey", "--case", "Tove", "--note", "Put Tove's LPETs back on their rows",
                              "--tool", "Claude Code")
        lp_board = read(lpfile)["boards"][0]
        check("393: the rekey puts every key back on its statement, one History step on the LPETs board",
              code == 0 and aligned() == [] and members("G2") == [card(key(r_now[-1], 0))]
              and lp_board["history"][-1]["name"] == "Before: Put Tove's LPETs back on their rows", err or str(aligned()))

        # ── E. a removal left behind: copies prune names the LPET it would empty, then takes the copy off
        code, shown, err = run("turn", "show", "Tove", s1, str(r_now[-1]))
        spec = scratch / "a393-remove2.json"
        spec.write_text(json.dumps({"remove": [key(r_now[-1], 0)], "version": shown["turns"][0]["version"],
                                    "request": "Take off the laughing statement"}), encoding="utf-8")
        held = lpfile.read_bytes()
        code, text, err = run("turn", "write", "Tove", s1, str(r_now[-1]), "--from", str(spec), "--tool", "Claude Code",
                              as_json=False)
        lpfile.write_bytes(held)
        whole = tree(sail)
        code, dry, err = run("copies", "prune", "--dry-run")
        code_t, dry_text, _ = run("copies", "prune", "--dry-run", as_json=False)
        pruned = [(m["timepoint"], m["key"]) for x in dry.get("participants") or [] for f in x["files"]
                  for m in f.get("pruned") or []]
        check("393: prune's dry run names the left-over copy by key and the LPET it would leave with no statement at "
              "T1, by title and timepoint, and writes nothing",
              code == 0 and pruned == [("T1", key(r_now[-1], 0))]
              and [(e["lpet"], e["title"], e["timepoint"]) for e in dry.get("emptied") or []]
              == [("G2", "Laughing it off", "T1")] and "Laughing it off" in dry_text and "stillness" not in dry_text
              and tree(sail) == whole, err or str(dry)[:600])
        code, done, err = run("copies", "prune", "--note", "Take off Tove's left-over copies", "--tool", "Claude Code")
        d = read(lpfile)
        check("393: the prune takes the copy off the copy and its card off the LPET",
              code == 0 and key(r_now[-1], 0) not in d["cases"]["T1"]["lines"] and members("G2") == []
              and card(key(r_now[-1], 0)) not in d["boards"][0]["cards"], err or str(members("G2")))
        code, again, err = run("copies", "prune", "--dry-run")
        check("393: a prune's dry run after it finds nothing", code == 0 and again.get("pruned") == 0, str(again)[:300])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept
