#!/usr/bin/env python3
"""The demos' recordings, downloaded the first time one is played (recdemand, 13 November 2026).

Adam, 13 November, by dialog: "Text in, recordings on demand". The installers carry each demo's text, its
transcripts, workbooks and boards, so Home shows every demo and each opens offline, and none of its recordings. The
first time a demo's recording is played, its player says the size and offers the download, and the recordings come
down from a GitHub release of their own on Pharkie/idiograph, `demo-recordings-1`, not a version's, one asset a
recording with `LICENSE-audio.md` beside them. They are kept on the computer after, where the app keeps its demo, so
the AI-made audio and its own licence stay out of every installer, the signed Windows one among them.

The manifest, `demo/recordings.json`, is committed and ships with the demo's text. It names the release, the
address its files are downloaded from and, for each recording and for the licence, the file, its size and its
sha256, so what the app carries, never what comes down, says what is right: a file is taken only when its every
byte matches. A recording's file name carries the hash of the transcript it was made from
(`audio.demo_recording_name`), so the manifest names a recording only for the transcript the app ships, and an
earlier encoding of the same recording (`earlier`, its sizes) is as good as the one named, its timecodes the same.

`Fetch` is one demo's download, on a thread of its own: each file comes down beside its place under a hidden
name, is counted as it comes for the page's progress, checked against its size and sha256, and only then takes its
place, so the player never reads half of one and a file that does not match is never kept. Cancel stops it between
two reads. A file already in place is never fetched again. The standard library alone.

Where it may come from (rechttps, 13 November 2026, Adam by dialog: "Harden first, then create"): HTTPS alone, to
GitHub's own hosts alone (`HOSTS`, fixed here and never read from the manifest), on port 443, for the first address
and for every redirect, each checked by `allowed` before it is opened, so a manifest or a redirect that names
anything else ends the download `failed` before a byte of it is read. A smoke run's loopback stand-in is let
through only when the caller hands `Fetch` its address, from `IDIOGRAPH_SEARCH_STUB` and never from the manifest,
and never in the installed app.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

MANIFEST = "recordings.json"
LICENCE = "LICENSE-audio.md"
# the release the recordings are assets of, on the app's own repository, never a version's tag, so the newest
# version's files and the update check never see it
RELEASE = "demo-recordings-1"
URL = f"https://github.com/Pharkie/idiograph/releases/download/{RELEASE}/"
CHUNK = 64 * 1024
# seconds a read may wait on the network before the download counts as offline
TIMEOUT = 20
# the only hosts a recording comes from, over HTTPS on 443: the release's own address and where GitHub redirects its
# downloads to (rechttps, 13 November 2026). Fixed here: no manifest, setting or answer widens it.
HOSTS = frozenset({"github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com"})
# redirects followed before the download gives up, GitHub's one and room to spare
REDIRECTS = 5
# a smoke run's stand-in is on this machine alone
LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})


class Mismatch(Exception):
    """A file that came down other than the manifest says, by its size or its sha256."""


class Cancelled(Exception):
    """Cancel pressed while a file was coming down."""


class Refused(Exception):
    """An address, the first or a redirect's, that is not HTTPS to one of GitHub's own hosts (`allowed`)."""


def origin(url: str) -> tuple | None:
    """A URL's scheme, host and port, or None when it has a user or password in it or cannot be read."""
    try:
        parts = urlsplit(str(url))
        port = parts.port
    except ValueError:
        return None
    if "@" in parts.netloc or not parts.hostname:
        return None
    scheme = parts.scheme.lower()
    return scheme, parts.hostname.lower(), port or {"https": 443, "http": 80}.get(scheme)


def allowed(url: str, stub: str = "") -> bool:
    """Whether a recording may be downloaded from `url`: HTTPS to one of `HOSTS` on 443, nothing else. `stub`, a
    smoke run's loopback stand-in handed by the caller, lets that one origin through too, never in the installed
    (frozen) app."""
    where = origin(url)
    if where is None:
        return False
    if where[0] == "https" and where[1] in HOSTS and where[2] == 443:
        return True
    if stub and not getattr(sys, "frozen", False):
        own = origin(stub)
        return own is not None and own[0] in ("http", "https") and own[1] in LOOPBACK and where == own
    return False


class Guard(urllib.request.HTTPRedirectHandler):
    """A redirect followed only to an address `allowed` takes, and at most `REDIRECTS` of them."""
    max_redirections = REDIRECTS

    def __init__(self, stub: str = ""):
        super().__init__()
        self.stub = stub

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed(newurl, self.stub):
            raise Refused()
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def opened(url: str, stub: str = ""):
    """The answer for `url`, refused before anything is sent when it is not `allowed`, and before its body is read
    when a redirect, or where it ended, is not. Certificates are checked as urllib always does, against the
    certificates the launcher points the frozen app at (`SSL_CERT_FILE`, certifi's)."""
    if not allowed(url, stub):
        raise Refused()
    opener = urllib.request.build_opener(Guard(stub))
    answer = opener.open(urllib.request.Request(url, headers={"User-Agent": "Idiograph"}), timeout=TIMEOUT)
    if not allowed(answer.geturl(), stub):
        answer.close()
        raise Refused()
    return answer


def file_sum(path: Path) -> str:
    """The sha256 of a file, read a block at a time."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_manifest(path: Path) -> dict:
    """The manifest at `path`, or {} when it is missing or cannot be read."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) and isinstance(data.get("recordings"), list) else {}


def entry(manifest: dict, file: str) -> dict | None:
    """The manifest's entry for a recording's file, or None when it names none of that name."""
    return next((e for e in manifest.get("recordings") or [] if isinstance(e, dict) and e.get("file") == file), None)


def fits(item: dict, size: int) -> bool:
    """Whether a file in place of this size is the entry's recording: its own size, or an earlier encoding's."""
    return size == item.get("size") or size in (item.get("earlier") or [])


def make_manifest(folder: Path, files: list[str], earlier: dict | None = None, url: str = URL,
                  release: str = RELEASE) -> dict:
    """The manifest for the recordings `files` in `folder` and the licence beside them. `earlier` maps a file's name
    to the sizes of its earlier encodings, which stay as good as it."""
    folder = Path(folder)
    rows = []
    for name in sorted(files):
        path = folder / name
        row = {"file": name, "size": path.stat().st_size, "sha256": file_sum(path)}
        sizes = sorted(set(int(s) for s in (earlier or {}).get(name, []) if int(s) != row["size"]))
        if sizes:
            row["earlier"] = sizes
        rows.append(row)
    licence = folder / LICENCE
    return {"release": release, "url": url, "recordings": rows,
            "licence": {"file": LICENCE, "size": licence.stat().st_size, "sha256": file_sum(licence)}}


def write_manifest(target: Path, folder: Path, files: list[str]) -> dict:
    """The manifest for `files` in `folder` written to `target`, through a file of its own. A file of the same name
    the manifest there already named keeps its earlier sizes, and its own when its bytes changed, a re-encoding of
    the same recording, so a copy holding that one is not asked to download it again."""
    old = read_manifest(target)
    earlier = {}
    for name in files:
        was = entry(old, name)
        if was:
            earlier[name] = list(was.get("earlier") or []) + [was.get("size")]
    data = make_manifest(folder, files, earlier, url=old.get("url") or URL, release=old.get("release") or RELEASE)
    target = Path(target)
    tmp = target.with_name(f".{target.name}.writing")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, target)
    return data


def address(manifest: dict, file: str, stub: str = "") -> str:
    """Where a file of the manifest is downloaded from. In a smoke run, `stub` a loopback stand-in's address, the
    release's host is replaced by it, so no run reaches GitHub."""
    base = str(manifest.get("url") or URL)
    if not base.endswith("/"):
        base += "/"
    if stub:
        from urllib.parse import urlparse
        return f"{stub.rstrip('/')}/github{urlparse(base).path}{file}"
    return base + file


def part_of(target: Path) -> Path:
    """The hidden name a file comes down under beside its place, which the player never takes."""
    return Path(target).with_name(f".{Path(target).name}.downloading")


class Fetch:
    """One demo's download: `items` each a dict of `url`, `size`, `sha256` and `targets`, the places the file goes,
    the first one written and the others copied from it once it is checked. `state` is downloading, done, failed
    or cancelled, `got` the bytes come down of `size` in all, and `why` offline, failed or checksum once failed.
    `stub`, a smoke run's loopback stand-in, is the one address besides GitHub's it may download from (`allowed`)."""

    def __init__(self, items: list[dict], stub: str = ""):
        self.items = items
        self.stub = stub
        self.size = sum(int(i["size"]) for i in items)
        self.got = 0
        self.state = "downloading"
        self.why = ""
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self.run, name="demo-recordings", daemon=True)

    def start(self) -> "Fetch":
        self.thread.start()
        return self

    def view(self) -> dict:
        with self.lock:
            return {"state": self.state, "got": self.got, "bytes": self.size, "why": self.why}

    def cancel(self) -> None:
        self.stop.set()

    def fetch(self, item: dict) -> None:
        """One file down to its first place's hidden name, counted, checked and put in its places."""
        targets = [Path(t) for t in item["targets"]]
        first = targets[0]
        first.parent.mkdir(parents=True, exist_ok=True)
        part = part_of(first)
        digest, size, came = hashlib.sha256(), int(item["size"]), 0
        try:
            with opened(item["url"], self.stub) as answer, open(part, "wb") as fh:
                while True:
                    if self.stop.is_set():
                        raise Cancelled()
                    block = answer.read(CHUNK)
                    if not block:
                        break
                    came += len(block)
                    if came > size:
                        raise Mismatch()
                    digest.update(block)
                    fh.write(block)
                    with self.lock:
                        self.got += len(block)
            if came != size or digest.hexdigest() != item["sha256"]:
                raise Mismatch()
            for other in targets[1:]:
                other.parent.mkdir(parents=True, exist_ok=True)
                held = part_of(other)
                shutil.copyfile(part, held)
                os.replace(held, other)
            os.replace(part, first)
        finally:
            part.unlink(missing_ok=True)

    def run(self) -> None:
        state, why = "done", ""
        try:
            for item in self.items:
                self.fetch(item)
        except Cancelled:
            state = "cancelled"
        except Mismatch:
            state, why = "failed", "checksum"
        except Refused:
            # an address that is not GitHub's over HTTPS, the first or a redirect's
            state, why = "failed", "failed"
        except urllib.error.HTTPError:
            # GitHub answered and had no such file, the release not made or the file taken away
            state, why = "failed", "failed"
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            state, why = "failed", "offline"
        except OSError:
            state, why = "failed", "failed"
        with self.lock:
            self.state, self.why = state, why


# one download a demo, kept while the server runs so a page opened again mid-way reads how far it has got
FETCHES: dict[str, Fetch] = {}
_fetches = threading.Lock()


def start(key: str, items: list[dict], stub: str = "") -> Fetch:
    """The demo's download, the running one when there is one, else a new one started on `items`, `stub` a smoke
    run's loopback stand-in or empty."""
    with _fetches:
        running = FETCHES.get(key)
        if running is not None and running.view()["state"] == "downloading":
            return running
        FETCHES[key] = Fetch(items, stub).start()
        return FETCHES[key]


def current(key: str) -> Fetch | None:
    with _fetches:
        return FETCHES.get(key)


def cancel(key: str) -> Fetch | None:
    """Cancel the demo's running download, and wait the moment it takes to stop and tidy up."""
    running = current(key)
    if running is not None:
        running.cancel()
        running.thread.join(timeout=TIMEOUT + 5)
    return running
