#!/usr/bin/env python3
"""The Contours set of pictures a participant can be given (picsets2, 20 November 2026, Adam: patterns beside the
faces, "maybe A and D together?"). Twenty abstract ink marks with no face, so a picture says nothing of a
participant's gender, age or ethnicity, in four kinds woven together: contour lines (nested wobbly loops, as on a
map), currents (wavy lines at an angle), strata (bands, one filled) and grain (a field of dots thinning one way).
Drawn by this script, Idiograph's own work under the app's licence, with no third party's terms, and written in
the app's ink and one grey on white into `apps/idiograph/static/faces/contour01.svg` to `contour20.svg`:

    python3 packaging/make_contours.py

Made once and committed, the same twenty every run (each picture's randomness is seeded by its kind and number).
Every line is written as a filled outline and every dot as a path of two arcs, so each file holds a rect, groups and
paths with a fill alone, as the app's other pictures do.
"""
from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "apps" / "idiograph" / "static" / "faces"
INK = "#2B2620"
GREY = "#C9C2B8"
WHITE = "#FFFFFF"
SIZE = 64


def f(v: float) -> str:
    return f"{v:.1f}".replace("-0.0", "0.0")


def path(points: list[tuple[float, float]], close: bool = True) -> str:
    return "M" + " L".join(f"{f(x)} {f(y)}" for x, y in points) + ("Z" if close else "")


def ribbon(points: list[tuple[float, float]], width: float) -> str:
    """An open line of `width` as a filled outline: the line offset to one side, then back along the other."""
    half = width / 2
    left, right = [], []
    for i, (x, y) in enumerate(points):
        ax, ay = points[max(0, i - 1)]
        bx, by = points[min(len(points) - 1, i + 1)]
        dx, dy = bx - ax, by - ay
        n = math.hypot(dx, dy) or 1
        nx, ny = -dy / n * half, dx / n * half
        left.append((x + nx, y + ny))
        right.append((x - nx, y - ny))
    return path(left + right[::-1])


def dot(x: float, y: float, r: float) -> str:
    return f"M{f(x - r)} {f(y)}a{f(r)} {f(r)} 0 1 0 {f(2 * r)} 0a{f(r)} {f(r)} 0 1 0 {f(-2 * r)} 0Z"


def loop(cx, cy, r, waves) -> list[tuple[float, float]]:
    out = []
    for i in range(72):
        a = 2 * math.pi * i / 72
        rr = r * (1 + sum(amp * math.sin(k * a + ph) for k, amp, ph in waves))
        out.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return out


def contour(rng: random.Random) -> list[str]:
    """Nested loops round a centre a little off the middle, each a ring of ink, the innermost sometimes filled."""
    cx, cy = 50 + rng.uniform(-14, 14), 50 + rng.uniform(-14, 14)
    waves = [(k, rng.uniform(0.03, 0.09), rng.uniform(0, 6.3)) for k in (2, 3, rng.choice((4, 5)))]
    n = rng.randint(3, 6)
    out = []
    for i in range(n):
        r = 8 + i * (40 / n)
        out.append(f'<path d="{path(loop(cx, cy, r + 1.3, waves))}{path(loop(cx, cy, r - 1.3, waves))}" fill="{INK}" fill-rule="evenodd"/>')
    if rng.random() < 0.5:
        out.append(f'<path d="{path(loop(cx, cy, 5, waves))}" fill="{INK}"/>')
    return out


def currents(rng: random.Random) -> list[str]:
    """Wavy lines at an angle, one sometimes heavier."""
    angle = rng.choice((-35, -20, 0, 15, 30, 50, 75, 90))
    n = rng.randint(4, 7)
    amp, period = rng.uniform(3, 8), rng.uniform(22, 45)
    out = []
    for i in range(n):
        y = 10 + i * 80 / (n - 1)
        pts = [(x, y + amp * math.sin(2 * math.pi * x / period + i * 0.6)) for x in range(-20, 125, 3)]
        out.append(f'<path d="{ribbon(pts, 5 if rng.random() < 0.2 else 2.4)}" fill="{INK}"/>')
    return [f'<g transform="rotate({angle} 50 50)">' + "".join(out) + "</g>"]


def strata(rng: random.Random) -> list[str]:
    """Bands one over another, one filled in ink and one in grey, a line along each."""
    angle = rng.choice((-12, -6, 0, 0, 6, 12))
    n = rng.randint(4, 6)
    filled, grey = rng.randrange(n), rng.randrange(n)
    out, y = [], -5.0
    for i in range(n):
        h = rng.uniform(12, 26)
        top = [(x, y + 2.5 * math.sin(x / rng.uniform(9, 16) + i)) for x in range(-20, 125, 4)]
        bot = [(x, y + h + 2.5 * math.sin(x / 13 + i + 1)) for x in range(124, -21, -4)]
        if i == filled:
            out.append(f'<path d="{path(top + bot)}" fill="{INK}"/>')
        elif i == grey:
            out.append(f'<path d="{path(top + bot)}" fill="{GREY}"/>')
        out.append(f'<path d="{ribbon(bot[::-1], 2.2)}" fill="{INK}"/>')
        y += h
    return [f'<g transform="rotate({angle} 50 50)">' + "".join(out) + "</g>"]


def grain(rng: random.Random) -> list[str]:
    """A field of dots, large on one side and thinning away to the other."""
    ax, ay = rng.uniform(-1, 1), rng.uniform(-1, 1)
    norm = math.hypot(ax, ay) or 1
    ax, ay = ax / norm, ay / norm
    step = rng.choice((7, 8, 9))
    dots = []
    for gx in range(0, 101, step):
        for gy in range(0, 101, step):
            x, y = gx + rng.uniform(-2, 2), gy + rng.uniform(-2, 2)
            t = ((x - 50) * ax + (y - 50) * ay) / 70 + 0.5
            r = max(0.0, 3.4 * (1 - t))
            if r > 0.6:
                dots.append(dot(x, y, r))
    return [f'<path d="{"".join(dots)}" fill="{INK}"/>']


# Left out at Adam's word on 21 November because they look like another picture of the set: of the forty first drawn
# (numbered as they were drawn, the four kinds in turn), each group of pictures a person would call the same pattern
# keeps the one most unlike the rest of the set. The groups, found by comparing every pair at the chooser's size and
# Home's ring size in greyscale after a light blur, turned and mirrored to the closest, all under 0.055 mean
# difference (0.075 for the waves and strata): tight rings 1, 5, 13, 17, 21, 29 (keeps 21), loose rings 9, 25, 33, 37
# (keeps 37), dots 4, 8, 16, 24, 32, 40 (keeps 4), dots on the diagonal 12, 20, 28, 36 (keeps 36), three thin waves
# 10, 30, 38 (keeps 38), five thin waves 2, 34 (keeps 2), bands 3, 39 (keeps 3).
LEFT_OUT = {1, 5, 8, 9, 10, 12, 13, 16, 17, 20, 24, 25, 28, 29, 30, 32, 33, 34, 39, 40}
KINDS = [("contour", contour), ("currents", currents), ("strata", strata), ("grain", grain)]


def pictures() -> dict[str, str]:
    """The twenty kept of the forty first drawn, the four kinds in turn, numbered with no gaps in their old order."""
    out, n, old = {}, 0, 0
    for i in range(10):
        for name, draw in KINDS:
            old += 1
            if old in LEFT_OUT:
                continue
            n += 1
            body = "".join(draw(random.Random(f"contours-{name}-{i}")))
            out[f"contour{n:02d}"] = (
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="{SIZE}" height="{SIZE}">'
                "<!-- Contours, Idiograph's own, drawn by packaging/make_contours.py -->"
                f'<rect x="0" y="0" width="100" height="100" fill="{WHITE}"/>{body}</svg>\n')
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Draw the Contours set into static/faces.")
    ap.add_argument("--out", default=str(OUT), help="where the pictures are written, static/faces by default")
    out = Path(ap.parse_args(argv).out)
    out.mkdir(parents=True, exist_ok=True)
    made = pictures()
    for name, svg in made.items():
        target = out / f"{name}.svg"
        if target.is_symlink():
            print(f"{target} is a link, so nothing was written there.", file=sys.stderr)
            return 1
        target.write_text(svg, encoding="utf-8", newline="\n")
    print(f"{len(made)} pictures in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
