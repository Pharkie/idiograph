"""Area 342: the relay for Working together (wtrelay, working together build 3, 8 November 2026, Adam's
rulings of that day and the spec's section 5). The relay in relay/ is a Cloudflare Worker with one Durable
Object per project, never deployed from here: the area runs it on this computer through Miniflare, the engine
`wrangler dev` uses, on a free loopback port with a made-up operator code (relay/test/serve.mjs, `cf: false`,
so nothing reaches Cloudflare), and drives it from Python through family/relay_transport.py, the relay route.

What matters: only an operator code makes a project, and only so many. Only a device on the lead's list gets
in, each call signed, and a tampered, stale or replayed one is refused. An envelope comes back byte for byte with
its number and its sender, and the live socket says when one came. A blob goes and comes back whole, and a wrong
hash is refused. What every device has read is deleted, and nothing sooner. A removed device is refused and
stays so. The limits per message and per invite hold. Skips where this computer has no node, no Miniflare or no
`cryptography`. Every key and code is made up here."""
from __future__ import annotations

import hashlib
import http.client
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

from . import support
from .support import check, skip

CODE = "made-up-operator-code-0123456789"


def miniflare_folder() -> Path | None:
    """Miniflare's package folder: IDIOGRAPH_MINIFLARE, relay/node_modules, or Wrangler's own copy."""
    named = os.environ.get("IDIOGRAPH_MINIFLARE")
    if named and (Path(named) / "dist" / "src" / "index.js").is_file():
        return Path(named)
    local = support.source("relay/node_modules/miniflare")
    if (local / "dist" / "src" / "index.js").is_file():
        return local
    wrangler = shutil.which("wrangler")
    if wrangler:
        real = Path(os.path.realpath(wrangler))
        for up in real.parents:
            if up.name == "wrangler" and (up / "node_modules" / "miniflare" / "dist" / "src" / "index.js").is_file():
                return up / "node_modules" / "miniflare"
    return None


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def raw_call(rt, relay, method: str, route: str, body: bytes = b"", *, headers: dict | None = None,
             sign_body: bytes | None = None, stamp: str | None = None):
    """A call by hand, so a check can send what the transport never would. Answers (status, json)."""
    target = relay._prefix + route
    signed = relay._headers(method, target, hashlib.sha256(body if sign_body is None else sign_body).hexdigest())
    if stamp is not None:
        # the signature over another time, as a request kept and sent late would carry
        nonce = signed["X-Nonce"]
        text = f"{method}\n{target}\n{stamp}\n{nonce}\n{hashlib.sha256(body).hexdigest()}".encode()
        signed.update({"X-Time": stamp, "X-Sig": rt.b64url(relay._key.sign(text))})
    sent = dict(signed, **(headers or {}))
    sent["Content-Length"] = str(len(body))
    conn = http.client.HTTPConnection(relay._host, relay._port, timeout=30)
    try:
        try:
            conn.request(method, target, body=body if method in ("POST", "PUT") else None, headers=sent)
        except OSError:
            pass  # a relay refusing a body by its length may answer and close before the body is sent
        answer = conn.getresponse()
        data = answer.read()
        try:
            return answer.status, json.loads(data)
        except ValueError:
            return answer.status, {}
    finally:
        conn.close()


def refused(fn) -> tuple[int, str]:
    import relay_transport as rt
    try:
        fn()
    except rt.RelayError as exc:
        return exc.status, exc.error
    return 0, "taken"


def test_relay(scratch: Path):
    print("\n342. The relay for Working together, run on this computer and driven from Python (wtrelay)")
    worker = support.text("relay/src/worker.js")
    config = support.text("relay/wrangler.jsonc")
    check("342: the relay is routed under idiograph.app/relay/v1/ alone, its Durable Objects in the EU, its blobs "
          "in an EU bucket, and no account id, operator code or secret written in its configuration",
          '"pattern": "idiograph.app/relay/v1/*"' in config and '"JURISDICTION": "eu"' in config
          and '"jurisdiction": "eu"' in config and '"new_sqlite_classes": ["Project", "Invite", "Operator"]' in config
          and "account_id" not in config and "OPERATOR_CODES" not in re.sub(r"//.*", "", config)
          and "ns.jurisdiction(where)" in worker and "workers_dev\": false" in config)
    licensed = [p for p in ("relay/src/worker.js", "relay/wrangler.jsonc", "relay/test/serve.mjs", "family/relay_transport.py")
                if "SPDX-License-Identifier: AGPL-3.0-or-later" not in support.text(p).splitlines()[0]]
    check("342: every file of the relay and its transport opens with its AGPL licence line", not licensed, str(licensed))

    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError:
        return skip("342: the relay driven from Python", "no cryptography in this Python")
    sys.path.insert(0, str(support.source("family")))
    import relay_transport as rt

    seed = bytes(range(32))
    one = rt.RelayTransport(seed, "http://127.0.0.1:9/relay/v1")
    head = one._headers("GET", "/relay/v1/p/x/messages?after=0", rt.EMPTY)
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    text = f"GET\n/relay/v1/p/x/messages?after=0\n{head['X-Time']}\n{head['X-Nonce']}\n{rt.EMPTY}".encode()
    try:
        Ed25519PublicKey.from_public_bytes(one.public_key).verify(rt.unb64url(head["X-Sig"]), text)
        verified = True
    except Exception:
        verified = False
    check("342: the transport signs the method, the path with its query, the time, a fresh nonce and the body's "
          "SHA-256, as the relay checks, and its device id is the first 16 bytes of the key's SHA-256",
          verified and one.device == hashlib.sha256(one.public_key).hexdigest()[:32]
          and one._headers("GET", "/a", rt.EMPTY)["X-Nonce"] != head["X-Nonce"])

    node = shutil.which("node")
    folder = miniflare_folder()
    if not node:
        return skip("342: the relay run on this computer", "no node on this machine")
    if not folder:
        return skip("342: the relay run on this computer", "no Miniflare (relay/node_modules, or Wrangler's own)")
    port = free_port()
    child = subprocess.Popen([node, str(support.source("relay/test/serve.mjs")), "--port", str(port), "--codes", CODE,
                              "--invite-limit", "1000", "--miniflare", str(folder)],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             cwd=str(scratch), encoding="utf-8", errors="replace")
    said = []
    ready = threading.Event()

    def read():
        for line in child.stdout:
            said.append(line.rstrip())
            if line.startswith("ready "):
                ready.set()
    threading.Thread(target=read, daemon=True).start()
    try:
        if not ready.wait(60):
            return check("342: the relay starts on this computer", False, " | ".join(said[-10:]))
        drive(rt, Ed25519PrivateKey, f"http://127.0.0.1:{port}/relay/v1")
    finally:
        try:
            child.stdin.close()
        except OSError:
            pass
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=10)


def drive(rt, Ed25519PrivateKey, url: str):
    lead = rt.RelayTransport(Ed25519PrivateKey.generate(), url)
    other = rt.RelayTransport(Ed25519PrivateKey.generate(), url)
    third = rt.RelayTransport(Ed25519PrivateKey.generate(), url)

    wrong = refused(lambda: lead.make_project("not-the-operator-code-at-all"))
    project = lead.make_project(CODE)
    check("342: a project is made with an operator code and answers a random 32-hex id, and a wrong code is refused",
          wrong == (403, "operator code") and re.fullmatch(r"[0-9a-f]{32}", project or "") is not None, f"{wrong} {project}")

    outside = refused(lambda: other.fetch(project, 0))
    by_other = refused(lambda: other.set_devices(project, [other.public_key]))
    listed = lead.set_devices(project, [lead.public_key, other.public_key])
    by_member = refused(lambda: other.set_devices(project, [lead.public_key, other.public_key, third.public_key]))
    check("342: a device off the lead's list is refused, the lead's list lets it in, and no one but the lead changes the list",
          outside == (403, "device") and by_other == (403, "device") and by_member == (403, "not the lead")
          and listed.get("devices") == [lead.device, other.device], f"{outside} {by_member} {listed}")

    calls = []
    stop = other.listen(project, lambda: calls.append(time.monotonic()))
    until = time.monotonic() + 10
    while not calls and time.monotonic() < until:
        time.sleep(0.05)
    connected = len(calls)
    sealed = [os.urandom(200), bytes(range(256)) * 4000]
    numbers = [lead.send(project, sealed[0]), other.send(project, sealed[1])]
    until = time.monotonic() + 10
    while len(calls) < connected + 2 and time.monotonic() < until:
        time.sleep(0.05)
    got = other.fetch(project, 0)
    check("342: envelopes come back byte for byte, in order, each with its relay number and its sender's device id",
          numbers == [1, 2] and got == [(1, lead.device, sealed[0]), (2, other.device, sealed[1])]
          and lead.fetch(project, 1) == [(2, other.device, sealed[1])], f"{numbers} {[(n, d) for n, d, _ in got]}")
    check("342: the live socket calls its listener once on connecting and again for each message that comes",
          connected == 1 and len(calls) >= 3, f"{connected} then {len(calls)}")

    route = f"/p/{project}/messages"
    tampered = raw_call(rt, lead, "POST", route, b"what was sent", sign_body=b"what was signed")
    stale = raw_call(rt, lead, "POST", route, b"late", stamp=str(int(time.time()) - 3600))
    unsigned = raw_call(rt, lead, "POST", route, b"x", headers={"X-Sig": ""})
    target = lead._prefix + route
    body = b"sent twice"
    head = lead._headers("POST", target, hashlib.sha256(body).hexdigest())
    twice = []
    for _ in range(2):
        conn = http.client.HTTPConnection(lead._host, lead._port, timeout=30)
        conn.request("POST", target, body=body, headers=dict(head, **{"Content-Length": str(len(body))}))
        twice.append(conn.getresponse().status)
        conn.close()
    check("342: a body other than the one signed, a time an hour old, a call with no signature and the same call sent "
          "twice are each refused",
          tampered[0] == 401 and stale == (401, {"ok": False, "error": "clock"}) and unsigned[0] == 401 and twice == [201, 409],
          f"{tampered} {stale} {unsigned} {twice}")
    big = refused(lambda: lead.send(project, b"x" * (rt.MAX_MESSAGE + 1)))
    big_raw = raw_call(rt, lead, "POST", route, b"x" * (rt.MAX_MESSAGE + 1))
    check("342: an envelope over the message limit is refused, by the transport and by the relay",
          big == (413, "too large") and big_raw[0] == 413, f"{big} {big_raw}")

    blob = "b" + os.urandom(12).hex()
    data = os.urandom(3 * 1024 * 1024 + 7)
    size = lead.put_blob(project, blob, data)
    back = other.get_blob(project, blob)
    wrong_hash = raw_call(rt, lead, "PUT", f"/p/{project}/blobs/{blob}x", b"these bytes", sign_body=b"other bytes",
                          headers={"X-Content-SHA256": hashlib.sha256(b"other bytes").hexdigest()})
    missing = refused(lambda: other.get_blob(project, "nosuchblob0123456789"))
    check("342: a sealed blob over a message's size goes to R2 and comes back whole, a body not matching its signed hash is "
          "refused, and a blob never sent is not found",
          size == len(data) and back == data and wrong_hash[0] == 400 and missing[0] == 404, f"{wrong_hash} {missing}")

    after = other.fetch(project, 0)
    top = after[-1][0]
    first = lead.seen(project, top)
    kept = other.fetch(project, 0)
    second = other.seen(project, top)
    left = lead.fetch(project, 0)
    check("342: nothing is deleted while one device has not read it, and what every device has read is deleted",
          first == 0 and len(kept) == len(after) and second == len(after) and left == [], f"{first} {second} {len(left)}")

    lead.set_devices(project, [lead.public_key, other.public_key, third.public_key])
    third.send(project, b"from the third")
    removed = lead.set_devices(project, [lead.public_key, other.public_key])
    shut = refused(lambda: third.fetch(project, 0))
    back_in = refused(lambda: lead.set_devices(project, [lead.public_key, other.public_key, third.public_key]))
    check("342: a device taken off the list is refused from then on, and the lead cannot put it back",
          removed.get("removed") == [third.device] and shut == (403, "removed") and back_in == (409, "a removed device stays removed"),
          f"{removed} {shut} {back_in}")
    stop()

    invite = os.urandom(16).hex()
    places = [lead.invite_post(invite, f"answer {i}".encode()) for i in range(10)]
    full = refused(lambda: other.invite_post(invite, b"eleventh"))
    large = raw_call(rt, lead, "POST", f"/invites/{os.urandom(16).hex()}", b"x" * (rt.MAX_INVITE + 1))
    answers = other.invite_fetch(invite, 8)
    check("342: an invite takes ten join answers unsigned and no more, none over 4 KB, and hands them back after a place",
          places == list(range(1, 11)) and full == (429, "invite full") and large[0] == 413
          and answers == [(9, b"answer 8"), (10, b"answer 9")], f"{full} {large} {answers}")

    # the glue: Working together's team module finds this route by name and sends invites through the invite mailbox
    import base64
    import transport
    seeds = [os.urandom(32), os.urandom(32)]
    devs = [{"id": rt.device_id(Ed25519PrivateKey.from_private_bytes(sd).public_key().public_bytes_raw()),
             "sign": base64.b64encode(sd).decode("ascii")} for sd in seeds]
    kept_override = transport.OVERRIDE
    transport.OVERRIDE = None
    try:
        inviter = transport.for_team("relay", devs[0], {"relay_url": url})
        joiner = transport.for_team("relay", devs[1], {"relay_url": url})
        box = f"{transport.INVITE_PREFIX}{os.urandom(16).hex()}"
        placed = [joiner.send(box, b"join answer one"), inviter.send(box, b"welcome")]
        read = inviter.fetch(box, 0)
        later = joiner.fetch(box, 1)
        signed_call = refused(lambda: joiner.fetch(project, 0))
    finally:
        transport.OVERRIDE = kept_override
    check("342: the relay is registered under transport.py's 'relay' route, made from the install's device key and the "
          "team's address, and an invite's mailbox (invite/<id>) goes through the relay's unsigned invite mailbox while "
          "a project's goes through the signed calls",
          "relay" in transport.FACTORIES and inviter.device == devs[0]["id"] and placed == [1, 2]
          and read == [(1, "", b"join answer one"), (2, "", b"welcome")] and later == [(2, "", b"welcome")]
          and signed_call == (403, "device"), f"{placed} {read} {signed_call}")

    made = 1
    while made < 25:
        try:
            rt.RelayTransport(Ed25519PrivateKey.generate(), url).make_project(CODE)
            made += 1
        except rt.RelayError as exc:
            break
    check("342: one operator code makes twenty projects and no more", made == 20, str(made))
