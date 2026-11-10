"""How Working together's sealed messages travel (wtkeys, 8 November 2026): the one shape every route has, and a
loopback for the suite and a smoke run.

A transport carries bytes already sealed on this computer (team.py) and never reads them. Its shape, which the
relay's (wtrelay) and the shared folder's follow, duck-typed:

    send(project_id: str, sealed: bytes) -> int
        one message, answered with its number in that project's mailbox, the relay's seq
    fetch(project_id: str, after: int) -> list[tuple[int, str, bytes]]
        the messages numbered above `after`, each (seq, the sender's device id, sealed), oldest first
    listen(project_id: str, on_new: Callable[[], None]) -> Callable[[], None]
        `on_new` called when something new comes, until the stop it answers is called

A route that carries files above a message's size (wtowners, 8 November 2026: a version's files over a message,
the first full copy's among them) has two calls more, which the relay's has and the loopback's here:

    put_blob(project_id: str, blob: str, sealed: bytes) -> int
        a sealed file under its name, answered with its size
    get_blob(project_id: str, blob: str) -> bytes
        the same bytes back

`project_id` is the team's random 16-byte id in hex, or an invite's mailbox, `INVITE_PREFIX` and the invite's id
(`invite/<32 hex>`), which the relay answers at `/relay/v1/invites/:invite` and the folder route as
`invites/<invite>/`.

A route is made by its factory, `factory(device, team)`, `device` this install's (team.py `device`, its keys there
for a route that signs its calls) and `team` the project's team.json as it stands, registered under the route's
name by its own module (`register`). The suite and a smoke run put a loopback in their place: `OVERRIDE`, or the
environment's `IDIOGRAPH_TEAM_LOOPBACK` naming a folder two scratch servers share.

Two routes are registered here: "relay" (family/relay_transport.py) and "folder", a folder the team already shares
(family/folder_transport.py, wtfolder, 9 November 2026).
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Callable

INVITE_PREFIX = "invite/"
ENV = "IDIOGRAPH_TEAM_LOOPBACK"
# the routes by name, each a factory(device, team), registered by the route's own module
FACTORIES: dict = {}
# a factory every route gives way to, the suite's
OVERRIDE: Callable | None = None


def register(route: str, factory: Callable) -> None:
    FACTORIES[route] = factory


def for_team(route: str, device: dict, team: dict):
    """The transport this project sends through: the suite's or a smoke run's loopback when one is set, else its
    route's own, refused with a plain line when that route is not built into this copy yet."""
    if OVERRIDE is not None:
        return OVERRIDE(device, team)
    shared = os.environ.get(ENV, "").strip()
    if shared:
        return Loopback(device.get("id") or "", Path(shared))
    factory = FACTORIES.get(route)
    if factory is None:
        import i18n
        import team as team_mod
        raise team_mod.TeamError(i18n.t("team.refused.no_route"), "no_route")
    return factory(device, team)


class Hub:
    """Mailboxes held in memory, the loopback's own, which every Loopback of one Hub shares."""

    def __init__(self):
        self.boxes: dict = {}
        self.blobs: dict = {}
        self.lock = threading.Lock()
        self.listeners: dict = {}


HUB = Hub()


class Loopback:
    """The shape on this machine alone: mailboxes in memory (a Hub), or in a folder two servers share, one file a
    message, `<mailbox>/<seq>.msg` holding the sender's device id and the sealed bytes."""

    def __init__(self, device: str, folder: Path | None = None, hub: Hub | None = None):
        self.device = device
        self.folder = Path(folder) if folder else None
        self.hub = hub or HUB

    def box(self, project_id: str) -> Path:
        safe = "".join(ch if ch.isalnum() else "_" for ch in project_id)
        return self.folder / safe

    def send(self, project_id: str, sealed: bytes) -> int:
        if self.folder is None:
            with self.hub.lock:
                box = self.hub.boxes.setdefault(project_id, [])
                box.append((len(box) + 1, self.device, bytes(sealed)))
                seq = len(box)
                waiting = list(self.hub.listeners.get(project_id, []))
        else:
            folder = self.box(project_id)
            folder.mkdir(parents=True, exist_ok=True)
            with self.hub.lock:
                seq = 1 + max((int(p.stem) for p in folder.glob("*.msg") if p.stem.isdigit()), default=0)
                tmp = folder / f".{seq}.tmp"
                tmp.write_text(json.dumps({"device": self.device, "sealed": bytes(sealed).hex()}), encoding="utf-8",
                               newline="\n")
                os.replace(tmp, folder / f"{seq}.msg")
            waiting = list(self.hub.listeners.get(project_id, []))
        for on_new in waiting:
            on_new()
        return seq

    def fetch(self, project_id: str, after: int) -> list[tuple[int, str, bytes]]:
        if self.folder is None:
            with self.hub.lock:
                return [m for m in self.hub.boxes.get(project_id, []) if m[0] > after]
        folder = self.box(project_id)
        out = []
        for p in sorted((p for p in folder.glob("*.msg") if p.stem.isdigit()), key=lambda p: int(p.stem)):
            if int(p.stem) <= after:
                continue
            try:
                held = json.loads(p.read_text(encoding="utf-8"))
                out.append((int(p.stem), str(held["device"]), bytes.fromhex(held["sealed"])))
            except (OSError, ValueError, KeyError):
                continue
        return out

    def put_blob(self, project_id: str, blob: str, sealed: bytes) -> int:
        data = bytes(sealed)
        if self.folder is None:
            with self.hub.lock:
                self.hub.blobs[(project_id, blob)] = data
            return len(data)
        folder = self.box(project_id) / "blobs"
        folder.mkdir(parents=True, exist_ok=True)
        safe = "".join(ch if ch.isalnum() else "_" for ch in blob)
        tmp = folder / f".{safe}.tmp"
        tmp.write_bytes(data)
        os.replace(tmp, folder / safe)
        return len(data)

    def get_blob(self, project_id: str, blob: str) -> bytes:
        if self.folder is None:
            with self.hub.lock:
                got = self.hub.blobs.get((project_id, blob))
            if got is None:
                raise FileNotFoundError(blob)
            return got
        safe = "".join(ch if ch.isalnum() else "_" for ch in blob)
        return (self.box(project_id) / "blobs" / safe).read_bytes()

    def listen(self, project_id: str, on_new: Callable[[], None]) -> Callable[[], None]:
        with self.hub.lock:
            self.hub.listeners.setdefault(project_id, []).append(on_new)

        def stop() -> None:
            with self.hub.lock:
                held = self.hub.listeners.get(project_id, [])
                if on_new in held:
                    held.remove(on_new)
        return stop


def _relay(device: dict, team: dict):
    """The relay route, imported when a project first sends through it so that a copy without PyCA's
    `cryptography` is told so only then."""
    import relay_transport
    return relay_transport.team_factory(device, team)


register("relay", _relay)


def folder_refuse(code: str, folder: str) -> None:
    """The shared folder's refusals in plain words, as team.py's own (`team.refused.<code>`)."""
    import i18n
    import team as team_mod
    said = {
        "no_folder": lambda: i18n.t("team.refused.no_folder"),
        "folder_missing": lambda: i18n.t("team.refused.folder_missing", folder=folder),
        "invite_not_here": lambda: i18n.t("team.refused.invite_not_here"),
        "blob_not_here": lambda: i18n.t("team.refused.blob_not_here"),
        "too_large": lambda: i18n.t("team.refused.too_large"),
    }.get(code)
    raise team_mod.TeamError(said() if said else i18n.t(f"team.refused.{code}", folder=folder), code)


def _folder(device: dict, team: dict):
    """The shared-folder route (wtfolder, 9 November 2026, family/folder_transport.py): the folder team.json names,
    this install's numbering kept beside its device file, and the roster's other devices as the ones whose reading
    lets a message be dropped. A folder not chosen or not there is refused at once, in plain words."""
    import folder_transport
    import team as team_mod
    data = team or {}
    roster = data.get("roster") or {}
    peers = [d.get("id") for m in team_mod.roster_members(roster) for d in m.get("devices") or []
             if isinstance(d, dict) and d.get("id")]
    way = folder_transport.FolderTransport(device.get("id") or "", data.get("folder") or "",
                                           team_mod.device_path().parent, peers, refuse=folder_refuse,
                                           team=str(data.get("team") or ""))
    way.shared()
    return way


register("folder", _folder)

