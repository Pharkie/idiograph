# Idiograph in a window of its own

The page in a window of its own, with the frozen server beside it, in place of a browser tab (Adam's
choice, 17 October 2026). Built on the branch `spike/tauri` alone and not shipped yet. How it works is
in `docs/internals.md`, under The window.

- `src-tauri/src/main.rs`, the window: the server started beside it, one Idiograph at a time, Restart
  and Quit, the app ending with its last window, `cli`, `mcp` and on Windows `stop` handed to the server,
  and since the second build a window that asks its page before it closes.
- `src-tauri/src/menu.rs`, the menus, each system's own, and `src-tauri/src/keep.rs`, what the window
  keeps between runs besides its size and place: the page's settings, its place and the zoom.
- `window.js`, the page's side, run in every window before the page's own scripts: Print on a Mac,
  Ctrl+N, a link opened in a new window, and a download handed to the window's save panel. Without the
  window's bridge it does nothing, so a browser's page is as it was.
- `drive_mac.py`, `drive_windows.py` and `drive_common.py`, the checks, on a build with the `drive`
  feature on a Mac and through WebView2's debugging port on GitHub's Windows machine
  (`.github/workflows/tauri.yml`), and the second build's, `drive_menus_mac.py` and `drive_windows_two.py`.
- Since the third build: `bundle.py`, Tauri's bundler run around the frozen server, the installer's own
  steps in `src-tauri/windows/hooks.nsh`, each system's server in `src-tauri/tauri.macos.conf.json` and
  `tauri.windows.conf.json`, and the checks `drive_windows_three.py`, `drive_installer.py`,
  `drive_installed_mac.py`, with `heading.js` heading a Mac's shots.
- Since the fourth build (18 October): `src-tauri/src/update.rs`, Idiograph's updates through Tauri's
  updater plugin and What's new, `draw_pictures.py`, the Windows installer's picture and the disk image's
  background, `src-tauri/windows/English.nsh`, the installer's words, `update_proof.py`, a test release on
  this machine with a throwaway key, and the checks `drive_update_mac.py`, `drive_update_windows.py` (the
  workflow's `update` job) and `drive_windows_four.py`.
- Since the fifth build (18 October): Adam's words for the updates and the crash notice, which shows once,
  a failed start in plain words, every line of `English.nsh` said plainly, his public key in
  `tauri.conf.json`, and `drive_installer.py --older --newer`, the installer's pages where another
  version is installed.
- Since the sixth build (18 October): Relaunch again for an update, six installer lines in the screenshot
  check's words, and `drive_failed_start.py`, a failed start's dialog taken by its frame alone, on this
  build and on the build before the fifth.
- Since the three-app split's build 6 (20 October): one window for Idiograph, Sift and Trace, each knowing
  its app by its executable's name (`src-tauri/src/app.rs`), `bundle.py` laying each app's name, bundle id,
  icons and update address over `tauri.conf.json`, and `make_icons.py`, which draws Sift's and Trace's
  icons into `src-tauri/icons/sift` and `src-tauri/icons/trace`.
- Since 31 October (quitcrash): `quit_loop_mac.py`, Quit asked of a test app built with `drive` many
  times, most of them with a board moving, the server's and the window's ends timed and every crash
  report the runs left counted.
- Since 6 November (fileassoc): `.idiograph`, a shared copy, Idiograph's own document type in
  `tauri.conf.json` (Sift, Trace and the test apps claim none), and `src-tauri/src/opening.rs`, a file
  opened from the Finder or Explorer handed to the page's Open a shared copy.
- Since 8 November (linux3): the window on Linux, `tauri.linux.conf.json` and `bundle.py`'s `linux=True` making an
  AppImage and a .deb around the frozen server (`packaging/build_linux.py --window`), `.idiograph` in the .deb through
  `src-tauri/linux/`, and `drive_linux.py`, which starts the AppImage under xvfb.

## Building it

`packaging/build_mac.py` and `packaging/build_windows.py` build it, the server frozen first and then
Tauri's bundler run around it through `bundle.py` (the third build, 17 October), with Rust and Node.js
installed and `IDIOGRAPH_TAURI_CLI` naming Tauri's CLI where one is installed, else npx fetching 2.12.1.
Everything built goes in the build folder, never in the checkout, and every check builds the test app,
never the real one, and outside iCloud Drive.

1. `python3 packaging/build_mac.py --out <folder> --unsigned --test-app --drive` builds
   `Idiograph Test.app`, its disk image and its update file in `<folder>/dist`, with the `drive` feature a
   check needs, for Apple Silicon, as every Mac build is.
2. `python3 packaging/tauri/drive_mac.py --app "<folder>/dist/Idiograph Test.app" --stage
   <folder>/build/stage --out <folder>` starts it with `open -g -n -W`, so it never takes the keyboard,
   and leaves its screenshots and results in `<folder>`, as `drive_menus_mac.py` does the second build's.

On Windows, `py packaging\build_windows.py --out <folder> --test-app` builds the test app's installer.
The real app is built with neither switch, and released by `packaging/release.py` (see
`docs/internals.md`, The installers, the release and the update key).

## Switches

`IDIOGRAPH_PORT` and `IDIOGRAPH_ARGS` work as they do for the launchers, the command line's
`--port`, `--root` and `--config` too, and `IDIOGRAPH_SERVER_DIR` names the frozen folder for a run
from cargo. A build with the `drive` feature also reads `IDIOGRAPH_WINDOW_DRIVE`, `IDIOGRAPH_WINDOW_SAVE_TO`,
`IDIOGRAPH_WINDOW_CLOSE` and `IDIOGRAPH_WINDOW_NO_OPEN`, and since the second build `IDIOGRAPH_WINDOW_ORDERS`,
`IDIOGRAPH_WINDOW_PICK` and `IDIOGRAPH_WINDOW_UNSAVED`, and since 28 October `IDIOGRAPH_WINDOW_PRINT_TO`, a
folder each print is written to as a PDF with no panel, which `drive_mac.py --pdfs` uses (see the `drive`
module in `main.rs`). `IDIOGRAPH_DRIVE_PORT` and `IDIOGRAPH_DRIVE_STUB` give a drive its own ports.
