"""Area 346: the app's folders on Linux and Show in Finder there (linux1, 8 November 2026, build 1 of the Linux plan).
On Linux the data, logs, config and cache folders follow XDG, each by its variable with its usual default, and a
relative value is ignored. The Mac and Windows folders are as they were. A source user's folders in the Mac's layout
under ~/Library are moved to the new places once, whole and never copied, and never onto a folder that already holds
files. Show in Finder runs xdg-open on Linux, open -R on a Mac and explorer on Windows. All on a faked platform and a
made-up home folder. Nothing here uses a participant's words."""
from __future__ import annotations

from pathlib import Path

from .support import check


def test_linux_folders(scratch: Path):
    print("\n346. The app's folders on Linux by XDG, the one-time move, and Show in Finder per system (linux1)")
    import app_folders as af
    import server as server_mod
    import idiograph_routes as routes

    home = Path("/home/ann")
    lin = af.folders("linux", home)
    check("346: Linux with no XDG variables uses the standard defaults under home",
          lin["data"] == home / ".local/share/Idiograph" and lin["logs"] == home / ".local/state/Idiograph/logs"
          and lin["config"] == home / ".config/Idiograph" and lin["cache"] == home / ".cache/Idiograph"
          and lin["trace"] == Path("/tmp/idiograph-launch.log"), str(lin))
    env = {"XDG_DATA_HOME": "/srv/d", "XDG_STATE_HOME": "/srv/s", "XDG_CONFIG_HOME": "/srv/c", "XDG_CACHE_HOME": "/srv/k"}
    lin = af.folders("linux", home, env)
    check("346: each XDG variable moves its own folder",
          lin["data"] == Path("/srv/d/Idiograph") and lin["logs"] == Path("/srv/s/Idiograph/logs")
          and lin["config"] == Path("/srv/c/Idiograph") and lin["cache"] == Path("/srv/k/Idiograph"), str(lin))
    lin = af.folders("linux", home, {"XDG_DATA_HOME": "relative/dir", "XDG_STATE_HOME": ""})
    check("346: a relative or empty variable is ignored", lin["data"] == home / ".local/share/Idiograph"
          and lin["logs"] == home / ".local/state/Idiograph/logs", str(lin))
    sift = af.folders("linux", home, app="sift")
    check("346: Sift's Linux folders are its own", sift["data"] == home / ".local/share/Sift"
          and sift["trace"] == Path("/tmp/sift-launch.log"), str(sift))
    mac = af.folders("darwin", home)
    win = af.folders("win32", home)
    check("346: the Mac's folders are as they were", mac == {"data": home / "Library/Application Support/Idiograph",
          "logs": home / "Library/Logs/Idiograph", "trace": Path("/tmp/idiograph-launch.log")}, str(mac))
    check("346: Windows's folders are as they were", win["data"] == home / "AppData/Roaming/Idiograph"
          and win["logs"] == home / "AppData/Local/Idiograph/Logs" and "config" not in win, str(win))

    # the one-time move
    h = scratch / "linux_home"
    old_data = h / "Library/Application Support/Idiograph"
    old_logs = h / "Library/Logs/Idiograph"
    old_data.mkdir(parents=True)
    old_logs.mkdir(parents=True)
    (old_data / "config.json").write_text('{"a": 1}', encoding="utf-8", newline="")
    (old_data / "demo").mkdir()
    (old_data / "demo" / "x.txt").write_text("x", encoding="utf-8", newline="")
    (old_logs / "idiograph.log").write_text("log", encoding="utf-8", newline="")
    check("346: the move does nothing on a Mac or Windows",
          af.move_legacy("darwin", h) == [] and af.move_legacy("win32", h) == [] and old_data.is_dir())
    moved = af.move_legacy("linux", h)
    new = af.folders("linux", h)
    check("346: the move takes both folders whole to the XDG places and leaves nothing behind",
          sorted(moved) == sorted([new["data"], new["logs"]])
          and (new["data"] / "config.json").read_text(encoding="utf-8") == '{"a": 1}' and (new["data"] / "demo/x.txt").read_text(encoding="utf-8") == "x"
          and (new["logs"] / "idiograph.log").read_text(encoding="utf-8") == "log"
          and not old_data.exists() and not old_logs.exists() and not (h / "Library").exists(), str(moved))
    (new["data"] / "config.json").write_text('{"a": 2}', encoding="utf-8", newline="")
    check("346: a second call finds nothing to move and keeps the newer file",
          af.move_legacy("linux", h) == [] and (new["data"] / "config.json").read_text(encoding="utf-8") == '{"a": 2}')

    # never over newer data
    h2 = scratch / "linux_home2"
    old = h2 / "Library/Application Support/Idiograph"
    old.mkdir(parents=True)
    (old / "config.json").write_text("old", encoding="utf-8", newline="")
    new2 = af.folders("linux", h2)["data"]
    new2.mkdir(parents=True)
    (new2 / "config.json").write_text("newer", encoding="utf-8", newline="")
    check("346: a data folder already holding files is never moved onto",
          af.move_legacy("linux", h2) == [] and (new2 / "config.json").read_text(encoding="utf-8") == "newer"
          and (old / "config.json").read_text(encoding="utf-8") == "old")
    h3 = scratch / "linux_home3"
    old = h3 / "Library/Application Support/Idiograph"
    old.mkdir(parents=True)
    (old / "state.json").write_text("s", encoding="utf-8", newline="")
    new3 = af.folders("linux", h3)["data"]
    new3.mkdir(parents=True)
    check("346: an empty folder in the way is replaced by the move",
          af.move_legacy("linux", h3) == [new3] and (new3 / "state.json").exists())
    h4 = scratch / "linux_home4"
    old = h4 / "Library/Application Support/Idiograph"
    old.mkdir(parents=True)
    (old / "state.json").write_text("s", encoding="utf-8", newline="")
    xdg = {"XDG_DATA_HOME": str(scratch / "xdg_data")}
    check("346: with XDG_DATA_HOME set the move goes there",
          af.move_legacy("linux", h4, xdg) == [scratch / "xdg_data" / "Idiograph"]
          and (scratch / "xdg_data" / "Idiograph" / "state.json").exists())

    # Show in Finder per system
    ran = []
    folder = Path("/home/ann/Studies/Night fishing")
    real_run = server_mod.subprocess.run
    real_platform, real_srv = server_mod.PLATFORM, routes.srv.PLATFORM
    real_reveal = routes.REVEAL
    got = {}
    try:
        server_mod.subprocess.run = lambda *a, **k: ran.append(a[0])
        routes.REVEAL = lambda f: ran.append(["open", "-R", str(f)])
        for plat in ("linux", "darwin", "win32"):
            server_mod.PLATFORM = routes.srv.PLATFORM = plat
            ran.clear()
            server_mod.show_in_folder(folder)
            routes.show_folder(folder)
            got[plat] = list(ran)
        server_mod.PLATFORM = routes.srv.PLATFORM = "linux2"
        ran.clear()
        server_mod.show_in_folder(folder)
        got["linux2"] = list(ran)
        server_mod.PLATFORM = routes.srv.PLATFORM = "freebsd"
        try:
            server_mod.reveal_folder(scratch)
            got["freebsd"] = "allowed"
        except Exception:
            got["freebsd"] = "refused"
        server_mod.PLATFORM = routes.srv.PLATFORM = "linux"
        ran.clear()
        server_mod.reveal_folder(scratch)
        got["revealed"] = list(ran)
    finally:
        server_mod.subprocess.run = real_run
        routes.REVEAL = real_reveal
        server_mod.PLATFORM, routes.srv.PLATFORM = real_platform, real_srv
    x = ["xdg-open", str(folder)]
    check("346: Linux opens the folder with xdg-open, in both places that ask", got["linux"] == [x, x], str(got["linux"]))
    check("346: a Mac still runs open -R", got["darwin"][0] == ["open", "-R", str(folder)], str(got["darwin"]))
    check("346: Windows still runs explorer /select,", got["win32"] == [f'explorer /select,"{folder}"'] * 2, str(got["win32"]))
    check("346: a platform named linux2 counts as Linux", got["linux2"] == [x], str(got["linux2"]))
    check("346: Show in Finder is allowed on Linux and still refused on another system",
          got["revealed"] == [["xdg-open", str(scratch)]] and got["freebsd"] == "refused", str(got))
