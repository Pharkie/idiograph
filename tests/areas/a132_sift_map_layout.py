from __future__ import annotations

import json
import re
import shutil

from . import support
from .support import check, sift_words_js, skip


def test_sift_map_layout(scratch):
    print("\n132. Country on a map, the circles set apart, 13 October, evening: circles 11 to 40 across their radius, "
          "each holding its number, nudged apart where they would overlap with the larger nearest home, a line from a "
          "moved circle back to its country, each country's name beside its circle, the same counts giving the same "
          "map, the names and lines in a saved SVG, and the note on the projection in the overlay alone. Since the test "
          "review of 18 October the circles' sizes, places, lines and names' layout are review shots, and a circle and "
          "its number for each country, the same map from the same counts and the saved SVG's contents stay")
    import subprocess

    app_src = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    sift_src = support.text("apps/sift/static/sift.js")
    world_text = support.text("apps/sift/static/world.json")
    node = shutil.which("node")
    base = scratch / "sift-map-132"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    note = "Equal Earth projection, equal area (Šavrič, Patterson and Jenny, 2019). Borders from Natural Earth."
    # thirteen European countries close together, and five elsewhere, counts made up for the check
    europe = {"GB": 19, "DE": 15, "NL": 10, "FR": 8, "BE": 6, "IE": 5, "ES": 4, "IT": 4, "CH": 3, "DK": 2, "SE": 2,
              "AT": 1, "LU": 1}
    elsewhere = {"US": 22, "AU": 6, "CA": 3, "BR": 2, "JP": 1}

    # ── A. the layout, in node
    if not node:
        skip("132: the circles, the lines and the names in node", "node is not installed")
    else:
        lead = app_src[app_src.index("const esc = "):app_src.index("// a line from the server with a command in backticks")]
        block = sift_src.split("/* ── the table's rows: its columns, sort and filter, worked out with no page ── */", 1)[-1].split(
            "/* ── the table, drawn ── */", 1)[0]
        block = support.table_js() + "\n" + block
        harness = r"""
const WORLD = __WORLD__;
const FIX = __FIX__;
const pick = (code) => ({ value: sfPickKey(WORLD.names[code]), label: WORLD.names[code] });
const tally = (fix) => Object.fromEntries(Object.entries(fix).map(([code, n]) => [sfPickKey(WORLD.names[code]), n]));
const choices = Object.keys(FIX).map(pick);
const m = sfMapModel(WORLD, choices, tally(FIX), 140);
const again = sfMapModel(WORLD, choices.slice().reverse(), tally(FIX), 140);
const trim = (svg) => svg.replace(WORLD.sphere, '').replace(/<g class="sf-map-land"[^>]*>.*?<\/g>/, '<g class="sf-map-land"/>');
const one = sfMapModel(WORLD, [pick('BR')], tally({ BR: 5 }), 5);
const ones = sfMapModel(WORLD, ['GB', 'FR', 'JP'].map(pick), tally({ GB: 1, FR: 1, JP: 1 }), 3);
console.log(JSON.stringify({
  circles: m.circles.map((c) => ({ code: c.code, name: c.name, n: c.n, r: c.r, x: c.x, y: c.y, hx: c.hx, hy: c.hy,
    off: c.off, line: c.line, label: c.label })),
  same: JSON.stringify(m) === JSON.stringify(again), twice: JSON.stringify(m) === JSON.stringify(sfMapModel(WORLD, choices, tally(FIX), 140)),
  paper: trim(sfMapSvg(WORLD, m, SF_MAP_PAPER)), screen: trim(sfMapSvg(WORLD, m, null)), size: [WORLD.width, WORLD.height],
  one: one.circles.map((c) => [c.code, c.r, c.x === c.hx && c.y === c.hy, c.line, c.label.anchor, c.label.clear, c.label.tie]),
  ones: ones.circles.map((c) => c.r),
  wide: [sfMapWide('United Kingdom', 9), sfMapWide('Malta', 9)],
}));
"""
        harness = harness.replace("__WORLD__", world_text).replace("__FIX__", json.dumps({**europe, **elsewhere}))
        script = base / "map-132.js"
        script.write_text("\n".join([lead, sift_words_js(sift_src), block, harness]), encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        why = (ran.stderr or "")[:400]
        circles = out.get("circles", [])
        check("132: in node, the model gives a circle for each of the eighteen countries, the largest first",
              [c["code"] for c in circles][:2] == ["US", "GB"] and len(circles) == 18
              and [c["n"] for c in circles] == sorted((c["n"] for c in circles), reverse=True), why)
        check("132: in node, the same counts give the same map, the choices in another order and run again",
              out.get("same") is True and out.get("twice") is True)
        paper = out.get("paper", "")
        screen = out.get("screen", "")
        groups = re.findall(r'<g class="sf-map-dot"><title>[^<]*</title><circle [^>]*/><text [^>]*>(\d+)</text></g>', paper)
        check("132: in node, every circle holds its number, 1 included",
              len(groups) == 18 and sorted(int(g) for g in groups) == sorted(c["n"] for c in circles), str(groups[:3]))
        names = paper.split('<g class="sf-map-names"', 1)[-1]
        check("132: in node, every country's name is there",
              circles and all(names.count(f'>{c["name"]}</text>') == 2 for c in circles), names[:200])
        check("132: in node, the saved SVG holds the names and the lines, its words kept as text",
              '<g class="sf-map-lines"' in paper and '<g class="sf-map-names"' in paper and ">United Kingdom</text>" in paper
              and "<path" not in names and "<image" not in paper, names[:200])
        check("132: in node, the note on the projection is in neither the saved SVG nor the screen's map",
              note not in paper and "Patterson" not in paper and "Natural Earth" not in paper and "Patterson" not in screen)
