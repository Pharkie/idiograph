"""Area 450: the updates list's Worker (updates by email, 23 November 2026, Adam's ask of that day and the red
team's changes to the plan). updates-worker/ is a Cloudflare Worker with a D1 table, never deployed from here:
the area runs its checks in node (updates-worker/test/run.mjs), with node's own SQLite standing in for D1 and
made from schema.sql, so the Worker's SQL runs as written, and a stand-in for fetch where Amazon SES would be, so
nothing leaves this computer.

What matters: a sign-up's answer is the same whether the address is new, pending or confirmed; a confirmation
email goes at most once an hour and three times a day to one address, ten sign-ups an hour from one hashed IP, a
hundred emails a day in all, past which the sign-up is kept with no email; a browser's request comes from the
site or is refused, and the app's server sends none; a filled honeypot keeps nothing; a GET never confirms or
unsubscribes, only the POST does; only the newest email's link confirms, and a confirmed row keeps no token and
no IP hash; an unsubscribe link is an HMAC of the row's id and deletes the row, RFC 8058's one-click included, and
an id is never given twice; the admin routes take the bearer token in the header alone; the cron clears pending
rows after 7 days; and SigV4 gives AWS's own published vectors. Since the Fable review of 23 November: 300
sign-ups at the same moment still pass no limit (each takes its place in one statement); the answer comes before
the email; the signature is over the body sent, checked with node's own crypto; nothing logged holds an address;
an email SES does not take gives its place back and keeps the earlier link working; a confirmation's token comes
from the form alone; a body is read no further than its limit; and a thousand-address delete keeps within D1's
50 queries. Skips where this computer has no node or a node
without node:sqlite (22.5 and later)."""
from __future__ import annotations

import json
import re
import shutil
import subprocess

from . import support
from .support import check, skip


def test_updates_worker(scratch):
    print("\n450. Updates by email: the Worker, its table and its limits, in node with a stand-in for D1 and SES")
    folder = support.source("updates-worker")
    names = ("worker.js", "wrangler.toml", "schema.sql", "README.md", "test/run.mjs", "test/sigv4_vectors.json")
    check("450: the folder holds the Worker, its config, its table, the steps and its checks",
          all((folder / n).is_file() for n in names), str([n for n in names if not (folder / n).is_file()]))
    if not all((folder / n).is_file() for n in names):
        return
    text = {n: (folder / n).read_text(encoding="utf-8") for n in names}
    toml = text["wrangler.toml"]
    check("450: wrangler.toml names idiograph-updates on the two zone routes, no workers.dev, a daily cron and D1 "
          "idiograph-updates with a placeholder id",
          'name = "idiograph-updates"' in toml and "workers_dev = false" in toml
          and '{ pattern = "idiograph.app/api/updates/*", zone_name = "idiograph.app" }' in toml
          and '{ pattern = "www.idiograph.app/api/updates/*", zone_name = "idiograph.app" }' in toml
          and re.search(r'^crons = \["[^"]+"\]$', toml, flags=re.M) is not None
          and 'database_name = "idiograph-updates"' in toml and 'database_id = "PUT-THE-ID-FROM-WRANGLER-D1-CREATE-HERE"' in toml)
    secrets = ("ADMIN_TOKEN", "IP_SALT", "UNSUB_SECRET", "CONFIRM_SALT", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY")
    # the shapes a pasted secret takes, each spelt with a class so this line never matches itself
    secretish = re.compile(r"[0-9a-f]{32,}|AK[I]A[0-9A-Z]{16}|sk[-]ant|Bearer [A-Za-z0-9]{20,}|(?:" + "|".join(secrets) + r')\s*=\s*"')
    shipped = ("worker.js", "wrangler.toml", "schema.sql", "README.md")
    check("450: every secret is named in the config and the steps, none is written in any file",
          all(s in toml and f"wrangler secret put {s}" in text["README.md"] for s in secrets)
          and not any(secretish.search(text[n]) for n in shipped),
          str([n for n in shipped if secretish.search(text[n])]))
    addresses = {a.lower() for n in names for a in re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", text[n]) if not a.endswith(".png")}
    check("450: no address in the folder but hello@idiograph.app and made-up ones on example.com, .org or .net",
          all(a == "hello@idiograph.app" or re.search(r"[@.-]example\.(?:com|org|net)$", a) for a in addresses),
          str(sorted(a for a in addresses if not a.endswith(("@example.com", "@example.org", "@example.net")))))
    check("450: the README's steps are written to be run by hand, and nothing here runs them",
          "wrangler d1 create idiograph-updates --location weur" in text["README.md"]
          and "wrangler d1 execute idiograph-updates --remote --file schema.sql" in text["README.md"]
          and "wrangler deploy" in text["README.md"])

    node = shutil.which("node")
    if not node:
        return skip("450: the Worker in node", "no node on this machine")
    has_sqlite = support.run_node("require('node:sqlite');\n", scratch, "sqlite-450.js")
    if has_sqlite.returncode != 0:
        return skip("450: the Worker in node", "this node has no node:sqlite (22.5 and later)")
    syntax = subprocess.run([node, "--check", str(folder / "test" / "run.mjs")], capture_output=True, text=True, encoding="utf-8")
    run = subprocess.run([node, str(folder / "test" / "run.mjs"), str(folder / "worker.js")], capture_output=True, text=True,
                         encoding="utf-8", timeout=120)
    if run.returncode != 0 or syntax.returncode != 0:
        return check("450: the Worker's checks run in node", False, (syntax.stderr + run.stderr).strip()[-400:])
    results = json.loads(run.stdout.strip().splitlines()[-1])
    check("450: node ran the Worker's checks, every one of them", len(results) >= 51, str(len(results)))
    for name, passed, detail in results:
        check(f"450: in node, {name}", passed, detail)
