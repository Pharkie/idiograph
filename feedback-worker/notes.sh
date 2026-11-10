#!/bin/sh
# The newest feedback notes, read straight from the D1 table through wrangler.
#
#   ./notes.sh                   the newest 200 notes as a table in the terminal
#   ./notes.sh --since 7         only those of the last seven days
#   ./notes.sh --md notes.md     the same notes as a Markdown table, written to notes.md
#
# It reads and never writes the table. It runs from anywhere, since it finds wrangler.toml beside
# itself, and needs `wrangler login` once on this machine and no token.
set -eu

since=""
md=""
while [ $# -gt 0 ]; do
  case "$1" in
    --since)
      [ $# -ge 2 ] || { echo "--since needs a number of days." >&2; exit 2; }
      since="$2"; shift 2 ;;
    --md)
      [ $# -ge 2 ] || { echo "--md needs a file to write." >&2; exit 2; }
      md="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,9p' "$0"; exit 0 ;;
    *)
      echo "Unknown option $1. Try --help." >&2; exit 2 ;;
  esac
done

case "$since" in
  "") where="" ;;
  *[!0-9]*) echo "--since takes a whole number of days." >&2; exit 2 ;;
  *) where="WHERE at >= strftime('%Y-%m-%dT%H:%M:%fZ', 'now', '-$since days') " ;;
esac

# the Markdown file lands where it was named from, before the move to this folder. A path that starts
# at a drive letter or a backslash, as Windows writes one under Git's sh, is whole already
if [ -n "$md" ]; then
  case "$md" in
    /*|[A-Za-z]:*|\\*) ;;
    *) md="$PWD/$md" ;;
  esac
fi

cd "$(dirname "$0")"
if command -v wrangler >/dev/null 2>&1; then
  wrangler() { command wrangler "$@"; }
else
  wrangler() { npx wrangler "$@"; }
fi

if [ -z "$md" ]; then
  wrangler d1 execute idiograph-feedback --remote \
    --command "SELECT id, at, screen, version, contact, text FROM notes ${where}ORDER BY id DESC LIMIT 200"
  exit 0
fi

held="$(mktemp)"
trap 'rm -f "$held"' EXIT
wrangler d1 execute idiograph-feedback --remote --json \
  --command "SELECT id, at, text, contact, version, platform, screen, agent FROM notes ${where}ORDER BY id DESC LIMIT 200" > "$held"
node -e '
const fs = require("fs");
const data = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
const rows = ((Array.isArray(data) ? data[0] : data) || {}).results || [];
const cols = ["id", "at", "text", "contact", "version", "platform", "screen", "agent"];
const cell = (v) => String(v == null ? "" : v).replace(/\\/g, "\\\\").replace(/\|/g, "\\|").replace(/\r?\n/g, "<br>");
const count = rows.length === 1 ? "One note" : `${rows.length} notes`;
const out = ["# Idiograph feedback", "", `${count}, newest first, read ${new Date().toISOString()}.`, "",
  `| ${cols.join(" | ")} |`, `|${cols.map(() => " --- ").join("|")}|`];
for (const r of rows) out.push(`| ${cols.map((c) => cell(r[c])).join(" | ")} |`);
process.stdout.write(out.join("\n") + "\n");
' "$held" > "$md"
echo "Wrote $md"
