from __future__ import annotations

import json
import shutil
import subprocess

import openpyxl

from . import support
from .support import check, skip
import idiograph_routes


def edges_js() -> str:
    """The column edges' model from app.js, `EDGE_MINS` to `edgesAt`, for a piece of it run in node."""
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    start = app.index("const EDGE_MINS = ")
    end = app.index("\n}\n", app.index("function edgesAt(")) + 3
    return app[start:end]


def test_column_widths(scratch):
    print("\n220. The statements screen's column edges and two windows in step (20 October, Adam's way C from a tester's "
          "letterbox at 2560): each edge's drag kept per screen across a restart, Reset widths and a double click "
          "on one edge, and a passage saved in one window reaching the other's statements screen")
    import server as server_mod
    import workbook as wb_mod

    root = scratch / "a220-root"
    shutil.rmtree(root, ignore_errors=True)
    pristine = support.DEMO_PRISTINE
    (root / "Rowan" / "Working").mkdir(parents=True)
    book = root / "Rowan" / "Rowan - EN & ES.xlsx"
    shutil.copy2(pristine / "Rowan - EN & ES.xlsx", book)
    for side in (pristine / "Working").glob("Rowan - *"):
        shutil.copy2(side, root / "Rowan" / "Working" / side.name)
    (root / "idiograph-project.json").write_text(json.dumps({"name": "Dogs, a scratch project"}), encoding="utf-8")
    config = scratch / "a220-config.json"
    config.write_text(json.dumps({"root": str(root), "interviewer": "Adam", "corpus": "", "gravity_reference": "",
                                  "corpus_exclude": []}), encoding="utf-8")

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = config, str(root)

        # ── A. the widths kept per screen, across a restart, one screen at a time
        wide = {"left": 270, "right": 180, "statements": 640, "notes": 736}
        server_mod.api_settings({"column_widths": {"screen": "2560", "widths": wide}})
        server_mod.api_settings({"column_widths": {"screen": 1280, "widths": {"left": 40, "notes": 300, "width": 9}}})
        on_disk = json.loads(config.read_text(encoding="utf-8")).get("column_widths")
        again = server_mod.merge_config(server_mod.saved_config())["column_widths"]
        check("220: a drag's widths are kept for their screen in config.json and read back after a restart, a second "
              "screen's beside them and never over them, a part that is no width left out",
              on_disk == again == {"2560": wide, "1280": {"left": 40, "notes": 300}}, json.dumps(on_disk))
        server_mod.api_settings({"column_widths": {"screen": "2560", "widths": None}})
        server_mod.api_settings({"column_widths": {"screen": "-3", "widths": wide}})
        server_mod.api_settings({"column_widths": {"widths": wide}})
        after = server_mod.merge_config(server_mod.saved_config())["column_widths"]
        check("220: Reset widths takes that screen's widths away and leaves the other's, and a screen that is no width "
              "writes nothing", after == {"1280": {"left": 40, "notes": 300}}, json.dumps(after))
        config.write_text(json.dumps({"root": str(root), "column_widths": {"2560": {"left": "wide"}, "x": {}}}),
                          encoding="utf-8")
        check("220: a settings file from before, or holding anything else, opens every screen as it always has",
              server_mod.merge_config(server_mod.saved_config())["column_widths"] == {}, "")

        # ── B. two windows in step: the stamp says the workbook's time and whether a window of the app wrote it
        first = idiograph_routes.api_stamp({"workbook": str(book)}).get("workbook") or {}
        opened = idiograph_routes.api_open({"path": str(book)})
        row = next(r for s in opened["sheets"] for r in s["rows"] if r.get("name") and r["name"] != "Adam")
        idiograph_routes.api_commit({"path": str(book), "sheet": row["sheet"], "row": row["row"], "v": row.get("v"),
                               "pairs": [{"es": "Walking at the dog's pace", "kq": ""}], "en": "Slowing down for her."})
        saved = idiograph_routes.api_stamp({"workbook": str(book)}).get("workbook") or {}
        read = idiograph_routes.api_open({"path": str(book)})
        now = next(r for s in read["sheets"] for r in s["rows"] if r["sheet"] == row["sheet"] and r["row"] == row["row"])
        check("220: a passage saved in one window moves the workbook's time on the stamp, said as this app's own, and "
              "the other window reads it again with the passage's new words and version",
              bool(first.get("at")) and saved.get("at") != first.get("at") and saved.get("here") is True
              and "Walking at the dog's pace" in (now.get("es") or "") and now.get("v") != row.get("v"),
              json.dumps([first, saved]))
        wb = openpyxl.load_workbook(book)
        wb.save(book)
        outside = idiograph_routes.api_stamp({"workbook": str(book)}).get("workbook") or {}
        check("220: a workbook saved outside the app is said as not this app's, so it keeps its own notice",
              outside.get("here") is False and outside.get("at") != saved.get("at"), json.dumps(outside))
        twice = idiograph_routes.api_stamp({"workbook": str(book)}).get("workbook") or {}
        check("220: the stamp writes nothing, its look leaving the workbook's time as it was",
              twice.get("at") == outside.get("at") and wb_mod.written_here(book) is False, json.dumps(twice))
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    # ── C. the edges' model in node: a drag moves its edge alone, the double click puts it back, Reset is nothing kept
    node = shutil.which("node")
    if not node:
        skip("220: the column edges' model in node", "node is not installed")
        return
    script = scratch / "a220-edges.js"
    script.write_text("""
globalThis.document = { documentElement: { clientWidth: 2560 } };
globalThis.window = { innerWidth: 2560 };
globalThis.getComputedStyle = () => ({ getPropertyValue: () => '28px' });
globalThis.$ = () => ({});
globalThis.stackedNow = () => false;
globalThis.S = {};
""" + edges_js() + r"""
const nat = { left: 540, right: 548, inL: 8, inR: 16, order: ['statements', 'transcript', 'notes'],
  widths: { statements: 370, notes: 370 } };
const out = {};
const at = (m) => edgesAt(m, nat).map(Math.round);
out.natural = at(nat);
out.tx = Math.round(edgesTx(nat, nat));
let m = edgeMove(nat, nat, 0, -270);
out.first = { at: at(m), w: m.widths, left: m.left, tx: Math.round(edgesTx(m, nat)) };
m = edgeMove(m, nat, 3, 360);
out.last = { at: at(m), w: m.widths, right: m.right };
m = edgeMove(m, nat, 1, 100);
out.between = { at: at(m), w: m.widths, tx: Math.round(edgesTx(m, nat)) };
const far = edgeMove(m, nat, 2, -5000);
out.far = { tx: Math.round(edgesTx(far, nat)), notes: Math.round(far.widths.notes) };
const narrow = edgeMove(nat, nat, 1, -5000);
out.narrow = Math.round(narrow.widths.statements);
const home = edgeHome(m, nat, 1);
out.home = { at: at(home), w: home.widths };
out.kept = edgesKept(m, nat, null);
let back = m;
for (const k of [0, 1, 2, 3]) back = edgeHome(back, nat, k);
out.allBack = edgesKept(back, nat, { left: 1, right: 2, statements: 3, notes: 4 });
document.documentElement.clientWidth = 1280;
const sq = edgesSqueezed(m, nat);
out.squeezed = { tx: Math.round(edgesTx(sq, nat)), left: Math.round(sq.left), right: Math.round(sq.right),
  w: Object.fromEntries(Object.entries(sq.widths).map(([k, v]) => [k, Math.round(v)])) };
console.log(JSON.stringify(out));
""", encoding="utf-8")
    ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    try:
        o = json.loads(ran.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        o = {}
    said = (ran.stdout + ran.stderr)[:600]
    nat_at = o.get("natural") or [0, 0, 0, 0]
    first = o.get("first") or {}
    last = o.get("last") or {}
    between = o.get("between") or {}
    check("220: in node, the first column's outer edge dragged 270 pixels out moves that edge alone, the statements "
          "taking the room and the transcript as it was",
          first.get("at", [None])[0] == nat_at[0] - 270 and first.get("at", [])[1:] == nat_at[1:]
          and first.get("w", {}).get("statements") == 640 and first.get("tx") == o.get("tx"), said)
    check("220: in node, the last column's outer edge dragged out grows the notes, every other edge where it was",
          last.get("at", [])[3:] == [nat_at[3] + 360] and last.get("at", [])[:3] == first.get("at", [])[:3]
          and last.get("w", {}).get("notes") == 730, said)
    check("220: in node, an edge between two columns moves alone, the statements growing and the transcript giving "
          "the room", between.get("at", [])[1] == nat_at[1] + 100 and between.get("w", {}).get("statements") == 740
          and between.get("tx") == o.get("tx") - 100, said)
    check("220: in node, a drag stops where the transcript keeps its 300 pixels and a column its least",
          300 <= (o.get("far") or {}).get("tx", 0) <= 301 and 210 <= (o.get("narrow") or 0) <= 211, said)
    check("220: in node, a double click puts its own edge back where the screen opens and leaves the others",
          (o.get("home") or {}).get("at", [])[1] == nat_at[1] and (o.get("home") or {}).get("at", [])[0] == between.get("at", [None])[0]
          and (o.get("home") or {}).get("at", [])[3] == between.get("at", [None, None, None, None])[3], said)
    check("220: in node, edges moved are kept as the screen's widths, and every edge back where it opens keeps nothing, "
          "so Reset widths is faint again",
          (o.get("kept") or {}).get("statements") == 740 and o.get("allBack") is None, said)
    sq = o.get("squeezed") or {}
    check("220: in node, widths kept on a wide window, on a narrower one, give the margins first and keep the "
          "transcript its 300 pixels", sq.get("tx", 0) >= 299 and sq.get("left") >= 16 and sq.get("right") >= 24, said)
