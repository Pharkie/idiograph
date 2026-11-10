#!/usr/bin/env python3
"""The two pictures the installers show, drawn with the standard library from Idiograph's mark as
`make_app.py` draws the icon (18 October 2026, the fourth Tauri build), and committed beside the
window's source, so every build carries the same files.

    python3 packaging/tauri/draw_pictures.py          # writes both
    python3 packaging/tauri/draw_pictures.py --check  # says whether the committed files are as drawn

- `src-tauri/windows/sidebar.bmp`, the Windows installer's picture on its Welcome and Finish pages,
  164 by 314 as NSIS asks, the mark on the paper, where NSIS's stock blue picture stood (17 October,
  the third build's screenshots).
- `src-tauri/dmg/background.png` and `background@2x.png`, the Mac disk image's window, 660 by 400, the
  paper with an arrow from where Idiograph stands to where Applications stands, so the window says to
  drag the one onto the other with no words, where it had no layout and nothing said what to do.
"""
from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent.parent
sys.path.insert(0, str(TOOL))
import boot  # noqa: E402  the family's folders on the path (boot.py)
boot.setup()

import make_app  # noqa: E402  the mark and its colours

SIDEBAR = HERE / "src-tauri" / "windows" / "sidebar.bmp"
BACKGROUND = HERE / "src-tauri" / "dmg" / "background.png"
BACKGROUND_2X = HERE / "src-tauri" / "dmg" / "background@2x.png"
# the disk image's window and where its two icons stand, their centres, as packaging/tauri/bundle.py
# lays them out
WINDOW = (660, 400)
APP_AT = (180, 190)
APPLICATIONS_AT = (480, 190)
# the arrow between them, clear of both 128 pixel icons, in the ink's softer tone
ARROW = ((262, 190), (398, 190))
ARROW_INK = (0x8A, 0x80, 0x72)


def canvas(w: int, h: int, rgb) -> bytearray:
    return bytearray(bytes((*rgb, 255)) * (w * h))


def paint_mark(buf: bytearray, w: int, size: int, left: int, top: int) -> None:
    """The mark drawn at `size` pixels square into a canvas `w` wide, its top left at (left, top): the
    brackets and the dot, without the icon's tile, since the canvas is the paper already."""
    mark = bytearray(size * size * 4)
    for box, radius, rgb in make_app.SHAPES[1:]:
        make_app._paint(mark, size, box, radius, rgb)
    for y in range(size):
        for x in range(size):
            i = 4 * (y * size + x)
            a = mark[i + 3] / 255
            if a:
                make_app._over(buf, 4 * ((top + y) * w + left + x), tuple(mark[i:i + 3]), a)


def paint_arrow(buf: bytearray, w: int, scale: int) -> None:
    """A line and its head, from ARROW's first point to its second, at `scale`."""
    (x0, y), (x1, _) = ((p[0] * scale, p[1] * scale) for p in ARROW)
    half = 2 * scale
    head = 14 * scale
    for x in range(x0, x1 - head + 1):
        for yy in range(y - half, y + half):
            make_app._over(buf, 4 * (yy * w + x), ARROW_INK, 1.0)
    # the head, a triangle drawn row by row, its edges softened by a pixel's coverage
    for dy in range(-head, head + 1):
        reach = head - abs(dy)
        for dx in range(0, reach + 1):
            x = x1 - head + dx
            a = 1.0 if dx < reach else 0.5
            make_app._over(buf, 4 * ((y + dy) * w + x), ARROW_INK, a)


def png(w: int, h: int, rgba: bytes) -> bytes:
    stride = w * 4
    raw = b"".join(b"\x00" + bytes(rgba[y * stride:(y + 1) * stride]) for y in range(h))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def bmp(w: int, h: int, rgba: bytes) -> bytes:
    """A 24-bit BMP, its rows from the foot up, each padded to four bytes, as NSIS takes it."""
    pad = (4 - (w * 3) % 4) % 4
    rows = []
    for y in range(h - 1, -1, -1):
        row = bytearray()
        for x in range(w):
            i = 4 * (y * w + x)
            row += bytes((rgba[i + 2], rgba[i + 1], rgba[i]))
        rows.append(bytes(row) + b"\x00" * pad)
    pixels = b"".join(rows)
    info = struct.pack("<IiiHHIIiiII", 40, w, h, 1, 24, 0, len(pixels), 2835, 2835, 0, 0)
    head = struct.pack("<2sIHHI", b"BM", 14 + len(info) + len(pixels), 0, 0, 14 + len(info))
    return head + info + pixels


def sidebar() -> bytes:
    w, h = 164, 314
    buf = canvas(w, h, make_app.PAPER)
    size = 112
    paint_mark(buf, w, size, (w - size) // 2, 58)
    return bmp(w, h, buf)


def background(scale: int) -> bytes:
    w, h = WINDOW[0] * scale, WINDOW[1] * scale
    buf = canvas(w, h, make_app.PAPER)
    paint_arrow(buf, w, scale)
    return png(w, h, buf)


def pictures() -> dict[Path, bytes]:
    return {SIDEBAR: sidebar(), BACKGROUND: background(1), BACKGROUND_2X: background(2)}


def main(argv: list[str] | None = None) -> int:
    check = "--check" in (argv if argv is not None else sys.argv[1:])
    differ = []
    for path, data in pictures().items():
        if check:
            if not path.is_file() or path.read_bytes() != data:
                differ.append(path.name)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        print(f"Drew {path.relative_to(TOOL)}, {len(data)} bytes")
    if check:
        print("The pictures are as drawn." if not differ else f"Not as drawn: {', '.join(differ)}")
        return 1 if differ else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
