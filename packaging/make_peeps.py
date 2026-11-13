#!/usr/bin/env python3
"""The set of pictures a participant can be given (peeps, 12 November 2026, Adam: "the pictures should be black and
white if not line drawings", from Open Peeps). Forty head-and-shoulders portraits from Open Peeps, Pablo Stanley's
hand-drawn library (CC0 1.0), each put together from explicit parts through DiceBear's `open-peeps` style and drawn
again here in the app's ink on white, written as small SVG files into `apps/idiograph/static/faces/peep01.svg` to
`peep40.svg`. Run it again after a change to SET:

    python3 packaging/make_peeps.py                # fetch each picture, write the set
    python3 packaging/make_peeps.py --keep DIR     # keep the downloads in DIR, and read them from there next time

Made once and committed: the app never goes online for them. Each download is untrusted data. It is parsed, never
run, a file with a doctype or an entity is refused, and only the shapes expected are written: paths and groups, each
path's outline checked, each colour one the request asked for or Open Peeps' own black or white (anything else stops
the run), every picture framed alike for the circle the app draws. Skin is left white, the face drawn by its outline
alone, with no skin colour, as Adam asked. The set before, `face01` to `face24`, drawn by the
`make_faces.py` this replaces, is kept by name in `trajectories.FACES_BEFORE`, each mapped to its nearest here.
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
API = "https://api.dicebear.com/11.x/open-peeps/svg"
INK = "#2B2620"
WHITE = "#FFFFFF"
# grey hair and a grey top, a warm light grey that reads as grey beside the ink and as white beside nothing
GREY = "#C9C2B8"
TONES = {"ink": INK, "grey": GREY, "white": WHITE}
# the colours the request asks for, each a stand-in the drawing is recoloured from: the outlines, the skin (left
# white), the clothing (a top, and a headscarf, turban, beanie or hair tie), the second hair colour (grey hair, a
# beard's grey, fair hair)
ASK = {"ink": "2b2620", "skin": "ffffff", "clothing": "0000fe", "contrast": "00fe00"}
# the window on Open Peeps' 704 square every picture shares: head and shoulders, the face a little right of centre
# as Open Peeps turns it, room above for the tallest hair in SET, the circle the app draws inscribed in it
VIEW = (45, 0, 710, 710)
SIZE = 64

# Each picture: its hair (Open Peeps' head), its expression, facial hair or None, glasses or None, then the tone of
# its second hair colour, of its top and of a headscarf, turban or beanie, and what it is, for the report. Chosen
# for range, never left to a seed: ages from about twenty to about eighty, women and men and some either way, hair
# short, long, curly, afro, locs, braids, bun, bald, grey, a headscarf, a turban and a beanie, beards and
# moustaches, clear glasses on some, every expression calm.
SET = [
    # (head, expression, facial hair, glasses, second hair colour, top, headscarf or turban, what)
    ("long", "smile", None, None, "ink", "grey", "white", "long hair"),
    ("short2", "smile", None, None, "ink", "white", "white", "short hair"),
    ("afro", "smile", None, None, "ink", "white", "white", "afro"),
    ("grayShort", "smile", None, "glasses", "grey", "ink", "white", "grey short hair, glasses, older"),
    ("hijab", "smile", None, None, "ink", "grey", "white", "headscarf"),
    ("turban", "calm", "full", None, "ink", "white", "white", "turban, full beard"),
    ("grayBun", "smile", None, "glasses3", "grey", "white", "white", "grey bun, glasses, older"),
    ("dreads1", "calm", None, None, "ink", "grey", "white", "curly locs"),
    ("short3", "smile", "chin", None, "ink", "white", "white", "short hair, short beard"),
    ("longCurly", "smile", None, None, "ink", "white", "white", "long curly hair"),
    ("hatBeanie", "calm", "goatee2", None, "ink", "white", "grey", "beanie, goatee"),
    ("grayMedium", "smile", None, None, "grey", "grey", "white", "grey hair, older"),
    ("cornrows", "smile", None, None, "ink", "grey", "white", "braided ponytail"),
    ("noHair1", "smile", "full2", None, "ink", "grey", "white", "bald, full beard"),
    ("mediumStraight", "serious", None, "glasses4", "ink", "white", "white", "straight hair, glasses"),
    ("bantuKnots", "smile", None, None, "ink", "white", "white", "bantu knots"),
    ("shaved2", "serious", "full3", None, "ink", "grey", "white", "short hair, big beard"),
    ("bangs", "smile", None, "glasses2", "grey", "white", "white", "grey bob with fringe, glasses, older"),
    ("pomp", "smile", None, "glasses", "ink", "white", "white", "quiff, glasses"),
    ("twists", "calm", None, None, "ink", "grey", "white", "twists"),
    ("noHair2", "old", "moustache9", "glasses5", "grey", "white", "white", "bald, grey moustache, glasses, older"),
    ("medium2", "smile", None, None, "ink", "white", "white", "flicked bob"),
    ("buns", "smile", None, None, "ink", "grey", "white", "two buns"),
    ("short1", "calm", None, None, "ink", "ink", "white", "short hair"),
    ("hijab", "calm", None, "glasses2", "ink", "white", "grey", "headscarf, glasses"),
    ("grayShort", "serious", "full4", None, "grey", "grey", "white", "grey hair and beard, older"),
    ("mediumBangs", "calm", None, None, "ink", "white", "white", "bob with fringe"),
    ("flatTop", "smile", None, None, "ink", "grey", "white", "flat top"),
    ("cornrows2", "calm", None, None, "ink", "white", "white", "long braids"),
    ("short4", "smile", None, None, "grey", "white", "white", "fair quiff"),
    ("longBangs", "smile", None, None, "ink", "white", "white", "long hair with fringe"),
    ("noHair3", "smile", None, None, "grey", "ink", "white", "bald, grey at the back, older"),
    ("medium3", "serious", None, "glasses", "ink", "grey", "white", "shoulder-length hair, glasses"),
    ("turban", "smile", "full4", "glasses5", "grey", "grey", "white", "turban, grey beard, glasses, older"),
    ("mediumBangs2", "smile", None, None, "grey", "white", "white", "fair wavy hair"),
    ("short5", "smile", "full", None, "ink", "white", "white", "short curly hair, beard"),
    ("dreads2", "smile", None, "glasses2", "ink", "white", "white", "short curls, glasses"),
    ("grayBun", "calm", None, None, "ink", "grey", "white", "bun"),
    ("mediumBangs3", "calm", None, None, "ink", "white", "white", "ponytail with fringe"),
    ("shaved1", "calm", "moustache6", None, "ink", "white", "white", "short hair, moustache"),
    # Forty more (picsets, 12 November 2026), widening what the first forty left thin: older faces, bald heads,
    # headscarves, turbans, hats, afros, locs and twists, beards and moustaches, glasses and dark tops, and the
    # heads the first forty left out that fit the circle (a brimmed hat, a high top, a blunt bob, a short bob, twists
    # and tousled hair). The big afro and the two buns with a bow or a curl on top are left out: the circle cuts them.
    ("grayShort", "old", "moustache9", None, "grey", "white", "white", "grey short hair, grey moustache, older"),
    ("hijab", "smile", None, None, "ink", "ink", "grey", "grey headscarf"),
    ("afro", "smile", "full", None, "ink", "grey", "white", "afro, beard"),
    ("noHair1", "old", None, "glasses2", "ink", "white", "white", "bald, glasses, older"),
    ("hatHip", "calm", None, None, "ink", "grey", "white", "brimmed hat"),
    ("bangs2", "smile", None, None, "ink", "white", "white", "blunt bob with fringe"),
    ("grayMedium", "old", None, "glasses4", "grey", "ink", "white", "grey hair, glasses, older"),
    ("dreads1", "calm", "full", None, "ink", "white", "white", "curly locs, beard"),
    ("bantuKnots", "calm", None, "glasses", "ink", "grey", "white", "bantu knots, glasses"),
    ("turban", "calm", "moustache6", None, "ink", "white", "grey", "grey turban, moustache"),
    ("noHair2", "smile", "full4", None, "grey", "grey", "white", "bald, grey beard, older"),
    ("medium1", "calm", None, "glasses", "ink", "white", "white", "short bob, glasses"),
    ("twists2", "smile", "goatee1", None, "ink", "grey", "white", "twists, goatee"),
    ("grayBun", "old", None, None, "grey", "ink", "white", "grey bun, older"),
    ("afro", "calm", None, "glasses3", "ink", "white", "white", "afro, glasses"),
    ("flatTopLong", "serious", None, None, "ink", "grey", "white", "high top"),
    ("hijab", "old", None, "glasses5", "ink", "grey", "white", "headscarf, glasses, older"),
    ("short2", "calm", "moustache7", "glasses2", "ink", "white", "white", "short hair, moustache, glasses"),
    ("mediumBangs3", "smile", None, "glasses5", "ink", "ink", "white", "ponytail with fringe, glasses"),
    ("shaved3", "calm", None, None, "ink", "grey", "white", "tousled hair"),
    ("hatBeanie", "smile", None, "glasses4", "ink", "ink", "white", "beanie, glasses"),
    ("mediumBangs2", "old", None, "glasses3", "grey", "white", "white", "grey wavy hair, glasses, older"),
    ("noHair1", "serious", "goatee2", None, "ink", "ink", "white", "bald, goatee"),
    ("cornrows2", "smile", None, "glasses2", "ink", "grey", "white", "long braids, glasses"),
    ("grayShort", "smile", "full", "glasses3", "grey", "white", "white", "grey hair, dark beard, glasses"),
    ("long", "calm", None, "glasses5", "ink", "ink", "white", "long hair, glasses"),
    ("turban", "smile", None, None, "ink", "grey", "white", "turban"),
    ("dreads2", "calm", "chin", None, "ink", "grey", "white", "short curls, short beard"),
    ("bangs", "smile", None, None, "ink", "white", "white", "dark bob with fringe"),
    ("short4", "old", "full4", "glasses", "grey", "grey", "white", "grey quiff, grey beard, glasses, older"),
    ("mediumStraight", "smile", None, None, "ink", "grey", "white", "straight hair"),
    ("hatHip", "smile", "full2", None, "ink", "white", "white", "brimmed hat, beard"),
    ("bangs", "old", None, None, "grey", "ink", "white", "grey bob with fringe, older"),
    ("longCurly", "calm", None, "glasses4", "ink", "grey", "white", "long curly hair, glasses"),
    ("noHair2", "calm", None, None, "ink", "white", "white", "bald"),
    ("pomp", "serious", "full2", None, "ink", "grey", "white", "quiff, beard"),
    ("medium2", "old", None, "glasses4", "ink", "grey", "white", "flicked bob, glasses, older"),
    ("short5", "calm", None, "glasses5", "ink", "grey", "white", "short curly hair, glasses"),
    ("mediumBangs", "old", None, "glasses", "ink", "grey", "white", "bob with fringe, glasses, older"),
    ("short1", "smile", "goatee2", "glasses4", "ink", "grey", "white", "short hair, goatee, glasses"),
]

TAG = re.compile(r"\{http://www\.w3\.org/2000/svg\}([a-zA-Z]+)$")
PATH_D = re.compile(r"[MmLlHhVvCcSsQqTtAaZz0-9eE.,\s+-]{1,200000}")
TRANSFORM = re.compile(r"\s*((matrix|translate|scale)\([0-9eE.,\s+-]{1,200}\)\s*){1,4}")
HREF = re.compile(r"#[A-Za-z][\w-]{0,80}")
PART = re.compile(r"(head|expression|facialHair|accessories|mask)-[\w-]+")
RULES = {"evenodd", "nonzero"}


class PeepError(Exception):
    """A download that is not what this expects: nothing is written."""


def url_of(n: int, head: str, expression: str, beard: str | None, glasses: str | None) -> str:
    """The request for one picture, every part named, so the seed decides nothing."""
    q = {"seed": f"peep{n:02d}", "headVariant": head, "expressionVariant": expression,
         "facialHairProbability": 100 if beard else 0, "accessoriesProbability": 100 if glasses else 0,
         "maskProbability": 0, "inkColor": ASK["ink"], "skinColor": ASK["skin"],
         "clothingColor": ASK["clothing"], "headContrastColor": ASK["contrast"]}
    if beard:
        q["facialHairVariant"] = beard
    if glasses:
        q["accessoriesVariant"] = glasses
    return f"{API}?{urllib.parse.urlencode(q)}"


def fetch(url: str, into: Path) -> bytes:
    """One download, kept in `into` under its request's hash and read from there when it is already there."""
    kept = into / f"{hashlib.sha256(url.encode()).hexdigest()[:24]}.svg"
    if kept.is_file() and not kept.is_symlink():
        return kept.read_bytes()
    req = urllib.request.Request(url, headers={"User-Agent": "make-peeps/1", "Accept": "image/svg+xml"})
    with urllib.request.urlopen(req, timeout=30) as res:
        body = res.read(600_000)
    if kept.is_symlink():
        raise PeepError(f"{kept} is a link, so nothing was kept there.")
    kept.write_bytes(body)
    return body


def colour_of(said: str, part: str, contrast: str, top: str, cover: str) -> str:
    """A fill as the picture keeps it: the stand-ins the request asked for, and Open Peeps' own black and white,
    each to ink, white or grey. Anything else stops the run."""
    c = (said or "").strip().lower()
    if c in ("#" + ASK["ink"], "#000000", "#000"):
        return INK
    if c in ("#" + ASK["skin"], "#fff"):
        return WHITE
    if c == "#" + ASK["clothing"]:
        return TONES[cover if part == "head" else top]
    if c == "#" + ASK["contrast"]:
        return TONES[contrast]
    if c == "none":
        return "none"
    raise PeepError(f"a colour this does not expect, {said!r}")


def clean(raw: bytes, contrast: str, top: str, cover: str) -> str:
    """The download drawn again: its paths and groups alone, in ink, white and grey, framed for the circle."""
    if len(raw) > 500_000:
        raise PeepError("a download over 500 KB")
    text = raw.decode("utf-8")
    if re.search(r"<!(DOCTYPE|ENTITY)|<\?xml-stylesheet", text, re.I):
        raise PeepError("a download with a doctype, an entity or a stylesheet")
    root = ET.fromstring(text)
    if TAG.match(root.tag or "") is None or TAG.match(root.tag).group(1) != "svg" \
            or root.get("viewBox") != "0 0 704 704":
        raise PeepError("a download that is not Open Peeps' 704 square")
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
                    raise PeepError(f"a part this does not expect in defs, {d.tag}")
        elif name == "g":
            if body is not None:
                raise PeepError("two drawings in one download")
            body = child
        elif name != "metadata":
            raise PeepError(f"a part this does not expect, {child.tag}")
    if body is None:
        raise PeepError("a download with no drawing")

    def path_of(el: ET.Element, part: str) -> str:
        extra = set(el.attrib) - {"d", "fill", "fill-rule", "clip-rule"}
        if extra:
            raise PeepError(f"a path with {sorted(extra)[0]}")
        d = el.get("d") or ""
        if not PATH_D.fullmatch(d):
            raise PeepError("a path whose outline is not one")
        fill = colour_of(el.get("fill") or "", part, contrast, top, cover)
        rule = el.get("fill-rule") or "nonzero"
        if rule not in RULES or (el.get("clip-rule") or "nonzero") not in RULES:
            raise PeepError("a path with a fill rule this does not expect")
        return f'<path d="{d}" fill="{fill}"' + (' fill-rule="evenodd"' if rule == "evenodd" else "") + "/>"

    def group_of(el: ET.Element, part: str, depth: int = 0) -> str:
        if depth > 4:
            raise PeepError("groups nested too deep")
        out = []
        for c in el:
            m = TAG.match(c.tag or "")
            kind = m.group(1) if m else ""
            if kind == "path":
                out.append(path_of(c, part))
            elif kind == "g":
                if set(c.attrib) - {"transform", "id"}:
                    raise PeepError("a group with more than a transform")
                inner = group_of(c, part, depth + 1)
                t = c.get("transform")
                out.append(f'<g transform="{checked(t)}">{inner}</g>' if t else inner)
            elif kind == "use" and depth == 0 and el is body:
                href = c.get("href") or c.get("{http://www.w3.org/1999/xlink}href") or ""
                if not HREF.fullmatch(href) or href[1:] not in defs or set(c.attrib) - {
                        "href", "{http://www.w3.org/1999/xlink}href", "transform"}:
                    raise PeepError("a use that is not of a part in the download")
                which = PART.fullmatch(href[1:]).group(1)
                inner = group_of(defs[href[1:]], which, depth + 1)
                t = c.get("transform")
                out.append(f'<g transform="{checked(t)}">{inner}</g>' if t else inner)
            else:
                raise PeepError(f"a part this does not expect, {c.tag}")
        return "".join(out)

    if set(body.attrib) - {"clip-path"}:
        raise PeepError("a drawing with more than its clip")
    drawing = group_of(body, "body")
    x, y, w, h = VIEW
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" width="{SIZE}" height="{SIZE}">'
            "<!-- Open Peeps by Pablo Stanley, CC0 1.0, through DiceBear, drawn in ink by packaging/make_peeps.py -->"
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{WHITE}"/>{drawing}</svg>\n')


def checked(transform: str) -> str:
    if not TRANSFORM.fullmatch(transform or ""):
        raise PeepError("a transform this does not expect")
    return transform.strip()


def names() -> list[str]:
    return [f"peep{n:02d}" for n in range(1, len(SET) + 1)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fetch the Open Peeps set and write it in ink into static/faces.")
    ap.add_argument("--keep", help="a folder to keep the downloads in, read from there when a picture is already in it")
    ap.add_argument("--out", default=str(OUT), help="where the pictures are written, static/faces by default")
    a = ap.parse_args(argv)
    out = Path(a.out)
    with tempfile.TemporaryDirectory() as tmp:
        into = Path(a.keep) if a.keep else Path(tmp)
        into.mkdir(parents=True, exist_ok=True)
        made = {}
        for n, (head, expression, beard, glasses, contrast, top, cover, _what) in enumerate(SET, start=1):
            raw = fetch(url_of(n, head, expression, beard, glasses), into)
            try:
                made[f"peep{n:02d}"] = clean(raw, contrast, top, cover)
            except (PeepError, ET.ParseError, UnicodeDecodeError) as e:
                print(f"peep{n:02d} ({head}): {e}, so nothing was written.", file=sys.stderr)
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
