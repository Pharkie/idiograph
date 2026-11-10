//! Idiograph's updates, through Tauri's own updater plugin (18 October 2026, the fourth Tauri build).
//!
//! The plugin reads `latest.json` from the app's own repository's releases, Pharkie/idiograph, which
//! `packaging/release.py` writes and signs, and checks every file it downloads against the public key
//! in `tauri.conf.json`, the version the file was signed for among it (`requireSignedVersion`), so a
//! manifest cannot pair a newer number with an older file. The key there is Adam's own since 18 October,
//! the fifth build, where a placeholder had refused every download. There is no other way an update
//! arrives (Adam, 17 October).
//!
//! This is the window's side. What he chose is kept in `window.json` (keep.rs, `updates`): `check`,
//! true or false once the page has asked, missing until then, `download`, the last check's time
//! `checked`, `ran`, the version that last ran, and `seen`, the version whose line was shown. With
//! checking on, the window checks a few seconds after each start and once a day while it runs, and
//! Check now checks whatever the ticks say. A newer version found is downloaded by itself when he has
//! chosen that, and otherwise when he presses Download. Once downloaded and checked it is ready:
//! Relaunch now installs it and starts the new version, and otherwise it installs as the app quits,
//! after Later or with nothing pressed. Its words are Adam's (18 October): the signature's failure saying
//! the update could not be confirmed as genuine (the fifth build), and Relaunch, the normal word, as the
//! fourth build had it, where the fifth said Restart (the sixth build).
//!
//! The page asks through the command `update` and hears every change (`push`, then window.js's event
//! `idiograph-update`): `here`, `running`, the window's own version, `check`, `download`, `state`
//! (idle, checking, none, available, downloading, ready or failed), the update's `version` and
//! `notes` and `date`, the manifest's `pub_date`, `got` and `size` while it downloads, `checked`, `reason`, a
//! failure in plain words, `later`, and `updated`, the version this run is the first of, with `before`, the
//! version that ran before it, both until its line has been shown. The page shows What's new for every version
//! after `before` up to `updated` (wnspan, 29 October 2026), and the update's own `notes` before it is installed.

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Mutex;
use std::thread::sleep;
use std::time::{Duration, Instant};

use serde_json::{json, Map, Value};
use tauri::{AppHandle, Manager};
use tauri_plugin_updater::{Error, Update, UpdaterExt};

use crate::words::t_app;
use crate::KEPT;

/// How long after a start the first check waits, so the window opens first, and how often the
/// window looks whether a day has passed since its last check.
const FIRST_WAIT: Duration = Duration::from_secs(4);
const LOOK_EVERY: Duration = Duration::from_secs(30 * 60);
const DAY: Duration = Duration::from_secs(24 * 60 * 60);
/// How long a check may take to hear from GitHub. A download has no limit, as a slow line needs time.
const CHECK_WAIT: Duration = Duration::from_secs(30);
/// How often the page hears how far a download has gone.
const TELL_EVERY: Duration = Duration::from_millis(400);

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum State {
    Idle,
    Checking,
    Nothing,
    Available,
    Downloading,
    Ready,
    Failed,
}

impl State {
    pub fn word(self) -> &'static str {
        match self {
            State::Idle => "idle",
            State::Checking => "checking",
            State::Nothing => "none",
            State::Available => "available",
            State::Downloading => "downloading",
            State::Ready => "ready",
            State::Failed => "failed",
        }
    }
}

/// Where the updates stand in this run.
struct Now {
    state: State,
    version: String,
    notes: String,
    got: u64,
    size: u64,
    reason: String,
    later: bool,
    updated: String,
    before: String,
    date: String,
}

static NOW: Mutex<Now> = Mutex::new(Now {
    state: State::Idle,
    version: String::new(),
    notes: String::new(),
    got: 0,
    size: 0,
    reason: String::new(),
    later: false,
    updated: String::new(),
    before: String::new(),
    date: String::new(),
});
/// The update a check found, and its file once downloaded and checked. Taken in this order after
/// NOW, never the other way, so no two locks are ever waited for in turn.
static FOUND: Mutex<Option<Update>> = Mutex::new(None);
static BYTES: Mutex<Option<Vec<u8>>> = Mutex::new(None);
/// A check or a download under way, so a second waits for the next press.
static BUSY: AtomicBool = AtomicBool::new(false);
/// When this run last checked, for the check once a day.
static LAST: Mutex<Option<Instant>> = Mutex::new(None);

/// A version's numbers, so 0.9.10 is newer than 0.9.9, as text would not have it.
pub fn numbers(version: &str) -> Vec<u64> {
    version.trim().split(['.', '-', '+']).take(3).map(|n| n.parse().unwrap_or(0)).collect()
}

/// Whether `a` is newer than `b`. An empty `b`, a version that kept nothing yet, is never older.
pub fn newer(a: &str, b: &str) -> bool {
    !b.trim().is_empty() && numbers(a) > numbers(b)
}

/// What he chose: whether to check, None until the page has asked, and whether to download by itself.
pub fn choice() -> (Option<bool>, bool) {
    let kept = KEPT.get().map(|k| k.updates()).unwrap_or_default();
    (kept.get("check").and_then(Value::as_bool), kept.get("download").and_then(Value::as_bool).unwrap_or(false))
}

fn keep(key: &str, value: Value) {
    if let Some(kept) = KEPT.get() {
        kept.set_update(key, value);
    }
}

/// The time now where the machine is, as the page reads it.
fn now_text() -> String {
    chrono::Local::now().format("%Y-%m-%dT%H:%M:%S%:z").to_string()
}

/// A failure in plain words, as the page shows it under Updates in Settings: GitHub not reached, its
/// answer unreadable, a file whose signature does not hold, or a download that failed.
pub fn said(err: &Error, fetching: bool) -> String {
    match err {
        Error::Minisign(_) | Error::Base64(_) | Error::SignatureUtf8(_) | Error::SignedVersionMismatch { .. }
        | Error::MissingSignedVersion => t_app("menus.update_signature"),
        Error::ReleaseNotFound | Error::Serialization(_) | Error::TargetNotFound(_) | Error::TargetsNotFound(_)
        | Error::Semver(_) => t_app("menus.update_not_read"),
        _ if fetching => t_app("menus.update_not_fetched"),
        _ => t_app("menus.update_not_reached"),
    }
}

/// What the page is told.
pub fn view(app: &AppHandle) -> Value {
    let (check, download) = choice();
    let checked = KEPT.get().and_then(|k| k.updates().get("checked").and_then(Value::as_str).map(str::to_string));
    let now = NOW.lock().unwrap();
    json!({
        "here": true,
        "running": app.package_info().version.to_string(),
        "check": check,
        "download": download,
        "state": now.state.word(),
        "version": now.version,
        "notes": now.notes,
        "got": now.got,
        "size": now.size,
        "checked": checked,
        "reason": now.reason,
        "later": now.later,
        "updated": now.updated,
        "before": now.before,
        "date": now.date,
    })
}

/// Every window of the app's own page told how the updates stand.
pub fn push(app: &AppHandle) {
    let told = view(app).to_string();
    for window in app.webview_windows().values() {
        if window.url().map(|u| u.path() == "/").unwrap_or(false) {
            let _ = window.eval(format!("window.__idiographUpdate && window.__idiographUpdate({told})"));
        }
    }
}

/// The updater as every check builds it: the plugin's settings from tauri.conf.json, a limit on how
/// long GitHub may take to answer, and on Windows the server stopped as Quit stops it before the
/// installer runs and the app ends.
fn updater(app: &AppHandle) -> Result<tauri_plugin_updater::Updater, Error> {
    app.updater_builder()
        .timeout(CHECK_WAIT)
        .on_before_exit(crate::stop_sidecar)
        .build()
}

/// The start: whether this run is the first of a newer version, for What's new, then the check a few
/// seconds on and once a day while checking is on.
pub fn begin(app: &AppHandle) {
    let running = app.package_info().version.to_string();
    if let Some(kept) = KEPT.get() {
        let ups = kept.updates();
        let ran = ups.get("ran").and_then(Value::as_str).unwrap_or("").to_string();
        let seen = ups.get("seen").and_then(Value::as_str).unwrap_or("").to_string();
        if newer(&running, &ran) && seen != running {
            let mut now = NOW.lock().unwrap();
            now.updated = running.clone();
            now.before = ran.clone();
        }
        if ran != running {
            kept.set_update("ran", json!(running));
        }
    }
    let app = app.clone();
    std::thread::spawn(move || {
        sleep(FIRST_WAIT);
        loop {
            let due = LAST.lock().unwrap().map(|at| at.elapsed() >= DAY).unwrap_or(true);
            if choice().0 == Some(true) && due {
                tauri::async_runtime::block_on(check(app.clone()));
            }
            sleep(LOOK_EVERY);
        }
    });
}

/// One check: a newer version found is offered, or downloaded by itself when he chose that. An update
/// already downloaded stays ready while the check finds the same version.
pub async fn check(app: AppHandle) {
    if BUSY.swap(true, Ordering::SeqCst) {
        return;
    }
    {
        let mut now = NOW.lock().unwrap();
        if now.state != State::Ready {
            now.state = State::Checking;
            now.reason.clear();
        }
    }
    push(&app);
    let found = match updater(&app) {
        Ok(updater) => updater.check().await,
        Err(err) => Err(err),
    };
    *LAST.lock().unwrap() = Some(Instant::now());
    keep("checked", json!(now_text()));
    let mut fetch = false;
    {
        let mut now = NOW.lock().unwrap();
        match found {
            Ok(Some(update)) => {
                if !(now.state == State::Ready && now.version == update.version) {
                    eprintln!("Idiograph: update {} found", update.version);
                    now.version = update.version.clone();
                    now.notes = update.body.clone().unwrap_or_default();
                    now.date = update.raw_json.get("pub_date").and_then(Value::as_str).unwrap_or("").to_string();
                    now.state = State::Available;
                    now.got = 0;
                    now.size = 0;
                    *FOUND.lock().unwrap() = Some(update);
                    *BYTES.lock().unwrap() = None;
                    fetch = choice().1;
                }
            }
            Ok(None) => {
                if now.state != State::Ready {
                    now.state = State::Nothing;
                }
            }
            Err(err) => {
                eprintln!("Idiograph: the check for updates failed: {err}");
                if now.state != State::Ready {
                    now.state = State::Failed;
                    now.reason = said(&err, false);
                }
            }
        }
    }
    BUSY.store(false, Ordering::SeqCst);
    push(&app);
    if fetch {
        download(app).await;
    }
}

/// The update downloaded and its signature checked against the public key, the plugin's own check,
/// then ready. A file whose signature does not hold is never kept.
pub async fn download(app: AppHandle) {
    let Some(update) = FOUND.lock().unwrap().clone() else { return };
    if BUSY.swap(true, Ordering::SeqCst) {
        return;
    }
    {
        let mut now = NOW.lock().unwrap();
        now.state = State::Downloading;
        now.got = 0;
        now.size = 0;
        now.reason.clear();
    }
    push(&app);
    let mut told = Instant::now();
    let tell = app.clone();
    let got = update
        .download(
            |n, size| {
                {
                    let mut now = NOW.lock().unwrap();
                    now.got += n as u64;
                    if let Some(size) = size {
                        now.size = size;
                    }
                }
                if told.elapsed() >= TELL_EVERY {
                    told = Instant::now();
                    push(&tell);
                }
            },
            || {},
        )
        .await;
    {
        let mut now = NOW.lock().unwrap();
        match got {
            Ok(bytes) => {
                eprintln!("Idiograph: update {} downloaded and its signature checked", update.version);
                *BYTES.lock().unwrap() = Some(bytes);
                now.state = State::Ready;
            }
            Err(err) => {
                eprintln!("Idiograph: the update did not download: {err}");
                now.state = State::Failed;
                now.reason = said(&err, true);
            }
        }
    }
    BUSY.store(false, Ordering::SeqCst);
    push(&app);
}

/// Relaunch now: the update put in place and the new version started. On Windows the installer does
/// both, the server stopped first and the app ended by the plugin. On a Mac the app quits as Quit
/// quits it, its server stopped first, the update is put in place as it quits (`at_quit`), and the
/// app starts again, the new version, or the old one still there should the update not go in.
fn relaunch(app: AppHandle) {
    let update = FOUND.lock().unwrap().clone();
    let ready = BYTES.lock().unwrap().is_some();
    let Some(update) = update.filter(|_| ready) else {
        fail(&app, &t_app("menus.update_not_ready"));
        return;
    };
    eprintln!("Idiograph: relaunching to install update {}", update.version);
    #[cfg(windows)]
    {
        let Some(bytes) = BYTES.lock().unwrap().clone() else { return };
        if let Err(err) = update.install(&bytes) {
            eprintln!("Idiograph: the update was not put in place: {err}");
            fail(&app, &t_app("menus.update_not_placed"));
        }
    }
    #[cfg(not(windows))]
    {
        let _ = update;
        app.restart();
    }
}

fn fail(app: &AppHandle, why: &str) {
    {
        let mut now = NOW.lock().unwrap();
        now.state = State::Failed;
        now.reason = crate::app::named(why);
    }
    push(app);
}

/// As the app quits, its server already stopped: an update downloaded and not yet installed is put in
/// place, so the next start is the new version, after Later, with nothing pressed, or on a Mac for
/// Relaunch now, whose start comes after. On Windows the installer runs with its progress bar alone
/// and starts nothing after it.
pub fn at_quit() {
    let update = FOUND.lock().unwrap().clone();
    let bytes = BYTES.lock().unwrap().take();
    let (Some(update), Some(bytes)) = (update, bytes) else { return };
    eprintln!("Idiograph: installing update {} as the app quits", update.version);
    let update = update.restart_after_install(false);
    if let Err(err) = update.install(&bytes) {
        eprintln!("Idiograph: Idiograph could not put the update in place. {err}");
    }
}

/// The page's command: `read`, `choose` (the question asked once) or `set` (Settings' Save) with
/// `check` and `download`, `check`, `download`, `later`, `seen` once the line of What's new has shown,
/// and `relaunch` with the page's place, which the new version opens on, the page's Relaunch now.
pub fn act(app: &AppHandle, op: &str, check_: Option<bool>, download_: Option<bool>, place: Option<Map<String, Value>>) -> Value {
    match op {
        "choose" | "set" => {
            let (was_check, was_download) = choice();
            if let Some(on) = check_ {
                keep("check", json!(on));
            }
            if let Some(on) = download_ {
                keep("download", json!(on));
            }
            let (now_check, now_download) = choice();
            if now_check == Some(true) && was_check != Some(true) {
                tauri::async_runtime::spawn(check(app.clone()));
            } else if now_download && !was_download && NOW.lock().unwrap().state == State::Available {
                tauri::async_runtime::spawn(download(app.clone()));
            }
        }
        "check" => {
            tauri::async_runtime::spawn(check(app.clone()));
        }
        "download" => {
            tauri::async_runtime::spawn(download(app.clone()));
        }
        "later" => {
            NOW.lock().unwrap().later = true;
            push(app);
        }
        "seen" => {
            let shown = {
                let mut now = NOW.lock().unwrap();
                now.before.clear();
                std::mem::take(&mut now.updated)
            };
            if !shown.is_empty() {
                keep("seen", json!(shown));
            }
        }
        "relaunch" => {
            if let (Some(kept), Some(place)) = (KEPT.get(), place) {
                kept.set_place(&place);
            }
            let app = app.clone();
            std::thread::spawn(move || relaunch(app));
        }
        _ => {}
    }
    view(app)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn compares_versions_as_numbers() {
        assert!(newer("0.9.2", "0.9.1"));
        assert!(newer("0.9.10", "0.9.9"));
        assert!(newer("1.0.0", "0.9.12"));
        assert!(!newer("0.9.1", "0.9.1"));
        assert!(!newer("0.9.1", "0.9.2"));
        assert!(!newer("0.9.2", ""));
        assert_eq!(numbers("0.9.2-beta"), vec![0, 9, 2]);
    }

    #[test]
    fn says_each_failure_plainly() {
        assert_eq!(said(&Error::ReleaseNotFound, false), "GitHub's answer about the newest version could not be read.");
        assert_eq!(said(&Error::MissingSignedVersion, true),
                   "Idiograph could not confirm the update is genuine, so it was not installed.");
        assert_eq!(said(&Error::EmptyEndpoints, false), "GitHub could not be reached, so Idiograph could not check for updates.");
        assert_eq!(said(&Error::EmptyEndpoints, true), "The update could not be downloaded.");
    }
}
