from __future__ import annotations

import workbook as wb_mod

from .support import check


def test_entries():
    print("\n11. Cell entry convention")
    check("entries split on a blank line",
          wb_mod.split_entries("one\n\ntwo\n\n\nthree") == ["one", "two", "three"])
    check("a textarea line per entry", wb_mod.field_to_lines("one\n\ntwo") == "one\ntwo")
    check("written back with a blank line between", wb_mod.lines_to_field("one\ntwo") == "one\n\ntwo")
    check("an empty field clears the cell", wb_mod.lines_to_field("  \n \n") is None)
    check("blank lines in the field are ignored", wb_mod.lines_to_field("one\n\n\ntwo") == "one\n\ntwo")
    check("timecodes at 75:12 render as MM:SS with hours flattened", wb_mod.timecode(3 * 3600 + 61, "75:12") == "181:01",
          wb_mod.timecode(3 * 3600 + 61, "75:12"))
    check("export timecodes stay HH:MM:SS", wb_mod.hhmmss(150) == "00:02:30")
