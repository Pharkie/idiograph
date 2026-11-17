"""Area 413: one export notice for every export (exportnotice, Adam, 17 November 2026: "the same function" behaves the
same on every tab, standardised on the PETs panel). Show in Finder on it goes through /api/reveal, which shows a file an
export wrote inside a project's folder, or one a save dialog put elsewhere this run, on a Mac, Windows or Linux, and
refuses anything else with nothing written. The statements screen's, Trajectories' and the Code list's exports end in
the same notice as the boards', its file and the path Show in Finder shows, and a failure's reason goes in it too.
Every fixture is invented, a project on keeping bees."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import server as server_mod

from . import support
from .support import check
import idiograph_routes


NODE_TABS = r"""
const out = {};
let failing = null, notices = [];
const t = (key) => key;
const say = (line) => notices.push({ said: line });
const needsRestart = () => false;
const RESTART_LINE = 'restart';
const exportNotice = (info) => notices.push(info);
const exportFailed = (err, fallback) => exportNotice({ failed: (err && err.message) || fallback });
const menu = { hidden: true, querySelector: () => null };
const $ = (id) => (id.endsWith('xmenu') ? menu : { contains: () => false });
const document = { activeElement: null };
const trajXmenu = () => {}, codesXmenu = () => {}, esXmenu = () => {};
const trajIdle = async () => {};
const distilSavePending = async () => true;
const TJ_EXPORT = '/api/trajectories-export', ES_EXPORT = '/api/transcript-export', CD_EXPORT = '/api/codes-export';
const TJ = { data: {}, path: '/bees/P1 - Wren/P1 Wren.xlsx' };
const S = { data: { path: '/bees/P1 - Wren/P1 Wren.xlsx' } };
const CD = { path: '/bees/P1 - Wren/P1 Wren.xlsx' };
async function api(url, body) {
  if (failing) throw new Error(failing);
  const name = { '/api/trajectories-export': 'Bees - Trajectories.pdf', '/api/transcript-export': 'Wren - Annotated transcript.pdf',
    '/api/codes-export': 'Bees - Code list.pdf' }[url];
  return { name, shown: [name], path: '/bees/' + name };
}
/*FN*/
(async () => {
  for (const [name, go] of [['traj', trajExportGo], ['es', esExportGo], ['codes', codesExportGo]]) {
    notices = []; failing = null;
    await go('pdf');
    out[name] = notices;
    notices = []; failing = 'The PDF could not be made, so nothing was written.';
    await go('pdf');
    out[name + 'Failed'] = notices;
  }
  process.stdout.write(JSON.stringify(out) + '\n');
})();
"""


def piece(script: str, head: str) -> str:
    return head + script.split(head, 1)[1].split("\n}\n", 1)[0] + "\n}\n"


def test_export_notice(scratch: Path):
    print("\n413. One export notice for every export: Show in Finder through /api/reveal, a file in a project or one a "
          "save dialog put elsewhere, and every tab's export ending in the same notice")
    base = scratch / "reveal-413"
    shutil.rmtree(base, ignore_errors=True)
    root = base / "Keeping bees"
    (root / "P1 - Wren").mkdir(parents=True)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({"name": "Keeping bees", "research_question":
                                                            "How do beekeepers live through a cold spring?",
                                                            "uid": "a413beef0000cafe"}), encoding="utf-8")
    made = root / "Keeping bees - Trajectories.pdf"
    made.write_bytes(b"%PDF-1.7 stands in")
    inner = root / "P1 - Wren" / "P1 Wren - Annotated transcript.pdf"
    inner.write_bytes(b"%PDF-1.7 stands in")
    outside = base / "elsewhere" / "Keeping bees.qdpx"
    outside.parent.mkdir()
    outside.write_bytes(b"PK\x03\x04 stands in")
    config_file = base / "config-413.json"
    config_file.write_text(json.dumps({"projects": [{"root": str(root)}], "interviewer": "Sam", "corpus": "",
                                       "gravity_reference": "", "corpus_exclude": []}), encoding="utf-8")

    def files(at: Path) -> dict:
        return {p.relative_to(at).as_posix(): p.read_bytes() for p in sorted(at.rglob("*")) if p.is_file()}

    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.PLATFORM,
            idiograph_routes.SHOW_FOLDER, set(idiograph_routes.SAVED_ELSEWHERE))
    shown = []
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = config_file, None, {"recent": []}
        idiograph_routes.SHOW_FOLDER = lambda target: shown.append(Path(target))
        before = files(base)

        server_mod.PLATFORM = "darwin"
        answers = [idiograph_routes.api_reveal({"file": str(made)}), idiograph_routes.api_reveal({"file": str(inner)})]
        check("413: on a Mac Show in Finder selects the file an export wrote, at the project's root or in a "
              "participant's folder, and writes nothing",
              answers == [{"revealed": True}] * 2 and shown == [made.resolve(), inner.resolve()] and files(base) == before,
              str(shown))

        shown.clear()
        server_mod.PLATFORM = "win32"
        idiograph_routes.api_reveal({"file": str(made)})
        server_mod.PLATFORM = "linux"
        idiograph_routes.api_reveal({"file": str(made)})
        check("413: Windows' Explorer selects the file and Linux's file manager opens its folder",
              shown == [made.resolve(), made.parent.resolve()], str(shown))

        shown.clear()
        server_mod.PLATFORM = "darwin"
        refused = []
        for body in ({"file": str(outside)}, {"file": str(root / "P1 - Wren" / ".." / ".." / "elsewhere" / outside.name)},
                     {"file": str(root / "gone.pdf")}, {"file": ""}):
            try:
                idiograph_routes.api_reveal(body)
                refused.append(False)
            except (server_mod.WorkbookError, server_mod.OutsideRoot):
                refused.append(True)
        server_mod.PLATFORM = "freebsd14"
        try:
            idiograph_routes.api_reveal({"file": str(made)})
            refused.append(False)
        except server_mod.WorkbookError:
            refused.append(True)
        check("413: a file no project holds, one reached by .. out of it, one not there, none named and a machine that "
              "is no Mac, Windows or Linux are refused, nothing shown and nothing written",
              refused == [True] * 5 and shown == [] and files(base) == before, str(refused))

        server_mod.PLATFORM = "darwin"
        idiograph_routes.SAVED_ELSEWHERE.add(str(outside.resolve()))
        answer = idiograph_routes.api_reveal({"file": str(outside)})
        check("413: a file a save dialog put outside every project this run (Export as REFI-QDA in the window) is shown",
              answer == {"revealed": True} and shown == [outside.resolve()], str(shown))
    finally:
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY, server_mod.PLATFORM,
         idiograph_routes.SHOW_FOLDER) = kept[:5]
        idiograph_routes.SAVED_ELSEWHERE.clear()
        idiograph_routes.SAVED_ELSEWHERE.update(kept[5])

    # ── in node, each tab's own export: the notice with the file and its path, a failure's reason in the same notice
    traj = support.text("apps/idiograph/static/trajectories.js")
    distil = support.text("apps/idiograph/static/distil.js")
    codes = support.text("apps/idiograph/static/codes.js")
    fns = (piece(traj, "async function trajExportGo(") + piece(distil, "async function esExportGo(")
           + piece(codes, "async function codesExportGo("))
    (scratch / "a413").mkdir(parents=True, exist_ok=True)
    ran = support.run_node(NODE_TABS.replace("/*FN*/", fns), scratch / "a413", "a413-tabs.js")
    got = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {}
    wanted = {"traj": ("documents.trajectories.name", "Bees - Trajectories.pdf"),
              "es": ("documents.transcript.name", "Wren - Annotated transcript.pdf"),
              "codes": ("documents.codes.name", "Bees - Code list.pdf")}
    check("413: Trajectories', the statements screen's and the Code list's Save as PDF end in the export notice, its "
          "heading's name, the file and the path Show in Finder shows, and no toast",
          all(got.get(k) == [{"what": w, "shown": [f], "path": "/bees/" + f}] for k, (w, f) in wanted.items()),
          ran.stderr[-400:] or json.dumps(got)[:600])
    check("413: an export that fails on each of them says the server's sentence in the same notice",
          all(got.get(k + "Failed") == [{"failed": "The PDF could not be made, so nothing was written."}] for k in wanted),
          json.dumps({k: got.get(k + "Failed") for k in wanted}))
