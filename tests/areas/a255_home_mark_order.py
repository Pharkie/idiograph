"""Which way in Idiograph's Home mark plays (23 October 2026, Adam: one of a random set, different each time): the
next of a shuffled order kept in the page's own storage, so every way plays once before any plays again, the same
one never twice running, and the order carries on across a reload. A storage that will not answer still gives one
of the set. Run in node on the shell's own homeMarkNext, with a storage of its own standing in for the page's."""
from __future__ import annotations

import json
import shutil
import subprocess

from . import support
from .support import check, skip


def test_home_mark_order(scratch):
    print("\n255. Home's mark: every way in plays once before any repeats, never the same twice running, the order "
          "kept across a reload")
    js = support.source("family/static/shell.js").read_text(encoding="utf-8")
    start, end = js.find("const HOME_MARK_ORDER_KEY"), js.find("function homeMarkPlay(")
    if start < 0 or end < start:
        return check("the shell picks the next way in with homeMarkNext", False, "homeMarkNext not found before homeMarkPlay")
    node = shutil.which("node")
    if not node:
        return skip("the order of the ways in, in node", "no node on this machine")
    script = scratch / "home-mark-order.js"
    script.write_text(js[start:end] + r"""
// a page's storage, kept across "reloads": each open below calls homeMarkNext afresh with the same store
const kept = {};
const store = { getItem: (k) => (k in kept ? kept[k] : null), setItem: (k, v) => { kept[k] = String(v); } };
let seed = 7;
const rand = () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
const plays = [];
for (let i = 0; i < HOME_MARK_WAYS.length * 40; i++) plays.push(homeMarkNext(HOME_MARK_WAYS, store, rand));
// a store that throws, as a private window's can
const broken = { getItem: () => { throw new Error('no'); }, setItem: () => { throw new Error('no'); } };
const fallback = homeMarkNext(HOME_MARK_WAYS, broken, rand);
// a way no longer in the set, left in an old order, is passed over
kept[HOME_MARK_ORDER_KEY] = JSON.stringify({ left: ['gone', 'kiss'], last: 'race' });
const afterOld = homeMarkNext(HOME_MARK_WAYS, store, rand);
console.log(JSON.stringify({ ways: HOME_MARK_WAYS, plays, fallback, afterOld, kept: JSON.parse(kept[HOME_MARK_ORDER_KEY]) }));
""", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("homeMarkNext runs in node", False, run.stderr.strip()[:300])
    out = json.loads(run.stdout)
    ways, plays, n = out["ways"], out["plays"], len(out["ways"])
    check("the set is seven, the spin among them", n == 7 and "spin" in ways, str(ways))
    rounds = [plays[i:i + n] for i in range(0, len(plays), n)]
    check("every way plays once in each round of seven, before any plays again",
          all(sorted(r) == sorted(ways) for r in rounds), str(rounds[:3]))
    check("the same way never plays twice running, across the turn of a round too",
          all(a != b for a, b in zip(plays, plays[1:])))
    check("the rounds are not all in one order", len({tuple(r) for r in rounds}) > 1)
    check("a storage that will not answer still gives one of the set", out["fallback"] in ways, str(out["fallback"]))
    check("an old order keeps its place, a way no longer in the set passed over",
          out["afterOld"] == "kiss" and out["kept"] == {"left": [], "last": "kiss"}, f"{out['afterOld']} {out['kept']}")
