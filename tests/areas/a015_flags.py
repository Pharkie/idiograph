from __future__ import annotations

import json

import rounds as rounds_mod

from .support import check


def test_flags(scratch):
    print("\n14. Flags a progress file keeps from before, untouched and unread")
    old = {"version": 1, "rows": {}, "rounds": {}, "days": {}, "last": None}
    work = scratch / "flags" / "book.xlsx"
    work.parent.mkdir(parents=True, exist_ok=True)
    rounds_mod.progress_path(work).parent.mkdir(parents=True, exist_ok=True)
    rounds_mod.progress_path(work).write_text(json.dumps(old), encoding="utf-8")
    loaded = rounds_mod.load_progress(work)
    check("a sidecar written before flagging loads with an empty list", loaded["flags"] == [],
          repr(loaded["flags"]))

    loaded["flags"] = ["Initial:12", "2d:40"]
    rounds_mod.save_progress(work, loaded)
    check("flags a file already holds survive a write and a read, in their order",
          rounds_mod.load_progress(work)["flags"] == ["Initial:12", "2d:40"])
