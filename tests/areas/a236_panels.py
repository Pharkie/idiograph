"""Area 236: columns stacked by dragging a heading (21 October 2026, the panels build, from Adam's backlog). A
heading let go over the other column's lower half stacks the two, the one dropped below, over its upper half
above, back in a gap it stands alone again, and the heading's menu has Stack under and Stand alone for the
keyboard. The stack is kept in config.json across a reload, and Reset widths puts every column back alone.
Every fixture is invented, a project on keeping bees."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import server as server_mod

from . import support
from .support import check, skip


def test_panels(scratch: Path):
    print("\n236. Columns stacked by dragging a heading: dropped on the other column's lower half or upper half, "
          "out to a gap again, the heading's menu, kept across a reload and undone by Reset widths")
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")

    def whole(name: str) -> str:
        at = app.index(f"function {name}(")
        return app[at:app.index("\n}\n", at) + 3]

    def line(start: str) -> str:
        at = app.index(start)
        return app[at:app.index("\n", at)]

    config = scratch / "a236-config.json"
    config.write_text(json.dumps({"interviewer": "Adam", "corpus": "", "gravity_reference": "", "corpus_exclude": []}),
                      encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.STATE_MEMORY)

    def reload() -> dict:
        return server_mod.merge_config(server_mod.saved_config())

    node = shutil.which("node")
    if not node:
        skip("236: the stacks in node", "node is not installed")
        return
    nat = app.index("const NOTES_PLACE_COLUMNS = {")
    pure = "\n".join([line("const COLUMNS = "), line("const COLUMN_WORDS = "), app[nat:app.index("};", nat) + 2],
                      line("const isColumns = "), line("const columnsSaid = "), line("const HIDEABLE_COLUMNS = "),
                      line("const STACK_SPLIT = "), line("const STACK_RANGE = "), line("const STACK_OTHER = "),
                      line("const stackTopOf = "), line("const stackExpand = ")]
                     + [whole(n) for n in ("columnsOf", "columnsHiddenOf", "stackSplitOf", "columnsLayout",
                                           "columnsShownSaid", "colsMoved", "colsStep", "stackUnits", "colsDropped",
                                           "colMenuItems", "colMenuChange", "stackResetChange")])
    script = scratch / "a236-stacks.js"
    script.write_text(support.i18n_js() + pure + r"""
const out = {};
const book = { statements_columns: ['statements', 'transcript', 'notes'] };
const lay = (cfg) => columnsLayout(cfg);
const apply = (cfg, change) => Object.assign({}, cfg, change || {});
// the notes' heading let go over the statements' lower half, then over their upper half
out.under = colsDropped(lay(book), 'notes', { kind: 'stack', onto: 'statements', half: 'lower' });
out.over = colsDropped(lay(book), 'notes', { kind: 'stack', onto: 'statements', half: 'upper' });
// the statements' heading let go over the notes' lower half: the stack where the notes stood
out.esUnder = colsDropped(lay(book), 'statements', { kind: 'stack', onto: 'notes', half: 'lower' });
const stacked = apply(book, out.under);
out.said = columnsShownSaid(lay(stacked));
out.saidOver = columnsShownSaid(lay(apply(book, out.over)));
// in the stack: the lower one over the upper half changes places, the lower one out to a gap stands alone there
out.swap = colsDropped(lay(stacked), 'notes', { kind: 'stack', onto: 'statements', half: 'upper' });
out.ownHalf = colsDropped(lay(stacked), 'notes', { kind: 'stack', onto: 'statements', half: 'lower' });
out.out = colsDropped(lay(stacked), 'notes', { kind: 'gap', before: null, shown: ['statements', 'transcript'] });
out.outLeft = colsDropped(lay(stacked), 'notes', { kind: 'gap', before: 'statements', shown: ['statements', 'transcript'] });
// the upper heading moves the whole stack, the transcript's its own column past it
out.moveStack = colsDropped(lay(stacked), 'statements', { kind: 'gap', before: null, shown: ['statements', 'transcript'] });
out.moveTx = colsDropped(lay(stacked), 'transcript', { kind: 'gap', before: 'statements', shown: ['statements', 'transcript'] });
// with a column hidden nothing stacks
out.hidden = colsDropped(lay(apply(book, { columns_hidden: ['notes'] })), 'statements', { kind: 'stack', onto: 'notes', half: 'lower' });
// the heading's menu
out.menu = {
  es: colMenuItems(lay(book), 'statements', false), en: colMenuItems(lay(book), 'notes', false),
  tx: colMenuItems(lay(book), 'transcript', false), narrow: colMenuItems(lay(book), 'notes', true),
  hidden: colMenuItems(lay(apply(book, { columns_hidden: ['statements'] })), 'notes', false),
  stackedEs: colMenuItems(lay(stacked), 'statements', false), stackedEn: colMenuItems(lay(stacked), 'notes', false) };
out.menuUnder = colMenuChange(lay(book), 'statements', 'under');
out.menuAlone = colMenuChange(lay(stacked), 'notes', 'alone');
out.menuAloneSide = colMenuChange(lay(book), 'notes', 'alone');
// Reset widths: every column back alone, the statements above for the next stack, the divider at half
out.reset = stackResetChange(apply(stacked, { stack_top: 'notes', stack_split: 0.3 }));
out.resetNone = stackResetChange(book);
console.log(JSON.stringify(out));
""", encoding="utf-8")
    ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    try:
        o = json.loads(ran.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        o = {}
    said = (ran.stdout + ran.stderr)[:600]

    check("236: in node, the notes' heading let go over the statements' lower half stacks them under the statements, "
          "over the upper half above them, and the statements let go over the notes' lower half stand under the notes "
          "where the notes stood",
          o.get("under") == {"columns_stacked": True, "stack_top": "statements",
                             "statements_columns": ["statements", "notes", "transcript"]}
          and o.get("over") == {"columns_stacked": True, "stack_top": "notes",
                                "statements_columns": ["notes", "statements", "transcript"]}
          and o.get("esUnder") == {"columns_stacked": True, "stack_top": "notes",
                                   "statements_columns": ["transcript", "notes", "statements"]}
          and o.get("said") == "statements over notes, transcript" and o.get("saidOver") == "notes over statements, transcript",
          said)
    check("236: in node, in a stack the lower heading over the upper half changes places, over its own half does "
          "nothing, let go in a gap stands alone there, the upper heading moves the stack whole and the transcript "
          "moves past it, and with a column hidden nothing stacks",
          o.get("swap") == {"stack_top": "notes"} and o.get("ownHalf") is None
          and o.get("out") == {"columns_stacked": False, "statements_columns": ["statements", "transcript", "notes"]}
          and o.get("outLeft") == {"columns_stacked": False, "statements_columns": ["notes", "statements", "transcript"]}
          and o.get("moveStack") == {"statements_columns": ["transcript", "statements", "notes"]}
          and o.get("moveTx") == {"statements_columns": ["transcript", "statements", "notes"]}
          and o.get("hidden") is None, said)
    m = o.get("menu") or {}
    check("236: in node, the heading's menu has Stack under the other column while the two stand side by side and "
          "Stand alone while they are stacked, nothing for the transcript, at 800px and below or with a column hidden, "
          "Stack under putting this column under the other and Stand alone undoing the stack",
          m.get("es") == [{"act": "under", "words": "Stack under Exploratory notes"}]
          and m.get("en") == [{"act": "under", "words": "Stack under Experiential statements"}]
          and m.get("tx") == [] and m.get("narrow") == [] and m.get("hidden") == []
          and m.get("stackedEs") == m.get("stackedEn") == [{"act": "alone", "words": "Stand alone"}]
          and o.get("menuUnder") == {"columns_stacked": True, "stack_top": "notes",
                                     "statements_columns": ["transcript", "notes", "statements"]}
          and o.get("menuAlone") == {"columns_stacked": False} and o.get("menuAloneSide") is None, said)

    # ── where the two would meet (panels2): the gap between two blocks of words nearest the column's middle, so
    # the line and the half a drop takes never cut through a statement, on a made-up column of rectangles
    split_js = scratch / "a236-split.js"
    sb = app.index("const SPLIT_BLOCKS = ")
    split_js.write_text(support.i18n_js() + app[sb:app.index("';\n", sb) + 3] + whole("colsSplit") + r"""
const block = (top, bottom, left = 20, right = 340, parked = false) => ({
  closest: (s) => (parked && s === '#es-park' ? {} : null),
  getBoundingClientRect: () => ({ top, bottom, left, right, width: right - left, height: bottom - top }),
});
let blocks = [];
global.document = { querySelectorAll: () => blocks };
const zone = { left: 20, right: 340, top: 100, bottom: 1000 };
const out = {};
// a heading, three statements whose middle one runs over the column's middle, the card's foot
blocks = [block(100, 140), block(200, 420), block(436, 610), block(626, 900), block(910, 960)];
out.gap = colsSplit(zone);
// two that touch are one block, a parked card and a neighbour column's words count for nothing
blocks = [block(100, 140), block(200, 540), block(540, 900), block(560, 580, 20, 340, true), block(500, 520, 400, 700)];
out.merged = colsSplit(zone);
// nothing but one block from end to end: the middle
blocks = [block(100, 1000)];
out.none = colsSplit(zone);
console.log(JSON.stringify(out));
""", encoding="utf-8")
    ran2 = subprocess.run([node, str(split_js)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    try:
        sp = json.loads(ran2.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        sp = {}
    check("236: in node, the line where the two would meet, and the half a drop takes, fall in the gap between two "
          "statements nearest the column's middle, blocks that touch counting as one and a parked card or a "
          "neighbour column's words as nothing, and the middle when there is no gap",
          sp.get("gap") == 618 and sp.get("merged") == 170 and sp.get("none") == 550,
          (ran2.stdout + ran2.stderr)[:600])

    try:
        server_mod.CONFIG_PATH = config
        # ── a stack kept across a reload: the drop's settings saved as the page sends them, read back as a new page reads
        server_mod.api_settings(o.get("over") or {"columns_stacked": True})
        server_mod.api_settings({"stack_split": 0.35})
        back = reload()
        check("236: a stack made by a drop is kept in config.json and read back after a reload, the notes above, the "
              "order and the divider's place with it",
              back["columns_stacked"] is True and back["stack_top"] == "notes"
              and back["statements_columns"] == ["notes", "statements", "transcript"] and back["stack_split"] == 0.35,
              json.dumps({k: back[k] for k in ("columns_stacked", "stack_top", "statements_columns", "stack_split")}))
        server_mod.api_settings({"stack_top": "transcript"})
        on_disk = json.loads(config.read_text(encoding="utf-8"))
        config.write_text(json.dumps({"interviewer": "Adam", "stack_top": 7}), encoding="utf-8")
        odd = reload()
        check("236: a column above that is neither the statements nor the notes leaves the file as it was, and a "
              "settings file from before, or holding anything else, reads as the statements above",
              on_disk.get("stack_top") == "notes" and odd["stack_top"] == "statements"
              and server_mod.defaults()["stack_top"] == "statements", json.dumps([on_disk.get("stack_top"), odd["stack_top"]]))

        # ── Reset widths: every edge back for the screen and every column back alone
        config.write_text(json.dumps({"interviewer": "Adam"}), encoding="utf-8")
        server_mod.api_settings({"columns_stacked": True, "stack_top": "notes", "stack_split": 0.3,
                                 "column_widths": {"screen": "1920", "widths": {"left": 60, "stack": 420}}})
        server_mod.api_settings(o.get("reset") or {})
        server_mod.api_settings({"column_widths": {"screen": "1920", "widths": None}})
        after = reload()
        check("236: Reset widths puts every column back alone, the statements above for the next stack, the divider at "
              "half and the screen's widths gone, and asks nothing of a screen with no stack",
              o.get("reset") == {"columns_stacked": False, "stack_top": "statements", "stack_split": 0.5}
              and o.get("resetNone") == {} and after["columns_stacked"] is False and after["stack_top"] == "statements"
              and after["stack_split"] == 0.5 and after["column_widths"] == {}
              and "const stack = stackResetChange(viewConfig());" in whole("widthsReset")
              and "cfg.columns_stacked === true" in whole("drawWidthsReset"),
              json.dumps({k: after[k] for k in ("columns_stacked", "stack_top", "stack_split", "column_widths")}))
    finally:
        server_mod.CONFIG_PATH, server_mod.STATE_MEMORY = kept
