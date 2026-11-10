from __future__ import annotations

import json
from pathlib import Path

from . import support
from .support import check
import idiograph_routes


def test_minimap(scratch):
    print("\n154. The minimap, 16 October, Adam's decision on a tester's feedback: the whole sheet at a glance beside the "
          "statements screen's transcript with the done marks, the key quotes, the current passage, the rounds and the "
          "part in view, a click moving the column and a drag on the box scrolling it, a tick in View and in Settings kept "
          "in step, on by default, and giving way where the column has no room. A strip down the column's right until 17 "
          "October, a small card at its bottom right since, and since 17 October, later, one column in one card, Auto, On "
          "or Off (area 169). Since the test review of 18 October its markup, look and words are review shots, its acts "
          "in node are area 169's, and the setting saved and read back and a press that never moves his place stay")
    import server as server_mod

    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")

    def whole(name):
        """A function of app.js whole, a one-line one included, or "" when there is none."""
        if f"function {name}(" not in app:
            return ""
        at = app.index(f"function {name}(")
        if app[max(0, at - 6):at] == "async ":
            at -= 6
        first = app[at:app.index("\n", at)]
        if first.rstrip().endswith("}") and first.count("{") == first.count("}"):
            return first
        return app[at:app.index("\n}", at) + 2]

    body = lambda name: whole(name).split("{", 1)[1] if whole(name) else ""

    # ── A. the key: on by default and when absent, saved and read back
    check("154: minimap is on in the server's defaults and the Mac app's shipped settings, Auto since 17 October, later "
          "(169), and a settings file without it reads Auto, the old tick's true Auto, its false Off, and On and Off kept",
          server_mod.defaults().get("minimap") == "auto" and server_mod.shipped_config()["minimap"] == "auto"
          and idiograph_routes.MINIMAP_MODES == ("auto", "on", "off")
          and server_mod.merge_config({"interviewer": "Wren"})["minimap"] == "auto"
          and server_mod.merge_config({"minimap": False})["minimap"] == "off"
          and server_mod.merge_config({"minimap": True, "larger_passage": False})["minimap"] == "auto"
          and server_mod.merge_config({"minimap": "on"})["minimap"] == "on"
          and server_mod.merge_config({"minimap": "sometimes"})["minimap"] == "auto")
    saved = server_mod.CONFIG_PATH
    server_mod.CONFIG_PATH = scratch / "minimap-154-config.json"
    try:
        server_mod.CONFIG_PATH.write_text(json.dumps({"interviewer": "Wren", "round_minutes": 12}), encoding="utf-8")
        before = server_mod.config()
        off = server_mod.api_settings({"minimap": "off"})["config"]
        off_disk = json.loads(server_mod.CONFIG_PATH.read_text(encoding="utf-8"))
        kept = server_mod.api_settings({"interviewer": "Wren", "larger_passage": False})["config"]
        back_off = server_mod.config()
        on = server_mod.api_settings({"minimap": "on"})["config"]
        on_disk = json.loads(server_mod.CONFIG_PATH.read_text(encoding="utf-8"))
        back_on = server_mod.config()
        old_page = server_mod.api_settings({"minimap": True})["config"]["minimap"]
        old_off = server_mod.api_settings({"minimap": False})["config"]["minimap"]
    finally:
        server_mod.CONFIG_PATH = saved
    check("154: the View menu's one key saves alone and keeps every other, a save without it leaves it as it was, and "
          "the file reads back the same, a page from before the choice sending its tick, true read as Auto and false as Off",
          before["minimap"] == "auto" and off["minimap"] == "off" and off_disk["minimap"] == "off"
          and off_disk["round_minutes"] == 12 and off_disk["interviewer"] == "Wren"
          and kept["minimap"] == "off" and kept["larger_passage"] is False and back_off["minimap"] == "off"
          and on["minimap"] == "on" and on_disk["minimap"] == "on" and back_on["minimap"] == "on"
          and on_disk["larger_passage"] is False and old_page == "auto" and old_off == "off",
          f"{off_disk.get('minimap')} {kept.get('minimap')} {on_disk.get('minimap')} {old_page} {old_off}")

    # ── C. the pointer taken on the card's map, a press scrolling the column and never moving his place
    check("154: the pointer is taken on the card's map, and a press, a drag or letting go scrolls the column and never "
          "moves the current passage",
          all(f"$('minimap-area').addEventListener('{ev}', {fn_});" in app for ev, fn_ in (
              ("pointerdown", "minimapDown"), ("pointermove", "minimapMove"), ("pointerup", "minimapUp"),
              ("pointercancel", "minimapUp"), ("lostpointercapture", "minimapUp")))
          and not any("goTo(" in body(n) for n in ("minimapDown", "minimapMove", "minimapUp", "minimapTo")))
