"""Area 271: three loose ends of 26 October 2026. Sift's reasons op takes the screening lock of each run
folder it writes reasons.csv into, so a run under another writer is refused BUSY with nothing written. A
chosen send that names a workbook after the participant's label sends the themes file and the GETs
file naming the workbook as it is sent. And the gate refuses a tree holding a 3-way apply's conflict
markers, naming the files, while a Markdown rule of equals signs alone passes.

The fixtures are invented: a review of reading by candlelight, a project on keeping a rooftop garden
with two made-up participants, one of whose folders carries a second part after the pseudonym, and a
made-up tree for the gate."""
from __future__ import annotations

import importlib.machinery
import json
import os
import shutil
import sys
import types
import zipfile
from pathlib import Path

from .support import check
from . import support

TESTS = Path(__file__).resolve().parents[1]
APP = TESTS.parent


def test_loose_ends(scratch: Path):
    print("\n271. Loose ends: the reasons op's run locks, a sent workbook's new name, the gate's conflict markers")
    reasons_and_the_run_lock(scratch)
    sent_workbook_named(scratch)
    gate_refuses_conflict_markers(scratch)


def reasons_and_the_run_lock(scratch: Path):
    import locks
    import sift
    import sift_search as ss
    from errors import WorkbookError

    base = scratch / "loose-271-sift"
    shutil.rmtree(base, ignore_errors=True)
    review = base / "Candle review"
    review.mkdir(parents=True)
    ss.new_plan(review, "Candle review", "How is reading by candlelight lived?")
    ss.save(review, {"databases": ["psycinfo"], "blocks": [{"name": "Candles", "terms": ["candle*"]}]})
    first = "code,meaning\nC1,Not about candles\n"
    (review / sift.REASONS_NAME).write_text(first, encoding="utf-8")
    runs = review / ss.RUNS_DIR
    fresh, begun_run = runs / "2026-10-20", runs / "2026-10-21"
    for folder, decision in ((fresh, ""), (begun_run, "include")):
        folder.mkdir(parents=True)
        (folder / sift.CSV_NAME).write_text("rec_id,title,abstract,decision,reason\n"
                                            f"R001,Wax and the page,Candles.,{decision},\n", encoding="utf-8")
        (folder / sift.REASONS_NAME).write_text(first, encoding="utf-8")
    edit = [{"code": "C1", "meaning": "Not about candles"}, {"code": "C2", "meaning": "No reading"}]
    said = ""
    try:
        with locks.held(sift.lock_path(fresh), wait=1):
            ss.save_reasons(review, edit, wait=0.2)
    except WorkbookError as exc:
        said = str(exc)
    check("271: the reasons op on a review whose run not begun is under another write is refused BUSY, "
          "the review's reasons.csv and the run's as they were",
          said == locks.BUSY and (review / sift.REASONS_NAME).read_text(encoding="utf-8") == first
          and (fresh / sift.REASONS_NAME).read_text(encoding="utf-8") == first, said)
    said = ""
    try:
        with locks.held(sift.lock_path(begun_run), wait=1):
            ss.save_reasons(review, edit, wait=0.2)
    except WorkbookError as exc:
        said = str(exc)
    two = "code,meaning\nC1,Not about candles\nC2,No reading\n"
    check("271: a begun run under another write takes nothing and holds nothing up, the run not begun taking the "
          "new reasons, the begun run keeping its copy",
          not said and (review / sift.REASONS_NAME).read_text(encoding="utf-8") == two
          and (fresh / sift.REASONS_NAME).read_text(encoding="utf-8") == two
          and (begun_run / sift.REASONS_NAME).read_text(encoding="utf-8") == first, said)


def sent_workbook_named(scratch: Path):
    import cli
    import project_pack
    import rounds as rounds_mod
    import server as server_mod
    from .a258_send_chosen import make_workbook

    base = scratch / "loose-271-send"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Rooftop garden"
    root.mkdir(parents=True)
    second = "Hollis"
    a_folder = "P1 - Wren" + "-" + second
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Rooftop garden", "research_question": "How do people live keeping a garden on a roof?",
        "names": {"P1 - Wren": "Wren"}, "agents": {"allowed": True, "at": "2026-10-26T10:00:00+00:00"}}),
        encoding="utf-8")
    a_book = make_workbook(root, a_folder, "Wren")
    b_book = make_workbook(root, "P2 - Ashby", "Ashby")
    for book in (a_book, b_book):
        rounds_mod.save_progress(book, {"version": 1, "rows": {"Initial:3": "has-content", "Initial:5": "has-content"}})
    config_file = base / "config-271.json"
    config_file.write_text(json.dumps({"projects": [], "interviewer": "Interviewer", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    out_dir, into = base / "out", base / "into"
    out_dir.mkdir()
    into.mkdir()

    def run_json(*args):
        code, out, err = cli.run(["--config", str(config_file), "--json", *args])
        got = support.plain(json.loads(out)) if out.strip() else {}
        return code, (got if code == 0 else {}), err + (got.get("error", "") if code != 0 else "")

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        plan = base / "plan.json"
        plan.write_text(json.dumps({"pets": [{"title": "Soil carried up", "members": ["S1"]}],
                                    "not_placed": {"S2": ""}}), encoding="utf-8")
        for who in ("Wren", "Ashby"):
            code, _, err = run_json("--root", str(root), "board", "new", who, "--from", str(plan), "--note",
                                    "A first board", "--tool", "Claude Code")
            check(f"271: a board is made on {who}'s canvas for the fixture", code == 0, err)
        (root / "idiograph-gets.json").write_text(json.dumps({"schema": 1, "boards": [], "cases": {
            "P1 - Wren": {"workbook": a_book.name, "board": "v1"},
            "P2 - Ashby": {"workbook": b_book.name, "board": "v1"}}}), encoding="utf-8")
        a_themes = a_book.parent / "Working" / (a_book.stem + ".themes.json")
        before_themes = a_themes.read_bytes()
        before_gets = (root / "idiograph-gets.json").read_bytes()

        for name, extra in (("chosen.idiograph", ()), ("current.idiograph", ("--boards", "current"))):
            sent = out_dir / name
            code, done, err = run_json("--root", str(root), "project", "send", "--to", str(sent),
                                       "--participant", "Wren", "--participant", "Ashby", *extra)
            held, themes, gets = [], {}, {}
            if code == 0:
                with zipfile.ZipFile(sent) as zf:
                    held = [n[len(project_pack.TOP):] for n in zf.namelist() if n.startswith(project_pack.TOP)]
                    themes = json.loads(zf.read(project_pack.TOP + "P1 - Wren/Working/P1 - Wren - EN & ES.themes.json"))
                    gets = json.loads(zf.read(project_pack.TOP + "idiograph-gets.json"))
            check(f"271: {name}: the themes file's and the GETs file's workbook name Wren's workbook as it is sent, "
                  "Ashby's as it was",
                  code == 0 and "P1 - Wren/P1 - Wren - EN & ES.xlsx" in held
                  and themes.get("workbook") == "P1 - Wren - EN & ES.xlsx"
                  and gets["cases"]["P1 - Wren"]["workbook"] == "P1 - Wren - EN & ES.xlsx"
                  and gets["cases"]["P2 - Ashby"]["workbook"] == "P2 - Ashby - EN & ES.xlsx"
                  and not any(second in n for n in held), err or json.dumps(themes)[:200])
        check("271: the project's own themes file and GETs file are byte for byte as they were",
              a_themes.read_bytes() == before_themes and (root / "idiograph-gets.json").read_bytes() == before_gets)

        code, _, err = run_json("project", "open-copy", str(out_dir / "chosen.idiograph"), "--into", str(into))
        copy = into / "Rooftop garden"
        code2, cases, err2 = run_json("--root", str(copy), "cases")
        wren = next((c for c in cases.get("cases", []) if c["case"] == "P1 - Wren"), {})
        check("271: the copy opens with Wren's board, its themes file naming the workbook beside it",
              code == 0 and code2 == 0 and len(wren.get("boards") or []) == 1
              and json.loads((copy / "P1 - Wren" / "Working" / "P1 - Wren - EN & ES.themes.json")
                             .read_text(encoding="utf-8"))["workbook"] == "P1 - Wren - EN & ES.xlsx",
              err + err2 + json.dumps(wren)[:300])
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept


def load_gate() -> types.ModuleType:
    """The gate's script as a module, its re-run under the venv's python held off."""
    flag = "IDIOGRAPH_VERIFY_REEXEC"
    was = os.environ.get(flag)
    os.environ[flag] = "1"
    try:
        loader = importlib.machinery.SourceFileLoader("verify_gate_271", str(APP / "verify"))
        module = types.ModuleType(loader.name)
        module.__file__ = loader.path
        # its dataclass reads the module from sys.modules while it is made
        sys.modules[loader.name] = module
        loader.exec_module(module)
        return module
    finally:
        if was is None:
            os.environ.pop(flag, None)
        else:
            os.environ[flag] = was


def gate_refuses_conflict_markers(scratch: Path):
    gate = load_gate()
    tree = scratch / "loose-271-gate"
    shutil.rmtree(tree, ignore_errors=True)
    (tree / "static").mkdir(parents=True)
    opener, divider, closer = "<" * 7, "=" * 7, ">" * 7
    files = {
        "README.md": f"# Moss\n\n{opener} ours\nMoss grows on the north side.\n{divider}\nMoss grows in shade.\n"
                     f"{closer} theirs\n",
        "static/garden.js": f"function water() {{\n{opener} ours\n  return 1;\n{divider}\n  return 2;\n{closer} theirs\n}}\n",
        "notes.md": f"Beds\n{divider}\n\nA rule of equals signs under a heading, nothing more.\n",
        "half.md": f"{opener} only an opener, which a 3-way apply never leaves alone\n",
        "photo.png": f"{opener} x\n{divider}\n{closer} y\n",
    }
    for rel, text in files.items():
        (tree / rel).write_text(text, encoding="utf-8")
    view = gate.View(root=tree, tracked=sorted(files), staged={}, changed=[])
    ok, said, reason = gate.check_conflict_markers(view)
    check("271: the gate refuses a tree holding conflict markers, RED with reason conflict-markers, naming each "
          "file and its lines, a lone rule of equals signs, a lone opener and a picture passed over",
          ok is False and reason == "conflict-markers" and "README.md: conflict markers at line(s) 3, 5, 7" in said
          and "static/garden.js: conflict markers at line(s) 2, 4, 6" in said
          and "notes.md" not in said and "half.md" not in said and "photo.png" not in said, said)
    clean = {rel: text for rel, text in files.items() if rel not in ("README.md", "static/garden.js")}
    view = gate.View(root=tree, tracked=sorted(clean), staged={}, changed=[])
    ok, said, reason = gate.check_conflict_markers(view)
    check("271: the same tree without them passes, and the fast gate runs the check",
          ok is True and reason is None
          and ("conflict markers", gate.check_conflict_markers) in gate.FAST_CHECKS, said)
