"""313. The canvas as a PDF and as an image (exportA, Adam, 1 November 2026: "Canvas should give both a PDF and an
image", Export following the view), drawn by Typst from the board since 9 November 2026 (typst5, area 367).

Checked on the demo's invented cases in a scratch project: the routes name the canvas's PDF and PNG beside the
workbook where the table's PDF goes, or at the project's root where the GETs card's goes, named as the table's with
" canvas" after it, their dry runs writing nothing, the file written by the server, never over a file there, in node
on themes.js's own `thCanvasOut`, the window and a browser's tab alike asking the server, Quotes on cards and the
participant notes sent, and the agents' `board export --canvas` and `gets export --canvas` naming the same files and
refusing the table's ticks, and writing only the file.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import support
from .support import DEMO_QUESTION, check, skip


NODE_OUT = r"""
const out = {};
let state = null;
const fresh = () => ({ calls: [], exported: null, said: [] });
const TH = { live: true, busy: false, dirty: false, path: '/p/Juno/Juno.xlsx', root: 'r1', meta: { id: 'b1', name: 'Board 1' } };
let GETS = false;
let failing = null;
const thGets = () => GETS;
const t = (key) => key;
const say = (line) => state.said.push(line);
const needsRestart = () => false;
const RESTART_LINE = 'restart';
const TH_CANVAS_EMPTY = 'empty';
const thXmenu = () => {};
const thTitleDone = () => {};
const thNoteDone = () => {};
const gtRowNoteDone = () => {};
const thFlush = async () => {};
const thWhere = () => ({});
const thQuotesWay = () => 'short';
const thCanvasCopy = () => ({ box: { x: 0, y: 0, w: 900, h: 600 }, html: '' });
const thExported = (info) => { state.exported = info; };
const console = { warn: () => {} };
async function api(url, body) {
  state.calls.push([url, body]);
  if (failing) throw new Error(failing);
  const name = url === '/api/gets-boards' ? 'Dogs - Board 1 - GETs canvas.' + body.kind : 'Juno - Board 1 - PETs canvas.' + body.kind;
  return { path: '/p/Juno/' + name, shown: [name], version: { name: 'Board 1' } };
}
const window = { location: { href: 'http://127.0.0.1:8799/#pets', origin: 'http://127.0.0.1:8799' } };
/*FN*/
(async () => {
  for (const kind of ['pdf', 'png']) {
    state = fresh();
    await thCanvasOut(kind);
    out[kind] = state;
  }
  state = fresh();
  GETS = true;
  await thCanvasOut('png', { notes: true });
  out.gets = state;
  state = fresh();
  failing = 'The PDF could not be made, so nothing was written.';
  await thCanvasOut('pdf', { notes: true });
  out.failed = state;
  process.stdout.write(JSON.stringify(out) + '\n');
})();
"""


def test_canvas_out(scratch: Path):
    print("\n313. The canvas as a PDF and as an image: named where the table's PDF goes, written by the server through "
          "Typst, the page's own Save asking the server, and the agents' the same files")
    import cli
    import i18n
    import idiograph_routes as routes
    import server as server_mod
    import typeset

    if not typeset.available():
        skip("313: the canvas's files", "typst-py is not installed")
        return
    pristine = support.DEMO_SHIPPED
    root = scratch / "a313"
    shutil.rmtree(root, ignore_errors=True)
    for name in ("Juno", "Mabel", "Rowan"):
        (root / name / "Working").mkdir(parents=True)
        shutil.copy2(pristine / f"{name} - EN & ES.xlsx", root / name / f"{name} - EN & ES.xlsx")
        for side in (pristine / "Working").glob(f"{name} - *"):
            shutil.copy2(side, root / name / "Working" / side.name)
    shutil.copy2(pristine / "idiograph-gets.json", root / "idiograph-gets.json")
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Dogs, a canvas project", "research_question": DEMO_QUESTION,
        "agents": {"allowed": True, "at": "2026-11-01T10:00:00+00:00"}}), encoding="utf-8")
    cfg = scratch / "a313-config.json"
    cfg.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Ada", "corpus": "",
                               "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")
    book = root / "Juno" / "Juno - EN & ES.xlsx"
    files = lambda: {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*"))
                     if p.is_file() and not p.name.startswith(".")}

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, str(root)
        before = files()
        gets_board = json.loads((root / "idiograph-gets.json").read_text(encoding="utf-8"))
        gid = str(((gets_board.get("boards") or gets_board.get("versions") or [{}])[0]).get("id") or "")

        # ── A. the routes name the files where the table's go, their dry runs writing nothing
        table = routes.api_themes_export({"workbook": str(book), "op": "pdf", "dry_run": True})
        named = {kind: routes.api_themes_export({"workbook": str(book), "op": "canvas", "kind": kind, "dry_run": True})
                 for kind in ("pdf", "png")}
        stem = Path(table["path"]).stem
        check("313: the canvas's PDF and PNG are named beside the workbook where the table's PDF goes, as the table's "
              "with canvas after it, and a dry run writes nothing",
              all(Path(n["path"]).parent == Path(table["path"]).parent == book.parent for n in named.values())
              and named["pdf"]["name"] == f"{stem} canvas.pdf" and named["png"]["name"] == f"{stem} canvas.png"
              and named["png"]["shown"] == [f"{stem} canvas.png"] and "href" not in named["png"] and files() == before,
              json.dumps({k: v.get("name") for k, v in named.items()}) + " " + table["name"])
        gets_table = routes.api_gets_boards({"root": str(root), "board": gid, "op": "pdf", "dry_run": True})
        gets_named = routes.api_gets_boards({"root": str(root), "board": gid, "op": "canvas", "kind": "png", "dry_run": True})
        check("313: a GETs board's canvas is named at the project's root where the print card's PDF goes",
              Path(gets_named["path"]).parent == Path(gets_table["path"]).parent == root
              and gets_named["name"].endswith(" - GETs canvas.png") and gets_named["name"].startswith("Dogs, a canvas project - ")
              and files() == before, f"{gets_named.get('name')} {gets_table.get('name')}")
        try:
            routes.api_themes_export({"workbook": str(book), "op": "canvas", "kind": "gif"})
            refused = ""
        except routes.WorkbookError as exc:
            refused = str(exc)
        check("313: a kind that is neither pdf nor png is refused with nothing written",
              refused == i18n.t("server.canvas_pdf_or_png") and files() == before, refused)

        # ── B. the file written by the server, never over a file there
        first = routes.api_themes_export({"workbook": str(book), "op": "canvas", "kind": "png"})
        second = routes.api_themes_export({"workbook": str(book), "op": "canvas", "kind": "png"})
        made = sorted(p.name for p in book.parent.glob("*canvas*.png"))
        check("313: Save as an image writes the picture beside the workbook, a second one dated, never over the first",
              first["name"] == f"{stem} canvas.png" and second["dated"] and second["name"] != first["name"] and len(made) == 2
              and (book.parent / first["name"]).read_bytes()[:8] == b"\x89PNG\r\n\x1a\n" and first.get("pixels"),
              json.dumps([first.get("name"), second.get("name"), made]))
        for p in book.parent.glob("*canvas*.png"):
            p.unlink()

        # ── C. the agents name the same files, refuse the table's ticks, and write only the file
        def run(*args):
            code, said, err = cli.run(["--root", str(root), "--config", str(cfg), *args, "--json"])
            return code, (support.plain(json.loads(said)) if said.strip() else {}), err
        code, dry, err = run("board", "export", "Juno", "--canvas", "png", "--dry-run")
        code_g, gdry, _ = run("gets", "export", "--canvas", "pdf", "--dry-run")
        code_t, tj, ticked = run("board", "export", "Juno", "--canvas", "png", "--labels", "numbers")
        ticked += json.dumps(tj)
        code_w, wj, what = run("gets", "export", "--canvas", "png", "--what", "trail")
        what += json.dumps(wj)
        check("313: board export --canvas and gets export --canvas name the files the routes name, their dry runs "
              "writing nothing, and the table's ticks refused",
              code == 0 and dry.get("file") == named["png"]["name"] and dry.get("dry_run") and code_g == 0
              and gdry.get("file") == Path(gets_named["path"]).with_suffix(".pdf").name
              and code_t != 0 and "--labels" in ticked and code_w != 0 and "--what" in what and files() == before,
              (err or ticked or what)[-300:] + json.dumps(dry)[:200])
        code, wrote, err = run("board", "export", "Juno", "--canvas", "png")
        after = files()
        new = sorted(set(after) - set(before))
        check("313: board export --canvas png writes only the PNG, its pixels said, the board's files unchanged",
              code == 0 and new == [f"Juno/{named['png']['name']}"] and all(after[k] == before[k] for k in before)
              and wrote.get("pixels") and wrote["pixels"][0] > 2000, err[-300:] + json.dumps(wrote)[:300])
        if new:
            (root / new[0]).unlink()
        code, gwrote, err = run("gets", "export", "--canvas", "pdf", "--notes")
        check("313: gets export --canvas pdf writes the PDF at the project's root",
              code == 0 and (root / gwrote.get("file", "-")).read_bytes()[:5] == b"%PDF-", err[-300:] + json.dumps(gwrote)[:300])
        if gwrote.get("file"):
            (root / gwrote["file"]).unlink()
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    # ── D. in node, the page's own thCanvasOut: the window and a browser's tab alike ask the server
    js = support.text("apps/idiograph/static/themes.js")
    fn = js.split("async function thCanvasOut(", 1)[1].split("\n}\n", 1)[0]
    ran = support.run_node(NODE_OUT.replace("/*FN*/", "async function thCanvasOut(" + fn + "\n}\n"), scratch / "a313", "a313-out.js")
    got = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {}
    pdf, png, gets, failed = (got.get(k) or {} for k in ("pdf", "png", "gets", "failed"))
    body = lambda s: (s.get("calls") or [[None, {}]])[-1][1]
    check("313: Save as PDF and Save as an image on the canvas ask the server for the file with the board, the kind and "
          "Quotes on cards as the canvas shows them, no page sent, and the line after names it",
          body(pdf) == {"op": "canvas", "kind": "pdf", "board": "b1", "quotes": "short", "workbook": "/p/Juno/Juno.xlsx",
                        "version": "b1"}
          and body(png).get("kind") == "png" and "html" not in body(png)
          and (png.get("exported") or {}).get("shown") == ["Juno - Board 1 - PETs canvas.png"]
          and (png.get("exported") or {}).get("reveal") is True, ran.stderr[-300:] or json.dumps(got)[:600])
    check("313: on the GETs the picture goes through the GETs boards' route with the participant notes asked, and a "
          "file the server could not make says its plain sentence",
          (gets.get("calls") or [[None]])[-1][0] == "/api/gets-boards" and body(gets).get("notes") is True
          and (gets.get("exported") or {}).get("reveal") is False
          and failed.get("said") == ["The PDF could not be made, so nothing was written."] and not failed.get("exported"),
          json.dumps([gets, failed])[:400])
