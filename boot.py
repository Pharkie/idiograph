"""Where the family's code and files are, the one place that decides (22 October 2026, the family
codebase's first build).

The codebase is one family of three apps. `family/` holds what every app shares and `apps/<app>/`
each app's own, each folder an import root, so a module keeps its plain name (`import sift`) wherever
it sits. Every entry, the root `server.py`, `cli.py` and `mcp_server.py` (since the fourth build the shims of
the family's modules of those names, see `shim`), the launchers, the make_* tools, the build scripts and
the suite, calls `setup` first, which puts those folders on `sys.path`.

`ROOT` is the folder the code runs from: this file's own from source, and in a frozen build the one
PyInstaller unpacks to (`sys._MEIPASS`), where a build has merged each folder's files into one tree.
`resource(path)` is a file the code reads beside itself, a page, a guide or a schema, found in an app's
folder, then the family's, then at the root, and frozen at the root alone.

The standard library only, so a launcher reads it before anything else is loaded.
"""
from __future__ import annotations

import sys
from pathlib import Path

FROZEN = bool(getattr(sys, "frozen", False))
ROOT = Path(sys._MEIPASS) if FROZEN and hasattr(sys, "_MEIPASS") else Path(__file__).resolve().parent
FAMILY = ROOT / "family"
APPS_DIR = ROOT / "apps"
# the family's three apps, each with a folder under apps/, Idiograph first as app_identity has them
APPS = ("idiograph", "sift", "trace")


def app_folders(app: str | None = None) -> list[Path]:
    """The folders of the apps a run serves: every app's when `app` is None, else the app's own and
    those app_identity's SERVES_TOO gives it."""
    if app is None:
        names = APPS
    else:
        import app_identity  # the family's, on the path by now
        names = app_identity.served(app)
    return [APPS_DIR / name for name in names]


def setup(app: str | None = None) -> list[Path]:
    """The family's folder, the served apps' folders and the root at the head of `sys.path`, in that
    order, each once, so nothing installed elsewhere can stand in for one of the family's modules. The root
    comes last of them (the fourth build, 22 October 2026): its server.py, cli.py and mcp_server.py are the
    shims of the family's modules of those names (see `shim`), and `import server` finds family/server.py.
    The folders stand where the first of them stood, at the head when none did. Called again it changes
    nothing. Returns the folders."""
    if str(FAMILY) not in sys.path:
        # app_identity, which says the apps a run serves, is the family's
        sys.path.insert(0, str(FAMILY))
    folders = [FAMILY] + app_folders(app) + [ROOT]
    want = [str(f) for f in folders]
    at = min((sys.path.index(w) for w in want if w in sys.path), default=0)
    if sys.path[at:at + len(want)] != want:
        rest = [p for p in sys.path if p not in want]
        before = [p for p in sys.path[:at] if p not in want]
        sys.path[:] = before + want + rest[len(before):]
    return folders


def shim(name: str, module: str):
    """A root shim's whole work (the fourth build, 22 October 2026): the root's server.py, cli.py and
    mcp_server.py stand for the family's modules of those names, which Restart, run.sh, run.command,
    run.bat, the root's commands and an MCP client's settings name by their paths. Run as a script, `name`
    being `__main__`, the family's module runs with the script's arguments, its `script` where it has one,
    else its `main`, and the process ends with what that answers. Imported, as only code that skipped
    `setup` can, the family's module takes the shim's place under its name and is answered."""
    import importlib
    setup()
    if name != "__main__":
        sys.modules.pop(module, None)
        return importlib.import_module(module)
    found = importlib.import_module(module)
    raise SystemExit(getattr(found, "script", found.main)())


def load(kind: str) -> list:
    """Each app's registrations of one kind (the family codebase's second build, 22 October 2026): the
    module `<app>_<kind>` of each app that has one, `trace_routes`, `trace_cli`, `trace_mcp` or
    `trace_find`, imported by its name, in the family's order, each registering itself with the family's
    module that called this as it is first imported. The family's code names no app's module, and an app
    with no such module, or a build that leaves an app out, is passed over. Answers the modules imported."""
    import importlib
    done = []
    for app in APPS:
        name = f"{app}_{kind}"
        try:
            done.append(importlib.import_module(name))
        except ModuleNotFoundError as exc:
            if exc.name != name:
                raise
    return done


def roots(apps=None) -> list[Path]:
    """The folders a file the code reads is looked for in, in order: each app's, or those of `apps` alone,
    the family's, the root. Frozen, the root alone, where the build merged the family's and its own app's."""
    if FROZEN:
        return [ROOT]
    return [APPS_DIR / name for name in APPS if apps is None or name in apps] + [FAMILY, ROOT]


def resource(path: str | Path) -> Path:
    """A file or folder the code reads beside itself, by its path from the root as it ships, `static/
    index.html` or `docs/agents.md`: the first folder of `roots` that has it, else the root's, so a
    missing file is named where it always was."""
    rel = Path(path)
    for base in roots():
        found = base / rel
        if found.exists():
            return found
    return ROOT / rel
