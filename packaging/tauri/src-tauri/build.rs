// The window's commands, named so the page on 127.0.0.1 may call them (capabilities/page.json):
// `print`, which the page's window.print calls on a Mac, `new_window`, which its Ctrl+N calls,
// `save_download`, which a download calls with the file's name and bytes, and since the second build
// (17 October) `pick` for Choose, `keep` for the page's settings, `recent` for Open Recent, `zoom`
// for Cmd or Ctrl with 0, + and -, `edit` for the Mac's Undo and Redo in a field, and `closing`, the
// page's answer as its window closes (see window.js), and since the fourth build (18 October) `updates`,
// Idiograph's own updates and What's new (src/update.rs), and since 21 October `save_path`, the save
// panel alone, for Send, whose file the server writes itself (Export as PDF's `save_pdf` and Save as an
// image's `save_png` went on 9 November 2026, typst5, when the server came to make both with Typst),
// and since 4 November `project_now`, whether a project with a history is open, for File, Project History.
fn main() {
    println!("cargo:rerun-if-changed=../window.js");
    // and since 6 November (fileassoc) `opened`, the shared copies the app was asked to open, which the page takes
    // (src/opening.rs), and since 9 November (linuxfix4) `announce`, the line at the foot said to Orca on Linux, and
    // (removefix) `confirm`, a line to confirm in the window's own message box, as the Mac's web view shows none
    tauri_build::try_build(
        tauri_build::Attributes::new().app_manifest(
            tauri_build::AppManifest::new().commands(&["print", "new_window", "save_download", "save_path", "pick", "confirm", "opened", "keep", "recent", "project_now", "zoom", "edit", "announce", "closing", "updates"]),
        ),
    )
    .expect("the window's build");
}
