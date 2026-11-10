from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import openpyxl

import workbook as wb_mod

from . import support
from .support import check, skip
import idiograph_cli

# the demo's invented case Juno, its turn 15 about the morning walk with the dog
TURN = 15
INSERT = '"she knows every inch of it, she [the dog] could do it without me"'
BOTH = '"Out of the door … she [the dog] could do it without me"'


def test_quote_inserts(scratch):
    print("\n216. A key quote's clarifying insert in square brackets (20 October, an agent's write refused): the "
          "insert passes as the analyst's, the rest of the quote found in order in the turn, through turn write, "
          "a sibling holding one never blocking a write, and the page's marks and the GETs print finding the quote")
    import cli
    import gets_print
    import server as server_mod

    root = scratch / "a216-root"
    shutil.rmtree(root, ignore_errors=True)
    pristine = support.DEMO_PRISTINE
    (root / "Juno" / "Working").mkdir(parents=True)
    book = root / "Juno" / "Juno - EN & ES.xlsx"
    shutil.copy2(pristine / "Juno - EN & ES.xlsx", book)
    for side in (pristine / "Working").glob("Juno - *"):
        shutil.copy2(side, root / "Juno" / "Working" / side.name)
    (root / "idiograph-project.json").write_text(json.dumps({"name": "Dogs, a scratch project", "agents": {"allowed": True, "at": "2026-10-20T09:00:00"}}),
                                                 encoding="utf-8")
    config = scratch / "a216-config.json"
    config.write_text(json.dumps({"root": str(root), "interviewer": "Adam", "corpus": "", "gravity_reference": "",
                                  "corpus_exclude": []}), encoding="utf-8")

    def spec(name, value):
        path = scratch / f"a216-{name}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return str(path)

    def write(name, pairs):
        return cli.run(["--root", str(root), "--config", str(config), "turn", "write", "Juno", "Initial", str(TURN),
                        "--from", spec(name, {"pairs": pairs, "request": "a216"})])

    def quotes():
        wb = openpyxl.load_workbook(book, read_only=True)
        ws = wb["Initial"]
        cell = ws.cell(TURN, wb_mod.detect_columns(ws)["kq"]).value
        wb.close()
        return wb_mod.quote_entries(cell)

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = config, str(root), {"recent": []}
        first = {"statement": "The dog's walk without him", "quote": INSERT}
        code, out, err = write("insert", [first])
        check("216: a quote with a clarifying insert is written, the insert kept as he typed it",
              code == 0 and quotes() == [INSERT], f"{code} {err.strip()[:300]} {quotes()}")
        second = {"statement": "Walked by the dog", "quote": "there are mornings where I genuinely think she is walking me"}
        code, out, err = write("sibling", [first, second])
        check("216: a write beside a sibling quote holding an insert, sent back unchanged, is not blocked",
              code == 0 and quotes() == [INSERT, '"there are mornings where I genuinely think she is walking me"'],
              f"{code} {err.strip()[:300]} {quotes()}")
        code, out, err = write("both", [first, second, {"statement": "Out and back", "quote": BOTH}])
        check("216: an ellipsis and an insert in one quote pass", code == 0 and quotes()[-1] == BOTH,
              f"{code} {err.strip()[:300]}")
        before = book.read_bytes()
        for name, quote in (("order", '"she [the dog] could do it without me … Out of the door"'),
                            ("absent", '"she [the dog] could do it without a lead"'),
                            ("missing", '"she knows [the dog] every inch of the park"')):
            code, out, err = write(name, [first, {"statement": "Wrong", "quote": quote}])
            check(f"216: a quote whose pieces round an insert are {name} is still refused, nothing written",
                  code == 1 and "is not in the turn's words as they stand" in err and book.read_bytes() == before,
                  f"{code} {err.strip()[:300]}")
        # a sibling quote the turn no longer holds, its words corrected in Excel since, is kept, not re-checked
        wb = openpyxl.load_workbook(book)
        ws = wb["Initial"]
        cols = wb_mod.detect_columns(ws)
        ws.cell(TURN, cols["kq"]).value = '"she could do it without me"\n\n"a line since corrected away"'
        wb.save(book)
        wb.close()
        code, out, err = write("stale", [{"statement": "The dog's walk without him", "quote": "she could do it without me"},
                                         {"statement": "Corrected", "quote": "a line since corrected away"}])
        check("216: a sibling quote already on the turn is not checked again, so it never blocks a write",
              code == 0, f"{code} {err.strip()[:300]}")
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    # the CLI's own finder and the GETs print's pieces
    text = "Out of the door, left. She knows every inch of it, she could do it without me."
    check("216: quote_in passes an insert and refuses the same words out of order",
          idiograph_cli.quote_in('"my rational [mind] tells me"', "my rational side tells me")
          and idiograph_cli.quote_in('"than I let him [pilot] know"', "than I let him know")
          and not idiograph_cli.quote_in('"tells me [mind] my rational"', "my rational side tells me"))
    check("216: the GETs print finds a quote with an insert piece by piece and bolds the turn's own words",
          gets_print.pieces('"she [the dog] could do it without me."') == ["she", "could do it without me"]
          and [w for w, bold in gets_print.around(text, INSERT) if bold]
          == ["She knows every inch of it, she", "could do it without me"],
          json.dumps(gets_print.around(text, INSERT)))

    # the page's marks in the passage, quote.js in node
    node = shutil.which("node")
    if not node:
        skip("216: the page's marks of a quote with an insert", "no node on this machine")
        return
    script = scratch / "a216-marks.js"
    script.write_text(support.text("family/static/quote.js") + r"""
const T = 'Out of the door, left. She knows every inch of it, she could do it without me.';
const cut = (q) => quoteSpans(q, T).map((s) => T.slice(s.start, s.end));
console.log(JSON.stringify({
  insert: cut('"she knows every inch of it, she [the dog] could do it without me"'),
  both: cut('"Out of the door … she [the dog] could do it without me"'),
  tail: cut('"could do it without me [laughs]."'),
  order: cut('"she [the dog] could do it without me … Out of the door"'),
}));
""", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        check("216: the marks run in node", False, run.stderr.strip()[:300])
        return
    out = json.loads(run.stdout)
    check("216: the page marks a quote with an insert round it, each piece of the turn's words on its own, and "
          "an insert at its end or pieces out of order as before",
          out["insert"] == ["She knows every inch of it, she", "could do it without me"]
          and out["both"] == ["Out of the door", "She", "could do it without me"]
          and out["tail"] == ["could do it without me"] and out["order"] == [], json.dumps(out))
