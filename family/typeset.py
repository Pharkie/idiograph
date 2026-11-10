"""Typst, the one engine every PDF and picture of a print view is made by (typst1, 9 November 2026, Adam, 9 November
about 18:10: Typst on the Mac, Windows and Linux, and no fallback: it works or it says it could not).

    typeset.render(template, data)                     # the PDF's bytes
    typeset.render(template, data, fmt="png", ppi=144) # one PNG's bytes a page

`template` is a view's main `.typ` file, its folder the root Typst reads files under, and `data` the view's data,
given to the template as the input `data` holding its JSON text (`#let d = json(bytes(sys.inputs.data))`). Every
page is set in the app's own fonts, `static/fonts/` (Charis SIL and Nunito Sans), and those alone: no system font
and no font of Typst's own, so the pages are the same on every computer and from either engine below.

Each way the app runs has one engine, never one tried and then the other:

- The installed app (frozen) runs its typesetter, `idiograph-typeset` (`.exe` on Windows), the small program
  built from `packaging/tauri/typeset/` and put beside the frozen server, found from `sys.executable`, so the
  window's server and the command line inside the app both find it. The data goes on its standard input, so no
  file is left behind, and it has `LIMIT` seconds.
- A run from source (the suite, `./idiograph`, GitHub's tests) uses typst-py, the Python package, pinned to the
  version whose Typst the typesetter's crates are pinned to (`TYPST`).

A failure raises `Failed`, whose words are a plain sentence from the catalogue for the person using the app.
What the engine said goes to the server's log (its standard error), never on the screen.
"""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import boot
import i18n

# the Typst version both engines carry: typst-py 0.15.2's, and the typesetter's crates pinned with `=` to it
TYPST = "0.15.1"
TYPST_PY = "0.15.2"
# the typesetter's name beside the frozen server
HELPER = "idiograph-typeset"
# the app's fonts, by their path as the app ships
FONTS = "static/fonts"
# how long the typesetter may take over one view before it is ended, in seconds
LIMIT = 60.0
FORMATS = ("pdf", "png")

_FONTS_HELD: dict = {}
_LOCK = threading.Lock()


class Failed(Exception):
    """The pages could not be made. `str()` is a sentence for the person using the app, in the app's language."""


def say(line: str) -> None:
    """A line for the server's log."""
    print(f"typeset: {line}", file=sys.stderr, flush=True)


def fonts_dir() -> Path:
    """The folder of the app's fonts: family/static/fonts from source, static/fonts in the frozen app."""
    return boot.resource(FONTS)


def helper_path(executable: str | None = None) -> Path:
    """Where the frozen app's typesetter is: beside the executable the server runs as."""
    name = HELPER + (".exe" if sys.platform == "win32" else "")
    return Path(executable or sys.executable).resolve().parent / name


def engine() -> str:
    """Which engine this run uses: `helper` frozen, `typst-py` from source."""
    return "helper" if boot.FROZEN else "typst-py"


def render(template, data: dict, *, fmt: str = "pdf", ppi: float = 144.0) -> bytes | list[bytes]:
    """The view `template` made with `data`: the PDF's bytes, or for `fmt="png"` a list of each page's PNG at
    `ppi`. Raises `Failed` when the pages cannot be made."""
    if fmt not in FORMATS:
        raise ValueError(f"fmt is pdf or png, not {fmt!r}")
    template = Path(template).resolve()
    text = json.dumps(data, ensure_ascii=False)
    if boot.FROZEN:
        return by_helper(helper_path(), template, text, fmt, ppi)
    return by_typst_py(template, text, fmt, ppi)


def failed(key: str, said: str = "") -> Failed:
    """`Failed` with the catalogue's sentence `typeset.<key>`, what the engine said put in the log."""
    if said:
        for line in said.strip().splitlines():
            say(line)
    # each sentence is asked for by name, so the catalogue's check sees it used
    return Failed({"failed": i18n.t("typeset.failed"), "slow": i18n.t("typeset.slow"),
                   "missing": i18n.t("typeset.missing")}[key])


def by_typst_py(template: Path, text: str, fmt: str, ppi: float) -> bytes | list[bytes]:
    """typst-py, from source: the fonts folder alone, no system font and no font of Typst's own."""
    try:
        import typst
    except ImportError as exc:
        raise failed("missing", f"typst-py {TYPST_PY} is not installed: {exc}") from None
    began = time.monotonic()
    try:
        out = typst.compile(str(template), root=str(template.parent), font_paths=held_fonts(typst),
                            format=fmt, ppi=ppi if fmt == "png" else None, sys_inputs={"data": text})
    except Exception as exc:  # typst.TypstError and anything the binding raises
        said = "\n".join(str(p) for p in (exc, getattr(exc, "diagnostic", ""), *(getattr(exc, "hints", None) or [])) if p)
        raise failed("failed", f"{template.name}: {said}") from None
    pages = out if isinstance(out, list) else [out]
    say(f"{template.name} as {fmt} by typst-py in {time.monotonic() - began:.2f}s")
    return pages if fmt == "png" else pages[0]


def held_fonts(typst):
    """typst-py's fonts, the folder alone, read once a run."""
    with _LOCK:
        if "fonts" not in _FONTS_HELD:
            _FONTS_HELD["fonts"] = typst.Fonts(include_system_fonts=False, include_embedded_fonts=False,
                                               font_paths=[str(fonts_dir())])
        return _FONTS_HELD["fonts"]


def helper_command(helper: Path, template: Path, fmt: str, ppi: float) -> list[str]:
    return [str(helper), "--root", str(template.parent), "--main", template.name, "--fonts", str(fonts_dir()),
            "--format", fmt, "--ppi", f"{ppi:g}"]


def by_helper(helper: Path, template: Path, text: str, fmt: str, ppi: float, limit: float = LIMIT) -> bytes | list[bytes]:
    """The frozen app's typesetter, the data on its standard input, its pages on its standard output, what it says
    to the log. Ended after `limit` seconds."""
    if not helper.is_file():
        raise failed("missing", f"no typesetter at {helper}")
    began = time.monotonic()
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
    try:
        done = subprocess.run(helper_command(helper, template, fmt, ppi), input=text.encode("utf-8"),
                              capture_output=True, timeout=limit, creationflags=flags)
    except subprocess.TimeoutExpired:
        raise failed("slow", f"{template.name} took over {limit:g}s and the typesetter was ended") from None
    except OSError as exc:
        raise failed("missing", f"the typesetter at {helper} did not run: {exc}") from None
    said = done.stderr.decode("utf-8", errors="replace")
    if done.returncode != 0:
        raise failed("failed", f"{template.name}, exit {done.returncode}:\n{said}")
    for line in said.strip().splitlines():
        say(line)
    try:
        pages = split_pages(done.stdout) if fmt == "png" else [done.stdout]
    except ValueError as exc:
        raise failed("failed", f"{template.name}: {exc}") from None
    if not pages or (fmt == "pdf" and not done.stdout.startswith(b"%PDF-")):
        raise failed("failed", f"{template.name}: the typesetter wrote no {fmt}")
    say(f"{template.name} as {fmt} by the typesetter in {time.monotonic() - began:.2f}s")
    return pages if fmt == "png" else pages[0]


def split_pages(out: bytes) -> list[bytes]:
    """The typesetter's PNGs, each its length as eight bytes, big end first, then its bytes."""
    pages, at = [], 0
    while at < len(out):
        if at + 8 > len(out):
            raise ValueError("a page's length is cut short")
        size = int.from_bytes(out[at:at + 8], "big")
        at += 8
        if at + size > len(out):
            raise ValueError("a page is cut short")
        pages.append(out[at:at + size])
        at += size
    return pages


def available() -> bool:
    """Whether this run's engine is there: the typesetter beside the frozen server, or typst-py from source."""
    if boot.FROZEN:
        return helper_path().is_file()
    try:
        import typst  # noqa: F401
        return True
    except ImportError:
        return False

