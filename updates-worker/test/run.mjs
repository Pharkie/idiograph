// SPDX-License-Identifier: AGPL-3.0-or-later
/* The updates Worker's checks, in node alone, for the suite's area 450 and for trying it by hand:

     node updates-worker/test/run.mjs

   D1 is a stand-in on node's own SQLite (node:sqlite, node 22.5 and later) made from schema.sql, so
   the Worker's SQL runs as written, and it can wait a few milliseconds a query, as D1 does, so that
   sign-ups sent at the same moment interleave. `fetch` is a stand-in that records what would go to
   Amazon SES, checks its SigV4 signature with node's own crypto, and answers 200, so nothing leaves
   this computer. Everything the Worker logs is kept, and must hold no address. The clock is node's
   Date.now, moved by hand.
   Every secret is made up here, and every address is on example.com, example.org or example.net.

   It prints one JSON list of [name, passed, detail], one item a check, and exits 0 even when a check
   fails: the suite reports each. A thrown error exits 1. */

import { readFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createHash, createHmac } from 'node:crypto';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const folder = path.resolve(here, '..');
const { DatabaseSync } = await import('node:sqlite');
const mod = await import(pathToFileURL(process.argv[2] || path.join(folder, 'worker.js')).href);
const worker = mod.default;
const schema = readFileSync(path.join(folder, 'schema.sql'), 'utf8');
const vectors = JSON.parse(readFileSync(path.join(here, 'sigv4_vectors.json'), 'utf8'));

const results = [];
const check = (name, ok, detail = '') => results.push([name, Boolean(ok), ok ? '' : String(detail).slice(0, 400)]);
const sha = (text) => createHash('sha256').update(text).digest('hex');

/* D1's prepare/bind/first/all/run/batch over node:sqlite. Like D1, each statement runs whole before
   the next starts. With `lag`, each query waits a few milliseconds first, as a round trip to D1 does,
   so sign-ups at the same moment interleave between their queries. `queries` counts them, as D1's
   limit of 50 in one invocation does, a batch's statements each. */
function d1({ lag = false } = {}) {
  const db = new DatabaseSync(':memory:');
  db.exec(schema);
  const plain = (row) => (row ? { ...row } : null);
  const wait = () => (lag ? new Promise((r) => setTimeout(r, 1 + Math.floor(Math.random() * 4))) : null);
  const out = {
    raw: db,
    queries: 0,
    prepare(sql) {
      const stmt = db.prepare(sql);
      const bound = (args) => ({
        async first() { await wait(); out.queries += 1; return plain(stmt.get(...args)); },
        async all() { await wait(); out.queries += 1; return { results: stmt.all(...args).map(plain), success: true }; },
        async run() { await wait(); out.queries += 1; return this.now(); },
        now() {
          const done = stmt.run(...args);
          return { success: true, meta: { changes: Number(done.changes), last_row_id: Number(done.lastInsertRowid) } };
        },
      });
      return { bind: (...args) => bound(args), ...bound([]) };
    },
    async batch(statements) {
      await wait();
      out.queries += statements.length;
      db.exec('BEGIN');
      try {
        const done = statements.map((st) => st.now());
        db.exec('COMMIT');
        return done;
      } catch (e) {
        db.exec('ROLLBACK');
        throw e;
      }
    },
  };
  return out;
}

let clock = Date.parse('2026-12-01T09:00:00.000Z');
Date.now = () => clock;
const minutes = (n) => { clock += n * 60 * 1000; };

/* SES's side of SigV4, worked out here with node's own crypto, not the Worker's code: the signature
   must be over the very body that is sent. */
function sesSignatureHolds(url, headers, body) {
  const u = new URL(url);
  const when = headers['x-amz-date'] || '';
  const named = { 'content-type': headers['content-type'], host: u.host, 'x-amz-date': when };
  const names = Object.keys(named).sort();
  const canonical = ['POST', u.pathname, '', names.map((k) => `${k}:${named[k]}\n`).join(''), names.join(';'), sha(body)].join('\n');
  const scope = `${when.slice(0, 8)}/eu-west-2/ses/aws4_request`;
  const toSign = ['AWS4-HMAC-SHA256', when, scope, sha(canonical)].join('\n');
  let key = createHmac('sha256', `AWS4${secrets.AWS_SECRET_ACCESS_KEY}`).update(when.slice(0, 8)).digest();
  for (const part of ['eu-west-2', 'ses', 'aws4_request']) key = createHmac('sha256', key).update(part).digest();
  const signature = createHmac('sha256', key).update(toSign).digest('hex');
  return headers.authorization === `AWS4-HMAC-SHA256 Credential=${secrets.AWS_ACCESS_KEY_ID}/${scope}, SignedHeaders=${names.join(';')}, Signature=${signature}`;
}

const mail = [];
let sesAnswer = 200;
let sesGate = null;        // a promise SES's answer waits on
let sesThrows = false;     // the network fails instead of answering
let onSend = null;         // runs while SES is answering
const signatures = { checked: 0, bad: 0 };
globalThis.fetch = async (url, init = {}) => {
  const headers = init.headers || {};
  signatures.checked += 1;
  if (!sesSignatureHolds(String(url), headers, init.body || '')) signatures.bad += 1;
  if (sesGate) await sesGate;
  if (sesThrows) throw new TypeError('network connection lost');
  mail.push({ url: String(url), headers, body: JSON.parse(init.body || '{}') });
  if (onSend) await onSend();
  return new Response('{"MessageId":"made-up"}', { status: sesAnswer });
};

/* Everything the Worker logs, which must never hold an address. Only the last line, the results, is
   printed. */
const logged = [];
const print = console.log.bind(console);
for (const level of ['error', 'warn', 'log', 'info', 'debug']) {
  console[level] = (...args) => { logged.push(args.map(String).join(' ')); };
}

const secrets = {
  ADMIN_TOKEN: 'made-up-admin-value-0123456789', IP_SALT: 'made-up-ip-salt', UNSUB_SECRET: 'made-up-unsub-secret',
  CONFIRM_SALT: 'made-up-confirm-salt', AWS_ACCESS_KEY_ID: 'AKIDMADEUPFORTESTS', AWS_SECRET_ACCESS_KEY: 'made-up-aws-secret',
  PUBLIC_URL: 'https://idiograph.app/api/updates', SES_ENDPOINT: 'https://ses.test',
};
let env = { DB: d1(), ...secrets };
const host = 'https://idiograph.app/api/updates';
const cors = [];

async function hit(request, e = env) {
  const waits = [];
  const res = await worker.fetch(request, e, { waitUntil: (p) => waits.push(p) });
  await Promise.all(waits);
  cors.push(res.headers.get('access-control-allow-origin'));
  return res;
}
const subscribe = (body, { ip = '203.0.113.7', origin = 'https://idiograph.app', e = env, raw = null } = {}) => hit(new Request(`${host}/subscribe`, {
  method: 'POST',
  headers: { 'content-type': 'application/json', 'cf-connecting-ip': ip, ...(origin ? { origin } : {}) },
  body: raw ?? JSON.stringify(body),
}), e);
const signup = (email, extra = {}) => ({ email, source: 'site', version: '', consent: 'updates-2026-11-23', website: '', ...extra });
const rows = (e = env) => e.DB.raw.prepare('SELECT * FROM subscribers ORDER BY id').all().map((r) => ({ ...r }));
const row = (email, e = env) => rows(e).find((r) => r.email === email);
const sends = (e = env) => e.DB.raw.prepare('SELECT * FROM sends ORDER BY id').all().map((r) => ({ ...r }));
const tokenOf = (m) => decodeURIComponent(/confirm\?t=([A-Za-z0-9_%-]+)/.exec(m.body.Content.Simple.Body.Text.Data)[1]);
const admin = (route, init = {}, token = secrets.ADMIN_TOKEN) => hit(new Request(`${host}/admin/${route}`, {
  ...init, headers: { ...(token === null ? {} : { authorization: `Bearer ${token}` }), ...(init.headers || {}) },
}));

// ── SigV4 against AWS's own vectors
const sigv4 = [];
for (const v of vectors.vectors) {
  const signed = await mod.signV4({
    method: v.method, url: v.url, headers: v.headers, body: v.body, amzDate: v.amz_date,
    accessKeyId: vectors.access_key_id, secretAccessKey: vectors.secret_access_key, region: vectors.region, service: vectors.service,
  });
  sigv4.push([v.name, signed.canonical === v.canonical, signed.stringToSign === v.string_to_sign, signed.signature === v.signature]);
}
check('SigV4: each of AWS\'s published test vectors gives AWS\'s canonical request, string to sign and signature',
  sigv4.length >= 7 && sigv4.every(([, a, b, c]) => a && b && c), JSON.stringify(sigv4.filter(([, a, b, c]) => !(a && b && c))));

// ── a sign-up from the site
let r = await subscribe(signup('  Reader.One@Example.COM '));
const answerNew = [r.status, await r.text()];
let one = row('reader.one@example.com');
check('a sign-up from idiograph.app answers 200 {"ok": true} and keeps one pending row, the address trimmed and lower-cased',
  answerNew[0] === 200 && answerNew[1] === '{"ok":true}' && rows().length === 1 && one && one.status === 'pending'
  && one.source === 'site' && one.consent === 'updates-2026-11-23' && one.confirmed_at === null, JSON.stringify([answerNew, rows()]));
check('the row keeps the SHA-256 of the IP and the salt, never the IP',
  one.ip_hash === sha(`${secrets.IP_SALT}:ip:203.0.113.7`) && !JSON.stringify(rows()).includes('203.0.113.7'), one.ip_hash);
const first = mail[0];
const token1 = first && tokenOf(first);
check('one confirmation email goes to SES v2 SendEmail, from Idiograph <hello@idiograph.app>, in configuration set idiograph, to that address alone',
  mail.length === 1 && first.url === 'https://ses.test/v2/email/outbound-emails'
  && first.body.FromEmailAddress === 'Idiograph <hello@idiograph.app>' && first.body.ConfigurationSetName === 'idiograph'
  && JSON.stringify(first.body.Destination) === '{"ToAddresses":["reader.one@example.com"]}', JSON.stringify(first && first.body).slice(0, 300));
const day = new Date(clock).toISOString().slice(0, 10).replace(/-/g, '');
check('the request to SES is signed with SigV4 for eu-west-2 and ses, over content-type, host and x-amz-date',
  new RegExp(`^AWS4-HMAC-SHA256 Credential=AKIDMADEUPFORTESTS/${day}/eu-west-2/ses/aws4_request, SignedHeaders=content-type;host;x-amz-date, Signature=[0-9a-f]{64}$`)
    .test(first.headers.authorization || '') && /^\d{8}T\d{6}Z$/.test(first.headers['x-amz-date'] || ''), first.headers.authorization);
const simple = first.body.Content.Simple;
check('the email has a subject, plain text and HTML, each with the thank-you, the confirm link, what they will get, and why it came with no unsubscribe link',
  simple.Subject.Data === 'Confirm your sign-up for Idiograph news' && [simple.Body.Text.Data, simple.Body.Html.Data].every((t) => t.includes('https://idiograph.app/api/updates/confirm?t=')
    && t.includes('Thank you for signing up for news of Idiograph.')
    && t.includes('news of Idiograph and its new versions, a few emails a year')
    && t.includes('This is a one-off service email, so it has no unsubscribe link.')
    && t.includes('No more emails will come unless the address is confirmed.')
    && t.includes('Confirm this email address') && !/\bmy\b/i.test(t)
    && !/probably you|someone/i.test(t)), simple.Body.Text.Data);
{
  const h = simple.Body.Html.Data;
  const loads = [...h.matchAll(/\b(?:src|background)=["']?([^"' >]+)/g)].map((m) => m[1]);
  check('the confirmation is the shared shape: the lockup PNGs from idiograph.app/email with alt "Idiograph", one Confirm button, the dark-mode meta tags and styles, and nothing else loaded',
    JSON.stringify(loads) === JSON.stringify(['https://idiograph.app/email/idiograph-lockup@2x.png', 'https://idiograph.app/email/idiograph-lockup-dark@2x.png'])
    && (h.match(/alt="Idiograph"/g) || []).length === 2 && (h.match(/class="btn-a"/g) || []).length === 1
    && h.includes('<meta name="color-scheme" content="light dark">') && h.includes('<meta name="supported-color-schemes" content="light dark">')
    && h.includes('@media (prefers-color-scheme: dark)') && h.includes('[data-ogsc] .lk-dark') && h.includes('max-width:600px')
    && !/@import|<link\b|fonts\.googleapis|<script|url\(/i.test(h), JSON.stringify(loads));
  check('no semicolon in the words of the confirmation, and no exclamation mark',
    !/[;!]/.test(simple.Body.Text.Data.replace(/https?:\/\/\S+/g, '')) && !/[;!]/.test(simple.Subject.Data), simple.Body.Text.Data);
}
check('the confirm token is 32 random bytes, kept only as the SHA-256 of it and CONFIRM_SALT',
  /^[A-Za-z0-9_-]{43}$/.test(token1) && one.token_hash === sha(`${secrets.CONFIRM_SALT}:confirm:${token1}`)
  && !JSON.stringify(rows()).includes(token1), one.token_hash);

// ── what is refused, and what is answered the same
const bad = ['not an address', 'a@b', `${'x'.repeat(250)}@example.com`, 'a b@example.com', '<a@example.com>', 'a@example.com\r\nBcc: b@example.org',
  'a..b@example.com', '.a@example.com', 'a@-example.com'];
const badAnswers = [];
for (const email of bad) { r = await subscribe(signup(email)); badAnswers.push([r.status, (await r.json()).error]); }
r = await subscribe(signup(42)); badAnswers.push([r.status, (await r.json()).error]);
check('an address that is not one, or is over 254 characters, is 400 {"error": "email"} and nothing is kept or sent',
  badAnswers.every(([s, e]) => s === 400 && e === 'email') && rows().length === 1 && mail.length === 1 && sends().length === 1, JSON.stringify(badAnswers));
const malformed = [];
for (const raw of ['not json', '[1]', 'null']) { r = await subscribe(null, { raw }); malformed.push([r.status, (await r.json()).error]); }
r = await subscribe(signup('reader.two@example.org', { consent: '' })); malformed.push([r.status, (await r.json()).error]);
r = await subscribe(null, { raw: JSON.stringify(signup('reader.two@example.org', { version: 'x'.repeat(3000) })) }); malformed.push([r.status, (await r.json()).error]);
check('a body that is not a JSON object, a sign-up with no consent wording, and a body over 2 KB are refused, and nothing is kept',
  JSON.stringify(malformed) === '[[400,"body"],[400,"body"],[400,"body"],[400,"consent"],[413,"size"]]' && rows().length === 1, JSON.stringify(malformed));

r = await subscribe(signup('reader.two@example.org'), { origin: 'https://elsewhere.example.net' });
const foreign = [r.status, (await r.json()).error];
r = await subscribe(signup('reader.two@example.org'), { origin: 'null' });
foreign.push(r.status);
check('a browser\'s request from any other origin is refused with 403 and nothing is kept or sent',
  foreign[0] === 403 && foreign[1] === 'origin' && foreign[2] === 403 && rows().length === 1 && mail.length === 1, JSON.stringify(foreign));
r = await subscribe(signup('reader.three@example.org', { source: 'app', version: '0.9.36' }), { origin: null, ip: '198.51.100.20' });
const fromApp = [r.status, row('reader.three@example.org')];
r = await subscribe(signup('reader.four@example.org'), { origin: 'https://www.idiograph.app', ip: '198.51.100.21' });
check('the app\'s own server, with no Origin, and www.idiograph.app are taken, the app\'s row keeping its source and version',
  fromApp[0] === 200 && fromApp[1] && fromApp[1].source === 'app' && fromApp[1].version === '0.9.36' && r.status === 200
  && row('reader.four@example.org') && mail.length === 3, JSON.stringify(fromApp));

const beforeHoney = [rows().length, sends().length, mail.length];
r = await subscribe(signup('bot@example.net', { website: 'https://spam.example.net' }), { ip: '192.0.2.50' });
const honey = [r.status, await r.text()];
check('a filled honeypot is answered as any sign-up is, and nothing is kept, counted or sent',
  honey[0] === 200 && honey[1] === '{"ok":true}' && JSON.stringify([rows().length, sends().length, mail.length]) === JSON.stringify(beforeHoney), JSON.stringify(honey));

// ── the per-address limit, and the token's rotation
const oldHash = row('reader.one@example.com').token_hash;
minutes(10);
r = await subscribe(signup('reader.one@example.com'));
const again = [r.status, await r.text()];
check('a second sign-up within the hour sends nothing, keeps the first link working, and answers exactly as a new one',
  again[0] === 200 && again[1] === answerNew[1] && mail.length === 3 && row('reader.one@example.com').token_hash === oldHash
  && sends().at(-1).held === 'address', JSON.stringify([again, sends().at(-1)]));
minutes(55);
await subscribe(signup('reader.one@example.com'));
const token2 = tokenOf(mail.at(-1));
r = await hit(new Request(`${host}/confirm?t=${token1}`));
const oldLink = r.status;
r = await hit(new Request(`${host}/confirm?t=${token2}`));
check('after the hour a new email goes, its token replaces the old one, and only the newest link works',
  mail.length === 4 && token2 !== token1 && oldLink === 404 && r.status === 200
  && row('reader.one@example.com').token_hash === sha(`${secrets.CONFIRM_SALT}:confirm:${token2}`), JSON.stringify([mail.length, oldLink, r.status]));
minutes(61);
await subscribe(signup('reader.one@example.com'));
minutes(61);
await subscribe(signup('reader.one@example.com'));
check('three confirmation emails a day to one address and no more',
  mail.filter((m) => m.body.Destination.ToAddresses[0] === 'reader.one@example.com').length === 3 && sends().at(-1).held === 'address',
  String(mail.length));

// ── the per-IP limit
minutes(120);
const ipBefore = rows().length;
for (let i = 0; i < 10; i += 1) await subscribe(signup(`many${i}@example.com`), { ip: '192.0.2.99' });
const tenth = [rows().length - ipBefore, mail.length];
await subscribe(signup('many10@example.com'), { ip: '192.0.2.99' });
await subscribe(signup('elsewhere@example.com'), { ip: '192.0.2.100' });
check('ten sign-ups an hour from one hashed IP; the eleventh keeps and sends nothing, and another IP still gets through',
  tenth[0] === 10 && !row('many10@example.com') && row('elsewhere@example.com') && mail.length === tenth[1] + 1, JSON.stringify(tenth));

// ── the day's cap
const capEnv = { DB: d1(), ...secrets };
const stamp = new Date(clock - 60 * 1000).toISOString();
for (let i = 0; i < 100; i += 1) capEnv.DB.raw.prepare("INSERT INTO sends (email_hash, ip_hash, at, held) VALUES (?, ?, ?, '')").run(`e${i}`, `i${i}`, stamp);
const capMail = mail.length;
r = await subscribe(signup('late@example.com'), { e: capEnv, ip: '192.0.2.7' });
const late = row('late@example.com', capEnv);
let count = await (await worker.fetch(new Request(`${host}/admin/count`, { headers: { authorization: `Bearer ${secrets.ADMIN_TOKEN}` } }), capEnv)).json();
check('past 100 confirmation emails in a day, a sign-up is kept with no link and no email, and counted as held by the cap',
  r.status === 200 && late && late.status === 'pending' && late.token_hash === null && mail.length === capMail
  && sends(capEnv).at(-1).held === 'cap' && count.last_day.held_cap === 1 && count.last_day.emails === 100, JSON.stringify([late, count]));
minutes(24 * 60 + 1);
await subscribe(signup('late@example.com'), { e: capEnv, ip: '192.0.2.7' });
check('the next day that sign-up gets its email and its link',
  mail.length === capMail + 1 && row('late@example.com', capEnv).token_hash !== null, String(mail.length));

// ── confirm
const confirmToken = tokenOf(mail.at(-1));
r = await worker.fetch(new Request(`${host}/confirm?t=${confirmToken}`), capEnv);
const confirmPage = await r.text();
check('GET /confirm shows a page with a Confirm button that POSTs the token, and changes nothing',
  r.status === 200 && /<form method="post" action="\/api\/updates\/confirm"><input type="hidden" name="t" value="[A-Za-z0-9_-]{43}"><button type="submit">Confirm<\/button><\/form>/.test(confirmPage)
  && row('late@example.com', capEnv).status === 'pending' && !confirmPage.includes('<script'), confirmPage.slice(0, 200));
check('the pages send no referrer, run no script and post only to their own origin',
  r.headers.get('referrer-policy') === 'no-referrer' && /default-src 'none'/.test(r.headers.get('content-security-policy'))
  && /form-action 'self'/.test(r.headers.get('content-security-policy')) && r.headers.get('cache-control') === 'no-store', r.headers.get('content-security-policy'));
const form = (body) => ({ method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' }, body });
r = await worker.fetch(new Request(`${host}/confirm`, form(`t=${confirmToken}`)), capEnv);
const confirmed = row('late@example.com', capEnv);
check('POST /confirm confirms the row, and sets its token and its IP hash to null',
  r.status === 200 && confirmed.status === 'confirmed' && /^\d{4}-\d\d-\d\dT/.test(confirmed.confirmed_at)
  && confirmed.token_hash === null && confirmed.ip_hash === null, JSON.stringify(confirmed));
r = await worker.fetch(new Request(`${host}/confirm`, form(`t=${confirmToken}`)), capEnv);
const reused = r.status;
r = await worker.fetch(new Request(`${host}/confirm`, form('t=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')), capEnv);
check('a used or made-up token confirms nothing', reused === 404 && r.status === 404, JSON.stringify([reused, r.status]));
const beforeConfirmedAgain = mail.length;
minutes(120);
r = await subscribe(signup('late@example.com'), { e: capEnv, ip: '192.0.2.7' });
check('a sign-up for a confirmed address sends nothing and answers the same as any other',
  r.status === 200 && (await r.text()) === answerNew[1] && mail.length === beforeConfirmedAgain && sends(capEnv).at(-1).held === 'confirmed', String(mail.length));

await subscribe(signup('slow@example.com'), { e: capEnv, ip: '192.0.2.8' });
const slowToken = tokenOf(mail.at(-1));
minutes(7 * 24 * 60 + 1);
r = await worker.fetch(new Request(`${host}/confirm`, form(`t=${slowToken}`)), capEnv);
check('a link over 7 days old confirms nothing', r.status === 404 && row('slow@example.com', capEnv).status === 'pending', String(r.status));

// ── the admin routes
env = capEnv;
const auth = [];
for (const [route, token, query] of [['count', null, ''], ['count', 'wrong', ''], ['recipients', null, `?token=${secrets.ADMIN_TOKEN}`], ['recipients', 'Bearer', '']]) {
  r = await hit(new Request(`${host}/admin/${route}${query}`, { headers: token === null ? {} : { authorization: token === 'Bearer' ? secrets.ADMIN_TOKEN : `Bearer ${token}` } }));
  auth.push(r.status);
}
r = await worker.fetch(new Request(`${host}/admin/delete`, { method: 'POST', body: '{"emails": ["late@example.com"]}', headers: { authorization: 'Bearer ' } }), { ...capEnv, ADMIN_TOKEN: '' });
auth.push(r.status);
check('the admin routes need the bearer token in the header: none, a wrong one, one in the address, no Bearer, or none set are all 401',
  JSON.stringify(auth) === '[401,401,401,401,401]' && row('late@example.com').status === 'confirmed', JSON.stringify(auth));
r = await admin('count');
const countText = await r.text();
count = JSON.parse(countText);
check('/admin/count gives counts only', r.status === 200 && count.confirmed === 1 && count.pending === 1 && !countText.includes('@'), countText);
await subscribe(signup('second@example.org'), { ip: '192.0.2.9' });
await hit(new Request(`${host}/confirm`, form(`t=${tokenOf(mail.at(-1))}`)));
r = await admin('recipients');
const listed = (await r.json()).recipients;
const unsub = Object.fromEntries(listed.map((x) => [x.email, x.unsubscribe]));
check('/admin/recipients gives the confirmed addresses alone, each with its own unsubscribe link',
  r.status === 200 && JSON.stringify(Object.keys(unsub)) === '["late@example.com","second@example.org"]'
  && Object.values(unsub).every((u) => /^https:\/\/idiograph\.app\/api\/updates\/unsubscribe\?t=\d+\.[0-9a-f]{64}$/.test(u))
  && unsub['late@example.com'] !== unsub['second@example.org'], JSON.stringify(listed));

// ── unsubscribe
const lateLink = new URL(unsub['late@example.com'] || `${host}/unsubscribe?t=missing.x`);
const lateToken = lateLink.searchParams.get('t');
const [lateId, lateSig] = lateToken.split('.');
check('the unsubscribe token is HMAC-SHA256 of the row\'s id under UNSUB_SECRET, and no column keeps it',
  lateSig === createHmac('sha256', secrets.UNSUB_SECRET).update(`unsubscribe:${lateId}`).digest('hex')
  && !JSON.stringify(rows()).includes(lateSig), lateToken);
r = await hit(new Request(lateLink));
const leavePage = await r.text();
check('GET /unsubscribe shows a page whose Stop button POSTs to the same link, and deletes nothing',
  r.status === 200 && leavePage.includes(`<form method="post" action="/api/updates/unsubscribe?t=${lateToken}"><button type="submit">Stop</button></form>`)
  && row('late@example.com'), leavePage.slice(0, 200));
const wrong = [];
for (const t of [`${lateId}.${'0'.repeat(64)}`, `${Number(lateId) + 1}.${lateSig}`, lateSig, '', `${lateId}.${lateSig.toUpperCase()}`]) {
  r = await hit(new Request(`${host}/unsubscribe?t=${encodeURIComponent(t)}`, form('List-Unsubscribe=One-Click')));
  wrong.push(r.status);
}
const otherSecret = await mod.unsubscribeToken({ UNSUB_SECRET: 'another-secret' }, lateId);
r = await hit(new Request(`${host}/unsubscribe?t=${otherSecret}`, form('List-Unsubscribe=One-Click')));
wrong.push(r.status);
check('a wrong, moved, partial or other secret\'s token deletes nothing', wrong.every((s) => s === 404) && rows().length === 3, JSON.stringify(wrong));
r = await hit(new Request(lateLink, form('List-Unsubscribe=One-Click')));
check('RFC 8058 one-click: a POST to the link with List-Unsubscribe=One-Click and no cookie deletes the row',
  r.status === 200 && !row('late@example.com') && row('second@example.org'), String(r.status));
r = await hit(new Request(lateLink, { method: 'POST' }));
check('the link used again, or the page\'s own button with an empty body, still answers 200', r.status === 200, String(r.status));

// ── the suppression sweep's delete
r = await admin('delete', { method: 'POST', body: JSON.stringify({ emails: ['SECOND@example.org', 'nobody@example.com', 'not an address'] }) });
const swept = await r.json();
r = await admin('delete', { method: 'POST', body: JSON.stringify({ emails: Array.from({ length: 1001 }, (_, i) => `x${i}@example.com`) }) });
check('/admin/delete deletes the rows of the addresses it is given, whatever their case, counts them, and refuses over 1000 at once',
  swept.ok && swept.deleted === 1 && !row('second@example.org') && r.status === 400, JSON.stringify(swept));

// ── ids never given twice
const lastId = Math.max(...rows().map((x) => x.id), 0);
capEnv.DB.raw.prepare('DELETE FROM subscribers').run();
await subscribe(signup('fresh@example.com'), { ip: '192.0.2.10' });
check('a row\'s id is never given again, so an old unsubscribe link cannot reach a new row',
  row('fresh@example.com').id > lastId && lastId > 0, JSON.stringify([lastId, row('fresh@example.com')]));

// ── the clear-up
const clear = { DB: d1(), ...secrets };
const ago = (days) => new Date(clock - days * 24 * 3600 * 1000).toISOString();
const ins = clear.DB.raw.prepare("INSERT INTO subscribers (email, status, consent, created_at) VALUES (?, ?, 'c', ?)");
ins.run('old.pending@example.com', 'pending', ago(8));
ins.run('new.pending@example.com', 'pending', ago(6));
ins.run('old.confirmed@example.com', 'confirmed', ago(400));
const sendIns = clear.DB.raw.prepare("INSERT INTO sends (email_hash, ip_hash, at, held) VALUES ('e', 'i', ?, '')");
sendIns.run(ago(3)); sendIns.run(ago(1));
const waits = [];
await worker.scheduled({ cron: '17 3 * * *' }, clear, { waitUntil: (p) => waits.push(p) });
await Promise.all(waits);
check('the cron deletes pending rows over 7 days old and the limits\' rows over 2, and keeps the rest',
  JSON.stringify(rows(clear).map((x) => x.email)) === '["new.pending@example.com","old.confirmed@example.com"]' && sends(clear).length === 1,
  JSON.stringify(rows(clear)));

// ── the answer comes before the email
{
  const e = { DB: d1(), ...secrets };
  let open;
  sesGate = new Promise((res) => { open = res; });
  const waits = [];
  const pending = worker.fetch(new Request(`${host}/subscribe`, {
    method: 'POST', headers: { 'content-type': 'application/json', 'cf-connecting-ip': '192.0.2.60' }, body: JSON.stringify(signup('early@example.com')),
  }), e, { waitUntil: (p) => waits.push(p) });
  const answered = await Promise.race([pending.then((res) => res.status), new Promise((res) => { setTimeout(() => res('no answer yet'), 300); })]);
  const mailedBefore = mail.length;
  open();
  sesGate = null;
  await pending;
  await Promise.all(waits);
  check('the answer to a sign-up comes while its email is still on its way, which goes on through waitUntil',
    answered === 200 && mail.length === mailedBefore + 1 && waits.length === 1, String(answered));
}

// ── sign-ups at the same moment: each limit holds
{
  const together = async (n, make) => {
    const e = { DB: d1({ lag: true }), ...secrets };
    const before = mail.length;
    const waits = [];
    await Promise.all(Array.from({ length: n }, (_, i) => {
      const [email, ip] = make(i);
      return worker.fetch(new Request(`${host}/subscribe`, {
        method: 'POST', headers: { 'content-type': 'application/json', 'cf-connecting-ip': ip }, body: JSON.stringify(signup(email)),
      }), e, { waitUntil: (p) => waits.push(p) });
    }));
    await Promise.all(waits);
    return [mail.length - before, e];
  };
  const [sameAddress] = await together(300, () => ['stranger@example.com', '203.0.113.9']);
  const [oneIp, ipEnv] = await together(300, (i) => [`stranger${i}@example.com`, '203.0.113.10']);
  const [many, manyEnv] = await together(300, (i) => [`crowd${i}@example.org`, `198.51.${Math.floor(i / 250)}.${i % 250}`]);
  const heldIp = sends(ipEnv).filter((x) => x.held === 'ip').length;
  check('300 sign-ups at the same moment: one email to one address, ten from one IP, a hundred in all',
    sameAddress === 1 && oneIp === 10 && many === 100 && heldIp === 290 && rows(ipEnv).length === 10
    && rows(manyEnv).length === 300 && sends(manyEnv).filter((x) => x.held === 'cap').length === 200, JSON.stringify([sameAddress, oneIp, many, heldIp]));
  const counted = await (await worker.fetch(new Request(`${host}/admin/count`, { headers: { authorization: `Bearer ${secrets.ADMIN_TOKEN}` } }), ipEnv)).json();
  check('/admin/count counts the sign-ups the IP limit held', counted.last_day.held_ip === 290 && counted.last_day.emails === 10, JSON.stringify(counted.last_day));
}

// ── one new address, signed up at once from three places
{
  const e = { DB: d1({ lag: true }), ...secrets };
  const before = logged.length;
  const waits = [];
  const answers = await Promise.all(['192.0.2.70', '192.0.2.71', '192.0.2.72'].map((ip) => worker.fetch(new Request(`${host}/subscribe`, {
    method: 'POST', headers: { 'content-type': 'application/json', 'cf-connecting-ip': ip }, body: JSON.stringify(signup('twice@example.com')),
  }), e, { waitUntil: (p) => waits.push(p) })));
  await Promise.all(waits);
  const newest = tokenOf(mail.at(-1));
  check('one new address signed up three times at once keeps one row, stores every sign-up, and its email\'s link works',
    answers.every((a) => a.status === 200) && rows(e).length === 1 && sends(e).length === 3 && logged.length === before
    && rows(e)[0].token_hash === sha(`${secrets.CONFIRM_SALT}:confirm:${newest}`), JSON.stringify([rows(e), logged.slice(before)]));
}

// ── confirmed while a second email was going: the late UPDATE leaves the confirmed row alone
{
  const e = { DB: d1(), ...secrets };
  await subscribe(signup('quick@example.com'), { e, ip: '192.0.2.80' });
  minutes(61);
  onSend = async () => {
    e.DB.raw.prepare("UPDATE subscribers SET status = 'confirmed', confirmed_at = ?, token_hash = NULL, ip_hash = NULL WHERE email = ?")
      .run(new Date(clock).toISOString(), 'quick@example.com');
  };
  await subscribe(signup('quick@example.com', { source: 'app' }), { e, ip: '192.0.2.81' });
  onSend = null;
  const q = row('quick@example.com', e);
  check('a re-sent email for an address confirmed meanwhile changes nothing of the confirmed row',
    q.status === 'confirmed' && q.token_hash === null && q.ip_hash === null && q.source === 'site', JSON.stringify(q));
}

// ── POST /confirm reads its token from the form alone
{
  const e = { DB: d1(), ...secrets };
  await subscribe(signup('query@example.com'), { e, ip: '192.0.2.82' });
  const t = tokenOf(mail.at(-1));
  r = await worker.fetch(new Request(`${host}/confirm?t=${t}`, { method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' }, body: '' }), e);
  check('POST /confirm with the token in the address and not in the form confirms nothing',
    r.status === 404 && row('query@example.com', e).status === 'pending', String(r.status));
}

// ── bodies: the read itself stops at the limit
{
  let pulled = 0;
  const endless = () => new ReadableStream({
    pull(c) { pulled += 1024; c.enqueue(new Uint8Array(1024).fill(32)); if (pulled > 16 * 1024 * 1024) c.close(); },
  });
  r = await hit(new Request(`${host}/subscribe`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: endless(), duplex: 'half' }));
  const sub = [r.status, pulled];
  pulled = 0;
  r = await admin('delete', { method: 'POST', body: endless(), duplex: 'half' });
  const del = [r.status, pulled];
  check('a body with no Content-Length is read no further than its limit: 2 KB for a sign-up, the longest delete for admin',
    sub[0] === 413 && sub[1] <= 8 * 1024 && del[0] === 413 && del[1] <= 512 * 1024, JSON.stringify([sub, del]));
}

// ── a thousand addresses deleted inside D1's 50 queries
{
  const e = { DB: d1(), ...secrets };
  const ins = e.DB.raw.prepare("INSERT INTO subscribers (email, status, consent, created_at) VALUES (?, 'confirmed', 'c', ?)");
  for (let i = 0; i < 1000; i += 1) ins.run(`gone${i}@example.com`, new Date(clock).toISOString());
  ins.run('stays@example.com', new Date(clock).toISOString());
  e.DB.queries = 0;
  r = await worker.fetch(new Request(`${host}/admin/delete`, {
    method: 'POST', headers: { authorization: `Bearer ${secrets.ADMIN_TOKEN}` },
    body: JSON.stringify({ emails: Array.from({ length: 1000 }, (_, i) => `GONE${i}@example.com`) }),
  }), e);
  const gone = await r.json();
  check('/admin/delete takes 1000 addresses in at most 50 queries and deletes exactly those',
    gone.deleted === 1000 && e.DB.queries <= 50 && rows(e).length === 1 && rows(e)[0].email === 'stays@example.com', JSON.stringify([gone, e.DB.queries]));
}

// ── the constant-time compare: the same answers either way, so only its shape can show it
{
  const text = mod.same.toString();
  check('tokens are compared byte by byte with no early way out: same() folds every byte\'s difference and compares only that',
    mod.same('abc', 'abc') && !mod.same('abc', 'abd') && !mod.same('abc', 'abcd')
    && JSON.stringify(text.match(/[!=]==?/g)) === '["==="]' && /return diff === 0;/.test(text) && /diff \|=/.test(text), text);
}

// ── routes, methods and setup
const routes = [];
for (const [method, p] of [['GET', '/subscribe'], ['PUT', '/subscribe'], ['DELETE', '/unsubscribe'], ['GET', '/admin/delete'], ['GET', '/nope'], ['GET', '/../feedback']]) {
  r = await hit(new Request(`${host}${p}`, { method }));
  routes.push(r.status);
}
r = await hit(new Request('https://idiograph.app/api/other', { method: 'POST' }));
routes.push(r.status);
check('each route takes its own method (405 otherwise) and any other path is 404', JSON.stringify(routes) === '[405,405,405,405,404,404,404]', JSON.stringify(routes));
const bare = { DB: d1(), ADMIN_TOKEN: '' };
r = await subscribe(signup('reader@example.com'), { e: bare });
check('with no salts set it keeps nothing and says so', r.status === 500 && rows(bare).length === 0, String(r.status));
const failEnv = { DB: d1(), ...secrets };
await subscribe(signup('refused@example.com'), { e: failEnv, ip: '192.0.2.11' });
const workingLink = tokenOf(mail.at(-1));
const keptHash = row('refused@example.com', failEnv).token_hash;
minutes(61);
sesAnswer = 500;
r = await subscribe(signup('refused@example.com'), { e: failEnv, ip: '192.0.2.11' });
const afterRefusal = [r.status, row('refused@example.com', failEnv), sends(failEnv).at(-1).held];
sesAnswer = 200;
sesThrows = true;
await subscribe(signup('refused@example.com'), { e: failEnv, ip: '192.0.2.11' });
sesThrows = false;
const afterThrow = sends(failEnv).at(-1).held;
check('when SES refuses the email, or cannot be reached, the answer is the same, the row stays pending, its sends row is '
  + 'failed and the link already sent still works',
  afterRefusal[0] === 200 && afterRefusal[1].status === 'pending' && afterRefusal[1].token_hash === keptHash && afterRefusal[2] === 'failed'
  && afterThrow === 'failed' && row('refused@example.com', failEnv).token_hash === keptHash, JSON.stringify(afterRefusal));
const mailedBeforeRetry = mail.length;
await subscribe(signup('refused@example.com'), { e: failEnv, ip: '192.0.2.11' });
check('a failed email counts towards no limit: a sign-up straight after it sends one, and its link replaces the old',
  mail.length === mailedBeforeRetry + 1 && sends(failEnv).at(-1).held === '' && tokenOf(mail.at(-1)) !== workingLink
  && row('refused@example.com', failEnv).token_hash === sha(`${secrets.CONFIRM_SALT}:confirm:${tokenOf(mail.at(-1))}`), String(mail.length - mailedBeforeRetry));
check('every request to SES carries a SigV4 signature over the very body sent, checked here with node\'s own crypto',
  signatures.checked >= 20 && signatures.bad === 0, JSON.stringify(signatures));
check('nothing the Worker logged holds an address, and something was logged (SES\'s refusals)',
  logged.length > 0 && !logged.some((l) => l.includes('@')), JSON.stringify(logged.filter((l) => l.includes('@')).slice(0, 3)));
check('no answer anywhere allows another origin', cors.every((c) => c === null), JSON.stringify(cors.filter(Boolean)));

print(JSON.stringify(results));
