//! The window's menus, each system's own (17 October, the second build).
//!
//! On a Mac the menu bar as Apple's guidelines have it: Idiograph, with About Idiograph (the page's own
//! card since 20 October, as on Windows), Settings… on
//! Cmd+comma, Services, Hide, Hide Others, Show All and Quit, then File, Edit, View, Window and Help.
//! On Windows each window carries its own menu bar, as a Windows program's does, with the keys Windows
//! names: File, Edit, View and Help, Settings in File and About in Help, Exit at the foot of File, and
//! no Window menu, since the windows stay separate windows there (Adam, 17 October).
//!
//! File has New Window, Open Recent, the home screen's projects as the page hands them over (see
//! `window.js`), each opening in a new window where it opens on the home screen, then Project History, the open
//! project's record, greyed where no project is open (4 November), Project Settings…, the open project's own
//! settings sheet, greyed on Home alone since a demo's opens read-only (settingsplit, 5 November), and Close Window.
//! Edit has Undo, Redo, Cut, Copy, Paste and Select All, then Find… (Cmd+F), Search on every screen, and Find and
//! Replace… (Cmd+Shift+F), the statements screen's Find and replace card, greyed where no statements screen is in
//! front (barsD, 6 November 2026), each pressing its keys in the page as he would. On a Mac Undo and Redo ask the page first,
//! so on a board they reach the app's own undo and in a text field the field's, and a Spelling and
//! Grammar menu follows, as a browser has it. On Windows the six give the page the keyboard and press
//! their keys there, and the page takes Ctrl+Z and Ctrl+Y on a board as it takes them in a field.
//! View has Home (Cmd+Shift+H, Alt+Home on Windows), then Bigger Text, Smaller Text and Actual Size, Cmd
//! or Ctrl with +, - and 0, the windows' zoom, which Settings' Text size moves too (20 October, Settled
//! 12), and Reload. Help has the
//! manual, What's New, the version's notes (the fourth build), the shortcuts and Send feedback.
//!
//! Linux has Windows's menu bar, its words cut at the tab where Windows names an item's keys in its words, and those
//! keys given as the item's own, which GTK draws at the right (linuxfix, 9 November 2026). Edit's Undo, Redo, Cut,
//! Copy, Paste and Select All carry no keys there, so the keys reach the page (linuxfix3, `edit_keys`).

use std::sync::Mutex;

use serde_json::Value;
use tauri::menu::{Menu, MenuItem, PredefinedMenuItem, Submenu};
use tauri::{AppHandle, Wry};

use crate::words::{t, t_app};

/// One of the home screen's projects as the page hands it over: its part, sift, distil or trace, its
/// name, and what opens it, a Distil project's id or a Sift or Trace project's folder.
#[derive(Clone, Debug, PartialEq)]
pub struct Recent {
    pub part: String,
    pub name: String,
    pub id: String,
    pub folder: String,
}

static RECENT: Mutex<Vec<Recent>> = Mutex::new(Vec::new());
/// Each menu bar's Open Recent, Send Feedback, Project History, Project Settings and Find and Replace, by the window it
/// belongs to, "app" for the menu the app starts with. On Windows each window but the first has a menu bar of its own
/// (see `for_window`).
type Bar = (String, Submenu<Wry>, MenuItem<Wry>, MenuItem<Wry>, MenuItem<Wry>, MenuItem<Wry>);
static BARS: Mutex<Vec<Bar>> = Mutex::new(Vec::new());
/// The parts in the home screen's order, each with the word its group carries in Open Recent.
pub const PARTS: [(&str, &str); 3] = [("sift", "Sift"), ("distil", "Idiograph"), ("trace", "Trace")];

fn item(app: &AppHandle, id: &str, text: &str, keys: Option<&str>) -> tauri::Result<MenuItem<Wry>> {
    MenuItem::with_id(app, id, text, true, keys)
}

/// The Mac's menu bar.
#[cfg(target_os = "macos")]
pub fn build(app: &AppHandle) -> tauri::Result<Menu<Wry>> {
    use tauri::menu::{HELP_SUBMENU_ID, WINDOW_SUBMENU_ID};
    let sep = || PredefinedMenuItem::separator(app);
    let idiograph = Submenu::with_items(app, crate::app::name(), true, &[
        // the app's own About, the page's card with its acknowledgements, in place of the system's panel
        // (20 October, Adam: thanks to Curt Strangward, Claude Code and the author)
        &item(app, "about", &t_app("menus.about"), None)?,
        &sep()?,
        &item(app, "settings", &t("menus.settings"), Some("CmdOrCtrl+,"))?,
        &sep()?,
        &PredefinedMenuItem::services(app, None)?,
        &sep()?,
        &PredefinedMenuItem::hide(app, Some(t_app("menus.hide").as_str()))?,
        &PredefinedMenuItem::hide_others(app, Some(t("menus.hide_others").as_str()))?,
        &PredefinedMenuItem::show_all(app, Some(t("menus.show_all").as_str()))?,
        &sep()?,
        // Quit asks every window to close as its close button does, so what is typed is saved first
        &item(app, "quit", &t_app("menus.quit"), Some("CmdOrCtrl+Q"))?,
    ])?;
    let recent = Submenu::with_id(app, "open-recent", t("menus.open_recent"), true)?;
    // the history of the project open in the window in front, as Home's project menu has it, greyed
    // where no project is open (4 November)
    let history = item(app, "project-history", &t("menus.project_history"), None)?;
    // and its own settings sheet, greyed on Home (settingsplit, 5 November)
    let project = item(app, "project-settings", &t("menus.project_settings"), None)?;
    let file = Submenu::with_items(app, t("menus.file"), true, &[
        &item(app, "new-window", &t("menus.new_window"), Some("CmdOrCtrl+N"))?,
        &recent,
        &sep()?,
        &history,
        &project,
        &sep()?,
        &PredefinedMenuItem::close_window(app, Some(t("menus.close_window").as_str()))?,
    ])?;
    // Find and Replace, the statements screen's card, greyed where it does not apply, as Project History is (barsD)
    let replace = item(app, "find-replace", &t("menus.find_replace"), Some("CmdOrCtrl+Shift+F"))?;
    let edit = Submenu::with_items(app, t("menus.edit"), true, &[
        &item(app, "undo", &t("menus.undo"), Some("CmdOrCtrl+Z"))?,
        &item(app, "redo", &t("menus.redo"), Some("CmdOrCtrl+Shift+Z"))?,
        &sep()?,
        &PredefinedMenuItem::cut(app, Some(t("menus.cut").as_str()))?,
        &PredefinedMenuItem::copy(app, Some(t("menus.copy").as_str()))?,
        &PredefinedMenuItem::paste(app, Some(t("menus.paste").as_str()))?,
        &PredefinedMenuItem::select_all(app, Some(t("menus.select_all").as_str()))?,
        &sep()?,
        // Find, Search on every screen of the app's, as Cmd+F opens it (barsD, 6 November 2026)
        &item(app, "find", &t("menus.find"), Some("CmdOrCtrl+F"))?,
        &replace,
    ])?;
    let view = Submenu::with_items(app, t("menus.view"), true, &[
        // Home, the page's Home from any screen, as the bars' mark is (20 October)
        &item(app, "home", &t("menus.home"), Some("CmdOrCtrl+Shift+H"))?,
        &sep()?,
        // the text size, the windows' zoom, as Settings' Text size has it (20 October, Settled 12)
        &item(app, "zoom-in", &t("menus.bigger_text"), Some("CmdOrCtrl+NumpadAdd"))?,
        &item(app, "zoom-out", &t("menus.smaller_text"), Some("CmdOrCtrl+-"))?,
        &item(app, "zoom-actual", &t("menus.actual_size"), Some("CmdOrCtrl+0"))?,
        &sep()?,
        // the PETs and GETs boards' status bar on or off, as Settings' View turns it (19 October)
        &item(app, "status-bar", &t("menus.status_bar"), None)?,
        &sep()?,
        &item(app, "reload", &t("menus.reload"), Some("CmdOrCtrl+R"))?,
        &sep()?,
        &PredefinedMenuItem::fullscreen(app, Some(t("menus.full_screen").as_str()))?,
    ])?;
    // the Window menu the system fills, its windows and its tab items among them, Show Previous Tab and
    // Show Next Tab on Ctrl+Shift+Tab and Ctrl+Tab, Merge All Windows and Move Tab to New Window, where
    // the first build's own pair on Cmd+Shift+[ and ] stood twice beside the system's (the second build)
    let window = Submenu::with_id_and_items(app, WINDOW_SUBMENU_ID, t("menus.window"), true, &[
        &PredefinedMenuItem::minimize(app, Some(t("menus.minimize").as_str()))?,
        &PredefinedMenuItem::maximize(app, Some(t("menus.zoom").as_str()))?,
        &sep()?,
        &PredefinedMenuItem::bring_all_to_front(app, Some(t("menus.bring_all_to_front").as_str()))?,
    ])?;
    let feedback = item(app, "feedback", &t("menus.feedback"), None)?;
    let help = Submenu::with_id_and_items(app, HELP_SUBMENU_ID, t("menus.help"), true, &[
        &item(app, "manual", &t_app("menus.manual"), None)?,
        &item(app, "whatsnew", &t_app("menus.whats_new"), None)?,
        &item(app, "shortcuts", &t("menus.shortcuts"), None)?,
        &sep()?,
        &feedback,
    ])?;
    keep_bar("app", recent, feedback, history, project, replace);
    let menu = Menu::with_items(app, &[&idiograph, &file, &edit, &view, &window, &help])?;
    draw_recent(app);
    Ok(menu)
}

/// Each window's menu bar on Windows, its letters underlined for Alt as Windows's own are.
#[cfg(not(target_os = "macos"))]
pub fn build(app: &AppHandle) -> tauri::Result<Menu<Wry>> {
    build_bar(app, "app")
}

/// A menu bar of a window's own on Windows, for every window but the first: one menu bar shared by
/// several windows went with the first of them to close, so every window opened after had none, the
/// print views, the manual and a second window (17 October, the third build's first Windows run).
#[cfg(not(target_os = "macos"))]
pub fn for_window(app: &AppHandle, label: &str) -> tauri::Result<Menu<Wry>> {
    build_bar(app, label)
}

#[cfg(not(target_os = "macos"))]
fn build_bar(app: &AppHandle, label: &str) -> tauri::Result<Menu<Wry>> {
    let sep = || PredefinedMenuItem::separator(app);
    let recent = Submenu::with_id(app, "open-recent", t("menus.win_open_recent"), true)?;
    let history = item(app, "project-history", &t("menus.win_project_history"), None)?;
    let project = item(app, "project-settings", &t("menus.win_project_settings"), None)?;
    let file = Submenu::with_items(app, t("menus.win_file"), true, &[
        &item(app, "new-window", &t("menus.win_new_window"), Some("Ctrl+N"))?,
        &recent,
        &sep()?,
        &history,
        &project,
        &sep()?,
        &item(app, "settings", &t("menus.win_settings"), Some("Ctrl+,"))?,
        &sep()?,
        &PredefinedMenuItem::close_window(app, Some(t("menus.win_close_window").as_str()))?,
        &item(app, "quit", &t("menus.win_exit"), None)?,
    ])?;
    // each the window's own, which gives the page the keyboard and then presses its keys there (see
    // `press_in_page` in main.rs), as the system's own pressed them before the page had the keyboard
    // back (17 October, the second build's third Windows run)
    // Find and Find and Replace name their keys in their words, as Home does, and the page hears the keys itself
    // (barsD, 6 November 2026), Find and Replace greyed where no statements screen is in front. On Linux the keys
    // are the item's own instead (`keyed`)
    let replace = keyed(app, "find-replace", &t("menus.win_find_replace"), "Ctrl+Shift+F")?;
    let edit = Submenu::with_items(app, t("menus.win_edit"), true, &[
        &item(app, "edit-undo", &t("menus.win_undo"), edit_keys("Ctrl+Z"))?,
        &item(app, "edit-redo", &t("menus.win_redo"), edit_keys("Ctrl+Y"))?,
        &sep()?,
        &item(app, "edit-cut", &t("menus.win_cut"), edit_keys("Ctrl+X"))?,
        &item(app, "edit-copy", &t("menus.win_copy"), edit_keys("Ctrl+C"))?,
        &item(app, "edit-paste", &t("menus.win_paste"), edit_keys("Ctrl+V"))?,
        &sep()?,
        &item(app, "edit-select-all", &t("menus.win_select_all"), edit_keys("Ctrl+A"))?,
        &sep()?,
        &keyed(app, "find", &t("menus.win_find"), "Ctrl+F")?,
        &replace,
    ])?;
    // Bigger Text and Smaller Text name their keys as Windows's own programs do, Ctrl+Plus and Ctrl+Minus, in the
    // item's words: the numeric pad's plus showed no key at all (17 October, the second build's
    // screenshots), and the page hears the keys itself (window.js), never the menu
    let view = Submenu::with_items(app, t("menus.win_view"), true, &[
        // Home names Alt+Home in its words, as a browser's is, and the page hears the keys itself
        &keyed(app, "home", &t("menus.win_home"), "Alt+Home")?,
        &sep()?,
        // on Linux the numeric pad's plus is Bigger Text's own key, as on a Mac, the row's = and + left to the page
        &keyed(app, "zoom-in", &t("menus.win_bigger_text"), "Ctrl+NumpadAdd")?,
        &keyed(app, "zoom-out", &t("menus.win_smaller_text"), "Ctrl+-")?,
        &item(app, "zoom-actual", &t("menus.win_actual_size"), Some("Ctrl+0"))?,
        &sep()?,
        &item(app, "status-bar", &t("menus.win_status_bar"), None)?,
        &sep()?,
        &item(app, "reload", &t("menus.win_reload"), Some("Ctrl+R"))?,
    ])?;
    let feedback = item(app, "feedback", &t("menus.win_feedback"), None)?;
    let help = Submenu::with_items(app, t("menus.win_help"), true, &[
        &item(app, "manual", &t_app("menus.win_manual"), Some("F1"))?,
        &item(app, "whatsnew", &t("menus.win_whats_new"), None)?,
        &item(app, "shortcuts", &t("menus.win_shortcuts"), None)?,
        &sep()?,
        &feedback,
        &sep()?,
        &item(app, "about", &t_app("menus.win_about"), None)?,
    ])?;
    keep_bar(label, recent.clone(), feedback, history, project, replace);
    let menu = Menu::with_items(app, &[&file, &edit, &view, &help])?;
    let list = RECENT.lock().unwrap().clone();
    draw_one(app, &recent, &list);
    Ok(menu)
}

/// An item whose Windows words name its keys after a tab, "&Find…\tCtrl+F", which Windows draws at the menu's right
/// while the page hears the keys itself. GTK draws the tab and the keys inside the words (linuxfix, 9 November 2026,
/// the Linux desktop's Edit and View menus), so on Linux the words are cut at the tab and `keys` given as the item's
/// own accelerator, which GTK draws at the right as it draws Undo's, the item then doing what its keys do.
#[cfg(not(target_os = "macos"))]
fn keyed(app: &AppHandle, id: &str, words: &str, keys: &str) -> tauri::Result<MenuItem<Wry>> {
    if cfg!(target_os = "linux") {
        item(app, id, before_tab(words), Some(keys))
    } else {
        item(app, id, words, None)
    }
}

/// The keys of Edit's Undo, Redo, Cut, Copy, Paste and Select All: Windows's, where the item presses them in the page
/// (`press_in_page` in main.rs), and none on Linux, where GTK took the keys for the item before the page had them, so
/// Ctrl+A, C, V and Z did nothing in a text field (linuxfix3, 9 November 2026, the Linux desktop). There the keys reach
/// the page, which edits as it always does, and the item runs WebKitGTK's own editing command (`linux::edit`).
#[cfg_attr(target_os = "macos", allow(dead_code))]
pub fn edit_keys(keys: &str) -> Option<&str> {
    if cfg!(target_os = "linux") { None } else { Some(keys) }
}

/// An item's words up to the tab that names its keys on Windows, the whole words where there is none.
#[cfg_attr(target_os = "macos", allow(dead_code))]
pub fn before_tab(words: &str) -> &str {
    words.split('\t').next().unwrap_or(words).trim_end()
}

/// The list the page hands over, the projects that have what opens them, at most forty.
pub fn take_recent(list: &[Value]) -> Vec<Recent> {
    let text = |v: &Value, k: &str| v.get(k).and_then(Value::as_str).unwrap_or("").trim().to_string();
    list.iter()
        .map(|v| Recent { part: text(v, "part"), name: text(v, "name"), id: text(v, "id"), folder: text(v, "folder") })
        .filter(|r| PARTS.iter().any(|(p, _)| *p == r.part) && !r.name.is_empty()
                    && (if r.part == "distil" { !r.id.is_empty() } else { !r.folder.is_empty() }))
        .take(40)
        .collect()
}

/// A menu bar's Open Recent, Send Feedback, Project History, Project Settings and Find and Replace kept, so each is
/// drawn afresh with the rest, the last four as the page last said.
fn keep_bar(label: &str, recent: Submenu<Wry>, feedback: MenuItem<Wry>, history: MenuItem<Wry>, project: MenuItem<Wry>,
            replace: MenuItem<Wry>) {
    let _ = feedback.set_enabled(*FEEDBACK_ON.lock().unwrap());
    let _ = history.set_enabled(*HISTORY_ON.lock().unwrap());
    let _ = project.set_enabled(*PROJECT_ON.lock().unwrap());
    let _ = replace.set_enabled(*REPLACE_ON.lock().unwrap());
    let mut bars = BARS.lock().unwrap();
    bars.retain(|(l, _, _, _, _, _)| l != label);
    bars.push((label.to_string(), recent, feedback, history, project, replace));
}

/// A window gone, its menu bar with it.
pub fn forget(label: &str) {
    BARS.lock().unwrap().retain(|(l, _, _, _, _, _)| l != label);
}

static FEEDBACK_ON: Mutex<bool> = Mutex::new(false);
static HISTORY_ON: Mutex<bool> = Mutex::new(false);
static PROJECT_ON: Mutex<bool> = Mutex::new(false);
static REPLACE_ON: Mutex<bool> = Mutex::new(false);

/// Project History on or greyed, as the page says whether a project with a history is open, Project Settings
/// as it says whether any project is open, a demo's included (settingsplit, 5 November), and Edit's Find and Replace
/// as it says whether the statements screen is in front, where its card is (barsD, 6 November).
pub fn set_history(on: bool, settings: bool, replace: bool) {
    *HISTORY_ON.lock().unwrap() = on;
    *PROJECT_ON.lock().unwrap() = settings;
    *REPLACE_ON.lock().unwrap() = replace;
    let items: Vec<(MenuItem<Wry>, MenuItem<Wry>, MenuItem<Wry>)> =
        BARS.lock().unwrap().iter().map(|(_, _, _, h, p, r)| (h.clone(), p.clone(), r.clone())).collect();
    for (history, project, find) in items {
        let _ = history.set_enabled(on);
        let _ = project.set_enabled(settings);
        let _ = find.set_enabled(replace);
    }
}

/// Open Recent and Send Feedback afresh from what the page handed over.
pub fn set_recent(app: &AppHandle, list: Vec<Recent>, feedback: bool) {
    *FEEDBACK_ON.lock().unwrap() = feedback;
    // the items taken out first, so no lock is held while a menu waits on the main thread
    let items: Vec<MenuItem<Wry>> = BARS.lock().unwrap().iter().map(|(_, _, i, _, _, _)| i.clone()).collect();
    for item in items {
        let _ = item.set_enabled(feedback);
    }
    {
        let mut held = RECENT.lock().unwrap();
        if *held == list {
            return;
        }
        *held = list;
    }
    draw_recent(app);
}

pub fn recent_at(n: usize) -> Option<Recent> {
    RECENT.lock().unwrap().get(n).cloned()
}

/// Open Recent in every menu bar.
fn draw_recent(app: &AppHandle) {
    let list = RECENT.lock().unwrap().clone();
    let menus: Vec<Submenu<Wry>> = BARS.lock().unwrap().iter().map(|(_, m, _, _, _, _)| m.clone()).collect();
    for menu in menus {
        draw_one(app, &menu, &list);
    }
}

/// One Open Recent: each part's projects under its word, the parts apart, or one line greyed when the
/// home screen has not been drawn yet.
fn draw_one(app: &AppHandle, menu: &Submenu<Wry>, list: &[Recent]) {
    while let Ok(Some(_)) = menu.remove_at(0) {}
    if list.is_empty() {
        if let Ok(none) = MenuItem::with_id(app, "recent-none", t("menus.no_projects"), false, None::<&str>) {
            let _ = menu.append(&none);
        }
        return;
    }
    let mut first = true;
    for (part, word) in PARTS {
        let rows: Vec<(usize, &Recent)> = list.iter().enumerate().filter(|(_, r)| r.part == part).collect();
        if rows.is_empty() {
            continue;
        }
        if !first {
            if let Ok(sep) = PredefinedMenuItem::separator(app) {
                let _ = menu.append(&sep);
            }
        }
        first = false;
        if let Ok(head) = MenuItem::with_id(app, format!("recent-head-{part}"), word, false, None::<&str>) {
            let _ = menu.append(&head);
        }
        for (n, r) in rows {
            // an ampersand in a name is its own on Windows, where one alone marks a letter for Alt
            let name = if cfg!(windows) { r.name.replace('&', "&&") } else { r.name.clone() };
            if let Ok(row) = MenuItem::with_id(app, format!("recent-{n}"), name, true, None::<&str>) {
                let _ = menu.append(&row);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn cuts_the_windows_keys_from_the_words() {
        assert_eq!(before_tab("&Find…\tCtrl+F"), "&Find…");
        assert_eq!(before_tab("&Bigger Text\tCtrl+Plus"), "&Bigger Text");
        assert_eq!(before_tab("&Reload"), "&Reload");
    }

    #[test]
    fn edit_items_leave_their_keys_to_the_page_on_linux() {
        let want = if cfg!(target_os = "linux") { None } else { Some("Ctrl+C") };
        assert_eq!(edit_keys("Ctrl+C"), want);
    }

    #[test]
    fn takes_only_what_opens() {
        let list = vec![
            json!({"part": "sift", "name": "Dog routines", "folder": "/x/sift"}),
            json!({"part": "distil", "name": "Walks", "id": "p1"}),
            json!({"part": "distil", "name": "No id"}),
            json!({"part": "trace", "name": "", "folder": "/x/t"}),
            json!({"part": "other", "name": "Odd", "id": "o"}),
        ];
        let got = take_recent(&list);
        assert_eq!(got.iter().map(|r| r.name.as_str()).collect::<Vec<_>>(), vec!["Dog routines", "Walks"]);
    }
}
