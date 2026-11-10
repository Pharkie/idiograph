"""Area 249: a GETs card that grows through a take makes room below it (22 October 2026). A PET that gained a
description, or a title a line longer, came in through gets take at its new height with every card round it left
where it was, so it ran over the card below it in its GET or in the pile until Arrange. The take now moves what a
grown card meets below it straight down, just far enough to keep the margin, and on in turn, and a GET whose
frame so grew pushes what lies below it the same way.

The checks build the GETs on the demo's invented participants, one board with Rowan's cards in a GET and Mabel's
in the pile, another with every card in the pile, write a made-up description on each of Rowan's PETs and
sub-PETs, take Rowan's changes, and read the saved file: no two neighbours nearer than the margin, nothing moved
sideways or up, and a take that changes no card's height moves nothing.
"""
from __future__ import annotations

import json
import shutil
from itertools import combinations

from . import support
from .support import check

SAID = "Walks at dawn and at dusk that set the shape of every day, whatever the weather"


def test_take_makes_room(scratch):
    print("\n249. A GETs card that grows through a take makes room below it, in a GET and in the pile (22 October)")
    import cli
    import gets as gets_mod
    import themes

    pristine = support.DEMO_PRISTINE
    root = scratch / "take-room-249-root"
    shutil.rmtree(root, ignore_errors=True)
    for name in ("Juno", "Rowan", "Mabel"):
        case = root / name
        (case / "Working").mkdir(parents=True)
        shutil.copy2(pristine / f"{name} - EN & ES.xlsx", case / f"{name} - EN & ES.xlsx")
        for side in (pristine / "Working").glob(f"{name} - *"):
            shutil.copy2(side, case / "Working" / side.name)
    (root / "idiograph-project.json").write_text(json.dumps({
        "name": "Dogs, a scratch project", "agents": {"allowed": True, "at": "2026-10-22T10:00:00+01:00"}}), encoding="utf-8")
    config_file = scratch / "take-room-249-config.json"
    config_file.write_text(json.dumps({"root": str(root), "interviewer": "Adam"}), encoding="utf-8")
    books = [{"case": n, "workbook": str(root / n / f"{n} - EN & ES.xlsx")} for n in ("Juno", "Rowan", "Mabel")]
    book = root / "Rowan" / "Rowan - EN & ES.xlsx"
    n_ops = [0]

    def answer(*args):
        code, out, err = cli.run(["--root", str(root), "--config", str(config_file), *args, "--json"])
        return code, (json.loads(out) if out.strip() else {}), err

    def ops(*operations) -> str:
        n_ops[0] += 1
        path = scratch / f"take-room-249-ops-{n_ops[0]}.json"
        path.write_text(json.dumps({"operations": list(operations)}), encoding="utf-8")
        return str(path)

    data, _, _, _ = gets_mod.assemble(root, books, themes.now_iso())
    gets_mod.write(root, gets_mod._file(data, themes.now_iso()))
    gfile = gets_mod.gets_path(root)
    gets_mod.version_op(root, books, "new", {"name": "All in the pile"})
    code, shown, err = answer("gets", "apply", "b1", "--ops", ops(
        {"op": "make", "ref": "a", "title": "Days given their shape", "inside": None,
         "members": [k for k in json.loads(gfile.read_text(encoding="utf-8"))["boards"][0]["cards"] if k.startswith("Rowan/")]}),
        "--note", "One GET")
    check("249: a GET made of Rowan's cards, and a second board with every card in the pile",
          code == 0 and len(json.loads(gfile.read_text(encoding="utf-8"))["boards"]) == 2, err)

    def clashes(board: dict, file: dict) -> list:
        shown = themes.normalise(gets_mod.named(board, file))
        drawn = themes.layout_boxes(shown, gets_mod.card_height)
        boxes = themes._solid_boxes(shown, drawn)
        gone = themes.off_canvas(shown)
        parents = themes.parents_of(shown["groups"])
        return [(a, b) for a, b in combinations(sorted(boxes), 2) if a not in gone and b not in gone
                and parents.get(a) == parents.get(b) and themes.clash(boxes[a], boxes[b], themes.MARGIN - 1)]

    before = json.loads(gfile.read_text(encoding="utf-8"))
    check("249: no card nearer its neighbour than the margin before the take",
          all(not clashes(b, before) for b in before["boards"]), str([clashes(b, before) for b in before["boards"]]))

    board = json.loads(themes.themes_path(book).read_text(encoding="utf-8"))["boards"][0]
    labels = [g["id"] for g in board["groups"]]
    code, _, err = answer("board", "apply", "Rowan", "v1", "--ops", ops(
        *[{"op": "describe", "label": gid, "description": SAID} for gid in labels]), "--note", "Describe", "--tool", "Claude Code")
    code_t, _, err_t = answer("gets", "take", "Rowan", "--note", "Take the descriptions")
    after = json.loads(gfile.read_text(encoding="utf-8"))
    check("249: after a take that brings a description to each of Rowan's PETs, no two cards on either board "
          "are nearer than the margin, in the GET or in the pile",
          code == 0 and code_t == 0 and all(not clashes(b, after) for b in after["boards"]),
          err + err_t + str([clashes(b, after) for b in after["boards"]]))
    spots = lambda f: {(b["id"], k): (c["x"], c["y"]) for b in f["boards"] for k, c in b["cards"].items()}
    was, now = spots(before), spots(after)
    moved = [k for k in was if now.get(k) != was[k]]
    check("249: what made room moved straight down, never sideways or up, and some cards did move",
          moved and all(now[k][0] == was[k][0] and now[k][1] > was[k][1] for k in moved), str(moved[:6]))

    code, _, err = answer("board", "apply", "Rowan", "v1", "--ops", ops(
        {"op": "note", "label": labels[0], "note": "A note the GETs cards do not show."}), "--note", "A note", "--tool", "Claude Code")
    code_t, _, err_t = answer("gets", "take", "Rowan", "--note", "Take the note")
    again = json.loads(gfile.read_text(encoding="utf-8"))
    check("249: a take that changes no card's height moves nothing", code_t == 0 and spots(again) == now, err + err_t)
