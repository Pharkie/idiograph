"""Area 435: another computer with the same project folder open (sharedopen, 20 November 2026, Adam's ruling that
day). While a page is in front of a project the server keeps `.idiograph-open/<id>.json` inside its folder, and the
project's read says which other installs have a file there newer than five minutes (`open_elsewhere`). Two scratch
installs, each its own settings folder and id, one project folder.

What matters: the second install sees the first and never itself; an old file is ignored; a conflict copy of a file
counts once for its owner; the presence folder is no participant, is not in Share a copy, does not stop Remove to
the Trash and is not what Working together walks; a read by the command line writes nothing, and a failure to
write is silent. No check pins the words. Every fixture is invented."""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from .support import check


def test_open_elsewhere(scratch: Path):
    print("\n435. Another computer with the project's folder open: a presence file in a dot-named folder, newer than "
          "five minutes, seen by the other install and never by its own, left out of a shared copy, a participant "
          "and the Trash's guard, read by the command line without writing (sharedopen)")
    import cli
    import idiograph_routes as routes
    import presence
    import project_pack
    import server as server_mod
    import trash

    home = scratch / "open-435"
    shutil.rmtree(home, ignore_errors=True)
    root = home / "Shared project"
    (root / "P1 - Ada").mkdir(parents=True)
    (root / server_mod.PROJECT_FILE).write_text(json.dumps({"name": "Shared project", "agents": {"allowed": True}}), encoding="utf-8")
    (root / "P1 - Ada" / "notes.txt").write_text("one", encoding="utf-8")
    configs = {}
    for who in ("one", "two"):
        folder = home / who
        folder.mkdir()
        (folder / "config.json").write_text(json.dumps({"projects": [{"root": str(root)}]}), encoding="utf-8")
        configs[who] = folder / "config.json"
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, presence.HELD.copy(), presence._ID[:])

    def at(who):
        server_mod.CONFIG_PATH = configs[who]
        server_mod.ROOT_OVERRIDE = None
        presence._ID[0] = presence._ID[1] = None

    def files(folder: Path) -> dict:
        return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}

    try:
        at("one")
        one_id = presence.install_id()
        one_key = presence.key_of(one_id)
        at("two")
        two_id = presence.install_id()
        at("one")
        check("435: each install keeps one id of its own beside its settings, the same every time it is asked",
              one_id and two_id and one_id != two_id and presence.install_id() == one_id
              and (configs["one"].parent / presence.ID_FILE).exists(), f"{one_id} {two_id}")

        # 1. the first install's page is in front of the project: the file is written, and the second sees it
        presence.HELD.clear()
        presence.sync([str(root)], wait=5)
        mine = root / presence.DIR / f"{one_key}.json"
        body = json.loads(mine.read_text(encoding="utf-8")) if mine.exists() else {}
        at("two")
        seen = routes.api_project({"root": str(root)})
        at("one")
        own = routes.api_project({"root": str(root)})
        check("435: a page in front of a project writes this install's file in the project's folder, whole, and the "
              "other install's read of the project names this computer while this install's own read does not",
              body.get("id") == one_key and body.get("name") == presence.computer() and len(seen["open_elsewhere"]) == 1
              and seen["open_elsewhere"][0] == presence.computer() and own["open_elsewhere"] == []
              and not [p for p in (root / presence.DIR).iterdir() if p.name.endswith(".tmp")], json.dumps(seen["open_elsewhere"]))

        # 2. an old file is ignored, a conflict copy counts once, a file that will not read is passed over
        folder = root / presence.DIR
        old = {"id": "old1", "name": "Old Mac", "app": "idiograph", "time": time.time() - 3600}
        (folder / "old1.json").write_text(json.dumps(old), encoding="utf-8")
        (folder / f"{one_key} 2.json").write_text(mine.read_text(encoding="utf-8"), encoding="utf-8")
        (folder / "broken.json").write_text("{not json", encoding="utf-8")
        at("two")
        names = presence.others(root)
        near = presence.others(root, now=time.time() + presence.FRESH - 20)
        past = presence.others(root, now=time.time() + presence.FRESH + 20)
        check("435: a file older than five minutes is ignored, a sync app's conflict copy of a file counts once for "
              "its owner, a file that will not read is passed over, and this install's own id is never another "
              "computer",
              len(names) == 1 and len(near) == 1 and past == [] and presence.others(root, ident=one_key) == [],
              json.dumps([names, near, past]))

        # 2b. a settings folder cloned onto another Mac (the same id file) is another computer by its hardware mark, a
        # lost id file does not make this install another computer to itself, and a computer whose clock is hours off
        # is named once its file's time has changed since the last look
        at("one")
        presence.install_id()
        cloned = {"id": f"{one_id}.0badc10e", "name": "Cloned Mac", "app": "idiograph", "time": time.time()}
        (folder / "cloned.json").write_text(json.dumps(cloned), encoding="utf-8")
        seen_clone = presence.others(root)
        (folder / "cloned.json").unlink()
        (configs["one"].parent / presence.ID_FILE).unlink()
        own_after_loss = presence.others(root)
        (configs["one"].parent / presence.ID_FILE).write_text(json.dumps({"id": one_id}), encoding="utf-8")
        skew = {"id": "skew1.aaaaaaaa", "name": "Far Mac", "app": "idiograph", "time": time.time() - 7200}
        (folder / "skew.json").write_text(json.dumps(skew), encoding="utf-8")
        first_look = presence.others(root)
        (folder / "skew.json").write_text(json.dumps(dict(skew, time=skew["time"] + 60)), encoding="utf-8")
        second_look = presence.others(root)
        (folder / "skew.json").unlink()
        check("435: a settings folder cloned onto another Mac (the same id file) is named by its hardware mark, a "
              "lost id file does not make this install another computer to itself, and a computer whose clock is "
              "hours off is named once its file's time has changed since the last look",
              "Cloned Mac" in seen_clone and own_after_loss == [] and "Far Mac" not in first_look
              and "Far Mac" in second_look, json.dumps([seen_clone, own_after_loss, first_look, second_look]))

        # 2c. a computer where getnode finds no address answers a random one each run, which must not change the key
        import uuid as _uuid
        real_node = _uuid.getnode
        try:
            _uuid.getnode = lambda: 0x1A2B3C4D5E6F | (1 << 40)
            key_a = presence.key_of(one_id)
            _uuid.getnode = lambda: 0x7A8B9C0D1E2F | (1 << 40)
            key_b = presence.key_of(one_id)
        finally:
            _uuid.getnode = real_node
        check("435: a computer whose network address cannot be read keeps the same key from one run to the next",
              key_a == key_b == one_id, json.dumps([key_a, key_b]))

        # 3. the presence folder is no participant, in no shared copy, no writer for the Trash, not the team's walk
        at("one")
        sent = [rel for _p, rel in project_pack.project_files(root)]
        cases = [str(row.get("path")) for row in routes.list_cases(root)] + [c["folder"] for c in routes.team_folders(root)]
        guard = None
        try:
            guard = trash.busy(root)
        except OSError:
            guard = None
        check("435: the presence folder is not a participant, is left out of a shared copy, is not a writer that "
              "stops Remove to the Trash and holds no .lock file",
              all(presence.DIR not in rel for rel in sent) and sent and not any(presence.DIR in c for c in cases) and guard is False
              and project_pack.never_sent(project_pack.PurePosixPath(presence.DIR) / f"{one_key}.json"),
              json.dumps({"sent": sent, "cases": cases, "busy": guard}))

        # 4. the command line reads and writes nothing, this install having no id yet
        three = home / "three"
        three.mkdir()
        configs["three"] = three / "config.json"
        configs["three"].write_text(json.dumps({"projects": [{"root": str(root)}]}), encoding="utf-8")
        at("three")
        before = files(root)
        code, out, err = cli.run(["--config", str(configs["three"]), "--json", "project", "show"])
        shown = json.loads(out) if out.strip().startswith("{") else {}
        check("435: the command line's project show names the other computers as open_elsewhere and writes nothing, "
              "no id file and nothing in the project's folder",
              code == 0 and len((shown.get("project") or {}).get("open_elsewhere", [])) == 1
              and files(root) == before and not (three / presence.ID_FILE).exists(), err or out[:300])

        # 5. a page that leaves the project takes its file away, through the beat; a demo is never written
        at("one")
        presence.HELD.clear()
        server_mod.PAGES.clear()
        server_mod.api_beat({"page": "p435", "at": str(root)})
        presence._IDLE.wait(5)
        wrote = mine.exists()
        server_mod.api_beat({"page": "p435", "gone": True})
        presence._IDLE.wait(5)
        gone = not mine.exists()
        server_mod.api_beat({"page": "p435", "at": "demo"})
        server_mod.api_beat({"page": "p435", "gone": True})
        presence._IDLE.wait(5)
        check("435: a page's beat writes this install's file and the page's last word takes it away, the other "
              "computers' files left as they were, and a demo's folder is never written",
              wrote and gone and (folder / "old1.json").exists()
              and not (server_mod.DEMO_DIR / presence.DIR).exists(), f"{wrote} {gone}")

        # 6. a failure to write is silent: the folder's name taken by a file, a folder that is not there
        blocked = home / "Blocked"
        blocked.mkdir()
        (blocked / presence.DIR).write_text("a file where the folder goes", encoding="utf-8")
        failed = presence.write(blocked) is False
        presence.sync([str(home / "nowhere")], wait=5)
        presence.remove(home / "nowhere")
        check("435: a presence file that cannot be written, or read, or taken away, is silent and stops nothing",
              failed and presence.others(blocked) == [] and presence.others(home / "nowhere") == [], str(failed))
    finally:
        presence.sync(None)
        (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE) = kept[:2]
        presence.HELD.clear()
        presence.HELD.update(kept[2])
        presence._ID[:] = kept[3]
        server_mod.PAGES.clear()
