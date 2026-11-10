"""Area 359: the quick keys on a thematic analysis project's Coding screen (quickkeysB, 9 November 2026, Adam's choice
of option B with A's keys). With words selected, R puts the code used last on them as a new extract, 1 to 5 that one
of the five codes used last, V makes them an in vivo code, a code named by the words themselves, and Q makes the
extract as ever. What is checked: the codes used last, the last one first, kept per project in its code list as a
passage's save puts codes on extracts and read back after a restart, a rename followed, the agents' ops
(`codes apply-last`, `codes in-vivo`, their route and MCP) writing the extract and its code, an in vivo code's name
trimmed of its stop, a code of that name on the list taken as it is spelled, a dry run writing nothing, and the
interviewer's passage, words the passage lacks and no code used yet refused, then on the page, in a real browser on
the app's own functions, what each key applies, nothing while a field has the caret, with Cmd or Ctrl, with no words
selected or in an IPA project, the menu's rows and keys, and the extract and code R and V make with one step of
undo. Every fixture is invented, the made-up house shared with a dog of area 316."""
from __future__ import annotations

import hashlib
import html as html_mod
import json
import subprocess
import tempfile
from pathlib import Path

import openpyxl

from . import support
from .support import check, skip
from .a316_code_list import NAMES, make_project, rows_of


def sha(path: Path) -> str:
    return hashlib.sha1(Path(path).read_bytes()).hexdigest()


def passages(book: Path) -> list[dict]:
    """The participant's passages of the workbook's first annotation sheet with words, as the workbook holds them."""
    import workbook as wb
    out = []
    w = openpyxl.load_workbook(book, rich_text=True)
    try:
        for ws in w.worksheets:
            cols = wb.detect_columns(ws)
            if "es" not in cols or "kq" not in cols:
                continue
            for r in range(2, ws.max_row + 1):
                name = str(ws.cell(r, cols["name"]).value or "").strip()
                text = wb.plain_text(ws.cell(r, cols["transcript"]).value)
                if name and name.lower() != "adam" and len(text.split()) > 12:
                    out.append({"sheet": ws.title, "row": r, "text": text, "name": name,
                                "pairs": wb.pairs_of(ws.cell(r, cols["es"]).value, ws.cell(r, cols["kq"]).value)})
            break
    finally:
        w.close()
    return out


def words_of(text: str, start: int, n: int) -> str:
    return " ".join(text.split()[start:start + n])


def whole(src: str, head: str) -> str:
    at = src.index(head)
    return src[at:src.index("\n}\n", at) + 3]


def line_of(src: str, start: str) -> str:
    return next(ln for ln in src.splitlines() if ln.startswith(start))


def test_quick_keys(scratch: Path):
    print("\n359. The quick keys on the Coding screen: the codes used last kept per project and after a restart, R, V "
          "and 1 to 5 for agents and on the page, nothing while a field has the caret (quickkeysB, 9 November)")
    import cli
    import codes
    import idiograph_routes as routes
    import mcp_server
    import server as server_mod
    from workbook import WorkbookError

    base = scratch / "quick-359"
    root, ipa = base / "Dogs", base / "Dogs IPA"
    make_project(root, "ta")
    make_project(ipa, "ipa")
    config_file = base / "config.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}, {"root": str(ipa)}], "interviewer": "Adam",
                                       "corpus": "", "gravity_reference": "", "corpus_exclude": [],
                                       "skip_permissions": False}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    book = {name: root / name / f"{name} - EN & ES.xlsx" for name in NAMES}

    def call(route: str, body: dict):
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = config_file, None, {"recent": []}
        try:
            with server_mod.scoped(route, body):
                return server_mod.ROUTES[route](body)
        finally:
            server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    def refused(route: str, body: dict) -> str:
        try:
            got = call(route, body)
        except WorkbookError as exc:
            return str(exc)
        return got.get("error", "") if isinstance(got, dict) else ""

    def answer(*args):
        code, out, err = cli.run(["--config", str(config_file), "--root", str(root), "--json", *args])
        got = support.plain(json.loads(out)) if out.strip() else {}
        return code, got, err + (got.get("error", "") if code else "")

    def recent() -> list:
        return call("/api/codes", {"root": str(root)})["recent"]

    def save(name: str, p: dict, pairs: list) -> dict:
        return call("/api/commit", {"path": str(book[name]), "sheet": p["sheet"], "row": p["row"], "pairs": pairs})

    try:
        # 1. no code used yet: the list made from the rows has none, and R is refused in plain words
        juno = passages(book["Juno"])
        check("359: a project's first read keeps no code used yet", recent() == [], json.dumps(recent()))
        bare = next(p for p in juno if not p["pairs"])
        said = refused("/api/codes-quick", {"root": str(root), "op": "last", "case": "Juno", "sheet": bare["sheet"],
                                            "row": bare["row"], "words": words_of(bare["text"], 0, 4)})
        check("359: R with no code used yet is refused, nothing written", said == "No code used yet.", said)

        # 2. the page's save puts codes on extracts: each becomes the code used last, the last one first
        coded = [p for p in juno if p["pairs"]]
        a, b = coded[0], coded[1]
        save("Juno", a, a["pairs"] + [{"es": "Smell of the lead", "kq": a["pairs"][0]["kq"]}])
        save("Juno", b, b["pairs"] + [{"es": "The kettle and the lead", "kq": b["pairs"][0]["kq"]},
                                      {"es": "Smell of the lead", "kq": b["pairs"][0]["kq"]}])
        first = recent()
        check("359: codes a passage's save puts on extracts are the codes used last, the last put on first",
              first[:2] == ["Smell of the lead", "The kettle and the lead"], json.dumps(first))
        save("Juno", a, a["pairs"] + [{"es": "Smell of the lead", "kq": a["pairs"][0]["kq"]}])
        check("359: a save that puts on no new code leaves the order as it was", recent() == first, json.dumps(recent()))

        # 3. R through the route: words of a passage with none, a new extract with the code used last
        words = words_of(bare["text"], 2, 5)
        before = sha(book["Juno"])
        dry = call("/api/codes-quick", {"root": str(root), "op": "last", "case": "Juno", "sheet": bare["sheet"],
                                        "row": bare["row"], "words": words, "dry_run": True})
        check("359: a dry run says what it would write and writes nothing", dry["dry_run"] is True
              and dry["code"] == "Smell of the lead" and sha(book["Juno"]) == before, json.dumps(dry)[:300])
        got = call("/api/codes-quick", {"root": str(root), "op": "last", "case": "Juno", "sheet": bare["sheet"],
                                        "row": bare["row"], "words": words, "note": "Code these with the last"})
        now = rows_of(book["Juno"])[(bare["sheet"], bare["row"])]
        check("359: R makes the words a new extract, in inverted commas, with the code used last on it",
              now == [{"es": "Smell of the lead", "kq": f'"{words}"'}] and got["recent"][0] == "Smell of the lead",
              json.dumps(now))
        hist = codes.load(root)["history"][-1]
        check("359: the code list's History says it, with his request", hist.get("note") == "Code these with the last"
              and hist["changes"][-1].startswith("Smell of the lead put on Juno's extract"), json.dumps(hist))

        # 4. 2 through the route: the second of the codes used last, which then comes first
        other = next(p for p in juno if not p["pairs"] and p["row"] != bare["row"])
        two = words_of(other["text"], 0, 3)
        got = call("/api/codes-quick", {"root": str(root), "op": "last", "n": 2, "case": "Juno", "sheet": other["sheet"],
                                        "row": other["row"], "words": two})
        check("359: 2 puts the second code used last on the words, and it is then the code used last",
              got["code"] == "The kettle and the lead" and got["recent"][:2] == ["The kettle and the lead", "Smell of the lead"],
              json.dumps(got.get("recent")))
        said = refused("/api/codes-quick", {"root": str(root), "op": "last", "case": "Juno", "sheet": other["sheet"],
                                            "row": other["row"], "words": two})
        check("359: the same code on the same words twice is refused", "already" in said, said)

        # 5. V: an in vivo code named by the words, trimmed of the stop at their end, joining the list
        rowan = passages(book["Rowan"])
        spot = next(p for p in rowan if not p["pairs"])
        sentence = spot["text"].split(".")[0].split()
        vivo_words = " ".join(sentence[-4:]) + "."
        got = call("/api/codes-quick", {"root": str(root), "op": "in-vivo", "case": "Rowan", "sheet": spot["sheet"],
                                        "row": spot["row"], "words": vivo_words})
        name = " ".join(sentence[-4:])
        check("359: V makes the words an extract and a code of their own, its name trimmed of the stop at their end",
              got["code"] == name and rows_of(book["Rowan"])[(spot["sheet"], spot["row"])] == [{"es": name, "kq": f'"{vivo_words}"'}]
              and any(c["name"] == name for c in codes.load(root)["codes"]) and got["recent"][0] == name, json.dumps(got)[:400])
        mabel = passages(book["Mabel"])
        spot2 = next(p for p in mabel if not p["pairs"])
        got = call("/api/codes-quick", {"root": str(root), "op": "in-vivo", "case": "Mabel", "sheet": spot2["sheet"],
                                        "row": spot2["row"], "words": words_of(spot2["text"], 0, 3)})
        check("359: an in vivo code on other words is a code of its own", got["code"] != name, json.dumps(got.get("code")))

        # 6. refusals: the interviewer's passage and words the passage lacks, nothing written
        import workbook as wb
        w = openpyxl.load_workbook(book["Juno"], read_only=True)
        ws = w.worksheets[0]
        cols = wb.detect_columns(ws)
        mine = next(r for r, v in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2)
                    if str(v[cols["name"] - 1] or "").strip() == "Adam" and len(str(v[cols["transcript"] - 1] or "").split()) > 3)
        adam_words = " ".join(str(ws.cell(mine, cols["transcript"]).value).split()[:3])
        sheet = ws.title
        w.close()
        before = sha(book["Juno"])
        said = refused("/api/codes-quick", {"root": str(root), "op": "last", "case": "Juno", "sheet": sheet, "row": mine,
                                            "words": adam_words})
        check("359: the interviewer's passage is refused", "interviewer" in said and sha(book["Juno"]) == before, said)
        said = refused("/api/codes-quick", {"root": str(root), "op": "in-vivo", "case": "Juno", "sheet": bare["sheet"],
                                            "row": bare["row"], "words": "a lighthouse keeper's lamp"})
        check("359: words the passage does not hold are refused", "does not hold" in said and sha(book["Juno"]) == before, said)

        # 7. kept across a restart: the code list read afresh, its rows forgotten, gives the same order
        order = recent()
        codes.ROWS.clear()
        on_disk = codes.listing(codes.load(root), codes.study_rows(routes.gets_books(root)))["recent"]
        check("359: the codes used last are kept in the project's code list and read back the same after a restart",
              on_disk == order and len(order) == 4, json.dumps([order, on_disk]))

        # 8. a rename follows them, a merge gives the merged one's place to the code that keeps its extracts
        view = call("/api/codes", {"root": str(root)})
        call("/api/codes-ops", {"root": str(root), "v": view["v"], "ops": [{"op": "rename", "code": "Smell of the lead",
                                                                            "name": "The lead's smell"}]})
        after = recent()
        check("359: a renamed code keeps its place among the codes used last under its new name",
              "The lead's smell" in after and "Smell of the lead" not in after
              and after.index("The lead's smell") == order.index("Smell of the lead"), json.dumps(after))

        # 9. the command line and MCP: codes apply-last and codes in-vivo, a dry run, a request asked for
        code, got, err = answer("codes", "apply-last", "Mabel", spot2["sheet"], str(spot2["row"]), "--words",
                                words_of(spot2["text"], 4, 3), "--recent", "3", "--dry-run")
        check("359: the command line's codes apply-last takes --recent and a dry run writes nothing",
              code == 0 and got.get("dry_run") is True and got.get("code") == after[2], err or json.dumps(got)[:300])
        code, got, err = answer("codes", "in-vivo", "Mabel", spot2["sheet"], str(spot2["row"]), "--words",
                                words_of(spot2["text"], 4, 3))
        check("359: a write from the command line asks for his request first", code != 0 and "--note" in err, err)
        code, got, err = answer("codes", "list")
        check("359: codes list gives the codes used last", code == 0 and got.get("recent") == after, err or json.dumps(got.get("recent")))
        srv = mcp_server.Server(str(root), config=str(config_file))
        tools = {t["name"]: t for t in mcp_server.tools_for("idiograph")}
        got = srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
            "name": "codes_in_vivo", "arguments": {"case": "Mabel", "sheet": spot2["sheet"], "row": spot2["row"],
                                                   "words": words_of(spot2["text"], 4, 3), "dry_run": True,
                                                   "request": "Code these words as they are"}}}))["result"]
        check("359: MCP has codes_apply_last and codes_in_vivo, each writing, and a dry run answers",
              {"codes_apply_last", "codes_in_vivo"} <= set(tools)
              and tools["codes_apply_last"]["annotations"]["readOnlyHint"] is False and not got.get("isError"),
              json.dumps(got)[:300])

        # 10. an IPA project has none of it
        said = refused("/api/codes-quick", {"root": str(ipa), "op": "last", "case": "Juno", "sheet": bare["sheet"],
                                            "row": bare["row"], "words": words})
        check("359: an IPA project refuses the quick keys' op", "IPA" in said, said)
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept

    page_checks(scratch)


PAGE = r"""
const out = {};
const key = (k, more = {}) => {
  const e = new KeyboardEvent('keydown', Object.assign({ key: k, bubbles: true, cancelable: true }, more));
  distilKeys(e);
  return e.defaultPrevented;
};
try {
  CX.recent = ['A gate left on the latch', 'Being pulled along', 'Dinner set by the bowl'];
  CX.codes = CX.recent.map((name) => ({ id: 'k', name, extracts: 1, participants: 1 }));
  // words selected: each key and what it asks commitQuote for
  window.PICKED = true;
  out.r = [key('r'), calls.pop()];
  out.R = [key('R'), calls.pop()];
  out.three = [key('3'), calls.pop()];
  out.v = [key('v'), calls.pop()];
  out.five = [key('5'), calls.length, said.pop()];
  out.six = [key('6'), calls.length];
  // with Cmd or Ctrl, the window's Reload and Paste, never a quick key
  out.cmdR = [key('r', { metaKey: true }), key('v', { ctrlKey: true }), calls.length];
  // the caret in a field: the key types there, nothing coded
  $('field').focus();
  out.field = [key('r'), key('1'), key('v'), calls.length];
  $('field').blur();
  // no words selected: nothing
  window.PICKED = false;
  out.none = [key('r'), key('2'), calls.length];
  // an IPA project: nothing
  window.PICKED = true;
  window.METHOD = 'ipa';
  out.ipa = [key('r'), key('v'), calls.length];
  window.METHOD = 'ta';
  // no code used yet: R says so and codes nothing
  const held = CX.recent;
  CX.recent = [];
  out.empty = [key('r'), calls.length, said.pop()];
  CX.recent = held;
  // a code put on here comes first, before the read that knows it
  cxUsed('Being pulled along');
  out.order = cxRecent();
  out.vivo = [cxVivoName('"she is walking me."'), cxVivoName('"... the gate, the latch!"')];
  // the menu's rows on words selected, each with its key
  const pick = { row: { i: 0, runs: [{ text: 'and she is walking me, really' }] }, start: 4, end: 21 };
  out.menu = cxQuickMenu(pick).map((g) => g.map((x) => x.head ? `[${x.head}]` : `${x.label}|${x.key}`));
  // R's and V's extract in a passage with none: the empty pair takes it, one step of undo puts it back
  window.REAL_COMMIT = true;
  window.QUOTE = '"she is walking me"';
  key('r');
  out.putR = pairsRead();
  out.undo = undone.length;
  undone[undone.length - 1].undo(undone[undone.length - 1]);
  out.afterUndo = pairsRead();
  window.QUOTE = '"Dinner set by the bowl."';
  key('v');
  out.putV = pairsRead();
  // the same words again with R: the extract there takes the code beside the one it has
  window.QUOTE = '"Dinner set by the bowl."';
  key('r');
  out.again = pairsRead();
} catch (err) { out.error = String(err && err.stack || err); }
document.getElementById('out').textContent = JSON.stringify(out);
"""

FIXTURE = """
<div id="work"></div><div id="pairs"><div class="pair" data-pid="p1"><input class="pair-es"><input class="pair-kq"></div></div>
<input type="text" id="field"><div id="transcript" tabindex="-1"></div><pre id="out">none</pre>
"""

STUBS = r"""
const $ = (id) => document.getElementById(id);
const MOD = (e) => e.metaKey || e.ctrlKey;
const REDO_Y = () => false;
const SEEK = () => false;
const APP = 'idiograph';
const S = { pending: [], data: { path: 'x' }, rowMenu: null, lastInput: {} };
const calls = [];
const said = [];
const undone = [];
const t = (k, v) => ({ 'codes.quick_none_used': 'No code used yet.', 'codes.quick.none_at': `No code is number ${v && v.n} yet.`,
  'page_idiograph.work.quote': 'Extract', 'codes.quick.last': 'Extract with the last code',
  'codes.quick.in_vivo_words': `In vivo code, "${v && v.words}"`, 'codes.quick.recent': 'Recent codes',
  'codes.has_it': `That extract has ${v && v.name} already.` }[k] || k);
const say = (s) => said.push(s);
const esc = (s) => s;
const escAttr = (s) => s;
const tMethodNow = () => window.METHOD || 'ta';
const selBarPick = () => (window.PICKED ? {} : null);
const current = () => ({ key: 'Initial|9', i: 0 });
const rowText = (row) => row.runs.map((r) => r.text).join('');
const clearPending = () => {};
const pairEls = () => [...document.querySelectorAll('#pairs .pair')];
const pairOf = (el) => ({ es: el.querySelector('.pair-es').value, kq: el.querySelector('.pair-kq').value });
const pairsChanged = () => {};
const undoPush = (e) => undone.push(e);
let pid = 1;
function insertPair(pair) {
  pid += 1;
  const el = document.createElement('div');
  el.className = 'pair';
  el.dataset.pid = `p${pid}`;
  el.innerHTML = '<input class="pair-es"><input class="pair-kq">';
  el.querySelector('.pair-es').value = pair.es;
  el.querySelector('.pair-kq').value = pair.kq;
  $('pairs').appendChild(el);
  return el;
}
const removePair = (el) => el.remove();
const pairsRead = () => pairEls().map((el) => [pairOf(el).es, pairOf(el).kq]);
function commitQuote(opts = {}) {
  if (window.REAL_COMMIT && (opts.code || opts.vivo)) { cxQuickPut(current(), window.QUOTE, opts); return; }
  calls.push(opts);
}
const nativeUndoOwns = () => false; const undoStep = () => {}; const pressAct = () => {}; const move = () => {};
const openFind = () => {}; const stepSheet = () => {}; const nudgeAudio = () => {}; const togglePlay = () => {};
const openEditor = () => {}; const assignKey = () => {}; const trimKey = () => {}; const openHelp = () => {};
const toggleGuide = () => {}; const minimapToggle = () => {}; const esStep = () => {};
const AUDIO_STEP = 5;
"""


def page_checks(scratch: Path) -> None:
    exe = support.browser()
    if exe is None:
        skip("359: the quick keys in a real browser", "no Chrome, Chromium, Brave or Edge on this computer")
        return
    distil = support.text("apps/idiograph/static/distil.js")
    codes_js = support.text("apps/idiograph/static/codes.js")
    parts = [
        STUBS,
        whole(distil, "function distilKeys("),
        line_of(codes_js, "const CX = "), line_of(codes_js, "const cxOn = "), line_of(codes_js, "const cxWords = "),
        line_of(codes_js, "const cdNorm = "),
        whole(codes_js, "function cxExtracts("), whole(codes_js, "function cxSet("), whole(codes_js, "function cxPairOut("),
        line_of(codes_js, "const CX_RECENT_MAX = "), line_of(codes_js, "const CX_STOPS = "), line_of(codes_js, "const cxShort = "),
        whole(codes_js, "function cxUsed("), whole(codes_js, "function cxRecent("), whole(codes_js, "function cxVivoName("),
        whole(codes_js, "function cxQuickPut("), whole(codes_js, "function cxQuickKey("), whole(codes_js, "function cxQuickMenu("),
    ]
    doc = ('<!doctype html><html><head><meta charset="utf-8"></head><body>' + FIXTURE + '<script>' + "\n".join(parts)
           + PAGE + "</script></body></html>")
    with tempfile.TemporaryDirectory(prefix="idiograph-359-") as tmp:
        page_file = Path(tmp) / "keys.html"
        page_file.write_text(doc, encoding="utf-8")
        cmd = [str(exe), "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
               "--disable-background-networking", "--disable-component-update", "--disable-sync", "--disable-default-apps",
               "--password-store=basic", "--use-mock-keychain", f"--user-data-dir={Path(tmp) / 'profile'}",
               "--window-size=1280,800", "--virtual-time-budget=3000", "--dump-dom", page_file.as_uri()]
        try:
            dumped = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=120).stdout
        except (OSError, subprocess.TimeoutExpired) as err:
            dumped = str(err)
    got = dumped.split('<pre id="out">', 1)[1].split("</pre>", 1)[0] if '<pre id="out">' in dumped else "{}"
    o = json.loads(html_mod.unescape(got)) if got.startswith("{") else {"said": got[:300]}
    last, second, third = "A gate left on the latch", "Being pulled along", "Dinner set by the bowl"
    check("359: with words selected, R and Shift R put the code used last on them, 3 the third, V an in vivo code",
          o.get("r") == [True, {"code": last}] and o.get("R") == [True, {"code": last}]
          and o.get("three") == [True, {"code": third}] and o.get("v") == [True, {"vivo": True}], str(o)[:600])
    check("359: a number past the codes used last says so and codes nothing, and 6 is no key",
          o.get("five") == [True, 0, "No code is number 5 yet."] and o.get("six") == [False, 0], str(o)[:600])
    check("359: nothing with Cmd or Ctrl, nothing while a field has the caret, nothing with no words selected and "
          "nothing in an IPA project", o.get("cmdR") == [False, False, 0] and o.get("field") == [False, False, False, 0]
          and o.get("none") == [False, False, 0] and o.get("ipa") == [False, False, 0], str(o)[:600])
    check("359: R with no code used yet says so and codes nothing", o.get("empty") == [True, 0, "No code used yet."], str(o)[:600])
    check("359: a code put on here is the code used last at once, before the project's list is read again",
          o.get("order") == [second, last, third], str(o)[:600])
    check("359: an in vivo code's name is the words, trimmed of the stop at their end and the dots at their start",
          o.get("vivo") == ["she is walking me", "the gate, the latch"], str(o)[:600])
    check("359: the right-click menu on words: Extract Q, Extract with the last code R, In vivo code with the words V, "
          "then Recent codes numbered 1 to 3",
          o.get("menu") == [["Extract|Q", "Extract with the last code|R", 'In vivo code, "she is walking me"|V'],
                            ["[Recent codes]", f"{second}|1", f"{last}|2", f"{third}|3"]], str(o)[:600])
    check("359: R in a passage with no extract fills its empty pair with the words and the code used last, one step of "
          "undo putting it back", o.get("putR") == [[second, '"she is walking me"']] and o.get("undo") == 1
          and o.get("afterUndo") == [["", ""]], str(o)[:600])
    check("359: V makes a new extract whose code is the words, and a code of that name on the list is taken as the list "
          "spells it, and R on the same words, whose extract has that code already, changes nothing",
          o.get("putV") == [[third, '"Dinner set by the bowl."']]
          and o.get("again") == [[third, '"Dinner set by the bowl."']], str(o)[:600])
