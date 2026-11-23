# Idiograph's updates list

People who want an email when a new version of Idiograph is out sign up on idiograph.app or in the
app's Settings. This Worker keeps their addresses in a Cloudflare D1 table, sends each a link to
confirm first (double opt-in), and lets anyone leave with the link in any email.
`packaging/updates_mail.py`, run on the Mac, sends the release email to the confirmed addresses
through Amazon SES. Nothing here is run by the app or the suite against Cloudflare or Amazon: the
suite checks the Worker in node with stand-ins (area 450) and the send script against fakes
(area 452).

The Worker is `idiograph-updates`, on two zone routes, `idiograph.app/api/updates/*` and
`www.idiograph.app/api/updates/*`. A zone route runs before the site's Worker, which is on those
hosts as custom domains, so the site's Worker stays assets-only and the sign-up form posts to its
own origin. It has no workers.dev address.

| Route | What it does |
|---|---|
| `POST /api/updates/subscribe` | `{"email", "source": "site" or "app", "version", "consent", "website"}`. Always 200 `{"ok": true}` for a well-formed sign-up, 400 `{"ok": false, "error": "email"}` for an address that is not one. The rest happens after the answer. |
| `GET /api/updates/confirm?t=` | A page with a Confirm button. Mail scanners open links, so the GET changes nothing. |
| `POST /api/updates/confirm` | The button: confirms the row. |
| `GET /api/updates/unsubscribe?t=` | A page with a Stop button. |
| `POST /api/updates/unsubscribe?t=` | Deletes the row: the button, and RFC 8058's one-click from a mail program. |
| `GET /api/updates/admin/count` | Counts only. Needs the admin token. |
| `GET /api/updates/admin/recipients` | The confirmed addresses, each with its unsubscribe link, for the send script. Needs the admin token. |
| `POST /api/updates/admin/delete` | `{"emails": [...]}`, at most 1000: deletes those rows (the suppression sweep), in ten statements of 100 sent as one D1 batch, inside the free plan's 50 queries an invocation. Needs the admin token. |

## What it keeps, and the limits

One row an address in `subscribers`: the address, lower-cased; pending or confirmed; where it came
from (site or app) and the app's version; which consent wording the person saw (the site's
form posts `updates-2026-11-23` and the app's Settings `updates-2026-11-23-app`; the Worker keeps any non-empty
string of 40 characters or fewer), which together with `source` names the exact words: the site's form and the
app's Settings each say them in their own way, so a version names one wording on the site and one in
the app, and a change to either is a new version; when it was made and confirmed; the hash of the newest confirm link's token;
and a hash of the sign-up's IP, set to null at confirmation. No raw IP and no token is kept. The
unsubscribe link is an HMAC of the row's id, worked out when needed, so there is nothing to keep for
it, and ids are never given twice.

`sends` holds one row for each sign-up the Worker acted on, by hashes alone, for the limits: one
confirmation email an hour and three a day to one address, ten sign-ups an hour from one IP, and
100 confirmation emails a day in all. Past that cap a sign-up is kept but no email goes; it is
counted in `admin/count` and gets its email when the person signs up again. Each sign-up takes its
row in one statement that counts and inserts at once (`INSERT … SELECT … WHERE (SELECT COUNT(*) …) <
limit`), and only the one whose row went in sends an email, so sign-ups sent at the same moment
cannot pass a limit together. An email SES does not take turns its row to `failed`, which no limit
counts, and the link of the email before it keeps working. A body is read no further than 2 KB (the
admin delete's, no further than its thousand addresses). A request from a
browser must come from idiograph.app or www.idiograph.app; the app's own server sends no Origin.
The form's hidden `website` field is a honeypot: when it is filled, nothing is kept.

A cron, daily at 03:17 UTC, deletes pending rows over 7 days old (their link has run out) and
`sends` rows over 2 days old.

## Setting it up, once

Every command runs from this folder, with Wrangler logged in to Adam's account (`wrangler login`),
never with a `CLOUDFLARE_API_TOKEN` in the environment.

1. `wrangler d1 create idiograph-updates --location weur`, in Western Europe, as the privacy page
   says. Its `database_id` is in `wrangler.toml` (not a secret).
2. `wrangler d1 execute idiograph-updates --remote --file schema.sql`, which makes the two tables.
3. The secrets. Wrangler keeps them in Cloudflare; none goes in any file here.
   - `openssl rand -hex 32 | wrangler secret put ADMIN_TOKEN`, and the same value into the Mac's
     Keychain for the send script: `security add-generic-password -a claude-code -s idiograph-updates-admin-token -w`
     (it asks for the value).
   - `openssl rand -hex 32 | wrangler secret put IP_SALT`
   - `openssl rand -hex 32 | wrangler secret put UNSUB_SECRET` (changing it later breaks every
     unsubscribe link already sent)
   - `openssl rand -hex 32 | wrangler secret put CONFIRM_SALT`
   - `wrangler secret put AWS_ACCESS_KEY_ID` and `wrangler secret put AWS_SECRET_ACCESS_KEY`: the
     Worker's own send-only SES key, not the Mac's.
4. `wrangler deploy`.
5. Check that both hosts reach this Worker and not the site's. A made-up path answers this Worker's
   own 404 in JSON, where the site would answer a page:

   ```
   curl -s https://idiograph.app/api/updates/nothing-here
   curl -s https://www.idiograph.app/api/updates/nothing-here
   ```

   Each answers `{"ok":false,"error":"path"}`. Then one sign-up with your own address, from the app
   or with curl (no Origin header), and the email's link.

## Reading the counts

```
read -rs IDIOGRAPH_UPDATES_TOKEN
curl -s -H "Authorization: Bearer $IDIOGRAPH_UPDATES_TOKEN" https://idiograph.app/api/updates/admin/count
```

It gives `confirmed`, `pending`, and for the last day the emails sent, the sign-ups held by an
address's limit, by the day's cap or by an IP's limit, those for an address already confirmed, and
the emails SES did not take. Without the header,
or with a wrong token, it is 401. `wrangler d1 execute idiograph-updates --remote --command "SELECT
status, COUNT(*) FROM subscribers GROUP BY status"` gives the same through Wrangler.

## How the send works

The release email is drafted from What's new and approved by Adam, then sent from the Mac with
`packaging/updates_mail.py`, which reads its three keys from the Keychain (account `claude-code`):
`idiograph-ses-mac-access-key-id`, `idiograph-ses-mac-secret-access-key` and
`idiograph-updates-admin-token`.

```
.venv/bin/python packaging/updates_mail.py --subject "Idiograph 0.9.37 is out" --body email.md
.venv/bin/python packaging/updates_mail.py --subject "Idiograph 0.9.37 is out" --body email.md --send --only <your address>
.venv/bin/python packaging/updates_mail.py --subject "Idiograph 0.9.37 is out" --body email.md --send
```

The first is a dry run: it counts the list and SES's suppression list, reads the account's limits,
shows the email as text and changes nothing. With `--send` it first deletes from the list every
address on SES's account-level suppression list (hard bounces and complaints), then sends one email
to each confirmed address with that person's own unsubscribe link in the body and in the
`List-Unsubscribe` and `List-Unsubscribe-Post` headers, paced by the account's sending rate.
`--only` sends to one address that is already confirmed, for a test, and skips the sweep. A full
send is refused until SES has given the account production access. A failed email, SES's refusal or
the network's, is counted and the run goes on (five in a row stop it); the counts are always
printed. Each email that went is recorded by its row's id, never the address, in a file per subject
under `~/Library/Application Support/Idiograph/updates-mail/`, so running the same subject again
sends only to those it missed. It follows no redirect, so the admin token goes to no other host. It
prints counts only, never an address.

## The two emails

The confirmation (`confirmationEmail` in worker.js) and the release email (`render` in
packaging/updates_mail.py) share one shape: `emailShell` and `textShell` in the Worker, `shell` and
`text_shell` in the script, which give the same bytes for the same words (area 452 checks it). It is a
table at most 600 pixels wide with inline styles, the site's paper, ink and crux orange, faces this
computer already has, and Idiograph's lockup with its Preview Edition stamp at the top. Email clients show
no SVG, so the lockup is two PNGs at twice their size, `site/holding/email/idiograph-lockup-2x.png` and its
dark twin, served by the site at https://idiograph.app/email/. `node packaging/email_lockup.mjs` draws
them again from the site's own SVG. A client that follows prefers-color-scheme shows the dark one, and the
light one sits on a solid plate of the paper's colour that holds the whole lockup and its clear space, so
the mark is never altered and shows as a plate where a client darkens the email itself. The PNGs are the only things an email loads: no font, no pixel and no counted link.

The confirmation is a one-off service email and says so, which is why it has no unsubscribe link. The
release email opens and signs off in Adam's words (`OPENING` and `SIGN_OFF` in the script), puts the
release's own text between them, and ends with the person's own Stop these emails link.

## Files

| File | What it does |
|---|---|
| `worker.js` | The Worker: the routes above, the limits, the pages, the confirmation email, SigV4 signing for SES, and the cron. |
| `wrangler.toml` | Names the Worker, its two routes, the cron, the D1 binding and the secrets it needs. |
| `schema.sql` | The `subscribers` and `sends` tables and their indexes. |
| `test/run.mjs` | The Worker's checks in node, with node's SQLite in place of D1 and nothing sent. |
| `test/sigv4_vectors.json` | AWS's published SigV4 test vectors, which both signers are checked against. |
