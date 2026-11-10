from __future__ import annotations

import json
import shutil

from . import support
from .support import check, skip


def test_picked_top(scratch):
    print("\n76. A label's picked quotes at the head of its Inspector, in pick order, and still with their statements (181)")
    js = support.text("apps/idiograph/static/themes.js")
    src = js.split("function thPickedHtml(", 1)[1].split("\n}\n", 1)[0] if "function thPickedHtml(" in js else ""
    node = shutil.which("node")
    if not node:
        skip("76: the picked quotes in node", "node is not installed")
    else:
        script = support.i18n_js() + (
            "const esc = (s) => String(s); const thSheetTag = (s) => `[${s}]`;\n"
            "const TH = { hasQuotes: true, quotes: {}, sheets: [] };\n"
            "const thPanelRows = () => [\n"
            "  { sheet: 'Initial', time: '02:10', quotes: [{ key: 'Initial:12:0', text: 'first words' }, { key: 'Initial:12:1', text: 'second words' }] },\n"
            "  { sheet: '2d', time: '04:31', quotes: [{ key: '2d:3:0', text: 'later words' }] }];\n"
            "function thPickedHtml(" + src + "\n}\n"
            "const out = [thPickedHtml({}, {}, new Set(['2d:3:0', 'Initial:12:0'])), thPickedHtml({}, {}, new Set()),\n"
            "  thPickedHtml({}, {}, new Set(['Initial:99:0']))];\n"
            "TH.hasQuotes = false; out.push(thPickedHtml({}, {}, new Set(['2d:3:0'])));\n"
            "console.log(JSON.stringify(out));\n")
        res = support.run_node(script, scratch, "picked-76.js")
        out = json.loads(res.stdout or "null") if res.returncode == 0 else None
        check("76: in node, the picks come in pick order with their time and sheet, and nothing shows with none, a pick gone or an old server",
              out is not None and out[0].index("later words") < out[0].index("first words") and "second words" not in out[0]
              and "04:31" in out[0] and "[2d]" in out[0] and out[1:] == ["", "", ""], res.stderr[-300:] if res.returncode else str(out)[:200])
    # no area hands node a script on its command line, which the catalogue runs past Windows's limit (the 0.9.11
    # tag run, WinError 206): each runs from a file through support.run_node
    import re
    eval_flag = "-" + "e"
    on_line = [f.name for f in support.suite_files()
               if re.search(r'\[\s*(?:node|"node"|shutil\.which\("node"\)[^,\]]*)\s*,\s*"' + eval_flag + '"',
                            f.read_text(encoding="utf-8"))]
    check("76: no area runs a script through node's command line, each from a file in its scratch", not on_line, str(on_line))
