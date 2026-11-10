"""Signatures in the form Tauri's updater checks, minisign's, made and checked in Python alone (17 October
2026, the third Tauri build), for `packaging/release.py` and its checks.

Tauri's updater takes a key pair `tauri signer generate` makes: a secret key sealed with a password by
scrypt, which minisign's own tools read too, and a public key built into every copy of the app. Each
update file is signed with the secret key, and `latest.json` carries each signature, which the app
checks before it installs anything. The signature is minisign's prehashed one: BLAKE2b-512 of the
file, signed with Ed25519, then a trusted comment, its time, the file's name and the version, signed
with the signature, as `tauri signer sign --app-version` writes it. Every key and signature travels
as base64 of minisign's own text, as Tauri's files hold them.

Ed25519 here is RFC 8032's own reference arithmetic, slow beside a library and fast enough for a few
signatures, so the release needs nothing installed and the app none of it. Nothing here reads the
Keychain or prints a key: `release.py` hands the secret key in and takes signatures out.
"""
from __future__ import annotations

import base64
import hashlib
import os
import time

# ── Ed25519, RFC 8032, section 6 ───────────────────────────────────────────────────────────────

P = 2 ** 255 - 19
L = 2 ** 252 + 27742317777372353535851937790883648493
D = -121665 * pow(121666, P - 2, P) % P
SQRT_M1 = pow(2, (P - 1) // 4, P)


def _inv(x: int) -> int:
    return pow(x, P - 2, P)


def _recover_x(y: int, sign: int) -> int | None:
    if y >= P:
        return None
    x2 = (y * y - 1) * _inv(D * y * y + 1) % P
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (P + 3) // 8, P)
    if (x * x - x2) % P:
        x = x * SQRT_M1 % P
    if (x * x - x2) % P:
        return None
    if (x & 1) != sign:
        x = P - x
    return x


_GY = 4 * _inv(5) % P
_GX = _recover_x(_GY, 0)
G = (_GX, _GY, 1, _GX * _GY % P)
ZERO = (0, 1, 1, 0)


def _add(a: tuple, b: tuple) -> tuple:
    p1 = (a[1] - a[0]) * (b[1] - b[0]) % P
    p2 = (a[1] + a[0]) * (b[1] + b[0]) % P
    c = 2 * a[3] * b[3] * D % P
    d = 2 * a[2] * b[2] % P
    e, f, g, h = p2 - p1, d - c, d + c, p2 + p1
    return (e * f % P, g * h % P, f * g % P, e * h % P)


def _mul(s: int, point: tuple) -> tuple:
    out = ZERO
    while s > 0:
        if s & 1:
            out = _add(out, point)
        point = _add(point, point)
        s >>= 1
    return out


def _equal(a: tuple, b: tuple) -> bool:
    return (a[0] * b[2] - b[0] * a[2]) % P == 0 and (a[1] * b[2] - b[1] * a[2]) % P == 0


def _compress(point: tuple) -> bytes:
    zinv = _inv(point[2])
    x, y = point[0] * zinv % P, point[1] * zinv % P
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


def _decompress(raw: bytes) -> tuple | None:
    if len(raw) != 32:
        return None
    y = int.from_bytes(raw, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _recover_x(y, sign)
    return None if x is None else (x, y, 1, x * y % P)


def _hash_int(data: bytes) -> int:
    return int.from_bytes(hashlib.sha512(data).digest(), "little") % L


def _expand(seed: bytes) -> tuple[int, bytes]:
    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a, h[32:]


def public_of(seed: bytes) -> bytes:
    """The 32-byte public key of a 32-byte seed."""
    return _compress(_mul(_expand(seed)[0], G))


def ed25519_sign(seed: bytes, message: bytes) -> bytes:
    a, prefix = _expand(seed)
    public = _compress(_mul(a, G))
    r = _hash_int(prefix + message)
    big_r = _compress(_mul(r, G))
    s = (r + _hash_int(big_r + public + message) * a) % L
    return big_r + int.to_bytes(s, 32, "little")


def ed25519_verify(public: bytes, message: bytes, signature: bytes) -> bool:
    if len(signature) != 64:
        return False
    a, r = _decompress(public), _decompress(signature[:32])
    if a is None or r is None:
        return False
    s = int.from_bytes(signature[32:], "little")
    if s >= L:
        return False
    h = _hash_int(signature[:32] + public + message)
    return _equal(_mul(s, G), _add(r, _mul(h, a)))


# ── minisign's keys and signatures, as Tauri writes them ─────────────────────────────────────────

ALG = b"Ed"
PREHASHED = b"ED"
KDF = b"Sc"
CHECKSUM = b"B2"
# scrypt's work and memory as minisign seals a key, libsodium's names for them
OPSLIMIT = 1_048_576
MEMLIMIT = 33_554_432
SECRET_COMMENT = "rsign encrypted secret key"
SIGNATURE_COMMENT = "signature from tauri secret key"


class BadKey(ValueError):
    """A key or signature that is not one, or a password that does not open the key."""


def _b64(text: str) -> bytes:
    try:
        return base64.b64decode("".join(text.split()), validate=True)
    except (ValueError, TypeError) as exc:
        raise BadKey("not base64") from exc


def _lines(blob: str) -> list[str]:
    """The text a Tauri key or signature holds, base64 of minisign's own lines."""
    return _b64(blob).decode("utf-8", errors="strict").splitlines()


def _scrypt_params(opslimit: int, memlimit: int) -> tuple[int, int, int]:
    """libsodium's crypto_pwhash_scryptsalsa208sha256 choice of N, r and p for a work and memory limit,
    as minisign seals and opens its keys."""
    opslimit = max(opslimit, 32768)
    r = 8
    if opslimit < memlimit // 32:
        p = 1
        max_n = opslimit // (r * 4)
        n_log2 = next(i for i in range(1, 63) if (1 << i) > max_n // 2)
    else:
        max_n = memlimit // (r * 128)
        n_log2 = next(i for i in range(1, 63) if (1 << i) > max_n // 2)
        max_rp = min((opslimit // 4) // (1 << n_log2), 0x3FFFFFFF)
        p = max_rp // r
    return 1 << n_log2, r, max(p, 1)


def _stream(password: str, salt: bytes, opslimit: int, memlimit: int, size: int) -> bytes:
    n, r, p = _scrypt_params(opslimit, memlimit)
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, maxmem=256 * 1024 * 1024, dklen=size)


def _checksum(keynum: bytes, secret: bytes) -> bytes:
    return hashlib.blake2b(ALG + keynum + secret, digest_size=32).digest()


def _wrap(comment: str, *lines: str) -> str:
    """minisign's text, its untrusted comment first, as base64 in one line, as Tauri keeps it."""
    text = "\n".join([f"untrusted comment: {comment}", *lines]) + "\n"
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


class SecretKey:
    """A secret key opened with its password: its number and its Ed25519 seed and public key."""

    def __init__(self, keynum: bytes, seed: bytes, public: bytes):
        self.keynum, self.seed, self.public = keynum, seed, public

    def public_key(self) -> str:
        """The public key as Tauri's tauri.conf.json and the `.pub` file hold it."""
        number = int.from_bytes(self.keynum, "little")
        raw = base64.b64encode(ALG + self.keynum + self.public).decode("ascii")
        return _wrap(f"minisign public key: {number:016X}", raw)

    def __repr__(self) -> str:  # never the seed, whatever prints it
        return f"SecretKey({int.from_bytes(self.keynum, 'little'):016X})"


def open_secret(blob: str, password: str) -> SecretKey:
    """A Tauri secret key, base64 as `tauri signer generate` writes it, opened with its password."""
    lines = _lines(blob)
    if len(lines) < 2 or not lines[0].startswith("untrusted comment:"):
        raise BadKey("not a minisign secret key")
    raw = _b64(lines[1])
    if len(raw) != 158 or raw[:2] != ALG or raw[4:6] != CHECKSUM:
        raise BadKey("not a minisign secret key")
    kdf, salt = raw[2:4], raw[6:38]
    ops, mem = int.from_bytes(raw[38:46], "little"), int.from_bytes(raw[46:54], "little")
    sealed = raw[54:]
    if kdf == KDF:
        sealed = bytes(x ^ y for x, y in zip(sealed, _stream(password, salt, ops, mem, len(sealed))))
    elif kdf != b"\x00\x00":
        raise BadKey("a key sealed some other way")
    keynum, secret, check = sealed[:8], sealed[8:72], sealed[72:104]
    if _checksum(keynum, secret) != check:
        raise BadKey("the password does not open this key")
    seed, public = secret[:32], secret[32:]
    if public_of(seed) != public:
        raise BadKey("the key's two halves do not match")
    return SecretKey(keynum, seed, public)


def make_secret(password: str, seed: bytes | None = None, keynum: bytes | None = None) -> str:
    """A new secret key sealed with `password`, as `tauri signer generate` makes one, for a check's
    throwaway key: never the release's own, which Adam makes with make_update_key.sh."""
    seed = seed or os.urandom(32)
    keynum = keynum or os.urandom(8)
    secret = seed + public_of(seed)
    salt = os.urandom(32)
    plain = keynum + secret + _checksum(keynum, secret)
    sealed = bytes(x ^ y for x, y in zip(plain, _stream(password, salt, OPSLIMIT, MEMLIMIT, len(plain))))
    raw = ALG + KDF + CHECKSUM + salt + OPSLIMIT.to_bytes(8, "little") + MEMLIMIT.to_bytes(8, "little") + sealed
    return _wrap(SECRET_COMMENT, base64.b64encode(raw).decode("ascii"))


def read_public(blob: str) -> tuple[bytes, bytes]:
    """A Tauri public key's number and Ed25519 key, or BadKey for anything else, the placeholder
    tauri.conf.json holds until Adam has made the key among them."""
    lines = _lines(blob)
    if len(lines) < 2 or not lines[0].startswith("untrusted comment:"):
        raise BadKey("not a minisign public key")
    raw = _b64(lines[1])
    if len(raw) != 42 or raw[:2] != ALG:
        raise BadKey("not a minisign public key")
    return raw[2:10], raw[10:]


def trusted_comment(name: str, version: str | None, when: int | None = None) -> str:
    """The trusted comment `tauri signer sign --app-version` writes: the time, the file and the
    version, which the signature covers, so a manifest cannot pair one version's number with another's file."""
    parts = [f"timestamp:{int(time.time()) if when is None else when}", f"file:{name}"]
    if version:
        parts.append(f"version:{version}")
    return "\t".join(parts)


def sign(key: SecretKey, data: bytes, comment: str) -> str:
    """A file's signature, base64 of minisign's text, as the `.sig` file and latest.json hold it."""
    signature = ed25519_sign(key.seed, hashlib.blake2b(data, digest_size=64).digest())
    box = base64.b64encode(PREHASHED + key.keynum + signature).decode("ascii")
    whole = ed25519_sign(key.seed, signature + comment.encode("utf-8"))
    return _wrap(SIGNATURE_COMMENT, box, f"trusted comment: {comment}", base64.b64encode(whole).decode("ascii"))


def verify(public_blob: str, data: bytes, signature_blob: str) -> str | None:
    """The trusted comment when `signature_blob` is a good signature of `data` by the public key, as
    the updater checks it, and None for anything else: another key, a changed file or comment."""
    try:
        keynum, public = read_public(public_blob)
        lines = _lines(signature_blob)
        if len(lines) < 4 or not lines[2].startswith("trusted comment: "):
            return None
        box, whole = _b64(lines[1]), _b64(lines[3])
        comment = lines[2][len("trusted comment: "):]
    except (BadKey, UnicodeDecodeError):
        return None
    if len(box) != 74 or box[2:10] != keynum or box[:2] not in (ALG, PREHASHED):
        return None
    signed = hashlib.blake2b(data, digest_size=64).digest() if box[:2] == PREHASHED else data
    signature = box[10:]
    if not ed25519_verify(public, signed, signature):
        return None
    if not ed25519_verify(public, signature + comment.encode("utf-8"), whole):
        return None
    return comment
