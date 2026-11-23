"""Area 452: the release email's sender, packaging/updates_mail.py (updates by email, 23 November 2026). It runs
on the maintainer's Mac against the updates Worker and Amazon SES; here it runs against a fake of each on this
computer (ports 8800 to 8819) and a stand-in for macOS's `security`, which hands it made-up keys.

What matters: it stops, naming the missing keys, before it asks anything of either service; a dry run reads and
never writes or sends; `--send` first deletes from the list every address SES has suppressed, then sends one
email each, signed with SigV4, from hello@idiograph.app in configuration set idiograph, each with its own
unsubscribe link in the body and in the List-Unsubscribe and List-Unsubscribe-Post headers, paced by the
account's MaxSendRate, a throttled one tried again; `--only` sends to one confirmed address and refuses any
other; more than today's quota sends nothing; and no address is ever printed. Its signing gives AWS's published
vectors. Since the Fable review of 23 November: it reaches the real addresses when nothing points it elsewhere
(the SES class once hid the SES address and every real run failed); `--only` skips the sweep; a full send needs
production access, and a Max24HourSend of -1 is no limit; a network failure mid-run is counted and the run goes
on, and a second run of the same subject sends only to those not reached, from a record of row ids outside the
repository; and a redirect is never followed, so the admin token goes nowhere else. The runs through the stand-in
for `security` skip on Windows, where the script is never run."""
from __future__ import annotations

import http.server
import importlib.util
import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

from . import support
from .support import check, skip

ADMIN = "made-up-admin-value-0123456789"
KEY_ID = "AKIDMADEUPFORTESTS"
SECRET = "made-up-aws-secret-for-the-suite"
LIST = ["one@example.com", "Two@Example.org", "three@example.net", "bounced@example.com"]
SUPPRESSED = ["BOUNCED@example.com", "elsewhere@example.org"]


def load():
    path = support.TOOL / "packaging" / "updates_mail.py"
    spec = importlib.util.spec_from_file_location("updates_mail", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ports(n: int) -> list[int]:
    """The first n free ports of 8800 to 8819."""
    found = []
    for port in range(8800, 8820):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                continue
        found.append(port)
        if len(found) == n:
            return found
    return found


class Fakes:
    """The updates Worker's admin routes and the four SES calls the script makes, with what each was asked."""

    def __init__(self, um, worker_port: int, ses_port: int):
        self.um = um
        self.lock = threading.Lock()
        self.reset()
        fakes = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def answer(self, status, data, kind=""):
                raw = json.dumps(data).encode("utf-8")
                self.send_response(status)
                self.send_header("content-type", "application/json")
                if kind:
                    self.send_header("x-amzn-ErrorType", kind)
                self.send_header("content-length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def body(self):
                return self.rfile.read(int(self.headers.get("content-length") or 0))

            def do_GET(self):
                fakes.route(self, "GET", b"")

            def do_POST(self):
                fakes.route(self, "POST", self.body())

        self.servers = [http.server.ThreadingHTTPServer(("127.0.0.1", p), Handler) for p in (worker_port, ses_port)]
        self.worker_port, self.ses_port = worker_port, ses_port
        for s in self.servers:
            threading.Thread(target=s.serve_forever, daemon=True).start()

    def reset(self, rate=4.0, quota=200, throttle_once=True, production=True, drop=None, redirect=False):
        with self.lock:
            self.list = {e.lower(): f"https://idiograph.app/api/updates/unsubscribe?t={i + 1}.{'ab' * 32}" for i, e in enumerate(LIST)}
            self.asked, self.sent, self.deleted, self.bad_sig, self.stolen = [], [], [], 0, []
            self.rate, self.quota, self.throttle = rate, quota, throttle_once
            self.production, self.drop, self.redirect = production, drop, redirect

    def stop(self):
        for s in self.servers:
            s.shutdown()
            s.server_close()

    def signed(self, handler, method, body) -> bool:
        """Recomputes the signature from the request as it came, with the same date."""
        auth = handler.headers.get("authorization", "")
        names = auth.split("SignedHeaders=")[1].split(",")[0].split(";") if "SignedHeaders=" in auth else []
        headers = {n: handler.headers.get(n, "") for n in names if n not in ("host", "x-amz-date")}
        url = f"http://{handler.headers.get('host')}{handler.path}"
        again = self.um.sign_v4(method, url, headers, body, KEY_ID, SECRET, "eu-west-2", "ses", handler.headers.get("x-amz-date"))
        return bool(auth) and again["headers"]["authorization"] == auth

    def route(self, handler, method, body):
        port = handler.server.server_address[1]
        path = handler.path
        with self.lock:
            self.asked.append((port == self.worker_port and "worker" or "ses", method, path.split("?")[0]))
        if path.startswith("/elsewhere"):
            with self.lock:
                self.stolen.append(handler.headers.get("authorization", ""))
            return handler.answer(200, {"ok": True, "recipients": []})
        if port == self.worker_port:
            if self.redirect:
                handler.send_response(302)
                handler.send_header("location", f"http://127.0.0.1:{self.ses_port}/elsewhere{path}")
                handler.send_header("content-length", "0")
                handler.end_headers()
                return None
            if handler.headers.get("authorization") != f"Bearer {ADMIN}":
                return handler.answer(401, {"ok": False, "error": "token"})
            if method == "GET" and path == "/api/updates/admin/recipients":
                return handler.answer(200, {"ok": True, "recipients": [{"email": e, "unsubscribe": u} for e, u in self.list.items()]})
            if method == "POST" and path == "/api/updates/admin/delete":
                emails = json.loads(body.decode("utf-8"))["emails"]
                with self.lock:
                    self.deleted.extend(emails)
                    gone = [e for e in emails if self.list.pop(e.lower(), None)]
                return handler.answer(200, {"ok": True, "deleted": len(gone)})
            return handler.answer(404, {"ok": False, "error": "path"})
        if not self.signed(handler, method, body):
            with self.lock:
                self.bad_sig += 1
            return handler.answer(403, {"message": "signature"}, "SignatureDoesNotMatchException")
        if method == "GET" and path == "/v2/email/account":
            return handler.answer(200, {"SendQuota": {"Max24HourSend": self.quota, "MaxSendRate": self.rate, "SentLast24Hours": 1},
                                        "SendingEnabled": True, "ProductionAccessEnabled": self.production})
        if method == "GET" and path.startswith("/v2/email/suppression/addresses"):
            if "NextToken=page%2F2%2B%3D" in path:
                return handler.answer(200, {"SuppressedDestinationSummaries": [{"EmailAddress": SUPPRESSED[1], "Reason": "COMPLAINT"}]})
            return handler.answer(200, {"SuppressedDestinationSummaries": [{"EmailAddress": SUPPRESSED[0], "Reason": "BOUNCE"}],
                                        "NextToken": "page/2+="})
        if method == "POST" and path == "/v2/email/outbound-emails":
            sent = json.loads(body.decode("utf-8"))
            if self.drop and sent["Destination"]["ToAddresses"] == [self.drop]:
                handler.close_connection = True  # the network fails: no answer at all
                return None
            with self.lock:
                if self.throttle:
                    self.throttle = False
                    return handler.answer(429, {"message": "Maximum sending rate exceeded for " + sent["Destination"]["ToAddresses"][0]},
                                          "TooManyRequestsException")
                self.sent.append((time.monotonic(), sent))
            return handler.answer(200, {"MessageId": "made-up"})
        return handler.answer(404, {"message": "no such call"})


def test_updates_mail(scratch):
    print("\n452. Updates by email: the release email's sender against a fake Worker and a fake SES")
    um = load()
    vectors = json.loads(support.source("updates-worker/test/sigv4_vectors.json").read_text(encoding="utf-8"))
    signed = [um.sign_v4(v["method"], v["url"], v["headers"], v["body"].encode("utf-8"), vectors["access_key_id"],
                         vectors["secret_access_key"], vectors["region"], vectors["service"], v["amz_date"]) for v in vectors["vectors"]]
    check("452: its SigV4 gives AWS's canonical request, string to sign and signature for each published vector",
          len(signed) >= 7 and all(s["canonical"] == v["canonical"] and s["string_to_sign"] == v["string_to_sign"]
                                   and s["signature"] == v["signature"] for s, v in zip(signed, vectors["vectors"])),
          str([v["name"] for s, v in zip(signed, vectors["vectors"]) if s["signature"] != v["signature"]]))

    text, page = um.render("Idiograph 1.0 is out", "# New\n\nThe **PETs** board is faster.\n\n- One\n- [Two](https://idiograph.app/x?a=1&b=2)\n\n<script>x</script>",
                           "https://idiograph.app/api/updates/unsubscribe?t=7.ab")
    check("452: the email's text and HTML carry the opening, the words, the download link, the sign-off, why it came and the "
          "person's own link to stop, and the HTML escapes the words",
          text.startswith("Hello,\n\n" + um.OPENING) and "The PETs board is faster." in text and "Two (https://idiograph.app/x?a=1&b=2)" in text
          and "https://idiograph.app/download.html" in text and um.SIGN_OFF in text
          and "\n-- \n" + um.WHY + "\nStop these emails: https://idiograph.app/api/updates/unsubscribe?t=7.ab\n" in text
          and "<strong>PETs</strong>" in page and 'href="https://idiograph.app/x?a=1&amp;b=2"' in page and "<li" in page
          and "&lt;script&gt;" in page and "<script>" not in page
          and 'href="https://idiograph.app/api/updates/unsubscribe?t=7.ab"' in page and ">Stop these emails</a>" in page, text)
    t2, p2 = um.render("S", "## A *quiet* heading\n\n* **One** with *stress*\n* Two\n\nSome *italic* words and 2 * 3 * 4.", "https://idiograph.app/u")
    check("452: the plain text has no # on a heading and no * or ** around a word, the HTML makes *word* emphasis, and the footer rule is '-- ' with its space",
          "A quiet heading" in t2 and "#" not in t2 and "**" not in t2 and "*italic*" not in t2 and "Some italic words and 2 * 3 * 4." in t2
          and "<em>italic</em>" in p2 and "<em>quiet</em>" in p2 and "<strong>One</strong>" in p2 and "2 * 3 * 4" in p2
          and "\n-- \n" in t2 and "\n--\n" not in t2, t2)
    _, p3 = um.render("S", "- First **thing**\n- Second [link](https://idiograph.app/x)\n\nMore.", "https://idiograph.app/u")
    _, p4 = um.render("S", "## The *big* news\n\nMore.", "https://idiograph.app/u")
    pre = lambda h: __import__("re").search(r'mso-hide:all[^>]*>([^<]*)</div>', h).group(1)
    check("452: the preheader is the first block with the bullet taken off every line, the # off a heading and no * left",
          pre(p3) == "First thing Second link" and pre(p4) == "The big news" and "*" not in pre(p3) + pre(p4), pre(p3) + "|" + pre(p4))
    check("452: Outlook gets a 600 table around the card, padding in the button's cell, and the lockup's alt text has a style",
          "<!--[if mso]><table" in page and "<![endif]-->" in page and 'width="600" align="center"' in page
          and "mso-padding-alt:14px 28px" in page and 'alt="Idiograph" style="font-family:' in page and "font-size:22px;color:#1F1B16" in page, "")
    words = " ".join([um.OPENING, um.SIGN_OFF, um.WHY, um.DOWNLOAD[0]])
    check("452: the release email's own words have no semicolon, no exclamation mark and no name under the sign-off",
          not any(c in words for c in ";!") and "Adam" not in text and "Adam" not in page, words)
    loads = __import__("re").findall(r"\bsrc=\"([^\"]+)\"", page)
    check("452: the release email loads the two lockup PNGs from idiograph.app/email and nothing else, with the dark-mode tags",
          loads == ["https://idiograph.app/email/idiograph-lockup-2x.png", "https://idiograph.app/email/idiograph-lockup-dark-2x.png"]
          and '<meta name="color-scheme" content="light dark">' in page and "@media (prefers-color-scheme: dark)" in page
          and "max-width:600px" in page, str(loads))
    root = Path(um.__file__).resolve().parent.parent
    pngs = [root / "site" / "holding" / "email" / n for n in ("idiograph-lockup-2x.png", "idiograph-lockup-dark-2x.png")]
    sizes = [(int.from_bytes(p.read_bytes()[16:20], "big"), int.from_bytes(p.read_bytes()[20:24], "big")) if p.is_file() else None for p in pngs]
    check("452: the lockup's two PNGs are in the site at twice the size the emails show them",
          sizes == [(2 * um.LOCKUP_WIDTH, 2 * um.LOCKUP_HEIGHT)] * 2, str(sizes))
    at = sorted(str(f.relative_to(root)) for f in (root / "site" / "holding").rglob("*") if "@" in f.name)
    check("452: no file under site/holding has an @ in its name, which an email client fetches literally and the site answers 404", not at, str(at))
    node = __import__("shutil").which("node")
    if not node:
        skip("452: the Worker's email shape and the script's are the same", "no node on this machine")
    else:
        args = ["A title & 'more'", "The line <after> the subject", "<p>Some words</p>", "<p>Why it came</p>"]
        worker = (root / "updates-worker" / "worker.js").as_uri()
        js = (f"const m = await import({json.dumps(worker)}); const a = {json.dumps(args)};"
              "process.stdout.write(JSON.stringify([m.emailShell(...a), m.textShell('Words\\n\\nmore', 'Why'),"
              " m.LOCKUP_WIDTH, m.LOCKUP_HEIGHT, m.EMAIL_STYLE, m.confirmationEmail('https://example.org/c?t=1')]));")
        done = subprocess.run([node, "--input-type=module", "-e", js], capture_output=True, text=True, encoding="utf-8", timeout=60)
        try:
            theirs = json.loads(done.stdout)
        except ValueError:
            theirs = None
        ours = [um.shell(*args), um.text_shell("Words\n\nmore", "Why"), um.LOCKUP_WIDTH, um.LOCKUP_HEIGHT, um.EMAIL_STYLE]
        conf = (theirs or [None] * 6)[5] or {}
        check("452: the confirmation's opening line is an h1 with the inline styles, its button cell has the Outlook padding and its text ends in the '-- ' rule",
              "<h1 class=\"lead ink\"" in conf.get("html", "") and "font-weight:400" in conf.get("html", "")
              and "mso-padding-alt:14px 28px" in conf.get("html", "") and "\n-- \n" in conf.get("text", ""), str(conf)[:200])
        theirs = theirs[:5] if theirs else theirs
        check("452: the Worker's email shape (emailShell, textShell, the lockup's size and the styles) and the script's "
              "(shell, text_shell) give the same bytes for the same words",
              theirs == ours, done.stderr[-300:] or str([i for i, (a, b) in enumerate(zip(theirs or [], ours)) if a != b]))

    saved = {k: os.environ.pop(k) for k in ("IDIOGRAPH_SES_URL", "IDIOGRAPH_UPDATES_URL") if k in os.environ}
    try:
        real = [um.SES({"access_key_id": "x", "secret_access_key": "y"}).base, um.Worker("z").base]
    except Exception as exc:  # noqa: BLE001 - the check names what broke
        real = [f"{type(exc).__name__}: {exc}"]
    finally:
        os.environ.update(saved)
    check("452: with nothing pointing it elsewhere it talks to SES in eu-west-2 and to the Worker on idiograph.app",
          real == ["https://email.eu-west-2.amazonaws.com", "https://idiograph.app/api/updates"], str(real))
    check("452: an admin delete is sent as many addresses as the Worker takes at once",
          um.DELETE_BATCH == 1000, str(um.DELETE_BATCH))

    now, slept = [0.0], []
    pace = um.Pace(4, clock=lambda: now[0], sleep=lambda s: (slept.append(round(s, 3)), now.__setitem__(0, now[0] + s)))
    for step in (0.0, 0.1, 0.3, 0.0):
        now[0] += step
        pace.wait()
    check("452: the pace keeps a quarter of a second between emails at 4 a second, and waits no more than it must",
          slept == [0.15, 0.25], str(slept))

    if os.name == "nt":
        return skip("452: the sender against the fakes", "the script runs on the maintainer's Mac alone")
    free = ports(2)
    if len(free) < 2:
        return skip("452: the sender against the fakes", "no two free ports in 8800 to 8819")
    fakes = Fakes(um, *free)
    bin_dir = scratch / "updates-mail-bin"
    keys = bin_dir / "keys"
    keys.mkdir(parents=True, exist_ok=True)
    security = bin_dir / "security"
    security.write_text(
        "#!/bin/sh\n"
        "echo \"$*\" >> \"$(dirname \"$0\")/asked.txt\"\n"
        "name=''\n"
        "while [ $# -gt 0 ]; do case \"$1\" in -s) name=\"$2\"; shift ;; esac; shift; done\n"
        "f=\"$(dirname \"$0\")/keys/$name\"\n"
        "if [ -f \"$f\" ]; then cat \"$f\"; exit 0; fi\n"
        "echo 'security: The specified item could not be found in the keychain.' >&2\n"
        "exit 44\n", encoding="utf-8", newline="\n")
    security.chmod(0o755)
    body = scratch / "updates-mail-body.md"
    body.write_text("Idiograph 1.0 is out.\n\n- The PETs board is faster.\n", encoding="utf-8", newline="\n")
    home = scratch / "updates-mail-home"
    state = home / "Library" / "Application Support" / "Idiograph" / "updates-mail"
    env = dict(os.environ, HOME=str(home), PATH=str(bin_dir) + os.pathsep + os.environ.get("PATH", ""),
               IDIOGRAPH_UPDATES_URL=f"http://127.0.0.1:{free[0]}/api/updates", IDIOGRAPH_SES_URL=f"http://127.0.0.1:{free[1]}",
               PYTHONIOENCODING="utf-8")
    script = str(support.TOOL / "packaging" / "updates_mail.py")
    said = []

    def forget():
        for f in state.glob("*") if state.is_dir() else []:
            f.unlink()

    def run(*extra):
        done = subprocess.run([sys.executable, script, "--subject", "Idiograph 1.0 is out", "--body", str(body), *extra],
                              capture_output=True, text=True, encoding="utf-8", env=env, timeout=120)
        said.append(done.stdout + done.stderr)
        return done

    try:
        (keys / "idiograph-ses-mac-access-key-id").write_text(KEY_ID, encoding="utf-8", newline="\n")
        done = run("--send")
        check("452: with keys missing from the Keychain it stops, naming each missing one, before asking either service",
              done.returncode == 2 and "idiograph-ses-mac-secret-access-key" in done.stderr and "idiograph-updates-admin-token" in done.stderr
              and "idiograph-ses-mac-access-key-id" not in done.stderr and fakes.asked == [] and KEY_ID not in done.stdout + done.stderr,
              done.stderr[-300:])
        asked = (bin_dir / "asked.txt").read_text(encoding="utf-8")
        check("452: each key is read from the Keychain's account claude-code with -w, never printed",
              asked.count("find-generic-password") == 3 and all("-a claude-code -w" in line for line in asked.splitlines()), asked)
        (keys / "idiograph-ses-mac-secret-access-key").write_text(SECRET, encoding="utf-8", newline="\n")
        (keys / "idiograph-updates-admin-token").write_text(ADMIN, encoding="utf-8", newline="\n")

        done = run()
        check("452: a dry run reads the list, both pages of the suppression list and the account, and sends or deletes nothing",
              done.returncode == 0 and fakes.sent == [] and fakes.deleted == [] and len(fakes.list) == 4
              and "On the list: 4 confirmed. Suppressed at SES: 2, of them on the list: 1." in done.stdout
              and "Dry run: 3 emails would go. Nothing was sent or changed." in done.stdout
              and sorted(a for a in fakes.asked) == sorted([("worker", "GET", "/api/updates/admin/recipients"),
                                                             ("ses", "GET", "/v2/email/suppression/addresses"),
                                                             ("ses", "GET", "/v2/email/suppression/addresses"),
                                                             ("ses", "GET", "/v2/email/account")])
              and fakes.bad_sig == 0, done.stdout + done.stderr[-300:])
        check("452: a dry run shows the email as text, with a stand-in for the link", "The PETs board is faster." in done.stdout
              and "<your own unsubscribe link>" in done.stdout, done.stdout[-300:])

        fakes.reset(throttle_once=False)
        done = run("--send", "--only", "nobody@example.com")
        check("452: --only refuses an address that is not confirmed, and sends nothing",
              done.returncode == 1 and fakes.sent == [] and "not a confirmed address" in done.stderr, done.stderr[-300:])
        fakes.reset(throttle_once=False)
        done = run("--send", "--only", "  TWO@example.org ")
        check("452: --only sends one email to that confirmed address alone, skips the sweep, and keeps no record",
              done.returncode == 0 and [s["Destination"]["ToAddresses"] for _, s in fakes.sent] == [["two@example.org"]]
              and fakes.deleted == [] and "Sent 1 of 1." in done.stdout and not any(state.glob("*.json")),
              done.stdout + done.stderr[-300:])
        fakes.reset(throttle_once=False, production=False)
        done = run("--send")
        refused = (done.returncode, list(fakes.sent), list(fakes.deleted), done.stderr)
        fakes.reset(throttle_once=False, production=False)
        done = run("--send", "--only", "two@example.org")
        check("452: without production access a full send sends nothing, and --only to one address still goes",
              refused[0] == 1 and refused[1] == [] and "production access" in refused[3] and "Nothing was sent." in refused[3]
              and done.returncode == 0 and len(fakes.sent) == 1, refused[3][-300:] + done.stdout[-200:])

        fakes.reset(rate=4.0, throttle_once=True)
        done = run("--send")
        sent = [s for _, s in fakes.sent]
        to = [s["Destination"]["ToAddresses"] for s in sent]
        check("452: --send first deletes from the list the addresses SES has suppressed that are on it, then sends to the rest",
              done.returncode == 0 and fakes.deleted == ["bounced@example.com"] and "bounced@example.com" not in fakes.list
              and to == [["one@example.com"], ["two@example.org"], ["three@example.net"]]
              and "Removed from the list: 1." in done.stdout and "Sent 3 of 3." in done.stdout, done.stdout + done.stderr[-300:])
        first_seen = [a for a in fakes.asked if a[1] == "POST"]
        check("452: the sweep comes before the first email",
              first_seen and first_seen[0] == ("worker", "POST", "/api/updates/admin/delete"), str(first_seen[:2]))
        links = {e.lower(): f"https://idiograph.app/api/updates/unsubscribe?t={i + 1}.{'ab' * 32}" for i, e in enumerate(LIST)}
        heads = [{h["Name"]: h["Value"] for h in s["Content"]["Simple"]["Headers"]} for s in sent]
        check("452: each email carries its own List-Unsubscribe link and List-Unsubscribe-Post: List-Unsubscribe=One-Click",
              all(h == {"List-Unsubscribe": f"<{links[t[0]]}>", "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"} for h, t in zip(heads, to))
              and len({h["List-Unsubscribe"] for h in heads}) == 3, json.dumps(heads)[:400])
        check("452: each email is from Idiograph <hello@idiograph.app> in configuration set idiograph, with text and HTML, "
              "its own link in both",
              all(s["FromEmailAddress"] == "Idiograph <hello@idiograph.app>" and s["ConfigurationSetName"] == "idiograph"
                  and s["Content"]["Simple"]["Subject"]["Data"] == "Idiograph 1.0 is out"
                  and links[t[0]] in s["Content"]["Simple"]["Body"]["Text"]["Data"]
                  and links[t[0]] in s["Content"]["Simple"]["Body"]["Html"]["Data"] for s, t in zip(sent, to)), json.dumps(sent[:1])[:400])
        check("452: every call to SES is signed with SigV4 for eu-west-2 and ses, and the fake's own signature matches",
              fakes.bad_sig == 0, str(fakes.bad_sig))
        times = [t for t, _ in fakes.sent]
        gaps = [round(b - a, 3) for a, b in zip(times, times[1:])]
        check("452: the emails are paced by MaxSendRate (4 a second, a quarter of a second apart), a throttled one tried again",
              len(gaps) == 2 and all(g >= 0.2 for g in gaps) and len(sent) == 3, str(gaps))

        record = list(state.glob("*.json"))
        kept = record[0].read_text(encoding="utf-8") if record else ""
        check("452: the run's record of who was sent this subject is outside the repository and holds row ids, no address",
              len(record) == 1 and json.loads(kept) == {"sent": ["1", "2", "3"]} and "@" not in kept, kept)
        fakes.reset(throttle_once=False)
        done = run("--send")
        check("452: the same subject run again sends nothing more", done.returncode == 0 and fakes.sent == []
              and "Already sent this subject: 3." in done.stdout and "Sent 0 of 0." in done.stdout, done.stdout[-300:])

        forget()
        fakes.reset(quota=3, throttle_once=False)
        done = run("--send")
        check("452: more emails than SES allows today sends none", done.returncode == 1 and fakes.sent == []
              and "Nothing was sent." in done.stderr, done.stderr[-300:])
        fakes.reset(quota=-1, throttle_once=False)
        done = run("--send")
        check("452: a Max24HourSend of -1 is no daily limit", done.returncode == 0 and len(fakes.sent) == 3
              and "no daily limit" in done.stdout, done.stdout[-300:] + done.stderr[-300:])

        forget()
        fakes.reset(throttle_once=False, drop="two@example.org")
        done = run("--send")
        first_go = (done.returncode, [s["Destination"]["ToAddresses"][0] for _, s in fakes.sent], done.stdout)
        fakes.reset(throttle_once=False)
        done = run("--send")
        check("452: a network failure mid-run is counted and the run goes on; the same subject again sends only to the one missed",
              first_go[0] == 1 and first_go[1] == ["one@example.com", "three@example.net"]
              and "Sent 2 of 3, 1 failed: unreachable." in first_go[2] and "Run the same subject again" in first_go[2]
              and done.returncode == 0 and [s["Destination"]["ToAddresses"] for _, s in fakes.sent] == [["two@example.org"]]
              and "Already sent this subject: 2." in done.stdout and "Sent 1 of 1." in done.stdout, first_go[2][-300:] + done.stdout[-300:])

        fakes.reset(throttle_once=False, redirect=True)
        done = run("--send")
        check("452: a redirect from the Worker is not followed, so the admin token goes nowhere else, and nothing is sent",
              done.returncode == 1 and fakes.stolen == [] and fakes.sent == [] and "302" in done.stderr, done.stderr[-300:])

        everything = "\n".join(said)
        named = [e for e in LIST + SUPPRESSED + ["nobody@example.com"] if e.lower() in everything.lower()]
        check("452: no run printed an address, a key or the admin token, only counts",
              not named and "@" not in everything.replace("hello@idiograph.app", "") and SECRET not in everything
              and ADMIN not in everything, str(named))
    finally:
        fakes.stop()
