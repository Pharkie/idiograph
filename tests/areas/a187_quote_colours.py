"""Area 187: a colour per statement (18 October 2026, Adam's choice from a drawing about 16:50). In the
transcript each statement's key quotes take its own colour by its place in the passage's list, statement 1
the crux orange as before, statements 2 to 6 the board map's participant colours and a seventh round again,
the card's number in a dot of that colour and its key quote with a stripe of it, a removal or a move
recolouring the rest at once, and words two statements share showing both. The checks are the behaviour:
which colour goes with which statement, the recolour on a removal and the shared words. The contrasts and
the words, Back to where I was among them, are measured and shown in the review shots (Adam, 18 October).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from . import support
from .support import check, skip

# statement 1 the crux orange, then the cases' colours Blue, Plum, Brown, Indigo and Teal by place, the board's order with
# Olive left out
COLOURS = ("--crux", "--th-case0", "--th-case2", "--th-case3", "--th-case4", "--th-case5")

HARNESS = r"""
const S = { pairsRow: null, prompt: '' };
const PROMPT_FALLBACK = 'A prompt';
let LIVE = [];
const pairsNow = () => LIVE;
const growPairs = () => {};
const drawWordCount = () => {};
const runNudges = () => {};
const fakeEl = () => ({ textContent: '', placeholder: '', attrs: {}, setAttribute(k, v) { this.attrs[k] = String(v); } });
const fakePair = () => { const kids = { '.pair-num': fakeEl(), '.pair-remove': fakeEl(), '.pair-es': fakeEl() };
  return { dataset: {}, querySelector: (sel) => kids[sel] || null }; };
let PAIRS = [];
const pairEls = () => PAIRS;
"""

SCENARIO = r"""
const T = 'The kettle sang on the stove while the rain came down the glass, and I stood there with both hands on the warm cup until the window cleared.';
const out = {};
const marks = (row) => [...markedHtml(row.runs, kqLayer(row)).matchAll(/<span class="kq" data-kq="([^"]*)"((?: data-es-colour(?:-b)?="\d")*) title="[^"]*">([^<]*)<\/span>/g)]
  .map((m) => ({ kq: m[1], colour: (m[2].match(/data-es-colour="(\d)"/) || [])[1] || '',
    second: (m[2].match(/data-es-colour-b="(\d)"/) || [])[1] || '', words: m[3] }));
const words = ['The kettle sang', 'on the stove', 'the rain came down', 'the glass', 'I stood there', 'both hands', 'the warm cup'];
const seven = words.map((w, n) => ({ es: `Statement ${n + 1}`, kq: `"${w}"` }));
// a passage of seven statements as saved: each one's marks by its place, a seventh starting the round again
const ROW = { key: 'Morning:2', stop: true, runs: [{ text: T }], pairs: seven };
out.seven = marks(ROW).map((m) => [m.words, m.colour]);
// the passage being worked on, marked from the fields: the second statement removed, every one after it moves up a colour
S.pairsRow = 'Morning:2';
LIVE = seven.filter((p, n) => n !== 1);
out.removed = marks(ROW).map((m) => [m.words, m.colour]);
// two statements moved, the third's quote now first: the colours follow the places, never the words
LIVE = [seven[2], seven[0], seven[1]];
out.moved = marks(ROW).map((m) => [m.words, m.colour]);
// words two statements share: the first's colour and the second's, and the words the first alone holds its colour alone
LIVE = [{ es: 'Rain', kq: '"the rain came down the glass"' }, { es: 'Glass', kq: '"the glass"' }];
out.shared = marks(ROW).map((m) => [m.words, m.kq, m.colour, m.second]);
// the card: each pair's colour by its place, seven and then round again, and a removal recolouring the rest
PAIRS = [0, 1, 2, 3, 4, 5, 6].map(fakePair);
pairsDrawn();
out.card = PAIRS.map((p) => [p.querySelector('.pair-num').textContent, p.dataset.esColour]);
PAIRS.splice(1, 1);
pairsDrawn();
out.cardRemoved = PAIRS.map((p) => [p.querySelector('.pair-num').textContent, p.dataset.esColour]);
// every other passage's statements: each number in its own statement's colour, an empty pair skipped with its colour kept
const list = statementsHtml({ pairs: [{ es: 'Rain', kq: '' }, { es: '', kq: '' }, { es: 'Glass', kq: '"the glass"' }] });
out.list = [...list.matchAll(/class="es-n" data-es-colour="(\d)">(\d)</g)].map((m) => [m[2], m[1]]);
console.log(JSON.stringify(out));
"""


def test_quote_colours(scratch):
    print("\n187. A colour per statement, 18 October, Adam's choice from a drawing: each statement's key quotes in "
          "its own colour by its place, its number's dot and its key quote's stripe on the card, a removal "
          "recolouring the rest, and words two statements share showing both")
    read = lambda path: Path(path).read_text(encoding="utf-8")
    app, quote_js, css = support.text("family/static/shell.js", "apps/idiograph/static/distil.js"), support.text("family/static/quote.js"), support.text("family/static/style.css", "apps/idiograph/static/distil.css")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    line = lambda src, start: start + src.split(start, 1)[1].split("\n", 1)[0] if start in src else ""

    # ── A. which colour each place takes, and the second's on shared words
    rule = lambda sel: css.split(sel + " {", 1)[-1].split("}", 1)[0] if sel + " {" in css else ""
    first = {n: (re.findall(r"--es: var\((--[\w-]+)\)", rule(f'[data-es-colour="{n}"]')) or [None])[0] for n in range(6)}
    tints = {n: (re.findall(r"--es-tint: var\((--[\w-]+)\)", rule(f'[data-es-colour="{n}"]')) or [None])[0] for n in range(6)}
    second = {n: (re.findall(r"--es-b: var\((--[\w-]+)\)", rule(f'[data-es-colour-b="{n}"]')) or [None])[0] for n in range(6)}
    check("187: statement 1 takes the crux orange and statements 2 to 6 Blue, Plum, Brown, Indigo and Teal of the "
          "cases' colours, each with its own bright tint for its wash, a statement's second colour on shared words "
          "the same by its place",
          tuple(first[n] for n in range(6)) == COLOURS and tuple(second[n] for n in range(6)) == COLOURS
          and [tints[n] for n in range(6)] == [None] + [f"--es-tint{n}" for n in range(1, 6)],
          f"{first} {tints} {second}")
    shared_rule = css.split(".turn-text .kq[data-es-colour-b] {", 1)[-1].split("}", 1)[0]
    check("187: a mark takes its statement's colour for its rule and its wash, statement 1 keeping the crux's wash, "
          "and words two statements share draw a rule in each one's colour",
          "box-shadow: 0 1px 0 var(--es);" in css.split(".turn-text .kq {", 1)[-1].split("}", 1)[0]
          and '.turn-text .kq[data-es-colour="0"] { --es-w: var(--crux-wash);' in css
          and "linear-gradient(var(--es), var(--es))" in shared_rule and "linear-gradient(var(--es-b), var(--es-b))" in shared_rule)
    check("187: the card's number sits in a dot of its statement's colour and its key quote has a stripe of it, and "
          "every other passage's numbers stand in their dots too",
          "background: var(--es);" in css.split(".pair-num {", 1)[-1].split("}", 1)[0]
          and "border-left: 3px solid var(--es);" in css.split(".pair .pair-kq {", 1)[-1].split("}", 1)[0]
          and "background: var(--es);" in css.split(".es-n {", 1)[-1].split("}", 1)[0])

    # ── B. in node: the marks, the card and the list by place, a removal and a move
    node = shutil.which("node")
    if not node:
        skip("187: the colours by place in node", "no node on this machine")
        return
    pieces = [HARNESS, quote_js, support.quote_span_js(), line(app, "const esc = "), line(app, "const escAttr = ")] + [
        whole(app, n) for n in ("rowPairs", "livePairs", "kqLayer", "kqTitle", "markedHtml", "pairsDrawn", "statementsHtml")]
    script = scratch / "quote-colours-187.js"
    script.write_text(support.i18n_js() + "\n".join(pieces + [SCENARIO]), encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        check("187: the colours by place run in node", False, run.stderr.strip()[:300])
        return
    out = json.loads(run.stdout)
    check("187: in node, each statement's marks take its place's colour, the first the crux's, and a seventh starts "
          "the round again",
          out["seven"] == [["The kettle sang", "0"], ["on the stove", "1"], ["the rain came down", "2"], ["the glass", "3"],
                           ["I stood there", "4"], ["both hands", "5"], ["the warm cup", "0"]], str(out["seven"]))
    check("187: in node, a statement removed from the passage being worked on recolours every one after it at once, "
          "and moved ones take their new places' colours",
          out["removed"] == [["The kettle sang", "0"], ["the rain came down", "1"], ["the glass", "2"], ["I stood there", "3"],
                             ["both hands", "4"], ["the warm cup", "5"]]
          and out["moved"] == [["The kettle sang", "1"], ["on the stove", "2"], ["the rain came down", "0"]],
          str([out["removed"], out["moved"]]))
    check("187: in node, words two statements share carry both colours, the first's and the second's, and the words "
          "one alone holds carry its colour alone",
          out["shared"] == [["the rain came down ", "0", "0", ""], ["the glass", "0 1", "0", "1"]], str(out["shared"]))
    check("187: in node, the card colours each pair by its place, the seventh round again, and a removal recolours the "
          "pairs after it with their new numbers",
          out["card"] == [["1", "0"], ["2", "1"], ["3", "2"], ["4", "3"], ["5", "4"], ["6", "5"], ["7", "0"]]
          and out["cardRemoved"] == [["1", "0"], ["2", "1"], ["3", "2"], ["4", "3"], ["5", "4"], ["6", "5"]],
          str([out["card"], out["cardRemoved"]]))
    check("187: in node, every other passage's numbers take their statements' colours, an empty pair skipped with its "
          "place kept", out["list"] == [["1", "0"], ["3", "2"]], str(out["list"]))
