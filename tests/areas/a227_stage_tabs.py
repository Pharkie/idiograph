"""Area 227: Idiograph's stage tabs (the split's build 3b, Adam's ruling of 20 October 2026): a fixed tab per stage
in place of the bar's steps, Experiential statements, PETs and GETs, and with two or more timepoints Experiential
statements, PETs, LPETs, LGETs and Trajectories, each shown only once its screen exists. Each tab opens its stage for
the participant in front of him, the participant picker in the tab switches the participant, and the keys move along
the tabs. Every fixture invented, on a made-up kite club, in the scratch folder."""
from __future__ import annotations

import base64
import json
import shutil
import subprocess
from pathlib import Path

from . import support
from .support import check, skip
import idiograph_routes

TEXT = ("Kit: [00:00:03] When did you first fly one?\n{who}: [00:00:08] On the hill, the day the wind turned.\n"
        "Kit: [00:00:40] And the line?\n{who}: [00:00:44] It cut my fingers, and I kept hold.\n")


def test_stage_tabs(scratch):
    print("\n227. Idiograph's stage tabs, 20 October: a tab per stage, shown once its screen exists, each opening its "
          "stage for the participant in front, the participant picker in the tab, and the keys along the tabs")
    import server as server_mod

    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    tjs = support.text("apps/idiograph/static/themes.js")
    page = support.page_text()
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: (("async " if f"async function {name}(" in src else "") + f"function {name}(" + fn(src, name) + "\n}")

    # ── A. the participants the statements tab's picker lists, through the API, which only reads
    base = scratch / "a227"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    cfg_file = scratch / "a227-config.json"
    cfg_file.write_text(json.dumps({"projects": [], "interviewer": "Kit"}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY)
    b64 = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")
    row = lambda name, who: {"name": name, "data": b64(TEXT.format(who=who)), "pseudonym": who, "interview": "Interview",
                             "speakers": {"Kit": "interviewer", who: "participant"}}

    def tree(at: Path) -> dict:
        return {p.relative_to(at).as_posix(): (p.read_bytes() if p.is_file() and p.suffix != ".lock" else None)
                for p in sorted(at.rglob("*"))}

    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg_file, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = scratch / "a227-state.json", {"recent": []}
        club = base / "Kite club"
        club.mkdir()
        idiograph_routes.api_new_project({"op": "make", "folder": str(club), "name": "Kite club",
                                    "research_question": "How do people come to fly kites?",
                                    "files": [row("pell.txt", "Pell"), row("odo.txt", "Odo"), row("brin.txt", "Brin")]})
        books = sorted(club.glob("P* - */*EN & ES.xlsx"))
        before = tree(club)
        got = idiograph_routes.api_participants({"workbook": str(books[1])})
        check("227: the picker's list is every participant of the project in case order, the one in front marked, "
              "with the project's name, and reading it writes nothing",
              got["project"] == "Kite club" and [p["case"] for p in got["participants"]] == ["P1 - Pell", "P2 - Odo", "P3 - Brin"]
              and [p["current"] for p in got["participants"]] == [False, True, False]
              and all(Path(server_mod.abs_path(p["path"])).is_file() for p in got["participants"])
              and tree(club) == before, json.dumps(got)[:400])
        check("227: the participants route is Idiograph's, beside the PETs switcher's",
              "/api/participants" in server_mod.routes_of("idiograph") and server_mod.ROUTE_APP["/api/participants"] == "idiograph")
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY = kept

    # ── B. the tabs on each bar open their stage, the old step shortcut kept
    work = page.split('<section id="work"', 1)[1].split("</section>", 1)[0]
    themes = page.split('<section id="themes"', 1)[1].split("</section>", 1)[0]
    check("227: both bars hold the tabs, each tab's name opening its stage, the participant picker in the path under them "
          "since option C of the bars (26 October 2026), P still opening PETs",
          'id="es-steps"' in work and 'id="es-who"' in work and 'id="th-steps"' in themes and 'id="th-cases"' in themes
          and themes.index('id="th-steps"') < themes.index('id="th-path"') < themes.index('id="th-cases"')
          and "$('es-step-pets').onclick = () => esStep('pets');" in app and "$('es-step-gets').onclick = () => esStep('gets');" in app
          and "$(id).onclick = () => thStepTo(step);" in tjs
          and "else if (key === 'p' && !$('work').hidden && S.data) { e.preventDefault(); esStep('pets'); }" in app)

    node = shutil.which("node")
    if not node:
        skip("227: the tabs in node", "node is not on this machine")
        return
    stages = "const DS_STAGES = " + app.split("const DS_STAGES = ", 1)[1].split("];", 1)[0] + "];"
    harness = r"""
const calls = [];
const noop = () => {};
const els = {};
let FOCUS = null;
const button = (id) => ({ id, attrs: {}, offsetParent: {}, focus() { FOCUS = this; }, scrollIntoView: noop,
  setAttribute(k, v) { this.attrs[k] = v; }, removeAttribute(k) { delete this.attrs[k]; } });
const tab = (step, ...ids) => {
  const btns = ids.map((id) => (els[id] = els[id] || button(id)));
  return { hidden: false, dataset: { step }, on: false, classList: { toggle(k, v) { tab.last = this; } }, btns,
    querySelector: () => btns[0], querySelectorAll: () => btns };
};
const tabs = [tab('statements', 'name-es', 'who'), tab('pets', 'name-pets'), tab('gets', 'name-gets')];
for (const t of tabs) t.classList.toggle = function (k, v) { t.on = v; };
const nav = { classList: { over: false, toggle(k, v) { this.over = v; } }, scrollLeft: 0, clientWidth: 300, scrollWidth: 300,
  querySelectorAll: (sel) => (sel === '.ds-tab' ? tabs : tabs.filter((t) => !t.hidden).flatMap((t) => t.btns)) };
const MOD = (e) => !!e.metaKey;
const $ = (id) => (id === 'nav' ? nav : (els[id] = els[id] || { hidden: true, attrs: {}, setAttribute(k, v) { this.attrs[k] = v; } }));
const document = { get activeElement() { return FOCUS; } };
const S = { data: { path: 'club/P2 - Odo/P2 Odo - EN & ES.xlsx' }, dirty: false };
let SAVE_FAILS = false;
const current = () => ({ key: 'Initial:3' });
const commit = async () => { calls.push(['commit']); S.dirty = SAVE_FAILS; };
const navGo = (again, open) => { calls.push(['nav']); return open(); };
const openCase = (path) => calls.push(['open', path]);
const esWhoMenu = (open) => calls.push(['menu', open]);
""" + stages + "\n" + "\n".join(whole(app, n) for n in ("dsStages", "dsTabsDraw", "dsTabsFit", "dsTabsKeys", "esWhoGo")) + r"""
(async () => {
  const out = {};
  const one = { timepoints: [{ n: 1, label: 'T1' }] };
  const three = { timepoints: [{ n: 1, label: 'T1' }, { n: 2, label: 'T2' }, { n: 3, label: 'T3' }] };
  out.one = dsStages(one);
  out.none = dsStages(null);
  out.many = dsStages(three);
  // the screens to come, as they will stand once built: five, GETs giving way to LGETs
  for (const s of DS_STAGES) s.built = true;
  out.manyBuilt = dsStages(three);
  out.oneBuilt = dsStages(one);
  for (const s of DS_STAGES) if (['lpets', 'lgets', 'trajectories'].includes(s.step)) s.built = false;
  // drawn for PETs: PETs marked and holding the picker, the others links
  dsTabsDraw('nav', one, 'pets');
  out.drawn = tabs.map((t) => [t.dataset.step, t.hidden, t.on, t.btns[0].attrs['aria-current'] || null]);
  // the keys: Right from the statements tab's name to its picker, then to PETs, End to GETs, Home back, Left stays
  const key = (k, mods = {}) => { let stopped = false; dsTabsKeys(Object.assign({ key: k, currentTarget: nav, preventDefault() { stopped = true; } }, mods)); return [FOCUS && FOCUS.id, stopped]; };
  FOCUS = els['name-es'];
  out.keys = [key('ArrowRight'), key('ArrowRight'), key('End'), key('Home'), key('ArrowLeft'), key('ArrowRight', { metaKey: true }), key('a')];
  // the picker: another participant opens on their statements, the passage in front saved first
  await esWhoGo({ case: 'P1 - Pell', path: 'club/P1 - Pell/P1 Pell - EN & ES.xlsx', current: false }); out.other = calls.splice(0);
  S.dirty = true; await esWhoGo({ case: 'P3 - Brin', path: 'club/P3 - Brin/P3 Brin - EN & ES.xlsx', current: false }); out.saved = calls.splice(0);
  S.dirty = true; SAVE_FAILS = true; await esWhoGo({ case: 'P3 - Brin', path: 'b', current: false }); out.unsaved = calls.splice(0);
  S.dirty = false; SAVE_FAILS = false; await esWhoGo({ case: 'P2 - Odo', path: S.data.path, current: true }); out.same = calls.splice(0);
  console.log(JSON.stringify(out));
})().catch((e) => { console.error(String(e && e.stack || e)); process.exit(1); });
"""
    script = scratch / "stage-tabs-227.js"
    script.write_text(harness, encoding="utf-8")
    run = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    o = json.loads(run.stdout) if run.returncode == 0 and run.stdout.strip() else {}
    said = (run.stdout + run.stderr)[:600]
    check("227: in node, a project of one timepoint, and one from before, show Experiential statements, PETs and GETs, "
          "and one of two or more the five since 21 October (timepoints part 3), LGETs in GETs' place",
          o.get("one") == ["statements", "pets", "gets"] and o.get("none") == ["statements", "pets", "gets"]
          and o.get("many") == ["statements", "pets", "lpets", "lgets", "trajectories"], said)
    check("227: in node, once their screens exist a project of two or more shows the five, LGETs in GETs' place, and "
          "a project of one still its three",
          o.get("manyBuilt") == ["statements", "pets", "lpets", "lgets", "trajectories"]
          and o.get("oneBuilt") == ["statements", "pets", "gets"], said)
    check("227: in node, the tab in front is marked as the page and the others are links",
          o.get("drawn") == [["statements", False, False, None], ["pets", False, True, "page"], ["gets", False, False, None]], said)
    check("227: in node, Left and Right move along the tabs and the picker, Home and End to the ends, and other keys and "
          "Cmd with an arrow are left alone",
          o.get("keys") == [["who", True], ["name-pets", True], ["name-gets", True], ["name-es", True], ["name-es", True],
                            ["name-es", False], ["name-es", False]], said)
    check("227: in node, the picker opens another participant on their statements, the passage in front saved first, "
          "stays when it cannot be saved, and the participant in front does nothing",
          o.get("other") == [["menu", False], ["nav"], ["open", "club/P1 - Pell/P1 Pell - EN & ES.xlsx"]]
          and o.get("saved") == [["menu", False], ["commit"], ["nav"], ["open", "club/P3 - Brin/P3 Brin - EN & ES.xlsx"]]
          and o.get("unsaved") == [["menu", False], ["commit"]] and o.get("same") == [["menu", False]], said)
