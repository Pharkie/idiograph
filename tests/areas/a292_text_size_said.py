"""Area 292: the text size said when it changes (zoomshow, 30 October 2026). In Idiograph's own window, when the keys or
View's items change the zoom the page's toast says the new size, "Text size 110%", at each step and again at the actual
size, the percent written by the Numbers format. A row picked in Settings does not say it, and nor does a browser's tab,
which has no `idiographTextSize`. Where the zoom stands at none of Small, Medium and Large, no row is ticked and the
heading says the size (option A of that day's round).

What is checked: in node on the shell's own functions and its own `idiograph-zoom` listener, against a stand-in window
that tells the page twice for a change as the real one does, a step to 110% said once on one line, Actual Size said,
a Settings pick said nowhere and the key after it said, a browser's tab saying nothing, and the rows ticked at 0.9, 1
and 1.25 alone with the heading carrying the size between them. Fixtures are the zoom numbers alone."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import support
from .support import check, skip


def whole(src: str, head: str) -> str:
    at = src.index(head)
    return src[at:src.index("\n}\n", at) + 3]


def line_of(js: str, start: str) -> str:
    at = js.index(start)
    return js[at:js.index("\n", at) + 1]


HARNESS = r"""
const els = {};
const mk = () => ({ hidden: false, textContent: '' });
const $ = (id) => els[id] || (els[id] = mk());
const said = [];
const say = (m) => said.push(m);
const radios = ['small', 'medium', 'large'].map((value) => ({ value, checked: false }));
const document = { querySelectorAll: () => radios };
const handlers = [];
const window = { addEventListener: (type, fn) => { if (type === 'idiograph-zoom') handlers.push(fn); } };
let zoom = 1;
// the window's two tellings of a change, the command's eval and the answer to the command
const fire = (z) => { zoom = z; for (const fn of handlers) fn({ detail: z }); };
const key = async (z) => { fire(z); await null; fire(z); };
const here = () => ({ rows: radios.filter((r) => r.checked).map((r) => r.value), heading: $('text-size-sub').textContent });
""" + "\n__PIECES__\n" + r"""
(async () => {
  const out = {};
  out.of = [0.9, 1, 1.25, 1.1, 0.67, 2].map(textSizeOf);
  // a browser's tab: no idiographTextSize, nothing said
  fire(1.1);
  out.browser = said.slice();
  window.idiographTextSize = async (to) => { const z = typeof to === 'number' ? to : zoom; await key(z); return z; };
  // the window: View's Bigger Text from 100 to 110 per cent, then Actual Size
  said.length = 0;
  await key(1.1);
  out.step = { said: said.slice(), distinct: [...new Set(said)], now: here() };
  said.length = 0;
  await key(1);
  out.actual = { distinct: [...new Set(said)], now: here() };
  // a row picked in Settings: seen there, so not said, then a key straight after it is
  said.length = 0;
  await textSizeSet('large');
  out.picked = { said: said.slice(), now: here() };
  await key(1.5);
  out.after = { distinct: [...new Set(said)], now: here() };
  console.log(JSON.stringify(out));
})();
"""


def test_text_size_said(scratch: Path):
    print("\n292. The text size said when it changes, and the exact size in Settings")
    node = shutil.which("node")
    if not node:
        skip("292: the text size said, under node", "node is not on this machine")
        return
    js = support.text("family/static/shell.js")
    pieces = "\n".join([
        support.i18n_js(),
        line_of(js, "const TEXT_SIZES = "), line_of(js, "const textSizeOf = "), line_of(js, "const textPercent = "),
        whole(js, "function textSizeDraw("), "let textSizePick = null;", whole(js, "async function textSizeSet("),
        whole(js, "function textSizeSay("), line_of(js, "window.addEventListener('idiograph-zoom'"),
    ])
    ran = support.run_node(HARNESS.replace("__PIECES__", pieces), scratch, "a292-text-size.js")
    try:
        got = json.loads(ran.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        got = {}
    detail = ran.stderr[-400:] or json.dumps(got)
    check("292: a row is ticked at 0.9, 1 and 1.25 alone, and none between or beyond them",
          got.get("of") == ["small", "medium", "large", "", "", ""], detail)
    check("292: in a browser's tab, where the window is not there, a change of zoom says nothing",
          got.get("browser") == [], detail)
    step = got.get("step") or {}
    check("292: a step to 110% by the keys says the size on one line, twice told, once shown, with no row ticked and "
          "the heading carrying the size",
          len(step.get("distinct") or []) == 1 and "110%" in step["distinct"][0]
          and step.get("now", {}).get("rows") == [] and "110%" in step.get("now", {}).get("heading", ""), detail)
    actual = got.get("actual") or {}
    check("292: Actual Size says 100%, ticks Medium and the heading is the plain one again",
          len(actual.get("distinct") or []) == 1 and "100%" in actual["distinct"][0]
          and actual.get("now", {}).get("rows") == ["medium"] and "%" not in actual.get("now", {}).get("heading", "%"),
          detail)
    picked, after = got.get("picked") or {}, got.get("after") or {}
    check("292: a row picked in Settings says nothing, and the next step by the keys says its size",
          picked.get("said") == [] and picked.get("now", {}).get("rows") == ["large"]
          and len(after.get("distinct") or []) == 1 and "150%" in after["distinct"][0], detail)
