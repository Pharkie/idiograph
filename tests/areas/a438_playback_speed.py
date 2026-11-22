"""Area 438: the player's speed (playspeed, 22 November 2026). One speed for every player, six steps from 0.5x to 2x,
held on this computer across opens, a button at the end of each player bar and a chord that steps it. What is held
here is what happens, in node, with the page's own functions: the remembered speed read back (a stranger's value,
an empty store and a store that throws all give 1x), a press of the button stepping round, the chord stepping and
stopping at either end, every player's audio element taking the speed with pitch kept and, since a new recording
resets a rate, as its default too, and each button showing the speed in force. Nothing here pins a drawing, a size
or a word of the look."""
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
let store = {}; let throws = false;
global.localStorage = {
  getItem(k) { if (throws) throw new Error('blocked'); return k in store ? store[k] : null; },
  setItem(k, v) { if (throws) throw new Error('blocked'); store[k] = String(v); },
};
const els = {};
const audio = () => ({ playbackRate: 1, defaultPlaybackRate: 1, preservesPitch: false, listeners: {},
  addEventListener(n, f) { this.listeners[n] = f; } });
for (const id of ['player', 'th-player', 'gt-trail-audio']) els[id] = audio();
for (const id of ['player-speed', 'th-pspeed']) {
  els[id] = { textContent: '', attrs: {}, on: false, shown: true, setAttribute(k, v) { this.attrs[k] = v; },
    getClientRects() { return this.shown ? [1] : []; }, classList: { toggle: (c, on) => { els[id].on = on; } } };
}
const $ = (id) => els[id] || null;
const t = (k, v) => k + ':' + (v ? v.speed : '');
const SEEK = (e) => e.seek;
// consts of an eval stay inside it, so they are read in as vars
eval((src.speeds + '\n' + src.key + '\n' + src.engines + '\n' + src.buttons + '\n' + src.fns).replace(/^const /gm, 'var '));
const out = {};
const ev = (code, alt) => ({ code, key: '?', getModifierState: (k) => k === 'AltGraph' && !!alt });
out.chord = [playSpeedChord(ev('BracketLeft')), playSpeedChord(ev('BracketRight')), playSpeedChord(ev('KeyA')), playSpeedChord(ev('BracketLeft', true)), playSpeedChord(ev('BracketRight', true))];
out.fresh = playSpeedGet();
store['idiograph-play-speed'] = '1.5'; out.kept = playSpeedGet();
store['idiograph-play-speed'] = '3'; out.stranger = playSpeedGet();
store['idiograph-play-speed'] = 'fast'; out.word = playSpeedGet();
throws = true; out.blocked = playSpeedGet(); playSpeedSet(2); out.blockedSet = playSpeedGet(); throws = false; PLAY_HELD.speed = 1;
store = {};
playSpeedAll();
out.drawnFresh = [els['player-speed'].textContent, els['th-pspeed'].textContent];
const seen = [];
for (let i = 0; i < 7; i++) { playSpeedCycle(); seen.push(playSpeedGet()); }
out.cycle = seen;
out.stored = store['idiograph-play-speed'];
playSpeedSet(2); playSpeedStep(1); out.top = playSpeedGet();
playSpeedSet(0.5); playSpeedStep(-1); out.bottom = playSpeedGet();
playSpeedStep(1); out.up = playSpeedGet(); playSpeedStep(1); out.up2 = playSpeedGet();
playSpeedSet(1.25);
out.engines = ['player', 'th-player', 'gt-trail-audio'].map((id) => [els[id].playbackRate, els[id].defaultPlaybackRate, els[id].preservesPitch]);
out.labels = [els['player-speed'].textContent, els['th-pspeed'].textContent];
out.changed = els['player-speed'].on;
playSpeedSet(1); out.changedOff = els['player-speed'].on;
out.aria = els['th-pspeed'].attrs['aria-label'];
out.shown = playBarShown();
els['player-speed'].shown = false; els['th-pspeed'].shown = false; out.hidden = playBarShown();
console.log(JSON.stringify(out));
"""


def test_playback_speed(scratch: Path):
    print("\n438. The player's speed: six steps from 0.5x to 2x, one speed for every player, held on this computer, "
          "pitch kept, a button in each bar and a chord (playspeed, 22 November)")
    page = support.page_text()
    js = support.text("apps/idiograph/static/distil.js")
    themes = support.text("apps/idiograph/static/themes.js")

    # ── A. the control in each bar, out of the Tab order as the others are, the chord on the shortcuts card
    for bar_id, button in (("player-bar", "player-speed"), ("th-pbar", "th-pspeed")):
        bar = page.split(f'id="{bar_id}"', 1)[1].split("\n        </div>", 1)[0]
        tag = re.search(rf'<button[^>]*id="{button}"[^>]*>', bar)
        check(f"438: the {bar_id} holds its speed button, out of the Tab order, labelled and with the chord in its tooltip",
              bool(tag) and 'tabindex="-1"' in tag.group(0) and "aria-label=" in tag.group(0)
              and "title=" in tag.group(0), tag.group(0) if tag else bar[-200:])
    check("438: the shortcuts card lists the chord beside the player's other keys",
          "page_idiograph.cards.ctrl_cmd_speed" in page, "audio section")
    catalogue = json.loads(support.text("apps/idiograph/static/i18n/en/page_idiograph.json"))
    check("438: the chord's tooltip and card line are in the catalogue",
          all(k in catalogue for k in ("page_idiograph.work.speed_key", "page_idiograph.cards.ctrl_cmd_speed",
                                       "page_idiograph.cards.speed_slower_faster")), "three keys")
    check("438: the audit trail's own player takes the speed before it plays",
          "playSpeedApply(player);" in js_function(themes, "gtTrailPlay"), "gtTrailPlay")

    # ── B. what it does, in node
    node = shutil.which("node")
    if not node:
        skip("438: the speed under node", "node is not on this machine")
        return
    parts = {"speeds": js_const(js, "PLAY_SPEEDS"), "key": js_const(js, "PLAY_SPEED_KEY"),
             "engines": js_const(js, "PLAY_ENGINES"), "buttons": js_const(js, "PLAY_BUTTONS") + "\n" + js_const(js, "PLAY_HELD"),
             "fns": "\n".join(js_function(js, n) for n in (
                 "playSpeedGet", "playSpeedLabel", "playSpeedApply", "playSpeedDraw", "playSpeedAll", "playSpeedSet",
                 "playSpeedCycle", "playSpeedStep", "playSpeedChord")) + "\n" + re.search(r"^const playBarShown = .*$", js, re.M).group(0)}
    with tempfile.TemporaryDirectory() as tmp:
        data, harness = Path(tmp, "src.json"), Path(tmp, "run.js")
        data.write_text(json.dumps(parts), encoding="utf-8")
        harness.write_text(HARNESS, encoding="utf-8")
        run = subprocess.run([node, str(harness), str(data)], capture_output=True, text=True, encoding="utf-8")
    try:
        out = json.loads(run.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        out = {}
    check("438: the harness ran", bool(out), (run.stderr or run.stdout)[-300:])
    check("438: the speeds are 0.5, 0.75, 1, 1.25, 1.5 and 2",
          js_const(js, "PLAY_SPEEDS").replace(" ", "") == "constPLAY_SPEEDS=[0.5,0.75,1,1.25,1.5,2];\n".replace(" ", ""),
          js_const(js, "PLAY_SPEEDS"))
    check("438: a fresh computer plays at 1x and a kept speed is read back",
          out.get("fresh") == 1 and out.get("kept") == 1.5, str(out))
    check("438: a value that is no step of the list, a word, or a store that throws all give 1x, and a store that "
          "throws still lets the speed change for the page",
          (out.get("stranger"), out.get("word"), out.get("blocked")) == (1, 1, 1) and out.get("blockedSet") == 2,
          str(out))
    check("438: a press of the button steps through the six speeds and round to the first, and each is kept",
          out.get("cycle") == [1.25, 1.5, 2, 0.5, 0.75, 1, 1.25] and out.get("stored") == "1.25", str(out))
    check("438: the chord's steps stop at either end",
          (out.get("top"), out.get("bottom"), out.get("up"), out.get("up2")) == (2, 0.5, 0.75, 1), str(out))
    check("438: every player's audio takes the speed as its rate and its default, with pitch kept, so a recording "
          "loaded later keeps it",
          out.get("engines") == [[1.25, 1.25, True]] * 3, str(out))
    check("438: both buttons show the speed in force, marked once it is not 1x, and name it for a reader",
          out.get("drawnFresh") == ["1x", "1x"] and out.get("labels") == ["1.25x", "1.25x"]
          and out.get("changed") is True and out.get("changedOff") is False
          and out.get("aria") == "distil.audio.speed_now:1x", str(out))
    check("438: the chord reads the key's place, and AltGr (which types the brackets on some layouts) is let through",
          out.get("chord") == [-1, 1, 0, 0, 0], str(out.get("chord")))
    check("438: the chord works while a bar shows and not otherwise", out.get("shown") and out.get("hidden") is False,
          str(out))
