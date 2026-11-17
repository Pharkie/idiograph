"""Area 418: one behaviour for one function on every screen (sameux2, 17 November 2026, Adam: "yes make sure there is a
solid UX guidance", and the coordinator's rulings on exportnotice's audit). docs/design.md's Behaviour section names,
for each function, its one component and the one shared function every screen calls; this area holds the rules that
can be read from the page's code and the routes, and pins no words and no pixels.

What is checked. A: every control that deletes at once by an icon alone (a label's on every board, a sticky note's, a
trajectory's, a statement's pair) carries `.del-bin` and shows the bin, the boards' and Trajectories' glyph one and the
same, and none shows the cross; a worded delete carries `.btn-remove`. B: no control with the cross deletes: the cross
is never the bin, and the corner panels' crosses only shut and leave for later. C: no export's result reaches the line
at the foot: every function that ends in the export panel says nothing at the foot but a refusal before it. D: the
statements screen, the boards, Trajectories and the Code list each send a change made elsewhere to `outsideNotice`,
look on a focus and every few seconds, and the page holds one such panel; the boards' and the Code list's refused
saves go to `staleNotice`, the Code list no longer reloading silently. E: Nothing to undo is one catalogue key pair,
said through `sayNothingToUndo` on every screen, and no screen says a line after an Undo that did something. F: the
export notice shut by any way clears the boards' copy, so a board's Escape is never swallowed. G: Trajectories keeps
its Export menu's Include ticks for the session and waits no more than about ten seconds for a change in flight. H: a
sticky note deleted says Deleted with its Undo as a label does, and a code deleted on the Code list does too. I: the
stamp reads the Trajectories file's time and the code list's alone, a write through the app answers `outside` false and
one from outside it true, and reading writes nothing. J: docs/design.md has the Behaviour section and the Toast row no
longer says the foot line takes every line after an act."""
from __future__ import annotations

import json
import os
import re
import shutil
import time
from pathlib import Path

from . import support
from .support import check as said_check

BIN_PATH = "M4 7h16M9.5 7V4.5h5V7M6.5 7l.9 12.2a1.8 1.8 0 0 0 1.8 1.6h5.6a1.8 1.8 0 0 0 1.8-1.6L17.5 7M10.2 11v6M13.8 11v6"
CROSSES = ("M5 5l14 14M19 5L5 19", "M6 6l12 12M18 6L6 18")
# a cross that still takes a row out, left to its own build: none since sameux2b gave the import cards' and the names
# list's rows the bin
WAITING: dict = {}


def check(name, ok, detail=""):
    said_check(name, bool(ok), "" if ok else str(detail)[:700])


def fn(src: str, name: str) -> str:
    """A script's function by its name, its body to the closing brace at the line's start"""
    m = re.search(rf"\n(?:async )?function {name}\(", src)
    if not m:
        return ""
    end = src.find("\n}\n", m.end())
    return src[m.end():end]


def const(src: str, name: str) -> str:
    m = re.search(rf"\nconst {name} = '([^\n]*)';", src)
    return m.group(1) if m else ""


def functions(src: str):
    for m in re.finditer(r"\n(?:async )?function (\w+)\(", src):
        end = src.find("\n}\n", m.end())
        yield m.group(1), src[m.end():end]


def test_same_behaviour(scratch: Path):
    print("\n418. One behaviour for one function on every screen: the bin, the cross, the export panel, a change made "
          "elsewhere, a save refused, Nothing to undo (sameux2, 17 November)")
    static = "apps/idiograph/static/"
    distil, themes, traj, codes = (support.text(static + f) for f in ("distil.js", "themes.js", "trajectories.js", "codes.js"))
    shell = support.text("family/static/shell.js")
    page = support.page_text()
    css = support.text(static + "themes.css")
    scripts = {"distil.js": distil, "themes.js": themes, "trajectories.js": traj, "codes.js": codes}

    # ── A. the bin
    th_bin, tj_bin, np_bin = const(themes, "TH_DEL_ICON"), const(traj, "TJ_BIN"), const(distil, "NP_BIN")
    check("418: the boards' delete glyph, Trajectories' and the import cards' and names list's are one and the same "
          "bin, never the cross",
          th_bin and th_bin == tj_bin == np_bin and BIN_PATH in th_bin and not any(c in th_bin for c in CROSSES), th_bin[:200])
    icon_deletes = {
        "a label's bin": (themes, r'class="th-del[ "][^>]*>\$\{TH_DEL_ICON\}'),
        "a sticky note's bin": (themes, r'class="th-sticky-del[ "][^>]*>\$\{TH_DEL_ICON\}'),
        "a trajectory's bin": (traj, r'class="tj-remove tf-bin[ "][\s\S]{0,400}?\$\{TJ_BIN\}'),
        "a statement's pair bin": (distil, r'class="pair-remove[ "][\s\S]{0,900}?</svg>'),
        "an import card's and the names list's row bin": (distil, r'class="np-remove[ "][^>]*>\$\{NP_BIN\}'),
    }
    found = {}
    for what, (src, pat) in icon_deletes.items():
        m = re.search(pat, src)
        found[what] = bool(m) and "del-bin" in m.group(0) and not any(c in m.group(0) for c in CROSSES)
    check("418: every control that deletes at once by an icon alone carries .del-bin and shows a bin, never the cross",
          all(found.values()), found)
    # any button the scripts or the page draw whose class names a delete by an icon (…-del, …-remove, …-bin) carries
    # .del-bin or .btn-remove
    loose = []
    for name, src in list(scripts.items()) + [("page", page)]:
        for m in re.finditer(r'<button\b[^>]*\bclass="([^"]*)"', src):
            classes = m.group(1).split()
            if any(re.search(r"-(del|remove|bin)$", c) for c in classes) and not {"del-bin", "btn-remove"} & set(classes) \
                    and not set(classes) & set(WAITING):
                loose.append(f"{name}: {m.group(1)}")
    check("418: no button whose class names a delete is without .del-bin or .btn-remove, but those waiting on their "
          "own build (WAITING)", not loose and not WAITING, loose)
    check("418: the Code list's Delete this code is a worded delete, .btn-remove",
          'class="ghost small btn-remove" data-act="delete"' in codes)
    check("418: .del-bin is the danger red under the pointer and in focus", ".del-bin:is(:hover, :focus-visible) { color: var(--danger); }" in css)

    # ── B. the cross closes and never deletes
    close_ids = re.findall(r'<button class="card-close[^"]*" id="([^"]+)"', page)
    crossing_deletes = [i for i in close_ids if re.search(r"(del|remove|bin)", i)]
    out_close = distil.split("$('th-outside-close').onclick = () => {", 1)[1].split("\n  };", 1)[0] if "$('th-outside-close').onclick" in distil else ""
    check("418: the cross on every card and panel is a close: none is named for a delete, and the corner panels' "
          "crosses only shut and leave the change for later",
          close_ids and not crossing_deletes and "outsideNotice(null, cornerOwner(info))" in out_close
          and not re.search(r"(delete|remove|Delete|Remove)", out_close)
          and "$('export-done-close').onclick = () => exportNotice(null);" in distil, (close_ids[:5], crossing_deletes, out_close))

    # ── C. no export's result at the foot
    leaks = {}
    ends = 0
    for name, src in scripts.items():
        for f, body in functions(src):
            if f in ("exportNotice", "exportFailed", "thExported", "exportNoticeWire", "outsideNotice", "staleNotice"):
                continue
            if not re.search(r"\b(exportNotice|thExported|exportFailed)\(", body):
                continue
            if not re.search(r"api\(|window\.open\(", body):
                continue
            ends += 1
            for said in re.findall(r"\bsay\(([^;]*)", body):
                if not re.search(r"t\('themes\.(print\.blocked|no_notes|unsaved\.stays_open)'\)|TH_NO_PASSAGE", said):
                    leaks.setdefault(f"{name} {f}", []).append(said)
    check("418: every export ends in the export panel and none says its result at the foot, only a refusal before it",
          ends >= 8 and not leaks, (ends, leaks))

    # ── D. a change made elsewhere and a save refused, the shared panels
    elsewhere = {"boards": fn(themes, "thOutside"), "statements": fn(distil, "esStampTick"),
                 "trajectories": fn(traj, "trajStampTick"), "code list": fn(codes, "codesStampTick")}
    check("418: every screen's change made elsewhere goes to the one shared panel, outsideNotice",
          all("outsideNotice(" in b for b in elsewhere.values()), {k: "outsideNotice(" in b for k, b in elsewhere.items()})
    check("418: Trajectories and the Code list read the stamp of their own file, on a focus and every few seconds",
          "api('/api/stamp', { workbook: path, of: 'trajectories' })" in elsewhere["trajectories"]
          and "api('/api/stamp', { workbook: path, of: 'codes' })" in elsewhere["code list"]
          and "window.addEventListener('focus', () => trajStampTick());" in fn(traj, "trajWire")
          and "setInterval(() => trajStampTick(), 4 * 1000);" in fn(traj, "trajWire")
          and "window.addEventListener('focus', () => codesStampTick());" in fn(codes, "codesWire")
          and "setInterval(() => codesStampTick(), 4 * 1000);" in fn(codes, "codesWire"))
    check("418: the page holds one change-made-elsewhere panel and one refused-save panel, outside every screen, and "
          "the statements screen's own line is gone",
          page.count('id="th-outside"') == 1 and page.count('id="th-stale"') == 1 and 'id="es-outside"' not in page
          and page.index('id="th-outside"') > page.index('id="export-done"') - 2000
          and "es-outside" not in distil and "$('th-outside')" not in themes and "$('th-stale')" not in themes)
    stale_codes = fn(codes, "codesOpsNow")
    check("418: a refused save goes to the one shared panel, staleNotice, on the boards and the Code list, and the "
          "Code list's refusal is no silent reload",
          "staleNotice(" in fn(themes, "thStaleDraw") and "staleNotice(null)" in fn(themes, "thStaleHide")
          and "codesStale();" in stale_codes and "staleNotice({ owner: 'codes'" in fn(codes, "codesStale")
          and "if (err.data && err.data.stale) await codesReload();" not in stale_codes
          and "codesOverwrite()" in fn(codes, "codesStale"))

    # ── E. Nothing to undo, one key; no line after an Undo
    nothing = fn(distil, "sayNothingToUndo")
    keys_used = {name: set(re.findall(r"t\('([\w.]*(?:nothing|no_redo|undo\.none)[\w.]*)'\)", src)) for name, src in scripts.items()}
    undo_keys = {k for ks in keys_used.values() for k in ks if re.search(r"undo|redo", k)}
    check("418: Nothing to undo is one key pair said by one function, and every screen's Undo calls it",
          "t('themes.undo.nothing')" in nothing and "t('themes.undo.nothing_redo')" in nothing and ", 2000)" in nothing
          and undo_keys <= {"themes.undo.nothing", "themes.undo.nothing_redo"}
          and all("sayNothingToUndo(" in b for b in (fn(distil, "undoStep"), fn(traj, "trajUndo"), fn(codes, "codesUndo")))
          and "sayNothingToUndo(backwards)" in themes, undo_keys)
    cat = json.loads(support.text("apps/idiograph/static/i18n/en/distil.json"))
    check("418: no line after an Undo that did something: the Code list's and the statements screen's lines are gone",
          "data.changes" not in fn(codes, "codesUndo") and "say(" not in fn(distil, "pairPut") and "say(" not in fn(distil, "quotePut")
          and not [k for k in cat if k in ("distil.undo.none", "distil.undo.no_redo", "distil.undo.quote_back",
                                           "distil.undo.statement_back")])

    # ── F. the export notice shut clears the boards' copy
    notice = fn(distil, "exportNotice")
    check("418: any notice shown or shut clears the boards' TH.exported, and a board's own sets it after, so a board's "
          "Escape is never swallowed by a notice already gone",
          "TH.exported = null" in notice.split("if (!info) {", 1)[0]
          and fn(themes, "thExported").index("exportNotice({") < fn(themes, "thExported").index("TH.exported = info;"))

    # ── G. Trajectories' Export menu
    xmenu, xgo = fn(traj, "trajXmenu"), fn(traj, "trajExportGo")
    check("418: Trajectories keeps its Include ticks for the session and gives up after about ten seconds of a change "
          "in flight, as its Undo does",
          ".checked = false" not in xmenu and "await trajIdle(250);" in xgo
          and xgo.index("await trajIdle(250);") < xgo.index("if (TJ.busy) {") < xgo.index("api(TJ_EXPORT"))

    # ── H. a sticky note's and a code's delete say so with Undo
    check("418: a sticky note deleted shows the Deleted notice with its Undo, as a label does, and a code deleted too",
          "thDeletedSay([], live, true);" in fn(themes, "thStickyDelete")
          and "sayUndo(t('themes.deleted_stickies'" in fn(themes, "thDeletedSay")
          and "sayUndo(t('codes.deleted_code'" in fn(codes, "codesDelete")
          and "unsayUndo()" in fn(codes, "codesSend"))

    # ── sameux2b: the Code list's notice, its refused changes, Trajectories' export given up, the panel's words
    tick, undo = fn(codes, "codesStampTick"), fn(codes, "codesUndo")
    check("418: the Code list's delete notice is withdrawn by a change from elsewhere, and its Undo sends the version "
          "the screen read",
          tick.index("unsayUndo()") < tick.index("outsideNotice(") and "v: CD.data && CD.data.v" in undo
          and "$('th-stale-over').hidden = !info.overwrite;" in fn(distil, "cornerSync"))
    # what the Code list does with a refused Undo and with the changes held behind a refused change is run in node (K)
    held_checks(scratch)
    check("418: Trajectories' export given up after its wait says so in the export panel",
          "if (TJ.busy) { exportFailed(null, t('trajectories.export_still_saving')); return; }" in fn(traj, "trajExportGo"))
    on = fn(distil, "cornerSync")
    callers = [fn(themes, "thOutside"), fn(distil, "esStampTick"), fn(traj, "trajStampTick"), fn(codes, "codesStampTick")]
    check("418: the change-made-elsewhere panel has the boards' heading on every screen, each screen's line under it, "
          "Update by default and Show it only where it takes him to something new",
          "$('th-outside-line').textContent = t('themes.outside.elsewhere');" in on
          and "info.word || t('themes.outside.update')" in on and 'id="th-outside-said"' in page
          and all("line: t('themes.outside.elsewhere')" not in c for c in callers)
          and "line: t('trajectories.outside_changed')" in callers[2] and "line: t('codes.outside_changed')" in callers[3]
          and "word: t('themes.outside.show')" in callers[1])

    # ── I. the stamp's Trajectories and code list reads
    stamp_checks(scratch)

    # ── J. the guidance
    doc = support.text("docs/design.md")
    behaviour = doc.split("## Behaviour", 1)[1].split("\n## ", 1)[0] if "## Behaviour" in doc else ""
    rows = [r for r in behaviour.splitlines() if r.startswith("| ") and not r.startswith("| Function") and not r.startswith("| Kind")]
    toast = next((r for r in doc.splitlines() if r.startswith("| Toast |")), "")
    named = ("exportNotice", "sayUndo", "unsayUndo", "sayNothingToUndo", "outsideNotice", "staleNotice", ".del-bin")
    check("418: docs/design.md has the Behaviour section, a row for each function naming its shared function, and the "
          "Toast row says which lines are not the foot's",
          len(rows) >= 20 and all(n in behaviour for n in named) and "corner panels" in toast
          and all(f"function {n}(" in distil + shell for n in named if not n.startswith(".")), (len(rows), toast[:200]))
    design = support.page_text("family/static/design.html")
    check("418: the /design page shows the Behaviour section from the app's classes",
          "Behaviour</h3>" in design and "th-outside" in design and "th-stale" in design and "del-bin" in design
          and "toast-undo" in design)


def stamp_checks(scratch: Path):
    import agent_log
    import codes as codes_mod
    import idiograph_routes as routes
    import server as server_mod
    import trajectories as traj_mod
    from .a316_code_list import make_project
    from .a394_lipa_demo import as_cloned

    def listing(root: Path) -> dict:
        return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}

    # Trajectories, on a scratch copy of the longitudinal demo
    fresh = scratch / "stamp-418-clone"
    shutil.rmtree(fresh, ignore_errors=True)
    shutil.copytree(support.source("demo"), fresh, ignore=as_cloned)
    kept = (server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO, os.environ.get(agent_log.PLACE), server_mod.CONFIG_PATH)
    cfg = scratch / "stamp-418-config.json"
    base = {"interviewer": "Interviewer", "corpus": "", "gravity_reference": "", "corpus_exclude": []}
    cfg.write_text(json.dumps(dict(base, projects=[])), encoding="utf-8")
    try:
        server_mod.DEMO_DIR = server_mod.SHIPPED_DEMO = fresh
        os.environ[agent_log.PLACE] = str(scratch / "stamp-418-agent-log.json")
        demo = server_mod.demo_lipa_dir()
        routes.fill_demo()
        root = scratch / "stamp-418-allotment"
        shutil.rmtree(root, ignore_errors=True)
        shutil.copytree(demo, root, ignore=shutil.ignore_patterns("pristine", "source"))
        cfg.write_text(json.dumps(dict(base, projects=[{"root": str(root)}])), encoding="utf-8")
        server_mod.CONFIG_PATH = cfg
        book = str(next(root.glob("Arlo/Arlo - *.xlsx")))

        def call(route: str, body: dict) -> dict:
            with routes.route_scope(route, body):
                return server_mod.ROUTES[route](body)

        view = call("/api/trajectories", {"workbook": book})
        before = listing(root)
        first = call("/api/stamp", {"workbook": book, "of": "trajectories"})
        check("418: the stamp reads the Trajectories file's time alone, as the board has it, and writes nothing",
              first.get("file") == "trajectories" and first.get("updated") == view.get("updated")
              and set(first) == {"file", "updated", "outside"} and listing(root) == before, first)
        col = (view.get("columns") or [{}])[0].get("id")
        made = call("/api/trajectories-ops", {"workbook": book, "ops": [{"op": "rename", "column": col, "title": "Rising again"}],
                                              "step": True})
        own = call("/api/stamp", {"workbook": book, "of": "trajectories"})
        check("418: after the app's own change the stamp gives its new time and says it was not made outside",
              own.get("updated") == made.get("updated") and own.get("outside") is False, (own, made.get("updated")))
        held = traj_mod.path_of(root)
        data = json.loads(held.read_text(encoding="utf-8"))
        data["updated"] = "2099-01-01T00:00:00"
        time.sleep(0.01)
        held.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        far = call("/api/stamp", {"workbook": book, "of": "trajectories"})
        check("418: a change to the Trajectories file from outside the app gives its time and outside true",
              far.get("updated") == "2099-01-01T00:00:00" and far.get("outside") is True, far)
    finally:
        server_mod.DEMO_DIR, server_mod.SHIPPED_DEMO = kept[0], kept[1]
        if kept[2] is None:
            os.environ.pop(agent_log.PLACE, None)
        else:
            os.environ[agent_log.PLACE] = kept[2]
        server_mod.CONFIG_PATH = kept[3]

    # the code list, on a small thematic analysis project of the suite's own
    base_dir = scratch / "stamp-418-codes"
    shutil.rmtree(base_dir, ignore_errors=True)
    troot = base_dir / "Dogs"
    make_project(troot, "ta")
    config_file = base_dir / "config.json"
    config_file.write_text(json.dumps(dict(base, projects=[{"root": str(troot)}], skip_permissions=False)), encoding="utf-8")
    keep = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)

    def tcall(route: str, body: dict):
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = config_file, None, {"recent": []}
        try:
            with server_mod.scoped(route, body):
                return server_mod.ROUTES[route](body)
        finally:
            server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = keep

    view = tcall("/api/codes", {"root": str(troot)})
    made = tcall("/api/codes-ops", {"root": str(troot), "ops": [{"op": "new", "name": "Waiting at the gate"}]})
    before = listing(troot)
    own = tcall("/api/stamp", {"root": str(troot), "of": "codes"})
    check("418: the stamp reads the code list's time alone, the app's own change not made outside, and writes nothing",
          own.get("file") == "codes" and own.get("updated") == made.get("updated") and own.get("outside") is False
          and listing(troot) == before and view.get("updated") is not None, (own, made.get("updated")))
    held = codes_mod.path_of(troot)
    data = json.loads(held.read_text(encoding="utf-8"))
    data["updated"] = "2099-01-01T00:00:00"
    time.sleep(0.01)
    held.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    far = tcall("/api/stamp", {"root": str(troot), "of": "codes"})
    check("418: a change to the code list from outside the app gives its time and outside true",
          far.get("updated") == "2099-01-01T00:00:00" and far.get("outside") is True, far)

    # M1 (sameux2b): the page's Undo takes the step it showed or none. A code deleted on the page, an agent's rename
    # after it, then the delete's notice's Undo with the version the page read: refused, nothing written, the agent's
    # rename kept and the code still gone
    tcall("/api/codes-ops", {"root": str(troot), "ops": [{"op": "new", "name": "Gate at dusk"}]})
    gone = tcall("/api/codes-ops", {"root": str(troot), "ops": [{"op": "delete", "code": "Gate at dusk"}]})
    first = (gone.get("codes") or [{}])[0]
    agent = tcall("/api/codes-ops", {"root": str(troot), "ops": [{"op": "rename", "code": first.get("id"),
                                                                    "name": "Renamed by an agent"}]})
    before = listing(troot)
    refused = tcall("/api/codes-undo", {"root": str(troot), "v": gone.get("v")})
    names = [c["name"] for c in tcall("/api/codes", {"root": str(troot)}).get("codes") or []]
    check("418: an Undo sent with the version the page read is refused once the list changed since, with nothing "
          "written, the agent's change kept and the delete standing",
          refused.get("stale") is True and refused.get("status") == 409 and listing(troot) == before
          and "Renamed by an agent" in names and "Gate at dusk" not in names and agent.get("v") != gone.get("v"),
          (refused, names[:4]))
    redone = tcall("/api/codes-undo", {"root": str(troot), "redo": True, "v": gone.get("v")})
    check("418: Redo is held to the version the same way", redone.get("stale") is True and listing(troot) == before, redone)
    own = tcall("/api/codes-undo", {"root": str(troot), "v": agent.get("v")})
    names = [c["name"] for c in own.get("codes") or []]
    check("418: with the version as it now stands the Undo takes the step on top, the rename",
          not own.get("stale") and first.get("name") in names and "Renamed by an agent" not in names, names[:4])


# ── K. the Code list's held changes, run in node with codes.js and distil.js's corner panels against the server's own
# routes on scratch copies of the thematic analysis demo (codesheld and codesheld2, 17 November 2026)
HELD_ROUTE = r"""
import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import boot
boot.setup()
import server as server_mod
import idiograph_routes
asked = json.loads(sys.stdin.read())
server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = Path(sys.argv[2]), None, {"recent": []}
try:
    with server_mod.scoped(asked["route"], asked["body"]):
        out = server_mod.ROUTES[asked["route"]](asked["body"])
except Exception as exc:  # a refusal, which the server answers with its words
    out = {"error": str(exc)}
print(json.dumps(out))
"""

HELD_RUN = r"""
const { execFileSync } = require('child_process');
const ELS = {};
class El {
  constructor(id) { this.id = id; this.hidden = false; this.shown = false; this.value = ''; this.textContent = ''; this.innerHTML = '';
    this.style = {}; this.classList = { toggle() {}, add() {}, remove() {}, contains: () => false }; }
  addEventListener() {}
  querySelector() { return null; }
  querySelectorAll() { return []; }
  contains() { return false; }
  focus() {}
}
const $ = (id) => (ELS[id] = ELS[id] || new El(id));
globalThis.document = { readyState: 'loading', addEventListener() {}, activeElement: null, hidden: false,
  documentElement: { dataset: {}, setAttribute() {}, lang: 'en' } };
globalThis.window = { addEventListener() {} };
const esc = (s) => String(s);
const escAttr = (s) => String(s);
const RESTART_LINE = 'Restart';
const needsRestart = () => false;
const pathProjectDraw = () => {};
const dsTabsDraw = () => {};
const SAID = [];
const say = (words) => SAID.push(String(words));
const sayUndo = (words) => SAID.push(String(words));
const unsayUndo = () => {};
const sayNothingToUndo = () => SAID.push('nothing');
// the screens' hosts: the Code list's and a board's, one in front at a time
const exportShown = (el) => !!el && !!el.shown;
const exportHost = () => ['th-stage', 'cd-body'].map((id) => $(id)).find((el) => el.shown) || null;
const cornerPlace = () => {};
const XN = { info: null };
const exportNotice = () => {};
const front = (id) => { for (const h of ['th-stage', 'cd-body']) $(h).shown = h === id; cornerSync(); };
// distil.js's corner panels themselves
__CORNERS__
// the server: the routes themselves on the scratch copies, one process a call; FAIL_NEXT a call that never reaches it
let FAIL_NEXT = false;
const serve = (route, body) => JSON.parse(execFileSync(process.env.HD_PY, [process.env.HD_ROUTE, process.env.HD_REPO, process.env.HD_CFG],
  { input: JSON.stringify({ route, body }), encoding: 'utf8' }));
async function api(route, body) {
  await new Promise((r) => setImmediate(r));
  if (FAIL_NEXT && route === '/api/codes-ops') { FAIL_NEXT = false; throw new TypeError('Load failed'); }
  const data = serve(route, body);
  if (data.error) { const err = new Error(data.error); err.data = data; err.code = data.code || ''; throw err; }
  return data;
}
__CODES__
codesDraw = () => {};
const BOOK = process.env.HD_BOOK;
const OTHER = process.env.HD_OTHER;
const names = () => serve('/api/codes', { workbook: BOOK }).codes.map((c) => c.name);
const panel = () => (XS.info ? { line: XS.info.line, overwrite: !!XS.info.overwrite, codes: !!XS.info.codes } : null);
const shown = () => !$('th-stale').hidden;
(async () => {
  const out = {};
  front('cd-body');
  await codesOpen(BOOK);
  const first = CD.data.codes[0];
  out.first = first.name;
  // L1: his change, an agent's after it, his Undo refused; then a change of his, which must be written
  await codesOps([{ op: 'new', name: 'Waiting at the door' }]);
  serve('/api/codes-ops', { workbook: BOOK, ops: [{ op: 'new', name: 'Made by an agent' }] });
  SAID.length = 0;
  await codesUndo(false);
  const undone = { said: SAID.slice(), panel: panel(), v: CD.data.v === serve('/api/codes', { workbook: BOOK }).v };
  await codesOps([{ op: 'new', name: 'After the refused Undo' }]);
  out.undo = Object.assign(undone, { held: CD.held.length, names: names() });
  // L2: an agent's change, then his, refused; a rename held behind it that the server will refuse (the agent's name),
  // and a third held
  serve('/api/codes-ops', { workbook: BOOK, ops: [{ op: 'new', name: 'Taken by an agent' }] });
  await codesOps([{ op: 'new', name: 'Refused at first' }]);
  const refused = panel();
  await codesOps([{ op: 'rename', code: first.id, name: 'Taken by an agent' }]);
  await codesOps([{ op: 'new', name: 'Third in line' }]);
  const held = CD.held.length;
  SAID.length = 0;
  await codesUndo(false);
  const undoWaits = { said: SAID.slice(), panel: panel(), held: CD.held.length };
  await XS.info.overwrite();
  out.over = { refused, held, undoWaits, panel: panel(), left: CD.held.map((ops) => ops.map((o) => o.name)), names: names() };
  await XS.info.overwrite();
  out.again = { panel: panel(), left: CD.held.length, names: names() };
  // the refused one last: nothing left, the panel shut and the server's sentence at the foot
  serve('/api/codes-ops', { workbook: BOOK, ops: [{ op: 'new', name: 'Another by an agent' }] });
  await codesOps([{ op: 'new', name: 'Fourth' }]);
  await codesOps([{ op: 'new', name: 'Another by an agent' }]);
  SAID.length = 0;
  await XS.info.overwrite();
  out.last = { panel: panel(), left: CD.held.length, said: SAID.slice(), names: names() };

  // H1 (codesheld2): a refused change and one held; the Themes board opens (its load shuts its own panel) and a
  // board's save is refused there; back on the Code list his panel is back, Overwrite sends what waited, and the
  // board's panel is never shut by the Code list's
  serve('/api/codes-ops', { workbook: BOOK, ops: [{ op: 'new', name: 'An agent before the board' }] });
  await codesOps([{ op: 'new', name: 'Held over the board' }]);
  await codesOps([{ op: 'new', name: 'Held behind it' }]);
  front('th-stage');
  staleNotice(null);
  const onBoard = { panel: panel(), shown: shown(), held: CD.held.length };
  staleNotice({ line: 'board refused', reload() {}, overwrite() {} });
  const boardOwn = panel();
  front('cd-body');
  await codesOpen(BOOK);
  const back = panel();
  await XS.info.overwrite();
  const after = { panel: panel(), left: CD.held.length, names: names(), board: !!XS.by.board };
  front('th-stage');
  out.board = { onBoard, boardOwn, back, after, boardStill: panel() };
  staleNotice(null);
  front('cd-body');

  // L3 and L2 of the second review: a change made while another is on the way waits and is written; an Undo while
  // Overwrite sends says so; a change that never reached the server still waits, and the line says so
  const a = codesOps([{ op: 'new', name: 'Made first' }]);
  const b = codesOps([{ op: 'new', name: 'Made while busy' }]);
  await Promise.all([a, b]);
  out.busy = { names: names() };
  serve('/api/codes-ops', { workbook: BOOK, ops: [{ op: 'new', name: 'An agent once more' }] });
  await codesOps([{ op: 'new', name: 'Not sent' }]);
  FAIL_NEXT = true;
  SAID.length = 0;
  const sending = XS.info.overwrite();
  await codesUndo(false);
  const undoSaid = SAID.slice();
  await sending;
  out.unsent = { undoSaid, panel: panel(), left: CD.held.length };

  // M1: another project's list opened with changes waiting says so in one line and drops them
  SAID.length = 0;
  await codesOpen(OTHER);
  out.other = { said: SAID.slice(), panel: panel(), left: CD.held.length, names: names() };

  // codesheld3: changes made while a call is on the way are sent in the order he made them, one queue, so two renames
  // of one code leave the later name
  const named = () => serve('/api/codes', { workbook: OTHER }).codes.map((c) => c.name);
  const one = CD.data.codes[0];
  const sent = [codesOps([{ op: 'new', name: 'Busy start' }]),
    codesOps([{ op: 'rename', code: one.id, name: 'Order one' }]),
    codesOps([{ op: 'rename', code: one.id, name: 'Order two' }]),
    codesOps([{ op: 'new', name: 'Order three' }])];
  const waited = CD.waiting.length;
  await Promise.all(sent);
  const after3 = named();
  out.order = { waited, names: after3, last: after3.includes('Order two') && !after3.includes('Order one') && after3.includes('Order three') };
  // and a change waiting on a call in flight when another project's list opens is counted in its line
  SAID.length = 0;
  const flying = codesOps([{ op: 'new', name: 'In flight' }]);
  const queued = codesOps([{ op: 'new', name: 'Queued behind it' }]);
  const queuedNow = CD.waiting.length;
  await codesOpen(BOOK);
  await Promise.all([flying, queued]);
  await new Promise((r) => setTimeout(r, 20));
  out.waitDrop = { queuedNow, said: SAID.slice(), waiting: CD.waiting.length, names: named() };
  process.stdout.write(JSON.stringify(out));
})().catch((e) => { console.error(e.stack); process.exit(1); });
"""


def held_checks(scratch: Path):
    import subprocess
    import sys

    import server as server_mod

    if not shutil.which("node"):
        support.skip("418: the Code list's held changes in node", "no node on this machine")
        return
    base_dir = scratch / "held-418"
    shutil.rmtree(base_dir, ignore_errors=True)
    root, other = base_dir / "Dogs coded", base_dir / "Dogs again"
    for r in (root, other):
        shutil.copytree(server_mod.demo_ta_dir(), r, ignore=shutil.ignore_patterns("pristine", "source"))
    cfg = base_dir / "config.json"
    cfg.write_text(json.dumps({"projects": [{"root": str(root)}, {"root": str(other)}], "interviewer": "", "corpus": "",
                               "gravity_reference": "", "corpus_exclude": [], "skip_permissions": False}), encoding="utf-8")
    route = base_dir / "route.py"
    route.write_text(HELD_ROUTE, encoding="utf-8")
    book, book2 = sorted(root.glob("*/*.xlsx"))[0], sorted(other.glob("*/*.xlsx"))[0]
    distil = support.text("apps/idiograph/static/distil.js")
    start, end = distil.find("\nconst XO = {"), distil.find("\nfunction cornerWire(")
    corners = distil[start:end] if 0 < start < end else ""
    check("418: distil.js's corner panels are found for the run", corners)
    path = base_dir / "held-418.js"
    path.write_text(support.i18n_js() + HELD_RUN.replace("__CORNERS__", corners)
                    .replace("__CODES__", support.text("apps/idiograph/static/codes.js")), encoding="utf-8")
    env = dict(os.environ, HD_PY=sys.executable, HD_ROUTE=str(route), HD_REPO=str(support.source(".")), HD_CFG=str(cfg),
               HD_BOOK=str(book), HD_OTHER=str(book2))
    run = subprocess.run([shutil.which("node"), str(path)], capture_output=True, text=True, encoding="utf-8",
                         timeout=400, env=env)
    got = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
    check("418: the Code list's held changes run in node against the routes", run.returncode == 0, run.stderr[-900:])
    if not got:
        return
    u = got["undo"]
    check("418: an Undo refused over an agent's change reads the list again at once with the server's sentence, no "
          "panel left holding his changes, and his next change is written",
          u["panel"] is None and u["v"] and len(u["said"]) == 1 and u["held"] == 0
          and "Made by an agent" in u["names"] and "Waiting at the door" in u["names"]
          and "After the refused Undo" in u["names"], json.dumps(u))
    o = got["over"]
    check("418: a refused change shows Reload and Overwrite, later changes wait behind it, and an Undo meanwhile undoes "
          "nothing and says so, the changes still waiting",
          o["refused"] and o["refused"]["overwrite"] and o["held"] == 3 and o["undoWaits"]["held"] == 3
          and o["undoWaits"]["panel"] and len(o["undoWaits"]["said"]) == 1, json.dumps(o))
    check("418: Overwrite writes the held changes in order until the server refuses one, which the panel names in the "
          "server's sentence, the change after it still waiting with Overwrite",
          o["panel"] and o["panel"]["overwrite"] and "Taken by an agent" in o["panel"]["line"]
          and o["left"] == [["Third in line"]] and "Refused at first" in o["names"] and got["first"] in o["names"]
          and "Third in line" not in o["names"], json.dumps(o))
    a = got["again"]
    check("418: Overwrite again writes what waited and the panel goes",
          a["panel"] is None and a["left"] == 0 and "Third in line" in a["names"], json.dumps(a))
    last = got["last"]
    check("418: where the refused change was the last held, the panel goes and the server's sentence is the line at the "
          "foot", last["panel"] is None and last["left"] == 0 and "Fourth" in last["names"]
          and any("Another by an agent" in s for s in last["said"]), json.dumps(last))
    bd = got["board"]
    check("418: a board's load and its own refused save leave the Code list's panel standing behind its screen, the "
          "board's panel the one in front there, and back on the Code list its panel is in front with Reload and "
          "Overwrite, which sends what waited while the board's still stands (codesheld2)",
          bd["onBoard"]["panel"] is None and not bd["onBoard"]["shown"] and bd["onBoard"]["held"] == 2
          and bd["boardOwn"] and not bd["boardOwn"]["codes"] and bd["back"] and bd["back"]["codes"]
          and bd["back"]["overwrite"] and bd["after"]["left"] == 0 and bd["after"]["board"]
          and "Held over the board" in bd["after"]["names"] and "Held behind it" in bd["after"]["names"]
          and bd["boardStill"] and bd["boardStill"]["line"] == "board refused", json.dumps(bd))
    check("418: a change made while another of the list's is on the way waits and is written, where it was dropped",
          {"Made first", "Made while busy"} <= set(got["busy"]["names"]), got["busy"]["names"][-6:])
    un = got["unsent"]
    check("418: an Undo while Overwrite sends says so, and a change that never reached the server still waits, the "
          "panel saying it is still waiting rather than a refusal's words",
          len(un["undoSaid"]) == 1 and un["left"] == 1 and un["panel"] and un["panel"]["overwrite"]
          and "still waiting" in un["panel"]["line"], json.dumps(un))
    od = got["order"]
    check("418: changes made while a call of the Code list's is on the way are sent in the order he made them, two "
          "renames of one code leaving the later name (codesheld3)", od["waited"] == 3 and od["last"], json.dumps(od)[:600])
    wd = got["waitDrop"]
    check("418: a change waiting on a call in flight when another project's list opens is counted in the line that "
          "says they were not saved, and the one in flight is written (codesheld3)",
          wd["queuedNow"] == 1 and sum("1 change" in w for w in wd["said"]) == 1 and wd["waiting"] == 0
          and "In flight" in wd["names"] and "Queued behind it" not in wd["names"], json.dumps(wd)[:600])
    ot = got["other"]
    check("418: another project's list opened with changes waiting says in one line that they were not saved, and its "
          "own list shows with no panel",
          len(ot["said"]) == 1 and "1 change" in ot["said"][0] and ot["panel"] is None and ot["left"] == 0
          and "Not sent" not in ot["names"], json.dumps(ot))
