// SPDX-License-Identifier: AGPL-3.0-or-later
// The lockup for the updates emails (updates-email, 23 November 2026): Idiograph's mark, IDIOGRAPH in the
// app's square-stroke capitals and the tilted PREVIEW EDITION stamp, drawn from the site's own SVG and CSS
// (site/holding/index.html and style.css) by headless Chrome and saved as two PNGs at twice their size, since
// email clients show no SVG:
//
//   site/holding/email/idiograph-lockup-2x.png       ink and stamp on a solid rectangle of the paper's colour
//                                                    that holds the whole lockup and its clear space, so the
//                                                    mark itself is never altered and, where a client
//                                                    darkens the email but not its images (Gmail's apps),
//                                                    the lockup shows as a paper-coloured plate, not
//                                                    outlined
//   site/holding/email/idiograph-lockup-dark-2x.png  the dark theme's ink and stamp, which the email shows in
//                                                    place of the first where the client follows
//                                                    prefers-color-scheme (Apple Mail, Outlook)
//
//   node packaging/email_lockup.mjs            writes both, and prints each one's size in CSS pixels
//
// The email shows each at LOCKUP_WIDTH and LOCKUP_HEIGHT (updates-worker/worker.js and packaging/updates_mail.py),
// so a change of size here is made there too. The lockup's clear space, its mark's height above and to its left,
// is inside both images (transparent in the dark one), and the email's own padding is reduced by as much.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { launch } from './motion/chrome.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const site = path.join(root, 'site', 'holding');
const out = path.join(site, 'email');
const index = readFileSync(path.join(site, 'index.html'), 'utf8');
const symbol = index.match(/<symbol id="idiograph"[\s\S]*?<\/symbol>/)[0];
const lockup = index.match(/<svg class="lockup"[\s\S]*?<\/svg>/)[0];

const LW = 220; // the lockup's width in CSS pixels, its stamp at the site home's size rule (style.css .pe-stamp)
const THEMES = {
  light: { file: 'idiograph-lockup-2x.png', ink: '#1F1B16', crux: '#B04E00', dot: '#F26B1D', plate: '#FBF7EF' },
  dark: { file: 'idiograph-lockup-dark-2x.png', ink: '#EFE7D9', crux: '#F79646', dot: '#F26B1D', plate: null },
};

const html = (t) => `<!doctype html><html><head><meta charset="utf-8"><style>
html, body { margin: 0; background: ${t.plate || 'transparent'}; }
:root { --lw: ${LW}px; --m: calc(var(--lw) * 15 / 107.33); --mark-dot: ${t.dot};
  --sans: "Avenir Next", "Avenir", "Gill Sans", "Segoe UI", system-ui, sans-serif; }
.symbols { position: absolute; width: 0; height: 0; }
.wrap { position: absolute; left: 48px; top: 48px; color: ${t.ink}; }
.lockup { display: block; width: var(--lw); height: var(--m); overflow: visible; }
.pe { position: relative; display: block; width: fit-content; padding: 0 calc(var(--m) * 12 / 32) calc(var(--m) * 30 / 32); }
.pe-stamp { position: absolute; top: calc(100% - var(--m) * 30 / 32 + var(--m) * 50 / 180);
  right: calc(var(--m) * 12 / 32 - var(--m) * 46 / 180);
  font: 600 max(9.5px, var(--m) * 46 / 180)/1 var(--sans); letter-spacing: .16em; text-transform: uppercase; white-space: nowrap;
  color: ${t.crux}; border: max(1px, .109em) solid ${t.crux}; border-radius: .304em; padding: .413em .652em .37em .761em; rotate: -4deg; }
</style></head><body>
<svg class="symbols" aria-hidden="true">${symbol}</svg>
<div class="wrap"><span class="pe">${lockup}<span class="pe-stamp">Preview Edition</span></span></div>
</body></html>`;

const browser = await launch();
try {
  mkdirSync(out, { recursive: true });
  for (const [name, t] of Object.entries(THEMES)) {
    const page = await browser.newPage({ width: 420, height: 200, scale: 2, scheme: name });
    if (!t.plate) await page.cdp('Emulation.setDefaultBackgroundColorOverride', { color: { r: 0, g: 0, b: 0, a: 0 } });
    await page.goto(`data:text/html;base64,${Buffer.from(html(t)).toString('base64')}`);
    await page.wait(300);
    // the lockup and the stamp's turned box together, with the mark's height of clear space above and to the left
    // and two pixels right and below
    const box = await page.evaluate(() => {
      const a = document.querySelector('.lockup').getBoundingClientRect();
      const b = document.querySelector('.pe-stamp').getBoundingClientRect();
      const clear = Math.ceil(a.height);
      const left = Math.floor(Math.min(a.left, b.left)) - clear;
      const top = Math.floor(Math.min(a.top, b.top)) - clear;
      return { x: left, y: top, width: Math.ceil(Math.max(a.right, b.right)) + 2 - left, height: Math.ceil(Math.max(a.bottom, b.bottom)) + 2 - top };
    });
    const r = await page.cdp('Page.captureScreenshot', { format: 'png', clip: { ...box, scale: 1 } });
    writeFileSync(path.join(out, t.file), Buffer.from(r.data, 'base64'));
    console.log(`${t.file}: ${box.width} x ${box.height} CSS pixels`);
  }
} finally {
  await browser.close();
}
