//! The window's own words (28 October 2026, the text layer's fifth build): its menus, its few messages
//! and the kinds its save panel names, by key from `family/static/i18n/<language>/menus.json`, as the
//! page takes its words from the same catalogue (`family/i18n.py`, `docs/internals.md`, The text layer).
//!
//! English is built into the window, so a key always has its words. The language is the one the app has
//! chosen, `language` in its settings (`config.json` in its data folder), or when that is empty the
//! computer's own: the Mac's first preferred language, else the environment's (LC_ALL, LC_MESSAGES,
//! LANG). A language's file, and a less specific one's (`es` for `es-MX`), comes from the server's own
//! `static/i18n/` in the bundle and replaces English's messages by key. A message's `{name}` slots are
//! filled by `t_with`.

use std::env;
use std::fs;
use std::path::PathBuf;
use std::sync::OnceLock;

use serde_json::{Map, Value};

/// English, the base every other language falls back to.
const ENGLISH: &str = include_str!("../../../../family/static/i18n/en/menus.json");

/// A tag as the catalogue's folders are named, `en_GB.UTF-8` as `en-GB`, or "" for none.
pub fn normal(tag: &str) -> String {
    let tag = tag.trim().split('.').next().unwrap_or("").split('@').next().unwrap_or("").replace('_', "-");
    if tag.is_empty() || tag == "C" || tag == "POSIX" {
        return String::new();
    }
    let mut parts = tag.split('-');
    let head = parts.next().unwrap_or("").to_lowercase();
    if !(2..=3).contains(&head.len()) || !head.chars().all(|c| c.is_ascii_lowercase()) {
        return String::new();
    }
    let rest: Vec<String> = parts
        .map(|p| if p.len() == 2 { p.to_uppercase() } else { p.to_string() })
        .collect();
    if rest.iter().any(|p| p.is_empty() || !p.chars().all(|c| c.is_ascii_alphanumeric())) {
        return String::new();
    }
    std::iter::once(head).chain(rest).collect::<Vec<_>>().join("-")
}

/// The app's settings file, where its chosen language is kept.
fn config_file() -> PathBuf {
    let name = crate::app::name();
    if cfg!(windows) {
        let roaming = env::var("APPDATA").map(PathBuf::from).unwrap_or_else(|_| {
            PathBuf::from(env::var("USERPROFILE").unwrap_or_default()).join("AppData").join("Roaming")
        });
        roaming.join(name).join("config.json")
    } else {
        PathBuf::from(env::var("HOME").unwrap_or_default())
            .join("Library").join("Application Support").join(name).join("config.json")
    }
}

/// The Mac's first preferred language, as System Settings orders them.
fn mac_language() -> String {
    if !cfg!(target_os = "macos") {
        return String::new();
    }
    let out = std::process::Command::new("/usr/bin/defaults").args(["read", "-g", "AppleLanguages"]).output();
    let Ok(out) = out else { return String::new() };
    let text = String::from_utf8_lossy(&out.stdout);
    text.split('"').nth(1).map(normal).unwrap_or_default()
}

/// The language the window speaks: the settings' choice, else the computer's, else English.
pub fn language() -> String {
    let chosen = fs::read_to_string(config_file())
        .ok()
        .and_then(|text| serde_json::from_str::<Value>(&text).ok())
        .and_then(|v| v.get("language").and_then(Value::as_str).map(normal))
        .unwrap_or_default();
    if !chosen.is_empty() {
        return chosen;
    }
    let mac = mac_language();
    if !mac.is_empty() {
        return mac;
    }
    for name in ["LC_ALL", "LC_MESSAGES", "LANG"] {
        let found = normal(&env::var(name).unwrap_or_default());
        if !found.is_empty() {
            return found;
        }
    }
    "en".into()
}

/// The folders a language's file may be in beside the frozen server, its `static/i18n/`.
fn folders(tag: &str) -> Vec<PathBuf> {
    let dir = crate::server_dir();
    [dir.join("_internal"), dir]
        .into_iter()
        .map(|base| base.join("static").join("i18n").join(tag).join("menus.json"))
        .collect()
}

/// Every message in `tag`: English's, then each less specific folder's that is there, then the most
/// specific's, each replacing the one before by key.
pub fn messages_in(tag: &str) -> Map<String, Value> {
    let mut out: Map<String, Value> = serde_json::from_str(ENGLISH).unwrap_or_default();
    let parts: Vec<&str> = tag.split('-').collect();
    for n in 1..=parts.len() {
        let step = parts[..n].join("-");
        if step == "en" || step.is_empty() {
            continue;
        }
        for file in folders(&step) {
            if let Some(Value::Object(more)) = fs::read_to_string(&file).ok().and_then(|t| serde_json::from_str(&t).ok()) {
                out.extend(more);
                break;
            }
        }
    }
    out
}

fn messages() -> &'static Map<String, Value> {
    static HELD: OnceLock<Map<String, Value>> = OnceLock::new();
    HELD.get_or_init(|| messages_in(&language()))
}

/// The message `key`, or the key itself, said once on the window's output, where none has it.
pub fn t(key: &str) -> String {
    match messages().get(key).and_then(Value::as_str) {
        Some(text) => text.to_string(),
        None => {
            eprintln!("Idiograph: no message for {key}");
            key.to_string()
        }
    }
}

/// The message `key` with each `{name}` slot filled.
pub fn t_with(key: &str, slots: &[(&str, &str)]) -> String {
    let mut text = t(key);
    for (name, value) in slots {
        text = text.replace(&format!("{{{name}}}"), value);
    }
    text
}

/// The message `key` with the app's own name in its `{app}` slot, "Quit Sift" in Sift.
pub fn t_app(key: &str) -> String {
    t_with(key, &[("app", crate::app::name())])
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn english_is_built_in_and_slots_fill() {
        let en: Map<String, Value> = serde_json::from_str(ENGLISH).unwrap();
        assert!(en.keys().all(|k| k.starts_with("menus.")));
        assert_eq!(messages_in("en").get("menus.edit").and_then(Value::as_str), Some("Edit"));
        assert_eq!(t_with("menus.quit", &[("app", "Sift")]), "Quit Sift");
        let nowhere = format!("menus.{}", "nowhere");
        assert_eq!(t(&nowhere), nowhere);
        assert_eq!(normal("en_GB.UTF-8"), "en-GB");
        assert_eq!(normal("es-mx"), "es-MX");
        assert_eq!(normal("C"), "");
    }
}
