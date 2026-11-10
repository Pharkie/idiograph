"""Area 275: Settings opens on a page that serves one app alone (26 October 2026, panefix). Since train 53 each app
ships alone, so Idiograph's page holds no pane of Sift's or Trace's, and each of theirs none of Idiograph's. The
family's `showPane` still set `hidden` on every category the card has ever held, so on each app's own page it threw
on the first pane the page lacks and Settings never opened, from Home or from any screen. And the shell's list of
cards held Idiograph's, so on Sift's and Trace's pages every key past the cards threw in `anyOverlayOpen` and Escape
never closed Settings. Both now pass over what the page does not hold.

The harness runs the shell's own functions in node against the ids each app's served page really holds, so a
pane or a card missing from a page is missing here too. No fixture data is needed."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from . import support
from .support import check, skip


def test_settings_opens_alone(scratch: Path):
    print("\n275. Settings opens on each app's own page, served alone: from its screen's button on the category the "
          "screen asks for, a click on each category showing it, the arrow keys walking them all, and Escape closing "
          "it, with no pane or card of another app's in the page (26 October 2026)")
    import boot

    shell = support.text("family/static/shell.js")
    lines = shell.splitlines()
    fn = lambda name: shell.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in shell else ""
    whole = lambda name: f"function {name}(" + fn(name) + "\n}"
    line = lambda start: next((ln for ln in lines if ln.startswith(start)), "")

    node = shutil.which("node")
    if not node:
        skip("275: Settings on each app's page in node", "node is not on this machine")
        return

    pieces = ["const PANES_BY_APP = {" + shell.split("const PANES_BY_APP = {", 1)[1].split("};", 1)[0] + "};",
              line("const PANES_ALL = "), line("const PANES = "), "let paneHeld = 'general';", line("const onScreen = "),
              line("const PANE_OF = "), whole("screenPane"), whole("showPane"), whole("paneKeys"), line("const OVERLAYS = "),
              line("const overlaysHere = "), line("const anyOverlayOpen = "), "function cardOpen() {}", line("const show = "),
              "const hide = (id) => { $(id).hidden = true; };"]
    harness = r"""
const [APP, ids, tabNames] = JSON.parse(process.argv[2]);
const els = {};
for (const id of ids) els[id] = { id, hidden: id.startsWith('pane-') || id === 'settings', scrollTop: 5 };
// the screens: Home in front
for (const s of ['library', 'work', 'themes', 'sift', 'sift-search', 'trace']) if (els[s]) els[s].hidden = s !== 'library';
const $ = (id) => els[id] || null;
const tabs = tabNames.map((p) => ({ dataset: { pane: p }, attrs: {}, tabIndex: -1, classList: { toggle() {} },
  setAttribute(k, v) { this.attrs[k] = v; }, focus() {} }));
const document = { querySelectorAll: () => tabs };
const appsSay = () => null;
""" + "\n".join(pieces) + r"""
const shown = () => Object.values(els).filter((e) => e.id.startsWith('pane-') && !e.hidden).map((e) => e.id.slice(5));
const out = { app: APP, panes: PANES };
const tryIt = (f) => { try { return f(); } catch (err) { return 'threw: ' + err.message; } };
// Settings from Home's button: openSettings('general') shows the pane, then the card
out.home = tryIt(() => { showPane('general'); show('settings'); return [!els.settings.hidden, shown()]; });
// a click on each category in the nav
out.clicks = PANES.map((p) => tryIt(() => { showPane(p); return shown(); }));
// the arrow keys from General round to it again
out.arrows = tryIt(() => {
  showPane('general');
  const seen = [];
  for (let i = 0; i < PANES.length; i++) { paneKeys({ key: 'ArrowDown', preventDefault() {} }); seen.push(shown().join(',')); }
  return seen;
});
// another app's category asked for opens General, as before
out.other = tryIt(() => { showPane(APP === 'idiograph' ? 'sift' : 'statements'); return shown(); });
// Escape with Settings open closes every card the page holds, and a key with none open finds none
out.escape = tryIt(() => { const open = anyOverlayOpen(); if (open) overlaysHere().forEach(hide); return [open, els.settings.hidden, anyOverlayOpen()]; });
console.log(JSON.stringify(out));
"""
    script = scratch / "a275-settings.js"
    script.write_text(harness, encoding="utf-8")
    for app in boot.APPS:
        page = support.page_text(app=app)
        ids = sorted(set(re.findall(r'\bid="([^"]+)"', page)))
        nav = page.split('id="settings-nav"', 1)[1].split("</nav>", 1)[0] if 'id="settings-nav"' in page else ""
        tabs = re.findall(r'data-pane="([a-z]+)"', nav)
        run = subprocess.run([node, str(script), json.dumps([app, ids, tabs])], capture_output=True, text=True,
                             encoding="utf-8", timeout=60)
        if run.returncode != 0:
            check(f"275: {app}'s Settings runs in node", False, run.stderr.strip()[:400])
            continue
        o = json.loads(run.stdout)
        panes = o["panes"]
        check(f"275: {app}'s page holds a pane for each of its categories and none of another app's",
              all(f"pane-{p}" in ids for p in panes)
              and not [i for i in ids if i.startswith("pane-") and i[5:] not in panes], str(panes))
        check(f"275: on {app}'s page served alone, Settings opens from Home's button on General, that pane alone shown",
              o["home"] == [True, ["general"]], str(o["home"]))
        check(f"275: on {app}'s page a click on each category shows that category alone",
              o["clicks"] == [[p] for p in panes], str(o["clicks"]))
        check(f"275: on {app}'s page ArrowDown from General walks every category and comes round to General",
              o["arrows"] == panes[1:] + ["general"], str(o["arrows"]))
        check(f"275: on {app}'s page another app's category opens General", o["other"] == ["general"], str(o["other"]))
        check(f"275: on {app}'s page Escape closes Settings, and with nothing open a key finds no card open",
              o["escape"] == [True, True, False], str(o["escape"]))
