//! What the window keeps between runs, beside the window-state plugin's own file in the app's config
//! folder, `uk.co.adamknowles.idiograph` under Application Support on a Mac and under %APPDATA% on
//! Windows: `window.json`, with three things in it (17 October, the second build).
//!
//! - `local`, the settings the page keeps in the browser, every key that begins `idiograph-`, its
//!   folds, filters, Sift's step and the appearance among them. A browser keeps them for each origin,
//!   the port included, so a window on 8766 while 8765 was taken started them all blank. The window
//!   hands them to every page as it opens (`window.js`), and the page hands back every change, so
//!   they follow the app, whatever port it runs on. Missing until a page first hands its own over.
//! - `place`, where the page was when its window last closed, the place a Restart returns to and the
//!   home screen's own place, which the browser keeps in the window's session alone, so a window that
//!   opens after a relaunch starts there. The page itself still takes a Restart's place only within
//!   ten minutes (see `spotTaken` in static/app.js).
//! - `zoom`, the windows' zoom, one for the app as a browser keeps one for a site.
//! - `updates`, since the fourth build (18 October): what he chose about updates and when the window
//!   last checked, and the version that last ran, for What's new (see update.rs).
//! - `size`, on Linux alone (linuxfix, 9 November 2026): the main window's width and height in logical pixels. The
//!   window-state plugin keeps them in the display's own pixels, which on Linux a change of the display's scale then
//!   read as half or twice the size, so there the window takes this size again once the plugin has put it in place.

use std::fs;
use std::path::PathBuf;
use std::sync::Mutex;

use serde_json::{json, Map, Value};

pub const FILE: &str = "window.json";
/// The page's own keys, the only ones kept.
pub const PREFIX: &str = "idiograph-";
/// The session's two places, the Restart's and the home screen's (static/app.js RETURN_KEY, HOME_KEY).
pub const PLACES: [&str; 2] = ["idiograph-return", "idiograph-home"];
/// The zoom's steps, a browser's own, and the one it starts at.
pub const ZOOMS: [f64; 13] = [0.5, 0.67, 0.75, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0];
pub const ACTUAL: f64 = 1.0;
/// A kept value longer than this is not the page's setting and is left out.
const MOST: usize = 64 * 1024;

pub struct Kept {
    path: PathBuf,
    data: Mutex<Value>,
}

impl Kept {
    /// What `dir` holds, or nothing kept yet when the file is missing or unreadable.
    pub fn load(dir: PathBuf) -> Kept {
        let path = dir.join(FILE);
        let data = fs::read(&path)
            .ok()
            .and_then(|raw| serde_json::from_slice::<Value>(&raw).ok())
            .filter(Value::is_object)
            .unwrap_or_else(|| json!({}));
        Kept { path, data: Mutex::new(data) }
    }

    /// The file written whole to a new name, then put in place, so a quit in the middle never
    /// leaves half of it.
    fn save(&self, data: &Value) {
        if let Some(dir) = self.path.parent() {
            let _ = fs::create_dir_all(dir);
        }
        let fresh = self.path.with_extension("json.new");
        if let Ok(text) = serde_json::to_vec_pretty(data) {
            if fs::write(&fresh, text).is_ok() {
                let _ = fs::rename(&fresh, &self.path);
            }
        }
    }

    /// The page's settings, or None when no page has handed its own over yet.
    pub fn local(&self) -> Option<Map<String, Value>> {
        self.data.lock().unwrap().get("local").and_then(Value::as_object).cloned()
    }

    /// One setting changed, or with None gone.
    pub fn set_local(&self, key: &str, value: Option<&str>) {
        if !key.starts_with(PREFIX) || value.is_some_and(|v| v.len() > MOST) {
            return;
        }
        let mut data = self.data.lock().unwrap();
        let local = data.as_object_mut().unwrap().entry("local").or_insert_with(|| json!({}));
        if !local.is_object() {
            *local = json!({});
        }
        let map = local.as_object_mut().unwrap();
        match value {
            Some(v) => map.insert(key.to_string(), Value::String(v.to_string())),
            None => map.remove(key),
        };
        self.save(&data);
    }

    /// Every setting at once: what a port's storage held when the app first kept them, or none.
    pub fn set_all(&self, all: &Map<String, Value>) {
        let map: Map<String, Value> = all
            .iter()
            .filter(|(k, v)| k.starts_with(PREFIX) && v.as_str().is_some_and(|s| s.len() <= MOST))
            .map(|(k, v)| (k.clone(), v.clone()))
            .collect();
        let mut data = self.data.lock().unwrap();
        data.as_object_mut().unwrap().insert("local".into(), Value::Object(map));
        self.save(&data);
    }

    /// The place a window closed on, its two keys and their values as the session held them.
    pub fn place(&self) -> Map<String, Value> {
        self.data.lock().unwrap().get("place").and_then(Value::as_object).cloned().unwrap_or_default()
    }

    pub fn set_place(&self, place: &Map<String, Value>) {
        let kept: Map<String, Value> = PLACES
            .iter()
            .filter_map(|k| place.get(*k).and_then(Value::as_str).filter(|v| v.len() <= MOST).map(|v| (k.to_string(), json!(v))))
            .collect();
        let mut data = self.data.lock().unwrap();
        data.as_object_mut().unwrap().insert("place".into(), Value::Object(kept));
        self.save(&data);
    }

    /// What the updates keep (update.rs), or nothing yet.
    pub fn updates(&self) -> Map<String, Value> {
        self.data.lock().unwrap().get("updates").and_then(Value::as_object).cloned().unwrap_or_default()
    }

    /// One thing the updates keep, changed.
    pub fn set_update(&self, key: &str, value: Value) {
        let mut data = self.data.lock().unwrap();
        let ups = data.as_object_mut().unwrap().entry("updates").or_insert_with(|| json!({}));
        if !ups.is_object() {
            *ups = json!({});
        }
        ups.as_object_mut().unwrap().insert(key.to_string(), value);
        self.save(&data);
    }

    /// The main window's size as it last closed on Linux, its width and height in logical pixels, the system's own
    /// points, which a change of the display's scale leaves alone (see `fit_size`), or nothing kept yet.
    #[cfg_attr(not(target_os = "linux"), allow(dead_code))]
    pub fn size(&self) -> Option<(f64, f64)> {
        let data = self.data.lock().unwrap();
        let pair = data.get("size")?.as_array()?;
        fit_size(pair.first()?.as_f64()?, pair.get(1)?.as_f64()?)
    }

    /// The main window's size kept, when it is one a window can be and differs from the one kept.
    #[cfg_attr(not(target_os = "linux"), allow(dead_code))]
    pub fn set_size(&self, width: f64, height: f64) {
        let Some((w, h)) = fit_size(width, height) else { return };
        if self.size() == Some((w, h)) {
            return;
        }
        let mut data = self.data.lock().unwrap();
        data.as_object_mut().unwrap().insert("size".into(), json!([w, h]));
        self.save(&data);
    }

    pub fn zoom(&self) -> f64 {
        self.data
            .lock()
            .unwrap()
            .get("zoom")
            .and_then(Value::as_f64)
            .filter(|z| ZOOMS.iter().any(|s| (s - z).abs() < 1e-6))
            .unwrap_or(ACTUAL)
    }

    /// The zoom a step in or out, or back to its actual size, kept, and given back.
    pub fn step_zoom(&self, by: i64) -> f64 {
        let next = step(self.zoom(), by);
        let mut data = self.data.lock().unwrap();
        data.as_object_mut().unwrap().insert("zoom".into(), json!(next));
        self.save(&data);
        next
    }

    /// The zoom set to one of the steps, the nearest to `to`, kept, and given back: Settings' Text size,
    /// Small, Medium or Large (20 October, Settled 12), which the page asks for by its zoom.
    pub fn set_zoom(&self, to: f64) -> f64 {
        let next = nearest(to);
        let mut data = self.data.lock().unwrap();
        data.as_object_mut().unwrap().insert("zoom".into(), json!(next));
        self.save(&data);
        next
    }
}

/// A window's size in logical pixels, whole, when it is one the main window can be: no smaller than its smallest,
/// 720 by 480, and no larger than any display.
pub fn fit_size(width: f64, height: f64) -> Option<(f64, f64)> {
    let ok = |v: f64, least: f64| v.is_finite() && v >= least && v <= 16384.0;
    (ok(width, 720.0) && ok(height, 480.0)).then(|| (width.round(), height.round()))
}

/// The step nearest to `to`, the actual size for a number that is none.
pub fn nearest(to: f64) -> f64 {
    if !to.is_finite() {
        return ACTUAL;
    }
    ZOOMS.iter().copied().fold(ACTUAL, |best, s| if (s - to).abs() < (best - to).abs() { s } else { best })
}

/// The zoom a step in or out from `now`, or back to its actual size for 0, among the steps.
pub fn step(now: f64, by: i64) -> f64 {
    let at = ZOOMS.iter().position(|s| (s - now).abs() < 1e-6).unwrap_or(5) as i64;
    if by == 0 { ACTUAL } else { ZOOMS[(at + by.signum()).clamp(0, ZOOMS.len() as i64 - 1) as usize] }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn keeps_settings_places_and_zoom() {
        let dir = std::env::temp_dir().join(format!("idiograph-keep-{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        let kept = Kept::load(dir.clone());
        assert!(kept.local().is_none());
        kept.set_local("idiograph-shut", Some("[\"sift\"]"));
        kept.set_local("someone-else", Some("x"));
        assert_eq!(kept.step_zoom(1), 1.1);
        let mut place = Map::new();
        place.insert("idiograph-home".into(), json!("demo"));
        place.insert("elsewhere".into(), json!("x"));
        kept.set_place(&place);
        let again = Kept::load(dir.clone());
        let local = again.local().unwrap();
        assert_eq!(local.get("idiograph-shut").and_then(Value::as_str), Some("[\"sift\"]"));
        assert!(local.get("someone-else").is_none());
        assert_eq!(again.zoom(), 1.1);
        assert_eq!(again.step_zoom(0), 1.0);
        assert_eq!(again.place().keys().collect::<Vec<_>>(), vec!["idiograph-home"]);
        again.set_update("check", json!(true));
        again.set_update("ran", json!("0.9.1"));
        let ups = Kept::load(dir.clone()).updates();
        assert_eq!(ups.get("check"), Some(&json!(true)));
        assert_eq!(ups.get("ran").and_then(Value::as_str), Some("0.9.1"));
        again.set_local("idiograph-shut", None);
        assert!(Kept::load(dir.clone()).local().unwrap().is_empty());
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn keeps_the_main_windows_size_in_logical_pixels() {
        assert_eq!(fit_size(1280.4, 800.0), Some((1280.0, 800.0)));
        assert_eq!(fit_size(600.0, 800.0), None);
        assert_eq!(fit_size(1280.0, f64::NAN), None);
        let dir = std::env::temp_dir().join(format!("idiograph-keep-window-{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        let kept = Kept::load(dir.clone());
        assert_eq!(kept.size(), None);
        kept.set_size(1440.0, 900.0);
        kept.set_size(100.0, 100.0);
        assert_eq!(Kept::load(dir.clone()).size(), Some((1440.0, 900.0)));
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn steps_a_zoom_of_its_own() {
        assert_eq!(step(1.0, 1), 1.1);
        assert_eq!(step(1.1, -1), 1.0);
        assert_eq!(step(3.0, 1), 3.0);
        assert_eq!(step(0.5, -1), 0.5);
        assert_eq!(step(2.0, 0), 1.0);
        assert_eq!(step(1.23, 1), 1.1);
    }

    #[test]
    fn sets_a_text_size_kept_for_the_next_run() {
        assert_eq!(nearest(1.25), 1.25);
        assert_eq!(nearest(0.9), 0.9);
        assert_eq!(nearest(1.2), 1.25);
        assert_eq!(nearest(f64::NAN), 1.0);
        let dir = std::env::temp_dir().join(format!("idiograph-keep-size-{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        let kept = Kept::load(dir.clone());
        assert_eq!(kept.set_zoom(1.25), 1.25);
        assert_eq!(Kept::load(dir.clone()).zoom(), 1.25);
        assert_eq!(Kept::load(dir.clone()).step_zoom(-1), 1.1);
        let _ = fs::remove_dir_all(&dir);
    }
}
