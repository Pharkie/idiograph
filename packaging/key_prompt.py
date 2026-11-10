#!/usr/bin/env python3
"""Tauri's CLI given the update key's password through a terminal of its own, so the password never
stands on a command line (18 October 2026, the fourth Tauri build). `make_update_key.sh` runs it:

    python3 packaging/key_prompt.py <file holding the password> <the CLI's command...>

`tauri signer generate` with no `-p` asks for the password on its terminal twice, as minisign asks,
and reads it with the terminal's echo off. This runs the CLI on a pseudo-terminal of its own and types
the password from the file at each of its two prompts, so the password passes through this process's
memory and that terminal alone, never an argument list or an environment, which `ps` can show, where
the third build's script handed it over with `-p` for the second the CLI ran. CI is taken out of the
CLI's environment, since with it set the CLI asks nothing and makes a key with no password at all. The
CLI's words go to standard output, the password never among them, and its exit code is this one's.
The standard library only, on a Mac or Linux, where a terminal can be made.

    python3 packaging/key_prompt.py --opens <key> <file holding the password> <public key>

says, once the CLI has made the pair, whether the key is sealed under that password and opens with it to
the public half beside it, through minisign.py, so a key made with no password, or another, is never kept.
"""
from __future__ import annotations

import os
import re
import select
import signal
import sys
import time
from pathlib import Path

# the CLI's two prompts, "Password: " and "Password (one more time): "
PROMPT = re.compile(rb"Password[^\n:]*: ")
ASKS = 2
# how long the CLI has to make the key, a first npx fetch among it
WAIT = 600


def run(secret: bytes, command: list[str], wait: float = WAIT) -> tuple[int, bytes]:
    """The command run on a terminal of its own, `secret` typed at each prompt: its exit code and its
    words with the secret taken out, should the terminal have echoed it before its echo went off."""
    import pty

    env = dict(os.environ)
    env.pop("CI", None)
    pid, fd = pty.fork()
    if pid == 0:
        try:
            os.execvpe(command[0], command, env)
        finally:
            os._exit(127)
    said = bytearray()
    answered = 0
    status = None
    deadline = time.time() + wait
    while time.time() < deadline:
        ready, _, _ = select.select([fd], [], [], 0.25)
        if fd not in ready:
            done, code = os.waitpid(pid, os.WNOHANG)
            if done:
                status = code
                break
            continue
        try:
            chunk = os.read(fd, 4096)
        except OSError:
            chunk = b""
        if not chunk:
            break
        said += chunk
        while answered < ASKS and len(PROMPT.findall(bytes(said))) > answered:
            # a moment for the CLI to turn its terminal's echo off once its prompt is out
            time.sleep(0.2)
            os.write(fd, secret + b"\n")
            answered += 1
    else:
        os.kill(pid, signal.SIGTERM)
        said += b"\nThe CLI did not finish in time.\n"
    if status is None:
        status = os.waitpid(pid, 0)[1]
    code = os.waitstatus_to_exitcode(status)
    try:
        os.close(fd)
    except OSError:
        pass
    return code, bytes(said).replace(secret, b"<password>")


def opens(key: Path, password: Path, public: Path) -> str | None:
    """Why the key made is not the one wanted, or None when it is sealed under the password, opens with
    it and matches its public half."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import base64

    import minisign

    try:
        blob = key.read_text(encoding="utf-8")
        lines = [ln for ln in base64.b64decode(blob.strip()).decode("utf-8").splitlines() if ln.strip()]
        sealed = base64.b64decode(lines[1])[2:4] == minisign.KDF
        opened = minisign.open_secret(blob, password.read_text(encoding="utf-8").strip())
    except (OSError, ValueError, IndexError, minisign.BadKey) as exc:
        return f"the key does not open with its password ({exc})"
    if not sealed:
        return "the key was made with no password"
    if opened.public_key().strip() != public.read_text(encoding="utf-8").strip():
        return "the key and its public half do not match"
    return None


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args[:1] == ["--opens"] and len(args) == 4:
        why = opens(Path(args[1]), Path(args[2]), Path(args[3]))
        if why:
            print(f"Tauri's CLI made a key, but {why}, so nothing was kept.", file=sys.stderr)
        return 1 if why else 0
    if len(args) < 2:
        print("python3 packaging/key_prompt.py <file holding the password> <the CLI's command...>", file=sys.stderr)
        return 2
    secret = Path(args[0]).read_bytes().strip()
    if not secret:
        print("The password's file is empty.", file=sys.stderr)
        return 2
    code, said = run(secret, args[1:])
    sys.stdout.write(said.decode("utf-8", "replace"))
    sys.stdout.flush()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
