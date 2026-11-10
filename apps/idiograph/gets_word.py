#!/usr/bin/env python3
"""A thematic analysis project's table of themes as a Word document (taword, 1 November 2026, Adam: "yes, add it"),
the theme table his Table view shows on the project's board of themes, in the shape `themes_word` gives a table of
PETs: portrait A4, Word's own heading styles, no table, no colour.

The document opens with the project's name under Heading 1 and under it, smaller in Word's Subtitle style, the
table's name in the method's words, "Table of themes". Then each theme in the order the canvas reads them under
Heading 2, its title in bold capitals by the run's All caps, its description, when the Descriptions tick leaves it
in, a plain grey second line of its heading, and its note in italics. A subtheme sits under its theme under Heading
3, a group inside it under Heading 4 and deeper under Heading 5, each with its description and note the same way.
Under each heading come its codes as the canvas reads them, each followed by whose it is and where, "(Juno, Initial,
00:14)", and on the next line its own extract in single curly quotation marks, set in a little. A code no longer in
the workbook says so in its reference. A participant note comes only with Include participant notes, in italics
after whose it is. Each participant's note for a theme, the row note the theme table keeps, follows the theme's codes
in italics. With Their key extract only, each theme holds every participant's key extract alone, as the printed
table does.

The file goes at the project's root, where the theme table's PDF goes, as "<project> - <board> - Theme table.docx",
and never over a file there (`themes_word.free_name`), the date and time in the name when it is taken. With Leave
out the board's name it is "<project> - Theme table.docx". Its author is Your name. The board, the themes file and
the workbooks are only read.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import gets as gt
import gets_print
import i18n
import print_pdf
import themes as th
import themes_word as tw
from themes_print import bare
from workbook import WorkbookError


def run(text: str, **marks) -> dict:
    return tw.run(text, **marks)


def heading(depth: int, group: dict, descriptions: bool) -> list[dict]:
    """A theme's heading at `depth`, 0 a theme, 1 a subtheme, its description as a second line of it and its note
    after it in italics."""
    runs = [run(group.get("label") or th.UNTITLED, bold=True, italic=depth >= 2, caps=depth == 0)]
    said = th.description_of(group) if descriptions else ""
    if said:
        runs.append(dict(run(said), desc=True))
    out = [{"style": min(tw.DEEPEST, depth + 2), "runs": runs}]
    for line in str(group.get("note") or "").splitlines():
        if line.strip():
            out.append({"style": 0, "runs": [run(line.strip(), italic=True)]})
    return out


def reference(who: str, item: dict) -> str:
    """Whose a code is and where, "Juno, Initial, 00:14", or that it is no longer in the workbook."""
    where = ", ".join(x for x in (who, item.get("sheet"), item.get("time")) if x)
    return i18n.t("exports.where_gone", where=where) if item.get("gone") else where


def code_blocks(who: str, item: dict, notes: bool) -> list[dict]:
    """A card under a theme: a code with its reference and its own extract under it, a PET's or a subtheme's card
    by its title, or with `notes` a participant note in italics."""
    if item["kind"] == "pn":
        return [{"style": 0, "runs": [run(f"{who}: {item['text']}", italic=True)]}] if notes and item["text"] else []
    text = item.get("text") if item["kind"] == "es" else item.get("title")
    out = [{"style": tw.STATEMENT, "runs": [run(f"{text} ({reference(who, item)})")]}]
    said = bare(item["quotes"][0]["text"]) if item["kind"] == "es" and item.get("quotes") else ""
    if said:
        out[0]["keep"] = True
        out.append({"style": tw.QUOTE, "runs": [run(f"‘{said}’")]})
    return out


def board_blocks(parts: dict, notes: bool = False, selected: bool = False, descriptions: bool = True) -> list[dict]:
    """The themes of the board `parts` holds (`gets_print.study_parts`), in the canvas's order, as paragraphs."""
    data, board = parts["data"], parts["board"]
    kept = gt.normal(board, data)
    shown = gt.named(kept, data)
    drawn = th.layout_boxes(shown, gt.card_height)
    by_id = {g["id"]: g for g in kept["groups"]}
    parents = th.parents_of(kept["groups"])
    thrown = set(shown.get("discarded") or [])
    held = data.get("cases") or {}
    inside = set(parts["inside"])
    table = {g["id"]: g for g in gets_print.gets_table(parts)}
    out: list[dict] = []

    def walk(gid: str, depth: int, seen: frozenset) -> None:
        for m in th.theme_order(shown, gid, drawn):
            if m in by_id:
                if m not in seen:
                    out.extend(heading(depth + 1, by_id[m], descriptions))
                    walk(m, depth + 1, seen | {m})
            elif m in (shown.get("cards") or {}) and m not in thrown:
                case = gt.split_key(m)["case"]
                if case in inside:
                    item = gt.item_of(held.get(case) or {}, m, shown["cards"][m])
                    out.extend(code_blocks(gt.who(case), item, notes))

    tops = th.canvas_order([g["id"] for g in kept["groups"] if g["id"] not in parents], by_id)
    for gid in tops:
        out.extend(heading(0, by_id[gid], descriptions))
        rows = (table.get(gid) or {}).get("rows") or []
        if selected:
            # each participant's key extract alone, as the printed table's Their key extract only
            for row in rows:
                q = row.get("quote") if row["counted"] else None
                if q:
                    out.append({"style": tw.STATEMENT, "keep": True, "runs": [run(reference(row["who"], q), bold=True)]})
                    out.append({"style": tw.QUOTE, "runs": [run(f"‘{bare(q['text'])}’")]})
        else:
            walk(gid, 0, frozenset({gid}))
        for row in rows:
            if row.get("note"):
                out.append({"style": 0, "runs": [run(f"{row['who']}: {row['note']}", italic=True)]})
    if not tops:
        out.append({"style": 0, "runs": [run(i18n.t("page_print.gets.none"))]})
    return out


def blocks(project: dict, parts: dict, notes: bool = False, selected: bool = False,
           descriptions: bool = True) -> list[dict]:
    """The document as paragraphs: the project and the table's name, then the themes."""
    name = " ".join(str(project.get("name") or "").split()) or i18n.t("page_print.gets.project")
    return ([{"style": 1, "runs": [run(name)]}, {"style": tw.SUBTITLE, "runs": [run(i18n.t("page_print.gets.table_name"))]}]
            + board_blocks(parts, notes, selected, descriptions))


def write(root: Path, books: list[dict], project: dict, board: dict, detail: str = "full", notes: bool = False,
          sending: bool = False, descriptions: bool = True, author: str = "", dry_run: bool = False,
          now: datetime | None = None) -> dict:
    """Write a board of themes as a Word document at the project's root, never over a file there, named as its PDF
    is with .docx, every code and extract or with `detail` "selected" each participant's key extract alone,
    participant notes only with `notes`, the board's name left out with `sending`, each theme's description under
    its title with `descriptions`, `author` Your name. With `dry_run` nothing is written and the answer names the
    file it would write. A board no longer there is refused."""
    root = Path(root)
    now = now or datetime.now().astimezone()
    parts = gets_print.study_parts(root, books, str(board.get("id") or "") or None, th.now_iso())
    shown = parts["board"]
    name = project.get("name") or i18n.t("page_print.gets.project")
    named = "" if sending else f"{shown.get('name') or th.FIRST_NAME} - "
    stem = print_pdf.safe_stem(f"{name} - {named}{i18n.t('page_print.gets.table')}")
    path, dated = tw.free_name(root, stem, now)
    kept = gt.normal(shown, parts["data"])
    tops = [g for g in kept["groups"] if g["id"] not in th.parents_of(kept["groups"])]
    codes = sum(1 for k in kept["cards"] if gt.split_key(k)["kind"] == "es" and any(
        k in (g.get("members") or []) for g in kept["groups"]))
    out = {"path": str(path), "name": path.name, "folder": str(root), "dated": dated,
           "counts": {"themes": len(tops), "codes": codes, "participants": len(parts["inside"])},
           "version": {"id": str(shown.get("id") or ""), "name": str(shown.get("name") or "")},
           "detail": "selected" if detail == "selected" else "full", "notes": bool(notes)}
    if dry_run:
        return dict(out, dry_run=True)
    paras = blocks(project, parts, notes, detail == "selected", descriptions)
    title = f"{' '.join(str(name).split())}, {i18n.t('page_print.gets.table_name')}"
    data = tw.package(paras, title, now, author)
    while True:
        try:
            # opened only when no file has the name, so a file there is never written over
            with open(path, "xb") as handle:
                try:
                    handle.write(data)
                except BaseException:
                    handle.close()
                    path.unlink(missing_ok=True)
                    raise
            break
        except FileExistsError:
            path, dated = tw.free_name(root, stem, now)
    return dict(out, path=str(path), name=path.name, dated=dated)


def refuse_unless_ta() -> None:
    """The Word export of a board of themes is a thematic analysis project's, an IPA project's GETs going to print,
    PDF and the canvas, its participants' tables of PETs to Word."""
    if i18n.method_now() != "ta":
        raise WorkbookError(i18n.t("server.gets_word_ta_only"))
