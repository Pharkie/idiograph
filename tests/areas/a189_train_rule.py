"""Area 189: the full suite in the coordinator's train, a targeted check in a build (Adam, 18 October).
The entry point runs every area only in a train, `--train`, the gate's own run or GitHub's, and says
what to run instead anywhere else, and `--changed` chooses the areas a change touches."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from areas import support
from areas.support import TOOL, check, skip


def test_train_rule(scratch):
    import test_idiograph as runner

    # ── the refusal: no --area, no train, so nothing runs and one line says what to run instead
    env = {k: v for k, v in os.environ.items() if k not in (runner.TRAIN_ENV, "GITHUB_ACTIONS")}
    env["PYTHONIOENCODING"] = "utf-8"
    ran = subprocess.run([sys.executable, str(support.source("tests/test_idiograph.py"))], cwd=TOOL, env=env,
                         capture_output=True, encoding="utf-8", errors="replace", timeout=300)
    said = [line for line in ran.stdout.splitlines() if line.strip()]
    check("189: outside a train the entry point with no --area runs nothing, exits 2 and says in one line that the "
          "full suite is the train's and to run --changed instead",
          ran.returncode == 2 and said == [runner.REFUSAL] and "--changed" in said[0] and "train" in said[0],
          f"exit {ran.returncode}, {said[:3]} {ran.stderr[-300:]}")

    # ── the four ways a full run goes ahead, and the values that do not count
    reason = runner.train_reason
    check("189: --train, the gate's IDIOGRAPH_TRAIN=1 and GitHub's GITHUB_ACTIONS=true each let a full run go ahead, "
          "and nothing else does",
          reason(True, {}) == "--train" and reason(False, {"IDIOGRAPH_TRAIN": "1"}) == "the gate"
          and reason(False, {"GITHUB_ACTIONS": "true"}) == "GitHub"
          and reason(False, {}) is None and reason(False, {"IDIOGRAPH_TRAIN": "0"}) is None
          and reason(False, {"GITHUB_ACTIONS": "false"}) is None and reason(False, {"IDIOGRAPH_TRAIN": ""}) is None,
          str([reason(True, {}), reason(False, {"IDIOGRAPH_TRAIN": "1"}), reason(False, {"GITHUB_ACTIONS": "true"})]))

    # ── the one unittest case unittest discover collects is skipped outside a train with the same line,
    # so a builder cannot run everything by that road either. The variables are put back as they were,
    # since inside the gate's run this one is a train and a run inside it would start the suite again.
    kept = {k: os.environ.pop(k) for k in (runner.TRAIN_ENV, "GITHUB_ACTIONS") if k in os.environ}
    try:
        result = unittest.TestResult()
        runner.ESHelperChecks("test_every_check_passes").run(result)
    finally:
        os.environ.update(kept)
    check("189: outside a train the unittest case is skipped with the same line, and nothing in it runs",
          result.testsRun == 1 and [why for _, why in result.skipped] == [runner.REFUSAL]
          and not result.failures and not result.errors,
          f"{result.testsRun} run, {len(result.skipped)} skipped, {len(result.failures)} failed, {len(result.errors)} errors")

    # ── --changed on an invented change, in a repository of its own: a committed change to one function
    # of the page's script, a staged change to one rule of its style sheet, one function of the server
    # changed in the working tree and a new area not yet added. Every area's source names app.js, more
    # than COMMON of them, so the file's own name chooses nothing.
    if shutil.which("git") is None:
        return skip("189: --changed on an invented change", "no git on this machine")
    tool = scratch / "a189" / "kites"
    shutil.rmtree(tool.parent, ignore_errors=True)
    (tool / "static").mkdir(parents=True)
    (tool / "tests" / "areas").mkdir(parents=True)
    genv = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    genv.update(GIT_AUTHOR_NAME="Kite Test", GIT_AUTHOR_EMAIL="kites@test.invalid", GIT_CONFIG_NOSYSTEM="1",
                GIT_COMMITTER_NAME="Kite Test", GIT_COMMITTER_EMAIL="kites@test.invalid")

    def git(*args):
        return subprocess.run(["git", "-c", "commit.gpgsign=false", *args],
                              cwd=tool, env=genv, capture_output=True, encoding="utf-8", errors="replace")

    def write(rel, text):
        (tool / rel).write_text(text, encoding="utf-8", newline="\n")

    write("static/app.js", "'use strict';\n\nfunction drawKites(list) {\n  return list.length;\n}\n\n"
                           "function foldSails(n) {\n  return n * 2;\n}\n")
    write("static/style.css", ".kite-tail {\n  color: var(--ink);\n}\n\n.sail-edge {\n  margin: 0;\n}\n")
    write("server.py", "def kite_weather(day):\n    return 'windy'\n\n\ndef sail_count():\n    return 3\n")
    areas = {"a001_kites": "drawKites", "a002_sails": "foldSails", "a003_weather": "kite_weather",
             "a004_tails": "kite-tail", "a005_edges": "sail-edge", "a006_counts": "sail_count"}
    for name, names in areas.items():
        write(f"tests/areas/{name}.py", f"# reads app.js\ndef test_{name[5:]}():\n    return '{names}'\n")
    git("init", "-q", "-b", "main")
    git("add", "-A")
    git("commit", "-q", "-m", "kites")
    git("checkout", "-q", "-b", "build")
    write("static/app.js", (tool / "static/app.js").read_text(encoding="utf-8").replace("n * 2", "n * 3"))
    git("commit", "-q", "-am", "fold further")
    write("static/style.css", (tool / "static/style.css").read_text(encoding="utf-8").replace("var(--ink)", "red"))
    git("add", "static/style.css")
    write("server.py", (tool / "server.py").read_text(encoding="utf-8").replace("'windy'", "'calm'"))
    write("tests/areas/a007_gusts.py", "# reads app.js\ndef test_gusts():\n    return 'gusts'\n")

    common = runner.COMMON
    runner.COMMON = 5
    try:
        got = runner.changed_areas(tool)
    finally:
        runner.COMMON = common
    fork, picked, too_common = got if got else ("", [], [])
    why = dict(picked)
    check("189: --changed chooses the areas naming what changed, committed, staged, in the working tree and a new "
          "area, each with its reason, and none for what did not change",
          set(why) == {"a002_sails", "a003_weather", "a004_tails", "a007_gusts"}
          and why.get("a002_sails") == "names foldSails (static/app.js)"
          and why.get("a004_tails") == "names kite-tail (static/style.css)"
          and why.get("a003_weather") == "names kite_weather (server.py)"
          and why.get("a007_gusts") == "a new area" and len(fork) == 40,
          str(picked))
    check("189: a file's own name that more areas carry than COMMON chooses none of them, and is said",
          any(name.startswith("app.js (") for name in too_common) and "a001_kites" not in why, str(too_common))

    # ── where git cannot say, a downloaded copy, it says so rather than choosing nothing. A folder of
    # the system's own for temporary files, since a scratch folder given by hand may sit inside a repo.
    loose = Path(tempfile.mkdtemp(prefix="idiograph-a189-"))
    try:
        check("189: --changed outside a repository chooses nothing and says it cannot",
              runner.changed_areas(loose) is None)
    finally:
        shutil.rmtree(loose, ignore_errors=True)
