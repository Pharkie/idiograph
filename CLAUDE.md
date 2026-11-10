# Idiograph

Idiograph is an app for Interpretative Phenomenological Analysis and reflexive thematic analysis. Sift and Trace are apps of their own built from this one codebase. The README says what each does and how to run them from source.

## Where things are

The app is this folder: `server.py` and its modules, `family/` (what the three apps share) and `apps/<app>/` (each app's own), found through `boot.py` (docs/internals.md, The family's folders), `static/` (the page), the suite in `tests/` (`tests/test_idiograph.py`, its areas in `tests/areas/`), `docs/` (manual, internals, agents, design), `packaging/` (the Mac, Windows and Tauri builds and the releases), the demo participants in `demo/`.

The suite's fixture is the demo, so it runs on any machine. The checks on the maintainer's own study data read a local gate file (`docs/internals.md`, "The local gate file") and skip where there is none.

## Rules

The venv is `.venv` at the root (openpyxl, lxml, pytest). Call its python by its path. Never write a symlink or a wrapper script to it.

`./verify` is the gate. Read its last stdout line, never the exit code: `VERIFY: GREEN merge=yes mode=full sha=<sha> tree=<state> snap=<tree>`. `./verify --fast` takes seconds. While building, run the areas a change touches, `.venv/bin/python tests/test_idiograph.py --changed`, and leave the full suite to the gate.

Commit only with `./commit -m "<msg>" -- <paths>`, naming the change's files, after a GREEN full gate.

No participant's real name and no case folder's second name in anything tracked (the gate checks both). Idiograph's data is changed only through its own API (the app, the command line and the MCP server, `docs/agents.md`), never by editing its files.

A maintainer's own notes go in `CLAUDE.local.md`, which git ignores.
