"""Area 417: the Guidance tab of the LPETs, LGETs and Trajectories screens (guidebuild, 17 November 2026, Adam's yes to
the draft). Each screen shows lines of its own, read afresh from `lpets_guidance.md`, `lgets_guidance.md` and
`trajectories_guidance.md` in the shape of `themes_guidance.md`, and the GETs screen keeps the GETs lines of
`pet_guidance.md` alone. Checked on a scratch copy of the longitudinal demo: a participant's LPETs, the LGETs and
Trajectories each answer their own file's lines and write nothing, an edit to a file shows on the next open, a missing
file gives none, and the page holds the Trajectories tab."""
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

from . import support
from .a394_lipa_demo import as_cloned
from .support import STUDY_PSEUDONYMS, check as said_check

WHO = "Arlo"
FILES = {"lpets": "lpets_guidance.md", "lgets": "lgets_guidance.md", "trajectories": "trajectories_guidance.md"}


def check(name, ok, detail=""):
    said_check(name, bool(ok), "" if ok else str(detail)[:700])


def test_screen_guidance(scratch: Path):
    print("\n417. The Guidance tab on LPETs, LGETs and Trajectories: each screen's own file, the GETs screen's lines "
          "kept (guidebuild, 17 November)")
    import agent_log
    import app_identity
    import idiograph_routes as routes
    import server as server_mod
    import themes_ai

    shipped = {k: support.source(f"apps/idiograph/{v}") for k, v in FILES.items()}
    check("417: the three files are shipped with the app and carry no pseudonym of either study",
          all(p.exists() for p in shipped.values())
          and set(FILES.values()) <= set(app_identity.FILES["idiograph"])
          and not [n for n in STUDY_PSEUDONYMS for p in shipped.values()
                   if re.search(rf"\b{n}\b", p.read_text(encoding="utf-8"))])
    read = {k: routes.themes_guidance(p) for k, p in shipped.items()}
    check("417: each file reads as groups of lines, and the three differ from one another and from the GETs lines",
          all(v and all(s["heading"] and s["lines"] for s in v) for v in read.values())
          and len({json.dumps(v) for v in read.values()}) == 3
          and all(v != themes_ai.gets_guidance_lines() for v in read.values()))

    fresh = scratch / "guide-417-clone"
    shutil.rmtree(fresh, ignore_errors=True)
    shutil.copytree(support.source("demo"), fresh, ignore=as_cloned)
    kept = (server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO, os.environ.get(agent_log.PLACE), server_mod.CONFIG_PATH,
            routes.LPETS_GUIDANCE, routes.LGETS_GUIDANCE, routes.TRAJECTORIES_GUIDANCE)
    cfg = scratch / "guide-417-config.json"
    base = {"interviewer": "Interviewer", "corpus": "", "gravity_reference": "", "corpus_exclude": []}
    try:
        server_mod.DEMO_DIR = server_mod.SHIPPED_DEMO = fresh
        os.environ[agent_log.PLACE] = str(scratch / "guide-417-agent-log.json")
        demo = server_mod.demo_lipa_dir()
        routes.fill_demo()
        root = scratch / "guide-417-allotment"
        shutil.rmtree(root, ignore_errors=True)
        shutil.copytree(demo, root, ignore=shutil.ignore_patterns("pristine", "source"))
        cfg.write_text(json.dumps(dict(base, projects=[{"root": str(root)}])), encoding="utf-8")
        server_mod.CONFIG_PATH = cfg
        routes.api_project({"root": str(root), "agents": True})
        book = next(root.glob(f"{WHO}/{WHO} - *.xlsx"))

        def call(route: str, body: dict) -> dict:
            with routes.route_scope(route, body):
                return server_mod.ROUTES[route](body)

        def tree():
            return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}

        before = tree()
        lp = call("/api/gets", {"workbook": str(book), "lpets": True})["guidance"]
        lg = call("/api/gets", {"workbook": str(book)})["guidance"]
        tj = call("/api/trajectories", {"workbook": str(book)})["guidance"]
        check("417: a participant's LPETs, the LGETs and Trajectories each answer their own file's lines",
              (lp, lg, tj) == (read["lpets"], read["lgets"], read["trajectories"]), (lp[:1], lg[:1], tj[:1]))
        check("417: opening the three writes nothing", tree() == before)

        edited = scratch / "guide-417-lpets.md"
        edited.write_text("# L\n\n## One\n\n- first, reworded\n", encoding="utf-8")
        routes.LPETS_GUIDANCE = edited
        now = call("/api/gets", {"workbook": str(book), "lpets": True})["guidance"]
        routes.LPETS_GUIDANCE = scratch / "gone" / "lpets_guidance.md"
        gone = call("/api/gets", {"workbook": str(book), "lpets": True})["guidance"]
        check("417: an edit to a file shows on the next open, a missing file gives none, the other screens unchanged",
              now == [{"heading": "One", "lines": ["first, reworded"]}] and gone == []
              and call("/api/gets", {"workbook": str(book)})["guidance"] == read["lgets"])
    finally:
        (server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO, env, server_mod.CONFIG_PATH,
         routes.LPETS_GUIDANCE, routes.LGETS_GUIDANCE, routes.TRAJECTORIES_GUIDANCE) = kept
        if env is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = env

    js = support.text("apps/idiograph/static/trajectories.js")
    html = support.text("apps/idiograph/static/idiograph.html")
    check("417: the page holds Trajectories' Guidance sidebar and its edge tab, drawn from the answer's guidance",
          'id="tj-guide"' in html and 'id="tj-open-guide"' in html and "TJ.data.guidance" in js
          and "function trajGuideDraw" in js)
