// What the motion tools share: headless Chrome driven over the DevTools protocol with node's own WebSocket (node 22
// or later), nothing installed, and Home's mark made ready to play on a virtual clock. From the markplay rounds of
// 23 October 2026, moved into the repo on 26 October (motiontools).
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

export const CHROME = process.env.IDIOGRAPH_CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

// --name value and --flag from the command line, with defaults. A value that is a number in the defaults is read as one
export function args(defaults, usage) {
  const out = { ...defaults }, argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '-h' || a === '--help') { console.log(usage); process.exit(0); }
    if (!a.startsWith('--')) { console.error(`not an option: ${a}\n${usage}`); process.exit(2); }
    const key = a.slice(2);
    if (!(key in defaults)) { console.error(`unknown option --${key}\n${usage}`); process.exit(2); }
    if (typeof defaults[key] === 'boolean') { out[key] = true; continue; }
    const v = argv[++i];
    if (v === undefined) { console.error(`--${key} needs a value\n${usage}`); process.exit(2); }
    out[key] = typeof defaults[key] === 'number' ? Number(v) : v;
  }
  return out;
}

// the server's address from --url or --port. Port 8765 is the one a person's own Idiograph runs on, never recorded
export function serverUrl(o) {
  const url = o.url || `http://127.0.0.1:${o.port}/`;
  if (new URL(url).port === '8765') { console.error('port 8765 is the running app\'s own: start a smoke server on another port'); process.exit(2); }
  return url;
}

export async function launch() {
  if (!existsSync(CHROME)) throw new Error(`no Chrome at ${CHROME} (set IDIOGRAPH_CHROME)`);
  const profile = mkdtempSync(join(tmpdir(), 'idiograph-motion-'));
  const proc = spawn(CHROME, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`, '--no-first-run',
    '--no-default-browser-check', '--hide-scrollbars', '--mute-audio', '--disable-extensions', 'about:blank'], { stdio: ['ignore', 'ignore', 'pipe'] });
  const wsUrl = await new Promise((ok, fail) => {
    let err = '';
    const t = setTimeout(() => fail(new Error('Chrome did not open its DevTools port in 20 s')), 20000);
    proc.stderr.on('data', (d) => { err += d; const m = err.match(/DevTools listening on (ws:\/\/\S+)/); if (m) { clearTimeout(t); ok(m[1]); } });
    proc.on('exit', (c) => { clearTimeout(t); fail(new Error(`Chrome quit (${c}): ${err.slice(-400)}`)); });
  });
  const ws = new WebSocket(wsUrl);
  await new Promise((ok, fail) => { ws.onopen = ok; ws.onerror = () => fail(new Error('no DevTools connection')); });
  let id = 0;
  const waiting = new Map(), listeners = [];
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && waiting.has(msg.id)) {
      const { ok, fail } = waiting.get(msg.id); waiting.delete(msg.id);
      msg.error ? fail(new Error(`${msg.error.message} ${msg.error.data || ''}`)) : ok(msg.result);
    } else if (msg.method) for (const l of listeners) l(msg);
  };
  const send = (method, params = {}, sessionId) => new Promise((ok, fail) => {
    const n = ++id; waiting.set(n, { ok, fail });
    ws.send(JSON.stringify({ id: n, method, params, ...(sessionId ? { sessionId } : {}) }));
  });
  const close = async () => {
    try { await send('Browser.close'); } catch { /* already gone */ }
    try { ws.close(); } catch { /* closed */ }
    await new Promise((ok) => { if (proc.exitCode !== null) ok(); else { proc.on('exit', ok); setTimeout(() => { proc.kill('SIGKILL'); ok(); }, 5000); } });
    rmSync(profile, { recursive: true, force: true });
  };
  // a page of its own size, device scale and colour scheme, motion never reduced
  const newPage = async ({ width, height = 800, scale = 1, scheme = 'light' }) => {
    const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
    const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
    const s = (m, p) => send(m, p, sessionId);
    const errors = [], loads = [];
    listeners.push((msg) => {
      if (msg.sessionId !== sessionId) return;
      if (msg.method === 'Runtime.exceptionThrown') { const d = msg.params.exceptionDetails; errors.push(String(d.exception?.description || d.text)); }
      if (msg.method === 'Page.loadEventFired') loads.splice(0).forEach((f) => f());
    });
    await s('Page.enable'); await s('Runtime.enable');
    const size = (h) => s('Emulation.setDeviceMetricsOverride', { width, height: h, deviceScaleFactor: scale, mobile: false });
    await size(height);
    await s('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: scheme }, { name: 'prefers-reduced-motion', value: 'no-preference' }] });
    const evaluate = async (fn, arg) => {
      const expression = typeof fn === 'function' ? `(${fn})(${arg === undefined ? '' : JSON.stringify(arg)})` : fn;
      const r = await s('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
      if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
      return r.result.value;
    };
    return {
      errors, evaluate, resize: size,
      // the page's own DevTools calls and its events, for a tool that drives the page (clip.mjs)
      cdp: s,
      on: (method, fn) => listeners.push((msg) => { if (msg.sessionId === sessionId && msg.method === method) fn(msg.params); }),
      initScript: (source) => s('Page.addScriptToEvaluateOnNewDocument', { source }),
      goto: async (url) => { const loaded = new Promise((ok) => loads.push(ok)); await s('Page.navigate', { url }); await loaded; },
      wait: (ms) => new Promise((ok) => setTimeout(ok, ms)),
      waitVisible: async (sel, ms = 20000) => {
        const end = Date.now() + ms;
        while (Date.now() < end) {
          if (await evaluate((q) => { const e = document.querySelector(q); if (!e) return false; const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; }, sel)) return;
          await new Promise((ok) => setTimeout(ok, 100));
        }
        throw new Error(`${sel} never showed`);
      },
      style: (css) => evaluate((c) => { const st = document.createElement('style'); st.textContent = c; document.head.appendChild(st); }, css),
      shot: async (path, clip) => {
        const r = await s('Page.captureScreenshot', { format: 'png', ...(clip ? { clip: { ...clip, scale: 1 } } : {}) });
        writeFileSync(path, Buffer.from(r.data, 'base64'));
      },
    };
  };
  return { newPage, close };
}

// The page's own requestAnimationFrame held: each __advance(ms) moves a virtual clock on and runs what was queued,
// so a recording takes as long as it needs and every frame is exactly 1/fps apart. The session's mark flag is set so
// Home does not play a way of its own on load
export const CLOCK = `(() => {
  sessionStorage.setItem('idiograph.homeMark', '1');
  let vt = 0, queue = [];
  window.requestAnimationFrame = (cb) => { queue.push(cb); return queue.length; };
  window.__advance = (ms) => { vt += ms; const q = queue; queue = []; for (const cb of q) cb(vt); return queue.length; };
})();`;

// the page's 5 s safety (style.css, home-mark-safe) runs on the wall clock, which a frame by frame recording outruns
export const NO_SAFETY = 'html.home-mark-due .wordmark .pe .lockup > use, html.home-mark-due .wordmark .pe .lockup > path, html.home-mark-due .wordmark .pe .pe-stamp { animation: none !important; }';

// Home open at a width with the mark at rest and the clock held, ready for homeMarkPlay(way)
export async function openHome(browser, url, { width, height = 800, scale = 1, scheme = 'light', clock = true }) {
  const page = await browser.newPage({ width, height, scale, scheme });
  await page.initScript(clock ? CLOCK : "sessionStorage.setItem('idiograph.homeMark', '1');");
  await page.goto(url);
  await page.waitVisible('.wordmark .pe .lockup');
  await page.wait(1200);
  return page;
}

// IDIOGRAPH's ink in the lockup's units: for each x (step 0.05) the topmost and lowest y inside the name's stroke,
// or null over a gap. Run in the page. The bounce solver and the frame checker read it
export function inkProfile() {
  const lock = document.querySelector('.wordmark .pe .lockup'), name = lock.querySelector(':scope > path');
  const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  p.setAttribute('d', name.getAttribute('d')); p.setAttribute('stroke-width', '1.3'); p.setAttribute('stroke', 'black');
  p.setAttribute('stroke-linecap', 'square'); p.setAttribute('stroke-linejoin', 'miter'); p.setAttribute('fill', 'none');
  lock.appendChild(p);
  const out = [];
  for (let x = 18; x <= 108.5; x += 0.05) {
    let top = null, bot = null;
    for (let y = 1.5; y <= 14; y += 0.025) {
      const pt = lock.createSVGPoint(); pt.x = x - 19.2; pt.y = y - 12.5;
      if (p.isPointInStroke(pt)) { if (top === null) top = y; bot = y; }
    }
    out.push([+x.toFixed(2), top === null ? null : +top.toFixed(3), bot === null ? null : +bot.toFixed(3)]);
  }
  p.remove();
  return out;
}
