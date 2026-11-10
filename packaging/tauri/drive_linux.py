#!/usr/bin/env python3
"""The Linux window started once, run by the `linux-app` job of `.github/workflows/windows-installer.yml`
(linux3, 8 November 2026, build 3 of the Linux plan) under `xvfb-run`, on a built AppImage or on the
executable of an installed .deb.

    xvfb-run -a dbus-run-session -- python3 packaging/tauri/drive_linux.py --app dist/Idiograph-x86_64.AppImage
        --id idiograph --out build/drive-linux

It proves the window starts, that its server serves and that it ends when asked. It does not prove how
anything looks, which needs a person on a Linux desktop. The steps:

1. The app started in a session of its own with a home folder of its own and every XDG folder left to
   default inside it, DISPLAY the virtual one xvfb gave, `IDIOGRAPH_PORT` a free port,
   `IDIOGRAPH_STAY_OPEN=1` so it never ends by itself, `IDIOGRAPH_WINDOW_NO_OPEN` so no link goes to a
   browser, and for an AppImage `APPIMAGE_EXTRACT_AND_RUN=1`, so a machine with no FUSE runs it too.
   WebKitGTK is told to draw in software (`WEBKIT_DISABLE_COMPOSITING_MODE`, `WEBKIT_DISABLE_DMABUF_RENDERER`,
   `LIBGL_ALWAYS_SOFTWARE`), since a hosted machine has no GPU.
2. `/api/server` asked until it answers, and its `app` must be the one named and its `window` true, which
   only a server the window started is (`IDIOGRAPH_WINDOW`).
3. The page asked for (`/`), which must be an HTML page.
4. A window on the virtual screen looked for with `xwininfo -root -tree` where it is installed, and the
   result kept in `results.json`. It is a note, never a failure, since no window manager runs and the title
   is the page's.
5. A SIGTERM to the app's whole process group, which the window hears as Quit (the server stopped first),
   and the run fails unless the window ends and the port closes within a time.

Every result goes in `results.json` beside the app's log in `--out`, and the log's last lines are printed
on a failure. The standard library only. Nothing here reaches any service but this machine's.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

START_WAIT = 120
END_WAIT = 40
# what makes WebKitGTK draw on a machine with no GPU and a virtual screen
SOFTWARE = {"WEBKIT_DISABLE_COMPOSITING_MODE": "1", "WEBKIT_DISABLE_DMABUF_RENDERER": "1", "LIBGL_ALWAYS_SOFTWARE": "1"}


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def listening(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def environment(home: Path, port: int, base: dict | None = None, appimage: bool = False) -> dict:
    """The app's environment for the run: a home of its own, no XDG folder of the machine's, the virtual
    display kept, the port, and the software drawing."""
    env = {k: v for k, v in (os.environ if base is None else base).items()
           if not k.startswith("XDG_") and k not in ("WAYLAND_DISPLAY", "BROWSER", "APPDIR", "APPIMAGE")}
    env.update(HOME=str(home), IDIOGRAPH_PORT=str(port), IDIOGRAPH_STAY_OPEN="1", IDIOGRAPH_WINDOW_NO_OPEN="1",
               PYTHONUNBUFFERED="1", **SOFTWARE)
    if appimage:
        env["APPIMAGE_EXTRACT_AND_RUN"] = "1"
    return env


def get(port: int, path: str, timeout: float = 3) -> str | None:
    """A GET of the server's `path` as text, or None when nothing answers."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=timeout) as got:
            return got.read().decode("utf-8", errors="replace")
    except (OSError, ValueError, urllib.error.URLError):
        return None


def windows_seen() -> str:
    """The virtual screen's windows by `xwininfo -root -tree`, or why they cannot be listed."""
    tool = shutil.which("xwininfo")
    if not tool or not os.environ.get("DISPLAY"):
        return "not listed (no xwininfo or no display)"
    done = subprocess.run([tool, "-root", "-tree"], capture_output=True, text=True, timeout=20)
    return done.stdout if done.returncode == 0 else f"not listed ({done.stderr.strip()[:200]})"


def last(log: Path, n: int = 40) -> str:
    try:
        return "".join(log.read_text(encoding="utf-8", errors="replace").splitlines(True)[-n:])
    except OSError:
        return ""


def end_group(proc: subprocess.Popen, seconds: float) -> float | None:
    """SIGTERM to `proc`'s whole group, which an AppImage's runtime, its window and the window's server all
    belong to, and the seconds until the leader ends, or None when it is still running after `seconds`."""
    begun = time.monotonic()
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return 0.0
    try:
        proc.wait(timeout=seconds)
    except subprocess.TimeoutExpired:
        return None
    return round(time.monotonic() - begun, 2)


def drive(app: Path, app_id: str, out: Path, start_wait: float = START_WAIT, end_wait: float = END_WAIT) -> dict:
    """The run. Answers the results, and raises SystemExit on the first thing that is wrong, with the log."""
    out.mkdir(parents=True, exist_ok=True)
    log = out / f"{app_id}-window.log"
    results: dict = {"app": str(app)}
    port = free_port()
    with tempfile.TemporaryDirectory(prefix="idiograph-drive-") as tmp:
        home = Path(tmp) / "home"
        home.mkdir()
        env = environment(home, port, appimage=app.name.endswith(".AppImage"))
        with open(log, "w", encoding="utf-8") as sink:
            proc = subprocess.Popen([str(app)], env=env, stdin=subprocess.DEVNULL, stdout=sink, stderr=subprocess.STDOUT,
                                    start_new_session=True)

        def fail(why: str) -> None:
            if proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait()
            results["failed"] = why
            (out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
            raise SystemExit(f"{why}\n--- {log.name}, its last lines:\n{last(log)}")

        try:
            state, end = None, time.monotonic() + start_wait
            while time.monotonic() < end and proc.poll() is None:
                text = get(port, "/api/server")
                if text:
                    try:
                        state = json.loads(text)
                        break
                    except ValueError:
                        pass
                time.sleep(0.5)
            if state is None:
                ended = f" (it ended with {proc.returncode})" if proc.poll() is not None else ""
                fail(f"The window's server did not answer /api/server within {start_wait:.0f} seconds{ended}.")
            results["server"] = state
            if state.get("app") != app_id:
                fail(f"The server answered as {state.get('app')!r}, not {app_id!r}.")
            if state.get("window") is not True:
                fail("The server does not say it was started by the window.")
            print(f"The window's server serves: {state.get('app')}, in the window, pid {state.get('pid')}", flush=True)

            page = get(port, "/") or ""
            results["page_bytes"] = len(page)
            if "<html" not in page.lower():
                fail("The page at / is not an HTML page.")
            print(f"The page is served, {len(page)} bytes", flush=True)

            results["windows"] = windows_seen()[:3000]
            took = end_group(proc, end_wait)
            results["ended_in_seconds"] = took
            if took is None:
                fail(f"The window did not end within {end_wait:.0f} seconds of SIGTERM.")
            closed = False
            for _ in range(int(end_wait * 5)):
                if not listening(port):
                    closed = True
                    break
                time.sleep(0.2)
            results["port_closed"] = closed
            if not closed:
                fail("The server still listens after the window ended.")
            print(f"The window ended in {took} s and the server's port closed", flush=True)
        finally:
            if proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait()
    (out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Start the Linux window once, check it serves, and end it.")
    ap.add_argument("--app", required=True, help="the AppImage, or the installed window's executable")
    ap.add_argument("--id", default="idiograph", choices=("idiograph", "sift", "trace"), help="the app, which /api/server must say")
    ap.add_argument("--out", default="build/drive-linux", help="where the log and results.json go")
    args = ap.parse_args(argv)
    if not sys.platform.startswith("linux"):
        raise SystemExit("The Linux window is driven on Linux, under xvfb-run, as GitHub's ubuntu-22.04 machine does it.")
    app = Path(args.app).resolve()
    if not app.is_file():
        raise SystemExit(f"{app} is not a file.")
    drive(app, args.id, Path(args.out).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
