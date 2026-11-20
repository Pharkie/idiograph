// What the motion tools share: headless Chrome driven over the DevTools protocol with node's own WebSocket (node 22
// or later), nothing installed, and Home's mark made ready to play on a virtual clock. From the markplay rounds of
// 23 October 2026, moved into the repo on 26 October (motiontools).
import { spawn, execFileSync } from 'node:child_process';
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

// Every Chrome this process started and has not closed, with its profile folder. A run that fails, ends early or is
// stopped (Ctrl-C, kill) must leave no Chrome and no profile behind (diskhygiene, 20 November 2026): the signal
// handlers quit each one cleanly over DevTools, which also removes macOS's code-sign clone, and the exit handler
// ends whatever is left, Chrome and the processes listed below it (watchBelow), and deletes the profile, synchronously
const LIVE = new Set();
const DIRS = new Set();
// every process from one `ps` listing, by pid: its parent and its start time (none where there is no `ps`)
export function processes() {
  let listing = '';
  try {
    listing = execFileSync('ps', ['-A', '-o', 'pid=,ppid=,lstart='], { encoding: 'utf8', timeout: 10000, env: { ...process.env, LC_ALL: 'C' } });
  } catch { return new Map(); }
  const table = new Map();
  for (const line of listing.split('\n')) {
    const m = line.trim().match(/^(\d+)\s+(\d+)\s+(.+)$/);
    if (m) table.set(Number(m[1]), { ppid: Number(m[2]), start: m[3].split(/\s+/).join(' ') });
  }
  return table;
}
// the processes below a pid, each with its parent and start time, into `into`. Only while the pid is this process's
// child not yet reaped (exitCode and signalCode null): node reaps it in its own event loop, which a synchronous `ps`
// holds still, so its number cannot be another process's while it is listed
function below(pid, into, table = processes()) {
  const kids = new Map();
  for (const [p, { ppid }] of table) kids.set(ppid, [...(kids.get(ppid) || []), p]);
  const todo = [pid];
  while (todo.length) {
    for (const k of kids.get(todo.pop()) || []) {
      if (into.has(k)) continue;
      into.set(k, table.get(k));
      todo.push(k);
    }
  }
  return into;
}
// SIGKILL each listed process that is still the one listed: the same start time, and the same parent or pid 1 when its
// parent has ended. A number another process has taken since is left alone. Returns the pids killed
export function endListed(listed) {
  if (!listed.size) return [];
  const table = processes(), killed = [];
  for (const [pid, { ppid, start }] of listed) {
    const now = table.get(pid);
    if (!now || now.start !== start || (now.ppid !== ppid && now.ppid !== 1)) continue;
    try { process.kill(pid, 'SIGKILL'); killed.push(pid); } catch { /* gone */ }
  }
  return killed;
}
// The processes below a started browser, listed while it lives (at 100 ms, then every half second, and once more
// before it is killed), because a helper whose parent has ended is handed to pid 1 and no longer shows below it, and
// once the browser is reaped its number may be another process's. `end()` kills the browser and then only those
// listed, each while it is still the same process, so a browser that had ended before it was listed has nothing
// killed for it (diskfix, 20 November 2026). The browser stays in this process's own process group, so a kill of that
// group takes it too
export function watchBelow(proc) {
  const listed = new Map();
  const alive = () => proc.pid && proc.exitCode === null && proc.signalCode === null;
  const look = () => { if (alive()) below(proc.pid, listed); return listed; };
  const first = setTimeout(look, 100), every = setInterval(look, 500);
  first.unref(); every.unref();
  const end = () => {
    clearTimeout(first); clearInterval(every);
    if (alive()) { look(); try { proc.kill('SIGKILL'); } catch { /* already gone */ } }
    return endListed(listed);
  };
  return { look, end, listed };
}
function reapAll() {
  for (const h of LIVE) { h.below.end(); try { rmSync(h.profile, { recursive: true, force: true }); } catch { /* gone */ } }
  LIVE.clear();
  for (const d of DIRS) { try { rmSync(d, { recursive: true, force: true }); } catch { /* gone */ } }
  DIRS.clear();
}
let handlers = false;
function installHandlers() {
  if (handlers) return;
  handlers = true;
  process.on('exit', reapAll);
  for (const [sig, code] of [['SIGINT', 130], ['SIGTERM', 143], ['SIGHUP', 129]]) {
    process.on(sig, async () => {
      try { await Promise.race([Promise.all([...LIVE].map((h) => h.close())), new Promise((ok) => setTimeout(ok, 8000))]); } catch { /* the exit handler reaps */ }
      process.exit(code);
    });
  }
}

// a scratch folder this process removes when it ends, whatever stops it (`rmSync` it earlier when its work is done)
export function tempDir(prefix) {
  installHandlers();
  const d = mkdtempSync(join(tmpdir(), prefix));
  DIRS.add(d);
  return d;
}

export async function launch() {
  if (!existsSync(CHROME)) throw new Error(`no Chrome at ${CHROME} (set IDIOGRAPH_CHROME)`);
  installHandlers();
  const profile = mkdtempSync(join(tmpdir(), 'idiograph-motion-'));
  const proc = spawn(CHROME, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`, '--no-first-run',
    '--no-default-browser-check', '--hide-scrollbars', '--mute-audio', '--disable-extensions', 'about:blank'],
    { stdio: ['ignore', 'ignore', 'pipe'] });
  const handle = { proc, profile, close: null, below: watchBelow(proc) };
  LIVE.add(handle);
  let ws = null, id = 0;
  const waiting = new Map(), listeners = [];
  const send = (method, params = {}, sessionId) => new Promise((ok, fail) => {
    const n = ++id; waiting.set(n, { ok, fail });
    ws.send(JSON.stringify({ id: n, method, params, ...(sessionId ? { sessionId } : {}) }));
  });
  const close = async () => {
    handle.below.look(); // its helpers as they stand before it is asked to quit
    if (ws) { try { await Promise.race([send('Browser.close'), new Promise((ok) => setTimeout(ok, 3000))]); } catch { /* already gone */ } try { ws.close(); } catch { /* closed */ } }
    await new Promise((ok) => {
      if (proc.exitCode !== null) return ok();
      proc.on('exit', ok);
      if (!ws) proc.kill('SIGTERM');
      setTimeout(ok, 5000);
    });
    handle.below.end();
    rmSync(profile, { recursive: true, force: true });
    LIVE.delete(handle);
  };
  handle.close = close;
  try {
    const wsUrl = await new Promise((ok, fail) => {
      let err = '';
      const t = setTimeout(() => fail(new Error('Chrome did not open its DevTools port in 20 s')), 20000);
      proc.stderr.on('data', (d) => { err += d; const m = err.match(/DevTools listening on (ws:\/\/\S+)/); if (m) { clearTimeout(t); ok(m[1]); } });
      proc.on('exit', (c) => { clearTimeout(t); fail(new Error(`Chrome quit (${c}): ${err.slice(-400)}`)); });
    });
    ws = new WebSocket(wsUrl);
    await new Promise((ok, fail) => { ws.onopen = ok; ws.onerror = () => fail(new Error('no DevTools connection')); });
  } catch (err) { await close(); throw err; }
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && waiting.has(msg.id)) {
      const { ok, fail } = waiting.get(msg.id); waiting.delete(msg.id);
      msg.error ? fail(new Error(`${msg.error.message} ${msg.error.data || ''}`)) : ok(msg.result);
    } else if (msg.method) for (const l of listeners) l(msg);
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
