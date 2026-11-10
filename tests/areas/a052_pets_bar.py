from __future__ import annotations

import inspect
import json
import shutil

from workbook import WorkbookError

from . import support
from .support import check, demo_copy, skip
import idiograph_routes


def test_pets_bar(scratch):
    print("\n52. The PETs bar carries less: the Current board, the Inspector, one door to the sidebar, "
          "the share glyph and New AI board from the board menu")
    import subprocess
    import server as server_mod
    import themes as themes_mod
    import themes_print

    js = support.text("apps/idiograph/static/themes.js")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0]

    # ── A. the Current board in the file, through the board op `choose`
    root = scratch / "pets-bar-root"
    work = demo_copy(root, "Juno", "Juno - EN & ES.xlsx")
    saved_root = server_mod.ROOT_OVERRIDE
    server_mod.ROOT_OVERRIDE = str(root)
    file = lambda: json.loads(themes_mod.themes_path(work).read_text(encoding="utf-8"))

    def refused(call):
        try:
            call()
        except WorkbookError as exc:
            return str(exc)
        return ""

    op = lambda name, **extra: idiograph_routes.api_themes_versions(dict({"workbook": str(work), "op": name}, **extra))
    try:
        opened = idiograph_routes.api_themes({"workbook": str(work)})
        check("113: a case with no themes file opens with no Current board, and writes nothing",
              opened["chosen"] is None and not themes_mod.themes_path(work).exists())
        first = op("choose", id="v1")
        check("113: a file with one board marks nothing by itself, and choose marks it beside current, never in its place",
              first["chosen"] == "v1" and first["current"] == "v1" and file()["chosen"] == "v1"
              and list(file()).index("chosen") == list(file()).index("current") + 1
              and list(file()).index("chosen") < list(file()).index("boards"))
        op("new")
        made = file()
        check("113: a new board goes on the canvas as current, and the Current board stays the one marked",
              made["current"] == "v2" and made["chosen"] == "v1" and op("switch", id="v1")["chosen"] == "v1")
        board = idiograph_routes.api_themes({"workbook": str(work)})
        idiograph_routes.api_themes_save({"workbook": str(work), "version": dict(board["version"], cards={c["key"]: {"x": c["x"], "y": c["y"], "text": c["text"]} for c in board["cards"]},
                                                                          groups=[], discarded=[], picks={}, chosen="v2")})
        check("113: a save from the canvas never moves the mark, whatever it sends",
              file()["chosen"] == "v1" and file()["current"] == "v1")
        dup = op("duplicate", id="v1")
        check("113: a duplicate of the Current board does not carry the mark",
              dup["current"] == "v3" and dup["chosen"] == "v1" and file()["chosen"] == "v1")
        moved = op("choose", id="v3")
        check("113: marking another board moves the mark, one Current board at most",
              moved["chosen"] == "v3" and file()["chosen"] == "v3" and moved["current"] == "v3")
        cleared = op("choose", id=None)
        check("113: choose with null clears the mark, and the file then carries none",
              cleared["chosen"] is None and "chosen" not in file() and cleared["current"] == "v3")
        check("113: choose of a board the file does not hold is refused, and the mark stays as it was",
              "no longer in the themes file" in refused(lambda: op("choose", id="v9")) and "chosen" not in file())
        op("choose", id="v2")
        gone = op("delete", id="v2")
        check("113: deleting the Current board clears the mark, and deleting another leaves it",
              gone["chosen"] is None and "chosen" not in file())
        op("choose", id="v1")
        kept = op("delete", id="v3")
        check("113: deleting a board that is not the Current one keeps the mark where it was",
              kept["chosen"] == "v1" and file()["chosen"] == "v1")
        printed = themes_print.page(work, "Juno", "v1", "", auto=False)
        other = op("new")
        printed_other = themes_print.page(work, "Juno", other["current"], "", auto=False)
        head = printed.split('<header class="head">', 1)[1].split("</header>", 1)[0]
        check("113, 311: the print view's header no longer says Current board, the board named in the foot (Adam, 31 October)",
              "Current board" not in head and "Juno (Board 1)" in printed
              and "Current board" not in printed_other.split("</header>", 1)[0])
        check("113: the board ops route names choose, and `chosen_of` reads only a board the file holds",
              "choose" in themes_mod.OPS and themes_mod.chosen_of({"chosen": "v7", "boards": [{"id": "v1"}]}) is None
              and themes_mod.chosen_of({"chosen": "v1", "boards": [{"id": "v1"}]}) == "v1"
              and themes_mod.chosen_of(None) is None and "`choose`" in inspect.getsource(idiograph_routes.api_themes_versions))
    finally:
        server_mod.ROOT_OVERRIDE = saved_root

    # ── B. the Current board on the page
    menu = fn(js, "thVmenuDraw")
    check("113: it carries Mark as current, or Unmark current on the Current board, for the board on the canvas",
          "marked ? t('themes.board.unmark') : t('themes.board.mark')" in menu and 'data-vop="choose"' in menu
          and "else if (what === 'choose') thChoose();" in js
          and "thBoardOp('choose', { id: TH.chosen === TH.meta.id ? null : TH.meta.id })" in fn(js, "thChoose"))
    check("113: the page takes the mark from every answer, and a server from before it says to restart",
          "TH.chosen = data.chosen || null;" in fn(js, "thLoad")
          and "TH.choosable = Object.prototype.hasOwnProperty.call(data, 'chosen');" in fn(js, "thLoad")
          and "if (Object.prototype.hasOwnProperty.call(data, 'chosen')) TH.chosen = data.chosen || null;" in fn(js, "thTakeBoards")
          and "if (!TH.choosable) { thVsaid(RESTART_LINE); return; }" in fn(js, "thChoose")
          and "chosen" not in fn(js, "thBody"))

    # ── C. the sidebar: its button, no handles, and what opens it
    check("114: n, Note and a PET note undone or done again open the Inspector, and the review's link leaves it as it was",
          "thInspectorOpen(item);" in fn(js, "thNamesAsk") and "thInspectorOpen({ kind: 'group', id });" in fn(js, "thNoteOpen")
          and "if (noted) thInspectorOpen({ kind: 'group', id: noted });" in fn(js, "thUndo")
          and "thInspectorOpen" not in fn(js, "thReviewShow") and "thInspectorOpen" not in fn(js, "thDragStart"))

    # ── D. the share glyph, and New AI board's card
    spark_entry = menu.split("data-vop=\"ai\"", 1)[1].split("</button>", 1)[0]
    check("118: New AI board in the board menu carries the sparkles, and is there only with the switch on",
          "${TH_SPARK_ICON}${esc(t('themes.board.ai'))}" in spark_entry and "(thAiOn() ? `<button" in menu
          and "else if (what === 'ai') thAiCard(true);" in js)
    check("118: with the switch off the card puts itself away, and the stepper still saves under themes",
          "if (!thAiOn() && !$('th-aicard').hidden) thAiCard(false);" in fn(js, "thAiDraw")
          and "api('/api/settings', { themes: { cap: next } })" in fn(js, "thCapStep"))

    # ── F. the page's own model, in node
    node = shutil.which("node")
    if not node:
        return skip("114: the Inspector's model in node", "no node on this machine")
    script = scratch / "pets-bar.js"
    script.write_text(support.i18n_js() + js + r"""
const store = {};
globalThis.localStorage = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); } };
const card = (x, y) => ({ x, y, text: 't' });
TH.v = { cards: { 'S:1:0': card(0, 0), 'S:2:0': card(300, 0), 'S:3:0': card(600, 0) }, groups: [], discarded: [], picks: {} };
const g = thMakeGroup(TH.v, ['S:3:0'], 'Mornings');
const out = {};
out.none = thPanelPick();
TH.sel.cards.add('S:1:0');
out.one = thPanelPick();
TH.sel.cards.add('S:2:0'); TH.sel.groups.add(g);
TH.lastPick = { kind: 'card', id: 'S:2:0' };
out.last = thPanelPick();
TH.lastPick = { kind: 'group', id: g };
out.label = thPanelPick();
TH.lastPick = null; TH.panel = { kind: 'card', id: 'S:1:0' };
out.held = thPanelPick();
TH.panel = null;
out.first = thPanelPick();
console.log(JSON.stringify(out));
""", encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return check("114: the Inspector's model runs in node", False, run.stderr.strip()[:300])
    out = json.loads(run.stdout)
    check("114: in node, nothing selected shows nothing, one selected shows that one",
          out["none"] is None and out["one"] == {"kind": "card", "id": "S:1:0"}, str(out))
    check("114: in node, with several selected the Inspector shows the one clicked last, a card or a label",
          out["last"] == {"kind": "card", "id": "S:2:0"} and out["label"] == {"kind": "group", "id": "g1"}, str(out))
    check("114: in node, with none clicked it keeps what it shows while that is selected, and else the first label",
          out["held"] == {"kind": "card", "id": "S:1:0"} and out["first"] == {"kind": "group", "id": "g1"}, str(out))
