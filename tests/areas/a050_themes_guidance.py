from __future__ import annotations

import json
import re
import shutil

from . import support
from .support import STUDY_PSEUDONYMS, check, demo_copy, skip
import idiograph_routes


def test_themes_guidance(scratch):
    print("\n50. Themes, the Guidance tab: themes_guidance.md in the board panel, as the rail shows guidance.md")
    import subprocess
    import server as server_mod
    import themes as themes_mod

    js = support.text("apps/idiograph/static/themes.js")
    shipped = support.source("apps/idiograph/themes_guidance.md")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0]
    HEADS = ["How many", "How to group", "Titles", "Group, stack or bin", "Inside a PET", "Before you finish"]

    # ── A. the file, and the one parser that reads it and guidance.md
    shown = idiograph_routes.themes_guidance()
    lines = [line for s in shown for line in s["lines"]]
    check("110: the shown lines carry no em dash, no semicolon and no pseudonym from either study",
          not any("\u2014" in line or ";" in line for line in lines)
          and not [name for name in STUDY_PSEUDONYMS if re.search(rf"\b{name}\b", shipped.read_text(encoding="utf-8"))])
    check("110: a missing file is an empty list",
          idiograph_routes.themes_guidance(scratch / "no-such-guidance.md") == [])
    edited = scratch / "themes-guidance-edited.md"
    edited.write_text("# A title\n\nAn intro the app never shows.\n\n## One\n\n- first\n* second\n\n## Two\n- third\n",
                      encoding="utf-8")
    first = idiograph_routes.themes_guidance(edited)
    edited.write_text("# A title\n\n## One\n\n- first, reworded\n", encoding="utf-8")
    check("110: any file in that format reads, either marker, and a second read takes the file as it now stands",
          first == [{"heading": "One", "lines": ["first", "second"]}, {"heading": "Two", "lines": ["third"]}]
          and idiograph_routes.themes_guidance(edited) == [{"heading": "One", "lines": ["first, reworded"]}], str(first))

    # ── B. /api/themes carries it, read afresh on every open, and writes nothing
    root = scratch / "guidance-root"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    saved_root, saved_file = server_mod.ROOT_OVERRIDE, idiograph_routes.THEMES_GUIDANCE
    server_mod.ROOT_OVERRIDE = str(root)
    try:
        before = work.read_bytes()
        answer = idiograph_routes.api_themes({"workbook": str(work)})
        check("110: /api/themes carries guidance, the six sections in the file's order, the intro left out",
              answer["guidance"] == shown and [s["heading"] for s in answer["guidance"]] == HEADS)
        check("110: opening it writes neither the workbook nor a themes file",
              work.read_bytes() == before and not themes_mod.themes_path(work).exists())
        copy = scratch / "themes-guidance-live.md"
        copy.write_text(shipped.read_text(encoding="utf-8"), encoding="utf-8")
        idiograph_routes.THEMES_GUIDANCE = copy
        was = idiograph_routes.api_themes({"workbook": str(work)})["guidance"]
        copy.write_text(copy.read_text(encoding="utf-8").replace("- Watch for your hopes", "- Watch closely for your hopes"),
                        encoding="utf-8")
        now = idiograph_routes.api_themes({"workbook": str(work)})["guidance"]
        check("110: an edit to the file shows on the next open, with no restart",
              was == shown and now[3]["lines"][-1].startswith("Watch closely for your hopes") and now[:3] == shown[:3])
        idiograph_routes.THEMES_GUIDANCE = scratch / "gone" / "themes_guidance.md"
        check("110: with the file missing /api/themes carries an empty list, and the rest of the answer as before",
              idiograph_routes.api_themes({"workbook": str(work)})["guidance"] == []
              and len(idiograph_routes.api_themes({"workbook": str(work)})["cards"]) == len(answer["cards"]))
    finally:
        server_mod.ROOT_OVERRIDE, idiograph_routes.THEMES_GUIDANCE = saved_root, saved_file

    # ── E. remembering, in the browser alone
    check("110, 183: whether the sidebar is open and on which tab is kept in localStorage for each screen, never in the file or the settings",
          "const TH_SIDE_KEYS = { pets: 'idiograph-themes-board', gets: 'idiograph-gets-board' };" in js
          and js.count("TH_SIDE_KEYS") == 2
          and "localStorage.setItem(thSideKey(TH.mode), JSON.stringify({ open: !!TH.sideOpen, tab: TH.tab }));" in fn(js, "thSideKeep")
          and "try {" in fn(js, "thSideKeep") and "try {" in fn(js, "thSideStored")
          and "if (keep) thSideKeep();" in fn(js, "thSideOpen") and "if (keep) thSideKeep();" in fn(js, "thSideShut")
          and "idiograph-themes-board" not in support.source("server.py").read_text(encoding="utf-8")
          and "sideOpen" not in fn(js, "thBody") and "TH.tab" not in fn(js, "thBody")
          and "const body = { workbook: path, version: thBody(v, TH.meta) };" in fn(js, "thSaveOnce"))
    opened = fn(js, "themesOpen")
    check("110, 183: an open of the screen shuts it without forgetting, then brings it back as it was once the board is on the canvas",
          "thSideShut(false);" in opened and opened.index("thLoad(data, { fit: true });") < opened.index("thSideRestore();")
          and "thSideShut(false);" in fn(js, "themesLeave")
          and "if (kept.open) thSideOpen(kept.tab, undefined, false);" in fn(js, "thSideRestore"))

    # ── G. the remembering, in node
    node = shutil.which("node")
    if not node:
        return skip("110: the sidebar's remembering in node", "no node on this machine")
    script = scratch / "themes-guidance.js"
    script.write_text(support.i18n_js() + js + r"""
const store = {};
globalThis.localStorage = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); } };
const out = {};
TH.mode = 'pets';
TH.ai = { on: true };
out.none = thSideStored();
TH.sideOpen = true; TH.tab = 'guidance'; thSideKeep();
out.open = [thSideStored(), store[thSideKey('pets')]];
TH.sideOpen = false; TH.tab = 'review'; thSideKeep();
out.shut = thSideStored();
store[thSideKey('pets')] = '{"open": true, "tab": "quotes"}';
out.stale = thSideStored();
store[thSideKey('pets')] = 'not json';
out.junk = thSideStored();
globalThis.localStorage = { getItem: () => { throw new Error('private'); }, setItem: () => { throw new Error('private'); } };
out.blocked = thSideStored();
TH.sideOpen = true; thSideKeep();
out.tabs = TH_TABS;
console.log(JSON.stringify(out));
""", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("110: the sidebar's remembering runs in node", False, run.stderr.strip()[:300])
    out = json.loads(run.stdout)
    check("110, 183: in node, nothing stored is closed on the Inspector, and what is kept comes back as it was",
          out["none"] == {"open": False, "tab": "inspector"} and out["open"][0] == {"open": True, "tab": "guidance"}
          and json.loads(out["open"][1]) == {"open": True, "tab": "guidance"} and out["shut"] == {"open": False, "tab": "review"}
          and out["tabs"] == ["inspector", "guidance", "history", "review", "revise"], str(out))
    check("110, 183: in node, a tab that is no more, a value that is not ours or a blocked store fall back to closed on the Inspector",
          out["stale"] == out["junk"] == out["blocked"] == {"open": False, "tab": "inspector"}, str(out))
