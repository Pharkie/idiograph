// SPDX-License-Identifier: AGPL-3.0-or-later
/* Idiograph's relay, the mailbox Working together passes sealed messages through (working together,
   build 3, 8 November 2026). Copyright (C) 2026 Adam Knowles. This program is free software: you can
   redistribute it and/or modify it under the terms of the GNU Affero General Public License as published
   by the Free Software Foundation, version 3 or any later version. It comes with no warranty. See LICENSE
   at the repository's root.

   The relay never sees a word of a project. Every message and every blob is sealed on the sender's
   computer before it comes here, and the relay keeps it, numbers it and hands it on. It knows a random
   project id, the devices' public keys, times, sizes and counts, and nothing else.

     POST /relay/v1/projects                 make a project with an operator code and the lead's key
     PUT  /relay/v1/p/:id/devices            the lead's list of device keys, the only devices let in
     POST /relay/v1/p/:id/messages           one sealed envelope, answered with its relay number n
     GET  /relay/v1/p/:id/messages?after=N   up to 200 envelopes after N
     GET  /relay/v1/p/:id/live               a WebSocket that says "new N" when a message comes
     PUT  /relay/v1/p/:id/blobs/:blob        a sealed file above a message's size, into R2
     GET  /relay/v1/p/:id/blobs/:blob        the same file back
     POST /relay/v1/p/:id/seen               a device's highest number read
     POST /relay/v1/invites/:invite          a sealed join answer, unsigned, limited by IP
     GET  /relay/v1/invites/:invite?after=K  the answers after the K-th

   Every call but an invite's is signed by the device making it: X-Device (its id, 32 hex), X-Time (Unix
   seconds, within five minutes of the relay's clock), X-Nonce (16 random bytes in hex, once only) and
   X-Sig (base64url Ed25519) over "<METHOD>\n<path and query>\n<X-Time>\n<X-Nonce>\n<SHA-256 of the
   body, hex>". A blob's PUT names its body's
   SHA-256 in X-Content-SHA256, which R2 checks as it stores it, so a 200 MB body is never held here.
   A device id is the first 16 bytes of the SHA-256 of its raw Ed25519 public key. */

import { DurableObject } from 'cloudflare:workers';

export const LIMITS = {
  message: 1536 * 1024,          // bytes, one envelope: a 1 MB padded inner message in its base64 and fields
  blob: 200 * 1024 * 1024,       // bytes, one sealed blob
  dayBytes: 2 * 1024 ** 3,       // bytes a project takes in a day, messages and blobs together
  dayMessages: 5000,             // messages a project takes in a day
  projectsPerCode: 20,           // projects one operator code makes
  page: 200,                     // envelopes one GET answers with at most
  pageBytes: 8 * 1024 * 1024,    // and the bytes it stops at, so a page of large ones stays small
  devices: 64,                   // devices on one project's list
  clockSkew: 300,                // seconds X-Time may stand from the relay's clock
  keepDays: 90,                  // days anything is kept, seen by all or not
  invite: 4096,                  // bytes, one join answer
  invitePosts: 10,               // answers one invite holds
  inviteDays: 7,                 // days an invite lives from its first answer
};

const PREFIX = '/relay/v1';
const HEX32 = /^[0-9a-f]{32}$/;
const BLOB = /^[A-Za-z0-9_-]{16,64}$/;
const DAY = 86400;
const enc = new TextEncoder();

const json = (data, status = 200) => new Response(JSON.stringify(data), {
  status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
});
const refuse = (status, error) => json({ ok: false, error }, status);
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

function codes(env) {
  return String(env.OPERATOR_CODES || '').split(',').map((c) => c.trim()).filter((c) => c.length >= 16);
}

async function makeProject(request, env) {
  const body = new Uint8Array(await request.arrayBuffer());
  if (body.length > 4096) return refuse(413, 'too large');
  let ask;
  try { ask = JSON.parse(new TextDecoder().decode(body)); } catch (err) { return refuse(400, 'not JSON'); }
  const key = unb64url(ask && ask.key);
  if (!key || key.length !== 32) return refuse(400, 'key');
  const code = typeof ask.code === 'string' ? codes(env).find((c) => sameText(c, ask.code)) : null;
  if (!code) return refuse(403, 'operator code');
  if ((request.headers.get('X-Device') || '') !== await deviceId(key)) return refuse(401, 'device');
  const bad = await checkSignature(request, key, await sha256(body));
  if (bad) return bad;
  // the code's count of projects, one Durable Object per code, named by the code's hash
  const ledger = namespaceIn(env, 'OPERATORS').get(namespaceIn(env, 'OPERATORS').idFromName(await sha256(enc.encode(code))));
  const counted = await ledger.take(LIMITS.projectsPerCode);
  if (!counted) return refuse(429, 'projects for this code');
  const id = hex(crypto.getRandomValues(new Uint8Array(16)));
  const box = projects(env).get(projects(env).idFromName(id));
  await box.init(id, b64url(key));
  return json({ ok: true, project: id }, 201);
}

async function invite(request, env, id) {
  if (env.INVITE_LIMIT && typeof env.INVITE_LIMIT.limit === 'function') {
    const ip = request.headers.get('CF-Connecting-IP') || 'local';
    const { success } = await env.INVITE_LIMIT.limit({ key: ip });
    if (!success) return refuse(429, 'slow down');
  }
  const ns = namespaceIn(env, 'INVITES');
  return ns.get(ns.idFromName(id)).fetch(request);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!url.pathname.startsWith(PREFIX + '/')) return refuse(404, 'not here');
    const parts = url.pathname.slice(PREFIX.length + 1).split('/');
    try {
      if (parts.length === 1 && parts[0] === 'projects') {
        return request.method === 'POST' ? await makeProject(request, env) : refuse(405, 'method');
      }
      if (parts[0] === 'invites' && parts.length === 2 && HEX32.test(parts[1])) {
        return ['POST', 'GET'].includes(request.method) ? await invite(request, env, parts[1]) : refuse(405, 'method');
      }
      if (parts[0] === 'p' && parts.length >= 3 && HEX32.test(parts[1])) {
        const id = parts[1];
        const box = projects(env).get(projects(env).idFromName(id));
        if (parts[2] === 'blobs' && parts.length === 4 && BLOB.test(parts[3])) return await blob(request, env, box, id, parts[3]);
        if (parts.length === 3 && ['devices', 'messages', 'live', 'seen'].includes(parts[2])) return await box.fetch(request);
      }
      return refuse(404, 'not here');
    } catch (err) {
      console.error('relay', err && err.stack ? err.stack : String(err));
      return refuse(500, 'relay');
    }
  },
};

/* A blob goes straight from the request to R2, never through the Durable Object, which only checks the
   signature and the day's bytes first. R2 refuses a body whose SHA-256 is not the one signed. */
async function blob(request, env, box, id, name) {
  const key = `p/${id}/${name}`;
  if (request.method === 'PUT') {
    const size = Number(request.headers.get('content-length') || NaN);
    const hash = (request.headers.get('X-Content-SHA256') || '').toLowerCase();
    if (!Number.isInteger(size) || size < 0) return refuse(411, 'length');
    if (size > LIMITS.blob) return refuse(413, 'too large');
    if (!/^[0-9a-f]{64}$/.test(hash)) return refuse(400, 'hash');
    const allowed = await box.allowBlob(serial(request), name, size, hash);
    if (allowed.status !== 200) return refuse(allowed.status, allowed.error);
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
    if (allowed.status !== 200) return refuse(allowed.status, allowed.error);
    const object = await env.BLOBS.get(key);
    if (!object) return refuse(404, 'no blob');
    return new Response(object.body, { headers: { 'content-type': 'application/octet-stream', 'content-length': String(object.size) } });
  }
  return refuse(405, 'method');
}

// what a request's signature rests on, passed to a Durable Object's method in place of the request
function serial(request) {
  return { method: request.method, url: request.url, headers: Object.fromEntries(['X-Device', 'X-Time', 'X-Nonce', 'X-Sig'].map((h) => [h, request.headers.get(h) || ''])) };
}
function unserial(s) {
  return new Request(s.url, { method: s.method, headers: s.headers });
}

/* One project's mailbox. Its SQLite holds the devices let in, the sealed messages by number, what each
   device has read, the blobs' sizes and the day's counts. */
export class Project extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    this.sql.exec(`
      CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
      CREATE TABLE IF NOT EXISTS devices(id TEXT PRIMARY KEY, key TEXT NOT NULL, added INTEGER NOT NULL, removed INTEGER);
      CREATE TABLE IF NOT EXISTS messages(n INTEGER PRIMARY KEY AUTOINCREMENT, device TEXT NOT NULL, at INTEGER NOT NULL, bytes INTEGER NOT NULL, body BLOB NOT NULL);
      CREATE TABLE IF NOT EXISTS seen(device TEXT PRIMARY KEY, n INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS blobs(id TEXT PRIMARY KEY, bytes INTEGER NOT NULL, at INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS usage(day INTEGER PRIMARY KEY, bytes INTEGER NOT NULL, messages INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS nonces(nonce TEXT PRIMARY KEY, at INTEGER NOT NULL);
    `);
    // a ping is answered without waking the object, so a quiet socket costs nothing
    ctx.setWebSocketAutoResponse(new WebSocketRequestResponsePair('ping', 'pong'));
  }

  meta(k) {
    const row = this.sql.exec('SELECT v FROM meta WHERE k = ?', k).toArray()[0];
    return row ? row.v : null;
  }

  async init(id, leadKey) {
    const key = unb64url(leadKey);
    const lead = await deviceId(key);
    this.sql.exec('INSERT OR REPLACE INTO meta(k, v) VALUES (?, ?), (?, ?), (?, ?)', 'id', id, 'lead', lead, 'made', String(now()));
    this.sql.exec('INSERT OR REPLACE INTO devices(id, key, added, removed) VALUES (?, ?, ?, NULL)', lead, leadKey, now());
    await this.ctx.storage.setAlarm(Date.now() + DAY * 1000);
  }

  /* The device behind a request, its signature checked and its signature not seen before, or the
     refusal. `bodyHash` as checkSignature takes it. */
  async who(request, bodyHash) {
    if (!this.meta('id')) return { refusal: refuse(404, 'no project') };
    const device = request.headers.get('X-Device') || '';
    const row = this.sql.exec('SELECT key, removed FROM devices WHERE id = ?', device).toArray()[0];
    if (!row) return { refusal: refuse(403, 'device') };
    if (row.removed) return { refusal: refuse(403, 'removed') };
    const bad = await checkSignature(request, unb64url(row.key), bodyHash);
    if (bad) return { refusal: bad };
    // a nonce is good once: a copy of a request sent again inside the five minutes is refused
    const nonce = request.headers.get('X-Nonce');
    this.sql.exec('DELETE FROM nonces WHERE at < ?', now() - 2 * LIMITS.clockSkew);
    if (this.sql.exec('SELECT 1 FROM nonces WHERE nonce = ?', nonce).toArray().length) return { refusal: refuse(409, 'sent before') };
    this.sql.exec('INSERT INTO nonces(nonce, at) VALUES (?, ?)', nonce, now());
    return { device };
  }

  // the day's counts, false when `bytes` and one more message (or none, for a blob) would pass them
  take(bytes, messages) {
    const day = today();
    const row = this.sql.exec('SELECT bytes, messages FROM usage WHERE day = ?', day).toArray()[0] || { bytes: 0, messages: 0 };
    if (row.bytes + bytes > LIMITS.dayBytes || row.messages + messages > LIMITS.dayMessages) return false;
    this.sql.exec('INSERT OR REPLACE INTO usage(day, bytes, messages) VALUES (?, ?, ?)', day, row.bytes + bytes, row.messages + messages);
    this.sql.exec('DELETE FROM usage WHERE day < ?', day - 2);
    return true;
  }

  async allowBlob(s, name, size, hash) {
    const { device, refusal } = await this.who(unserial(s), hash);
    if (refusal) return { status: refusal.status, error: (await refusal.json()).error };
    if (size >= 0) {
      if (!this.take(size, 0)) return { status: 429, error: 'day' };
      this.sql.exec('INSERT OR REPLACE INTO blobs(id, bytes, at) VALUES (?, ?, ?)', name, size, now());
    } else if (!this.sql.exec('SELECT 1 FROM blobs WHERE id = ?', name).toArray().length) {
      return { status: 404, error: 'no blob' };
    }
    return { status: 200, device };
  }

  // a blob R2 refused, its hash not the one signed
  forgetBlob(name) {
    this.sql.exec('DELETE FROM blobs WHERE id = ?', name);
  }

  async fetch(request) {
    const url = new URL(request.url);
    const route = url.pathname.split('/')[5];
    if (route === 'live') return this.live(request);
    if (route === 'messages' && request.method === 'GET') return this.list(request, url);
    if (request.method !== (route === 'devices' ? 'PUT' : 'POST')) return refuse(405, 'method');
    const length = Number(request.headers.get('content-length') || 0);
    if (length > LIMITS.message) return refuse(413, 'too large');
    const body = new Uint8Array(await request.arrayBuffer());
    if (body.length > LIMITS.message) return refuse(413, 'too large');
    const { device, refusal } = await this.who(request, await sha256(body));
    if (refusal) return refusal;
    if (route === 'messages') return this.post(device, body);
    let ask;
    try { ask = JSON.parse(new TextDecoder().decode(body)); } catch (err) { return refuse(400, 'not JSON'); }
    if (route === 'seen') return this.seen(device, ask);
    return this.devices(device, ask);
  }

  post(device, body) {
    if (body.length === 0) return refuse(400, 'empty');
    if (!this.take(body.length, 1)) return refuse(429, 'day');
    this.sql.exec('INSERT INTO messages(device, at, bytes, body) VALUES (?, ?, ?, ?)', device, now(), body.length, body.buffer);
    const n = this.sql.exec('SELECT last_insert_rowid() AS n').one().n;
    for (const ws of this.ctx.getWebSockets()) {
      try { ws.send(`new ${n}`); } catch (err) { /* a socket going away is the socket's business */ }
    }
    return json({ ok: true, n }, 201);
  }

  async list(request, url) {
    const { refusal } = await this.who(request, await sha256(new Uint8Array(0)));
    if (refusal) return refusal;
    const after = Number(url.searchParams.get('after') || 0);
    if (!Number.isInteger(after) || after < 0) return refuse(400, 'after');
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
    return json({ ok: true, messages: out, more, last: top ? top.n : 0 });
  }

  /* The lead's list of devices. Keys on it and not here are let in, devices here and not on it are
     refused from now on, and their sockets closed. `lead` hands the role to another device on the list. */
  async devices(device, ask) {
    if (device !== this.meta('lead')) return refuse(403, 'not the lead');
    const keys = ask && Array.isArray(ask.devices) ? ask.devices : null;
    if (!keys || !keys.length || keys.length > LIMITS.devices) return refuse(400, 'devices');
    const listed = new Map();
    for (const k of keys) {
      const raw = unb64url(k);
      if (!raw || raw.length !== 32) return refuse(400, 'key');
      listed.set(await deviceId(raw), k);
    }
    const lead = ask.lead === undefined ? device : ask.lead;
    if (!listed.has(lead)) return refuse(400, 'the lead is not on the list');
    const t = now();
    for (const id of listed.keys()) {
      if (this.sql.exec('SELECT 1 FROM devices WHERE id = ? AND removed IS NOT NULL', id).toArray().length) {
        return refuse(409, 'a removed device stays removed');
      }
    }
    for (const [id, key] of listed) {
      this.sql.exec('INSERT OR IGNORE INTO devices(id, key, added, removed) VALUES (?, ?, ?, NULL)', id, key, t);
    }
    const gone = [];
    for (const row of this.sql.exec('SELECT id FROM devices WHERE removed IS NULL').toArray()) {
      if (!listed.has(row.id)) gone.push(row.id);
    }
    for (const id of gone) {
      this.sql.exec('UPDATE devices SET removed = ? WHERE id = ?', t, id);
      this.sql.exec('DELETE FROM seen WHERE device = ?', id);
      for (const ws of this.ctx.getWebSockets(id)) {
        try { ws.close(4003, 'removed'); } catch (err) { /* gone already */ }
      }
    }
    this.sql.exec("INSERT OR REPLACE INTO meta(k, v) VALUES ('lead', ?)", lead);
    this.drop();
    return json({ ok: true, devices: [...listed.keys()], removed: gone, lead });
  }

  seen(device, ask) {
    const n = ask && ask.n;
    if (!Number.isInteger(n) || n < 0) return refuse(400, 'n');
    const row = this.sql.exec('SELECT n FROM seen WHERE device = ?', device).toArray()[0];
    if (!row || n > row.n) this.sql.exec('INSERT OR REPLACE INTO seen(device, n) VALUES (?, ?)', device, n);
    return json({ ok: true, dropped: this.drop() });
  }

  // what every device on the list has read is deleted, a device that has read nothing holding all
  drop() {
    const active = this.sql.exec('SELECT d.id, COALESCE(s.n, 0) AS n FROM devices d LEFT JOIN seen s ON s.device = d.id WHERE d.removed IS NULL').toArray();
    if (!active.length) return 0;
    const low = Math.min(...active.map((r) => r.n));
    if (low <= 0) return 0;
    return this.sql.exec('DELETE FROM messages WHERE n <= ?', low).rowsWritten;
  }

  async live(request) {
    if (request.headers.get('Upgrade') !== 'websocket') return refuse(426, 'websocket');
    const { device, refusal } = await this.who(request, await sha256(new Uint8Array(0)));
    if (refusal) return refusal;
    const pair = new WebSocketPair();
    this.ctx.acceptWebSocket(pair[1], [device]);
    return new Response(null, { status: 101, webSocket: pair[0] });
  }

  // a socket only listens: anything it says but a ping (answered above without waking) is ignored
  webSocketMessage() {}
  webSocketClose(ws, code) {
    try { ws.close(code === 1005 ? 1000 : code, 'bye'); } catch (err) { /* closed */ }
  }

  // once a day: anything older than keepDays goes, messages and blobs alike, seen or not
  async alarm() {
    const cut = now() - LIMITS.keepDays * DAY;
    this.sql.exec('DELETE FROM messages WHERE at < ?', cut);
    const old = this.sql.exec('SELECT id FROM blobs WHERE at < ?', cut).toArray().map((r) => r.id);
    const id = this.meta('id');
    if (old.length && id) await this.env.BLOBS.delete(old.map((b) => `p/${id}/${b}`));
    this.sql.exec('DELETE FROM blobs WHERE at < ?', cut);
    await this.ctx.storage.setAlarm(Date.now() + DAY * 1000);
  }
}

/* One invite's mailbox: up to ten sealed join answers, from either side, kept seven days from the
   first. Unsigned, since the one answering has no device on any project yet: the invite id comes from
   the invite's secret, which never leaves the two computers, and the answers are sealed with it. */
export class Invite extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    this.sql.exec('CREATE TABLE IF NOT EXISTS answers(k INTEGER PRIMARY KEY AUTOINCREMENT, at INTEGER NOT NULL, body BLOB NOT NULL)');
  }

  async fetch(request) {
    const first = this.sql.exec('SELECT at FROM answers ORDER BY k LIMIT 1').toArray()[0];
    if (first && now() - first.at > LIMITS.inviteDays * DAY) {
      await this.ctx.storage.deleteAll();
      return refuse(410, 'invite over');
    }
    if (request.method === 'GET') {
      const after = Number(new URL(request.url).searchParams.get('after') || 0);
      if (!Number.isInteger(after) || after < 0) return refuse(400, 'after');
      const rows = this.sql.exec('SELECT k, at, body FROM answers WHERE k > ? ORDER BY k', after).toArray();
      return json({ ok: true, answers: rows.map((r) => ({ k: r.k, at: r.at, body: b64url(r.body) })) });
    }
    if (Number(request.headers.get('content-length') || 0) > LIMITS.invite) return refuse(413, 'too large');
    const body = new Uint8Array(await request.arrayBuffer());
    if (!body.length) return refuse(400, 'empty');
    if (body.length > LIMITS.invite) return refuse(413, 'too large');
    const count = this.sql.exec('SELECT COUNT(*) AS c FROM answers').one().c;
    if (count >= LIMITS.invitePosts) return refuse(429, 'invite full');
    this.sql.exec('INSERT INTO answers(at, body) VALUES (?, ?)', now(), body.buffer);
    if (!first) await this.ctx.storage.setAlarm(Date.now() + LIMITS.inviteDays * DAY * 1000);
    return json({ ok: true, k: this.sql.exec('SELECT last_insert_rowid() AS k').one().k }, 201);
  }

  async alarm() {
    await this.ctx.storage.deleteAll();
  }
}

// how many projects each operator code has made, one object per code
export class Operator extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    this.sql.exec('CREATE TABLE IF NOT EXISTS made(k INTEGER PRIMARY KEY AUTOINCREMENT, at INTEGER NOT NULL)');
  }

  take(limit) {
    if (this.sql.exec('SELECT COUNT(*) AS c FROM made').one().c >= limit) return false;
    this.sql.exec('INSERT INTO made(at) VALUES (?)', now());
    return true;
  }
}
