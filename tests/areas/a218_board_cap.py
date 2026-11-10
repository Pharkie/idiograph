from __future__ import annotations

import json
import shutil

from . import support
from .support import check
import idiograph_routes


def test_board_cap(scratch):
    print("\n218. The most PETs an AI board proposes limits the AI's boards alone (20 October, an agent's board of four "
          "warned past a cap of three): board new makes every PET a structure gives and never names a cap, and cases "
          "reads the AI's limit from the settings file the app reads")
    import cli
    import server as server_mod
    import themes as themes_mod

    root = scratch / "a218-root"
    shutil.rmtree(root, ignore_errors=True)
    pristine = support.DEMO_PRISTINE
    (root / "Rowan" / "Working").mkdir(parents=True)
    book = root / "Rowan" / "Rowan - EN & ES.xlsx"
    shutil.copy2(pristine / "Rowan - EN & ES.xlsx", book)
    for side in (pristine / "Working").glob("Rowan - *"):
        shutil.copy2(side, root / "Rowan" / "Working" / side.name)
    (root / "idiograph-project.json").write_text(json.dumps({"name": "Dogs, a scratch project",
                                                             "agents": {"allowed": True, "at": "2026-10-20T09:00:00"}}),
                                                 encoding="utf-8")
    config = scratch / "a218-config.json"

    def settings(cap):
        config.write_text(json.dumps({"root": str(root), "interviewer": "Adam", "corpus": "", "gravity_reference": "",
                                      "corpus_exclude": [], "themes": {"cap": cap}}), encoding="utf-8")

    def run(*words):
        return cli.run(["--root", str(root), "--config", str(config), *words])

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        settings(3)
        plan = {"pets": [{"title": "Walks at first light", "members": ["S1", "S2", "S3"]},
                         {"title": "A dog that sets the hours", "members": ["S4", "S5", "S6"]},
                         {"title": "The park as a second home", "members": ["S7", "S8", "S9"]},
                         {"title": "Company on the bad days", "members": ["S10", "S11", "S12"]}]}
        source = scratch / "a218-plan.json"
        source.write_text(json.dumps(plan), encoding="utf-8")
        before = book.read_bytes()
        code, dry, err = run("board", "new", "Rowan", "--from", str(source), "--dry-run")
        check("218: a dry run of a board of four PETs, with the AI's limit at three, says four and names no cap",
              code == 0 and "4 PETs" in dry and "cap" not in dry.lower() and "past" not in dry, f"{code} {err[:200]} {dry[:300]}")
        code, made, err = run("board", "new", "Rowan", "--from", str(source), "--note", "Make a board of my four PETs",
                              "--tool", "Claude Code")
        stored = json.loads(themes_mod.themes_path(book).read_text(encoding="utf-8"))
        board = stored["boards"][-1]
        parents = themes_mod.parents_of(board["groups"])
        tops = [g["label"] for g in board["groups"] if g["id"] not in parents]
        check("218: board new writes all four PETs, the board made current, and its answer names no cap",
              code == 0 and sorted(tops) == sorted(p["title"] for p in plan["pets"]) and stored["current"] == board["id"]
              and "cap" not in made.lower() and "past" not in made and book.read_bytes() == before,
              f"{code} {err[:200]} {tops} {made[:300]}")

        code, text, err = run("cases")
        code_json, data, _ = run("cases", "--json")
        data = json.loads(data)
        check("218: cases names no limit on a new board, and its JSON carries the AI's limit from the settings file, 3",
              code == 0 and "PETs" not in text.split("Rowan:", 1)[0] and "cap" not in text.lower()
              and data["project"]["ai_board_most_pets"] == 3 and "pet_cap" not in data["project"], text[:300])
        settings(7)
        code_json, data, _ = run("cases", "--json")
        check("218: a limit Settings saves, 7, is the one cases reads next",
              code_json == 0 and json.loads(data)["project"]["ai_board_most_pets"] == 7)
        guide = idiograph_routes.agents_project(root)
        check("218: the guide's place for this project names no limit on a new board",
              "PETs" not in guide and "cap" not in guide.lower() and "A GET needs" in guide, guide)
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
