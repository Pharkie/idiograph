#!/usr/bin/env python3
"""Draw Sift's and Trace's icons, every file their builds and the page's favicon need (20 October 2026,
the three-app split's build 6, drawing 4 of the plan).

    python3 packaging/tauri/make_icons.py          # on a Mac, both apps' icons, written in the checkout
    python3 packaging/tauri/make_icons.py sift     # Sift's alone

Each icon is the family's paper tile, the mark in ink and one point in the crux orange, drawn by
make_app's `draw_icon` (Idiograph's dot, Sift's record falling through, Trace's citation). For each
app it writes `src-tauri/icons/<app>/`, the files tauri.conf.json names for Idiograph in `icons/`
(`bundle.ICON_FILES`, with `icon.png` at 512 beside them), and `favicon-<app>.svg`, the page's
icon in the mark drawn for 16 pixels, light and dark as `static/favicon.svg` is, in the app's own
`apps/<app>/static/` where it has one, else `static/`. Idiograph's own files
are never written here: they stay as they are. The icns needs the Mac's sips and iconutil, so the
script runs on a Mac, and its outputs are committed, so a build anywhere has them.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent.parent
sys.path.insert(0, str(TOOL))
sys.path.insert(0, str(HERE.parent))
import boot  # noqa: E402  the family's folders on the path (boot.py)
boot.setup()

import make_app  # noqa: E402  the icons' drawing
import build_windows  # noqa: E402  the .ico, at the sizes Windows asks
import bundle  # noqa: E402  each app's icons' folder

ICONS = HERE / "src-tauri"
# each PNG file and the pixels it is drawn at
PNGS = {"32x32.png": 32, "128x128.png": 128, "128x128@2x.png": 256, "icon.png": 512}
APPS = ("sift", "trace")
# the favicon's colours, light and then dark, as static/favicon.svg has them
FAVICON_STYLE = (".t{fill:#F6F1E8}.i{fill:#1F1B16}.k{fill:#C25E0B}@media (prefers-color-scheme:dark)"
                 "{.t{fill:#211C15}.i{fill:#EFE7D9}.k{fill:#F0A45C}}")


def favicon_svg(app: str) -> str:
    """The page's icon for `app`: the 16 pixel drawing's tile and rectangles, in the page's colours,
    light and dark."""
    _, small = make_app.DRAWINGS[app]
    cls = {make_app.PAPER: "t", make_app.INK: "i", make_app.CRUX: "k"}
    parts = []
    for (x0, y0, x1, y1), radius, rgb in small:
        x, y, w, h = (round(v / 64, 2) for v in (x0, y0, x1 - x0, y1 - y0))
        rx = f' rx="{round(radius / 64, 2):g}"' if radius else ""
        parts.append(f'<rect class="{cls[rgb]}" x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}"{rx}/>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16">'
            f'<style>{FAVICON_STYLE}</style>' + "".join(parts) + "</svg>\n")


def make(app: str) -> list[Path]:
    """Every icon file of `app`, written. Answers the files."""
    if app not in APPS:
        raise SystemExit(f"Icons are drawn here for {' and '.join(APPS)}, and Idiograph's stay as they are.")
    folder = ICONS / bundle.icon_dir(app)
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for name, size in PNGS.items():
        (folder / name).write_bytes(make_app.png_bytes(size, make_app.draw_icon(size, app)))
        written.append(folder / name)
    (folder / "icon.ico").write_bytes(build_windows.ico_bytes(app=app))
    make_app.build_icns(folder / "icon.icns", app)
    # in the app's own static/ where it has one, Trace's since the family codebase's second build, else the root's
    own = TOOL / "apps" / app / "static"
    favicon = (own if own.is_dir() else TOOL / "static") / f"favicon-{app}.svg"
    favicon.write_text(favicon_svg(app), encoding="utf-8")
    return written + [folder / "icon.ico", folder / "icon.icns", favicon]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Draw Sift's and Trace's icons.")
    ap.add_argument("apps", nargs="*", default=list(APPS), help="sift, trace or both")
    args = ap.parse_args(argv)
    if sys.platform != "darwin":
        raise SystemExit("The icons are drawn on a Mac, which has sips and iconutil for the icns.")
    for app in args.apps:
        for path in make(app):
            print(f"Wrote {path.relative_to(TOOL).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
