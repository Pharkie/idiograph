//! A shared copy opened from outside the app (fileassoc, 6 November 2026, Adam: the tester's copy came back as a
//! `.idiograph` file and the Finder did not know it for Idiograph's). tauri.conf.json makes `.idiograph` Idiograph's
//! own document type, so a double click in the Finder or Explorer, a drop on the Dock's icon and Open With all open
//! the file in Idiograph. Each file is handed to the page, which takes it into Home's Open a shared copy with the file
//! already chosen (`idiographOpenFile` in distil.js), so a copy coming back offers its boards to its project as the
//! button's way does.
//!
//! The files come three ways. On a Mac the system tells the running app, `RunEvent::Opened`, whether the file
//! started it or it was open already. On Windows the file is the command line's argument, `Idiograph.exe "%1"` as
//! the installer writes it: for the first start in `main`, and for a start while Idiograph runs through the
//! single-instance plugin, which hands the second start's arguments and folder to the running app and ends the
//! second before it starts a server. Either way the files wait here until a window of the app's own page takes them
//! (`take`, through the command `opened`): the first window as its page loads, or the window in front, told there
//! are files waiting and brought forward. Sift and Trace claim no file type (bundle.py, `NO_FILES`) and take none.

use std::path::{Path, PathBuf};
use std::sync::atomic::Ordering;
use std::sync::Mutex;

use serde_json::Map;
use tauri::{AppHandle, Manager};

/// The files waiting for a page to take them, as their paths, in the order they came.
static WAITING: Mutex<Vec<String>> = Mutex::new(Vec::new());

/// The server's options that take a value after them, whose value is never a file to open.
const WITH_VALUE: [&str; 4] = ["--port", "--root", "--config", "--app"];

/// The page told, in the window in front, that files are waiting (window.js).
const TELL_JS: &str = "window.__idiographOpened && window.__idiographOpened()";

/// Whether this app takes files, Idiograph alone.
fn ours() -> bool {
    std::ptr::eq(super::app::this(), &super::app::APPS[0])
}

/// The command line's arguments apart: the rest as they came, for the server, and the files, each an argument
/// that is no option and no option's value, as Explorer gives a file it opens, made whole against `cwd`. The
/// server takes no argument of that kind, so none is ever handed to it.
pub fn apart(args: &[String], cwd: &Path) -> (Vec<String>, Vec<String>) {
    let (mut rest, mut files) = (Vec::new(), Vec::new());
    let mut value = false;
    for arg in args {
        if value {
            rest.push(arg.clone());
            value = false;
        } else if arg.starts_with('-') {
            value = WITH_VALUE.contains(&arg.as_str());
            rest.push(arg.clone());
        } else if !arg.trim().is_empty() {
            let path = Path::new(arg);
            let whole: PathBuf = if path.is_absolute() { path.to_path_buf() } else { cwd.join(path) };
            files.push(whole.display().to_string());
        }
    }
    (rest, files)
}

/// The files among the addresses the Mac's system hands the app, each a file's own.
#[cfg(target_os = "macos")]
pub fn in_urls(urls: &[tauri::Url]) -> Vec<String> {
    urls.iter()
        .filter(|u| u.scheme() == "file")
        .filter_map(|u| u.to_file_path().ok())
        .map(|p| p.display().to_string())
        .collect()
}

/// Files to open kept until a page takes them, Idiograph's alone. Whether any were kept.
pub fn keep(files: Vec<String>) -> bool {
    if files.is_empty() || !ours() {
        return false;
    }
    WAITING.lock().unwrap().extend(files);
    true
}

/// Files to open, from a running app: kept, and the window in front told and brought forward. Before the first
/// window is open there is nothing to tell, and its page takes them as it loads. With no window of the app's own
/// page open, the manual's alone, a window on Home opens and takes them. Whether any were kept, so Sift and Trace,
/// which take none, bring their window forward as before.
pub fn hand(app: &AppHandle, files: Vec<String>) -> bool {
    if !keep(files) {
        return false;
    }
    let open = app.webview_windows().into_values().any(|w| !super::let_go_already(app, w.label()));
    if !open || super::QUITTING.load(Ordering::SeqCst) || super::EXITING.load(Ordering::SeqCst) {
        return true;
    }
    match super::front(app, true) {
        Some(window) => {
            let _ = window.eval(TELL_JS);
            // a check's windows never take the keyboard, and it says which window was told
            #[cfg(feature = "drive")]
            eprintln!("drive: files told to {}", window.label());
            #[cfg(not(feature = "drive"))]
            {
                let _ = window.unminimize();
                let _ = window.show();
                let _ = window.set_focus();
            }
        }
        None => {
            let port = super::PORT.load(Ordering::SeqCst) as u16;
            super::aside(app, move |app| {
                let _ = super::app_window(&app, port, None, Map::new());
            });
        }
    }
    true
}

/// What a page takes, every file waiting, each once: a window of the app's own page alone, never a print view's
/// or the manual's.
pub fn take(window: &tauri::WebviewWindow) -> Vec<String> {
    if !super::own_page(window) {
        return Vec::new();
    }
    std::mem::take(&mut *WAITING.lock().unwrap())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn strings(list: &[&str]) -> Vec<String> {
        list.iter().map(|s| s.to_string()).collect()
    }

    #[test]
    fn a_file_on_the_command_line_is_opened_and_never_handed_to_the_server() {
        // a folder whole on either system, the second start's own
        let cwd = std::env::temp_dir().join("Kites");
        let whole = cwd.join("Back from Curt.idiograph").display().to_string();
        // Explorer's double click: the file alone, whole
        let (rest, files) = apart(&[whole.clone()], &cwd);
        assert!(rest.is_empty());
        assert_eq!(files, vec![whole]);
        // the options and their values go to the server, a value never taken for a file, and a file named from
        // the folder the start was in made whole there
        let (rest, files) = apart(&strings(&["--port", "9100", "--config", "config.json", "--root=r", "--no-browser",
                                              "Winter.idiograph", "-psn_0_1234"]), &cwd);
        assert_eq!(rest, strings(&["--port", "9100", "--config", "config.json", "--root=r", "--no-browser", "-psn_0_1234"]));
        assert_eq!(files, vec![cwd.join("Winter.idiograph").display().to_string()]);
        // nothing given, nothing to open
        assert_eq!(apart(&[], &cwd), (Vec::new(), Vec::new()));
    }
}
