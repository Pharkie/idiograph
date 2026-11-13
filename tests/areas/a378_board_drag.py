"""Area 378: a card dragged on a large PETs board keeps the frame rate (boardperf, 13 November 2026).

Adam, 13 November, on a participant's PETs board of about 105 statements in the Mac app: "the frame rate seems very
low as I drag it left and right. The tilting seems very clunky in a way it didn't before." On every frame of a drag
the board placed everything again and with it drew the close pairs' lines afresh, none while a drag lasts, as two
SVG layers rebuilt from their markup under a clip the size of the whole board, so WebKit, the Mac window's engine,
painted all of the board on screen again on every frame. The more of the board the screen holds, the longer each
frame: the same 105 cards at 60% took about 25 ms a frame laid out square, as the whole board's Auto-arrange has laid
boards out since 13 November, and 17 laid out as one long column, where the screen gives one every 16.7.
Here, in WebKit through packaging/wk_shot.swift, on an invented participant, Wren, learning to keep bees at fifty,
112 statements with their quotes, 105 cards showing in six PETs of sixteen sub-PETs and seven stacked, the whole
board arranged, served by the app's own handler, at 1587 by 1234 with the scroll bars a mouse brings and the
transitions running, a card dragged left and right across the PETs for two seconds with the pointer emulated in the
page keeps its median frame at 18 ms or less and none over 50 ms, tried once more when the machine's load starves
the window, adds or removes nothing in the board after the drag's first frame and reads no layout as the pointer
moves. The lines drawn afresh every frame, as they were, put back on the same board rebuild them, which the watch
sees.

Since perfreview (13 November 2026, Adam's recording of a PET dragged by its title, uneven from frame to frame with
holds and jumps): a PET dragged by its title across the same board, its cards and sub-PETs with it, keeps the same
pace after the frame that picks it up, each thing it carries drawn in a layer of its own while it moves, and both
drags move an even step a frame, each frame's step within 0.7 to 1.35 of an even hand's for eight frames in ten, the
pointer's place taken a moment before each frame from the moves either side of then. Each frame taking the latest
move as it is, as it did, put back on the same board steps unevenly, which the watch sees.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import openpyxl

from . import support
from .support import check, skip

OPEN = ["The first hive in the garden", "My hands in the gloves", "The smell of the smoker", "Being stung on the wrist",
        "The queen with her dot of paint", "Lifting a full super", "The cold in February", "Learning to read a frame",
        "My back the day after", "The swarm in the plum tree", "The first jar of honey", "My son watching from the door",
        "The hum when the lid comes off", "Being the slowest in the class", "The rain on the roof of the shed",
        "Talking to them before I open up"]
TAIL = ["felt like being let into a secret nobody had told me about, and I kept it close for weeks.",
        "made me clumsy at first and then, slowly, less so, until my hands knew what to do before I did.",
        "was the part of the week I kept for myself and told nobody about, not even my sister.",
        "showed me how much I had stopped trying new things since the shop closed and the house went quiet.",
        "frightened me more than I let anyone see, and I went back out to them the next morning anyway.",
        "was something I could not explain to the others at work, so I stopped trying to."]
N = 112
TALK = [f"{OPEN[n % len(OPEN)]} {TAIL[(n // len(OPEN)) % len(TAIL)]}" for n in range(N)]
# six PETs: their own statements, then sub-PETs of mixed sizes, 105 in all, and seven more stacked under others
PLAN = [("Becoming someone who keeps bees", 3, [10, 6, 4]), ("The hive as a place of her own", 2, [8, 5, 7, 3]),
        ("A body that learns slowly", 4, [9, 2]), ("Fear, and going back anyway", 0, [6, 6, 5]),
        ("Who she is among the others", 5, [4, 3]), ("Time measured by the seasons", 1, [7, 5])]
SUBS = ["The first weeks", "What the teacher saw", "Others watching", "Mornings alone", "A word for it", "The cold",
        "Hands and back", "Getting it wrong", "The swarm", "Going back", "In the club", "Smoke", "The plum tree",
        "Honey", "The shed", "Stings"]
DESCRIBED = ("What she found she could still learn, slowly and in front of others, when nobody expected her to, and "
             "what it cost her to be seen getting it wrong in the garden, week after week")

# The pointer in the page: an offscreen WebKit window takes no mouse moves, so the press goes to the card and the
# moves to the canvas, which holds the pointer while a button is down, as a mouse's do. WebKit keeps :hover on what
# was pressed while the button is down, so nothing else takes it as the card passes. Counted while the drag runs: the
# frames, by requestAnimationFrame, what is added to or taken from the board after its first frame, and the reads
# of the layout made as the pointer moves
DRAG_INIT = r"""
window.__bd = {
  reads: 0, inMove: false,
  wrap() {
    if (this.wrapped) return;
    this.wrapped = true;
    const self = this;
    const watch = (fn) => function (...a) { if (self.inMove) self.reads += 1; return fn.apply(this, a); };
    const P = Element.prototype, H = HTMLElement.prototype;
    for (const m of ['getBoundingClientRect', 'getClientRects']) P[m] = watch(P[m]);
    for (const g of ['offsetWidth', 'offsetHeight', 'offsetLeft', 'offsetTop']) {
      const d = Object.getOwnPropertyDescriptor(H, g);
      Object.defineProperty(H, g, { configurable: true, get: watch(d.get) });
    }
    for (const g of ['clientWidth', 'clientHeight', 'scrollWidth', 'scrollHeight']) {
      const d = Object.getOwnPropertyDescriptor(P, g);
      Object.defineProperty(P, g, { configurable: true, get: watch(d.get), set: d.set });
    }
    window.getComputedStyle = watch(window.getComputedStyle);
    const efp = document.elementFromPoint;
    document.elementFromPoint = watch(function (x, y) { return efp.call(document, x, y); });
  },
  pe(type, x, y) {
    return new PointerEvent(type, { bubbles: true, cancelable: true, composed: true, clientX: x, clientY: y, pointerId: 1,
      pointerType: 'mouse', isPrimary: true, button: type === 'pointermove' ? -1 : 0, buttons: 1 });
  },
  sleep(ms) { return new Promise((r) => setTimeout(r, ms)); },
  // a card in a PET as near the canvas's middle as leaves room to swing `amp` either way
  pick(amp) {
    const sb = document.getElementById('th-stage').getBoundingClientRect();
    let best = null, bd = Infinity;
    for (const c of document.querySelectorAll('#th-world .th-card.in')) {
      const b = c.getBoundingClientRect(), cx = b.left + b.width / 2, cy = b.top + b.height / 2;
      if (cx - amp < sb.left + 20 || cx + amp > sb.right - 20 || cy < sb.top + 40 || cy > sb.bottom - 40) continue;
      const d = Math.hypot(cx - (sb.left + sb.width / 2), cy - (sb.top + sb.height / 2));
      if (d < bd) { bd = d; best = { el: c, x: Math.round(cx), y: Math.round(cy) }; }
    }
    return best;
  },
  // a PET's title, a label of no parent, as near the canvas's middle as leaves room to swing `amp` either way
  pickTitle(amp) {
    const sb = document.getElementById('th-stage').getBoundingClientRect();
    const parents = thParents(TH.v);
    let best = null, bd = Infinity;
    for (const [id, el] of Object.entries(TH.els.labels)) {
      if (parents[id]) continue;
      const b = el.getBoundingClientRect(), cx = b.left + Math.min(40, b.width / 2), cy = b.top + b.height / 2;
      if (cx - amp < sb.left + 10 || cx + amp > sb.right - 10 || cy < sb.top + 20 || cy > sb.bottom - 20) continue;
      const d = Math.hypot(cx - (sb.left + sb.width / 2), cy - (sb.top + sb.height / 2));
      if (d < bd) { bd = d; best = { el, x: Math.round(cx), y: Math.round(cy) }; }
    }
    return best;
  },
  async drag(ms = 2000, amp = 420, kind = 'card') {
    this.wrap();
    const stage = document.getElementById('th-stage');
    const p = kind === 'title' ? this.pickTitle(amp) : this.pick(amp);
    if (!p) return { error: 'no ' + kind };
    const frames = [];
    const rows = [];
    let stop = false;
    let t0 = null;
    const z = TH.view.z;
    // what each frame drew of what is dragged, read the next frame from its own style, so nothing is laid out
    const tx = () => { const m = /^(-?[\d.]+)px/.exec(p.el.style.translate || ''); return m ? Number(m[1]) * z : 0; };
    const tick = (t) => {
      frames.push(t);
      if (t0 !== null && TH.drag) rows.push({ t, ideal: amp * Math.sin((2 * Math.PI * (t - t0)) / 1400), at: tx() });
      if (!stop) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
    await this.sleep(50);
    t0 = performance.now();
    p.el.dispatchEvent(this.pe('pointerdown', p.x, p.y));
    let added = 0, first = true;
    const world = document.getElementById('th-world');
    const count = (list) => { for (const r of list) added += r.addedNodes.length + r.removedNodes.length; };
    const mo = new MutationObserver(count);
    this.reads = 0;
    while (performance.now() - t0 < ms) {
      await this.sleep(8);
      const t = performance.now() - t0;
      const x = Math.round(p.x + amp * Math.sin((2 * Math.PI * t) / 1400));
      const y = Math.round(p.y + 60 * Math.sin((2 * Math.PI * t) / 3780));
      // once the drag is under way, as a move then only hands itself to the next frame
      this.inMove = !!TH.drag;
      stage.dispatchEvent(this.pe('pointermove', x, y));
      this.inMove = false;
      // the drag's first frame draws what a drag shows, and from then on it is watched
      if (first && TH.drag && t > 100) { first = false; mo.observe(world, { subtree: true, childList: true }); }
    }
    stop = true;
    const dragging = !!TH.drag;
    count(mo.takeRecords());
    mo.disconnect();
    thDragCancel();
    TH.press = null;
    const d = [];
    for (let i = 1; i < frames.length; i += 1) if (frames[i] > t0 + 100) d.push(frames[i] - frames[i - 1]);
    const s = d.slice().sort((a, b) => a - b);
    // after the pickup, the frame that lifts what is picked up, which for a theme draws its layers
    const late = [];
    for (let i = 1; i < frames.length; i += 1) if (frames[i - 1] > t0 + 150) late.push(frames[i] - frames[i - 1]);
    // each frame's step of what is dragged against an even hand's over the frame it was drawn for, where the hand
    // moves three pixels or more, the middle eight in ten of them
    const r = [];
    const live = rows.filter((x) => x.t > t0 + 200);
    for (let i = 2; i < live.length; i += 1) {
      const hand = live[i - 1].ideal - live[i - 2].ideal;
      if (Math.abs(hand) >= 3) r.push((live[i].at - live[i - 1].at) / hand);
    }
    r.sort((a, b) => a - b);
    const q = (f) => (r.length ? Math.round(r[Math.min(r.length - 1, Math.floor(f * r.length))] * 100) / 100 : null);
    return { kind, dragging, frames: d.length, median: Math.round(s[Math.floor(s.length / 2)] * 10) / 10,
      max: Math.round(s[s.length - 1] * 10) / 10, over50: d.filter((x) => x > 50).length, over50late: late.filter((x) => x > 50).length,
      added, reads: this.reads,
      steps: r.length, even: [q(0.1), q(0.9)] };
  },
};
"""

# each frame taking the latest move as it is, as a drag did until perfreview, where the pointer's place is taken a
# moment before the frame from the moves either side of then
OLD_STEP = "(() => { window.thDragAt = () => null; return 1; })()"
# the lines drawn afresh on every frame of a drag, as they were until boardperf
OLD_LINES = ("(() => { const f = thLinksDraw; window.thLinksDraw = (d) => { for (const id of ['th-links', 'th-linkends']) "
             "{ const s = document.getElementById(id); if (s) s.thDrawn = null; } return f(d); }; return 1; })()")


def make_workbook(root: Path, folder: str, speaker: str) -> Path:
    """Wren's annotated workbook, a statement to each of her 112 turns, one line long to four."""
    import workbook as wb_mod
    case = root / folder
    (case / "Source").mkdir(parents=True)
    raw = openpyxl.Workbook()
    first = raw.active
    first.title = "Initial"
    first.append(["Name", "Timestamp", "Transcript"])
    for n, said in enumerate(TALK):
        first.append(["Interviewer", f"00:{(n // 2) % 60:02d}:{(n % 2) * 30 + 4:02d}", "And then?"])
        first.append([speaker, f"00:{(n // 2) % 60:02d}:{(n % 2) * 30 + 20:02d}", said])
    source = case / "Source" / f"{folder} - interview.xlsx"
    raw.save(source)
    return wb_mod.create_from_source(source, case / f"{folder} - EN & ES.xlsx")


def statement(n: int, said: str) -> str:
    return " ".join((said.rstrip(".") + ", " + said).split()[:5 + 5 * (n % 4)])


def test_board_drag(scratch: Path):
    print("\n378. A card dragged on a large PETs board keeps the frame rate, 13 November: in WebKit, 105 cards in six "
          "PETs, two seconds of dragging within a screen's frame, nothing drawn afresh, no layout read on a move")
    import platform
    import threading
    from http.server import ThreadingHTTPServer
    import cli
    import locks
    import server as server_mod
    import themes

    swiftc = shutil.which("swiftc")
    if platform.system() != "Darwin" or not swiftc:
        skip("378: a card dragged on a large PETs board in the Mac's own window engine", "WebKit's window engine is the Mac's alone")
        return

    base = scratch / "board-drag-378"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Bees"
    root.mkdir(parents=True)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Bees", "research_question": "How do adults experience learning to keep bees?",
        "agents": {"allowed": True, "at": "2026-11-13T09:00:00+00:00"}}), encoding="utf-8")
    book = make_workbook(root, "P1 - Wren", "Wren")
    config_file = base / "config-378.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Interviewer", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": [], "card_quotes": True}), encoding="utf-8")

    def run(*args):
        return cli.run(["--config", str(config_file), "--root", str(root), *args])

    # every statement and its quote written as an agent writes a passage's, then the board built and arranged
    wrote = []
    spec = base / "spec.json"
    for n, said in enumerate(TALK):
        quote = " ".join(said.split()[-(6 + 3 * (n % 3)):]).rstrip(".")
        spec.write_text(json.dumps({"pairs": [{"statement": statement(n, said), "quote": quote}]}), encoding="utf-8")
        wrote.append(run("turn", "write", "Wren", "Initial", str(3 + 2 * n), "--from", str(spec), "--note", "Quote",
                         "--tool", "Claude Code")[0])
    made = run("board", "fresh", "Wren", "--start", "empty", "--note", "A board to build", "--tool", "Claude Code")
    f = next((root / "P1 - Wren" / "Working").glob("* - EN & ES.themes.json"))
    name = themes.current_version(json.loads(f.read_text(encoding="utf-8")))["name"]
    ids = iter(range(1, N + 1))
    ops, s_i = [], 0
    for p, (title, own, subs) in enumerate(PLAN, start=1):
        ops.append({"op": "make", "ref": f"p{p}", "title": title, "inside": None, "members": [f"S{next(ids)}" for _ in range(own)]})
        for s, size in enumerate(subs, start=1):
            ops.append({"op": "make", "ref": f"p{p}s{s}", "title": SUBS[s_i % len(SUBS)], "inside": f"p{p}",
                        "members": [f"S{next(ids)}" for _ in range(size)]})
            if s_i % 4 == 1:
                ops.append({"op": "describe", "label": f"p{p}s{s}", "description": DESCRIBED})
            s_i += 1
    ops += [{"op": "stack", "items": [f"S{k}"], "under": u}
            for k, u in zip(range(106, N + 1), ["S5", "S20", "S33", "S48", "S61", "S77", "S90"])]
    ops.append({"op": "arrange", "way": "grid"})
    spec.write_text(json.dumps({"operations": ops}), encoding="utf-8")
    built = run("board", "apply", "Wren", name, "--ops", str(spec), "--note", "Build", "--tool", "Claude Code")
    if any(wrote) or made[0] or built[0]:
        check("378: the invented board is built through the command line", False, (built[1] + built[2])[-400:])
        return

    tool = next((p for p in (scratch / "a376-wk_shot", scratch / "a192-wk_shot") if p.exists()), None)
    if tool is None:
        tool = scratch / "a378-wk_shot"
        compiled = subprocess.run([swiftc, "-O", str(support.source("packaging/wk_shot.swift")), "-o", str(tool)],
                                  capture_output=True, text=True, encoding="utf-8", timeout=600)
        if compiled.returncode != 0:
            check("378: wk_shot builds for the WebKit check", False, compiled.stderr[-400:])
            return

    open_js = f"Promise.resolve(openThemes({json.dumps(str(book))}, 'library')).then(() => document.querySelectorAll('#th-world .th-card').length)"
    steps = [{"js": open_js, "waitFor": "#th-world .th-card", "wait": 1500},
             {"js": "__bd.drag(1000)", "wait": 500},
             {"js": "__bd.drag(2000)", "wait": 500},
             {"js": "__bd.drag(2000, 250, 'title')", "wait": 500},
             {"js": OLD_STEP, "wait": 100},
             {"js": "__bd.drag(2000)", "wait": 500},
             {"js": OLD_LINES, "wait": 100},
             {"js": "__bd.drag(1000)", "wait": 100}]
    steps_file = base / "steps.json"
    steps_file.write_text(json.dumps(steps), encoding="utf-8")

    def drive():
        kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, locks.WAIT)
        httpd = None
        try:
            server_mod.CONFIG_PATH = config_file
            server_mod.ROOT_OVERRIDE = str(root)
            server_mod.STATE_MEMORY = {"recent": []}
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
            threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
            ran = subprocess.run([str(tool), "--url", f"http://127.0.0.1:{httpd.server_address[1]}/", "--out", str(base / "wk"),
                                  "--steps", str(steps_file), "--width", "1587", "--height", "1234", "--scale", "1",
                                  "--no-still", "--init", DRAG_INIT, "--timeout", "120"],
                                 capture_output=True, text=True, encoding="utf-8", timeout=180)
        finally:
            if httpd:
                httpd.shutdown()
                httpd.server_close()
            server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, locks.WAIT = kept
        said = {}
        for line in ran.stdout.splitlines():
            if line.startswith("js ") and ": " in line:
                try:
                    said[int(line[3:line.index(":")])] = json.loads(line[line.index(":") + 2:])
                except ValueError:
                    pass
        return ran, said

    def smooth(m: dict, stalls: str = "over50") -> bool:
        return bool(m) and m.get("dragging") is True and m.get("frames", 0) >= 80 and m.get("median", 99) <= 18 and m.get(stalls, 99) == 0

    # each frame's step of what is dragged against an even hand's, the middle eight in ten, within a band of it
    def even(m: dict) -> bool:
        e = (m or {}).get("even") or [None, None]
        return (m or {}).get("steps", 0) >= 50 and e[0] is not None and e[0] >= 0.7 and e[1] <= 1.35

    def held(said: dict) -> bool:
        return smooth(said.get(2)) and smooth(said.get(3), "over50late") and even(said.get(2)) and even(said.get(3))

    ran, said = drive()
    # under a full gate's load the offscreen window can be starved of frames, which says nothing of the page: once more
    if ran.returncode != 0 or not held(said):
        ran, said = drive()
    m, title, uneven, old = said.get(2) or {}, said.get(3) or {}, said.get(5) or {}, said.get(7) or {}
    check("378: in WebKit at 1587 by 1234, a card dragged left and right across a board of 105 cards in six PETs for two "
          "seconds keeps its median frame at 18 ms or less, a screen's frame being 16.7, and none over 50 ms",
          ran.returncode == 0 and said.get(0) == 105 and smooth(m), f"{said.get(0)} {m} {ran.stdout[-300:]} {ran.stderr[-300:]}")
    check("378: a PET dragged by its title across the same board, fifteen cards and labels with it, keeps its median "
          "frame at 18 ms or less and none over 50 ms after the frame that picks it up (perfreview)",
          ran.returncode == 0 and smooth(title, "over50late"), f"{title}")
    check("378: what is dragged moves an even step a frame, each frame's step within 0.7 to 1.35 of an even hand's for "
          "eight frames in ten, the card and the PET alike (perfreview)", even(m) and even(title),
          f"card {m.get('even')} over {m.get('steps')}, title {title.get('even')} over {title.get('steps')}")
    check("378: each frame taking the latest move as it is, as a drag did until perfreview, put back on the same board "
          "steps unevenly, which the watch sees", uneven.get("dragging") is True and not even(uneven), f"{uneven}")
    check("378: while the card is dragged nothing is added to the board or taken from it after the drag's first frame, "
          "the close pairs' lines among it, and the pointer's moves read no layout",
          m.get("added") == 0 and m.get("reads") == 0, f"{m}")
    check("378: the lines drawn afresh on every frame of a drag, as they were until boardperf, rebuild them on the same "
          "board, which the watch sees", old.get("dragging") is True and old.get("added", 0) > 0, f"{old}")
