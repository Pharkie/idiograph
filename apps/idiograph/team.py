"""Working together's keys (wtkeys, 8 November 2026, the first build of the design of that day, Adam's choices about
19:10 by dialog: all the spec's defaults, PyCA `cryptography` in the server).

Working together is off in every project until it is turned on in Project settings, and while it is off nothing here
is read or written: no key is made, no file is written, and the section shows its one tick alone.

**The device.** Turning it on makes this install's two key pairs once, Ed25519 to sign and X25519 to receive, and
keeps them in `team-device.json` beside the app's settings (`server.CONFIG_PATH`'s folder, the app's data folder in
an installed app, `~/Library/Application Support/Idiograph` on a Mac), mode 600, never in a project and never in a
sent copy. The device's id is the first 16 bytes of SHA-256 of its signing key, in hex. The command line and the MCP
server read the same file, so an agent signs as its user's device. The same file keeps each team's project keys, by
epoch, and the invites this device made, with their secrets.

**The team.** `team.json` at the project's root (left out of a sent copy, `project_pack.LEFT_OUT`) holds whether it
is on, the route (the relay or a shared folder), the folder, whether recordings go, this install's member id and the
roster. The roster lists the members, their devices' public keys, their roles, each participant's owner and the GETs
board's, and the project key of its epoch sealed to every device on it. It is numbered, one higher each time, and
signed by a device of the lead's: a roster signed by any other device, or numbered no higher than the one held, is
refused.

**Sealing.** A message to the team is an envelope `{v, project, epoch, device, seq, sealed}`, `sealed` the inner
message `{id, kind, member, device, sent, body, sig}` padded to 4, 16, 64, 256 KB or 1 MB and sealed under the
epoch's key with the envelope's other fields as associated data. The library has no XChaCha20, so each seal takes a
fresh 24-byte nonce, derives its own key from the epoch's with HKDF-SHA256 over that nonce, and seals with
ChaCha20-Poly1305 (the spec's fallback, section 3). A key sealed to one device is an ephemeral X25519 exchange,
HKDF-SHA256 and ChaCha20-Poly1305. `open_envelope` refuses a tampered envelope, a device not on the roster, a bad
signature, and a roster from anyone but the lead.

**Invite and join.** An invite is a one-time 16-byte secret, shown as twelve words from `team_words.txt` (2,048
plain words, 11 bits each, the last four bits a check) and as a link whose part after `#` is the same words. Its
mailbox id and key come from the secret by HKDF. The lead's install posts its device's keys there, the joiner posts
his name and keys, and both compute the same six digits from SHA-256 of the secret and both devices' keys. They
match adds him to the roster with the project key sealed to his device and posts it back, and They differ throws the
answer away. An invite works once, for seven days, and a second join is refused.

Every message goes through a transport of `transport.py`'s shape. The ops here write the project's files only
through the route in `idiograph_routes.api_team`, under the project's lock, with its History.
"""
from __future__ import annotations

import base64
import contextlib
import hashlib
import json
import os
import secrets
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import boot
import i18n
import locks
import server as srv
import transport as transport_mod

FILE = "team.json"
DEVICE_FILE = "team-device.json"
# where a dropped message is noted, at the project's root, left out of a sent copy
LOG_DIR = ".idiograph-team"
SCHEMA = 1
INVITE_DAYS = 7
LINK_BASE = "https://idiograph.app/join"
ROUTES = ("relay", "folder")
PADS = (4096, 16384, 65536, 262144, 1048576)
WORDS_FILE = "team_words.txt"
NAME_MOST = 60
# the kinds of message a member may send, the roster the lead's alone (spec, section 4)
KINDS = ("roster", "version", "gets_version", "review_asked", "comment", "thread_state", "suggestion", "board",
         "review", "answer", "hand_over", "take_over", "seen", "devices")
# where this build's own reading of the team's messages has got to, in the device file's team (wtdevices)
TAKEN = "members_after"
# a stand-in for the device file's place, for the suite's two installs in one process
DEVICE_PATH: Path | None = None


class TeamError(ValueError):
    """A refusal, in the reader's language, with a code a check can test in place of its words."""

    def __init__(self, message: str, code: str = ""):
        super().__init__(message)
        self.code = code


# ------------------------------------------------------------------ the library

def lib():
    """PyCA `cryptography`'s parts this module uses, imported only when Working together is used, so a setup from
    before it was pinned starts as it always did and says what it needs when Working together is turned on."""
    try:
        from cryptography.exceptions import InvalidSignature, InvalidTag
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
        from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    except ImportError:
        raise TeamError(i18n.t("team.refused.needs_library"), "needs_library") from None
    return {"InvalidSignature": InvalidSignature, "InvalidTag": InvalidTag, "hashes": hashes,
            "serialization": serialization, "ed25519": ed25519, "x25519": x25519, "aead": ChaCha20Poly1305,
            "HKDF": HKDF}


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def unb64(text) -> bytes:
    try:
        return base64.b64decode(str(text or ""), validate=True)
    except (ValueError, TypeError):
        raise TeamError(i18n.t("team.refused.tampered"), "tampered") from None


def canon(obj) -> bytes:
    """The one byte form a signature and associated data are taken over."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def hkdf(ikm: bytes, salt: bytes, info: bytes, n: int = 32) -> bytes:
    c = lib()
    return c["HKDF"](algorithm=c["hashes"].SHA256(), length=n, salt=salt, info=info).derive(ikm)


def raw_public(key) -> bytes:
    s = lib()["serialization"]
    return key.public_key().public_bytes(s.Encoding.Raw, s.PublicFormat.Raw)


def raw_private(key) -> bytes:
    s = lib()["serialization"]
    return key.private_bytes(s.Encoding.Raw, s.PrivateFormat.Raw, s.NoEncryption())


# ------------------------------------------------------------------ sealing

def aead_seal(key: bytes, plain: bytes, aad: bytes = b"") -> bytes:
    """`plain` sealed under `key`: a fresh 24-byte nonce, a key of its own from HKDF over it, ChaCha20-Poly1305."""
    nonce = secrets.token_bytes(24)
    sub = hkdf(key, nonce, b"idiograph v1 seal")
    return nonce + lib()["aead"](sub).encrypt(bytes(12), plain, aad)


def aead_open(key: bytes, sealed: bytes, aad: bytes = b"") -> bytes:
    c = lib()
    if len(sealed) < 24 + 16:
        raise TeamError(i18n.t("team.refused.tampered"), "tampered")
    sub = hkdf(key, sealed[:24], b"idiograph v1 seal")
    try:
        return c["aead"](sub).decrypt(bytes(12), sealed[24:], aad)
    except c["InvalidTag"]:
        raise TeamError(i18n.t("team.refused.tampered"), "tampered") from None


def seal_to(box_public: str, plain: bytes) -> bytes:
    """`plain` sealed to one device's X25519 key: an ephemeral key's exchange, HKDF, ChaCha20-Poly1305."""
    c = lib()
    them = unb64(box_public)
    eph = c["x25519"].X25519PrivateKey.generate()
    eph_pub = raw_public(eph)
    shared = eph.exchange(c["x25519"].X25519PublicKey.from_public_bytes(them))
    key = hkdf(shared, eph_pub + them, b"idiograph v1 sealed to a device")
    return eph_pub + c["aead"](key).encrypt(bytes(12), plain, b"")


def open_sealed(dev: dict, sealed: bytes) -> bytes:
    c = lib()
    if len(sealed) < 32 + 16:
        raise TeamError(i18n.t("team.refused.tampered"), "tampered")
    mine = c["x25519"].X25519PrivateKey.from_private_bytes(unb64(dev["box"]))
    shared = mine.exchange(c["x25519"].X25519PublicKey.from_public_bytes(sealed[:32]))
    key = hkdf(shared, sealed[:32] + raw_public(mine), b"idiograph v1 sealed to a device")
    try:
        return c["aead"](key).decrypt(bytes(12), sealed[32:], b"")
    except c["InvalidTag"]:
        raise TeamError(i18n.t("team.refused.tampered"), "tampered") from None


def sign(dev: dict, data: bytes) -> str:
    c = lib()
    return b64(c["ed25519"].Ed25519PrivateKey.from_private_bytes(unb64(dev["sign"])).sign(data))


def verify(sign_public: str, data: bytes, sig: str) -> bool:
    c = lib()
    try:
        c["ed25519"].Ed25519PublicKey.from_public_bytes(unb64(sign_public)).verify(unb64(sig), data)
        return True
    except (c["InvalidSignature"], TeamError, ValueError):
        return False


def signed(dev: dict, obj: dict) -> dict:
    """`obj` with its `sig`, this device's signature over the rest."""
    body = {k: v for k, v in obj.items() if k != "sig"}
    return dict(body, sig=sign(dev, canon(body)))


def signed_by(sign_public: str, obj: dict) -> bool:
    return isinstance(obj, dict) and verify(sign_public, canon({k: v for k, v in obj.items() if k != "sig"}),
                                            str(obj.get("sig") or ""))


def pad(data: bytes) -> bytes:
    """The bytes with their length first, padded to the next of 4, 16, 64, 256 KB or 1 MB, so a size says little."""
    whole = len(data) + 4
    size = next((p for p in PADS if p >= whole), None)
    if size is None:
        raise TeamError(i18n.t("team.refused.too_large"), "too_large")
    return len(data).to_bytes(4, "big") + data + bytes(size - whole)


def unpad(data: bytes) -> bytes:
    if len(data) < 4:
        raise TeamError(i18n.t("team.refused.tampered"), "tampered")
    n = int.from_bytes(data[:4], "big")
    if n > len(data) - 4:
        raise TeamError(i18n.t("team.refused.tampered"), "tampered")
    return data[4:4 + n]


# ------------------------------------------------------------------ the device

def device_path() -> Path:
    return Path(DEVICE_PATH) if DEVICE_PATH else Path(srv.CONFIG_PATH).parent / DEVICE_FILE


def load_device_file() -> dict | None:
    """The device file, None when there is none. One there that will not read is refused as busy
    (`locks.read_json`), never taken as none, which would make new keys or drop the team's (teamflake)."""
    data = locks.read_json(device_path())
    return data if isinstance(data, dict) and isinstance(data.get("device"), dict) else None


# the device file's reads and writes as one, across this server's threads (the looks and a request each number
# their messages) and, by a lock file beside it, across the command line and the MCP server (teamflake)
_DEVICE_RUN = threading.RLock()
_DEVICE_DEPTH = [0]


@contextlib.contextmanager
def device_held():
    with _DEVICE_RUN:
        _DEVICE_DEPTH[0] += 1
        try:
            if _DEVICE_DEPTH[0] > 1:
                yield
            else:
                with locks.held(device_path().with_name(device_path().name + ".lock")):
                    yield
        finally:
            _DEVICE_DEPTH[0] -= 1


def save_device_file(data: dict) -> None:
    """The device file written whole through a new name renamed into place, readable by its owner alone."""
    target = device_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = locks.new_tmp(target)
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as out:
        out.write(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    os.replace(tmp, target)
    try:
        os.chmod(target, 0o600)
    except OSError:
        pass


def device_id(sign_public: bytes) -> str:
    return hashlib.sha256(sign_public).digest()[:16].hex()


def device(make: bool = False) -> dict | None:
    """This install's device: `{"id", "sign", "box", "sign_pub", "box_pub", "made"}`, made once with `make` and kept,
    or None when it has none."""
    data = load_device_file()
    if data is not None:
        return data["device"]
    if not make:
        return None
    dev = new_device()
    save_device_file({"schema": SCHEMA, "device": dev, "teams": {}})
    return dev


def new_device() -> dict:
    """A device's two key pairs, made in memory and not kept: `device(make=True)` keeps one at once, and turning on
    with a relay code keeps it only once the relay has taken the code (relaywire)."""
    c = lib()
    sk = c["ed25519"].Ed25519PrivateKey.generate()
    bk = c["x25519"].X25519PrivateKey.generate()
    pub = raw_public(sk)
    return {"id": device_id(pub), "sign": b64(raw_private(sk)), "box": b64(raw_private(bk)),
            "sign_pub": b64(pub), "box_pub": b64(raw_public(bk)), "made": now_iso(), "computer": computer_name()}


def computer_name() -> str:
    """This computer's own name as the system has it, "Ada's MacBook Air" for Ada-s-MacBook-Air.local, so a member
    with two can tell them apart in People. It travels sealed, inside the list of people, never to the relay."""
    import socket
    try:
        name = socket.gethostname().split(".")[0]
    except OSError:
        name = ""
    return one_line(name.replace("-s-", "'s ").replace("-", " ").replace("_", " "))[:NAME_MOST]


def public(dev: dict) -> dict:
    out = {"id": dev["id"], "sign": dev["sign_pub"], "box": dev["box_pub"]}
    name = dev.get("computer") or computer_name()
    return dict(out, name=name) if name else out


def held_team(team: str) -> dict:
    data = load_device_file() or {}
    return dict((data.get("teams") or {}).get(team) or {})


def keep_team(team: str, held: dict) -> None:
    with device_held():
        data = load_device_file()
        if data is None:
            raise TeamError(i18n.t("team.refused.no_device"), "no_device")
        data.setdefault("teams", {})[team] = held
        save_device_file(data)


def keep_key(team: str, epoch: int, key: bytes) -> None:
    with device_held():
        held = held_team(team)
        held.setdefault("keys", {})[str(int(epoch))] = b64(key)
        keep_team(team, held)


def project_key(team: str, epoch: int | None = None) -> bytes | None:
    keys = held_team(team).get("keys") or {}
    if epoch is None:
        epoch = max((int(k) for k in keys), default=0)
    got = keys.get(str(int(epoch)))
    return unb64(got) if got else None


def project_keys(team: str) -> dict:
    return {int(k): unb64(v) for k, v in (held_team(team).get("keys") or {}).items()}


# ------------------------------------------------------------------ the roster

def roster_members(roster: dict) -> list[dict]:
    return [m for m in (roster or {}).get("members") or [] if isinstance(m, dict)]


def member_of(roster: dict, member: str) -> dict | None:
    return next((m for m in roster_members(roster) if m.get("id") == member), None)


def device_on(roster: dict, dev_id: str) -> tuple[dict, dict] | tuple[None, None]:
    for m in roster_members(roster):
        for d in m.get("devices") or []:
            if d.get("id") == dev_id:
                return m, d
    return None, None


def lead_devices(roster: dict) -> dict:
    lead = member_of(roster, str((roster or {}).get("lead") or "")) or {}
    return {d["id"]: d for d in lead.get("devices") or [] if isinstance(d, dict) and d.get("id")}


def sign_roster(dev: dict, roster: dict) -> dict:
    """The roster signed by this device, which must be the lead's."""
    body = dict(roster, signed_by=dev["id"])
    body.pop("sig", None)
    return signed(dev, body)


def check_roster(roster: dict, lead_keys: dict | None = None, held_n: int = 0) -> dict:
    """The roster when it is signed by a device of its lead, numbered higher than `held_n`, and, given the lead's
    devices as this install knew them (`lead_keys`, {id: device}), signed by one of those. Refused otherwise."""
    if not isinstance(roster, dict) or not isinstance(roster.get("n"), int):
        raise TeamError(i18n.t("team.refused.tampered"), "tampered")
    signer = str(roster.get("signed_by") or "")
    leads = lead_keys if lead_keys is not None else lead_devices(roster)
    d = leads.get(signer)
    if d is None or not signed_by(d["sign"], roster):
        raise TeamError(i18n.t("team.refused.roster_not_lead"), "roster_not_lead")
    if lead_keys is None and signer not in lead_devices(roster):
        raise TeamError(i18n.t("team.refused.roster_not_lead"), "roster_not_lead")
    if roster["n"] <= held_n:
        raise TeamError(i18n.t("team.refused.roster_old"), "roster_old")
    return roster


def seal_keys(key: bytes, roster: dict) -> dict:
    """The epoch's key sealed to every device on the roster."""
    return {d["id"]: b64(seal_to(d["box"], key)) for m in roster_members(roster) for d in m.get("devices") or []}


def open_key(dev: dict, roster: dict) -> bytes | None:
    got = (roster.get("keys") or {}).get(dev["id"])
    return open_sealed(dev, unb64(got)) if got else None


# ------------------------------------------------------------------ envelopes

def seal_envelope(team: str, epoch: int, key: bytes, dev: dict, member: str, seq: int, kind: str, body) -> bytes:
    """One message to the team as the bytes a transport carries."""
    inner = signed(dev, {"id": uuid.uuid4().hex, "kind": kind, "member": member, "device": dev["id"],
                         "sent": now_iso(), "body": body})
    head = {"v": 1, "project": team, "epoch": int(epoch), "device": dev["id"], "seq": int(seq)}
    sealed = aead_seal(key, pad(canon(inner)), canon(head))
    return canon(dict(head, sealed=b64(sealed)))


def open_envelope(raw: bytes, roster: dict, keys: dict) -> dict:
    """The inner message of one envelope, when its seal holds under its epoch's key, its device is on the roster, its
    signature is that device's, and its member may send its kind (a roster the lead's alone). Refused otherwise."""
    try:
        env = json.loads(raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw)
    except (ValueError, UnicodeDecodeError):
        raise TeamError(i18n.t("team.refused.tampered"), "tampered") from None
    if not isinstance(env, dict) or env.get("v") != 1:
        raise TeamError(i18n.t("team.refused.tampered"), "tampered")
    head = {k: env.get(k) for k in ("v", "project", "epoch", "device", "seq")}
    key = keys.get(int(env.get("epoch") or 0)) if isinstance(env.get("epoch"), int) else None
    if key is None:
        raise TeamError(i18n.t("team.refused.no_key"), "no_key")
    inner = json.loads(unpad(aead_open(key, unb64(env.get("sealed")), canon(head))).decode("utf-8"))
    member, d = device_on(roster, str(env.get("device") or ""))
    if d is None or inner.get("device") != env.get("device") or inner.get("member") != member.get("id"):
        raise TeamError(i18n.t("team.refused.not_on_roster"), "not_on_roster")
    if not signed_by(d["sign"], inner):
        raise TeamError(i18n.t("team.refused.bad_signature"), "bad_signature")
    if inner.get("kind") not in KINDS or (inner.get("kind") == "roster" and member.get("id") != roster.get("lead")):
        raise TeamError(i18n.t("team.refused.kind_not_allowed"), "kind_not_allowed")
    return inner


def note_dropped(root: Path, why: str, device_from: str = "") -> None:
    """A message dropped, noted in `.idiograph-team/log.jsonl` at the project's root."""
    folder = Path(root) / LOG_DIR
    try:
        folder.mkdir(exist_ok=True)
        with open(folder / "log.jsonl", "a", encoding="utf-8", newline="\n") as out:
            out.write(json.dumps({"at": now_iso(), "dropped": why, "device": device_from}) + "\n")
    except OSError:
        pass


# ------------------------------------------------------------------ the words and the check code

def word_list() -> list[str]:
    words = boot.resource(WORDS_FILE).read_text(encoding="utf-8").split()
    if len(words) != 2048:
        raise TeamError(i18n.t("team.refused.tampered"), "tampered")
    return words


def secret_words(secret: bytes) -> list[str]:
    """Sixteen bytes as twelve words: 128 bits, then the first four bits of their SHA-256 as a check."""
    words = word_list()
    bits = int.from_bytes(secret, "big") << 4 | hashlib.sha256(secret).digest()[0] >> 4
    return [words[(bits >> (11 * (11 - i))) & 0x7FF] for i in range(12)]


def words_secret(text: str) -> bytes:
    """The secret from the twelve words, or from a link whose part after # holds them. Refused when a word is not on
    the list, there are not twelve, or the check fails."""
    text = str(text or "").strip()
    if "#" in text:
        text = text.split("#", 1)[1]
    given = [w for w in text.replace("-", " ").replace(",", " ").lower().split() if w]
    index = {w: i for i, w in enumerate(word_list())}
    if len(given) != 12 or any(w not in index for w in given):
        raise TeamError(i18n.t("team.refused.bad_words"), "bad_words")
    bits = 0
    for w in given:
        bits = bits << 11 | index[w]
    secret = (bits >> 4).to_bytes(16, "big")
    if bits & 0xF != hashlib.sha256(secret).digest()[0] >> 4:
        raise TeamError(i18n.t("team.refused.bad_words"), "bad_words")
    return secret


def invite_link(words: list[str], relay: str = "") -> str:
    """The invite's link, its words after #, and before them, for a team running its own relay, that relay's address,
    so the one joining reaches the invite there (relaywire)."""
    from urllib.parse import quote
    return f"{LINK_BASE}{'?relay=' + quote(relay, safe='') if relay else ''}#{'-'.join(words)}"


def link_relay(text: str) -> str:
    """The relay's address a link carries before its #, "" when it carries none."""
    from urllib.parse import parse_qs, urlsplit
    head = str(text or "").strip().split("#", 1)[0]
    if "?" not in head:
        return ""
    got = (parse_qs(urlsplit(head).query).get("relay") or [""])[0].strip()
    return got if got.startswith(("https://", "http://")) else ""


def invite_id(secret: bytes) -> str:
    return hkdf(secret, b"", b"idiograph v1 invite id", 16).hex()


def invite_key(secret: bytes) -> bytes:
    return hkdf(secret, b"", b"idiograph v1 invite key")


def mailbox(inv: str) -> str:
    """An invite's mailbox as a transport names it (see transport.py)."""
    return f"{transport_mod.INVITE_PREFIX}{inv}"


def check_code(secret: bytes, a: dict, b: dict) -> str:
    """The six digits both screens show, from SHA-256 of the secret and both devices' public keys, the same on
    either side whichever is first."""
    pair = sorted([canon({"sign": a["sign"], "box": a["box"]}), canon({"sign": b["sign"], "box": b["box"]})])
    digest = hashlib.sha256(b"idiograph v1 check code" + secret + pair[0] + pair[1]).digest()
    n = int.from_bytes(digest[:8], "big") % 1_000_000
    return f"{n:06d}"[:3] + " " + f"{n:06d}"[3:]


# ------------------------------------------------------------------ team.json

def team_path(root: Path) -> Path:
    return Path(root) / FILE


def read_team(root: Path) -> dict | None:
    """team.json, None when there is none. One there that will not read is refused as busy (`locks.read_json`),
    never taken as Working together off (teamflake)."""
    data = locks.read_json(team_path(root))
    if not isinstance(data, dict):
        return None
    # Send through is the lead's choice alone: a member's install goes by the route in the lead's signed list
    roster = data.get("roster") if isinstance(data.get("roster"), dict) else {}
    if roster.get("route") in ROUTES and str(data.get("member") or "") != str(roster.get("lead") or ""):
        data["route"] = roster["route"]
    return data


def write_team(root: Path, data: dict) -> None:
    target = team_path(root)
    tmp = locks.new_tmp(target)
    tmp.write_text(json.dumps(dict(data, schema=SCHEMA), indent=1, ensure_ascii=False) + "\n", encoding="utf-8",
                   newline="\n")
    os.replace(tmp, target)


def is_on(root: Path) -> bool:
    data = read_team(root)
    return bool(data and data.get("on") is True)


def one_line(text) -> str:
    return " ".join(str(text or "").split())


def name_given(text) -> str:
    name = one_line(text)[:NAME_MOST]
    if not name:
        raise TeamError(i18n.t("team.refused.no_name"), "no_name")
    return name


def transport_for(data: dict, dev: dict):
    return transport_mod.for_team(data.get("route") or "relay", dev, data)


def owner_here(data: dict, folder: str) -> str:
    """Who works on a participant: the one the lead named, else the member who added it (team.json's `added`, kept
    on each computer until the lead's names them), else the lead. One added by someone no longer on the list goes
    back to the lead (landwt, 9 November 2026)."""
    roster = (data or {}).get("roster") or {}
    named = (roster.get("owners") or {}).get(folder)
    if named:
        return str(named)
    added = str(((data or {}).get("added") or {}).get(folder) or "")
    if added and member_of(roster, added) is not None:
        return added
    return str(roster.get("lead") or "")


# ------------------------------------------------------------------ what the page and the agents read

def view(root: Path, participants: list[dict] | None = None) -> dict:
    """Working together as Project settings and `team show` read it. Off, `{"on": false}` and nothing more, with
    nothing read but team.json and nothing written."""
    data = read_team(root)
    if not data or data.get("on") is not True:
        return {"on": False}
    dev = device() or {}
    roster = data.get("roster") or {}
    me = str(data.get("member") or "")
    lead = str(roster.get("lead") or "")
    people = []
    for m in roster_members(roster):
        devices = [d for d in m.get("devices") or [] if isinstance(d, dict)]
        people.append({"id": m.get("id"), "name": m.get("name") or "", "lead": m.get("id") == lead,
                       "you": m.get("id") == me, "computers": len(devices),
                       "this_computer": any(d.get("id") == dev.get("id") for d in devices),
                       "heard": m.get("heard") or "",
                       "devices": [{"id": d.get("id") or "", "name": one_line(d.get("name"))[:NAME_MOST],
                                    "added": d.get("added") or "", "this": d.get("id") == dev.get("id")}
                                   for d in devices]})
    rows = [{"folder": p["folder"], "label": p["label"], "owner": owner_here(data, p["folder"])}
            for p in participants or []]
    pending = []
    for inv, held in (held_team(str(data.get("team") or "")).get("invites") or {}).items():
        if not held.get("used") and not expired(held):
            pending.append({"invite": inv, "own": bool(held.get("own")), "expires": held.get("expires") or ""})
    state, unopened = folder_state(data)
    return {"on": True, "route": data.get("route") or "relay", "folder": data.get("folder") or "",
            "folder_state": state, "unopened": unopened,
            "recordings": data.get("recordings") is True, "member": me, "lead": lead, "you_lead": me == lead,
            "epoch": roster.get("epoch") or 1, "n": roster.get("n") or 0, "people": people, "participants": rows,
            "gets_owner": roster.get("gets_owner") or lead, "alone": len(people) <= 1, "invites": pending,
            "device": dev.get("id") or "", "removed": bool(me) and member_of(roster, me) is None,
            "asked": [a for a in data.get("asked") or [] if isinstance(a, dict)],
            "needs_code": needs_code(data) and me == lead, "on_relay": bool(relay_note(data).get("project"))}


def folder_state(data: dict) -> tuple[str, int]:
    """The shared folder as the page says it (wtfolder): "" with nothing to say, `none` when none is chosen, `missing`
    when the one chosen is not there, `unopened` when files in it would not open at the last look (a placeholder
    still syncing), with how many. Reads no file in it: only whether the folder is there."""
    if (data.get("route") or "relay") != "folder":
        return "", 0
    folder = str(data.get("folder") or "").strip()
    if not folder:
        return "none", 0
    path = Path(folder).expanduser()
    if not path.is_dir():
        return "missing", 0
    import folder_transport
    n = int(folder_transport.UNOPENED.get(str(path)) or 0)
    return ("unopened", n) if n else ("", 0)


def expired(held: dict) -> bool:
    try:
        return datetime.fromisoformat(str(held.get("expires"))) < datetime.now(timezone.utc)
    except ValueError:
        return True


def held_on(root: Path) -> dict:
    """team.json of a project where Working together is on, or a refusal."""
    data = read_team(root)
    if not data or data.get("on") is not True:
        raise TeamError(i18n.t("team.refused.off"), "off")
    return data


def must_lead(data: dict, dev: dict) -> None:
    if str(data.get("member") or "") != str((data.get("roster") or {}).get("lead") or "") \
            or dev["id"] not in lead_devices(data.get("roster") or {}):
        raise TeamError(i18n.t("team.refused.lead_only"), "lead_only")


def next_seq(team: str) -> int:
    with device_held():
        held = held_team(team)
        held["seq"] = int(held.get("seq") or 0) + 1
        keep_team(team, held)
    return held["seq"]


# ------------------------------------------------------------------ the project on the relay (relaywire, 9 November 2026)
#
# The relay makes a project only for an operator code (the spec, section 5), and answers its own random id. The lead
# puts the code in once, in Project settings' Relay code or with `team on --code-stdin`: it goes to the relay in that
# one call and is kept nowhere. The relay's id goes into the list of people as `relay`, `{"project"}` and, for a relay
# the team runs itself, its `url`, so every member has it from the lead's signature, and the relay route maps the
# team's id to it (relay_transport.TeamRelay).

RELAY = "relay"


def relay_note(data: dict) -> dict:
    held = ((data or {}).get("roster") or {}).get(RELAY)
    return held if isinstance(held, dict) else {}


def own_relay(data: dict) -> str:
    """The address of a relay the team runs itself, "" for idiograph.app's."""
    return one_line((data or {}).get("relay_url") or relay_note(data).get("url") or "")


def loopback() -> bool:
    """The suite's or a smoke run's loopback in place of every route, which needs no project made anywhere."""
    return transport_mod.OVERRIDE is not None or bool(os.environ.get(transport_mod.ENV, "").strip())


def needs_code(data: dict) -> bool:
    """Sent through the relay with no project there yet, so the lead's relay code is wanted."""
    return ((data or {}).get("route") or "relay") == "relay" and not relay_note(data).get("project") and not loopback()


def relay_refusal(exc) -> TeamError:
    """The relay's refusal of a code in plain words: a wrong code, one that has made all its projects, no
    connection, or anything else it refused."""
    status, said = getattr(exc, "status", None), str(getattr(exc, "error", "") or "")
    if status == 403 and said == "operator code":
        return TeamError(i18n.t("team.refused.wrong_code"), "wrong_code")
    if status == 429 and said == "projects for this code":
        return TeamError(i18n.t("team.refused.code_used"), "code_used")
    if not status:
        return TeamError(i18n.t("team.refused.relay_unreached"), "relay_unreached")
    return TeamError(i18n.t("team.refused.relay_refused"), "relay_refused")


def made_on_relay(data: dict, dev: dict, code) -> dict:
    """The project made on the relay with an operator code, this computer its lead there. Answers the list of
    people's `relay` note. Refused in plain words for no code, a wrong one, a used-up one or no connection."""
    code = str(code or "").strip()
    if not code:
        raise TeamError(i18n.t("team.refused.no_code"), "no_code")
    maker = getattr(transport_for(data, dev), "make_project", None)
    if maker is None:
        raise TeamError(i18n.t("team.refused.no_route"), "no_route")
    try:
        project = str(maker(code))
    except TeamError:
        raise
    except Exception as exc:  # noqa: BLE001 - the relay's refusal, or no connection
        raise relay_refusal(exc) from None
    url = own_relay(data)
    return dict({"project": project}, **({"url": url} if url else {}))


def put_on_relay(root: Path, data: dict, code, dry_run: bool = False) -> dict:
    """The lead's relay code taken: the project made on the relay, its id in the list of people, signed one
    higher, sent, and the relay told which computers may send."""
    dev = device() or {}
    must_lead(data, dev)
    changes = [i18n.t("team.history.relay_made")]
    if dry_run:
        return {"changes": changes, "dry_run": True}
    roster = deep(data.get("roster"))
    roster[RELAY] = made_on_relay(data, dev, code)
    signed_out(root, data, dev, roster)
    return {"changes": changes, "dry_run": False}


# ------------------------------------------------------------------ turning it on and off, and its settings

def turn_on(root: Path, name: str, route: str = "relay", folder: str = "", dry_run: bool = False, code=None,
            relay_url: str = "") -> dict:
    """Working together on for this project. The first time, this device's keys (made once and kept), a random
    16-byte team id, epoch 1's project key and a roster with this member as its lead, signed. Once made, on again
    keeps the team as it was. With `code`, a relay code, the project is made on the relay first (`relay_url` a
    team's own), and a refusal there writes nothing at all."""
    route = route if route in ROUTES else "relay"
    data = read_team(root)
    if data and data.get("on") is True and not data.get("roster"):
        return {"changes": [], "dry_run": dry_run}
    if data and data.get("roster"):
        changes = [] if data.get("on") is True else [i18n.t("team.history.on_again")]
        if changes and not dry_run:
            data = dict(data, on=True)
            write_team(root, data)
        if code is not None and needs_code(data):
            changes += put_on_relay(root, data, code, dry_run)["changes"]
        return {"changes": changes, "dry_run": dry_run}
    who = name_given(name)
    changes = [i18n.t("team.history.on_relay", name=who) if route == "relay"
               else i18n.t("team.history.on_folder", name=who)]
    url = one_line(relay_url)
    base = dict({"route": route}, **({"relay_url": url} if url else {}))
    asked = code is not None and needs_code(base)
    if asked:
        changes.append(i18n.t("team.history.relay_made"))
    if dry_run:
        lib()
        return {"changes": changes, "dry_run": True}
    dev = device()
    fresh = dev is None
    if fresh:
        dev = new_device()
    note = made_on_relay(base, dev, code) if asked else {}
    if fresh:
        save_device_file({"schema": SCHEMA, "device": dev, "teams": {}})
    team = secrets.token_bytes(16).hex()
    member = secrets.token_bytes(8).hex()
    key = secrets.token_bytes(32)
    roster = {"n": 1, "team": team, "epoch": 1, "lead": member,
              "members": [{"id": member, "name": who, "role": "lead",
                           "devices": [dict(public(dev), added=now_iso())]}],
              "owners": {}, "gets_owner": member}
    if note:
        roster[RELAY] = note
    roster["keys"] = seal_keys(key, roster)
    keep_key(team, 1, key)
    after = dict({"on": True, "team": team, "member": member, "route": route, "folder": one_line(folder),
                  "recordings": False, "roster": sign_roster(dev, roster)}, **base)
    write_team(root, after)
    if note:
        tell_relay(after, transport_for(after, dev), after["roster"])
    return {"changes": changes, "dry_run": False}


def turn_off(root: Path, dry_run: bool = False) -> dict:
    """Off: nothing more sent or taken in. team.json keeps the team, so on again picks it up."""
    data = read_team(root)
    if not data or data.get("on") is not True:
        return {"changes": [], "dry_run": dry_run}
    if not dry_run:
        write_team(root, dict(data, on=False))
    return {"changes": [i18n.t("team.history.off")], "dry_run": dry_run}


def set_team(root: Path, body: dict, participants: list[dict], dry_run: bool = False) -> dict:
    """The route, the shared folder, whether recordings go, and, by the lead, who works on each participant and on the
    GETs board. Each left out stays as it is."""
    data = held_on(root)
    roster = dict(data.get("roster") or {})
    changes, after = [], dict(data)
    if "route" in body:
        route = str(body.get("route") or "")
        if route not in ROUTES:
            raise TeamError(i18n.t("team.refused.bad_route"), "bad_route")
        if route != (data.get("route") or "relay"):
            if str(data.get("member") or "") != str(roster.get("lead") or ""):
                raise TeamError(i18n.t("team.refused.route_lead"), "route_lead")
            must_lead(data, device() or {})
            after["route"] = route
            changes.append(i18n.t("team.history.route_relay") if route == "relay"
                           else i18n.t("team.history.route_folder"))
            # the members follow at once, unless the relay has no project yet: then with the code's project
            if not needs_code(after) and not dry_run:
                listed = deep(roster)
                listed["route"] = route
                listed["n"] = int(listed.get("n") or 0) + 1
                roster = listed
                after["roster"] = sign_roster(device() or {}, listed)
    if "folder" in body:
        folder = one_line(body.get("folder"))
        if folder != (data.get("folder") or ""):
            after["folder"] = folder
            changes.append(i18n.t("team.history.folder", folder=folder) if folder else i18n.t("team.history.no_folder"))
    if "recordings" in body:
        rec = body.get("recordings") is True
        if rec != (data.get("recordings") is True):
            after["recordings"] = rec
            changes.append(i18n.t("team.history.recordings_on") if rec else i18n.t("team.history.recordings_off"))
    owners_asked = body.get("owners") if isinstance(body.get("owners"), dict) else {}
    gets_asked = body.get("gets_owner")
    if owners_asked or gets_asked:
        dev = device() or {}
        must_lead(data, dev)
        owners = dict(roster.get("owners") or {})
        by_folder = {p["folder"]: p for p in participants}
        by_label = {p["label"].lower(): p for p in participants}
        for who, member in owners_asked.items():
            p = by_folder.get(who) or by_label.get(str(who).lower())
            m = member_of(roster, str(member)) or next(
                (x for x in roster_members(roster) if (x.get("name") or "").lower() == str(member).lower()), None)
            if p is None:
                raise TeamError(i18n.t("team.refused.no_participant", who=one_line(who)), "no_participant")
            if m is None:
                raise TeamError(i18n.t("team.refused.no_member", who=one_line(member)), "no_member")
            if (owners.get(p["folder"]) or roster.get("lead")) != m["id"]:
                owners[p["folder"]] = m["id"]
                changes.append(i18n.t("team.history.owner", participant=p["label"], name=m.get("name") or ""))
        if gets_asked:
            m = member_of(roster, str(gets_asked)) or next(
                (x for x in roster_members(roster) if (x.get("name") or "").lower() == str(gets_asked).lower()), None)
            if m is None:
                raise TeamError(i18n.t("team.refused.no_member", who=one_line(gets_asked)), "no_member")
            if (roster.get("gets_owner") or roster.get("lead")) != m["id"]:
                roster["gets_owner"] = m["id"]
                changes.append(i18n.t("team.history.gets_owner", name=m.get("name") or ""))
        was = data.get("roster") or {}
        if owners != (roster.get("owners") or {}) or roster.get("gets_owner") != was.get("gets_owner"):
            roster["owners"] = owners
            roster["n"] = int(roster.get("n") or 0) + 1
            if not dry_run:
                after["roster"] = sign_roster(dev, roster)
    made = body.get("code") is not None and needs_code(after)
    if made:
        # the relay code (relaywire): the project made there before anything here is written
        dev = device() or {}
        must_lead(after, dev)
        changes.append(i18n.t("team.history.relay_made"))
        if not dry_run:
            listed = deep(after.get("roster"))
            listed[RELAY] = made_on_relay(after, dev, body.get("code"))
            if after.get("roster") is data.get("roster") or listed.get("route") != after.get("route"):
                listed["n"] = int(listed.get("n") or 0) + 1
            listed["route"] = after.get("route") or "relay"
            after["roster"] = sign_roster(dev, listed)
    if changes and not dry_run:
        write_team(root, after)
        if after.get("roster") is not data.get("roster"):
            if (data.get("route") or "relay") != (after.get("route") or "relay") and not made:
                # the members still on the old route hear of the new one there
                send_roster(dict(after, route=data.get("route")), device() or {})
                try:
                    send_roster(after, device() or {})
                except Exception:  # noqa: BLE001 - the new route not reached yet: the next list carries it
                    pass
            else:
                send_roster(after, device() or {})
        if made:
            tell_relay(after, transport_for(after, device() or {}), after["roster"])
            if (data.get("route") or "relay") != "relay":
                # the members still on the old route hear of the relay's project there
                send_roster(dict(after, route=data.get("route")), device() or {})
    return {"changes": changes, "dry_run": dry_run}


def send_roster(data: dict, dev: dict, under: int | None = None) -> None:
    """A new roster to the team, sealed under its epoch's key, or under the epoch before (`under`) when it brings a
    new key, which the devices left open from the roster itself. A transport that is not there yet sends nothing:
    the next roster carries it."""
    roster = data.get("roster") or {}
    team = str(data.get("team") or "")
    epoch = int(under or roster.get("epoch") or 1)
    key = project_key(team, epoch)
    if key is None or sum(len(m.get("devices") or []) for m in roster_members(roster)) <= 1:
        return
    try:
        way = transport_for(data, dev)
    except TeamError:
        return
    way.send(team, seal_envelope(team, epoch, key, dev, str(data.get("member") or ""), next_seq(team), "roster",
                                 roster))


def take_roster(root: Path, roster: dict) -> dict:
    """A roster come in, taken when the lead signed it and its number is higher, and this device's key for its epoch
    opened and kept. Answers the changes, or refuses."""
    data = held_on(root)
    held = data.get("roster") or {}
    check_roster(roster, lead_devices(held), int(held.get("n") or 0))
    dev = device() or {}
    key = open_key(dev, roster) if dev else None
    if key is not None:
        keep_key(str(data.get("team") or ""), int(roster.get("epoch") or 1), key)
    write_team(root, dict(data, roster=roster, **({"route": roster["route"]} if roster.get("route") in ROUTES else {})))
    return {"changes": [], "epoch": roster.get("epoch")}


# ------------------------------------------------------------------ invite, answer, match

def invite(root: Path, own: bool = False, dry_run: bool = False) -> dict:
    """An invite: a one-time secret, its words and link, posted to its mailbox with this device's keys, kept on this
    device for seven days. With `own`, for another computer of this member's."""
    data = held_on(root)
    dev = device() or {}
    if not own:
        must_lead(data, dev)
    if needs_code(data):
        raise TeamError(i18n.t("team.refused.no_relay"), "no_relay")
    changes = [i18n.t("team.history.invite_own") if own else i18n.t("team.history.invite")]
    if dry_run:
        return {"changes": changes, "dry_run": True}
    way = transport_for(data, dev)
    secret = secrets.token_bytes(16)
    inv = invite_id(secret)
    expires = (datetime.now(timezone.utc) + timedelta(days=INVITE_DAYS)).isoformat(timespec="seconds")
    team = str(data.get("team") or "")
    roster = data.get("roster") or {}
    me = member_of(roster, str(data.get("member") or "")) or {}
    offer = signed(dev, {"kind": "invite", "device": public(dev), "lead": roster.get("lead"),
                         "from": me.get("name") or "", "own": bool(own), "expires": expires})
    way.send(mailbox(inv), aead_seal(invite_key(secret), canon(offer)))
    held = held_team(team)
    held.setdefault("invites", {})[inv] = {"secret": b64(secret), "made": now_iso(), "expires": expires,
                                           "own": bool(own), "used": False, "thrown": []}
    keep_team(team, held)
    words = secret_words(secret)
    relay = own_relay(data) if (data.get("route") or "relay") == "relay" else ""
    return {"changes": changes, "dry_run": False, "invite": inv, "words": " ".join(words),
            "link": invite_link(words, relay), "expires": expires}


def mailbox_items(way, inv: str, key: bytes) -> list[tuple[str, dict]]:
    """An invite mailbox's messages that open under its key, each `(sender device, message)`, in order."""
    out = []
    for _seq, sender, sealed in way.fetch(mailbox(inv), 0):
        try:
            out.append((sender, json.loads(aead_open(key, sealed).decode("utf-8"))))
        except (TeamError, ValueError, UnicodeDecodeError):
            continue
    return out


def answers(root: Path, inv: str) -> dict:
    """An invite as its maker's install sees it: answered or not, and when answered the joiner's name and the six
    digits."""
    data = held_on(root)
    team = str(data.get("team") or "")
    held = (held_team(team).get("invites") or {}).get(inv)
    if not held:
        raise TeamError(i18n.t("team.refused.no_invite"), "no_invite")
    if held.get("used"):
        raise TeamError(i18n.t("team.refused.invite_used"), "invite_used")
    if expired(held):
        raise TeamError(i18n.t("team.refused.invite_expired"), "invite_expired")
    dev = device() or {}
    secret = unb64(held["secret"])
    answer = first_answer(transport_for(data, dev), inv, secret, held)
    if answer is None:
        return {"invite": inv, "answered": False}
    return {"invite": inv, "answered": True, "name": answer["name"],
            "code": check_code(secret, public(dev), answer["device"]), "own": bool(held.get("own"))}


def first_answer(way, inv: str, secret: bytes, held: dict) -> dict | None:
    """The first answer to an invite, signed by the device it names, not one thrown away."""
    for _sender, msg in mailbox_items(way, inv, invite_key(secret)):
        d = msg.get("device") if isinstance(msg.get("device"), dict) else None
        if msg.get("kind") != "answer" or d is None or not signed_by(str(d.get("sign") or ""), msg):
            continue
        if d.get("id") in (held.get("thrown") or []) or d.get("id") != device_id(unb64(d.get("sign"))):
            continue
        return msg
    return None


def admit(root: Path, inv: str, match: bool, dry_run: bool = False) -> dict:
    """They match: the joiner on the roster, a member or, for an invite of one's own, another computer of this
    member's, the project key sealed to his device, the roster signed and numbered one higher, posted back to the
    mailbox, and the invite closed. They differ: the answer thrown away, the invite still open."""
    data = held_on(root)
    team = str(data.get("team") or "")
    tm = held_team(team)
    held = (tm.get("invites") or {}).get(inv)
    if not held:
        raise TeamError(i18n.t("team.refused.no_invite"), "no_invite")
    if held.get("used"):
        raise TeamError(i18n.t("team.refused.invite_used"), "invite_used")
    if expired(held):
        raise TeamError(i18n.t("team.refused.invite_expired"), "invite_expired")
    dev = device() or {}
    own = bool(held.get("own"))
    if not own:
        must_lead(data, dev)
    secret = unb64(held["secret"])
    way = transport_for(data, dev)
    answer = first_answer(way, inv, secret, held)
    if answer is None:
        raise TeamError(i18n.t("team.refused.no_answer"), "no_answer")
    name = one_line(answer.get("name"))[:NAME_MOST]
    if not match:
        changes = [i18n.t("team.history.thrown", name=name)]
        if not dry_run:
            held.setdefault("thrown", []).append(answer["device"]["id"])
            tm["invites"][inv] = held
            keep_team(team, tm)
        return {"changes": changes, "dry_run": dry_run}
    me = str(data.get("member") or "")
    roster = json.loads(json.dumps(data.get("roster") or {}))
    joined = dict(answer["device"], added=now_iso())
    if device_on(roster, joined["id"])[1] is not None:
        raise TeamError(i18n.t("team.refused.already_on"), "already_on")
    if own and me != roster.get("lead"):
        # a member's own computer, from a computer of his not the lead's: the lead's install signs it on (wtdevices)
        return admit_own(root, data, dev, way, inv, secret, held, joined, dry_run)
    if own:
        target = member_of(roster, me)
        target["devices"] = list(target.get("devices") or []) + [joined]
        member, changes = me, [i18n.t("team.history.computer_added", name=target.get("name") or "")]
    else:
        member = secrets.token_bytes(8).hex()
        roster["members"] = roster_members(roster) + [{"id": member, "name": name, "role": "member",
                                                       "devices": [joined]}]
        changes = [i18n.t("team.history.joined", name=name)]
    if dry_run:
        return {"changes": changes, "dry_run": True}
    key = project_key(team, int(roster.get("epoch") or 1))
    roster["keys"] = dict(roster.get("keys") or {}, **{joined["id"]: b64(seal_to(joined["box"], key))})
    roster["n"] = int(roster.get("n") or 0) + 1
    roster = sign_roster(dev, roster)
    welcome = signed(dev, {"kind": "welcome", "to": joined["id"], "member": member, "team": team,
                           "route": data.get("route") or "relay", "roster": roster})
    way.send(mailbox(inv), aead_seal(invite_key(secret), canon(welcome)))
    way.send(mailbox(inv), aead_seal(invite_key(secret), canon(signed(dev, {"kind": "closed"}))))
    held["used"] = True
    tm = held_team(team)
    tm.setdefault("invites", {})[inv] = held
    keep_team(team, tm)
    after = dict(data, roster=roster)
    write_team(root, after)
    send_roster(after, dev)
    tell_relay(after, way, roster)
    return {"changes": changes, "dry_run": False}


def join(root: Path, words: str, name: str, dry_run: bool = False, relay_url: str = "") -> dict:
    """The joiner's side: the invite read from its mailbox, refused when it is closed, expired or not there, this
    device's name and keys posted as the answer, and the six digits to read on the call. Joined once the lead's
    They match comes back (`joined`)."""
    secret = words_secret(words)
    inv = invite_id(secret)
    data = read_team(root) or {}
    roster = data.get("roster") or {}
    if data.get("on") is True and len(roster_members(roster)) > 1:
        raise TeamError(i18n.t("team.refused.already_team"), "already_team")
    who = name_given(name)
    if dry_run:
        lib()
        return {"changes": [i18n.t("team.history.join_asked", name=who)], "dry_run": True}
    dev = device(make=True)
    # a team's own relay, as its link or the joiner names it (relaywire)
    relay = one_line(relay_url) or link_relay(words)
    way = transport_mod.for_team((data.get("route") or "relay"), dev, dict(data, relay_url=relay) if relay else data)
    offer = read_offer(way, inv, secret)
    answer = signed(dev, {"kind": "answer", "name": who, "device": public(dev)})
    way.send(mailbox(inv), aead_seal(invite_key(secret), canon(answer)))
    data_dev = load_device_file() or {}
    data_dev.setdefault("joining", {})[inv] = dict({"secret": b64(secret), "lead": offer["device"], "name": who,
                                                    "asked": now_iso(), "root": str(Path(root))},
                                                   **({"relay_url": relay} if relay else {}))
    save_device_file(data_dev)
    return {"changes": [], "dry_run": False, "invite": inv, "from": offer.get("from") or "",
            "code": check_code(secret, offer["device"], public(dev))}


def read_offer(way, inv: str, secret: bytes) -> dict:
    items = mailbox_items(way, inv, invite_key(secret))
    offer = next((m for _s, m in items if m.get("kind") == "invite" and isinstance(m.get("device"), dict)
                  and signed_by(str(m["device"].get("sign") or ""), m)), None)
    if offer is None:
        raise TeamError(i18n.t("team.refused.no_invite"), "no_invite")
    if any(m.get("kind") == "closed" and signed_by(offer["device"]["sign"], m) for _s, m in items):
        raise TeamError(i18n.t("team.refused.invite_used"), "invite_used")
    if expired(offer):
        raise TeamError(i18n.t("team.refused.invite_expired"), "invite_expired")
    return offer


def joined(root: Path, inv: str, dry_run: bool = False) -> dict:
    """The joiner's side once more: the lead's welcome read, its roster checked against the lead's device the invite
    named, the project key opened and kept, and team.json written. Answers `joined` false while it has not come, and
    with `dry_run` whether it has come, writing nothing."""
    data_dev = load_device_file() or {}
    asked = (data_dev.get("joining") or {}).get(inv)
    if not asked:
        raise TeamError(i18n.t("team.refused.no_invite"), "no_invite")
    dev = device() or {}
    secret = unb64(asked["secret"])
    lead = asked["lead"]
    data = read_team(root) or {}
    relay = str(asked.get("relay_url") or "")
    way = transport_mod.for_team(data.get("route") or "relay", dev, dict(data, relay_url=relay) if relay else data)
    welcome = None
    for _s, m in mailbox_items(way, inv, invite_key(secret)):
        if m.get("kind") == "welcome" and m.get("to") == dev["id"] and signed_by(lead["sign"], m):
            welcome = m
    if welcome is None:
        return {"joined": False, "changes": []}
    given = welcome.get("roster") if isinstance(welcome.get("roster"), dict) else {}
    if welcome.get("own") is True and lead["id"] not in lead_devices(given):
        # another computer of the member's let it in (wtdevices): the list as the lead signed it, the inviting
        # computer on it as this member's, the key sealed to this computer in the welcome itself. The lead's
        # computer puts this one on the list when it takes the asking in.
        roster = check_roster(given)
        who = device_on(roster, lead["id"])[0]
        if who is None or who.get("id") != welcome.get("member"):
            raise TeamError(i18n.t("team.refused.tampered"), "tampered")
        key = open_sealed(dev, unb64(welcome.get("key")))
    else:
        roster = check_roster(given, {lead["id"]: lead})
        key = open_key(dev, roster)
    if key is None:
        raise TeamError(i18n.t("team.refused.no_key"), "no_key")
    team = str(welcome.get("team") or "")
    if roster.get("team") != team:
        raise TeamError(i18n.t("team.refused.tampered"), "tampered")
    lead_name = (member_of(roster, str(roster.get("lead") or "")) or {}).get("name") or ""
    if dry_run:
        return {"joined": False, "come": True, "changes": [i18n.t("team.history.joined_team", name=lead_name)],
                "dry_run": True}
    keep_key(team, int(roster.get("epoch") or 1), key)
    write_team(root, {"on": True, "team": team, "member": str(welcome.get("member") or ""),
                      "route": welcome.get("route") or "relay", "folder": data.get("folder") or "",
                      "recordings": data.get("recordings") is True, "roster": roster})
    data_dev = load_device_file() or {}
    (data_dev.get("joining") or {}).pop(inv, None)
    save_device_file(data_dev)
    return {"joined": True, "changes": [i18n.t("team.history.joined_team", name=lead_name)]}


# ------------------------------------------------------------------ remove, with a new key

def remove(root: Path, member: str, dry_run: bool = False) -> dict:
    """The lead takes a member off the roster: his devices gone, epoch's key made new and sealed to every device
    left, the roster signed and sent. What he already has stays on his computer."""
    data = held_on(root)
    dev = device() or {}
    must_lead(data, dev)
    roster = json.loads(json.dumps(data.get("roster") or {}))
    m = member_of(roster, str(member)) or next(
        (x for x in roster_members(roster) if (x.get("name") or "").lower() == one_line(member).lower()), None)
    if m is None:
        raise TeamError(i18n.t("team.refused.no_member", who=one_line(member)), "no_member")
    if m["id"] == roster.get("lead"):
        raise TeamError(i18n.t("team.refused.not_the_lead"), "not_the_lead")
    changes = [i18n.t("team.history.removed", name=m.get("name") or "")]
    if dry_run:
        return {"changes": changes, "dry_run": True}
    roster["members"] = [x for x in roster_members(roster) if x["id"] != m["id"]]
    owners = {k: v for k, v in (roster.get("owners") or {}).items() if v != m["id"]}
    roster["owners"] = owners
    if roster.get("gets_owner") == m["id"]:
        roster["gets_owner"] = roster.get("lead")
    was = rotated(str(data.get("team") or ""), roster)
    signed_out(root, data, dev, roster, under=was)
    return {"changes": changes, "dry_run": False}


# ------------------------------------------------------------------ members and computers (wtdevices, 9 November 2026)
#
# Build 8 of the design: Add a computer of mine for a member who is not the lead, Remove one computer (a lost one,
# from the member's other computer or by the lead), and Make lead. Only the lead's computer signs the list of
# people (Adam's choice 2), so a member's change to his own computers goes to the team as a `devices` message,
# signed by one of his computers, and the lead's install takes it in (`take`) and signs the list that follows: it
# accepts a change from a member for that member's own computers alone. Every removal makes the next epoch's key and
# seals it to every computer left, so a removed computer opens nothing sent after it.

def deep(obj):
    return json.loads(json.dumps(obj or {}))


def computer_label(d: dict) -> str:
    return one_line((d or {}).get("name"))[:NAME_MOST] or i18n.t("team.page.a_computer")


def tell_relay(data: dict, way, roster: dict, lead: str | None = None) -> None:
    """The relay told which computers may send from now on, and with `lead` which computer leads, when the route
    keeps such a list (the relay's `set_devices`). A loopback or a folder keeps none, and a relay out of reach hears
    it with the next list: the new key is what keeps a removed computer out."""
    setter = getattr(way, "set_devices", None)
    if setter is None:
        return
    keys = [unb64(d["sign"]) for m in roster_members(roster) for d in m.get("devices") or [] if d.get("sign")]
    try:
        setter(str(data.get("team") or ""), keys, lead)
    except Exception:  # noqa: BLE001 - the relay's refusal or no connection changes nothing here
        pass


def signed_out(root: Path, data: dict, dev: dict, roster: dict, under: int | None = None,
               lead_device: str | None = None) -> dict:
    """The list numbered one higher, signed by this computer (the lead's), written to team.json and sent to the
    team, sealed under the epoch before when it brings a new key, and the relay told. Answers team.json."""
    roster["n"] = int(roster.get("n") or 0) + 1
    roster = sign_roster(dev, roster)
    after = dict(data, roster=roster)
    write_team(root, after)
    send_roster(after, dev, under=under)
    try:
        tell_relay(after, transport_for(after, dev), roster, lead_device)
    except TeamError:
        pass
    return after


def rotated(team: str, roster: dict) -> int:
    """The next epoch's key made, sealed to every computer on `roster` and kept here. Answers the epoch before."""
    was = int(roster.get("epoch") or 1)
    roster["epoch"] = was + 1
    key = secrets.token_bytes(32)
    roster["keys"] = seal_keys(key, roster)
    keep_key(team, roster["epoch"], key)
    return was


def ask_lead(data: dict, dev: dict, body: dict) -> None:
    """A change to this member's own computers sent to the team, for the lead's computer to take in and sign."""
    team = str(data.get("team") or "")
    roster = data.get("roster") or {}
    epoch = int(roster.get("epoch") or 1)
    key = project_key(team, epoch)
    if key is None:
        raise TeamError(i18n.t("team.refused.no_key"), "no_key")
    transport_for(data, dev).send(team, seal_envelope(team, epoch, key, dev, str(data.get("member") or ""),
                                                      next_seq(team), "devices", body))


def asked_now(data: dict, entry: dict) -> list[dict]:
    return [a for a in data.get("asked") or [] if isinstance(a, dict)] + [dict(entry, at=now_iso())]


def lead_name(roster: dict) -> str:
    return (member_of(roster, str(roster.get("lead") or "")) or {}).get("name") or ""


def admit_own(root: Path, data: dict, dev: dict, way, inv: str, secret: bytes, held: dict, joined: dict,
              dry_run: bool) -> dict:
    """They match on an invite of a member's own, from a computer of his that is not the lead's: the project's key
    sealed to the new computer here, the welcome carrying the list as the lead signed it, and the new computer asked
    of the lead's, whose install puts it on the list when it next takes in what has come."""
    roster = data.get("roster") or {}
    me = member_of(roster, str(data.get("member") or "")) or {}
    changes = [i18n.t("team.history.computer_asked", name=me.get("name") or "", lead=lead_name(roster))]
    if dry_run:
        return {"changes": changes, "dry_run": True}
    team = str(data.get("team") or "")
    key = project_key(team, int(roster.get("epoch") or 1))
    if key is None:
        raise TeamError(i18n.t("team.refused.no_key"), "no_key")
    welcome = signed(dev, {"kind": "welcome", "to": joined["id"], "member": me.get("id"), "team": team,
                           "route": data.get("route") or "relay", "roster": roster, "own": True,
                           "key": b64(seal_to(joined["box"], key))})
    way.send(mailbox(inv), aead_seal(invite_key(secret), canon(welcome)))
    way.send(mailbox(inv), aead_seal(invite_key(secret), canon(signed(dev, {"kind": "closed"}))))
    held["used"] = True
    tm = held_team(team)
    tm.setdefault("invites", {})[inv] = held
    keep_team(team, tm)
    ask_lead(data, dev, {"add": [{k: joined[k] for k in ("id", "sign", "box", "name") if k in joined}]})
    write_team(root, dict(data, asked=asked_now(data, {"add": joined["id"], "name": computer_label(joined)})))
    return {"changes": changes, "dry_run": False}


def remove_computer(root: Path, computer: str, dry_run: bool = False) -> dict:
    """One computer off the list, a lost one: by the lead, any member's but the one he is on, with a new key at
    once, or by a member, another of his own, asked of the lead's computer, which makes the new key when it takes
    the asking in. A member's only computer is refused: Remove takes the member."""
    data = held_on(root)
    dev = device() or {}
    roster = deep(data.get("roster"))
    owner, d = device_on(roster, str(computer or ""))
    if d is None:
        raise TeamError(i18n.t("team.refused.no_computer"), "no_computer")
    if d["id"] == dev.get("id"):
        raise TeamError(i18n.t("team.refused.this_computer"), "this_computer")
    if len(owner.get("devices") or []) <= 1:
        raise TeamError(i18n.t("team.refused.last_computer", name=owner.get("name") or ""), "last_computer")
    me = str(data.get("member") or "")
    label = computer_label(d)
    if me == str(roster.get("lead") or "") and dev.get("id") in lead_devices(roster):
        changes = [i18n.t("team.history.computer_removed", computer=label, name=owner.get("name") or "")]
        if dry_run:
            return {"changes": changes, "dry_run": True}
        owner["devices"] = [x for x in owner.get("devices") or [] if x.get("id") != d["id"]]
        was = rotated(str(data.get("team") or ""), roster)
        signed_out(root, data, dev, roster, under=was)
        return {"changes": changes, "dry_run": False}
    if owner.get("id") != me:
        raise TeamError(i18n.t("team.refused.lead_only"), "lead_only")
    changes = [i18n.t("team.history.computer_remove_asked", computer=label, lead=lead_name(roster))]
    if dry_run:
        return {"changes": changes, "dry_run": True}
    ask_lead(data, dev, {"remove": [d["id"]]})
    write_team(root, dict(data, asked=asked_now(data, {"remove": d["id"], "name": label})))
    return {"changes": changes, "dry_run": False}


def make_lead(root: Path, member: str, participants: list[dict] | None = None, dry_run: bool = False) -> dict:
    """The lead hands the list to another member: the list naming him lead, signed one last time by this computer,
    so every install takes it from the lead it knew, and from then on signed by his. A participant or the GETs
    board that was the lead's by default stays with the one who led, so nothing changes hands but the list."""
    data = held_on(root)
    dev = device() or {}
    must_lead(data, dev)
    roster = deep(data.get("roster"))
    m = member_of(roster, str(member)) or next(
        (x for x in roster_members(roster) if (x.get("name") or "").lower() == one_line(member).lower()), None)
    if m is None:
        raise TeamError(i18n.t("team.refused.no_member", who=one_line(member)), "no_member")
    was = str(roster.get("lead") or "")
    if m["id"] == was:
        raise TeamError(i18n.t("team.refused.lead_already", name=m.get("name") or ""), "lead_already")
    changes = [i18n.t("team.history.made_lead", name=m.get("name") or "")]
    if dry_run:
        return {"changes": changes, "dry_run": True}
    owners = dict(roster.get("owners") or {})
    for p in participants or []:
        owners.setdefault(p["folder"], owner_here(dict(data, roster=dict(roster, lead=was)), p["folder"]))
    roster["owners"] = owners
    roster["gets_owner"] = roster.get("gets_owner") or was
    roster["lead"] = m["id"]
    for x in roster_members(roster):
        x["role"] = "lead" if x["id"] == m["id"] else "member"
    signed_out(root, data, dev, roster, lead_device=((m.get("devices") or [{}])[0]).get("id"))
    return {"changes": changes, "dry_run": False}


def apply_devices(root: Path, data: dict, dev: dict, inner: dict) -> list[str]:
    """A member's change to his own computers, taken in by the lead's computer: those he adds put on the list with
    the key sealed to them, those he removes taken off with a new key, never another member's computer, never the
    one that asked and never his last. Answers the changes."""
    roster = deep(data.get("roster"))
    m = member_of(roster, str(inner.get("member") or ""))
    body = inner.get("body") if isinstance(inner.get("body"), dict) else {}
    if m is None:
        return []
    changes, gone = [], False
    team = str(data.get("team") or "")
    for d in body.get("add") or []:
        if not isinstance(d, dict) or not d.get("sign") or not d.get("box"):
            continue
        if d.get("id") != device_id(unb64(d["sign"])) or device_on(roster, d["id"])[1] is not None:
            continue
        m["devices"] = list(m.get("devices") or []) + [
            dict({k: d[k] for k in ("id", "sign", "box", "name") if k in d}, added=now_iso())]
        key = project_key(team, int(roster.get("epoch") or 1))
        if key is not None:
            roster["keys"] = dict(roster.get("keys") or {}, **{d["id"]: b64(seal_to(d["box"], key))})
        changes.append(i18n.t("team.history.computer_added", name=m.get("name") or ""))
    for gone_id in body.get("remove") or []:
        mine = [x for x in m.get("devices") or [] if x.get("id") == gone_id]
        if not mine or gone_id == inner.get("device") or len(m.get("devices") or []) <= 1:
            continue
        m["devices"] = [x for x in m["devices"] if x.get("id") != gone_id]
        gone = True
        changes.append(i18n.t("team.history.computer_removed", computer=computer_label(mine[0]),
                              name=m.get("name") or ""))
    if not changes:
        return []
    was = rotated(team, roster) if gone else None
    signed_out(root, data, dev, roster, under=was)
    return changes


def come(root: Path) -> list:
    """What has come since this build's reading last got to, fetched with no lock held, since a relay can be slow
    to answer: `take` reads it under the project's lock. Refused plainly when the route cannot be reached."""
    data = held_on(root)
    if needs_code(data):
        raise TeamError(i18n.t("team.refused.no_relay"), "no_relay")
    dev = device() or {}
    team = str(data.get("team") or "")
    way = transport_for(data, dev)
    try:
        return list(way.fetch(team, int(held_team(team).get(TAKEN) or 0)))
    except TeamError:
        raise
    except Exception:  # noqa: BLE001 - the relay's refusal, no connection, a folder not there
        raise TeamError(i18n.t("team.refused.no_connection"), "no_connection") from None


def take(root: Path, dry_run: bool = False, items: list | None = None) -> dict:
    """What has come for the list of people, taken in: a newer list the lead signed, with this computer's key for
    its epoch opened and kept, and on the lead's computer a member's change to his own computers. Every other kind
    is left to the builds that read it. A message that will not open, or from a computer not on the list, is
    dropped and noted. `items` is what `come` fetched, fetched here when left out. Answers the changes, with
    `removed` when the list no longer has this member."""
    data = held_on(root)
    dev = device() or {}
    team = str(data.get("team") or "")
    changes = []
    if items is None:
        items = come(root)
    for seq, sender, raw in items:
        if int(seq) <= int(held_team(team).get(TAKEN) or 0):
            continue
        data = read_team(root) or data
        roster = data.get("roster") or {}
        try:
            inner = open_envelope(raw, roster, project_keys(team))
        except (TeamError, ValueError, KeyError, TypeError, UnicodeDecodeError) as exc:
            if not dry_run and sender != dev.get("id"):
                note_dropped(root, getattr(exc, "code", "") or "tampered", sender)
            inner = None
        kind = (inner or {}).get("kind")
        if inner is None or inner.get("device") == dev.get("id"):
            pass
        elif kind == "roster" and int((inner.get("body") or {}).get("n") or 0) > int(roster.get("n") or 0):
            if dry_run:
                changes.append(i18n.t("team.history.list_taken"))
            else:
                try:
                    take_roster(root, inner["body"])
                    changes.append(i18n.t("team.history.list_taken"))
                except TeamError as exc:
                    note_dropped(root, exc.code, sender)
        elif kind == "devices" and str(data.get("member") or "") == str(roster.get("lead") or "") \
                and dev.get("id") in lead_devices(roster):
            changes += [i18n.t("team.history.list_taken")] if dry_run else apply_devices(root, data, dev, inner)
        if not dry_run:
            held = held_team(team)
            held[TAKEN] = max(int(held.get(TAKEN) or 0), int(seq))
            keep_team(team, held)
    data = read_team(root) or data
    roster = data.get("roster") or {}
    if not dry_run:
        asked = [a for a in data.get("asked") or [] if isinstance(a, dict)]
        left = [a for a in asked if (a.get("add") and device_on(roster, a["add"])[1] is None)
                or (a.get("remove") and device_on(roster, a["remove"])[1] is not None)]
        if left != asked:
            write_team(root, dict(data, asked=left))
    me = str(data.get("member") or "")
    return {"changes": changes, "dry_run": dry_run, "removed": bool(me) and member_of(roster, me) is None}
