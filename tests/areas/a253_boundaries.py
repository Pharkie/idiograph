"""The family's boundaries (22 October 2026, the family codebase's first build).

The codebase is one family of three apps, `family/` what all share and `apps/<app>/` each app's own
(boot.py). The family never reaches into an app, nor one app into another. Each place it does today is
a crossing, counted here from every tracked file, and kept in `tests/boundaries.json`, the baseline,
which may only go down: a crossing not in it fails, and one it holds that has gone fails too, until the
baseline is written again with `python3 tests/areas/a253_boundaries.py --write`.

- Python: each import (`import`, `from`, and `importlib.import_module` or `__import__` with a string)
  resolved to its module's owner. The family importing an app's module, or one app another's, is a
  crossing. tests/ and packaging/ are free.
- The page: a script naming a top-level name only another owner's scripts define (the family's an
  app's, or one app's another's), a property after a dot, an object literal's key and a name the script
  binds of its own passed over, a script calling another app's route (`/api/sift` in trace.js), and
  a page's `src` or `href` loading another app's file.

A file's owner is its folder, family/ or apps/<app>/, and for a file still at the root the baseline's
`owners` table, which every tracked module and page file must be in. The mixed ones, app.js among them,
were the family's until they were split, so what of an app's they reached was counted. Each build that moved
or cut lowered the count, and builds 4 and 5 made it 0. Since the fourth build (22 October 2026) Python's
is 0 and strict, and since the fifth (23 October 2026) the page's too: any crossing at all fails, whatever
the baseline holds.

The bundles: `build_mac.py --list` for each app, each module, page file, data file, doc and the demo
whose owner is another app counted, a number per app that went down to 0 with the sixth build (23 October
2026), when each app's bundle came to carry the family's and its own alone, and is strict since: anything of
another app's in any bundle fails, the owner of a file beside the code taken from `app_identity.FILES`. And
every entry starts under `python -I` from a folder of its own, so none leans on the folder it is run from to
find the family's modules.

Only the standard library at the top: run as a script it writes the baseline.
"""
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parents[2]
BASELINE = TOOL / "tests" / "boundaries.json"
APPS = ("idiograph", "sift", "trace")
FREE = ("tests/", "packaging/", "feedback-worker/")
# the entries every run starts from, each asked for its --help (or --list) under `python -I`
ENTRIES = (("server.py", "--help"), ("cli.py", "--help"), ("mcp_server.py", "--help"), ("apps/idiograph/make_demo.py", "--help"),
           ("apps/sift/make_world.py", "--help"), ("wipe_draft.py", "--help"), ("family/make_app.py", "--help"),
           ("packaging/release.py", "--help"), ("packaging/tauri/make_icons.py", "--help"),
           ("packaging/build_mac.py", "--scripts"), ("packaging/build_windows.py", "--help"),
           ("apps/trace/trace_main.py", "--help"), ("apps/sift/sift_main.py", "--help"),
           ("apps/idiograph/idiograph_main.py", "--help"))
JS_TOP = re.compile(r"^(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)|^(?:const|let|var|class)\s+([A-Za-z_$][\w$]*)")
WORD = re.compile(r"[A-Za-z_$][\w$]*")
LOADS = re.compile(r'\b(?:src|href)="/?([^"#?:]+)"')
ROUTE = re.compile(r"['\"`](/[A-Za-z0-9_\-/.]+)")


# what a walk of a folder with no git leaves out: git's own, the first run's venv, a build's folders, caches
LEFT_OUT = {".git", ".venv", ".venv-setup", "build", "dist", "__pycache__", "node_modules"}


def tracked() -> list[str]:
    """Every file git keeps or would keep, tracked or new and not ignored, by its path from the root.
    Where git cannot say, as in the gate's snapshot, which is a copy of the tracked files with no .git
    of its own (train 40, 22 October: every crossing went unseen there), every file under the root but
    those in LEFT_OUT."""
    alone = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    try:
        out = subprocess.run(["git", "-c", "core.quotepath=off", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                             cwd=TOOL, capture_output=True, timeout=60, env=dict(alone, GIT_OPTIONAL_LOCKS="0"))
        listed = out.stdout.decode("utf-8") if out.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        listed = ""
    if listed:
        return sorted(p for p in listed.split("\0") if p and (TOOL / p).is_file())
    return sorted(p.relative_to(TOOL).as_posix() for p in TOOL.rglob("*")
                  if p.is_file() and not LEFT_OUT & set(p.relative_to(TOOL).parts))


def owner_of(path: str, owners: dict) -> str | None:
    """A file's owner: family/ the family's, apps/<app>/ that app's, else the owners table's."""
    parts = Path(path).parts
    if parts[0] == "family":
        return "family"
    if parts[0] == "apps" and len(parts) > 2 and parts[1] in APPS:
        return parts[1]
    return owners.get(path)


def is_code(path: str) -> bool:
    """A module or a page file the boundaries are drawn between: a .py at the root, in family/ or an
    app's folder, and a file of the page under a static/ folder."""
    parts = Path(path).parts
    if path.endswith(".py"):
        return len(parts) == 1 or parts[0] == "family" or (parts[0] == "apps" and len(parts) > 2)
    return "static" in parts and not path.startswith(FREE)


def imported(tree: ast.AST) -> set[str]:
    """The top-level names of every module a Python file imports, a string import's among them."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
        elif (isinstance(node, ast.Call) and node.args and isinstance(node.args[0], ast.Constant)
              and isinstance(node.args[0].value, str)
              and ((isinstance(node.func, ast.Attribute) and node.func.attr == "import_module")
                   or (isinstance(node.func, ast.Name) and node.func.id in ("__import__", "import_module")))):
            names.add(node.args[0].value.split(".")[0])
    return names


def script_code(text: str) -> str:
    """A script's code with its comments and its strings blanked, the code inside a template's ${} kept."""
    out, i, n, stack = [], 0, len(text), []
    while i < n:
        c = text[i]
        if stack and stack[-1] == "`":
            if c == "\\":
                out.append("  ")
                i += 2
                continue
            if c == "`":
                stack.pop()
                out.append(" ")
            elif text.startswith("${", i):
                stack.append("{")
                out.append("  ")
                i += 2
                continue
            else:
                out.append("\n" if c == "\n" else " ")
            i += 1
            continue
        if text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(re.sub(r"[^\n]", " ", text[i:j]))
            i = j
            continue
        if c in "'\"":
            j = i + 1
            while j < n and text[j] != c and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            out.append(" " * (min(j + 1, n) - i))
            i = j + 1
            continue
        if c == "`":
            stack.append("`")
            out.append(" ")
        elif c == "{" and stack:
            stack.append("{")
            out.append(c)
        elif c == "}" and stack and stack[-1] == "{":
            stack.pop()
            out.append(" " if stack and stack[-1] == "`" else c)
        else:
            out.append(c)
        i += 1
    return "".join(out)


# the names a script binds of its own, which shadow any other script's of the same name: a const, let or var,
# a function and its parameters, an arrow's parameters and a catch's (the family codebase's fifth build, 23
# October 2026, when Distil's 700 names left the family's script and Sift's `const move` and Trace's `project`
# argument named none of them)
BINDS = (re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)"),
         re.compile(r"\b([A-Za-z_$][\w$]*)\s*=>"),
         re.compile(r"\bcatch\s*\(\s*([A-Za-z_$][\w$]*)"))
BIND_LISTS = (re.compile(r"\b(?:const|let|var)\s*[\[{]([^=;]*)[\]}]\s*="),
              re.compile(r"\bfunction\s*\*?\s*[A-Za-z_$]?[\w$]*\s*\(([^)]*)\)"),
              re.compile(r"\(([^()]*)\)\s*=>"))


def bound(text: str) -> set[str]:
    """The names a script's code binds of its own (see BINDS)."""
    names = {m.group(1) for rx in BINDS for m in rx.finditer(text)}
    for rx in BIND_LISTS:
        for m in rx.finditer(text):
            names.update(n for n in WORD.findall(re.sub(r"=[^,]*", "", m.group(1))) if n not in ("const", "let", "var"))
    return names


def named(text: str) -> set[str]:
    """The names a script's code uses, leaving out a property after a dot (`TH.mode`), an object literal's key
    (`{ current: 1 }`) and every name the script binds of its own (see `bound`)."""
    out = set()
    for m in WORD.finditer(text):
        before = text[max(0, m.start() - 400):m.start()].rstrip()
        if before.endswith(".") and not before.endswith("..."):
            continue
        after = text[m.end():m.end() + 8].lstrip(" \t")
        if after.startswith(":") and not after.startswith("::") and (not before or before[-1] in "{,("):
            continue
        out.add(m.group(0))
    return out - bound(text)


def crossings(files: list[str], owners: dict, route_app: dict) -> list[str]:
    """Every crossing in these files, one line each, sorted."""
    found = set()
    code = [p for p in files if is_code(p)]
    # Python: each module by its name, with its owner
    modules = {Path(p).stem: p for p in code if p.endswith(".py")}
    for path in (p for p in code if p.endswith(".py")):
        mine = owner_of(path, owners)
        if mine is None:
            continue
        try:
            tree = ast.parse((TOOL / path).read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for name in sorted(imported(tree)):
            theirs = owner_of(modules[name], owners) if name in modules else None
            if theirs and theirs != mine and theirs != "family":
                found.add(f"py: {path} imports {name} ({theirs})")
    # the page: each script's top-level names, then what each script names of another owner's
    scripts = [p for p in code if p.endswith(".js") and "/vendor/" not in p]
    texts = {p: script_code((TOOL / p).read_text(encoding="utf-8", errors="replace")) for p in scripts}
    defined: dict[str, set[str]] = {}
    for path, text in texts.items():
        for line in text.splitlines():
            m = JS_TOP.match(line)
            if m:
                defined.setdefault(next(g for g in m.groups() if g), set()).add(path)
    for path, text in texts.items():
        mine = owner_of(path, owners)
        if mine is None:
            continue
        for name in sorted(named(text)):
            where = defined.get(name, set())
            kinds = {owner_of(p, owners) for p in where}
            if not where or path in where or mine in kinds or "family" in kinds:
                continue
            first = sorted(where)[0]
            found.add(f"js: {path} names {name} ({first}, {owner_of(first, owners)})")
    for path in scripts:
        mine = owner_of(path, owners)
        raw = (TOOL / path).read_text(encoding="utf-8", errors="replace")
        for route in sorted(set(ROUTE.findall(raw))):
            theirs = route_app.get(route.split("?")[0])
            if theirs in APPS and mine is not None and theirs != mine:
                found.add(f"route: {path} calls {route} ({theirs})")
    for path in (p for p in code if p.endswith((".html", ".htm"))):
        mine = owner_of(path, owners)
        raw = (TOOL / path).read_text(encoding="utf-8", errors="replace")
        base = Path(path).parent
        for target in sorted(set(LOADS.findall(raw))):
            hit = next((str(Path(b) / target) for b in (base,) if (TOOL / b / target).is_file()), None)
            theirs = owner_of(Path(hit).as_posix(), owners) if hit else None
            if theirs in APPS and mine is not None and theirs != mine:
                found.add(f"src: {path} loads {Path(hit).as_posix()} ({theirs})")
    return sorted(found)


def unowned(files: list[str], owners: dict) -> list[str]:
    """Each module or page file with no owner, by folder or in the table."""
    return [p for p in files if is_code(p) and owner_of(p, owners) is None]


def row_owner(dest: str, source: str, owners: dict) -> str | None:
    """Whose a row of a build's list is: a module's or a page file's by its source's folder or the owners
    table, and a data file's, a doc's or the demo's by `app_identity.FILES`, by its path in the bundle, which
    is its path from the root (the sixth build, 23 October 2026)."""
    import app_identity
    return owner_of(source, owners) or app_identity.owner_of_file(dest)


def foreign_in_bundles(listing, owners: dict, detail: bool = False) -> dict:
    """For each app, the rows of its build's list whose owner is another app, counted, or with `detail` named."""
    found = {}
    for app in APPS:
        found[app] = [dest for dest, source in listing(app) if row_owner(dest, source, owners) in APPS
                      and row_owner(dest, source, owners) != app]
    return found if detail else {app: len(rows) for app, rows in found.items()}


def load_baseline() -> dict:
    return json.loads(BASELINE.read_text(encoding="utf-8"))


def current(route_app: dict, listing) -> dict:
    base = load_baseline()
    files = tracked()
    return {"crossings": crossings(files, base["owners"], route_app),
            "foreign": foreign_in_bundles(listing, base["owners"]), "unowned": unowned(files, base["owners"])}


def test_boundaries(scratch):
    from .support import check, source
    import server as server_mod
    sys.path.insert(0, str(source("packaging")))
    import build_mac

    base = load_baseline()
    files = tracked()
    check("253: the files read are the app's own, git's list or, with no git as in the gate's snapshot, a walk of the folder",
          {"server.py", "family/static/shell.js", "family/app_identity.py", "tests/boundaries.json"} <= set(files),
          f"{len(files)} files")
    now = current(server_mod.ROUTE_APP, build_mac.listing)
    have, had = set(now["crossings"]), set(base["crossings"])
    check("253: every module and page file has an owner, its folder's or the baseline's table",
          not now["unowned"], ", ".join(now["unowned"][:8]))
    check("253: no crossing the baseline does not hold, the family reaching into no new app's code nor one app "
          "into another's", not (have - had), "; ".join(sorted(have - had)[:6]))
    python = sorted(c for c in have | had if c.startswith("py:"))
    check("253: no Python crossing at all, the family importing no app's module nor one app another's, strict since "
          "the fourth build", not python, "; ".join(python[:6]))
    check("253: no crossing of the page at all, the family's scripts and page naming none of an app's names, routes "
          "or files, nor one app's another's, strict since the fifth build", not have, "; ".join(sorted(have)[:6]))
    check("253: the baseline holds no crossing that has gone, so its count only goes down (write it again with "
          "--write)", not (had - have), f"{len(had - have)} gone: " + "; ".join(sorted(had - have)[:6]))
    check("253: the baseline's count is its list's", base.get("count") == len(base["crossings"]),
          f"{base.get('count')} for {len(base['crossings'])}")
    foreign = foreign_in_bundles(build_mac.listing, base["owners"], detail=True)
    check("253: no app's bundle carries anything of another app's, module, page file, data file, doc or demo, strict "
          "since the sixth build", base["foreign"] == {a: 0 for a in APPS} and not any(foreign.values()),
          str({a: rows[:6] for a, rows in foreign.items() if rows}))

    # the folder lists: every module once, the page merged without a name twice, each app's own and the family's
    lists = {app: build_mac.listing(app) for app in APPS}
    dests = {app: [d for d, _ in rows] for app, rows in lists.items()}
    check("253: build_mac.py --list names each module once, boot's among them, and the page and data once each, for every app",
          all(len(d) == len(set(d)) for d in dests.values()) and all("PYZ/boot" in d for d in dests.values())
          and all(f"PYZ/{m}" in dests[a] for a in APPS for m in build_mac.modules(a))
          and set(build_mac.MODULES) == {m for a in APPS for m in build_mac.modules(a)})
    check("253: every bundle carries the family's modules, page, licences and versions, each its own config, and the demo "
          "Idiograph's alone",
          all({f"PYZ/{m}" for m in build_mac.MODULES_BY_OWNER["family"]} | {"static/page.html", "static/shell.js", "LICENSE",
                                                                             "NOTICE.md", "versions.json", "config.json"}
              <= set(dests[a]) for a in APPS)
          and any(d.startswith("demo/") for d in dests["idiograph"])
          and not any(d.startswith("demo/") for a in ("sift", "trace") for d in dests[a])
          and all(dict(lists[a])["config.json"] == f"server.shipped_config({a!r})" for a in APPS))
    check("253: the page's own scripts for node --check are the shipped ones, the vendored left out, each from its own folder",
          all(sorted(f"static/{p.name}" for p in build_mac.page_scripts(a))
              == sorted(d for d in dests[a] if d.startswith("static/") and d.endswith(".js") and d.count("/") == 1)
              for a in APPS))

    # every entry starts under python -I from a folder of its own
    alone = scratch / "boundaries-cwd"
    alone.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("PYTHON", "IDIOGRAPH_"))}
    env["PYTHONIOENCODING"] = "utf-8"
    failed = []
    for entry, flag in ENTRIES:
        ran = subprocess.run([sys.executable, "-I", str(TOOL / entry), flag], cwd=alone, env=env, capture_output=True,
                             encoding="utf-8", errors="replace", timeout=120)
        if ran.returncode != 0:
            failed.append(f"{entry}: {(ran.stderr or ran.stdout).strip().splitlines()[-1:]}")
    check("253: every entry starts under python -I from a folder of its own, the family's modules found through boot",
          not failed, "; ".join(failed[:4]))

    # repath: a patch made before a move, its paths rewritten, a split file left for a hand
    import repath
    before_move = ("diff --git a/app_identity.py b/app_identity.py\nindex 1..2 100644\n--- a/app_identity.py\n"
                   "+++ b/app_identity.py\n@@ -1 +1 @@\n-old\n+new\n"
                   "diff --git a/static/app.js b/static/app.js\n--- a/static/app.js\n+++ b/static/app.js\n@@ -1 +1 @@\n-a\n+b\n")
    remade, moved, kept = repath.repath(before_move, {"app_identity.py": "family/app_identity.py"},
                                        {"static/app.js": ("static/shell.js", "static/distil.js")})
    check("253: repath rewrites a moved file's paths in a patch, its hunks as they were, and leaves a split file for a hand",
          "diff --git a/family/app_identity.py b/family/app_identity.py" in remade and "+++ b/family/app_identity.py" in remade
          and "--- a/family/app_identity.py" in remade and "-old\n+new\n" in remade and moved == ["app_identity.py"]
          and kept == ["static/app.js"] and "+++ b/static/app.js" in remade, remade[:200])

    # boot itself: the folders on the path once each, a file found where it is
    import boot
    before = list(sys.path)
    boot.setup()
    check("253: boot.setup puts the root, family/ and every app's folder on the path, and again changes nothing",
          sys.path == before and all(str(f) in sys.path for f in boot.setup()) and sys.path == before
          and boot.ROOT == TOOL and boot.resource("versions.json") == TOOL / "versions.json"
          and boot.resource("static/page.html") == TOOL / "family" / "static" / "page.html"
          and boot.resource("static/distil.js") == TOOL / "apps" / "idiograph" / "static" / "distil.js")


def write() -> dict:
    """The baseline written again from the tree as it is, the owners table kept."""
    sys.path.insert(0, str(TOOL))
    import boot
    boot.setup()
    sys.path.insert(0, str(TOOL / "packaging"))
    import build_mac
    import server
    base = load_baseline()
    now = current(server.ROUTE_APP, build_mac.listing)
    if now["unowned"]:
        raise SystemExit(f"Give these an owner in {BASELINE.name} first: {', '.join(now['unowned'])}")
    base.update(count=len(now["crossings"]), crossings=now["crossings"], foreign=now["foreign"])
    BASELINE.write_text(json.dumps(base, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return base


if __name__ == "__main__":
    if sys.argv[1:] != ["--write"]:
        raise SystemExit("Run it with --write to write tests/boundaries.json again from the tree as it is.")
    done = write()
    print(f"{done['count']} crossings, foreign in each bundle {done['foreign']}")
