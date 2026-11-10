"""Area 360: what the Linux desktop showed (linuxfix, 9 November 2026, from the linuxvm test on Ubuntu 24.04 in a
VM). On any machine: the menu words that name their keys after a tab given to the menu as keys on Linux, a project's
menu saying Show in Files on Linux, the line at the foot shown empty and given its words a frame later so a screen
reader hears them as a change, Print on Linux asking the window with the page's own orientation and paper, Idiograph's
own .deb carrying a desktop entry with %F and the .idiograph type's icon in the hicolor theme (Sift, Trace and a test
app neither), and the Linux files named for the machine's architecture. What only a Linux desktop proves (GTK drawing
the keys, Orca speaking, the print dialog's page, the file manager's icon, a file opened with the app, the window's
size across a scale change, a Tab with Orca on that no longer ends WebKitGTK's page) is the VM's. Since orcacrash, the
guard on Linux alone after the statements' group and at the end of Columns. The window's own parts (the cut at the tab, the dialog's title, the paper's
GTK name, the size kept in logical pixels) are its cargo tests. Every fixture is made up, a project on keeping bees."""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from . import support
from .support import check, skip


def whole(src: str, head: str) -> str:
    at = src.index(head)
    return src[at:src.index("\n}\n", at) + 3]


def line_of(src: str, start: str) -> str:
    return next(ln for ln in src.splitlines() if ln.startswith(start))


def png_size(path: Path) -> tuple[int, int]:
    head = path.read_bytes()[:24]
    return struct.unpack(">II", head[16:24]) if head[:8] == b"\x89PNG\r\n\x1a\n" else (0, 0)


TOAST_RUN = r"""
const queue = [];
const frames = [];
let clock = 0;
function setTimeout(fn, ms) { queue.push({ fn, at: clock + ms, id: queue.length + 1 }); return queue.length; }
function clearTimeout(id) { const job = queue.find((j) => j.id === id); if (job) job.fn = null; }
function requestAnimationFrame(fn) { frames.push(fn); }
function frame() { const now = frames.splice(0); now.forEach((fn) => fn()); }
function pass(ms) { clock += ms; for (const job of queue) if (job.fn && job.at <= clock) { const fn = job.fn; job.fn = null; fn(); } }
const el = { hidden: true, textContent: '', style: {}, getBoundingClientRect: () => ({ left: 0, right: 0, top: 0, bottom: 0 }) };
// the status the line stands in, between a card and a script in the page, and how often it was taken out and put back
let moves = 0;
const home = { kids: [] };
const live = { get parentNode() { return home.kids.includes(live) ? home : null; },
  get nextSibling() { return home.kids[home.kids.indexOf(live) + 1] || null; },
  remove() { home.kids.splice(home.kids.indexOf(live), 1); } };
home.kids.push({ card: true }, live, { script: true });
home.insertBefore = (node, next) => { moves += 1; home.kids.splice(next ? home.kids.indexOf(next) : home.kids.length, 0, node); };
el.parentElement = live;
const document = { querySelectorAll: () => [] };
const window = { innerHeight: 800 };
const $ = (id) => (id === 'toast' ? el : null);
__PIECES__
const out = {};
// a line put away: shown empty, its words a frame later
say('The frames are back in the hive.');
out.first = { hidden: el.hidden, text: el.textContent };
frame();
out.afterFrame = el.textContent;
// a line that stands takes new words at once
say('The queen is marked.');
out.standing = el.textContent;
// put away and said again, then taken back before its frame: its words never come
pass(5000);
out.gone = el.hidden;
say('Smoking the hive.');
unsay('Smoking the hive.');
frame();
pass(200);
out.unsaid = { hidden: el.hidden, text: el.textContent };
// two lines before a frame: the second is what it says
pass(5000);
say('Brood frames counted.');
say('Honey frames counted.');
frame();
pass(200);
out.second = el.textContent;
// no frames drawn, a window out of sight: the words still come after a tenth of a second
pass(5000);
say('Supers on.');
pass(150);
out.noFrame = el.textContent;
out.moves = moves;
process.stdout.write(JSON.stringify(out) + '\n');
"""

# the line at the foot on Linux (linuxfix3): the same made-up clock and frames, and the status the line stands in
TOAST_LINUX_RUN = TOAST_RUN.split("const out = {};")[0] + r"""
const out = {};
say('The frames are back in the hive.');
out.first = { hidden: el.hidden, text: el.textContent, moves, sameplace: home.kids.indexOf(live) === 1 };
frame();
out.afterFrame = { hidden: el.hidden, text: el.textContent };
pass(150);
out.shown = { hidden: el.hidden, text: el.textContent };
say('The queen is marked.');
out.standing = { hidden: el.hidden, moves };
pass(150);
out.standingShown = el.hidden ? '' : el.textContent;
pass(5000);
say('Smoking the hive.');
unsay('Smoking the hive.');
pass(200);
out.unsaid = { hidden: el.hidden, text: el.textContent };
pass(5000);
say('Brood frames counted.');
say('Honey frames counted.');
pass(200);
out.second = el.hidden ? '' : el.textContent;
pass(5000);
out.gone = el.hidden;
process.stdout.write(JSON.stringify(out) + '\n');
"""

PRINT_RUN = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
function load(os) {
  const t = { invoked: [], printed: 0 };
  const style = { textContent: '@page { size: A4 landscape; margin: 12mm; }' };
  const win = {
    __IDIOGRAPH_OS__: os,
    location: { href: 'http://127.0.0.1:8800/themes/print?board=b1' },
    document: { title: 'Hive 3 - Board 1 - PETs', querySelectorAll: () => [style], addEventListener: () => {} },
    addEventListener: () => {},
    print: () => { t.printed += 1; },
    open: () => ({ location: { href: 'about:blank' }, document: { title: '', querySelectorAll: () => [] }, print: () => { t.printed += 1; } }),
    btoa: (s) => Buffer.from(s, 'latin1').toString('base64'),
    __TAURI_INTERNALS__: { invoke: (cmd, args) => { t.invoked.push([cmd, args]); return Promise.resolve(null); } },
  };
  t.basePrint = win.print;
  new Function('window', src)(win);
  t.win = win;
  return t;
}
const out = {};
const linux = load('other');
linux.win.print();
const canvas = linux.win.open('about:blank', '_blank');
canvas.document.title = 'Hive 3 - Board 1 - PETs canvas';
canvas.print();
out.linux = { invoked: linux.invoked.filter((x) => x[0] === 'print'), native: linux.printed };
const windows = load('windows');
out.windows = windows.win.print === windows.basePrint;
process.stdout.write(JSON.stringify(out) + '\n');
"""

# the line at the foot in Linux's window (linuxfix4): the window says it to Orca, and the line shows as elsewhere
TOAST_VOICE_RUN = TOAST_RUN.split("const out = {};")[0] + r"""
const out = {};
const said = [];
window.idiographSay = (words) => { said.push(words); };
say('The frames are back in the hive.');
frame();
out.first = { said: said.slice(), hidden: el.hidden, text: el.textContent, moves };
pass(1000);
say('The queen is marked.');
out.second = { said: said.slice(), hidden: el.hidden, text: el.textContent, moves };
pass(5000);
out.gone = el.hidden;
process.stdout.write(JSON.stringify(out) + '\n');
"""

# Ctrl+Z, Ctrl+Y and Shift+Ctrl+Z in a text field in Linux's window (linuxfix4): what the window is asked, by system
KEYS_RUN = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
function load(os) {
  const t = { asked: [], keys: [] };
  const win = {
    __IDIOGRAPH_OS__: os, location: { href: 'http://127.0.0.1:8800/' }, document: { title: '', querySelectorAll: () => [] },
    addEventListener: (type, fn) => { if (type === 'keydown') t.keys.push(fn); },
    print: () => {}, open: () => ({}), btoa: (s) => Buffer.from(s, 'latin1').toString('base64'),
    __TAURI_INTERNALS__: { invoke: (cmd, args) => { t.asked.push([cmd, args]); return Promise.resolve(null); } },
  };
  new Function('window', src)(win);
  t.win = win;
  return t;
}
const field = { tagName: 'TEXTAREA' };
const entry = { tagName: 'INPUT', type: 'text' };
const box = { tagName: 'INPUT', type: 'checkbox' };
const board = { tagName: 'DIV', isContentEditable: false };
const written = { tagName: 'DIV', isContentEditable: true };
const shut = { tagName: 'INPUT', type: 'text', readOnly: true };
function press(t, target, key, mods, pageTakes) {
  const e = Object.assign({ key, code: 'Key' + key.toUpperCase(), ctrlKey: false, shiftKey: false, altKey: false, metaKey: false,
    target, defaultPrevented: false, preventDefault() { this.defaultPrevented = true; }, stopPropagation() {} }, mods);
  t.keys.forEach((fn) => fn(e));
  if (pageTakes) e.preventDefault();
}
const out = {};
const linux = load('other');
press(linux, field, 'z', { ctrlKey: true });
press(linux, entry, 'y', { ctrlKey: true });
press(linux, written, 'Z', { ctrlKey: true, shiftKey: true });
press(linux, board, 'z', { ctrlKey: true });
press(linux, box, 'z', { ctrlKey: true });
press(linux, shut, 'z', { ctrlKey: true });
press(linux, field, 'z', {});
press(linux, field, 'z', { ctrlKey: true, altKey: true });
press(linux, field, 'y', { ctrlKey: true, shiftKey: true });
press(linux, field, 'z', { ctrlKey: true }, true);
// a layout with no Latin letters: the key's place
press(linux, field, 'я', { ctrlKey: true, code: 'KeyZ' });
out.voice = typeof linux.win.idiographSay === 'function';
linux.win.idiographSay('Saved.');
const others = ['macos', 'windows'].map((os) => {
  const t = load(os);
  press(t, field, 'z', { ctrlKey: true, metaKey: os === 'macos' });
  return { os, voice: typeof t.win.idiographSay, t };
});
setTimeout(() => {
  out.linux = linux.asked.filter((x) => x[0] === 'edit' || x[0] === 'announce');
  out.others = others.map((o) => ({ os: o.os, voice: o.voice, asked: o.t.asked.filter((x) => x[0] === 'edit' || x[0] === 'announce') }));
  process.stdout.write(JSON.stringify(out) + '\n');
}, 30);
"""


def test_linux_desktop_fixes(scratch: Path):
    print("\n360. What the Linux desktop showed (linuxfix): menu keys, Show in Files, the line at the foot said, Print's "
          "page, the desktop entry's %F, the file type's icon and the files' architecture")
    sys.path.insert(0, str(support.source("packaging")))
    spec = importlib.util.spec_from_file_location("idiograph_360_build_linux", support.source("packaging") / "build_linux.py")
    build_linux = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build_linux)
    spec = importlib.util.spec_from_file_location("idiograph_360_release", support.source("packaging") / "release.py")
    release = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(release)
    window = build_linux.window
    src = support.source("packaging/tauri/src-tauri")
    root = scratch / "linux_desktop"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)

    # ── 1. every menu word that names its keys after a tab is Windows's alone: on Linux it goes through `keyed`
    menus = json.loads(support.text("family/static/i18n/en/menus.json"))
    tabbed = sorted(k.split(".", 1)[1] for k, v in menus.items() if isinstance(v, str) and "\t" in v)
    menu_rs = (src / "src" / "menu.rs").read_text(encoding="utf-8")
    keyed = set(re.findall(r'keyed\(app, "[a-z-]+", &t\("menus\.([a-z_]+)"\), "[^"]+"\)', menu_rs))
    plain = set(re.findall(r'item\(app, "[a-z-]+", &t\("menus\.([a-z_]+)"\)', menu_rs))
    check("360: each menu word naming its keys after a tab is given its keys through `keyed`, which on Linux cuts the "
          "words at the tab and makes the keys the item's own, and none goes through a plain item",
          tabbed and set(tabbed) <= keyed and not set(tabbed) & plain, f"{tabbed} keyed {sorted(keyed)}")

    node = shutil.which("node")
    if not node:
        skip("360: the page's and the window's scripts in node", "node is not installed")
    else:
        shell = support.text("family/static/shell.js")
        # ── 2. Show in Files on Linux
        words = support.i18n_js() + "const APP_NAME = 'Idiograph';\n" + whole(shell, "function projectMenuWord(") + r"""
const out = { mac: projectMenuWord('show', true, false), windows: projectMenuWord('show', false, false),
  linux: projectMenuWord('show', false, true), unset: projectMenuWord('show', false) };
var LINUX = true;
out.global = projectMenuWord('show', false);
process.stdout.write(JSON.stringify(out) + '\n');
"""
        ran = support.run_node(words, scratch, "a360-words.js")
        got = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {}
        check("360: a project's menu says Show in Finder on a Mac, Show in Explorer on Windows and Show in Files on Linux, "
              "Explorer where nothing says the system is Linux",
              got == {"mac": "Show in Finder", "windows": "Show in Explorer", "linux": "Show in Files", "unset": "Show in Explorer",
                      "global": "Show in Files"}, ran.stderr[-300:] or str(got))
        check("360: the page knows Linux by the platform WebKitGTK names, as it knows a Mac",
              "const LINUX = navigator.platform.toUpperCase().includes('LINUX');" in shell)

        # ── 3. the line at the foot
        pieces = "\n".join(["let toastTimer;", "let toastWords = '';", line_of(shell, "const TOAST_CLEAR = "),
                            whole(shell, "function toastClear("), whole(shell, "function say("), whole(shell, "function unsay("),
                            line_of(shell, "let toastDue = "), whole(shell, "function toastAnew("),
                            line_of(shell, "const TOAST_ANEW_MS = ")])
        ran = support.run_node(TOAST_RUN.replace("__PIECES__", "const LINUX = false;\n" + pieces), scratch, "a360-toast.js")
        o = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {}
        check("360: a line at the foot that was put away is shown empty and given its words a frame later, a change inside "
              "the status a screen reader says",
              o.get("first") == {"hidden": False, "text": ""} and o.get("afterFrame") == "The frames are back in the hive.",
              ran.stderr[-300:] or str(o))
        check("360: a line that stands takes new words at once, one taken back before its frame never says them, the "
              "second of two lines before a frame is what it says, and with no frames drawn the words come anyway",
              o.get("standing") == "The queen is marked." and o.get("gone") is True
              and o.get("unsaid") == {"hidden": True, "text": ""} and o.get("second") == "Honey frames counted."
              and o.get("noFrame") == "Supers on.", str(o))
        # on Linux (linuxfix3): every line a new line inside a status put back in its place, so WebKitGTK names both to Orca
        ran = support.run_node(TOAST_LINUX_RUN.replace("__PIECES__", "const LINUX = true;\n" + pieces), scratch,
                               "a360-toast-linux.js")
        lo = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {}
        check("360: on Linux a line is put away, its status taken out and put back in the same place, and the line shown "
              "with its words a little after, never on the frame alone",
              lo.get("first") == {"hidden": True, "text": "", "moves": 1, "sameplace": True}
              and lo.get("afterFrame") == {"hidden": True, "text": ""}
              and lo.get("shown") == {"hidden": False, "text": "The frames are back in the hive."},
              ran.stderr[-300:] or str(lo))
        check("360: on Linux a line that stands comes again as a new line with its new words, one taken back before it "
              "shows never shows, the second of two lines said together is what shows, and the line still goes after its time",
              lo.get("standing") == {"hidden": True, "moves": 2} and lo.get("standingShown") == "The queen is marked."
              and lo.get("unsaid") == {"hidden": True, "text": ""} and lo.get("second") == "Honey frames counted."
              and lo.get("gone") is True, str(lo))
        check("360: off Linux the line at the foot never takes its status out of the page",
              o.get("moves", 0) == 0, str(o))
        # in Linux's window (linuxfix4): the window says each line to Orca, and the line shows as it does elsewhere
        ran = support.run_node(TOAST_VOICE_RUN.replace("__PIECES__", "const LINUX = true;\n" + pieces), scratch,
                               "a360-toast-voice.js")
        vo = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {}
        check("360: in Linux's window each line at the foot, and a second while the first shows, is handed to the window "
              "to say, the line shown with its words and its status never taken out of the page",
              vo.get("first") == {"said": ["The frames are back in the hive."], "hidden": False,
                                   "text": "The frames are back in the hive.", "moves": 0}
              and vo.get("second") == {"said": ["The frames are back in the hive.", "The queen is marked."], "hidden": False,
                                       "text": "The queen is marked.", "moves": 0}
              and vo.get("gone") is True, ran.stderr[-300:] or str(vo))
        page = support.page_text()
        check("360: the line at the foot stands inside a polite status that is always on the page",
              '<div id="toast-live" role="status" aria-live="polite"><div id="toast" class="toast" hidden></div></div>' in page)

        # ── 3b. Orca on Linux (orcacrash): a zero-width space hidden from screen readers after the statements' group and
        # at the end of Columns, where a Tab with Orca on ended WebKitGTK 2.52's page, and nothing off Linux
        guard_run = r"""
const made = [];
const document = { createElement: (tag) => { const n = { tag, attrs: {}, className: '', textContent: '',
  setAttribute(k, v) { this.attrs[k] = v; } }; made.push(n); return n; } };
const el = (name) => ({ name, placed: [], after(n) { this.placed.push(['after', n.tag, n.className, n.attrs, n.textContent]); },
  append(n) { this.placed.push(['end', n.tag, n.className, n.attrs, n.textContent]); } });
const out = {};
for (const linux of [true, false]) {
  const LINUX = linux;
  __GUARD__
  const group = el('pairs'), button = el('cols-pick');
  axGuard(group); axGuard(button, true); axGuard(null);
  out[linux ? 'linux' : 'other'] = { group: group.placed, button: button.placed, made: made.length };
}
process.stdout.write(JSON.stringify(out) + '\n');
""".replace("__GUARD__", whole(shell, "function axGuard("))
        ran = support.run_node(guard_run, scratch, "a360-guard.js")
        go = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {}
        zw = ["span", "ax-guard", {"aria-hidden": "true"}, "​"]
        check("360: on Linux a guard is one zero-width space in a span hidden from screen readers, put after a group or at "
              "the end of a button, none for an element not there, and off Linux nothing is made",
              go.get("linux") == {"group": [["after", *zw]], "button": [["end", *zw]], "made": 2}
              and go.get("other") == {"group": [], "button": [], "made": 2}, ran.stderr[-300:] or str(go))
        boot = whole(support.text("apps/idiograph/static/distil.js"), "function distilBoot(")
        check("360: the statements screen guards the place after its statements' group and the end of Columns, the two "
              "places where a Tab with Orca on ended WebKitGTK's page",
              "axGuard($('pairs'));" in boot and "axGuard($('cols-pick'), true);" in boot)
        css = support.text("family/static/style.css")
        check("360: a guard takes no room on the page",
              re.search(r"\.ax-guard \{ position: absolute; width: 0; height: 0; overflow: hidden;", css) is not None)

        # ── 4. Print on Linux asks the window, with the page's orientation and paper
        harness = root / "print-360.js"
        harness.write_text(PRINT_RUN, encoding="utf-8")
        import subprocess
        run = subprocess.run([node, str(harness), str(support.source("packaging/tauri/window.js"))],
                             capture_output=True, text=True, encoding="utf-8")
        try:
            pr = json.loads(run.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            pr = {}
        lx = pr.get("linux") or {}
        check("360: on Linux the page's Print and the canvas's, written into about:blank, ask the window to print with "
              "the page's landscape A4, and WebKitGTK's own print is never called, while Windows keeps its own print",
              lx.get("native") == 0 and len(lx.get("invoked") or []) == 2
              and lx["invoked"][0][1].get("orientation") == "landscape" and lx["invoked"][0][1].get("paper") == "a4"
              and lx["invoked"][0][1].get("title") == "Hive 3 - Board 1 - PETs"
              and lx["invoked"][1][1].get("title") == "Hive 3 - Board 1 - PETs canvas" and pr.get("windows") is True,
              run.stderr[-300:] or str(pr))

        # ── 4b. Ctrl+Z, Ctrl+Y and Shift+Ctrl+Z in a text field on Linux (linuxfix4)
        harness = root / "keys-360.js"
        harness.write_text(KEYS_RUN, encoding="utf-8")
        run = subprocess.run([node, str(harness), str(support.source("packaging/tauri/window.js"))],
                             capture_output=True, text=True, encoding="utf-8")
        try:
            ks = json.loads(run.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            ks = {}
        edits = [x[1].get("action") for x in ks.get("linux") or [] if x[0] == "edit"]
        check("360: on Linux Ctrl+Z in a text field asks the window for WebKitGTK's Undo, Ctrl+Y and Shift+Ctrl+Z for its "
              "Redo, in a textarea, a text input and written words alike, and by the key's place where the layout has no "
              "Latin letters",
              edits == ["undo", "redo", "redo", "undo"], run.stderr[-300:] or str(ks))
        check("360: on Linux nothing is asked for a key the page took itself, on a board, in a checkbox or a read-only "
              "field, for Z alone, with Alt, or for Shift+Ctrl+Y",
              len(edits) == 4 and ks.get("linux") is not None, str(ks))
        check("360: Linux's window takes the line at the foot to say, and the Mac's and Windows's neither ask for an undo "
              "nor take the line",
              ks.get("voice") is True and ["announce", {"words": "Saved."}] in (ks.get("linux") or [])
              and len(ks.get("others") or []) == 2
              and all(o.get("voice") == "undefined" and o.get("asked") == [] for o in ks.get("others") or []), str(ks))

    # ── 5 and 6. Idiograph's own .deb: the desktop entry with %F, the type's icon in the hicolor theme
    idio = window.overrides("0.9.99", False, None, None, "idiograph", True)["bundle"]["linux"]["deb"]
    template = src / window.LINUX_DESKTOP_TEMPLATE
    body = template.read_text(encoding="utf-8") if template.is_file() else ""
    check("360: Idiograph's Linux build writes its desktop entry from its own template, whose Exec line ends in %F, "
          "with Tauri's MimeType line kept",
          idio.get("desktopTemplate") == window.LINUX_DESKTOP_TEMPLATE
          and re.search(r"^Exec=\{\{exec\}\} %F$", body, re.M) and "MimeType={{mime_type}}" in body
          and re.search(r"^Icon=\{\{icon\}\}$", body, re.M) and "Type=Application" in body, body[:300])
    sizes = {dest: png_size(src / source) for dest, source in idio["files"].items() if dest in window.LINUX_MIME_ICONS}
    check("360: the .deb puts the app's mark in the hicolor theme's mimetypes folders under the type's icon name, each "
          "picture the size its folder says",
          len(sizes) == 3 and all(f"/{w}x{h}/mimetypes/{window.LINUX_MIME_ICON}.png" in dest for dest, (w, h) in sizes.items()),
          str(sizes))
    ns = "{http://www.freedesktop.org/standards/shared-mime-info}"
    node_type = ET.parse(src / window.LINUX_MIME_FILE).getroot().find(f"{ns}mime-type")
    icon = node_type.find(f"{ns}icon") if node_type is not None else None
    check("360: the mime file gives the .idiograph type that icon name",
          icon is not None and icon.get("name") == window.LINUX_MIME_ICON)
    for label, over in (("Sift", window.overrides("0.9.99", False, None, None, "sift", True)),
                        ("Trace", window.overrides("0.9.99", False, None, None, "trace", True)),
                        ("Idiograph's test app", window.overrides("0.9.99", True, None, None, "idiograph", True))):
        deb = over.get("bundle", {}).get("linux", {}).get("deb", {})
        check(f"360: {label} takes no files on Linux: Tauri's own desktop entry and no file type icon",
              "desktopTemplate" not in deb and "files" not in deb, str(deb))

    names = build_linux.window_names("idiograph", False, "x86_64")
    sift = build_linux.window_names("sift", False, "x86_64")
    depends = "libc6 (>= 2.35), libgtk-3-0, libwebkit2gtk-4.1-0"

    def deb_tree(tag, n, exec_line, mime, icons):
        tree = root / tag
        (tree / "usr" / "bin").mkdir(parents=True)
        (tree / "usr" / "bin" / n["main"]).write_bytes(b"x")
        srv = tree / "usr" / "lib" / n["product"] / "server"
        (srv / "_internal").mkdir(parents=True)
        (srv / n["name"]).write_bytes(b"x")
        # the typesetter beside the server (typst1, 9 November 2026)
        (srv / "idiograph-typeset").write_bytes(b"x")
        (srv / "idiograph-typeset").chmod(0o755)
        apps = tree / "usr" / "share" / "applications"
        apps.mkdir(parents=True)
        entry = f"[Desktop Entry]\nName={n['product']}\n{exec_line}\nIcon={n['main']}\n"
        if mime:
            entry += f"MimeType={window.LINUX_MIME};\n"
            (tree / window.LINUX_MIME_DEST.lstrip("/")).parent.mkdir(parents=True)
            (tree / window.LINUX_MIME_DEST.lstrip("/")).write_text("<mime-info/>", encoding="utf-8")
        (apps / f"{n['main']}.desktop").write_text(entry, encoding="utf-8")
        pic = tree / "usr" / "share" / "icons" / "hicolor" / "128x128" / "apps"
        pic.mkdir(parents=True)
        (pic / f"{n['main']}.png").write_bytes(b"x")
        for dest in (window.LINUX_MIME_ICONS if icons else ()):
            (tree / dest.lstrip("/")).parent.mkdir(parents=True, exist_ok=True)
            (tree / dest.lstrip("/")).write_bytes(b"x")
        return tree

    right = build_linux.deb_problems(deb_tree("ok", names, "Exec=Idiograph %F", True, True), depends, names)
    no_f = build_linux.deb_problems(deb_tree("no-f", names, "Exec=Idiograph", True, True), depends, names)
    no_icon = build_linux.deb_problems(deb_tree("no-icon", names, "Exec=Idiograph %F", True, False), depends, names)
    check("360: check_deb takes Idiograph's .deb with %F and the type's icon, and refuses one without either",
          right == [] and len(no_f) == 1 and "%F" in no_f[0] and len(no_icon) == 1 and window.LINUX_MIME_ICON in no_icon[0],
          f"{right} {no_f} {no_icon}")
    sift_ok = build_linux.deb_problems(deb_tree("sift-ok", sift, "Exec=Sift", False, False), depends, sift)
    sift_f = build_linux.deb_problems(deb_tree("sift-f", sift, "Exec=Sift %F", False, False), depends, sift)
    check("360: Sift's .deb takes no files, and one whose entry would take them is refused",
          sift_ok == [] and len(sift_f) == 1 and "only Idiograph" in sift_f[0], f"{sift_ok} {sift_f}")

    # ── 9. the files named for the machine's architecture, release.py's x86_64 names unchanged
    arm = build_linux.window_names("idiograph", False, "aarch64")
    check("360: on an ARM machine the files are Idiograph-aarch64.AppImage and Idiograph-arm64.deb, on x86_64 as before, "
          "and release.py's names are x86_64's",
          arm["appimage"] == "Idiograph-aarch64.AppImage" and arm["deb"] == "Idiograph-arm64.deb"
          and build_linux.linux_arch("arm64") == ("aarch64", "arm64")
          and names["appimage"] == release.names("idiograph")["linux"] == "Idiograph-x86_64.AppImage"
          and names["deb"] == release.names("idiograph")["deb"] == "Idiograph-amd64.deb", f"{arm} {names}")
    if not sys.platform.startswith("linux"):
        check("360: off Linux a dry run names the release machine's x86_64 files",
              build_linux.window_names("idiograph", False)["appimage"] == "Idiograph-x86_64.AppImage")
