// A storyboard of one recording: chosen frames in a grid, each cut to the part that matters and its time under it,
// rendered to a PNG for review_shot.js to put its heading and "Check: ..." on.
// --times are seconds into the recording. --top, --left and --tall cut each frame (in the recording's CSS pixels,
// from the clip's top left), --zoom enlarges it, --cols sets the grid (two columns by default, the whole 1176 wide)
import { readFileSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { args, launch } from './chrome.mjs';

const USAGE = `node packaging/motion/storyboard.mjs --raw <recording folder> --out <storyboard.png> --times 0.5,1,1.5,...
  [--top 40] [--left 50] [--tall 115] [--zoom 1.7] [--cols 2]`;
const o = args({ raw: '', out: '', times: '', top: 40, left: 50, tall: 0, zoom: 1.7, cols: 2 }, USAGE);
if (!o.raw || !o.out || !o.times) { console.error(USAGE); process.exit(2); }
const Z = o.zoom, top = o.top, left = o.left, tall = o.tall || (top < 40 ? 140 : 115);
const meta = JSON.parse(readFileSync(`${o.raw}/meta.json`, 'utf8'));
const GAP = 12, WIDE = 1176, cell = Math.floor((WIDE - GAP * (o.cols - 1)) / o.cols);
const cells = o.times.split(',').map(Number).map((t) => {
  const n = Math.min(meta.frames - 1, Math.round(t * meta.fps));
  const png = readFileSync(`${o.raw}/f${String(n).padStart(4, '0')}.png`).toString('base64');
  return `<figure><div class="cut"><img src="data:image/png;base64,${png}"></div><figcaption>${t.toFixed(2)} s</figcaption></figure>`;
}).join('');
const dark = meta.scheme === 'dark';
const html = `<!doctype html><meta charset="utf-8"><style>
  body { margin: 0; background: ${dark ? '#24201b' : '#e9e4da'}; font: 600 15px/1.2 -apple-system, sans-serif; color: ${dark ? '#d9d2c5' : '#4a443b'}; }
  main { display: grid; grid-template-columns: repeat(${o.cols}, ${cell}px); gap: ${GAP}px; padding: 12px; width: ${WIDE}px; }
  .cut { width: ${cell}px; height: ${Math.round(tall * Z)}px; overflow: hidden; border-radius: 4px; }
  .cut img { display: block; width: ${meta.clip.width * Z}px; margin: -${top * Z}px 0 0 -${left * Z}px; }
  figure { margin: 0; } figcaption { padding: 5px 2px 0; }
</style><main>${cells}</main>`;
const dir = mkdtempSync(join(tmpdir(), 'idiograph-board-'));
const browser = await launch();
try {
  writeFileSync(join(dir, 'board.html'), html);
  const page = await browser.newPage({ width: WIDE + 24, height: 400, scheme: dark ? 'dark' : 'light' });
  await page.goto(pathToFileURL(join(dir, 'board.html')).href);
  const r = await page.evaluate(() => { const b = document.querySelector('main').getBoundingClientRect(); return { x: b.x, y: b.y, width: b.width, height: b.height }; });
  await page.resize(Math.ceil(r.y + r.height));
  await page.shot(o.out, r);
  console.log(o.out, `${Math.round(r.width)}x${Math.round(r.height)}`);
} finally { await browser.close(); rmSync(dir, { recursive: true, force: true }); }
