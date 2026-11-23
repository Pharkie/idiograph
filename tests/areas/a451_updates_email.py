"""Area 451: Email for updates in Idiograph's Settings (updates-app, 23 November 2026).

Settings, General, under Your name, takes an address, says in one line why and links the privacy page, and Sign up sends
at once: the app's own server posts `{"email", "source": "app", "version", "consent": "updates-2026-11-23", "website": ""}`
to the updates Worker on idiograph.app, as Send feedback posts a note, the address in `updates_url` over the built-in
one. The Worker sends the confirmation email, so the page says "Check your email to confirm" with the address. The
address is kept in the app's own settings, never in a project. Get updates by email… in Idiograph's Help menu and in
About opens Settings at General with the field in front. Sift and Trace have none of it.

What is checked: over HTTP, in this process, against a fake Worker on a port of the suite's own, the route's POST has
the contract's body and no Origin header, an invalid address is refused before anything is posted, the Worker's own
400, a refusal and a Worker out of reach are each one line and keep no address, a good sign-up keeps the address in the
settings and in no file of the project, and a settings save keeps it; in node, the page's Sign up, which refuses a
bad address before it asks and shows the state, and the item that opens Settings at General with the field focused; and
in the sources, the Help menu's item in Idiograph's own bar alone on a Mac and on Windows, handled by the window and the
page, About's link, and that Sift and Trace answer none of it."""
from __future__ import annotations

import http.server
import json
import shutil
import threading
import urllib.error
import urllib.request

from . import support
from .support import check, skip


def whole(src: str, head: str) -> str:
    at = src.index(head)
    return src[at:src.index("\n}\n", at) + 3]


HARNESS = r"""
const log = [];
const els = {};
const el = (id) => els[id] || (els[id] = { id, hidden: false, value: '', textContent: '', disabled: false,
  attrs: {}, setAttribute(k, v) { this.attrs[k] = v; }, removeAttribute(k) { delete this.attrs[k]; },
  classList: { toggle() {} }, focus() { log.push('focus ' + id); }, scrollIntoView() { log.push('scroll ' + id); } });
const $ = el;
const t = (key, slots) => key + (slots ? ' ' + JSON.stringify(slots) : '');
const saidIn = (id, text, failed) => { $(id).textContent = text; $(id).failed = !!failed; };
const needsRestart = () => false;
const RESTART_LINE = 'restart';
const said = [];
const say = (m) => said.push(m);
const hide = (id) => { log.push('hide ' + id); $(id).hidden = true; };
const openSettings = (pane) => { log.push('openSettings ' + pane); };
let asked = [];
let answer = { email: 'ada@example.org', sent: true };
const api = async (path, body) => { asked.push([path, body]); if (answer instanceof Error) throw answer; return answer; };
__CODE__
(async () => {
  const out = {};
  // 1. nothing sent before a sign-up: an empty line with the field as it was saved
  updatesOpen({});
  out.fresh = [$('set-updates-email').value, $('set-updates-said').textContent];
  UPDATES.email = null;
  // the mark from an earlier session is no state line: it came back every time Settings opened
  updatesOpen({ updates_email: 'ada@example.org', updates_sent: true });
  out.kept = [$('set-updates-email').value, $('set-updates-said').textContent];
  updatesOpen({ updates_email: 'ada@example.org' });
  out.unsent = $('set-updates-said').textContent;
  out.keptSave = updatesSaves();
  // 2. a bad address is said plainly and never asked
  $('set-updates-email').value = 'not an address';
  await updatesSignUp();
  out.bad = [asked.length, $('set-updates-said').textContent, $('set-updates-said').failed, log.slice(-1)[0],
    $('set-updates-email').attrs['aria-invalid']];
  // 2b. Save with a bad address: refused, Settings stays open, the field marked
  $('set-updates-email').attrs = {};
  const badSave = updatesSaves();
  out.saveBad = [badSave, updatesRefuse(badSave), $('set-updates-email').attrs['aria-invalid'], asked.length];
  // 3. a good one is asked of the route, trimmed, and the state shows the address
  $('set-updates-email').value = '  ada@example.org ';
  await updatesSignUp();
  out.good = [asked.slice(), $('set-updates-said').textContent, $('set-updates-said').failed, $('set-updates-go').disabled];
  // 4. the card opened again in this session keeps what was signed up, whatever snapshot of the settings it is given
  updatesOpen({});
  out.again = [$('set-updates-email').value, $('set-updates-said').textContent, $('set-updates-email').attrs['aria-invalid']];
  // 4b. the same address again on Save is no second sign-up
  out.saveSame = [updatesSaves(), asked.length];
  // 4c. Save with a new, valid address sends it as Sign up does, and says so over the screen behind
  answer = { email: 'cy@example.org', sent: true };
  $('set-updates-email').value = ' cy@example.org ';
  const newSave = updatesSaves();
  await updatesSendSaved(newSave);
  out.saveNew = [newSave, asked.slice(-1)[0], said.slice(), $('set-updates-said').textContent];
  // 4d. an empty field is no sign-up and no refusal
  $('set-updates-email').value = '  ';
  out.saveEmpty = [updatesSaves(), updatesRefuse(updatesSaves())];
  answer = { email: 'ada@example.org', sent: true };
  // 5. a refusal from the server is its line, in the failure tint, and the button is back
  answer = new Error('The sign-up could not be sent.');
  $('set-updates-email').value = 'bo@example.org';
  await updatesSignUp();
  out.refused = [$('set-updates-said').textContent, $('set-updates-said').failed, $('set-updates-go').disabled];
  // 6. Help's and About's item: About put away, Settings at General, the field focused
  $('about').hidden = false;
  log.length = 0;
  window.idiographUpdates();
  out.open = log.slice();
  console.log(JSON.stringify(out));
})();
"""


def test_updates_email(scratch):
    print("\n451. Email for updates: Settings, the route, Help and About (updates-app)")
    import server as server_mod

    shell = support.text("family/static/shell.js")
    distil = support.text("apps/idiograph/static/distil.js")
    window_js = support.text("packaging/tauri/window.js")
    menu_rs = support.text("packaging/tauri/src-tauri/src/menu.rs")
    main_rs = support.text("packaging/tauri/src-tauri/src/main.rs")
    menus = json.loads(support.text("family/static/i18n/en/menus.json"))
    page = support.page_text()

    # ── A. the route over HTTP, against a Worker of the suite's own
    seen: list = []
    mode = {"status": 200}

    class Worker(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("content-length") or 0)
            seen.append({"path": self.path, "headers": {k.lower(): v for k, v in self.headers.items()},
                         "body": json.loads(self.rfile.read(length) or b"{}")})
            data = b'{"ok": true}' if mode["status"] == 200 else b'{"ok": false, "error": "email"}'
            self.send_response(mode["status"])
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *_):
            pass

    httpd = None
    for port in range(8841, 8860):
        try:
            httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Worker)
            break
        except OSError:
            continue
    if httpd is None:
        check("451: a port of the suite's own for the fake Worker", False, "8841 to 8859 are all taken")
        return
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    worker_url = f"http://127.0.0.1:{port}/api/updates/subscribe"
    root = scratch / "updates-root"
    work = support.demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    cfg_path = scratch / "updates-config.json"
    cfg_path.write_text(json.dumps({"interviewer": "Adam", "updates_url": worker_url}), encoding="utf-8")
    off_path = scratch / "updates-off.json"
    off_path.write_text(json.dumps({"interviewer": "Adam"}), encoding="utf-8")
    kept = (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY, server_mod.CONFIG_PATH,
            server_mod.UPDATES_URL)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_MEMORY = {"recent": []}
    server_mod.CONFIG_PATH = cfg_path
    mail = "ada.lark@example.org"
    try:
        check("451: the Worker's address is idiograph.app's route, the wording's version is the contract's, and the "
              "route is Idiograph's own, posted to and kept to its window",
              kept[4] == "https://idiograph.app/api/updates/subscribe" and server_mod.UPDATES_CONSENT == "updates-2026-11-23"
              and server_mod.UPDATES_TIMEOUT == 15 and "/api/updates" in server_mod.POST_ONLY
              and "/api/updates" in server_mod.WINDOW_ONLY and server_mod.ROUTE_APP.get("/api/updates") == "idiograph"
              and server_mod.ROUTES.get("/api/updates") is server_mod.api_updates)
        bad = [server_mod.api_updates({"email": e}) for e in
               ("", "   ", None, "ada", "ada@", "@example.org", "ada@example", "a b@example.org", "ada@@example.org",
                "x" * 250 + "@example.org", "ada@example.org\n.evil")]
        check("451: an address that is not one is refused in one line before anything is posted",
              all(b == {"error": "That is not an email address. Check it and try again.", "status": 400} for b in bad)
              and not seen, str(bad[:3]))
        sent = server_mod.api_updates({"email": f"  {mail} ", "source": "site", "website": "x", "consent": "other"})
        call = seen[0] if seen else {"body": {}, "headers": {}}
        check("451: a sign-up is one POST to the Worker with the contract's body, the address trimmed, the app as its "
              "source and the honeypot empty, whatever the page adds, and no Origin header",
              sent == {"sent": True, "email": mail} and len(seen) == 1 and call.get("path") == "/api/updates/subscribe"
              and call["body"] == {"email": mail, "source": "app", "version": server_mod.VERSION,
                                   "consent": "updates-2026-11-23", "website": ""}
              and "origin" not in call["headers"] and call["headers"].get("content-type") == "application/json"
              and call["headers"].get("user-agent") == f"Idiograph/{server_mod.VERSION}", str((sent, call)))
        held = json.loads(cfg_path.read_text(encoding="utf-8"))
        check("451: the address is kept in the app's own settings with the mark that it was sent, the rest of the file as it was",
              held.get("updates_email") == mail and held.get("updates_sent") is True and held.get("interviewer") == "Adam"
              and held.get("updates_url") == worker_url and server_mod.config().get("updates_email") == mail)
        server_mod.api_settings({"your_name": "Ada Lark"})
        after = json.loads(cfg_path.read_text(encoding="utf-8"))
        check("451: a save of Settings keeps it", after.get("updates_email") == mail and after.get("updates_sent") is True
              and after.get("your_name") == "Ada Lark")
        # never in a project: no file of the project folder holds the address, and the project's own routes do not say it
        found = [str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and mail.encode() in p.read_bytes()]
        check("451: the address is in no file of the project's folder", not found and work.exists(), str(found))
        mode["status"] = 400
        before = len(seen)
        said = server_mod.api_updates({"email": "bo@example.org"})
        check("451: the Worker's own 400 is the same plain line, and no address is kept for it",
              said == {"error": "That is not an email address. Check it and try again.", "status": 400}
              and len(seen) == before + 1 and server_mod.config().get("updates_email") == mail)
        mode["status"] = 503
        said = server_mod.api_updates({"email": "bo@example.org"})
        check("451: a Worker that refuses says so in plain words with its status, and keeps nothing",
              said == {"error": "The sign-up could not be sent just now (HTTP 503). Try again later.", "status": 502}
              and server_mod.config().get("updates_email") == mail, str(said))
        mode["status"] = 200
        httpd.shutdown()
        httpd.server_close()
        said = server_mod.api_updates({"email": "bo@example.org"})
        check("451: a Worker out of reach is one line to check the connection, and keeps nothing",
              said == {"error": "The sign-up could not be sent. Check the connection and try again.", "status": 502}
              and server_mod.config().get("updates_email") == mail, str(said))
        server_mod.CONFIG_PATH = off_path
        server_mod.UPDATES_URL = ""
        off = server_mod.api_updates({"email": "bo@example.org"})
        check("451: with no address anywhere the route says so and sends nothing, and an address that is not https, or http on "
              "this machine alone, counts as none",
              off == {"error": "Updates by email are not set up in this build.", "status": 501}
              and server_mod.updates_url({"updates_url": "file:///etc/hosts"}) == ""
              and server_mod.updates_url({"updates_url": "http://updates.example.com/subscribe"}) == ""
              and server_mod.updates_url({"updates_url": "http://127.0.0.1:8841/x"}) == "http://127.0.0.1:8841/x"
              and server_mod.updates_url({"updates_url": "http://localhost:8841/x"}) == "http://localhost:8841/x"
              and server_mod.updates_url({"updates_url": "ftp://x.example/y"}) == ""
              and server_mod.updates_url({"updates_url": " https://x.example/y "}) == "https://x.example/y"
              and not json.loads(off_path.read_text(encoding="utf-8")).get("updates_email"))
    finally:
        (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY, server_mod.CONFIG_PATH,
         server_mod.UPDATES_URL) = kept
        try:
            httpd.shutdown()
        except Exception:
            pass

    # ── B. the page: Settings' field, Sign up and the item that opens it, in node
    node = shutil.which("node")
    if not node:
        skip("451: the page's Sign up and the item that opens Settings, in node", "node is not installed")
    else:
        code = "\n".join([distil[distil.index("const UPDATES = "):distil.index("/* the project whose page the home screen shows")]])
        script = "var window = {};\n" + HARNESS.replace("__CODE__", code)
        ran = support.run_node(script, scratch, "a451-page.js")
        got = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {}
        check("451: opening Settings shows the address kept and an empty line, whatever mark an earlier session left, "
              "and the address kept is no new sign-up for Save",
              got.get("fresh") == ["", ""] and got.get("unsent") == ""
              and got.get("kept") == ["ada@example.org", ""] and got.get("keptSave") == {"skip": True},
              ran.stderr[-300:] or str(got))
        check("451: a bad address is said plainly in the failure tint with the field focused, and nothing is asked",
              got.get("bad", [1])[0] == 0 and got["bad"][1] == "distil.updates.not_an_address" and got["bad"][2] is True
              and got["bad"][3] == "focus set-updates-email" and got["bad"][4] == "true", str(got.get("bad")))
        check("451: Save with a typed address that is not one is refused (Settings stays open), the field marked invalid, "
              "and nothing is asked; with an empty field it is neither",
              got.get("saveBad") == [{"bad": True}, True, "true", 0] and got.get("saveEmpty") == [{"skip": True}, False],
              str(got.get("saveBad")) + str(got.get("saveEmpty")))
        check("451: Save with a new valid address sends it as Sign up does, trimmed, and says Check your email over the "
              "screen behind; the address already sent is sent no second time",
              got.get("saveNew", [0, 0, 0, 0])[0] == {"email": "cy@example.org"}
              and got["saveNew"][1] == ["/api/updates", {"email": "cy@example.org"}]
              and len(got["saveNew"][2]) == 1 and got["saveNew"][2][0].startswith("distil.updates.check_your_email")
              and got["saveNew"][3].startswith("distil.updates.check_your_email")
              and got.get("saveSame", [0, 0])[0] == {"skip": True}, str(got.get("saveNew")) + str(got.get("saveSame")))
        check("451: a good one is asked of /api/updates with the address trimmed, and shows Check your email to confirm with "
              "the address, which the card keeps on opening again",
              got.get("good", [[]])[0] == [["/api/updates", {"email": "ada@example.org"}]]
              and got["good"][1].startswith("distil.updates.check_your_email") and got["good"][2] is False
              and got["good"][3] is False and got.get("again", ["", ""])[0] == "ada@example.org"
              and got["again"][1].startswith("distil.updates.check_your_email") and got["again"][2] is None, str(got.get("good")))
        check("451: a refusal is the server's line in the failure tint and Sign up is back",
              got.get("refused") == ["The sign-up could not be sent.", True, False], str(got.get("refused")))
        check("451: Help's and About's item puts About away and opens Settings at General with the field focused",
              got.get("open") == ["hide about", "openSettings general", "focus set-updates-email", "scroll set-updates-email"],
              str(got.get("open")))

    # ── C. the markup, the menus and the other apps
    check("451: Settings, General has the field under Your name, the one line with the privacy link opened the way "
          "About's links are, Sign up in its row and the line under them",
          page.index('id="set-your-name"') < page.index('id="set-updates-email"') < page.index('id="set-updates-go"')
          and 'type="email"' in page[page.index('id="set-updates-email"') - 80:page.index('id="set-updates-email"') + 120]
          and 'href="https://idiograph.app/privacy" target="_blank" rel="noopener">Privacy</a>' in page
          and "I send news of Idiograph and its new versions a few times a year. I never sell your address." in page
          and 'aria-describedby="set-updates-why set-updates-said"' in page and 'id="set-updates-why"' in page
          and page.index('id="set-updates-email"') < page.index('id="set-updates-go"') < page.index('id="set-updates-why"')
          and '<div class="setting setting-updates">' in page
          and "&nbsp;<a href=\"https://idiograph.app/privacy\"" in page
          and "aria-invalid" in distil and "addEventListener('input'" in distil
          and "Email for updates" in page and "updates_email" not in whole(distil, "function distilSettingsBody("))
    check("451: About holds Get updates by email… for Idiograph alone, wired to the same item",
          'id="about-updates"' in support.text("family/static/page.html") and 'data-only="idiograph"' in
          support.text("family/static/page.html").split('id="about-updates"')[0][-120:]
          and 'id="about-updates"' in page and "Get updates by email…" in page
          and "$('about-updates').onclick" in shell and "window.idiographUpdates" in shell)
    mac = menu_rs.split("pub fn build(", 1)[1].split("\n}\n", 1)[0]
    win = menu_rs.split("fn build_bar(", 1)[1].split("\n}\n", 1)[0]
    handled = main_rs.split("fn menu_event(", 1)[1].split("\n}\n", 1)[0]
    check("451: Help gets Get Updates by Email… after Send Feedback in Idiograph's own bar alone, on a Mac and on Windows, "
          "handled by the window and handed to the page",
          'if crate::app::name() == "Idiograph" {' in mac and 'item(app, "updates", &t("menus.updates"), None)' in mac
          and mac.index("&feedback,") < mac.index('"updates"') < mac.index('keep_bar("app"')
          and 'if crate::app::name() == "Idiograph" {' in win and 'item(app, "updates", &t("menus.win_updates"), None)' in win
          and win.index("&feedback,") < win.index('"updates"') < win.index("keep_bar(label")
          and menus["menus.updates"] == "Get Updates by Email…" and menus["menus.win_updates"] == "Get &Updates by Email…"
          and '"updates"' in handled
          and "updates: function () { if (typeof win.idiographUpdates === 'function') win.idiographUpdates(); }" in window_js)
    check("451: the page defines the item's action as Idiograph's own script, and Sift's and Trace's pages and routes "
          "hold none of it",
          "window.idiographUpdates = () => {" in distil
          and all("set-updates-email" not in support.page_text(app=a) for a in ("sift", "trace"))
          and "Idiograph's alone" in support.text("family/static/page.html").split('id="about-updates"')[0][-400:]
          and server_mod.ROUTE_APP.get("/api/updates") == "idiograph",
          str([("set-updates-email" in support.page_text(app=a),)
               for a in ("sift", "trace")]))
