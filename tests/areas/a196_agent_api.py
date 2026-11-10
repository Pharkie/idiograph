from __future__ import annotations

import json
import shutil

from . import support
from .support import check


def test_agent_api(scratch):
    print("\n196. Agent access, the first five gaps: an order at every level on a board as it is, a note taken off, "
          "the board menu's acts, picks that no longer fit dropped and each label's export label")
    import cli
    import mcp_server
    import server as server_mod
    import themes

    pristine = support.DEMO_PRISTINE
    root = scratch / "agent-api-root"
    shutil.rmtree(root, ignore_errors=True)
    for name in ("Juno", "Rowan", "Mabel"):
        case = root / name
        (case / "Working").mkdir(parents=True)
        shutil.copy2(pristine / f"{name} - EN & ES.xlsx", case / f"{name} - EN & ES.xlsx")
        for side in (pristine / "Working").glob(f"{name} - *"):
            shutil.copy2(side, case / "Working" / side.name)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Dogs, a scratch project", "agents": {"allowed": True, "at": "2026-10-19T10:00:00+01:00"}}), encoding="utf-8")
    config_file = scratch / "agent-api-config.json"
    config_file.write_text(json.dumps({"root": str(root), "interviewer": "Adam"}), encoding="utf-8")
    book = root / "Rowan" / "Rowan - EN & ES.xlsx"
    themes_file = themes.themes_path(book)

    def run(*args):
        return cli.run(["--root", str(root), "--config", str(config_file), *args])

    def answer(*args):
        code, out, err = run(*args, "--json")
        return code, (support.plain(json.loads(out)) if out.strip() else {}), err

    def ops(*operations) -> str:
        path = scratch / "agent-api-ops.json"
        path.write_text(json.dumps({"operations": list(operations)}), encoding="utf-8")
        return str(path)

    def saved() -> dict:
        return json.loads(themes_file.read_text(encoding="utf-8"))

    def board(vid="v1") -> dict:
        return next(b for b in saved()["boards"] if b["id"] == vid)

    def shown(name="Board 1", *more) -> dict:
        return answer("board", "show", "Rowan", name, *more)[1]

    def orders(view: dict) -> dict:
        """Each label's order as the outline reads it, and the PETs' under None."""
        out = {None: [t["id"] for t in view["themes"]]}

        def walk(t):
            out[t["id"]] = list(t["order"])
            for x in t["themes"]:
                walk(x)
        for t in view["themes"]:
            walk(t)
        return out

    def overlaps(b: dict) -> int:
        """Siblings that overlap on the board, PETs among PETs and members inside each label."""
        v = themes.normalise(b)
        d = themes.layout_boxes(v)
        by_id = {g["id"]: g for g in v["groups"]}
        parents = themes.parents_of(v["groups"])
        n = 0
        for members in [[g for g in by_id if g not in parents]] + [g["members"] for g in v["groups"]]:
            boxes = [d["frames"][m] if m in by_id else d["cards"].get(m) for m in members]
            boxes = [x for x in boxes if x]
            n += sum(1 for i, a in enumerate(boxes) for c in boxes[i + 1:] if themes.clash(a, c))
        return n

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        before = orders(shown())
        pets = before[None]
        history = len(board().get("history") or [])
        start_overlaps = overlaps(board())

        # ── A. the PETs set in a new order on the board as it is
        wanted = list(reversed(pets))
        raw = themes_file.read_bytes()
        code, dry, _ = answer("board", "apply", "Rowan", "v1", "--ops", ops({"op": "order", "under": None, "items": wanted}),
                              "--note", "Most compelling first", "--dry-run")
        check("196: an order's dry run says the order it would set and writes nothing",
              code == 0 and dry.get("dry_run") is True and themes_file.read_bytes() == raw
              and "would have: set the PETs in the order" in dry["said"]
              and dry["ordered"][0]["order"] == wanted, dry.get("said", "")[:200])
        code, out, err = run("board", "apply", "Rowan", "v1", "--ops", ops({"op": "order", "under": None, "items": wanted}),
                             "--note", "Most compelling first", "--tool", "Claude Code")
        after = orders(shown())
        check("196: the PETs read back in the order asked, on the same board, each PET holding what it held",
              code == 0 and after[None] == wanted and all(after[g] == before[g] for g in before if g is not None)
              and [b["id"] for b in saved()["boards"]] == ["v1"], err or out[:200])
        check("196: the order is one step in the board's History, named for his request, and nothing comes to overlap",
              len(board().get("history") or []) == history + 1
              and board()["history"][-1]["name"] == "Before: Most compelling first"
              and overlaps(board()) <= start_overlaps)
        code, out, _ = run("board", "apply", "Rowan", "v1", "--ops", ops({"op": "order", "under": None, "items": wanted}),
                           "--note", "Again")
        check("196: the order it already reads in writes nothing", code == 0 and "Nothing to change" in out
              and len(board().get("history") or []) == history + 1)

        # ── B. inside a PET: its statements and its sub-theme, a few named first and the rest after them
        pet = next(g for g in before if g is not None and any(m.startswith("g") for m in before[g]))
        sub = next(m for m in before[pet] if m.startswith("g"))
        cards = [m for m in before[pet] if not m.startswith("g")]
        sids = shown()["themes"]
        sid = {s["key"]: s["id"] for t in sids for s in t["statements"]}
        first = [sub, sid[cards[-1]]]
        code, data, err = answer("board", "apply", "Rowan", "v1", "--ops", ops({"op": "order", "under": pet, "items": first}),
                                 "--note", "Sub-theme first")
        inner = orders(shown())
        check("196: inside a PET the sub-theme and a statement named come first, the rest after them as they read",
              code == 0 and inner[pet] == [sub, cards[-1]] + cards[:-1] and inner[None] == wanted
              and overlaps(board()) <= start_overlaps, err or json.dumps(data.get("ordered"))[:200])

        # ── C. inside a sub-theme, cards alike in size, each in the place of the one before
        held = inner[sub]
        spots = {k: (board()["cards"][k]["x"], board()["cards"][k]["y"]) for k in held}
        turned = list(reversed(held))
        code, data, err = answer("board", "apply", "Rowan", "v1",
                                 "--ops", ops({"op": "order", "under": sub, "items": [sid.get(k, k) for k in turned]}),
                                 "--note", "Best statement first")
        now = {k: (board()["cards"][k]["x"], board()["cards"][k]["y"]) for k in held}
        check("196: inside a sub-theme each statement takes the place of the one that read at its turn before",
              code == 0 and orders(shown())[sub] == turned
              and sorted(now.values()) == sorted(spots.values()) and data["ordered"][0]["how"] in ("kept", "room"),
              err or json.dumps(data.get("ordered"))[:200])

        # ── D. refusals, each one line, nothing written
        raw = themes_file.read_bytes()
        stranger = next(k for g in before if g not in (None, pet, sub) for k in before[g] if not k.startswith("g"))
        code, out, err = run("board", "apply", "Rowan", "v1",
                             "--ops", ops({"op": "order", "under": sub, "items": [sid.get(stranger, stranger)]}), "--note", "x")
        code2, _, err2 = run("board", "apply", "Rowan", "v1", "--ops", ops({"op": "order", "under": "g99", "items": ["S1"]}),
                             "--note", "x")
        code3, _, err3 = run("board", "apply", "Rowan", "v1", "--ops", ops({"op": "order", "under": None, "items": []}),
                             "--note", "x")
        check("196: an order naming something not directly in the label, a label not on the board or nothing is refused",
              code == 1 and "which is not directly under" in err and err.strip().endswith("Nothing was written.")
              and code2 == 1 and "not a label on the board" in err2 and code3 == 1 and "no items" in err3
              and themes_file.read_bytes() == raw, err + err2 + err3)

        # ── E. an order beside the other operations, naming a label a make made by its ref
        code, data, err = answer("board", "apply", "Rowan", "v1", "--ops", ops(
            {"op": "make", "ref": "new1", "title": "Two walks a day, whatever the weather", "inside": None,
             "members": [sid.get(cards[0], cards[0])]},
            {"op": "order", "under": None, "items": ["new1"]}), "--note", "A new PET, first")
        made = (data.get("made") or [None])[0]
        check("196: an order runs after a make, naming its label by its ref, all in one History step",
              code == 0 and made and orders(shown())[None][0] == made
              and board()["history"][-1]["name"] == "Before: A new PET, first", err[:200])

        # ── F. a label's note taken off
        noted = next(g["id"] for g in board()["groups"] if g.get("note"))
        raw = themes_file.read_bytes()
        code, _, _ = run("board", "apply", "Rowan", "v1", "--ops", ops({"op": "note", "label": noted, "note": ""}),
                         "--note", "Take the note off", "--dry-run")
        dry_kept = themes_file.read_bytes() == raw
        code2, out, err = run("board", "apply", "Rowan", "v1", "--ops", ops({"op": "note", "label": noted, "note": ""}),
                              "--note", "Take the note off")
        gone = next(g for g in board()["groups"] if g["id"] == noted)
        code3, _, err3 = run("board", "apply", "Rowan", "v1", "--ops", ops({"op": "note", "label": noted}), "--note", "x")
        check("196: a note given empty takes the label's note off, its dry run writing nothing, a note left out still refused",
              code == 0 and dry_kept and code2 == 0 and "note" not in gone and "took the note off" in out.lower()
              and board()["history"][-1]["name"] == "Before: Take the note off" and code3 == 1, err or err3)

        # ── G. the board menu's acts
        raw = themes_file.read_bytes()
        dries = [run("board", act, "Rowan", "Board 1", *extra, "--note", "x", "--dry-run")
                 for act, extra in (("duplicate", ()), ("rename", ("Ordered",)), ("canvas", ()))]
        check("196: duplicate, rename and canvas each have a dry run that writes nothing",
              all(c == 0 and "Dry run" in o for c, o, _ in dries[:2]) and themes_file.read_bytes() == raw,
              " ".join(e for _, _, e in dries))
        code, data, err = answer("board", "duplicate", "Rowan", "Board 1", "--name", "Board 1 trial",
                                 "--note", "Try a copy", "--tool", "Claude Code")
        copy = next((b for b in saved()["boards"] if b["name"] == "Board 1 trial"), {})
        check("196: duplicate copies the board under its name, puts it on the canvas and says who made it, the board copied as it was",
              code == 0 and copy and saved()["current"] == copy["id"] and "Claude Code" in copy["note"]
              and "Try a copy" in copy["note"] and not copy.get("history")
              and copy["groups"] == board()["groups"], err)
        code, _, err = run("board", "canvas", "Rowan", "Board 1", "--note", "Back to the first")
        check("196: canvas puts a board on the canvas and nothing else changes",
              code == 0 and saved()["current"] == "v1" and len(saved()["boards"]) == 2, err)
        code, _, err = run("board", "rename", "Rowan", "Board 1 trial", "Trial order", "--note", "Name it")
        named = next((b for b in saved()["boards"] if b["id"] == copy["id"]), {})
        code2, _, err2 = run("board", "rename", "Rowan", "Trial order", "Board 1", "--note", "Name it")
        check("196: rename renames it and keeps it first in its History, a name another board has refused",
              code == 0 and named.get("name") == "Trial order" and named["history"][-1]["name"].startswith("Renamed from Board 1 trial")
              and code2 == 1 and "Another board is called Board 1" in err2, err + err2)
        code, data, err = answer("board", "delete", "Rowan", "Trial order", "--note", "Drop the trial")
        archived = root / "Rowan" / "_Archive" / data.get("backup", "-")
        code2, _, err2 = run("board", "delete", "Rowan", "Board 1", "--note", "Drop it")
        check("196: delete takes the board out after a copy of it whole for this participant's _Archive, and the last board is refused",
              code == 0 and [b["id"] for b in saved()["boards"]] == ["v1"] and archived.is_file()
              and json.loads(archived.read_text(encoding="utf-8"))["id"] == copy["id"]
              and code2 == 1 and "last board" in err2, err + err2)
        code, _, err = run("board", "rename", "Rowan", "Board 1", "Ordered")
        check("196: a housekeeping write needs his request", code == 1 and "--note" in err, err)

        # ── H. board new drops a pick whose statement is not under its label, in one line
        keys = [s["key"] for t in shown()["themes"] for s in t["statements"] if s.get("quote")]
        spec = scratch / "agent-api-new.json"
        spec.write_text(json.dumps({"pets": [{"title": "The lead by the door", "members": [keys[0]],
                                               "picks": [keys[0], keys[1]]}]}), encoding="utf-8")
        code, data, err = answer("board", "new", "Rowan", "--from", str(spec), "--note", "One PET")
        newest = next((b for b in saved()["boards"] if b["id"] == data.get("id")), {})
        picked = [k for ks in (newest.get("picks") or {}).values() for k in ks]
        check("196: board new makes the board, drops the pick that does not fit and says so in one line",
              code == 0 and data.get("dropped_picks") == [{"key": keys[1], "label": "'The lead by the door'"}]
              and data["said"].count("It dropped 1 pick") == 1 and picked == [keys[0]], err or data.get("said", ""))

        # ── I. each label's export label in the JSON, as the exports give it
        view = shown()
        numbers = themes.pet_numbers(themes.outline(themes.read_cards(book), themes.find_version(saved(), "v1"))["themes"])
        labelled = {t["id"]: t["export_label"] for t in view["themes"]}
        labelled.update({s["id"]: s["export_label"] for t in view["themes"] for s in t["themes"]})
        as_numbers = shown("Board 1", "--labels", "numbers")
        check("196: board show --json gives every label the export label the PDF prints, letters or numbers",
              labelled and all(labelled[g] == numbers[g] for g in labelled)
              and [t["export_label"] for t in view["themes"]][:2] == ["A", "B"]
              and as_numbers["themes"][0]["export_label"] == "PET 1"
              and all(s["export_label"].startswith("PET 1") for s in as_numbers["themes"][0]["themes"]), json.dumps(labelled)[:200])

        # ── J. the same through MCP
        srv = mcp_server.Server(str(root), config=str(config_file))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))

        def call(name, **given):
            return srv.receive(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                           "params": {"name": name, "arguments": given}}))["result"]
        pets_now = orders(shown())[None]
        raw = themes_file.read_bytes()
        res = call("board_apply", case="Rowan", board="Board 1", request="Swap the first two", dry_run=True,
                   operations=[{"op": "order", "under": None, "items": [pets_now[1], pets_now[0]]}])
        res2 = call("board_canvas", case="Rowan", board="Board 1", request="Show it", dry_run=True)
        res3 = call("board_apply", case="Rowan", board="Board 1", request="Swap the first two",
                    operations=[{"op": "order", "under": None, "items": [pets_now[1], pets_now[0]]}])
        check("196: through MCP an order and the board menu's acts run as on the command line, the dry runs writing nothing",
              not res["isError"] and support.plain(res["structuredContent"])["dry_run"] is True and not res2["isError"]
              and not res3["isError"] and orders(shown())[None][:2] == [pets_now[1], pets_now[0]]
              and board()["changed"]["tool"] == "Claude Code" and raw != themes_file.read_bytes(),
              json.dumps(res3)[:300])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
