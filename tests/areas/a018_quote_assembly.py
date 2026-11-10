from __future__ import annotations

import json
import shutil

from . import support
from .support import check, skip


def test_quote_assembly(scratch):
    print("\n17. Building one key quote from several pieces")
    import subprocess
    node = shutil.which("node")
    if not node:
        return skip("quote assembly", "no node on this machine to run the rule")
    script = scratch / "quote-check.js"
    script.write_text(
        "const q = require(process.argv[2]);\n"
        "const text = 'looking at the instruments and then I saw the speed we were going';\n"
        "const out = {\n"
        "  ordered: q.assembleQuote([{start: 42, end: 65}, {start: 0, end: 26}], text),\n"
        "  overlap: q.assembleQuote([{start: 0, end: 14}, {start: 8, end: 26}], text),\n"
        "  touching: q.assembleQuote([{start: 0, end: 10}, {start: 11, end: 26}], text),\n"
        "  one: q.assembleQuote([{start: 0, end: 26}], text),\n"
        "  three: q.assembleQuote([{start: 0, end: 7}, {start: 27, end: 35}, {start: 42, end: 65}], text),\n"
        "  empty: q.assembleQuote([], text),\n"
        "  spaces: q.assembleQuote([{start: 0, end: 27}], text),\n"
        "  first: q.quoteTarget([{es: '', kq: ''}], -1),\n"
        "  filled: q.quoteTarget([{es: 'a', kq: '\"one\"'}], 0),\n"
        "  undone: q.quoteOut([{es: 'a', kq: '\"one\"'}, {es: 'b', kq: '\"two\"'}], 1, '\"two\"'),\n"
        "  undoneAdded: q.quoteOut([{es: 'a', kq: '\"one\"'}, {es: '', kq: '\"two\"'}], 1, '\"two\"'),\n"
        "  undoneMissing: q.quoteOut([{es: 'a', kq: '\"one\"'}], 0, '\"never added\"'),\n"
        "};\n"
        "console.log(JSON.stringify(out));\n", encoding="utf-8")
    quote_js = support.source("family/static/quote.js")
    run = subprocess.run([node, str(script), str(quote_js)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("the quote rule runs", False, run.stderr.strip()[:200])
    out = json.loads(run.stdout)
    check("pieces sort back into transcript order whatever order they were picked",
          out["ordered"] == '"looking at the instruments … the speed we were going"', out["ordered"])
    check("overlapping pieces become one", out["overlap"] == '"looking at the instruments"', out["overlap"])
    check("pieces with only a space between them become one",
          out["touching"] == '"looking at the instruments"', out["touching"])
    check("a single piece carries no ellipsis", out["one"] == '"looking at the instruments"', out["one"])
    check("three pieces take two ellipses",
          out["three"] == '"looking … and then … the speed we were going"', out["three"])
    check("nothing selected is no quote", out["empty"] == "", repr(out["empty"]))
    check("a trailing space is trimmed off the piece",
          out["spaces"] == '"looking at the instruments"', out["spaces"])
    check("the first quote goes into the key quote of the one pair there (198)",
          out["first"] == {"place": 0, "added": False, "old": ""}, repr(out["first"]))
    check("a quote for a pair that has one goes into a pair of its own under the last, never over the quote there, as "
          "it did until 14 October, when it replaced it in place (136), and again since 16 October (153)",
          out["filled"] == {"place": 1, "added": True, "old": ""}, repr(out["filled"]))
    check("undo takes out exactly the quote it put in, from its pair",
          out["undone"] == {"place": 1}, repr(out["undone"]))
    check("undo finds a pair with no statement that holds the quote, the pair q added (153)",
          out["undoneAdded"] == {"place": 1}, repr(out["undoneAdded"]))
    check("a quote that is not there leaves the pairs alone",
          out["undoneMissing"] is None, repr(out["undoneMissing"]))
