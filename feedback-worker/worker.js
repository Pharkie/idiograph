/* Idiograph's feedback collector: a Cloudflare Worker that writes each note a tester sends from
   the app as one row of a D1 table, which Adam reads from time to time with notes.sh or the route
   below.

     POST /v1/feedback  {"text", "contact", "version", "platform", "screen", "agent", "at"}
                        answers {"ok": true, "id": <the row's id>}
     GET  /v1/notes     the newest 200 notes as JSON, or with ?format=html as a plain table, only
                        with the header `Authorization: Bearer <ADMIN_TOKEN>`, and 401 otherwise

   The app's own server calls it, never a browser, so it allows no CORS and answers no preflight.
   It keeps no raw IP: a row carries the SHA-256 of the IP and the IP_SALT secret, and the hourly
   limit counts those. `at` is the collector's own clock, so the limit cannot be dated around. No
   cookies, no analytics. ADMIN_TOKEN and IP_SALT are Worker secrets, set with `wrangler secret
   put`, and never written in any file. */

const MAX_BODY = 8192;        // bytes, the whole JSON body
const HOURLY = 30;            // notes an hour from one hashed IP
const LIST = 200;             // notes GET /v1/notes answers with, newest first
// the screens a note may name, the same short words as FEEDBACK_SCREENS in the app's server.py
const SCREENS = ['home', 'project', 'statements', 'pets', 'gets', 'sift', 'searches', 'trace'];
const LIMITS = { contact: 200, version: 40, platform: 160, agent: 400 };
const COLUMNS = ['id', 'at', 'text', 'contact', 'version', 'platform', 'screen', 'agent'];

const json = (data, status = 200, extra = {}) => new Response(JSON.stringify(data), {
  status,
  headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', ...extra },
});
const refuse = (status, error, extra = {}) => json({ ok: false, error }, status, extra);

async function sha256(text) {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

/* every byte compared whatever the first difference, so the time a wrong token takes says nothing */
function same(a, b) {
  const x = new TextEncoder().encode(String(a));
  const y = new TextEncoder().encode(String(b));
  let diff = x.length ^ y.length;
  for (let i = 0; i < Math.max(x.length, y.length); i += 1) diff |= (x[i] || 0) ^ (y[i] || 0);
  return diff === 0;
}

/* the token travels in the header alone, never in the address */
function authorised(request, env) {
  const token = env.ADMIN_TOKEN;
  const found = /^Bearer\s+(\S+)$/i.exec((request.headers.get('authorization') || '').trim());
  return Boolean(token && found && same(found[1], token));
}

const field = (value, limit) => (typeof value === 'string' ? value.trim().slice(0, limit) : '');

/* The row a note becomes: the text whole, the rest trimmed to a length, the screen one of the words
   in SCREENS or nothing, never the page's own text, and the hash in place of the IP. Nothing else
   from the body is kept. */
export function noteRow(body, at, ipHash) {
  return {
    at,
    text: body.text.trim(),
    contact: field(body.contact, LIMITS.contact),
    version: field(body.version, LIMITS.version),
    platform: field(body.platform, LIMITS.platform),
    screen: SCREENS.includes(body.screen) ? body.screen : '',
    agent: field(body.agent, LIMITS.agent),
    ip_hash: ipHash,
  };
}

async function postNote(request, env) {
  if (Number(request.headers.get('content-length') || 0) > MAX_BODY) return refuse(413, 'The note is over 8 KB.');
  const raw = await request.text();
  if (new TextEncoder().encode(raw).length > MAX_BODY) return refuse(413, 'The note is over 8 KB.');
  let body;
  try {
    body = JSON.parse(raw);
  } catch {
    return refuse(400, 'The body is not JSON.');
  }
  if (!body || typeof body !== 'object' || Array.isArray(body) || typeof body.text !== 'string' || !body.text.trim()) {
    return refuse(400, 'The body needs a text string.');
  }
  if (!env.IP_SALT) return refuse(500, 'The collector has no IP_SALT secret.');
  const ipHash = await sha256(`${env.IP_SALT}:${request.headers.get('cf-connecting-ip') || ''}`);
  const now = new Date();
  const since = new Date(now.getTime() - 3600 * 1000).toISOString();
  try {
    const sent = await env.DB.prepare('SELECT COUNT(*) AS n FROM notes WHERE ip_hash = ? AND at > ?')
      .bind(ipHash, since).first();
    if (sent && Number(sent.n) >= HOURLY) return refuse(429, 'Too many notes from here in the last hour.');
    const row = noteRow(body, now.toISOString(), ipHash);
    const done = await env.DB.prepare(
      'INSERT INTO notes (at, text, contact, version, platform, screen, agent, ip_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
    ).bind(row.at, row.text, row.contact, row.version, row.platform, row.screen, row.agent, row.ip_hash).run();
    return json({ ok: true, id: done.meta.last_row_id });
  } catch {
    return refuse(500, 'The note could not be stored.');
  }
}

const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

/* The notes as a plain page in the app's faces and colours, light or dark as the system is, with
   no script and nothing fetched. */
export function notesPage(notes) {
  const rows = notes.map((n) => `<tr><td class="mono">${esc(n.id)}</td><td class="mono">${esc(n.at)}</td>`
    + `<td class="note">${esc(n.text)}</td><td>${esc(n.contact)}</td><td>${esc(n.screen)}</td>`
    + `<td class="small">${esc(n.version)}<br>${esc(n.platform)}</td><td class="small">${esc(n.agent)}</td></tr>`).join('\n');
  return `<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Idiograph feedback</title>
<style>
:root { --paper: #FBF7EF; --ink: #1F1B16; --ink-soft: #554C41; --ink-faint: #8C8172; --rule: #E3D9C7;
  --serif: "Iowan Old Style", "Charter", "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif;
  --sans: "Avenir Next", "Avenir", "Gill Sans", "Gill Sans MT", "Segoe UI", system-ui, sans-serif;
  --mono: "SF Mono", ui-monospace, Menlo, Consolas, monospace; }
@media (prefers-color-scheme: dark) {
  :root { --paper: #16130E; --ink: #EFE7D9; --ink-soft: #B6AC9B; --ink-faint: #7B7263; --rule: #2E2820; }
}
body { margin: 0; padding: 32px 24px; background: var(--paper); color: var(--ink); font-family: var(--sans); font-size: 13px; }
h1 { font-family: var(--serif); font-weight: 400; font-size: 24px; margin: 0 0 4px; }
p { color: var(--ink-faint); margin: 0 0 20px; }
table { border-collapse: collapse; width: 100%; }
th { text-align: left; font-size: 11px; letter-spacing: .12em; text-transform: uppercase; font-weight: 600;
  color: var(--ink-soft); padding: 8px 10px; border-bottom: 1px solid var(--rule); }
td { vertical-align: top; padding: 10px; border-bottom: 1px solid var(--rule); }
td.note { font-family: var(--serif); font-size: 15px; line-height: 1.5; white-space: pre-wrap; min-width: 18em; }
.mono { font-family: var(--mono); font-size: 12px; white-space: nowrap; }
.small { font-size: 11.5px; color: var(--ink-faint); }
</style></head><body>
<h1>Idiograph feedback</h1>
<p>${notes.length === 1 ? 'One note' : `${notes.length} notes`}, newest first.</p>
<table><thead><tr><th>Id</th><th>At</th><th>Note</th><th>Contact</th><th>Screen</th><th>Version and system</th><th>Browser</th></tr></thead>
<tbody>
${rows}
</tbody></table>
</body></html>
`;
}

async function listNotes(request, env, url) {
  if (!authorised(request, env)) return refuse(401, 'This needs the admin token.', { 'www-authenticate': 'Bearer' });
  let notes;
  try {
    const { results } = await env.DB.prepare(`SELECT ${COLUMNS.join(', ')} FROM notes ORDER BY id DESC LIMIT ?`)
      .bind(LIST).all();
    notes = results || [];
  } catch {
    return refuse(500, 'The notes could not be read.');
  }
  if (url.searchParams.get('format') === 'html') {
    return new Response(notesPage(notes), {
      headers: {
        'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store', 'referrer-policy': 'no-referrer',
        'content-security-policy': "default-src 'none'; style-src 'unsafe-inline'",
      },
    });
  }
  return json({ ok: true, notes });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method !== 'POST' && request.method !== 'GET') {
      return refuse(405, 'Only POST and GET.', { allow: 'GET, POST' });
    }
    if (url.pathname === '/v1/feedback') {
      return request.method === 'POST' ? postNote(request, env) : refuse(405, 'Send a note with POST.', { allow: 'POST' });
    }
    if (url.pathname === '/v1/notes') {
      return request.method === 'GET' ? listNotes(request, env, url) : refuse(405, 'Read the notes with GET.', { allow: 'GET' });
    }
    return refuse(404, 'No such path.');
  },
};
