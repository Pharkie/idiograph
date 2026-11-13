"""Area 374: a click outside a card closes it, the same everywhere (clickout, Adam, 12 November 2026: "make sure that's
consistent across the app"). What matters is what the pointer does: a press and its release both on the backdrop round
the card in front do what Esc does on that card, and a card with Done at its foot, applying as you go, closes as Done
does. The card stays open when words have been typed in it and not saved, when it is busy with its work, and when a
press starts inside it and ends outside, or the other way round. Each runs in the computer's own browser, headless, on
the shell's own functions taken from shell.js, its Esc taken from its own lines, and the cards' own markup from the
three apps' pages: the shortcuts card, Sift's Set columns, Remove's confirmation, Rename, New project's card and
About. Every word typed is invented, a heron."""
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


def statement(src: str, head: str) -> str:
    at = src.index(head)
    return src[at:src.index(";\n", at) + 2]


def line_of(src: str, start: str) -> str:
    return next(ln for ln in src.splitlines() if ln.strip().startswith(start)).strip()


def card_markup(page: str, ids: list[str]) -> str:
    from lxml import html as lxml_html
    doc = lxml_html.fromstring(page)
    return "\n".join(lxml_html.tostring(doc.get_element_by_id(i), encoding="unicode") for i in ids)


RUN = r"""
const out = {};
const tick = () => new Promise((r) => setTimeout(r, 0));
const opts = (x, y, buttons) => ({ bubbles: true, cancelable: true, composed: true, clientX: x, clientY: y, button: 0,
  buttons, isPrimary: true, pointerId: 1, pointerType: 'mouse' });
// a press and its release as the browser sends them: down and up each on the element under it, and the click on the
// nearest element holding both
const press = (down, [dx, dy], up = down, [ux, uy] = [dx, dy]) => {
  down.dispatchEvent(new PointerEvent('pointerdown', opts(dx, dy, 1)));
  const kept = down.dispatchEvent(new MouseEvent('mousedown', opts(dx, dy, 1)));
  up.dispatchEvent(new PointerEvent('pointerup', opts(ux, uy, 0)));
  up.dispatchEvent(new MouseEvent('mouseup', opts(ux, uy, 0)));
  let both = down;
  while (!both.contains(up)) both = both.parentElement;
  both.dispatchEvent(new MouseEvent('click', opts(ux, uy, 0)));
  return { caretKept: !kept };
};
const key = (el, k) => el.dispatchEvent(new KeyboardEvent('keydown', { key: k, bubbles: true, cancelable: true }));
const typed = (box, words) => { box.focus(); box.value = words; box.dispatchEvent(new Event('input', { bubbles: true })); };
// the backdrop beside the card, and a point on the card's own heading
const beside = (id) => { const r = $(id).querySelector('.card').getBoundingClientRect(); return [Math.max(4, r.left / 2), r.top + 20]; };
const onCard = (id) => { const el = $(id).querySelector('.card h2') || $(id).querySelector('.card'); const r = el.getBoundingClientRect(); return [el, [r.left + 8, r.top + r.height / 2]]; };
const outside = (id) => press($(id), beside(id));
(async () => {
  cardsWatch();
  cardsOutsideWatch();
  // ── the shortcuts card, opened by a button: a click outside closes it, the focus back on the button
  $('open-help').focus();
  show('help');
  await tick();
  outside('help');
  await tick();
  out.helpClosed = $('help').hidden;
  out.helpBack = document.activeElement.id;
  // ── a press inside it let go outside, and one outside let go inside, leave it open
  show('help');
  await tick();
  const [head, onHead] = onCard('help');
  press(head, onHead, $('help'), beside('help'));
  await tick();
  out.dragOut = !$('help').hidden;
  press($('help'), beside('help'), head, onHead);
  await tick();
  out.dragIn = !$('help').hidden;
  outside('help');
  await tick();
  out.helpAfter = $('help').hidden;
  // ── Set columns, Sift's, applies as you go: Done closes it by its X, and a name typed in it holds nothing
  $('sf-cols').hidden = false;
  await tick();
  $('sf-cols-done').click();
  await tick();
  out.colsDone = $('sf-cols').hidden;
  $('sf-cols').hidden = false;
  await tick();
  typed($('sf-col-name'), 'Heron');
  outside('sf-cols');
  await tick();
  out.colsTypedOut = $('sf-cols').hidden;
  // ── Remove's confirmation: a click outside removes nothing, as Esc, and Remove is never pressed
  show('remove-card');
  await tick();
  outside('remove-card');
  await tick();
  out.removeClosed = $('remove-card').hidden;
  out.removeAnswer = RM_SAID;
  // ── Rename with words typed: the click leaves it open, the caret and the words where they were, and Esc closes it
  show('rename');
  await tick();
  typed($('rn-name'), 'Heron');
  const held = outside('rename');
  await tick();
  out.renameHeld = !$('rename').hidden;
  out.renameCaret = held.caretKept && document.activeElement === $('rn-name');
  out.renameWords = $('rn-name').value;
  key($('rn-name'), 'Escape');
  await tick();
  out.renameEsc = $('rename').hidden;
  // opened again, nothing typed yet, the click closes it
  show('rename');
  await tick();
  outside('rename');
  await tick();
  out.renameAgain = $('rename').hidden;
  // ── New project's card while it makes the project stays, and once done closes
  BUSY = true;
  show('newproject');
  await tick();
  outside('newproject');
  await tick();
  out.busyHeld = !$('newproject').hidden;
  BUSY = false;
  outside('newproject');
  await tick();
  out.busyDone = $('newproject').hidden;
  // ── About over the shortcuts card: a click outside About closes it alone
  show('help');
  show('about');
  await tick();
  outside('about');
  await tick();
  out.aboutAlone = $('about').hidden && !$('help').hidden;
  document.getElementById('out').textContent = JSON.stringify(out);
})().catch((err) => { document.getElementById('out').textContent = JSON.stringify({ error: String(err && err.stack || err) }); });
"""

CSS = """
.overlay { position: fixed; inset: 0; display: grid; place-items: center; padding: 24px; }
.card { width: min(560px, 100%); max-height: 100%; overflow: auto; background: #fff; padding: 34px; position: relative; }
[hidden] { display: none !important; }
"""


def test_click_outside(scratch: Path):
    print("\n374. A click outside a card (clickout, 12 November 2026): what Esc does, Done's way on a card that applies as "
          "you go, and open with words typed, while busy, and for a press begun or ended inside it")
    exe = support.browser()
    if exe is None:
        skip("374: a click outside a card in a real browser", "no Chrome, Chromium, Brave or Edge on this computer")
        return
    try:
        import lxml  # noqa: F401  the cards' markup is read with it, as area 340 reads the package
    except ImportError:
        skip("374: a click outside a card in a real browser", "lxml is not installed")
        return
    shell = support.text("family/static/shell.js")
    markup = card_markup(support.every_page(), ["help", "sf-cols", "remove-card", "rename", "newproject", "about"])
    # the shell's Esc, from its own lines: Remove's card first, then the cards of its list, then an X no Esc takes
    remove = shell[shell.index("if (!$('remove-card').hidden) {"):]
    remove = remove[:remove.index("\n    }\n") + 6]
    esc = ("document.addEventListener('keydown', (e) => {\n" + remove + "\n  if (e.key === 'Escape') {\n"
           + line_of(shell, "if (anyOverlayOpen()) { overlaysHere().forEach(hide); return; }") + "\n"
           + line_of(shell, "if (cardEscX()) return;") + "\n  }\n});")
    parts = [
        "const $ = (id) => document.getElementById(id);",
        "const t = (k) => ({ 'page.done': 'Done' }[k] || k);",
        "let BUSY = false;",
        "let RM_SAID = 'not asked';",
        # an app's answer that a card is busy, as Idiograph's names New project's card while it makes the project
        "const FAMILY_APPS = { test: { cardBusy: (o) => o.id === 'newproject' && BUSY } };",
        "const RVC = { busy: false };",
        "const FEEDBACK = { busy: false };",
        whole(shell, "function appsSay("),
        line_of(shell, "const show = "),
        block(shell, "const hide = "),
        line_of(shell, "const CARDS = "), line_of(shell, "const CARD_SELECTOR = "), line_of(shell, "const CARD_STOPS = "),
        line_of(shell, "const CARD_FIELDS = "), line_of(shell, "const cardBox = "), line_of(shell, "const cardShown = "),
        line_of(shell, "const cardTop = "),
        whole(shell, "function cardLabel("), whole(shell, "function cardStops("), whole(shell, "function cardFocusIn("),
        whole(shell, "function cardOpen("), whole(shell, "function cardClose("), whole(shell, "function cardTab("),
        whole(shell, "function cardsWatch("),
        line_of(shell, "const OUTSIDE = "), statement(shell, "const CARD_WORDS = "),
        whole(shell, "function cardBackdrop("), whole(shell, "function cardHeld("), whole(shell, "function cardOutside("),
        whole(shell, "function cardDone("), whole(shell, "function cardEscX("), line_of(shell, "const CARDS_ALONE = "),
        whole(shell, "function cardAloneKeys("), whole(shell, "function cardsOutsideWatch("),
        line_of(shell, "const OVERLAYS = "), line_of(shell, "const overlaysHere = "), line_of(shell, "const anyOverlayOpen = "),
        # Remove's answer as the shell's own takes it, the card shut and what was answered kept
        "function rmAnswer(go) { RM_SAID = go; hide('remove-card'); }",
        "$('rm-go').onclick = () => rmAnswer(true);",
        # Set columns' X as Sift wires it
        "$('sf-cols-close').onclick = () => { $('sf-cols').hidden = true; };",
        esc,
    ]
    doc = ('<!doctype html><html><head><meta charset="utf-8"><style>' + CSS + '</style></head><body>'
           '<button type="button" id="open-help">Shortcuts</button>' + markup + '<pre id="out">none</pre><script>'
           + "\n".join(parts) + RUN + "</script></body></html>")
    with tempfile.TemporaryDirectory(prefix="idiograph-374-") as tmp:
        page_file = Path(tmp) / "outside.html"
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
    check("374: a click outside the shortcuts card closes it, as Esc does, and the focus goes back to the button that "
          "opened it", o.get("helpClosed") is True and o.get("helpBack") == "open-help", str(o)[:600])
    check("374: a press on the card let go on the backdrop, and a press on the backdrop let go on the card, both leave it "
          "open, and a click outside then closes it",
          o.get("dragOut") is True and o.get("dragIn") is True and o.get("helpAfter") is True, str(o)[:600])
    check("374: Set columns, which applies as you go, closes by its Done, now in the shell for Sift too, and a click "
          "outside closes it with a name typed in it, as Done does",
          o.get("colsDone") is True and o.get("colsTypedOut") is True, str(o)[:600])
    check("374: a click outside Remove's confirmation closes it as its Esc does, removing nothing",
          o.get("removeClosed") is True and o.get("removeAnswer") is False, str(o)[:600])
    check("374: with words typed in Rename a click outside leaves it open, the caret and the words in the box, Esc still "
          "closes it, and opened again with nothing typed a click outside closes it",
          o.get("renameHeld") is True and o.get("renameCaret") is True and o.get("renameWords") == "Heron"
          and o.get("renameEsc") is True and o.get("renameAgain") is True, str(o)[:600])
    check("374: a card its app says is busy, New project's card while it makes the project, stays open on a click "
          "outside, and closes once it is done", o.get("busyHeld") is True and o.get("busyDone") is True, str(o)[:600])
    check("374: a click outside About closes it alone, the card under it staying", o.get("aboutAlone") is True, str(o)[:600])
