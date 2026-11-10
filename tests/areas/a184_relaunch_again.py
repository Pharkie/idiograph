"""Area 184: the sixth Tauri build (18 October 2026). Installing a downloaded update says Relaunch again,
the normal word, which Adam never asked to change, six of the installer's lines in the screenshot check's
words, and the Windows checks that take what the check could not use: a failed start's dialog alone, with
the build before the fifth's for its Before, the second window on a small screen with each window in front
in turn, and the installer's details widened until every line shows whole.

Every string here is Adam's, from his word at 14:30 on 18 October and his yes to the check's suggestions.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from . import support
from .support import STUDY_PSEUDONYMS, check, skip


def js_function(src: str, name: str) -> str:
    """A top-level function of a page script, from its `function` line to the brace that closes it."""
    m = re.search(rf"^(?:async )?function {name}\(", src, re.M)
    if not m:
        return ""
    end = src.find("\n}\n", m.start())
    return src[m.start():end + 3] if end > 0 else ""


def test_relaunch_again(scratch):
    print("\n184. The sixth Tauri build (18 October): Relaunch again for an update, six installer lines in the "
          "screenshot check's words, a failed start's dialog alone with the build before the fifth's for its "
          "Before, the second window with each window in front, and the installer's details whole. Since the test review "
          "of 18 October the lines' words, the installer's lines and the drivers' shots are review shots, and a relaunch "
          "stopped while what is typed cannot be saved, the place handed on and no participant named stay")
    tauri = support.source("packaging/tauri")
    read = lambda p: Path(p).read_text(encoding="utf-8")  # noqa: E731
    app_js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    english = read(tauri / "src-tauri" / "windows" / "English.nsh")
    node = shutil.which("node")

    # ── A. Relaunch on the page, the menu's Restart Idiograph left as it is
    upd = app_js[app_js.index("Idiograph's own updates, and What's new"):app_js.index("window.openWhatsNew = openWhatsNew;")]
    if node:
        bits = "\n".join(js_function(app_js, n) for n in ("updLine", "updTake", "updRelaunch"))
        harness = scratch / "relaunch-184.js"
        harness.write_text(support.i18n_js() + r"""
const APP_NAME = 'Idiograph';
const UPD = { view: null, opened: null, relaunching: false };
const SERVER = { busy: false };
const said = [];
const say = (t) => said.push(t);
let saveOk = true;
const savePending = async () => saveOk;
const spotKeep = () => {};
const RETURN_KEY = 'idiograph-return', HOME_KEY = 'idiograph-home';
const sessionStorage = { getItem: (k) => (k === RETURN_KEY ? 'a case' : null) };
const asked = [];
const updAsk = async (op, more) => { asked.push([op, more]); return null; };
const updDraw = () => {}; const wnFoot = () => {}; const updTicks = () => {};
const $ = () => ({ hidden: true });
""" + bits + r"""
(async () => {
  const ready = updLine({ check: true, state: 'ready', version: '0.9.2' });
  saveOk = false; await updRelaunch();
  const notSaved = said.splice(0); const askedNotSaved = asked.splice(0);
  saveOk = true; await updRelaunch();
  const going = said.splice(0); const askedGoing = asked.splice(0);
  updTake({ here: true, state: 'failed', reason: '' });
  const plain = said.splice(0);
  UPD.relaunching = true;
  updTake({ here: true, state: 'failed', reason: 'Idiograph could not put the update in place.' });
  const why = said.splice(0);
  updTake({ here: true, state: 'failed', reason: 'GitHub could not be reached.' });
  const notRelaunching = said.splice(0);
  console.log(JSON.stringify({ ready: { said: ready.said, yes: ready.yes, no: ready.no }, notSaved, askedNotSaved,
    going, askedGoing, plain, why, notRelaunching }));
})();
""", encoding="utf-8")
        run = subprocess.run([node, str(harness)], capture_output=True, text=True, encoding="utf-8")
        try:
            got = json.loads(run.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            got = {"error": (run.stdout + run.stderr)[-500:]}
        check("184: the ready line offers Relaunch now and Later, Relaunch now says Relaunching Idiograph. and hands the "
              "window the page's place, and what is typed that cannot be saved stops it with its own line",
              bool((got.get("ready") or {}).get("said")) and bool((got.get("ready") or {}).get("yes"))
              and len(got.get("notSaved") or []) == 1 and got.get("askedNotSaved") == []
              and len(got.get("going") or []) == 1 and got.get("askedGoing") == [["relaunch", {"place": {"idiograph-return": "a case"}}]],
              json.dumps(got)[:600])
        check("184: a relaunch that fails says the window's reason, or Idiograph did not relaunch. Quit it and open it "
              "again. when it gives none, once, and a failure while no relaunch is under way says nothing of one",
              len(got.get("plain") or []) == 1 and got.get("why") == ["Idiograph could not put the update in place."]
              and got.get("notRelaunching") == [], json.dumps(got)[:600])
    else:
        skip("184: Relaunch now and its three messages under node", "node is not on this machine")

    # ── D. the failed start's driver loads on any system
    sys.path.insert(0, str(tauri))
    import drive_failed_start
    check("184: drive_failed_start.py loads on any system, its Windows calls made only as it runs",
          callable(drive_failed_start.failed_start) and drive_failed_start.RESULTS == {})

    # ── G. no study's participant named in the new words
    new_text = "\n".join([upd, english, read(tauri / "drive_failed_start.py"), read(tauri / "drive_windows_four.py"),
                          read(tauri / "drive_installer.py")])
    check("184: the new words name no study's participant",
          not any(re.search(rf"\b{n}\b", new_text) for n in STUDY_PSEUDONYMS))
