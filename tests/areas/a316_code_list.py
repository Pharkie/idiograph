"""Area 316: a thematic analysis project's code list (codes, 2 November 2026, Adam's ruling of 28 October, choice 1
(a), and his choice of the drawings on 2 November: coding A, the code list as its own tab, the board's code cards).

A code is a label many extracts share, each extract still one quote: in the workbook a code on an extract is a
statement of the code's name with the extract as its quote, two codes on one extract two statements with the same
quote, and the list is `idiograph-codes.json` at the project's root. What is checked, on an invented copy of the demo
made a thematic analysis project, its statements written as a few shared codes (a house shared with a dog): a
project made before the list has it made on its first read, each board keeping a revision first and a code whose
cards stood apart gathered where most of them stood; what a code put on an extract, a second code on it and one
taken off write to the workbook and the list; a rename and a merge across two participants and a board, one
revision of each file kept, refused whole when one workbook is open in Excel, and each undone and done again; a
delete only of a code with no extracts; a name typed on the Coding screen joining the list; the board's save from
the page, which sends a code's lead alone, laying its rows back beside it; the command line's and MCP's ops, a dry
run writing nothing and a rename waiting for his yes; and an IPA project refusing every op, its files untouched."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import openpyxl

from .support import DEMO_SHIPPED, check
from . import support

CODES = ["A gate left on the latch", "Being pulled along", "Dinner set by the bowl", "The second stair",
         "Rain and the long way round", "A chair given up"]
NAMES = ("Juno", "Rowan", "Mabel")


def sha(path: Path) -> str:
    return hashlib.sha1(Path(path).read_bytes()).hexdigest()


def make_project(root: Path, method: str = "ta") -> None:
    """A copy of the demo's three participants, each passage with a quote coded with one or two of CODES on its
    first quote, in a project of `method`, with no PETs boards."""
    import workbook as wb
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    for ci, name in enumerate(NAMES):
        case = root / name
        (case / "Working").mkdir(parents=True)
        book = case / f"{name} - EN & ES.xlsx"
        shutil.copy2(DEMO_SHIPPED / f"{name} - EN & ES.xlsx", book)
        side = DEMO_SHIPPED / "Working" / f"{name} - EN & ES.progress.json"
        if side.exists():
            shutil.copy2(side, case / "Working" / side.name)
        w = openpyxl.load_workbook(book, rich_text=True)
        n = 0
        for ws in w.worksheets:
            cols = wb.detect_columns(ws)
            if "es" not in cols or "kq" not in cols:
                continue
            for r in range(2, ws.max_row + 1):
                pairs = wb.pairs_of(ws.cell(r, cols["es"]).value, ws.cell(r, cols["kq"]).value)
                quote = next((p["kq"] for p in pairs if p["kq"]), "")
                if not pairs:
                    continue
                if not quote or n >= 8:
                    ws.cell(r, cols["es"]).value = None
                    ws.cell(r, cols["kq"]).value = None
                    continue
                codes = [CODES[(n + ci) % 4]] + ([CODES[4]] if n in (1, 5) else [])
                es, kq = wb.pairs_to_cells([{"es": c, "kq": quote} for c in codes])
                ws.cell(r, cols["es"]).value = es
                ws.cell(r, cols["kq"]).value = kq
                n += 1
        wb._atomic_save(w, book)
        w.close()
    (root / "idiograph-project.json").write_text(json.dumps({
        "name": "A house shared with a dog", "method": method,
        "agents": {"allowed": True, "at": "2026-11-02T09:00:00+00:00"}}), encoding="utf-8")


def rows_of(book: Path) -> dict:
    """Each passage's pairs, by sheet and row, as the workbook holds them."""
    import workbook as wb
    out = {}
    w = openpyxl.load_workbook(book, read_only=True)
    try:
        for ws in w.worksheets:
            cols = wb.detect_columns(ws)
            if "es" not in cols:
                continue
            for r, values in enumerate(ws.iter_rows(min_row=2, max_col=max(cols.values()), values_only=True), start=2):
                pairs = wb.pairs_of(values[cols["es"] - 1], values[cols["kq"] - 1] if "kq" in cols else None)
                if pairs:
                    out[(ws.title, r)] = pairs
    finally:
        w.close()
    return out


def test_code_list(scratch: Path):
    print("\n316. A thematic analysis project's code list: made on an old project's first read, a code on an "
          "extract and two on one, rename and merge across participants and a board, refused whole when a workbook "
          "is open, undo of each, delete, the board's save, the command line and MCP, an IPA project refusing (2 "
          "November)")
    import cli
    import codes
    import gets
    import holds
    import i18n
    import idiograph_routes as routes
    import mcp_server
    import server as server_mod
    import themes
    from workbook import WorkbookError

    base = scratch / "codes-316"
    root, ipa = base / "Dogs", base / "Dogs IPA"
    make_project(root, "ta")
    make_project(ipa, "ipa")
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}, {"root": str(ipa)}], "interviewer": "Adam",
                                       "corpus": "", "gravity_reference": "", "corpus_exclude": [],
                                       "skip_permissions": False}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, holds.RUN_AT_ONCE)
    book = {name: root / name / f"{name} - EN & ES.xlsx" for name in NAMES}

    def call(route: str, body: dict):
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = config_file, None, {"recent": []}
        try:
            with server_mod.scoped(route, body):
                return server_mod.ROUTES[route](body)
        finally:
            server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept[:3]

    def refused(route: str, body: dict) -> str:
        try:
            got = call(route, body)
        except WorkbookError as exc:
            return str(exc)
        return got.get("error", "") if isinstance(got, dict) else ""

    def run(*args):
        return cli.run(["--config", str(config_file), "--root", str(root), *args])

    def answer(*args):
        code, out, err = run("--json", *args)
        got = support.plain(json.loads(out)) if out.strip() else {}
        return code, got, err + (got.get("error", "") if code else "")

    def listed() -> dict:
        return call("/api/codes", {"root": str(root)})

    def code_named(view: dict, name: str) -> dict | None:
        return next((c for c in view["codes"] if c["name"] == name), None)

    def board() -> dict:
        return themes.boards_of(gets.load(root))[0]

    try:
        # 0. a Themes board made before the list, in IPA's run (no folding): the code "A gate left on the latch"
        # with one card in a theme and the rest loose, two to one, so it gathers where most of them stood
        books = routes.gets_books(root)
        data, _cases, _disk, _taken = gets.assemble(root, books, "2026-11-01T09:00:00+00:00")
        gets.write(root, gets._file(data, "2026-11-01T09:00:00+00:00"))
        data = gets.load(root)
        by_code: dict = {}
        for case, rec in data["cases"].items():
            for k, line in rec["lines"].items():
                by_code.setdefault(codes.norm(line["text"]), []).append(f"{case}/es/{k}")
        gate = by_code[codes.norm(CODES[0])]
        cards = {k: {"x": 100 + i * 220, "y": 600, "text": ""} for i, k in enumerate(gate)}
        cards.update({k: {"x": 100 + i * 220, "y": 900, "text": ""} for i, k in enumerate(by_code[codes.norm(CODES[1])])})
        version = {"id": "b1", "name": "Board 1", "cards": cards, "discarded": [],
                   "groups": [{"id": "G1", "label": "Doors and edges", "x": 0, "y": 0, "members": gate[:1]},
                              {"id": "G2", "label": "Walks", "x": 0, "y": 400,
                               "members": by_code[codes.norm(CODES[1])]}]}
        gets.save(root, books, version)
        gets_before = sha(gets.gets_path(root))
        before = {name: sha(path) for name, path in book.items()}

        # 1. the first read makes the list from the rows, every board kept first and its codes gathered
        view = listed()
        made = codes.load(root)
        names = sorted(c["name"] for c in view["codes"])
        check("316: an old project's first read makes the list, one code a name, its counts by extract and participant",
              names == sorted(CODES[:5]) and code_named(view, CODES[4])["extracts"] == 6
              and code_named(view, CODES[4])["participants"] == 3 and all(c["description"] == "" for c in made["codes"]),
              json.dumps([(c["name"], c["extracts"], c["participants"]) for c in view["codes"]]))
        b = board()
        parents = themes.parents_of(b["groups"])
        where = {parents.get(k) for k in gate}
        rev = themes.history_of(b)[-1]
        check("316: the board kept a revision first, naming the codes made and the code gathered, and the gathered "
              "code's cards all stand where most of them stood, out of the theme",
              rev.get("kind") == "codes_listed_moved" and CODES[0] in rev["name"] and "5 codes" in rev["name"]
              and where == {None} and len({(b["cards"][k]["x"], b["cards"][k]["y"]) for k in gate}) == 1,
              json.dumps([rev.get("name"), sorted(map(str, where))]))
        check("316: the History line says how many codes the list made, the GETs file copied first, no workbook "
              "written", made["history"][0]["changes"][0].endswith("5 codes.")
              and any(p.name.startswith("idiograph-gets (pre-codes") for p in (root / "_Archive").iterdir())
              and before == {name: sha(path) for name, path in book.items()}, json.dumps(made["history"]))
        list_was, gets_was = sha(codes.path_of(root)), sha(gets.gets_path(root))
        check("316: a second read writes nothing", listed()["v"] == view["v"] and list_was == sha(codes.path_of(root))
              and gets_was == sha(gets.gets_path(root)) and gets_before != gets_was)

        # 2. a code on an extract, a second code on it, one taken off: the passage's pairs as the workbook holds them
        x = code_named(view, CODES[2])["by"][0]
        first = x["extracts"][0]
        case = x["case"]
        got = call("/api/codes-extract", {"root": str(root), "op": "add", "case": case, "sheet": first["sheet"],
                                           "row": first["row"], "quote": first["quote"], "code": "Smell of the lead",
                                           "note": "Code this one too"})
        pairs = rows_of(book[case])[(first["sheet"], first["row"])]
        same = [p for p in pairs if " ".join(p["kq"].split()) == first["quote"]]
        check("316: a second code on an extract is a second statement with the same quote, and a new name joins the list",
              [p["es"] for p in same] == [CODES[2], "Smell of the lead"]
              and code_named(listed(), "Smell of the lead")["extracts"] == 1, json.dumps(pairs))
        refusal = refused("/api/codes-extract", {"root": str(root), "op": "add", "case": case, "sheet": first["sheet"],
                                                 "row": first["row"], "quote": first["quote"], "code": "smell OF the lead "})
        check("316: a name the list has, typed in another case with outer spaces, is that code, and twice is refused",
              "already" in refusal, refusal)
        call("/api/codes-extract", {"root": str(root), "op": "remove", "case": case, "sheet": first["sheet"],
                                    "row": first["row"], "quote": first["quote"], "code": CODES[2]})
        call("/api/codes-extract", {"root": str(root), "op": "remove", "case": case, "sheet": first["sheet"],
                                    "row": first["row"], "quote": first["quote"], "code": "Smell of the lead"})
        pairs = rows_of(book[case])[(first["sheet"], first["row"])]
        check("316: a code taken off its extract's last keeps the extract, with no code", pairs == [{"es": "", "kq": pairs[0]["kq"]}]
              and " ".join(pairs[0]["kq"].split()) == first["quote"], json.dumps(pairs))
        call("/api/codes-extract", {"root": str(root), "op": "add", "case": case, "sheet": first["sheet"],
                                    "row": first["row"], "quote": first["quote"], "code": CODES[2]})
        check("316: a code put back on an extract with none fills it", rows_of(book[case])[(first["sheet"], first["row"])][0]["es"] == CODES[2])

        # 3. a rename across every participant and the board, a revision of each file kept, one step of undo
        view = listed()
        olds = {name: sha(path) for name, path in book.items()}
        got = call("/api/codes-ops", {"root": str(root), "v": view["v"], "note": "Call it the bowl",
                                      "ops": [{"op": "rename", "code": CODES[4], "name": "The bowl at six"}]})
        texts = [p["es"] for name in NAMES for pairs in rows_of(book[name]).values() for p in pairs]
        lines = [line["text"] for rec in gets.load(root)["cases"].values() for line in rec["lines"].values()]
        b = board()
        check("316: a rename writes every workbook that holds the code and the GETs file's copies, the old name nowhere",
              texts.count("The bowl at six") == 6 and CODES[4] not in texts and lines.count("The bowl at six") == 6
              and CODES[4] not in lines and set(got["files"]) >= {f"{n}/{n} - EN & ES.xlsx" for n in NAMES}
              and themes.history_of(b)[-1].get("kind") == "codes_changed", json.dumps(got.get("files")))
        archived = [p.name for n in NAMES for p in (root / n / "_Archive").iterdir()]
        check("316: a copy of each workbook was kept before the rename", sum("pre-codes" in a for a in archived) == 3, str(archived))
        stale = refused("/api/codes-ops", {"root": str(root), "v": view["v"], "ops": [{"op": "describe", "code": CODES[0], "description": "x"}]})
        check("316: a change from a page that read the list before is refused, nothing written", stale == i18n.t("codes.stale"), stale)
        call("/api/codes-undo", {"root": str(root)})
        check("316: undo of a rename puts every workbook back as it was", olds == {n: sha(p) for n, p in book.items()}
              and code_named(listed(), CODES[4]) is not None)
        call("/api/codes-undo", {"root": str(root), "redo": True})
        check("316: and redo makes it again", code_named(listed(), "The bowl at six")["extracts"] == 6)

        # 4. refused whole when one workbook is open in Excel: nothing written, the list as it was
        lock = book["Mabel"].with_name("~$" + book["Mabel"].name)
        lock.write_text("", encoding="utf-8")
        olds = {name: sha(path) for name, path in book.items()}
        list_was = sha(codes.path_of(root))
        refusal = refused("/api/codes-ops", {"root": str(root), "ops": [{"op": "rename", "code": "The bowl at six", "name": "Six o'clock"}]})
        lock.unlink()
        check("316: a rename with one workbook open in Excel is refused whole, no workbook and not the list written",
              "Excel" in refusal and olds == {n: sha(p) for n, p in book.items()} and list_was == sha(codes.path_of(root)), refusal)

        # 5. a merge: an extract that had both keeps one row, the merged code leaves the list, its cards follow
        view = listed()
        a, into = code_named(view, CODES[1]), code_named(view, "The bowl at six")
        both = {(p["case"], x["sheet"], x["row"]) for p in a["by"] for x in p["extracts"]} & \
               {(p["case"], x["sheet"], x["row"]) for p in into["by"] for x in p["extracts"]}
        olds = {name: sha(path) for name, path in book.items()}
        call("/api/codes-ops", {"root": str(root), "ops": [{"op": "describe", "code": CODES[1], "description": "Pulled on the lead"}]})
        got = call("/api/codes-ops", {"root": str(root), "ops": [{"op": "merge", "code": CODES[1], "into": "The bowl at six"}]})
        after = code_named(got, "The bowl at six")
        texts = [p["es"] for name in NAMES for pairs in rows_of(book[name]).values() for p in pairs]
        check("316: a merge gives every extract to the code kept, an extract that had both keeping one row, and the "
              "merged code leaves the list with its description added",
              code_named(got, CODES[1]) is None and CODES[1] not in texts
              and after["extracts"] == a["extracts"] + into["extracts"] - len(both) and "Pulled on the lead" in after["description"],
              json.dumps([a["extracts"], into["extracts"], len(both), after["extracts"]]))
        folded, shown = codes.fold(board(), gets.load(root))
        check("316: on the board the code kept is one card, its count every extract", any(
            v["name"] == "The bowl at six" and v["n"] == after["extracts"] for v in shown.values()), json.dumps(list(shown.values()))[:300])
        call("/api/codes-undo", {"root": str(root)})
        check("316: undo of a merge puts the merged code and its extracts back", code_named(listed(), CODES[1])["extracts"] == a["extracts"]
              and olds == {n: sha(p) for n, p in book.items()})

        # 6. delete: only a code with no extracts
        refusal = refused("/api/codes-ops", {"root": str(root), "ops": [{"op": "delete", "code": CODES[0]}]})
        call("/api/codes-ops", {"root": str(root), "ops": [{"op": "new", "name": "Guilt at the door"}]})
        got = call("/api/codes-ops", {"root": str(root), "ops": [{"op": "delete", "code": "Guilt at the door"}]})
        check("316: a code with extracts cannot be deleted, a code with none is", "cannot be deleted" in refusal
              and code_named(got, "Guilt at the door") is None, refusal)
        call("/api/codes-undo", {"root": str(root)})
        check("316: undo of a delete brings the code back", code_named(listed(), "Guilt at the door") is not None)

        # 7. a name typed on the Coding screen joins the list with the passage's save
        rows = rows_of(book["Juno"])
        (sheet, row), pairs = next(iter(rows.items()))
        server_mod.CONFIG_PATH = config_file
        try:
            with server_mod.scoped("/api/commit", {"path": str(book["Juno"])}):
                routes.api_commit({"path": str(book["Juno"]), "sheet": sheet, "row": row,
                                   "pairs": pairs + [{"es": "Collar on the hook", "kq": pairs[0]["kq"]}]})
        finally:
            server_mod.CONFIG_PATH = kept[0]
        check("316: a name typed as New code joins the list when its passage is saved",
              any(c["name"] == "Collar on the hook" for c in codes.load(root)["codes"]))

        # 8. the board's save from the page: a code's lead alone, its rows laid back beside it
        state = call("/api/gets", {"root": str(root)})
        lead = next(k for k, v in (state.get("codes") or {}).items() if codes.norm(v["name"]) == codes.norm(CODES[0]))
        page = {"id": state["current"], "v": state["version"]["v"], "cards": {c["key"]: {"x": c["x"], "y": c["y"]} for c in state["cards"]},
                "groups": state["groups"], "discarded": state["discarded"]}
        page["cards"][lead] = {"x": 2000, "y": 2000}
        page["groups"][0]["members"] = page["groups"][0]["members"] + [lead]
        call("/api/gets-save", {"root": str(root), "version": page})
        b = board()
        mine = [k for k in b["cards"] if codes.line_codes(gets.load(root)).get(k) == codes.norm(CODES[0])]
        parents = themes.parents_of(b["groups"])
        check("316: the page saves a code's one card, and the file keeps each of its rows there, in its theme",
              len(state["cards"]) < sum(1 for _ in by_code) * 3 and len(mine) == len(gate)
              and {(b["cards"][k]["x"], b["cards"][k]["y"]) for k in mine} == {(2000, 2000)}
              and {parents.get(k) for k in mine} == {page["groups"][0]["id"]}, json.dumps([len(mine), len(gate)]))

        # 9. the command line and MCP: a list, a dry run writing nothing, a rename waiting for his yes
        code, got, err = answer("codes", "list")
        check("316: codes list answers the list", code == 0 and any(c["name"] == CODES[0] for c in got["codes"]), err)
        olds = {name: sha(path) for name, path in book.items()}
        code, got, err = answer("codes", "rename", CODES[0], "The latch", "--dry-run")
        check("316: a rename's dry run says what it would do and writes nothing", code == 0 and got["dry_run"]
              and got["changes"] and olds == {n: sha(p) for n, p in book.items()}, err)
        holds.RUN_AT_ONCE = None
        code, got, err = answer("codes", "rename", CODES[0], "The latch", "--note", "Shorter name", "--tool", "Claude Code")
        hid = (got.get("held") or {}).get("id")
        check("316: an agent's rename waits for his yes in the app, nothing written", bool(hid)
              and olds == {n: sha(p) for n, p in book.items()} and CODES[0] in got["held"]["question"], err or json.dumps(got)[:300])
        server_mod.CONFIG_PATH = config_file
        try:
            done = routes.api_holds({"op": "approve", "root": str(root), "id": hid})
        finally:
            server_mod.CONFIG_PATH = kept[0]
        check("316: approved in the app, the rename runs", code_named(listed(), "The latch") is not None, json.dumps(done)[:300])
        srv = mcp_server.Server(str(root), config=str(config_file))
        tools = {t["name"] for t in mcp_server.tools_for("idiograph")}
        got = srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                      "params": {"name": "codes_show", "arguments": {"code": "The latch"}}}))["result"]
        check("316: MCP has every op of the list, and codes_show reads a code", {
            "codes_list", "codes_show", "codes_new", "codes_rename", "codes_describe", "codes_merge", "codes_delete",
            "codes_add", "codes_remove", "codes_undo", "codes_redo"} <= tools and not got.get("isError"), json.dumps(got)[:300])

        # 9b. an agent's gets apply: one card of a code moved takes the code's other cards with it, a split refused
        holds.RUN_AT_ONCE = True
        codes_now = codes.line_codes(gets.load(root))
        latch = sorted(k for k, c in codes_now.items() if c == codes.norm("The latch") and k in board()["cards"])
        ops = base / "ops.json"
        ops.write_text(json.dumps({"operations": [{"op": "move", "items": [latch[-1]], "to": "G2"}]}), encoding="utf-8")
        code, got, err = answer("gets", "apply", "Board 1", "--ops", str(ops), "--note", "The latch under walks", "--tool", "Claude Code")
        b = board()
        parents = themes.parents_of(b["groups"])
        check("316: an agent moving one card of a code into a theme moves every card of the code there, at one place",
              code == 0 and {parents.get(k) for k in latch} == {"G2"}
              and len({(b["cards"][k]["x"], b["cards"][k]["y"]) for k in latch}) == 1, err or json.dumps([parents.get(k) for k in latch]))
        before_gets = sha(gets.gets_path(root))
        ops.write_text(json.dumps({"operations": [{"op": "move", "items": [latch[0]], "to": "G1"},
                                                  {"op": "move", "items": [latch[1]], "to": None, "reason": "Later"}]}),
                       encoding="utf-8")
        code, got, err = answer("gets", "apply", "Board 1", "--ops", str(ops), "--note", "Split it", "--tool", "Claude Code")
        check("316: an agent moving two cards of one code to different places is refused, nothing written",
              code != 0 and "different places" in err and before_gets == sha(gets.gets_path(root)), err)
        holds.RUN_AT_ONCE = None

        # 9c. a share of one participant takes the codes they use, and a copy coming back adds the codes it lacks
        sent = base / "Juno's copy.idiograph"
        server_mod.CONFIG_PATH = config_file
        try:
            routes.send_project(root, sent, participants=["Juno"])
        finally:
            server_mod.CONFIG_PATH = kept[0]
        import zipfile
        import project_pack as pack_mod
        with zipfile.ZipFile(sent) as zf:
            carried = json.loads(zf.read("project/idiograph-codes.json"))
        juno = {codes.norm(p["es"]) for pairs in rows_of(book["Juno"]).values() for p in pairs if p["es"].strip()}
        check("316: a share of some participants carries the code list holding the codes they use alone, descriptions "
              "with them", {codes.norm(c["name"]) for c in carried["codes"]} == juno
              and any(c["description"] for c in carried["codes"]), json.dumps(carried["codes"])[:300])
        carried["codes"] = [dict(c, description="Their words") for c in carried["codes"]] + [
            {"id": "k99", "name": "LEAD by the door", "description": "Waiting by the door with the lead"}]
        back = base / "Juno back.idiograph"
        with zipfile.ZipFile(sent) as zin, zipfile.ZipFile(back, "w") as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "project/idiograph-codes.json":
                    data = json.dumps(carried).encode("utf-8")
                elif item.filename == "project/" + server_mod.PROJECT_FILE:
                    # the copy as one opened from this project's send and sent back holds it
                    held = json.loads(data)
                    held["copy_of"] = {"uid": routes.project_file(root).get(pack_mod.UID_KEY), "name": held.get("name")}
                    data = json.dumps(held).encode("utf-8")
                zout.writestr(item, data)
        mine = {c["name"]: c["description"] for c in codes.load(root)["codes"]}
        server_mod.CONFIG_PATH = config_file
        try:
            with server_mod.scoped("/api/boards-in", {"root": str(root)}):
                came = routes.boards_in(root, back, from_name="Curt", request="Bring Curt's codes in")
        finally:
            server_mod.CONFIG_PATH = kept[0]
        now = {c["name"]: c["description"] for c in codes.load(root)["codes"]}
        check("316: a copy coming back adds the codes it lacks by name, its description with it, and never changes a "
              "description the project has", came.get("codes") == ["LEAD by the door"]
              and now["LEAD by the door"] == "Waiting by the door with the lead"
              and all(now[n] == d for n, d in mine.items()), json.dumps(came.get("codes")))

        # 10. an IPA project refuses every op, its files untouched
        ipa_books = {name: sha(ipa / name / f"{name} - EN & ES.xlsx") for name in NAMES}
        said = refused("/api/codes", {"root": str(ipa)})
        code, _out, err = cli.run(["--config", str(config_file), "--root", str(ipa), "codes", "list"])
        state = call("/api/gets", {"root": str(ipa)})
        check("316: an IPA project refuses the code list on the page's route and the command line, writes no list, "
              "and its board folds nothing", said == i18n.t("codes.refused_ipa") and code != 0
              and not codes.path_of(ipa).exists() and "codes" not in state
              and ipa_books == {name: sha(ipa / name / f"{name} - EN & ES.xlsx") for name in NAMES}, said + err)
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, holds.RUN_AT_ONCE = kept
