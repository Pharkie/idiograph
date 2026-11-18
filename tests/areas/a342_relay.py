"""Area 342: the relay for Working together (wtrelay, working together build 3, 8 November 2026, Adam's
rulings of that day and the spec's section 5). The relay in relay/ is a Cloudflare Worker with one Durable
Object per project, never deployed from here: the area runs it on this computer through Miniflare, the engine
`wrangler dev` uses, on a free loopback port with a made-up operator code (relay/test/serve.mjs, `cf: false`,
so nothing reaches Cloudflare), and drives it from Python through family/relay_transport.py, the relay route.

What matters (relayopen, 18 November 2026; relayfix2: the invite limit as deployed against the cards' pace, two
listeners on one key, a fourth socket, seen above the top, the lead's list unchanged and changed, a new
project's call sent twice): anyone starts a project with no code, three a day from one address
and only so many in all. Only a device on the lead's list gets
in, each call signed, and a tampered, stale or replayed one is refused. An envelope comes back byte for byte with
its number and its sender, and the live socket says when one came. A blob goes and comes back whole, and a wrong
hash is refused. What every device has read is deleted, and nothing sooner. A removed device is refused and
stays so. The limits per message and per invite hold. A message names the file it carries and the file goes when
every computer has read it; a project's day, its 250 MB waiting, one file's limit and the relay's ceiling each refuse
in their own word, a failed upload handing its bytes back; a project the old relay made (relay/test/worker_v1.js,
run first on the same storage) keeps working under its old limits, and the old relay run again on the new one's
storage reads it (a rollback); the operator's key reads usage and deletes a project, and with no key set nothing
does; a call that cannot be signed is refused before any project is touched; small messages have a cap of their own
waiting, files their share of the day, and messages a count a day; new invites a day are counted; and a project's
alarm, brought to seconds, deletes what is old, sweeps a file no message names, mends the sums, stops when the
project is idle and is set again by its next message (relayfix). The later runs lay smaller limits over the relay's
own (--test-limits). Skips where this computer has no node, no Miniflare or no `cryptography`. Every key and code is
made up here."""
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
KEY = "made-up-operator-key-0123456789ab"


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


def drive(rt, Ed25519PrivateKey, url: str):
    lead = rt.RelayTransport(Ed25519PrivateKey.generate(), url)
    other = rt.RelayTransport(Ed25519PrivateKey.generate(), url)
    third = rt.RelayTransport(Ed25519PrivateKey.generate(), url)

    project = lead.make_project()
    check("342: a project is made with the lead's signed key alone, no code asked, and answers a random 32-hex id",
          re.fullmatch(r"[0-9a-f]{32}", project or "") is not None, str(project))
    junk = os.urandom(16).hex()
    no_sig = raw_call(rt, lead, "GET", f"/p/{junk}/messages?after=0", headers={"X-Sig": ""})
    no_box = refused(lambda: lead.fetch(junk, 0))
    keyless = operator_call(url, "GET", "/operator/usage", KEY)
    empty_invite = refused(lambda: lead.invite_fetch(os.urandom(16).hex(), 0))
    unopened = refused(lambda: lead.invite_post(os.urandom(16).hex(), b"an answer nobody asked for"))
    check("342: a call with no signature is refused before any project is asked, a signed look at a project never "
          "made is refused as no project, an invite no project opened takes and gives nothing, and with no operator "
          "key set the operator's routes refuse every key",
          no_sig[0] == 401 and no_box == (404, "no project") and keyless[0] == 403
          and empty_invite == (404, "no invite") and unopened == (404, "no invite"),
          f"{no_sig} {no_box} {keyless[0]} {empty_invite}")

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
    live = stop.__self__
    was = live.connects
    rt._send_frame(live._sock, 0x1, b"anything but a ping")
    until = time.monotonic() + 10
    while live.connected and time.monotonic() < until:
        time.sleep(0.05)
    closed = not live.connected
    # the app waits before it connects again after the relay closed its socket (review2's N3), never a second
    time.sleep(3)
    check("342: a socket that says anything but a ping is closed by the relay, and the app does not connect again "
          "at once",
          closed and live.connects == was, f"{closed} {live.connects - was}")

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
    target = lead._prefix + f"/p/{project}/messages?after=0"
    head = lead._headers("GET", target, rt.EMPTY)
    reads = []
    for _ in range(2):
        conn = http.client.HTTPConnection(lead._host, lead._port, timeout=30)
        conn.request("GET", target, headers=head)
        reads.append(conn.getresponse().status)
        conn.close()
    check("342: a GET's nonce is not written down, so the same look sent twice is answered twice, and changes nothing",
          reads == [200, 200], str(reads))
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
    lead.invite_open(project, invite)
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
        lead.invite_open(project, box[len(transport.INVITE_PREFIX):])
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


class Relay:
    """The relay on this computer: `node serve.mjs` on a free loopback port, started and stopped by its own process,
    never another's. Answers its URL from `start`, or None when it did not start, with what it said."""

    def __init__(self, scratch: Path, node: str, folder: Path, *extra: str):
        self.port = free_port()
        self.url = f"http://127.0.0.1:{self.port}/relay/v1"
        self.said: list[str] = []
        self.child = subprocess.Popen([node, str(support.source("relay/test/serve.mjs")), "--port", str(self.port),
                                       "--codes", CODE, "--invite-limit", "1000", "--miniflare", str(folder), *extra],
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                      cwd=str(scratch), encoding="utf-8", errors="replace")
        self.ready = threading.Event()
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.child.stdout:
            self.said.append(line.rstrip())
            if line.startswith("ready "):
                self.ready.set()

    def up(self) -> bool:
        return self.ready.wait(60)

    def stop(self):
        try:
            self.child.stdin.close()
        except OSError:
            pass
        try:
            self.child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.child.kill()
            self.child.wait(timeout=10)


def test_relay(scratch: Path):
    print("\n342. The relay for Working together, run on this computer and driven from Python (wtrelay, relayopen)")
    worker = support.text("relay/src/worker.js")
    config = support.text("relay/wrangler.jsonc")
    check("342: the relay is routed under idiograph.app/relay/v1/ alone, its Durable Objects in the EU, its blobs "
          "in an EU bucket, the counter added by a migration of its own, and no account id, operator code or secret "
          "written in its configuration",
          '"pattern": "idiograph.app/relay/v1/*"' in config and '"JURISDICTION": "eu"' in config
          and '"jurisdiction": "eu"' in config and '"new_sqlite_classes": ["Project", "Invite", "Operator"]' in config
          and '{ "tag": "v2", "new_sqlite_classes": ["Counter"] }' in config
          and "account_id" not in config and "OPERATOR_CODES" not in re.sub(r"//.*", "", config)
          and "ns.jurisdiction(where)" in worker and "workers_dev\": false" in config)
    licensed = [p for p in ("relay/src/worker.js", "relay/wrangler.jsonc", "relay/test/serve.mjs", "relay/test/worker_v1.js",
                            "family/relay_transport.py")
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
    # the first run with no operator key set, so its routes are shown refusing every key
    relay = Relay(scratch, node, folder)
    try:
        if not relay.up():
            return check("342: the relay starts on this computer", False, " | ".join(relay.said[-10:]))
        drive(rt, Ed25519PrivateKey, relay.url)
    finally:
        relay.stop()

    # the relay with the invite limit wrangler.jsonc deploys, and the cards' own pace against it (review2's N2), then
    # two listeners on one key (N3)
    real_limit = int(re.search(r'"name": "INVITE_LIMIT".*?"limit": (\d+)', config).group(1))
    poll_ms = int(re.search(r"const WT_POLL_MS = (\d+);", support.text("apps/idiograph/static/team.js")).group(1))
    real = Relay(scratch, node, folder, "--invite-limit", str(real_limit), "--project-limit", "20",
                 "--test-limits", json.dumps({"projectsPerIp": 20}))
    try:
        if not real.up():
            return check("342: the relay starts with the invite limit it is deployed with", False,
                         " | ".join(real.said[-10:]))
        invite_pace(rt, Ed25519PrivateKey, real.url, real_limit, poll_ms)
        two_sockets(rt, Ed25519PrivateKey, real.url)
        no_writes(rt, Ed25519PrivateKey, real.url)
    finally:
        real.stop()

    # the old relay's storage under the new relay, then the limits, with smaller ones laid over them
    store = scratch / "relay-342-store"
    shutil.rmtree(store, ignore_errors=True)
    store.mkdir(parents=True)
    old = Relay(scratch, node, folder, "--persist", str(store), "--script", str(support.source("relay/test/worker_v1.js")))
    try:
        if not old.up():
            return check("342: the old relay starts on this computer", False, " | ".join(old.said[-10:]))
        made = old_project(rt, Ed25519PrivateKey, old.url)
    finally:
        old.stop()
    new = Relay(scratch, node, folder, "--persist", str(store), "--operator-key", KEY,
                "--test-limits", json.dumps(TEST_LIMITS))
    try:
        if not new.up():
            return check("342: the new relay starts on the old one's storage", False, " | ".join(new.said[-10:]))
        later = limits(rt, Ed25519PrivateKey, new.url, made)
    finally:
        new.stop()
    back = Relay(scratch, node, folder, "--persist", str(store), "--script", str(support.source("relay/test/worker_v1.js")))
    try:
        if not back.up():
            return check("342: the old relay starts again on the new one's storage", False, " | ".join(back.said[-10:]))
        rolled_back(rt, back.url, made, later)
    finally:
        back.stop()
        shutil.rmtree(store, ignore_errors=True)
    alarms = Relay(scratch, node, folder, "--operator-key", KEY, "--test-limits", json.dumps(ALARM_LIMITS))
    try:
        if not alarms.up():
            return check("342: the relay starts with its alarms in seconds", False, " | ".join(alarms.said[-10:]))
        alarm(rt, Ed25519PrivateKey, alarms.url)
        removed_most(rt, Ed25519PrivateKey, alarms.url, ALARM_LIMITS["removedMost"])
    finally:
        alarms.stop()


# the limits laid over the relay's own for the second run, so each is reached with a few hundred kilobytes
TEST_LIMITS = {"blob": 300_000, "dayBytes": 1_000_000, "dayFiles": 800_000, "waiting": 600_000, "dayMessages": 30,
               "waitingMessages": 250_000, "smallWaiting": 50_000, "ceilingBlobs": 2_000_000,
               "ceilingMessages": 50_000_000, "projectsPerDay": 7, "projectsPerIp": 3, "invitesPerProject": 3,
               "filesPerDay": 6, "relayFilesPerDay": 6, "fetchesPerFile": 3}
# and for the run of the alarms: in seconds, keeping nothing, a project idle at once, every message reported, and a
# ceiling for messages a few kilobytes high
ALARM_LIMITS = {"keepDays": 0, "orphanDays": 0, "idleDays": 0, "alarmEvery": 6, "report": 0, "ceilingMessages": 5_000,
                "projectsPerIp": 20, "projectsPerDay": 20, "removedMost": 2}


def invite_pace(rt, Ed25519PrivateKey, url: str, limit: int, poll_ms: int) -> None:
    """A minute of an invite as the app makes it, both computers behind one address (Add a computer of mine at
    home): the offer posted, the invite card's looks and the join card's looks at the cards' pace, the joiner's
    read and answer, and the lead's read and two posts at They match. None may meet the relay's invite limit as
    wrangler.jsonc deploys it, and the limit, once passed, answers `slow down`."""
    lead = rt.RelayTransport(Ed25519PrivateKey.generate(), url)
    joiner = rt.RelayTransport(Ed25519PrivateKey.generate(), url)
    project = lead.make_project()
    lead.set_devices(project, [lead.public_key])
    inv = os.urandom(16).hex()
    lead.invite_open(project, inv)
    looks = max(1, 60000 // poll_ms)
    calls = [lambda: lead.invite_post(inv, b"the offer")]
    calls += [lambda: lead.invite_fetch(inv)] * looks
    calls += [lambda: joiner.invite_fetch(inv), lambda: joiner.invite_post(inv, b"the answer")]
    calls += [lambda: joiner.invite_fetch(inv)] * looks
    calls += [lambda: lead.invite_fetch(inv), lambda: lead.invite_post(inv, b"welcome"),
              lambda: lead.invite_post(inv, b"closed")]
    took = [refused(c) for c in calls]
    more = []
    for _ in range(3 * limit):
        more.append(refused(lambda: lead.invite_fetch(inv)))
        if more[-1] != (0, "taken"):
            break
    check(f"342: a minute of an invite, both cards looking every {poll_ms // 1000} s from one address with the offer, "
          f"the answer and They match, is {len(calls)} calls and none meets the relay's {limit} a minute as deployed, "
          "and past that the relay answers slow down",
          len(calls) <= limit and all(t == (0, "taken") for t in took) and more and more[-1] == (429, "slow down"),
          json.dumps({"calls": len(calls), "refused": [t for t in took if t != (0, "taken")], "more": len(more),
                      "last": more[-1] if more else None}))


def kept_call(relay, method: str, route: str, data: dict | None):
    """One signed call made once and sent as often as asked, byte for byte, so a check can tell whether the first
    wrote its nonce (the second is then refused as sent before). Answers a function giving each send's status."""
    body = json.dumps(data, separators=(",", ":")).encode() if data is not None else b""
    target = relay._prefix + route
    head = dict(relay._headers(method, target, hashlib.sha256(body).hexdigest()),
                **{"Content-Length": str(len(body)), "Content-Type": "application/json"})

    def send() -> int:
        conn = http.client.HTTPConnection(relay._host, relay._port, timeout=30)
        try:
            conn.request(method, target, body=body if method in ("POST", "PUT") else None, headers=head)
            answer = conn.getresponse()
            answer.read()
            return answer.status
        finally:
            conn.close()
    return send


def no_writes(rt, Ed25519PrivateKey, url: str) -> None:
    """The signed calls that could write rows without bound (review2's M1, M2 and L4): a `seen` above the highest
    message, the lead's list sent unchanged, the lead's list changed past the day's, and one new project's call sent
    again."""
    lead = rt.RelayTransport(Ed25519PrivateKey.generate(), url)
    other = rt.RelayTransport(Ed25519PrivateKey.generate(), url)
    made = kept_call(lead, "POST", "/projects", {"key": rt.b64url(lead.public_key)})
    first, again = made(), made()
    check("342: one signed call to start a project, sent again byte for byte, makes no second project",
          (first, again) == (201, 409), f"{first} {again}")

    project = lead.make_project()
    lead.set_devices(project, [lead.public_key, other.public_key])
    for i in range(3):
        lead.send(project, f"message {i}".encode())
    other.seen(project, 3)
    above = kept_call(other, "POST", f"/p/{project}/seen", {"n": 6000})
    at_top = [above(), above()]
    lead.seen(project, 9999)
    lead.send(project, b"message 4")
    lead.seen(project, 4)
    still = [n for n, _d, _b in other.fetch(project, 3)]
    check("342: a seen above the highest message is held to the top, so once a computer's mark is there a further "
          "seen writes nothing, and a later message waits for it",
          at_top == [200, 200] and still == [4], f"{at_top} {still}")

    unchanged = kept_call(lead, "PUT", f"/p/{project}/devices",
                          {"devices": [rt.b64url(lead.public_key), rt.b64url(other.public_key)]})
    same = [unchanged(), unchanged()]
    changed = []
    for _ in range(30):
        extra = rt.RelayTransport(Ed25519PrivateKey.generate(), url)
        changed.append(refused(lambda: lead.set_devices(project, [lead.public_key, other.public_key,
                                                                  extra.public_key])))
    check("342: in a project made open the lead's list sent unchanged answers at once and writes nothing, and a "
          "changed list is taken 30 times a day (the first list among them), then refused in a word of its own",
          same == [200, 200] and changed[:29] == [(0, "taken")] * 29 and changed[29] == (429, "lists today"),
          f"{same} {changed[-2:]}")


def removed_most(rt, Ed25519PrivateKey, url: str, most: int) -> None:
    """The rows of removed devices a project made open keeps are capped (review2's M2), with `most` laid low."""
    lead = rt.RelayTransport(Ed25519PrivateKey.generate(), url)
    project = lead.make_project()
    said = []
    for _ in range(most + 2):
        extra = rt.RelayTransport(Ed25519PrivateKey.generate(), url)
        said.append(refused(lambda: lead.set_devices(project, [lead.public_key, extra.public_key])))
    # the first list adds one, and each after it removes the one before
    check(f"342: a project keeps at most {most} removed devices, and a list that would remove more is refused",
          said[:most + 1] == [(0, "taken")] * (most + 1) and said[most + 1] == (409, "too many removed"), str(said))


def two_sockets(rt, Ed25519PrivateKey, url: str) -> None:
    """Two Idiographs on one computer listen on one project with one key, as the installed app and a server on
    another port do (review2's N3): the relay keeps both sockets, so neither is closed and neither reconnects. A
    fourth socket for one device closes the oldest, and a socket the relay closes is waited on, never tried again
    at once."""
    lead = rt.RelayTransport(Ed25519PrivateKey.generate(), url)
    project = lead.make_project()
    lead.set_devices(project, [lead.public_key])
    counts = {"opens": 0}
    real_open = rt._Live._open

    def counted(self):
        counts["opens"] += 1
        return real_open(self)
    rt._Live._open = counted
    stops = []
    try:
        heard = [threading.Event(), threading.Event()]
        stops = [lead.listen(project, heard[0].set), lead.listen(project, heard[1].set)]
        time.sleep(6)
        settled = counts["opens"]
        for h in heard:
            h.clear()
        lead.send(project, b"one for both")
        both = heard[0].wait(10) and heard[1].wait(10)
        time.sleep(4)
        after = counts["opens"]
    finally:
        rt._Live._open = real_open
        for stop in stops:
            stop()
    check("342: two listeners on one project with one key both stay open: in ten seconds they connect twice in all, "
          "and both hear a new message",
          settled == 2 and after == 2 and both, json.dumps({"settled": settled, "after": after, "both": both}))

    # a fourth socket for the device closes the oldest, and the app waits before it tries again
    from urllib.parse import urlsplit
    parts = urlsplit(url)
    socks = [raw_socket(lead, parts, project) for _ in range(4)]
    try:
        first_closed = closed_soon(socks[0])
        others_open = not any(closed_soon(s, 0.5) for s in socks[1:])
    finally:
        for s in socks:
            try:
                s.close()
            except OSError:
                pass
    check("342: the relay keeps up to three sockets a device and closes the oldest when a fourth opens",
          first_closed and others_open, json.dumps({"first": first_closed, "others": others_open}))


def raw_socket(relay, parts, project: str):
    """A socket upgraded to the live route by hand, signed as the transport signs it, its handshake read."""
    target = relay._prefix + f"/p/{project}/live"
    head = relay._headers("GET", target, hashlib.sha256(b"").hexdigest())
    key = "dGhlIHNhbXBsZSBub25jZQ=="
    lines = [f"GET {target} HTTP/1.1", f"Host: {parts.hostname}:{parts.port}", "Upgrade: websocket",
             "Connection: Upgrade", f"Sec-WebSocket-Key: {key}", "Sec-WebSocket-Version: 13"]
    lines += [f"{k}: {v}" for k, v in head.items()]
    sock = socket.create_connection((parts.hostname, parts.port), timeout=10)
    sock.sendall(("\r\n".join(lines) + "\r\n\r\n").encode())
    got = b""
    while b"\r\n\r\n" not in got:
        chunk = sock.recv(4096)
        if not chunk:
            break
        got += chunk
    if b" 101 " not in got.split(b"\r\n", 1)[0]:
        raise AssertionError(got[:200])
    time.sleep(0.3)
    return sock


def closed_soon(sock, wait: float = 3.0) -> bool:
    """Whether the relay closes this socket within `wait` seconds (a close frame or the connection ended)."""
    sock.settimeout(wait)
    try:
        data = sock.recv(4096)
    except socket.timeout:
        return False
    except OSError:
        return True
    # an empty read is the end, and a frame of opcode 8 is a close
    return not data or (data[0] & 0x0F) == 8


def made_from(rt, relay, ip: str) -> str:
    """A project made with the address the relay counts it by, as Cloudflare would set it."""
    body = json.dumps({"key": rt.b64url(relay.public_key)}).encode()
    return relay._call("POST", "/projects", body, headers={"Content-Type": "application/json", "CF-Connecting-IP": ip})["project"]


def operator_call(url: str, method: str, route: str, key: str | None = KEY) -> tuple:
    from urllib.parse import urlsplit
    parts = urlsplit(url)
    conn = http.client.HTTPConnection(parts.hostname, parts.port, timeout=30)
    try:
        conn.request(method, parts.path + route, headers={"Authorization": f"Bearer {key}"} if key else {})
        answer = conn.getresponse()
        return answer.status, json.loads(answer.read() or b"{}")
    finally:
        conn.close()


def usage_of(url: str, project: str) -> dict:
    rows = operator_call(url, "GET", "/operator/usage")[1].get("projects", [])
    return {r["project"]: r for r in rows}.get(project) or {}


def old_project(rt, Ed25519PrivateKey, url: str) -> dict:
    """A project made by the relay as it ran before relayopen, with its operator code: two devices, a message read
    by neither, and a 3 MB file, over the new limit for one file."""
    lead = rt.RelayTransport(Ed25519PrivateKey.generate(), url)
    other = rt.RelayTransport(Ed25519PrivateKey.generate(), url)
    project = lead.make_project(CODE)
    lead.set_devices(project, [lead.public_key, other.public_key])
    first = lead.send(project, b"made under the old relay")
    blob = "o" + os.urandom(12).hex()
    data = os.urandom(3 * 1024 * 1024)
    lead.put_blob(project, blob, data, 200 * 1024 * 1024)
    return {"lead": lead, "other": other, "project": project, "first": first, "blob": blob, "data": data}


def limits(rt, Ed25519PrivateKey, url: str, old: dict) -> dict:
    # the same two computers, at the new relay's address
    lead, other = (rt.RelayTransport(old[k]._key, url) for k in ("lead", "other"))
    project = old["project"]
    came = other.fetch(project, 0)
    back = other.get_blob(project, old["blob"])
    later_body = os.urandom(40_000)
    later = lead.send(project, later_body)
    check("342: a project the old relay made keeps working on the new relay's storage: its message and its 3 MB file "
          "come back whole, and it takes a message of 40 KB",
          came == [(old["first"], lead.device, b"made under the old relay")] and back == old["data"] and later == old["first"] + 1,
          f"{[(n, d) for n, d, _ in came]} {len(back)} {later}")

    a = rt.RelayTransport(Ed25519PrivateKey.generate(), url)
    b = rt.RelayTransport(Ed25519PrivateKey.generate(), url)
    p = made_from(rt, a, "203.0.113.9")

    def put(name: str, size: int):
        return refused(lambda: a.put_blob(p, name, os.urandom(size), 10 ** 9))
    lonely = (put("s" + os.urandom(12).hex(), 1_000), refused(lambda: a.send(p, os.urandom(40_000))),
              refused(lambda: a.send(p, os.urandom(300))))
    check("342: a project with one computer on its list keeps no file and no larger message, nobody being there to "
          "fetch them, and still takes a small one",
          lonely == ((409, "nobody to send to"), (409, "nobody to send to"), (0, "taken")), str(lonely))
    a.set_devices(p, [a.public_key, b.public_key])

    b1, b2, b3, b4 = ("n" + os.urandom(12).hex() for _ in range(4))
    first = put(b1, 250_000)
    wrong = raw_call(rt, a, "PUT", f"/p/{p}/blobs/{'w' + os.urandom(12).hex()}", os.urandom(250_000),
                     sign_body=b"other bytes", headers={"X-Content-SHA256": hashlib.sha256(b"other bytes").hexdigest()})
    second = put(b2, 250_000)
    again = refused(lambda: a.put_blob(p, b2, os.urandom(10)))
    full = put(b3, 250_000)
    check("342: a new project's file goes, a file R2 refuses for its hash is refused, a file under a name already there "
          "is refused, and a file that would put more than the project's limit waiting on the relay is refused as the "
          "project full",
          first == (0, "taken") and wrong[0] == 400 and second == (0, "taken") and again == (409, "blob there")
          and full == (429, "project full"), f"{first} {wrong} {second} {again} {full}")

    unknown = refused(lambda: a._call("POST", f"/p/{p}/messages?blob={'x' + os.urandom(12).hex()}", b"names nothing"))
    n1 = int(a._call("POST", f"/p/{p}/messages?blob={b1}", os.urandom(300))["n"])
    twice = refused(lambda: a._call("POST", f"/p/{p}/messages?blob={b1}", os.urandom(300)))
    n2 = int(a._call("POST", f"/p/{p}/messages?blob={b2}", os.urandom(300))["n"])
    a.fetch(p, 0)
    a.seen(p, n2)
    kept = refused(lambda: b.get_blob(p, b1))
    usage_before = usage_of(url, p)
    b.fetch(p, 0)
    b.seen(p, n1)
    one_read = (refused(lambda: b.get_blob(p, b1)), refused(lambda: b.get_blob(p, b2)))
    b.seen(p, n2)
    gone = refused(lambda: b.get_blob(p, b2))
    usage_after = usage_of(url, p)
    check("342: a message names the file it carries, a name not there or named before is refused, and a file stays "
          "on the relay until every computer has read its message, then is deleted, the counter's sum for the project "
          "falling with it",
          unknown == (404, "no blob") and twice == (409, "blob named") and kept == (0, "taken")
          and one_read == ((404, "no blob"), (0, "taken")) and gone == (404, "no blob")
          and usage_before.get("files") == 500_000 and usage_after.get("files") == 0,
          f"{unknown} {twice} {kept} {one_read} {gone} {usage_before} {usage_after}")

    # the day's files stand at 500,000 of 800,000: the refused upload's 250,000 came back, or this one would not fit
    third = put(b3, 250_000)
    day_files = put(b4, 60_000)
    large = put("l" + os.urandom(12).hex(), 300_001)
    big = refused(lambda: a.send(p, os.urandom(100_000)))
    bigger = refused(lambda: a.send(p, os.urandom(140_000)))
    messages_full = refused(lambda: a.send(p, os.urandom(30_000)))
    for who in (a, b):
        who.seen(p, max(n for n, _d, _b in who.fetch(p, 0)))
    day = refused(lambda: a.send(p, os.urandom(30_000)))
    small = refused(lambda: a.send(p, os.urandom(1_000)))
    check("342: the bytes of an upload R2 refused come back to the day, so a file still fits; files stop at their "
          "share of the day's bytes while a larger message still goes in the share kept for changes; one file over the "
          "limit is refused as too large; messages waiting stop at their share of the project's bytes; and once the "
          "day's bytes are used a small message (a list of people) still goes while a larger one is refused as the day",
          third == (0, "taken") and day_files == (429, "day files") and large == (413, "too large")
          and big == (0, "taken") and bigger == (0, "taken") and messages_full == (429, "project full")
          and day == (429, "day") and small == (0, "taken"),
          f"{third} {day_files} {large} {big} {bigger} {messages_full} {day} {small}")

    # a file put with its message, fetched by one computer only so often (the abuse plan's M5)
    a._call("POST", f"/p/{p}/messages?blob={b3}", os.urandom(300))
    fetches = [refused(lambda: b.get_blob(p, b3)) for _ in range(4)]
    # files counted by number, an empty one too, never handed back: b1, the refused upload, b2 and b3 are four of six
    empties = [put("e" + os.urandom(12).hex(), 0) for _ in range(3)]
    check("342: one computer fetches a file only so many times, and a project puts only so many files a day, an "
          "empty one counted and a refused upload's number never handed back",
          fetches == [(0, "taken")] * 3 + [(429, "fetched too often")]
          and empties == [(0, "taken"), (0, "taken"), (429, "project files today")], f"{fetches} {empties}")

    # a refused call writes no nonce, so the same call sent once its refusal has gone is taken, and only once
    body = os.urandom(10_000)
    target = a._prefix + f"/p/{p}/messages"
    head = dict(a._headers("POST", target, hashlib.sha256(body).hexdigest()), **{"Content-Length": str(len(body))})

    def send_kept() -> int:
        conn = http.client.HTTPConnection(a._host, a._port, timeout=30)
        try:
            conn.request("POST", target, body=body, headers=head)
            return conn.getresponse().status
        finally:
            conn.close()
    filled = 0
    while send_kept() == 201 and filled < 10:
        filled += 1
        head = dict(a._headers("POST", target, hashlib.sha256(body).hexdigest()), **{"Content-Length": str(len(body))})
    refused_first = send_kept()
    for who in (a, b):
        who.seen(p, max(n for n, _d, _b in who.fetch(p, 0)))
    kept_then = [send_kept(), send_kept()]
    seen_body = json.dumps({"n": 1}).encode()
    seen_target = b._prefix + f"/p/{p}/seen"
    seen_head = dict(b._headers("POST", seen_target, hashlib.sha256(seen_body).hexdigest()),
                     **{"Content-Length": str(len(seen_body)), "Content-Type": "application/json"})

    def seen_kept() -> int:
        conn = http.client.HTTPConnection(b._host, b._port, timeout=30)
        try:
            conn.request("POST", seen_target, body=seen_body, headers=seen_head)
            return conn.getresponse().status
        finally:
            conn.close()
    unmoved = [seen_kept(), seen_kept()]
    check("342: a refused call writes nothing, so the very same call sent once its refusal has gone is taken and then "
          "refused as sent before, and a look that does not move a computer's mark writes nothing either",
          refused_first == 429 and kept_then == [201, 409] and unmoved == [200, 200], f"{refused_first} {kept_then} {unmoved}")

    # small messages have a cap of their own waiting: the 50,000 bytes laid over the relay's 8 MB (W1)
    a.seen(p, max(n for n, _d, _b in a.fetch(p, 0)))
    smalls = [refused(lambda: a.send(p, os.urandom(10_000))) for _ in range(6)]
    over = None
    try:
        a.send(p, os.urandom(10_000))
    except rt.RelayError as exc:
        over = exc
    check("342: small messages no reader has fetched stop at their own cap, refused as the project full, the refusal "
          "naming the computer that has not read them",
          smalls[:4] == [(0, "taken")] * 4 and smalls[4] == (429, "project full") and over is not None
          and over.error == "project full" and over.behind == [b.device],
          f"{smalls} {getattr(over, 'behind', None)} {b.device}")

    # and a count a day: 30 laid over the relay's 500
    b.seen(p, max(n for n, _d, _b in b.fetch(p, 0)))
    counted = []
    for _ in range(40):
        counted.append(refused(lambda: a.send(p, os.urandom(100))))
        if counted[-1] != (0, "taken"):
            break
    check("342: a project's messages stop at the day's count, refused in a word of their own",
          counted[-1] == (429, "day messages") and 1 < len(counted) <= 30, f"{len(counted)} {counted[-1]}")

    r_lead, r_other = (rt.RelayTransport(Ed25519PrivateKey.generate(), url) for _ in range(2))
    r = made_from(rt, r_lead, "198.51.100.9")
    r_lead.set_devices(r, [r_lead.public_key, r_other.public_key])
    relay_day = refused(lambda: r_lead.put_blob(r, "r" + os.urandom(12).hex(), os.urandom(1_000)))
    old_big = refused(lambda: lead.put_blob(project, "q" + os.urandom(12).hex(), os.urandom(1_200_000), 10 ** 9))
    check("342: the relay as a whole takes only so many files a day, refused in a word of its own, and the project made "
          "before the relay was open is never refused by it",
          relay_day == (503, "files today") and old_big == (0, "taken"), f"{relay_day} {old_big}")
    c = rt.RelayTransport(Ed25519PrivateKey.generate(), url)
    q = made_from(rt, c, "198.51.100.7")
    c.set_devices(q, [c.public_key, rt.RelayTransport(Ed25519PrivateKey.generate(), url).public_key])
    ceiling = refused(lambda: c.put_blob(q, "c" + os.urandom(12).hex(), os.urandom(10_000)))
    check("342: the project made before keeps its old limits and the ceiling never refuses it, its bytes still "
          "counted, so a new project's file is refused once the relay's files pass the ceiling",
          old_big == (0, "taken") and ceiling == (503, "relay full"), f"{old_big} {ceiling}")

    v6 = [refused(lambda ip=ip: made_from(rt, rt.RelayTransport(Ed25519PrivateKey.generate(), url), ip))
          for ip in ("2001:db8:1:2::5", "2001:db8:1:2:aa::1", "2001:0db8:0001:0012::9", "2001:db8:1:20::7")]
    last = refused(lambda: made_from(rt, rt.RelayTransport(Ed25519PrivateKey.generate(), url), "192.0.2.1"))
    after = refused(lambda: made_from(rt, rt.RelayTransport(Ed25519PrivateKey.generate(), url), "192.0.2.2"))
    check("342: no code is asked to start a project; one address (an IPv6 /56 written any way) starts three a day "
          "and no more, and the relay as a whole only so many",
          v6[:3] == [(0, "taken")] * 3 and v6[3] == (429, "projects from here") and last == (0, "taken")
          and after == (429, "projects today"), f"{v6} {last} {after}")

    boxes = [os.urandom(16).hex() for _ in range(4)]
    opened = [refused(lambda box=box: a.invite_open(p, box)) for box in boxes]
    answered = refused(lambda: b.invite_post(boxes[0], b"an answer"))
    shut_box = refused(lambda: b.invite_post(boxes[3], b"an answer"))
    check("342: a project's computers open only so many invites a day, an opened invite takes its answers, and one "
          "the relay refused to open takes none",
          opened[:3] == [(0, "taken")] * 3 and opened[3] == (429, "invites today") and answered == (0, "taken")
          and shut_box == (404, "no invite"), f"{opened} {answered} {shut_box}")

    no_key = operator_call(url, "GET", "/operator/usage", None)
    wrong_key = operator_call(url, "GET", "/operator/usage", "not-the-operator-key-at-all")
    by_code = operator_call(url, "GET", "/operator/usage", CODE)
    usage = operator_call(url, "GET", "/operator/usage")[1]
    rows = {r["project"]: r for r in usage.get("projects", [])}
    deleted = operator_call(url, "DELETE", f"/operator/p/{p}")
    after_delete = {r["project"] for r in operator_call(url, "GET", "/operator/usage")[1].get("projects", [])}
    shut = refused(lambda: a.fetch(p, 0))
    check("342: the operator's key alone, never an old operator code, reads each project's bytes, the old project "
          "shown as made before the relay was open with its files added up from its rows, and deletes a project with "
          "its files, which the counter forgets and the relay then does not know",
          no_key[0] == 403 and wrong_key[0] == 403 and by_code[0] == 403
          and (rows.get(project) or {}).get("made_open") is False
          and (rows.get(project) or {}).get("files") == 3 * 1024 * 1024 + 1_200_000
          and (rows.get(p) or {}).get("made_open") is True and usage.get("made_today") == 7
          and usage.get("invites_opened_today") == 3 and usage.get("files_today") == 6
          and usage.get("made_from_addresses") == 5
          and deleted[0] == 200 and deleted[1].get("files", 0) >= 1 and p not in after_delete and project in after_delete
          and shut == (404, "no project"),
          f"{no_key[0]} {wrong_key[0]} {by_code[0]} {rows.get(project)} {usage} {deleted} {shut}")
    closed = operator_call_body(url, "/operator/allow", {"projects": 0})
    none_today = refused(lambda: made_from(rt, rt.RelayTransport(Ed25519PrivateKey.generate(), url), "192.0.2.77"))
    reopened = operator_call_body(url, "/operator/allow", {"projects": 40})
    one_more = refused(lambda: made_from(rt, rt.RelayTransport(Ed25519PrivateKey.generate(), url), "192.0.2.78"))
    by_stranger = operator_call_body(url, "/operator/allow", {"projects": 40}, "not-the-operator-key-at-all")
    check("342: the operator closes the day's new projects and opens it again after they are used up, with the "
          "operator's key alone",
          closed[0] == 200 and none_today == (429, "projects today") and reopened[0] == 200 and one_more == (0, "taken")
          and by_stranger[0] == 403, f"{closed} {none_today} {reopened} {one_more} {by_stranger[0]}")
    return {"later": later, "later_body": later_body, "c": c, "q": q}


def operator_call_body(url: str, route: str, body: dict, key: str = KEY) -> tuple:
    from urllib.parse import urlsplit
    parts = urlsplit(url)
    data = json.dumps(body).encode()
    conn = http.client.HTTPConnection(parts.hostname, parts.port, timeout=30)
    try:
        conn.request("POST", parts.path + route, body=data, headers={"Authorization": f"Bearer {key}",
                                                                    "Content-Type": "application/json",
                                                                    "Content-Length": str(len(data))})
        answer = conn.getresponse()
        return answer.status, json.loads(answer.read() or b"{}")
    finally:
        conn.close()


def rolled_back(rt, url: str, old: dict, new: dict) -> None:
    """The old relay on the storage the new one wrote: what deploy.md's rollback to step A runs on (T7)."""
    lead, other = (rt.RelayTransport(old[k]._key, url) for k in ("lead", "other"))
    project = old["project"]
    came = other.fetch(project, 0)
    back = other.get_blob(project, old["blob"])
    c = rt.RelayTransport(new["c"]._key, url)
    sent = refused(lambda: c.send(new["q"], b"after a rollback"))
    got = c.fetch(new["q"], 0)
    check("342: the old relay started again on the new one's storage reads it: the old project's messages and file "
          "come back whole, and a project the new relay made takes and hands back a message",
          [(n, body) for n, _d, body in came] == [(old["first"], b"made under the old relay"),
                                                  (new["later"], new["later_body"])]
          and back == old["data"] and sent == (0, "taken") and [body for _n, _d, body in got] == [b"after a rollback"],
          f"{[(n, len(b)) for n, _d, b in came]} {sent} {len(got)}")


def alarm(rt, Ed25519PrivateKey, url: str) -> None:
    """A project's alarm, brought to seconds (T1): what is old deleted, read or not, a file no message names swept,
    the sums worked out again so a relay full of messages is not full any more, the alarm stopped once the project
    holds nothing and has taken nothing, and set again by its next message."""
    x = rt.RelayTransport(Ed25519PrivateKey.generate(), url)
    y = rt.RelayTransport(Ed25519PrivateKey.generate(), url)
    project = made_from(rt, x, "192.0.2.50")
    x.set_devices(project, [x.public_key, y.public_key])
    orphan, named = ("a" + os.urandom(12).hex() for _ in range(2))
    x.put_blob(project, orphan, os.urandom(1_000))
    x.put_blob(project, named, os.urandom(1_000))
    x._call("POST", f"/p/{project}/messages?blob={named}", os.urandom(300))
    x.send(project, os.urandom(6_000))
    full = refused(lambda: x.send(project, os.urandom(100)))

    def emptied() -> bool:
        return (x.fetch(project, 0) == [] and refused(lambda: y.get_blob(project, orphan)) == (404, "no blob")
                and refused(lambda: y.get_blob(project, named)) == (404, "no blob"))
    until = time.monotonic() + 30
    while not emptied() and time.monotonic() < until:
        time.sleep(0.5)
    swept = emptied()
    row = usage_of(url, project)
    check("342: a project's alarm deletes what is past its days, read or not, with the file its message names, sweeps "
          "a file no message names, and works its sums out again, so the relay full of messages before is not now",
          full == (503, "relay full") and swept and row.get("files") == 0 and row.get("messages") == 0, f"{full} {row}")
    reported = row.get("reported")
    time.sleep(9)
    still = usage_of(url, project).get("reported")
    taken = refused(lambda: x.send(project, os.urandom(100)))
    until = time.monotonic() + 30
    while x.fetch(project, 0) and time.monotonic() < until:
        time.sleep(0.5)
    check("342: an idle project's alarm stops, so it reports nothing more, and its next message is taken and sets the "
          "alarm again, which deletes it in turn",
          still == reported and taken == (0, "taken") and x.fetch(project, 0) == [],
          f"{reported} {still} {taken}")
