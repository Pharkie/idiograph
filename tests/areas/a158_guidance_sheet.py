from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import rounds as rounds_mod

from . import support
from .support import check, skip


def test_guidance_sheet(scratch):
    print("\n158. The guidance a sheet over the right of the statements screen, 16 October, Adam's decision on a "
          "tester's feedback: closed by default and in no column, so the exploratory notes stand beside the transcript "
          "at 1280, opened from Guidance on the bar and closed by its close button, the tool, g, Esc or a click outside, "
          "kept across a reload, and the screenshot check's fixes to the minimap, the selection's toolbar and the way back. "
          "Since the test review of 18 October its layout, colours and words are review shots, and what a key, a press "
          "and a reload do stays")
    import subprocess

    read = lambda path: Path(path).read_text(encoding="utf-8")
    page, app = support.page_text(), support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    after = lambda src, a, b: src.split(a, 1)[1].split(b, 1)[0] if a in src and b in src.split(a, 1)[1] else ""
    node = shutil.which("node")
    keydown = support.keydown_text(app)

    check("158: g is the guidance's key alone on the statements screen, outside a field",
          keydown.count("key === 'g'") == 1 and "else if (key === 'g' && !$('work').hidden) { toggleGuide(); }" in keydown
          and keydown.index("if (typing || MOD(e) || e.altKey) return;") < keydown.index("key === 'g'"))

    # ── B. the sheet in node: opened and closed every way, closed by default, kept across a reload
    guide_src = after(app, "const GUIDE_KEY = ", "\nconst toggleGuide = ")
    toggle_line = "const toggleGuide = " + after(app, "\nconst toggleGuide = ", "\n") if guide_src else ""
    outside = after(app, "  document.addEventListener('pointerdown', (e) => {\n    if (guideOpen()", "\n  }, true);")
    escape = after(keydown, "      if (guideOpen() && !$('work').hidden && !anyOverlayOpen()) {", "\n      }")
    if not node:
        skip("158: the sheet in node", "node is not on this machine")
    else:
        code = r"""
let STORE = new Map();
let THROWS = false;
const localStorage = {
  getItem(k) { if (THROWS) throw new Error('private'); return STORE.has(k) ? STORE.get(k) : null; },
  setItem(k, v) { if (THROWS) throw new Error('private'); STORE.set(k, String(v)); },
};
const FOCUS = [];
const handlers = {};
const document = { activeElement: null, addEventListener(type, f, capture) { handlers[type] = { f, capture }; } };
const mk = (id, kids = []) => {
  const e = { id, kids, attrs: {}, cls: new Set(), onclick: null,
    setAttribute(k, v) { this.attrs[k] = v; }, contains(x) { return x === this || this.kids.includes(x); },
    focus() { document.activeElement = this; FOCUS.push(id); } };
  e.classList = { toggle: (c, on) => (on ? e.cls.add(c) : e.cls.delete(c)), contains: (c) => e.cls.has(c) };
  return e;
};
let els;
const $ = (id) => els[id];
let OVERLAY = false;
const anyOverlayOpen = () => OVERLAY;
const fresh = () => {
  const close = mk('guide-close');
  els = { guide: mk('guide', [close]), 'guide-close': close, 'btn-guide': mk('btn-guide'), work: { hidden: false } };
  document.activeElement = null;
  FOCUS.length = 0;
};
fresh();
const GUIDE_KEY = """ + guide_src + "\n" + toggle_line + r"""
const wire = () => {
""" + "\n".join(ln for ln in app.splitlines() if ln.strip() in ("$('btn-guide').onclick = () => toggleGuide(true);",
                                                               "$('guide-close').onclick = () => guide(false, { keep: true, focus: true });")) + r"""
  document.addEventListener('pointerdown', (e) => {
    if (guideOpen()""" + outside + r"""
  }, true);
};
const boot = () => { fresh(); guide(guideStored()); wire(); };
const press = (inside) => { const e = { prevented: false, stopped: false, preventDefault() { this.prevented = true; },
  stopPropagation() { this.stopped = true; }, target: { closest: () => (inside ? {} : null) } };
  handlers.pointerdown.f(e); return { prevented: e.prevented, stopped: e.stopped, capture: handlers.pointerdown.capture }; };
const esc = () => { const e = { prevented: false, preventDefault() { this.prevented = true; } };
  (() => { if (guideOpen() && !$('work').hidden && !anyOverlayOpen()) {""" + escape + r"""
  } })(); return e.prevented; };
const gKey = (e = { key: 'g' }) => { if (false) {}
  """ + "else if (e.key === 'g' && !$('work').hidden) { toggleGuide(); }" + r""" };
const state = () => ({ open: $('guide').cls.has('open'), expanded: $('btn-guide').attrs['aria-expanded'],
  kept: STORE.has(GUIDE_KEY) ? STORE.get(GUIDE_KEY) : null, focus: FOCUS.slice() });
const out = {};
boot(); out.fresh = state();
for (const v of ['away', 'here', 'yes', '', 'closed', 'open']) { STORE = new Map([[GUIDE_KEY, v]]); boot(); out['kept_' + (v || 'empty')] = state().open; }
STORE = new Map(); boot();
$('btn-guide').onclick(); out.tool = state();
boot(); out.reloadOpen = state();
$('guide-close').onclick(); out.close = state();
boot(); out.reloadClosed = state();
$('btn-guide').onclick(); FOCUS.length = 0; $('btn-guide').onclick(); out.toolAgain = state();
FOCUS.length = 0; gKey(); out.gOpen = state(); gKey(); out.gClose = state();
gKey(); $('guide-close').focus(); FOCUS.length = 0; gKey(); out.gFromInside = state();
$('btn-guide').onclick(); FOCUS.length = 0; out.escPrevented = esc(); out.esc = state(); out.escAgain = esc();
$('btn-guide').onclick(); OVERLAY = true; out.escUnderCard = esc(); out.underCard = state().open; OVERLAY = false; esc();
$('btn-guide').onclick(); FOCUS.length = 0; out.pressIn = press(true); out.inside = state().open;
out.pressOut = press(false); out.outside = state();
$('btn-guide').onclick(); $('work').hidden = true; press(false); out.elsewhere = state().open; out.escElsewhere = esc();
$('work').hidden = false; esc();
THROWS = true; boot(); out.privateStart = state().open; $('btn-guide').onclick(); out.privateTool = state().open;
console.log(JSON.stringify(out));
"""
        script = scratch / "guidance-sheet-158.js"
        script.write_text(code, encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        o = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
        if not o:
            check("158: the sheet runs in node", False, (run.stderr or run.stdout).strip()[:300])
        else:
            check("158: in node, a new install starts with the sheet closed and keeps nothing until a press, and only a "
                  "kept open opens it, an old away or here, an empty or an unknown value reading as closed",
                  o["fresh"] == {"open": False, "expanded": "false", "kept": None, "focus": []}
                  and [o[f"kept_{k}"] for k in ("away", "here", "yes", "empty", "closed", "open")] == [False] * 5 + [True],
                  str(o["fresh"]))
            check("158: in node, the bar's tool opens it, the keyboard going to its close button, and a reload opens it "
                  "as left, its close button closes it, the keyboard back on the tool, and a reload keeps it closed",
                  o["tool"] == {"open": True, "expanded": "true", "kept": "open", "focus": ["guide-close"]}
                  and o["reloadOpen"]["open"] is True and o["reloadOpen"]["focus"] == []
                  and o["close"] == {"open": False, "expanded": "false", "kept": "closed", "focus": ["btn-guide"]}
                  and o["reloadClosed"]["open"] is False, str([o["tool"], o["close"]]))
            check("158: in node, the tool again closes it, and g opens and closes it with the focus left where it was, "
                  "unless it was inside the sheet, which hands it to the tool",
                  o["toolAgain"] == {"open": False, "expanded": "false", "kept": "closed", "focus": ["btn-guide"]}
                  and o["gOpen"] == {"open": True, "expanded": "true", "kept": "open", "focus": []}
                  and o["gClose"] == {"open": False, "expanded": "false", "kept": "closed", "focus": []}
                  and o["gFromInside"] == {"open": False, "expanded": "false", "kept": "closed", "focus": ["btn-guide"]},
                  str([o["toolAgain"], o["gOpen"], o["gFromInside"]]))
            check("158: in node, Esc closes it and keeps it closed, the keyboard on the tool, and does nothing with it "
                  "closed or under a card",
                  o["escPrevented"] is True and o["esc"] == {"open": False, "expanded": "false", "kept": "closed", "focus": ["btn-guide"]}
                  and o["escAgain"] is False and o["escUnderCard"] is False and o["underCard"] is True, str(o["esc"]))
            check("158: in node, a press inside the sheet or on its tool leaves it open, a press outside closes it and "
                  "keeps it closed and goes on to do what it does, the keyboard handed from inside it to the tool, and on "
                  "another screen a press or Esc leaves it be",
                  o["pressIn"] == {"prevented": False, "stopped": False, "capture": True} and o["inside"] is True
                  and o["pressOut"] == {"prevented": False, "stopped": False, "capture": True}
                  and o["outside"] == {"open": False, "expanded": "false", "kept": "closed", "focus": ["btn-guide"]}
                  and o["elsewhere"] is True and o["escElsewhere"] is False, str([o["pressOut"], o["outside"]]))
            check("158: in node, a private window, whose storage refuses, starts closed and still opens it",
                  o["privateStart"] is False and o["privateTool"] is True)

    line_of = lambda src, start: start + src.split(start, 1)[1].split("\n", 1)[0] if start in src else ""
    if not node:
        skip("158, 17 October: the keyboard after a reload in node", "node is not on this machine")
    else:
        code = r"""
let STORE = new Map([['idiograph-guide', 'open']]);
const localStorage = { getItem: (k) => (STORE.has(k) ? STORE.get(k) : null), setItem: (k, v) => STORE.set(k, String(v)) };
const document = { activeElement: null };
const FOCUS = [];
const mk = (id, kids = []) => { const e = { id, kids, attrs: {}, cls: new Set(), hidden: false,
  setAttribute(k, v) { this.attrs[k] = v; }, contains(x) { return x === this || this.kids.includes(x); },
  focus() { document.activeElement = this; FOCUS.push(id); }, querySelector: () => null };
  e.classList = { toggle: (c, on) => (on ? e.cls.add(c) : e.cls.delete(c)), contains: (c) => e.cls.has(c) }; return e; };
const es = mk('pair-es');
const pair = { querySelector: () => es };
const close = mk('guide-close');
const els = { guide: mk('guide', [close]), 'guide-close': close, 'btn-guide': mk('btn-guide'), work: mk('work'), note: mk('note') };
const $ = (id) => els[id];
const S = { note: null, editing: null, timeEdit: null };
const workingPair = () => pair;
// every column shown, as on a new install (186)
const colsHidden = () => false;
const GUIDE_KEY = """ + after(app, "const GUIDE_KEY = ", "\nconst toggleGuide = ") + "\n" + whole(app, "focusEntry") + "\n" + whole(app, "guideHolds") + r"""
const out = {};
// the page's start with the sheet kept open, then the case shown, as a reload does
guide(guideStored()); focusEntry(); out.reload = { open: guideOpen(), focus: FOCUS.slice() };
// a move by its keys with the keyboard inside the sheet leaves it there
FOCUS.length = 0; focusEntry(); out.inside = FOCUS.slice();
// closed, the statement takes the caret as it always did
guide(false, { keep: true }); FOCUS.length = 0; document.activeElement = null; focusEntry(); out.closed = FOCUS.slice();
// open on another screen, the sheet hidden with it, it holds nothing
guide(true); els.work.hidden = true; FOCUS.length = 0; out.elsewhere = [guideHolds(), FOCUS.slice()];
console.log(JSON.stringify(out));
"""
        script = scratch / "guidance-focus-158.js"
        script.write_text(code, encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        o = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
        check("158, 17 October: in node, a reload with the sheet kept open shows it open with the keyboard on its close "
              "button, never in the statement under it, a move with the keyboard inside it leaves it there, closed the "
              "statement takes the caret, and on another screen the sheet holds nothing",
              o.get("reload") == {"open": True, "focus": ["guide-close"]} and o.get("inside") == []
              and o.get("closed") == ["pair-es"] and o.get("elsewhere") == [False, []], (run.stdout + run.stderr)[:300])


    # Statements complete, and why it is right on the demo
    sheets = [{"name": "Initial", "rows": [
        {"sheet": "Initial", "row": r, "name": who, "es": es, "text": "A walk by the canal.", "time": "00:00", "seconds": 0}
        for r, who, es in ((2, "Adam", ""), (3, "Wren", "Noticing the water first"), (4, "Adam", ""), (5, "Wren", ""))]}]
    skipped = {"rows": {"Initial:3": "has-content", "Initial:5": "reviewed-empty"}, "last": {"sheet": "Initial", "row": 5}}
    states = rounds_mod.row_states(sheets, skipped, "Adam")
    open_last = rounds_mod.row_states(sheets, {"rows": {"Initial:3": "has-content"}, "last": {"sheet": "Initial", "row": 3}}, "Adam")
    shipped = {n: json.loads((support.source("demo/pristine/Working") / f"{n} - EN & ES.progress.json").read_text(encoding="utf-8"))
               for n in ("Rowan", "Mabel")}
    check("158, 17 October: Statements complete is right while statement 1 is empty: a passage skipped, decided with no "
          "statement, counts as decided, so a case marked complete with every passage decided reads complete, and the "
          "demo's Rowan and Mabel are marked and open on their last passage, which was skipped",
          rounds_mod.REVIEWED_EMPTY in rounds_mod.DECIDED and states == {"Initial:3": "has-content", "Initial:5": "reviewed-empty"}
          and open_last["Initial:5"] == "unvisited"
          and all(p.get("complete", {}).get("at") and p["rows"][f"{p['last']['sheet']}:{p['last']['row']}"] == "reviewed-empty"
                  and all(v in ("has-content", "reviewed-empty") for v in p["rows"].values()) for p in shipped.values()),
          str(states))
    if not node:
        skip("158, 17 October: the bar's mark in node", "node is not on this machine")
    else:
        code = r"""
const mk = () => ({ hidden: false, textContent: '', innerHTML: '', title: '', cls: new Set(),
  get classList() { const c = this.cls; return { toggle: (k, on) => (on ? c.add(k) : c.delete(k)) }; } });
const els = {};
const $ = (id) => (els[id] || (els[id] = mk()));
const roundsHere = () => false;
""" + support.i18n_js() + "\n" + whole(app, "whenOf") + "\n" + whole(app, "drawMark") + r"""
const shown = () => ({ mark: !$('rail-mark').hidden, date: $('rail-mark-date').textContent, left: $('rail-mark-left').innerHTML.replace(/<[^>]+>/g, '') });
const out = {};
drawMark({ caseDone: 2, caseTotal: 2 }, { complete: '2026-09-30T10:06:30' }); out.decided = shown();
drawMark({ caseDone: 1, caseTotal: 2 }, { complete: '2026-09-30T10:06:30' }); out.open = shown();
console.log(JSON.stringify(out));
"""
        script = scratch / "complete-158.js"
        script.write_text(code, encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        o = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
        check("158, 17 October: in node, the bar says Statements complete with its date only when every passage is "
              "decided, and with one undecided it says so beside the mark, so it never claims a passage left open",
              o.get("decided") == {"mark": True, "date": "30 Sep 2026", "left": ""}
              and o.get("open") == {"mark": True, "date": "", "left": " · 1 passage undecided"}, (run.stdout + run.stderr)[:300])

    if not node:
        skip("158, 17 October: the player in node", "node is not on this machine")
    else:
        code = r"""
const mk = () => ({ hidden: true, textContent: '', attrs: {}, src: '', pause() {}, removeAttribute(k) { delete this.attrs[k]; },
  getAttribute(k) { return this.attrs[k] || null; } });
const els = { player: mk(), 'player-bar': mk(), 'player-wrap': mk(), 'player-note': mk(), 'player-offset': mk() };
const $ = (id) => els[id];
const S = { data: { path: 'Wren.xlsx' }, audioSheet: null };
let ANSWER = null;
const LATER = [];
const setTimeout = (f) => LATER.push(f);
const api = async () => { if (ANSWER === 'fail') throw new Error('no'); return ANSWER; };
const cueAudio = () => {}; const drawPlayer = () => {}; const drawOffsetButton = () => {};
// the demo's recordings on demand (recdemand, 13 November 2026), which a plain participant never reaches
const REC_GET = { box: '' }; const recGetClose = () => {}; const recGetTurn = () => {}; const markTurnAt = () => {};
const said = [];
const say = (m) => said.push(m);
""" + "async " + whole(app, "loadAudio") + "\n" + whole(app, "playFrom") + r"""
const state = () => ({ wrap: !$('player-wrap').hidden, bar: !$('player-bar').hidden, note: $('player-note').textContent });
(async () => {
  const out = {};
  ANSWER = { found: false, note: 'No recording found for Initial.' };
  const p = loadAudio('Initial', 0); out.looking = state(); await p; out.none = state();
  playFrom(12); out.said = said.slice();
  ANSWER = { found: true, url: '/audio?x', name: 'Wren.m4a' }; S.audioSheet = null; await loadAudio('Second', 0); out.found = state();
  ANSWER = 'fail'; S.audioSheet = null; await loadAudio('Fourth', 0); out.failed = state();
  console.log(JSON.stringify(out));
})();
"""
        script = scratch / "player-158.js"
        script.write_text(support.i18n_js() + code, encoding="utf-8")
        run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        o = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
        check("158, 17 October: in node, nothing shows while the recording is looked for or when there is none, a press on "
              "a timecode says the server's line, a recording found shows the player, and a failure shows nothing",
              o.get("looking") == {"wrap": False, "bar": False, "note": ""}
              and o.get("none") == {"wrap": False, "bar": False, "note": "No recording found for Initial."}
              and o.get("said") == ["No recording found for Initial."]
              and o.get("found") == {"wrap": True, "bar": True, "note": "Wren.m4a"}
              and o.get("failed") == {"wrap": False, "bar": False, "note": "No recording for this sheet."}, (run.stdout + run.stderr)[:300])

    # the participant is they in the guidance and in every prompt the screen shows
    guidance_md = read(support.source("apps/idiograph/guidance.md"))
    work_page = after(page, '<section id="work"', "\n</section>")
    prompts = ([ln for ln in guidance_md.splitlines() if ln.startswith(("- ", "* "))]
               + re.findall(r'placeholder="([^"]*)"', work_page)
               + re.findall(r"'([^']*)'", after(app, "const NOTE_PROMPTS = [", "];")))
    gendered = [p for p in prompts if re.search(r"\b(she|her|hers|herself)\b", p, flags=re.I)]
    check("158, 17 October later: the guidance's lines, its craft prompts, every placeholder on the statements screen "
          "and the interviewer note's prompts speak of the participant as they, their or them, never she or her",
          not gendered and len(prompts) >= 20, str(gendered[:4]))

