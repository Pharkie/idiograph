from __future__ import annotations

import json
import shutil

from . import support
from .support import check
import idiograph_routes


def test_no_continue(scratch):
    print("\n101. No Continue on the home screen: no button, no highlight on the row and no rule for either, and the "
          "recent list keeps no screen")
    import server as server_mod

    # ── B. a state.json on disk from a build that kept the screen, written again without it
    root = scratch / "no-continue-root"
    shutil.rmtree(root, ignore_errors=True)
    case_dir = root / "P1 - {}-{}".format("Ivy", "Example")
    case_dir.mkdir(parents=True)
    book = case_dir / "P1 Ivy - EN & ES.xlsx"
    shutil.copy2(support.DEMO_WORKBOOK, book)
    state_file = scratch / "no-continue-state.json"
    kept = (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = str(root), state_file, None
    try:
        older = {"path": "elsewhere/P2 Wyn - EN & ES.xlsx", "name": "P2 Wyn - EN & ES", "case": "P2 - Wyn",
                 "opened": 1, "screen": "pets"}
        mine = {"path": server_mod.rel_path(book), "name": book.stem, "case": "P1 - Ivy", "opened": 2, "screen": "pets"}
        sift = [{"folder": "reviews/one", "opened": 3}]
        state_file.write_text(json.dumps({"recent": [mine, older], "sift": sift}), encoding="utf-8")
        before = idiograph_routes.api_cases({})["participants"]
        idiograph_routes.api_themes({"workbook": str(book)})
        after = idiograph_routes.api_cases({})["participants"]
        on_disk = json.loads(state_file.read_text(encoding="utf-8"))
        check("101: a case opened last under a build from before draws as any other row, before and after its PETs",
              [c["case"] for c in before] == [c["case"] for c in after] == ["P1 - Ivy"]
              and not any("continue" in c for c in before + after))
        check("101: the next opening writes the recent list again with no screen in any entry, and the screenings kept",
              [r["path"] for r in on_disk["recent"]] == [mine["path"], older["path"]]
              and all(sorted(r) == ["case", "name", "opened", "path"] for r in on_disk["recent"])
              and on_disk["sift"] == sift, str([sorted(r) for r in on_disk["recent"]]))
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept
