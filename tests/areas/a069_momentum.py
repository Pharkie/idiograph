from __future__ import annotations

import json
import re
import shutil

import rounds as rounds_mod
import workbook as wb_mod

from . import support
from .support import check, demo_copy, demo_sheet, skip


def test_momentum(scratch):
    print("\n69. Momentum: today's haul on a break, the statements left on the PETs "
          "screen, and Celebrations with Sound (158 to 161)")
    import datetime as dt
    import subprocess
    import server as server_mod

    js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    tjs = support.text("apps/idiograph/static/themes.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    line_of = lambda src, start: next((l for l in src.splitlines() if l.startswith(start)), "")
    node = shutil.which("node")
    day = lambda k: (dt.date.today() - dt.timedelta(days=k)).isoformat()

    # ── A. the figures the haul is made of: the rounds closed today, their turns and their seconds
    rnds = [{"number": n, "stops": [("Initial", r) for r in range(a, b)]}
            for n, (a, b) in enumerate([(2, 14), (14, 21), (21, 30), (30, 33)], start=1)]
    now = dt.datetime.now().isoformat(timespec="seconds")
    held = {"rounds": {"1": {"seconds": 1500, "completed": f"{day(1)}T18:00:00"},
                       "2": {"seconds": 1820, "completed": now},
                       "3": {"seconds": 2500, "completed": now},
                       "4": {"seconds": 400, "completed": None}}}
    check("158: today's work is the turns of the rounds closed today and the seconds measured on them, "
          "a round closed yesterday or not at all left out",
          rounds_mod.today_work(held, rnds) == (7 + 9, 1820 + 2500)
          and rounds_mod.today_work({"rounds": {}}, rnds) == (0, 0))
    root = scratch / "momentum"
    work = demo_copy(root / "cases", "Juno", "Juno - EN & ES.xlsx")
    _, her, him = demo_sheet(work)
    case = wb_mod.read_case(work)
    demo_rounds = rounds_mod.build_rounds(case["sheets"], 10, him)
    progress = rounds_mod.load_progress(work)
    progress["rounds"]["1"] = {"seconds": 600, "completed": now}
    progress["days"][day(0)] = {"rounds": 1}
    summary = rounds_mod.summary(case["sheets"], progress, demo_rounds, him, 2)
    check("158: the summary carries todayTurns and todaySeconds beside todayRounds, from the round closed today",
          summary["todayRounds"] == 1 and summary["todayTurns"] == len(demo_rounds[0]["stops"]) > 0
          and summary["todaySeconds"] == 600, f"{summary['todayRounds']}, {summary['todayTurns']}, {summary['todaySeconds']}")

    # ── C. the two settings: their defaults, the save, and a file from before them
    check("161: celebrations is on and sound off by default, and a config.json from before them reads the same",
          server_mod.defaults()["celebrations"] is True and server_mod.defaults()["sound"] is False
          and server_mod.merge_config({"interviewer": "Adam"})["celebrations"] is True
          and server_mod.merge_config({})["sound"] is False)
    settings_file = root / "settings.json"
    settings_file.write_text(json.dumps({"interviewer": "Adam", "feedback_url": "https://example.invalid/x"}), encoding="utf-8")
    saved_path = server_mod.CONFIG_PATH
    server_mod.CONFIG_PATH = settings_file
    try:
        server_mod.api_settings({"celebrations": False, "sound": True})
        first = json.loads(settings_file.read_text(encoding="utf-8"))
        server_mod.api_settings({"celebrations": 1, "sound": ""})
        second = json.loads(settings_file.read_text(encoding="utf-8"))
        server_mod.api_settings({"interviewer": "Adam"})
        third = json.loads(settings_file.read_text(encoding="utf-8"))
    finally:
        server_mod.CONFIG_PATH = saved_path
    check("161: Save writes both ticks as true or false, and a save without them leaves them as they were",
          first["celebrations"] is False and first["sound"] is True and second["celebrations"] is True
          and second["sound"] is False and third["celebrations"] is True and third["sound"] is False
          and third["feedback_url"] == "https://example.invalid/x", str(first))

    # ── D. the page: the elements, the settings pane and the styles
    # since 20 October a Celebrations switch for each screen (area 234), Sound waiting on any of them
    check("161: the card reads the ticks, Sound waits on Celebrations, and Save sends both",
          "cheerDraw(c);" in fn(js, "openSettings")
          and "$('set-sound').checked = c.sound === true;" in fn(js, "openSettings")
          and "cheerSoundGate();" in fn(js, "openSettings")
          and "...cheerBody()," in fn(js, "saveSettings")
          and "sound: $('set-sound').checked," in fn(js, "saveSettings")
          and "$('cheer-set').onchange = () => cheerSoundGate();" in js)
    audio_files = [p.name for folder in support.static_folders() for p in folder.rglob("*") if p.suffix.lower() in (".mp3", ".wav", ".ogg", ".m4a", ".aac", ".flac")]
    check("161: the sounds are made with the Web Audio API in the page, and no audio file is shipped or fetched",
          "window.AudioContext || window.webkitAudioContext" in fn(js, "playSound") and "createOscillator()" in fn(js, "playSound")
          and not audio_files and "new Audio(" not in js + tjs and not re.search(r"\.(mp3|wav|ogg|m4a)\b", js + tjs),
          ", ".join(audio_files))

    # ── E. in node: the haul, the days, the switch, the sound and the confetti's gate
    if not node:
        skip("158 to 161: the haul, the days, the sound and the statements left in node", "no node on this machine")
    else:
        consts = "const CONFETTI_LEVELS = {" + js.split("const CONFETTI_LEVELS = {", 1)[1].split("function confetti(level", 1)[0]
        pieces = [support.i18n_js(), line_of(js, "const esc = "), line_of(js, "const escAttr = "), line_of(js, "const HAUL_MS = "),
                  "let haulTimer = null;", line_of(js, "function roundsOn("), line_of(js, "function roundsHere("),
                  whole(js, "haulTime"), whole(js, "formatMinutes"),
                  whole(js, "haulLine"), whole(js, "haulShow"), whole(js, "haulHide"), whole(js, "stopHere"),
                  whole(js, "countWord"), whole(js, "flashCount"), consts, whole(js, "confetti")]
        script = root / "momentum.js"
        script.write_text(
            "const timers = []; const setTimeout = (f, ms) => { timers.push([f, ms]); return timers.length; };\n"
            "const clearTimeout = () => {};\n"
            "const mk = () => { const set = new Set(); return { hidden: true, textContent: '', innerHTML: '', offsetWidth: 1, set,\n"
            "  classList: { add: (c) => set.add(c), remove: (c) => set.delete(c), toggle: (c, v) => (v ? set.add(c) : set.delete(c)) } }; };\n"
            "const els = {}; let touched = [];\n"
            "const $ = (id) => { touched.push(id); return els[id] || (els[id] = mk()); };\n"
            "let reduce = false; const listening = new Set();\n"
            "const tones = [];\n"
            "class FakeCtx { constructor() { this.state = 'running'; this.currentTime = 0; this.destination = {}; }\n"
            "  createOscillator() { const o = { type: '', frequency: { value: 0 }, connect() {}, start(t) { o.at = t; }, stop(t) { o.end = t; } }; tones.push(o); return o; }\n"
            "  createGain() { return { gain: { setValueAtTime() {}, exponentialRampToValueAtTime() {} }, connect() {} }; }\n"
            "  resume() {} }\n"
            "const window = { AudioContext: FakeCtx, matchMedia: () => ({ matches: reduce }),\n"
            "  addEventListener: (t) => listening.add(t), removeEventListener: (t) => listening.delete(t) };\n"
            "const document = { hidden: false, querySelector: () => null, addEventListener() {}, removeEventListener() {} };\n"
            "const S = { data: { progress: null, config: { work_in_rounds: true } }, libConfig: null, doneSheet: false };\n"
            "const said = []; const say = (t) => said.push(t); const hide = (id) => { $(id).hidden = true; };\n"
            "const closingOnMove = () => false;\n"
            "const current = () => ({ key: 'Initial:11' });\n"
            "const currentRound = () => ({ stops: [2, 4, 9, 11, 12].map((row) => ({ sheet: 'Initial', row })) });\n"
            # the family's celebrations ask Idiograph's part which screen is in front (the fifth build)
            "const FAMILY_APPS = {};\n" + support.distil_hooks(js)
            + "\n".join(pieces) + "\n"
            "const out = {};\n"
            "const P = (p) => haulLine(p);\n"
            "out.lines = [P({ todayRounds: 3, todayTurns: 47, todaySeconds: 4320 }), P({ todayRounds: 1, todayTurns: 12, todaySeconds: 540 }),\n"
            "  P({ todayRounds: 3 }), P({ todayRounds: 2, todayTurns: 20, todaySeconds: 25 }), P({ todayRounds: 4, todayTurns: 51, todaySeconds: 7200 }),\n"
            "  P({ todayRounds: 2, todaySeconds: 3000 }), P({}), P(null), P({ todayRounds: 1, todayTurns: 16, todaySeconds: 36 })];\n"
            "// Take a break: the toast as before, and the haul where the card stood, its timer, then a key or a click\n"
            "S.data.progress = { todayRounds: 3, todayTurns: 47, todaySeconds: 4320 };\n"
            "stopHere();\n"
            "out.shown = { hidden: $('haul').hidden, text: $('haul').textContent, on: $('haul').set.has('on'),\n"
            "  card: $('round-done').hidden, toast: said[said.length - 1], wait: timers.map((t) => t[1]) };\n"
            "timers.filter((t) => t[1] === 0).forEach((t) => t[0]());\n"
            "out.listens = [...listening].sort();\n"
            "haulHide();\n"
            "out.gone = { hidden: $('haul').hidden, listens: [...listening] };\n"
            "// the switch off: no haul, no count, no confetti and no sound\n"
            "S.data.config = { celebrations: false, sound: true, work_in_rounds: true }; timers.length = 0; tones.length = 0;\n"
            "stopHere(); flashCount(); touched = []; confetti(3);\n"
            "out.off = { haul: $('haul').hidden, flash: $('count-flash').set.has('on'), canvas: touched.includes('confetti'), tones: tones.length,\n"
            "  cheer: cheerOn(), sound: soundOn(), toast: said[said.length - 1] };\n"
            "// a server from before the two keys: on, and sound off\n"
            "S.data.config = { work_in_rounds: true }; tones.length = 0; flashCount();\n"
            "out.old = { cheer: cheerOn(), sound: soundOn(), flash: $('count-flash').set.has('on'), text: $('count-flash').innerHTML.replace(/<[^>]+>/g, ''), tones: tones.length };\n"
            "S.data = null; S.libConfig = { celebrations: false }; out.lib = cheerOn(); S.data = { progress: null, config: {} };\n"
            "// Sound on: the tick on a decided turn, under reduced motion too, two notes for a round, more for a sheet or the case\n"
            "S.data.config = { sound: true, work_in_rounds: true }; reduce = true; $('count-flash').set.clear(); tones.length = 0;\n"
            "flashCount(); out.tick = { tones: tones.length, flash: $('count-flash').set.has('on'), length: tones.length ? tones[0].end - tones[0].at : null };\n"
            "tones.length = 0; touched = []; confetti(1); out.round = { tones: tones.length, canvas: touched.includes('confetti'),\n"
            "  length: Math.max(...tones.map((t) => t.end)) - Math.min(...tones.map((t) => t.at)) };\n"
            "tones.length = 0; confetti(2); out.sheet = tones.length; tones.length = 0; confetti(3);\n"
            "out.caseDone = { tones: tones.length, length: Math.max(...tones.map((t) => t.end)) - Math.min(...tones.map((t) => t.at)) };\n"
            "S.data.config = { sound: false, work_in_rounds: true }; tones.length = 0; flashCount(); confetti(1); out.quiet = tones.length;\n"
            "reduce = false;\n"
            "console.log(JSON.stringify(out));\n", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("158 to 161: the haul, the days and the switch run in node", False, run.stderr.strip()[:400])
        else:
            o = json.loads(run.stdout)
            check("158: in node, the line is today's rounds, turns and time, one of each read in the singular",
                  o["lines"][:2] == ["Today: 3 rounds, 47 passages, 1 h 12 min.", "Today: 1 round, 12 passages, 9 min."], str(o["lines"]))
            check("158: in node, a figure the server does not send is left out, and so is a time under half a minute",
                  o["lines"][2:] == ["Today: 3 rounds.", "Today: 2 rounds, 20 passages.", "Today: 4 rounds, 51 passages, 2 h.",
                                     "Today: 2 rounds, 50 min.", "", "", "Today: 1 round, 16 passages, 1 min."], str(o["lines"]))
            s_ = o["shown"]
            check("158: in node, Take a break closes the card, keeps its line at the foot, and shows the haul for four seconds",
                  s_["card"] and not s_["hidden"] and s_["on"] and s_["text"] == "Today: 3 rounds, 47 passages, 1 h 12 min."
                  and s_["toast"] == "A break at a round end. The next round is here when you are ready."
                  and 4000 in s_["wait"] and 0 in s_["wait"], str(s_))
            check("158: in node, a key or a click takes it away at once, listening only once the press that showed it is past",
                  o["listens"] == ["keydown", "pointerdown"] and o["gone"] == {"hidden": True, "listens": []}, str(o["listens"]))
            off = o["off"]
            check("161: in node, Celebrations off silences every flourish: the haul, the count, the confetti and the sound",
                  off["haul"] and not off["flash"] and not off["canvas"] and off["tones"] == 0 and not off["cheer"]
                  and not off["sound"] and off["toast"].startswith("A break at a round end."), str(off))
            check("161: in node, a page in front of a server that knows neither key reads Celebrations on and Sound off",
                  o["old"] == {"cheer": True, "sound": False, "flash": True, "text": "4 / 5", "tones": 0} and o["lib"] is False, str(o["old"]))
            check("161: in node, Sound on ticks on a decided turn under reduced motion too, under 200ms, with the count still away",
                  o["tick"]["tones"] == 1 and not o["tick"]["flash"] and 0 < o["tick"]["length"] < 0.2, str(o["tick"]))
            check("161: in node, a round closing chimes two notes, a sheet or the case a longer one, and reduced motion keeps the canvas off",
                  o["round"]["tones"] == 2 and not o["round"]["canvas"] and o["sheet"] == 4 and o["caseDone"]["tones"] == 4
                  and o["caseDone"]["length"] > o["round"]["length"] and o["quiet"] == 0, str(o["round"]) + str(o["caseDone"]))

        # ── F. in node: the statements left on the PETs screen
        tpieces = [line_of(tjs, "const thStickies = "), line_of(tjs, "const thIsGroup = "), line_of(tjs, "const thCalm = "), line_of(tjs, "const thStacks = "), whole(tjs, "thTopOf"),
                   whole(tjs, "thParents"), whole(tjs, "thCounts"), whole(tjs, "thMomentum"), whole(tjs, "thFlash")]
        script = root / "pets-left.js"
        script.write_text(support.i18n_js() + 
            "let reduce = false; let cheer = true;\n"
            "const window = { matchMedia: () => ({ matches: reduce }) };\n"
            "const set = new Set(); const ops = [];\n"
            "const flash = { innerHTML: '', offsetWidth: 1, classList: { add: (c) => { set.add(c); ops.push('+' + c); },\n"
            "  remove: (c) => { set.delete(c); ops.push('-' + c); }, toggle: (c, v) => (v ? set.add(c) : set.delete(c)) } };\n"
            "const $ = () => flash;\n"
            "const fired = []; const confetti = (level) => fired.push(level);\n"
            "const cheerOn = () => cheer;\n"
            "const TH = { v: null };\n"
            + "\n".join(tpieces) + "\n"
            "const snap = (v) => JSON.parse(JSON.stringify(v));\n"
            "const cards = {}; for (const k of ['a', 'b', 'c', 'd', 'e', 'f', 'g']) cards[k] = { x: 0, y: 0, text: k };\n"
            "TH.v = { cards, groups: [], discarded: [], stickies: [] };\n"
            "const shown = () => (set.has('on') ? flash.innerHTML.replace(/<[^>]+>/g, '') : null);\n"
            "const act = (change) => { const before = snap(TH.v); change(TH.v); set.clear(); ops.length = 0; thMomentum(before); return shown(); };\n"
            "const out = {};\n"
            "out.placed = act((v) => { v.groups.push({ id: 'g1', label: 'One', members: ['a'] }); });\n"
            "out.line1 = set.has('line');\n"
            "out.sub = act((v) => { v.groups.push({ id: 'g2', label: 'Sub', members: ['b'] }); v.groups[0].members.push('g2'); });\n"
            "out.discarded = act((v) => { v.discarded.push('c'); });\n"
            "out.swap = act((v) => { v.groups[0].members = ['g2', 'd']; });\n"
            "out.back = act((v) => { v.groups[0].members = ['g2']; });\n"
            "out.moved = act((v) => { v.cards.a.x = 40; });\n"
            "out.firedBefore = fired.slice();\n"
            "out.restart = (() => { const before = snap(TH.v); TH.v.groups[0].members.push('a'); set.add('on'); ops.length = 0; thMomentum(before); return ops.slice(); })();\n"
            "cheer = false; out.off = act((v) => { v.discarded.push('d'); });\n"
            "cheer = true; reduce = true; out.reduced = act((v) => { v.groups[0].members.push('e'); });\n"
            "reduce = false;\n"
            "out.beforeLast = thCounts(TH.v).unplaced;\n"
            "fired.length = 0;\n"
            "out.last = act((v) => { v.groups[0].members.push('f', 'g'); });\n"
            "out.lastLine = set.has('line'); out.lastFired = fired.slice();\n"
            "out.undo = (() => { const before = snap(TH.v); fired.length = 0; set.clear(); thMomentum(before); return [shown(), fired.length]; })();\n"
            "console.log(JSON.stringify(out));\n", encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
        if run.returncode != 0:
            check("160: the statements left run in node", False, run.stderr.strip()[:400])
        else:
            p = json.loads(run.stdout)
            check("160: in node, a statement placed in a PET, in a sub-theme or on the pile raises the count of those left",
                  p["placed"] == "6 left" and not p["line1"] and p["sub"] == "5 left" and p["discarded"] == "4 left", str(p))
            check("160: in node, an act that leaves Unplaced as it was or brings one back raises nothing",
                  p["swap"] is None and p["back"] is None and p["moved"] is None and p["firedBefore"] == [], str(p))
            check("160: in node, a new count replaces one still showing, taken off and put back",
                  p["restart"][:2] == ["-on", "+on"] or p["restart"][-2:] == ["-on", "+on"], str(p["restart"]))
            check("160: in node, Celebrations off and reduced motion show nothing",
                  p["off"] is None and p["reduced"] is None, str(p))
            check("160: in node, the last statement placed fires the third level of confetti with its one line",
                  p["beforeLast"] == 2 and p["last"] == "Every statement placed." and p["lastLine"] and p["lastFired"] == [3]
                  and p["undo"] == [None, 0], str(p))
