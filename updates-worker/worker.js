/* Idiograph's updates list: a Cloudflare Worker that keeps the addresses of people who asked for an
   email when a new version is out, each confirmed by a link in an email first (double opt-in), in
   one D1 table. It runs on idiograph.app/api/updates/ and www.idiograph.app/api/updates/ as zone
   routes, which Cloudflare runs before the site's own Worker on those hosts.

     POST /api/updates/subscribe    {"email", "source", "version", "consent", "website"}: always 200
                                    {"ok": true} for a well-formed request, 400 {"ok": false, "error":
                                    "email"} for an address that is not one. The rest happens after
                                    the answer, through ctx.waitUntil, so the answer and its time say
                                    nothing about whether the address is already on the list.
     GET  /api/updates/confirm?t=   a page with a Confirm button; mail scanners follow links, so a
                                    GET changes nothing
     POST /api/updates/confirm      the button: t in the form's body confirms the pending row
     GET  /api/updates/unsubscribe?t=  a page with a Leave button
     POST /api/updates/unsubscribe?t=  deletes the row: the page's button, and RFC 8058's one-click,
                                    whose body is List-Unsubscribe=One-Click and whose token is in the
                                    address
     GET  /api/updates/admin/count       counts only
     GET  /api/updates/admin/recipients  the confirmed addresses with their unsubscribe links, for
                                    packaging/updates_mail.py alone
     POST /api/updates/admin/delete      {"emails": [...]}: deletes those rows (the suppression sweep)

   The admin routes need `Authorization: Bearer <ADMIN_TOKEN>`, never a token in the address.

   The limits: one confirmation email an hour and three a day to one address, ten sign-ups an hour
   from one hashed IP, and 100 confirmation emails a day in all, past which a sign-up is still kept
   but no email goes out (each counted in the `sends` table, whose row a sign-up takes in one
   statement that counts and inserts at once, so sign-ups at the same moment cannot pass a limit
   together). An email SES does not take gives its place back and leaves the earlier link working. A filled honeypot (`website`) is
   answered as any other and kept nowhere. A request from a browser must come from idiograph.app or
   www.idiograph.app; the app's own server sends no Origin.

   No raw IP is kept: `ip_hash` is the SHA-256 of the IP and IP_SALT, and it is set to null when the
   address is confirmed. The confirm token is a random 32 bytes, kept only as the SHA-256 of it and
   CONFIRM_SALT, and a new email rotates it, so only the newest email's link works. The unsubscribe
   token is HMAC-SHA256(UNSUB_SECRET, the row's id), worked out when needed and kept nowhere. A cron
   deletes pending rows 7 days after their latest email, and `sends` rows after 2 days, so one can last up to
   three days, the cron being daily.

   The confirmation email goes through Amazon SES's v2 API, signed with AWS Signature Version 4 on
   WebCrypto below. Secrets, set with `wrangler secret put` and never written in a file: ADMIN_TOKEN,
   IP_SALT, UNSUB_SECRET, CONFIRM_SALT, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY. No cookies, no
   analytics, no CORS. */

const PREFIX = '/api/updates';
const MAX_BODY = 2048;             // bytes, a sign-up's or a form's whole body
const MAX_EMAIL = 254;             // characters, RFC 5321's limit on a path
const PER_ADDRESS_HOUR = 1;        // confirmation emails to one address in an hour
const PER_ADDRESS_DAY = 3;         // and in a day
const PER_IP_HOUR = 10;            // sign-ups from one hashed IP in an hour
const DAILY_CAP = 100;             // confirmation emails a day, all addresses together
const PENDING_DAYS = 7;            // an unconfirmed sign-up, and its link, last this long
const SENDS_DAYS = 2;              // the limits' own rows are kept this long
const DELETE_MAX = 1000;           // addresses one admin delete takes (packaging/updates_mail.py's DELETE_BATCH)
const DELETE_CHUNK = 100;          // addresses one DELETE statement binds: D1's limit on bound values
const ADMIN_MAX_BODY = DELETE_MAX * (MAX_EMAIL + 8) + 64;  // bytes, the longest admin delete's body
const HOUR = 3600 * 1000;
const DAY = 24 * HOUR;
const ORIGINS = ['https://idiograph.app', 'https://www.idiograph.app'];
const SOURCES = ['site', 'app'];
const FROM = 'Idiograph <hello@idiograph.app>';
const CONFIGURATION_SET = 'idiograph';

const enc = new TextEncoder();
const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');

export async function sha256Hex(data) {
  return hex(await crypto.subtle.digest('SHA-256', typeof data === 'string' ? enc.encode(data) : data));
}

async function hmac(key, text) {
  const k = await crypto.subtle.importKey('raw', typeof key === 'string' ? enc.encode(key) : key,
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  return crypto.subtle.sign('HMAC', k, enc.encode(text));
}

/* every byte compared whatever the first difference, so the time a wrong token takes says nothing */
export function same(a, b) {
  const x = enc.encode(String(a));
  const y = enc.encode(String(b));
  let diff = x.length ^ y.length;
  for (let i = 0; i < Math.max(x.length, y.length); i += 1) diff |= (x[i] || 0) ^ (y[i] || 0);
  return diff === 0;
}

/* ── AWS Signature Version 4, on WebCrypto. The suite checks it against AWS's published test vectors
   (test/sigv4_vectors.json). Paths are taken as the URL gives them, each segment decoded and encoded
   once, which is all SES's ASCII paths need. */

const rfc3986 = (s) => encodeURIComponent(s).replace(/[!'()*]/g, (c) => `%${c.charCodeAt(0).toString(16).toUpperCase()}`);

export function canonicalRequest(method, url, headers, bodyHash) {
  const u = new URL(url);
  const path = u.pathname.split('/').map((seg) => rfc3986(decodeURIComponent(seg))).join('/') || '/';
  const pairs = [];
  if (u.search.length > 1) {
    for (const part of u.search.slice(1).split('&')) {
      if (!part) continue;
      const at = part.indexOf('=');
      const k = at < 0 ? part : part.slice(0, at);
      const v = at < 0 ? '' : part.slice(at + 1);
      const dec = (s) => decodeURIComponent(s.replace(/\+/g, '%20'));
      pairs.push([rfc3986(dec(k)), rfc3986(dec(v))]);
    }
  }
  pairs.sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0));
  const named = Object.entries(headers).map(([k, v]) => [k.toLowerCase(), String(v).trim().replace(/\s+/g, ' ')]);
  named.sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
  const signed = named.map(([k]) => k).join(';');
  const text = [method, path, pairs.map(([k, v]) => `${k}=${v}`).join('&'),
    named.map(([k, v]) => `${k}:${v}\n`).join(''), signed, bodyHash].join('\n');
  return { text, signed };
}

/* The headers to send: those given, with host and x-amz-date, and the Authorization header over them. */
export async function signV4({ method, url, headers = {}, body = '', accessKeyId, secretAccessKey, region, service, amzDate }) {
  const when = amzDate || new Date(Date.now()).toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
  const day = when.slice(0, 8);
  const all = { ...headers, host: new URL(url).host, 'x-amz-date': when };
  const { text, signed } = canonicalRequest(method, url, all, await sha256Hex(body));
  const scope = `${day}/${region}/${service}/aws4_request`;
  const toSign = ['AWS4-HMAC-SHA256', when, scope, await sha256Hex(text)].join('\n');
  let key = await hmac(`AWS4${secretAccessKey}`, day);
  for (const part of [region, service, 'aws4_request']) key = await hmac(key, part);
  const signature = hex(await hmac(key, toSign));
  return {
    canonical: text,
    stringToSign: toSign,
    signature,
    headers: { ...all, authorization: `AWS4-HMAC-SHA256 Credential=${accessKeyId}/${scope}, SignedHeaders=${signed}, Signature=${signature}` },
  };
}

/* ── answers */

const json = (data, status = 200, extra = {}) => new Response(JSON.stringify(data), {
  status,
  headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', ...extra },
});
const refuse = (status, error, extra = {}) => json({ ok: false, error }, status, extra);

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/* A plain page in Idiograph's faces and colours, light or dark as the system is, with no script and
   nothing fetched. The token travels in the address, so no page sends a referrer. */
export function page(title, paragraphs, form = null, status = 200) {
  const body = paragraphs.map((p) => `<p>${p}</p>`).join('\n');
  const button = form
    ? `<form method="post" action="${esc(form.action)}">${(form.fields || []).map(([k, v]) => `<input type="hidden" name="${esc(k)}" value="${esc(v)}">`).join('')}<button type="submit">${esc(form.label)}</button></form>`
    : '';
  return new Response(`<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>${esc(title)} · Idiograph</title>
<style>
:root { --paper: #FBF7EF; --ink: #1F1B16; --ink-soft: #554C41; --rule: #E4DCCD; --crux: #B04E00; --on-crux: #FFFFFF; --crux-hover: #8F3F00;
  --serif: "Iowan Old Style", "Charter", "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif;
  --sans: "Avenir Next", "Avenir", "Gill Sans", "Gill Sans MT", "Segoe UI", system-ui, sans-serif; color-scheme: light; }
@media (prefers-color-scheme: dark) {
  :root { --paper: #16130E; --ink: #EFE7D9; --ink-soft: #B6AC9B; --rule: #3A332A; --crux: #F79646; --on-crux: #1B1206; --crux-hover: #FFB277; color-scheme: dark; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--paper); color: var(--ink); font-family: var(--sans); font-size: 16px; line-height: 1.5; }
main { max-width: 34rem; margin: 0 auto; padding: 64px 16px; }
.name { font-family: var(--serif); font-size: 15px; letter-spacing: .14em; text-transform: uppercase; color: var(--ink-soft); margin: 0 0 32px; }
.name a { color: inherit; text-decoration: none; }
h1 { font-family: var(--serif); font-weight: 400; font-size: 30px; line-height: 1.2; margin: 0 0 16px; }
p { margin: 0 0 16px; color: var(--ink-soft); }
a { color: var(--crux); }
button { font: 600 16px var(--sans); background: var(--crux); color: var(--on-crux); border: 0; border-radius: 8px; padding: 12px 24px; margin-top: 8px; cursor: pointer; }
button:hover { background: var(--crux-hover); }
button:focus-visible { outline: 2px solid var(--crux); outline-offset: 3px; }
</style></head><body><main>
<p class="name"><a href="https://idiograph.app/">Idiograph</a></p>
<h1>${esc(title)}</h1>
${body}
${button}
</main></body></html>
`, {
    status,
    headers: {
      'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store', 'referrer-policy': 'no-referrer',
      'x-content-type-options': 'nosniff',
      'content-security-policy': "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'",
    },
  });
}

/* ── the pieces of a sign-up */

/* An address as the list keeps it: trimmed and lower-cased, or null for one that is not an address. */
export function cleanEmail(value) {
  if (typeof value !== 'string') return null;
  const email = value.trim().toLowerCase();
  if (!email || email.length > MAX_EMAIL) return null;
  if (!/^[^\s@<>()[\]\\,;:"\x00-\x1f\x7f]{1,64}@[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*\.[a-z]{2,63}$/.test(email)) return null;
  if (/^\.|\.\.|\.@/.test(email)) return null;
  return email;
}

const short = (value, limit) => (typeof value === 'string' ? value.trim().slice(0, limit) : '');

export function originAllowed(request) {
  const origin = request.headers.get('origin');
  return origin === null || ORIGINS.includes(origin);
}

function randomToken() {
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  return btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

const confirmHash = (env, token) => sha256Hex(`${env.CONFIRM_SALT}:confirm:${token}`);
const ipHashOf = (env, request) => sha256Hex(`${env.IP_SALT}:ip:${request.headers.get('cf-connecting-ip') || ''}`);
const emailHashOf = (env, email) => sha256Hex(`${env.IP_SALT}:email:${email}`);

export async function unsubscribeToken(env, id) {
  return `${id}.${hex(await hmac(env.UNSUB_SECRET, `unsubscribe:${id}`))}`;
}

/* The row's id for a good unsubscribe token, or null. */
export async function unsubscribeId(env, token) {
  const found = /^([1-9]\d{0,15})\.([0-9a-f]{64})$/.exec(String(token || ''));
  if (!found || !env.UNSUB_SECRET) return null;
  return same(await unsubscribeToken(env, found[1]), found[0]) ? Number(found[1]) : null;
}

const base = (env) => (env.PUBLIC_URL || 'https://idiograph.app/api/updates').replace(/\/+$/, '');

/* ── the emails' one shape, kept in step with packaging/updates_mail.py's `shell` and `text_shell`, which give
   the same bytes for the same words (area 452 checks it). Tables and inline styles for the clients that read
   nothing else, 600 pixels at most, the site's paper, ink and crux orange, and the lockup as a PNG at twice its
   size with "Idiograph" for its alt text (packaging/email_lockup.mjs draws it). Where a client follows
   prefers-color-scheme (Apple Mail, Outlook) the email takes the site's dark colours and the lockup's dark PNG.
   Where a client darkens the email itself and leaves its images alone (Gmail's apps), the light PNG is a solid
   paper-coloured plate behind the whole lockup and its clear space, so the mark is never altered and never
   outlined. The plate holds the mark's height clear above and to its left, so the cell's padding is that much
   less. No font is fetched and nothing is counted: the two PNGs are all the email loads. */

export const EMAIL_ASSETS = 'https://idiograph.app/email';
export const LOCKUP_WIDTH = 262;   // CSS pixels: packaging/email_lockup.mjs's PNGs are twice this
export const LOCKUP_HEIGHT = 96;
export const EMAIL_SANS = "'Avenir Next',Avenir,'Segoe UI',Helvetica,Arial,sans-serif";
export const EMAIL_SERIF = "'Iowan Old Style',Charter,'Palatino Linotype',Palatino,Georgia,serif";

export const EMAIL_STYLE = `:root { color-scheme: light dark; supported-color-schemes: light dark; }
body { margin: 0 !important; padding: 0 !important; width: 100% !important; }
table { border-collapse: collapse; }
img { border: 0; outline: none; text-decoration: none; }
.lk-dark { display: none; }
@media (max-width: 480px) {
  .outer { padding: 0 !important; }
  .lead { font-size: 23px !important; }
}
@media (prefers-color-scheme: dark) {
  .bg { background: #16130E !important; }
  .ink { color: #EFE7D9 !important; }
  .soft { color: #B6AC9B !important; }
  .rule { border-color: #3A332A !important; }
  .link { color: #F79646 !important; }
  .btn { background: #F79646 !important; }
  .btn-a { color: #1B1206 !important; }
  .lk-light { display: none !important; }
  .lk-dark { display: block !important; }
}
[data-ogsb] .bg { background: #16130E !important; }
[data-ogsc] .ink { color: #EFE7D9 !important; }
[data-ogsc] .soft { color: #B6AC9B !important; }
[data-ogsc] .link { color: #F79646 !important; }
[data-ogsb] .btn { background: #F79646 !important; }
[data-ogsc] .btn-a { color: #1B1206 !important; }
[data-ogsc] .lk-light { display: none !important; }
[data-ogsc] .lk-dark { display: block !important; }`;

/* One email's HTML: the lockup, then `content` (HTML, already escaped), then `footer` (HTML) under a rule.
   `preheader` is the line an inbox shows after the subject. */
export function emailShell(title, preheader, content, footer) {
  const img = (cls, file, style) => `<img class="${cls}" src="${EMAIL_ASSETS}/${file}" width="${LOCKUP_WIDTH}" height="${LOCKUP_HEIGHT}" alt="Idiograph" style="font-family:${EMAIL_SANS};font-size:22px;color:#1F1B16;${style}">`;
  return `<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="x-apple-disable-message-reformatting">
<meta name="color-scheme" content="light dark">
<meta name="supported-color-schemes" content="light dark">
<title>${esc(title)}</title>
<style>
${EMAIL_STYLE}
</style>
</head>
<body class="bg" style="margin:0;padding:0;background:#FBF7EF;">
<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;font-size:1px;line-height:1px;color:#FBF7EF;">${esc(preheader)}</div>
<table role="presentation" class="bg" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#FBF7EF;">
<tr><td class="outer" align="center" style="padding:16px 12px;">
<!--[if mso]><table role="presentation" width="600" align="center" cellpadding="0" cellspacing="0" border="0"><tr><td><![endif]-->
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;">
<tr><td style="padding:9px 5px 32px 5px;">
<a href="https://idiograph.app" style="text-decoration:none;">${img('lk-light', 'idiograph-lockup-2x.png', `display:block;width:${LOCKUP_WIDTH}px;height:auto;`)}<!--[if !mso]><!-->${img('lk-dark', 'idiograph-lockup-dark-2x.png', `display:none;width:${LOCKUP_WIDTH}px;height:auto;`)}<!--<![endif]--></a>
</td></tr>
<tr><td class="ink" style="padding:0 36px;font-family:${EMAIL_SANS};font-size:17px;line-height:1.6;color:#1F1B16;">
${content}
</td></tr>
<tr><td style="padding:12px 36px 40px 36px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td class="rule soft" style="border-top:1px solid #E4DCCD;padding-top:20px;font-family:${EMAIL_SANS};font-size:14px;line-height:1.55;color:#554C41;">
${footer}
<p style="margin:12px 0 0;"><a class="soft" href="https://idiograph.app" style="color:#554C41;">idiograph.app</a></p>
</td></tr></table>
</td></tr>
</table>
<!--[if mso]></td></tr></table><![endif]-->
</td></tr>
</table>
</body>
</html>
`;
}

/* One email's plain text: the words, then the footer under a rule. */
export function textShell(content, footer) {
  return `${content.trim()}\n\n-- \n${footer.trim()}\nhttps://idiograph.app\n`;
}

/* The confirmation, a one-off service email: a thank-you, what they will get, one button, and why it came. */
export const CONFIRMATION = {
  subject: 'Confirm your sign-up for Idiograph news',
  opening: 'Thank you for signing up for news of Idiograph.',
  ask: 'Please confirm that this is your email address. After that, you will get news of Idiograph and its new versions, a few emails a year.',
  button: 'Confirm this email address',
  after: 'The button opens a page on idiograph.app, where you press Confirm once more. It works for 7 days.',
  fallback: 'If the button does not work, copy this link into your browser:',
  footer: 'This is a one-off service email, so it has no unsubscribe link. It was sent because this address was entered at idiograph.app. If that was not you, you do not need to do anything. No more emails will come unless the address is confirmed.',
};

export function confirmationEmail(link) {
  const c = CONFIRMATION;
  // the text has a link where the HTML has a button, and says so
  const text = textShell([c.opening, '', c.ask, '', `${c.button}:`, link, '', c.after.replace('The button', 'The link')].join('\n'), c.footer);
  const soft = 'margin:0 0 12px;font-size:15px;line-height:1.55;color:#554C41;';
  const content = [
    `<h1 class="lead ink" style="margin:0 0 20px;font-family:${EMAIL_SERIF};font-weight:400;font-size:26px;line-height:1.3;color:#1F1B16;">${esc(c.opening)}</h1>`,
    `<p style="margin:0 0 24px;">${esc(c.ask)}</p>`,
    '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 28px;"><tr>'
      + '<td class="btn" bgcolor="#B04E00" style="border-radius:8px;background:#B04E00;mso-padding-alt:14px 28px;">'
      + `<a class="btn-a" href="${esc(link)}" style="display:inline-block;padding:14px 28px;font-family:${EMAIL_SANS};font-size:17px;font-weight:600;line-height:1.2;color:#FFFFFF;text-decoration:none;border-radius:8px;">${esc(c.button)}</a>`
      + '</td></tr></table>',
    `<p class="soft" style="${soft}">${esc(c.after)}</p>`,
    `<p class="soft" style="${soft}margin-bottom:20px;">${esc(c.fallback)}<br><a class="link" href="${esc(link)}" style="color:#B04E00;word-break:break-all;">${esc(link)}</a></p>`,
  ].join('\n');
  const html = emailShell(c.subject, c.ask, content, `<p style="margin:0;">${esc(c.footer)}</p>`);
  return { subject: c.subject, text, html };
}

/* One email through SES v2's SendEmail, from hello@idiograph.app, in the configuration set. Answers
   whether SES took it. */
export async function sendEmail(env, to, { subject, text, html, headers = [] }) {
  const region = env.SES_REGION || 'eu-west-2';
  const url = `${(env.SES_ENDPOINT || `https://email.${region}.amazonaws.com`).replace(/\/+$/, '')}/v2/email/outbound-emails`;
  const body = JSON.stringify({
    FromEmailAddress: FROM,
    Destination: { ToAddresses: [to] },
    Content: {
      Simple: {
        Subject: { Data: subject, Charset: 'UTF-8' },
        Body: { Text: { Data: text, Charset: 'UTF-8' }, Html: { Data: html, Charset: 'UTF-8' } },
        ...(headers.length ? { Headers: headers } : {}),
      },
    },
    ConfigurationSetName: CONFIGURATION_SET,
  });
  const signed = await signV4({
    method: 'POST', url, headers: { 'content-type': 'application/json' }, body,
    accessKeyId: env.AWS_ACCESS_KEY_ID, secretAccessKey: env.AWS_SECRET_ACCESS_KEY, region, service: 'ses',
  });
  const { host, ...sent } = signed.headers;  // fetch sets Host itself
  const answer = await fetch(url, { method: 'POST', headers: sent, body });
  return answer.ok;
}

/* Everything after the answer: the limits, the row, and the email. `held` on the sends row says why no
   email went, or is '' when one did.

   Each sign-up's place under the limits is taken by one statement, which counts and inserts at once:
   D1 runs one statement at a time, so a hundred sign-ups at the same moment cannot all read the same
   count before any of them writes. Only the sign-up whose row went in with held '' sends an email. A
   row that went in another way says which limit held it ('ip', 'address' or 'cap'), and an email SES
   did not take turns its row to 'failed', which no limit counts, so it can be tried again. */
export async function signUp(env, { email, source, version, consent, ipHash, now = Date.now() }) {
  const at = new Date(now).toISOString();
  const emailHash = await emailHashOf(env, email);
  const db = env.DB;
  const hourAgo = new Date(now - HOUR).toISOString();
  const dayAgo = new Date(now - DAY).toISOString();
  // a sign-up held by the IP limit is counted but never counts towards it, nor does a failed email
  const ipOk = `(SELECT COUNT(*) FROM sends WHERE ip_hash = ?1 AND held NOT IN ('ip', 'failed') AND at > ?4) < ${PER_IP_HOUR}`;
  const addressOk = `(SELECT COUNT(*) FROM sends WHERE email_hash = ?2 AND held = '' AND at > ?4) < ${PER_ADDRESS_HOUR}`
    + ` AND (SELECT COUNT(*) FROM sends WHERE email_hash = ?2 AND held = '' AND at > ?5) < ${PER_ADDRESS_DAY}`;
  const capOk = `(SELECT COUNT(*) FROM sends WHERE held = '' AND at > ?5) < ${DAILY_CAP}`;
  const insert = (held, where) => {
    // ?1 to ?5 name the values below; each becomes a plain ? with its value in order
    const values = [ipHash, emailHash, at, hourAgo, dayAgo];
    const args = [];
    const sql = `INSERT INTO sends (email_hash, ip_hash, at, held) SELECT ?2, ?1, ?3, ${held} WHERE ${where}`
      .replace(/\?(\d)/g, (_, n) => { args.push(values[Number(n) - 1]); return '?'; });
    return db.prepare(sql).bind(...args).run();
  };

  const row = await db.prepare('SELECT id, status FROM subscribers WHERE email = ?').bind(email).first();
  if (row && row.status === 'confirmed') {
    await insert(`CASE WHEN ${ipOk} THEN 'confirmed' ELSE 'ip' END`, '1');
    return 'confirmed';
  }
  const reserved = await insert("''", `${ipOk} AND ${addressOk} AND ${capOk}`);
  const sendId = Number(reserved?.meta?.changes || 0) === 1 ? reserved.meta.last_row_id : null;
  let held = '';
  if (sendId === null) {
    // held: which limit, in one statement too. Never '' here, even if a count moved in between.
    const labelled = await insert(`CASE WHEN NOT (${ipOk}) THEN 'ip' WHEN NOT (${addressOk}) THEN 'address' ELSE 'cap' END`, '1');
    const last = await db.prepare('SELECT held FROM sends WHERE id = ?').bind(labelled?.meta?.last_row_id ?? -1).first();
    held = last?.held || 'cap';
    if (held === 'ip') return 'ip';  // nothing kept but the count, and the answer was the same as any other
  }
  // a new address is kept pending, with no link that works until its email has gone
  await db.prepare('INSERT INTO subscribers (email, status, source, version, consent, created_at, token_hash, ip_hash) '
    + "VALUES (?, 'pending', ?, ?, ?, ?, NULL, ?) ON CONFLICT (email) DO NOTHING")
    .bind(email, source, version, consent, at, ipHash).run();
  if (sendId === null) return held;

  const token = randomToken();
  const mail = confirmationEmail(`${base(env)}/confirm?t=${encodeURIComponent(token)}`);
  let took = false;
  try {
    took = await sendEmail(env, email, mail);
    if (!took) console.error('updates: SES refused a confirmation email');
  } catch {
    console.error('updates: the confirmation email could not be sent');
  }
  if (!took) {
    // the allowance is given back and the link already sent, if any, still works
    await db.prepare("UPDATE sends SET held = 'failed' WHERE id = ?").bind(sendId).run();
    return 'failed';
  }
  // the email went: its link is the only one that works from now on, and its 7 days start now
  await db.prepare('UPDATE subscribers SET source = ?, version = ?, consent = ?, created_at = ?, token_hash = ?, ip_hash = ? '
    + "WHERE email = ? AND status = 'pending'").bind(source, version, consent, at, await confirmHash(env, token), ipHash, email).run();
  return 'mailed';
}

/* At most `limit` bytes of the body, read from the stream itself and stopped there, whatever
   Content-Length says or does not say: null for a longer body. */
async function readBody(request, limit = MAX_BODY) {
  if (Number(request.headers.get('content-length') || 0) > limit) return null;
  if (!request.body) return '';
  const reader = request.body.getReader();
  const parts = [];
  let size = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > limit) {
      await reader.cancel().catch(() => {});
      return null;
    }
    parts.push(value);
  }
  const all = new Uint8Array(size);
  let at = 0;
  for (const p of parts) { all.set(p, at); at += p.byteLength; }
  return new TextDecoder().decode(all);
}

async function subscribe(request, env, ctx) {
  if (!originAllowed(request)) return refuse(403, 'origin');
  const raw = await readBody(request);
  if (raw === null) return refuse(413, 'size');
  let body;
  try {
    body = JSON.parse(raw);
  } catch {
    return refuse(400, 'body');
  }
  if (!body || typeof body !== 'object' || Array.isArray(body)) return refuse(400, 'body');
  const email = cleanEmail(body.email);
  if (!email) return refuse(400, 'email');
  const consent = short(body.consent, 40);
  if (!consent) return refuse(400, 'consent');
  if (body.website !== undefined && body.website !== '') return json({ ok: true });  // the honeypot: kept nowhere
  if (!env.IP_SALT || !env.CONFIRM_SALT) return refuse(500, 'setup');
  const fields = {
    email, consent, source: SOURCES.includes(body.source) ? body.source : '', version: short(body.version, 40),
    ipHash: await ipHashOf(env, request),
  };
  const later = signUp(env, fields).catch(() => console.error('updates: a sign-up could not be stored'));
  if (ctx && typeof ctx.waitUntil === 'function') ctx.waitUntil(later);
  return json({ ok: true });
}

const notValid = 'This link no longer works. It may have been used already, a newer email may have replaced it, or it is over 7 days old. You can sign up again on idiograph.app.';

async function pendingByToken(env, token, now = Date.now()) {
  if (typeof token !== 'string' || !/^[A-Za-z0-9_-]{43}$/.test(token) || !env.CONFIRM_SALT) return null;
  const since = new Date(now - PENDING_DAYS * DAY).toISOString();
  return env.DB.prepare("SELECT id FROM subscribers WHERE token_hash = ? AND status = 'pending' AND created_at > ?")
    .bind(await confirmHash(env, token), since).first();
}

async function confirmPage(env, url) {
  const token = url.searchParams.get('t') || '';
  if (!await pendingByToken(env, token)) return page('This link has expired', [esc(notValid)], null, 404);
  return page('Confirm your address', ['Press Confirm to finish signing up for news of Idiograph and its new versions.'],
    { action: `${PREFIX}/confirm`, fields: [['t', token]], label: 'Confirm' });
}

async function confirm(request, env) {
  const raw = await readBody(request);
  const token = raw === null ? '' : new URLSearchParams(raw).get('t') || '';
  const row = await pendingByToken(env, token);
  if (!row) return page('This link has expired', [esc(notValid)], null, 404);
  await env.DB.prepare("UPDATE subscribers SET status = 'confirmed', confirmed_at = ?, token_hash = NULL, ip_hash = NULL "
    + "WHERE id = ? AND status = 'pending'").bind(new Date(Date.now()).toISOString(), row.id).run();
  return page('Thank you, you are signed up', ['You will get news of Idiograph and its new versions, a few emails a year.',
    'Every email has a link to stop them.']);
}

async function unsubscribePage(env, url) {
  const token = url.searchParams.get('t') || '';
  if (await unsubscribeId(env, token) === null) return page('This link does not work', ['Check that the whole link was opened, or write to hello@idiograph.app.'], null, 404);
  return page('Stop the emails', ['Press Stop to take your address off the list. Nothing more will be sent.'],
    { action: `${PREFIX}/unsubscribe?t=${encodeURIComponent(token)}`, label: 'Stop' });
}

/* The page's button and RFC 8058's one-click alike: the token from the address, the body unread. */
async function unsubscribe(env, url) {
  const id = await unsubscribeId(env, url.searchParams.get('t') || '');
  if (id === null) return page('This link does not work', ['Check that the whole link was opened, or write to hello@idiograph.app.'], null, 404);
  await env.DB.prepare('DELETE FROM subscribers WHERE id = ?').bind(id).run();
  return page('You are off the list', ['Your address has been deleted. Nothing more will be sent.']);
}

/* the token travels in the header alone, never in the address */
function authorised(request, env) {
  const token = env.ADMIN_TOKEN;
  const found = /^Bearer\s+(\S+)$/i.exec((request.headers.get('authorization') || '').trim());
  return Boolean(token && found && same(found[1], token));
}

async function adminCount(env) {
  const n = async (sql, ...args) => Number((await env.DB.prepare(sql).bind(...args).first())?.n || 0);
  const dayAgo = new Date(Date.now() - DAY).toISOString();
  const held = async (why) => n('SELECT COUNT(*) AS n FROM sends WHERE held = ? AND at > ?', why, dayAgo);
  return json({
    ok: true,
    confirmed: await n("SELECT COUNT(*) AS n FROM subscribers WHERE status = 'confirmed'"),
    pending: await n("SELECT COUNT(*) AS n FROM subscribers WHERE status = 'pending'"),
    last_day: {
      emails: await n("SELECT COUNT(*) AS n FROM sends WHERE held = '' AND at > ?", dayAgo),
      held_address: await held('address'),
      held_cap: await held('cap'),
      held_ip: await held('ip'),
      already_confirmed: await held('confirmed'),
      failed: await held('failed'),
    },
    cap: DAILY_CAP,
  });
}

async function adminRecipients(env) {
  if (!env.UNSUB_SECRET) return refuse(500, 'setup');
  const { results } = await env.DB.prepare("SELECT id, email FROM subscribers WHERE status = 'confirmed' ORDER BY id").bind().all();
  const recipients = [];
  for (const r of results || []) {
    recipients.push({ email: r.email, unsubscribe: `${base(env)}/unsubscribe?t=${await unsubscribeToken(env, r.id)}` });
  }
  return json({ ok: true, recipients });
}

/* A thousand addresses in ten statements of a hundred, sent to D1 as one batch: the free plan allows
   50 queries in one invocation, and a statement binds at most 100 values. */
async function adminDelete(request, env) {
  const raw = await readBody(request, ADMIN_MAX_BODY);
  if (raw === null) return refuse(413, 'size');
  let body;
  try {
    body = JSON.parse(raw);
  } catch {
    return refuse(400, 'body');
  }
  if (!body || !Array.isArray(body.emails) || body.emails.length > DELETE_MAX) return refuse(400, 'emails');
  const emails = [...new Set(body.emails.map(cleanEmail).filter(Boolean))];
  const statements = [];
  for (let at = 0; at < emails.length; at += DELETE_CHUNK) {
    const chunk = emails.slice(at, at + DELETE_CHUNK);
    statements.push(env.DB.prepare(`DELETE FROM subscribers WHERE email IN (${chunk.map(() => '?').join(', ')})`).bind(...chunk));
  }
  const done = statements.length ? await env.DB.batch(statements) : [];
  const deleted = done.reduce((n, d) => n + Number(d?.meta?.changes || 0), 0);
  return json({ ok: true, deleted });
}

/* The cron: pending rows past their 7 days, and the limits' rows past 2. */
export async function clearUp(env, now = Date.now()) {
  const pending = await env.DB.prepare("DELETE FROM subscribers WHERE status = 'pending' AND created_at < ?")
    .bind(new Date(now - PENDING_DAYS * DAY).toISOString()).run();
  const sends = await env.DB.prepare('DELETE FROM sends WHERE at < ?').bind(new Date(now - SENDS_DAYS * DAY).toISOString()).run();
  return { pending: Number(pending?.meta?.changes || 0), sends: Number(sends?.meta?.changes || 0) };
}

const ROUTES = {
  'POST /subscribe': (request, env, url, ctx) => subscribe(request, env, ctx),
  'GET /confirm': (request, env, url) => confirmPage(env, url),
  'POST /confirm': (request, env) => confirm(request, env),
  'GET /unsubscribe': (request, env, url) => unsubscribePage(env, url),
  'POST /unsubscribe': (request, env, url) => unsubscribe(env, url),
  'GET /admin/count': (request, env) => adminCount(env),
  'GET /admin/recipients': (request, env) => adminRecipients(env),
  'POST /admin/delete': (request, env) => adminDelete(request, env),
};

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (!url.pathname.startsWith(`${PREFIX}/`)) return refuse(404, 'path');
    const path = url.pathname.slice(PREFIX.length);
    const route = ROUTES[`${request.method} ${path}`];
    if (!route) {
      const known = Object.keys(ROUTES).filter((k) => k.endsWith(` ${path}`)).map((k) => k.split(' ')[0]);
      return known.length ? refuse(405, 'method', { allow: known.join(', ') }) : refuse(404, 'path');
    }
    if (path.startsWith('/admin/') && !authorised(request, env)) return refuse(401, 'token', { 'www-authenticate': 'Bearer' });
    try {
      return await route(request, env, url, ctx);
    } catch {
      return refuse(500, 'store');
    }
  },
  async scheduled(event, env, ctx) {
    ctx.waitUntil(clearUp(env));
  },
};
