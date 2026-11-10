"""Area 281: the boards' words through the text layer (i18nthemes, 28 October 2026). The words of the PETs, GETs,
LPETs and Trajectories boards (themes.js, trajectories.js) and of the family's table (table.js) moved into their
catalogues, themes.json, trajectories.json and table.json, each sentence whole with its slots and each count's forms
by the count. These checks run the boards' own script in node with the catalogue the page loads, on an invented
study of birdwatchers, and read what a count, a slot or a list makes of each sentence that was joined from pieces
before the move: the status bar, a GET's count of participants, the delete card, the AI board's lines, a revision's
line and the participants whose changes came in. No fixture data is needed."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from . import support
from .support import check, skip

SCENARIO = r"""
const out = {};
TH.mode = 'pets';
out.pets = thStatusWords({ pets: 1, placed: 12, unplaced: 3, loose: 1, binned: 0, stacked: 2 }, false).map((p) => p[1]);
out.many = thStatusWords({ pets: 4, placed: 1, unplaced: 1, loose: 0, binned: 2, stacked: 0 }, false).map((p) => p[1]);
TH.mode = 'gets';
out.gets = thStatusWords({ pets: 1, placed: 5, unplaced: 0, loose: 0, binned: 1, stacked: 0 }, true).map((p) => p[1]);
TH.lgets = true;
out.lgets = thStatusWords({ pets: 3, placed: 5, unplaced: 0, loose: 0, binned: 0, stacked: 0 }, true).map((p) => p[1]);
TH.lgets = false; TH.mode = 'pets';
out.sum = thStatusSumText(thStatusSum({ pets: 2, placed: 7, unplaced: 2, loose: 0, binned: 1, stacked: 0 }, false));
out.selected = [thStatusSelected({ cards: new Set(['a']), groups: new Set(), stickies: new Set() }, false),
  thStatusSelected({ cards: new Set(['a', 'b']), groups: new Set(), stickies: new Set() }, true),
  thStatusSelected({ cards: new Set(['a']), groups: new Set(), stickies: new Set() }, true),
  thStatusSelected({ cards: new Set(['a']), groups: new Set(['g']), stickies: new Set() }, false)];
out.count = [gtCountText(1, 1), gtCountText(3, 8)];
out.grouping = [gtGrouping({ pets: 1, subs: 0 }), gtGrouping({ pets: 6, subs: 1 }), gtGrouping({ pets: 2, subs: 3 })];
TH.gets = { cases: [{ case: 'a', who: 'Ash' }, { case: 'b', who: 'Bryn' }, { case: 'c', who: 'Cole' }] };
out.took = [gtTookSaid(['a']), gtTookSaid(['a', 'b']), gtTookSaid(['a', 'b', 'c'])];
out.round = [thRoundHead({ items: [{ state: 'open' }] }, 1), thRoundHead({ items: [{ state: 'considered' }, { state: 'open' }] }, 2, true)];
out.pairs = [thPairWords({ same: true }), thPairWords({ unit: 'rows', gap: 1 }), thPairWords({ unit: 'rows', gap: 3 }),
  thPairWords({ unit: 's', gap: 12 }), thGapWords(30), thGapWords(60), thGapWords(120)];
out.cut = [gtCutLine(1), gtCutLine(4)];
console.log(JSON.stringify(out));
"""

TABLE = r"""
const st = { filters: {}, facetsFind: {}, facetsMore: new Set(), matchHead: [] };
const esc = (s) => String(s); const escAttr = (s) => String(s);
const g = { key: 'k', label: 'Birds', col: {}, choices: ['Wren', 'Robin', 'Jay', 'Finch', 'Rook', 'Crow'].map((v) => ({ value: v, label: v })) };
const counts = { Wren: 1, Robin: 2, Jay: 1, Finch: 1, Rook: 1, Crow: 1 };
const out = { closed: tbGroupHtml(g, counts, 0, st) };
st.facetsMore.add('k');
st.filters.k = ['Wren'];
out.open = tbGroupHtml(g, counts, 0, st);
console.log(JSON.stringify(out));
"""


def test_boards_words(scratch: Path):
    print("\n281. The boards' words through the text layer: in node the status bar's counts, a GET's participants, the "
          "AI board's grouping and cut lines, the participants whose changes came in, a review's round, a close pair and "
          "the table's Show more and Clear, each count's form picked by its count and each slot filled as before the "
          "move (28 October 2026)")
    node = shutil.which("node")
    if not node:
        skip("281: the boards' words in node", "no node on this machine")
        return
    script = scratch / "boards-words-281.js"
    script.write_text(support.i18n_js() + support.text("apps/idiograph/static/themes.js") + SCENARIO, encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=120)
    if run.returncode:
        check("281: the boards' script runs in node with the catalogue", False, run.stderr[-600:])
        return
    out = json.loads(run.stdout.strip().splitlines()[-1])
    check("281: the PETs status bar says one PET and four PETs, the stacked and the rest by their counts",
          out["pets"] == ["1 PET", "12 in PETs", "2 stacked", "0 set aside", "3 not placed", "1 in no PET"]
          and out["many"][:2] == ["4 PETs", "1 in PETs"], str(out["pets"]) + str(out["many"]))
    check("281: on GETs and LGETs the unit is the board's own, one GET and three LGETs",
          out["gets"][:2] == ["1 GET", "5 in GETs"] and out["lgets"][:2] == ["3 LGETs", "5 in LGETs"],
          str(out["gets"]) + str(out["lgets"]))
    check("281: the total heads its parts and the selection is said by its count and the board's unit",
          out["sum"] == ["10 ES: 7 in PETs, 0 stacked, 1 set aside, 2 not placed", "2 PETs"]
          and out["selected"] == ["1 ES selected", "2 cards selected", "1 card selected", "2 selected"],
          str(out["sum"]) + str(out["selected"]))
    check("281: a GET's count says one participant and eight participants by the study's total",
          out["count"] == ["1 of 1 participant", "3 of 8 participants"], str(out["count"]))
    check("281: grouping says one PET or six, and the sub-themes after them only when there are any",
          out["grouping"] == ["Grouping one PET", "Grouping 6 PETs and one sub-theme", "Grouping 2 PETs and 3 sub-themes"],
          str(out["grouping"]))
    check("281: the participants whose changes came in are one list in the language's way, and with their PETs",
          out["took"] == ["Brought in the changes to Ash's PETs.", "Brought in the changes to Ash and Bryn's PETs.",
                          "Brought in the changes to Ash, Bryn and Cole's PETs."], str(out["took"]))
    check("281: a review's round says its questions by their count, and a folded one how many he ticked",
          out["round"] == ["Round 1 · 1 question", "Round 2 · 2 questions · 1 ticked"], str(out["round"]))
    check("281: a close pair says one row, three rows, the seconds and the menu's gaps as before",
          out["pairs"] == ["Same passage", "1 row apart", "3 rows apart", "12 s apart", "30 seconds", "1 minute", "2 minutes"],
          str(out["pairs"]))
    check("281: the AI board's cut line says one statement or four",
          "the words of one statement, the lowest" in out["cut"][0] and "the words of 4 statements, the lowest" in out["cut"][1],
          str(out["cut"]))

    table = scratch / "table-words-281.js"
    table.write_text(support.table_js() + TABLE, encoding="utf-8")
    run = subprocess.run([node, str(table)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    if run.returncode:
        check("281: the family's table runs in node with the catalogue", False, run.stderr[-600:])
        return
    drawn = json.loads(run.stdout.strip().splitlines()[-1])
    check("281: a filter's group of six says Show more, and once whole Show less with Clear while a tick holds",
          'data-act="more">Show more</button>' in drawn["closed"] and 'data-act="clear">Clear</button>' not in drawn["closed"]
          and 'data-act="more">Show less</button>' in drawn["open"] and 'data-act="clear">Clear</button>' in drawn["open"],
          drawn["open"][:300])
