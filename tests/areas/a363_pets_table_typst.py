"""Area 363: the table of PETs as a Typst template (typst2, 9 November 2026, and Adam, 9 November about 18:10: Typst is the
one engine for every PDF, no fallback). The design now lives twice, in themes_print's HTML view and in
`apps/idiograph/typst/pets_table.typ`, both from one walk of the board (`themes_print.walk`), so these checks read the
PDF Typst makes against the HTML view of the same board: the text of each page in the HTML's order (the drift check, a
change made in one place and not the other fails here), each page opening on a row's start and never ending on a
heading, the foot's three parts on every page with "Page n of N", the project cut at a word with "…" when the foot is
too long and whole when it fits, the board left out with "Leave out the board's name", numbers in place of letters and
the empty board's line. On the demo's Juno and an invented board with every part: groups five deep, descriptions and
notes, a stack, Not placed, the statements set aside with a reason, the board's note and a long project name. No
check pins a pixel, a colour or a size, the pictures being review shots'."""
from __future__ import annotations

import html.parser
import shutil
from pathlib import Path

from . import support
from .support import check, skip

FLAT = lambda s: "".join(str(s).split()).casefold()
LONG = ("The allotment after a death: how people who garden alone keep a shared plot going through the first year, "
        "the second and the winters after, a study of six gardeners")
# the kinds of text that head something and must never end a page, and those that never open one (a row's later parts)
HEADS = {"pet-title", "sub-title", "group-title", "desc", "tnote", "rest-h2"}
INNER = {"ref", "kq", "why", "stk-head", "stk"}


class Nodes(html.parser.HTMLParser):
    """The HTML view's text in order, each piece with the class of what holds it, the page's controls, foot,
    scripts and style left out."""

    def __init__(self):
        super().__init__()
        self.stack: list[str] = []
        self.out: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        cls = dict(attrs).get("class") or ""
        if tag in ("script", "style", "title", "footer") or "controls" in cls.split():
            kind = "skip"
        elif tag == "h2" and not cls:
            kind = "rest-h2"
        else:
            kind = next((c for c in cls.split() if c in HEADS | INNER | {"st", "case", "table-name", "label", "value",
                                                                         "note", "none", "number", "title"}), "")
            if kind in ("number", "title"):
                kind = "pet-title"
        if tag not in ("meta", "link", "input", "br"):
            self.stack.append(kind or (self.stack[-1] if self.stack else ""))

    def handle_endtag(self, tag):
        if tag not in ("meta", "link", "input", "br") and self.stack:
            self.stack.pop()

    def handle_data(self, data):
        if self.stack and "skip" not in self.stack and data.strip():
            self.out.append((self.stack[-1], data))


def nodes_of(page: str) -> list[tuple[str, str]]:
    p = Nodes()
    p.feed(page.split("<body>", 1)[1])
    return p.out


def make_board(root: Path, th) -> Path:
    """An invented board on a scratch copy of the demo's workbook: a PET five deep with descriptions and notes, a top
    with three stacked under it, three more PETs, two with a sub-PET, the rest not placed, three set aside, two with a
    reason, and the board's note."""
    shutil.rmtree(root, ignore_errors=True)
    (root / "P4 - Heron" / "Working").mkdir(parents=True)
    book = root / "P4 - Heron" / "P4 Heron - EN & ES.xlsx"
    shutil.copy2(support.DEMO_SHIPPED / "Juno - EN & ES.xlsx", book)
    read = th.read_cards(book)
    board = th.blank_version(read["cards"])
    take = iter(c["key"] for c in read["cards"])
    at = {"y": 0}
    groups = []

    def cards(n, x):
        out = []
        for _ in range(n):
            k = next(take)
            at["y"] += 100
            board["cards"][k].update(x=x, y=at["y"])
            out.append(k)
        return out

    def group(gid, label, x, **extra):
        at["y"] += 60
        groups.append({"id": gid, "label": label, "members": [], "x": x, "y": at["y"], **extra})
        return groups[-1]

    g1 = group("g1", "Keeping the allotment going through the first winter alone", 0,
               description="Cold mornings at the plot as a way of keeping a promise to someone gone",
               note="Every sub-theme here came back in the second interview.\nKept as one PET for now.")
    g1["members"] += cards(3, 0)
    top = g1["members"][0]
    chain = [("g2", "Tools left where he left them", {"description": "Nothing moved from the shed"}),
             ("g3", "The fork by the water butt", {}), ("g4", "Handles worn to his grip", {"note": "A group inside a group."}),
             ("g5", "Gloves still in the pocket", {})]
    parent = g1
    for gid, label, extra in chain:
        g = group(gid, label, 0, **extra)
        parent["members"].append(gid)
        g["members"] += cards(2, 0)
        parent = g
    g1["members"] += cards(2, 0)
    stacked = cards(3, 0)
    for i, (gid, label, sub) in enumerate((("g6", "Talking to the beans", "g7"), ("g8", "Seed saved from the best plants", "g9"),
                                            ("g10", "A row kept for a brother", None))):
        x = 3000 * (i + 1)
        at["y"] = 0
        g = group(gid, label, x)
        g["members"] += cards(6, x)
        if sub:
            s = group(sub, f"{label}, at dusk", x)
            g["members"].append(sub)
            s["members"] += cards(5, x)
        g["members"] += cards(4, x)
    gone = [next(take) for _ in range(3)]
    board.update(groups=groups, stacks={top: stacked}, discarded=gone,
                 ai={"discarded": {gone[0]: "Says the same as the statement before it, a minute later.",
                                   gone[1]: "About the neighbour's plot, not hers."}},
                 note="Board kept for the second supervision.\nThe dusk sub-themes may merge.")
    th.save(book, board, "P4 - Heron")
    return book


def test_pets_table_typst(scratch: Path):
    print("\n363. The table of PETs in Typst: the HTML view's text, each page opening on a row and never ending on a "
          "heading, the foot's three parts and its cut, the board's name left out, numbers and the empty board")
    try:
        import typeset
    except ImportError:
        skip("363 the Typst view", "family/typeset.py is not here yet (typst1)")
        return
    import pdftext
    import themes as th
    import themes_print as tp

    root = scratch / "a363"
    shutil.rmtree(root, ignore_errors=True)
    (root / "Juno" / "Working").mkdir(parents=True)
    shutil.copy2(support.DEMO_SHIPPED / "Juno - EN & ES.xlsx", root / "Juno" / "Juno - EN & ES.xlsx")
    for side in sorted((support.DEMO_SHIPPED / "Working").glob("Juno - *")):
        shutil.copy2(side, root / "Juno" / "Working" / side.name)
    juno = root / "Juno" / "Juno - EN & ES.xlsx"
    heron = make_board(root / "heron", th)
    runs = {
        "Juno": (juno, "Juno", dict(project="Living with a dog", researcher="Ada Lark", question=support.DEMO_QUESTION,
                                    unplaced=True, binned=True, stacked=True)),
        "Heron": (heron, "P4 - Heron", dict(project=LONG, researcher="Ada Lark", note=True, labels=th.NUMBERS,
                                            question="How do people keep an allotment going alone after a bereavement?",
                                            unplaced=True, binned=True, stacked=True)),
    }
    for name, (book, case, kw) in runs.items():
        data = tp.typst_data(book, case, **kw)
        page = tp.page(book, case, auto=False, **kw)
        try:
            pdf = typeset.render(tp.TEMPLATE, data)
        except typeset.Failed as exc:
            check(f"363 {name}: Typst makes the table", False, str(exc))
            continue
        pages = pdftext.pages_text(pdf)
        total = len(pages)
        check(f"363 {name}: the table runs to pages", total >= 2 if name == "Heron" else total >= 1, f"{total} pages")

        # ── A. the foot on every page, the body without it
        foot_left = "".join(data["foot"]["left"])
        foot_starts = FLAT(data["foot"]["left"][0])
        bodies = []
        for text in pages:
            flat = FLAT(text)
            cut = flat.rfind(foot_starts)
            bodies.append(flat[:cut] if cut >= 0 else flat)
        page_of = [FLAT(data["foot"]["page_of"].replace("{page}", str(n)).replace("{pages}", str(total)))
                   for n in range(1, total + 1)]
        middle = FLAT(data["foot"]["middle"])
        check(f"363 {name}: every page's foot has its three parts and Page n of N",
              all(FLAT(t)[FLAT(t).rfind(foot_starts):].endswith(page_of[i]) and middle in FLAT(t) for i, t in enumerate(pages)))

        # ── B. the drift check: the HTML view's text, piece by piece, on the pages in the same order
        nodes = nodes_of(page)
        joined = "".join(bodies)
        bounds, at = [], 0
        for b in bodies:
            at += len(b)
            bounds.append(at)
        # the head is a grid, read row by row on paper and column by column in the HTML, so its pieces are looked for
        # on the first page in any order, and a row's parts from the row's start, its quote standing after its
        # stacked statements on paper and before them in the HTML
        head = {"case", "table-name", "label", "value", "note"}
        missing = [said for kind, said in nodes if kind in head and FLAT(said) not in bodies[0]]
        pos, start, placed = 0, 0, []
        for kind, said in nodes:
            if kind in head:
                continue
            f = FLAT(said)
            hit = joined.find(f, start if kind in INNER | {"kq"} else pos)
            if hit < 0:
                missing.append(said)
                continue
            if kind not in INNER | {"kq"}:
                start = hit
            placed.append((kind, hit, hit + len(f)))
            pos = max(pos, hit + len(f))
        check(f"363 {name}: every piece of the HTML view's text is on the pages in its order", not missing,
              f"{len(nodes)} pieces" if not missing else f"missing {missing[:3]}")

        # ── C. each page after the first opens on a row's start or a heading, never inside a row, and none ends on a heading
        opens, ends = [], []
        for i, edge in enumerate(bounds[:-1]):
            first = next((k for k, s, e in placed if s >= edge), None)
            last = [k for k, s, e in placed if e <= edge]
            if first in INNER:
                opens.append((i + 2, first))
            if last and last[-1] in HEADS:
                ends.append((i + 1, last[-1]))
        check(f"363 {name}: no page opens inside a row", not opens, str(opens))
        check(f"363 {name}: no heading ends a page", not ends, str(ends))

        # ── D. the foot's left part: whole when it fits, the project cut at a word with "…" when it does not
        flat_foot = FLAT(pages[0])[FLAT(pages[0]).rfind(foot_starts):]
        if name == "Juno":
            check("363 Juno: the foot's left part whole, the board in it", flat_foot.startswith(FLAT(foot_left))
                  and "(board1)" in flat_foot.casefold())
        else:
            words = kw["project"].split()
            cuts = [" ".join(words[:n]).rstrip(",;:.") + "…" for n in range(1, len(words))]
            said = next((c for c in cuts if FLAT(c) in flat_foot), "")
            check("363 Heron: the long project cut at a word with an ellipsis, the table's name kept", bool(said)
                  and FLAT(data["table"]) in flat_foot and FLAT(kw["project"]) not in flat_foot, said)
        if name == "Heron":
            check("363 Heron: numbers in place of letters, PET 1. and 1a.1.1.1 five deep",
                  FLAT("PET 1.") in joined and FLAT("1a.1.1.1 Gloves still in the pocket") in joined and "a.keeping" not in joined)
            check("363 Heron: a reason under a statement set aside", FLAT("About the neighbour's plot, not hers.") in joined)

    # ── E. Leave out the board's name: off the foot and out of the document's title
    sent = tp.typst_data(juno, "Juno", project="Living with a dog", sending=True)
    kept = tp.typst_data(juno, "Juno", project="Living with a dog")
    pdf = typeset.render(tp.TEMPLATE, sent)
    check("363 Leave out the board's name: no board in the foot or the title, the board in both without it",
          "(Board" not in "".join(sent["foot"]["left"]) and "Board 1" not in "".join(pdftext.pages_text(pdf))
          and sent["title"] == "Juno" and "(Board 1)" in "".join(kept["foot"]["left"]) and "Board 1" in kept["title"])

    # ── F. a board with nothing on it: one page with the empty board's line
    empty = root / "empty"
    empty.mkdir()
    book = support.demo_copy(empty, "Wick", "Wick - EN & ES.xlsx")
    data = tp.typst_data(book, "Wick")
    pages = pdftext.pages_text(typeset.render(tp.TEMPLATE, data))
    check("363 an empty board: one page carrying the empty board's line", len(pages) == 1 and data["none"]
          and FLAT(data["none"]) in FLAT(pages[0]))
    # ── G. a template that fails says so in a plain sentence, never a page
    try:
        typeset.render(tp.TEMPLATE, {"case": "x"})
        check("363 data the template cannot read fails plainly", False, "a PDF was made")
    except typeset.Failed as exc:
        check("363 data the template cannot read fails plainly", bool(str(exc)) and "typst" not in str(exc).lower(), str(exc))
