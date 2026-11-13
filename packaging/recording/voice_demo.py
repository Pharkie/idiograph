#!/usr/bin/env python3
"""The demo's three interviews voiced turn by turn in Google Gemini's voices, joined into the recordings committed
beside this file, and the transcripts' timecodes written from them (recvoices, 12 November 2026, from the voices
run of 11 and 12 November: Adam, 11 November, the `say` voices "sound so robot", Gemini 3.8 Flash TTS his choice
and the casting left to Claude).

    .venv/bin/python packaging/recording/voice_demo.py --clips ~/demo-voices --status
    .venv/bin/python packaging/recording/voice_demo.py --clips ~/demo-voices
    .venv/bin/python packaging/recording/voice_demo.py --clips ~/demo-voices --case Mabel
    .venv/bin/python packaging/recording/voice_demo.py --clips ~/demo-voices --join-only

`--clips` names a folder outside the repo, or in its own ignored `.verify/`, that keeps one clip a turn, `<clips>/<Name>/NNN.wav` with its record
`NNN.json`, NNN the turn's row counted from 0 in `demo/source/<Name> - interview.csv`. Each clip is 16-bit mono WAV
at the model's rate, trimmed to its speech with TRIM_PAD either side and levelled to LEVEL_DB. A turn already
spoken with the same voice, style and text is never spoken again, so after an edit to one turn a run speaks that
turn alone, and the clips of every other turn are joined as they were. `--status` says what a run would speak and
calls nothing.

A run, in order:

1. Each turn of the chosen interviews (all three unless `--case` names some) not yet spoken as it now reads is
   spoken, one call a turn, SPACING seconds apart, with the speaker's stored voice and the style for their part.
   A take whose pace or tail fails the checks below is taken again, up to TAKES times, the last one kept.
2. Each interview whose every turn is spoken as it reads is joined by `make_demo.build_recording`: the clips
   measured, each turn's Timestamp in its CSV written from their lengths and the half-second gap, and the clips
   joined into `<Name>-Initial-<hash>.m4a` here, named by the CSV as then written, its older recording taken away,
   and `demo/recordings.json` written again. The new file then goes up to the `demo-recordings-1` release with the
   manifest (`gh release upload`), since the installed app downloads it from there (recdemand, 13 November 2026).
3. When a timecode moved, the demo is built again from its sources by its own steps, `make_demo.ship_all` and
   `ship_ta`, so the workbooks, the pristine copy, the GETs and the thematic analysis demo carry the new times.
   `--no-build` leaves that for `make_demo.py --written --force`.

`--join-only` does 2 and 3 alone, with no call to Google, from clips already made.

The key is Google's, read from the Keychain at run time (`security find-generic-password -s GEMINI_API_KEY -w`),
sent only in the request's `x-goog-api-key` header and never printed, logged or written. Each call's usage goes to
`<clips>/ledger.jsonl`, and a run stops before the ledger would pass `--budget` dollars. Google's Tier 1 allows 10
calls a minute and 100 a day for this model: a refusal for the day stops the run, the turns spoken so far kept, and
the next run after midnight Pacific carries on. The standard library alone, so it runs on the repo's venv.
"""
from __future__ import annotations

import argparse
import array
import base64
import hashlib
import io
import json
import math
import subprocess
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parents[1]
sys.path.insert(0, str(TOOL))
import boot  # noqa: E402  the family's folders on the path (boot.py)

boot.setup()

import make_demo  # noqa: E402

MODEL = "gemini-3.8-flash-tts"
BASE = "https://generativelanguage.googleapis.com/v1beta"
KEY_SERVICE = "GEMINI_API_KEY"

# The four stored voices, made by Gemini's voice design from these descriptions on 11 November 2026 (type prompted,
# stored), each kept a year from its last use. None is cloned from anyone's recording. The interviewer's is the only
# southern English accent and the only older man, Juno's a Spanish woman long in England (her interview is in
# English and Spanish), Mabel's a woman of 73 from Lancashire, Rowan's a quiet Dublin man of about thirty
VOICES = {
    "interviewer": "voice_01i0f9yj75rq",
    "Juno": "voice_fmjdhudmistf",
    "Mabel": "voice_vjg4pl6hgwrh",
    "Rowan": "voice_sv4oca0bhd3v",
}
DESIGNS = {
    "interviewer": ("male", "en-GB", "A calm, warm British man in his late forties with a soft, educated southern "
                    "English accent, a qualitative researcher interviewing someone: gently curious, attentive and "
                    "unhurried, low-to-mid pitch, speaking quietly and kindly."),
    "Juno": ("female", "en-GB", "A Spanish woman in her early forties who has lived in England for many years, "
             "speaking fluent, natural English with a clear, warm Spanish accent, plain-spoken and wry, mid-to-low "
             "pitch, unhurried and conversational."),
    "Mabel": ("female", "en-GB", "A cheerful widow of seventy-three from the north of England, Lancashire, chatty "
              "and teasing with a ready laugh, the lighter, slightly thinner voice of an older woman, warm and "
              "plain-spoken, natural conversational pace."),
    "Rowan": ("male", "en-IE", "A quiet Irish man of about thirty from Dublin, soft-spoken and reflective, a little "
              "hesitant, a gentle mid-pitched voice, speaking plainly and conversationally."),
}

# The pace, set by each turn's style after the samples were measured (11 November 2026). Mabel and Rowan keep the
# plain style, at 154 to 178 words a minute. Juno raced at it, 170 to 196, and her own style takes her to 160 to 168.
# The interviewer's turns of under SHORT_WORDS words raced at 200 to 250 and take the slow style
STYLE_INTERVIEWER = "Calm and attentive, at an unhurried conversational pace."
STYLE_INTERVIEWER_SHORT = "Calm and attentive, speaking slowly and gently."
SHORT_WORDS = 10
STYLE_PARTICIPANT = "Natural and conversational, at an ordinary speaking pace."
STYLE_OWN = {"Juno": "Thoughtful and conversational, at an unhurried pace, with natural pauses between sentences."}
# a take is kept when its pace over its speech is within PACE words a minute, or the turn is under PACE_FROM words,
# and its last TAIL seconds are not noise, else taken again up to TAKES times, the last take kept
PACE = (110, 210)
PACE_FROM = 8
TAKES = 2
TAIL = 0.3
# each clip trimmed to its speech, the first and last 10 ms frame within SPEECH_DB of its loudest, with TRIM_PAD
# seconds either side, then levelled to LEVEL_DB of full scale, its peak at most PEAK
SPEECH_DB = -40.0
TRIM_PAD = 0.12
LEVEL_DB = -20.0
PEAK = 0.95
# Tier 1's ten calls a minute, one every SPACING seconds, and the prices to 31 December 2026, per token: text in,
# audio out at 25 tokens a second
SPACING = 6.5
PRICE_IN = 0.50 / 1e6
PRICE_OUT = 9.00 / 1e6
BUDGET = 2.00


class Stop(Exception):
    """A reason the run stops, said in one line."""


# ── the turns ───────────────────────────────────────────────────────────────────────────────────────────────

def part_of(case: str, row: dict) -> str:
    """The part a turn is spoken in: the participant's own, or the interviewer's for every other speaker."""
    return case if row["Name"].strip() == case else "interviewer"


def style_of(part: str, text: str) -> str:
    if part == "interviewer":
        return STYLE_INTERVIEWER_SHORT if len(text.split()) < SHORT_WORDS else STYLE_INTERVIEWER
    return STYLE_OWN.get(part, STYLE_PARTICIPANT)


def key_of(voice: str, style: str, text: str) -> str:
    """What a clip was spoken from, so a turn is spoken again only when its voice, style or text changed."""
    return hashlib.sha1(json.dumps([voice, style, text]).encode("utf-8")).hexdigest()[:12]


def turns(case: str) -> list[dict]:
    """Each turn of a participant's interview as it is to be spoken: row, part, voice, style, text and key."""
    out = []
    for i, row in enumerate(make_demo.read_turns(make_demo.written_sources(case)[0])):
        part = part_of(case, row)
        text = make_demo.spoken(row["Transcript"])
        voice, style = VOICES[part], style_of(part, text)
        out.append({"row": i, "part": part, "voice": voice, "style": style, "text": text,
                    "key": key_of(voice, style, text)})
    return out


def clip_paths(clips: Path, case: str, row: int) -> tuple[Path, Path]:
    return clips / case / f"{row:03d}.wav", clips / case / f"{row:03d}.json"


def is_current(clips: Path, case: str, turn: dict) -> bool:
    """Whether the turn's clip is there and was spoken from the turn as it now reads."""
    wav, meta = clip_paths(clips, case, turn["row"])
    if not (wav.is_file() and meta.is_file()):
        return False
    try:
        held = json.loads(meta.read_text(encoding="utf-8"))
    except ValueError:
        return False
    return held.get("key") == turn["key"]


# ── the sound, the standard library alone ───────────────────────────────────────────────────────────────────

def read_wav(raw: bytes) -> tuple[list[float], int]:
    """A WAV's own frames as floats in -1 to 1 and its rate, mono. Only the data chunk is read, so the C2PA chunk
    Gemini puts after the audio never reaches a clip."""
    with wave.open(io.BytesIO(raw), "rb") as w:
        rate, channels, width, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        frames = w.readframes(n)
    if width != 2:
        raise Stop(f"The audio came back {8 * width}-bit, not 16-bit.")
    samples = array.array("h")
    samples.frombytes(frames[: n * channels * 2])
    if sys.byteorder == "big":
        samples.byteswap()
    if channels > 1:
        return [sum(samples[i:i + channels]) / channels / 32768.0 for i in range(0, len(samples), channels)], rate
    return [s / 32768.0 for s in samples], rate


def write_wav(path: Path, x: list[float], rate: int) -> None:
    """Floats in -1 to 1 written as 16-bit mono PCM, through a file of its own."""
    samples = array.array("h", (max(-32768, min(32767, int(round(v * 32767)))) for v in x))
    if sys.byteorder == "big":
        samples.byteswap()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.part")
    with wave.open(str(tmp), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(samples.tobytes())
    tmp.replace(path)


def blocks(x: list[float], rate: int, hop: float = 0.01) -> list[float]:
    """The sum of squares of each `hop`-second block."""
    h = int(rate * hop)
    return [sum(v * v for v in x[i:i + h]) for i in range(0, len(x) - h + 1, h)]


def frame_levels(x: list[float], rate: int, width: int) -> list[float]:
    """The RMS of each frame `width` 10 ms blocks wide, one frame starting every 10 ms."""
    b, h = blocks(x, rate), int(rate * 0.01)
    return [math.sqrt(sum(b[k:k + width]) / (width * h)) for k in range(0, len(b) - width + 1)]


def speech_bounds(x: list[float], rate: int) -> tuple[float, float]:
    """The first and last 20 ms frame within SPEECH_DB of the loudest, in seconds."""
    lv = [20 * math.log10(r + 1e-9) for r in frame_levels(x, rate, 2)]
    if not lv:
        return 0.0, 0.0
    floor = max(lv) + SPEECH_DB
    on = [k for k, v in enumerate(lv) if v > floor]
    return (on[0] * 0.01, on[-1] * 0.01 + 0.02) if on else (0.0, 0.0)


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    at = (len(ordered) - 1) * q
    low = int(at)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (at - low)


def tail_noisy(x: list[float], rate: int) -> bool:
    """Noise at the end: the last TAIL seconds loud (above -35 dB of the speech) and crossing zero often."""
    t = x[-int(rate * TAIL):] if len(x) > int(rate * TAIL) else x
    levels = frame_levels(x, rate, 3)
    speech = percentile(levels, 0.9) if levels else 1e-9
    rms = math.sqrt(sum(v * v for v in t) / max(1, len(t)))
    rel = 20 * math.log10(rms / (speech + 1e-12) + 1e-12)
    crossings = sum(1 for a, b in zip(t, t[1:]) if (a > 0) != (b > 0)) / max(1, len(t) - 1)
    return rel > -35 and crossings > 0.25


def trim(x: list[float], rate: int) -> list[float]:
    a, b = speech_bounds(x, rate)
    return x[max(0, int((a - TRIM_PAD) * rate)):min(len(x), int((b + TRIM_PAD) * rate))]


def level(x: list[float]) -> list[float]:
    rms = math.sqrt(sum(v * v for v in x) / max(1, len(x))) or 1e-9
    peak = max((abs(v) for v in x), default=0.0) or 1e-9
    gain = min(10 ** (LEVEL_DB / 20) / rms, PEAK / peak)
    return [v * gain for v in x]


# ── Gemini ──────────────────────────────────────────────────────────────────────────────────────────────────

class Gemini:
    """One turn spoken by one stored voice, the key read from the Keychain on the first call and held in memory
    alone, every call's usage kept in the ledger."""

    def __init__(self, ledger: Path, budget: float):
        self.ledger, self.budget, self._key, self._last = ledger, budget, None, 0.0

    def key(self) -> str:
        if self._key is None:
            done = subprocess.run(["security", "find-generic-password", "-s", KEY_SERVICE, "-w"],
                                  capture_output=True, text=True, encoding="utf-8")
            if done.returncode != 0 or not done.stdout.strip():
                raise Stop(f"There is no {KEY_SERVICE} in the Keychain, so nothing can be spoken.")
            self._key = done.stdout.strip()
        return self._key

    def scrub(self, text: str) -> str:
        return text.replace(self._key, "<key>") if self._key else text

    def spent(self) -> float:
        if not self.ledger.is_file():
            return 0.0
        return sum(json.loads(line).get("cost", 0.0)
                   for line in self.ledger.read_text(encoding="utf-8").splitlines() if line.strip())

    def note(self, entry: dict) -> None:
        with self.ledger.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(entry) + "\n")

    def speak(self, text: str, voice: str, style: str, tag: str) -> tuple[list[float], int]:
        """The turn's audio and its rate. Refused before the call when the ledger and a worst case for this turn,
        120 words a minute and half again, would pass the budget."""
        worst = (len(text.split()) / 2.0 + 3) * 25 * PRICE_OUT * 1.5 + len(text) * PRICE_IN
        if self.spent() + worst > self.budget:
            raise Stop(f"The ledger stands at ${self.spent():.2f}, and this turn could take it past the budget "
                       f"of ${self.budget:.2f}.")
        wait = self._last + SPACING - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()
        body = {"model": MODEL,
                "input": [{"type": "user_input", "content": [
                    {"type": "text", "text": text, "annotations": [{"type": "speech_metadata", "style": style}]}]}],
                "response_format": {"type": "audio"},
                "generation_config": {"speech_config": [{"voice": voice}]}}
        req = urllib.request.Request(f"{BASE}/interactions", data=json.dumps(body).encode("utf-8"), method="POST",
                                     headers={"x-goog-api-key": self.key(), "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                answer = json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as exc:
            said = self.scrub(exc.read().decode("utf-8", "replace"))[:600]
            self.note({"tag": tag, "status": exc.code, "cost": 0.0})
            if exc.code == 429 and "per day" in said.lower():
                raise Stop("Google's limit for the day is reached. The turns spoken so far are kept, and a run "
                           "after midnight Pacific carries on.")
            raise RuntimeError(f"HTTP {exc.code}: {said}")
        found = find_audio(answer)
        if not found:
            self.note({"tag": tag, "status": 200, "cost": 0.0, "noaudio": True})
            raise RuntimeError("The answer held no audio.")
        x, rate = read_wav(found)
        usage = answer.get("usage") or answer.get("usageMetadata") or {}
        cost = (usage.get("total_input_tokens", 0) * PRICE_IN + usage.get("total_output_tokens", 0) * PRICE_OUT
                if usage else len(text) / 4 * PRICE_IN + len(x) / rate * 25 * PRICE_OUT)
        self.note({"tag": tag, "status": 200, "seconds": round(len(x) / rate, 3), "cost": cost,
                   "usage": {k: usage.get(k) for k in ("total_input_tokens", "total_output_tokens")}})
        return x, rate


def find_audio(obj) -> bytes | None:
    """The first audio blob in an answer, wherever it sits, as bytes."""
    if isinstance(obj, dict):
        mime = str(obj.get("mime_type") or obj.get("mimeType") or "")
        data = obj.get("data")
        if isinstance(data, str) and len(data) > 200 and (obj.get("type") == "audio" or mime.startswith("audio")):
            return base64.b64decode(data)
        obj = list(obj.values())
    if isinstance(obj, list):
        for value in obj:
            found = find_audio(value)
            if found:
                return found
    return None


def speak_turn(gemini: Gemini, clips: Path, case: str, turn: dict) -> dict:
    """One turn spoken into its clip and record, taken again while its pace or tail fails, up to TAKES times."""
    words = len(turn["text"].split())
    takes = []
    for take in range(1, TAKES + 1):
        for attempt in range(5):
            try:
                x, rate = gemini.speak(turn["text"], turn["voice"], turn["style"], f"{case}:{turn['row']}:t{take}")
                break
            except (RuntimeError, OSError) as exc:
                if attempt == 4:
                    raise Stop(f"{case}'s turn {turn['row']} could not be spoken: {exc}")
                time.sleep(10 * (attempt + 1))
        a, b = speech_bounds(x, rate)
        wpm = words / max(b - a, 0.01) * 60
        ok = not tail_noisy(x, rate) and (words < PACE_FROM or PACE[0] <= wpm <= PACE[1])
        takes.append({"take": take, "wpm": round(wpm, 1), "ok": ok})
        if ok:
            break
    y = level(trim(x, rate))
    wav, meta = clip_paths(clips, case, turn["row"])
    write_wav(wav, y, rate)
    record = {"interview": case, "row": turn["row"], "part": turn["part"], "voice": turn["voice"],
              "style": turn["style"], "text_words": words, "seconds": round(len(y) / rate, 3), "rate": rate,
              "wpm": takes[-1]["wpm"], "takes": takes, "ok": takes[-1]["ok"], "key": turn["key"]}
    meta.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8", newline="\n")
    return record


# ── the run ─────────────────────────────────────────────────────────────────────────────────────────────────

def join(clips: Path, case: str) -> dict | None:
    """The participant's clips joined into their committed recording and their CSV's timecodes written, when every
    turn is spoken as it reads, else None."""
    ts = turns(case)
    if not all(is_current(clips, case, t) for t in ts):
        return None
    return make_demo.build_recording(case, [clip_paths(clips, case, t["row"])[0] for t in ts], write_csv=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Voice the demo's interviews with Gemini, join the recordings and "
                                             "write the timecodes.")
    ap.add_argument("--clips", required=True, help="the folder of clips, outside the repo, one clip a turn")
    ap.add_argument("--case", action="append", choices=list(make_demo.CASES), help="an interview, all three if none")
    ap.add_argument("--status", action="store_true", help="say what a run would speak, and call nothing")
    ap.add_argument("--join-only", action="store_true", help="join the clips already made, with no call to Google")
    ap.add_argument("--no-build", action="store_true", help="leave the demo's workbooks for make_demo.py")
    ap.add_argument("--budget", type=float, default=BUDGET, help="the most the ledger may come to, in dollars")
    args = ap.parse_args(argv)
    clips = Path(args.clips).expanduser().resolve()
    # never where git would take them up: outside the repo, or in its own gitignored .verify/
    if (clips == TOOL or TOOL in clips.parents) and TOOL / ".verify" not in clips.parents:
        print("The clips are kept outside the repo, or in its .verify folder. Name a folder of their own.",
              file=sys.stderr)
        return 2
    cases = args.case or list(make_demo.CASES)
    todo = {case: [t for t in turns(case) if not is_current(clips, case, t)] for case in cases}
    for case in cases:
        rows = todo[case]
        words = sum(len(t["text"].split()) for t in rows)
        print(f"  {case}: {len(turns(case)) - len(rows)} of {len(turns(case))} turns spoken as they read"
              + (f", {len(rows)} to speak, {words} words, rows {', '.join(str(t['row']) for t in rows)}" if rows else ""))
    if args.status:
        return 0
    try:
        if not args.join_only and any(todo.values()):
            clips.mkdir(parents=True, exist_ok=True)
            gemini = Gemini(clips / "ledger.jsonl", args.budget)
            for case in cases:
                for turn in todo[case]:
                    made = speak_turn(gemini, clips, case, turn)
                    print(f"  {case} {turn['row']:3d} {made['seconds']:6.2f}s {made['wpm']:6.1f} wpm"
                          + ("" if made["ok"] else ", kept after its last take failed the checks"), flush=True)
            print(f"  the ledger stands at ${gemini.spent():.2f}")
        moved = 0
        for case in cases:
            made = join(clips, case)
            if made is None:
                print(f"  {case}: not every turn is spoken as it reads, so their recording is as it was")
                continue
            moved += made["moved"]
        if moved and not args.no_build:
            print("Building the demo again with the new timecodes.")
            make_demo.ship_all(force=True)
            make_demo.ship_ta(force=True)
    except (Stop, make_demo.DemoError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
