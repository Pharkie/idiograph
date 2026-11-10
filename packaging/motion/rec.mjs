// Records Home's mark coming in one way, frame by frame on a virtual clock: each frame the clock moves on 1/fps and the
// frame is captured at device scale 2, until the way has ended and the lockup has rested for --settle seconds.
// Writes f0000.png on and meta.json (the way, width, scheme, frames, fps, clip, the lockup's box, page errors).
// --probe shoots the resting frame alone as probe.png and prints the clip, to check the framing first
import { mkdirSync, writeFileSync } from 'node:fs';
import { args, serverUrl, launch, openHome, NO_SAFETY } from './chrome.mjs';

const USAGE = `node packaging/motion/rec.mjs --way <spin|pong|pinball|anagram|football|kiss|race> --out <folder>
  [--width 1280] [--height 800] [--scheme light|dark] [--fps 60] [--seconds 7] [--settle 0.5]
  [--port 8770 | --url http://127.0.0.1:8770/] [--clip x,y,w,h] [--probe]`;
const o = args({ way: '', out: '', width: 1280, height: 800, scheme: 'light', fps: 60, seconds: 7, settle: 0.5, port: 8770, url: '', clip: '', probe: false }, USAGE);
if (!o.way || !o.out) { console.error(USAGE); process.exit(2); }
const W = o.width, FPS = o.fps;

const browser = await launch();
try {
  const page = await openHome(browser, serverUrl(o), { width: W, height: o.height, scale: 2, scheme: o.scheme });
  const box = await page.evaluate(() => {
    const r = document.querySelector('.wordmark .pe').getBoundingClientRect();
    return { x: r.x, y: r.y, w: r.width, h: r.height, edition: document.documentElement.dataset.edition };
  });
  // the frame: what each way uses round the lockup. At a narrow width the whole width, the race to the window's right
  // edge it runs in from, the spin from the window's corner it circles in, the others past the lockup's end
  const top = Math.max(0, Math.floor(box.y - 70)), tall = Math.ceil(Math.min(box.y, 70) + box.h + 30);
  const clip = o.clip ? Object.fromEntries(o.clip.split(',').map(Number).map((v, i) => [['x', 'y', 'width', 'height'][i], v]))
    : W < 600 ? { x: 0, y: top, width: W, height: tall }
    : o.way === 'race' ? { x: Math.floor(box.x - 90), y: top, width: W - Math.floor(box.x - 90), height: tall }
    : o.way === 'spin' ? { x: 0, y: 0, width: Math.ceil(box.x + box.w + 140), height: Math.ceil(box.y + box.h + 34) }
    : { x: Math.floor(box.x - 90), y: top, width: Math.ceil(box.w + (o.way === 'anagram' ? 340 : 180)), height: tall };
  mkdirSync(o.out, { recursive: true });
  if (o.probe) {
    await page.shot(`${o.out}/probe.png`, clip);
    console.log(JSON.stringify({ box, clip, errors: page.errors }));
  } else {
    await page.style(NO_SAFETY);
    await page.evaluate((w) => homeMarkPlay(w), o.way);
    let n = 0, idle = 0;
    const shoot = async () => { await page.shot(`${o.out}/f${String(n++).padStart(4, '0')}.png`, clip); };
    await page.evaluate(() => window.__advance(0));
    await shoot();
    for (let i = 0; i < FPS * o.seconds; i++) {
      await page.evaluate((ms) => window.__advance(ms), 1000 / FPS);
      await shoot();
      const busy = await page.evaluate(() => !!document.querySelector('.wordmark .home-mark') || document.documentElement.classList.contains('home-mark-due'));
      if (!busy && ++idle > FPS * o.settle) break;
    }
    writeFileSync(`${o.out}/meta.json`, JSON.stringify({ way: o.way, width: W, scheme: o.scheme, frames: n, fps: FPS, clip, box, errors: page.errors }));
    console.log(o.way, W, o.scheme, n, 'frames', (n / FPS).toFixed(2), 's', page.errors.length ? 'errors: ' + page.errors.join(' | ') : 'no page errors');
  }
} finally { await browser.close(); }
