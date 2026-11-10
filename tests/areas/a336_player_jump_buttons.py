"""Area 336: the player bar's jump buttons (jumpbtns, 8 November 2026, Adam's pick of three drawings). An arrow
icon with a small 5 stands either side of Play, out of the Tab order as Play is, the chord's name in each tooltip.
What is held here is what a press does: in node, the page's own `nudgeAudio` and the two `onclick` lines that wire
the buttons, so each button goes five seconds back or forward through the very function the keys call, never
below 0 and never past the end of the recording. Nothing here pins a drawing, a size or a word of the look."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import support
from .a167_window_menus import js_const, js_function
from .support import check, skip

HARNESS = r"""
const src = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const player = { src: 'x.wav', duration: 42, readyState: 4, currentTime: 0, getAttribute(k) { return k === 'src' ? this.src : null; } };
const els = {};
const $ = (id) => (id === 'player' ? player : (els[id] = els[id] || {}));
const S = { cueAt: 0, seekAt: 7, audioOffset: 0 };
const said = []; const marked = []; let drawn = 0;
const say = (m) => said.push(m);
const t = (k) => k;
const markTurnAt = (at) => marked.push(at);
const drawPlayer = () => { drawn += 1; };
eval(src.step + '\n' + src.heard + '\n' + src.nudge + '\n' + src.wire);
const press = (id) => els[id].onclick();
const out = {};
out.start = player.currentTime;
press('player-fwd'); out.fwd1 = player.currentTime;
press('player-fwd'); out.fwd2 = player.currentTime;
press('player-back'); out.back1 = player.currentTime;
press('player-back'); press('player-back'); out.floor = player.currentTime;
player.currentTime = 40; press('player-fwd'); out.ceiling = player.currentTime;
player.currentTime = 41.5; press('player-fwd'); out.end = player.currentTime;
out.seekAtCleared = S.seekAt === null;
out.marked = marked.length; out.drawn = drawn; out.said = said.length;
player.src = ''; player.currentTime = 3; press('player-fwd'); out.noRecording = player.currentTime; out.saidNone = said.length;
console.log(JSON.stringify(out));
"""


def test_player_jump_buttons(scratch: Path):
    print("\n336. The player bar's jump buttons: an arrow with a small 5 either side of Play, each five seconds "
          "through the function the keys use, clamped at 0 and at the end (jumpbtns, 8 November)")
    page = support.page_text()
    js = support.text("apps/idiograph/static/distil.js")
    catalogue = json.loads(support.text("apps/idiograph/static/i18n/en/page_idiograph.json"))

    # ── A. the buttons in the bar, either side of Play
    bar = page.split('id="player-bar"', 1)[1].split("</div>", 1)[0]
    back, play, fwd = bar.index('id="player-back"'), bar.index('id="player-play"'), bar.index('id="player-fwd"')
    check("an icon button stands either side of Play in the player bar, back first and forward last",
          back < play < fwd, "in the bar's own order, so they read left to right")
    tags = {i: re.search(rf'<button[^>]*id="{i}"[^>]*>', bar).group(0) for i in ("player-back", "player-play", "player-fwd")}
    check("they stay out of the Tab order as Play does, so the cursor keeps its place in a field",
          all('tabindex="-1"' in tag for tag in tags.values()), "all three")
    check("each tooltip names the key and each has a label",
          all(re.search(r'title="[^"]*Ctrl \+ Cmd', tags[i]) and 'aria-label="Five seconds' in tags[i]
              for i in ("player-back", "player-fwd")),
          "the same chord the shortcuts card gives, " + tags["player-back"][-160:])
    check("no switch of drawings is left behind", "data-jump" not in page and "dataset.jump" not in js,
          "one drawing, Adam's A")

    # ── B. what a press does, in node
    node = shutil.which("node")
    if not node:
        skip("336: a press of each button under node", "node is not on this machine")
        return
    wire = "\n".join(re.findall(r"^ *\$\('player-(?:back|fwd)'\)\.onclick = .*$", js, re.M))
    check("each button's click calls nudgeAudio with the step the keys use",
          "nudgeAudio(-AUDIO_STEP)" in wire and "nudgeAudio(AUDIO_STEP)" in wire and wire.count("onclick") == 2,
          wire.strip())
    parts = {"step": js_const(js, "AUDIO_STEP"), "heard": "const heardAt = (at) => at - (S.audioOffset || 0);",
             "nudge": js_function(js, "nudgeAudio"), "wire": wire}
    with tempfile.TemporaryDirectory() as tmp:
        data, harness = Path(tmp, "src.json"), Path(tmp, "run.js")
        data.write_text(json.dumps(parts), encoding="utf-8")
        harness.write_text(HARNESS, encoding="utf-8")
        run = subprocess.run([node, str(harness), str(data)], capture_output=True, text=True, encoding="utf-8")
    try:
        out = json.loads(run.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        out = {}
    check("the harness ran", bool(out), (run.stderr or run.stdout)[-300:])
    check("the forward button goes five seconds on each press and the back button five back",
          (out.get("fwd1"), out.get("fwd2"), out.get("back1")) == (5, 10, 5), str(out))
    check("back stops at 0 and forward at the end of the recording",
          out.get("floor") == 0 and out.get("ceiling") == 42 - 0 - 0 + 0 - 0 and out.get("end") == 42, str(out))
    check("a press moves the turn and the clock and ends the timecode toggle",
          out.get("marked") == 7 and out.get("drawn") == 7 and out.get("seekAtCleared") is True, str(out))
    check("with no recording a press says so and moves nothing",
          out.get("noRecording") == 3 and out.get("saidNone") == 1, str(out))
