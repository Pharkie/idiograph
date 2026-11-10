"""The family's server (22 October 2026, the family codebase's fourth build, from the root's server.py): the
one server every app of the family runs on, a tab at localhost, the page and the JSON API from the standard
library, so openpyxl is the only dependency anyone needs to install.

What every app shares is here: the paths and the settings, the recent list, the key and the models, Send
feedback, What's new, the manual, Restart and Quit, the family on each Home, the page's assembly, the
handler and `main`. Each app's own routes, Idiograph's in apps/idiograph/idiograph_routes.py, Sift's and
Trace's in theirs, register with it (`register`) as `boot.load("routes")` at the foot of this file imports
them by their names, so the server names no app's module. The root's server.py runs it, as run.sh,
run.command, run.bat and Restart do:

    ./run.sh                                     # from the app's folder, run.command or run.bat alike
    .venv/bin/python Tools/idiograph/server.py   # from the repo root

Options: --app (idiograph by default, sift or trace), --port (the app's own, 8765 for Idiograph), --no-browser, --root "<folder>" for a run of that one project,
--config "<file>" to read and write settings there instead of config.json.
"""
from __future__ import annotations

import argparse
import contextlib
import functools
import hmac
import html
import json
import mimetypes
import os
import platform
import re
import secrets
import shlex
import shutil
import socketserver
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import urlparse, parse_qs

# every entry puts the family's folders on the path first (boot.py), the root's server.py among them, so
# each module is found by its plain name wherever it sits. HERE is the root, the app's folder from source
if not getattr(sys, "frozen", False) and str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import boot  # noqa: E402

boot.setup()
HERE = boot.ROOT

try:
    import openpyxl  # noqa: F401
except ImportError:
    raise SystemExit(
        "openpyxl is needed. Start Idiograph with run.command on a Mac, run.bat on Windows or\n"
        "run.sh on Linux, in this folder, and its first run sets it up."
    )

import agent_log
import ai_suggest as ai_mod
import app_folders
import app_identity
import app_search
import i18n
import locks
from errors import WorkbookError, refusal

# Run from the Mac app, Idiograph.app built by packaging/build_mac.py, the code is frozen inside the
# bundle and nothing may write there. Run from source, it is this folder as it always was.
FROZEN = bool(getattr(sys, "frozen", False))
# Which of the family's three apps this run is (see `app_identity`): frozen, the launcher's own name
# says, and else Idiograph until `--app` says otherwise (see `use_app`). Idiograph's run is as it was
APP = app_identity.chosen([], FROZEN)


def source_base(here: Path = HERE) -> Path:
    """The folder a relative path is taken from, run from source.

    In the repo this folder is `Tools/<name>`, and a relative path starts at the repo root, two
    folders up, as it always has. A downloaded copy, the GitHub copy with this folder at its top, is
    the folder alone, and a relative path starts here, inside the copy. A folder whose parent is
    called Tools is the repo's, unless it carries a `.git` or a `.venv` of its own, as a clone and a
    copy its first run has set up do."""
    here = Path(here)
    if here.parent.name == "Tools" and not (here / ".git").exists() and not (here / ".venv").exists():
        return here.parent.parent
    return here


def app_paths(bundle: bool = FROZEN, home: Path | None = None, system: str | None = None,
              app: str | None = None) -> dict:
    """Where the files the app writes live, the one place that decides.

    From source: beside the app, as always, with relative paths taken from `source_base`. Frozen:
    the data folder `app_folders.folders` gives, on a Mac `~/Library/Application Support/Idiograph`
    and on Windows `%APPDATA%\\Idiograph`, with the settings, the recent list, the key file where
    there is no keychain and the demo, copied there from the bundle's own copy, which Reset demo
    restores from. A launcher's log and pid file are in its logs folder either way, on a Mac
    `~/Library/Logs/Idiograph` and on Windows `%LOCALAPPDATA%\\Idiograph\\Logs`.

    `app` is one of the family's three, this run's by default. Sift's and Trace's frozen folders are
    their own, `Application Support/Sift` beside Idiograph's, and from source their settings and
    recent list are `config.sift.json` and `state.sift.json` beside Idiograph's (Trace's likewise),
    with the key file beside the code that all three share.
    """
    app = app_identity.check(app or APP)
    if system is None and home is None:
        app_folders.move_legacy(app=app)      # Linux only: a source user's Mac-layout folders, once
    where = app_folders.folders(system, home, app=app)
    support, logs = where["data"], where["logs"]
    data = support if bundle else HERE
    names = {"config": "config.json", "state": "state.json"} if bundle else app_identity.file_names(app)
    return {"data": data, "base": data if bundle else source_base(HERE), "app": app,
            "config": data / names["config"], "state": data / names["state"], "env": data / ".env",
            "demo": data / "demo", "shipped_demo": boot.resource("demo"), "logs": logs}


PATHS = app_paths()
REPO_ROOT = PATHS["base"]
# the app's version, which a note sent from Send feedback carries so a bug can be placed, and which
# both builds read. Its last number goes up each time a build is sent to a tester (15 October). Each
# app's is in versions.json since the three-app split (20 October), read here and by every build
VERSION = app_identity.version(APP)
# the commit a copy built on Adam's Mac each day was made from, empty in a release and from source (macdaily,
# 9 November 2026). About shows it after the version, and a note from Send feedback carries it with the version
BUILD = app_identity.build()
IDENTITY = app_identity.identity(APP)
CONFIG_PATH = PATHS["config"]
STATE_PATH = PATHS["state"]

# A GRAVITY case folder is `P<n> - Pseudonym-Secondname`, and the second name never reaches the
# screen. Every case label the server hands the page goes through display_case, which keeps the
# pseudonym part. The paths keep the folder as it is, because the server needs them to find it.
CASE_FOLDER = re.compile(r"^(P\d+ - [A-Z][a-z]+)-[A-Z][a-z]+$")

# The bundled demo: invented interviews that ship with the app, so the whole interface can be
# recorded without a participant's words on the screen. It sits beside the app rather than under
# the case root, and the root guard below lets this one folder through as well.
DEMO_DIR = PATHS["demo"]
# the demo as the app ships it, the same folder from the repo and read-only inside the Mac app
SHIPPED_DEMO = PATHS["shipped_demo"]
DEMO_CASE = DEMO_DIR / "Juno"
DEMO_WORKBOOK = DEMO_CASE / "Juno - EN & ES.xlsx"

# A project is a root folder holding its case folders. Its settings, the research question first,
# live in one file at its root, read afresh on every request. The demo is a project of its own: its
# file is committed beside it, and it never reads or writes a file at any other root.
PROJECT_FILE = "idiograph-project.json"
DEMO_PROJECT = DEMO_DIR / PROJECT_FILE

# The settings every app keeps, the family's, in the order a settings file holds them. Each app's own are put
# in among them by its registration (`place_defaults`, the family codebase's fourth build, 22 October 2026),
# Idiograph's from apps/idiograph/idiograph_routes.py and Sift's from apps/sift/sift_routes.py, so a file keeps
# the order it always had, and since the sixth build (23 October 2026) only for the apps a run serves (see
# `defaults`), where until then a Sift or Trace save wrote Idiograph's corpus, themes and nudges into its own file.
DEFAULTS = {
    # The projects, in the order they were added, each `{"root": "<folder>"}`. None until one is
    # added, so the case list asks for a folder (see `add_project`). No study's folder is named here
    "projects": [],
    # The status bar along the foot of a board (19 October), General's, which every app saves (23 October)
    "status_bar": True,
    # AI features, the one switch for every AI feature in the app, off on a new install, and a
    # config that has the key keeps its value. The key is read only when he asks for a suggestion.
    # `ai_provider` is `anthropic` or `local`:
    # `model` is the Anthropic model, chosen in settings, and `local_model` the Ollama one at
    # `local_url`, which needs no key.
    "ai_suggest": False,
    "ai_provider": ai_mod.ANTHROPIC,
    "model": ai_mod.MODEL,
    "local_url": ai_mod.LOCAL_URL,
    "local_model": "",
    # and the OpenAI-style providers (aiwire, 8 November 2026): Mistral, Google Gemini, OpenAI, Azure OpenAI,
    # Another service and LM Studio. `ai_address` is Azure's or Another service's address, `ai_deployment`
    # Azure's deployment, `ai_api_version` Azure's api-version, `other_model` the model Another service is
    # asked, and `ai_models` the model each of the others is asked, by provider. A key is each provider's
    # own item in the keychain and never in this file
    "ai_address": "",
    # LM Studio's address, its usual one by default, as `local_url` is Ollama's (aipage, 8 November 2026)
    "lmstudio_url": ai_mod.LMSTUDIO_URL,
    "ai_deployment": "",
    "ai_api_version": ai_mod.AZURE_API_VERSION,
    "other_model": "",
    "ai_models": {},
    # Celebrations, under General in settings: the confetti, the count, the line a break shows and
    # the PETs count, on by default, and Sound, the soft tick and the chimes, off by default and
    # only ever with Celebrations on
    "celebrations": True,
    # and since 20 October a switch for each screen, Experiential statements, PETs and GETs (Adam's call),
    # a file from before them read as all three as `celebrations` says (see `celebrations_of`), and
    # `celebrations` kept true while any is on, for a page or an app from before
    "celebration_screens": {"statements": True, "pets": True, "gets": True},
    "sound": False,
    # The tick at the end of General in Settings (16 October, after a tester closed the tab and found
    # the app still running): the server quits by itself a few minutes after its last tab closes,
    # unless something is still running (see `idle_quit`). On for a new install, and a config without
    # the key reads on. Off, it runs until Quit
    "quit_when_closed": True,
}


# each app's own settings with their defaults, the blocks its registration gives (see `register`)
APP_DEFAULTS: dict = {}


def place_defaults(items: list, blocks) -> list:
    """An app's own settings put among the settings `items`, each block `(key, {setting: default})` before that
    key, after any block another app put there first, so a settings file holds every key in the order it always
    has. Answers the items."""
    items = list(items)
    for before, block in blocks:
        at = next(i for i, (key, _) in enumerate(items) if key == before)
        held = {key for key, _ in items}
        items[at:at] = [(key, value) for key, value in block.items() if key not in held]
    return items


def defaults(app: str | None = None) -> dict:
    """The settings a run of `app` keeps with their defaults, this run's by default: the family's with the own
    settings of each app it serves put in among them, in the family's order of the apps (the family codebase's
    sixth build, 23 October 2026), so Sift's file takes Sift's and Idiograph's Idiograph's."""
    items = list(DEFAULTS.items())
    served = apps_served(app)
    for own in (a for a in boot.APPS if a in served):
        items = place_defaults(items, APP_DEFAULTS.get(own, ()))
    return dict(items)

ENV_PATH = PATHS["env"]
SAMPLE_CSV = DEMO_DIR / "source" / "Juno - interview.csv"
# The statements Juno's demo workbook ships with, which the examples rail and the prompt's
# {examples} fall back on when this machine has no corpus and no reference set
DEMO_EXAMPLES = DEMO_DIR / "pristine" / DEMO_WORKBOOK.name

# The live model list, held for an hour so opening settings does not ask the API every time. Only
# a live answer is held, and saving or removing the key lets it go.
MODEL_CACHE_SECONDS = 3600
_model_cache: dict = {"at": 0.0, "answer": None}

_lock = threading.Lock()


ROOT_OVERRIDE: str | None = None        # set by --root, a run of that one project, never saved
# A run with --root keeps its recent list here, in memory, and never reads or writes state.json.
# A trial or smoke server used to share the live list and have it copied back afterwards, which put
# back the order from before any case Adam opened on his own server while it ran.
STATE_MEMORY: dict | None = None
# A restart of such a run carries the list across in its environment, under this name, as JSON, so
# its Sift and Trace projects and its recent cases stand as they did, where a restart forgot them
# (17 October, later). Only a run with --root reads it, and it is taken out of the environment as read.
STATE_CARRIED = "IDIOGRAPH_STATE_CARRIED"


def carried_state(environ=None) -> dict:
    """A --root run's list as its restart carried it, `{"recent": []}` when nothing came or what came
    was not a list's JSON. The name is taken out of the environment, so nothing started from this run
    later reads it by chance."""
    environ = os.environ if environ is None else environ
    held = environ.pop(STATE_CARRIED, None)
    try:
        data = json.loads(held) if held else None
    except ValueError:
        data = None
    if not isinstance(data, dict):
        return {"recent": []}
    if not isinstance(data.get("recent"), list):
        data["recent"] = []
    return data


# --------------------------------------------------------------- config

def load_json(path: Path, fallback: dict) -> dict:
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            merged = dict(fallback)
            merged.update(data)
            return merged
        except (ValueError, OSError):
            pass
    return dict(fallback)


def save_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def saved_config() -> dict:
    """config.json as it sits on disk, with nothing merged into it."""
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (ValueError, OSError):
            pass
    return {}


def _json_members(text: str) -> tuple[dict, int, int] | None:
    """The top-level keys of a JSON object's text, each with where its value starts and ends, and where
    the object opens and closes. None for text that is not one object."""
    decoder = json.JSONDecoder()
    space = re.compile(r"\s*")
    i = space.match(text, 0).end()
    if i >= len(text) or text[i] != "{":
        return None
    opened = i
    i = space.match(text, i + 1).end()
    members: dict[str, tuple[int, int, int]] = {}
    if i < len(text) and text[i] == "}":
        return members, opened, i
    while i < len(text) and text[i] == '"':
        key_at = i
        key, i = json.decoder.scanstring(text, i + 1)
        i = space.match(text, i).end()
        if i >= len(text) or text[i] != ":":
            return None
        start = space.match(text, i + 1).end()
        _, end = decoder.raw_decode(text, start)
        members[key] = (key_at, start, end)
        i = space.match(text, end).end()
        if i < len(text) and text[i] == ",":
            i = space.match(text, i + 1).end()
            continue
        if i < len(text) and text[i] == "}":
            return members, opened, i
        return None
    return None


def config_text_with(text: str, changes: dict) -> str | None:
    """The settings file's text with only `changes` written into it: a key it holds with another value
    gets the new value in its place, a key it lacks goes in after the last, and every other byte stays
    as it was. None when the text is not one JSON object, so the caller writes the file afresh."""
    try:
        held = json.loads(text)
        found = _json_members(text) if isinstance(held, dict) else None
    except ValueError:
        return None
    if found is None:
        return None
    members, opened, closed = found
    nl = "\r\n" if "\r\n" in text else "\n"

    def indent_of(key_at: int) -> str | None:
        # the spaces before a key on its own line, or None for a key with other text before it
        line = text.rfind("\n", 0, key_at) + 1
        lead = text[line:key_at]
        return lead if not lead.strip() else None

    def dumped(value, indent: str | None) -> str:
        if indent is None:
            return json.dumps(value, ensure_ascii=False)
        return json.dumps(value, indent=2, ensure_ascii=False).replace("\n", nl + indent)

    edits: list[tuple[int, int, str]] = []
    added: list[tuple[str, object]] = []
    for key, value in changes.items():
        if key in held and held[key] == value:
            continue
        if key in members:
            key_at, start, end = members[key]
            edits.append((start, end, dumped(value, indent_of(key_at))))
        else:
            added.append((key, value))
    if added:
        if members:
            key_at, _, end = max(members.values(), key=lambda m: m[2])
            indent = indent_of(key_at)
            lead = ", " if indent is None else "," + nl + indent
            part = "".join(lead + json.dumps(k, ensure_ascii=False) + ": " + dumped(v, indent) for k, v in added)
            edits.append((end, end, part))
        else:
            part = ("," + nl).join("  " + json.dumps(k, ensure_ascii=False) + ": " + dumped(v, "  ")
                                   for k, v in added)
            edits.append((opened + 1, closed, nl + part + nl))
    out = text
    for start, end, part in sorted(edits, reverse=True):
        out = out[:start] + part + out[end:]
    try:
        if json.loads(out) != {**held, **changes}:
            return None
    except ValueError:
        return None
    return out


def write_config_keys(changes: dict, path: Path | None = None) -> bool:
    """Write only these settings into the settings file, the rest of it left byte for byte as it was,
    and nothing at all when the file already holds them. A file that is not one JSON object, or none,
    is written afresh with them. Answers whether the file was written."""
    path = Path(path or CONFIG_PATH)
    try:
        # read as bytes, so a file with Windows line ends keeps them
        text = path.read_bytes().decode("utf-8") if path.exists() else None
    except (OSError, UnicodeDecodeError):
        text = None
    edited = config_text_with(text, changes) if text is not None else None
    if edited is None:
        data = saved_config() if path == Path(CONFIG_PATH) else {}
        if text is not None and all(k in data and data[k] == v for k, v in changes.items()):
            return False
        save_json(path, {**data, **changes})
        return True
    if edited == text:
        return False
    tmp = path.with_suffix(".tmp")
    tmp.write_text(edited, encoding="utf-8", newline="")
    os.replace(tmp, path)
    return True


def merge_config(saved: dict) -> dict:
    """The defaults with the saved settings over them, and the one renamed key carried across.

    The switch was called `haiku` before the suggestions stopped naming a model. A config written
    then keeps its value, because `ai_suggest` takes it whenever the file has no such key.
    """
    cfg = defaults()
    cfg.update(saved)
    if "ai_suggest" not in saved and "haiku" in saved:
        cfg["ai_suggest"] = bool(saved["haiku"])
    # the status bar, General's, on unless the file says otherwise
    cfg["status_bar"] = saved.get("status_bar") is not False
    # each app's own settings as it reads them from the file, of the apps this run serves alone (see `register`):
    # Idiograph's nudges, its Themes screen's limit, its columns and its boards' bars
    for read in hooks(SETTINGS_READ):
        read(cfg, saved)
    cfg["celebration_screens"] = celebrations_of(saved)
    cfg["projects"] = projects_in(saved)
    cfg.pop("root", None)
    return cfg


CHEER_SCREENS = ("statements", "pets", "gets")


def celebrations_of(saved: dict, given=None) -> dict:
    """Celebrations by screen, `{"statements", "pets", "gets"}` each true or false: `given`'s where it
    says, else the file's `celebration_screens`, else for a file from before them all three as its
    `celebrations` says, on with neither."""
    held = saved.get("celebration_screens") if isinstance(saved.get("celebration_screens"), dict) else None
    base = saved.get("celebrations") is not False
    out = {k: (held[k] is not False) if held is not None and k in held else base for k in CHEER_SCREENS}
    if isinstance(given, dict):
        out.update({k: bool(given[k]) for k in CHEER_SCREENS if k in given})
    return out


def projects_in(saved: dict) -> list[dict]:
    """The projects a settings file names, each `{"root": "<folder>"}` as stored. A file from before
    the projects, with `root` alone, reads as one project with that root, and is written in the new
    shape only when Settings saves. An entry with no root is passed over."""
    held = saved.get("projects")
    if isinstance(held, list):
        out = []
        for entry in held:
            root = str((entry or {}).get("root") or "").strip() if isinstance(entry, dict) else ""
            if root:
                out.append({"root": root})
        return out
    root = str(saved.get("root") or "").strip()
    return [{"root": root}] if root else []


def config() -> dict:
    cfg = merge_config(saved_config())
    if ROOT_OVERRIDE:
        # a run of that one project, whatever the file names
        cfg["projects"] = [{"root": ROOT_OVERRIDE}]
    return cfg


def project_roots(cfg: dict | None = None) -> list[Path]:
    """Every project's root folder, resolved on disk, in the order they were added, each once."""
    cfg = config() if cfg is None else cfg
    out: list[Path] = []
    for entry in cfg.get("projects") or []:
        root = configured(entry.get("root")) if isinstance(entry, dict) else None
        if root is not None and all(same_folder(root, r) is False for r in out):
            out.append(root)
    return out


def same_folder(a: Path, b: Path) -> bool:
    try:
        return Path(a).resolve() == Path(b).resolve()
    except OSError:
        return False


def inside(p: Path, root: Path) -> bool:
    """Whether a path is the folder or sits anywhere under it."""
    try:
        Path(p).resolve().relative_to(Path(root).resolve())
    except (ValueError, OSError):
        return False
    return True


def project_of(p: Path, cfg: dict | None = None) -> Path | None:
    """The project a path belongs to: the demo's folder for anything inside the demo, the thematic analysis
    demo's for anything inside that, else the project whose root holds it, the deepest of two should a
    hand-edited file nest them, and None for a path under no project's root."""
    if is_demo(p):
        return demo_root_of(p)
    holding = [root for root in project_roots(cfg) if inside(p, root)]
    return max(holding, key=lambda r: len(Path(r).resolve().parts)) if holding else None


def project_named(value: str) -> Path:
    """The project a request names by its id, refused as outside every root when no project has it."""
    text = str(value or "").strip()
    if text == "demo":
        return DEMO_DIR
    if text == DEMO_TA_ID:
        return demo_ta_dir()
    if text:
        asked = configured(text)
        for root in project_roots():
            if same_folder(asked, root):
                return root
    raise OutsideRoot(i18n.t("errors.folder_project_s_root"))


def state() -> dict:
    if STATE_MEMORY is not None:
        return json.loads(json.dumps(STATE_MEMORY))
    return load_json(STATE_PATH, {"recent": []})


# one writer of the state file at a time, as the files this process wrote are kept in it after every save
STATE_LOCK = threading.RLock()


def save_state(data: dict) -> None:
    global STATE_MEMORY
    with STATE_LOCK:
        if STATE_MEMORY is not None:
            STATE_MEMORY = json.loads(json.dumps(data))
            return
        save_json(STATE_PATH, data)


def display_case(name: str) -> str:
    """A case folder's name as the page shows it: `P<n> - Pseudonym-Secondname` becomes `P<n> - Pseudonym`.

    Anything else, the demo's `Juno`, a folder with no second name, one whose second part is not a
    capitalised word, comes back as it is.
    """
    m = CASE_FOLDER.match(str(name or ""))
    return m.group(1) if m else str(name or "")


def display_path(value: str) -> str:
    """A path for a line on the screen, every case folder in it shown by its pseudonym alone. A
    Windows path's folders are split at its backslashes as a Mac's are at its slashes, each kept."""
    return "".join(part if part in ("/", "\\") else display_case(part) for part in re.split(r"([/\\])", str(value)))


def abs_path(value: str) -> Path:
    """A path setting or a typed path, absolute or from `REPO_ROOT`. A path in quotes, as Windows
    copies one, is taken without them."""
    text, bare = str(value), str(value).strip()
    if len(bare) > 1 and bare[0] == bare[-1] and bare[0] in "\"'":
        text = bare[1:-1]
    p = Path(text).expanduser()
    return p if p.is_absolute() else (REPO_ROOT / p)


def resolve_path(value: str) -> Path:
    """A configured path, with any `*` resolved against the disk.

    Configured paths are written as globs on the pseudonym (`P<n> - Pseudonym*`) so no case folder name
    is ever stored in the repo. An unmatched glob comes back as written, and the caller finds the
    file missing rather than crashing.
    """
    target = abs_path(value)
    if "*" not in str(target) and "?" not in str(target):
        return target
    anchor = Path(target.anchor)
    matches = sorted(anchor.glob(str(target.relative_to(anchor))))
    return matches[0] if matches else target


def rel_path(p: Path) -> str:
    """A path as the API's answers carry it. One under `REPO_ROOT` is given from there with forward
    slashes on every system, so an agent gets the same answer on Windows as on a Mac (20 October).
    Any other is kept as the system writes it, a Windows path with its drive and backslashes, since
    that is how a project's root is stored in config.json and shown in Settings, and an agent or the
    page that sends it back names the same folder either way."""
    try:
        return Path(p).resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(p)


def is_demo(p: Path) -> bool:
    """A path inside the bundled demo folder, so any of its cases, Juno's, Rowan's or Mabel's, the thematic analysis
    demo's among them."""
    try:
        Path(p).resolve().relative_to(DEMO_DIR.resolve())
    except (ValueError, OSError):
        return False
    return True


# The thematic analysis demo (demos, 3 November 2026, Adam's word that evening): the same three invented
# participants coded in a thematic analysis project, in a folder of its own inside the demo's, so it ships, seeds
# and is guarded as the demo is. The page and the command line name it by its id, `demo-ta`, and `ta` names it to
# `--demo`, the IPA demo staying the one `--demo` alone names.
DEMO_TA_ID = "demo-ta"
DEMO_TA_FOLDER = "ta"


def demo_ta_dir() -> Path:
    """The thematic analysis demo's folder, inside the demo's wherever that is."""
    return DEMO_DIR / DEMO_TA_FOLDER


def demo_dir_of(which) -> Path:
    """The demo a word names: `ta` the thematic analysis demo, anything else that names one the IPA demo."""
    return demo_ta_dir() if str(which or "").strip().lower() in (DEMO_TA_FOLDER, DEMO_TA_ID) else DEMO_DIR


def demo_root_of(p: Path) -> Path | None:
    """The demo a path is inside, the thematic analysis demo's folder or the IPA demo's, or None."""
    if not is_demo(p):
        return None
    return demo_ta_dir() if inside(p, demo_ta_dir()) else DEMO_DIR


def is_demo_root(root) -> bool:
    """Whether a folder is one of the two demos' own, which are fixed."""
    return root is not None and (same_folder(root, DEMO_DIR) or same_folder(root, demo_ta_dir()))


def within_root(p: Path) -> bool:
    """A path some project's root contains, or one inside the bundled demo folder.

    Anything else is refused, whoever asked. The demo is the one folder outside every root that is
    allowed, and only that folder: its parent, the rest of the tool and every sibling are refused
    the same way a live case is refused to a server started with `--root` at a scratch folder.
    With no project yet the demo is the one folder there is, never the folder the app sits in.
    """
    return project_of(p) is not None


class OutsideRoot(Exception):
    """A path no project's root contains."""


# Open project folder, under Distil's cards on the home screen: the
# Mac's own folder dialog, run from the server by osascript. The dialog answers the folder's POSIX
# path, or nothing for Cancel. Off a Mac the folder is typed. AppKit's open panel through osascript's
# JavaScript comes up in about a second, where AppleScript's choose folder takes three or four, so
# the panel goes first and choose folder stands in when the panel's script fails.
PANEL_SCRIPT = ('ObjC.import("AppKit")', "function run(argv) {",
                "  $.NSApplication.sharedApplication.activateIgnoringOtherApps(true)",
                "  var panel = $.NSOpenPanel.openPanel",
                "  panel.canChooseDirectories = true", "  panel.canChooseFiles = false",
                "  panel.allowsMultipleSelection = false", "  panel.canCreateDirectories = true",
                "  panel.message = argv[0]",
                '  return panel.runModal == 1 ? ObjC.unwrap(panel.URL.path) : ""', "}")
PICK_SCRIPT = ("on run argv", "activate", "try",
               "set chosen to choose folder with prompt (item 1 of argv)",
               "on error number -128", 'return ""', "end try",
               "return POSIX path of chosen", "end run")
# the same two for a file, a Markdown or Word document for Sift's reference check (14 October)
FILE_PANEL_SCRIPT = tuple(line.replace("canChooseDirectories = true", "canChooseDirectories = false")
                          .replace("canChooseFiles = false", "canChooseFiles = true")
                          .replace("canCreateDirectories = true", "canCreateDirectories = false") for line in PANEL_SCRIPT)
FILE_PICK_SCRIPT = tuple(line.replace("choose folder", "choose file") for line in PICK_SCRIPT)


PICKING = threading.Lock()


def pick_folder(prompt: str = i18n.t("errors.choose_folder_holds_participants"), files: bool = False) -> Path | None:
    """The folder chosen in the Mac's folder dialog, or with `files` a file, or None when it is
    cancelled or fails. The dialog takes a second or so to come up, so a second ask while one is open
    opens no second dialog and answers None, as a Cancel does."""
    if not PICKING.acquire(blocking=False):
        return None
    try:
        for script in ((FILE_PANEL_SCRIPT, FILE_PICK_SCRIPT) if files else (PANEL_SCRIPT, PICK_SCRIPT)):
            args = ["osascript"] + (["-l", "JavaScript"] if script in (PANEL_SCRIPT, FILE_PANEL_SCRIPT) else [])
            for line in script:
                args += ["-e", line]
            run = subprocess.run(args + [prompt], capture_output=True, text=True, encoding="utf-8", timeout=900)
            if run.returncode == 0:
                break
    except (OSError, subprocess.TimeoutExpired):
        return None
    finally:
        PICKING.release()
    chosen = run.stdout.strip()
    return Path(chosen) if run.returncode == 0 and chosen else None


# a name here so the suite can stand in for the dialog
PICK_FOLDER = pick_folder


def show_in_folder(folder: Path) -> None:
    """A project's folder shown in the Finder on a Mac, in Explorer on Windows, selected in the folder it sits in,
    or opened by the file manager (xdg-open) on Linux: Show in Finder on a Sift or Trace project's menu
    (barsD, 6 November 2026), as Idiograph's card has it."""
    if PLATFORM == "darwin":
        subprocess.run(["open", "-R", str(folder)], check=False, timeout=15,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif PLATFORM.startswith("linux"):
        try:
            subprocess.run(["xdg-open", str(folder)], check=False, timeout=15,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            pass
    else:
        subprocess.run(f'explorer /select,"{folder}"', check=False, timeout=15,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# a name here so the suite can stand in for the Finder
SHOW_IN_FOLDER = show_in_folder


def reveal_folder(folder: Path) -> dict:
    """Show in Finder for a project the list holds: refused in one line on a machine that is not a Mac, Windows
    or Linux and for a folder no longer there, writing nothing either way."""
    if PLATFORM not in ("darwin", "win32") and not PLATFORM.startswith("linux"):
        raise WorkbookError(i18n.t("errors.show_folder_mac_windows_only"))
    if not Path(folder).is_dir():
        raise WorkbookError(i18n.t("errors.folder"))
    SHOW_IN_FOLDER(Path(folder))
    return {"revealed": True}



# ---------------------------------------------------------- an app's project folder

# What Sift's and Trace's projects share, which stays the family's as their routes move to their own
# folders (the family codebase's third build, 22 October 2026): a folder named in a request, whether one is
# empty, where New project writes, the model's name in words, a Zotero item's link and a file opened in the
# computer's own app for it.
# what a folder's name may not hold, on a Mac, Windows or Linux
NOT_IN_FOLDER = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


def there_folder(value) -> Path:
    """A folder from a request, refused in one line when none is named or it is not there."""
    text = str(value or "").strip()
    if not text:
        raise WorkbookError(i18n.t("errors.name_folder_first"))
    folder = abs_path(text)
    if not folder.is_dir():
        raise WorkbookError(i18n.t("errors.folder"))
    return folder.resolve()


def is_empty(folder: Path) -> bool:
    """Whether a folder holds nothing but hidden files such as the Finder's own."""
    try:
        return not any(not p.name.startswith(".") for p in Path(folder).iterdir())
    except OSError:
        return False


def review_target(place: Path, name: str) -> Path:
    """Where New review writes: the folder given when it is empty, else a new folder inside it named
    for the review, one already there taken only when it is empty."""
    if is_empty(place):
        return place
    leaf = NOT_IN_FOLDER.sub(" ", name)
    leaf = " ".join(leaf.split()).strip(" .")[:80].strip(" .")
    if not leaf:
        raise WorkbookError(i18n.t("errors.folder_cannot_take_name_give"))
    target = place / leaf
    if target.exists() and not (target.is_dir() and is_empty(target)):
        raise WorkbookError(i18n.t("errors.folder_named_already", leaf=leaf))
    return target


def ai_model_words(cfg: dict) -> str:
    """The model the app's AI calls go to, named from the settings alone, the key never looked up: "Opus
    5.5", or a local one's name on this machine."""
    provider = cfg.get("ai_provider") if cfg.get("ai_provider") in ai_mod.PROVIDERS else ai_mod.ANTHROPIC
    if provider == ai_mod.LOCAL:
        local = str(cfg.get("local_model") or "").strip()
        return f"{local} on this machine" if local else "a local model"
    if provider in ai_mod.OPENAI_SHAPED:
        return ai_mod.route_model(ai_route_fields(cfg, provider))
    return ai_mod.model_name(str(cfg.get("model") or "").strip() or ai_mod.MODEL)


# ------------------------------------------------------------------------ Zotero's item link

ZOTERO_ITEM = "zotero://select/{library}/items/{key}"


def zotero_item_link(cfg: dict, key: str) -> str:
    """A Zotero item's link for the Zotero app on this computer, in the library Sift's export goes to,
    or empty with no item: a group's, by the digits of its id, when the settings name the group library and
    give one, as Sift's `sift_zotero.clean_settings` reads them, else his own."""
    key = str(key or "").strip()
    if not re.fullmatch(r"[A-Z0-9]{8}", key):
        return ""
    held = cfg.get("zotero") if isinstance(cfg.get("zotero"), dict) else {}
    group = re.sub(r"\D", "", str(held.get("group_id") or ""))[:12]
    library = f"groups/{group}" if held.get("library") == "group" and group else "library"
    return ZOTERO_ITEM.format(library=library, key=key)


def open_with_default(target: Path) -> None:
    """A file opened in the app the computer opens it with, `open` on a Mac."""
    if PLATFORM == "darwin":
        subprocess.run(["open", str(target)], check=False, timeout=15, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif PLATFORM.startswith("win"):
        os.startfile(str(target))                  # Windows's own call, there alone
    else:
        subprocess.run(["xdg-open", str(target)], check=False, timeout=15, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)


# a name here so the suite can stand in for it
OPEN_FILE = open_with_default


def seed_demo(shipped: Path | None = None, demo: Path | None = None) -> list[Path]:
    """Copy each file of the shipped demo that is missing from the demo the app works on.

    In the Mac app that is the first run's copy into Application Support, and the repair of a
    file taken away since. A file already there is never replaced, so a demo worked on stays as
    it is until Reset demo. From the repo the two are one folder and nothing is copied.
    """
    shipped, demo = shipped or SHIPPED_DEMO, demo or DEMO_DIR
    if Path(shipped).resolve() == Path(demo).resolve() or not Path(shipped).is_dir():
        return []
    import shutil as _shutil
    copied = []
    for source in sorted(Path(shipped).rglob("*")):
        target = Path(demo) / source.relative_to(shipped)
        if source.is_file() and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            _shutil.copyfile(source, target)
            copied.append(target)
    return copied


def first_run(paths: dict | None = None, config_path: Path | None = None) -> list[Path]:
    """Ready the folder the app writes in, before the first request.

    From the repo it is the app's own folder, and nothing moves. From the Mac app it is
    `~/Library/Application Support/Idiograph`: made if it is not there, the settings the bundle
    ships copied in when there are none, which name no root, and Idiograph's demo copied from the
    bundle. Sift and Trace have no use for its participants, so their folders never take it (23
    October). Answers the files copied.
    """
    paths = paths or PATHS
    if paths["data"] == HERE:
        return []
    import shutil as _shutil
    paths["data"].mkdir(parents=True, exist_ok=True)
    config_path = Path(config_path or paths["config"])
    copied = []
    shipped = paths["shipped_demo"].parent / "config.json"
    if not config_path.exists() and shipped.is_file():
        _shutil.copyfile(shipped, config_path)
        copied.append(config_path)
    if app_identity.check(paths.get("app") or app_identity.DEFAULT) != app_identity.DEFAULT:
        return copied
    return copied + seed_demo(paths["shipped_demo"], paths["demo"])


def use_app(app: str | None) -> str:
    """This run as one of the family's three apps, `--app` on the server, the command line and the
    MCP server (see `app_identity`): its folders, its settings and recent-list files, its key file,
    its demo, its version and its What's new. Idiograph's, the default, leaves every path as it was.
    Answers the app's name."""
    global APP, IDENTITY, VERSION, PATHS, REPO_ROOT, CONFIG_PATH, STATE_PATH, ENV_PATH
    global DEMO_DIR, SHIPPED_DEMO, DEMO_CASE, DEMO_WORKBOOK, DEMO_PROJECT, SAMPLE_CSV, DEMO_EXAMPLES, WHATS_NEW_FILE
    name = app_identity.check(app)
    if name == APP:
        return name
    APP, IDENTITY, VERSION = name, app_identity.identity(name), app_identity.version(name)
    PATHS = app_paths(app=name)
    REPO_ROOT, CONFIG_PATH, STATE_PATH, ENV_PATH = PATHS["base"], PATHS["config"], PATHS["state"], PATHS["env"]
    for mod in KEY_FILES:
        mod.ENV_PATH = ENV_PATH
    DEMO_DIR, SHIPPED_DEMO = PATHS["demo"], PATHS["shipped_demo"]
    DEMO_CASE = DEMO_DIR / "Juno"
    DEMO_WORKBOOK = DEMO_CASE / "Juno - EN & ES.xlsx"
    DEMO_PROJECT = DEMO_DIR / PROJECT_FILE
    SAMPLE_CSV = DEMO_DIR / "source" / "Juno - interview.csv"
    DEMO_EXAMPLES = DEMO_DIR / "pristine" / DEMO_WORKBOOK.name
    WHATS_NEW_FILE = IDENTITY["whats_new"]
    return name


APP_GLOBALS = ("APP", "IDENTITY", "VERSION", "PATHS", "REPO_ROOT", "CONFIG_PATH", "STATE_PATH", "ENV_PATH",
               "DEMO_DIR", "SHIPPED_DEMO", "DEMO_CASE", "DEMO_WORKBOOK", "DEMO_PROJECT", "SAMPLE_CSV",
               "DEMO_EXAMPLES", "WHATS_NEW_FILE")


def app_held() -> dict:
    """What `use_app` sets, as it stands, for `app_back` to put back after a run of another app in
    this process, the command line's `--app` among them."""
    return {**{name: globals()[name] for name in APP_GLOBALS}, "key_files": [(mod, mod.ENV_PATH) for mod in KEY_FILES]}


def app_back(held: dict) -> None:
    globals().update({name: held[name] for name in APP_GLOBALS})
    for mod, path in held["key_files"]:
        mod.ENV_PATH = path


def state_beside(config_path: Path, app: str | None = None) -> Path:
    """The recent list of a run given its own settings file (`--config`, as a trial or smoke server is):
    beside that file, under the app's own name, `state.json` for Idiograph, `state.sift.json` for Sift
    and `state.trace.json` for Trace, so a run without `--root` never writes the list in daily use, and
    Sift's never writes Idiograph's beside it, which its first start reads (21 October)."""
    return Path(config_path).parent / app_identity.file_names(app or APP)["state"]


def first_start_sources(config_path: Path | None = None, paths: dict | None = None) -> dict:
    """Idiograph's files a first start of Sift or Trace copies from: Idiograph's own settings, recent
    list and key file. A run given its own settings file (`--config`, as a trial or smoke server is)
    takes Idiograph's from beside that file, `config.json` and `state.json` there, never the ones in
    daily use."""
    paths = paths or PATHS
    own = Path(config_path or CONFIG_PATH)
    idio = app_paths(bundle=FROZEN, app=app_identity.DEFAULT)
    if own.resolve() != Path(paths["config"]).resolve():
        return {"config": own.parent / "config.json", "state": own.parent / "state.json",
                "env": None, "base": idio["base"]}
    return {"config": idio["config"], "state": idio["state"], "env": idio["env"], "base": idio["base"]}


def first_start_copy(app: str | None = None, config_path: Path | None = None, sources: dict | None = None,
                     own_env: Path | None = None, own_base: Path | None = None) -> bool:
    """The first start of Sift or Trace: what it shares with Idiograph copied from Idiograph's files
    into its own, once (see `app_identity.first_start_plan`), and the key file where there is one,
    which only a machine with no keychain keeps, also once. Idiograph's files are only read. Answers
    whether a copy was made."""
    name = app_identity.check(app or APP)
    config_path = Path(config_path or CONFIG_PATH)
    sources = sources or first_start_sources(config_path)
    own_config = load_json(config_path, {}) if config_path.exists() else {}
    from_config = load_json(Path(sources["config"]), {}) if sources.get("config") else {}
    from_state = load_json(Path(sources["state"]), {}) if sources.get("state") else {}
    plan = app_identity.first_start_plan(name, own_config, from_config, state(), from_state,
                                         from_base=sources.get("base"), own_base=own_base or REPO_ROOT)
    if plan is None:
        return False
    new_config, new_state = plan
    env_from, env_to = sources.get("env"), Path(own_env or ENV_PATH)
    if env_from and Path(env_from).is_file() and not env_to.exists() \
            and Path(env_from).resolve() != env_to.resolve():
        env_to.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(env_from, env_to)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    save_state(new_state)
    # only what the copy adds or changes, the marker always among it, the rest of the file as it was
    write_config_keys({k: v for k, v in new_config.items() if k not in own_config or own_config[k] != v},
                      config_path)
    return True


def shipped_config(app: str | None = None) -> dict:
    """The settings an app's build ships, `app`'s, this run's by default, which the build writes into the
    bundle: the app's defaults with no project, so the case list asks for a folder."""
    return dict(defaults(app), projects=[])


# the app each search scope belongs to, Everything every app's, holding its own projects alone
SEARCH_SCOPE_APP = {"case": "idiograph", "project": "idiograph", "sift": "sift", "trace": "trace", "all": None}
# the part of a search's answer each app's kinds stand under (see `app_search.PARTS`)
SEARCH_PART_APP = {"sift": "sift", "distil": "idiograph", "trace": "trace"}


def own_kinds(found: dict, served) -> dict:
    """Everything's answer with the parts and counts of the apps this run answers for alone, and as it
    was when it answers for all three."""
    if all(app in served for app in SEARCH_PART_APP.values()):
        return found
    parts = [p for p in found.get("parts", []) if SEARCH_PART_APP.get(p[0]) in served]
    kinds = {k for _, ks in parts for k in ks}
    return dict(found, parts=parts, counts={k: n for k, n in found.get("counts", {}).items() if k in kinds})


def api_search(body: dict) -> dict:
    """Search across the app (17 and 18 October, see `app_search`): `q`, the words typed, over `scope`:
    `case`, the workbook `path` and its themes file, `project`, every case of the project `path` belongs to
    or `root` names by its id, its GETs, its cases' names and its research question, `sift`, the Sift
    project of `folder`, a review's or a screening's, its screening's records and its plan, `trace`, the
    Trace project `folder`, its manuscripts' claims, references and notes, or `all`, every project the home
    screen lists, Sift's, Distil's with the demo last and Trace's. `kinds`, `cases`, `sheets` and
    `projects` are the filters ticked, and `whole_word` and `match_case` the two ticks beside the field, Whole word
    on unless it is false and Match case off unless it is true (searchmods, 6 November 2026). Read-only: the files are read once and held in memory against their
    time and size, and nothing is written, the recent list and the lists of projects included."""
    scope = str(body.get("scope") or "")
    if scope not in app_search.SCOPES:
        raise WorkbookError(app_search.NO_SCOPE)
    # each app searches its own kinds: another app's scope answers as its route would (see `not_here`),
    # and Everything holds only the projects of the apps this run answers for, its own since the cutover
    served = apps_served()
    # the page names its own app, `app`, and Everything then holds that app's projects alone
    if body.get("app") in served:
        served = (body["app"],)
    owner = SEARCH_SCOPE_APP.get(scope)
    if owner is not None and owner not in served:
        them = app_identity.APPS[owner]
        return {"error": i18n.t("errors.other_apps", name=them['name'], name2=IDENTITY['name']), "app": owner, "port": them["port"],
                "status": 404}
    listed = lambda key: [str(v) for v in body.get(key) or [] if isinstance(v, str)] if isinstance(body.get(key), list) else []
    q = body.get("q") or ""
    if scope in SEARCH_SCOPES:
        return SEARCH_SCOPES[scope](body, listed("kinds"))
    # Everything: each served app's projects under its part, Idiograph's Distil projects with the demo last,
    # Sift's and Trace's, as each app lists them (see `register`)
    parts = {part: SEARCH_ROWS[app]() for part, app in SEARCH_PART_APP.items() if app in served and app in SEARCH_ROWS}
    whole, match_case = app_search.options(body)
    found = app_search.search_all(q, kinds=listed("kinds"), projects=listed("projects"), whole=whole,
                                  match_case=match_case, **parts)
    return own_kinds(found, served)


def ai_on(cfg: dict, feature: str) -> bool:
    """Whether one AI feature is on: AI features on in Settings and that feature's own switch not turned
    off (see `app_identity.ai_feature_on`)."""
    return app_identity.ai_feature_on(cfg, feature)


def ai_state(cfg: dict, feature: str = "pets") -> dict:
    """Whether the switch in Settings is on, with the feature's own, `pets` or `gets`, the model the Themes screen's help asks and his limit
    on the themes a proposal makes, for the page to draw its controls by. The model is the PETs
    screen's own when one is set. Read from the settings alone: the key is never looked up. The PETs
    screen's model and the limit are Idiograph's, each as its registration gives it (`AI_CHOICE`, `AI_MORE`)."""
    own = next((choice(cfg) for choice in hooks(AI_CHOICE)), {})
    provider = own.get("provider") or cfg.get("ai_provider")
    provider = provider if provider in ai_mod.PROVIDERS else ai_mod.ANTHROPIC
    if provider == ai_mod.LOCAL:
        local = str(own.get("local_model") or cfg.get("local_model") or "").strip()
        name = f"{local} on this machine" if local else "a local model"
    elif provider in ai_mod.OPENAI_SHAPED:
        name = ai_mod.route_model(ai_route_fields(cfg, provider, own.get("model")))
    else:
        name = ai_mod.model_name(own.get("model") or cfg.get("model") or ai_mod.MODEL)
    out = {"on": ai_on(cfg, feature), "provider": provider, "model_name": name}
    for more in hooks(AI_MORE):
        out.update(more(cfg))
    return out


# Show in Finder: `open -R` on the file, on a Mac alone. A name here so the suite can stand in for it.
PLATFORM = sys.platform


def configured(value) -> Path | None:
    """A path setting resolved on disk, or None when the setting is empty."""
    text = str(value or "").strip()
    return resolve_path(text) if text else None


# The settings an app keeps of its own, which another app's /api/settings leaves as its file has them
# (the split's second build, 20 October 2026), each app's from its registration (see `register`), Sift's since
# the sixth build (23 October 2026). A key in none of these is General's, which every app saves: the AI
# settings, Celebrations and its Sound, the status bar and the closing tick.
SETTINGS_BY_APP: dict = {}


# Appearance's three, as the page names them
APPEARANCES = ("light", "dark", "system")


def is_day(value) -> bool:
    """Whether `value` is a day written YYYY-MM-DD, as `support_asked` holds one."""
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def settings_for_app(body: dict, app: str | None = None) -> dict:
    """A settings save's body with only General's keys and the keys of the apps this run answers for,
    so Sift's settings never take Idiograph's nor Idiograph's Sift's."""
    served = apps_served(app)
    others = {key for owner, keys in SETTINGS_BY_APP.items() if owner not in served for key in keys}
    return {k: v for k, v in body.items() if k not in others}


def api_settings(body: dict) -> dict:
    """Save the settings. The API key is never one of them: it goes to `/api/key` and the keychain.
    An app saves General's keys and its own (see `settings_for_app`). `op` of `read` saves nothing and
    answers the settings as they stand, which the page reads its appearance from at boot."""
    if isinstance(body, dict) and body.get("op") == "read":
        cfg = config()
        return {"config": cfg, "ai": ai_state(cfg)}
    body = settings_for_app(body if isinstance(body, dict) else {})
    # Appearance sent alone, as its rows under General send it: only that key goes into the file, and a
    # choice the file already holds writes nothing, so the defaults never land in a file that lacked them
    if set(body) == {"appearance"}:
        if body["appearance"] in APPEARANCES:
            write_config_keys({"appearance": body["appearance"]})
        cfg = config()
        return {"config": cfg, "ai": ai_state(cfg)}
    # and the language sent alone, as the Language row under General sends it, the same way (i18nus): a tag, or
    # "" for the computer's own, only that key written, and one that is no language refused
    if set(body) == {"language"}:
        tag = body["language"].strip() if isinstance(body["language"], str) else None
        if tag is not None and (not tag or i18n.normal(tag) == tag):
            write_config_keys({"language": tag})
        cfg = config()
        return {"config": cfg, "ai": ai_state(cfg)}
    # and the formats sent alone, as the rows under Language and formats send them (fmtcore, 28 October 2026),
    # each key sent taking its place in the settings' `formats`, the rest kept, "" for the computer's own, and
    # anything not one of the choices refused by name, so an agent setting them hears why
    if set(body) == {"formats"}:
        refused = i18n.format_refused(body["formats"])
        if refused:
            raise WorkbookError(i18n.t("errors.formats_choice", what=refused))
        held = i18n.formats_of(saved_config().get("formats"))
        write_config_keys({"formats": {**held, **body["formats"]}})
        cfg = config()
        return {"config": cfg, "ai": ai_state(cfg)}
    # and the day the one-time line about supporting the app first showed (supportcard, 28 October 2026), sent alone
    # by the note after the first Word export of PETs as the line shows: a day, YYYY-MM-DD, only that key written,
    # the first day kept, and anything that is not a day passed over. Until then the settings have no such key
    if set(body) == {"support_asked"}:
        if is_day(body["support_asked"]) and not saved_config().get("support_asked"):
            write_config_keys({"support_asked": body["support_asked"]})
        cfg = config()
        return {"config": cfg, "ai": ai_state(cfg)}
    cfg = merge_config(saved_config())            # saved settings, never the --root override
    switch_was = cfg.get(SWITCH_SETTING)
    for name in ("ai_suggest", "local_url"):
        if name in body:
            cfg[name] = body[name]
    if body.get("ai_provider") in ai_mod.PROVIDERS:
        cfg["ai_provider"] = body["ai_provider"]
    # the OpenAI-style providers' own fields, as text, and the model each is asked by provider
    for name in ("ai_address", "ai_deployment", "ai_api_version", "other_model", "lmstudio_url"):
        if name in body:
            cfg[name] = str(body[name] or "").strip()
    if isinstance(body.get("ai_models"), dict):
        cfg["ai_models"] = {**(cfg.get("ai_models") if isinstance(cfg.get("ai_models"), dict) else {}),
                            **{p: str(m or "").strip() for p, m in body["ai_models"].items()
                               if p in ai_mod.OPENAI_SHAPED}}
    # the page sends the plain id, and a dated id already stored for the same model stays as it is
    chosen = str(body.get("model") or "").strip()
    if chosen and ai_mod.plain_model(cfg.get("model")) != chosen:
        cfg["model"] = chosen
    if "local_model" in body:
        cfg["local_model"] = str(body.get("local_model") or "").strip()
    # a page from before the rename sends only the old name, and it still lands. The old key is
    # never written back: merge_config still reads it from a config that carries it, and a
    # save drops it from the file
    if "ai_suggest" not in body and "haiku" in body:
        cfg["ai_suggest"] = bool(body["haiku"])
    cfg.pop("haiku", None)
    # the two ticks under Celebrations, saved as they stand. A page from before sends neither
    for name in ("celebrations", "sound", "status_bar"):
        if name in body:
            cfg[name] = bool(body[name])
    # Celebrations by screen, each as sent and the rest as the file has them, with `celebrations` true
    # while any is on, and the one switch of a page from before, or Sift's or Trace's, sets all three
    if isinstance(body.get("celebration_screens"), dict):
        cfg["celebration_screens"] = celebrations_of(cfg, body["celebration_screens"])
        cfg["celebrations"] = any(cfg["celebration_screens"].values())
    elif "celebrations" in body:
        cfg["celebration_screens"] = {k: cfg["celebrations"] for k in CHEER_SCREENS}
    # each app's own settings as its screens and its part of Settings send them, of the apps this run serves
    # alone (see `register`): Idiograph's interviewer, rounds, prompt, nudges, columns, exports and boards' bars
    for save in hooks(SETTINGS_SAVE):
        save(cfg, body)
    # an app's own settings as its part of Settings holds them, each cleaned by the app, of the apps this run
    # serves alone (see `register`): Sift's databases in their order and its Zotero library, never a key. A
    # page from before one sends none, and the file keeps what it had
    for owner, cleaners in SETTINGS_CLEAN.items():
        for key, (kind, clean) in cleaners.items():
            if owner in apps_served() and isinstance(body.get(key), kind):
                cfg[key] = clean(body[key])
    # Appearance, Light, Dark or Same as this computer, kept in the app's own settings as well as the
    # page's browser storage, so Sift's and Trace's first start copy it (the split's third build)
    if body.get("appearance") in APPEARANCES:
        cfg["appearance"] = body["appearance"]
    # the AI features turned off under AI features in Settings, each app's own (see `ai_on`). A save
    # names only this app's, so another app's turned off stay as the file has them
    if isinstance(body.get(app_identity.AI_OFF_KEY), list):
        mine = app_identity.AI_FEATURES[APP]
        kept = [f for f in app_identity.clean_ai_off(cfg.get(app_identity.AI_OFF_KEY)) if f not in mine]
        sent = [f for f in body[app_identity.AI_OFF_KEY] if f in mine]
        cfg[app_identity.AI_OFF_KEY] = app_identity.clean_ai_off(kept + sent)
    # the language the page and the server's lines are in (i18ncore, 28 October 2026): a tag such as `es` or
    # `en-US`, or "" for the computer's own, sent by the Language row under General the moment a row is ticked
    # (i18nus)
    if "language" in body and isinstance(body["language"], str) and (
            not body["language"].strip() or i18n.normal(body["language"]) == body["language"].strip()):
        cfg["language"] = body["language"].strip()
    # and the formats beside it, a whole save keeping each key sent that is one of its choices
    if isinstance(body.get("formats"), dict) and not i18n.format_refused(body["formats"]):
        cfg["formats"] = {**i18n.formats_of(cfg.get("formats")), **body["formats"]}
    # the tick at the end of General, read afresh by `idle_quit` at each look, so it holds at once
    if "quit_when_closed" in body:
        cfg["quit_when_closed"] = bool(body["quit_when_closed"])
    save_json(CONFIG_PATH, cfg)
    # Dangerously skip permissions turned on or off, a line in its record (see `record_switch`)
    if switch_was is not None and SWITCH_SETTING in cfg and (cfg[SWITCH_SETTING] is True) != (switch_was is True):
        record_switch(cfg[SWITCH_SETTING] is True)
    # `ai` is what the Themes screen's bar draws by, so a save from over it shows there at once
    return {"config": cfg, "ai": ai_state(cfg)}


def ai_route_fields(cfg: dict, provider: str, model: str | None = None, body: dict | None = None) -> dict:
    """What an OpenAI-style provider's route carries besides its key: the model it is asked, its address
    and its deployment, from the body (the bench, a card) first and the settings after. Another service's
    model is `other_model`, the others' is `ai_models` by provider, then the preset's own."""
    body = body or {}
    held = cfg.get("ai_models") if isinstance(cfg.get("ai_models"), dict) else {}
    chosen = str(model or "").strip()
    if not chosen:
        chosen = str((cfg.get("other_model") if provider == ai_mod.OTHER else held.get(provider)) or "").strip()
    # LM Studio's own address, `lmstudio_url`, apart from Azure's and Another service's `ai_address`
    held_at = "lmstudio_url" if provider == ai_mod.LMSTUDIO else "ai_address"
    return {"provider": provider, "model": chosen or ai_mod.PRESETS[provider]["model"],
            "address": str(body.get(held_at) or cfg.get(held_at) or "").strip(),
            "deployment": str(body.get("ai_deployment") or cfg.get("ai_deployment") or "").strip(),
            "api_version": str(cfg.get("ai_api_version") or "").strip() or ai_mod.AZURE_API_VERSION}


def provider_key(provider: str, address: str | None = None) -> str | None:
    """The key of an OpenAI-style provider, from its own keychain item (the smoke run's held in memory),
    never a `.env`. A provider that takes none has none."""
    if not ai_mod.PRESETS[provider].get("service"):
        return None
    run, _env = key_place()
    return ai_mod.find_key(None, runner=run, service=ai_mod.key_service(provider, address))


def ai_route(cfg: dict, body: dict | None = None) -> dict:
    """The provider, the model, the key and the prompt a suggestion goes out with.

    The bench in settings may carry its own provider, model and prompt, so a choice can be tried
    before it is saved. The key is looked up only for a provider that takes one, from that provider's own
    keychain item: nothing about it applies to Local or LM Studio.
    """
    body = body or {}
    provider = body.get("provider") if body.get("provider") in ai_mod.PROVIDERS else cfg.get("ai_provider")
    if provider not in ai_mod.PROVIDERS:
        provider = ai_mod.ANTHROPIC
    extra = {}
    if provider == ai_mod.LOCAL:
        model = str(body.get("local_model") or cfg.get("local_model") or "").strip()
        key = None
    elif provider in ai_mod.OPENAI_SHAPED:
        extra = ai_route_fields(cfg, provider, body.get("model") or body.get("local_model"), body)
        model = extra.pop("model")
        key = provider_key(provider, extra["address"])
    else:
        model = str(body.get("model") or cfg.get("model") or "").strip() or ai_mod.MODEL
        key = ai_mod.find_key(ENV_PATH)
    template = body.get("ai_prompt") if str(body.get("ai_prompt") or "").strip() else cfg.get("ai_prompt")
    # the project's question fills `{research_question}`: the bench's as it stands in the panel, saved or
    # not, else as the app whose project it is reads it (see `register`), Idiograph's the demo's own for the
    # demo and the root's for any other case
    if "research_question" in body:
        question = str(body.get("research_question") or "")
    else:
        question = next((asked(body) for asked in hooks(QUESTION)), "")
    return {"provider": provider, "model": model, "key": key, "template": template,
            "local_url": cfg.get("local_url"), "research_question": question, **extra}


def key_place() -> tuple:
    """The `security` runner and the `.env` the Anthropic key goes through: in a smoke run, while
    `IDIOGRAPH_SEARCH_STUB` names a loopback stub, Sift's keychain held in memory and no file, so the
    run never reads or writes the login keychain, else the login keychain and `ENV_PATH`."""
    if ai_mod.stub_base():
        return ai_mod.STUB_KEYCHAIN, None
    return None, ENV_PATH


def ai_transport():
    """How the model list and Check key reach Anthropic: straight there, or in a smoke run to the loopback
    stub, Anthropic's host replaced by the stub's address and `/anthropic`."""
    base = ai_mod.stub_base()
    if not base:
        return None

    def send(method, url, headers, payload, timeout):
        return ai_mod.http_call(method, url.replace("https://api.anthropic.com", base + "/anthropic", 1),
                                headers, payload, timeout)
    return send


def anthropic_list(fresh: bool = False) -> dict:
    """The Anthropic models for the dropdown, live when a key is stored and held for an hour."""
    held = _model_cache.get("answer")
    if held and not fresh and time.monotonic() - _model_cache["at"] < MODEL_CACHE_SECONDS:
        return held
    run, env = key_place()
    answer = ai_mod.anthropic_models(ai_mod.find_key(env, runner=run), transport=ai_transport())
    if answer.get("source") == "live":
        _model_cache.update(at=time.monotonic(), answer=answer)
    return answer


def forget_models() -> None:
    _model_cache.update(at=0.0, answer=None)


def api_models(body: dict) -> dict:
    """The model lists, the local status, and what is chosen now. Never the key. While an OpenAI-style
    provider is the chosen one (a `provider` in the body trying one before it is saved, else the settings')
    only its list is asked, as `openai`, and with AI features off no list is asked at all."""
    cfg = config()
    provider = body.get("provider") if body.get("provider") in ai_mod.PROVIDERS else cfg.get("ai_provider")
    provider = provider if provider in ai_mod.PROVIDERS else ai_mod.ANTHROPIC
    if provider in ai_mod.OPENAI_SHAPED:
        fields = ai_route_fields(cfg, provider, None, body)
        # the switch as saved, or as Settings' box stands while it is open (the page asks only while it is on)
        if cfg.get("ai_suggest") or body.get("ai_suggest") is True:
            listed = ai_mod.openai_model_list(provider, provider_key(provider, fields["address"]),
                                              fields["address"], transport=ai_transport())
        else:
            listed = {"models": [], "source": "off", "note": ""}
        return {"provider": provider, "model": fields["model"], "openai": dict(listed, provider=provider),
                "anthropic": {"models": ai_mod.model_options(ai_mod.ANTHROPIC_MODELS), "source": "builtin", "note": ""},
                "local_model": str(cfg.get("local_model") or ""),
                "local": {"running": False, "models": [], "note": "", "url": cfg.get("local_url")}}
    try:
        anthropic = anthropic_list(bool(body.get("fresh")))
    except Exception:
        anthropic = {"models": ai_mod.model_options(ai_mod.ANTHROPIC_MODELS), "source": "builtin",
                     "note": i18n.t("errors.built_list")}
    return {"provider": provider,
            "model": ai_mod.plain_model(cfg.get("model")) or ai_mod.MODEL,
            "local_model": str(cfg.get("local_model") or ""),
            "anthropic": anthropic,
            "local": ai_mod.local_models(str(body.get("local_url") or "").strip() or cfg.get("local_url"))}


def openai_provider_of(body: dict) -> str | None:
    """The OpenAI-style provider a key route is asked about, or None for Anthropic's own."""
    return body.get("provider") if body.get("provider") in ai_mod.OPENAI_SHAPED else None


def body_address(body: dict) -> str:
    """The address a key route is asked about: the one typed in the body, else the settings'."""
    return str(body.get("ai_address") or config().get("ai_address") or "").strip()


def api_key(body: dict) -> dict:
    """Store the API key, or remove it. The value never comes back and never reaches a file here.

    It goes to the macOS keychain as a generic password under `ANTHROPIC_API_KEY`. Nothing about
    it is returned but the fact that it was saved, and no exception from below is passed on,
    because the argv of the `security` call carries the key.
    """
    forget_models()                               # a new key, or none, may see another list
    run, env = key_place()
    other = openai_provider_of(body)
    service = ai_mod.key_service(other, body_address(body)) if other else ai_mod.KEYCHAIN_SERVICE
    if other:
        env = None                                # the OpenAI-style providers' keys are never in a `.env`
        if not service or (other == ai_mod.OTHER and not ai_mod.address_ok(body_address(body))):
            return {"error": i18n.t("errors.key_could_stored")}
    try:
        if body.get("clear"):
            return {"cleared": bool(ai_mod.clear_key(runner=run, service=service, env_path=env).get("cleared"))}
        result = ai_mod.save_key(body.get("key"), runner=run, service=service, env_path=env)
    except Exception:
        return {"error": i18n.t("errors.key_could_stored")}
    if result.get("error"):
        return {"error": result["error"]}
    return {"saved": True}


def check_openai(provider: str, typed: str, body: dict, run) -> dict:
    """Check key for an OpenAI-style provider (aiwire): its list of models asked with the key typed or the
    one stored under its own keychain item. An accepted key that was typed is stored there, a refused one
    never, and the answer carries the list for the Model list. The key never comes back."""
    address = body_address(body)
    service = ai_mod.key_service(provider, address)
    try:
        key = typed or (provider_key(provider, address) if ai_mod.PRESETS[provider].get("service") else None)
    except Exception:
        key = None
    answer = ai_mod.check_openai_key(provider, key, address, transport=ai_transport(),
                                     api_version=config().get("ai_api_version"))
    if not answer.get("ok"):
        return {"ok": False, "said": answer["said"]}
    if typed and service:
        try:
            stored = ai_mod.save_key(typed, runner=run, service=service, env_path=None)
        except Exception:
            stored = {"error": True}
        if stored.get("error"):
            return {"ok": False, "said": i18n.t("errors.key_works_but_could_stored")}
    where = None
    if service:
        try:
            where = ai_mod.key_status(None, runner=run, service=service).get("source")
        except Exception:
            where = None
    return {"ok": True, "said": answer["said"], "openai": dict(answer["list"], provider=provider), "source": where}


def api_check_key(body: dict) -> dict:
    """Check key, beside the API key in Settings (Adam, 21 October): Anthropic asked, through the server,
    which models the key can call, the key typed in the field or else the one stored. An accepted key
    that was typed is stored as Save key stored it, and the answer carries the models for the Model
    list. A refused one is never stored, and the list is left as it was. The key never comes back, and
    nothing about it reaches a log."""
    run, env = key_place()
    typed = str(body.get("key") or "").strip()
    other = openai_provider_of(body)
    if other:
        return check_openai(other, typed, body, run)
    try:
        key = typed or ai_mod.find_key(env, runner=run)
    except Exception:
        key = None
    answer = ai_mod.check_key(key, transport=ai_transport())
    if not answer.get("ok"):
        return {"ok": False, "said": answer["said"]}
    if typed:
        try:
            stored = ai_mod.save_key(typed, runner=run, env_path=env)
        except Exception:
            stored = {"error": True}
        if stored.get("error"):
            return {"ok": False, "said": i18n.t("errors.key_works_but_could_stored")}
    forget_models()
    if answer["anthropic"].get("source") == "live":
        _model_cache.update(at=time.monotonic(), answer=answer["anthropic"])
    try:
        where = ai_mod.key_status(env, runner=run).get("source")
    except Exception:
        where = None
    return {"ok": True, "said": answer["said"], "anthropic": answer["anthropic"], "source": where}


def api_key_status(body: dict) -> dict:
    """Whether a key is stored and where it sits. Never what it is. For an OpenAI-style provider named in
    the body, under its own keychain item."""
    run, env = key_place()
    other = openai_provider_of(body or {})
    try:
        if other:
            service = ai_mod.key_service(other, body_address(body))
            return ai_mod.key_status(None, runner=run, service=service) if service else {"set": False, "source": None}
        return ai_mod.key_status(env, runner=run)
    except Exception:
        return {"set": False, "source": None}


# --------------------------------------------------------------- feedback

# Send feedback: a tester's note, a bug or an idea, posted to Adam's own collector, a Cloudflare
# Worker writing one row to a D1 table (see `feedback-worker/`). FEEDBACK_URL is its address, deployed
# on 3 October 2026, and `feedback_url` in config.json stands in for it on one machine.
# With neither, the bug in the bar is hidden and the route says so. The note goes only when he
# presses Send, with the app's version, the system in plain words, the browser's user agent, the
# screen it came from as one word and the time. Never a case, a file, a path, a key or the settings.
FEEDBACK_URL = "https://idiograph-feedback.adam-e56.workers.dev/v1/feedback"
FEEDBACK_TIMEOUT = 15
# the collector refuses a body over 8 KB, so the server stops a longer note before it goes
FEEDBACK_MAX = 8192
# the screens a note may name, each one short word as its bar sends it: the first screen, a project's
# page, Experiential statements, PETs, GETs, Sift, its searches and Trace. The collector keeps the same
# list, and any other word, or anything that is not a word of it, goes as none
FEEDBACK_SCREENS = ("home", "project", "statements", "pets", "gets", "sift", "searches", "trace")
# a note that did not go, in plain words: one that never reached the service, and one it refused, its
# status in brackets (17 October, later)
# the transport, `(method, url, headers, payload, timeout)` answering `(status, body)`, the shape
# ai_suggest's calls take, so the suite hands it a fake and nothing reaches the network
FEEDBACK_SEND = ai_mod.http_call


def feedback_url(cfg: dict) -> str:
    """The collector's address: `feedback_url` in the settings over FEEDBACK_URL, and only an
    http or https address, so a stray value never opens a file."""
    url = str(cfg.get("feedback_url") or FEEDBACK_URL or "").strip()
    return url if re.match(r"^https?://[^\s/]+", url) else ""


def platform_words() -> str:
    """The system in plain words with `sys.platform` after it, "macOS 15.5, darwin"."""
    try:
        if sys.platform == "darwin":
            release = platform.mac_ver()[0]
            words = f"macOS {release}" if release else "macOS"
        elif sys.platform.startswith("win"):
            release, build = platform.win32_ver()[:2]
            words = " ".join(w for w in ("Windows", release, f"(build {build})" if build else "") if w)
        else:
            words = " ".join(w for w in (platform.system(), platform.release()) if w)
    except Exception:
        words = ""
    return f"{words}, {sys.platform}" if words else sys.platform


def feedback_payload(text: str, contact, screen, agent, now: datetime | None = None) -> dict:
    """The note as it travels: his words, the reply address he chose to give, and what the server
    knows, the version, the system, the screen as one word, the user agent and the time. Nothing
    else is ever added."""
    return {
        "text": str(text),
        "contact": str(contact or "").strip()[:200],
        "version": f"{VERSION} build {BUILD}" if BUILD else VERSION,
        "platform": platform_words(),
        "screen": screen if screen in FEEDBACK_SCREENS else "",
        "agent": str(agent or "").strip()[:400],
        "at": (now or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
    }


def api_feedback(body: dict) -> dict:
    """Send one note to the collector and answer with the row's id, or one line saying why not."""
    url = feedback_url(config())
    if not url:
        return {"error": i18n.t("errors.feedback_set_up_build"), "status": 501}
    text = str(body.get("text") or "").strip()
    if not text:
        return {"error": i18n.t("errors.write_note_first"), "status": 400}
    payload = feedback_payload(text, body.get("contact"), body.get("screen"), body.get("agent"))
    if len(json.dumps(payload).encode("utf-8")) > FEEDBACK_MAX:
        return {"error": i18n.t("errors.note_too_long_send_one"), "status": 413}
    headers = {"content-type": "application/json", "user-agent": f"Idiograph/{VERSION}"}
    try:
        status, answer = FEEDBACK_SEND("POST", url, headers, payload, FEEDBACK_TIMEOUT)
    except Exception:
        status, answer = 0, ""
    if status == 0:
        return {"error": i18n.t("errors.note_could_sent_check_connection"), "status": 502}
    if not 200 <= status < 300:
        # in plain words with the status in brackets, never the service's own answer (17 October, later)
        return {"error": i18n.t("errors.note_could_sent_just_now", status=status), "status": 502}
    try:
        row = json.loads(answer or "{}").get("id")
    except (ValueError, AttributeError):
        row = None
    return {"sent": True, "id": row}


# ------------------------------------------------- Using your own AI agents

# Each app's AI features page ends with "Using your own AI agent" (Adam, 21 October 2026): a box of words
# to paste into an agent he already uses, Claude Code or another, saying where this install's command
# line, its MCP server and its guide for agents are, and the rule to dry-run first and show the result
# before any write. The paths are this install's own: the Mac app's server inside the bundle, the Windows
# app's console twin, or from source the app's command beside the code and the venv's python running
# mcp_server.py. Every app its own command, server and guide.
AGENT_START_PATH = "/api/agent-start"
AGENT_WHAT = {"idiograph": "an app for Interpretative Phenomenological Analysis (IPA) and thematic analysis",
              "sift": "an app for a systematic review's searches and screening",
              "trace": "an app that holds each claim a manuscript makes against its source"}
# the first command to try, Idiograph's projects and participants, Sift's and Trace's own list of commands
AGENT_TRY = {"idiograph": ["cases"], "sift": ["--help"], "trace": ["--help"]}


def agent_line(words: list[str], windows: bool) -> str:
    """A command as its system's shell takes it, each word quoted where it needs to be."""
    return subprocess.list2cmdline(words) if windows else " ".join(shlex.quote(w) for w in words)


def agent_commands(app: str | None = None, frozen: bool | None = None, executable: str | None = None,
                   here: Path | None = None, system: str | None = None) -> dict:
    """How an agent runs this install of `app`: `cli` its command line, `mcp` its MCP server, and `guide`
    its guide's file and `uri` the same guide as the MCP server's resource. Frozen, the app's own server
    with `cli` or `mcp` first, on Windows its console twin, since the windowed one prints nothing. From
    source, `idiograph`, `sift` or `trace` beside the code (its `.bat` on Windows), and the venv's python
    running mcp_server.py, with `--app` for Sift and Trace."""
    import mcp_server
    name = app_identity.check(app or APP)
    frozen = FROZEN if frozen is None else frozen
    exe = executable or sys.executable
    windows = app_folders.is_windows(system)
    # a frozen install's folder in its own system's shape, a Mac's with / and a Windows install's with \,
    # whatever machine draws it (22 October: a Mac app's guide came out with \ in the suite on Windows).
    # From source the folder is this machine's own, read for its venv
    if here is None:
        here = HERE
    elif frozen:
        here = (PureWindowsPath if windows else PurePosixPath)(here)
    else:
        here = Path(here)
    if frozen:
        if windows:
            exe = str(PureWindowsPath(exe).with_name(app_folders.console_exe(name)))
        cli, mcp = [exe, "cli"], [exe, "mcp"]
    else:
        cli = [str(here / (name + (".bat" if windows else "")))]
        mcp = mcp_server.server_command(frozen=False, executable=exe, here=Path(here), system=system)
        mcp += ["--app", name] if name != "idiograph" else []
    guide = here / "docs" / mcp_server.GUIDES[name].name
    return {"app": name, "windows": windows, "cli": cli, "mcp": mcp, "guide": str(guide),
            "uri": mcp_server.guide_uri(name)}


def agent_start(how: dict) -> str:
    """The words the box holds, for `agent_commands`' answer."""
    name, windows = how["app"], how["windows"]
    title = app_identity.APPS[name]["name"]
    lines = [
        f"I use {title}, {AGENT_WHAT[name]}, on this computer. Help me with my work in it through its "
        "command line or its MCP server, never by editing its files.",
        "",
        f"Read its guide for agents first: the MCP resource {how['uri']}, or the file {how['guide']}",
        "",
        "Its command line: " + agent_line(how["cli"] + AGENT_TRY[name], windows),
        "",
        "Its MCP server, for Claude Code: " + agent_line(["claude", "mcp", "add", "--scope", "user", name, "--"]
                                                       + how["mcp"], windows),
        "For another agent, the MCP server's command: " + agent_line(how["mcp"], windows),
        "",
    ]
    if name == "idiograph":
        lines += ["It opens a project to you only where its Project settings, \"Allow AI agents to read this "
                  "project\" is ticked.", ""]
    lines.append("Run every change as a dry run first (--dry-run on the command line, dry_run on a tool), show "
                 "me what it would do, and write only when I say yes.")
    return "\n".join(lines)


def api_agent_start(_body: dict) -> dict:
    """The box under Using your own AI agents: its words, and the paths they hold."""
    how = agent_commands()
    return {"text": agent_start(how), "cli": how["cli"], "mcp": how["mcp"], "guide": how["guide"], "uri": how["uri"]}


# ------------------------------------------------- Restart and Quit, from the page

# Settings' foot, and the restart line wherever it shows, restart or quit the server from the page:
# a POST to SERVER_PATH with `op` of `restart` or `quit`, refused from any page but the server's
# own, and a GET the server's own state, which the page asks for at boot and waits on through a
# restart. Restart waits for any write in hand, answers, closes the listening socket and runs the
# same program again in this same process, so the pid file a launcher keeps still names it. Quit
# answers and ends the server as a launcher's Stop does, the pid file cleared.
SERVER_PATH = "/api/server"
SERVER_OPS = ("restart", "quit")
# this start of the server, told apart from the next one by a page waiting through a restart
STARTED = f"{os.getpid()}-{time.time_ns()}"
# the program a restart runs again: the Mac app's launcher sets it, and else it is this file as it
# was run, read in `main`
RELAUNCH: list[str] | None = None
ARGV: list[str] = []
# how a restart runs the program again, a name so the suite can stand in for it
EXEC = os.execve
# and how one on Windows starts it anew, the same
POPEN = subprocess.Popen


def spawn_again(command: list[str], env: dict, key: str | None = None) -> None:
    """A restart on Windows, which cannot run a program again in one process: the same program
    started anew as a process of its own, in the same window and writing to the same output as this
    one, which then ends as `main` returns. A stream this process lacks, as a program with no window
    lacks one, is none for the new one too. The window's `key`, when it handed one over, goes on the new
    one's standard input, a pipe, never in its environment (see `take_window_key`)."""
    streams = {}
    for name, fd in (("stdin", 0), ("stdout", 1), ("stderr", 2)):
        try:
            os.fstat(fd)
            streams[name] = fd
        except OSError:
            streams[name] = subprocess.DEVNULL
    if key:
        streams["stdin"] = subprocess.PIPE
    child = POPEN(command, env=env, close_fds=True, **streams)
    if key and getattr(child, "stdin", None) is not None:
        child.stdin.write((key + "\n").encode("ascii"))
        child.stdin.close()


# Windows cannot run a program again in the same process, so there a restart starts the server anew,
# `spawn_again` from source and in run.bat's window, and in the Windows app its launcher's own,
# `windows_launcher.respawn(command, env)`, which it sets here. This one then ends as `main` returns.
# A Mac and Linux run it again in the same process through EXEC, with this None
SPAWN = spawn_again if sys.platform == "win32" else None
SERVER_STATE: dict = {"op": None}
# set for a restart, so the browser is not opened a second time
RESTARTED = "IDIOGRAPH_RESTARTED"
# set by run.command, run.sh and run.bat, so Quit can say how to open the app again
STARTED_BY = "IDIOGRAPH_START"
# every request, not Restart and Quit alone: a page served from anywhere else, or a name that only
# points at this machine, gets nothing read and nothing written


def named(line: str, **more) -> str:
    """One of the server's own lines in the running app's name, Idiograph, Sift or Trace (see `app_identity`)."""
    return line.format(name=IDENTITY["name"], **more)


def own_origin(headers, address) -> bool:
    """A request from the server's own page: its Host the server's own address, and its Origin, when
    it sends one, the same, so no page served from anywhere else, and no name that only points at
    this machine, can read a case, write one or press Restart or Quit."""
    port = address[1] if len(address) > 1 else ""
    names = {f"{h}:{port}" for h in (str(address[0]), "127.0.0.1", "localhost", "[::1]")}
    if str(headers.get("Host") or "").strip().lower() not in names:
        return False
    origin = str(headers.get("Origin") or "").strip().lower()
    return not origin or origin in {f"http://{n}" for n in names}


# ------------------------------------------------- The window's key (agentlock, 2 November 2026)

# `own_origin` passes any program on this machine that names the server's own address, so a shell's curl
# could approve an agent's held action or turn on Dangerously skip permissions. What governs agents asks
# for a key besides, made at each start and never served by any route. The window makes it and hands it
# to its page in a script it runs before the page's own, and to the server it starts on the server's
# standard input, a pipe no other program reads, with WINDOW_KEY_FROM saying so and never the key. A run
# from source in a browser has no window to hold it, so the server makes its own and puts it in the page
# it serves, where a program on this machine has to read the page first: a second step, not a lock (see
# docs/internals.md, The window's key).
WINDOW_KEY_FROM = "IDIOGRAPH_WINDOW_KEY"
KEY_HEADER = "X-Idiograph-Key"
# `key` the one this start takes, and `window` whether the window handed it over (else the page carries it)
WINDOW_KEY = {"key": secrets.token_urlsafe(32), "window": False}
# each route that governs agents, with the one key of a body that makes it so, or None for every call:
# an app's own join it (see `register`), Idiograph's /api/holds, /api/mcp, /api/agents-guide, the
# skip_permissions setting and a project's tick for agents
WINDOW_ONLY: dict = {}
# where the window's key is read from, a name so the suite can stand in for it
READ_KEY = None


def key_line(fd: int = 0) -> str:
    """One line from `fd`, the window's key as the window wrote it, read to its end or its newline, and "" when
    there is none to read."""
    got = b""
    try:
        while len(got) < 512 and not got.endswith(b"\n"):
            more = os.read(fd, 512 - len(got))
            if not more:
                break
            got += more
    except OSError:
        return ""
    return got.decode("ascii", "replace").strip()


def take_window_key(env: dict | None = None) -> None:
    """This start's key: the window's, read from standard input when WINDOW_KEY_FROM says it is there, or one
    made here for a page in a browser, which the page then carries (see `keyed_page`). A window's key that
    never came is said in the log, and the run goes on as a browser's."""
    env = os.environ if env is None else env
    if env.get(WINDOW_KEY_FROM) == "stdin":
        key = (READ_KEY or key_line)()
        if len(key) >= 32:
            WINDOW_KEY.update(key=key, window=True)
            return
        print("The window's key did not arrive, so this run's page carries one.", flush=True)
    WINDOW_KEY.update(key=secrets.token_urlsafe(32), window=False)


def keyed(headers) -> bool:
    """Whether a request carries this start's key."""
    sent = str(headers.get(KEY_HEADER) or "")
    return bool(sent) and hmac.compare_digest(sent.encode("utf-8", "replace"), WINDOW_KEY["key"].encode("ascii"))


def window_only(path: str, body) -> bool:
    """Whether a call governs agents, so that only the app's own window may make it: a route of WINDOW_ONLY,
    every call to it or only one whose body carries its key."""
    if path not in WINDOW_ONLY:
        return False
    key = WINDOW_ONLY[path]
    return key is None or (isinstance(body, dict) and key in body)


def keyed_page(page: str) -> str:
    """The page with the key in its head for a run in a browser, which has no window to hand it over, and
    as it is for the window's own run, whose window hands its page the key itself."""
    if WINDOW_KEY["window"] or 'name="idiograph-key"' in page:
        return page
    return page.replace("</head>", f'<meta name="idiograph-key" content="{WINDOW_KEY["key"]}"></head>', 1)


def key_to_stdin() -> None:
    """Before a restart on a Mac or Linux, which runs the program again in this process: the window's key put
    on a pipe as this process's standard input, where the run that follows reads it (see `take_window_key`)."""
    if not WINDOW_KEY["window"]:
        return
    read, write = os.pipe()
    os.write(write, (WINDOW_KEY["key"] + "\n").encode("ascii"))
    os.close(write)
    os.dup2(read, 0)
    os.close(read)


# Dangerously skip permissions turned on or off, a line each time in a file beside the app's settings
# (agentlock, 2 November 2026): when, on or off, and from where, the window or a page in a browser
SWITCH_SETTING = "skip_permissions"


def switch_record_path(config=None) -> Path:
    """The record of the switch, beside the settings file: `config.skip-permissions.jsonl` beside config.json, or
    beside the settings `config` names, which the agent log reads it from (agent_log.py)."""
    config = Path(config).expanduser().resolve() if config else CONFIG_PATH
    return config.with_name(config.stem + ".skip-permissions.jsonl")


def record_switch(on: bool) -> None:
    """A line in the switch's record: when, on or off, and from where."""
    line = {"at": datetime.now().astimezone().isoformat(timespec="seconds"), "on": bool(on),
            "from": "window" if WINDOW_KEY["window"] else "browser"}
    try:
        with open(switch_record_path(), "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(line) + "\n")
    except OSError as exc:
        print(f"The switch's record could not be written: {exc}", flush=True)


def restart_blocked(system: str | None = None) -> str | None:
    """Why this way of running cannot restart itself, in one line, or None when it can. Windows
    starts the server anew through SPAWN, so only a Windows run with none set cannot."""
    return named(i18n.t("errors.cannot_restart_itself_windows_close")) if (system or sys.platform).startswith("win") and SPAWN is None else None


def reopen_line(system: str | None = None) -> str:
    """How to open the app again once it is closed, by the way it was started."""
    system = system or sys.platform
    how = os.environ.get(STARTED_BY, "")
    if FROZEN:
        if system.startswith("win"):
            return i18n.t("errors.open_again_start_menu", name=IDENTITY["name"])
        return i18n.t("errors.open_again_applications", name=IDENTITY["name"])
    if how in ("run.bat", "run.command"):
        return i18n.t("errors.open_again_double_click", how=how)
    if how == "run.sh":
        return i18n.t("errors.open_again_run_run_sh")
    if system == "darwin" and not (sys.stdin is not None and sys.stdin.isatty()):
        return i18n.t("errors.open_again_double_click_idiograph")
    return i18n.t("errors.open_again_run_server_py")


def server_state() -> dict:
    """The server's own state, with `app`, which of the family's three apps it is (see `app_identity`)."""
    return {"started": STARTED, "pid": os.getpid(), "restart": restart_blocked(), "reopen": reopen_line(),
            "window": in_window(), "quit": quit_word(), "app": APP, "version": VERSION,
            "build": BUILD}


def quit_word(system: str | None = None) -> str:
    """Settings' word for quitting, as the system names it: Exit Idiograph in Idiograph's own window on
    Windows, whose File menu says Exit, and Quit Idiograph everywhere else, a browser's tab among them
    (17 October, the third Tauri build)."""
    system = system or sys.platform
    name = IDENTITY["name"]
    return f"Exit {name}" if in_window() and system.startswith("win") else f"Quit {name}"


# ------------------------------------------------------------- the family on each Home

# Where a frozen Mac or Windows build of each app is installed, looked for by `family_rows`: a Mac's
# Applications folders, the system's and his own, and on Windows the folder each installer writes to
MAC_APPS = (Path("/Applications"), Path.home() / "Applications")


def installed_at(app: str, system: str | None = None) -> Path | None:
    """Where the app is installed on this machine, or None. A frozen build looks for the other app's
    own build. A run from source holds every app's code, so every app is there to run from it."""
    them = app_identity.APPS[app]
    system = system or sys.platform
    if not FROZEN:
        return HERE / "server.py"
    if system == "darwin":
        for folder in MAC_APPS:
            if (folder / f"{them['name']}.app").is_dir():
                return folder / f"{them['name']}.app"
        return None
    if system.startswith("win"):
        local = os.environ.get("LOCALAPPDATA") or ""
        exe = Path(local) / them["name"] / f"{them['name']}.exe" if local else None
        return exe if exe and exe.is_file() else None
    return None


def releases_page(app: str) -> str:
    """The page an app is downloaded from, its own releases repository's latest release."""
    return f"https://github.com/{app_identity.APPS[app]['releases']}/releases/latest"


def family_line(app: str) -> str:
    """An app's one line in the run's language (i18nleft4, 2 November 2026), `app_identity`'s English where the
    catalogue has no key for the app."""
    said = {"idiograph": lambda: i18n.t("shell.family.line.idiograph"),
            "sift": lambda: i18n.t("shell.family.line.sift"),
            "trace": lambda: i18n.t("shell.family.line.trace")}
    return said[app]() if app in said else app_identity.APPS[app]["line"]


def family_rows() -> list[dict]:
    """The other two apps of the family, as each Home's foot shows them (decision 4 of the split's plan:
    always shown): each with its id, name, one line, and whether it is installed here, which says Open
    and otherwise Download."""
    return [{"app": key, "name": them["name"], "line": family_line(key), "installed": installed_at(key) is not None}
            for key, them in app_identity.APPS.items() if key != APP]


def api_family(_body: dict) -> dict:
    """The family at the foot of each Home (see `family_rows`). Only reads."""
    return {"app": APP, "apps": family_rows()}


# what Open and Download run, a hook a check replaces so nothing is opened or started
FAMILY_OPENER = None


def family_open_plan(app: str, system: str | None = None) -> dict:
    """What Open or Download does for another app of the family: an installed Mac build opened by its
    bundle, a Windows one run, from source that app's own server started from this code, and one not
    installed its releases page opened in the browser."""
    them = app_identity.APPS[app]
    system = system or sys.platform
    where = installed_at(app, system)
    if where is None:
        return {"do": "browse", "url": releases_page(app)}
    if not FROZEN:
        return {"do": "run", "command": [sys.executable, str(HERE / "server.py"), "--app", app],
                "url": f"http://127.0.0.1:{them['port']}/"}
    if system == "darwin":
        return {"do": "run", "command": ["open", "-b", them["bundle_id"]]}
    return {"do": "run", "command": [str(where)]}


def family_go(plan: dict) -> None:
    """Carry out a plan of `family_open_plan`: a page opened in the browser, or the app started apart
    from this server. A run from source whose app already answers on its port has its page opened."""
    if plan["do"] == "browse":
        webbrowser.open(plan["url"])
        return
    url = plan.get("url")
    if url:
        try:
            from urllib.request import urlopen
            with urlopen(url + "api/server", timeout=1.5):
                webbrowser.open(url)
                return
        except OSError:
            pass
    kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL, "stdin": subprocess.DEVNULL,
              "cwd": str(HERE)}
    if sys.platform.startswith("win"):
        kwargs["creationflags"] = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen(plan["command"], **kwargs)


def api_family_open(body: dict) -> dict:
    """Open or Download at a Home's foot: `app`, another app of the family, opened when it is installed
    and its releases page opened when not (see `family_open_plan`)."""
    app = str(body.get("app") or "")
    if app not in app_identity.APPS or app == APP:
        raise WorkbookError(i18n.t("errors.another_app_family"))
    plan = family_open_plan(app)
    (FAMILY_OPENER or family_go)(plan)
    return {"app": app, "did": plan["do"], "apps": family_rows()}


def api_home(_body: dict) -> dict:
    """Sift's and Trace's Home (the split's third build): what `/api/cases` gives Idiograph's, for the app
    this run is: its settings, the feedback bug, the folder dialog, its version, and its own projects,
    Sift's `reviews` or Trace's `traces`. Only reads."""
    cfg = config()
    answer = {"app": APP, "config": cfg, "feedback": bool(feedback_url(cfg)), "choose": PLATFORM == "darwin",
              "one": False, "version": VERSION, "build": BUILD, "projects": [], "demos": []}
    if APP in HOME_ROWS:
        key, rows = HOME_ROWS[APP]
        answer[key] = rows()
    return answer


def api_server(_body: dict) -> dict:
    """The server's own state, for a GET. A POST goes to `Handler._server_op`, which checks where it
    came from first."""
    return server_state()


def quiet(wait: float | None = None) -> bool:
    """Whether the writes in hand have finished, waited for up to `wait` seconds: every write the
    server makes holds its own lock, with the file lock the command line takes inside it."""
    if not _lock.acquire(timeout=locks.WAIT if wait is None else wait):
        return False
    _lock.release()
    return True


def relaunch() -> tuple[list[str], dict]:
    """The program a restart runs again, with its arguments and its environment: the Mac app's
    `--serve`, or the file this server was run as, from the folder it was run in."""
    if RELAUNCH:
        command = list(RELAUNCH)
    elif FROZEN:
        command = [sys.executable, "--serve", *ARGV[1:]]
    else:
        command = [sys.executable, *ARGV]
    env = dict(os.environ, **{RESTARTED: "1"})
    if FROZEN:
        env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    # a run with --root carries its list across, which it keeps in memory alone (see `carried_state`)
    env.pop(STATE_CARRIED, None)
    if STATE_MEMORY is not None:
        env[STATE_CARRIED] = json.dumps(STATE_MEMORY, ensure_ascii=False)
    return command, env


def pidfile(port: int, logs: Path | None = None) -> Path:
    """A launcher's pid file for this port, `idiograph-<port>.pid` in the logs folder."""
    return Path(logs if logs is not None else PATHS["logs"]) / f"idiograph-{port}.pid"


def clear_pidfile(port: int, logs: Path | None = None) -> bool:
    """The pid file removed when it names this process, as a launcher's Stop removes it."""
    path = pidfile(port, logs)
    try:
        if int(path.read_text(encoding="utf-8").strip()) == os.getpid():
            path.unlink()
            return True
    except (OSError, ValueError):
        pass
    return False


def finish(op: str, port: int) -> None:
    """After Restart or Quit has stopped the serving and closed the socket: the writes in hand
    waited for, then the same program run again in this process, or the pid file cleared and the
    server ended, as `main` returns."""
    held = _lock.acquire(timeout=60)
    try:
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.flush()
            except (AttributeError, OSError, ValueError):
                pass
        if op == "restart":
            print("Restarting.", flush=True)
            command, env = relaunch()
            try:
                if SPAWN is not None:
                    # Windows: the server started anew, and this one ends as `main` returns
                    if WINDOW_KEY["window"]:
                        SPAWN(command, env, key=WINDOW_KEY["key"])
                    else:
                        SPAWN(command, env)
                else:
                    # the window's key on a pipe for the run that follows, never in its environment
                    key_to_stdin()
                    EXEC(command[0], command, env)
                return
            except OSError as exc:
                # the program could not run again, so this one ends as a quit does, and the page
                # waiting on it says how to open it
                print(f"{IDENTITY['name']} could not start again: {exc}", flush=True)
        clear_pidfile(port)
        # the window reads this line to know the quit was asked for, so it stays in English
        print(named(i18n.t("errors.closed", lang="en")), flush=True)
    finally:
        if held:
            _lock.release()


# ------------------------------------------------- Quitting after the last tab closes

# Idiograph quits by itself a few minutes after its last tab closes (16 October, Adam's word on a
# tester who closed the tab and found it still running). Every page it serves beats through
# BEAT_PATH about every thirty seconds, in view or hidden, and says a last word as it goes
# (`static/beat.js`), and every other request it answers, a page's own or an agent's, is a sign of
# use as well (see `in_use`). Once no sign has come for QUIT_AFTER seconds and nothing is running,
# the server quits by Quit's own path, the serving stopped and then `finish`, so every write has
# finished and its lock is let go. A request in hand, a write, a Restart or a Quit under way, a Sift
# search run, a Zotero sync or the demo's recording being made holds it, and the time starts again
# once that ends. The tick at the end of General, `quit_when_closed`, is read at every look, so
# turning it off holds at once, and STAY_OPEN in the environment keeps a run open whatever the tick
# says, as the suite's servers and a smoke's do.
BEAT_PATH = "/api/beat"
QUIT_AFTER = 5 * 60
# how often the watcher looks, in seconds, never more than a quarter of the wait
QUIT_LOOK = 15
# a look this many seconds later than it was due means the machine slept, when no tab could beat,
# so its tabs have the whole wait again from the waking
WOKE_AFTER = 60
STAY_OPEN = "IDIOGRAPH_STAY_OPEN"
# the wait in seconds, set in the environment by a check that waits a second or two, not five minutes
QUIT_AFTER_ENV = "IDIOGRAPH_QUIT_AFTER"
# the answer to a request that comes once the quit is decided, before the socket has closed
BEAT_TAG = '<script src="/beat.js"></script>'
_life = threading.Lock()
# the last sign of use on the monotonic clock, the requests in hand, and whether a quit is decided
LIFE = {"seen": time.monotonic(), "requests": 0, "closing": False}


def used() -> None:
    """A sign that the app is in use: a page's beat or its last word, or any request of its own page."""
    with _life:
        LIFE["seen"] = time.monotonic()


def in_use(method):
    """A request the handler answers: a sign of use as it comes and as it ends, when it is from the
    server's own page or a program on this machine (see `own_origin`), and while it is in hand a hold
    on quitting. One that comes once a quit is decided is told the app is closed, so no write starts
    after it."""
    @functools.wraps(method)
    def answered(self):
        ours = own_origin(self.headers, self.server.server_address)
        with _life:
            closing = LIFE["closing"]
            if not closing:
                LIFE["requests"] += 1
                if ours:
                    LIFE["seen"] = time.monotonic()
        if closing:
            return self._json({"error": named(i18n.t("errors.closed"))}, 503)
        try:
            return method(self)
        finally:
            with _life:
                LIFE["requests"] -= 1
                if ours:
                    LIFE["seen"] = time.monotonic()
    return answered


def api_beat(body: dict) -> dict:
    """A page's beat, or its last word as it goes, which `in_use` has already taken as a sign of use,
    so the wait runs from the moment the last tab closed. A beat names the page, `page`, and the project
    it is in front of, `at`, kept in PAGES so a project open in another window is never moved to the Trash
    (removetrash, 10 November 2026), and its last word, `gone`, takes the page off."""
    used()
    body = body if isinstance(body, dict) else {}
    page = str(body.get("page") or "")[:64]
    if page:
        with _life:
            if body.get("gone"):
                PAGES.pop(page, None)
            else:
                PAGES[page] = {"at": str(body.get("at") or "")[:2000], "seen": time.monotonic()}
    return {"heard": True}


# each page by its id, the project it is in front of and when it last beat (see `api_beat`)
PAGES: dict = {}
# a page that has not beaten for this long, a beat's thirty seconds and room, is taken as closed
PAGE_GONE_AFTER = 75


def open_elsewhere(match, page: str = "") -> bool:
    """Whether a page other than `page` is in front of a project now, `match(at)` saying whether the place a page
    named is the project's. Only reads."""
    now = time.monotonic()
    with _life:
        shown = [(k, v["at"]) for k, v in PAGES.items() if now - v["seen"] < PAGE_GONE_AFTER]
    for k, at in shown:
        if k != str(page or "") and at:
            try:
                if match(at):
                    return True
            except (OSError, ValueError, WorkbookError, OutsideRoot):
                continue
    return False


def known_projects() -> list[tuple[str, Path]]:
    """Every project folder this app's settings and recent list name, Idiograph's projects, Sift's and Trace's, each
    with its folder's name, for the Trash's guard (`trash_guard`). Only reads."""
    out = [(r.name, r) for r in project_roots()]
    held = state()
    for key in ("sift_reviews", "trace_projects"):
        for e in held.get(key) or []:
            if isinstance(e, dict) and e.get("folder"):
                folder = abs_path(str(e["folder"]))
                out.append((folder.name, folder))
    return out


def trash_guard(folder, name: str, match, page: str = "") -> Path:
    """Remove's tick to move a project's folder to the Trash (removetrash, 10 November 2026): the folder, resolved,
    once `trash.guard` refuses nothing and no other window is in front of the project (`open_elsewhere`, `match` its
    test of a page's place). Moves nothing."""
    import trash
    keep = [HERE, DEMO_DIR, demo_ta_dir(), SHIPPED_DEMO, CONFIG_PATH, STATE_PATH, PATHS["data"], PATHS["logs"]]
    chosen = trash.guard(folder, name=name, keep=keep,
                         others=[(n, p) for n, p in known_projects() if not same_folder(p, folder)])
    if open_elsewhere(match, page):
        raise trash.refused(i18n.t("trash.open", where=trash.where(), name=name))
    return chosen


def trash_move(folder: Path, name: str) -> str:
    """The project's folder put in the system's Trash (`trash.TRASH`), answering where it went, the Trash's own name.
    A move the system refuses is a plain line of its own, the folder left where it was, and the system's own words
    go to the server's log alone."""
    import trash
    try:
        return trash.TRASH(Path(folder))
    except WorkbookError:
        raise
    except Exception as exc:          # the system's own refusal, whatever it is
        why = str(exc).strip() or type(exc).__name__
        print(f"The move of {folder} to the Trash was refused: {why}", file=sys.stderr, flush=True)
        raise trash.refused(i18n.t("trash.failed", where=trash.where(), name=name)) from None


def record_removal(name: str, folder: Path, trashed: bool, by: str = "") -> None:
    """A line in the app's own record of removals, beside its settings (`trash.record`)."""
    import trash
    trash.record(CONFIG_PATH, APP, name, Path(folder), trashed, by)


def beating(page: str) -> str:
    """A page the server makes, a print view, with the beat that says it is open, once."""
    return page if BEAT_TAG in page else page.replace("</body>", BEAT_TAG + "</body>", 1)


# Nothing of the browser's own on a print view's paper: an empty box at the head and the foot of the page's
# margin keeps out the date, the title, the page's address with the project's folder in it and the page count
# that Chromium, and so Windows's web view in Idiograph's own window, print there by themselves (17 October)
PRINT_MARGINS = '<style>@page { @top-right { content: ""; } @bottom-right { content: ""; } }</style>'


def own_margins(page: str) -> str:
    """A print view with PRINT_MARGINS in its head, once."""
    return page if PRINT_MARGINS in page else page.replace("</head>", PRINT_MARGINS + "</head>", 1)


def quit_on(cfg: dict | None = None) -> bool:
    """Whether the server quits by itself after its last tab closes: the tick, on unless config.json
    says otherwise, and never in a run with STAY_OPEN set. A server the window started quits by itself
    whatever the tick says, since the window beats for as long as it is open and stops it as it
    closes, so the wait only ever runs out after a window that ended without a word (see `in_window`)."""
    if os.environ.get(STAY_OPEN):
        return False
    if in_window():
        return True
    cfg = config() if cfg is None else cfg
    return bool(cfg.get("quit_when_closed", True))


# The window, Idiograph in a window of its own (packaging/tauri), starts the server with WINDOW in its
# environment, which a Restart carries over. The page then hides the tick at the end of General,
# which means nothing in the window, as the app quits when its last window closes (17 October).
WINDOW = "IDIOGRAPH_WINDOW"


def in_window() -> bool:
    """Whether the window started this server."""
    return bool(os.environ.get(WINDOW))


# The window's own end without Quit, a crash or a Force Quit, left the server it started running until
# the wait ran out (31 October, quitcrash: 0.9.14 crashed as Adam quit it, and its server still held the
# port two minutes later). On a Mac a process whose parent has ended is handed to launchd, so the server
# notes its parent as it starts, and one the window started that finds its parent changed quits at the
# watcher's next look, as after the wait, once nothing holds it. A Restart on a Mac runs again in the
# same process under the same window. On Windows nothing is handed over, and a Restart starts the server
# anew from the old one, so it is never asked there.
PARENT = os.getppid()


def window_gone() -> bool:
    """Whether the window that started this server has ended without stopping it."""
    return in_window() and sys.platform != "win32" and os.getppid() != PARENT


def quit_wait() -> float:
    """The wait in seconds, QUIT_AFTER, or the one a check sets in the environment."""
    try:
        return max(0.2, float(os.environ.get(QUIT_AFTER_ENV) or QUIT_AFTER))
    except ValueError:
        return float(QUIT_AFTER)


def holding() -> str:
    """What holds a quit, in a few words, or "" for nothing: a request in hand, a write, a Restart or
    a Quit under way, or an app's work as it registers it (`HOLDS`), Idiograph's the demo's recording being
    made, Sift's a search run or a Zotero sync."""
    if LIFE["requests"]:
        return "a request"
    if _lock.locked():
        return "a write"
    if SERVER_STATE["op"]:
        return SERVER_STATE["op"]
    for held in hooks(HOLDS):
        said = held()
        if said:
            return said
    return ""


def idle_quit(server, wait: float | None = None, look: float | None = None,
              stop: threading.Event | None = None) -> bool:
    """The watcher, on a thread of its own from `main`. Every `look` seconds: with the tick off,
    something running, or the machine just woken, the time starts again, and once `wait` seconds have
    passed with no sign of use, or at once when the window that started it has gone (`window_gone`),
    the quit is decided under the same lock every request takes, the
    serving stopped as Quit stops it, and `main` finishes it as it finishes Quit (see `finish`).
    Answers True once it has quit, False when `stop` is set first."""
    wait = quit_wait() if wait is None else wait
    look = min(QUIT_LOOK, wait / 4) if look is None else look
    stop = stop or threading.Event()
    wall = time.time()
    while not stop.wait(look):
        try:
            on = quit_on()
        except Exception:                             # a settings file it cannot read keeps it open
            on = False
        woke = time.time() - wall > look + WOKE_AFTER
        wall = time.time()
        with _life:
            now = time.monotonic()
            if woke or not on or holding():
                LIFE["seen"] = now
                continue
            if now - LIFE["seen"] < wait and not window_gone():
                continue
            LIFE["closing"] = True
            SERVER_STATE["op"] = "quit"
        # the window reads this line to know the server quit by itself, so it stays in English
        print(named(i18n.t("errors.tab_been_open_few_minutes", lang="en")), flush=True)
        server.shutdown()
        return True
    return False


def watch_idle(server) -> threading.Thread | None:
    """The watcher started for this run, the wait from now, or None in a run with STAY_OPEN set,
    which never quits by itself, as the suite's servers and a smoke's."""
    used()
    if os.environ.get(STAY_OPEN):
        return None
    watcher = threading.Thread(target=idle_quit, args=(server,), daemon=True, name="idle-quit")
    watcher.start()
    return watcher


# What's new (18 October, the fourth Tauri build): docs/whats-new.md, a section a version, newest first,
# its heading the number and the date, `## 0.9.1, 17 October 2026`, and a plain line a part under it,
# which packaging/release.py also copies into the update's manifest. The page in Idiograph's own window
# shows the sections of every version since the one before as a sheet once after an update, and the running
# version's from Settings, General and the Help menu, each with Earlier versions (wnspan, 29 October 2026), all
# from this one answer. The window's bundle carries the file beside the manual, and a run from source reads it
# from docs/. A copy without it answers no versions, and the sheet says so.
WHATS_NEW_FILE = "whats-new.md"
WHATS_NEW_HEAD = re.compile(r"^## (\d+\.\d+\.\d+), (.+?)\s*$")


def whats_new_source() -> Path:
    """Where What's new is read from: beside the manual the window names, else docs/ beside the code."""
    return i18n.long_text(manual_source().with_name(WHATS_NEW_FILE))


def whats_new_versions(text: str) -> list[dict]:
    """Each version's number, date and lines, in the file's order, newest first. The lines before the
    first version's heading, the file's own title and its note, are not a version's."""
    versions: list[dict] = []
    for line in text.splitlines():
        head = WHATS_NEW_HEAD.match(line)
        if head:
            versions.append({"version": head.group(1), "date": head.group(2), "lines": []})
        elif versions and line.strip() and not line.startswith("#"):
            versions[-1]["lines"].append(line.strip())
    return versions


def api_whats_new(_body: dict) -> dict:
    """Every version's notes, for the page's sheet."""
    try:
        text = whats_new_source().read_text(encoding="utf-8")
    except OSError:
        return {"versions": []}
    return {"versions": whats_new_versions(text)}


# the routes every app answers, each app's own joining them as it registers (see `register`)
ROUTES = {
    "/api/search": api_search,
    "/api/settings": api_settings,
    "/api/models": api_models,
    "/api/key": api_key,
    "/api/key-status": api_key_status,
    "/api/check-key": api_check_key,
    "/api/feedback": api_feedback,
    AGENT_START_PATH: api_agent_start,
    # the agent log, each app's own beside its settings, read alone (agentlog and siftlog, 3 November 2026)
    "/api/agent-log": agent_log.api_agent_log,
    "/api/server": api_server,
    "/api/family": api_family,
    "/api/family-open": api_family_open,
    "/api/home": api_home,
    "/api/beat": api_beat,
    "/api/whats-new": api_whats_new,
}

# a request to these carries the key in its body, so the verbose log says the path and no more, and an
# app's own that carry one join it (see `register`): Sift's databases, whose `key` op carries a database's
# key, and its Zotero sync, whose `key` op carries his Zotero key
SILENT = ("/api/key",)
# these send something off the machine, open a dialog or write another program's settings, so they
# answer a POST from the page and never a GET, and an app's own join them (see `register`)
POST_ONLY = ("/api/feedback", "/api/family-open")
# these answer a POST only from the server's own page (see `own_origin`), and an app's own join them,
# Idiograph's /api/mcp, which writes Claude Desktop's settings
OWN_PAGE = (SERVER_PATH, "/api/family-open", "/api/agent-log")
# the design system's reference page, every component in a light panel and a dark one, from the app's
# own stylesheets, named in docs/design.md and in no menu (15 October)
DESIGN_PATH = "/design"
DESIGN_PAGE = "design.html"
# the page's icon at 32 pixels for a browser that takes no SVG icon, drawn once by make_app's
# draw_icon from the mark drawn for 16 pixels, beside static/favicon.svg (15 October)
FAVICON_PATH = "/favicon.png"
FAVICON_SIZE = 32
FAVICON = {}


def static_file(name: str, app: str | None = None) -> Path | None:
    """A page's file by its name under static/, from the first of boot's folders that has it, those of the
    apps a run of `app` serves, this run's by default, and the family's, so another app's file is not this
    app's page, as it is not in its bundle (the sixth build, 23 October 2026), or None when none has or the
    name would lead out of static/."""
    for root in boot.roots(apps_served(app)):
        base = (root / "static").resolve()
        target = (base / name).resolve()
        if str(target).startswith(str(base)) and target.exists():
            return target
    return None


def favicon_png() -> bytes:
    """The 32 pixel PNG of the app's icon, Sift's for Sift (static/favicon-sift.svg beside it), drawn
    on the first asking and kept."""
    if APP not in FAVICON:
        import make_app
        FAVICON[APP] = make_app.png_bytes(FAVICON_SIZE, make_app.draw_icon(FAVICON_SIZE, APP))
    return FAVICON[APP]


# The manual, each app's own as a page of its own, which the window's Help menu opens in a window of
# its own (17 October): Idiograph's docs/manual.md, Sift's docs/manual-sift.md and Trace's
# docs/manual-trace.md (20 October, `app_identity`). The window's bundle carries its app's file beside
# the server and names it in MANUAL_FILE, and a run from source reads it from docs/. A copy without it
# says so in one line.
MANUAL_PATH = "/manual"
MANUAL_FILE = "IDIOGRAPH_MANUAL"
# The licence, the GNU AGPL v3 in LICENSE beside the code, which every bundle carries (21 October), as
# plain text for the About card's link, so it opens with no internet
LICENCE_PATH = "/licence"
LICENCE_FILE = boot.resource("LICENSE")
MANUAL_STYLE = """
html { background: var(--paper); color: var(--ink); }
body { font: 15px/1.6 var(--serif); max-width: 46rem; margin: 0 auto; padding: 32px 24px 64px; }
h1, h2, h3, h4 { font-family: var(--sans); line-height: 1.25; margin: 1.8em 0 .5em; }
h1 { font-size: 26px; margin-top: 0; }
h2 { font-size: 19px; border-top: 1px solid var(--rule); padding-top: 1.2em; }
h3, h4 { font-size: 15.5px; }
p { margin: 0 0 1em; }
ul, ol { margin: 0 0 1em; padding-left: 1.5em; }
li { margin: 0 0 .35em; }
code { font: 13px var(--mono); background: var(--paper-sunk); padding: 1px 4px; border-radius: 3px; }
pre { background: var(--paper-sunk); padding: 12px 14px; border-radius: 6px; overflow-x: auto; }
pre code { padding: 0; background: none; }
a { color: var(--ink); }
nav { font-family: var(--sans); font-size: 13px; border: 1px solid var(--rule); border-radius: 8px;
      padding: 10px 16px; margin: 0 0 24px; }
nav a { display: block; padding: 2px 0; color: var(--ink-soft); text-decoration: none; }
nav a:hover { color: var(--ink); text-decoration: underline; }
.none { font-family: var(--sans); color: var(--ink-soft); }
"""
# The page on translating the apps (fmtcore, 28 October 2026): docs/translating.md, which every bundle carries
# (app_identity's family files), read as the manual is and opened from the line under Language, in a window of
# the app's own, so it opens offline too, and the repository is public since November 2026, so the line could point at the page on GitHub
TRANSLATING_PATH = "/translating"
TRANSLATING_FILE = "docs/translating.md"
TRANSLATING_TITLE = "Translating Idiograph"
# the appearance the page keeps, Light, Dark or Same as this computer, as the app's own pages take it
MANUAL_THEME = ("<script>try { var t = localStorage.getItem('idiograph-theme'); "
                "document.documentElement.dataset.theme = t === 'light' || t === 'dark' ? t : 'system'; } "
                "catch (e) { document.documentElement.dataset.theme = 'system'; }</script>")


def manual_source() -> Path:
    """Where the manual is read from: the file the window names, else the app's own in docs/ beside the code."""
    given = os.environ.get(MANUAL_FILE) or ""
    return Path(given) if given else boot.resource(f"docs/{IDENTITY['manual']}")


def translating_source() -> Path:
    """Where the page on translating is read from: beside the code, as every bundle carries it."""
    return boot.resource(TRANSLATING_FILE)


def translating_page(source: Path | None = None) -> tuple[int, str]:
    """The page on translating, read as the manual is with its lists, or a page of one line in a copy without it."""
    return manual_page(source or translating_source(), TRANSLATING_TITLE, i18n.t("errors.translating_copy"), lists=True)


def manual_inline(text: str) -> str:
    """One line of the manual's Markdown in HTML: code, bold, italics, and a link, which keeps its
    words alone unless it leads off this machine, since the docs it names beside it are not served."""
    parts = re.split(r"(`[^`]+`)", text)
    out = []
    for part in parts:
        if len(part) > 1 and part.startswith("`") and part.endswith("`"):
            out.append(f"<code>{html.escape(part[1:-1])}</code>")
            continue
        part = html.escape(part, quote=False)
        part = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
                      lambda m: f'<a href="{html.escape(m.group(2))}">{m.group(1)}</a>', part)
        part = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", part)
        part = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", part)
        part = re.sub(r"(?<![\w*])\*([^*\s][^*]*)\*(?![\w*])", r"<em>\1</em>", part)
        out.append(part)
    return "".join(out)


def manual_page(source: Path | None = None, title: str | None = None, gone: str | None = None,
                lists: bool = False) -> tuple[int, str]:
    """The manual as one page, its sections listed at its head, or a page of one line when this copy
    has no manual. Another of the docs the app carries reads the same way, by its `source`, its page's `title`
    and the line `gone` it says when the copy lacks it, the page on translating among them (fmtcore), whose lines
    starting "- " or "1. " are read as lists (`lists`)."""
    head = ['<!doctype html>', '<html lang="en-GB">', '<head><meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f'<title>{html.escape(title or IDENTITY["name"] + " manual")}</title>', MANUAL_THEME,
            '<link rel="stylesheet" href="/tokens.css">', f'<style>{MANUAL_STYLE}</style></head>', '<body>']
    try:
        text = (source or manual_source()).read_text(encoding="utf-8")
    except OSError:
        line = gone if gone is not None else i18n.t("errors.manual_copy")
        return 404, "\n".join(head + [f'<p class="none">{html.escape(named(line))}</p>', "</body>", "</html>", ""])
    body, para, code, contents = [], [], None, []
    # a list's kind, ul or ol, and its items' lines, where `lists` reads them as lists
    listing: list = []

    def end_list():
        if listing:
            kind, items = listing
            body.append(f"<{kind}>" + "".join(f"<li>{manual_inline(' '.join(i))}</li>" for i in items) + f"</{kind}>")
            listing.clear()

    def end_para():
        if para:
            body.append(f"<p>{manual_inline(' '.join(para))}</p>")
            para.clear()
        end_list()

    for line in text.splitlines():
        if code is not None:
            if line.startswith("```"):
                body.append(f"<pre><code>{html.escape(chr(10).join(code))}</code></pre>")
                code = None
            else:
                code.append(line)
            continue
        if line.startswith("```"):
            end_para()
            code = []
            continue
        heading = re.match(r"(#{1,4})\s+(.*)", line)
        if heading:
            end_para()
            level, words = len(heading.group(1)), heading.group(2).strip()
            anchor = re.sub(r"[^a-z0-9]+", "-", words.lower()).strip("-") or f"part-{len(body)}"
            if level == 2:
                contents.append(f'<a href="#{anchor}">{html.escape(words)}</a>')
            body.append(f'<h{level} id="{anchor}">{manual_inline(words)}</h{level}>')
            continue
        if not line.strip():
            end_para()
            continue
        item = re.match(r"(-|\d+\.)\s+(.*)", line) if lists else None
        if item:
            if para:
                end_para()
            kind = "ul" if item.group(1) == "-" else "ol"
            if listing and listing[0] != kind:
                end_list()
            if not listing:
                listing.extend([kind, []])
            listing[1].append([item.group(2).strip()])
            continue
        if listing and line.startswith(" "):
            listing[1][-1].append(line.strip())
            continue
        end_list()
        para.append(line.strip())
    end_para()
    if code is not None:
        body.append(f"<pre><code>{html.escape(chr(10).join(code))}</code></pre>")
    nav = [f'<nav aria-label="Contents">{"".join(contents)}</nav>'] if contents else []
    # the contents under the title, the first block
    return 200, "\n".join(head + body[:1] + nav + body[1:] + ["</body>", "</html>", ""])


# ------------------------------------------------------------- routes by app

# Which of the family's apps answers each route (the split's second build, 20 October 2026), the one table, each
# path's owner: `shared` every app answers, and each app its own, as it registers them (see `register`). Every
# route in ROUTES is here once, and the page's other paths with it, the print views, the recording, the PDFs, the
# manual, the icon and /design. A path in none of these is the page's own files. Until the sixth build (23 October
# 2026) a table of each app's paths, ROUTES_BY_APP, stood beside it, this computed from that.
SHARED_ROUTES = (SERVER_PATH, BEAT_PATH, "/api/settings", "/api/key", "/api/key-status", "/api/check-key", "/api/models",
                 "/api/feedback", "/api/whats-new", "/api/search", "/api/family", "/api/family-open", "/api/home",
                 AGENT_START_PATH, "/api/agent-log", MANUAL_PATH, TRANSLATING_PATH, LICENCE_PATH, FAVICON_PATH,
                 DESIGN_PATH)
ROUTE_APP = {path: "shared" for path in SHARED_ROUTES}
# a path an app's registration claimed that another owner already had, which it never takes (see `unplaced_routes`)
CLAIMED_TWICE: list = []
# The apps whose routes an app answers beside its own. Until the cutover Idiograph answered Sift's and
# Trace's as before the split, and since it (the sixth build, 23 October 2026) each app answers its own
# alone. The one table is `app_identity.SERVES_TOO`, which the command line and the MCP servers follow too.
SERVES_TOO = app_identity.SERVES_TOO

# ------------------------------------------------------------- the apps' registrations

# Each app's own code registers what it answers with the family's server (the family codebase's second
# build, 22 October 2026), so the server names no app's module: Trace's in apps/trace/trace_routes.py and
# Sift's in apps/sift/sift_routes.py (the third build), which `boot.load("routes")` at the foot of this file
# imports by its name, and Idiograph's still in this file until its build. `register` puts an app's routes in
# ROUTES and ROUTE_APP, so `not_here` and the boundary check see them as ever, and keeps beside them the
# paths its GETs answer, its rows on the home screen, its Search's scope and its projects under Everything,
# and since the third build the routes whose body carries a key, the settings it cleans, the modules that keep
# its keys' file and its work that holds a quit.
GET_PATHS: dict = {}            # a path an app's GET answers, its handler taking the query and answering (code, body, type)
HOME_ROWS: dict = {}            # an app's projects on the home screen, (the answer's key, the rows), Idiograph's and its own
SEARCH_SCOPES: dict = {}        # a Search scope an app holds, its handler taking the body and the kinds ticked
SEARCH_ROWS: dict = {}          # an app's projects under Everything, by the part of the answer they stand in
# Each hook below is kept with its app's name, (the app, the hook), and a run calls those of the apps it serves
# alone (`hooks`): every app's module registers in every app's server from source, since `boot.load` imports each
# one it finds, so until the sixth build (23 October 2026) Sift's and Trace's servers ran Idiograph's settings hooks
SETTINGS_CLEAN: dict = {}       # an app's settings, {setting: (the kind a save sends it as, its cleaner)}, as Settings saves them
KEY_FILES: list = []            # an app's module that keeps its keys' file as ENV_PATH, set as the app's paths are
HOLDS: list = []                # an app's work under way that holds a quit, each answering a few words or ""
# and since the fourth build, Idiograph's (22 October 2026)
STREAMS: dict = {}              # a path an app's GET answers through the handler itself, (handler, query), a recording
SCOPES: list = []               # a scope an app runs its routes' requests in, a context manager taking (route, body)
SETTINGS_READ: list = []        # an app's settings as `merge_config` reads them from the file, each taking (cfg, saved)
SETTINGS_SAVE: list = []        # an app's settings as `api_settings` saves them, each taking (cfg, body)
AI_CHOICE: list = []            # an app's screen's own provider and model for `ai_state`, taking the settings
AI_MORE: list = []              # what else `ai_state` carries for an app's screens, taking the settings
QUESTION: list = []             # the research question an AI route fills its prompt with, taking the body
STARTS: list = []               # what an app does as the server starts, its hook taking whether the run is of one --root


def register(app: str, routes: dict | None = None, post_only=(), get_paths: dict | None = None, home=None,
             search_scope=None, search_rows=None, silent=(), settings: dict | None = None, key_files=(),
             holding=None, streams: dict | None = None, own_page=(), defaults=(), own_settings=None,
             read_settings=None, save_settings=None, ai_choice=None, ai_more=None, question=None, scope=None,
             start=None, window_only=None) -> None:
    """What `app` answers, from its own module: `routes`, each path's handler, those of them that answer a
    POST alone in `post_only`, `get_paths`, the paths it answers a GET at outside /api/, `home`, the key of its
    projects in the home screen's answer and the function that lists them, `search_scope`, a Search scope's
    name and its handler, and `search_rows`, its projects as Everything searches them. `silent`, its routes
    whose body can carry a key, which the verbose log names by their path alone, `settings`, each setting of
    its own with the kind a save sends it as and the function that cleans it, `key_files`, its modules that
    keep a key's file as `ENV_PATH`, and `holding`, what of its work under way holds a quit. Since the fourth build (22 October 2026), for Idiograph's: `streams`, the paths its
    GETs answer through the handler itself, `own_page`, its routes only its own page may ask, `defaults`, its
    settings with their defaults in blocks each before a setting of the family's (`place_defaults`),
    `own_settings`, the keys of its own another app's save leaves alone (Sift's too since the sixth build), `read_settings` and `save_settings`,
    its settings as the file is read and as a save sends them, `ai_choice` and `ai_more`, its screen's own
    model and what else the AI's state carries, `question`, the research question an AI route asks, `scope`,
    the scope its routes' requests run in, and `start`, what it does as the server starts. `window_only` (agentlock,
    2 November 2026), its routes that govern agents, each with the one key of a body that makes it so or None
    for every call, answered only with the window's key (see `WINDOW_ONLY`). Called once, as its module is
    first imported."""
    global POST_ONLY, SILENT, OWN_PAGE
    routes, get_paths, streams = dict(routes or {}), dict(get_paths or {}), dict(streams or {})
    ROUTES.update(routes)
    POST_ONLY = POST_ONLY + tuple(p for p in post_only if p not in POST_ONLY)
    SILENT = SILENT + tuple(p for p in silent if p not in SILENT)
    OWN_PAGE = OWN_PAGE + tuple(p for p in own_page if p not in OWN_PAGE)
    WINDOW_ONLY.update(window_only or {})
    STREAMS.update(streams)
    APP_DEFAULTS[app] = tuple(APP_DEFAULTS.get(app, ())) + tuple(defaults)
    if own_settings is not None:
        SETTINGS_BY_APP[app] = tuple(own_settings)
    # each hook kept with its app's name, since only the apps a run serves run theirs (see `hooks`)
    for hook, held in ((read_settings, SETTINGS_READ), (save_settings, SETTINGS_SAVE), (ai_choice, AI_CHOICE),
                       (ai_more, AI_MORE), (question, QUESTION), (scope, SCOPES), (start, STARTS), (holding, HOLDS)):
        if hook is not None:
            held.append((app, hook))
    if settings:
        SETTINGS_CLEAN.setdefault(app, {}).update(settings)
    for mod in key_files:
        mod.ENV_PATH = ENV_PATH
        KEY_FILES.append(mod)
    GET_PATHS.update(get_paths)
    for path in (*routes, *get_paths, *streams):
        if ROUTE_APP.get(path, app) != app:
            CLAIMED_TWICE.append(path)
        else:
            ROUTE_APP[path] = app
    if home is not None:
        HOME_ROWS[app] = home
    if search_scope is not None:
        # one scope as (its name, its handler), or several by name, Idiograph's This case and This project
        SEARCH_SCOPES.update(search_scope if isinstance(search_scope, dict) else dict([search_scope]))
    if search_rows is not None:
        SEARCH_ROWS[app] = search_rows


def hooks(held: list, app: str | None = None) -> list:
    """The hooks of one kind, `held`, that a run of `app` calls, this run's by default: those of the apps it
    serves (`apps_served`), never another's (the family codebase's sixth build, 23 October 2026, as train 47
    keyed the starts): Sift's and Trace's servers read and save no setting of Idiograph's, ask no question
    of its projects, run no request in its scopes and hold no quit for its work."""
    served = apps_served(app)
    return [hook for owner, hook in held if owner in served]


def start_hooks(app: str | None = None) -> list:
    """The start hooks a run of `app` runs as it starts, this run's by default: those of the apps it serves
    (`hooks`), never another's. Idiograph's fills its demo, which Sift's and Trace's servers have no use for
    (23 October 2026)."""
    return hooks(STARTS, app)


@contextlib.contextmanager
def scoped(route: str | None, body):
    """A request run in every scope the apps set for their routes (see `register`): Idiograph's, a board at
    a timepoint, or a participant's LPETs, when the call names one. Any other request runs as it is."""
    with contextlib.ExitStack() as stack:
        for scope in hooks(SCOPES):
            stack.enter_context(scope(route, body))
        yield


def unplaced_routes() -> list[str]:
    """Each route ROUTES holds that ROUTE_APP gives no owner, and each two owners claimed, so a new route
    never goes unplaced."""
    return sorted({p for p in ROUTES if p not in ROUTE_APP} | set(CLAIMED_TWICE))


def routes_of(app: str) -> tuple:
    """The paths `app` answers of its own, or `shared` every app's, in the order they were placed."""
    return tuple(path for path, owner in ROUTE_APP.items() if owner == app)


def apps_served(app: str | None = None) -> tuple:
    """The apps whose routes this run answers: its own and those SERVES_TOO gives it."""
    name = app_identity.check(app or APP)
    return (name, *SERVES_TOO.get(name, ()))


def route_owner(path: str) -> str | None:
    """The app a route belongs to, `shared`, or None for a path the table does not hold. A Sift or Trace route
    a build without that app's module never registered is found in `app_identity.ROUTES`."""
    return ROUTE_APP.get(path) or app_identity.route_owner(path)


def not_here(path: str, app: str | None = None) -> dict | None:
    """The 404's body for another app's route, naming the app that has it, or None when this run
    answers it: a shared route, its own, one SERVES_TOO lets it answer, or a path of the page's."""
    owner = route_owner(path)
    if owner in (None, "shared") or owner in apps_served(app):
        return None
    them, us = app_identity.APPS[owner], app_identity.APPS[app_identity.check(app or APP)]
    return {"error": i18n.t("errors.other_apps", name=them['name'], name2=us['name']), "app": owner, "port": them["port"]}


# The Preview Edition (Adam, 21 October 2026): while this is True Idiograph's page carries
# data-edition="preview" on its root, which shows the Preview Edition stamp on Home's lockup, at the top of
# About and beside the mark on each bar. False when the preview ends, and the stamp goes everywhere at once.
# Sift and Trace never show it.
PREVIEW_EDITION = True


# The page's assembly (the family codebase's second build, 22 October 2026): the family's page, holds a slot
# where each app's part of it stands, `<!--slot:home-->`, and each app's own `static/<app>.html` holds its parts,
# each under a line `<!--part:home-->`, so the family's page names no app's markup or file. Each slot takes every
# app's part of its name in the family's order, and one no app fills is left out. The family's page is
# family/static/page.html since the fifth build (23 October 2026), static/index.html until then, a path the
# server still answers with it.
PAGE = "page.html"
SLOT = re.compile(r"^<!--slot:([a-z-]+)-->\n", re.M)
PART = re.compile(r"^<!--part:([a-z-]+)-->\n", re.M)


def page_parts(app: str | None = None) -> dict:
    """Each slot's markup from the parts of the apps a run of `app` serves, this run's by default, in the
    family's order of the apps, read afresh. Since the cutover (the sixth build, 23 October 2026) that is the
    app's own alone, so Idiograph's page carries none of Sift's or Trace's."""
    served = apps_served(app)
    out: dict = {}
    for own in (a for a in boot.APPS if a in served):
        found = static_file(f"{own}.html", app)
        if found is None:
            continue
        pieces = PART.split(found.read_text(encoding="utf-8"))
        for name, text in zip(pieces[1::2], pieces[2::2]):
            out[name] = out.get(name, "") + text
    return out


def assembled(page: str, app: str | None = None) -> str:
    """A page of the family's with each slot filled by the parts of the apps a run of `app` serves, this
    run's by default (see `page_parts`), and then its words: each `{{key}}` marker the message in the chosen
    language and the catalogue for the scripts where `<!--i18n-->` stands (`i18n.fill`, 28 October 2026)."""
    parts = page_parts(app)
    page = SLOT.sub(lambda m: parts.get(m.group(1), ""), page)
    name = app_identity.APPS[app_identity.check(app or APP)]["name"]
    return i18n.fill(page, page_language(), boot.roots(apps_served(app)), {"app": name})


def page_language() -> str:
    """The language the page and the server's lines are in: `language` in the settings, a tag such as `es` or
    `en-US`, or the computer's own when that is unset (i18n.chosen), set by Settings' Language row. It is read
    afresh for each page, so a page loaded after the row is ticked is in the new language."""
    return i18n.chosen(config())


# the text layer reads the run's language and its catalogue's folders, those of the apps this run serves and
# the family's, from here
i18n.LANGUAGE = page_language
i18n.ROOTS = lambda: boot.roots(apps_served())
# and the formats its settings choose, read afresh for each page as the language is (fmtcore)
i18n.CHOSEN_FORMATS = lambda: config().get("formats")


def own_page(page: str, app: str | None = None) -> str:
    """The one page as this app's (the split's third build): `data-app` on its root naming the app, which
    shows that app's screens, Settings and Search alone, and its title the app's name. Idiograph's root also
    says data-edition="preview" while PREVIEW_EDITION is on."""
    name = app_identity.check(app or APP)
    edition = ' data-edition="preview"' if PREVIEW_EDITION and name == "idiograph" else ""
    # the page's language the locale its words are in (i18n.locale_of), en-GB for English
    lang = i18n.locale_of(page_language(), boot.roots(apps_served(name)))
    page = page.replace('<html lang="en-GB" data-theme="auto">',
                        f'<html lang="{lang}" data-theme="auto" data-app="{name}"{edition}>', 1)
    return page.replace("<title>Idiograph</title>", f"<title>{app_identity.APPS[name]['name']}</title>", 1)


class AppServer(ThreadingHTTPServer):
    """The app's server, its queue of connections waiting to be taken 128 long, where the standard
    library's 5 let Windows refuse outright the burst of requests a page's reload makes, two windows
    reloading at once after a Restart among them, so a page came back with neither its script nor its
    marks (17 October, the third Tauri build's third and fourth Windows runs). A Mac and Linux wait
    for room, and Windows refuses."""
    request_queue_size = 128

    def server_bind(self):
        """The socket bound as the standard library binds it, without its lookup of this computer's own
        name (`socket.getfqdn`), which nothing in the app reads. Where a reverse lookup of 127.0.0.1 goes
        unanswered, that lookup held the start for half a minute before the server took a connection,
        as on GitHub's Mac for every real server the suite starts (7 November 2026)."""
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[:2]


class Handler(BaseHTTPRequestHandler):
    server_version = "ESHelper"

    def log_message(self, fmt, *args):
        """The request line only, and for the key routes not even that beyond the path.

        `BaseHTTPRequestHandler` never logs a body, and this makes sure nothing ever does: a line
        about `/api/key` is replaced by one that says the body was not looked at.
        """
        if "--verbose" not in sys.argv:
            return
        line = fmt % args
        if any(route in line for route in SILENT):
            path = urlparse(getattr(self, "path", "") or "").path
            line = f"{getattr(self, 'command', '?')} {path} (the body is never logged)"
        sys.stderr.write("  %s\n" % line)

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        try:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            # the page let the request go before the answer reached it, as on Windows when a Restart
            # ends this server under a request still open, which is no error of the server's (17 October)
            self.close_connection = True

    def _json(self, data, code: int = 200) -> None:
        self._send(code, json.dumps(data, ensure_ascii=False, default=str).encode("utf-8"),
                   "application/json; charset=utf-8")

    @in_use
    def do_GET(self):
        url = urlparse(self.path)
        if not own_origin(self.headers, self.server.server_address):
            return self._json({"error": named(i18n.t("errors.own_page_ask"))}, 403)
        # another app's route, named (see `not_here`)
        refused = not_here(url.path)
        if refused:
            return self._json(refused, 404)
        # an app's path that answers through the handler itself, Idiograph's recording and its sent project
        if url.path in STREAMS:
            return STREAMS[url.path](self, {k: v[0] for k, v in parse_qs(url.query).items()})
        if url.path in GET_PATHS:
            return self._send(*GET_PATHS[url.path]({k: v[0] for k, v in parse_qs(url.query).items()}))
        if url.path.startswith("/api/"):
            handler = ROUTES.get(url.path)
            if not handler:
                return self._json({"error": i18n.t("errors.such_endpoint"), "code": "no_endpoint"}, 404)
            if url.path in POST_ONLY:
                return self._json({"error": i18n.t("errors.endpoint_takes_post")}, 405)
            query = {k: v[0] for k, v in parse_qs(url.query).items()}
            if window_only(url.path, query) and not keyed(self.headers):
                return self._json({"error": named(i18n.t("errors.window_only"))}, 403)
            return self._run(handler, query, url.path)
        if url.path == FAVICON_PATH:
            return self._send(200, favicon_png(), "image/png")
        if url.path == LICENCE_PATH:
            if not LICENCE_FILE.is_file():
                return self._send(404, b"The licence is not in this copy.", "text/plain; charset=utf-8")
            return self._send(200, LICENCE_FILE.read_bytes(), "text/plain; charset=utf-8")
        if url.path == MANUAL_PATH:
            code, page = manual_page()
            return self._send(code, own_margins(beating(page)).encode("utf-8"), "text/html; charset=utf-8")
        if url.path == TRANSLATING_PATH:
            code, page = translating_page()
            return self._send(code, own_margins(beating(page)).encode("utf-8"), "text/html; charset=utf-8")
        name = (PAGE if url.path in ("/", "", "/index.html") else DESIGN_PAGE if url.path == DESIGN_PATH
                else url.path.lstrip("/"))
        target = static_file(name)
        if target is None:
            return self._send(404, b"Not found", "text/plain; charset=utf-8")
        ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype.endswith("javascript"):
            ctype += "; charset=utf-8"
        if name == PAGE:
            return self._send(200, keyed_page(own_page(assembled(target.read_text(encoding="utf-8")))).encode("utf-8"),
                              ctype)
        if name == DESIGN_PAGE:
            return self._send(200, assembled(target.read_text(encoding="utf-8")).encode("utf-8"), ctype)
        return self._send(200, target.read_bytes(), ctype)

    @in_use
    def do_POST(self):
        url = urlparse(self.path)
        if not own_origin(self.headers, self.server.server_address):
            return self._json({"error": named(i18n.t("errors.own_page_ask"))}, 403)
        refused = not_here(url.path)
        if refused:
            return self._json(refused, 404)
        handler = ROUTES.get(url.path)
        if not handler:
            return self._json({"error": i18n.t("errors.such_endpoint"), "code": "no_endpoint"}, 404)
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return self._json({"error": i18n.t("errors.request_valid_json")}, 400)
        # what governs agents, from the app's own window alone, never another program on this machine
        if window_only(url.path, body) and not keyed(self.headers):
            return self._json({"error": named(i18n.t("errors.window_only"))}, 403)
        if url.path in OWN_PAGE and not own_origin(self.headers, self.server.server_address):
            return self._json({"error": named(i18n.t("errors.own_page_only"))}, 403)
        if url.path == SERVER_PATH:
            return self._server_op(body if isinstance(body, dict) else {})
        return self._run(handler, body, url.path)

    def _server_op(self, body: dict):
        """Restart or Quit: refused on a way of running that cannot restart itself, and while a write
        is still under way, then answered, and the serving stopped from another thread, since
        `shutdown` waits for the loop this request came through. `main` does the rest (see `finish`)."""
        op = body.get("op")
        if op not in SERVER_OPS:
            return self._json({"error": i18n.t("errors.op_restart_quit")}, 400)
        blocked = restart_blocked() if op == "restart" else None
        if blocked:
            return self._json({"error": blocked}, 409)
        if not quiet():
            return self._json({"error": named(i18n.t("errors.write_still_under_way_did"), op=op)}, 409)
        self._json(dict(server_state(), op=op))
        try:
            self.wfile.flush()
        except OSError:
            pass
        SERVER_STATE["op"] = op
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def _run(self, handler, body, route=None):
        try:
            # in the scope an app sets for it, a board at a timepoint, or a participant's LPETs, when the
            # call names one (21 October, see `scoped`)
            with scoped(route, body):
                result = handler(body)
        except OutsideRoot as exc:
            return self._json({"error": str(exc)}, 403)
        except WorkbookError as exc:
            # its words, and its code beside them for the page to test (errors.CODES, 31 October 2026)
            return self._json(refusal(exc), 409)
        except KeyError as exc:
            return self._json({"error": i18n.t("errors.missing_field", exc=exc)}, 400)
        except FileNotFoundError as exc:
            return self._json({"error": i18n.t("errors.file_found", exc=exc)}, 404)
        except Exception as exc:                      # surfaced in the interface, not swallowed
            import traceback
            traceback.print_exc()
            return self._json({"error": i18n.t("errors.unexpected", kind=type(exc).__name__, exc=exc)}, 500)
        code = result.pop("status", 200) if isinstance(result, dict) else 200
        return self._json(result, code)


def start_up(args) -> None:
    """Everything `main` does before it serves, for the app `args.app` names: its folders and files, the
    settings file a run with `--config` names, the one project of a run with `--root`, the data folder
    readied (`first_run`), the shipped settings where there are none, Sift's or Trace's first start, and
    then the start hooks of the apps this run serves alone (`start_hooks`, 23 October 2026). Every app's
    module registers in every app's server, a frozen one above all, so a hook of Idiograph's run in Sift's
    server wrote Idiograph's demo into Sift's data folder."""
    global CONFIG_PATH, STATE_PATH
    # the app first, since its folders and files are where everything below reads and writes
    use_app(args.app or APP)
    if args.config:
        CONFIG_PATH = Path(args.config).expanduser().resolve()
        # its recent list beside that file, never the one in daily use (21 October)
        STATE_PATH = state_beside(CONFIG_PATH)
    if args.root:
        global ROOT_OVERRIDE, STATE_MEMORY
        ROOT_OVERRIDE = args.root
        # empty at a first start, and after a restart the list the run held (17 October, later)
        STATE_MEMORY = carried_state()

    first_run(PATHS, CONFIG_PATH)
    # A downloaded copy carries no config.json, which holds one machine's projects, so its first run
    # writes the defaults with no project, the settings the Mac app ships
    if not CONFIG_PATH.exists():
        save_json(CONFIG_PATH, shipped_config())
    # Sift's or Trace's first start takes what it shares with Idiograph from Idiograph's files, once
    if APP != app_identity.DEFAULT:
        first_start_copy()
    # the start of each app this run serves (see `register`): Idiograph's fills the demo's missing sidecars,
    # which a trial run with --root leaves as it finds them, and takes up the list of the files it wrote
    for start in start_hooks():
        start(bool(args.root))


def main() -> None:
    ap = argparse.ArgumentParser(description="Idiograph, a local writing surface for experiential statements.")
    ap.add_argument("--app", default=None, choices=list(app_identity.APPS),
                    help="which of the three apps this run is, idiograph by default, sift or trace")
    ap.add_argument("--port", type=int, default=None, help="the app's own port by default, 8765 for idiograph, "
                                                           "8766 for sift, 8767 for trace")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--root", help="a run of this one project, its root absolute or relative to the repo "
                                   "root. It is not written to config.json.")
    ap.add_argument("--config", help="a settings file for this run, read and written in place of "
                                     "config.json, its recent list beside it, so a trial or smoke server "
                                     "never saves over either.")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    # its lines in UTF-8 to a pipe or a log, whatever the system's code page
    app_folders.utf8_streams()
    # the window's key, or one of this run's own for a page in a browser (see `take_window_key`)
    take_window_key()
    start_up(args)
    if args.port is None:
        args.port = IDENTITY["port"]
    global ARGV
    # the file as it was run, from the folder it was run in, for a restart (see `relaunch`)
    head = sys.argv[0] if sys.argv else ""
    ARGV = [head if FROZEN else os.path.abspath(head), *sys.argv[1:]]

    server = AppServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"{IDENTITY['name']} is running at {url}")
    roots = project_roots()
    for root in roots:
        print(f"Participants under: {display_path(rel_path(root))}")
    if not roots:
        print("No project folder chosen yet.")
    print("Stop it with Control-C.")
    # a restart reloads the page that asked for it, so it opens no second tab
    if not args.no_browser and not os.environ.get(RESTARTED):
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    # it quits by itself a few minutes after its last tab closes, with the tick on (see `idle_quit`)
    watch_idle(server)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        if SERVER_STATE["op"]:
            # Restart and Quit close the socket at once and wait for the writes in hand alone,
            # never for a request still open, such as a browser's idle connection
            server.socket.close()
        else:
            server.server_close()
    if SERVER_STATE["op"]:
        finish(SERVER_STATE["op"], args.port)


# each app's routes registered, Idiograph's from apps/idiograph/idiograph_routes.py, Sift's from
# apps/sift/sift_routes.py and Trace's from apps/trace/trace_routes.py, each imported by its name (see
# `register`). The root's server.py runs `main` (see `boot.shim`)
boot.load("routes")


def __getattr__(name: str) -> str:
    """The refusals other modules and the checks name as this module's, each read in the run's language when
    asked for (the text layer, 28 October 2026)."""
    said = {
        "NOT_OURS": lambda: i18n.t("errors.own_page_only"),
        "ELSEWHERE": lambda: i18n.t("errors.own_page_ask"),
        "WINDOWS_LINE": lambda: i18n.t("errors.cannot_restart_itself_windows_close"),
        "QUIT_LINE": lambda: i18n.t("errors.tab_been_open_few_minutes"),
        "CLOSED_LINE": lambda: i18n.t("errors.closed"),
        "NO_MANUAL": lambda: i18n.t("errors.manual_copy"),
        "NO_DIALOG": lambda: i18n.t("errors.folder_dialog_mac_only_type"),
        "NO_FILE_DIALOG": lambda: i18n.t("errors.file_dialog_mac_only_type"),
    }
    if name in said:
        return said[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
