from __future__ import annotations

import json
import shutil

import rounds as rounds_mod

from . import support
from .support import DEMO_SHEET, check, demo_copy, skip
import idiograph_routes


def test_turn_bar(scratch):
    print("\n54. The session clock stands still while he is away and resets (130), and the turn's buttons (131)")
    import subprocess
    import server as server_mod

    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0]
    keydown = support.keydown_text(app)

    # ── A. the clock (130)
    away = support.section(app, "away time")
    check("130: opening a case starts it, and a reload in place after a trim or an assignment leaves it running",
          "if (!inPlace) { clockClear(); drawClock(); }" in fn(app, "startCase"))
    check("130: nothing about the clock is saved anywhere",
          "localStorage" not in away and "sessionStorage" not in away and "api(" not in away
          and "clock" not in fn(app, "commit") and "clock" not in fn(app, "skipTurn"))

    check("130: a click sets the clock to zero, and no key does",
          "$('rail-clock-reset').onclick = () => { clockReset(); drawClock();" in app
          and "clockReset" not in keydown and "clock.from = Date.now();" in fn(away, "clockClear")
          and "clock.away = 0;" in fn(away, "clockClear"))

    node = shutil.which("node")
    if not node:
        skip("130: the clock's arithmetic in node", "no node on this machine")
    else:
        script = scratch / "clock-check.js"
        script.write_text(
            "let NOW = 1000000;\nDate.now = () => NOW;\nconst el = { textContent: '' };\nconst $ = () => el;\n"
            + away + "\n"
            "const out = {};\n"
            "NOW += 60000; out.running = clockSeconds();\n"
            "awayStart(); NOW += 30000; out.hidden = clockSeconds();\n"
            "awayStop(); NOW += 5000; out.back = clockSeconds();\n"
            "out.paceAway = awayTally(); awayReset(); out.paceAfterSave = awayTally(); out.clockAfterSave = clockSeconds();\n"
            "awayStart(); NOW += 10000; awayReset(); NOW += 10000; awayStop(); out.saveWhileAway = clockSeconds(); out.paceSince = awayTally();\n"
            "NOW += 1000; drawClock(); out.drawn = el.textContent;\n"
            "clockReset(); out.reset = clockSeconds(); drawClock(); out.resetDrawn = el.textContent;\n"
            "NOW += 4000; out.afterReset = clockSeconds(); out.paceKept = awayTally();\n"
            "awayStart(); clockReset(); NOW += 7000; out.resetAway = clockSeconds(); awayStop(); NOW += 2000; out.resetBack = clockSeconds();\n"
            "awayStart(); awayStart(); NOW += 3000; awayStop(); awayStop(); out.twice = clockSeconds();\n"
            "console.log(JSON.stringify(out));\n", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("130: the clock's arithmetic runs in node", False, run.stderr.strip()[:300])
        else:
            out = json.loads(run.stdout)
            check("130: in node, the clock runs while he is there and stands still while he is away",
                  out["running"] == 60 and out["hidden"] == 60 and out["back"] == 65, str(out))
            check("130: in node, a save clears the pace's counter and leaves the clock's total, even while away",
                  out["paceAway"] == 30 and out["paceAfterSave"] == 0 and out["clockAfterSave"] == 65
                  and out["saveWhileAway"] == 65 and out["paceSince"] == 10, str(out))
            check("130: in node, the clock draws as minutes and seconds",
                  out["drawn"] == "01:06" and out["resetDrawn"] == "00:00", str(out))
            check("130: in node, the reset sets it to zero and it runs on from there, the pace's counter untouched",
                  out["reset"] == 0 and out["afterReset"] == 4 and out["paceKept"] == 10, str(out))
            check("130: in node, a reset while away stays at zero until he is back, and a doubled event counts once",
                  out["resetAway"] == 0 and out["resetBack"] == 2 and out["twice"] == 2, str(out))

    # flags a progress file already holds stay in it, through a save, untouched
    root = scratch / "turnbar"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    seeded = rounds_mod.load_progress(work)
    seeded["flags"] = ["Initial:40", "Initial:3"]
    rounds_mod.save_progress(work, seeded)
    saved = (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_PATH = scratch / "turnbar-state.json"
    server_mod.STATE_MEMORY = None
    try:
        idiograph_routes.api_commit({"path": str(work), "sheet": DEMO_SHEET, "row": 5, "es": "A statement on the turn"})
        idiograph_routes.api_commit({"path": str(work), "sheet": DEMO_SHEET, "row": 7})
        after = rounds_mod.load_progress(work)
        check("131: flags already in a progress file stay in it, in their order, through a Next and a Skip",
              after["flags"] == ["Initial:40", "Initial:3"] and after["rows"].get("Initial:5") == "has-content"
              and after["rows"].get("Initial:7") == "reviewed-empty", str(after["flags"]))
    finally:
        server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = saved

    check("131: Cmd + Enter does what the button says, and the button does the same",
          "if (MOD(e) && e.key === 'Enter') { e.preventDefault(); pressAct(); return; }" in keydown
          and "$('btn-commit').onclick = () => pressAct();" in app and "commit(null, true)" not in keydown)
    check("131: Skip is what Skip did and Next what Next did",
          "'/api/commit'" in fn(app, "skipTurn") and "es:" not in fn(app, "skipTurn")
          and "pairs, es: cells.es, en: $('en').value, kq: cells.kq" in fn(app, "commit"))

    if not node:
        skip("131: the button's word in node", "no node on this machine")
    else:
        script = scratch / "act-check.js"
        script.write_text(
            "const F = { en: '' };\nlet P = [{ es: '', kq: '' }];\nlet ROW = { es: '', en: '', kq: '' };\n"
            "const $ = (id) => ({ value: F[id] });\nconst current = () => ROW;\nconst pairsNow = () => P;\n"
            "function turnAct(" + fn(app, "turnAct") + "\n}\n"
            "const out = {};\n"
            "out.blank = turnAct();\n"
            "P = [{ es: 'Living with the dog', kq: '' }]; out.typed = turnAct();\n"
            "P = [{ es: '', kq: '' }, { es: '', kq: '' }]; F.en = 'a note'; out.note = turnAct();\n"
            "F.en = ''; P = [{ es: '', kq: '' }, { es: '', kq: '\"a quote\"' }]; out.quote = turnAct();\n"
            "P = [{ es: '  ', kq: '   \\n ' }]; out.spaces = turnAct();\n"
            "P = [{ es: '', kq: '' }]; ROW = { es: 'Once written', en: '', kq: '' }; out.emptied = turnAct();\n"
            "ROW = null; out.none = turnAct();\n"
            "console.log(JSON.stringify(out));\n", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("131: the button's word runs in node", False, run.stderr.strip()[:300])
        else:
            out = json.loads(run.stdout)
            check("131: in node, Skip with the three fields empty, Next with words in any of them",
                  out["blank"] == "skip" and out["typed"] == "next" and out["note"] == "next"
                  and out["quote"] == "next" and out["spaces"] == "skip" and out["none"] == "skip", str(out))
            check("131: in node, a turn emptied of words the workbook holds reads Next, so the empties are written",
                  out["emptied"] == "next", str(out))
