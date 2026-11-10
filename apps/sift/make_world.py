#!/usr/bin/env python3
"""Build `static/world.json`, the map Sift's Country filter shows its counts on (13 October, later).

Every country's outline from Natural Earth's 1:110m countries, Antarctica left out, and every
country's label point from its 1:50m countries, which hold small countries the 110m file lacks, such
as Singapore, Malta and Hong Kong. Each is known by its ISO 3166 two letters, `ISO_A2_EH`, which
gives France and Norway theirs where `ISO_A2` reads -99, and named as Sift's Country column names it.
Both are projected on Equal Earth, an equal-area projection, so a circle's size means the same at
every latitude, into a frame 1000 wide, each outline an SVG path with its points to a tenth.

    .venv/bin/python3 -I Tools/idiograph/apps/sift/make_world.py ne_110m_admin_0_countries.geojson ne_50m_admin_0_countries.geojson

It reads the two GeoJSON files it is given, Natural Earth 5.1.2, in the public domain, and fetches
nothing. The page reads what it writes and nothing else, so the map is drawn with no network.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

# the family's folders on the path first (boot.py), under `python -I` too, the root two folders up
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import boot  # noqa: E402

boot.setup("sift")
# Sift's own names for the countries, so the map knows a record's country by the name the column gives
import sift  # noqa: E402

OUT = boot.resource("static/world.json")
WIDTH = 1000
# Equal Earth's constants (Šavrič, Patterson and Jenny, 2018)
A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796
M = math.sqrt(3) / 2
# the space left round the land, in the frame's units
MARGIN = 6
# the file's size at most, so the page loads it at once
LIMIT = 150_000
SOURCE = "Natural Earth 5.1.2, admin 0 countries at 1:110m for the outlines and 1:50m for the label points, public domain"


def project(lon: float, lat: float) -> tuple[float, float]:
    """A point on Equal Earth, x east and y north, the equator's half width about 2.71."""
    lam, phi = math.radians(lon), math.radians(lat)
    theta = math.asin(M * math.sin(phi))
    t2 = theta * theta
    t6 = t2 * t2 * t2
    x = 2 * math.sqrt(3) * lam * math.cos(theta) / (3 * (A1 + 3 * A2 * t2 + t6 * (7 * A3 + 9 * A4 * t2)))
    y = theta * (A1 + A2 * t2 + t6 * (A3 + A4 * t2))
    return x, y


HALF = project(180, 0)[0]
SCALE = (WIDTH - 2 * MARGIN) / (2 * HALF)


def rings(geometry: dict) -> list:
    """Every ring of a Polygon or MultiPolygon, outer and inner alike."""
    kind, coords = geometry.get("type"), geometry.get("coordinates") or []
    if kind == "Polygon":
        return list(coords)
    if kind == "MultiPolygon":
        return [ring for polygon in coords for ring in polygon]
    return []


def tenths(t: int) -> str:
    """A number held in tenths as the path writes it, 12, 12.5, -.5."""
    s = str(t // 10) if t % 10 == 0 else f"{t / 10:.1f}"
    return s.replace("0.", ".", 1) if s.startswith("0.") else s.replace("-0.", "-.", 1)


def joined(numbers: list[str]) -> str:
    """Numbers one after another, a space only where a minus sign does not part them."""
    out = ""
    for n in numbers:
        out += n if (not out or n.startswith("-")) else " " + n
    return out


def path_of(ring_list: list, top: float) -> str:
    """An outline as an SVG path: each ring moved to, then drawn relative to the point before, the
    points rounded to a tenth in the frame, a point that rounds onto the one before left out."""
    parts = []
    for ring in ring_list:
        pts = []
        for lon, lat, *_ in ring:
            x, y = project(lon, lat)
            p = (round((MARGIN + (x + HALF) * SCALE) * 10), round((top - y * SCALE) * 10))
            if not pts or p != pts[-1]:
                pts.append(p)
        if len(pts) > 1 and pts[0] == pts[-1]:
            pts.pop()
        if len(pts) < 3:
            continue
        steps = [tenths(b[0] - a[0]) + "," + tenths(b[1] - a[1]) for a, b in zip(pts, pts[1:])]
        parts.append(f"M{tenths(pts[0][0])} {tenths(pts[0][1])}l" + joined_pairs(steps) + "z")
    return "".join(parts)


def joined_pairs(steps: list[str]) -> str:
    """Each step as `dx dy`, written as tightly as SVG reads it."""
    numbers = []
    for s in steps:
        numbers += s.split(",")
    return joined(numbers)


def build(outlines_file: Path, points_file: Path) -> dict:
    outlines = json.loads(outlines_file.read_text(encoding="utf-8"))["features"]
    labels = json.loads(points_file.read_text(encoding="utf-8"))["features"]
    code = lambda f: str((f.get("properties") or {}).get("ISO_A2_EH") or "").upper()
    kept = [f for f in outlines if code(f) != "AQ"]
    lats = [lat for f in kept for ring in rings(f["geometry"]) for _, lat, *_ in ring]
    north, south = max(lats), min(lats)
    top = MARGIN + project(0, north)[1] * SCALE
    height = round(top - project(0, south)[1] * SCALE + MARGIN)
    shapes = []
    for f in kept:
        c = code(f)
        d = path_of(rings(f["geometry"]), top)
        if d:
            shapes.append({"code": c if len(c) == 2 and c.isalpha() else "", "d": d})
    points, names = {}, {}
    for f in labels:
        c = code(f)
        p = f.get("properties") or {}
        if len(c) != 2 or not c.isalpha() or c == "AQ" or c in points:
            continue
        if not isinstance(p.get("LABEL_X"), (int, float)) or not isinstance(p.get("LABEL_Y"), (int, float)):
            continue
        x, y = project(p["LABEL_X"], p["LABEL_Y"])
        points[c] = [round(MARGIN + (x + HALF) * SCALE, 1), round(top - y * SCALE, 1)]
        names[c] = sift.country_name(c)
    # the edge of the projection from the south of the land to its north, the sea's outline
    edge = [project(180, lat) for lat in range(math.floor(south), math.ceil(north) + 1)]
    east = [(round((MARGIN + (x + HALF) * SCALE) * 10), round((top - y * SCALE) * 10)) for x, y in edge]
    west = [(WIDTH * 10 - x, y) for x, y in reversed(east)]
    loop = east + west
    sphere = "M" + "L".join(f"{tenths(x)} {tenths(y)}" for x, y in loop) + "z"
    return {"source": SOURCE, "projection": "Equal Earth", "width": WIDTH, "height": height,
            "sphere": sphere, "shapes": shapes, "points": dict(sorted(points.items())), "names": dict(sorted(names.items()))}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build static/world.json from Natural Earth's countries.")
    ap.add_argument("outlines", help="ne_110m_admin_0_countries.geojson")
    ap.add_argument("points", help="ne_50m_admin_0_countries.geojson")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)
    world = build(Path(args.outlines), Path(args.points))
    text = json.dumps(world, ensure_ascii=False, separators=(",", ":"))
    size = len(text.encode("utf-8"))
    if size > LIMIT:
        print(f"world.json would be {size:,} bytes, over {LIMIT:,}, so nothing was written.")
        return 1
    Path(args.out).write_text(text, encoding="utf-8", newline="\n")
    print(f"{len(world['shapes'])} outlines and {len(world['points'])} label points, {size:,} bytes, "
          f"{world['width']} by {world['height']}, written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
