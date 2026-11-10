// Every screen at each zoom in the Mac's own engine (zoomsweep, 30 October 2026, after Adam's sideways bar on Send
// feedback's note box at Text size Large, 29 October): a group of screens.mjs shot through packaging/wk_shot.swift
// at each page zoom and window size, with what the page itself shows of the faults a zoom brings, read in the page
// and set beside the same screen at 100%.
//
//   node packaging/pixels/zoom_sweep.mjs --port <PORT> --out <dir> [--group zoom] [--zooms 1,1.25,1.5]
//        [--sizes 1280x800,720x800] [--scheme light] [--scale 1] [--wk <compiled wk_shot>]
//        [--sift <screening folder>] [--trace <Trace project folder>]
//
// Each size and zoom is one run of wk_shot (compiled into a temporary folder when --wk is left out), the whole sweep
// one run of ~/.claude/bin/heavy where it is there. It writes <dir>/<width>x<height>-<zoom>/<screen>.png and faults.json, and
// at the end <dir>/faults.md: for each screen and zoom, each fault the page shows there that it does not show at the
// first zoom of the list at that size. What it reads in the page (FAULTS below): a box or the page with a scroll bar
// it needs, sideways or up and down, words cut short with no ellipsis, a control past the window's edge where nothing
// scrolls to it, a card taller than the window, two controls or two lines of words over each other, and how tall
// each bar is, a bar that grows having wrapped. Pictures are for the eye, the list for where to look.
import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir, homedir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { args, serverUrl } from '../motion/chrome.mjs';
import { SCREENS } from './screens.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const USAGE = `node packaging/pixels/zoom_sweep.mjs --port <port> --out <dir> [--group zoom] [--zooms 1,1.25,1.5]
     [--sizes 1280x800,720x800] [--scheme light] [--scale 1] [--wk <compiled wk_shot>] [--sift <folder>] [--trace <folder>]`;

// What a zoom breaks, read in the page: a list of [kind, where, how much], `where` an element's tag, id and first
// classes with the start of its words. Kinds: bar-x and bar-y (a box drawing a scroll bar, by how many pixels it
// overflows), page-x and page-y (the window itself scrolls), cut (words wider than a box that hides the rest, no
// ellipsis), off (a control past the window's edge, nothing scrolling to it), tall (a card taller than the window
// with nothing in it scrolling), overlap (two controls, or two lines of words, over each other), bar (a bar's height)
const FAULTS = `(() => {
  const W = innerWidth, H = innerHeight, out = [];
  const shown = (e) => { if (!e.getClientRects().length) return false; const s = getComputedStyle(e); return s.visibility !== 'hidden' && s.display !== 'none' && Number(s.opacity) > 0.05; };
  const name = (e) => { const c = [...e.classList].slice(0, 2).join('.'); const t = (e.innerText || e.value || e.placeholder || e.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' ').slice(0, 30);
    return e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (c ? '.' + c : '') + (t ? ' "' + t + '"' : ''); };
  const scrolls = (e, axis) => { const s = getComputedStyle(e); const o = axis === 'x' ? s.overflowX : s.overflowY;
    return (o === 'auto' || o === 'scroll') && (axis === 'x' ? e.scrollWidth > e.clientWidth : e.scrollHeight > e.clientHeight); };
  const all = [...document.querySelectorAll('body *')].filter((e) => !e.closest('[hidden]') && shown(e));
  const se = document.scrollingElement || document.documentElement;
  if (se.scrollWidth > W + 1) out.push(['page-x', 'the window', se.scrollWidth - W]);
  if (se.scrollHeight > H + 1 && getComputedStyle(document.body).overflowY !== 'hidden') out.push(['page-y', 'the window', se.scrollHeight - H]);
  for (const e of all) {
    const s = getComputedStyle(e);
    for (const axis of ['x', 'y']) {
      const o = axis === 'x' ? s.overflowX : s.overflowY;
      if (o !== 'auto' && o !== 'scroll') continue;
      const over = axis === 'x' ? e.scrollWidth - e.clientWidth : e.scrollHeight - e.clientHeight;
      const bar = axis === 'x' ? e.offsetHeight - e.clientHeight - (parseFloat(s.borderTopWidth) + parseFloat(s.borderBottomWidth))
        : e.offsetWidth - e.clientWidth - (parseFloat(s.borderLeftWidth) + parseFloat(s.borderRightWidth));
      // a pixel over is the rounding of a fraction, which WebKit draws no bar for
      if (over > 1 || (o === 'scroll' && bar > 0)) out.push(['bar-' + axis, name(e), over]);
    }
    if ((s.overflowX === 'hidden' || s.overflowX === 'clip') && s.textOverflow !== 'ellipsis' && e.scrollWidth > e.clientWidth + 1
        && [...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) out.push(['cut', name(e), e.scrollWidth - e.clientWidth]);
  }
  const controls = all.filter((e) => e.matches('button, a[href], input:not([type=hidden]), select, textarea, [role=button], [role=tab], label'));
  for (const e of controls) {
    const r = e.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    const past = r.right > W + 1 ? 'right' : r.bottom > H + 1 ? 'bottom' : r.left < -1 ? 'left' : r.top < -1 ? 'top' : '';
    if (!past) continue;
    const axis = past === 'right' || past === 'left' ? 'x' : 'y';
    let reach = axis === 'x' ? se.scrollWidth > W + 1 : se.scrollHeight > H + 1;
    for (let p = e.parentElement; p && !reach; p = p.parentElement) reach = scrolls(p, axis);
    if (!reach) out.push(['off', name(e), past]);
  }
  for (const c of all.filter((e) => e.matches('.card, [role=dialog]') && !e.closest('#themes .th-canvas, #tj-board'))) {
    const r = c.getBoundingClientRect();
    if (r.height > H + 1 || r.bottom > H + 1 || r.top < -1) {
      const inner = [c, ...c.querySelectorAll('*')].some((e) => scrolls(e, 'y'));
      if (!inner) out.push(['tall', name(c), Math.round(r.height - H)]);
    }
  }
  const lines = [];
  for (const e of all) {
    if (e.closest('.th-canvas, #tj-board, svg')) continue;
    const own = [...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
    if (!own && !e.matches('button, input, select, textarea')) continue;
    const r = e.getBoundingClientRect();
    if (!(r.width > 1 && r.height > 1 && r.bottom > 0 && r.top < H && r.right > 0 && r.left < W)) continue;
    // on top where it is drawn, so words a card covers are never counted against the card's
    const at = document.elementFromPoint(Math.min(W - 1, Math.max(0, (r.left + r.right) / 2)), Math.min(H - 1, Math.max(0, (r.top + r.bottom) / 2)));
    if (at && (e.contains(at) || at.contains(e))) lines.push([e, r]);
  }
  const clip = (e, r) => { let x0 = r.left, y0 = r.top, x1 = r.right, y1 = r.bottom;
    for (let p = e.parentElement; p; p = p.parentElement) { const s = getComputedStyle(p); if (s.overflow === 'visible') continue;
      const q = p.getBoundingClientRect(); x0 = Math.max(x0, q.left); y0 = Math.max(y0, q.top); x1 = Math.min(x1, q.right); y1 = Math.min(y1, q.bottom); }
    return [x0, y0, x1, y1]; };
  const boxes = lines.map(([e, r]) => [e, clip(e, r)]).filter(([, b]) => b[2] - b[0] > 1 && b[3] - b[1] > 1);
  for (let i = 0; i < boxes.length; i++) {
    for (let j = i + 1; j < boxes.length; j++) {
      const [a, p] = boxes[i], [b, q] = boxes[j];
      if (a.contains(b) || b.contains(a)) continue;
      const w = Math.min(p[2], q[2]) - Math.max(p[0], q[0]), h = Math.min(p[3], q[3]) - Math.max(p[1], q[1]);
      if (w > 3 && h > 3) {
        const top = document.elementFromPoint((Math.max(p[0], q[0]) + Math.min(p[2], q[2])) / 2, (Math.max(p[1], q[1]) + Math.min(p[3], q[3])) / 2);
        if (top && (a.contains(top) || b.contains(top) || top.contains(a) || top.contains(b))) out.push(['overlap', name(a) + ' / ' + name(b), Math.round(w) + 'x' + Math.round(h)]);
      }
    }
  }
  for (const b of all.filter((e) => e.matches('header, footer, [role=toolbar], .rail, .topbar, .toolbar, .statusbar, .status-bar, .card-actions'))) {
    out.push(['bar', name(b).replace(/ ".*/, ''), Math.round(b.getBoundingClientRect().height)]);
  }
  return out;
})()`;

const LIST_PANES = `[...document.querySelectorAll('#settings-nav [role="tab"]')].filter((t) => t.offsetParent !== null).map((t) => t.dataset.pane)`;
const PANE = (p) => `(async () => { document.querySelector('#settings-nav [data-pane="${p}"]').click(); const box = document.getElementById('settings-panes');
  box.scrollTop = 0; await new Promise((r) => setTimeout(r, 300)); return box.scrollHeight > box.clientHeight + 1; })()`;
const PANE_END = `(() => { const box = document.getElementById('settings-panes'); box.scrollTop = box.scrollHeight; return box.scrollTop; })()`;

function compile(o) {
  if (o.wk) return resolve(o.wk);
  const dir = mkdtempSync(join(tmpdir(), 'wk-shot-'));
  const bin = join(dir, 'wk_shot');
  const r = spawnSync('swiftc', ['-O', join(HERE, '..', 'wk_shot.swift'), '-o', bin], { encoding: 'utf8' });
  if (r.status !== 0) { console.error(r.stderr); process.exit(1); }
  return bin;
}

// one run of wk_shot, inside the sweep's heavy run, and the js lines of its output by step
function wk(bin, o, size, zoom, steps, out) {
  mkdirSync(out, { recursive: true });
  const file = join(out, 'steps.json');
  writeFileSync(file, JSON.stringify(steps));
  const [w, h] = size.split('x');
  // each screen from Home freshly loaded, never the screen the last one left (the page's return place), and Home's
  // mark not played
  const init = `try { sessionStorage.clear(); sessionStorage.setItem('idiograph.homeMark', '1'); } catch (e) {}
    window.SWEEP = ${JSON.stringify({ sift: o.sift, trace: o.trace })};`;
  const cmd = [bin, '--url', serverUrl(o), '--out', out, '--steps', file, '--width', w, '--height', h, '--zoom', String(zoom),
    '--scheme', o.scheme, '--scale', String(o.scale), '--init', init, '--timeout', '1800'];
  const r = spawnSync(cmd[0], cmd.slice(1), { encoding: 'utf8', maxBuffer: 64 << 20 });
  if (r.status !== 0) console.error(`${size} at ${zoom}: ${(r.stderr || '').trim().slice(-400)}`);
  const said = {};
  for (const line of (r.stdout || '').split('\n')) {
    const m = line.match(/^js (\d+): (.*)$/);
    if (m) { try { said[m[1]] = JSON.parse(m[2]); } catch { said[m[1]] = m[2]; } }
  }
  return said;
}

const o = args({ port: 0, url: '', out: '', group: 'zoom', zooms: '1,1.25,1.5', sizes: '1280x800,720x800', scheme: 'light',
  scale: 1, wk: '', sift: '', trace: '' }, USAGE);
if (!o.out || (!o.port && !o.url) || !SCREENS[o.group]) { console.error(USAGE); process.exit(2); }
// the whole sweep one heavy run on a shared Mac, this script run again inside it
const heavy = join(homedir(), '.claude', 'bin', 'heavy');
if (existsSync(heavy) && !process.env.ZOOM_SWEEP_HEAVY) {
  const r = spawnSync(heavy, ['idiograph', 'shots', process.execPath, ...process.argv.slice(1)],
    { stdio: 'inherit', env: { ...process.env, ZOOM_SWEEP_HEAVY: '1' } });
  process.exit(r.status ?? 1);
}
const group = SCREENS[o.group];
const bin = compile(o);
const zooms = o.zooms.split(',').map(Number);
const report = ['# Faults by zoom', ''];

for (const size of o.sizes.split(',')) {
  // the Settings categories each screen with panes holds, read once at the first zoom
  const panes = {};
  const listing = [];
  for (const s of group.filter((x) => x.panes)) {
    listing.push({ load: serverUrl(o) }, { js: `(${s.open})()`, waitFor: s.wait, wait: 600 }, { js: LIST_PANES });
  }
  if (listing.length) {
    const said = wk(bin, o, size, zooms[0], listing, join(o.out, 'panes'));
    group.filter((x) => x.panes).forEach((s, i) => { panes[s.name] = Array.isArray(said[i * 3 + 2]) ? said[i * 3 + 2] : []; });
  }
  const found = {};
  for (const zoom of zooms) {
    const steps = [], probes = {};
    const probe = (shot) => { probes[steps.length] = shot; steps.push({ js: FAULTS, wait: 100 }); steps.push({ shot, wait: 100 }); };
    for (const s of group) {
      steps.push({ load: serverUrl(o) }, { js: `(${s.open})()`, waitFor: s.wait, wait: 700 });
      if (!s.panes) { probe(s.name); continue; }
      for (const p of panes[s.name] || []) {
        steps.push({ js: PANE(p), wait: 300 });
        probe(`${s.name}-${p}`);
        steps.push({ js: PANE_END, wait: 300 });
        probe(`${s.name}-${p}-end`);
      }
    }
    const dir = join(o.out, `${size}-${zoom}`);
    const said = wk(bin, o, size, zoom, steps, dir);
    const faults = {};
    for (const [at, shot] of Object.entries(probes)) faults[shot] = Array.isArray(said[at]) ? said[at] : [['probe', String(said[at]), '']];
    writeFileSync(join(dir, 'faults.json'), JSON.stringify(faults, null, 1));
    found[zoom] = faults;
  }
  // what each zoom shows that the first does not, by kind and place, a bar by its height
  const key = (f) => (f[0] === 'bar' ? f.join(' ') : `${f[0]} ${f[1]}`);
  const first = found[zooms[0]];
  for (const zoom of zooms.slice(1)) {
    report.push(`## ${size} at ${Math.round(zoom * 100)}%, set beside ${Math.round(zooms[0] * 100)}%`, '');
    for (const [shot, list] of Object.entries(found[zoom])) {
      const before = new Set((first[shot] || []).map(key));
      const fresh = list.filter((f) => !before.has(key(f)));
      if (fresh.length) report.push(`- ${shot}: ${fresh.map((f) => `${f[0]} ${f[1]} (${f[2]})`).join('; ')}`);
    }
    report.push('');
  }
  report.push(`## ${size} at ${Math.round(zooms[0] * 100)}%, all`, '');
  for (const [shot, list] of Object.entries(first)) {
    const real = list.filter((f) => f[0] !== 'bar' && f[0] !== 'bar-y');
    if (real.length) report.push(`- ${shot}: ${real.map((f) => `${f[0]} ${f[1]} (${f[2]})`).join('; ')}`);
  }
  report.push('');
}
writeFileSync(join(o.out, 'faults.md'), report.join('\n'));
console.log(`ZOOM: ${o.group} at ${zooms.join(', ')} in ${o.sizes}, faults in ${join(o.out, 'faults.md')}`);
