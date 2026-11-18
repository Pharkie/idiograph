"""Area 280: Idiograph's own words in the catalogue (i18ndistil, 28 October 2026, the text layer's build 3).
distil.js, the statements screen, Home's Idiograph cards and pickers and the cards it opens, takes every word it
shows from apps/idiograph/static/i18n/en/distil.json through t(). What is checked is what the words do once they
are messages: a count picks its form and fills its slots, a sentence once joined from pieces reads as it did, a
list of rounds or statements goes through tList, and the PETs limit's line names its ordinal whole, run in node
on the page's own functions with the text layer before them, as the page loads it."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from . import support
from .support import check, skip

SCENARIO = r"""
const out = {};
out.stand = [standLine([{ boards: 1 }]), standLine([]), standLine([], false)];
// a ring's or a bar's words (homecardbuild): its count in the singular and the plural, and the researcher's mark
out.gets = [stageWords('pets', { decided: 1, total: 1, complete: null }), stageWords('es', { decided: 3, total: 9, complete: null }),
  stageWords('gets', { decided: 0, total: 4, complete: null }), stageWords('pets', { decided: 54, total: 54, complete: { at: 'x' } })];
out.trim = [trimLine({ count: 1, from: '00:10', to: '' }), trimLine({ count: 2, from: '00:10', to: '00:40', direction: 'before' }),
  trimLine({ count: 4, from: '01:00', to: '03:15', direction: 'after' }), trimShort({ count: 2, direction: 'before' }),
  trimShort({ count: 5, direction: 'after' })];
out.kq = [kqTitle([0]), kqTitle([0, 2]), kqTitle([1, 3, 4])];
// a copy coming back's line under a participant's boards (copyback, 6 November 2026), each statement counted once
const said = (key, kind, wording) => ({ key, kind, wording });
out.match = [cbLineSaid({ boards: [{ statements: 1, not_matched: [] }] }, 'Curt'),
  cbLineSaid({ boards: [{ statements: 6, not_matched: [] }, { statements: 6, not_matched: [] }] }, 'Curt'),
  cbLineSaid({ boards: [{ statements: 4, not_matched: [said('a', 'edited', 'yours')] }, { statements: 4, not_matched: [said('a', 'edited', 'yours')] }] }, 'Curt'),
  cbLineSaid({ boards: [{ statements: 4, not_matched: [said('a', 'gone', 'copy'), said('b', 'missing', 'copy')] }] }, ''),
  cbLineSaid({ boards: [{ statements: 9, not_matched: [said('a', 'differs', 'yours'), said('b', 'differs', 'yours'), said('c', 'missing', 'copy')] }] }, 'Curt'),
  cbLineSaid({ boards: [{ statements: 9, not_matched: [said('a', 'edited', 'yours'), said('b', 'own', 'yours'), said('c', 'own', 'copy'), said('d', 'own', 'copy')] }] }, 'Jess')];
out.add = [1, 5, 0].map((n) => t('distil.copy.add_n', { n }));
console.log(JSON.stringify(out));
"""


def test_distil_words(scratch: Path):
    print("\n280. Idiograph's own words in the catalogue: counts pick their form and fill their slots, the sentences once "
          "joined from pieces read as they did, lists through tList, and the PETs limit's line whole (28 October 2026)")
    node = shutil.which("node")
    if not node:
        return skip("280: the words in node", "no node on this machine")
    js = support.text("apps/idiograph/static/distil.js")
    lines = js.splitlines()

    def whole(name):
        return f"function {name}(" + js.split(f"function {name}(", 1)[1].split("\n}", 1)[0] + "\n}"

    def const(name):
        start = next(i for i, line in enumerate(lines) if line.startswith(f"const {name} = "))
        end = start
        while not lines[end].rstrip().endswith(";"):
            end += 1
        return "\n".join(lines[start:end + 1])

    pieces = [support.i18n_js(), whole("standLine"), "const stageBegun = (c) => !!c && (Number(c.decided) > 0 || !!c.complete);", whole("stageCount"),
              whole("stageWords"), whole("trimLine"), whole("trimShort"),
              whole("kqTitle"),
              whole("cbWhose"), whole("cbLineSaid")]
    script = scratch / "distil-words-280.js"
    script.write_text("\n".join(pieces) + SCENARIO, encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    out = json.loads(run.stdout) if run.returncode == 0 else None
    if not out:
        return check("280: the words run in node", False, run.stderr.strip()[:300])
    check("280: a project card's line says when it has no participant or its folder is gone, and nothing beside its "
          "rings", out["stand"] == ["", "No participants yet", "Its folder is not there"], str(out["stand"]))
    check("280: a ring's or a bar's words count in the singular and the plural, say Not started whole, and put the "
          "researcher's mark first",
          out["gets"] == ["1 of 1 statement placed. Not marked complete.", "3 of 9 passages decided", "Not started",
                          "Complete. 54 of 54 statements placed."], str(out["gets"]))
    check("280: a cut says its rows, which passages and when, in the singular and the plural, either way",
          out["trim"] == ["Cut 1 row: this passage only, 00:10.", "Cut 2 rows: this passage and the one before it, 00:10 to 00:40.",
                          "Cut 4 rows: this passage and the 3 after it, 01:00 to 03:15.", "Cut this passage and one before",
                          "Cut this passage and 4 after"], str(out["trim"]))
    check("280: a quote's mark names its statement, or its statements as a list through tList",
          out["kq"] == ["Experiential statement 1", "Experiential statements 1 and 3", "Experiential statements 2, 4 and 5"],
          str(out["kq"]))
    check("280: a copy coming back says once under a participant's boards how its statements came, one and many, each "
          "counted once across the boards, whose wording each keeps, the other analyst's with no name",
          out["match"] == ["Its statement matches yours.", "All 6 statements match yours.",
                           "Since you sent the copy, you have reworded 1 of these statements. They keep their places on these "
                           "boards and show your current wording.",
                           "Since you sent the copy, you have removed 2 of these statements. They keep their places on these "
                           "boards and show the other analyst's wording.",
                           "Since you sent the copy, you have reworded 2 of these statements and removed 1. They keep "
                           "their places on these boards and show your current wording. The removed ones show Curt's wording.",
                           "Since you sent the copy, you have reworded 1 of these statements. Jess reworded 1 in the copy and "
                           "added 2. They keep their places on these boards and show your current wording. The rest show Jess' wording."],
          str(out["match"]))
    check("280: its button counts the boards ticked, one and many", out["add"] == ["Add 1 board", "Add 5 boards", "Add 0 boards"],
          str(out["add"]))
