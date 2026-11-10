#!/usr/bin/env python3
"""A test release on this machine, for proving the updater end to end (18 October 2026, the fourth Tauri
build): a throwaway key, a version's files signed with it by `packaging/release.py` itself, a manifest
whose addresses point here, a tampered copy of each file, and a server on this machine alone that hands
them to the test app. Nothing here ever touches the real key, the Keychain or GitHub. The standard library
only, with `packaging/minisign.py` and `release.py` beside it.

    python3 packaging/tauri/update_proof.py key <folder>
        a throwaway key pair in <folder>: update.key, update.key.password, update.key.pub
    python3 packaging/tauri/update_proof.py next
        the newer version a test release is made at, the patch after versions.json's own
    python3 packaging/tauri/update_proof.py notes <file> <version> <date>
        a check's own What's new, an invented section for <version> above docs/whats-new.md's own
    python3 packaging/tauri/update_proof.py release <folder> <version> --key <folder> --notes <file>
        [--mac-update <tar.gz>] [--windows <setup.exe>] [--dmg <dmg>] [--base http://127.0.0.1:8798]
        the version signed by release.py with the throwaway key into <folder>, latest-good.json pointing
        here, and latest-tampered.json pointing at a copy of each update file with one byte changed
    python3 packaging/tauri/update_proof.py serve <folder> [--port 8798]
        <folder> served on 127.0.0.1 alone, latest.json being whichever of the two the check copies there

The test app is built with the key's public half and the manifest's address laid over tauri.conf.json
(`build_mac.py` or `build_windows.py` with --test-app --update-key --update-url), which no build that
ships can take. A file missing for one system, the Windows installer on a Mac, the Mac's update on
Windows, is stood in for, so release.py has its three files and signs each as it signs a release.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import socketserver
import struct
import subprocess
import sys
import tempfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKAGING = HERE.parent
TOOL = PACKAGING.parent
sys.path.insert(0, str(PACKAGING))
sys.path.insert(0, str(HERE))

import minisign  # noqa: E402  beside release.py
import release  # noqa: E402

PORT = 8798
BASE = f"http://127.0.0.1:{PORT}"
# a Mach-O header for both of a Mac's architectures, for the Mac's update stood in for on Windows
FAT = struct.pack(">II", 0xCAFEBABE, 2) + struct.pack(">IIIII", 0x01000007, 3, 4096, 16, 12) \
    + struct.pack(">IIIII", 0x0100000C, 0, 8192, 16, 14) + b"\0" * 64
# the invented notes of a check's own version
NOTES = ("The PETs board keeps a dog's walk on the canvas you left it on.",
         "Sift: the record count stays in view as you screen.",
         "Trace: each claim's reference opens beside it.")


class NoLookupServer(ThreadingHTTPServer):
    """A server bound as the standard library binds it, without its lookup of this computer's own name
    (`socket.getfqdn`), which held every server half a minute on the hosted Mac (train 173, family/server.py)."""

    def server_bind(self):
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[:2]


def next_version() -> str:
    """The newer version a test release is made at: the patch after the app's own version in
    versions.json, so a bump of the app never meets a check's own invented notes at the same number
    (20 October)."""
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", release.server_version())
    if not m:
        raise SystemExit("versions.json names no version of three numbers for Idiograph")
    return f"{m[1]}.{m[2]}.{int(m[3]) + 1}"


def make_key(folder: Path) -> Path:
    """A throwaway key pair, sealed under a throwaway password, as `tauri signer generate` makes one."""
    folder.mkdir(parents=True, exist_ok=True)
    password = "a throwaway password for a check, " + folder.name
    secret = minisign.make_secret(password)
    (folder / "update.key").write_text(secret, encoding="utf-8")
    (folder / "update.key.password").write_text(password, encoding="utf-8")
    pub = folder / "update.key.pub"
    pub.write_text(minisign.open_secret(secret, password).public_key(), encoding="utf-8")
    return pub


def make_notes(path: Path, version: str, date: str) -> Path:
    """A check's own What's new: an invented section for `version` above the file's own."""
    own = release.WHATS_NEW.read_text(encoding="utf-8")
    head, _, rest = own.partition("\n## ")
    section = f"## {version}, {date}\n\n" + "\n".join(NOTES) + "\n\n"
    path.write_text(head + "\n" + section + ("## " + rest if rest else ""), encoding="utf-8")
    return path


def stand_in_mac(dest: Path) -> Path:
    """The Mac's update stood in for, an app whose executable names both architectures."""
    sys.path.insert(0, str(HERE))
    import bundle

    with tempfile.TemporaryDirectory() as tmp:
        app = Path(tmp) / "Idiograph.app"
        (app / "Contents" / "MacOS").mkdir(parents=True)
        (app / "Contents" / "MacOS" / "Idiograph").write_bytes(FAT)
        (app / "Contents" / "Info.plist").write_text("<plist/>\n", encoding="utf-8")
        return bundle.update_tarball(app, dest)


def tampered(src: Path, dest: Path) -> Path:
    """A copy of `src` with one byte in its middle changed, its size the same."""
    data = bytearray(src.read_bytes())
    data[len(data) // 2] ^= 0x5A
    dest.write_bytes(bytes(data))
    return dest


def make_release(folder: Path, version: str, key: Path, notes: Path, files: dict[str, Path | None],
                 base: str = BASE) -> dict:
    """The version's three files signed by release.py with the throwaway key, its dry run, then
    latest-good.json with every address on this machine and latest-tampered.json pointing each system
    at a changed copy of its file with the signature of the true one."""
    source = folder / "from"
    shutil.rmtree(source, ignore_errors=True)
    source.mkdir(parents=True)
    for name in release.FILES:
        given = files.get(name)
        if given and Path(given).is_file():
            shutil.copyfile(given, source / name)
        elif name == release.MAC_UPDATE:
            stand_in_mac(source / name)
        else:
            (source / name).write_bytes(f"a stand-in for {name}, which this check never runs\n".encode())
    out = folder / "signed"
    shutil.rmtree(out, ignore_errors=True)
    done = subprocess.run([sys.executable, str(PACKAGING / "release.py"), f"v{version}", "--dry-run", "--test-key", str(key),
                           "--from", str(source), "--out", str(out), "--whats-new", str(notes)],
                          capture_output=True, text=True, encoding="utf-8")
    if done.returncode != 0:
        raise SystemExit(f"release.py refused: {(done.stdout + done.stderr).strip()[-600:]}")
    data = json.loads((out / release.MANIFEST).read_text(encoding="utf-8"))
    for name in (release.MAC_UPDATE, release.WINDOWS):
        shutil.copyfile(out / name, folder / name)
        tampered(out / name, folder / f"tampered-{name}")
    good = json.loads(json.dumps(data))
    bad = json.loads(json.dumps(data))
    for platform, entry in good["platforms"].items():
        name = entry["url"].rsplit("/", 1)[-1]
        entry["url"] = f"{base}/{name}"
        bad["platforms"][platform]["url"] = f"{base}/tampered-{name}"
    (folder / "latest-good.json").write_text(json.dumps(good, indent=2) + "\n", encoding="utf-8")
    (folder / "latest-tampered.json").write_text(json.dumps(bad, indent=2) + "\n", encoding="utf-8")
    shutil.copyfile(folder / "latest-good.json", folder / "latest.json")
    return {"said": done.stdout.strip().splitlines()[-2:], "platforms": sorted(good["platforms"]), "version": good["version"],
            "notes": good["notes"].splitlines()[:1]}


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def serve(folder: Path, port: int = PORT, background: bool = True) -> ThreadingHTTPServer:
    """`folder` served on 127.0.0.1 alone, from a thread of its own unless `background` is off, until
    the caller shuts it down."""
    import functools
    import threading

    server = NoLookupServer(("127.0.0.1", port), functools.partial(Quiet, directory=str(folder)))
    if background:
        threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="A test release on this machine, for proving the updater.")
    sub = ap.add_subparsers(dest="what", required=True)
    sub.add_parser("next")
    k = sub.add_parser("key")
    k.add_argument("folder")
    n = sub.add_parser("notes")
    n.add_argument("file")
    n.add_argument("version")
    n.add_argument("date")
    r = sub.add_parser("release")
    r.add_argument("folder")
    r.add_argument("version")
    r.add_argument("--key", required=True)
    r.add_argument("--notes", required=True)
    r.add_argument("--mac-update")
    r.add_argument("--windows")
    r.add_argument("--dmg")
    r.add_argument("--base", default=BASE)
    s = sub.add_parser("serve")
    s.add_argument("folder")
    s.add_argument("--port", type=int, default=PORT)
    a = ap.parse_args(argv)
    if a.what == "next":
        print(next_version())
    elif a.what == "key":
        print(make_key(Path(a.folder).resolve()))
    elif a.what == "notes":
        print(make_notes(Path(a.file).resolve(), a.version, a.date))
    elif a.what == "release":
        said = make_release(Path(a.folder).resolve(), a.version, Path(a.key).resolve(), Path(a.notes).resolve(),
                            {release.MAC_UPDATE: a.mac_update, release.WINDOWS: a.windows, release.DMG: a.dmg}, a.base)
        print(json.dumps(said, indent=2))
    else:
        server = serve(Path(a.folder).resolve(), a.port, background=False)
        print(f"Serving {a.folder} on 127.0.0.1:{a.port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
