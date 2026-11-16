"""Area 398: the exports no screen had before (exportnew, 16 November 2026, Adam: Export on every tab, Option C).

The Trajectories board, the statements screen's annotated transcript and a thematic analysis project's code list,
each as a print view, a PDF and a Word document, the code list as a CSV too, and Microsoft Word on an IPA project's
GETs, its LGETs and a participant's LPETs, which was a thematic analysis project's alone. Each from its route, the
command line and MCP (one API). Checked on the three demos as a fresh clone has them, every word made up: each file
is a valid PDF, Word document or CSV holding what its Include ticks say, never written over another, and a dry run
writes nothing."""
from __future__ import annotations

import csv
import io
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
    """The demo as a fresh clone has it: the files a run makes beside the participants left out, every pristine copy
    kept whole (as area 394 copies it)."""
    if "pristine" in Path(folder).parts:
        return []
    made = {"Working", "Source", "_Archive", "pictures", "idiograph-gets.json", "idiograph-codes.json",
            "idiograph-lgets.json", "idiograph-trajectories.json"}
    return [n for n in names if n in made or n.endswith(".m4a") or n.endswith((".pdf", ".docx", ".csv"))]


def word_text(path: Path) -> str:
    """A Word document's words, each paragraph a line, after checking it opens as Word's package."""
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        assert {"[Content_Types].xml", "word/document.xml", "word/styles.xml", "docProps/core.xml"} <= names
        body = z.read("word/document.xml").decode("utf-8")
    body = re.sub(r"</w:p>", "\n", body)
    return re.sub(r"<[^>]+>", "", body)


def squash(text: str) -> str:
    return re.sub(r"\s+", "", str(text)).casefold()


def files(at: Path) -> dict:
    return {p.relative_to(at).as_posix(): p.stat().st_mtime_ns for p in sorted(at.rglob("*"))
            if p.is_file() and not p.name.endswith(".lock")}


def test_document_exports(scratch: Path):
    print("\n398. The exports no screen had before: Trajectories, the annotated transcript and the code list, and Word "
          "on GETs, LPETs and LGETs (exportnew)")
    import cli as family_cli
    import documents
    import gets as gets_mod
    import i18n
    import idiograph_routes as routes
    import mcp_server
    import pdftext
    import server as srv
    import themes as themes_mod
    import trajectories as traj_mod
    import workbook as wb_mod
    from workbook import WorkbookError
    try:
        import typeset
    except ImportError:
        skip("398: the document exports", "family/typeset.py is not here")
        return
    if not typeset.available():
        skip("398: the document exports", "typst-py is not installed")
        return

    fresh = scratch / "docs-398-clone"
    shutil.rmtree(fresh, ignore_errors=True)
    shutil.copytree(support.source("demo"), fresh, ignore=as_cloned)
    kept = (srv.DEMO_DIR, srv.SHIPPED_DEMO, srv.CONFIG_PATH, srv.ROOT_OVERRIDE, srv.STATE_PATH, srv.STATE_MEMORY)
    cfg = scratch / "a398-config.json"

    def call(route: str, body: dict):
        try:
            with routes.route_scope(route, body):
                return srv.ROUTES[route](body)
        except (WorkbookError, srv.OutsideRoot) as exc:
            return str(exc)

    try:
        srv.DEMO_DIR = srv.SHIPPED_DEMO = fresh
        routes.fill_demo()
        ipa, ta, lipa = srv.DEMO_DIR, srv.demo_ta_dir(), srv.demo_lipa_dir()
        juno = ipa / "Juno" / "Juno - EN & ES.xlsx"
        read = wb_mod.read_case(juno)
        rows = [r for s in read["sheets"] for r in s["rows"]]
        interviewer = rows[0]["name"]
        cfg.write_text(json.dumps({"projects": [], "interviewer": interviewer, "corpus": "", "gravity_reference": "",
                                   "corpus_exclude": [], "your_name": "A. Researcher"}), encoding="utf-8")
        srv.CONFIG_PATH, srv.STATE_PATH, srv.STATE_MEMORY = cfg, scratch / "a398-state.json", {"recent": []}
        srv.ROOT_OVERRIDE = None

        # ── A. Trajectories, on the longitudinal demo
        board = traj_mod.board(traj_mod.load(lipa), routes.traj_people(lipa))
        placed = [c for c in board["participants"] if c["column"]]
        noted = next((c for c in placed if c["note"]), None)
        lpet = next(r for c in placed for r in c["rows"] if r.get("shown", True))
        state = next(cell["state"] for c in placed for r in c["rows"] for cell in r["cells"].values() if cell["state"])
        before = files(lipa)
        dry = call("/api/trajectories-export", {"root": "demo-lipa", "dry_run": True})
        ck("398: Trajectories' dry run names the file at the project's root and writes nothing",
           isinstance(dry, dict) and dry.get("dry_run") is True and dry["name"].endswith("Trajectories.pdf")
           and Path(dry["folder"]) == lipa and files(lipa) == before, dry)
        pdf = call("/api/trajectories-export", {"root": "demo-lipa", "notes": True})
        text = " ".join(pdftext.pages_text((lipa / pdf["name"]).read_bytes())) if isinstance(pdf, dict) else ""
        ck("398: Trajectories as a PDF: each trajectory, each participant placed, an LPET's title, a state and, with "
           "Each participant's note, his note",
           isinstance(pdf, dict) and (lipa / pdf["name"]).read_bytes()[:5] == b"%PDF-"
           and all(squash(col["title"]) in squash(text) for col in board["columns"])
           and all(squash(c["who"]) in squash(text) for c in placed) and squash(lpet["title"]) in squash(text)
           and squash(state[:40]) in squash(text) and (noted is None or squash(noted["note"][:40]) in squash(text))
           and pdf["counts"]["participants"] == len(placed), pdf)
        word = call("/api/trajectories-export", {"root": "demo-lipa", "format": "word"})
        words = word_text(lipa / word["name"]) if isinstance(word, dict) else ""
        ck("398: Trajectories as Word: the LPET table's columns, each timepoint, a state and the title, his notes left "
           "out unless ticked, landscape A4",
           isinstance(word, dict) and word["name"].endswith(".docx") and "T1, Before the season" in words
           and squash(state[:40]) in squash(words) and squash(lpet["title"]) in squash(words)
           and (noted is None or squash(noted["note"][:40]) not in squash(words))
           and 'w:orient="landscape"' in zipfile.ZipFile(lipa / word["name"]).read("word/document.xml").decode(), word)
        again = call("/api/trajectories-export", {"root": "demo-lipa", "format": "word"})
        ck("398: a second export never writes over the first, the date going in its name",
           isinstance(again, dict) and again["dated"] and again["name"] != word["name"]
           and (lipa / word["name"]).is_file() and (lipa / again["name"]).is_file(), again)
        code, page, _type = routes.traj_print_view({"root": "demo-lipa", "auto": "0"})
        page = page.decode("utf-8")
        ck("398: Trajectories' print view, the same document as a page the window prints",
           code == 200 and "<h1>Trajectories</h1>" in page and squash(lpet["title"]) in squash(html_text(page)), code)

        # ── B. the annotated transcript, on the IPA demo's Juno
        statement = next(p["es"] for r in rows for p in r["pairs"] if p["es"].strip())
        note_line = next(line for r in rows for line in r["en"].splitlines() if line.strip())
        turn = next(r for r in rows if r["name"] == interviewer)
        wb_mod.save_interviewer_note(juno, turn["sheet"], turn["row"], "Asked twice, a made-up note.", interviewer)
        body = {"workbook": str(juno), "format": "word", "interviewer_notes": True, "portrait": True}
        full = call("/api/transcript-export", body)
        words = word_text(juno.parent / full["name"]) if isinstance(full, dict) else ""
        person = json.loads((ipa / "idiograph-project.json").read_text(encoding="utf-8")).get("participants", {}).get("Juno", {})
        ck("398: the annotated transcript as Word beside the workbook: the turns, the exploratory notes, the statements "
           "with their quotes, the interviewer's note and the pen portrait",
           isinstance(full, dict) and Path(full["folder"]) == juno.parent and "Annotated transcript" in words
           and squash(rows[1]["text"][:40]) in squash(words) and squash(statement[:40]) in squash(words)
           and squash(note_line[:40]) in squash(words) and "Asked twice, a made-up note." in words
           and (not person.get("label") or person["label"] in words) and full["counts"]["interviewer_notes"] >= 1, full)
        bare = call("/api/transcript-export", {"workbook": str(juno), "format": "word", "notes": False,
                                                "statements": False})
        words = word_text(juno.parent / bare["name"]) if isinstance(bare, dict) else ""
        ck("398: with Exploratory notes, Experiential statements and Interviewer notes unticked the transcript alone",
           isinstance(bare, dict) and squash(rows[1]["text"][:40]) in squash(words)
           and squash(statement[:40]) not in squash(words) and squash(note_line[:40]) not in squash(words)
           and "Asked twice" not in words and "Exploratory notes" not in words, bare)
        pdf = call("/api/transcript-export", {"workbook": str(juno), "sheet": turn["sheet"]})
        text = " ".join(pdftext.pages_text((juno.parent / pdf["name"]).read_bytes())) if isinstance(pdf, dict) else ""
        ck("398: the annotated transcript as a PDF, one interview with sheet, the participant and the researcher on it",
           isinstance(pdf, dict) and squash("Juno") in squash(text) and squash(statement[:30]) in squash(text)
           and squash("A. Researcher") in squash(text), pdf)
        ck("398: an interview the workbook does not hold is refused, nothing written",
           "no interview named" in str(call("/api/transcript-export", {"workbook": str(juno), "sheet": "Nowhere"})))

        # ── C. the code list, on the thematic analysis demo
        view = routes.codes_document(ta, {})[1]
        coded = next(c for c in view["codes"] if c["extracts"])
        listed = (ta / "idiograph-codes.json").read_bytes() if (ta / "idiograph-codes.json").exists() else None
        out = {fmt: call("/api/codes-export", {"root": "demo-ta", "format": fmt}) for fmt in ("pdf", "word", "csv")}
        table = list(csv.reader(io.StringIO((ta / out["csv"]["name"]).read_text(encoding="utf-8-sig"))))
        extracts = sum(len(by["extracts"]) for c in view["codes"] for by in c["by"])
        empty = sum(1 for c in view["codes"] if not c["by"])
        words = word_text(ta / out["word"]["name"])
        text = " ".join(pdftext.pages_text((ta / out["pdf"]["name"]).read_bytes()))
        parts = {"csv": len(table) == 1 + extracts + empty and table[0][0] == "Code"
                        and any(r[0] == coded["name"] for r in table[1:]),
                 "word": all(squash(c["name"]) in squash(words) for c in view["codes"])
                         and squash(th_bare(coded["by"][0]["extracts"][0]["quote"])[:30]) in squash(words),
                 "pdf": squash(coded["name"]) in squash(text),
                 "root": all(Path(o["folder"]) == ta for o in out.values()),
                 "list": ((ta / "idiograph-codes.json").read_bytes() if listed is not None else None) == listed}
        ck("398: the code list as a CSV, a row for each extract and each code with none, as a PDF and as Word, each "
           "code by name with its extracts, at the project's root, the list itself unchanged", all(parts.values()),
           f"{parts} {len(table)} {extracts} {empty}")
        lean = call("/api/codes-export", {"root": "demo-ta", "format": "word", "extracts": False})
        words = word_text(ta / lean["name"])
        ck("398: with Extracts unticked each code with its counts alone",
           squash(coded["name"]) in squash(words) and squash(th_bare(coded["by"][0]["extracts"][0]["quote"])[:30]) not in squash(words))
        ck("398: an IPA project has no code list to export, nothing written",
           isinstance(call("/api/codes-export", {"root": "demo", "format": "csv"}), str) and not list(ipa.glob("*.csv")))
        code, page, _type = routes.transcript_print_view({"workbook": str(ta / "Juno" / "Juno - EN & ES.xlsx"), "auto": "0"})
        ck("398: a thematic analysis project's transcript prints in its own words, Coded transcript and Codes",
           code == 200 and "Coded transcript" in page.decode() and "Experiential statements" not in page.decode())

        # ── D. Microsoft Word on an IPA project's GETs, a participant's LPETs and the LGETs
        gid = routes.api_gets({"root": "demo"})["version"]["id"]
        gets_word = call("/api/gets-boards", {"root": "demo", "board": gid, "op": "word"})
        words = word_text(ipa / gets_word["name"]) if isinstance(gets_word, dict) else ""
        ck("398: an IPA project's GETs go to Word at the project's root under Table of Group Experiential Themes",
           isinstance(gets_word, dict) and Path(gets_word["path"]).parent == ipa
           and "Table of Group Experiential Themes" in words and "Theme table" not in gets_word["name"], gets_word)
        hollis = lipa / "Hollis" / "Hollis - EN & ES.xlsx"
        with routes.lpets_scope(hollis):
            lid = str(themes_mod.boards_of(gets_mod.load(hollis))[0]["id"])
        lpets = call("/api/gets-boards", {"workbook": str(hollis), "lpets": True, "board": lid, "op": "word"})
        words = word_text(Path(lpets["path"])) if isinstance(lpets, dict) else ""
        ck("398: a participant's LPETs go to Word beside their workbook, named by them, under the LPETs' table name",
           isinstance(lpets, dict) and Path(lpets["path"]).parent == hollis.parent and lpets["name"].startswith("Hollis")
           and "Table of Longitudinal Personal Experiential Themes" in words and "LPET table" in lpets["name"], lpets)
        with routes.board_scope(lipa):
            gid = str(themes_mod.boards_of(gets_mod.load(lipa))[0]["id"])
        lgets = call("/api/gets-boards", {"root": "demo-lipa", "board": gid, "op": "word"})
        words = word_text(Path(lgets["path"])) if isinstance(lgets, dict) else ""
        ck("398: the LGETs go to Word at the project's root under their own table's name",
           isinstance(lgets, dict) and "Table of Longitudinal Group Experiential Themes" in words, lgets)

        # ── E. one API: the command line and MCP write the same
        def said(*args):
            code, out_, err = family_cli.run(["--config", str(cfg), *args])
            return code, out_ if code == 0 else err

        before = files(lipa)
        code, line = said("--demo", "lipa", "trajectories", "export", "--word", "--dry-run")
        ck("398: trajectories export --dry-run names the Word document and writes nothing",
           code == 0 and "Trajectories" in line and ".docx" in line and files(lipa) == before, line)
        code, line = said("--demo", "ta", "codes", "export", "--csv")
        ck("398: codes export --csv writes the CSV at the project's root", code == 0 and ".csv" in line, line)
        code, line = said("--demo", "transcript", "export", "Juno", "--word", "--no-notes")
        ck("398: transcript export writes the Word document beside the workbook", code == 0 and ".docx" in line, line)
        names = {t["name"]: t for t in mcp_server.TOOLS}
        ck("398: MCP has trajectories_export, transcript_export and codes_export, each writing a file and taking dry_run",
           all(n in names and "dry_run" in names[n]["inputSchema"]["properties"]
               and not names[n]["annotations"]["readOnlyHint"] for n in ("trajectories_export", "transcript_export",
                                                                          "codes_export")))
        ck("398: every format each export writes, and no other", documents.FORMATS == {
            "trajectories": ("pdf", "word"), "transcript": ("pdf", "word"), "codes": ("pdf", "word", "csv")}
           and "pdf, word" in str(call("/api/trajectories-export", {"root": "demo-lipa", "format": "csv"})))
    finally:
        srv.DEMO_DIR, srv.SHIPPED_DEMO, srv.CONFIG_PATH, srv.ROOT_OVERRIDE, srv.STATE_PATH, srv.STATE_MEMORY = kept
        i18n.method_now()


def th_bare(text: str) -> str:
    import themes
    return themes.bare(text)


def html_text(page: str) -> str:
    return re.sub(r"<[^>]+>", " ", page)
