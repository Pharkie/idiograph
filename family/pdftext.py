"""A PDF's text and a reference's keys, read the same way by each of the family's apps (22 October 2026,
the family codebase's second build, from Sift's `sift_oa.py` and `sift_search.py`): a DOI and a title as
two records are matched by them, whether bytes are a PDF, and the text of a PDF's pages, read with the
standard library alone, the pages found through the catalogue's page tree, their content streams
inflated, their strings read through each font's ToUnicode map where it has one. Sift reads a download's
first page through here, and Trace a reference's pages.

The standard library and the family's `textfiles.py` only, and nothing here writes.
"""
from __future__ import annotations

import base64
import re
import unicodedata
import zlib

from textfiles import plain


# ------------------------------------------------------------------ the keys

def one_line(text) -> str:
    return " ".join(str(text or "").split())


def norm_doi(value) -> str:
    """A DOI as two records are compared by: lower case, with no address, `doi:` or spaces."""
    d = one_line(value).lower()
    d = re.sub(r"^(?:https?://)?(?:dx\.)?doi\.org/", "", d)
    d = re.sub(r"^doi:\s*", "", d)
    return d.strip().rstrip(".")


def norm_title(text) -> str:
    """A title as two are matched by: its letters and digits alone, folded, every space and stop gone."""
    return "".join(ch for ch in unicodedata.normalize("NFKC", plain(text)).casefold() if ch.isalnum())


def is_pdf(body: bytes) -> bool:
    return b"%PDF-" in body[:1024]


# ------------------------------------------------------------- a PDF's pages

OBJ = re.compile(rb"(\d+)\s+(\d+)\s+obj\b")
REF = rb"(\d+)\s+\d+\s+R"
PAGE = re.compile(rb"/Type\s*/Page(?![A-Za-z])")


def head_of(body: bytes) -> bytes:
    """An object's dictionary, everything before its stream."""
    i = body.find(b"stream")
    return body if i < 0 else body[:i]


def inflate(raw: bytes) -> bytes:
    try:
        return zlib.decompress(raw)
    except zlib.error:
        try:
            return zlib.decompressobj().decompress(raw)
        except zlib.error:
            return b""


def stream_of(body: bytes) -> bytes | None:
    """An object's stream with its filters undone, Flate, ASCIIHex and ASCII85, or None for one in
    another, an image's."""
    i = body.find(b"stream")
    if i < 0:
        return None
    head, j = body[:i], i + 6
    if body[j:j + 2] == b"\r\n":
        j += 2
    elif body[j:j + 1] in (b"\n", b"\r"):
        j += 1
    k = body.rfind(b"endstream")
    raw = body[j:k] if k > j else body[j:]
    for name in re.findall(rb"/(\w+Decode)\b", head):
        if name == b"FlateDecode":
            raw = inflate(raw)
        elif name == b"ASCIIHexDecode":
            hexes = re.sub(rb"[^0-9A-Fa-f]", b"", raw.split(b">")[0])
            raw = bytes.fromhex((hexes + b"0" * (len(hexes) % 2)).decode())
        elif name == b"ASCII85Decode":
            try:
                raw = base64.a85decode(raw.strip().split(b"~>")[0].lstrip(b"<~"))
            except ValueError:
                return None
        else:
            return None
    return raw


def objects(data: bytes) -> dict[int, bytes]:
    """Every object of a PDF by its number, those packed in object streams among them, a later one of
    the same number taking the place of an earlier, as an update does."""
    found: dict[int, bytes] = {}
    for m in OBJ.finditer(data):
        start = m.end()
        end = data.find(b"endobj", start)
        found[int(m.group(1))] = data[start:end if end >= 0 else len(data)]
    for body in list(found.values()):
        head = head_of(body)
        if b"/ObjStm" not in head:
            continue
        raw = stream_of(body)
        first = re.search(rb"/First\s+(\d+)", head)
        if not raw or not first:
            continue
        at = int(first.group(1))
        nums = [int(x) for x in re.findall(rb"\d+", raw[:at])]
        pairs = list(zip(nums[0::2], nums[1::2]))
        for k, (num, off) in enumerate(pairs):
            end = pairs[k + 1][1] if k + 1 < len(pairs) else len(raw) - at
            found.setdefault(num, raw[at + off:at + end])
    return found


def ref_of(head: bytes, name: bytes) -> int | None:
    m = re.search(rb"/" + name + rb"\s+" + REF, head)
    return int(m.group(1)) if m else None


def inner(head: bytes, name: bytes) -> bytes:
    """The dictionary a key holds inline, its own `<<` to the `>>` that closes it, or empty."""
    m = re.search(rb"/" + name + rb"\s*<<", head)
    if not m:
        return b""
    depth, i = 1, m.end()
    while i < len(head) and depth:
        if head[i:i + 2] == b"<<":
            depth, i = depth + 1, i + 2
        elif head[i:i + 2] == b">>":
            depth, i = depth - 1, i + 2
        else:
            i += 1
    return head[m.end():i - 2]


def dict_at(objs: dict, head: bytes, name: bytes) -> bytes:
    """A key's dictionary, inline or by reference."""
    found = inner(head, name)
    if found:
        return found
    ref = ref_of(head, name)
    return head_of(objs.get(ref, b"")) if ref is not None else b""


def first_page(objs: dict) -> int | None:
    """The first page, found down the catalogue's page tree by the first kid of each node, or with no
    tree the first object that is a page."""
    root = None
    for body in objs.values():
        head = head_of(body)
        if re.search(rb"/Type\s*/Catalog\b", head):
            root = ref_of(head, b"Pages")
            break
    node, seen = root, set()
    while node is not None and node in objs and node not in seen:
        seen.add(node)
        head = head_of(objs[node])
        if PAGE.search(head):
            return node
        kids = re.search(rb"/Kids\s*\[(.*?)\]", head, re.S)
        refs = re.findall(REF, kids.group(1)) if kids else []
        node = int(refs[0]) if refs else None
    pages = [n for n, body in sorted(objs.items()) if PAGE.search(head_of(body))]
    return pages[0] if pages else None


def resources(objs: dict, page: int) -> bytes:
    """A page's resources, its own or the nearest a parent gives it, as they are inherited."""
    node, seen = page, set()
    while node is not None and node in objs and node not in seen:
        seen.add(node)
        head = head_of(objs[node])
        found = dict_at(objs, head, b"Resources")
        if found:
            return found
        node = ref_of(head, b"Parent")
    return b""


def cmap(data: bytes) -> dict[bytes, str]:
    """A ToUnicode map, each code's bytes to its text."""
    out: dict[bytes, str] = {}
    hexes = lambda s: bytes.fromhex(re.sub(rb"\s", b"", s).decode() or "")
    utf16 = lambda b: b.decode("utf-16-be", "ignore")
    for block in re.findall(rb"beginbfchar(.*?)endbfchar", data, re.S):
        for src, dst in re.findall(rb"<([0-9A-Fa-f\s]+)>\s*<([0-9A-Fa-f\s]*)>", block):
            try:
                out[hexes(src)] = utf16(hexes(dst))
            except ValueError:
                continue
    for block in re.findall(rb"beginbfrange(.*?)endbfrange", data, re.S):
        for lo, hi, dst in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(<[0-9A-Fa-f\s]*>|\[[^\]]*\])", block):
            try:
                a, b, width = int(lo, 16), int(hi, 16), len(lo) // 2
                if b < a or b - a > 4096:
                    continue
                if dst.startswith(b"["):
                    for k, one in enumerate(re.findall(rb"<([0-9A-Fa-f\s]*)>", dst)):
                        out[(a + k).to_bytes(width, "big")] = utf16(hexes(one))
                else:
                    start = hexes(dst[1:-1])
                    base = int.from_bytes(start, "big")
                    for k in range(b - a + 1):
                        out[(a + k).to_bytes(width, "big")] = utf16((base + k).to_bytes(max(2, len(start)), "big"))
            except (ValueError, OverflowError):
                continue
    return out


def fonts(objs: dict, res: bytes) -> dict[bytes, dict]:
    """Each font of the resources by its name, with its ToUnicode map, empty when it has none."""
    out = {}
    for name, ref in re.findall(rb"/([^\s/<>\[\]()]+)\s+" + REF, dict_at(objs, res, b"Font")):
        body = objs.get(int(ref), b"")
        to = ref_of(head_of(body), b"ToUnicode")
        raw = stream_of(objs.get(to, b"")) if to is not None else None
        out[name] = cmap(raw) if raw else {}
    return out


def decode(s: bytes, table: dict) -> str:
    """A string's text through a font's map, the longest code that fits first, else as Windows' Latin
    code page, which most simple fonts of English text follow."""
    if not table:
        return s.decode("cp1252", "replace")
    widths = sorted({len(k) for k in table}, reverse=True)
    out, i = [], 0
    while i < len(s):
        for w in widths:
            hit = table.get(s[i:i + w])
            if hit is not None:
                out.append(hit)
                i += w
                break
        else:
            i += widths[-1]
    return "".join(out)


ESCAPES = {ord("n"): b"\n", ord("r"): b"\r", ord("t"): b"\t", ord("b"): b"\b", ord("f"): b"\f"}


def literal(data: bytes, i: int) -> tuple[bytes, int]:
    """A string in brackets from its opening one, its escapes read, and where it ends."""
    out, depth, i = bytearray(), 1, i + 1
    while i < len(data) and depth:
        c = data[i]
        if c == 0x5C:
            i += 1
            e = data[i] if i < len(data) else 0
            if e in ESCAPES:
                out += ESCAPES[e]
            elif 0x30 <= e <= 0x37:
                m = re.match(rb"[0-7]{1,3}", data[i:i + 3])
                out.append(int(m.group(0), 8) & 0xFF)
                i += len(m.group(0)) - 1
            elif e in (0x0A, 0x0D):
                if e == 0x0D and data[i + 1:i + 2] == b"\n":
                    i += 1
            else:
                out.append(e)
        elif c == 0x28:
            depth += 1
            out.append(c)
        elif c == 0x29:
            depth -= 1
            if depth:
                out.append(c)
        else:
            out.append(c)
        i += 1
    return bytes(out), i


TOKEN = re.compile(rb"/[^\s/<>\[\]()%{}]*|[+-]?(?:\d+\.?\d*|\.\d+)|[A-Za-z'\"*]+[0-9]?|\S")


def content_text(objs: dict, data: bytes, res: bytes, depth: int = 0) -> str:
    """The text a content stream shows, each string through its font, a wide gap in a TJ array and
    each move of the text a space, and a form it draws read in its place, one level down."""
    table = fonts(objs, res)
    out: list[str] = []
    stack: list = []
    font: dict = {}
    i, n = 0, len(data)
    while i < n:
        c = data[i]
        if c in b" \t\r\n\x0c\x00":
            i += 1
            continue
        if c == 0x25:
            j = data.find(b"\n", i)
            i = n if j < 0 else j + 1
            continue
        if c == 0x28:
            s, i = literal(data, i)
            stack.append(s)
            continue
        if c == 0x3C and data[i + 1:i + 2] != b"<":
            j = data.find(b">", i)
            j = n if j < 0 else j
            hexes = re.sub(rb"[^0-9A-Fa-f]", b"", data[i + 1:j])
            stack.append(bytes.fromhex((hexes + b"0" * (len(hexes) % 2)).decode()))
            i = j + 1
            continue
        if c == 0x5B:
            stack.append("[")
            i += 1
            continue
        if c == 0x5D:
            k = len(stack) - 1
            while k >= 0 and stack[k] != "[":
                k -= 1
            items = stack[k + 1:]
            del stack[max(k, 0):]
            stack.append(("array", items))
            i += 1
            continue
        m = TOKEN.match(data, i)
        tok = m.group(0) if m else data[i:i + 1]
        i += max(1, len(tok))
        if tok.startswith(b"/"):
            stack.append(("name", tok[1:]))
            continue
        if re.fullmatch(rb"[+-]?(?:\d+\.?\d*|\.\d+)", tok):
            stack.append(float(tok))
            continue
        op = tok
        if op == b"Tf":
            names = [x for x in stack if isinstance(x, tuple) and x[0] == "name"]
            font = table.get(names[-1][1], {}) if names else {}
        elif op in (b"Tj", b"'", b'"'):
            strings = [x for x in stack if isinstance(x, bytes)]
            if strings:
                out.append(decode(strings[-1], font))
        elif op == b"TJ":
            arrays = [x for x in stack if isinstance(x, tuple) and x[0] == "array"]
            if arrays:
                part = []
                for item in arrays[-1][1]:
                    if isinstance(item, bytes):
                        part.append(decode(item, font))
                    elif isinstance(item, float) and item < -250:
                        part.append(" ")
                out.append("".join(part))
        elif op in (b"Td", b"TD", b"T*", b"Tm", b"BT", b"ET"):
            out.append(" ")
        elif op == b"Do" and depth < 2:
            names = [x for x in stack if isinstance(x, tuple) and x[0] == "name"]
            ref = None
            if names:
                ref = ref_of(dict_at(objs, res, b"XObject"), re.escape(names[-1][1]))
            body = objs.get(ref, b"") if ref is not None else b""
            if re.search(rb"/Subtype\s*/Form\b", head_of(body)):
                inner_res = dict_at(objs, head_of(body), b"Resources") or res
                out.append(" " + content_text(objs, stream_of(body) or b"", inner_res, depth + 1) + " ")
        elif op == b"BI":
            j = data.find(b"EI", i)
            i = n if j < 0 else j + 2
        stack.clear()
    return "".join(out)


def page_text(objs: dict, page: int) -> str:
    """The text one page shows, its content streams read in order, its spacing tidied, empty when it
    shows none."""
    head = head_of(objs[page])
    m = re.search(rb"/Contents\s*\[(.*?)\]", head, re.S)
    refs = [int(r) for r in re.findall(REF, m.group(1))] if m else []
    one = ref_of(head, b"Contents")
    if not refs and one is not None:
        body = objs.get(one, b"")
        listed = re.findall(REF, body) if b"stream" not in body else []
        refs = [int(r) for r in listed] or [one]
    content = b"\n".join(stream_of(objs.get(r, b"")) or b"" for r in refs)
    return " ".join(content_text(objs, content, resources(objs, page)).split())


def page_list(objs: dict) -> list[int]:
    """Every page in reading order, down the catalogue's page tree, each node's kids in turn, or with
    no tree every object that is a page in the order of their numbers (Sift's reference check reads
    them all, 14 October)."""
    root = None
    for body in objs.values():
        head = head_of(body)
        if re.search(rb"/Type\s*/Catalog\b", head):
            root = ref_of(head, b"Pages")
            break
    out: list[int] = []
    seen: set[int] = set()

    def walk(node, depth=0):
        if node is None or node not in objs or node in seen or depth > 64:
            return
        seen.add(node)
        head = head_of(objs[node])
        if PAGE.search(head):
            out.append(node)
            return
        kids = re.search(rb"/Kids\s*\[(.*?)\]", head, re.S)
        for ref in re.findall(REF, kids.group(1)) if kids else []:
            walk(int(ref), depth + 1)

    walk(root)
    return out or [n for n, body in sorted(objs.items()) if PAGE.search(head_of(body))]


def pages_text(data: bytes) -> list[str]:
    """The text of each page of a PDF in order, a page that shows none empty, and no pages when the
    file cannot be read."""
    try:
        objs = objects(data)
        return [page_text(objs, page) for page in page_list(objs)]
    except (ValueError, IndexError, KeyError, OverflowError, RecursionError):
        return []


def first_page_text(data: bytes) -> str:
    """The text of a PDF's first page, or with no page tree found the first stream that shows text,
    empty when none can be read."""
    try:
        objs = objects(data)
        page = first_page(objs)
        if page is not None:
            text = page_text(objs, page)
            if text.strip():
                return text
        for body in objs.values():
            raw = stream_of(body) if b"stream" in body else None
            if raw and b"BT" in raw and (b"Tj" in raw or b"TJ" in raw):
                text = content_text(objs, raw, b"")
                if text.strip():
                    return " ".join(text.split())
    except (ValueError, IndexError, KeyError, OverflowError, RecursionError):
        return ""
    return ""
