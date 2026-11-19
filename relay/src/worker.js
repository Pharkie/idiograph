// SPDX-License-Identifier: AGPL-3.0-or-later
/* Idiograph's relay, the mailbox Working together passes sealed messages through (working together,
   build 3, 8 November 2026). Copyright (C) 2026 Adam Knowles. This program is free software: you can
   redistribute it and/or modify it under the terms of the GNU Affero General Public License as published
   by the Free Software Foundation, version 3 or any later version. It comes with no warranty. See LICENSE
   at the repository's root.

   The relay never sees a word of a project. Every message and every blob is sealed on the sender's
   computer before it comes here, and the relay keeps it, numbers it and hands it on. It knows a random
   project id, the devices' public keys, times, sizes and counts, and nothing else.

     POST /relay/v1/projects                 make a project with the lead's key
     PUT  /relay/v1/p/:id/devices            the lead's list of device keys, the only devices let in
     POST /relay/v1/p/:id/messages[?blob=B]  one sealed envelope, answered with its relay number n, naming the
                                             sealed file B it carries, which is freed with it
     GET  /relay/v1/p/:id/messages?after=N   up to 200 envelopes after N
     GET  /relay/v1/p/:id/live               a WebSocket that says "new N" when a message comes
     PUT  /relay/v1/p/:id/blobs/:blob        a sealed file above a message's size, into R2
     GET  /relay/v1/p/:id/blobs/:blob        the same file back
     POST /relay/v1/p/:id/seen               a device's highest number read
     POST /relay/v1/invites/:invite          a sealed join answer, unsigned, limited by IP
     GET  /relay/v1/invites/:invite?after=K  the answers after the K-th
     GET  /relay/v1/operator/usage           the operator's: each project's bytes, the ceilings, today's counts
     DELETE /relay/v1/operator/p/:id         the operator's: a project and its files deleted

   Open since relayopen (18 November 2026, Adam's rulings that day): anyone with the app starts a project and no
   code is asked. Small limits keep the bill small, each named once in LIMITS below. A project made before then
   (no `open` in its meta) keeps OLD_LIMITS and the ceilings never refuse it, though its bytes still count in
   them. The operator's routes take the OPERATOR_KEY secret as their key and are refused while it is not set.

   Every call but an invite's is signed by the device making it: X-Device (its id, 32 hex), X-Time (Unix
   seconds, within five minutes of the relay's clock), X-Nonce (16 random bytes in hex, once only) and
   X-Sig (base64url Ed25519) over "<METHOD>\n<path and query>\n<X-Time>\n<X-Nonce>\n<SHA-256 of the
   body, hex>". A blob's PUT names its body's
   SHA-256 in X-Content-SHA256, which R2 checks as it stores it, so a large body is never held here. A GET's nonce
   is not written down: a GET sent twice changes nothing, and a row for every look would be most of the writes.
   A device id is the first 16 bytes of the SHA-256 of its raw Ed25519 public key. */

import { DurableObject } from 'cloudflare:workers';

const MB = 1024 * 1024;

// Every limit of a project made open, in one place. A change of ruling is one line here, and the app's own
// copies are in family/relay_transport.py (MAX_BLOB) and apps/idiograph/team_sync.py (SMALL).
export const LIMITS = {
  message: 1536 * 1024,          // bytes, one envelope: a 1 MB padded inner message in its base64 and fields
  small: 24 * 1024,              // bytes, an envelope outside the day's bytes (a list of people, a comment)
  smallWaiting: 8 * MB,          // bytes of those small envelopes a project keeps waiting, unread
  blob: 80 * MB,                 // bytes, one sealed file
  dayBytes: 100 * MB,            // bytes a project takes in a day, files and messages over `small` together
  dayFiles: 80 * MB,             // of which files may take this much, so the rest always stays for changes
  waiting: 250 * MB,             // bytes a project keeps on the relay, files and messages over `small` together
  waitingMessages: 100 * MB,     // of which messages over `small` may be this much (the Durable Objects' share)
  dayMessages: 1000,             // messages a project takes in a day
  filesPerDay: 150,              // files a project puts in a day, counted when allowed and never handed back
  relayFilesPerDay: 20000,       // files the whole relay takes in a UTC day, inside R2's free operations
  fetchesPerFile: 10,            // times one device fetches one file
  ceilingBlobs: 9 * 1024 ** 3,   // bytes of sealed files the whole relay keeps (R2)
  ceilingMessages: 4 * 1024 ** 3, // bytes of messages the whole relay keeps (the Durable Objects)
  projectsPerDay: 20,            // new projects the relay makes in a UTC day, unless the operator sets the day's
  projectsMost: 200,             // the most the operator may allow in a day
  projectsPerIp: 3,              // and from one address (an IPv6 /56) in that day
  invitesPerProject: 10,         // invite mailboxes a project's computers open in a day
  report: 600,                   // seconds a project's last report to the counter stands for its messages
  orphanDays: 1,                 // days a file no message names is kept, in a project made open
  idleDays: 90,                  // days with nothing posted, nothing held, after which a project's alarm stops
  alarmEvery: 86400,             // seconds between a project's alarms
  page: 200,                     // envelopes one GET answers with at most
  pageBytes: 8 * MB,             // and the bytes it stops at, so a page of large ones stays small
  devices: 24,                   // devices on one project's list
  listsPerDay: 30,               // changed lists of devices the lead sends in a day
  removedMost: 200,              // removed devices a project keeps a row for, the most
  clockSkew: 300,                // seconds X-Time may stand from the relay's clock
  keepDays: 90,                  // days anything is kept, seen by all or not
  invite: 4096,                  // bytes, one join answer
  invitePosts: 10,               // answers one invite holds
  inviteDays: 7,                 // days an invite lives from its first answer
};
// a project made before the relay was open keeps these, and the ceilings never refuse it
export const OLD_LIMITS = { blob: 200 * MB, dayBytes: 2 * 1024 ** 3, dayFiles: 2 * 1024 ** 3, dayMessages: 5000,
  filesPerDay: Infinity, devices: 64 };

/* The limits in force: LIMITS, or for the suite's run on one computer, LIMITS with TEST_LIMITS laid over them
   (JSON in a var that wrangler.jsonc never sets), so a check reaches 250 MB with a few hundred kilobytes, or a
   project's alarm comes in seconds. */
let laid = null;
function limitsFor(env) {
  if (!env || !env.TEST_LIMITS) return LIMITS;
  if (!laid || laid.from !== env.TEST_LIMITS) {
    let over = {};
    try { over = JSON.parse(env.TEST_LIMITS); } catch (err) { over = {}; }
    laid = { from: env.TEST_LIMITS, limits: Object.freeze({ ...LIMITS, ...over }) };
  }
  return laid.limits;
}

const PREFIX = '/relay/v1';
// live sockets one device keeps open on a project: two or three Idiographs on one computer share its key
const SOCKETS_A_DEVICE = 3;
const HEX32 = /^[0-9a-f]{32}$/;
const BLOB = /^[A-Za-z0-9_-]{16,64}$/;
const DAY = 86400;
const enc = new TextEncoder();

const json = (data, status = 200) => new Response(JSON.stringify(data), {
  status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
});
const refuse = (status, error, more = {}) => json({ ok: false, error, ...more }, status);
const now = () => Math.floor(Date.now() / 1000);
const today = () => Math.floor(Date.now() / 1000 / DAY);

function hex(buf) {
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
}
function b64url(bytes) {
  let s = '';
  for (const b of new Uint8Array(bytes)) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
function unb64url(text) {
  if (typeof text !== 'string' || !/^[A-Za-z0-9_-]*$/.test(text)) return null;
  const s = atob(text.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((text.length + 3) % 4));
  return Uint8Array.from(s, (c) => c.charCodeAt(0));
}
async function sha256(bytes) {
  return hex(await crypto.subtle.digest('SHA-256', bytes));
}
async function deviceId(key) {
  return (await sha256(key)).slice(0, 32);
}
function sameText(a, b) {
  // a comparison whose time does not depend on where the two first differ
  const x = enc.encode(String(a)), y = enc.encode(String(b));
  let diff = x.length ^ y.length;
  for (let i = 0; i < Math.max(x.length, y.length); i++) diff |= (x[i] || 0) ^ (y[i] || 0);
  return diff === 0;
}
// whether a SQLite table is there, read without writing anything
function hasTable(sql, name) {
  return sql.exec("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", name).toArray().length > 0;
}

/* A request that cannot be signed, by its headers' shape alone, or null: the refusal costs no Durable Object. */
function unsigned(request) {
  const time = request.headers.get('X-Time') || '';
  if (!HEX32.test(request.headers.get('X-Device') || '') || !HEX32.test(request.headers.get('X-Nonce') || '')
      || !/^\d{1,12}$/.test(time) || !/^[A-Za-z0-9_-]{86}$/.test(request.headers.get('X-Sig') || '')) return refuse(401, 'unsigned');
  if (Math.abs(now() - Number(time)) > LIMITS.clockSkew) return refuse(401, 'clock');
  return null;
}

/* The signature on a request, checked against `key` (raw 32 bytes). `bodyHash` is the body's SHA-256
   in hex, worked out here or, for a blob, taken from X-Content-SHA256. Answers null when it holds, or
   the refusal. */
async function checkSignature(request, key, bodyHash) {
  const time = request.headers.get('X-Time') || '';
  const nonce = request.headers.get('X-Nonce') || '';
  const sig = unb64url(request.headers.get('X-Sig') || '');
  if (!/^\d{1,12}$/.test(time) || !HEX32.test(nonce) || !sig || sig.length !== 64) return refuse(401, 'unsigned');
  if (Math.abs(now() - Number(time)) > LIMITS.clockSkew) return refuse(401, 'clock');
  const url = new URL(request.url);
  const text = `${request.method}\n${url.pathname}${url.search}\n${time}\n${nonce}\n${bodyHash}`;
  let good = false;
  try {
    const pub = await crypto.subtle.importKey('raw', key, { name: 'Ed25519' }, false, ['verify']);
    good = await crypto.subtle.verify({ name: 'Ed25519' }, pub, sig, enc.encode(text));
  } catch (err) {
    good = false;
  }
  return good ? null : refuse(401, 'signature');
}

/* Every mailbox lives in the jurisdiction JURISDICTION names, "eu" in wrangler.jsonc, wherever its
   devices are. The engine on one's own computer has no jurisdictions, so a local run sets it to "". */
const projects = (env) => namespaceIn(env, 'PROJECTS');
function namespaceIn(env, binding) {
  const ns = env[binding];
  const where = env.JURISDICTION === undefined ? 'eu' : env.JURISDICTION;
  return where ? ns.jurisdiction(where) : ns;
}

/* The address a new project is counted by: an IPv4 address as it is, an IPv6 one by its /56, its first three
   groups and half the fourth, the block most hosts and providers hand one customer, so it counts once. */
export function ipKey(ip) {
  const text = String(ip || '').trim().toLowerCase();
  if (!text.includes(':')) return text || 'none';
  const [head, tail] = text.split('::');
  const a = head ? head.split(':') : [];
  const b = tail ? tail.split(':') : [];
  const groups = tail === undefined ? a : [...a, ...Array(Math.max(0, 8 - a.length - b.length)).fill('0'), ...b];
  const full = groups.slice(0, 4).map((g) => (g || '0').padStart(4, '0'));
  while (full.length < 4) full.push('0000');
  return [...full.slice(0, 3), full[3].slice(0, 2) + '00'].map((g) => g.replace(/^0+(?=.)/, '')).join(':') + '::/56';
}

// the one counter for the whole relay, in the same jurisdiction as the projects
function counter(env) {
  const ns = namespaceIn(env, 'COUNTER');
  return ns.get(ns.idFromName('relay'));
}

// a rate binding's verdict for this address, true when it lets the call through or is not bound
async function within(env, binding, request) {
  const limit = env[binding];
  if (!limit || typeof limit.limit !== 'function') return true;
  const { success } = await limit.limit({ key: request.headers.get('CF-Connecting-IP') || 'local' });
  return success;
}

/* A request's body read here in the Worker, never in a Durable Object, so a client sending it slowly holds no object
   awake: its Content-Length first, then the bytes, either over `most` refused. Answers the bytes or the refusal. */
async function bodyOf(request, most) {
  if (Number(request.headers.get('content-length') || 0) > most) return { refusal: refuse(413, 'too large') };
  const body = new Uint8Array(await request.arrayBuffer());
  if (body.length > most) return { refusal: refuse(413, 'too large') };
  return { body };
}

async function makeProject(request, env) {
  if (!await within(env, 'PROJECT_LIMIT', request)) return refuse(429, 'slow down');
  const got = await bodyOf(request, 4096);
  if (got.refusal) return got.refusal;
  const body = got.body;
  let ask;
  try { ask = JSON.parse(new TextDecoder().decode(body)); } catch (err) { return refuse(400, 'not JSON'); }
  const key = unb64url(ask && ask.key);
  if (!key || key.length !== 32) return refuse(400, 'key');
  if ((request.headers.get('X-Device') || '') !== await deviceId(key)) return refuse(401, 'device');
  const bad = await checkSignature(request, key, await sha256(body));
  if (bad) return bad;
  const limits = limitsFor(env);
  // the call's nonce kept by the counter, so one signed request sent again makes no second project (review2's L4)
  const counted = await counter(env).admit(ipKey(request.headers.get('CF-Connecting-IP')), limits.projectsPerDay,
    limits.projectsPerIp, request.headers.get('X-Nonce') || '');
  if (!counted.ok) return refuse(counted.error === 'sent before' ? 409 : 429, counted.error);
  const id = hex(crypto.getRandomValues(new Uint8Array(16)));
  const box = projects(env).get(projects(env).idFromName(id));
  await box.init(id, b64url(key));
  return json({ ok: true, project: id }, 201);
}

/* The operator's two routes, keyed by the OPERATOR_KEY secret as a bearer token: what each project keeps, and a
   project deleted with its files. No key, a wrong one and a relay with no OPERATOR_KEY set are refused alike. */
async function operator(request, env, parts) {
  const key = String(env.OPERATOR_KEY || '').trim();
  const given = (request.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '');
  if (key.length < 16 || !given || !sameText(key, given)) return refuse(403, 'operator');
  if (parts.length === 2 && parts[1] === 'usage' && request.method === 'GET') {
    return json(Object.assign({ ok: true }, await counter(env).usage(limitsFor(env))));
  }
  if (parts.length === 2 && parts[1] === 'allow' && request.method === 'POST') {
    // today's allowance of new projects: 0 closes the day, a number reopens it after someone has used it up
    const got = await bodyOf(request, 1024);
    if (got.refusal) return got.refusal;
    let ask;
    try { ask = JSON.parse(new TextDecoder().decode(got.body)); } catch (err) { return refuse(400, 'not JSON'); }
    const n = ask && ask.projects;
    if (!Number.isInteger(n) || n < 0 || n > limitsFor(env).projectsMost) return refuse(400, 'projects');
    return json(Object.assign({ ok: true }, await counter(env).allow(n)));
  }
  if (parts.length === 3 && parts[1] === 'p' && HEX32.test(parts[2]) && request.method === 'DELETE') {
    const box = projects(env).get(projects(env).idFromName(parts[2]));
    const gone = await box.erase();
    await counter(env).forget(parts[2]);
    return json({ ok: true, project: parts[2], files: gone.files, messages: gone.messages });
  }
  return refuse(404, 'not here');
}

/* An invite's mailbox, unsigned, limited by address. It takes and gives answers only once a computer on a project
   has opened it with a signed call (`POST p/:id/invites/:invite`), and refuses anything else with nothing written. */
async function invite(request, env, id) {
  if (!await within(env, 'INVITE_LIMIT', request)) return refuse(429, 'slow down');
  const ns = namespaceIn(env, 'INVITES');
  const box = ns.get(ns.idFromName(id));
  if (request.method === 'GET') {
    const after = Number(new URL(request.url).searchParams.get('after') || 0);
    if (!Number.isInteger(after) || after < 0) return refuse(400, 'after');
    return answer(await box.answers(after));
  }
  const got = await bodyOf(request, LIMITS.invite);
  if (got.refusal) return got.refusal;
  if (!got.body.length) return refuse(400, 'empty');
  return answer(await box.take(got.body));
}

// a Durable Object's answer, `{status, data}`, as the Response the Worker sends
const answer = (said) => json(said.data, said.status);

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!url.pathname.startsWith(PREFIX + '/')) return refuse(404, 'not here');
    const parts = url.pathname.slice(PREFIX.length + 1).split('/');
    try {
      if (parts.length === 1 && parts[0] === 'projects') {
        return request.method === 'POST' ? await makeProject(request, env) : refuse(405, 'method');
      }
      if (parts[0] === 'operator') return await operator(request, env, parts);
      if (parts[0] === 'invites' && parts.length === 2 && HEX32.test(parts[1])) {
        return ['POST', 'GET'].includes(request.method) ? await invite(request, env, parts[1]) : refuse(405, 'method');
      }
      if (parts[0] === 'p' && parts.length >= 3 && HEX32.test(parts[1])) {
        // refused here, before any Durable Object is touched: a call with no signature's shape, or a body over a
        // message's limit (a file's limits are checked in blob() before its object is asked)
        const shape = unsigned(request);
        if (shape) return shape;
        const id = parts[1];
        const box = projects(env).get(projects(env).idFromName(id));
        if (parts[2] === 'blobs' && parts.length === 4 && BLOB.test(parts[3])) return await blob(request, env, box, id, parts[3]);
        if (parts.length === 3 && parts[2] === 'live') return await box.fetch(request);
        if (parts.length === 3 && parts[2] === 'messages' && request.method === 'GET') return answer(await box.list(serial(request)));
        const route = parts.length === 3 && ['devices', 'messages', 'seen'].includes(parts[2]) ? parts[2]
          : parts.length === 4 && parts[2] === 'invites' && HEX32.test(parts[3]) ? 'invites' : '';
        if (!route) return refuse(404, 'not here');
        if (request.method !== (route === 'devices' ? 'PUT' : 'POST')) return refuse(405, 'method');
        const got = await bodyOf(request, LIMITS.message);
        if (got.refusal) return got.refusal;
        return answer(await box.call(serial(request), route, got.body, parts[3] || ''));
      }
      return refuse(404, 'not here');
    } catch (err) {
      console.error('relay', err && err.stack ? err.stack : String(err));
      return refuse(500, 'relay');
    }
  },
};

/* A blob goes straight from the request to R2, never through the Durable Object, which only checks the
   signature, the day's bytes and files, the project's waiting bytes and the relay's ceiling first. R2 refuses a body
   whose SHA-256 is not the one signed, and an upload refused or broken off hands its bytes back. */
async function blob(request, env, box, id, name) {
  const key = `p/${id}/${name}`;
  if (request.method === 'PUT') {
    const size = Number(request.headers.get('content-length') || NaN);
    const hash = (request.headers.get('X-Content-SHA256') || '').toLowerCase();
    if (!Number.isInteger(size) || size < 0) return refuse(411, 'length');
    if (size > Math.max(OLD_LIMITS.blob, limitsFor(env).blob)) return refuse(413, 'too large');
    if (!/^[0-9a-f]{64}$/.test(hash)) return refuse(400, 'hash');
    const allowed = await box.allowBlob(serial(request), name, size, hash);
    if (allowed.status !== 200) return answer(allowed);
    try {
      await env.BLOBS.put(key, request.body, { sha256: hash });
    } catch (err) {
      await box.forgetBlob(name);
      return refuse(400, 'hash');
    }
    return json({ ok: true, blob: name, bytes: size }, 201);
  }
  if (request.method === 'GET') {
    const allowed = await box.allowBlob(serial(request), name, -1, await sha256(new Uint8Array(0)));
    if (allowed.status !== 200) return answer(allowed);
    const object = await env.BLOBS.get(key);
    if (!object) {
      try {
        await box.uncountFetch(name, allowed.device);
      } catch (err) {
        // a fetch left counted costs the computer one of its ten and nothing else
      }
      return refuse(404, 'no blob');
    }
    return new Response(object.body, { headers: { 'content-type': 'application/octet-stream', 'content-length': String(object.size) } });
  }
  return refuse(405, 'method');
}

// what a request's signature rests on, passed to a Durable Object's method in place of the request
function serial(request) {
  return { method: request.method, url: request.url, headers: Object.fromEntries(['X-Device', 'X-Time', 'X-Nonce', 'X-Sig'].map((h) => [h, request.headers.get(h) || ''])) };
}

// a Durable Object's answers, plain objects the Worker turns into a Response (`answer`)
const ok = (data = {}, status = 200) => ({ status, data: { ok: true, ...data } });
const no = (status, error, more = {}) => ({ status, data: { ok: false, error, ...more } });

const TABLES = `
  CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
  CREATE TABLE IF NOT EXISTS devices(id TEXT PRIMARY KEY, key TEXT NOT NULL, added INTEGER NOT NULL, removed INTEGER);
  CREATE TABLE IF NOT EXISTS messages(n INTEGER PRIMARY KEY AUTOINCREMENT, device TEXT NOT NULL, at INTEGER NOT NULL, bytes INTEGER NOT NULL, body BLOB NOT NULL);
  CREATE TABLE IF NOT EXISTS seen(device TEXT PRIMARY KEY, n INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS blobs(id TEXT PRIMARY KEY, bytes INTEGER NOT NULL, at INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS usage(day INTEGER PRIMARY KEY, bytes INTEGER NOT NULL, messages INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS nonces(nonce TEXT PRIMARY KEY, at INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS named(n INTEGER PRIMARY KEY, blob TEXT NOT NULL UNIQUE);
  CREATE TABLE IF NOT EXISTS pending(blob TEXT PRIMARY KEY, at INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS files_day(day INTEGER PRIMARY KEY, bytes INTEGER NOT NULL, n INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS fetched(blob TEXT NOT NULL, device TEXT NOT NULL, n INTEGER NOT NULL, PRIMARY KEY(blob, device));
  CREATE TABLE IF NOT EXISTS invites_day(day INTEGER PRIMARY KEY, n INTEGER NOT NULL);
`;

/* One project's mailbox. Its SQLite holds the devices let in, the sealed messages by number, what each
   device has read, the blobs' sizes and the day's counts. Since relayopen, new tables beside them and never a new
   column on an old one, so a mailbox the old relay made opens as it was: which message names which blob
   (`named`), blobs put and not yet named (`pending`), the day's bytes and number of files (`files_day`), how often
   each device has fetched each file (`fetched`), the invites opened a day (`invites_day`), and in `meta` whether
   it was made open (`open`) and one row, `sums`, with the project's sums, when it last took something and what the
   counter last said. An object no project was made in creates no table: a call to it is refused 404 and writes
   nothing. Every call's refusals are decided before its nonce is written, so a refused call writes no row. */
export class Project extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    this.limits = limitsFor(env);
    this.ready = hasTable(this.sql, 'meta');
    // a mailbox the old relay made gains the new tables once
    if (this.ready && !hasTable(this.sql, 'invites_day')) this.sql.exec(TABLES);
    this.cache = null;
    // the sums row is made now, so a project the old relay made is not added up in the middle of its first call
    // (a message just inserted would be counted twice)
    if (this.ready) this.sums();
    // a ping is answered without waking the object, so a quiet socket costs nothing
    ctx.setWebSocketAutoResponse(new WebSocketRequestResponsePair('ping', 'pong'));
  }

  meta(k) {
    if (!this.ready) return null;
    const row = this.sql.exec('SELECT v FROM meta WHERE k = ?', k).toArray()[0];
    return row ? row.v : null;
  }
  setMeta(k, v) {
    this.sql.exec('INSERT OR REPLACE INTO meta(k, v) VALUES (?, ?)', k, String(v));
  }

  // made open, under the new limits, or before (the pilot's), under the old ones and outside the ceilings
  get open() {
    return this.meta('open') === '1';
  }
  get most() {
    return this.open ? this.limits : OLD_LIMITS;
  }
  // a project made open with one computer on its list has nobody to send a file or a larger message to
  alone() {
    return this.open && this.sql.exec('SELECT COUNT(*) AS c FROM devices WHERE removed IS NULL').one().c <= 1;
  }

  /* The project's sums as the rows hold them: files (b), messages (m), messages over `small` (w). */
  counted() {
    const b = this.sql.exec('SELECT COALESCE(SUM(bytes), 0) AS b FROM blobs').one().b;
    const m = this.sql.exec('SELECT COALESCE(SUM(bytes), 0) AS m FROM messages').one().m;
    const w = this.sql.exec('SELECT COALESCE(SUM(bytes), 0) AS w FROM messages WHERE bytes > ?', this.limits.small).one().w;
    return { b, m, w };
  }
  /* The one `sums` row: b, m and w, `last` (when it last took something), `idle` (its alarm stopped), `r` (when
     it last reported to the counter) and `full` (whether the counter said the relay's messages are full). A
     mailbox the old relay made has none, so the first call adds up its rows once. */
  sums() {
    if (this.cache) return this.cache;
    let s = null;
    try { s = JSON.parse(this.meta('sums') || 'null'); } catch (err) { s = null; }
    if (!s || typeof s !== 'object') {
      s = { ...this.counted(), last: now(), idle: false, r: 0, full: false };
      this.setMeta('sums', JSON.stringify(s));
    }
    this.cache = s;
    return s;
  }
  keep(s) {
    this.cache = s;
    this.setMeta('sums', JSON.stringify(s));
  }
  /* The sums moved by what was taken or deleted, in one row written. `took` marks something taken now, and
     answers true when the project's alarm had stopped and must be set again. */
  move(blobs, messages, waiting, took = false) {
    const s = { ...this.sums() };
    s.b = Math.max(0, s.b + blobs);
    s.m = Math.max(0, s.m + messages);
    s.w = Math.max(0, s.w + waiting);
    const wake = took && s.idle;
    if (took) {
      s.last = now();
      s.idle = false;
    }
    this.keep(s);
    return wake;
  }
  async rearm(wake) {
    if (wake) await this.ctx.storage.setAlarm(Date.now() + this.limits.alarmEvery * 1000);
  }

  async init(id, leadKey) {
    const key = unb64url(leadKey);
    const lead = await deviceId(key);
    this.sql.exec(TABLES);
    this.ready = true;
    this.sql.exec('INSERT OR REPLACE INTO meta(k, v) VALUES (?, ?), (?, ?), (?, ?), (?, ?)', 'id', id, 'lead', lead, 'made', String(now()), 'open', '1');
    this.sql.exec('INSERT OR REPLACE INTO devices(id, key, added, removed) VALUES (?, ?, ?, NULL)', lead, leadKey, now());
    this.sums();
    await this.ctx.storage.setAlarm(Date.now() + this.limits.alarmEvery * 1000);
    await this.report(true);
  }

  /* The project's sums told to the counter, which answers whether the relay is full. `blobsAfter` asks for room
     for a file first, and counts it against the relay's files of the day: refused, nothing is recorded. Messages
     ask only when the last answer is older than `report` seconds, so a busy project costs the counter one call in
     ten minutes. */
  async report(force = false, blobsAfter = null) {
    const id = this.meta('id');
    if (!id) return { ok: true };
    const s = this.sums();
    if (!force && blobsAfter === null && now() - Number(s.r || 0) < this.limits.report) {
      return { ok: true, messagesFull: !!s.full };
    }
    const said = await counter(this.env).report(id, blobsAfter === null ? s.b : blobsAfter, s.m, !this.open,
      this.limits, blobsAfter !== null);
    this.keep({ ...this.sums(), r: now(), full: !!said.messagesFull });
    return said;
  }

  /* The device behind a request with its signature checked, or the refusal. It writes nothing: `once` writes the
     nonce, after the caller has decided its refusals. */
  async signed(s, bodyHash) {
    if (!this.ready || !this.meta('id')) return { refusal: no(404, 'no project') };
    const request = new Request(s.url, { method: s.method, headers: s.headers });
    const device = request.headers.get('X-Device') || '';
    const row = this.sql.exec('SELECT key, removed FROM devices WHERE id = ?', device).toArray()[0];
    if (!row) return { refusal: no(403, 'device') };
    if (row.removed) return { refusal: no(403, 'removed') };
    const bad = await checkSignature(request, unb64url(row.key), bodyHash);
    if (bad) return { refusal: { status: bad.status, data: await bad.json() } };
    return { device, nonce: request.headers.get('X-Nonce') || '' };
  }
  /* A nonce is good once: the copy of a request sent again inside the five minutes is refused "sent before".
     Written only for a call that is about to change something. Answers the refusal or null. */
  once(nonce) {
    this.sql.exec('DELETE FROM nonces WHERE at < ?', now() - 2 * LIMITS.clockSkew);
    if (this.sql.exec('SELECT 1 FROM nonces WHERE nonce = ?', nonce).toArray().length) return no(409, 'sent before');
    this.sql.exec('INSERT INTO nonces(nonce, at) VALUES (?, ?)', nonce, now());
    return null;
  }
  // whether a nonce has been taken already, read without writing, so a refusal can say "sent before" first
  seenNonce(nonce) {
    return this.sql.exec('SELECT 1 FROM nonces WHERE nonce = ? AND at >= ?', nonce, now() - 2 * LIMITS.clockSkew).toArray().length > 0;
  }

  /* The day's counts, read: "" when `bytes` (of which `files` are files, `puts` of them) and `messages` more fit,
     else the refusal's word, "day" for the day's bytes, "day files" for the files' share of them, "files today" for
     the number of files, "day messages" for the count of messages. Nothing is written. */
  fits(bytes, messages, files = 0, puts = 0) {
    const day = today();
    const most = this.most;
    const row = this.sql.exec('SELECT bytes, messages FROM usage WHERE day = ?', day).toArray()[0] || { bytes: 0, messages: 0 };
    const filed = files || puts ? (this.sql.exec('SELECT bytes, n FROM files_day WHERE day = ?', day).toArray()[0] || { bytes: 0, n: 0 }) : { bytes: 0, n: 0 };
    if (bytes > 0 && row.bytes + bytes > most.dayBytes) return 'day';
    if (files > 0 && filed.bytes + files > most.dayFiles) return 'day files';
    if (puts > 0 && filed.n + puts > most.filesPerDay) return 'project files today';
    if (messages > 0 && row.messages + messages > most.dayMessages) return 'day messages';
    return '';
  }
  /* The day's counts moved. Negative `bytes` and `files` hand bytes back; a file's number is never handed back. */
  take(bytes, messages, files = 0, puts = 0) {
    const day = today();
    const row = this.sql.exec('SELECT bytes, messages FROM usage WHERE day = ?', day).toArray()[0] || { bytes: 0, messages: 0 };
    this.sql.exec('INSERT OR REPLACE INTO usage(day, bytes, messages) VALUES (?, ?, ?)', day, Math.max(0, row.bytes + bytes), row.messages + messages);
    if (files || puts) {
      const filed = this.sql.exec('SELECT bytes, n FROM files_day WHERE day = ?', day).toArray()[0] || { bytes: 0, n: 0 };
      this.sql.exec('INSERT OR REPLACE INTO files_day(day, bytes, n) VALUES (?, ?, ?)', day, Math.max(0, filed.bytes + files), filed.n + puts);
      this.sql.exec('DELETE FROM files_day WHERE day < ?', day - 2);
    }
    this.sql.exec('DELETE FROM usage WHERE day < ?', day - 2);
  }

  /* The computers on the list that have not read the oldest message held, so the lead can see which one holds the
     project's bytes on the relay. */
  behind() {
    const oldest = this.sql.exec('SELECT MIN(n) AS n FROM messages').one().n;
    if (oldest === null || oldest === undefined) return [];
    return this.sql.exec('SELECT d.id FROM devices d LEFT JOIN seen s ON s.device = d.id WHERE d.removed IS NULL AND COALESCE(s.n, 0) < ?', oldest)
      .toArray().map((r) => r.id);
  }

  /* A file's PUT (`size` its bytes) or GET (`size` -1) let through, or refused with nothing written. A PUT is
     counted in the day's bytes, files and number of files, and asks the counter for room in the relay's files and
     its files of the day. A GET is counted against `fetchesPerFile` for its device in the same step as the check,
     and handed back by `uncountFetch` when R2 has no file to give (relayfix3, review2's L2). */
  async allowBlob(s, name, size, hash) {
    const { device, nonce, refusal } = await this.signed(s, hash);
    if (refusal) return refusal;
    const exists = this.sql.exec('SELECT 1 FROM blobs WHERE id = ?', name).toArray().length > 0;
    if (size < 0) {
      if (!exists) return no(404, 'no blob');
      if (this.open) {
        const row = this.sql.exec('SELECT n FROM fetched WHERE blob = ? AND device = ?', name, device).toArray()[0] || { n: 0 };
        if (row.n >= this.limits.fetchesPerFile) return no(429, 'fetched too often');
        this.sql.exec('INSERT OR REPLACE INTO fetched(blob, device, n) VALUES (?, ?, ?)', name, device, row.n + 1);
      }
      return { status: 200, device };
    }
    if (this.seenNonce(nonce)) return no(409, 'sent before');
    if (exists) return no(409, 'blob there');
    const sums = this.sums();
    if (size > this.most.blob) return no(413, 'too large');
    if (this.alone()) return no(409, 'nobody to send to');
    if (this.open && sums.b + sums.w + size > this.limits.waiting) return no(429, 'project full', { behind: this.behind() });
    const word = this.fits(size, 0, size, 1);
    if (word) return no(429, word);
    const twice = this.once(nonce);
    if (twice) return twice;
    // the file's row and its bytes taken before the counter is asked, so a second upload at once sees them
    this.take(size, 0, size, 1);
    this.sql.exec('INSERT OR REPLACE INTO blobs(id, bytes, at) VALUES (?, ?, ?)', name, size, now());
    if (this.open) this.sql.exec('INSERT OR REPLACE INTO pending(blob, at) VALUES (?, ?)', name, now());
    const wake = this.move(size, 0, 0, true);
    const said = await this.report(true, this.sums().b);
    if (!said.ok) {
      this.sql.exec('DELETE FROM blobs WHERE id = ?', name);
      this.sql.exec('DELETE FROM pending WHERE blob = ?', name);
      this.take(-size, 0, -size, 0);
      this.move(-size, 0, 0);
      return no(503, said.error || 'relay full');
    }
    await this.rearm(wake);
    return { status: 200, device };
  }

  /* A fetch's count handed back, when R2 had no file to give. */
  async uncountFetch(name, device) {
    if (!this.ready || !this.open) return;
    const row = this.sql.exec('SELECT n FROM fetched WHERE blob = ? AND device = ?', name, device).toArray()[0];
    if (!row) return;
    this.sql.exec('UPDATE fetched SET n = ? WHERE blob = ? AND device = ?', Math.max(0, row.n - 1), name, device);
  }

  // a blob R2 did not take, its hash not the one signed or its upload broken off: its bytes handed back, its number not
  async forgetBlob(name) {
    if (!this.ready) return;
    const row = this.sql.exec('SELECT bytes FROM blobs WHERE id = ?', name).toArray()[0];
    if (!row) return;
    this.sql.exec('DELETE FROM blobs WHERE id = ?', name);
    this.sql.exec('DELETE FROM pending WHERE blob = ?', name);
    this.sql.exec('DELETE FROM fetched WHERE blob = ?', name);
    this.take(-row.bytes, 0, -row.bytes, 0);
    this.move(-row.bytes, 0, 0);
    await this.report(true);
  }

  // the live socket, the only call that comes as a request
  async fetch(request) {
    if (request.headers.get('Upgrade') !== 'websocket') return refuse(426, 'websocket');
    const { device, refusal } = await this.signed(serial(request), await sha256(new Uint8Array(0)));
    if (refusal) return json(refusal.data, refusal.status);
    // up to SOCKETS_A_DEVICE sockets a device (two Idiographs on one computer share its key, review2's N3): past
    // that the oldest are closed, by the time each was opened
    const open = this.ctx.getWebSockets(device)
      .filter((ws) => ws.readyState === undefined || ws.readyState === 1)
      .map((ws) => ({ ws, at: Number((ws.deserializeAttachment() || {}).at || 0) }))
      .sort((a, b) => a.at - b.at);
    for (const { ws } of open.slice(0, Math.max(0, open.length - (SOCKETS_A_DEVICE - 1)))) {
      try { ws.close(1000, 'replaced'); } catch (err) { /* gone already */ }
    }
    const pair = new WebSocketPair();
    this.ctx.acceptWebSocket(pair[1], [device]);
    pair[1].serializeAttachment({ at: Date.now() });
    return new Response(null, { status: 101, webSocket: pair[0] });
  }

  /* A signed call with its body, read by the Worker: a message, the lead's list of devices, what a device has
     read, or an invite opened (`invite`, its id). */
  async call(s, route, body, invite) {
    const { device, nonce, refusal } = await this.signed(s, await sha256(body));
    if (refusal) return refusal;
    if (this.seenNonce(nonce)) return no(409, 'sent before');
    if (route === 'messages') return this.post(device, nonce, body, new URL(s.url).searchParams.get('blob'));
    if (route === 'invites') return this.openInvite(device, nonce, invite);
    let ask;
    try { ask = JSON.parse(new TextDecoder().decode(body)); } catch (err) { return no(400, 'not JSON'); }
    if (route === 'seen') return this.seen(device, nonce, ask);
    return this.devices(device, nonce, ask);
  }

  /* One envelope. In a project made open one over `small` counts in the day's bytes, in the 250 MB, in the messages'
     share of it (`waitingMessages`) and in the relay's ceiling for messages, and a project with one computer on its
     list takes none. One at or under `small` (a list of people) is outside the day's bytes, so it goes when larger
     ones cannot, and has a cap of its own waiting (`smallWaiting`). Both count in the day's messages and in the
     relay's ceiling. `blob`, when given, is a file put before it, freed when every device has read this message. */
  async post(device, nonce, body, blob) {
    if (body.length === 0) return no(400, 'empty');
    if (blob !== null && blob !== undefined) {
      if (!BLOB.test(blob) || !this.sql.exec('SELECT 1 FROM blobs WHERE id = ?', blob).toArray().length) return no(404, 'no blob');
      if (this.sql.exec('SELECT 1 FROM named WHERE blob = ?', blob).toArray().length) return no(409, 'blob named');
    }
    const small = body.length <= this.limits.small;
    if (this.open) {
      if (!small && this.alone()) return no(409, 'nobody to send to');
      const s = this.sums();
      const over = small ? s.m - s.w + body.length > this.limits.smallWaiting
        : s.b + s.w + body.length > this.limits.waiting || s.w + body.length > this.limits.waitingMessages;
      if (over) return no(429, 'project full', { behind: this.behind() });
      const said = await this.report();
      if (said.messagesFull) return no(503, 'relay full');
    }
    const counted = this.open && small ? 0 : body.length;
    const word = this.fits(counted, 1);
    if (word) return no(429, word);
    const twice = this.once(nonce);
    if (twice) return twice;
    this.take(counted, 1);
    this.sql.exec('INSERT INTO messages(device, at, bytes, body) VALUES (?, ?, ?, ?)', device, now(), body.length, body.buffer);
    const n = this.sql.exec('SELECT last_insert_rowid() AS n').one().n;
    const wake = this.move(0, body.length, small ? 0 : body.length, true);
    if (blob) {
      this.sql.exec('INSERT INTO named(n, blob) VALUES (?, ?)', n, blob);
      this.sql.exec('DELETE FROM pending WHERE blob = ?', blob);
    }
    await this.rearm(wake);
    for (const ws of this.ctx.getWebSockets()) {
      try { ws.send(`new ${n}`); } catch (err) { /* a socket going away is the socket's business */ }
    }
    return ok({ n }, 201);
  }

  async list(s) {
    const { refusal } = await this.signed(s, await sha256(new Uint8Array(0)));
    if (refusal) return refusal;
    const after = Number(new URL(s.url).searchParams.get('after') || 0);
    if (!Number.isInteger(after) || after < 0) return no(400, 'after');
    const out = [];
    let bytes = 0;
    for (const row of this.sql.exec('SELECT n, device, at, bytes, body FROM messages WHERE n > ? ORDER BY n LIMIT ?', after, LIMITS.page)) {
      if (out.length && bytes + row.bytes > LIMITS.pageBytes) break;
      bytes += row.bytes;
      out.push({ n: row.n, device: row.device, at: row.at, body: b64url(row.body) });
    }
    const last = out.length ? out[out.length - 1].n : after;
    const more = this.sql.exec('SELECT 1 FROM messages WHERE n > ? LIMIT 1', last).toArray().length > 0;
    const top = this.sql.exec("SELECT seq AS n FROM sqlite_sequence WHERE name = 'messages'").toArray()[0];
    return ok({ messages: out, more, last: top ? top.n : 0 });
  }

  /* The lead's list of devices. Keys on it and not here are let in, devices here and not on it are
     refused from now on, and their sockets closed. `lead` hands the role to another device on the list. */
  async devices(device, nonce, ask) {
    if (device !== this.meta('lead')) return no(403, 'not the lead');
    const keys = ask && Array.isArray(ask.devices) ? ask.devices : null;
    if (!keys || !keys.length || keys.length > this.most.devices) return no(400, 'devices');
    const listed = new Map();
    for (const k of keys) {
      const raw = unb64url(k);
      if (!raw || raw.length !== 32) return no(400, 'key');
      listed.set(await deviceId(raw), k);
    }
    const lead = ask.lead === undefined ? device : ask.lead;
    if (!listed.has(lead)) return no(400, 'the lead is not on the list');
    for (const id of listed.keys()) {
      if (this.sql.exec('SELECT 1 FROM devices WHERE id = ? AND removed IS NOT NULL', id).toArray().length) {
        return no(409, 'a removed device stays removed');
      }
    }
    const gone = [];
    const active = this.sql.exec('SELECT id FROM devices WHERE removed IS NULL').toArray();
    for (const row of active) {
      if (!listed.has(row.id)) gone.push(row.id);
    }
    const day = today();
    if (this.open) {
      // in a project made open (review2's M2): a list that changes nothing answers at once and writes nothing, a
      // changed one is counted against the day's, and the rows of removed devices kept are capped
      const same = !gone.length && active.length === listed.size && lead === this.meta('lead');
      if (same) return ok({ devices: [...listed.keys()], removed: [], lead });
      const counted = Number(this.meta('lists_day')) === day ? Number(this.meta('lists_n') || 0) : 0;
      if (counted >= this.limits.listsPerDay) return no(429, 'lists today');
      const removed = this.sql.exec('SELECT COUNT(*) AS c FROM devices WHERE removed IS NOT NULL').one().c;
      if (removed + gone.length > this.limits.removedMost) return no(409, 'too many removed');
      const twice = this.once(nonce);
      if (twice) return twice;
      this.setMeta('lists_day', day);
      this.setMeta('lists_n', counted + 1);
    } else {
      const twice = this.once(nonce);
      if (twice) return twice;
    }
    const t = now();
    for (const [id, key] of listed) {
      this.sql.exec('INSERT OR IGNORE INTO devices(id, key, added, removed) VALUES (?, ?, ?, NULL)', id, key, t);
    }
    for (const id of gone) {
      this.sql.exec('UPDATE devices SET removed = ? WHERE id = ?', t, id);
      this.sql.exec('DELETE FROM seen WHERE device = ?', id);
      for (const ws of this.ctx.getWebSockets(id)) {
        try { ws.close(4003, 'removed'); } catch (err) { /* gone already */ }
      }
    }
    if (lead !== this.meta('lead')) this.sql.exec("INSERT OR REPLACE INTO meta(k, v) VALUES ('lead', ?)", lead);
    await this.drop();
    return ok({ devices: [...listed.keys()], removed: gone, lead });
  }

  /* A device's highest number read, never above the highest number given out (review2's M1), so once its mark is
     at the top a further `seen` answers at once and writes nothing, and a mark above the top cannot drop later
     messages before this device has read them. One that does not move it answers at once and writes nothing. */
  async seen(device, nonce, ask) {
    const asked = ask && ask.n;
    if (!Number.isInteger(asked) || asked < 0) return no(400, 'n');
    const top = this.sql.exec("SELECT seq AS n FROM sqlite_sequence WHERE name = 'messages'").toArray()[0];
    const n = Math.min(asked, top ? top.n : 0);
    const row = this.sql.exec('SELECT n FROM seen WHERE device = ?', device).toArray()[0];
    if (n <= (row ? row.n : 0)) return ok({ dropped: 0 });
    const twice = this.once(nonce);
    if (twice) return twice;
    this.sql.exec('INSERT OR REPLACE INTO seen(device, n) VALUES (?, ?)', device, n);
    return ok({ dropped: await this.drop() });
  }

  /* An invite's mailbox opened by a computer on the project, so a joiner's answers can be taken there, at most
     `invitesPerProject` a day. The counter counts it for the operator's usage. */
  async openInvite(device, nonce, invite) {
    const day = today();
    const row = this.sql.exec('SELECT n FROM invites_day WHERE day = ?', day).toArray()[0] || { n: 0 };
    if (this.open && row.n >= this.limits.invitesPerProject) return no(429, 'invites today');
    const twice = this.once(nonce);
    if (twice) return twice;
    this.sql.exec('INSERT OR REPLACE INTO invites_day(day, n) VALUES (?, ?)', day, row.n + 1);
    this.sql.exec('DELETE FROM invites_day WHERE day < ?', day - 2);
    const ns = namespaceIn(this.env, 'INVITES');
    await ns.get(ns.idFromName(invite)).open();
    await counter(this.env).opened();
    return ok({ invite }, 201);
  }

  /* What every device on the list has read is deleted, a device that has read nothing holding all, and with
     each message the file it names, from R2 first, so a fault there leaves the rows for the next try. */
  async drop() {
    const active = this.sql.exec('SELECT d.id, COALESCE(s.n, 0) AS n FROM devices d LEFT JOIN seen s ON s.device = d.id WHERE d.removed IS NULL').toArray();
    if (!active.length) return 0;
    const low = Math.min(...active.map((r) => r.n));
    if (low <= 0) return 0;
    return this.forgetMessages('n <= ?', low);
  }

  // the messages `where` picks deleted, with the files they name, and the sums moved. Answers how many.
  async forgetMessages(where, value) {
    const filesOf = () => this.sql.exec(`SELECT b.id, b.bytes FROM named x JOIN blobs b ON b.id = x.blob WHERE x.n IN (SELECT n FROM messages WHERE ${where})`, value).toArray();
    const sumsOf = () => this.sql.exec(`SELECT COUNT(*) AS c, COALESCE(SUM(bytes), 0) AS m, COALESCE(SUM(CASE WHEN bytes > ? THEN bytes ELSE 0 END), 0) AS w FROM messages WHERE ${where}`, this.limits.small, value).one();
    const before = filesOf();
    if (!sumsOf().c && !before.length) return 0;
    await this.deleteFiles(before.map((f) => f.id));
    // read again after the await, so a drop that ran meanwhile and took some of these is not subtracted twice
    // (review2's L3): what is left is a part of what was read, its files already gone from R2
    const files = filesOf();
    const sums = sumsOf();
    if (!sums.c && !files.length) return 0;
    this.sql.exec(`DELETE FROM named WHERE n IN (SELECT n FROM messages WHERE ${where})`, value);
    const gone = this.sql.exec(`DELETE FROM messages WHERE ${where}`, value).rowsWritten;
    for (const f of files) {
      this.sql.exec('DELETE FROM blobs WHERE id = ?', f.id);
      this.sql.exec('DELETE FROM fetched WHERE blob = ?', f.id);
    }
    this.move(-files.reduce((a, f) => a + f.bytes, 0), -sums.m, -sums.w);
    if (gone && files.length) await this.report(true);
    return gone;
  }

  async deleteFiles(names) {
    const id = this.meta('id');
    if (!id) return;
    for (let i = 0; i < names.length; i += 1000) {
      await this.env.BLOBS.delete(names.slice(i, i + 1000).map((b) => `p/${id}/${b}`));
    }
  }

  // a socket only listens: anything it says but a ping (answered above without waking) closes it
  webSocketMessage(ws) {
    try { ws.close(1008, 'listen only'); } catch (err) { /* closed */ }
  }
  webSocketClose(ws, code) {
    try { ws.close(code === 1005 ? 1000 : code, 'bye'); } catch (err) { /* closed */ }
  }

  /* Once a day, the next alarm set first: anything older than keepDays goes, messages and blobs alike, seen or
     not; in a project made open, a file no message has named for a day (a send broken off after its upload).
     Then the sums are worked out again from the rows, so any drift mends, and told to the counter. A project
     that holds nothing and has taken nothing for idleDays stops its alarm, and its next message or file sets it
     again. */
  async alarm() {
    if (!this.ready || !this.meta('id')) return;
    await this.ctx.storage.setAlarm(Date.now() + this.limits.alarmEvery * 1000);
    const cut = now() - this.limits.keepDays * DAY;
    await this.forgetMessages('at < ?', cut);
    const old = this.sql.exec('SELECT id, bytes FROM blobs WHERE at < ?', cut).toArray();
    const orphans = this.open ? this.sql.exec('SELECT b.id, b.bytes FROM pending p JOIN blobs b ON b.id = p.blob WHERE p.at < ?', now() - this.limits.orphanDays * DAY).toArray() : [];
    const files = [...old, ...orphans.filter((o) => !old.some((x) => x.id === o.id))];
    await this.deleteFiles(files.map((f) => f.id));
    for (const f of files) {
      this.sql.exec('DELETE FROM blobs WHERE id = ?', f.id);
      this.sql.exec('DELETE FROM pending WHERE blob = ?', f.id);
      this.sql.exec('DELETE FROM named WHERE blob = ?', f.id);
      this.sql.exec('DELETE FROM fetched WHERE blob = ?', f.id);
    }
    const s = { ...this.sums(), ...this.counted() };
    const empty = !s.b && !s.m && !this.sql.exec('SELECT 1 FROM blobs LIMIT 1').toArray().length;
    s.idle = empty && now() - Number(s.last || 0) >= this.limits.idleDays * DAY;
    this.keep(s);
    await this.report(true);
    if (s.idle) await this.ctx.storage.deleteAlarm();
  }

  /* The operator's delete: every file in R2, then every row and the alarm. Answers what went. */
  async erase() {
    if (!this.ready) return { files: 0, messages: 0 };
    const files = this.sql.exec('SELECT id FROM blobs').toArray().map((r) => r.id);
    const messages = this.sql.exec('SELECT COUNT(*) AS c FROM messages').one().c;
    await this.deleteFiles(files);
    for (const ws of this.ctx.getWebSockets()) {
      try { ws.close(4004, 'deleted'); } catch (err) { /* gone already */ }
    }
    await this.ctx.storage.deleteAlarm();
    await this.ctx.storage.deleteAll();
    this.ready = false;
    this.cache = null;
    return { files: files.length, messages };
  }
}

/* One invite's mailbox: up to ten sealed join answers, from either side, kept seven days from when a computer on
   a project opened it. Unsigned, since the one answering has no device on any project yet: the invite id comes
   from the invite's secret, which never leaves the two computers, and the answers are sealed with it. A mailbox
   nobody opened takes nothing and gives nothing, and a call to it writes nothing. */
export class Invite extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
  }

  // its table made and its alarm set, by a project's signed call. Opened again, it stays as it is
  async open() {
    if (hasTable(this.sql, 'answers')) return;
    this.sql.exec('CREATE TABLE IF NOT EXISTS answers(k INTEGER PRIMARY KEY AUTOINCREMENT, at INTEGER NOT NULL, body BLOB NOT NULL)');
    await this.ctx.storage.setAlarm(Date.now() + LIMITS.inviteDays * DAY * 1000);
  }

  async answers(after) {
    if (!hasTable(this.sql, 'answers')) return no(404, 'no invite');
    const rows = this.sql.exec('SELECT k, at, body FROM answers WHERE k > ? ORDER BY k', after).toArray();
    return ok({ answers: rows.map((r) => ({ k: r.k, at: r.at, body: b64url(r.body) })) });
  }

  async take(body) {
    if (!hasTable(this.sql, 'answers')) return no(404, 'no invite');
    const count = this.sql.exec('SELECT COUNT(*) AS c FROM answers').one().c;
    if (count >= LIMITS.invitePosts) return no(429, 'invite full');
    this.sql.exec('INSERT INTO answers(at, body) VALUES (?, ?)', now(), body.buffer);
    return ok({ k: this.sql.exec('SELECT last_insert_rowid() AS k').one().k }, 201);
  }

  async alarm() {
    await this.ctx.storage.deleteAll();
  }
}

/* The operator codes' counts of the relay before relayopen. It stays exported because migration v1 made the
   class, and the worker of the first deploy step (relay/test/worker_v1.js) and a rollback to it still use it.
   This worker never calls it. */
export class Operator extends DurableObject {}

/* The relay's one counter (relayopen, 18 November 2026): new projects by UTC day and by address, the day's files,
   invites opened, the operator's allowance of new projects for the day, and each project's last reported sums,
   which overwrite the one before, so there is no running total to drift. A project's daily alarm reports, so a row
   not reported for three days is let go. An address is kept for the day it made a project and deleted after. */
export class Counter extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    this.sql.exec(`
      CREATE TABLE IF NOT EXISTS made(day INTEGER PRIMARY KEY, n INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS made_from(day INTEGER NOT NULL, ip TEXT NOT NULL, n INTEGER NOT NULL, PRIMARY KEY(day, ip));
      CREATE TABLE IF NOT EXISTS days(day INTEGER PRIMARY KEY, files INTEGER NOT NULL, opened INTEGER NOT NULL, allow INTEGER);
      CREATE TABLE IF NOT EXISTS sizes(project TEXT PRIMARY KEY, blobs INTEGER NOT NULL, messages INTEGER NOT NULL, old INTEGER NOT NULL, at INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS made_nonces(nonce TEXT PRIMARY KEY, at INTEGER NOT NULL);
    `);
  }

  // yesterday's addresses and old days' counts let go
  tidy() {
    const day = today();
    this.sql.exec('DELETE FROM made WHERE day < ?', day - 2);
    this.sql.exec('DELETE FROM days WHERE day < ?', day - 2);
    this.sql.exec('DELETE FROM made_from WHERE day < ?', day);
    // a new project's nonce is kept as long as its signed time can stand
    this.sql.exec('DELETE FROM made_nonces WHERE at < ?', now() - 2 * LIMITS.clockSkew);
  }
  day() {
    return this.sql.exec('SELECT files, opened, allow FROM days WHERE day = ?', today()).toArray()[0] || { files: 0, opened: 0, allow: null };
  }
  setDay(d) {
    this.sql.exec('INSERT OR REPLACE INTO days(day, files, opened, allow) VALUES (?, ?, ?, ?)', today(), d.files, d.opened, d.allow);
  }

  /* one more new project today, from `ip`, or the refusal's word. The operator's allowance stands for the day's.
     A nonce seen before is refused, and one is kept only when the project is let in. */
  admit(ip, perDay, perIp, nonce = '') {
    const day = today();
    this.tidy();
    if (nonce && this.sql.exec('SELECT 1 FROM made_nonces WHERE nonce = ?', nonce).toArray().length) {
      return { ok: false, error: 'sent before' };
    }
    const allow = this.day().allow;
    const most = allow === null || allow === undefined ? perDay : allow;
    const all = (this.sql.exec('SELECT n FROM made WHERE day = ?', day).toArray()[0] || { n: 0 }).n;
    if (all >= most) return { ok: false, error: 'projects today' };
    const here = (this.sql.exec('SELECT n FROM made_from WHERE day = ? AND ip = ?', day, ip).toArray()[0] || { n: 0 }).n;
    if (here >= perIp) return { ok: false, error: 'projects from here' };
    this.sql.exec('INSERT OR REPLACE INTO made(day, n) VALUES (?, ?)', day, all + 1);
    this.sql.exec('INSERT OR REPLACE INTO made_from(day, ip, n) VALUES (?, ?, ?)', day, ip, here + 1);
    if (nonce) this.sql.exec('INSERT INTO made_nonces(nonce, at) VALUES (?, ?)', nonce, now());
    return { ok: true };
  }

  // the operator's allowance of new projects for today
  allow(n) {
    this.setDay({ ...this.day(), allow: n });
    return { allowed_today: n };
  }

  // one more invite opened today, for the operator's usage
  opened() {
    const d = this.day();
    this.setDay({ ...d, opened: d.opened + 1 });
  }

  /* A project's sums. With `asking` (a file's PUT), its files' sum is what it would be with one more file, refused
     when that passes the ceiling for a project made open, or when the relay has taken its files of the day, and
     then not recorded. Answers whether the messages are over theirs. */
  report(project, blobs, messages, old, limits, asking) {
    this.tidy();
    this.sql.exec('DELETE FROM sizes WHERE at < ?', now() - 3 * DAY);
    const others = this.sql.exec('SELECT COALESCE(SUM(blobs), 0) AS b, COALESCE(SUM(messages), 0) AS m FROM sizes WHERE project != ?', project).one();
    const messagesFull = !old && others.m + messages > limits.ceilingMessages;
    if (asking && !old) {
      if (others.b + blobs > limits.ceilingBlobs) return { ok: false, error: 'relay full', messagesFull };
      const d = this.day();
      if (d.files >= limits.relayFilesPerDay) return { ok: false, error: 'files today', messagesFull };
      this.setDay({ ...d, files: d.files + 1 });
    }
    this.sql.exec('INSERT OR REPLACE INTO sizes(project, blobs, messages, old, at) VALUES (?, ?, ?, ?, ?)', project, blobs, messages, old ? 1 : 0, now());
    return { ok: true, messagesFull };
  }

  forget(project) {
    this.sql.exec('DELETE FROM sizes WHERE project = ?', project);
  }

  usage(limits) {
    this.tidy();
    const rows = this.sql.exec('SELECT project, blobs, messages, old, at FROM sizes ORDER BY blobs + messages DESC').toArray();
    const made = (this.sql.exec('SELECT n FROM made WHERE day = ?', today()).toArray()[0] || { n: 0 }).n;
    const from = this.sql.exec('SELECT COUNT(*) AS c FROM made_from WHERE day = ?', today()).one().c;
    const d = this.day();
    return {
      projects: rows.map((r) => ({ project: r.project, files: r.blobs, messages: r.messages, made_open: !r.old, reported: r.at })),
      project_count: rows.length,
      files: rows.reduce((a, r) => a + r.blobs, 0), messages: rows.reduce((a, r) => a + r.messages, 0),
      ceiling_files: limits.ceilingBlobs, ceiling_messages: limits.ceilingMessages,
      made_today: made, made_from_addresses: from,
      projects_per_day: d.allow === null || d.allow === undefined ? limits.projectsPerDay : d.allow,
      files_today: d.files, files_per_day: limits.relayFilesPerDay, invites_opened_today: d.opened,
    };
  }
}
