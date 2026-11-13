#!/usr/bin/env python3
"""The Fluent Emoji set of pictures a participant can be given (picsets, 12 November 2026, Adam: "more sets, a tab
each"). The people of Microsoft's Fluent Emoji (MIT) that suit a participant, adults' heads alone (varied hair,
older people, with and without beards, a headscarf and turbans; no smileys, gestures or professions), each its
High Contrast drawing recoloured to the app's ink on white and written as small SVG files into
`apps/idiograph/static/faces/fluent01.svg` onwards. Run it again after a change to SET:

    python3 packaging/make_fluent.py                # fetch each picture, write the set
    python3 packaging/make_fluent.py --keep DIR     # keep the downloads in DIR, and read them from there next time

Made once and committed: the app never goes online for them. They are fetched from the Fluent Emoji repository at
one commit, COMMIT, so a run again draws the same pictures. Each download is untrusted data. It is parsed, never
run, a file with a doctype or an entity is refused, and only the shapes expected are written: paths, each path's
outline checked, each colour the High Contrast drawing's one dark (anything else stops the run), every picture
framed alike for the circle the app draws. MIT asks that its copyright and permission notice go with the pictures:
NOTICE.md carries it in full, and `LICENSE-fluent-emoji.txt` beside the pictures.
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
REPO = "https://raw.githubusercontent.com/microsoft/fluentui-emoji"
# the repository's main at 24 August 2026, the commit every picture is fetched from
COMMIT = "1ffb34c752ecf5d402f04cfb4b392c77f57c54bc"
INK = "#2B2620"
WHITE = "#FFFFFF"
# the High Contrast drawings' one dark, which a few name black, drawn here in the app's ink
DARKS = {"#212121", "BLACK", "#000000", "#000"}
# the window on the emoji's 32 square every picture shares: a little room round the head, so the circle the app
# draws cuts no hair at the sides and no shoulders of a headscarf at the foot
VIEW = (-2.5, -2.5, 37, 37)
SIZE = 64
# the repository's licence, kept beside the pictures
LICENCE = "LICENSE-fluent-emoji.txt"

# Each picture: the emoji's name in the repository, then what it is, for the report. Chosen for range: a person,
# a woman and a man each with dark, light and curly hair, a bald woman and man, older people, a headscarf, a woman's
# and a man's turban and three beards. Left out, since in ink each draws as one here again: red hair (the dark
# hair's drawing), white hair (the light hair's) and the third bald head and turban (a line of lashes or brows
# apart). The skullcap is left out with its jacket.
SET = [
    ("Person", "person, dark hair"),
    ("Woman", "woman, dark hair"),
    ("Man", "man, dark hair"),
    ("Person blonde hair", "person, light hair"),
    ("Woman blonde hair", "woman, light hair"),
    ("Man blonde hair", "man, light hair"),
    ("Person curly hair", "person, curly hair"),
    ("Woman curly hair", "woman, curly hair"),
    ("Man curly hair", "man, curly hair"),
    ("Woman bald", "woman, bald"),
    ("Man bald", "man, bald"),
    ("Older person", "older person"),
    ("Old woman", "older woman"),
    ("Old man", "older man"),
    ("Woman with headscarf", "woman, headscarf"),
    ("Woman wearing turban", "woman, turban"),
    ("Man wearing turban", "man, turban"),
    ("Person beard", "person, beard"),
    ("Man beard", "man, beard"),
    ("Woman beard", "long hair, beard"),
]

TAG = re.compile(r"\{http://www\.w3\.org/2000/svg\}([a-zA-Z]+)$")
PATH_D = re.compile(r"[MmLlHhVvCcSsQqTtAaZz0-9eE.,\s+-]{1,200000}")
NAME = re.compile(r"[A-Z][a-z]+( [a-z]+){0,4}")
RULES = {"evenodd", "nonzero"}


class FluentError(Exception):
    """A download that is not what this expects: nothing is written."""


def url_of(name: str) -> str:
    """The High Contrast drawing of one emoji at COMMIT, by the repository's own naming of its files."""
    if not NAME.fullmatch(name):
        raise FluentError(f"a name this does not expect, {name!r}")
    stem = name.lower().replace(" ", "_")
    return (f"{REPO}/{COMMIT}/assets/{urllib.parse.quote(name)}/Default/High%20Contrast/"
            f"{stem}_high_contrast_default.svg")


def fetch(url: str, into: Path) -> bytes:
    """One download, kept in `into` under its request's hash and read from there when it is already there."""
    kept = into / f"{hashlib.sha256(url.encode()).hexdigest()[:24]}.svg"
    if kept.is_file() and not kept.is_symlink():
        return kept.read_bytes()
    req = urllib.request.Request(url, headers={"User-Agent": "make-fluent/1", "Accept": "image/svg+xml"})
    with urllib.request.urlopen(req, timeout=30) as res:
        body = res.read(600_000)
    if kept.is_symlink():
        raise FluentError(f"{kept} is a link, so nothing was kept there.")
    kept.write_bytes(body)
    return body


def clean(raw: bytes, view: tuple = VIEW) -> str:
    """The download drawn again: its paths alone, in ink on white, framed for the circle."""
    if len(raw) > 500_000:
        raise FluentError("a download over 500 KB")
    text = raw.decode("utf-8")
    if re.search(r"<!(DOCTYPE|ENTITY)|<\?xml-stylesheet", text, re.I):
        raise FluentError("a download with a doctype, an entity or a stylesheet")
    root = ET.fromstring(text)
    m = TAG.match(root.tag or "")
    if m is None or m.group(1) != "svg" or root.get("viewBox") != "0 0 32 32" \
            or set(root.attrib) - {"width", "height", "viewBox", "fill"}:
        raise FluentError("a download that is not a Fluent Emoji's 32 square")
    kind = lambda el: (TAG.match(el.tag or "") or [None, ""])[1] if isinstance(el.tag, str) else ""
    # a drawing may sit in one group clipped to its own 32 square, which cuts nothing: the group is let go and
    # its paths drawn as the others are
    whole = set()
    for el in root:
        if kind(el) == "defs":
            for cp in el:
                rects = list(cp)
                if kind(cp) != "clipPath" or not re.fullmatch(r"[\w-]{1,60}", cp.get("id") or "") or len(rects) != 1 \
                        or kind(rects[0]) != "rect" or len(rects[0]) \
                        or {k: v for k, v in rects[0].attrib.items() if k != "fill"} != {"width": "32", "height": "32"}:
                    raise FluentError("a clip this does not expect")
                whole.add(cp.get("id"))
    drawn = []
    for el in root:
        if kind(el) == "g":
            if set(el.attrib) != {"clip-path"} or el.get("clip-path")[5:-1] not in whole \
                    or not re.fullmatch(r"url\(#[\w-]{1,60}\)", el.get("clip-path")):
                raise FluentError("a group this does not expect")
            drawn.extend(el)
        elif kind(el) != "defs":
            drawn.append(el)
    paths = []
    for el in drawn:
        if kind(el) != "path":
            raise FluentError(f"a part this does not expect, {el.tag}")
        if set(el.attrib) - {"d", "fill", "fill-rule", "clip-rule"} or len(el):
            raise FluentError("a path with more than an outline and a fill")
        d = el.get("d") or ""
        if not PATH_D.fullmatch(d):
            raise FluentError("a path whose outline is not one")
        if (el.get("fill") or "").strip().upper() not in DARKS:
            raise FluentError(f"a colour this does not expect, {el.get('fill')!r}")
        rule = el.get("fill-rule") or "nonzero"
        if rule not in RULES or (el.get("clip-rule") or "nonzero") not in RULES:
            raise FluentError("a path with a fill rule this does not expect")
        paths.append(f'<path d="{d}" fill="{INK}"' + (' fill-rule="evenodd"' if rule == "evenodd" else "") + "/>")
    if not paths:
        raise FluentError("a download with no drawing")
    x, y, w, h = view
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" width="{SIZE}" height="{SIZE}">'
            "<!-- Fluent Emoji, Copyright (c) Microsoft Corporation, MIT License (NOTICE.md and"
            " LICENSE-fluent-emoji.txt), drawn in ink by packaging/make_fluent.py -->"
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{WHITE}"/>{"".join(paths)}</svg>\n')


def licence(raw: bytes) -> str:
    """The repository's LICENSE at COMMIT, kept beside the pictures as MIT asks: plain words, the MIT License with
    Microsoft's copyright, or the run stops."""
    text = raw.decode("utf-8")
    if len(raw) > 5000 or "<" in text or not re.search(r"^\s*MIT License\s*$", text, re.M) \
            or "Copyright (c) Microsoft Corporation." not in text or "Permission is hereby granted" not in text:
        raise FluentError("a LICENSE that is not the MIT License with Microsoft's copyright")
    return text.rstrip() + "\n"


def names() -> list[str]:
    return [f"fluent{n:02d}" for n in range(1, len(SET) + 1)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fetch the Fluent Emoji set and write it in ink into static/faces.")
    ap.add_argument("--keep", help="a folder to keep the downloads in, read from there when a picture is already in it")
    ap.add_argument("--out", default=str(OUT), help="where the pictures are written, static/faces by default")
    a = ap.parse_args(argv)
    out = Path(a.out)
    with tempfile.TemporaryDirectory() as tmp:
        into = Path(a.keep) if a.keep else Path(tmp)
        into.mkdir(parents=True, exist_ok=True)
        made = {}
        for n, (name, _what) in enumerate(SET, start=1):
            try:
                made[f"fluent{n:02d}.svg"] = clean(fetch(url_of(name), into))
            except (FluentError, ET.ParseError, UnicodeDecodeError) as e:
                print(f"fluent{n:02d} ({name}): {e}, so nothing was written.", file=sys.stderr)
                return 1
        try:
            made[LICENCE] = licence(fetch(f"{REPO}/{COMMIT}/LICENSE", into))
        except (FluentError, UnicodeDecodeError) as e:
            print(f"LICENSE: {e}, so nothing was written.", file=sys.stderr)
            return 1
    out.mkdir(parents=True, exist_ok=True)
    for name, body in made.items():
        target = out / name
        if target.is_symlink():
            print(f"{target} is a link, so nothing was written there.", file=sys.stderr)
            return 1
        target.write_text(body, encoding="utf-8", newline="\n")
    print(f"{len(made) - 1} pictures and {LICENCE} in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
