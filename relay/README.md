# Idiograph relay

Working together passes a project's changes, comments and boards between the computers of the people on it. Each message is sealed on the sender's computer before it leaves, and the relay keeps it until every computer on the project has read it, then deletes it. The relay cannot read anything it holds. It knows a random project id, each computer's public key, IP addresses, times, sizes and counts. It never sees names, pseudonyms, words, file names, or how many participants or boards a project has. It also sees which message carries which file, and each file's exact sealed size, since files are not padded. An invite's offer, the first message in its mailbox, is sealed under the invite's own secret and always the same size, 3,880 bytes: it carries the inviting computer's public keys, the inviter's name, when it expires, 200 keyed digests, one for each participant (its folder name with the time its workbook was made) and random ones making up the rest, so even someone holding the invite cannot count the participants, and padding.

The relay keeps an address only for the day it started a project there, to count the three a day an address may start. It deletes the address after that day.

This folder is the relay: a Cloudflare Worker, `idiograph-relay`, with one Durable Object per project as its mailbox and an R2 bucket for sealed files too large for a message. It is licensed under the GNU Affero General Public License, version 3 or later, as the rest of Idiograph is. A team or a university can run its own copy on its own Cloudflare account, and Working together then takes that relay's address.

## What it does

Every call but an invite's answers and the operator's is signed by the computer making it, with the Ed25519 key its Idiograph made when Working together was turned on. The headers are `X-Device` (the first 16 bytes of the SHA-256 of the public key, in hex), `X-Time` (Unix seconds, within five minutes of the relay's clock), `X-Nonce` (16 random bytes in hex, taken once) and `X-Sig`, the base64url signature over these lines joined by a newline: the method, the path with its query, `X-Time`, `X-Nonce`, and the SHA-256 of the body in hex. A call whose headers cannot be a signature is refused before any project is looked at, and a refused call writes nothing.

| Route | Does |
|---|---|
| `POST /relay/v1/projects` | Makes a project. The body is `{"key"}`, the lead computer's public key (base64url), the call signed with that key. Answers `{"project"}`, 32 hex. The same signed call sent again is refused, `sent before`. |
| `PUT /relay/v1/p/:id/devices` | The lead's list of every computer let in, `{"devices": [key, ...], "lead"?}`, at most 24. A computer dropped from it is refused from then on and its live socket closed, and it cannot be put back. `lead` hands the role to another computer on the list. In a project made open, a list that changes nothing answers at once and writes nothing, a changed list is taken 30 times a day (`lists today`), and a project keeps at most 200 removed computers (`too many removed`). |
| `POST /relay/v1/p/:id/messages[?blob=B]` | One sealed envelope, at most 1.5 MB, which holds a padded message of up to 1 MB. Answers `{"n"}`, its number. `blob` names a sealed file put before it, which is deleted when every computer has read this message. |
| `GET /relay/v1/p/:id/messages?after=N` | Up to 200 envelopes after N, at most 8 MB together, each `{n, device, at, body}`, with `more` when there are others. |
| `GET /relay/v1/p/:id/live` | A WebSocket that says `new N` when a message comes, up to three for each computer, the oldest closed when a fourth opens (two Idiographs on one computer share its key). It answers `ping` with `pong` without waking the Durable Object, so a quiet one costs nothing, and closes on anything else. |
| `PUT`, `GET /relay/v1/p/:id/blobs/:blob` | A sealed file up to 80 MB, kept in R2 as `p/<id>/<blob>`. The PUT names its body's SHA-256 in `X-Content-SHA256`, signed in place of the body's, and R2 refuses a body that does not match it. A name already there is refused. One computer fetches one file at most 10 times. |
| `POST /relay/v1/p/:id/seen` | `{"n"}`, the highest number this computer has read, held to the highest number given out. Whatever every computer on the list has read is deleted. One that does not move the mark writes nothing. |
| `POST /relay/v1/p/:id/invites/:invite` | Opens an invite's mailbox, signed by a computer on the project, at most 10 a project a day. |
| `POST /relay/v1/invites/:invite` | A sealed join answer of up to 4 KB, unsigned, to a mailbox a project opened. Ten to an invite, all gone seven days after it opened. The two invite routes take 30 calls a minute from one IP together (`slow down`). The app's invite and join cards ask about every 10 seconds. |
| `GET /relay/v1/invites/:invite?after=K` | The answers after the K-th. |
| `GET /relay/v1/operator/usage` | The operator's: each project's bytes of files and messages as last reported, whether it was made open, the totals against the ceilings, how many projects there are, today's new projects and the addresses they came from, today's files and today's opened invites. `Authorization: Bearer <OPERATOR_KEY>`. |
| `POST /relay/v1/operator/allow` | The operator's: `{"projects": n}`, today's allowance of new projects, 0 to 200. 0 closes the day, and a number opens it again after someone has used it up. The same key. |
| `DELETE /relay/v1/operator/p/:id` | The operator's: a project deleted, its files from R2 and its mailbox, and the counter told. The same key. |

A GET's nonce is not written down: a GET sent twice changes nothing, and a row for every look would be most of the relay's writes.

## Limits

The relay at idiograph.app is open: anyone with Idiograph starts a project, and no code is asked. Invites still decide who joins, and sealing keeps everything private. Small limits keep it inside Cloudflare's free plan. Each is one named constant in `LIMITS` in `src/worker.js`.

- Each project sends at most 100 MB a day, files and messages over 24 KB together. Files take at most 80 MB of that and 150 files, so the rest is always left for changes. A file's number is counted when it is allowed and never handed back. An upload that fails hands its bytes back.
- A message of 24 KB or less, such as a list of people, is outside the day's bytes, so it goes when larger ones cannot. A project keeps 8 MB of these waiting. Every message counts in the day's 1,000.
- One file is at most 80 MB.
- At most 250 MB of a project's files and larger messages wait on the relay, and at most 100 MB of that may be messages. A file is deleted as soon as every computer on the project has read the message that names it. Nothing unread is deleted before 90 days, and a file no message names is deleted after a day. A rule on the R2 bucket deletes any file older than 91 days besides, as a backstop to the daily alarm.
- A project with one computer on its list keeps no file and no larger message, since nobody is there to fetch them.
- The whole relay keeps at most 9 GB of files (R2) and about 4 GB of messages (the Durable Objects), worked out from the sums each project reports to the counter, and takes 20,000 files a UTC day.
- It starts at most 20 new projects a UTC day, unless the operator sets the day's allowance, and 3 from one address (an IPv6 address counts by its /56). An address starts at most 6 a minute.
- Anything older than 90 days is deleted, read or not, by each project's daily alarm. A project that holds nothing and has taken nothing for 90 days stops its alarm until its next message.

Each refusal has its own word: `day`, `day files`, `project files today`, `day messages`, `project full` (with `behind`, the computers that have not read the oldest message), `nobody to send to`, `too large`, `fetched too often`, `relay full`, `files today`, `projects today`, `projects from here`, `invites today`, `no invite`, `lists today`, `too many removed`, `slow down`, `sent before`. A project made before 18 November 2026 keeps the old limits (200 MB a file, 2 GB a day, 5,000 messages, 64 computers) and the ceilings never refuse it, though its bytes count in them.

All the Durable Objects (`Project`, `Invite`, `Operator`, kept from the relay before 18 November 2026 and no longer called, and the one `Counter`) are made in the EU (`JURISDICTION` in `wrangler.jsonc`), and the bucket is made there too.

## Abuse

To report something hosted on the relay at idiograph.app, write to hello@idiograph.app. The operator deletes a project reported as abuse with its files, using `DELETE /relay/v1/operator/p/:id`, and can close the day's new projects with `POST /relay/v1/operator/allow`.

## A relay of your own

A team or a university can run its own copy. A team's own relay is open and limited as idiograph.app's is. Change `LIMITS` in `src/worker.js` for other limits.

`src/worker.js` is the whole of it. Idiograph's side is `family/relay_transport.py`.

## Running it on your own computer

Nothing here needs a Cloudflare account.

- `node relay/test/serve.mjs --port 8860 --operator-key some-made-up-key-123 --miniflare "$(npm root -g)/wrangler/node_modules/miniflare"` runs it on `http://127.0.0.1:8860/relay/v1` with Miniflare, the engine `wrangler dev` uses, its storage in memory. `--persist DIR` keeps it in a folder. `--test-limits '{"waiting": 600000}'` lays smaller limits over the worker's own. `--script relay/test/worker_v1.js` runs the relay as it was before 18 November 2026 (with an empty `Counter` class, the first deploy step's worker), with `--codes` its operator codes, so the new one can be tried on its storage and back. Leave out `--miniflare` after `npm install miniflare` in this folder. It reads the options shape of the Miniflare in Wrangler 4.97 and of the one in 4.158 alike.
- Or `wrangler dev` from this folder, with a file `.dev.vars` beside `wrangler.jsonc` holding two lines, `JURISDICTION=` and `OPERATOR_KEY=some-made-up-key-123`. The engine on one computer has no jurisdictions, hence the empty `JURISDICTION`. The repository leaves `.dev.vars` out.

Idiograph's suite drives it from Python in area 342, `tests/areas/a342_relay.py`, and skips when this computer has no node or no Miniflare. Its later runs try the old relay and the new on one folder, each way, and bring a project's alarm to seconds.

## Deploying it

On your own Cloudflare account, with Wrangler logged in to it (`wrangler login`). The free plan is enough for a team of two to ten.

1. The bucket, in the EU: `wrangler r2 bucket create idiograph-relay-blobs --jurisdiction eu`.
2. The operator's key: one long random string (`openssl rand -hex 32` makes one). `wrangler secret put OPERATOR_KEY` and paste it at the prompt. It goes in no file. Without it the operator's routes refuse every call.
3. The route. `wrangler.jsonc` routes `idiograph.app/relay/v1/*` in the zone `idiograph.app`. For your own relay, change the pattern and the zone to a domain of yours on the same account. The relay answers only under `/relay/v1/`.
4. `wrangler deploy` from this folder. It applies the migrations in `wrangler.jsonc`, `v2` adding the counter.
5. Worth adding on Cloudflare: a rate-limiting rule on `/relay/v1/*` per IP, and an R2 lifecycle rule deleting objects after 91 days as a backstop to the daily alarm.

Working together in Idiograph then takes the address, such as `https://relay.example.ac.uk/relay/v1`. The lead's first invite starts the project there, and everyone else joins by an invite from someone already on the project.
