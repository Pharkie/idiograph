"""Area 402: `gets take`'s dry run counts what the take changes, by keys, and the take writes exactly that, keeping
each board's own structure (takedry, 16 November 2026).

Found by the GRAVITY session on a longitudinal project: once every statement was placed on the PETs boards, the
LPETs still held old copies of each timepoint, and `gets take T1 --lpets <participant>`'s dry run said only that the
copy differed. What is checked, on the longitudinal demo as a fresh clone has it (a scratch copy, as area 394 makes
it, never the repo's demo folders). At T2 one participant's statements are added, reworded, moved and removed, and a
PET is made, retitled and taken apart, each through the command line as an agent. A: the dry run answers counts and
keys and never a word, what changes in the copy and on each LPETs board, the board Trajectories reads marked, and
writes nothing. B: the take answers the same counts, and they are what the files show changed: the copy's PETs and
statements by key, each board's cards renamed, added and moved, the cards whose source has gone, and the Trajectories
cells whose key quote or bold changes. C: each board keeps its own structure: its LPETs, their titles and places,
the cards under each in order (a card's key followed where the take gave it a new one), the bin, the picks and the
rows with the states, key quotes and bold Trajectories shows. D: the take is one line in the record of agents'
changes, and its undo puts the LPETs' copy and boards back, after which the take comes again with the same counts.
E: the LGETs' take of that participant, the same code, writes what its dry run said too.

Then on a second copy (takefix, 16 November 2026): F, a packed board, an LPET 30 px under another and a sticky note in
it, where a card grows from one line to four: the take moves the LPET and the note down, counts them and passes, and
nothing else changes. G, a stacked, picked statement card ticked as a key quote whose key changes, a write that could
not reach the LPETs' copy left behind: it keeps its stack, its pick and its key quote with his bold, and its old and
new keys reach an agent plain. H, a refused take, its dry run too, names the board and what differs by kind and key
and writes nothing. I, the route's dry run leaves no lock file."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from . import support
from .a394_lipa_demo import as_cloned
from .support import check as said_check

WHO = "Nell"


def check(name, ok, detail=""):
    said_check(name, bool(ok), "" if ok else str(detail)[:700])


def test_take_dry(scratch: Path):
    print("\n402. gets take's dry run counts by keys what the take changes on a participant's LPETs, writes nothing, "
          "and the take writes exactly that, each board keeping its LPETs, cards, picks and key quotes (takedry, "
          "16 November)")
    import agent_changes
    import agent_log
    import cli
    import gets as gets_mod
    import idiograph_routes as routes
    import server as server_mod
    import themes
    from server import WorkbookError

    fresh = scratch / "take-402-clone"
    shutil.rmtree(fresh, ignore_errors=True)
    shutil.copytree(support.source("demo"), fresh, ignore=as_cloned)
    kept = (server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO, os.environ.get(agent_log.PLACE), server_mod.CONFIG_PATH)
    cfg = scratch / "take-402-config.json"
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Interviewer", "corpus": "", "gravity_reference": "",
                               "corpus_exclude": []}), encoding="utf-8")
    n_ops = [0]
    try:
        server_mod.DEMO_DIR = server_mod.SHIPPED_DEMO = fresh
        os.environ[agent_log.PLACE] = str(scratch / "take-402-agent-log.json")
        demo = server_mod.demo_lipa_dir()
        routes.fill_demo()
        # the demo keeps no restore points, so its participants are worked on as a project of their own
        root = scratch / "take-402-allotment"
        shutil.rmtree(root, ignore_errors=True)
        shutil.copytree(demo, root, ignore=shutil.ignore_patterns("pristine", "source"))
        cfg.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Interviewer", "corpus": "",
                                   "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
        server_mod.CONFIG_PATH = cfg
        routes.api_project({"root": str(root), "agents": True})
        book = next(root.glob(f"{WHO}/{WHO} - *.xlsx"))
        lpfile = gets_mod.lpets_path(book)

        def run(*args, note="Bring Nell's midsummer changes in"):
            words = ["--root", str(root), "--config", str(cfg), *args, "--json"]
            if note:
                words += ["--note", note, "--tool", "Claude Code"]
            code, out, err = cli.run(words)
            return code, (support.plain(json.loads(out)) if out.strip() else {}), err + (out if code else "")

        def spec(body: dict) -> str:
            n_ops[0] += 1
            path = scratch / f"take-402-spec-{n_ops[0]}.json"
            path.write_text(json.dumps(body), encoding="utf-8")
            return str(path)

        def tree() -> dict:
            # a lock file among them, so a dry run that left one is caught (takefix)
            return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*"))
                    if p.is_file() and "pristine" not in p.parts}

        def read() -> dict:
            return json.loads(lpfile.read_text(encoding="utf-8"))

        # ── the edits at T2, each through the command line as an agent
        copy_was = lpfile.read_bytes()
        code, shown, err = run("board", "show", WHO, "--timepoint", "2", note=None)
        groups = {g["id"]: [s["id"] for s in g["statements"]] for g in shown.get("themes") or []}
        check("402: Nell's midsummer PETs board reads, four PETs over her statements", code == 0 and len(groups) == 4,
              err or groups)
        code, turn, err = run("turn", "show", WHO, "T2", "27", note=None)
        t = turn["turns"][0]
        pair = t["pairs"][0]
        code_w, _x, err_w = run("turn", "write", WHO, "T2", "27", "--from", spec({
            "version": t["version"], "request": "Reword one, add one",
            "pairs": [{"key": pair["key"], "statement": "Outdone in three weeks by her own mother", "quote": pair["quote"]},
                      {"statement": "A mother who worked without a word", "quote": "She didn't say anything. She just worked."}]}))
        code, turn, err = run("turn", "show", WHO, "T2", "35", note=None)
        t2 = turn["turns"][0]
        code_r, _x, err_r = run("turn", "write", WHO, "T2", "35", "--from", spec({
            "version": t2["version"], "request": "Take one off", "remove": [t2["pairs"][0]["key"]]}))
        # a save brings its statements into the LPETs' copy itself (copiesadd, 16 November); one that could not reach
        # it, the file unreadable then, leaves the copy as it was before the writes, so the take is what brings in the
        # statement added, the one reworded and the one taken off, as section G does for keys
        lpfile.write_bytes(copy_was)
        code, shown, err = run("board", "show", WHO, "--timepoint", "2", note=None)
        groups = {g["id"]: [s["id"] for s in g["statements"]] for g in shown.get("themes") or []}
        code_b, _x, err_b = run("board", "apply", WHO, shown["id"], "--timepoint", "2", "--ops", spec({"operations": [
            {"op": "move", "items": [groups["g1"][0]], "to": "g2"},
            {"op": "retitle", "label": "g3", "title": "Ground that is hers at last"},
            {"op": "apart", "label": "g4"},
            {"op": "make", "ref": "n", "title": "Help that comes unasked", "inside": None,
             "members": groups["g4"][:2]}]}))
        check("402: a statement reworded and one added, one removed, one moved, a PET retitled, one taken apart and one "
              "made at T2, each through the command line", code_w == code_r == code_b == 0, err_w + err_r + err_b)

        # ── A. the dry run: counts and keys, never a word, nothing written
        lp_was = read()
        whole = tree()
        code, dry, err = run("gets", "take", "T2", "--lpets", WHO, "--dry-run")
        counts = dry.get("counts") or {}
        c = counts.get("copy") or {}
        boards = counts.get("boards") or []
        traj = [b for b in boards if b.get("trajectories")]
        dumped = json.dumps(counts)
        words = [w for w in ("Outdone", "mother", "without a word", "hers at last", "unasked") if w in dumped]
        check("402: the dry run counts the copy's changes: a PET added, one retitled and one removed, a statement added, "
              "one reworded and some moved",
              code == 0 and dry.get("dry_run") and c.get("n_pets_added") == 1 and c.get("n_pets_removed") == 1
              and c.get("n_pets_renamed") == 1 and c.get("n_statements_added") >= 1 and c.get("n_statements_moved") >= 1
              and c.get("n_statements_changed", 0) + c.get("n_statements_removed", 0) >= 1
              and all(c[f"n_{k}"] == len(c[k]) for k in ("pets_added", "statements_added", "statements_moved",
                                                          "statements_changed", "statements_removed")),
              err or json.dumps(c)[:600])
        check("402: it names each LPETs board, the one Trajectories reads among them, with the LPETs and cards it "
              "changes, by key", len(boards) == len(lp_was["boards"]) and len(traj) == 1
              and any(b["n_labels_changed"] and b["n_cards_changed"] and b["n_cards_lost"] and b["n_cards_added"] for b in boards)
              and all(set(b["labels_changed"]) <= {g["id"] for x in lp_was["boards"] for g in x["groups"]} for b in boards),
              json.dumps(boards)[:700])
        check("402: the dry run says no participant's word, in its JSON or its lines, and writes nothing",
              not words and tree() == whole, words or "a file changed")

        code, raw, err = cli.run(["--root", str(root), "--config", str(cfg), "gets", "take", "T2", "--lpets", WHO,
                                  "--dry-run", "--json"])
        raw_counts = json.loads(raw).get("counts") or {}
        check("402: the dry run's keys reach an agent plain, never marked as a participant's words, the board's name alone "
              "marked", code == 0 and raw_counts.get("copy") == c and all(
                  {k: v for k, v in b.items() if k != "name"} == {k: v for k, v in s.items() if k != "name"}
                  and isinstance(b["name"], dict) for b, s in zip(raw_counts.get("boards") or [], boards)),
              err or raw[:400])

        # ── B. the take: the same counts, and the files show exactly that
        code, took, err = run("gets", "take", "T2", "--lpets", WHO)
        lp_now = read()
        check("402: the take answers the counts its dry run said", code == 0 and took.get("counts") == counts,
              err or json.dumps(took.get("counts"))[:600])
        old, new = lp_was["cases"]["T2"], lp_now["cases"]["T2"]
        key = lambda kind, ident: gets_mod.card_of("T2", kind, ident)  # noqa: E731
        o_ids, n_ids = {p["id"] for p in old["pets"]}, {p["id"] for p in new["pets"]}
        o_lines, n_lines = old["lines"], new["lines"]
        reworded = sorted(key("es", k) for k in set(o_lines) & set(n_lines)
                          if o_lines[k]["text"] != n_lines[k]["text"] or o_lines[k].get("quotes") != n_lines[k].get("quotes"))
        check("402: the copy changed as counted: its PETs and statements added and removed, and reworded, by key",
              sorted(key("group", i) for i in n_ids - o_ids) == sorted(c["pets_added"])
              and sorted(key("group", i) for i in o_ids - n_ids) == sorted(c["pets_removed"])
              and sorted(key("es", k) for k in set(n_lines) - set(o_lines)) == sorted(c["statements_added"])
              and sorted(key("es", k) for k in set(o_lines) - set(n_lines)) == sorted(c["statements_removed"])
              and reworded == sorted(c["statements_changed"]), json.dumps(c)[:600])
        said = {b["board"]: b for b in boards}
        qmap = gets_mod.quotes_followed("T2", old, new)
        wrong = []
        for was_b in lp_was["boards"]:
            now_b = next(b for b in lp_now["boards"] if b["id"] == was_b["id"])
            b = said[was_b["id"]]
            ren = dict(b["cards_renamed"])
            m = lambda k: ren.get(k, k)  # noqa: E731
            cw, cn = was_b["cards"], now_b["cards"]
            if set(cn) != {m(k) for k in cw} | set(b["cards_added"]):
                wrong.append(f"{was_b['id']} cards")
            if sorted(k for k in cw if (cw[k].get("x"), cw[k].get("y")) != (cn[m(k)].get("x"), cn[m(k)].get("y"))) \
                    != sorted(k for k in cw if m(k) in b["cards_moved"]):
                wrong.append(f"{was_b['id']} moved")
            lost = sorted(k for k in cn if k.startswith("T2/") and (
                (gets_mod.split_key(k)["kind"] == "group" and gets_mod.split_key(k)["ident"] not in n_ids)
                or (gets_mod.split_key(k)["kind"] == "es" and gets_mod.split_key(k)["ident"] not in n_lines))
                and not ((gets_mod.split_key(k)["kind"] == "group" and gets_mod.split_key(k)["ident"] not in o_ids)
                         or (gets_mod.split_key(k)["kind"] == "es" and gets_mod.split_key(k)["ident"] not in o_lines)))
            if lost != b["cards_lost"]:
                wrong.append(f"{was_b['id']} lost {lost} {b['cards_lost']}")
            cells = lambda data, board: {f"{r['id']}/T2": (  # noqa: E731
                (r["cells"]["T2"]["quote"] or {}).get("text"),
                r["cells"]["T2"]["chosen"], r["cells"]["T2"]["bold"])
                for r in gets_mod.lpet_rows(data, board, ["T2"], bare=False)}
            cb, ca = cells(lp_was, was_b), cells(lp_now, now_b)
            if sorted(k for k in set(cb) | set(ca) if cb.get(k) != ca.get(k)) != b["cells_changed"]:
                wrong.append(f"{was_b['id']} cells")
            # ── C. its own structure kept
            groups_was = [dict(g, members=[m(x) for x in g["members"]]) for g in was_b.get("groups") or []]
            if groups_was != now_b.get("groups") or [m(k) for k in was_b.get("discarded") or []] != now_b.get("discarded"):
                wrong.append(f"{was_b['id']} labels")
            # a ticked quote follows its words to a new place, its bold with it (takefix)
            rows_was = json.loads(json.dumps(was_b.get("rows") or {}))
            for cases in rows_was.values():
                if (cases.get("T2") or {}).get("quote") in qmap:
                    cases["T2"]["quote"] = qmap[cases["T2"]["quote"]]
            if rows_was != (now_b.get("rows") or {}) or any(was_b.get(f) != now_b.get(f) for f in ("picks", "notes", "name")):
                wrong.append(f"{was_b['id']} picks, rows or notes")
        check("402: each board changed exactly as counted: its cards renamed, added and moved, the cards whose source "
              "has gone and the Trajectories cells whose key quote or bold changes", not [w for w in wrong if
                                                                                          "labels" not in w and "picks" not in w], wrong)
        check("402: each board kept its own structure: its LPETs, their titles and places, the cards under each in "
              "order, the bin, the picks and the rows Trajectories shows", not [w for w in wrong if "labels" in w or "picks" in w],
              wrong)

        # the take's own guard: the board as written passes, and one with a card moved to another LPET, a title changed
        # or a key quote's row changed would be refused
        was_b = lp_was["boards"][0]
        now_b = next(b for b in lp_now["boards"] if b["id"] == was_b["id"])
        eff = said[was_b["id"]]
        moved_card = json.loads(json.dumps(now_b))
        g0, g1 = moved_card["groups"][0], moved_card["groups"][1]
        g1["members"].append(g0["members"].pop())
        retitled = json.loads(json.dumps(now_b))
        retitled["groups"][0]["label"] += " again"
        unticked = json.loads(json.dumps(now_b))
        unticked["rows"] = {}
        check("402: the take's guard passes the board as it wrote it and refuses one with a card under another LPET, an "
              "LPET retitled or the key quotes changed",
              gets_mod.structure_kept(was_b, now_b, "T2", dict(eff["cards_renamed"]), qmap, eff, eff["cards_lost"])
              and not any(gets_mod.structure_kept(was_b, x, "T2", dict(eff["cards_renamed"]), qmap, eff, eff["cards_lost"])
                          for x in (moved_card, retitled, unticked)))

        # ── D. recorded, and its undo puts it back
        line = [e for e in agent_changes.read(root) if e.get("op") == "gets take"]
        code, undone, err = run("agents", "undo-change", line[-1]["id"] if line else "c0", note="Put the take back")
        check("402: the take is a line in the record of agents' changes, and its undo puts the LPETs back as they were "
              "before it", len(line) == 1 and code == 0 and json.loads(lpfile.read_text(encoding="utf-8"))["cases"]["T2"]
              == lp_was["cases"]["T2"]
              and [b["groups"] for b in read()["boards"]] == [b["groups"] for b in lp_was["boards"]],
              err or [e.get("op") for e in agent_changes.read(root)])
        code, again, err = run("gets", "take", "T2", "--lpets", WHO)
        check("402: after the undo the take comes again with the same counts", code == 0 and again.get("counts") == counts,
              err or json.dumps(again)[:400])

        # ── E. the LGETs' take of the participant, the same code: its dry run is what the take writes
        lgets = root / gets_mod.LGETS_FILE
        before_g = lgets.read_bytes()
        code, dry_g, err = run("gets", "take", WHO, "--dry-run")
        kept_g = lgets.read_bytes() == before_g
        code2, took_g, err2 = run("gets", "take", WHO)
        check("402: on the LGETs a participant's take writes what its dry run said, the dry run writing nothing",
              code == code2 == 0 and kept_g and dry_g.get("counts") and dry_g["counts"] == took_g.get("counts")
              and lgets.read_bytes() != before_g, err + err2 + json.dumps(dry_g)[:300])

        # ── F to I (takefix, 16 November 2026), on a second copy of the demo's participants, Nell's LPETs as they ship
        root2 = scratch / "take-402-packed"
        shutil.rmtree(root2, ignore_errors=True)
        shutil.copytree(demo, root2, ignore=shutil.ignore_patterns("pristine", "source"))
        cfg.write_text(json.dumps({"projects": [{"root": str(root)}, {"root": str(root2)}], "interviewer": "Interviewer",
                                   "corpus": "", "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
        routes.api_project({"root": str(root2), "agents": True})
        book2 = next(root2.glob(f"{WHO}/{WHO} - *.xlsx"))
        lp2 = gets_mod.lpets_path(book2)

        def run2(*args, note="Bring Nell's changes in"):
            words = ["--root", str(root2), "--config", str(cfg), *args, "--json"]
            if note:
                words += ["--note", note, "--tool", "Claude Code"]
            code, out, err = cli.run(words)
            return code, (support.plain(json.loads(out)) if out.strip() else {}), err + (out if code else "")

        def tree2() -> dict:
            return {p.relative_to(root2).as_posix(): p.read_bytes() for p in sorted(root2.rglob("*")) if p.is_file()}

        # I. the route's dry run makes no lock file where there was none (the command line's is checked in A)
        lock_was = sorted(p.name for p in root2.rglob("*.lock"))
        whole2 = tree2()
        try:
            routes.api_gets_cases({"root": str(root2), "op": "take", "case": WHO, "dry_run": True})
        except WorkbookError:
            pass
        check("402: the take's dry run through the app's route leaves no lock file and writes nothing",
              sorted(p.name for p in root2.rglob("*.lock")) == lock_was and tree2() == whole2,
              sorted(p.name for p in root2.rglob("*.lock")))

        def boxes(data: dict, board: dict) -> dict:
            shown = gets_mod.named(board, data)
            return themes._solid_boxes(shown, themes.layout_boxes(shown, gets_mod.card_height))

        # F. a packed board, as Auto-arrange's grid and an agent's square boards leave it: G4 30 px under G1, a sticky
        # note in G4, and the bottom card of G1, T3's g1, growing from one line to four through a retitle at T3, its
        # title made one line first and taken in
        code, shown3, err = run2("board", "show", WHO, "--timepoint", "3", note=None)
        code_s, _x, err_s = run2("board", "apply", WHO, shown3.get("id") or "", "--timepoint", "3", "--ops", spec({
            "operations": [{"op": "retitle", "label": "g1", "title": "Letting go"}]}))
        code_s2, _x, err_s2 = run2("gets", "take", "T3", "--lpets", WHO)
        check("402: T3's first PET given a title of one line and taken into the LPETs", code_s == code_s2 == 0,
              err_s + err_s2)
        lp = json.loads(lp2.read_text(encoding="utf-8"))
        b = next(x for x in lp["boards"] if x["id"] == lp.get("current"))
        g4 = next(g for g in b["groups"] if g["id"] == "G4")
        b["notes"] = [{"id": "n402", "text": "x", "colour": "yellow", "x": g4["x"] + 20, "y": g4["y"] + 60, "in": "G4"}]
        drawn = boxes(lp, b)
        by_id = {g["id"]: g for g in b["groups"]}
        themes._shift(by_id, b, "G4", 0, drawn["G1"][1] + drawn["G1"][3] + 30 - drawn["G4"][1])
        lp2.write_text(json.dumps(lp, ensure_ascii=False, indent=1), encoding="utf-8")
        packed = json.loads(lp2.read_text(encoding="utf-8"))
        long_title = ("Her mother's garden found again in her own half, the village and England meeting at the "
                      "fence, the guest's half given away and the wish found to be the garden itself, slowly")
        code_t, _x, err_t = run2("board", "apply", WHO, shown3.get("id") or "", "--timepoint", "3", "--ops", spec({
            "operations": [{"op": "retitle", "label": "g1", "title": long_title}]}))
        code, dry3, err3 = run2("gets", "take", "T3", "--lpets", WHO, "--dry-run")
        bd = next((x for x in (dry3.get("counts") or {}).get("boards") or [] if x["board"] == b["id"]), {})
        check("402: on a packed board a card grown from one line to four pushes the LPET under it and its sticky note "
              "down, and the take's dry run passes, counting them",
              code_t == 0 and code == 0 and "G4" in bd.get("labels_moved", []) and bd.get("notes_moved") == ["n402"]
              and bd.get("n_labels_moved") == len(bd.get("labels_moved", [])),
              err_t + err3 + json.dumps(bd)[:500])
        # H. a refused take, its dry run too, names the board and what it would change, by kind and key, never a word
        real = gets_mod.structure_changes
        gets_mod.structure_changes = lambda *a, **k: {"labels": ["G2"], "key_quotes": ["G3/T3"]}
        try:
            whole2 = tree2()
            code_h, out_h, err_h = cli.run(["--root", str(root2), "--config", str(cfg), "gets", "take", "T3", "--lpets",
                                            WHO, "--dry-run", "--json"])
            err_h += out_h
        finally:
            gets_mod.structure_changes = real
        pb0 = next(x for x in packed["boards"] if x["id"] == lp["current"])
        moved_card = json.loads(json.dumps(pb0))
        mg1 = next(g for g in moved_card["groups"] if g["id"] == "G1")
        mg2 = next(g for g in moved_card["groups"] if g["id"] == "G2")
        mg2["members"].append(mg1["members"].pop(0))
        unticked = json.loads(json.dumps(pb0))
        unticked["rows"]["G3"] = {"T3": unticked["rows"]["G3"]["T3"]}
        none = {"cards_added": [], "cards_moved": []}
        differs = (gets_mod.structure_changes(pb0, moved_card, "T3", {}, {}, none),
                   gets_mod.structure_changes(pb0, unticked, "T3", {}, {}, none))
        check("402: a refused take, its dry run too, names the board and what differs by kind and key, never a word, "
              "and writes nothing", differs == ({"labels": ["G1", "G2"]}, {"key_quotes": ["G3/T1", "G3/T2"]})
              and code_h != 0 and pb0["id"] in err_h and "G2" in err_h and "G3/T3" in err_h and tree2() == whole2,
              json.dumps(differs) + err_h[:300])
        code, took3, err = run2("gets", "take", "T3", "--lpets", WHO)
        now = json.loads(lp2.read_text(encoding="utf-8"))
        nb = next(x for x in now["boards"] if x["id"] == b["id"])
        pb = next(x for x in packed["boards"] if x["id"] == b["id"])
        free = lambda xs, ids: [{k: v for k, v in x.items() if not (x["id"] in ids and k in ("x", "y"))} for x in xs]  # noqa: E731
        after = boxes(now, nb)
        check("402: the take writes what its dry run said, the LPETs moved down as counted and nothing else of the board "
              "changed, G4 now clear of G1",
              code == 0 and took3.get("counts") == dry3.get("counts")
              and free(pb["groups"], bd["labels_moved"]) == free(nb["groups"], bd["labels_moved"])
              and free(pb["notes"], bd["notes_moved"]) == free(nb["notes"], bd["notes_moved"])
              and sorted(g["id"] for g in nb["groups"] if (g["x"], g["y"]) != next(
                  (p["x"], p["y"]) for p in pb["groups"] if p["id"] == g["id"])) == bd["labels_moved"]
              and all(pb.get(f) == nb.get(f) for f in ("rows", "picks", "discarded", "name"))
              and after["G4"][1] >= after["G1"][1] + after["G1"][3], err + json.dumps(took3.get("counts"))[:400])

        # G. a statement's card stacked, picked and ticked as the key quote whose key changes: at T1 the first of row 15's
        # two statements is taken off, so the second, T1:15:1, comes to stand at T1:15:0
        lp = json.loads(lp2.read_text(encoding="utf-8"))
        b = next(x for x in lp["boards"] if x["id"] == lp.get("current"))
        g1 = next(g for g in b["groups"] if g["id"] == "G1")
        top, under = "T1/es/T1:15:1", "T1/es/T1:3:0"
        x0 = max(b["cards"][k]["x"] for k in g1["members"])
        y0 = max(b["cards"][k]["y"] for k in g1["members"])
        b["cards"][top] = {"x": x0, "y": y0 + 400}
        b["cards"][under] = {"x": x0, "y": y0 + 400}
        g1["members"] += [top, under]
        b["stacks"] = {top: [under]}
        b["picks"] = {"G1": [top]}
        b["rows"]["G1"]["T1"] = dict(b["rows"]["G1"]["T1"], quote="T1:15:1", bold=[[10, 40]])
        lp2.write_text(json.dumps(lp, ensure_ascii=False, indent=1), encoding="utf-8")
        set_up = json.loads(lp2.read_text(encoding="utf-8"))
        sb = next(x for x in set_up["boards"] if x["id"] == b["id"])
        cell = lambda data, board: next(  # noqa: E731
            (r["cells"]["T1"]["quote"] or {}).get("text") for r in gets_mod.lpet_rows(data, board, ["T1"], bare=False)
            if r["id"] == "G1")
        cell_was = cell(set_up, sb)
        code, turn, err = run2("turn", "show", WHO, "T1", "15", note=None)
        t = turn["turns"][0]
        code_w, _x, err_w = run2("turn", "write", WHO, "T1", "15", "--from", spec({
            "version": t["version"], "request": "Take the first off", "remove": [t["pairs"][0]["key"]]}))
        # a write carries its passage's keys into the LPETs' copy itself (lpetdrop, 13 November); one that could not
        # reach it, the file unreadable then, leaves the copy and its boards on the old keys, which the take follows
        lp2.write_text(json.dumps(set_up, ensure_ascii=False, indent=1), encoding="utf-8")
        code, dry1, err1 = run2("gets", "take", "T1", "--lpets", WHO, "--dry-run")
        code_raw, raw1, _x = cli.run(["--root", str(root2), "--config", str(cfg), "gets", "take", "T1", "--lpets", WHO,
                                      "--dry-run", "--json"])
        renamed_raw = [b.get("cards_renamed") for b in (json.loads(raw1).get("counts") or {}).get("boards") or []]
        check("402: the renamed cards' keys, old and new, reach an agent plain, never marked as words",
              code_raw == 0 and [top, "T1/es/T1:15:0"] in [p for r in renamed_raw for p in r or []],
              json.dumps(renamed_raw)[:300])
        code2, took1, err2 = run2("gets", "take", "T1", "--lpets", WHO)
        now = json.loads(lp2.read_text(encoding="utf-8"))
        nb = next(x for x in now["boards"] if x["id"] == b["id"])
        bd = next((x for x in (took1.get("counts") or {}).get("boards") or [] if x["board"] == b["id"]), {})
        moved_to = "T1/es/T1:15:0"
        check("402: a stacked, picked statement card whose key changes keeps its stack, its pick and its key quote with "
              "his bold, the take counting the rename and writing what its dry run said",
              code_w == code == code2 == 0 and dry1.get("counts") == took1.get("counts")
              and [top, moved_to] in bd.get("cards_renamed", [])
              and nb.get("stacks") == {moved_to: [under]} and nb.get("picks") == {"G1": [moved_to]}
              and nb["rows"]["G1"]["T1"].get("quote") == "T1:15:0" and nb["rows"]["G1"]["T1"].get("bold") == [[10, 40]]
              and moved_to in next(g for g in nb["groups"] if g["id"] == "G1")["members"]
              and cell(now, nb) == cell_was and "G1/T1" not in bd.get("cells_changed", []),
              err_w + err1 + err2 + json.dumps(bd)[:500] + json.dumps({k: nb.get(k) for k in ("stacks", "picks")}))
    finally:
        server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO, server_mod.CONFIG_PATH = kept[0], kept[1], kept[3]
        if kept[2] is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = kept[2]
