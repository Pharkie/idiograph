//! Idiograph in a window of its own (see ../../README.md).
//!
//! The frozen server, the executable `build_mac.py` and `build_windows.py` freeze, sits in the
//! bundle's resources under `server/` and runs as a sidecar: started with `--serve` and
//! `--no-browser` on port 8765, or the next free one, as the launchers start it, the window opened
//! on its page once it answers, and stopped by Quit's own path, a POST to /api/server, once Quit or
//! the last window's close has heard from every page, before the app ends (`end`, since 31 October on
//! a Mac with no web view torn down first). When the server ends by itself, by Quit in Settings, the windows close with
//! it, and through a Restart in Settings they wait for it. One Idiograph at a time: a second start
//! brings the open window forward. New Window, Cmd or Ctrl+N, opens another window on the home
//! page, and on a Mac the windows merge into tabs. `Idiograph cli ...` and `Idiograph mcp ...`, and
//! on Windows `Idiograph stop`, hand over to the sidecar, so the entry Claude Desktop holds still runs.
//!
//! What the page asks of a browser the window does here, with `../window.js` run in every window
//! before the page's own scripts: a page it opens with window.open, the print views among them,
//! opens in a window of its own, a link to anywhere else opens in the default browser, a download
//! opens the system's save panel with the file's name in it, Tauri's own handling of drops is off so
//! the page's own takes a file dragged onto it, and on a Mac the page's Print asks the window for its
//! print panel.
//!
//! The second build (17 October): the menus, each system's own (`menu.rs`), the window's size and
//! place kept across a quit by the window-state plugin, and what the window keeps besides in
//! `window.json` (`keep.rs`): the page's own settings, so they follow the app and not the port, the
//! place the page was on when its window closed, so a relaunch opens there, and the zoom. A window
//! closed asks its page first, which saves what is typed, keeps its place and is told it is going as
//! a browser tells it. Choose opens the system's own folder dialog on the window, every window takes
//! its page's title, and the log's line says the time where the machine is. A server that ends
//! without Quit's word says so before the app ends.
//!
//! The fourth build (18 October): updates through Tauri's own updater plugin (`update.rs`), What's new
//! from the Help menu, every window kept whole on its screen, and the notice when the server ends
//! unasked in plain words.
//!
//! The fifth build (18 October): that notice in Adam's words and shown once, by the page alone when a
//! page can show it, and a start that fails said as plainly, the log's lines on the window's output.
//!
//! The three-app split's build 6 (20 October): the same window is Sift's or Trace's when its executable
//! is named for that app (`app.rs`): it runs the server of that name on that app's port, keeps its log
//! in that app's logs folder, and its titles, menus and notices say that app's name.
//!
//! Since 6 November (fileassoc): a `.idiograph` file, a shared copy, opened from the Finder or Explorer, by a
//! double click, a drop on the app's icon or Open With, goes to the page's Open a shared copy (`opening.rs`).

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod app;
mod formats;
mod keep;
mod key;
mod menu;
mod opening;
mod update;
mod words;

use std::collections::HashMap;
use std::env;
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Seek, SeekFrom, Write};
use std::net::{SocketAddr, TcpListener, TcpStream};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::{Arc, Mutex, OnceLock};
use std::thread::sleep;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

use base64::Engine as _;
use serde_json::{json, Map, Value};
use tauri::webview::{DownloadEvent, NewWindowResponse};
use tauri::{AppHandle, Manager, RunEvent, Url, WebviewUrl, WebviewWindowBuilder, WindowEvent};

/// How many ports after the first are tried, the first being the app's own (app.rs), as the launchers try it.
const SPAN: u16 = 20;
/// The family's three apps' ports, Idiograph's, Sift's and Trace's (app_identity.py), which a fallback
/// from a held port never takes for another app.
const FAMILY_PORTS: [u16; 3] = [8765, 8766, 8767];
const MAIN: &str = "main";
const LOG: &str = "idiograph.log";
/// How long the server has to answer at start, a first start after a download being the slowest.
const START_WAIT: Duration = Duration::from_secs(60);
/// How long Quit has to finish a write in hand before the server is ended.
const QUIT_WAIT: Duration = Duration::from_secs(30);
/// How long the windows wait for the server after a Restart, which on Windows starts it anew.
const BACK_WAIT: Duration = Duration::from_secs(15);
/// The lines the server prints as it ends: a Restart's first, then Quit's or its own quit's, each in the
/// app's own name, "Sift is closed." as much as "Idiograph is closed."
const RESTARTING: &str = "Restarting.";
const CLOSED: [&str; 2] = [" is closed.", "so it quit by itself."];

/// The page's side of the window (see the file).
const WINDOW_JS: &str = include_str!("../../window.js");
/// The start of the part of a window's address after its # that names the screen it opens on, the
/// form the page's Open in a new window gives (20 October).
const OPEN_HASH: &str = "#open=";
/// File, New Window asked of the page in front, which hands over its place, or a page without
/// window.js's part asking for the home screen.
const NEW_WINDOW_JS: &str = "window.__idiographNewWindow ? window.__idiographNewWindow() : window.__TAURI_INTERNALS__ && window.__TAURI_INTERNALS__.invoke('new_window', {})";

/// The server this window started, its port and log, whether the window is closing it, and whether
/// that is done, held for the whole of a stop so a second caller waits for the first to finish.
struct Sidecar {
    port: u16,
    log: PathBuf,
    child: Mutex<Option<Child>>,
    stopping: AtomicBool,
    stopped: Mutex<bool>,
}

static SIDE: OnceLock<Arc<Sidecar>> = OnceLock::new();
/// The server's port, for the windows a command or the menu opens.
static PORT: AtomicUsize = AtomicUsize::new(0);
static OPENED: AtomicUsize = AtomicUsize::new(0);
/// What the window keeps between runs (see keep.rs), from the app's config folder.
static KEPT: OnceLock<keep::Kept> = OnceLock::new();
/// The windows asked to close, by label: whether the page has answered, and whether it kept its
/// window open after all.
static CLOSES: Mutex<Option<HashMap<String, (bool, bool)>>> = Mutex::new(None);
/// Quit under way, each window asked in turn, or the app ending once its last window has closed.
static QUITTING: AtomicBool = AtomicBool::new(false);
/// The windows let go and hidden, by label, whose web views are kept whole while the app ends, or
/// until they are torn down a moment later when it goes on (see `let_go`).
static LET_GO: Mutex<Vec<String>> = Mutex::new(Vec::new());
/// How long a window closed while the app goes on stays hidden before its web view is torn down,
/// so the Mac's web view has stopped drawing it first (see `let_go`).
#[cfg(target_os = "macos")]
const TEARDOWN_WAIT: Duration = Duration::from_millis(600);
/// The app's end under way, RunEvent::Exit reached.
static EXITING: AtomicBool = AtomicBool::new(false);
/// How long a page has to answer that it is closing before its window closes without it.
const CLOSE_WAIT: Duration = Duration::from_secs(3);
/// The words the window shows when a page could not save what was typed before its window closes
/// (`menus.unsaved`, Close Anyway and Cancel), and when the server ends without Quit's word: what
/// happened and what to do (`menus.ended` and `menus.ended_more`), where the notice of the second build
/// showed the log's last lines, a port, 127.0.0.1 and "Stop it with Control-C" among them (17 October,
/// the third build's screenshots), in Adam's words since the fifth build (18 October). The lines still
/// go to the window's own output, for whoever reads it. All of them from the catalogue (words.rs).
/// Whether a page has shown that notice, so the system's own never says it a second time: the fourth
/// build showed it twice, the page's and the system's over it (18 October, the fifth build). A page says
/// so through `closing` with the step `ended`, and the system's notice says it only when no page has
/// within ENDED_WAIT, as when no window holds the app's page.
static ENDED_SHOWN: AtomicBool = AtomicBool::new(false);
const ENDED_WAIT: Duration = Duration::from_secs(3);
/// A failed start's words, said as plainly as the notice above (`menus.not_started`), where its dialog
/// showed the log's last lines (18 October, the fifth build), which go to the window's own output.
fn not_started(log: &Path, why: &str) -> String {
    eprintln!("Idiograph: {why} The last lines of {}:\n\n{}", log.display(), tail(log, 12));
    words::t_app("menus.not_started")
}

/// The folder the frozen server is in: `server/` in the bundle's resources, beside the executable
/// on Windows, in Contents/Resources on a Mac and in `<prefix>/lib/<product name>/` on Linux, or
/// IDIOGRAPH_SERVER_DIR for a run from cargo.
fn server_dir() -> PathBuf {
    if let Ok(dir) = env::var("IDIOGRAPH_SERVER_DIR") {
        return PathBuf::from(dir);
    }
    let exe = env::current_exe().unwrap_or_default();
    let here = exe.parent().map(Path::to_path_buf).unwrap_or_default();
    if cfg!(target_os = "macos") {
        here.parent().map(|c| c.join("Resources").join("server")).unwrap_or_default()
    } else if cfg!(target_os = "linux") {
        // Tauri's resource directory on Linux, where the .deb puts /usr/lib/<name>/ and an AppImage
        // mounts the same layout under its own prefix, never "beside the executable" (linux2)
        let found = linux_server_candidates(&exe, app::name());
        found.iter().find(|c| c.is_dir()).or(found.first()).cloned().unwrap_or_default()
    } else {
        here.join("server")
    }
}

/// Where the server can be on Linux, best first: `<prefix>/lib/<executable's name>/server`, since Tauri
/// names the folder for the product and the executable is named the same, then `<prefix>/lib/<app>/server`
/// for a name that differs (a test build), the executable being in `<prefix>/bin`, then `server/`
/// beside it, as a build run from its own target folder has it.
fn linux_server_candidates(exe: &Path, app_name: &str) -> Vec<PathBuf> {
    let here = exe.parent().map(Path::to_path_buf).unwrap_or_default();
    let lib = here.parent().map(|prefix| prefix.join("lib"));
    let own = exe.file_stem().map(|s| s.to_string_lossy().into_owned()).unwrap_or_default();
    let mut out = Vec::new();
    if let Some(lib) = lib {
        out.push(lib.join(&own).join("server"));
        if own != app_name {
            out.push(lib.join(app_name).join("server"));
        }
    }
    out.push(here.join("server"));
    out
}

/// The logs folder `app_folders.py` names, so the server's log is where the launchers put it.
fn logs_dir() -> PathBuf {
    if cfg!(windows) {
        let local = env::var("LOCALAPPDATA").map(PathBuf::from).unwrap_or_else(|_| {
            PathBuf::from(env::var("USERPROFILE").unwrap_or_default()).join("AppData").join("Local")
        });
        local.join(app::name()).join("Logs")
    } else if cfg!(target_os = "linux") {
        // XDG: $XDG_STATE_HOME (an absolute path) or ~/.local/state, then Idiograph/logs
        let home = PathBuf::from(env::var("HOME").unwrap_or_default());
        let state = match env::var("XDG_STATE_HOME") {
            Ok(v) if Path::new(&v).is_absolute() => PathBuf::from(v),
            _ => home.join(".local").join("state"),
        };
        state.join(app::name()).join("logs")
    } else {
        PathBuf::from(env::var("HOME").unwrap_or_default()).join("Library").join("Logs").join(app::name())
    }
}

/// `Idiograph cli ...` and `Idiograph mcp ...`, and on Windows `Idiograph stop`, which Setup runs:
/// the sidecar run in this process's place, on this process's standard streams, as the launchers
/// hand them to `cli.main`, `mcp_server.main` and `stop_all`.
fn hands_over(args: &[String]) -> bool {
    match args.first().map(String::as_str) {
        Some("cli" | "mcp") => true,
        Some("stop") => cfg!(windows),
        _ => false,
    }
}

fn hand_over(args: &[String]) -> ! {
    let dir = server_dir();
    #[cfg(unix)]
    {
        use std::os::unix::process::CommandExt;
        let err = Command::new(app::server_exe(&dir, false)).args(args).exec();
        eprintln!("Idiograph: the server in {} did not run: {err}", dir.display());
        std::process::exit(1);
    }
    #[cfg(windows)]
    {
        let code = Command::new(app::server_exe(&dir, true))
            .args(args)
            .status()
            .map(|s| s.code().unwrap_or(1))
            .unwrap_or(1);
        std::process::exit(code);
    }
}

/// What the command line gives, as the launchers take it: the port, `--port N` or `--port=N`, and
/// every other argument for the server, `--root` and `--config` among them. The Finder's old
/// `-psn_` argument goes, and so does `--no-browser`, which the window always gives.
fn split_args(args: &[String]) -> (Option<String>, Vec<String>) {
    let (mut port, mut extra) = (None, Vec::new());
    let mut i = 0;
    while i < args.len() {
        let arg = &args[i];
        if arg == "--port" && i + 1 < args.len() {
            port = Some(args[i + 1].clone());
            i += 1;
        } else if let Some(p) = arg.strip_prefix("--port=") {
            port = Some(p.to_string());
        } else if !arg.starts_with("-psn_") && arg != "--no-browser" && arg != "--serve" {
            extra.push(arg.clone());
        }
        i += 1;
    }
    (port, extra)
}

fn listening(port: u16) -> bool {
    TcpStream::connect_timeout(&SocketAddr::from(([127, 0, 0, 1], port)), Duration::from_millis(300)).is_ok()
}

/// The ports tried from `first`, the one asked for and the span after it, without the family's other
/// apps' ports, so Idiograph on its own held port never takes Sift's or Trace's.
fn tried_ports(first: u16) -> impl Iterator<Item = u16> {
    (first..=first + SPAN).filter(move |p| *p == first || !FAMILY_PORTS.contains(p))
}

/// The first port from `first` that nothing listens on and this process can take.
fn free_port(first: u16) -> Option<u16> {
    tried_ports(first).find(|p| !listening(*p) && TcpListener::bind(("127.0.0.1", *p)).is_ok())
}

/// One request to the server, as its own page sends it, Host its own address and no Origin.
fn http(port: u16, method: &str, path: &str, body: &str, wait: Duration) -> Option<(u16, String)> {
    let mut s = TcpStream::connect_timeout(&SocketAddr::from(([127, 0, 0, 1], port)), wait).ok()?;
    s.set_read_timeout(Some(wait)).ok()?;
    s.set_write_timeout(Some(wait)).ok()?;
    let req = format!(
        "{method} {path} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nContent-Type: application/json\r\n\
         Content-Length: {}\r\nConnection: close\r\n\r\n{body}",
        body.len()
    );
    s.write_all(req.as_bytes()).ok()?;
    let mut raw = Vec::new();
    let _ = s.read_to_end(&mut raw);
    let text = String::from_utf8_lossy(&raw).into_owned();
    let status = text.split_whitespace().nth(1)?.parse().ok()?;
    Some((status, text))
}

/// Whether Idiograph's server answers on `port`: /api/server with its `started`.
fn answers(port: u16) -> bool {
    matches!(http(port, "GET", "/api/server", "", Duration::from_secs(2)),
             Some((200, ref text)) if text.contains("\"started\""))
}

/// The time now where the machine is, as the launchers' log line gives it (17 October, the second
/// build, where the first wrote UTC's).
fn stamp() -> String {
    chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string()
}

/// The milliseconds since 1970, as the page's own clock keeps them, for a place the window hands it.
fn now_ms() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_millis() as u64).unwrap_or(0)
}

/// The log's last `n` lines, for a start that failed.
fn tail(log: &Path, n: usize) -> String {
    let text = fs::read(log).map(|b| String::from_utf8_lossy(&b).into_owned()).unwrap_or_default();
    let lines: Vec<&str> = text.lines().collect();
    lines[lines.len().saturating_sub(n)..].join("\n")
}

/// What the server last said in its log since the window started it: a Restart's word, Quit's or its
/// own quit's, or nothing yet, read from the log's last few thousand bytes after the window's own line.
#[derive(Clone, Copy, Debug, PartialEq)]
enum Word {
    Restart,
    Closed,
    Nothing,
}

fn last_word(log: &Path) -> Word {
    let Ok(mut file) = File::open(log) else { return Word::Nothing };
    let size = file.metadata().map(|m| m.len()).unwrap_or(0);
    let _ = file.seek(SeekFrom::Start(size.saturating_sub(8_192)));
    let mut raw = Vec::new();
    let _ = file.read_to_end(&mut raw);
    let all = String::from_utf8_lossy(&raw);
    let all: &str = &all;
    let text = all.rfind("\n=== ").map(|at| &all[at..]).unwrap_or(all);
    let closed = CLOSED.iter().filter_map(|line| text.rfind(line)).max();
    match (text.rfind(RESTARTING), closed) {
        (Some(restart), Some(closed)) if restart > closed => Word::Restart,
        (Some(_), None) => Word::Restart,
        (_, Some(_)) => Word::Closed,
        _ => Word::Nothing,
    }
}

/// How long the window waits for the server's last word once it has gone: while the process it
/// started still runs, as long as the server waits for a write in hand before it says it, and once
/// that process has ended, or after a Restart on Windows, where the server is another's, a few seconds.
const WORD_WAIT_RUNNING: Duration = Duration::from_secs(65);
const WORD_WAIT_ENDED: Duration = Duration::from_secs(5);

/// The manual the bundle carries beside the server, `docs/manual.md`, for Help's first item.
fn manual_file() -> PathBuf {
    server_dir().parent().map(|p| p.join("docs").join("manual.md")).unwrap_or_default()
}

/// The server started on `port`, its output in the log the launchers keep, with the arguments
/// IDIOGRAPH_ARGS adds, as the launchers take them, after the command line's own. IDIOGRAPH_WINDOW
/// tells it the window started it, and IDIOGRAPH_MANUAL names the manual the bundle carries. The window's
/// key (key.rs) goes on its standard input, a pipe, and `key::FROM` tells it so (agentlock, 2 November 2026).
fn start_server(port: u16, extra: &[String], log: &Path) -> Result<Child, String> {
    let logs = log.parent().map(Path::to_path_buf).unwrap_or_default();
    let shown = log.display().to_string();
    let cannot = || words::t_with("menus.no_log", &[("app", app::name()), ("path", &shown)]);
    fs::create_dir_all(&logs).map_err(|_| cannot())?;
    let mut out = OpenOptions::new().create(true).append(true).open(log).map_err(|_| cannot())?;
    writeln!(out, "\n=== {}, starting on port {port} for the window", stamp()).map_err(|_| cannot())?;
    let err = out.try_clone().map_err(|_| cannot())?;
    let mut cmd = Command::new(app::server_exe(&server_dir(), false));
    cmd.args(["--serve", "--port", &port.to_string(), "--no-browser"])
        .args(extra)
        .args(env::var("IDIOGRAPH_ARGS").unwrap_or_default().split_whitespace())
        .env("PYTHONUNBUFFERED", "1")
        .env("PYINSTALLER_RESET_ENVIRONMENT", "1")
        .env("IDIOGRAPH_WINDOW", "1")
        .env("IDIOGRAPH_MANUAL", manual_file())
        .env(key::FROM, "stdin")
        .current_dir(&logs)
        .stdin(Stdio::piped())
        .stdout(out)
        .stderr(err);
    // and the computer's own formats, which the page cannot see (formats.rs), unless the window's own
    // environment already names them, as a check's does
    if env::var_os(formats::VARIABLE).is_none() {
        if let Some(said) = formats::computer() {
            cmd.env(formats::VARIABLE, said);
        }
    }
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x0800_0000;
        cmd.creation_flags(CREATE_NO_WINDOW);
    }
    let mut child = cmd.spawn().map_err(|err| {
        let _ = OpenOptions::new().append(true).open(log).and_then(|mut f| writeln!(f, "The server did not run: {err}"));
        not_started(log, &format!("the server did not start on port {port}."))
    })?;
    // the key, one line, and the pipe closed, so the server reads it as it starts and nothing more comes
    if let Some(mut input) = child.stdin.take() {
        let _ = writeln!(input, "{}", key::key());
    }
    Ok(child)
}

fn exited(side: &Sidecar) -> bool {
    match side.child.lock().unwrap().as_mut() {
        Some(child) => !matches!(child.try_wait(), Ok(None)),
        None => !listening(side.port),
    }
}

/// Whether the server has gone: its process ended, or nothing listening on its port, asked twice
/// half a second apart. On Windows a Restart starts the server anew, and the old process may linger
/// while it lets its last connections go, so its port says more than its process (17 October, the
/// sixth Windows run, where Quit after a Restart left the windows open).
fn gone(side: &Sidecar) -> bool {
    exited(side) || (!listening(side.port) && {
        sleep(Duration::from_millis(500));
        !listening(side.port)
    })
}

/// Quit's own path: a POST to /api/server, asked again while a write still holds it, the server
/// ended only when it has not gone after QUIT_WAIT. Once nothing listens, the process the window
/// started has two seconds to end, as an old one after a Restart on Windows may linger. A second
/// caller waits until the first has finished, so Quit's own thread and the app's end never part with
/// the server half stopped. Answers whether this call stopped it.
fn stop_server(side: &Sidecar) -> bool {
    let mut stopped = side.stopped.lock().unwrap_or_else(|held| held.into_inner());
    if *stopped || side.stopping.swap(true, Ordering::SeqCst) {
        *stopped = true;
        return false;
    }
    let deadline = Instant::now() + QUIT_WAIT;
    let mut asked = Instant::now() - Duration::from_secs(10);
    while Instant::now() < deadline {
        if !listening(side.port) {
            let grace = Instant::now() + Duration::from_secs(2);
            while !exited(side) && Instant::now() < grace {
                sleep(Duration::from_millis(100));
            }
            break;
        }
        if asked.elapsed() >= Duration::from_secs(2) {
            let _ = http(side.port, "POST", "/api/server", r#"{"op":"quit"}"#, Duration::from_secs(5));
            asked = Instant::now();
        }
        sleep(Duration::from_millis(100));
    }
    if let Some(child) = side.child.lock().unwrap().as_mut() {
        if matches!(child.try_wait(), Ok(None)) {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
    *stopped = true;
    true
}

/// The server this window started stopped by Quit's own path, for Quit and the last window's close
/// before the app ends (see `end`), for the updater on Windows, whose installer runs once the app has
/// ended, and for a signal to the window (see ending).
fn stop_sidecar() {
    if let Some(side) = SIDE.get() {
        stop_server(side);
    }
}

/// A SIGTERM, a SIGHUP or a SIGINT to the window ends it as Quit does, the server stopped first.
/// Unheard, such a signal ended the window at once, with no RunEvent::Exit, and left the server it
/// started running under launchd until it quit by itself five minutes later, or never in a run with
/// IDIOGRAPH_STAY_OPEN (27 October, the drives' loose end). A quit the Mac asks for, Quit Idiograph,
/// Activity Monitor's Quit or a shutdown, reaches RunEvent::Exit as before. A SIGKILL, Force Quit,
/// cannot be heard, and the server quits by itself after its wait.
#[cfg(unix)]
mod ending {
    use std::sync::atomic::{AtomicBool, Ordering};
    use std::time::{Duration, Instant};
    use tauri::AppHandle;

    static HEARD: AtomicBool = AtomicBool::new(false);

    // libSystem's own, which std links already
    extern "C" {
        fn signal(sig: i32, handler: extern "C" fn(i32)) -> usize;
    }

    // all a handler may safely do is note it
    extern "C" fn heard(_: i32) {
        HEARD.store(true, Ordering::SeqCst);
    }

    /// The signals heard from now, and a thread that ends the app once one comes: the server stopped
    /// by Quit's own path, then the app asked to end, and should its loop be held, by a sheet's own
    /// loop, ended a few seconds later all the same.
    pub fn listen(app: &AppHandle) {
        const SIGHUP: i32 = 1;
        const SIGINT: i32 = 2;
        const SIGTERM: i32 = 15;
        for sig in [SIGHUP, SIGINT, SIGTERM] {
            unsafe {
                signal(sig, heard);
            }
        }
        let app = app.clone();
        std::thread::spawn(move || {
            while !HEARD.load(Ordering::SeqCst) {
                std::thread::sleep(Duration::from_millis(100));
            }
            let begun = Instant::now();
            super::stop_sidecar();
            eprintln!("Idiograph: a signal ended the window, the server stopped after {} ms", begun.elapsed().as_millis());
            app.exit(0);
            std::thread::sleep(Duration::from_secs(5));
            std::process::exit(0);
        });
    }
}

/// The server watched while a window is open. When it ends by itself, by Quit in Settings, the
/// windows close at once. When its last word was a Restart's they wait up to BACK_WAIT for it to
/// answer again, since on Windows a Restart starts it anew as another process, and on a Mac the
/// same process runs again and never ends. The watching is a bare connection, never a request, so
/// it is never taken for use. The window beats for its pages every thirty seconds, since a Mac's
/// web view stops a minimised page's own beat after about eight minutes and the server would then
/// quit behind an open window (16 October). Should the window itself end without a word, the beat
/// stops and the server quits by itself as after a browser's last tab. A server that ends with no
/// word of Quit's or a Restart's in its log, one that failed, says so once: each page covers itself
/// with the notice, and the app ends as its windows are closed, and only when no page has said it does
/// the system's own notice say it before the app ends (18 October, the fifth build, where both said it).
fn watch(app: AppHandle, side: Arc<Sidecar>) {
    let mut beat = Instant::now();
    std::thread::spawn(move || loop {
        sleep(Duration::from_millis(500));
        if side.stopping.load(Ordering::SeqCst) {
            return;
        }
        if beat.elapsed() >= Duration::from_secs(30) {
            beat = Instant::now();
            let _ = http(side.port, "POST", "/api/beat", "{}", Duration::from_secs(5));
        }
        if !gone(&side) {
            continue;
        }
        // the server's last word comes a moment after its socket has closed, as it lets the writes in
        // hand finish first, so it is waited for: read too early, a Restart was taken for a server that
        // had failed (17 October, the second build's third Windows run)
        let gone_at = Instant::now();
        let mut word = last_word(&side.log);
        while word == Word::Nothing {
            let running = side.child.lock().unwrap().as_mut().map(|c| matches!(c.try_wait(), Ok(None))).unwrap_or(false);
            let limit = if running { WORD_WAIT_RUNNING } else { WORD_WAIT_ENDED };
            if gone_at.elapsed() > limit {
                break;
            }
            sleep(Duration::from_millis(250));
            word = last_word(&side.log);
        }
        if word == Word::Restart {
            let tries = (BACK_WAIT.as_millis() / 250) as usize;
            let back = (0..tries).any(|_| {
                sleep(Duration::from_millis(250));
                listening(side.port)
            });
            if back {
                *side.child.lock().unwrap() = None;
                continue;
            }
        }
        side.stopping.store(true, Ordering::SeqCst);
        if word != Word::Closed {
            eprintln!("Idiograph: Idiograph stopped unexpectedly. The last lines of {}:\n\n{}", side.log.display(), tail(&side.log, 12));
            // each page says so itself, over whatever a request that failed left at its foot, and says
            // back that it has, and then the app ends as he closes its windows
            for window in app.webview_windows().values() {
                if window.url().map(|u| u.path() == "/").unwrap_or(false) {
                    let _ = window.eval(ended_js());
                }
            }
            let asked = Instant::now();
            while !ENDED_SHOWN.load(Ordering::SeqCst) && asked.elapsed() < ENDED_WAIT {
                sleep(Duration::from_millis(100));
            }
            if ENDED_SHOWN.load(Ordering::SeqCst) {
                eprintln!("Idiograph: the page shows that the server stopped");
                return;
            }
            // no page has said it, so the system's own notice says it, once, and the app ends after it
            let app_ = app.clone();
            let _ = app.run_on_main_thread(move || {
                rfd::MessageDialog::new()
                    .set_title(app::name())
                    .set_description(format!("{} {}", words::t_app("menus.ended"), words::t_app("menus.ended_more")))
                    .set_level(rfd::MessageLevel::Warning)
                    .show();
                app_.exit(1);
            });
            return;
        }
        app.exit(0);
        return;
    });
}

/// The page's own notice that the server has gone, over everything, its line at the foot taken away:
/// the second build's notice stood over "Failed to fetch", a request the page made as the server went.
/// Once it shows, the page says so through `closing`, step `ended`, so no other notice says it again.
fn ended_js() -> String {
    format!(
        "(function () {{ var t = document.getElementById('toast'); if (t) t.hidden = true; \
         if (typeof serverGone !== 'function') return; serverGone({}, {}); \
         var tauri = window.__TAURI_INTERNALS__; \
         if (tauri && typeof tauri.invoke === 'function') tauri.invoke('closing', {{ step: 'ended' }}); }})()",
        json!(words::t_app("menus.ended")),
        json!(words::t_app("menus.ended_more"))
    )
}

/// The server started, the window opened on its page once it answers, and the watching begun, on a
/// thread of its own so the app is running while the server starts. A start that fails says so in
/// plain words, the log's last lines on the window's own output (`not_started`), and ends the app.
fn launch(app: &AppHandle, port_text: Option<String>, extra: &[String]) -> Result<(), String> {
    let text = port_text
        .or_else(|| env::var("IDIOGRAPH_PORT").ok().filter(|p| !p.is_empty()))
        .unwrap_or_else(|| app::this().port.to_string());
    let first = text
        .parse::<u16>()
        .ok()
        .filter(|p| *p > 0 && *p < u16::MAX - SPAN)
        .ok_or_else(|| format!("That is not a port number: {text}"))?;
    let port = free_port(first).ok_or_else(|| {
        let (low, high) = (first.to_string(), (first + SPAN).to_string());
        words::t_with("menus.ports_taken", &[("first", &low), ("last", &high), ("app", app::name())])
    })?;
    PORT.store(port as usize, Ordering::SeqCst);
    let log = logs_dir().join(LOG);
    let child = start_server(port, extra, &log)?;
    let side = Arc::new(Sidecar { port, log: log.clone(), child: Mutex::new(Some(child)), stopping: AtomicBool::new(false),
                                  stopped: Mutex::new(false) });
    let _ = SIDE.set(side.clone());
    let started = Instant::now();
    while !answers(port) {
        if started.elapsed() > START_WAIT || exited(&side) {
            stop_server(&side);
            return Err(not_started(&log, &format!("the server did not answer on port {port}.")));
        }
        sleep(Duration::from_millis(50));
    }
    eprintln!("Idiograph: the server answered on port {port} after {} ms", started.elapsed().as_millis());
    // the first window opens where the last window closed, the page taking a Restart's place only
    // within ten minutes, as it does after a Restart
    let place = KEPT.get().map(keep::Kept::place).unwrap_or_default();
    app_window(app, port, Some(MAIN), place).map_err(|err| not_started(&log, &format!("the window did not open: {err}.")))?;
    watch(app.clone(), side);
    Ok(())
}

fn own(url: &Url, port: u16) -> bool {
    url.scheme() == "http" && url.host_str() == Some("127.0.0.1") && url.port() == Some(port)
}

fn inner(url: &Url, port: u16) -> bool {
    own(url, port) || matches!(url.scheme(), "about" | "blob" | "data")
}

/// The window's print panel, which the page's window.print asks for on a Mac, with Save as PDF, as
/// a browser's print gives, on the window whose page asked, `href` its address (see `asking`).
/// `orientation` and `paper` are what the page's own @page size asks for (window.js,
/// idiographPagePaper): WebKit's print panel takes its page from the print info alone and never
/// from the page, so a print view's landscape A4 came out portrait on the Mac's default paper (28
/// October, printland). With them the panel opens on that orientation and paper, a copy of the
/// shared print info so the next print starts as before, and he is still free to change either in
/// the panel. Without them it is the shared print info, as Tauri's own print has it.
#[tauri::command]
fn print(window: tauri::WebviewWindow, href: Option<String>, title: Option<String>, orientation: Option<String>,
         paper: Option<String>, foot: Option<serde_json::Value>) -> Result<(), String> {
    let target = asking(&window, href.as_deref(), title.as_deref());
    #[cfg(feature = "drive")]
    eprintln!("drive: print {} asked through {} orientation {:?} paper {:?}", target.label(), window.label(), orientation, paper);
    #[cfg(target_os = "macos")]
    {
        let landscape = match orientation.as_deref() {
            Some("landscape") => Some(true),
            Some("portrait") => Some(false),
            _ => None,
        };
        let size = paper.as_deref().and_then(paper_points);
        #[cfg(feature = "drive")]
        let save = drive::print_to(target.label());
        #[cfg(not(feature = "drive"))]
        let save: Option<PathBuf> = None;
        return target
            .with_webview(move |webview| unsafe {
                mac::print(webview.inner() as *mut _, webview.ns_window() as *mut _, landscape, size, save, foot);
            })
            .map_err(|err| err.to_string());
    }
    // WebKitGTK's print dialog, like the Mac's panel, takes its page from its page setup alone and never from the
    // page's @page, so a canvas came out portrait A4 (linuxfix, 9 November 2026, the Linux desktop's Print to File):
    // the dialog opens on the orientation and paper the page asks for, and he can still change either there
    #[cfg(target_os = "linux")]
    {
        let landscape = match orientation.as_deref() {
            Some("landscape") => Some(true),
            Some("portrait") => Some(false),
            _ => None,
        };
        let _ = foot;
        return target
            .with_webview(move |webview| linux::print(webview.inner(), landscape, paper.as_deref().and_then(gtk_paper)))
            .map_err(|err| err.to_string());
    }
    #[cfg(windows)]
    {
        // Windows's web view draws the page's own foot, its margin boxes, as Chrome does
        let _ = (orientation, paper, foot);
        target.print().map_err(|err| err.to_string())
    }
}

/// GTK's name for a paper the page's @page names, as `paper_points` has the Mac's.
#[cfg_attr(not(target_os = "linux"), allow(dead_code))]
fn gtk_paper(name: &str) -> Option<&'static str> {
    match name.to_ascii_lowercase().as_str() {
        "a3" => Some("iso_a3"),
        "a4" => Some("iso_a4"),
        "a5" => Some("iso_a5"),
        "b4" => Some("iso_b4"),
        "b5" => Some("iso_b5"),
        "letter" => Some("na_letter"),
        "legal" => Some("na_legal"),
        "ledger" => Some("na_ledger"),
        _ => None,
    }
}

/// Linux's own part: the print dialog opened on the page's orientation and paper.
#[cfg(target_os = "linux")]
mod linux {
    use gtk::prelude::*;
    use webkit2gtk::{PrintOperationExt, WebViewExt};

    /// WebKitGTK's print dialog over the window, its page setup the orientation and paper the page asks for where it
    /// asks for one, else the dialog's own, as Tauri's own print has it.
    pub fn print(view: webkit2gtk::WebView, landscape: Option<bool>, paper: Option<&str>) {
        let operation = webkit2gtk::PrintOperation::new(&view);
        if landscape.is_some() || paper.is_some() {
            let setup = gtk::PageSetup::new();
            if let Some(name) = paper {
                setup.set_paper_size_and_default_margins(&gtk::PaperSize::new(Some(name)));
            }
            // a named paper with no orientation is portrait, as CSS has it (window.js, idiographPagePaper)
            setup.set_orientation(if landscape == Some(true) { gtk::PageOrientation::Landscape } else { gtk::PageOrientation::Portrait });
            operation.set_page_setup(&setup);
        }
        let parent = view.toplevel().and_then(|w| w.downcast::<gtk::Window>().ok());
        operation.run_dialog(parent.as_ref());
    }

    /// One of WebKitGTK's editing commands, "Copy", "Paste", "Undo" and the rest, on the window's view, which edits
    /// the field with the focus as its keys do there (linuxfix3, 9 November 2026).
    pub fn edit(view: webkit2gtk::WebView, command: &str) {
        view.grab_focus();
        view.execute_editing_command(command);
    }

    /// The line at the foot said to Orca (linuxfix4, 9 November 2026): ATK's announcement on the window, which the
    /// bridge sends as AT-SPI's object:announcement and Orca 46 speaks as a message, whatever has the focus. WebKitGTK
    /// tells Orca nothing of a live region. An ATK older than 2.46 has no such signal, and then nothing is said.
    pub fn announce(view: webkit2gtk::WebView, words: &str) {
        use gtk::glib::prelude::*;
        let Some(top) = view.toplevel() else { return };
        let Some(accessible) = top.accessible() else { return };
        if gtk::glib::subclass::SignalId::lookup("announcement", accessible.type_()).is_some() {
            accessible.emit_by_name::<()>("announcement", &[&words]);
        }
    }
}

/// A named paper's width and height in points, portrait, as CSS's page sizes name them.
#[cfg_attr(not(target_os = "macos"), allow(dead_code))]
fn paper_points(name: &str) -> Option<(f64, f64)> {
    let mm = |w: f64, h: f64| Some((w * 72.0 / 25.4, h * 72.0 / 25.4));
    match name.to_ascii_lowercase().as_str() {
        "a3" => mm(297.0, 420.0),
        "a4" => mm(210.0, 297.0),
        "a5" => mm(148.0, 210.0),
        "b4" => mm(250.0, 353.0),
        "b5" => mm(176.0, 250.0),
        "letter" => Some((612.0, 792.0)),
        "legal" => Some((612.0, 1008.0)),
        "ledger" => Some((792.0, 1224.0)),
        _ => None,
    }
}

/// The window whose page asked. On a Mac a window the page opens, a print view or a table, is made
/// with its opener's web view setup, as WebKit asks, and so shares its opener's message handler, so
/// whatever it asks reaches the app as the opener's: Print printed the board behind the table, its
/// panel out of sight (Adam, 18 October). The page names its own address and title, and the window on
/// both is taken, else the one window with that title, since the page of a window written in, the
/// canvas's print, has its opener's address, else those on the address: the one in front where two
/// are on it, else the one that seemed to ask, else the first.
fn asking(caller: &tauri::WebviewWindow, href: Option<&str>, title: Option<&str>) -> tauri::WebviewWindow {
    let Some(href) = href.filter(|h| !h.is_empty()) else { return caller.clone() };
    let named = |t: &str| if t.trim().is_empty() { app::name().to_string() } else { t.trim().to_string() };
    let all: Vec<tauri::WebviewWindow> = caller.app_handle().webview_windows().into_values().collect();
    let at = |w: &tauri::WebviewWindow| w.url().map(|u| u.as_str() == href).unwrap_or(false);
    let titled = |w: &tauri::WebviewWindow| match title {
        Some(t) => w.title().map(|wt| named(&wt) == named(t)).unwrap_or(false),
        None => false,
    };
    let both: Vec<tauri::WebviewWindow> = all.iter().filter(|w| at(w) && titled(w)).cloned().collect();
    let by_title: Vec<tauri::WebviewWindow> = all.iter().filter(|w| titled(w)).cloned().collect();
    let on = if !both.is_empty() {
        both
    } else if by_title.len() == 1 {
        by_title
    } else {
        all.iter().filter(|w| at(w)).cloned().collect()
    };
    if let Some(front) = on.iter().find(|w| w.is_focused().unwrap_or(false)) {
        return front.clone();
    }
    if on.iter().any(|w| w.label() == caller.label()) {
        return caller.clone();
    }
    on.into_iter().next().unwrap_or_else(|| caller.clone())
}

/// A new window, from the page's Ctrl+N or File, New Window, on what the window it came from shows
/// (20 October, Adam's drawing of two windows in step): `place` the page's places, its screen and the
/// home screen's, which the new window starts on as a restart's, and `hash` the same screen as
/// `#open=` and the place, the form Open in a new window gives its window. With neither, the home
/// screen. Async, so it is made off the main thread: on Windows a window made on the main thread, from
/// a command or a menu's item, opened blank and with no menu bar (17 October, the second build's
/// screenshots).
#[tauri::command]
async fn new_window(app: AppHandle, place: Option<Map<String, Value>>, hash: Option<String>) -> Result<(), String> {
    let port = PORT.load(Ordering::SeqCst) as u16;
    let (session, hash) = new_window_place(place, hash);
    app_window_at(&app, port, None, session, hash.as_deref()).map(|_| ()).map_err(|err| err.to_string())
}

/// What a new window starts on, from what the page handed over: its two places alone, each a string,
/// and the address's `#open=` part alone, or none.
fn new_window_place(place: Option<Map<String, Value>>, hash: Option<String>) -> (Map<String, Value>, Option<String>) {
    let mut session = Map::new();
    for (key, value) in place.unwrap_or_default() {
        if keep::PLACES.contains(&key.as_str()) && value.is_string() {
            session.insert(key, value);
        }
    }
    let hash = hash
        .and_then(|h| h.strip_prefix(OPEN_HASH).map(str::to_string))
        .filter(|h| !h.is_empty() && h.chars().all(|c| c.is_ascii_graphic() && c != '#'));
    (session, hash.map(|h| format!("open={h}")))
}

/// The words of Choose's dialog: a Mac shows them as a sentence over the folders, and Windows as the
/// dialog's title, which ends in no full stop (17 October, the second build's screenshots), as GTK's dialog on Linux
/// does too (linuxfix, 9 November 2026).
fn pick_title(prompt: &str) -> String {
    title_words(prompt, cfg!(target_os = "macos"))
}

/// `prompt` as a sentence, or as a title with no full stop at its end.
fn title_words(prompt: &str, sentence: bool) -> String {
    let words = prompt.trim();
    if sentence { words.to_string() } else { words.trim_end_matches('.').trim_end().to_string() }
}

/// Choose, from the page: the system's own folder dialog on the window, or with `files` its file
/// dialog, `prompt` its words. The path chosen, or none for Cancel.
#[tauri::command]
async fn pick(window: tauri::WebviewWindow, prompt: String, files: bool) -> Option<String> {
    let mut panel = rfd::AsyncFileDialog::new().set_parent(&window);
    if !prompt.trim().is_empty() {
        panel = panel.set_title(pick_title(&prompt));
    }
    let chosen = if files { panel.pick_file().await } else { panel.pick_folder().await }.map(|h| h.path().to_path_buf());
    #[cfg(feature = "drive")]
    let chosen = drive::picked(chosen);
    chosen.map(|p| p.display().to_string())
}

/// The shared copies the app was asked to open and no page has taken yet (opening.rs), each once, for a window of
/// the app's own page alone: its page hands each to Open a shared copy (fileassoc, 6 November).
#[tauri::command]
fn opened(window: tauri::WebviewWindow) -> Vec<String> {
    opening::take(&window)
}

/// One of the page's settings changed, `key` and its `value`, or none for gone, or with `all`
/// every one at once (see keep.rs).
#[tauri::command]
async fn keep(key: Option<String>, value: Option<String>, all: Option<Map<String, Value>>) {
    let Some(kept) = KEPT.get() else { return };
    if let Some(all) = all {
        kept.set_all(&all);
    } else if let Some(key) = key {
        kept.set_local(&key, value.as_deref());
    }
}

/// The home screen's projects for Open Recent, and whether Send feedback is there.
#[tauri::command]
async fn recent(app: AppHandle, list: Vec<Value>, feedback: bool) {
    menu::set_recent(&app, menu::take_recent(&list), feedback);
}

/// Whether a project with a history is open in the window in front, for File, Project History, and since
/// settingsplit (5 November) `settings`, whether any project is open, a demo's included, for File, Project Settings. A
/// page from before it says nothing of `settings`, and the item follows History. Since barsD (6 November) `replace`,
/// whether the statements screen is in front, for Edit, Find and Replace, greyed when a page from before says nothing.
#[tauri::command]
async fn project_now(on: bool, settings: Option<bool>, replace: Option<bool>) {
    menu::set_history(on, settings.unwrap_or(on), replace.unwrap_or(false));
}

/// Cmd or Ctrl with 0, + or -, from the page: the zoom a step in, out, or back to its actual size, of
/// the window whose page asked, `href` and `title` its own (see `asking`). On a Mac a print view's
/// asking reached the app as its opener's, so the window behind it zoomed (20 October, the backlog).
/// With `to` in place of `by`, Settings' Text size (20 October, Settled 12): the app's zoom set to that
/// step, every window as one, as View's three move it. With neither it changes nothing. Either way it
/// answers the app's zoom as it now stands, which Settings ticks its row by.
#[tauri::command]
async fn zoom(window: tauri::WebviewWindow, by: Option<i64>, to: Option<f64>, href: Option<String>,
              title: Option<String>) -> f64 {
    if let Some(to) = to {
        zoom_to(window.app_handle(), to);
    } else if let Some(by) = by {
        let target = asking(&window, href.as_deref(), title.as_deref());
        zoom_on(&target, by);
    }
    KEPT.get().map(|kept| kept.zoom()).unwrap_or(keep::ACTUAL)
}

/// A print view's or the manual's own zoom, by its window's label, once it is zoomed by itself.
static OWN_ZOOM: Mutex<Option<HashMap<String, f64>>> = Mutex::new(None);
/// The windows the page opened on about:blank to write in, the canvas's print, which then have their
/// opener's address, so they read as the app's own page by it alone.
static WRITTEN: Mutex<Vec<String>> = Mutex::new(Vec::new());

/// The zoom of the window in front: the app's own page zooms every window as one, as before, and a
/// print view or the manual zooms alone, from the app's zoom it opened at.
fn zoom_on(window: &tauri::WebviewWindow, by: i64) {
    if own_page(window) {
        zoom_by(window.app_handle(), by);
        return;
    }
    let app_zoom = KEPT.get().map(|kept| kept.zoom()).unwrap_or(keep::ACTUAL);
    let to = {
        let mut held = OWN_ZOOM.lock().unwrap();
        let own = held.get_or_insert_with(HashMap::new);
        let to = keep::step(own.get(window.label()).copied().unwrap_or(app_zoom), by);
        own.insert(window.label().to_string(), to);
        to
    };
    #[cfg(feature = "drive")]
    eprintln!("drive: zoom {} {to}", window.label());
    let _ = window.set_zoom(to);
}

/// The zoom of every window, one for the app, kept for the next run, each print view zoomed by itself
/// keeping its own.
fn zoom_by(app: &AppHandle, by: i64) {
    let Some(kept) = KEPT.get() else { return };
    let to = kept.step_zoom(by);
    zoom_all(app, to);
}

/// The app's zoom set to a step, Settings' Text size, kept as a step of View's is.
fn zoom_to(app: &AppHandle, to: f64) {
    let Some(kept) = KEPT.get() else { return };
    let to = kept.set_zoom(to);
    zoom_all(app, to);
}

/// Every window of the app's own page at the app's zoom, each print view or manual zoomed by itself
/// keeping its own.
fn zoom_all(app: &AppHandle, to: f64) {
    #[cfg(feature = "drive")]
    eprintln!("drive: zoom app {to}");
    let own: Vec<String> = OWN_ZOOM.lock().unwrap().as_ref().map(|m| m.keys().cloned().collect()).unwrap_or_default();
    for window in app.webview_windows().values() {
        if !own.iter().any(|label| label == window.label()) {
            let _ = window.set_zoom(to);
            // told to the page, so Settings' Text size follows View's items as it follows the keys
            let _ = window.eval(format!("window.dispatchEvent(new CustomEvent('idiograph-zoom', {{ detail: {to} }}))"));
        }
    }
}

/// Undo or Redo in a text field, from the Mac's Edit menu once the page has left the key to the
/// field: the action the system's own Edit menu sends, to the field with the focus.
#[tauri::command]
fn edit(window: tauri::WebviewWindow, action: String) {
    #[cfg(target_os = "macos")]
    {
        let _ = window.run_on_main_thread(move || mac::send(&action));
    }
    // Linux's Undo and Redo where the page leaves them, as in a text field: WebKitGTK's own (linuxfix3)
    #[cfg(target_os = "linux")]
    webkit_edit(&window, &action);
    #[cfg(windows)]
    let _ = (window, action);
}

/// The line at the foot, said by the window to a screen reader (linuxfix4, 9 November 2026): on Linux through ATK's
/// announcement (`linux::announce`), since Orca hears nothing of WebKitGTK's live region. The page asks only on Linux.
/// VoiceOver and NVDA hear the page's own live region, so on a Mac and Windows it does nothing.
#[tauri::command]
fn announce(window: tauri::WebviewWindow, words: String) {
    let words = speakable(&words);
    #[cfg(target_os = "linux")]
    if !words.is_empty() {
        let words = words.to_string();
        let _ = window.with_webview(move |webview| linux::announce(webview.inner(), &words));
    }
    #[cfg(not(target_os = "linux"))]
    let _ = (window, words);
}

/// The words a line says, trimmed, and none past a short paragraph's length, so a page cannot hand the screen reader
/// a book.
fn speakable(words: &str) -> &str {
    let words = words.trim();
    match words.char_indices().nth(400) {
        Some((at, _)) => &words[..at],
        None => words,
    }
}

/// An item of Linux's Edit menu, which carries no keys there (menu::edit_keys, linuxfix3, 9 November 2026): Undo and
/// Redo ask the page first, as the Mac's do, so on a board they are the app's own, and in a field the page hands them
/// back through `edit`. Cut, Copy, Paste and Select All run WebKitGTK's own editing command.
#[cfg(target_os = "linux")]
fn linux_edit_item(window: &tauri::WebviewWindow, id: &str) {
    match id {
        "edit-undo" | "edit-redo" => {
            let name = if id == "edit-undo" { "undo" } else { "redo" };
            let _ = window.eval(format!("window.__idiographMenu && window.__idiographMenu('{name}')"));
        }
        _ => webkit_edit(window, id),
    }
}

/// WebKitGTK's editing command for `id` run on the window's view, on the main thread.
#[cfg(target_os = "linux")]
fn webkit_edit(window: &tauri::WebviewWindow, id: &str) {
    if let Some(command) = webkit_command(id) {
        let _ = window.with_webview(move |webview| linux::edit(webview.inner(), command));
    }
}

/// WebKitGTK's editing command for an Edit item, by its id or the page's `edit` action (linuxfix3, 9 November 2026).
#[cfg_attr(not(target_os = "linux"), allow(dead_code))]
fn webkit_command(id: &str) -> Option<&'static str> {
    match id.strip_prefix("edit-").unwrap_or(id) {
        "undo" => Some("Undo"),
        "redo" => Some("Redo"),
        "cut" => Some("Cut"),
        "copy" => Some("Copy"),
        "paste" => Some("Paste"),
        "select-all" => Some("SelectAll"),
        _ => None,
    }
}

/// A window asked to close: its page answers as it goes. `begun` says it has heard, `unsaved` that
/// what is typed could not be saved, and the window asks whether to close anyway, `kept` that the
/// window stays, and `done` hands over the page's place and closes it. Since the fifth build (18
/// October) `ended` says the page shows that the server stopped, so no other notice says it again.
#[tauri::command]
async fn closing(window: tauri::WebviewWindow, step: String, place: Option<Map<String, Value>>) -> bool {
    let label = window.label().to_string();
    let mark = |kept: bool| {
        let mut held = CLOSES.lock().unwrap();
        held.get_or_insert_with(HashMap::new).insert(label.clone(), (true, kept));
    };
    match step.as_str() {
        "ended" => {
            ENDED_SHOWN.store(true, Ordering::SeqCst);
            true
        }
        "begun" => {
            mark(false);
            true
        }
        "unsaved" => {
            mark(false);
            let close_anyway = words::t("menus.close_anyway");
            let answer = rfd::AsyncMessageDialog::new()
                .set_title(app::name())
                .set_description(words::t("menus.unsaved"))
                .set_level(rfd::MessageLevel::Warning)
                .set_buttons(rfd::MessageButtons::OkCancelCustom(close_anyway.clone(), words::t("menus.cancel")))
                .set_parent(&window)
                .show()
                .await;
            #[cfg(feature = "drive")]
            let answer = drive::unsaved(answer);
            matches!(answer, rfd::MessageDialogResult::Ok)
                || matches!(&answer, rfd::MessageDialogResult::Custom(word) if *word == close_anyway)
        }
        "kept" => {
            mark(true);
            QUITTING.store(false, Ordering::SeqCst);
            false
        }
        _ => {
            // the place of the app's own page alone, never a print view's or the manual's
            if window.url().map(|u| u.path() == "/").unwrap_or(false) {
                if let (Some(kept), Some(place)) = (KEPT.get(), place) {
                    kept.set_place(&place);
                }
            }
            let_go(&window);
            true
        }
    }
}

/// Idiograph's updates, from the page (update.rs): the question asked once, Settings' Updates rows,
/// the home screen's line, Relaunch now with the page's place, and What's new's line once shown.
#[tauri::command]
async fn updates(app: AppHandle, op: String, check: Option<bool>, download: Option<bool>,
                 place: Option<Map<String, Value>>) -> Value {
    update::act(&app, &op, check, download, place)
}

/// A window's close button, Close Window or Quit: its page asked first (window.js), which answers
/// within CLOSE_WAIT or the window is let go without it, as a page that no longer answers cannot hold it.
fn ask_close(window: &tauri::WebviewWindow) {
    let label = window.label().to_string();
    CLOSES.lock().unwrap().get_or_insert_with(HashMap::new).insert(label.clone(), (false, false));
    let asked = window.eval("window.__idiographClosing ? window.__idiographClosing() : null").is_ok();
    let app = window.app_handle().clone();
    std::thread::spawn(move || {
        let deadline = Instant::now() + CLOSE_WAIT;
        while Instant::now() < deadline && asked {
            sleep(Duration::from_millis(100));
            let answered = CLOSES.lock().unwrap().as_ref().and_then(|m| m.get(&label).copied()).unwrap_or((false, false));
            if answered.0 {
                return;
            }
        }
        if let Some(window) = app.get_webview_window(&label) {
            let_go(&window);
        }
    });
}

/// Whether the window `label` has been let go, hidden or gone.
fn let_go_already(app: &AppHandle, label: &str) -> bool {
    app.get_webview_window(label).is_none() || LET_GO.lock().unwrap().iter().any(|l| l == label)
}

/// Whether every window but `label` has been let go, so letting it go ends the app.
fn alone(app: &AppHandle, label: &str) -> bool {
    app.webview_windows().keys().all(|l| l == label || let_go_already(app, l))
}

/// A window closed, its page having answered or given no answer in time. On a Mac since 31 October
/// (quitcrash) it is hidden at once and its web view is never torn down while the app turns on to its
/// end: during Quit, or when it is the last window, it is kept whole until the process ends, as AppKit's
/// own Quit ends an app, and Quit, or for the last window `end`, stops the server and ends the app.
/// Another window, the app going on, is torn down TEARDOWN_WAIT later, once its page has stopped
/// drawing. 0.9.14 crashed as Adam quit it on 31 October: its window torn down while the app ran on to
/// its end, the system's web view sent a frame's scrolling to a part of the page already freed (WebKit
/// bug 327576, fixed in WebKit in October 2026, not yet in macOS 26.5), and the server, which Quit
/// stopped only after the windows, went on. Elsewhere the window closes at once, as before.
fn let_go(window: &tauri::WebviewWindow) {
    #[cfg(target_os = "macos")]
    {
        let app = window.app_handle().clone();
        let label = window.label().to_string();
        let ending = QUITTING.load(Ordering::SeqCst) || alone(&app, &label);
        let _ = window.hide();
        {
            let mut held = LET_GO.lock().unwrap();
            if !held.contains(&label) {
                held.push(label.clone());
            }
        }
        if !ending {
            tear_down_later(app, label);
        } else if !QUITTING.load(Ordering::SeqCst) {
            // the last window closed by its close button or Close Window: the app ends as Quit ends it
            std::thread::spawn(move || end(&app));
        }
    }
    #[cfg(not(target_os = "macos"))]
    {
        #[cfg(target_os = "linux")]
        linux_size::state_before_going(window);
        let _ = window.destroy();
    }
}

/// A window let go while the app goes on, torn down once it has been hidden for TEARDOWN_WAIT, and
/// never once the app has begun to end, Quit's or the last window's, so its web view goes with the process.
#[cfg(target_os = "macos")]
fn tear_down_later(app: AppHandle, label: String) {
    std::thread::spawn(move || {
        sleep(TEARDOWN_WAIT);
        if QUITTING.load(Ordering::SeqCst) {
            return;
        }
        if let Some(window) = app.get_webview_window(&label) {
            let _ = window.destroy();
        }
        LET_GO.lock().unwrap().retain(|l| *l != label);
    });
}

/// The app's end once its windows have been let go, Quit's or the last window's: the server stopped by
/// Quit's own path first, here, so it is stopped whatever comes after, then the app asked to end, its
/// windows still whole, and RunEvent::Exit puts an update in place.
fn end(app: &AppHandle) {
    // the app ending, so no window is torn down from here on (see tear_down_later)
    QUITTING.store(true, Ordering::SeqCst);
    let begun = Instant::now();
    if SIDE.get().map(|side| stop_server(side)).unwrap_or(false) {
        eprintln!("Idiograph: the server stopped {} ms after the windows closed", begun.elapsed().as_millis());
    }
    // never asked once the app is ending already, as on Windows when its last window has gone, since an
    // ask that comes too late ends the process at once, an update's installer with it
    if !EXITING.load(Ordering::SeqCst) {
        app.exit(0);
    }
}

/// Quit: every window asked to close in turn, the one in front last, so its place is the one kept,
/// and Quit given up when a window stays, the windows it had let go then closed. Once every window is
/// let go, `end` stops the server and ends the app.
fn quit_all(app: &AppHandle) {
    if QUITTING.swap(true, Ordering::SeqCst) {
        return;
    }
    let mut labels: Vec<(bool, String)> = app
        .webview_windows()
        .into_iter()
        .map(|(label, w)| (w.is_focused().unwrap_or(false) || label == MAIN, label))
        .collect();
    labels.sort();
    let app = app.clone();
    std::thread::spawn(move || {
        for (_, label) in labels {
            let Some(window) = app.get_webview_window(&label) else { continue };
            if let_go_already(&app, &label) {
                continue;
            }
            // a print view or the manual is let go at once, as it has nothing to save, and on Windows
            // closes at once, as it must while its print panel holds its page
            if !own_page(&window) {
                #[cfg(target_os = "macos")]
                let_go(&window);
                #[cfg(not(target_os = "macos"))]
                let _ = window.destroy();
                continue;
            }
            ask_close(&window);
            let deadline = Instant::now() + Duration::from_secs(60);
            while !let_go_already(&app, &label) && Instant::now() < deadline {
                if !QUITTING.load(Ordering::SeqCst) {
                    // a page kept its window: the windows this Quit let go close, as a close button closes them
                    #[cfg(target_os = "macos")]
                    {
                        let held = LET_GO.lock().unwrap().clone();
                        for label in held {
                            tear_down_later(app.clone(), label);
                        }
                    }
                    return;
                }
                sleep(Duration::from_millis(100));
            }
        }
        end(&app);
    });
}

/// The window in front, else the main window, else any, for the menu's items that act on a page,
/// taken among the app's own pages when `own` asks, so Settings from a print view acts on the app.
fn front(app: &AppHandle, own: bool) -> Option<tauri::WebviewWindow> {
    // never a window let go, hidden as it closes
    let windows: Vec<tauri::WebviewWindow> = app.webview_windows().into_values().filter(|w| !let_go_already(app, w.label())).collect();
    let page = |w: &tauri::WebviewWindow| (!own || own_page(w)) && !let_go_already(app, w.label());
    // a check's windows never take the keyboard, so it names the one standing in front
    #[cfg(feature = "drive")]
    let focused = |w: &tauri::WebviewWindow| drive::FRONT.lock().unwrap().as_deref() == Some(w.label());
    #[cfg(not(feature = "drive"))]
    let focused = |w: &tauri::WebviewWindow| w.is_focused().unwrap_or(false);
    windows.iter().find(|w| focused(w) && page(w)).cloned()
        .or_else(|| app.get_webview_window(MAIN).filter(|w| page(w)))
        .or_else(|| windows.iter().find(|w| page(w)).cloned())
}

/// A page of the server's other than the app's own, the manual, in a window of its own, or the one
/// already open brought forward.
fn page_window(app: &AppHandle, path: &str) {
    let port = PORT.load(Ordering::SeqCst) as u16;
    if let Some(open) = app.webview_windows().into_values()
        .find(|w| w.url().map(|u| u.path() == path).unwrap_or(false) && !let_go_already(app, w.label())) {
        let _ = open.unminimize();
        #[cfg(not(feature = "drive"))]
        let _ = open.set_focus();
        return;
    }
    let Ok(url) = format!("http://127.0.0.1:{port}{path}").parse::<Url>() else { return };
    let label = format!("page-{}", OPENED.fetch_add(1, Ordering::SeqCst));
    let made = handled(WebviewWindowBuilder::new(app, label, WebviewUrl::External(url)).inner_size(900.0, 800.0), app, port, Map::new())
        .min_inner_size(720.0, 480.0)
        .title(app::name())
        .on_document_title_changed(|window, title| {
            let _ = window.set_title(&title);
        })
        .build();
    if let Ok(window) = made {
        if let Some(kept) = KEPT.get() {
            let _ = window.set_zoom(kept.zoom());
        }
        fitted(&window, Some((900.0, 800.0)));
        on_screen(&window);
        #[cfg(feature = "drive")]
        drive::opened(&window);
    }
}

/// A project from Open Recent, in a new window that opens where its card on the home screen opens:
/// a Distil project's page, a Sift project's screening or a Trace project's claims.
fn open_recent(app: &AppHandle, n: usize) {
    let Some(r) = menu::recent_at(n) else { return };
    let mut session = Map::new();
    if r.part == "distil" {
        session.insert(keep::PLACES[1].into(), json!(r.id));
    } else {
        let place = json!({"screen": r.part, "path": r.folder, "at": now_ms()});
        session.insert(keep::PLACES[0].into(), json!(place.to_string()));
    }
    let port = PORT.load(Ordering::SeqCst) as u16;
    let _ = app_window(app, port, None, session);
}

/// An Edit item of Windows's menu bar: the page given the keyboard, then Ctrl and the item's key pressed
/// there, as he would press them, so a field takes them as its own and a board as the app's (Ctrl+Z and
/// Ctrl+Y). The system's own items pressed the keys before the page had the keyboard back from the menu.
#[cfg_attr(target_os = "linux", allow(dead_code))]
fn press_in_page(window: tauri::WebviewWindow, id: &str) {
    let key = match id {
        "edit-undo" => 'Z',
        "edit-redo" => 'Y',
        "edit-cut" => 'X',
        "edit-copy" => 'C',
        "edit-paste" => 'V',
        _ => 'A',
    };
    std::thread::spawn(move || {
        sleep(Duration::from_millis(120));
        let webview: &tauri::Webview = window.as_ref();
        let _ = webview.set_focus();
        sleep(Duration::from_millis(150));
        #[cfg(windows)]
        win::ctrl_and(key as u16);
        #[cfg(not(windows))]
        let _ = key;
    });
}

/// Windows's own part: keys pressed as the keyboard presses them.
#[cfg(windows)]
mod win {
    use windows_sys::Win32::UI::Input::KeyboardAndMouse::{SendInput, INPUT, INPUT_KEYBOARD, KEYEVENTF_KEYUP, VK_CONTROL};

    /// Ctrl and `key`, a letter's virtual key, down and up.
    pub fn ctrl_and(key: u16) {
        unsafe {
            let mut inputs: [INPUT; 4] = std::mem::zeroed();
            for (n, (vk, up)) in [(VK_CONTROL, false), (key, false), (key, true), (VK_CONTROL, true)].into_iter().enumerate() {
                inputs[n].r#type = INPUT_KEYBOARD;
                inputs[n].Anonymous.ki.wVk = vk;
                inputs[n].Anonymous.ki.dwFlags = if up { KEYEVENTF_KEYUP } else { 0 };
            }
            SendInput(inputs.len() as u32, inputs.as_ptr(), std::mem::size_of::<INPUT>() as i32);
        }
    }
}

/// What a menu item does, on the window in front.
fn menu_event(app: &AppHandle, id: &str) {
    #[cfg(feature = "drive")]
    eprintln!("drive: menu item {id}");
    let port = PORT.load(Ordering::SeqCst) as u16;
    match id {
        // a second window on what the app's window in front shows, its page handing over its place
        // (window.js), or the home screen when no window of the app's own is open
        "new-window" => match front(app, true) {
            Some(window) if window.eval(NEW_WINDOW_JS).is_ok() => {}
            _ => aside(app, move |app| {
                let _ = app_window(&app, port, None, Map::new());
            }),
        },
        "quit" => quit_all(app),
        // the window in front, a print view by itself (20 October)
        "zoom-actual" | "zoom-in" | "zoom-out" => {
            let by = match id { "zoom-in" => 1, "zoom-out" => -1, _ => 0 };
            match front(app, false) {
                Some(window) => zoom_on(&window, by),
                None => zoom_by(app, by),
            }
        }
        "manual" => aside(app, |app| page_window(&app, "/manual")),
        "edit-undo" | "edit-redo" | "edit-cut" | "edit-copy" | "edit-paste" | "edit-select-all" => {
            if let Some(window) = front(app, false) {
                #[cfg(not(target_os = "linux"))]
                press_in_page(window, id);
                #[cfg(target_os = "linux")]
                linux_edit_item(&window, id);
            }
        }
        // About is the page's own card, its version, licence and acknowledgements, on either system (20 October)
        // Find and Find and Replace press their keys in the window in front, as Undo and Redo do (barsD, 6 November)
        "settings" | "shortcuts" | "feedback" | "whatsnew" | "about" | "undo" | "redo" | "reload" | "status-bar"
        | "home" | "project-history" | "project-settings" | "find" | "find-replace" => {
            let own = matches!(id, "settings" | "shortcuts" | "feedback" | "whatsnew" | "about" | "home" | "project-history"
                | "project-settings");
            if let Some(window) = front(app, own) {
                let _ = window.eval(format!("window.__idiographMenu && window.__idiographMenu('{id}')"));
                // from a print view's menu, the app's own window comes forward, as a check's never does
                #[cfg(not(feature = "drive"))]
                if own {
                    let _ = window.set_focus();
                }
            }
        }
        _ => {
            if let Some(n) = id.strip_prefix("recent-").and_then(|n| n.parse::<usize>().ok()) {
                aside(app, move |app| open_recent(&app, n));
            }
        }
    }
}

/// A menu's item that makes a window, its work done on a thread of its own: on Windows a window made
/// on the main thread, where a menu's item runs, opened blank and with no menu bar (17 October, the
/// second build's screenshots of New Window).
fn aside(app: &AppHandle, work: impl FnOnce(AppHandle) + Send + 'static) {
    let app = app.clone();
    std::thread::spawn(move || work(app));
}

/// Whether the window-state plugin keeps a size for the main window, which it then restores as the
/// window opens.
fn kept_main_size(app: &AppHandle) -> bool {
    app.path()
        .app_config_dir()
        .ok()
        .and_then(|dir| fs::read_to_string(dir.join(tauri_plugin_window_state::DEFAULT_FILENAME)).ok())
        .and_then(|text| serde_json::from_str::<Value>(&text).ok())
        .map(|kept| kept.get(MAIN).is_some())
        .unwrap_or(false)
}

/// A window on Windows given a menu bar of its own and then its size again below the bar. Every window
/// shared the first's menu bar, which went with the first of them to close, so the print views, the
/// manual and a second window had none (17 October, the second build's screenshots and the third
/// build's first Windows run), and the bar takes its height from the window, so a page asked at 1280 by
/// 800 had 1280 by 780. `size` is none for a main window whose kept size the window-state plugin
/// restores, and a maximised window keeps its own.
#[cfg(windows)]
fn fitted(window: &tauri::WebviewWindow, size: Option<(f64, f64)>) {
    if window.label() != MAIN {
        if let Ok(own) = menu::for_window(window.app_handle(), window.label()) {
            let _ = window.set_menu(own);
        }
    }
    if let Some((width, height)) = size {
        if !window.is_maximized().unwrap_or(false) && !window.is_fullscreen().unwrap_or(false) {
            let _ = window.set_size(tauri::LogicalSize::new(width, height));
        }
    }
}

#[cfg(not(windows))]
fn fitted(_window: &tauri::WebviewWindow, _size: Option<(f64, f64)>) {}

/// Whether a window is one of the app's own page, never a print view's or the manual's, nor a window
/// written in, which has its opener's address.
fn own_page(window: &tauri::WebviewWindow) -> bool {
    window.url().map(|u| u.path() == "/").unwrap_or(false)
        && !WRITTEN.lock().unwrap().iter().any(|label| label == window.label())
}

/// The place a window of `size` at `at` takes to stand whole in a screen's work area, the part the
/// taskbar, the Dock and the menu bar leave: no larger than the area and moved inside it. Physical
/// pixels throughout, the area as (x, y, width, height).
fn fit_in(at: (i32, i32), size: (i32, i32), area: (i32, i32, i32, i32)) -> ((i32, i32), (i32, i32)) {
    let (ax, ay, aw, ah) = area;
    // a screen that says it has no room is no guide, and the window stays as it is
    if aw <= 0 || ah <= 0 {
        return (at, size);
    }
    let (w, h) = (size.0.min(aw).max(1), size.1.min(ah).max(1));
    ((at.0.clamp(ax, ax + aw - w), at.1.clamp(ay, ay + ah - h)), (w, h))
}

/// A window kept whole on its screen, on either system: a window larger than the screen's work area
/// made to fit it, and one that would stand past its edge moved inside, so no foot goes under the
/// taskbar (17 October, the third build's screenshots, a second window's foot under it). Its own
/// screen, or the main one when it stands on none, as after a second screen was taken away.
fn on_screen(window: &tauri::WebviewWindow) {
    if window.is_maximized().unwrap_or(false) || window.is_fullscreen().unwrap_or(false) {
        return;
    }
    let monitor = window.current_monitor().ok().flatten().or_else(|| window.primary_monitor().ok().flatten());
    let Some(monitor) = monitor else { return };
    let area = monitor.work_area();
    let (Ok(at), Ok(outer), Ok(inner)) = (window.outer_position(), window.outer_size(), window.inner_size()) else {
        return;
    };
    let (ow, oh) = (outer.width as i32, outer.height as i32);
    let (place, (w, h)) = fit_in(
        (at.x, at.y),
        (ow, oh),
        (area.position.x, area.position.y, area.size.width as i32, area.size.height as i32),
    );
    if (w, h) != (ow, oh) {
        let frame = (ow - inner.width as i32, oh - inner.height as i32);
        let _ = window.set_size(tauri::PhysicalSize::new((w - frame.0).max(1) as u32, (h - frame.1).max(1) as u32));
    }
    if place != (at.x, at.y) {
        let _ = window.set_position(tauri::PhysicalPosition::new(place.0, place.1));
    }
    #[cfg(feature = "drive")]
    eprintln!("drive: on screen {} at {:?} size {:?} in {:?}", window.label(), place, (w, h),
              (area.position.x, area.position.y, area.size.width, area.size.height));
}

/// A file's name as a save panel may propose it: its last part alone, with nothing a folder name
/// could hide in, and "download" for none.
fn file_name(name: &str) -> String {
    let last = name.rsplit(['/', '\\']).next().unwrap_or("").trim();
    let clean: String = last.chars().filter(|c| !c.is_control() && !matches!(c, ':' | '*' | '?' | '"' | '<' | '>' | '|')).collect();
    if clean.is_empty() || clean == "." || clean == ".." { "download".into() } else { clean }
}

/// A file's kind as a save panel's type list names it: "PNG image (*.png)" on Windows, as Windows
/// names its own, and "PNG image" on a Mac, which shows the kind alone (17 October, the second build).
fn kind_of(ext: &str) -> String {
    let lower = ext.to_lowercase();
    let word = match lower.as_str() {
        "png" => words::t("menus.kind_png"),
        "svg" => words::t("menus.kind_svg"),
        "jpg" | "jpeg" => words::t("menus.kind_jpeg"),
        "pdf" => words::t("menus.kind_pdf"),
        "csv" => words::t("menus.kind_csv"),
        "xlsx" => words::t("menus.kind_xlsx"),
        "docx" => words::t("menus.kind_docx"),
        "json" => words::t("menus.kind_json"),
        "md" => words::t("menus.kind_md"),
        "txt" => words::t("menus.kind_txt"),
        "zip" => words::t("menus.kind_zip"),
        "html" | "htm" => words::t("menus.kind_html"),
        _ => words::t_with("menus.kind_other", &[("kind", &lower.to_uppercase())]),
    };
    if cfg!(windows) { format!("{word} (*.{lower})") } else { word }
}

/// A message about a download, in a sheet on the window or a box over it.
async fn tell(window: &tauri::WebviewWindow, words: String) {
    rfd::AsyncMessageDialog::new()
        .set_title(app::name())
        .set_description(words)
        .set_level(rfd::MessageLevel::Warning)
        .set_parent(window)
        .show()
        .await;
}

/// A line the page asks to have confirmed, OK or Cancel, in a sheet on the window or a box over it (removefix,
/// 9 November 2026): the page's own window.confirm answers Cancel at once in the Mac's web view, which shows no
/// box for it, so Remove from Idiograph and every other confirm did nothing in the window. True for OK.
#[tauri::command]
async fn confirm(window: tauri::WebviewWindow, message: String) -> bool {
    let ok = words::t("menus.ok");
    let answer = rfd::AsyncMessageDialog::new()
        .set_title(app::name())
        .set_description(message)
        .set_level(rfd::MessageLevel::Warning)
        .set_buttons(rfd::MessageButtons::OkCancelCustom(ok.clone(), words::t("menus.cancel")))
        .set_parent(&window)
        .show()
        .await;
    #[cfg(feature = "drive")]
    let answer = drive::confirmed(answer);
    matches!(answer, rfd::MessageDialogResult::Ok)
        || matches!(&answer, rfd::MessageDialogResult::Custom(word) if *word == ok)
}

/// The folder a save panel opens on: Downloads, when it is there.
fn downloads(window: &tauri::WebviewWindow) -> Option<PathBuf> {
    window.path().download_dir().ok().filter(|dir| dir.is_dir())
}

/// The system's save panel on the window, the file's name in it, its kind the one type and Downloads
/// its folder, and `message` its line when there is one (the panel's message on a Mac, its title on
/// Windows): the path he chose, or None for Cancel.
async fn save_panel(window: &tauri::WebviewWindow, name: &str, message: &str) -> Option<PathBuf> {
    let mut panel = rfd::AsyncFileDialog::new().set_file_name(name).set_parent(window);
    if !message.trim().is_empty() {
        panel = panel.set_title(pick_title(message));
    }
    // the file's kind as the panel's one type, so the name keeps its ending, named as the system names it
    if let Some((_, ext)) = name.rsplit_once('.').filter(|(stem, ext)| !stem.is_empty() && !ext.is_empty() && ext.len() <= 8) {
        panel = panel.add_filter(kind_of(ext), &[ext]);
    }
    if let Some(dir) = downloads(window) {
        panel = panel.set_directory(dir);
    }
    let chosen = panel.save_file().await.map(|handle| handle.path().to_path_buf());
    #[cfg(feature = "drive")]
    let chosen = drive::save_to(chosen, name);
    chosen
}

/// Where to save a file the server then writes itself, Send's whole project (21 October): the save
/// panel alone, nothing read or written here, so a project with its recordings never passes through
/// the page. The path he chose, or None for Cancel.
#[tauri::command]
async fn save_path(window: tauri::WebviewWindow, name: String, message: Option<String>) -> Option<String> {
    save_panel(&window, &file_name(&name), message.as_deref().unwrap_or("")).await.map(|p| p.display().to_string())
}

/// A download from the page (`window.js`): the system's save panel, with the file's name in it and
/// Downloads its folder, then the file written where it was put. Cancel saves nothing and says
/// nothing. A file the page could not read, or one that could not be written, says so.
#[tauri::command]
async fn save_download(window: tauri::WebviewWindow, name: String, data: Option<String>) -> Result<String, String> {
    let name = file_name(&name);
    let Some(bytes) = data.and_then(|d| base64::engine::general_purpose::STANDARD.decode(d).ok()) else {
        tell(&window, words::t_with("menus.not_saved", &[("app", app::name()), ("name", &name)])).await;
        return Err("not read".into());
    };
    let Some(path) = save_panel(&window, &name, "").await else {
        return Ok("cancelled".into());
    };
    match fs::write(&path, &bytes) {
        Ok(()) => Ok(path.display().to_string()),
        Err(err) => {
            let shown = path.file_name().map(|n| n.to_string_lossy().into_owned()).unwrap_or(name);
            let folder = path.parent().map(|p| p.display().to_string()).unwrap_or_default();
            tell(&window, words::t_with("menus.not_saved_in", &[("app", app::name()), ("name", &shown), ("folder", &folder)])).await;
            Err(err.to_string())
        }
    }
}

/// A link to anywhere but the server, opened in the default browser.
fn outside(url: &Url) {
    eprintln!("Idiograph: outside link {url}");
    #[cfg(feature = "drive")]
    if env::var("IDIOGRAPH_WINDOW_NO_OPEN").is_ok() {
        return;
    }
    let _ = tauri_plugin_opener::open_url(url.as_str(), None::<&str>);
}

/// A download the page's own script did not take, the web view's own: saved in Downloads under a
/// name not yet there, and a message once it ends, where it went or that it failed, so it never
/// goes without a word.
fn native_download(webview: tauri::Webview, event: DownloadEvent<'_>) -> bool {
    match event {
        DownloadEvent::Requested { destination, .. } => {
            let name = destination.file_name().map(|n| n.to_string_lossy().into_owned()).unwrap_or_default();
            let dir = webview.path().download_dir().unwrap_or_else(|_| destination.parent().map(Path::to_path_buf).unwrap_or_default());
            let name = file_name(&name);
            let (stem, ext) = match name.rsplit_once('.') {
                Some((s, e)) if !s.is_empty() => (s.to_string(), format!(".{e}")),
                _ => (name.clone(), String::new()),
            };
            let mut path = dir.join(&name);
            let mut n = 2;
            while path.exists() {
                path = dir.join(format!("{stem} ({n}){ext}"));
                n += 1;
            }
            *destination = path;
            true
        }
        DownloadEvent::Finished { path, success, .. } => {
            let window = webview.window();
            let words = match (&path, success) {
                (Some(p), true) => words::t_with("menus.saved_in", &[
                    ("app", app::name()),
                    ("name", &p.file_name().map(|n| n.to_string_lossy().into_owned()).unwrap_or_default()),
                    ("folder", &p.parent().map(|d| d.display().to_string()).unwrap_or_default()),
                ]),
                _ => words::t_app("menus.not_saved_file"),
            };
            if let Some(window) = window.get_webview_window(window.label()) {
                tauri::async_runtime::spawn(async move { tell(&window, words).await });
            }
            true
        }
        _ => true,
    }
}

/// The arguments wry gives WebView2 when the program gives none: the mini menu and SmartScreen off.
#[cfg(windows)]
const WRY_ARGS: &str = "--disable-features=msWebOOUI,msPdfOOUI,msSmartScreenProtection";

/// Every Idiograph window shares one tabbing identifier, so on a Mac they merge into tabs with
/// Window, Merge All Windows, and Cmd+Shift+] moves between them.
#[cfg(target_os = "macos")]
const TABS: &str = "idiograph";

/// The script every window runs before the page's own: the system's name, what the window hands
/// the page as it opens, the page's kept settings and `session`, a place to start on, this start's key
/// (key.rs), then `window.js`.
fn window_script(session: &Map<String, Value>) -> String {
    let os = if cfg!(target_os = "macos") { "macos" } else if cfg!(windows) { "windows" } else { "other" };
    let local = KEPT.get().and_then(keep::Kept::local).map(Value::Object).unwrap_or(Value::Null);
    let seed = json!({"local": local, "session": session});
    let key = key::key();
    format!("window.__IDIOGRAPH_OS__ = '{os}';\nwindow.__IDIOGRAPH_SEED__ = {seed};\nwindow.__IDIOGRAPH_KEY__ = '{key}';\n{WINDOW_JS}")
}

/// The window's handlers: a page the server serves, or about:blank the page then writes into,
/// opens in a window of its own, anything else in the default browser, a download the page's
/// script did not take lands in Downloads with a word, and Tauri's own handling of drops is off, so
/// the page's own takes a file dragged onto it.
fn handled<'a>(
    builder: WebviewWindowBuilder<'a, tauri::Wry, AppHandle>,
    app: &AppHandle,
    port: u16,
    session: Map<String, Value>,
) -> WebviewWindowBuilder<'a, tauri::Wry, AppHandle> {
    let app_ = app.clone();
    #[cfg(target_os = "macos")]
    let builder = builder.tabbing_identifier(TABS);
    // WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS went unread on the first Windows run of 17 October, the
    // window giving wry's own arguments, so the window adds the variable's to them, the same for
    // every window, as WebView2 asks. Nothing sets it but a check's run (drive_windows.py)
    #[cfg(windows)]
    let builder = match env::var("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS") {
        Ok(more) if !more.trim().is_empty() => builder.additional_browser_args(&format!("{WRY_ARGS} {}", more.trim())),
        _ => builder,
    };
    let builder = builder
        .initialization_script(window_script(&session))
        // the page's own zoom keys and pinch off, as View's Zoom In, Zoom Out and Actual Size, which
        // window.js asks for on Cmd or Ctrl with + - and 0, are the window's, one zoom for the app
        .zoom_hotkeys_enabled(false)
        .on_navigation(move |url| {
            if inner(url, port) {
                return true;
            }
            outside(url);
            false
        })
        .on_new_window(move |url, features| {
            if !inner(&url, port) {
                outside(&url);
                return NewWindowResponse::Deny;
            }
            let label = format!("page-{}", OPENED.fetch_add(1, Ordering::SeqCst));
            if url.scheme() == "about" {
                WRITTEN.lock().unwrap().push(label.clone());
            }
            // the size of a main window unless the page asks for its own, as a browser opens a tab
            let asked = features.size().map(|s| (s.width, s.height)).unwrap_or((1280.0, 800.0));
            let made = handled(
                WebviewWindowBuilder::new(&app_, label, WebviewUrl::External(url.clone())).inner_size(1280.0, 800.0),
                &app_,
                port,
                Map::new(),
            )
            .window_features(features)
            // no window of the app narrower than the main one's least, 720 wide
            .min_inner_size(720.0, 480.0)
            .title(app::name())
            .on_document_title_changed(|window, title| {
                let _ = window.set_title(&title);
            })
            .build();
            match made {
                Ok(window) => {
                    if let Some(kept) = KEPT.get() {
                        let _ = window.set_zoom(kept.zoom());
                    }
                    fitted(&window, Some(asked));
                    on_screen(&window);
                    #[cfg(feature = "drive")]
                    drive::opened(&window);
                    NewWindowResponse::Create { window }
                }
                Err(_) => NewWindowResponse::Deny,
            }
        })
        .on_download(native_download)
        .disable_drag_drop_handler();
    #[cfg(feature = "drive")]
    let builder = drive::placed(drive::loaded(builder));
    builder
}

/// An Idiograph window on the server's home page: the first, `main`, or another from New Window or
/// Open Recent, `session` the place it starts on. It takes its page's title, so two windows on two
/// cases tell apart in the Dock, the taskbar and Alt+Tab, and the app's zoom. The window-state
/// plugin puts `main` where it was when the app last quit.
fn app_window(app: &AppHandle, port: u16, label: Option<&str>, session: Map<String, Value>) -> tauri::Result<tauri::WebviewWindow> {
    app_window_at(app, port, label, session, None)
}

/// An Idiograph window as `app_window` makes one, its address ending in `fragment` after its #.
fn app_window_at(app: &AppHandle, port: u16, label: Option<&str>, session: Map<String, Value>,
                 fragment: Option<&str>) -> tauri::Result<tauri::WebviewWindow> {
    let mut url: Url = format!("http://127.0.0.1:{port}/").parse().expect("a page address");
    url.set_fragment(fragment);
    let label = label.map(str::to_string).unwrap_or_else(|| format!("page-{}", OPENED.fetch_add(1, Ordering::SeqCst)));
    // the main window's kept size is the window-state plugin's to restore, never set again here
    let restored = label == MAIN && kept_main_size(app);
    let mut builder = WebviewWindowBuilder::new(app, label, WebviewUrl::External(url))
        .title(app::name())
        .inner_size(1280.0, 800.0)
        // the smallest window the bars are drawn for, 720 wide (Adam, 26 October 2026, 360 dropped)
        .min_inner_size(720.0, 480.0)
        .on_document_title_changed(|window, title| {
            let title = if title.trim().is_empty() { app::name() } else { title.trim() };
            #[cfg(feature = "drive")]
            eprintln!("drive: title {} {title}", window.label());
            let _ = window.set_title(title);
        });
    // a new window steps down and right of the first, as a browser's does, never exactly over it, a step
    // for each window of the app's own page already open, at most five, where the second build stepped
    // by every window ever opened, print views among them, so a second window opened 196 pixels down
    // with its foot under the taskbar (17 October, the third build's screenshots)
    if let Some(first) = app.get_webview_window(MAIN) {
        if let (Ok(at), Ok(scale)) = (first.outer_position(), first.scale_factor()) {
            let open = app.webview_windows().values().filter(|w| own_page(w)).count().min(5);
            let step = 28.0 * open as f64;
            builder = builder.position(at.x as f64 / scale + step, at.y as f64 / scale + step);
        }
    }
    let window = handled(builder, app, port, session).build()?;
    if let Some(kept) = KEPT.get() {
        let _ = window.set_zoom(kept.zoom());
    }
    fitted(&window, if restored { None } else { Some((1280.0, 800.0)) });
    #[cfg(target_os = "linux")]
    if window.label() == MAIN {
        linux_size::restore(&window);
    }
    on_screen(&window);
    #[cfg(target_os = "macos")]
    mac::spelling_window(&window);
    #[cfg(feature = "drive")]
    drive::opened(&window);
    Ok(window)
}

/// A second start of Idiograph brings the open window forward and starts nothing.
fn bring_forward(app: &AppHandle) {
    let windows = app.webview_windows();
    // never a window let go, hidden as it closes
    let shown = |w: &&tauri::WebviewWindow| !let_go_already(app, w.label());
    let window = windows.get(MAIN).filter(shown).or_else(|| windows.values().find(shown));
    // a check says it and takes nothing from whoever is at the machine
    #[cfg(feature = "drive")]
    if let Some(window) = window {
        eprintln!("drive: brought forward {}", window.label());
        return;
    }
    if let Some(window) = window {
        let _ = window.unminimize();
        let _ = window.show();
        let _ = window.set_focus();
    }
}

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    if hands_over(&args) {
        hand_over(&args);
    }
    // a shared copy Explorer opens is the command line's file, kept for the first window's page, never the server's
    let (args, files) = opening::apart(&args, &env::current_dir().unwrap_or_default());
    opening::keep(files);
    let (port_text, extra) = split_args(&args);
    // the single-instance plugin first, so a second start ends before it starts a server. A second start with a
    // shared copy, Explorer's while Idiograph runs, hands the file to the window in front, which comes forward
    // (opening.rs). Its arguments begin with its own executable's path
    let builder = tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, args, cwd| {
            let (_, files) = opening::apart(args.get(1..).unwrap_or(&[]), Path::new(&cwd));
            if !opening::hand(app, files) {
                bring_forward(app);
            }
        }))
        // the main window's size and place kept across a quit, and restored as it opens; the others
        // open stepped down from it, as a browser's do
        .plugin(
            tauri_plugin_window_state::Builder::default()
                .with_state_flags(window_state_flags())
                .with_filter(|label| label == MAIN)
                .build(),
        )
        // Idiograph's updates, from the releases repository, each file checked against the public key in
        // tauri.conf.json before it is kept (update.rs, the fourth build)
        .plugin(tauri_plugin_updater::Builder::new().build())
        .invoke_handler(tauri::generate_handler![print, new_window, save_download, save_path, pick, confirm, opened, keep, recent, project_now, zoom, edit, announce, closing, updates])
        .menu(menu::build)
        .on_menu_event(|app, event| menu_event(app, event.id().as_ref()))
        // a window of the app's own page closed by its close button or Close Window asks its page
        // first (see ask_close). A print view or the manual has nothing to save and closes at once,
        // as it must while its print panel holds its page (17 October, the second build's first
        // Windows run, where a print view held open by its print panel held the main page too)
        .on_window_event(|window, event| {
            // a window gone takes its own menu bar with it (see menu::for_window)
            if let WindowEvent::Destroyed = event {
                menu::forget(window.label());
            }
            // on Linux the main window's size in logical pixels, kept as it closes (see linux_size)
            #[cfg(target_os = "linux")]
            if window.label() == MAIN {
                linux_size::seen(window, event);
            }
            if let WindowEvent::CloseRequested { api, .. } = event {
                if let Some(webview) = window.app_handle().get_webview_window(window.label()) {
                    // never a window written in, the canvas's print, whose page answered as its
                    // opener's and so closed the window behind it (20 October)
                    if own_page(&webview) {
                        api.prevent_close();
                        ask_close(&webview);
                    } else if cfg!(target_os = "macos") && alone(window.app_handle(), window.label()) {
                        // a print view or the manual as the last window: the app ends as Quit ends it,
                        // its web view never torn down first (see let_go)
                        api.prevent_close();
                        let_go(&webview);
                    }
                }
            }
        });
    let app = builder
        .setup(move |app| {
            let handle = app.handle().clone();
            if let Ok(dir) = handle.path().app_config_dir() {
                let _ = KEPT.set(keep::Kept::load(dir));
            }
            // a signal to the window ends it as Quit does, its server with it (see ending)
            #[cfg(unix)]
            ending::listen(&handle);
            // whether this run is the first of a newer version, and the check at start and once a day
            update::begin(&handle);
            #[cfg(target_os = "macos")]
            {
                // Edit, Spelling and Grammar, as a browser has it (each window turns spelling on, see
                // mac::spelling_window)
                let _ = handle.run_on_main_thread(mac::spelling_menu);
                // a mouse's back and forward buttons as Back and Forward (see mac::mouse_buttons)
                let buttons = handle.clone();
                let _ = handle.run_on_main_thread(move || mac::mouse_buttons(&buttons));
            }
            #[cfg(feature = "drive")]
            {
                drive::awake();
                drive::sheets(&handle);
                drive::edit_menu(&handle);
            }
            std::thread::spawn(move || {
                if let Err(said) = launch(&handle, port_text, &extra) {
                    eprintln!("Idiograph: {said}");
                    // the message on the main thread, once the app runs, then the app ends
                    let app = handle.clone();
                    let _ = handle.run_on_main_thread(move || {
                        rfd::MessageDialog::new()
                            .set_title(app::name())
                            .set_description(said)
                            .set_level(rfd::MessageLevel::Warning)
                            .show();
                        app.exit(1);
                    });
                }
            });
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("the window");
    // the app ends when its last window closes, as Tauri ends it, and the server with it, and then an
    // update downloaded and not yet installed is put in place, so the next start is the new version
    app.run(|_app, event| {
        // a shared copy the Mac's system asks the app to open, a double click in the Finder, a drop on the Dock's
        // icon or Open With, whether it started the app or the app was open (opening.rs)
        #[cfg(target_os = "macos")]
        if let RunEvent::Opened { urls } = &event {
            opening::hand(_app, opening::in_urls(urls));
        }
        if let RunEvent::Exit = event {
            EXITING.store(true, Ordering::SeqCst);
            #[cfg(target_os = "linux")]
            linux_size::keep();
            // Quit's and the last window's own end stopped it already (see `end`), and this waits for that
            if let Some(side) = SIDE.get() {
                let begun = Instant::now();
                if stop_server(side) {
                    eprintln!("Idiograph: the server stopped {} ms after the window closed", begun.elapsed().as_millis());
                }
            }
            update::at_quit();
        }
    });
}

/// What the window-state plugin keeps of the main window: its size, its place, whether it was
/// maximised or full screen, never whether it was shown, so a check's window is never brought
/// forward as it opens.
fn window_state_flags() -> tauri_plugin_window_state::StateFlags {
    use tauri_plugin_window_state::StateFlags;
    StateFlags::SIZE | StateFlags::POSITION | StateFlags::MAXIMIZED | StateFlags::FULLSCREEN
}

/// The main window's size on Linux in logical pixels (linuxfix, 9 November 2026). The window-state plugin keeps
/// the size in the display's own pixels and sets it again as those, so on GTK, which sizes a window in logical
/// pixels, a window kept at 200% opened twice as big at 100% and one kept at 100% half as big at 200%. The plugin
/// still keeps the place, maximised and full screen, and this keeps the size as the window last stood (keep.rs, `size`),
/// and puts it back once the plugin has placed the window.
#[cfg(target_os = "linux")]
mod linux_size {
    use std::sync::Mutex;

    use tauri::WindowEvent;

    use super::KEPT;

    /// The size the main window last stood at, unmaximised, not full screen.
    static NOW: Mutex<Option<(f64, f64)>> = Mutex::new(None);

    /// The kept size given to the main window as it opens, unless the plugin maximised it or made it full screen.
    pub fn restore(window: &tauri::WebviewWindow) {
        let Some((width, height)) = KEPT.get().and_then(|kept| kept.size()) else { return };
        *NOW.lock().unwrap() = Some((width, height));
        if window.is_maximized().unwrap_or(false) || window.is_fullscreen().unwrap_or(false) {
            return;
        }
        let _ = window.set_size(tauri::LogicalSize::new(width, height));
    }

    /// Each new size of the main window noted, in logical pixels, and kept as it goes.
    pub fn seen(window: &tauri::Window, event: &WindowEvent) {
        match event {
            WindowEvent::Resized(size) => {
                let whole = !window.is_maximized().unwrap_or(false) && !window.is_fullscreen().unwrap_or(false)
                    && !window.is_minimized().unwrap_or(false);
                if let (true, Ok(scale)) = (whole, window.scale_factor()) {
                    let at = size.to_logical::<f64>(scale);
                    *NOW.lock().unwrap() = Some((at.width, at.height));
                }
            }
            WindowEvent::Destroyed => keep(),
            _ => {}
        }
    }

    /// The main window's state as it stands, maximised or not, saved by the window-state plugin before the window goes
    /// (linuxfix3, 9 November 2026). The plugin notes maximised only as a close button is pressed and at exit, when a
    /// window already gone is not asked, so a window Quit closed kept the maximised it opened with, though Super+Down
    /// had put it back to its size. Done on the main thread, where the plugin's own notes are taken, so neither waits
    /// on the other, and before the window is destroyed, which the main thread does next.
    pub fn state_before_going(window: &tauri::WebviewWindow) {
        use tauri::Manager;
        if window.label() != super::MAIN {
            return;
        }
        let app = window.app_handle().clone();
        let _ = window.run_on_main_thread(move || {
            use tauri_plugin_window_state::AppHandleExt;
            let _ = app.save_window_state(super::window_state_flags());
        });
    }

    /// The size last seen written to window.json.
    pub fn keep() {
        let now = *NOW.lock().unwrap();
        if let (Some(kept), Some((width, height))) = (KEPT.get(), now) {
            kept.set_size(width, height);
        }
    }
}

/// The Mac's own parts of the window: spelling as a browser has it, and the Edit menu's actions sent
/// to the field with the focus.
#[cfg(target_os = "macos")]
mod mac {
    use objc2::runtime::{AnyObject, Sel};
    use objc2::{class, msg_send, sel, DefinedClass};
    use tauri::{AppHandle, Manager};

    /// A mouse's back and forward buttons, the Mac's buttons 3 and 4, as Back and Forward in the window
    /// they are pressed over, as a browser has them (19 October, Adam pressing his mouse's back button on
    /// a passage he opened from a PETs card). The Mac's web view gives the page no such buttons and goes
    /// nowhere by them, so the app takes them before the web view sees them, on the press, and the page's
    /// history steps as a browser's Back and Forward step it. The release is taken too, so the web view
    /// never sees half a click. Every other button, and every other event, goes on as it came.
    pub fn mouse_buttons(app: &AppHandle) {
        // NSEventMaskOtherMouseDown and NSEventMaskOtherMouseUp
        const OTHER_MOUSE: u64 = (1 << 25) | (1 << 26);
        // NSEventTypeOtherMouseDown
        const DOWN: usize = 25;
        let app = app.clone();
        let monitor = block2::RcBlock::new(move |event: *mut AnyObject| -> *mut AnyObject {
            if event.is_null() {
                return event;
            }
            unsafe {
                let number: isize = msg_send![event, buttonNumber];
                let step = match number {
                    3 => "back",
                    4 => "forward",
                    _ => return event,
                };
                let kind: usize = msg_send![event, type];
                if kind == DOWN {
                    let over: *mut AnyObject = msg_send![event, window];
                    let windows = app.webview_windows();
                    let window = windows
                        .values()
                        .find(|w| !over.is_null() && w.ns_window().map(|p| p as *mut AnyObject == over).unwrap_or(false))
                        .or_else(|| windows.values().find(|w| w.is_focused().unwrap_or(false)))
                        .or_else(|| windows.get(super::MAIN));
                    #[cfg(feature = "drive")]
                    eprintln!("drive: mouse button {number} {step} on {}", window.map(|w| w.label()).unwrap_or("none"));
                    if let Some(window) = window {
                        let _ = window.eval(format!("window.history.{step}()"));
                    }
                }
                std::ptr::null_mut()
            }
        });
        unsafe {
            let held: *mut AnyObject =
                msg_send![class!(NSEvent), addLocalMonitorForEventsMatchingMask: OTHER_MOUSE, handler: &*monitor];
            // the monitor lasts as long as the app, so neither it nor its block is ever let go
            std::mem::forget(monitor);
            let _ = held;
        }
    }

    unsafe fn text(s: &str) -> *mut AnyObject {
        let c = std::ffi::CString::new(s).unwrap_or_default();
        msg_send![class!(NSString), stringWithUTF8String: c.as_ptr()]
    }

    /// Spelling and Grammar in Edit after Select All, as Safari and TextEdit have it, each item's action
    /// sent to the field with the focus, which ticks the ones that are on.
    pub fn spelling_menu() {
        unsafe {
            let ns_app: *mut AnyObject = msg_send![class!(NSApplication), sharedApplication];
            let main: *mut AnyObject = msg_send![ns_app, mainMenu];
            if main.is_null() {
                return;
            }
            let edit_item: *mut AnyObject = msg_send![main, itemWithTitle: text(&crate::words::t("menus.edit"))];
            if edit_item.is_null() {
                return;
            }
            let edit: *mut AnyObject = msg_send![edit_item, submenu];
            let spelling = crate::words::t("menus.spelling");
            let had: *mut AnyObject = msg_send![edit, itemWithTitle: text(&spelling)];
            if edit.is_null() || !had.is_null() {
                return;
            }
            let sub: *mut AnyObject = msg_send![class!(NSMenu), alloc];
            let sub: *mut AnyObject = msg_send![sub, initWithTitle: text(&spelling)];
            let t = crate::words::t;
            let rows: [(String, Option<Sel>, &str); 6] = [
                (t("menus.spelling_show"), Some(sel!(showGuessPanel:)), ":"),
                (t("menus.spelling_check_now"), Some(sel!(checkSpelling:)), ";"),
                (String::new(), None, ""),
                (t("menus.spelling_while_typing"), Some(sel!(toggleContinuousSpellChecking:)), ""),
                (t("menus.spelling_grammar"), Some(sel!(toggleGrammarChecking:)), ""),
                (t("menus.spelling_correct"), Some(sel!(toggleAutomaticSpellingCorrection:)), ""),
            ];
            for (title, action, key) in rows {
                let item: *mut AnyObject = if action.is_none() {
                    msg_send![class!(NSMenuItem), separatorItem]
                } else {
                    let made: *mut AnyObject = msg_send![class!(NSMenuItem), alloc];
                    msg_send![made, initWithTitle: text(&title), action: action, keyEquivalent: text(key)]
                };
                let _: () = msg_send![sub, addItem: item];
            }
            let parent: *mut AnyObject = msg_send![class!(NSMenuItem), alloc];
            let none: Option<Sel> = None;
            let parent: *mut AnyObject = msg_send![parent, initWithTitle: text(&spelling), action: none, keyEquivalent: text("")];
            let _: () = msg_send![parent, setSubmenu: sub];
            // straight after Select All, where Apple puts it, ahead of the items AppKit adds at the foot
            // of Edit, AutoFill, Start Dictation and Emoji & Symbols, where it stood after them (17
            // October, the second build's screenshots)
            let line: *mut AnyObject = msg_send![class!(NSMenuItem), separatorItem];
            let all: isize = msg_send![edit, indexOfItemWithTitle: text(&crate::words::t("menus.select_all"))];
            if all >= 0 {
                let _: () = msg_send![edit, insertItem: line, atIndex: all + 1];
                let _: () = msg_send![edit, insertItem: parent, atIndex: all + 2];
            } else {
                let _: () = msg_send![edit, addItem: line];
                let _: () = msg_send![edit, addItem: parent];
            }
        }
    }

    /// Whether a window's web view checks spelling as it is typed, and whether he has ever chosen,
    /// the key in the app's own defaults rather than the default registered above.
    pub unsafe fn spelling_state(wk: *mut AnyObject) -> (bool, bool) {
        let can: bool = msg_send![wk, respondsToSelector: sel!(isContinuousSpellCheckingEnabled)];
        let on: bool = if can { msg_send![wk, isContinuousSpellCheckingEnabled] } else { false };
        let defaults: *mut AnyObject = msg_send![class!(NSUserDefaults), standardUserDefaults];
        let domain: *mut AnyObject = msg_send![class!(NSBundle), mainBundle];
        let name: *mut AnyObject = msg_send![domain, bundleIdentifier];
        let mine: *mut AnyObject = if name.is_null() { std::ptr::null_mut() } else { msg_send![defaults, persistentDomainForName: name] };
        let chosen: *mut AnyObject = if mine.is_null() { std::ptr::null_mut() } else { msg_send![mine, objectForKey: text("WebContinuousSpellCheckingEnabled")] };
        (on, !chosen.is_null())
    }

    /// Check Spelling While Typing turned on in a window's web view, as Edit, Spelling and Grammar turns
    /// it on, while he has never chosen, which WebKit then keeps in the app's defaults: a Mac's web view
    /// has it off, and underlined nothing (17 October), and a default registered for it went unread.
    pub fn spelling_window(window: &tauri::WebviewWindow) {
        let _ = window.with_webview(|webview| unsafe {
            let wk = webview.inner() as *mut AnyObject;
            let (on, chosen) = spelling_state(wk);
            if !on && !chosen {
                let can: bool = msg_send![wk, respondsToSelector: sel!(toggleContinuousSpellChecking:)];
                if can {
                    let none: *mut AnyObject = std::ptr::null_mut();
                    let _: () = msg_send![wk, toggleContinuousSpellChecking: none];
                }
            }
        });
    }

    /// A size as AppKit takes it, NSSize, two CGFloats.
    #[repr(C)]
    #[derive(Clone, Copy, Debug)]
    pub struct Size {
        pub width: f64,
        pub height: f64,
    }

    unsafe impl objc2::Encode for Size {
        const ENCODING: objc2::Encoding = objc2::Encoding::Struct("CGSize", &[f64::ENCODING, f64::ENCODING]);
    }

    /// A rectangle as AppKit takes it, NSRect, for a check's print alone.
    #[repr(C)]
    #[derive(Clone, Copy, Debug)]
    pub struct Rect {
        pub x: f64,
        pub y: f64,
        pub size: Size,
    }

    unsafe impl objc2::Encode for Rect {
        const ENCODING: objc2::Encoding = objc2::Encoding::Struct(
            "CGRect", &[objc2::Encoding::Struct("CGPoint", &[f64::ENCODING, f64::ENCODING]), Size::ENCODING]);
    }

    /// What a print holds until it has run: the web view, kept alive, and the zoom it had.
    pub struct Printing {
        wk: *mut AnyObject,
        zoom: Option<f64>,
        /// the operation's view, when the window draws its foot, to let its foot go once the print has run
        footed: std::cell::Cell<usize>,
        ran: std::cell::Cell<bool>,
    }

    objc2::define_class!(
        // NSObject asks nothing of a subclass, and this one has no Drop
        #[unsafe(super(objc2::runtime::NSObject))]
        #[thread_kind = objc2::MainThreadOnly]
        #[name = "IdiographPrinted"]
        #[ivars = Printing]
        pub struct Printed;

        impl Printed {
            /// The print operation's end, its panel answered or a check's file written: the web view's own
            /// zoom given back and the page's foot let go.
            #[unsafe(method(printOperationDidRun:success:contextInfo:))]
            fn did_run(&self, _op: *mut AnyObject, _success: objc2::runtime::Bool, _context: *mut std::ffi::c_void) {
                let held = self.ivars();
                if held.ran.replace(true) {
                    return;
                }
                unsafe {
                    if let Some(zoom) = held.zoom {
                        let _: () = msg_send![held.wk, setPageZoom: zoom];
                    }
                    let _: () = msg_send![held.wk, release];
                }
                if held.footed.get() != 0 {
                    if let Ok(mut feet) = FEET.lock() {
                        feet.retain(|(v, _)| *v != held.footed.get());
                    }
                }
            }
        }
    );

    thread_local! {
        /// Each print's delegate, kept until its print has run, since the operation keeps none of its own.
        static PRINTING: std::cell::RefCell<Vec<objc2::rc::Retained<Printed>>> = const { std::cell::RefCell::new(Vec::new()) };
    }

    /// The print panel on a window's web view, `wk`, as Tauri's own print opens it (wry's
    /// print_with_options, its margins nothing, so the page's @page margins hold), with `landscape`
    /// and `paper` (points, portrait) set first when the page asks for them, on a copy of the shared
    /// print info, which stays as it was for the next print (see `print`). `save` writes the PDF there
    /// with no panel, as the panel's Save as PDF would: a check's print (`drive::print_to`).
    ///
    /// The web view prints at its own size whatever the window's zoom (31 October, pdfexport): the Mac's
    /// web view lays a print out at its page zoom, so the table of PETs came out 3% larger at Large and
    /// 14% larger at 200%, with four pages more. Its zoom is set to 100% for the print and given back once
    /// the print has run, the panel's Cancel among the ways it ends.
    pub unsafe fn print(wk: *mut AnyObject, ns_window: *mut AnyObject, landscape: Option<bool>, paper: Option<(f64, f64)>,
                        save: Option<std::path::PathBuf>, foot: Option<serde_json::Value>) {
        if wk.is_null() || ns_window.is_null() {
            return;
        }
        let can: bool = msg_send![wk, respondsToSelector: sel!(printOperationWithPrintInfo:)];
        let Some(main) = objc2::MainThreadMarker::new() else { return };
        if !can {
            return;
        }
        // the zoom held at 100% for the print, the window's own kept to give back
        let zooms: bool = msg_send![wk, respondsToSelector: sel!(pageZoom)];
        let was: Option<f64> = if zooms {
            let zoom: f64 = msg_send![wk, pageZoom];
            if (zoom - 1.0).abs() > 1e-6 {
                let _: () = msg_send![wk, setPageZoom: 1.0f64];
                Some(zoom)
            } else {
                None
            }
        } else {
            None
        };
        let _: *mut AnyObject = msg_send![wk, retain];
        let made = main.alloc::<Printed>().set_ivars(Printing {
            wk, zoom: was, footed: std::cell::Cell::new(0), ran: std::cell::Cell::new(false),
        });
        let delegate: objc2::rc::Retained<Printed> = msg_send![super(made), init];
        let delegate_ptr: *const Printed = &*delegate;
        PRINTING.with(|held| {
            let mut held = held.borrow_mut();
            // a print that has run lets its delegate go
            held.retain(|d| !d.ivars().ran.get());
            held.push(delegate);
        });
        let shared: *mut AnyObject = msg_send![class!(NSPrintInfo), sharedPrintInfo];
        let own = landscape.is_some() || save.is_some();
        let info: *mut AnyObject = if own {
            // the copy is the run loop's to let go of, the operation keeping its own
            let made: *mut AnyObject = msg_send![shared, copy];
            msg_send![made, autorelease]
        } else {
            shared
        };
        let _: () = msg_send![info, setTopMargin: 0.0f64];
        let _: () = msg_send![info, setRightMargin: 0.0f64];
        let _: () = msg_send![info, setBottomMargin: 0.0f64];
        let _: () = msg_send![info, setLeftMargin: 0.0f64];
        if let Some(landscape) = landscape {
            if let Some((w, h)) = paper {
                let _: () = msg_send![info, setPaperSize: Size { width: w, height: h }];
            }
            // NSPaperOrientationPortrait 0, NSPaperOrientationLandscape 1, which turns the paper with it
            let _: () = msg_send![info, setOrientation: if landscape { 1isize } else { 0isize }];
        }
        if let Some(path) = &save {
            #[link(name = "AppKit", kind = "framework")]
            extern "C" {
                static NSPrintJobSavingURL: *mut AnyObject;
                static NSPrintSaveJob: *mut AnyObject;
            }
            let url: *mut AnyObject = msg_send![class!(NSURL), fileURLWithPath: text(&path.display().to_string())];
            let dict: *mut AnyObject = msg_send![info, dictionary];
            let _: () = msg_send![dict, setObject: url, forKey: NSPrintJobSavingURL];
            let _: () = msg_send![info, setJobDisposition: NSPrintSaveJob];
        }
        #[cfg(feature = "drive")]
        {
            let turned: isize = msg_send![info, orientation];
            let size: Size = msg_send![info, paperSize];
            eprintln!("drive: print info orientation {turned} paper {:.0} x {:.0}", size.width, size.height);
        }
        let op: *mut AnyObject = msg_send![wk, printOperationWithPrintInfo: info];
        if op.is_null() {
            // nothing to run, so the zoom is given back
            let nothing: *mut AnyObject = std::ptr::null_mut();
            let _: () = msg_send![delegate_ptr, printOperationDidRun: nothing, success: objc2::runtime::Bool::NO,
                                  contextInfo: std::ptr::null_mut::<std::ffi::c_void>()];
            return;
        }
        let _: () = msg_send![op, setCanSpawnSeparateThread: true];
        // the page's foot, which the Mac's web view never draws, drawn on each page by the window
        if let Some(foot) = foot.as_ref().and_then(Foot::read) {
            let view: *mut AnyObject = msg_send![op, view];
            if footed(view, foot) {
                (*delegate_ptr).ivars().footed.set(view as usize);
            }
        }
        if save.is_some() {
            let _: () = msg_send![op, setShowsPrintPanel: false];
            let _: () = msg_send![op, setShowsProgressPanel: false];
            // with no panel to lay it out, the operation's view is given the web view's frame
            let view: *mut AnyObject = msg_send![op, view];
            if !view.is_null() {
                let bounds: Rect = msg_send![wk, bounds];
                let _: () = msg_send![view, setFrame: bounds];
            }
        }
        let _: () = msg_send![op, runOperationModalForWindow: ns_window, delegate: delegate_ptr,
                              didRunSelector: Some(sel!(printOperationDidRun:success:contextInfo:)),
                              contextInfo: std::ptr::null_mut::<std::ffi::c_void>()];
    }

    /// One part of a box of the foot: words, or the page's number or the count of pages.
    enum Part {
        Words(String),
        Page,
        Pages,
    }

    /// The foot a print view asks for on paper, its bottom margin boxes (window.js, idiographPageFoot), which
    /// Chrome and Windows's web view draw and the Mac's web view, WebKit, never does (31 October 2026,
    /// exportpdf2): the left, middle and right boxes, the type's size in points, its colour and face, and the
    /// page's margins in points, top, right, bottom and left.
    pub struct Foot {
        boxes: [Vec<Part>; 3],
        size: f64,
        rgb: (f64, f64, f64),
        family: String,
        margins: [f64; 4],
        /// the left box's part that may be shortened with "…" when the parts would come too close, the project
        fit: Option<usize>,
        /// the last page given its foot
        drawn: isize,
    }

    impl Foot {
        pub fn read(said: &serde_json::Value) -> Option<Foot> {
            let parts = |name: &str| -> Vec<Part> {
                said.get(name).and_then(|v| v.as_array()).map(|all| {
                    all.iter().filter_map(|p| match (p.as_str(), p.get("counter").and_then(|c| c.as_str())) {
                        (Some(words), _) => Some(Part::Words(words.to_string())),
                        (None, Some("page")) => Some(Part::Page),
                        (None, Some("pages")) => Some(Part::Pages),
                        _ => None,
                    }).collect()
                }).unwrap_or_default()
            };
            let boxes = [parts("left"), parts("center"), parts("right")];
            if boxes.iter().all(|b| b.is_empty()) {
                return None;
            }
            let hex = said.get("color").and_then(|c| c.as_str()).unwrap_or("").trim().trim_start_matches('#').to_string();
            let channel = |i: usize| u8::from_str_radix(hex.get(i..i + 2).unwrap_or("66"), 16).unwrap_or(0x66) as f64 / 255.0;
            let rgb = if hex.len() == 6 { (channel(0), channel(2), channel(4)) } else { (0.46, 0.42, 0.36) };
            let mut margins = [0.0f64; 4];
            if let Some(given) = said.get("margins").and_then(|m| m.as_array()) {
                for (i, mm) in given.iter().take(4).enumerate() {
                    margins[i] = mm.as_f64().unwrap_or(0.0) * 72.0 / 25.4;
                }
            }
            Some(Foot {
                boxes,
                size: said.get("size").and_then(|s| s.as_f64()).filter(|s| *s > 0.0).unwrap_or(7.0),
                rgb,
                family: said.get("family").and_then(|f| f.as_str()).unwrap_or("").to_string(),
                margins,
                fit: said.get("fit").and_then(|f| f.as_i64()).filter(|f| *f >= 0).map(|f| f as usize)
                    .filter(|f| *f < boxes_len(said)),
                drawn: 0,
            })
        }

        /// A box's words on page `page` of `pages`, each run of spaces one space, as a margin box's
        /// `white-space: normal` sets them in Chrome, the part `fit` names cut to its first `keep` characters
        /// and "…" when `keep` is given.
        fn words(&self, i: usize, page: isize, pages: isize, keep: Option<usize>) -> String {
            let said: String = self.boxes[i].iter().enumerate().map(|(k, part)| match part {
                Part::Words(words) => match keep {
                    Some(n) if i == 0 && Some(k) == self.fit => cut_at_word(words, n),
                    _ => words.clone(),
                },
                Part::Page => page.to_string(),
                Part::Pages => pages.to_string(),
            }).collect();
            said.split_whitespace().collect::<Vec<_>>().join(" ")
        }

        /// Where the part `fit` names may be cut, the end of each of its words but the last, in characters, 0
        /// first, as the page's own script cuts (themes_print, FOOT_FIT).
        fn word_ends(&self) -> Vec<usize> {
            let mut ends = vec![0];
            if let Some(Part::Words(words)) = self.fit.and_then(|k| self.boxes[0].get(k)) {
                let chars: Vec<char> = words.chars().collect();
                for i in 1..chars.len() {
                    if chars[i].is_whitespace() && !chars[i - 1].is_whitespace() {
                        ends.push(i);
                    }
                }
            }
            ends
        }
    }

    /// `words` cut to its first `n` characters, any space, comma, semicolon, colon or full stop at the cut taken
    /// off, and "…" after it (1 November 2026), as the page's own script cuts.
    pub fn cut_at_word(words: &str, n: usize) -> String {
        let cut: String = words.chars().take(n).collect();
        format!("{}\u{2026}", cut.trim_end_matches(|c: char| c.is_whitespace() || ",;:.".contains(c)))
    }

    /// How many parts the left box of a foot `said` has, so `fit` names one of them.
    fn boxes_len(said: &serde_json::Value) -> usize {
        said.get("left").and_then(|v| v.as_array()).map(|a| a.len()).unwrap_or(0)
    }

    /// Where the foot's three parts go across a line `room` wide, from their widths, the left part's
    /// start at 0 (1 November 2026, Adam): the right one ends at the line's end and the middle one is centred
    /// in the room between the left one's end and the right one's start, so a long left part never runs into
    /// it. The middle's start, and whether the three keep `gap` between each two that show.
    pub fn foot_places(room: f64, left: f64, middle: f64, right: f64, gap: f64) -> (f64, bool) {
        let shown = (middle > 0.0) as u8 as f64 + (right > 0.0) as u8 as f64;
        let x = left + (room - right - left - middle) / 2.0;
        (x, left + middle + right + gap * shown <= room)
    }

    /// Each footed print's foot, by its operation's view, read as each page's border is drawn, which can be on
    /// the print's own thread.
    static FEET: std::sync::Mutex<Vec<(usize, Foot)>> = std::sync::Mutex::new(Vec::new());

    /// The print operation's view made to draw `foot` on each page: its class given a subclass of its own,
    /// once for each class, whose `drawPageBorderWithSize:` draws what WebKit's own does and then the foot,
    /// the way AppKit gives a view to draw on each page round its content. WebKit's print view lays the
    /// pages out and draws them as before, so the pages are the same with the foot as without. False when
    /// there is no view to draw it on.
    unsafe fn footed(view: *mut AnyObject, foot: Foot) -> bool {
        if view.is_null() {
            return false;
        }
        let class: &objc2::runtime::AnyClass = (*view).class();
        let own = class.name().to_str().unwrap_or("").to_string();
        let sub: &objc2::runtime::AnyClass = if own.starts_with("IdiographFooted") {
            class
        } else {
            let Ok(cname) = std::ffi::CString::new(format!("IdiographFooted{own}")) else { return false };
            match objc2::runtime::AnyClass::get(&cname) {
                Some(made) => made,
                None => {
                    let Some(mut builder) = objc2::runtime::ClassBuilder::new(&cname, class) else { return false };
                    builder.add_method(sel!(drawPageBorderWithSize:), draw_border as unsafe extern "C-unwind" fn(_, _, _));
                    builder.register()
                }
            }
        };
        match FEET.lock() {
            Ok(mut feet) => {
                feet.retain(|(v, _)| *v != view as usize);
                feet.push((view as usize, foot));
            }
            Err(_) => return false,
        }
        AnyObject::set_class(&*view, sub);
        true
    }

    /// Each page's border: WebKit's own first, then the page's foot in its bottom margin, the left box at the
    /// left margin, the middle one halfway between the other two and the right one ending at the right margin, each set
    /// in the middle of the margin's height, as Chrome sets a margin box.
    unsafe extern "C-unwind" fn draw_border(this: &AnyObject, _cmd: Sel, border: Size) {
        let class: &objc2::runtime::AnyClass = this.class();
        if let Some(sup) = class.superclass() {
            let _: () = msg_send![super(this, sup), drawPageBorderWithSize: border];
        }
        let op: *mut AnyObject = msg_send![class!(NSPrintOperation), currentOperation];
        if op.is_null() {
            return;
        }
        let page: isize = msg_send![op, currentPage];
        let range: Range = msg_send![op, pageRange];
        let pages = (range.location + range.length).saturating_sub(1) as isize;
        let mut feet = match FEET.lock() {
            Ok(feet) => feet,
            Err(_) => return,
        };
        let Some((_, foot)) = feet.iter_mut().find(|(v, _)| *v == this as *const AnyObject as usize) else { return };
        // WebKit draws a border again on the main thread when the print runs on a thread of its own, so a page
        // already given its foot is not given it twice
        if foot.drawn == page {
            return;
        }
        foot.drawn = page;
        let mut font: *mut AnyObject = std::ptr::null_mut();
        if !foot.family.is_empty() {
            let manager: *mut AnyObject = msg_send![class!(NSFontManager), sharedFontManager];
            font = msg_send![manager, fontWithFamily: text(&foot.family), traits: 0usize, weight: 5isize, size: foot.size];
        }
        if font.is_null() {
            font = msg_send![class!(NSFont), systemFontOfSize: foot.size];
        }
        let colour: *mut AnyObject = msg_send![class!(NSColor), colorWithSRGBRed: foot.rgb.0, green: foot.rgb.1,
                                                blue: foot.rgb.2, alpha: 1.0f64];
        #[link(name = "AppKit", kind = "framework")]
        extern "C" {
            static NSFontAttributeName: *mut AnyObject;
            static NSForegroundColorAttributeName: *mut AnyObject;
        }
        let keys = [NSFontAttributeName, NSForegroundColorAttributeName];
        let values = [font, colour];
        let attrs: *mut AnyObject = msg_send![class!(NSDictionary), dictionaryWithObjects: values.as_ptr(),
                                               forKeys: keys.as_ptr(), count: 2usize];
        // AppKit draws a page's border in the paper's own space, its origin at the foot unless the context
        // says it is flipped, whatever the view is
        let context: *mut AnyObject = msg_send![class!(NSGraphicsContext), currentContext];
        let flipped: bool = !context.is_null() && msg_send![context, isFlipped];
        let [_, right, bottom, left] = foot.margins;
        // each part measured in the foot's type, the left one with the project shortened with "…" until the three
        // keep a clear gap of 6 mm, the middle one centred between the left's end and the right's start (Adam, 1
        // November 2026), as the page's own script lays out Chrome's margin boxes (themes_print, FOOT_FIT)
        let measured = |words: &str| -> (*mut AnyObject, Size) {
            let line: *mut AnyObject = msg_send![class!(NSAttributedString), alloc];
            let line: *mut AnyObject = msg_send![line, initWithString: text(words), attributes: attrs];
            let size: Size = msg_send![line, size];
            (line, size)
        };
        let room = border.width - left - right;
        let gap = 6.0 * 72.0 / 25.4;
        let width_of = |words: &str| -> f64 {
            if words.is_empty() {
                return 0.0;
            }
            let (line, size) = measured(words);
            let _: () = msg_send![line, release];
            size.width
        };
        let middle_words = foot.words(1, page, pages, None);
        let right_words = foot.words(2, page, pages, None);
        let (middle_w, right_w) = (width_of(&middle_words), width_of(&right_words));
        // whether the project is cut is decided against the widest page number the page's own script assumes,
        // "Page 00 of 00", so every page of a print cuts it alike and as Chrome does
        let widest_w = width_of(&foot.words(2, 0, 0, None).replace('0', "00"));
        let mut left_words = foot.words(0, page, pages, None);
        if !foot_places(room, width_of(&left_words), middle_w, widest_w, gap).1 && foot.fit.is_some() {
            // the most words of the project that still fit, found by halving
            let ends = foot.word_ends();
            let (mut lo, mut hi) = (0usize, ends.len() - 1);
            while lo < hi {
                let k = (lo + hi + 1) / 2;
                if foot_places(room, width_of(&foot.words(0, page, pages, Some(ends[k]))), middle_w, widest_w, gap).1 {
                    lo = k;
                } else {
                    hi = k - 1;
                }
            }
            left_words = foot.words(0, page, pages, Some(ends[lo]));
        }
        let left_w = width_of(&left_words);
        let (middle_x, _) = foot_places(room, left_w, middle_w, right_w, gap);
        for (i, words) in [left_words, middle_words, right_words].iter().enumerate() {
            if words.is_empty() {
                continue;
            }
            let (line, size) = measured(words);
            let x = match i {
                0 => left,
                1 => left + middle_x,
                _ => border.width - right - size.width,
            };
            let from_foot = (bottom - size.height) / 2.0;
            let y = if flipped { border.height - from_foot - size.height } else { from_foot };
            let _: () = msg_send![line, drawAtPoint: Point { x, y }];
            let _: () = msg_send![line, release];
            #[cfg(feature = "drive")]
            eprintln!("drive: foot part {i} on page {page} from {x:.1} to {:.1} of {:.1}: {words}", x + size.width, border.width);
        }
        #[cfg(feature = "drive")]
        eprintln!("drive: foot drawn on page {page} of {pages}, flipped {flipped}, border {:.0} x {:.0}", border.width, border.height);
    }

    /// A point as AppKit takes it, NSPoint.
    #[repr(C)]
    #[derive(Clone, Copy, Debug)]
    struct Point {
        x: f64,
        y: f64,
    }

    unsafe impl objc2::Encode for Point {
        const ENCODING: objc2::Encoding = objc2::Encoding::Struct("CGPoint", &[f64::ENCODING, f64::ENCODING]);
    }

    /// A range as Foundation has it, NSRange.
    #[repr(C)]
    #[derive(Clone, Copy, Debug)]
    struct Range {
        location: usize,
        length: usize,
    }

    unsafe impl objc2::Encode for Range {
        const ENCODING: objc2::Encoding = objc2::Encoding::Struct("_NSRange", &[usize::ENCODING, usize::ENCODING]);
    }

    /// The system Edit menu's Undo or Redo, sent to the field with the focus.
    pub fn send(action: &str) {
        let selector = if action == "redo" { sel!(redo:) } else { sel!(undo:) };
        unsafe {
            let ns_app: *mut AnyObject = msg_send![class!(NSApplication), sharedApplication];
            let none: *mut AnyObject = std::ptr::null_mut();
            let _: bool = msg_send![ns_app, sendAction: selector, to: none, from: none];
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn a_new_window_starts_where_the_page_said() {
        let mut given = Map::new();
        given.insert("idiograph-return".into(), json!("{\"screen\":\"pets\",\"path\":\"/x/a.xlsx\"}"));
        given.insert("idiograph-home".into(), json!("demo"));
        given.insert("elsewhere".into(), json!("x"));
        given.insert("idiograph-shut".into(), json!(1));
        let (session, hash) = new_window_place(Some(given), Some("#open=%7B%22screen%22%3A%22pets%22%7D".into()));
        let mut keys: Vec<&String> = session.keys().collect();
        keys.sort();
        assert_eq!(keys, vec!["idiograph-home", "idiograph-return"]);
        assert_eq!(hash.as_deref(), Some("open=%7B%22screen%22%3A%22pets%22%7D"));
        // nothing handed over, or an address of another form, is the home screen
        assert_eq!(new_window_place(None, None), (Map::new(), None));
        assert_eq!(new_window_place(None, Some("#elsewhere".into())).1, None);
        assert_eq!(new_window_place(None, Some("#open=a b".into())).1, None);
    }

    #[test]
    fn a_dialogs_title_ends_in_no_full_stop_off_a_mac() {
        assert_eq!(title_words(" Choose the folder for the copy. ", false), "Choose the folder for the copy");
        assert_eq!(title_words("Choose the folder for the copy.", true), "Choose the folder for the copy.");
        assert_eq!(pick_title("Open a shared copy."), if cfg!(target_os = "macos") { "Open a shared copy." } else { "Open a shared copy" });
        assert_eq!(gtk_paper("A4"), Some("iso_a4"));
        assert_eq!(gtk_paper("letter"), Some("na_letter"));
        assert_eq!(gtk_paper("folio"), None);
    }

    #[test]
    fn a_line_said_is_trimmed_and_kept_short() {
        assert_eq!(speakable("  The frames are back in the hive. \n"), "The frames are back in the hive.");
        assert_eq!(speakable("   "), "");
        let long = "é".repeat(500);
        assert_eq!(speakable(&long).chars().count(), 400);
    }

    #[test]
    fn each_edit_item_has_webkitgtks_own_command() {
        let got: Vec<_> = ["edit-undo", "edit-redo", "edit-cut", "edit-copy", "edit-paste", "edit-select-all", "undo", "redo", "find"]
            .iter()
            .map(|id| webkit_command(id))
            .collect();
        assert_eq!(got, vec![Some("Undo"), Some("Redo"), Some("Cut"), Some("Copy"), Some("Paste"), Some("SelectAll"),
                             Some("Undo"), Some("Redo"), None]);
    }

    #[test]
    fn linux_finds_the_server_in_tauris_resource_folder() {
        let at = linux_server_candidates(Path::new("/usr/bin/Idiograph"), "Idiograph");
        assert_eq!(at, vec![PathBuf::from("/usr/lib/Idiograph/server"), PathBuf::from("/usr/bin/server")]);
        // an AppImage's mount has the same layout under its own prefix
        let mounted = linux_server_candidates(Path::new("/tmp/.mount_Idiogr/usr/bin/Idiograph"), "Idiograph");
        assert_eq!(mounted[0], PathBuf::from("/tmp/.mount_Idiogr/usr/lib/Idiograph/server"));
        // a test build's executable and product share a name that is not the app's
        let test = linux_server_candidates(Path::new("/usr/bin/Idiograph Test"), "Idiograph");
        assert_eq!(test[0], PathBuf::from("/usr/lib/Idiograph Test/server"));
        assert_eq!(test[1], PathBuf::from("/usr/lib/Idiograph/server"));
    }

    #[cfg(target_os = "macos")]
    #[test]
    fn the_foots_middle_sits_between_its_neighbours() {
        // a short left part: the middle centred in the room between the left's end and the right's start
        let (x, apart) = mac::foot_places(750.0, 100.0, 150.0, 50.0, 17.0);
        assert!(apart);
        assert!(((x - 100.0) - (750.0 - 50.0 - (x + 150.0))).abs() < 1e-9);
        // a left part so long the three would come closer than the gap
        assert!(!mac::foot_places(750.0, 520.0, 150.0, 50.0, 17.0).1);
        // with no middle, only the left and the right keep the gap
        assert!(mac::foot_places(750.0, 680.0, 0.0, 50.0, 17.0).1);
        // a project cut at the end of a word, the comma there taken off
        assert_eq!(mac::cut_at_word("a city flat: companionship, routine", 27), "a city flat: companionship\u{2026}");
        assert_eq!(mac::cut_at_word("a city flat: companionship, routine", 0), "\u{2026}");
    }

    #[test]
    fn a_fallback_skips_the_familys_other_ports() {
        let tried: Vec<u16> = tried_ports(8765).take(3).collect();
        assert_eq!(tried, vec![8765, 8768, 8769]);
        assert_eq!(tried_ports(8766).next(), Some(8766));
        assert!(!tried_ports(8766).skip(1).any(|p| FAMILY_PORTS.contains(&p)));
    }

    #[test]
    fn says_a_stop_and_a_failed_start_plainly_and_once() {
        // the page's notice in Adam's words, and the page saying back that it shows it
        let js = ended_js();
        assert!(js.contains("serverGone(\"Idiograph stopped unexpectedly.\", \"What you saved is kept. Close this window and open Idiograph again.\")"));
        assert!(js.contains("tauri.invoke('closing', { step: 'ended' })"));
        assert!(js.find("serverGone(").unwrap() < js.find("tauri.invoke(").unwrap());
        // a failed start in plain words, the log's lines never among them
        let dir = env::temp_dir().join(format!("idiograph-start-{}", std::process::id()));
        let _ = fs::create_dir_all(&dir);
        let log = dir.join("idiograph.log");
        fs::write(&log, "Idiograph is running on http://127.0.0.1:8765\nStop it with Control-C\n").unwrap();
        let said = not_started(&log, "the server did not answer on port 8765.");
        assert_eq!(said, "Idiograph could not start. What you saved is kept. Open Idiograph again.");
        assert!(!said.contains("127.0.0.1") && !said.contains("8765") && !said.contains("Control-C"));
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn fits_a_window_in_its_screen() {
        // a screen of 1366 by 768, its taskbar 40 high at the foot
        let area = (0, 0, 1366, 728);
        // a window of 1280 by 851 opened 196 down and right: smaller, and moved up and left inside
        assert_eq!(fit_in((196, 196), (1280, 851), area), ((86, 0), (1280, 728)));
        // one that fits stays where it is
        assert_eq!(fit_in((40, 30), (900, 600), area), ((40, 30), (900, 600)));
        // one past the left and the top edge comes back inside
        assert_eq!(fit_in((-300, -50), (900, 600), area), ((0, 0), (900, 600)));
        // a second screen to the right, its work area from 1920 on
        assert_eq!(fit_in((3000, 900), (1280, 800), (1920, 0, 1920, 1040)), ((2560, 240), (1280, 800)));
    }

    #[test]
    fn reads_the_last_word_since_the_window_started_the_server() {
        let dir = env::temp_dir().join(format!("idiograph-word-{}", std::process::id()));
        let _ = fs::create_dir_all(&dir);
        let log = dir.join("idiograph.log");
        let word = |text: &str| {
            fs::write(&log, text).unwrap();
            last_word(&log)
        };
        assert_eq!(word("old
Idiograph is closed.

=== 2026-10-17 17:00:13, starting
Idiograph is running
"), Word::Nothing);
        assert_eq!(word("
=== now
Idiograph is running
Restarting.
"), Word::Restart);
        assert_eq!(word("
=== now
Restarting.
Idiograph is running
Idiograph is closed.
"), Word::Closed);
        assert_eq!(word("
=== now
Restarting.
Idiograph is closed.
Restarting.
"), Word::Restart);
        assert_eq!(word("
=== now
No Idiograph tab has been open for a few minutes, so it quit by itself.
"), Word::Closed);
        let _ = fs::remove_dir_all(&dir);
    }
}

/// For a check of the window on a Mac alone (`packaging/tauri/drive_mac.py`), built only with the
/// `drive` feature and never shipped: IDIOGRAPH_WINDOW_DRIVE names a script run in every window
/// once its page has loaded, each window's number is said for a screenshot, and a sheet, the print
/// panel, a save panel or a message, is said as it opens and ended by itself four seconds later,
/// a message by its one button and a panel cancelled. IDIOGRAPH_WINDOW_SAVE_TO is the folder a
/// download is then written to, one that is missing to try a write that fails. The Edit menu is
/// said once with its keys. IDIOGRAPH_WINDOW_CLOSE names a file whose lines are windows to close,
/// and with IDIOGRAPH_WINDOW_NO_OPEN an outside link is only said, never opened in this Mac's browser.
#[cfg(feature = "drive")]
mod drive {
    use super::*;
    use tauri::webview::PageLoadEvent;

    pub fn loaded<'a>(builder: WebviewWindowBuilder<'a, tauri::Wry, AppHandle>) -> WebviewWindowBuilder<'a, tauri::Wry, AppHandle> {
        let Some(js) = env::var("IDIOGRAPH_WINDOW_DRIVE").ok().and_then(|p| fs::read_to_string(p).ok()) else {
            return builder;
        };
        builder.on_page_load(move |window, payload| {
            if payload.event() == PageLoadEvent::Finished {
                let _ = window.eval(format!("window.__driveLabel = {:?};\n{js}", window.label()));
            }
        })
    }

    /// Where a check's save goes: IDIOGRAPH_WINDOW_SAVE_TO and the proposed name, however the panel
    /// was answered, since the check never presses the panel's own Save (17 October: pressing it
    /// from code raised an exception Rust cannot pass, and the test app aborted).
    pub fn save_to(chosen: Option<PathBuf>, name: &str) -> Option<PathBuf> {
        match env::var("IDIOGRAPH_WINDOW_SAVE_TO") {
            Ok(dir) if !dir.is_empty() => Some(PathBuf::from(dir).join(name)),
            _ => chosen,
        }
    }

    /// Where a check's print goes, IDIOGRAPH_WINDOW_PRINT_TO, a folder: the window's print written there
    /// as a PDF with no panel, `<label>-<n>.pdf`, n counting the prints of the run, said as it is asked.
    pub fn print_to(label: &str) -> Option<PathBuf> {
        static PRINTS: AtomicUsize = AtomicUsize::new(0);
        let dir = env::var("IDIOGRAPH_WINDOW_PRINT_TO").ok().filter(|d| !d.is_empty())?;
        let n = PRINTS.fetch_add(1, Ordering::SeqCst) + 1;
        let path = PathBuf::from(dir).join(format!("{label}-{n}.pdf"));
        eprintln!("drive: print to {}", path.display());
        Some(path)
    }

    /// What a check's Choose answers, IDIOGRAPH_WINDOW_PICK, however the dialog was answered, which
    /// the check cancels as it cancels every panel.
    pub fn picked(chosen: Option<PathBuf>) -> Option<PathBuf> {
        eprintln!("drive: picked");
        match env::var("IDIOGRAPH_WINDOW_PICK") {
            Ok(path) if !path.is_empty() => Some(PathBuf::from(path)),
            _ => chosen,
        }
    }

    /// A check's answer to Close Anyway, IDIOGRAPH_WINDOW_UNSAVED, `close` or `keep`, however the
    /// message was answered.
    pub fn unsaved(answer: rfd::MessageDialogResult) -> rfd::MessageDialogResult {
        eprintln!("drive: unsaved asked");
        match env::var("IDIOGRAPH_WINDOW_UNSAVED").as_deref() {
            Ok("close") => rfd::MessageDialogResult::Ok,
            Ok("keep") => rfd::MessageDialogResult::Cancel,
            _ => answer,
        }
    }

    /// A check's answer to a confirm the page asked for (removefix), IDIOGRAPH_WINDOW_CONFIRM, `ok` or `cancel`,
    /// however the sheet was answered, said with the answer.
    pub fn confirmed(answer: rfd::MessageDialogResult) -> rfd::MessageDialogResult {
        let answer = match env::var("IDIOGRAPH_WINDOW_CONFIRM").as_deref() {
            Ok("ok") => rfd::MessageDialogResult::Ok,
            Ok("cancel") => rfd::MessageDialogResult::Cancel,
            _ => answer,
        };
        eprintln!("drive: confirm asked, {answer:?}");
        answer
    }

    /// One order of a check's, a line of the file IDIOGRAPH_WINDOW_ORDERS names: `menus` says every
    /// menu with its items, keys and actions, `item <id>` does what that menu item does, `popup
    /// <Title>` opens that menu of the menu bar over the main window for three seconds, `about` presses
    /// About Idiograph and says its title, `about-close` closes the page's card with Done, `frame <x>
    /// <y> <w> <h>` moves and sizes the main window, `where` says where it is, `front <label>` names the
    /// window the menu's items take as the one in front, `snap <prefix>` draws every window of the app's
    /// own to a picture, `snappage <label> <path>` a window's page, and `spellstate <label>` whether its
    /// web view checks spelling as it is typed.
    /// The window a check says stands in front, by `front <label>`, for the menu's items.
    pub static FRONT: Mutex<Option<String>> = Mutex::new(None);

    #[cfg(target_os = "macos")]
    pub fn order(app: &AppHandle, line: &str) {
        let mut words = line.split_whitespace();
        let head = words.next().unwrap_or("");
        let rest: Vec<&str> = words.collect();
        eprintln!("drive: order {line}");
        match head {
            "menus" => {
                let _ = app.run_on_main_thread(|| unsafe { menus() });
            }
            "item" => menu_event(app, rest.first().copied().unwrap_or("")),
            "front" => *FRONT.lock().unwrap() = rest.first().map(|l| l.to_string()),
            "popup" => {
                let title = rest.join(" ");
                let at = app.get_webview_window(MAIN).and_then(|w| w.ns_window().ok()).map(|ns| ns as usize);
                let _ = app.run_on_main_thread(move || unsafe { popup(&title, at) });
            }
            "about" => {
                let _ = app.run_on_main_thread(|| unsafe { about() });
            }
            // the card read and closed on the page, as Done closes it
            "about-close" => {
                if let Some(window) = app.get_webview_window(MAIN) {
                    let _ = window.eval("var d = document.getElementById('about-done'); if (d) d.click();");
                    eprintln!("drive: about closed page");
                }
            }
            "snap" => {
                let prefix = rest.join(" ");
                let _ = app.run_on_main_thread(move || unsafe { snap_windows(&prefix) });
            }
            "spellstate" => {
                if let Some(window) = app.get_webview_window(rest.first().copied().unwrap_or(MAIN)) {
                    let _ = window.with_webview(|webview| unsafe {
                        let (on, chosen) = mac::spelling_state(webview.inner() as *mut objc2::runtime::AnyObject);
                        eprintln!("drive: spellstate on {on} chosen {chosen}");
                    });
                }
            }
            "snappage" => {
                if let (Some(label), Some(path)) = (rest.first(), rest.get(1..).map(|r| r.join(" "))) {
                    if let Some(window) = app.get_webview_window(label) {
                        snap_page(&window, path);
                    }
                }
            }
            "frame" => {
                let n: Vec<f64> = rest.iter().filter_map(|w| w.parse().ok()).collect();
                if let (Some(window), [x, y, w, h]) = (app.get_webview_window(MAIN), n.as_slice()) {
                    let _ = window.set_position(tauri::LogicalPosition::new(*x, *y));
                    let _ = window.set_size(tauri::LogicalSize::new(*w, *h));
                }
            }
            "where" => {
                if let Some(window) = app.get_webview_window(MAIN) {
                    let scale = window.scale_factor().unwrap_or(1.0);
                    let at = window.outer_position().map(|p| p.to_logical::<f64>(scale)).ok();
                    let size = window.inner_size().map(|s| s.to_logical::<f64>(scale)).ok();
                    eprintln!("drive: where {:?} {:?}", at.map(|p| (p.x, p.y)), size.map(|s| (s.width, s.height)));
                }
            }
            _ => {}
        }
    }

    #[cfg(target_os = "macos")]
    #[repr(C)]
    #[derive(Clone, Copy, Debug)]
    struct Point {
        x: f64,
        y: f64,
    }

    #[cfg(target_os = "macos")]
    #[repr(C)]
    #[derive(Clone, Copy, Debug)]
    struct Rect {
        origin: Point,
        size: Point,
    }

    #[cfg(target_os = "macos")]
    unsafe impl objc2::encode::Encode for Point {
        const ENCODING: objc2::encode::Encoding =
            objc2::encode::Encoding::Struct("CGPoint", &[f64::ENCODING, f64::ENCODING]);
    }

    #[cfg(target_os = "macos")]
    unsafe impl objc2::encode::Encode for Rect {
        const ENCODING: objc2::encode::Encoding = objc2::encode::Encoding::Struct(
            "CGRect",
            &[Point::ENCODING, objc2::encode::Encoding::Struct("CGSize", &[f64::ENCODING, f64::ENCODING])],
        );
    }

    #[cfg(target_os = "macos")]
    unsafe fn ns_text(s: &str) -> *mut objc2::runtime::AnyObject {
        let c = std::ffi::CString::new(s).unwrap_or_default();
        objc2::msg_send![objc2::class!(NSString), stringWithUTF8String: c.as_ptr()]
    }

    #[cfg(target_os = "macos")]
    unsafe fn rust_text(o: *mut objc2::runtime::AnyObject) -> String {
        if o.is_null() {
            return String::new();
        }
        let c: *const std::os::raw::c_char = objc2::msg_send![o, UTF8String];
        if c.is_null() { String::new() } else { std::ffi::CStr::from_ptr(c).to_string_lossy().into_owned() }
    }

    /// Every menu of the menu bar, each item a line: its menu, title, key, modifier mask, action,
    /// whether it is on, and whether it is ticked.
    #[cfg(target_os = "macos")]
    unsafe fn menus() {
        use objc2::runtime::{AnyObject, Sel};
        use objc2::{class, msg_send};
        unsafe fn walk(menu: *mut AnyObject, path: &str) {
            let n: isize = msg_send![menu, numberOfItems];
            for i in 0..n {
                let item: *mut AnyObject = msg_send![menu, itemAtIndex: i];
                let sep: bool = msg_send![item, isSeparatorItem];
                if sep {
                    eprintln!("drive: menu {path} | ---");
                    continue;
                }
                let title = rust_text(msg_send![item, title]);
                let mask: usize = msg_send![item, keyEquivalentModifierMask];
                let action: Option<Sel> = msg_send![item, action];
                let enabled: bool = msg_send![item, isEnabled];
                let state: isize = msg_send![item, state];
                eprintln!("drive: menu {path} | {title} | {} | {mask:#x} | {} | {enabled} | {state}",
                          rust_text(msg_send![item, keyEquivalent]), action.map(|s| s.name().to_string_lossy().into_owned()).unwrap_or_default());
                let sub: *mut AnyObject = msg_send![item, submenu];
                if !sub.is_null() {
                    let _: () = msg_send![sub, update];
                    walk(sub, &format!("{path}/{title}"));
                }
            }
        }
        let ns_app: *mut AnyObject = msg_send![class!(NSApplication), sharedApplication];
        let main: *mut AnyObject = msg_send![ns_app, mainMenu];
        if !main.is_null() {
            walk(main, "");
        }
        eprintln!("drive: menus done");
    }

    /// The menu bar's menu `title` opened over the main window's top left corner, and closed three
    /// seconds later from the run loop, its tracking's own mode among the common ones.
    #[cfg(target_os = "macos")]
    unsafe fn popup(title: &str, window: Option<usize>) {
        use objc2::runtime::AnyObject;
        use objc2::{class, msg_send, sel};
        let ns_app: *mut AnyObject = msg_send![class!(NSApplication), sharedApplication];
        let main: *mut AnyObject = msg_send![ns_app, mainMenu];
        // a menu of the bar by its title, or one inside it, File>Open Recent
        let mut names = title.split('>');
        let first = names.next().unwrap_or("");
        let mut top: *mut AnyObject = if first == "Idiograph" { msg_send![main, itemAtIndex: 0isize] } else { msg_send![main, itemWithTitle: ns_text(first)] };
        for name in names {
            if top.is_null() {
                break;
            }
            let menu: *mut AnyObject = msg_send![top, submenu];
            top = if menu.is_null() { std::ptr::null_mut() } else { msg_send![menu, itemWithTitle: ns_text(name)] };
        }
        if top.is_null() {
            eprintln!("drive: popup none {title}");
            return;
        }
        let sub: *mut AnyObject = msg_send![top, submenu];
        let _: () = msg_send![sub, update];
        let at = match window {
            Some(ns) => {
                let frame: Rect = msg_send![ns as *mut AnyObject, frame];
                Point { x: frame.origin.x + 24.0, y: frame.origin.y + frame.size.y - 40.0 }
            }
            None => Point { x: 200.0, y: 600.0 },
        };
        let modes: *mut AnyObject = msg_send![class!(NSArray), arrayWithObject: ns_text("kCFRunLoopCommonModes")];
        let none: *mut AnyObject = std::ptr::null_mut();
        let _: () = msg_send![sub, performSelector: sel!(cancelTracking), withObject: none, afterDelay: 3.0f64, inModes: modes];
        eprintln!("drive: popup open {title}");
        let _: bool = msg_send![sub, popUpMenuPositioningItem: none, atLocation: at, inView: none];
        eprintln!("drive: popup closed {title}");
    }

    /// A picture of every visible window of the app's own drawn by AppKit itself, the About panel and
    /// a menu standing open among them, each written to `<prefix>-<number>.png`, since this Mac takes
    /// no screen capture of a check's windows (17 October, both builds).
    #[cfg(target_os = "macos")]
    unsafe fn snap_windows(prefix: &str) {
        use objc2::runtime::AnyObject;
        use objc2::{class, msg_send};
        let ns_app: *mut AnyObject = msg_send![class!(NSApplication), sharedApplication];
        let windows: *mut AnyObject = msg_send![ns_app, windows];
        let n: usize = msg_send![windows, count];
        for i in 0..n {
            let w: *mut AnyObject = msg_send![windows, objectAtIndex: i];
            let visible: bool = msg_send![w, isVisible];
            if !visible {
                continue;
            }
            let number: isize = msg_send![w, windowNumber];
            let level: isize = msg_send![w, level];
            let kind = (*w).class().name().to_string_lossy().into_owned();
            let content: *mut AnyObject = msg_send![w, contentView];
            if content.is_null() {
                continue;
            }
            let frame_view: *mut AnyObject = msg_send![content, superview];
            let view = if frame_view.is_null() { content } else { frame_view };
            let bounds: Rect = msg_send![view, bounds];
            let rep: *mut AnyObject = msg_send![view, bitmapImageRepForCachingDisplayInRect: bounds];
            if rep.is_null() {
                eprintln!("drive: snap {number} {kind} {level} none");
                continue;
            }
            let _: () = msg_send![view, cacheDisplayInRect: bounds, toBitmapImageRep: rep];
            let path = format!("{prefix}-{number}.png");
            let ok = write_png(rep, &path);
            eprintln!("drive: snap {number} {kind} {level} {ok} {path}");
        }
        eprintln!("drive: snap done {prefix}");
    }

    #[cfg(target_os = "macos")]
    unsafe fn write_png(rep: *mut objc2::runtime::AnyObject, path: &str) -> bool {
        use objc2::runtime::AnyObject;
        use objc2::{class, msg_send};
        let props: *mut AnyObject = msg_send![class!(NSDictionary), dictionary];
        // NSBitmapImageFileTypePNG
        let png: *mut AnyObject = msg_send![rep, representationUsingType: 4usize, properties: props];
        if png.is_null() {
            return false;
        }
        msg_send![png, writeToFile: ns_text(path), atomically: true]
    }

    /// A picture of a window's page as its web view draws it, written to `path`.
    #[cfg(target_os = "macos")]
    pub fn snap_page(window: &tauri::WebviewWindow, path: String) {
        let _ = window.with_webview(move |webview| unsafe {
            use objc2::runtime::AnyObject;
            use objc2::{class, msg_send};
            let wk = webview.inner() as *mut AnyObject;
            let path = path.clone();
            let done = block2::RcBlock::new(move |image: *mut AnyObject, _error: *mut AnyObject| {
                if image.is_null() {
                    eprintln!("drive: snappage none {path}");
                    return;
                }
                let tiff: *mut AnyObject = msg_send![image, TIFFRepresentation];
                let rep: *mut AnyObject = msg_send![class!(NSBitmapImageRep), imageRepWithData: tiff];
                let ok = !rep.is_null() && write_png(rep, &path);
                eprintln!("drive: snappage {ok} {path}");
            });
            let none: *mut AnyObject = std::ptr::null_mut();
            let _: () = msg_send![wk, takeSnapshotWithConfiguration: none, completionHandler: &*done];
        });
    }

    /// About Idiograph from the menu bar, the first item of its first menu pressed as a click presses
    /// it, and its title said. Since 20 October it opens the page's own card, not the system's panel,
    /// so a check reads the card from the page (see `about-close`).
    #[cfg(target_os = "macos")]
    unsafe fn about() {
        use objc2::runtime::AnyObject;
        use objc2::{class, msg_send};
        let ns_app: *mut AnyObject = msg_send![class!(NSApplication), sharedApplication];
        let main: *mut AnyObject = msg_send![ns_app, mainMenu];
        let top: *mut AnyObject = msg_send![main, itemAtIndex: 0isize];
        let sub: *mut AnyObject = msg_send![top, submenu];
        let first: *mut AnyObject = msg_send![sub, itemAtIndex: 0isize];
        let title = rust_text(msg_send![first, title]);
        let _: () = msg_send![sub, performActionForItemAtIndex: 0isize];
        eprintln!("drive: about item {title}");
    }

    /// The Mac's Edit menu as AppKit holds it, each item with its key and its action, said once,
    /// so a check sees that Cmd+C, Cmd+V, Cmd+X, Cmd+A, Cmd+Z and Cmd+Shift+Z reach the page.
    #[cfg(target_os = "macos")]
    pub fn edit_menu(app: &AppHandle) {
        let _ = app.run_on_main_thread(|| unsafe {
            use objc2::runtime::{AnyObject, Sel};
            use objc2::{class, msg_send};
            unsafe fn text(o: *mut AnyObject) -> String {
                if o.is_null() {
                    return String::new();
                }
                let c: *const std::os::raw::c_char = msg_send![o, UTF8String];
                if c.is_null() { String::new() } else { std::ffi::CStr::from_ptr(c).to_string_lossy().into_owned() }
            }
            let ns_app: *mut AnyObject = msg_send![class!(NSApplication), sharedApplication];
            let main: *mut AnyObject = msg_send![ns_app, mainMenu];
            if main.is_null() {
                eprintln!("drive: edit menu none");
                return;
            }
            let n: isize = msg_send![main, numberOfItems];
            for i in 0..n {
                let top: *mut AnyObject = msg_send![main, itemAtIndex: i];
                if text(msg_send![top, title]) != "Edit" {
                    continue;
                }
                let sub: *mut AnyObject = msg_send![top, submenu];
                let m: isize = if sub.is_null() { 0 } else { msg_send![sub, numberOfItems] };
                for j in 0..m {
                    let item: *mut AnyObject = msg_send![sub, itemAtIndex: j];
                    let mask: usize = msg_send![item, keyEquivalentModifierMask];
                    let action: Option<Sel> = msg_send![item, action];
                    eprintln!("drive: edit item {} | {} | {:#x} | {}", text(msg_send![item, title]),
                              text(msg_send![item, keyEquivalent]), mask, action.map(|s| s.name().to_string_lossy().into_owned()).unwrap_or_default());
                }
            }
        });
    }

    #[cfg(not(target_os = "macos"))]
    pub fn edit_menu(_app: &AppHandle) {}

    /// A check's window never takes the keyboard or covers anything of whoever is at the machine: on
    /// every Space, so it is drawn wherever they work, below every other window, and never focused
    /// (17 October, Adam at the Mac while the check ran).
    pub fn placed<'a>(builder: WebviewWindowBuilder<'a, tauri::Wry, AppHandle>) -> WebviewWindowBuilder<'a, tauri::Wry, AppHandle> {
        builder.focused(false).visible_on_all_workspaces(true).always_on_bottom(true)
    }

    /// The window's number said for `screencapture`, and its web view told to go on drawing and
    /// running its timers while other windows cover it, as WebKit otherwise stops a covered page.
    #[cfg(target_os = "macos")]
    pub fn opened(window: &tauri::WebviewWindow) {
        let label = window.label().to_string();
        let Ok(ns) = window.ns_window() else { return };
        let ns = ns as usize;
        let _ = window.run_on_main_thread(move || unsafe {
            use objc2::msg_send;
            use objc2::runtime::AnyObject;
            let w = ns as *mut AnyObject;
            let number: isize = msg_send![w, windowNumber];
            // on every Space, a full-screen one among them, where only that app's own windows and
            // its helpers show, so the window is drawn below whatever is in front
            let behaviour: usize = msg_send![w, collectionBehavior];
            let _: () = msg_send![w, setCollectionBehavior: behaviour | 1 | 256];
            eprintln!("drive: window {label} {number}");
        });
        let _ = window.with_webview(|webview| unsafe {
            use objc2::runtime::{AnyObject, Sel};
            use objc2::{msg_send, sel};
            let wk = webview.inner() as *mut AnyObject;
            let config: *mut AnyObject = msg_send![wk, configuration];
            let prefs: *mut AnyObject = if config.is_null() { std::ptr::null_mut() } else { msg_send![config, preferences] };
            let mut done = Vec::new();
            let mut off = |target: *mut AnyObject, name: &str, selector: Sel| {
                if target.is_null() {
                    return;
                }
                let can: bool = msg_send![target, respondsToSelector: selector];
                if can && objc2::exception::catch(std::panic::AssertUnwindSafe(|| {
                    let _: () = msg_send![target, performSelector: selector, withObject: std::ptr::null_mut::<AnyObject>()];
                })).is_ok() {
                    done.push(name.to_string());
                }
            };
            // each takes a BOOL, and a nil object passed for it is NO
            off(wk, "occlusion", sel!(_setWindowOcclusionDetectionEnabled:));
            off(prefs, "timer throttling", sel!(_setHiddenPageDOMTimerThrottlingEnabled:));
            off(prefs, "throttling increases", sel!(_setHiddenPageDOMTimerThrottlingAutoIncreases:));
            off(prefs, "process suppression", sel!(_setPageVisibilityBasedProcessSuppressionEnabled:));
            // its page's process held in the foreground (removeproof, 10 November 2026): a window `open -g` started
            // is never on view, so its page is hidden, and once a sheet came WebKit suspended the page, which
            // stopped every step of the check's until the window was resized (see `sheets`, which wakes it)
            let can: bool = msg_send![wk, respondsToSelector: sel!(_setThrottleStateForTesting:)];
            if can && objc2::exception::catch(std::panic::AssertUnwindSafe(|| {
                let _: () = msg_send![wk, _setThrottleStateForTesting: 2i32];
            })).is_ok() {
                done.push("foreground".to_string());
            }
            eprintln!("drive: kept awake {}", done.join(", "));
        });
    }

    /// No App Nap for a check's run, which `open -g` starts in the background.
    #[cfg(target_os = "macos")]
    pub fn awake() {
        unsafe {
            use objc2::runtime::AnyObject;
            use objc2::{class, msg_send};
            let info: *mut AnyObject = msg_send![class!(NSProcessInfo), processInfo];
            let reason: *mut AnyObject = msg_send![class!(NSString), stringWithUTF8String: c"a check of the window".as_ptr()];
            // NSActivityUserInitiated, held for the life of the run
            let token: *mut AnyObject = msg_send![info, beginActivityWithOptions: 0x00FF_FFFFu64, reason: reason];
            let _: *mut AnyObject = msg_send![token, retain];
        }
    }

    #[cfg(not(target_os = "macos"))]
    pub fn awake() {}

    #[cfg(not(target_os = "macos"))]
    pub fn opened(_window: &tauri::WebviewWindow) {}

    /// Every half second, each window's sheet: said once as it opens, with its window's number
    /// and its kind, then answered four seconds later.
    #[cfg(target_os = "macos")]
    pub fn sheets(app: &AppHandle) {
        let app = app.clone();
        std::thread::spawn(move || {
            let seen: Arc<Mutex<std::collections::HashMap<isize, Instant>>> = Arc::default();
            let asleep: Arc<Mutex<std::collections::HashMap<String, bool>>> = Arc::default();
            loop {
                sleep(Duration::from_millis(500));
                for window in app.webview_windows().into_values() {
                    // whether WebKit has suspended the window's page, said when it changes, and a suspended page
                    // woken by its window made a point wider and back (removeproof, 10 November 2026: holding it
                    // in the foreground again did not wake it, a resize did)
                    let (asleep, label, held) = (asleep.clone(), window.label().to_string(), window.clone());
                    let _ = window.with_webview(move |webview| unsafe {
                        use objc2::runtime::AnyObject;
                        use objc2::{msg_send, sel};
                        let wk = webview.inner() as *mut AnyObject;
                        let can: bool = msg_send![wk, respondsToSelector: sel!(_isSuspended)];
                        if !can {
                            return;
                        }
                        let now: bool = msg_send![wk, _isSuspended];
                        let mut asleep = asleep.lock().unwrap();
                        if asleep.insert(label.clone(), now) != Some(now) {
                            eprintln!("drive: page {label} suspended {now}");
                        }
                        if !now {
                            return;
                        }
                        let scale = held.scale_factor().unwrap_or(1.0);
                        if let Ok(size) = held.inner_size().map(|s| s.to_logical::<f64>(scale)) {
                            let _ = held.set_size(tauri::LogicalSize::new(size.width + 1.0, size.height));
                            let _ = held.set_size(tauri::LogicalSize::new(size.width, size.height));
                            eprintln!("drive: page {label} woken by a point's resize");
                        }
                    });
                }
                for window in app.webview_windows().into_values() {
                    let Ok(ns) = window.ns_window() else { continue };
                    let (ns, seen, label) = (ns as usize, seen.clone(), window.label().to_string());
                    let _ = window.run_on_main_thread(move || unsafe {
                        use objc2::runtime::AnyObject;
                        use objc2::{class, msg_send};
                        let sheet: *mut AnyObject = msg_send![ns as *mut AnyObject, attachedSheet];
                        if sheet.is_null() {
                            return;
                        }
                        let number: isize = msg_send![sheet, windowNumber];
                        let save: bool = msg_send![sheet, isKindOfClass: class!(NSSavePanel)];
                        let kind = (*sheet).class().name().to_string_lossy().into_owned();
                        let mut seen = seen.lock().unwrap();
                        let first = *seen.entry(number).or_insert_with(|| {
                            eprintln!("drive: sheet {label} {number} {kind}");
                            Instant::now()
                        });
                        if first.elapsed() < Duration::from_secs(4) {
                            return;
                        }
                        seen.remove(&number);
                        let none: *mut AnyObject = std::ptr::null_mut();
                        // every sheet ended from outside it, never by a message to the panel
                        // itself: a save panel cancelled (save_to then writes the file), a
                        // message by its one button, and the print panel cancelled, so nothing
                        // is printed
                        let alert = !save && kind.contains("Alert");
                        let ns_app: *mut AnyObject = msg_send![class!(NSApplication), sharedApplication];
                        let code: isize = if alert { 1000 } else { 0 };
                        let (app_, sheet_) = (ns_app as usize, sheet as usize);
                        let ended = objc2::exception::catch(std::panic::AssertUnwindSafe(move || {
                            let (ns_app, sheet) = (app_ as *mut AnyObject, sheet_ as *mut AnyObject);
                            let _: () = msg_send![ns_app, endSheet: sheet, returnCode: code];
                            let _: () = msg_send![sheet, orderOut: none];
                        }));
                        eprintln!("drive: answered {label} {number} {}{}", if alert { "ok" } else { "cancel" },
                                  if ended.is_ok() { "" } else { ", AppKit raised an exception" });
                    });
                }
                // a check's orders, a line each (see `order`)
                if let Ok(path) = env::var("IDIOGRAPH_WINDOW_ORDERS") {
                    if let Ok(text) = fs::read_to_string(&path) {
                        let _ = fs::remove_file(&path);
                        for line in text.lines().map(str::trim).filter(|l| !l.is_empty()) {
                            order(&app, line);
                        }
                    }
                }
                // the windows IDIOGRAPH_WINDOW_CLOSE names, a label a line, closed as their close
                // button closes them
                if let Ok(path) = env::var("IDIOGRAPH_WINDOW_CLOSE") {
                    if let Ok(text) = fs::read_to_string(&path) {
                        let _ = fs::remove_file(&path);
                        for label in text.lines().map(str::trim).filter(|l| !l.is_empty()) {
                            if let Some(window) = app.get_webview_window(label) {
                                eprintln!("drive: closing {label}");
                                let _ = window.close();
                            }
                        }
                    }
                }
            }
        });
    }

    #[cfg(not(target_os = "macos"))]
    pub fn sheets(_app: &AppHandle) {}
}
