// SPDX-License-Identifier: AGPL-3.0-or-later
/* The site Worker's Range answers, in node alone, for the suite's area 405 and for trying by hand:

     node site/holding/test-worker.mjs

   The assets are a stand-in that always sends a file whole with a 200 and an ETag, as Cloudflare's do, and
   answers 304 to a matching If-None-Match. It prints one JSON list of [name, passed, detail] and exits 0. */

import { pathToFileURL } from 'node:url';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const { handle, parseRange } = await import(pathToFileURL(path.join(here, 'worker.js')).href);

const bytes = new Uint8Array(1000).map((_, i) => i % 251);
// a body that comes in small chunks and counts how many have been pulled and whether it was cancelled
let pulled = 0, cancelled = false;
const chunked = (size, step) => new ReadableStream({
  pos: 0,
  pull(c) {
    if (this.pos >= size) return c.close();
    const n = Math.min(step, size - this.pos);
    c.enqueue(bytes.slice(this.pos, this.pos + n));
    this.pos += n;
    pulled++;
  },
  cancel() { cancelled = true; },
});
let whole = 0, asked = 0;
const env = {
  ASSETS: {
    async fetch(req) {
      const u = new URL(req.url).pathname;
      if (u === '/clips/chunks.mp4') {
        pulled = 0; cancelled = false;
        return new Response(chunked(1000, 7), { status: 200, headers: { 'content-type': 'video/mp4', etag: '"abc"', 'content-length': '1000' } });
      }
      if (u === '/clips/nosize.mp4' || u === '/clips/noetag.mp4') {
        asked++;
        const res = new Response(bytes, { status: 200, headers: u.includes('noetag') ? { 'content-type': 'video/mp4' } : { 'content-type': 'video/mp4', etag: '"nosize"' } });
        const was = res.arrayBuffer.bind(res);
        res.arrayBuffer = () => { whole++; return was(); };
        return res;
      }
      const h = { 'content-type': 'video/mp4', etag: '"abc"', 'cache-control': 'public, max-age=0, must-revalidate' };
      if (req.headers.get('range')) throw new Error('the Worker must not pass the Range line to the assets');
      if (req.headers.get('if-none-match') === '"abc"') return new Response(null, { status: 304, headers: h });
      return new Response(req.method === 'HEAD' ? null : bytes, { status: 200, headers: { ...h, 'content-length': '1000' } });
    },
  },
};
const out = [];
const check = (name, ok, detail = '') => out.push([name, !!ok, ok ? '' : String(detail).slice(0, 300)]);
const get = (headers = {}, method = 'GET') => handle(new Request('https://idiograph.app/clips/a.mp4', { method, headers }), env);
const same = (buf, a, b) => { const x = new Uint8Array(buf); return x.length === b - a + 1 && x.every((v, i) => v === bytes[a + i]); };

let r = await get();
check('no Range: the whole file, 200, and it says it takes ranges', r.status === 200 && r.headers.get('accept-ranges') === 'bytes' && (await r.arrayBuffer()).byteLength === 1000);
r = await get({ range: 'bytes=0-1' });
check('bytes=0-1: 206, two bytes, Content-Range 0-1/1000', r.status === 206 && r.headers.get('content-range') === 'bytes 0-1/1000' && r.headers.get('content-length') === '2' && same(await r.arrayBuffer(), 0, 1), r.status);
r = await get({ range: 'bytes=900-' });
check('an open range bytes=900-: 206, the last 100 bytes', r.status === 206 && r.headers.get('content-range') === 'bytes 900-999/1000' && same(await r.arrayBuffer(), 900, 999));
r = await get({ range: 'bytes=-100' });
check('a suffix range bytes=-100: 206, the last 100 bytes', r.status === 206 && r.headers.get('content-range') === 'bytes 900-999/1000' && same(await r.arrayBuffer(), 900, 999));
r = await get({ range: 'bytes=-5000' });
check('a suffix longer than the file gives the whole file as a 206', r.status === 206 && r.headers.get('content-range') === 'bytes 0-999/1000');
r = await get({ range: 'bytes=990-5000' });
check('an end past the file is cut to its last byte', r.status === 206 && r.headers.get('content-range') === 'bytes 990-999/1000');
r = await get({ range: 'bytes=1000-' });
check('a start past the end: 416 with Content-Range bytes */1000', r.status === 416 && r.headers.get('content-range') === 'bytes */1000');
r = await get({ range: 'bytes=5000-6000' });
check('a range wholly past the end: 416', r.status === 416);
r = await get({ range: 'bytes=-0' });
check('a suffix of nothing: 416', r.status === 416);
for (const bad of ['bytes=0-1,5-9', 'items=0-1', 'bytes=abc', 'bytes=-', 'bytes=9-3']) {
  r = await get({ range: bad });
  check(`${bad}: ignored, the whole file`, r.status === 200 && (await r.arrayBuffer()).byteLength === 1000, r.status);
}
r = await get({ range: 'bytes=0-1', 'if-range': '"other"' });
check('If-Range that does not match the ETag: the whole file', r.status === 200 && (await r.arrayBuffer()).byteLength === 1000);
r = await get({ range: 'bytes=0-1', 'if-range': '"abc"' });
check('If-Range that matches the ETag: the piece', r.status === 206);
r = await get({ 'if-none-match': '"abc"' });
check('a revalidation still gets its 304 and no body', r.status === 304 && r.headers.get('accept-ranges') === 'bytes' && (await r.arrayBuffer()).byteLength === 0);
r = await get({ range: 'bytes=0-1' }, 'HEAD');
check('HEAD: says it takes ranges, keeps the size, has no body', r.status === 200 && r.headers.get('accept-ranges') === 'bytes' && r.headers.get('content-length') === '1000' && (await r.arrayBuffer()).byteLength === 0);
r = await get({ range: 'bytes=0-1' }, 'GET');
check('the 206 keeps the type, the ETag and the cache line and sets no cookie', r.headers.get('content-type') === 'video/mp4' && r.headers.get('etag') === '"abc"' && r.headers.get('cache-control').includes('must-revalidate') && !r.headers.has('set-cookie'));
const at = (p, headers = {}, method = 'GET') => handle(new Request('https://idiograph.app' + p, { headers, method }), env);
// a body of 143 chunks of 7 bytes: a range's bytes are exact across the chunk edges, and only what it needs is read
for (const [a, b] of [[0, 0], [5, 8], [6, 7], [7, 13], [13, 14], [20, 20], [100, 400], [993, 999], [990, 999], [994, 5000]]) {
  r = await at('/clips/chunks.mp4', { range: `bytes=${a}-${b}` });
  const e = Math.min(b, 999);
  check(`chunks, bytes=${a}-${b}: exact bytes across chunk edges`, r.status === 206 && r.headers.get('content-range') === `bytes ${a}-${e}/1000` && same(await r.arrayBuffer(), a, e), r.status);
}
r = await at('/clips/chunks.mp4', { range: 'bytes=10-20' });
await r.arrayBuffer();
check('a range near the start reads only a few chunks and cancels the rest of the file', pulled <= 6 && cancelled, `pulled ${pulled}, cancelled ${cancelled}`);
r = await at('/clips/chunks.mp4', { range: 'bytes=0-' });
check('bytes=0- sends the whole file as a 206 straight through', r.status === 206 && r.headers.get('content-range') === 'bytes 0-999/1000' && r.headers.get('content-length') === '1000' && same(await r.arrayBuffer(), 0, 999));
r = await at('/clips/chunks.mp4', { range: 'bytes=-10' });
check('a suffix of a chunked body: the last 10 bytes', r.status === 206 && same(await r.arrayBuffer(), 990, 999));
r = await at('/clips/chunks.mp4', { range: 'bytes=5000-' });
check('a 416 on a chunked body cancels it', r.status === 416 && cancelled);
whole = 0;
r = await at('/clips/chunks.mp4', { range: 'bytes=50-60' });
await r.arrayBuffer();
check('no range of a sized file reads it whole', whole === 0);
r = await at('/clips/nosize.mp4', { range: 'bytes=10-19' });
check('no Content-Length but an ETag: the size is counted as a stream, the file is never held, the range exact', r.status === 206 && r.headers.get('content-range') === 'bytes 10-19/1000' && same(await r.arrayBuffer(), 10, 19) && whole === 0, `whole ${whole}`);
asked = 0;
r = await at('/clips/nosize.mp4', { range: 'bytes=-20' });
check('the counted size is remembered: the next range asks the assets once', r.status === 206 && same(await r.arrayBuffer(), 980, 999) && asked === 1 && whole === 0, `asked ${asked}`);
r = await at('/clips/nosize.mp4', {}, 'HEAD');
check('HEAD of a file with no Content-Length gets its size from the count', r.status === 200 && r.headers.get('content-length') === '1000');
whole = 0;
r = await at('/clips/noetag.mp4', { range: 'bytes=10-19' });
check('no Content-Length and no ETag: buffered, the only case, and the range still exact', r.status === 206 && r.headers.get('content-range') === 'bytes 10-19/1000' && same(await r.arrayBuffer(), 10, 19) && whole === 1, `whole ${whole}`);
check('parseRange: bytes=2-4 of 10 is [2,4]', JSON.stringify(parseRange('bytes=2-4', 10)) === '[2,4]');
console.log(JSON.stringify(out));
