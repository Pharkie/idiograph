//! Which of the family's three apps this window is, Idiograph, Sift or Trace (20 October 2026, the
//! three-app split's build 6), as `app_identity.py` decides it for the server: by the window's own
//! executable's name, which `bundle.py` sets through tauri.conf.json's `mainBinaryName`. `Sift` and
//! `Sift Test` are Sift, `Trace` and `Trace Test` Trace, and any other name, `Idiograph`, `Idiograph Test`
//! and a check's own, Idiograph. Each app has its name, which its frozen server, its logs folder and
//! its words carry, and its port.

use std::env;
use std::path::Path;
use std::sync::OnceLock;

/// One of the three apps: its name and the port its server tries first.
#[derive(Debug, PartialEq, Eq)]
pub struct App {
    pub name: &'static str,
    pub port: u16,
}

/// The family, Idiograph first, as app_identity.py has it.
pub const APPS: [App; 3] = [
    App { name: "Idiograph", port: 8765 },
    App { name: "Sift", port: 8766 },
    App { name: "Trace", port: 8767 },
];

/// The app an executable's name is: its first word, without `.exe` or `-console`, matched without
/// regard to case, Idiograph when it is none of the three.
pub fn from_name(name: &str) -> &'static App {
    let stem = name.strip_suffix(".exe").unwrap_or(name);
    let first = stem.split(' ').next().unwrap_or("");
    let first = first.strip_suffix("-console").unwrap_or(first);
    APPS.iter().find(|a| a.name.eq_ignore_ascii_case(first)).unwrap_or(&APPS[0])
}

/// This window's app, by its own executable's name, decided once.
pub fn this() -> &'static App {
    static THIS: OnceLock<&'static App> = OnceLock::new();
    THIS.get_or_init(|| {
        let exe = env::current_exe().unwrap_or_default();
        from_name(exe.file_name().and_then(|n| n.to_str()).unwrap_or(""))
    })
}

/// This app's name, `Sift` for Sift.
pub fn name() -> &'static str {
    this().name
}

/// Words written for Idiograph said for this app, `Quit Idiograph` as `Quit Sift` in Sift, so each
/// line stays written once.
pub fn named(text: &str) -> String {
    named_for(this(), text)
}

pub fn named_for(app: &App, text: &str) -> String {
    text.replace("Idiograph", app.name)
}

/// The frozen server's executable in its folder, the app's own name: `Sift`, or `Sift.exe` and its
/// console twin `Sift-console.exe` on Windows.
pub fn server_exe(dir: &Path, console: bool) -> std::path::PathBuf {
    let name = this().name;
    if cfg!(windows) {
        dir.join(if console { format!("{name}-console.exe") } else { format!("{name}.exe") })
    } else {
        dir.join(name)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn each_name_is_its_app() {
        assert_eq!(from_name("Sift").name, "Sift");
        assert_eq!(from_name("Sift Test").port, 8766);
        assert_eq!(from_name("Trace.exe").name, "Trace");
        assert_eq!(from_name("Trace-console.exe").name, "Trace");
        assert_eq!(from_name("Idiograph Test").name, "Idiograph");
        assert_eq!(from_name("idiograph-0123abcd").name, "Idiograph");
        assert_eq!(from_name("").port, 8765);
        assert_eq!(named_for(&APPS[1], "Quit Idiograph"), "Quit Sift");
    }
}
