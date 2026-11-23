"""Area 451: Email for updates in Idiograph's Settings (updates-app, 23 November 2026).

Settings, General, under Your name, takes an address, says in one line why and links the privacy page, and Sign up sends
at once: the app's own server posts `{"email", "source": "app", "version", "consent": "updates-2026-11-23-app", "website": ""}`
to the updates Worker on idiograph.app, as Send feedback posts a note, the address in `updates_url` over the built-in
one. The Worker sends the confirmation email, so the page says "Check your email to confirm" with the address. The
address is kept in the app's own settings, never in a project. Get updates by email… in Idiograph's Help menu and in
About opens Settings at General with the field in front. Sift and Trace have none of it.

Since appup (23 November 2026, Adam's word) the field is "Your email", one piece drawn in Settings, folded in a box on
Home and at What's new's foot, and the app knows from its settings that it has signed up: the address then stands as
words with Edit and no Sign up, and Home and What's new show no box.

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
  dataset: { built: '1' }, attrs: {}, cls: {},
  setAttribute(k, v) { this.attrs[k] = v; }, removeAttribute(k) { delete this.attrs[k]; },
  classList: { toggle(c, on) { el(id).cls[c] = !!on; }, add() {} },
  focus() { log.push('focus ' + id); }, select() {}, scrollIntoView() { log.push('scroll ' + id); } });
const $ = el;
const t = (key, slots) => key + (slots ? ' ' + JSON.stringify(slots) : '');
const esc = (x) => String(x);
const needsRestart = () => false;
const RESTART_LINE = 'restart';
const said = [];
const say = (m) => said.push(m);
const hide = (id) => { log.push('hide ' + id); $(id).hidden = true; };
const openSettings = (pane) => { log.push('openSettings ' + pane); };
const S = { libConfig: {}, data: null };
let asked = [];
let answer = { email: 'ada@example.org', sent: true };
const api = async (path, body) => { asked.push([path, body]); if (answer instanceof Error) throw answer; return answer; };
__CODE__
const view = (w) => ({ field: !$('upd-' + w + '-email').hidden,
  addr: $('upd-' + w + '-addr').hidden ? null : $('upd-' + w + '-addr').textContent,
  go: !$('upd-' + w + '-go').hidden, edit: !$('upd-' + w + '-edit').hidden, cancel: !$('upd-' + w + '-cancel').hidden,
  said: $('upd-' + w + '-said').textContent, failed: !!$('upd-' + w + '-said').cls['said-failed'],
  invalid: $('upd-' + w + '-email').attrs['aria-invalid'] || null, box: !$('upd-' + w).hidden });
(async () => {
  const out = {};
  // 1. a first visit: the field with Sign up, no line, and the box on Home
  updatesOpen({});
  updatesHome({});
  out.fresh = [view('settings'), view('home').box];
  // 2. a bad address is said under the field, the field marked and in front, and nothing is asked
  $('upd-settings-email').value = 'not an address';
  await updatesSignUp('settings');
  out.bad = [asked.length, view('settings'), log.slice(-1)[0]];
  // 2b. Save with a bad address: refused, Settings stays open
  const badSave = updatesSaves();
  out.saveBad = [badSave, updatesRefuse(badSave), asked.length];
  // 3. a send that did not go through: its line in the warning tint, the field unmarked, the address kept, Sign up in front
  answer = new Error('The sign-up could not be sent.');
  $('upd-settings-email').value = 'bo@example.org';
  await updatesSignUp('settings');
  out.refused = [view('settings'), $('upd-settings-email').value, log.slice(-1)[0], $('upd-settings-go').disabled];
  // 3b. the Worker's own 400 marks the field as the local check does, with the focus in it, and says it was said
  const e400 = new Error('That is not an email address.'); e400.code = 'not_an_address';
  answer = e400;
  $('upd-settings-email').value = 'bo@example.org';
  await updatesSignUp('settings');
  out.e400 = [view('settings').invalid, log.slice(-1)[0], e400.said === true, $('upd-settings-said').attrs['aria-live']];
  // 4. a good one, signed up from Home
  answer = { email: 'ada@example.org', sent: true };
  $('upd-home-email').value = '  ada@example.org ';
  await updatesSignUp('home');
  out.good = [asked.slice(-1)[0], view('home'), log.slice(-1)[0], view('settings'), view('whatsnew').box,
    S.libConfig.updates_email, S.libConfig.updates_sent];
  // 5. Home drawn again: the box is gone; Settings opened again in this page's life keeps the line
  updatesHome(S.libConfig);
  updatesOpen(S.libConfig);
  out.after = [view('home').box, view('settings')];
  // 6. Edit, then Cancel
  updatesEdit('settings');
  out.edit = [view('settings'), $('upd-settings-email').value, updatesSaves()];
  updatesCancel('settings');
  out.cancel = [view('settings'), asked.length, updatesSaves()];
  // 6b. Edit, then Sign up with the address as it stood: a Cancel, nothing sent
  updatesEdit('settings');
  const before6 = asked.length;
  await updatesSignUp('settings');
  out.same = [asked.length - before6, view('settings').edit, view('settings').field];
  // 7. Save with a new address while editing sends it
  updatesEdit('settings');
  answer = { email: 'cy@example.org', sent: true };
  $('upd-settings-email').value = ' cy@example.org ';
  const newSave = updatesSaves();
  await updatesSendSaved(newSave);
  out.saveNew = [newSave, asked.slice(-1)[0], said.slice(), view('settings')];
  // 8. Help's and About's item
  $('about').hidden = false;
  log.length = 0;
  window.idiographUpdates();
  out.open = log.slice();
  console.log(JSON.stringify(out));
})();
"""

KNOWN = r"""
const S = { libConfig: {}, data: null };
const log = [];
const els = {};
const $ = (id) => els[id] || (els[id] = { id, hidden: false, value: '', textContent: '', dataset: { built: '1' }, attrs: {},
  cls: {}, setAttribute(k, v) { this.attrs[k] = v; }, removeAttribute(k) { delete this.attrs[k]; },
  classList: { toggle(c, on) { $(id).cls[c] = !!on; }, add() {} }, focus() { log.push('focus ' + id); },
  scrollIntoView() {} });
const t = (k) => k;
const hide = () => {};
const openSettings = () => {};
__CODE__
// a later visit: the settings say it has signed up
updatesOpen({ updates_email: 'ada@example.org', updates_sent: true });
updatesHome({});
updatesWhatsNew();
$('about').hidden = true;
window.idiographUpdates();
console.log(JSON.stringify([$('upd-settings-email').hidden, $('upd-settings-addr').textContent, $('upd-settings-go').hidden,
  $('upd-settings-edit').hidden, $('upd-settings-said').textContent, $('upd-home').hidden, $('upd-whatsnew').hidden,
  log.slice(-1)[0]]));
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
              kept[4] == "https://idiograph.app/api/updates/subscribe" and server_mod.UPDATES_CONSENT == "updates-2026-11-23-app"
              and server_mod.UPDATES_TIMEOUT == 15 and "/api/updates" in server_mod.POST_ONLY
              and "/api/updates" in server_mod.WINDOW_ONLY and server_mod.ROUTE_APP.get("/api/updates") == "idiograph"
              and server_mod.ROUTES.get("/api/updates") is server_mod.api_updates)
        bad = [server_mod.api_updates({"email": e}) for e in
               ("", "   ", None, "ada", "ada@", "@example.org", "ada@example", "a b@example.org", "ada@@example.org",
                "x" * 250 + "@example.org", "ada@example.org\n.evil")]
        check("451: an address that is not one is refused in one line before anything is posted",
              all(b == {"error": "That is not an email address.", "code": "not_an_address", "status": 400} for b in bad)
              and not seen, str(bad[:3]))
        sent = server_mod.api_updates({"email": f"  {mail} ", "source": "site", "website": "x", "consent": "other"})
        call = seen[0] if seen else {"body": {}, "headers": {}}
        check("451: a sign-up is one POST to the Worker with the contract's body, the address trimmed, the app as its "
              "source and the honeypot empty, whatever the page adds, and no Origin header",
              sent == {"sent": True, "email": mail} and len(seen) == 1 and call.get("path") == "/api/updates/subscribe"
              and call["body"] == {"email": mail, "source": "app", "version": server_mod.VERSION,
                                   "consent": "updates-2026-11-23-app", "website": ""}
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
              said == {"error": "That is not an email address.", "code": "not_an_address", "status": 400}
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

    # ── B. the page: the one piece in Settings, on Home and in What's new, and the item that opens it, in node
    node = shutil.which("node")
    if not node:
        skip("451: the page's Your email and the item that opens Settings, in node", "node is not installed")
    else:
        code = distil[distil.index("const UPDATES = "):distil.index("/* the project whose page the home screen shows")]
        ran = support.run_node("var window = {};\n" + HARNESS.replace("__CODE__", code), scratch, "a451-page.js")
        got = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {}
        fresh = {"field": True, "addr": None, "go": True, "edit": False, "cancel": False, "said": "", "failed": False,
                 "invalid": None, "box": True}
        check("451: a first visit shows the field with Sign up and no line in Settings, and the box on Home",
              got.get("fresh") == [fresh, True], ran.stderr[-300:] or str(got.get("fresh")))
        bad = got.get("bad", [1, {}, ""])
        check("451: a bad address is said under the field in the warning tint, the field marked invalid and in front, "
              "and nothing is asked",
              bad[0] == 0 and bad[1].get("said") == "distil.updates.not_an_address" and bad[1].get("failed") is True
              and bad[1].get("invalid") == "true" and bad[2] == "focus upd-settings-email", str(bad))
        check("451: Save with a typed address that is not one is refused (Settings stays open) and nothing is asked",
              got.get("saveBad") == [{"bad": True}, True, 0], str(got.get("saveBad")))
        ref = got.get("refused", [{}, "", "", True])
        check("451: a send that did not go through is said under the field in the warning tint, the field unmarked with "
              "the address kept, Sign up in front and enabled",
              ref[0].get("said") == "The sign-up could not be sent." and ref[0].get("failed") is True
              and ref[0].get("invalid") is None and ref[0].get("field") is True and ref[1] == "bo@example.org"
              and ref[2] == "focus upd-settings-go" and ref[3] is False, str(ref))
        good = got.get("good", [None, {}, "", {}, True, None, None])
        check("451: a good address is asked trimmed; the place it was sent from shows it as words with Edit, no Sign up, "
              "and the line to check the email, Edit in front; Settings knows at once, its old failure line gone, What's new's box goes, and the "
              "page's settings carry it",
              good[0] == ["/api/updates", {"email": "ada@example.org"}]
              and good[1] == {"field": False, "addr": "ada@example.org", "go": False, "edit": True, "cancel": False,
                              "said": "distil.updates.sent", "failed": False, "invalid": None, "box": True}
              and good[2] == "focus upd-home-edit" and good[3].get("addr") == "ada@example.org"
              and good[3].get("said") == "" and good[3].get("failed") is False
              and good[3].get("go") is False and good[4] is False and good[5] == "ada@example.org" and good[6] is True,
              str(good))
        aft = got.get("after", [True, {}])
        check("451: Home drawn again shows no box, and Settings opened again in the page's life keeps the line",
              aft[0] is False and aft[1].get("addr") == "ada@example.org" and aft[1].get("said") == "distil.updates.sent",
              str(aft))
        ed, ca = got.get("edit", [{}, "", None]), got.get("cancel", [{}, 0, None])
        check("451: Edit makes the address a field again with Sign up and Cancel; Cancel puts it back as words and sends "
              "nothing; the address unchanged is no sign-up for Save",
              ed[0].get("field") is True and ed[0].get("go") is True and ed[0].get("cancel") is True
              and ed[0].get("edit") is False and ed[1] == "ada@example.org" and ed[2] == {"skip": True}
              and ca[0].get("field") is False and ca[0].get("addr") == "ada@example.org" and ca[1] == 3
              and ca[2] == {"skip": True}, str(ed) + str(ca))
        e4, sm = got.get("e400", [None, "", False, ""]), got.get("same", [1, False, True])
        check("451: the Worker's own 400 marks the field as a bad address, the focus in it, the line heard once "
              "(the status region off while the field is marked), and the error carries that it was said",
              e4 == ["true", "focus upd-settings-email", True, "off"], str(e4))
        check("451: Edit, then Sign up with the address unchanged is a Cancel: nothing sent, Edit back",
              sm == [0, True, False], str(sm))
        sn = got.get("saveNew", [None, None, [], {}])
        check("451: Save with a new address while editing sends it as a new sign-up, trimmed, and says so over the "
              "screen behind",
              sn[0] == {"email": "cy@example.org"} and sn[1] == ["/api/updates", {"email": "cy@example.org"}]
              and sn[2] == ["distil.updates.sent"] and sn[3].get("addr") == "cy@example.org", str(sn))
        check("451: Help's and About's item puts About away and opens Settings at General with Edit in front once signed up",
              got.get("open") == ["hide about", "openSettings general", "focus upd-settings-edit", "scroll upd-settings-edit"],
              str(got.get("open")))
        ran = support.run_node("var window = {};\n" + KNOWN.replace("__CODE__", code), scratch, "a451-known.js")
        known = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else []
        check("451: a later visit knows from the settings it has signed up: the address as words with Edit, no Sign up, "
              "no line, no box on Home or in What's new, and Help's item puts Edit in front",
              known == [True, "ada@example.org", True, False, "", True, True, "focus upd-settings-edit"],
              ran.stderr[-300:] or str(known))

    # ── C. the markup, the menus and the other apps
    family_page = support.text("family/static/page.html")
    check("451: Settings, General has Your email's place under Your name, Home its box on the picker before the "
          "projects, and What's new its box at its foot, Idiograph's alone; the piece says Your email, Sign up, Edit, "
          "Cancel and the one why line with the privacy link opened the way About's links are",
          page.index('id="set-your-name"') < page.index('id="upd-settings"')
          and page.index('id="upd-home"') < page.index('id="home-analysis"')
          and page.index('id="whatsnew-earlier"') < page.index('id="upd-whatsnew"') < page.index('id="whatsnew-done"')
          and "<!--slot:whatsnew-foot-->" in family_page and 'id="upd-' not in family_page
          and all('id="upd-' not in support.page_text(app=a) for a in ("sift", "trace"))
          and "t('distil.updates.your_email')" in distil and "t('distil.updates.sign_up')" in distil
          and "t('distil.updates.edit')" in distil and "t('distil.updates.cancel')" in distil
          and "t('distil.updates.get_by_email')" in distil and "t('distil.updates.why')" in distil
          and 'href="https://idiograph.app/privacy" target="_blank" rel="noopener"' in distil
          and "I never sell" not in page and "Email for updates" not in page
          and "aria-describedby=\"${id('said')} ${id('why')}\"" in distil
          and "updates_email" not in whole(distil, "function distilSettingsBody("))
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
