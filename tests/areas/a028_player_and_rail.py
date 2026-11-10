from __future__ import annotations

from . import support
from .support import check


def test_player_and_rail():
    print("\n27. The timecode toggle, the audio keys, the player bar, the rail and the count")
    import server as server_mod
    static = server_mod.HERE / "static"
    page = support.page_text()
    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")

    # ── A. clicking a timecode again
    play_from = js.split("function playFrom(", 1)[1].split("\n}", 1)[0]
    cue = js.split("function cueAudio(", 1)[1].split("\n}", 1)[0]
    nudge_audio = js.split("function nudgeAudio(", 1)[1].split("\n}", 1)[0]
    check("the timecode it is already playing from pauses on the next click",
          "if (S.seekAt !== null && S.seekAt === from) { togglePlay(); return; }" in play_from
          and "S.seekAt = from;" in play_from and "cueAudio(from);" in play_from,
          "and the click after that carries on from where it stopped, because togglePlay does")
    check("another timecode jumps there and keeps playing",
          "const played = player.play();" in play_from and "player.readyState >= 1" in play_from,
          "the cue and the play, as they always were")
    check("a cue to anywhere else ends the toggle",
          "if (S.seekAt !== null && S.seekAt !== said) S.seekAt = null;" in cue,
          "so that timecode plays from its own place again rather than pausing")
    check("the drag and the five second jump end it too",
          "seekAt: null," in js
          and "S.seekAt = null;" in js.split("function scrubTo(", 1)[1].split("\n}", 1)[0]
          and "S.seekAt = null;" in nudge_audio)

    # ── B. the keyboard
    guard = js.index("if (typing || MOD(e) || e.altKey) return;")
    check("Space plays or pauses, and never from inside a field or the turn editor",
          "if (e.key === ' ' && !$('work').hidden) { e.preventDefault(); togglePlay(); }" in js
          and guard < js.index("if (e.key === ' '"),
          "the guard that hands every bare key to the field it is in is read first")
    check("Ctrl + Cmd and the arrows jump five seconds, from inside the fields as well (item 33)",
          "const AUDIO_STEP = 5;" in js
          and "const SEEK = (e) => (MAC ? e.metaKey && e.ctrlKey : e.ctrlKey && e.altKey) && !e.shiftKey;" in js
          and "if (SEEK(e) && e.key === 'ArrowLeft' && !$('work').hidden) {" in js
          and "if (SEEK(e) && e.key === 'ArrowRight' && !$('work').hidden) {" in js
          and js.index("nudgeAudio(-AUDIO_STEP)") < guard,
          "read before that guard, so the chord reaches the player from a field")
    check("Cmd and an arrow are left to the text, the line ends and with Shift the selection (item 33)",
          "MOD(e) && e.key === 'ArrowLeft'" not in js and "MOD(e) && e.key === 'ArrowRight'" not in js
          and "Ctrl + Cmd + ←" in page and "Cmd + ← / →" in page,
          "no handler takes Cmd + arrow, and the card says which keys are the text's")
    check("the jump moves the playhead and the elapsed time at once",
          "markTurnAt(heardAt(at));" in nudge_audio and "drawPlayer();" in nudge_audio
          and "S.cueAt = at;" in nudge_audio and "Math.min(from + delta, duration)" in nudge_audio,
          "and never runs past either end of the recording")
    check("Grammarly is told to stay out of every text box: the fields, the editor, the timecode (item 41)",
          'data-gramm="false" data-gramm_editor="false" data-enable-grammarly="false"' in js
          and "field.dataset.gramm = 'false';" in js
          and all('data-gramm="false"' in page.split(f'<textarea id="{i}"', 1)[1].split(">", 1)[0]
                  for i in ("en", "set-prompt"))
          and 'data-gramm="false" data-gramm_editor="false" data-enable-grammarly="false"' in js.split("const GRAMM_OFF = ", 1)[1][:120]
          and js.split("function pairHtml(", 1)[1][:1100].count("${GRAMM_OFF}></textarea>") == 2)
    check("t opens the trim card on the current turn with both ends offered (item 39)",
          "else if (key === 't' && !$('work').hidden) { e.preventDefault(); trimKey(); }" in js
          and "function trimKey()" in js and "function confirmTrim(row, direction, both = false)" in js
          and 'id="trim-other"' in page and '<td class="mono">T</td>' in page)

    # ── G. the nudge line
    nudge_fn = js.split("function runNudges(", 1)[1].split("\n}", 1)[0]
    check("each statement's nudges stand under it, with no line number to say which (198)",
          "Line ${line.line + 1}:" not in nudge_fn and "el.querySelector('.nudges').innerHTML" in nudge_fn
          and "for (const line of data.lines) by[line.line] = line.flags;" in nudge_fn
          and "lines.join('\\n')" in nudge_fn,
          "the statements go in one request, one a line, and come back by line")
