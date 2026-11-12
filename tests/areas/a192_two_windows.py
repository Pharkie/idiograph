"""Area 192: no work lost between two windows, a resize while typing, and a drag that takes whole words (18 October).

A save of a passage's statements, notes and key quotes carries the version of the passage it last read, and
a save over a newer one is refused with nothing written, from the page and from the MCP server alike. The
field holding the caret stays where it stood across a resize of the window, and a drag's selection in a
passage is taken out to whole words. Every passage here is the demo's invented one, on living with a dog,
with invented statements.
"""
from __future__ import annotations

import json
import shutil
import subprocess

import rounds as rounds_mod
import workbook as wb_mod

from . import support
from .support import DEMO_QUESTION, DEMO_SHEET, check, skip
import idiograph_routes
import idiograph_cli


def test_two_windows(scratch):
    print("\n192. Two windows on one passage, a resize while typing and a drag over part of a word, 18 October: a stale "
          "save refused with nothing written, the MCP server's too, the focused field kept in view, whole words taken")
    import locks
    import mcp_server
    import server as server_mod

    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    node = shutil.which("node")
    pristine = support.DEMO_PRISTINE

    root = scratch / "two-windows-root"
    shutil.rmtree(root, ignore_errors=True)
    (root / "Juno" / "Working").mkdir(parents=True)
    book = root / "Juno" / "Juno - EN & ES.xlsx"
    shutil.copy2(pristine / "Juno - EN & ES.xlsx", book)
    for side in (pristine / "Working").glob("Juno - *"):
        shutil.copy2(side, root / "Juno" / "Working" / side.name)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({
        "name": "Dogs, a two windows project", "research_question": DEMO_QUESTION,
        "agents": {"allowed": True, "at": "2026-10-18T12:00:00+01:00"}}), encoding="utf-8")
    config_file = scratch / "two-windows-config.json"
    config_file.write_text(json.dumps({"root": str(root), "interviewer": "Adam"}), encoding="utf-8")
    row_of = lambda n: next(r for s in wb_mod.read_case(book)["sheets"] if s["name"] == DEMO_SHEET
                            for r in s["rows"] if r["row"] == n)

    # ── 1. the workbook: a save carries the version it read, and a newer one refuses it whole
    first = row_of(15)
    check("192: every passage the page reads carries its version, the same for the same words spaced otherwise",
          isinstance(first.get("v"), str) and len(first["v"]) == 12
          and wb_mod.passage_version("a\n\nb", None, "(no quote)\n\n\"q\"") == wb_mod.passage_version("a\n\n\n b ", "", "(No Quote)\n\n\"q\""))
    one = wb_mod.save_turn(book, DEMO_SHEET, 15, None, "", None,
                           pairs=[{"es": "A walk written in the first window", "kq": ""}], was=first["v"])
    newer = row_of(15)
    check("192: a fresh save is written and answers the passage's new version",
          one["changed"] is True and one["v"] == newer["v"] != first["v"]
          and newer["es"] == "A walk written in the first window")
    before = book.read_bytes()
    try:
        wb_mod.save_turn(book, DEMO_SHEET, 15, None, "A note from the second window", None,
                         pairs=[{"es": "A walk written in the second window", "kq": ""}], was=first["v"])
        stale = None
    except wb_mod.StaleTurn as exc:
        stale = exc
    check("192: a save over a passage changed since it was read is refused, nothing written, and the refusal carries "
          "the passage as it now reads, the newer statement kept",
          stale is not None and str(stale) == wb_mod.STALE_LINE and book.read_bytes() == before
          and stale.now["es"] == "A walk written in the first window" and stale.now["v"] == newer["v"]
          and stale.now["pairs"] == [{"es": "A walk written in the first window", "kq": ""}])
    same = wb_mod.save_turn(book, DEMO_SHEET, 15, None, None, None,
                            pairs=[{"es": "A walk written in the first window", "kq": ""}], was=first["v"])
    check("192: a save from an old read that changes nothing is answered as ever, nothing written",
          same["changed"] is False and book.read_bytes() == before)

    # ── 2. the page's route: 409 with the passage as saved, the progress file untouched
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, locks.WAIT)
    try:
        server_mod.CONFIG_PATH = config_file
        server_mod.ROOT_OVERRIDE = str(root)
        server_mod.STATE_MEMORY = {"recent": []}
        progress = rounds_mod.progress_path(book)
        held = progress.read_bytes() if progress.exists() else None
        refused = idiograph_routes.api_commit({"path": str(book), "sheet": DEMO_SHEET, "row": 15, "en": "", "v": first["v"],
                                         "pairs": [{"es": "A walk written in the second window", "kq": ""}]})
        check("192: /api/commit refuses a stale save with 409, the line and the passage as saved, nothing written to the "
              "workbook or the progress file",
              refused.get("status") == 409 and refused.get("error") == wb_mod.STALE_LINE
              and refused["stale"]["es"] == "A walk written in the first window" and refused["stale"]["v"] == newer["v"]
              and book.read_bytes() == before and (progress.read_bytes() if progress.exists() else None) == held)
        fresh = idiograph_routes.api_commit({"path": str(book), "sheet": DEMO_SHEET, "row": 15, "en": "", "v": newer["v"],
                                       "pairs": [{"es": "A walk written in the first window", "kq": ""},
                                                 {"es": "A second, seen and kept", "kq": ""}]})
        check("192: /api/commit takes a save from the version as saved, Overwrite's way, and answers the new one",
              "status" not in fresh and fresh["changed"] is True and fresh["v"] == row_of(15)["v"]
              and row_of(15)["es"] == "A walk written in the first window\nA second, seen and kept")
        legacy = idiograph_routes.api_commit({"path": str(book), "sheet": DEMO_SHEET, "row": 17, "en": "",
                                        "pairs": [{"es": "From a page with no version", "kq": ""}]})
        check("192: a page from before the version still saves", legacy["changed"] is True)

        # ── 3. the MCP server: turn_show gives the version, a turn_write from an older one is refused
        srv = mcp_server.Server(str(root), config=str(config_file))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                           "clientInfo": {"name": "claude-ai", "version": "0.1.0"}}}))
        call = lambda mid, name, **given: srv.receive(json.dumps({"jsonrpc": "2.0", "id": mid, "method": "tools/call",
                                                                  "params": {"name": name, "arguments": given}}))["result"]
        shown = call(2, "turn_show", case="Juno", sheet=DEMO_SHEET, row=15)
        read_v = shown["structuredContent"]["turns"][0]["version"]
        check("192: turn_show gives each passage's version, in its words and its JSON",
              read_v == row_of(15)["v"] and f"Version: {read_v}" in shown["content"][0]["text"])
        idiograph_routes.api_commit({"path": str(book), "sheet": DEMO_SHEET, "row": 15, "en": "", "v": read_v,
                               "pairs": [{"es": "Changed in the app after the agent read it", "kq": ""}]})
        app_now = book.read_bytes()
        late = call(3, "turn_write", case="Juno", sheet=DEMO_SHEET, row=15, request="Code turn 15", version=read_v,
                    statements=["An agent's statement over words it has not seen"])
        check("192: the MCP server's write from an older version is refused, nothing written, the app's words kept",
              late["isError"] is True and late["content"][0]["text"].startswith(cli_line())
              and book.read_bytes() == app_now and row_of(15)["es"] == "Changed in the app after the agent read it")
        again = call(4, "turn_write", case="Juno", sheet=DEMO_SHEET, row=15, request="Code turn 15",
                     version=row_of(15)["v"], statements=["Changed in the app after the agent read it",
                                                          "An agent's statement, written once read"])
        check("192: and its write from the version as it is now goes through",
              again["isError"] is False
              and row_of(15)["es"] == "Changed in the app after the agent read it\nAn agent's statement, written once read")
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, locks.WAIT = kept

    # ── 4 and 5. the page: the focused field kept in view across a resize, a drag taken to whole words
    if not node:
        skip("192: the resize and the drag in the page", "no node on this machine")
        return

    def whole(name):
        at = app.index(f"function {name}(")
        return app[at:app.index("\n}", at) + 2]

    card_js = r"""
// the page's card over a refused save: Reload, Put my words back and Overwrite, the fields as drawTurn draws them
const els = {};
const $ = (id) => (els[id] = els[id] || { id, hidden: true, textContent: '', value: '', children: [],
  appendChild(c) { this.children.push(c); }, scrollIntoView() {},
  set textContent(v) { this._t = v; if (v === '') this.children = []; }, get textContent() { return this._t || ''; } });
const document = { createElement: () => ({ className: '', textContent: '', children: [], appendChild(c) { this.children.push(c); } }) };
const S = { stale: null, dirty: true };
const row = { key: 'Initial:15', v: 'old', es: '', en: '', kq: '', pairs: [{ es: '', kq: '' }], unpaired: false };
const current = () => row;
let fields = { pairs: [{ es: 'Typed here', kq: '"a walk"' }], en: 'A note typed here' };
const pairsNow = () => fields.pairs;
$('en').value = fields.en;
const draws = [];
// drawTurn fills the fields from the row and puts away a card that is not this passage's
function drawTurn() {
  if (!S.stale || S.stale.key !== row.key) hideStale();
  fields = { pairs: row.pairs.map((x) => ({ ...x })), en: row.en };
  $('en').value = row.en;
  draws.push(JSON.parse(JSON.stringify(fields)));
}
const drawAct = () => {};
const commits = [];
const commit = (r) => { commits.push({ v: r.v, fields: JSON.parse(JSON.stringify(fields)) }); };
""" + whole("showStale") + "\nconst STALE_LINE = 'line';\nconst STALE_RELOADED = 'reloaded';\n" + "\n".join(
        whole(n) for n in ("hideStale", "drawFieldsFrom", "staleReload", "staleBack", "staleOverwrite")) + r"""
const now = { es: 'Saved elsewhere', en: '', kq: '', pairs: [{ es: 'Saved elsewhere', kq: '' }], unpaired: false, v: 'new' };
const out = {};
showStale(row, now);
staleReload();
out.reload = { fields, dirty: S.dirty, v: row.v, rowEs: row.es, kept: $('stale-pairs').children.map((li) => li.children.map((c) => c.textContent)),
  notes: $('stale-notes').textContent, card: !$('stale').hidden, back: !$('stale-mine').hidden };
staleBack();
out.back = { fields, dirty: S.dirty, v: row.v, rowEs: row.es, card: !$('stale').hidden };
// a second refusal, and Overwrite this time
row.v = 'old';
showStale(row, now);
staleOverwrite();
out.overwrite = { commits, card: !$('stale').hidden };
console.log(JSON.stringify(out));
"""
    script = scratch / "a192-card.js"
    script.write_text(card_js, encoding="utf-8")
    done = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    got = json.loads(done.stdout) if done.returncode == 0 and done.stdout.strip() else {}
    mine = {"pairs": [{"es": "Typed here", "kq": "\"a walk\""}], "en": "A note typed here"}
    check("192: Reload loads the passage as it now is into the fields, its version taken, nothing left to save, and "
          "keeps what was typed under the line",
          got.get("reload", {}).get("fields") == {"pairs": [{"es": "Saved elsewhere", "kq": ""}], "en": ""}
          and got["reload"]["dirty"] is False and got["reload"]["v"] == "new" and got["reload"]["card"] is True
          and got["reload"]["back"] is True and got["reload"]["kept"] == [["Typed here", "\"a walk\""]]
          and got["reload"]["notes"] == "A note typed here", f"{got} {done.stderr[-300:]}")
    check("192: Put my words back brings what was typed into the fields again, to save, the passage's record left as "
          "it is saved",
          got.get("back", {}).get("fields") == mine and got["back"]["dirty"] is True and got["back"]["v"] == "new"
          and got["back"]["rowEs"] == "Saved elsewhere" and got["back"]["card"] is False, f"{got}")
    check("192: Overwrite saves what was typed over the change, from the version the refusal gave",
          got.get("overwrite", {}).get("commits") == [{"v": "new", "fields": mine}] and got["overwrite"]["card"] is False,
          f"{got}")

    resize_js = r"""
const SPEAKER_CLEAR = 24;
const work = { hidden: false };
// a column 600 tall whose field stands `fieldAt` down its content, and the content longer at a narrow width
const col = { scrollTop: 400, clientWidth: 900, clientHeight: 600, top: 100,
  getBoundingClientRect() { return { top: this.top, bottom: this.top + this.clientHeight }; },
  contains(el) { return el === field || el === turn; }, querySelector() { return turn; } };
let fieldAt = 700;
const field = { matches: () => true, getBoundingClientRect() { const t = col.top + fieldAt - col.scrollTop; return { top: t, bottom: t + 60, width: 200, height: 60 }; } };
const turn = { getBoundingClientRect() { const t = col.top + fieldAt - 40 - col.scrollTop; return { top: t, bottom: t + 400, width: 600, height: 400 }; } };
const document = { activeElement: field };
const $ = (id) => (id === 'work' ? work : col);
const VIEW = { el: null, at: 0, w: 0, h: 0 };
""" + whole("colRoom") + "\n" + whole("viewAnchor") + "\n" + whole("keepView") + r"""
viewAnchor();
const was = field.getBoundingClientRect().top;
// the window narrowed: the column narrower and the field 500px further down its content, the scroll as it was
col.clientWidth = 560; fieldAt = 1200;
const away = field.getBoundingClientRect().top;
keepView();
const narrow = field.getBoundingClientRect().top;
// a scroll of his own before the resize back, then wider again with the field where it was in the content
viewAnchor();
col.clientWidth = 900; fieldAt = 700;
keepView();
const back = field.getBoundingClientRect().top;
console.log(JSON.stringify({ was, away, narrow, back, lost: away > col.top + col.clientHeight }));
"""
    script = scratch / "a192-resize.js"
    script.write_text(resize_js, encoding="utf-8")
    done = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    got = json.loads(done.stdout) if done.returncode == 0 and done.stdout.strip() else {}
    check("192: narrowing the window while typing keeps the field holding the caret where it stood in the column, "
          "where it was pushed out of sight, and widening again keeps it there",
          got.get("lost") is True and got.get("narrow") == got.get("was") and got.get("back") == got.get("was"),
          f"{got} {done.stderr[-300:]}")

    # the way back's strip is no resize (wobble, 12 November 2026): the passage leaving sight brings Back to where I
    # was and the 44 pixels the column gives it, which the column's observer read as a new size, so keepView scrolled
    # the passage back and the wheel could not leave it, and a long passage's card flipped between held and free
    strip_js = r"""
const SPEAKER_CLEAR = 24;
const work = { hidden: false };
// a column 600 tall in its wrap, the passage 300 tall at 1,700 down its content, in sight at the start
const wrap = { clientHeight: 600 };
const col = { scrollTop: 1400, clientWidth: 900, clientHeight: 600, top: 100, parentElement: wrap,
  getBoundingClientRect() { return { top: this.top, bottom: this.top + this.clientHeight }; },
  contains(el) { return el === turn; }, querySelector() { return turn; } };
const turn = { getBoundingClientRect() { const t = col.top + 1700 - col.scrollTop; return { top: t, bottom: t + 300, width: 600, height: 300 }; } };
// a long passage's card and words for reachOf, the card beside the words
const pair = { querySelector: () => ({ getBoundingClientRect: () => ({ bottom: 300 }) }) };
const card = { getClientRects: () => [1], getBoundingClientRect: () => ({ left: 0, right: 300, top: 200 }),
  querySelector: (q) => (q === '.pair' ? pair : { offsetHeight: 50 }) };
const words = { getBoundingClientRect: () => ({ left: 340, right: 900, top: 230 }), scrollHeight: 490 };
const row = { querySelector: () => words, contains: () => true, getBoundingClientRect: () => ({ top: 200 }) };
const getComputedStyle = () => ({ lineHeight: '30px' });
const document = { activeElement: null };
const $ = (id) => (id === 'work' ? work : id === 'es-card' ? card : col);
const VIEW = { el: null, at: 0, w: 0, h: 0 };
""" + "\n".join(whole(n) for n in ("colRoom", "viewAnchor", "keepView", "reachOf")) + r"""
// the strip as the IntersectionObserver brings it, the passage out of the column's band 24 pixels in from each edge,
// and the column's observer running keepView whenever the column's box changes
let strips = 0;
const settle = () => {
  const b = turn.getBoundingClientRect();
  const box = col.getBoundingClientRect();
  const away = !(b.bottom > box.top + 24 && b.top < box.bottom - 24);
  const h = wrap.clientHeight - (away ? 44 : 0);
  if (h !== col.clientHeight) { col.clientHeight = h; strips += 1; keepView(); }
};
viewAnchor();
const free = reachOf(row).long;
// a hundred small turns of the wheel up, 10 pixels each, each scroll taken by viewAnchor as the page's listener takes it
for (let i = 0; i < 100; i += 1) { col.scrollTop -= 10; viewAnchor(); settle(); }
const up = 1400 - col.scrollTop;
// the long passage's measure with the strip there, as it stands now
col.clientHeight = wrap.clientHeight - 44;
const held = reachOf(row).long;
// and down past the passage the other way
col.scrollTop = 1400; settle(); viewAnchor();
for (let i = 0; i < 100; i += 1) { col.scrollTop += 10; viewAnchor(); settle(); }
const down = col.scrollTop - 1400;
// a real resize still keeps the passage where it stood
col.scrollTop = 1600; settle(); viewAnchor();
const at = turn.getBoundingClientRect().top;
wrap.clientHeight = 480; col.clientHeight = 480; col.clientWidth = 700; keepView();
console.log(JSON.stringify({ up, down, strips, free, held, kept: turn.getBoundingClientRect().top === at }));
"""
    script = scratch / "a192-strip.js"
    script.write_text(strip_js, encoding="utf-8")
    done = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    got = json.loads(done.stdout) if done.returncode == 0 and done.stdout.strip() else {}
    check("192: the wheel takes the column off the current passage both ways, the way back's strip coming as the "
          "passage leaves sight and recalling nothing, a long passage's card held or free alike with the strip, and a "
          "real resize still keeping the passage where it stood",
          got.get("up") == 1000 and got.get("down") == 1000 and got.get("strips", 0) >= 2
          and got.get("free") is False and got.get("held") is False and got.get("kept") is True,
          f"{got} {done.stderr[-300:]}")

    drag_js = r"""
// one passage's words as two text nodes, the second a key quote's mark, and drags cut inside words
const words = 'It is the same walk... Out of the door; left, "always" (every day).';
const nodes = [{ nodeValue: words.slice(0, 12) }, { nodeValue: words.slice(12) }];
const box = { textContent: words };
const document = { createTreeWalker() { let i = -1; return { nextNode: () => nodes[++i] || null }; } };
const NodeFilter = { SHOW_TEXT: 4 };
const at = (n, o) => nodes.slice(0, nodes.indexOf(n)).reduce((s, x) => s + x.nodeValue.length, 0) + o;
const place = (i) => { let pos = 0; for (const n of nodes) { if (i <= pos + n.nodeValue.length) return [n, i - pos]; pos += n.nodeValue.length; } };
// the live selection, its anchor where the drag began and its focus where the pointer is
let sel = null;
const select = (anchor, focus) => { const [an, ao] = place(anchor); const [fn, fo] = place(focus); sel = { an, ao, fn, fo }; };
const window = { getSelection: () => ({
  get anchorNode() { return sel.an; }, get anchorOffset() { return sel.ao; },
  get focusNode() { return sel.fn; }, get focusOffset() { return sel.fo; },
  getRangeAt() { const a = at(sel.an, sel.ao), f = at(sel.fn, sel.fo); const s = a <= f ? [sel.an, sel.ao] : [sel.fn, sel.fo];
    const e = a <= f ? [sel.fn, sel.fo] : [sel.an, sel.ao]; return { startContainer: s[0], startOffset: s[1], endContainer: e[0], endOffset: e[1] }; },
  setBaseAndExtent(an, ao, fn, fo) { sel = { an, ao, fn, fo }; },
}) };
const selectionTurns = () => { const a = at(sel.an, sel.ao), f = at(sel.fn, sel.fo); return [{ box, start: Math.min(a, f), end: Math.max(a, f) }]; };
""" + whole("snapWords") + "\n" + whole("boxPoint") + "\n" + whole("snapDrag") + r"""
const got = () => { const a = at(sel.an, sel.ao), f = at(sel.fn, sel.fo); return { text: words.slice(Math.min(a, f), Math.max(a, f)), back: f < a }; };
const out = {};
// down the passage, from inside "It" to inside "Out"
select(1, 25); out.cut = words.slice(1, 25); snapDrag(); out.down = got();
// back up it, from inside "door;" to inside "same", the anchor kept at the end it began
select(36, 11); snapDrag(); out.up = got();
// from inside "left," to inside "(every", the comma, quote marks and bracket going with their words
select(41, 58); snapDrag(); out.marks = got();
// whole words already, left as they are
select(0, 22); snapDrag(); out.whole = got();
console.log(JSON.stringify(out));
"""
    script = scratch / "a192-drag.js"
    script.write_text(drag_js, encoding="utf-8")
    done = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    got = json.loads(done.stdout) if done.returncode == 0 and done.stdout.strip() else {}
    check("192: a drag that starts and ends inside words takes them whole, the punctuation touching them with them, "
          "so a selection holds no part of a word, and a drag over whole words is left as it is",
          got.get("cut") == "t is the same walk... Ou"
          and got.get("down") == {"text": "It is the same walk... Out", "back": False}
          and got.get("up") == {"text": "same walk... Out of the door;", "back": True}
          and got.get("marks") == {"text": "left, \"always\" (every", "back": False}
          and got.get("whole") == {"text": "It is the same walk...", "back": False}, f"{got} {done.stderr[-300:]}")

def cli_line() -> str:
    import cli
    return idiograph_cli.STALE_WRITE
