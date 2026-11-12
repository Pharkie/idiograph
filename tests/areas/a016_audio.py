from __future__ import annotations

import ast
import contextlib
import hashlib
import importlib.util
import io
import re
import shutil
import struct
import wave
from pathlib import Path

import audio as audio_mod

from . import support
from .support import TOOL, check, skip


def mp4_seconds(path: Path) -> float:
    """An .m4a's length from its movie header, `moov` then `mvhd`, read here so the check needs no audio tool."""
    data = Path(path).read_bytes()

    def boxes(start: int, end: int):
        at = start
        while at + 8 <= end:
            size, kind = struct.unpack(">I4s", data[at:at + 8])
            head = 8
            if size == 1:
                size, head = struct.unpack(">Q", data[at + 8:at + 16])[0], 16
            elif size == 0:
                size = end - at
            if size < head:
                return
            yield kind, at + head, at + size
            at += size

    for kind, body, end in boxes(0, len(data)):
        if kind == b"moov":
            for inner, at, _ in boxes(body, end):
                if inner == b"mvhd":
                    if data[at] == 1:
                        scale, length = struct.unpack(">IQ", data[at + 20:at + 32])
                    else:
                        scale, length = struct.unpack(">II", data[at + 12:at + 20])
                    return length / scale if scale else 0.0
    return 0.0


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, support.source(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def silence(path: Path, seconds: float, rate: int = 24000) -> Path:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * int(rate * seconds))
    return path


def test_audio(scratch):
    print("\n15. Choosing and ranging the recording")
    folder = scratch / "audio" / "P1 - Pseudonym" / "Source" / "Initial" / "Source"
    folder.mkdir(parents=True, exist_ok=True)
    check("an empty folder offers nothing", audio_mod.choose(folder, "Initial", "P1") is None)
    (folder / "P1 Macbook.m4a").write_bytes(b"x" * 900)
    (folder / "P1-Initial-track-Adam.m4a").write_bytes(b"x" * 5000)
    check("a lone mixed file is chosen over a bigger per-speaker track",
          audio_mod.choose(folder, "Initial", "P1").name == "P1 Macbook.m4a",
          audio_mod.choose(folder, "Initial", "P1").name)
    (folder / "P1 second.m4a").write_bytes(b"x" * 2000)
    check("otherwise the largest file with no track in its name wins",
          audio_mod.choose(folder, "Initial", "P1").name == "P1 second.m4a",
          audio_mod.choose(folder, "Initial", "P1").name)
    (folder / "P1-Initial.m4a").write_bytes(b"x" * 10)
    check("an exact P<n>-<Sheet> stem beats the size rule",
          audio_mod.choose(folder, "Initial", "P1").name == "P1-Initial.m4a",
          audio_mod.choose(folder, "Initial", "P1").name)
    tracks = scratch / "audio" / "tracks"
    tracks.mkdir(parents=True, exist_ok=True)
    (tracks / "P1-2d-track-Adam.m4a").write_bytes(b"x" * 10)
    check("per-speaker tracks alone are no recording", audio_mod.choose(tracks, "2d", "P1") is None)

    book = scratch / "audio" / "P1 - Pseudonym" / "P1 Pseudonym - EN & ES.xlsx"
    check("the folder is read off the workbook and the sheet name",
          audio_mod.source_folder(book, "Initial") == folder, str(audio_mod.source_folder(book, "Initial")))
    check("the P number comes off the workbook name", audio_mod.case_tag(book) == "P1",
          audio_mod.case_tag(book))
    book.write_bytes(b"not a workbook, only a name")
    check("for_sheet puts the two together",
          audio_mod.for_sheet(book, "Initial").name == "P1-Initial.m4a")
    check("m4a is served as audio/mp4", audio_mod.content_type(folder / "P1-Initial.m4a") == "audio/mp4")

    check("a first hundred bytes range", audio_mod.parse_range("bytes=0-99", 1000) == (0, 99))
    check("an open ended range runs to the last byte", audio_mod.parse_range("bytes=100-", 1000) == (100, 999))
    check("a suffix range counts back from the end", audio_mod.parse_range("bytes=-100", 1000) == (900, 999))
    check("a range past the end is refused and the whole file served",
          audio_mod.parse_range("bytes=2000-", 1000) is None)
    check("an end past the file is clamped", audio_mod.parse_range("bytes=900-5000", 1000) == (900, 999))
    check("no header, and nonsense, both mean the whole file",
          audio_mod.parse_range(None, 1000) is None and audio_mod.parse_range("bytes=abc", 1000) is None)
    span = b"".join(audio_mod.read_span(folder / "P1 Macbook.m4a", 10, 19))
    check("the span read back is the bytes asked for", span == b"x" * 10, f"{len(span)} bytes")

    demo_recordings(scratch)


def demo_recordings(scratch):
    """The demo's three recordings (recvoices, 12 November 2026): committed for the transcripts they were made from,
    the timecodes inside them, copied into place by the builds and the server, nothing ever spoken."""
    print("\n16. The demo's recordings, committed, staged and put in place, nothing spoken")
    import make_demo
    import server as server_mod
    import workbook as wb_mod
    import idiograph_routes

    # ── A. each committed under the hash of its transcript as it stands, and nothing else in the folder
    folder = support.source("packaging/recording")
    build_mac = load("idiograph_build_mac_16", "packaging/build_mac.py")
    named = {}
    for name in make_demo.CASES:
        text = make_demo.written_sources(name)[0].read_bytes().replace(b"\r\n", b"\n")
        named[name] = folder / f"{name}-Initial-{hashlib.sha256(text).hexdigest()[:16]}.m4a"
    check("16: each demo participant's recording is committed under the hash of their transcript as it stands, the "
          "one name make_demo, the server and the builds take, and no other recording is in the folder",
          all(p.is_file() and make_demo.committed(n) == p == build_mac.committed_recording(n) for n, p in named.items())
          and sorted(folder.glob("*.m4a")) == sorted(named.values()) and (folder / make_demo.AUDIO_LICENCE).is_file(),
          ", ".join(p.name for p in named.values()))

    # ── B. the timecodes rise from nothing and end inside each recording
    spans = {}
    for name in make_demo.CASES:
        seconds = [wb_mod.ts_seconds(r["Timestamp"]) for r in make_demo.read_turns(make_demo.written_sources(name)[0])]
        spans[name] = (seconds, mp4_seconds(named[name]) if named[name].is_file() else 0.0)
    check("16: each transcript's timecodes start at nothing and only rise, and the last turn's falls inside its recording",
          all(s[0] == 0 and all(b > a for a, b in zip(s, s[1:])) and 0 < s[-1] < length for s, length in spans.values()),
          ", ".join(f"{n} last {wb_mod.hhmmss(s[-1])} of {wb_mod.hhmmss(int(length))}" for n, (s, length) in spans.items()))

    # ── C. no build and no server path calls say
    paths = ["packaging/build_mac.py", "packaging/build_windows.py", "packaging/build_linux.py", "packaging/mac_daily.py",
             "packaging/recording/voice_demo.py", "apps/idiograph/make_demo.py", "apps/idiograph/idiograph_routes.py",
             "family/server.py"]
    said = []
    for rel in paths:
        tree_ = ast.parse(support.source(rel).read_text(encoding="utf-8"))
        said += [f"{rel}:{n.lineno}" for n in ast.walk(tree_) if isinstance(n, ast.Constant) and isinstance(n.value, str)
                 and re.fullmatch(r"say( +-.*)?", n.value)]
    check("16: no build and no server path calls macOS say, the demo's recordings being copied, never spoken",
          not said and not hasattr(make_demo, "say_clip") and not hasattr(build_mac, "speak_recording"), str(said))

    # ── D. a build stages all three and the licence beside each, and says which when one is missing
    stage = scratch / "recordings-16" / "stage"
    shutil.rmtree(stage.parent, ignore_errors=True)
    stage.mkdir(parents=True)
    demo = build_mac.stage_cases(stage)
    line = build_mac.stage_recordings(demo)
    licence = (folder / make_demo.AUDIO_LICENCE).read_bytes()
    staged = {n: demo / build_mac.recording_path(n) for n in make_demo.CASES}
    check("16: a build stages each participant's recording where the player finds it, its licence beside it, and says so",
          all(p.is_file() and p.read_bytes() == named[n].read_bytes()
              and (p.parent / make_demo.AUDIO_LICENCE).read_bytes() == licence for n, p in staged.items())
          and all(p == make_demo.recording(n, demo) for n, p in staged.items())
          and line.startswith("with the three recordings"), line)
    two = stage.parent / "two"
    two.mkdir()
    for name in ("Juno", "Mabel"):
        shutil.copyfile(named[name], two / named[name].name)
    shutil.copyfile(folder / make_demo.AUDIO_LICENCE, two / make_demo.AUDIO_LICENCE)
    kept_folder = build_mac.RECORDINGS
    try:
        build_mac.RECORDINGS = two
        fewer = build_mac.stage_cases(stage.parent / "stage-two")
        fewer_line = build_mac.stage_recordings(fewer)
    finally:
        build_mac.RECORDINGS = kept_folder
    check("16: a transcript with no recording made from it as it stands ships without its audio, said in one line",
          not (fewer / build_mac.recording_path("Rowan")).exists() and (fewer / build_mac.recording_path("Mabel")).is_file()
          and "without Rowan's recording" in fewer_line and "\n" not in fewer_line, fewer_line)

    # ── E. the server, run from source, copies a participant's recording in on the request, and none for an edit
    work = scratch / "recordings-16" / "demo"
    shutil.copytree(support.source("demo"), work, ignore=shutil.ignore_patterns("*.m4a", "Working", "_Archive", "ta"))
    kept = (server_mod.DEMO_DIR, server_mod.DEMO_CASE, server_mod.DEMO_WORKBOOK, server_mod.SHIPPED_DEMO,
            server_mod.DEMO_PROJECT, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    root = scratch / "recordings-16" / "root"
    root.mkdir()
    older = make_demo.recording("Mabel", work)
    older.parent.mkdir(parents=True)
    older.write_bytes(b"an older recording of hers, in the say voices")
    try:
        server_mod.DEMO_DIR = server_mod.SHIPPED_DEMO = work
        server_mod.DEMO_CASE = work / "Juno"
        server_mod.DEMO_WORKBOOK = server_mod.DEMO_CASE / "Juno - EN & ES.xlsx"
        server_mod.DEMO_PROJECT = work / "idiograph-project.json"
        server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = str(root), {"recent": []}
        mabel = work / "Mabel" / "Mabel - EN & ES.xlsx"
        heard = idiograph_routes.api_audio({"path": str(mabel), "sheet": "Initial"})
        csv_path = make_demo.written_sources("Rowan", work)[0]
        csv_path.write_bytes(csv_path.read_bytes().replace(b"No. No, I think", b"No. No, I really think", 1))
        edited = idiograph_routes.api_audio({"path": str(work / "Rowan" / "Rowan - EN & ES.xlsx"), "sheet": "Initial"})
    finally:
        (server_mod.DEMO_DIR, server_mod.DEMO_CASE, server_mod.DEMO_WORKBOOK, server_mod.SHIPPED_DEMO,
         server_mod.DEMO_PROJECT, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY) = kept
    placed = make_demo.recording("Mabel", work)
    check("16: run from source, the server copies a demo participant's committed recording into place as the player "
          "asks for it, over an older one of hers, and an edited transcript, its timecodes no longer the voices', gets "
          "none and a quiet player",
          heard.get("found") is True and heard.get("name") == "Mabel-Initial.m4a"
          and placed.is_file() and placed.read_bytes() == named["Mabel"].read_bytes()
          and edited.get("found") is False and not make_demo.recording("Rowan", work).exists()
          and not list(placed.parent.glob(".*")), f"{heard.get('name')} {edited.get('note', '')}")

    # ── F. the join: each turn's timecode from its clip, the recording named by the CSV as then written
    if not (shutil.which("afconvert") or shutil.which("ffmpeg")):
        skip("16: the join writes the timecodes and names the recording", "neither afconvert nor ffmpeg is here")
    else:
        pip = scratch / "recordings-16" / "pip"
        (pip / "source").mkdir(parents=True)
        made = pip / "made"
        made.mkdir()
        (made / "Pip-Initial-0123456789abcdef.m4a").write_bytes(b"made from an older transcript")
        transcript = pip / "source" / "Pip - interview.csv"
        transcript.write_bytes(b"Name,Timestamp,Transcript\r\nQuill,00:00:00,What is the boat like?\r\n"
                               b"Pip,00:00:09,\"Small, and mine.\"\r\nQuill,00:00:30,Thank you.\r\n")
        clips = [silence(pip / f"{i:03d}.wav", s) for i, s in enumerate((1.2, 2.4, 0.7))]
        try:
            make_demo.build_recording("Pip", clips, write_csv=False, verbose=False, folder=made, demo=pip)
            refused = False
        except make_demo.DemoError:
            refused = True
        result = make_demo.build_recording("Pip", clips, write_csv=True, verbose=False, folder=made, demo=pip)
        times = [r["Timestamp"] for r in make_demo.read_turns(transcript)]
        expected = made / audio_mod.demo_recording_name("Pip", "Initial", transcript)
        check("16: the join writes each turn's timecode from its clip and the half-second gap, names the recording by "
              "the CSV as then written, takes the one made from the older transcript away, and refuses to join over "
              "timecodes the clips no longer give",
              refused and times == ["00:00:00", "00:00:02", "00:00:05"] and result["moved"] == 2
              and result["path"] == expected and sorted(p.name for p in made.iterdir()) == [expected.name]
              and transcript.read_bytes().count(b"\r\n") == 4 and 4.5 < mp4_seconds(expected) < 6.0,
              f"{times} {result['moved']} moved, {[p.name for p in made.iterdir()]}")

    # ── G. the voicing tool: a turn spoken as it reads is not spoken again, and its status and join call nobody
    voice = load("idiograph_voice_demo_16", "packaging/recording/voice_demo.py")
    clips_dir = scratch / "recordings-16" / "clips"
    first = voice.turns("Juno")[0]
    wav, meta = voice.clip_paths(clips_dir, "Juno", first["row"])
    wav.parent.mkdir(parents=True)
    silence(wav, 0.5)
    meta.write_text('{"key": "%s"}' % first["key"], encoding="utf-8")
    same = voice.is_current(clips_dir, "Juno", first)
    meta.write_text('{"key": "%s"}' % voice.key_of(first["voice"], first["style"], first["text"] + " Edited."),
                    encoding="utf-8")
    changed = voice.is_current(clips_dir, "Juno", first)
    asked = []

    def refuse(*args, **kwargs):
        asked.append(args[0] if args else kwargs)
        raise OSError("no call in a check")

    real = (voice.urllib.request.urlopen, voice.subprocess.run)
    out = io.StringIO()
    try:
        voice.urllib.request.urlopen = voice.subprocess.run = refuse
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            codes = [voice.main(["--clips", str(clips_dir), "--status"]),
                     voice.main(["--clips", str(clips_dir), "--join-only", "--no-build"]),
                     voice.main(["--clips", str(TOOL / "voices"), "--status"])]
    finally:
        voice.urllib.request.urlopen, voice.subprocess.run = real
    check("16: the voicing tool keeps a turn spoken with the same voice, style and text and speaks one edited again, its "
          "status and its join call neither Google nor the Keychain and join nothing short of a turn, and a clip folder "
          "inside the repo is refused",
          same and not changed and not asked and codes == [0, 0, 2]
          and all(make_demo.committed(n) == named[n] for n in make_demo.CASES), out.getvalue()[-300:])
