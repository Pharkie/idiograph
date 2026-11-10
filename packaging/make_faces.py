#!/usr/bin/env python3
"""The set of pictures a participant can be given on the Trajectories screen (trajbuild2, 10 November 2026):
twenty-four drawn line portraits, head and shoulders in ink on white, written as small SVG files into
`apps/idiograph/static/faces/face01.svg` to `face24.svg`. They are drawn here, for Idiograph, and are under
its own licence (NOTICE.md). Each is a pairing of one of eight heads of hair with one of three finishes
(none, glasses, a beard or earrings), so no two are alike. Run it again after a change:

    python3 packaging/make_faces.py
"""
from __future__ import annotations

from pathlib import Path

INK = "#2B2620"
SHADE = "#8A8178"
OUT = Path(__file__).resolve().parent.parent / "apps" / "idiograph" / "static" / "faces"

# each head of hair: the hair behind the face (drawn first) and over it (drawn after), its fill ink or grey
HAIR = [
    ("short", "", '<path d="M21 27c0-9 5-14 11-14s11 5 11 14c-2-5-6-8-11-8s-9 3-11 8z" fill="{ink}"/>'),
    ("bob", '<path d="M19 38c-2-14 3-25 13-25s15 11 13 25h-5V27H24v11z" fill="{ink}"/>',
     '<path d="M22 27c2-6 6-9 10-9s8 3 10 9c-4-3-7-4-10-4s-6 1-10 4z" fill="{ink}"/>'),
    ("long", '<path d="M17 48c-1-21 3-35 15-35s16 14 15 35l-6-4V28H23v16z" fill="{ink}"/>',
     '<path d="M22 28c1-7 5-11 10-11s9 4 10 11c-3-4-6-5-10-5s-7 1-10 5z" fill="{ink}"/>'),
    ("bun", '<circle cx="32" cy="10" r="5" fill="{ink}"/>',
     '<path d="M21 27c0-8 5-13 11-13s11 5 11 13c-3-4-7-6-11-6s-8 2-11 6z" fill="{ink}"/>'),
    ("curly", '<path d="M19 30c-3-4-1-9 2-10-1-4 3-8 7-7 2-3 7-3 9 0 4-1 8 3 7 7 3 1 5 6 2 10z" fill="{ink}"/>', ""),
    ("bald", "", '<path d="M23 25c1-6 5-10 9-10s8 4 9 10" fill="none" stroke="{ink}" stroke-width="1.6"/>'),
    ("ponytail", '<path d="M42 22c6 1 8 8 6 16-2-3-4-5-6-6z" fill="{ink}"/>',
     '<path d="M21 27c0-9 5-14 11-14s11 5 11 14c-3-5-7-7-11-7s-8 2-11 7z" fill="{ink}"/>'),
    ("grey", '<path d="M20 31c-1-11 4-18 12-18s13 7 12 18l-3-1V26H23v4z" fill="{grey}"/>',
     '<path d="M22 27c1-6 5-10 10-10s9 4 10 10c-3-3-6-5-10-5s-7 2-10 5z" fill="{grey}"/>'),
]

FINISH = {
    "none": "",
    "glasses": ('<g fill="none" stroke="{ink}" stroke-width="1.4"><circle cx="27.5" cy="29" r="3.2"/>'
                '<circle cx="36.5" cy="29" r="3.2"/><path d="M30.7 29h2.6"/></g>'),
    "beard": '<path d="M24 32c1 7 4 10 8 10s7-3 8-10c-2 3-5 4-8 4s-6-1-8-4z" fill="{ink}"/>',
    "earrings": '<circle cx="21.5" cy="34" r="1.3" fill="{ink}"/><circle cx="42.5" cy="34" r="1.3" fill="{ink}"/>',
}


def face(hair: tuple, finish: str) -> str:
    """One portrait: shoulders, neck, the hair behind, the face, its eyes and mouth, the hair over it, then its
    finish, every line in ink."""
    _name, back, front = hair
    fill = {"ink": INK, "grey": SHADE}
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="5 7 54 54" width="64" height="64">',
        '<rect width="64" height="64" fill="#FFFFFF"/>',
        back.format(**fill),
        f'<path d="M10 64c1-11 9-17 22-17s21 6 22 17" fill="#FFFFFF" stroke="{INK}" stroke-width="1.6"/>',
        f'<path d="M28 41v6c1 2 7 2 8 0v-6" fill="#FFFFFF" stroke="{INK}" stroke-width="1.6"/>',
        f'<ellipse cx="32" cy="29" rx="10" ry="12" fill="#FFFFFF" stroke="{INK}" stroke-width="1.6"/>',
        f'<circle cx="27.8" cy="29" r="1.1" fill="{INK}"/><circle cx="36.2" cy="29" r="1.1" fill="{INK}"/>',
        f'<path d="M29 35.5c2 1.4 4 1.4 6 0" fill="none" stroke="{INK}" stroke-width="1.4" stroke-linecap="round"/>',
        front.format(**fill),
        FINISH[finish].format(**fill),
        "</svg>",
    ]
    return "".join(p for p in parts if p) + "\n"


def faces() -> list[str]:
    """The twenty-four, each head of hair with no finish, then with glasses, then with a beard or earrings."""
    out = []
    for third in ("none", "glasses", "beard"):
        for n, hair in enumerate(HAIR):
            finish = third
            if third == "beard" and hair[0] in ("bob", "long", "bun", "ponytail"):
                finish = "earrings"
            out.append(face(hair, finish))
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for n, svg in enumerate(faces(), start=1):
        (OUT / f"face{n:02d}.svg").write_text(svg, encoding="utf-8", newline="\n")
    print(f"{len(faces())} pictures in {OUT}")


if __name__ == "__main__":
    main()
