"""Area 332: a shared copy opened from outside the app (fileassoc, Adam, 6 November 2026: a tester's copy came back as
a .idiograph file and the Finder did not know it for Idiograph's). tauri.conf.json makes `.idiograph` Idiograph's own
document type, the macOS type exported by the app and on Windows the ProgID the installer writes, and Sift, Trace and
every test app claim none. A file opened that way, by a double click, a drop on the app's icon or Open With, waits in
the window until a page of the app's own takes it (window.js, the command `opened`), and the page hands it to Home's
Open a shared copy with the file already chosen: the same read and the same card or folder that Home's button gives
once its dialog has chosen. The screen in front is left as Home leaves it first. A file that is not a sent project,
or is not there, is said in the server's own words and asks for no folder.

The fixtures are invented: a project on flying kites in winter."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from . import support
from .support import check, skip


def block(js: str, start: str, end: str) -> str:
    """The text of `js` from the line that opens with `start` to the one before `end`."""
    return start + js.split(start, 1)[1].split(end, 1)[0]


def test_shared_copy_file(scratch: Path):
    print("\n332. A shared copy opened from the Finder or Explorer: Idiograph's own document type, handed to Home's "
          "Open a shared copy, a bad file said in the server's words (6 November)")
    import i18n
    import project_pack as pack_mod
    import server as server_mod
    import idiograph_routes as routes
    from workbook import WorkbookError

    tauri = support.source("packaging/tauri")
    src = tauri / "src-tauri"
    conf = json.loads((src / "tauri.conf.json").read_text(encoding="utf-8"))
    sys.path.insert(0, str(tauri))
    import bundle

    # ── A. the document type: Idiograph's own, and nobody else's in the family
    kinds = conf["bundle"].get("fileAssociations") or []
    kind = kinds[0] if len(kinds) == 1 else {}
    exported = kind.get("exportedType") or {}
    check("332: tauri.conf.json makes a shared copy's own suffix Idiograph's document type, as its Editor and Owner, "
          "named by a ProgID for Windows's installer and by a type the app exports for the Mac, which is data",
          kind.get("ext") == [pack_mod.SUFFIX.lstrip(".")] and kind.get("role") == "Editor" and kind.get("rank") == "Owner"
          and re.fullmatch(r"Idiograph\.[A-Za-z]+", kind.get("name") or "") is not None and bool(kind.get("description"))
          and exported.get("identifier", "").startswith(conf["identifier"] + ".")
          and "public.data" in (exported.get("conformsTo") or []), json.dumps(kinds))
    laid = {app: bundle.merged(conf, bundle.overrides("1.0.0", app=app)) for app in ("idiograph", "sift", "trace")}
    tests = {app: bundle.merged(conf, bundle.overrides("1.0.0", test=True, app=app)) for app in ("idiograph", "sift")}
    check("332: Idiograph's build keeps it, Sift's and Trace's take it away, and so does every test app, so a double "
          "click never opens another app of the family nor a test copy in the real app's place",
          laid["idiograph"]["bundle"]["fileAssociations"] == kinds
          and laid["sift"]["bundle"]["fileAssociations"] is None and laid["trace"]["bundle"]["fileAssociations"] is None
          and all(t["bundle"]["fileAssociations"] is None for t in tests.values())
          and bundle.overrides("1.0.0") == {"version": "1.0.0"} and bundle.NO_FILES == {"bundle": {"fileAssociations": None}},
          json.dumps({a: v["bundle"].get("fileAssociations") for a, v in laid.items()}))

    # ── B. the window: every way a file comes reaches the waiting list, and only the app's own page takes it
    main_rs = (src / "src" / "main.rs").read_text(encoding="utf-8")
    opening_rs = (src / "src" / "opening.rs").read_text(encoding="utf-8")
    check("332: the window takes a file from the Mac's open event, from the command line at the first start, and from "
          "a second start through the single-instance plugin, never handing one to the server, and the page takes it "
          "through its own command, a window of the app's own page alone",
          "if let RunEvent::Opened { urls } = &event {\n            opening::hand(_app, opening::in_urls(urls));" in main_rs
          and main_rs.index("opening::apart(&args, &env::current_dir()") < main_rs.index("split_args(&args);\n    // the single-instance")
          and "opening::apart(args.get(1..).unwrap_or(&[]), Path::new(&cwd));\n            if !opening::hand(app, files) {\n                bring_forward(app);" in main_rs
          and "fn opened(window: tauri::WebviewWindow) -> Vec<String> {\n    opening::take(&window)" in main_rs
          and "if !super::own_page(window) {\n        return Vec::new();" in opening_rs
          and "std::ptr::eq(super::app::this(), &super::app::APPS[0])" in opening_rs)

    node = shutil.which("node")
    if not node:
        skip("332: the page's part under node", "node is not on this machine")
    else:
        # ── C. window.js: taken as the page loads, again when the window says more wait, never by a page without it
        harness = r"""
const src = require('fs').readFileSync(process.argv[2], 'utf8');
function load(hasOpen) {
  const t = { invoked: [], on: {}, handed: [], waiting: ['/Users/wren/Kites/Back from Curt.idiograph'] };
  const win = {
    __IDIOGRAPH_OS__: 'macos', __IDIOGRAPH_SEED__: {},
    addEventListener: (n, f) => { (t.on[n] = t.on[n] || []).push(f); },
    __TAURI_INTERNALS__: { invoke: (cmd, args) => {
      t.invoked.push(cmd);
      if (cmd !== 'opened') return Promise.resolve(null);
      const all = t.waiting; t.waiting = []; return Promise.resolve(all);
    } },
  };
  if (hasOpen) win.idiographOpenFile = (f) => { t.handed.push(f); return true; };
  new Function('window', 'document', src)(win, {});
  Object.assign(t, { win });
  return t;
}
const tick = () => new Promise((r) => setTimeout(r, 30));
(async () => {
  const out = {};
  const a = load(true);
  out.before = a.handed.length;
  (a.on.load || []).forEach((f) => f());
  await tick();
  out.loaded = a.handed.slice();
  a.waiting = ['C:\\Users\\Wren\\Downloads\\Winter.idiograph'];
  out.told = a.win.__idiographOpened();
  await tick();
  out.again = a.handed.slice();
  const b = load(false);
  (b.on.load || []).forEach((f) => f());
  await tick();
  out.without = { asked: b.invoked.filter((c) => c === 'opened').length, left: b.waiting.length };
  console.log(JSON.stringify(out));
})();
"""
        (scratch / "window-332.js").write_text(harness, encoding="utf-8")
        run = subprocess.run([node, str(scratch / "window-332.js"), str(tauri / "window.js")], capture_output=True,
                             text=True, encoding="utf-8", timeout=30)
        try:
            got = json.loads(run.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            got = {}
        check("332: the page takes a file waiting once its own scripts are there, as it loads, and each file the window "
              "says waits later, each handed once to its Open a shared copy",
              got.get("before") == 0 and got.get("loaded") == ["/Users/wren/Kites/Back from Curt.idiograph"]
              and got.get("told") is True
              and got.get("again") == ["/Users/wren/Kites/Back from Curt.idiograph", "C:\\Users\\Wren\\Downloads\\Winter.idiograph"],
              run.stderr[-400:] or json.dumps(got))
        check("332: a page with no Open a shared copy, a print view's or the manual's, takes nothing, so the file waits "
              "for a page that has it", got.get("without") == {"asked": 0, "left": 1}, json.dumps(got.get("without")))

        # ── D. the page: the file handed goes the way Home's button goes once its dialog has chosen
        distil = support.text("apps/idiograph/static/distil.js")
        press = block(distil, "async function openSentPress() {", "\n/* the copy's folder asked for")
        page = r"""
const out = { calls: [] };
const window = {};
let PICKING = false;
const S = { started: null };
let HERE = { screen: 'home' };
let LEAVES = true;
let COVERED = false;
const NOT_SENT = %(not_sent)s;
const searchWhere = () => HERE;
const searchCovered = () => COVERED;
const goHome = async () => { out.calls.push(['home']); if (LEAVES) HERE = { screen: 'home' }; return LEAVES; };
const windowPicks = () => true;
const PICK_SAYS = { sent: 'Choose the shared copy.' };
const $ = (id) => ({ id });
const say = (line) => out.calls.push(['say', line]);
const api = async (route, body) => {
  out.calls.push(['api', route, body]);
  if (/Notes/.test(body.file)) throw new Error(NOT_SENT);
  return { checked: true, name: 'Kite flying', folder: 'Kite flying', ...(/Back/.test(body.file) ? { returning: { root: 'p1', name: 'Kite flying' } } : {}) };
};
const cbOpen = async (read, given) => { out.calls.push(['card', read.returning.name, given]); return true; };
const sentInto = async (given, read) => { out.calls.push(['folder', given, read.name]); };
%(press)s
const tick = () => new Promise((r) => setTimeout(r, 20));
const until = async (f) => { for (let i = 0; i < 100 && !f(); i++) await tick(); };
(async () => {
  // Home's own button: its dialog chooses, then the file is read and its folder asked
  window.idiographPick = async () => '/Users/wren/Kites/Winter.idiograph';
  await openSentPress();
  out.button = out.calls.splice(0);
  // the same file handed by the window, on Home
  window.idiographOpenFile('/Users/wren/Kites/Winter.idiograph');
  await until(() => out.calls.length >= 2);
  out.handed = out.calls.splice(0);
  // a copy coming back, from a participant's screen: Home first, as its own way leaves the screen, then the card
  HERE = { screen: 'statements', path: '/x/a.xlsx' };
  window.idiographOpenFile('/Users/wren/Kites/Back from Curt.idiograph');
  await until(() => out.calls.length >= 3);
  out.back = out.calls.splice(0);
  // a screen whose save fails keeps him there with what he typed, and nothing is read
  HERE = { screen: 'statements', path: '/x/a.xlsx' };
  LEAVES = false;
  window.idiographOpenFile('/Users/wren/Kites/Winter.idiograph');
  await until(() => out.calls.length >= 1); await tick();
  out.stays = out.calls.splice(0);
  LEAVES = true; HERE = { screen: 'home' };
  // a file that is no sent project: the server's words, and no folder asked
  window.idiographOpenFile('/Users/wren/Kites/Notes.idiograph');
  await until(() => out.calls.length >= 2);
  out.bad = out.calls.splice(0);
  // a card open: the file waits for him to close it, and the page's start first
  COVERED = true;
  let started; S.started = new Promise((r) => { started = r; });
  window.idiographOpenFile('/Users/wren/Kites/Winter.idiograph');
  await tick(); await tick();
  out.waitsStart = out.calls.length;
  started(); await tick(); await tick();
  out.waitsCard = out.calls.length;
  COVERED = false;
  await until(() => out.calls.length >= 2);
  out.after = out.calls.splice(0).map((c) => c[0]);
  console.log(JSON.stringify(out));
})();
""" % {"press": press, "not_sent": json.dumps(i18n.t("server.file_project_sent_from_idiograph"))}
        ran = support.run_node(page, scratch, "page-332.js")
        try:
            got = json.loads(ran.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            got = {}
        read_call = ["api", "/api/open-sent", {"file": "/Users/wren/Kites/Winter.idiograph", "check": True}]
        folder_call = ["folder", {"file": "/Users/wren/Kites/Winter.idiograph"}, "Kite flying"]
        check("332: a file handed by the window takes the very calls Home's Open a shared copy makes once its dialog "
              "has chosen: the file read first, then the folder for the copy",
              got.get("button") == [read_call, folder_call] and got.get("handed") == got.get("button"),
              ran.stderr[-400:] or json.dumps(got)[:600])
        check("332: a copy coming back, handed on a participant's screen, leaves the screen as Home does, then offers its "
              "boards to its project in the card, as the button's way does",
              got.get("back") == [["home"], ["api", "/api/open-sent", {"file": "/Users/wren/Kites/Back from Curt.idiograph", "check": True}],
                                  ["card", "Kite flying", {"file": "/Users/wren/Kites/Back from Curt.idiograph"}]],
              json.dumps(got.get("back")))
        check("332: a screen whose save fails keeps him where he is, and the file is not read",
              got.get("stays") == [["home"]], json.dumps(got.get("stays")))
        check("332: a file that is no sent project is said in the server's own words, and no folder is asked for",
              got.get("bad") == [["api", "/api/open-sent", {"file": "/Users/wren/Kites/Notes.idiograph", "check": True}],
                                 ["say", i18n.t("server.file_project_sent_from_idiograph")]], json.dumps(got.get("bad")))
        check("332: the page finishes its start first, and a card he has open is his to close before the file is read",
              got.get("waitsStart") == 0 and got.get("waitsCard") == 0 and got.get("after") == ["api", "folder"],
              json.dumps({k: got.get(k) for k in ("waitsStart", "waitsCard", "after")}))

    # ── E. the server's own words for a file that is not a sent project, or not there, by the call the page makes
    base = scratch / "shared-copy-332"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    notes = base / "Kite notes.idiograph"
    notes.write_text("Wind from the north, the line wet.\n", encoding="utf-8")
    other_zip = base / "Kite photos.idiograph"
    with zipfile.ZipFile(other_zip, "w") as zf:
        zf.writestr("photos/one.txt", "a kite over the dunes")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE)

    def said(file: Path) -> str:
        try:
            routes.api_open_sent({"file": str(file), "check": True})
        except WorkbookError as exc:
            return str(exc)
        return ""

    try:
        server_mod.ROOT_OVERRIDE = None
        words = [said(notes), said(other_zip), said(base / "Gone.idiograph")]
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = kept
    check("332: a file that is not a sent project, a text file or another zip under the suffix, and a file that is not "
          "there, are refused in the server's existing words, with nothing opened",
          words == [i18n.t("server.file_project_sent_from_idiograph")] * 2 + [i18n.t("server.file")]
          and not any(p.is_dir() for p in base.iterdir()), json.dumps(words))
