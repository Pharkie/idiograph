"""Trace's routes on the family's server (22 October 2026, the family codebase's second build, from
server.py): its projects, `/api/trace-project`, a project's manuscripts, claims and acts, `/api/trace`, a
reference's PDF for the pane, `/trace/pdf`, its cards on the home screen and its Search, each registered
with the server by `register`, which the server's start imports this module for (`boot.load`).

Trace (15 October), the third part beside Sift and Distil (see `trace_claims.py`). A Trace project is a
folder of its own, kept in the list of Trace projects, `trace_projects` in the app's state, newest first,
which the home screen's Trace section lists. New project makes one and Open project folder takes one,
writing nothing into it, Sift's Check references folder of 14 October among them, read in place. A route
reads or writes a project's files only when the list holds it. Its name is kept in the list, as a Sift
project's is, renamed under Trace in Settings.

A reference's PDF is found in the project's `pdfs/` and in the screenings of Sift's projects: Idiograph's
list of them while the run serves Sift too, and in Trace's own app Sift's own list, read and never
written (`screenings.reviews_in`, Adam's call of 22 October).

The server's names are read from it as each request comes, `srv.PICK_FOLDER` and the rest, so a check
that stands in a dialog or a platform of its own is heard here too.
"""
from __future__ import annotations

import base64
import binascii
import time
from pathlib import Path

import ai_suggest as ai_mod
import app_search
import i18n
import pdftext
import screenings
import server as srv
import trace_claims as trace_mod
import trace_find

# The words this module says, read in the run's language when said (i18nleft4, 2 November 2026): other
# modules and the checks read them as the module's names, through `__getattr__`, as themes_ai's are
SAID = {
    "NEW_TRACE_PROMPT": lambda **v: i18n.t("trace_server.said.new_trace_prompt", v),
    "OPEN_TRACE_PROMPT": lambda **v: i18n.t("trace_server.said.open_trace_prompt", v),
    "TRACE_NOT_OPENED": lambda **v: i18n.t("trace_server.said.trace_not_opened", v),
    "TRACE_NOT_MADE": lambda **v: i18n.t("trace_server.said.trace_not_made", v),
    "TRACE_PROMPT": lambda **v: i18n.t("trace_server.said.trace_prompt", v),
}


def _w(name: str, **vals) -> str:
    return SAID[name](**vals)


def __getattr__(name: str) -> str:
    """This module's words other modules and the checks name, read in the run's language."""
    if name in SAID:
        return SAID[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

TRACES_KEPT = 16
TRACE_PDF_PATH = "/trace/pdf"
# a PDF he adds for a reference, the most it may be, as a record's PDF in Sift
PDF_MAX = 200 * 1024 * 1024


# ------------------------------------------------------------------ the list

def traces_kept() -> list[dict]:
    """The Trace projects in the list, newest first, each `{"folder", "opened"}` and `name` when he gave one."""
    rows = srv.state().get("trace_projects")
    return [e for e in rows if isinstance(e, dict) and e.get("folder")] if isinstance(rows, list) else []


def kept_trace(folder: Path) -> dict | None:
    return next((e for e in traces_kept() if srv.same_folder(srv.abs_path(e["folder"]), folder)), None)


def remember_trace(folder: Path, name: str | None = None) -> None:
    """A Trace project to the head of the list, with the name he gave, or the one it had when that is None."""
    data = srv.state()
    kept = traces_kept()
    was = next((e for e in kept if srv.same_folder(srv.abs_path(e["folder"]), folder)), None)
    entry = {"folder": srv.rel_path(folder), "opened": int(time.time())}
    given = (was or {}).get("name") if name is None else name
    if given:
        entry["name"] = given
    data["trace_projects"] = ([entry] + [e for e in kept if e is not was])[:TRACES_KEPT]
    srv.save_state(data)


def trace_name(folder: Path, entry: dict | None = None) -> str:
    """A Trace project's name: the one he gave, else its own."""
    return str((entry or {}).get("name") or "") or trace_mod.own_name(folder)


def edit_trace(folder: Path, name) -> None:
    """A Trace project's name as he gave it under Trace in Settings, kept in its entry in the list in place
    and never in its folder, one the same as its own leaving the entry without one."""
    data = srv.state()
    kept = traces_kept()
    entry = next((e for e in kept if srv.same_folder(srv.abs_path(e["folder"]), folder)), None)
    if entry is None:
        raise srv.OutsideRoot(_w("TRACE_NOT_OPENED"))
    entry = dict(entry)
    given = pdftext.one_line(name)[:120]
    if given and given != trace_mod.own_name(folder):
        entry["name"] = given
    else:
        entry.pop("name", None)
    data["trace_projects"] = [entry if srv.same_folder(srv.abs_path(e["folder"]), folder) else e for e in kept]
    srv.save_state(data)


def forget_trace(folder: Path) -> str:
    """A Trace project taken out of the list, its folder and every file in it left as they are."""
    data = srv.state()
    kept = traces_kept()
    entry = next((e for e in kept if srv.same_folder(srv.abs_path(e["folder"]), folder)), None)
    if entry is None:
        raise srv.OutsideRoot(_w("TRACE_NOT_OPENED"))
    name = trace_name(folder, entry) if folder.is_dir() else str(entry.get("name") or folder.name)
    data["trace_projects"] = [e for e in kept if e is not entry]
    srv.save_state(data)
    return name


def trace_folder(value) -> Path:
    """A Trace project's folder from a request, refused unless the list holds it."""
    folder = srv.there_folder(value)
    if kept_trace(folder) is None:
        raise srv.OutsideRoot(_w("TRACE_NOT_OPENED"))
    return folder


def trace_view(folder: Path) -> dict:
    """A Trace project as its screen names it: its folder as the page names it back and its name."""
    return {"folder": srv.rel_path(folder), "name": trace_name(folder, kept_trace(folder))}


def trace_rows() -> list[dict]:
    """The home screen's Trace cards: each project in the list, its folder as the page names it back, its
    name, the folder above it, whether it is there and its one line. Only reads."""
    out = []
    for e in traces_kept():
        folder = srv.abs_path(e["folder"])
        there = folder.is_dir()
        out.append({"folder": e["folder"], "name": trace_name(folder, e) if there else (e.get("name") or folder.name),
                    "where": srv.display_path(srv.rel_path(folder.parent)), "there": there, "opened": e.get("opened"),
                    "line": trace_mod.stands(folder) if there else i18n.t("trace_server.trace_rows.not_there_now")})
    return out


# ------------------------------------------------------------ Sift's screenings

# where Sift's own app keeps its list of projects, its state file and the folder its paths start from,
# asked as each lookup comes, so a check can stand in a list of its own
SIFT_PATHS = lambda: srv.app_paths(app="sift")  # noqa: E731


def trace_screenings() -> list[Path]:
    """Every screening of every Sift project he keeps, its own and each run's, where a reference's PDF and
    Zotero item may be found by its DOI or title: Sift's own list of its projects, read and never written.
    Only reads."""
    held = SIFT_PATHS()
    folders = screenings.reviews_in(held["state"], held["base"])
    out = []
    for folder in folders:
        if folder.is_dir():
            out += screenings.of_review(folder)
    return out


def found_in() -> list[Path]:
    """The screenings `trace_screenings` gives, or none when they cannot be read, for the command line."""
    try:
        return trace_screenings()
    except (OSError, ValueError, srv.WorkbookError):
        return []


# ------------------------------------------------------------------ the routes

def new_trace_place(value) -> Path:
    """The folder New project was given, refused in one line when it holds a Trace project. Writes nothing."""
    folder = srv.there_folder(value)
    if trace_mod.is_project(folder):
        raise srv.WorkbookError(i18n.t("trace_server.new_trace_place.that_folder_holds_a_trace_project"))
    return folder


def api_trace_project(body: dict) -> dict:
    """Trace's projects, with `op`, as Sift's are: `folder` takes the folder typed as `path`, or with none
    the Mac's folder dialog, whose Cancel answers `chosen` false, for New project with `mode` new or Open
    project folder with `mode` open, and answers the folder and the name the card fills in. `new` makes a
    project in `folder`, or in a new folder inside it named for the project when it holds anything, and
    keeps it in the list. `open` keeps a project that stands in the list, writing nothing into it. `read`
    is a project the list holds. `rename` keeps the `name` he gives one under Trace in Settings in the list,
    and `forget` takes one out of the list, its folder and files left as they are or with `trash` moved to the
    Trash, each answering the cards afresh as `traces`. `reveal` shows a project's folder in the Finder or Explorer and writes nothing (barsD)."""
    op = str(body.get("op") or "")
    if op == "folder":
        mode = "open" if body.get("mode") == "open" else "new"
        if str(body.get("path") or "").strip():
            chosen = body["path"]
        else:
            if srv.PLATFORM != "darwin":
                raise srv.WorkbookError(srv.NO_DIALOG)
            chosen = srv.PICK_FOLDER(_w("OPEN_TRACE_PROMPT") if mode == "open" else _w("NEW_TRACE_PROMPT"))
            if chosen is None:
                return {"chosen": False}
        if mode == "open":
            folder = trace_mod.to_open(srv.there_folder(chosen)).resolve()
            return {"chosen": True, "folder": str(folder), "name": trace_name(folder, kept_trace(folder))}
        folder = new_trace_place(chosen)
        return {"chosen": True, "folder": str(folder), "name": folder.name if srv.is_empty(folder) else ""}
    if op == "new":
        place = new_trace_place(body.get("folder"))
        name = pdftext.one_line(body.get("name"))
        if not name:
            raise srv.WorkbookError(i18n.t("trace_server.api_trace_project.name_the_project_first"))
        target = srv.review_target(place, name)
        with srv._lock:
            made = not target.exists()
            try:
                trace_mod.make(target, name)
            except OSError:
                try:
                    trace_mod.project_file(target).unlink(missing_ok=True)
                    if made:
                        target.rmdir()
                except OSError:
                    pass
                raise srv.WorkbookError(_w("TRACE_NOT_MADE")) from None
            remember_trace(target.resolve(), "")
        return {"made": True, "project": trace_view(target.resolve())}
    if op == "open":
        folder = trace_mod.to_open(srv.there_folder(body.get("folder"))).resolve()
        given = pdftext.one_line(body.get("name"))
        with srv._lock:
            remember_trace(folder, given if given != trace_mod.own_name(folder) else "")
        return {"opened": True, "project": trace_view(folder)}
    if op == "read":
        return {"project": trace_view(trace_folder(body.get("folder")))}
    if op == "rename":
        folder = trace_folder(body.get("folder"))
        with srv._lock:
            edit_trace(folder, body.get("name"))
        return {"project": trace_view(folder), "traces": trace_rows()}
    if op == "forget":
        text = str(body.get("folder") or "").strip()
        if not text:
            raise srv.WorkbookError(i18n.t("trace_server.api_trace_project.name_the_folder_first"))
        folder = srv.abs_path(text)
        trash, where = body.get("trash") is True, ""
        if trash:
            # his tick on Remove's card (removetrash, 10 November 2026): the folder to the system's Trash first, a
            # move refused keeping the project in the list
            entry = kept_trace(folder)
            if entry is None:
                raise srv.OutsideRoot(_w("TRACE_NOT_OPENED"))
            named = trace_name(folder, entry) if folder.is_dir() else str(entry.get("name") or folder.name)
            chosen = srv.trash_guard(folder, named, lambda at: srv.inside(srv.abs_path(at), folder),
                                     str(body.get("page") or ""))
            where = srv.trash_move(chosen, named)
        with srv._lock:
            name = forget_trace(folder)
        srv.record_removal(name, folder, trash)
        return {"forgotten": True, "name": name, "trash": trash, "where": where, "traces": trace_rows()}
    if op == "reveal":
        # Show in Finder on the project's menu, on its card on Home and behind its name in the bar (barsD)
        return srv.reveal_folder(trace_folder(body.get("folder")))
    raise srv.WorkbookError(i18n.t("trace_server.api_trace_project.the_op_is_folder_new_open"))


def trace_docs(folder: Path) -> list[dict]:
    """The manuscripts of a project, each path as a line on the screen shows one."""
    return [dict(d, path=srv.display_path(srv.rel_path(Path(d["path"])))) for d in trace_mod.docs(folder)]


def trace_list(folder: Path) -> dict | None:
    """The project's reference list, its path as a line on the screen shows one, or None."""
    held = trace_mod.list_of(folder)
    return dict(held, path=srv.display_path(srv.rel_path(Path(held["path"]))), there=Path(held["path"]).is_file()) if held else None


def api_trace(body: dict) -> dict:
    """Trace on a project in the list, with `op`: `list`, its manuscripts, its reference list and `choose`,
    whether the Mac's file dialog is there, `add`, a manuscript or a reference list by its typed `path` or
    with none through that dialog, `chosen` false for a Cancel, read once and never written, `read`, a
    manuscript's claims as it now reads, `doc`, or with none the reference list alone, with its sections,
    what Undo would take back, the app's AI switch and the model its calls go to, `judge`, Y, Q or N on a
    claim, `claim` and `value`, and `note`, his note on one, each a line of the log answering the claim's
    state and Undo, `undo`, `open`, a reference's PDF opened in the computer's own app, nothing written,
    `pdf`, a PDF he adds for a reference, `data` in base64, kept in the project's pdfs/ and never over one
    there, and with the app's AI switch on `plan`, the references AI find passages for the rows shown,
    `ids`, would ask about, and `passages`, the AI's passages for one reference, each found in the PDF's
    own text before it is kept, never setting a judgement. A project the list does not hold is refused, 403."""
    op = str(body.get("op") or "list")
    folder = trace_folder(body.get("folder"))
    cfg = srv.config()
    found_in = trace_screenings()
    if op == "list":
        return {"docs": trace_docs(folder), "list": trace_list(folder), "choose": srv.PLATFORM == "darwin",
                "project": trace_view(folder)}
    if op == "add":
        text = str(body.get("path") or "").strip()
        if text:
            target = srv.abs_path(text)
        else:
            if srv.PLATFORM != "darwin":
                raise srv.WorkbookError(srv.NO_FILE_DIALOG)
            picked = srv.PICK_FOLDER(_w("TRACE_PROMPT"), files=True)
            if picked is None:
                return {"chosen": False, "docs": trace_docs(folder), "list": trace_list(folder)}
            target = picked
        with srv._lock:
            added = trace_mod.add(folder, target)
        return dict(added, chosen=True, docs=trace_docs(folder), list=trace_list(folder))
    doc = str(body.get("doc") or "")
    passages_on = srv.ai_on(cfg, "passages")
    if op == "read":
        if doc:
            analysis = trace_mod.analyse(trace_mod.doc_entry(folder, doc)["path"], trace_mod.listed(folder))
            view = trace_mod.rows(folder, doc, analysis, found_in)
            with srv._lock:
                trace_mod.refresh(folder, view["doc"], analysis)
                remember_trace(folder)
            view["path"] = srv.display_path(srv.rel_path(Path(view["path"])))
        else:
            view = trace_mod.list_rows(folder, found_in)
        for row in view["rows"]:
            row["zotero"] = srv.zotero_item_link(cfg, row["zotero"])
            if not passages_on:
                row["passage"], row["passages"] = None, None
        return dict(view, docs=trace_docs(folder), list=trace_list(folder), project=trace_view(folder),
                    config={"ai_suggest": passages_on}, model_name=srv.ai_model_words(cfg) if passages_on else "")
    if op in ("judge", "note"):
        with srv._lock:
            done = trace_mod.act(folder, doc, body.get("claim"), op, body.get("value" if op == "judge" else "note"), ai_on=passages_on)
        return trace_answer(done, passages_on)
    if op == "undo":
        with srv._lock:
            return trace_answer(trace_mod.undo(folder, doc), passages_on)
    if op == "open":
        srv.OPEN_FILE(trace_mod.pdf_path(folder, doc, body.get("ref"), found_in))
        return {"opened": True}
    if op == "pdf":
        try:
            data = base64.b64decode(str(body.get("data") or ""), validate=True)
        except (binascii.Error, ValueError):
            raise srv.WorkbookError(i18n.t("trace_server.api_trace.that_file_did_not_arrive_whole")) from None
        if len(data) > PDF_MAX:
            raise srv.WorkbookError(i18n.t("trace_server.api_trace.that_pdf_is_over_200_mb"))
        with srv._lock:
            return trace_mod.save_pdf(folder, doc, body.get("ref"), data)
    if op in ("plan", "passages"):
        if not passages_on:
            raise srv.WorkbookError(ai_mod.AI_OFF)
        if op == "plan":
            return trace_mod.plan(folder, doc, body.get("ids"), found_in)
        started = time.monotonic()
        # the call goes out of the server's lock, and the passages are written under the project's own
        result = trace_mod.find_passages(folder, doc, body.get("ref"), srv.ai_route(cfg, {"research_question": ""}),
                                         screenings=found_in)
        if "error" in result:
            return dict(result, status=502)
        return dict(trace_answer(result, passages_on), seconds=round(time.monotonic() - started, 1))
    raise srv.WorkbookError(i18n.t("trace_server.api_trace.the_op_is_list_add_read"))


def trace_answer(done: dict, ai_on: bool) -> dict:
    """An act's answer for the page, the passages left out while the app's AI switch is off."""
    return done if ai_on else dict(done, passages=None)


def trace_pdf(query: dict) -> tuple[int, bytes, str]:
    """A reference's PDF for Trace's pane, found as its table finds it, in the project's pdfs/ or a
    screening of a Sift project he keeps, and nothing from anywhere else."""
    try:
        folder = trace_folder(query.get("folder"))
        found = trace_mod.pdf_path(folder, query.get("doc") or None, query.get("ref"), trace_screenings())
    except srv.OutsideRoot as exc:
        return 403, str(exc).encode("utf-8"), "text/plain; charset=utf-8"
    except (srv.WorkbookError, OSError) as exc:
        return 404, str(exc).encode("utf-8"), "text/plain; charset=utf-8"
    return 200, found.read_bytes(), "application/pdf"


# ------------------------------------------------------------------ Search

def search_scope(body: dict, kinds: list[str]) -> dict:
    """Search's This Trace project: the project `folder`, its manuscripts' claims, references and notes."""
    if not body.get("folder"):
        raise srv.WorkbookError(trace_find.NO_TRACE)
    folder = trace_folder(body["folder"])
    whole, match_case = app_search.options(body)
    return trace_find.search_trace(body.get("q") or "", folder, str(body["folder"]), kinds=kinds, whole=whole,
                                   match_case=match_case)


def search_rows() -> list[dict]:
    """Everything's Trace projects, each there now, in the home screen's order."""
    return [{"id": e["folder"], "name": trace_name(srv.abs_path(e["folder"]), e), "folder": srv.abs_path(e["folder"]),
             "folder_id": e["folder"]} for e in traces_kept() if srv.abs_path(e["folder"]).is_dir()]


srv.register("trace", routes={"/api/trace": api_trace, "/api/trace-project": api_trace_project},
             post_only=("/api/trace", "/api/trace-project"), get_paths={TRACE_PDF_PATH: trace_pdf},
             home=("traces", trace_rows), search_scope=("trace", search_scope), search_rows=search_rows)
