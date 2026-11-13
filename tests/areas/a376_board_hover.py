"""Area 376: the PETs canvas stands still under the pointer (boardhover, 13 November 2026).

Adam saw the whole PETs board redraw a little, its coloured outlines changing for a moment, each time the pointer went
into a PET or a sub-PET or out of it. In WebKit, the Mac window's engine, a label's small controls faded in and out by
their opacity, which WebKit runs on a layer of its own, and while the fade ran it drew the whole board as a layer too,
the canvas's zoom and its offset of a fraction of a pixel laid over it whole. Here, in WebKit through
packaging/wk_shot.swift, on the demo's Juno board served by the app's own handler, at Text sizes 100% and 110%, the
pointer going into a PET's label, a sub-PET's and the empty inside of a frame and out again moves no box, changes no
outline's width and makes no layer, and the old fade put back on the same board makes one, so the watch can see it.
"""
from __future__ import annotations

import json
import shutil
import subprocess

from . import support
from .support import DEMO_QUESTION, check, skip

# The pointer in the page: an offscreen WebKit window in a process that is never active takes no mouse moves, so every
# :hover in the stylesheets reads .bh-hover instead, set on the element under the point and its ancestors as :hover
# would be, and the pointer events the board listens for are sent as a move sends them
HOVER_INIT = r"""
window.__bh = {
  ready: false, chain: [], s0: null,
  css() {
    if (this.ready) return;
    const walk = (list) => {
      for (const r of list) {
        if (r.cssRules && !r.selectorText) walk(r.cssRules);
        else if (r.selectorText && r.selectorText.includes(':hover')) r.selectorText = r.selectorText.replace(/:hover/g, '.bh-hover');
      }
    };
    for (const s of document.styleSheets) { try { walk(s.cssRules); } catch (e) { /* another origin's */ } }
    this.ready = true;
  },
  at(x, y) {
    this.css();
    const el = document.elementFromPoint(x, y);
    const next = [];
    for (let e = el; e; e = e.parentElement) next.push(e);
    const prev = this.chain, was = prev[0];
    const o = { bubbles: true, cancelable: true, composed: true, clientX: x, clientY: y, pointerId: 1, pointerType: 'mouse', isPrimary: true };
    if (was && was !== el) {
      was.dispatchEvent(new PointerEvent('pointerout', { ...o, relatedTarget: el }));
      for (const e of prev) if (!next.includes(e)) e.dispatchEvent(new PointerEvent('pointerleave', { ...o, bubbles: false }));
    }
    for (const e of prev) if (!next.includes(e)) e.classList.remove('bh-hover');
    for (const e of next) e.classList.add('bh-hover');
    if (el && el !== was) {
      el.dispatchEvent(new PointerEvent('pointerover', { ...o, relatedTarget: was || null }));
      for (const e of next.slice().reverse()) if (!prev.includes(e)) e.dispatchEvent(new PointerEvent('pointerenter', { ...o, bubbles: false }));
    }
    if (el) el.dispatchEvent(new PointerEvent('pointermove', o));
    this.chain = next;
    return el ? [...el.classList].filter((c) => c !== 'bh-hover').join('.') || el.id : '';
  },
  // the pointer on the label's middle
  on(sel) {
    const l = document.querySelector(sel), b = l.getBoundingClientRect();
    this.at(Math.round(b.left + b.width / 2), Math.round(b.top + b.height / 2));
    this.last = l;
    return this.chain.includes(l) ? 'label' : 'missed';
  },
  // the stage itself under the point: away from everything, or a frame's empty inside below its label
  empty(box) {
    for (let y = box.bottom - 3; y > box.top + 4; y -= 2) for (let x = box.left + 4; x < box.right - 4; x += 3) {
      const e = document.elementFromPoint(x, y);
      if (e && e.id === 'th-stage') { this.at(x, y); return 'stage'; }
    }
    return 'nowhere';
  },
  away() { const s = document.getElementById('th-stage').getBoundingClientRect(); return this.empty({ left: s.right - 60, right: s.right - 10, top: s.top + 60, bottom: s.top + 200 }); },
  inFrame() { return this.empty(document.querySelector('#th-world .th-frame').getBoundingClientRect()); },
  boxes() {
    const out = {};
    document.querySelectorAll('#th-world .th-label, #th-world .th-frame, #th-world .th-card, #th-world .th-badge, #th-stage').forEach((e, i) => {
      const b = e.getBoundingClientRect(), cs = getComputedStyle(e);
      out[i] = [b.left, b.top, b.width, b.height, cs.borderTopWidth, cs.borderLeftWidth, cs.borderBottomWidth, cs.outlineWidth].join(' ');
    });
    out.world = document.getElementById('th-world').style.transform;
    return out;
  },
  // the boxes that moved since the pointer was first away, and whether the label last aimed at shows its cross, drawn
  // in a colour of its own once its fade is over
  after() {
    const now = this.boxes();
    const moved = Object.keys(this.s0).filter((k) => now[k] !== this.s0[k]).length;
    const del = this.last && this.last.querySelector('.th-del');
    return `${moved} ${del && getComputedStyle(del).color !== 'rgba(0, 0, 0, 0)' ? 'shown' : 'hidden'}`;
  },
};
"""

# main's way until boardhover: the label's controls faded by their opacity
OLD_FADE = ("(() => { const s = document.createElement('style'); s.textContent = '.th-label .th-del, .th-label .th-arr, "
            ".th-label .th-more { opacity: 0; transition: opacity .14s } .th-label.bh-hover .th-del, .th-label.bh-hover .th-arr, "
            ".th-label.bh-hover .th-more { opacity: 1 }'; document.head.appendChild(s); return 1; })()")

WATCH = {"every": 16, "for": 450}
PET = "#th-world .th-label.upper"
SUB = "#th-world .th-label:not(.upper)"


def test_board_hover(scratch):
    print("\n376. The PETs canvas still under the pointer, 13 November: in WebKit at 100% and 110%, into a PET's label, a "
          "sub-PET's and a frame's empty inside and out again, no box moved, no outline's width changed, no layer made")
    import platform
    import threading
    from http.server import ThreadingHTTPServer
    import locks
    import server as server_mod

    swiftc = shutil.which("swiftc")
    if platform.system() != "Darwin" or not swiftc:
        skip("376: the PETs canvas under the pointer in the Mac's own window engine", "WebKit's window engine is the Mac's alone")
        return
    tool = scratch / "a376-wk_shot"
    made = subprocess.run([swiftc, "-O", str(support.source("packaging/wk_shot.swift")), "-o", str(tool)],
                          capture_output=True, text=True, encoding="utf-8", timeout=600)
    if made.returncode != 0:
        check("376: wk_shot builds for the WebKit check", False, made.stderr[-400:])
        return

    # the demo as it ships, whose Juno has three PETs holding nine sub-PETs on her board
    pristine = support.source("demo/pristine")
    root = scratch / "a376-root"
    shutil.rmtree(root, ignore_errors=True)
    (root / "Juno" / "Working").mkdir(parents=True)
    book = root / "Juno" / "Juno - EN & ES.xlsx"
    shutil.copy2(pristine / "Juno - EN & ES.xlsx", book)
    for side in (pristine / "Working").glob("Juno - *"):
        shutil.copy2(side, root / "Juno" / "Working" / side.name)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({"name": "Dogs, a board under the pointer",
                                                           "research_question": DEMO_QUESTION}), encoding="utf-8")
    config_file = scratch / "a376-config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "corpus": "", "corpus_exclude": [],
                                       "gravity_reference": ""}), encoding="utf-8")

    steps = [{"js": f"Promise.resolve(openThemes({json.dumps(str(book))}, 'library')).then(() => 'open')",
              "waitFor": "#th-world .th-label", "wait": 1500}]
    rounds = []
    for zoom in (1.0, 1.1):
        steps += [{"size": [1587, 1234], "zoom": zoom, "js": "__bh.away()", "wait": 700},
                  {"js": "(__bh.s0 = __bh.boxes(), Object.keys(__bh.s0).length)", "wait": 50}]
        for where, move in (("a PET's label", f"__bh.on({json.dumps(PET)})"), ("a sub-PET's label", f"__bh.on({json.dumps(SUB)})"),
                            ("a frame's empty inside", "__bh.inFrame()")):
            for way, js in (("into " + where, move), ("out of " + where, "__bh.away()")):
                rounds.append((zoom, way, len(steps), len(steps) + 1))
                steps += [{"js": js, "wait": 0, "layers": WATCH}, {"js": "__bh.after()", "wait": 0}]
    control = len(steps) + 2
    steps += [{"zoom": 1.0, "js": "__bh.away()", "wait": 600}, {"js": OLD_FADE, "wait": 300},
              {"js": f"__bh.on({json.dumps(PET)})", "wait": 0, "layers": WATCH}]
    steps_file = scratch / "a376-steps.json"
    steps_file.write_text(json.dumps(steps), encoding="utf-8")

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, locks.WAIT)
    httpd = None
    try:
        server_mod.CONFIG_PATH = config_file
        server_mod.ROOT_OVERRIDE = str(root)
        server_mod.STATE_MEMORY = {"recent": []}
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
        threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
        ran = subprocess.run([str(tool), "--url", f"http://127.0.0.1:{httpd.server_address[1]}/", "--out", str(scratch / "a376-wk"),
                              "--steps", str(steps_file), "--width", "1587", "--height", "1234", "--scale", "1",
                              "--scheme", "dark", "--overlay-bars", "--no-still", "--init", HOVER_INIT, "--timeout", "150"],
                             capture_output=True, text=True, encoding="utf-8", timeout=200)
    finally:
        if httpd:
            httpd.shutdown()
            httpd.server_close()
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, locks.WAIT = kept

    said, layers = {}, {}
    for line in ran.stdout.splitlines():
        for head, into in (("js ", said), ("layers ", layers)):
            if line.startswith(head) and ": " in line:
                try:
                    into[int(line[len(head):line.index(":")])] = json.loads(line[line.index(":") + 2:])
                except ValueError:
                    pass
    if ran.returncode == 0 and all(layers.get(i) is None for _, _, i, _ in rounds) and layers.get(control) is None:
        skip("376: the PETs canvas's layers under the pointer", "this WebKit does not describe its layers")
        return
    seen = [(zoom, way, said.get(i), layers.get(i), said.get(j)) for zoom, way, i, j in rounds]
    on_label = lambda way: way.startswith("into") and "label" in way
    still = [s for s in seen if s[3] and s[3]["most"] == s[3]["least"] and s[2] == ("label" if on_label(s[1]) else "stage")
             and s[4] == ("0 shown" if on_label(s[1]) else "0 hidden")]
    check("376: in WebKit at 100% and 110%, the pointer going into a PET's label, a sub-PET's and a frame's empty inside "
          "and out of each moves no box on the board, changes no outline's width and makes no layer, so nothing is drawn "
          "again, and a label under it shows its controls", ran.returncode == 0 and len(seen) == 12 and len(still) == 12,
          f"{[s for s in seen if s not in still]} {ran.stdout[:400]} {ran.stderr[-300:]}")
    old = layers.get(control) or {}
    check("376: the label's controls faded by their opacity, as they were until boardhover, make layers for the fade on "
          "the same board, which the watch sees", old.get("most", 0) > old.get("least", 0), f"{old}")
