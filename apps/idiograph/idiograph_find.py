"""Idiograph's part of Search, Distil's (22 October 2026, the family codebase's fourth build, from
app_search.py): what a case holds, its passages and the interviewer's notes on his own, its statements, quotes
and exploratory notes, from the workbook, and its PETs, sub-themes, their notes, its sticky notes and each
board's note, from its themes file, and what a project holds, every case of its study, and its GETs, their
notes, the GET table's row notes, the participant notes, the GETs boards' sticky notes and board notes, from
`idiograph-gets.json`, the cases by their names and the research question. History revisions, AI threads and
reviews stay out. Its kinds, its two scopes, This case and This project, and its finder under Everything are
registered with the family's Search engine, `app_search.register`, which the engine's import of this module
by its name makes (`boot.load`). Each file is only read, through the engine's memory of what it read.
"""
from __future__ import annotations

import time
from pathlib import Path

import openpyxl

import app_search as engine
import gets as gets_mod
import i18n
import themes as th
from workbook import detect_columns, field_to_lines, quote_entries, split_entries, timecode, timecodes_for, ts_seconds

# Every kind a search of Distil finds, in the order the card lists them and the results stand: the
# transcript, then what the analysis made of it, case by case and then across the cases, then the project
# itself
KINDS = ("passage", "inote", "statement", "quote", "enote", "pet", "sub", "petnote", "sticky", "boardnote",
         "get", "getnote", "rownote", "pnote", "case", "question")
# what This case holds, the rest being the project's
CASE_KINDS = KINDS[:10]
# what is kept in a workbook, which alone has sheets
SHEET_KINDS = ("passage", "inote", "statement", "quote", "enote")
# each kind by its name, one and many, as the card names them (`SEARCH_KINDS` in search.js), for the command
# line's answer (20 October)
NAMES = {
    "passage": ("Passage", "Passages"), "inote": ("Interviewer note", "Interviewer notes"),
    "statement": ("Statement", "Statements"), "quote": ("Quote", "Quotes"),
    "enote": ("Exploratory note", "Exploratory notes"), "pet": ("PET", "PETs"), "sub": ("Sub-theme", "Sub-themes"),
    "petnote": ("PET note", "PET notes"), "sticky": ("Sticky note", "Sticky notes"),
    "boardnote": ("Board note", "Board notes"), "get": ("GET", "GETs"), "getnote": ("GET note", "GET notes"),
    "rownote": ("Row note", "Row notes"), "pnote": ("Participant note", "Participant notes"),
    "case": ("Case", "Cases"), "question": ("Research question", "Research question")}
# the kinds an agent names together, each a few of the card's (20 October), beside the card's own names
GROUPS = (("passages", ("passage",)), ("statements", ("statement",)), ("quotes", ("quote",)), ("notes", ("enote", "inote")),
          ("pets", ("pet", "sub", "petnote")), ("gets", ("get", "getnote", "rownote", "pnote")),
          ("boards", ("sticky", "boardnote")), ("cases", ("case", "question")))


# ------------------------------------------------------------------ a workbook

def workbook_items(path: Path) -> list[dict]:
    """Every passage of a workbook, the interviewer's notes on his own, every statement, quote and
    exploratory note, read-only, in sheet order and row by row. `where` is the sheet and the timecode, as
    the statements screen writes it, and `go` the passage, the line and the field a click lands on."""
    form = timecodes_for(path)
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = []
    try:
        for s, ws in enumerate(book.worksheets):
            cols = detect_columns(ws)
            if not {"name", "ts", "transcript"} <= set(cols):
                continue
            width = max(cols.values())
            for r, values in enumerate(ws.iter_rows(min_row=2, max_col=width, values_only=True), start=2):
                values = tuple(values) + (None,) * (width - len(values))
                cell = lambda role: values[cols[role] - 1] if role in cols else None
                name, stamp, words = cell("name"), cell("ts"), cell("transcript")
                if name is None and stamp is None and words is None:
                    continue
                at = f"{ws.title} {timecode(ts_seconds(stamp), form)}".strip()
                go = {"screen": "statements", "sheet": ws.title, "row": r,
                      "speaker": str(name).strip() if name is not None else ""}
                text = " ".join(str(words or "").split())
                if text:
                    out.append(engine.item("passage", text, at, dict(go, field="passage"), (s, r, 0), ws.title))
                note = " ".join(field_to_lines(cell("note")).split())
                if note:
                    out.append(engine.item("inote", note, at, dict(go, field="note"), (s, r, 0), ws.title))
                for i, line in enumerate(split_entries(cell("es"))):
                    out.append(engine.item("statement", line, at, dict(go, field="es", line=i), (s, r, i), ws.title))
                for i, line in enumerate(quote_entries(cell("kq"))):
                    if line:
                        out.append(engine.item("quote", line, at, dict(go, field="kq", line=i), (s, r, i), ws.title))
                for i, line in enumerate(split_entries(cell("en"))):
                    out.append(engine.item("enote", " ".join(line.split()), at, dict(go, field="en", line=i), (s, r, i),
                                    ws.title))
    finally:
        book.close()
    return out


# ------------------------------------------------------------------ a themes file

def pet_marks(board: dict, labels: str) -> dict[str, tuple[int, str]]:
    """Each label of a board by its id, its depth and the mark the print view gives it, "PET B" for a
    PET, "B1" for a sub-theme and "B1.1" for a group with the book's letters, "PET 2", "PET 2a" and
    "2a.1" with numbers, each layer counted in the order the canvas reads it (`themes.pet_numbers`)."""
    version = th.normalise(board)
    drawn = th.layout_boxes(version)
    by_id = {g["id"]: g for g in version["groups"]}
    parents = th.parents_of(version["groups"])

    def tree(gid: str, seen: frozenset) -> dict:
        subs = [m for m in th.theme_order(version, gid, drawn) if m in by_id and m not in seen]
        return {"id": gid, "themes": [tree(m, seen | {m}) for m in subs]}

    tops = th.canvas_order([g["id"] for g in version["groups"] if g["id"] not in parents], by_id)
    numbers = th.pet_numbers([tree(g, frozenset({g})) for g in tops], labels)
    letters = th.pet_labels_of(labels) == th.LETTERS
    out = {}
    for gid, mark in numbers.items():
        depth = th.depth_of(parents, gid)
        out[gid] = (depth, f"PET {mark}" if letters and depth == 0 else mark)
    return out


def themes_items(workbook: Path, labels: str) -> list[dict]:
    """Every board of a case's themes file: its PETs and sub-themes by their titles, their notes, its
    sticky notes and its own note, board by board in the file's order. `where` is the board's name and
    the PET's mark, "Board 3 · PET B", and `go` the board and what to select on it."""
    data = th.load(workbook)
    out = []
    for b, board in enumerate(th.boards_of(data)):
        bid = str(board.get("id") or "")
        name = " ".join(str(board.get("name") or th.FIRST_NAME).split())
        try:
            marks = pet_marks(board, labels)
        except Exception:
            marks = {}
        groups = [g for g in board.get("groups") or [] if isinstance(g, dict) and g.get("id")]
        order = {gid: n for n, gid in enumerate(marks)}
        go = {"screen": "pets", "board": bid}
        for n, g in enumerate(groups):
            gid = str(g["id"])
            depth, mark = marks.get(gid, (0, ""))
            where = " · ".join(p for p in (name, mark) if p)
            at = (b, order.get(gid, len(order) + n))
            title = " ".join(str(g.get("label") or "").split())
            if title:
                out.append(engine.item("pet" if depth == 0 else "sub", title, where, dict(go, item="group", id=gid), at))
            note = " ".join(str(g.get("note") or "").split())
            if note:
                out.append(engine.item("petnote", note, where, dict(go, item="group", id=gid), at))
        ids = {str(g["id"]) for g in groups}
        for n, sticky in enumerate(th.notes_of(board, ids)):
            text = " ".join(sticky["text"].split())
            if not text:
                continue
            mark = marks.get(sticky.get("in", ""), (0, ""))[1]
            out.append(engine.item("sticky", text, " · ".join(p for p in (name, mark) if p),
                            dict(go, item="sticky", id=sticky["id"]), (b, 10000 + n)))
        note = " ".join(str(board.get("note") or "").split())
        if note:
            out.append(engine.item("boardnote", note, name, dict(go, item="board"), (b, 20000)))
    return out


# ------------------------------------------------------------------ the GETs file

def gets_items(path: Path) -> list[dict]:
    """Every board of a project's GETs file: its GETs by their titles and their notes, the GET table's
    row notes, the participant notes, its sticky notes and its own note. `where` says GETs and the
    board, then the GET or the case, and `go` the board and what to select on it."""
    data = gets_mod.load(Path(path).parent)
    out = []
    for b, board in enumerate(gets_mod.boards_of(data)):
        bid = str(board.get("id") or "")
        name = " ".join(str(board.get("name") or gets_mod.FIRST_NAME).split())
        head = f"GETs · {name}"
        go = {"screen": "gets", "board": bid}
        groups = [g for g in board.get("groups") or [] if isinstance(g, dict) and g.get("id")]
        titles = {}
        for n, g in enumerate(groups):
            gid = str(g["id"])
            title = " ".join(str(g.get("label") or "").split())
            titles[gid] = title
            if title:
                out.append(engine.item("get", title, head, dict(go, item="group", id=gid), (b, n)))
            note = " ".join(str(g.get("note") or "").split())
            if note:
                out.append(engine.item("getnote", note, " · ".join(p for p in (head, title) if p),
                                dict(go, item="group", id=gid), (b, n)))
        for gid, cases in gets_mod.rows_of(board).items():
            for case, row in cases.items():
                note = " ".join(str(row.get("note") or "").split())
                if note:
                    who = gets_mod.who(case)
                    out.append(dict(engine.item("rownote", note, " · ".join(p for p in (head, titles.get(gid, "")) if p),
                                         dict(go, item="group", id=gid), (b, 5000)), case=who))
        cards = board.get("cards") if isinstance(board.get("cards"), dict) else {}
        for key, card in cards.items():
            k = gets_mod.split_key(key)
            text = " ".join(str((card or {}).get("text") or "").split()) if isinstance(card, dict) else ""
            if k["kind"] == "pn" and text:
                out.append(dict(engine.item("pnote", text, head, dict(go, item="card", id=key), (b, 6000)),
                                case=gets_mod.who(k["case"])))
        for n, sticky in enumerate(th.notes_of(board, set(titles))):
            text = " ".join(sticky["text"].split())
            if text:
                out.append(engine.item("sticky", text, " · ".join(p for p in (head, titles.get(sticky.get("in", ""), "")) if p),
                                dict(go, item="sticky", id=sticky["id"]), (b, 7000 + n)))
        note = " ".join(str(board.get("note") or "").split())
        if note:
            out.append(engine.item("boardnote", note, head, dict(go, item="board"), (b, 8000)))
    return out


# ------------------------------------------------------------------ the search

def distil_found(words: list[str], scope: str, cases: list[dict], project: dict | None = None,
                 gets_file: Path | None = None, labels: str = th.LETTERS) -> list[dict]:
    """What a Distil case or project holds that every word typed is in: each case's workbook and themes
    file, a thematic analysis project's workbooks alone, and with `scope` of project the GETs file, the cases'
    names and the research question."""
    found = []
    # a thematic analysis project has no PETs board, its themes being on the project's board, so a case's themes
    # file is no place a result of its could open (tagaps, 1 November 2026)
    pets = (project or {}).get("method") != "ta"
    for rank, case in enumerate(cases):
        who = gets_mod.who(case["case"])
        book = Path(case["workbook"])
        # kept with the project's timecodes, so a change in Settings writes the places again
        for it in engine.held(book, "workbook", workbook_items, timecodes_for(book)):
            if engine.hit(it, words):
                found.append(dict(it, case=who, rank=rank, path=case.get("path", "")))
        if not pets:
            continue
        for it in engine.held(th.themes_path(book), "themes", lambda _p: themes_items(book, labels), labels):
            if engine.hit(it, words):
                found.append(dict(it, case=who, rank=rank, path=case.get("path", "")))
    if scope == "project":
        ranks = {gets_mod.who(c["case"]): n for n, c in enumerate(cases)}
        anyone = cases[0].get("path", "") if cases else ""
        if gets_file is not None:
            for it in engine.held(Path(gets_file), "gets", gets_items):
                if engine.hit(it, words):
                    found.append(dict(it, case=it.get("case", ""), rank=ranks.get(it.get("case"), len(ranks)),
                                      path=anyone))
        name = (project or {}).get("name") or ""
        pid = (project or {}).get("id") or ""
        for rank, case in enumerate(cases):
            who = gets_mod.who(case["case"])
            if engine.holds(who, words):
                found.append(dict(engine.item("case", who, name, {"screen": "project", "id": pid, "case": case["case"]},
                                       (0,)), case=who, rank=rank, path=case.get("path", "")))
        question = " ".join(str((project or {}).get("research_question") or "").split())
        if question and engine.holds(question, words):
            found.append(dict(engine.item("question", question, name, {"screen": "project", "id": pid}, (0,)),
                              case="", rank=len(cases), path=anyone))
    return found


def search(q: str, scope: str, cases: list[dict], project: dict | None = None, gets_file: Path | None = None,
           labels: str = th.LETTERS, kinds=(), only_cases=(), sheets=(), limit: int = engine.LIMIT, whole: bool = False,
           match_case: bool = False) -> dict:
    """The results of `q` over Distil's `cases`, each `{"case", "workbook"}` in case order, the case by its
    label, and with `scope` of project the GETs file and the project, `{"name", "research_question", "id"}`.
    `kinds`, `only_cases` and `sheets` narrow what is shown (see `answer`), `whole` and `match_case` being Whole
    word and Match case."""
    started = time.perf_counter()
    scope = scope if scope in ("case", "project") else "project"
    q, words, phrase = engine.query(q, whole, match_case)
    found = engine.phrased(distil_found(words, scope, cases, project, gets_file, labels) if words else [], phrase)
    return engine.answer(q, scope, words, found, started, kinds=kinds, only_cases=only_cases, sheets=sheets,
                  case_names=[gets_mod.who(c["case"]) for c in cases], limit=limit)


def found(words: list[str], p: dict) -> list[dict]:
    """A Distil project under Everything, `{"id", "name", "cases", "project", "gets_file", "labels"}`, searched
    as This project searches it (the engine's `search_all`)."""
    return distil_found(words, "project", p["cases"], p.get("project"), p.get("gets_file"), p.get("labels") or th.LETTERS)


# the kinds whose names a project's method says otherwise, each by its key in the catalogue (taword, 1 November
# 2026): a thematic analysis project's Codes, Extracts, Notes, Subthemes and Themes
KIND_WORDS = {"statement": lambda n: i18n.t("cli.kind.statement", n=n), "quote": lambda n: i18n.t("cli.kind.quote", n=n),
              "enote": lambda n: i18n.t("cli.kind.enote", n=n), "sub": lambda n: i18n.t("cli.kind.sub", n=n),
              "get": lambda n: i18n.t("cli.kind.get", n=n), "getnote": lambda n: i18n.t("cli.kind.getnote", n=n)}
METHOD_KINDS = tuple(KIND_WORDS)


def kind_named(kind: str, many: bool = False) -> str | None:
    """A kind's name in the words of the method the run is in, or None where IPA's registered name stands."""
    if kind not in KIND_WORDS or i18n.method_now() == i18n.BASE_METHOD:
        return None
    return KIND_WORDS[kind](2 if many else 1)


def names_now() -> dict:
    """The kinds' names the run's method says otherwise, one and many, for the page's Search card, empty for
    IPA's, whose names the card holds."""
    if i18n.method_now() == i18n.BASE_METHOD:
        return {}
    return {k: [kind_named(k), kind_named(k, True)] for k in METHOD_KINDS}


engine.register("distil", KINDS, found, NAMES, *GROUPS, scopes={"case": CASE_KINDS, "project": KINDS},
                screens=("statements", "pets", "gets"), namer=kind_named)
