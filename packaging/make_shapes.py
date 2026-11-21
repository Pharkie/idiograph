#!/usr/bin/env python3
"""The Shapes set of pictures a participant can be given (picsets2, 20 November 2026, Adam: patterns beside the
faces, "maybe A and D together?"). Abstract pictures with no face, so a picture says nothing of a participant's
gender, age or ethnicity: three overlapping flat shapes each, from DiceBear's own `shapes` style, "Shapes" by
DiceBear, licensed under CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/; the style's licence is in
`meta.license` of https://github.com/dicebear/styles/blob/main/src/shapes.json and in that repository's LICENSE.md).
Each is drawn again here in the app's ink, a soft ink and one grey on white and written as a small SVG file into
`apps/idiograph/static/faces/shape01.svg` to `shape33.svg`. Run it again after a change to SET:

    python3 packaging/make_shapes.py                # fetch each picture, write the set
    python3 packaging/make_shapes.py --keep DIR     # keep the downloads in DIR, and read them from there next time

Made once and committed: the app never goes online for them. Each picture is asked by its seed, named in SET, so
the same thirty-three come every time, every colour asked as a stand-in and mapped to the app's own. Each download is
untrusted data. It is parsed, never run, a file with a doctype or an entity is refused, and only the shapes expected
are written: each `<use>` of a part inlined as a group with its transform checked, the part's paths with their
outline checked, the clip, the animation and the metadata dropped, so every file holds a rect, groups and paths
with a fill alone. A picture that reads as an X or a cross (two lines crossing) or as a play button (a small
triangle, filled or in outline, as its second or third shape) stops the run, so SET holds none: of the forty first
shown to Adam (seeds 01 to 40), twenty-one were left out by that rule, and the set was made up again to forty from
later seeds, of which seven were then left out at Adam's word on 21 November, so the set is thirty-three.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "apps" / "idiograph" / "static" / "faces"
API = "https://api.dicebear.com/11.x/shapes/svg"
INK = "#2B2620"
SOFT = "#7A7166"
GREY = "#C9C2B8"
WHITE = "#FFFFFF"
# each stand-in asked for and the app's colour it is drawn in: the largest shape ink, the middle one grey, the
# smallest, which sits on top, the soft ink
ASK = {"backgroundColor": "ffffff", "shape1Color": "111111", "shape2Color": "222222", "shape3Color": "333333"}
COLOURS = {"#ffffff": WHITE, "#111111": INK, "#222222": GREY, "#333333": SOFT}
SIZE = 64
# The seeds kept, in the set's order: `idiograph-shapes-NN`. 01 to 40 were the candidate sheet Adam saw; 03 to 07,
# 12, 14, 16, 18, 21, 22, 26, 28, 30, 31, 33 to 35, 37, 38 and 40 are left out (a cross or a small triangle), and
# the twenty-one after 39 are the first later seeds the same rule passes.
# Left out at Adam's word on 21 Nov because they might read as a sign or a symbol: seeds 11, 15, 23, 24, 44, 48 and 59.
SET = [1, 2, 8, 9, 10, 13, 17, 19, 20, 25, 27, 29, 32, 36, 39, 42, 47, 51, 54,
       55, 60, 61, 62, 63, 65, 66, 72, 74, 75, 77, 78, 79, 81]

TAG = re.compile(r"\{http://www\.w3\.org/2000/svg\}([a-zA-Z]+)$")
PATH_D = re.compile(r"[MmLlHhVvCcSsQqTtAaZz0-9eE.,\s+-]{1,200000}")
TRANSFORM = re.compile(r"\s*((matrix|translate|scale|rotate)\([0-9eE.,\s+-]{1,200}\)\s*){1,8}")
HREF = re.compile(r"#[A-Za-z][\w-]{0,80}")
PART = re.compile(r"(shape0[123])-(ellipse|ellipseFilled|line|polygon|polygonFilled|rectangle|rectangleFilled)-[0-9a-f]{1,16}")
ROTATE = re.compile(r"rotate\((-?[0-9.]+)")
RULES = {"evenodd", "nonzero"}


class ShapesError(Exception):
    """A download that is not what this expects, or a picture the set leaves out: nothing is written."""


def url_of(seed: int) -> str:
    """The request for one picture: its seed and the stand-in colours."""
    return f"{API}?{urllib.parse.urlencode(dict(seed=f'idiograph-shapes-{seed:02d}', **ASK))}"


def fetch(url: str, into: Path) -> bytes:
    """One download, kept in `into` under its request's hash and read from there when it is already there."""
    kept = into / f"{hashlib.sha256(url.encode()).hexdigest()[:24]}.svg"
    if kept.is_file() and not kept.is_symlink():
        return kept.read_bytes()
    req = urllib.request.Request(url, headers={"User-Agent": "make-shapes/1", "Accept": "image/svg+xml"})
    with urllib.request.urlopen(req, timeout=30) as res:
        body = res.read(200_000)
    if kept.is_symlink():
        raise ShapesError(f"{kept} is a link, so nothing was kept there.")
    kept.write_bytes(body)
    return body


def colour_of(said: str) -> str:
    """A fill as the picture keeps it, a stand-in mapped to the app's own. Anything else stops the run."""
    c = (said or "").strip().lower()
    if c in COLOURS:
        return COLOURS[c]
    raise ShapesError(f"a colour this does not expect, {said!r}")


def checked(transform: str) -> str:
    if not TRANSFORM.fullmatch(transform or ""):
        raise ShapesError("a transform this does not expect")
    return transform.strip()


def left_out(parts: list[tuple[str, str, float]]) -> str:
    """Why a picture is left out of the set, or "": two lines crossing read as an X, and a small triangle, filled
    or in outline, as the second or third shape reads as a play button."""
    lines = [turn for _shape, kind, turn in parts if kind == "line"]
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            if 25 < abs(lines[i] - lines[j]) % 180 < 155:
                return "two lines crossing"
    if any(kind in ("polygon", "polygonFilled") and shape != "shape01" for shape, kind, _turn in parts):
        return "a small triangle"
    return ""


def clean(raw: bytes) -> str:
    """The download drawn again: a white ground and its parts as groups of paths, in the app's colours."""
    if len(raw) > 150_000:
        raise ShapesError("a download over 150 KB")
    text = raw.decode("utf-8")
    if re.search(r"<!(DOCTYPE|ENTITY)|<\?xml-stylesheet", text, re.I):
        raise ShapesError("a download with a doctype, an entity or a stylesheet")
    root = ET.fromstring(text)
    if TAG.match(root.tag or "") is None or TAG.match(root.tag).group(1) != "svg" \
            or root.get("viewBox") != "0 0 100 100":
        raise ShapesError("a download that is not Shapes' 100 square")
    defs: dict[str, ET.Element] = {}
    body = None
    for child in root:
        name = (TAG.match(child.tag or "") or [None, None])[1] if isinstance(child.tag, str) else None
        if name == "defs":
            for d in child:
                dn = TAG.match(d.tag or "")
                if dn and dn.group(1) == "g" and PART.fullmatch(d.get("id") or ""):
                    defs[d.get("id")] = d
                elif not (dn and dn.group(1) == "clipPath"):
                    raise ShapesError(f"a part this does not expect in defs, {d.tag}")
        elif name == "g":
            if body is not None:
                raise ShapesError("two drawings in one download")
            body = child
        elif name not in ("metadata", "style"):
            raise ShapesError(f"a part this does not expect, {child.tag}")
    if body is None:
        raise ShapesError("a download with no drawing")
    if set(body.attrib) - {"clip-path"}:
        raise ShapesError("a drawing with more than its clip")

    def path_of(el: ET.Element) -> str:
        extra = set(el.attrib) - {"d", "fill", "fill-rule", "clip-rule"}
        if extra:
            raise ShapesError(f"a path with {sorted(extra)[0]}")
        d = el.get("d") or ""
        if not PATH_D.fullmatch(d):
            raise ShapesError("a path whose outline is not one")
        rule = el.get("fill-rule") or "nonzero"
        if rule not in RULES or (el.get("clip-rule") or "nonzero") not in RULES:
            raise ShapesError("a path with a fill rule this does not expect")
        return f'<path d="{d}" fill="{colour_of(el.get("fill") or "")}"' + (' fill-rule="evenodd"' if rule == "evenodd" else "") + "/>"

    def circle_of(el: ET.Element) -> str:
        """A filled circle written as a path of two arcs, so the file holds paths alone."""
        if set(el.attrib) - {"cx", "cy", "r", "fill"}:
            raise ShapesError("a circle with more than its centre, radius and fill")
        try:
            cx, cy, r = (float(el.get(k) or "0") for k in ("cx", "cy", "r"))
        except ValueError:
            raise ShapesError("a circle whose size is not a number")
        if not 0 < r <= 400:
            raise ShapesError("a circle of a size this does not expect")
        d = f"M{cx - r:g} {cy:g}a{r:g} {r:g} 0 1 0 {2 * r:g} 0a{r:g} {r:g} 0 1 0 {-2 * r:g} 0Z"
        return f'<path d="{d}" fill="{colour_of(el.get("fill") or "")}"/>'

    parts, out = [], []
    for c in body:
        kind = (TAG.match(c.tag or "") or [None, ""])[1]
        if kind == "rect":
            if colour_of(c.get("fill") or "") != WHITE:
                raise ShapesError("a ground that is not white")
            continue
        if kind != "use":
            raise ShapesError(f"a part this does not expect, {c.tag}")
        href = c.get("href") or c.get("{http://www.w3.org/1999/xlink}href") or ""
        if not HREF.fullmatch(href) or href[1:] not in defs or set(c.attrib) - {
                "href", "{http://www.w3.org/1999/xlink}href", "transform", "data-dicebear-component"}:
            raise ShapesError("a use that is not of a part in the download")
        part = defs[href[1:]]
        shape, variant = PART.fullmatch(href[1:]).groups()[:2]
        transform = checked(c.get("transform") or "")
        turn = ROTATE.search(transform)
        parts.append((shape, variant, float(turn.group(1)) if turn else 0.0))
        paths = []
        for p in part:
            el = (TAG.match(p.tag or "") or [None, ""])[1]
            if el == "circle":
                paths.append(circle_of(p))
            elif el == "path":
                paths.append(path_of(p))
            else:
                raise ShapesError(f"a part holding {p.tag}")
        out.append(f'<g transform="{transform}">{"".join(paths)}</g>')
    why = left_out(parts)
    if why:
        raise ShapesError(f"left out of the set: {why}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="{SIZE}" height="{SIZE}">'
            "<!-- Shapes by DiceBear, CC0 1.0, drawn in ink by packaging/make_shapes.py -->"
            f'<rect x="0" y="0" width="100" height="100" fill="{WHITE}"/>{"".join(out)}</svg>\n')


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fetch the Shapes set and write it in ink into static/faces.")
    ap.add_argument("--keep", help="a folder to keep the downloads in, read from there when a picture is already in it")
    ap.add_argument("--out", default=str(OUT), help="where the pictures are written, static/faces by default")
    ap.add_argument("--try", dest="tries", type=int, default=0,
                    help="list which of the seeds after SET's last the rule passes, up to this seed, and write nothing")
    a = ap.parse_args(argv)
    out = Path(a.out)
    with tempfile.TemporaryDirectory() as tmp:
        into = Path(a.keep) if a.keep else Path(tmp)
        into.mkdir(parents=True, exist_ok=True)
        if a.tries:
            passed = []
            for seed in range(max(SET) + 1, a.tries + 1):
                try:
                    clean(fetch(url_of(seed), into))
                    passed.append(seed)
                except ShapesError as e:
                    print(f"seed {seed:02d}: {e}")
            print("passed:", ", ".join(str(s) for s in passed))
            return 0
        made = {}
        for n, seed in enumerate(SET, start=1):
            try:
                made[f"shape{n:02d}"] = clean(fetch(url_of(seed), into))
            except (ShapesError, ET.ParseError, UnicodeDecodeError) as e:
                print(f"shape{n:02d} (seed {seed:02d}): {e}, so nothing was written.", file=sys.stderr)
                return 1
    out.mkdir(parents=True, exist_ok=True)
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
