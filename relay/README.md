# Idiograph relay

Working together passes a project's changes, comments and boards between the computers of the people on it. Each message is sealed on the sender's computer before it leaves, and the relay keeps it until every computer on the project has read it, then deletes it. The relay cannot read anything it holds. It knows a random project id, each computer's public key, IP addresses, times, sizes and counts. It never sees names, pseudonyms, words, file names, or how many participants or boards a project has.

This folder is the relay: a Cloudflare Worker, `idiograph-relay`, with one Durable Object per project as its mailbox and an R2 bucket for sealed files too large for a message. It is licensed under the GNU Affero General Public License, version 3 or later, as the rest of Idiograph is. A team or a university can run its own copy on its own Cloudflare account, and Working together then takes that relay's address.

## What it does

Every call but an invite's is signed by the computer making it, with the Ed25519 key its Idiograph made when Working together was turned on. The headers are `X-Device` (the first 16 bytes of the SHA-256 of the public key, in hex), `X-Time` (Unix seconds, within five minutes of the relay's clock), `X-Nonce` (16 random bytes in hex, taken once) and `X-Sig`, the base64url signature over these lines joined by a newline: the method, the path with its query, `X-Time`, `X-Nonce`, and the SHA-256 of the body in hex.

| Route | Does |
|---|---|
| `POST /relay/v1/projects` | Makes a project. The body is `{"code", "key"}`: an operator code and the lead computer's public key (base64url), the call signed with that key. Answers `{"project"}`, 32 hex. |
| `PUT /relay/v1/p/:id/devices` | The lead's list of every computer let in, `{"devices": [key, ...], "lead"?}`. A computer dropped from it is refused from then on and its live socket closed, and it cannot be put back. `lead` hands the role to another computer on the list. |
| `POST /relay/v1/p/:id/messages` | One sealed envelope, at most 1.5 MB, which holds a padded message of up to 1 MB. Answers `{"n"}`, its number. |
| `GET /relay/v1/p/:id/messages?after=N` | Up to 200 envelopes after N, at most 8 MB together, each `{n, device, at, body}`, with `more` when there are others. |
| `GET /relay/v1/p/:id/live` | A WebSocket that says `new N` when a message comes. It answers `ping` with `pong` without waking the Durable Object, so a quiet one costs nothing. |
| `PUT`, `GET /relay/v1/p/:id/blobs/:blob` | A sealed file up to 200 MB, kept in R2 as `p/<id>/<blob>`. The PUT names its body's SHA-256 in `X-Content-SHA256`, signed in place of the body's, and R2 refuses a body that does not match it. |
| `POST /relay/v1/p/:id/seen` | `{"n"}`, the highest number this computer has read. Whatever every computer on the list has read is deleted. |
| `POST /relay/v1/invites/:invite` | A sealed join answer of up to 4 KB, unsigned. Ten to an invite, all gone seven days after the first, 30 calls a minute from one IP. |
| `GET /relay/v1/invites/:invite?after=K` | The answers after the K-th. |

Limits on each project: 2 GB and 5,000 messages a day. Each operator code makes at most 20 projects. Anything older than 90 days is deleted, read or not, by a daily alarm, sealed files too. All three kinds of Durable Object are made in the EU (`JURISDICTION` in `wrangler.jsonc`), and the bucket is made there too.

`src/worker.js` is the whole of it. Idiograph's side is `family/relay_transport.py`.

## Running it on your own computer

Nothing here needs a Cloudflare account.

- `node relay/test/serve.mjs --port 8860 --codes some-made-up-code-123 --miniflare "$(npm root -g)/wrangler/node_modules/miniflare"` runs it on `http://127.0.0.1:8860/relay/v1` with Miniflare, the engine `wrangler dev` uses, its storage in memory. `--persist DIR` keeps it in a folder. Leave out `--miniflare` after `npm install miniflare` in this folder. It reads the options shape of the Miniflare in Wrangler 4.97 and of the one in 4.158 alike.
- Or `wrangler dev` from this folder, with a file `.dev.vars` beside `wrangler.jsonc` holding two lines, `JURISDICTION=` and `OPERATOR_CODES=some-made-up-code-123`. The engine on one computer has no jurisdictions, hence the empty `JURISDICTION`. The repository leaves `.dev.vars` out.

Idiograph's suite drives it from Python in area 342, `tests/areas/a342_relay.py`, and skips when this computer has no node or no Miniflare.

## Deploying it

On your own Cloudflare account, with Wrangler logged in to it (`wrangler login`). The free plan is enough for a team of two to ten.

1. The bucket, in the EU: `wrangler r2 bucket create idiograph-relay-blobs --jurisdiction eu`.
2. The operator codes, the only thing that can make a project: one long random string per person who may start projects, joined by commas, each at least 16 characters (`openssl rand -hex 16` makes one). `wrangler secret put OPERATOR_CODES` and paste them at the prompt. They go in no file.
3. The route. `wrangler.jsonc` routes `idiograph.app/relay/v1/*` in the zone `idiograph.app`. For your own relay, change the pattern and the zone to a domain of yours on the same account. The relay answers only under `/relay/v1/`.
4. `wrangler deploy` from this folder.

Working together in Idiograph then takes the address, such as `https://relay.example.ac.uk/relay/v1`, and a code to make the first project. Everyone else joins by an invite from someone already on the project, and needs no code.
