"""A project's folder moved to the system's own Trash (removetrash, 10 November 2026, Adam: after removing a
duplicate shared copy, "there should be a possibility ... I would have chosen to delete files and folders").

Remove from Idiograph, from Sift and from Trace asks with a tick, off to start, to move the project's folder to the
Trash as well: the Bin on a Mac, the Recycle Bin on Windows, the freedesktop Trash on Linux. Never a delete: each
system's own way of putting a folder in its Trash, from the standard library alone, so it can be taken out again.

`guard` refuses, with nothing moved, a folder that is not exactly the project's own: not there, a link, a drive's
top folder, the home folder or one holding it, a cloud drive's top folder, a standard folder of the home (Desktop,
Documents, Downloads), one holding the app's own files, its data or settings, one holding another project, a project
being written now (a lock held inside it) and a project open in another window (`server.open_elsewhere`). `move`
puts it in the Trash through the system and answers where it went, and `TRASH` is the name the suite stands in for,
so no check ever reaches the real Trash. `record` keeps a line for each removal in the app's own record beside its
settings, never in a project.
"""
from __future__ import annotations

import ctypes
import ctypes.util
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import i18n
import locks
from errors import WorkbookError

PLATFORM = sys.platform
# the standard folders of the home a project never is, each by its name under the home
HOME_FOLDERS = ("Desktop", "Documents", "Downloads")
# the record of removals beside the settings file, `config.removed.jsonl` beside config.json
RECORD_SUFFIX = ".removed.jsonl"


def where_key(platform: str | None = None) -> str:
    """The catalogue's key of the Trash's own name on this system."""
    platform = platform or PLATFORM
    return ("trash.where.mac" if platform == "darwin" else "trash.where.windows" if platform == "win32"
            else "trash.where.linux")


def where() -> str:
    """The Trash's own name on this system, in the run's language: the Bin, the Recycle Bin, the Rubbish Bin."""
    return i18n.t(where_key())


def refused(said: str) -> WorkbookError:
    """A refusal of the Trash, its line said already in the run's language, nothing moved."""
    return WorkbookError(said)


# ------------------------------------------------------------------ what is never the project's own folder

def cloud_tops(home: Path) -> list[Path]:
    """The top folders of the cloud drives on this computer: iCloud Drive's, OneDrive's, and every folder the Mac's
    File Provider keeps under CloudStorage (OneDrive, Dropbox, Google Drive and the like)."""
    out = [home / "Library" / "Mobile Documents", home / "Library" / "Mobile Documents" / "com~apple~CloudDocs",
           home / "Library" / "CloudStorage", home / "iCloudDrive"]
    store = home / "Library" / "CloudStorage"
    try:
        out += [p for p in store.iterdir() if p.is_dir()]
    except OSError:
        pass
    for name in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        if os.environ.get(name):
            out.append(Path(os.environ[name]))
    try:
        out += [p for p in home.iterdir() if p.is_dir() and p.name.startswith("OneDrive")]
    except OSError:
        pass
    return out


def resolved(p) -> Path | None:
    try:
        return Path(p).expanduser().resolve()
    except (OSError, RuntimeError):
        return None


def under(p: Path, root: Path) -> bool:
    """Whether `p` is `root` or sits anywhere under it, both resolved."""
    try:
        p.relative_to(root)
    except ValueError:
        return False
    return True


def guard(folder, *, name: str, keep=(), others=(), home: Path | None = None) -> Path:
    """The project's folder, resolved, once nothing refuses it: the folder the list names, `folder`, there and not a
    link, never a drive's top folder, the home folder or one holding it, a cloud drive's top folder or a standard
    folder of the home, never one holding any of `keep`, the app's own files, its data and its settings, and never
    one holding any of `others`, every other project the app lists. Each refusal is a plain line, nothing moved."""
    given = Path(folder).expanduser()
    if not given.exists():
        raise refused(i18n.t("trash.gone", where=where()))
    if given.is_symlink():
        raise refused(i18n.t("trash.link", where=where()))
    chosen = resolved(given)
    if chosen is None or not chosen.is_dir():
        raise refused(i18n.t("trash.gone", where=where()))
    if chosen.parent == chosen or Path(chosen.anchor) == chosen:
        raise refused(i18n.t("trash.drive", where=where()))
    home = resolved(home or Path.home())
    if home is not None and under(home, chosen):
        raise refused(i18n.t("trash.home", where=where()))
    if home is not None and any(chosen == resolved(home / f) for f in HOME_FOLDERS):
        raise refused(i18n.t("trash.home", where=where()))
    if home is not None and any(chosen == resolved(c) for c in cloud_tops(home)):
        raise refused(i18n.t("trash.cloud", where=where()))
    for k in keep:
        r = resolved(k)
        if r is not None and under(r, chosen):
            raise refused(i18n.t("trash.holds_app", where=where()))
    for other_name, other in others:
        r = resolved(other)
        if r is not None and under(r, chosen) and r != chosen:
            raise refused(i18n.t("trash.holds_project", where=where(), other=other_name))
    if busy(chosen):
        raise refused(i18n.t("trash.busy", where=where(), name=name))
    return chosen


def busy(folder: Path) -> bool:
    """Whether a writer holds a lock inside the project's folder now, the app's own or an agent's."""
    for here, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if not d.startswith(".") or d == ".idiograph"]
        for f in files:
            if f.endswith(".lock") and locks.is_held(Path(here) / f):
                return True
    return False


# ------------------------------------------------------------------ the move, through each system's own way

def move(folder: Path) -> str:
    """The folder put in the system's Trash, never deleted. Answers where it went, the Trash's own name. A move
    the system refuses raises its reason, and the folder stays where it was."""
    if PLATFORM == "darwin":
        _mac(folder)
    elif PLATFORM == "win32":
        _windows(folder)
    else:
        _freedesktop(folder)
    return where()


TRASH = move           # a name here, so the suite stands in for the real Trash with a folder of its own


def _mac(folder: Path) -> None:
    """NSFileManager's trashItemAtURL, through the Objective-C runtime: the Finder's own Move to Bin, with Put Back."""
    objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
    ctypes.cdll.LoadLibrary("/System/Library/Frameworks/Foundation.framework/Foundation")
    objc.objc_getClass.restype = ctypes.c_void_p
    objc.objc_getClass.argtypes = [ctypes.c_char_p]
    objc.sel_registerName.restype = ctypes.c_void_p
    objc.sel_registerName.argtypes = [ctypes.c_char_p]
    objc.objc_autoreleasePoolPush.restype = ctypes.c_void_p
    objc.objc_autoreleasePoolPop.argtypes = [ctypes.c_void_p]
    send = ctypes.cast(objc.objc_msgSend, ctypes.c_void_p).value
    cls, sel = objc.objc_getClass, objc.sel_registerName
    vp = ctypes.c_void_p

    def call(restype, *argtypes):
        return ctypes.CFUNCTYPE(restype, vp, vp, *argtypes)(send)

    pool = objc.objc_autoreleasePoolPush()
    try:
        text = call(vp, ctypes.c_char_p)(cls(b"NSString"), sel(b"stringWithUTF8String:"), str(folder).encode("utf-8"))
        url = call(vp, vp)(cls(b"NSURL"), sel(b"fileURLWithPath:"), text)
        manager = call(vp)(cls(b"NSFileManager"), sel(b"defaultManager"))
        error = vp(None)
        ok = call(ctypes.c_bool, vp, vp, ctypes.POINTER(vp))(
            manager, sel(b"trashItemAtURL:resultingItemURL:error:"), url, None, ctypes.byref(error))
        if not ok:
            why = ""
            if error.value:
                said = call(vp)(error.value, sel(b"localizedDescription"))
                raw = call(ctypes.c_char_p)(said, sel(b"UTF8String")) if said else None
                why = raw.decode("utf-8", "replace") if raw else ""
            raise OSError(why or "the Finder did not move it")
    finally:
        objc.objc_autoreleasePoolPop(pool)


def _windows(folder: Path) -> None:
    """SHFileOperationW with FOF_ALLOWUNDO: Explorer's own Delete, to the Recycle Bin. A folder on a drive that has
    no Recycle Bin, a network or a removable one, is refused first, since Windows would delete it outright there."""
    from ctypes import wintypes
    kernel = ctypes.windll.kernel32
    drive = Path(folder).anchor
    if kernel.GetDriveTypeW(ctypes.c_wchar_p(drive)) != 3:          # DRIVE_FIXED
        raise refused(i18n.t("trash.no_bin", where=where()))

    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [("hwnd", wintypes.HWND), ("wFunc", wintypes.UINT), ("pFrom", wintypes.LPCWSTR),
                    ("pTo", wintypes.LPCWSTR), ("fFlags", ctypes.c_uint16), ("fAnyOperationsAborted", wintypes.BOOL),
                    ("hNameMappings", ctypes.c_void_p), ("lpszProgressTitle", wintypes.LPCWSTR)]

    FO_DELETE = 3
    # FOF_SILENT | FOF_NOCONFIRMATION | FOF_ALLOWUNDO | FOF_NOERRORUI | FOF_WANTNUKEWARNING
    flags = 0x0004 | 0x0010 | 0x0040 | 0x0400 | 0x4000
    op = SHFILEOPSTRUCTW(None, FO_DELETE, str(folder) + "\0", None, flags, False, None, None)
    code = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
    if code or op.fAnyOperationsAborted or Path(folder).exists():
        raise OSError(f"Windows did not move it (code {code})")


def _freedesktop(folder: Path, home: Path | None = None) -> None:
    """The freedesktop.org Trash, as GNOME's Files and KDE's Dolphin keep it: the home Trash for a folder on the
    home's own drive, else `.Trash-<uid>` at the top of the folder's own drive, its info file written first and the
    folder renamed into `files`, never copied, so a move across drives is refused rather than half done."""
    home = home or Path.home()
    data = Path(os.environ.get("XDG_DATA_HOME") or home / ".local" / "share")
    folder = Path(folder)
    dev = folder.stat().st_dev
    can = data / "Trash"
    try:
        can.mkdir(parents=True, exist_ok=True)
        same = can.stat().st_dev == dev
    except OSError:
        same = False
    if not same:
        top = folder
        while top.parent != top and top.parent.stat().st_dev == dev:
            top = top.parent
        can = top / f".Trash-{os.getuid()}"
    files, info = can / "files", can / "info"
    for p in (files, info):
        p.mkdir(parents=True, exist_ok=True, mode=0o700)
    base, n = folder.name, 1
    while True:
        name = base if n == 1 else f"{base}.{n}"
        try:
            fd = os.open(info / f"{name}.trashinfo", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            n += 1
            continue
        if (files / name).exists():
            os.close(fd)
            os.unlink(info / f"{name}.trashinfo")
            n += 1
            continue
        break
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("[Trash Info]\nPath={}\nDeletionDate={}\n".format(
            quote(str(folder.resolve()), safe="/"), time.strftime("%Y-%m-%dT%H:%M:%S")))
    try:
        os.rename(folder, files / name)
    except OSError:
        os.unlink(info / f"{name}.trashinfo")
        raise


# ------------------------------------------------------------------ the app's own record

def record_path(config: Path) -> Path:
    """The record of removals beside the settings file: `config.removed.jsonl` beside config.json."""
    config = Path(config)
    return config.with_name(config.stem + RECORD_SUFFIX)


def record(config: Path, app: str, name: str, folder: Path, trashed: bool, by: str = "") -> None:
    """A line in the app's own record of removals: when, the app, the project's name and folder, whether the
    folder went to the Trash, and who asked, the app or an agent by its tool. Never in a project's folder, and a
    record that cannot be written fails nothing."""
    line = {"at": datetime.now().astimezone().isoformat(timespec="seconds"), "app": app, "name": name,
            "folder": str(folder), "trash": bool(trashed), "by": by or "app"}
    try:
        with open(record_path(config), "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(line, ensure_ascii=False) + "\n")
    except OSError:
        pass


def records(config: Path) -> list[dict]:
    """The record of removals, oldest first, each line that reads."""
    out = []
    try:
        text = record_path(config).read_text(encoding="utf-8")
    except OSError:
        return out
    for raw in text.splitlines():
        try:
            out.append(json.loads(raw))
        except ValueError:
            continue
    return out
