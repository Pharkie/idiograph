from __future__ import annotations

from .support import check
import idiograph_routes


def test_root_guard(scratch):
    print("\n20. The case root guard")
    # A scratch server must never reach a live case. Every workbook API resolves its path through
    # case_path, which refuses anything the configured root does not contain, and the recent list
    # is filtered the same way.
    import openpyxl
    import server as server_mod
    root = scratch / "guard-root"
    inside = root / "P9 - Nobody" / "P9 Nobody - EN & ES.xlsx"
    inside.parent.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    wb.active.append(["Name", "Timestamp", "Experiential statements", "Transcript", "Exploratory notes", "Key quotes"])
    wb.save(inside)
    outside = scratch / "guard-elsewhere.xlsx"
    wb.save(outside)
    saved_root, saved_state = server_mod.ROOT_OVERRIDE, server_mod.state
    server_mod.ROOT_OVERRIDE = str(root)
    try:
        check("a workbook inside the root resolves", idiograph_routes.case_path(str(inside)) == inside,
              "case_path returns the absolute path unchanged")
        refused = False
        try:
            idiograph_routes.case_path(str(outside))
        except server_mod.OutsideRoot:
            refused = True
        check("an absolute path outside the root is refused", refused, "case_path raises OutsideRoot")
        refused = False
        try:
            idiograph_routes.case_path("Other Study/Data collection and analysis/Main Data/x.xlsx")
        except server_mod.OutsideRoot:
            refused = True
        check("a repo-relative path outside the root is refused", refused,
              "the live case root is outside a scratch root")
        refused = False
        try:
            idiograph_routes.case_path("")
        except server_mod.OutsideRoot:
            refused = True
        check("an empty path is refused", refused, "no path resolves to the repo root")
        server_mod.state = lambda: {"recent": [{"path": str(outside), "name": "x", "case": "x"},
                                               {"path": str(inside), "name": "y", "case": "y"}]}
        recent = idiograph_routes.api_cases({})["recent"]
        check("the recent list hides cases outside the root", [r["name"] for r in recent] == ["y"],
              f"got {[r['name'] for r in recent]}")
        refused = False
        try:
            idiograph_routes.api_open({"path": str(outside)})
        except server_mod.OutsideRoot:
            refused = True
        check("api_open refuses a workbook outside the root", refused, "the open API goes through case_path")
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.state = saved_root, saved_state
