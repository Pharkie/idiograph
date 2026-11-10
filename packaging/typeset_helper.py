"""The typesetter every build puts beside the frozen server (typst1, 9 November 2026): `idiograph-typeset`, the small
Rust program in `packaging/tauri/typeset/` that makes every PDF and picture of a print view with Typst, its crates
pinned with `=` to the Typst version typst-py carries (`family/typeset.py`, which finds it from `sys.executable`).

`build_mac.py`, `build_windows.py` and `build_linux.py` call `build` once the server is frozen, with Tauri's own
release settings and `--locked`, so the crates are Cargo.lock's, and `place` copies it into the frozen folder,
which each system's bundle carries whole beside the window: `Contents/Resources/server/` on a Mac, `server\\` in the
Windows install folder, `<prefix>/lib/<Name>/server/` in the .deb and the AppImage. Cargo's work goes in the
build's own folder, never the checkout. `check` typesets a one-line page with the app's own fonts, so a typesetter
that does not run stops the build. The standard library only.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent
CRATE = HERE / "tauri" / "typeset"
NAME = "idiograph-typeset"
# the one-line page `check` typesets, in the app's own text font
PAGE = '#set page(width: 120mm, height: auto, margin: 10mm)\n#set text(font: "Charis SIL")\n#sys.inputs.data\n'
LINE = "Idiograph typesets"


def say(line: str) -> None:
    print(line, flush=True)


def exe_name(windows: bool | None = None) -> str:
    """The typesetter's file name, with `.exe` on Windows."""
    windows = sys.platform == "win32" if windows is None else windows
    return NAME + (".exe" if windows else "")


def build_command(target_dir: Path, target: str | None = None) -> list[str]:
    """Cargo's build of the typesetter, release and locked to Cargo.lock, for `target` or this machine's own."""
    cmd = ["cargo", "build", "--release", "--locked", "--manifest-path", str(CRATE / "Cargo.toml"),
           "--target-dir", str(target_dir)]
    return cmd + (["--target", target] if target else [])


def built_at(target_dir: Path, target: str | None = None, windows: bool | None = None) -> Path:
    """Where cargo leaves the typesetter."""
    base = target_dir / target if target else target_dir
    return base / "release" / exe_name(windows)


def build(build_dir: Path, target: str | None = None, env: dict | None = None) -> Path:
    """The typesetter built into `build_dir/typeset-target`, its path answered."""
    target_dir = build_dir / "typeset-target"
    say(f"Building the typesetter, {NAME}, with cargo")
    subprocess.run(build_command(target_dir, target), check=True, env=dict(os.environ if env is None else env))
    made = built_at(target_dir, target)
    if not made.is_file():
        raise SystemExit(f"cargo built no {made.name} in {made.parent}.")
    return made


def place(made: Path, frozen: Path) -> Path:
    """The typesetter copied into the frozen server's folder, beside its executable, runnable."""
    target = frozen / made.name
    shutil.copyfile(made, target)
    target.chmod(0o755)
    return target


def sign_mac(helper: Path, identity: str | None) -> None:
    """On a Mac, the typesetter signed as PyInstaller signs the server's binaries: with the Developer ID and the
    hardened runtime when there is one, else ad hoc."""
    if identity:
        cmd = ["codesign", "--force", "--timestamp", "--options", "runtime", "--sign", identity, str(helper)]
    else:
        cmd = ["codesign", "--force", "--sign", "-", str(helper)]
    subprocess.run(cmd, check=True, capture_output=True)


def fonts_in(frozen: Path) -> Path:
    """The app's fonts in a frozen folder: PyInstaller's data under `_internal/`, or at its top in an older layout."""
    for base in (frozen / "_internal", frozen):
        if (base / "static" / "fonts").is_dir():
            return base / "static" / "fonts"
    return frozen / "_internal" / "static" / "fonts"


def check(helper: Path, fonts: Path, timeout: float = 60) -> int:
    """The typesetter run on a one-line page with `fonts`, the bundle's own: a PDF must come back. Answers its size."""
    with tempfile.TemporaryDirectory(prefix="idiograph-typeset-") as tmp:
        (Path(tmp) / "line.typ").write_text(PAGE, encoding="utf-8")
        done = subprocess.run([str(helper), "--root", tmp, "--main", "line.typ", "--fonts", str(fonts), "--format", "pdf"],
                              input=LINE.encode("utf-8"), capture_output=True, timeout=timeout)
    if done.returncode != 0 or not done.stdout.startswith(b"%PDF-"):
        said = done.stderr.decode("utf-8", errors="replace").strip()
        raise SystemExit(f"The typesetter did not typeset a line, exit {done.returncode}:\n{said[-2000:]}")
    return len(done.stdout)
