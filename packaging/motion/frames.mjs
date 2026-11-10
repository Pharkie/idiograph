// Plays one way frame by frame on the virtual clock and writes, for each frame, the matrices (in the lockup's units)
// of the two brackets' paths, the dot and each letter, with the page's scroll width, and once the toolbar's icons, the
// notice, the window's edges and IDIOGRAPH's ink profile. check.py reads it. The scene ways only (all but the spin,
// whose pieces are CSS 3D blocks, not the scene's SVG)
import { writeFileSync } from 'node:fs';
import { args, serverUrl, launch, openHome, NO_SAFETY, inkProfile } from './chrome.mjs';

const USAGE = `node packaging/motion/frames.mjs --way <pong|pinball|anagram|football|kiss|race> --out <frames.json>
  [--width 1280] [--height 800] [--fps 60] [--seconds 6.5] [--port 8770 | --url http://127.0.0.1:8770/]`;
const o = args({ way: '', out: '', width: 1280, height: 800, fps: 60, seconds: 6.5, port: 8770, url: '' }, USAGE);
if (!o.way || !o.out) { console.error(USAGE); process.exit(2); }
if (o.way === 'spin') { console.error('the spin has no scene SVG to read: check it by its recording and storyboard'); process.exit(2); }
const FPS = o.fps;

const browser = await launch();
try {
  const page = await openHome(browser, serverUrl(o), { width: o.width, height: o.height });
  await page.style(NO_SAFETY);
  const profile = await page.evaluate(inkProfile);
  const info = await page.evaluate(() => {
    const lock = document.querySelector('.wordmark .pe .lockup'), at = lock.getBoundingClientRect(), u = at.width / 107.33;
    const bars = [...document.querySelectorAll('.lib-tools .bar-tool > *')].map((el) => el.getBoundingClientRect()).filter((r) => r.width)
      .map((r) => [(r.left - at.left) / u, (r.top - at.top) / u, (r.right - at.left) / u, (r.bottom - at.top) / u]);
    const note = document.querySelector('.pe-note').getBoundingClientRect();
    return { u, winR: (innerWidth - at.left) / u, winT: -at.top / u, winB: (innerHeight - at.top) / u, winL: -at.left / u, bars,
      note: [(note.left - at.left) / u, (note.top - at.top) / u, (note.right - at.left) / u, (note.bottom - at.top) / u] };
  });
  await page.evaluate((w) => homeMarkPlay(w), o.way);
  await page.evaluate(() => window.__advance(0));
  const frames = [];
  for (let i = 0; i < FPS * o.seconds; i++) {
    await page.evaluate((ms) => window.__advance(ms), 1000 / FPS);
    const f = await page.evaluate(() => {
      const svg = document.querySelector('.wordmark svg.home-mark');
      if (!svg) return null;
      const M0 = svg.getScreenCTM().inverse();
      const mx = (el) => { const m = M0.multiply(el.getScreenCTM()); return [m.a, m.b, m.c, m.d, m.e, m.f, Number(el.getAttribute('opacity') ?? el.parentElement.getAttribute('opacity') ?? 1)]; };
      const kids = [...svg.children], dot = kids[kids.length - 1], rb = kids[kids.length - 2], lb = kids[kids.length - 3];
      const letters = kids.length > 4 ? [...kids[0].children].map(mx) : [];
      return { lb: mx(lb.firstElementChild).slice(0, 6).concat(Number(lb.getAttribute('opacity'))), rb: mx(rb.firstElementChild).slice(0, 6).concat(Number(rb.getAttribute('opacity'))),
        dot: mx(dot), letters, sw: document.documentElement.scrollWidth, iw: innerWidth };
    });
    if (!f) break;
    frames.push({ t: (i + 1) / FPS, ...f });
  }
  writeFileSync(o.out, JSON.stringify({ way: o.way, width: o.width, info, profile, frames, errors: page.errors }));
  console.log(o.way, o.width, frames.length, 'frames', page.errors.length ? 'errors: ' + page.errors.join(' | ') : 'no page errors');
} finally { await browser.close(); }
