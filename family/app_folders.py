"""Where the installed app keeps what it writes, by platform: the one place that decides.

The Mac app and the Windows app each keep their settings, the recent list, the key file where
there is no keychain and the demo in a data folder of the user's, the launcher's log and pid file in
a logs folder, and every launch's two lines in a trace file, all outside the folder the app is
installed in, so a newer version put over the old one finds every setting and case where it left
them. `server.app_paths` takes the data and logs folders from here, and each launcher, the Mac's
`packaging/mac_launcher.py` and Windows's `packaging/windows_launcher.py`, its logs folder and
trace file. The standard library only, so a launcher reads it before anything else is loaded.

    Mac       data  ~/Library/Application Support/Idiograph
              logs  ~/Library/Logs/Idiograph
              trace /tmp/idiograph-launch.log
    Windows   data  %APPDATA%\\Idiograph
              logs  %LOCALAPPDATA%\\Idiograph\\Logs
              trace %TEMP%\\idiograph-launch.log
    Linux     data  $XDG_DATA_HOME/Idiograph (~/.local/share/Idiograph)
              logs  $XDG_STATE_HOME/Idiograph/logs (~/.local/state/Idiograph/logs)
              config $XDG_CONFIG_HOME/Idiograph, cache $XDG_CACHE_HOME/Idiograph (~/.config, ~/.cache)
              trace /tmp/idiograph-launch.log
    A source user's folders on Linux from before this, in the Mac's layout under ~/Library, are moved
    once by `move_legacy` (8 November 2026).
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import app_identity

NAME = "Idiograph"
TRACE_FILE = "idiograph-launch.log"
# the Windows app's two executables in its install folder: the windowed one a double-click runs,
# which runs the server too, and its console twin for the command line and the MCP server, since a
# windowed program cannot print to the terminal that ran it
WINDOWED_EXE = "Idiograph.exe"
CONSOLE_EXE = "Idiograph-console.exe"


def windowed_exe(app: str | None = None) -> str:
    """The windowed executable of `app`, `Idiograph.exe`, `Sift.exe` or `Trace.exe`, the name by which
    a frozen server knows which app it is (`app_identity.from_executable`)."""
    return f"{app_identity.APPS[app_identity.check(app)]['name']}.exe"


def console_exe(app: str | None = None) -> str:
    """The console twin of `app`, `Idiograph-console.exe`, `Sift-console.exe` or `Trace-console.exe`."""
    return f"{app_identity.APPS[app_identity.check(app)]['name']}-console.exe"


def is_windows(system: str | None = None) -> bool:
    return (system or sys.platform).startswith("win")


def is_linux(system: str | None = None) -> bool:
    return (system or sys.platform).startswith("linux")


def utf8_streams() -> None:
    """Standard output and error write UTF-8 when they go to a pipe or a file, as an agent reading
    the command line or a log expects, never in the system's own code page, which on Windows lacks
    some of the app's characters, its arrows among them. A console keeps its own, which shows them
    all. The command line, the MCP server and the server each call it as they start (14 October)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            if stream is not None and not stream.isatty():
                stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def folders(system: str | None = None, home: Path | None = None, env: dict | None = None,
            app: str | None = None) -> dict:
    """The data folder, the logs folder and the trace file, for `system` (`sys.platform` by default),
    of `app`, one of the family's three, Idiograph by default (see `app_identity`): Sift's are
    `Application Support/Sift`, `Logs/Sift` and `/tmp/sift-launch.log`, Trace's the same.

    On Windows they come from APPDATA, LOCALAPPDATA and TEMP, each with its usual place under the home
    folder when it is not set. A `home` given is a trial's: the environment is then left out unless
    `env` is given too, so a check builds the same folders on any machine."""
    name = app_identity.APPS[app_identity.check(app)]["folder"]
    trace = f"{name.lower()}-launch.log"
    given = home is not None
    home = Path(home) if given else Path.home()
    env = ({} if given else os.environ) if env is None else env
    if is_windows(system):
        local = Path(env.get("LOCALAPPDATA") or home / "AppData" / "Local")
        roaming = Path(env.get("APPDATA") or home / "AppData" / "Roaming")
        temp = Path(env.get("TEMP") or env.get("TMP") or local / "Temp")
        return {"data": roaming / name, "logs": local / name / "Logs", "trace": temp / trace}
    if is_linux(system):
        def xdg(var: str, default: str) -> Path:
            value = env.get(var) or ""
            # the XDG rule: a relative value is invalid and ignored
            return Path(value) if value and os.path.isabs(value) else home / default
        return {"data": xdg("XDG_DATA_HOME", ".local/share") / name,
                "logs": xdg("XDG_STATE_HOME", ".local/state") / name / "logs",
                "config": xdg("XDG_CONFIG_HOME", ".config") / name,
                "cache": xdg("XDG_CACHE_HOME", ".cache") / name,
                "trace": Path("/tmp") / trace}
    library = home / "Library"
    return {"data": library / "Application Support" / name, "logs": library / "Logs" / name,
            "trace": Path("/tmp") / trace}


def _has_files(folder: Path) -> bool:
    return folder.is_dir() and any(folder.iterdir())


def move_legacy(system: str | None = None, home: Path | None = None, env: dict | None = None,
                app: str | None = None) -> list:
    """On Linux, the one-time move of a source user's folders from the Mac's layout to the XDG ones:
    `~/Library/Application Support/<name>` to the data folder and `~/Library/Logs/<name>` to the logs
    folder. Each is moved whole, never copied, so nothing is left behind and a second call finds nothing
    to do. A folder is never moved onto one that already holds files, since those are newer. Anything
    but Linux does nothing. The folders moved are returned."""
    if not is_linux(system):
        return []
    given = home is not None
    base = Path(home) if given else Path.home()
    where = folders(system, base if given else None, env, app)
    name = app_identity.APPS[app_identity.check(app)]["folder"]
    library = base / "Library"
    moved = []
    for old, new in ((library / "Application Support" / name, where["data"]), (library / "Logs" / name, where["logs"])):
        if not old.is_dir() or old.is_symlink() or _has_files(new):
            continue
        try:
            new.parent.mkdir(parents=True, exist_ok=True)
            if new.is_dir():
                new.rmdir()
            shutil.move(str(old), str(new))
        except OSError:
            continue
        moved.append(new)
    for parent in (library / "Application Support", library / "Logs", library):
        try:
            parent.rmdir()          # only an empty one goes
        except OSError:
            pass
    return moved
