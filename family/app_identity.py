"""Which of the family's three apps this run is, Idiograph, Sift or Trace, the one place that decides.

One codebase serves three apps (Adam, 20 October 2026: Idiograph the IPA app, Sift and Trace apps of
their own, each released when it changed). A run is one of them, chosen by `--app` on `server.py`,
`cli.py` and `mcp_server.py`, Idiograph when it is left out, and in a frozen build by the launcher's
own name, `Sift.exe` or `Sift.app`'s executable. Each app has its name, its bundle id, its data folder,
its port, its mark, its colour token, its What's new file, its update endpoint and its version, the
last from `versions.json` at the root, so a bump stays one edit.

From source Idiograph reads `config.json` and `state.json` beside the code as always, and Sift reads
`config.sift.json` and `state.sift.json` beside them, Trace `config.trace.json` and `state.trace.json`.
Frozen, each has its own data folder, `Application Support/Sift` beside `Application Support/Idiograph`
(`%APPDATA%\\Sift` on Windows), which `app_folders.folders` gives.

The first start of Sift or Trace copies from Idiograph's files what that app shares with it (see
`first_start_plan`), only reading them, once, a marker in the new app's own settings saying so. The
key stays in the keychain under one name, so all three see it.

The standard library only, so a launcher reads it before anything else is loaded.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import boot

VERSIONS_FILE = boot.resource("versions.json")
DEFAULT = "idiograph"

APPS: dict[str, dict] = {
    "idiograph": {"name": "Idiograph", "bundle_id": "uk.co.adamknowles.idiograph", "folder": "Idiograph",
                  "port": 8765, "mark": "idiograph", "colour": "--part-distil", "whats_new": "whats-new.md", "manual": "manual.md",
                  "agents": "agents.md", "releases": "Pharkie/idiograph"},
    "sift": {"name": "Sift", "bundle_id": "uk.co.adamknowles.sift", "folder": "Sift",
             "port": 8766, "mark": "sift", "colour": "--part-sift", "whats_new": "whats-new-sift.md", "manual": "manual-sift.md",
             "agents": "agents-sift.md", "releases": "Pharkie/sift-releases"},
    "trace": {"name": "Trace", "bundle_id": "uk.co.adamknowles.trace", "folder": "Trace",
              "port": 8767, "mark": "trace", "colour": "--part-trace", "whats_new": "whats-new-trace.md", "manual": "manual-trace.md",
              "agents": "agents-trace.md", "releases": "Pharkie/trace-releases"},
}
# Each app's one line, as the other two apps' Homes name it at their foot (the split's third build, 20
# October 2026, drawings 1 to 3 of the plan Adam accepted), the English. Home shows it from the catalogue,
# `shell.family.line.<app>` (i18nleft4, `server.family_line`)
APPS["idiograph"]["line"] = "Interpretative Phenomenological Analysis: statements, PETs and GETs"
APPS["sift"]["line"] = "Screening for a systematic review, by PRISMA 2020"
APPS["trace"]["line"] = "Each claim a manuscript makes, held against its reference"
for _key, _app in APPS.items():
    _app["id"] = _key
    _app["endpoint"] = f"https://github.com/{_app['releases']}/releases/latest/download/latest.json"
# Each app's entry, the module a frozen launcher imports by its name to run the app's server (the family
# codebase's second build, 22 October 2026): Trace's own, apps/trace/trace_main.py, since the third build
# Sift's, apps/sift/sift_main.py, and since the fourth Idiograph's, apps/idiograph/idiograph_main.py, each of
# which registers its routes and runs the family's server
ENTRIES = {"idiograph": "idiograph_main", "sift": "sift_main", "trace": "trace_main"}


# Each app's own files beside its code, by their paths from the root as the code reads them and a bundle carries
# them (the family codebase's sixth build, 23 October 2026), so each app's build ships the family's and its own
# alone: Idiograph's guidance, its transcript template, its demo and its guide's schemas, Sift's Mermaid, which
# draws its PRISMA flow, and with each app's docs from `docs` below, its guide for agents, its manual and its
# What's new. A file in apps/<app>/ is that app's by its folder, as well as by this table. The family's are
# every app's: the licence, the notice of third-party software and the versions.
FILES = {
    "family": ("LICENSE", "NOTICE.md", "versions.json", "docs/translating.md"),
    "idiograph": ("guidance.md", "pet_guidance.md", "themes_guidance.md", "ta_guidance.md", "ta_themes_guidance.md",
                  "template/Transcript template.xlsx", "demo", "docs/schemas", "team_words.txt", "typst"),
    "sift": ("static/vendor/mermaid.min.js", "static/vendor/LICENSE-mermaid.txt"),
    "trace": (),
}
# each app's docs by their keys in APPS: its guide for agents, its manual and its What's new
DOCS = ("agents", "manual", "whats_new")


def docs(app: str | None = None) -> tuple:
    """The app's docs by their paths from the root, `docs/agents-sift.md`, `docs/manual-sift.md` and
    `docs/whats-new-sift.md` for Sift."""
    name = check(app)
    return tuple(f"docs/{APPS[name][key]}" for key in DOCS)


def files(app: str) -> tuple:
    """`app`'s own files beside its code (see FILES), its docs among them, or the family's for "family"."""
    return FILES["family"] if app == "family" else FILES[check(app)] + docs(app)


def owner_of_file(path: str) -> str | None:
    """Whose a file beside the code is by its path from the root, the family's or an app's, by its folder or by
    FILES, a file inside a folder FILES names among it, or None for one no table holds."""
    parts = Path(path).parts
    if parts and parts[0] == "family":
        return "family"
    if len(parts) > 2 and parts[0] == "apps" and parts[1] in APPS:
        return parts[1]
    for owner in ("family", *APPS):
        for own in files(owner):
            if Path(path) == Path(own) or Path(own) in Path(path).parents:
                return owner
    return None


def entry(app: str | None = None) -> str:
    """The module that runs `app`'s server, by its name, for a launcher to import as a string."""
    return ENTRIES.get(check(app), "server")


# the family's three ports, which a fallback from a held port never takes for another app
FAMILY_PORTS = tuple(app["port"] for app in APPS.values())

# The apps whose routes, commands and MCP tools an app answers beside its own. Until the cutover
# Idiograph answered Sift's and Trace's as before the split, the page on 8765, `idiograph sift` and
# `idiograph trace` on the command line and their tools on Idiograph's MCP server. The cutover (the family
# codebase's sixth build, 23 October 2026, once the review's session had moved to Sift's own app) set
# Idiograph's to (), so each app answers its own alone and refuses another's by name. The server's routes
# (`server.SERVES_TOO`), the command line and the MCP server all read it here.
SERVES_TOO = {"idiograph": (), "sift": (), "trace": ()}
# Sift's and Trace's routes by their paths, so a server whose build ships neither app's module, Idiograph's
# since the sixth build, still refuses them naming the app that has them (land6, 23 October 2026). Each app's
# routes module registers them as ever, and the suite holds this table to what they register (area 222).
ROUTES = {"sift": ("/api/sift", "/api/sift-search", "/api/sift-review", "/api/databases", "/api/zotero", "/sift/pdf"),
          "trace": ("/api/trace", "/api/trace-project", "/trace/pdf")}


def route_owner(path: str) -> str | None:
    """The app of ROUTES whose route `path` is, or None."""
    return next((app for app, paths in ROUTES.items() if path in paths), None)


def served(app: str | None = None) -> tuple:
    """The apps whose routes, commands and tools `app` answers: its own first, then those SERVES_TOO
    gives it."""
    name = check(app)
    return (name, *SERVES_TOO.get(name, ()))


# The other apps each app names to the person using it, at its Home's foot, in Open and Download and in its
# command line's refusals (nosiftrace, Adam, 12 November 2026: Sift and Trace are early apps, for the maintainer
# alone). Idiograph names neither, so its Home ends with its own projects. Sift's and Trace's own builds name the
# family as before.
NAMES = {"idiograph": (), "sift": ("idiograph", "trace"), "trace": ("idiograph", "sift")}


def names(app: str | None = None) -> tuple:
    """The other apps `app` names to its user, in the family's order (see NAMES)."""
    return NAMES.get(check(app), ())

# The settings Sift and Trace share with Idiograph, copied on their first start: the AI settings, the
# appearance where a file keeps it, Celebrations and its Sound, and the closing tick at the end of General
SHARED_SETTINGS = ("ai_suggest", "ai_provider", "model", "local_url", "local_model", "ai_address",
                   "lmstudio_url", "ai_deployment", "ai_api_version", "other_model", "ai_models", "appearance",
                   "celebrations", "celebration_screens", "sound", "quit_when_closed")
OWN_SETTINGS = {"idiograph": (), "sift": ("databases", "sift_email", "zotero"), "trace": ()}
# the lists in the state file each takes: Sift's projects, each with the run it had open, under the
# name they have now and the two before it, and Trace's projects
OWN_STATE = {"idiograph": (), "sift": ("sift_reviews", "sift", "sift_searches"), "trace": ("trace_projects",)}
# the marker in the new app's own settings that its first start has copied from Idiograph's files
MARKER = "first_start_copied"

# Each app's AI features, each with its own switch under AI features in that app's Settings (Adam, 20
# October 2026), every one on while the app's AI features switch is, until it is turned off. The
# settings keep the ones turned off, `ai_features_off`, so a new feature starts on.
AI_FEATURES = {
    "idiograph": ("statements", "pets", "gets"),
    "sift": ("proposals",),
    "trace": ("passages",),
}
AI_OFF_KEY = "ai_features_off"


def ai_feature_on(cfg: dict, feature: str) -> bool:
    """Whether one AI feature is on: the app's AI features switch on, and the feature's own not turned off."""
    if not (cfg or {}).get("ai_suggest"):
        return False
    off = (cfg or {}).get(AI_OFF_KEY)
    return not (isinstance(off, list) and feature in off)


def clean_ai_off(value) -> list[str]:
    """The features turned off as a save sends them, only the family's own names, each once, in order."""
    known = [f for features in AI_FEATURES.values() for f in features]
    if not isinstance(value, (list, tuple)):
        return []
    return [f for f in known if f in value]


class UnknownApp(ValueError):
    pass


def check(app: str | None) -> str:
    """`app` as one of the three, Idiograph when it is None or empty. Anything else is refused."""
    name = (app or DEFAULT).strip().lower()
    if name not in APPS:
        raise UnknownApp(f"There is no app called {app}. The apps are {', '.join(APPS)}.")
    return name


def identity(app: str | None = None) -> dict:
    """The app's identity, with its version."""
    name = check(app)
    return dict(APPS[name], version=version(name))


def from_executable(path: str | None = None) -> str:
    """The app a frozen build is, by its executable's name: `Sift.exe`, `Sift-console.exe` or the
    `Sift` inside `Sift.app` is Sift, and any other name, `Idiograph Test` among them, Idiograph."""
    stem = Path(path if path is not None else sys.executable).name.lower()
    for suffix in (".exe",):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    stem = stem.removesuffix("-console")
    return stem if stem in APPS else DEFAULT


def chosen(argv: list[str] | None = None, frozen: bool | None = None, executable: str | None = None) -> str:
    """The app this run is: `--app NAME` or `--app=NAME` in `argv`, else the frozen launcher's name,
    else Idiograph. An app name that is none of the three is refused."""
    named = asked(sys.argv[1:] if argv is None else argv)
    if named:
        return named
    frozen = bool(getattr(sys, "frozen", False)) if frozen is None else frozen
    return from_executable(executable) if frozen else DEFAULT


def asked(argv: list[str]) -> str | None:
    """The app `--app NAME` or `--app=NAME` names in `argv`, or None when it names none."""
    args = list(argv)
    for i, arg in enumerate(args):
        if arg == "--app" and i + 1 < len(args):
            return check(args[i + 1])
        if arg.startswith("--app="):
            return check(arg.split("=", 1)[1])
    return None


def strip_app(argv: list[str]) -> list[str]:
    """`argv` without its `--app` and the name after it, for a parser that does not know it."""
    out, skip = [], False
    for arg in argv:
        if skip:
            skip = False
        elif arg == "--app":
            skip = True
        elif not arg.startswith("--app="):
            out.append(arg)
    return out


def versions(path: Path | None = None) -> dict[str, str]:
    """Every app's version, from versions.json."""
    data = json.loads(Path(path or VERSIONS_FILE).read_text(encoding="utf-8"))
    return {name: str(data[name]) for name in APPS if name in data}


def version(app: str | None = None, path: Path | None = None) -> str:
    """The app's version, from versions.json, the one place each reader takes it from."""
    name = check(app)
    held = versions(path)
    if name not in held:
        raise SystemExit(f"versions.json has no version for {name}.")
    return held[name]


# the file a build made on Adam's Mac carries beside the code, naming the commit it was built from (macdaily,
# 9 November 2026). A release and a run from source have none
BUILD_FILE = "build.json"


def build(path: Path | None = None) -> str:
    """The short commit a daily build of the app was made from, from `build.json` in the bundle, so a copy
    built on the Mac each day is told apart from the week's release of the same version. Empty for a
    release, a run from source and a file that cannot be read."""
    if path is None:
        if not boot.FROZEN:
            return ""
        path = boot.ROOT / BUILD_FILE
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    sha = str(data.get("build") or "") if isinstance(data, dict) else ""
    return sha if sha.isalnum() and len(sha) <= 40 else ""


def file_names(app: str | None = None) -> dict[str, str]:
    """The settings and recent-list files' names run from source: `config.json` and `state.json` for
    Idiograph, `config.sift.json` and `state.sift.json` for Sift, and the same for Trace."""
    name = check(app)
    if name == DEFAULT:
        return {"config": "config.json", "state": "state.json"}
    return {"config": f"config.{name}.json", "state": f"state.{name}.json"}


def fallback_ports(first: int, span: int, app: str | None = None):
    """The ports a launcher tries, `first` and the `span` after it, without the family's other apps'
    ports, so Idiograph's server, its own port held, never takes Sift's or Trace's. The first port
    asked for is always tried, whichever it is."""
    for p in range(first, first + span + 1):
        if p == first or p not in FAMILY_PORTS:
            yield p


def _absolute(entry: dict, base: Path | None) -> dict:
    """A list entry whose `folder` is from Idiograph's base, made whole, where the new app's base is
    another folder, so the copy finds the same folder."""
    folder = entry.get("folder")
    if base is None or not isinstance(folder, str) or not folder or Path(folder).is_absolute():
        return entry
    return dict(entry, folder=str(Path(base) / folder))


def first_start_plan(app: str, own_config: dict, from_config: dict, own_state: dict, from_state: dict,
                     from_base: Path | None = None, own_base: Path | None = None) -> tuple[dict, dict] | None:
    """What the first start of Sift or Trace takes from Idiograph's settings and recent list, as the
    new settings and the new list, or None when there is nothing to do: Idiograph itself, or an app
    whose settings carry the marker. Before the marker the new app's file holds at most the settings
    it ships with, so Idiograph's take their place. Nothing here writes, and the dicts given are never
    changed."""
    name = check(app)
    if name == DEFAULT or own_config.get(MARKER):
        return None
    config = dict(own_config)
    for key in SHARED_SETTINGS + OWN_SETTINGS[name]:
        if key in from_config:
            config[key] = json.loads(json.dumps(from_config[key]))
    state = dict(own_state)
    moved = from_base is not None and own_base is not None and Path(from_base) != Path(own_base)
    for key in OWN_STATE[name]:
        if key in from_state:
            held = json.loads(json.dumps(from_state[key]))
            if moved and isinstance(held, list):
                held = [_absolute(e, from_base) if isinstance(e, dict) else e for e in held]
            state[key] = held
    config[MARKER] = {"from": DEFAULT}
    return config, state
