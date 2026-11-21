"""Area 419: one PET, sub-theme or statement drawn on by two LPETs, and the LPET table timepoints across (drawsbuild,
17 November 2026, Adam's requirements of that day, points 4, 7 and 9, his choices by dialog).

Point 4: rarely, one moment of an interview informs two LPETs. A card on a participant's LPETs board gains a second
card under another LPET, `<key>/2`, through its menu's "Also drawn on by…" or Option-drag in the app, which saves the
board through the page's own route, and through `gets apply`'s `also` for an agent, recorded and undone as every
`gets apply` is. Both cards then read "Also drawn on by <the other LPET>", and the forward trace lists both LPETs.
Points 7 and 9: the LPET table sets each LPET timepoints across, as Nizza's Table 8, and its Word and PDF are the
thesis appendix, with the PETs no LPET draws on and his reasons after the LPETs.

What is checked, on a scratch copy of the longitudinal demo's Arlo: a duplicate of a PET's card made by the app's
route (a save from the page) is kept and read back, the trace naming both LPETs, whole; an agent's `also` of a
statement brought in, its dry run writing nothing and naming the new card by key, the change one record line, both
LPETs drawing on the statement whole, and its undo putting every file back byte for byte; each refusal (a card not
there, one set aside, a sub-LPET, an LPET already drawing on it) one line with nothing written; a duplicate set aside
leaving the other card drawn on by its LPET alone, undone byte for byte; the statement's second card following its
first when the take of a reworded statement renames it; the table's data, LPET by LPET and timepoint by timepoint,
matching the board read independently (its state, key quote and what it draws on, by key); and the Word document
and the PDF holding every LPET's title, each timepoint's state and the PETs no LPET draws on with his reason; and a
second card under an LPET drawing on its PET, so his reason is hidden on every read (the trace, gets show, the
appendix's list) while the file keeps it, by an agent's also undone byte for byte and by the page's save, whose Undo
save shows the reason again (drawsbuild2, on drawswordfix2); and a State of 600 words and a key quote of a passage
of about 2800 words, each taller than a page, every word of each in the PDF, the print view and Word, nothing in the
PDF printed past a page's foot line, by the words' places, and Word's key quote in double marks (drawsbuild5)."""
from __future__ import annotations

import hashlib
import html as html_mod
import json
import re
import shutil
import zipfile
from pathlib import Path

from .support import check
from . import support

ASKED = "Draw on that moment in a second LPET"
WHY = "Folded into the prescribed-project thread at this timepoint."


def digest(root: Path) -> dict:
    """Every file of the project by its contents, the locks, the record of agents' changes and its restore points
    set aside."""
    import agent_changes
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if (not p.is_file() or p.name.endswith(".lock") or rel == agent_changes.FILE
                or rel.startswith(agent_changes.STORE) or "_Archive/" in rel or "/superseded/" in rel):
            continue
        out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def changed(a: dict, b: dict) -> list:
    return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))


def test_lpet_draws_across(scratch: Path):
    print("\n419. One card drawn on by two LPETs, and the LPET table timepoints across with its appendix (drawsbuild, "
          "17 November)")
    import agent_changes
    import agent_log
    import cli
    import gets as gets_mod
    import gets_print
    import gets_word
    import idiograph_routes as routes
    import os
    import pdftext
    import print_pdf
    import server as server_mod
    import themes
    import themes_word

    base = scratch / "draws-across-419"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Allotment"
    (root / "Arlo" / "Working").mkdir(parents=True)
    lipa = support.source("demo/lipa")
    held = json.loads((lipa / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
    held["agents"] = {"allowed": True, "at": "2026-11-17T09:00:00+00:00"}
    (root / server_mod.PROJECT_FILE).write_text(json.dumps(held), encoding="utf-8")
    arlo = root / "Arlo" / "Arlo - EN & ES.xlsx"
    shutil.copy2(lipa / "pristine" / "Arlo - EN & ES.xlsx", arlo)
    for one in sorted((lipa / "pristine" / "Working").glob("Arlo - EN & ES.*")):
        shutil.copy2(one, root / "Arlo" / "Working" / one.name)
    shutil.copy2(lipa / "pristine" / "idiograph-lgets.json", root / "idiograph-lgets.json")
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Adam", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    log = base / "agent-log.json"
    kept = (agent_changes.ALL_OPS, os.environ.get(agent_log.PLACE))
    agent_changes.ALL_OPS = None
    os.environ[agent_log.PLACE] = str(log)
    lp = ("--lpets", "Arlo")

    def run(*args, tool="Claude Code"):
        given = ["--config", str(config_file), "--root", str(root), "--json", *args]
        if tool is not None:
            given += ["--tool", tool]
        code, out, err = cli.run(given)
        return code, (support.plain(json.loads(out)) if out.strip() else {}), err + (out if code else "")

    def ops_file(name, operations):
        path = base / f"{name}.json"
        path.write_text(json.dumps({"operations": operations}), encoding="utf-8")
        return str(path)

    def page(fn):
        was = (server_mod.ROOT_OVERRIDE, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY)
        server_mod.ROOT_OVERRIDE, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY = str(root), config_file, {"recent": []}
        try:
            return fn()
        finally:
            server_mod.ROOT_OVERRIDE, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY = was

    def lpets_file() -> dict:
        def read():
            with routes.lpets_scope(arlo):
                return gets_mod.load(arlo)
        return page(read)

    def board_now() -> dict:
        data = json.loads((root / "Arlo" / "Working" / "Arlo - EN & ES.lpets.json").read_text(encoding="utf-8"))
        return next(b for b in data["boards"] if b["id"] == "b1")

    def top_of(board, key):
        parents = themes.parents_of(board["groups"])
        at, last = parents.get(key), None
        while at is not None:
            last, at = at, parents.get(at)
        return last

    def drawn(n, *more):
        code, got, err = run("board", "drawn-on", "Arlo", "--timepoint", str(n), *more, tool=None)
        return code, got, err

    try:
        # ── 1. the app's route: a PET's second card under another LPET, saved from the page as gtPlaceAlso leaves it
        start = digest(root)

        def save_also():
            with routes.lpets_scope(arlo):
                d = gets_mod.load(arlo)
                b = gets_mod.source_board(d)[0]
                version = json.loads(json.dumps({k: v for k, v in b.items() if k != themes.WHY}))
                version["cards"]["T1/g1/2"] = dict(version["cards"]["T1/g1"], x=version["cards"]["T1/g1"]["x"] + 600)
                next(g for g in version["groups"] if g["id"] == "G2")["members"].append("T1/g1/2")
                version["v"] = themes.board_version(b)
                gets_mod.save(arlo, routes.gets_books(arlo), version)
                return gets_mod.state(arlo, routes.gets_books(arlo), board=b["id"])
        answered = page(save_also)
        board = board_now()
        shown = {c["key"]: c for c in answered.get("cards") or []}
        check("419: a PET's second card made in the app and saved from the page stands under the other LPET, its first "
              "where it was, and the board's answer gives it as a second card of the same PET",
              top_of(board, "T1/g1/2") == "G2" and top_of(board, "T1/g1") == "G1"
              and (shown.get("T1/g1/2") or {}).get("copy") == "2" and (shown.get("T1/g1/2") or {}).get("pet") == "g1",
              json.dumps(shown.get("T1/g1/2"))[:300])
        code, got, err = drawn(1, "--pet", "g1")
        check("419: the trace lists both LPETs as drawing on the PET whole",
              code == 0 and sorted((d["id"], d["how"]) for d in got["pets"]["g1"]["lpets"]) == [("G1", "whole"), ("G2", "whole")],
              err[:300] + json.dumps(got.get("pets"))[:300])
        code, got, err = drawn(1, "--pet", "g4")
        check("419: and lists both, through the PET, for its sub-theme",
              code == 0 and sorted((d["id"], d["how"]) for d in got["pets"]["g4"]["lpets"]) == [("G1", "through"), ("G2", "through")],
              err[:300] + json.dumps(got.get("pets"))[:300])
        code, shown_, err = run("gets", "show", *lp, tool=None)
        check("419: gets show reads the board with both cards", code == 0 and "T1/g1/2" in json.dumps(shown_), err[:300])
        page_saved = digest(root)

        # ── 2. an agent: a statement brought into G1, then drawn on by G3 too, by `also`
        brought = "T2/es/T2:13:0"
        code, done, err = run("gets", "apply", "b1", *lp, "--ops",
                              ops_file("bring", [{"op": "bring_in", "statement": brought, "to": "G1"}]), "--note", "Bring it in")
        check("419: a statement brought into G1 by an agent", code == 0 and top_of(board_now(), brought) == "G1", err[:300])
        before = digest(root)
        records = len(agent_changes.read(root))
        also = ops_file("also", [{"op": "also", "item": brought, "to": "G3"}])
        code, dry, err = run("gets", "apply", "b1", *lp, "--ops", also, "--dry-run", tool=None)
        check("419: the also's dry run names the new card by key and the card it copies, and writes nothing, no record line",
              code == 0 and dry.get("also") == [{"card": brought + "/2", "from": brought, "label": "G3"}]
              and dry.get("n_also") == 1 and digest(root) == before and len(agent_changes.read(root)) == records,
              err[:300] + json.dumps(dry.get("also")))
        code, done, err = run("gets", "apply", "b1", *lp, "--ops", also, "--note", ASKED)
        board = board_now()
        code2, got, err2 = drawn(2, "--statement", "T2:13:0")
        lines = agent_changes.read(root)
        check("419: the agent's also puts a second card of the statement under G3, the first staying in G1, and the "
              "trace lists both LPETs drawing on it whole",
              code == 0 and code2 == 0 and top_of(board, brought + "/2") == "G3" and top_of(board, brought) == "G1"
              and sorted((d["id"], d["how"]) for d in got["statements"]["T2:13:0"]["lpets"]) == [("G1", "whole"), ("G3", "whole")],
              err[:300] + err2[:300] + json.dumps(got.get("statements"))[:300])
        check("419: the also is one line in the record of agents' changes",
              len(lines) == records + 1 and lines[-1].get("op") == "gets apply", json.dumps(lines[-1:])[:300])
        texts = json.dumps(done) + json.dumps(dry)
        spoken = (gets_mod.statement_line(lpets_file(), brought) or {}).get("text") or ""
        check("419: the also's answers name keys, never the statement's words", spoken and spoken not in texts, "")
        made = {k: board_now()[k] for k in ("cards", "groups", "discarded")}
        code_u, _x, err_u = run("agents", "undo-change", lines[-1]["id"], "--note", "Take it back")
        check("419: the also's undo puts every file back byte for byte",
              code_u == 0 and digest(root) == before, err_u[:300] + str(changed(before, digest(root))))
        run("gets", "apply", "b1", *lp, "--ops", also, "--note", ASKED)
        check("419: made again, the board's cards and LPETs are as the first also left them",
              {k: board_now()[k] for k in ("cards", "groups", "discarded")} == made, "")

        # ── 3. refusals, each one line, nothing written, dry run or not
        here = digest(root)
        records = len(agent_changes.read(root))
        cases = [("a card the board has not got", [{"op": "also", "item": "T2/g42", "to": "G1"}], "not a card"),
                 ("a card set aside", [{"op": "also", "item": "T1/g4", "to": "G2"}], "set aside"),
                 ("an LPET drawing on it already", [{"op": "also", "item": brought, "to": "G3"}], "holds a card of it"),
                 ("a label not there", [{"op": "also", "item": "T2/g1", "to": "G9"}], "no LPET"),
                 ("no card named", [{"op": "also", "to": "G2"}], "names no card")]
        for what, operations, said in cases:
            spec = ops_file("refused", operations)
            outs = [run("gets", "apply", "b1", *lp, "--ops", spec, "--dry-run", tool=None),
                    run("gets", "apply", "b1", *lp, "--ops", spec, "--note", ASKED)]
            check(f"419: {what} is refused in one line, the dry run too, with nothing written",
                  all(c != 0 and said in e and "Operation 1" in e for c, _d, e in outs) and digest(root) == here
                  and len(agent_changes.read(root)) == records, " | ".join(e[:200] for _c, _d, e in outs))

        # ── 4. the second card set aside: the first is drawn on by its LPET alone, undone byte for byte
        spec = ops_file("aside", [{"op": "set_aside", "items": [brought + "/2"]}])
        code, done, err = run("gets", "apply", "b1", *lp, "--ops", spec, "--note", "Set the second aside")
        code2, got, err2 = drawn(2, "--statement", "T2:13:0")
        check("419: the second card set aside goes to Set aside as any card does, and the statement is drawn on by "
              "G1 alone",
              code == 0 and brought + "/2" in board_now()["discarded"]
              and [d["id"] for d in got["statements"]["T2:13:0"]["lpets"]] == ["G1"], err[:300] + err2[:300])
        code_u, _x, err_u = run("agents", "undo-change", agent_changes.read(root)[-1]["id"], "--note", "Put it back")
        check("419: and its undo puts every file back byte for byte",
              code_u == 0 and digest(root) == here, err_u[:300] + str(changed(here, digest(root))))

        # ── 4b. a second card of one item moved into the LPET already holding the first is refused, an agent's move and
        # the page's save, nothing written (21 November 2026)
        records = len(agent_changes.read(root))
        move = ops_file("twin-move", [{"op": "move", "items": [brought + "/2"], "to": "G1"}])
        outs = [run("gets", "apply", "b1", *lp, "--ops", move, "--dry-run", tool=None),
                run("gets", "apply", "b1", *lp, "--ops", move, "--note", ASKED)]
        check("419: an agent's move of the second card into the LPET holding the first is refused in one line, the dry "
              "run too, and nothing is written",
              all(c != 0 and "already has a card in" in (d.get("error") or e) for c, d, e in outs) and digest(root) == here
              and len(agent_changes.read(root)) == records, " | ".join((d.get("error") or e)[:200] for _c, d, e in outs))

        def save_twin():
            with routes.lpets_scope(arlo):
                d = gets_mod.load(arlo)
                b = gets_mod.source_board(d)[0]
                version = json.loads(json.dumps({k: v for k, v in b.items() if k != themes.WHY}))
                for g in version["groups"]:
                    g["members"] = [m for m in g["members"] if m != brought + "/2"]
                    if g["id"] == "G1":
                        g["members"].append(brought + "/2")
                version["v"] = themes.board_version(b)
                try:
                    gets_mod.save(arlo, routes.gets_books(arlo), version)
                except Exception as exc:
                    return str(exc)
                return ""
        page_said = page(save_twin)
        check("419: the page's save of the same move is refused in one line, nothing written",
              "already has a card in" in page_said and digest(root) == here, page_said + str(changed(here, digest(root))))

        # ── 5. a second card follows its first when its statement's key moves (the take's follower)
        b = {"cards": {brought: {"text": "x"}, brought + "/2": {"text": "x"}}, "groups": [
            {"id": "G1", "members": [brought]}, {"id": "G3", "members": [brought + "/2"]}], "discarded": []}
        gets_mod.board_remapped(b, "T2", {"T2:13:0": "T2:14:0"}, {})
        check("419: a second card follows its first when the statement's key moves, each under its own LPET",
              sorted(b["cards"]) == ["T2/es/T2:14:0", "T2/es/T2:14:0/2"]
              and [g["members"] for g in b["groups"]] == [["T2/es/T2:14:0"], ["T2/es/T2:14:0/2"]], json.dumps(b)[:300])
        lf = gets_mod.lines_followed("T2", {brought: {}, brought + "/2": {}}, {"T2:13:0": {"text": "a b"}},
                                     {"T2:14:0": {"text": "a b"}})
        check("419: the take's follower moves the second card with its first",
              lf == {brought: "T2/es/T2:14:0", brought + "/2": "T2/es/T2:14:0/2"}, json.dumps(lf))

        # ── 6. the LPET table timepoints across matches the board, read independently
        data = lpets_file()
        brd = gets_mod.source_board(data)[0]

        def parts_now():
            with routes.lpets_scope(arlo):
                books = routes.gets_books(arlo)
                return gets_print.study_parts(root, books, None, themes.now_iso()), books
        parts, books = page(parts_now)

        def across():
            with routes.lpets_scope(arlo):
                return [gets_print.lpet_across(g) for g in gets_print.gets_table(parts)]
        table = page(across)
        groups = {g["id"]: g for g in brd["groups"]}
        thrown = set(brd.get("discarded") or [])
        tops = [g for g in groups if top_of(brd, g) is None]
        ok, said = sorted(x["id"] for x in table) == sorted(tops), []
        for x in table:
            keys, todo = [], [x["id"]]
            while todo:
                at = todo.pop()
                for m in groups[at]["members"]:
                    (todo if m in groups else keys).append(m)
            for col in x["cols"]:
                want = sorted(k for k in keys if k not in thrown and gets_mod.split_key(k)["case"] == col["case"])
                got_ = sorted(d["key"] for d in col["draws"])
                state = ((brd.get("rows") or {}).get(x["id"]) or {}).get(col["case"], {}).get("note") or ""
                if got_ != want or col["state"] != state or (not want) != bool(col["nothing"]):
                    ok = False
                    said.append([x["id"], col["case"], got_, want])
                held = ((brd.get("rows") or {}).get(x["id"]) or {}).get(col["case"], {})
                if col["quote"] and not (held.get("quote") or held.get("passage")):
                    # no stand-in: a key quote only where he chose one (Adam, 17 November 2026)
                    ok = False
                    said.append([x["id"], col["case"], "stand-in"])
                if col["quote"] and not col["quote"]["cite"].startswith("Arlo, " + col["case"]):
                    ok = False
                    said.append([x["id"], col["case"], col["quote"]["cite"]])
            if [c["case"] for c in x["cols"]] != ["T1", "T2", "T3"]:
                ok = False
        check("419: the LPET table across gives each LPET a column a timepoint, its state the board's row, its key quote "
              "cited with the participant and timepoint where he chose one and none where he did not, and what it draws on there the board's cards by key, both "
              "duplicates among them",
              ok and any(d["key"] == "T1/g1/2" for x in table for c in x["cols"] for d in c["draws"])
              and any(d["key"] == brought + "/2" for x in table for c in x["cols"] for d in c["draws"]), json.dumps(said)[:600])

        # ── 7. the appendix: a PET no LPET draws on with his reason, then the Word document and the PDF
        move = ops_file("move", [{"op": "move", "items": ["T2/g3"], "to": None}])
        code, _x, err = run("gets", "apply", "b1", *lp, "--ops", move, "--note", "Take it out")
        why = base / "why.json"
        why.write_text(json.dumps([{"op": "why", "participant": "Arlo", "timepoint": "T2", "pet": "g3", "why": WHY}]), encoding="utf-8")
        code2, _x, err2 = run("trajectories", "apply", "--ops", str(why), "--note", "Say why")
        parts, books = page(parts_now)

        def unplaced():
            with routes.lpets_scope(arlo):
                return gets_print.lpet_unplaced(parts)
        rows = page(unplaced)
        check("419: the PETs no LPET draws on list T2's g3 with his reason",
              code == 0 and code2 == 0 and any(r["case"] == "T2" and r["pet"] == "g3" and r["why"] == WHY for r in rows),
              err[:200] + err2[:200] + json.dumps(rows)[:300])
        titles = [g["label"] for g in brd["groups"] if g["id"] in tops]
        states = [s.get("note") for cs in (brd.get("rows") or {}).values() for s in cs.values() if s.get("note")]

        before = digest(root)
        code, word, err = run("gets", "export", "b1", *lp, "--word", tool=None)
        text = ""
        if code == 0:
            with zipfile.ZipFile(word["path"]) as z:
                xml = z.read("word/document.xml").decode("utf-8")
            text = re.sub(r"<[^>]+>", " ", xml)
        squash = lambda s: support.squashed(s.replace("&#x27;", "'").replace("&apos;", "'"))  # noqa: E731
        found = squash(text)
        check("419: the Word appendix holds every LPET's title, each state and the unplaced PET's reason, and writes "
              "only its own file",
              code == 0 and titles and all(squash(themes.bare(t)) in found or squash(t) in found for t in titles)
              and all(squash(s) in found for s in states) and squash(WHY) in found
              and changed(before, digest(root)) == [Path(word["path"]).resolve().relative_to(root.resolve()).as_posix()],
              err[:300] + str([t for t in titles if squash(t) not in found]) + str(changed(before, digest(root)))[:200])
        before = digest(root)
        code, pdf, err = run("gets", "export", "b1", *lp, tool=None)
        said_pdf = support.squashed(" ".join(pdftext.pages_text(Path(pdf["path"]).read_bytes()))) if code == 0 else ""
        check("419: the PDF appendix holds every LPET's title, each state and the unplaced PET's reason",
              code == 0 and all(support.squashed(t) in said_pdf for t in titles)
              and all(support.squashed(s) in said_pdf for s in states) and support.squashed(WHY) in said_pdf,
              err[:300] + str([t for t in titles if support.squashed(t) not in said_pdf])
              + str([s for s in states if support.squashed(s) not in said_pdf])[:300])

        # ── 8. a second card under an LPET draws on its PET, so his reason is hidden on every read and kept in the
        # file (drawswordfix2), by an agent's also and by the page's save, each undo showing it again
        def file_why():
            return board_now().get(themes.WHY) or {}

        def listed():
            p, _b = page(parts_now)

            def read():
                with routes.lpets_scope(arlo):
                    return gets_print.lpet_unplaced(p)
            return any(r["case"] == "T2" and r["pet"] == "g3" for r in page(read))
        before = digest(root)
        g3 = ops_file("also-g3", [{"op": "also", "item": "T2/g3", "to": "G3"}])
        code, _x, err = run("gets", "apply", "b1", *lp, "--ops", g3, "--note", ASKED)
        code2, got, err2 = drawn(2, "--pet", "g3")
        code3, shown_, err3 = run("gets", "show", *lp, tool=None)
        check("419: a second card of a PET his reason is on, under an LPET, draws on it: the trace names that LPET and "
              "no reason, gets show and the appendix's list leave the reason out, and the file keeps it",
              code == 0 and code2 == 0 and code3 == 0 and top_of(board_now(), "T2/g3/2") == "G3"
              and [d["id"] for d in got["pets"]["g3"]["lpets"]] == ["G3"] and "why" not in got["pets"]["g3"]
              and WHY not in json.dumps(shown_) and not listed() and file_why().get("T2/g3") == WHY,
              err[:200] + err2[:200] + err3[:200] + json.dumps(got.get("pets"))[:300])
        code_u, _x, err_u = run("agents", "undo-change", agent_changes.read(root)[-1]["id"], "--note", "Take it back")
        check("419: the also's undo puts every file back byte for byte and the reason shows again",
              code_u == 0 and digest(root) == before and listed(), err_u[:300] + str(changed(before, digest(root))))

        def page_save(edit):
            def go():
                with routes.lpets_scope(arlo):
                    d = gets_mod.load(arlo)
                    b = gets_mod.source_board(d)[0]
                    version = json.loads(json.dumps({k: v for k, v in b.items() if k != themes.WHY}))
                    edit(version)
                    version["v"] = themes.board_version(b)
                    return gets_mod.save(arlo, routes.gets_books(arlo), version)
            return page(go)

        def dup(version):
            version["cards"]["T2/g3/2"] = dict(version["cards"]["T2/g3"], x=version["cards"]["T2/g3"]["x"] + 600)
            next(g for g in version["groups"] if g["id"] == "G3")["members"].append("T2/g3/2")

        def undup(version):
            version["cards"].pop("T2/g3/2", None)
            for g in version["groups"]:
                g["members"] = [m for m in g["members"] if m != "T2/g3/2"]
        made = page_save(dup)
        check("419: the page's save of the second card answers no reason for the PET, the file keeping it",
              "T2/g3" not in (made.get("why") or {}) and file_why().get("T2/g3") == WHY and not listed(),
              json.dumps(made.get("why")))
        back = page_save(undup)
        check("419: and the page's Undo, a save of the board without it, shows the reason again in its answer and every read",
              (back.get("why") or {}).get("T2/g3") == WHY and listed(), json.dumps(back.get("why")))

        # ── 9. a case folder with a second name: the LPET table's cites, its exports and agents'
        # answers name the participant as every screen does, never the folder's second name, and Rename's name
        # where he renamed them keeping the folder (drawsbuild2, the review's privacy finding)
        sec = base / "second" / "Allotment"
        shutil.copytree(root, sec)
        SECOND = "Smithson"
        folder2 = f"P1 - Arlo-{SECOND}"
        (sec / "Arlo").rename(sec / folder2)
        book2 = sec / folder2 / "Arlo - EN & ES.xlsx"
        config2 = base / "config-second.json"
        config2.write_text(json.dumps({"projects": [{"root": str(sec)}], "interviewer": "Adam", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")

        def run2(*args, tool="Claude Code"):
            given = ["--config", str(config2), "--root", str(sec), "--json", *args]
            if tool is not None:
                given += ["--tool", tool]
            code, out, err = cli.run(given)
            return code, out, err

        def page2(fn):
            was = (server_mod.ROOT_OVERRIDE, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY)
            server_mod.ROOT_OVERRIDE, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY = str(sec), config2, {"recent": []}
            try:
                return fn()
            finally:
                server_mod.ROOT_OVERRIDE, server_mod.CONFIG_PATH, server_mod.STATE_MEMORY = was

        def made(out):
            """The file an export wrote: its answer names the folder as the screens do, never by its second name"""
            name = Path(support.plain(json.loads(out))["path"]).name
            return max(sec.rglob(name), key=lambda f: f.stat().st_mtime)

        def outputs(who):
            """Every export of the LPET table and every agent's read of the LPETs, as text, and whether each holds
            `who, T1` as a key quote's cite."""
            said = {}
            code, out, err = run2("gets", "export", "b1", "--lpets", who, "--word", tool=None)
            if code == 0:
                with zipfile.ZipFile(made(out)) as z:
                    said["word"] = z.read("word/document.xml").decode("utf-8")
            said["word_answer"] = out + err
            code, out, err = run2("gets", "export", "b1", "--lpets", who, "--replace", tool=None)
            if code == 0:
                said["pdf"] = " ".join(pdftext.pages_text(made(out).read_bytes()))
            said["pdf_answer"] = out + err
            code, out, err = run2("gets", "export", "b1", "--lpets", who, "--canvas", "pdf", "--replace", tool=None)
            if code == 0:
                said["canvas"] = " ".join(pdftext.pages_text(made(out).read_bytes()))
            said["canvas_answer"] = out + err

            def html():
                return routes.gets_print_page({"workbook": str(book2), "lpets": "1", "board": "b1", "what": "all",
                                               "auto": "0"})[1]
            said["html"] = page2(html)
            for name, args in (("show", ("gets", "show", "--lpets", who)),
                               ("drawn", ("board", "drawn-on", who, "--timepoint", "1")),
                               ("trajectories", ("trajectories", "show"))):
                code, out, err = run2(*args, tool=None)
                said[name] = out + err
            return said

        said = outputs("Arlo")
        leaks = [k for k, v in said.items() if SECOND in v]
        check("419: with a case folder with a second name no export of the LPET table (the print view, the Word document, "
              "the PDF, the canvas's PDF) and no agent's read holds the folder's second name, and each quote is cited "
              "Arlo, as every screen names him",
              not leaks and all(k in said for k in ("word", "pdf", "canvas", "html"))
              and "Arlo, T1" in said["word"] and "arlo,t1" in support.squashed(said["pdf"]) and "Arlo, T1" in said["html"],
              str(leaks) + str(sorted(said))[:200])
        # Rename from his row on the project's page, the folder kept (the command line's rename finds no folder with a
        # second name: Found in passing, drawsbuild2)
        def rename():
            try:
                routes.api_rename({"root": str(sec), "case": "P1 - Arlo", "name": "Ansel", "folder": False, "op": "rename"})
                return 0, "", ""
            except Exception as exc:  # noqa: BLE001
                return 1, "", str(exc)
        code, out, err = page2(rename)
        said = outputs("Ansel")
        leaks = [k for k, v in said.items() if SECOND in v]
        check("419: renamed Ansel with the folder kept, the cites say Ansel in the print view, the Word document and the "
              "PDF, and still nothing holds the folder's second name",
              code == 0 and not leaks and "Ansel, T1" in said["word"] and "ansel,t1" in support.squashed(said["pdf"])
              and "Ansel, T1" in said["html"] and "Arlo, T1" not in said["word"],
              (err or out)[:300] + str(leaks))

        # ── 10. a long State and a long key quote (drawsbuild5, the second review's medium): a State of 600 words and a
        # key quote of a passage of about 2800 words, each taller than a page, flow onto the next pages of the PDF, every
        # word of each in the PDF, the print view and the Word document, and nothing printed past a page's foot line
        state = " ".join(f"zs{k:03d}" for k in range(1, 601))
        passage = " ".join(f"zq{k:04d}" for k in range(1, 2801))
        code, _x, err = run("turn", "edit", "Arlo", "T1", "3", "--text", passage, "--note", "A long passage")
        long_ops = base / "long.json"
        long_ops.write_text(json.dumps([
            {"op": "state", "participant": "Arlo", "lpet": "G1", "timepoint": "T1", "state": state},
            {"op": "quote", "participant": "Arlo", "lpet": "G1", "timepoint": "T1",
             "passage": {"interview": "T1", "turn": "T1:3"}}]), encoding="utf-8")
        code2, _x, err2 = run("trajectories", "apply", "--ops", str(long_ops), "--note", "A long state and quote")
        held = ((board_now().get("rows") or {}).get("G1") or {}).get("T1") or {}
        check("419: a State of 600 words and a key quote of a passage of 2800 words are kept on G1 at T1",
              code == 0 and code2 == 0 and held.get("note") == state and (held.get("passage") or {}).get("turn") == "T1:3",
              err[:300] + err2[:300] + json.dumps({k: str(v)[:80] for k, v in held.items()}))
        tokens = state.split() + passage.split()

        def missing(said):
            flat = support.squashed(said)
            return [t for t in tokens if t not in flat]
        code, word, err = run("gets", "export", "b1", *lp, "--word", tool=None)
        text = ""
        if code == 0:
            with zipfile.ZipFile(word["path"]) as z:
                text = re.sub(r"<[^>]+>", " ", z.read("word/document.xml").decode("utf-8"))
        gone = missing(text) if code == 0 else tokens
        flat = re.sub(r"\s+", "", text)
        check("419: every word of the long State and the long key quote is in the Word document, the quote in double "
              "marks as the PDF, the print view and the screen set it",
              code == 0 and not gone and "“zq0001" in flat and "zq2800”" in flat,
              err[:300] + f"{len(gone)} missing, first {gone[:3]}")

        def html_page():
            return routes.gets_print_page({"workbook": str(arlo), "lpets": "1", "board": "b1", "what": "all", "auto": "0"})[1]
        served = page(html_page)
        gone = missing(html_mod.unescape(re.sub(r"<[^>]+>", " ", served)))
        check("419: every word of each is in the print view", not gone, f"{len(gone)} missing, first {gone[:3]}")
        code, pdf, err = run("gets", "export", "b1", *lp, "--replace", tool=None)
        body = Path(pdf["path"]).read_bytes() if code == 0 else b""
        gone = missing(" ".join(pdftext.pages_text(body))) if code == 0 else tokens
        check("419: every word of the long State and the long key quote is in the PDF, none cut off at a page's foot",
              code == 0 and not gone, err[:300] + f"{len(gone)} missing, first {gone[:3]}")
        # by the text's places on each page (pdftotext's boxes): nothing at or below the foot line but the foot
        boxes = shutil.which("pdftotext")
        said_boxes, why_not = "", ""
        if code != 0:
            why_not = "no PDF to read"
        elif not boxes:
            why_not = "no pdftotext on this machine to read the words' places"
        else:
            import subprocess
            # the boxes go to stdout ("-"), so no output file's path is involved (Windows' paths broke it, run 44023877293)
            try:
                got = subprocess.run([boxes, "-bbox", pdf["path"], "-"], capture_output=True)
            except OSError as e:
                got = None
                why_not = f"pdftotext could not be run ({type(e).__name__})"
            if got is not None and got.returncode != 0:
                why_not = f"pdftotext exited with status {got.returncode} on this machine, so the words' places are not read"
            elif got is not None:
                said_boxes = got.stdout.decode("utf-8", "replace")
        if why_not:
            support.skip("419: nothing printed past a page's foot line", why_not)
        else:
            pages = re.findall(r"<page [^>]*>(.*?)</page>", said_boxes, flags=re.S)
            over, feet, seen = [], 0, set()
            for n, one in enumerate(pages, 1):
                words = [(float(a), float(b), float(c), float(d), html_mod.unescape(t)) for a, b, c, d, t in re.findall(
                    r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>', one)]
                said = [w[4] for w in words]
                tops = [words[k][1] for k in range(len(words) - 2)
                        if said[k] == "Page" and said[k + 2] == "of" and said[k + 1].isdigit()]
                if not tops:
                    continue
                feet += 1
                foot = max(tops)
                over += [(n, w[4]) for w in words if w[3] > foot - 1 and abs(w[1] - foot) > 2]
                over += [(n, w[4]) for w in words if abs(w[1] - foot) <= 2 and re.fullmatch(r"z[sq]\d+", w[4])]
                seen |= {re.sub(r"\W", "", w[4]) for w in words if w[3] <= foot - 1}
            unseen = [t for t in tokens if t not in seen]
            check("419: on every page of the PDF nothing is printed past the foot line and every word of the long State "
                  "and key quote stands above it, by the words' places",
                  bool(pages) and feet == len(pages) and not over and not unseen,
                  f"{len(pages)} pages, {feet} feet, over {over[:5]}, {len(unseen)} not above a foot line {unseen[:3]}")
    finally:
        agent_changes.ALL_OPS = kept[0]
        if kept[1] is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = kept[1]
        agent_log.flush()
