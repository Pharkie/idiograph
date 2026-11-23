"""The release email: one email to each confirmed address on Idiograph's updates list, run on the
maintainer's Mac (updates by email, 23 November 2026). See updates-worker/README.md, How the send works.

    .venv/bin/python packaging/updates_mail.py --subject "Idiograph 0.9.37 is out" --body email.md
    .venv/bin/python packaging/updates_mail.py --subject ... --body email.md --send --only <address>
    .venv/bin/python packaging/updates_mail.py --subject ... --body email.md --send

It is a dry run unless `--send` is given: it reads the list, the suppression list and the account's
limits, says how many emails would go and shows the email as text, and changes nothing. With `--send`:

1. the sweep: every address on SES's account-level suppression list (hard bounces and complaints,
   ListSuppressedDestinations) is deleted from the list through the Worker's admin delete;
2. the confirmed addresses come from the Worker's admin recipients route, each with its own
   unsubscribe link;
3. one email each goes through SES v2's SendEmail, from Idiograph <hello@idiograph.app> in
   configuration set `idiograph`, with the List-Unsubscribe and List-Unsubscribe-Post (RFC 8058)
   headers as custom headers, paced by GetAccount's MaxSendRate.

`--only <address>` sends to that address alone, and only if it is already confirmed: a test to the
maintainer before the real send. It skips the sweep, and it neither reads nor adds to the record below.

A full send needs SES's production access; until it is granted only `--only` to a verified address
can go. A call that fails, SES's refusal or the network's, is counted as failed and the run carries on
(five in a row stop it), and the counts are always printed. Each email that went is recorded by its
row's id (the number in its unsubscribe link, never the address) in a file per subject under
~/Library/Application Support/Idiograph/updates-mail/, so running the same subject again sends only
to those it has not reached.

The keys are read from the Keychain (account `claude-code`): idiograph-ses-mac-access-key-id,
idiograph-ses-mac-secret-access-key and idiograph-updates-admin-token. It stops, naming the missing
ones, when any is not there. It never prints or writes an address, nor anything SES says that could
hold one: counts only. Signing is AWS Signature Version 4 with the standard library.

IDIOGRAPH_UPDATES_URL and IDIOGRAPH_SES_URL point it elsewhere (the suite's fakes); plain http is
taken only for this computer. No redirect is followed, so the admin token goes to no other host.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import hmac
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REGION = "eu-west-2"
WORKER = "https://idiograph.app/api/updates"
SES_URL = f"https://email.{REGION}.amazonaws.com"
FROM = "Idiograph <hello@idiograph.app>"
CONFIGURATION_SET = "idiograph"
ACCOUNT = "claude-code"
KEYS = {
    "access_key_id": "idiograph-ses-mac-access-key-id",
    "secret_access_key": "idiograph-ses-mac-secret-access-key",
    "admin_token": "idiograph-updates-admin-token",
}
DELETE_BATCH = 1000  # addresses one admin delete is sent: the Worker's DELETE_MAX, in ten statements of 100
RETRIES = 3          # tries more for an email SES throttles
IN_A_ROW = 5         # failed emails in a row that stop the run
TIMEOUT = 30
STATE = Path.home() / "Library" / "Application Support" / "Idiograph" / "updates-mail"


class Stop(Exception):
    """A reason to stop, said plainly, with the exit code."""

    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.code = code


class Unreachable(Stop):
    """The network failed before an answer came."""


# ── AWS Signature Version 4 (the suite checks it against AWS's published test vectors,
#    updates-worker/test/sigv4_vectors.json)

def _rfc3986(text: str) -> str:
    return urllib.parse.quote(text, safe="-_.~")


def canonical_request(method: str, url: str, headers: dict, body_hash: str) -> tuple[str, str]:
    """The canonical request and the signed headers' names."""
    parts = urllib.parse.urlsplit(url)
    path = "/".join(_rfc3986(urllib.parse.unquote(seg)) for seg in (parts.path or "/").split("/")) or "/"
    pairs = []
    for piece in parts.query.split("&") if parts.query else []:
        key, _, value = piece.partition("=")
        unq = lambda s: urllib.parse.unquote(s.replace("+", "%20"))
        pairs.append((_rfc3986(unq(key)), _rfc3986(unq(value))))
    pairs.sort()
    named = sorted((k.lower(), " ".join(str(v).split())) for k, v in headers.items())
    signed = ";".join(k for k, _ in named)
    text = "\n".join([method, path, "&".join(f"{k}={v}" for k, v in pairs),
                      "".join(f"{k}:{v}\n" for k, v in named), signed, body_hash])
    return text, signed


def _hmac(key: bytes, text: str) -> bytes:
    return hmac.new(key, text.encode("utf-8"), hashlib.sha256).digest()


def sign_v4(method: str, url: str, headers: dict, body: bytes, access_key_id: str, secret_access_key: str,
            region: str, service: str, amz_date: str | None = None) -> dict:
    """The headers to send (those given, with host and x-amz-date, and Authorization over them), and the
    canonical request, string to sign and signature."""
    when = amz_date or datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    day = when[:8]
    host = urllib.parse.urlsplit(url).netloc
    every = dict(headers, host=host, **{"x-amz-date": when})
    text, signed = canonical_request(method, url, every, hashlib.sha256(body).hexdigest())
    scope = f"{day}/{region}/{service}/aws4_request"
    to_sign = "\n".join(["AWS4-HMAC-SHA256", when, scope, hashlib.sha256(text.encode("utf-8")).hexdigest()])
    key = _hmac(f"AWS4{secret_access_key}".encode("utf-8"), day)
    for part in (region, service, "aws4_request"):
        key = _hmac(key, part)
    signature = hmac.new(key, to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    every["authorization"] = (f"AWS4-HMAC-SHA256 Credential={access_key_id}/{scope}, "
                              f"SignedHeaders={signed}, Signature={signature}")
    return {"canonical": text, "string_to_sign": to_sign, "signature": signature, "headers": every}


# ── the keys

def keychain(service: str) -> str | None:
    """One key from the Keychain, or None. The value is never printed."""
    tool = shutil.which("security")
    if not tool:
        return None
    done = subprocess.run([tool, "find-generic-password", "-s", service, "-a", ACCOUNT, "-w"],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT)
    value = done.stdout.strip() if done.returncode == 0 else ""
    return value or None


def read_keys() -> dict:
    keys = {name: keychain(service) for name, service in KEYS.items()}
    missing = [KEYS[name] for name, value in keys.items() if not value]
    if missing:
        raise Stop("These keys are not in the Keychain (account claude-code): " + ", ".join(missing)
                   + ". Add each with: security add-generic-password -a claude-code -s <name> -w", 2)
    return keys


# ── the two services

def _endpoint(name: str, default: str) -> str:
    url = (os.environ.get(name) or default).rstrip("/")
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" and not (parts.scheme == "http" and parts.hostname in ("127.0.0.1", "localhost", "::1")):
        raise Stop(f"{name} must be an https address (plain http only on this computer).", 2)
    return url


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect is answered as the error it is here, never followed: the admin token and the signed
    calls go to the host named and no other."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def _call(method: str, url: str, headers: dict, body: bytes | None) -> tuple[int, dict, str]:
    """(status, the JSON answer or {}, SES's error type or '')."""
    request = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with _OPENER.open(request, timeout=TIMEOUT) as answer:
            raw, status, kind = answer.read(), answer.status, ""
    except urllib.error.HTTPError as exc:
        raw, status, kind = exc.read(), exc.code, exc.headers.get("x-amzn-ErrorType", "")
    except (urllib.error.URLError, OSError) as exc:
        raise Unreachable(f"Could not reach {urllib.parse.urlsplit(url).netloc}: {type(exc).__name__}.") from None
    try:
        data = json.loads(raw.decode("utf-8")) if raw else {}
    except ValueError:
        data = {}
    # only the error's type, never its message, which can name an address
    return status, data if isinstance(data, dict) else {}, kind.split(":")[0]


class Worker:
    def __init__(self, token: str):
        self.base = _endpoint("IDIOGRAPH_UPDATES_URL", WORKER)
        self.token = token

    def _ask(self, method: str, route: str, payload=None) -> dict:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"authorization": f"Bearer {self.token}", "accept": "application/json"}
        if body is not None:
            headers["content-type"] = "application/json"
        status, data, _ = _call(method, f"{self.base}/admin/{route}", headers, body)
        if status != 200 or not data.get("ok"):
            raise Stop(f"The updates Worker answered {status} to admin/{route}.")
        return data

    def recipients(self) -> list[dict]:
        listed = self._ask("GET", "recipients").get("recipients")
        if not isinstance(listed, list):
            raise Stop("The updates Worker's recipients were not a list.")
        return [r for r in listed if isinstance(r, dict) and r.get("email") and r.get("unsubscribe")]

    def delete(self, emails: list[str]) -> int:
        deleted = 0
        for at in range(0, len(emails), DELETE_BATCH):
            deleted += int(self._ask("POST", "delete", {"emails": emails[at:at + DELETE_BATCH]}).get("deleted", 0))
        return deleted


class SES:
    def __init__(self, keys: dict):
        self.base = _endpoint("IDIOGRAPH_SES_URL", SES_URL)
        self.keys = keys

    def call(self, method: str, path: str, payload=None, query: dict | None = None) -> tuple[int, dict, str]:
        url = self.base + path + ("?" + urllib.parse.urlencode(sorted(query.items()), quote_via=urllib.parse.quote) if query else "")
        body = json.dumps(payload).encode("utf-8") if payload is not None else b""
        headers = {"content-type": "application/json"} if payload is not None else {}
        signed = sign_v4(method, url, headers, body, self.keys["access_key_id"], self.keys["secret_access_key"], REGION, "ses")
        sent = {k: v for k, v in signed["headers"].items() if k != "host"}
        return _call(method, url, sent, body if payload is not None else None)

    def account(self) -> dict:
        status, data, kind = self.call("GET", "/v2/email/account")
        if status != 200:
            raise Stop(f"SES GetAccount answered {status} {kind}".rstrip() + ".")
        return data

    def suppressed(self) -> set[str]:
        found, token = set(), None
        while True:
            query = {"PageSize": "1000", **({"NextToken": token} if token else {})}
            status, data, kind = self.call("GET", "/v2/email/suppression/addresses", query=query)
            if status != 200:
                raise Stop(f"SES ListSuppressedDestinations answered {status} {kind}".rstrip() + ".")
            for item in data.get("SuppressedDestinationSummaries") or []:
                if isinstance(item, dict) and item.get("EmailAddress"):
                    found.add(str(item["EmailAddress"]).strip().lower())
            token = data.get("NextToken")
            if not token:
                return found

    def send(self, to: str, subject: str, text: str, html_body: str, unsubscribe: str) -> tuple[int, str]:
        payload = {
            "FromEmailAddress": FROM,
            "Destination": {"ToAddresses": [to]},
            "Content": {"Simple": {
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Text": {"Data": text, "Charset": "UTF-8"}, "Html": {"Data": html_body, "Charset": "UTF-8"}},
                "Headers": [{"Name": "List-Unsubscribe", "Value": f"<{unsubscribe}>"},
                            {"Name": "List-Unsubscribe-Post", "Value": "List-Unsubscribe=One-Click"}],
            }},
            "ConfigurationSetName": CONFIGURATION_SET,
        }
        status, _, kind = self.call("POST", "/v2/email/outbound-emails", payload)
        return status, kind


# ── the email's shape, kept in step with updates-worker/worker.js's `emailShell` and `textShell`, which give the
#    same bytes for the same words (area 452 checks it): tables and inline styles, 600 pixels at most, the site's
#    paper, ink and crux orange, the lockup's two PNGs (packaging/email_lockup.mjs), the dark-mode styles, and no
#    font fetched and nothing counted. The Worker's comment says why each piece is there.

EMAIL_ASSETS = "https://idiograph.app/email"
LOCKUP_WIDTH = 262   # CSS pixels: the PNGs are twice this
LOCKUP_HEIGHT = 96
EMAIL_SANS = "'Avenir Next',Avenir,'Segoe UI',Helvetica,Arial,sans-serif"
EMAIL_SERIF = "'Iowan Old Style',Charter,'Palatino Linotype',Palatino,Georgia,serif"

EMAIL_STYLE = """:root { color-scheme: light dark; supported-color-schemes: light dark; }
body { margin: 0 !important; padding: 0 !important; width: 100% !important; }
table { border-collapse: collapse; }
img { border: 0; outline: none; text-decoration: none; }
.lk-dark { display: none; }
@media (max-width: 480px) {
  .outer { padding: 0 !important; }
  .lead { font-size: 23px !important; }
}
@media (prefers-color-scheme: dark) {
  .bg { background: #16130E !important; }
  .ink { color: #EFE7D9 !important; }
  .soft { color: #B6AC9B !important; }
  .rule { border-color: #3A332A !important; }
  .link { color: #F79646 !important; }
  .btn { background: #F79646 !important; }
  .btn-a { color: #1B1206 !important; }
  .lk-light { display: none !important; }
  .lk-dark { display: block !important; }
}
[data-ogsb] .bg { background: #16130E !important; }
[data-ogsc] .ink { color: #EFE7D9 !important; }
[data-ogsc] .soft { color: #B6AC9B !important; }
[data-ogsc] .link { color: #F79646 !important; }
[data-ogsb] .btn { background: #F79646 !important; }
[data-ogsc] .btn-a { color: #1B1206 !important; }
[data-ogsc] .lk-light { display: none !important; }
[data-ogsc] .lk-dark { display: block !important; }"""


def esc(value) -> str:
    """The Worker's `esc`: & < > " and ' as entities, ' as &#39;."""
    return html.escape(str(value), quote=True).replace("&#x27;", "&#39;")


def shell(title: str, preheader: str, content: str, footer: str) -> str:
    """One email's HTML: the lockup, then `content` (HTML, already escaped), then `footer` (HTML) under a rule."""
    def img(cls: str, file: str, style: str) -> str:
        return (f'<img class="{cls}" src="{EMAIL_ASSETS}/{file}" width="{LOCKUP_WIDTH}" height="{LOCKUP_HEIGHT}" '
                f'alt="Idiograph" style="font-family:{EMAIL_SANS};font-size:22px;color:#1F1B16;{style}">')
    light = img("lk-light", "idiograph-lockup-2x.png", f"display:block;width:{LOCKUP_WIDTH}px;height:auto;")
    dark = img("lk-dark", "idiograph-lockup-dark-2x.png", f"display:none;width:{LOCKUP_WIDTH}px;height:auto;")
    return f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="x-apple-disable-message-reformatting">
<meta name="color-scheme" content="light dark">
<meta name="supported-color-schemes" content="light dark">
<title>{esc(title)}</title>
<style>
{EMAIL_STYLE}
</style>
</head>
<body class="bg" style="margin:0;padding:0;background:#FBF7EF;">
<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;font-size:1px;line-height:1px;color:#FBF7EF;">{esc(preheader)}</div>
<table role="presentation" class="bg" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#FBF7EF;">
<tr><td class="outer" align="center" style="padding:16px 12px;">
<!--[if mso]><table role="presentation" width="600" align="center" cellpadding="0" cellspacing="0" border="0"><tr><td><![endif]-->
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;">
<tr><td style="padding:9px 5px 32px 5px;">
<a href="https://idiograph.app" style="text-decoration:none;">{light}<!--[if !mso]><!-->{dark}<!--<![endif]--></a>
</td></tr>
<tr><td class="ink" style="padding:0 36px;font-family:{EMAIL_SANS};font-size:17px;line-height:1.6;color:#1F1B16;">
{content}
</td></tr>
<tr><td style="padding:12px 36px 40px 36px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td class="rule soft" style="border-top:1px solid #E4DCCD;padding-top:20px;font-family:{EMAIL_SANS};font-size:14px;line-height:1.55;color:#554C41;">
{footer}
<p style="margin:12px 0 0;"><a class="soft" href="https://idiograph.app" style="color:#554C41;">idiograph.app</a></p>
</td></tr></table>
</td></tr>
</table>
<!--[if mso]></td></tr></table><![endif]-->
</td></tr>
</table>
</body>
</html>
"""


def text_shell(content: str, footer: str) -> str:
    """One email's plain text: the words, then the footer under a rule."""
    return f"{content.strip()}\n\n-- \n{footer.strip()}\nhttps://idiograph.app\n"


# The words around the release's own text, which Adam approves each time: his opening and sign-off, the
# download button, and the footer with the person's own link to stop. The email ends at the sign-off, with no
# name under it (the From says Idiograph, and Adam's emails never end with his name).
GREETING = "Hello,"
OPENING = "I have just released a new version of Idiograph, and I wanted to tell you what is in it."
DOWNLOAD = ("Download the new version", "https://idiograph.app/download.html")
SIGN_OFF = ("Thank you for using Idiograph. If anything gets in your way, or you would like to tell me how you use it, "
            "reply to this email. It comes straight to me.")
WHY = "You are getting this email because you signed up for news of Idiograph."
STOP = "Stop these emails"

LINK = re.compile(r"\[([^\]]+)\]\(((?:https?://|mailto:)[^)\s]+)\)")
BOLD = re.compile(r"\*\*(.+?)\*\*")
EMPH = re.compile(r"(?<![*\w])\*(?![*\s])(.+?)(?<![*\s])\*(?![*\w])")
HEADING = re.compile(r"^#{1,6}[ \t]+", re.MULTILINE)
BULLET = re.compile(r"^[ \t]*[-*] ", re.MULTILINE)


def _marked(text: str) -> str:
    """Text escaped, with **bold** and *emphasis* as strong and em."""
    return EMPH.sub(r"<em>\1</em>", BOLD.sub(r"<strong>\1</strong>", html.escape(text, quote=False)))


def _plain(text: str) -> str:
    """The plain text of Markdown: no # on headings, no ** or * around a word, a link as `words (address)`."""
    return LINK.sub(r"\1 (\2)", EMPH.sub(r"\1", BOLD.sub(r"\1", HEADING.sub("", text))))


def _inline(text: str) -> str:
    out, at = [], 0
    for m in LINK.finditer(text):
        out.append(_marked(text[at:m.start()]))
        out.append(f'<a class="link" href="{esc(m.group(2))}" style="color:#B04E00;">{html.escape(m.group(1), quote=False)}</a>')
        at = m.end()
    out.append(_marked(text[at:]))
    return "".join(out)


def render(subject: str, markdown: str, unsubscribe: str) -> tuple[str, str]:
    """(plain text, HTML) of one email: Adam's opening, the release's words, the download button, his sign-off,
    then why it came and the person's own link to stop."""
    blocks = [b.strip("\n") for b in re.split(r"\n\s*\n", markdown.replace("\r\n", "\n").strip()) if b.strip()]
    words = "\n\n".join(_plain(b) for b in blocks)
    text = text_shell(f"{GREETING}\n\n{OPENING}\n\n{words}\n\n{DOWNLOAD[0]}: {DOWNLOAD[1]}\n\n{SIGN_OFF}",
                      f"{WHY}\n{STOP}: {unsubscribe}")
    parts = [f'<p style="margin:0 0 20px;">{esc(GREETING)}</p>', f'<p style="margin:0 0 20px;">{esc(OPENING)}</p>']
    for block in blocks:
        lines = block.split("\n")
        if all(BULLET.match(line) for line in lines):
            items = "".join('<li style="margin:0 0 10px;">' + _inline(BULLET.sub("", line)) + "</li>" for line in lines)
            parts.append(f'<ul style="margin:0 0 20px;padding-left:22px;">{items}</ul>')
        elif re.match(r"#{1,3} ", block):
            parts.append(f'<h2 class="ink" style="font-family:{EMAIL_SERIF};font-weight:400;font-size:23px;line-height:1.3;'
                         f'color:#1F1B16;margin:28px 0 12px;">{_inline(block.lstrip("#").strip())}</h2>')
        else:
            parts.append(f'<p style="margin:0 0 20px;">{_inline(" ".join(line.strip() for line in lines))}</p>')
    parts.append('<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:8px 0 28px;"><tr>'
                 '<td class="btn" bgcolor="#B04E00" style="border-radius:8px;background:#B04E00;mso-padding-alt:14px 28px;">'
                 f'<a class="btn-a" href="{esc(DOWNLOAD[1])}" style="display:inline-block;padding:14px 28px;font-family:{EMAIL_SANS};'
                 'font-size:17px;font-weight:600;line-height:1.2;color:#FFFFFF;text-decoration:none;border-radius:8px;">'
                 f'{esc(DOWNLOAD[0])}</a></td></tr></table>')
    parts.append(f'<p style="margin:0 0 20px;">{esc(SIGN_OFF)}</p>')
    footer = f'<p style="margin:0;">{esc(WHY)} <a class="soft" href="{esc(unsubscribe)}" style="color:#554C41;">{esc(STOP)}</a></p>'
    preheader = " ".join(LINK.sub(r"\1", EMPH.sub(r"\1", BOLD.sub(r"\1", BULLET.sub("", HEADING.sub("", blocks[0]))))).split()) if blocks else OPENING
    return text, shell(subject, preheader, "\n".join(parts), footer)


# ── the run

class Pace:
    """At most `rate` emails a second: each waits until 1/rate after the one before it started."""

    def __init__(self, rate: float, clock=time.monotonic, sleep=time.sleep):
        self.gap = 1.0 / max(float(rate), 0.1)
        self.clock, self.sleep, self.last = clock, sleep, None

    def wait(self):
        if self.last is not None:
            left = self.last + self.gap - self.clock()
            if left > 0:
                self.sleep(left)
        self.last = self.clock()


class Record:
    """Which of the list one subject's emails have reached, by row id alone, so a second run of the
    same subject sends only to the rest. Kept on this Mac, outside the repository."""

    def __init__(self, subject: str, folder: Path | None = None):
        self.path = (folder or STATE) / (hashlib.sha256(subject.encode("utf-8")).hexdigest()[:24] + ".json")
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.done = set(data.get("sent") or []) if isinstance(data, dict) else set()
        except (OSError, ValueError):
            self.done = set()

    @staticmethod
    def key(recipient: dict) -> str:
        """The row's id from the unsubscribe link (t=<id>.<hmac>), or else a hash of the whole link."""
        link = str(recipient.get("unsubscribe", ""))
        found = re.search(r"[?&]t=(\d+)\.", link)
        return found.group(1) if found else "h" + hashlib.sha256(link.encode("utf-8")).hexdigest()[:32]

    def has(self, recipient: dict) -> bool:
        return self.key(recipient) in self.done

    def add(self, recipient: dict):
        self.done.add(self.key(recipient))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        part = self.path.with_name(self.path.name + ".part")
        part.write_text(json.dumps({"sent": sorted(self.done)}), encoding="utf-8", newline="\n")
        os.replace(part, self.path)


def run(args, out=print) -> int:
    subject = args.subject.strip()
    markdown = Path(args.body).read_text(encoding="utf-8")
    if not subject or not markdown.strip():
        raise Stop("The subject and the body both need words.", 2)
    keys = read_keys()
    worker, ses = Worker(keys["admin_token"]), SES(keys)
    only = args.only.strip().lower() if args.only is not None else None

    listed = worker.recipients()
    suppressed = ses.suppressed()
    on_both = sorted({r["email"].strip().lower() for r in listed} & suppressed)
    out(f"On the list: {len(listed)} confirmed. Suppressed at SES: {len(suppressed)}, of them on the list: {len(on_both)}.")
    if args.send and on_both and only is None:
        out(f"Removed from the list: {worker.delete(on_both)}.")
    recipients = [r for r in listed if r["email"].strip().lower() not in suppressed]
    record = None
    if only is not None:
        recipients = [r for r in recipients if r["email"].strip().lower() == only]
        if not recipients:
            raise Stop("That address is not a confirmed address on the list (or it is suppressed). Nothing was sent.")
    else:
        record = Record(subject)
        before = len(recipients)
        recipients = [r for r in recipients if not record.has(r)]
        if before != len(recipients):
            out(f"Already sent this subject: {before - len(recipients)}.")

    account = ses.account()
    quota = account.get("SendQuota") or {}
    rate = float(quota.get("MaxSendRate") or 1)
    most = float(quota.get("Max24HourSend") or 0)
    left = float("inf") if most < 0 else most - float(quota.get("SentLast24Hours") or 0)
    production = bool(account.get("ProductionAccessEnabled"))
    out(f"SES: {rate:g} a second, " + ("no daily limit" if most < 0 else f"{left:g} left of today's {most:g}")
        + f", production access: {'yes' if production else 'no (verified addresses only)'}.")

    if not args.send:
        sample_text, _ = render(subject, markdown, "<your own unsubscribe link>")
        out(f"Dry run: {len(recipients)} email{'' if len(recipients) == 1 else 's'} would go. Nothing was sent or changed.")
        out(f"\nSubject: {subject}\n\n{sample_text}")
        return 0
    if not account.get("SendingEnabled", True):
        raise Stop("Sending is paused on this SES account. Nothing was sent.")
    if not production and only is None:
        raise Stop("SES has not given this account production access, so it can mail verified addresses only. "
                   "Nothing was sent. Use --only for a test until it is granted.")
    if len(recipients) > left:
        raise Stop(f"{len(recipients)} emails is more than the {left:g} SES allows today. Nothing was sent.")

    pace, sent, failed, in_a_row, stopped = Pace(rate), 0, [], 0, False
    try:
        for r in recipients:
            text, page = render(subject, markdown, r["unsubscribe"])
            status, kind = 0, ""
            for attempt in range(RETRIES + 1):
                pace.wait()
                try:
                    status, kind = ses.send(r["email"], subject, text, page, r["unsubscribe"])
                except Unreachable:
                    status, kind = 0, "unreachable"
                if status == 429 or kind in ("TooManyRequestsException", "ThrottlingException"):
                    if attempt < RETRIES:
                        time.sleep(2 ** attempt)
                        continue
                break
            if status == 200:
                sent += 1
                in_a_row = 0
                if record is not None:
                    record.add(r)
            else:
                failed.append(f"{status or ''} {kind}".strip())
                in_a_row += 1
                if in_a_row >= IN_A_ROW:
                    stopped = True
                    break
    finally:
        out(f"Sent {sent} of {len(recipients)}" + (f", {len(failed)} failed: " + ", ".join(sorted(set(failed))) if failed else "") + "."
            + (f" Stopped after {IN_A_ROW} failures in a row." if stopped else "")
            + (" Run the same subject again to send to the rest." if (failed or stopped) and record is not None else ""))
    return 1 if failed else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Send the release email to Idiograph's updates list. A dry run unless --send.")
    ap.add_argument("--subject", required=True, help="the email's subject")
    ap.add_argument("--body", required=True, help="a Markdown file with the email's words")
    ap.add_argument("--send", action="store_true", help="send; without it nothing is sent or changed")
    ap.add_argument("--only", metavar="ADDRESS", help="send to this one address, which must already be confirmed")
    args = ap.parse_args(argv)
    try:
        return run(args)
    except Stop as stop:
        print(stop, file=sys.stderr)
        return stop.code
    except OSError as exc:
        print(f"Could not read the body file: {type(exc).__name__}.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
