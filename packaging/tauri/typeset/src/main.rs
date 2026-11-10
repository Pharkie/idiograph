//! Idiograph's typesetter (typst1, 9 November 2026): one Typst template, its data and the app's own fonts made
//! into a PDF or one PNG a page, by the Typst version typst-py carries, so the frozen app makes the pages a run
//! from source makes. `family/typeset.py` runs it from beside the frozen server.
//!
//!     idiograph-typeset --root <folder> --main <file.typ> --fonts <folder> [--format pdf|png] [--ppi 144]
//!     idiograph-typeset --version
//!
//! The data comes on the standard input, its whole text given to the template as the input `data`, so no file is
//! left behind. Only the fonts in `--fonts` are used: no system font and no font of Typst's own, so the pages are
//! the same on every computer. A file the template reads must be under `--root`, and there are no packages.
//! The PDF goes to the standard output as it is. PNGs go there one after another, each its length as eight bytes,
//! big end first, then its bytes. On failure the exit is not zero and Typst's own diagnostics go to the standard
//! error, one a line, with the file, line and column where it has them.

use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::process::ExitCode;
use std::time::{SystemTime, UNIX_EPOCH};

use typst::diag::{FileError, FileResult, Severity, SourceDiagnostic};
use typst::foundations::{Bytes, Datetime, Dict, Duration, IntoValue};
use typst::syntax::{DiagSpan, FileId, RootedPath, Source, VirtualPath, VirtualRoot};
use typst::text::{Font, FontBook};
use typst::utils::LazyHash;
use typst::{Library, LibraryExt, World, WorldExt};
use typst_layout::PagedDocument;

/// The Typst version the crates are pinned to (Cargo.toml), said by `--version`.
const TYPST: &str = "0.15.1";

struct Page {
    root: PathBuf,
    main: FileId,
    library: LazyHash<Library>,
    book: LazyHash<FontBook>,
    fonts: Vec<Font>,
}

impl Page {
    fn new(root: &Path, main: &str, fonts: &Path, data: String) -> Result<Self, String> {
        let mut found = Vec::new();
        let mut names: Vec<PathBuf> = std::fs::read_dir(fonts)
            .map_err(|e| format!("the fonts folder {} cannot be read: {e}", fonts.display()))?
            .filter_map(|entry| entry.ok().map(|e| e.path()))
            .filter(|p| p.extension().map_or(false, |e| e.eq_ignore_ascii_case("ttf") || e.eq_ignore_ascii_case("otf")))
            .collect();
        // a fixed order, so the same folder makes the same book on every system
        names.sort();
        for path in names {
            let bytes = std::fs::read(&path).map_err(|e| format!("{} cannot be read: {e}", path.display()))?;
            found.extend(Font::iter(Bytes::new(bytes)));
        }
        if found.is_empty() {
            return Err(format!("no font in {}", fonts.display()));
        }
        let vpath = VirtualPath::new(main).map_err(|e| format!("{main} is not a file under the root: {e}"))?;
        let mut inputs = Dict::new();
        inputs.insert("data".into(), data.into_value());
        Ok(Page {
            root: root.to_path_buf(),
            main: FileId::new(RootedPath::new(VirtualRoot::Project, vpath)),
            library: LazyHash::new(Library::builder().with_inputs(inputs).build()),
            book: LazyHash::new(FontBook::from_fonts(&found)),
            fonts: found,
        })
    }

    fn read(&self, id: FileId) -> FileResult<Vec<u8>> {
        if !matches!(id.get().root(), VirtualRoot::Project) {
            return Err(FileError::AccessDenied);
        }
        let path = id.get().vpath().realize(&self.root).map_err(|_| FileError::AccessDenied)?;
        std::fs::read(&path).map_err(|e| FileError::from_io(e, &path))
    }

    /// Where a diagnostic points, `file:line:column`, or empty when it points nowhere.
    fn place(&self, span: DiagSpan) -> String {
        let Some(id) = span.id() else { return String::new() };
        let file = id.get().vpath().get_without_slash().to_string();
        let at = self.range(span).and_then(|range| {
            self.source(id).ok().and_then(|s| s.lines().byte_to_line_column(range.start))
        });
        match at {
            Some((line, col)) => format!("{file}:{}:{}: ", line + 1, col + 1),
            None => format!("{file}: "),
        }
    }

    fn said(&self, diag: &SourceDiagnostic) -> String {
        let kind = if diag.severity == Severity::Error { "error" } else { "warning" };
        let mut out = format!("{kind}: {}{}", self.place(diag.span), diag.message);
        for hint in &diag.hints {
            out.push_str(&format!("\n  hint: {}", hint.v));
        }
        out
    }
}

impl World for Page {
    fn library(&self) -> &LazyHash<Library> { &self.library }
    fn book(&self) -> &LazyHash<FontBook> { &self.book }
    fn main(&self) -> FileId { self.main }
    fn source(&self, id: FileId) -> FileResult<Source> {
        let text = String::from_utf8(self.read(id)?).map_err(|_| FileError::InvalidUtf8)?;
        Ok(Source::new(id, text))
    }
    fn file(&self, id: FileId) -> FileResult<Bytes> { Ok(Bytes::new(self.read(id)?)) }
    fn font(&self, index: usize) -> Option<Font> { self.fonts.get(index).cloned() }
    fn today(&self, offset: Option<Duration>) -> Option<Datetime> {
        // the day by the clock, in UTC or at the offset asked, without a time-zone table
        let secs = SystemTime::now().duration_since(UNIX_EPOCH).ok()?.as_secs() as i64
            + offset.map_or(0, |d| d.seconds() as i64);
        let (y, m, d) = civil(secs.div_euclid(86_400));
        Datetime::from_ymd(y, m, d)
    }
}

/// The calendar day of a count of days since 1970-01-01 (Howard Hinnant's civil_from_days).
fn civil(days: i64) -> (i32, u8, u8) {
    let z = days + 719_468;
    let era = z.div_euclid(146_097);
    let doe = z - era * 146_097;
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = (doy - (153 * mp + 2) / 5 + 1) as u8;
    let m = if mp < 10 { mp + 3 } else { mp - 9 } as u8;
    let y = (yoe + era * 400 + if m <= 2 { 1 } else { 0 }) as i32;
    (y, m, d)
}

struct Args {
    root: PathBuf,
    main: String,
    fonts: PathBuf,
    png: bool,
    ppi: f64,
}

fn args() -> Result<Option<Args>, String> {
    let mut it = std::env::args().skip(1);
    let (mut root, mut main, mut fonts, mut png, mut ppi) = (None, None, None, false, 144.0);
    while let Some(a) = it.next() {
        let mut value = || it.next().ok_or_else(|| format!("{a} needs a value"));
        match a.as_str() {
            "--version" => return Ok(None),
            "--root" => root = Some(PathBuf::from(value()?)),
            "--main" => main = Some(value()?),
            "--fonts" => fonts = Some(PathBuf::from(value()?)),
            "--format" => png = match value()?.as_str() {
                "pdf" => false,
                "png" => true,
                other => return Err(format!("--format is pdf or png, not {other}")),
            },
            "--ppi" => {
                ppi = value()?.parse().map_err(|_| "--ppi takes a number".to_string())?;
                if !(ppi > 0.0 && ppi <= 2400.0) {
                    return Err("--ppi is above 0 and at most 2400".into());
                }
            }
            other => return Err(format!("unknown argument {other}")),
        }
    }
    Ok(Some(Args {
        root: root.ok_or("--root is needed")?,
        main: main.ok_or("--main is needed")?,
        fonts: fonts.ok_or("--fonts is needed")?,
        png,
        ppi,
    }))
}

fn run() -> Result<(), String> {
    let Some(a) = args()? else {
        println!("idiograph-typeset, Typst {TYPST}");
        return Ok(());
    };
    let mut data = String::new();
    std::io::stdin().read_to_string(&mut data).map_err(|e| format!("the data on the standard input is not text: {e}"))?;
    let world = Page::new(&a.root, &a.main, &a.fonts, data)?;
    let compiled = typst::compile::<PagedDocument>(&world);
    let doc = match compiled.output {
        Ok(doc) => doc,
        Err(errors) => {
            let mut lines: Vec<String> = errors.iter().map(|e| world.said(e)).collect();
            lines.extend(compiled.warnings.iter().map(|w| world.said(w)));
            return Err(lines.join("\n"));
        }
    };
    for w in compiled.warnings.iter() {
        eprintln!("{}", world.said(w));
    }
    let mut out = std::io::stdout().lock();
    if a.png {
        let opts = typst_render::RenderOptions { pixel_per_pt: (a.ppi / 72.0).into(), ..Default::default() };
        for page in doc.pages() {
            let png = typst_render::render(page, &opts).encode_png().map_err(|e| format!("a page's PNG: {e}"))?;
            out.write_all(&(png.len() as u64).to_be_bytes()).map_err(|e| e.to_string())?;
            out.write_all(&png).map_err(|e| e.to_string())?;
        }
    } else {
        let pdf = typst_pdf::pdf(&doc, &typst_pdf::PdfOptions::default()).map_err(|errors| {
            errors.iter().map(|e| world.said(e)).collect::<Vec<_>>().join("\n")
        })?;
        out.write_all(&pdf).map_err(|e| e.to_string())?;
    }
    out.flush().map_err(|e| e.to_string())
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(said) => {
            eprintln!("{said}");
            ExitCode::FAILURE
        }
    }
}
