#!/usr/bin/env python3
"""The Notionists set of pictures a participant can be given (picsets, 12 November 2026, Adam: "before long we're
going to need multiple sets because people may not like the style"). Forty head-and-shoulders line drawings from
Notionists, Zoish's hand-drawn library (CC0 1.0), each put together from explicit parts through DiceBear's
`notionists` style, already ink on paper, drawn again here in the app's ink on white and written as small SVG files
into `apps/idiograph/static/faces/notion01.svg` to `notion40.svg`. Run it again after a change to SET:

    python3 packaging/make_notionists.py                # fetch each picture, write the set
    python3 packaging/make_notionists.py --keep DIR     # keep the downloads in DIR, and read them from there next time

Made once and committed: the app never goes online for them. Each download is untrusted data. It is parsed, never
run, a file with a doctype or an entity is refused, and only the shapes expected are written: paths and groups, each
path's outline checked, each colour the ink or the paper the request asked for (anything else stops the run), every
picture framed alike for the circle the app draws. The clothes drawn with a mask or a stroke (variants 05 to 10) are
left out, so every file holds paths alone, as the Open Peeps do.
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
API = "https://api.dicebear.com/11.x/notionists/svg"
INK = "#2B2620"
WHITE = "#FFFFFF"
ASK = {"ink": "2b2620", "paper": "ffffff"}
# the window on Notionists' 1744 square every picture shares: head and shoulders, room above for the tallest hair
# in SET, the circle the app draws inscribed in it
VIEW = (322, 140, 1100, 1100)
SIZE = 64
# the clothes left out: each drawn with a mask or a stroke, which the files here never hold
CLOTHES_OUT = {f"variant{n:02d}" for n in range(5, 11)}

# Each picture: its hair (Notionists' `hat` or a variant's number), beard or None, glasses or None, clothes, mouth,
# eyes, eyebrows and nose, each a variant's number, then what it is, for the report. Chosen for range, never left
# to a seed: hair short, long, curly, tied up, white, a headscarf and a cap (no bald head, since Notionists draw no
# line over the top of one), beards and moustaches, clear glasses alone (variants 3, 8 and 11, never dark ones), every mouth calm (3, 4, 13,
# 17, 21, 22, 23, never an open smile), the eyes open or lidded (1, 4, 5), the brows at rest.
SET = [
    # (hair, beard, glasses, clothes, mouth, eyes, brows, nose, what)
    (2, None, None, 13, 3, 4, 5, 1, "shoulder-length hair"),
    (5, 2, None, 16, 22, 1, 9, 5, "short hair, full beard"),
    (62, None, None, 21, 22, 4, 1, 12, "headscarf"),
    (42, 3, 11, 14, 21, 1, 8, 18, "white hair, moustache, glasses, older"),
    (20, None, None, 23, 23, 5, 4, 7, "curly hair"),
    ("hat", None, None, 1, 17, 4, 9, 10, "cap"),
    (15, 1, None, 19, 4, 1, 2, 6, "short hair, goatee"),
    (61, None, 8, 11, 3, 4, 5, 13, "white hair, glasses, older"),
    (45, None, None, 22, 3, 5, 12, 16, "ponytail with fringe"),
    (13, None, 11, 20, 13, 4, 8, 4, "side parting, glasses"),
    (57, None, None, 12, 22, 1, 1, 20, "top knot"),
    (22, 7, None, 25, 21, 4, 9, 5, "short curls, moustache"),
    (63, None, 3, 13, 3, 1, 5, 1, "headscarf, glasses"),
    (41, None, None, 16, 17, 4, 4, 18, "long straight hair"),
    (42, 2, 11, 14, 21, 1, 8, 7, "white hair, full beard, glasses, older"),
    (59, None, None, 21, 23, 5, 12, 12, "two buns"),
    (1, 8, None, 17, 4, 4, 2, 10, "wavy hair, goatee"),
    (8, None, 8, 15, 23, 1, 1, 13, "long hair, headband, glasses"),
    (60, 10, None, 19, 13, 4, 9, 6, "cropped hair, moustache"),
    (33, None, None, 23, 22, 5, 4, 16, "curly top"),
    (10, None, None, 11, 3, 4, 5, 4, "long hair with fringe"),
    (35, 12, 8, 16, 17, 1, 8, 20, "quiff, small beard, glasses"),
    (58, None, None, 14, 21, 4, 12, 5, "bob"),
    (42, None, None, 25, 3, 5, 1, 18, "white hair, older"),
    (48, None, 11, 12, 3, 4, 5, 7, "messy bun, glasses"),
    (31, 2, None, 1, 22, 1, 9, 12, "short curls, full beard"),
    (39, None, None, 13, 23, 4, 4, 10, "low ponytail"),
    (9, None, None, 21, 13, 5, 12, 13, "curly hair, swept"),
    (24, 11, None, 20, 21, 4, 2, 1, "short hair, moustache and chin beard"),
    (23, None, 3, 15, 17, 1, 1, 16, "long wavy hair, glasses"),
    ("hat", 2, None, 17, 4, 4, 8, 6, "cap, full beard"),
    (11, None, None, 19, 22, 5, 5, 4, "curly bob"),
    (54, None, 11, 23, 3, 4, 9, 20, "swept hair, glasses"),
    (47, None, None, 22, 22, 4, 12, 5, "high ponytail"),
    (6, 3, None, 16, 13, 1, 8, 18, "short hair, big moustache"),
    (40, None, None, 11, 21, 5, 4, 7, "tousled curls"),
    (61, None, None, 12, 23, 1, 1, 12, "white hair, older"),
    (16, 9, 8, 13, 4, 4, 9, 10, "short hair, moustache, glasses"),
    (29, None, None, 14, 17, 5, 5, 13, "small bun"),
    (62, None, None, 25, 22, 5, 12, 16, "headscarf"),
]


def part(x) -> str | None:
    """A part as DiceBear names it: `hat`, a variant's number as `variant07`, or None for none."""
    return None if x is None else x if isinstance(x, str) else f"variant{int(x):02d}"

TAG = re.compile(r"\{http://www\.w3\.org/2000/svg\}([a-zA-Z]+)$")
PATH_D = re.compile(r"[MmLlHhVvCcSsQqTtAaZz0-9eE.,\s+-]{1,200000}")
TRANSFORM = re.compile(r"\s*((matrix|translate|scale)\([0-9eE.,\s+-]{1,200}\)\s*){1,4}")
HREF = re.compile(r"#[A-Za-z][\w-]{0,80}")
PART = re.compile(r"(head|clothes|hair|mouth|nose|eyes|eyebrows|beard|glasses)-(variant\d{2}|hat)-[0-9a-f]{1,16}")
RULES = {"evenodd", "nonzero"}


class NotionError(Exception):
    """A download that is not what this expects: nothing is written."""


def url_of(n: int, hair: str, beard: str | None, glasses: str | None, clothes: str, mouth: str, eyes: str,
           brows: str, nose: str) -> str:
    """The request for one picture, every part named, so the seed decides nothing."""
    if clothes in CLOTHES_OUT:
        raise NotionError(f"clothes {clothes} are drawn with a mask or a stroke")
    q = {"seed": f"notion{n:02d}", "hairVariant": hair, "hairProbability": 100, "beardProbability": 100 if beard else 0,
         "glassesProbability": 100 if glasses else 0, "gestureProbability": 0, "clothesGraphicProbability": 0,
         "clothesVariant": clothes, "mouthVariant": mouth, "eyesVariant": eyes, "eyebrowsVariant": brows,
         "noseVariant": nose, "inkColor": ASK["ink"], "paperColor": ASK["paper"]}
    if beard:
        q["beardVariant"] = beard
    if glasses:
        q["glassesVariant"] = glasses
    return f"{API}?{urllib.parse.urlencode(q)}"


def fetch(url: str, into: Path) -> bytes:
    """One download, kept in `into` under its request's hash and read from there when it is already there."""
    kept = into / f"{hashlib.sha256(url.encode()).hexdigest()[:24]}.svg"
    if kept.is_file() and not kept.is_symlink():
        return kept.read_bytes()
    req = urllib.request.Request(url, headers={"User-Agent": "make-notionists/1", "Accept": "image/svg+xml"})
    with urllib.request.urlopen(req, timeout=30) as res:
        body = res.read(600_000)
    if kept.is_symlink():
        raise NotionError(f"{kept} is a link, so nothing was kept there.")
    kept.write_bytes(body)
    return body


def colour_of(said: str) -> str:
    """A fill as the picture keeps it: the ink and the paper the request asked for, each the app's own. Anything
    else stops the run."""
    c = (said or "").strip().lower()
    if c == "#" + ASK["ink"]:
        return INK
    if c == "#" + ASK["paper"]:
        return WHITE
    if c == "none":
        return "none"
    raise NotionError(f"a colour this does not expect, {said!r}")


def checked(transform: str) -> str:
    if not TRANSFORM.fullmatch(transform or ""):
        raise NotionError("a transform this does not expect")
    return transform.strip()


def clean(raw: bytes, view: tuple = VIEW) -> str:
    """The download drawn again: its paths and groups alone, in ink and white, framed for the circle."""
    if len(raw) > 500_000:
        raise NotionError("a download over 500 KB")
    text = raw.decode("utf-8")
    if re.search(r"<!(DOCTYPE|ENTITY)|<\?xml-stylesheet", text, re.I):
        raise NotionError("a download with a doctype, an entity or a stylesheet")
    root = ET.fromstring(text)
    if TAG.match(root.tag or "") is None or TAG.match(root.tag).group(1) != "svg" \
            or root.get("viewBox") != "0 0 1744 1744":
        raise NotionError("a download that is not Notionists' 1744 square")
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
                    raise NotionError(f"a part this does not expect in defs, {d.tag}")
        elif name == "g":
            if body is not None:
                raise NotionError("two drawings in one download")
            body = child
        elif name != "metadata":
            raise NotionError(f"a part this does not expect, {child.tag}")
    if body is None:
        raise NotionError("a download with no drawing")

    def path_of(el: ET.Element) -> str:
        extra = set(el.attrib) - {"d", "fill", "fill-rule", "clip-rule"}
        if extra:
            raise NotionError(f"a path with {sorted(extra)[0]}")
        d = el.get("d") or ""
        if not PATH_D.fullmatch(d):
            raise NotionError("a path whose outline is not one")
        fill = colour_of(el.get("fill") or "")
        rule = el.get("fill-rule") or "nonzero"
        if rule not in RULES or (el.get("clip-rule") or "nonzero") not in RULES:
            raise NotionError("a path with a fill rule this does not expect")
        return f'<path d="{d}" fill="{fill}"' + (' fill-rule="evenodd"' if rule == "evenodd" else "") + "/>"

    def group_of(el: ET.Element, depth: int = 0) -> str:
        if depth > 4:
            raise NotionError("groups nested too deep")
        out = []
        for c in el:
            m = TAG.match(c.tag or "")
            kind = m.group(1) if m else ""
            if kind == "path":
                out.append(path_of(c))
            elif kind == "g":
                if set(c.attrib) - {"transform", "id"}:
                    raise NotionError("a group with more than a transform")
                inner = group_of(c, depth + 1)
                t = c.get("transform")
                out.append(f'<g transform="{checked(t)}">{inner}</g>' if t else inner)
            elif kind == "use" and el is body:
                href = c.get("href") or c.get("{http://www.w3.org/1999/xlink}href") or ""
                if not HREF.fullmatch(href) or href[1:] not in defs or set(c.attrib) - {
                        "href", "{http://www.w3.org/1999/xlink}href", "transform"}:
                    raise NotionError("a use that is not of a part in the download")
                inner = group_of(defs[href[1:]], depth + 1)
                t = c.get("transform")
                out.append(f'<g transform="{checked(t)}">{inner}</g>' if t else inner)
            else:
                raise NotionError(f"a part this does not expect, {c.tag}")
        return "".join(out)

    if set(body.attrib) - {"clip-path"}:
        raise NotionError("a drawing with more than its clip")
    drawing = group_of(body)
    x, y, w, h = view
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" width="{SIZE}" height="{SIZE}">'
            "<!-- Notionists by Zoish, CC0 1.0, through DiceBear, drawn in ink by packaging/make_notionists.py -->"
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{WHITE}"/>{drawing}</svg>\n')


def names() -> list[str]:
    return [f"notion{n:02d}" for n in range(1, len(SET) + 1)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fetch the Notionists set and write it in ink into static/faces.")
    ap.add_argument("--keep", help="a folder to keep the downloads in, read from there when a picture is already in it")
    ap.add_argument("--out", default=str(OUT), help="where the pictures are written, static/faces by default")
    a = ap.parse_args(argv)
    out = Path(a.out)
    with tempfile.TemporaryDirectory() as tmp:
        into = Path(a.keep) if a.keep else Path(tmp)
        into.mkdir(parents=True, exist_ok=True)
        made = {}
        for n, (*parts, _what) in enumerate(SET, start=1):
            hair = part(parts[0])
            try:
                raw = fetch(url_of(n, *(part(x) for x in parts)), into)
                made[f"notion{n:02d}"] = clean(raw)
            except (NotionError, ET.ParseError, UnicodeDecodeError) as e:
                print(f"notion{n:02d} ({hair}): {e}, so nothing was written.", file=sys.stderr)
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
