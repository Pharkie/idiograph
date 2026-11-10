from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from . import support
from .support import check, skip

# a script's line that holds a one-letter key compared in lowercase: `e.key === 'q'`, or a key the handler lowered
# first, `key === 'q'` or `k === 'z'`
LETTER = re.compile(r"(?<![\w.])(e\.key|key|k) === '([a-z])'")


def letter_problems(src: str) -> list[str]:
    """Each line of a page script that takes a letter key in lowercase alone: `e.key` compared with a lowercase
    letter and not with its capital on the same line, or a `key` or `k` compared with one where the nearest `const`
    before it that sets it does not lower `e.key`."""
    out = []
    lines = src.split("\n")
    for i, line in enumerate(lines):
        for m in LETTER.finditer(line):
            name, letter = m.groups()
            if name == "e.key":
                if f"e.key === '{letter.upper()}'" not in line:
                    out.append(f"{i + 1}: {line.strip()[:90]}")
                continue
            made = next((lines[j] for j in range(i, -1, -1) if re.search(rf"\bconst {name} = ", lines[j])), "")
            if "toLowerCase()" not in made:
                out.append(f"{i + 1}: {line.strip()[:90]}")
    return out


def test_polish_seven(scratch):
    print("\n176. What polish6's screenshot check left, 18 October: Sift's flow's stage under way in the ink over "
          "Mermaid's own rule, a drag across passages kept to their words, Auto-arrange clear of the picked quotes, the "
          "line at the foot over the canvas's zoom bar and bin, and the statements screen's letter keys with Caps Lock on. "
          "Since the test review of 18 October the colours, the margins and the line's place are review shots, and the "
          "letter keys with Caps Lock on stay")
    read = lambda path: Path(path).read_text(encoding="utf-8")
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    node = shutil.which("node")

    # ── 5. the statements screen's letter keys in either case
    keydown = support.keydown_text(app)
    lowered = "    const key = (e.key || '').length === 1 ? e.key.toLowerCase() : e.key;"
    check("176: the statements screen lowers a one-letter key before its letters, after a field or a chord has taken "
          "its own, and asks the lowered key for E, Q, C, T, G, M and P (M the minimap's, area 169)",
          lowered in keydown and keydown.index("if (typing || MOD(e) || e.altKey) return;") < keydown.index(lowered)
          and sorted(re.findall(r"else if \(key === '([a-z])'", keydown)) == sorted("ceqtgmp")
          and not re.findall(r"else if \(e\.key === '([a-z])'", keydown))
    found = {Path(p).name: letter_problems(support.text(p)) for p in (
        "family/static/shell.js", "apps/idiograph/static/distil.js", "apps/idiograph/static/themes.js", "apps/sift/static/sift.js",
        "apps/trace/static/trace.js", "family/static/search.js", "apps/sift/static/sift_search.js", "family/static/quote.js",
        "family/static/beat.js", "family/static/table.js")}
    found = {n: v for n, v in found.items() if v}
    planted = ("if (e.key === 'q') go();", "const key = e.key;\nif (key === 'q') go();")
    check("176: every part takes a letter key with Caps Lock on, each lowercase letter compared with its capital or "
          "with a key lowered first, the statements screen's, PETs', Sift's, Trace's and Search's, and the check finds "
          "one that is not",
          not found and all(letter_problems(p) for p in planted)
          and not letter_problems("if (e.key === 'g' || e.key === 'G') go();")
          and not letter_problems("const key = e.key.length === 1 ? e.key.toLowerCase() : e.key;\nif (key === 'u') go();"),
          json.dumps(found)[:400])
    if not node:
        skip("176: the statements screen's keys in node", "node is not on this machine")
    else:
        start = keydown.index(lowered)
        code = r"""
const APP = 'idiograph';
const calls = [];
const work = { hidden: false };
const $ = (id) => (id === 'work' ? work : null);
const S = { data: { path: 'a.xlsx', name: 'Ada' } };
const stub = (name) => () => calls.push(name);
const togglePlay = stub('play'), openEditor = stub('edit'), current = () => null, commitQuote = stub('quote');
const assignKey = stub('assign'), trimKey = stub('trim'), openHelp = stub('help'), toggleGuide = stub('guide');
// P is the PETs step since 18 October (area 177), esStep('pets'), which opens PETs as openThemes did
const openThemes = stub('pets'), esStep = stub('pets'), move = stub('move');
const press = (key, shiftKey = false) => { const e = { key, shiftKey, preventDefault() {} }; ((e) => {
""" + keydown[start:] + r"""
  })(e); return calls.splice(0).join(' '); };
const out = {};
for (const k of ['e', 'q', 'c', 't', 'g', 'p']) out[k] = [press(k), press(k.toUpperCase())];
out.other = [press(' '), press('?', true), press('ArrowLeft'), press('Dead'), press('x'), press('X')];
work.hidden = true;
out.away = press('Q');
console.log(JSON.stringify(out));
"""
        script = scratch / "keys-176.js"
        script.write_text(code, encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        o = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
        check("176: in node, E, Q, C, T, G and P do on the statements screen with Caps Lock on what they do with it off, "
              "Space, ? and the arrows as before, a key it has no use for nothing, and Q nothing off the screen",
              o.get("e") == ["edit", "edit"] and o.get("q") == ["quote", "quote"] and o.get("c") == ["assign", "assign"]
              and o.get("t") == ["trim", "trim"] and o.get("g") == ["guide", "guide"] and o.get("p") == ["pets", "pets"]
              and o.get("other") == ["play", "help", "move", "", "", ""] and o.get("away") == "",
              (run.stdout + run.stderr)[:400])

