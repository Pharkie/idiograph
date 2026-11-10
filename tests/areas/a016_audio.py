from __future__ import annotations

import audio as audio_mod

from .support import check


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
