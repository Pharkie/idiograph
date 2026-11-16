#!/usr/bin/env python3
"""The exports no screen had before (exportnew, 16 November 2026, Adam: Export on every tab, Option C): the
Trajectories board, the statements screen's annotated transcript, and a thematic analysis project's code list, each
as a print view, a PDF and a Microsoft Word document, the code list as a CSV too. One API: each is a route, a command
and an MCP tool, and the window's menus call the routes.

Each export is first a document, one walk of what the screen holds (`trajectories`, `transcript`, `codes`), which the
three writers read, so the print view, the PDF and Word never disagree: the print view's HTML (`page`), the Typst
data for `typst/document.typ` (`typst_data`), and Word's parts (`word_bytes`). A document is its head (the title,
the table's name under it, the project and the research question), its foot (as every print view's foot: the
project and the document at the left, the researcher, Confidential and the day in the middle, the page at the
right), the participant's label and pen portrait where the export asks for them, and its blocks:

    {"kind": "heading", "level": 1 | 2 | 3, "text": "...", "desc": "..."}
    {"kind": "para", "style": "plain" | "soft" | "note" | "quote", "runs": [{"text", "b", "i", "small"}], "keep"}
    {"kind": "table", "heads": [...], "widths": [2, 3, 3], "rows": [[[para, ...], ...]], "split": [bool, ...]}

A heading, and a paragraph with `keep`, always stays with what follows it, a table's head repeats on every page and
its rows flow across pages, each whole unless its `split` lets a row too long for that run on (Adam's print rules of
31 October 2026: rows flow across pages, a heading never ends one). A run that is `small` is the quiet sans the
print views give a timecode. The print views and the PDFs are A4 landscape, as every print view is; Word's page turns with
the document's widest table.

The Trajectories board (Adam's revD trajectories table): each trajectory under its title and sentence, its
participants in his order, each with their own label and, with Each participant's note ticked, his note on why, then
their LPETs, a row each across the timepoints, the LPET's title and domain, and in each timepoint's cell its key quote
with his bold kept and the state he wrote for it. An LPET he hid on that screen stays out. Unplaced, ticked, sets
out the participants in no trajectory the same way at the end.

The annotated transcript: a participant's transcript, a row each turn, with its exploratory notes at the left and its
experiential statements, each with its quote, at the right (the statements screen's columns, 1 : 3 : 2), and the
interviewer's notes under their turns, each part by its Include tick, the participant's label and pen portrait under
the head with Pen portrait. A workbook of several interviews sets each under its own heading, or one alone with
`sheet`.

The code list: each code in the list's order with its description and how many extracts and participants it has,
and with Extracts (on unless untucked) its extracts by participant, where each was said and its words. Its CSV has a
row for each extract, a code with none a row of its own.

Every file goes where its screen's other exports go, never over a file there unless `replace`, the date and time in
its name when the plain name is taken (`themes_word.free_name`): the Trajectories and the code list at the project's
root, the annotated transcript beside the participant's workbook. Only reads the project's files.
"""
from __future__ import annotations

import csv
import html
import io
import json
import os
import zipfile
from datetime import datetime
from pathlib import Path

import boot
import i18n
import themes as th
import themes_print as tp
import themes_word as tw
from workbook import WorkbookError, no_quote

TEMPLATE = boot.resource("typst") / "document.typ"
KINDS = ("trajectories", "transcript", "codes")
# the formats each export writes as a file, the print view being a page of its own
FORMATS = {"trajectories": ("pdf", "word"), "transcript": ("pdf", "word"), "codes": ("pdf", "word", "csv")}
EXT = {"pdf": ".pdf", "word": ".docx", "csv": ".csv"}

esc = lambda text: html.escape(str(text or ""), quote=True)  # noqa: E731


# ------------------------------------------------------------------ the blocks

def run(text, b: bool = False, i: bool = False, small: bool = False) -> dict:
    return {"text": str(text or ""), "b": bool(b), "i": bool(i), "small": bool(small)}


def para(runs, style: str = "plain", keep: bool = False) -> dict:
    """A paragraph, kept with what follows it with `keep`, as a heading is (a note or a count over a table)."""
    return {"kind": "para", "style": style, "runs": [run(runs)] if isinstance(runs, str) else list(runs), "keep": keep}


def heading(level: int, text: str, desc: str = "") -> dict:
    return {"kind": "heading", "level": level, "text": " ".join(str(text or "").split()),
            "desc": " ".join(str(desc or "").split())}


# the most characters a table's row holds and still stays whole on a page: a turn longer than about half a page's
# column may run on to the next, where a short one never leaves its speaker alone at a page's foot
WHOLE_MOST = 1200


def table(heads: list[str], widths: list[int], rows: list[list[list[dict]]], breakable: bool = False) -> dict:
    """A table, each row whole on a page, or with `breakable` a row too long to stay whole free to run on."""
    split = [breakable and sum(len(r["text"]) for cell in row for p in cell for r in p["runs"]) > WHOLE_MOST
             for row in rows]
    return {"kind": "table", "heads": list(heads), "widths": list(widths), "rows": rows, "split": split}


def quoted_runs(text: str, bold=None) -> list[dict]:
    """A quote in single curly marks, in italics, with his bold kept on its words: `bold` as `[start, end]` spans of
    `text` (the LPET table's row as Trajectories reads it)."""
    text = str(text or "")
    marked = [False] * len(text)
    for span in bold or []:
        try:
            a, b = int(span[0]), int(span[1])
        except (TypeError, ValueError, IndexError):
            continue
        for k in range(max(0, a), min(len(text), b)):
            marked[k] = True
    out: list[dict] = []
    for ch, on in zip(text, marked):
        if out and out[-1]["b"] == on:
            out[-1]["text"] += ch
        else:
            out.append(run(ch, b=on, i=True))
    return [run("‘", i=True), *out, run("’", i=True)]


def document(kind: str, name: str, title: str, head: dict, word: list[str], foot: tuple, blocks: list[dict],
             counts: dict, none: str, who: dict | None = None, landscape: bool = True) -> dict:
    pieces, fit, middle = foot
    return {"kind": kind, "name": name, "title": title, "head": head, "word": word,
            "foot": {"pieces": pieces, "fit": fit, "middle": middle}, "blocks": blocks, "counts": counts,
            "none": none, "who": who, "landscape": landscape}


def foot_of(case: str, project: str, name: str, researcher: str, now: datetime | None) -> tuple:
    """The foot every print view has (Adam, 31 October 2026): at the left the participant where there is one, the
    project and the document, in the middle the researcher, Confidential and the day, the page at the right."""
    _left, middle = tp.foot_parts(case, project, name, researcher, True, day=tp.when_printed(now))
    pieces, fit = tp.foot_pieces(case, project, name, cut_case=False)
    return pieces, fit, middle


def words(text) -> str:
    return " ".join(str(text or "").split())


# ------------------------------------------------------------------ Trajectories

def timepoint_head(label: str, description: str) -> str:
    label, description = words(label), words(description)
    return i18n.t("documents.trajectories.timepoint", label=label, description=description) if description else label


def lpet_rows(card: dict, tps: list[tuple]) -> list[list[list[dict]]]:
    """A participant's LPETs as rows across the timepoints, an LPET hidden on Trajectories left out: its title and
    domain, then at each timepoint its key quote, his bold kept, where it was said, and the state he wrote."""
    out = []
    for r in card.get("rows") or []:
        if r.get("shown") is False:
            continue
        first = [para([run(r.get("title") or th.UNTITLED, b=True)])]
        if words(r.get("domain")):
            first.append(para([run(words(r["domain"]), small=True)], "soft"))
        cells = [first]
        for key, _label, _desc in tps:
            cell = (r.get("cells") or {}).get(key) or {}
            parts = []
            q = cell.get("quote")
            if q and words(q.get("text")):
                said = quoted_runs(q["text"], cell.get("bold"))
                if words(q.get("time")):
                    said.append(run(f"  {words(q['time'])}", small=True))
                parts.append(para(said, "quote"))
            for line in str(cell.get("state") or "").splitlines():
                if line.strip():
                    parts.append(para(line.strip()))
            if not parts and cell.get("missing"):
                parts.append(para(i18n.t("exports.not_interviewed"), "soft"))
            cells.append(parts)
        out.append(cells)
    return out


def trajectories(board: dict, tps: list[tuple], project: dict, notes: bool = False, unplaced: bool = False,
                 researcher: str = "", now: datetime | None = None) -> dict:
    """The Trajectories board as a document. `board` is `trajectories.board`'s, `tps` each timepoint's key, label and
    description, `notes` Each participant's note and `unplaced` Unplaced."""
    name = i18n.t("documents.trajectories.name")
    project_name = words(project.get("name"))
    cards = {c["case"]: c for c in board.get("participants") or []}
    heads = [i18n.t("documents.trajectories.lpet")] + [timepoint_head(label, desc) for _k, label, desc in tps]
    widths = [2] + [3] * len(tps)
    blocks: list[dict] = []
    counts = {"trajectories": 0, "participants": 0, "unplaced": 0, "lpets": 0}

    def person(case: str) -> None:
        c = cards.get(case)
        if c is None:
            return
        blocks.append(heading(2, c.get("who") or case, c.get("title") or ""))
        if notes and words(c.get("note")):
            for line in str(c["note"]).splitlines():
                if line.strip():
                    blocks.append(para(line.strip(), "note", keep=True))
        rows = lpet_rows(c, tps)
        counts["lpets"] += len(rows)
        if rows:
            blocks.append(table(heads, widths, rows))
        else:
            blocks.append(para(i18n.t("documents.trajectories.no_lpets"), "soft"))

    for col in board.get("columns") or []:
        counts["trajectories"] += 1
        blocks.append(heading(1, col.get("title") or th.UNTITLED, col.get("description") or ""))
        for case in col.get("participants") or []:
            counts["participants"] += 1
            person(case)
    left = list(board.get("unplaced") or [])
    counts["unplaced"] = len(left)
    if unplaced and left:
        blocks.append(heading(1, th.counted(i18n.t("documents.trajectories.unplaced"), len(left))))
        for case in left:
            person(case)
    head = {"title": name, "subtitle": "", "project": project_name,
            "question": words(project.get("research_question"))}
    title = i18n.t("documents.file", name=project_name or name, what=name)
    return document("trajectories", name, title, head, [project_name or name, name],
                    foot_of("", project_name, name, researcher, now), blocks, counts,
                    i18n.t("documents.trajectories.none"))


# ------------------------------------------------------------------ the annotated transcript

def transcript(read: dict, case: str, project: dict, who: dict | None = None, notes: bool = True,
               statements: bool = True, interviewer_notes: bool = False, sheet: str | None = None,
               researcher: str = "", now: datetime | None = None) -> dict:
    """A participant's annotated transcript as a document. `read` is `workbook.read_case`'s, `case` the participant's
    label, `who` their label and pen portrait with Pen portrait ticked, and `notes`, `statements` and
    `interviewer_notes` the three Include ticks. `sheet` keeps it to one interview. A sheet the workbook does not
    hold is refused."""
    name = i18n.t("documents.transcript.name")
    sheets = read.get("sheets") or []
    if sheet:
        sheets = [s for s in sheets if s["name"] == sheet]
        if not sheets:
            raise WorkbookError(i18n.t("documents.transcript.no_sheet", sheet=words(sheet)))
    heads, widths = [], []
    if notes:
        heads.append(i18n.t("documents.transcript.notes"))
        widths.append(1)
    heads.append(i18n.t("documents.transcript.transcript"))
    widths.append(3)
    if statements:
        heads.append(i18n.t("documents.transcript.statements"))
        widths.append(2)
    blocks: list[dict] = []
    counts = {"interviews": len(sheets), "passages": 0, "statements": 0, "notes": 0, "interviewer_notes": 0}
    noted = i18n.t("documents.transcript.interviewer_note")
    for s in sheets:
        if len(sheets) > 1 or sheet:
            blocks.append(heading(1, s["name"]))
        rows = []
        for r in s.get("rows") or []:
            counts["passages"] += 1
            said = []
            top = [run(words(r.get("name")), b=True)] if words(r.get("name")) else []
            if words(r.get("time")):
                top.append(run(("  " if top else "") + words(r["time"]), small=True))
            if top:
                said.append(para(top))
            for line in str(r.get("text") or "").splitlines():
                if line.strip():
                    said.append(para(line.strip()))
            if words(r.get("note")):
                counts["interviewer_notes"] += 1
                if interviewer_notes:
                    for line in str(r["note"]).splitlines():
                        if line.strip():
                            said.append(para([run(f"{noted}: ", i=True), run(line.strip(), i=True)], "note"))
            cells = []
            if notes:
                mine = [para(line.strip(), "soft") for line in str(r.get("en") or "").splitlines() if line.strip()]
                counts["notes"] += len(mine)
                cells.append(mine)
            cells.append(said)
            pairs = [p for p in r.get("pairs") or [] if words(p.get("es")) or words(p.get("kq"))]
            counts["statements"] += sum(1 for p in pairs if words(p.get("es")))
            if statements:
                mine = []
                for p in pairs:
                    if words(p.get("es")):
                        mine.append(para(words(p["es"])))
                    if words(p.get("kq")) and not no_quote(p["kq"]):
                        mine.append(para(quoted_runs(words(th.bare(p["kq"]))), "quote"))
                cells.append(mine)
            rows.append(cells)
        if rows:
            blocks.append(table(heads, widths, rows, breakable=True))
    project_name = words(project.get("name"))
    head = {"title": tp.case_title(case), "subtitle": name, "project": project_name,
            "question": words(project.get("research_question"))}
    title = i18n.t("documents.file", name=case, what=name)
    return document("transcript", name, title, head, [tp.case_title(case), name],
                    foot_of(tp.case_title(case), project_name, name, researcher, now), blocks, counts,
                    i18n.t("documents.transcript.none"), who=who)


# ------------------------------------------------------------------ the code list

def codes(listing: dict, project: dict, extracts: bool = True, researcher: str = "",
          now: datetime | None = None) -> dict:
    """A thematic analysis project's code list as a document. `listing` is `codes.listing`'s, `extracts` the Extracts
    tick: each code with its extracts by participant, or without it one table of the codes with their counts."""
    name = i18n.t("documents.codes.name")
    blocks: list[dict] = []
    listed = listing.get("codes") or []
    if extracts:
        heads = [i18n.t("documents.codes.participant"), i18n.t("documents.codes.where"),
                 i18n.t("documents.codes.extract")]
        for c in listed:
            blocks.append(heading(2, c["name"], c.get("description") or ""))
            blocks.append(para([run(counted(c), small=True)], "soft", keep=True))
            rows = []
            for by in c.get("by") or []:
                for x in by.get("extracts") or []:
                    where = ", ".join(w for w in (words(x.get("sheet")), words(x.get("time"))) if w)
                    said = [para(quoted_runs(words(th.bare(x["quote"]))), "quote")] if words(x.get("quote")) else []
                    rows.append([[para(by["who"])], [para([run(where, small=True)])], said])
            if rows:
                blocks.append(table(heads, [2, 2, 8], rows))
            else:
                blocks.append(para(i18n.t("documents.codes.no_extract"), "soft"))
    elif listed:
        heads = [i18n.t("documents.codes.code"), i18n.t("documents.codes.description"),
                 i18n.t("documents.codes.extracts"), i18n.t("documents.codes.participants")]
        rows = [[[para([run(c["name"], b=True)])], [para(c.get("description") or "", "soft")] if c.get("description") else [],
                 [para(str(c.get("extracts") or 0))], [para(str(c.get("participants") or 0))]] for c in listed]
        blocks.append(table(heads, [4, 8, 1, 1], rows))
    total = listing.get("total") or {}
    counts = {"codes": len(listed), "extracts": int(total.get("extracts") or 0),
              "participants": int(total.get("participants") or 0)}
    project_name = words(project.get("name"))
    head = {"title": name, "subtitle": "", "project": project_name, "question": words(project.get("research_question"))}
    title = i18n.t("documents.file", name=project_name or name, what=name)
    return document("codes", name, title, head, [project_name or name, name],
                    foot_of("", project_name, name, researcher, now), blocks, counts,
                    i18n.t("documents.codes.none"), landscape=extracts is False)


def counted(c: dict) -> str:
    return i18n.t("documents.codes.counted", extracts=i18n.t("documents.codes.n_extracts", n=int(c.get("extracts") or 0)),
                  participants=i18n.t("documents.codes.n_participants", n=int(c.get("participants") or 0)))


def codes_csv(listing: dict) -> bytes:
    """The code list as a CSV, in UTF-8 with its mark so Excel reads it as such: a row for each extract, its code,
    the code's description, the participant, the interview, the timecode and the extract's words, and a code with no
    extract a row of its own with those empty."""
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow([i18n.t("documents.codes.code"), i18n.t("documents.codes.description"),
                i18n.t("documents.codes.participant"), i18n.t("exports.csv_interview"),
                i18n.t("exports.csv_timestamp"), i18n.t("documents.codes.extract")])
    for c in listing.get("codes") or []:
        rows = [(by["who"], x) for by in c.get("by") or [] for x in by.get("extracts") or []]
        if not rows:
            w.writerow([c["name"], c.get("description") or "", "", "", "", ""])
        for who, x in rows:
            w.writerow([c["name"], c.get("description") or "", who, x.get("sheet") or "", x.get("time") or "",
                        x.get("quote") or ""])
    return ("﻿" + out.getvalue()).encode("utf-8")


# ------------------------------------------------------------------ the print view

PAGE_CSS = """
main { font-family: var(--serif); }
.dh { margin: 0; break-after: avoid; page-break-after: avoid; break-inside: avoid; }
.dh1 { font-weight: normal; font-size: 15pt; line-height: 1.3; margin: 16pt 0 6pt; padding-bottom: 3pt;
  border-bottom: 1px solid var(--rule-firm); }
main > .dh1:first-child { margin-top: 0; }
.dh2 { font-weight: bold; font-size: 12pt; line-height: 1.3; margin: 12pt 0 4pt; }
.dh3 { font-family: var(--sans); font-weight: 600; font-size: 10pt; margin: 10pt 0 3pt; }
.dh .desc { display: block; font-family: var(--serif); font-weight: normal; font-size: 10pt; line-height: 1.35;
  color: var(--ink-soft); margin-top: 1pt; }
main p { margin: 0 0 4pt; font-size: 10pt; line-height: 1.4; }
main p.soft { color: var(--ink-soft); }
main p.keep { break-after: avoid; page-break-after: avoid; }
main p.note { color: var(--ink-soft); font-style: italic; }
main p.quote { font-size: 9.5pt; }
.sm { font-family: var(--sans); font-size: 7pt; font-style: normal; font-weight: normal; color: var(--ink-faint); }
table.dt { width: 100%; border-collapse: collapse; table-layout: fixed; margin: 4pt 0 10pt; }
table.dt thead { display: table-header-group; }
table.dt th { font-family: var(--sans); font-size: 7.5pt; font-weight: 600; letter-spacing: .08em; text-transform: uppercase;
  color: var(--ink-faint); text-align: left; vertical-align: bottom; padding: 2pt 6pt 3pt; border-bottom: 1px solid var(--rule-firm); }
table.dt td { vertical-align: top; padding: 4pt 6pt; border-bottom: 1px solid var(--rule); }
table.dt td p { font-size: 9.5pt; margin: 0 0 3pt; }
table.dt td p:last-child { margin-bottom: 0; }
table.dt tr.whole { break-inside: avoid; page-break-inside: avoid; }
p.none { color: var(--ink-soft); }
"""


def runs_html(runs: list[dict]) -> str:
    out = []
    for r in runs:
        text = esc(r["text"])
        if r.get("small"):
            out.append(f'<span class="sm">{text}</span>')
            continue
        if r.get("b"):
            text = f"<b>{text}</b>"
        if r.get("i"):
            text = f"<i>{text}</i>"
        out.append(text)
    return "".join(out)


def para_html(p: dict) -> str:
    style = (p.get("style") or "plain") + (" keep" if p.get("keep") else "")
    return f'<p class="{esc(style)}">{runs_html(p["runs"])}</p>'


def block_html(b: dict) -> str:
    if b["kind"] == "heading":
        tag = {1: "h2", 2: "h3"}.get(b["level"], "h4")
        desc = f'<span class="desc">{esc(b["desc"])}</span>' if b.get("desc") else ""
        return f'<{tag} class="dh dh{b["level"]}">{esc(b["text"])}{desc}</{tag}>'
    if b["kind"] == "para":
        return para_html(b)
    if b["kind"] == "table":
        total = sum(b["widths"]) or 1
        cols = "".join(f'<col style="width: {w * 100 / total:.2f}%">' for w in b["widths"])
        head = "".join(f"<th>{esc(h)}</th>" for h in b["heads"])
        rows = "".join(("<tr>" if split else '<tr class="whole">')
                       + "".join("<td>" + "".join(para_html(p) for p in cell) + "</td>" for cell in row)
                       + "</tr>" for row, split in zip(b["rows"], b["split"]))
        return f'<table class="dt"><colgroup>{cols}</colgroup><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>'
    return ""


def who_html(who: dict | None) -> list[str]:
    if not who:
        return []
    out = tp.who_html(who)
    if who.get("values") and out:
        out.insert(-1, f'<p class="who-portrait">{esc(who["values"])}</p>')
    return out


def page(doc: dict, auto: bool = True) -> str:
    """The document as its print view, one HTML page in the print views' faces and head, which the window prints or
    a browser saves as PDF. `auto` opens the print dialog once the fonts have loaded."""
    h = doc["head"]
    head = ['<header class="head">', '<div class="top">', '<div class="titles">', f'<h1>{esc(h["title"])}</h1>']
    if h.get("subtitle"):
        head.append(f'<p class="table-name">{esc(h["subtitle"])}</p>')
    head += ["</div>", *tp.about_block(h["project"], h["question"]), "</div>", "</header>"]
    head += who_html(doc.get("who"))
    body = [block_html(b) for b in doc["blocks"]] or [f'<p class="none">{esc(doc["none"])}</p>']
    f = doc["foot"]
    style = f"{tp.HEAD}{tp.PAGE}{PAGE_CSS}{tp.TAIL}"
    middle = f["middle"]
    left = "".join(f["pieces"])
    script = ("document.getElementById('print').onclick = () => window.print();"
              "if (AUTO) { const ready = document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve();"
              " ready.then(() => setTimeout(() => window.print(), 150)); }")
    return "\n".join([
        "<!doctype html>", f'<html lang="{tp.page_lang()}">', "<head>", '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{esc(doc['title'])}</title>", tp.FONTS_LINK,
        f"<style>{style}{tp.page_foot(f['pieces'], middle, numbered=True, fit=f['fit'])}</style>", "</head>", "<body>",
        f'<div class="controls noprint"><button type="button" id="print">{esc(i18n.t("page_print.print"))}</button></div>',
        *head, "<main>", *body, "</main>",
        f"<footer>{esc(left + ('  ' + chr(183) + '  ' + middle if middle else ''))}</footer>",
        tp.foot_fit(f["pieces"], f["fit"], middle, style),
        f"<script>const AUTO = {'true' if auto else 'false'};{script}</script>", "</body>", "</html>", ""])


# ------------------------------------------------------------------ the PDF

def typst_data(doc: dict) -> dict:
    """The document as `typst/document.typ` takes it, every word the page prints in the run's language."""
    lang = tp.page_lang()
    page_of = i18n.t("page_print.page_of", page="\x00", pages="\x01")
    before, rest = page_of.split("\x00", 1) if "\x00" in page_of else (page_of, "")
    between, after = rest.split("\x01", 1) if "\x01" in rest else (rest, "")
    f = doc["foot"]
    out = {"title": doc["title"], "lang": lang.split("-")[0], "region": (lang.split("-") + [""])[1],
           "head": dict(doc["head"], labels={"project": i18n.t("page_print.project"),
                                             "question": i18n.t("page_print.research_question")}),
           "foot": {"left": [p for p in f["pieces"] if p], "fit": f["fit"], "middle": f["middle"],
                    "page": [before, between, after]},
           "blocks": doc["blocks"], "none": doc["none"]}
    if doc.get("who"):
        out["who"] = {k: doc["who"].get(k) or "" for k in ("label", "values", "portrait")}
    return out


def pdf_bytes(doc: dict) -> bytes:
    import print_pdf
    return print_pdf.typeset_pdf(TEMPLATE, typst_data(doc))


# ------------------------------------------------------------------ Word

# the type in Word's tables, 10pt, a timecode's 7pt in a grey, the soft ink's grey for a note and a state
WORD_SMALL, WORD_GREY, WORD_SOFT = 14, "756A5C", "554C41"
# A4's width less margins of an inch, upright and on its side, in twentieths of a point
WORD_WIDTH = {False: 11906 - 2 * 1440, True: 16838 - 2 * 1440}


def para_xml(p: dict, size: int, indent: bool = False) -> str:
    style = p.get("style") or "plain"
    ind = f'<w:ind w:left="{tw.SET_IN}"/>' if indent else ""
    keep = "<w:keepNext/>" if p.get("keep") else ""
    props = f'<w:pPr>{keep}<w:spacing w:before="0" w:after="60"/>{ind}</w:pPr>'
    runs = []
    for r in p["runs"]:
        small = r.get("small")
        marks = (("<w:b/><w:bCs/>" if r.get("b") else "") + ("<w:i/><w:iCs/>" if r.get("i") or style == "note" else ""))
        colour = WORD_GREY if small else WORD_SOFT if style in ("soft", "note") else ""
        marks += f'<w:color w:val="{colour}"/>' if colour else ""
        n = WORD_SMALL if small else size
        marks += f'<w:sz w:val="{n}"/><w:szCs w:val="{n}"/>'
        runs.append(f'<w:r><w:rPr>{marks}</w:rPr><w:t xml:space="preserve">{tw.xml_text(r["text"])}</w:t></w:r>')
    return f"<w:p>{props}{''.join(runs)}</w:p>"


def cell_xml(paras: list[dict], width: int, head: str | None = None) -> str:
    rule = (f'<w:tcBorders><w:bottom w:val="single" w:sz="6" w:space="0" w:color="{tw.TABLE_RULE_FIRM}"/></w:tcBorders>'
            if head is not None else "")
    if head is not None:
        inner = (f'<w:p><w:pPr><w:spacing w:before="0" w:after="0"/></w:pPr><w:r><w:rPr><w:b/><w:bCs/>'
                 f'<w:sz w:val="{tw.TABLE_SIZE}"/><w:szCs w:val="{tw.TABLE_SIZE}"/></w:rPr>'
                 f'<w:t xml:space="preserve">{tw.xml_text(head)}</w:t></w:r></w:p>')
    else:
        inner = "".join(para_xml(p, tw.TABLE_SIZE) for p in paras) or "<w:p/>"
    return f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{rule}</w:tcPr>{inner}</w:tc>'


def table_xml(b: dict, room: int) -> str:
    total = sum(b["widths"]) or 1
    widths = [room * w // total for w in b["widths"]]
    widths[-1] += room - sum(widths)
    rules = (f'<w:tblBorders><w:top w:val="single" w:sz="6" w:space="0" w:color="{tw.TABLE_RULE_FIRM}"/>'
             f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="{tw.TABLE_RULE_FIRM}"/>'
             f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{tw.TABLE_RULE}"/></w:tblBorders>')
    margins = ('<w:tblCellMar><w:top w:w="60" w:type="dxa"/><w:left w:w="100" w:type="dxa"/>'
               '<w:bottom w:w="60" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tblCellMar>')
    rows = ['<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>'
            + "".join(cell_xml([], w, head=h) for h, w in zip(b["heads"], widths)) + "</w:tr>"]
    rows += [f"<w:tr><w:trPr>{'' if split else '<w:cantSplit/>'}</w:trPr>"
             + "".join(cell_xml(c, w) for c, w in zip(row, widths)) + "</w:tr>"
             for row, split in zip(b["rows"], b["split"])]
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    # a paragraph after it, as Word needs between two tables and the space a table wants under it
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{room}" w:type="dxa"/>{rules}<w:tblLayout w:type="fixed"/>{margins}'
            f'</w:tblPr><w:tblGrid>{grid}</w:tblGrid>' + "".join(rows) + '</w:tbl><w:p/>')


def word_paragraphs(doc: dict) -> list[str]:
    room = WORD_WIDTH[doc["landscape"]]
    first, second = doc["word"]
    out = [tw.paragraph({"style": 1, "runs": [tw.run(first)]}), tw.paragraph({"style": tw.SUBTITLE, "runs": [tw.run(second)]})]
    out += [tw.paragraph(p) for p in tw.who_blocks(doc.get("who"))]
    if doc.get("who") and doc["who"].get("values"):
        out.append(tw.paragraph({"style": 0, "runs": [tw.run(doc["who"]["values"])]}))
    for b in doc["blocks"]:
        if b["kind"] == "heading":
            runs = [tw.run(b["text"], bold=True)]
            if b.get("desc"):
                runs.append(dict(tw.run(b["desc"]), desc=True))
            out.append(tw.paragraph({"style": min(tw.DEEPEST, b["level"] + 1), "runs": runs}))
        elif b["kind"] == "para":
            out.append(para_xml(b, tw.SIZE, indent=b.get("style") == "quote"))
        elif b["kind"] == "table":
            out.append(table_xml(b, room))
    if not doc["blocks"]:
        out.append(para_xml(para(doc["none"], "soft"), tw.SIZE))
    return out


def word_bytes(doc: dict, author: str = "", now: datetime | None = None) -> bytes:
    """The document as a Word file, Word's own heading styles as the table of PETs' Word has them, its tables plain
    with their heads repeated on each page, A4 on its side for a table of four columns or more."""
    now = now or datetime.now().astimezone()
    wide = doc["landscape"]
    size = ('<w:pgSz w:w="16838" w:h="11906" w:orient="landscape"/>' if wide else '<w:pgSz w:w="11906" w:h="16838"/>')
    section = (f'<w:sectPr>{size}<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" '
               'w:footer="708" w:gutter="0"/></w:sectPr>')
    body = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:document xmlns:w="{tw.W}" xmlns:r="{tw.R}">'
            "<w:body>" + "".join(word_paragraphs(doc)) + section + "</w:body></w:document>")
    parts = tw.parts([], doc["title"], now, author)
    parts["word/document.xml"] = body
    stamp = now.timetuple()[:6]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for name, text in parts.items():
            info = zipfile.ZipInfo(name, date_time=stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, text.encode("utf-8"))
    return buffer.getvalue()


# ------------------------------------------------------------------ the file

def where_to(out, stem: str, default: Path, ext: str) -> tuple[Path, str]:
    """The folder and the name without its ending that `out` names: a folder there, the file named as the print view
    names it, or a file ending `ext` in a folder there. With no `out`, `default`."""
    if out is None or not str(out).strip():
        return Path(default), stem
    given = Path(str(out).strip()).expanduser()
    if given.is_dir():
        return given.resolve(), stem
    if given.suffix.lower() != ext or not given.parent.is_dir():
        raise WorkbookError(i18n.t("documents.out_refused", ext=ext))
    return given.parent.resolve(), " ".join(given.stem.translate(th.UNSAFE).split()) or stem


def place(folder: Path, stem: str, ext: str, replace: bool, now: datetime, dry_run: bool, make) -> dict:
    """Put the bytes `make()` makes at `folder`/`stem` with `ext`, never over a file there unless `replace`, and then
    by a whole new file put in its place, otherwise with the date and time in the name. With `dry_run` nothing is
    made or written, and the answer names the file it would write."""
    plain = folder / f"{stem}{ext}"
    if replace:
        path, dated = plain, False
    else:
        path, dated = tw.free_name(folder, stem, now, ext)
    out = {"path": str(path), "name": path.name, "folder": str(folder), "dated": dated,
           "replaced": bool(replace and plain.exists())}
    if dry_run:
        return dict(out, dry_run=True)
    # made before a file is opened, so a failure writes nothing
    data = make()
    if replace:
        part = folder / f".{stem}{ext}.part"
        part.write_bytes(data)
        os.replace(part, path)
        return out
    while True:
        try:
            with open(path, "xb") as handle:
                try:
                    handle.write(data)
                except BaseException:
                    handle.close()
                    path.unlink(missing_ok=True)
                    raise
            break
        except FileExistsError:
            path, dated = tw.free_name(folder, stem, now, ext)
    return dict(out, path=str(path), name=path.name, dated=dated)


def write(doc: dict, fmt: str, folder: Path, out=None, replace: bool = False, dry_run: bool = False,
          author: str = "", now: datetime | None = None, csv_of=None) -> dict:
    """Write the document as `fmt`, pdf, word or csv (the code list's alone, `csv_of` making its bytes), where its
    screen's exports go, `folder`, or where `out` names. The answer names the file and gives the document's counts."""
    if fmt not in FORMATS[doc["kind"]]:
        raise WorkbookError(i18n.t("documents.format_refused", formats=", ".join(FORMATS[doc["kind"]])))
    now = now or datetime.now().astimezone()
    ext = EXT[fmt]
    where, stem = where_to(out, " ".join(doc["title"].translate(th.UNSAFE).split()) or doc["name"], Path(folder), ext)
    make = {"pdf": lambda: pdf_bytes(doc), "word": lambda: word_bytes(doc, author, now),
            "csv": lambda: csv_of()}[fmt]
    made = place(where, stem, ext, replace, now, dry_run, make)
    return dict(made, format=fmt, kind=doc["kind"], counts=doc["counts"])
