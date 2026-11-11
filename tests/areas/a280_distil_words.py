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
out.stand = [standLine([{ boards: 1 }], null), standLine([{ boards: 0 }, { boards: 2 }, { boards: 1 }], null),
  standLine([], null), standLine([], null, false)];
out.gets = [cardGetsLine({ themes: 1 }), cardGetsLine({ themes: 4 }), cardGetsLine({ lgets: true, themes: 2 }),
  cardGetsLine({ lgets: true }), cardGetsLine({ done: true })];
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

    pieces = [support.i18n_js(), whole("standLine"), whole("cardGetsLine"), whole("trimLine"), whole("trimShort"),
              whole("kqTitle"),
              whole("cbWhose"), whole("cbLineSaid")]
    script = scratch / "distil-words-280.js"
    script.write_text("\n".join(pieces) + SCENARIO, encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    out = json.loads(run.stdout) if run.returncode == 0 else None
    if not out:
        return check("280: the words run in node", False, run.stderr.strip()[:300])
    check("280: a project card's line counts its participants in the singular and the plural, and says when it has "
          "none or its folder is gone",
          out["stand"] == ["1 participant, 1 with PETs", "3 participants, 2 with PETs", "No participants yet",
                           "Its folder is not there"], str(out["stand"]))
    check("280: the GETs line names group themes or LGETs by their count, and not started and complete whole",
          out["gets"] == ["GETs: 1 group theme", "GETs: 4 group themes", "LGETs: 2 LGETs", "LGETs not started",
                          "GETs complete"], str(out["gets"]))
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
                           "1 of these statements you have reworded since you sent the copy. They keep their places on these "
                           "boards, in your current wording.",
                           "2 of these statements you have removed since you sent the copy. They keep their places on these "
                           "boards, in the other analyst's wording.",
                           "2 of these statements you have reworded since you sent the copy, and 1 you have removed. They keep "
                           "their places on these boards, in your current wording, and the removed ones in Curt's.",
                           "1 of these statements you have reworded since you sent the copy. Jess reworded 1 in the copy and "
                           "added 2. They keep their places on these boards, in your current wording, and the rest in Jess'."],
          str(out["match"]))
    check("280: its button counts the boards ticked, one and many", out["add"] == ["Add 1 board", "Add 5 boards", "Add 0 boards"],
          str(out["add"]))
