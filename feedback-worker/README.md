# Idiograph feedback collector

The bug in Idiograph's top bar sends a tester's note to this: a Cloudflare Worker on the free tier
that writes each note as one row of a Cloudflare D1 table, an SQLite database, for you to read from
time to time. The app's own server posts to it, never the browser, so the Worker allows no CORS.

A row holds the note, the reply address the tester chose to give, the app's version, the system in
plain words, the screen the note came from as one word of a fixed list, `home`, `project`,
`statements`, `pets`, `gets`, `sift`, `searches` or `trace`, and empty for anything else, the
browser's user agent, the time the Worker received it, and a hash of the sender's IP with a salt, so no raw IP is kept. The
hash also counts the notes from one sender, at most 30 an hour. No cookies, no analytics.

## Setting it up, once

Every command runs from this folder, `Tools/idiograph/feedback-worker/`.

1. A Cloudflare account, the free plan. Sign up at dash.cloudflare.com.
2. Wrangler, Cloudflare's command line: `npm i -g wrangler`, or put `npx` before every `wrangler`
   below and nothing needs installing.
3. `wrangler login`, which opens the browser once to let wrangler act for the account.
4. `wrangler d1 create idiograph-feedback`. It prints a block with a `database_id`. Put that id in
   `wrangler.toml` in place of `PUT-THE-ID-FROM-WRANGLER-D1-CREATE-HERE`. The id is not a secret.
5. `wrangler d1 execute idiograph-feedback --remote --file schema.sql`, which makes the `notes`
   table.
6. Two secrets, each any long random string. `openssl rand -hex 32` makes one.
   - `wrangler secret put ADMIN_TOKEN` and paste one at the prompt. It is what reads the notes over
     the web, so keep it in your password manager.
   - `openssl rand -hex 32 | wrangler secret put IP_SALT`. Nobody needs to know this one.

   Wrangler keeps both in Cloudflare. Neither goes in any file here.
7. `wrangler deploy`. It prints the Worker's address, in the form
   `https://idiograph-feedback.<your-subdomain>.workers.dev`.
8. The app's collector address is that address with `/v1/feedback` after it. Put it in
   `FEEDBACK_URL` near the end of `Tools/idiograph/server.py` so every copy of the app carries it,
   or in `config.json` as `"feedback_url"` for one machine only. Restart the app's server, and the
   bug appears in every bar.

## Trying it

One note by hand, which lands as a row like any other:

```
curl -s -X POST https://idiograph-feedback.<your-subdomain>.workers.dev/v1/feedback \
  -H "content-type: application/json" \
  -d '{"text": "A test note from curl", "screen": "statements", "version": "0.9.0"}'
```

It answers `{"ok":true,"id":1}`. A body that is not JSON, or has no `text`, or runs over 8 KB, is
refused with a short JSON error, and so is any method but POST and GET.

## Reading the notes

`./notes.sh` prints the newest 200 as a table in the terminal, `./notes.sh --since 7` only the last
seven days, and `./notes.sh --md notes.md` writes them as a Markdown table to keep. It goes through
`wrangler login`, so it needs no token.

Over the web the notes need the admin token in a header, never in the address. Read the token into
the shell without it reaching the history, then ask:

```
read -rs IDIOGRAPH_NOTES_TOKEN
curl -s -H "Authorization: Bearer $IDIOGRAPH_NOTES_TOKEN" \
  https://idiograph-feedback.<your-subdomain>.workers.dev/v1/notes
curl -s -H "Authorization: Bearer $IDIOGRAPH_NOTES_TOKEN" \
  "https://idiograph-feedback.<your-subdomain>.workers.dev/v1/notes?format=html" > notes.html
open notes.html
```

The first gives JSON, the second a plain table in the app's faces. Without the header, or with a
wrong token, both answer 401.

## Files

| File | What it does |
|---|---|
| `worker.js` | The Worker: `POST /v1/feedback` stores a note, `GET /v1/notes` lists them for the token. |
| `wrangler.toml` | Names the Worker `idiograph-feedback` and binds the D1 database as `DB`. |
| `schema.sql` | The `notes` table and the index the hourly limit reads. |
| `notes.sh` | The newest notes in the terminal, or as a Markdown file, through wrangler. |

Idiograph's suite checks `worker.js` with node and a stand-in for D1, and never reaches Cloudflare.
