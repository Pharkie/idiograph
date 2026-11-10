from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from . import support
from .support import check, skip


def test_distil_left(scratch):
    print("\n166. What the night's screenshot checks of 16 to 17 October left open in Distil and its print views, each "
          "a defect or a break of a written rule, measured in shots of invented data and mended. Since the test review "
          "of 18 October the faces, tints, contrast, focus rings, widths and words are review shots, and Rename's line "
          "about the copies, said only while a rename would keep them, stays")
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    rn = whole(app, "rnListShow")
    node = shutil.which("node")

    # ── Rename: the line about the copies goes with the list while a refusal shows, since a refused rename keeps none
    if not node:
        skip("166: Rename's refusal in node", "no node on this machine")
    else:
        harness = r"""
const mk = () => ({ hidden: true, textContent: '', innerHTML: '', children: [] });
const els = { 'rn-said': mk(), 'rn-list': mk(), 'rn-lead': mk(), 'rn-copy': mk() };
const $ = (id) => els[id];
""" + whole(app, "rnSaid") + "\n" + rn + r"""
const state = () => ({ list: !els['rn-list'].hidden, copy: !els['rn-copy'].hidden, said: !els['rn-said'].hidden });
const out = {};
rnSaid(''); out.empty = state();
els['rn-list'].children = [1, 2]; rnListShow(); out.drawn = state();
rnSaid('Mabel is another participant\'s name in this project, so nothing was changed.'); out.refused = state();
rnSaid(''); out.typed = state();
console.log(JSON.stringify(out));
"""
        script = scratch / "rename-166.js"
        script.write_text(harness, encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        o = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
        check("166: in node, the line about the copies shows with the list, goes while a refusal shows and comes back as "
              "the name is typed again",
              o == {"empty": {"list": False, "copy": False, "said": False}, "drawn": {"list": True, "copy": True, "said": False},
                    "refused": {"list": False, "copy": False, "said": True}, "typed": {"list": True, "copy": True, "said": False}},
              (run.stdout + run.stderr)[:300])
