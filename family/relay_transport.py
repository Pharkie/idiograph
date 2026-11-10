# SPDX-License-Identifier: AGPL-3.0-or-later
"""The relay route for Working together (working together, build 3, 8 November 2026): the transport
that passes a project's sealed envelopes through the relay in `relay/`, at idiograph.app or a
university's own.

It has the shape every transport has (transport.py, the keys build's):

    send(project_id, sealed) -> int                      the relay's number for the envelope
    fetch(project_id, after) -> [(n, device, sealed)]    every envelope after n, in order
    listen(project_id, on_new) -> stop                   on_new() whenever something may have come

and what only the relay needs: `make_project` with an operator code, `set_devices` (the lead's list),
`seen`, blobs and the invite mailbox. It seals nothing: what it is handed is sealed already, and it
signs each call with the device's Ed25519 key, as relay/src/worker.js checks. Only the standard
library, and PyCA `cryptography` for the signature, imported when a transport is made so that a
module importing this one never needs it.

The signature is over "<METHOD>\\n<path and query>\\n<X-Time>\\n<X-Nonce>\\n<SHA-256 of the body,
hex>", sent as X-Device (the device id, the first 16 bytes of SHA-256 of the raw public key, in hex),
X-Time (Unix seconds), X-Nonce (16 random bytes in hex, which the relay takes once) and X-Sig
(base64url).
"""
from __future__ import annotations

import base64
import hashlib
import http.client
import json
import os
import secrets
import socket
import ssl
import struct
import threading
import time
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit

RELAY_URL = "https://idiograph.app/relay/v1"
# the relay's own limits (relay/src/worker.js, LIMITS), checked here first so a refusal says why
MAX_MESSAGE = 1536 * 1024
MAX_BLOB = 200 * 1024 * 1024
MAX_INVITE = 4096
TIMEOUT = 30
# how long a live socket stays quiet before it pings, and the longest wait between tries after a fault
PING_EVERY = 25
BACKOFF_MOST = 60
EMPTY = hashlib.sha256(b"").hexdigest()


class RelayError(Exception):
    """A call the relay refused or could not take: `status` is its HTTP status (0 when it was never
    reached) and `error` its one word, such as "removed", "day" or "too large"."""

    def __init__(self, status: int, error: str):
        super().__init__(f"relay {status}: {error}")
        self.status = status
        self.error = error


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def unb64url(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def device_id(public_key: bytes) -> str:
    """The device id of a raw 32-byte Ed25519 public key, as the spec and the relay make it."""
    return hashlib.sha256(public_key).digest()[:16].hex()


def _signing_key(key):
    """An Ed25519 private key from `key`: one already (anything with sign and public_key), or its raw
    32-byte seed."""
    if hasattr(key, "sign") and hasattr(key, "public_key"):
        return key
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    return Ed25519PrivateKey.from_private_bytes(bytes(key))


def _raw_public(key) -> bytes:
    from cryptography.hazmat.primitives import serialization
    return key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


class RelayTransport:
    """One device's way to the relay at `url` (RELAY_URL unless a team runs its own), signing with
    `key`, an Ed25519 private key or its 32-byte seed. Thread-safe: each call opens its own
    connection."""

    def __init__(self, key, url: str = RELAY_URL, timeout: float = TIMEOUT):
        self._key = _signing_key(key)
        self.public_key = _raw_public(self._key)
        self.device = device_id(self.public_key)
        parts = urlsplit(url.rstrip("/"))
        if parts.scheme not in ("https", "http") or not parts.hostname:
            raise ValueError("the relay's address starts https://")
        self._scheme, self._host, self._prefix = parts.scheme, parts.hostname, parts.path
        self._port = parts.port or (443 if parts.scheme == "https" else 80)
        self.timeout = timeout

    # the signed call ------------------------------------------------------------------------------

    def _headers(self, method: str, target: str, body_hash: str) -> dict:
        stamp, nonce = str(int(time.time())), secrets.token_hex(16)
        text = f"{method}\n{target}\n{stamp}\n{nonce}\n{body_hash}".encode("utf-8")
        return {"X-Device": self.device, "X-Time": stamp, "X-Nonce": nonce, "X-Sig": b64url(self._key.sign(text))}

    def _connection(self, timeout: float | None = None):
        if self._scheme == "https":
            return http.client.HTTPSConnection(self._host, self._port, timeout=timeout or self.timeout,
                                               context=ssl.create_default_context())
        return http.client.HTTPConnection(self._host, self._port, timeout=timeout or self.timeout)

    def _call(self, method: str, route: str, body=b"", *, signed: bool = True, headers: dict | None = None,
              body_hash: str | None = None, length: int | None = None, raw: bool = False):
        """One call to `route` under the relay's address. `body` is bytes or an open binary file (with
        `body_hash` and `length` given). Answers the JSON, or the bytes when `raw`, and raises RelayError."""
        target = self._prefix + route
        sent = dict(headers or {})
        if signed:
            sent.update(self._headers(method, target, body_hash or hashlib.sha256(body).hexdigest()))
        if body is not None and method in ("POST", "PUT"):
            sent["Content-Length"] = str(length if length is not None else len(body))
            sent.setdefault("Content-Type", "application/octet-stream")
        conn = self._connection()
        try:
            conn.request(method, target, body=body if method in ("POST", "PUT") else None, headers=sent)
            answer = conn.getresponse()
            data = answer.read()
            status = answer.status
        except (OSError, http.client.HTTPException) as exc:
            raise RelayError(0, type(exc).__name__) from exc
        finally:
            conn.close()
        if status >= 400 or not raw:
            try:
                parsed = json.loads(data.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                parsed = {"error": "not the relay"}
            if status >= 400:
                raise RelayError(status, str(parsed.get("error", "refused")))
            return parsed
        return data

    def _json(self, method: str, route: str, data: dict):
        return self._call(method, route, json.dumps(data, separators=(",", ":")).encode("utf-8"),
                          headers={"Content-Type": "application/json"})

    # projects and devices --------------------------------------------------------------------------

    def make_project(self, operator_code: str) -> str:
        """A new project on the relay, this device its lead, made with one of the operator's codes.
        Answers the relay's random project id (32 hex)."""
        return self._json("POST", "/projects", {"code": operator_code, "key": b64url(self.public_key)})["project"]

    def set_devices(self, project_id: str, public_keys: list[bytes], lead: str | None = None) -> dict:
        """The lead's list of every device let in, as raw public keys, this one among them. A device on
        the relay's list and not on this one is refused from now on. `lead` hands the role to another
        device on the list by its id. Answers {devices, removed, lead}."""
        ask = {"devices": [b64url(k) for k in public_keys]}
        if lead is not None:
            ask["lead"] = lead
        return self._json("PUT", f"/p/{project_id}/devices", ask)

    # the transport's shape -------------------------------------------------------------------------

    def send(self, project_id: str, sealed: bytes) -> int:
        """One sealed envelope to the project's mailbox. Answers the relay's number for it."""
        if len(sealed) > MAX_MESSAGE:
            raise RelayError(413, "too large")
        return int(self._call("POST", f"/p/{project_id}/messages", bytes(sealed))["n"])

    def fetch(self, project_id: str, after: int) -> list[tuple[int, str, bytes]]:
        """Every envelope after the relay's number `after`, oldest first, as (n, sender's device id,
        sealed), page by page until there are no more."""
        out: list[tuple[int, str, bytes]] = []
        while True:
            page = self._call("GET", f"/p/{project_id}/messages?after={int(after)}")
            for m in page.get("messages", []):
                out.append((int(m["n"]), str(m["device"]), unb64url(m["body"])))
            if not page.get("more") or not page.get("messages"):
                return out
            after = out[-1][0]

    def seen(self, project_id: str, n: int) -> int:
        """This device has read everything up to `n`. What every device has read is deleted from the
        relay. Answers how many messages that dropped."""
        return int(self._json("POST", f"/p/{project_id}/seen", {"n": int(n)}).get("dropped", 0))

    def listen(self, project_id: str, on_new: Callable[[], None]) -> Callable[[], None]:
        """Calls on_new() when the project's live socket says a message came, and once each time it
        (re)connects, since something may have come while it was away. Reconnects after a fault,
        waiting longer each time up to a minute. Answers a stop, which returns once the thread is
        done."""
        live = _Live(self, project_id, on_new)
        live.start()
        return live.stop

    # blobs ------------------------------------------------------------------------------------------

    def put_blob(self, project_id: str, blob: str, sealed) -> int:
        """A sealed blob, bytes or the path of a file holding them, under the name `blob` (16 to 64
        letters, digits, - and _). Answers its size."""
        if isinstance(sealed, (str, Path)):
            path = Path(sealed)
            size = path.stat().st_size
            digest = hashlib.sha256()
            with path.open("rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    digest.update(chunk)
            if size > MAX_BLOB:
                raise RelayError(413, "too large")
            with path.open("rb") as fh:
                return int(self._call("PUT", f"/p/{project_id}/blobs/{blob}", fh, body_hash=digest.hexdigest(), length=size,
                                      headers={"X-Content-SHA256": digest.hexdigest()})["bytes"])
        data = bytes(sealed)
        if len(data) > MAX_BLOB:
            raise RelayError(413, "too large")
        digest = hashlib.sha256(data).hexdigest()
        return int(self._call("PUT", f"/p/{project_id}/blobs/{blob}", data, body_hash=digest,
                              headers={"X-Content-SHA256": digest})["bytes"])

    def get_blob(self, project_id: str, blob: str) -> bytes:
        return self._call("GET", f"/p/{project_id}/blobs/{blob}", raw=True)

    # the invite's mailbox, unsigned ----------------------------------------------------------------

    def invite_post(self, invite: str, sealed: bytes) -> int:
        """A sealed join answer to the invite's mailbox (its id, 32 hex, from the invite's secret).
        Answers its place in the mailbox."""
        if len(sealed) > MAX_INVITE:
            raise RelayError(413, "too large")
        return int(self._call("POST", f"/invites/{invite}", bytes(sealed), signed=False)["k"])

    def invite_fetch(self, invite: str, after: int = 0) -> list[tuple[int, bytes]]:
        page = self._call("GET", f"/invites/{invite}?after={int(after)}", signed=False)
        return [(int(a["k"]), unb64url(a["body"])) for a in page.get("answers", [])]


class _Live(threading.Thread):
    """The live socket: a WebSocket client of the standard library's alone, enough for the relay's
    one-way "new N" and its ping and pong. Frames from here are masked, as RFC 6455 asks of a client."""

    def __init__(self, relay: RelayTransport, project_id: str, on_new: Callable[[], None]):
        super().__init__(daemon=True, name=f"relay-live-{project_id[:8]}")
        self.relay, self.project_id, self.on_new = relay, project_id, on_new
        self._halt = threading.Event()
        self._sock = None
        self._lock = threading.Lock()
        self.connects = 0

    def stop(self) -> None:
        self._halt.set()
        with self._lock:
            sock = self._sock
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        if threading.current_thread() is not self:
            self.join(timeout=5)

    def _tell(self) -> None:
        try:
            self.on_new()
        except Exception:
            pass  # a listener's fault is its own, the socket keeps listening

    def run(self) -> None:
        wait = 1
        while not self._halt.is_set():
            try:
                self._session()
                wait = 1
            except RelayError as exc:
                if exc.status in (401, 403, 404, 410):
                    wait = BACKOFF_MOST  # refused, not broken: try again rarely
            except (OSError, ValueError):
                pass
            finally:
                with self._lock:
                    if self._sock is not None:
                        try:
                            self._sock.close()
                        except OSError:
                            pass
                    self._sock = None
            if self._halt.wait(wait):
                return
            wait = min(wait * 2, BACKOFF_MOST)

    def _open(self):
        r = self.relay
        raw = socket.create_connection((r._host, r._port), timeout=r.timeout)
        if r._scheme == "https":
            raw = ssl.create_default_context().wrap_socket(raw, server_hostname=r._host)
        return raw

    def _session(self) -> None:
        r = self.relay
        target = f"{r._prefix}/p/{self.project_id}/live"
        sock = self._open()
        with self._lock:
            self._sock = sock
        if self._halt.is_set():
            return
        nonce = base64.b64encode(os.urandom(16)).decode("ascii")
        head = {"Host": r._host if r._port in (80, 443) else f"{r._host}:{r._port}", "Upgrade": "websocket",
                "Connection": "Upgrade", "Sec-WebSocket-Key": nonce, "Sec-WebSocket-Version": "13"}
        head.update(r._headers("GET", target, EMPTY))
        sock.sendall((f"GET {target} HTTP/1.1\r\n" + "".join(f"{k}: {v}\r\n" for k, v in head.items()) + "\r\n").encode("ascii"))
        reply = b""
        while b"\r\n\r\n" not in reply:
            chunk = sock.recv(4096)
            if not chunk:
                raise OSError("closed")
            reply += chunk
            if len(reply) > 65536:
                raise ValueError("header")
        header, rest = reply.split(b"\r\n\r\n", 1)
        status = int(header.split(b" ", 2)[1])
        if status != 101:
            raise RelayError(status, "live")
        accept = base64.b64encode(hashlib.sha1((nonce + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
        if accept.encode() not in header:
            raise ValueError("handshake")
        self.connects += 1
        self._tell()
        frames = _Frames(sock, rest)
        sock.settimeout(PING_EVERY)
        while not self._halt.is_set():
            try:
                op, payload = frames.next()
            except socket.timeout:
                _send_frame(sock, 0x1, b"ping")
                continue
            if op == 0x8:
                return
            if op == 0x9:
                _send_frame(sock, 0xA, payload)
            elif op == 0x1 and payload.startswith(b"new "):
                self._tell()


class _Frames:
    """The frames read from a socket, the bytes already read after the handshake first."""

    def __init__(self, sock, start: bytes):
        self.sock, self.buf = sock, bytearray(start)

    def _need(self, n: int) -> bytes:
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise OSError("closed")
            self.buf += chunk
        out = bytes(self.buf[:n])
        del self.buf[:n]
        return out

    def next(self) -> tuple[int, bytes]:
        b0, b1 = self._need(2)
        size = b1 & 0x7F
        if size == 126:
            size = struct.unpack(">H", self._need(2))[0]
        elif size == 127:
            size = struct.unpack(">Q", self._need(8))[0]
        if size > 1 << 20:
            raise ValueError("frame")
        mask = self._need(4) if b1 & 0x80 else None
        payload = self._need(size)
        if mask:
            payload = bytes(c ^ mask[i % 4] for i, c in enumerate(payload))
        return b0 & 0x0F, payload


def _send_frame(sock, op: int, payload: bytes) -> None:
    mask = secrets.token_bytes(4)
    size = len(payload)
    head = bytes([0x80 | op])
    if size < 126:
        head += bytes([0x80 | size])
    elif size < 1 << 16:
        head += bytes([0x80 | 126]) + struct.pack(">H", size)
    else:
        head += bytes([0x80 | 127]) + struct.pack(">Q", size)
    sock.sendall(head + mask + bytes(c ^ mask[i % 4] for i, c in enumerate(payload)))


# the route as Working together's team module asks for it (transport.py's `register`, glue of 8 November 2026) ----

INVITE_PREFIX = "invite/"


class TeamRelay:
    """The relay as team.py's transport: the project's mailbox through the signed calls, and an invite's
    (`invite/<id>`, as transport.py names it) through the relay's unsigned invite mailbox, where no answer
    names its sender.

    The team layer names a project by its team id, team.json's `team`, which the relay never sees. The relay
    names it by the id it answered when the lead made it there with an operator code (relaywire, 9 November
    2026), kept in the lead's signed list of people as `relay.project`, so every member has it. Here the one
    becomes the other: a call under the team id goes to the relay's project, refused before it leaves while
    the project has none, and any other id goes as it is."""

    def __init__(self, relay: RelayTransport, team: str = "", project: str = ""):
        self.relay = relay
        self.device = relay.device
        self.team = team
        self.project = project

    def __getattr__(self, name):
        return getattr(self.relay, name)

    @staticmethod
    def _invite(project_id: str) -> str | None:
        return project_id[len(INVITE_PREFIX):] if project_id.startswith(INVITE_PREFIX) else None

    def where(self, project_id: str) -> str:
        """The relay's id for a project the team layer names."""
        if self.team and project_id == self.team:
            if not self.project:
                raise RelayError(404, "no project")
            return self.project
        return project_id

    def send(self, project_id: str, sealed: bytes) -> int:
        invite = self._invite(project_id)
        if invite is not None:
            return self.relay.invite_post(invite, sealed)
        return self.relay.send(self.where(project_id), sealed)

    def fetch(self, project_id: str, after: int) -> list[tuple[int, str, bytes]]:
        invite = self._invite(project_id)
        if invite is not None:
            return [(k, "", body) for k, body in self.relay.invite_fetch(invite, after)]
        return self.relay.fetch(self.where(project_id), after)

    def listen(self, project_id: str, on_new: Callable[[], None]) -> Callable[[], None]:
        if self._invite(project_id) is not None:
            return lambda: None
        return self.relay.listen(self.where(project_id), on_new)

    def seen(self, project_id: str, n: int) -> int:
        return self.relay.seen(self.where(project_id), n)

    def set_devices(self, project_id: str, public_keys: list[bytes], lead: str | None = None) -> dict:
        return self.relay.set_devices(self.where(project_id), public_keys, lead)

    def put_blob(self, project_id: str, blob: str, sealed) -> int:
        return self.relay.put_blob(self.where(project_id), blob, sealed)

    def get_blob(self, project_id: str, blob: str) -> bytes:
        return self.relay.get_blob(self.where(project_id), blob)


def relay_url(team: dict) -> str:
    """The relay a team uses: the address team.json names (`relay_url`, a team running its own), else the one the
    lead's list of people names, else idiograph.app's."""
    team = team or {}
    held = ((team.get("roster") or {}).get("relay") or {}) if isinstance(team.get("roster"), dict) else {}
    return str(team.get("relay_url") or (held.get("url") if isinstance(held, dict) else "") or RELAY_URL)


def team_factory(device: dict, team: dict) -> TeamRelay:
    """`factory(device, team)` for transport.register: the relay at the team's own address or idiograph.app
    (`relay_url`), signed with this install's device key (team.py's `device`, raw seed in standard base64), the team's
    id mapped to the relay's project id the list of people names."""
    team = team or {}
    seed = base64.b64decode(str(device.get("sign") or ""))
    held = ((team.get("roster") or {}).get("relay") or {}) if isinstance(team.get("roster"), dict) else {}
    project = str(held.get("project") or "") if isinstance(held, dict) else ""
    return TeamRelay(RelayTransport(seed, relay_url(team)), str(team.get("team") or ""), project)
