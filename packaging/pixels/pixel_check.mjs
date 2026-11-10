// The pixel check (i18ncore, 28 October 2026): a change that should change nothing on screen, words moved into the
// catalogue above all, proved by shooting the same screens from the app before and after and comparing them exactly.
// Headless Chrome over the DevTools protocol (packaging/motion/chrome.mjs), nothing installed.
//
//   node packaging/pixels/pixel_check.mjs shoot --port 8851 --out <dir>/before [--group shell] [--width 1280]
//        [--height 800] [--scale 1] [--schemes light,dark] [--sift <screening folder>] [--trace <Trace project folder>]
//   node packaging/pixels/pixel_check.mjs compare <dir>/before <dir>/after [--diff <dir>/diff]
//
// The groups `sift` and `trace` shoot Sift's and Trace's own apps, on a server of that app, a review or a Trace
// project of invented records named by --sift or --trace (tracestyle, 30 October 2026), which the page reads as
// SWEEP, as the zoom sweep's groups do.
//
// `shoot` writes <screen>-<width>-<scheme>.png for each screen of the group (screens.mjs) and each scheme, with every
// animation, transition and caret stilled and Home's mark not played, so two runs of one app come out the same.
// `compare` decodes each pair and counts the pixels that differ, writes a picture of them (the after shot with each
// differing pixel in magenta) where it is asked to, and ends on one line, `PIXELS: SAME 14/14` or
// `PIXELS: DIFFER 2/14`, exit 0 or 1. A shot in one folder alone counts as differing.
import { readFileSync, writeFileSync, mkdirSync, readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { inflateSync, deflateSync, crc32 } from 'node:zlib';
import { args, serverUrl, launch } from '../motion/chrome.mjs';
import { SCREENS, MASKS } from './screens.mjs';

const STILL = `*, *::before, *::after { animation: none !important; transition: none !important; caret-color: transparent !important; }
${MASKS.join(', ')} { color: transparent !important; }`;

// ── shooting
// Home's answer from the server taken and drawn (the shell's `S.lib`, set as loadLibrary draws Home), so a screen that
// starts from Home's cards, or reads S.lib as the boards group does, never runs before them: Home shows before its
// answer comes, and a slow answer on a loaded machine would leave a screen an empty Home (loose31, 31 October 2026)
async function homeAnswered(page, ms = 20000) {
  const end = Date.now() + ms;
  while (Date.now() < end) {
    if (await page.evaluate("typeof S !== 'undefined' && !!S && !!S.lib")) return;
    await page.wait(100);
  }
  throw new Error(`Home had no answer from the server in ${ms / 1000} s`);
}

async function shoot(o) {
  const group = SCREENS[o.group];
  if (!group) { console.error(`no group ${o.group}: ${Object.keys(SCREENS).join(', ')}`); process.exit(2); }
  const url = serverUrl(o);
  mkdirSync(o.out, { recursive: true });
  const browser = await launch();
  const written = [];
  try {
    for (const scheme of o.schemes.split(',')) {
      for (const screen of group) {
        const page = await browser.newPage({ width: o.width, height: o.height, scale: o.scale, scheme });
        await page.initScript("try { sessionStorage.setItem('idiograph.homeMark', '1'); } catch (e) {}"
          + `window.SWEEP = ${JSON.stringify({ sift: o.sift, trace: o.trace })};`);
        await page.goto(url);
        await page.waitVisible('#library');
        await homeAnswered(page);
        await page.style(STILL);
        await page.wait(1200);
        await page.evaluate(`(${screen.open})()`);
        if (screen.wait) await page.waitVisible(screen.wait);
        await page.evaluate('document.fonts.ready.then(() => true)');
        await page.wait(600);
        const name = (part) => join(o.out, `${part}-${o.width}-${scheme}.png`);
        if (!screen.panes) {
          await page.shot(name(screen.name));
          written.push(name(screen.name));
        } else {
          const panes = await page.evaluate(() => [...document.querySelectorAll('#settings-nav [role="tab"]')]
            .filter((t) => t.offsetParent !== null).map((t) => t.dataset.pane));
          for (const pane of panes) {
            const scrolls = await page.evaluate((p) => {
              document.querySelector(`#settings-nav [data-pane="${p}"]`).click();
              const box = document.getElementById('settings-panes');
              box.scrollTop = 0;
              return box.scrollHeight > box.clientHeight + 1;
            }, pane);
            await page.wait(400);
            await page.shot(name(`${screen.name}-${pane}`));
            written.push(name(`${screen.name}-${pane}`));
            if (scrolls) {
              await page.evaluate(() => { const box = document.getElementById('settings-panes'); box.scrollTop = box.scrollHeight; });
              await page.wait(400);
              await page.shot(name(`${screen.name}-${pane}-end`));
              written.push(name(`${screen.name}-${pane}-end`));
            }
          }
        }
        if (page.errors.length) console.log(`${screen.name} ${scheme}: page errors: ${page.errors.join(' | ')}`);
      }
    }
  } finally { await browser.close(); }
  console.log(`${written.length} shots in ${o.out}`);
}

// ── a PNG read and written, 8 bits a channel, not interlaced: what Chrome writes
function readPng(path) {
  const buf = readFileSync(path);
  let at = 8, width = 0, height = 0, type = 0, depth = 0;
  const data = [];
  while (at < buf.length) {
    const len = buf.readUInt32BE(at), kind = buf.toString('latin1', at + 4, at + 8), body = buf.subarray(at + 8, at + 8 + len);
    if (kind === 'IHDR') { width = body.readUInt32BE(0); height = body.readUInt32BE(4); depth = body[8]; type = body[9]; if (body[12]) throw new Error(`${path} is interlaced`); }
    else if (kind === 'IDAT') data.push(body);
    else if (kind === 'IEND') break;
    at += 12 + len;
  }
  const ch = { 2: 3, 6: 4, 0: 1, 4: 2 }[type];
  if (depth !== 8 || !ch) throw new Error(`${path}: colour type ${type}, depth ${depth} not read`);
  const raw = inflateSync(Buffer.concat(data)), stride = width * ch, out = Buffer.alloc(width * height * 4);
  let prev = Buffer.alloc(stride);
  for (let y = 0; y < height; y++) {
    const f = raw[y * (stride + 1)], line = Buffer.from(raw.subarray(y * (stride + 1) + 1, (y + 1) * (stride + 1)));
    for (let i = 0; i < stride; i++) {
      const a = i >= ch ? line[i - ch] : 0, b = prev[i], c = i >= ch ? prev[i - ch] : 0;
      const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
      line[i] = (line[i] + [0, a, b, (a + b) >> 1, pa <= pb && pa <= pc ? a : pb <= pc ? b : c][f]) & 255;
    }
    for (let x = 0; x < width; x++) {
      const s = x * ch, d = (y * width + x) * 4;
      if (ch >= 3) { out[d] = line[s]; out[d + 1] = line[s + 1]; out[d + 2] = line[s + 2]; out[d + 3] = ch === 4 ? line[s + 3] : 255; }
      else { out[d] = out[d + 1] = out[d + 2] = line[s]; out[d + 3] = ch === 2 ? line[s + 1] : 255; }
    }
    prev = line;
  }
  return { width, height, rgba: out };
}

function writePng(path, { width, height, rgba }) {
  const chunk = (kind, body) => {
    const len = Buffer.alloc(4); len.writeUInt32BE(body.length);
    const head = Buffer.from(kind, 'latin1'), crc = Buffer.alloc(4);
    crc.writeUInt32BE(crc32(Buffer.concat([head, body])) >>> 0);
    return Buffer.concat([len, head, body, crc]);
  };
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0); ihdr.writeUInt32BE(height, 4); ihdr[8] = 8; ihdr[9] = 6;
  const raw = Buffer.alloc(height * (width * 4 + 1));
  for (let y = 0; y < height; y++) rgba.copy(raw, y * (width * 4 + 1) + 1, y * width * 4, (y + 1) * width * 4);
  writeFileSync(path, Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr),
    chunk('IDAT', deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]));
}

// ── comparing
function compare(before, after, diffDir) {
  const names = [...new Set([...readdirSync(before), ...readdirSync(after)])].filter((n) => n.endsWith('.png')).sort();
  let differ = 0;
  if (diffDir) mkdirSync(diffDir, { recursive: true });
  for (const n of names) {
    const a = join(before, n), b = join(after, n);
    if (!existsSync(a) || !existsSync(b)) { differ++; console.log(`${n}: only in ${existsSync(a) ? 'before' : 'after'}`); continue; }
    if (readFileSync(a).equals(readFileSync(b))) { console.log(`${n}: same`); continue; }
    const pa = readPng(a), pb = readPng(b);
    if (pa.width !== pb.width || pa.height !== pb.height) { differ++; console.log(`${n}: ${pa.width}x${pa.height} before, ${pb.width}x${pb.height} after`); continue; }
    let count = 0, x0 = Infinity, y0 = Infinity, x1 = -1, y1 = -1;
    const mark = Buffer.from(pb.rgba);
    for (let i = 0; i < pa.rgba.length; i += 4) {
      if (pa.rgba.readUInt32BE(i) === pb.rgba.readUInt32BE(i)) continue;
      count++;
      const p = i / 4, x = p % pa.width, y = Math.floor(p / pa.width);
      x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y);
      mark[i] = 255; mark[i + 1] = 0; mark[i + 2] = 255; mark[i + 3] = 255;
    }
    if (!count) { console.log(`${n}: same (encoded differently)`); continue; }
    differ++;
    console.log(`${n}: ${count} pixels differ, in ${x1 - x0 + 1}x${y1 - y0 + 1} at ${x0},${y0}`);
    if (diffDir) writePng(join(diffDir, n), { width: pb.width, height: pb.height, rgba: mark });
  }
  console.log(`PIXELS: ${differ ? 'DIFFER' : 'SAME'} ${differ ? differ : names.length}/${names.length}`);
  process.exit(differ || !names.length ? 1 : 0);
}

const USAGE = `node packaging/pixels/pixel_check.mjs shoot --port <port> --out <dir> [--group shell] [--width 1280] [--height 800] [--scale 1] [--schemes light,dark]
     [--sift <screening folder>] [--trace <Trace project folder>]
node packaging/pixels/pixel_check.mjs compare <before> <after> [--diff <dir>]`;
const verb = process.argv[2];
if (verb === 'shoot') {
  process.argv.splice(2, 1);
  const o = args({ port: 0, url: '', out: '', group: 'shell', width: 1280, height: 800, scale: 1, schemes: 'light,dark', sift: '', trace: '' }, USAGE);
  if (!o.out || (!o.port && !o.url)) { console.error(USAGE); process.exit(2); }
  await shoot(o);
} else if (verb === 'compare' && process.argv[3] && process.argv[4]) {
  const at = process.argv.indexOf('--diff');
  compare(process.argv[3], process.argv[4], at > 0 ? process.argv[at + 1] : '');
} else { console.error(USAGE); process.exit(2); }
