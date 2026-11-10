from __future__ import annotations

from . import support
from .support import check


def test_new_surface():
    print("\n18. The endpoints and the controls the new work added")
    import server as server_mod
    for route in ("/api/audio", "/api/suggest", "/api/haiku", "/api/trim",
                  "/api/key", "/api/key-status"):
        check(f"{route} is served", route in server_mod.ROUTES)
    page = support.page_text()
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    css = support.text("family/static/style.css", "apps/idiograph/static/distil.css")
    check("the player follows the turn, cued and never played on its own",
          "loadAudio(row.sheet, row.seconds)" in js and "function cueAudio(" in js
          and "cueAudio(cueSeconds)" in js,
          "a turn becoming current cues the recording to its timecode")
    check("the away seconds are counted and sent with every save",
          "visibilitychange" in js and "away: awayTally()" in js and "awayReset()" in js)
    check("the trim sits in the row's menu and on t, always behind the one confirm card",
          "data-menu" in js and ".row-menu-open" in css and 'id="trim"' in page
          and "act: 'cut', direction," in js and "contextmenu" in js
          and "trimKey(); }" in js and "confirmTrim(row, at < onSheet.length / 2 ? 'before' : 'after', true);" in js,
          "the hover control, a right-click and t all lead to the card, nothing cuts without it")
    applier = js.split("async function trimApply(", 1)[1].split("\n}", 1)[0]
    check("the case is reopened after a trim, so the column and the rounds are rebuilt",
          "if (data.land) await reloadInPlace(data.land);" in applier
          and "else await openCase(S.data.path);" in applier,
          "in place on the turn the server names, or opened afresh in front of an older server")
