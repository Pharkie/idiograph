from __future__ import annotations

import json
import re
import shutil

from . import support
from .support import SPARKLES, check, skip


def bezier_peak(x1, y1, x2, y2):
    """The furthest a CSS cubic-bezier easing runs past its end, as a fraction over 1."""
    best = 0.0
    for i in range(2001):
        t = i / 2000
        best = max(best, 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t * t * y2 + t ** 3)
    return best - 1


def test_themes_feedback_three(scratch):
    print("\n45. Themes, the third feedback: the cards lean, Statements and Themes, Auto-arrange and the "
          "sparkles, the Alt tip, stronger motion")
    import subprocess
    page = support.page_text()
    js = support.text("apps/idiograph/static/themes.js")
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0]

    # ── 104. Auto-arrange, and the sparkles on exactly the AI controls
    sparkled = []
    for button in re.findall(r"<button\b.*?</button>", page, flags=re.S):
        if SPARKLES in button:
            found = re.search(r'id="([^"]+)"', button.split(">", 1)[0])
            sparkled.append(found.group(1) if found else "?")
    names_go = fn(js, "thNamesHtml")
    check("104, 118, 173: the sparkles are on exactly the AI controls: btn-ai, btn-bench and the panel's th-names-go, "
          "New AI board, AI review and AI revise having gone (aiout)",
          sorted(sparkled) == ["btn-ai", "btn-bench"] and page.count(SPARKLES) == 2
          and js.count(SPARKLES) == 1 and js.count("TH_SPARK_ICON") == 2
          and "th-names-go" in names_go and "${TH_SPARK_ICON}" in names_go and SPARKLES not in app, str(sparkled))

    def callers(src, needles):
        out = []
        for chunk in re.split(r"\n(?=(?:async )?function \w+\()", src):
            name = re.match(r"(?:async )?function (\w+)\(", chunk)
            if name and any(n in chunk for n in needles):
                out.append(name.group(1))
        return out
    ai_routes = ("api('/api/suggest',", "api('/api/suggest-sample', body)", "api('/api/themes-ai',", "api(thAiPath(),")
    check("104: the functions that call a model are the three the sparkled controls run, and nothing else calls them",
          callers(app, ai_routes) == ["askAI", "runBench"] and callers(js, ai_routes) == ["thNamesAsk"]
          and "$('btn-ai').onclick = () => askAI();" in app and app.count("askAI(") == 2
          and "$('btn-bench').onclick = () => runBench();" in app and app.count("runBench(") == 2
          and "if (names && names.dataset.names === 'go') { thNamesAsk(); return; }" in js,
          f"{callers(app, ai_routes)} {callers(js, ai_routes)}")
    check("104: Auto-arrange and every other control carry none",
          SPARKLES not in js.split("const TH_ARR_ICON = '", 1)[1].split("';", 1)[0]
          and "TH_SPARK_ICON" not in fn(js, "thArrangeHtml") + fn(js, "thRender") + fn(js, "thMenuOpen")
          and "TH_SPARK_ICON" not in fn(js, "thVmenuDraw"))

    # ── 105. the Alt tip
    check("105: nothing about it is saved",
          not re.search(r"thSoon|thSave|thDone|thStep|api\(|localStorage|TH\.v\b", fn(js, "thTip")))

    # ── the lean and the tip, in node
    node = shutil.which("node")
    if not node:
        return skip("the third feedback's lean and tip in node", "no node on this machine")
    script = scratch / "themes-feedback-three.js"
    script.write_text(support.i18n_js() + js + r"""
const fake = () => {
  const names = new Set();
  return { style: {}, hidden: true, textContent: '', offsetWidth: 150,
    classList: { toggle: (c, on) => (on ? names.add(c) : names.delete(c)), has: (c) => names.has(c) } };
};
let calm = false;
globalThis.window = { matchMedia: () => ({ matches: calm }), innerWidth: 1200, innerHeight: 800 };
const tip = fake();
globalThis.$ = (id) => (id === 'th-tip' ? tip : null);
globalThis.MAC = true;
const out = {};
const turns = (ids) => ids.map((id) => (TH.els.cards[id] || TH.els.labels[id]).style.rotate || '');
// 102: a theme dragged by its label: the label and every card it carries lean the same way
TH.els = { cards: { a: fake(), b: fake(), c: fake() }, labels: { g1: fake() }, frames: {} };
const theme = { moving: new Set(['g1', 'a', 'b']), grabbed: new Set(['g1']), lean: 0, lastX: 0, still: null };
TH.drag = theme;
thLean({ clientX: 40 });
out.fast = turns(['g1', 'a', 'b', 'c']);
theme.lean = 0; theme.lastX = 0;
thLean({ clientX: 2 });
out.slow = turns(['g1', 'a', 'b']);
theme.lean = 0; theme.lastX = 0;
thLean({ clientX: -400 });
out.back = turns(['g1', 'a', 'b']);
clearTimeout(theme.still);
// 102: a card dragged on its own leans too
TH.els = { cards: { a: fake() }, labels: {}, frames: {} };
const single = { moving: new Set(['a']), grabbed: new Set(['a']), lean: 0, lastX: 0, still: null };
TH.drag = single;
thLean({ clientX: 30 });
out.single = turns(['a']);
clearTimeout(single.still);
// reduced motion: no lean at all
TH.els = { cards: { a: fake() }, labels: {}, frames: {} };
calm = true;
const still = { moving: new Set(['a']), grabbed: new Set(['a']), lean: 0, lastX: 0, still: null };
TH.drag = still;
thLean({ clientX: 30 });
out.calm = turns(['a']);
calm = false;
// 105: the words, by the platform and by Alt
out.words = [thTipText(false, true), thTipText(false, false), thTipText(true, true), thTipText(true, false)];
// 105: the tip follows the pointer, says what Alt does, and goes with the drag
TH.drag = { tip: true, alt: false };
thTip({ clientX: 100, clientY: 200 });
out.shown = [tip.hidden, tip.textContent, tip.style.left, tip.style.top];
TH.drag.alt = true;
thTip();
out.held = [tip.hidden, tip.textContent, tip.classList.has('alt'), tip.style.left];
TH.drag = null;
thTip();
out.gone = tip.hidden;
TH.drag = { tip: false, alt: false };
thTip({ clientX: 100, clientY: 200 });
out.never = tip.hidden;
TH.drag = null;
// 105: who the tip is for: a card in a theme and a sub-theme, never a card in none or a theme on its own
const card = (x, y) => ({ x, y, text: 't' });
const v = { cards: { 'm:1:0': card(0, 0), 'm:2:0': card(0, 200), 'm:3:0': card(900, 0), 'm:4:0': card(0, 400) },
  groups: [], discarded: [], picks: {} };
const outer = thMakeGroup(v, ['m:1:0', 'm:2:0', 'm:4:0'], 'Outer');
const inner = thMakeGroup(v, ['m:4:0'], 'Inner');
const shows = (cards, groups) => thLeavers(v, thMoving(v, new Set(cards), new Set(groups))).size > 0;
out.who = [shows(['m:1:0'], []), shows(['m:3:0'], []), shows([], [outer]), shows([], [inner]), shows(['m:4:0'], [])];
console.log(JSON.stringify(out));
""", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("the third feedback's lean and tip run in node", False, run.stderr.strip()[:300])
    out = json.loads(run.stdout)
    check("102: with reduced motion nothing leans", out["calm"] == [""], str(out["calm"]))
    check("105: it is for a card in a theme and a sub-theme, never a card in no theme or a theme dragged by its own label",
          out["who"] == [True, False, False, True, True], str(out["who"]))
