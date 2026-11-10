from __future__ import annotations

import inspect
import json
import os
import re
import shutil
import sys

from . import support
from .support import check, demo_copy, skip
import idiograph_routes


FEEDBACK_WORKER_CHECK = r"""
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';
const mod = await import(pathToFileURL(process.argv[2]).href);
const worker = mod.default;

// a stand-in for D1: the hourly count, the insert and the list, the list giving back the columns
// its SELECT names and no others
function fakeD1() {
  const rows = [];
  const db = {
    rows,
    prepare(sql) {
      return {
        bind(...args) {
          return {
            async first() { const [hash, since] = args; return { n: rows.filter((r) => r.ip_hash === hash && r.at > since).length }; },
            async run() {
              const [at, text, contact, version, platform, screen, agent, ip_hash] = args;
              rows.push({ id: rows.length + 1, at, text, contact, version, platform, screen, agent, ip_hash });
              return { success: true, meta: { last_row_id: rows.length, changes: 1 } };
            },
            async all() {
              const cols = /SELECT (.*?) FROM/.exec(sql)[1].split(', ');
              const picked = rows.slice().reverse().slice(0, args[0]).map((r) => Object.fromEntries(cols.map((c) => [c, r[c]])));
              return { results: picked };
            },
          };
        },
      };
    },
  };
  return db;
}

const env = { DB: fakeD1(), ADMIN_TOKEN: 'suite-admin-value', IP_SALT: 'suite-salt' };
const base = 'https://collector.test';
const cors = [];
const hit = async (req, e = env) => { const res = await worker.fetch(req, e); cors.push(res.headers.get('access-control-allow-origin')); return res; };
const post = (body, ip = '203.0.113.7', e = env) => hit(new Request(base + '/v1/feedback', {
  method: 'POST', headers: { 'content-type': 'application/json', 'cf-connecting-ip': ip },
  body: typeof body === 'string' ? body : JSON.stringify(body) }), e);
const out = {};

const note = { text: '  The trim card hides the timecode.  ', contact: 'me@example.org', version: '0.9.0',
  platform: 'macOS 26.5, darwin', screen: 'pets', agent: 'UA', at: '2020-01-01T00:00:00+00:00',
  path: '/Users/someone/case.xlsx', case: 'Juno', key: 'k' };
let r = await post(note);
out.first = [r.status, await r.json()];
out.row = env.DB.rows[0];
out.hash = createHash('sha256').update('suite-salt:203.0.113.7').digest('hex');
out.row_text = JSON.stringify(out.row);

const status = async (req) => (await hit(req)).status;
out.methods = [
  await status(new Request(base + '/v1/feedback', { method: 'PUT', body: '{}' })),
  await status(new Request(base + '/v1/feedback', { method: 'DELETE' })),
  await status(new Request(base + '/v1/feedback', { method: 'OPTIONS', headers: { origin: 'https://elsewhere.test', 'access-control-request-method': 'POST' } })),
  await status(new Request(base + '/v1/feedback')),
  await status(new Request(base + '/v1/notes', { method: 'POST', body: '{}' })),
  await status(new Request(base + '/elsewhere')),
];
const refusal = async (body) => { const res = await post(body, '198.51.100.9'); return [res.status, (await res.json()).error]; };
out.bodies = [
  await refusal('not json'), await refusal('[1, 2]'), await refusal({ contact: 'x' }), await refusal({ text: 5 }),
  await refusal({ text: '   ' }), await refusal({ text: 'x'.repeat(9000) }),
];
out.after_refusals = env.DB.rows.length;

for (let i = 0; i < 29; i += 1) await post({ text: `note ${i}` });
out.thirtieth = env.DB.rows.length;
r = await post({ text: 'one too many' });
out.limited = [r.status, env.DB.rows.length];
r = await post({ text: '<script>alert(1)</script>', screen: 'statements' }, '192.0.2.1');
out.other_ip = [r.status, (await r.json()).id];

const get = (query = '', headers = {}) => hit(new Request(base + '/v1/notes' + query, { headers }));
out.auth = [
  (await get()).status, (await get('', { authorization: 'Bearer wrong' })).status,
  (await get('?token=' + env.ADMIN_TOKEN)).status, (await get('', { authorization: env.ADMIN_TOKEN })).status,
];
r = await get('', { authorization: 'Bearer ' + env.ADMIN_TOKEN });
const listed = await r.json();
out.list = [r.status, listed.notes.length, listed.notes[0].id, Object.keys(listed.notes[0])];
r = await get('?format=html', { authorization: 'Bearer ' + env.ADMIN_TOKEN });
const html = await r.text();
out.html = [r.status, r.headers.get('content-type'), html.includes('&lt;script&gt;alert(1)&lt;/script&gt;'),
  html.includes('<script>'), r.headers.get('content-security-policy'), html.includes('Iowan Old Style')];

const bare = { DB: fakeD1(), ADMIN_TOKEN: '' };
r = await post({ text: 'no salt' }, '203.0.113.7', bare);
out.no_salt = [r.status, bare.DB.rows.length];
r = await hit(new Request(base + '/v1/notes', { headers: { authorization: 'Bearer ' } }), bare);
out.no_token = r.status;
out.cors = cors.filter((c) => c !== null);
console.log(JSON.stringify(out));
"""


def test_feedback(scratch):
    print("\n56. Send feedback: the bug in both bars, the card, the route and the collector (136)")
    import http.server
    import subprocess
    import threading
    import urllib.error
    import urllib.request
    import server as server_mod

    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    js = support.text("apps/idiograph/static/themes.js")
    folder = support.source("feedback-worker")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0]
    keys = ("text", "contact", "version", "platform", "screen", "agent", "at")

    # ── A. the route, the payload and the transport
    root = scratch / "feedback-root"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    off_cfg = scratch / "feedback-off.json"
    on_cfg = scratch / "feedback-on.json"
    url = "http://127.0.0.1:9/v1/feedback"
    off_cfg.write_text(json.dumps({"interviewer": "Adam"}), encoding="utf-8")
    on_cfg.write_text(json.dumps({"interviewer": "Adam", "feedback_url": url}), encoding="utf-8")
    calls, answers = [], []

    def fake(method, to, headers, payload, timeout):
        calls.append({"method": method, "url": to, "headers": dict(headers), "payload": payload, "timeout": timeout})
        step = answers.pop(0) if answers else (200, '{"ok": true, "id": 7}')
        if isinstance(step, Exception):
            raise step
        return step

    kept = (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY, server_mod.CONFIG_PATH,
            server_mod.FEEDBACK_SEND, server_mod.FEEDBACK_URL)
    server_mod.ROOT_OVERRIDE = str(root)
    server_mod.STATE_MEMORY = {"recent": []}
    server_mod.FEEDBACK_SEND = fake
    server_mod.FEEDBACK_URL = ""
    try:
        check("136, updated 15 October (146): the app carries a version, and the collector's address is the deployed Worker's",
              bool(re.fullmatch(r"\d+\.\d+\.\d+", server_mod.VERSION)) and kept[5] == "https://idiograph-feedback.adam-e56.workers.dev/v1/feedback"
              and server_mod.FEEDBACK_TIMEOUT == 15
              and server_mod.FEEDBACK_MAX == 8192 and "\nFEEDBACK_SEND = ai_mod.http_call\n" in inspect.getsource(server_mod)
              and server_mod.ROUTES.get("/api/feedback") is server_mod.api_feedback and "/api/feedback" in server_mod.POST_ONLY)
        server_mod.CONFIG_PATH = off_cfg
        off = server_mod.api_feedback({"text": "A note", "screen": "statements"})
        check("136: with no address anywhere the route says so in one line and sends nothing",
              off == {"error": "Feedback is not set up in this build.", "status": 501} and not calls, str(off))
        check("136: and the case list, the turn screen and PETs all tell the page to keep the bug hidden",
              idiograph_routes.api_cases({})["feedback"] is False and idiograph_routes.case_payload(work)["feedback"] is False
              and idiograph_routes.api_themes({"workbook": str(work)})["feedback"] is False)
        check("136: an address that is not http or https counts as none, so a stray value never opens a file",
              server_mod.feedback_url({"feedback_url": "file:///etc/hosts"}) == ""
              and server_mod.feedback_url({"feedback_url": "  "}) == ""
              and server_mod.feedback_url({"feedback_url": " https://x.workers.dev/v1/feedback "}) == "https://x.workers.dev/v1/feedback")
        server_mod.FEEDBACK_URL = "https://built.example/v1/feedback"
        check("136: FEEDBACK_URL in server.py turns it on for every copy, and feedback_url in config.json stands in for it on one machine",
              server_mod.feedback_url(server_mod.config()) == "https://built.example/v1/feedback"
              and server_mod.feedback_url({"feedback_url": url}) == url)
        server_mod.FEEDBACK_URL = ""
        server_mod.CONFIG_PATH = on_cfg
        check("136: with an address the three answers say so, and the page draws the bug",
              idiograph_routes.api_cases({})["feedback"] is True and idiograph_routes.case_payload(work)["feedback"] is True
              and idiograph_routes.api_themes({"workbook": str(work)})["feedback"] is True)
        empty = [server_mod.api_feedback(b) for b in ({}, {"text": ""}, {"text": "   \n "}, {"text": None})]
        check("136: an empty note is refused and nothing goes",
              all(e == {"error": "Write the note first.", "status": 400} for e in empty) and not calls, str(empty))
        body = {"text": "  The trim card hides the timecode.  ", "contact": " tester@example.org ", "screen": "pets",
                "agent": "Mozilla/5.0 Test", "path": str(work), "workbook": str(work), "case": "Juno",
                "root": str(root), "key": "not-a-key", "config": {"root": str(root)}}
        sent = server_mod.api_feedback(body)
        call = calls[-1] if calls else {}
        payload = call.get("payload") or {}
        check("136: a note goes by POST to the configured address with a 15-second wait, and the route answers with the row's id",
              sent == {"sent": True, "id": 7} and len(calls) == 1 and call["method"] == "POST" and call["url"] == url
              and call["timeout"] == 15 and call["headers"].get("content-type") == "application/json"
              and call["headers"].get("user-agent") == f"Idiograph/{server_mod.VERSION}", str(sent))
        check("136: the payload is the words, the reply line, the version, the system, the screen, the user agent and the time, and nothing else",
              tuple(payload) == keys and payload["text"] == "The trim card hides the timecode."
              and payload["contact"] == "tester@example.org" and payload["version"] == server_mod.VERSION
              and payload["screen"] == "pets" and payload["agent"] == "Mozilla/5.0 Test"
              and payload["platform"].endswith(sys.platform)
              and bool(re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00$", payload["at"])), str(payload))
        flat = json.dumps(payload)
        check("136: no key named case, workbook, path, root or key, and no path, case or setting in any value, whatever the page sends",
              not any(k in payload for k in ("case", "workbook", "path", "root", "key", "config"))
              and str(work) not in flat and str(root) not in flat and "Juno" not in flat and "not-a-key" not in flat)
        bare = server_mod.feedback_payload("x", None, "anything", None)
        check("136, updated 16 October (160): a screen not in the fixed list goes as none, a missing reply line and "
              "agent as empty, and each is kept short",
              bare["screen"] == "" and bare["contact"] == "" and bare["agent"] == ""
              and server_mod.feedback_payload("x", "", "statements", "")["screen"] == "statements"
              and len(server_mod.feedback_payload("x", "c" * 900, "pets", "")["contact"]) == 200
              and len(server_mod.feedback_payload("x", "", "pets", "a" * 900)["agent"]) == 400)
        words = server_mod.platform_words()
        check("136: the system goes in plain words with Python's name for it",
              (words.endswith(", " + sys.platform) or words == sys.platform)
              and (sys.platform != "darwin" or words.startswith("macOS")), words)
        answers[:] = [(503, ""), (404, ""), (0, ""), OSError("down"), (201, "not json")]
        outcomes = [server_mod.api_feedback({"text": "A note"}) for _ in range(5)]
        check("136: a collector that answers anything but 2xx is one line in plain words with its status in brackets "
              "(17 October, later)",
              outcomes[0] == {"error": "The note could not be sent just now (HTTP 503). Try again later.", "status": 502}
              and outcomes[1] == {"error": "The note could not be sent just now (HTTP 404). Try again later.", "status": 502},
              str(outcomes[:2]))
        check("136: one out of reach, or a transport that throws, is one line too, and a 2xx with no id still counts as sent",
              outcomes[2] == outcomes[3] == {"error": "The note could not be sent. Check the connection and try again.",
                                             "status": 502}
              and outcomes[4] == {"sent": True, "id": None}, str(outcomes[2:]))
        before = len(calls)
        long = server_mod.api_feedback({"text": "word " * 2000})
        check("136: a note over the collector's 8 KB is stopped before it goes, in one line",
              long.get("status") == 413 and "too long" in long.get("error", "") and len(calls) == before, str(long))
        server_mod.api_settings({"interviewer": "Adam"})
        kept_url = json.loads(on_cfg.read_text(encoding="utf-8")).get("feedback_url") == url
        server_mod.CONFIG_PATH = off_cfg
        server_mod.api_settings({"interviewer": "Adam"})
        check("136: Save in Settings keeps a feedback_url written by hand and never adds one",
              kept_url and "feedback_url" not in json.loads(off_cfg.read_text(encoding="utf-8")))
        server_mod.CONFIG_PATH = on_cfg

        # over HTTP: a POST sends, a GET never does
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server_mod.Handler)
        threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
        base = f"http://127.0.0.1:{httpd.server_address[1]}/api/feedback"

        def ask(method, body=None, query=""):
            req = urllib.request.Request(base + query, method=method,
                                         data=None if body is None else json.dumps(body).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    return r.status, json.loads(r.read())
            except urllib.error.HTTPError as exc:
                return exc.code, json.loads(exc.read())

        try:
            before = len(calls)
            got = ask("GET", query="?text=hello")
            posted = ask("POST", {"text": "Over HTTP", "screen": "statements", "agent": "UA"})
            blank = ask("POST", {"text": ""})
        finally:
            httpd.shutdown()
            httpd.server_close()
        check("136: over HTTP a GET is refused and sends nothing, a POST sends, and an empty one is a 400",
              got[0] == 405 and posted == (200, {"sent": True, "id": 7}) and blank[0] == 400
              and len(calls) == before + 1 and calls[-1]["payload"]["text"] == "Over HTTP", str((got, posted, blank)))
    finally:
        (server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY, server_mod.CONFIG_PATH,
         server_mod.FEEDBACK_SEND, server_mod.FEEDBACK_URL) = kept

    # ── B. the bug in both bars, and the card
    draw = fn(app, "drawFeedback")
    send = fn(app, "sendFeedback")
    check("136: the page draws the bug from what the server says, on both bars at once, and an old server's silence keeps it hidden",
          "FEEDBACK.on = !!on;" in draw and "for (const bug of document.querySelectorAll('.rail-feedback')) bug.hidden = !FEEDBACK.on;" in draw
          and "drawFeedback(data.feedback);" in fn(app, "loadLibrary") and "drawFeedback(data.feedback);" in fn(app, "startCase"))
    check("136, updated 16 October (160): the turn screen's bug says statements and the PETs and GETs bar's pets or "
          "gets, with one line in themes.js, and every other bar's names its own screen, the home screen's home or "
          "project, each a word the collector keeps",
          "$('btn-feedback').onclick = () => openFeedback('statements');" in app
          and "$('th-feedback').onclick = () => openFeedback(TH.mode === 'gets' ? 'gets' : 'pets');" in js
          and js.count("openFeedback(") == 1 and js.count("th-feedback") == 1
          and "$('lib-feedback').onclick = () => openFeedback(!$('home-project') || $('home-project').hidden ? 'home' : 'project');" in app
          and "FEEDBACK.screen = String(screen || '');" in fn(app, "openFeedback"))
    check("136: the page sends the words, the reply line, the screen and the user agent, and nothing of the case or the page",
          "text, contact: $('feedback-contact').value.trim(), screen: FEEDBACK.screen, agent: navigator.userAgent," in send
          and not any(w in fn(app, "openFeedback") + send for w in ("canvas", "toDataURL", "clipboard", "getSelection",
                                                                     "S.data", "TH.", "innerText", "outerHTML", "path")))
    keydown = support.keydown_text(app)
    check("136: the card keeps its keys before anything else: Esc cancels, Cmd + Enter sends, and no shortcut fires while typing",
          keydown.index("if (!$('feedback').hidden) {") < keydown.index("if (S.rowMenu)")
          and "if (e.key === 'Escape') { e.preventDefault(); closeFeedback(); }" in keydown
          and "(MOD(e) || e.target === $('feedback-contact'))" in keydown
          and "if (anyOverlayOpen()) return;" in fn(js, "thKeyDown"))

    # ── D. the collector
    names = ("worker.js", "wrangler.toml", "schema.sql", "notes.sh", "README.md")
    check("136: the collector's folder holds the Worker, its config, the table, the notes script and the steps",
          all((folder / n).exists() for n in names))
    if not all((folder / n).exists() for n in names):
        return
    schema = (folder / "schema.sql").read_text(encoding="utf-8")
    notes = (folder / "notes.sh").read_text(encoding="utf-8")
    steps = (folder / "README.md").read_text(encoding="utf-8")
    worker = (folder / "worker.js").read_text(encoding="utf-8")
    cols = re.findall(r"^\s+(\w+)\s+(?:INTEGER|TEXT)\b", schema, flags=re.M)
    check("136: schema.sql makes the notes table, the IP's hash in place of any IP, and the index the hourly count reads",
          cols == ["id", "at", "text", "contact", "version", "platform", "screen", "agent", "ip_hash"]
          and "id       INTEGER PRIMARY KEY" in schema
          and "CREATE INDEX IF NOT EXISTS notes_by_sender ON notes (ip_hash, at);" in schema, str(cols))
    check("136: the Worker allows no CORS, sets no cookie and counts nothing but the notes",
          "access-control" not in worker.lower() and "cookie" not in worker.split("*/", 1)[1].lower()
          and "analytics" not in worker.split("*/", 1)[1].lower()
          and "const HOURLY = 30;" in worker and "const MAX_BODY = 8192;" in worker and "const LIST = 200;" in worker)
    # the shapes a pasted token takes, spelt with a class in each so this line never matches itself
    secretish = re.compile(r"[0-9a-f]{32,}|gh[p]_|github[_]pat_|sk[-]ant|Bearer [A-Za-z0-9]{20,}|(?:ADMIN_TOKEN|IP_SALT)\s*=\s*\"")
    check("136: no secret in any file of the folder, the token read into the shell unseen and sent in a header",
          not any(secretish.search((folder / n).read_text(encoding="utf-8")) for n in names)
          and "read -rs IDIOGRAPH_NOTES_TOKEN" in steps and '"Authorization: Bearer $IDIOGRAPH_NOTES_TOKEN"' in steps
          and "wrangler secret put ADMIN_TOKEN" in steps and "openssl rand -hex 32 | wrangler secret put IP_SALT" in steps)
    check("136: notes.sh reads the table through wrangler, with --since and --md, and never writes it",
          os.access(folder / "notes.sh", os.X_OK) and "wrangler d1 execute idiograph-feedback --remote" in notes
          and "--since)" in notes and "--md)" in notes
          and not any(w in notes for w in ("INSERT", "DELETE", "UPDATE", "DROP")))

    node = shutil.which("node")
    if not node:
        return skip("136: the collector in node", "no node on this machine")
    copy = scratch / "feedback-worker-check.mjs"
    shutil.copy2(folder / "worker.js", copy)
    run = subprocess.run([node, "--check", str(copy)], capture_output=True, text=True, encoding="utf-8")
    plain = [subprocess.run([node, "--check", str(support.source(n))], capture_output=True, text=True, encoding="utf-8").returncode
             for n in ("family/static/shell.js", "apps/idiograph/static/distil.js", "apps/idiograph/static/themes.js")]
    check("136: worker.js, app.js and themes.js pass node --check", run.returncode == 0 and plain == [0, 0, 0],
          run.stderr.strip()[:200])
    script = scratch / "feedback-worker-run.mjs"
    script.write_text(FEEDBACK_WORKER_CHECK, encoding="utf-8")
    run = subprocess.run([node, str(script), str(copy)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("136: the collector runs in node with a stand-in for D1", False, run.stderr.strip()[:300])
    out = json.loads(run.stdout)
    row = out["row"]
    check("136: in node, a note is stored as one row and the answer carries its id",
          out["first"] == [200, {"ok": True, "id": 1}]
          and sorted(row) == sorted(["id", "at", "text", "contact", "version", "platform", "screen", "agent", "ip_hash"])
          and row["text"] == "The trim card hides the timecode." and row["contact"] == "me@example.org"
          and row["version"] == "0.9.0" and row["platform"] == "macOS 26.5, darwin" and row["screen"] == "pets"
          and row["agent"] == "UA", str(row))
    check("136: in node, the row keeps the SHA-256 of the IP and the salt, never the IP, and nothing the note carried besides",
          row["ip_hash"] == out["hash"] and "203.0.113.7" not in out["row_text"]
          and "/Users/someone" not in out["row_text"] and "Juno" not in out["row_text"])
    check("136: in node, the time is the collector's own clock, not the one the note carried",
          bool(re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$", row["at"])) and not row["at"].startswith("2020"), row["at"])
    check("136: in node, any method but POST and GET is refused, each route takes its own, and another path is a 404",
          out["methods"] == [405, 405, 405, 405, 405, 404], str(out["methods"]))
    codes = [b[0] for b in out["bodies"]]
    check("136: in node, a body that is not JSON, not an object, has no text string, an empty one, or is over 8 KB is refused with a short error",
          codes == [400, 400, 400, 400, 400, 413] and all(isinstance(b[1], str) and 0 < len(b[1]) < 60 for b in out["bodies"])
          and out["after_refusals"] == 1, str(out["bodies"]))
    check("136: in node, 30 notes an hour from one hashed IP and no more, while another IP still gets through",
          out["thirtieth"] == 30 and out["limited"] == [429, 30] and out["other_ip"] == [200, 31], str(out["limited"]))
    check("136: in node, the notes need the bearer token in the header: none, a wrong one, one in the address or no Bearer are all 401",
          out["auth"] == [401, 401, 401, 401] and out["no_token"] == 401, str(out["auth"]))
    check("136: in node, with the token the newest 200 come back newest first, and never the hash",
          out["list"][0] == 200 and out["list"][1] == 31 and out["list"][2] == 31
          and out["list"][3] == ["id", "at", "text", "contact", "version", "platform", "screen", "agent"], str(out["list"]))
    check("136: in node, ?format=html is a plain page in the app's faces with every note escaped and no script",
          out["html"][0] == 200 and out["html"][1].startswith("text/html") and out["html"][2] is True
          and out["html"][3] is False and "default-src 'none'" in (out["html"][4] or "") and out["html"][5] is True, str(out["html"]))
    check("136: in node, a collector with no salt stores nothing, and no answer anywhere allows another origin",
          out["no_salt"] == [500, 0] and out["cors"] == [], str(out["no_salt"]))

    # notes.sh against a stand-in for wrangler, which never reaches the network
    shell = shutil.which("sh")
    if not shell:
        return skip("136: notes.sh with a stand-in for wrangler", "no sh on this machine")
    bin_dir = scratch / "feedback-bin"
    bin_dir.mkdir(exist_ok=True)
    fake_wrangler = bin_dir / "wrangler"
    fake_wrangler.write_text(
        "#!/bin/sh\n"
        "echo \"$*\" >> \"$(dirname \"$0\")/asked.txt\"\n"
        "case \"$*\" in\n"
        "  *--json*) printf '%s\\n' '[{\"results\":[{\"id\":2,\"at\":\"2026-10-03T17:00:00.000Z\",\"text\":\"Two lines\\nwith a | pipe\","
        "\"contact\":\"\",\"version\":\"0.9.0\",\"platform\":\"macOS 26.5, darwin\",\"screen\":\"pets\",\"agent\":\"UA\"}],\"success\":true}]' ;;\n"
        "  *) echo 'a table' ;;\n"
        "esac\n", encoding="utf-8")
    fake_wrangler.chmod(0o755)
    env = dict(os.environ, PATH=f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    syntax = subprocess.run([shell, "-n", str(folder / "notes.sh")], capture_output=True, text=True, encoding="utf-8")
    table = subprocess.run([shell, str(folder / "notes.sh"), "--since", "7"], capture_output=True, text=True, encoding="utf-8", env=env)
    target = scratch / "feedback-notes.md"
    md = subprocess.run([shell, str(folder / "notes.sh"), "--md", str(target)], capture_output=True, text=True, encoding="utf-8", env=env)
    wrong = subprocess.run([shell, str(folder / "notes.sh"), "--since", "a week"], capture_output=True, text=True, encoding="utf-8", env=env)
    asked = (bin_dir / "asked.txt").read_text(encoding="utf-8") if (bin_dir / "asked.txt").exists() else ""
    written = target.read_text(encoding="utf-8") if target.exists() else ""
    check("136: notes.sh asks wrangler for the newest notes, the last N days with --since, and refuses a --since that is not a number",
          syntax.returncode == 0 and table.returncode == 0 and "a table" in table.stdout
          and "d1 execute idiograph-feedback --remote --command SELECT id, at, screen, version, contact, text FROM notes WHERE at >= strftime('%Y-%m-%dT%H:%M:%fZ', 'now', '-7 days') ORDER BY id DESC LIMIT 200" in asked
          and wrong.returncode == 2, asked[:300])
    check("136: notes.sh --md writes the notes as a Markdown table, a pipe escaped and a line break kept",
          md.returncode == 0 and "| id | at | text | contact | version | platform | screen | agent |" in written
          and "| 2 | 2026-10-03T17:00:00.000Z | Two lines<br>with a \\| pipe |  | 0.9.0 |" in written
          and "ip_hash" not in written, written[:300])
