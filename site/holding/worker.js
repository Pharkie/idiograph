// SPDX-License-Identifier: AGPL-3.0-or-later
// The holding page's Worker script: it runs first for the Screenshots clips and the home page's film alone
// (`run_worker_first` in wrangler.jsonc) and does one thing, answers a Range request. Cloudflare's static assets
// send a whole file with a 200 whatever a request asks for and never say they take byte ranges, and a browser that
// plays a video by asking for pieces of it (Safari and every WebKit, a looping clip's seek back to the start) needs
// the 206 and the Content-Range. Everything else is the assets' answer as it was, with Accept-Ranges added.
// It keeps nothing, logs nothing, sets no cookie and reads nothing of the visitor but the Range line.

const keep = ['content-type', 'etag', 'last-modified', 'cache-control'];

// bytes=a-b, bytes=a-, bytes=-n: [start, end] clamped to the file, null for a line it should ignore (more than one
// range, another unit, nonsense: the whole file is the right answer), 'none' for a range the file cannot give
export function parseRange(line, size) {
  const m = /^bytes=(\d*)-(\d*)$/.exec((line || '').trim());
  if (!m || (m[1] === '' && m[2] === '')) return null;
  if (m[1] === '') {
    const n = Number(m[2]);
    return n === 0 || size === 0 ? 'none' : [Math.max(size - n, 0), size - 1];
  }
  const start = Number(m[1]);
  const end = m[2] === '' ? size - 1 : Math.min(Number(m[2]), size - 1);
  if (start >= size) return 'none';
  if (end < start) return null;
  return [start, end];
}

// Sizes learnt by counting a file once, by its ETag, for assets that send no Content-Length of their own
// (wrangler's local assets are one). A size of a file, nothing of a visitor.
const sizes = new Map();

async function count(body) {
  const reader = body.getReader();
  let n = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) return n;
    n += value.byteLength;
  }
}

export async function handle(request, env) {
  if (request.method !== 'GET' && request.method !== 'HEAD') return env.ASSETS.fetch(request);
  const wanted = request.headers.get('range');
  // the assets are asked as the browser asked, less the range, so a revalidation still gets its 304
  const headers = new Headers(request.headers);
  headers.delete('range');
  headers.delete('if-range');
  // always as a GET: the assets leave Content-Length off a HEAD
  const ask = () => env.ASSETS.fetch(new Request(request.url, { method: 'GET', headers }));
  let res = await ask();
  const out = new Headers(res.headers);
  out.set('accept-ranges', 'bytes');
  const etag = res.headers.get('etag');
  let size = res.headers.has('content-length') ? Number(res.headers.get('content-length')) : NaN;
  if (!Number.isInteger(size) || size < 0) size = etag && res.status === 200 ? sizes.get(etag) ?? NaN : NaN;
  if (Number.isNaN(size) && etag && res.status === 200 && (request.method === 'HEAD' || wanted)) {
    // counted as it streams past, never held, then the file is asked for again
    size = await count(res.body);
    if (sizes.size > 64) sizes.clear();
    sizes.set(etag, size);
    res = await ask();
  }
  if (!Number.isNaN(size) && res.status === 200) out.set('content-length', String(size));
  if (request.method === 'HEAD') {
    if (res.body) res.body.cancel();
    return new Response(null, { status: res.status, headers: out });
  }
  if (!wanted || res.status !== 200) return new Response(res.status === 304 ? null : res.body, { status: res.status, headers: out });
  const ifRange = request.headers.get('if-range');
  if (ifRange && ifRange !== etag) return new Response(res.body, { status: 200, headers: out });
  if (!Number.isNaN(size)) return streamed(res, wanted, size, out);
  // no size and no ETag to remember one by: the only case that reads the file whole
  const body = await res.arrayBuffer();
  const total = body.byteLength;
  const r = parseRange(wanted, total);
  if (r === null) return new Response(body, { status: 200, headers: out });
  if (r === 'none') return unsatisfiable(total);
  return new Response(body.slice(r[0], r[1] + 1), { status: 206, headers: piece(out, r, total) });
}

function unsatisfiable(size) {
  return new Response(null, { status: 416, headers: { 'content-range': `bytes */${size}`, 'accept-ranges': 'bytes' } });
}

function piece(out, r, size) {
  const h = new Headers({ 'accept-ranges': 'bytes', 'content-range': `bytes ${r[0]}-${r[1]}/${size}`, 'content-length': String(r[1] - r[0] + 1) });
  for (const k of keep) if (out.has(k)) h.set(k, out.get(k));
  return h;
}

// the size is known: the file is never held whole. The whole file goes through as it is, any other range through a
// stream that skips to the start and stops after the end, which cancels what is left of the file
function streamed(res, wanted, size, out) {
  const r = parseRange(wanted, size);
  if (r === null) return new Response(res.body, { status: 200, headers: out });
  if (r === 'none') {
    if (res.body) res.body.cancel();
    return unsatisfiable(size);
  }
  const [start, end] = r;
  if (start === 0 && end === size - 1) return new Response(res.body, { status: 206, headers: piece(out, r, size) });
  let pos = 0;
  const cut = new TransformStream({
    transform(chunk, controller) {
      const from = pos;
      pos += chunk.byteLength;
      if (pos > start) controller.enqueue(chunk.subarray(Math.max(start - from, 0), Math.min(end + 1 - from, chunk.byteLength)));
      if (pos > end) controller.terminate();
    },
  });
  // Workers' FixedLengthStream makes the runtime send the Content-Length instead of chunking
  const piped = res.body.pipeThrough(cut);
  const body = typeof FixedLengthStream === 'function' ? piped.pipeThrough(new FixedLengthStream(end - start + 1)) : piped;
  return new Response(body, { status: 206, headers: piece(out, r, size) });
}

export default { fetch: handle };
