#!/bin/sh
# Make Idiograph's update key, once, on Adam's Mac (17 October 2026, the third Tauri build).
#
#     sh packaging/make_update_key.sh
#
# Tauri's updater checks every update against a public key built into each copy of the app, and
# packaging/release.py signs each update with the secret key that goes with it. This makes the pair
# with Tauri's own `tauri signer generate`, under a password made here at random, and puts the secret
# key and its password into the login Keychain as idiograph-update-key and
# idiograph-update-key-password, where release.py reads them. Neither is ever printed: they travel to
# the Keychain through `security -i` on standard input, never on its command line, and the folder the
# CLI writes the key in, private to this user, is removed as the script ends however it ends. The
# password reaches Tauri's CLI through a terminal of the CLI's own, typed at its two prompts by
# packaging/key_prompt.py from the private file, so it never stands on a command line or in an
# environment, which a process list shows, where until 18 October it went on the CLI's command line for
# the second the CLI ran (the fourth Tauri build). It prints
# the public key alone, which goes in packaging/tauri/src-tauri/tauri.conf.json, and asks for the
# secret key and its password to be kept in 1Password too, since losing them means every tester
# reinstalls by hand. It refuses to run a second time, so a key in use is never replaced.
#
# Two switches for its checks alone (areas 173 and 175): IDIOGRAPH_KEYCHAIN_STUB names a folder that
# stands in for the Keychain, and IDIOGRAPH_TAURI_CLI the Tauri CLI, its tauri.js or a program. Without
# the second, npx fetches the CLI at the version every build uses.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)

KEY_ITEM="idiograph-update-key"
PASSWORD_ITEM="idiograph-update-key-password"
CLI_VERSION="2.12.1"
STUB="${IDIOGRAPH_KEYCHAIN_STUB:-}"
ME=$(id -un)

# whether the Keychain holds an item, its secret never read
held() {
    if [ -n "$STUB" ]; then
        [ -f "$STUB/$1" ]
    else
        security find-generic-password -a "$ME" -s "$1" >/dev/null 2>&1
    fi
}

# an item put in the Keychain, its secret the file named, through standard input alone
keep() {
    if [ -n "$STUB" ]; then
        (umask 077 && cp "$2" "$STUB/$1")
    else
        { printf 'add-generic-password -a "%s" -s "%s" -w "' "$ME" "$1"; tr -d '\n' < "$2"; printf '"\n'; } \
            | security -i >/dev/null 2>&1 || true
    fi
    held "$1"
}

if [ "$(uname)" != "Darwin" ] && [ -z "$STUB" ]; then
    echo "The update key is made on the Mac that releases, into its Keychain." >&2
    exit 1
fi
if held "$KEY_ITEM" || held "$PASSWORD_ITEM"; then
    echo "The Keychain already holds Idiograph's update key, so nothing was made. A key in use is never replaced." >&2
    exit 1
fi

umask 077
work=$(mktemp -d "${TMPDIR:-/tmp}/idiograph-key.XXXXXX")
trap 'rm -rf "$work"' EXIT
trap 'exit 1' INT TERM HUP
# a password of 40 letters and digits, never shown
LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 40 > "$work/password"

# Tauri's CLI, asked with no password on its command line, so it asks for one on its terminal
set -- signer generate -w "$work/update.key"
case "${IDIOGRAPH_TAURI_CLI:-}" in
    "") set -- npx --yes "@tauri-apps/cli@$CLI_VERSION" "$@" ;;
    *.js) set -- node "$IDIOGRAPH_TAURI_CLI" "$@" ;;
    *) set -- "$IDIOGRAPH_TAURI_CLI" "$@" ;;
esac
if ! python3 "$HERE/key_prompt.py" "$work/password" "$@" > "$work/generate.log" 2>&1; then
    echo "Tauri's CLI did not make the key. Its words, with no key in them:" >&2
    sed -E 's/[A-Za-z0-9+\/=]{40,}/<key>/g' "$work/generate.log" >&2
    exit 1
fi
if [ ! -s "$work/update.key" ] || [ ! -s "$work/update.key.pub" ]; then
    echo "Tauri's CLI made no key." >&2
    exit 1
fi
# the key sealed under the password made here, never one made with none, and its public half its own
if ! python3 "$HERE/key_prompt.py" --opens "$work/update.key" "$work/password" "$work/update.key.pub"; then
    exit 1
fi

if ! keep "$KEY_ITEM" "$work/update.key"; then
    echo "The Keychain did not take the key, so nothing was kept. Run this again." >&2
    exit 1
fi
if ! keep "$PASSWORD_ITEM" "$work/password"; then
    echo "The Keychain took the key but not its password. Remove $KEY_ITEM in Keychain Access, then run this again." >&2
    exit 1
fi

echo "Idiograph's update key is made and in the Keychain, as $KEY_ITEM, and its password as $PASSWORD_ITEM."
echo
echo "The public key, for \"pubkey\" in packaging/tauri/src-tauri/tauri.conf.json:"
echo
cat "$work/update.key.pub"
echo
echo
echo "Keep both in 1Password now, in one new item: in Keychain Access, find $KEY_ITEM, tick"
echo "Show password and copy it in, then the same for $PASSWORD_ITEM. Without them no update can be"
echo "signed again, and every tester would reinstall by hand."
