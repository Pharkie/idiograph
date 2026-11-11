# Idiograph internals

How Idiograph works underneath, for whoever runs a trial server, changes the code or checks a
claim the manual makes: how it starts, the files it keeps, the API the page calls, how a workbook
is written, the tests, the source files and the known gaps. What each screen does is in the
[manual](manual.md), and how to install and start the app is in the [README](../README.md).
How it looks, its tokens, its components and the rules that hold them, is in [design](design.md).

All three phases of the first plan are built. Every AI feature sits
behind one switch in settings, AI features, and is off until you turn it on.

The code and the files keep `turn` in their names, `S.stops`, `turnHtml`, `/api/edit-turn`,
`turnsDone`, the `turn` command and `turn_show`, and the UI says passage, the IPA book's word for one
person's stretch of talk, since 15 October.

## Running it

The app's folder runs in two layouts. In the repo it is `Tools/idiograph`, two folders below the
root, whose `.venv` it runs on, and from the root:

```
.venv/bin/python Tools/idiograph/server.py
```

A tab opens at `http://127.0.0.1:8765`. Double-clicking `run.command` in Finder does the same
thing, and `run.sh` and `run.bat` cover Linux and Windows. Stop it with Control-C.

A downloaded copy is the folder alone: GitHub's copy is `git subtree split --prefix=Tools/idiograph`,
so the app's files sit at its top, with its own `.venv` beside them. Each run script finds the app's
folder from its own place, and the `.venv` there first, then two folders up, and starts the server
from the folder that holds it. `run.command` hands over to `run.sh`. With neither, the first run makes `.venv`
beside the app with the first Python it finds of 3.11 or later, `py -3` and then `python` on
Windows, installs openpyxl at the version `packaging/build_mac.py` pins and starts. It is made as
`.venv-setup` and renamed `.venv` once openpyxl is in it, so a failed or stopped setup leaves
nothing a second run could take for a good one. No Python, or one older than 3.11, gets a plain
line naming python.org, and on Windows the tick "Add python.exe to PATH" in its installer.
`source_base` in `server.py` decides where a relative path starts: at the repo root for a folder
under one called Tools with no `.git` or `.venv` of its own, and at the app's folder otherwise.

On the Mac, `Idiograph.app` in the app's folder is the way to start it from the Desktop or the Dock. The
Desktop shortcut is a symlink to it, and dragging the bundle onto the Dock keeps it there. A
double-click starts the server in the background, with no Terminal window, and the tab opens as
above. A second double-click while it runs offers Stop, Restart and Open, with Open the default.
Stop ends only the process listening on the port, and only when that process is Idiograph's server.
Settings carries Restart Idiograph and Quit Idiograph as well, at its foot, however the server was
started (see Restart and Quit, below), and with the tick at the end of General on the server quits by
itself a few minutes after its last tab closes (see Quitting after the last tab, below). The bundle runs on the `.venv` beside the app's files when
there is one, from the app's folder, and else on the repo root's, from the root, as the run scripts
do. With neither, its dialog says to double-click `run.command` once, which sets one up.

The server's output goes to `~/Library/Logs/Idiograph/idiograph.log`, and its process number to
`idiograph-8765.pid` beside it. Both sit outside iCloud Drive because macOS lets a script launched
from Finder read or change a file in iCloud Drive only when the script made that file. The server runs as
its own process and reads and writes the repo as usual. If nothing listens within ten seconds, a
dialog shows the last lines of the log. Every launch also writes a line to
`/tmp/idiograph-launch.log` before it does anything else, then a second with the outcome or the
reason it stopped, so a launch that fails without a dialog still leaves its date and its reason. An
antivirus such as Bitdefender may block a new or rebuilt bundle on its first launch until it is told
to trust it.

`family/make_app.py`, run with any Python 3 from the app's folder, rebuilds the bundle in place, icon
included, and `--desktop` also makes the Desktop symlink, replacing an old symlink and refusing
anything else of that name. The launcher is the `LAUNCHER` text in `family/make_app.py`, so change it there
and rebuild. `IDIOGRAPH_PORT` and `IDIOGRAPH_ARGS` point a trial launch at another port and case
root, for example `IDIOGRAPH_PORT=8770 IDIOGRAPH_ARGS="--no-browser --root /tmp/scratch"
Idiograph.app/Contents/MacOS/Idiograph` from the app's folder.

Options: `--port`, `--no-browser`, `--verbose`, `--root "<folder>"` for a run of that one
project, whatever `config.json` names (it is not written there), and `--config "<file>"` to read and
write the settings in that file instead of `config.json`, so a smoke server's Save never lands on
the live settings. A run with `--root` also keeps its
recent list in memory and never reads or writes `state.json`, so a trial or smoke server cannot put
back the order of the live list. Until 30 September 2026 a smoke run copied the file back when it
finished, which undid any case opened on the live server while it ran. A run with `--config` and no
`--root` keeps its recent list beside that file under the app's own name (`server.state_beside`):
`state.json` for Idiograph, `state.sift.json` for Sift, `state.trace.json` for Trace. Until 21
October 2026 such a run wrote the list beside the code, the repo's own.

The only dependency is openpyxl, with no lxml in either installer or in a run from source, so
openpyxl writes every part with the standard library's ElementTree there, where the repo's own
venv has lxml and writes with it. `shared_strings.py` sets every string out as Excel writes it
whichever of the two wrote it, and area 174 checks the round trip on the shipped writer (17
October). Without lxml, et_xmlfile opens each sheet's temporary file by its path in text mode,
and Windows wrote every line feed there as a carriage return and a line feed, kept since 17 October
as one more carriage return a save. `shared_strings.keep_line_feeds`, in place once the module is
imported (`workbook.py` and `convert.py` import it at their head), opens that path in binary mode,
and area 174 plays Windows's text mode on any system to check it (20 October). Everything else is the Python standard library, so the whole
folder can be zipped and run anywhere with Python 3.11 or later. A shared copy ships without
`config.json`, which carries this machine's projects, corpus and reference paths and is gitignored,
and without `state.json` and `.env`. On its first run the server writes `config.json` from
`shipped_config()`, the defaults with no project, no corpus and no reference set, so the examples
rail and the prompt's `{examples}` draw on the demo's own statements until `corpus` and
`gravity_reference` point at files of the new owner's.

**Windows.** Read through, not yet run there, 14 October: the file lock is `msvcrt.locking`, the
folder dialog is a typed path, a path typed in quotes, as Windows copies one, is taken without them,
a path on the screen has its case folders scrubbed at backslashes as at slashes, a key goes to
`.env` beside the app with no keychain, Show in Finder is a Mac's alone, Restart starts the server
anew in `run.bat`'s window, since Windows cannot run a program again in one process (`spawn_again` in
`server.py`), Quit ends the server, and the Windows app's files live in `%APPDATA%\Idiograph` (see
The Windows app, below). Nothing leans on Windows's code page: every file the app opens, reads or
writes names UTF-8, and so does every program's output it reads, the command line, the MCP server
and the server write UTF-8 to a pipe or a log (`app_folders.utf8_streams`), and every file the app
writes ends its lines in LF, so a case's files come out byte for byte the same whichever system
wrote them. The suite scans the source for both (area 144). `.gitattributes` gives the batch files
CRLF in a checkout and in GitHub's zip, which cmd needs for their labels, and the scripts LF.
`.github/workflows/windows-installer.yml` runs the suite with Python 3.11 on GitHub's Windows
machine on every pull request, on a version tag and by hand, never on a push to main (23 October, so a release runs once) or another branch's (cloud builders push branches), then builds the Windows app's installer by hand and on a version
tag, and runs the suite on its Mac by hand alone, when asked, since a Mac minute counted as ten while the
repository was private (it is public from November 2026). It runs once the copy is pushed.

**The Mac app.** For a Mac with nothing installed, `packaging/build_mac.py` builds `Idiograph.app`,
Idiograph in a window of its own that carries its own Python, openpyxl, the code and the static page,
`Idiograph.dmg` to ship it, and `Idiograph.app.tar.gz`, the app as Tauri's updater takes it, from a
clean checkout in one command, run from the app's folder with Rust and Node.js installed:

```
python3 packaging/build_mac.py
```

The Mac app is for Apple Silicon Macs alone (M1 or later) since 0.9.23 (Adam, 9 November 2026, relfix):
PyCA `cryptography` has had an Apple Silicon wheel alone since 49.0.0, and cffi, which it loads, no
wheel with both architectures, so 0.9.23's universal2 freeze was refused. An Intel Mac keeps the copy it
has, which goes on working, and is offered no update. `build_mac.py` refuses to run on an Intel Mac
(`apple_silicon`) and makes a build venv in `build/venv` with PyInstaller, openpyxl, certifi and
cryptography at the versions it pins, from the newest python.org Python of 3.11 or later when one is
installed and else the Python running it, refused unless it runs as arm64 (`runs_arm64`).
It stages the demo as Reset demo leaves it, its three cases from `demo/pristine/` with their boards
and the GETs file, and Juno's recording, the checkout's when the app has made one there and else spoken
by `make_demo.py` into `build/recording`, and `config.json` from `server.shipped_config()`, which
names no root. PyInstaller freezes `packaging/mac_launcher.py` and every module it reaches, with
`template/Transcript template.xlsx` among its data, into one folder, the server, and the build runs
its `cli --help` before it goes on. Since 17 October (the third Tauri build) Tauri's bundler makes the
rest, through `packaging/tauri/bundle.py`, where PyInstaller's own app and `hdiutil`'s image stood: the
window with the frozen server inside it as `Contents/Resources/server`, its links kept, the disk image
with the app and a link to /Applications, made since the fourth build by dmgbuild (below), and the update file, all arm64 alone: PyInstaller's
`target_arch` is `build_mac.ARCH`, the window is built for this Mac's own Rust target, and the build
stops if the app's executable is for anything else. All three land
in `dist/`, and `build/` and `dist/` are gitignored. What of `build_mac.py` stays is everything before
the app itself: the build venv, the stage, the freeze and the choice of identity. `--out <folder>` puts
the two folders elsewhere, `--this-mac` is kept for older commands and changes nothing, and
`--test-app` builds the test app, Idiograph Test. With a Developer ID Application identity in the login
keychain and the notarytool profile `idiograph-notary` stored, PyInstaller signs the server's every
binary with it and Tauri the app, both with the hardened runtime, and the image is signed, notarised and
stapled. Without both every part is signed ad hoc, and the build says in one line that it is unsigned.

The frozen server's executable is `mac_launcher.py`, the launcher of the browser's days in Python,
which the window runs with `--serve`, and which `Idiograph cli` and `Idiograph mcp` hand over to. Run
by itself it is still that launcher: the server in the background and the browser opened, Stop,
Restart and Open on a second double-click, the log and the pid file in `~/Library/Logs/Idiograph` and
the line in `/tmp/idiograph-launch.log`. Only a server run with `--serve` is the app's own, so with
port 8765 held by anything else, a server run from the repo included, it starts on the next free port.
Nothing writes inside the bundle. `app_paths` in `server.py` is the one place that decides, with the
folders from `app_folders.py`, which the window and the two launchers read too: frozen, `config.json`,
`state.json`, `.env` and the demo live in `~/Library/Application Support/Idiograph`, the first run
copies the shipped `config.json` and the demo there, and Reset demo restores from the bundle's own
copy. Sift's and Trace's first run (`first_run`, `paths["app"]`) copies no demo into their own
folders, which have no use for its participants (23 October). On Linux (8 November) `app_folders.folders` follows XDG: data in `$XDG_DATA_HOME/Idiograph`, logs in `$XDG_STATE_HOME/Idiograph/logs`, config and cache beside them, a relative variable ignored, and `move_legacy` moves a source user's `~/Library` folders there once, whole and never onto a folder holding files (`app_paths` calls it, the Tauri shell's `logs_dir` names the same logs folder). Show in Finder runs `xdg-open` there (area 346). Run from source, every path is the one this page gives. The window takes the server's options,
so a trial runs `dist/Idiograph.app/Contents/MacOS/Idiograph --port 8789` with `HOME` at a scratch
folder, and never through the Finder, which would take port 8765.

**Three apps from one codebase** (20 October, the first build of the split). `app_identity.py` names
the family's three apps, Idiograph, Sift and Trace, each with its name, bundle id
(`uk.co.adamknowles.idiograph`, `.sift`, `.trace`), data folder (`Idiograph`, `Sift`, `Trace` under
Application Support or `%APPDATA%`), port (8765, 8766, 8767), mark, colour token, What's new file,
releases repository and update endpoint, and its version from `versions.json` (Idiograph 0.9.24, Sift and
Trace 1.0.0). A run is one of them: `--app` on `server.py`, `cli.py` and `mcp_server.py`, Idiograph when
it is left out, and frozen, the launcher's own name (`app_identity.from_executable`). `server.use_app`
sets the run's folders, files, version and What's new, and `app_folders.folders` and `server.app_paths`
take the app. From source Sift reads and writes `config.sift.json` and `state.sift.json` beside
`config.json`, Trace `config.trace.json` and `state.trace.json`, all gitignored, and the key file beside
the code is the one all three share. The first start of Sift or Trace (`server.first_start_copy`, the keys
in `app_identity.first_start_plan`) copies from Idiograph's settings the AI settings, the appearance where
the file has it, Celebrations and Sound and the closing tick, for Sift also its databases, the Unpaywall
email and the Zotero library, and from Idiograph's recent list Sift's projects with the run each had open,
or Trace's projects. It only reads Idiograph's files and runs once, `first_start_copied` in the new app's
settings saying so. A run given `--config` copies from `config.json` and `state.json` beside that file,
never the ones in daily use. The key stays in the keychain under `ANTHROPIC_API_KEY`, so all three see
it, and where there is no keychain Idiograph's `.env` is copied once into the new app's folder. A
launcher's fallback from a held port (`app_identity.fallback_ports`, the Python launchers' `choose_port`
and the window's `tried_ports`) never takes another app's port of the three. With no `--app` every path,
port, file and answer is as before.

**Each app its own routes** (20 October, the second build of the split). `ROUTE_APP`, beside the
handler in `family/server.py`, gives every route its one owner (a table of each app's paths, `ROUTES_BY_APP`,
stood beside it until the sixth build of the family codebase, 23 October 2026): `shared` (`/api/server`, which now answers `app`,
`/api/beat`, `/api/settings`, `/api/key`, `/api/key-status`, `/api/models`, `/api/feedback`,
`/api/whats-new`, `/api/search`, `/manual`, `/licence`, the icon and `/design`), Idiograph's (the cases, statements,
boards, GETs, projects, import, export, the recording, the print views, the demo, the statements' AI and
`/api/mcp`), Sift's (`/api/sift`, `/api/sift-review`, `/api/sift-search`, `/api/databases`, `/api/zotero`,
`/sift/pdf`) and Trace's (`/api/trace`, `/api/trace-project`, `/trace/pdf`). The page's own files are in
no line and every app serves them. Another app's route, a GET or a POST, answers 404 with
`{"error", "app", "port"}` naming the app that has it (`not_here`), before the route runs. `SERVES_TOO`
let Idiograph answer Sift's and Trace's routes as before until the cutover of 23 October 2026, which set its
one line to `()`, and since it Idiograph's server refuses theirs by name as theirs refuse its. Idiograph's
own build ships neither Sift's nor Trace's routes module, so their paths are also written out in
`app_identity.ROUTES`, which `route_owner` reads for a path no module registered, and area 222 holds that
table to what the modules register. Idiograph's routes have no such table, so Sift's and Trace's own builds
answer one of them with the plain 404. `/api/settings`
saves General's keys and the app's own (`SETTINGS_BY_APP`, `settings_for_app`), so Sift's never takes
Idiograph's interviewer or board settings, and since the sixth build the settings hooks run for the app's own
alone (see The family's folders). `/api/search`
refuses another app's scope by name, and Everything holds only the projects and kinds of the apps the
run answers for (`own_kinds`). `unplaced_routes` names any route the table leaves out, which area 222
checks. Area 222 also plays a live review's calls (`sift-search` drop and save, `sift` read and
decide, `sift search strings` and `sift search run --draft --date --follows` through `cli.py`) on an
invented review against an Idiograph server and a `--app sift` server, and every file of the review is
the same byte for byte, its ISO times alone masked.

**One page per app** (20 October, the third build of the split). The server serves `index.html` through
`own_page`, which sets `data-app` on its root and the app's name as its title, so the first paint is the
app's. Whatever in the page belongs to one app carries `data-only="idiograph"`, `sift` or `trace` (each Home
section, the days, Settings' tabs and AI switches, the lockups and ledes), and one rule in `style.css` hides
another app's. `app.js` reads `APP` and `APP_NAME` from the root: `loadLibrary` asks `/api/cases` on
Idiograph and `/api/home` (shared: settings, feedback, version and the app's own `reviews` or `traces`) on
the others, `drawPick` draws only the app's section, `windowRecent` hands only its projects, and
`/api/guidance`, `/api/days`, the bench's sample and the projects' and GETs' panes are asked on Idiograph
alone. `/api/family` lists the other two apps (`family_rows`, each `installed` by `installed_at`: a Mac's
Applications folders, Windows's `%LOCALAPPDATA%\<Name>`, and from source always), and `/api/family-open`
(POST, own page) runs `family_open_plan` through `family_go`, or `FAMILY_OPENER` in a check: an installed
build opened by its bundle id or run, from source that app's `server.py --app` started detached unless its
port already answers, and one not installed its releases page in the browser. Settings' categories are
`PANES_BY_APP`, `showPane` sending another app's to General, and the panes `pane-databases`, `pane-zotero`,
`pane-gets` and `pane-ai` are new, Sift's former pane now its Projects. Since each app ships alone (train 53)
its page holds its own panes and cards and the family's, so `showPane` passes over a pane of `PANES_ALL` the
page lacks, and `overlaysHere` gives the cards of `OVERLAYS` the page holds, which `anyOverlayOpen` and Escape
read (panefix, 26 October 2026: before it Settings threw and never opened on any app's page, and on Sift's and
Trace's every key past the cards threw). `/api/settings` takes `appearance`
(`APPEARANCES`), which the page sends the moment a row is ticked (`themeKeep`) and reads at boot with
`{"op": "read"}`, which writes nothing (`themeFromSettings`), so opening the page leaves config.json as it
was. `appearance` sent alone writes that one key into the file as it stands (`write_config_keys`), never
the defaults, and nothing when the file already holds it. And `ai_features_off`, each app saving only its own of `app_identity.AI_FEATURES` (idiograph
statements, pets, gets, sift proposals, trace passages). `server.ai_on(cfg, feature)` guards each feature's
calls, `api_suggest`, `api_themes_ai`, `api_gets_ai`, Sift's proposals and Trace's passages, and `ai_state`
takes the feature, PETs' or GETs'. The page's `aiFor` and the body's `ai-off-<feature>` classes hide a
feature's controls. Search sends `app`, and Everything then holds that app's projects alone. Area 223.

**The Preview Edition** (21 October, Adam's lockup from the launch video). `server.PREVIEW_EDITION`, a constant
and no setting, makes `own_page` add `data-edition="preview"` to Idiograph's root (never Sift's or Trace's). Every
`.pe-stamp` in `index.html` stands hidden unless the root says `data-app="idiograph"` and `data-edition="preview"`:
one after Home's lockup (`.wordmark .pe`, the lockup 32px high while the stamp shows), one after About's
(`.about-lockup`, Idiograph's About showing it in place of its kicker and `#about-title`, which stays as the
dialog's label and is Sift's and Trace's heading), and one inside each bar's `.rail-home` (`.pe-bar`, hidden
below 560px). The stamp is HTML text in the crux token, tilted -4 degrees, so it follows light and dark. Home's takes the
launch film's size and place (22 October, Adam's choice): `--pe-m`, the mark's height (32px), sets its type at
46/180 of it, its right edge 46/180 past the name's end and its top 50/180 under the lockup's foot, its rule,
round and padding in the film's ems, so the film's title card and Home stand alike, at rest and as it is stamped on. Its
`.pe` holder keeps room for it in padding (`--pe-room`), so the lockup's box holds the stamp. Setting the
constant to False ends the preview everywhere, the server restarted. Home's `.pe-note`, the panel saying what the
preview means, right under the lockup since 22 October, follows the same root attributes, so it goes with the stamp. Its warning sign (22 October) is an
inline SVG, `.pe-warn`, in the crux token, the words in a span beside it, the panel a flex row. Its words,
`page.preview_note`, end since 29 October (supportcard2, Adam: a private alpha by invitation) on the Support card's
private line in its own words, "Please keep it to yourself for now: don't share it or post about it.", and area 289
checks that the note and the card both carry it.

**The mark coming in on Home** (22 October, from the launch film's title card, launchvideo9's `stamp.js` and
`bounce.js`). Whether it plays is decided before the first paint: a small inline script in `index.html`'s head puts
`home-mark-due` on the root when the app is Idiograph, the tab's `sessionStorage` has no `idiograph.homeMark` and
the system does not ask for reduced motion. While the class is there `style.css` hides the lockup's `<use>`, its name
`<path>` and `.pe-stamp` (with a 5 s CSS fallback, 4 s until 23 October, that shows them should the script never run), so the resting
mark never paints first. `homeMarkPlay` in `app.js`, called by `boot` when the page opens on Home (no spot taken
back from a reload or a restart), sets `idiograph.homeMark` and plays, or takes the class off at once. Once-per-open
is page-only: a reload, a restart and every later return to Home leave the mark still, and a new window or a fresh
launch plays it. It reads the lockup's own mark square from the `<use>`'s `getScreenCTM` (the `<use>`'s bounding
box is the strokes' bounds, not the 15 units) and lays a cover, `.home-mark`, absolutely over it inside
`.wordmark .pe` (out of flow, `pointer-events: none`, `aria-hidden`). The cover holds the mark's three parts as
marks.svg draws them, two brackets in a `preserve-3d` span with `perspective` and the dot in `--mark-dot`, the
mark's own orange, the film's `#F26B1D` in both themes (22 October), which marks.svg's four Idiograph symbols
and `favicon.svg` use too, while `--crux` stays the words' orange.
Since Adam's notes of the evening of 22 October it is one movement, Home's own (the film keeps its three beats
until it follows Home): the brackets from 3.2 times the size and 1.75 turns of `rotateY`, a little apart in
depth, from 0 s, landing at 1.2 s with a small thud to 1.35 s, while the dot by `homeMarkDot`, the film's
physics (`HOME_MARK_BOUNCE`: one ground at the brackets' foot, restitution 0.624 worked out so the second bounce
rises exactly to the middle, the first bounce 0.526 s), starts its fall at about 0.24 s, first touches the
ground at about 0.66 s and comes to rest at 1.35 s, the moment the thud ends. The name's `<path>` fades in from
0.15 s to 1.2 s (smoothstep). Then `.pe-stamp` is stamped on from 1.45 s to 1.8 s: its `scale` property (so its
`rotate` stays) from 1.45 down past its size to 0.93 in the first 55 per cent, then back to 1, its opacity full in
the first 15 per cent. At 1.8 s the cover goes, the inline styles are cleared and the class comes off, so the rest
is the static lockup itself.

**Seven ways in** (23 October, Adam: one of a random set, different each time, in the Pixar lamp's spirit). The spin
above is `homeMarkSpin`, one of `HOME_MARK_WAYS`: spin, pong, pinball, anagram, football and kiss
(Adam's ideas) and race (the builder's, the hop until Adam named it). `homeMarkPlay(which)` plays the way named (a string, for a recording:
whatever is playing goes and the next frame starts it, `home-mark-due` put on by the call itself), else
`homeMarkNext()`: the page's `localStorage` key `idiograph.homeMarkOrder` holds `{ left, last }`, this round's
shuffled ways not yet played and the one played last. The first of `left` plays, a new round is shuffled
(Fisher-Yates) when it is empty, its first swapped away when it is `last`, and a way no longer in the set is passed
over. A storage that throws gives a random way. Area 255 checks the rule in node, with a store of its own. The six
others are `HOME_MARK_SCENES`, each `{ letters, stamp, extra, init, frame }`, played by `homeMarkScene`: an SVG
`.home-mark` with the lockup's own `viewBox`, laid exactly over the lockup's `<svg>` inside `.wordmark .pe`, holding
the two brackets as marks.svg draws them, each in a `<g>` moved, turned and squashed about a pivot (`HM`: a mark's
unit is 15/24 of the lockup's), the dot in `--mark-dot`, and, for the three that move or light letters, IDIOGRAPH's
nine letters cut from the name's own `<path>` at its `M`s (I, D, I, O, G, R's two, A's two, P, H's three), the real
name kept at opacity 0 meanwhile. Each frame starts every piece at rest and the scene moves it, so the last frame
is the lockup and the copy goes. One gravity for all (`HOME_MARK_BOUNCE.g`), lobs by `hmLob`. Since Adam's second
notes (23 October: a pinball does not bounce off the bottom, it drains) only the spin's dot comes to rest by bouncing
off the brackets' foot line. In the six it comes into the middle by `hmHome(x0, y0, vx, vy)`, a spring a little under
critical damping from where it is and how fast it moves: a glide that slows into place, goes a fifth of a unit or
so past and settles back, never near the foot line (Football's trap is the same spring, quicker and stiffer, from the
lob's own speed). The stamp by `hmStamp`, the film's `stampOn`, about 0.29 s after the dot rests. Pong and Football
put the left bracket out past the mark only as far as the window leaves room (`K.room`), so a phone keeps it on
screen. Pinball (redone twice that day from Adam's notes) lays each bracket down about the foot of its spine as a
flipper from the first frame, with a gap of 5.5 units between them, the right flipper ending 3.6 units short of the
name's I. With 10 units or more of room on the left they rest 38 degrees down and the gap's room is taken on the
left. On a phone they rest 58 degrees down, which brings their outer ends in, and the gap sits a little further
right, so nothing reaches the window's edge. Three bumpers (`r` 1.7, faint outlines) stand over the flippers in
the mark's own room. The dot rests on the left flipper, and each flip dips 8 degrees, snaps to 20 up in 0.06 s
and sends the dot in 0.13 s to a bumper (right, left, right, then softly to the top one, peaking there), which
pulses, and each hit turns one run of neighbouring letters fully on at once (`K.lamps`: RA, ID, PH, IOG, Adam's order since his third notes), faint at
0.2 till then. At the end the flippers stand up out wide and step in, so they never sweep through each other or
the dot, and the dot glides home from the top bumper. Lengths, stamp included: spin 1.85 s, pong 2.8, pinball 3.2,
kiss 3.1, hop 2.7, football 3.2, anagram 4.4. The anagram (GO RAPID HI, no comma since Adam's notes) is sorted in
three moves, one at a time, each a bracket holding letters from the side with 2.7 units between its arms' tips
and the letter, lifting them 15 units, clear over the line (under it on a phone, where the toolbar sits just over
the name's end, the brackets coming up into place from under the line and G and the last I tossed up into theirs), carrying them and putting them down (G and the last I
let go just clear of the letter under the bracket and dropped in), while the rest of the phrase stays on its line
as words: the right takes ID to the front (ID GO RAP HI), the left takes G over O as RAP shuffles along (ID OGRAP
HI), and the right drops the last I in after ID as the word closes up under it. The phrase is laid out from a word
space after the name's D, so ID's place at the front is free from the start, with word spaces of 10 (room for a
bracket with a clear gap either side), and R A P and I D at the name's own spacing so each moves as one. Every hop
goes straight up, across high over the letters and straight down, so no bracket sweeps through a letter beside it.

**Adam's third notes** (23 October, about 12:40). The spin since: each bracket is drawn at its largest (`Z`, the
start's scale rounded up) and scaled down, so it stays sharp, in nine layers set back through a depth of 3 units
(the back ones at 0.45 ink) with its spine's outer side as a face of its own, so turned side on it reads solid. The
two circle each other in depth, on a circle seen a little from above, starting 14 units out from the middle at
up to 5 times their size and 1.5 turns round, and come in by `1 - (1 - k)^2` to 5.5 units, their own size and no
turn at 1.25 s, each turning with the circle (`rotateY`). The start's size and the circle's centre are fitted to
the room round the mark (the window's left and top, down to the element under `.wordmark`, along to 20px past the
name's end), so at 360 the circle starts over where the name will be. The depth flattens over the last 0.4 s, the
name fades in from 0.6 s, the dot by `homeMarkDot` as before, the stamp 1.5 to 1.85 s. Pong's ball is a steady
8-bit ball with no squash: `shots` lists each hit's time and place and the wall a shot comes off (unfolded about
it), six hits, then the soft return to the middle at 2.36 s that both paddles come in with. The paddles' heights
are keyed (`LK`, `RK`), with a lean of up to 8 degrees from their speed, and the left one stands only as far out as
leaves room to the window's edge. The hop's three each have their own way: the left `{ stones, lands, jumps,
home }` H, A, G, D from 0 s, home at 1.62 s, the right H, R, O from 0.45 s in leaps of three letters, leaning 12
degrees, home at 1.98 s in a high last leap, both last leaps going across before down (`1 - (1 - k)^2`) so they clear the first I, and
the dot on three times the brackets' gravity from 0.15 s, fifteen quick uneven bounces from H between the two,
back and forth on the first two letters under the right's leap, then a spring from the first I at 2.0 s to over the
middle and `hmHome` down. Pong's right paddle stands at 14 and its left leaves 6.4 units to the window's edge.
Pinball's right flipper stands up no further out than 13.4, and its unlit letters are at 0.26. Checked frame by frame for gaps with the builder's own tools.

**Adam's fourth notes** (23 October, about 16:00), which supersede the third's on the spin's layers, Pong's lean,
Pinball's start, Football's kicks and the hop's dot. The spin's brackets are real solids in CSS 3D: each stroke of a
bracket a block (`block`, its rectangle from marks.svg's own stroke, square caps and mitred corner, as its front and
back and four side faces as deep as `--d`, 2 units), all in one `preserve-3d` context with `backface-visibility:
hidden`, so the browser sorts the faces itself and an arm turned away is seen end on. A face's colour is set each
frame (`paint`) from where its normal points after the bracket's `rotateY` and a tilt of up to 17 degrees that shows
the tops early on: the ink when it faces the viewer, leaning towards the paper behind the mark as it turns away
(half way side on, a touch more for a face turned up, less for one turned down), as `color-mix` with the paper
found up the page. The ink comes in by colour, not opacity, which would flatten the 3D. Nothing is fetched and no
library is used. Pong's paddles move only up and down their own lines in the rally (no lean, no push at the ball):
they slide apart before the serve and in after it, each once lined up with the middle, and the last return leaves
at the rally's speed and eases to rest in the middle by `1 - (1 - k)^3` by 2.5 s. Pinball's dot starts at the top
of the left flipper (1.4 along it) and rolls down it from 0.22 s at five sevenths of gravity along the slope
(`K.roll`), and the first flip has no dip (`K.nodip`), kicking as the dot reaches the sweet spot. Football (`K.b`)
has a header: the left kicks to the right's foot, the right lofts it to the left's head (`K.headAt`, where the
middle of its top arm meets the dot as the left, 1.4 up in its jump, nods forward through upright), the header goes
back to the right's foot, the right taps it 2.4 out in front of itself (`K.chipX`, so its own top arm is clear) and
chips it into the middle for the trap. The right player stands at 13 and winds back only 12 degrees, so its top
stays clear of the name's I, and the left stands 9.2 units in from the window's edge on a phone, room for its wind
back. The hop's order along the way is always the left, the right, the dot: the right from 0.42 s, H, R, O, home at
1.82 s, and the dot from 0.62 s under the one gravity, three bounces, the H at 0.92 s, the G at 1.32 s and the D at
1.72 s, then over the right (home by then) to over the middle, slowing across by a quarter sine, and `hmHome` down.
Lengths now, stamp included: spin 1.85 s, pong 2.9, pinball 3.3, football 3.6, hop 2.75, the kiss and the anagram
as before.

**Adam's fifth notes** (23 October, about 17:00), which supersede the fourth's on the hop and the earlier ones on
the spin's start. The spin's circle starts as large and as far out as the room round the mark allows, up to 7 times
the size and 22 units out: `reach` walks the whole way in (61 steps, both brackets, each block's corners turned and
seen through the cover's perspective) and a halving search on one dial for the two (`fit`, the start's scale and
radius together) keeps the largest that stays in the room, the room's top now 4px under the window's top and its
foot 6px over the element under `.wordmark`. They come in by `1 - (1 - k)^1.7`, and fade in by `1 - cos(k pi / 2)`,
nothing at the start and most of it late, set as `--o` on every face (each face's own `opacity`): a block shows at
most three faces to the viewer and they never overlap, so this reads as the solid's opacity without flattening it.
`paint`'s `ink` is now 1 throughout. The dot takes the same fade, and the name now fades in from 0.85 s, once the larger circle has
passed off its first letters (at 360 they are over them till about 0.8 s). At 1280 the start is about 149px tall (127 before), at 360 about 126. Pinball's
first roll starts at 0.3 s and goes on to `K.roll.d1`, the flipper's length less the dot's radius and 0.3, nearly
its inner end, and the first kick goes from there (`launch0`, `hit0`), riding the flipper's snap at that distance;
everything after is 0.16 s later and the stamp meets the page at 3.28 s. The anagram's clock stands still for
`HM_PAUSE` (1 s) from 0.37 s, the brackets down either side of GO RAPID HI and before they shake their heads, each
leaning its top 4 degrees in towards the phrase and back meanwhile (the left from 0.47 s, the right 0.12 s after),
the landing squash run on the real clock. On a phone its word spaces are 8, not 10, so the right bracket keeps 20px from the window's edge. Its stamp is at 5.25 s, so the page's safety in `style.css` that shows the
mark, name and stamp if the script never runs is now 6 s. The hop: the right goes first, H, R, O, D (lands 0.3,
0.58, 0.86, 1.14 s) and home at 1.47 s, the left from 0.32 s, H, G, D (0.62, 0.93, 1.25 s), then over the right,
which crouches for it (to 0.39 of its height about its foot, 1.5 to 1.95 s), home at 1.74 s. Both leaps home go
across before down. The dot is a thrown ball (`K.ball`): one restitution, 0.76, for every bounce and one pace across
all the way, so the spans between bounces shrink by 0.76 (31 units from the H's left stroke to the R, then the O,
then the D's flat top at the name's x 8). The pace is worked out once so that the last arc, launched at 0.76 times
the bounce before it, ends exactly at the middle (7.5, 7.5): `vx = sqrt(g D (D - e s) / (2 (7.5 - yb)))`, D from the
D's top to the middle, s the last span, yb the ball's centre on a letter's top, about 53 units/s. It comes into
sight at 1.45 s, 0.3 s before the H, falling from its throw (its speed onto the H the bounce's over 0.76), and lands
in the middle at about 3.48 s. Its last arc comes down too steeply into the mark for the right's top arm, so the
right ducks (the same crouch, without the spread) from the D bounce and stands as the ball lands, where it is caught
by `hmHome` from its own speed, stiff (60, damping 0.9), less than half a unit of give. Stamp at 3.62 s. Lengths
now, stamp included: spin 1.85 s, pong 2.9, pinball 3.45, football 3.6, hop 3.8, the kiss 3.1, the anagram 5.4.

**The race** (Adam's notes of 23 October, about 18:00 and 18:05, which replace the hop and rename it: the way's
name is now `race`, so `homeMarkPlay('race')`). Only it changed. The right bracket, the left and the dot race to
their places, all in a hurry, in that order. Its timing depends on the window, so its `init` sets `K.stamp`, and
`homeMarkScene` takes the stamp and the end from `K` after `init` (each other way's own `stamp` as before). `K` also
carries `winR` and `winT`, the window's right edge and top, `bars`, Home's toolbar's icons and words
(`.lib-tools .bar-tool > *`), all in the lockup's units, and `unit`, the lockup's pixels to a unit. Each bracket's
way is a list of legs, `[kind, start, end, x0, y0, x1, y1]`: a run along the name's foot line, already at full pace
(`V`, at least 260 units/s, as fast as the room needs to reach the H's foot in 0.65 s), a leap onto the H's right
post (0.34 s), leaps along the letters' tops (the right R, O, D, the left G and the second I, each a lob under the
one gravity) and the leap home, across first and then down. The run starts wholly past the window's right edge,
`winR + 2.4 + V/30`, so at 60 frames a second nothing is drawn for two frames and the third shows only the
bracket's leading tip (3.6 units ahead of its middle, leaning into the run) crossing the edge (markplay8, after
the check found the right drawn 40 px inside the edge on its first frame at 360). Where the toolbar's icons stand
over the run (on a phone), the run goes lower, enough to keep 8 px clear of them. The left starts 0.3 s after the
right and overtakes it in the air near the finish. In its place a bracket is the rest pose from that frame on,
with no squash and no duck. Times at 1280: the right home at 2.32 s, the left at 2.43 s, and at 360 1.83 s and 1.95 s.
The dot (markplay8, after the check found it floating, a 0.4 s hang and a creep of small hops) bounces twice, on
the G and on the right bracket's top arm, and falls quicker than the other ways' dots: its own gravity `gb`, 1.75
squared times the one gravity, so its paths are those of a slower ball played 1.75 times as fast. The chain is
worked out backward from the middle (a search over the name's top profile, kept in the builder's notes). Off the
arm, at (9.8, -0.13), it pops up to -10.5 and drops nearly straight down, crossing the arms' middle line at the
mark's middle and going on down to it, where `hmHome` catches it (60, 0.9). Onto the arm it comes from the G, at
(57.6, 0.84), at the speed that pop needs, each bounce keeping 0.84 of its speed up, and the arm takes nearly all
of its pace across. The dot is 5.4 of the mark's units across and the gap between the arms' tips 5, so it narrows
to 0.8 of its width, drawn out 1.2 along its fall, from just above the tips to just below them. It meets the arm
1.48 s after the right lands on the H, just after the left is home. The throw meets the G falling at the speed the
bounce off it needs, from an apex 21.4 units above the lockup's top. Its pace across is chosen as the page opens:
of those that keep the ball 8 px clear of `bars` and clear of the window's top and the letters, the one nearest a
throw that enters level with the letters' tops. At 1280 that throw comes in low from the right and passes under
the toolbar, 11 px clear (886 units/s), at 360 it passes over the toolbar's icons, 11 px clear (290). Apexes after the throw's:
14.8 and 10.5 units above the lockup's top. Stamp 0.2 s after it reaches the middle. Lengths, stamp included:
3.2 s at 1280, 2.7 s at 360.

**The head's order** (22 October, Adam's notes). `.lib-head`'s grid: the lockup (`mark`), the Preview Edition's
`.pe-note` right under it (`note`), the line (`lede`) and the points (`points`), the days in the right column
from the note's row down, and under 560px one column, the days last. One grid since 5 November (homehead, Adam): the
head's column is `.lib-body`'s, 1080px at most with the gutter, so both share one left edge and one right edge. Its
top row, `.lib-top` (`top`, both columns), is a flex row of `.wordmark` and `.lib-tools`, the lockup 3px lower than
the tools, its mark's ink level with the icons'. Since headroom (6 November 2026, Adam) the row stands the lockup's
clear space down: `--head-top` is `--mark-h` less those 3px, `--mark-h` being the mark's height, 24px and 32px on
Idiograph's Home while the Preview Edition's lockup is drawn at 32 (`html[data-app="idiograph"][data-edition="preview"]
.lib-head`, beside that lockup's own size), so the lockup's top is at least its mark's height under the page's top, the
bottom of the window's title bar, at every width and zoom, and the tools stand level with it as before (they were 11px
under the title bar, the lockup 14). The rule is docs/design.md's Marks, Clear space, which measures each place
the lockup stands: Home's head and the project page's, which share `.lib-head`, About (35px inside the card's edge for
a 28px lockup, its card's padding and border, and `.about-card` takes 28px of padding on a phone's narrow card, where
the other cards' 26px and 18px left it short) and the bars (15px for a 15px lockup, centred in a 46px bar, exactly and
no more). To the left the head and `.lib-body` take `--home-edge` (set on `#library`: 32px from 560px of page, the page's
`--gutter` below) for their padding and `max-width: calc(1048px + 2 * var(--home-edge))`, so the lockup, the preview
box, the line, Projects and a project page's way back and name keep one left edge 32px in at every width down to the
app's smallest window, 720px, at Large (576px of page) too, the column 1048px wide so a wide window is as it was
(headroom, Adam, 6 November 2026: margin 32 at every width), and the lockup's space to its left is at least its mark's
height, the Preview Edition's 32px included. Area 333 measures the top space in a real browser at 1280,
720, each at Large (125%) as 1024 and 576 CSS pixels of page, and 360, and the left space at 1280, 1050, 1024, 720 and 576, in Idiograph's Preview Edition, a plain
Idiograph and Sift's and Trace's lockups, each width in a frame of its own. The tools' words follow the bars' rule, shown from 761px by
the same selectors as `.screen > .rail`, and `barLockups` hands `.lib-top` to `barFitWatch`, so `barFit` sets
`.bar-fit-words` when the row overflows. `homeMarkSpin` reads the room under the mark from `.lib-top`'s next
sibling. `.pe-note` fills its column up to 58em, about 110 characters a line at 14px, four lines at 1280, and up to
960px it takes both columns (`note note`) with the days beside the line and the points. The days' top is the
note's (`margin-top: 22px`, 26px beside the line). Idiograph's line is "Software for
Interpretative Phenomenological Analysis" (siteremix, Adam, 11 November: the line says IPA alone, and thematic
analysis is left for people to find, in place of methods2's "and thematic analysis" of 2 November). `.lede` wraps balanced
(`text-wrap: balance`), and `.lede-points` is as wide as its items (`width: fit-content`). Idiograph's points
are the film's, Free, Open source, No cloud and Flexible, Built for IPA taken out on 2 November (methods2, Adam,
option B: the app is for thematic analysis too), its items marked `data-only`, and Sift's and Trace's keep Free, Open source, Flexible and
No cloud (22 October). Each item's dot is its own `::before`, set absolutely in the flex `column-gap` at its left
(`--lp-sep`), which flex leaves only between items on one line, and the list's `clip-path` cuts away the dot of an
item that starts a line, so the row wraps cleanly at any width. Open source, No cloud and Flexible are one item
since 5 November, `.lp-rest`, its spans each after the first with an inline dot of its own, so the row wraps as two
groups and never leaves a word alone (homehead).

**The Ko-fi button** (22 October, Ko-fi's own artwork since that evening, Adam's ask). Inside the points' first
item, `li.lp-free`, beside Free on every app's Home: `a.kofi`, Ko-fi's button as its widget (`Widget_2.js`,
`kofiwidget2`) draws it, copied into the app, made about half its size and quieter on 26 October (Adam: too
dominant as the only coloured thing on the page), 22px tall in place of 40. A pale wash of Ko-fi's blue
`#72a4f2` (`--kofi`, `#E0E6F0` light, `#23272E` dark) with a 1px edge of the blue (`--kofi-edge`) in place of
the shadow, its words "Support me on Ko-fi" in a deeper blue (`--kofi-ink`, `#2F5A9C` light, about 5.5 to 1,
`#9EC0F5` dark) in Quicksand 700 at 11px, letter-spacing -0.1px, line-height 20px, padding 0 8px, radius 5px,
opacity .85 on hover, its title "Support me on ko-fi.com". Before the words `img.kofi-cup`, the cup with the
heart, 15 by 10 with 4px after it, alt "Ko-fi donations", which `kofi-wiggle`, Ko-fi's own keyframes, grows and
rocks once every 3 seconds. The system's reduced motion stops it with every other animation (the
`prefers-reduced-motion` block at the foot of `style.css`). A plain link to Adam's Ko-fi page with `target="_blank"`, which the
window opens in the system's browser as it does About's address. No script or frame from Ko-fi and nothing
fetched from Ko-fi, Google Fonts or a CDN: the page holds the local API to the participants' files, so the
artwork and the face are files of the app's own, which `packaging/build_mac.py` names in `FAMILY_VENDORED`:

| File | Source | Version, date |
| --- | --- | --- |
| `family/static/vendor/kofi/cup-border.png` (285 by 229) | `https://storage.ko-fi.com/cdn/cup-border.png`, Ko-fi's artwork | Last-Modified 18 Nov 2024, fetched 22 Oct 2026, sha256 `36c6b7a7...ca2c33` |
| `family/static/vendor/quicksand/quicksand-latin-700-normal.woff2` | `https://cdn.jsdelivr.net/npm/@fontsource/quicksand@5.3.0/files/quicksand-latin-700-normal.woff2` | Fontsource 5.3.0 (19 Jul 2026), fetched 22 Oct 2026, sha256 `00bfba44...b28ae7` |
| `family/static/vendor/quicksand/OFL-quicksand.txt` | `https://cdn.jsdelivr.net/npm/@fontsource/quicksand@5.3.0/LICENSE`, SIL OFL 1.1 | as the face |

`style.css` declares the face with `@font-face` (`font-display: swap`, Latin only, the button's words being
Latin). `NOTICE.md` credits both. Under 560px the item takes its own line and the next item drops its dot.

**Support Idiograph** (supportcard, 28 October 2026, Adam's wording 1 of that day's Section 17, the drawing
`support-plan.md` in the harness's history). Three ways in to one card, `#support` in the family's `page.html`
beside `#about`, in About's look (`card about-card support-card`, its close, Done and Esc, Settings under it
staying), in `OVERLAYS`:

- Home's link, `button.linklike.lp-support#lib-support`, "Other ways to help" (`page.lede.support`), inside
  `li.lp-free` after `a.kofi`, so it keeps with Ko-fi when the row wraps, 13px in the soft ink, never coloured,
  in all three apps.
- Settings' link, `#settings-support`, "Support {app}" (`page.support.title`), beside About at the foot.
- Idiograph's one-time line after the first Word export of PETs (below).

The card's heading is `page.support.title`, the app's own name in Sift and Trace. Under it, first and plain, no
stamp, the private preview's line, `p.support-private` (`page.support.private`, supportcard2, 29 October 2026:
Idiograph is a private alpha by invitation, so testers keep it to themselves, in all three apps). Then six parts,
each under an `h3.section-label.about-head`: Cite it, `p.about-ref#support-ref` with `#support-copy`, Translate
it, the Language row's own line and link (`page.language.translate`, `/translating`), Send feedback
(`#support-feedback`), Contribute code (`#support-code`, `page.support.code_html`, its link the code on GitHub,
github.com/Pharkie/idiograph, since the repository went public, pubreadme, 10 November 2026, where "ask me for
access" opened Send feedback), Fund it, the costs in pounds (`page.support.costs`, Claude Code about £180 a month first, then the Windows
certificate about £40 a year and the idiograph.app domain about £11 a year, $50 and $14.20 at 29 October's
rate, and hosting and other fees that may follow), then Ko-fi's anchor, the same as Home's, and "A department or a
grant can pay too: ask me how." (`#support-grant`), and Thanks, Acknowledgments in en-US. The two links marked
`data-support-feedback` close the card and open Send feedback (`openFeedback('support')`, a word the screens'
lists do not hold, so the note names no screen). Where the build has no collector, `FEEDBACK.on` false,
`openSupport` hides the Send feedback part and the department's line, as the bars hide their bug, and
Contribute code stays, since its link needs no collector. Nothing is fetched at run time. Spreading the word (share it, tell your groups) is held for the launch.

The citation is written in `shell.js`, never in the catalogue, since a citation is not translated:
`supportCitation(version, html)`, `Knowles, A. (2026). <i>{app}</i> (Version {version}) [Computer software].
{address}`, the address `SUPPORT_ADDRESS`, one constant, `https://idiograph.app` in all three apps (Adam,
29 October, once he had registered the domain). About's link to the code is left as it is. The version is
`runningVersion()`, the window's where there is one, else the server's, as About has it. Copy writes the plain
text, no italics, with `navigator.clipboard.writeText` and says "Copied" in the toast, or the clipboard's
refusal. `supportWire()` in `boot` wires the card.

**The one-time line** (moment A, Adam's pick of that day). `thExport(true)` on a PETs board (`TH.mode` `pets`, so
never a GETs or LPETs board) hands `word: true` to `thExported`, which removes any `#th-once` first, so the line
goes with the note it came in, and calls `thSupportOnce`. That reads the settings afresh (`/api/settings`,
`{op: "read"}`) and, while `support_asked` is unset and the same note is still up, appends
`p.th-once#th-once` to `#th-exported`, under a thin rule, `themes.support.once_html`, its link
(`white-space: nowrap`) opening the card through `window.openSupport`, then sends `{support_asked: "YYYY-MM-DD"}`,
the day, alone. `api_settings` writes that key alone (`write_config_keys`), keeps the first day it holds, and
passes over anything that is not a day (`is_day`). So the line shows once ever, across restarts and windows, and
an agent reads the day with `{"op": "read"}`. Until it has shown the settings have no such key. No moment B.
Area 289.

**The AI's providers in Settings** (aipage, 8 November 2026, aiprov's drawing). `#set-provider` lists eight,
`PROVIDER_ROWS` in shell.js saying what each shows: `key`, `address` (the slot of `S.aiAt` its Address row holds,
`shared` for Azure's and Another service's `ai_address`, `local` for `local_url`, `lmstudio` for `lmstudio_url`, the
local two filled with `LOCAL_AT`), `deployment` (Azure's `#deployment-row` in place of `#other-model-row`) and
`where`, the `shell.ai.where_*` line in `#ai-where`, Another service's and an address off this computer naming its
host (`drawWhere`). `drawProvider` shows the chosen provider's rows alone, `#ai-anthropic`, `#ai-local` or
`#ai-other`, and `chooseProvider` then asks `keyStatus` and `loadModels` afresh, each sending `keyAsk()` or the
card's provider, addresses and switch. `aiHeldOpen(c)` reads the addresses, `ai_models`, `other_model` and
`ai_deployment` when Settings opens, `S.aiPick` keeps each provider's model as it is chosen, and `aiSaveBody` sends
them all with Save. `drawOtherModels` fills `#set-other-model` from `openai.models` by their ids, or shows
`#set-other-name` to type one where the list is empty, `#other-note` only when the list failed. The key row,
Check key and Remove act on `keyProvider()`, the chosen provider's own keychain item, the Anthropic one while
the row stands under PETs for an Anthropic model there. The PETs list adds the chosen OpenAI-style provider's
models as `<provider>:<id>`, which `pets_choice` hands `ai_route` as `model`, and the test bench sends the card's
choice through `aiTryBody`. Every row sits in `#ai-more[data-ai-set]`, so the switch off hides it and nothing is
asked. The where lines follow each provider's published terms, checked 8 November 2026: Anthropic's data
residency page (`inference_geo` `global` by default, workspace geo `us` alone), Mistral's regional inference page
(no promise for `api.mistral.ai`, `api.eu.mistral.ai` in the EU, so the preset asks the EU address), the Gemini API
Additional Terms (Unpaid Services used to improve Google's products, read by human reviewers), OpenAI's Your data
guide (no processing constraint without a regional domain) and Microsoft Foundry's deployment types (Global in any
region, Data Zone within its zone, Standard within its geography). The command line's `settings --ai-provider`,
`--ai-address`, `--ai-deployment` and `--ai-model` and MCP's `settings_set` set the same keys through
`api_settings` (`settings_ai_given`), and `settings` reads them with the where line (`settings_ai`). Area 347.

**Using your own AI agents** (21 October, plural since 22 October). The end of each app's AI features page, outside `#ai-more` so it
shows with the switch off. `GET /api/agent-start`, a shared route, answers `text`, the box's words, with
`cli`, `mcp`, `guide` and `uri`. `server.agent_commands(app, frozen, executable, here, system)` works out
this install's commands: frozen, the app's executable with `cli` or `mcp` (on Windows its console twin,
`app_folders.console_exe`), from source the app's command beside the code (`idiograph`, `sift`, `trace`, or
its `.bat`) and `mcp_server.server_command` with `--app` for Sift and Trace, and the guide as the file
beside the code and as the MCP resource (`mcp_server.guide_uri`). `agent_start` writes the words, Idiograph's
naming the project tick. The page asks for it each time Settings opens (`drawAgentStart`), and Copy says
Copied for a moment. Area 246.

**An agent's action waiting for his yes** (holdsbuild, 27 October 2026, Adam's ruling of Section 13 on the holds
design of 26 October). `apps/idiograph/holds.py`. Every Idiograph command an agent runs passes through
`idiograph_cli.run_in_scope`, which hands it to `holds.gate` in its scope: an op of `holds.HELD` (board and GETs
delete and restore, `transcript replace --all`, `replace-undo` over two workbooks or more, `turn trim`, `turn
write` taking a placed statement off the boards, a board or GETs `apply` with a `merge` or `apart` on a board
whose `made.by` is not `agent`, `trajectories apply` with a `remove`, `gets take` with PETs gone, `participant
rename --folder`, `project send` of every participant or out of the folder) not run as a dry run runs its dry
run instead, on its arguments with every file read once (`frozen`), and when its rule says so writes a hold to
`idiograph-holds.json` at the project's root under its own lock, `.idiograph-holds.lock`, apart from the
project's and a case's: the id, `h<n>`, the op, the agent's tool and his request, the dry run's lines (`dry`),
what it would do as the card says it (`would_do`, `would_lines`: what goes or changes with its counts, where a copy
is kept, and the board that stays the Current board), the arguments without the project's choices, the words of the line, the card and the line after
each answer (`said_of`), in English and as the catalogue's keys and slots under `said` (the text layer, below), and `fingerprint`, each touched file's mtime and size. The answer is `held`, marked as
every answer is (`op` and `status` plain in `cli.PLAIN`). With `skip_permissions` true in the settings the run
reads (Idiograph's own setting, off by default, saved by Settings' Save), the op runs at once with its tool
"<agent>, without asking", which every History record the op makes carries. `holds.RUN_AT_ONCE`, set by the
suite's runner alone, runs every op as before holds, and area 276 puts it back. `hold` and `hold show <id>`
(MCP `hold`, `hold_show`) read it. `/api/holds` is the page's own, POST only and from the server's own page
(`own_page`), area 261 listing it so: `list` the waiting across `holds_roots()` (the app's projects, a run's
`--root` and the demo), `check` the card's look (the dry run again, the hold taking the new lines and
`changed` when they, clock times aside, or the fingerprint differ), `approve` (marked `approving` so it never
runs twice, the dry run again, nothing run and `changed` when it differs, else `run_scoped` with `_approved`
and the tool "<agent>, approved in the app", the hold `approved` with the op's answer, or `failed` with its
refusal) and `decline` (the hold `declined`, and for a board or GETs op a revision of that board named
"Declined in the app: ..." through `board revision` or `gets revision`). The page (`distil.js`, `holdsTick`
every four seconds on the statements screen, PETs and GETs) draws `#hold-line` fixed where `#es-outside` or
`#th-outside` sits, below it when it shows, Review opening `#hold-card` for the oldest, and the setting's row
in the `agent-more` slot after Copy with `#skip-confirm` as `#ai-confirm` asks. `project_pack.LEFT_OUT` never
sends the holds file. Area 276.

**The agent's words as its own, and each hold's risk** (agentholds, Adam, 2 November 2026, by dialog). The card
quotes what the agent says he asked as the agent's, `server.holds_asked_request` ("{asked}. {agent} says you
asked: ...") and on the card for several `distil.holds.agent_says`, its groups by project, request and agent.
`holds.agent_words`, after Harbour's `keyWords`, cleans it when it is shown, never in the file: one line, no
character of `Cf`, `Cc`, `Co` or `Cs` nor the fillers, the combining grapheme joiner and the variation
selectors, every quotation mark and lookalike (`QUOTE_LIKE`, `Pi` and `Pf`) as a plain apostrophe, every `://`
as `: //`, and at most `WORDS_MOST` characters (300) with an ellipsis, `NAME_MOST` (60) for the agent's name and a
new name. A replace's find and put and a new code's or participant's name are kept in `said` as `said_by`, the
words as they came, said through `agent_words` by `text_of`. `shown` gives `tool` and `request` cleaned.
`holds.RISK` names the risk each op of `HELD` answers, of `RISKS`, the four at the head of agents.md, and each
`PAGE_ONLY` route in area 261 carries its risk or `screen` or `own AI`. Area 261 fails on an op with none, a
row of agents.md's table of holds that differs from `RISK`, and a route with no tag.

**Several answered together** (holdbatchA, 1 November 2026, Adam's option A of that day). With more than one
waiting, Review opens `#holds-batch` (`holdsBatchOpen` in `distil.js`, in `OVERLAYS`): the rows under each
project's request (`hbGroups`), each its tick in a label in a `data-tick-row` row, the agent and `hbWhen`
(`tTime`, the day too when not today), and Details opening the row's card under it (`HB.open`). Every row is
ticked but one whose hold says `changed`, then `/api/holds` `check` with `holds`, a list of `{root, id}`, runs
each dry run again and unticks those changed now. Decline N and Approve N send the ticked ones to `approve` or
`decline` with `holds`, which `holds.answer_all` answers in the order given with each one's `outcome`
(`approved`, `declined`, `changed` with `server.holds_changed_waits`, `failed` with its refusal, `answered` or
`gone`) and `done`. `hbAfter` draws the outcome, `said` (`shown`'s line without its first word) for each done,
the reason for each not done, and the rows not ticked still waiting, with Review the N waiting (`hbAgain`) and
Done (`hbClose`, the line then counting what still waits, or saying the card's title when nothing does). One
waiting keeps `#hold-card`. The fault it fixes: an approved board delete changes that participant's boards
file, as a decline's History line does, so the next hold on the same file was refused once as changed (ten
deletes, about 37 clicks). `holds.carry` runs after every Approve and Decline: a waiting hold whose files stood
as they did just before his answer, and stand now as his answer left them, every other file as the hold has
it, takes the new `fingerprint` and its dry run afresh, so his own answers never count as a change and
anything else's still does. A hold that something else changed too still has the files his answer changed
advanced, so `changed_what` (`check` and `approve`, from the fingerprints) names only what changed elsewhere,
"Mabel's boards", in the row, the single card (`distil.holds.what_changed`) and the refusal
(`server.holds_what_changed_waits`). A hold carried whose dry run now says otherwise, a replace whose boards
were deleted since, takes `since_yours`, `deleted` after an approved delete else `changed`, and its row says
so in his own terms, never as changed since the agent asked. The replace's line, card and row give the agent's
own words, `replace “dog” with “hound” in every participant's transcript`, and the card's words say "Archive
folder" for `_Archive`. `fingerprint` keys each file by its path with links resolved, since a project
reached as /var and as /private/var gave two keys and every hold read as changed. Agents still answer none:
the route is the page's own (`own_page`), no command or tool approves or declines, and `hold show` takes several
ids (MCP `hold_show` with `ids`) to read each one's outcome, `holds` in the order given. Area 314.

**Progress while several are answered, and waiting actions on Home** (holdsprog, 11 November 2026, Adam, after 13 slow
approvals on one participant that "just sat there", and Home saying nothing of them, ruled by dialog: count and bar, on
the project's card). `hbAnswer` no longer sends the ticked rows in one call: it sends each, in the order shown, as
`/api/holds` with `holds` of one `{root, id}`, so `holds.answer_all` runs unchanged and the outcome has the shape it
had, and `hbRun` gives the card the class `running` (`.holds-batch.running`, which hides `#hb-all`, `.hb-sum`,
`.hb-list` and `.card-actions` and shows `#hb-run`) with the heading, `distil.holds.approving_of` or `declining_of`
("Approving 4 of 13", `n` the ones finished, so line and bar agree), and `#hb-bar`, a `role="progressbar"` whose
`#hb-fill` is `n` over the total, in the round bar's colours (`--rule` under `--good`, its ease) at 4px. `holdKeys`
ignores Esc while `HOLDS.busy`, and the card has no other way to close. A call that throws (the server gone, a refused
route) stops there: that row is `failed` with the error's words, the rows after it are `HB.after.unreached` and read
"Not reached. It still waits for your yes." (`distil.holds.not_reached`), counted in `still`, and `hbAfter` then draws
the result as it always did. One action alone (`holdAnswer`) shows `#hold-run`, "Approving..." or "Declining...",
only once `HOLD_SLOW_MS` (500) has passed, and its Esc is likewise ignored while it answers. For Home,
`/api/holds` has a fourth read, `counts`: `holds.counts(roots)` reads each listed project's `idiograph-holds.json` and
counts `waiting`, with no `shown`, no dry run and nothing else of the project, so Home reads no more of a project
than before (a project that never had a hold costs one failed open), and the route names each by `project_id`, the id
its card has (`[{id, root, n}]`, none with `n` of 0). `distilHomeDraw` calls `homeHoldsRead` after `drawPick`, so the
counts are asked each time the picker is drawn, Home shown again or the way back from a project's page, and not while
it stays up. A project's card takes a `.hc-hold` button beside its own (a button inside a button is not markup), its
`li` `has-hold` and its list `has-holds`, which keeps the room under every card of the list so the row stays level, `distil.home.holds_waiting` ("{n} actions are waiting for your yes" without the full
stop) in `--crux`, the orange of the Preview note's sign. A press (`holdsOpenFromHome`, delegated from `#projects` and
`#demo-projects` in `holdsBoot`) opens the project's page and the first participant's PETs the way his own clicks
do (`openPage`, `openThemesIn`, so Back walks them), reads the list afresh (`holdsRead`, split out of `holdsTick`)
and opens the card as Review does, for every action waiting, not only that project's. Area 314 holds the one-id calls
and `counts`, area 110's harness stubs `homeHoldsRead`.

**A command and an MCP server per app** (20 October, the fifth build of the split). `sift` and `trace`,
with their `.bat` twins, sit beside `idiograph` at the root, each running `cli.py --app <app>`, and a
frozen build is the app its executable is, `Sift cli ...`. `cli.parser(app)` gives Sift the `sift`
command's arguments at its top (`add_sift_arguments`), Trace the `trace` command's, and either its
Search alone with `search ... --folder` (`args_for`). A leading `sift` under Sift, the old form, means the
same. `OWN_COMMANDS` names each app's first words, and `elsewhere` refuses another app's by name with the
command to run in its place, before anything else, while `outside` refuses the same inside `perform`, so
the MCP server's calls hold to it too, and a Search of the cases is Idiograph's alone.
`cmd_search_folder` refuses a folder of an app the run does not serve before reading it. The one line
`app_identity.SERVES_TOO` (which `server.SERVES_TOO` now is) kept `idiograph sift` and `idiograph trace`
as aliases, and Sift's and Trace's tools on Idiograph's MCP server, until the cutover of 23 October 2026, and
since it each is refused by name with the command to run in its place. `cli.first_start`
runs Sift's or Trace's first start from its command line or MCP server when its window never has, unless
`--config` names a trial's settings. In `mcp_server.py`, `tools_for(app)` gives each server its tools,
today's names: Sift's and Trace's their own and `own_search(app)`, which needs a folder, and Idiograph's
its own and its search, Sift's and Trace's too until the cutover. Another app's tool is refused by name.
Each has its own `instructions(app)` (Sift's `SIFT_CORE` from `sift_mcp.py` and Trace's `TRACE_CORE` from
`trace_mcp.py`, Idiograph's `TOOLS_LINE` its own `DISTIL_LINE` since the cutover, see The family's folders), its
own guide, `docs/agents-sift.md` and `docs/agents-trace.md` as `sift://guide` and `trace://guide`, whole since
the sixth build, when their sections of `agents.md` and their conventions moved into them (`guide_sections(app)`),
and no prompt, schema or project resource. `skills/sift/SKILL.md` and `skills/trace/SKILL.md` carry those guides
word for word, as `skills/idiograph` carries `agents.md`. Area 226 runs `search strings` and `search run
--draft --date --follows` through `sift` on one copy of an invented review, and through `idiograph sift` on
another, where each is refused and writes nothing.

**The Linux server** (linux2, 8 November 2026, build 2 of the Linux plan). `packaging/build_linux.py` freezes the server with PyInstaller on Linux, one folder `build/pyinstaller-dist/<Name>/` holding one executable named for the app, from `packaging/linux_launcher.py` (the Mac launcher's server, command line and MCP server, with no dialog, since the window will own those). It takes `build_mac.py`'s pins, modules, data files and stage, PyInstaller's prebuilt bootloader, and checks `cli --help`. `--smoke` then starts it with no display in a home folder of its own, asks `/api/server`, posts the quit and fails unless it answered as the app and ended. `--dry-run` writes the spec and says every step on any machine. The `linux-server` job of `.github/workflows/windows-installer.yml` runs it on `ubuntu-22.04` on a tag and on a dispatch with `linux_server` ticked, `continue-on-error`, and no other job needs it. `tauri.linux.conf.json` carries the server as the resource `server/`, and `server_dir()` in `main.rs` looks in `<prefix>/lib/<name>/server` (a .deb's `/usr/lib`, an AppImage's mount), then beside the executable. No window, installer or upload yet. Area 348.

**The Linux window** (linux3, 8 November 2026, build 3 of the Linux plan). `build_linux.py --window` runs Tauri's bundler (`packaging/tauri/bundle.py`, `linux=True`) on the window around the frozen server for `deb` and `appimage`, x86_64, and writes `dist/<Name>-x86_64.AppImage` (the download) and `dist/<Name>-amd64.deb`. `tauri.linux.conf.json` carries the server as the resource `server/` (Tauri lays it at `<prefix>/lib/<product>/server`, where `server_dir()` looks) and the .deb's section. On Linux alone `Cargo.toml` gives rfd its `gtk3` backend (GTK 3 is already linked through WebKitGTK, and rfd with no backend would call zenity or kdialog, which a machine may lack). Idiograph's own Linux build claims `.idiograph`: `bundle.linux_file_type` adds `mimeType` to the file association (Tauri writes only the desktop entry's `MimeType=` line from it) and has the .deb install `src-tauri/linux/uk.co.adamknowles.idiograph.xml` into `/usr/share/mime/packages`, which dpkg's shared-mime-info trigger picks up. Sift, Trace and a test app claim none, and an AppImage registers nothing alone. `check_deb` unpacks the .deb and fails the build unless the window, the server, one desktop entry, the `libwebkit2gtk-4.1` dependency and (Idiograph's alone) the file type are in it (`deb_problems`). `packaging/tauri/drive_linux.py` starts the AppImage under `xvfb-run` and a D-Bus session in a home of its own with the software drawing WebKitGTK needs on a machine with no GPU, waits for `/api/server` to say the app and `window: true`, fetches the page, and ends the window with SIGTERM to its process group, failing unless it ends and the port closes. The `linux-app` job of `.github/workflows/windows-installer.yml` (tag or dispatch with `linux_app`, `ubuntu-22.04`, `continue-on-error`, no job waits for it) installs WebKitGTK 4.1's development files, GTK 3, xvfb and libfuse2, runs both and keeps the files as an artifact. It freezes the server itself and repeats the smoke, so `linux-server` is for a dispatch alone since linux57. Area 350.

**The Linux release** (linux57, 9 November 2026, builds 5 and 7 of the Linux plan). The AppImage is the Linux download and the file Tauri's updater replaces in place, so `release.py` signs it with the same key as the Mac's and Windows's update files, bound to the version, and `latest.json` gains `linux-x86_64`. The .deb cannot update itself: it goes on the release beside the AppImage, unsigned and not in the manifest. A draft is collected with both when it has them (`Idiograph-x86_64.AppImage`, `Idiograph-amd64.deb`, `names()` gives Sift's and Trace's), and a draft whose Linux job failed, which gh reports as no asset matching, goes out for the Mac and Windows alone with a note, so Linux stays allowed to fail while it is new. The workflow's `linux-app` job says `ok` as an output only after its last step and always keeps its artifact for a tester. The `release` job needs `[windows, mac-app, linux-app]` but runs whatever Linux did, once Windows and the Mac passed, and downloads the Linux artifact and adds its files to the draft only when `ok` is `true`. No signing key is in the workflow. The README has a Linux download line. Area 355.

**Sift and Trace on Linux** (linux9, 9 November 2026, build 9 of the Linux plan). The Linux build was already per app: `build_linux.py --app sift|trace` freezes `Sift` or `Trace` (the executable's name is what `app_identity.from_executable` and `app.rs` read), `bundle.overrides(..., linux=True)` lays that app's product name, identifier, icon files (`icons/sift`, `icons/trace`) and update address over tauri.conf.json, and `NO_FILES` plus `linux_file_type` keep `.idiograph` and its mime file Idiograph's alone. The files are `Sift-x86_64.AppImage` and `Sift-amd64.deb`, as `release.names` has them, and the `linux-app` job takes the app from the tag through `release.py --which`. What linux9 added is `deb_problems` asking that the .deb's desktop entry has an `Icon=` line and a picture of that name under `usr/share/icons` (Tauri names both for the executable), so an app's menu entry carries its own mark, and area 356, which holds each app's names, icons, update address, file type, .deb contents, dry run and tag on any machine. Only a CI run on a tag proves that Tauri writes the entry and icons under those names. The README's Linux line is unchanged.

**What the Linux desktop showed** (linuxfix, 9 November 2026, from linuxvm's run of the .deb on Ubuntu 24.04 arm64 under GNOME). Nine faults, each fixed with Mac and Windows unchanged. (1) GTK drew the `\t<keys>` of Windows's menu words inside the words (`win_find`, `win_find_replace`, `win_home`, `win_bigger_text`, `win_smaller_text`): `menu.rs` builds those items through `keyed`, which on Linux cuts the words at the tab (`before_tab`) and gives the keys as the item's accelerator, Ctrl+F, Ctrl+Shift+F, Alt+Home, Ctrl and the numeric pad's plus (as the Mac's Bigger Text has it, the row's = and + left to window.js) and Ctrl+-, so the item does what its keys do through `__idiographMenu`, and on Windows passes the words whole with no accelerator as before. (2) `projectMenuWord` says Show in Files on Linux (`shell.project_menu.files`, `LINUX` from `navigator.platform` beside `MAC`, a third argument that defaults to it). (3) WebKitGTK's print dialog ignores `@page`, so window.js's `printer` now runs on every system but Windows, and `print` in main.rs on Linux runs `webkit2gtk::PrintOperation` with a `gtk::PageSetup` of the page's orientation and paper (`gtk_paper`, ISO and North American names) before `run_dialog` over the window, through `with_webview` (the `gtk` and `webkit2gtk` crates at the versions Tauri builds with, Linux alone). (4) `say` shows a line that was put away empty and sets its words a frame later (or after 100 ms where no frame is drawn), so Orca hears them as a change inside `#toast-live`, a polite status. A standing line takes new words at once, and `unsay` goes by `toastWords`. (5) Idiograph's own Linux build writes its desktop entry from `src-tauri/linux/idiograph.desktop` (`bundle.LINUX_DESKTOP_TEMPLATE`, the .deb's `desktopTemplate`, which Tauri's AppImage builds from too), Tauri's own template with `%F` after `{{exec}}`. (6) The .deb puts 32, 128 and 256 pixel copies of the app's mark at `usr/share/icons/hicolor/<size>/mimetypes/application-x-idiograph.png` (`LINUX_MIME_ICONS`), the name the mime file's `<icon>` gives the type. `deb_problems` asks Idiograph's .deb for both and refuses either in Sift's, Trace's or a test app's. (7) The window-state plugin keeps the main window's size in device pixels and sets it again as those, which GTK read as half or twice the size after a change of the display's scale: on Linux `linux_size` in main.rs notes the size in logical pixels on each resize (unmaximised, not full screen or minimised), writes it to window.json's `size` (keep.rs, `fit_size`) as the window goes and at exit, and sets it once the plugin has placed the window. (8) `pick_title` drops the full stop off a Mac (`title_words`). (9) `build_linux.window_names` names the files for the machine (`linux_arch`): `<Name>-aarch64.AppImage` and `<Name>-arm64.deb` on ARM, x86_64's as before, and x86_64's off Linux, where a dry run says what the release builds. release.py's names are unchanged. Area 360 holds the parts that run on any machine, and cargo's tests the window's own (`before_tab`, `title_words`, `gtk_paper`, `fit_size`). Only the VM proves GTK drawing the keys, the accelerators reaching the page's Find and Home, Orca speaking the line, the print dialog's page, the file manager's icon, a file opened from it, and the window's size across a scale change.

**What the second VM run found** (linuxfix3, 9 November 2026, from linuxvm2's run of train 201's .deb). Three faults, Mac and Windows unchanged. (1) Ctrl+A, C, V and Z did nothing in a text field: Edit's items held those keys as accelerators, GTK took them before the page, and `press_in_page` presses nothing off Windows. On Linux the six items carry no keys (`menu::edit_keys`), so the keys reach the page, which edits as in any browser and takes Ctrl+Z and Ctrl+Y on a board. A click on Cut, Copy, Paste or Select All runs WebKitGTK's own editing command on the window's view (`webkit_command`, `linux::edit`, `webkit_web_view_execute_editing_command` through `with_webview`), and Undo and Redo ask the page first through `__idiographMenu('undo')`, as the Mac's do, the `edit` command then running WebKitGTK's Undo or Redo where the page leaves it, as in a field. (2) Orca heard no line at the foot. WebKitGTK's AT-SPI code has no live-region event at all (`AXObjectCacheAtspi.cpp` lets `AXLiveRegionChanged` fall through): Orca hears a live region only as `children-changed:add` on it, which WebKit sends only when the region has been registered on the bus, that is named to an assistive technology once, and words set in an element already shown send nothing, static text being folded into its parent. A status there since the page loaded need not be registered, and linuxfix's line shown empty a frame before its words sent its one add with no words. So on Linux `say` goes by `toastAnew`: the line is put away, `#toast-live` taken out and put back in its own place, which sends `children-changed:add` on the web area naming the status (and so registering it), and `TOAST_ANEW_MS` (120 ms) later the line is shown with its words, an add inside the status that carries them. A standing line comes again the same way, and `unsay` cancels a line still due (`toastDue`). Off Linux `say` is as linuxfix left it. (3) After Super+Down took a maximised window back to its size, the next start opened maximised again. The window-state plugin notes maximised only on CloseRequested and at exit, asking the windows still open, and Quit destroys the window with no CloseRequested, so the note stayed the one the window opened with. On Linux `let_go` asks the plugin to save the main window's state (`linux_size::state_before_going`, `save_window_state` on the main thread, before the destroy that follows it there). Windows takes the same path through Quit and keeps the plugin's own behaviour, as the brief asked. Area 360 and area 339 hold the line at the foot, and cargo's tests `edit_keys` and `webkit_command`. Only the VM proves the keys in a field, the menu's items, Orca speaking and the state kept.

**What the third VM run found** (linuxfix4, 9 November 2026, from linuxvm3's run of train 203). Two faults, Mac and Windows unchanged. (1) Ctrl+Z, Ctrl+Y and Shift+Ctrl+Z in a text field undid nothing: WebKitGTK on GTK 3 binds no key to undo, and since linuxfix3 Edit's items carry none. On Linux window.js listens for the keys (`idiographFieldUndo`: Ctrl and Z, or Y, or Shift and Z, in a textarea, a text input or written words, read-only and disabled fields left out, the key's place read where the layout gives no Latin letter), and once the page has had the key, where it left it (not `defaultPrevented`), asks the window's `edit` command for WebKitGTK's own Undo or Redo (`webkit_command`, `linux::edit`), the route Edit's items take. Off a field the page's own undo takes the key as before. (2) Orca 46.1 said no line at the foot, linuxfix3's `toastAnew` notwithstanding: Orca's WebKitGTK script presents no live region. A probe in the VM (a GTK 3 window under Orca's debug log) showed Orca 46.1 speaking both ATK's `announcement` signal, which the ATK bridge (2.52) sends as AT-SPI's `object:announcement` and Orca's default script presents as a message whatever has the focus, and a notification-role object shown, said with "notification" before it. So on Linux window.js gives the page `idiographSay`, and shell.js's `say` hands it each line, which the window's `announce` command (trimmed to 400 characters, `speakable`) emits as `announcement` on the window's accessible through `with_webview` (`linux::announce`), only where the signal is there (ATK 2.46 and on), and the line shows as it does on a Mac and Windows. `toastAnew` stays for the page in a browser on Linux. `unsay` puts the line away, and a line already said stays said. VoiceOver and NVDA keep the page's live region. Area 360 holds the keys and the window's voice, and cargo's test `speakable`. Only the VM proves WebKitGTK's undo on the keys and Orca speaking.

**Orca and WebKitGTK's crash** (orcacrash, 9 November 2026, from linuxfix4's run). With Orca 46.1 on, WebKitGTK 2.52.6's page process aborted (SIGABRT) on Ubuntu 24.04 arm64. The backtrace with Ubuntu's debug symbols: `UTF16OffsetToUTF8` reading its offset table past the end (`WTF::CrashOnOverflow`) inside `AccessibilityObjectAtspi::textAtOffset`, called for AT-SPI's `Text.GetStringAtOffset`. When an object's text holds an embedded object (U+FFFC, so the text is 16-bit and the table is used), the start of the word, sentence, line or paragraph comes from `boundaryOffset` and only its end is clamped to the text's length, so a place whose next caret place lies outside the object, past a button after it or through buttons with only an icon, gives a start beyond the table. WebKit's main still has it. It needs no Orca: AT-SPI calls alone end a bare WebKitGTK page of a group holding a button with a button after the group. Orca reaches it two ways. A Tab to the statement's quote asks the line of `#pairs` past its arrow and bin, and a Tab to Columns asks it at the end of `#cols-head`. And Orca 46.1's WebKitGTK script (a default-script descendant, not the web script) keeps its structural navigation's one-letter keys grabbed in a text field, so typed letters jump about the page and ask the same. On Linux `axGuard` (shell.js) puts one zero-width space in a span with `aria-hidden` and no room (`.ax-guard`) after `#pairs` and at the end of `#cols-pick` (distilBoot), which gives those places a caret stop of their own, the groups' text and names unchanged. Off Linux nothing is added. A sweep of every object's offsets on the statements screen still ends the page in a few objects Orca's Tab, arrows and typing never reached (the transcript's end, the status bar), and Home, PETs and GETs took 40 Tabs each way without it. Typing with Orca needs `Orca + Z` (structural navigation keys off), which is Orca's own. Area 360 holds the guard, only the VM proves the crash gone.

**A line to confirm in the window** (removefix, 9 November 2026, Adam: Remove from Idiograph on a shared copy's card did nothing, twice, in his daily copy). The Mac's web view shows nothing for `window.confirm` and answers it with Cancel at once: WKWebView asks its UI delegate, and wry's (`WryWebViewUIDelegate`) has no `runJavaScriptConfirmPanelWithMessage`, so every confirm in the window stopped at its first line, Remove from Idiograph on any card, a copy's or an ordinary project's, in the band's menu and in Project settings, Reset demo, Sift's and Trace's Remove, and Working together's Remove, Hand over and Make lead. Chrome, WebView2 and WebKitGTK show their own. Every confirm of the three apps now goes through shell.js's `askSure(message)`: in the app's window `window.idiographConfirm` (window.js), which asks the window's `confirm` command (main.rs, in build.rs and `allow-confirm` in the capability), an rfd message box on the window, a sheet on a Mac, its title the app's name, OK (`menus.ok`) and Cancel (`menus.cancel`), true for OK alone, and in a browser the browser's own confirm. No page calls `window.confirm` itself. A drive build's check answers the box by `IDIOGRAPH_WINDOW_CONFIRM`, `ok` or `cancel` (`drive::confirmed`), or the sheet is answered OK after four seconds as every sheet is. Area 330 holds it, area 164 the command's name.

**Remove, and its folder to the Trash** (removetrash, 10 November 2026, Adam, after removing a duplicate shared copy: "there should be a possibility ... I would have chosen to delete files and folders"). A system's box carries no tick, so Remove from Idiograph, from Sift and from Trace no longer go through `askSure`: shell.js's `askRemove(name)` shows the family's card `#remove-card` (page.html), the project's name, Remove from the app, a line that follows the tick and the tick itself, Move its folder to the Bin too, off each time it opens, and answers null for Cancel or Esc, else `{ trash }`. The six places that remove (distil.js `homeRemove` and `removeProject`, sift_settings.js `siftRemove` and `sfpRemove`, trace.js `traceRemove` and `trpRemove`) send `trash` and the page's id, `page`, with the app's own remove (`/api/projects` op `remove`, `/api/sift-review` and Trace's route op `forget`), and `removedSaid` puts where the folder went at the foot. The server's side is the family's `trash.py`: `guard` refuses, nothing moved, a folder not there or a link, a drive's top, the home folder or one holding it, the home's Desktop, Documents and Downloads, a cloud drive's top (iCloud Drive's, `~/Library/CloudStorage`'s folders, OneDrive's), one holding the app's code, demo, data, logs or settings (`server.trash_guard`'s `keep`), one holding another project the settings or the recent list name (`known_projects`), and one where a lock is held (`busy`, any `*.lock` taken by a writer). `server.open_elsewhere` refuses a project another page is in front of: each beat (beat.js) now names its page by an id of its own, `idiographPageId`, and the project the app says it is in front of, `window.idiographAt` (Idiograph's project id, Sift's and Trace's folder), beating at once when that changes, and `PAGES` keeps them for 75 seconds, a page's last word taking it off. An approved hold names the page approving through `api_holds`'s `ASKING_PAGE`. `move` is each system's own: on a Mac NSFileManager's `trashItemAtURL` through the Objective-C runtime (ctypes, so Put Back works), on Windows `SHFileOperationW` with `FOF_ALLOWUNDO`, refused first on a drive that is not fixed, where Windows would delete outright, and on Linux the freedesktop.org Trash, the home Trash or `.Trash-<uid>` at the top of the folder's drive, its info file written first and the folder renamed, never copied. `TRASH` is the name the suite stands in for, so no check reaches the real Trash. The move comes before the list is written, so a move refused keeps the project. Each removal is a line in `config.removed.jsonl` beside the settings (`trash.record`), when, the app, the name, the folder, `trash` and who asked. Agents: `project remove [--trash]` (MCP `project_remove`), held with `--trash` (`holds.HELD`, risk 3), and an approved one whose folder went to the Trash writes nothing more into it, so no lock makes the folder again. Area 330 holds it.

**The Windows app.** For a Windows PC with nothing installed, `packaging/build_windows.py` builds
Idiograph in its window with its own Python and `dist\Idiograph-Setup.exe` to install it. GitHub's
Windows machine runs it from `.github/workflows/windows-installer.yml`, after the suite, by hand and on
a tag `v` and a number, and a tag's installer goes on a draft release beside the Mac's files. It takes
`build_mac.py`'s pins, certifi left out since Python on Windows checks HTTPS against Windows's own
certificates, its modules, its data files and its stage, so the two apps carry the same code and
demo. Windows has no `say`, so `python3 packaging/build_windows.py --speak`, on a Mac, speaks Juno's
recording into `packaging/recording/`, committed as the one piece of audio in git (Adam's word, 14
October 2026) so GitHub's build carries it, under
a name that carries the first 16 hex of the hash of the transcript it was spoken from. A build
takes it only when that is the transcript's own, since another's timecodes would land on the wrong
words, and else ships the demo without it and says so in one line, as GitHub's build does, the
player then saying there is no recording. The icon is `Idiograph.ico`, make_app's drawing at each size Windows asks, up to 32 from the mark drawn for 16 pixels. PyInstaller makes
one folder with two executables from `packaging/windows_launcher.py`: `Idiograph.exe`, windowed,
which runs the server, and `Idiograph-console.exe`, its console twin, for `cli`, `mcp` and `stop`,
since a windowed program cannot print to the terminal that ran it, and Add Idiograph to Claude
Desktop names the twin. The build runs the twin's `cli --help` before it goes on. Since 17 October
(the third Tauri build) Tauri's bundler makes the installer, NSIS's, in place of Inno Setup 6's, through
`packaging/tauri/bundle.py`: the window, `Idiograph.exe`, with the frozen folder beside it as `server\`,
for the current user alone, in `%LOCALAPPDATA%\Idiograph`, with no administrator prompt, a Start menu
entry, a desktop shortcut when its tick on the last page is ticked, an uninstaller in Settings, Apps,
and the server's version. That version is Idiograph's entry in `versions.json` at the top, 0.9.24 since 10
November, which `server.VERSION`, `release.py`, `update_proof.py next` and both builds read through
`app_identity.version`, and which
every build lays over `tauri.conf.json`'s, and its last number goes up each time a build is sent to a
tester, 0.9.0 having gone to two, a Mac build on 13 October and a Windows build on 15 October. A newer
version installs over the old in the same folder, and `packaging/tauri/src-tauri/windows/hooks.nsh`
gives the installer Idiograph's own steps: before a file is touched it stops a running Idiograph
through `server\Idiograph-console.exe stop`, as `Idiograph.exe stop` did under Inno Setup, then
removes 0.9.0's Inno Setup install, found by its id, `APP_ID` in `build_windows.py`, with its own
uninstaller run quietly, which stops its server first, and waits for its entry to go, since that
uninstaller hands over to a copy of itself and returns at once. The uninstaller stops a running
Idiograph the same way, removes the app's own files and leaves the folder's `Logs`. Nothing of the
user's is in the install folder, so every setting and case stays in `%APPDATA%\Idiograph` through an
install, an upgrade and an uninstall, and the uninstaller's tick, Delete the application data, takes
only the window's own, its size and place, its kept settings and WebView2's folder.
Unsigned, SmartScreen says "Windows protected your PC", and More info, Run anyway runs the
installer, once. `--sign-sha1` with a certificate's thumbprint signs both executables with signtool,
`SIGNTOOL` the one place, and has Tauri sign the window and the installer with the same certificate. It
needs a code-signing certificate from a certificate authority, or Azure Trusted Signing, in the store of
the machine that builds, and on GitHub's machine a secret to bring it there.
`python3 packaging/build_windows.py --dry-run` on any machine writes the spec and the settings laid over
`tauri.conf.json` into `build/` and says every step without running one.

*Against false findings* (22 October 2026). Windows Defender removed 0.9.3 from Curt's machine as
`Trojan:Win32/Bearfoos.x!ml`, a cloud machine-learning guess, not a known signature, and a common
false finding on unsigned PyInstaller apps. Three things changed in the Windows build, none in what
the app does. Each of PyInstaller's two executables carries a full Windows version resource
(`version_resource`, its `version=` file written beside the spec): the publisher and copyright
`tauri.conf.json` gives, the app's name as product and description, its version in Windows's four
numbers and the file's own name, where before it carried none. Tauri already writes the same for the
window from `tauri.conf.json`, without the file's own name, and its NSIS script for the installer
without a company, which `hooks.nsh` now adds. PyInstaller is installed from its source at the pin,
with `PYINSTALLER_COMPILE_BOOTLOADER=1`, `--no-binary pyinstaller` and `--no-cache-dir`, so its
bootloader is compiled on GitHub's machine by the Visual Studio there, which PyInstaller's waf finds
through vswhere. The prebuilt bootloader in the wheel is the same bytes in every PyInstaller app,
malware's too, which is why scanners learn to flag it. The build stops when pip said nothing of
compiling it and prints the new bootloaders' hashes. Last, the workflow's step after the build runs
`build_windows.py --scan`: Defender, brought up to date, scans the frozen folder, the window and the
installer with nothing removed, prints its report, and a finding fails the run, before any upload, as
a GitHub error naming the file and the detection. With Defender missing or off it says so and the run
goes on. A cloud `!ml` guess may not show in a scan on GitHub's machine, so a clean scan is no proof
that Curt's machine will agree. Left as they were: one folder, never one file, UPX off, `--clean`,
and PyInstaller's own manifest, all already the choices that draw fewest findings. Signing, which
would do most, is Adam's decision and its cost, and the build is ready for it (`--sign-sha1`). A file
Defender still flags can be sent to Microsoft as a false finding at its submission page.

`windows_launcher.py` is `mac_launcher.py` in Windows terms, the window's server and, run by itself,
the launcher of the browser's days. A double-click with nothing on the
port starts the server, `Idiograph.exe --serve`, with no console window, its output in
`%LOCALAPPDATA%\Idiograph\Logs\idiograph.log` and its pid file beside it, and the line of every
launch goes to `%TEMP%\idiograph-launch.log`. A double-click while it runs offers Stop, Restart and
Open, Open the default, in Windows's task dialog through ctypes, with version 6 of the common
controls activated around it, and where no dialog can be shown it opens the page. One launch at a
time, through a lock beside the log, so a second double-click while the first is starting waits and
then finds its server. Port 8765 first, then the next free, the listening sockets and their pids
from iphlpapi's `GetExtendedTcpTable` and each pid's command line from `NtQueryInformationProcess`,
none of it in words that change with Windows's language. A server is the app's own only when it is
`Idiograph.exe` run with `--serve`, so a server run from source is another program. Stop asks the
server to quit through `/api/server`, as Quit in Settings does, and ends the process only when it
still listens five seconds later, and a port another program holds is refused before anything is
sent. Restart in Settings works in the Windows app: Windows cannot run a program again in one
process, so the launcher sets `server.SPAWN` to `respawn`, which starts the server anew and lets
this one end. Every Windows call is a name the suite stands in for, so its logic runs on a Mac.

**The window (Tauri, 17 October).** Adam chose Tauri at 11:20 on 17 October: Idiograph in a window of
its own, its icon in the Dock and the taskbar, in place of a browser tab. Not shipped yet, it is built
on the branch `spike/tauri` alone, and this is build 1 of about five, the installers and the updater
to come. `packaging/tauri/src-tauri/src/main.rs` is the window, Tauri 2.12.1, with the frozen server
the two builds above make carried in the bundle's resources as `server/` and run beside it. The
single-instance plugin comes first, so a second start brings the open window forward and ends before
it starts anything. Then a thread of its own takes the port as the launchers do, `--port` on the
command line, `IDIOGRAPH_PORT` or 8765, and the next free of the twenty after it, starts the server
with `--serve`, `--port` and `--no-browser`, the command line's other arguments, `--root` and
`--config` among them, and `IDIOGRAPH_ARGS`, its output in the launchers' log with a line
`=== <date and time>, starting on port <n> for the window`, the time where the machine is as the
launchers write it (the first build wrote UTC's), and opens the window on the page once
`/api/server` answers, within a minute. A start that fails says why in the launchers' own words and
ends. The window beats through `/api/beat` every thirty seconds, since a Mac's web view stops a
minimised page's own beat. The server has gone when its process ends or nothing listens on its
port, asked twice half a second apart, since on Windows a Restart starts it anew as another process
and the old one may linger while it lets its last connections go. Its last word in the log then
decides: after `Restarting.` the windows wait fifteen seconds for it, and after
`Idiograph is closed.`, Quit's or its own quit's, they close and the app ends. The sixth Windows
run of 17 October found Quit after a Restart leaving the windows open, the port not yet read then,
and the fix is not yet seen on Windows. The app ends when its last window closes, and stops the server by Quit's own path, a POST to
`/api/server`, asked again for thirty seconds while a write holds it, then ended. Since 31 October (quitcrash) Quit and the last window's close stop the server themselves once every page has answered, on a thread of their own and before the app is asked to end (`end` in `main.rs`), and on a Mac the windows are hidden and their web views are never torn down before the process ends, as AppKit's own Quit ends an app (`let_go`). 0.9.14 crashed as Adam quit it on 31 October after 21 hours open: each window was torn down while the app still ran on to its end, and the system's web view (WebKit 21624, macOS 26.5.2) sent a display refresh's scrolling to the page's scrolling coordinator it had already freed (`WebCore::ScrollingTree::takePendingScrollUpdates` from `RemoteScrollingCoordinatorProxy::sendScrollingTreeNodeUpdate`, an `EXC_BAD_ACCESS` at 0x122, WebKit bug 327576, whose fix, the coordinator kept alive and invalidated with its page, landed in WebKit on 26 October 2026 and is not yet in macOS), and the server, stopped only at RunEvent::Exit after the windows, ran on, still holding its port two minutes later. A window closed while the app goes on is hidden first and torn down `TEARDOWN_WAIT`, 0.6 seconds, later, once its page has stopped drawing, a mitigation the evidence does not prove. `stop_server` holds its lock for a whole stop, so a second caller waits for the first. `packaging/tauri/quit_loop_mac.py` asks Quit of a test app many times, most of them with a board moving, and counts the crash reports. A quit the Mac asks for, Quit Idiograph, Activity Monitor's Quit or a shutdown, ends it the same way. Since 27 October a SIGTERM, a SIGHUP or a SIGINT on a Mac does too (`ending` in `main.rs`): unheard, it ended the window at once, and the server it started went on under launchd until its own wait ran out five minutes later, or never in a check's run with `IDIOGRAPH_STAY_OPEN`. A SIGKILL, Force Quit, still leaves the server to quit by itself. `drive_mac.py`'s `App` notes the window it starts and everything under it as they come, and stops whatever is left at each run's end, at the drive's end and when the drive itself is ended by a signal, since `open` starts the window under launchd and never as the drive's child (area 277). `drive_menus_mac.py` and `drive_update_mac.py` start theirs through it, and `quit_mac.py` too since 31 October (loose31), where a run that failed part way left the window and its server running. `Idiograph cli`,
`Idiograph mcp` and, on Windows, `Idiograph stop`, which Setup runs, hand over to the server, on a
Mac in the same process and on Windows through `server\Idiograph-console.exe`. Add Idiograph to
Claude Desktop writes the server's own path, so for the window's bundle the entry runs
`/Applications/Idiograph.app/Contents/Resources/server/Idiograph mcp` on a Mac and
`%LOCALAPPDATA%\Idiograph\server\Idiograph-console.exe mcp` on Windows, where Tauri's installer
puts the app for the one user.

What the browser did, the window does, the page's side in `packaging/tauri/window.js`, which every
window runs before the page's own scripts, `window.__IDIOGRAPH_OS__` set first. It does nothing
without the window's bridge, so the page a browser is served, a source install's or Claude's browser
pane's beside the window, is the page it was. Since the second build the server knows the window
started it and the page has two hooks the window fills, below. The page may call three commands of the window's, `capabilities/page.json` and `build.rs`,
from 127.0.0.1 alone: `print`, which on a Mac stands in for `window.print`, which does nothing in
the Mac's web view, and opens the window's print panel, Save as PDF among it, while Windows's web view
prints by itself, `new_window`, which Ctrl+N or Cmd+N asks for, and `save_download`. A click on a link
with `download`, the PRISMA map's SVG and PNG today, is stopped, its file read and sent as base64 with
its name, and the window opens the system's save panel on Downloads with the name in it, writes the
file where it is put, and says "Idiograph could not save <name> in <folder>." when it cannot. Since 21
October `save_path` opens the same save panel alone and answers the path, which Share a copy posts to
`/api/send-project` for the server to write, so a shared project with recordings is never read into the
page (`window.idiographSavePath`). Its `message`, the page's `SHARE_LINE`, is the panel's line, through
rfd's `set_title`, which is the panel's message on a Mac and its title on Windows. A file
the web view downloads by itself, which nothing in the app does, goes to Downloads under a name not
yet there, with a message either way. A page of the server's, or `about:blank` a page writes into,
opens in a window of its own, 1280 by 800 unless the page asks for a size, so each print view is a
window that prints the same way. On a Mac such a window is made with its opener's web view setup, as
WebKit asks, and shares its opener's message handler, so what it asks reaches the app as its opener's.
Print printed the window behind, its panel out of sight, until 19 October (Adam, 18 October). So
`print` takes the page's `href` and `title`, and `asking` in `main.rs` prints the window on both, else
the one window with that title, as a window written in has its opener's address, else the one in front
on the address, and window.js gives a window opened on `about:blank` and written in, the
canvas's print, the same Print from the page that opened it. Such a window also shares the scripts
of every window it opened or was opened by, so Tauri's own script runs after window.js there and sets
its own `print`, `plugin:webview|print`, which the capability refuses, so the Print button did nothing
at all. window.js, run again, sets its own Print again. Every other command such a window asks
reaches its opener the same way.

A Mac's print panel takes its page from the print info alone, never from the page's own `@page`
size, and Tauri's print opened it on the shared print info, portrait on the Mac's default paper, so
from the window's first build (17 October) to 28 October every print view, though it asks for
landscape A4 and Chrome's PDF of it is landscape, came to the panel portrait (Adam, 28 October, eight
portrait pages of a table of PETs). Since then window.js reads the page's own size from its style
elements (`idiographPagePaper`, the last `@page` rule that says one, a margin box's own declarations
left out, a named paper alone portrait as CSS has it) and `print` takes it as `orientation` and
`paper`. With them `mac::print` sets them on a copy of the shared print info, the paper first and the
orientation turning it, before it opens the panel as wry's print did, its margins nothing, so the
table of PETs, the GET table, the trail and the full set open on landscape A4 and the canvas's print,
which asks for landscape alone, on landscape on the person's own paper. He is still free to change
either in the panel, the shared print info is left as it was for the next print, and a page that says
no size, the app's own, prints as before. Windows's web view prints the page through Chromium's own
print preview, which takes the page's `@page` size as Chrome does, so it needed nothing. A check's
build (`drive`) with `IDIOGRAPH_WINDOW_PRINT_TO` writes each print there as a PDF with no panel, and
`drive_mac.py --pdfs` prints every view so, the page's paper with it and, for comparison, without
it. Area 287 holds the reader on every view.

Since 31 October (pdfexport) `mac::print` holds the web view's `pageZoom` at 100% for every print and
gives it back once the print has run, in its delegate `Printed` (`printOperationDidRun:success:contextInfo:`,
the panel's Cancel among the ways it ends), which also tells a caller whether it ran. The Mac's web view
lays a print out at its page zoom, so the table of PETs came out 3% larger at Large and 14% larger at
200%, with four pages more. Export as PDF was the command `save_pdf` until typst5 (9 November 2026), when the server
came to make every PDF with Typst and the command went (see Every export through Typst): (`href`, a page of the server's,
`path`, a `.pdf` in a folder that is there, `margins`, the page's own in millimetres, and `foot`): the
print view loaded in a hidden window of its own, printed to the file with no panel, then let go, the
path answered or why not, a print that never ends given up after a minute. On a Mac it is `mac::print`
with a save to the file, so the pages are Print's (Juno's table: Print 6 pages, Export 6 pages, at text
size 100% and 125%). On Windows it is WebView2's `PrintToPdf` (`ICoreWebView2_7`, settings from
`ICoreWebView2Environment6`): landscape A4, the page's margins, which WebView2 takes over the page's own,
backgrounds on and Chromium's own head and foot off, the page's margin boxes drawn by Chromium as Chrome
draws them. That code has not been compiled or run: the Windows window is built only by the release.
The page reaches it through `window.idiographSavePdf(href, path, margins)` in window.js. The server
names the path: `/api/themes-export` with `op` `pdf` and `/api/gets-boards` with `op` `pdf` answer `path`,
`name`, `shown`, `dated` and `margins` (`print_pdf.margins_of`), a dry run of `print_pdf.write` and
`write_gets`, so the file goes where the agents' `board export --pdf` and `gets export` put theirs, named
the same, the date and time added when a file of that name is there. They write nothing. `themes_reveal`
takes a PDF beside the workbook as it takes the Word document.

The foot on the Mac (31 October, exportpdf2). The Mac's web view draws no `@page` margin box, so its
print had no foot line. window.js reads the foot from the page's own style elements, as it reads the
paper (`idiographPageFoot`: the `@bottom-left`, `@bottom-center` and `@bottom-right` boxes' `content`,
strings and `counter(page)` and `counter(pages)`, a later box winning unless the earlier is `!important`
and the later not, as `server.PRINT_MARGINS`' empty box comes after the page's own, with the box's
`font-size`, `color` and first `font-family` and the `@page` margins in millimetres), and hands it to
`print` and `save_pdf` as `foot`, `idiographSavePdf` fetching the print view's own page for it. So the
foot's words are said in one place, `themes_print.page_foot`. `mac::print` gives the print operation's
view, WebKit's `WKPrintingView`, a subclass of its own made once at run time
(`IdiographFootedWKPrintingView`, `footed`, the instance's class set to it) whose
`drawPageBorderWithSize:` (`draw_border`) calls WebKit's own and then draws each box in the bottom
margin, as AppKit lets a view draw round each page: the left box at the left margin, the middle one
halfway between the other two since 1 November (below), the right one ending at the right margin, each in the middle of the margin's
height as Chrome sets a margin box, the page from `NSPrintOperation`'s `currentPage` and the count from
its `pageRange`. The text is drawn in the paper's own space, the context's flipped state read, never the
view's. WebKit draws the border again on the main thread when the print runs on a thread of its own, so
each page is given its foot once (`Foot.drawn`). The pages are laid out by WebKit as before, so the
count is the same with the foot as without. This is the window's Print, its panel's preview and Save as
PDF in it, and Export as PDF alike. A print in Safari, outside the window, still has no foot. The
other way, stamping each page of a saved PDF with PDFKit, would have reached Export as PDF alone, not
Print to paper. Area 311 holds the reader and that Print and Export as PDF hand the window the page's foot.

A foot that never collides (1 November 2026, pdfpolish, Adam: "the middle ... dynamically centred ... or do we just
add an ellipsis ... I think we should have an approach for it"). One rule in every PDF: the middle part sits
halfway between the end of the left part and the start of the right, and when the three would come closer than
`FOOT_GAP_MM`, 6 mm, between each two, the project in the left part is cut at the end of a word, as few words as it
takes, a comma or colon there taken off, and ends in "…". The participant, the board, the table, the name, Confidential, the date and the page are never cut.
Chrome centres `@bottom-center` on the page and gives the left and right boxes what is left either side, so a long
left part wrapped under the middle one. Margin box content is text alone and the server cannot measure the type
the browser will choose, so the page measures itself: `themes_print.foot_fit` puts `FOOT_FIT` in the print view
(and the GETs print), with the left part's pieces (`foot_pieces`), the piece it may cut, the middle, the right as
"Page 00 of 00" for the fit and "Page 0 of 0" for the centring, the room between the page's margins (`foot_room`,
from its `@page` rule) and the type. As the page loads it measures each in a hidden span in the foot's own face and
size, cuts the project at a word, halving over its words' ends, until the three fit, and adds a style, marked `data-foot-fitted`, whose
`@bottom-left` holds the left part, as many no-break spaces as reach the middle's start (measured as the line
sets them) and the middle, and whose `@bottom-center` is `none`. So Print in Chrome, the agents' headless Chrome
(`print_pdf.render`) and Windows's WebView2, which is Chromium, all print the same foot. On the Mac the window
draws the foot itself: window.js leaves the fitted style out (`style:not([data-foot-fitted])`) and reads
`--idiograph-fit` from the left box as `foot.fit`, and `draw_border` measures each part with
`NSAttributedString`'s `size` on each page, decides the cut against "Page 00 of 00" as the page's script does, so
both cut the same words (`word_ends`, `cut_at_word`), and places the middle by `mac::foot_places` with the page's
own number. The print is laid out at its true size whatever the window's text size, and the foot with it: at
100% and at Large (125%) every part is drawn at the same point. Juno's table: the middle 58.0 mm from the left
part and 57.7 mm from the right. An invented participant with a 112-character project and a 37-character name:
the project cut after "care" in both, where the left part wrapped onto two lines in Chrome and ran over the
middle on the Mac before. Area 311 holds the cut
and the centring in node with type of a fixed width, and the window reading which piece to cut.

The table of PETs as a Typst template (typst2, 9 November 2026, and Adam, 9 November about 18:10: Typst is the one
engine for every PDF, no fallback). `apps/idiograph/typst/pets_table.typ` holds the view, `pets-table(d)`, which a
full set can `#import`, and `pets_table_main.typ` reads the data, the input `data` holding the JSON text, sets the
document's title and author and calls it. `themes_print.TEMPLATE` names the main file, the folder Typst's root.
`themes_print.typst_data` makes the data with the same arguments as `page` (less `auto`), and both read the board
through `themes_print.walk`, the board as the canvas reads it with the stacks and descriptions the ticks ask for,
each label's tint (`tints`) and the labels letters or numbers (`themes.pet_numbers`), so the two views cannot
disagree about what is on the board. Every word the page prints is in the data in the run's language, so the
template holds none. It carries all `page` prints: the head as a grid of two by two (the participant with the
table's name under it, in two fifths of the width at most, PROJECT and RESEARCH QUESTION to the right), the board's
note with `note`, each PET in its band with its number, its title in capitals and its description, a sub-theme and a
group (`block_data`, depth 1 to 4, the type and indent stopping at `DEEP` as `.deep` does), notes, rows of a
statement, its reference in Nunito Sans with tabular figures and its quote at 136 mm, a discard's reason and the
statements stacked under a top, "Nothing in it yet." and the empty board's line, and Not placed and the statements
set aside with their counts. A label's lead (its heading, note and first row, or its first sub-theme's lead) is a
block a page never splits, the rest flowing a row at a time, so a heading never ends a page and a row is never
split, as `.lead` and `.cont` do in the HTML. The foot is drawn on every page in three parts from
`typst_data`'s `foot`: the left part's pieces and the one that may be cut, the middle, "Page {page} of {pages}"
from the catalogue, the room between the margins (`foot_room`) and `FOOT_GAP_MM`. Typst measures them in the
foot's own type, cuts the project at a word end with "…" (any comma, colon or stop before it taken off) when the
three would come closer than the gap, and places the middle halfway between the left's end and the right's start,
the right measured at the last page's number on every page. "Leave out the board's name" takes the board off the
foot and out of the document's title (`title_of`), as on the HTML view. Lines CSS sets at `line-height: normal`
take the font's ascender and descender in Typst (`normal`), and the rest a box of their line height (`lh`). On the
demo's Juno and an invented board with every part, every page of the Typst PDF opens on the same row as Chrome's
print of the HTML view in the same two fonts (7 and 6 pages).

A print change is now made in two places, `themes_print`'s CSS and HTML and `pets_table.typ`, and area 363 is the
drift check that catches a miss: it reads each piece of the HTML view's text (`page`) and finds it on the Typst
PDF's pages (`family/pdftext.py`) in the same order, the head's in any order on the first page and a row's parts
from the row's start, so a word, a part or a row left out of the template, or added to one view alone, fails. It
also checks each page after the first opens on a row's start, no page ends on a heading, every foot has its three
parts and its "Page n of N", the long project cut at a word and a short one whole, numbers, five levels, a reason,
the board's name left out, and the empty board, never a pixel, a colour or a size. The HTML view is set in the same
two faces, Charis SIL (`--serif`) and Nunito Sans (`--sans`, `FOOT_FAMILY`), through `FONTS_LINK`,
`/fonts/fonts.css`, which the server serves from `family/static/fonts/`, so the screen and the PDF match, the
system's faces after them only for a page opened where the fonts cannot be reached.

Cmd or Ctrl and a click, or a middle click, on a link of the app's
opens it in a new window. Every other address opens in the default browser through the opener plugin.
Tauri's own handling of drops is off, so the page's own takes a file dragged onto it. On GitHub's
Windows machine a file dragged from another program reaches the page and drops there (the second
build's third run, a drag that lets go once the page has said it takes a copy), where the first
build's drag, let go by the mouse at once, ended as a dragleave, the test's fault and not the window's. The menus are the second build's,
below. On Windows the windows stay separate, with no tabs of their own (Adam, 17 October).

The bundle is `uk.co.adamknowles.idiograph`, the Mac app's own identity, and every check builds the
test app instead, `uk.co.adamknowles.idiograph.test`, Idiograph Test, so no test copy is taken for
the real app. A check builds with the `drive` feature, which no shipped build has: a script run in
every window once its page loads, which `packaging/tauri/drive_mac.py` uses on a Mac, starting the app
with `open -g -n -W` so it never takes the keyboard, with `screencapture` for each window and sheet.
On Windows, `.github/workflows/tauri.yml` built and installed the test app on a push to `spike/tauri`
alone (dropped on 21 October, before the public copy, since two of its jobs took files from runs of the
private repository), and `packaging/tauri/drive_windows.py` drives it through WebView2's own debugging port,
`WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=9222` in the check's environment
alone, with Playwright's `connect_over_cdp`. `drive_common.py` holds their invented world, dogs at
home, the stub they report to and the page's steps. Since 3 November (drivefix) its screens are
Idiograph's own, the Statements, PETs, GETs and Settings, since Sift and Trace are apps of their own with
windows of their own and Idiograph's page has neither, and `drive_mac.py`'s save is Share a copy of the
whole project from Home: the save panel with the file's name, the file the server writes where the panel
answers, and in the second run, with the answer a missing folder, the card's line that nothing was sent.
An error a step meets is said with its own words before its stack, which the Mac's web view leaves out.
The page's script gives up each ask of the stub after five seconds, since the Mac's web view now and then
left one unanswered for good and every step after it went unanswered, Quit's among them, and the stub
hands a step again until its answer reaches it, which the page answers again without running it twice. Since 4 November (winprisma) `drive_windows.py` and its second, third and fourth builds are level with that on paper: no Sift or Trace screens (the PETs board stands where Sift's page was in the whole-page and scroll bar steps), no setup step, and the save is Share a copy through Windows's own save panel, found by its title (the card's line, `SHARE_LINE`, its full stop off, as the window titles it), answered by Enter, the file found in Downloads with its zip header. Its save-fails step types a name in a folder the user may not write to (an `icacls` deny, lifted after) and reads the card's line, and says so when the panel refuses that folder itself and stays open. No machine or workflow has run these since `tauri.yml` was dropped, so none of it has run on Windows: it was checked by compiling and against the page's functions as they stand, and its first run may find the title match or the locked folder wrong. Of the launchers' jobs, the window does not write
the line of every launch in the trace file or the pid file beside the log, since only the launchers
read them, their Stop, Restart and Open, and `stop_all`, which Setup runs, finds a server by its port
and command line and only removes the pid file. The Stop, Restart and Open dialog is gone, bringing
the window forward and Settings' Restart and Quit standing in for it.

**The window's menus and its state (Tauri, 17 October, the second build).** The menus are
`packaging/tauri/src-tauri/src/menu.rs`, each system's own. On a Mac: Idiograph (About Idiograph, since 20 October the
page's own card, `openAbout` in app.js, through `__idiographMenu('about')` as on Windows, Settings… on
Cmd+comma, Services, Hide Idiograph, Hide Others, Show All, Quit Idiograph on Cmd+Q), File (New Window
Cmd+N, Open Recent, Close Window Cmd+W), Edit (Undo Cmd+Z, Redo Shift+Cmd+Z, Cut, Copy, Paste, Select
All, Find… Cmd+F and Find and Replace… Shift+Cmd+F since barsD, 6 November 2026, then Spelling and Grammar), View (Home Cmd+Shift+H since 20 October, `__idiographMenu('home')` calling the page's `idiographHome`, then Bigger Text Cmd++ (the numeric pad's plus, so the menu shows it, and Cmd+= or Cmd++ as the page hears them), Smaller Text Cmd+- and Actual Size Cmd+0, until 20 October Zoom In, Zoom Out and Actual Size, Reload Cmd+R,
Enter Full Screen), Window (Tauri's `WINDOW_SUBMENU_ID`, so AppKit fills it with the windows and its tab
items, Show Previous Tab and Show Next Tab on Ctrl+Shift+Tab and Ctrl+Tab among them, Minimize, Zoom,
Bring All to Front, where the first build's own pair on Cmd+Shift+[ and ] stood twice beside the
system's) and Help (Tauri's
`HELP_SUBMENU_ID`, so it has the system's search field, then Idiograph Manual, Keyboard Shortcuts and Send
Feedback…, greyed while the build has no collector). On Windows every window carries File (New Window
Ctrl+N, Open Recent, Settings Ctrl+comma, Close Window Alt+F4, Exit), Edit (Undo Ctrl+Z, Redo Ctrl+Y,
Cut, Copy, Paste, Select All, &Find… and Find and R&eplace…, their keys in their words as Home's are), View (Home, Alt+Home in its words as the page hears it, then Bigger Text, Smaller Text and Actual Size on Ctrl with +, - and 0, Reload
Ctrl+R) and Help (Idiograph Manual F1, Keyboard Shortcuts, Send Feedback…, About Idiograph, the
page's own card since 20 October, where a message of the system's own stood), each letter marked for Alt, and no Window menu. Windows's Edit items are the
window's own (`press_in_page`): each gives the web view the keyboard, then presses Ctrl and its key
there, so they act as the keys do, since muda's own pressed them before the web view had the keyboard
back from the menu and nothing reached the page (the second build's third Windows run), and the page
takes Ctrl+Y for Redo off a Mac (`REDO_Y` in `static/app.js`, on the statements screen and on a board). The
Mac's Undo and Redo are the window's own: `window.js` sends the page Cmd+Z or Shift+Cmd+Z, which a board
or a list takes for the app's undo, and when the page leaves it, as in a text field, the window sends
`undo:` or `redo:` to the field as the system's Edit menu does. Settings…, Keyboard Shortcuts and Send
Feedback… press the button of the bar in view (`window.js`, `__idiographMenu`), and Reload saves what
is typed first. File, Project History (histmenu, 4 November 2026, on Windows too, unbuilt there) opens the project's History sheet through `__idiographMenu('project-history')`, the page's `idiographProjectHistory`. It sits in File under Open Recent, and File, Project Settings… under it (settingsplit, 5 November 2026, `__idiographMenu('project-settings')`, the page's `idiographProjectSettings`, opening the project's own sheet), on wherever any project is open, a demo's included, since a demo's sheet opens read-only: `idiographProjectSettingsNow` (`projectHere` in `distil.js`) goes with `on` as `project_now`'s `settings`, `menu::set_history(on, settings)`, a page from before it saying nothing and the item following History. It is grey until the page says a project is open: `window.js` asks `idiographProjectNow` twice a second and on focus, and tells the command `project_now` on a change (`menu::set_history`), so every menu bar's item follows the last window to say. None for Home and the demos (`projectNow` in `distil.js`, from `S.home`). Edit's Find… and Find and Replace… (barsD, 6 November 2026) press the page's own keys where the focus is, `Cmd+F` or `Ctrl+F` and with Shift, through `__idiographMenu('find')` and `__idiographMenu('find-replace')` (`find` in `window.js`), as Undo and Redo press theirs, on the window in front, so each does just what its key does there: Search, and the statements screen's Find and replace card. Find and Replace… is grey but on the statements screen, `idiographReplaceNow` in `distil.js` going with History's and Project Settings' flags as `project_now`'s `replace`, `menu::set_history(on, settings, replace)`, a page from before it saying nothing and the item grey. No command was added, so the capability file and `build.rs` are as they were. Open Recent is the home screen's projects as the page hands them over each time it
draws the home screen (`windowRecent` in `app.js`, the command `recent`): Sift's, Idiograph's with the demo
last, then Trace's, each part under its word, and one opens in a new window seeded with the place its
card opens, a Idiograph project's page through `idiograph-home` and a Sift or Trace project through
`idiograph-return`, as a Restart comes back. The zoom is the window's (`zoom_hotkeys_enabled(false)`
on every web view, whose own zoom keys on a Mac needed a permission the page has not): `window.js` takes
Cmd or Ctrl with =, +, - and 0 and the command `zoom` steps every window through a browser's steps, 50
to 300 per cent, kept for the next run. Since 20 October the zoom is the window in front's
(`zoom_on`): the page names its own address and title with `zoom`, as with `print`, since on a Mac a
window the page opens shares its opener's message handler and so asked as the window behind it, and
View's Bigger Text, Smaller Text and Actual Size take `front`. Since 20 October (Settled 12) `zoom` takes `to` in
place of `by`, Settings' Text size, Small 0.9, Medium 1 and Large 1.25, which `keep::set_zoom` keeps as the
nearest step (`keep::nearest`), and answers the app's zoom either way, which window.js's `idiographTextSize`
hands the page. Every change of the app's zoom is told to each window as the event `idiograph-zoom`, so
Settings' rows follow the keys and the menu. The page ticks Small at 0.9, Medium at 1 and Large at 1.25
(`textSizeOf`, none between them), and shows the rows only where `idiographTextSize` is there. Where the zoom
stands at none of the three, no row is ticked and the heading says the size, "Text size: 110%"
(`page.text_size.title_at`, 30 October, option A of the round drawn for Adam). The page also says the new size
in its toast, "Text size 110%" (`textSizeSay`, `shell.text_size.said`, the percent through `tNum` so the Numbers
format writes it), on every `idiograph-zoom` that the keys or View's items made: the event comes twice for a
change (the window's `eval` and `told`) and `say` replaces its one line. A row picked in Settings is not said
(`textSizePick`, the same zoom within 1.5 seconds), and a browser's tab has no event and no
`idiographTextSize`. It is the page's script alone, so no window build is needed. A mouse's back and forward
buttons (`mouseup` with button 3 or 4) are the history's Back and Forward on a Mac, where WKWebView leaves
them to its app. An app's own page zooms every window as one,
as before, and a print view or the manual zooms alone from the app's zoom (`OWN_ZOOM`, `keep::step`),
keeping its own while the app's changes. In a Mac's print view, `/themes/print`, `/gets/print` or a
window written in on `about:blank`, Cmd+S opens that window's print panel, where Save as PDF is. A
window written in loses `window.js`'s listeners as it is written, so `keysFor` gives the canvas's print
its keys again once its page is there (`data-idiograph-keys` on its root), and since it then has its
opener's address the window keeps its label in `WRITTEN`, so `own_page` and `front` never take it for
the app's own page, for the zoom, New Window or Settings, nor asks its page as it closes: its answer
came as its opener's, so closing the canvas's print closed the window behind it and the app with it
(seen on the drive build of 20 October). File, New Window, from the
menu (`front` among the app's own pages, its page asked with `NEW_WINDOW_JS`) or Cmd or Ctrl+N, opens
on what that window shows (`__idiographNewWindow` in `window.js`, the command `new_window` with `place`
and `hash`): `spotNow()` as `idiograph-return` with the home screen's `idiograph-home`, the window's
start as a Restart's, and the address `/#open=` and the spot, the form Open in a new window gives, so
both open alike. A print view or the manual opens the home screen. Help, Idiograph Manual opens `/manual` in a window of its own,
`docs/manual.md` as one page with its sections listed at its head (`manual_page` in `server.py`), read
from the copy the bundle carries beside the server, which the window names in `IDIOGRAPH_MANUAL`, and
in a run from source from `docs/`.

**A shared copy opened from outside the app** (fileassoc, 6 November 2026, after a tester's copy came back and the
Finder did not know it). `tauri.conf.json`'s `bundle.fileAssociations` makes `.idiograph` (`project_pack.SUFFIX`)
Idiograph's own document type: `name` `Idiograph.SharedCopy`, which is `CFBundleTypeName` on a Mac and the ProgID
Tauri's NSIS template writes on Windows (`APP_ASSOCIATE`, HKCU `Software\Classes\.idiograph` to the ProgID, its
open command `Idiograph.exe "%1"` and its icon the executable's own), `description` "Idiograph shared copy", the
Mac's `UTTypeDescription` and Explorer's Type, `role` Editor, `rank` Owner, and `exportedType`
`uk.co.adamknowles.idiograph.shared-copy`, conforming to `public.data` and `public.content`, the
`UTExportedTypeDeclarations` entry the app exports. There is no document icon of its own: the Mac draws Idiograph's
icon on a page for it, and Windows shows the executable's. `bundle.NO_FILES`, `fileAssociations` null, which
Tauri's merge of a `--config` file takes away, is laid over it for Sift and Trace (`app_conf`) and for every test
app (`overrides`), so a double click never opens another app of the family, nor a test copy built on this Mac in
the place of the real app. The files reach the window three ways (`src/opening.rs`). On a Mac it is
`RunEvent::Opened` in `app.run`, whether the file started the app or it was open, which covers a double click, a
drop on the Dock's icon and Open With. On Windows it is the command line, `opening::apart` taking each argument
that is no option and no option's value (`--port`, `--root`, `--config`, `--app`) as a file, made whole against the
start's folder, before `split_args`, so none reaches the server. And on Windows a start while Idiograph runs is
ended by the single-instance plugin (already in the shell) before it starts a server, its arguments, its own path
first, and its folder handed to the running app's callback, which takes the files and leaves `bring_forward` to a
start with none.
`opening::keep` holds them, Idiograph's alone (`app::this()`), until a window of the app's own page takes them
with the command `opened` (build.rs, the capability's `allow-opened`, `own_page` checked), each once. `window.js`'s
`__idiographOpened` asks it on the page's `load` and whenever `opening::hand` tells the window in front with
`TELL_JS` and brings it forward (`front`, among the app's own pages). Before the first window is open nothing is
told and its page takes them as it loads. With only the manual open, a window opens on Home and takes them. A page
with no `idiographOpenFile`, a print view's or the manual's, takes nothing. The page's `idiographOpenFile`
(distil.js) queues each file and `sentHanded` waits for the page's start (`S.started`, `homeStart` in shell.js,
Home drawn and the screen kept opened again), then for any card (`searchCovered`) or dialog (`PICKING`) to close,
leaves the screen in front with `goHome`, stopping where a save fails, and calls `openSentFile`, the very path
`openSentPress` takes once the window's dialog has chosen: `/api/open-sent` with `check`, then `cbOpen` for a copy
coming back or `sentInto` for the folder. A refused file says the server's own words, `say(err.message)`. The
bundler's Info.plist was read for this build in a scratch debug bundle (CLI 2.12.1): Idiograph's holds the
`CFBundleDocumentTypes` and `UTExportedTypeDeclarations` entries above, Idiograph Test's neither. The release run's
Windows installer is the first to write the ProgID, which `reg query HKCU\Software\Classes\.idiograph` shows.

**The licence** (21 October). Idiograph, Sift and Trace are under the GNU AGPL v3, its text verbatim in
`LICENSE` at the repo's root, and `NOTICE.md` opens with the copyright and the two additional terms of
its section 7, credit (7(b)) and names (7(e)), before the third-party list. Every build ships `LICENSE` and
`NOTICE.md` beside the modules, the family's files in `app_identity.FILES`, and `build_windows.py` takes the same
list. The
Tauri project declares `AGPL-3.0-only` in `Cargo.toml` and in `tauri.conf.json`'s `bundle.license`. The
server answers `/licence`, a shared route, with `LICENSE` as plain text, 404 in a copy without it, and
the About card's GNU AGPL v3 links there, so it opens in a window of the app's own with no internet.
The card names its author once, "By Adam Knowles" under the version, and the licence's line starts
"© 2026.", never the "Based on" credit of section 7(b), which is for a work derived from it.

The main window's size, place, maximised and full screen are kept by the window-state plugin, 2.5.0,
in `.window-state.json` in the app's config folder (`uk.co.adamknowles.idiograph` under Application
Support on a Mac, under `%APPDATA%` on Windows), never whether it was shown, so a check's window is never
brought forward. Beside it the window keeps `window.json` (`keep.rs`): `local`, every setting the page
keeps in the browser under a key that begins `idiograph-`, the folds, filters, Sift's step and the
appearance among them, which a browser keeps for each origin, the port included, so a window on 8766
while 8765 was taken started them all blank. Every window opens with them in
`window.__IDIOGRAPH_SEED__`, which `window.js` lays into the page's storage once a window, before the
page's own scripts read anything, taking out a key of the page's the app no longer keeps, and every
change the page makes goes back through the command `keep`. The first window of a version that kept
nothing yet hands the port's own over. `place` is the session's `idiograph-return` and `idiograph-home`
of the last app window to close, which the first window after a relaunch is seeded with, so it opens
where he was, the page taking a Restart's place only within ten minutes as it always has, after an
update's relaunch among them. A browser's tab keeps all of these for its own origin, as it did.

A window of the app's own page asked to close, by its close button, Close Window or Quit, is held
while its page answers
(`ask_close` and the command `closing`): `window.js` asks the page whether anything typed is unsaved as a
browser asks before a page goes, saves it with the page's own `savePending` when it is, tells the page
it is going with `pagehide`, so it keeps its place and the canvas sends a save still to go, and hands the
place over, and the window closes, on a Mac since 31 October hidden at once and torn down a moment later,
or during Quit and as the last window kept whole until the app ends (see The window, above). A page that cannot save asks "What you typed here could not be saved.
Close the window anyway?" with Close Anyway and Cancel, and Cancel keeps the window and ends a Quit. A
page that does not answer within three seconds is closed without it. Quit asks each window in turn, the
one in front last, so its place is the one kept. The Dock's Quit and a log out end the app as AppKit
ends it, with no question asked of the pages. A print view or the manual closes at once, as it has
nothing to save, and must while its print panel holds its page, which on Windows holds every page of
the app with it (the second build's first Windows run).

The page in the window: every window takes its page's title, which the page sets twice a second from
the bar in front (`pageTitle`, the app first and then what is open: its project, its participant and its
screen, as in "Idiograph - Living with a dog - Juno - Experiential statements", the home screen Idiograph, a project's
page Idiograph and its project, GETs, LGETs, Trajectories and the Code list the project and the board, PETs and LPETs
the participant too, and Sift's and Trace's screens the app and the project, 6 November 2026, headroom: `titled(app, ...parts)`
joins what the screen has, so no dash stands alone, and `distilTitle` reads the project from the bar's path and the
participant through `caseShown`, "P2 Wren" with a space where the label has a dash, so the separators stay clear,
as the print views name theirs), so two cases in two windows tell apart in the Dock, the taskbar and Alt+Tab, and a
browser's tab takes the same title. Each Tauri window takes `document.title` as the page changes it
(`on_document_title_changed` in `main.rs`, set on every window), so the Mac's and Windows's window titles need no
word of their own. Choose opens the system's own folder
dialog on the window, on either system, through the command `pick` (rfd), which `window.js` gives the
page as `window.idiographPick`, and `picking` in `app.js` then sends the folder as if typed, with the
words the Mac's dialog says (`PICK_SAYS`). The server is started with `IDIOGRAPH_WINDOW`, which a
Restart carries over, says `window` in `/api/server`, and then quits by itself after the window's beat
stops whatever General's tick says, which the page then hides, since the app quits as its last window
closes. On a Mac, a web view checks no spelling until told, so it underlined nothing, and a default
registered for it went unread: each window turns Check Spelling While Typing on as the menu item does
(`mac::spelling_window`) while he has never chosen, which WebKit then keeps in the app's defaults as
`WebContinuousSpellCheckingEnabled`, and Edit gets Spelling and Grammar as Safari has it, where he can
turn it off for good. Nothing of the browser's
own reaches paper: an empty `@top-right` and `@bottom-right` box in the page's margin keeps out the date,
the title, the address and the page count Chromium prints, and so WebView2, the address with the
project's folder in it on the GETs page's foot (17 October, the first build's Windows shots). The
server puts them in every print view it serves (`own_margins`), and `style.css` and the canvas print
have them. Every scrollbar is thin and in the rules' ink (`style.css`), where Windows drew its grey bars
of 17 pixels. The page scrollbar of twice the window's height that the first build's Windows shots showed on the
statements screen, PETs, GETs, Settings and the closed page was Sift's or Trace's screen, each 100vh,
left showing under the home screen when the check went home from it through `loadLibrary`, which now
hides every other screen as it shows the home screen, in a browser's tab as in the window. A save panel names its one type as the system does, "PNG image (*.png)" on Windows. The
server's last word since the window started it (`last_word`) is waited for once it has gone, as it
comes a moment after its socket closes, while the server waits for a write in hand: read too early,
the third Windows run of the second build took a Restart for a server that had failed and stood
waiting on that word, so Quit after a Restart left the windows open. A server that ends with no word
of Quit's or a Restart's says so before the app ends, since the fifth build in Adam's words and once (see
below), and with the log's last lines before the
app ends. A Windows Restart ending
the old server under a request still open no longer logs a traceback (`_send`). The checks are area
167, and on the Mac `packaging/tauri/drive_menus_mac.py`, and on Windows the second build's steps in
`drive_windows.py`.

**The installers, the release and the update key (Tauri, 17 October, the third build).** Idiograph
ships as the window (Adam, 17 October), built unsigned for two testers, and updates through Tauri's own
updater, the fourth build's, from a public repository's releases: Pharkie/idiograph-releases until 0.9.23,
and from 0.9.24 the app's own, Pharkie/idiograph (pubreadme, 10 November 2026, below).
Both installers are Tauri's, made by the two build scripts above through `packaging/tauri/bundle.py`,
which lays the window's source out under the build folder as the app's folder holds it, the frozen
server as `build/tauri-server`, the manual as `docs/manual.md` and each file the window's source builds in
from beyond `packaging/` (`WINDOW_BUILDS_IN`, English's `family/static/i18n/en/menus.json`, which `words.rs`
names by `include_str!`) at its own path, so `tauri.conf.json`'s paths and the source's find them as in the
checkout (the 0.9.11 tag run failed for want of the menus there, area 173 checks every one) and nothing is
written in the checkout, and runs the CLI, Tauri's own at 2.12.1, which
`IDIOGRAPH_TAURI_CLI` names when it is installed and npx fetches when not, with `CI=true`, so the disk
image is made with no Finder window scripted on the screen. On a Mac the server goes in through
`tauri.macos.conf.json`'s `files`, which keeps PyInstaller's links as links, where `resources` copied
each as a file, and on Windows through `tauri.windows.conf.json`'s `resources`, the installer's own
steps in `hooks.nsh` (see The
Windows app). A build lays the server's version over
`tauri.conf.json`'s, and a check's build the test app's identity. The Mac's update file,
`Idiograph.app.tar.gz`, is the app under its own name at the archive's top, its links and modes kept,
in a fixed order, so the same app makes the same file. Installers are built only by hand or on a v tag,
never on a push to main: the workflow's `mac-app` job, on a tag or when asked, builds for Apple Silicon
alone on an Apple Silicon runner from python.org's Python, and a tag puts `Idiograph.dmg`,
`Idiograph.app.tar.gz` and `Idiograph-Setup.exe` on a draft release of the app's repository.

`packaging/release.py`, on Adam's Mac and on his word, takes them from that draft with `gh`, reads the
version's notes from `docs/whats-new.md`, newest first, its number and date as a heading and a plain
line a part under it, eight at most, signs the update files (the Mac's, the Windows installer and, when the draft has it, the Linux AppImage), and writes `latest.json` in Tauri's
updater's form: the version, the notes, the date and, for each system, the file's address on the
releases repository and its signature, the Mac's `darwin-aarch64` alone (`release.MAC_PLATFORM`),
never `darwin-x86_64`, a Mac app whose executable has no arm64 part refused before anything is signed,
and `check_manifest` finding fault with a manifest that lists another Mac or none. It signs with
the update key from the macOS Keychain, `idiograph-update-key` and its password
`idiograph-update-key-password`, read through `security find-generic-password` at the moment it signs,
never printed, written to a file or put on a command line, and never a GitHub secret, since the
workflow signs nothing. The signatures are minisign's, as `tauri signer sign --app-version` makes them,
in `packaging/minisign.py`, Python alone, RFC 8032's Ed25519 with BLAKE2b and scrypt from the standard
library: each binds the file's name and the version in its trusted comment, so a manifest cannot pair a
newer number with an older file, which the updater since its fix for CVE-2026-95625 checks. Every
signature is checked again with the public key before anything is uploaded, and a key whose public half
is not `tauri.conf.json`'s is refused, Adam's own since the fifth build, since every copy of the app checks
against that one. Then it uploads the three files and `latest.json` to the releases repository with
`gh`, its first commit made first when it is empty, published, or a draft with `--draft`, and a version
there already is refused. `--dry-run` does all but the upload, into `build/release/<tag>`. Empty means
GitHub answers 409, "Git Repository is empty", for the newest commit, never a size of 0, which GitHub
gives a repository holding a short README alone: on 22 October that took idiograph-releases for empty,
and 0.9.3's upload was refused making README.md again. An upload that fails after signing says the line
that finishes it, `release.py <tag> --from build/release/<tag>`: a folder with `latest.json` and
`notes.md` beside the files is uploaded as it is, its signatures checked again with the public key, and
nothing is signed twice.

**Releases on the app's own repository** (pubreadme, 10 November 2026, Adam's ruling about 12:50: the
repository public, still a Preview). From 0.9.24 every copy asks
`https://github.com/Pharkie/idiograph/releases/latest/download/latest.json` (`tauri.conf.json`,
`app_identity`'s `releases`, whose `endpoint` Sift and Trace build from, they keeping their own releases
repositories, since `releases/latest` is one release a repository). `release.py` publishes to each repository
in `names(app)["repos"]`: Pharkie/idiograph, and for the transitional 0.9.24 Pharkie/idiograph-releases too
(`release.ALSO`), where every copy up to 0.9.23 asks, so they update to one that asks the new address. Each gets
its own `latest.json` and `notes.md`, every address in them on that repository (`for_repo`, the signatures the
same, since they sign the files), the other's in `build/release/<tag>/to-Pharkie-idiograph-releases/`. On
Pharkie/idiograph the tag's draft, which the workflow made with the files, is given `latest.json` and its
notes and published (`gh release upload --clobber`, then `gh release edit --draft=false`), never a second
release made. A repository that has the version published already is passed over and said, so a run that
failed half way finishes the rest with the `--from` line, and one GitHub says is archived is passed over too,
so once idiograph-releases is archived nothing here changes. Every release's notes end on "Which file do I
need?" (`which_file`), the table the README has: each computer and its download in this release, the Linux rows
only when the release has their files. The file names carry no version, so
`releases/latest/download/<file>` always finds the newest. The `idiograph-release` helper outside the
repository still fetches the Mac app from idiograph-releases, which holds 0.9.24 too, and moves to
Pharkie/idiograph once that one is archived.

**Weekly releases and the maintainer's daily Mac copy** (macdaily, 9 November 2026, Adam, 9 November about
13:20). A release goes to GitHub once a week, on Mondays, for the Mac, Windows and Linux, since each tag run
costs about 120 Actions minutes. The maintainer's own Mac copy is built on his Mac each day from main by
`packaging/mac_daily.py`, which spends none. It exports the commit (`--ref`, main by default) with `git
archive` into `.verify/macdaily/src-<sha>`, never the working tree, and runs that export's own `build_mac.py
--unsigned --build <sha> --out .verify/macdaily` through `~/.claude/bin/heavy idiograph build`: the workflow's
mac-app job's build, the same pins, the frozen server, Tauri's bundle at the pinned CLI, arm64 alone and
signed ad hoc as the job signs it. The build folder is kept between days, so the venv, Juno's recording and
cargo's work are made once. `--build` makes `stage_build` write `build.json`, `{"build": "<short sha>"}`, into
the stage, shipped at the bundle's top, and a build without it removes any an earlier one left, so a release
never carries one. `app_identity.build` reads it in a frozen app alone, `server.BUILD`, empty from source and
in a release. `/api/server` answers `version` and `build`, Home's answers carry `build`, About says "Version
0.9.23, build e45b1af" (`shell.about.version_build`) where there is one, and a note from Send feedback carries
`0.9.23 build e45b1af` as its version, inside the collector's 40 characters. The checks: the app's executable
and its server `lipo -archs` arm64 alone, the bundle's version versions.json's, the build it carries the
commit's, `codesign --verify --deep --strict`, the server's `cli --help`, and the server inside the app started
with `--serve --no-browser` on a free port in a home folder of its own, `/api/server` answering as Idiograph
with the version and the build, then quit. Without `--dry-run` the checked app is copied to
`.verify/macdaily/ready-<sha>` and the script hands it to `~/.claude/bin/idiograph-swap-watch`, as
idiograph-release hands a release, the old copy kept in `.verify/app-before-daily-<date>` (`-2` and on for a
second that day, `backup_dir`, since the watch moves the old app into that folder). A copy of the same commit
already in /Applications is left as it is unless `--force`, `DAILY: SAME <sha>`. The lines to read are
`DAILY: BUILT`, `DAILY: FAILED` and the watch's `SWAP: DONE`. The version stays main's, the week's release's
number, and update.rs needs nothing: Tauri's updater offers a release only when its version is greater than the
running one, so a daily copy of 0.9.24 made before 0.9.24's release is never offered 0.9.23 and is not offered
0.9.24 once it is out, the next day's copy replacing it. A version with `+<sha>` would break that, since the
semver crate orders build metadata, so the commit is kept out of the version. Area 361. Since typst1 the
checks also ask for the typesetter beside the server, arm64 alone, typesetting a one-line page with the fonts
the app carries.

**The typesetter** (typst1, 9 November 2026, Adam, 9 November about 18:10: Typst for every PDF and picture, no
fallback). Typst is the one engine for Export as PDF, Save as an image and the agents' exports, on the Mac,
Windows and Linux, through `family/typeset.py`: `typeset.render(template, data, fmt="pdf", ppi=144.0)` answers
the PDF's bytes, or with `fmt="png"` a list of each page's PNG at `ppi`. `template` is a view's main `.typ`
file, its folder the root Typst reads files under, and `data` reaches it as the string input `data` holding the
JSON text (`#let d = json(bytes(sys.inputs.data))`). A failure raises `typeset.Failed`, whose words are the
catalogue's (`typeset.failed`, `typeset.slow`, `typeset.missing`, in `family/static/i18n/en/typeset.json`), and
what the engine said goes to the server's log as `typeset:` lines on its standard error. Each way the app runs
has one engine and never tries a second. From source (the suite, `./idiograph`, GitHub's tests) it is typst-py,
the Python package, 0.15.2, in the venv and installed by CI's test jobs. The frozen app runs its typesetter,
`idiograph-typeset` (`.exe` on Windows), found from `sys.executable` beside the frozen server, so the window's
server and the command line inside the app both find it and `main.rs` needs nothing. The data goes on its
standard input and nothing is written to disk. The PDF comes back on its standard output, PNGs one after
another, each its length as eight bytes big end first then its bytes (`split_pages`). It has `LIMIT`, 60
seconds, before it is ended (`typeset.slow`). On a failure it exits non-zero with Typst's own diagnostics on its
standard error, one a line with the file, line and column. On Windows it runs with no console window.

Both engines are given the fonts folder alone, `static/fonts/` (`family/static/fonts/` from source), and no
system font and none of Typst's own: typst-py through `typst.Fonts(include_system_fonts=False,
include_embedded_fonts=False)`, the typesetter because it reads no other. A page asking for a font the folder
lacks is set in one of the folder's, so a page looks the same on every computer and from either engine. The
folder holds Charis SIL (text) and Nunito Sans (headings, labels), each cut to Latin, their OFL texts beside
them, and `fonts.css`, one `@font-face` a file at `/fonts/...`, for the print views on screen.

The typesetter's source is `packaging/tauri/typeset/`, a crate of its own with Tauri's release settings
(`codegen-units = 1`, `lto`, `opt-level = "s"`, `strip`), its `typst`, `typst-pdf`, `typst-layout` and
`typst-render` crates pinned with `=` to 0.15.1, the Typst typst-py 0.15.2 carries (`typeset.TYPST`), and its
`Cargo.lock` committed. `packaging/typeset_helper.py` is the builds' one place for it: `build` runs `cargo build
--release --locked` into the build folder's `typeset-target`, `place` copies it into the frozen folder, `check`
typesets a one-line page with the fonts that folder carries and stops the build if no PDF comes back.
`build_mac.py` signs it as PyInstaller signs the server (Developer ID with the hardened runtime, else ad hoc),
`build_windows.py` signs it with signtool beside the two executables when signing, and `build_linux.py`
builds it on the machine it runs on and `check_deb` asks for it, runnable, in `usr/lib/<Name>/server`. Each
system's bundle then carries it with the frozen folder: `Contents/Resources/server/` on a Mac, `server\` in the
Windows install folder, `<prefix>/lib/<Name>/server/` in the .deb and the AppImage. No frozen server takes
typst-py (`build_mac.EXCLUDES`). On an Apple Silicon Mac it is 25.8 MB, 11.2 MB compressed as the disk image
compresses (zlib) and 8.0 MB as the Windows and Linux installers do (LZMA). Its size on Windows and Linux, built on
GitHub's machines, is not yet measured.

**Moving Typst's version on purpose.** Both carriers move together, never one alone. Find the Typst version the
new typst-py carries (its wheel's `_typst` library names its crates, `typst-library-0.x.y`), put it in the
typesetter's `Cargo.toml` with `=` and run `cargo update -p typst` there so `Cargo.lock` follows, set `TYPST` and
`TYPST_PY` in `typeset.py`, the `typst==` pin in the workflow's three test jobs and the venv, and run area 362
and every template's area: Typst before 1.0 changes its Rust interface between minor versions (0.14 to 0.15 did),
so `main.rs` may need a change too. Area 362.

**Each app built and released on its own** (20 October, the three-app split's build 6). `build_mac.py
--app sift` and `build_windows.py --app sift` build Sift in place of Idiograph, and Trace likewise. The
server is frozen under the app's own name, `Sift` on a Mac and `Sift.exe` with `Sift-console.exe` on
Windows, the name by which it knows which app it is (`app_identity.from_executable`).
`bundle.overrides(..., app=)` lays the app's name, bundle id, version from `versions.json`, icons,
installer icon, update address and What's new over `tauri.conf.json`, which stays Idiograph's, so
Idiograph's build is as it was. The window knows its app the same way, by its own executable's name
(`src-tauri/src/app.rs`): it runs that server on that app's port, keeps its log in that app's logs
folder, and says that app's name in its titles, menus and notices. `Sift-Setup.exe` installs Sift for
the user in its own folder under LocalAppData, beside Idiograph, its own entry in Settings, Apps. Each
Setup stops the server its folder holds, and only Idiograph's removes the Inno Setup install of 0.9.0.
Sift's icons are under `src-tauri/icons/sift`, Trace's under `src-tauri/icons/trace`, and the page's
`static/favicon-sift.svg` and `favicon-trace.svg` beside them, all drawn by
`packaging/tauri/make_icons.py` from make_app's `draw_icon(size, app)`, the family's paper tile, the mark
in ink and one point in the crux orange: Sift's sieve with a record falling through it, Trace's page
corner with a citation beside its bracket. The server's `/favicon.png` is the running app's. A tag names
its app, `sift-v1.0.0` and `trace-v1.0.0`, a bare `v` (or `idiograph-v`) Idiograph's, the rule written
once in `release.tag_app`, which the workflow reads through `release.py --which` and builds that app
alone. `release.py sift-v1.0.0` takes `Sift.dmg`, `Sift.app.tar.gz` and `Sift-Setup.exe`, Sift's notes in
`docs/whats-new-sift.md`, Sift's version and its own releases repository, `Pharkie/sift-releases`, and one
update key signs all three apps. Its dry run says what it would publish, where and under which tag.

`packaging/make_update_key.sh` makes the key pair once, on the Mac that releases: `tauri signer
generate` under a password of 40 letters and digits made at random, the key and its password put in the
login Keychain through `security -i` on standard input, never on its command line, and the folder the
CLI wrote them in, private to the user, removed however the script ends. The CLI is given no password on
its command line and asks for one on its terminal, twice, as minisign asks, and `packaging/key_prompt.py`
runs it on a pseudo-terminal of its own and types the password from the private file at each prompt, so
the password never stands in a command line or an environment, which a process list shows, where the
third build handed it over with `-p` for the second the CLI ran (18 October, the fourth build). CI is
taken out of the CLI's environment, since with it set the CLI asks nothing and makes a key with no
password, and `key_prompt.py --opens` then checks through `minisign.py` that the key is sealed under that
password and opens to its own public half before anything is kept. It prints the public key alone,
for `"pubkey"` in `tauri.conf.json`, which held a placeholder no signature could match until the fifth build, so
every update is refused, and asks for both secrets to go into 1Password from Keychain Access, since
without them no update can be signed again and every tester would reinstall by hand. It refuses to run
when the Keychain holds either already. Its checks run with `IDIOGRAPH_KEYCHAIN_STUB`, a folder standing
in for the Keychain, and a stand-in for the CLI, and the release's with `--test-key`, a throwaway pair in
a check's folder, and `--from`, the files from a folder (area 173). Tauri's own CLI made a signature with
a throwaway key on 17 October that the suite holds, so Python's checking is held to Tauri's own.

On GitHub, `.github/workflows/tauri.yml` had three jobs on a push to `spike/tauri`, until it was dropped on
21 October with its drive scripts kept in `packaging/tauri` for a later workflow. `windows` drove the
test app through WebView2's debugging port, now with `drive_windows_three.py`, which reads from the
windows themselves what the second build's screenshots found, the page's height against the client area
below the menu bar among them. `installer` puts the real installer over the Inno Setup install of 0.9.0
from the run of 15 October, 38701841756, takes its pages and the installed app's first window from the
screen with a heading baked in, then uninstalls it with every setting and case kept
(`drive_installer.py`). `mac`, on a push whose message holds [mac] alone, builds the real Mac app for the
machine's architecture, takes the disk image's window and the installed app's first window from the
screen, headed by `heading.js`, and runs `Idiograph mcp` and `cli` from the bundle
(`drive_installed_mac.py`).

What the second build's screenshots found is mended. A window made from a command or a menu's item on
the main thread opened blank and with no menu bar on Windows, so New Window, Open Recent and the manual
make theirs off it (`aside`, and `new_window` async). On Windows every window but the first gets a menu
bar of its own (`menu::for_window`), let go as it closes, since the one bar every window shared stood in
the first window alone, so the print views, the manual and a second window had none, and every window
its size again below the bar (`fitted`), since the bar took its height from the page, and the check had
laid 1280 by 800 over a page of 1280 by 780, which cut every shot's foot. Windows's Zoom In and Zoom Out
show Ctrl+Plus and Ctrl+Minus in their words, where the numeric pad's plus showed nothing. About on a
Mac says the version once, and on Windows the year too, its copyright now the window's own constant,
`menu::COPYRIGHT`, which it read at run time as nothing there. Open Recent tells two projects of one name
apart, the demo by its tag's word and any other by its folder's. Spelling and Grammar stands after
Select All. Every scrollbar's thumb is `--scroll-thumb`, 3 to 1 or more. The statements screen's window
takes the case's name, as PETs does. Settings says Exit Idiograph in the window on Windows, the server's
word in `/api/server`. Choose's dialog on Windows has a title with no full stop. The server's queue of
connections waiting to be taken is 128 long (`AppServer`), where the standard library's five let Windows
refuse outright the burst two windows make reloading at once after a Restart, so the third build's third
and fourth Windows runs found a page come back with neither its script nor its marks. It binds without the
standard library's lookup of the computer's own name (`socket.getfqdn`), which nothing reads: where a
reverse lookup of 127.0.0.1 goes unanswered, it held the start for half a minute before the server took a
connection, as for every real server the suite started on GitHub's Mac (7 November 2026).

**The updater and What's new (Tauri, 18 October, the fourth build).** Updates come through Tauri's own
updater plugin, 2.13.1, and no other way (Adam, 17 October), in `packaging/tauri/src-tauri/src/update.rs`.
The plugin reads `latest.json` from `tauri.conf.json`'s endpoint, the releases repository's
`releases/latest/download/latest.json`, and checks each file it downloads against `"pubkey"` there, the
version the file was signed for among it, since `requireSignedVersion` is on, before the window keeps it.
A download whose signature does not hold against Adam's public key, there since the fifth build, is
refused with Idiograph could not confirm the update is genuine, so it was not installed. What he chose is kept in `window.json` under `updates` (`keep.rs`):
`check`, missing until the page has asked, `download`, the last check's time `checked`, `ran`, the
version that last ran, and `seen`. With checking on the window checks four seconds after each start and
again once a day while it runs, and the page's Check now checks whatever the ticks say. A newer version
found is downloaded by itself when Download updates without asking is ticked, and else when he presses
Download. A downloaded file is kept in memory, never on disk, and only once its signature holds. Restart
now installs it and starts the new version: on Windows the plugin runs the installer with its progress
bar alone (`installMode` passive) after the window has stopped the server by Quit's path
(`on_before_exit`), and the installer starts the new version with the same command line. On a Mac the app
quits as Quit quits it, the update is put in place as it quits, over the app where it is, and it starts
again, the new version, or the old one still there should the update not go in. An update downloaded and
not installed, after Later or with nothing pressed, is put in place as the app quits (`at_quit`), on
Windows with the installer's progress bar and nothing started after it. The page asks through the
command `updates` and hears every change as the event `idiograph-update` (`window.js`), and a browser's
tab, with no bridge, shows nothing of it. A failure says in plain words that GitHub could not be reached,
that its answer could not be read, that the update could not be downloaded, that its signature did not
match, or that Idiograph could not put the update in place.

What's new: `docs/whats-new.md` goes in every bundle beside the manual (`tauri.conf.json`'s
`resources`, `bundle.py`), and the server answers it as `/api/whats-new`. The first run of a version
newer than `ran` tells the page `updated`, which shows once at the foot, "Updated to Idiograph 0.9.2."
with What's new and Close, and the window is told `seen` as it shows. While it shows `wnFootRoom` keeps
its height on the body as `--foot-h`, measured again on `resize`, two rows on a phone, and `body.foot-on
.lib-body` takes `max(72px, calc(26px + var(--foot-h) + var(--find-room) + 24px))` at its foot, the
line's place, its height and 24 pixels, so the home screen's last line scrolls clear above it (18 October, where at 360 Add
transcripts stayed partly under it), and a toast stands 8 pixels over `--foot-h`, where it took the line
as one row of 44 with 52. What's new opens the sheet, reached again from Settings, General, the version with
What's new under Updates, and from Help, What's New in Idiograph on a Mac and What's New on Windows
(`menu.rs`, the page's `openWhatsNew`).

Every version since the one before (wnspan, 29 October 2026, Adam's yes to Sparkle's way on a Mac, after an
update from 0.9.10 straight to 0.9.13 had shown 0.9.13's lines alone). `begin` keeps `ran` as `before` beside
`updated` in update.rs's `Now`, both in the view until `seen` lets them go, and `wnFoot` keeps `before` in `WN`
as the line shows, so the line's What's new opens `openWhatsNew({ since })`. `wnSpan(versions, running,
before)` sorts the file's versions as numbers (`wnNumbers` and `wnCompare`, update.rs's `numbers` in the
page) and gives `shown`, every version after `before` up to `running`, newest first, or `running` alone when
there is no `before` or it is not older, the file's newest when no version is known, and `earlier`, every
version older than those. The file holds whatever versions were released, so 0.9.10 to 0.9.13 is 0.9.13 and
0.9.12 with no 0.9.11. The first shown fills `#whatsnew-title`, `#whatsnew-date` and `#whatsnew-notes`, which
the update drivers read, and each after it a section of its own in `#whatsnew-rest` (`wnSection`), a rule
above it. `#whatsnew-earlier`, Earlier versions, stands under the last while `earlier` holds any, and
`wnEarlier` adds them below, hides itself and moves the focus to the first heading added without scrolling.
The card is a column and `#whatsnew-body` scrolls between the kicker and Done, so Done stays in reach at 1280
by 800 and 720 wide. Settings' What's new passes `incoming`: while an update is available, downloading or
ready, newer than the running version, `wnIncoming` puts its own notes first, the manifest's `notes` a line
each, under its version and the manifest's `pub_date`, the view's `date` (update.rs takes it from the update's
`raw_json`), where until then it showed the running version's file alone. The Help menu, which calls
`openWhatsNew()`, shows the running version first. `/api/whats-new` is as it was, every version of the app's
own file, so Sift and Trace show theirs (area 291).

A release is proved end to end on this machine without the real key: `packaging/tauri/update_proof.py`
makes a throwaway key, a check's own notes and a test release, the newer version's files signed by
`release.py --dry-run --test-key --whats-new` with its manifest's addresses pointing at a server on
127.0.0.1 alone, and a tampered copy of each file. The test app takes the key's public half and the
manifest's address through `build_mac.py` or `build_windows.py` with `--test-app --update-key
--update-url`, and `--version` and `--whats-new` for the newer one (`bundle.test_update`), which a build
without `--test-app` refuses, so no build that ships can point anywhere but the releases repository or
take plain http. `drive_update_mac.py` drives it on a Mac and `drive_update_windows.py` on GitHub's
Windows machine, the workflow's `update` job: asked once, Check, Download, the ready line, Settings'
rows, Relaunch now, the new version with What's new, a tampered file refused, and Later's update
installed as the app quits.

What the third build's screenshots found is mended (18 October). The Windows installer and uninstaller
carry Idiograph's icon (`installerIcon`, `uninstallerIcon`) and its mark on the Welcome and Finish pages
(`sidebarImage`, `src-tauri/windows/sidebar.bmp`, drawn with the disk image's background by
`packaging/tauri/draw_pictures.py` from make_app's drawing), where NSIS's stock icon and blue picture
stood. The Welcome page says Setup installs Idiograph for you alone with no administrator's password and no restart,
and that an open Idiograph is closed first and your cases and settings stay, where NSIS's own text spoke
of system files and rebooting (`MUI_WELCOMEPAGE_TEXT` in `hooks.nsh`). The uninstaller's first page says
your cases, transcripts and projects stay whether or not the box is ticked (`MUI_UNCONFIRMPAGE_TEXT_TOP`),
and its tick says what it clears, Also clear the window's size, zoom, appearance and folded sections, in
`src-tauri/windows/English.nsh`, Tauri's English words laid over its own (`customLanguageFiles`), where
Delete the application data read as deleting his cases, and the three about an open Idiograph no longer
speak of killing it. Every window stands whole on its screen (`on_screen` and `fit_in` in `main.rs`): one
larger than the work area, the part the taskbar, the Dock and the menu bar leave, is made to fit it, and
one past its edge is moved inside, and a new window steps 28 pixels down and right for each window of
the app's own page already open, five at most, where it stepped by every window ever opened, print views
among them, and opened 196 pixels down with its foot under the taskbar. The notice when the server ends
unasked says what happened and what to do, in the fifth build's words Idiograph stopped unexpectedly. What
you saved is kept. Close this window and open Idiograph again., where it showed the log's last lines, a port, 127.0.0.1 and "Stop it with
Control-C" among them, and each page covers itself first with the same words (`serverGone`), where
"Failed to fetch" stood at its foot. The Mac's disk image is made by dmgbuild (`bundle.disk_image`,
pinned in `build_mac.py`'s `DMG_PINS`), its window 660 by 400 with no toolbar, sidebar or path bar,
Idiograph at the left, Applications at the right and an arrow between them in its background, laid out
in the image itself, so no Finder window is driven on the screen as Tauri's script would drive one. The
Windows checks set the world the page's steps need before Sift's picture, since a reload had taken it and
the picture showed a PETs board, and hear a drop without taking it (`DROP_ARM`), since the check's own
listener had taken the drop and the New project card stood empty (`drive_windows_four.py`, with a second
window on a screen of 1366 by 768).

**Adam's words, the crash notice once and the key (Tauri, 18 October, the fifth build).** Every string
of the updater is Adam's, from his choice of the screenshot check's suggestions. The fifth build said
Restart now where the fourth said Relaunch now, and the sixth put Relaunch back (see below). The second
tick says Download updates without asking. The
privacy line, in Settings, the question asked once, the README and the manual alike, says "Once a day
Idiograph asks GitHub for a newer version. GitHub sees your internet address and version number, never
your work." A file whose signature does not hold says "Idiograph could not confirm the update is
genuine, so it was not installed." (`update::SIGNATURE`). The page's internal names stay, `updRelaunch`, the command's op
`relaunch` and `#update-relaunch`, which only the code reads. The foot line puts a no-break space between
Idiograph and its number, so at 360 "Idiograph 0.9.2." never breaks. The crash notice says "Idiograph
stopped unexpectedly." and "What you saved is kept. Close this window and open Idiograph again." and shows
once, where the fourth build showed it twice, the page's and the system's over it: each page covers
itself (`ended_js`, through the page's `serverGone`) and says back through the command `closing`, step
`ended`, that it has (`ENDED_SHOWN`), and the window, having waited `ENDED_WAIT`, three seconds, for
that word, leaves the app to end as its windows close. Only when no page has said it, as when no window
holds the app's page, does the system's own notice say it and the app end after it. A start that fails
says "Idiograph could not start. What you saved is kept. Open Idiograph again." (`not_started`), where
its dialog showed the log's last lines, which now go to the window's own output alone, whether the server
did not run, did not answer or the window did not open. The other failures keep the launchers' words.
The installer's every one of Tauri's stock lines in `English.nsh` is said plainly, with no exclamation
mark, nothing recommended, no operation and short sentences saying what happens: the page that asks what
to do says what is installed, "Choose what to do, then click Next.", over Install it again or Uninstall
Idiograph for the same version and Uninstall it first or Install over it for another, and the WebView2
lines say plainly what they do. The Welcome page says "It needs no administrator's password and no
restart.", the uninstaller's tick "Also clear the window's size, zoom, appearance and folded sections",
and the last page's tick "Open Idiograph" (`MUI_FINISHPAGE_RUN_TEXT` in `hooks.nsh`), where NSIS's own
said Run. `tauri.conf.json`'s `"pubkey"` is Adam's own public key, minisign's 3CEA6A356EFB3E63, which
`make_update_key.sh` made on his Mac and which is public, where a placeholder that refused every update
had stood, so a build that ships checks every update against it, and `release.py` signs only with the
key whose public half it is. A check never uses it: the test app takes a throwaway key through
`--test-app --update-key` as before. `build_mac.py` gives speaking Juno's recording `SPEAK_WAIT`,
fifteen minutes, in a process group of its own, so a `say` that hangs is ended with everything it
started, as the fourth build's hung for twelve minutes after 7 of its 39 clips, and the build carries on
with the recording spoken for this same transcript in `packaging/recording`, the one the Windows build
ships, or without one, said in one line. `run.sh` and `run.bat` install et_xmlfile at 2.0.0 beside
openpyxl, the version the build and GitHub's suite pin, so a copy run from source writes its workbooks as
the suite tests them. GitHub's Windows checks see the crash notice once, the page's alone and the window
closed as it says (`drive_windows_two.py`), a failed start's words (`IDIOGRAPH_ARGS` with a switch the
server does not take), the installer's details unfolded, Setup run again for the same version, and with
`drive_installer.py --older --newer` in the update job an older version's Setup where a newer one is
installed and the other way round, each Setup ended on its page, and the update's available and
downloading lines. The checks are area 180.

**Relaunch again, six installer lines and the shots the check could not use (Tauri, 18 October, the
sixth build).** Installing a downloaded update says Relaunch again, the normal word, which Adam never
asked to change: Relaunch now on the home screen's line and in Settings, the ready line "Idiograph 0.9.2
is ready. Relaunch to use it.", and the page's messages around it, "Relaunching Idiograph.", "Your last
change could not be saved, so Idiograph did not relaunch." and, when the window gives no reason, "Idiograph
did not relaunch. Quit it and open it again." The menu's Restart Idiograph stays, a different act. Six of
`English.nsh`'s lines are the screenshot check's words: `newerVersionInstalled` "A newer version of
Idiograph is installed. This Setup is older. Choose what to do, then click Next.",
`dontUninstallDowngrade` "Install over it (not possible with an older version)", `silentDowngrades`
ending "Double-click this installer to choose what to do.", `installingWebview2` "Installing
Microsoft's WebView2, which Idiograph needs", `webview2DownloadError` "WebView2 did not download ($0).
Check you are online, then run this installer again." and `webview2InstallError` "WebView2 did not
install (code $1). Run this installer again." The Windows checks take what the check could not use:
`drive_failed_start.py` minimises every window, starts the window with a switch its server does not take
and takes the dialog that says so by its own frame alone (`DWMWA_EXTENDED_FRAME_BOUNDS`), for the fifth
run's start in `drive_windows_two.py` and, as the workflow's windows job ends, for the build before the
fifth, installed from the fourth build's last run's own installer (`BEFORE_FIFTH_RUN`), whose dialog
showed the log's last lines. The second window on a screen of 1366 by 768 is taken twice, each of the two
windows brought in front in turn, and the pair put side by side (`drive_windows_four.py`, `FRONT` and
`PAIR`). The installer's details list is widened to its longest line and made taller, its window, page,
bar, buttons and heading moved to suit, then put back before Finish (`whole_details` and
`restore_details` in `drive_installer.py`), and the installer's pages are taken by their frame alone
beside the shots with a heading (`dialog_shot`). The checks are area 184.

**The command line.** `cli.py` is how an AI agent in a conversation, Claude Code, Claude Desktop
or Codex, reads and writes a project, and `docs/agents.md` is the guide it reads. From source it
runs as `idiograph <command>` in the app's folder, a small script running the venv's python, the
one beside it and else the repo root's, with `idiograph.bat` beside it for Windows, and in the Mac app as the frozen server with `cli` first,
`Idiograph.app/Contents/Resources/server/Idiograph cli <command>`, which `mac_launcher.py` hands to `cli.main`
(the window's own `Contents/MacOS/Idiograph cli` hands over to it, so both work)
before it looks at anything else. The commands are `cases`, `statements`, `board list`, `board show`,
`board compare`, `board new`, `board import`, `board apply`, `board current`, `board canvas`, `board rename`, `board duplicate`, `board delete`, `board export`, `board note`, `board history`, `board revision`, `board restore`, `board copy`, `gets show`, `gets apply`, `gets import`, `gets take`, the GETs board menu's and History's `gets` commands and `gets settings`, `turn show`,
`turn write`, `validate` and `search`, and `sift <folder>` with `counts`, `export`, `prisma`, `list`, `show`,
`add` and `propose`, which work on a screening by its folder through `sift.py` and need no project.
The MCP server offers those as `sift_list`, `sift_show`, `sift_counts`, `sift_export`, which only
says the rows, `sift_prisma`, `sift_add` and `sift_propose`, and none decides, notes or undoes a
record. `list` and `show`, and their tools, give his own fields to read, and none writes them. `sift search` with `plan`, `strings`, `register`, `run` and `runs` works on a review folder's
searches through `sift_search.py`, and the MCP server offers `sift_search_plan`,
`sift_search_strings`, `sift_search_runs` and `sift_search_run`, the newest registered version alone,
and none registers or edits a plan, a draft that carries his decision on terms or strings being written
through Sift's own save, the route's `save` (Adam, 14 October). `sift search databases` and `sift_search_databases` give his list
of databases from the settings, `--config` naming another file, and whether each key is saved, and
none saves, removes or shows a key. `trace <folder>`, with a manuscript's name or none, reads a
Trace project through `cmd_trace` in `apps/trace/trace_cli.py` and `trace_claims.py`, and the MCP server offers it as
`trace_claims`, and none judges a claim, writes a note or asks for passages (15 October). `sift <review
folder> refs` and `sift_refs` of 14 October are gone with Check references. `search <words>`, and the MCP
tool `search`, is the app's Search for an agent (20 October, `cli.cmd_search`): `app_search.distil_found`,
`sift_found` or `trace_found` finds, `app_search.answer` orders and cuts, as `/api/search` does, so its hits are
the app's, with no second search engine. Over every project the command reads, each hit naming its project when
there are several, or `--case` one case, `--board` with it one board's PETs and notes, its themes hits kept to
that board, or `--folder` a screening, a review's plan or a Trace project, as `sift` and `trace` take a folder,
needing no tick. Words in quotation marks are a phrase, `app_search.phrase_in` keeping the hits that hold it.
Each word typed carries its other forms (20 October, `app_search.term`): `lemmas` takes a form back to its plain
form by a few English rules, -s, -es, -ies, -ing and -ed, a doubled consonant undone, a final e put back, and the
irregular words in `IRREGULAR`, and `inflected` makes each plain form's others, so "sleep" finds "slept" and
"walked" "walking". The word typed is found anywhere in a text as before, each other form only as a whole word
(`Term.rx`), so "man" finding "men" never finds "moment". `app_search.query` reads a phrase in quotation marks
with no other form, for the app's Search and the agents' alike, and the answer's `forms` lets `searchMarked`
in search.js wash them too.
Two modifiers (searchmods, 6 November 2026), the Search card's Whole word and Match case, in the
engine and so for the card, the command line and MCP alike. Whole word is on at first (Adam, 6 November 2026, "Whole
word on", as in Find and replace) and Match case off until set. The engine reads what it is passed, off unless `whole`
or `case` is, and the default is where a request is read: the card's `#search-word` is `checked` in page.html, and
`options(body)` gives `whole_word` on unless the request says `false`, and `match_case` on only when it is `true`,
the same in `api_search`, each app's scope handler and MCP's `arguments`, while the command line's `--whole-word` is a
`BooleanOptionalAction` defaulting on (the style of `transcript replace --word`), so `--no-whole-word` is the way to a
part-word search, and `cli.search_modifiers` reads it. `app_search.query(q, whole, case)` reads them into the words
it makes: `words_of` gives a `Words` list carrying `whole` and `case`, each `Term` its own flags and pattern, a `Phrase`
the same for a quoted phrase. `Term.rx` under Whole word holds the word and its forms each through `edged`, a lookbehind and a
lookahead for no letter or digit (`[^\W_]`) beside an end that is one itself, Find and replace's `findSpans` rule, so
"so" is never found in "also" and is found in "so," and "so's". `found_in` and `spans_of` then use that pattern alone,
and `phrase_in` a phrase's `edged` pattern. Under Match case the folding is `plain`, accents off and the case kept,
and the word's other forms are made from its lower-case spelling and given the word's case again (`recase`): lower
case for a word in lower case, a capital first letter for "Sleep", capitals for "SLEEP", and none for a word of mixed
case such as "McKee" or a single capital. An item holds the folded text it was made with, so `hit(it, words)` asks the
`Words.loose` copy of the words, read without Match case, of that first and only then takes the accents off the text as
written (`searched(it)`, the item's `s` where its `f` was made of more than its text, a record's ID with its title in
sift_find.py), and `holds(text, words)` does the same for a name or the research question. `marked` and `snippet` fold
by the words' own rule. The answer carries `whole_word` and `match_case`, which `search_said` repeats in the command
line's JSON. The route reads the two booleans in each app's scope handler (`api_search`, `idiograph_routes.search_scope`,
`sift_routes.search_scope`, `trace_routes.search_scope`), the command line takes `--whole-word` (on, `--no-whole-word` off) and `--match-case`
(`--case` stays a participant, `cli.search_modifiers`) and MCP's `search` the true or false `whole_word` and `match_case`,
Sift's and Trace's tools too. On the page the two ticks are `#search-word` and `#search-case` in the card's head, in
`.search-mods`, labels with the box inside as Find and replace's are, sent by `searchOptions()` in each request and
changing a search at once. They are never rebuilt, so they keep between openings and screens as Find and replace's
`#find-word` and `#find-case` do, until the page is loaded again, and are saved nowhere. `searchMarked(text, q, forms,
opts)` takes the answer's two flags and marks by the same rules, `fits` ruling out a place of a word with a letter or a
digit beside an end that is one. Their words, "Whole word" and "Match case", are the family's `page.search.whole_word`
and `page.search.match_case`, the same as Idiograph's own for Find and replace. Area 329.
`--kinds` takes the card's kinds or the agent's groups, `app_search.KIND_GROUPS`, the counts by kind every kind's.
Each hit carries its snippet with every word between two asterisks (`app_search.marked`, each character folded on
its own so a place found maps back), its sheet, row, time and speaker, a statement's short id, key and `placed`,
where the Current board or the board named places it, with its label's export label (`SearchCase`), a PET's board
and label, and `open`, the tool, its inputs and the command line that read it whole. A page holds `--limit` hits,
25 by default and 200 at most, and `more` is the offset of the next, passed back as `--more`. It only reads. `board export --word` and `--pdf` are the exports it makes, the PETs screen's Word
document through `themes_word.write` and the table of PETs' PDF through `print_pdf.write` (Typst since typst5), with `--dry-run` and no `--note`, since they change nothing he
made, and never over a file, a PDF over its own name only with `--replace`. The PDF goes beside the workbook
as on 19 October, or where `--out` names (20 October, `print_pdf.where_to`), a folder or a file ending .pdf,
`--board-note` the print view's Board note. `gets export`, MCP's
`gets_export`, is the GETs screen's print card as a PDF, `print_pdf.write_gets` typesetting `gets_print.typst_data` with
`--what` table, trail or all, `--selected`, `--notes`, `--for-sending` and `--get`, at the project's root beside
the GETs file unless `--out` names a place, with `--replace` and `--dry-run`, reading only. On a case with no themes file `board new` writes its board as Board 1, as its dry run says, with no
empty board before it, `seed` false to `propose`. `board new` reads `subs` on a PET and `groups` on a sub-theme or a group,
at any depth, `cli.build_board`, and `cli.lay_board` lays them out through `themes_ai.lay_out`, which
nests a group's blob inside its sub-theme's. `board current` marks a board the Current board through
`themes.version_op`'s `choose`, the board kept first in its History as "Marked the Current board: "
and his request, `cli.cmd_board_current`. `board canvas`, `board rename`, `board duplicate` and `board delete` are the board menu's acts through `version_op`'s `switch`, `rename`, `duplicate` and `delete` (19 October): a rename keeps the board first in its History as "Renamed from " and its old name, a duplicate takes `note` in its body for the words naming the tool and the request, which the board menu leaves empty, and a delete writes the board whole, its History with it, as JSON into the case's `_Archive/` before it goes. `board apply` takes `order` beside the applier's operations, run after them in `cli.cmd_board_apply` on the landed board through `themes.reorder`: the canvas, the PETs table and the exports read order from positions (`order_of`, `theme_order`, `canvas_order`), so an order moves things, each item to the place the one before it in that place read from, a label with its whole subtree, rows kept by `read_rows`, those along a row pushed right and the rows below pushed down only on an overlap, a label that grew then making room among its neighbours up to the PETs, and loose cards and free notes a PET covers moved to a free spot. Each label is stored where the page draws it first and after (`sync_labels`), as the page stores it on every layout. A `note` operation with an empty note takes the note off, in `themes_ai.revise_ops`. `board new` never reads or names `themes.cap`, the most PETs an AI board proposes, which only the AI's proposals take (`themes_ai.parse_grouping`, its prompt), and `cases` carries it only in its JSON as `ai_board_most_pets` (was `pet_cap`), read through `server.config()` from `CONFIG_PATH`: `config.json` beside `server.py` from source, the data folder's (`~/Library/Application Support/Idiograph`) in the Mac app's executable, `--config` over either (capfix, 20 October). `board new` drops a pick whose statement is not under its label and says it in one line, and `board show --json` gives each label `export_label` from `themes.pet_numbers`. Since 19 October (agentapi2) a change of what holds what lands first through `themes.land_kept` with `strict`, the canvas's landing: what stays in its label keeps its place, a label moves whole (`_block`, `_shift`), one lifted stands where it stood, one nested goes under its new label's body, then level by level from the deepest what moved goes to `free_offset`'s nearest spot and the neighbours of a label that grew are pushed aside by the least distance, in turn. A change that puts a statement into a label elsewhere, or a new label over more than one label's things, answers None there and lands by `themes.land` as before. `gets apply` runs `order` the same way through `cli.run_orders`, with `gets.card_height`, and `gets show` reads canvas order (`theme_order`, `canvas_order`). `board new` keeps a board's layout through `cli.carry_layout`: `cli.match_labels` pairs each new label with the source's by title, then by half or more of the same statements, the source followed and merged with the workbook, its bin held in a label of its own for the landing, `land_kept` without `strict`, then `themes.reorder` sets each label's statements and labels in the order given in the places each kind reads in, and the PETs, `--layout fresh` keeping `lay_board`. `board new` takes a pick of any quote of a passage with a statement under its label. Since 19 October (stacks) `board apply` takes `stack`, `unstack` and `top` too, run in
`cli.run_stacks` after the applier's operations and before an order, through `themes.stack_onto`,
`themes.take_out` and `themes.make_top`, each refused with its number on a statement that is not on the
board, a stack under a statement stacked under another or in the bin, or one taken out of no stack.
`themes_ai.revise_start` leaves a stacked statement out of `items`, so the applier never moves one, and
`cli.reasons_after` drops the Not placed reason of one stacked. `board new` takes `stacked`, read by
`cli.as_stacks`, the stacked statements left out of `lay_out`'s pile as the bin's are, and `board show`
gives each top `stacked` from `themes.outline`. A board `board new` makes keeping another's layout
takes that board's stacks through `cli.carried_stacks`, for the statements its structure names nowhere,
`themes.copy_into` brings each copied top's stack, and `themes.below`, with the page's `thBelowStack`,
puts a statement taken out just below its stack, moved down past what stands there. `gets take` is `gets.take` under the root lock, each GETs board then marked changed by the agent. `turn write` carries a passage's lines to every board through `themes.passage_written` (rekey, 20 October, where before `themes.statements_written` carried rewording by place alone, so a removal before a passage's last line left every later card on its old key, reworded with its neighbour's words, and the removed one stale). `themes.passage_lines` maps each old line to its new place or None: by the keys the pairs send (`cli.pair_keys`, the keys `turn show` gives through `cli.keyed_pairs`), else the same words, nearest first, then by place when as many lines are left on both sides, else by difflib's ratio in order, at least `SIMILAR`. `cli.quote_lines` maps the quotes the same way, a lone quote by its words. `themes.passage_moved` reads each board as it reads now (`as_read`), takes the removed lines' cards off through `drop_cards` (a removed top's stack kept whole under its next statement by `make_top`, its key gone from labels, the bin, stacks, Not the same and reasons), renames the rest through `keys_renamed`, gives a reworded line's card its new words when it held the old, and follows the board into the workbook after the write. Every revision in a board's History is moved the same way, then the board as it stood is kept as a revision named by `themes_ai.revision_name`, and the board takes `updated` and `changed` with its hash, so `save`'s `outside_since` refuses a page that saw the old keys. The dry run reads `then` through `with_row`. `board apply` takes `remove` (cards by key) and `remove_missing` (every card on the board with no line), `cli.run_removes`, through `drop_cards` before the other operations, refusing a key whose statement is live. `gets.take` follows a case's statement cards by their words through `gets.lines_followed`, the rule of `follow`. Since 22 October (getsdesc) it also makes room under a card that comes in taller: `gets.make_room_below` weighs each card's height before and after by `gets.card_height` over `gets.named`, its title and description, and hands the grown ones to `themes.push_clear`, which moves each neighbour below a grown card in the same label, or on the canvas, straight down by the overlap and the margin, then pushes on from it, and from a label whose frame so grew. Nothing moves up or sideways, and the positions are saved with the take, so the app's own take and an agent's alike leave no overlap. The page's `thMakeRoom` leaves two cards in the pile as they lie, so the room had to be made in the take. Area 249. It is built on the server's own functions, imported from `server.py` with the
recent list kept in memory, and re-implements no rule: the cards are `themes.read_cards`'s, a new
board is laid out by `themes_ai.lay_out` and added through `themes.version_op` with `propose`, a
change to a board goes through `themes_ai.revise_ops`, the board's applier, and lands by
`themes.land`, and a turn is written through
`workbook.save_turn` after `workbook.archive_copy`, as a trim's backup is. With no option it reads
every project of the config, `open_projects`, and a case named by its pseudonym is looked for in
each, `project_for`, a pseudonym two projects share refused in one line asking for `--project`.
`cases` and `validate` answer each project under its name, `each_project`, and `gets` asks for
`--project` when there are several. `--project <name>` takes the project of that name, `--root`
a run of that one folder and `--demo` the demo. A project answers only with `agents` ticked in its
file, the demo always, and one with it unticked is never opened. A statement's short id, `S1` on in the order
`read_cards` reads, is `themes.short_ids`, worked out on every read, and `/api/themes` sends the
same as `sids` for the Inspector. Every write validates first, takes `--dry-run`, `--note`, his
request, and `--tool`, keeps a revision named "Before: " and his request before it changes a board,
marks the board `made` or `changed`, and answers with the change in plain words. Output is plain
text, or JSON with `--json`, and every line goes through the same scrub as the server's paths, so
a case folder's second part never reaches it. `cli.run` runs one command in the calling process,
for the suite, and `cli.perform` one on its parsed arguments, which `main` and the MCP server share.
Standard library and openpyxl only. The command line and the MCP server never read `ai_suggest`, so
they work whatever AI features says.

The boards' remaining routes as ops (parity3, 26 October, the parity check's third group): `board note` is `version_op`'s `note`, the board kept first in its History as `cli.NOTED` and the request, as `board rename` keeps it. `board history`, `board revision`, `board restore` and `board copy` are `themes.board_op`'s `view`, `revision`, `restore` and `copy`, `history` reading `themes.history_list` and drawing a revision through `shown_board`, the others writing under the case's lock and then `cli.stamp_pets` putting the tool and the request on the revision the op kept and, for a restore or a copy, `changed` with its hash on the board written. `board export --draft` is `routes.api_themes_export` itself, through `cli.board_draft`. The GETs board menu is `gets.version_op` under the root lock through `cli.gets_op` (`gets fresh`, `duplicate`, its note set after by `note`, `rename`, `note`, `canvas`, `current`, `delete`, the board copied first to the `_Archive/` beside the GETs file, and `complete`), rename, note and current keeping the board first through `cli.gets_revision_first`. `gets history`, `revision`, `restore` and `subs` are `gets.board_op`'s, `subs` landing each card the op answers at its `x` and `y`, as the page lands them, `gets settings` `gets.settings_view` and `gets.settings_op`. Each dry run is the function's own `dry_run`, which makes every check and writes nothing: `themes.board_op`, `themes.version_op`, `gets.version_op`, `gets.board_op`, `gets.settings_op` and `api_themes_export` take it, and their routes pass `dry_run` on. Area 267.

`import` (20 October, agentimport) is the import card's Make and the create card's build for an
agent, on their code. `cli.import_path` takes the file by its path from the project's root or in
full and refuses one outside the root, `OUTSIDE`, or anywhere but a case's folder or that folder's
own `Source/`, `NOT_IN_CASE`, and `import_project` picks the project whose root holds a full path,
one with the tick off refused as `PRIVATE`. A transcript file goes through `server.import_read` and
`server.import_make`, which `api_import` now calls too, so its read, its line that holds Make back,
its interviewer under Settings' name and its raw source are the card's. A raw source, `read_sheets`
`raw`, goes to `workbook.create_from_source` into `suggested_output` or `--name` in the case's
folder, under `server.writing`, and a case's workbook is refused. `--columns` takes the card's role
names or keys (`import_roles`) as `convert.choose` reads a list, refused on a file with no columns, and
`--interviewer` must be a speaker, the guess when left out.

Marked up to any degree (20 October, importplus). `convert.time_kind` names the format of one cell's
time, `time_found` a column's, `time_seconds` reads one by the format set or its own, strictly when
one is set, frames below `frame_rate`, and `table_turns` and `read_docx_table` put each time they
cannot read in `bad_times`, which `turns_view` answers with `time_found`, `timing` and each preview
turn's `bad`. `convert.speaker_roles` guesses each speaker's role, the interviewer and the rest
Participants, `roles_said` holds Make back on two interviewers or no participant, and
`case_turns` writes the interviewer under Settings' name and marks every other speaker's turn, which
`_fill` writes as Other speaker in a column of that heading. `workbook.ROLE_TESTS` finds it as `ctx`,
`_annotated_sheet` copies it after Interviewer notes, `read_case` answers `context` a row, and
`rounds.is_stop` passes it, while the page keeps it a stop that `stepTo` steps over. One transcript
is always one case (Adam's ruling). `server.import_plan` takes the roles, the recording and its
offset, `place_audio` copies the recording into `Source/<sheet>/Source/` with `offset.json` beside
it (`audio.write_offset`), and `import_make` takes away what it wrote when it fails. Since 9 November
2026 (ayabuild12) the copy is named by `server.recording_name(case, timepoint, timepoints, source)`,
`<Pseudonym> T<n>.<ext>` in a project of two timepoints or more and `<Pseudonym>.<ext>` in one, the
extension lower case, never the source's own name. `import_plan` puts it in the plan as `audio_name`,
which `plan_view` sends the card and the command line's dry run answers with `audio_writes`.
`qdpx_case` names a REFI-QDA project's recordings the same way. `audio.choose` still finds the copy,
the largest file that is not a track. The page adds
`S.audioOffset` in `cueAudio` and takes it off in `heardAt` for the playhead, the PETs player adds
`TH.audioOffset`, and the GETs trail's `data-at` carries it through `gets_audio`'s `offset`.
`convert.TIME_FORMATS` names each format by an example of it (importplus2), with `fraction` for a
time with a fraction of a second, which `hms` reads and is read by (`_ONE_CLOCK`). New project's
rows draw the same choosers through `speakerChoosersHtml`, `api_new_project`'s read answers
`speaker_roles`, `new_cases` takes each file's `speakers` (or `interviewer` from an older page) and
refuses on `roles_said`, and `case_sheet` writes through `convert.as_new_case`, the interviewer
under Settings' name, participants under the pseudonym, another speaker under Other speaker, marked.
On a phone the preview's table stacks in CSS, each notes and statements cell carrying `data-head`,
and the Time column takes the width of its longest time. `write_source`, `write_sheets` and
`create_from_source` take `made`, which `cli.made_by` fills with the tool, his request and the file,
kept as the workbook's own description, and empty from the cards. The dry run answers `columns`
(heading and role), `speakers`, `interviewer`, `interviewer_guessed`, `interviewer_written_as`, the
first `convert.PREVIEW` passages as they land (`cli.landed`), `left_out`, `brings`, `writes` and
`said`, the line that holds the make back.

**The MCP server.** `mcp_server.py` is the command line's commands as tools of the Model Context
Protocol, for Claude Desktop, Cowork or any other client, run from source as `mcp_server.py --root
<case root>`, with `--project`, `--demo` and `--config` as the command line takes them, and with none
of the three on every project of the config, and in the Mac app as the
app's executable with `mcp` first, which `mac_launcher.py` hands to `mcp_server.main`. It speaks
JSON-RPC 2.0 on standard input and output, a message a line: `initialize`, answered with the
protocol version the client asks for when it is one of `VERSIONS` and the latest of them otherwise,
`ping`, `tools/list` and `tools/call`, `prompts/list` and `prompts/get`, `resources/list`,
`resources/read` and `resources/templates/list` (19 October), every notification taken in silence and any
other method answered with the error for a method not found. A line that is not JSON gets the parse error.
Standard output carries the protocol alone: the server keeps a copy of it for the messages and sends
standard output itself to standard error, so a print in the app's code never lands among them. The
tools are `cases`, `statements`, `board_list`, `board_show`, `board_compare`, `board_new`,
`board_apply`, `board_current`, `board_canvas`, `board_rename`, `board_duplicate`, `board_delete`, `board_export`, `gets_show`, `gets_apply`, `gets_take`, `gets_colour`, `turn_show`, `turn_write`, `import` and `validate`,
`board_export` taking `dry_run` and no `request`. `setup`'s line for Claude Code is
`claude mcp add --scope user idiograph -- ...` since 20 October, since `claude mcp add` alone adds a
server at local scope, tied to the folder it was run in. Each one's input
is checked against its JSON Schema by `cli.conform` and run by `cli.perform` on the arguments the
parser would have made, a structure in place of the file the command line reads, so the privacy
tick, the lock, the revisions and never the bin hold as they do there. A result carries the
command's plain words as text and its JSON as `structuredContent`, a refusal is a result with
`isError` and its own lines, and `made` names the client `initialize` gave, Claude Desktop for
`claude-ai`. Every word goes through the command line's scrub. The read tools are marked
`readOnlyHint`, and the ones that change what is there `destructiveHint`. The `instructions` it
answers `initialize` with are `CORE`, a paragraph on the tools, and the guide's method and
conventions, from `docs/agents.md`. Claude Code keeps only about the first 2,000 characters of a
server's instructions, as the trial of 19 October found, so `CORE` holds within `CORE_LIMIT` what a
stranger's agent must not miss: the privacy line, his decisions, `cases` first, dry runs, never his
boards unasked, never the bin, `add_notes`, the tools as the one way in, and the prompt and the
resources. They never grow longer than the 8,288 characters of 19
October, area 206 holding them to it.

**The project's words marked (26 October, Adam's ruling).** Every JSON answer passes through
`cli.dumps`, `--json`'s and the MCP server's `structuredContent` alike, and `cli.mark` there turns each
string into `{"untrusted_text": "..."}` unless its key is one of `cli.PLAIN`'s: the ids, keys, times,
kinds and counts the app makes, and the names an agent hands back as an input, `case`, `sheet`,
`timepoint`, `export_label`. A key not in `PLAIN` is marked, so a new answer's words are marked without
anyone listing them. An empty string, a number and a yes or no stay as they are. `Server.call` puts the
answer's plain words between `<untrusted_text>` and `</untrusted_text>` (`cli.fenced`) when the answer
holds a marked string (`cli.marked`), a marker inside them turned to `[untrusted_text]` so nothing a
participant said closes the block. `cli.unmark` takes the marking off a structure an agent hands back,
in `read_spec` and on every Idiograph tool's input. `mcp_server.UNTRUSTED_LINE` says it in Idiograph's instructions, after
its core and within the first 2,000 characters, and every Idiograph tool that only reads ends its
description with `UNTRUSTED_NOTE` (`register_own`). The plain text the command line prints for
a person is not marked. The suite's checks read answers through `support.plain` and `support.unfenced`,
and area 274 checks the marking itself.

Sift's and Trace's answers are marked too since 2 November 2026 (Adam, by dialog, knowing the QHR
review runs on Sift): `dumps` marks by the plain keys of its `app` (`cli.plain_of`), Idiograph's
`PLAIN`, and Sift's and Trace's own, `SIFT_PLAIN` in `sift_cli.py` and `TRACE_PLAIN` in `trace_cli.py`,
each given to `cli.register` as `plain` (`cli.APP_PLAIN`), an app that names none keeping only a
refusal's `error` and `lines` plain. Each names only what its app makes or checks, ids, a decision, kinds,
dates, files and folders, so a record's title, abstract, keywords (`more`, a record's other columns in
Sift, never a cursor) and a manuscript's claims and references are marked. `cli.unmark` takes the marking
off every app's tool input. `mcp_server.register`'s `untrusted`, `SIFT_UNTRUSTED` and `TRACE_UNTRUSTED`,
says it in each server's instructions after its core, and each of its reading tools ends with
`UNTRUSTED_NOTE`. Area 318 checks it. The app's screens, the CSV, the log and every file Sift and Trace
write are unchanged.

The one prompt, `start` (`PROMPTS`, `START_TEXT`), is a user
message with the privacy line, his decisions, the project as the `cases` tool answers it, dry runs and
the resources, and his first request when `request` gives one. The resources are `idiograph://guide`,
the guide whole, `idiograph://guide/<section>`, each of its second-level sections by `slug`,
`idiograph://schemas/<file>`, each file of `docs/schemas/`, and `idiograph://project/AGENTS.md`, or
`idiograph://project/<name>/AGENTS.md` with several projects, for each project holding one
(`Server.projects`, which reads the project files alone). The prompt runs `cases` through `call`, so
the tick holds as for a tool: with it off the prompt is the refusal's line. `turn write`'s
`add_notes` (`cli.cmd_turn_write`, 19 October) adds exploratory notes after those the passage holds,
one it holds already passed over, where `notes` takes the place of them all, the two refused together
(`NOTES_OR_ADD`), and `added_lines` says on the dry run and the write how many it adds and keeps. The project's `AGENTS.md`
answers with `cli.PRIVATE` with the tick off, and the guide and the schemas, which hold nothing of a
project, are read either way. A uri it does not hold gets the protocol's error -32002, never a file
beside the one named.

**The config writer.** `/api/mcp`, from Settings, builds the entry with
`mcp_server.desktop_entry`: from source the repo's venv python by its own path, never the
interpreter its link leads to, with `mcp_server.py`, and frozen the bundle's executable with `mcp`,
then `--root` and the project's case root, or `--demo`, and `--config` when the server reads
another settings file. `add_to_desktop` writes it under `mcpServers` as `idiograph` in the file
`desktop_config_path` names, every other key kept and a copy of the old file beside it first, and
refuses a file that is not valid JSON. `IDIOGRAPH_CLAUDE_DESKTOP_CONFIG` points
`desktop_config_path` at another file, which the suite and every smoke run use, so nothing they run
writes the real one.

**Only its own page.** Every request, a GET or a POST, is answered only when its `Host` is the
server's own address and its `Origin`, when it sends one, is the same (`own_origin` in `server.py`),
else 403 with "Only Idiograph's own page can ask this.". A page served from anywhere else cannot
post a plain-text body the server would read as JSON, and a name that only points at this machine
cannot read a case. The command line and the MCP server read the files themselves and never come
through it.

**The window's key** (agentlock, 2 November 2026, Adam's ruling: close it). `own_origin` passes any program
on this machine that names the server's own address, with no Origin or a forged one, so a shell's `curl`
could have approved an agent's held action or turned on Dangerously skip permissions. What governs agents
now asks for a key besides, in the header `X-Idiograph-Key` (`keyed`, compared in constant time), made at
each start and never served by any route to the window's run: `/api/holds` (every op), `/api/mcp`,
`/api/agents-guide`, `/api/settings` with `skip_permissions` in its body and `/api/project` with `agents`
in its body (`WINDOW_ONLY`, Idiograph's through `register(window_only=...)`, each a path with None for
every call or the one body key that makes it so). A call without it is refused, a GET or a POST, 403 with
"Only Idiograph's own window can do this.", before anything is read or written. The rest of those routes,
the settings' other keys and a project's other fields, answer as before. The page's `api` in `shell.js`
sends the key on every call.

How it travels in the window: the shell makes it from the system's random source (`key.rs`, /dev/urandom
on a Mac, BCryptGenRandom on Windows), writes it as one line to the server's standard input, a pipe, and
closes it, with `IDIOGRAPH_WINDOW_KEY=stdin` saying it is there, never the key (`start_server`), and puts it
in the script every window runs before the page's own, `window.__IDIOGRAPH_KEY__` (`window_script`). It is
never an argument, an environment variable, a file or a log line, so `ps` and another program's read of
the app's files find nothing. The server reads it as it starts (`take_window_key`, `key_line`). A Restart
hands it on the same way: on a Mac a pipe put on the process's standard input before `os.execve`
(`key_to_stdin`), on Windows the new process started with its standard input a pipe the key is written to
(`spawn_again`, `windows_launcher.respawn`, each taking `key`). A key that never arrives is said in the
log, and the run goes on as a browser's.

**Running from source in a browser** has no window to hold the key, so the server makes its own and puts
it in the page it serves, `<meta name="idiograph-key">` (`keyed_page`), which `api` reads first. A
program on this machine can read the page and send the key, so there it is a second step, not a lock: a
plain POST is still refused. The window's own page never carries it. A tab open across a Restart in a
browser takes the new key when it reloads.

**The switch's record.** Each time Dangerously skip permissions changes, `api_settings` appends a line to
`config.skip-permissions.jsonl` beside the settings file (`record_switch`): `at`, `on`, and `from`,
`window` or `browser`. Since 3 November 2026 the agent log shows it (below). Area 317 checks all of this.

**The agent log** (agentlog, 3 November 2026, Adam's option B by dialog, on refusaldraw's drawings).
`family/agent_log.py`. Each refusal of an agent goes into `agent-log.json` beside the settings file (`place`, or
the file `IDIOGRAPH_AGENT_LOG` names, which the suite sets to its scratch folder), never in a project. The
command line logs from `cli.main` after its answer (`logged`), every refusal there: a page-only command named
by its words (`page_only`, Idiograph's `PAGE_ONLY`, `hold approve` and `hold decline`, now refused
in one line in place of the parser's error), the parser's own (`parse_refusal`: no such command, or a shape it
does not take), another app's command, and every `Refused` and `WorkbookError` of a command. The MCP server
logs from `tools_call` and `call` (`Server.logged`), on the log's own thread (`agent_log.later`) so the answer
goes first: an unknown tool, a page-only tool name (refused as a result in one line), inputs the schema refuses,
and each tool's refusal. `holds.decline` logs a declined action (`logged_decline`). Since siftlog (3 November
2026, Adam: Sift and Trace too) every app logs, each into its own file beside its own settings, Sift's and Trace's
folders under their own app's settings, never a review's or a project's, and in the suite `IDIOGRAPH_AGENT_LOG`'s
name with the app's added (`suite-agent-log-sift.json`). Sift's and Trace's commands take a folder first, so their
`call` keeps only their own acts as each registers them (`cli.register`'s `words`, `cli.app_lead`): `sift list
--round`, `sift search plan`, never a folder, a record id or a document, and `op` is the act as the MCP tool names it
(`cli.app_op`: `sift plan` for `sift search plan`). The project is the folder an agent named, by its name (`named`:
Sift's review over `runs/`, `sift_cli.log_name`, Trace's `trace_claims.own_name`, `cli.app_project`), never its path.

An entry: `via` (cli, mcp, hold), `agent`, `project` (or `closed`, how many projects agents may not read, from
`agent_log.HERE`, which `idiograph_cli.open_projects` and `run_in_scope` set), `op`, `call` (the command's words
and flag names, or the tool's name and its inputs' names), `code` (a refusal's own of `errors.CODES`, else
`agent_log.KINDS`: `not_allowed`, `no_command`, `page_only`, `declined`, `invalid`, `refused`), `line`, `request`,
`at`, `time` and `count`. Every word of the agent's is cleaned as a hold's are (`agent_log.agent_words`, moved
there from holds.py), the line and the request cut to 300 characters, and every value it handed in (any
argument but the names, `cli.NAMES`) taken out of the line (`scrubbed`). The same refusal within 60 seconds
adds to the entry's `count` (`merged`). Kept: the last 7 days (`DAYS`), an older entry dropped as the log is written or
read, and within them the latest 500, a backstop against a flood. No setting and no Clear (Adam, 3 November). A write waits half a
second for `.agent-log.lock` beside it and is dropped after: logging never fails a command.

Dangerously skip permissions stays in agentlock's record, `config.skip-permissions.jsonl`, and `agent_log.read`
merges those of the last 7 days in as entries of `kind` `switch`, the record itself never changed. The
window reads `/api/agent-log`, the family's route since siftlog (`agent_log.api_agent_log`, in `server.ROUTES` and
`OWN_PAGE`), each refusal with `said`, its line spoken to him (`agent_log.said`: the drawn lines, else "he" and "his" made "you" and "your"), and the page names each op as a plain action (`AL_OPS` in `family/static/agentlog.js`, each app adding its own from `agentlog_idiograph.js`, `sift_settings.js` and `trace.js`, their words in `agentlog_<app>.json`), "A command Idiograph doesn't have" (or Sift, or Trace) for none. A refusal before a project opened names the one it was asked of (`cli.where_asked`, `idiograph_cli.log_where`), "Not known" in Details where none is.
Agents read it with `idiograph agents log [--since <day>] [--limit n]` (`sift agents log`, `trace agents log`, through
`cli.agents_parser`) and MCP `agent_log` (`mcp_server.log_tool`, each app's own, Sift's and Trace's outside `TOOLS`), read
only, through `cli.agents_log`: in Idiograph an entry naming a project agents may not read now comes back only in
`closed`, a count. `agents` is a family word beside `search` (`cli.FAMILY_WORDS`), no app's own. The page is the family's `agentlog.js`: the
line under Using your own AI agents in page.html (`agentLogLine`, from `openSettings`) and the sheet `#agent-log-sheet`,
Esc closing it from shell.js's keys, its words in `family/static/i18n/en/agentlog.json` and its styles in style.css.
Area 321, and area 323 for Sift and Trace.

**Restart and Quit.** A POST to `/api/server` with `op` of `restart` or `quit` answers only a
request whose `Host` is the server's own address and whose `Origin`, when it sends one, is the same,
as a POST to `/api/mcp` does, so no page served from anywhere else can press either. Both are
refused while a write is still under way after ten seconds, and Restart is refused in one line where
the way of running cannot start again by itself, a Windows run with no `SPAWN` set. It answers,
stops the serving from another thread, closes the listening socket at once, waits for the server's
own lock, which every write holds with the file lock inside it, and runs the same program with the
same arguments through `os.execve`, as `relaunch` in `server.py` gives them: from source the python
and the file as they were run, and in the Mac app the executable with `--serve`, which
`mac_launcher.py` sets as `RELAUNCH`. The process number stays the same, so a launcher's pid file
still names it, and `IDIOGRAPH_RESTARTED` keeps the browser from opening a second tab. Windows
cannot run a program again in one process, so there `SPAWN` starts it anew and this one then ends:
`spawn_again`, the same command as a process of its own on this one's window and output, from source
and in `run.bat`'s window, and in the Windows app the launcher's `respawn`, which writes the new
process number in its pid file. A program that cannot run again ends the way Quit ends it, with the
reason in the log. Quit answers the same way, then clears the pid file when it names this process
and returns from `main`. A GET answers `started`, which a restart changes, `pid`, `restart`, the
line when it cannot restart, and `reopen`, the line Quit shows, which `IDIOGRAPH_START` decides, set
by `run.command`, `run.sh` and `run.bat` to their own names. Before a restart the page keeps where
it is under `idiograph-return` in this tab's `sessionStorage`, `spotKeep` in `app.js`, and its next
start opens that screen again, `comeBack`.

**Quitting after the last tab (16 October).** A tester closed the tab and found Idiograph still
running, so the server quits by itself a few minutes after its last tab closes, with the tick at the
end of General on, `quit_when_closed`, on for a new install. Every page it serves loads
`static/beat.js`, `index.html` and `design.html` by their own tags and the two print views through
`beating`, and beats with a POST to `/api/beat` about every thirty seconds, in view or hidden, with
a last word through `navigator.sendBeacon` on `pagehide`, so the wait runs from the moment the last
tab went. `in_use` wraps `do_GET` and `do_POST`, so every request from the server's own page or a
program on this machine, an agent's included, is a sign of use as it comes and as it ends, and holds
a quit while it is in hand. `watch_idle` starts `idle_quit` on a thread of its own from `main`,
which looks every `QUIT_LOOK` seconds, 15, and once no sign has come for `QUIT_AFTER`, five minutes,
and `holding` names nothing, a request in hand, a write under `_lock`, a Restart or a Quit under way,
a Sift search run in `SEARCH_RUNS`, a Zotero sync in `ZOTERO_SYNCS` or the demo's recording being
made, decides the quit under `_life`, the lock every request takes as it comes, prints
`QUIT_LINE` and stops the serving. `main` then closes the socket and runs `finish` as it does for
Quit, so every write in hand has finished, the server's lock is let go and the pid file a launcher
keeps is cleared, and opening the app again starts it at once. Anything holding it, the tick off, or
a look that comes more than `WOKE_AFTER`, a minute, late, as when the machine slept and no tab could
beat, starts the wait again. A request that comes once the quit is decided is answered 503 with
"Idiograph is closed.", so no write starts after it. A beat with no answer is asked again every two
seconds for forty, so a restart is never taken for a close, then `window.idiographClosed` in
`app.js` shows "Idiograph is closed." with how to open it again, as Quit does, and the beat goes
quiet, as it does after Quit through `window.idiographQuiet`, so an old tab never holds a later start
open. `IDIOGRAPH_STAY_OPEN` in the environment keeps a run open whatever the tick says, as the suite
sets it for every server it starts and a smoke sets it for its own, and `IDIOGRAPH_QUIT_AFTER` sets
the wait in seconds for a check that waits a second or two. Since 31 October (quitcrash) a server the
window started quits at the watcher's next look, without the wait, once the window has gone without
Quit, a crash or a Force Quit: on a Mac a process whose parent ends is handed to launchd, so the server
notes its parent as it starts (`PARENT`) and `window_gone` asks whether it has changed, anything
`holding` names still holding it (area 159). A Restart on a Mac runs again in the same process under the
same window, and Windows hands an orphan to no one and starts a Restart anew from the old server, so it
is never asked there.

**One writer at a time.** `locks.py` is a file lock the server and the command line both take
around every write, `fcntl.flock` on `Working/.idiograph.lock` in a case for its workbook, progress
file and themes file, and `.idiograph.lock` at the case root for the GETs and project files, with
`msvcrt.locking` on Windows. The server takes it inside its own lock through `writing` in
`server.py`, every route that writes, and the command line around its read, its check and its
write. A write that cannot have it in ten seconds says so and writes nothing. The system lets a
lock go when its process ends, however it ends, and a folder that is not there takes none.

**The schemas.** `docs/schemas/` holds a JSON Schema for each file a project keeps, `themes`,
`progress`, `project` and `gets`, and `idiograph validate` reads every file of a project against
them with the standard library, each problem one plain line. The suite runs it over the demo.

**An AI prompt's room (14 October).** `themes_ai.room_of(route, tokens)` is the characters a prompt
has at four characters a token: on a local model `PROMPT_CEILING`, its context less 12,000 tokens kept
for the answer (`ANSWER_ROOM`), and on Anthropic its context less the call's own answer room, thinking or
not. A title's prompt on PETs goes through `cut_quotes`, the quotes of the statements lowest on the
canvas going first, by `y` and then `x`, one statement at a time, against `PROMPT_CEILING` on either
provider. A GET's title prompt goes through `cut_words`, the words of the lowest statement of every PET
first, against `room_of`.
The statements, their keys, the labels and his request always go whole, so a ceiling no cut can meet
sends every statement bare and no thread. The prompt says what it left out, and `room_said` ends the
answer's `said` with `cut_line`, `gets_cut_line` or `thread_line`, cutting the answer's own words at a
word where the whole would pass the 2,000 characters a thread's line keeps. The grouping, the review
and a reply on PETs are sent whole (see Known gaps).

## How the workbook is written

**Why the workbook is the store** (Adam's ruling of 11 November 2026, after storeeval's evaluation). The
transcript, the exploratory notes and the statements live in the participant's Excel workbook, not in a file
of Idiograph's own, for three reasons: it is the IPA table supervisors and examiners read, it opens in Excel
with no Idiograph at all, and it is current at every save, with no export step to forget. The cost is a save
of under a tenth of a second at 600 passages (savespeed's figures below). It would change, to a native file per participant
with the workbook as an export, if workbooks well past 2,000 passages became usual, if Working together
needed two people on one participant at once, if testers lost work to Excel's lock or a format fault, or if
Adam decided that for 1.0 the workbook is an export and not the record.

Every save takes the same path, in `workbook.py`:

1. Refuse if `~$<name>.xlsx` sits beside the workbook.
2. `load_workbook(path, rich_text=True)`.
3. Touch only columns C, E and F, column D only when the
   text of the turn is corrected or a find and replace changes it, or `/api/crux`, which the page no
   longer calls since Highlight went on 16 October, adds or clears a highlight, column B only when a timecode
   is corrected, the Interviewer notes
   column only when a note is written on one of the interviewer's turns, and whole rows only
   when words are assigned to another speaker or the ends are trimmed, or either is undone. A find
   and replace writes every transcript cell it changes through the one per-cell write a correction
   takes, `rewrite_transcript`, and since 26 October the statements, quotes, exploratory notes and
   Interviewer notes cells of the same rows as plain text, an entry at a time (see Find and replace's
   reach), and saves once for the whole of it, its undo and its redo the same. A cell
   whose entries are unchanged is left exactly as it is, spacing and all, so revisiting a turn and
   moving on writes nothing at all. The Interviewer notes column is added the first time a sheet
   takes a note, its heading in the first empty header cell after the last used one, G in the
   standard layout, in the header font and 42 wide, and found by its header on every read after
   that, wherever it sits.
4. Have openpyxl write the workbook into memory, nothing packed (`shared_strings.save`, its
   `ExcelWriter` run as openpyxl's own `save_workbook` runs it).
5. Convert the inline strings openpyxl writes into a shared-strings part, the way Excel writes
   them (`shared_strings.share`), check every XML part with expat and pack the file once into a temp
   file in the same directory, its CRCs checked after (`shared_strings.pack`). Until savespeed (11
   November 2026) openpyxl packed the file to disk, the pass read it back, packed it again and checked
   it by building a minidom tree of every part, about half of a save's time. The parts are byte for byte
   what that wrote, which area 174 holds on both writers. Excel for Mac rejected a workbook with inline rich text on
   19 September 2026, which is why this step exists. Since 17 October each string is set out as
   Excel writes it, so the shared strings are the same bytes whether openpyxl wrote with lxml or
   with ElementTree: an empty element with no space before its slash, a character past ASCII as
   itself, a carriage return as `&#13;`, which every save without lxml had turned into a line feed,
   `xml:space="preserve"` on every run and cell whose words begin or end with a space, which
   openpyxl leaves off a run of spaces alone with either writer and off a cell of spaces alone
   without lxml, and the body font's scheme, `<scheme val="minor"/>`, only on a run in the
   workbook's own body font, its minor font, or in none named. Until then a run in another font in
   the body colour, Georgia in black, gained it on every save, which marks the run to Excel as one
   in the workbook's body font.
6. `os.replace` over the original.

**What a save costs** (savespeed, 11 November 2026). `/api/commit` answers the page's counts from the
workbook it has just saved, `save_turn(..., outline=True)` handing `workbook.outline_of` of it to
`refresh_summary`, each passage's sheet, row, speaker, seconds, statements and other speaker's mark read as
`read_case` reads them, so a commit no longer reads the whole file a second time (area 58 holds the counts
the same as a fresh read's). Median of five on the evaluation's invented workbooks, on Adam's Mac, before
and after: a statement saved 140 to 74 ms at 600 passages and 512 to 231 ms at 2,000, the whole commit 179
to 83 ms and 608 to 242 ms, a correction 138 to 77 ms and 505 to 231 ms, Replace all there and back 360 to
195 ms and 1,144 to 562 ms. Opening is unchanged, 33 and 101 ms. `shared_strings.normalise_string`
runs each of its passes only on a string holding what that pass looks for, and `edged` looks at a run's two
ends where a pattern ending in `$` had been tried at every character.

**A statement and its quote.** Column C holds the statements and column F the quotes, each
cell's entries separated by a blank line, and the two pair by place: the first quote is the first
statement's (item 198). A statement's key is `sheet:row:i`, and a quote's key is `sheet:row:i` of its
place in the quotes cell, so a statement and its own quote share one key, and every board's
picks stay valid. Once a turn has a quote, `pairs_to_cells` in `workbook.py` writes exactly one entry
a statement into column F, `(no quote)` for a statement with none, and a quote whose statement is
empty after them. A turn with no quote at all keeps the cell empty. `quote_entries` reads the cell by
place with `(no quote)`, Excel's spelling of it included, as empty, and every reader goes through it,
`read_case`, `read_cards`, the command line and the counts an assignment's card gives, so the mark
is never a quote anywhere and never moves another quote's place. `pairs_of` pairs a turn by order,
and `unpaired` names a turn saved before this, at least one quote and a count of entries in column F
that differs from its statements', which pairs by order on screen and is listed under Quotes to pair
until a save writes it paired. A merge of rows keeps each row's quotes with its own statements
(`merged_quotes`).

**A pair's heading and its Remove (14 October).** On the turn screen `pairHtml` in `app.js` opened
each pair with `.pair-head`, a label `.pair-num` in the Quote label's small capitals and the
shared Remove, `button.btn-remove.pair-remove`, where a cross once sat inside the statement's field.
Since 17 October, in the current passage's card, `.pair-num` is the number alone beside the
statement, the label of its field, and Remove stands in `.pair-qhead` at the right of the Quote
label, `.pair-head` gone (see The three columns). Since 18 October, Adam's drawing, Remove is
`button.pair-remove` alone, no longer a `btn-remove`, a bin drawn inline with no word, last in the pair
so `Tab` meets it after the quote, placed by `.pair-body`'s grid in the statement's row at its right,
6 pixels from the top so its middle meets the first line's, so the statement's field ends short of it and `.pair-qhead` holds the label
alone. It stands in `--ink-soft` and takes `--danger` with a wash of it under the pointer and in
`:focus-visible`, its tooltip and accessible name Remove this statement, and the red line round the pair
follows `:hover` and `:focus-visible`.
`pairsDrawn` runs after every change to the pairs, a turn drawn, Add another, a quote or a candidate
taken, a removal and its undo, and numbers each pair by place: the number reads 1 and on and the
statement's accessible name Experiential statement 1, where until 18 October Remove's read Remove
experiential statement 2 and its quote.
Remove keeps the cross's `data-remove`, `tabindex="-1"` and `removePair`, so its click, its one step
of undo and the focus after are as they were. A `::after` line in `--danger` on `.pair`, shown by
`:has()` while Remove is hovered or has the focus, is drawn over the pair's margins, so it
moves nothing.

**`q`, one key for a quote (16 October).** `quoteTarget` in `quote.js` names where the selection
goes, `{place, added, old}`: the quote of the pair being worked on while it is empty, "(no
quote)" counting as empty, whatever its statement holds, and else a new pair under the last, where
Add another puts one, `old` the quote field as it read. `commitQuote` in `app.js`, on `q` in the
page's keydown and on the toolbar's `#sel-quote`, as on `#btn-quote` under the fields until 17
October, says the line about selecting first when nothing is selected,
keeps an open interviewer note first, goes through `goTo` to another of her passages when the
selection is there (`selectionElsewhere`, from `selectionTurns`), takes the pieces and the quote
through `takeSelection`, `pendingQuote` and `mergePieces`, writes the quote with `insertPair` for a
new pair, puts the caret in the pair's statement and pushes one entry. An empty quote filled
pushes `what: 'the quote'` with `old`, undone by `quotePut` through `quoteOut`, which finds the
pair holding exactly the new quote and gives its field back `old`, and redone at the entry's place,
what it finds there becoming `old`. A pair added pushes `what: 'the new pair'`, undone and redone by
`statementPut`, which takes the pair out while its statement is empty and else empties its key
quote and leaves the statement, `taken` saying which. A turn already saved with the quote is saved
again either way. `undoPush` drops the oldest entry past `UNDO_DEPTH`. From 14 October to 16 October
`quoteTarget` answered `{place, old, replaced}`, `commitQuote` wrote over a quote there and
`undoPush` held a replaced quote of the turn in front of him past the depth. The picks on a PET
board follow through `themes.follow`, as for a quote edited by hand, with no pick logic of its own.

**New statement from the selection (16 October).** For that morning `statementTarget` in `quote.js`
and `statementFromSelection` in `app.js`, on `s` and `#btn-statement`, made a pair from the
selection while `q` replaced. The same afternoon both went into `quoteTarget` and `commitQuote` (see
`q`, one key for a quote), and `statementTarget`, `statementFromSelection`, `s` and
`#btn-statement` are gone. `statementPut` stays as the undo of a pair `q` adds. Nothing stored
changes shape, and the AI parts are untouched.

**Quotes in the passage (16 October).** `quoteSpans(quote, text)` in `quote.js` answers where a
quote stands, one `{start, end}` a piece, the inverted commas round the whole quote set aside,
the pieces split at an ellipsis, `…` or three dots, or at a clarifying insert in square brackets,
never looked for, a piece with no letter or digit dropped (20 October), and each found after the one before in the text
folded the same way, each run of spaces one space, case set aside and curly inverted commas and
apostrophes made straight, each found piece mapped back to the passage's own offsets. A piece not
found makes the whole answer empty, so a quote the passage no longer holds goes unmarked.
`kqLayer(row)` in `app.js` lays every pair's spans over the passage as `{cls: 'kq', kq: n}`, from
`livePairs(row)`, the fields while `S.pairsRow` names the passage, set as `drawTurn` draws its pairs
and cleared as a case opens, and `rowPairs(row)` otherwise. `drawTurn` and `findFieldsAgain` set it
just before `drawPairs`, never after it (countdrift, 30 October 2026): `drawPairs` draws the status bar's count, and
with the passage just left still named there the count took the new passage twice and the one left not at all. `rowHtml` and `paintTurn` hand them to
`markedHtml` with the pieces being built and the find's washes, and `markedHtml` gives each chunk
its classes and, under a quote, `data-kq` naming the places of its pairs and a title from
`kqTitle`. `markedHtml` no longer reads a run's `crux`, so a highlight is drawn as plain words. The same cuts hold in `cli.quote_in`, `turn write`'s check (its `QUOTE_CUTS`), and in
`gets_print.pieces`, which bolds a quote in the GETs print. `turn write` checks only a quote the turn
does not already hold, by `quote_words`, so a sibling sent back unchanged never blocks a write (20 October).
`markKeyQuotes`, from `pairsChanged` and from a keystroke in a quote, repaints the current passage
when `kqSignature` has moved, the selection kept. `lightMarks` puts `.lit` on the marks of the pair
in `S.kqHover`, from `mouseover` on `#pairs`, or else `S.kqFocus`, from `focusin`, by place. The
column's click sends a plain click on `.turn-text .kq` to `toStatement(row, n)`, which keeps an open
note, focuses the pair's statement on the current passage and else goes through `goTo` first, and then
`pairIntoView` (21 October) scrolls the box's nearest scrolling column by just enough to show it whole,
its top first when it is taller than the view, and not at all when it shows already. A drag never gets
there, as `pressMoved` and `selectionLive` return first, and words under two quotes carry `data-kq` in
order, so the first number is the first statement. The
style is `.turn-text .kq`, `--crux-wash` with a `--crux` rule under it over words in their passage's
own ink, stronger with `.lit` or under the pointer, and `white-space: pre-line` inside it, so the
space where a quote wraps folds away and the wash and the rule stop at its last word on the line
(16 October, later, where its words were `--crux` and the wash ran on over that space).

**A quote across her passages (quotespan, 30 October 2026, Adam: "Adjacent passages may combine into one
block quote with a timecode range").** A quote may take in the same speaker's passages next to its
statement's own. It is still one quote in one entry of its statement's row's quotes cell, the words alone,
its pieces in transcript order joined with " … " as pieces of one passage are, so an older Idiograph reads
and shows the same words and only leaves them unmarked. Nothing else is stored: which passages it takes in
is found from its words on every read, as where a quote of one passage stands always was, so a correction,
a trim, an assignment or a find and replace under a piece is followed as a quote of one passage is
(Replace all changes the quote's cell and the transcript's alike, and anything else leaves it unmarked).
Two passages are adjacent when they are the same speaker's on the same sheet, the name compared with case
and spacing set aside, with nothing between but the interviewer's turns (Settings' `interviewer`) or rows
with no speaker, so no participant passage, hers or another speaker's, a turn the workbook marks as another
speaker's included, is ever skipped. `workbook.quote_reach(quote, texts, home)` and `quoteReach` in
`quote.js` hold the one rule: the pieces (`quote_pieces`, `quotePieces`, the cuts `quoteSpans` always made)
are found in order, each after the one before in the same passage or anywhere in the next, so the passages
taken in run unbroken, each holding a piece, the statement's own among them. Its own passage is tried
alone first, which is exactly `quoteSpans`'s answer for a quote of one passage (`quoteSpans` is now
`quoteReach` over that passage alone), then running on into the passages after it, then starting up to n - 1
passages before it for a quote of n pieces. Within a passage the earliest place a piece stands is taken, as
before, and a search that fails is remembered by piece, passage and place, so a long quote never searches
twice. A quote of one piece never runs on. `speakers_run(rows, i, interviewer, most)` gives the adjacent
passages either side, `quote_turns(rows, i, quote)` a statement's quote as (row, start, end) pieces, the
interviewer read from Settings (`interviewer_name`) only for a quote its own passage does not hold, and
`time_span(first, last, form)` the range, "25:51–26:50" with an en dash in the project's timecodes, one
time where the two read the same. `themes.read_cards` reads every row of a sheet into `spoken` and
`spread_quotes` gives each quote that runs on, and its statement's card, `time` (the range), `span` (the
first and last passages' seconds) and `rows`, the card keeping its own `seconds` to play from, so the
canvas's cards and Inspector, the Table view, `outline` and every export made from it (the print view, its
PDF, the Word document, the PET draft) and `statements` give the range with no change of their own,
`outline`'s picks taking the quote's own `time`. `gets.snapshot` copies `span` onto the GETs file's line,
and `gets.retimed` writes a line with one as the range, so the GETs and LGETs boards, the GETs print and
the trail give it too once the participant's changes come in. On the page (`distil.js`) `quoteRun(row, most)`
and `quoteTurns(row, quote)` are the same rule over `S.flat`, a passage being `row.stop` and another
speaker's turn `row.other`. `kqLayer(row)` lays the quotes of the passage's own pairs and of the pairs of
her passages up to `KQ_NEAR` (8) either side whose quotes run on into it, a piece of another passage's
quote carrying `from`, that passage's index, which `markedHtml` writes as `data-kq-far="i:n"` beside
`data-kq`, coloured by its statement's place, with `kqFarTitle`'s tooltip, "Experiential statement 1,
25:51". A click on such a mark goes to `toStatement` of that passage, `lightMarks` lights them with the
pair under the pointer or the caret, and `markKeyQuotes` repaints the passages the current passage's quotes
ran on into and run on into now (`kqFarPaint`, `S.kqFar`, set in `drawTurn` from `kqFarKeys`). The pieces
being built (`S.pending`) each carry `key`, their passage's, and with a piece held a Cmd selection in another
passage goes to `takeBeside`, which refuses with a line, through `besideRefusal`, the interviewer's turn
(`distil.pair.span_interviewer`), another speaker's passage (`span_speaker`) and a passage not next to
those the pieces are in (`span_next`), a selection over two passages with `distil.assign.two_passages`, and
else takes the piece there, marks it (`pendingLayer` in `rowHtml`) and keeps the selection.
`selectionElsewhere` passes over words just taken that way, so `Q` and the selection's Quote take the pieces
there instead of going to that passage. `pendingQuote` is `assembleAcross` over `pendingRows`, an ellipsis
at every gap, and the pieces kept for undo carry their keys (`paintPending`). `clearPending` and `drawTurn`
repaint the passages holding pieces. The command line's `turn write` takes a quote its passage does not hold
when `quote_rows` finds it running on, says so in its dry run and its answer ("The quote ... would take in
rows 156, 158 and 160 of Initial, 25:51–26:50", `spans` in its JSON), and else refuses it with
`quote_refusal`'s line, a piece in the interviewer's turn, in another speaker's passage, in a passage of hers
not next to this one or skipping one of hers, or the line it always gave. `turn show` and `statements` add
the rows and the range to such a quote's line, and `rows` and `time` to its JSON. No route is new: the page
saves the quote through `/api/commit`, whose parity entry is `turn write`.

**A colour per statement (18 October, Adam's choice from a drawing).** `markedHtml` gives a key
quote's chunk `data-es-colour`, its first pair's place modulo 6, and on words two pairs share
`data-es-colour-b`, the second's. `pairsDrawn` sets the same on each `.pair` by its place and
`statementsHtml` on each `.es-n`, so a removal, a move or an undo recolours the marks, which
`markKeyQuotes` repaints as `kqSignature` moves, the dots and the stripes at once. In `style.css`
`[data-es-colour="0"]` to `"5"` set `--es` to `--crux`, `--th-case0`, `--th-case2`, `--th-case3`,
`--th-case4` and `--th-case5` from `themes.css`, the board's order with Olive left out, and `--es-tint`
to `--es-tint1` to `--es-tint5` from `tokens.css`, and `[data-es-colour-b]` sets `--es-b` the same.
`.turn-text .kq` takes `--es` for its rule and `--es-wash` of `--es-tint` for its wash, `--es-lit`
lit, statement 1 keeping `--crux-wash` and the crux at 24 per cent lit. Each tint is its colour's
OKLCH hue, moved up to 15 degrees so no two washes read alike, at Excel orange's lightness, 0.76,
with as much chroma as sRGB holds up to the orange's, and `--es-wash` is the most of it at which the
words on every tint read at least as on `--crux-wash` in that theme, 12.5 per cent in light and
14.5 in dark, `--es-lit` 34 and 22 against the crux's lit wash. A mark
with `data-es-colour-b` draws its wash and two rules as background layers inside a padding of 4
pixels, 6 lit, the first rule where the box shadow stands on any mark and the second under a gap of
the passage's ground, the pending piece and the find's washes taking the wash's place over it.
`.pair-num` is a dot of `--es` with the number in `--card`, `.pair .pair-kq` a 3 pixel left border of
`--es`, its left padding 2 pixels less, and `.es-n` a smaller dot. Olive stays out, 0.6 from the dark crux
under protanopia and deuteranopia.

**Done marks (16 October).** `turnHtml` gives every row a `.turn-done` span, and `drawDoneMarks`
sets `data-done` on each `.turn` of the drawn sheet from `doneLevels(rows, states)`: 2 for
`has-content`, 1 for `reviewed-empty` alone, through `DONE_LEVEL`, and nothing for `unvisited` or
`passed`, a passage only jumped over (Adam's word of 16 October), and each run of the interviewer's
rows the smaller of the two participant rows either side, nothing before the first or after the last.
The states are `S.data.progress.states`, the server's `row_states`, unchanged, so the counts and the
rounds still take `passed` as decided while its bar stays off. It runs at the end of `drawTranscript` and of
`drawProgress`, after every commit, skip and round close, and writes nothing. The span stands at
`left: 98px`, 2px wide, the whole height of the row, in `--good` whole and at 45% through
`color-mix` (72% and 36% until 16 October, later, when the first read grey in light), under
`.turn.current::before`, which is solid, `--crux` mixed 45% into `--paper`, so the green never shows
through it as brown, and below 1000 pixels of window at the row's left edge, 3px wide, the current
passage's pinned there too with `right: auto`, where `.turn` and the round markers keep 12px of padding
on the left. There the band of `#work.same-size .turn.current` draws its
hairline above, below and at the left alone, so nothing of the current passage stands in the
scrollbar's lane at 360.

**On screen, not behind keys (16 October).** After a tester found too much hidden behind keys and
right-click, and typed a c into a statement pressing `c`. The toolbar by the selection is `#sel-bar`
in `index.html`, beside the transcript column, `position: fixed` under the title bar, with
`#sel-quote` and `#sel-give`. `selBarPick` in `app.js` reads `selectionTurns()`, and takes a
selection inside one participant passage's text, every rectangle of the range's `getClientRects()`,
the first and the highest top and lowest bottom among them. `selBarPlace` stands the bar 6px above
the highest, or under the lowest where the column has no room above, its left at the selection's,
kept inside its room from `selBarRoom`, and hides it where neither fits, so it never covers the
words. `selBarRoom` is the column less 4px each side, and where the passage's `.turn-notes` stands
beside its `.turn-text`, the words' side of it, 4px clear, so the bar never covers the notes (16
October, later, after it was found on the first line and the notes' edge at 1280, measured then
from the first and last rectangles alone). Its `animation` is `fade`, where `rise` brought it up
over the line under it. Before it measures the bar it sets its
`max-width` to the column's width less 8px and its `left` to the column's left edge, so a narrow
column wraps it inside and a place left from before never squeezes it past the edge, which at 360px
it did. Both are its room's since 16 October, later. `#minimap` stands outside `#transcript`, and the bar, fixed over the page, stands over its card where the two meet. `selBarShow`, from the column's `mouseup` after
`takeSelection`, places it and moves the focus from a field to `#transcript`, which carries
`tabindex="-1"`, so the keydown's `typing` is false and `q` and `c` act. The bar's `mousedown` is
prevented, so a press keeps the selection and the focus, `#sel-quote` calls `commitQuote` and
`#sel-give` `assignKey`. It goes on Esc, first after a menu, with the selection and the pieces, on a
`selectionchange` that leaves nothing selected in the column, as `commitQuote`, `assignKey`,
`openRowMenu` and `drawTurn` begin, and it follows the words on the column's scroll and the window's
resize. `.row-menu-open`, the margin's three dots, lost its `opacity: 0`, so it stands in view on
every row. On the canvas `#th-group` and `#th-undo` call `thGroupKey` and `thUndo(true)`, their
`pointerdown` prevented so the focus stays on the canvas. `TH_MORE`, a `.th-more` button, ends every
card's and label's markup in `thRender`: on a card it shows with `.sel` at the top right corner, and
on a label with its other small controls. A click on it in `#th-world` opens `thMenuOpen` on that
item under it, and `thPointerDown` passes it by as it passes `.th-del`. The menu's entries whose act
is in `TH_TAKES`, `leave`, `delete` and `unstick`, and the board menu's delete carry `btn-remove`,
their border kept quiet in a menu until the pointer is on them. `keyName(text)` in `app.js` gives a
tooltip's key as the machine names it, Ctrl for Cmd off a Mac, and at boot every `title` with "Cmd +"
in it passes through it, the PETs bar's Undo among them. `drawAct` adds "(Cmd + Enter)" to the filled
button's title.

**Quotes a write keeps.** A pick matches its quote by `themes.quote_words`, the words with the
inverted commas round the whole quote set aside, double or single, straight or curly. `themes.follow`
does the matching for the canvas's open, the server's save and the command line alike, so a quote
that gains or loses inverted commas keeps its picks, and a pick that stays takes its quote's words as
they read now under `quoted`. Only a change of words moves or drops a pick. A lone quote is a quote
past a turn's statements with no statement of its own. `idiograph turn write` keeps every lone quote
of its turn that its spec does not name, in its place and as it stands (`cli.lone_after`), and takes
a pair with a quote and no statement as one. Statements alone on a turn with a lone quote go with the
quotes in their places, where before they left the cell for him to pair. The dry run and the write
list the lone quotes kept and every pick on a board of the case the write moves or drops, from
`themes.pick_moves` on the turn as the write leaves it (`themes.with_row`).

**How many picks a label takes.** One rule, `themes.picks_kept`: every quote he picks, each once.
The tick on the PETs screen, `normalise`, `board new` and a pick operation of `board apply` keep
every one, so a file's three are never cut. A board that sets no `pick_max` of its own is held to two,
`themes_ai.PICKS_MAX`. Before this a pick from `board apply` kept two.

`tests/test_idiograph.py` compares all 2,640 cells of the reference workbook's three sheets before and after, run by
run and colour by colour, including column widths, freeze panes and zoom. Marking a highlight and
clearing it again leaves the workbook identical, and a save of the statements leaves a highlight's
rich text byte for byte as it was, which area 153 holds since the page stopped drawing them. Area
174 (17 October) sets a workbook out by hand as Excel writes it, on an invented allotment, rich text
in every column the app reads and writes, a person's fill, a carriage return and a cell of spaces
among it, and runs it through every save path twice, in a child Python with `OPENPYXL_LXML=False`,
the writer the app ships with whether lxml is installed or not, and in the suite's own. Every cell
is read back from the file's own XML with the standard library, run by run, words, spaces and
properties, against the fixture, and the two writers' shared strings must be the same bytes.

Progress lives in `<case>/Working/<stem>.progress.json`, never in the workbook: per-row state,
measured minutes per round, the daily tally, a record of every trim, with its id and whether it has been undone, a record
of every turn corrected in place, a record of every assignment, and `complete`, the time the phase
was marked complete, once it is (see [docs/manual.md](manual.md), Complete). A progress file written before 3 October 2026 can
also hold `flags`, the turns flagged for later while the app still had flags: they stay in the file
as they stood and move with their rows, and nothing reads them. The row states it stores are
`has-content`, `reviewed-empty` and, by their absence, `unvisited`. `passed` is never stored: it is
derived from those and from `last` whenever the case is read, so opening a case writes nothing to
it. A sidecar written before any of those existed loads with them empty. Delete it and only the
tally, the timings, the three records and the mark are lost, and an assignment or a trim made
before then can no longer be undone, because a row with a statement in it counts as done from the workbook
itself. That also means a finished case opened with no sidecar reads every blank turn before the
last statement on each sheet as passed, so its rounds up to there show done and close on that
open, counted today.

## Files on disk

Idiograph keeps no database. Beside each case's workbook it writes two JSON files, in the case's
`Working/` folder and named by the workbook's stem. At the case root it keeps the project file and the GETs file, and
beside itself `config.json` and `state.json`, which the Mac app keeps in
`~/Library/Application Support/Idiograph` instead. Each is written to a temporary file in the same
folder and moved over the old one with `os.replace`, so none is ever left half written. A
transcript made into a workbook gets its raw source beside it in the case's `Source/`, written the
same way and never over a file there, and the transcript itself is only read.

**The project's own History** (projhistory, 2 November 2026, Adam's yes by dialog). `project_history.py`.
`idiograph-history.json` at the case root, `{"schema": 1, "history": [...]}`, oldest first and the last 500
kept, each record `{"when", "op", "changes", "by"}` with `tool` and `request` when `by` is `agent`. The route
that makes the change adds it under the project's lock (`locks.root`), the same hold as its own write, through
`record(root, op, changes, who)`: `api_project`'s save (`project set`, its lines `project_changes`, the privacy
tick among them), `write_timepoints` (`timepoints`), `write_statement_words` (`length`), `api_complete`
(`participant complete`, which now takes the project's lock before the case's, as `writing` orders them, and
records only a mark or a reopen that changes the mark, `complete_said`), `rename_case` (`participant rename`,
the line kept with its undo in `back`, so a failed rename takes it away too) and `gets.settings_op` (`gets
settings`, its lines `gets.settings_changes`). `asker(body)` reads who asked: the command line and MCP send
`tool` and `request` (`idiograph_cli.asked_by`, the tool carrying "approved in the app" or "without asking"
from `holds.gate` and `holds.approve`), and the page sends neither, so its records say `app`. A dry run, a
refusal and a change with no line write none, and the demo keeps none. `project history` and MCP's
`project_history` read it, `--limit` the newest. `project_pack.LEFT_OUT` never sends it. Area 319.

**Working together's keys and pairing** (wtkeys, 8 November 2026, build 1 of the design of that day, the spec in
the harness, `history/Idiograph_working_together_spec_08Nov26.md`, and Adam's choices about 19:10 by dialog). `team.py`
and `transport.py`. PyCA `cryptography` 50.0.2, pinned in `build_mac.PINS` (and so Windows's), `run.sh`,
`run.bat` and the workflow's three installs. It is imported only when Working together is used (`team.lib`), so a setup
from before it starts as it did and is refused in one line (`team.refused.needs_library`) when he ticks it. Off is
the default and costs nothing: `team.view` reads `team.json` alone and answers `{"on": false}`, and nothing makes a
key or writes a file until `on`. The device file `team-device.json` sits beside `server.CONFIG_PATH`, the app's data
folder when installed and the repo's root from source (in `.gitignore`), written through a new name at mode 600:
`device` (Ed25519 `sign`, X25519 `box`, both raw in base64, their public halves, `id` the first 16 bytes of SHA-256
of the signing key in hex), `teams.<team>.keys` (each epoch's 32-byte key), `invites` (the secret, `expires`,
`used`, `thrown`), `seq`, and `joining` while a join waits. `team.json` at the project's root (`project_pack.LEFT_OUT`
with `.idiograph-team/`, where `note_dropped` logs a dropped message): `on`, `team` (16 random bytes, the relay's
project id), `member`, `route` (`relay` or `folder`), `folder`, `recordings`, `roster`. The roster: `n`, `team`,
`epoch`, `lead`, `members` (`id`, `name`, `role`, `devices` with `id`, `sign`, `box`, `added`), `owners`
(participant folder to member), `gets_owner`, `keys` (the epoch's key sealed to each device), `signed_by` and
`sig`, a device of the lead's signature over the canonical JSON of the rest (`canon`: sorted keys, no spaces).
`check_roster` refuses one not signed by a lead's device, or one numbered no higher than the one held. Sealing:
the library has no XChaCha20, so `aead_seal` takes a fresh 24-byte nonce, HKDF-SHA256 over it for a key of its own,
and ChaCha20-Poly1305 with a zero nonce. `seal_to` is an ephemeral X25519 exchange, HKDF and ChaCha20-Poly1305.
`seal_envelope` and `open_envelope` are section 4's envelope, the inner message padded to 4, 16, 64, 256 KB or 1 MB
(`pad`), the head as associated data, refused as `tampered`, `not_on_roster`, `bad_signature`, `kind_not_allowed`
(a roster from anyone but the lead) or `no_key`. The words: `team_words.txt`, 2,048 plain words (shipped through
`app_identity.FILES`), 128 bits and a 4-bit check in twelve 11-bit words (`secret_words`, `words_secret`), the link
`https://idiograph.app/join#<words joined by ->`. `invite_id` and `invite_key` are HKDF of the secret, the mailbox
`invite/<id>` (`transport.INVITE_PREFIX`). An invite posts the lead's device keys sealed under the invite's key, a
join reads them, refuses a closed or expired invite, posts its own name and keys, and both sides compute
`check_code` from SHA-256 of the secret and both devices' keys. `admit` with `match` puts the joiner on the roster,
seals the epoch's key to his device, numbers and signs it, posts a `welcome` and a `closed`, and marks the invite
used. `joined` checks the welcome's roster against the lead's device the invite named and keeps the key. `remove`
makes the next epoch's key, sealed to the devices left, the roster sent under the epoch before. The route is
`/api/team` (`api_team`, ops `show`, `on`, `off`, `set`, `choose`, `invite`, `answers`, `admit`, `join`, `joined`,
`remove`, each write under the project's lock with a `team <op>` History record), the command line's `team` and
MCP's `team_*`, area 261's parity mapping them. `team on`, `invite`, `admit` (a match), `join` and `remove` are
`holds.HELD`, risk 4. Transport: `send`, `fetch` and `listen` as wt-common names them, a route's factory
`factory(device, team)` registered by its module (`transport.register`), and `Loopback`, in memory (`Hub`) or in a
folder two servers share (`IDIOGRAPH_TEAM_LOOPBACK`), for the suite and a smoke run. With no route registered an op
that sends is refused (`team.refused.no_route`). The page: `#wt-block` in Project settings before the agents'
block, `#wt-invite-card` and `#wt-join-card`, `team.js` (`wtOpen` from `openProjectSettings`, polling `answers`
and `joined` every two seconds while a card is open). Area 341.

**Working together's owners and versions** (wtowners, 8 November 2026, the spec's build 2). `team_sync.py`.
The one writer: `team_sync.guard` is `workbook.WRITE_GUARD`, run by `workbook.case_held` before the case's lock,
which every write to a participant's files takes (`routes.writing` for the app and the routes the command line
calls, `case_held` itself in the command line's board ops), so the app and an agent are refused alike. It finds the
project by the nearest folder above holding a project file, and, where `team.json` is on, refuses
(`team.refused.not_yours`, code `not_yours`) a participant whose owner, `roster.owners[folder]` or the lead, is not
`team.json`'s `member`. An export passes `export=True` (`writing(..., export=True)` in `api_export` and
`api_themes_export`, the command line's `board export`) and is not refused. The command line's `turn write` runs
the guard before it reads the write, its dry run too, so a write that would change nothing is refused in the owner's
words, never "Nothing to write" (smokefix, 9 November 2026). `team_sync.gets_guard` is
`gets.WRITE_GUARD`, run by `gets.write` for the GETs file (not an LPETs file, `FILE_AT`), refused when
`gets_owner` is someone else (`team.refused.not_yours_gets`). Both are set when the routes load
(`team_sync.install_guards`). Versions: `mine` lists this member's participants (`participant_books`, their
workbook, the `Working/` files of its stem that are a progress file or `project_pack.PETS_FILE`, recordings by
`kind_in_case` when `recordings` is on) and the GETs board when it is his (`project_pack.GETS_FILES`). `waiting`
compares each one's prints (`[size, mtime_ns, sha256]` by path, the SHA-256 taken again only when the size or time
moved) with those it last went with. `push` sends what has waited `WAIT` (60) seconds since its newest file's time,
or all of it with `now`, and to a device on the roster not in `copied` everything of his at once, the first full
copy. A version: `{participant, n, files: [{name, sha, size}], zip}` (kind `version`) or `{n, files, zip}`
(`gets_version`), the zip in base64 inside the envelope up to `INLINE_MOST` (640 KB) and otherwise `blob`, a random
32-hex name, the zip sealed under the epoch's key with the name as associated data and put with the transport's
`put_blob` (the relay's, and the loopback's in memory or in its folder's `blobs/`). `n` is one more than the
higher of the count sent and the count taken in. `pull` fetches from `cursor`, passes over its own device's,
opens each (`team.open_envelope`), takes a roster (`team.take_roster`), applies a version through `take_version`,
and hands any other kind to `HANDLERS[kind]` when a later build registers one. `take_version` drops one from a
member who is not the owner, one for a participant this member owns, one whose folder or a file's path is not a
participant's (`allowed_folder`, `allowed_in_case`) and a SHA-256 that does not match, each noted in
`.idiograph-team/log.jsonl`, passes over one numbered no higher than held, moves the count on in silence when the
files are those here, and otherwise writes each beside its place (`.<name>.incoming`) and renames it into place
under `server._lock` and the case's lock (the root's for the GETs), dropping it from `workbook.WRITTEN`, so a
board or the statements screen says "changes made elsewhere". The lead's first full copy carries every
participant, and another's keeps the count it came with: a computer that has nothing of a participant or of the
GETs board yet takes the lead's copy of it as its first. `.idiograph-team/sync.json`: `cursors` (one count a
transport, by its kind, so a change of route starts its own), `sent` (by
folder or `gets`: `n`, `print`, `at`), `held`, `arrivals` (`member`, `at`, `n`), `copied`, `failed`. `sync` runs
`pull` then `push` under a thread lock and `.idiograph-team/sync.lock`. Working together's own files (team.json, the
device file, `sync.json`, `out.json`, the boards' record and the shared folder's numbering) are read through
`locks.read_json` (teamflake, 9 November 2026): a file not there reads as none, and one there that will not read or
parse is read again `READ_TRIES` (5) times `READ_PAUSE` (0.1) seconds apart and then refused as busy, so a look
writes nothing rather than starting its counts, keys or waiting messages afresh. Under load (a virus scanner, Time
Machine) one such read had made the lead send a full copy numbered from one, which the others dropped as older.
Each is written under a temporary name of its own (`locks.new_tmp`), and the device file's reads and writes are one
under `team.device_held` (a thread lock and `team-device.json.lock`), so the server's looks, a request and the
command line never lose each other's sequence numbers or keys. The server's thread (`team_sync.start`
from `routes.start`) looks every `EVERY` (15) seconds and when a transport's `listen` says something came, and
`atexit` sends what waits at once. `/api/team` op `send` is Send now (`team send`, `team_send`), its dry run
listing `due`, with no History line. `status` is what the project's page shows, `team` in `project_section`
while on: `tags` by participant label (`owner`, or `review` from `REVIEW_WITH`, the review build's to set),
`arrivals` today, `waiting`, `offline`. `team.js` `wtPageDraw` puts the tags before a row's dots and the lines in
`#wt-team` under the question (option A of shot 05). Area 349.

**Working together's members and computers** (wtdevices, 9 November 2026, build 8 of the spec). Only the lead's
computer signs the roster, so everything else here is a roster the lead's install signs (`signed_out`: `n` one
higher, signed, written, sent, and the relay told through its `set_devices` when the route has one, duck-typed,
a failure there changing nothing since the key is what keeps a computer out). `remove_computer` takes one
computer off: by the lead any member's but the one he is on, never someone's only one (`last_computer`), with
`rotated` making the next epoch's key sealed to the computers left and the roster sent under the epoch before, and by
a member another of his own, sent to the team as a `devices` message (`ask_lead`, a kind added to `KINDS`, body
`{remove: [id]}` or `{add: [device]}`) and noted in team.json's `asked`. `admit` of a member's own invite from a
computer not the lead's (`admit_own`) seals the epoch's key to the new computer in the `welcome` itself (`key`,
`own: true`) beside the roster as the lead signed it, and asks the lead's computer to add it. `joined` then checks
that roster against its own lead and the inviting computer as the welcome's member, and opens the key from the
welcome. `take` (op `take`, fetched first by `come` outside the project's lock) reads the team's messages after its
own cursor (`TAKEN`, `members_after` in the device file's team), takes a newer roster (`take_roster`), and on the
lead's computer applies a `devices` message (`apply_devices`) for that member's own computers alone, never the
computer that asked and never his last. Every other kind is left to the builds that read it, and a message that
will not open is noted by `note_dropped`. `make_lead` names another member lead, signed one last time by the old
lead's computer so every install takes it from the lead it knew, and pins each participant and the GETs board that
was the lead's by default to the one who led. Each computer now carries `name`, the system's own name for it
(`computer_name`), in its public part, so People can list a member's computers. `view` answers each person's
`devices`, `removed` and `asked`. The page: Make lead and Remove on each other person's row for the lead, a
person's computers listed under the row when there are two or more with Remove this computer on all but this one,
Add a computer of mine for every member, `#wt-asked` for what waits on the lead, and `take` when the section opens.
Ops `remove` with `computer`, `lead` (held, risk 4) and `take`, the command line's `team remove --computer`, `team
lead` and `team take`, MCP's `team_lead` and `team_take`. Area 352.

**Working together's shared folder** (wtfolder, 9 November 2026, the spec's section 6). `family/folder_transport.py`,
`FolderTransport(device, folder, state, peers, refuse, team)`, registered as `folder` by `transport._folder`, which
takes the folder from `team.json`, the peers from the roster's devices, keeps this install's numbering in
`team-folder/<project>.json` beside the device file, and raises `team.refused.<code>` through `folder_refuse`. The
layout inside the chosen folder: `Idiograph <first 8 hex of the team id>/devices/<device>/messages/<seq>.sealed`
(the envelope's own bytes), `.../blobs/<blob>.sealed`, `.../seen.json` (each sender's highest unbroken seq read) and
`invites/<invite>/<time_ns>-<random>.join`. Every write is a dot-named temporary file in the same folder renamed into
place (`write_new`), and a device writes only under its own `devices/<id>/` and, under a fresh name, in an invite's
folder. The joiner finds an invite by its id under any `Idiograph *` folder, since he does not yet know the team's
id. A reader takes only `<digits>.sealed` in a folder named by a 32-hex device id, each sender's in seq order from
the one after the highest it has numbered, and stops at a gap or a file that will not open or is cut short (`complete`:
an envelope that is not whole JSON), counting it in `UNOPENED` by folder. No global number exists, so `send`
answers and `fetch` takes this install's own numbers, given in the order files are first read. `seen(project, n)`
writes `seen.json` when it changes and calls `drop`, which deletes this device's own messages every other roster
device's `seen.json` covers (none while it is alone or a peer has none). `listen` is a thread (`_Watch`) that looks
on starting, every `POLL` (15) seconds and when the wall clock runs ahead of the monotonic one by more than
`WOKE_AFTER` seconds (the computer slept), calling `on_new` when the names and sizes of the files changed. Its stop
is the Event `_halt`, as is relay_transport's `_Live`'s, never `_stop`, which is `threading.Thread`'s own method on
Python 3.11 and 3.12, so a join there would call the Event (relfix, 9 November 2026). A folder
not chosen or not there is refused (`no_folder`, `folder_missing`) and never made. `team.view` adds `folder_state`
(`none`, `missing`, `unopened` with `unopened`, or "") from whether the folder is there and `UNOPENED`, shown by
`team.js` `wtFolderSaid` under the folder (`#wt-folder-said`) and by `team show`. Choose uses `picking`, so the app's
own window opens the system's dialog on Windows too. Area 353.

**A reviewer's board sent straight in** (wtboard, 9 November 2026, build 6 of the design, the spec's `board` message,
sections 4 and 7; Adam: "for Curt to send me a PETs board directly in the app and me receive it"). `team_board.py`.
`send` (a member's own board of a participant whose owner, `roster.owners[folder]` else the lead, is someone else)
seals a `board` message, its body `ref` (8 random bytes, the answer's handle), `to` (the owner's member id),
`participant` (its folder), `label`, `timepoint`, `name`, `board` (the board whole as `themes.normalise` keeps it,
`team_board.LEFT` dropped: History, review, revise, origin and agent marks), `places` (`themes.places_print`) and
`statements` (each card's key with `project_pack.statement_print` of its words as the sender read them), and sends it
through `team.transport_for`. Refused as `alone`, `yours` or `no_board`. `take` fetches the team's mailbox after
`board_after` (kept in the device file's team, apart from any other reader's place), opens each envelope, a failure
noted by `team.note_dropped`, and for a `board` to this member runs `came_in`, which since wtreview2 (9 November
2026, the spec's sections 4, 7 and 9) only keeps it waiting: the participant by folder, then label, the entry in the
record with `held` (the board whole and the sender's statement prints) and nothing written to the participant.
`answer` with accept runs `add_board`, which does what `came_in` did before: `idiograph_routes.board_coming` as a
shared copy's board comes against the statements as they are then (by words, then key, the sender's prints
saying what was reworded since), the note `board_in_note` with the `team_board.note_head` and `team_board.note`
keys (wording 2: "Curt's board, sent 9 Nov: 4 statements as sent, 1 reworded since."), the sender's own note on the
next line, `origin` with `team` (the ref, `themes.ORIGIN_FIELDS` and `origin_of` take it in place of `file`), the
name `team_board.name` kept clear of the others, one revision of kind `team_board` ("Sent by Curt"), appended after
the boards under the case's lock with `current` untouched, and a participant with no board given it as the only board
and `current`, with no blank first board made beside it (smokefix, 9 November 2026).
A `ref` already in the record is never taken twice. An `answer` (`what` board, `of` the ref, `accept`, `reason`) to
a board this member sent marks it in the record. `answer` adds a board waiting (Add as next board, its board id as
`added`) or writes nothing to the participant (Decline, the record keeping it with `reason`, `held` dropped, and
`board_declined` in the team log), and either sends the answer back through `team_sync.post`. A waiting board is
named by `ref`, or by the participant's `workbook`, the newest of it waiting. `beside` names the board on the canvas
it would come in beside. The record is `.idiograph-team/boards.json` at the root (`sent`, `came`, each with `ref`,
participant, board id and name once added, whose, when, `answer`, "" while waiting, and `held` while it waits),
which keeps a waiting board across a restart. `view` leaves `held` out. The route is `/api/team-board` (`api_team_board`, ops `show`, `send`, `take`,
`answer`, each write under the project's lock with a `team board-<op>` History record, `take` and `answer` with a
`workbook` answering `state`, the participant's boards as `/api/themes` gives them, when one came or one was
answered), the command line's `team board-send`, `board-take`, `board-answer` and `boards`, MCP's
`team_board_send`, `team_board_take`, `team_board_answer` and `team_boards`, area 261 mapping them. `board-answer`
is `holds.HELD`, risk 1. The page: `team_board.js`, `tmbAfterLoad` from the end of `thLoad` taking in when the
participant on the PETs canvas changes or 20 seconds have passed (and every 20 seconds while the screen is open),
`tmbMenuItem` in the board menu under the board's name (Send board, there only while `can_send` and on a board of his
own). A board come in is answered on review.js's line and card (`rvwBoardHtml`, `rvwBoardAnswer`), `#tmb-line` gone
with wtreview2. Areas 351 and 343.

**A reviewer's own boards** (ownboards, 9 November 2026). A member's own boards of a participant someone else works
on are kept apart in his copy, `.idiograph-team/own-boards/<participant's folder>/<the PETs file's name>` at the
root, one file a timepoint as the PETs files are (`team_board.own_file`, set as `themes.OWN_FILE` when the routes
load, None for a participant of his own and while Working together is off). The team folder is not in a version
(`team_sync.participant_files` takes the workbook, the PETs files in `Working/` and the progress file), so his
boards never go as one and a version coming in never writes there. `themes.load` gives the owner's file with his
boards after the owner's (`with_own`), each marked `own` in memory alone, and the board on his canvas his file's
`current`. `themes.write` sends such a participant to `write_own`: his boards, and `current`, go to his file, ids
starting `o` (`OWN_ID`, `_next_id` among his, and one without it renamed on the way), and a change to an owner's
board, one taken off, or a changed `chosen` or `complete`, is the one writer's refusal (`WRITE_GUARD`), the owner's
file never written. The board ops pass the guard with `boards`: `routes.writing(path, boards=True)` for
`/api/themes-save`, `/api/themes-versions` and `/api/themes-boards`, and `workbook.case_held(book,
boards=True)` for the command line's `board` ops, which sets `workbook.BOARDS_ONLY` for the block, where
`workbook._atomic_save` and `rounds.save_progress` still run the guard (`boards_pass_check`). `summary` carries
`own`, the board menu says "Yours" after the name (`tmbOwnMark`, `.th-vown`), `board list` marks `own`, and
`team_board.send` refuses a board that is not his own (`team_board.refused.not_own`). `view` with a workbook lists
his own boards as `own`. On a board of the owner's, the board menu greys out what the guard would refuse (Rename,
the note, Mark as current, Save a revision, Delete this board), each with the refusal's words as its tooltip
(`tmbTheirsTip`, from `view`'s `own` list, landreview, 9 November 2026), and Mark PETs complete and Reopen PETs on
every board of such a participant (`tmbTheirsTip(true)`, the participant named). His first board of a participant whose
owner has none yet is saved as `v1` and written as `o1`: `thSaveOnce` takes the id the save answers with at once
(`thTakeOwnId`), in the meta, the board list, `TH.known` and the PETs mark, so the next save names it. Area 351.

**Working together's builds joined** (landwt, 9 November 2026). One loop reads every kind: `team_sync.pull`, which
the server's thread runs, takes a roster and a version as before, and hands `devices`, `board` and `answer` to
`TAKEN_HERE`: `take_devices` runs `team.apply_devices` on the lead's computer, and `take_board` runs
`team_board.came_in` or `answered` for a message to this member, each under `routes.writing` with its History line
(`team take`, `team board-take`), and `sync` answers what they took as `taken`. `team take` and `team board-take` still
read with their own counts, and taking a message twice changes nothing (a computer already on the list, a board's
`ref` already in the record). After a look `pull` calls the transport's `seen` when it has one, so the shared folder
writes `seen.json` and drops what everyone has read: the folder route goes through `team_sync`'s `send`, `fetch`,
`put_blob`, `get_blob` and `listen` like the relay. Who works on a participant is `team.owner_here`: the member the
list names, else the member who added it (team.json's `added`), else the lead, an `added` member no longer on the list
counting for nothing. `team_sync.adding` notes the new participants of an Add or a REFI-QDA import as this member's
when he is not the lead, inside `writing` before the files are made (`unadding` on a failure), so the guard lets his
writes through. A version of a participant a computer has nothing of, from a member not the lead and not named for
it, is noted as his (`claimed`), and on the lead's computer named his in the list, signed and sent. Make lead pins
each participant to `owner_here` under the old lead. Areas 349, 351, 352 and 353.

**The project's History on screen** (historyui, 3 November 2026; Adam on the first shots: not a setting, so not
in Settings). Project history on a project's card menu on Home (`homeMenuItems`, never the demo's or a card whose
folder is gone) opens `#project-history`, a tall sheet (`.ph-sheet`, as high as its list up to the window's) with
the project's name in its head, All, In the app and By an agent (`#ph-filter`), and the list (`#ph-list`)
scrolling between its rules, each day's head (Today, Yesterday, the date) over its changes, each its time, who
(`phWho`), every line and the agent's account of the request. distil.js `openProjectHistory` reads
`/api/project-history` (`api_project_history`: `root` or `path` as `/api/project` takes them, `limit`, `offset`,
`by` "app" or "agent") a page of 50 at a time, the next asked while the list's end is within a screen of sight
(`phNear`), a late answer for another filter or project passed over (`PH.ask`). The route reads as `project
history` does (`project_history.newest`, newest first, `total` the count with that `by`) and answers each record
through `project_history.for_page`: the agent's name split from its hold (`hold`, "approved" or "without", from
`holds.APPROVED` and `holds.WITHOUT`), the name and the request cleaned by `holds.agent_words`, and each line on
one line with nothing unseen (`line_shown`), its quotation marks kept. No record says "No change yet." (or none
in the app or by an agent yet, under its filter). The route is the page's half of `project history` in area 261's
parity. The app's menu bar has no Project history yet. Area 322.

**REFI-QDA projects** (21 October, the plan of that day with Adam's rulings). `qdpx.py` reads a
`.qdpx`, a zip of `project.qde` and `Sources/`, in memory with the standard library: a zip name with
`..`, a leading slash, a backslash or a drive is never read and is listed as left out, project.qde
is capped at 64 MB, a source's text at 32 MB and a recording at 4 GB, and a project.qde carrying a
document type is refused, so no entity is expanded. The element names follow the open-source
QualCoder's `refi.py`, read on 21 October, since the XSD and the specification sit behind a file
viewer no page reader opens: `Users/User`, `CodeBook/Codes/Code` (nested), `Sets/Set` with
`MemberCode` and `MemberSource` (`MemberCode` on documentation alone), `Notes/Note` with
`PlainTextContent`, `Sources` with `TextSource` (`plainTextPath`, `PlainTextSelection` with
`startPosition` and `endPosition`, its `Description` the comment, `Coding/CodeRef` and `NoteRef`),
`AudioSource` and `VideoSource` (`path`, `Transcript` with `SyncPoint`s, `position` and `timeStamp`
in milliseconds, and `TranscriptSelection` from one sync point to another), `PDFSource`,
`PictureSource`, `Cases/Case`, `Variables`, `Links` and `Graphs`. A position counts the plain text's
characters as a Python string does, line endings as the file has them.

`qdpx.passages` splits a source's text as `convert.read_plain` splits plain text, keeping where each
passage's words begin and end. `qdpx.map_source` places each selection on the passage where it
starts, cut at that passage's end and counted, and makes the passage's notes and pairs under the
choices: `codes` statements (one statement a code a passage, its quotations there the pieces of one
quote by `assemble_quote`, which merges as `static/quote.js` does), notes or leave, `comments` notes
or statements, `loose` blank (a pair with an empty statement and its quote) or leave, and `user`
one coder's alone. A code or a comment as a statement on the interviewer's or another speaker's
passage is left out and counted, a comment kept as a note there.

`server.qdpx_import` reads every source, refuses a row naming a source that is not there or is left
out, and checks the rows through `new_cases`, whose `reader` (here the mapped turns and notes, the
`.qdpx` itself as the data, which `keep_transcript` copies from its path) stands in for a dropped
file's. `qdpx_write` writes each participant as Add does (`write_case`, `add_interviews`), then
`qdpx_case`: the pairs through `put_pairs` in one save, written as `workbook.pairs_to_cells` writes
a turn's, the new workbook's description naming who made it, the import's lines under `imports` in
the progress file, the memos to `Source/<Pseudonym> - memos.txt`, never over one there, the
recording copied out of the zip into `Source/<interview>/Source/` with an offset of 0, and with
`pets` the board through `qdpx_board`, laid out by `themes_ai.lay_out` and added by
`themes.version_op`'s `propose`, which since this build takes a `name`. Every step goes into the
`back` list `unadd` reads, so a failure takes away what the import made and puts back a joined
participant's workbook and progress file.

A blank statement is a pair whose statement is empty, so the workbook holds its quote after the
statements, as a lone quote is held, and every reader takes it as before: `turn show` gives it as a
pair with an empty statement, `read_cards` makes no card of it, and the statements screen lists its
passage under Quotes to pair until the statement is written.

The import card (21 October, qdpx2) is New project's card holding a `.qdpx` alone (`NP.qdpx` in
`static/app.js`, drawn into `#np-qdpx` by `drawQd`). A drop gives the page no path, so its first
read sends the file in base64 and `qdpx_hold` keeps it in a folder of its own under the system's
temporary folder, capped at 256 MB, at most four held, the oldest taken away first, all of them at
the server's end (`atexit`). The key, the folder's name, comes back as `held`, and every read after
sends it with the card's choices and its ticked sources, whole again when a restart has dropped it
(`QDPX_GONE`). A read is `qdpx_import` with no `make`, against Add's project, New project's folder
once chosen (`qdpx_card_root`), or before then the held copy's own folder, a root of no participants.
Add's make is `/api/qdpx` with `root`; New project's is `make_project` with `qdpx`, which checks the
import before it writes, writes the project file, brings the import in outside its own write lock
(the lock is not re-entrant and `qdpx_write` takes it), adds the project, and on a failure takes
away the participants the import made with the rest. The held copy goes once made. `qdpx_view` now
gives each source its guessed `interview`, and the lines count a source with no pseudonym yet as a
participant of its own.

**Export as REFI-QDA** (8 November 2026, qdpxout). `qdpx_out.py` writes a project, or the participants
named, as a REFI-QDA 1.5 project, mirroring `qdpx.py`'s mapping so its own import reads it back the
same. `plan` reads each participant's workbook (`workbook.read_case`, a workbook open in Excel
refused) and builds plain records: each sheet a `Source` whose text is a passage a paragraph,
`[HH:MM:SS] Name: words`, the words squashed as `convert._squash` squashes them so `qdpx.passages`
finds the same passages, with `squash_map` placing each quote's pieces (`workbook.quote_turns`) in
it. A passage with no time takes the one before it, and a speaker's name the reader would not take
as a label (`convert.good_name`) is written with capitals, else as Speaker. In IPA each statement is
a code by its card's key, applied to each piece, a selection named by its whole quote (as ATLAS.ti
names a quotation) so two quotes of one code on one passage stay apart, and a statement with no
quote, or whose quote is not in the transcript, coded on its whole passage in a selection named
`qdpx.WHOLE`. `pets_tree` lays each participant's PETs out from `gets.source_board` (followed with
`themes.follow`), tops in `themes.canvas_order`, members in `themes.theme_order`, a stacked statement
after its top, then Not placed and Set aside, each PET also a set of every statement under it.
`gets_sets` makes each GET on the GETs board's current board a set of its PETs' and statements'
codes, in a project of one timepoint. In thematic analysis the codes come from the code list
(`codes.load`) and the rows, one code a name, and `themes_tree` nests them under the Themes board's
themes, each also a set. Notes are `Note` elements with `PlainTextContent`, linked from a selection
of the passage, a label's from its code. With `recordings` a sheet's recording (`audio.for_sheet`,
at most 2 GB, the standard's limit) makes the source an `AudioSource` with the text as its
`Transcript`, a sync point at each passage's start at its time plus the recording's offset and one
at each end of a selection at its passage's time. `qde` writes the XML in Project.xsd's order and
`write` the zip through a temporary file beside the target, refusing one there.
`routes.qdpx_export` is the one function the card (`/api/qdpx-export` in the window, `QDPX_PATH`'s
download in a browser), `project export-qdpx` and MCP's `project_export_qdpx` call, under the
writers' lock, reading only. The reader learned three things for the round trip: `Idiograph` as a
package name, a selection named `qdpx.WHOLE` from a project Idiograph wrote read as a statement with
no quote and a selection's name keeping two quotes of one code apart, and a set's description carried
to its PET's in the PET draft (`code_groups`, `qdpx_board`), from any programme. Area 340 validates
the package against `tests/refi-qda/Project.xsd` and runs the round trip on both demos.

The round trip made whole (9 November 2026, qdpxround). The reader keeps each code's description and
`NoteRef`s and each set's `MemberNote`s. `qdpx.set_tree` takes a set's tree from the code of its name
that cannot be coded and holds exactly its codes, so `qdpx_board` nests sub-PETs (lay_out's own
numbering, tops then each one's sub-labels in turn, carries each label's description and note), and
`qdpx.set_aside` sends the statements under a participant's Set aside code (its name in the run's
language or English, from an Idiograph package alone) to the bin. `qdpx.upper_groups`, the sets that
hold codes that cannot be coded, become a GETs draft (`routes.qdpx_gets`, `gets.propose`) in a project
of one timepoint, its cards the PETs `qdpx_board` made, by code. The export writes a GET's note as its
set's `MemberNote`. In a thematic analysis project `routes.qdpx_themes` writes each code's description
to the code list where it has none (`codes.change`, describe) and the sets as a Themes draft holding
the extracts, gathered by code, where the import used to make a PETs board for each participant.
`qdpx.offset_of` keeps a transcript's own times when its sync points differ from them by one amount,
which becomes the recording's offset, from any programme. From an Idiograph package a passage's
statements keep the selections' order in the file, and a source's interview is its name after its
case's. Area 340's third part trips an invented project of two timepoints.
**Names replaced as a transcript comes in** (namesrule, 8 November 2026, the first of three builds, Adam's picks of that
day). `family/names.py` is the whole of it: the store, the rules and a key file's read. A project's list is
`{"entries": [{"real": [spellings], "to", "for", "case"}]}` in `idiograph-names.json` (`names.FILE`) at the project's root
beside the project file, mode 600, written through a temporary file, an empty list taking the file away (namesui, Adam's
pick of 8 November about 22:50: the list lives in the project's folder and moves with it, named for the app and for
what it holds so a folder handed on by hand shows it). namesrule kept it in the app's data folder as
`names/<key>.json` under `names_key` in the project file: `names.load_at` moves such a list into the project's folder
the first time it is read, deleting the old file and the key (`names.OVERRIDE` or `IDIOGRAPH_NAMES_DIR` give the suite
another old folder). The list is in no workbook, progress file, History line, the agent log, a shared copy
(`project_pack.LEFT_OUT`) or an export, and the app copies it nowhere. The rules: a pattern per list and
participant (`compile_list`), a whole word by Unicode letters and digits on either side (an underscore ends a word),
case ignored unless the entry's `case`, spellings with any run of spaces matching, initials (`T.M.`) matching with or
without dots and the space between and always by case, the longest spelling first in one pass, so no replacement is
replaced again, and an entry `for` a participant applying to that participant's pseudonym alone. `Run` carries one Add:
each entry's finds counted across the files in order (`nth`), the skips (`read_skip`, `3:1`, `[3, 1]` or
`{"entry", "nth"}`), every find with its words and place, and `counts()`, the same with no name in it, which is all an
agent is told. A quote takes the skips of its passage's text (`mirror`) so a highlight is still found.

`routes.pseudo_run` makes a `Run` from the project's list and a call's `skip`. `new_cases` applies it as each file is
read, for Add and New project, every format `convert.read_data` reads: the file's name (not its extension), the
interview's name, each distinct speaker's name once, every passage and every note (`pseudo_read`), the roles moving
to the speakers' new names. A file with a replaced name is kept in `Source/<interview>/` as `P<n>-<interview>.txt`
written from the replaced turns (`names.render`, `copy_suffix`), the original not kept, so no copy holds a name the rules
found. `qdpx_import` replaces the package's code names, sets and sources' names (`pseudo_package`), each source's turns,
notes, comment statements and quotes as it is mapped (`pseudo_mapped`, a code's statement already named by its code's
replaced name) and the memos as they are written, passes `new_cases` an empty `Run`, and keeps the package out of Source,
writing the replaced text in its place. `import_make` replaces the turns of an import into a case. The answers carry
`names` (`pseudo_answer`): the counts, a line and one for each entry, and for the app's own call (`names_preview`) every
find with its words. `/api/names` (`api_names`) is the list: `list`, `set`, `remove`, `check`, `read-key` and `key-file`,
a call with a `tool` (the command line and MCP) told entry numbers and counts and refused `set`, `read-key` and
`key-file`. It is post-only and window-only. The command line's `names list`, `check` and `remove` and MCP's
`names_list`, `names_check` and `names_remove` call it, and `project add-transcripts` and `qdpx` take `--skip`. Area 345.

The screens (namesui, 8 November 2026, drawn in pseudodraw and approved that evening). A row of Add transcripts and New
project has a Real name beside its Pseudonym, sent as the file's `real`: `names.with_real_names` makes an entry for that
participant alone, the name and its first word when it has two, unless the list holds them already, and `pseudo_keep`
writes the list once the Add or the new project is written. An agent's call with a `real` is refused. The card asks
`/api/names` op `preview` a moment after each change (`nmSoon`), with the rows as the Add will send them: `pseudo_preview`
runs every file through a `Run` the way `new_cases` does, so each find's `nth` is the Add's, and answers each file's
finds, with the words either side (`before`, `after`, `names.CONTEXT`), its first passages and its speakers as segments
(`pseudo_segments`), and the list. The page tints each replacement (`.nm-swap`, the name it replaced as its tooltip),
keeps each find he unticks on the Review card (`nmReviewOpen`) by its place in its file, and sends them as `skip` with
the Add after one last preview. Names to replace (`nmListOpen`) is the list as a table, saved with `set` as each field
changes, from the row's Names line in Add and from Project settings. Its Check transcripts already in is op `check`:
`pseudo_check` runs every participant's annotated workbook through `workbook.names_in_book` with nothing saved, each
row's speaker, transcript, then each statement, quote, exploratory note and interviewer's note entry by entry. Review
and replace is op `replace` with the skips: `pseudo_replace` runs the same order, so the numbers agree, and for each
workbook with a find to replace keeps it and its raw source in `_Archive` (`archive_copy`, label `pre-names`), writes
the rows, has the boards and the GETs follow (`follow_replace`, as a find and replace does), runs the raw source with
the same finds left (`mirror`), and brings `Source/`'s copies into line (`pseudo_copies`: a text copy replaced where it
stands, any other kept as `.txt` from its read), the old copy into `_Archive` first. One History record, counts only.
`project_pack.left_out` leaves out anything named `(pre-names `, since those copies keep the real names. The command
line's `names replace` and MCP's `names_replace` call the same op, counts only. Area 345.

**A Word table of transcript and notes** (19 October, a tester's Figure 1). `convert.read_data` tries
`read_docx_table` on a `.docx` first. It takes the body's own tables of two columns or more, those as
wide as the first, and reads them only when their words outnumber the words outside them, so a
transcript with a small table of details is read a paragraph a line as before. `_rows_of` gives each
row its grid's cells, a spanning cell its first column's, each the lines of its paragraphs. A first
row whose cells name a role by `_head_role`, the transcript by `HEADERS["text"]` or "transcript", the
statements by `STATEMENT_STEMS`, the notes by `NOTE_STEMS` (since 20 October also thought, memo,
reflect and reflexi, so Thoughts, Memos and Reflections are guessed as notes, in a spreadsheet too), and the speaker and time as a CSV's are,
is the heading row, and a later row the same is passed over. With no heading row, a column whose
first lines are mostly times (`_timed`) is the time, then the transcript is the column whose rows open
with most speaker labels, then whose lines run longest, then a column of a few names that each pass
`good_name` (`_names`) is the speaker, and the fullest column left is the notes. A column with a
heading that names nothing is left out, and so is the third column with no heading. The guess goes
through `choose` with the card's choice, so a choice takes its place (see Column matching below). The
transcript's first line goes through `label_of`
and `_named` as plain text's lines do, else `_lead_time`, a row with no label carrying on the speaker
before it. A notes or statements line with no letter or digit, the dot a Word table keeps to hold a
note's level, is dropped. A row with no words adds its notes to the turn before it. The read carries
`notes`, a `{"en", "es"}` of lines joined by line breaks for each turn, and `left`, a line each for
what is left out, which `convert.brings` makes the card's `brings` line through `turns_view`. `_fill`
writes them into the raw source in columns headed Notes and Statements, which no role test in
`workbook.ROLE_TESTS` takes, so the source stays raw, and the notes on turns written under the name
Settings gives the interviewer in Interviewer notes. `server.case_sheet` passes that name for New
project and Add transcripts when he was chosen, and `api_import` for the import card. `_annotated_sheet`
finds them by `workbook.RAW_EXTRAS` and the `note` role and writes each through `lines_to_field`, so a
line is an entry, into Experiential statements, Exploratory notes and a new Interviewer notes column at
G. A hand-made raw source with a column headed Notes or Statements now brings it in the same way.

**A Quote column** (ayabuild12, 9 November 2026, the Ayahuasca plan's build 1). `convert.ROLES` gains
`kq`, named Quote, guessed by `_head_role` from a heading in `QUOTE_KEYS` or ending in quote or quotes, and
`EXTRAS` (`en`, `es`, `kq`) is what `table_turns` and `read_docx_table` carry beside each turn. `_fill`
writes a turn's quotes into a raw source's `Quote lines` column (`RAW_QUOTES`), never Quote or Quotes,
which `ROLE_TESTS` would read as an annotated workbook's. `workbook.RAW_EXTRAS` maps it to `kq`, and
`_annotated_sheet` writes the statements and the quotes through `source_pairs`, `pair_entries` then
`pairs_to_cells`, so the first quote goes with the first statement, a statement past the last quote
has "(no quote)" and a quote past the last statement is kept after them, which `unpaired` lists under
Quotes to pair. A quote is marked in the words on reading as every quote is (`quote_reach`), so one not
word for word stays in the cell, unmarked. `workbook.quote_census` counts `paired`, `unpaired`,
`no_quote` and `unmarked` (a quote `quote_reach` cannot find in its own passage), which
`server.quote_counts` gives `turns_view` as `quotes`, `add_plan` per interview, `add_record` for
History and the command line's `import` dry run, said by `quote_lines`. `names.render` keeps a quote
under its passage in the replaced copy. An Excel file is read at a sheet by name: `table_of_xlsx(path,
name, sheet, info)` refuses a sheet the file has not got in one line (`server.no_sheet_named`) and fills
`info` with `sheets` and the `sheet` read, which `read_data` answers. `read_entry`, New project's `read`
and `import_asks` take `sheet`, the command line's `import --sheet` and `add-transcripts`' `"sheet"`,
MCP's `sheet` on both. New project's and Add transcripts' rows show a Sheet chooser (`data-np="sheet"`)
for a file of two sheets or more, the sheets kept on the row across a read that fails, a change reading
the file again with its columns guessed afresh, and `npFilesSent` sends it.

**Tables of PETs and LPETs** (ayabuild34, 9 November 2026, the Ayahuasca plan's builds 3 and 4).
`table_import.py` reads and matches, and writes nothing. `read_table` reads a CSV through
`convert.table_of_csv` and an Excel file at a sheet through `table_of_xlsx`. `pet_rows` finds the
columns by `PET_HEADS`, carries a PET's and a sub-theme's title down, and reads Location by `at_seconds`
(an Excel fraction of a day too). `match_pets` takes the passages of the timepoint's sheets as
`cli.turns_of` reads them: a statement of the same words (`key`, case and marks set aside), the one
nearest the Location first, else the best `ratio` (difflib's) of `FUZZY` or more among the statements of
the passage within `SLACK` seconds of the Location, then of the passages `quote_in` finds the quote in,
cut at an ellipsis or an insert, else the nearest of the participant's own statements there at `CLOSE` or
more (`rewritten`), else `added` or `skipped`. A key taken by an earlier row makes a later one a
`duplicate` with `of`. `cli.cmd_board_import` writes each passage `passage_writes` names through
`cli.turn_write` with `pairs` keyed to their lines (so `themes.passage_written` carries every board's
cards and the edit lands in the progress file's `edits`), a new statement's key its passage's next line,
then hands `board_spec` to `cli.make_board`, `board new`'s body split out (`wanted` names the board
through `themes.board_name`, given to `version_op`'s `propose` as `name`, and `fresh` lays it out
afresh). `cli.cmd_gets_import` runs in `lpets_scope` (`scope_of`): `lpet_rows` finds each timepoint's
column by its key or label (`lpet_columns`), `pets_at` reads each timepoint's top PETs and every
statement under them from the LPETs file as `gets.assemble` would leave it, `propose` matches the cells'
quotes (`CELL_QUOTE`) and lines, then the board is made by `gets.version_op`'s `new` and filled by
`cmd_gets_apply` with `make` and `describe`, and each LPET's note, `note_of`'s paragraphs, is written
after on the board under `locks.root`, since `themes_ai.clean_note` keeps one paragraph. MCP's
`board_import` and `gets_import` hand `file` over as `--from`. `table_import` is in `build_mac`'s modules.

**A statement brought onto a board** (lpetadd, 11 November 2026, from a data run on a participant's LPETs, where
`gets apply` could only move cards already there). `cli.cmd_gets_apply` takes `{"op": "bring_in", ...}`
(`cli.BRING_IN`, `bring` too), what the Participants panel's drag does (`gtCardFrom`, `gtPullDrop`).
`cli.bring_ins` reads each against the board as `gets.normal` holds it and the study's copies: the card's key
given whole, or made from `statement`, an id read through `themes.read_cards` at the timepoint as `statements`
numbers them or a key, and the entry `cli.bring_in_entry` finds, the timepoint on LPETs through
`gets.timepoint_of` over `gets.NAMES`, the participant on GETs and LGETs through `Project.case`, and on LGETs a
timepoint over `gets.LGETS` for an id. The line is `gets.statement_line`, the copy's line the page's row reads,
and `to` is a label's id, the ref of a make before it, or a title one label has. Every refusal is gathered and
the change refused whole. `gets.bring_in` then lays the cards in before anything else runs, through `lay_in` as
`take_in` lays a new case's, each with its words, which `gets.normal` keeps on a statement's card as it keeps
those the drag's save sends to `/api/gets-save` (`thBody`), so the two clients leave the same board but for
where the card stands (area 235 compares them). A `bring_in` with `to` becomes a `move` at its place among the
applier's operations, so a ref resolves, and is left out of `applied` and `change_line`. A change that brings
one into a label lands with `land_kept(..., strict=True, statements_in=True)`, under what the label holds, as
`cmd_board_apply` lands a statement moved into a PET, and every other `gets apply` lands as before. One
brought in to no label is a change of its own, never "Nothing to change". `bring_in_said` says each, the unit
by `bring_in_unit`, LPET, LGET or GET (a theme in a thematic analysis project), where `codes.follow_moved` takes
it as a card brought in, its code's other rows following. The parity check needs nothing new, `/api/gets-save`
being `gets apply` already. Area 235.

**A label keeps what a change does not speak of** (domainkeep, 11 November 2026, from a data run whose
`bring_in` into an LPET took every LPET's domain off four participants' boards, titles, notes, descriptions and
the rows' states, key quotes and bold left as they were). `cli.cmd_gets_apply` and `cmd_board_apply` hand the
applier (`themes_ai.revise_ops`) a plain board, each label its id, title, note, description and members, and a
change that alters what holds what lands through `themes.land_kept` or `themes.land`, which built every label
afresh from those fields and the old place, so a field the applier never sees, the LPET's `domain` (trajbuild2),
went from every label on the board on any `gets apply` but one that leaves the labels as they were (an order, an
arrange, a `bring_in` with no `to`). It was so from the domain's first day, 10 November, on the command line and
MCP alike. The app's own saves never lost it: `thBody` sends each label whole (`thLabelOut`, descloss), the drag
from the Participants panel, a move, a rename, a merge and undo among them, and area 235 drives them in node and
in a browser. Now `themes.label_kept(group, gid)` is the one place that says what a label carries, which
`normalise` keeps, and `themes.label_landed(old, said, made)` starts each landed label from the board's own label
of its id, whole, the change's title, note, description and members (`CHANGE_SAYS`) over it, so the domain and any
field a label comes to carry stays. A label the change made, `revised["made"]` (each apply passes `info["made"]`),
takes only the place of a label gone that had its id, since `cli.as_gets` numbers a new GET past the GETs left,
which can be one the change took away. On a page's save `themes.fields_kept(kept, sent, held)`, in `themes.save`
and `gets.save` in place of `descriptions_kept`, gives each label every field of the file's label of that id the
page sent no key for at all, except those a page always says (`PAGE_SAYS`: id, title, members, place and the
note, which the page leaves out for none), so a page that does not know a field never takes it away, and a key
sent, `""` among them, is the page's word. Area 235.

**Column matching** (19 October, Adam: "let them check that it's correctly detected the columns").
A Word table, a CSV and an Excel file are read the same way: a guess of a column for each of
`convert.ROLES`, `name`, `ts`, `text`, `en`, `es` and since 9 November `kq`, then `convert.choose(guess, given, width)`.
`guess_columns` takes a spreadsheet's notes and statements columns by `_head_role` before the other
roles, so a Notes heading is never taken for the words, and in a sheet with no headings the fullest
column left that is not times or numbers is the notes. `given` is the card's list of a role a column,
"" for Leave out, or a `{role: index}` as a page or an agent from before sends it, whose roles not
named keep the guess and give up a column a named role takes. `choose` answers the role to column
(`mapping`), the role of each column (`roles`) and `said`, "Two columns are set to <role>. Choose
one." or `NO_TRANSCRIPT`, which holds Make back: `api_import`'s make and `new_cases` refuse on it
(New project's line names the file), and two columns on one role are read by the first meanwhile, so
the preview still shows. `table_turns` reads a spreadsheet's rows as `read_table` does, with a
`{"en", "es"}` beside each turn as a Word table's. `left_out` makes the line for each column with
something in it that no role takes, by its heading, or by its place when the heading is one
`_with_headers` gave (`_GIVEN`). `turns_view` sends `roles`, `shown`, the roles chosen in
`ROLES`'s order, with Speaker and Time too when a Word table's rows name their speakers and times
in the words, the preview's columns, and each preview turn's `en` and `es`, each cut by
`preview_words` at the last whole word within 240 characters. The page's `importMapHtml` draws a
chooser a column on the import card and on New project's rows, and `importPreviewHtml` the preview,
a table of a column a role inside `.import-preview`, which scrolls sideways on its own. Plain text,
VTT and SRT keep the three-column preview of before.

**The progress file.** `<case>/Working/<stem>.progress.json`, written by `rounds.py`. `version` is 1.
`rows` holds each participant turn's state by its sheet and row, `"Initial:12": "has-content"`,
either `has-content` or `reviewed-empty`, and a turn with no entry is unvisited. `rounds` holds each
round by its number across the case, `{"seconds", "completed"}`, the seconds of work measured on it
and the time it closed, or null. `days` holds the rounds closed on each date,
`{"2026-10-03": {"rounds": 2}}`, which the daily target and the streak count. `last` is the last
turn saved, `{"sheet", "row"}`, and `last_commit_at` and `last_commit_round` are the time of the
last save, in seconds, and its round, which the pace is measured from. `trims` holds a record of
every trim: its `id`, `sheet`, `direction`, `row`, `first`, `last`, `count`, `timecode`, `head`,
`backup`, `when` and `undone`, with `sidecar`, what the file said about the rows cut. `edits` holds
a record of every turn corrected in place: `sheet`, `row`, `old`, `new` and `when`, with `old_time`
and `new_time` when the timecode changed too, and `cut` once a trim has taken its row. A row a find
and replace changed is recorded the same way, with `batch`, the one id of the press that changed
it, `find`, `replace`, `count`, the occurrences replaced in it, `crux`, where a highlight it dropped
sat, as `[start, end, font]`, and `undone` with `undone_when` or `redone_when` once it is undone or
done again.
`assignments` holds a record of every assignment: `id`, `sheet`, `row`, `kind`, `whole`, `start`,
`end`, `from`, `to`, `before`, `after`, `block`, `shift`, `holder`, `backup`, `when`, `undone` and
`sidecar`. `complete` is `{"at": "<iso time>"}` once the phase is marked complete, and `flags`
stays in a file written before 3 October 2026. In a project of two or more timepoints (20 October)
`timepoints` places each sheet at T2 or later by its name, `{"Midsummer": 2}`, and `complete_timepoints`
holds each later timepoint's Statements complete, `{"2": {"at": "<iso time>"}}`, T1's being
`complete` (see Timepoints, below). A key an older file lacks loads empty. A turn an AI
agent wrote through the command line is an entry of `edits` too, with `by` of `agent`, `tool`,
`request`, his request in his words, `when`, `before` and `after`, the fields it changed as lists
of lines, and `backup`, the copy in `_Archive`. It sets the turn's state in `rows` and never
`last`, his place in the case.

**The themes file.** `<case>/Working/<stem>.themes.json`, written by `themes.py` and set out in
full under Autosave and the file in the [manual](manual.md). Its top level is `schema`, 2, `case`,
the case by its pseudonym, `workbook`, its file name, `created`, `updated`, `current`, the board on
the canvas, `chosen`, the Current board when one is marked, `complete`, `{"at", "board", "name"}`
once the PETs are marked complete (see [docs/manual.md](manual.md), The Current board), and
`boards`. A board carries `id`,
`name`, `note`, `created`, `updated`, `cards` by key with each card's place and text, `groups`
with each label's members, place and note, `discarded`, `picks`, `notes`, its sticky notes,
`quoted`, and `cut`, `ai`, `review` and `revise` when it has them, then `history`, its revisions,
each with its `state`, and one the app named with its `kind` and `slots` (the text layer, below). `review` and
`revise`, a board's AI review rounds and revise thread from before 11 November 2026 (aiout), are carried as the
file holds them and never read (`themes.FROM_BEFORE`): `normalise` passes them through untouched, a save keeps
the file's since the page sends neither, a trim or a rekey leaves them as they were, and a duplicate carries
neither. A revision's `state` holds neither. `stacks` (19 October) is each top's
statements stacked under it, `{"Initial:12:0": ["Initial:13:0"]}`, kept by `themes.stacks_kept`: a
stacked statement is in no group and not in `discarded`, under one top, never a top, and a top stacked
under another brings its own stack, so a stack is one level deep. It is in a revision's `state`
(`STATE_KEYS`), followed through `follow` with the keys, kept by a save from a page that sends none,
and left off a board with none. The layout and every loose list read it through `themes.off_canvas`,
and a pick on a stacked statement's quote stays (`with_stacked`). The page draws a top with paper
edges and its count, `thStackEdges` giving one edge for each statement under it up to four (`TH_EDGES_MAX`,
the classes `.edges-1` to `.edges-4`) and past four `.edges-more` with `.th-edgemore`, a small plus on the
corner where the edges end (19 October, later), opens a stack in place as a view, `TH.opened`, the cards below moved down by
`thStackRoom` and recorded in `TH.shifts`, which `thUnshifted` takes back for every save and step of
undo, so an open stack never reaches the file. Quotes on cards (19 October) take their room the
same way: `thMeasure` keeps each card's whole height in `TH.qfull` and its `.th-kq`'s share with its
margin in `TH.qextra`, and `thStacksRoom` runs `thRoomMake`, which stands each quoted card at its height
without the quote and grows a row at a time down the board, cards sharing a place with tops within
`TH_ROW`, `thStackRoom` taking a list of regions each with its own `d` and moving what stands below by
the most of them, then the stacks shown open as before. `TH.roomShown` keeps where everything showed,
the board's `cards` object and `thRoomSign`, the quotes' shares and the stacks open: a card, label or
note an act moved since, weighed in the same room, takes its share of the room back off its place in the
file (`thRoomMoved`, up to four rounds), so it shows where it was let go and the file keeps it as it
stands with the quotes off. A board read afresh or put back by undo has a new `cards` object, and its
places are the file's. Since 23 October (quotejump, a tester: cards jumped with the quotes shown) `thRoomSign` holds the stacks open alone: it held `TH.qextra`, whose keys come in the order the cards are drawn, and a card picked up is drawn last, so the first act after an open, and a drop bringing a quoted card onto the canvas, took every place it moved, room and all, as the file's. `thRoomFollow`, run by `thPlace` when no drag is under way, makes the room again for whatever moved since it was made (a settle, the room made on an open, a note growing as he types), so the file never keeps a place the room showed. `thInFile(fn)` runs a settle with the board where the file keeps it, the room taken back off, every quoted card at `qfull - qextra` and every top at `baseH`, and `TH.roomShown` null, then makes the room again: `thDone`'s settle with `thBaseSize` against `thFileBoxes(before)`, the labels and frames of its snapshot laid out at those sizes, and `thMakeRoom` on an open and once the type has loaded, and the direct settles of `thNewEmpty`, `thStatementWrite`, a new note, a note's words and the table's join, whose `was` is `thFileBoxes()`. So a settle moves in the file just what it moves with the quotes off, and the room's own moves never count as a frame that grew. `thRoomOn()` says whether the view makes any room, and with none each runs as before. `thMeasure` ends by running `thStacksRoom`, so every measure makes the room as `thRender` does: `document.fonts.ready`, `thFace` back to the canvas (and the open's `thFaceRestore`), and the title's and the note's editors, so the quotes' room follows the loaded type and an open stack's top keeps its height (the loose end of 19 October, closed 26 October by stacktop: a measure followed only by `thPlace` left the top at its own height and its label's frame ending above the stack until the next render). `thMeasure` clears `TH.baseH` and measures each top at its own height, and `thStacksRoom` makes the room from there. Its last round keeps its room. Area 259. Since 30 October (subgap2, Adam's report on a PET whose third sub-PET stood about 190 pixels under the two side by side above it and would go no closer) `thRoomMake` passes `thStackRoom` a `track` from `thRoomTrack`: the foot of every card and label's frame before any room (`feet`, by `card:<key>` and `group:<id>`) and how far each card, label and note has moved down since (`moved`). Each room carries its owner's id and `need`, how far the owner's foot has come down since the room began, and `thRoomBy` moves what stands below it by `need` less what it has moved already, never less than keeps its top under the owner's new foot. Each quoted row and each open stack is a call of its own, and before, what stood below two that grew in turn moved by the first one's growth and then the second's, their sum, so it showed lower than the file has it by the smaller. A drag's rest a margin from them in the view (`thNearRest`) then landed nearer than the margin in the file, where `thDone`'s settle with `stay` sent the two up out of its way, and the room made again showed the same gap, every try. A single chain moves as it did, by each room's depth. A board saved with the fault has nothing wrong in its file and shows right on open. A known gap remains: under two of which the one whose foot stands higher in the file grew more, the sub-PET shows that growth as room under the other too, and a drag closing it sends the other up the board as far as the file needs, once. Area 302. Since 31 October (agentoverlap, Adam on 0.9.15 with the quotes Full: an agent changed the board, he took the change, and the card it changed stood over the one under it until he dragged it) the room made once a board is measured takes every pair. An agent's `turn write` gave a card longer words on every board and made no room, so it stood taller over the card under it in the file, and `thStackRoom` moves only what stands below a quoted card's foot (`b.y >= room.y - 1`), so its quote's room ran under that card too, while `thMakeRoom`, run by `thLoad` through `thInFile` on an open, on Take the changes (`thOutsideTake`), on a change from another window (`thOwnLoad`), on Reload and once the type has loaded, made room only for a pair with a label in it. Now two cards or notes settle as a drag's drop settles them: `thReadsFirst` (by `thReadOrder`) names the one that reads first, which leads through `thSettle` with `stay`, and the other is pushed clear of it by the least distance, pushing on what it meets, a frame that grew pushing its own neighbours, all where the file keeps the board, so the room for the quotes is made again from a board with nothing over anything at every setting. A pair with a label in it is as before. It writes nothing: the places it gives go to the file with his next act on the board, as the room made on an open always has. The server settles each agent's change by the same rule with its own sizes: `themes.settle_change(before, after)` takes what the change touched, each card, note and label whose box (`themes.canvas_boxes`, a statement waiting in Not placed off the canvas as `thOnCanvas` leaves it) moved, grew or came onto the canvas, as leading, the one that reads first firmest (`FIRM_LEADS`), and pushes each neighbour nearer than the margin by more than `SETTLE_SLACK` (2, the pixel or so the server's sizes run over the page's) clear of what is firmer by `free_offset`, deepest labels first, a label whose frame so grew firm in turn (`FIRM_GREW`), what a push moved after it (`FIRM_PUSHED`), for `SETTLE_PASSES` passes, then `sync_labels`. `cli.cmd_board_apply` runs it on the board every operation left, `passage_written` on each board `turn write` changes, `cards_reworded` on each board Find and replace changes, and `statement_edited` on each board an edit on the canvas reaches, whose page takes the board's version from the answer as before. `take_out`, an unstack, no longer counts a statement waiting in Not placed among what the card it takes out goes down past, as `thBelowStack` never has. Before it, 370 random operations of `board apply` on a copy of the demo's Rowan left an order of the PETs or an unstack with a frame over a neighbour, or a card in no PET nearer than the margin to one, seven times, and 500 after it none. Area 309. Close pairs (20 October): `not_same` is the pairs marked Not the same, each two
keys in transcript order (`themes.pair_of`, `not_same_kept`), in a revision's `state` (`STATE_KEYS`,
`STATE_OPTIONAL`), followed with the keys by `follow` and moved with rows by `_moved` (which since this
build moves `stacks` too), kept by a save from a page that sends none and left off a board with none.
`themes.close_pairs` finds the pairs from a board and `read_cards`, the same rule as the page's
`thClosePairs`: members of one group that are cards on the canvas, one sheet, times within the gap or rows
within `gap // ROW_SECONDS`. The settings are `close_pairs` and `close_gap` (`themes.close_gap`, one of
`CLOSE_GAPS`). `cli.close_of` gives `board show` its `close`, `--close` any whole seconds to an hour, and
`run_stacks` takes `not_same` and `show_again`. The page draws the lines in `#th-links`, an SVG between
the frames and the cards, and their end dots in `#th-linkends` over the cards (`thLinksDraw`, `thLinkPath`,
from `thPlace`, none during a drag, a straight drop from foot to top where one card stands over the other and none stands between, and both layers inside the clip `#th-more-clip`, holed by `thMoreHoles` round each selected card's top right corner, `TH_MORE_CLEAR` across, so no line or dot meets its ⋯), each pair a `g.th-pair` lit by `thLinksLit` (`hot` under the
pointer, `on` selected, `cur` stepped to). `TH.pairs` is what the canvas last drew, `TH.pairAt` the
stepping's pair by its keys, `TH.pmenu` the line's menu (`thPairMenuOpen`), `#th-cpmenu` the gap's,
`TH.pairable` a server that sends `not_same`. `thPanelDraw` reads two selected cards that are a pair as
the pair (`thPairSelected`, `thPairPanelHtml`). `thCorners` takes a fifth step, `th-status-tiny`, hiding
the ‹ › and the zoom's minus and plus. `thFitRoom` is the part of the stage `thFit`, `thFitTo` and `thPairShow` fill: the stage less 56px and less the palette and the bin, each taking the side it costs least. Where a board comes on (boardview, 30 October 2026, Adam: another board "opens up in blank space"): an open fits it, `thLoad(data, { fit: true })` and `thFit` again once the sidebar is restored, as since 1 October, and the way back from a passage or a search then puts its kept view back (`thBackFromPassage`). A switch (`thSwitch`) and the board after a delete (`thDeleteGo`) call `thLoad(data)` with no fit, which from 2 October to 30 October kept the view of the board left, so the next board's cards were in view only where the two stood in one place, as a duplicate's do. `thLoad` now notes the board on the canvas before it, keeps its view in `TH.views` by id while it is still a board (a deleted one's is not kept), and for another board coming on with no fit calls `thLand`: the view as it stands when it shows any of the board's cards (`thShows`, the middle of a card, a label's title or a note inside `thFitRoom`), so a duplicate opens where its original was and two boards laid out alike are compared in one place, else the board's own view from `TH.views` when that shows any, else `thFit`. `TH.views` is reset with the undo stacks when another canvas opens (`TH.stacksPath`), and nothing of it is saved. `thUsedBoxes` is what `thFit` fits and `thShows` weighs: the cards drawn, the labels' titles and the notes. `thFit` hands `thFitTo` its `corner`, so a board too wide or tall to show whole even at `TH_ZOOM_MIN` starts at the room's left or top edge, its top left in view, where centring showed its middle, which can be blank. An empty board still shows the origin in the middle at 100%. Area 305. `thStackClear` glides the view up after a stack opens
until its last card clears the bin and the zoom, and `thTip` hides the Alt tip while `TH.stackAt` is
set, a drop there stacking. A schema 1 file, its boards under `versions`, is read as schema 2 and written as
schema 2 on its next save. `made` and `changed` say what an AI agent did to a board through the
command line, the board it made and its last change, each `{"by": "agent", "tool", "request",
"at"}`, and the revision kept before an agent's change carries `made` too. A board `board new` makes
keeps `from` in `made` as well, by `cli.source_of`, the board on the canvas or all statements. `made` keeps `hash`, the board's
state hash as `themes.made_state` takes it when it was made, and `edited`, the time of his first save
whose state differs from it (see `themes.edited_mark`). `themes.made_said` reads the board menu's
"with AI" from it, or for an agent's board from before it from its note, and `themes.summary` carries that as
`with_ai`. The mark a New AI board left, `{"by": "ai", ...}`, `made_mark` reads as nothing since 11 November
2026, so such a board is an ordinary one and loses the mark on its next save. Every new board is named by `themes.board_name`, `Board N`, the next free number. The
page never sends either key, so a save keeps the file's, and a duplicate carries neither. A save from a page whose
`updated` is older than the board's `changed` is refused, its canvas kept in the board's history
first as "The canvas when a conversation changed this board", so neither the change nor his work is
lost.

**An agent's change keeps the order it does not name** (agentorder, 10 November 2026, from the Gravity
session: across one afternoon's revisions an agent's `board apply` changed the reading order of PETs,
sub-PETs and statements it never named, and the PETs table and the PDF, which read order from where things
stand, followed). The revisions named "The canvas when a conversation changed this board" were only where
the shifts showed, the page's refused saves kept beside each change. There were two causes. On the server,
a change that put a statement into a label elsewhere answered None from `land_kept` with `strict` and was
landed by `themes.land`, which lays the whole PET it touched out afresh as a round blob, so its sub-PETs
and statements took new rows and read in another order, and the room `land_kept`, `settle_change` and
`reorder` then made moved things by the least distance, which can carry one past a neighbour's row. On
the page, a board whose type measures taller than the server's sizes (the Mac's at Large) made room on
taking the change (`thMakeRoom`, through `thOutsideTake` or Reload), and a card that gave way to a frame
went to its nearest free spot, past its neighbour, an order his next act saved. Now `cmd_board_apply`
lands with `land_kept(..., strict=True, statements_in=True)`, a statement put into a label elsewhere packed
under what that label holds as a label is, so it reads last there and its new neighbours keep their
places, `land` kept for a new label over more than one label's things. After `settle_change`,
`themes.keep_order(followed, landed, wanted, named)` sets each place back to `themes.order_kept`'s order
through `reorder`, the deepest first and the PETs last, for up to four rounds: what was there reads as
before in the places those of it read in now, what came up from a label inside or out of a stack there
(and a label new to the board) keeps the place it landed in, and what came in from elsewhere reads last,
in the order the operations name it (`cli.named_in`). A place an `order` set takes that order, and one an
`arrange`, `align` or `spread` touched (`cli.laid_places`) the order it left. On the page `thMakeRoom`
compares every place's order (`thOrders`) before and after its room (`thRoomPairs`): when any reads
otherwise it puts the board back (`thBoardHeld`, `thBoardBack`) and makes the room again with every
pair led by the one that reads first, as two cards always were, and when that too reads otherwise it
leaves the board as it was. `gets apply` lands as before. Area 371.

**Timepoints** (20 October, the tpmodel build, the first of three, after Farr and Nizza 2019). A
participant is the unit: one case, one workbook, at every timepoint. The model, in five parts:

1. The project's timepoints are `timepoints` in the project file, a list in order of `{"label",
   "description"}`, written by `server.write_timepoints` only with two or more, the key taken away
   for one. `timepoints_of` reads it, always at least `[{"n": 1, "label": "T1", "description": ""}]`,
   and `read_project` sends it. A timepoint is known by its place, `n`, never its label, so a
   label renamed moves no data.
2. A timepoint is a set of the participant's sheets. The progress file's `timepoints` places each
   sheet at T2 or later by its name (`rounds.sheet_timepoints`, `tag_sheets`), a sheet not named
   at T1, so an interview in two parts stays two sheets of one timepoint and an interview at T2 is
   new sheets at the end of the same workbook. Why the progress file: the workbook is his Excel file,
   where a renamed sheet or a hidden property would be seen or lost. The progress file is Idiograph's
   own record of those sheets, already keyed by sheet name, and Rename, the archive copies and every
   reader already carry it. `load_progress` keeps a key it does not know and `set_complete` writes
   only its own, so no writer from before drops the tags.
3. Statements complete is per timepoint, `rounds.complete_at_timepoint`: T1's is `complete`, as it
   always was, so a file from before has its mark at T1, and a later one is in `complete_timepoints`.
4. A project of one timepoint writes nothing new and answers nothing new: `longitudinal` is false,
   `timepoints_view` answers None, a card and a summary carry no `timepoints`, and the import card's
   `timepoints` is empty.
5. A workbook from before reads unchanged: no tag reads as T1 and no `complete_timepoints` as no
   later mark.

Lowering the number is refused while a timepoint it would take away holds data, a sheet placed there
or its mark (`timepoint_holders`, over `timepoint_books`, every annotated workbook and the workbook a
raw source becomes), naming the participants. `by_timepoint` gives a participant's timepoints, each
`{"n", "label", "description", "sheets", "done", "total", "complete", "state"}`, `state` `none`,
`progress` or `complete`, from the passage states by `sheet:row`: `summary_of` puts it on every
summary the page draws its bar from (`/api/open`, `/api/commit`, `/api/round-complete`,
`/api/complete`) and `card_timepoints` on the home screen's card, kept with `turns_of`'s counts
against the workbook's, the progress file's and the project's timepoints' marks. Where a timepoint is
chosen: New project's and Add transcripts' rows send `timepoint` (`new_cases`, `place_timepoints`),
the import card sends it to `/api/import`, whose `import_timepoint` answers `joins`, the participant's
one workbook, and `sheet`, the timepoint's label made free with `free_sheet`, when they have one, so
Make writes the raw source and adds its sheet to that workbook after `archive_copy`, rolled back by
`unadd` with its `progress` step, and otherwise `/api/create` takes `timepoint` for the workbook it
makes. `/api/complete` takes `timepoint`, its number or its label (`timepoint_asked`). On the page,
`tpList`, `tpHere` and `markOf` in `app.js` give the bar the timepoint of the current passage's sheet,
`fillTpPick` and `drawTpPick` draw the switch where the sheet switch stood, `tpMenu` its menu, and
`barNumbers` and `drawMark` the timepoint's counts and mark. Settings' rows are `drawTimepoints` and
`saveTimepoints`, `tpAfter` drawing the screen behind again once the card shuts. The command line's
`timepoints` and `import --timepoint`, and the MCP's `timepoints` and `timepoints_set`, go through the
same functions. With `#tp-pick` shown, `style.css` (`.rail:has(#tp-pick:not([hidden]))`) hides View and
Feedback from 620px down and gives `.rail-case` a min-width of 3.5em, and at 400px closes the bar's gap
to 3px and takes the name to 13px and the label to 14px, so the name reads "P1 W..." at 360.

**Timepoints, part 2** (21 October, tp2): a PETs canvas per timepoint and the LPETs canvas. A timepoint's
boards are a themes file of their own, `<stem>.themes-t2.json` for T2, T1's the file it always was, so a
board's id, its Current board and its PETs complete are the timepoint's and no reader of the T1 file
changes. `themes.SCOPE`, a context variable set by `themes.scoped(n)` for one request or one command,
names the timepoint: `themes_path` gives its file and `read_cards` reads only the sheets the progress
file places there (`placed_sheets`), so a participant with sheets placed reads T1's alone with none set,
and one with none, every project of one timepoint, reads every sheet as before. The writers that carry a
change to the boards go by it too: `rekey` runs once for each PETs file (`each_timepoint`) and
`statement_edited`, `statements_written` and `passage_written` on the timepoint of the passage's sheet
(`at_sheet_timepoint`), and `cli.cmd_turn_write` runs at its sheet's timepoint. LPETs are `gets.py` run
inside `gets.lpets(workbook, names)`: `gets_path` gives `<stem>.lpets.json`, each "case" is a timepoint,
`T1`, named by its label through `NAMES` in `who`, and each book (`server.lpets_books`) carries its
`timepoint`, which `fresh_of` and `at_timepoint` read the snapshot at, `cite`, the label a line's time
takes, and `missing`, `NOT_INTERVIEWED` in the panel. On the server `route_scope(route, body)` wraps
`_run` and both print pages: `timepoint` on `THEMES_ROUTES` sets the scope (`board_timepoint`, None in a
project of one, refused for a timepoint the project has not got), and `lpets` on `GETS_ROUTES` runs
`lpets_scope`, which sets `LPETS_FOR`, so `gets_books` and `held_books` answer the timepoints. `/api/themes`
answers `timepoint` and `timepoints` (`participant_timepoints`) in a project of two or more, the GETs reply
`lpets`, `participant` and `timepoints` on LPETs, and `/api/gets-ai` refuses there (`LPETS_NO_AI`). On the
page `themesOpen` takes `timepoint` and `lpets`, keeps `TH.tp`, `TH.tps`, `TH.lpets` and `TH.scope`, and
`api` in `app.js` asks `thScopeFor` to add the scope to every call in `TH_SCOPED` about the canvas in
front. The undo stacks are kept by workbook and canvas. `thTpDraw`, `thTpMenu`, `thTpGo` and `thTpWire`
draw and run `#th-tp-pick` after the PETs bar's tabs, `thStageGo` and `thToLpets` move between stages,
`thWhere` is what a way back or a new window reopens, and `spotNow` and `comeBack` keep it across a
restart. `DS_STAGES` marks LPETs built, and on LPETs `#th-cases` stands in its tab (`.lpets-mode`).
Two faults of part 2 were mended in part 3. `export.export` takes `timepoints`, each `(n, label)`, which
`api_export` passes in a project of two or more: `export_timepoints` writes each timepoint's rows in turn,
ordered and labelled from that timepoint's board, with a last column, `Timepoint`, and the PETs screen's
export passes the timepoint in front alone. `cli.cmd_statements` without `--timepoint` runs
`statements_at` once a timepoint and adds `timepoint` and `timepoint_label` to each row. And a timepoint's
copy on LPETs keeps `cite`, the label its times were cited with: `snap_hash` leaves the cite out, and
`gets.load` inside `lpets` re-cites every copy whose label has changed (`recite`), so a renamed timepoint
is never "changed since it came in".

**Timepoints, part 3** (21 October, tp3): LGETs and the Trajectories board. LGETs are `gets.py` run inside
`gets.lgets(root, names)`: `gets_path` gives `idiograph-lgets.json`, each case a participant, `case_files`
their workbook and LPETs file, and `snapshot` hands over to `lpets_snapshot`, which reads the participant's
LPETs file through `lpets` and makes each LPET (and an LPET inside one) a "PET" of the copy, its statements
those under its timepoint PETs and its own statement cards, every line keeping `at`, its timepoint's key,
and `cite`, the label its time was cited with. `snap_hash` leaves each line's cite out and `load` re-cites
a line whose label changed. On the server `board_scope(root)` runs `lgets_scope` in a project of two or
more timepoints, and `route_scope` puts every route in `LGETS_ROUTES` there unless it names `lpets`, so
the page, the CLI's `gets` (`cli.scope_of`) and the MCP tools reach LGETs where GETs were with no new
argument. `gets_head` answers `lgets`, the GETs reply `lgets` and `timepoints`, `/api/gets-ai` refuses
(`LGETS_NO_AI`), and `gets_print` names its kicker. `trajectories.py` keeps the board in
`idiograph-trajectories.json`: `apply` runs the six operations in order and refuses them all on one wrong,
`change` writes with a History line unless `dry_run`, and `board` answers the columns, the unplaced and each
participant's card. `/api/trajectories` and `/api/trajectories-ops` (`traj_root`, refused with `TRAJ_ONE`
in a project of one) answer through `traj_reply`, each card's colour from the LGETs' `looks` and its LPETs
from `lpets_snapshot`, and `cli.cmd_trajectories_show` and `cmd_trajectories_apply` call `traj_reply` and
`traj_apply` under the project's lock. On the page `DS_STAGES` marks LGETs and Trajectories built, so the
GETs tab hides in a project of timepoints, `TH.lgets` comes from the answer and names the words
(`thGetWord`, `gtKicker`, `gtNotComplete`, `gtNoPets`), and `thStepTo` and `esStep` open the board
through `thToTraj` and `esToTraj`. `static/trajectories.js` draws `#traj`: `trajOpen` and `trajLeave` as
the other screens' ways in and back, `trajOps` sending every change through `/api/trajectories-ops` and
drawing the answer, `trajStep` for its tabs, `trajHome` for the mark, and `spotNow`, `spotTaken`,
`comeBack`, `navHere` and `navWayBack` know the screen as `trajectories`. The Not placed band hides from `#tj-open-side` in `#tj-bar` (trajside, 10 November 2026, Adam: more horizontal room): `trajSideSet` keeps `idiograph-trajectories-side` (`open` or `closed`) in localStorage as the boards' `TH_SIDE_KEY` is, `trajDraw` drops the fixed band while shut, and the button carries `.th-door-n` with the count not placed and the boards' `themes.side.hide` and `themes.side.show` words. Backspace on a participant's cell sends them to Not placed. Area 237 holds it in a headless browser at 1280 and 720.

**Trajectories, layout F** (trajbuild2, 10 November 2026, Adam's Freeform page of revD, option F of
trajdesign). `trajectories.py` keeps on each column `description`, `colour` (a key of `PALETTE`, the app's
tokens `good`, `amber`, `danger`, `excerpt`, `sift`, `trace`, `accent` and `crux`, said Green, Amber, Red,
Blue, Plum, Teal, Taupe and Orange, each with its dark value from tokens.css), `icon` (one of `ICONS`) and
`order`, the participants in his order, any not named after them in case order (`order_of`). On each
participant in `placed` it keeps `title`, their own label, `tags`, `picture` and `hidden`, the LPET ids
this screen leaves out, and at the top `tags`, each word's place in the participants' palette (`TAG_NAMES`,
gets' 25), so a tag, and an LPET's domain, has one colour across the project (`colour_for`). `apply` runs
`OPS` and hands `LPET_OPS` (`state`, `quote`, `bold`, `domain`, `states_from_notes`) to the caller's
`lpet_op`. `traj_apply` in idiograph_routes.py opens a participant's LPETs file only when an op names it
(`traj_lpets`, the board `gets.source_board` gives, under `lpets_scope`), runs `gets.row_op` on it in memory,
and `change` calls `commit` to write those boards only once every op has passed, after its own checks and
before its own file, so a refusal anywhere writes nothing. `gets.row_op` works on the LPET table's rows
(`board.rows[gid][T1]`, `{quote, note, bold}`): `state` is the row's `note`, `quote` its tick (a key of
`row_choices`, the Inspector's offer), `bold` spans `[start, end]` of the key quote's characters
(`spans_kept` merges and orders them), ticking the quote standing in, a new quote dropping the old bold,
and `domain` the LPET's own `domain` key, which `themes.normalise` now keeps (`themes.DOMAIN`, 40
characters) so a save from the LPETs canvas keeps it. `states_from_notes` reads each LPET's note with
`states_in_note`, paragraphs headed by a timepoint's key, label or description ("T1:", "**T2 (Midsummer)**
-"), into rows whose note is empty, a row with a state already kept and said, the note untouched.
`gets.rows_of` and `table` carry `bold`, and themes.js `gtRowsKept` keeps it and `gtRowSet` drops it with a
new quote, so the LPET table keeps what Trajectories made. `gets.lpet_rows` gives each LPET's `cells` per
timepoint (`state`, `quote`, `chosen`, `bold`, `choices`, `missing`), and `traj_people` adds them to each
participant as `rows`. The LPETs screen and the LPET table keep the domain and the bold but do not draw them
yet (backlogged).

A key quote's own marks and several domains (trajfix, 11 November 2026, from Adam's shots of his study).
A Quote cell that holds its own inverted commas came through `lpet_rows` as it was and the page set its
curly marks round them, `“"...”"`. `lpet_rows` now gives each quote and each of `choices` without them,
through `quote_cut`, which takes `themes.bare` (the rule of thBareQuote and canvas_out's `bare_quote`) and
answers how many characters came off the front. His bold stays kept against the quote as the LPETs file's
copy holds it, marks and all, so a bold made before the fix stays on its words: `lpet_rows` moves the
spans back by that many to show them, clipped to the words and an empty one dropped, and `row_op`, which
reads the rows as kept (`bare=False`), takes `spans` against the words alone and moves them forward by as
many to keep them. The workbook is never touched. An LPET's `domain` stays one string, read with commas
between domains by `trajectories.domains_of` (each trimmed, an empty part or a repeat left out). `board`
gives each row `domains`, `[{"word", "colour"}]`, a word no op has coloured yet coloured on a copy of
`tags` by `colour_for` as the next op would, so opening writes nothing, and the `domain` op gives each word
its colour with `colour_for`. The page draws each as a `.tf-pill` inside `.tf-pills`.

A key quote from anywhere in the interview (trajchoose, 11 November 2026, Adam's ruling). A cell's key quote
comes from one of three places, `gets.SOURCES`: `lpet`, the LPET's own at that timepoint (`row_choices`, each
now with its `source`), `interview`, any other statement's own quote of that timepoint's interview, its
statement in another LPET or in none (`interview_quotes`, read from the LPETs file's copy of that timepoint,
whose `lines` hold every statement, placed or not), and `transcript`, a passage of any of the participant's
interviews. A statement's quote is ticked by its key as before, so `table` and `quote_at` find it and the
LPETs screen's table shows the same tick, and `row_op` now takes any key `quote_at` finds in that timepoint's copy.
A passage is kept on the row as `passage`, `{"at": "T3", "turn": "<sheet>:<row>", "start", "end", "text"}`,
with `quote` empty (`passage_kept`, which `rows_of` calls, so `normal` and a save keep it, and themes.js
`gtRowsKept` sends it back and `gtRowSet` drops it when a quote is ticked in the Inspector). `passage_from`
reads the op's `passage` (`interview` by key, number or label, `turn` or `sheet` and `row`, `start` and `end`,
the whole turn without them) against the transcript and widens it to whole words, refusing an interview with
no transcript, a turn not there, a span outside its words, and a quote and a passage at once.
`passage_found` reads a kept passage back at its place, or where its words stand in that turn after an edit,
and `lpet_rows` gives it as the cell's quote with `source` `transcript`, an empty key, `at`, its time cited
with that timepoint's label (`cite_of`) and `passage`. A passage whose turn or words are gone gives nothing,
so the row falls back to the first quote as a lost tick does. Bold on a passage keeps the passage, and bold
on a quote standing in still ticks it. The transcript is read by `themes.transcript_turns`, every turn with
words of the workbook's transcript sheets with its timepoint by `placed_sheets`, read-only and held in
`TURNS_HELD` while the workbook's time and size stay the same, so drawing the board after each change opens it
once. `traj_turns` in idiograph_routes.py hands `lpet_rows` and `row_op` a reader by timepoint key, and
`traj_people` adds each participant's `quotes`, `interview_quotes` by timepoint, which the page and
`traj_answer` take each cell's other quotes from (the command line's choices carry `lpet`, the LPET each sits
in). `/api/trajectories-turns` answers the participant's own turns at a timepoint, the interviewer's (Settings'
interviewer) and another speaker's left out, and `interviews`, the timepoints they have a transcript at. An
agent reads the same with `turn show`, so the parity list maps it there. On the page `trajChooserHtml` draws
the three parts (`.tf-choose-part`, `.tf-choose-h`), a cell with No quote opens it too, and Choose a
passage... opens `trajPassHtml` in a grid row of its own under the LPET's row (columns 2 to the end, the
participant's cell spanning one more row): the interviews (`data-pass-at`), a find box redrawing the list
alone (`trajPassFind`, `<mark class="tf-found">`), and the turns, the passage taken marked `tf-taken`. A
`selectionchange` listener keeps the words selected in one turn (`trajPassPicked`), Take the words selected
sending them as `start` and `end` and Take the whole turn the turn alone (`trajPassTake`).

Pictures: `picture_bytes` keeps a PNG cut square at its middle and scaled to 256 in the standard library
(`png_read`, `square`, `png_write`), a JPEG of 400 KB or less or an SVG of 200 KB or less with no script as
it came, refusing anything else. `change` writes them to `<project>/trajectories/pictures/<Pseudonym>.png`
through `picture_files`, the one replaced or taken off moved to `pictures/_Archive` with the time in its name, never deleted. The page
sends a picture already squared to 256 by a canvas as a data URL (`trajOwnPicture`), an agent a path
(`from`). `traj_picture_url` answers `/faces/faceNN.svg` for the set, `set:faceNN`, and `/traj-picture` for
his own, `stream_traj_picture` serving it by name alone from the project's pictures folder with a CSP that
runs nothing. The set is 24 line portraits in `apps/idiograph/static/faces/`, drawn by
`packaging/make_faces.py` for the app and under its licence (NOTICE.md). Change picture... is an
`<input type=file>` (`#tj-picture-file`): wry 0.57's `WryWebViewUIDelegate` answers
`runOpenPanelWithParameters` with an `NSOpenPanel` in the Mac's window, so it opens there as in a browser
(it passes no file types, so the panel offers any file, and one that is no picture is refused with
`trajectories.picture_unread`).

The screen (`trajectories.js`, the `.tf-*` block in themes.css): `trajBandHtml` draws a band, its head
in its colour's token, `trajPersonHtml` a participant, `trajCellHtml` a cell, the stand-in
quote `.tf-q-auto`, `trajChooserHtml` the quotes a cell can take as radios in its three parts, `trajPassHtml`
the passage picker, `trajEditHtml` the editor in
place, `trajPickerHtml` the colour and icon. A picture, a tag's pill and a tag's colour dot take their colour from the cases' `case-N` classes (`--case`, as `--pc`), and a picture stands on `--tf-face-ground`, white in either theme. Every change goes through `trajOps`. Keys on a focused cell
(`trajMove`, `trajPlace`) and Cmd or Ctrl+B in a key quote (`trajChosenSpan`, `trajBold`). A drag of a
participant's cell drops at the place under the pointer (`trajDropAt`). Settings `traj_quotes` (`off`,
`short`, `full`, short on a new install) and `traj_notes` (off) are the status bar's Quotes and Notes,
`OWN_SETTINGS`. The board's own note (trajnote, 10 November 2026) is `note` at the top of the trajectories
file, set by the op `note_board` (`NOTE_MAX`, trimmed, its lines kept, "" taking the key away), answered by
`board` as `note` and printed first by the command line's `traj_lines`. On the page it is `#tj-board-note`, a
textarea in `#tj-band` after the question, a line of its own (`flex: 1 0 100%`) in the sentence's look,
which `trajNoteDraw` hides while `traj_notes` is off and fills from the answer unless it has the focus.
Enter or leaving it sends `note_board`, Shift+Enter a new line, Esc puts it back. There is no Trajectories
PDF or picture yet, so it goes into no export. Area 369 holds the ops, their dry runs, the migration, the stand-in, the bold, the domain
kept through an LPETs save, the shared tag colour, the moves, hide and show, the pictures, the CLI and MCP,
and the keys, Cmd+B, the chooser and a drop's place in a headless browser.

**The project file.** `idiograph-project.json` at a project's root, `{"name", "research_question",
"updated"}`, which Settings writes under Projects (see Projects in the [manual](manual.md)). With no
file the name is the root folder's own and the question is empty, and a key the file carries
beyond the three is kept. `uid`, since 26 October, is the project's own id, written by `send_project` (`project_uid`) at its first send under the project's lock and never changed. `copy_of`, since 21 October, `{"name", "opened"}`, and since 26 October with the shared project's `uid`, `sent`, `version` and `statements`, is written by `mark_copy`
into a project opened from a shared copy before `add_project` lists it, and `read_project` answers
`copy` true for it, the "copy" tag on its card and its page. `names`, since 16 October, is the new pseudonym Rename gave each case whose folder it kept, by the folder's label, `display_case` of its name, so a second part is never written (see Rename and the passage below). `order` is his order of the rows, a list of case labels by pseudonym,
which `/api/order` writes through `write_order`, every other key kept, and `in_his_order` reads:
the cases it names first, in its order, then the rest in participant order, a label with no case passed
over. The demo's order is fixed. `agents` is the privacy tick, Allow AI agents to read this project,
`{"allowed": true, "at": "<iso time>"}`, absent and so off until he ticks it, and the command line
reads no project without it. The demo's always reads as allowed. Write a guide for AI agents
writes `AGENTS.md` beside it, `docs/agents.md` with the project filled in where the guide marks the
place, its first line saying the app wrote it, and never over a file without that line.
`pet_labels` is how the exports label the PETs, "letters", A, A1, A1.1, as Smith, Flowers and
Larkin's Box 5.6 letters them, or "numbers", PET 1, PET 1a, 1a.1. A missing key, or anything else,
reads as letters, `themes.pet_labels_of`, and `read_project` sends it. PET labels, under Export on
the PETs screen and under Settings, Projects, writes it at once through `/api/project` and
`write_labels`, every other key kept. On the server `pet_labels_for` gives a case's project's
setting to the Word document, the print view and the PET draft, which take their labels from
`themes.pet_numbers` with that setting, `labels`, so the three never disagree. The command line's `board
export` takes the project's setting, `--labels` overriding it for one run, and MCP's
`board_export` takes `labels`. The demo's own is `demo/idiograph-project.json`, and a save for the demo
is refused, so the demo keeps the letters.
`timecodes` is how the project writes a timecode (28 October, Adam: the project's, not the user's),
"75:12", "1:15:12" or "01:15:12", each the form itself at 4512 seconds. A missing key, or anything
else, reads 1:15:12, `workbook.timecodes_of`, and `read_project` sends it. Timecodes, under Settings,
Projects, writes it through `/api/project` and `write_timecodes`, and `project set --timecodes` and MCP's
`project_set` with `timecodes` the same way, its change a line of `project_changes`. One function writes
every timecode, `workbook.timecode(seconds, form)`, in place of `mmss`, `themes.clock` and the page's
`clockText`, and its twin `timecode(seconds, form)` in distil.js, which themes.js shares for its player.
The server passes the form in: `read_case`, `edit_turn`, `replace_words`, `trim_preview`,
`assign_preview` and `themes.read_cards` take `form`, by default the project of the workbook,
`workbook.timecodes_for(path)` through `server.project_of`, and `read_cards` answers `timecodes`, which
`with_row` writes by. Find keeps its places with the form (`app_search.held`'s `extra`), the import
previews take the project's (`turns_view`, `qdpx_view`, the command line's `landed`), and the command
line's `turns_of`. The GETs and LPETs files keep every time as 1:15:12, `gets.KEPT_AS`: `gets.load`
gives each line's time in the project's form from its `seconds`, a time cited with its timepoint keeping
it (`retime`), `gets.write` writes them back as kept, and `snap_hash` reads them as kept, so a change of
timecodes changes no file and no case reads as changed since. `routes.gets_file` keeps its read with
the project file's mark. The page reads `timecodesOf(project)`, the player's clock and the box's prefill
the case's, and a save retimes the open transcript from each row's seconds (`retimeRows`) and reads an
open board again (`thOwnLoad`). Never following it: the statements CSV and the notes export
(`hhmmss`, 01:15:12), the workbook's Timestamp cell (`timecode_like`), QDPX's milliseconds, `--json`'s
seconds, Import's Time codes choice, and the round's clock and the minimap, which are lengths of time. A `second_part` key a file from before 9 October holds,
Adam's two-part folder names, is passed over and never sent: New project and Add transcripts make
every case `P<n> - Pseudonym`, and `new_cases` ignores a `second` or a `second_part` a page from
before sends. A case folder that already carries a second part, `P<n> - Pseudonym-Secondname` as
GRAVITY's do, is listed, opened, joined (`JOINABLE`) and shown by its pseudonym alone through
`display_case`, as before.

**Rename and the passage (16 October).** Rename is `/api/rename` in `server.py`: `rename_folder_of`
finds the row's case folder at the project's root by its label, refusing the demo, a workbook in the
root itself and a label no folder has now, `rename_plan` says what will change and the plan its act
follows, both from the files as they stand and nothing written, and `rename_case` makes it. The plan
reads the case's workbooks, `case_books`, the annotated ones and any raw source in the folder and the
raw sources in `Source/`, counting through `workbook.speaker_rows` the rows of each transcript sheet
whose Name cell reads the case's pseudonym, case and spacing aside and never the interviewer's, and
takes the themes files, the GETs file when `names_label` finds the case's label or the label its
themes file gives it in it, the project file and the recent list's entries in the folder. Ticked, it
adds the folder and each workbook whose name carries the pseudonym as a whole word with its
progress and themes files, `renamed`. Its lines name no file the app keeps (16 October, later):
`books_said` names each workbook by its kind, the annotated workbook, the transcript or the
transcript in Source, its file's name after only where the case has two of a kind in one place,
`passages_said` says 'of the "Initial" sheet', the sheet in straight marks as the bar's `sheetLabel` names it
(17 October, later), each workbook's line leads with the pseudonym, "Ada's
name on" its passages, and names the workbook after them, ", in" its `books_said` words, only where
more than one workbook carries the name (17 October, later), a moved workbook's line says it "takes
the new name" in words, never by its file's new name (17 October), and ends with `sidecars_said`,
"and keeps its progress and PETs boards", and `project_said` says what the project file gains, his order
when `order` names the case and the note of the new name, `noted`, while the folder is kept, or the
note that goes, `unnoted`. Ticked, the note is never written, so its line goes, and each state's
lines are exactly the files its act writes, which area 156 compares. `rename_refusal` says the one
line of a refusal, "another participant's name" for a name taken. The act holds
the case's lock and the project's, keeps a copy of every file it writes in `_Archive/` through
`keep_copy`, `<stem> (pre-rename <date-time>)<suffix>` as `archive_copy` names a workbook's, the case's
`_Archive/` for its workbooks and sidecars and the root's for the GETs file and the project file,
then writes the Name cells through `workbook.rename_speaker`, the one write path every save takes,
the themes files' `case` and `workbook`, the progress files' trim and assignment `backup` paths when
the folder moves, the GETs file through `relabel_all`, every key and string naming the case or a card
under it, the project file's `order` and `names`, and moves the files. The folder moves after, under
the project's lock alone, since Windows renames no folder with a file open in it. A failure puts
everything back through `unrename`, the copies taken away with it. The recent list is written last
and `_gets_books` lets the study go. A folder kept keeps the new name in the project file's `names`,
by the folder's label, which `names_at` reads and holds until the file changes, and `label_for` gives
a case folder its label from it, `display_case` of the folder's name with the new pseudonym in place
of the folder's own. Every label the server hands the page or writes into a file goes through
`case_label`, its case folder's `label_for`, `list_cases` and `participants` taking the names once
for every row, `standing_cases` joining a renamed case by its new name, and `shown_name` giving the
statements screen's bar the workbook's stem with the new pseudonym in place of the one its file still
carries. On the page `openRename` opens the card, `rnPlan` asks the plan, again on each pause in the
typing, `rnTyped`, and on the tick, and `rnGo` renames and draws the rows again, then `rnShowRow`
brings the renamed row to the middle of the window and, where the page cannot scroll it clear of the
toast, stands the toast just above it through its `bottom`, which `say` clears for the next line. `cardHtml` puts
Rename after Files where the row is no demo's and its card says `folder`, which `participants` sends.

**Every file that names a participant (renamefix, 11 November 2026).** pbiodraw found that a rename left the
Trajectories board and the LGETs behind, both keyed by the participant's label, and with the folder ticked left
the LPETs file and the PETs boards after T1 under the workbook's old stem. `case_files.py` is now the one place
every such file is named, and `rename_plan`, `rename_refusal` and `rename_case` follow it, so the app's Rename,
`participant rename` and MCP's `participant_rename` all carry the participant through each. Beside a workbook,
`sidecars` is every file in its `Working/` named `<stem>.<anything>` (a file named after a longer-named file of
the folder left to that one), which moves with the workbook, and `side_files` those that name the participant
inside, read by the plan and carried by `carry_side`: each PETs boards file's `case` and `workbook` at every
timepoint, the LPETs file's `workbook` for each timepoint, and the progress file's trim and assignment
`backup` paths when the folder moves. At the root `PROJECT` lists each file with its line, its carry and its
write: the GETs and the LGETs (`relabel_all` over every label in `was`, the copy's `workbook`, the GETs through
`gets.write` with its one-writer guard and the LGETs through the same write at `FILE_AT`), the Trajectories
board (`placed` by the new label, each trajectory's `order`, and the picture's name when `picture_move` moves
its file, named after the participant, with the folder ticked), the list of names to replace (`for` and `to`
naming the old pseudonym take the new, written by `names.save_at` at mode 600 and never copied into
`_Archive/`), and the project's own file (`order` and `names`, as before). `KEPT` names every other root file
the code names with why a rename leaves it: the project's History, the code list, the holds, a shared copy's
manifest and `team.json`. Area 156's `_every_file_named` reads every `idiograph-*.json` and `team.json` in
`apps/` and `family/` and fails on one in neither. The plan reads each file first, so one that is there and
cannot be read is `unread` and refuses the rename (`server.not_renamed_unread`), and with Working together on a
move of the folder or a file is refused (`server.rename.team_folder`), since the team's signed list and its
messages name a participant by their folder. The act works out every file's new contents before it writes,
keeps a copy of exactly those that change, and records each write in `back` through `case_files.snapshot`,
its mode with its bytes, so `unrename` puts the list of names to replace back at its own mode.

**Each participant's picture, label and pen portrait (pbiobuild, 11 November 2026, Adam's layout A of
pbiodraw's proposal).** `participants.py` is the set: `one` reads a participant's `label` (up to `LABEL_MAX`,
Trajectories' 60), `portrait` (up to `PORTRAIT_MAX`, 800, its whitespace folded) and `picture` (`set:faceNN`, or a
file's name, through `trajectories.picture_kept`), kept in the project file under `participants` by the
participant's label, as `order` and `names` are, the file every screen already reads. `view` is what every
screen and agent reads, the project file's own with Trajectories' old `placed[case]["title"]` and `["picture"]`
merged in wherever the project file holds none, a picture from there marked `from_traj` so `person_url` gives
its `/traj-picture` address. A read writes nothing. `settle` moves those over for good, under the project's
lock: a picture's file copied from `trajectories/pictures/` into `pictures/` (its original left), both files
copied to `_Archive/` as `(pre-participants <date-time>)`, the project file written, then `title` and `picture`
taken off `placed` with a line in the Trajectories file's History and the same line in the project's
(`people_settle`). `api_cases` runs it for each project once there is something to move (`people_settled`,
which leaves it for the next listing when the lock is busy), and so does the first write of a set
(`person_change`). `apply` changes one participant's set in memory, each field left out kept, "" clearing it,
refused whole when a label or portrait is over its limit or holds a name of the project's list of names to
replace (`real_name_in`, every entry whoever it is for, through `names.find`, the refusal naming the entry by its
number, never the name), or a picture is not one of the set or cannot be read (Trajectories' own `picture_bytes`,
`data_url` and `read_picture`). A picture's bytes go through `trajectories.picture_files` with `folder` the
participants' `pictures/`, the one replaced moved to its `_Archive`. In the routes `person_change` holds a
change, dry or not, `api_participant` is `/api/participant` (`op` `show`, or any of `label`, `portrait`,
`picture`, `data`, `from`), `stream_person_picture` serves `/participant-picture`, `person_of` and
`participants.shown` give the page's `person` (`case`, `who`, `label`, `portrait`, `picture`, `picture_url`,
`colour`, their place round the GETs palette among the project's participants), and `with_people` adds it to the
project page's rows (`participants`, `demo_cards`), the statements picker (`api_participants`), the PETs
switcher (`api_themes_cases`), and `person_for_book` to `/api/open`, `/api/themes` and an LPETs answer, and
`gets_reply` to each case of the GETs' and LGETs' Participants panel, and `qdpx_export` gives `qdpx_out.plan` each
participant's `portrait`, written as their `Case`'s `Description`, first in it as Project.xsd asks. Trajectories' `title` and `picture` ops
take `set_person`, which `traj_apply` gives as a `person_change`'s `apply`, its `commit` writing the set after
the LPETs boards, and `trajectories.board` reads each card's `title` and `picture` from the participant's
`person`. Rename carries the set: `case_files.set_of` finds it, `project_line` answers a list now, his order's line
and "Their picture, label and pen portrait in the project", `project_carry` moves the key and the picture's new name,
and `set_picture_move` moves their own picture's file, named after them, with the folder ticked ("Their picture
in the project's pictures folder takes the new name"). On the page `personPic` draws the picture or the initial on `case-N`, Trajectories'
`.tf-pic`, `cardHtml` puts it with `.pp-label` and `ppPortraitHtml` on a row, `ppOpen`, `ppDraw`, `ppClose`,
`ppKeepFields` and `ppSave` are the fields across the row (each change through `/api/participant`, one at a time
in `PP.chain`, a field sent only when it differs from what was last sent), `ppMenuText` the pickers' rows,
`ppBarDraw` the bars' `#rail-pic`/`#rail-label` and `#th-pic`/`#th-label`, and `gtCasesDraw` the Participants
panel's `.pp-gwho`. The demo's two project files carry a set for the three. The command line's `participant
set` and `participant show` and MCP's `participant_set` and `participant_show` run the same route, and the
parity check holds `/api/participant` to them. Area 373 checks it.

**The label and the pen portrait in the exports (pbioexport, 11 November 2026, the Exports of pbiodraw's
proposal).** `participants.printed` is what an export takes of a participant, their `label` and `portrait`, never
the picture, and `table_rows(people, cases, name)` the participants table's rows, `number` (`number_of`: the folder's
P2, else the place in the order), `pseudonym`, `label` and `portrait`, "" where there is none, with `table_heads`
from `page_print.people.*`. Two ticks, both off on a new install and in `OWN_SETTINGS`: `export_portrait`, Pen
portrait, last under Export on PETs (`#th-inc-portrait`, in `TH_INCLUDES` so `thIncludesSent` sends `portrait` with
Print, PDF and Word) and last of `themes_print.INCLUDES` on the print view, and `export_participants`, Participants
table, last on the GETs print card (`#gt-print-people`, its row `#gt-print-people-row` hidden by `gtPrintDraw` for the
canvas, one GET's trail and LPETs through `gtPeopleShown`, sent as `participants` by `gtPrintUrl`, `gtPdfGo` and
`gtWordGo` through `gtPeopleSent`). The card's `[data-include]` ticks now save as they change through one listener,
where Descriptions there drew from the settings and saved nothing. The routes read them with `export_portrait` and
`export_participants` (`export_tick`), and `portrait_printed(path, given)` gives the set or None, `people_printed(root,
given)` every participant's (`people_view`) or None. The table of PETs takes `who`: `themes_print.page` puts
`who_html` (`section.who`, `.who-label` in italics, `.who-portrait`) after the head and before the board's note, its
tick checked when `who` is not None, `typst_data`'s `who` sets the same in `pets_table.typ` (190 mm wide, kept
together, 12pt under), and `themes_word.blocks` adds `who_blocks` after the Subtitle, the label a kept italic
paragraph. A participant with neither gets nothing. The GETs print takes `people`: `walked` gives `people`, the rows
for `parts["inside"]` named by `gets.who`, none in LPETs, `page` sets `people_section` (`section.part.first.people`,
`table.pt` with `pt-n`, `pt-who`, `pt-label`, `pt-portrait`, heads repeated, rows never split) first, after a full
set's contents with its line first there, and gives the table's and the trail's parts their `h2` and their new page.
`typst_data` gives `people` (`heads`, `rows`) and `names.people`, `gets-parts.typ` holds `part-head` (moved from
gets-all.typ) and `people-table`, `gets.typ` sets the table, a page break and the next part's heading, and
`gets-all.typ` lists it first in the contents and sets it after them. A theme table's Word document
(`gets_word.blocks`) puts `people_blocks` after the Subtitle: Heading 2 "Participants", a `themes_word.TABLE`
paragraph (`table_xml`, `cell_xml`: fixed columns `PEOPLE_WIDTHS`, a firm rule over it, under its heads and under it,
a light one between rows, `w:tblHeader` and `w:cantSplit`) and a `BREAK`, a page's end. `print_pdf.write` takes
`who`, `write_gets` `people`. The command line's `board export --portrait` and `gets export --participants` (also
with `--word`) and MCP's `portrait` and `participants` call the same writers through `routes.portrait_printed` and
`routes.people_printed`, `--draft` and `--canvas` refusing them. Area 373 checks it.

A statement card's passage is `thToPassage` in `themes.js`, from Go to the passage in `thMenuItems`,
which `thMenuDo` takes as `passage`, `thIsStatement` saying which cards are, every card on the PETs
canvas and a card of kind `es` on GETs, LGETs and LPETs, where until getsedit (below) a double-click on a
statement card in `thPointerUp` went there too. On the PETs canvas, since 30 October (cardedit,
Adam: a title's double-click renames it, so a card's should edit its statement), `thPointerUp`'s
double-click on any card, a stack's top and a card of a stack shown open among them, runs
`thCardEditOpen`, the editor the Inspector's double-click opens with `panel`, as it did until 16 October:
`thCardEl` finds the card in `TH.els.cards` or, open in a stack, `TH.els.under`, the box goes in after
`.th-text`, so a quote shown on the card stays under it, and `.th-text[hidden]` hides the words, which
`.th-text`'s `display: -webkit-box` otherwise kept on screen. It saves through `thCardEditDone` and
`thStatementWrite` to `/api/edit-statement`, the route the Inspector's edit takes (agents write a statement
with `turn write`, unchanged). A press on the quote keeps `kq` and opens `thKqOpen` on each click, so its
double-click edits nothing. Area 297 runs `thPointerUp` in node on themes.js's own code.

The same on the GETs, LGETs and LPETs boards (getsedit, 30 October, Adam: "Edit there too"). `thPointerUp`
runs `thCardEditOpen` on every card, and on GETs (`TH.mode === 'gets'`) it hands a card that is not a
statement to `gtCardOpen`, the Inspector, as before. A statement's line is `thLineAt`: on PETs the board's
workbook and the card's `sheet`, `row` and `line`, on GETs the case's `path` from the Participants panel
(`gtCase`, the participant's workbook, on LPETs the timepoint's, which is the participant's too) and the line
`thLineOf` reads from the key's ident, null for a case or line not found, which `thCardEditOpen` refuses
with `TH_EDIT_MISSING` as it does a `gone` card. On GETs the route's `check` must answer `copies`, kept in
`TH.canCopies`, else the double-click says `RESTART_LINE` and opens nothing. `thStatementWrite` sends
`thLineAt`'s body, then `gtLineTook` gives the words to the panel's copy, `TH.gets.cases[...].lines`, and
draws the panel, and the board's `v` comes from the answer's `copies` for the file on the canvas, `lpets`,
`lgets` or `gets`. `gtPanelDraw` gives a statement's title `data-edit` and `themes.inspector.edit_tip`, so
the Inspector's double-click opens the box there as on PETs. The Shortcuts card's `help-gets` row is
`page_idiograph.cards.edit_or_inspector`.

The Inspector's buttons under a label's count sit on one `.th-leave-row` (auditgap, 11 November 2026), whose
margins, 10px up under the count and 20px below, are what the Take out row and the note box after it count on.
`thArrangeHtml(id, more)` draws Auto-arrange and a GET's Audit trail as `more` on the one row, and a theme's
panel in a thematic analysis project draws the same row, with `.gt-acts` on it, which wraps in a longer language.
A button drawn outside such a row, as Audit trail was, or a row with margins of its own, as the theme panel's
`.gt-tacts` was, ends under the box that follows it: Audit trail under a GET's note box by 8px, and Auto-arrange
under a sub-theme's Take out by 4px.

On the server `api_edit_statement` holds the case's lock and the root's (`writing(path, root=...)`), reads
`copies_before` first, writes the line, carries it to the case's boards through `themes.statement_edited`
(at the sheet's timepoint, `at_sheet_timepoint`, since a GETs board sends no `timepoint`), then
`follow_statements` with the line's key and its words before and after, and answers its result as
`copies`. `statement_copies` names the files that keep a copy, the GETs file, then in a project of two or
more timepoints the participant's LPETs and the LGETs, in that order so each copy's fresh read sees the
file before it, `copy_scope` entering each (`lpets_scope`, `lgets_scope`), the LPETs' books from
`lpets_books`. In `gets.py`, `held_of` finds the participant's cases in the file in scope, by the copy's
`workbook` name on GETs and LGETs and by the books' timepoints on LPETs, `copies_untouched` says which stood
as their files did (`untouched` at each timepoint), and `statements_followed` gives each line that held
the old words the new, each board's card of it too where it keeps `text`, and the copy a new `snap_hash`,
so the edit alone never marks it changed. A copy that stood untouched is read again through `fresh_of`,
and when that read hashes as the copy now does it takes the read's `seen`, so the stamp and the next open
do not read it again. A change already waiting keeps its mark. With `changed`, an agent's mark, each board
with a card that took words keeps a revision first under `history` and takes `updated` and `changed` with
its hash, as `themes.passage_written` marks a PETs board. Each file's answer is `cases`, `boards` (id,
name, keys) and `versions`, `themes.summary` of each board as `load` reads it after the write, for the
page's next save. The route's `check` answers `copies: true`. `turn write` (`cli.turn_write`) takes the
root's lock before the case's, carries each statement reworded in its own place (`reworded`, by
`moves_lines` mapping a line to itself) through `routes.follow_statements` with the agent's mark and the
revision's name, `copies_before` read under the lock, and its dry run through the same with `dry`, and
says each in `copy_lines`, answering `copies`. A line moved or removed is left to Take the changes, as
before. The parity check keeps `/api/edit-statement` with `turn write`. Area 298.

**A History line for every statement edit (histreplace, 30 October 2026, Adam by dialog: "Add a History
line").** His edit of a statement, from any screen, keeps one revision on every board that holds a card of
it, the board as it stood before, named by `themes.edit_line(who, old, new)`, `STATEMENT_EDITED`,
`Juno's statement edited: "..." to "..."`, `who` the pseudonym (`gets.who` of `case_label`, through
`routes.edit_lines`, which gives each statement's line by its key). `edit_words` shows both sides whole when
each fits in `EDIT_WORDS` (60) characters, else the words that differ with `EDIT_AROUND` (3) words of the
shared start and end round them and an ellipsis for the rest, each cut at a word past 60. A revision added
this way leaves the board's version as it was (`board_version` leaves `history` out), so an open page's next
save is never stale for it. `api_edit_statement` passes the line to `themes.statement_edited(..., said=)`,
which keeps it on each board of the case at the sheet's timepoint with a card of the key, whether or not
its card held the old words, before the card takes the new, and to `follow_statements(..., said=)`, where
`gets.statements_followed` keeps it through `noted_on` on every board of each copy with a card
`card_of(case, "es", key)`, took or not, before the copy takes the words. The answer adds `histories`, each
such PETs board's `history_list` by id, and each copy's answer its own, which `thStatementWrite` puts in
`TH.history` for the board on the canvas and draws when the History tab shows. `api_commit`, the statements
screen's save, takes `statements` from `workbook.save_turn`'s answer, the cell's entries before and after,
set only when the save changes the statements and popped before the page sees it, and for each line
`themes.reworded` names keeps the line on the case's boards through `themes.statements_noted` under the
case's lock, then on each copy's boards through `routes.statements_noted` and `gets.statements_noted` under
the root's lock alone, taken after the case's is let go so the save never waits on a long write elsewhere
and a copy that cannot have it keeps no line, the save standing. The cards and the copies keep their words
there, so the boards show the change and Take the changes as before. An agent's `turn write` passes no
`said`: its `history`, "Before: " and his request, stays its one line a board. A replace keeps none, since
it rewrites every revision's words too (`cards_reworded`), so a line would keep no old words. Area 300.

**A board's History in the order it was made (histdate, 30 October 2026).** The timer's save, `themes.save` and
`gets.save` with `revision` of `auto` (PETs boards, and GETs, LPETs and LGETs boards through the scopes), kept the
board as the file held it at `was["updated"]`, the board's last write. A statement's edit (`statement_edited`,
`statements_noted`, `gets.statements_followed` and `noted_on` for his own edit), a revision kept by hand, Reload's
`keep_before_reload` and `keep_canvas` change a board or add a revision without moving its `updated`, so the
automatic revision appended after one could carry an earlier date, and `history_list`, the array reversed, showed
it between later ones (Today, 28 September, Today). Every other maker, the board ops, the agents' ops, `take`, a
board brought in from a shared copy (its own `history` dropped by `current_board_only` and popped on the way in),
already took the clock. Both saves now pass the save's own `when`. `themes.history_of`, which every reader of a
board's revisions goes through, the History tab, `board history` and `gets history`, a restore's "Before
restoring" and `revision_by`, reads an automatic revision dated before the revision made just before it at that
revision's time, the earliest it can have been made, in place, so a board saved with the fault lists in order on
open with nothing written, and its next write that keeps the history keeps that time. A revision kept by hand or
by an op is never moved, since each always took the clock. The list stays in the order the revisions were made,
the array's, never sorted by time, so revisions of one second, an agent's to the microsecond beside the page's to
the second, keep their order. Area 303, and area 44's automatic revision brought up to date.
It splits the card's key through `thLineOf`, `Initial:12:0` from the right, takes the workbook, the
board's own or on GETs the case's from the Cases panel, `gtCase`, saves the canvas through
`thFlush`, and hands `openPassage` in `app.js` the workbook, the passage, `leave`, which puts the
screen away as `themesBack` does, `back`, which reopens the board through `themesOpen` or `getsOpen`
with `restore`, and `to`, PETs or GETs. `openPassage` asks `/api/open` with `passage`, which
`passage_in` checks against the case's rows and refuses with `NO_PASSAGE` before the recent list
moves, looks for the passage itself for a server from before, then leaves the board, opens the case
through `startCase` with `at`, sets `S.backTo` and `drawBackTo`, which names the bar's way back in
its title and its `aria-label`, the arrow alone since 18 October, when Idiograph's steps came to name
every screen beside it, where from 16 October later `#to-library-word` stood beside the arrow with
`.worded`, GETs always and PETs only while `#btn-themes` was hidden, and puts the caret in the statement's pair with `S.kqLit`, which `lightMarks` lights after the pointer's
and the caret's and `drawTurn` lets go. `toLibrary` takes `S.backTo` before the home screen, and
`openCase` and `loadLibrary` end it.

Back and Forward on Idiograph's screens (19 October, area 203) follow Sift's record (`SF_HISTORY`). `navGo` in
`app.js` wraps every way in that gives a screen its way back, `thToPassage` and `thToStatements` around
`openPassage` and `openStatements`, `gtFromPets`, `gtToPets`, `esStep`, and from the home screen
`openCaseIn`, `openThemesIn` and `openGetsIn`. Once the screen in front has changed it pushes an entry
`{ kind: 'idiograph-distil', n, p }`, `n` growing from `Date.now()` so it grows across a reload, `p` the
entry it was taken from, and keeps in `NAV.ways` the screen and workbook it was taken from (`navHere`) and
the action to take it again. `toLibrary` and `themesBack` call `navBackNow` first, which on an entry of
Idiograph's calls `history.back()`, so the arrow, Esc and a step that is the way back are Back. `navPop` hears
`popstate`: to an older entry `navBack` takes the way back once for each entry stepped over (`navSteps`),
`toLibraryNow` or `themesLeave`, each awaiting the board's reopening and answering false when it refuses,
and on a refusal pushes the entry back. To a newer entry `navForward` takes the stored action again with
`NAV.replay` set, so `navGo` pushes nothing, where `navHere` still matches its place, and otherwise, or when
the action opened nothing, moves the browser back with `NAV.skip` set so that move is passed over. Moves run
one after another on `NAV.chain`. The Mac app's window gets neither the mouse's buttons 3 and 4 nor Cmd + [
from its web view, so `mac::mouse_buttons` in `main.rs` adds an `NSEvent` local monitor for other-mouse
down and up, takes buttons 3 and 4 before the web view (returning nil) and evaluates `history.back()` or
`history.forward()` in the window they came over, and `window.js` takes Cmd + [ and Cmd + ] on a Mac. A
browser and Windows's web view do both by themselves (read 20 October, not yet driven): Tauri 2.12 leaves
wry's `browser_accelerator_keys` at its default, true (wry 0.57 `lib.rs`), so WebView2's
`AreBrowserAcceleratorKeysEnabled` stays on and Alt + Left and Alt + Right are its Back and Forward, and the
mouse's buttons 4 and 5 reach WebView2's own window, a child of tao's, never tao's, where Chromium steps
the history as Edge does. The page takes neither, its only Alt and arrow key a resize grip's. A run of the
Windows drive could prove it: open a passage from a PETs card, press the button through `SendInput`
(`mouse_event` with `MOUSEEVENTF_XDOWN` and `XUP`, `XBUTTON1`, through PowerShell as `ps_press` sends
keys) over the window, and read back that PETs is in front with the card selected, then `XBUTTON2` for
the passage again, and the same with `ps_press('%{LEFT}')` and `'%{RIGHT}'`. The shortcuts card writes the keys as Cmd + [ and Cmd + ], and `keyName` names them Alt + ← and
Alt + → off a Mac. `block2` is now a plain dependency on a Mac. `thBackFromPassage` puts the view and the selection back once
`themesOpen` has the board on the canvas, and when the card the passage was opened from, `from`,
stands with its middle outside the stage, a window resized meanwhile, moves the view at the same
zoom to put it in the middle. Since 17 October the caret's focus takes `preventScroll`, and
`passageStartInView`, run at once and again in the frame after `drawTurn`'s second centring, puts
the passage's first line at the column's head when centring left it above, and scrolls the window
back to it when it stands above the bar or near the window's foot, as at a phone's width, where the
fields stand under the column. The menu's path is driven in node in area 156, `thMenuOpen`'s click
on Go to the passage through `thMenuDo` to `openPassage`, on PETs and on GETs. On GETs `thToPassage` takes a statement's key, `<case>/es/<line>`, whether its card is on the board or not, so `gtRowClick`, a second click on the same statement's row of the Cases panel within 450 ms, goes the same way.

The case's thin line and the round's short bar, `.progress-strip span` and `.round-bar span`, are
`--good` since 16 October, later, the colour of a decided passage's done bar, since they count
decided passages, the crux orange keeping to cruxes and quotes on the statements screen.

**The cases' colours told apart, the badge's floor and a GET's title (16 October, later).** The dark
`--th-case0` to `--th-case7` were spread in hue and lightness, and area 147's `case_palette_problems`
holds light and dark each to `CASE_APART`, a colour distance, a colour-blind distance and `small_mark_distance`,
the difference of two marks a quarter of a degree across after Stone, Szafir and Setlur (2014), at
what each of them reached. A GETs card's kicker is a flex row of a fixed 15px, the badge then
`.gt-ktext`, and `.th-card .gt-badge` takes `zoom: var(--gt-up, 1)`, which `thView` sets on the
world from `gtBadgeUp(z)` with `gt-far` past `GT_BADGE_MOST`, where `.gt-far` hides the letter.
`thCanvasPage`'s script does the same by its scale, and takes `gets-mode` on `.cp-canvas` for a GETs
canvas. `.tr-who .gt-badge` and `.gt-twho .gt-badge` zoom by 1.2 and 1.1, and `gets_print.CASES`
draws it at 8.5pt. `.gets-mode .th-label` and `.gets-mode .th-swatch` take `--ink`. `gtColourMenu`
names Default's colour and puts the badge in each row's `.gt-cdot`. Below 520px `.th-cpanel` takes
the whole width, and `.gt-tree ul` carries the guide line. Since 17 October `.gets-mode .th-card.in`
sets `--th-edge` to `--ink`, which the left edge's inset shadow of `.th-card.in`, `.sel`, `.dragging`
and `.landing` takes before `--hue`, and `.gt-thead`, `.gt-titem` and `.gt-trail-head h2` draw their
stripe and underline in the ink, the GET's tint left to the washes. Below 900px `.th-discard` and
`.th-zoomer` stand at z-index 13, over both sidebars' 12, so a `--th-corners-up` measured before the
canvas settled never leaves them under the full-width Cases panel.

**The cases' colours and the Cases panel's tree (16 October).** `gets.looks` gives each case its
`colour`, his choice from the GETs file's `colours` through `gets.colours_of` or else `default`, its
place in participant order round the palette, `gets.COLOURS` of them, `chosen`, and `badge` from
`gets.badges`, the initial, two letters where two cases share one, and the initial and a number where
those are shared too. `gets.panel` puts them on each case of the answer, and `gets.colour_op`, behind
`/api/gets-cases` with `op` of `colour`, writes a choice or takes it away, as an act that takes every
case not yet in first, as Settings' save does. On the page `GT_COLOURS` names the palette, themes.css's
`--th-case0` to `--th-case7` through the classes `.case-0` on, which set `--case`. Since 21 October the
palette is 25, `gets.COLOUR_NAMES`, `--th-case0` to `--th-case24`, `.case-0` to `.case-24` and the
trajectories' `data-colour` the same. `gets.defaults_of` gives a case with no choice its own place while
free and else the next free after it, `looks` its `default` as it would be with its choice taken away, and
`colour_op` refuses with `TAKEN_COLOUR` a colour another case has. On the page `gtTakenColours` marks
another's colours disabled in `gtColourMenu`, whose More colours opens `gtMoreColours`, a grid of
`GT_MORE_COLUMNS` kept as `TH.menu.sub`. `gtLook` reads a
case's look, working it out as the server does for a server from before, `gtBadgeHtml` draws the
badge, and `gtDress` gives every card its case's class, which `.th-card.gt-card` draws along its top
edge, the border three pixels and the padding two less, and the drag's ghost the same. The Table view's
rows and `gets_print`'s GET table and trail put the badge before the name, the print view's colours
`gets_print.CASE_COLOURS`, the light ones, as the page is. The swatch on a case's row opens
`gtColourMenu`, a row menu of `menuitemradio` buttons, Default first, and `gtColourSet` saves the
canvas, asks the server, then draws the cards and the panel again, and takes the boards' stamps
through `thKnow` so the change is not taken for one from elsewhere. `gtTree` builds a case's tree from
its copy, each top-level PET's own statements, its sub-themes with every statement at any depth under
them, and the rest under Not in a PET, and `gtCasesDraw` draws it, a fold of each row in `TH.cfold`
by `<case>`, `<case>/<id>` and `<case>/:none`, which `gtFold` turns and `gtFoldsKeep` keeps in
`localStorage` under `idiograph-gets-folds`, by the project's `root`, and `gtFoldsRead` reads when
`gtLoad` meets a new project. During a search a row holding what it finds is open, and `TH.cflip`
holds the rows a chevron turned the other way until the search changes.

**The demo.** `demo/` beside the app is a project of its own, Living with a dog, with three cases,
`Juno/`, `Rowan/` and `Mabel/`, each holding `<name> - EN & ES.xlsx` and its `Working/` as any case
does. Since 26 October it is a finished project (Adam, 24 October). `demo/source/` holds each
interview as a CSV and `<name> - annotations.json` beside it: every participant turn's statements,
note, quotes and highlight, or empty, the times of the work, and the board, each PET and sub-PET with
its title, description and statements and each PET with its note and picks, the highlights kept as the
file's own and drawn as plain words since 16 October. `demo/source/GETs.json` holds the GETs board:
each GET's title, description, note and members, a PET or sub-PET named by participant and title, the
quote ticked for each participant's row, and the cards set aside. `make_demo.py --written`
(`ship_all`) builds each case into the workbook, the progress file and the themes file
(`build_written`), then the GETs across the three into `idiograph-gets.json` (`build_gets`, through
`gets.assemble`, `themes_ai.lay_out` with `gets.card_height`, `gets.row_targets`, `gets.save` and
`gets.version_op`), with the clock held at the files' times, every part of each workbook's zip dated
alike and the case files the GETs read dated at the GETs' `made` time, so `seen` comes out the same,
and the same sources build the same bytes. A copy whose files are dated otherwise, a clone or the Mac
app's, reads as unchanged through the snapshot's hash. `demo/pristine/` holds the three workbooks,
in its `Working/` their progress files and boards, and the GETs file, all committed, and
`pristine_copy` in `server.py` keeps a workbook in a folder named
`pristine` beside a folder of its case's name out of the case list, the GETs study, the PETs switcher and the
home screen's days, so a copy of the demo added as a project lists each case once (20 October), while a
live case's two sidecars and the live GETs file are gitignored. Reset demo copies the three back and the
GETs file with them, as a new copy so no cached read of the GETs file outlives it, and removes the
exports' `demo/Working/`. A normal start of the server copies in any of a case's three files that is
missing, and the GETs file when it is, never over one there, so a clone opens the demo as it ships, and
a run with `--root` leaves the demo alone.

**The thematic analysis demo** (demos, 3 November 2026, Adam that evening: two methods, so two demos, apart from
his projects). `demo/ta/` is a thematic analysis project of its own inside the demo's folder, the same three
invented participants coded from the IPA demo's own CSVs: `demo/ta/source/<name> - coding.json` (each turn's
extracts with their codes and its note, or empty, and the times of the work) and `demo/ta/source/Themes.json`
(the code list with descriptions, and each theme's title, definition, note, codes and subthemes, a code in no
theme not placed). `make_demo.ship_ta` (`--ta`, and `--written` after `ship_all`) builds each participant through
`create_from_source` and `code_turns`, which writes an extract's codes as the passage's pairs with the same quote
through `save_turn`, then `record_work`, then the code list (`build_ta_codes`, `codes.write`, every code on an
extract and none missing) and the Themes board (`build_ta_themes`: each code's lead card, the first of its rows by
`codes.key_order`, placed by hand on a grid (`ta_layout`: each theme a column, its codes two to a row under its label, a subtheme below in the same columns), then `gets.save` in TA's method, whose `codes.unfold` lays
every other extract of the code where its lead stands, and `choose`), the clock held, the same bytes each time.
It ships its pristine copy and live workbooks as the IPA demo does, `fill` and `reset_all` taking the code list
beside the GETs file. Being inside `DEMO_DIR`, `srv.is_demo` covers it, so it seeds, ships and is guarded as the
demo is: `srv.demo_ta_dir()`, `srv.DEMO_TA_ID` (`demo-ta`, the id the page names it back by), `srv.demo_root_of`
(which demo a path is in, so `project_of` answers the thematic analysis demo's folder for its participants),
`srv.is_demo_root` (every refusal that was the demo's folder alone) and `srv.demo_dir_of` (`ta` names it, else the
IPA demo). `list_cases` leaves out any folder under a root holding a project file of its own, so the IPA demo, and
a copy of the demo folder added as a project, never reads its participants as cases. `packaging/build_mac.py`'s
`stage_cases` stages it inside the staged demo the same way.

**The GETs file.** `idiograph-gets.json` at the case root, beside the project file, written by
`gets.py` and set out in full under The file in the [manual](manual.md), GETs. Its top level is
`schema`, 1, `created`, `updated`, `current`, the GETs board on the canvas, `chosen`, the Current
board when one is marked, `complete`, GETs marked complete or null, `settings`, `minimum`, null for
Smith's band, and `one_per_pet`, `study`, each case in or out with its reason, `colours` (16
October), the colour he chose for a case by its label, a place in the cases' palette, missing until he
chooses one and written only while it holds one, `cases`, each case's
copy by its pseudonym, its workbook's file name, the board it came from, `came`, `seen`, `hash` and `state`,
its `pets` and every statement in `lines`, and `boards`, each as a themes file's board with `rows`
beside it, its cards keyed by case and kind. `seen` (20 October) is the workbook's and the themes file's `st_mtime_ns` as `gets.snapshot` found them before it read a word, null for a themes file not there, and `gets.written_since` compares a file's time now with it to the nanosecond, for `untouched`, the read skipped on an open, and `changed_outside`, the stamp's `outside` for a case. `came` alone, kept to the whole second, had read a workbook written in the second a case came in as changed since, and outside the app when no window of it had written it, and area 217 failed about one run in three for it. A case kept before `seen` still goes by `came`, a file written in its second or later counting as written since. Wherever a board gets a case's cards by itself, `blank_board`
for New board, `take_in` for a case coming in and `save` for one that comes in with a save, it gets
one for every PET and every sub-theme, `gets.cards_of`, each in no group, laid in by
`gets.lay_in`. A sub-theme's groups, at any depth, `gets.depths` 2 and on, ride inside its card and
get none of their own, and `gets.ai_study` sends their statements after the sub-theme's own. A card a
board holds already for one stays. `gets.take` lays in a top-level PET with no card and a PET or a sub-theme new to the
case, never a sub-theme the copy held already, which `gets.add_subs` brings. `rows` is the GET table's, by GET and then by case, each
row the quote he ticked, `quote`, by its sheet, row and place among the row's quotes, and his
`note`, `gets.rows_of` leaving out a row with neither and a GET no longer on the board. A board keeps
`made`, `ai`, `review` and `revise` as a themes file's board does. A `cap` under `settings` from before 11
November 2026, the most GETs a New AI board made, `settings_of` reads as nothing. The page
sends the rows with the board on every save, so a tick and a note are steps of undo like any act,
and a save without them keeps the rows the file holds. The study is every case folder the case list finds with
an annotated workbook, and with two in one folder the one with a themes file, then the newest. The
demo's own is `demo/idiograph-gets.json`, gitignored with `demo/Working/`.

**The settings.** `config.json` beside the app. The server reads it afresh on every request,
merged over `DEFAULTS` in `server.py`, so a key the file lacks takes its default, and writes the
defaults to it when there is no file. Save in Settings writes every key back. Starting the server
leaves the file byte for byte as it was: `main` writes it only when there is none, and Sift's or Trace's
first start (`first_start_copy`) writes only what it copies from Idiograph's and its marker. Every write
of one setting, `add_project`, `remove_project`, `save_sift_email`, `save_databases`, Appearance sent
alone and that first start, goes through `write_config_keys`, which puts only the keys given into the file's
own text (`config_text_with`: a key it holds gets the new value in place, a new key goes after the last,
the file's indent and line ends kept), writes nothing when the file already holds them, and writes the
file afresh only when it is not one JSON object. Area 223 holds it (21 October, after sendproj found a
smoke's settings file rewritten whole with the defaults). A run with
`--config "<file>"` reads and writes that file in place of `config.json`, every key below
included, and `--root` makes `projects` that one folder for one run without writing it anywhere.

| Key | What it does |
|---|---|
| `projects` | The projects, in the order they were added, each `{"root": "<path>"}`, a root folder holding its case folders and its project file, absolute or relative to the repo root, or to the app's folder in a downloaded copy (`source_base`). A `*` in it is matched on the disk, so a case folder is named by its pseudonym. Empty is no project, the default and the Mac app's as it ships. `add_project` appends the folder Add project names, a case folder in it as a glob, and `remove_project` takes one out, its files untouched. A file with `root` alone, from before the projects, reads as one project with that root (`projects_in`), and Save writes the new shape. No study's folder is named in the code. |
| `interviewer` | The interviewer as the Name column has it, Adam by default. Those turns are context, never a stop, and alone take an interviewer note. |
| `work_in_rounds` | Work in rounds, off by default, so a new install starts with it off and a file without the key reads off (15 October). Off, the page shows nothing of rounds, no round count, short bar, clock, marker, target, streak or days, `loadDays` asks nothing of `/api/days`, and the card comes only for the round that ends its sheet or the case (`endsSheet`). `roundsOn` and `roundsHere` in `app.js` ask it. The server cuts and records the rounds either way, and the page still closes each through `/api/round-complete`, so the daily tally stays true. Saved with Celebrations' two ticks in `api_settings`. |
| `columns_hidden` | The statements screen's columns hidden (18 October), `statements`, `notes` or both, never the transcript, `[]` by default, set by Columns' Show ticks and Settings' View, `api_settings` saving such a list and leaving the file as it was for anything else, and a file holding anything else reading as none hidden. Hidden is never deleted. |
| `columns_stacked` | The notes under the statements in one column beside the transcript (18 October), `false` by default, set by Columns and Settings' View, holding only while both are shown and above 800 pixels. |
| `stack_top` | The column above in that column (21 October), `statements` by default or `notes`, set by a heading dropped on the other column's upper or lower half or by the heading's menu, `api_settings` saving either name and leaving the file as it was for anything else, and a file holding anything else reading as the statements above. |
| `stack_split` | The divider's place in that column, the upper half's share (the statements' until 21 October, when either may stand above), 0.5 by default, kept between 0.2 and 0.8 to a thousandth, set by a drag on it or its arrow keys. |
| `column_widths` | The statements screen's column edges as dragged (20 October), `{}` by default, each screen's width in pixels as text keyed to `left` and `right`, the first column's distance from the window's left and the last one's from its right, and `statements`, `notes` and `stack`, those columns' widths, whole pixels. `api_settings` takes one screen at a time, `{"screen": "2560", "widths": {...}}`, and widths of null take that screen out, so two windows on two screens never write over each other's. `column_widths`, `column_width_set` and `column_screen` in `server.py` clean it, twelve screens kept at most, and a file holding anything else reads as none. |
| `statements_columns` | The statements screen's three columns in their order (17 October), the names `statements`, `transcript` and `notes` once each, the book's order, `["statements", "transcript", "notes"]`, by default and on the Mac app as it ships. A heading's grip sets it and Columns' Back to the book's order puts the book's back, where until 18 October Columns and Settings' View chose among the six too, `api_settings` saving an order and leaving the file as it was for anything else. A file with `notes_place` from before, where the notes stood `right` or `left` of the transcript or `under` the statements in the panel at the right, reads the order nearest the screen it drew (`statements_columns` and `NOTES_PLACE_COLUMNS` in `server.py`), right `transcript, notes, statements`, left `notes, transcript, statements` and under `transcript, statements, notes`, any other value the book's, and `merge_config` drops the old key, so the next save writes the order in its place. |
| `larger_passage` | Larger current passage, on by default: the passage being worked on drawn larger than the rest. Off, every passage at one size and the current one on a band. Saved with the other ticks in `api_settings`. |
| `export_not_placed`, `export_binned` | The PETs table's export's two ticks (18 October), Include not placed and Include binned experiential statements, off by default. `themes.js` draws them under Export (`thIncludesDraw`), saves each alone through `thInclude` and sends both with Table, `unplaced` and `binned` in the print view's query, and with Word, in the body (`thIncludesSent`). The print view draws the same two beside Board note, `themes_print.INCLUDES`, and its script posts the key to `/api/settings` and draws the page again by its query. `server.export_includes` takes the request's value, else the settings', and `themes_print.page` and `themes_word.blocks` leave Not placed and the bin, headed `themes_print.BINNED`, Binned experiential statements, out without them. The command line's `board export` takes `--not-placed` and `--binned`, MCP's `not_placed` and `binned`, both off when left out. |
| `export_stacked` | The third tick under Export (19 October), Include stacked statements, off by default, beside the two above and drawn and saved the same way, `stacked` in the print view's query and Word's body. `server.export_stacked` takes the request's value, else the settings', and `themes.stacks_shown` keeps or drops each top's `stacked` in the outline the print view, the Word document and the PET draft read. The command line's `board export` takes `--stacked`, MCP's `stacked`. |
| `export_descriptions` | Descriptions (21 October), first among the ticks under Export, beside Board note on the print view and on the GETs print card, on by default (`server.export_descriptions`: on unless the request or the file says false), `descriptions` in the print view's, the GETs print's and the Word export's requests. Off, `themes.descriptions_shown` drops every label's description from the outline the print view and the Word table read, and `gets_print.page` from its GETs and PET tables. |
| `export_portrait` | Pen portrait (pbioexport, 11 November 2026), last under Export on PETs and on the print view, off by default: the participant's label and pen portrait under the head of the table of PETs, its print view, PDF and Word, `portrait` in their requests (`routes.export_portrait`, `portrait_printed`). The command line's `board export --portrait`, MCP's `portrait`. |
| `export_participants` | Participants table (pbioexport), last on the GETs print card, off by default: a first page listing each participant before the GET table, the trail or the full set, and a theme table's Word document, `participants` in their requests (`routes.export_participants`, `people_printed`). The command line's `gets export --participants`, MCP's `participants`. |
| `export_for_sending` | Leave out the board's name (For sending from 19 to 31 October, the key and the API's `for_sending` and `sending` kept), beside the two under Export and on the GETs print card, off by default, in `TH_INCLUDES` so it is drawn, saved and sent as they are, `sending` in the print view's and the GETs print's query and in the Word export's body. `server.export_sending` takes the request's value, else the settings'. `themes_print.page` then leaves the board's name off its foot and titles the page by the case alone (`title_of`), which names the PDF the browser saves, `themes_word.file_stem` names the document `<case>.docx`, `free_name` putting the date in brackets after it when taken, and `gets_print.page` leaves the board off its head, its PET tables and its title. The foot is kept in all of them. |
| `minimap` | The minimap's card at the bottom right of the statements screen's transcript column (16 October, a card since 17 October), `auto`, `on` or `off` since 17 October, later, `auto` by default, so a file without it reads Auto, an old true Auto and an old false Off. The View menu and Settings' View both set it, and `api_settings` saves it through `minimap_mode`. |
| `round_minutes` | The transcript minutes in a round, 10 by default. |
| `daily_target` | The rounds a day the target asks for, 2 by default. |
| `corpus` | A markdown file of statements under one heading per source, one pool of the examples rail. Empty by default. |
| `corpus_exclude` | The sources left out of the corpus. |
| `gravity_reference` | A finished workbook whose statement column is the register anchor, the other pool, and the one Examples from this project only keeps. Empty by default. |
| `nudges` | A switch for each nudge on a statement, `length`, `lead`, `quote`, `semicolon`, `emdash`, `arrow` and `readsas`, all on by default. |
| `ai_suggest` | AI features, the one switch for every AI feature in the app, off by default, so a new install starts with it off and a file that has it keeps its value. Off, the page hides every AI part (`aiOn` and `aiPage` in `app.js`, `data-ai` in the markup, `data-ai-set` in Settings) and `/api/suggest`, `/api/themes-ai` and `/api/gets-ai` refuse. A file that still has its old name, `haiku`, is read by it, and a save drops the old key. |
| `ai_prompt` | The system prompt of a suggestion, a template with `{research_question}`, `{guidance}` and `{examples}`. Agents read and set it through `settings --ai-prompt-file` and `--ai-prompt-default`, MCP's `settings` and `settings_set` (`ai_prompt`, `ai_prompt_default`), saved through `api_settings` as the page's Save saves it, the default put back as the page's Put the default back button does it, by writing `statement_prompts.DEFAULT_PROMPT`'s text. Only with his request in `--note`, an empty text refused, area 327. |
| `ai_provider` | `anthropic`, the default, `local` (Ollama), or since aiwire (8 November 2026) one of the OpenAI-style providers: `mistral`, `gemini`, `openai`, `azure`, `other` (Another service, by its address) or `lmstudio`. |
| `model` | The Anthropic model, `claude-haiku-5-5` by default. |
| `local_url` | Ollama's address, `http://127.0.0.1:11434` by default. |
| `local_model` | The Ollama model, empty until one is chosen. |
| `lmstudio_url` | LM Studio's address, `http://127.0.0.1:1234/v1` by default (aipage, 8 November 2026), Settings' Address under LM Studio, as `local_url` is under Ollama. One that is not https or http on this computer is passed over for the usual one. |
| `ai_address`, `ai_deployment`, `ai_api_version` | Azure OpenAI's and Another service's address, Azure's deployment and its api-version (`2024-10-21` by default), all empty or default until set. An address is taken only as https, or http on this computer (`address_ok`). |
| `other_model`, `ai_models` | The model Another service is asked, and the model each of the other OpenAI-style providers is asked, by provider (`{"mistral": "..."}`), the preset's own when none is chosen. Never a key: each provider's key is its own keychain item (`MISTRAL_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`, `AZURE_OPENAI_API_KEY`, `IDIOGRAPH_AI_KEY <host>`), never a `.env`. |
| `pets_provider` | The PETs screen's own provider, `anthropic` or `local`, and empty for the Experiential statements one, the default. |
| `pets_model` | The PETs screen's own model, set with `pets_provider` and empty with it. The PET and GET titles ask it, and the test bench never does. |
| `themes` | Until 11 November 2026 the PETs screen's own settings, `cap`, the most PETs a New AI board proposed. A file that holds it keeps it, and nothing reads it. |
| `celebrations` | Celebrations, on by default: the confetti, the count, today's haul on a break and the statements left on the PETs screen. Off turns them all off, and Sound with them. Since 20 October kept true while any of `celebration_screens` is, for a page or an app from before, and Sift's and Trace's one switch. |
| `celebration_screens` | Celebrations by screen since 20 October, `{"statements", "pets", "gets"}`, each on by default. A file without it reads all three as `celebrations` says (`celebrations_of`). The page reads the one of the screen in front (`cheerScreen`, `cheerOnFor`). A save of `celebrations` alone sets all three. |
| `sound` | Sound, off by default: a soft tick on a decided turn and the chimes that go with the confetti, made in the page with the Web Audio API. It plays only with `celebrations` on. |
| `databases` | Sift's databases, his own list under Sift in Settings, empty by default and in his order: each `{"source", "how"}`, `source` a database Sift knows or `other` with its `name`, `platform`, `ebsco`, `ovid` or `proquest`, for PsycInfo and CINAHL, and `how`, `api` or `export`. Never a key, which the keychain holds (see `sift_search.save_key`). |
| `sift_email` | The email Unpaywall asks of Sift's Find open-access PDFs, empty by default, given once under Sift in Settings and saved by `/api/sift`'s `email`, `save_sift_email`, every other setting as it was. |
| `zotero` | The Zotero library Sift's sync goes to, `{"library": "user", "group_id": ""}` by default, `library` `user` for his own, the key's owner's, which the sync reads from the key's own record, or `group` for a group's by `group_id`, digits alone, a `user_id` an older config holds passed over, written by Settings' Save through `sift_zotero.clean_settings`. Never the key, which is in the keychain under `ZOTERO_API_KEY`. |
| `quit_when_closed` | Quit Idiograph a few minutes after its last tab closes, the tick at the end of General, on for a new install, so a file without it reads on (16 October). `idle_quit` reads it at every look, so a Save holds at once, and off the server runs until Quit. |
| `feedback_url` | Written by hand alone: an http or https address that takes the place of `FEEDBACK_URL` for Send feedback on this machine. |

**The recent list.** `state.json` beside the app, `{"recent": [...]}`, newest first and eight at
most, each entry the workbook's `path` from the repo root, or from the app's folder in a downloaded copy, its `name`, the `case` by its pseudonym,
and `opened`, the time in seconds. `/api/open`, `/api/create` and `/api/themes` put the case at its
head, `/api/themes` unless asked with `beside`, for the board shown beside the GETs canvas, which is
not an opening. Of two annotated workbooks in a case the home screen's row takes the one nearer the
head. An older entry still carrying a folder's second name, or a `screen` from a build from before,
loses it the next time a case is opened. It is gitignored. The demo never enters it, and a run with
`--root` keeps its list in memory and never reads or writes the file. `sift_reviews` beside `recent`
is the list of reviews, newest first and sixteen at most, each `{"folder", "opened"}` and `name` when
he gave one on opening it, and `run` in its entry, the folder name of the run whose screening he
opened last, which Sift's read keeps there and never in the review's folder, which the home screen's
Sift section lists as Sift projects, `review_rows`, each with `second`, its second
screener settings, kept in its entry as `name` is, and `screening`, the
screening its Screening step opens, for Settings, and `run`, that run's name and counts. Until it is
first written it is read from the two lists before it, `reviews_old`: `sift`, the screenings opened,
a run's folder taken as the review above it, and `sift_searches`, the review folders whose searches
were opened, newest first and each folder once, and the first write takes both away.
`trace_projects` beside them is the list of Trace projects (15 October), newest first and sixteen at
most, each `{"folder", "opened"}` and `name` when he gave one, which the home screen's Trace section
lists, `trace_rows` in `apps/trace/trace_routes.py`.

**A review.** A review is one folder: one holding `search_plan.json` and its runs under `runs/`, or
one holding `screening.csv` alone, a screening with no searches, which `has_searches` tells apart.
`review_of` finds the review a folder is or sits in by that layout alone, `newest_screening` the
newest run holding a screening, in the order the runs were made, and `screening_of` the screening
its Screening step opens: `kept_run`, the run in its entry while it holds a screening, else the
newest, so a new run never takes the step over by itself. `review_view` is what both screens draw
the review's steps from, its name, whether it has searches, that screening and `opens`, its run's
folder name, and for a screening a run holds `run`, its folder name, and `label`, its name in words
with its draft mark, `sift_search.run_title`. The
name is the one he gave on opening it, else the plan's own, `sift_search.own_name`, else the
folder's. Every route on a review's files is guarded by the list: `review_folder` refuses a folder it
does not hold, `sift_folder` a screening whose review it does not hold, through `review_holding`,
which takes a run's folder by the review above it, and `search_folder` a review with no searches as
well, so a screening alone never gains a plan. Sift's New project, `/api/sift-review`'s `new`, checks the
folder in `new_review_place`, picks the folder in `review_target`, the one given when it is empty and
else a new one inside it named for the review, and writes `search_plan.json` through
`sift_search.new_plan`, the name, the question and no version yet, in `make_review`. `read_file`
keeps the name and question through every later write. Sift's Open project folder, `open`, takes the folder through
`review_to_open`, which reads the plan or the screening to be sure it opens and writes nothing, and
for a folder that is no review `reviews_inside` gives the review folders directly inside it, one
opened at once and several raised as `SeveralReviews`, which `folder` answers as `choices`. The
page draws the cards in `drawSiftHome`, their line in `reviewLine`, which the suite runs in node, and
the card in `openReviewCard`, `rvMake` opening the project it makes or opens through `rvShow`, and
any line the card said cleared as a field changes, and `sift_search.js` holds the review's way in,
`rvOpen`, and its steps,
`rvHead` and `rvStepsDraw`, the step each review was left on kept in this browser under
`idiograph-sift-step` (see Steps and sidebars for the steps as one row since 12 October).

**A screening.** Sift's files sit beside `screening.csv` in the folder he chose, and `sift.py` alone
reads and writes them, for the server and the command line alike: `screening.log.jsonl`, one JSON
line an act, appended and never rewritten, the CSV's decision columns written afresh from it by
rec_id after each act through a temporary file and `os.replace`, `screening.lock`, the lock every
act holds and any outside writer takes the same way, `reasons.csv`, the codes, `log.csv`, the
search tool's record, read for the counts, `pdfs/`, the records' PDFs, a dropped one written there
through a temporary file, and one found in an earlier run by `gather_pdfs` named in `pdfs/.found.json`, `screening.counts.csv`, which Export writes, `prisma.md`, the PRISMA flow
as Mermaid, written by `write_prisma` after every act that moves it and on opening, and
`sift.json`, the screening's AI switch and prompt, which `sift_ai.py` reads and writes. The flow is
`prisma_source`, built from `counts` alone, whose `flow` adds the records from other methods, the
duplicates and the reports with no PDF. `searches` splits `log.csv` into `runs`, a database met again on
the same day beginning the next run's rows, so two runs of one day are two searches, which `count_rows`
numbers. **The active run alone (16 October).** Every figure of the flow is the active run's, as
PRISMA 2020's diagram reports the review's own search and not every trial run before it: `own_search`
takes the run's own rows of `log.csv`, those after the `searches` count `run.json`'s `carried` keeps
of the earlier runs at its head, else its own day's, and every row of a run that follows none, and
`earlier`, the records carried and not found again. `flow_of` leaves those records out, keeps the
records from other methods, sums the run's own rows by database, takes the duplicates as its records
saved less its records from databases, and counts the stages afresh through `stage_counts` over what
is left, with `included_counts` for the last box, so `flow` carries `search`, `stages` and `records` of its
own. A screening of no run whose `log.csv` holds more than one search has no active run, `active`
false, and its first box says `NO_ACTIVE`, "No active run to count", with no sum and no duplicates.
The screen's counts, `counts`' `stages`, and the export's rows, with `included` for its studies, stay
the whole screening's. Sift's own proposals go in its `ai_` columns through
`write_ai`, and the review's side writes its own through `propose_review` and adds records through
`add_records`, all under the lock. His own fields are columns of Sift's own, written by `set_field`,
and his columns are added, renamed and removed by `column`, each a line of the log under the lock,
the review's columns never written. `guess_participants` reads a count from the abstract by pattern
on every reading and writes nothing. `sift.json` also keeps the table, its columns in his order and
his own columns, through `save_view` and `column`, every other key it holds kept, and its filters
and find boxes' words, `filters` and `find` under `table`, which `kept_filters` cleans to the
columns the table has, a slider's column, `RANGE_COLUMNS` and his Number columns by `range_keys`, holding its two ends and `none` and any
other a list of ticks, an empty one taken away, `column` moving a kept filter to a renamed column and
dropping it with a removed one, `TABLE_COLUMNS`
and the page's `SF_COLS` starting the abstract hidden, a list he saved kept as it is, and `numbers`,
each record's number by rec_id, `numbers_of`, given in rec_id order, `natural`, by `keep_numbers`
when the screen opens the screening, and to a record added later the next after the highest ever
given, so no sort, filter or new record changes one, though since 13 October the screen shows the ID in
its place. `record_view` gives it as `n`, and `url`, the
`url` column as a link when it holds one address. The table's `view` it still keeps is no longer
read, since the screen always opens on the table. A reason that names two codes, an older line's or
cell's, reads as its first, `first_reason`, in `state_of`, one reason a record. The table sorts and
filters in the page, the family's `tbSortRows` and `tbFilterRows` read through Sift's `sfRead`, which need no page and which the suite runs in
node, the ID's column, `SF_ID`, ahead of every other and in no list of columns (the number's until 13
October), and draws every
row as text, each drawn again alone when its record changes, its decision a pill, `sfPillHtml`, in
the stage's words, `sfWords` from `SF_WORDS`, as `sfPillSet` gives a record's head, a proposal and
the bench, and the filters' Decision group its choices (see The decisions' words), the
reason for No or Exclude a pill of its own, `sfReasonPill`, a record's PDF a red pill, `--pdf` with `--on-pdf` on it, no link,
each database a pill in its colour, `sfDbPill`, the colour by its name through `sfDbKey`, its own
for the databases Sift knows, `SF_DB_COLOURS`, else one of six by the name, the tokens `--db-*` never
red, and a publication type as pills, `sfCatPills`, the review's columns through `sfReviewCell`. The
runs' rows on Search strategy call `sfDbPill` too. The headings only sort. The filters are a
sidebar, `#sf-facets`, at the table's left, opened and shut by `sfFacetsOpen` and kept in this
browser as `idiograph-sift-filters`, open at first above 899 pixels. `sfGroups` makes a group for
each column a pick can filter, `sfPickable`, in the columns' order, the review's columns when they
hold 2 to 30 values and the journal and `pub_type` always, `SF_PICK_ALWAYS`, a search's name and a
review's value by `sfPickKey`, case and spacing set aside, a list in a cell parted by `sfParts` and
labelled in the words most records write by `sfWritten`, the PDF's headed by `SF_GROUP_WORDS` and the
abstract's source with its ⓘ line from `SF_GROUP_ABOUT`. Year, Cited by, the participants and the
rating, `SF_RANGES`, are sliders: a group with `range`, `low` and `high`, its filter `{from, to, none}` read
by `sfRangeHeld`, either end open as null, `sfRangeSet` holding an end at the round's own limit open,
`sfRangeMove` drawing a handle's move at once and setting the filter when it is let go, and
`sfRangeBars` its chart, its bars from `sfBarSpans`: the year's five years each from a year that ends
in 0 or 5, or ten, 25 or more, `SF_BAR_YEARS`, when five would make more than `SF_BARS`, the
participants' five each to 50, `SF_BAR_FIVES`, then `SF_BAR_WIDE` and 1001 and over, and the rating's
a star each, each bar kept to the round's lowest and highest and carrying its run in words, `label`,
which its hover says. The year's and the participants' handles stand on a track laid out by those
bars (12 October), `sfTrack`, each bar an equal stretch of it, the runs carried in the group's
`data-runs` and read back by `sfTrackRead`, the rating's and a slider of one bar left a whole number
a step. `sfTrackAt` places a number on it, the lower end at the start of its place in its bar,
`sfTrackBar`, and the upper at the end, `sfTrackSnap` takes a handle to the nearest edge it may stand
at, `sfTrackEdge` gives that edge's number and `sfTrackStep` the next edge a bar on or back, which
`sfHandleKey` takes for the arrows, Page Up and Down, Home and End, ahead of `sfKeyDown`'s own.
`sfRangeMove` reads the moved handle's end from its place and the other's from its box, so a number
typed between two edges keeps its place, and a handle dragged past the other stops at the other's
bar. The handles say their number through `aria-valuetext`. `sfPicked` gives the
choices a record stands under, `sfPasses` whether it passes a group, `SF.filters` holds each group of
ticks as a list, `sfTicksRead` reads a filter held in an older form and lets go what no group offers,
and `tbFacetCounts` counts each choice over the round's rows with every other group's filter and its
own set aside, through `tbEachOpen`, as `sfRangeBars` does. A group of more than four shows four,
`TB_FACET_SHOW`, and one of more than ten a find box, `TB_FACET_FIND`, matched by `tbFindMatch`.
`sfFacetsDraw` draws the sidebar with the table, again only when it changed. `sfFacetsMark` gives
the toggle over the sidebar the count of groups set in its word and its name, Filters (2), and shows
Clear all beside it while anything is set.
`siftOpen` reads the filters `sift.json` keeps through `sfKeptRead`, `sfTicksRead` with every group
taken as fixed over every record, so a tick no record carries is let go, and the find boxes' words
through `sfFindRead`. `sfFiltersKeep` writes them back through the `view` route, queued as every act is, when `sfKeptJson`,
the two in one line in order, differs from what was kept: at once after a tick, a slider, a Clear, a
round or a column, and `SF_KEEP_WAIT` after the last letter typed in a find box, or as the screen is
left. Clear all clears the find boxes too. A
double-click or Enter on a row opens the record, `sfSetView`, the second press's `mousedown` kept from
selecting a word, and its way back or Esc returns to the
same row, the filters and sort untouched. `sfNoteSave` holds the note in the record at once, as
`sfDecide` holds a decision, and gives the box the note as kept once its answer lands, should an
earlier act's answer have drawn the record over it. The foot bar's matched and overruled show once
a decision meets a proposal, and AI propose for the rows shown says Proposing and, pressed again,
leaves the rest for later, the `plan` op taking the table's rows as `ids`. The suggestion boxes,
`#sf-proposal` and `#sf-proposal-2` (14 October), draw `sfSuggestions`, a record's proposals with an
AI's dropped while the switch is off, each under a title from `SF_SUGGESTION` by its `kind`, which
`sift.made_by` gives from the source and the `proposed_by`, `ft_proposed_by` or `ai_proposed_by` cell,
`rules`, `model`, `unstated`, `sift` or `sift_model`, the sparkles put on `#sf-prop-spark` as Sift starts
and shown for an AI's alone. Accept suggestion, `#sf-take`, coloured by `data-decision`, calls
`sfTakeProposal(i)`, as Enter calls it for the first box, which calls `sfDecide` with the suggested
decision and reason, so nothing tells it from a press of that decision. `sift.decide_in` writes
`suggestion_match` into every `decide` line, the agreement between the screener's decisions and the
suggestions, `matched_suggestion`, `suggestion_source`, `suggestion_by` and with two shown
`other_suggestion`, from `suggestions_shown` with the server's AI switch, `ai_on`, and
`suggestion_words` words it for `show`. `sift_ai.propose` gives `write_ai` the model, `route_model`,
for `ai_proposed_by`. The counts and the flow read none of it, so a decision by Accept suggestion
counts as any of his. His key excerpts (14 October) reuse Experiential statements' `quote.js`: `sfExTake`
turns the selection in `#sf-title-text` or `#sf-abstract` into a piece, `{ in, start, end }`, on mouse up,
in place of the pieces or after them with Cmd or Ctrl, `sfExMerged` lays the title and the abstract end to
end with a NUL between them, `SF_EX_GAP`, so `mergePieces` sorts and joins the pieces of both and never one
across them, and `sfExWords` is `assembleQuote` without its quotation marks. H calls `sfExKeep`, which adds
the excerpt to the record at once and sends the `excerpt` op, `act` add with the stage and the pieces, and
Remove in `#sf-ex-list`, drawn by `sfExList`, sends remove with the place and the words. `sfExSpans` gives
`sfMarked`, which lays any number of classed spans over a text since then, the marks of the excerpts whose
pieces still read as their words, `sfExShown`, as `sf-excerpt`, hidden with the grounds' Hide, and the
pieces being built as `sf-piece`, which always show, and `sfGroundsLine` names Key excerpts beside the
grounds in `#sf-gline-ex`. On the server `sift.excerpt` checks the pieces against the plain title and
abstract with `excerpt_pieces`, in the text's order and within it, works out the words itself and writes
the `excerpts` column, one of `OWN_COLUMNS`, as JSON in ASCII alone through `excerpts_cell`, read back by
`excerpts_of`, with one `excerpt` line of the log carrying no stage, so `read_log` and the counts never see
it. Undo reads `undo_lines`, his acts and these lines, so `undo_target` reaches the newest of a decision, a
note and an excerpt, and `undo_excerpt` puts the cell back as it stood, its `undone` naming the excerpt so
`sfUndo` marks its words again after one kept is taken out. `excerpts_text` gives the included records' CSV
its last column, and the command line's `show` lists them through `excerpts_said` and words their lines
through `excerpt_said`. The line at the foot of every screen, `.toast` in `style.css`, is centred by its
margins since 14 October, since the `rise` it comes in on ends at no transform and so undid the
`translateX(-50%)` that centred it before, cutting it off at 360 pixels. The reasons stand over the screen in `#sf-why`, drawn by
`sfReasonsDraw`. The page draws the flow with the vendored Mermaid,
`static/vendor/mermaid.min.js`, 11.14.0, in the sidebar `#sf-side` while it is open, which
`sfFlowOpen` opens and shuts, kept in this browser as `idiograph-sift-flow`, and given the colour
tokens of light or dark as they stand, drawn again when they change. The grounds' Hide is kept as
`idiograph-sift-marks`. Add PDF and a PDF dropped on the record go through the `pdf` op, as a dropped
one always has. `sift_oa.py` is Find open-access PDFs: `plan` the records with no PDF, and `find`
one record looked up by its DOI in OpenAlex and Unpaywall, or in OpenAlex by its exact normalised
title and year, `norm_title`, the places in `places`' order tried, a download kept through
`sift.save_pdf` without `replace` only when `is_pdf` and `carries_title` hold of its
`first_page_text`, read with the standard library from the page tree's first page, its content
streams inflated and its strings read through each font's ToUnicode map. The server does the
looking outside its lock and the keeping under it, and the page asks one record at a time,
`sfOaRun`. `IDIOGRAPH_SEARCH_STUB` sends its requests to a stub, the host at the head of the path,
`stubbed`, and `fetch` is a parameter the suite fills. The bench is `sift_ai.trial`, `asked`
without the write, through the `try` op, the page's `sfBenchTry`. Sift's own settings card is gone
(9 October): its cog opens Settings on Sift, where a Sift project's parts follow Databases, the
projects' row `#sfp-pick` drawn by `sfpLoad` and `sfaPick` in `app.js`, the screening chosen
`sfaFolder()`, PDFs, `sfOaShow` in `sift.js`, and with the switch on the AI proposals, `sfaShow`,
and the bench, `sfBenchFill`, its records the screen's own for the screening open and the `titles`
op's for another. `sift_zotero.py` is Export to Zotero, Sync to Zotero until 12 October, the card
`#sf-zot` from Export's menu,
`sfZotOpen`, `sfZotPlan` and `sfZotGo`, through `/api/zotero`, its sync on a thread of its own,
`zotero_sync_thread`, kept in `ZOTERO_SYNCS` and asked after by `progress`, under `zotero.lock`
beside the CSV. Each record's item key goes in the CSV's `zotero_key` through `sift.write_zotero`
under the screening's lock, which `record_view` and the table's extra columns leave out and `reset`
keeps. Zotero under Sift in Settings is `zotLoad`, `zotSaveKey`, `zotClearKey` and `zotCheck`, the
check asked as soon as a key is saved or the library changes, its library and group id sent with Save
as `zotero`. `reset`, Start again, starts a
screening again under its lock: the log moved whole by `os.replace` into `_Archive/` beside the CSV
as `screening.log (<date-time>).jsonl`, `archive_name`, then `RESET_COLUMNS`, the decision columns,
his own and Sift's AI proposal columns, and every `col_` column emptied, and the counts file, when
there is one, and `prisma.md` written afresh. `sift_search.begun` takes a run started again, a
carried one too, by what is left in it. The contract is in
[docs/agents.md](agents.md), Sift.

**Round 2 of the review (12 October).** Search strategy's plan holds `reasons`, each stage's
exclusion reasons as `{code, meaning}`, cleaned by `sift_search.reasons_of` from the screen's lines
or from a list, `REASON_STAGES` `ta` and `ft`, part of the version as the blocks are, written into
`search_plan.md` under Exclusion reasons and into a new run's `reasons.csv` by `reasons_csv` in
`assemble` when the review folder holds none of its own and the run has none, a run's own never
written over. The screen draws them with `sfsDrawReasons` and `sfsReasonLines`. `how_of` sends a
database his list does not hold, and every database while the list is empty, by its default, by API
when it is keyless or its key is saved, else by export, and a row of the list decides for its own
database (12 October), and the screen's `sfsAccRow` takes the same. `sfsRows` is the databases in one list in the plan's own order, his
list's marked `.sfs-mine`, and `sfsShownOrder` follows it. The review's research question is
`sift_search.own_question`, or the one he gave, kept in its entry in the list by `edit_review`, read
by `review_question`, which `review_view` and `review_rows` send as `question`, the card under its
name and `rvHead` at the head of Search strategy's plan as `#sfs-question`, in `#sfs-question-part`. `forget_review` takes a review out
of the list. Under Sift in Settings `sfpLoad` lists every project whose folder is there, each
`{review, folder, name, question, root}`, `sfpShow` chooses one, `sfpOwnDraw` and `sfpKeep` its
Project part, `sfpSaves` what Save sends as `rename` and `second`, and `sfpRemove` Remove from Idiograph. In the
screening `sfTypeWord`, `SF_TYPE_WORDS`, `sfTypeParts` and `sfIsType` give a
publication type in plain words in the pills and the filter, the CSV never changed. `SF_TADEC` and
`sfStageCols` add At title and abstract at full text to the table and the filters, its filter kept
in sift.json as `STAGE_FILTERS` lets it be. `#sf-undo` at the foot calls `sfUndo` while `SF.undo`
names what it takes back. `sift.export_included`, `included_ids`, `ris_text` and `included_csv`
write `INCLUDED_RIS` and `INCLUDED_CSV`, the type by `sift_zotero.item_type` through `RIS_TYPE` and
the authors by `sift_zotero.creators_of`, and `sfIncluded` asks for it, the button off while no
record is included at full text. The title bar's tools are `.bar-tool` buttons with their `.bar-word`
(see One title bar). The flow's Records screened
counts every record at title and abstract, `ta["records"]`, and `sift_oa.plan` looks only for the
records that passed title and abstract, `in_stage` at full text.

**Screening from use (12 October).** From Adam's own screening of a trial run. The title bar's
writing and sending tools are one Export, `#sf-export`, whose menu, `#sf-export-menu`, stands outside
the bar so the bar's own scroll never clips it, placed under the button by `sfMenuOpen`: Export to
Zotero, `#sf-zotero`, Export included records, `#sf-included`, off while none is included at full
text, and Export PRISMA counts, `#sf-counts`, the `export` op as Write the counts was. `sfMenuTake`
shuts it before an item's work, `sfMenuKey` takes the arrows, Home, End, Esc and Tab ahead of every
other key of Sift's, and a press beside it shuts it. The stages, later that day steps of the
review's one row (see Steps and sidebars), open at title and abstract while `sfFtOn` finds no record
at full text. Filters and Columns left the bar for a strip over the table, `.sf-tv-top`: the toggle,
`#sf-facets-toggle`, with its count in `#sf-facets-word`, and Clear all at the top left, and
Columns, now Set columns, at the right. The sidebar's right edge, `#sf-facets-edge`, a `separator`,
drags its width or moves it a step for an arrow, set as `--sf-facets-w` and kept in sift.json's
`table` as `sidebar` through the `view` op, within `SIDEBAR_MIN` and `SIDEBAR_MAX`, `sidebar_width`,
by the code both sidebars now share, `sfEdgeBoot` and its kin. Each choice and group head carries its words as a
title, so a name cut short reads whole on hover. The dropdown of rounds is gone: the screen asks
`list` for `all` at the stage, `SF.round`, and Decision in the sidebar is the one filter of where a
record stands, with Differs from the proposal, `SF_DIFFERS`, while a record shows a proposal, and
Where we differ, `SF_APART`, while the second screener's side holds a difference, each read from the
record's marks, `differs` from `record_view`, his decision against `proposal_seen`, and `proposed`
and `apart` from `sfMark`, so `sfGroups` and `sfPicked` still need no page. A round the old dropdown
kept in this browser, `SF_ROUND_TICKS`, is read once into the Decision filter when sift.json keeps
none, and the card's Where we differ sets that tick. A record with nothing in a slider's column
stands under `SF_BLANK_WORDS`, No year, Unknown, Not rated or No count, and the table and the record
say the same through `sfBlankHtml`, the rating's slider now one star to five with Not rated under it,
`sfRangeValue` giving none for a record not rated. `field_cells` takes nought participants. Found by
reads Database and Rating My rating, the count's circle gone. `TABLE_COLUMNS` starts the DOI hidden
and Cited by, `cited`, shown after Year, and `table_settings` gives `defaults`, `default_columns`, the columns as they first stand for Set columns' Reset to default, `#sf-cols-reset`, waiting while they stand so, and hides the abstract and the DOI once in
columns placed before `FIRST`, `FIRST_OFF`, `save_view` and `column` marking what they write
`first`. Cited by is `cited_by`, `CITED_COLUMN`, and `cited_by_date`, `CITED_DATE`, in `SHOWN`, read
by `cited_of` into the record's `cited` and `cited_date`, a slider with its bars from
`SF_BAR_CITED`. A run fills both in `fill_from_openalex`. For a screening made before, Find
citation counts under Sift in Settings, `sfCiteRun`, asks the `cited_plan` op,
`sift_search.citation_plan`, then the `cited` op fifty at a time from `at`,
`sift_search.find_citations`, which asks OpenAlex for `CITED_FIELDS` outside the server's lock and
writes through `sift.write_cited` under it, Sift's own two columns alone. `file_reasons` reads the
review folder's own `reasons.csv`, `state` sends it as `reasons_file`, `sfsDrawReasons` shows it in
place of the fields, and `with_file_reasons` gives the plan its reasons in `save` and `register`. A
drop on Search strategy names the run the screen shows, `run`, and `drop_target` keeps it there,
refused when a later run of its day has been made since, so a drop never goes into an earlier run
of the day, and with none named the day's newest run, as before.

**Steps and sidebars (12 October, later).** From Adam's use of the screen above. The review's steps
are one row on both Sift screens, `rvStepsDraw` in `sift_search.js` drawing `#sf-steps` and
`#sfs-steps` from `rvStepsHtml`: Search strategy, `data-step="searches"`, while the review has
searches, then Screen by title and abstract, `ta`, and Screen by full text, `ft`, each stage named with its
verb (12 October, Adam's words), each stage's count of records in
`.sf-step-c`, the one shown `aria-current="step"`, a chevron, `.sf-step-sep`, between each. A step
that waits is `aria-disabled`, so it keeps the focus and its reason as a title, `RV_TA_LATER` until a
run has a screening and `RV_FT_LATER` until a record has passed title and abstract. The row is built
again only when its markup changes, `RV_DRAWN`, so a step keeps the focus. On Screening `sfBar` draws
it with `SF.stage` and the counts the screen holds, and a stage chosen there is `sfStageTo`. On
Search strategy `rvHead` draws it, `rvStageCounts` asks the `counts` op of the screening the steps
open, which only reads, and `rvStep` opens that screening at the stage chosen through `siftOpen`'s
third argument. Under 760 pixels the row takes a line of its own in a bar that wraps. PRISMA flow,
`#sf-flow-toggle`, left the title bar for the line under it, `#sf-tv-top`, now over both views at
the head of `.sf-main`, beside Set columns, `#sf-tv-cols`, Columns until then, whose card says Set
columns too. The line's `data-view` hides the table's own tools, `.sf-tv-only`, on a record and on an
empty full text, and the views and the flow's sidebar stand in `.sf-views`. Both sidebars drag by one
set of functions, `SF_EDGES`, `sfEdgeWidth`, `sfEdgeKeep`, `sfEdgeBoot` and `sfEdgeKey`, each edge's
`way` saying which way it widens: the filters' `#sf-facets-edge` at their right, `--sf-facets-w`, and
the flow's `#sf-side-edge` at its left, `--sf-side-w`, 240 to 720 pixels and 300 at first, the
diagram taking the sidebar's whole width over the width Mermaid sets. The view op's `sidebar` takes a
number, the filters' width as before, or a record of `filters` and `flow`, `sidebar_widths`, and
sift.json's `table` keeps `flow` beside `sidebar` within `FLOW_MIN` and `FLOW_MAX`, which
`table_settings` gives back. The Decision group's and At title and abstract's choices carry `dec`,
drawn by `tbChoiceHtml` as `.sf-decdot` in the colour of the decision's pills. A slider chart's bar
carries its run and count in `data-tip`, and `sfBarTip` shows it in `#sf-bar-tip`, fixed in the
window over the chart, the bar found from the pointer's place across the chart so the gaps and a
bar's empty top count too, hidden as the pointer leaves, as the sidebar scrolls and as it is drawn
again. A click on a row opens its record, `sfOpenRecord(true)`, while a star, a guess, a link and a
cell of his do their own work, a press that began while a cell was open, `SF.tvTyping`, ends the
typing alone, words selected across the row open nothing, and `SF_SECOND_PRESS` swallows a
double-click's second press on the record it opened. A record opened is an entry of the browser's
history, `sfHistoryPush`, its record kept by `sfHistoryKeep` as he walks, the way back and Esc going
`history.back()` through `sfToTable`, and `sfPopState` showing the table or the record.
`sfHistoryDrop` lets go an entry left from before as a screening opens or is left. Each decision's
hover is `SF_SAYS`, by stage, Maybe's among them.

**A second screener (12 October).** `sift_second.py` is the second screener's side, PRISMA 2020 item
8. The settings are the project's, `second` in its entry in `sift_reviews`, cleaned by `settings_of`
and kept by `save_second` through `/api/sift-review`'s `second`, which `remember_review` keeps, and
`second_of` passes them to every act that needs them. Every act is one line of the screening's log,
`act` `second` with its `change`, which `sift.read_log` passes over, so no line of theirs moves a
decision of his: `draw`, `workbook`, `decision`, `unblind`, `agreement`, `reply`, `outcome` and
`third`. `Two` reads them once. `calibration` is the first draw's list, or before it the first of
the stage's records by number. `draw_in` draws `size_of` the `pool_of`, the stage's records less the
calibration and earlier draws in number order, by `redraw`, `random.Random(seed).sample`, the seed
from `SystemRandom` and the pool logged, so it repeats. `waits` holds a draw back until the
calibration records are decided and, at full text, every record at title and abstract. `sift.decide`
is split, `decide_in` writing one line under a lock its caller holds, and takes `second`: `marks`
adds `calibration` and `after` discussion to his line, and `settle` writes a draw's `unblind`, his
decisions as they stood, once he has decided every record of it, his Maybe at full text counted
undecided by `his`, and its `agreement` once theirs are all in, `agreement` working the kappa on going
forward against exclude, None when chance agreement is whole. `undo` settles too. `second_book` and
`differences_book` write the workbooks with openpyxl, `put` keeping text as text, no fill ever, the
sheets protected with no password by `guard` and the structure locked, `open_cells` the only cells
that take typing, `dropdown` the lists, the Reason list read from column D of the very hidden
`mark_sheet`, which names the kind, stage, screening, seeds and records that `take_back` checks
through `read_mark`, the workbook's keywords standing in when the sheet is gone. `unique_path` never
writes over a file, and `copy_pdfs` fills the full text folder. `take_decisions` and `take_replies`
take the rows in, `write_mirror` writes `screening.second.csv`, and `settle_one` sets a difference's
outcome, a decision it changes going through `decide_in` with `after`. `view` is the screen's side,
blind until a draw is unblinded, `differences_of` the round `apart`, Where we differ, `hidden_lines`
what `sift.history` leaves out, and `report`, `count_rows` and `flow_lines` what `counts`,
`count_rows` and `prisma_source` add, the flow's `twota` and `twoft` boxes. `eligibility_of` in the
server reads a run's plan version for the workbook's first sheet. On the page `sfTwoOpen` and
`sfTwoDraw` draw the card `#sf-two` from `#sf-two-btn`, `sfTwoMake`, `sfTwoDifferences`,
`sfTwoFurther` and `sfTwoTakeFile` its acts through the `second` op, a dropped `.xlsx` going to
`sfTwoTakeFile` from anywhere on the screen as `sfXlsx` tells it, and `sfTwoRecDraw` the record's
`#sf-two-rec` and `#sf-cal`, its outcomes through `sfTwoOutcome`. Under Sift in Settings
`sfpTwoDraw`, `sfpTwoShow`, `sfpTwoRead` and `sfpTwoKey` draw, read and compare the part.

**A review's searches.** `sift_search.py` alone reads and writes a review folder's search files, for
the server and the command line alike, under `search.lock` in the folder: `search_plan.json`, every
version of the plan kept whole, a version once registered never written again, `search_plan.md`,
the newest registered version as Markdown, and `runs/<date>/`, a run, a later run that day
`runs/<date>-2/` and up, every run kept, `next_run` naming a new one, `run_parts` and `run_said`
reading a name as its day and number and in words, 9 October 2026, run 2, and `run_dirs` listing
them in the order they were made, its `raw_<source>.json` for
each database, `log.csv`, `screening.csv`, `reasons.csv` from the folder's own, `run.json`, the
version it ran, each database's state and how it went and the exports with the version each was
dropped under, and `<source>.ris`, `<source>.bib` or `<source>.csv`, an export dropped on the
screen, `read_bib` reading BibTeX. A run that the
page starts goes on a thread of its own in the server, `SEARCH_RUNS` holding its state for
`progress`, and holds the folder's lock and never the server's. `run_target` chooses the folder a
run writes, under that lock: a new one every time, but for the day's newest run when a dropped
export began it, `waiting_for_run` in its `run.json`, or in a folder from before that mark a
database still waiting, and Run has not run it, of the same version and not begun, which Run
completes. An export dropped goes to `day_run`, the day's newest run. A run folder holding a
decision, a proposal, a screening log or a PDF is never written again, `refuse_begun` saying so in
one line that ends Run makes a new run. A run of a version not yet registered keeps `draft` in
`run.json`, and `run_lines` and the screen name it as from a draft, not registered, `draft_said`.
A run that follows an earlier one, `follows`, the earlier run's folder name, which `check_follows`
refuses when it is the run itself, a later run by `run_parts` or a run with no screening, is
written by `carry`: the earlier screening read under its own lock
when it has one and never written, its records the anchors of `merge`, `numbered_on` giving the new
ones the rec_ids after its highest, `carried_text` its CSV with every earlier column kept, and
`carry_log` the later log, a `follow` line and then `carry` lines through `sift.append`, each with
`from`, the earlier run's day and log line, before `sift.rebuild` writes the decisions into the CSV.
His settings and the PDFs are copied, `log.csv` holds the earlier rows before its own, and
`run.json` keeps `follows`, the counts, and `carried`, the carry's log lines, its PDFs, the
CSV's SHA-256 and `searches`, the earlier run's rows at the head of `log.csv`, so `summary` tells
the run's own rows from them though both runs fell on one day, and `begun` and `changed_since` find
a folder holding the carry alone unbegun and `clear_carry` takes it away before an export dropped
on it writes it afresh. Since 23 October a run and a drop take the run folder's `screening.lock`, and
a drop the lock of the run it follows (`writing`, `followed_lock`), before they remove or write
anything in the folder, so one refused BUSY leaves every file there as it was. `carry`, `assemble` and
`sift.gather_pdfs(..., held=True)` take no lock of their own, the caller holding them. `follow_choices` and `default_follows` give the earlier runs with
decisions, newest first, an earlier run of the same day among them, which the screen offers and the
command line and MCP take when `--follows` or `follows` is left out. The writers are `write_scopus`,
`write_wos`, `write_pubmed`, `write_epmc`, `write_openalex`, `write_ebsco`, `write_ovid` and
`write_proquest`, which `writer_for` picks for PsycInfo and CINAHL by the plan's `platforms`,
`write_embase`, `write_scholar` and `write_other`, each from the plan alone, and the merge is `merge`,
then `fill_from_openalex` and `ordered`. `fill_from_openalex` asks OpenAlex by DOI, fifty a request,
`FILL_FIELDS`, through `works_by_doi`, for every record with a DOI, `asked_doi`, and takes the
abstract it lacks, where a record names one author or none, `author_names`, and OpenAlex names more,
OpenAlex's authors through `openalex_authors`, joined as `openalex_record` joins them, and each
record's `cited_by_count`, `cited_count`, with the day as `cited_by` and `cited_by_date` (12 October),
a carried record never asked, and `run.json` keeps `filled`, `authors_filled` and `cited_filled`,
which `summary` and `run_lines` say. Each follows its vendor's own help as read on 8 October 2026,
`write_proquest` now `TITLE,ABSTRACT,IF()`. `run_end` ends Web of Science's and Europe PMC's range
of years at `this_year`, the year of the run, since neither documents an open end, the day read
through `CLOCK`, which the suite stands in for. `OFFERED` holds the platforms each vendor offers now,
CINAHL on EBSCO alone, which the screen's choices take, and `RETIRED` the note under a string a plan
still writes for one no longer offered. A run, a dry run and a drop from the server or the command line
take his list of databases, `databases` in `config.json`, and `how_of` sends a database it does not
hold By API by export. Every key goes by its keychain service, `KEY_FIELDS`: `read_key` reads one
through `ai_suggest.find_key`, `save_key`, `clear_key` and `key_saved` go through `ai_suggest`'s own,
each taking the service, the keychain on a Mac and `.env` off one, and `check` sends one record's
search with it. `scrub` takes every key out of a note or an error before it is kept or shown. `openalex_params` adds OpenAlex's optional key, `OPENALEX_API_KEY`, as
`api_key` to the search and the abstract fill alike when one is saved, and nothing without it.
`IDIOGRAPH_SEARCH_STUB`, a loopback address, sends every request to a stub server and every key to
`STUB_KEYCHAIN`, a keychain in memory whose untouched services hold a stand-in, for a smoke run
alone. A plan names databases of its own as `other`, `other2` and up to `other20`, each by its name
under `others`, `is_other`, `kind_of` and `in_order` taking each as the `other` kind for its writer,
its fields and its limits, and a plan from before several still reads its `other_name`.
`benchmark_of` reads the benchmark's lines, a DOI with its title after it into `benchmark_titles`, and
`benchmark_titles` gives each DOI's title, the plan's or the first a run's raw files give, newest run
first, which `state` with the runs, `progress` once a run ends and `drop` send the screen. `assemble`
writes no `screening.csv` for a run that brought no records, so `newest_screening` passes it by and
the review's Screening step keeps the screening before it, and passes by a run from before that whose
CSV is a header alone, `sift.has_records`, while an earlier run holds records. `state` sends `block_problems`, each
block's own share of `problems` from `term_problems`, which the screen draws under each block as
well as under Register, and each block has its Remove at its foot, which asks first through `sfsAsk`
when the block holds terms. `sfsRunWords` names a run as the runs list does, its day and its place
that day, for the list and Keep the decisions from alike, and `sfsFilled` says what OpenAlex filled
only when it filled any, in a run's Details. `SITES` and `PLATFORM_SITES` are the pages
an export row's Open link takes him to, a link and never a request of the app's. The screen,
`sift_search.js`, draws the plan, the searches, Register and the runs as four numbered parts. Each
database's cog, on its row under Searches, draws the same access as Settings' Databases through `dbsAccessParts` and
`dbsBindAccess`, the keys through `dbsSaveKey`, `dbsClearKey` and `dbsCheck`, and writes his list at
once through `/api/databases` `save`, as Add database does. The contract is in
[docs/agents.md](agents.md), Sift's searches.

**Search strategy in one column (12 October, later still).** From Adam's use of the screen, the
two columns, the plan at the left turning into the strings at the right, gave way to one column in
the order of the work, built by `sfsBuild`. Plan, `#sfs-h-plan`, carries one tag, `#sfs-state`,
Draft or Registered with the date, `Version 2, ` before it once there is more than one version, and
`#sfs-versions` folds each earlier version, `state` sending each version's head before the newest
with `text`, its plan as `markdown` writes it. Under it Research question, `#sfs-question-part`,
then Search terms, Limits, Databases, Benchmark papers and Exclusion reasons, the reasons from the
review's own `reasons.csv` under one line with Open the file, `#sfs-reasons-open`. Searches,
`#sfs-h-strings`, is `sfsDrawStrings`: a row for each database, `.sfs-str`, its name, By API or By
export from `sfsExported`, its cog and an export's steps from `sfsSteps` in `.sfs-str-how`, its
search, Edit manually and Copy for a search Sift runs in `.sfs-str-text`, the two side by side and
stacked under 760 pixels. The plan's own list of databases keeps the boxes, the platform and In your
list, and the cog moved to the row under Searches. Register, `sfsDrawVersion` too, says in
`.sfs-reg-text` what registering does, `#sfs-register` reads Register this plan, its confirm
`sfsRegisterLine` the same, and once registered `#sfs-reg-when`, `#sfs-reg-file` with Open
search_plan.md, the `open` op, and Copy, and `#sfs-reg-next`, `state` sending `plan_file`, whether
the folder holds `search_plan.md`. Runs, `sfsDrawRun`, lists `SFS.runs` newest first through
`sfsRunRow`, each its name from `sfsRunWords`, Trial for a run whose `draft` is set or Registered
search, its counts, `.sfs-open-tag` Screening on the run `sfsOpensDay` names or Screen this run,
`.sfs-open-run`, a row for each database awaiting its export with its drop, `data-run` naming the
run so `sfsDropFile` keeps the file there, and `sfsRunMore`'s Details. New run, `#sfs-h-new`, says in
`#sfs-new-what` whether the next run is a trial or the registered search, lists each database in
`#sfs-sources`, its state while a run goes, then Run the searches and Keep the decisions from,
`#sfs-follows`, `sfsRunWords` naming each run in it. Earlier runs, Open the screening, Screening has
begun, Screening opens this one and the line at the screen's head are gone.

**Search strategy, second round (12 October, latest).** From Adam's use of the one column. Each block
in `sfsDrawBlocks` is headed `.sfs-bnum`, Block 1 and up, its name in `.sfs-bname` beside it, then
`.sfs-search-in`, Search in, `.sfs-bscope` in a boxed `.sfs-select`, over its terms. Search in, by
database, is a button, `.sfs-own-toggle`, made by `sfsToggleHtml` with `SFS_CHEVRON`, shut at first on
every block, its open blocks kept in `SFS.ownOpen`, a WeakSet of the block objects, and while shut
`sfsDiffers` gives a `.sfs-own-said` line for each chosen database whose scope differs, named by
`sfsScopeWord`. The per-database choice's first option reads Same as the block. Limits became Limits
and restrictions, PRISMA-S's item 9, on the screen and in `markdown`. A database's row, `sfsDbItem`,
drops In your list and carries By API or By export from `sfsExported` and Access not set where
`sfsNeedsAccess` finds a keyed database his list sends by API with no key saved, `SFS.keys` from the
read's `keys`. The benchmark is `sfsDrawBench`, a `.sfs-paper` row for each DOI in `SFS.benchRows`, its
box `.sfs-doi`, its title from `sfsPaperWords`, and Remove, then `#sfs-bench-add`. A DOI entered goes
through `sfsDoi`, as `norm_doi` has it, `sfsBenchSync` sets the plan's `benchmark` and prunes its
`benchmark_titles`, and `sfsFindTitle` asks the new `title` op, `sift_search.paper_title`, OpenAlex's
work by DOI through `works_by_doi` with `TITLE_FIELDS`, keeping the title in the plan's
`benchmark_titles`, `SFS.notFound` marking Title not found. `sfsDrawBenchTitles` redraws the titles
alone. The exclusion reasons are one list: `reasons_of` answers a list, a plan of before's two stages
read into it, `blank_plan` holds `[]`, `file_reasons` answers `reasons`, `staged` and `said`, and
`reasons_text` writes the one-list form, `REASONS_HEAD`, `code,meaning`. `sfsDrawReasons` edits
`SFS.reasons`, a `.sfs-reason` row each with `.sfs-rcode`, `.sfs-rmeaning`, `.sfs-rmove` up and down
and Remove, `#sfs-reason-add`, `sfsReasonSaid` saying a code held twice, and `sfsReasonsSave` sends
the new `reasons` op, `sift_search.save_reasons`, which writes the review's `reasons.csv`, copies it
into each run whose screening `begun` finds unbegun, each such run's `screening.lock` taken first
(26 October, as a drop takes it) and `begun` asked again under it, so a lock another writer holds
refuses BUSY with nothing written, and saves the plan so `with_file_reasons` takes them in. `sift.reason_problem` makes a reason optional at title and abstract and required at full
text, in `decide_in` and `propose_review`, and Screening's picker, `sfReasonChoices`, puts No reason
first, key 0, at title and abstract, `sfDecide` taking `chosen`. Register is Export search_plan.md,
`#sfs-export`, `sfsExport` and the new `export` op, `sift_search.export`, which writes the newest
version's `markdown` at any time and answers `exported`, which Copy, `#sfs-md-copy`, copies, Open
search_plan.md shown once `plan_file`, and `#sfs-reg-steps`, then `#sfs-mark`, Mark as registered,
whose card `#sfs-mark-card`, `sfsMark`, `sfsMarkReady` and `sfsMarkGo`, asks the registry and the
number or link, which the `register` op needs and `register` keeps as `registry` and `registration`,
`registered_with` saying them in `markdown` and `sfsWhere` on the screen, `state`'s heads carrying
both. Register this plan, `sfsRegister`, `sfsRegisterLine` and the `reasons` file of the `open` op are
gone, `SEARCH_FILES` holding `plan` alone. Search runs is a table, `#sfs-runs-table`, `sfsRunRow` a
`tr.sfs-run` each with `data-label` cells for the stacked layout under 760 pixels, Active in
`.sfs-open-tag` or Make active, `.sfs-open-run`, and a `.sfs-run-sub` row for waits, failures and
Details, `.sfs-details-toggle`, open runs kept in `SFS.open` by `run:<folder>`, as Earlier versions,
`#sfs-versions-toggle`, is by `versions`. `sfsRunWords` reads `Run N, D Month` from each run's
`number`, which `run_numbers` gives, held in `runs/numbers.json` (`NUMBERS_NAME`, `held_numbers`) and
written by `keep_numbers` as `run` and `take_export` make a run folder, any run it lacks numbered after
the highest in the order made, so a removed run moves no number. `run_said(name, folder)` and
`summary`'s `label` and `number`, `run_title`, `follow_said` and the home screen's `review_stands` name
a run so, `review_of_run` finding a run's review, while the command line keeps the day and its
number that day. New run's button is Start new run. Every Remove and Delete button with words takes
`.btn-remove` from `style.css`, `--danger` in light and dark, a red outline and a bin drawn by a CSS
mask: `.sfs-bremove`, `.sfs-db-remove`, `.dbs-remove`, `.dbs-key-clear`, `.sf-col-remove`,
`#project-remove`, `#sfp-remove`, `#btn-key-clear`, `#zot-key-clear`, `#th-confirm-go`, the PETs pile's
Remove for a missing card, `.th-leave`, the new benchmark and reason rows', `.pair-remove` on each
pair of the turn screen (14 October) until it became a bin alone (18 October), and `sfsAsk`'s and
`sfAsk`'s Yes when it says Remove or Delete. `sfsFlush` saves the plan and the reasons before an act
that reads them.

**PDFs carried by paper (12 October, later still).** A PDF belongs to the paper, not the run.
`sift.gather_pdfs` gives each record of a run's screening with no PDF the one an earlier run holds
for its paper: `earlier_runs`, the runs before it under the same `runs/` folder holding a screening
and a PDF, newest first by `run_order`, `pdf_index` their records by `match_doi` and by `match_title`
with `match_year`, and `pdf_for` the DOI's PDF, else the title and year's from a record with no DOI or
the same, none when a run holds two records of them or they carry two DOIs. Each is a plain byte copy
through a temporary file and `os.replace`, never over a file there, never outside `pdfs/`, under the
screening's lock, and named with its size and source in `pdfs/.found.json`, which `found_pdfs` reads.
`assemble` calls it once a run's screening is written and the `read` op of `/api/sift` on every
opening, before `refresh_prisma`. `own_pdfs`, every PDF but one found and unchanged since, is what
`begun` and `changed_since` count, so a found PDF is never a screening begun, `clear_found` takes the
found ones away before `assemble` writes a run afresh, since its records are numbered anew, and
`save_pdf` forgets one he replaces with `forget_found`.

**One handle, and columns moved by their headings (12 October, latest).** From Adam's look at Set
columns. Every list he puts in his order is dragged by one handle, `gripHtml` in `app.js`, the home
rows' `.pc-grip` with its one style in `style.css`, moved by `gripDrag` and by `gripKeys`, Alt and an
arrow, each list giving its own `how`: `rows`, `live`, `said` and `moved`. The home rows' is
`cardGrip`, saving through `saveOrder` as before. Set columns' rows carry it in place of their up and
down arrows, `sfColsGrip`, a drag heard on `#sf-cols-list` and Alt and an arrow through `sfColsKey`,
since Sift hears every key first, and `sfColsMoved` saves the new order through `sfColsSave`, the
`view` op's `columns` as before, the handle keeping the focus. The exclusion reasons on Search
strategy carry it in place of Move up and Move down, `sfsReasonGrip`, Alt and an arrow through
`sfsKeyDown`, and `sfsReasonsMoved` writes the new order at once through `sfsReasonsChanged`, as
Remove does. Each list says a move in a live line of its own, `#order-said`, `#sf-cols-said` and
`#sfs-reasons-moved`. A heading of the table drags its column: `sfThPress` on `#sf-thead` makes a
press a drag once the pointer travels `SF_TH_TRAVEL` pixels, the boards' four, marks the heading
`.dragging` and the nearest place, `sfThGaps`, with `.sf-drop-before` or `.sf-drop-after` through
`sfThMark`, scrolls `#sf-tv-box` sideways near its edge, and on the let go moves the column by
`sfColMoved`, the hidden columns keeping their places, and saves it by `sfColsSave`, so Set columns
and the table hold one order. `SF.thDragged` makes `sfThClick` skip the click that ends a drag, so a
press that never travels still sorts. The ID, `SF_ID`, the number until 13 October, and At title and
abstract, `SF_TADEC`, neither drag nor take a drop, `sfThMoves`, so the ID stays first and the first
stage's column after Decision. A finger on a heading pans the table as before, and the handle in Set columns moves a
column by touch. No column resizes by hand, a design decision: each takes its width from its
content and the window, its `--w` at least, and the box scrolls sideways when the window is narrower.

**The decisions' words (12 October, latest).** From Adam's reading of a record that read Accepted at
title and abstract and Undecided at full text. Title and abstract is a filter and full text the
decision, so each stage has its own words, words only: `sift.SHOWN_WORDS`, Yes, Maybe and No at `ta`
and Include, Maybe and Exclude at `ft`, and `sift.TO_SCREEN` for an empty decision, read by
`shown_word`, and `SF_WORDS`, `SF_TO_SCREEN` and `sfWords` in `sift.js`, the one place each side maps
them. Nothing stored changed: the CSV's decision columns, the log, `sift.json`'s filters, ticks
`undecided`, `include`, `maybe` and `exclude` as before, and the second screener's log lines and
`screening.second.csv` keep include, maybe and exclude. `sfPillHtml` and `sfPillSet` take the stage,
the record's own by default and `ta` for At title and abstract. `sfActsDraw` gives `#sf-acts` its
words, its keys from `SF_KEYS` and its hovers from `SF_SAYS` as the record is drawn, and
`sfKeysOpen` the shortcuts card's three rows, `#sf-kk-*` and `#sf-kw-*`, as it opens. `sfKeyDown`
asks `sfKeyDecision`, the stage's Y, M and N or I, M and E, then `SF_KEYS_OLD`, A and R at both,
shown nowhere, and the note moved from N to T. `sift.decision_word` reads yes and no too, and
`round_key` takes a round by `ROUND_SAID`, to-screen, yes or include, no or exclude, beside its own
name, `rows_of_round` giving the round's own name back. The flow's Awaiting a decision, Sift's own
line inside PRISMA's box, is To screen, PRISMA's own box words unchanged. `sift_second.py` writes
`CHOICES` as the Decision dropdown, `HOW_SECOND` and `REASONS_HEAD` by stage, and the differences
workbook's decisions through `SHOWN_WORDS`, while `SAID` reads yes, no, include, exclude and the
older accept and reject. `NO_REASON` is by stage. `cli.py`'s `sift_lines`, `decision_said`,
`proposal_said` and `round_words` print the stage's words, the JSON keeping the stored values. The
counts file, `screening.counts.csv`, keeps its measure names, include, maybe, exclude and undecided,
since it is read by the review's own tooling.

**Whole rows, Done, the ID first and Number columns (13 October, latest).** From Adam's use of Set
columns. Every checkbox and radio ticks from its whole row. Each sits inside its `<label>`, the row
itself where it can be, and one rule in `style.css` gives a tick's label a pointer and the row's wash
under it. A row that holds other controls too, Set columns' rows with their handle, his name box,
Remove and choices, and the databases' rows on Search strategy with their tags and Remove, carries
`data-tick-row`, and `tickRowClick` in `app.js`, heard on the document, ticks the row's box from a
press anywhere on it but on a control or a label, `TICK_SKIP`, unless the press began on one, which
the pointerdown it keeps in `tickPressed` says, so a handle's drag let go on the row ticks nothing.
`sfColsDraw` puts a built-in column's tick and name in one label, `.sf-col-tick.sf-col-whole`, and
his own column's tick in a label alone. The suite's `tick_problems`, area 127, scans `index.html` and
every `static/*.js` but the vendor's, and fails on a tick in no label and named by no `<label for>`,
in markup, a template string, joined strings or `createElement` alike. Done, a `data-done` button in
the card's actions marked `.card-done`, stands at the foot right of a card that keeps each change as it is made,
Set columns alone for now, Settings keeping its Save, and `cardDone` presses the card's own
`.card-close`, so no card wires its own. The record's ID is the table's first column, `SF_ID`, kind
`id`, sorting by `TB_TEXT`'s natural order, R2 before R10, in place of the number's column, which is
gone from the page, while `sift.json` keeps `numbers` and `record_view` and `list` still give `n`.
`rec_id` left `TABLE_COLUMNS` and `SF_COLS`, so Set columns has no row for it and a `columns` naming
it is passed over. The record's head reads Record and its ID, `#sf-num`, the reasons' heading, Undo's
hover, the bench and the second screener's calibration line name it by ID too. `COLUMN_TYPES` adds
`number`: `field_cells` keeps a whole number from nought to `NUMBER_MAX`, commas dropped and leading
noughts with them, or none, and refuses anything else in one line, and `range_keys` makes its filter
a slider's in `kept_filters`. In the page `sfColumns` gives it kind `number`, `sfIsRange` and
`sfRangeKey` treat it as a slider's column with the participants' bars, `sfBlankWord` its blank
Unknown, `sfTvCell` and `sfFieldsDraw` show it as the participants are shown, and `sfTvEdit` opens it
with the number keys. A later run that keeps the decisions carried his columns already, `sift.json`
copied whole by `carry` and their values in the CSV's cells and the `carry` lines of the records
matched by `merge`, so only a check was added for it.

**OpenAlex's and Crossref's columns, key works and studies (13 October).** Five columns for every Sift
project, Adam's choice from the coordinator's list. `fill_from_openalex` asks OpenAlex for `FILL_FIELDS`,
which gained `is_retracted`, `open_access` and `referenced_works`, in the same batch of fifty as before,
and `crossref_works` asks Crossref's works for the same DOIs in one request, a `filter` of each `doi:`,
`select` of `CROSSREF_SELECT`, asked again whole on a 400, with `mailto` from `Context.email`, the
`sift_email` config.json keeps, which the server gives a run, a drop and the fill. `Context.crossref`
is the real address only while OpenAlex's is, `crossref_for`, so a stubbed run or check sends Crossref's
requests to the same stub under `/api.crossref.org/works`. `openalex_cells` writes `cited_by`,
`open_access`, `countries`, `openalex_authors` and `openalex_date`, `crossref_notices` reads
`updated-by` through `UPDATE_KINDS`, and `retraction_cells` writes `retraction` and
`retraction_notices` from both, `none` once either has said. Each record's references, `openalex_refs`
and `crossref_refs`, the latter each reference's DOI, year and folded titles from `REF_TITLES`, go under
the merged record's `references` and into `screening.references.json` through `sift.write_references`,
read by `sift.references`, held once for each stamp of the file. The run's CSV puts `OWN_AFTER` after
every column it wrote before, and `run.json` counts `openalex_filled` and `crossref_filled`. A carry
fills a carried record's missing columns with `bibliographic` false and copies the earlier run's
references. Fill from OpenAlex, `sfFillRun` under Sift in Settings in place of `sfCiteRun`, asks the
`fill_plan` op and then `fill` fifty at a time from `at`, `fill_columns`, which asks only what
`fill_wants` finds missing, Cited by among it, and writes through `write_filled` in `sift.py` under the lock.
The `cited_plan` and `cited` ops stay. In `sift.py`, `extras_of` works out once for a screening what
`own_view` adds to each record: `notices`, `oa`, `countries` named by `COUNTRY_NAMES`, `study`,
`study_with`, `cites` and `suggest`, holding the authors and title words in `_EXTRAS` while their cells stand, so an act works none of them out again. `cites_of` reads Crossref's references when it holds any for the
record and OpenAlex's only when it holds none, and `ref_cites` matches a key work by its DOI, or by its
folded title in one of a reference's titles with its year within `YEAR_SLACK`. `suggestions` compares
the lists of `author_list`, OpenAlex's with IDs where the record has them, through `shared_authors` and
`name_key`, two shared or half the shorter list, strengthened by `participants_of`, the `title_words`
rare in the screening by `RARE_SHARE`, and years within four. `study` is Same study and Unlink, a line
of `act` `study`, `next_study` never giving a label twice, and `STUDY_COLUMN` is in `OWN_COLUMNS`, so
`reset` clears it, `carry_log` carries it and `last_line` finds the link that set it. `flow_of` counts
`studies` and `reports` among the records included, and `prisma_source`'s last box and `count_rows`
say both. The key works are `key_works` beside the versions in `search_plan.json`, kept through every
write by `read_file`, cleaned by `clean_key_works`, written by `save_key_works` and the `key_works` op,
found by `find_works` and the `works` op, and read for a run's screening by `key_works_of` through
`review_of`. In the page `SF_COLS` gains `study`, `retracted`, `oa`, `country` and `keyworks`, their
kinds read in `sfValue`, `sfOrder`, `sfPickable`, `sfPicked`, `sfGroups` and `sfTvCell`, `sfNoticeTags`
puts the word beside a title, `sfStudyDraw` and `sfFactsDraw` draw the record's parts, `sfStudy` sends
the `study` op, and `sfLand` takes every record of `records`. `sfsDrawKeys`, `sfsKwFind`, `sfsKwAdd`
and `sfsKwSave` are the Plan's Key works. The suite's `hive_stub`, area 128, answers OpenAlex and
Crossref on loopback.

**Extract and appraise (13 October, later).** A stage after full text for every Sift project, Adam's
choice, where each paper included at full text has its data extracted and its quality appraised on a form
the project sets up, PRISMA 2020's items 9 to 11. The form is his own columns extended, one definition:
`own_entry` reads each entry of `own` in `sift.json` with `where`, `table`, `form` or `both`, `table` for a
column made before, `not_reported`, `when`, the key and values of a field of `CONDITION_TYPES` it is shown
for, `section`, and `from`, one of `SIFT_SOURCES` or another column's key, and `kept_entry` writes
`OWN_KEYS` back. `COLUMN_TYPES` adds `yesno`, `multi`, `long` and `passages`, `TABLE_TYPES` keeping Set
columns' three. `form_field` sets a field whole under the lock, adding with no key, a part left out kept,
its key with or without `col_` checked by `KEY_SHAPE`, unique case set aside and never one of `FIRST_KEYS`,
by default its name's slug, which follows a new name while the key is still the old name's, a new key
renaming the CSV's column and the `when` and `from` that name it, `condition_of` refusing a condition on
the field itself, on a field of no choices or one that waits on it, a field others wait on keeping its
choices. `column` keeps Set columns' add and change through it and removes as before, the conditions
and starts on the column gone let go. `keep_own` writes `own` in `form_order`, `columns` and `sections`,
which `sections_of` reads. `order_form` sets the sections and their fields whole and is no line of the
log, as the table's order is not. `own_cell` checks a value by type for `field_cells`, Not reported as
`NOT_REPORTED`, several choices in the list's order parted by a semicolon, passages a JSON list of `page`
and `text`, the cell's own value always standing. `start_value` and `field_value` give a field its Sift
column's value while his cell is empty, `citation_of` the citation, `shown_fields` the fields shown by
their conditions down a chain, a hidden field keeping its value, and `form_state` each record's `shown`,
`sift` and `done`, which `record_view` gives as `form` from `extras_of`'s `form` and `own`.
`benchmark_ids` matches the plan's newest version's benchmark DOIs, else for a record with none its kept
title, and `form_round` is the stage's `ids` and `bench` with `form_of`'s sections and fields. `form_cell`, `form_rows` and `form_read` give
the export's rows, `export_form` writes `FORM_CSV`, and `form_of` the form for the reading tools.
`sift_form_op` in server.py is the `form` op, `list`, `read`, `field`, `order`, `remove` and `export`,
values going through the `field` op. In the page `SF.form` stands at full text, `sfStageTo('ex')`,
`sfRound` asking `form` `list`, `sfBaseIds` the included records or with `bench` ticked the benchmark
papers, `sfViewCols` putting `SF_FORMDONE` after the ID, `sfColumns` leaving the form's own fields off the
screening's table, and `sfFieldValue`, `sfShownKeys` and `sfFormDone` mirroring `sift.py`. `sfFormDraw`
and `sfFormInto` draw the form by its shape, `sfFormSet` its values, `sfFormBoot` keeps each change
through `sfFormSave`, `sfFieldsDraw` draws the form's types of a column on the table among his fields,
and `sfFcDraw`, `sfFcBoot`, `sfFcOrder` and `sfFormDef` are Set up the form. `RV_FORM_NAME` in
sift_search.js and `FORM_STAGE` in sift.py hold the stage's name, and `rvStepsHtml` its step and count.
The CLI's `sift form` and `form_lines`, `show`'s `form_said`, and MCP's `sift_form` only read.

**The plan's terms as filters (13 October, later).** Kept apart from the form. `terms_of_plan` reads the
review's plan's newest version, the draft among them, once for each change to `search_plan.json`, each
block with terms and each term's patterns from `term_rule`: `parse_term`'s reading through `term_pattern`,
folded as `fold` folds, a word edge each side, a trailing asterisk any ending and a hyphen a hyphen, a
space or none, and for a term in a database's syntax its plain words after `TERM_SYNTAX` and
`TERM_OPERATORS` take out tags, field codes and operators. `keywords_index` reads the run's
`raw_*.json` once for each change, by DOI and by title, and `record_terms` gives each record's terms of
each block, `term:` and its place, which `record_view` gives as `terms`, `blocks_view` the blocks as
`screen` and `history` give them, and `TERM_KEY` lets `kept_filters` keep their ticks. Nothing is
written. In the page `sfTermCols` makes each block a column of kind `terms` that only the filters take,
`sfGroups` its choices with the block's lines last, `sfPicked` a record's terms, and `sfTermsDraw` the
record's lines under its facts. The CLI's `show` says them by `terms_lines`.

**How a record matched (14 October).** `record_match` gives each record's terms of each block, as
`record_terms` did, and `matched`: for a block it holds terms of, `in`, the fields they were found in from
`MATCH_PLACES`, and for one it holds none of, `why` from `match_why`, each line a value of a bar and its
kind, its label and the databases it names. `match_context`, held once for each change to the plan or
`run.json`, maps each name `sources` may give, folded by `db_key`, to its database, takes the plan version
the run ran, else the newest, and asks `beyond_text` in `sift_search.py` what each database searched each block in
beyond the title and abstract: `methods`, `keywords` unless `NO_KEYWORDS` names it and its platform, or
`fulltext`, which the fourth line names since 14 October, after the keywords and before no abstract.
`MATCH_LINES` holds Adam's lines, the one place they are worded, `match_line` fills in the databases,
and `MATCHED_IN` is the CLI's word. `extras_of` holds `how`,
`record_view` gives `matched` beside `terms`, and `screen` passes the records to `blocks_view`, which gives
each block's `why`, the lines its records stand under with the databases of all of them in the plan's
order. The page's `sfTermCols` carries `why`, `sfGroups` puts the lines after the terms, `sfPicked`
gives a record holding no term its lines' values, `sfTermsDraw` draws Matched in or the lines, and
`sfMatchedLines` the Matched in column, `matched` in `SF_COLS` and `TABLE_COLUMNS`,
hidden at first. The CLI's `terms_lines` says them. The keywords: `KEYWORDS_COLUMN` after the screening's
own in `COLUMNS`, `WRITTEN` and `CARRIED_CELLS`, PubMed's KeywordList and MeSH headings, Europe PMC's
`keywordList` and OpenAlex's `keywords` through `keyword_list` and `openalex_keywords`, `merge` keeping
the list `keyword_count` finds fullest, `fill_from_openalex` filling a record that lacks them with
`keywords` in `OPENALEX_FIELDS`, `FILL_FIELDS` and `OWN_FIELDS`, `fill_wants` asking for a record that
lacks them, and `write_filled` writing them only where the cell is empty. `record_match` reads the column
beside the raw files that `keywords_index` reads.

**The match lines reworded, and Can't check (14 October, later).** Adam's words by dialog, so a reader
understands them at once. `MATCH_LINES` holds each line as the filters say it, `{} methods sections`,
`{} keywords`, `{} full text`, `the abstract, which Sift does not hold` and, new, `none`, `a field Sift
cannot name`, which `match_why` gives a record whose block no other line explains, its value `|none` the
same as the page's `TB_BLANK`, so `blocks_view` lists it last among a block's `why` and the page needs no
words of its own for it. `match_line` joins the databases by `or_join`, A, B or C. `MATCH_SAID` holds each
line as the record says it, filled by `match_said` with the databases and its or their, `MATCH_NONE` the
words before them, and `record_match` gives a block holding none of its terms `said`, `MATCH_NONE` and each
line's own, which `sfTermsDraw` draws after the block's label in a Matched in row of the record and the
CLI's `terms_lines` says after it. `MATCH_HEAD` is the heading of two lines over a block's lines, which
`screen` gives as `match_head` and `sfTake` keeps in `SF.matchHead`. On the page `sfGroups` gives a block
More than one, `SF_MANY`, where it has two or more terms, `sfPicked` adds it for a record holding two or
more, each line its choice with `line`, `sfFacetOrder` orders a block's terms by count, then More than one,
then its lines by count, and `tbGroupHtml` cuts only the terms at Show more and draws the lines whole under
the heading in `.sf-lines`, while one of them holds a record or is ticked. `sfMatchedLines` parts a
block's lines by a middle dot, and `SF_TERMS_NONE` is gone. Cites key works: `SF_BLANK_WORDS.keyworks`
is Can't check, the column and the filter taking it, `SF_CITES_UNCHECKED` the sentence `sfFactsDraw`
gives the record, and `CITES_UNCHECKED` in `sift.py` the same sentence for the CLI's `facts_lines`,
for a record whose `cites_of` is None.

**Each record's language (14 October).** `LANGUAGE_COLUMN`, `language`, holds a record's languages by
their English names, parted by semicolons. `LANGUAGE_NAMES` maps ISO 639-1 and 639-2 codes and the names
themselves to English names, `language_name` gives one, a code not there kept as given and `und` as
none, `language_list` a record's list and `language_cell` its cell. `record` takes it from PubMed's
`Article/Language`, each of them, Europe PMC's `language` and OpenAlex's, asked in `OPENALEX_FIELDS`,
from `read_ris` by LA, `read_csv_export` by a `language`, `la` or Scopus's `language of original
document` column and `read_bib` by a `language` field. `merge` keeps the one `language_rank` puts first:
`LANGUAGE_ORDER`, PubMed, Europe PMC, PsycInfo, Web of Science and Scopus, then any other database, then
OpenAlex. `screening_text` writes it at the end of the header, `carried_text` keeps an earlier CSV's
column where it stands or adds one at the end, `CARRIED_CELLS` fills a carried record's empty cell, and
`fill_from_openalex`, `fill_wants` and `fill_columns` fill an empty cell from OpenAlex, `FILL_FIELDS`
and `OWN_FIELDS` asking for it, through `write_filled`, which writes it only where the cell is empty.
`extra_columns` leaves it out of the review's columns, `record_view` gives `language` and names it so in
`more`. The page's `language` in `SF_COLS`, after Country and hidden at first as in `TABLE_COLUMNS`, is a
group whose choices `sfPicked` and `sfWritten` give as Country's are, Unknown from `SF_BLANK_WORDS`, and
`sfTvCell` and `sfValue` say it.

**Truncation safeguards (14 October).** Adam's rule is truncation on single words alone. `parse_term`
refuses a phrase, quoted or of several words, holding `*` or `?`, with `PHRASE_TRUNCATION` after the term,
so `term_problems`, `block_problems` and `problems` name it and `ready` keeps the plan from being
registered or run, on the screen, the command line and MCP alike. `phrase_problems` gives those lines, and
`save` raises `Unsaved`, a `SearchError` carrying them and `view`, the problems of the plan sent, before
the lock is taken, so nothing is written. The route's `save` answers the plan as it stands with `view` and
`unsaved`, an empty list once a save goes through, and `save_reasons` keeps the reasons in their file and
answers `unsaved` when the newest plan holds such a phrase. `SearchError` says several lines one after
another. The page's `sfsUnsaved` reads `unsaved`: `sfsDrawVersion` says Not saved in the state tag and
holds Mark as registered, and `sfsDrawRun`, `sfsRun` and `sfsCheck` hold the run and the check.
`rewrites` gives each database's changes from the plan in plain words, `strings` passes them as
`rewrites`, from `field_codes` with `FIELD_CODES`, `EBSCO_FIELDS`, `OVID_FIELDS` and `PROQUEST_FIELDS`,
`fields_said`, `block_said`, `KEYWORD_SWAPS`, and `years_clause` and `types_clause`, which every writer
now reads through `limits_of`, so a rewrite and its string never differ. A string edited manually gives
its reason alone. The page's `sfsRewritesHtml` draws them under Rewrites and the CLI's `strings` under
`Rewrites:`. The dry run's truncation check is `truncation_check`: `starred` gives each word with an
asterisk and its block, `alone` the plan with that block holding the word alone, written by each
database's own writer with and without the asterisk, `counter` asks for the count as its runner does,
one record or none, `tries=2`, with `PAUSE` between requests to one database, for `TRUNCATES`, Scopus,
Web of Science, PubMed and Europe PMC, among the databases searched by API (`by_api`), and `flag_rows`
flags `READS_AS` and `NO_HITS`, `NO_HITS_FOR` naming the term in the flags' list. `run` takes
`check_terms`: a dry run answers the table as `terms`, and a run checks after its first `run.json`, each
database heard as `checking`, writes `terms_text` to `TERMS_NAME`, `dry_run_terms.csv`, removed with the
rest when a run folder is written afresh, and keeps `terms`, its file, rows and flags, in `run.json`,
which `summary` passes and `run_lines` says. The CLI's `run` passes `check_terms` both ways, and so MCP,
with `terms_lines` for the dry run, and the route's run thread passes it while its own dry run, which
only sets up the run's state, does not. `check_terms` is the route's `terms`, Check truncation, for the
newest version, refused as a run is and while one goes. `state` gives `truncated`, the count of starred
words, and `search_catalog` `truncates`, from which `sfsCheckable` shows the button, and `sfsDrawCheck`
draws the table, a row a word in each database, stacked on a phone. `SFS_STATE.checking` names the state.
The fourth match line, `fulltext` in `MATCH_LINES` and `match_why`, is under How a record matched.

**The filters by their counts and Country on a map (13 October, later).** `sfFacetsDraw` takes its rows,
groups and counts from `sfFacetsData`, then orders each group's choices by `sfFacetOrder`: `sfByCount`, a
stable sort by the counts drawn, the most first and the noughts last, a tie in `sfGroups`' own order, so
`sfGroups` is unchanged and its order is the tie's. `sfOwnOrder` keeps a scale's own order, the sliders,
`tadec`, `formdone` and his own columns, and the decision keeps its four with its reasons by count among
themselves. `SF.facetsOrder` holds each group's values as drawn, and a tick or a group's Clear calls
`sfFacetsHoldAt`, which sets `SF.facetsHold` to that group's drawn order, so it keeps it while the
others re-sort. Opening a screening, a stage or the sidebar, and Clear all, drop the hold. Show on map
in `tbGroupHead` beside Country, the Country group's `tool`, opens `#sf-map`, an `.overlay`. `sfMapOpen` reads `static/world.json`
once into `SF.world` from the app itself through `api`, so sift.js makes no request of its own, and `sfMapFrom` takes the Country group's choices and counts
from the same `sfFacetsData`, with the records that pass every other group's filter as its total, so
the map's counts are the group's. `sfMapModel` takes each country's label point by the name
`world.json` gives it, the radius by the square root of its count, scaled so the largest is
`SF_MAP_MOST` (40), a count of one at most `SF_MAP_UNIT` (14) and none under `SF_MAP_LEAST` (11), so
every circle holds its number, and lists a country with no point in `unplaced` for `sfMapLine`.
`sfMapLayout` sets the circles apart (13 October, evening). Each starts as a point at home, `hx` and
`hy`, and they grow to full size over `SF_MAP_GROW` steps of `SF_MAP_PASSES` passes, each pass drawing
every circle back by `SF_MAP_PULL` and pushing apart any two nearer than their radii and `SF_MAP_GAP`,
the push shared by the fourth power of the radius, so the larger stay nearest home and none passes
through another, then passes with the push shared by area until none touch. The order is fixed and
nothing is random, so the same counts give the same positions. A circle whose point is out from under
it gets `line`, drawn from its edge to a dot on the point. `sfMapNames` places each name, the largest
circle's first, at twenty-four turns round its circle `SF_MAP_PAD` out, then at each step of
`SF_MAP_OUT` with a tie, a short line back to the circle. It takes the first place beside the circle
clear of every circle, every name before it, every line's point and the frame, and nearer its own
circle than any other, else the first clear tied place, else the first clear place beside it, else the
place that runs least into a circle or off the frame and then overlaps least, with `clear` false.
`sfMapWide` measures a name by a rough width for each letter, so the placing needs no page and runs
the same in node. `sfMapSvg` draws the lines under the circles
and the names over them, with classes for the tokens `--sf-map-sea`, `--sf-map-land`,
`--sf-map-border`, `--sf-map-dot`, `--sf-map-ring`, `--sf-map-num`, `--sf-map-line` and
`--sf-map-name` in `sift.css`, each name ringed in the sea's colour by `paint-order: stroke`, or with
`SF_MAP_PAPER`'s light colours written in on white for `sfMapSave`, each name's ring there a copy of
it in the sea's colour drawn first, and the text kept as text in a stack of faces. `sfMapSave`
serialises it through the browser's own `XMLSerializer` for the SVG and draws it on a canvas
`SF_MAP_PNG` wide for the PNG, `sfMapFile` naming each after the run. `SF_MAP_WORDS` holds every word
the map shows, `note` among them, the projection and the borders' source, which `sfMapBoot` puts in
`#sf-map-note` under the line in the overlay and no saved file carries. `make_world.py` builds `world.json` from Natural Earth 5.1.2's admin 0 countries, given
by path and never fetched, the 1:110m file for the outlines, Antarctica left out, and the 1:50m file
for every country's label point, `LABEL_X` and `LABEL_Y`, each by `ISO_A2_EH`, named by
`sift.country_name`. It projects them on Equal Earth (Šavrič, Patterson and Jenny, 2018), an
equal-area projection, so a circle's area means the same at every latitude, into a frame 1000 wide,
each outline a path of relative steps to a tenth, `sphere` the projection's edge between the land's
southernmost and northernmost latitudes for the sea, and refuses to write a file over 150,000 bytes.
`packaging/build_mac.py` carries all of `static/`, `world.json` with it.

**Trace (15 October).** The third part beside Sift and Idiograph, grown from Sift's Check references of
14 October, which stood as a step of every Sift project after Extract and appraise and is gone from
`rvStepsHtml`, a review left on it opening on its own steps by `rvStepOf`. `trace_claims.py` alone reads a
manuscript or a reference list and writes a project's judgements, for the server and the command line
alike. A project is a folder holding `PROJECT_FILE`, `trace-project.json`, its name and `list`, the
reference list he loaded, made by `make` and opened by `to_open`, which takes Sift's `reference_check/`
folder of 14 October as one, `is_legacy`, given itself or by its Sift project's folder, writing nothing.
Trace's routes (`apps/trace/trace_routes.py`) keep the projects in `trace_projects` in the app's state,
newest first, as Sift's reviews are kept, `traces_kept`, `remember_trace`, `edit_trace` for his name under Trace in Settings, `forget_trace` for
Remove from Idiograph, and `trace_folder` refuses a folder the list does not hold, 403. `trace_rows` gives
the home screen's cards, each line from `stands`, which reads the readable file's `counts` alone.
`blocks_of` reads Markdown through `md_blocks`, front matter, comments and code passed over, a list item a
paragraph, emphasis that runs over a line's end taken away by `md_inline` on the paragraph whole, and Word
through `textfiles.docx_paragraphs`, each paragraph with its heading level from its own outline level, its
style's or the style's name, Heading 1 and Title among them, read from `word/styles.xml` by `_styles`, so
`docx_text` and the transcripts read as before through `_docx_body`. `ref_section` finds the last heading
named as `REF_HEAD` says, or a short paragraph that says no more, to the next heading as high, and
`entries_of` splits a paragraph of it into entries, a line that opens as `ENTRY_START` after one that ends
as an entry does starting the next. `parse_reference` gives the surnames, `surnames`, a group's name whole
when no initial stands in it, the year and letter by `YEAR_PAREN`, n.d. and in press among them, the title
as near as the entry gives it and the DOI, and `keyed` gives each a key, the first surname and the year
with its letter, `page2021`, a second alike `-2`. A reference list alone is read by `read_list`: a CSV by
`csv_refs`, its columns found by their headings in `LIST_HEADS`, a column of whole references read by
`parse_reference` and otherwise each made from its authors, `persons`, year and title by `entry_of` and
`made_text`, with the DOI and an eight-character Zotero `Key` from their columns, an RIS file by
`ris_refs`, and BibTeX by `bib_refs` through `bib_fields`, `bib_people` and `delatex`, and `lettered` gives
the same authors' works of a year their letters by their titles, `title_order`, as APA letters them.
`citations_in` finds each bracket by `brackets`, its items parted at semicolons and at as cited in, e.g.
and see let go by `LEAD`, each item read by `ITEM` and kept when `plausible`, and the narrative form by
`NARRATIVE`, each with `end`, where its bracket closes, a group's abbreviation in square brackets kept as
an alias and one alone in a bracket after the group's name, `ABBR` and `BEFORE`, taken as one too. `match`
answers a citation of one year by the first surname and the year with its letter, two authors' second
surname too, et al. three or more and a group by its name or alias, a narrative citation's opening words
let go one at a time, and none when two answer alike. `analyse` takes the manuscript's own list, or with
none the project's, `listed`, and `enrich` gives its own entries the list's DOI and Zotero item where they
have none. `sentences` parts a paragraph at a stop outside a bracket and after no abbreviation, `ABBREV`,
or initial. Each citation keeps its sentence whole with the heading above it, and where the citation
closes it, `CLOSES`, and it leans on the one before, `leans` by `LEANS`, the sentence before as `before`.
`claims_of` gives each reference's sentences once, each a claim keyed `<ref>~<hash>`, `claim_hash` of its
letters and digits, so a change of spacing keeps his judgement and a change of words asks again, and
`analyse` answers every claim in the manuscript's order, a citation no reference answers among them by its
form, `cited_as`. `pdf_index` and `pdf_for` find a PDF in the project's `pdfs/` by the key, the DOI in the
file's name, `alnum`, or on its first page, read once for each size and time by `first_page`, else a
screening record's by DOI or title in any Sift project he keeps, `trace_screenings` in `trace_routes.py`,
Idiograph's list while the run serves Sift and in Trace's own app Sift's own state file, read and never
written (`screenings.reviews_in`, 22 October),
each screening's records read once for each size and time of its CSV by `screening_hits`, with its
`zotero_key`, which the server makes a link for the Zotero app by `zotero_item_link`, `ZOTERO_ITEM`. Every
relative path it answers takes forward slashes, `rel_name` by `as_posix`, `slashed` for one written with
backslashes, and `joined` joins one back with Path, and a manuscript's and a list's path are kept whole
and as `relative`, from the project's folder, `from_folder`, so `located` finds one moved with the
project. The judgements are kept in the project's folder: `<doc>.log.jsonl`, one JSON line an act,
`judge`, `note`, `undo` and `passages`, each with `n`, `at`, `claim`, `ref`, `tool` and `by`, `researcher`
for his and `ai` for passages, a judgement with `judged`, Y, Q or N, `was` and `words` from `judge_words`,
and with the app's switch on and passages on the reference `passages_shown`, and `<doc>.json`, the
manuscript's path, name and day added, each claim in order with its reference, section, sentence, `before`,
`judged` in words, `set` and `note`, a claim he judged that the manuscript no longer holds kept with
`in_document` false, then `no_reference`, `never_cited`, `passages` and `counts`, written afresh by
`write_state` only when it changed, under `trace.lock` through `locks.held`. `states` reads the log, an
undone act passed over, Sift's `check` lines history alone and its `pointer` read as passages,
`undo_target` the newest judgement or note not undone, and `act` and `undo` answer `answer_of`, the claim's
state, its reference's passages and Undo. `rows` gives the screen a row a claim, `kind` claim or missing,
then each reference never cited, `uncited`, and `list_rows` the list alone. `find_passages` sends a
reference's claims, each with the sentence before it, and the PDF's pages from `sift_oa.pages_text`, the
pages that share most words with them chosen in their order past `PDF_CHARS` by `page_choice`, through
`ai_suggest.complete` with `PASSAGES_PROMPT` and `PASSAGES_SHAPE`, and `read_answer` keeps a passage only
where `locate` finds it, its letters and digits in order on one page by `letters`, each piece parted by an
ellipsis in order, at least `PASSAGE_MIN`, kept in the page's own words with its page, else `unverified`.
`plan` names the references of the claims shown with a PDF and no passages. The screen is `trace.js`,
built once by `trBuild`, holding `TR`: `trOpen` from a card, `trRead` and `trTake`, `trApply` through
the family's `tbFilterRows` and `tbSortRows` (`table.js`), its columns `TR_COLS` and the filters' own `TR_ONLY_FILTERS`,
`picks` columns as the family's `tbValue`, `tbPicked` and `tbGroups` take them, the groups in
`TR_GROUPS`' order drawn by `trFacetsDraw` through `tbGroupHtml`, the headings by `tbTvHeadHtml` and a
press on one by `tbSortNext`. `trJudge`, `trNoteSave` and `trUndo` go through `trQueue` in order and
`trLand` takes each answer, a reference's passages into each of its claims. `trRecordDraw` draws a claim
and the PDF from `/trace/pdf`, `#view=FitH&navpanes=0`, a passage's page sending the pane there,
`trFindOne` and `trFindAll` the passages, `trAsk` the one question and `trKeyDown` the keys. `trRef` writes
a row's reference, the grey pill `trMissing` or `trUncited` before a label kept whole in `.tr-short`, in
the Reference column and under the claim on a phone, and `trDocsDraw` hides both typed paths, over the
table and on an empty project, where `TR.choose` says the Mac's file dialog is there (15 October,
later). `trace.css`
holds its own parts, the rest Sift's through `#trace`. The filters and the manuscript open are kept in
this browser, `TR_FILTER_KEY` and `TR_DOC_KEY`, and the place by `spotNow` as `trace`. Settings' Trace
tab is `trpLoad`, `trpSaves` and `trpRemove`, and the project card is Sift's, `openReviewCard` with its
`part`, through `/api/trace-project`. The second copy check of 15 October: a citation with no reference
wears To screen's grey pill, `trMissing` and the record's `tr-pill` with `data-decision` empty, never a
judgement's colour, `trAskedLine` gives the toast after the rows shown, how many references were asked,
how many came back with no passage, `found` nought, and how many were left not asked, the question says
once alone for one reference, a claim's day reads Judged on, the Citations filter's `claim` choice is
Cited and listed, the line over a list alone is `TR_NO_CLAIMS`, No manuscript yet, `TR_PASS.none` and
`NOT_FOUND` say the model gave no passage for this claim, and below 480px `trace.css` hides `.sf-act-key`
in `.tr-acts` and gives each judgement the width of its word, a row that does not wrap, so the three sit
on one line down to 320px. An answer that is not the JSON asked for is one line everywhere,
`ai_suggest.NOT_JSON`, "The model's answer could not be read.", which `sift_ai`, `themes_ai` and
`trace_claims` take as their own `NOT_JSON`. A Sift or Trace card's hover on the home screen is
`homeHover`, the folder above and the name joined by the folder's own separator, a backslash on Windows.
The third look of 15 October: a citation with no reference keeps its claim in the ink, `trace.css` greying
`.tr-uncited .tr-c-ref` alone and no longer `.tr-missing .tr-c-claim`, the record's line of forms is
`trForms`, each form that is the reference's `short` left out, so the author and year stand once over the
full reference at every width and a page or a full list of authors still shows, a missing reference's form
kept, and the empty project's `tr-add-empty` says Add file as the bar's `tr-add` does. Settings shows a
project's folder under Sift, Idiograph and Trace, `sfp-root`, `project-root` and `trp-root`, through
`pathHtml` in `app.js`, each folder's name with its separator a `.path-part` span, `inline-block` up to
the line's width, and a `<wbr>` after each slash or backslash, so the path breaks at its separators alone
and a name inside itself only when it is wider than the line, `.path` no longer `word-break: break-all`.

**The project of a path.** `project_of` answers the project a path belongs to: the demo's folder
for anything inside the demo, else the project whose root holds it, the deepest should two nest,
else None. `within_root` is whether it answers one, `case_path` refuses a workbook it does not as
`OutsideRoot`, 403, and `project_root` is it, or with no path the first project. `project_roots`
is every project's root, resolved, `project_id` the id the page names one back by, its root as a
project's `root` stores it, a case folder in it a glob on its pseudonym, or `demo`, and
`project_named` the root an id names, refused as `OutsideRoot` when no project has it.
`asked_root` is the project a Settings request is for, by its `root` id, else by the workbook
`path`, else the only project, a write with neither refused while there are several.

**The cards.** `projects` in `/api/cases` is a section for each project, in the order they were
added, built by `project_section`: `id`, `project`, `there`, whether its root is a folder, `cases`,
`participants`, its rows, and `gets`. `cases`, `recent`, `participants`, `gets`, `root` and
`project` stay at the top for a page from before the projects, the first project's, and
`demo_project` is the demo's own for its head. `participants` is a project's rows, built by
`participants` from the case list's own rows, and only read. A row stands for each case folder
under the root, the first folder of a row's path, and for each workbook sitting in the root itself,
named by its stem, in his order (`in_his_order`), and with no `order` in participant order by
`gets.case_order`, the folders with a P-number first, then the other folders by name, then the
root's workbooks. Each carries `case`, its title, then `path`, `name`, `sheets`
and `locked` of its workbook, the annotated one opened last, else the newest, or null, `turns`,
`{"done", "total"}`, `complete`, `board`, `boards`, how many boards its themes file holds,
`pets_complete`, `in_gets`, whether the GETs file at the root holds the case under the name its
themes file gives, `start`, the newest raw source, else the newest transcript, of a case with no
annotated workbook, `files`, every row of the case with its workbook first, and `demo`.
`read_book` opens each workbook read-only once for its sheets and its turns, the rows `read_case`
keeps, each with its speaker and whether it holds a statement, and `turns_of` counts the decided
ones through `rounds.row_states` with the progress file, as the case's own screen counts them. Each
keeps what it read against the modification time and size of the files it read, and so do
`boards_count` and `gets_file`, so a listing opens no file that has not changed since the last.
`demo_participants` is the demo's three, built the same way from `demos`.

**The home screen.** Each app's Home is drawn from `/api/cases` (9 October). `index.html` holds the three
sections, `sift-home`, `home-analysis` and `trace-home`, each headed Projects and marked `data-only` for its
app, so the page shows its own app's alone (see One page per app, above). `drawPick` fills Idiograph's, a card
for each project, `homeCardHtml`, its one line from `standLine`, then the Demo projects section (`#home-demos`,
3 November 2026), the two demos from `demosOf` (the IPA demo, `demo`, and the thematic analysis demo, `demo-ta`,
from `demos_ta`, `demo_ta_participants` and `demo_ta_project`), each card with its own tag (`distil.tag.demo_ipa`,
`distil.tag.demo_ta`), folded by `demosFold`: shut by default, open on a Home with no project, and kept as he leaves
it by the fold ids `demos:open` and `demos:shut` in Projects' own fold list, and calls
the other two, Sift's from `reviews`, `drawSiftHome`, and Trace's from `traces`, `drawTraceHome`. Under the
sections stands `#family`, the other two apps, which `loadFamily` asks of `/api/family` and `drawFamily`
draws, its heading their names joined by "and", each card with Open or Download. Idiograph's section was
named Analyse until later on 15 October, so its ids, `home-analysis`, `analysis-head`, `analysis-body`,
the fold's key `analysis`, and every route, file and setting keep that name. A card opens its project's page, `drawPage`,
or the demo's, `drawDemoPage`, from the same answer, kept as `S.lib`. Which shows is `S.home`, a
project's id, `demo`, or empty for the picker, kept in this tab's `sessionStorage` under
`idiograph-home` by `homeKeep`, so a reload keeps it and every `loadLibrary` from a case draws its
project's page. Never kept, null, a run with `--root` takes its one project's page. A reload keeps
the screen in front too, as a restart does: `spotKeep` runs on `pagehide`, and `comeBack` opens the
case, PETs, GETs or Sift it names within ten minutes. Settings opens from the Home on
General, and over it `settingsCase` gives no case, and a project's page gives its project and its GETs
workbook. `PANES` is `PANES_BY_APP[APP]`, Idiograph's `general`, `formats`, `statements`, `pets` and `ai`
since settingsplit (5 November 2026, Adam: Settings holds the app's own settings alone, the same on Home and in
a project), its `gets`, `export` and `project` gone, Sift's `general`, `databases`,
`sift`, `zotero` and `ai`, and Trace's `general`, `trace` and `ai`, the order of Settings' list, which the
arrow keys walk, and the panes' sections in `index.html` keep their own order, one shown at a time.
`screenPane` is the category a screen's own settings open on, `pets` over the PETs and GETs boards, and `PANE_OF`
takes `proposals` for Sift's Projects. Under Sift's Projects, with the switch on, `sfaLoad` lists the Sift projects with a screening, from each card's
`screening`, the one open on Sift's screen first, reads each one's AI settings through
`/api/sift`'s `ai` as it is shown, and `sfaSaves` sends the changed ones with `settings` after the
switch is saved.

**Project settings (settingsplit, 5 November 2026).** Adam: the picker of projects in Settings would be a mess with
sixteen projects, and Settings mixed the app's settings with a project's. So Settings is the app's alone, and each
project's own settings are `#projset`, a sheet in `idiograph.html`'s `cards-more` for one project with no picker,
`openProjectSettings(p)`: the copy the screen behind holds when it is that project (`projectBehind`, from
`settingsCase`), else Home's (`HOME_PROJECTS`), drawn by the same `drawProjectPane`, `drawLabels`, `drawTimecodes`,
`drawTimepoints`, `drawWords` and `drawAgents` as before, `PROJ` now `{ p, own }`. GETs' rules come by
`getsTarget(p)`, the case or board's workbook behind it, a demo's first workbook, or `{ root: id }`, which
`gets_root` takes. A thematic analysis project hides `#words-block` (its codes take no nudges) and `#gets-block`.
The agents' part shows as the saved AI switch says. `saveProjectSettings` refuses on a participant out of GETs with
no reason, then sends GETs' rules and `projectSaves()` (name and question, the tick on its own), and `projectTake`
puts the answer into `S.data.project` and the band, the board's (`thSettingsSaved`), and Home. Shutting it runs
`projsetShut` (the family's `hide`), so a timepoints change opens the screen behind again as Settings did. It opens
from `#hp-settings` on the project's page, the card's menu (`projectSettingsFor`), File, Project Settings…, and the
band's link. The length nudge's row in Settings has no number now, its label the open project's. Include interviewer
notes is `#export-notes` under Markdown and CSV in the PETs board's Export menu: with it ticked, `thExport` asks
`/api/export` with `notes` first, then `/api/themes-export`, whose CSV takes the place of the first's, so the
API is unchanged and the notes file is named with the board's two. `drive_menus_mac.py`'s `project_history` reads
File's Project Settings… on Home (grey), a demo and a project (on) and presses it. Area 328 checks what the sheet
saves and where.

**Idiograph's tabs (20 October).** `nav.ds-tabs` stands on the statements bar, `#es-steps`, and on the PETs and
GETs bar, `#th-steps`, in place of the steps' row, each `.ds-tab` holding its `.ds-tab-name` (the old step ids,
`es-step-*` and `th-step-*`, kept, so `esStep` and `thStepTo` below open them as before) and the tab in front
`.on`, its name `aria-current="page"`. `DS_STAGES` in `app.js` lists the six stages, which a project of one
timepoint and one of two or more each show, and which are built. `dsStages(project)` gives the bar's list,
GETs standing for LGETs until LGETs is built, and `dsTabsDraw(nav, project, here)` hides the rest and marks
`here`. `startCase` and `themesLoad` draw it with the project's name in `#rail-project` and `#th-project`.
The statements tab holds `#es-who`, the participant picker, whose `#es-whomenu` asks `/api/participants`
each time it opens (`esWhoMenu`, `esWhoDraw`), and `esWhoGo` saves the passage in front and opens the other
participant through `navGo` and `openCase`. The PETs tab holds `#th-cases`, the switcher of 178 as it was,
hidden on GETs. `dsTabsKeys` moves the focus along a bar's tabs on Left, Right, Home and End, and
`dsTabsFit` sets `.over` while a tab waits past the right edge, which draws the fade. In `style.css` the
bar round the tabs takes the sunk paper, the tools their icons alone from 1280 to 1439 pixels, ES below
1280, and at 760 pixels and below `.ds-rail` wraps to three rows by `order`, 46, 42 and 33 pixels, with
`--rail-h` at 122px, which the progress strip, the band, `#tp-menu` and `.th-body` take in place of 46. Above
760 pixels `th-names-row` keeps its two rows on PETs, the tabs on the first.

**What the tabs run through (from the steps of 18 October).** The tabs above took the place of a row of
three steps, `nav.sf-steps.ds-steps`, on 20 October, and kept their ids and their code. Each tab's
button carries `data-step` `statements`, `pets` or `gets`, and the first holds `.ds-long`, Experiential
statements, and `.ds-short`, ES, which shows below 1280 pixels (1600 under the steps), its `aria-label`
naming it whole. Sift's steps are drawn by `rvStepsHtml` and keep `.sf-steps`, whose rules stand in
`style.css`, its focus ring `--focus-small`. On the statements bar `esStep` in
`app.js` takes PETs and GETs: the way back, `toLibrary`, where `S.backTo` names that board, else
`openThemes` from `work`, or `esToGets`, which saves the passage as `openThemes` does and opens the GETs
through `openGets` with `to: 'statements'` and the way back to this passage. `P` calls `esStep('pets')`. On
the boards `TH.to`, set in `themesOpen` from `opts.to`, `statements`, `pets`, `gets` or `cases`, says where
the way back goes, by the step's key in `TH_STEPS` (`S.backTo.to` and `TJ.to` too, since i18ncodes of 31
October 2026, which passed the steps' English names, PETs or GETs, between the scripts before), and
`thToPassage`, `searchBoardBack`, `searchToBoard`, `gtFromPets` and `spotNow` read it where they read
`#th-back-word` until then. `thToPassage` names the passage's way back by the step's key of the board it leaves, `lgets` on the
LGETs and `pets` with `timepoint` on a timepoint's PETs, so `esStep` on that step takes the way back, the board
reopened where he left it, where until 1 November 2026 (loose01) the LGETs passed `gets` and a timepoint's PETs
no timepoint, and the step opened that board afresh (area 315). `gtScreen` calls `thStepsDraw`, which marks the step in front and names the
case each other step opens in its title, `gtStepCase` finding it in `TH.gets.cases` by `TH.path`, and
`gtLoad` calls it again once the cases come. Since 26 October (getsB, Adam's option B) the GETs or LGETs
opened from Home's card, `TH.to` of `cases`, take `TH.gets.last` in its place, the GETs answer's
`last_opened`: `last_opened` in the routes reads the recent list, newest first, and answers the first entry
whose case folder is one of the board's cases, `{case, path, timepoint}`, or None, and none on LPETs. In a
project of two or more timepoints `remember` keeps `timepoint` on the entry, the one `/api/themes` opened,
and an open of the statements screen keeps the entry's, so `thStepAt` hands the steps that workbook and
timepoint. `thStepTo` takes a step: nothing for the one in front,
`themesBack` where `TH.to` is that step, else `gtFromPets`, `gtToPets`, which opens the PETs of `thStepAt`'s
workbook at its timepoint with `to: 'gets'` and the way back to the GETs board, or `thToStatements`, which keeps the board's view and
selection as `thToPassage` does and hands `openStatements` in `app.js` `leave`, `back` and `to`.
`openStatements` asks `/api/open`, puts the board away, sets `S.backTo` and opens the case through
`startCase`, at the passage it was on where `S.data` still holds that case. `#th-sticky`, New sticky note,
the first of the boards' own tools, calls `thStickyBar`, which hands `thStickyNew` the middle of
`#th-stage` clear of `#th-side` or `#th-cpanel` lying over it with `free`, so the note is in no PET and
`thSettle` takes it to the nearest place clear of every PET and card, with the room `thStickyRoom` gives it
(see Sticky notes' room, area 182), and pushes the tools right below 480 pixels
where `#th-group` did. The project's page holds `#hp-list` before `#hp-gets`, and `drawPage` draws the rows
before `drawGetsCard`. On the statements bar the rest gives way earlier so the tabs keep their words and
the participant's name its letters: below 1440 pixels `.mark-full` and the round's long words (760 until then),
below 760 `#btn-help` and `#rail-sheet` with the switch's chevron (540 until then), below 480
`#btn-view`, `#btn-guide` taking the tools right, the bar's sides 8px, and below 400
the tools 16px wide. `#rail-part`, `#rail-part-sep`, `#btn-themes`, the PETs bar's `.rail-sheet`,
`#th-gets`, `.th-step`, `#th-back-word`, `#to-library-word` and the `.worded` rules are gone, and the
Tauri drive presses `#th-step-gets`. In the suite, `top_bar_kinds` reads a `data-step` button as a tab,
and `top_bar_problems` fails on a row of tabs split, before the way back or after a tool, or Idiograph's out
of the book's order.

**One title bar.** Every bar's tools, the home screen's Settings among them, are `.bar-tool` buttons, each
holding its icon and its word in a `.bar-word` hidden from a screen reader, the button's `aria-label`
naming it (12 October; Home's tools since 5 November follow the title bars' rule from 761px, see The head's
order). One rule in `style.css` hides every `.bar-word` and, from 1280 pixels (1440
until 13 October), widens each `.bar-tool` to hold its word, 4px of padding each side and 4px between
icon and word, and shows it. Below that width each bar keeps its own sizes and steps.
No screen keeps a rule of its own for its tools' words, so Sift's `.sf-wordy` and `.sf-bword` are gone.
The way back is a place rather than a tool, the arrow alone since 18 October, when `#th-back-word` and
`#th-back.worded` went with the way back's word (see What the tabs run through).
Every bar keeps one order, set down in The title bar in `docs/design.md` and held by area 155's
`top_bar_problems` (16 October): on GETs
`#th-open-cases` first, before the way back, the screen's own tools, then Search, Shortcuts, Send
feedback and Settings, and on PETs and GETs `#th-open-side`, named Inspector, last. Below 480 pixels
`#btn-view` pushes the turn screen's tools right and `#th-sticky` the PETs and GETs bar's (`#th-group` until
18 October), where the
case's name and the board's take `flex-shrink: 1` and `.th-save` shows a failure alone. Since 17
October the board bars' `.rail-case` keeps `min-width: 1.9em` and `.th-vname` `1.8em`, a letter and
the ellipsis, `#th-back:hover` keeps a transparent border, the way back being a place, and
The boards' sidebar in place of the bin (sidebar, 20 October, Adam's way A): no file format change. `themes.LOOSE`, `loose: true` on a card, marks one on the canvas in no PET, kept by `normalise` only for a card in no group, not in `discarded` and not stacked, and sent by `merge`. A card in no PET without it waits in the sidebar's Not placed, so a board from before keeps every card in no PET waiting and reads and writes as it did, and `discarded` is Set aside (`themes.DISCARDED` and `BINNED_HEADING` say Set aside and Experiential statements set aside in the CSV, the draft, the print view and Word). `themes.waiting_keys`, `put_all_on`, `set_aside` and `put_back` do on a board what the sidebar does, `blank_version(..., start)` and `version_op`'s `new` with `start` of `canvas` make every card loose. The command line's `board apply` runs `set_aside`, `put_back` and `put_all_on` in `cli.run_stacks` (`SIDEBAR_OPS`, where `discard` and `bin` answer as `set_aside` and `unbin`, `restore` and `undiscard` as `put_back`), `check_ops` refusing only `delete` (`NO_DELETE`). `board fresh --start` is `cli.cmd_board_fresh`, MCP's `board_fresh`, which on a participant with no file names the new board past the Board 1 `version_op` seeds first (`blank_version([])` among the boards it names it by), so its answer and `id` are the board made (boardgaps, 30 October). Since 30 October (boardgaps, the GRAVITY session's two gaps) `themes.with_new(version, cards)` gives a followed board a card for every live line it has never seen, a statement written after the board was made, at the spot `place_new` finds and not loose, so it waits in Not placed: `merge` places its `new` cards through it, so the page and the API agree, and `cli.cmd_board_apply` and `board_entry` (`board list`'s counts, which now read the workbook) run on `with_new(follow(...))`. Before, `board apply` ran on the file's cards alone while `revise_start` (through `merge`) offered the new statement, so a move into a label passed the applier, said "moved" and was dropped by `land` and `normalise` for want of a card, `put_all_on` (`waiting_keys`) passed it over and `run_stacks` refused it as not on the board. The key's form, `2d:6:0` or `Initial:13:0`, was never the cause. A `move` to null leaves `loose` to the CLI, since the applier knows labels alone: `cli.sent_to_wait` replays the change's moves on `revise_ops` to find, for each move to null, the statements it took out of a label or off the canvas (loose in `followed`, not since put in a label) and those waiting already, `cmd_board_apply` takes `loose` off the ones that end in no label, as `thSendWaiting` does on the canvas, counts that as a change, and words the answer from the moves as they landed, with "Left S9 waiting in Not placed, as it was already" for the rest. Area 294. `board export --set-aside` is `--binned`, and MCP's `set_aside` is `binned`. `board show` and `board list` give `set_aside` beside `discarded`, `loose` on a statement and `waiting`. In `themes.js` a PETs board is `v.waits`, `thWaitsRead` sets each card's `wait` from `loose` on every load and revision on view, `thWaiting` reads `wait` only for a card in no group, not set aside and not stacked, and `thOnCanvas` leaves waiting cards out, so the canvas, the layout, the lasso and the minimap never meet them. `thBody` sends `loose` for a card not waiting. `thSendWaiting` (Take out of PET, `Backspace`, `thLeaveThemes` and `thDeleteKey` through `thWaitDo`), `thDiscard` (X), `thPutOn` and `thJoin` keep `wait`, and `thPut` restores it from a step of undo. The sidebar is `#th-cpanel` on both boards, `gtCasesOpen` on PETs too with its own `localStorage` key (`TH_SIDE_KEY`), `#gt-cases` holding Not placed on PETs (`thListDraw`, `thWaitRows`, in interview order by `thInterviewCmp`, a stack as its top, the missing last) and `#th-aside` Set aside on both (`thAsideDraw`), their folds in `TH_SIDE_FOLDS`. Rows select into `TH.ssel` (`thSideClick`), drag by `thSPullDown`, `thSPullMove` and `thSPullEnd` to `thSideDrop`, and Put all on the board is `thSideAll`. A canvas drag over `#th-aside` is `{ discard: true }` and over the rest of the panel `{ wait: true }` in `thTargetAt`, armed by `thSideArm`. `#th-discard` stays in the page hidden. `thSelectAll` is Cmd + A and `#th-selall`. The status bar's `loose` count, said only when it is above 0, and `binned` say In no PET and Set aside, and `.th-stat-go` on Not placed and Set aside opens the sidebar on its section (`thListOpenAt`). `thDoorCount` names the left panel's button Statements or Cases and carries the waiting count.

The status bar and the palette (19 October): `#th-status` is the `.th-zoomer` with `#th-status-counts` first and `#th-help` last, and `.th-status-on` on `#th-stage` lays it along the foot. `thStatusDraw`, run from `thDrawCounts`, `gtDrawCounts` and `thSettingsSaved`, writes the counts from `thStatusNumbers` and `thStatusWords` as the settings' `status_bar` and `status_counts` say. Since 26 October (wording C, Adam's choice of countskofi's drawings) `thStatusSum` folds the parts, `TH_STATUS_PARTS` (placed, stacked, binned, unplaced, loose, in the order Adam ruled on 26 October), into one `.th-stat-sum` (`data-stat="sum"`): `.th-stat-total` with the total, `.th-stat-unit` (`ES` on PETs, `card` or `cards` on GETs, LGETs and LPETs, `Cards` with no total), then each part a `.th-part` with its `data-stat` and its own `.th-sep` comma, Not placed and Set aside still `.th-stat-go`. The total is left out when a part unticked in `status_counts` holds anything, so it always equals the parts shown, and `thStatusSumText` says it for the tooltip. `data-stat="pets"` follows, then `thStatusSelected`'s count, "1 ES selected", and the close pairs' count. `.th-status-least` hides `.th-stat-total` and every `.th-part` but placed and unplaced, `text-transform: capitalize` on the unit, and `.th-status-bare` hides the placed part and the comma after it. `#th-status` carries `role="toolbar"`, which `shot_box` reads to treat it as a bar. Area 264 runs `thStatusDraw` in node on invented PETs, GETs and LPETs boards and checks the total equals its parts and the cards the board holds. `thCorners` sets `--th-status-h` and adds `TH_STATUS_STEPS` a step at a time while the bar overflows, in the order Adam set on 26 October 2026, the counts last: `.th-status-short` (the tools' words, each tool's `title` its word), `.th-status-opt` (the selected and close pairs' counts), `.th-status-shortest` (the spacing closed up), `.th-status-shorter` (the pointer and hand, the minimap's button and Shortcuts), `.th-status-tiny` (the zoom's minus and plus and the pairs' steps), `.th-status-lean` (Quotes, Notes and Close pairs), `.th-status-trim` (the PETs count), `.th-status-least` and `.th-status-bare`, no 767px query hiding a count any more (`#th-faces` stood here from train 71 until tablemove moved it to the toolbar). Area 201 reads the order and what each step hides, and area 269 runs the bar with the page's stylesheets in a headless browser at the canvas's width in a 1280 window and at 720, `#th-status-counts` never shrinking so no word is cut, and `thStatusDraw` runs it again when a count's words change, and `thMapPlace` takes the map's width from the pointer to the bar's end. `#th-smenu`, from a right click, saves `status_counts` through `thStatusSave`. `#th-palette` holds `#th-sticky`, `#th-group`, `#th-undo` and `#th-redo`, `thPaletteGrab` drags it by `#th-palette-grip`, `thPaletteDrop` gives the edge and the share of the room, saved as `palette_place`, and `thPalettePlace` draws it. `server.py` cleans the three keys with `status_counts` and `palette_place`. The toolbar (21 October): `#th-palette` moves between `#th-dock`, a strip after `#th-band` whose height `thBandMeasure` adds to `--band` (each measured to the fraction by `getBoundingClientRect` since 31 October, loose31, where `offsetHeight` rounded the band's 55.25 px down and the screen stood a quarter pixel taller than the window, the status bar's foot under its edge), and `#th-stage`, by `thPalettePlace` as `thDocked()` reads the setting `palette_docked` (true unless the file holds `false`), `.docked` laying it in a row. Each tool carries `.th-pal-word`. `thPaletteFit` adds `.snug` (Select all's word), `.terse` (Align's and Spread's), `.bare` (every word) and `.fold` (`.th-pal-fits` hidden, `#th-pal-more` shown). Docked, since 26 October (option B, Adam's choice of tablemove's drawings), `.fold` always, then `TH_DOCK_STEPS`, `.snug` and `.bare`, a step at a time while the bar overflows, so at 1280 Sticky note, Group, Auto-arrange, Undo and Redo keep their words, and floating `.fold` then `.bare` while the column is taller than the canvas, run from `thPalettePlace`, a ResizeObserver on `#th-dock` and `document.fonts.ready`. `thPaletteGrab` pulls a docked toolbar off after 5 pixels, shows `#th-dock-slot` while it moves, and docks it when `thPaletteDocks(pointerY, stageTop)` says so, saving `palette_docked` and `palette_place` in one `thStatusSave` (its third argument), since two writes at once raced for the settings file. Auto-arrange's ways: `TH_ARRANGE_WAYS`, `thArrangeWay()` from the setting `arrange_way`, `thArrange(v, gid, size, way)` (`cols` 1 for Column, all for Row), `thArrangeTool` for `#th-arrange`, `thArrangeMenu` for `#th-arrange-way` through `thToolMenu`, a `.th-tbmenu` row menu whose `button` `thMenuClose` sets back to `aria-expanded="false"`. Align and Spread: `thAlignIds` (the selection, nothing inside a selected label), `thAlignPlan(boxes, how)`, pure, the same as `themes.align_plan`, `thAlignDo`, one `thDone` with the moved block settling clear, `thPaletteState` from `thDrawSel` setting `disabled` (two for Align, three for Spread), `thAlignMore` for the dots, its rows from `thAlignMoreRows`, `thAlignRows` with the buttons' words (`TH_ALIGN_WORDS`) and a `head` on the first of each section, Align and Spread, which `thToolMenu` writes as a `.th-cmenu-head` before the row, `thAlignRows` making every row faint on a revision on view as `thPaletteState` does the buttons, and in `thMenuItems` an `alignsub` entry whose row opens `thAlignSub`, a `.th-subpop` on the page beside the menu kept as `TH.menu.sub`, which the press outside and `thMenuClose` respect. The Mac and Windows menus' View, Status Bar calls `window.thStatusToggle` through `window.js`. Quotes on cards (19 October, later): `#th-quotes-btn` after `#th-map-btn`, `aria-pressed` set by `thStatusDraw` and `thQuotesDraw`, calls `thQuotesToggle`, which saves `card_quotes` through `thStatusSave` (`server.py`: off unless the file holds `true`) and draws the board again. `thKqHtml` puts `.th-kq` under a card's `.th-text` from `thCardQuote`, on PETs the row's quote in `TH.quotes` at the statement's place, on GETs a statement card's from its case's copy (`gtLineQuotes`), its inverted commas taken off by `thBareQuote`. A press on `.th-kq` sets `kq` on `TH.press`, and a click with no drag opens `#th-kqpop` by `thKqOpen` beside the card (`thKqSpot`: right, left, under or over, inside the canvas above the status bar, the place covering least of the boxes `thKqOthers` gives, then the side with more room), its play button through `thPlayQuote` on PETs and `[data-kqgo]` running `thKqGo`, `thToPassage`. Esc in `thKeyDown`, a press outside and the wheel close it. The counts left the bar then, so what follows held until 19 October: `#th-count` was `flex: none`, never cut: `thCountSet` writes it with the discarded in `.th-count-bin`,

Quotes in three ways (30 October, quotes3, Adam: "full quotes on each card without having to click anything"). `thQuotesWay()` reads Off, Short or Full from `card_quotes` and `card_quotes_full` (`idiograph_routes.py`: `DEFAULTS`, `merge_config`, `save_settings` and `OWN_SETTINGS`, off unless the file holds `true`), so a file from before reads as Off or Short and an app from before reads Full as Short. `thKqHtml` gives Short's `.th-kq` as before, `data-kq` and the whole in its `title`, three lines by `-webkit-line-clamp: 3`, and Full's `.th-kq.th-kq-full`, the whole quote with no `data-kq` and no `title`, `display: block` with the clamp lifted, so a press on it is a press on the card (a click selects, two open `thCardEditOpen`) and `#th-kqpop` never opens. `gtUnfoldHtml` gives `.gt-uq.gt-uq-full` the same way at Full. `thMeasure` measures a whole quote as it measures a short one, so `thRoomMake` and `thStackRoom` (with subgap2's `thRoomTrack` and `thRoomBy`) make its room unchanged. `TH_QUOTES_CONTROL` holds the way the button sets it, `'cycle'` (A, in force) or `'menu'` (B), both drawn for Adam: `thQuotesToggle` takes the next of `TH_QUOTES_WAYS` in A and opens `thQuotesMenu` in B, and in both a right click or a press held (550 ms, as Close pairs') opens `#th-qmenu`, a `.row-menu.th-cpmenu.th-qmenu` drawn by `thQuotesMenuDraw`, its rows `.th-qway` with `data-qway`, its foot `TH_QMENU_GAP` (10) over the bar, so a review shot's box round it clears the bar. `thQuotesSet(way)` saves both keys in one `thStatusSave('card_quotes_full', ..., { card_quotes })`, the key checked for a server from before being the new one, and `thStatusSave` draws through `thQuotesDraw`. `thQuotesButton`, from `thStatusDraw` and `thQuotesDraw`, sets the button's `data-quotes`, `aria-pressed` (Short and Full), its `title` and `aria-label` from `TH_QUOTES_TIPS` ("Quotes: full"), and in B `aria-haspopup` and `aria-expanded`. Its `.th-quotes-mark` after `.th-btn-word` holds `.th-qm-short` (two lines) and `.th-qm-full` (four), shown by `data-quotes`, `visibility: hidden` at Off so the button keeps its width. `thKeyDown` stops every key at the window (`e.stopPropagation()` before the right-click menu's lines), so the document's Esc listeners for `#th-smenu` and `#th-cpmenu` never heard it: since 30 October `thKeyDown` puts away `TH.qmenu`, `TH.cpmenu` and `TH.smenu` on Esc itself. Area 304 runs it in node.

A tester's feedback on the boards (20 October). **Own and outside changes.** `workbook.WRITTEN` maps each file this process wrote, by its resolved path, to its `st_mtime_ns` after the write: `themes.write`, `gets.write` and `workbook._atomic_save` call `note_written`, which keeps the newest `WRITTEN_MOST` (500) and then calls `WRITTEN_HOOK`. `written_here(path)` is true while the file's time is still the one noted. The command line and the MCP server write in processes of their own, so nothing they write is noted. `server.keep_written_on`, from `main` alone (the CLI imports `server` and never calls it), loads the state's `written` through `workbook.still_written`, which keeps only the files whose time is unchanged, and sets the hook to `keep_written`, which stores the list as `written` in the app's state under `STATE_LOCK` (also held by `save_state`), in `state.json`, or in `STATE_MEMORY` for a `--root` run, carried across its restart as the rest of its state is. So after a restart a file left as the app wrote it is still its own, and one changed while the app was closed is outside. `/api/stamp` gives `outside` and on GETs `cases`. The page's `thStampTick` loads a change of its own by `thOwnLoad` (the canvas flushed first, its undo cleared when the board on view changed) and takes each own case by `gtTakeAll` (one undo step, a History line "Before X's changes came in" from `gets.take`, the toast from `gtTookSaid`), which also runs at the GETs screen's open. An outside change shows `#th-outside`, "Changes made elsewhere" with Update, its tooltip from `thOutsideLine` or "X: PETs changed outside Idiograph.". `thOutsideShow` runs `thOutsideTake`, its cross `thOutsideClose` keeping the cases left in `TH.farLeft`. `#th-take`, `gtTakeOpen` and `gtTakeGo` are gone, and `th-take` with them from `OVERLAYS` in `app.js`. **Take out.** `thLeaveLabel` words the move, "Take out of PET", of GET, of sub-theme or of group, in the Inspector as `button.btn-out` with its arrow and in the menu, `leave` no longer in `TH_TAKES`, so never red. **Group and Ungroup.** `thGroupItems` adds `groupsel` (as `G`, the card alone when not selected) and `ungroup` when `thUngroupOf` finds the selection is the whole of one label, deleted as Delete this label does. **Notes on cards.** `#th-notes-btn` after `#th-quotes-btn`, shown on GETs alone, calls `thNotesToggle`, saving `card_notes` (`server.py` `DEFAULTS`, `merge_config`, the settings allowlist: off unless the file holds `true`). `thEnHtml` gives `.th-kq.th-en` from the case's line `notes`, and `thMeasure` measures it with the quote. `.th-btn-word` gives Minimap, Quotes and Notes beside the icons, hidden off the status bar and at `.th-status-short`. **Stacks on GETs.** `gtStacked` reads each line's `stacked`, and `gtTree` returns `under`, a top's stacked keys, so the Cases panel shows "N stacked" (`.gt-stk`, its fold `case/stack/key`) and the PET's Inspector "Stacked under it", never Not in a PET. **The card's source line.** `gtFrom` says "PET: title · GET: label" or "PET: title". **Every PET placed.** `gtTally(v)` counts the study's PETs and sub-themes, with a card or not, `left` those in no GET and not wholly binned, `placed` those under one, and `thMomentum` raises nothing on GETs unless `placed` rose.

A PET card unfolded in place on GETs (21 October, Adam's ruling of 20 October, topic 9). `gtUnfoldable(key, c)` is true for a `pet` or `sub` card, not `gone`, whose PET in its case's copy (`gtUnfoldPet`) holds a statement or a sub-theme. `gtCardHtml` then gives the count as `button.gt-unfold.gt-n` with `GT_CHEV` and `data-unfold`, and for a key in `TH.unfolded` adds `gtUnfoldHtml`'s `.gt-unfolded` after the foot: `.gt-ulist` of the PET's own statements, then per sub-theme `.gt-usub` and the statements under it at any depth, as `gtTree` walks them, each `.gt-uline` its words, its own quote (`gtLineQuotes(line, key)[0]`, `.gt-uq`), its notes when `thNotesOn()` (`.gt-uen`) and its timecode, a stacked line (`gtStacked`) only under its top in `.gt-ustack`. The click handler on `#th-world` and `gtMenuItems` (Unfold or Fold after Inspect, act `unfold`) call `gtUnfold`, which toggles the key, keeps it, and draws with `thRender` and `thEase`. `thPointerDown` skips `.gt-unfold`, so a press there neither selects nor drags. `thMeasure` counts `.gt-unfolded` with `.th-kq` in `qextra`, so `thRoomMake` gives the card its room as a view in `TH.shifts`, which `thBody` takes back off, and `thSize` reads the whole height for Auto-arrange, `gtByParticipant` and `thFit`. `gtUnfoldKeep` and `gtUnfoldRead` (from the board load, keeping only keys among its cards) hold the set in `localStorage` under `idiograph-gets-unfolded`, by `thFaceKey('gets', TH.path, board)`, the key the board's Canvas or Table view is kept under. Nothing reaches the GETs file or the server. Area 233.

Descriptions (21 October, desc, Adam's ruling on the drawings): a label's `description`, the longer line under its short title. `themes.description_of(group)` reads it on one line, `""` for none, and `themes.normalise` keeps it after `note` only when it has words, so a board with none writes as before, byte for byte. `land` and `land_kept` carry it, `outline` gives it on each theme, and `descriptions_shown(board, on)` drops it from an outline for an export with the tick off. `label_size(text, upper, marks, description, body)` adds `DESC_LINES` at most (six since 31 October, two before) at `DESC_SCALE` (0.8) of the title's size, `DESC_LEADING` 1.3 and `DESC_GAP` 2, the page's `.th-desc`, so `layout_boxes`, `blob`, `arrange` and `themes_ai._blob` lay a described label out at its height. Since 31 October (labeldesc, Adam: "I'd rather have it wider than deeper") a described label runs as wide as `body`, the width of what it holds, where that is wider than `LABEL_W` (340), its title and its description wrapping there, so a frame is never wider for it: each of those four passes the body it has just laid out, `arrange` its inner block's width. A label with no description, or none under it, is sized as before. On the page `thLabelsWiden(v, els, sizes, size)`, run by `thMeasure` after the cards and notes are measured and by `gtBesideRender`, clears each label's inline `max-width`, measures them at the stylesheet's 340, lays the board out once (each label's `x` and `y` put back after) and gives each `.described` label whose body is wider than `TH_LABEL_W` that body's width as its `max-width`, then measures those again. A label at its widest leaves every frame as wide as before, so the bodies come right from the first measure and one pass is exact. The taller or shorter label then goes through the settle and `thMakeRoom` as any label that changed size does. `thTitleOpen` keeps such a label's width in its two boxes, where it held them to 300 at most. The GETs board's PET cards (`.gt-desc`, `gets.card_height`) keep their two lines, a card's width being fixed. The operation is `themes_ai.revise_ops`' `describe`, `DESCRIBE`, which the applier takes only from a board marked `human`, as `cli.cmd_board_apply` and `cmd_gets_apply` mark theirs, never from an AI revise, `change_line` saying "wrote the description under" or "took the description off". `board new` reads `description` on each label, `board show` and `gets show` give it and a `Description:` line. On GETs the case copy's `pets` carry it through `gets.described` only when set, so a copy's hash is as before without, `cards_shown` puts it on a PET's or sub-PET's card and `gets.table` on each GET, and `gets.layout_text` puts it after `DESC_MARK` in the words `gets.card_height` estimates a card from, two lines at most. The page: `thDescOf`, `thSetDesc` and `thDescStep` beside the note's helpers. `thRender` puts `.th-desc` in `.th-words` under `.th-title`, `.described` on the label, the whole in its `title`, and `gtBesideRender` the same. `thTitleOpen` opens `.th-desc-box` under the title's box, `TH.editing.desc`, Tab or Shift + Enter moving to it and Enter keeping both from either box (22 October, area 252), a blur to the other box no click away, and `thTitleDone` sets both in one step. `thMenuItems` gives Add description, or Edit description and Remove description, acts `desc` and `undesc` (`thDescOpen`, the Inspector's box in the Table view, and `thDescRemove`). `thDescHtml` puts `#th-gdesc` first in a label's Inspector on PETs and GETs, `TH.describing` holding it open as `TH.noting` holds a note, `thDescHeld` and `thDescRefocus` keeping its caret while the panel draws, and `thNoteDone` closing it too. `thTableHeadHtml` adds `p.tb-desc` after `.tb-head.tb-described`, in the band. `gtCardHtml` adds `.gt-desc` from `gtCardDesc`. The Descriptions tick: `export_descriptions` in the settings, true unless the file holds false, in `TH_INCLUDES` and `TH_INCLUDES_ON` (`thIncluded` reads it on unless false), `#th-inc-descriptions` under Export and `#gt-print-descriptions` on the GETs print card, `descriptions` in the print view's, the GETs print's and Word's requests, read by `server.export_descriptions`. `themes_print` sets `.desc` inside the heading, its tick first in `INCLUDES`. `themes_word` a run after `<w:br/>`, `DESC_SIZE` 20 and `DESC_COLOUR` 595959, not bold, not italic, no capitals. `gets_print` `.gdesc` in a GET's bar and trail head through `get_desc`. `board export` and `gets export` take `--no-descriptions`, MCP `descriptions: false`. Area 242.

A title open in place (subpetjump, 10 November 2026): a label sits on what it holds, its foot fixed, `thLayout` setting its `y` from the body's top less `TH_GAP` and its measured height. Until then `thTitleOpen` put the title's and the description's boxes into the label in the title's place, so the label grew by the boxes' padding and the second box, and the next `thMeasure` and `thPlace`, run on every key, lifted it by as much, a sub-PET's over the sub-PET above it, until the edit ended and the board was drawn again. Now the two boxes go in `.th-title-boxes`, laid over the label (`position: absolute` in the title's column, `.th-label.editing .th-words` relative, the label `z-index: 4` over the cards), the title and its description kept unseen with `visibility: hidden`, so the label keeps its size and nothing on the board moves while the boxes are open or when they close. The title's box stands `TH_TITLE_INSET` (7px, its border and left padding) left of the column and 3px above it, its inside the column's `offsetWidth` and a pixel more (the width rounds down), its right border and 2px padding (`TH_TITLE_RIGHT`) in the gap before the label's icons, 180 at least, with no `max-width`, so its words stand where the title's stood and wrap where they wrapped, a label run wider for its description included. The description's box sits under it at the same width, in the description's size and leading (until then `.th-title-edit`'s `font-size: inherit` won over `.th-desc-box`, so it opened at the title's size), and the label's icons are hidden while the boxes are open. GETs, LGETs and LPETs take the same function. A statement's box on its card (`thCardEditOpen`) never measured the board while open and needed no change. Area 80 holds it.

Descriptions kept (22 October, descloss): on a real board every description went in one session of edits, because the page's `thBody` sent a hand-picked few of each label's fields, so any save from the canvas, a rename, a reorder or a move, took every description off. The page now sends each label whole through `thLabelOut`, its note when it has one and its `description` always, `""` for none, and `thReviseTake` starts each label from the one the page held, so an AI revise keeps what it does not speak of. On the server `themes.descriptions_kept(kept, sent, held)` gave a label the page sent with no `description` key at all the file's, in `themes.save` and `gets.save`, so a page loaded from an older copy of the app never takes one away, and one sent `""` is taken off. Since 11 November (domainkeep) `themes.fields_kept` does it for every field but those a page always sends, the description among them. `copy_into` carries each label whole under its new id, and `gets.revise_start` each GET but its place. A page loaded before a description was written meets the stale-save notice as any outside change, its canvas kept in History. Area 247 drives the page's save, turn write, every `board apply` op that rewrites labels, a restore, a copy, `gets take` and the GETs board's save, the description read from the file after each.
and `thCountFit`, run from it, from `thSaveLine`, from `thDrawBoard` and by a `ResizeObserver` on
the bar, adds `.short`, which hides the discarded, while the bar overflows or the name is cut, then
`.gone`. Since 17 October, later, it measures on one row every time, and where a name or a switcher is
still cut once the counts have gone, counts or none, it gives `#themes` `.th-names-row`, at any width
since the screenshot check of 17 October that found a long name cut at 761 pixels and above, where a
`matchMedia` for 760 pixels had held it: the bar wraps to 76 pixels, its `::after` at `order: 1` and a
whole row's basis breaking the rows, every child but `.rail-btn`, `.rail-grow`, `.th-count` and, since 18
October, `.ds-steps` at `order: 2` on the second row, and `.th-body` takes 76 pixels (88 since 23 October) off its height for 46. On two rows the
counts come back whole and step down again only while the bar runs past its edge or its foot, its
`scrollHeight` over its `clientHeight`, which is the first row wrapping, and `.th-cpick` and `.th-vpick`
take `flex: 1 1 0` and `max-width: max-content`, so the second row never wraps to a third and the two
names share what it leaves. Inside `.th-cpick` the `.rail-case` takes `flex-shrink: 1`, the whole of the
switcher's narrowing, where the bar's `.01` gave it a hundredth (a factor under 1 alone in a flex line takes
only that fraction of the overflow) and a long case name ran past its switcher over the chevron and PETs, on one
row as on two, so the label ends in its ellipsis inside its box. The measure has no mode and no width in it, so PETs and GETs take one
rule, and it starts from one row each time, so the observer's one call after the bar's height changes
finds the same rows and stops. Since 23 October (toggleplace) it takes the bar's narrower forms first, `TH_FIT_STEPS`, `.th-fit-save` (the save state its mark alone, as below 900 pixels) and then `.th-fit-es` (ES for Experiential statements, as below 1280), each kept only while the bar is still short, and gives `.th-names-row` only where a name is cut after both, taking both off for it. The tabs, the project's name and the mark's stamp joined the bar in 0.9.3's train (8e44132, 21 October) and the PETs bar then needed about 1,340 pixels, so from 0.9.3 the board, its save state and Canvas and Table took the second row at 1280 and at 1400 with long names. The second row is 88 pixels since, `row-gap: 0` and a 4 pixel `::after`, where at 76 with a gap either side of the break the 30 pixel switch hung 10 pixels below the bar. `gtWhere` keeps its classes, and `GT_WHERE_SAID` gives the Cases panel's word, "not placed"
for `unplaced`, the word the bar, the Inspector, Take the changes (`gets.changes`, `NOT_PLACED`)
and the manual use for a statement on no PET. Appearance
left every bar for Settings, General: `#appearance-set`, three radios named `set-appearance`, whose
`change` calls `theme`, which sets `html[data-theme]`, keeps `idiograph-theme` in `localStorage` as
before, `system`, `light` or `dark`, ticks the row through `drawAppearance`, also run as Settings
opens, and sends `idiograph-theme` on `document`, on which Sift draws its flow again. `THEME_TITLE`,
`cycleTheme`, `#btn-theme`, `#sf-theme`, `#sfs-theme` and `#tr-theme` and their glyph rules are gone.
Every bar's bug is a `.rail-feedback`, and `drawFeedback` sets `hidden` on all of them, the home
screen's `#lib-feedback`, Sift's `#sf-feedback` and the ones the searches' and Trace's builders make,
`#sfs-feedback` and `#tr-feedback`, hidden as built until the page has heard the server
(`tbBugHidden`). `openFeedback` keeps the screen's word: `home`, or `project` while `#home-project` shows, `statements`,
`pets`, or `gets` while `TH.mode` is `gets`, `sift`, `searches` and `trace`. The server's
`FEEDBACK_SCREENS` and the collector's `SCREENS` are the same fixed list, held equal by area 160, and
each takes any other value as none (16 October). Sift's, the searches' and Trace's keys wait while `#feedback` is
open, as they wait on Settings. Send, `#feedback-send`, is disabled while `#feedback-text` is empty or holds only
spaces (`feedbackReady` in shell.js, run on the box's `input`, in `openFeedback`, since the words stay in the box across
opens, and as a send ends), in the look every disabled primary button has (`button.primary:disabled`, Done on /design),
and `.busy` on it, put there by `sendFeedback` alone, gives the progress cursor while a note is on its way
(29 October 2026). A key that sends finds the box empty and does nothing, as `sendFeedback` always checked. The note
box never scrolls sideways: `.question-box` and Sift's `#sift-search textarea` take `overflow-x: hidden` with
`overflow-y: auto`, a long note scrolling up and down only. WebKit, the engine of the Mac window, lays a textarea's
placeholder out wider than the box at any page zoom but 100%, by about the box's width times the zoom less one (43 px
in a 450 px box at 110%, 107 at 125%, 213 at 150%, measured in WKWebView), and `overflow: auto` then drew a
horizontal bar with a near-full thumb under the empty box. The window's zoom (`keep.rs`, Text size Large is 125%) is
how it got there, and a browser tab at 100% shows none. The textareas that set overflow auto without a placeholder, `.prompt-box`,
`.bench-box` and `.bench-prior`, show no bar at any zoom and are left as they were. The statements screen's View, `#btn-view`, takes 55 pixels with its
word: at 1280 with Work in rounds off a name of 30 letters keeps 439 pixels of room, and with rounds on
it ended in its ellipsis before View came, 218 pixels for a name that needs 240, and had 159 with
View and Appearance both there, and has its room from before View again now.
The turn screen's bar holds the most, so since 13 October, Adam's choice, its part's name `#rail-part`
with its rule and the line to today's target `#rail-daily` leave it below 1440 pixels (since 18 October
the part's name is Idiograph's first step, `.ds-long`, which gives way to `.ds-short`, ES, below 1600), its items stand
8px apart (`#work .rail`) and its tools 4px, the round's short bar is 40px, and `fitSheetSwitch` in
`app.js` sets the sheet switch to the width of the sheet it shows, where a select is as wide as its
longest option. Below 480 pixels the switch gives way once the case name has given all of its own
(`#work .rail-case` shrinks a hundred times faster), so a case of two sheets fits at 360. Measured at
1280 pixels with the words shown, each bar with an invented name of 30 letters (13 October, later):
the turn screen's needs 1198 on a case of two sheets, 1224 on its second sheet, and 1422 marked
complete with turns undecided, where the name gives way to its ellipsis. It needed 1643 on that case
and 1476 on the demo before. PETs' needs 1114, 1251 with the way back's word, GETs' 1049, Search
strategy's 973, Screening's 1195 on the table and 1250 on a record with its PDF, as Extract and
appraise's does, and with Second screener shown 1320 and 1376, where the review's name gives way to
its ellipsis, its whole name and run in its title. The home screen's Settings holds its word. So the
shared width is 1280. At 1440 the turn screen's bar holds its part's name and the line to today's
target again and needs 1505 on that case, so there a name of 30 letters ends in its ellipsis until
the window is about that wide.

**The place in the turn screen's bar.** `#rail-place` holds the speaker's name in `#rail-who`, the
word passage in `#rail-unit`, the numbers, " in this round" in `#rail-in-round` and its narrow form
" in round 1" in `#rail-in-round-n`, a `.rail-short` that `drawRoundsShown` hides with Work in rounds
off. The place keeps "passage" and the numbers at every width and gives way in order (16 October),
the speaker's name, then the sheet's label, `#rail-sheet`, or the switch's select narrowed
to its chevron, at steps in `style.css` measured on Juno and on
a scratch case of two sheets, rounds on and off, with and without the demo tag: with rounds on at
940, 760 and 620 pixels, with them off at 620 and 540. Below 620 pixels `#work #rail-in-round-n`
goes, the round left to the title, so the place reads "passage 7 of 16" with rounds on as with them
off, and the sheet's label goes at 540 for both (16 October, later), where with rounds on the label
and the word passage went at 620. Two ids outrank `#work.es-reopened .rail-short`. `#work.es-reopened` takes the short form at
every width, since the mark stands before it, where with rounds on it ran 29px past the window at
1280. Nothing overlaps or scrolls sideways from 360 to 1440. The place's title names the passage and
the round's count, "Juno, passage 7 of 16 in this round, round 1 of 3". The way back, `#back-to-turn`,
sits in a 44px strip at the foot of `.transcript-wrap` that `.away` gives it, `wayBack` setting both,
so it never covers a line, and `centreCurrent` takes the strip back before it measures. `cheerLine`
writes Celebrations' line in Settings from the Work in rounds tick as it stands. The thin line's
title says decided, "120 of 300 passages decided", as the bar's Every passage decided does, and a
Save that cuts the rounds again says "The rounds are set again." (16 October, later).

**The statements screen's view (16 October).** `larger_passage` in `config.json`, read by `largerPassage` in
`app.js` from `S.data.config`, on when absent, and `drawView` draws the columns in their order (`drawColumns`,
see The three columns), sets `#work.same-size`, places the card and the notes field and draws the View
menu's rows. Until 17 October `notes_place` stood beside it, `right`, `left` or `under`, read by
`notesPlace`, and `drawView` set `#work.notes-beside` and `#work.notes-left`, the notes beside the words in a
grid of the transcript's column by a container query on `.transcript`, from 640 pixels of column and 540
where the margin lay along the top, or under the statements in `#d-en` in the panel, with its dot
`#dot-en` and its head `#notes-head`. There is one notes field, `#en`: `placeNotes`, from `markCurrent`,
moves it into the current passage's `.turn-notes` cell, and `parkNotes` puts it back in `#es-park` and
the cell's text back from its row, before `drawTranscript` replaces the rows. So `commit`, undo, `Tab`,
`isEntryField` and `drawAct` never know where the field stands. `growNotes` keeps it two lines high. The
column's click, mouse-up and right-click handlers leave the current passage's cell to the field, and a
click in another passage's cell goes there through `goTo` and focuses the field. `centreCurrent` stands a
current passage taller than the column with the lowest of `#en` and `#es-card` under its words 24 pixels
above the column's foot, where centring left the field below it, as far as its speaker line allows.
`#work.same-size .turn.current` takes the other passages' size, padding and measure, 15px, 1.6 and 54ch,
on `--paper-sunk` with an inset hairline in `--rule-firm`, and drops the orange bar. `#btn-view` opens
`#view-menu`, a `.row-menu` of the tick label for the larger passage, then the minimap's, a tick from the
evening of 16 October and since 17 October, later, three radio labels under `.view-head`, their
`accent-color` and Settings' ticks' `--ink` since 16 October, later, so the orange stays the quotes'
and the crux's, placed under the button by `viewMenu` as the PETs export menu is, shut by `Esc` and by a
press anywhere else. Its three radio labels for the notes' places went on 17 October. `setView` draws
the choice at once and sends that one key alone to `/api/settings`, the restart line answering a server
that does not keep it. Settings' View rows are read on open, and Save sends a key only when it has moved
since (`S.viewOpened`), each compared as JSON writes it since the order is a list, so a card opened over
PETs or the home screen never puts back a choice the menu made. `api_settings` saves `larger_passage`
with the other ticks.

**The three columns (17 October).** Adam's decision on a tester's "J-way", Smith, Flowers and Larkin
(2022), Box 5.4: the statements screen is experiential statements, the transcript and exploratory notes
side by side, each passage a row across the three, where until then `.stage` was two columns,
`minmax(0, 1fr) var(--desk)`, the transcript beside `section.desk`, the panel of fields for the current
passage alone, whose notes could stand beside the words. `.stage` is a block now and `.reading` holds
`.cols-head`, the scrolling `#transcript` and the player, up to 1480 pixels wide. `statements_columns` in
`config.json` is read by `columnsOf` in `app.js` as the server reads it, `COLUMNS` the book's order,
`NOTES_PLACE_COLUMNS` an old place's nearest, where until 18 October `COLUMN_ORDERS` listed the six for
Columns and Settings. `drawColumns`
sets on `#work` what `colsVars(order)` gives: `--es-col`, `--tx-col` and `--en-col`, each column's place
among three, `--cols`, the tracks in their order from `--es-track`, `minmax(210px, 2fr)`, `--tx-track`,
`minmax(300px, 3fr)`, and `--en-track`, `minmax(160px, 1fr)` (the notes 1, the transcript 3 and the statements 2
since 6 November, from Adam's own widths, where they were 3fr, 5fr and 3fr), `--es-col2`, `--tx-col2` and `--cols2` for
the two columns up to 800px, and `--es-ord` and `--en-ord`, the order the statements and the notes follow
the words at a phone's width. It moves each `.col-head`, a `gripHtml` grip and its name, into that order
before `#cols-pick`, so Tab and a screen reader meet them as the eye does, and says the columns shown in
Columns' title (`columnsShownSaid`, 18 October), its word alone at every width (until 18 October `#cols-pick-said` said it beside the word
where the last heading left the room, which only the transcript's heading at 800 pixels did), the
transcript's heading 108 pixels in, over the words, and 12 at
1000 pixels and below, as Adam's drawing has it. Each `.turn` and `.round-mark` is a grid of `var(--cols)` with
`--col-gap`, `.turn-text`, `.turn-edit` and `.quote-preview` in `var(--tx-col)` 108 pixels in, `.turn-es`
and `.turn-notes` each spanning the row's rows in their own, and `.turn-gutter`, `.turn-done`, `::before`
and `::after`, absolutely placed, taking `grid-column: var(--tx-col)` with their rows auto, so the
transcript's column is their containing block across and the row's padding box down, and the margin
stands at the left of the words in every order. At 1000 pixels and below the margin lies along the top in
the same column, a round's marker its name over its rule in one row. `@media (max-width: 800px)` takes
`--cols2`, puts `.turn-notes` in the transcript's column under the words and hides the notes' heading, and
`@media (max-width: 600px)` (560px until zoomsweep, 30 October, where a 576 window, 720 at Large, scrolled
the two columns sideways) makes `.turn` a column of flex, the words first and the cells after by `order`,
and hides `.cols-head`. `measureColumns`, on `drawColumns`, a resize and a `ResizeObserver` on
`#transcript`, sets `--sb`, the room the column's scrollbar takes, which `.cols-head` leaves at its right,
marks the last heading on screen `.col-last` with `--pick-w` of room for Columns, sets `#work.cols-tight` where its
longest word, measured in a probe, would not stand whole beside the word, Columns then keeping its
chevron alone so no name is cut through a letter, `--flash-x`, the middle of the
transcript's column for the count, and `#work.guide-whole` with `--guide-w`, the sheet's width over the
last column whole above 1100 pixels where that column is `GUIDE_WHOLE`, 300 pixels, or more. A grip
moves its column: `colGripDown` on a `pointerdown` in `#cols-head` follows the pointer on the window, marks
the nearest gap from `colsGaps` with `.drop-before` or `.drop-after`, a bar in `--ink`, and on the let go
`colsMoved(order, name, before, shown)` gives the new order, which `setView('statements_columns', ...)`
keeps, and `colGripKeys` moves it a place on `Alt` and the left or right arrow through `colsStep`, the
column out of sight keeping its place, the grip keeping the focus and `#cols-said` saying its new place.
`#cols-pick` opens `#cols-menu` through `colsMenu`, shut by `Esc` and a press elsewhere, where until 18
October its six radio rows, drawn by `drawColsMenu` with the book's marked `.cols-book`, chose the order and
Settings' View held them as `#set-columns` (see The columns shown, hidden or stacked). `turnHtml` gives each of her passages a
`.turn-es` cell holding `statementsHtml(row)`, an `.es-list` of `.es-go` buttons, each its `.es-n` and
`.es-words`, a pair with only a quote showing `.es-quote`, numbered by place as the card numbers its
pairs, and the column's click sends a click on one through `toStatement(row, n)`. The current passage's
card, `#es-card`, waits in `#es-park` with `#en` and `#note-entry`: `placeCard`, from `markCurrent` and
`drawView`, moves it into the current row's `.turn-es` and `parkCard` back, the cell it left given
`statementsHtml` of its row as saved, before `drawTranscript` replaces the rows, as the notes field goes.
`pairHtml` numbers each pair with a `.pair-num` label beside its `.pair-body`, Remove a bin at the pair's
top right since 18 October, where it stood in `.pair-qhead` at the right of the Quote label, and `growField` grows a pair's empty field to its prompt, measured in a
twin of the field, `.hint-twin`, after it and taken out at once, so its words and its undo are never
touched. The card's foot, `.es-foot`, holds `#pair-add`, `#btn-ai` and `.es-next`, `#saved` and
`#btn-commit` kept together at its right, and is `position: sticky` 30 pixels above the column's foot,
over its faded edge, so Next stays in reach while a card of several pairs runs past it. `footStuck`
marks it `.stuck` while the card's foot lies below its own, on every scroll of `#transcript`, from
`placeCard`, and from a `ResizeObserver` on `#es-card` and on `#transcript` (18 October): then its
corners square, `box-shadow` draws a hairline under it, `::after` lays `--under-foot`, the row's own
paper (`--paper`, or `--paper-sunk` under the hover wash and the same-size band), 31 pixels down to the
column's foot, and `::before` fades the fields 44 pixels above it into `--card`. A row takes no
hover wash while the pointer is in `#es-card`, `#en` or `#note-entry` (`:has()`), and the current rule
takes `grid-row: 1 / 4`, the rows of the words, an open box and a quote being built, so it never runs
down the height a tall card gives the row. The playhead has no rule of its own since 28 October:
`.turn.listening .time` is the accent and bold, its `::before` a 6 by 7 pixel play triangle cut by
`clip-path`, the two kept on one line (`white-space: nowrap`), where on one of the interviewer's rows
with a note a timecode of seven or eight figures would part them: that line runs up to 10 pixels out
of the margin to the left instead. `.turn.listening` moves as before (`markTurn`). `#btn-prev`,
`#btn-quote`, `.actions`, `#commit-hint`, `.entry`, `#d-en`, `#dot-en`, `#notes-head` and the disclosure's
`DISCLOSE_KEY` having gone. `focusEntry` and `toStatement` focus with `preventScroll`, so the caret never
cuts the column's glide short. `openNote` puts `#note-entry` in the interviewer's row's `.turn-notes`,
made for it as `.note-cell`, and `bringIntoColumn` scrolls his passage whole into the column where it ran
past its head or foot, and `parkNote` takes it back, where `.entry.noting` hid the three fields.
`minimapYield` counts `#es-card` among what the minimap gives way to, and `selBarRoom` keeps the toolbar
inside the transcript's heading's span where a statement or a note stands beside the words. The guidance's
sheet is `340px` until `#work.guide-whole` gives it `--guide-w`, and `--desk` is gone from `tokens.css`.

**Quote first (21 October, Adam's ruling on his drawings, area 241).** `pairHtml` adds to each pair's
`.pair-body` a `.pair-qtoggle` in `.pair-qhead` beside the Quote label, a `.pair-kq-line` before `.pair-kq`
and, after it, `.pair-take`, the arrow, in the body's second column level with the quote. `pairTakeDraw`
lights every `.pair-take` (`.lit`, `aria-disabled`) while `selectionInTurn()` or `S.pending` holds words,
run from `pairsDrawn`, `paintTurn`, `clearPending` and the document's `selectionchange`. A click on one runs
`pairTake(pair)`: `S.pairFocus` set to that pair and then `commitQuote`, so `quoteTarget`, the undo, the
line at the foot and the save are `Q`'s own, and `#pairs` takes `mousedown` on it with `preventDefault` so
the selection stays. No API op is new: the arrow reaches the same quote as `Q`, saved by the same commit.
`levelPairs`, through `levelSoon` (one `requestAnimationFrame`), places the boxes: each `.pair` is a box of
its own since 21 October (`.es-card` lost its border, background and padding, and `.es-foot` closes the
last `.pair`), and for each pair whose quote has a mark in the current `.turn-text` (`[data-kq]`, its first
client rect) the box's top goes level with it, `--lift` on `#es-card` for the first and `--drop` on a later
`.pair`, never negative, so a box never rises over the one before it. It runs only where the `.turn-es`
cell stands beside the words, from `pairsDrawn` (a passage opened, a quote set by `Q`, the arrow, the
selection's Quote, an undo or redo, a pair added or removed), `placeCard`, `measureColumns` (a resize or the
columns' change), `quotesDraw` and `quoteOpen`, and never from `#pairs`' `input`, so typing never moves a box.
Quotes on the status bar is `es_quotes` in `config.json` (`server.py`: on unless the file holds `false`,
in `SETTINGS_BY_APP` for Idiograph and saved by `api_settings` with the other ticks). `quotesDraw`, from
`drawView`, sets `#work.quotes-folded` and `#es-quotes-btn`'s `aria-pressed`, and `quotesToggle` saves it
through `setView`. `pairsFoldDraw` marks a pair `.kq-filled` and writes its folded line, and a click on
`.pair-qtoggle` or `.pair-kq-line` runs `quoteOpen` on that pair alone. Since 21 October a pair's own state
goes against the bar's: `.kq-shut` folds one under Quotes on and `.kq-open` opens one under Quotes off,
`quoteShown` reading the two with `quotesFolded`, and the toggle shows on every `.kq-filled` pair, its
chevron by `aria-expanded`. `quotesDraw` clears both from every pair only when the bar's state differs from
`S.quotesWere`, so a press on Quotes resets every quote and any other `drawView` keeps them. The two
ways of hiding differ only in the stylesheet (Adam, later on 21 October): `.kq-shut` under Quotes on hides
`.pair-kq` and shows `.pair-kq-line`, while `#work.quotes-folded` hides `.pair-kq` and `.pair-take` of a
pair not `.kq-open` and never shows its `.pair-kq-line`, so Quotes off leaves only `.pair-qtoggle`. Area 243
reads what shows in each of the four states from the stylesheet's own cascade. The status
bar is `#es-status`, `position: fixed` at the window's foot, `--es-status-h` (31 pixels) taken off
`.reading`'s height, with `#rail-place`, moved there from the title bar with its ids, `#es-count`, written by
`esCountDraw` from `livePairs` over every row of `S.flat`, an interviewer's turn's statements counted as the board's
cards and the agents' `statements` count them (countdrift, 30 October 2026, where until then only the participant's
passages were), the passage being worked on as its fields hold it, an unsaved statement as it is typed, `#es-map-btn`, which calls `minimapToggle` and takes
`aria-pressed` in `minimapYield` beside the hidden `#minimap-btn`, `#es-quotes-btn` and `#btn-help`, moved
from the title bar with its id, so `window.js` still finds it. With the place gone, `drawMark` hides
`#es-sheet-sep` unless a mark or the round's counts follow it, and `#rail-round-sep` always. Below 480px
`.es-sword`, `#es-count`, `#rail-who` and the player's `.player-note` go.

**The card in reach beside a long passage (cardlarge, 30 October 2026).** zoomsweep's shot at Text size Large
in a 1280 by 800 window (1024 by 640 CSS pixels) found the card of a long passage below the window's foot: the
column was 370 pixels high, the passage's words 638, and `levelPairs` had lowered the card 473 pixels to its
quote, so neither its first statement nor Next showed until he scrolled. At 720 by 800 (576 CSS pixels, the
passages stacked) the card under the words stood below the foot for any long passage, `centreCurrent` keeping
the speaker line at the head. `CARD_REACH` in distil.js chooses one of three ways drawn for Adam, `'cap'` (A),
`'hold'` (B, in force) or `'scroll'` (C), and `''` leaves the screen as it was. `reachOf(row)` measures the current
passage: `under`, the card across the words rather than beside them, `need`, the card's top to the foot of its
first statement's box with the card's own foot added, the part that must show for the card to be in reach,
`room`, the column's height less `SPEAKER_CLEAR`, the 30 pixel fade at its foot, what stands above the words in
their row (the name and time where they lie along the top), the row's 9 pixels under them and, under the words,
`need` and the card's 12 pixels, never under two lines, and `long`, the words' `scrollHeight` past `room`. `reachDraw`, from `centreCurrent` before it measures and from `measureColumns`, takes `reach-long` and
`--reach-cap` off every row, measures, keeps the answer in `REACH` and marks the current row `reach-long`, and
sets `#work.reach-cap` or `#work.reach-hold` from the constant. A passage that fits, a card in the stacked
column (`#stack-es`) and a parked card are never marked, so nothing changes at 100% with a short passage. A:
the words take `max-height: var(--reach-cap)` and scroll inside themselves, `reachFade` marking them
`reach-above` and `reach-below` for a 30 pixel fade at an edge with more beyond it (a capture listener for
`scroll` on `#transcript`), and `levelPairs` lowers the first box no further than the words' box leaves its
statement and the card's foot whole (`REACH.need` above its foot). B: the card is `position: sticky` 30 pixels
inside the column's head and foot, `--reach-cap` high (the column less its two fades beside the words, about
half the column under them, never less than `need`), scrolling inside itself with `.es-foot` at `bottom: 0`, and
`footStuck` reads a held card's own scroll for `stuck`. Its lift goes on its cell, `--reach-lift`, a `::before`
of that height, so the card rises from there to the column's foot where its quote lies below it, and its later
boxes take no `--drop`. Under the words the cell itself is sticky at the column's foot, on `--under-foot`, a
30 pixel fade into that paper above it and a `box-shadow` of it down to the column's foot, so the words pass
behind it.
C: `centreCurrent` levels the boxes at once for a long passage (`levelPairs`), then after the speaker line's cap scrolls on until the card's top plus `need` stands 38 pixels above the column's
foot, the speaker line going above the head, so the card's first statement and Next show as the passage opens,
its quote beside it. The columns settle just after a passage opens (measured: 68 pixels lower at 1280, 76 at
720), so for 1.5 seconds after a centring (`REACH.settle`), never in a glide (`REACH.glide`), `levelSoon`'s
frame ends with `reachInView`, which takes the column down after the card. In all three `centreCurrent` levels a long
passage's boxes before it measures, and `drawTurn` centres a long passage once more when the serif has loaded
(`document.fonts.ready`) on a column drawn anew. Nothing moves while he types: `reachDraw` runs on centring and
on a resize, never on input.

**The columns shown, hidden or stacked (18 October).** Adam's drawing of four layouts and one menu.
`columns_hidden`, `columns_stacked` and `stack_split` stand in `config.json` beside `statements_columns`,
cleaned by `columns_hidden` and `stack_split` in `server.py` (`HIDEABLE_COLUMNS`, `STACK_SPLIT`,
`STACK_RANGE`) in `merge_config` and `api_settings`, and read by `columnsLayout(cfg)` in `app.js`, which
answers the order, the columns hidden (`columnsHiddenOf`), the choice of Stacked, `stacked` where it holds,
which is only while both columns are shown, and the divider's place (`stackSplitOf`). `drawColumns(lay)`
keeps it as `S.layout`, sets `colsVars(order, hidden)`, where a hidden column takes no track and stands at
place 1 out of sight and `--stk-cols` gives the stacked column's track, `--st-track`, `minmax(280px,
2fr)` (3.4fr until 6 November, 2 to the transcript's 3 as `--cols2` has them), and the transcript's in the statements' place, and toggles `#work.hide-es`, `#work.hide-en`,
`#work.cols-alone` and `#work.cols-stacked`. A hidden column's cells and heading take `display: none`, an
interviewer's `.note-cell` going under his words, and the transcript alone takes `--tx-track` of
`minmax(300px, 820px)` with its grids centred and its grip gone. `cardCell` and `notesCell` say where the
card and `#en` stand: the current row's cells, `#stack-es` and `#stack-en-cell` while `stackedNow()`,
which is Stacked above 800 pixels (`colsNarrow`), or none, the park, while their column is hidden, so the
words stay loaded and `Cmd + Enter` saves as ever. `cellsAgain`, from `drawView` and a `matchMedia` change
across 800 pixels, draws every other row's cells again from what is saved, since a row the card left while
it stood in the stack or the park kept its old words. `#cols-body` wraps `.transcript-wrap` and `#stack`, a
flex row as before and, under `#work.cols-stacked` above 800 pixels, a grid of `--stk-cols`, `#stack` a
grid of three rows, `#stack-es`, `#stack-divider` and `#stack-en`, the halves `--stack-a` and `--stack-b`
in thousandths that `drawStack(split)` sets, each half scrolling, `.transcript` taking `--cols` of one
track and `--tx-col` 1 for its rows. In the stack the card's foot keeps to the half's foot (`bottom: 0`),
`footStuck` reading `.stack-es` as a row's cell and running on its scroll, and `growNotes` leaves `#en` to
fill its half. The divider is `role="separator"` with `aria-valuenow`: `stackDividerDown` follows a drag
and keeps it on the let go, `stackDividerKeys` moves it `STACK_STEP` on the up and down arrows and to
either end on Home and End, a double click puts it at `STACK_SPLIT`, and `stackSplitKeep` sends
`stack_split` through `setView`. Columns' menu is `#cols-show-statements` and `#cols-show-notes`, sent as
`columns_hidden` through `colsTicked`, `#cols-side` and `#cols-stacked`, sent as `columns_stacked`,
offered or faint (`.row-off`) by `colsStackRows`, and `#cols-book`, `colsBookOrder`, offered off the
book's order. `drawColsMenu` sets them from `S.layout`, `colsMenuPlace` places the menu as it opens and
after each change, a press from the keyboard (`e.detail === 0`) puts the focus on the first tick, and
`colsMenuKeys` keeps `Tab` inside it, one stop for the two choices. Settings' View holds the same ticks
and choices, `#set-show-statements`, `#set-show-notes`, `#set-side` and `#set-stacked`, filled by
`fillColumnsSet(lay)`, Stacked offered as the ticks change (`colsSetTicked`), and `viewChoice` sends
`columns_hidden` and `columns_stacked` once they have moved. The pair's Remove is a bin since the same day
(see A pair's heading and its Remove), last in the pair, so `Tab` in the card runs statement, quote,
bin, and every field the custom order holds is passed over while it is out of sight. `focusEntry` puts the
caret in the notes while the statements are hidden. Area 186 holds them.

**The column edges (20 October).** Adam's way C, from a tester's letterbox at 2560. `#col-edges` in `.reading`,
which is `position: relative` for it, holds one `.col-edge` per edge, the columns shown plus one, each
`role="separator"`, a slot placed by `edgesDraw` over the gap between two headings or just outside
the first and the last. `edgePlace` says whether an edge lies between two columns, `.between`, and `--edge-mid`, the
middle of the columns' visible height from the edge's top. A `.between` edge is 12 pixels wide on the gap's middle
(`margin-left: -2px`), its `::before` a faint rule (`--rule-firm`) always shown and its `::after` the pill handle, 12 by
48 pixels at `--edge-mid`, two upright bars on a chip. The edges lie over the columns, so the pill stays in view as they
scroll. Hovered, in a drag and with the focus the rule is `--ink-faint` and 2 pixels and the pill fills in `--ink-faint`
with its bars in `--card`. The two outer edges, the margins, stay 8 pixels with the `::before` line on hover only (the handle,
6 November, Adam's option C). The
model is `{ left, right, widths }`: `edgesNatural` measures the screen as it opens with `#work.cols-sized`
and the track variables taken off for a moment, giving the outer distances, `inL` and `inR`, what lies
between the reading area's padding and the columns, the order of the columns shown and the side columns'
widths, `edgeKey` naming the statements' column `stack` while `stackedNow()`. `edgesModel` lays what
`widthsHeld()` holds for `colsScreen()` over it, `edgeShifted` moves one edge, a side column either side
taking the room and the transcript, always the `1fr`, the rest, `edgeMove` as far as `edgesFit` allows by
bisection (`EDGE_MINS`, the reading padding at least 8), `edgeHome` puts one edge back for the double
click, `edgesSqueezed` fits a model to a narrower window, margins first, and `edgesKept` answers what to
keep or null when every edge stands where it opens. `edgesApply` sets `#work.cols-sized`, `--read-l` and
`--read-r` for the reading area's padding, `--es-track`, `--en-track` and `--st-track` in pixels and
`--tx-track` of `minmax(300px, 1fr)`, the stylesheet then taking off the reading area's `max-width` and the
transcript's words' measure above 800 pixels. `measureColumns` runs `edgesDraw` first, which hides the
edges at 800 pixels and below and with the transcript alone (`edgesOffered`). `edgeDown`, `edgeBack` and
`edgeKeys` on `#col-edges` drag, double click and step by `EDGE_STEP`, and `widthsSave` sends one screen
through `/api/settings`. `#cols-widths` under Widths in Columns' menu and `#set-widths-reset` under Column
widths in Settings call `widthsReset`, `drawWidthsReset` keeping both faint while nothing is held.

**Stacks by dragging a heading (21 October, panels).** From Adam's backlog. `stack_top` stands beside
`columns_stacked` (`stack_top` in `server.py`, `HIDEABLE_COLUMNS`), read by `columnsLayout` as `top`, and
`drawColumns` toggles `#work.stack-notes-top` while the notes stand above: the notes' heading then stands
over the stacked column in the statements' place, `#stack` takes four rows, `#stack-en`, the divider,
`.stack-es-head` and `#stack-es`, and `--stack-a` is the upper half's share whichever it is. Each half
scrolls on its own, and `stackFade` (from `footStuck`, the halves' scrolls and a `ResizeObserver` on
`#stack-en`) marks it `more-above` and `more-below`, a mask fading 44 pixels at its top and 48 at its
foot, the foot's fade ending just over a `stuck` card foot (`--fade-foot`, the foot's height from the half's
foot) so Next stays whole (panels2). Each half's
heading is a `.stack-head` with its grip, which `boot` puts before its name with `gripHtml`, the lower
one's alone showing. `colGripDown`, on `#cols-head` and `#stack`, takes a press that moves under 4 pixels
as a click and otherwise asks `colsDropAt` for the drop under the pointer: a half of the column it would
stack with (`colsStackZone`, the other column's heading's span inset by `STACK_INSET`, from the headings'
top to the columns' foot, or with the two stacked `#stack`, the lower heading offered the upper half and
the upper one the lower), else the nearest gap as before. `colsMark` draws a gap's bar or `#stack-drop`, a
box in the ink round the whole column, its `.stack-drop-half` (`data-half`) in `--tick-wash`, the faint tint
of the ink, the box 16 pixels outside the column and the line where the two would meet (its `::before`)
spanning only the column's own width. That line, and the half the pointer picks, follow
`colsSplit(zone)` (panels2): every block holding words in the column's span (`SPLIT_BLOCKS`: headings,
pairs, the card's foot, other passages' statements and notes, the notes field) merged where they touch,
and the middle of the gap between two nearest the column's middle, at least 40 pixels from its ends, else
the middle. `colsDropped(lay, name, drop)`
answers the settings the drop changes, sent through `setViews`, which sets several view keys and sends
them in one `/api/settings`, or `setView` for an order alone. Stacked, the order is two units
(`stackUnits`, the stack in the statements' place), so the upper heading and the transcript's move units
and `stackExpand` writes the three back, Alt and an arrow too (`colGripKeys`). The heading's menu,
`#col-menu`, opens from a grip's click or Enter or Space (`colGripClick`, the focus on its entry from the
keyboard) and a right-click on a heading (`colHeadContext`), its entry from `colMenuItems` and its act
from `colMenuChange`, Esc closing it to the grip. `widthsReset` also sends `stackResetChange(cfg)`,
setting Settings' radios and `S.viewOpened` so its Save never stacks them again, and `drawWidthsReset`
offers Reset while a stack stands. `colsBookOrder` puts the statements back above, `stackedWords` says
Stacked's row either way up in the menu and in Settings, and `columnsShownSaid` says "notes over
statements". `edgeKey` names the upper column's heading `stack`. Area 236 holds them.

**A new window, and two in step (20 October).** `openInWindow(spot)` opens `/#open=` and the spot, as
`spotNow` makes one, `work`, `pets` or `gets`, in a browser through `window.open` with `popup` and a size.
In the Mac and Windows app it calls `__idiographOpenWindow(spot, hash)`, which `packaging/tauri/window.js`
gives the page, and that asks the app's own `new_window` command with `place` (the return spot) and `hash`
(the same `#open=` address), as File, New Window does since printwin, since a window that `window.open`
makes shares its opener's handler and closing it could close the window behind it. The page never names
the bridge (area 164). It needs printwin's `new_window(place, hash)` landed. The hash
never reaches the server. `spotFromAddress` at `boot` reads it once (`spotOpened`), takes it off the address and keeps it as
the return spot, so `spotTaken` and `comeBack` open it as they open a restart's. Open in a new window is `data-window` on each row of the
participant switcher (`thCaseWindow`) and `data-vop="window"` in the board menu (`thWindow`, the canvas
saved first). Two windows in step reuse `/api/stamp` and `workbook.WRITTEN`: `esStampTick`, every
`ES_STEP_EVERY`, hands the stamp's `workbook` to `esStepTake`, which keeps the time it last saw for the
case, passes a change from outside the app to the notice as before, and for one of this app's reads
`/api/open` again once no field holds words unsaved, comparing each row's `v`, its runs, name and time,
calling `startCase` in place on the current passage with the column's `scrollTop` kept, and washing each
statement that changed, alone, and a passage's notes only when they changed (`esStepWash`, `.came-in`). `thStampTick` keeps `TH.wbAt` and calls `thOwnLoad` when the
workbook moved and this app wrote it, so a statement reworded on Experiential statements or another board
comes onto the PETs board. Area 220 holds the widths, Reset, the double click and the stamp.

**The minimap (16 October).** `minimap` in `config.json`, `auto`, `on` or `off` since 17 October,
later, where it was a tick, read by `minimapMode` from the same config as the view, `auto` when absent,
an old true reading as `auto` and an old false as `off`, as the server's `minimap_mode` reads it in
`merge_config` and on a save, `MINIMAP_MODES` its three. `drawView` sets `#work.minimap-on` for Auto
and On and `#work.minimap-always` for On, `drawViewMenu` checks `#view-minimap-auto`, `-on` or `-off`
under `.view-head`, `openSettings` checks `#set-minimap-auto`, `-on` or `-off` under its own small
heading, `viewChoice` carries the checked one so Save sends it only once it has moved, and the menu's
change handler sends it through `minimapChoose(mode)`, which drops any opening or hiding of his and
wakes the card for Auto. It is a card, `#minimap` in `.transcript-wrap`, absolutely placed 14 pixels
from the column's right edge, clear of its scrollbar, and 6 from the wrapper's foot whether or not the
way back shows, `.back-to-turn`'s own 6, so the two share one bottom edge (17 October, later, where the
card stood at 10), where until 17 October it was a strip 22 pixels wide down the column's right padding
that hid the column's scrollbar. It holds `#minimap-card`, on `--card` with a `--rule-firm` edge,
`--r-card` corners and `--rest`, which holds `#minimap-area`, `aria-hidden`, 125 by 290 pixels, with
`#minimap-map` in it, the column's box, `MINIMAP_ROOM`, 62 by 280, at `MINIMAP_AT`, 17 and 5, and
`#minimap-views`, the box's layer, 3 pixels wider at each side with `overflow: hidden` since 18 October,
where it was the column's box, so the box's dimming below stays on the column clear of the track and the
time, so the card is one size, 135 by 300, whatever the interview's length, then
`#minimap-btn` outside the card, 32 pixels square on the same paper, edge, corners and lift, 4 pixels to
its right on its bottom edge, `aria-pressed` while the map shows, where until 17 October, later, it stood
inside the card beside the last label, and `#minimap-tip`. Since 17 October, later, Adam's drawing of that evening,
`minimapLayout(col)` reads the column as laid out, every `.turn`'s top and height from
`getBoundingClientRect` in the column's scroll coordinates, its `data-i`, hers or `.aside`, its
`data-done`, its words through `minimapWords` from `S.flat`'s `text` and its `seconds`, with
`scrollHeight` as its height. `minimapPlan(layout, room)` gives each of her passages its words' share
of the room's height less a gap between two blocks and before or after an interviewer's turn at either
end, and while the smallest block would come out under the least, joins it with the smaller of its
neighbours and works the scale out again. `minimapGrain(rows)` gives the least and the gap,
`MINIMAP_LEAST`, 4.5 pixels, and `MINIMAP_GAP`, 2.1, up to an hour, both growing evenly finer to
`MINIMAP_FINE`'s 2.5 and 1.6 at three hours, by the last timecode or, with none, the words at 150 a
minute, so three hours draws about half as many blocks again as an hour, where until 18 October it drew
31 against an hour's 30 and looked like an hour (Adam's drawing of 17 October). It gives each
row its span in the map, an interviewer's turn a point at its mark, `MINIMAP_MARK` into the gap, or
where two passages joined meet, the blocks, the marks where an interviewer's turn falls between two
blocks, the done track's runs, each from a passage with `data-done` to the last after it with only the
interviewer's between, and `minimapTimes(rows, spans)`, a dash at each five, fifteen or thirty
minutes by the last timecode, under 1800 seconds, up to 5400 and beyond, with short dashes at the
fifteens between thirties, each placed between the timecodes either side, its label `MM:00` in
minutes however long, left off where it would stand within `MINIMAP_APART`, 11 pixels, of the one
above. `minimapAnchors(layout, plan)` ties each row's top and foot in the column to its span in the
map, and `minimapToMap(plan, y)` and `minimapToCol(plan, m)` read a place in one as a place in the
other. `minimapHtml(plan)` writes `.mm-track`, `.mm-done`, `.mm-block`, `.mm-ask`, `.mm-dash`, with
`.short`, and `.mm-time` as `<i>` and `<span>` elements with their top and height inline, and nothing
else, no quote, no round and no current passage since 17 October, later. `drawMinimap` reads
nothing while the card is not wanted, fills `#minimap-map` and keeps the plan in `S.mm` with its
anchors, and `scheduleMinimap` runs it once a frame from `drawView`, `markCurrent`, `drawDoneMarks`,
`paintTurn` and `repaintRow`, and from a `ResizeObserver` on `#transcript`, `#transcript-rows` and
`#minimap`, which catches a font settling, a notes field growing, the way back's strip and the
window. `drawMinimapView` writes one `.minimap-view` into `#minimap-views` from `minimapView(plan, top,
tall)` with the column's `scrollTop` and `clientHeight`, on every `scroll`, so the box follows a glide,
never under `MINIMAP_BOX`, 12 pixels since 18 October, where at 6 it was a faint sliver at an hour and
three hours, a short one centred on its place. The box's look is its `box-shadow`, a line and a ground
as custom properties on `.minimap-views`, as Adam chose it on 18 October from four looks drawn for him,
A's line with D's dimming: `--mm-line`, a solid `--ink` line 2 pixels as an inset shadow, and
`--mm-ground`, a 600 pixel spread of `--dim` round the box, the card's paper at 35% in light and 25% in
dark, that the layer's `overflow` keeps on the column, so the view stays clear and the rest is dimmed.
Since 17 October, later, the box was an 18% wash of `--ink` with no edge. Under the pointer
`background-color` takes an 8% wash of `--ink` in the clear view.
`minimapWanted` is the card in
the corner before it gives way: never with `#work.minimap-on` off or `S.mmHush`, set by a hiding of
his, always with `#work.minimap-peek`, an opening of his, never else at and below `MINIMAP_NARROW`, the
stack's 1100, and from 1101 pixels with `#work.minimap-always` or `S.mmAwake`. `minimapShown` is that and not
given way. `minimapWake`, from `minimapScrolled`, a second `scroll` listener on `#transcript`, and from
`drawMinimap` whenever the current passage is another than `S.mmAt`, sets `S.mmAwake` in Auto, and
`minimapRest` lets it sleep `MINIMAP_AWAKE`, 2000 milliseconds, after the last, never while `S.mmOver`
or `S.mmDrag`, starting again from `minimapLeave` and `minimapUp`. `minimapToggle`, from the button's
click and `M` in the keydown, does nothing with Off and otherwise sets `minimap-peek` and `S.mmHeld` to
show or `S.mmHush` to hide, and a new current passage in `drawMinimap` clears all three. `minimapYield`
gives the card `.yield` where `minimapOver(box, rects)` finds the card's box over the current
`.turn`'s `.turn-text`, `.turn-edit`, `.quote-preview`, `.notes-head` or `#en`, or a field in focus in
`#transcript`, while it is wanted, and `.gone`, the card and its button at `opacity: 0` and
`visibility: hidden`, where the button's box is over one of them at every width, where until 17 October,
later, the button stayed at `MINIMAP_NARROW` and below, never with `minimap-peek`, never while `S.mmDrag` or `S.mmOver`, set by the card's
`pointerenter` and cleared by `minimapLeave` on its `pointerleave`. An opening of his sets `S.mmHeld`,
which keeps `minimap-peek` over what stands in the corner then. `minimapYield` clears it once the card
stands clear, `minimapLeave` once the pointer leaves the card, and `minimapScrolled` on a scroll while
the pointer is off the card and no press is under way, and with it cleared anything over the card, or
at once a field in focus in the column under it, drops `minimap-peek`, the card then giving way as it
does at any time above `MINIMAP_NARROW` and closing to its button at and below it (17 October, later,
where `minimap-peek` held for the whole passage and at 1024 wide covered the notes field). It sets
`.shut` while the map does not show, `#minimap-card` faded to `opacity: 0` and `visibility: hidden` and
`#minimap` taking no pointer but its button's, so the button never moves, `.off` with Off, the button's
`aria-pressed`, and `--mm-room` on the wrapper, the card and the button's width or the button's alone,
`MINIMAP_CLEAR`'s 14 and an 8 pixel gap, which
`.transcript-wrap .back-to-turn` takes as its `right`, so Back to where I was stands to the card's left,
where until 17 October, later, `.transcript-wrap.away .minimap` raised the card 44 pixels. Where the
wrapper's width leaves Back to where I was less than `MINIMAP_CLEAR.back`, 200 pixels (180 until the button said Back to where I
was on 18 October, 18 pixels wider), beside the card, as
at 360 with the card open, `--mm-room` is `MINIMAP_CLEAR.right` alone and, while the way back shows, the
wrapper takes `.mm-lift`: `.transcript-wrap.away.mm-lift .transcript` takes a mask clear for its
first 44 pixels and fading in over the next 30, in `--ink` for its opaque part, and
`.transcript-wrap.mm-lift .back-to-turn` stands 6 pixels from the top over that strip, so Back to
where I was never cuts through a line and the words never move, where it stood squeezed to two lines and
then over a line above the card (17 October, later). While an opening of his shows, `minimapBand()`
reads the passages level with the card from `S.mm`'s rows, their `.turn-text`, `.turn-edit` and
`.quote-preview`, and where the card stands over one, and no field in focus in the column reaches lower
than 36 pixels above the card, sets `--mm-band` on the wrapper, the column's foot to 12 pixels above
the card, and `.mm-band`, so `.transcript-wrap.mm-band .transcript` takes a mask
fading the words out over 24 pixels to that height and clear below it, and
`.transcript-wrap.away.mm-lift.mm-band .transcript` the same with the strip at its head, so the card's
edges never cut a line, as at 360 (18 October). At 1100px and below, while the button stands alone,
not `gone` and the map not shown, `minimapButtonBand()` sets the same band where a passage's words stand
under the button, found by `document.elementsFromPoint` at nine points across it since no `S.mm` is
drawn there, and none while a field in focus reaches into the band (polish 10). While the card is `shut`
and fading, `drawMinimapView()` leaves `#minimap-views` as it was, so the box fades with the map rather
than going first. `#work.minimap-on .transcript-rows` keeps 322 pixels under the last
passage, the card's height, its offset and 16 clear. `minimapPoint(plan, e)` turns a pointer into a
place across and down the map, and `minimapRowAt(plan, x, m)` into the passage there, its span or the
nearest within 2 pixels. `minimapDown` on `pointerdown` takes the pointer, keeps the press in
`S.mmDrag` and, off the box, glides the column through `minimapTo(top, smooth)` so the place pressed
comes to its middle, `minimapMove` scrolls at once once the pointer has moved 4 pixels, or from the
first move on the box, and otherwise shows the tip through `minimapHover` and `minimapTip`, the
passage's `name` and `time` as `turnHtml` writes them, and `minimapUp` ends it on `pointerup`,
`pointercancel` and `lostpointercapture`, the tip going on `pointerleave`. `minimapWheel` on the
card's `wheel`, not passive, scrolls the column by the wheel's lines or pages and leaves a pinch to
the browser. A `mousedown` on the card is cancelled, so the caret stays in the fields, and nothing
calls `goTo`. The style is tokens alone, each block and the green 3 to 1 or more on `--card`
in both themes: the blocks `--ink-faint` at 80% through `color-mix`, the interviewer's mark `--rule-firm` at 40%
of the column's width, the track's outline `--rule-firm`, the done runs `--good` whole, a skipped
passage's too, where until 17 October, later, they were at 75%, the box 18% of `--ink` with no edge and
24% under the pointer, where it was a tenth with an `--ink-soft` edge that read as a frame, the time's dashes and its 9 pixel labels in `--mono`
`--ink-faint`, the button `--ink-soft` hidden and `--ink` shown, and the tip `.th-tip`'s chip. Until 17
October, later, the card held short columns side by side, one a round or ten minutes of talk, with the
quotes' marks in `--crux`, round rules and the current passage's edge and notch, and until 17
October below 1100 pixels `.reading`'s right padding was `calc(23px + var(--gutter))`, the strip's
room and a gutter, where it is 28 pixels at both sides now.

**The board's minimap (18 October).** Adam's yes of 17 October, item 3 of the minimap's research,
Miro's and tldraw's way. `#th-map`, a `.th-ui` in `#th-stage` after `#th-tip` and before
`#th-viewing`, so the bin, the pile and the export's line stand over it, holds `#th-map-area`, its
`#th-map-items` and `#th-map-view`, and is `aria-hidden`. Its button, `#th-map-btn`, ends the zoom bar
after Fit all and a `.th-map-sep`, the transcript button's map icon, "Minimap (M)" in its tooltip,
`aria-pressed` saying whether the map shows, and pressed it takes `.th-mode.on`'s sunk paper, firm edge and
ink, where until 18 October it took the ink alone. `.th-map` stands `var(--gutter)` from the canvas's right
and `var(--th-zoom-up)` over its foot, 8 pixels over the zoom bar, which `thCorners` measures, and over
the bar's own place at `.th-tighter`, `var(--th-map-w)` wide, which `thMapPlace` sets from the bar's
`offsetWidth` on the canvas, from `themesOpen` after `thCorners`, a second `ResizeObserver` on
`#th-stage` and `thMapChosen`, and 160 pixels high, `TH_MAP.height`, on `--card` with a `--rule-firm`
edge, `--r-card` and `--rest`, as `.minimap-card` stands. `TH_MAP` holds the card's height, `pad`, 6
pixels round the board inside the area, `least`, 2
pixels, a mark's least side, `box`, 6, the view box's least side, `glide`, 240 milliseconds, and
`narrow`, 767. `thMapItems(v, layout, size, look)` lists the frames from the layout, `tm-frame` with
`thTintClass`, the sticky notes, `tm-sticky sticky-<paper>`, and every card on the canvas, a discarded
one left out, `tm-card` with `in hue-<n>`, the tint `thTints` gives the group that holds it, so a card
in a sub-theme takes its PET's own at `--hue-base`, or on GETs `tm-case case-<n>` from `look`, which
`thMapDraw` gives as `gtLook(c.case).colour`, and `missing` on a card no longer in its workbook.
`thMapFit(boxes, w, h)` fits their `thUnion` into the area, `pad` clear and centred, a small board as large
as a big one across the area's width or height, whichever it meets first (until 18 October `k` was no more
than `most`, 0.2), or null with nothing to draw, and `thMapToMap` and `thMapToBoard` read a place in one as a place
in the other. `thMapHtml(items, fit)` writes one `<i>` for each, frames first. `thMapSeen(view, w, h)` is
the part of the board in view, and `thMapBox(fit, seen)` its box on the map, `box` or more a side and
centred on its place, its whole size where it reaches past the map, which `.th-map-area`'s `overflow: hidden`
cuts at the edge (until 18 October it was held inside the map and shrank there), or null where it lies wholly
off it. `thMapAround(board, boxes, seen)` is the fit the map is drawn at: the board's own, `TH.mapBoard`,
or where the view's box on it would reach past every side of the area, as after Fit all, `thMapFit` of the
marks and `seen` together, so the box stands whole inside the area with its line on all four sides and the
board inside it as the canvas shows it (18 October, where the whole area was washed with no edge), and
`thMapSame(a, b)` says whether two fits put the marks in the same places. `thMapWanted` is false
before `TH.live`, while `#themes` is hidden, with Off and at `narrow` and below, and otherwise
`TH.mapHand`'s `show` or `hide` while set, else On or `TH.mapAwake`. `thMapMode` is `minimapMode(TH.config)`,
the transcript's own setting, so one choice rules both. `thMapSchedule` runs `thMapDraw` once a frame:
`thMapChosen` sees a new setting against `TH.mapMode`, clears `TH.mapHand`, wakes a new Auto and sets
`.th-map-off` on the canvas, which takes away the map, its separator and its button, running `thCorners`
and `thMapPlace` again when that changes, then the marks are listed again into `TH.mapItems` and the
board fitted again into `TH.mapBoard` while `TH.mapStale` or the area's size changed, `.shut` set while
the map does not show, gives way or has nothing to draw, and `thMapViewDraw` takes `thMapAround`'s fit
into `TH.map`, writes the marks again only where it differs from `TH.mapDrawn`, the fit they were last
written at, so a pan alone leaves them and a view holding the whole map carries them with it, and sets
`#th-map-view` from `TH.view` and the canvas's size and keeps it in `TH.mapBox`. While `TH.mapDrag` lasts
it keeps `TH.map` as it was, so the place under the pointer stays under it, and `thMapUp` asks for a frame
so the fit comes back. While `TH.drag` lasts (18 October, the Mac window's judder) `thMapDraw` reads no
layout: it keeps `TH.mapBoard` and `TH.mapDrawn` as the drag found them and `thMapPatch(items)` sets the
`style` of only the marks in `TH.mapMarks` whose place or size changed, each mark's id, classes, style and
element as `thMapViewDraw` last wrote them, falling back to a whole draw when a mark came, went or changed
its tint. `thMapViewDraw` skips the canvas's size while `TH.mapViewAt`, the view it last drew for, is the
same, and `thMapCovered` reads no box while no sidebar is open. A drag itself takes one step a frame:
`thPointerMove` hands the move to `thDragQueue`, which keeps the latest in `drag.next` and asks for a frame,
and `thDragStep` runs it through `thDragMove`, first on `thPointerUp` and `thDragAlt` too. What is dragged
leans with no rotate transition, `.dragging`, and eases only as it stands up, `.standing` from `thStand`,
and what comes along with a label trails it by `thTrail` and `thTrailTick`, eased each frame, where both
were transitions WebKit began again on every move. A row dragged from a sidebar (21 October) moves the
same way: `thSPullMove` and `gtPullMove` hand its cards, `.th-card` with `.ts-ghost` or `.gt-ghost`, to
`thPullLift`, which lays them by `thPullSpot` in `.th-pull`, a fixed layer that `thPullFollow` moves to the
pointer at the canvas's zoom, adds `.dragging` two frames on so they lift, and leans them by `thLean(e, pull)`,
which with `pull.els` set tilts those cards in place of `drag.moving`. `thSideDrop` and `gtPullDrop` put each
card at the same `thPullSpot`, so it lands where it showed, and pass `lifted` and the pull's `lean` to
`thDone`, which eases it down as a canvas drop does. `thPullGone` takes the layer away. A drop merges on a title strip, and since 31 October in a body at the level it keeps (design A, below): `thTargetAt`
answers the bin or a label, `thMergeInto` says whether a drop there merges, `thMergeShow` lays
`#th-merge` over that strip, `thWayHome` is the theme what is dragged stands in otherwise, and
`thInsertAt` and `thInsertShow` put `#th-insert` where it comes in that theme's order, read from
`drag.layout`, the board as the drop would leave it, and since 26 October only when `thInsertMoves` says the
drop changes that order or brings something in, the order as the drag began read from `thAtStart`, the board
at `drag.from`. A theme dragged in its own place rests a margin from its neighbours (26 October, Adam: the last
sub-PET of a PET would not go closer to the ones above it, each that came inside its margin being sent up out
of its way by `thMakeWay`, and by `thSettle` at the drop): `thNearRest`, run by `thWay` and `thDragEnd` before
`thPreview`, takes the pointer's own move, `drag.free`, set by `thDragMove`, weighs the dragged top items
against their neighbours in `home` where they stood as the drag began, and when the shortest shift that
clears them all (`thFreeOffset`) is `TH_NEAR`, three margins, or less, adds it to `drag.dx` and `drag.dy`, so
what is dragged is drawn, eased and dropped a margin from them and nothing makes way. Statements and notes
alone, Alt held, a drop into another theme and a drop on a strip have no shift. Area 262 checks it. Statements alone also move into a body (19 October):
`thDragStart` sets `drag.cards` when all that moves is statements and keeps `drag.frames`, `thFrames` of the
layout as the drag began, and `thTargetAt` answers `{ group, frame: true, body: true }` for the innermost of
them holding the pointer (`thInnermost`), never with Alt held, and from `TH.layout` for a row pulled in from
the Cases panel. `thWay` sets `drag.out` when that body is not the statements' own, and `thPreview` and
`thPlace` then show them leaving as Alt does, `thInsertAt` reading them among that theme's members, and
`thDragEnd` hands the theme to `thDrop` as `frame`, which joins it.
Design A (dragA, 31 October, Adam's dialog after the drag audit, `.verify/wip-31Oct26/dragaudit/audit.md`): no
PET or sub-PET moves out of the way while a drag lasts. `thDragStart` keeps `drag.frames` from
`thBodiesFor(v, moving, layout)`: every frame for statements and notes, for a sub-PET or a group the frames one
level above its own (the higher of several dragged), and none for a PET, so a body hit keeps the level.
`thTargetAt` gives nothing on the canvas with Alt held, no title, body or card's middle (Alt joins nothing), and
the hot spot it kept from `drag.was` is gone (`drag.was` stays for `thDone`'s frames that grew). `thPreview`
hands `thMakeWay` a place only when `drag.hitNow` is a body and its group the drop's `home`, so only the PET or
sub-PET whose body is under the pointer makes room, nothing over a title, and `from.groups` as `pins`. With `pins` `thMakeWay` works in
that one place, never on the canvas (`home` ''), and moves only its statements and notes, its sub-PETs' frames
and its own title, short of the `TH_GAP` under it, held still as places they are sent clear of without ever
pushing. `thDragLayout(v, size, moving, alt, from)` hands `thLayout` the same `pins`, every label not dragged
held where it stood while its frame runs round what it holds, so no title runs from the pointer and the frame
of a PET a member is dragged out of stretches after it and pushes nothing (`thPlace` passes
`drag.from.groups`). `thHover` outlines a body under the pointer as it does a strip when the drop would bring
what is dragged into it, `thInsertAt` reads a sub-PET or a group coming in by its frame, so the line shows for
them too, and `thDragEnd` sets `drag.hitNow` before its own `thPreview`. The drop's `thDone` with `stay` settles
the rest by `thSettle`, weighed in the file through `thInFile` when the quotes' or a stack's room is in the view
(`thRoomTrack`, `thRoomBy`). `thMakeWay` without `pins` is as it was, for `thReviseTake`. The same code serves
the PETs, GETs, LGETs and LPETs boards. No file format change and no new op: `board apply`'s `move` already moves
a statement or a label into any label. Areas 312, 64, 71, 188 and 262.
While the map is not wanted nothing is read. `thMapCovered` gives it way while `#th-side` or `#th-cpanel`, open,
stands over it, as both do below 900 pixels, stopping above the bin and the zoom bar, and `thMapShown` is
`thMapWanted` and not given way, which `thMapDraw` and `thMapToggle` read. A `MutationObserver` on each
panel's `hidden` asks for a frame as it opens or closes. `thView` ends with `thMapViewed`, which wakes the map in
Auto through `thMapWake` and asks for a frame, and `thPlace` with `thMapMoved`, which sets
`TH.mapStale`, so a drag draws the board as `drag.seen` shows it once a frame. Each does nothing on a
page without `#th-map`. `thMapRest` lets it sleep `MINIMAP_AWAKE` after the last, never while
`TH.mapOver`, set on the card's `pointerenter`, or `TH.mapDrag`, starting again from `thMapLeave` and
`thMapUp`. `thMapToggle`, from the button's click and `M` in `thKeyDown`, does nothing before a board,
with Off or at `narrow`, and otherwise hides a map that shows, `hide` with On and asleep in Auto, or
shows one that does not, `show` in Auto and cleared with On, and `themesOpen` clears `TH.mapHand`,
`TH.mapAwake` and `TH.mapMode`. `thMapDown` on the area's `pointerdown` takes the pointer and keeps the
press in `TH.mapDrag`: on the box its grab, the place pressed against the view's top left on the board,
and off it the view's middle, with `thMapGlide(x, y)` bringing the place pressed to the canvas's middle
over `glide` with a cubic ease, at once under reduced motion, any other move of `TH.view` on the way
ending it. `thMapMove` pans at once from the first move on the box, or once the pointer has moved 4
pixels, and `thMapUp` ends it on `pointerup`, `pointercancel` and `lostpointercapture`. The wheel over
the map reaches `thWheel` on the canvas, which zooms about the pointer, and `thPointerDown` and
`thContextMenu` leave a `.th-ui` alone, the card's own `contextmenu` cancelled. The style is tokens
alone: the card `.tm-card` `--ink-faint` at 80% through `color-mix`, `.tm-card.in` `--hue-base`,
`.tm-case` `--case`, `.missing` at .45, `.tm-frame` a 1 pixel `--hue` outline, `.tm-sticky` its
`--sticky` inside a 1 pixel inset of `--ink-faint` at 70%, and `.th-map-view` as the transcript's
`.minimap-view` since 18 October, an inset `box-shadow` of 2 pixels of `--ink` and a 600 pixel spread
of `--dim` that the area's overflow keeps on the map, with 8% of `--ink` under the pointer, where it was
14% of `--ink` with an edge of 35%, 19% under the pointer, its tints at 3 to 1 or more on `--card` in both themes. At 767 pixels
and below `.th-map`, `.th-map-sep` and `.th-map-btn` take `display: none`.

**The guidance as a sheet (16 October).** Adam's decision on a tester's feedback, who asked for the
exploratory notes in a column beside the transcript, the IPA book's layout: at 1280 the rail's
300px kept `.transcript` under the 640 pixels the notes need beside the words. `.stage` is two
columns, `minmax(0, 1fr) var(--desk)` and `"read desk"`, and below 1100 pixels one, `"read" "desk"`,
and `--handle`, `.stage.no-guide`, `#guide-handle`, `#guide-toggle` and their rules are gone. The
`aside.guide` keeps its place in `.stage` and its contents, and is `position: fixed` under the title
bar, `top: 48px` until it went under the band too (17 October, later), at the right, `min(340px,
100vw)` wide, `z-index: calc(var(--z-bar) - 1)`, in `--paper-sunk` with `--lift`, off the screen by `translateX(100%)` and `visibility:
hidden` until `.open`, which slides it in over `--quick` with `--ease`, the reduced motion rule
taking the slide away. `#btn-guide`, a `.bar-tool` after `#btn-view` with `aria-controls="guide"`,
is pressed in through `aria-expanded`. `guide(open, how)` in `app.js` sets `.open` and
`aria-expanded`, keeps `open` or `closed` under `GUIDE_KEY`, `idiograph-guide`, in `localStorage`
when `how.keep`, moves the focus to `#guide-close` on opening when `how.focus`, and to `#btn-guide`
on closing when `how.focus` or the focus was inside it. `guideStored` reads `open` alone as open, so
a new install, a key absent and the rail's `away` and `here` all read as closed, and `boot` calls
`guide(guideStored())` without keeping it. `toggleGuide(focus)` serves `#btn-guide`, with the focus,
and `g`, without it. `#guide-close` closes with the focus, a `pointerdown` in the capture phase
outside `#guide` and `#btn-guide` closes it while `#work` shows and lets the press go on, and `Esc`
closes it after the View menu and before the row's menu while no overlay is open. Measured on the
demo with the sheet closed, the notes stand beside the words from the widest window down to 1101
pixels in two columns, `.transcript` 643 pixels there, 802 at 1280, and below 1100 pixels, stacked,
down to about 570, 913 pixels at 1024 with the words 405 and the notes 254, so the container
thresholds stay 640 and 540. Open, it covers the right of the screen and changes no width. Since 17
October the stage is the three columns and these measures are history (see The three columns).

**The statements screen after the sheet (17 October).** A screenshot check of the sheet's build found
twelve things, and these are the changes. The sheet's edge is `--rule-firm` beside `--lift`, and
`@media (max-width: 520px)` makes it `width: 100%` with no edge, as `.th-cpanel` is there.
`guideHolds()` in `app.js` answers whether the open sheet takes the keyboard, focusing `#guide-close`
unless the focus is already inside `#guide`, and `focusEntry` and `openPassage` ask it before they
focus a field, so a reload through `comeBack`, a passage from a board and `Cmd + J` or `Cmd + K` never
leave the caret under the sheet. `unsay(message)` hides the line at the foot while it still says
`message`, and `openCase` calls it with `OPENING_LINE` once `startCase` has drawn the case.
`keyName(text)` names every key on the screen: on a Mac it keeps `Cmd` and `Option` of a card's `Cmd /
Ctrl` and `Option / Alt`, and elsewhere it turns `Cmd + ← / →` into `Home / End`, `Ctrl + Cmd + ` into
`Ctrl + Alt + `, those pairs into `Ctrl` and `Alt`, and any `Cmd` left into `Ctrl`. `PAIR_QUOTE_HINT`,
`#commit-hint`, the correction box's hint, `trimmedLine`, the replace's line and the timecode's line
use it, and `boot` runs it over `#help .keys td.mono` as over every title with `Cmd + `, so no
`MAC ? 'Cmd' : 'Ctrl'` is left. Since 17 October, later, it writes a letter key it is given in its
capital, alone, in brackets, after a `+` and after "press", and every key written by hand stands in its
capital too (area 171). Since i18nleft (1 November 2026) the keys' names it reads and writes are the
catalogue's, `shell.keys.cmd`, `ctrl`, `option`, `alt`, `shift`, `home` and `end`, so a language whose sentences say
Strg for Ctrl names it so and `keyName` finds it there. `loadAudio(sheet, cueSeconds, again)` keeps `#player-wrap` hidden
until `/api/audio` finds a recording or says the demo's is building, `again` the look again that
keeps the building note, and with none the note keeps the server's words for `playFrom` and
`togglePlay` to say. `#sel-quote`, `#sel-give` and `#btn-quote` carry their words alone, their keys in
their titles, and the quote candidate's head its label alone, so `.sel-bar .mono` and
`.quote-preview-hint` are gone. `.bar-tool` is `font-size: 15px` and `font-weight: 600`, so the
typed `?` of every bar's Shortcuts matches the drawn icons, and `.bar-word` keeps `font-weight: 400`.
`.turn.current .speaker`, `.turn.current::before`, `.round-mark.now` and its rule, and the margin's
hovers take `--ink`, never `--crux`. With the notes left, from 1001 pixels and 640 of column,
`--notes-w` on `.turn` and `.round-mark` is `max(200px, (100% - 118px) * .32)`, the notes' width at
the right, the row's `padding-left` is 0, its columns `minmax(200px, calc((100% - 108px) * .32))
minmax(0, 1fr)` with a gap of 130, and `.turn-gutter` stands at `--notes-w` plus 22, `.turn-done` and
the current rule at plus 120, and a round's marker after the notes the same way, so the margin keeps
its 16 pixels to the words, measured at 1280 and 1024. Below 1001 the margin's line takes
`grid-column: 2` with the notes left, all of which the three columns of 17 October replaced, the
margin standing in the transcript's column in every order (see The three columns), as `#commit-hint`
and `#btn-quote` went with the panel. Rowan's and Mabel's "Statements complete" is right: each case
is marked and every passage decided, and each opens on its last passage, `reviewed-empty`, skipped
with no statement.

**The screenshot check of those fixes (17 October, later).** Ten more, and these are the changes.
`.guide` stands at `top: calc(48px + var(--band))`, under the research question at every width, and
`@media (min-width: 1101px)` gives it `width: var(--desk)`, the stage's last column, so its left edge
is the fields' column's on a page with no margin, where since 17 October `#work.guide-whole` gives it
`--guide-w` over the last of the three columns (see The three columns). `.guide.open` carries `--lift` and a spread of
`100vmax` in `color-mix(in srgb, var(--paper) 62%, transparent)`, the wash over the rest of the
screen where the columns stack, a shadow that takes no pointer, and the same block takes it back to
`--lift` alone above 1100px. `stickyBottom()` in `app.js` measures the foot of `#work .rail` and
`#band` as they stand, the hidden ones aside, and `SPEAKER_CLEAR`, 24, keeps a speaker line clear of
the column's 30 pixel mask: `centreCurrent` caps its scroll so the current passage's top stands at
the larger of the column's head plus `SPEAKER_CLEAR` and `stickyBottom()` plus 8, after the field's
rule of 16 October, and `passageStartInView` takes `stickyBottom()` for the bar's foot.
`selBarSpeaker(holder)` answers the box of a passage's `.turn-gutter`, and `selBarPlace` moves the
toolbar over that line where the two would meet above the selection, and under the line where they
would meet below it. `guidance.md`, `#en`'s placeholder and `NOTE_PROMPTS` speak of the participant
as they. On the boards `thCountSet` leaves out every part of the counts that reads 0, the discarded
in its `.th-count-bin` only when there is something before it. `gtTableFace` writes
`GT_NOTHING_NO_PETS` for a participant with no PETs and nothing under the GET, with no `GT_NO_PETS`
mark, and `gets_print.py` writes `gets.NOTHING_NO_PETS` the same way in the trail and the table on
paper, `.gt-tnone` and `.tr-none` in `--ink-soft`. `.kicker` is `--ink-soft`, never `--crux`.
`.gt-find` keeps no padding under the field, and `.gt-cases` takes `padding-top: 14px`, and with
`.scrolled`, which its `scroll` listener sets once it has scrolled, a `mask-image` that fades its top
26 pixels, reading the ink's alpha alone. On the Rename card `#rn-lead`
says What will change over `#rn-list`, and `rnListShow()` shows both only while the list holds a line
and `#rn-said` is hidden. The way back on GETs keeps the rule `gtScreen` and `themesOpen` already
drew, the arrow alone to the case list and PETs beside it back to PETs, which `drawBackTo` keeps on
Experiential statements.

The player bar's jump buttons (jumpbtns, 8 November 2026, Adam's pick of three drawings): `#player-back` and `#player-fwd`, `.player-jump` with an inline `.jump-ico` (an arrow and a small 5, stroked in `currentColor`), either side of `#player-play` in `#player-bar`, `tabindex="-1"` as Play has. Their `onclick` is `nudgeAudio(-AUDIO_STEP)` and `nudgeAudio(AUDIO_STEP)`, the function the `Ctrl + Cmd` arrows call, so the jump clamps at 0 and at the end and moves the playhead, the elapsed time and the current turn at once. The tooltips are `page_idiograph.work.five_seconds_back_key` and `five_seconds_forward_key`, the labels the shortcuts card's. At 720 wide only the track gives way. Area 336 holds it.

### Working together's comments and review (wtreview, 8 November 2026, on the team layer since wtreview2, 9 November)

`apps/idiograph/review.py`, build 4 of the spec of 8 November. The messages are the spec's `review_asked`,
`comment` (a thread's first comment and every reply), `thread_state` (resolved, unresolved, reopened) and `review`.
A send applies the message here at once, under `.idiograph-team/.review.lock`, then hands it to
`team_sync.post`, which seals it (`team.seal_envelope`, the roster's present epoch, this computer's signature),
keeps it sealed in `.idiograph-team/out.json` and sends it through the project's transport at once, or, with no
connection, at the next look (`team_sync.flush`, first thing in `push`), the waiting count on the project's page
counting it. Nothing is written in the clear for another install to read, and nothing here reads team.json: the
roster, the owners (`team.owner_here`, by folder) and the names come through `team_sync.team_on` and team.py. What
comes is opened by `team_sync.pull` (a device not on the roster, a bad seal or signature dropped there), and these
kinds are in `team_sync.EPOCH_NOW`, so one sealed under an epoch older than the roster's is dropped as
`old_epoch`. `team_sync.HANDLERS` hands the rest to `review.came`, which drops a kind its member may not send (an
ask on a participant he does not own, a first comment on his own, a reply or state on another's thread) and notes it
in `.idiograph-team/log.jsonl`. `team_sync.builds` imports review.py before a look so its handlers are there.
`review.review_with` is `team_sync.REVIEW_WITH`: each participant of this member's with an ask whose first teammate
has sent neither a review nor a board since, for "With Curt for review". What this install holds, its drafts,
threads, reviews and asks, is `.idiograph-team/review.json` (schema 2). The folder is in `project_pack.LEFT_OUT`. A
participant is named in a message by its folder from the root, the GETs board by "", and on the page and to agents
by its pseudonym. `view` puts each board come in (team_board's record) beside the unread review of the same
teammate and participant, or as a review of its own, `board-<ref>`, holding only that board, while it waits.

The page's route is `/api/team-review` (`state`, `ask`, `comment`, `send`, `reply`, `thread`, `done`, each with
`dry_run`), post only. `state` with `all` gives every review and thread of the project, the participant on view
named apart with its owner. The command line's `team ask`, `comment`, `review-send`, `reply`, `thread`,
`review-done` and `review` run the same functions, and MCP's `team_*` tools the command line's. Each write adds one
record to the project's History (`team ask`, `team comment`, `team review send`, `team reply`, `team thread`,
`team review done`). Answers name a comment's words `text` and the words it is on `quote`, so `cli.mark` marks
both for an agent. Area 343 runs three installs through the loopback transport and the shared folder.

The page's part is `static/review.js` and `review.css`: Ask for review in a participant's row menu
(`rvwRow` from `drawCards`), Comment under each pair (`rvwPairsDrawn` from `pairsDrawn`), by the selection
(`#sel-wtcomment`) and in a label's menu (`rvwLabelItems` from `thMenuItems`), the tray `#wt-tray` (a row of the screen under the toolbar's dock, moved there by `rvwTrayDraw`, its height in `--band` through `measureBand` and `thBandMeasure`, so it covers neither Columns nor a grip nor a card), the owner's line
`#wt-line` in the held line's look (`rvwCounts`: comments, and a board), and the card `#wt-review`, a board's item
(`rvwBoardHtml`) with Decline and Add as next board calling `/api/team-board`'s `answer`. It asks for `state` every four seconds on the
statements screen, PETs and GETs, and draws nothing while the answer is `{on: false}`. Its top-level names begin `rvw` and `RVW` (wtreview2), since team.js, on the same page, has `WT` and `wt...`: one script's `const` of a name another declared stops that script loading.

**Suggestions** (wtsuggest, 10 November 2026, the spec's build 5). `review.suggest` keeps a draft in review.json's
`suggestions` (status `draft`) holding the op the command line would run, unrun: `turn write` with every pair of
the passage by its key and the one statement reworded (built as board import builds a rewording), `board apply`
with a `retitle` on the owner's board (the board on view when it is the owner's, else the Current one, never one of
the reviewer's own), or `gets apply` with one. `on` keeps the kind, key, time, label and board, and `seen` the
words as he saw them. `send` sends each draft as a `suggestion` message (`id`, `on`, `op`, `seen`, `text`,
`reason`) before the `review`, which names them under `suggestions`. `came` applies one only from a member who
does not own its participant and whose `op` is its kind's (`_op_ok`). `_target` finds what a suggestion changes
in the files as they stand, words first, key second: `stale` when only the key found it, `gone` when neither did.
`review.answer` (route op `answer`, `team suggestion-answer`) accepts by rebuilding the op on what `_target` found
(`_run_args`), running its dry run, then running it through `idiograph_cli.run_scoped` as `holds.approve` runs a
held op, `_approved` set, the tool "Curt's suggestion, accepted in the app" (or "accepted by" an agent's tool) and
`_member` set, which `idiograph_cli.mark` turns into `by: "member"` with `themes.MEMBER_KEYS` (`member`,
`accepted_by`, `suggestion`) on the board's `changed` and `made` marks and the progress file's edit
(`themes.agent_mark` and `made_mark` keep them). The project's History record (`team suggestion-answer`) carries
the same. Decline writes nothing to the files. Either sends an `answer` (`what: "suggestion"`, `of`, `accept`,
`to`, `reason`), which reaches the reviewer through team_sync's one `answer` taker, now `review.take_answer`,
handing a board's answer on to `team_sync.take_board` and keeping a suggestion's beside it with a `team take` line
in History. `team suggestion-answer` is in `holds.HELD` (risk 1). `view` gives each review's `suggestions` (with
`now`, `stale` and `gone` while it waits) and `waiting`, and the reviewer's own as `suggested` and `suggestions`.
Their words sit under keys `cli.mark` marks. On the page, `rvwPairsDrawn` adds Suggest a wording
(`data-wt-sline`), `rvwLabelItems` Suggest a title (`wtsuggest`, `rvwLabelSuggest`), `rvwSuggestHtml` the box,
`rvwSuggestItem` the card's item with Decline (asking why, `RVW.decline`) and Accept, and the line stays while a
review has `waiting`. `project_history.for_page` and Project history name a member's record "Curt's suggestion,
accepted by you". Area 368.

## The API

The page talks to the server through the routes in `ROUTES`, near the end of `server.py`, a JSON
body in and a JSON answer out. Each answers a POST with its fields in the body, and a GET with the
same fields in the query string, except `/api/feedback`, `/api/choose-root`, `/api/projects`, `/api/new-project`, `/api/add-transcripts`, `/api/names`, `/api/qdpx`, `/api/open-sent`, `/api/send-project`, `/api/order`, `/api/rename`, `/api/mcp`, `/api/sift`, `/api/sift-search`, `/api/trace`, `/api/trace-project`, `/api/sift-review`, `/api/databases` and `/api/zotero`, which take a POST alone, and `/api/server`, whose POST restarts or quits. A refusal comes
back as `{"error": ...}`: 403 for a path under no project's root, 409 for one the workbook layer
refuses, Excel's lock among them, 400 for a missing field, 404 for a route that is not there and
500, with the exception's type and words, for anything else. A route of another app of the family
answers 404 with `app` and `port` naming the app that has it (see Each app its own routes), Sift's and
Trace's on Idiograph's server since the cutover of 23 October 2026. A workbook is named by its path,
absolute or from the repo root, or the app's folder in a downloaded copy. The routes, in the table's order:

| Route | Body | Answer |
|---|---|---|
| `/api/cases` | nothing | The case list, the recent list, the demo's rows as `demos`, Juno, Rowan and Mabel, with Juno's alone as `demo` for an older page, the thematic analysis demo's as `demos_ta`, its cards as `demo_ta_participants` and its project as `demo_ta_project` (3 November 2026), the settings, the root, empty while none is chosen, the project, `feedback` and `choose`, whether the Mac's folder dialog is there, `version`, the server's, which About shows in a browser tab (20 October), and `gets`, the GETs card's figures, or null. Each row carries `board`, the Current board's name or null, read from the themes file's head, and `complete` and `pets_complete`. `participants` is the home screen's cards and `demo_participants` the demo's, built from the same rows (see The cards). `cases` and `recent` stay for a page from before the cards. `reviews` is the Sift section's cards, each review in the list with where it stands and `screening`, its newest screening (see A review). |
| `/api/days` | nothing | The rounds closed on each date across every case under the root, summed from each progress file's `days`, with `today` and `dailyTarget`. It only reads. |
| `/api/open` | `path`, and `passage`, a sheet and a row, from a statement card (16 October) | The case: its sheets and rows, its rounds, the progress summary, `last`, the settings, the project and `feedback`. Any case but the demo goes to the head of the recent list. With `passage` it is refused, the list as it was, unless the transcript has a participant passage there. |
| `/api/create` | `path` of a raw source, and `out` when named | The annotated workbook built from it, answered as `/api/open` answers. |
| `/api/import` | `path` of a transcript file, `op` of `read`, `make` or `pick-audio`, `columns` for a Word table, a CSV or an Excel file, a list of a role a column (`name`, `ts`, `text`, `en`, `es`, or "" to leave it out) or a `{role: index}`, `speakers`, a role a speaker (`interviewer`, `participant`, `other`), `times`, `{format, fps}`, `audio`, a recording's path, `offset` in seconds, and `interviewer` from a page before `speakers` | For `read`, the first turns as read, each with its `en` and `es`, the speakers, the interviewer guessed, `as`, the name each speaker's turns go under as the interviewer, the headings, `mapping` and `roles` of a table, `shown`, the preview's columns, `brings`, the line saying what a Word table brings beside the words and leaves out, empty for any other file, and `said`, one line when nothing can be read or the raw source is already there. For `make`, the raw source written beside the file, a Word table's notes with it, as a case list row. |
| `/api/commit` | `path`, `sheet`, `row`, `pairs`, `en`, `round`, `away`, `v`, and `es` and `kq` as text for a page from before the pairs | The turn's statements, quotes and notes written, the statements and quotes from `pairs` as `pairs_to_cells` sets them out, with `pairs` as they now read, `unpaired`, `v`, its state and the summary. `v` is `workbook.passage_version` of the three cells as the page read them (every row of `read_case` carries it): a save that would change a passage whose cells hold another version now is refused with 409, nothing written, the progress file included, and `stale`, the passage as it now reads (`workbook.turn_now`), which the page shows on its stale card (18 October). A page that sends no `v` saves as before. |
| `/api/crux` | `path`, `sheet`, `row`, `start`, `end`, `text`, and `op` of `add` or `remove` | The highlight added, taken off or toggled, and the op it performed. The page calls it no more since Highlight went on 16 October. |
| `/api/edit-turn` | `path`, `sheet`, `row`, `text`, `timecode` | The turn corrected and its row as the reader renders it, with any highlight dropped. |
| `/api/replace` | `path`, `find`, `replace`, or `pairs`, a list of [find, replace], `word`, `case`, `dry_run`, `mask`, `tool` and `request`, and for one occurrence `sheet`, `row`, `ordinal` and `text` | The rows changed as the reader renders them, each with any highlight dropped and the passage's `es`, `en`, `kq`, `pairs`, `unpaired`, `v` and `note`, the count per sheet, `places`, a line for each column of each row, its sheet, row, timecode, column and count, never the words, the `batch` id, and `boards`, `gets` and `failed`, what took the new words beside the workbook. With `dry_run` the count and the places alone, nothing written (`routes.replace_in_case`). |
| `/api/replace-undo` | `path`, `batch`, `redo`, `dry_run`, `tool`, `request` | The rows written back, or written again for `redo`, shaped as `/api/replace` answers (`routes.undo_in_case`). |
| `/api/interviewer-note` | `path`, `sheet`, `row`, `text` | The note as written, and `changed`. |
| `/api/trim` | `path`, `sheet`, `row`, `direction`, `current` | The trim's record, its id among it, and the turn to land on. |
| `/api/rows` | `path`, `op` of `assign`, `preview`, `restore` or `untrim`, with `sheet`, `row`, `to`, `start` and `end`, or `id` | An assignment and the turn to land on, the confirm card's lines, or the rows put back. |
| `/api/audio` | `path`, `sheet` | Whether the sheet has a recording, the `/audio` address that streams it, and its `offset` in seconds, the time codes kept as they are and playback moved by it. |
| `/api/audio-offset` | `path`, `sheet`, `offset`, `dry_run` | A sheet's recording given a new offset, kept as `offset.json` beside it (`server.set_audio_offset`), the offset it had as `was`, and the new. |
| `/api/audio-attach` | `path`, `file`, `timepoint`, `interview`, `replace`, `offset`, `dry_run`, `tool`, `request` | A recording copied onto an interview already in (audioop, 9 November 2026), `routes.attach_audio`: the interview is the participant's sheet at the timepoint (`attach_sheet`), the file checked by `recording_checked` (a file Idiograph plays, there, not empty), the copy named by `recording_name` and put where `place_audio` puts an import's, so the player finds it, its offset beside it. An interview with a recording is refused unless `replace`, which moves the one there to the case's `_Archive/` first, and a failure puts everything back. History is a record under `imports` with `attach`, the copy's name, the sheet and the timepoint. No page calls it, `cli audio attach` and MCP's `audio_attach` do. `add_transcripts` takes `audio` and `offset` on an entry the same way (checked in `new_cases`, copied by `write_case` and `add_interviews` through `place_audio`, `add_plan` answering `recording`, `add_record` listing `recordings`). |
| `/api/reset-demo` | nothing, or `demo` of `ta` | The three demo cases put back as they ship, and the demo's GETs file and its `Working/` removed. With `demo` of `ta` (3 November 2026) the thematic analysis demo's three, its code list and its Themes board's file, the IPA demo left alone, answered with `demo`, the id of the demo reset. |
| `/api/round-complete` | `path`, `round` | The summary, and `recorded`, whether this call recorded the round. |
| `/api/complete` | `workbook`, `op` of `mark` or `reopen`, `timepoint`, and `dry_run` | The mark's time, or null, and the summary. With `dry_run` (26 October, for `participant complete`) nothing is written, and the answer is the mark as it stands and `changed`, whether the op would change it. |
| `/api/export` | `path`, `notes`, `dry_run` | The statements CSV written, and the interviewer notes file when `notes` is true, with their paths. With `dry_run` (26 October, for `participant export`) the same checks and the same answer, the files it would write, and nothing written. It keeps no History, from the page or an agent. |
| `/api/themes` | `workbook`, and `board` to show that board in place of the one last open, and `beside` for a look from the GETs canvas | The PETs screen: the cards merged with the stored board, the boards, the picks and the history, `chosen` and `complete`, with `ai`, `platform`, `project`, `config`, `print`, `notes`, `guidance`, `feedback` and `word`. Any case but the demo goes to the head of the recent list, unless `beside`. |
| `/api/themes-save` | `workbook`, `version`, `revision` | The board written, and the history when the timer's revision was kept. `version.v` is the board's version as the page last read it (`themes.board_version`, a hash of the board as the file holds it, its history aside, never written): a save over a board holding another version now is refused with 409, nothing written, and `stale`, the board's id and its `v` now, which Overwrite sends back (19 October). An agent's change keeps the History path of `OUTSIDE`. |
| `/api/board-order` | `version`, the board as the page holds it, `under`, a label's id or null for the PETs or the GETs, `items`, `heights`, the page's measures of its cards by key, and `gets` | The Table view's reorder (19 October): the board set in that order through `themes.reorder`, the one an agent's `order` op runs, and where each card, label and sticky note then stands, `cards`, `groups` and `notes`, with `order`, `how` and `moved`. Nothing is written: the page lands the places as one step of its undo and saves as the canvas saves. |
| `/api/themes-versions` | `workbook`, `op` of `new`, `duplicate`, `rename`, `note`, `switch`, `delete`, `choose`, `complete` or `reopen`, `id`, `name`, `note`, `dry_run` | The screen's state afterwards. With `dry_run` (26 October, for `board note`) every check is made and nothing is written. |
| `/api/themes-boards` | `workbook`, `op` of `copy`, `revision`, `view` or `restore`, `id`, `revision`, `group`, `to`, `name`, `dry_run` | The revision for `view`, and the screen's state afterwards for the rest. With `dry_run` (26 October, for `board revision`, `restore` and `copy`) every check is made, nothing is written, and the answer is the op with the revision it would keep and what it would restore or copy. |
| `/api/participants` | `workbook` | The statements tab's participant picker: `participants`, every participant of the workbook's project with an annotated workbook in participant order, each `case`, `path` and `current`, and `project`, its name. Writes nothing. |
| `/api/themes-cases` | `workbook` | The case switcher's `cases`: every case of the project with a themes file, by its pseudonym, each with the board it opens on and `table`, that board's print view, and on any demo case the demo's three. Writes nothing. |
| `/api/themes-export` | `workbook`, `version`, or `op` of `word`, or `op` of `reveal` with `file` | The PET draft and the CSV written, with their paths and `shown`, or for `word` the Word document written at the case folder's root, never over a file, with `word`, `shown` and `dated`, or the file shown in the Finder. With `dry_run` (26 October, for `board export --draft`) the draft is made in memory and nothing is written, the answer naming `markdown` and `csv` and `there`, those a write would put a new copy over. |
| `/api/themes-ai` | `workbook`, `op` of `names`, `version` and `group` | Up to three `names` for the label `group` names, and `said` when quotes went for room. Any other op is refused with `unknown_op` (aiout, 11 November 2026: New AI board, AI review and AI revise went). Writes nothing. |
| `/api/edit-statement` | `workbook`, `sheet`, `row`, `line`, `text`, `old`, or `check` | The new text, or `ready` and `copies` for `check`. Every board of the themes file, at the sheet's timepoint, whose card held `old` takes the new text, and `versions`, each board's summary after, so the page's next save carries the version the edit wrote. Since 30 October the GETs file's copy of the participant, and in a project of timepoints the participant's LPETs and the LGETs, take it too, under `copies` by `gets`, `lpets` and `lgets`, each with `cases`, `boards` and `versions` (see getsedit, under the statement card's passage). |
| `/api/gets` | `workbook`, any of the project, the case root's with none, and `board` | The GETs screen: the board's cards named from each case's copy, its groups, its `rows`, the boards, `cases` for the Cases panel with what changed, each with the `path` and `board` Open beside opens and its `colour`, `default`, `chosen` and `badge` (16 October), `colours`, his choices, `study`, `settings`, `minimum`, `band` and `total`, `discard_reasons` of the board, `ai`, the switch and the PETs model, `guidance`, the GETs sections of `pet_guidance.md`, a thematic analysis project's `ta_themes_guidance.md` with `guidance_ta` true, and `root` and `gets_print` for the print view. Writes nothing. |
| `/api/gets-head` | `workbook` | `gets`, the GETs card of that workbook's project: `cases`, the cases of the study, `complete`, those with PETs complete, `held`, those the GETs file holds, `board`, its Current board's name or null, `boards`, how many it has, `done` and `path`. Writes nothing. |
| `/api/gets-save` | `workbook`, `version`, `revision` | The board written, every case not yet in taken in on the way, and the history when the timer's revision was kept. A save whose `version.v` is not the board's now, after an agent's gets apply or take or another window's save, is refused with 409, nothing written, and `stale` as `/api/themes-save` gives it (19 October). |
| `/api/gets-ops` | `workbook`, `op` of `new`, `duplicate`, `rename`, `note`, `switch`, `delete`, `choose`, `complete` or `reopen`, `id`, `name`, `note` | The screen's state afterwards. `complete` is refused while a case of the study is not in from its marked board unchanged. With `dry_run` (26 October, for the agents' `gets` board ops) every check is made, nothing is written, and the answer is the op, the board on the canvas after it, `complete` and each board's id and name. |
| `/api/gets-boards` | `workbook`, `op` of `revision`, `view`, `restore` or `subs`, `id`, `revision`, `name` | The revision for `view`, `added` for `subs`, Add every sub-theme, a card for each sub-theme of the study with none on the board, placed by `gets.add_subs` through `gets.lay_in`, for the page to land as one step of undo, refused with one line when there is none, and the screen's state afterwards for the rest. `view` and `subs` write nothing, and with `dry_run` (26 October, for `gets revision` and `restore`) no op does. The agents' `gets subs` puts each card `subs` answers on the board at the place it gives, the board kept first in its History. |
| `/api/gets-cases` | `workbook`, `op` of `take` or `colour`, `case`, and `colour` for `colour` | `take`: the changes of a case changed since it came in taken in, each board keeping a revision first (the page's `gtTakeAll`, by itself for a change of the app's own and from Update for one from outside, since 20 October, when Take the changes went), and the screen's state afterwards. `colour` (16 October): the case's colour on the GETs board, a place in the cases' palette from 0 to 24 (to 7 until 21 October) or null for Default, one another case has refused, kept in the GETs file's `colours` at once through `gets.colour_op`, a case the project does not have or a colour the palette does not hold refused with nothing written, and the screen's state afterwards. |
| `/api/gets-settings` | `workbook`, `op` of `read` or `save`, and for a save `minimum`, `one_per_pet` and `study`, any of them | For `read`, what Settings shows under GETs, reading no workbook. For `save`, the screen's state afterwards, or with `dry_run` (26 October, for `gets settings`) nothing written and the settings and each case's place in the study as they would be. |
| `/api/gets-trail` | `workbook`, `board`, `get` | One GET's audit trail as `html`, every item and the participant notes with it, without the head the card draws, and its `label`, `note`, `tint`, `count`, `total`, `minimum` and `under`. A turn with a recording carries its `/audio` address. Writes nothing. |
| `/api/gets-ai` | `workbook`, `op` of `names`, `version` and `group` | As `/api/themes-ai` answers, on the GETs board `version` names: three `names` for a GET or a sub-theme. Refused with the switch off, on LPETs and LGETs, in a thematic analysis project and for any other op. Writes nothing. |
| `/api/search` | `q`, `scope` of `case`, `project`, `sift`, `trace` or `all`, `path`, a workbook, or for a project `root`, its id, for `sift` and `trace` `folder`, the project's as the page names it, a review's, a screening's or a Trace project's, and the filters ticked, `kinds`, `cases`, `sheets` and `projects`, each a list | Search across the app (17 October, `app_search.search`, and 18 October, `search_sift`, `search_trace` and `search_all`): every word of `q` in an item's words, in any order, case and accents aside, as Sift's `sfFindMatch` matches. `case` reaches the workbook's passages, interviewer notes, statements, quotes and exploratory notes, and its themes file's PETs, sub-themes, their notes, sticky notes and board notes, every board's. `project` reaches every case of the study as `held_books` finds it, in his order of the cases (`search_cases`), the GETs file's GETs, their notes, the GET table's row notes, participant notes, sticky notes and board notes, the cases' names and the research question. `sift` reaches, through `search_sift_place`, the screening a review's Screening step opens, or the screening named and the review it belongs to, each record's title, searched with its rec_id, abstract, authors and journal, his decision notes at each stage from the log, his notes, digest, critique and columns, a column on the form his form's answer, his key excerpts, and the newest version's search terms and exclusion reasons, the review's `reasons.csv` where it holds one. `trace` reaches each manuscript of the project as `trace_claims.analyse` reads it with the project's list, its claims, the references they take, one shared by two manuscripts once, and his claim notes from the log, or with no manuscript the reference list. `all` reaches every Sift project in the list, every Idiograph project as `project` does with the demo last while its workbooks are there, and every Trace project in the list. History revisions, AI threads, AI proposals, AI passages, PDFs' text and reviews stay out. The answer: `results`, the first 200 by kind in `app_search.ALL_KINDS` order, Sift's, Idiograph's and Trace's, project, case and place, each `kind`, `text`, cut to a window of 240 characters round the first word found, `where`, `case`, `sheet`, with `all` `project` and `part`, and `go`, where a click lands, `screen` of `statements`, `pets`, `gets` or `project` with the workbook's `path`, the `sheet`, `row`, `field` and `line`, or the `board` and the `item` to select, a `group`, `card` or `sticky` by its `id`, `sift` with the screening's `folder`, the `rec`, the `stage` it lands at, `ta`, `ft` or `ex`, the `field`, `form` and an excerpt's `line`, `searches` with the review's `folder` and the `block` and `line` or the `reason`, or `trace` with the project's `folder`, the `doc` and the row's `key`. Then `total`, `counts` by kind, `cases` and `sheets` with theirs for `project`, `parts` and `projects` with theirs for `all`, each group counted with the other groups' ticks alone, and `ms`. Each file is read once and held in `app_search.HELD` against its time and size, a screening's against its CSV's, its log's, its `sift.json`'s and its plan's, and a manuscript's against its own, its log's and the project's list's, as `read_book` holds the workbooks, and nothing is written, no index on disk, not the recent list and no list of projects. |
| `/api/stamp` | `workbook`, and `gets` for its project's GETs file | The file's `updated`, the board on the canvas, the Current board and each board's `id`, `name` and `updated`, with `made` and `changed` when an AI agent made or changed it, and without `gets` `turns`, how many turns an agent wrote and the last. `outside` (20 October): the themes file, or with `gets` the GETs file, is not as this process last wrote it (`workbook.written_here`), so an AI agent's command line or a hand on the file changed it. With `gets`, `cases` lists each case changed since it came in as `{case, outside}`, `outside` from `gets.changed_outside`. Without `gets`, `workbook` too, the workbook's `st_mtime_ns` as text and `here`, whether this server wrote it last (`written_here`). Writes nothing. The PETs and GETs screens and Experiential statements ask it on a focus, Experiential statements and PETs every four seconds since 20 October and GETs every thirty. |
| `/api/agents-guide` | `root`, the project's id, or `path`, and `update` | `AGENTS.md` written at that project's root from `docs/agents.md` with the project filled in, or `ours` when the app's own is there already and `update` was not sent. Refused over a file of his and for the demo. |
| `/api/examples` | `gravity_only` | Three statements for the examples rail. |
| `/api/nudges` | `text`, `path` | The nudges' lines on it, the length nudge at the statement length of the project `path`'s workbook belongs to, 15 without one, and `statement_words`, that length. |
| `/api/settings` | the settings to save | The settings as saved, and `ai`. |
| `/api/project` | `root`, the project's id, or `path`, a workbook of it, and `name` and `research_question` for a save, or `agents`, true or false, or `pet_labels`, `letters` or `numbers`, or `timecodes`, `75:12`, `1:15:12` or `01:15:12` | The project, with `agents`, the privacy tick and when it was set, `pet_labels` and `timecodes`. A save naming no project is refused while there are several, and so is a save for the demo. A save answers `changes`, a line each, and with `dry_run` (26 October, for `project set`) the name, the question, the tick, the labels and the timecodes are said and nothing is written. |
| `/api/choose-root` | nothing | Choose folder for a page from before the projects: the Mac's folder dialog, and the folder chosen added as a project, answered with `chosen` and its `root`, or `chosen` false for Cancel with nothing written. Off a Mac it refuses. |
| `/api/projects` | `op` of `read`, `add`, `remove` or `reveal`, and `path`, the folder typed, for an add, or `root`, the project's id, for a remove or a reveal | Every project as `read_project` reads each, with `choose` and `one`. `add` with no `path` opens the Mac's folder dialog, and adds the folder through `add_project`, answered with `added` and the `project`, refused for a folder added already, inside another project's root or holding one, or holding the app or its demo. `remove` forgets the project, its files untouched, answered with `removed`, its `name`, `folder` and `trash`, from Settings or a card's Remove from Idiograph, and with `trash` (removetrash) moves its folder to the system's Trash first through `srv.trash_guard` and `srv.trash_move`, answered with `where`, `page` the asking page and `dry_run` moving nothing. `reveal` (21 October), a card's Show in Finder, shows the project's folder through `show_project_folder` and `SHOW_FOLDER` (`open -R` on a Mac, `explorer /select,` on Windows), writes nothing, and refuses the demo, a folder not there and any other machine, answered with `revealed` and its `name`. A run with `--root` adds and removes none. |
| `/api/new-project` | `op` of `folder`, with `path` or none for the Mac's folder dialog, `read`, with a file's `name`, its `data` in base64 and `columns` for a table, or `make`, with `folder`, `name`, `research_question` and `files`, each `name`, `data`, `columns`, `interviewer`, `pseudonym`, `interview` and `number` | New project, through `api_new_project`. `folder` answers the folder as it will be added, refused as Add project refuses one, its `next` free number, and the `name` and `research_question` a project file there gives, or `chosen` false for Cancel. `read` answers the file as the import card's read does, with `interview`, its name guessed from the file's by `convert.interview_of`. `make` checks every file first and refuses in one line, then writes each case, `P<n> - Pseudonym` with its copies in `Source/<interview>/`, its raw source of a sheet an interview and its annotated workbook, the project file, and the folder added through `add_project`, answered with every project, `made`, the `project` and its `cases` by label. A failure takes away what that Make wrote. `make` with `dry_run` (26 October, for `project new`) makes every check and writes nothing, answering the folder, the name, the question and each case it would make, its label and each interview's file, speakers' roles and timepoint. |
| `/api/add-transcripts` | `op` of `project` or `add`, each with `root`, the project's id, and for `add` the `files` as `make` takes them | Add transcripts, through `api_add_transcripts`. `project` answers the project's `name`, its `next` free number and its `cases`, each `label` and `pseudonym`. `add` checks every file first and refuses in one line, then writes a new pseudonym's case as Make does and adds a case's own as a further interview: its copy in `Source/<interview>/`, a sheet at the end of the raw source through `convert.add_sheets`, and the same sheet at the end of the annotated workbook through `workbook.add_from_source`, once `archive_copy` has kept the workbook in `_Archive/` as `(pre-add <date-time>)`. Its answer is the `project`, its new `cases` and the cases `joined`, by label. A failure puts the workbook back from its copy and the raw source from its bytes, and takes away what that Add made. A file is read through `/api/new-project`'s `read`. |
| `/api/names` | `op` of `list`, `set`, `remove`, `check`, `replace`, `preview`, `read-key` or `key-file`, with `root`, the project's id (or for `preview` on New project `folder`), and for `set` the whole list as `entries`, for `remove` the entries' numbers, for `replace` the `skip`, for `preview` the card's `files`, `dry_run`, and `tool` for an agent | The project's list of real names and what each is written as, through `api_names`. The app's own call sees the names, an agent's is told numbers and counts alone and cannot set or preview. See Names replaced as a transcript comes in under Files on disk. |
| `/api/qdpx` | `op` of `read` or `make`, the choices `qdpx_import` takes, and either `root`, the project's id, with `path`, a `.qdpx` under its folder (an agent), or the import card's file, its `name` and `data` in base64 the first time and the key that read answered as `held` after, with `root` in Add or `folder` in New project | A REFI-QDA project read or brought in as participants through `server.qdpx_import`, the one function the card, the command line's `qdpx` and MCP's `import_qdpx` share. A card's read answers `held`. A card's make needs `root`, New project's going through `/api/new-project`'s make with `qdpx`. See REFI-QDA projects under Files on disk. |
| `/api/order` | `root`, the project's id, and `order`, its case labels top to bottom | His order saved as `order` in the project's file, every other key kept. The demo's is refused. |
| `/project/send` | a GET, `root`, the project's id, and from Share a copy's card `card`, its choice as JSON | Share a copy (21 October, Send until Adam's Way A): the whole project folder as one zip, `<Project name>.idiograph` by `project_pack.sent_name`, written by `send_project` under the writers' lock to a scratch file and served from it in pieces, `Content-Disposition` naming it, nothing in the project changed. The demo, a folder not there and a root that is no project's are refused in JSON. A browser fetches it through a link with `download`. Idiograph's own window never does, since `window.js` would read the whole file into the page and hand it over in base64: the page asks the window's save panel for a path through `window.idiographSavePath` (the command `save_path`, the panel alone) and posts it to `/api/send-project`. With `card` the choice goes through `card_options` as `/api/send-project` takes it (23 October). |
| `/api/send-project` | `root`, the project's id, `to`, the path the window's save panel chose | Share a copy in Idiograph's own window (21 October): `send_project` writes the file straight to `to`, `.idiograph` added when the name lacks it, through a file beside it renamed into place, so a project with recordings never passes through the page. A file there already is written over, since the save panel asked. A folder not there, a folder at `to`, the demo and a root that is no project's are refused. Answers `sent`, `file`, `name`, `files`, `bytes` and `size`. Since 23 October it takes a chosen send's `participants`, `leave_out`, `with` and `blind` as the command line's options, then answers `participants`, `kinds_out`, `left` and `notes` too, and `dry_run` answers the plan with `listed` and writes nothing. For the card's design E (23 October) it takes `pets` and `audio`, the participants whose PETs or recordings go (`send_chosen` gives each participant its own `out` for `project_pack.choose`), answering `each`, every label sent with the kinds going for it, and `leave_out` of `audio` alone with nothing else chosen is `project_pack.whole_less_audio`, every file of a plain send but the recordings, answering `whole`. Share a copy's card on Home (design E, 23 October) reads `/api/send-list` as it opens and sends `card`, turned into options by `card_options`: `{"whole": true, "audio": ...}` the plain send, or with `audio` false the whole project less its recordings, or `participants`, `pets` and `audio`, the labels ticked in each column, a chosen send of those participants with the GETs left out, and the PETs too when no one's are ticked. No participant ticked is refused. The card's `boards`, `current` or `all`, is the send's `boards` (train 57): the page's `#sc-boards-below`, Boards with Current board only and All boards (Adam's option A, 26 October), shows in both forms only when `scBoardsMatter(list, whole, on, petsOn)` finds a board file going with two or more boards, a participant's `boards` from `/api/send-list` (PETs or LPETs), and in Whole project its `gets_boards` too. `sendProject` starts it on All boards, and `scChoice` sends `current` only while the row is there, so a hidden row sends `all`. Area 263. |
| `/api/boards-in` | `root`, the project's id, `file`, the sent file's path, `from_name`, `participants`, `boards`, each a name or `{participant, board}`, `dry_run`, `request` | A shared copy coming back (26 October), through `boards_in`, as `project boards-in` and MCP's `project_boards_in`: the file read by `returned_from` (`project_pack.read_sent`, the copy's project file in it through `sent_json`), matched to the project by `came_back_to` (`copy_of.uid` against the project file's `uid`, else, for a file from 0.9.5 or earlier, `copy_of.name` against the project's name), each participant's PETs files from `project_pack.sent_boards` matched by label, then pseudonym, and each board turned by `board_coming` (copyback, 6 November 2026, where every card not matched had waited in Not placed): every card keeps its place, its PET, its stack, the bin or Not placed, and is matched through `themes.follow` with its `keys` and `own`: by its words first, the card's text or the copy's `live` reading against the statement at its key, else an unclaimed statement with the same words on its row, the nearest line, then on its sheet, so a statement moved up its passage by a removal is found. Then by its key, a statement no other card took by its words, the card linked to it, its `text` the copy's wording and `live` the project's now, so the canvas marks it changed. Else it moves past every line of its row, placed in the copy's wording and marked missing. A card whose key held no statement when the copy was sent (not in `copy_of.statements`) is the other analyst's own and never takes a statement by its key alone. `unmatched_reason` gives each card not read the same its kind and reason, `edited`, `own` or `differs` when linked, `gone`, `own` or `missing` when placed in the copy's wording, by the prints. The review, revise thread and agent marks are dropped. A participant's boards are named by every board of theirs in the copy, so a board chosen alone keeps the name it has among them. `boards_chosen` reads `boards`, names for any participant's board and `{participant, board, timepoint}` choices for one participant's, at that timepoint alone when given (`timepoint_is`, its number, T2 or its label, since copyback2, where a board unticked at one timepoint came in by its namesake's tick at another), the participant matched by the copy's label, the project's or either's pseudonym, so a participant found by pseudonym alone takes the boards ticked by the project's label. The command line's `--board-of PARTICIPANT BOARD [TIMEPOINT]` (`boards_asked`) and MCP's `boards` objects make the same choice. `from_name`, when empty, is the file's `from`, its sender's Your name. Each is written after the boards there, `current` and `chosen` untouched, under the case's lock, with `origin`, a note and one revision, "Brought in from <file>". A board brought in before (its `origin`) or the same as one there (`state_hash`) is left. A board that is the sender's own as he sent it (copyback2, 8 November 2026) is answered under the participant's `as_sent` and left out unless chosen by name: its `themes.places_print` (each card's key, each PET's id, title and members in order, the stacks, the bin and the loose cards, never names, times, notes, words or canvas places) is one of `sent_places_of`, the prints the send recorded (`send_origin`'s `boards`, by `sent_places`, kept by `mark_copy` in the copy's `copy_of.boards`), or, in `his_places`, of one of his boards now or a revision in their History, a board brought in from a copy (its `origin`) never counted. Chosen, it comes in with `as_sent` true. Answers `file`, `project`, `matched_by`, `sent`, `version`, `who`, the name used, `sender`, the file's own, and `participants`, each `case`, `timepoint`, `already` and `boards`, each `from`, `name`, `statements`, `matched` (by words), `by_key`, `copy_words`, `kinds`, `came` (`came_counts`: `statements`, `as_sent`, `reworded`, `removed`, `own`), `as_sent` when it is the sender's own, and `not_matched`, each card not read the same with `key`, `to`, its key now, `text`, the copy's wording, `reason`, `kind`, `wording` (`yours`, linked, or `copy`) and, when linked, `now`, the project's wording. From a browser's file chooser it takes `data` and `name` in place of `file` (`sent_upload`). Each participant's answer carries `path`, its workbook as the page opens it. The board's note (`board_in_note`, copyback2, Adam's wording 2 of 8 November 2026) says whose copy, when it was sent and how its statements came from `came`, "Curt's copy, sent 30 Oct: 80 statements as sent, 37 reworded since, 5 removed since.", each count in its catalogue form and a clause left out when its count is 0, the file named in `origin` and History alone, then on the next line the board's own note in the copy as it was, when it has one. Home's Open a shared copy calls it for its card (`cbOpen` in distil.js, the card `#copy-back`, rebuilt 6 November): the dry run as the card opens, Name on the boards filled from its `sender`, and again as the name is typed, each participant's boards from `cbGroupsOf` with a tick each (`CB.off` the ones unticked, `#cb-all` for all of them), `cbLineSaid` once under them from their `not_matched`, the sender's own as sent left out of the list with `distil.copy.as_sent_left` under the participant (Adam's option A, 8 November 2026, the one way the card has), each statement counted once by its key, `#cb-as` the first ticked board's new name, the button `distil.copy.add_n` by the boards ticked, disabled with `#cb-need` beside it while no board is ticked or no name typed, then for real on Add with `boards` as `{participant, board, timepoint}` choices, landing on the first participant's PETs board with `thVmenu(true)`. Open as its own project goes on through `sentInto` to `/api/open-sent` with `from_name`. |
| `/api/send-list` | `root`, the project's id | What Share a copy's card draws itself from, read only (`send_list`, `project_pack.inventory`, one walk of the folder and the themes files read): `name`, `participants`, each `label`, `pets` (a board, a PET draft or a PET table), `audio`, `audio_bytes` and `audio_size`, then the whole project's `gets`, `audio`, `audio_bytes`, `audio_size`, `bytes`, `size`, `bytes_less_audio` and `size_less_audio`. A recording in `_Archive` counts in the whole project's alone. Each participant's `boards` and the whole project's `gets_boards` list every board file with its `kind`, its count of `boards` and the `current` one it goes with, which the card's Boards row reads. The demo is refused. |
| `/api/open-sent` | `file`, a sent file's path, or `data`, its contents in base64, or neither for the Mac's file dialog, `into`, the folder for the copy, or none for the Mac's folder dialog, and `check` | Open a shared copy, through `open_copy`: the file read by `project_pack.read_sent`, then the copy unpacked by `project_pack.unpack` into a new folder in `into`, its own name or with ` copy` after it (`copy_folder`), each file checked against the file's list, its project file marked `copy_of` by `mark_copy` (since 26 October with the shared project's `uid`, `sent`, `version` and `statements`, the project's own `uid` taken out so the copy takes its own at its first send), and added through `add_project`, answered with every project, `opened`, `folder`, `folder_name` and the `project`. `check` reads the file alone, `checked`, its `name` and `folder`, for the window, which then asks for the folder, the new folder's name in the dialog's line (`into_prompt` on the server, `intoSays` on the page), and since 26 October (boardsbackA, Adam's option A) `returning`, `{root, name}`, the project of his a copy coming back belongs to (`returning_said`, by `returning_to`), and, from the Mac's file dialog in a browser, the `file` chosen, so the page asks for the folder after with `file` alone. `data` comes with `name`, the file's own name, written to a folder of its own in the temporary folder under it (`sent_upload`) and taken away after. `from_name` names a copy coming back opened as its own project (`copy_named`). A newer `format`, a file that is no sent project, a path reaching out of the copy, a folder inside another project's root and a run with `--root` are refused with nothing written, and a failure after the unpacking takes the folder away. Either dialog cancelled answers `opened` false. |
| `/api/rename` | `op`, `plan` or `rename`, `root`, the project's id, `case`, the row's label, `name`, the new pseudonym, and `folder`, the tick | `plan`: `case`, `old`, `new`, `label`, `lines`, each file it writes, `folder_lines`, each folder and file it moves when ticked, and `folder`, nothing written. `rename`: the same and the case's new `label` as `case`, `old` and `path`, after it changes them (16 October). Refused in one line with nothing changed. |
| `/api/sift` | `folder` and `op` of `read`, `list` with `stage` and `round`, `decide` with `rec_id`, `stage`, `decision`, `reason` and `note`, `note`, `undo`, `field` with `rec_id`, `field` and `value`, `view` with `view`, `columns`, `filters`, `find` and `sidebar`, `cited_plan`, `cited` with `at`, `fill_plan`, `fill` with `at`, `study` with `act`, `rec_id` and `with`, `column` with `act`, `key`, `name`, `type` and `options`, `stamp`, `counts`, `export`, `included`, `reset` with `dry_run`, `pdf` with `rec_id`, `data` in base64 and `replace`, `ai`, `email` with `email`, `oa_plan`, `oa_find` with `rec_id`, `titles` with `stage`, and with the AI switch on `try` with `rec_id`, `stage` and `prompt`, `settings` with `ai_proposals` and `prompt`, `plan` with `stage` and `round`, and `propose` with `rec_id` and `stage`, and `second` with `act`, `draw`, `workbook` or `differences` with `stage`, `take` with `data` in base64 and `name`, or `outcome` with `rec_id`, `stage`, `outcome` and `decision` | Sift, through `sift.py`, `sift_oa.py`, `sift_ai.py` and `sift_second.py`, `read`, `decide`, `undo` and `second` each with `second`, the second screener's side blind both ways: `read` the whole screening with `prisma`, each record with its number, `config` with the AI switch, `ai`, the screening's AI settings or null with the switch off, `email`, and `review`, its review for the steps, put at the head of the list of reviews, the numbers of records without one written into sift.json, `ai` the screening's AI settings for Settings, under Sift, whatever the switch says, and only read, `email` the email saved, `oa_plan` the `ids` that passed title and abstract with no PDF, with `passed` and `have`, `oa_find` one record with `saved`, `skipped` or `said`, and with a PDF kept the record, `counts` and `prisma`, `titles` the `records` of the stage with each one's number and title, for the bench under Sift in Settings, only read, `try` the bench's answer, the decision, reason, grounds, `found`, `seconds` and `model_name`, nothing written, or a 502 with one line, `list` a round's `ids`, the three acts and `field` the record as it now stands with `counts`, `prisma` and `undo`, `view` and `column` the `table`, its view, columns, his own columns, filters and find boxes' words, `stamp` the files' times and sizes and the AI switch, `counts` the counts and their rows, `export` the counts file written, `included` the records included
at full text written as `screening.included.ris` and `screening.included.csv`, with `records`, `files`
and `written`, false with none included, `reset` the decisions and notes it clears and with `dry_run` false the screening started again and `archive`, the log's copy, `pdf` the record with `saved`, or `exists` and nothing written without `replace`, `settings` the screening's AI settings, `plan` the `ids` a proposal for the rows shown would ask about, those of `ids` when sent, and its `calls`, `cited_plan` the `ids` with a DOI, `of` and `records`, `cited` where the next fifty start, `at`, `of`, `asked` and `filled`, or `said`, `fill_plan` the same with `missing`, the records that lack one of Sift's own columns, `fill` as `cited` does for every one of them, `study` the record and every record it moved under `records`, with `counts` and `prisma`, `propose` the record with Sift's proposal written, or a 502 with one line. A screening whose review the list of reviews does not hold is refused, 403. |
| `/api/sift-search` | `folder` and `op` of `read`, `save` with `plan` and `reason`, `register` with `reason`, `works` with `text`, `key_works` with `rows`, `terms`, Check truncation's counts of the newest version with nothing written, `run` with `follows`, `progress`, `drop` with `source`, `name`, `data` in base64 and `run`, the run the screen shows, `runs`, `screening` with `date`, or `open` with `file` | Sift's searches, through `sift_search.py`: `read` the plan, its versions, each database's string, `problems`, `markdown`, the runs, `how` each database goes, `keys`, whether each key is set and never the key, `today`, a run under way, `catalog` and `review`, the review for its steps, put at the head of the list of reviews, `save` the plan kept, a draft of the next version when the newest is registered, `register` the newest version frozen with its `markdown`, `works` the works OpenAlex holds for a key work's DOI or title, to pick from, nothing written, `key_works` the review's key works kept beside the plan's versions, with the plan, `run` a run of the newest version started on its own thread into a new run folder, carrying the screening of `follows`, an earlier run's folder name, or none, `progress` its state and with it done the runs, `titles`, each benchmark DOI's title where the plan or a run knows it, which `read` sends too, and `review`, `drop` the export kept in the day's newest run folder and that run written afresh, with the runs, `titles` and `review`, `runs` the runs, each with `date`, its folder's name, `day`, `n` and `label`, `screening` a run's folder, `date`, for Sift to open, and `open` a file of the review's folder, `file`, `reasons` for `reasons.csv` or `plan` for `search_plan.md`, opened in the computer's own app for it through `OPEN_FILE`, nothing written. A review the list of reviews does not hold is refused, 403, and a review with no searches in one line. Every answer that draws the plan carries `plan_version`, the newest version's number and a hash of it, and a `save` or `reasons` that sends it as `seen` over a plan holding another version now, another window's save, is refused with 409, nothing written, and `stale`, the version now, which Overwrite sends back (19 October). |
| `/api/sift-review` | `op` of `folder` with `mode`, `new` or `open`, and `path` or none for the Mac's folder dialog, `new` with `folder`, `name` and `question`, `open` with `folder` and `name`, `read` with `folder`, `rename` with `folder`, `name` and `question`, `second` with `folder` and `second`, or `forget` with `folder` | Sift's reviews (see A review): `folder` the folder checked for Sift's New project or Open project folder, with the name the card fills in, or `chosen` false for a Cancel, and with `choices` for a folder holding several reviews, `new` the review made, its blank plan written and the review kept in the list, `open` the review kept in the list, its name when it is not its own, and nothing written into its folder, `read` a review the list holds, `rename` his name and question for it kept in its entry in the list, `second` its second screener settings kept there, and `forget` it taken out of the list, its folder left as it is, each of the two with `reviews`, the cards afresh. Each answers `review`, its folder, name, `question`, `searches`, the screening its Screening step opens and `opens`, that run's folder name, `run` and `label`. |
| `/api/trace` | `folder`, a Trace project the list holds, and `op` of `list`, `add` with `path` or none for the Mac's file dialog, `read` with `doc`, or none for the reference list alone, `judge` with `doc`, `claim` and `value`, Y, Q or N, `note` with `doc`, `claim` and `note`, `undo` with `doc`, `open` with `doc` and `ref`, `pdf` with `doc`, `ref` and `data` in base64, and with the AI switch on `plan` with `doc` and `ids` and `passages` with `doc` and `ref` | Trace, through `trace_claims.py`: `list` the manuscripts, the reference list and `choose`, `add` a manuscript read once and never written, `doc`, or a reference list, `list`, `chosen` false for a Cancel, `read` its rows, sections, `source`, Undo, `config` and `model_name`, the readable file brought up to it, each passage left out with the switch off, `judge`, `note` and `undo` the claim's `state`, its reference's `passages` and `undo`, `undone` for an undo, `open` the PDF opened in the computer's own app through `OPEN_FILE`, `pdf` a PDF kept in the project's pdfs/ never over one, `plan` the `ids` and `calls`, and `passages` the reference's passages, or a 502 with one line. A project the list does not hold is refused, 403. |
| `/api/trace-project` | `op` of `folder` with `mode` new or open and `path` or none for the Mac's folder dialog, `new` with `folder` and `name`, `open` with `folder` and `name`, `read`, `rename` with `folder` and `name`, and `forget` with `folder` | Trace's projects, as `/api/sift-review` is Sift's: `folder` the folder and the name the card fills in, `new` a project made in the folder or a new one inside it, `open` one that stands, Sift's `reference_check/` among them, kept in the list and nothing written, each answering `project`, its folder and name, `rename` his name kept in the list alone and `forget` the project out of the list, its folder and files left, each answering `traces`, the home screen's cards. |
| `/api/guidance` | nothing | The rail's lines, `framing`, the paragraph shown under them, the craft prompts, the default prompt and the examples' counts, and `ta`, a thematic analysis project's rail from `ta_guidance.md` in the same shape (`rail_of`). |
| `/api/suggest` | `turn`, `prior`, `time`, `name`, `path`, `quotes` | Key concepts and up to three candidate statements, with `quotes` counted when the turn's quotes went, or one line. Refused with the switch off. |
| `/api/haiku` | as `/api/suggest` | The same, under the name it had before. |
| `/api/suggest-sample` | nothing, or the four fields of a suggestion with the panel's settings | The bench's demo turn, or a suggestion on the turn sent. |
| `/api/models` | `fresh`, and from Settings (aipage, 8 November 2026) `provider`, `ai_address`, `local_url`, `lmstudio_url` and `ai_suggest`, the card's choice and its switch before Save | Anthropic's model list, Ollama's status (at the `local_url` sent) and the models chosen, and while an OpenAI-style provider is the one sent or saved, its list alone as `openai`, asked only with the switch on as saved or as sent. Each Anthropic model carries `name`, `hint` (name and price, the PETs list's label) and `price` (the price alone, the line `drawModelPrice` puts under the AI page's Model list, which lists names only). |
| `/api/key` | `key`, or `clear`, with `provider` and `ai_address` | `saved` or `cleared`, the provider's own keychain item, and never the key. |
| `/api/key-status` | `provider` and `ai_address`, or nothing for Anthropic's | Whether a key is stored, and where. |
| `/api/databases` | `op` of `read`, `key` with `service` and `key`, `clear` with `service`, `check` with `source`, or `save` with `rows` | Sift's databases under Sift in Settings, through `sift_search.py`: `read` his list, the catalogue and `saved`, whether each key is saved, `key` and `clear` a database's key stored in or removed from the keychain, answering `saved` or `cleared` and never the key, `check` one line, `said`, on whether the database took its key, and `save` the list written at once through `save_databases`, as a database's cog and Add database on Search strategy change it. Settings saves the list with the rest through `/api/settings`. |
| `/api/zotero` | `op` of `read`, `key` with `key`, `clear`, `check` with `settings`, `plan` with `folder`, `which` and `ids`, `sync` with the same, or `progress` with `folder` | Sift's sync to Zotero, through `sift_zotero.py`: `read` the library and ids under `zotero` and `saved`, whether the key is in the keychain, `key` and `clear` the key stored in or removed from the keychain under `ZOTERO_API_KEY`, answering `saved` or `cleared` and never the key, `check` one line, `said`, `plan` the preview, `adds`, `updates`, `leaves`, `pdfs`, `collection`, `collection_there` and `said`, nothing written, `which` `included`, the records included at full text, `filter`, the `ids` the table shows, or `all`, `sync` the sync started on a thread of its own, refused while one runs, and `progress` how far it has gone, `done` of `of`, and once it ends `result`, the counts and `said`, or `error`, one line. No answer carries a key, and the verbose log never logs its body. |
| `/api/feedback` | `text`, `contact`, `screen`, `agent` | The collector's row id, or one line saying why not. |
| `/api/mcp` | `path`, and `op` of `show` or `add` | The entry that runs the MCP server on this project, as `entry` and as `json`, `claude_code`, the one line for Claude Code, `desktop`, where Claude Desktop's settings file is, and `there`, whether it holds this entry already, then for `add` the entry written, with `backup` and `said`. A POST from the server's own page alone. |
| `/api/server` | for a POST, `op` of `restart` or `quit` | For a GET, `started`, `pid`, `restart` and `reopen`. For a POST from the server's own page alone, the same with `op`, then the restart or the quit (see Restart and Quit, under Running it). |
| `/api/beat` | none, or `gone` | `heard`. The beat every page sends about every thirty seconds, and its last word as it goes, each a sign of use, which every request is as well (see Quitting after the last tab, under Running it). |
| `/api/whats-new` | none | `versions`, each version's `version`, `date` and `lines` as `docs/whats-new.md` holds them, newest first, read beside the manual the window names, or none when this copy has no such file (see The updater and What's new, under Running it). |

Two paths outside the table answer a GET. `/audio?path=<workbook>&sheet=<name>` streams the
sheet's recording, with Range support so the player can seek. `/themes/print?workbook=<path>&board=<id>`
is the print view of a board, the book's table of Personal Experiential Themes as HTML that `themes_print.py` renders from the themes file, the
current board when `board` is empty, `auto=0` leaves the print dialog shut, and `note=1` puts the
board's note under the head (see Print in the [manual](manual.md)). `/sift/pdf?folder=<folder>&rec=<rec_id>`
is a record's PDF for Sift's pane, `pdfs/<rec_id>.pdf` beside the CSV of a screening whose review the
list of reviews holds and of a record its CSV holds, and nothing that resolves outside that folder.
`/trace/pdf?folder=<project>&doc=<doc>&ref=<key>` is a reference's PDF for Trace's pane, found as its table
finds it, in the project's pdfs/ or a screening's pdfs/ of a Sift project the list holds, and nothing from
anywhere else. `/gets/print?root=<path>&board=<id>&what=table|trail|all&auto=0` is the print
view of the GETs, HTML that `gets_print.py` renders from the GETs file as the screen would show it,
every case not yet in shown as it would come in, with `detail` of `full` or `selected`, `notes=1` to
bring participant notes in, which no export carries without it, and `get` for one GET's trail.
`root` must be the case root or the demo's folder, `workbook` stands in for it, and with neither it
is the case root. The trail reads the words of each turn it names from the workbook opened
read-only, and nothing is written (see Print, under GETs, in the [manual](manual.md)). Since 9 November
(typst3) the same views are Typst templates too, in `apps/idiograph/typst/`: `gets.typ` the main file, which
reads `gets_print.typst_data(...)`'s JSON from the string input `data` and sets the page, the head and the foot
(`gets-parts.typ`), then calls `gets-table(d)` (`gets-table.typ`) and `gets-trail(d)` (`gets-trail.typ`), each a
function a full set can `#import`. `typst_data` takes `page`'s arguments and reads the same walk (`walked`, with
`head_of` for the head and `foot_of` for the foot's pieces), so the HTML and the PDF cannot disagree about what
is on a board: the head, the foot in its pieces with the one to cut, every GET with its tint, count, rows or
blocks, and every word in the run's language. In the trail each row is a grid of its own, a gap two half-gaps
wide, and three rows (the strip down to the line's height, the rest of the nodes, the row's space), so a stub is
a strip cell's foot and an upright piece the edge between a gap's halves (`cell_data`, `spines`). A table's
row is never split unless it is taller than a page under the column heads, measured in the template, where it
flows as the browser's does. The column heads repeat on each page, a GET's bar and a participant's name stick
to their first row, and the foot cuts the project at a word to keep its three parts 6mm apart. The timecodes
are in the sans (Typst is given the two faces alone) and the nodes' corners are square. The HTML print view
links `/fonts/fonts.css` (`FONTS_CSS`, family/static/fonts/). Area 364. The canvas
print has no path of its own: `thCanvasPrint` in `themes.js` copies the canvas on screen, with the
page's own rules, into a tab it opens, and asks the server for nothing but a save still to go. The
copy shows every statement whole: `thCanvasMeasure` sets it off screen under `th-whole`, which lifts
the four-line clamp of `.th-text`, for each card's whole height, and `thCanvasWhole` runs the
canvas's own `thSettle` and `thLayout` with those heights on a copy of the board that `thSnap` takes,
so the canvas's board, `TH.sizes` and `TH.layout` are never written. The Table view of 19 October,
`#th-table` over the canvas, is drawn by `thTableDraw` from the board on the page, on a PETs board under
`.tb-titles`, the participant from `#th-case` through `thCanvasTitle` as `.tb-heading.tb-who-head` and the
table's name under it as `.tb-table-name` (20 October), the GETs board keeping its own heading: `thPlace` asks for it
on its next frame (`thTableSoon`) whenever it shows, and the canvas stays laid out under it, its world
hidden, so `thMeasure` and `TH.layout` hold while the table shows. `thTableTree` is its model, with no DOM:
the PETs in `gtCanvasOrder`, each label's items by `thThemeOrder`, coded as `pet_numbers` codes them. A
reorder, a grip's drop or Alt with an arrow, goes to `/api/board-order` (`thTableOrder`), which runs
`themes.reorder` on the board the page sends, the agents' `order`, and the places that come back land
through `thOrderLand` as one `thStep`. A move into another label first runs `thTableJoin`, the canvas's
`thJoin` and `thSettle`, then the same reorder, all one step. A rename is the canvas's Renamed a label
through `thDone`. The view each board shows is kept in localStorage under `idiograph-board-face`, by
screen, workbook or project, and board id. On the GETs board `gtTableFace` draws the GET table there, each
row's quote and `gtRowNoteHtml` under its items and Audit trail under each GET's title, the row's note
box kept with its caret through a draw. The GETs sidebar's own Table tab, `gtTableDraw` in `#th-bpanel`, went
on 19 October (Adam), `GT_TABS` losing `table`, and `thSideTableGone` turns a sidebar kept on it into the
Table view. Export's Print (Print table until 31 October) opens the print view with `auto=1`. Since 20 October (way 1, Adam) the
table works by the canvas's own code. Its rows carry `data-trow`, `data-tkind` (`label`, `statement`, or
`under` for a statement shown under its top) and `data-tparent`, and `thTableSelect` sets `TH.sel`, the
canvas's selection, through `thSelectOnly` and `thToggle`, with `TH.tanchor` for Shift's run over
`thTableFlat`, the rows in reading order. `thDrawSel` marks the rows (`thTableMarks`, `tb-sel`) and draws the
status bar, which leads with the count selected. `thKeyDown` in the table runs the canvas's own acts on that
selection: `thGroupKey`, `thDiscardKey`, `thDeleteKey`, `thInspectorKey`, `thNamesAsk`, and
`thTableStackKey`, which stacks under the first in table order. `thTitleOpen` opens a title in its row when
the table shows (`thTableTitleOpen`), and a fresh label's `TH.tedit` carries `before`, so its making and
title are one Made a theme through `thDone`. `thGroupKey` with nothing selected, and New group inside (`act:
'inside'` in `thMenuItems`, on GETs too since tableparity2), run `thNewEmpty`, which makes the label with `thMakeEmpty` where
`thEmptyAt` puts it: under its parent's body, below the whole board in the table so it reads last, or in the
middle of the view on the canvas. A right click or a row's ⋯ (`data-tmore`) opens `thMenuOpen` on the row's
item, and on GETs a case's name (`data-tcase`) opens `gtCaseMenu` with the GET, so `gtNoteNew` joins the new
note to it. A drag of a selected statement's grip carries every statement selected (`TH.tdrag.keys`,
`rows`). `thTableDropAt` answers `merge` over another label's `.tb-head` where `thMergeInto` allows it
(`thTableMerge`: statements through `thTableOrder` with `move.keys`, a label shifted with `thMoving` and
joined with `thJoin`, Joined and its title), `TH_TABLE_LOOSE` over Not placed (`thLeaveThemes`), or a body
and a place, where `thTablePut` sets several in at once (`thTableMovedAll`). `thTableJoin` joins a list,
one under another. `thTableBin` draws Binned and Missing from the workbook at the table's foot, with
`data-trestore` to `thPutBack` and `data-tremove` to `thRemove`. A stack's count is `data-tstack`, toggling
`thStackShow`, and an open stack's statements are drawn under their top. A double-click goes to
`thToPassage`, whose kept state carries `tscroll`, put back by `thBackFromPassage`. The palette stays over
the table at `z-index` 6, the table padded past it, and `#th-sticky` hidden there. In the GET table a
GET's sub-themes are rows of their own (`gtTableSubs`, `gtTableSubHtml`), `section.tb-label.tb-getsub` in a
`.tb-subs` at the top of the GET's body, nested for a group inside one, and `thTableFlat` lists them after
their GET. Their cards stay in the GET's case rows, each with its `within`, so a card is one row however deep
it sits, and a GET sub-theme's grip only merges, since a GET's cards read by case and have no order there. A
row of the Cases panel dragged over the table goes through the table's own pointer listeners, which pass
`TH.pull`'s moves and its let go to `gtPullMove` and `gtPullUp` before they stop them reaching the canvas.
`gtTableTargetAt` finds the innermost GET or sub-theme section under the pointer, or Not placed's `.tb-rest`,
`gtTableIntoShow` lights it (`tb-pullinto`), and `gtPullTableDrop` brings the card in or moves it, out of the
bin, through `thTableJoin` or `thLeave`, one `thDone` step, Brought a card in or Moved a card from the Cases
panel as the canvas's `gtPullDrop` names them. A row brought into view in the table (`thTableShow`, a title box opening) calls `thTableStageStill`, since
near the table's end the browser also scrolls `#th-stage` under it, shifting the palette and the status bar, and
In the Table view `.th-stage` is a size container (`tbstage`), so the table's quotes column (`--tb-q`, in
`cqw`), its one-column layout and the palette's place follow the stage's width rather than the window's: at
701 and wider the table pads 64 past the palette, at 700 and narrower the palette lies flat at the stage's foot
right (its inline place overridden, its grip hidden) and the table takes its whole width. A `mousedown`
listener on the table cancels the browser's word selection for Shift, Cmd and Ctrl clicks, right clicks and
double-clicks on a row. `thCorners` measures only the bar and bin that show, since the table hides the bin and
its top of 0 left the sidebar no height at a phone's width. `thFace` back to the canvas runs `thMapPlace` again, since a board opened in the table measured the map with
the status bar's tools hidden and drew it the stage's width. `/favicon.png` is the tab's icon
at 32 pixels, `favicon_png` drawing it once with make_app's `draw_icon` and keeping it, beside
`static/favicon.svg` (15 October). Every other
path is a file from `static/`, `index.html` for the root.

**Find and replace's reach (26 October, Adam's ruling of 24 October, "Everything follows").** One replace
serves the page and an agent alike, `routes.replace_in_case` over `workbook.replace_words`, which took
the place of `replace_transcript`: `/api/replace` calls it, and so do the command line's `transcript
replace` and MCP's `transcript_replace`. The words change wherever a row holds them, its transcript
(D), its statements (C), its quotes (F), its exploratory notes (E) and the interviewer's note, each
column found by `detect_columns` (`REPLACE_ROLES`). `find_spans` matches in every one alike. An
annotation cell changes an entry at a time, never across the blank line between two
(`_replaced_entries`): a "(no quote)" keeps its place untouched and an entry the replace would leave
empty keeps its words, so every statement keeps its card's key and every quote its pick's. `pairs` runs
several finds in turn over each cell, each on what the one before left. The one occurrence the page's
Replace names changes the transcript alone. The progress file's record of a row keeps `old` and `new`,
the transcript's, beside `cells`, each annotation cell changed with its old and its new text, and
`columns`, the count in each, and `put_back` writes them all back, or all again for a redo, after
checking every cell reads as the other text. With `mask` the record's `find` and `replace` read
"[match]", and an agent's replace carries `by`, `tool` and his `request` (`rounds.record_replace`). A
batch spanning several workbooks, `--all`, takes one id, so its undo finds every record by it.

Every other copy of the words is kept in step, by `follow_replace` after the workbook is saved and
under the same lock, and again the other way by the undo. Each board of the case, and every revision in
its history, takes the new words on each card of a statement that held the old, and each pick's quote
under `quoted` the same (`themes.cards_reworded`, one sheet at a time, so a timepoint's sheets reach
their own file). Each copy of the participant takes them on each statement's words, quotes and notes,
and each board's card of a statement (`gets.words_replaced`), through `statement_copies` and `copy_scope`
as an edit's copies are: the GETs file's, and in a project of two or more timepoints the participant's
LPETs, each timepoint's copy from `lpets_books`, then the LGETs (histreplace, 30 October 2026: until then
`follow_replace` asked the GETs file alone, outside any copy's scope, leaving the LPETs and the LGETs to
Take the changes, and `words_replaced` and `case_untouched` took the one case whose copy named the workbook,
which on LPETs, where every timepoint names the same workbook, would have found none).
`copies_before`, read under the lock before the workbook is written, says which copies stood as their files
did, and `gets.kept_in`, shared with `statements_followed`, reads each of those afresh and keeps the read's
`seen` when it hashes as the copy now does, so a replace alone never marks the participant Changed since it
came in. The answer gives each copy's keys by its kind, `gets`, `lpets` and `lgets`, and the command
line's lines and counts name each. The dry run writes nothing, as before. The search reads each file afresh
by its time and size, so it needs nothing. What stays as it was, on purpose: the PET drafts, tables and CSVs an export wrote, which the next
export writes again, the Word and PDF exports of a board, never written over unasked, an AI thread's
or review's words, `_Archive`'s copies, the raw source in `Source/`, which the `edits` records reconcile,
those records' own `old` words, which the undo needs. The page counts the occurrences in
the statements, quotes and notes it holds into `FIND.more` with `findSpans`, adds them to Replace all's
number, and takes each row's fields from the answer (`findApply`), the passage being worked on drawn
again unless he has typed in it since, when its version stays as he read it so his save meets the
stale card.

**The parity check (26 October).** Area 261 lists every route the page calls, each quoted `/api/...` in
`apps/idiograph/static/*.js` and `family/static/*.js`, and fails for any route in none of its three
lists. `AGENT_OPS`, the routes that work the project's data, each with the command line's ops that do
the same, each of which must be in `idiograph_cli.COMMANDS` (Search and opening a sent copy are run
before that table) and among the MCP server's tools. `PAGE_ONLY`, the routes that are the page's own
business, the window, its layout, the app's settings and keys, the app's own AI and the screen's own
aids, each with its one line. `KNOWN_GAPS`, the routes with no agent op today, each a next build. A
route named twice, a gap an op has closed and an entry no page calls any more fail it too, so a new
canvas action needs its op, or a line saying why it needs none, in the same build.

## The wipe utility

A command-line tool, deliberately not in the interface.

```
.venv/bin/python Tools/idiograph/wipe_draft.py \
    --workbook "<case>/P8 Wren - EN & ES.xlsx" \
    --sheet Initial --after-row 47 --all-sheets-except Initial --dry-run
```

It prints a table of every row it would clear. Drop `--dry-run` to write: the workbook is copied to
`_Archive/<stem> (pre-wipe <date>).xlsx` first, then columns C, E and F are cleared past the
boundary on the named sheet, and on every row of the other sheets when asked. The transcript column
and its highlights are never touched, and a workbook open in Excel is refused.

## Tests

```
.venv/bin/python tests/test_idiograph.py --changed
```

A build checks the areas its change touches with `--changed`, or the areas it names with `--area`,
once, at the end. The full suite runs in the coordinator's train, about four a day and one before the
hand-over, by `./verify` at the repository's root (18 October). From the app's folder in a downloaded copy,
`.venv\Scripts\python tests\test_idiograph.py` on Windows, and
`.venv/bin/python tests/test_idiograph.py` from the repo root. `.github/workflows/windows-installer.yml`
runs every area with Python 3.11 on GitHub's machines, before it builds the Windows installer. The checks print area by area, and the last lines give the time and count the passed, the failed and the skipped. The fixture is the demo case that ships with the app, Juno's,
built once per run from `demo/source/` as the demo shipped her until 26 October, statements on her
first six turns and the rest to do (`support.head_start`), since the demo itself now ships finished and
the checks that annotate, trim or assign need turns still to do. A demonstration left half finished
never changes what the suite reads, and the checks on the demo itself read `demo/pristine/`. The
round trip, the crux, the turn editor, the find and replace and its undo, the flags a progress file keeps from before, the trim and its undo, the assignments and their undo, the
wipe, the export, the progress file, the passed turns, the round back-fill through its endpoint and
the lock guard all run on a scratch copy of it, create-from-source builds its raw three-column
workbook from the demo transcript, and a second sheet is added to the scratch copy where a check is
about the sheet it was not pointed at. The whole suite passes on a machine with no GRAVITY data on
it at all.

Each area of checks is a file of its own under `tests/areas/` (17 October), named by its place in
the order and a short name, `a158_guidance_sheet.py` holding `test_guidance_sheet` and any helper no
other area uses. `tests/areas/support.py` holds what more than one area uses: the paths, the check
counter, `check` and `skip`, the demo fixture and the shared helpers and constants. An area reads a
file of the app by its path as it is now, `support.source("family/static/shell.js")`, a Path, or
`support.text(...)`, the text of one or several paths joined, app.js being `support.APP_JS`, the shell and
`distil.js`. From the family codebase's first build (22 October) to its sixth (23 October 2026) the suite's alias
table, `support.ALIASES`, took each path an area named from before the family's folders to where the file was,
which `--changed` read backwards. `support.code_files("*.py")` is every module in the root, `family/` and the
apps' folders, and `support.static_folders()` every static/ folder of the page. `support.page_text()` is
Idiograph's page as its server serves it, `page_text(app="sift")` Sift's, and `support.every_page()` the
family's page with every app's parts, for a check over all three apps' markup at once. `support.as_app(app)`, a
context or a decorator, runs the suite's server and command line as Sift or Trace in this process.
`tests/test_idiograph.py` keeps the order, `AREAS`, loads each area as its turn comes, chooses the
areas for `--changed`, and stays the one file the gate's `unittest discover` and GitHub's run call.
`--area 158` runs one area alone, `--area 157,158` or `--area 150-152` several, and `--area guidance`
every area whose file name holds the word. `--changed` takes every file of the app that differs from
where the branch left main, committed, staged, in the working tree and new, and chooses every area
whose source names one of those files or a top-level name the change touches: a function, class or
constant whose lines changed in a script or a Python file, a class, id or custom property of a rule
that changed in a style sheet, an id or class on a line that changed in a page. Every new area and
every area whose own file changed is chosen too, and a name more than `COMMON` areas carry, 20, such
as `app.js` or a class called `card`, chooses nothing. `choose_changed` makes the choice from the
files' texts and diffs alone, and `changed_areas` asks git for them, or says it cannot where there is
no git or no main. Every area runs in a train alone, as `train_reason` says: `--train`,
`IDIOGRAPH_TRAIN=1`, which `./verify` sets for the gate's run, or GitHub's `GITHUB_ACTIONS=true`.
Anywhere else the file with no `--area` or `--changed` prints `REFUSAL`, one line naming
`--changed`, and exits 2 without running, and `ESHelperChecks` skips itself with the same line, so
`unittest discover` runs nothing either. Each area's seconds and count of checks go to `TIMINGS` as
it ends, a full run lists the 15 slowest at its end, and `--timings <file>` writes them all, slowest
first. Area 189 holds the refusal, the three ways a full run goes ahead and `--changed`'s choice on
an invented change in a repository of its own. A new area is a new file under `tests/areas/` and its line at the end of `AREAS`, as
`tests/README.md` says. After the areas every run checks that each file under `tests/areas/` is in
`AREAS` and each name there a file, and compiles every Python file of the app with Python 3.11, the
oldest it runs on and the one GitHub's Windows run uses, when the machine has one, and says it
skipped that when it has none.

**The local gate file (21 October).** What names the maintainer's own studies stays out of the public
tree, in a JSON file on the maintainer's Mac that the suite (`tests/areas/support.py`) and `./verify`
read when it is there: `~/.config/idiograph/gate.local.json`, or the file `IDIOGRAPH_GATE_LOCAL` names.
Its keys: `academy`, the folder holding the real data (`IDIOGRAPH_ACADEMY` wins over it), and under it
`main_data` (the cases), `corpus` (the statements corpus) and `participants` (a study's transcripts),
`reference_workbook`, `reference_export` and `reference_source`, each a list of a case folder's prefix
and the parts of a path inside it (the export's beside the workbook), `study_pseudonyms`, the names no
shipped file may carry, and for the gate alone `register`, `name_scan` and `case_study_dir`, the
real-name scan's register and script and the folder `--docs` reports on, and `forbidden_names`,
patterns no tracked file may match, `words_sources`, a list of folders under `academy` whose case
folders the participants'-words scan reads beside `main_data`'s, and `interviewer`, the speaker or
speakers (a name or a list) whose turns it leaves out. With no file, as on GitHub's machines and in a contributor's
copy, every check that needs real data skips, the gate's forbidden-name and real-name scans say in
one line that they skipped, and nothing else changes. `name_scan` is an absolute path or one under
`academy`: the script stays in the study folder beside its register, and the gate runs it over the
snapshot, every tracked file of this tree.

**Participants' words (10 November).** Before the repository went public a check was found using a
participant's spoken lines as its invented fixture, and another a PET title of the maintainer's for a
real participant. So `./verify` refuses RED with `reason=participant-words` a tree in which any
tracked or staged file holds eight words running from a participant's words
(`check_participant_words`). The words are every case folder's under `main_data` and under each folder
of `words_sources` (a folder starting with `_` or `.` left out, so an `_Archive`'s older copies): each
workbook's and CSV's turns, but the interviewer's, its statements, its quotes, another speaker's words
and the PET column of a PETs table, found by their headings as the app finds them, and each board
file's titles, descriptions, statements and notes. The workbooks are opened read-only. A run in three
cases or more is everyday speech and dropped. Words are compared in lower case, apostrophes dropped and
punctuation set aside. The tree is read whole, JSON, code and scripts among it, and its workbooks and
Word files by their text parts, pictures and fonts passed over. A hit names the file and how many runs,
never the words or the case. The runs are kept as 64-bit hashes in `.verify/participant-words.bin`,
keyed on the sources' sizes and times, and each file's count by its content in
`.verify/participant-words-files.json`, so neither holds a word and a run with nothing changed reads no
workbook. The full gate reads the sources when they changed. The fast gate and `./commit` take the
cache alone, and skip, saying so, when the sources changed since it was made. With no data reachable
the scan skips and says so. Area 372 runs it over invented workbooks and an invented tree.

**Conflict markers (26 October).** Train 55 passed with a 3-way apply's markers left in
`tests/README.md`, so `./verify`, the fast gate too, refuses RED with `reason=conflict-markers` and
names each file and its lines when a tracked or staged file holds all three kinds of marker line, an
opener of seven `<` and a space, a divider of seven `=` alone and a closer of seven `>` and a space,
each at a line's start (`check_conflict_markers`). One kind alone, a Markdown rule of seven `=` under a
heading, never refuses. Every file is read but the binary kinds of `CONFLICT_SKIP_SUFFIXES`, code,
styles and scripts among them. Area 271 runs the check over an invented tree.

**GitHub's checks (21 October, a push to main dropped 23 October).** The workflow runs the suite on
Windows, a Mac and Linux on every pull request, on Windows before a tag's installers, and on Windows
and, when asked, a Mac by hand. A push to main runs nothing on GitHub: a release ran twice, the tag's
run and the push's, the push's mostly repeating the tag's, and Actions minutes come from a hard monthly
budget. The full gate on the maintainer's Mac checks every commit to main instead. A pull request runs as `pull_request`, never `pull_request_target`, so a fork's run
has a read-only token and no secret. The Linux job adds what of `./verify` needs no real data:
`py_compile` over every tracked `.py`, `node --check` over every script in `static/`, and the
case-folder rule. `./verify` itself stays on the Mac, since its snapshot takes APFS clones and it
waits its turn in the Mac's heavy queue.

The reference workbook and a raw source from the transcription pipeline add coverage when they are
there, and report a skip when they are not. They carry the same round trip over three sheets and
2,640 cells, the headers and widths the app writes checked against the workbook they were taken
from, four rounds over 123 turns, the examples panel drawing on a finished GRAVITY set, and the
export compared line for line with the reference CSV. A machine without them reports six skips and
nothing else.

The shipped folder is checked as someone else might receive it. No file in `static/`, nor
`ai_suggest.py`, `themes_ai.py`, `themes_print.py`, `corpus.py`, `guidance.md` or `pet_guidance.md`, may name a pseudonym from the maintainer's studies, and nor may the
README, the manual or these notes. The names come from the local gate file, so with none the check skips. None of those files may carry a
statement from the corpus or a case workbook, or eight words running from any turn of a case
workbook or a study's transcript, all of them opened read-only, and the part with nothing to
read on a machine reports a skip.

The look is checked as well (15 October). Area 147, `colour_problems`, fails on a colour written in a
stylesheet outside a token block, in the page's markup or in a script's style string, three allowed
with their reasons, on a `var(--name)` that no stylesheet, script or page defines, on the two dark
blocks of `tokens.css`, `themes.css` or `sift.css` disagreeing, on an ink under 4.5 to 1 on paper,
card or sunk paper, on a row of `docs/design.md`'s token tables that disagrees with `tokens.css`, and
on more distinct font sizes or radii than its two counts, which may only fall. The meanings that colour
words, the crux orange, the accent, Supports' green, the amber, the red and the excerpt's blue, are held
to the same 4.5 to 1. Since 16 October it holds the cases' palette of the GETs board too,
`case_palette_problems` over `themes.css` and `tokens.css` (area 239 calls it since 21 October): `--th-case0` on, 25 in light and
dark alike, the first eight held to `CASE_APART` between any two and all 25 to `CASE_NEIGHBOURS` between
neighbours in the picker's order and its grid of five and `CASE_ALL_25` between any two, each at 4.5 to 1 on paper, card and sunk paper as a badge's ground under the card's colour,
a colour distance of 12 or more between any two and 6 or more under each colour blindness, 15 or more
from every judgement's colour, the crux orange among them, and no hue below 75 degrees of OKLCH or
above 345, from red to amber, a crux orange planted in a copy found. Area 148, `identity`, holds the marks (15 October): the four symbols of
`static/marks.svg` and each one used, the part's class on the home screen's sections, every title bar
and Settings' part tabs, the parts' colours at 4.5 to 1 in both themes, the dark crux's distance
from the amber, the favicons served, and `draw_icon` drawing the mark at 1024, 128, 32 and 16. Since
later that day it holds too each part's colour at about 7 to 1 on paper in both themes, within six
degrees of the board's hue, apart from the others in plain sight and under protanopia, deuteranopia
and tritanopia, after Machado, Oliveira and Fernandes (2009), and far from the judgements' colours,
each part's mark drawn again for 16 and 18 pixels with every edge on a whole pixel, the bars and
Settings calling those, every bar's mark 7px from its name through `--rail-gap`, the name shown after
it at every width and never the part's word, Idiograph's mark before its first tab where Settings' tabs
make a row, its name in the list's own case, and each label over its field below 480px. At the day's
finish it holds the three within a tenth of 7 to 1 on paper in both themes, `WAS_PARTS` keeping the
values before, the home screen's own drawings for 20 pixels, `#distil-20` and the others, each line
two pixels, the first row of the bars of Sift, its searches and Trace 11px from the top below 760px,
Sift's row of project names in Settings under its name over Databases, as Trace's, hidden by
`sfaReset` with its block, and the player's note, alone with no recording, taking the row and wrapping.
Area 145, `trace`, holds the two of that finish in Trace, the never cited heading wrapping, `.tr-said.sf-blank`,
and the empty project's typed path, the toolbar's box at Add file's height in a block the screen's width.
Area 149, `part_order`, holds the three parts in the order a study does them (15 October, later),
Sift, Idiograph and Trace, on the home screen, in Settings' list and the order its arrow keys walk, on
`/design`'s colours, marks, title bars and tabs, Idiograph's name and one of its tabs now standing there
between Sift's and Trace's as in Settings, in the openings of the README, the manual and the agents'
guide, in the skill's description and the command line's help, and in the MCP server's line on its
tools, each section, tab, key and route keeping its old name.
Area 150, `rounds_and_passages`, holds Work in rounds, off on a new install, an absent key off,
saved and read back, the page with it off drawing no round count, clock, marker, target, streak or
days and the sheet-end and case-end cards still coming, with it on everything as before, the bar's
place "Juno, passage 8 of 120", and `index.html` and the manual naming the unit passage.
Area 161, `screens_sweep`, holds the sweep of 17 October over the first screen, a project's page,
Settings, Sift's steps and Trace, each break measured in a headless browser's shots of invented data:
the key beside a decision's word, `.sf-act .mono`, and Enter on Accept suggestion, `.sf-take .mono`,
whole, in the word's own colour by `color: inherit` over the faint ink of `:where(button) .mono` since 17 October, later, each decision's colour reaching 4.5 to 1 on its wash at rest, under the pointer and
pressed in both themes, computed from `tokens.css` and the washes `sift.css` writes, Maybe's wash
under the pointer a tenth of its amber on both, the one taken keeping its fill, a range's count of
none unfaded, the ticks of Search strategy and Set columns given the ink by `accent-color`, and the
placeholders of a key's field, a setting's field and Set columns' fields given `--ink-faint`.
Area 161 since 17 October, later, holds every key hint on a button in a token's colour and never an
opacity, `:where(button) .mono` in `--ink-faint` at a class's weight so `.sf-n` and `.sf-rc` keep their own,
the time on Back to where I was taking it since `.back-to-turn .mono` went (area 166), the time on Quotes to pair in the ink and a reason's number in the soft ink
under their washes, computed from `tokens.css`, Mark as registered's radios, Set up the form's ticks and the
form's own given the ink by `accent-color`, and no tick outside `sift.css` in the crux, the study's cases in
Settings and Include participant notes on the GETs print card among them, the crux orange off them.

The Export menu and the GETs print card in literal words (31 October 2026, exportcards, Adam: "whatever it does it
should name that"). `#th-xmenu` runs Print and Save as PDF (`data-xop` `print` and `pdf`), a `.row-menu-rule`, Canvas
on one page, Word, and Markdown and CSV (`canvas`, `word`, `export`), a rule, the five ticks, each with a tooltip of
what it puts on the page, and PET labels. On the GETs print card, `#gt-print-what` and `#gt-print-detail` are each a
list of `label.gt-choice` rows, a radio and its name with a `.gt-choice-line` under it in the soft ink, the row's
`data-what` or `data-detail` what the card's click reads as before, and `gtPrintDraw` sets each radio's `checked` from
`TH.printing`. A `.gt-print-head` names each list, What to print and Under each participant. The card is 720px wide
at most, so at 1280 each line stays on one, and wraps in a narrower window. The values the API takes, `what`
(`table`, `trail`, `all`, `canvas`), `detail` (`full`, `selected`) and `for_sending`, are unchanged.

Export follows the view, and the canvas as a PDF or an image (1 November 2026, exportA, Adam's way A of exportdesign's
drawings: "I always switch to the table view if I want to print or export the table", and "Canvas should give both a
PDF and an image"). `#th-xmenu` holds two parts, `.th-xpart[data-xpart]`, each under a `.th-xhead` in the soft ink,
and `thXmenu` shows the one for `TH.face`: `table`, The table, with Print, Save as PDF, Microsoft Word and Markdown and
CSV (`data-xop` `print`, `pdf`, `word`, `export`), the ticks and PET labels, and `canvas`, The canvas, with Print,
Save as PDF and Save as an image (`canvas`, `cpdf`, `cpng`) and no ticks. Canvas on one page's string is gone. The
canvas's page is made by the page, `thCanvasMade` (the copy `thCanvasPrint` writes into its tab), and with `image`
`thCanvasPage` marks its root `cp-image`, which lays the page out at the canvas's own size, `.cp-page` the canvas's
width and 48px, `--s` 1, no shadow, no Print, on white, for its picture. Its script runs in a function of its own,
since a page written over the app's own keeps the app's globals, and once its faces are in it marks its root
`data-canvas-ready`. `thCanvasOut(kind)` sends the page to the server, `/api/themes-export` or `/api/gets-boards` with
`op` `canvas`, `kind` `pdf` or `png` and `html` (until typst5, 9 November 2026, which draws the canvas with Typst from the board and
took the held page, the window's picture and the agents' browser away), which holds it (`canvas_out.hold`, ten minutes, twelve at most) and
serves it at `/themes/canvas?id=` (`canvas_out.page_view`), and names the file where the table's PDF goes,
`canvas_out.place` with `stem_of` the table's title and " canvas": beside the workbook (`themes_canvas`), at the
project's root for the GETs (`gets_canvas`), beside a participant's workbook for their LPETs, the date and time added
when a file has the name, `margins` the page's 10mm. In the window `idiographSavePdf` prints the held page to the PDF
as the table's (`save_pdf`, A4 landscape, the foot reader finding no foot), and `idiographSavePng`, window.js, asks the
new command `save_png` (build.rs, the capability's `allow-save-png`), which loads the held page in a hidden window
of its own and pictures it whole. On a Mac (`picture_page`, `mac::page_size`, `mac::picture`) the page is asked its
`.cp-page` size until it is ready, the window made that size (8192 points at most), and WKWebView's
`takeSnapshotWithConfiguration:` taken of that rect with `snapshotWidth` the width times `PNG_SCALE`, 2, over the
window's backing scale, so the PNG is twice the page's pixels on any screen, written through `NSBitmapImageRep`. On
Windows `picture_page` calls WebView2's `CallDevToolsProtocolMethod`, `Runtime.evaluate` for the size once the faces
are in and `Page.captureScreenshot` with `captureBeyondViewport` and a clip at scale 2, its base64 written as the file.
That code follows WebView2's documentation and has not been compiled or run: the Windows window is built only by the
release. In a browser's tab Save as PDF opens the canvas's Print, and Save as an image sends `make` with
`location.origin`, and the server has a headless browser picture its own held page from that loopback address
(`canvas_out.shoot_held`) and writes it (`canvas_out.write`, a `.part` file only for `replace`, else never over a file
there). The line after is `thExported`'s, Show in Finder on a Mac, `themes_reveal` taking a PNG beside the workbook. On
the GETs print card `#gt-print-png`, Save as an image, shows with Canvas on one page, and Save as PDF stays for it,
`gtPdfGo` and `gtPngGo` going to `thCanvasOut` with Include participant notes. The agents' `board export --canvas` and
`gets export --canvas` (`board_canvas`, `gets_canvas` in idiograph_cli.py, MCP's `canvas`) name the same files and
make them with the app's own page: `canvas_out.agent_shot` starts the app's server for the one project
(`server_command`, the frozen executable's `--serve` or the repository's server.py, `--root`, a settings file of the
run's own from `run_settings`, `IDIOGRAPH_STAY_OPEN`), and opens `/#open=` with the board's spot and `shot` in a
headless browser. shell.js's `spotOpened` sets `window.__idiographShot`, `thSaveOnce` saves nothing while it is set,
and `themesOpen` ends in `thShot`, which writes the canvas page over the app's once the faces are in, or says `empty`,
and a board that will not open says `gone` (`comeBack`). `canvas_out.browser_page` drives the browser through its
DevTools protocol over a WebSocket of the standard library's own (`Cdp`), waits for `data-canvas-ready`, then
`Page.printToPDF` on A4 landscape by the page's own rules, or `Emulation.setDeviceMetricsOverride` at the page's size
and device scale 2 and `Page.captureScreenshot`. Juno's Board 1: 6532 by 5678 pixels, 2.0 MB, in about three seconds.
Area 313 holds the routes' names, the held page, the server's picture, `thCanvasOut` in node and, with a browser, a
page wider than its window pictured whole at twice its size and an agent's real PNG.
**PDF and image on Linux** (linux4, 9 November 2026, build 4 of the Linux plan, gone the same day with typst5: every
computer now asks the server, which makes the file with Typst, see Every export through Typst). The Linux window has no print or
picture of its own (`print_to_pdf` and `picture_page` in main.rs still answer "no PDF here" and "no picture here",
and nothing calls them there), and the plan's WebKitGTK print was not written, since it could not be compiled or run
off a Linux desktop. window.js sets `idiographByServer` when the system is neither "macos" nor "windows" (the Linux
window's `__IDIOGRAPH_OS__` is "other") and a window is there, and themes.js's `thWindowSave`, used by `thPdf`,
`thCanvasOut` and `gtPdfGo` in place of calling `idiographSavePdf` and `idiographSavePng`, then posts `/api/page-file`
(`api_page_file`, post-only and window-only) with `kind`, the page's path and query, the path the server named and
`location.origin`. `canvas_out.save_page` takes only a loopback origin and a page that is a print view
(`/themes/print`, `/gets/print`) or the held canvas page, a path ending as the kind does in a folder there, not a link,
and with no browser (`print_pdf.browser`, the same lookup, the Linux names `google-chrome`, `chromium` and the rest on
the path, or `IDIOGRAPH_PDF_BROWSER`) answers `server.page_file_no_browser` in plain words. A canvas page and any
picture go through `browser_page` (`Page.printToPDF`, `Page.captureScreenshot` at scale 2), a print view is fetched
from the server's own address and printed by `print_pdf.render`, and the file is written as a `.part` file then put in
place, over one there as the window's own save does. A failure's text shows in place of "The PDF was not saved." (`err.said`).
Area 354 holds it on a faked platform and a stub browser. What only a real Linux run proves: Chrome or Chromium
starting headless under a snap or a distribution's sandbox, a print view's margin boxes and page foot as that browser
draws them, a canvas pictured whole at twice its size, and the line after (`thExported`) with no Show in Finder
button on a desktop without xdg-open.
**The canvas in Typst** (typst4, 9 November 2026, Adam, 9 November about 18:10: Typst the one engine, no fallback).
The canvas's PDF and picture are drawn from the board's saved layout alone, with no window, so the command line and
MCP can make them as the app does. `canvas_out.typst_data(state, heading, gets=, lgets=, lpets=, notes=, quotes=,
image=)` reads the screen's own answer for the board (`themes.state` on PETs and LPETs, `gets.state` on GETs,
`pets_data` and `gets_data` read them) and gives the template what the canvas draws: each card on the canvas (not set
aside, not stacked under a top, not waiting in Not placed) where the file keeps it, with its words, timecode, a later
sheet's tag, missing or changed, its tint (`tints_of`, thTints carried over), a top's count and edges, the reason an
AI left it out and, with `quotes`, its quote, each label with its members, description, note and picks marks and its
badge, on GETs "n of total" and `under` past the minimum (`_gets_count`), each sticky note, and on GETs each card's
case colour and badge, kicker, a PET's description and count and what it names (`_gets_card`, `_gets_from`, gtCardHtml
carried over). A participant note is laid out but drawn only with `notes`, as the copy removes it after measuring.
Every word comes in the data from the catalogue. `apps/idiograph/typst/canvas.typ` holds the view, `canvas(d)`, and
`canvas-main.typ` reads `sys.inputs.data` and sets the page: in the PDF a landscape A4 page, 10mm margins, one canvas
pixel 0.75pt as a browser prints it, the board scaled to the room under the title and never past its own size, and in the
picture (`image`) one pixel a point, the page the board's width and 48 with the title over it, rendered at 144 ppi so
it is twice the canvas's size as before. The template measures every part itself: each card as the screen shows it
(the statement four lines at most, a top's stack count in its foot) and whole, each label at 340px or, with a
description over a wider body, that body's width (thLabelsWiden), its hidden Arrange and Delete counted in, each note
and each frame's badge, every line its CSS line-height, the glyphs set with the browser's half-leading from each
face's ascent and descent. Then it lays the board out by the app's own rule, carried whole from themes.js: thLayout
(each label above what it holds, its frame round them), thCanvasWhole (each card taller whole than on screen taking
its whole height in reading order), thSettle with `stay` (what it comes inside the margin of shifting clear by
thFreeOffset's search, the same binary heap and the same order, a theme with all it holds, for eight passes, a card
in no theme left in a frame joining it), thReadOrder and thBadgeSpots, with JavaScript's half-up rounding. The page's
box is thCanvasBox's, 24px round everything drawn. It records its layout as `metadata` under `<canvas-layout>`
(frames, screen and whole sizes, places, box), which area 365 reads. Drawn: frames in their tint's wash and line,
badges, labels with their dot, underline, description and the note and quote marks (`typst/marks/`, recoloured per
tint), cards in their wash with their left rule, a top's paper edges and the plus past four, the foot's timecode in
Nunito Sans with tabular figures, sheet tag and marks, missing cards faded and dashed, sticky notes on their paper, and
on GETs the case's colour along each card's top, its badge (grown by the print's scale as gtBadgeUp grows it) and
kicker. Not drawn: drop shadows (cards, notes and labels are flat), the close pairs' lines, a stack shown open and a
GETs card unfolded (the print draws them shut and folded, as the canvas page did), the handwriting face (a note is set
in Nunito Sans italic), and the room thMakeRoom makes on opening a board whose words now take more room. A thematic
analysis project's code cards are drawn as statement cards. `canvas_out.typeset_canvas(data, kind)` hands the data to
`typeset.render`, the PDF or the picture's one page. Wiring Export, Save as an image and the agents' exports to it is
typst5's (below). Area 365 holds the frames the template sizes equal to the app's rule run in node on the same sizes, on an
invented board with every part, every card's, label's and note's words on the page, the picture's width following the
board, and the demo's PETs and GETs boards made without a window.
**Every export through Typst, the old routes gone** (typst5, 9 November 2026, Adam about 18:10: Typst for every PDF
and picture, "it should work or error", no fallback). The server makes every PDF and picture, for the window on every
system, a browser's tab, the command line and MCP alike, through `typeset.render`, and writes it where it went before
under the same name. Export as PDF of the table of PETs: the page posts `/api/themes-export` with `op` `pdf`, the
ticks and the timepoint, and `themes_pdf_place` writes it through `print_pdf.write` (`themes_print.typst_data` into
`pets_table_main.typ`, the project's research question, name and Your name in it), answering `pdf`, `shown`, `path`,
`name`, `dated`, `version` and `labels`, `margins` gone. A GETs view's Save as PDF: `/api/gets-boards` with `op` `pdf`,
`gets_pdf_place`, `print_pdf.write_gets`, `gets_print.typst_data` into `gets.typ` for the GET table, the audit trail
and thematic analysis's Theme table, and for `all` into `gets-all.typ`, the full set as the HTML orders it: the head
and the contents (`contents`, its parts and each participant and GET by name), each participant's table of PETs from
a page of its own (`pet_data`, from `pet_tops`, the walk `pet_section` reads too, drawn by pets_table.typ's
`pets-blocks`, which `pets-table` now calls as well), then the GET table and the trail, each part under its heading
from a new page. The canvas's Save as PDF and Save as an image: the same routes with `op` `canvas`, `kind` and
`quotes` (Quotes on cards as the canvas shows it, the settings' when none is sent), `notes` on GETs, the board read
afresh (`canvas_out.pets_data`, `gets_data` in the request's scope, so a timepoint's board, a participant's LPETs and
the LGETs come as the screen reads them), Close pairs from the settings on PETs (`close_of`), typeset and written by
`canvas_written` (`canvas_out.made`), answering the place, `shown`, `bytes` and a picture's `pixels`. A board with
nothing on it is refused (`server.canvas_empty`). Each route takes `dry_run`, which names the file and makes and
writes nothing. The command line's `board export --pdf` and `--canvas`, `gets export` and `--canvas` (with
`--lpets` too since typst5, a participant's LPETs canvas beside their workbook, `LPETS_FOR` naming the workbook in
the LPETs scope) and MCP's `board_export` and `gets_export` call the same functions. When Typst fails,
`typeset.Failed`'s plain sentence becomes the refusal (`print_pdf.typeset_pdf`, `canvas_out.typeset_canvas`), the
page's line at the foot shows it, the command line exits with it and MCP answers it as an error, and since each file is
made before it is opened nothing is written.

Removed, no fallback: `print_pdf.browser`, `render`, `margins_of` and the browsers' names. From `canvas_out` its held page
(`hold`, `held`, `href_of`, `page_view`, `PAGE_PATH`, `/themes/canvas`), its headless browser (`Cdp`, `browser_page`,
`shoot_held`, `active_port`, `remove_profile`), Linux's `save_page` and `/api/page-file`, and the agents' shot
(`agent_shot`, `server_command`, `run_settings`, `free_port`), with shell.js's `__idiographShot`, themes.js's
`thShot`, `thWindowSave` and the canvas page's picture mode (`cp-image`, `data-canvas-ready`). From the window its
`save_pdf` (the Mac's `mac::print` with a save to a file for Export, WebView2's `PrintToPdf`) and `save_png`
(`picture_page` on the Mac and Windows, `mac::page_size`, `mac::picture`, `PNG_SCALE`), their commands in build.rs
and the capability, and window.js's `idiographSavePdf`, `idiographSavePng` and `idiographByServer`. `mac::print` no
longer takes `done`, which only Export's print-to-file told. Print on paper is as it was: `print`, the Mac's
`mac::print` with `draw_border` and its foot, a check's `IDIOGRAPH_WINDOW_PRINT_TO`, Linux's print dialog and
Windows's own print. The suite's browser checks find their Chrome through `support.browser()`, the lookup that was
`print_pdf.browser`, and `support.typeset_words` stands in for `print_pdf.typeset_pdf` where a check reads a PDF's
words. typst4's gaps closed in canvas.typ: a clamped line (a label's description past six lines, a GETs card's
description past two, an AI's reason past two, a short quote past three) cut at a word with "…" (`clamp`), the close
pairs' lines while Close pairs is on (`link-path`, thLinkPath carried over, drawn where the cards stand once laid out
whole, over the frames and under the cards, their dots over the cards), and a thematic analysis project's code drawn
as its code's card (`whos-rows`, Code with its extracts, the name, each participant's letter and count, no
participant's colour along its top). Area 367 holds the wiring, the full set's order, a failing engine's sentence with
nothing written, the LPETs and LGETs on an invented timepoints project, the gaps, and the old routes' absence.
The same night's fixes stand in their own areas. Area 145 holds Trace's shortcuts card naming Undo's key
through `keyName`, and area 98 Sift's card run through it at `sfBoot`, and `ground_spans` in `sift.py`
setting case aside through `case_free`, one character for one so the offsets hold, and `reasons` offering
an exclude's bare reason alone. Area 111 holds Add PDF once, in the record's links, the empty pane's
`#sf-nopdf` saying No PDF. alone. Area 138 holds `sfPropReasonHtml`, a code on an exclude its red pill and
any other reason a sentence in `.sf-prop-why` that wraps. Area 115 holds a ticked filter row of none
unfaded, `.sf-choice.zero` faint only under `:has(input:disabled)`. Area 103 holds the unlit stars an
outline in `--ink-faint` by `-webkit-text-stroke`. Area 122 holds `rvStepsSeps` in `sift_search.js`,
which hides a chevron that ends a wrapped line of the steps and takes out one that starts a line, measured
again by a `ResizeObserver` as the row changes width. Area 123 holds New run's line empty and hidden while
the plan names no database. Area 57 holds `.keys td + td` wrapping. Area 157 holds the Cases panel's one
No PETs yet, and area 52 the bin's count hidden at nought on both boards, `#th-pile-count` hidden in the
page until the first count.
The rule breaks the screenshot check of that night's fixes found, measured as it measured them, the
strongest pixel of the text against its box's commonest colour in shots at 1280 and 360, light and dark,
stand in their areas too. Area 139 holds H after Key excerpts, `.sf-ex-key`, in `--ink-soft` at weight
500, the decisions' keys' weight, at least 4.7 to 1 in light and 5.6 in dark wherever its strokes fall on
the pixels, where `--ink-faint` read 2.8 and 3.0. Area 52 holds `.th-names-row`, and `.th-bin-word` in
`--ink-soft` at rest, the empty bin's drawing alone in `--ink-faint`, 5.2 and 5.7 to 1 where it read 3.65,
and `.th-pile-count` never fainter than `--ink-soft`. Area 115 holds every choice of Sift's filters wrapping,
`.sf-cw` at `white-space: normal` and `overflow-wrap: anywhere`, the box, a dot and `.sf-cn` by its first
line, `.sf-cn` and `.sf-cw` by `align-self: baseline`. Area 161 holds every radio the app's own, `appearance:
none`, a ring of 1.5 pixels in `--ink-faint` with a transparent middle, and checked a ring and a dot of
`radial-gradient` in the ink, where it read `--tick`, which `.sf-zot-which input` set to the crux until
area 165 put it in the ink with every other tick and the property went. Area
138 holds `sfSentence`, which `sfPropReasonHtml` runs a sentence through, a full stop added where the words
end with none of their own.

Area 163, `sweep_cards`, holds the sweep of 17 October over the cards and dialogs, the print views, `/design`
and the empty and error states, each break measured in a headless browser's shots of invented data:
`.find-tick input` and `.switches input` given the ink by `accent-color`, Settings' and Rename's own rules
kept, `.find-input::placeholder` given `--ink-faint`, the print views' faint ink `PRINT_FAINT` in
`themes_print.py`, the light `--ink-faint` of `tokens.css`, which `HEAD` and `page_foot` write and the GETs
print takes through `tp.HEAD`, contrast computed on white and on every tint's 5 per cent wash of a trail's box,
on the audit trail's card `.tr-c.node` small print in `--ink-soft`, computed on every tint's 6 per cent wash in
both themes, the card's passages under `.tr-get .tr-said` at 13px, since Trace's `.tr-said` at 21px in `trace.css`
loads after `themes.css` and carried the same name, `.turn-text .find-hit` in `--ink` so a find in a passage set in
the faint ink reads on its wash, and the dark `--find-on` at 40 per cent.

Area 163 since 17 October, later, holds the night's plain errors and the trail on paper. A request of Sift's
that fails raises a `SearchError` whose words are plain, `failed_said` in `sift_search.py`: the database,
named by `service_of` from the run's own addresses and Crossref's, what happened, did not answer for no
answer or a 5xx, refused the key for a 401 or 403 that carried one, refused the request for any other
refusal, asked for a break from requests for a 429, and the status in brackets, or `unread_said`, sent
something Sift could not read. Its `detail` keeps the status, the address and the start of the answer,
scrubbed, and its `code` the status, which the Scopus and Crossref fallbacks and Settings' Check now read in
place of the words. `logged` gives a failure's detail, which a run writes to `run.json`'s `note` and
`log.csv` as before, beside `said`, the plain line, in `run.json`, and `summary` gives each failed row
`said`, from `run.json` or, for a run made before, from its note through `note_said`. `sfsRunRow` shows
`said` alone. The truncation check's rows carry `said` for the screen and `detail` for
`dry_run_terms.csv` and the command line, and its table shows `said` with no Failed before it. Every other
lookup of Sift's that says a failure, the fill, the citation counts, a title or a key work, says the same
plain line. The feedback route says `FEEDBACK_UNSENT` and `FEEDBACK_REFUSED` with the status, and the AI
calls `refused_said` in `ai_suggest.py`, Anthropic or Ollama, as the model list's note does. Zotero's
refusals keep their own words for now. The audit trail on paper and in the card share one grid,
`.tr-wide`, its five tracks `minmax(min-content, Nfr)` at the old shares, and `.tr-cols`, `.tr-block`,
`.tr-rows` and `.tr-row` are its subgrids, after a fallback of each row's own shares, so a column too
narrow for its longest word takes the room it needs and every row keeps the same columns. `.tr-c.node`
wraps with `overflow-wrap: break-word`, and `rows_html` draws each upright, `.tr-sp`, inside the cell of
the column after its gap, half a gap to its left and down past the row's padding, `--rp`, to its foot,
where it stood at a share of the row, since one placed on the grid by `grid-column` strayed onto the
first page of the printed trail. `trail_section` wraps the heads and the
blocks in `.tr-wide`, which scrolls sideways on the print view's screen and never on paper. Measured in
headless shots of invented data at 360, 93 of the trail's 896 words broke over lines, and none since,
with the lines on the gaps' middles. On the statements bar with rounds on, `#rail-who` and `.round-bar`
leave below 1440 pixels, where they left at 940 and 760, since with Guidance and Search on the bar a name
of 25 letters lost 4 pixels at 1280, where the name had 175 pixels and has 261 now, and a name of 30
letters needs about 228. Below 700 pixels `.find-card`
takes the whole width at the window's foot. Areas 17, 38, 41, 51, 56, 70, 78, 106, 113, 131, 134 and 150
hold the words and rules they pinned as they now stand.

Area 165, `sift_trace_left`, holds what the night's checks of 16 to 17 October left in Sift, Trace and
Settings. Every failure line is in `--amber`: on Search strategy `.sfs-run-fail`, `.sfs-problems p`,
`.sfs-src.failed`, `.sfs-paper-not` and `.sfs-state.unsaved`, where they took `--danger`, and a line beside
a control that failed takes `.said-failed` in `style.css`, which `dbsSaid` sets on the databases' line
in Settings by the check's `ok` and a key's failed Save or Remove, and `sfSaid` on the PDFs part's two
lines in `sift.js`. `.sf-choice input` and `.sf-zot-which input` take the ink, so no rule anywhere sets
the crux as a tick's colour, and a chosen radio's ring and dot are `--ink` itself, `--tick` gone with
the one rule that set it. Sift's shortcuts card has a row an act, Cmd or Ctrl with a selection on a
row of its own. `.keys td` aligns a key and its phrase by `baseline`. `terms_problems` in
`sift_search.py` gives `NO_TERM` while no block holds a term, `problems` takes it from there, and
`state` and an unsaved plan's view carry it, which `sfsDrawBlockProblems` draws in `#sfs-terms-said`
under the blocks. `sfsDrawStrings` and `sfsSteps` hold Copy and Copy the search while the search is
empty, and `sfsDrawRun` holds Start new run while `problems` holds a line, as Mark as registered is
held. A field's type on Set up the form leaves the sheet switcher's `.sheet-pick`, whose select has no
`appearance`, for `.sf-fc-sel` alone. `.sf-flow .node.future` lost its opacity of .5, the class's dash
kept. Above 700 pixels New project's cards set their labels in a column of 7.5em and their fields
from one edge. A run with `--root` keeps its list in `STATE_MEMORY` alone, and `relaunch` writes it
into the restart's environment as `STATE_CARRIED`, JSON, which `carried_state` reads back in `main`
and takes out of the environment, so a restart lists the run's Sift and Trace projects again, where it
came back with none. A run without `--root` carries none and drops any it inherited. The area starts
a real server with `--root`, opens a review and a Trace project, restarts it through `/api/server` and
reads both again. Areas 34, 98, 99, 123, 139 and 161 hold the words and rules they pinned as they now
stand.

Area 166, `distil_left`, holds what the night's screenshot checks of 16 to 17 October left open in Idiograph
and its print views. `themes_print.refusal` sets its line in `HEAD`, the print views' faces, ink and paper,
as `.refused`, and every print page says `lang="en-GB"`. `PRINT_AMBER`, the light `--amber`, is `HEAD`'s
`--amber`, which the GETs print's `.waiting`, `.tr-mark` and `.gt td.who .mark` take. `HEADS` in
`gets_print.py` is the trail's five column heads, written once under a GET's title by `trail_section` and
again at the top of each block with paths by `block_html` as `.tr-cols.tr-again`, which shows on paper alone,
the GET's own heads going there, and never in the card. `table_section` wraps the GET table in `.gt-wide`,
which scrolls sideways while `table.gt` keeps 720px, and the GET's `.bar` and `.tr-head` wrap. In the page,
`.back-to-turn .mono` went, the trim card's warning names a workbook highlight, `#rn-copy` goes and comes
with the list in `rnListShow`, `sourceSaid` names the create and import cards' source, and the UI's own
words in `app.js`, `themes.js` and `index.html` carry no curly quotation mark, and the board's `.rail-sep`
on PETs and GETs stays at every width. `.rail-btn`, `.rail-mark`, `.th-step` (Idiograph's `.sf-steps button` since
18 October), `.sheet-pick select` and
every checkbox take `--focus` or `--focus-small` from the keyboard, and a field of one line takes `--focus` at
no weight, `:where(...)`, so a field's own rule wins. Since 8 November both rings are the solid `--crux`
(4.6 to 1 or more on paper, card and sunk paper in light, 7.7 to 1 or more in dark, where the wash they were
stood at 1.1 and 1.3 to 1), and the edge of every text field, note box and chooser is `--field-edge`
(`#8F8473` light, `#6F6758` dark, 3.1 to 1 or more on the same three papers), where `--rule` and `--rule-firm`
stay for dividers and cards. `.find-card` stands under `--band`,
`#trim .card` takes 640px, `/design`'s sample hid its part's word below 1440px as the app did (Idiograph's steps
since 18 October), the
margin's `.turn.aside .speaker` and `.round-mark.todo` lost their opacity, a tinted card's `.th-time` and
`.gt-n` take `--ink-soft`, and `.th-badge` takes its `--hue-base` 65 per cent to `--ink`'s 35. Areas 34, 46,
51, 61, 156, 161 and 163 hold their pinned words and harnesses as they now stand.

Area 168, `search`, holds Search across Idiograph (17 October, build 1 of 2): `app_search.fold` and `matches`
beside `tbFindMatch` in node, the window round the first word found, This case and This project on an invented
allotment project of three cases, each of the sixteen kinds found with where it is and where a click lands, the
PETs' marks as the print view gives them, the three groups of filters each counted with the others' ticks,
the first 200 and the total, a workbook read once and held against its time and size, a POST and a GET over
HTTP, a path outside every root refused with 403, and no file written, none added and the recent list
untouched. In the page it holds the card, Search on the three bars in Find's place and on a project's page
alone on the home screen's head, the shortcuts card's rows, and in node `searchKey`, which takes
`Cmd + F` on the statements screen, PETs, GETs and a project's page and leaves it to the browser on the picker, any
other screen, under a card of the app's own and with Shift or Alt held, `searchScopes` and `searchMarked`.
`support.top_bar_kinds` reads Search, and Find and replace on a bar, as `search`, and areas 56, 62, 66, 82,
120, 131 and 155 hold the bars, the manual's sections and the routes as they now stand.

Area 170, `one_tone`, holds one failure tone and the orange kept to its places. `saidIn` and `saidErr` in
`app.js` write every line beside a control in Settings, Zotero's, the key's, the models', the bench's, the
exports', the projects', the labels', the agents' guide's and Claude Desktop's, and the AI note on
Experiential statements, toggling `.said-failed` on a failure and never on a restart, as `sfSaid` does for
Sift's Zotero card, by `SF.zot.failed`, its bench and its second screener, and `thNote` and `gtBesideNote`
for the canvas. `ai_suggest.anthropic_models` marks a live list that failed `failed`, which the models' note
takes. A second rule of two classes holds the amber over `.ai-note`, `.sf-zot-said`, `.sf-two-said`,
`.th-note` and `.th-qnone`, and `.th-save.failed`, `.th-exported-head.failed`, `.th-names-note.failed`,
`.th-vsaid` and `.gets-said` take `--amber` where they took `--crux`. Sift's `.sf-bar.in` and the slider's
stretch take `--ink-soft` and its knobs `--ink`, the funnel its word's ink, `.sfs-open-tag` and a running
`.sfs-src-state` the ink, and a link to a page outside the app, `.sfs-reg-steps a`, `.sfs-reg-when a`,
`.sfs-site` and `.tr-links a`, the accent underlined as `.sf-links a`. `.count-flash` and `.th-flash` take
the ink, `.nudge i` the amber, `.turn:hover` and `.turn.noting` `--paper-sunk`, and a quote in a passage
not current `--ink-soft`. `themes_print.quoted` sets a quote in single curly marks for every print
view, `gets_print` among them, `refusal` takes `PAGE`, and the trail's heads under a GET's title carry the
minimum widths that keep its five columns about 720px on a narrow screen. A label's `.th-more` stands
absolute at its top right corner, so the line it leaves the title is `LABEL_CHROME`'s. `.band` takes no
selection, `passages_said` names a sheet in straight marks as `sheetLabel` does, and `sfMapLine` says "No
records to map." with none. Areas 115 and 156 hold their pinned words as they now stand.

Area 171, `keys_and_orange`, holds the keys in capitals, the last of the orange out of its places, a drag
kept off the title bar and a PET's or a GET's title clear of what stands round it. Every key written by hand in
`index.html` and the scripts stands in its capital, which the area's `lower_keys` looks for in brackets,
after a `+`, after "press", opening a sentence and in every shortcuts card's cell, and in the manual's
backticks. `.tag.raw` takes `--ink-soft`, the outline of `.day.today` `--ink`, `.dot` `--ink-soft`,
`count-tick` runs from `--ink-faint` to `--ink`, `.player-btn:hover`, the scrub's hover, `.th-play:hover`
and `.th-pbtn:hover` the ink, a playing `.th-play` the accent, `.sf-arrow`, `.sf-drop-before`,
`.sf-drop-after` and `.sf-flow .node.now` the ink, `.sfs-drop:hover` and `.find-pair-go:hover`
`--paper-sunk`, and the Sift sidebars' edges `--ink-faint` under the pointer, their `:focus-visible` keeping
the crux edge. The area holds every `--crux` in the five stylesheets to the places design.md gives it.
`.rail` takes no selection, as `.band` does. `thPick` settles with `labels: [gid]` as a PET note does,
`thStatementWrite` settles the card it wrote against the labels and frames before it, and
`thMakeRoom(v, size)`, after `thSettle` in `themes.js`, runs once `thLoad` has drawn and again once the
type has loaded: each pair `thClashes` finds with a PET or a GET in it settles by the one that gives way, a
card or a note before a PET or a GET and the second of two, through `thSettle`, and since 31 October two cards
or notes as a drop settles them, the one `thReadsFirst` names leading (area 309), each pair once, and nothing is
saved by it. `themes.label_size(text, upper, marks)` estimates a label by its title and its marks alone,
as the page has drawn one since its count went to its frame's badge on 3 October, and area 55's table is
the page's labels measured again on 17 October. Areas 23, 25, 27, 28, 30, 45, 49, 51, 52, 54, 55, 57, 61,
62, 82, 100, 125, 136, 139, 152, 153, 155 and 158 hold their pinned keys, colours and sizes as they now
stand.

Area 176, `polish_seven`, holds what polish6's screenshot check left (18 October). Mermaid scopes its own rules
by the drawing's id, `#sf-flow-svg-N .node rect`, which outranked `.sf-flow .node.now rect`, so that rule's
`stroke: var(--ink)` now carries `!important`, and `prisma_source`'s `classDef` lines keep no colour, so
`prisma.md` holds none of the screen's. `.turn-gutter`, `.turn-notes-text` and `.notes-head` take no selection,
as `.rail`, `.band` and `.round-mark` take none, and `.turn-gutter input`, the timecode open for correction,
keeps its own. `.th-qlist.th-picked` keeps the 20px under it that `.th-panel-meta` keeps, so a `.th-leave-row`
or a note drawn 10px up into it stands clear of the last picked quote. `say` calls `toastClear(el)`, which
raises `#toast` 8px over whatever of `TOAST_CLEAR`, the zoom bar and `#th-discard` while `#themes` shows, its
rectangle meets, by an inline `bottom` as `rnShowRow` sets one, and touches nothing on any other screen. The
statements screen's keydown lowers a one-letter `e.key` into `key`, so E, Q, C, T, G and P take Caps Lock as
PETs', Sift's and Trace's always did, and the area fails on any line of the page's scripts that compares
`e.key` with a lowercase letter and not its capital, or a lowered key whose `const` does not lower it. Areas
23, 25, 28, 30, 39, 51, 152, 153, 155, 158 and 171 hold their pinned keys, the toast's harness and the flow's rule
as they now stand.

Area 177, `distil_steps`, holds Idiograph's tabs on its three bars, the project's page in the order of the
work and New sticky note on the boards' bars (18 October, Topic A of 17 October): the markup and its order
on both bars, the shared style in `style.css`, ES below the tabs' width, the tabs on the first of two rows, the
way back's arrow alone, `esStep`, `esToGets`, `openStatements`, `thStepTo`, `gtToPets`, `thToStatements`,
`thBackDraw`, `thStepsDraw` and `thStickyBar` in node, the statements bar's narrow steps, the page's order and
the docs. Areas 38, 39, 43, 45, 49, 51, 52, 53, 66, 74, 75, 82, 85, 89, 95, 109, 110, 120, 122, 131, 148, 150,
151, 155, 156, 157, 158 and 166 hold their pinned words and harnesses as they now stand.

Area 178, `search_sift_trace`, holds Search's second build (18 October): an invented Sift project on
village ponds, a review with a plan, reasons and a run whose screening holds decisions, decision notes, his
fields, a column on the table and one on the form and key excerpts, and an invented Trace project on seed
libraries, a protocol in Markdown with its references and a claim note. It holds each of the ten new kinds,
where it is and where a click lands, a record at its stage, a form's answer at Extract and appraise, a
term at its block and line, a claim, a reference at its first claim and one never cited at its own row, This
Sift project from the review and from its run alike, This Trace project with a reference shared by two
manuscripts found once, Everything over the three parts in a study's order with the demo last among Idiograph's,
Project's counts and its tick, a refusal for a folder in no list, each file read once and held, and nothing
written over HTTP. In the page it holds Search on Sift's, Search strategy's and Trace's bars and the picker,
the shortcuts cards' rows, the scopes, `searchCovered`, the three screens' keys left to the card, the kinds'
names, the parts' headings, the landings `searchToSift`, `searchToPlan` and `searchToTrace`, and in node
`searchKey` and `searchWhere` on every screen and `searchWhereLine` with Everything. Areas 120, 155 and 168
hold the bars, the keys and the scopes as they now stand.

Area 182, `polish_eight`, holds the polish after Adam's look at the night's builds (18 October). `growNotes`
gives `#en` `NOTES_LINES`, five, of its own computed line height with its padding and edge at the least, and
its `scrollHeight` with its edge beyond that, read after its height is let go, and the page draws it with
`rows="5"`, where `grow($('en'), 2)` started it at two. Columns keeps its word, its order in its title
alone, `#cols-pick-said` and `#work.cols-said` gone. `colsMenu` starts the menu from its own width, measures
the strip of `.col-head.col-last` it would leave at its left, and where that is under half its width gives
it `min-width` to the column's left edge. `selBarPlace` reads `selBarLines`, every line box of `.turn-text`,
`.turn-notes-text` and the speaker line in the rows near the selection by a `Range` over each, and
`selBarCut` finds a line across the toolbar's width that an edge would cut through its letters. Its foot
first kept clear of the line next to the selection, a far edge that cuts a line steps the toolbar clear of
that line where the step is `gap - 2` pixels or less, so its near edge stays 2 pixels off the words, else
`selBarWhole` moves the far edge past the line, up above the words and down under them, where the edge
falls among the letters, outside `tail`, 22 per cent of the line's box at its foot, and `head`, 12 at its
top, and else it stays, the difference set as `min-height` and `.sel-bar`'s buttons centred in it. On the boards `.th-map-btn[aria-pressed="true"]` takes
`.th-mode.on`'s rule, `thMapFit` fits with no cap, `TH_MAP` losing `most`, and `thMapBox` keeps the box's
size for `.th-map-area`'s `overflow: hidden` to cut. Sticky notes' room: `thStickyRoom(id)` is a size
function giving a new note `TH_STICKY.w` and `TH_STICKY_ROOM` lines of `TH_STICKY_LINE` more than it
measures, which `thStickyNew` settles with, and the box's `input` asks `thStickyOver(v, id)`, whether the
note meets a neighbour in its own place as it measures, settling a fresh note alone again with the room
when it does, and since area 185 a note there already too, `TH.stickyEdit.moved` keeping that move as an
edit though the words come back to what they were. In node it holds the field's height, the menu's width, the toolbar over 24 and 34 pixel
lines, the map's fit and box, and a note made between two cards. Areas 61, 155, 158, 163, 172 and 179 hold
their pinned words and harnesses as they now stand.

Area 185, `polish_nine`, holds what polish 8 and the sixth Tauri build left (18 October). On the boards
`thMapAround` fits the board and the view together where the view's box would reach past every side of
the map, `thMapViewDraw` writing the marks again only where the fit changed and holding it through a drag
on the map, and `.th-map-view` takes the transcript's line and dimming. `thStickyEditOpen`'s `input`
moves any note whose words grow over a neighbour, a new one or one there already, and `wnFootRoom` keeps
What's new's line's height as `--foot-h` for the home screen's foot and a toast over it. In node it holds the fit after Fit
all, a pan and a view inside the map, the marks written once for a pan, a drag's held fit, a note there
already moved clear as it grows and the line's room. Areas 179 and 180 hold their pins and harness as they
now stand.

Area 193, `polish_ten`, holds the behaviour of the sweep's Wrong and Rough of 18 October. `openSearch` hides
`.search-in` where `searchScopes` gives one place alone, the home screen's Everything, and `searchMore` gives
a heading `.over-none`, hidden in its place, while More holds every row under it below 700px. In node it holds
Search in on the home screen, a case's screens, a project's page, Sift and Trace, and the headings at 360
with More shut and open and at a desk width. The rest of polish 10 is words and layout, in review shots:
`.saved` taking no width once it has faded, the PETs bar's counts at 1280, What's new for 0.9.1, the
playhead at the words, the minimap's box fading with its card and the button's band at 360. Area 181 holds
its pin of the band's line as it now stands.

Area 212, `search_cases`, holds Search for agents (20 October) on an invented project of two potters, each case
a copy of the demo's interview with a statement, a note and two boards' PETs planted: hits in both cases with
each one's sheet, row, speaker, short id, key, placing and the tool that opens it, the marks in every snippet, a
case and a board alone, the kinds, a phrase, the cursor's pages together every hit once, the same hits as
`/api/search` for the project and the case, the MCP tool's answer, every refusal, the tick off, a screening by its
folder, and no file changed.

Area 228, `words`, holds the words build of the three-app split (Adam's rulings of 20 October): the analysis's old part
name gone from every screen and doc, participant for case on every screen and in the agents' guides, Quote for Key
quote wherever a person reads it (the workbook's own column and `export.py`'s header followed on 22 October, area 250), and
the API's names, `case`, `cases`, `--case` and `key_quote`, kept, the MCP instructions saying a case is one
participant. The manual is one file per app, `docs/manual.md` Idiograph's IPA sections, `docs/manual-sift.md`
and `docs/manual-trace.md`, named by `app_identity`'s `manual`, read by `manual_source` and staged by
`bundle.stage_source` as the bundle's `docs/manual.md`. The server's own lines, `CLOSED_LINE`, `QUIT_LINE`,
`ELSEWHERE`, `NOT_OURS`, `BUSY_LINE`, `WINDOWS_LINE` and `NO_MANUAL`, hold `{name}`, filled by `named` from
`IDENTITY`, and the window's `CLOSED` reads " is closed." so any app's last line ends its windows. A GETs
revision kept as a participant's changes come in is named "Before Rowan's changes came in". The area
checks each app's `/manual`, the lines as Sift and Trace, the staged manual, and `cases`, `--case` and
the MCP tools still answering in case.

Area 250, `quote_header`, holds the last three places of that rename (Adam's ruling of 22 October):
`workbook.HEADER` heads the quotes column Quote in every new workbook, `export.HEADER` heads the CSV's
last column Quote, and `gets_get_lines` gives "Quote for Rowan:". `ROLE_TESTS["kq"]` reads any heading holding "key quote" and
Quote or Quotes, so a workbook headed Key quotes, made before then, reads and writes through
`read_case`, `save_turn`, the command line, the MCP tools and the export exactly as before. The app never
renames that heading by itself: a save touches only the cells it changes, and a heading Adam may have read in Excel
for months is his file's, not ours to rewrite. Since 23 October (Adam's ruling) one op renames it on his
word: `workbook.quote_heading` changes the quotes column's heading cell on each sheet `read_case` reads,
a heading holding "key quote" taking Quote and nothing else, and `routes.rename_quote_heading` runs it
under `writing`, after `archive_copy(..., "pre-heading")`, recording each sheet in the progress file's
`edits` at row 1 with `heading: true` and one batch id. `api_stamp` leaves those records out of its
`turns`, so the statements screen never says a passage was written. The command line's `quote-heading`
(one participant, or `--all`, each workbook its own write and a refusal of one said and skipped), MCP's
`quote_heading` and `/api/quote-heading` all run it. Area 257 checks it. The demo's three workbooks were rebuilt with Quote, each
differing from the old one in cell F1 alone. The area checks a new workbook and one made from the
template, the four headings, the CLI's `statements` the same under either heading, a `turn write` to an
old-headed workbook changing only that row's C, E and F, and both CSVs.

Since 26 October (parity with the page, group 1) the statements screen's own writes have ops for agents,
each calling the route itself with the page's body and three keys more, `dry_run`, `tool` and `request`,
which the page never sends: `turn edit` and MCP's `turn_edit` call `api_edit_turn`, `turn interviewer-note`
`api_interviewer_note`, `turn assign`, `turn assign-undo` and `turn trim-undo` `api_rows` (ops `assign`,
`restore` and `untrim`), `turn trim` `api_trim`, and `project add-transcripts` `api_add_transcripts` (op
`add`, each file read first by `/api/new-project`'s `read`, so each speaker's role is the card's guess). A dry
run reads and checks as the write does and saves nothing: `workbook.edit_turn`, `save_interviewer_note` and
`trim_rows` take `dry`, an assignment's dry run is the `preview` op's answer, an undo's checks its record
alone, and `add_transcripts` answers `add_plan` once `new_cases` has checked every row. `marked` puts `by`,
`tool` and `request` on the op's own History record, the edit, the assignment or the trim (an undo's as
`undone_by`, `undone_tool` and `undone_request`). An agent's interviewer note goes into `edits` with
`interviewer_note: true` and the note before and after, the rows and rounds untouched, and the page's own
note still writes nothing there. An agent's Add names the tool and request in each new workbook's
description (`add_made`) and records itself in each participant's progress file under `imports`
(`add_record`), the progress file put back with the rest when the Add fails. Area 265 checks each op
against the route called as the page calls it on a twin workbook, cell for cell.

Area 238, `check_key`, holds Check key (21 October, round2fix): `/api/check-key`, `api_check_key` in
server.py, a route every app answers, asks Anthropic's model list through `ai_suggest.check_key` with the key
typed in the field or else the stored one, stores an accepted typed key as `/api/key` did, caches the live list
for the Model select, and answers `ok`, `said` (`KEY_WORKS`, `KEY_REFUSED`, `KEY_UNCHECKED`), `anthropic` and
the key's `source`, never the key. `key_place` and `ai_transport` give the Anthropic key and model list the
same stub hook Sift's searches have: with `IDIOGRAPH_SEARCH_STUB` at a loopback address the key goes through
`sift_search.STUB_KEYCHAIN` in memory and the model list to the stub's `/anthropic/v1/models`, so a smoke run
never reads the login keychain or calls Anthropic. The area runs a provider of its own on loopback. The AI
features page's large switch is the same `#set-ai` box, a `role="switch"` input drawn as `.ai-slide` beside it
in `label.ai-master`, saved as `ai_suggest`, and the order under it is `#ai-provider-row`, `#ai-key`
(`keyHome` puts it back before `#ai-choice`), `#ai-choice`, then `#ai-features`. The paragraph over it is each
app's own `<p data-only>` in `#ai-warn`, and each app's confirm card body its own `.ai-confirm-body` with `data-only` (22 October).

The same build put the statement length in the length nudge's row (`nudgeRow` drew `#words-n` there until settingsplit,
5 November 2026, which moved the field to Project settings, `wordsSet` saving it through `/api/project` a moment
after the last change), let a GETs or LGETs card's mark wrap whole
under its count (`.gt-card .th-foot` wraps), gave the project's name the first row of the PETs and GETs bars
at 760px and below by moving the two doors to the ends of the board's row (themes.css), and made Home's
highlights a list of four, `ul.lede-points`, on every app's Home.

Every fixture is copied into a scratch folder first, so nothing under `Main Data` is ever opened for
writing. A smoke run of the server for testing starts with `--root` at a scratch folder, and every
workbook API refuses a path outside that root, so the recent list cannot reach a live case from a
test server. Pass `--scratch <folder>` to keep the copies, and `--main-data <folder>`, or the
`IDIOGRAPH_MAIN_DATA` variable, to run as though no live data were on the machine. The launcher
checks run the bundle's root resolution from a copy reached through a symlink and never start a
server. The quote rule and the PETs canvas's model, the half of `themes.js` with no DOM in it, are checked
with node when node is on the machine, and so is the feedback collector, with a stand-in for its
database. No test needs a key, the keychain, Ollama or the network: the
API call, the model list, the local model and the feedback route all take their transport as a parameter, the keychain
calls take their runner, and the suite hands both a fake. The key checks assert that a key string appears in the one command that stores it
and in nothing else, and that no response carries it at all.

### Review shots

For whoever builds the app. Every screenshot a builder hands Adam explains itself: a heading band above
it says what changed (or, with no Before, what it shows) and, after "Check:", what to look at, a change
shows Before and After at one scale, and a dashed box marks the changed part on each. Two files make them:
`packaging/shot_box.js` measures the boxes and the crop in the page, and `packaging/review_shot.js` draws
the composite and refuses one that breaks the rules review checks kept finding broken.

The capture. Shoot at device scale 2. Inject `shot_box.js`'s text into the page (`Runtime.evaluate` with
the file's text and then `shotPlan([...selectors])`, `returnByValue`), shoot the plan's `crop` as the clip
at scale 1, and write the plan as JSON beside the PNG under its name, `notes-after.png` beside
`notes-after.shot.json`. Then compose:

```
osascript -l JavaScript packaging/review_shot.js --out <review>/01-notes.png \
    --before <raw>/notes-before.png --after <raw>/notes-after.png \
    --changed "Exploratory notes column: wider" --check "each note fits on two lines" \
    --boxes-from-before <raw>/notes-before.shot.json --boxes-from-after <raw>/notes-after.shot.json
```

Each dashed box carries a halo under its dashes in the picture's own light or dark, read from the pixels just inside and outside the box's line (white on a light shot, the shot's own dark colour on a dark one), so the dashes stand out on both with no glow round the box.

and `osascript -l JavaScript packaging/review_shot.js pack <review>` (or `node`) prints each shot's
heading in the order of their names, the lines a report lists. Keep the raw shots in a folder of their
own, and number the review shots in the order to look at them.

`shotBox(target)` takes a selector or an element: its rectangle plus 8 pixels a side, checked against
every line of text (`Range.getClientRects` on each text node), picture (img, svg, canvas, an avatar or an
icon), divider and side of a visible border on the page that is not inside it. A picture lying under the
whole element, a board's backdrop, does not count, and nor does the border of a bar holding it. When the box would cross or touch one it climbs to the next
larger enclosing element until one clears, skipping wrappers of the same size and stopping short of one
three quarters of the window both ways, and says which it chose (`element`, `row`, `card`, `menu`, `bar`,
`dialog` or `block`, from the role or the class's last word, `row-menu` a menu, `card-close` not a card).
The box also lies at least 8 pixels inside the edge of every menu, card, panel, list, section or bar it
sits in, or it climbs to that container (the shotlint2 build, 20 October, after two builders' shots made
with the tool failed their check on a box on a menu's border, on a panel's foot, 7 pixels from a card's
border). An edge is a visible border on a side, or, on every side, a background that stands out from what
the element sits on or a shadow, so a menu drawn by its shadow alone counts. A side on the window's edge
is left to the mat (`--pad`), a bar too thin to hold the box with room across it keeps the rule above, and
a container three quarters of the window both ways is the page. The box names the container it climbed
to as `container`, with the reason, and lists each edge it cleared as `edges`.
`shotCrop(boxes, margin)` is the boxes with 24 pixels of room, grown until no card, row, menu, bar or
bordered box is cut at an edge (one longer than three quarters of the window along a side is cut at its
ends), inside the window. `shotMinText(crop)` is the smallest text drawn inside the crop, its font size
times any transform's scale. `shotPlan` gives all of it in one: the device scale, the crop, each box in the
crop's own coordinates with what it chose, the smallest text, and the problems, a box that clears nowhere,
a selector that matches nothing, a part the window cuts, a box at the window's edge, two boxes overlapping.

The composite. `--before` and `--changed` go together, and a shot with no Before takes `--shows`, a line
saying what it shows, then `--check`. `--boxes-from <sidecar>` marks both panels, `--boxes-from-before`
and `--boxes-from-after` one each, drawn exactly where the sidecar says, since the room is in them. The
sidecar's device scale is the shots', so `--scale` is left out. `--box x,y,w,h`, `--box-before` and
`--box-after` still take boxes by hand, in the shot's CSS pixels, padded a little outward. Before and After
sit side by side, or one over the other when a shot is wider than twice its height, and `--stack` or
`--side` chooses. `--pad N` draws a mat of N pixels in the page's colour round each shot, its own edge
kept as a thin line, for a box flush with the window's edge: a button in a full-width status bar keeps its
own box across the bar's border and past the window, `shotPlan` asks for `--pad 16` with a note instead of
a problem, and the box's 8 pixels count from the mat's edge. It refuses, exit 1 with the reason in plain words: a box within 8 pixels of its panel's
edge, two boxes overlapping on a panel, a composite over 1,400 pixels wide in its own pixels, a Before with
no `--changed`, a shot with no Before and no `--shows`, a sidecar asking for a mat composed without one, and when a sidecar is there, given or beside a raw
shot under its name, a sidecar listing the capture's problems, a box under 8 pixels inside one of its
`edges` (a box put back by hand where the climb refused it), one made for another crop or another scale,
and a smallest text that would show under 12 pixels with the composite shown 900 wide (its size times the
device scale times 900 over the composite's width). A bar shown whole (bump097, 26 October, Adam: a bar cut into windows stacked on each other is very hard to read, he
reviews on a wide screen and clicks a shot to zoom, and the app is designed at 1280 wide). The recipe: shoot a
full-width bar (top bar, toolbar, status bar) at 1280 wide and device scale 1, everything else at scale 2 as
before. `shotPlan` notes "the crop spans the window" when the crop is as wide as the window. Compose with
`--pad 16` (the mat the flush note asks for) and `--whole`, or let that note switch it on: Before is stacked
above After, never side by side, and the smallest text is held to 10 pixels at its real size, not at 900 wide,
since the shot is read zoomed in. The 1,400 limit stays: 1280 and its mat make a composite about 1,350 wide.
It also refuses a missing check, a box past its shot
and an `--out` that would overwrite a raw shot or write through a symbolic link.

The look follows Harbour's `scripts/lib/review-shot.ts`: a dark heading band, the first line in semibold
and "Check:" in amber before what to look at, then the shot, or Before and After labelled in a grey and a
teal pill. Both are drawn at the scale they were shot at and never stretched. The heading is 1/46 of the
composite's width and never under 20 pixels, and the gutter 0.6 of it, so `layout` settles the two in a
few rounds. The heading's lines are a fixed 1.3 of its size: with a multiple, AppKit drew them taller than
it measured them, and the band cut the last line (20 October). A box is magenta dashes on a white halo,
each side starting and ending on a corner. Past 16,000 pixels a side the render scale comes down.

The file runs in two places. Through `osascript -l JavaScript`, its `run` reads the PNGs with
`NSBitmapImageRep`, measures the heading with AppKit and draws into an offscreen sRGB bitmap, as
`packaging/tauri/heading.js` does, so no screen is read and nothing is installed. In node it exports the
pure functions, reads a PNG's size from its header, runs the pack, and takes a shot through every refusal,
stopping only at the drawing. Beside each PNG goes `<name>.caption.json`, with Harbour's `changed` (null
with no before), `check`, `beforeAfter` and `arrangement`, `shows` when there is no before, and `boxes`,
each panel's as given. `pack <folder>` refuses a shot with no caption file or one that reads wrong, a
caption with no shot and a folder with no shots, so raw shots keep a folder of their own. Area 183 checks
the layout maths, the captions, every refusal and the pack in node, `shot_box.js` on a made-up page through
a stand-in for the few DOM calls it makes, and on a Mac draws shots, a sidecar's among them, and reads their
pixels back, the heading band holding nine wrapped lines among them.

**Shots at a zoom, in the Mac's own engine** (zoomsweep, 30 October 2026). Chrome's shots are Blink at 100%,
and the Mac app is the system WebKit at the zoom Cmd+plus and Settings' Text size set (Small 90%, Medium 100%,
Large 125%), so a fault only WebKit lays out, or a scroll bar only a zoom brings, never shows in them: fbcard's
sideways bar on Send feedback's note box (29 October) showed only there. Since Adam's answer of 29 October a
layout change's shots include Large. `packaging/wk_shot.swift` is a WKWebView, the Tauri window's engine on a
Mac, in a window off the screens, at a page zoom (`pageZoom`, what the window's zoom sets), light or dark, at a
window size, with legacy scroll bars, always shown as with a mouse plugged in, for its own process alone and
never a system setting, and no storage kept from one run to the next. Compile it once into a scratch folder:

```
swiftc -O packaging/wk_shot.swift -o <scratch>/wk_shot
~/.claude/bin/heavy idiograph shots <scratch>/wk_shot --url http://127.0.0.1:<PORT>/ --out <raw> \
    --steps <steps.json> --zoom 1.25 [--scheme dark] [--width 1280 --height 800] [--scale 2] \
    --shot-box packaging/shot_box.js [--init "<js run at each page's start>"]
```

The steps are a JSON list, each an object done in this order: `size` [w, h], `zoom`, `scheme`, `load` a URL,
`js` an expression run in the page and awaited (a screen's `open` from `packaging/pixels/screens.mjs` as
`"(<open>)()"`), `waitFor` a selector, `wait` milliseconds, then `shot` a name, the whole window, or with
`clip` {x, y, w, h} in CSS pixels, or with `plan` [selectors] (and `planOptions`), which runs `shotPlan` in
the page, shoots its crop and writes `<name>.shot.json` beside `<name>.png`. Every value a `js` step gives
is printed as `js <n>: <json>`, and the run ends `WK: done <n> shots`. What differs from Chrome's: the
sidecar's `scale` is the pixels a CSS pixel came out at, `--scale` times the zoom, 2.5 at Large, where
shot_box's own is the page's devicePixelRatio, so review_shot.js maps the boxes and holds the smallest text
as it does a Chrome shot's, and a crop comes out 1.25 times as many pixels across: crop tighter, `--stack`,
give the shot's step `"perCss": 2`, 2 pixels a CSS pixel at any zoom as Chrome's at device scale 2 (a step's
`"scale"` is its pixels a point), or `--scale 1` for a bar shown whole, 1280 pixels at any zoom. WebKit keeps a Mac's scroll bars out of its
snapshots (it draws them outside the page since 2023), so the tool turns off its async scrolling, which
draws them in the page again where the snapshot holds them, the layout unchanged. The window's own bar, at
the right of a page that scrolls as Home does, is the one a snapshot still leaves out. A step with `"native":
true` shoots the window server's own picture instead, the window as the screen shows it, at the screen's
scale and never more, 1 on Adam's display: the check that a snapshot's bars are the window's. Shoot Before
and After alike, both through wk_shot at one zoom, main on PORT + 1 as before.

### Motion recordings

For whoever works on Home's mark coming in (its seven ways, `homeMarkPlay` in `family/static/shell.js`). The tools
the markplay rounds of 23 October 2026 made in scratch live in `packaging/motion/` since 26 October (motiontools).
They need only what the Mac has: node 22 or later, Google Chrome (`IDIOGRAPH_CHROME` names another), ffmpeg,
ffprobe, rsvg-convert and the venv's python by its path. `chrome.mjs` holds what they share: Chrome run headless and
driven over the DevTools protocol with node's own WebSocket, nothing installed, and Home opened at a width with the
page's `requestAnimationFrame` held on a virtual clock, so each frame is exactly 1/60 s on however long it takes to
shoot, and the page's 5 s safety, which runs on the wall clock, turned off. Every tool records a server of its own
(`--port`, 8770 by default, or `--url`) and refuses port 8765, the running app's: start one with `--root` and
`--config` at scratch copies of `demo/` and a settings file, and `IDIOGRAPH_STAY_OPEN=1`.

- `node packaging/motion/rec.mjs --way race --width 1280 --scheme light --out <raw>/race-1280-light --port <port>` records one
  way at device scale 2, frame by frame, to `f0000.png` on and `meta.json` (frames, fps, clip, the lockup's box, page
  errors), until the way ends and the lockup has rested half a second. The frame is cut round what the way uses: the
  whole width under 600 pixels, the race to the window's right edge, the spin from the window's corner. `--clip x,y,w,h`
  frames it by hand, `--probe` shoots the resting frame alone to check the framing first.
- `encode.sh <raw folder> <review>/07-race-1280-light` makes `07-race-1280-light.mp4` at real speed and
  `07-race-1280-light-half.mp4` at half speed.
- `node packaging/motion/frames.mjs --way race --width 360 --out <raw>/frames-race-360.json --port <port>` plays the way
  again and writes each frame's matrices of the brackets, the dot and the letters in the lockup's units, with the
  toolbar's icons, the notice, the window's edges and IDIOGRAPH's ink profile. The spin's pieces are CSS 3D blocks, not
  the scene's SVG, so it is checked by its recording alone.
- `.venv/bin/python3 packaging/motion/check.py <frames.json> [--near 8] [--path]` is the frame checker. It prints each
  frame where a bracket or the dot passes through a letter, the dot through a bracket, a piece comes nearer the toolbar or
  the notice than `--near` pixels, a piece is cut at the window's left, top or right edge, or the page grows wider than
  the window. Then each piece's first frame inside the window and how far in it is drawn, its least room from the toolbar
  and the notice, when each piece last moved, and with `--path` the dot's highs and lows. A piece crossing the edge it
  runs in from is expected, the race's first frames among them.
- `node packaging/motion/storyboard.mjs --raw <raw folder> --out <raw>/sb-race.png --times 0.3,0.8,1.5,2.15 [--top --left
  --tall --zoom --cols]` puts chosen frames of a recording in a grid with each one's time under it, each frame cut to the
  part that matters, for `review_shot.js` to head with `--shows` and `--check`.
- `node packaging/motion/profile.mjs --out <profile.json>` writes the ink profile alone, and
  `.venv/bin/python3 packaging/motion/bounce.py <profile.json> <out.json> [--speed 1.5 --e 0.84]` is the bounce solver: it
  searches backward from the middle for a ball thrown in from the right that bounces once on a letter and once on the right
  bracket's top arm and drops between the arms' tips, as the race's ball does, and prints the roomiest it found.
- `packaging/motion/reel.sh --review <review> --out <reel.mp4> [--ways "01-spin:Spin ..."] [--variant 1280-light]` makes
  one titled video of a review folder's recordings, 1280 by 720, each after a card with its number and name (an
  underscore in a name for a space). With no `--ways` it takes every `<NN>-<way>-<variant>.mp4` there.

A motion round runs them in this order: a smoke server, `rec.mjs --probe` for the framing, `rec.mjs` for each way at
1280 and 360, light and dark, `frames.mjs` and `check.py` at each width until the checker prints nothing unexpected,
`encode.sh` for each recording, `storyboard.mjs` and `review_shot.js` for the frames to look at, then the review
folder's page and `reel.sh` for a video to share. The bounce solver comes before any of it when a ball's path is
being worked out.

The review folder holds `index.html`, a page with a section for each way (whose idea it was, what it does, its
length) and its recordings playing side by side, 1280 and 360, light and dark, a Real or Half switch choosing the
speed. Beside it the recordings, `<NN>-<way>-<width>-<scheme>.mp4` and the same with `-half`, and the storyboards,
`<NN>-<way>.png` with letters after the number for the close-ups (`07b-race-edge.png`), each made by `review_shot.js`
with its heading and "Check: ..." and its `.caption.json`, so `review_shot.js pack` lists them. The raw frames stay
in a folder of their own.

## Files

### The bars of option C (26 October 2026)

The title bars carry no back arrow. Each screen's band opens with the path, `.ds-path`. `distilToProject(project)` in distil.js is the project's step on the statements screen, the boards and Trajectories: it leaves the screen through `searchLeaveFor`, as Home does, so a typed field is saved and a canvas flushed, then keeps the project's page (`homeKeep`, the demo by `DEMO_ID`) and loads Home. The participant's chooser, `#es-who` and `#th-cases`, stands in the path, `thPickerPlace` hiding the boards' one on GETs and LGETs, and `thWhoDraw` shows the name alone (`whoName`) while keeping the case's whole label in `data-label` for the exports' headings and the window's title (`thCaseLabel`). `#th-dock` shows with the band whether the palette is docked or floating, holding `#th-open-cases`, the board and `#th-open-side`, and `thPalettePlace` docks the palette before `.th-dock-end`. `#th-faces` stands in `.th-boardset` on `#th-dock`, directly after `#th-save` (Adam, 26 October 2026: Canvas and Table is not a status bar thing, tablemove), `flex: none` so it never gives way, the docked palette's steps narrowing first, and the dock showing in the Table view too. `thFace` runs `thPaletteFit` when the switch first shows or goes, and below 760px the save state keeps its words on the board's line. `#th-status` holds the counts and its tools alone. The statements screen's sheet, round, clock and Mark complete stand on `#es-status`, their ids unchanged. In shell.js `barLockups` puts the app's lockup in every `.bar-brand` (Sift's and Trace's screens call it once built) and `barFit` sets `.bar-fit-words` then `.bar-fit-tabs` on a title bar that overflows, watched by a ResizeObserver. Trajectories has Search (`tj-search`, the GETs' scopes) and Send feedback, which sends `gets`, a word of the collector's fixed list. Area 269 holds what the bars do, `thFace` switching both ways in node and the toolbar with its palette docked in a headless browser at 1280 and 720, the switch whole after Auto-saved and nothing overflowing. The app's windows are at least 720 wide (`min_inner_size(720.0, 480.0)` on every `WebviewWindowBuilder` in packaging/tauri's main.rs, 26 October 2026), so Idiograph's two-row bar, `.ds-tabs` on a row of its own, applies only below 720px in a browser, while Sift's `.sf-steps` take their own row at 760px and below.

### The band of option D and the statements screen's toolbar (6 November 2026)

Adam's option D of barsrethink's drawings (barsD): the path has no Home, the lockup being Home (`es-path-home`, `th-path-home`, `tj-path-home`, `cd-path-home`, `sf-path-home`, `sfs-path-home` and `tr-path-home` are gone, with `.ds-path-home` and `.ds-path-house`), and `distilToProject` is gone with the project's link. Since Adam's word on the shots (about 18:00 the same day) the project's name is the menu's button, the "..." after it gone: `#rail-project`, `#th-project`, `#tj-project`, `#cd-project`, Sift's `#sf-name` and `#sfs-name` and Trace's `#tr-name` are each a `button.ds-proj` with `aria-haspopup`, its words in `.ds-proj-name`, cut at 22em with their ellipsis, and a `.ds-chevron` after them, styled as the participant's chooser (`.ds-path .ds-proj` in style.css). `bandNameSet(id, name, title)` in shell.js writes the name and its tooltip, `pathProjectDraw` in distil.js calling it. The family's code holds the menu for all three apps (shell.js, "a project's menu"): `projectMenuHtml(rows)` draws an app's rows, `{ act, word, line, remove }`, a rule before Remove, `projectMenuWord` gives the shared words (Show in Finder or Explorer, Project settings, Remove from the app, `shell.project_menu.*`), `projectDotsHtml(name, rows)` a card's "..." and its menu, and `projectMenus(list, pick)` wires every card's dots in a list, `shutProjectMenus` shutting the others. The band's menu is one `#path-menu` in the family's page: `bandMenuWire(id, menu)` makes a name open it, `menu()` giving the rows and the pick of the project in front, `bandMenuOpen` draws it under the name and focuses its first item, and `bandMenuBoot` (run by `boot`) gives it the chooser's keys, Up and Down round its items and Esc back to the name, and shuts it on a press elsewhere or a resize. Idiograph's rows are its card's, `homeMenuRows(homeMenuItems(...))`, `homeMenuHtml` drawing them by `projectMenuHtml`, `homeMenus` wiring Home's cards through `projectMenus`, and `pathMenu` the band's for the project in front (`pathProject`, from `S.data`, `TH`, `TJ` or `CD`, the demo's by `DEMO_ID`). `homeMenuDo(act, id, name, p, inside)` is what an item does, and from the band `inside` is true, so `homeRemove` runs `goHome()` after its confirm, leaving the screen as Home does, a save that fails stopping there, before `/api/projects` `op: remove` and `loadLibrary`, so it ends on Home's picker without the project. Sift's are `siftMenuItems`, `siftMenuRows`, `siftMenuDo`, `siftRemove` and `siftBandMenu` in sift_settings.js and Trace's the `trace*` ones in trace.js: Show in Finder in the window alone, through the new `op: reveal` of `/api/sift-review` and `/api/trace-project` (`srv.reveal_folder`, the Finder or Explorer by `srv.SHOW_IN_FOLDER`, refused off a Mac or Windows and for a folder the list does not hold, no command or tool, as Idiograph's own reveal has none), Project settings, `openSettings('sift')` or `('trace')` with `SFA.want` or `TRP.want` putting that project first in `sfpLoad` and `trpLoad`, and Remove, `op: forget`, with `goHome()` first from inside. A gone folder's menu is Remove alone, and neither app has Share a copy or History. The card menus' styles moved from distil.css to style.css with `.pc-dots`, so Sift's and Trace's cards carry them. The way back to the table from a record (sifttable, Adam's choice of option C, 8 November 2026): since the name opens the menu, shell.js's `bandTableWire(id, { word, away(), go() })` gives a name button's id the table's own name (`sift.band.table`, Records, and `trace.band.table`, Claims), whether the screen is away from the table and the step back (`sfToTable`, `trToTable`), and `bandTableDraw(id)` makes or shows `#<id>-back`, a `button.ds-back` before the name (a left chevron and the word, tooltip and `aria-label` `shell.band.back_to`, Back to Records), hidden on the table, run from `sfBar` and `trDraw` each time the view changes. Sift's searches screen has no table and no link. Area 337 checks it in node.

The statements screen's toolbar is `#es-dock`, a `.th-dock.es-dock` under `#band`, holding `#es-palette`, a `.th-palette.es-palette`: `#es-palette-grip`, `#es-find` (`openFind`), `#es-prev` and `#es-next` (`move(-1)` and `move(1)`, as `Cmd + J` and `K`), and `#es-undo` and `#es-redo` (`esUndoTool`: `document.execCommand` while `nativeUndoOwns`, else `undoStep`, as `Cmd + Z` does), a press on any keeping the focus where it was. It docks and floats by the boards' own code, generalised for it: `thDocked`, `thPaletteHeld`, `thPaletteRoom`, `thPalettePlace(place, spec)`, `thPaletteFit(spec)` and `thPaletteGrab(e, spec)` take a spec, the boards' `TH_TOOLS` by default and the statements screen's `ES_TOOLS` in distil.js, which names its parts (`es-palette`, `es-dock`, the stage `#es-stage`, the `main.reading`, and `#es-dock-slot`), its settings, `es_palette_docked` (true by default) and `es_palette_place` (`idiograph_routes.py`, read and saved as the boards' `palette_docked` and `palette_place` are), the player as the foot it keeps clear of, `measureBand` as what it measures again and `esToolsSave` as how it keeps a change. Its spec is `alone`, so `#es-dock` hides while the toolbar floats, and `measureBand` counts the dock's height into `--band` while it shows. `esToolsBoot` wires it, and the case's open (`thPalettePlace(undefined, ES_TOOLS)` after `drawBand`) places it.

Every tab's words stand in a `.tab-w` with a hidden bold copy in `data-bold` (`.tab-w::after` in style.css, `visibility: hidden`, no height), so a tab is always as wide as its bold name: Idiograph's four rows in the markup, `tMarked` in i18n.js wording `data-bold` again for a thematic analysis project, and Sift's steps in `rvStepsHtml`. `#themes`, `#traj` and `#codes-screen` start their tabs 4px further right from 720px, where the statements bar starts them. On the boards `#th-board` and `#th-save` stand in a `.th-boardname` column, the save state under the name at 10.5px. Area 330 holds the band's order, the name's menu, its keys and Remove's ending in all three apps, Sift's and Trace's reveal, the toolbar's buttons and its place kept, the tabs' widths and the Edit menu's two items.

### Cards, menus and headings for the keyboard and a screen reader (8 November 2026)

a11yfix, on a11ycheck's findings. Every card is `.overlay` or `#search`, and shell.js opens and closes them one way: `show` calls `cardOpen` and `hide` calls `cardClose`, and `cardsWatch` (from `boot`) hears the cards an app's script shows by `hidden` itself, a MutationObserver on `hidden` under the body and one on the body's children for the cards Sift and Trace build. `cardLabel` gives the card (`cardBox`, the overlay's `.card`) `role="dialog"` where it has no role, `aria-modal="true"` and `aria-labelledby` its one `h1` or `h2`, or with several its `.kicker`. `cardOpen` keeps what had the focus (`CARDS.from`, else the last of `CARDS.seen`, the focus's last places), and after the opening script `cardFocusIn` puts the focus on the first field (`CARD_FIELDS`, the selected tab of Settings' categories among them) or on Done when the last input was a key (`CARDS.keyed`, set on keydown and cleared on pointerdown), and else on the card itself, `tabindex="-1"`, with no ring (`.card[tabindex="-1"]:focus`). `cardTab`, on the window before every other keydown, moves Tab and Shift + Tab round `cardStops` of the card in front (`cardTop`), a group of radios one stop, and leaves a menu of the card's own that stands outside it alone. `cardClose` gives the focus back to `CARDS.from` only when the focus was lost with the card, so an app's own refocus, the statements screen's field after Settings or Search, stands.

`menuKeys(e, menu, back)` is the band's menu's arrows made one for every menu: Down and Up round the ends, Home and End, Enter on a tick, Esc to `back`, a text box inside keeping its keys. `menuFirst` focuses a menu's first item and `menuRoles` gives it `role="menu"` and its buttons and ticks `menuitem`, `menuitemcheckbox` and `menuitemradio`. The project row's menu (distil.js `drawCards`), Home's cards' menus (`projectMenus`), the band's `#path-menu`, View (`#view-menu`, with Tab shutting it back to View) and the PETs bar's `#th-vmenu`, `#th-casemenu` and `#th-xmenu` (themes.js `thMenuKeys`, ahead of `thKeyDown`, so the canvas hears none of a menu's keys) use it, each focusing its first item when opened by Enter or Space (`e.detail === 0`).

`screenHeads`, run with `titleKeep`, gives each `.screen` that shows no `h1` a `h1.sr-only.screen-head` in the words of its bar's tab in front (`aria-current`), or the app's name on Home's picker. The project's rows' names are `h3` with `aria-level="2"`, Search has an `h2.sr-only`, and Sift's and Trace's filters an `h2.sr-only` over their groups. `#toast` stands inside `#toast-live`, `role="status"`, so a line said is heard, and Sift's and Trace's screens go before `#toast-live`. `#saved` is a status. The quote box is named `distil.pair.quote_n`, and the handle's words are `shell.grip.label` and `shell.grip.title`. The handle's `onkeydown` has a block body, so a key `gripKeys` does not take, Tab among them, is not cancelled. Area 339 checks the keys.

### The text layer

Since 28 October 2026 (i18ncore, Adam's ruling of that night: every on-screen word through one place, English only
for now, an American English overlay its first proof, and the same layer thematic analysis's terms will use) the
words the page shows come from a catalogue of messages by key, not from literals in the code. The shell's own words
moved first, `family/static/shell.js` and `family/static/page.html`. Everything else moves in builds 2 to 5, and until
then stays as it was. The language is English, so nothing on screen changed, and the pixel check below proves it.

**The files.** `static/i18n/<language>/<area>.json` in the family's folder and in each app's:
`family/static/i18n/en/shell.json` (the shell's scripts), `family/static/i18n/en/page.json` (the family's page), and
an app's own beside its code, `apps/idiograph/static/i18n/en/statements.json` for one. The boards' words (build 4,
i18nthemes) are in `apps/idiograph/static/i18n/en/themes.json` (themes.js: the PETs, GETs and LPETs boards),
`trajectories.json` beside it and `family/static/i18n/en/table.json` (the family's table), and the pixel check's
`boards` group shoots their screens. Every file of a language is
merged at load, so two builders moving different areas never edit one file. Each file is one JSON object of
messages, and every key starts with the file's name and a dot (`shell.updates.ready` in `shell.json`), so no two
files hold one key. A file's name is used once a language across every folder, since a build merges every
`static/` into one. English (`en`) is the base and British, its locale `en-GB`. Another language (`es`) or an
overlay (`en-US`, later TA's `en.ta`) is a folder of files of the same shape holding only the messages it changes,
whole sentences by key, never words swapped inside one. Idiograph's page markup, `idiograph.html`, is in
`apps/idiograph/static/i18n/en/page_idiograph.json` (keys by the page's parts, `page_idiograph.work.view`), and its
print views, the table of PETs and the GETs' table, trail and full set, in `page_print.json` beside it (i18npage).
Idiograph's own script, `distil.js` (the statements screen,
Home's Idiograph cards and pickers and the cards it opens), takes its words from `apps/idiograph/static/i18n/en/distil.json`
since build 3 (i18ndistil), keys under `distil.`, its checks in area 280.

**A message.** A whole sentence with named slots, `"{app} {version} is ready. Relaunch to use it."`, never pieces
joined in code, since word order changes between languages. A count is an object of plural forms, picked by the
slot `n`: `{"one": "{n} statement", "other": "{n} statements"}`, with `other` always there and any of CLDR's
`zero`, `two`, `few` and `many` a language needs. A key ending `_html` holds markup and goes into the page as it
is (`page.about.licence_html`). Every other message is text and is escaped.

**The language.** `language` in the settings, a tag such as `es` or `en-US`, saved by `/api/settings` when sent, an
empty one meaning the computer's own (`i18n.computer_language`: the Mac's first preferred language, Windows' user
locale, else `LC_ALL`, `LC_MESSAGES` or `LANG`, and `IDIOGRAPH_COMPUTER_LANGUAGE` before all of them, which the
suite sets to en-GB so its checks read British English on any computer). Settings' Language row sets it (below). A
lookup takes the most specific folder that exists, then the less specific, then English, then the key itself, so
`es-MX` reads `es` then `en`, and a message missing from a language shows in English. The locale the page writes
dates, lists and plurals in is that of the most specific folder found, so a computer in en-AU reads en-GB, having no
folder of its own. The page's `lang` follows it.

**Python, `family/i18n.py`.** `i18n.t("key", {"name": value})` (or `t("key", name=value)`) in the run's language,
which the server sets (`i18n.LANGUAGE`, `server.page_language`, and `i18n.ROOTS`, the folders of the apps the run
serves and the family's). `server.assembled` fills the page as it puts it together (`i18n.fill`): each
`{{key}}` marker in the markup becomes its message, its slots filled from `{app}`, the app's name, and
`<!--i18n-->` becomes one inline script, `var I18N = {language, locale, messages}`, the merged catalogue the scripts
read. So the first paint is in the chosen language, and every check reading the page through `support.page_text`
or `support.every_page` reads English. A key nowhere is named once on stderr.

**Scripts, `family/static/i18n.js`,** loaded before every other script. `t('key', { name: value })`, the plural by
`Intl.PluralRules` in the catalogue's locale, a key nowhere showing as itself and named once in the console.
`tDate(when, options)` writes a date with `Intl.DateTimeFormat`'s own options in that locale, with `timeZone: 'UTC'`
for a time read as it is written. `tDay(iso)` is a YYYY-MM-DD day at midnight UTC, for that. `tList(items)` joins a
list as the locale joins one, "a, b and c" in English. The three hand-written month tables (table.js's
`tbDayWords`, distil.js's `whenOf` and the days' tooltips, themes.js's history and review lines) go through `tDate`
since, the same English out of them. CLDR's British English writes September short as "Sept", and the app's
English has always said "Sep", so `I18N_DATE_FIX` puts it back for en-GB alone.

**Writing a string from now on.** A word a person reads is never a literal in a script or the markup:

1. Pick the area's file, or make one, `<folder>/static/i18n/en/<area>.json`, and a key under its name in lowercase
   words joined by dots, `statements.round.done`.
2. Write the whole sentence there, its values as named slots, a count's forms under `one` and `other`.
3. In a script, `t('statements.round.done', { n })`. In markup, `{{statements.round.done}}` (attributes too). In the
   server, `i18n.t("statements.round.done", n=n)`. Write the key as a literal, never built from pieces, so the check
   below finds it.
4. Dates through `tDate`, lists through `tList`, never a month or weekday table and never `', '.join` for a sentence.

**American English and the Language row** (i18nus, the seventh build, 28 October 2026). The first overlay is
`en-US`: `family/static/i18n/en-US/page.json` and `apps/idiograph/static/i18n/en-US/` (`page_idiograph.json`,
`distil.json`, `themes.json`, `server.json`), 30 messages in all, each a whole sentence by key holding only what
American English writes otherwise. Spelling: color, center, capitalized, labeled, anymore, Acknowledgments. Words:
Select for Tick a participant, checked for ticked, quotation marks for inverted commas, apartment for flat, Moving
around, Eggplant for the colour Aubergine. No word for the bin: since i18nus2 English says Set aside for it, as the
boards' sidebar does (the Shortcuts card's X, a GET's facts, and the hidden bin's button and pile, which the code
still measures), so the overlay needs no Trash. Dates come out in American order through `tDate`, the locale being en-US, and so do a
time of day through `tTime` (Updates' last check, 2:05 PM since fmtsweep, 02:05 PM before) and a list's comma before and. The list with British and American side by side is in the build's
`en-US.md`. What Python writes as a date (a print view's head, the notes file's Exported on) goes through `family/formats.py`
since fmtsweep (below), so American English writes it month first unless Dates says otherwise. The window's menus hold no word that differs, so there is no `menus.json`
in `en-US`. Sift's own words are in its catalogue since 1 November (siftlang, below), and its en-US overlay since i18nleft3, `apps/sift/static/i18n/en-US/page_sift.json`, percent its one true difference of spelling.
Trace has its own overlay since i18nleft2, `apps/trace/static/i18n/en-US/` (`trace.json`, `page_trace.json`), judgment
for judgement, five messages.

Under Settings, `Language` (under General until fmtcore, under Language and formats since) has three rows: Same as this computer, named as the app reads
it (`I18N.computer`, the locale `i18n.script` gives the computer's language, so a computer in French says English,
UK), English (UK) (`en-GB`) and English (US) (`en-US`). Ticking one sends `{language}` alone to `/api/settings`,
which writes that key alone (as Appearance's rows do), keeps what is typed and not saved (`savePending`, refusing
with "Not saved, so the language did not change." when it cannot), and loads the page again, which comes back on
its screen as any reload does and opens Settings on Language and formats again (`languageAgain`, a stamp in sessionStorage
taken once within a minute). The server reads the setting for each page, so the new language holds with no
restart. The window's menus are built at its start (`words.rs`), so a language whose menus differ would take
them at the next start. Area 283 checks it.

**Language and formats** (fmtcore, 28 October 2026, Adam's B and wording 1 of that day, the plan
`formats-plan.md` in the harness's history). Settings has a page of its own after General in all three apps,
`pane-formats` (`formats` in `PANES_BY_APP`), in the family's `page.html`: the Language rows above, moved there
from General, the line under them, then Dates, Times of day and Numbers. Each format is a key of `formats` in the
settings, beside `language`: `dates` (`dmy`, `mdy`, `ymd`), `time` (`24`, `12`) and `numbers` (`comma`, `point`,
`space`, `apostrophe`), each "" for the computer's own (`i18n.FORMATS`). `/api/settings` with `{formats: {...}}`
alone writes those keys and keeps the rest, and refuses a key or a choice that is not one by name
(`errors.formats_choice`), so an agent sets them the way the rows do. A row ticked sends its key alone, keeps what
is typed first, and loads the page again, Settings opening on this page again (`languageAgain`). The server puts
the chosen formats and the computer's own into the page's `I18N` beside the language (`formats`,
`computer_formats`, `i18n.script`), read afresh for each page.

The computer's own: the page's `Intl` sees only the language, never the Mac's Date format, Number format and
24-hour time nor Windows' Region formats. So the window (`formats.rs`) asks the system to write 28 October 2026,
14:05 and 1234.5 its own way, on a Mac through Foundation's NSDateFormatter (short date, short time) and
NSNumberFormatter (decimal) in `NSLocale.autoupdatingCurrentLocale`, on Windows through `GetDateFormatEx`
(DATE_SHORTDATE), `GetTimeFormatEx` (TIME_NOSECONDS) and `GetNumberFormatEx` for the user's locale, overrides
included, and hands them to the server it starts in `IDIOGRAPH_COMPUTER_FORMATS`, `{"date": "28/10/2026",
"time": "14:05", "number": "1,234.5"}`, unless its own environment names them already. `i18n.computer_formats`
maps each to the nearest choice (`nearest_date`: the year first is ymd, the month before the day mdy, else dmy;
`nearest_time`: 14 is 24-hour; `nearest_number`: a decimal comma with points is `point`, with a space or none
`space`, a decimal point with an apostrophe `apostrophe`, else `comma`). With none, as in a browser, each is ""
and the page writes as its language's locale does, as before. The suite sets British formats as it sets the
computer's language.

In the scripts (`i18n.js`): `tFormat(kind)` is the setting's, else the computer's, else "". `tDate` takes its
order from it: where the language already writes a date in that order its own writing stands ("28 de octubre de
2026"), else its parts (`formatToParts`, the month's name still the language's) are put in that order, 28
October 2026 or October 28, 2026, and `ymd` is all numbers, 2026-10-28, 10-28 with no year. An hour asked of
`tDate` takes the time format's clock. `tTime(when)` is a time of day, 14:05, or 2:05 pm with no leading zero, am
and pm the language's. `tNum(n, options)` is Intl's number in the language with the format's marks between the
thousands and before the decimals (1,234.5, 1.234,5, 1 234,5 with a no-break space, 1’234.5). Every place that
writes a date through `tDate` follows at once: the statements screen's Complete date, the Home cards' days, the
boards' History, Projects' agents line, the family's table and Updates' last check. Timecodes are the project's
own (tcproject).

**The sweep** (fmtsweep, 28 October 2026). Every other place moved onto the formats. On screen: themes.js's
`thClockOf` is `tTime` (a board's History and its stale banner), distil.js's `whenOf` writes
Mark complete's time through `tTime` read in UTC as the file wrote it, and Updates' last check (`updWhen`) through
`tTime`, so twelve-hour has no leading zero. Sift's review day (`reviewDay`), its search days (`sfsDay`,
`sfsRunWords`) go through `tDate` in place of `toLocaleDateString('en-GB')`, its counts (cited by, the truncation
table) and Search's "20 of 1,284" through `tNum` in place of `toLocaleString('en-GB')`, and the numbers with
decimals in a sentence (the kappa, the model's seconds on the bench in Idiograph and Sift) through `tNum` with
their decimals fixed in place of `toFixed`. Sift's sentences themselves are in the catalogue since 1 November (siftlang). Lengths of
time: distil.js's `formatMinutes` is the one form, the end card's time left and the break's line (`haulTime`)
both, from `distil.length.minutes`, `distil.length.hours` and `distil.length.hours_minutes`, 45 min, 1 h, 1 h 25
min (the end card said 85 min and 1 h 30 before). The round's clock, the player's and every timecode stay as
they are, the project's own (tcproject).

The server: `family/formats.py`, `date_words(when, short=False)`, writes a day in the dates choice the settings
hold (`i18n.CHOSEN_FORMATS`), else the computer's own (`i18n.computer_formats`), else the language's own (`OWN`,
month first for en-US, else day first): 28 October 2026, October 28, 2026 or 2026-10-28, and short 4 Oct 2026.
The months' names are the language's, `family/static/i18n/en/dates.json` (`dates.month.*`, `dates.mon.*`), and the
sentence putting the three together too (`dates.dmy`, `dates.mdy`), so a language words it its own way. It writes
the print views' foot (`themes_print.when_printed`, the GETs' through it), and the interviewer notes file's
Exported on (`export.export_notes`). What stays as it was: the
saved files and `--json` (ISO), backups' and file names' forms, a revision's name and provenance already written,
and the command line's and MCP's human lines, English for agents. The hold card's Asked line takes its month from
`dates.month.*` since i18nleft. Area 288 checks a
sample of each kind of place in English (UK) and (US).

The line under Language, "Help translate {app} into your language.", the whole of it the link, opens
`/translating` in a window of the app's own: `docs/translating.md`, every bundle's (`app_identity.FILES["family"]`),
read by the manual's reader (`server.translating_page`, `manual_page(..., lists=True)`, which reads lines starting
"- " or "1. " as lists). The repository is public from November 2026, so the link could point at the page on
GitHub, and stays the app's own window, which opens offline too. Area 285 checks
the formats and the line.

**The server's words and the window's** (i18nserver, the fifth build): Idiograph's refusals and the lines its routes
send the page in `apps/idiograph/static/i18n/en/server.json`, the family server's (server.py, locks, search, the AI
calls, text files) in `family/static/i18n/en/errors.json`, the exports' headings (the statements CSV, the interviewer
notes file, Not placed, Stacked under it and the GETs' marks) in `apps/idiograph/static/i18n/en/exports.json`, and the
Mac and Windows window's menus, messages and save panel kinds in `family/static/i18n/en/menus.json`, which the
window's `words.rs` builds in for English and reads beside the frozen server for the language the settings choose
(`t`, `t_app` for the `{app}` slot, `t_with`). A refusal a module kept as a constant that other modules or checks name
(`themes.GONE`, `locks.BUSY`) is read through the module's `__getattr__`, so it is in the run's language when raised,
never frozen at import. The lines the window reads from the server's output ("is closed.", "quit by itself") stay
English. The command line and MCP keep English, their runs never setting a language. Setup's words stay in NSIS's own
language file, `windows/English.nsh`, which a language joins as its own `.nsh` in tauri.conf.json, since Setup runs
before the app. A list of names inside a refusal goes through Python's tList, `formats.list_words`, since
i18ncodes (below).

**Codes, not English, and Python's lists** (i18ncodes, 31 October 2026, Adam by dialog: make Idiograph ready for
a second language, nothing translated yet). The page and the server's modules never decide by a refusal's words,
which change with the language. A refusal a script reacts to carries a code beside its words, one of
`family/errors.py`'s `CODES`: `WorkbookError(words, code="unknown_op")`, `errors.refusal(exc)` making the answer
`{"error": words, "code": "unknown_op"}` in `server._run`, and the words staying for the person, agents and logs.
`no_endpoint` is no such route (both 404s of `do_GET` and `do_POST`). `unknown_op` is no such op, from the
boards' and the GETs' ops (`themes.board_op`, `themes.version_op`, `gets.board_op`, `gets.version_op`,
`api_themes_versions`, `api_gets_cases`), `api_rows` and the AI help's two routes (answered as a dict with
`code`). `board_changed_outside` is a save refused over an agent's change (`themes.save`). `file_not_held` is a
.qdpx the card sent before and the server no longer holds (`qdpx_held`). `busy` is the lock (`locks.held`), which
Sift's `refresh_prisma` and its numbers' save test, and `zotero_storage_full` Sift's Zotero upload stopping.
`SearchError`'s HTTP status, `code` until then, is `status`. On the page `api` puts the answer's code on the
error as `err.code`, `refusedAs(err, code)` tests it, `needsRestart` is `refusedAs(err, 'no_endpoint')`, and
`olderServer()` is the error a feature throws when a server answers without what a newer page needs. So
`thSaveOnce` ticks the corner on `board_changed_outside`, the review's ask, reply and revise, Add every
sub-theme, a GETs colour and a trim's undo say to restart on `unknown_op` (the constants `TH_REVIEW_OFF`,
`TH_OUTSIDE_REFUSED`, `GT_OLD_OP`, `OLD_ROWS` and `NO_ENDPOINT` gone), and `qdRead` sends the file whole again on
`file_not_held` (`distil.qd.gone`, the page's copy of the server's line, gone). A server from before sends no
code, so its refusals read as any other until it is restarted. The ways back name their step by key (above).
Sift's run's `follows` carries its `number` beside its `label` and a run's row `set_aside` beside its note, so
the page reads neither out of English words, a run file from before keeping the note's words.

Python's tList is `formats.list_words(items, kind="and")`, its tDate `formats.date_words` (fmtsweep): the
patterns are CLDR's four for "and" and "or", two items, then the first, each middle and the last pair of three
or more, in `family/static/i18n/en/lists.json` (`lists.and.two`, `lists.and.start`, `lists.and.middle`,
`lists.and.end`, `lists.or.*`) and `en-US/lists.json` for American English's comma before and. They come out as
the page's `tList` (Intl.ListFormat) writes them, and join the names and counts of the server's refusals and
lines (the timepoints held, a name matching several, participants not in a project, a shared pseudonym, a merged
passage's carries, an import's choices, GETs waiting, a send's GETs), `gets.said_list` among them. A list of three
names reads "A, B and C" where it read "A and B and C". What stays English is as before: the command line's and
MCP's lines, the uncatalogued words of the hold card, the AI's change lines and Sift's own. Area 307 checks it,
on a made-up language whose catalogue words every coded refusal otherwise.

**What i18ncodes left** (i18nleft, 1 November 2026, nothing in English changed). The untitled label: the file keeps
the English word `Untitled` for a label with no title, as it keeps the workbook's headings, in the page
(`TH_UNTITLED_SAVED`) and in Python (`themes.UNTITLED`). themes.js keeps a label through `thLabelKept` (blank, or the
language's word typed, is kept as `Untitled`), shows it through `thLabelShown` (the file's `Untitled` in the language's
word, `themes.untitled`) and asks `thUntitled` (blank, `Untitled` or the language's word), so a board saved in English
reads as untitled in every language and a name suggestion never sends it as a title. A board a page saved in another
language before this kept that language's word, which reads as a title until the label is named. The hold card's
words the server says when it shows a hold (`holds.shown`): the question, the waiting line, the Declined line, the
agent unnamed (`server.holds_agent`, `server.holds_agent_inside`), the Asked line with its month from `dates.month.*`,
and whose files changed (`changed_what`, its parts `server.holds_part_*` joined by `formats.list_words`, so three
read "A, B and C"). What a hold keeps in its file when the agent asks, `what`, `done`, `kept` and `would_do`, is
written in the agent's run, English as the command line is, and shows as it was written. The AI's words for the
person, `apps/idiograph/static/i18n/en/themes_ai.json`: every refusal of `themes_ai` (`SAID`, read inside the module
through `_w` and from others as the module's names, `themes_ai.OFF`, through its `__getattr__`), the revision
kept before a change (`themes_ai.revision_before`, `BEFORE` its head for the command line's cut), the lines when
something went for room (`themes_ai.room.*`) and the change lines a change through the API writes (`change_line`,
each change a sentence part with its slots, joined by `formats.list_words`, the small numbers `themes_ai.number.*` through
`_count_said`, the units `themes_ai.count.*`). The prompts stay English and keep `_count`. `NOT_JSON` is read from
`ai_suggest` when said, where it was frozen at import. The print title: the canvas's page title,
`themes.canvas.page_title`, and the print views' and the canvas page's `lang` the run's locale
(`themes_print.page_lang`, the page's own `lang`). `keyName` above. Trace's own page and script: its markup's words in
`apps/trace/static/i18n/en/page_trace.json` and trace.js's in `trace.json`, keys under `trace.`. What is left: Sift's
page and scripts (sift.html, sift.js, sift_search.js, sift_settings.js, several hundred sentences) and Sift's and Trace's
Python, the History's revision names (`themes.CANVAS_KEPT` and `RELOAD_KEPT`, which a check compares as stored
text, "Before restoring", "Before {who}'s changes came in", a statement's edit line), the steps of undo's own names in
themes.js, which no screen shows, and an en-US overlay for Trace (judgment). Area 307's part E checks the untitled
label, the keys' names, a change line and the hold card in the made-up language.

**What i18nleft left** (i18nleft2, 1 November 2026, nothing in English changed). The History's own names: a
revision the app names itself carries a mark of what it is, `kind`, and the words that fill it, `slots`, beside its
English `name` (`themes.REVISION_SAID`, `REVISION_SLOTS`): `canvas_kept` and `reload_kept` (`themes.CANVAS_KEPT`,
`RELOAD_KEPT`), `before_restoring` with `when`, `before_copy` with `label` and `board` and `before_copy_revision`
with `when` too, `before_changes` with `who` (a participant's changes into the GETs), `statement_edited` with `who`,
`old` and `new` and `statement_edited_bare`, and `brought_in` with `file`. `themes.revision_name(kind, **slots)`
makes the English, from `themes.revision.named.<kind>` in English and IPA's words whatever the run's language, as a
`RevisionName`, a str that carries its kind and slots through code that passes names along as text (a statement's
edit line from the route to every board), and `add_revision` keeps them, or takes `kind` and `slots` itself.
`revision_mark` gives a revision's kind and slots, its own or, for one kept before marks, read back from its English
name by each kind's sentence (most slots first), and code compares the kind (`keep_canvas` finds the canvas kept
before by it). `revision_summary` puts both in what the History tab, `board history` and `gets history` read, and
themes.js shows the name through `thRevisionSaid` (`TH_REVISION_SAID`), in the History, the revision on view's tip
and the lines after Save a revision and Restore. A revision named by hand, an agent's and the AI's "Before: " and
his request carry none and show as named. undo's steps: every name themes.js gives a step (`thDone`, `thStep`) is
`themes.step.*`, a count by its plural, Align and Spread through `TH_ALIGN_STEP`, with en-US's center, recolored,
checked and check mark. Trace's en-US overlay, above. A hold's own words: `said_of` and `would_lines` make each
sentence a key of `apps/idiograph/static/i18n/en/holds.json` and its slots (`holds.t`), a slot itself such a pair
or the agent's or the command line's own words kept as they came (a change line, the project send's dry-run lines,
the names of the boards a write keeps, joined by "and"), `upper` and `lead` its capital and indent. The hold keeps
the English in `what`, `done`, `kept` and `would_do`, as the command line and MCP read them and `differs` and
`carry` compare them, and the keys under `said`. `shown` says them in the reader's language through `text_of`
(`said_now`), and a hold kept before keys shows its English as written. A fresh dry run (`dry_now`) gives both, and
`take_would` keeps them together, dropping the keys when the dry run refused. Left: Trace's Python, as before (Sift's moved the same night, below), a revision's `when` (the clock and an English month, as `when_said` writes it), and
the thematic analysis words for these sentences (none in `en.ta`, so a TA project reads them as IPA's). Area 307's
part F checks an old revision found by its English, a new one's mark, the History's names, undo's steps and a
hold's lines in the made-up language and an older hold as written (its check of Trace's judgment, one
overlay word, went on 2 November, testspeed).
**Sift's own words** (siftlang, 1 November 2026, Adam's yes of that night, nothing in English changed). Sift's markup,
`sift.html`, is in `apps/sift/static/i18n/en/page_sift.json` (keys by the page's parts, `page_sift.screens.export`),
sift.js's words in `sift.json` (`sift.`), sift_search.js's in `sift_search.json` (the Search strategy screen, whose
markup the script builds, `sift_search.screen.`, and Settings' Databases) and sift_settings.js's in
`sift_settings.json`. A count is a plural message where the code joined "1 record" or a plural's s, a list of names
goes through `tList` (sift.js's `sfAnd`, sift_search.js's `sfsFilled`), and the question cards say by a flag that a
Yes removes (`sfAsk`'s and `sfsAsk`'s `removes`) where they read it off the button's English word. Two pieces of
sift.js that bound a local `t`, the second screener's card's tallies and their side of a record, name it `ts` and
`th`. Sift's Python says its words through `sift_words.t`, the family's `i18n.t` with Sift's folder always among the
roots, so a command, a check or another app's run that calls a Sift module reads Sift's sentences, in
`sift_server.json` (`sift_server.`): every refusal of sift.py, sift_routes.py, sift_search.py, sift_second.py,
sift_zotero.py, sift_oa.py and sift_ai.py, the lines they send the page (a key's check, Zotero's preview and its
end, Find open-access PDFs' reasons, a DOI looked up, the second screener's waits), the PRISMA flow's boxes and the
second screener's box in it, the filters' Matched in lines, the study's suggestions, a database's notes and rewrites
under Searches, the field scopes Search in offers (`sift_search.scope_said`) and Search's places (`sift_find`). A
word another module or a check names, `sift_routes.NOT_OPENED`, `sift_second.NOT_OURS`, `sift_ai.SIFT_OFF`,
`sift_oa.NO_EMAIL`, `sift_zotero.NO_KEY`, `sift_find.NO_SIFT`, `sift_search.NO_TERM`, `STALE_PLAN`,
`PROQUEST_STAR` and `PHRASE_TRUNCATION`, is read in the run's language through the module's `__getattr__` (`SAID`,
`_w` inside it), as themes_ai's are. The stage in a sentence is `sift.stage_said`, the plan's scopes
`sift_search.scope_said`, and `sift.and_join` and `or_join` go through `formats.list_words`. What a file keeps stays
as it was written, in English: the CSV's and the log's words (`STAGE_WORDS`, `SHOWN_WORDS`, a run's and a log's
notes, `NO_DOIS`, a run's `said`), the second screener's workbooks, which Sift reads back, the counts CSV's measures,
search_plan.md, which a plan's version keeps as its text, and the run folders' and files' names. Left as they were:
the command line's and MCP's lines, the prompts, the language and country names a record's columns show (lists of
names, for Intl or CLDR later), a run's name with its day (`sift_search.run_said`, `sift.day_words`) and a
publication type's word, which a kept filter holds as its value. A test harness that runs a piece of Sift's scripts
in node gets the text layer from a preload the suite names in NODE_OPTIONS (`support.node_text_layer`), as the page
loads i18n.js first, and `support.text` reads Sift's scripts with each word taken by key alone put back as English
(`support.english_js`), so the checks that read the scripts' own text read them as before. Area 126's part G checks a
made-up language on a Sift screen, in sift.js, in a refusal, a module's word and the PRISMA flow, and English as
before. The pixel check's `sift-strategy` group shoots Search strategy, its end and its Mark as registered card, on a
Sift server with `--sift` naming a project with searches.

**The text layer's remainder** (i18nleft3, 2 November 2026, nothing in English changed but a list of three or more
names). A revision's time: `themes.when_said` writes it as the History's `thWhen` does, the clock by
`formats.clock_words` (the time format, 14:05 or 2:05 pm, `dates.clock.am` and `pm`, AM and PM in en-US), a day
of this year by `formats.day_words` (1 October, October 1 or 10-01, `dates.dm` and `dates.md`) and of another year
by `date_words`, put together by `themes.history.when`, in the formats in force and the run's language. `lang` on
`chosen`, `date_words`, `day_words`, `clock_words`, `list_words` and `when_said` names a fixed language whose own
formats alone are used, for words a file keeps. A revision named with a time keeps it as ISO beside its slots,
`when_at` (`themes.WHEN_AT`, `slots_kept`, given to `revision_name` in place of `when`), its English name still
"Before restoring 1 October 12:04" in English's own formats, and `thRevisionSaid` says the time from `when_at` in
the page's language and formats as it read when the revision was made. A revision from before keeps its words. A
hold keeps a time as `holds.when_of` (its ISO and the moment of the dry run) and names as `holds.names_of`, said by
`text_of` when the card shows them (the restore's "its revision of", a turn write's boards, "A, B and C" where it
read "A and B and C"), and the Asked line's day and clock through `day_words` and `clock_words`
(`server.holds_asked_on` takes `day` alone). `holds.shown(h, root)` says a hold in the words of its project's
method (`method_at`). The family's other apps on Home, `#family-h`, join through `tList`, Open and Download in
`shell.family.*`. Thematic analysis's words: `en.ta/holds.json` (the themes board, codes, themes, extracts),
`en.ta/themes.json` for a statement's edit line in the History (`themes.revision.named.statement_edited`, `_bare`)
and the undo steps that name statements, quotes, sub-themes or the GET table, and `en.ta/cli.json` for the
command line's GETs board lines (`cli.gets.*`: new, duplicate, rename, note, canvas, current, delete, revision,
restore and take). Sift's en-US overlay, above. Left: the Rename card's lines (`idiograph_routes.rename_plan`,
`sidecars_said`, `project_said`), English and uncatalogued, the family apps' lines on Home (`app_identity`'s
`line`), the AI's made-on note's day, which a board note keeps, and the command line's other English lines. Area
307's part G checks them.

**The last leftovers** (i18nleft4, 2 November 2026, nothing in English changed). The Rename card's lines,
`server.rename.*` in `server.json` (`passages_said`, `books_said`, `sidecars_said`, `project_said` and
`rename_plan`'s own), the passages of two sheets or more joined by `formats.list_words`, and in a thematic analysis
project "The project's themes" (`en.ta/server.json`). The family's lines on Home, `shell.family.line.<app>`
(`server.family_line`), `app_identity`'s `line` kept as the English. The command line's lines of the three apps and
the family's: Idiograph's in `cli.json` (keys under `cli.<command>.`, a line two commands say under `cli.said.`, a
count `cli.n.<word>` in place of `cli.plural`), the family's `family/static/i18n/en/family_cli.json`, Sift's
`sift_cli.json` through `sift_words.t` and Trace's `trace_cli.json`. A module's words other modules and the checks
name (`idiograph_cli.PRIVATE`, `cli.NO_WORDS`, `sift_cli.NO_YES`) are its `SAID`, read through its `__getattr__`,
`_w` inside it. The lines were moved by a script that turns each f-string into its message and named slots, so the
English is the old one by construction, and each was compared old and new before landing. About a third are pieces
the code still joins ("  Boards: " before a list), keys of their own until a language needs whole sentences there.
Thematic analysis's words for 59 of them in `en.ta/cli.json` (codes, extracts, the themes board and file). Trace's
refusals and its card's line are in `apps/trace/static/i18n/en/trace_server.json` (`trace_claims`' and
`trace_routes`' words, through their `__getattr__`). What stays English in code, and why: argparse's help and each
CLI's description, which are the agents' own interface as the prompts are; what a file keeps (a board's note made in
a conversation, a revision's name, a deleted board's archive name, `NOT_PLACED` as a card's place); the lines of
`project send`'s dry run that the hold card reads back (`holds.would_lines`: "It would write", "It would hold:",
`UID_DRY`); `cli.when_said`, the agents' dates; Sift's and Trace's `SEARCH_REFUSED`, handed over once when the
command line starts; Trace's log lines (`judge_words`, `check_words`), citations' "et al." and "in press", the AI's
passages' lines and its prompts; and a single word a line shows alone ("none"). Area 307's part H checks it.

**The long texts** (i18nguide, the sixth build): the guidance rails (`apps/idiograph/guidance.md`, `themes_guidance.md`, and thematic analysis's `ta_guidance.md` and `ta_themes_guidance.md`)
and What's new (`docs/whats-new.md`) are whole files, not catalogue keys. A language's own sits beside the English
file with its tag before the suffix, `guidance.es.md`, `whats-new.es.md`, and `i18n.long_text(path)` picks the most
specific tag the run's language has (`es-MX`, then `es`) and else the English file itself. The rail's readers
(`guidance_sections`, `guidance_examples`, `guidance_framing`, `themes_guidance`) and `server.whats_new_source` go
through it, so an untranslated language shows English. `pet_guidance.md` rides in the AI prompts and stays English.
`release.py` reads the English What's new for the updater and takes no language. No language's file ships yet, and a
builder adding one lists it in `app_identity` beside its English file so the bundle carries it. Area 284.

**A project's method** (tadraw, 31 October 2026, thematic analysis's phase one, drawn for Adam and not landed until
he approves the pictures). The project file's `method`, "ipa" or "ta", chosen on New project (`np-method`, sent as
`method` with Make, `routes.method_asked`) and fixed after: `routes.read_project` answers it, IPA's for a file with
none (`routes.method_of`), `api_project` refuses one that is not the file's (`method.refused_fixed`), `make_project`
writes it only into a project file it makes and refuses another than a file there holds, and `write_timepoints`
refuses two or more in a TA project. The CLI's `project new --method`, `project set --method` (refused when it
differs), `project show` and `cases` carry it, MCP's `project_new`, `project_set` and `project_show` the same, and
`method` is one of `cli.PLAIN`'s keys. The method switch's own words are in `apps/idiograph/static/i18n/en/method.json`.

The words: a method other than IPA is a catalogue folder beside its language's, `<language>.<method>`, so
`apps/idiograph/static/i18n/en.ta/` (`distil.json`, `themes.json`, `page_idiograph.json`) holds the whole sentences
thematic analysis says otherwise, each key the base's own under its file's name, with no slot English lacks (it may
leave one out). `i18n.languages` skips such a folder, `i18n.method_chain` takes `en-US.ta` then `en.ta` before the
language's own chain, and `i18n.t(key, method="ta")` and `i18n.messages(tag, roots, method)` read through it.
`i18n.script` puts each method's sentences in the page beside the base's, `I18N.methods.ta`, and `I18N.marked`, the
markup's keys whose words a method changes, which `fill` gathers as it fills the markers. In the scripts,
`tMethod(method)` sets the method in front (`startCase` from the case's project, `themesOpen` from `TH.project`, Home's
project page from its project, IPA's elsewhere), `t()` takes its sentence before the base's, and the markup's marked
words are worded again in it (`tMarked`, found as i18n.js loads, after the markup and before any other script
draws). `tIn(method, fn)` draws one thing in a method, each project card on Home in its own, and `tBase` reads IPA's.
`html[data-method]` carries the method for CSS. In a TA project `dsStages` gives the statements screen and the GETs
board alone (Codes and Themes), the project page's rows the coding half alone (`.pcard.ta`), Settings, Projects no PET
labels and no timepoints and Settings no PETs category, the statements screen its own rail (`guideRail`, tarail), no nudges
(`runNudges`) and no AI (`aiPage` and `aiFor` in shell.js, `thAiOn`, the switch itself untouched), and the GETs board no PET marks on its participants
(`thTa`), no "placed" badges, no minimum (0) and no Mark complete in its menu (`gtMenuFoot`). Area 306 checks it.

Thematic analysis's guidance (tarail, 3 November 2026). `ta_guidance.md` is the Coding screen's rail in the format of
`guidance.md`, read by `rail_of` and sent as `/api/guidance`'s `ta`, and `guideRail` in distil.js draws the rail
of the method in front as the screen opens (lines, examples, framing, craft prompts), hiding `#guide-examples`, the
personal examples, in a TA project. Add a code's field keeps its placeholder, Add a code, and no craft prompt
(Adam, 3 November). `ta_themes_guidance.md` is the Themes board's Guidance tab in the format of `themes_guidance.md`,
sent by `gets_reply` with `guidance_ta`. en.ta words the rail's title Coding guidance and the tab's foot. Both
files ship through `app_identity.FILES`. `themesOpen` calls `aiPage` again once `tMethod` has the board's project's
method, and `thTabsDraw` hides every tab `thTabsOf` leaves out, so a TA board opened after an IPA screen with AI
features on shows no AI control (taai's finding). Area 324 checks it.

Thematic analysis's AI (taaibuild, 3 November 2026, Adam's Coding A and Themes A, the prompts as taai drafted them
in its prompts.md). `apps/idiograph/ta_ai.py` holds the prompt and its reader, in English as IPA's are. IPA's AI
stays away in a TA project (`aiPage`, `aiFor`, `thAiOn` as before), and TA's draws by its own test: `aiTaFor(cfg,
feature)` in shell.js, true only in a TA project with AI features and the feature's switch on. **Codes for an extract:** AI suggest beside an extract's Codes (`cxAiButton`, `cxAiAsk`, `cxAiHtml` in
codes.js, `CX.ai` by the extract's words, set aside when another passage is in front, `cxAiFresh`) posts
`/api/codes-suggest` with the passage, the interviewer's before it, the time, the name, the extract and its codes.
`api_codes_suggest` refuses with AI features or the `statements` switch off and in an IPA project (`codes_root`),
sends one call through `srv.ai_route`, the system prompt carrying the question, lines 3 to 9 of `ta_guidance.md`'s
rail and the code list with counts and descriptions (300 at most), and `ta_ai.parse_codes` keeps up to three listed
codes under their own spelling with their counts and up to two new names, dropping a name the list lacks and a code
on the extract. One pass, with no critic. A click on one is `cxPut`, Add a code's own, so the code lands through
the passage's save with no mark of the AI, and nothing is kept of the suggestions. The Themes board's review went
on 11 November 2026 (aiout): `/api/gets-ai` refuses every op in a TA project, and a board's rounds from before stay
in the GETs file unread. Area 326 checks it.

The server in a method's words (tagaps, 1 November 2026). `i18n.NOW_METHOD`, a context variable, holds the method a
request or a command runs in, and `i18n.t` with no `method` of its own reads through it (`i18n.in_method`,
`i18n.method_now`). The server sets it for every route in `routes.route_scope`, from the project the body names
(`routes.request_method`: its `workbook` or `path`, else `root` by id or folder, else `folder`, else the only
project), the print views with it since they run in that scope, and the command line in `idiograph_cli.scope_of`
from the project's root, so a refusal, a status line, an export's headings and file name and a print view read in
TA's words in a TA project and IPA's everywhere else. TA's sentences for them are in `en.ta/server.json`,
`exports.json` and `page_print.json`, beside the page's. The print (`gets_print`): in a TA project (`gets_print.ta`)
no PETs line under the head or by a participant's name, the full set with no PET tables, and a GET's trail in four
columns, the PET column left out (`four_of`, `.tr-four`, in the print's CSS and themes.css), unless a theme holds a
PET brought from elsewhere. Save as PDF's and `gets export`'s name take `print_pdf.gets_what`, the print view's
own words, and the codes' CSV its name from `exports.csv_name` ("<case> - All Codes.csv"). The board menu's
Export is back in a TA project, its tooltip read when it is drawn. Search (`idiograph_find.distil_found`) reads no
case's themes file in a TA project, which has no PETs board to open.

The code list (codes, 2 November 2026, Adam's ruling of 28 October, choice 1 (a), and his choice of the drawings
of 2 November: coding A, the code list as its own tab, the board's code cards). `apps/idiograph/codes.py`. A code is
a label many coded extracts share, each extract still one quote: in the workbook a code on an extract is a passage's
statement, the code's name in column C, with the extract as its quote in column F, so two codes on one extract are
two pairs with the same quote and every reader of statements and quotes reads them as before. The list is
`idiograph-codes.json` at the project's root, only in a thematic analysis project: `schema`, `created`, `updated`,
`codes` (each `id`, `k1` on, `name`, `description`), `history` (each change's lines, his `note` and the `tool`), and
`undo` and `redo`, the last change's step. The name is the link between the list and the rows, not an id in the
row: names are unique ignoring case and outer spaces (`codes.norm`), and an id in the row would need a column
every reader skips while a rename rewrites the name in every row anyway. A name the rows hold that the list
lacks joins it (`sync`, run by `ensure` on every read, and `names_typed`, run by `/api/commit` after a passage of a
thematic analysis project is saved). `rows_of` reads a workbook's passages read-only, kept against its time and
size, `extracts_of` gives every code on an extract with its card key (`sheet:row:line`), and `listing` the list as
the screen and the agents read it, `v` its version (`version`, the codes and where each extract stands).

A change (`change`, through `apply`): `new`, `rename`, `describe`, `merge` and `delete`, refused whole when one is
wrong. Rename and merge become functions of a passage's pairs (`plan_rows`), each pair carrying its place before,
so `moved` says where each statement went, a merge keeping one pair of an extract that had both codes. `land`
writes it whole or not at all: `checked_first` (a workbook's `~$` lock file, a file it cannot write), a copy of
each file (`keep_copy`, a workbook through `workbook.archive_copy` as "pre-codes", the GETs file into the root's
`_Archive`), each workbook in one save (`write_rows`, through `pairs_to_cells` and `_atomic_save`), then the GETs
file (`follow_gets`: a revision of each board first, kind `codes_changed`, its cards rekeyed with their statements,
`rekey_board`, each changed participant's copy read again and each code gathered), a failure copying back every
file written. The list keeps the step: each file, its copy and its sha1 after. `undo` (and redo) puts each file
back from its copy, after a copy of it as it stands, only while every file's sha1 is the step's, and the list
takes its codes as they were. `extract_change` puts a code on an extract the passage holds (`add`, into its pair
with no code, else a pair after the last) or takes one off (`remove`, the pair kept with no code when it was the
extract's last), through `workbook.save_turn`. A page's change carries `v` and a list changed since is refused with
`Stale` (409 with `stale`), the screen drawing the list again. In an IPA project every op refuses with
`codes.refused_ipa` (`refuse_unless_ta`).

A project made before the list (`ensure`): on its first read the list is built from the rows, every description
empty, and each GETs board that changes keeps a revision first, kind `codes_listed` or `codes_listed_moved` naming
the codes gathered, the GETs file copied to the root's `_Archive` first, and the list's History says how many codes
it made. On the GETs board of a thematic analysis project a code is one card. The file keeps a card for each row,
so every reader of the board (the print, the Word theme table, the trail, Search) reads each extract under its
theme. `gather(board, data, leads, keep_out)` keeps every row card of a code where its lead stands, in the lead's
label just after it, at its place, set aside with it, and brings in a card for a row of a placed code that has none,
so a code's extracts follow it. With no lead given the lead is where most of the code's cards stood, a tie the
first in reading order. `gets.answer` folds the board for the page (`fold`, each code's lead alone, the first of its
rows by key, `codes` its name, `n` and `by`), and `gets.save` unfolds the page's save (`unfold`: a code with two
cards sent takes the one the page just brought in, and a code sent with no card has every card taken off).
`gets.take_in` and `gets.take` gather too, so a participant's new extract of a placed code comes in where it stands. An agent's `gets apply` runs `follow_moved` on the board it leaves: a card put in another label, set aside or brought in leads its code's other cards, a card only shifted on the canvas leads when none of its code moved, and two cards of one code moved to different labels are refused (`codes.split_refused`).
The routes are `/api/codes` (the list, made on the first read), `/api/codes-ops`, `/api/codes-extract`,
`/api/codes-quick` and `/api/codes-undo` (`codes_root`, `codes_reply`, `codes_apply`), the command line's `codes list`,
`show`, `new`, `rename`, `describe`, `merge`, `delete`, `add`, `remove`, `apply-last`, `in-vivo`, `undo` and `redo`,
MCP's `codes_*`, and `rename`, `merge`
and `delete` among the holds (`holds.HELD`). The board revisions' words are `themes.revision.named.codes_*`.
`/api/codes-suggest` is the app's own AI's codes for an extract (taaibuild, see Thematic analysis's AI), page-only
like `/api/suggest`, an agent working in its place and taking a code with `codes add`.

The page. `codes.js` and `codes.css`. The Code list screen (`#codes-screen`, `codesOpen`, `codesLoad`,
`codesDraw`), a tab between Coding and Themes in a thematic analysis project's bars (`dsStages`, `es-step-codes`,
`th-step-codes`, `esToCodes`, `thToCodes`), every change through `codesOps` and drawn again from the answer:
Rename in place (`codesRename`), Merge two codes (`#cd-merge`, `codesMergeSaid` counting an extract both codes
had once), Delete this code for a code with no extracts, the row's menu (`codesMenu`), New code (`codesNew`), the
description saved as it loses the focus, Go to the passage through `openPassage`, Undo and Redo on its status bar
and Cmd + Z. Coding A (`cx*`): the passage's pairs stay the page's model and what `/api/commit` saves, hidden
under `.ta-codes`, and `cxDraw`, run by `pairsDrawn` after every change, draws an extract per distinct quote with
its codes as chips. Add a code suggests from `/api/codes` (`cxCodesRead`, read as a case opens and after each
save), and `cxPut`, `cxOff` and their undo entries change the pairs. `markedHtml` colours a mark by its extract
(`cxPlaceOf`) and numbers each extract after its last words with an empty `.cx-pn` whose number the stylesheet
draws, so the passage's words a selection counts never hold it. On the board `gtCodeCardHtml` draws a code's card
from the participants' copies (`gtCodes`), with no participant's colour (`.gt-code`). A Participants panel row is
placed while its code's card is on the board, and dragged it moves that card (`gtCardFrom`, `gtCodeCard`).
Area 316.

Quick keys while coding (quickkeysB, 9 November 2026, Adam's choice of option B with A's keys from the quickkeys
drawings). The codes used last are the list file's `recent`, up to `RECENT_MAX` (5) code ids, the last first, so a
rename follows them and a merge gives the merged code's place to `into`, a code no longer on the list left out by
`recent_of`. `listing` answers them as `recent`, by name. `used` moves codes to the front. `api_commit` calls
`note_used` after `names_typed`, with `put_on`, every name the passage's statements hold more often after the save
than before (`save_turn`'s `statements`), so whatever puts a code on an extract on the Coding screen moves them, and
the file is written only when they change, with no History line (the list's `version` does not read them, so a page
holding the list is never made stale by it). `extract_change`'s `add` moves them too. `quick(root, books, how, case,
sheet, row, words, when, n)` is the agents' op, `how` of `last` (`n` 1 to 5) or `in-vivo` (`vivo_name`: the words,
the inverted commas set aside, less `VIVO_STOPS` at their end and dots at their start, a code of that name on the
list taken as it is spelled, else `checked_name`): the words, checked in the passage's own text by
`workbook.quote_reach` (`passage_text`, which also refuses the interviewer's passage), become a new pair in inverted
commas, or fill the empty-code pair of an extract of the same words, or are refused (`codes.has_it`) when that
extract has the code. History and `--dry-run` as `extract_change`. The route `/api/codes-quick` (`api_codes_quick`,
agent-only, the page coding through `/api/commit` as Add a code does), the command line's `codes apply-last` (with
`--recent`) and `codes in-vivo`, both with `--words`, and MCP's `codes_apply_last` and `codes_in_vivo`.

The page (codes.js, `cxQuick*`). `CX.recent` is `/api/codes`'s `recent`, read by `cxCodesRead`, and `CX.used` the codes
put on here since a read was asked (`cxUsed`, called by `cxPut` and `cxQuickPut`), so `cxRecent` is right before the
save's read comes back. `commitQuote(opts)` takes `code` or `vivo` and hands the quote it put together to
`cxQuickPut`, which fills the passage's empty pair or adds one, or puts the code on an extract of the same words, as
`cxPut` does, one undo entry. `distilKeys` sends R, V and 1 to 5, without Cmd, Ctrl or Alt and outside a field, to
`cxQuickKey`, which acts only in a thematic analysis project with words selected (`selBarPick`) or pieces held, and
with the row menu open chooses its row. `selBarShow` draws `#sel-vivo` and `#sel-recent` first (`cxQuickBar`), so
the toolbar is measured with its second line. `rowMenuGroups` puts `cxQuickMenu`'s groups first on words selected,
an item's `key` drawn in `.row-menu-key` and a `head` as `.row-menu-head`, and `chooseFromMenu` sends a quick item to
`cxQuickChosen`, which selects the words again and runs the key. The shortcuts card's `.help-ta` rows show in a
thematic analysis project alone. Area 359.

The Themes board as the thematic map (themesbuild, 2 November 2026, Adam's choices of the themesmap drawings: the
codes waiting A, the Inspector on a code A, the Inspector on a theme as drawn, Compact B). No data shape changes.
`thLoad` reads the code list on a thematic analysis project's board (`gtCodeListRead`, `/api/codes`, kept in
`TH.codeList`, none on an IPA board, LPETs or LGETs). `thStatusNumbers` counts the list's codes there
(`gtCodeNumbers`, `gtCodePlace`: placed under a theme, binned set aside, else not placed, a code with no card among
them), the cards until the list comes, en.ta's `themes.status.card(s)` saying "codes". `gtCodes` keeps each code's
rows (`rows`, `<case>/es/<line>`). The panel's head is two tabs on that board (`#gt-ptabs`, `gtPtabsDraw`,
`gtPtabSet`, `TH.ptab`, kept in the browser as `idiograph-gets-ptab`): Codes (`gtCodesPanelDraw`, each code once,
Not placed and In themes as sections folding by `:codes/out` and `:codes/in` in the panel's folds, a row dragging as
its code's first row does, `.gt-nodrag` for a code with no row in the study) and Participants (`gtCasesDraw` as
before). The Inspector on a code (`gtCodePanelHtml`): its head `codes.card_kicker`, its description through
`/api/codes-ops` describe on focus out (`gtCodeDescStart`, `gtCodeDescDone`, the answer taken as the list), its
theme, Take out of theme (`data-leave`), Open in Code list (`gtCodeOpen`, `thToCodes({ open })`, `codesOpen`'s
`open`), and its extracts from the participants' copies (`gtCodeExtracts`), Go to the passage through `thToPassage`, and under a theme a tick on each, its participant's key extract for the theme kept as the board's `rows` quote as on IPA's board (`gtTick`), the first of theirs in theme order ticked faintly until one is chosen (`gtTaKeyExtract`). The status bar adds the subthemes (`codes.board.themes_subs`).
On a theme (`gtThemePanelHtml`): the description box labelled Definition (en.ta's `themes.label.description`
Definition on the whole board), its codes, extracts and participants counted from every code card under it, its
codes and subthemes in `thThemeOrder`, each participant's extracts. The Guidance tab shows
`ta_themes_guidance.md` there (tarail), and `thTabsOf` leaves it out only before a server that sends `guidance_ta`. Compact (`#th-compact-btn`, `thCompactOn`, `thCompactToggle`, the
setting `card_compact`, off by default, saved as `card_notes` is) draws a code card as its name alone in
`gtCodeCardHtml`, the room made as Extracts makes it. The Table view there is `gtTableTa` (each theme in canvas
order with its definition, note and Audit trail, its cards in theme order, a code with its extracts, its subthemes
nested, then Not placed: loose cards and the list's codes with no card, then the bin), its rows in order
`gtTableTaFlat`. Its styles are in codes.css. Area 320.

The command line and Search in a method's words, and the theme table in Word (taword, 1 November 2026). The command
line's own sentences that name a method's things are in `apps/idiograph/static/i18n/en/cli.json`, TA's in
`en.ta/cli.json`, read through the method `scope_of` sets: `cases` (with no GET minimum and no PETs line in TA),
`gets show`'s head and its cards' kinds (`gets_card_line`), `statements`' head and quote lines, `project show`'s
length line, and `gets history`'s heads. The rest of its sentences stay English and IPA's. Search's kind names
are `cli.kind.<kind>` (`idiograph_find.KIND_KEYS`): the family's `app_search.kind_name` asks each part's `namer`
(`register(..., namer=)`, `KIND_NAMERS`) before its registered names, Idiograph's `idiograph_find.kind_named`
giving TA's in a TA project, so the command line's hits and counts say Codes and Extracts, `cmd_search` running
its answer in the method when every project answering has one. For the page, the case and project scopes' answer
carries `names` (`idiograph_find.names_now`, only in a method other than IPA), and `search.js`'s `searchKind` takes
a kind's name from it before `SEARCH_KINDS`. The theme table in Word is `gets_word.py`: Microsoft Word in a TA
board's Table view (`data-tact="gword"`) and on the Export card with Theme table chosen (`#gt-print-word`,
`gtWordGo`) call `/api/gets-boards` with `op` `word` (`routes.gets_word_write`, refused outside a TA project by
`gets_word.refuse_unless_ta`), and `gets export --word` the same. The parts and the file come from `themes_word`
(`package`, `free_name`), the name from the PDF's (`print_pdf.safe_stem`, "<project> - Board 1 - Theme table").

Never translated: whatever the researcher writes (participants' words, quotes, statements, notes, PET and GET names,
descriptions), the workbook's column headings (its file format), the command line, MCP and the agents guide, the
apps' names and a citation.

**Checks, area 278.** Every file is one object, every key under its file's name, every plural has `other`. Every key
a script, the markup or the server names is in English, and every English key is used somewhere (a stale one fails).
Every key of another language or overlay is in English with the same slots. On an invented catalogue of garden birds,
Python and the scripts pick plurals, fill slots, fall back to English and then to the key alike, and an overlay
replaces a whole message. Every marker of each app's page is filled. The three month tables' output for every month
comes out of Intl the same, and `language` is saved, refused when it is no tag and followed. A node harness that runs
a piece of a page script puts `support.i18n_js()` first (the English catalogue as the page has it and i18n.js), as
the page loads it before every script. `support.table_js()` carries it. Such a script runs from a file in the
area's scratch, `support.run_node`, never through `node -e`, since the catalogue takes it past Windows's 32,767
characters on a command line (WinError 206, the 0.9.11 tag run). Area 76 checks no area does.

**The pixel check.** A build that moves words changes nothing on screen, and `packaging/pixels/pixel_check.mjs`
proves it. `packaging/pixels/screens.mjs` lists the screens by group, `shell` holding Home, each Settings category
(at its top and, where it scrolls, its end), About and What's new. Each screen starts from Home freshly loaded, every
animation, transition and caret stilled and Home's mark not played, and `MASKS` makes transparent what differs
between two copies for no reason of the change (the agent box naming the install's folder). A build moving another
area adds a group of its own with the screens its words show on. To run it, with smoke servers as the builders' rules
have them, main exported on PORT + 1 and the build on PORT, both on one `--root` copy of `demo/pristine/` so their paths
match (a copy of `demo/` itself has no boards, so the `boards` group never shoots), each through
`~/.claude/bin/heavy`:

```
node packaging/pixels/pixel_check.mjs shoot --port <PORT+1> --out <scratch>/pixels/before [--group shell]
node packaging/pixels/pixel_check.mjs shoot --port <PORT> --out <scratch>/pixels/after [--group shell]
node packaging/pixels/pixel_check.mjs compare <scratch>/pixels/before <scratch>/pixels/after --diff <scratch>/pixels/diff
```

`shoot` writes `<screen>-1280-<light|dark>.png` (`--width`, `--height`, `--scale` and `--schemes` change that).
Every group runs on that one pristine copy. `shoot` waits for Home's answer from the server (`S.lib`) before a
screen opens, since Home shows before it and the screens start from its cards. The `distil` group's Rename card,
which a row's menu holds only for a participant in a folder of its own, opens on a pristine row as the menu would
open it and shows the server's refusal there. On a copy of `demo/`, whose participants each have a folder, it
opens from the menu and shows the list of what will change, so a change to those words shoots the group there
too. Its participant is opened first, so that list is the same whatever the server showed before (loose31, 31
October 2026: on a pristine copy the group stopped at that screen, after its first seven).
`compare` decodes each pair, counts the pixels that differ and where, writes the after shot with each differing
pixel in magenta to `--diff`, and ends on `PIXELS: SAME 24/24` or `PIXELS: DIFFER 2/24`, exit 0 or 1. A shot in one
folder alone differs. The shell's slice came out `PIXELS: SAME` for Idiograph (24 shots), Sift (18) and Trace (14).
The groups `sift` and `trace` (tracestyle, 30 October 2026) shoot Sift's and Trace's own apps, each on a server of
its own app (`--app sift` or `--app trace`) given a review or a Trace project of invented records with `--sift
<folder>` or `--trace <folder>`, which the page reads as `SWEEP` as the zoom groups do and the server's list keeps
beside `--config`: Home with the project's row, the card that opens a project, the table, the table with its
filters, a record, and Trace's Shortcuts and its card that asks.
Serve Sift or Trace with `--app sift` or `--app trace` to shoot theirs.

**The zoom sweep** (zoomsweep, 30 October 2026). `packaging/pixels/zoom_sweep.mjs` shoots a group of
`screens.mjs` through `packaging/wk_shot.swift` (Review shots) at each zoom and window size, and reads in the
page what a zoom breaks: a box or the window drawing a scroll bar, words cut short with no ellipsis, a
control past the window's edge with nothing scrolling to it, a card taller than the window that does not
scroll, two controls or two lines of words over each other, and each bar's height, a bar that grows having
wrapped. Its groups: `zoom`, Idiograph's Home, the project's page and Rename, the statements screen with its
player, its note, Shortcuts and Trim, PETs and GETs on Canvas and Table, Trajectories, every Settings
category from Home and from the statements screen, Send feedback, Support, About and What's new, on a
`--root` copy of `demo/pristine/`, and `zoom-sift` and `zoom-trace`, the table and a record of each, on a
server of that app with `--sift <screening folder>` or `--trace <Trace project folder>` of invented records.
Each size and zoom is one run of wk_shot, compiled into a temporary folder unless `--wk` names one, and the
whole sweep one run of `heavy`:

```
node packaging/pixels/zoom_sweep.mjs --port <PORT> --out <scratch>/zoom --sizes 1280x800 --zooms 1,1.25,1.5
node packaging/pixels/zoom_sweep.mjs --port <PORT> --out <scratch>/zoom720 --sizes 720x800 --zooms 1,1.25
```

It writes `<width>x<height>-<zoom>/<screen>.png` at device scale 1 (`--scale`) with `faults.json` beside
them, and `faults.md`, for each zoom and screen each fault the page shows there and not at the first zoom
listed, then those the first zoom shows itself. The list says where to look and the shots show what is
there: a pixel over is the rounding of a fraction, which WebKit draws no bar for, so it is left out, and a
card over the page or a board's own scrolling is no fault. The first sweep (30 October) fixed What's new, About
and Support opening scrolled to their foot when taller than the window (`doneAtFoot` in shell.js focuses Done
without scrolling), the Settings tabs' second bar from 700px down (`overflow-y: hidden`), the transcript's
sideways bar between 561 and 600px (the passages stack from 600px), Sift's title bar keeping words it had no
room for once its steps were drawn (`barFit` after `rvStepsDraw` and in `sfBar`), and, at any zoom, Sift's
screening never opening in Sift's own app, whose page has no `#work` or `#themes` for `siftOpen` to hide since
the page split of 23 October.

### The family's folders

Since 22 October 2026 (the family codebase's first build, the plan in the Academy folder's history,
`Idiograph_family_codebase_plan_22Oct26.md`) the code is one family of three apps in folders:
`family/`, what every app shares, and `apps/idiograph/`, `apps/sift/` and `apps/trace/`, each app's
own. The apps sit under `apps/` since `idiograph`, `sift` and `trace` at the root are the commands. A
module keeps its plain name wherever it sits (`import sift`, `import app_identity`), since each folder
is an import root. `boot.py` at the root decides it, the standard library only:

- `boot.ROOT`, the folder the code runs from, this file's own from source and `sys._MEIPASS` frozen.
- `boot.setup(app=None)` puts `family/`, the served apps' folders and the root at the head of
  `sys.path`, in that order, each once, every app's when `app` is left out. The root comes last since the
  fourth build, its `server.py`, `cli.py` and `mcp_server.py` being shims of the family's modules of those
  names (`boot.shim`), so `import server` finds `family/server.py`. Every entry calls it first: the root
  shims, the make_* tools, the launchers and each app's `<app>_main.py`, the build and release scripts and
  the suite, each putting the root on the path for `boot` before, so a run under `python -I` from any
  folder finds every module.
- `boot.resource(path)` is a file the code reads beside itself, by its path as the bundle carries it,
  `docs/agents.md` or `static/page.html`: the first of each app's folder, the family's and the root
  that has it, and frozen the root alone. Every such read goes through it, the server's static files
  through `server.static_file`, which looks in each folder's `static/` in that order.

The first build moved `app_identity.py`, `app_folders.py` and `make_app.py` to `family/`. Everything
else is at the root until the builds that move it, Trace's, Sift's and Idiograph's in turn.

The second build, Trace's (22 October 2026), gave the family what Trace and Sift share, each taken out of
the module that had it, which imports it back under the same names: `family/errors.py`, the one error,
`WorkbookError`, also named `AppError`, with `ScreeningError`, `family/files.py`, `now_iso` and
`write_atomic` (from `sift.py`), `family/textfiles.py`, `decode`, the Word reader and `plain` (from
`convert.py` and `sift.py`), `family/pdftext.py`, `norm_doi`, `norm_title`, `is_pdf` and a PDF's text
(from `sift_search.py` and `sift_oa.py`), `family/screenings.py`, Sift's screenings read and never
written, `Screening`, `load`, `pdf_path`, `run_dirs`, `of_review` and `reviews_in` (from `sift.py` and
`sift_search.py`), and in `ai_suggest.py` `route_ready`, `route_model` and `AI_OFF` (from `sift_ai.py`).
Trace's own code went to `apps/trace/`: `trace_claims.py`, `trace_routes.py`, its routes, `trace_cli.py`,
its command, `trace_mcp.py`, its tools, `trace_find.py`, its part of Search, `trace_main.py`, its entry,
and `static/` with `trace.js`, `trace.css`, `favicon-trace.svg` and `trace.html`, its parts of the page.

The family names no app's module: each app's registers itself. `boot.load(kind)` imports each app's
`<app>_<kind>` module by its name, `routes` at the foot of `server.py`, `cli` at `cli.py`'s, `mcp` at
`mcp_server.py`'s and `find` at `app_search.py`'s, and an app with no such module, or a build without it,
is passed over. Each module calls its family module's `register`: `server.register` (its routes, which of
them take a POST alone, `GET_PATHS`, `HOME_ROWS`, `SEARCH_SCOPES` and `SEARCH_ROWS`, and `ROUTE_APP`
taking its paths, so `not_here` answers as before), `cli.register` (`APP_COMMANDS`, its
arguments, its words, its Search over a folder, and `SCREEN_HITS`), `mcp_server.register` (its tools
after the rest, its own server's instructions, its line in Idiograph's, its guide and `APP_ARGUMENTS`) and
`app_search.register` (its kinds after the rest, its scope before Everything, its finder in `FOUND`).
The root's `server.py`, `cli.py` and `mcp_server.py` run the family's modules of those names through
`boot.shim`, so an app's module that imports `server` gets the running one. A frozen launcher imports
`app_identity.entry(app)` by its name, `idiograph_main`, `sift_main` or `trace_main`, then runs the server.

The page: the family's page (`static/index.html` until the fifth build, `family/static/page.html` since)
holds a slot, `<!--slot:home-->` on a line of its own, where each app's part
stands, and each app's `static/<app>.html` its parts, each after a line `<!--part:home-->`.
`server.assembled` fills each slot with every app's part of it in the family's order (`page_parts`), for
the page and `/design`, so the page served is as before. Trace's slots are `head`, `lede`, `home`,
`settings-tab`, `settings-pane`, `ai-warn`, `ai-feature`, `ai-confirm` and `scripts`. In the page an app's
script registers its hooks in `FAMILY_APPS` (`app.js`), its screen, its projects' route, its opener, its
Home section, its Settings pane's load and sends, a Save over its screen, its place kept for a reload and
Search's place, leaving and landing, and the shell and `search.js` call it there alone (`familyApp(screen)`).
`family/static/table.js` is the family's table, its sort, filters, groups, counts and their drawing for
any app's columns of kind `picks`, and the bars' icons, which `trace.js` draws through, and since Sift's
build `sift.js` too.

The third build, Sift's (22 October 2026), moved Sift's own code to `apps/sift/`: `sift.py`, `sift_ai.py`,
`sift_oa.py`, `sift_search.py`, `sift_second.py`, `sift_zotero.py` and `make_world.py`, and beside them
`sift_routes.py`, its routes from `server.py` (its projects, `/api/sift-review`, a screening, `/api/sift`,
its searches, `/api/sift-search`, his databases, `/api/databases`, the sync to Zotero, `/api/zotero`, and
`/sift/pdf`), `sift_cli.py`, the `sift` command from `cli.py`, `sift_mcp.py`, its fourteen tools from
`mcp_server.py`, `sift_find.py`, its part of Search from `app_search.py`, and `sift_main.py`, its entry
(`app_identity.ENTRIES`). Its page went to `apps/sift/static/`: `sift.js`, `sift_search.js`, `sift.css`,
`sift_search.css`, `favicon-sift.svg`, `world.json` and `vendor/` with Mermaid, `sift.html`, its parts of
the page, and `sift_settings.js`, its parts of the shell from `app.js`, its section on Home, its parts of
Settings, a Sift project's own, its AI proposals and their bench and Zotero, what Save sends for them, the
screen kept for a reload and Search's place on its two screens, registered as `FAMILY_APPS.sift`. Search's
landings moved with the screens, `searchToSift` to `sift.js` and `searchToPlan` to `sift_search.js`.
`quote.js` went to `family/static/`, the family's, which Sift's excerpts and Idiograph's quotes share. The
smoke run's stub, `stub_base` and the keychain held in memory, `STUB_KEYCHAIN`, went to `ai_suggest.py`,
since the family's key and model routes ask it, `sift_search.py` taking them back under the same names.
Sift's table went onto the family's, its copies in `sift.js` gone: the sort (`tbSortRows`, `tbCmp`,
`tbSortNext`), the filters (`tbFilterRows`, `tbEachOpen`, `tbFacetCounts`, `tbTicks`), the headings
(`tbTvHeadHtml`), a group and its choices (`tbGroupHtml`, `tbGroupHead`, `tbChoiceHtml`, `tbFindMatch`,
`tbByCount`, `tbFacetOrder`), `TB_TEXT`, `TB_BLANK`, `TB_SPARKS`, `tbDayWords` and `tbBase64`, and
`sift_search.js`'s bar icons (`TB_BUG`, `TB_COG`, `TB_GLASS`, `tbBugHidden`). The family's table reads a
screen's rows through a reader, `TB_READ` its own, each part of which a screen can bring: a row's value,
two values' order, a row's picks, whether a filter holds anything, whether a row passes it and what a row
is counted under. Sift's, `sfRead(stage)`, brings its records' values and picks at the stage
(`sfValue`, `sfPicked`), its kinds' order (`sfOrder`), its sliders (`sfFilterOn`, `sfPasses`, `sfUnder`),
and its headings' classes (`sfHeadKind`) and its own order of a group's choices (`sfCountOrder`) go in as
arguments. What only Sift's table drew is the family's now and draws nothing for a screen that brings none
of it: a database's dot, `db`, a code with its meaning, `sub`, a choice that is a line, `line` and `wrap`,
the lines' heading, `matchHead`, and a button of a group's own, `tool`, which Country brings for its map.
Its columns of its own kinds, its sliders, its form and its reading of filters kept in older forms
(`sfKeptRead`) stay Sift's. The suite's node harnesses put `table.js` ahead of the piece of `sift.js` or
`sift_search.js` they run (`support.table_js`), as the page loads it first.

The registries grew what Sift needed. `server.register` also takes `silent`, routes whose body can carry a
key, which the verbose log names by their path alone, `settings`, each setting the app cleans as Settings
saves it (`SETTINGS_CLEAN`), `key_files`, its modules that keep a key's file as `ENV_PATH`, set with the
app's paths and put back with them (`KEY_FILES`, `app_held`, `app_back`), `projects`, its projects'
folders for another app (`PROJECTS`, Trace finding PDFs in Sift's screenings while the run served Sift, gone
with the cutover), and `holding`, its work that holds a quit (`HOLDS`). `cli.register` takes several screens for one hit's
opener and `search_acts`, the words after `search` that are the app's own acts. `mcp_server.register`
puts the line of an app before Idiograph in a study's order before Distil's (`ORDER`, `LINES_BEFORE`),
and an app's arguments take the project's options. `app_search.register` puts each part in its place in a
study's order (`ORDER`, Sift, Distil, Trace) and takes several groups of kinds. What Sift and Trace share
stays the family's in `server.py`: `there_folder`, `is_empty`, `review_target`, `ai_model_words`,
`zotero_item_link` and `OPEN_FILE`. In the page `FAMILY_APPS` hooks gained `screens`, `made`,
`settingsReset`, `aiLoad`, `settingsLater`, `settingsBody` and `searchClear`, and `familyApp(screen)` finds
an app by any of its screens. Sift's slots are `head`, `lede`, `home-first`, `screens`, `settings-tab`,
`settings-pane`, `ai-warn`, `ai-feature`, `ai-confirm` and `scripts`, the page served the same as before
apart from the line that loads `sift_settings.js`.

The fourth build, Idiograph's server (22 October 2026), split the three mixed modules. `family/server.py` is
the family's server, the paths and settings, the recent list, the key and models, feedback, What's new, the
manual, Restart and Quit, the family rows, the page's assembly, the handler and `main`, and
`apps/idiograph/idiograph_routes.py` everything of Idiograph's it held, its 59 routes and all they alone
reach, reading the family's names as `srv.NAME` as each request comes. `family/cli.py` keeps the options,
the parser at the top, the refusals, `perform`, Search over a folder and every Search's answer, and
`apps/idiograph/idiograph_cli.py` holds Idiograph's thirteen commands. `family/mcp_server.py` keeps the
protocol, the prompt and the resources and the shared `SEARCH` tool, and `apps/idiograph/idiograph_mcp.py`
holds Idiograph's tools, its core and its line. `family/ai_suggest.py` is the providers, key, models and
transport, and `apps/idiograph/statement_prompts.py` the statements prompt, its passes and `suggest`.
`family/app_search.py` is the engine, with no part of its own, and `apps/idiograph/idiograph_find.py`
Distil's kinds and finders. `family/locks.py` holds the locks, the case's lock's place being Idiograph's,
`workbook.case_lock` and `workbook.case_held`. `apps/idiograph/idiograph_main.py` is Idiograph's entry.
Idiograph's other modules, workbook, themes, themes_ai, themes_print, themes_word, gets, gets_print,
rounds, trajectories, qdpx, audio, corpus, export, nudges, print_pdf, project_pack, shared_strings and
make_demo, and its guidance, guidance.md, pet_guidance.md and themes_guidance.md, went to `apps/idiograph/`.
`convert.py` and the dev tools stay at the root for now.

The registries grew what Idiograph needed. `server.register` also takes `streams`, paths answered through
the handler itself, the recording and Send (`STREAMS`), `own_page`, `defaults`, its settings with their
defaults, each block put before a setting of the family's so a settings file keeps its key order
(`place_defaults`, since the sixth build in `defaults(app)` for the apps a run serves), `own_settings` (`SETTINGS_BY_APP`), `read_settings` and `save_settings`, its settings as
`merge_config` reads them and `api_settings` saves them, `ai_choice`, the PETs screen's own
model in `ai_state` (its `ai_more`, the Themes screen's limit, went on 11 November 2026), `question`, the research question `ai_route` fills
(`QUESTION`), `scope`, the timepoint and LPETs scope a request runs in (`SCOPES`, entered by `scoped` in
`_run`), and `start`, the demo filled and the written list taken up as `main` starts (`STARTS`), with
`search_scope` taking several scopes by name and the print views as `get_paths`. `cli.register_own` is the
family's first app's commands at the top of `idiograph`, its perform and its Search hits (`CASE_HITS`), and
`mcp_server.register_own` its tools before every other's, its core, its line, its arguments and its
projects. `app_search.register` takes `scopes`, a part's own scopes in place of one of its name, This case
and This project first among the scopes, and `screens`, whose results carry the case's path. No family
module imports an app's: area 253 fails on any Python crossing, whatever its baseline holds.

Every app's module registers in every app's server, since `boot.load` imports each one it finds and a frozen
build merges them all, so a hook that reads or writes runs in another app's server unless the family keeps
it out. `STARTS` holds each start with its app's name, and `start_up`, all `main` does before it serves,
runs `start_hooks()` alone, the starts of the apps the run serves (`apps_served`). Until 23 October 2026 it ran
them all, and a frozen Sift or Trace ran Idiograph's, which filled Idiograph's demo into its own data folder
(found by siftapp2). Area 256 runs `start_up` on frozen paths for each app.

The fifth build, Idiograph's page (23 October 2026), split the page. `static/app.js` became the family's
`family/static/shell.js`, the plumbing, Home and its family of apps, the cards, Settings with General, AI
features and agents, celebrations, Restart and Quit, updates, What's new and About, and the page's start, and
Idiograph's `apps/idiograph/static/distil.js`, its Home and project pages, the statements screen and all it
alone reaches, its cards, its parts of Settings and Search's openers and landings on its screens (from
`search.js`), which registers `FAMILY_APPS.idiograph` at its foot and wires its controls (`distilBoot`). The
shell's `boot` wires the family's controls, and Home's start (`homeStart`, the screen kept from a restart
among it) waits for `DOMContentLoaded`, so every app's script has registered its part first. The shell asks
the apps through hooks: `appsSay(name)`, the first app's answer (the settings a screen holds, `config`, the
screen celebrations count for, `cheerScreen`, the page's `title`, Settings' category for the screen,
`screenPane`, and the case Settings opens over, `settingsCase`), and `appsKeys(name, e)` for the one
keydown, `keysEscape` before the panels go, `keysEscapeLast` after, `keysCards` and `keys`. Idiograph's other
hooks: `screens`, `scope` (the PETs canvas's timepoint on a request, thScopeFor), `homeRoute`
(`/api/cases`), `homeTaken`, `homeDraw`, `homeAfter`, `homeFirst`, `recent` (Sift's and Trace's too, for Open
Recent), `settingsOpen`, `settingsBody`, `settingsSaved`, `settingsAfter`, `settingsShut`, `projsetShut` (Project
settings shut, settingsplit, as `settingsLast`, `settingsSends`, `settingsRefuse` and `settingsSend` went with Settings'
GETs and Projects that day, Sift's own `settingsSends` and `settingsSend` kept), `aiLoad`, `refocus`, `savePending`, `spot`, `comeBack`,
`searchWhere`, `searchClear`, `searchClosed`, `searchReplace`, `searchTo`, `searchLeave` and `searchAway`.
`static/index.html` became `family/static/page.html`, the family's markup, and Idiograph's went to
`apps/idiograph/static/idiograph.html` in seventeen parts, its slots `icon`, `head`, `lede`, `home`,
`home-page`, `work`, `screens`, `cards`, `settings-tab`, `settings-first`, `settings-pane`, `ai-warn`,
`ai-feature`, `ai-confirm`, `cards-more`, `cards-last` and `scripts`, so the page served is as before but for
the lines that load `shell.js`, `distil.js` and `distil.css`. The server serves `page.html` at `/` and at
`/index.html`. `style.css` kept the family's rules, and every rule whose every selector names an id or a class
only Idiograph's markup and scripts use went to `apps/idiograph/static/distil.css`, loaded after it and before
`themes.css`. The cascade's order holds: three of Idiograph's rules stay in `style.css` where they stood, since
a later rule there sets the same property on the same element at the same specificity, and a narrow window's
rule naming both apps' parts is split, its Idiograph selectors in `distil.css`'s block for that width. A
section of `app.js` whose parts went to both scripts carries its heading again in each, `<name>, the family's
part` or `<name>, Idiograph's part`, so a section read by its heading ends where it did. `design.html` links the family's styles and takes each app's through the `icon` and `head`
slots. The family's other files went to `family/static/` (`beat.js`, `design.html`, `marks.svg`, `search.js`,
`tokens.css`, `vendor/` and the apps' icons in `apps/`), and Idiograph's to `apps/idiograph/static/`
(`themes.js`, `themes.css`, `trajectories.js` and `favicon.svg`). No root `static/` is left. Area 253 is strict
for the page too since: a script naming another owner's top-level name, a property after a dot, an object's
key and a name the script binds itself passed over, a route of another app's or a file of another app's
loaded fails, whatever the baseline holds.

The sixth build, ship-alone (23 October 2026, once the review's session had moved to Sift's own app), made each
app stand alone. The cutover: `app_identity.SERVES_TOO` is `()` for every app, so Idiograph's server refuses Sift's
and Trace's routes with the 404 naming the app, `idiograph sift ...`, `idiograph trace ...` and Idiograph's
`search --folder` on their folders are refused by name with the command to run, Idiograph's MCP server lists its
own tools and its instructions name them alone, `/api/cases` no longer carries `reviews` and `traces`, and Trace
reads Sift's own list of its projects whatever the run, `PROJECTS` gone. Each app's page is assembled from its own
parts alone (`page_parts(app)`, `assembled(page, app)`), and `static_file(name, app)` looks in the served apps'
`static/` and the family's (`boot.roots(apps)`), so another app's file is no app's page, as it is in no app's
bundle. Sift's and Trace's sections of `agents.md` and their conventions went to `agents-sift.md` and
`agents-trace.md`, whole guides of their own.

That left Trace's own app unstyled for a week (tracestyle, 30 October 2026, found by zoomsweep's sweep). Trace's
screen, drawn by `trace.js`, wears the frame it shares with Sift, the classes `sf-*` and `#trace` beside `#sift`,
and the family's table draws its rows and filters in the same classes, but those rules stood in `sift.css`, which
Trace's page had loaded only because every page held every app's parts. From the cutover Trace's page linked
`tokens.css`, `style.css` and `trace.css` alone: its filters showed as bare headings and boxes, its claims had no
rules, its record no frame, and Home's project rows were plain. The frame is the family's since,
`family/static/frame.css`: the rules of `sift.css` that Trace's screen can match, found in a browser in each of its
states and from every class `trace.js`, `trace.html` and `table.js` name, moved whole and in their order, Home's rows
and the card that opens a project, the title bar, the foot, the decisions' pills, the views, the record, its
decisions and note, the PDF, the table and its filters, and their narrow-window rules. Sift's and Trace's head parts
link it before their own stylesheet. Every element's computed style on Sift's screens came out the same before and
after at 1280, 720, 600 and 420 (28 states), and on Trace's the same as its page with the old `sift.css` put back
before `trace.css` (32 states), and the pixel check's `sift` group came out `PIXELS: SAME`. What is Sift's alone stays
in `sift.css`. Sift's and Idiograph's pages lacked nothing their screens use: the one class of another app's their
markup carries, `rail-home` on Sift's and Trace's bars, is Idiograph's rule for its own lockup button in
`distil.css`, Sift's and Trace's bars taking the family's `.bar-brand` as option C was approved. Area 295 holds each
page's links and its classes (its browser check of each part's styles went on 2 November, testspeed, as the pixel
check's groups show those). The same build stopped Sift's record
scrolling sideways at 150% in a 1280 window with the PDF and the flow beside it (zoomsweep's find): the record is
about 250 CSS pixels wide there, and Same study as's box and button (`.sf-study-as`, a row that never wrapped)
widened the study's column, every suggestion with it, while the rating's stars and Not rated (`.sf-fval`) ran past
the record. Both rows wrap now, as the form's did, and the zoom sweep's `zoom-sift` group shows no sideways bar on the
record at 125% or 150%.

Each app's files beside its code are in `app_identity.FILES`, the family's the licence, the notice and the
versions, Idiograph's the guidance, the transcript template, the demo and its guide's schemas, Sift's Mermaid and
its licence, with each app's docs from `docs(app)`, its guide for agents (`agents` in `APPS`), its manual and its
What's new. `files(app)` gives them and `owner_of_file(path)` says whose a file is, by its folder or that table.

The settings hooks are keyed by app, as train 47 keyed the starts. `DEFAULTS` is the family's, `status_bar`,
General's, among them, and `defaults(app)` puts in the own settings of the apps a run serves (`APP_DEFAULTS`),
Idiograph's in the order a file has always held them and Sift's `databases`, `sift_email` and `zotero`, which were
the family's, its own and its `own_settings`. `SETTINGS_READ`, `SETTINGS_SAVE`, `AI_CHOICE`,
`QUESTION`, `SCOPES`, `HOLDS` and `STARTS` hold (app, hook) and a run calls those of the apps it serves through
`hooks(kind)`, `SETTINGS_CLEAN` by app likewise, so a Sift or Trace save writes no setting of Idiograph's, where
until then it wrote Idiograph's corpus, themes and nudges into its own file. `shipped_config(app)` is the app's own.
qdpx's hook at the process's end is taken as Idiograph first holds a copy, never on import. `ROUTE_APP` is the one
table of each route's owner, filled by each registration, a path claimed twice named by `unplaced_routes`
(`CLAIMED_TWICE`), and `routes_of(app)` an app's own. Area 256 section 4 holds the settings, area 223 each page,
areas 222 and 226 the refusals.

Both builds take what they ship from the folder lists in `packaging/build_mac.py`: `code_folders(app)`,
`family/`, the app's own folder and the root, in `boot.setup`'s order (each bundle carried all three apps
until the sixth build), `module_files`, each module of the app's (`modules(app)`, the family's and its own
of `MODULES_BY_OWNER`) from the one folder that has it, the root's shims never (`ROOT_SHIMS`), `static_files(app)`,
the `static/` of each of those folders merged into the bundle's one `static/`, a path in two folders stopping the
build, `data_files(app)`, the family's and the app's own of `app_identity.files`, the page's vendored files
(`vendored(app)`, the family's Ko-fi and Quicksand and Sift's Mermaid) and the docs the window carries aside, and
the demo for Idiograph alone (`ships_demo`), each app with its own `config.json` from `shipped_config(app)`.
`bundle_inputs` gives PyInstaller the folders, the data and the modules, the Mac's spec and the Windows one alike.
`python3 packaging/build_mac.py --list --app sift` prints each file a build would ship and where it comes from,
building nothing, `build_windows.py --list` the Windows build's, and `--scripts` the page's own scripts, which
GitHub's suite checks with `node --check`. At the sixth build Idiograph's list went from 133 rows to 100, Sift's
to 58 and Trace's to 47, nothing of another app's in any.

The boundaries: area 253 (`tests/areas/a253_boundaries.py`) counts every place the family reaches into
an app or one app into another, the Python imports, a script naming another owner's top-level name,
calling another app's route or a page loading another app's file, against `tests/boundaries.json`,
whose `owners` table says whose each file still at the root is. A new crossing fails, and so does one the
baseline holds that has gone: a build that cuts one writes the baseline again with
`python3 tests/areas/a253_boundaries.py --write`. It counted 202 on 22 October, 156 after Trace's build, 111 after
Sift's, 80 after Idiograph's server and 0 after its page, since when any crossing fails. It also counts, for
each app, the rows of its build's list that are another app's, the modules, page files, data files, docs and demo,
the owner of a file beside the code from `app_identity.FILES`, 0 for every app and strict since the sixth build,
and starts every entry under `python -I` from a folder of its own.

A patch made before a move is remade by `packaging/repath.py <patch> --from <sha>` (or `--move
old=new`), which rewrites each moved file's paths for a three-way apply, and names a file split into
several, which is remade by hand.

| File | What it does |
|---|---|
| `boot.py` | Where the family's code and files are: `ROOT`, `setup` and `resource` (see The family's folders). The standard library only. |
| `family/`, `apps/` | The family's folder and each app's (see The family's folders). |
| `server.py`, `cli.py`, `mcp_server.py` | The root's shims, the entries Restart, run.sh, the commands and an MCP client's settings name, each running the family's module of its name (`boot.shim`). |
| `family/server.py` | The family's server: `ThreadingHTTPServer`, the JSON API, the static files, opens the browser, and the registries each app's routes join (see The family's folders). |
| `apps/idiograph/idiograph_routes.py`, `idiograph_cli.py`, `idiograph_mcp.py`, `idiograph_find.py`, `idiograph_main.py`, `statement_prompts.py` | Idiograph's routes, its commands, its tools, its part of Search, its entry and its statements prompt, each registered with the family's module (see The family's folders). |
| `apps/idiograph/workbook.py` | The files this process wrote (`WRITTEN`, `note_written`, `written_here`, `still_written`, 20 October). Reading, writing, rich text, create-from-source, correcting a turn and its timecode, trimming the ends and putting them back, assigning words to another speaker and putting them back, the lock guard. |
| `convert.py` | A transcript in another shape read into turns, VTT, SRT, plain text, CSV, Excel and Word, the column, speaker and interviewer guesses, the interview's name guessed from a file's, and the raw source written from it, one sheet or a sheet an interview. The standard library and openpyxl only. |
| `apps/idiograph/shared_strings.py` | The inline-to-shared-strings conversion Excel needs, each string set out as Excel writes it, the same bytes whichever XML writer openpyxl used (17 October), and since savespeed (11 November) every save of the app in one pass, `save`, openpyxl's write in memory, the conversion and one packing. Ported from a study folder's own script, `xlsx_inline_to_shared_strings.py`, which has not yet taken the 17 October change. |
| `apps/idiograph/rounds.py` | Rounds, row state, the sidecar, pace, the one re-key for rows inserted and deleted, the trim and assignment records and their undo, the daily target and the streak, and the mark that the phase is complete, set and cleared with nothing else written. |
| `apps/idiograph/nudges.py` | The live nudges, from `ipa_annotation_audit.py`. |
| `apps/idiograph/corpus.py` | The examples panel and the prompt's `{examples}`: the two pools, and the demo's statements when neither is there. |
| `apps/idiograph/audio.py` | Finding the sheet's recording and the Range arithmetic the player needs. |
| `family/ai_suggest.py` | The key in the keychain, the prompt template, the model table and the live list, the Messages API, Ollama and (aiwire, 8 November 2026) OpenAI-style chat calls behind one function, the demo turn for the bench, and the defensive parse. The OpenAI-style shape is `POST {base}/chat/completions` and `GET {base}/models` with Bearer, or `api-key` for Azure, for the `PRESETS` table (Mistral, Google Gemini, OpenAI, Azure OpenAI, Another service, LM Studio): model and two turns, no temperature, a ceiling only when the caller sets one, in `max_completion_tokens` for OpenAI and Azure and `max_tokens` for the rest. Azure's chat goes to `{address}/openai/deployments/{deployment}/chat/completions?api-version=`. `route_problem` refuses before any call (no key, no model, no deployment, no address, an address not https unless on this computer), failures go through `refused_said` with the provider's plain name or the address's host, Azure's 404 naming the deployment, nothing answering saying to check the address (LM Studio: start its server). `server.ai_route` carries `address` and `deployment`, `/api/key`, `/api/key-status` and `/api/check-key` take a `provider` and use its own keychain item, `/api/models` asks the chosen OpenAI-style provider's list alone as `openai` and nothing while the AI switch is off. In a smoke run `IDIOGRAPH_SEARCH_STUB` sends each preset to `{stub}/{provider}` and an address not on this computer likewise. Area 344. |
| `apps/idiograph/export.py` | The CSV export, with the Proposed PET column from a board of the themes file when one is named, and each statement's own quote last, `Quote`. Also runs on its own: `python export.py "<workbook>"`. |
| `apps/idiograph/themes_ai.py` | The AI's titles in PETs and in GETs, their prompts with the IPA guidance read from `pet_guidance.md` and the strict reading of three titles, and the plain pieces the API's boards are built with: `lay_out`, the round blobs a structure is laid out in, and `revise_ops`, a change's operations read strictly and applied in order to a plain board. Reads no key and writes nothing itself. |
| `apps/idiograph/themes.py` | The PETs screen's data: the cards read from column C and the quotes, the round pile and the search for a free spot that keeps cards and labels apart, the merge with the stored board, keys following their words, the picks, the themes file and the re-key that moves it with the rows, the board ops, the PETs marked complete, the copy to another board, each board's history, the PET draft, the outline of a board the review and the print view share, the names of the layers, PET, sub-theme and group, `themes.layer`, the labels at any depth, the book's letters A, A1, A1.1 by default or the numbers PET 1, PET 1a, 1a.1, `themes.pet_numbers`, a project's setting read by `themes.pet_labels_of`, and the order under each heading that the print view, the Word document and the draft share, and the labels for the CSV's PET column. Never writes a workbook. |
| `family/app_search.py` | Search across the app (17 and 18 October): the kinds, Idiograph's `KINDS`, Sift's `SIFT_KINDS` and Trace's `TRACE_KINDS`, registered from `sift_find.py` and `trace_find.py`, in `PARTS` in a study's order, the words folded as `sfFindMatch` folds them, each workbook, themes file, GETs file, screening, plan and manuscript read into its items once and held in memory against its time and size and those of the files read beside it, never an index on disk, the PETs' marks from `themes.pet_numbers`, the facets' counts, Project's with Everything, and the window round the first word found. Reads only, through openpyxl read-only, `themes.py` and `gets.py`, and Sift's and Trace's projects through `sift_find.py` and `trace_find.py`. |
| `family/cli.py` | The command line an AI agent works through, `cases`, `search`, `statements`, `board`, `gets`, `turn` and `validate`, on the server's own functions, and the JSON Schema reading `validate` does. The standard library and openpyxl only. |
| `family/mcp_server.py` | The MCP server, the command line's commands as tools on standard input and output, and the config writer behind Add Idiograph to Claude Desktop. The standard library only, beside what `cli.py` needs. |
| `idiograph` | The command line from source on a Mac or Linux, the venv's python running `cli.py`, the `.venv` beside it first and then the repo root's, and `idiograph.bat` beside it for Windows. |
| `idiograph.bat` | The same on Windows. |
| `family/app_folders.py` | Where the Mac app and the Windows app keep what they write, their data, their logs and the launch line, the one place that decides it for `server.app_paths` and both launchers, and the Windows app's two executables by name. The standard library only. |
| `family/agent_log.py` | The agent log (agentlog, 3 November 2026), every app's since siftlog that day: each refusal of an agent kept in `agent-log.json` beside the app's own settings, its values never, its route `/api/agent-log`, repeats counted, the last 7 days and at most 500, read with agentlock's record of the switch, and cleaned as a hold's words are. |
| `family/locks.py` | One writer at a time: the file lock the server and the command line both take around a write, a case's in its `Working/` and the root's at the root. |
| `apps/idiograph/project_pack.py` | A project sent as one file and opened as a copy (21 October): `<Project name>.idiograph`, a zip of `idiograph-sent.json`, its `kind`, `format` (1), `name`, `folder`, `sent`, `version` and `files`, each `path`, `bytes` and `sha256`, then every file of the folder under `project/`, a link never followed and the lock, `.DS_Store` and Excel's `~$` files left out. `read_sent` refuses a higher `format`, a file that is no sent project and a path that climbs out, `copy_folder` names the copy's folder, and `unpack` writes it through a folder beside it renamed into place once every file matches its list. A chosen send (23 October): `choose` takes every participant, `{folder, label, send}`, from `routes.send_participants`, the kinds left out and those asked for, and answers the files, each a path or the project file's bytes less `names`, under their names in the file, every chosen participant's folder by its label (`clean_name`) and a file name carrying the folder's whole name given the label in its place (`as_renamed`), and since 26 October each themes or LPETs file's `workbook` and each GETs, LGETs and Trajectories file's `cases` workbook naming the workbook as it is sent (`workbook_named`), with `left`, the files each reason leaves out (`LEFT_ORDER`, said by `LEFT_SAID`), `kinds_out` and `notes`. `kind_in_case` reads a participant's file as None (the workbook, a backup's `BACKUP_STEM` aside, and the progress file, which always go), `pets` (`PETS_FILE`, `PET_DRAFT`, a Word or PDF table beside the workbook), `audio` (`AUDIO_EXT`), `source` (anything in Source), `archive`, or `notes` (every other file, since 23 October's blinding leak), `audio`, `notes` and `source` left out unless asked (`OPT_IN`), and at the root `GETS_FILES` and a table are `gets`. GETs whose `cases`, `study` or `placed` hold a participant not sent stay out with a note, or refuse the send when asked for by name. With `pets` out, a progress file goes as `progress_without_history`, `PROGRESS_KEEP`'s keys alone, listed under `history`. `send` takes the plan as `chosen` and adds `chosen`, the participants and the kinds left out, to the manifest, which an Idiograph from before reads past, `format` staying 1. `routes.send_chosen` resolves the names and kinds and leaves the recordings out unless asked, and `send_project` runs it under the same lock. `boards` current (23 October): `current_boards` takes any plan, `choose`'s or `whole_less_audio`'s (now given every participant and `audio`), by its `cases`, each participant's folder in the file with its label, and gives each themes, LPETs, GETs and LGETs file `current_board_only` (`board_going`: `chosen`, else `current`, else the first, the board's `history` dropped, `current` and `chosen` set to it, a `complete` of another board null), keeps a PET draft or table only when `tied_to` its board's name (`board_safe`), strips every progress file's History and leaves `_Archive` out, adding `boards` and `board_choice`, and the manifest's `chosen.boards`. `inventory` gives each participant's `boards` and the root's `gets_boards` (`boards_said`). A copy coming back (26 October): `send` takes `origin`, the manifest's `uid`, `statements` (each participant's `statement_print` by key, from `routes.send_origin`), `copy_of` (`COPY_KEYS`) and since 6 November `from`, the sender's Settings Your name when it is set, never the Interviewer's, and since 8 November `boards`, each participant's boards' places prints (`themes.places_print`), `read_sent` answers them with `sent` and `version`, `new_uid` makes a project's id, and `sent_json` and `sent_boards` read a file's project file and its PETs files for `routes.boards_in`. The standard library and `locks.py` only. |
| `apps/sift/sift.py` | Sift, screening for a systematic review: the CSV read and checked, the log appended, the decision columns written afresh from it, undo by a line of its own, the reason codes, the grounds found in the abstract, the rounds, the one count that the screen, the command line and the export share, the searches in `log.csv`, the PRISMA flow and `prisma.md`, the review's side adding records and writing its proposals, Sift's own proposals in their `ai_` columns, and the PDF path that never leaves `pdfs/`, a dropped PDF kept there. His own fields and columns, the participant guess, and the table's view, columns and filters in `sift.json`. A screening that follows an earlier run, `follow_of` its log's first line, `carried_of` the records carried, each other one `new` in `record_view`, `counts`' `follows`, and the flow from the active run's own search alone, `own_search`, since 16 October. The standard library and `locks.py` only, and it calls no model. |
| `apps/sift/sift_second.py` | Sift's second screener, PRISMA 2020 item 8: the project's settings, the seeded draw, calibration, the workbooks written with openpyxl and taken back, blinding, the agreement and Cohen's kappa recorded once, the differences, their outcomes and the replies, each act a line of the screening's log that `sift.read_log` passes over, and what the counts and the flow add. The standard library, openpyxl, `locks.py` and `sift.py`, and it calls no model. |
| `apps/sift/sift_ai.py` | Sift's AI proposals, off unless the app's AI switch and the screening's own are on: `sift.json`, the default prompt, one record's call through `ai_suggest.complete` on the app's own provider, model and key, the answer read strictly and written through `sift.write_ai`, the plan of a proposal for the round, its calls counted first, and the bench, `trial`, one record asked with the prompt as the box holds it and nothing written. |
| `apps/sift/sift_zotero.py` | Sift's sync to Zotero through its Web API v3: `check` the key's own record and the library's name, `survey` what a sync would add, update and leave and the PDFs it would upload, and `sync` the collection named for the Sift project made when missing, new items written fifty at a time with a write token, each item that stands given what it lacks with `If-Unmodified-Since-Version`, its creators from `sift_search.author_names` through `creators_of`, creators exactly as `creators_before` wrote them before 12 October 2026 put right, its `sift:` tags set to the record's, and each PDF uploaded in the API's three steps, authorise, upload and register, `Backoff` and `Retry-After` honoured, nothing ever deleted. The key is read through `sift_search.read_key` and goes in a header to api.zotero.org alone, and every error is scrubbed of it. The keys go into the CSV's `zotero_key` through `sift.write_zotero`, and `zotero.lock` beside the CSV keeps one sync at a time. The standard library, `locks.py`, `sift.py` and `sift_search.py` only, and it calls no model. |
| `apps/trace/trace_claims.py` | Trace (15 October), the third part: a project's manuscripts, Markdown or Word, and its reference list, CSV, RIS or BibTeX, read and never written, the APA citations matched both ways, each claim a reference's citing sentence with its section and the sentence before where it leans on it, a reference's PDF found in the project's pdfs/ or a screening, his judgements kept in the project's folder as a log and a readable JSON file, undo by a line of its own, the AI's passages, each kept only once found in the PDF's own text, and Sift's Check references folder of 14 October read in place. The standard library and the family's `locks.py`, `ai_suggest.py`, `errors.py`, `files.py`, `textfiles.py`, `pdftext.py` and `screenings.py`, and it calls a model only in `find_passages`. |
| `apps/trace/trace_routes.py`, `trace_cli.py`, `trace_mcp.py`, `trace_find.py`, `trace_main.py` | Trace's routes, its command, its tools, its part of Search and its entry, each registered with the family's module (see The family's folders). |
| `apps/trace/static/` | Trace's screen, `trace.js`, drawn through the family's table and wearing the family's `frame.css`, its own style, `trace.css`, its icon, `favicon-trace.svg`, and its parts of the page, `trace.html`. |
| `family/errors.py`, `files.py`, `textfiles.py`, `pdftext.py`, `screenings.py` | What Trace and Sift share: the one error, a file written whole, a file's text and a Word file's paragraphs, a PDF's text and a reference's keys, and Sift's screenings read and never written (see The family's folders). The standard library and each other only. |
| `family/static/table.js` | The family's table for any app's screen, Sift's and Trace's, read through a screen's reader, and the bars' icons. |
| `family/static/frame.css` | The frame Sift's and Trace's screens share, the family's table's styles among it, which their head parts link before their own (30 October). |
| `apps/sift/sift_routes.py`, `sift_cli.py`, `sift_mcp.py`, `sift_find.py`, `sift_main.py` | Sift's routes, its command, its tools, its part of Search and its entry, each registered with the family's module (see The family's folders). |
| `apps/sift/make_world.py` | Builds `world.json`, the map Sift's Country filter draws, from Natural Earth's countries. |
| `apps/sift/static/` | Sift's screen, `sift.js`, its searches' `sift_search.js`, their styles, `sift.css` and `sift_search.css`, its icon, `favicon-sift.svg`, the map, `world.json`, `vendor/mermaid.min.js`, Mermaid 11.14.0, with its licence beside it, Sift's own in `app_identity.FILES`, which its build alone ships, its parts of the page, `sift.html`, and its parts of the shell, `sift_settings.js`. |
| `family/static/quote.js` | A quote's pieces merged and assembled, Idiograph's quotes and Sift's excerpts alike. |
| `apps/sift/sift_oa.py` | Sift's Find open-access PDFs: each record with no PDF looked up by its DOI in OpenAlex and Unpaywall, or in OpenAlex by its exact title and year, its open copies tried and one kept through `sift.save_pdf` only when it is a PDF whose first page, read with the standard library, carries the record's title, never over a PDF there. The standard library, `sift.py` and `sift_search.py` only, and it calls no model. |
| `apps/sift/sift_search.py` | Sift's searches: the plan and its versions in `search_plan.json`, each database's string written from it, PsycInfo and CINAHL on EBSCO, Ovid or ProQuest, registration and `search_plan.md`, his list of databases and their keys, saved, removed and checked by keychain service, a run by API through PubMed's E-utilities, Europe PMC, OpenAlex, Scopus and Web of Science Starter, a RIS, BibTeX or CSV export read, the records merged by DOI, a version suffix set aside, and then by title with a year at most one apart (`near_years`), a record with no year by its title alone when the title is unambiguous, a benchmark DOI found by title in an export without DOIs, abstracts and authors filled from OpenAlex, and `runs/<date>/` written in the shape `sift.py` screens, every run kept, a later run that day `runs/<date>-2/` and up, a later run carrying the screening of the earlier run it follows. The standard library, `locks.py`, `sift.py` and `ai_suggest.py` only, and it calls no model. |
| `skills/` | `idiograph/SKILL.md`, the guide in `docs/agents.md` as a skill for Claude Code and Claude Desktop, word for word under its name and description, and `sift/SKILL.md` and `trace/SKILL.md`, `docs/agents-sift.md` and `docs/agents-trace.md` likewise. |
| `apps/idiograph/gets.py` | The GETs screen's data: the study's cases, each one's copy and its hash, the unchanged fast path, what changed and Take the changes, the GETs file and its boards, a card for every PET and sub-theme and Add every sub-theme, Arrange by participant (`by_participant`, the page's `gtByParticipant` with the same `BY_` numbers, 19 October: every PET and sub-theme card in no GET and not in the bin in a row for its case in the Cases panel's order, each PET in its case's order with its sub-themes after it, a sub-theme whose PET is in a GET or in the bin at the row's end, below and at the left of what stays, which `cli.cmd_gets_apply` runs for `{"op": "arrange", "by": "participant"}` after the other operations and the orders), the count, Smith's band and the minimum, Mark GETs complete, each case's colour and badge and his choice of colour, and a board set out GET by GET for a GET's titles, the rows the demo's quotes are picked from, and a board laid out whole added. The standard library and `themes.py`, and never writes a workbook or a themes file. |
| `apps/idiograph/themes_print.py` | The print view of a board, the page `/themes/print` renders for the browser to print or save as PDF, and a case's table from the switcher: the book's table of Personal Experiential Themes, Smith, Flowers and Larkin's Box 5.6, typeset on landscape A4, headed by the participant, `h1.case`, the table's name smaller beside it on the same line, `.table-name` (20 October, beside it since 31 October), the PETs labelled in capitals with a band and a rule of their tint, A or PET 1, a sub-theme in bold, A1 or PET 1a, a group in bold italic, A1.1 or 1a.1, the indent and type steps stopping at a group inside a group, `DEEP`, Not placed and Binned experiential statements, the bin, with their counts each by its tick, `unplaced` and `binned`, the headings and notes across the full width, each statement a row, `.item`, of two columns about equal, its words and its reference on the left and its own quote on the right in single curly marks, the right empty when it has none, a row never split across a page, each block two sections one after the other, `.lead`, its heading, note and first row, which a page never splits (`break-inside: avoid`, which WebKit honours where it ignores `break-after: avoid`), and `.cont`, the rest, which flows, a first sub-theme's lead nested in its PET's and its `.cont` first in the PET's, `.end` a lead with nothing after it, and nothing else kept together, every other row flowing so the pages fill (Adam's third ruling of 31 October, after a sub-PET kept whole and a block's last two rows kept together left half pages empty, `tall`, `ROOM` and `.tail` gone), the head with no stamp at its top right since 31 October (the date and the board in the foot, Current board gone), and since 1 November (pdfpolish, Adam: "a kind of two by two grid") `.top` a grid of three columns and two rows, `.titles` and `about_block(project, question)`'s `.about` set `display: contents` so their parts are its cells: the participant over the table's name in the first column, at most two fifths of the width (`fit-content(40%)`), the `.label`s in the second and the `.value`s in the third, `page_print.project` in the first row (`.row1`) and `page_print.research_question` in the second (`.row2`), each row's cells on one baseline, so the values line up and the question wraps in its column, no rule under the head (`ROW`, the head's rules both printed tables share), and no PETs marked complete line, `done_line` and its four `page_print.*.done*` strings gone (Adam, 31 October: "I don't want that"), the foot `page_foot(pieces, middle, numbered=True, fit=fit)` in three margin boxes from `foot_pieces` and `foot_parts`, the left box's content one string a piece and `--idiograph-fit` naming the piece that may be shortened, the project: the participant with the board in brackets (none for sending), the project and the table's name at the left, the researcher, Settings' `your_name` (Your name, `read_settings` and `save_settings`, the command line's `settings --your-name`, Word's `dc:creator` through `themes_word.core_xml`) else `idiograph_routes.researcher_name`, Settings' `interviewer`, and `page_print.confidential` and the day printed (`when_printed`) in the middle, Confidential alone with no name, and `page_print.page_of` with `counter(page)` and `counter(pages)` at the right, marked `!important` as `server.PRINT_MARGINS`' empty right box comes after it, which Chrome and WebView2 draw and WebKit does not, the GETs print's the same with the project and its part, and `confidential` and `researcher` on `page`, `print_pdf.write` and `write_gets`, the agents' exports passing the project and the researcher too (31 October, pdfexport: `LINES`, `WIDE` and `lines_in`, which kept a block of up to 30 lines whole, are gone, as the PETs flow on), the rows spaced by their own padding and no padding at a PET's foot nor margin after the last block, since the PET's 2pt of bottom padding carried its rule onto a page of its own in the Mac's print (Adam's blank last page with one green bar), the type a step under the screen's, 18pt, 11.5, 10.5, 10 and 9, the quote's column 136mm, and `TAIL`'s `@supports (font: -apple-system-body)` printing the page at 0.9375 in WebKit, which prints a CSS pixel as 0.8pt (its print lays out at 1.25 times the page's width in points and shrinks by 1.25) where Chromium prints 0.75, so a point is a point on every system and the Mac's pages are Chrome's, the print info's own scaling factor having cut rows across WebKit's pages, the labels from `themes.pet_numbers` and the order from `themes.in_order`, which the Word document takes too. `BLOCKS` is the table's own rules, which the GETs print sets each case's PET table in through `scoped`. Reads only. |
| `apps/idiograph/themes_word.py` | A board as a Word document in the shape of the book's table of Personal Experiential Themes, Smith, Flowers and Larkin's Box 5.6, on portrait A4 where the print view's PDF is landscape: the participant under Heading 1 and the table's name under it in a Subtitle style of its own (20 October), the PETs labelled in bold capitals by the run's All caps, A or PET 1, a sub-theme in bold, A1 or PET 1a, a group in bold italic, A1.1 or 1a.1, Heading 2 to 5 and anything deeper at Heading 5, Not placed and Binned experiential statements, the bin, with their counts each by its tick, `unplaced` and `binned`, each statement followed by its sheet and timecode and its own quote on the next line in single curly marks, from `themes.outline`, whose statements carry `quote` and whose PETs and sub-themes carry `order`. The zip of XML parts written with the standard library, Heading 1 to 5 by Word's names, no colour, fill, list or table, at the case folder's root and never over a file. Reads the workbook and the themes file only. |
| `apps/idiograph/canvas_out.py` | The canvas as a PDF and as a PNG (1 November 2026, exportA), drawn by Typst from the board as its file keeps it since 9 November 2026 (typst4, typst5): `typst_data` (and `pets_data`, `gets_data`) the template's data, the close pairs' lines (`_pairs`) and a thematic analysis code's card (`_codes`, `_code_card`), Quotes on cards and Close pairs from the settings (`quotes_of`, `close_of`), `typeset_canvas` through `typeset.render`, the file named where the table's PDF goes with " canvas" after its name (`place`, `stem_of`) and written never over a file there unless replacing (`write`, `made`). No browser and no held page. |
| `apps/idiograph/typst/canvas.typ`, `canvas-main.typ`, `marks/` | The canvas as a Typst page (typst4, 9 November 2026): the view `canvas(d)` measuring every card, label and note and laying the board out by the app's own rule carried from themes.js, and its main file setting the PDF's landscape A4 or the picture's page sized to the board; the note and quote marks as SVG. |
| `apps/idiograph/print_pdf.py` | The table of PETs and a GETs board as PDFs, for the window, a browser's tab, the command line and MCP alike (19 October, `board export --pdf`, `gets export`), made by Typst since 9 November 2026 (typst5, `typeset_pdf`): `themes_print.typst_data` into `typst/pets_table_main.typ`, `gets_print.typst_data` into `typst/gets.typ`, or for `all` `typst/gets-all.typ`, named as the print view names it (`stem_of`, `where_to`), written never over a file there unless `replace`, then as a `.part` put in its place (`place`). A failure is the catalogue's plain sentence and nothing is written. |
| `apps/idiograph/team.py` | Working together's keys (wtkeys, 8 November 2026): this computer's Ed25519 and X25519 keys in `team-device.json`, the project key by epoch, sealing and opening an envelope, the roster signed by the lead, invite, answer, match and join with the twelve words and the six digits, remove with a new key, a member's computers added and removed and Make lead (wtdevices, 9 November 2026), and `team.json` at the project's root. PyCA `cryptography`, imported when used. |
| `apps/idiograph/team_sync.py` | Working together's owners and versions (wtowners, 8 November 2026): the one writer per participant and per GETs board, a participant's files sent as a version a minute after the owner's last save, applied only when newer, the first full copy for a new computer, and what came in and waits for the project's page. |
| `apps/idiograph/transport.py` | How Working together's sealed messages travel: the shape every route follows (`send`, `fetch`, `listen`), routes registered by name, and a loopback in memory or in a shared folder for the suite and a smoke run. |
| `apps/idiograph/team_words.txt` | The 2,048 plain words an invite's twelve words come from. |
| `apps/idiograph/team_board.py` | A reviewer's board sent straight in (wtboard, 9 November 2026): Send board seals a member's own board of a participant someone else owns as a `board` message, the owner's install takes it in as that participant's next board, never current, through `idiograph_routes.board_coming`, and Accept or Decline goes back as an `answer`. Its record is `.idiograph-team/boards.json`. A reviewer's own boards of another's participant are kept apart in `.idiograph-team/own-boards/` (`own_file`, ownboards). |
| `apps/idiograph/static/team_board.js` | Send board in the PETs board menu, and the line that says a teammate's board came in, with Show, Decline and Accept (wtboard, 9 November 2026). |
| `apps/idiograph/static/team.js` | Working together in Project settings, the invite's card and the join's card (wtkeys, 8 November 2026). |
| `apps/idiograph/project_history.py` | The project's own History (projhistory, 2 November 2026): `idiograph-history.json`, one record for each change to the project's settings, timepoints, statement length or GETs settings, a participant renamed or marked complete, with who asked. |
| `apps/idiograph/codes.py` | A thematic analysis project's code list (codes, 2 November 2026): `idiograph-codes.json`, the codes read from the rows and kept in step with them, rename, merge, describe, new and delete written whole across the workbooks, the GETs file and the list with a copy of each first and one step of undo, a code put on an extract or taken off, a project's first read making its list, and a code's row cards kept in one place on the Themes board (`gather`, `fold`, `unfold`). |
| `apps/idiograph/gets_word.py` | A thematic analysis project's table of themes as a Word document (taword, 1 November 2026), in `themes_word`'s shape: the project under Heading 1 and "Table of themes" in the Subtitle style, each theme of the board in canvas order under Heading 2 in bold capitals with its description and note, its subthemes under Heading 3 to 5 as `themes.theme_order` reads them, and under each heading its codes, each with whose it is and where and its own extract set in under it (`code_blocks`), or with Their key extract only each participant's key extract (`board_blocks`), participant notes only when ticked and each row note after the theme. Written at the project's root, never over a file there, its author Your name (`write`). Reads the GETs file and the workbooks only. |
| `apps/idiograph/gets_print.py` | The GETs in print, the page `/gets/print` renders, the GET table, the audit trail and the full set, its head (`header`) the table of PETs' since 31 October, `themes_print.ROW`, and since 1 November in full (Adam: "it should be consistent across the PETs and GETs tables"): the document's name as the `h1`, `page_print.gets.table_name` ("Table of Group Experiential Themes", `lget_table_name` and `lpet_table_name` for LGETs and LPETs), the trail's and the full set's own names, and `themes_print.about_block(project, question)` to its right, PROJECT in the title's row and RESEARCH QUESTION in the next, the board's note and the cases not complete, with no PETs or changed since they came in (`page_print.gets.waiting`, `.waiting`), under it, and the minimum and the line of what each row shows gone from the page with their strings and styles (`page_print.gets.minimum`, `minimum_band`, `shown_*`, `.minimum`, `.shown`), its foot's piece to shorten the project in the participant's place (`foot_pieces(..., cut_case=True)`), no rule and no GETs marked complete line, each case's PET table there the print view's, `themes_print.block_html`, landscape A4, and the audit trail the GETs screen's card shows, each participant's name with its badge in its case's colour. Its lines are drawn from each row in CSS, so they meet at any width and on paper. Reads the GETs file and the workbooks, these read-only, and writes nothing. |
| `run.command`, `run.sh`, `run.bat` | The run scripts, the Mac's handing over to `run.sh`: each finds the app's `.venv` beside it or at the repo root, and on a downloaded copy's first run makes it (see Running it). |
| `.gitattributes` | CRLF for the batch files and LF for the scripts, in a checkout and in GitHub's zip alike. |
| `.github/` | `workflows/windows-installer.yml`, the suite on GitHub's Windows machine, a Mac and Linux on every pull request (never on a push to main), Linux adding py_compile, node --check and the case-folder rule, then the Windows installer by hand and on a version tag, the Mac app, its disk image and update file on a tag or when asked, and all three on a draft release on a tag (see The installers, the release and the update key, and GitHub's checks). |
| `family/make_app.py` | Builds `Idiograph.app`: the Info.plist, the launcher script and the icon, Idiograph's mark drawn with the standard library from `SHAPES`, the sizes up to 32 from `SHAPES_16`, the mark drawn for 16 pixels, and packed by `iconutil`. `--desktop` adds the Desktop symlink. The server draws the tab's PNG icon with it, so the builds ship it among their modules. |
| `Idiograph.app` | The Mac launcher `family/make_app.py` builds. Committed, so the Desktop symlink and the Dock have something to point at on a fresh checkout. |
| `packaging/` | `build_mac.py`, which builds the Mac app with its own Python and its disk image, and `mac_launcher.py`, that app's executable (see The Mac app, under Running it), and `build_windows.py`, which builds the Windows app and `Idiograph-Setup.exe`, `windows_launcher.py`, its two executables, and `recording/`, gitignored, where `--speak` puts Juno's recording for it (see The Windows app), and `tauri/`, Idiograph in a window of its own, `src-tauri/` the window, its installer's own steps in `src-tauri/windows/hooks.nsh`, `window.js` its page's side, `bundle.py`, Tauri's bundler run around the frozen server, `drive_mac.py`, `drive_windows.py` and `drive_common.py` its checks, with `drive_installer.py`, `drive_installed_mac.py` and `heading.js` the installers' (see The window), and `release.py`, `minisign.py` and `make_update_key.sh`, the release and its key (see The installers, the release and the update key), and `repath.py`, which remakes a patch made before a move (see The family's folders), and `review_shot.js`, the screenshots builders hand Adam with their heading, Before and After and dashed boxes, and its pack, with `shot_box.js`, which measures the boxes and the crop in the page (see Review shots, under Tests). |
| `build/` | The build venv, the stage and PyInstaller's work, made by `packaging/build_mac.py` or `packaging/build_windows.py`, with Tauri's: the window's source laid out in `tauri/`, cargo's `target/` and the settings laid over `tauri.conf.json`, and a release's files in `release/<tag>`. Gitignored. |
| `dist/` | `Idiograph.app`, `Idiograph.dmg` and `Idiograph.app.tar.gz`, as `packaging/build_mac.py` leaves them, and `Idiograph-Setup.exe`, as `packaging/build_windows.py` does. Gitignored. |
| `apps/idiograph/make_demo.py` | The bundled demo, a finished project: Juno's timecodes and spoken recording, the three cases built from their sources, the GETs across them, and Reset demo. |
| `demo/` | The demo itself: the sources, the three cases with their sidecars, the pristine copy, the generated recording, and `idiograph-project.json`, the demo's own project. |
| `make_template.py` | Builds `template/Transcript template.xlsx`, its three invented rows written out in the script. |
| `template/` | `Transcript template.xlsx`, the three columns a transcript is read in as it stands. |
| `wipe_draft.py` | The wipe utility. |
| `diff_workbooks.py` | Round-trip check after a live session: `python diff_workbooks.py BEFORE.xlsx AFTER.xlsx` lists the cells that differ by column, confirms every orange run in BEFORE survives in AFTER, and flags any cell fill. |
| `family/static/` | The family's page since 23 October (see The family's folders): `page.html`, with the slots each app's parts of the page fill, `tokens.css`, every colour, shadow, face, scale and layer as a token in light and dark, linked first (15 October), `design.html`, the reference page at `/design` (see [design](design.md)), `marks.svg`, Idiograph's mark and each part's as a symbol, `apps/`, the three apps' icons at 256 pixels for each Home's foot, `shell.js`, `style.css`, `frame.css`, the frame Sift's and Trace's screens share (30 October), `beat.js`, the beat every page the server serves sends so it can quit after its last tab closes, Search's `search.js`, its card's rules in `style.css` (17 October), over every screen since 18 October, `table.js`, `quote.js` and `vendor/` with Ko-fi's cup and Quicksand. No framework, no build step, nothing fetched at runtime. |
| `apps/idiograph/static/` | Idiograph's page: `idiograph.html`, its parts, `distil.js`, its Home, the statements screen and its parts of Settings and Search, `distil.css`, the PETs screen's `themes.js` and `themes.css`, `trajectories.js` and `favicon.svg`, the tab's icon. |
| `feedback-worker/` | The collector Send feedback posts to, deployed on Adam's own Cloudflare account and nowhere else: `worker.js`, `wrangler.toml`, `schema.sql`, `notes.sh` to read the notes, and a `README.md` with the steps. The app never runs it, it only posts to its address. |
| `relay/` | The relay Working together passes sealed messages through (8 November 2026), not yet deployed: `src/worker.js`, the Worker and its three Durable Objects, `wrangler.jsonc`, `test/serve.mjs`, which runs it on this computer through Miniflare, and a `README.md` for running it and for a team's own copy. See The relay below. The app never runs it. |
| `family/relay_transport.py` | The relay route, `RelayTransport`: the transport's `send`, `fetch` and `listen`, and `make_project`, `set_devices`, `seen`, `put_blob`, `get_blob`, `invite_post` and `invite_fetch`, each call signed with the device's Ed25519 key, the live socket a WebSocket client of its own. The standard library and PyCA `cryptography`, imported only when a transport is made. |
| `family/folder_transport.py` | The shared-folder route, `FolderTransport`: the transport's `send`, `fetch` and `listen`, and `seen`, `drop`, `put_blob` and `get_blob`, through a folder the team already shares, each device writing only in its own subfolder through a temporary name renamed into place, `listen` looking every 15 seconds and on waking. The standard library alone. |
| `site/holding/` | idiograph.app (29 October 2026, a Preview's site since 10 November): the home page, `index.html`, and the Features page, `features.html` (11 November 2026), sharing one header and `style.css` with the tokens it reads copied from `tokens.css`, `mark.js`, Home's mark code copied from `shell.js` with its comments left out, so one of the ways in plays on each visit, `get.js` offering the visitor's download, `features.js` the Features page's find (its Key features' icons are drawn in the page, 11 November 2026), `film-poster.jpg` a title card in the film's look, played from a round button by a few lines in the home page itself, and the tab's icons. No served file carries a comment, so `README.md` says what each is. A Cloudflare Worker with static assets serves it on idiograph.app and www.idiograph.app (`wrangler.jsonc`, `.assetsignore` keeping `README.md` and the config off the site), deployed with Wrangler on Adam's yes. Nothing kept on the visitor's machine. The app never reads it. |
| `apps/idiograph/guidance.md` | The eleven lines in the rail under Holding the craft, each with its Less this and More this examples indented under it (`guidance_examples`, sent as `examples` by `/api/guidance` and opened from each line's arrow by `drawRules` and `ruleExamples` in app.js), with the plain paragraph under that heading the panel shows beneath them (`guidance_framing`), and the craft prompts under their own heading. An indented bullet is never a line of its own (`guidance_sections`). |
| `apps/idiograph/pet_guidance.md` | The guidance on personal experiential themes the AI's titles carry: section 1, what a PET is, and section 3, the rules for a PET, and on GETs section 4, what a GET is, with section 5, the questions a reviewer asks of a GETs board, which the GETs Guidance tab shows. Edit it to change what the AI is told. |
| `apps/idiograph/themes_guidance.md` | The lines of the PETs screen's Guidance tab, distilled from `pet_guidance.md`: how many PETs, how to group, titles, discarding, what goes first inside a PET and what to ask before finishing. Read afresh on every open of the screen, so editing it changes the tab on the next reload. |
| `config.json` | Root folder, the examples' corpus, the sources left out of it (`corpus_exclude`) and the reference workbook, interviewer, round minutes, daily target, nudge switches, the AI switch, the prompt template, the provider (`ai_provider`), the Anthropic model (`model`), Ollama's address and model (`local_url`, `local_model`), the PETs screen's own provider and model (`pets_provider`, `pets_model`), the PETs screen's own settings under `themes`, the limit on a proposal's PETs as `cap`, and the Celebrations and Sound ticks (`celebrations`, `sound`). A `feedback_url` written by hand points Send feedback at a collector for this machine alone, and Save keeps it as it is and never adds one. Gitignored, so a downloaded copy has none until its first run writes the defaults with no project. |
| `state.json` | The recent list, newest first, each case by its pseudonym, and Sift's list of reviews. Written by the app, gitignored. A run with `--root` keeps its own in memory and never touches it. |
| `.env` | `ANTHROPIC_API_KEY=`, read before the keychain. Gitignored. Read only in the server process, only when you ask for a suggestion. |

### The relay

Working together's relay (wtrelay, 8 November 2026, the spec's section 5) is a Cloudflare Worker, `idiograph-relay`, in `relay/`, routed on `idiograph.app/relay/v1/*` and never linked from the site. It holds sealed bytes and nothing it can read: the keys build seals every envelope before the transport is handed it. `relay/README.md` lists the routes. Not deployed yet.

**Storage.** One SQLite-backed Durable Object per project, `Project`, named by the relay's random 16-byte project id, with the tables `devices(id, key, added, removed)`, `messages(n, device, at, bytes, body)` (`n` an AUTOINCREMENT, so a number is never used twice after a delete), `seen(device, n)`, `blobs(id, bytes, at)`, `usage(day, bytes, messages)` and `nonces(nonce, at)`, and `meta` for the id, the lead and when it was made. Sealed blobs go from the request straight to the R2 bucket `BLOBS` as `p/<id>/<blob>`, never through the object. `Invite`, one per invite id, keeps up to ten join answers. `Operator`, one per operator code's SHA-256, counts the projects the code has made. All three are made in `JURISDICTION` ("eu"). The engine on one computer has no jurisdictions, so a local run sets it empty.

**Auth.** A device id is the first 16 bytes of the SHA-256 of its raw Ed25519 public key. Every call but an invite's carries `X-Device`, `X-Time`, `X-Nonce` and `X-Sig`, the base64url Ed25519 signature over the method, the path with its query, the time, the nonce and the body's SHA-256 in hex, joined by newlines, which the object checks with WebCrypto against the key it holds. The time stands within five minutes of the relay's, and a nonce is taken once, so a request copied and sent again is refused. A blob's PUT signs `X-Content-SHA256` in place of its body, and R2 refuses a body that does not match it. Making a project is signed by the key it names and needs one of the codes in the `OPERATOR_CODES` secret, joined by commas. Only the lead changes the device list. A device dropped from it is refused, its socket closed, and it never comes back on.

**Limits** (`LIMITS` in `worker.js`). An envelope 1.5 MB, which holds a padded message of up to 1 MB in base64 with its fields. A blob 200 MB. A project 2 GB and 5,000 messages a day. A code 20 projects. A page of messages 200 or 8 MB. An invite answer 4 KB, ten to an invite, seven days from the first, and 30 calls a minute from one IP through the `INVITE_LIMIT` rate limit. Whatever every device on the list has read is deleted on each `seen`, a device that has read nothing holding everything, and a daily alarm deletes messages and blobs older than 90 days.

**Live.** `GET /p/:id/live` is a WebSocket taken with the hibernation API, tagged by device. The relay sends `new N` on each message, answers `ping` with `pong` without waking, and closes a removed device's sockets.

**The Python side.** `family/relay_transport.py`'s `RelayTransport(key, url)` has the transport's shape, `send` answering the relay's number, `fetch` reading every page after a number as `(n, device, sealed)`, and `listen` a thread on the live socket that calls `on_new()` on connecting and on each `new N`, reconnecting after a fault with a wait that doubles up to a minute, and answers its stop. It pings every 25 seconds. Errors are `RelayError(status, error)`.

**The project on the relay** (relaywire, 9 November 2026). Before it, the team layer sent under team.json's own
`team`, its random 16-byte id, which the relay never made, so with the relay live a lead's first send was refused.
Now the lead's relay code (an operator code) makes the project once: `team.made_on_relay` calls `make_project`
through the route, and the relay's own id goes into the list of people as `relay`, `{"project"}`, with `url` for a
relay the team runs itself (team.json's `relay_url`, `team on --relay-url`). The list is signed by the lead, so every
member has the id from the welcome or the next list, and a member who switches to the relay needs no code.
`relay_transport.team_factory` builds `TeamRelay(relay, team, project)`, which sends, fetches, listens, marks seen,
puts and gets blobs and sets the devices under the relay's id whenever the team layer names the team's, refusing
before it leaves (`RelayError(404, "no project")`) while there is none. The code comes from the page's Relay code
(`set` with `code`), `on` or `set` with `--code-stdin`, goes to the relay in that one call, and is kept nowhere: not
in team.json, the device file, History, a log or a hold. So `holds.gate` refuses `team on` and `team set` with
`--code-stdin` (`holds.CODE_OPS`, `team.cli.code_held`) while Dangerously skip permissions is off, before the
standard input is read, rather than keep a hold whose Approve would run without the code (smokefix, 9 November 2026). On a fresh install the device's keys are made in memory and kept
only once the relay has taken the code, so a wrong code (403 `operator code`), a used-up one (429), no connection
or any other refusal writes nothing, each said in plain words (`team.relay_refusal`). After the project is made,
after They match and after every change to the list, `team.tell_relay` gives the relay the list's device keys.
`team.needs_code` is true while the route is the relay, the list names no project and no loopback stands in, and
then `view` says `needs_code` (to the lead alone), and `invite` and `come` are refused. An invite of a team's own
relay carries its address in the link (`?relay=` before the `#`), which `join` reads, or `relay_url` on `join`.
Send through is the lead's alone (routelead, 9 November 2026): `set_team` refuses a route change from a member
(`team.refused.route_lead`, nothing written), and the lead's change goes into the signed list as `roster["route"]`
with `n` one higher, sent over the old route and the new, once the relay has its project (a switch to the relay
with no project yet is held in team.json and joins the list with the code's project, so no member moves before the
relay has one). `read_team` gives a member's install the list's route, and `take_roster` writes it, so each
install follows. The page shows a member the team's route alone. The Relay code row's input is `wt-relay-code`
(the invite card's check code keeps `wt-code`). MCP's `team_on` refuses the relay route: the code is his. team_sync's look tries `listen` again on each look until a
route listens, so a project made on the relay while the app is open is heard without a restart. Area 357.

**Testing.** Area 342 runs `relay/test/serve.mjs` (Miniflare, `cf: false`, a made-up code, a free loopback port, storage in memory) and drives it from Python, skipping without node, Miniflare or `cryptography`. Nothing in the suite reaches Cloudflare.

**Deploying** needs Wrangler's own login on Adam's account, never the DNS token: the bucket made in the EU (`wrangler r2 bucket create idiograph-relay-blobs --jurisdiction eu`), the `OPERATOR_CODES` secret, the idiograph.app zone on the same account for the route, then `wrangler deploy` from `relay/`.

## Known gaps

- A trim never reaches into a `Source/` folder, so rebuilding a case from its raw source brings the
  cut rows back. Trim the source CSV with a study folder's own trim script, `gravity_trim_transcript.py`, to make
  it stick, and the `trims` record in the progress file holds the boundary timecode and the first
  words of the boundary turn, which is what that script needs to find the phrase.
- A correction to a turn never reaches into a `Source/` folder either, so a rebuild brings the
  uncorrected text back. The `edits` record in the progress file holds the old and the new text of
  every one, a find and replace's rows among them, which is what reconciles the two.
- A replacement that holds the words found, as "so," holds "so", is found again by the next count,
  as in any find and replace. One Replace all passes over every sheet once.
- Nor does an assignment, so a rebuild brings the words back into the turn they were transcribed
  in. The `assignments` record holds the offsets, the speakers and the text before and after.
- A timecode on a new row is an estimate from the length of the text, not from the recording.
  Listening and correcting it with a double-click on the timecode is what makes it exact.
- Undo reaches an assignment or a trim only through the stack, newest first, so the rows it names
  are still where it left them. A change made to those rows in Excel in between is refused rather
  than overwritten, and the stack goes with a reload, so a trim made before one stays cut. Its
  backup in `_Archive` still holds the rows.
- A round closed on open is counted today, whatever day its turns were read, so the first open
  after passed turns began to count put rounds finished earlier into that day's tally.
- Today's haul counts the turns of the rounds closed today and the seconds measured on them, so a
  round begun on an earlier day brings that day's seconds with it, and one closed on open brings its
  turns and no time.
- Round numbers can shift after a cut at the front of a sheet, because the rounds are cut from
  transcript time on the rows that are there. Round records in the sidecar are keyed by number, so a
  front cut leaves the old timings attached to the new numbering.
- Find open-access PDFs reads a first page's text with the standard library alone, so a PDF whose
  fonts carry no ToUnicode map and no Latin encoding, or a scan with no text at all, is refused even
  when it is the paper, and is left to be added by hand.
- The second screener's settings live in the app's own list, so a decision made on the command line
  marks a calibration record only once the stage's first draw has fixed the calibration records.
- A returned workbook is read whole by openpyxl, up to 50 MB, so a workbook built to swell when
  unpacked is refused only by running out of memory. It comes from the second screener alone.
- The Windows app in its window has run on GitHub's Windows machine alone, its installer over 0.9.0's
  Inno Setup install among it, and on no tester's PC yet. Its launcher's logic is checked on a Mac with
  every Windows call stood in for. `packaging/build_windows.py --sign-sha1` has not yet run, there
  being no certificate, nor Tauri's signing of the window and the installer with it. GitHub's build
  takes Juno's recording from `packaging/recording/` only when it was spoken from the transcript as it
  stands.
- The signing and notarising half of `packaging/build_mac.py` has not yet run, since the Mac it
  was written on holds no Developer ID identity. The unsigned build is the one tried. Notarising would
  also need the server's binaries under `Contents/Resources`, which Tauri seals as resources, signed
  with the hardened runtime, which PyInstaller's own signing is trusted to give and nothing has proved.
- The disk image has no window laid out, Tauri's bundler making it with no Finder scripted, so Finder
  shows the app and the link to Applications where it puts them, as 0.9.0's image did.
- The updater has not yet carried a release: `tauri.conf.json` holds Adam's public key since the fifth
  build, and no release has been signed with its key or put on the releases repository yet.
- One person at a time. The server takes a lock around every write, but two browser tabs on the
  same case would still fight over the same rows.
- openpyxl rewrites the whole workbook on save. These workbooks hold nothing it cannot carry, and
  the test proves it cell by cell, but a workbook with charts, images or conditional formatting
  would need checking before it went through here.
- Area 174 reads a saved workbook's own XML and never opens Excel. That Excel may drop a run of
  spaces alone without `xml:space="preserve"`, and takes a run marked with the body font's scheme
  for one in the workbook's body font whatever its rFont says, is the format's rule as written, not
  tried in Excel itself.
- Statements, notes and quotes are one per line. None of the current workbooks has an entry with a
  line break inside it, which is what makes that safe.
- A deleted board is gone from the themes file, its history with it: the card says so, and nothing
  puts it back.
- On a local model the PETs grouping, review and reply send every statement whole, so a case of
  about a hundred statements can pass the model's room. They carry no statement's quotes to leave
  out, the review and a reply only each label's picks, and the statements are what they work on.
- The import readers find a speaker by a `<v Name>` tag or a label at the head of a line. A
  transcript that names its speakers some other way comes in under Speaker, a row a cue or a
  paragraph, to be assigned in the app, and an Excel file is read from its first sheet with
  anything on it.
- A recording dropped on the New project card, or on Add transcripts, is not yet taken, so a case's
  audio goes into its `Source/<interview>/Source/` by hand. A Word file's text boxes, headers and footnotes are not read.
- A run follows one earlier run. Two runs screened apart, each on its own day, are never joined, and
  a later run that follows one of them takes the other's records in as new and undecided where its
  own search finds them again. Scopus pages by `start`, so a search of more than
  5,000 records keeps the first 5,000, and PubMed gives the first 10,000, each said in the run's note.
- A search plan names up to twenty other databases of its own. His list's rows keep the order they
  were added in, with no way yet to move one.
- A run's screening opens only when he presses Open the screening or Screening, never by itself.
  Until he first opens a run, Screening opens the newest run with a screening.
- Trace reads APA's author and year citations alone, so a manuscript in a numbered style or
  with footnote citations shows its reference list with every reference never cited. A citation two
  references answer alike, a 2020 that the list holds twice with no letter, stands as no reference. A
  sentence leans on the one before only by the word it opens with, so a claim carried by a sentence two
  back, or by a pronoun later in the sentence, shows its own sentence alone.
- Trace finds a PDF Sift or its own folder holds and fetches none, so a reference in Zotero alone,
  outside every Sift project's screenings, needs its PDF added by hand. A reference list's author
  without a comma is read as a group's name, so a list that writes Given Surname with no comma keys the
  reference by the whole name. A PDF's text is read with the standard library,
  as Find open-access PDFs reads one, so a scan or a font with no map gives the AI nothing to point to.

**Home and the statement length (20 October, homebatch).** The bars' Idiograph mark is a button, `es-home`
and `th-home`, which calls `goHome` in app.js: the screen in front is left by `searchLeaveFor` (search.js),
what is typed saved and a canvas flushed, a failed save keeping him there, then Home's picker. View's Home,
Cmd+Shift+H and Alt+Home (`HOME_KEY_PRESSED`) call it too. A project's page is a screen of its own in
Back and Forward's history: `navHere` answers `project` with its id, `openPage` goes through `navGo`, and
`navWayBack` on it is `closePage`, so Back from a project is Home and Forward opens it again. The page's
own arrow is Back where the page has its entry. The project file's `statement_words`, a whole number from
5 to 60 (`WORDS_MIN`, `WORDS_MAX`), is written by `write_statement_words` only when it is not 15 and taken
away at 15, read by `statement_words_of` and sent in `read_project`. `/api/project` sets it with
`statement_words` and `dry_run`, the CLI's `length` and MCP's `statement_length_set` the same. `nudges.check_field`
and `check_statement` take `high`. The page's word count reads `wordBand()`, the open case's project's.
