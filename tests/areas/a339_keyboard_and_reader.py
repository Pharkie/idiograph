"""Area 339: the standard fixes for the keyboard and a screen reader (a11yfix, Adam, 8 November 2026, on a11ycheck's
findings). What matters is what the keys do: Tab leaves a project's row's handle while Alt and an arrow still move the
row, a card takes the focus as it opens, keeps Tab and Shift + Tab inside it and gives the focus back to what opened it
when it closes, a menu walks by the arrows, Home and End and shuts on Esc back to its button, and the line at the foot
is said inside a status that is always there. Each runs in the computer's own browser, headless, on the app's own
functions taken from its scripts and the page's own markup. Words and looks go to Adam as review shots. Every fixture
is invented, a project on keeping bees."""
from __future__ import annotations

import html as html_mod
import json
import subprocess
import tempfile
from pathlib import Path

from . import support
from .support import check, skip


def whole(src: str, head: str) -> str:
    at = src.index(head)
    return src[at:src.index("\n}\n", at) + 3]


def block(src: str, head: str) -> str:
    at = src.index(head)
    return src[at:src.index("\n};", at) + 3]


def line_of(src: str, start: str) -> str:
    return next(ln for ln in src.splitlines() if ln.strip().startswith(start))


RUN = r"""
const out = {};
const tick = () => new Promise((r) => setTimeout(r, 0));
const key = (el, k, more = {}) => {
  const e = new KeyboardEvent('keydown', Object.assign({ key: k, bubbles: true, cancelable: true }, more));
  el.dispatchEvent(e);
  return e;
};
(async () => {
  cardsWatch();
  // ── the handle: Tab goes its way, and Alt and an arrow still move the row
  const list = $('rows');
  const li = list.querySelector('li');
  const grip = li.querySelector('button.pc-grip');
  const how = { rows: ':scope > li', live: 'said', said: (row, to, n) => `moved to ${to + 1} of ${n}`, moved: () => {} };
  ROW_KEYS(grip, li, list, how);
  grip.focus();
  out.gripTab = key(grip, 'Tab').defaultPrevented;
  out.gripMove = key(grip, 'ArrowDown', { altKey: true }).defaultPrevented;
  out.gripOrder = [...list.children].map((x) => x.dataset.case);
  out.gripFocus = document.activeElement === grip;
  // ── a card opened from the keyboard: a dialog named by its title, the focus in its first field, Tab kept inside
  const opener = $('open-card');
  opener.focus();
  key(opener, 'Enter');
  show('hive-card');
  await tick();
  const card = $('hive-card').querySelector('.card');
  out.role = card.getAttribute('role');
  out.modal = card.getAttribute('aria-modal');
  const named = card.getAttribute('aria-labelledby');
  out.name = named && $(named) ? $(named).textContent : null;
  out.openFocus = document.activeElement.id;
  const seen = [];
  for (let i = 0; i < 5; i += 1) { key(document.activeElement, 'Tab'); seen.push(document.activeElement.id); }
  out.tabs = seen;
  const back = [];
  for (let i = 0; i < 2; i += 1) { key(document.activeElement, 'Tab', { shiftKey: true }); back.push(document.activeElement.id); }
  out.shiftTab = back;
  // Esc, as the shell's keys put the cards away, and the focus back on what opened it
  key(document.activeElement, 'Escape');
  await tick();
  out.closed = $('hive-card').hidden;
  out.backTo = document.activeElement.id;
  // ── a card an app's script shows itself, opened by the pointer: the card itself takes the focus, no field
  const other = $('open-other');
  other.focus();
  window.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }));
  $('frame-card').hidden = false;
  await tick();
  await tick();
  out.pointerFocus = document.activeElement === $('frame-card').querySelector('.card');
  out.frameRole = $('frame-card').querySelector('.card').getAttribute('role');
  $('frame-card').hidden = true;
  await tick();
  await tick();
  out.frameBack = document.activeElement.id;
  // ── a menu: the arrows walk its items round, past a disabled one, Home and End, and Esc back to its button
  const menu = $('comb-menu');
  const button = $('comb-button');
  menu.hidden = false;
  menu.onkeydown = (e) => menuKeys(e, menu, () => { menu.hidden = true; button.focus(); });
  menuFirst(menu);
  const walk = [document.activeElement.id];
  for (const k of ['ArrowDown', 'ArrowDown', 'ArrowDown', 'ArrowUp', 'End', 'Home']) { key(document.activeElement, k); walk.push(document.activeElement.id); }
  out.walk = walk;
  key(document.activeElement, 'Escape');
  out.menuShut = menu.hidden;
  out.menuBack = document.activeElement.id;
  // ── the line at the foot: said inside a status that is there before and after
  const live = $('toast').closest('[role="status"]');
  out.liveBefore = !!live && !live.hidden && live.getAttribute('aria-live');
  say('The frames are back in the hive.');
  // the words come a frame after the line is shown, as a change inside the status (linuxfix, 9 November 2026)
  await new Promise((done) => setTimeout(done, 250));
  out.liveText = live ? live.textContent : '';
  out.liveShown = !$('toast').hidden;
  // ── on Linux (linuxfix3): the status taken out and put back in its own place, then the line inside it with its words
  LINUX = true;
  const above = live.previousElementSibling;
  const below = live.nextElementSibling;
  say('The smoker is lit.');
  out.linuxWaiting = $('toast').hidden;
  await new Promise((done) => setTimeout(done, 300));
  const again = $('toast').closest('[role="status"]');
  out.linux = { same: again === live, place: live.previousElementSibling === above && live.nextElementSibling === below,
    text: again ? again.textContent : '', shown: !$('toast').hidden };
  document.getElementById('out').textContent = JSON.stringify(out);
})().catch((err) => { document.getElementById('out').textContent = JSON.stringify({ error: String(err) }); });
"""

FIXTURE = """
<ul id="rows" class="prows">
  <li data-case="Wren"><button type="button" class="pc-grip">grip</button></li>
  <li data-case="Moss"><button type="button" class="pc-grip">grip</button></li>
</ul>
<p id="said"></p>
<button type="button" id="open-card">Hive settings</button>
<button type="button" id="open-other">Frames</button>
<button type="button" id="comb-button">Comb</button>
<div class="row-menu" id="comb-menu" hidden>
  <button type="button" id="m-one">Brood</button>
  <button type="button" id="m-two" disabled>Honey</button>
  <button type="button" id="m-three">Pollen</button>
  <button type="button" id="m-four">Wax</button>
</div>
<div class="overlay" id="hive-card" hidden>
  <div class="card">
    <p class="kicker">Apiary</p>
    <h2>Hive settings</h2>
    <input type="text" id="f-name" aria-label="Hive name">
    <label><input type="radio" name="side" id="f-east" checked> East</label>
    <label><input type="radio" name="side" id="f-west"> West</label>
    <button type="button" id="f-cancel">Cancel</button>
    <button type="button" class="primary" id="f-done">Done</button>
  </div>
</div>
<div class="overlay" id="frame-card" hidden>
  <div class="card"><h2>Frames</h2><button type="button" class="primary" id="g-done">Done</button></div>
</div>
"""


def test_keyboard_and_reader(scratch: Path):
    print("\n339. The keyboard and a screen reader (a11yfix, 8 November 2026): Tab leaving a row's handle, a card's focus, "
          "Tab and way back, a menu's arrows and the line at the foot said in a status")
    exe = support.browser()
    if exe is None:
        skip("339: the keys in a real browser", "no Chrome, Chromium, Brave or Edge on this computer")
        return
    shell = support.text("family/static/shell.js")
    distil = support.text("apps/idiograph/static/distil.js")
    page = support.page_text()
    # the row's handle wired as a project's page wires it, its own line from drawCards
    grip_line = line_of(distil, "grip.onkeydown = ")
    toast = page[page.index('<div id="toast-live"'):]
    toast = toast[:toast.index("</div></div>") + 12] if "</div></div>" in toast else ""
    parts = [
        "const $ = (id) => document.getElementById(id);",
        "const MAC = true;",
        "let LINUX = false;",
        "const MOD = (e) => (MAC ? e.metaKey : e.ctrlKey);",
        "const t = (k) => ({ 'page.done': 'Done' }[k] || k);",
        "const FAMILY_APPS = {};",
        "let toastTimer = null;",
        "let toastWords = '';",
        line_of(shell, "const TOAST_CLEAR = "),
        whole(shell, "function toastClear("),
        whole(shell, "function say("),
        line_of(shell, "let toastDue = "), whole(shell, "function toastAnew("), line_of(shell, "const TOAST_ANEW_MS = "),
        whole(shell, "function gripKeys("),
        "function ROW_KEYS(grip, li, list, how) {\n  " + grip_line.strip() + "\n}",
        line_of(shell, "const show = "),
        block(shell, "const hide = "),
        line_of(shell, "const CARDS = "), line_of(shell, "const CARD_SELECTOR = "), line_of(shell, "const CARD_STOPS = "),
        line_of(shell, "const CARD_FIELDS = "), line_of(shell, "const cardBox = "), line_of(shell, "const cardShown = "),
        line_of(shell, "const cardTop = "),
        # the words typed in each card, which a card opened afresh clears (clickout, area 374)
        line_of(shell, "const OUTSIDE = "),
        whole(shell, "function cardLabel("), whole(shell, "function cardStops("), whole(shell, "function cardFocusIn("),
        whole(shell, "function cardOpen("), whole(shell, "function cardClose("), whole(shell, "function cardTab("),
        whole(shell, "function cardsWatch("),
        whole(shell, "function menuItems("), whole(shell, "function menuKeys("), whole(shell, "function menuFirst("),
        # Esc puts the cards away, as the shell's keys do with every card open
        "document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !$('hive-card').hidden) { e.preventDefault(); hide('hive-card'); } });",
    ]
    doc = ('<!doctype html><html><head><meta charset="utf-8"><style>.card{display:block}[hidden]{display:none !important}'
           '</style></head><body>' + FIXTURE + toast + '<pre id="out">none</pre><script>' + "\n".join(parts) + RUN
           + "</script></body></html>")
    with tempfile.TemporaryDirectory(prefix="idiograph-339-") as tmp:
        page_file = Path(tmp) / "keys.html"
        page_file.write_text(doc, encoding="utf-8")
        cmd = [str(exe), "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
               "--disable-background-networking", "--disable-component-update", "--disable-sync", "--disable-default-apps",
               "--password-store=basic", "--use-mock-keychain", f"--user-data-dir={Path(tmp) / 'profile'}",
               "--window-size=1280,800", "--virtual-time-budget=3000", "--dump-dom", page_file.as_uri()]
        try:
            dumped = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=120).stdout
        except (OSError, subprocess.TimeoutExpired) as err:
            dumped = str(err)
    said = dumped.split('<pre id="out">', 1)[1].split("</pre>", 1)[0] if '<pre id="out">' in dumped else "{}"
    o = json.loads(html_mod.unescape(said)) if said.startswith("{") else {"said": said[:300]}
    check("339: Tab on a project's row's handle goes its way, no longer cancelled, and Alt and Down still move the row "
          "one place with the handle keeping the focus",
          o.get("gripTab") is False and o.get("gripMove") is True and o.get("gripOrder") == ["Moss", "Wren"]
          and o.get("gripFocus") is True, str(o)[:600])
    check("339: a card opened from the keyboard is a modal dialog named by its title, and its first field takes the focus",
          o.get("role") == "dialog" and o.get("modal") == "true" and o.get("name") == "Hive settings"
          and o.get("openFocus") == "f-name", str(o)[:600])
    check("339: Tab goes round the card and never out of it, a group of radios one stop, and Shift + Tab goes back, from "
          "its first stop to its last",
          o.get("tabs") == ["f-east", "f-cancel", "f-done", "f-name", "f-east"] and o.get("shiftTab") == ["f-name", "f-done"],
          str(o)[:600])
    check("339: Esc puts the card away and gives the focus back to the button that opened it",
          o.get("closed") is True and o.get("backTo") == "open-card", str(o)[:600])
    check("339: a card an app's script shows itself after a press of the pointer is a dialog too and takes the focus on "
          "itself, no field, and closed it gives the focus back",
          o.get("pointerFocus") is True and o.get("frameRole") == "dialog" and o.get("frameBack") == "open-other", str(o)[:600])
    check("339: a menu opened from the keyboard has its first item in focus, Down and Up walk its items round at the "
          "ends past a disabled one, End and Home go to the last and the first, and Esc shuts it back to its button",
          o.get("walk") == ["m-one", "m-three", "m-four", "m-one", "m-four", "m-four", "m-one"]
          and o.get("menuShut") is True and o.get("menuBack") == "comb-button", str(o)[:600])
    check("339: the line at the foot is said inside a status, polite, that is on the page before anything is said",
          o.get("liveBefore") == "polite" and o.get("liveText") == "The frames are back in the hive."
          and o.get("liveShown") is True, str(o)[:600])
    check("339: on Linux the status is taken out and put back in its own place in a real page, the line waiting, then shown "
          "inside it with its words, a part added inside the status that WebKitGTK names to Orca (linuxfix3)",
          o.get("linuxWaiting") is True
          and o.get("linux") == {"same": True, "place": True, "text": "The smoker is lit.", "shown": True}, str(o)[-600:])
