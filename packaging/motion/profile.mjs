// IDIOGRAPH's ink profile in the lockup's units, for the bounce solver: a list of [x, top, bottom] every 0.05 units,
// top and bottom null over a gap. The same profile frames.mjs writes into its frames
import { writeFileSync } from 'node:fs';
import { args, serverUrl, launch, openHome, inkProfile } from './chrome.mjs';

const USAGE = 'node packaging/motion/profile.mjs --out <profile.json> [--port 8770 | --url http://127.0.0.1:8770/]';
const o = args({ out: '', port: 8770, url: '' }, USAGE);
if (!o.out) { console.error(USAGE); process.exit(2); }
const browser = await launch();
try {
  const page = await openHome(browser, serverUrl(o), { width: 1280, clock: false });
  const p = await page.evaluate(inkProfile);
  writeFileSync(o.out, JSON.stringify(p));
  console.log(o.out, p.length, 'columns,', p.filter((c) => c[1] !== null).length, 'with ink');
} finally { await browser.close(); }
