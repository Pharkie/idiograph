from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import support
from .support import check, skip


def test_part_order(scratch):
    print("\n149. The parts in the order a study does them, 15 October, later, Adam's word: Sift, the literature "
          "review, then Distil, the analysis, then Trace, checking the references, on the first screen, in Settings, "
          "on /design and wherever the docs name the three together, every id, key, route and file as it was. Since the "
          "test review of 18 October the sections', the list's and the docs' order are review shots, and the folds' old "
          "keys and the arrow keys walking Settings' list stay")
    import subprocess

    read = lambda path: Path(path).read_text(encoding="utf-8")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    # Sift's parts of the shell, from app.js since the family codebase's third build (22 October 2026)
    sset = support.text("apps/sift/static/sift_settings.js")
    trace = support.text("apps/trace/static/trace.js")

    # ── A. each section folds under its old key, so a fold kept in the browser still holds
    check("149: the page draws each section into its own place and folds each under its old key, so the order on the "
          "screen is the markup's and a fold kept in the browser still holds",
          # the family's Home asks the app's own section since the fifth build (23 October 2026), Idiograph's
          # picker its own homeDraw
          "if (own && own.home) own.home(data);" in fn(app, "drawHome")
          and "drawSiftHome" not in fn(app, "drawHome") and "home: drawSiftHome" in sset
          and "foldable($('home-analysis'), $('analysis-head'), 'analysis');" in fn(app, "drawPick")
          and "foldable($('sift-home'), $('sift-head'), 'sift');" in fn(sset, "drawSiftHome")
          and "foldable($('trace-home'), $('trace-head'), 'trace');" in fn(trace, "drawTraceHome") and "home: drawTraceHome" in trace)

    # ── B. the arrow keys walk Settings' list
    node = shutil.which("node")
    if not node:
        skip("149: the arrow keys walk Settings' list in node", "node is not installed")
    else:
        # Idiograph's page, its own categories since the split's third build (20 October)
        line = ("const APP = 'idiograph';\nconst PANES_BY_APP = {" + app.split("const PANES_BY_APP = {", 1)[1].split("};", 1)[0]
                + "};\n" + next((ln for ln in app.splitlines() if ln.startswith("const PANES = ")), ""))
        script = scratch / "panes-149.js"
        script.write_text(
            "const shown = [];\n"
            "function showPane(name) { paneHeld = name; shown.push(name); }\n"
            + line + "\nlet paneHeld = 'general';\n"
            + "function paneKeys(" + fn(app, "paneKeys") + "\n}\n"
            "const press = (key, n) => { for (let i = 0; i < n; i++) paneKeys({ key, preventDefault() {} }); return shown.splice(0); };\n"
            "const down = press('ArrowDown', 8);\n"
            "const up = press('ArrowUp', 2);\n"
            "paneHeld = 'general';\n"
            "const right = press('ArrowRight', 2);\n"
            "console.log(JSON.stringify({ down, up, right }));\n", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
        check("149, 20 October: in node, the arrow keys walk Idiograph's Settings as it stands, Down from General to "
              "Language and formats (fmtcore), "
              "Experiential statements, PETs, AI features and round to General, GETs, Export and Projects gone since "
              "settingsplit, Up back the other way",
              out.get("down") == ["formats", "statements", "pets", "ai", "general", "formats", "statements", "pets"]
              and out.get("up") == ["statements", "formats"] and out.get("right") == ["formats", "statements"],
              str(out) if out else run.stderr.strip()[:300])
