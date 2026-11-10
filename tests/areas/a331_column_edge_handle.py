"""Area 331: the statements screen's column edges shown, and the new default widths (coledge, Adam, 6 November 2026).
He found the edge between Transcript and Exploratory notes invisible, so the two edges between columns show a faint
rule always, with a pill handle on it at the middle of the columns' visible height, 12 px wide to take the pointer, the
two outer edges staying 8 px with a line on hover only, and a screen opens with the columns sharing the width as the
notes 1, the transcript 3 and the statements 2, whatever their order. What is held here is what behaves: the default
tracks and the widths they give, the handle drawn at rest, the hit area, where it stands as the columns scroll, the
edges' model keeping widths held and Reset going to the new default, and Columns keeping its name where it is narrow.
Nothing here pins a colour or a pixel of the look, which the review shots hold."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from . import support
from .a220_column_widths import edges_js
from .support import check, skip


def css_rules(css: str) -> list[tuple[list[str], dict[str, str]]]:
    """Each plain rule of a style sheet as its selectors and declarations, comments taken out, media blocks read inside."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out = []
    for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        decls = {}
        for d in body.split(";"):
            if ":" in d:
                k, v = d.split(":", 1)
                decls[k.strip()] = " ".join(v.split())
        out.append(([" ".join(s.split()) for s in sel.split(",")], decls))
    return out


def declarations(rules, selector: str) -> dict[str, str]:
    """The declarations of every rule that names exactly `selector`, later ones over earlier."""
    merged: dict[str, str] = {}
    for sels, decls in rules:
        if selector in sels:
            merged.update(decls)
    return merged


def grid(tracks: list[tuple[float, float]], total: float) -> list[float]:
    """Widths of `minmax(least, Nfr)` tracks as a grid settles them: a track whose share falls under its least is held at it
    and the rest share what is left."""
    held: dict[int, float] = {}
    while True:
        free = [i for i in range(len(tracks)) if i not in held]
        room = total - sum(held.values())
        share = {i: room * tracks[i][1] / sum(tracks[j][1] for j in free) for i in free}
        low = [i for i in free if share[i] < tracks[i][0]]
        if not low:
            return [held[i] if i in held else share[i] for i in range(len(tracks))]
        for i in low:
            held[i] = tracks[i][0]


def minmax(value: str) -> tuple[float, float]:
    m = re.fullmatch(r"minmax\((\d+)px,\s*([\d.]+)fr\)", value or "")
    return (float(m.group(1)), float(m.group(2))) if m else (0.0, 0.0)


def test_column_edge_handle(scratch: Path):
    print("\n331. The column edges shown (6 November, Adam's option C): a rule between the columns always and a pill handle "
          "at the middle of their height, 12 px to take the pointer, the margins 8 px and on hover only, and the new "
          "default widths, the notes 1, the transcript 3 and the statements 2")
    shared = css_rules(support.text("family/static/style.css"))
    css = css_rules(support.text("apps/idiograph/static/distil.css"))
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    page = support.page_text()

    # ── A. the default tracks, each column's own, so the share holds whatever the columns' order
    work = {}
    for sels, decls in shared:
        if sels == ["#work"] and "--es-track" in decls:
            work = decls
    es, tx, en, st = (minmax(work.get(k, "")) for k in ("--es-track", "--tx-track", "--en-track", "--st-track"))
    check("331: the default tracks are the notes 1, the transcript 3 and the statements 2, each held to its own least "
          "width, 160, 300 and 210 px, as before",
          (en[1], tx[1], es[1]) == (1.0, 3.0, 2.0) and (en[0], tx[0], es[0]) == (160.0, 300.0, 210.0), json.dumps(work))
    check("331: the stacked column stands beside the transcript in the same 2 to 3, and the two columns up to 800px, which "
          "take the statements' and the transcript's tracks, do too",
          st[1] == es[1] and st[0] == 280.0 and work.get("--cols2") == "var(--es-track) var(--tx-track)", json.dumps(work))
    at_1280 = grid([es, tx, en], 1147)
    at_1050 = grid([es, tx, en], 917)
    at_801 = grid([es, tx, en], 692)
    check("331: at 1,280 the tracks give the statements 382, the transcript 574 and the notes 191 px, at 1,050 the notes "
          "stand at their least 160 with the statements 303 and the transcript 454, and at 801 the notes stand at 160 "
          "with the others above their least",
          [round(w) for w in at_1280] == [382, 574, 191] and [round(w) for w in at_1050] == [303, 454, 160]
          and round(at_801[2]) == 160 and at_801[0] >= 210 and at_801[1] >= 300,
          json.dumps([at_1280, at_1050, at_801]))

    # ── B. the edges: the rule and the pill at rest, the hit area, the margins as they were
    edge = declarations(css, ".col-edge")
    between = declarations(css, ".col-edge.between")
    outer_line = declarations(css, ".col-edge::before")
    rule = declarations(css, ".col-edge.between::before")
    pill = declarations(css, ".col-edge.between::after")
    pill_hover = declarations(css, ".col-edge.between:hover::after")
    check("331: an edge between two columns is 12 px wide on the gap's middle, 2 px more than the 8 px slot it stands in, and "
          "the two outer edges stay 8 px",
          edge.get("width") == "8px" and between.get("width") == "12px" and between.get("margin-left") == "-2px"
          and edge.get("cursor") == "col-resize", json.dumps([edge, between]))
    check("331: the rule between two columns is shown at rest, where an outer edge's line is shown on hover only, and the pill "
          "is drawn at rest too, a 12 by 48 px chip with nothing hiding it",
          rule.get("opacity") == "1" and outer_line.get("opacity") == "0"
          and pill.get("content") == '""' and pill.get("width") == "12px" and pill.get("height") == "48px"
          and not {"opacity", "visibility"} & set(pill) and pill.get("display") != "none",
          json.dumps([rule, outer_line, pill]))
    check("331: hovered, dragged or focused the pill fills in another colour than at rest, and the rule darkens, so the "
          "handle itself says it is under the pointer",
          pill_hover.get("background-color") and pill_hover.get("background-color") != pill.get("background-color")
          and declarations(css, ".col-edge:hover::before").get("background")
          != rule.get("background") and ".col-edge.between.dragging::after" in
          [s for sels, _ in css for s in sels] and ".col-edge.between:focus-visible::after" in [s for sels, _ in css for s in sels],
          json.dumps([pill, pill_hover]))
    check("331: the pill stands where `--edge-mid` says, from the edge's top, and the edges lie over the columns, in the "
          "reading area before the columns' body and outside the scrolling transcript, so the pill stays in view as they "
          "scroll",
          "--edge-mid" in pill.get("top", "") and declarations(css, ".col-edges").get("position") == "absolute"
          and 'class="col-edges" id="col-edges"' in page
          and page.index('id="col-edges"') < page.index('id="cols-body"') < page.index('id="transcript"'),
          pill.get("top", ""))
    check("331: below 801px the edges are still hidden, the narrow layout having none to drag",
          any(sels == [".col-edges"] and decls.get("display") == "none" for sels, decls in css), "")
    check("331: the keyboard and the double click are as they were: Tab reaches an edge, the left and right arrows move it "
          "EDGE_STEP, 16 px, four times as far with Shift, and a double click puts that edge back",
          "const EDGE_STEP = 16;" in js and "e.shiftKey ? dx * 4 : dx" in js
          and "ArrowLeft: -EDGE_STEP, ArrowRight: EDGE_STEP" in js and "edgeBack" in js and "el.tabIndex = 0;" in js, "")

    # ── C. the edges' model in node: which edges lie between, where the middle is, held widths kept, Reset the new default
    node = shutil.which("node")
    if not node:
        skip("331: the edges' placing and model in node", "node is not installed")
        return
    script = scratch / "a331-edges.js"
    script.write_text("""
globalThis.document = { documentElement: { clientWidth: 1280 } };
globalThis.window = { innerWidth: 1280 };
globalThis.getComputedStyle = () => ({ getPropertyValue: () => '28px' });
globalThis.$ = () => ({});
globalThis.stackedNow = () => false;
globalThis.S = {};
""" + edges_js() + r"""
const out = {};
out.three = [0, 1, 2, 3].map((k) => edgePlace(k, 3, 115, 157, 686).between);
out.two = [0, 1, 2].map((k) => edgePlace(k, 2, 115, 157, 686).between);
out.mid = edgePlace(1, 3, 115, 157, 686).mid;
out.midShort = edgePlace(1, 3, 115, 157, 486).mid;
// the new default's natural geometry at 1,280: 382 | 574 | 191 with the margins 32 and 45
const nat = { left: 32, right: 45, inL: 8, inR: 16, order: ['statements', 'transcript', 'notes'], widths: { statements: 382, notes: 191 } };
const held = { left: 40, right: 40, statements: 313, notes: 313 };
const kept = edgesModel(nat, held);
out.held = { left: kept.left, w: kept.widths };
const fresh = edgesModel(nat, null);
out.fresh = { left: fresh.left, w: fresh.widths };
out.reset = edgesKept(fresh, nat, held);
out.dragged = edgesKept(edgeMove(fresh, nat, 2, -60), nat, null) !== null;
console.log(JSON.stringify(out));
""", encoding="utf-8")
    ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    try:
        o = json.loads(ran.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        o = {}
    said = (ran.stdout + ran.stderr)[:600]
    check("331: in node, the edges between two columns are told from the outer two, three columns having two and two "
          "columns one, and the pill's middle is the middle of the columns' visible height from the edge's top",
          o.get("three") == [False, True, True, False] and o.get("two") == [False, True, False]
          and o.get("mid") == 307 and o.get("midShort") == 207, said)
    check("331: in node, widths held for a screen are kept over the new default, an edge with none held opens where the "
          "new default puts it, Reset (every edge back) keeps nothing, and a drag from the default is kept",
          o.get("held") == {"left": 40, "w": {"statements": 313, "notes": 313}}
          and o.get("fresh") == {"left": 32, "w": {"statements": 382, "notes": 191}}
          and o.get("reset") is None and o.get("dragged") is True, said)

    # ── D. Columns stays Columns where its word goes: the chevron alone, with its name and its tooltip
    check("331: where a narrow column leaves Columns no room for its word it keeps its chevron alone, still named Columns "
          "for a screen reader and still saying the columns shown in its tooltip",
          declarations(shared, ".cols-tight .cols-pick-word").get("display") == "none"
          and re.search(r'id="cols-pick" aria-label="[^"]+"', page) is not None
          and "$('cols-pick').title = t('distil.cols.title'" in js,
          "")
