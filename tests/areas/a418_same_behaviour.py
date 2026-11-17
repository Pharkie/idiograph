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
          close_ids and not crossing_deletes and "outsideNotice(null)" in out_close
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
    stale_codes = fn(codes, "codesOps")
    check("418: a refused save goes to the one shared panel, staleNotice, on the boards and the Code list, and the "
          "Code list's refusal is no silent reload",
          "staleNotice(" in fn(themes, "thStaleDraw") and "staleNotice(null)" in fn(themes, "thStaleHide")
          and "codesStale(true)" in stale_codes and "staleNotice({ codes: true" in fn(codes, "codesStale")
          and "if (err.data && err.data.stale) await codesReload();" not in stale_codes
          and "codesOps(ops, true)" in fn(codes, "codesStale"))

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
          and "unsayUndo()" in fn(codes, "codesOps"))

    # ── sameux2b: the Code list's notice, its refused changes, Trajectories' export given up, the panel's words
    tick, ops, undo, stale = fn(codes, "codesStampTick"), fn(codes, "codesOps"), fn(codes, "codesUndo"), fn(codes, "codesStale")
    check("418: the Code list's delete notice is withdrawn by a change from elsewhere, and its Undo sends the version "
          "the screen read, a refusal showing the refused change's panel with Reload alone",
          tick.index("unsayUndo()") < tick.index("outsideNotice(") and "v: CD.data && CD.data.v" in undo
          and "codesStale(false)" in undo and "overwrite: overwrite ?" in stale
          and "$('th-stale-over').hidden = !info.overwrite;" in fn(distil, "staleNotice"))
    check("418: while the Code list's refused change shows, later changes wait behind it and Overwrite sends them all "
          "in order, Reload dropping them",
          "if (!over && XS.info && XS.info.codes) { CD.held.push(...ops);" in ops and "codesStale(true)" in ops
          and "const ops = CD.held.slice();" in stale and "codesOps(ops, true)" in stale and "CD.held = [];" in stale)
    check("418: Trajectories' export given up after its wait says so in the export panel",
          "if (TJ.busy) { exportFailed(null, t('trajectories.export_still_saving')); return; }" in fn(traj, "trajExportGo"))
    on = fn(distil, "outsideNotice")
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
