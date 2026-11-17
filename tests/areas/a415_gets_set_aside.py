"""Area 415: set aside and put back on a GETs, LPETs or LGETs board, and the cards shown twice (lpetsaside, 17 November
2026, found on a participant's LPETs, where statement cards an agent brought in lay loose beside the PETs' cards
that held them, and no agent op took a card off the board).

`gets apply` refused `set_aside` ("a change to a board does not do"), so only the app could tidy them. Now
`{"op": "set_aside", "items": [...]}` and `{"op": "put_back", "items": [...]}` do what X and the Set aside list's
Put back do on those boards, any card by its key, and `gets show` names each statement card whose PET's card is on
the board too under `shown_twice`, by key.

What is checked, on scratch copies of the longitudinal demo (Arlo's LPETs and the LGETs) and of the demo (the
GETs): no card is shown twice to start; a statement brought in beside its PET's card is found by the read, by key;
its set aside's dry run says it by key and writes nothing; the set aside takes it off the canvas into Set aside, one
line in the record, the read no longer naming it, and its undo puts every file back byte for byte; put back's dry
run writes nothing and the put back stands it in no label, clear of everything, its undo byte for byte; a card the
board has not got, a label, one set aside twice and one put back that is not are refused in one line with nothing
written, dry run or not; another agent's run of a set aside and a put back is undone byte for byte by the run's
undo; and on the LGETs and the GETs a statement brought in beside its PET's card is found, set aside and undone
the same way."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from .support import check
from . import support

ASKED = "Take the duplicate card off the board"


def digest(root: Path) -> dict:
    """Every file of the project by its contents, the lock files, the record and restore points of agents' changes,
    the archive copies set aside and the History chunks a write superseded left out (no part of any History, see
    `board_history.SUPERSEDED`)."""
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


def test_gets_set_aside(scratch: Path):
    print("\n415. Set aside and put back on the LPETs, LGETs and GETs boards, and the cards shown twice: the read, the "
          "dry runs, the refusals and the undo (lpetsaside, 17 November)")
    import agent_changes
    import agent_log
    import cli
    import os
    import server as server_mod

    base = scratch / "gets-aside-415"
    shutil.rmtree(base, ignore_errors=True)
    lroot = base / "Allotment"
    (lroot / "Arlo" / "Working").mkdir(parents=True)
    lipa = support.source("demo/lipa")
    held = json.loads((lipa / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
    held["agents"] = {"allowed": True, "at": "2026-11-17T09:00:00+00:00"}
    (lroot / server_mod.PROJECT_FILE).write_text(json.dumps(held), encoding="utf-8")
    shutil.copy2(lipa / "pristine" / "Arlo - EN & ES.xlsx", lroot / "Arlo" / "Arlo - EN & ES.xlsx")
    for one in sorted((lipa / "pristine" / "Working").glob("Arlo - EN & ES.*")):
        shutil.copy2(one, lroot / "Arlo" / "Working" / one.name)
    shutil.copy2(lipa / "pristine" / "idiograph-lgets.json", lroot / "idiograph-lgets.json")

    groot = base / "Dogs"
    demo = support.source("demo")
    held = json.loads((demo / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
    held["agents"] = {"allowed": True, "at": "2026-11-17T09:00:00+00:00"}
    groot.mkdir(parents=True)
    (groot / server_mod.PROJECT_FILE).write_text(json.dumps(held), encoding="utf-8")
    for name in ("Juno", "Mabel", "Rowan"):
        (groot / name / "Working").mkdir(parents=True)
        shutil.copy2(demo / "pristine" / f"{name} - EN & ES.xlsx", groot / name / f"{name} - EN & ES.xlsx")
        for one in sorted((demo / "pristine" / "Working").glob(f"{name} - EN & ES.*")):
            shutil.copy2(one, groot / name / "Working" / one.name)
    shutil.copy2(demo / "pristine" / "idiograph-gets.json", groot / "idiograph-gets.json")

    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(lroot)}, {"root": str(groot)}], "interviewer": "Adam",
                                       "corpus": "", "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    log = base / "agent-log.json"
    kept = (agent_changes.ALL_OPS, os.environ.get(agent_log.PLACE))
    agent_changes.ALL_OPS = None
    os.environ[agent_log.PLACE] = str(log)

    def run(root, *args, tool="Claude Code"):
        given = ["--config", str(config_file), "--root", str(root), "--json", *args]
        if tool is not None:
            given += ["--tool", tool]
        code, out, err = cli.run(given)
        return code, (support.plain(json.loads(out)) if out.strip() else {}), err + (out if code else "")

    def ops_file(name, operations):
        path = base / f"{name}.json"
        path.write_text(json.dumps({"operations": operations}), encoding="utf-8")
        return str(path)

    def lpets_board() -> dict:
        data = json.loads((lroot / "Arlo" / "Working" / "Arlo - EN & ES.lpets.json").read_text(encoding="utf-8"))
        return next(b for b in data["boards"] if b["id"] == "b1")

    try:
        lp = ("--lpets", "Arlo")
        dup = "T3/es/T3:29:0"
        code, shown, err = run(lroot, "gets", "show", *lp, tool=None)
        check("415: before anything, Arlo's LPETs show no card twice, and the read says so by count",
              code == 0 and shown.get("shown_twice") == [] and shown.get("n_shown_twice") == 0, err[:300])

        # ── 1. a duplicate made: the statement brought in beside the PET's card that holds it
        code, done, err = run(lroot, "gets", "apply", "b1", *lp, "--ops",
                              ops_file("bring", [{"op": "bring_in", "statement": dup}]), "--note", "Bring it in")
        code_s, shown, err_s = run(lroot, "gets", "show", *lp, tool=None)
        check("415: the read finds the statement brought in beside its PET's card, by key alone, in no LPET",
              code == 0 and code_s == 0 and shown.get("shown_twice") == [
                  {"card": dup, "case": "T3", "also": ["T3/g3"], "label": None}] and shown.get("n_shown_twice") == 1,
              err[:300] + err_s[:300] + json.dumps(shown.get("shown_twice")))
        check("415: the read's lines name keys alone, never a statement's words",
              all("T3:29:0" in x and "'" not in x for x in [json.dumps(shown.get("shown_twice"))]), "")
        start = digest(lroot)
        records = len(agent_changes.read(lroot))

        # ── 2. set aside: the dry run, the change, the record, the read, the undo
        aside = ops_file("aside", [{"op": "set_aside", "items": [dup]}])
        code, dry, err = run(lroot, "gets", "apply", "b1", *lp, "--ops", aside, "--dry-run", tool=None)
        check("415: set aside's dry run names the card by key, counts it, and writes nothing",
              code == 0 and dry.get("set_aside") == [dup] and dry.get("n_set_aside") == 1 and digest(lroot) == start
              and len(agent_changes.read(lroot)) == records, err[:300] + json.dumps(dry)[:300])
        code, done, err = run(lroot, "gets", "apply", "b1", *lp, "--ops", aside, "--note", ASKED)
        board = lpets_board()
        code_s, shown, _e = run(lroot, "gets", "show", *lp, tool=None)
        lines = agent_changes.read(lroot)
        check("415: set aside takes the card out of every LPET into Set aside, its place on the board kept, and the read "
              "no longer names it",
              code == 0 and dup in board["discarded"] and dup in board["cards"]
              and not any(dup in g["members"] for g in board["groups"]) and shown.get("shown_twice") == [],
              err[:300] + json.dumps(done)[:300])
        check("415: the set aside is one line in the record of agents' changes",
              len(lines) == records + 1 and lines[-1].get("op") == "gets apply", json.dumps(lines[-1:])[:300])
        code_u, _x, err_u = run(lroot, "agents", "undo-change", lines[-1]["id"], "--note", "Put it back")
        check("415: the set aside's undo puts every file back byte for byte",
              code_u == 0 and digest(lroot) == start, err_u[:300] + str(changed(start, digest(lroot))))

        # ── 3. put back: set aside again, then the dry run, the change and its undo
        run(lroot, "gets", "apply", "b1", *lp, "--ops", aside, "--note", ASKED)
        set_off = digest(lroot)
        records = len(agent_changes.read(lroot))
        back = ops_file("back", [{"op": "put_back", "items": [dup]}])
        code, dry, err = run(lroot, "gets", "apply", "b1", *lp, "--ops", back, "--dry-run", tool=None)
        check("415: put back's dry run names the card by key and writes nothing",
              code == 0 and dry.get("put_back") == [dup] and dry.get("n_put_back") == 1 and digest(lroot) == set_off
              and len(agent_changes.read(lroot)) == records, err[:300] + json.dumps(dry)[:300])
        code, done, err = run(lroot, "gets", "apply", "b1", *lp, "--ops", back, "--note", "Put it back on the board")
        board = lpets_board()
        import gets as gets_mod
        import themes
        drawn = themes.layout_boxes(dict(board, cards={k: dict(c, text=c.get("text") or "x") for k, c in board["cards"].items()}),
                                    gets_mod.card_height)
        mine = drawn["cards"].get(dup)

        def meets(a, b):
            return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]
        others = [v for k, v in drawn["cards"].items() if k != dup] + list(drawn["frames"].values()) \
            + list(drawn["labels"].values())
        check("415: put back stands the card on the board in no LPET, clear of every card and frame there, and the "
              "read finds it again",
              code == 0 and dup not in board["discarded"] and not any(dup in g["members"] for g in board["groups"])
              and mine is not None and not any(meets(mine, o) for o in others)
              and len(run(lroot, "gets", "show", *lp, tool=None)[1].get("shown_twice") or []) == 1,
              err[:300] + json.dumps(done)[:300])
        lines = agent_changes.read(lroot)
        code_u, _x, err_u = run(lroot, "agents", "undo-change", lines[-1]["id"], "--note", "Set it aside again")
        check("415: the put back's undo puts every file back byte for byte",
              code_u == 0 and digest(lroot) == set_off, err_u[:300] + str(changed(set_off, digest(lroot))))

        # ── 4. refusals, one line each, nothing written, the dry run too
        records = len(agent_changes.read(lroot))
        cases = [("a key the board has not got", [{"op": "set_aside", "items": ["T3/es/T3:999:0"]}], "T3/es/T3:999:0"),
                 ("a label", [{"op": "set_aside", "items": ["G1"]}], "G1"),
                 ("a card set aside already", [{"op": "set_aside", "items": [dup]}], "set aside already"),
                 ("a card put back that is not set aside", [{"op": "put_back", "items": ["T3/g3"]}], "not set aside"),
                 ("an operation naming no card", [{"op": "set_aside"}], "names no cards")]
        for what, operations, said in cases:
            spec = ops_file("refused", operations)
            outs = [run(lroot, "gets", "apply", "b1", *lp, "--ops", spec, "--dry-run", tool=None),
                    run(lroot, "gets", "apply", "b1", *lp, "--ops", spec, "--note", ASKED)]
            check(f"415: {what} is refused in one line, the dry run too, with nothing written",
                  all(c != 0 and said in e and "Operation 1" in e for c, _d, e in outs) and digest(lroot) == set_off
                  and len(agent_changes.read(lroot)) == records,
                  " | ".join(e[:200] for _c, _d, e in outs))

        # ── 5. another agent's run, put back and set aside again with an old name, undone whole
        here = digest(lroot)
        steps = [run(lroot, "gets", "apply", "b1", *lp, "--ops", back, "--note", ASKED, tool="Tidy agent"),
                 run(lroot, "gets", "apply", "b1", *lp, "--ops", ops_file("bin", [{"op": "discard", "items": [dup]}]),
                     "--note", ASKED, tool="Tidy agent")]
        rid = agent_changes.read(lroot)[-1]["run"]
        code_u, _x, err_u = run(lroot, "agents", "undo-run", rid, "--note", "Put it all back")
        check("415: another agent's put back and set aside (by the bin's old name) run, and the run's undo puts every "
              "file back byte for byte",
              all(c == 0 for c, _d, _e in steps) and code_u == 0 and digest(lroot) == here,
              " ".join(e[:200] for _c, _d, e in steps) + err_u[:300] + str(changed(here, digest(lroot))))

        # ── 6. the LGETs and the GETs alike
        for label, root, extra, case in (("LGETs", lroot, (), "Arlo"), ("GETs", groot, (), "Juno")):
            name = "idiograph-lgets.json" if label == "LGETs" else "idiograph-gets.json"
            data = json.loads((root / name).read_text(encoding="utf-8"))
            board = next(b for b in data["boards"] if b["id"] == "b1")
            pet = next(p for p in data["cases"][case]["pets"]
                       if p.get("statements") and f"{case}/{p['id']}" in board["cards"]
                       and f"{case}/{p['id']}" not in board["discarded"])
            key = f"{case}/es/{pet['statements'][0]}"
            code, done, err = run(root, "gets", "apply", "b1", *extra, "--ops",
                                  ops_file("bring2", [{"op": "bring_in", "statement": key}]), "--note", "Bring it in")
            code_s, shown, err_s = run(root, "gets", "show", *extra, tool=None)
            check(f"415: on the {label} the read finds a statement brought in beside its PET's card, by key",
                  code == 0 and [x["card"] for x in shown.get("shown_twice") or []] == [key]
                  and shown["shown_twice"][0]["also"] == [f"{case}/{pet['id']}"], err[:300] + err_s[:300])
            before = digest(root)
            spec = ops_file("aside2", [{"op": "set_aside", "items": [key]}])
            code, dry, err = run(root, "gets", "apply", "b1", *extra, "--ops", spec, "--dry-run", tool=None)
            ok_dry = code == 0 and dry.get("set_aside") == [key] and digest(root) == before
            code, done, err2 = run(root, "gets", "apply", "b1", *extra, "--ops", spec, "--note", ASKED)
            after = json.loads((root / name).read_text(encoding="utf-8"))
            now = next(b for b in after["boards"] if b["id"] == "b1")
            ok = code == 0 and key in now["discarded"] and run(root, "gets", "show", *extra, tool=None)[1].get("shown_twice") == []
            line = agent_changes.read(root)[-1]
            code_u, _x, err_u = run(root, "agents", "undo-change", line["id"], "--note", "Put it back")
            check(f"415: on the {label} set aside's dry run writes nothing, the set aside takes the card into Set aside, "
                  "and its undo puts every file back byte for byte",
                  ok_dry and ok and code_u == 0 and digest(root) == before,
                  err[:200] + err2[:200] + err_u[:200] + str(changed(before, digest(root))))
    finally:
        agent_changes.ALL_OPS = kept[0]
        if kept[1] is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = kept[1]
        agent_log.flush()
