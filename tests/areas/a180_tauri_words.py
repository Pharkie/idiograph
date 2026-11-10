"""Area 180: the fifth Tauri build (18 October 2026), Adam's words for the updater, the crash notice shown
once, a failed start in plain words, the installer's every stock line said plainly, his public key, and
the small things: a `say` that hangs ended, and et_xmlfile pinned where the app sets itself up.

Every string here is Adam's, word for word, from his choice of the screenshot check's suggestions at 11:50
on 18 October, but the failed start's, which follows the crash notice's. Since the test review of 18 October the
words are review shots, and what runs stays: the notice's script in a page, a say that hangs ended, et_xmlfile
pinned, and no pseudonym in what the build ships.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import support
from .support import STUDY_PSEUDONYMS, check, skip

ENDED = "Idiograph stopped unexpectedly."
ENDED_MORE = "What you saved is kept. Close this window and open Idiograph again."


def rust_fn(src: str, name: str) -> str:
    """A Rust function whole, from its `fn` line to the brace at the start of a line that closes it."""
    m = re.search(rf"^(?:pub )?(?:async )?fn {name}\(", src, re.M)
    if not m:
        return ""
    end = src.find("\n}\n", m.start())
    return src[m.start():end + 3] if end > 0 else ""


def ended_script(main_rs: str) -> str:
    """The script `ended_js` hands every page, read from its format string as Rust builds it: each line's
    break and the spaces after it taken out, the doubled braces made single, the two words put in."""
    body = rust_fn(main_rs, "ended_js")
    # the two words, now read from the catalogue by key (words::t_app), Idiograph's as written
    m = re.search(r'format!\(\s*"(.*?)",\s*json!\((?:app::named\(ENDED\)|words::t_app\("menus\.ended"\)|ENDED)\),\s*json!\((?:app::named\(ENDED_MORE\)|words::t_app\("menus\.ended_more"\)|ENDED_MORE)\)', body, re.S)
    if not m:
        return ""
    text = re.sub(r"\\\n\s*", "", m.group(1)).replace("{{", "\x00").replace("}}", "\x01")
    parts = text.split("{}")
    if len(parts) != 3:
        return ""
    text = parts[0] + json.dumps(ENDED) + parts[1] + json.dumps(ENDED_MORE) + parts[2]
    return text.replace("\x00", "{").replace("\x01", "}").replace('\\"', '"')


def test_tauri_words(scratch):
    print("\n180. The fifth Tauri build (18 October): Adam's words for the updates (Relaunch again since the sixth, area 184), Download updates "
          "without asking, the privacy line and the refused update, the crash notice in his words and shown once, a "
          "failed start in plain words, the installer's stock lines plain, his public key, a say that hangs ended, "
          "et_xmlfile pinned where the app sets itself up, and the Windows checks of each")
    tauri = support.source("packaging/tauri")
    src = tauri / "src-tauri"
    read = lambda p: Path(p).read_text(encoding="utf-8")  # noqa: E731
    main_rs = read(src / "src" / "main.rs")
    english, hooks = read(src / "windows" / "English.nsh"), read(src / "windows" / "hooks.nsh")
    node = shutil.which("node")

    # ── C. the crash notice in Adam's words, shown once
    script = ended_script(main_rs)
    if node and script:
        harness = scratch / "ended-180.js"
        harness.write_text(r"""
const script = process.argv[2];
function run(withPage) {
  const t = { calls: [], invoked: [], toast: { hidden: false } };
  const document = { getElementById: (id) => (id === 'toast' ? t.toast : null) };
  const window = { __TAURI_INTERNALS__: { invoke: (cmd, args) => { t.invoked.push([cmd, args]); return Promise.resolve(true); } } };
  const page = withPage ? { serverGone: (head, line) => t.calls.push([head, line]) } : {};
  new Function('document', 'window', 'serverGone', script)(document, window, page.serverGone);
  return { calls: t.calls, invoked: t.invoked, toastHidden: t.toast.hidden };
}
console.log(JSON.stringify({ page: run(true), none: run(false) }));
""", encoding="utf-8")
        # the page's own serverGone is a global, which the script names bare, so it is handed in by that name
        run = subprocess.run([node, str(harness), script], capture_output=True, text=True, encoding="utf-8")
        try:
            got = json.loads(run.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            got = {"error": (run.stdout + run.stderr)[-400:], "script": script[:300]}
        check("180: the script each page is handed covers the page with Adam's two lines and then says so through "
              "closing, step ended, and a page without the app's notice says nothing, so the system's notice says it",
              got.get("page", {}).get("calls") == [[ENDED, ENDED_MORE]]
              and got.get("page", {}).get("invoked") == [["closing", {"step": "ended"}]] and got.get("page", {}).get("toastHidden") is True
              and got.get("none", {}).get("calls") == [] and got.get("none", {}).get("invoked") == [], json.dumps(got)[:500])
    else:
        skip("180: the page's notice script under node", "node is not on this machine" if not node else "the script was not found")

    # ── G. a say that hangs ended, the build carrying on
    sys.path.insert(0, str(support.source("packaging")))
    import build_mac
    bm = read(support.source("packaging/build_mac.py"))
    if sys.platform == "win32":
        skip("180: a say that hangs ended, and the recording the build carries on with", "a process group is ended on a Mac or Linux alone")
    else:
        hang = scratch / "hang"
        hang.mkdir()
        fake_py = hang / "fake-python"
        marker = hang / "child.pid"
        # a stand-in for the build venv's python: it starts a child that sleeps, as make_demo starts say, and hangs
        fake_py.write_text(f"#!/bin/sh\nsleep 120 &\necho $! > '{marker}'\nwait\n", encoding="utf-8")
        fake_py.chmod(0o755)
        t0 = time.time()
        why = build_mac.speak_recording(fake_py, hang / "kept.m4a", wait=1)
        took = time.time() - t0
        written = marker.read_text(encoding="utf-8").strip() if marker.is_file() else ""
        child = int(written) if written.isdigit() else 0

        def alive(pid: int) -> bool:
            try:
                os.kill(pid, 0)
                return True
            except (OSError, ValueError):
                return False
        # the ended child is gone once the system has taken it back, a moment after
        gone_by = time.time() + 5
        while child and alive(child) and time.time() < gone_by:
            time.sleep(0.2)
        child_alive = bool(child) and alive(child)
        old = (build_mac.RECORDING, build_mac.TRANSCRIPT, build_mac.RECORDINGS, build_mac.speak_recording)
        transcript = hang / "Juno - interview.csv"
        transcript.write_bytes(b"Name,Timestamp,Transcript\r\nJuno,00:00:01,About the dog\r\n")
        cached_dir = hang / "recordings"
        cached_dir.mkdir()
        import hashlib
        text_sum = hashlib.sha256(transcript.read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:16]
        cached = cached_dir / f"Juno-Initial-{text_sum}.m4a"
        cached.write_bytes(b"a recording of the check's own")
        try:
            build_mac.RECORDING = Path("no-such-folder") / "Juno-Initial.m4a"
            build_mac.TRANSCRIPT, build_mac.RECORDINGS = transcript, cached_dir
            build_mac.speak_recording = lambda py, kept, wait=None: "Speaking had not finished after 15 minutes and was ended"
            with_cache = build_mac.recording(hang / "build", fake_py)
            cached.unlink()
            without = build_mac.recording(hang / "build2", fake_py)
        finally:
            build_mac.RECORDING, build_mac.TRANSCRIPT, build_mac.RECORDINGS, build_mac.speak_recording = old
        check("180: a say that hangs is ended within its wait, the child it started gone with it, and the build carries "
              "on with the recording spoken for this transcript, or without one",
              why is not None and why.startswith("Speaking had not finished after") and took < 10 and child and not child_alive
              and with_cache == cached and without is None and not list((hang / "build" / "recording").glob("*.m4a")),
              f"{why} {took:.1f}s child {child} alive {child_alive} cache {with_cache} without {without}")

    # ── H. et_xmlfile pinned where the app sets itself up
    run_sh, run_bat = read(support.source("run.sh")), read(support.source("run.bat"))
    pin = next((p for p in build_mac.PINS if p.startswith("et_xmlfile==")), "")
    suite_pin = re.findall(r"et_xmlfile==[0-9.]+", read(support.source(".github/workflows/windows-installer.yml")))
    check("180: run.sh and run.bat install et_xmlfile at 2.0.0 beside openpyxl, the version the build and GitHub's "
          "suite pin, so a copy run from source writes as the suite tests it",
          pin == "et_xmlfile==2.0.0" and set(suite_pin) == {pin}
          and f'ET_XMLFILE="{pin}"' in run_sh and '-q "$OPENPYXL" "$ET_XMLFILE"' in run_sh
          and f'set "ET_XMLFILE={pin}"' in run_bat and '-q "%OPENPYXL%" "%ET_XMLFILE%" "%CRYPTOGRAPHY%" || goto failed' in run_bat
          and b"\r\n" in support.source("run.bat").read_bytes() and support.source("run.bat").read_bytes().count(b"\n") == support.source("run.bat").read_bytes().count(b"\r\n"))


    # ── J. no study's participant named in what the build ships
    new_text = "\n".join([english, hooks, rust_fn(main_rs, "not_started"), rust_fn(main_rs, "ended_js"),
                          bm[bm.index("def recording("):bm.index("def stage_config(")]])
    check("180: what the fifth build ships names no study's participant",
          not any(re.search(rf"\b{n}\b", new_text) for n in STUDY_PSEUDONYMS))
