from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from . import support
from .support import STUDY_PSEUDONYMS, check, skip

# Tauri 2.12.1's own English words for its installer, every name its installer script asks for, which
# English.nsh must keep each of (the fourth Tauri build, 18 October)
TAURI_LANG_NAMES = ("addOrReinstall", "alreadyInstalled", "alreadyInstalledLong", "appRunning", "appRunningOkKill",
                    "chooseMaintenanceOption", "choowHowToInstall", "createDesktop", "dontUninstall",
                    "dontUninstallDowngrade", "failedToKillApp", "installingWebview2", "newerVersionInstalled", "older",
                    "olderOrUnknownVersionInstalled", "silentDowngrades", "unableToUninstall", "uninstallApp",
                    "uninstallBeforeInstalling", "unknown", "webview2AbortError", "webview2DownloadError",
                    "webview2DownloadSuccess", "webview2Downloading", "webview2InstallError", "webview2InstallSuccess",
                    "deleteAppData")


def js_function(src: str, name: str) -> str:
    """A top-level function of a page script, from its `function` line to the brace that closes it."""
    m = re.search(rf"^(?:async )?function {name}\(", src, re.M)
    if not m:
        return ""
    end = src.find("\n}\n", m.start())
    return src[m.start():end + 3] if end > 0 else ""


def test_updates(scratch):
    print("\n175. Idiograph's updates and What's new, the fourth Tauri build (18 October): Tauri's own updater, the "
          "question asked once, Settings' Updates rows, the ready line, Relaunch now and Later, What's new once after "
          "an update, a test release proved on this machine with a throwaway key, the installers' pictures and words, "
          "every window whole on its screen, the crash notice in plain words, and the key's password off every command line")
    tauri = support.source("packaging/tauri")
    src_dir = tauri / "src-tauri"
    read = lambda p: Path(p).read_text(encoding="utf-8")  # noqa: E731
    conf = json.loads(read(src_dir / "tauri.conf.json"))
    main_rs, update_rs = (read(src_dir / "src" / n) for n in ("main.rs", "update.rs"))
    cargo, lock, build_rs = read(src_dir / "Cargo.toml"), read(src_dir / "Cargo.lock"), read(src_dir / "build.rs")
    caps = json.loads(read(src_dir / "capabilities" / "page.json"))
    app_js = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    sys.path.insert(0, str(tauri))
    sys.path.insert(0, str(support.source("packaging")))
    import bundle as window
    import minisign
    import update_proof

    # ── A. the updater: Tauri's own plugin, the releases repository alone, every file's signature and version
    up = conf["plugins"]["updater"]
    check("175: the updater is Tauri's own plugin, pinned, read from the releases repository over https alone, with "
          "the version every file was signed for required and the installer run on Windows with its progress bar alone",
          'tauri-plugin-updater = "=2.13.1"' in cargo and 'name = "tauri-plugin-updater"\nversion = "2.13.1"' in lock
          and up["endpoints"] == ["https://github.com/Pharkie/idiograph/releases/latest/download/latest.json"]
          and up.get("requireSignedVersion") is True and up.get("windows", {}).get("installMode") == "passive"
          and "dangerousInsecureTransportProtocol" not in up and "dangerousAcceptInvalidCerts" not in up
          and up["pubkey"].startswith("dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXk6IDNDRUE2QTM1NkVGQjNFNjM")
          and "tauri_plugin_updater::Builder::new().build()" in main_rs,
          json.dumps(up)[:300])
    check("175: the page reaches the updates through the window's own command alone, never the plugin's, and the "
          "window's command is named for the page",
          '"updates"]' in build_rs and "allow-updates" in caps["permissions"]
          and not any(p.startswith("updater") for p in caps["permissions"])
          and "closing, updates])" in main_rs and "fn updates(" in main_rs and "update::act(" in main_rs)

    # ── B. a test release: a check's own key and address in the test app alone, never in Idiograph
    try:
        window.overrides("0.9.2", test=False, update=window.test_update("RW", "http://127.0.0.1:8798/latest.json"))
        leaked = "laid over the real app"
    except SystemExit as exc:
        leaked = str(exc)
    try:
        window.test_update("RW", "http://example.org/latest.json")
        elsewhere = "taken"
    except SystemExit as exc:
        elsewhere = str(exc)
    test = window.overrides("0.9.2", test=True, update=window.test_update(" RWkey\n", "http://127.0.0.1:8798/latest.json"))
    tls = window.test_update("RWkey", "https://127.0.0.1:8798/latest.json")
    check("175: a check's own update key and address go in the test app alone, plain http on this machine alone, and "
          "a build that ships keeps the releases repository and its key",
          "test app alone" in leaked and "this machine alone" in elsewhere
          and test["identifier"] == "uk.co.adamknowles.idiograph.test" and test["version"] == "0.9.2"
          and test["plugins"]["updater"] == {"pubkey": "RWkey", "endpoints": ["http://127.0.0.1:8798/latest.json"],
                                             "dangerousInsecureTransportProtocol": True}
          and "dangerousInsecureTransportProtocol" not in tls["plugins"]["updater"]
          and "plugins" not in window.overrides("0.9.1"), json.dumps(test)[:300])
    bm, bw = read(support.source("packaging/build_mac.py")), read(support.source("packaging/build_windows.py"))
    import build_windows
    try:
        build_windows.main(["--dry-run", "--version", "0.9.2"])
        refused = "built"
    except SystemExit as exc:
        refused = str(exc)
    nsis = scratch / "made" / "nsis"
    nsis.mkdir(parents=True)
    for name in ("Idiograph Test_0.9.1_x64-setup.exe", "Idiograph Test_0.9.2_x64-setup.exe"):
        (nsis / name).write_bytes(b"MZ")
    try:
        build_windows.installer_of(scratch / "made", "0.9.3")
        none_for = "found"
    except SystemExit as exc:
        none_for = str(exc)
    check("175: the Windows build takes the installer made for the version it built, never another version's left "
          "beside it by a cache, as GitHub's second run of 18 October took a 0.9.2 installer for 0.9.1",
          build_windows.installer_of(scratch / "made", "0.9.1").name == "Idiograph Test_0.9.1_x64-setup.exe"
          and "no installer for 0.9.3" in none_for, none_for)
    check("175: both builds take a test version, notes, key and address for the test app alone, and refuse them for Idiograph",
          "test app alone" in refused and all('"--update-key"' in b and '"--update-url"' in b and '"--version"' in b
                                              and '"--whats-new"' in b and "for the test app alone." in b for b in (bm, bw)),
          refused)
    rel = read(support.source("packaging/release.py"))
    import release
    try:
        import server as server_version_of
        release.main([f"v{server_version_of.VERSION}", "--dry-run", "--whats-new", str(scratch / "x.md")])
        notes_refused = "read"
    except SystemExit as exc:
        notes_refused = str(exc)
    check("175: release.py reads a check's own notes only with a throwaway key, never for a release",
          "--test-key alone" in notes_refused and '"--whats-new"' in rel, notes_refused)

    proof = scratch / "proof"
    # the test release's newer version, the patch after the app's own, so no bump of VERSION meets it
    own_version, newer = server_version_of.VERSION, update_proof.next_version()
    pub = update_proof.make_key(proof / "key")
    notes = update_proof.make_notes(proof / "whats-new.md", newer, "20 October 2026")
    made = update_proof.make_release(proof / "release", newer, proof / "key", notes, {})
    good = json.loads((proof / "release" / "latest-good.json").read_text(encoding="utf-8"))
    bad = json.loads((proof / "release" / "latest-tampered.json").read_text(encoding="utf-8"))
    public = pub.read_text(encoding="utf-8")
    mac = good["platforms"]["darwin-aarch64"]
    mac_file = (proof / "release" / "Idiograph.app.tar.gz").read_bytes()
    tampered = (proof / "release" / "tampered-Idiograph.app.tar.gz").read_bytes()
    signed = minisign.verify(public, mac_file, mac["signature"])
    check("175: a test release is signed by release.py itself with a throwaway key, its manifest pointing at this "
          "machine alone, its notes the check's own, and each tampered file one byte from the true one with the "
          "true one's signature, which then does not hold",
          newer.split(".")[:2] == own_version.split(".")[:2] and int(newer.split(".")[2]) == int(own_version.split(".")[2]) + 1
          and made["version"] == newer and made["platforms"] == ["darwin-aarch64", "windows-x86_64"]
          and all(e["url"].startswith("http://127.0.0.1:8798/") for e in good["platforms"].values())
          and all("/tampered-" in e["url"] for e in bad["platforms"].values())
          and signed is not None and f"version:{newer}" in signed.split("\t")
          and minisign.verify(public, tampered, mac["signature"]) is None
          and len(tampered) == len(mac_file) and sum(a != b for a, b in zip(tampered, mac_file)) == 1
          and good["notes"].startswith("The PETs board keeps") and f"## {newer}, 20 October 2026" in notes.read_text(encoding="utf-8")
          and (proof / "release" / "latest.json").read_text(encoding="utf-8") == (proof / "release" / "latest-good.json").read_text(encoding="utf-8"),
          json.dumps(made)[:400])

    # ── C. What's new: the file in every bundle, the server's route, the line once and the sheet
    import server as server_mod
    versions = server_mod.whats_new_versions(notes.read_text(encoding="utf-8"))
    own = server_mod.api_whats_new({})["versions"]
    old_manual = os.environ.get(server_mod.MANUAL_FILE)
    os.environ[server_mod.MANUAL_FILE] = str(scratch / "nowhere" / "manual.md")
    missing = server_mod.api_whats_new({})
    if old_manual is None:
        os.environ.pop(server_mod.MANUAL_FILE, None)
    else:
        os.environ[server_mod.MANUAL_FILE] = old_manual
    check("175: What's new is docs/whats-new.md, a section a version newest first, carried beside the manual in every "
          "bundle and answered by the server as /api/whats-new, none for a copy without it",
          versions[0]["version"] == newer and own_version in [v["version"] for v in versions[1:3]] and versions[0]["date"] == "20 October 2026"
          and len(versions[0]["lines"]) == 3 and own and server_mod.VERSION in [v["version"] for v in own[:2]]
          and (own[0]["version"] == server_mod.VERSION
               or tuple(map(int, own[0]["version"].split("."))) > tuple(map(int, server_mod.VERSION.split("."))))
          and all(1 <= len(v["lines"]) <= 8 for v in own) and missing == {"versions": []}
          and server_mod.ROUTES.get("/api/whats-new") is server_mod.api_whats_new and "/api/whats-new" not in server_mod.POST_ONLY
          and conf["bundle"]["resources"].get("../../../docs/whats-new.md") == "docs/whats-new.md"
          and 'notes = whats_new or notes_file(app)' in read(tauri / "bundle.py")
          and window.notes_file() == support.source("docs/whats-new.md"),
          json.dumps(versions)[:300])
    frozen = scratch / "frozen"
    (frozen / "_internal").mkdir(parents=True)
    staged = window.stage_source(scratch / "stage", frozen, notes)
    check("175: a test build carries the check's own notes, and a build that ships the app's own",
          (scratch / "stage" / "tauri" / "docs" / "whats-new.md").read_text(encoding="utf-8") == notes.read_text(encoding="utf-8")
          and (staged / "windows" / "sidebar.bmp").is_file() and (staged / "windows" / "English.nsh").is_file())

    # ── D. the page: the line asked once, the ready line, the foot's line, and no bridge in a browser's tab
    node = shutil.which("node")
    if node:
        bits = "\n".join(js_function(app_js, n) for n in ("updLine", "updDownloading", "updWhen")) + "\n" + \
            app_js[app_js.index("const UPD_PRIVACY"):].split("\n", 1)[0]
        harness = scratch / "upd-175.js"
        harness.write_text(support.i18n_js() + "const APP_NAME = 'Idiograph';\nconst UPD = {};\nconst updAsk = () => null;\nconst updRelaunch = () => null;\n" + bits + r"""
const line = (v) => { const l = updLine(v); return l && { said: l.said, more: l.more || '', yes: l.yes || '', no: l.no || '' }; };
const out = {
  asked: line({ check: null, state: 'idle' }),
  ready: line({ check: true, state: 'ready', version: '0.9.2' }),
  available: line({ check: true, download: false, state: 'available', version: '0.9.2' }),
  byItself: line({ check: true, download: true, state: 'available', version: '0.9.2' }),
  downloading: line({ check: true, download: false, state: 'downloading', version: '0.9.2', got: 450, size: 1000 }),
  later: line({ check: true, state: 'ready', version: '0.9.2', later: true }),
  none: line({ check: false, state: 'none' }),
  noView: line(null),
  today: updWhen(new Date().toISOString()).startsWith('today at '),
  bad: updWhen('not a time'),
};
console.log(JSON.stringify(out));
""", encoding="utf-8")
        run = subprocess.run([node, str(harness)], capture_output=True, text=True, encoding="utf-8")
        try:
            got = json.loads(run.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            got = {"error": (run.stdout + run.stderr)[-400:]}
        two = lambda key: bool((got.get(key) or {}).get("yes")) and bool((got.get(key) or {}).get("no"))  # noqa: E731
        check("175: the home screen's line asks once with two answers, offers a newer version only when it does not "
              "download by itself, says how far a download has got, says the update is ready with two answers, and "
              "Later hides it",
              two("asked") and two("ready") and two("available") and "0.9.2" in got["ready"]["said"]
              and got.get("byItself") is None and "45%" in (got.get("downloading") or {}).get("said", "")
              and got.get("later") is None and got.get("none") is None and got.get("noView") is None
              and got.get("today") is True and got.get("bad") == "", json.dumps(got)[:500])
        wharness = scratch / "window-175.js"
        wharness.write_text(r"""
const src = require('fs').readFileSync(process.argv[2], 'utf8');
function load(withIpc) {
  const t = { invoked: [], events: [] };
  const win = {
    __IDIOGRAPH_OS__: 'macos', __IDIOGRAPH_SEED__: { local: {} },
    addEventListener: () => {}, dispatchEvent: (e) => { t.events.push(e); return true; },
  };
  if (withIpc) win.__TAURI_INTERNALS__ = { invoke: (cmd, args) => { t.invoked.push([cmd, args]); return Promise.resolve({ here: true, state: 'idle' }); } };
  global.CustomEvent = class { constructor(type, o) { this.type = type; this.detail = (o || {}).detail; } };
  global.document = { getElementById: () => null };
  new Function('window', 'document', src)(win, global.document);
  return Object.assign(t, { win });
}
(async () => {
  const out = {};
  const tab = load(false);
  out.tab = { bridge: typeof tab.win.idiographUpdate, told: typeof tab.win.__idiographUpdate };
  const w = load(true);
  out.answer = await w.win.idiographUpdate('set', { check: true, download: 'yes', place: { 'idiograph-home': 'p1' }, other: 1 });
  await w.win.idiographUpdate();
  w.win.__idiographUpdate({ here: true, state: 'ready' });
  out.calls = w.invoked.map((c) => c);
  out.events = w.events.map((e) => [e.type, e.detail && e.detail.state]);
  console.log(JSON.stringify(out));
})();
""", encoding="utf-8")
        run = subprocess.run([node, str(wharness), str(tauri / "window.js")], capture_output=True, text=True, encoding="utf-8")
        try:
            got = json.loads(run.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            got = {"error": (run.stdout + run.stderr)[-400:]}
        check("175: window.js gives a browser's page no bridge at all, and in the window hands the page's asks to the "
              "command updates with only what it takes, and each word of the window's to the page as an event",
              got.get("tab") == {"bridge": "undefined", "told": "undefined"} and got.get("answer") == {"here": True, "state": "idle"}
              and got.get("calls") == [["updates", {"op": "set", "check": True, "place": {"idiograph-home": "p1"}}],
                                       ["updates", {"op": "read"}]]
              and got.get("events") == [["idiograph-update", "ready"]], json.dumps(got)[:500])
    else:
        skip("175: the page's update line and window.js under node", "node is not on this machine")

    # ── E. the installer's words file, every name Tauri's installer script asks for
    nsis = conf["bundle"]["windows"]["nsis"]
    english = read(src_dir / "windows" / "English.nsh")
    named = re.findall(r"^LangString (\w+) \$\{LANG_ENGLISH\} ", english, re.M)
    check("175: the installer's own words file is laid over Tauri's and keeps every name its installer script asks for",
          nsis.get("customLanguageFiles") == {"English": "windows/English.nsh"} and sorted(named) == sorted(TAURI_LANG_NAMES)
          and "{{" not in english, str(sorted(set(TAURI_LANG_NAMES) ^ set(named))))


    # ── G. the key's password off every command line
    if sys.platform == "win32":
        skip("175: key_prompt.py on a terminal of its own", "a terminal is made on a Mac or Linux alone")
    else:
        import key_prompt
        stand = scratch / "stand-in-cli"
        record = scratch / "cli-record"
        stand.write_text(f"""#!/bin/sh
# Tauri's CLI as the check stands it in: it asks for a password twice on its terminal, as minisign asks
echo "args: $*" > "{record}"
echo "ci: ${{CI:-none}}" >> "{record}"
echo "Please enter a password to protect the secret key."
printf 'Password: ' > /dev/tty
stty -echo < /dev/tty
read first < /dev/tty
stty echo < /dev/tty
printf '\\nPassword (one more time): ' > /dev/tty
stty -echo < /dev/tty
read second < /dev/tty
stty echo < /dev/tty
[ "$first" = "$second" ] || {{ echo "passwords don't match!"; exit 1; }}
echo "given: $first" >> "{record}"
echo "Your keypair was generated successfully"
""", encoding="utf-8")
        stand.chmod(0o755)
        secret = "dogsAtHome40lettersAndDigits1234567890ab"
        old_ci = os.environ.get("CI")
        os.environ["CI"] = "true"
        try:
            code, said = key_prompt.run(secret.encode(), [str(stand), "signer", "generate", "-w", "x"], wait=60)
        finally:
            if old_ci is None:
                os.environ.pop("CI", None)
            else:
                os.environ["CI"] = old_ci
        recorded = record.read_text(encoding="utf-8") if record.exists() else ""
        check("175: key_prompt.py types the password at each of the CLI's two prompts on its terminal, never in its "
              "arguments, takes CI out so the CLI asks, and says the CLI's words with the password never among them",
              code == 0 and f"given: {secret}" in recorded and secret not in recorded.split("given:")[0]
              and "ci: none" in recorded and b"generated successfully" in said and secret.encode() not in said,
              recorded + said.decode("utf-8", "replace")[-200:])
        sealed = minisign.make_secret("a password")
        (scratch / "k").write_text(sealed, encoding="utf-8")
        (scratch / "pw").write_text("a password", encoding="utf-8")
        (scratch / "pub").write_text(minisign.open_secret(sealed, "a password").public_key(), encoding="utf-8")
        raw = bytearray(base64.b64decode(base64.b64decode(sealed).decode().splitlines()[1]))
        # a key of a check's own made with no password, as the CLI makes one with CI set: its secret plain
        seed, keynum = bytes(range(32)), bytes(range(8))
        secret = seed + minisign.public_of(seed)
        plain = keynum + secret + minisign._checksum(keynum, secret)
        bare_raw = (minisign.ALG + b"\x00\x00" + minisign.CHECKSUM + bytes(32) + minisign.OPSLIMIT.to_bytes(8, "little")
                    + minisign.MEMLIMIT.to_bytes(8, "little") + plain)
        (scratch / "bare").write_text(minisign._wrap("rsign encrypted secret key", base64.b64encode(bare_raw).decode()), encoding="utf-8")
        (scratch / "bare.pub").write_text(minisign.open_secret((scratch / "bare").read_text(encoding="utf-8"), "").public_key(), encoding="utf-8")
        check("175: the key made is kept only when it is sealed under its password and opens to its own public half",
              key_prompt.opens(scratch / "k", scratch / "pw", scratch / "pub") is None
              and "does not open" in (key_prompt.opens(scratch / "k", scratch / "pub", scratch / "pub") or "")
              and "no password" in (key_prompt.opens(scratch / "bare", scratch / "pw", scratch / "bare.pub") or "")
              and "do not match" in (key_prompt.opens(scratch / "k", scratch / "pw", scratch / "k") or "") and len(raw) == 158)

    # ── H. GitHub's update job went with tauri.yml before the public copy (21 October). update_proof.py and
    # drive_update_windows.py stay in packaging/tauri for a later workflow

    # ── I. no study's participant named in what this build ships
    new_text = "\n".join([update_rs, english, app_js[app_js.index("Idiograph's own updates, and What's new"):app_js.index("window.openWhatsNew = openWhatsNew;")],
                          read(tauri / "update_proof.py"), read(tauri / "drive_update_mac.py"), read(tauri / "drive_update_windows.py"),
                          read(tauri / "drive_windows_four.py"), read(tauri / "draw_pictures.py"), read(support.source("packaging/key_prompt.py"))])
    check("175: what this build ships names no study's participant",
          not any(re.search(rf"\b{n}\b", new_text) for n in STUDY_PSEUDONYMS))
