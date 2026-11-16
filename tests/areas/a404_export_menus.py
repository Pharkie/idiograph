"""Area 404: the Export menus wired to their routes (exportwire, 16 November 2026, Adam: Export on every tab).

The page's menus on Trajectories, the statements screen and a thematic analysis project's Code list send each item's
format and each Include tick by the names the menu gives them, to the routes their scripts name: each is checked here
by calling the route with those very names and finding the document holding what the ticks say, Unplaced among them.
A participant's LPETs as a PDF go beside their workbook, named by them, so two participants' never take one name, and
a demo named by its folder, as the page sends a project's root back, is that demo. On the three demos as a fresh
clone has them, every word made up."""
from __future__ import annotations

import json
import re
import shutil
import zipfile
from pathlib import Path

from . import support
from .support import check, skip


def ck(name: str, condition, detail="") -> None:
    check(name, bool(condition), "" if condition else str(detail)[:600])


def as_cloned(folder: str, names: list[str]) -> list[str]:
    if "pristine" in Path(folder).parts:
        return []
    made = {"Working", "Source", "_Archive", "pictures", "idiograph-gets.json", "idiograph-codes.json",
            "idiograph-lgets.json", "idiograph-trajectories.json"}
    return [n for n in names if n in made or n.endswith(".m4a") or n.endswith((".pdf", ".docx", ".csv"))]


def word_text(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        body = z.read("word/document.xml").decode("utf-8")
    return re.sub(r"<[^>]+>", "", re.sub(r"</w:p>", "\n", body))


def squash(text: str) -> str:
    return re.sub(r"\s+", "", str(text)).casefold()


def menu(page: str, menu_id: str) -> tuple[list[str], list[str]]:
    """A menu's items (`data-xop`) and its Include ticks (`data-xinc`) as the page has them."""
    at = page.index(f'id="{menu_id}"')
    body = page[at:page.index("</div>\n", page.index("th-xhead", at))]
    return re.findall(r'data-xop="([a-z]+)"', body), re.findall(r'data-xinc="([a-z_]+)"', body)


def const(script: str, name: str) -> str:
    found = re.search(rf"const {name} = '([^']+)';", script)
    return found.group(1) if found else ""


def test_export_menus(scratch: Path):
    print("\n404. The Export menus wired to their routes: Trajectories, the statements screen, the Code list, and the "
          "LPETs' PDF beside the participant (exportwire)")
    import gets as gets_mod
    import idiograph_routes as routes
    import server as srv
    import themes as themes_mod
    import trajectories as traj_mod
    import workbook as wb_mod
    from workbook import WorkbookError
    try:
        import typeset
    except ImportError:
        skip("404: the export menus", "family/typeset.py is not here")
        return
    if not typeset.available():
        skip("404: the export menus", "typst-py is not installed")
        return

    static = Path(support.source("apps")) / "idiograph" / "static"
    page = (static / "idiograph.html").read_text(encoding="utf-8")
    scripts = {n: (static / f"{n}.js").read_text(encoding="utf-8") for n in ("trajectories", "distil", "codes")}
    wired = {"trajectories": ("tj-xmenu", const(scripts["trajectories"], "TJ_EXPORT"),
                              const(scripts["trajectories"], "TJ_PRINT")),
             "transcript": ("es-xmenu", const(scripts["distil"], "ES_EXPORT"), const(scripts["distil"], "ES_PRINT")),
             "codes": ("cd-xmenu", const(scripts["codes"], "CD_EXPORT"), const(scripts["codes"], "CD_PRINT"))}
    gets_paths = {routes.TRAJ_PRINT_PATH: routes.traj_print_view, routes.TRANSCRIPT_PRINT_PATH: routes.transcript_print_view,
                  routes.CODES_PRINT_PATH: routes.codes_print_view}
    ck("404: each menu's script names a route the server answers and a print view it draws",
       all(route in srv.ROUTES and shown in gets_paths for _m, route, shown in wired.values()),
       {k: v[1:] for k, v in wired.items()})
    items = {k: menu(page, v[0]) for k, v in wired.items()}
    ck("404: each menu has Print, Save as PDF and Microsoft Word, and the Code list CSV too",
       all({"print", "pdf", "word"} <= set(ops) for ops, _ticks in items.values()) and "csv" in items["codes"][0], items)

    fresh = scratch / "menus-404-clone"
    shutil.rmtree(fresh, ignore_errors=True)
    shutil.copytree(support.source("demo"), fresh, ignore=as_cloned)
    kept = (srv.DEMO_DIR, srv.SHIPPED_DEMO, srv.CONFIG_PATH, srv.ROOT_OVERRIDE, srv.STATE_PATH, srv.STATE_MEMORY)
    cfg = scratch / "a404-config.json"

    def call(route: str, body: dict):
        try:
            with routes.route_scope(route, body):
                return srv.ROUTES[route](body)
        except (WorkbookError, srv.OutsideRoot) as exc:
            return str(exc)

    def view(path: str, query: dict) -> str:
        with routes.route_scope(path, query):
            code, body, _type = gets_paths[path](dict(query, auto="0"))
        return body.decode("utf-8") if code == 200 else ""

    try:
        srv.DEMO_DIR = srv.SHIPPED_DEMO = fresh
        routes.fill_demo()
        ipa, ta, lipa = srv.DEMO_DIR, srv.demo_ta_dir(), srv.demo_lipa_dir()
        juno = ipa / "Juno" / "Juno - EN & ES.xlsx"
        rows = [r for s in wb_mod.read_case(juno)["sheets"] for r in s["rows"]]
        cfg.write_text(json.dumps({"projects": [], "interviewer": rows[0]["name"], "corpus": "", "corpus_exclude": [],
                                   "gravity_reference": "", "your_name": "A. Researcher"}), encoding="utf-8")
        srv.CONFIG_PATH, srv.STATE_PATH, srv.STATE_MEMORY = cfg, scratch / "a404-state.json", {"recent": []}
        srv.ROOT_OVERRIDE = None

        # ── A. Trajectories: a trajectory taken away leaves its participants Unplaced, which the tick puts in
        people = sorted(p.parent for p in lipa.glob("*/*.xlsx") if "pristine" not in p.parts)
        book = next(p for p in lipa.glob("*/*.xlsx") if "pristine" not in p.parts)
        board = traj_mod.board(traj_mod.load(lipa), routes.traj_people(lipa))
        column = board["columns"][0]
        out = [c["who"] for c in board["participants"] if c["column"] == column["id"]]
        gone = call("/api/trajectories-ops", {"workbook": str(book), "ops": [{"op": "remove", "column": column["id"]}]})
        ops, ticks = items["trajectories"]
        _m, route, shown = wired["trajectories"]
        made = {op: call(route, dict({t: True for t in ticks}, workbook=str(book), format=op)) for op in ops if op != "print"}
        words = word_text(Path(made["word"]["path"])) if isinstance(made.get("word"), dict) else ""
        ck("404: Trajectories' menu, its ticks by their names: the PDF and Word made at the project's root, the "
           "participants taken off a trajectory in them under Unplaced",
           isinstance(gone, dict) and out and all(isinstance(m, dict) and Path(m["folder"]) == lipa
                                                  and m["counts"]["unplaced"] == len(out) for m in made.values())
           and all(squash(w) in squash(words) for w in out), made)
        on = view(shown, dict({t: "1" for t in ticks}, workbook=str(book)))
        off = view(shown, dict({t: "0" for t in ticks}, workbook=str(book)))
        ck("404: Trajectories' Print with Unplaced ticked shows them, unticked leaves them out",
           on and off and all(squash(w) in squash(on) and squash(w) not in squash(off) for w in out), (len(on), len(off)))

        # ── B. the statements screen: each Include tick by its name, on and off
        ops, ticks = items["transcript"]
        _m, route, shown = wired["transcript"]
        statement = next(p["es"] for r in rows for p in r.get("pairs") or [] if (p.get("es") or "").strip())
        note = next(r["en"] for r in rows if (r.get("en") or "").strip())
        both = {}
        for on_ in (True, False):
            both[on_] = call(route, dict({t: on_ for t in ticks}, workbook=str(juno), format="word"))
        text_on = word_text(Path(both[True]["path"])) if isinstance(both[True], dict) else ""
        text_off = word_text(Path(both[False]["path"])) if isinstance(both[False], dict) else ""
        ck("404: the statements screen's menu, its ticks by their names: Word beside the workbook with the "
           "statements and notes ticked, and without them unticked",
           {"notes", "statements"} <= set(ticks) and isinstance(both[True], dict)
           and Path(both[True]["folder"]) == juno.parent
           and squash(statement[:40]) in squash(text_on) and squash(statement[:40]) not in squash(text_off)
           and squash(note.splitlines()[0][:40]) in squash(text_on)
           and squash(note.splitlines()[0][:40]) not in squash(text_off), (both, statement[:20]))
        pdf = call(route, dict({t: True for t in ticks}, workbook=str(juno), format="pdf"))
        ck("404: the statements screen's Save as PDF writes a PDF beside the workbook",
           isinstance(pdf, dict) and Path(pdf["path"]).read_bytes()[:5] == b"%PDF-", pdf)
        ck("404: the statements screen's Print draws the view with its ticks",
           squash(statement[:40]) in squash(view(shown, dict({t: "1" for t in ticks}, workbook=str(juno)))))

        # ── C. the Code list: PDF, Word and CSV, Extracts by its name
        ops, ticks = items["codes"]
        _m, route, shown = wired["codes"]
        ta_book = next(p for p in ta.glob("*/*.xlsx") if "pristine" not in p.parts)
        made = {op: call(route, dict({t: True for t in ticks}, workbook=str(ta_book), format=op)) for op in ops if op != "print"}
        csv_text = Path(made["csv"]["path"]).read_text(encoding="utf-8-sig") if isinstance(made.get("csv"), dict) else ""
        ck("404: the Code list's menu: a PDF, a Word document and a CSV of its extracts at the project's root",
           set(made) == {"pdf", "word", "csv"} and all(isinstance(m, dict) and Path(m["folder"]) == ta for m in made.values())
           and len(csv_text.splitlines()) > 2, made)
        with_x = view(shown, dict({t: "1" for t in ticks}, workbook=str(ta_book)))
        without = view(shown, dict({t: "0" for t in ticks}, workbook=str(ta_book)))
        ck("404: the Code list's Print with Extracts unticked is the shorter list of the codes alone",
           "extracts" in ticks and with_x and without and len(without) < len(with_x), (len(with_x), len(without)))

        # ── D. a participant's LPETs as a PDF beside their workbook, named by them, as their Word document is
        names = []
        for folder in people[:2]:
            wb = next(folder.glob("*.xlsx"))
            with routes.lpets_scope(wb):
                gid = str(themes_mod.boards_of(gets_mod.load(lipa))[0]["id"])
            got = call("/api/gets-boards", {"workbook": str(wb), "lpets": "1", "root": "demo-lipa", "board": gid,
                                            "op": "pdf"})
            names.append(got)
        ck("404: two participants' LPETs PDFs each go beside their own workbook, named by them, never one name",
           len(names) == 2 and all(isinstance(n, dict) and Path(n["path"]).parent == f
                                   and Path(n["path"]).is_file() and n["name"].startswith(f.name)
                                   for n, f in zip(names, people[:2]))
           and names[0]["name"] != names[1]["name"], names)

        # ── E. a demo named by its folder, as the page sends a project's root back: the LGETs and TA Themes
        for folder, name in ((lipa, "the LGETs"), (ta, "a thematic analysis demo's Themes")):
            rel = srv.rel_path(folder)
            try:
                found = srv.project_named(rel)
            except srv.OutsideRoot:
                found = None
            ck(f"404: {name}, its project named by its folder, is that demo", found == folder, rel)
    finally:
        srv.DEMO_DIR, srv.SHIPPED_DEMO, srv.CONFIG_PATH, srv.ROOT_OVERRIDE, srv.STATE_PATH, srv.STATE_MEMORY = kept
