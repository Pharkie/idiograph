from __future__ import annotations

import http.client
import json
import re
import shutil
import subprocess
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

from . import support
from .support import STUDY_PSEUDONYMS, check, skip


def test_tauri_window(scratch):
    print("\n164. Idiograph in a window of its own (Tauri, 17 October, build 1 of about five): the window does what the "
          "browser tab did, print, the print views, a download through the system's save panel, a link out to the "
          "browser and the page's own drop, and what the launchers did, one at a time, Restart and Quit and the MCP "
          "server, while the page a browser is served stays as it was")
    import mcp_server
    import server as server_mod

    tauri = support.source("packaging/tauri")
    src = tauri / "src-tauri"
    read = lambda path: Path(path).read_text(encoding="utf-8")
    main_rs, build_rs, cargo = read(src / "src" / "main.rs"), read(src / "build.rs"), read(src / "Cargo.toml")
    conf, cap = json.loads(read(src / "tauri.conf.json")), json.loads(read(src / "capabilities" / "page.json"))
    window_js, common = read(tauri / "window.js"), read(tauri / "drive_common.py")
    page_js = "\n".join(read(p) for p in sorted(p for folder in support.static_folders() for p in folder.glob("*.js")))

    # ── A. the page a browser is served is the page it was: the window's script lives beside the window
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    try:
        def get(path):
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=20)
            conn.request("GET", path, headers={"Host": f"127.0.0.1:{port}"})
            res = conn.getresponse()
            body = res.read().decode("utf-8", errors="replace")
            conn.close()
            return res.status, body
        home_status, home = get("/")
        js_status, _ = get("/window.js")
    finally:
        httpd.shutdown()
        httpd.server_close()
    marks = ("__TAURI", "__IDIOGRAPH_OS__", "__idiographWindow", "window.js", "save_download")
    check("164: the page a browser is served names nothing of the window, no file of the window's is served, and "
          "nothing under static/ or in server.py reaches for the window's bridge",
          home_status == 200 and "<html" in home.lower() and not any(m in home for m in marks) and js_status == 404
          and not any((folder / "window.js").exists() for folder in support.static_folders())
          and not any(m in page_js for m in marks) and "__TAURI" not in read(support.source("server.py")),
          f"/ {home_status}, /window.js {js_status}")

    # ── B. window.js under node, with a window of its own made up for it
    node = shutil.which("node")
    if node:
        harness = scratch / "tauri-164.js"
        harness.write_text(r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
function load(os, bridge, fetchFails) {
  const t = { invoked: [], opened: [], fetched: [], on: {}, nativeClicks: 0, printed: 0 };
  function Anchor(attrs, connected) { this.attrs = attrs; this.isConnected = connected; this.href = attrs.href; }
  Anchor.prototype.getAttribute = function (n) { return n in this.attrs ? this.attrs[n] : null; };
  Anchor.prototype.hasAttribute = function (n) { return n in this.attrs; };
  Anchor.prototype.closest = function () { return this; };
  Anchor.prototype.click = function () { t.nativeClicks += 1; };
  const win = {
    __IDIOGRAPH_OS__: os,
    HTMLAnchorElement: Anchor,
    addEventListener: (n, f, capture) => { (t.on[n] = t.on[n] || []).push([f, capture]); },
    open: (url, target) => { t.opened.push([url, target]); return {}; },
    print: () => { t.printed += 1; },
    btoa: (s) => Buffer.from(s, 'latin1').toString('base64'),
    fetch: (url) => {
      t.fetched.push(url);
      if (fetchFails) return Promise.reject(new TypeError('Failed to fetch'));
      const bytes = url.indexOf('big') >= 0 ? Uint8Array.from({ length: 100000 }, (_, i) => (i * 7) % 256) : new Uint8Array([60, 115, 118, 103, 62]);
      return Promise.resolve({ ok: true, status: 200, arrayBuffer: () => Promise.resolve(bytes.buffer) });
    },
  };
  if (bridge) win.__TAURI_INTERNALS__ = { invoke: (cmd, args) => { t.invoked.push([cmd, args]); return Promise.resolve('ok'); } };
  t.basePrint = win.print;
  t.baseClick = Anchor.prototype.click;
  new Function('window', src)(win);
  t.win = win; t.Anchor = Anchor;
  return t;
}
function fire(t, name, e) {
  const ev = Object.assign({ prevented: false, stopped: false, preventDefault() { this.prevented = true; }, stopPropagation() { this.stopped = true; } }, e);
  for (const [f] of t.on[name] || []) f(ev);
  return ev;
}
const tick = () => new Promise((r) => setTimeout(r, 20));
(async () => {
  const out = {};
  const bare = load('macos', false);
  out.bare = { listeners: Object.keys(bare.on).length, print: bare.win.print === bare.basePrint, click: bare.Anchor.prototype.click === bare.baseClick };
  const mac = load('macos', true);
  mac.win.print();
  out.macPrint = { invoked: mac.invoked.map((x) => x[0]), native: mac.printed };
  const winOs = load('windows', true);
  out.windowsPrint = winOs.win.print === winOs.basePrint;
  // Ctrl+N and Cmd+N, and the keys that are not it
  const k1 = fire(mac, 'keydown', { ctrlKey: true, key: 'n' });
  const k2 = fire(mac, 'keydown', { metaKey: true, key: 'N' });
  const k3 = fire(mac, 'keydown', { key: 'n' });
  const k4 = fire(mac, 'keydown', { ctrlKey: true, shiftKey: true, key: 'n' });
  out.keys = { invoked: mac.invoked.filter((x) => x[0] === 'new_window').length, prevented: [k1.prevented, k2.prevented, k3.prevented, k4.prevented] };
  // a download: its bytes, as base64, with its name, the click's own way stopped
  const d = load('macos', true);
  const svg = new d.Anchor({ href: 'blob:http://127.0.0.1:8765/abc', download: 'sift-review countries.svg' }, true);
  const c1 = fire(d, 'click', { target: svg, button: 0 });
  await tick();
  out.download = { prevented: c1.prevented, fetched: d.fetched.slice(), invoked: JSON.parse(JSON.stringify(d.invoked)) };
  // a big one, read in pieces and joined whole
  const big = new d.Anchor({ href: 'blob:big', download: 'map.png' }, true);
  fire(d, 'click', { target: big, button: 0 });
  await tick();
  const sent = d.invoked[d.invoked.length - 1][1].data;
  out.bigWhole = Buffer.from(sent, 'base64').equals(Buffer.from(Uint8Array.from({ length: 100000 }, (_, i) => (i * 7) % 256)));
  // names: from the address when the link gives none, and "download" for a blob's
  const n1 = new d.Anchor({ href: 'http://127.0.0.1:8765/files/report%20one.csv?x=1', download: '' }, true);
  const n2 = new d.Anchor({ href: 'blob:http://127.0.0.1:8765/def', download: '' }, true);
  fire(d, 'click', { target: n1, button: 0 });
  fire(d, 'click', { target: n2, button: 0 });
  await tick();
  out.names = d.invoked.slice(-2).map((x) => x[1].name);
  // a file that cannot be read: the window is told, with no bytes
  const f = load('windows', true, true);
  fire(f, 'click', { target: new f.Anchor({ href: 'blob:gone', download: 'gone.svg' }, true), button: 0 });
  await tick();
  out.failed = f.invoked;
  // a link clicked while in no page: saved too, and an ordinary link's own click left alone
  const g = load('macos', true);
  new g.Anchor({ href: 'blob:loose', download: 'loose.svg' }, false).click();
  new g.Anchor({ href: '/', download: 'kept.svg' }, true).click();
  new g.Anchor({ href: '/' }, false).click();
  await tick();
  out.loose = { invoked: g.invoked.map((x) => x[1] && x[1].name), native: g.nativeClicks };
  // Cmd or Ctrl and a click, or a middle click, on a link of the app's: a new window. A plain click, a
  // link within the page and a download are not
  const l = load('macos', true);
  const link = new l.Anchor({ href: '/design' }, true);
  link.href = 'http://127.0.0.1:8765/design';
  const a1 = fire(l, 'click', { target: link, metaKey: true, button: 0 });
  const a2 = fire(l, 'click', { target: link, ctrlKey: true, button: 0 });
  const a3 = fire(l, 'auxclick', { target: link, button: 1 });
  const a4 = fire(l, 'click', { target: link, button: 0 });
  const hash = new l.Anchor({ href: '#top' }, true);
  const a5 = fire(l, 'click', { target: hash, ctrlKey: true, button: 0 });
  out.links = { opened: l.opened, prevented: [a1.prevented, a2.prevented, a3.prevented, a4.prevented, a5.prevented] };
  // run twice, it takes hold once
  const twice = load('macos', true);
  new Function('window', src)(twice.win);
  out.once = (twice.on.click || []).length;
  console.log(JSON.stringify(out));
})();
""", encoding="utf-8")
        run = subprocess.run([node, str(harness), str(tauri / "window.js")], capture_output=True, text=True, encoding="utf-8")
        try:
            got = json.loads(run.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            got = {}
        check("164: in a browser, with no window's bridge, window.js does nothing at all: no listener, print and a link's "
              "click as they were", got.get("bare") == {"listeners": 0, "print": True, "click": True}, run.stderr[-300:] or str(got.get("bare")))
        check("164: on a Mac the page's Print asks the window for its print panel, and on Windows print is the web "
              "view's own", got.get("macPrint") == {"invoked": ["print"], "native": 0} and got.get("windowsPrint") is True,
              str(got.get("macPrint")))
        check("164: Ctrl+N and Cmd+N ask for a new window, and n alone or with Shift does not",
              got.get("keys") == {"invoked": 2, "prevented": [True, True, False, False]}, str(got.get("keys")))
        check("164: a download link's click is stopped, its file read and handed to the window as base64 with its own "
              "name, a big file read in pieces and whole",
              got.get("download") == {"prevented": True, "fetched": ["blob:http://127.0.0.1:8765/abc"],
                                      "invoked": [["save_download", {"name": "sift-review countries.svg", "data": "PHN2Zz4="}]]}
              and got.get("bigWhole") is True, str(got.get("download"))[:300])
        check("164: a download with no name takes the last part of its address, and a blob's is called download; a "
              "file that cannot be read reaches the window with no bytes, so it says it was not saved",
              got.get("names") == ["report one.csv", "download"]
              and got.get("failed") == [["save_download", {"name": "gone.svg", "data": None}]], f"{got.get('names')} {got.get('failed')}")
        check("164: a download link clicked while in no page is saved the same way, and any other link's click is "
              "the page's own", got.get("loose") == {"invoked": ["loose.svg"], "native": 2}, str(got.get("loose")))
        check("164: Cmd or Ctrl and a click, or a middle click, opens a link of the app's in a new window, and a plain "
              "click or a link within the page stays",
              got.get("links") == {"opened": [["http://127.0.0.1:8765/design", "_blank"]] * 3,
                                   "prevented": [True, True, True, False, False]} and got.get("once") == 1, str(got.get("links")))
    else:
        skip("164: window.js under node", "node is not on this machine")

    # ── C. the commands the page may call, named alike in the build, the handler and the capability
    built = re.findall(r'"([a-z_]+)"', build_rs.split(".commands(&[", 1)[1].split("])", 1)[0])
    handled = [c.strip() for c in main_rs.split("generate_handler![", 1)[1].split("]", 1)[0].split(",")]
    allowed = sorted(p.removeprefix("allow-").replace("-", "_") for p in cap["permissions"])
    commands = ["print", "new_window", "save_download", "save_path", "pick", "confirm", "opened", "keep", "recent", "project_now", "zoom", "edit", "announce", "closing", "updates"]
    check("164: the page may call the window's commands and nothing else, print, new_window and save_download, and "
          "since the second build pick, keep, recent, zoom, edit and closing (area 167), and since the fourth updates (area 175), and since 21 October save_path (area 232), "
          "and since 6 November opened (area 332), and since 9 November announce (area 360) and confirm (area 330), save_pdf and save_png gone since 9 November (area 367), "
          "named alike in build.rs, the handler and the capability, from the server's own address alone",
          built == handled == commands and allowed == sorted(built)
          and cap["remote"]["urls"] == ["http://127.0.0.1:*", "http://127.0.0.1:*/*"] and cap["windows"] == ["main", "page-*"],
          f"{built} {handled} {allowed}")
    # `ask` for a command whose failure is nothing, `ipc.invoke` itself where the page hears it fail
    used = set(re.findall(r"(?:ask|ipc\.invoke)\('([a-z_]+)'", window_js))
    check("164: window.js calls only those commands", used == set(commands), str(used))

    # ── D. nothing for a check ships: the drive feature off by default, the debugging port only in a check's run
    drive_uses = [i for i, line in enumerate(main_rs.splitlines()) if "drive::" in line and not line.strip().startswith(("//", "///"))]
    lines = main_rs.splitlines()
    guarded = all(any("cfg(feature = \"drive\")" in lines[j] for j in range(max(0, i - 5), i)) for i in drive_uses)
    shipped = (main_rs, cargo, json.dumps(conf), build_rs, window_js)
    check("164: the drive feature is off in every build that ships, every use of it is behind its cfg, and no shipped "
          "file opens a debugging port",
          "[features]" in cargo and "drive = [" in cargo and "default" not in cargo.split("[features]", 1)[1].split("[profile", 1)[0]
          and drive_uses and guarded and "#[cfg(feature = \"drive\")]\nmod drive" in main_rs
          and not any("remote-debugging" in text for text in shipped)
          and "--remote-debugging-port" in read(tauri / "drive_windows.py"), f"{len(drive_uses)} uses")
    # the window's own workflow, tauri.yml, was dropped before the public copy (21 October): it ran only on
    # spike/tauri and took two jobs' files from runs of the private repository. Its drive scripts stay
    check("164, updated 21 October: the test app the drive scripts build is uk.co.adamknowles.idiograph.test, "
          "Idiograph Test, and no workflow of the window's own is left",
          not support.source(".github/workflows/tauri.yml").exists()
          and '"identifier": "uk.co.adamknowles.idiograph.test"' in read(tauri / "bundle.py")
          and '"productName": "Idiograph Test"' in read(tauri / "bundle.py")
          and not support.source(".github/workflows/tauri-spike.yml").exists())
    check("164: the bundle's own identity is the Mac app's, uk.co.adamknowles.idiograph, Idiograph, and Tauri's own "
          "handling of drops is off in every window, so the page's own takes a file dragged onto it",
          conf["identifier"] == "uk.co.adamknowles.idiograph" and conf["productName"] == "Idiograph"
          and conf["mainBinaryName"] == "Idiograph" and ".disable_drag_drop_handler()" in main_rs)

    # ── E. the window and the server speak the same words
    finish = server_mod.finish.__code__.co_consts
    check("164: the window reads the server's last words in its log as the server prints them: Restarting., "
          "<app> is closed. and its own quit's line, so a Restart is waited for and a Quit closes the windows",
          'const RESTARTING: &str = "Restarting.";' in main_rs and "Restarting." in finish and "errors.closed" in finish and "en" in finish
          and 'const CLOSED: [&str; 2] = [" is closed.", "so it quit by itself."];' in main_rs
          and server_mod.named(server_mod.CLOSED_LINE).endswith(" is closed.") and server_mod.QUIT_LINE.endswith("so it quit by itself."))

    # ── F. Claude Desktop's entry for the window's bundle on each system
    mac_server = "/Applications/Idiograph.app/Contents/Resources/server/Idiograph"
    win_server = r"C:\Users\Wren\AppData\Local\Idiograph\server\Idiograph.exe"
    check("164: Add Idiograph to Claude Desktop names the window bundle's own server, on a Mac the server in the "
          "bundle's Resources and on Windows its console twin beside it",
          mcp_server.server_command(frozen=True, executable=mac_server, system="darwin") == [mac_server, "mcp"]
          and mcp_server.server_command(frozen=True, executable=win_server, system="win32")
          == [r"C:\Users\Wren\AppData\Local\Idiograph\server\Idiograph-console.exe", "mcp"])

    # ── G. the checks' own world is invented
    check("164: the checks' world is invented, dogs at home, and names no participant of a real study",
          "Dog routines" in common and not any(re.search(rf"\b{n}\b", common) for n in STUDY_PSEUDONYMS))
