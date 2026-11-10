#!/usr/bin/env python3
"""The table of PETs and a GETs board as PDFs, for the window, a browser's tab, the command line and the MCP server
alike (gap 4 of the agent access plan, 19 October 2026), made by Typst (typst5, 9 November 2026, Adam about 18:10:
Typst is the one engine for every PDF, no fallback, "it should work or error"). The table of PETs is the template
`typst/pets_table_main.typ` with `themes_print.typst_data`, a GETs board's `typst/gets.typ` with
`gets_print.typst_data` (the GET table, the audit trail), and its full set `typst/gets-all.typ` with the same
data for `all` (a contents page, each participant's table of PETs, the GET table and the trail), each data
made from the same walk of the board as the HTML print view, so the two cannot disagree. No browser and no window
takes part. When Typst cannot make the pages the answer is the catalogue's plain sentence (`typeset.Failed`) and
nothing is written.

The file goes where the Word document goes, at the case's root beside the workbook, as it has since
19 October, or a GETs board's at the project's root beside the GETs file, unless `out` names another
place (20 October), a folder or a file ending .pdf. In a folder it is named as the print view names the
PDF, "P9 - Wren - Board 3 - PETs.pdf", or "P9 - Wren.pdf" for sending. Editing the
board never changes the name, only renaming it does, and for sending not even that. It never writes
over a file there unless asked (`replace`), and then only by a whole new file put in its place, so a
reader holding the old one never sees half of it. Otherwise the date and time go in the name, as the
Word document's do. The workbook, the themes file and the GETs file are only read.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import i18n
import themes as th
import themes_print
import themes_word
from workbook import WorkbookError


def typeset_pdf(template: Path, data: dict) -> bytes:
    """The PDF of `template` with `data`, through the one engine, or the engine's plain sentence as a refusal."""
    import typeset
    try:
        out = typeset.render(template, data, fmt="pdf")
    except typeset.Failed as exc:
        raise WorkbookError(str(exc)) from None
    if not out.startswith(b"%PDF"):
        raise WorkbookError(i18n.t("typeset.failed"))
    return out


def stem_of(case: str, board_name: str, sending: bool = False) -> str:
    """The PDF's name without `.pdf`, the print view's title, any character a file name cannot carry
    made a hyphen."""
    said = themes_print.title_of(case, board_name or th.FIRST_NAME, sending)
    return safe_stem(said)


def safe_stem(said: str) -> str:
    return " ".join(str(said or "").translate(th.UNSAFE).split()) or th.FIRST_NAME


def where_to(out, stem: str, default: Path) -> tuple[Path, str]:
    """The folder and the name without `.pdf` that `out` names: a folder there, the PDF named as the print
    view names it, or a file ending .pdf in a folder there. With no `out`, `default`, the folder it has
    always gone in, named as the print view names it."""
    if out is None or not str(out).strip():
        return Path(default), stem
    given = Path(str(out).strip()).expanduser()
    if given.is_dir():
        return given.resolve(), stem
    if given.suffix.lower() != ".pdf":
        raise WorkbookError(i18n.t("server.file_out_names_ends_pdf") if given.parent.is_dir() and given.suffix
                            else i18n.t("server.folder_out_names_nothing_written"))
    if not given.parent.is_dir():
        raise WorkbookError(i18n.t("server.folder_out_names_nothing_written"))
    return given.parent.resolve(), safe_stem(given.stem)


def place(folder: Path, stem: str, replace: bool, now: datetime, dry_run: bool, make) -> dict:
    """Put the PDF `make()` makes at `folder`/`stem`.pdf, never over a file there unless `replace`, and
    then by a whole new file put in its place, otherwise with the date and time in the name. With
    `dry_run` nothing is printed or written, and the answer names the file it would write."""
    plain = folder / f"{stem}.pdf"
    if replace:
        path, dated = plain, False
    else:
        path, dated = themes_word.free_name(folder, stem, now, ".pdf")
    out = {"path": str(path), "name": path.name, "folder": str(folder), "dated": dated,
           "replaced": bool(replace and plain.exists())}
    if dry_run:
        return dict(out, dry_run=True)
    # made before a file is opened, so a failure writes nothing
    data = make()
    if replace:
        part = folder / f".{stem}.pdf.part"
        part.write_bytes(data)
        os.replace(part, path)
        return out
    while True:
        try:
            # opened only when no file has the name, so a file there is never written over
            with open(path, "xb") as handle:
                handle.write(data)
            break
        except FileExistsError:
            path, dated = themes_word.free_name(folder, stem, now, ".pdf")
    return dict(out, path=str(path), name=path.name, dated=dated)


def write(workbook: Path, case: str, vid=None, question: str = "", labels: str = th.LETTERS,
          unplaced: bool = False, binned: bool = False, stacked: bool = False, sending: bool = False,
          note: bool = False, out=None, replace: bool = False, dry_run: bool = False,
          now: datetime | None = None, descriptions: bool = True, project: str = "", researcher: str = "") -> dict:
    """Write a board's table of PETs as a PDF beside the workbook, or where `out` names, a folder or a
    file, as the print view
    draws it with the same ticks: Board note (`note`), Include not placed, Include binned experiential
    statements, Include stacked statements and For sending, each off as on a new install, and the
    labels the project's. With `dry_run` nothing is printed or written and the answer names the file it
    would write."""
    workbook = Path(workbook)
    now = now or datetime.now().astimezone()
    board, version = themes_word.board_of(workbook, vid)
    folder, stem = where_to(out, stem_of(case, version.get("name"), sending), workbook.parent)
    counts = {"pets": len(board["themes"]),
              "statements": sum(len(t["statements"]) for t in themes_word.walk(board["themes"])),
              "not_placed": len(board["unplaced"]), "discarded": len(board["discarded"])}
    made = place(folder, stem, replace, now, dry_run, lambda: typeset_pdf(themes_print.TEMPLATE, themes_print.typst_data(
        workbook, case, str(version.get("id") or "") or None, question, now=now, note=note,
        labels=labels, unplaced=unplaced, binned=binned, stacked=stacked, sending=sending, descriptions=descriptions,
        project=project, researcher=researcher)))
    return dict(made, counts=counts, version=th.summary(version), labels=th.pet_labels_of(labels))


GETS_WHAT = {"table": "GET table", "trail": "Audit trail", "all": "GETs"}
# the same as the print view's title names them, in the words of the project's method (tagaps, 1 November 2026)
GETS_WHAT_KEYS = {"table": "page_print.gets.table", "trail": "page_print.gets.trail", "all": "page_print.gets.project"}


def gets_what(what: str) -> str:
    """What a GETs PDF holds as its name says it, "GET table", "Audit trail" or "GETs", a thematic analysis
    project's "Theme table" and "Themes"."""
    return i18n.t(GETS_WHAT_KEYS[what])


def write_gets(root: Path, books: list[dict], project: dict, board: dict, what: str = "table",
               detail: str = "full", notes: bool = False, get: str | None = None, sending: bool = False,
               out=None, replace: bool = False, dry_run: bool = False, now: datetime | None = None,
               descriptions: bool = True, researcher: str = "") -> dict:
    """Write a GETs board as a PDF at the project's root, beside the GETs file, or where `out` names, as
    the GETs screen's print card makes it: the GET
    table, the audit trail or the full set (`what`), Full or Selected (`detail`), Include participant
    notes (`notes`) and For sending, one GET's trail alone with `get`, the defaults the card's own, the
    GET table, Full and both ticks off. Named as the print view names the PDF, "Study -
    Board 2 - GET table", with the GET's id after it for one GET's trail. With `dry_run` nothing is
    printed or written. The GETs file and the workbooks are only read."""
    import gets_print
    now = now or datetime.now().astimezone()
    what = "trail" if get else what
    if what not in gets_print.WHATS:
        raise WorkbookError(i18n.t("server.what_export_table_trail_all"))
    if detail not in gets_print.DETAILS:
        raise WorkbookError(i18n.t("server.items_full_selected_nothing_written"))
    bid = str(board.get("id") or "") or None
    # its data made first, dry run or not, so a board or a GET no longer there is refused before a name is given
    data = gets_print.typst_data(root, books, project, bid, what=what, detail=detail, notes=notes, get=get, now=now,
                                 sending=sending, descriptions=descriptions, researcher=researcher)
    template = gets_print.FULL_TEMPLATE if what == "all" else gets_print.TEMPLATE
    parts = gets_print.study_parts(root, books, bid, th.now_iso())
    table = gets_print.gets_table(parts)
    name = project.get("name") or gets_what("all")
    named = "" if sending else f"{board.get('name') or th.FIRST_NAME} - "
    said = f"{name} - {named}{gets_what(what)}" + (f" - {get}" if get else "")
    folder, stem = where_to(out, safe_stem(said), Path(root))
    made = place(folder, stem, replace, now, dry_run, lambda: typeset_pdf(template, data))
    counts = {"gets": len(table), "participants": len(parts["inside"]),
              "trails": len([g for g in table if not get or g["id"] == get]) if what != "table" else 0}
    return dict(made, counts=counts, what=what, detail=detail, notes=bool(notes), get=get or "",
                version={"id": str(board.get("id") or ""), "name": str(board.get("name") or "")})


def __getattr__(name: str) -> str:
    """The refusals other modules and the checks name as this module's, each read in the run's language when
    asked for (the text layer, 28 October 2026)."""
    said = {
        "NOT_PDF": lambda: i18n.t("server.file_out_names_ends_pdf"),
    }
    if name in said:
        return said[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
