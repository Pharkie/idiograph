// Records a short clip of the real app for the website's Screenshots page (siteclips, 12 November 2026): a clip
// script drives the page in headless Chrome with a pointer drawn in the page where its mouse is, and Chrome's own
// screencast writes each frame it paints, with its time, to the out folder (f00000.jpg on, frames.json), never the
// screen. clip-encode.sh makes the frames a looping MP4 and WebM at a steady rate.
// A clip script is a module with `setup(h)`, run before the recording (open the screen, get it ready), and
// `act(h)`, the action recorded. `h` is below. --probe runs setup alone and shoots probe.png, to check the framing
import { mkdirSync, writeFileSync, rmSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { args, serverUrl, launch } from './chrome.mjs';

const USAGE = `node packaging/motion/clip.mjs --script <clip script.mjs> --out <folder>
  [--port 8770 | --url http://127.0.0.1:8770/] [--width 1280] [--height 800] [--scale 2] [--scheme light|dark]
  [--quality 92] [--probe]`;
const o = args({ script: '', out: '', port: 8770, url: '', width: 1280, height: 800, scale: 2, scheme: 'light', quality: 92, probe: false }, USAGE);
if (!o.script || !o.out) { console.error(USAGE); process.exit(2); }
const base = serverUrl(o);
const clip = await import(pathToFileURL(resolve(o.script)).href);

// the pointer: an arrow in the page at the mouse, moved by the page's own pointer events, so the frames show
// where each move, press and drag happens. A press darkens its ring. It takes no events and sits over everything
export const POINTER = `(() => {
  const draw = () => {
    if (document.getElementById('clip-pointer') || !document.body) return;
    const p = document.createElement('div');
    p.id = 'clip-pointer';
    p.innerHTML = '<span class="ring"></span><svg width="22" height="30" viewBox="0 0 22 30"><path d="M2 2v21.5l5.6-5.2 3.7 8.6 3.6-1.6-3.6-8.4H19z" fill="#111" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    const st = document.createElement('style');
    st.textContent = '#clip-pointer{position:fixed;left:0;top:0;z-index:2147483647;pointer-events:none;will-change:transform;transform:translate(-200px,-200px)}'
      + '#clip-pointer svg{position:absolute;left:-2px;top:-2px;filter:drop-shadow(0 1px 1.5px rgba(0,0,0,.35))}'
      + '#clip-pointer .ring{position:absolute;left:-14px;top:-14px;width:28px;height:28px;border-radius:50%;background:rgba(242,107,29,.0);transition:background .12s}'
      + '#clip-pointer.down .ring{background:rgba(242,107,29,.28)}';
    document.documentElement.appendChild(st);
    document.documentElement.appendChild(p);
    const at = window.__clipAt || { x: -200, y: -200 };
    p.style.transform = 'translate(' + at.x + 'px,' + at.y + 'px)';
  };
  const move = (e) => {
    window.__clipAt = { x: e.clientX, y: e.clientY };
    const p = document.getElementById('clip-pointer');
    if (p) p.style.transform = 'translate(' + e.clientX + 'px,' + e.clientY + 'px)';
  };
  for (const k of ['pointermove', 'pointerdown', 'pointerup']) window.addEventListener(k, move, { capture: true, passive: true });
  // and by hand while a page's own drag and drop runs, which sends the page no pointer events
  window.__clipMove = (x, y, down) => {
    move({ clientX: x, clientY: y });
    const p = document.getElementById('clip-pointer');
    if (p) p.classList.toggle('down', !!down);
  };
  window.addEventListener('pointerdown', () => { const p = document.getElementById('clip-pointer'); if (p) p.classList.add('down'); }, true);
  window.addEventListener('pointerup', () => { const p = document.getElementById('clip-pointer'); if (p) p.classList.remove('down'); }, true);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', draw); else draw();
  new MutationObserver(draw).observe(document, { childList: true, subtree: true });
})();`;

const KEYS = {
  Enter: { code: 'Enter', vk: 13, text: '\r' }, Escape: { code: 'Escape', vk: 27 }, Tab: { code: 'Tab', vk: 9 },
  Backspace: { code: 'Backspace', vk: 8 }, Delete: { code: 'Delete', vk: 46 }, Space: { key: ' ', code: 'Space', vk: 32, text: ' ' },
  ArrowUp: { code: 'ArrowUp', vk: 38 }, ArrowDown: { code: 'ArrowDown', vk: 40 }, ArrowLeft: { code: 'ArrowLeft', vk: 37 }, ArrowRight: { code: 'ArrowRight', vk: 39 },
};
const MODS = { alt: 1, ctrl: 2, meta: 4, shift: 8 };
const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const sleep = (ms) => new Promise((ok) => setTimeout(ok, ms));

const browser = await launch();
let failed = null;
try {
  const page = await browser.newPage({ width: o.width, height: o.height, scale: o.scale, scheme: o.scheme });
  await page.initScript(POINTER);
  let at = { x: o.width / 2, y: o.height / 2 }, pressed = false, chooser = null;
  page.on('Page.fileChooserOpened', (p) => {
    if (!chooser) return;
    const files = chooser;
    chooser = null;
    page.cdp('DOM.setFileInputFiles', { files, backendNodeId: p.backendNodeId }).catch((err) => console.error('file chooser:', err.message));
  });
  const mouse = (type, x, y, extra = {}) => page.cdp('Input.dispatchMouseEvent', { type, x, y, button: pressed || type !== 'mouseMoved' ? 'left' : 'none', buttons: pressed ? 1 : 0, ...extra });
  const h = {
    page, base, width: o.width, height: o.height, scheme: o.scheme, out: resolve(o.out), sleep,
    wait: sleep,
    // a place after a # loads afresh, as the app reads it as it starts (a change of the # alone loads nothing)
    goto: async (path = '') => { if (path.includes('#')) await page.goto('about:blank'); await page.goto(new URL(path, base).href); },
    visible: (sel, ms) => page.waitVisible(sel, ms),
    eval: (fn, arg) => page.evaluate(fn, arg),
    // an element's box in CSS pixels, its middle as cx and cy, or null when there is none or it is not shown
    box: (sel) => page.evaluate((q) => {
      const e = typeof q === 'string' ? document.querySelector(q) : null;
      if (!e) return null;
      const r = e.getBoundingClientRect();
      if (!r.width && !r.height) return null;
      return { x: r.x, y: r.y, w: r.width, h: r.height, cx: r.x + r.width / 2, cy: r.y + r.height / 2 };
    }, sel),
    // the pointer to x, y over ms with an ease, a step each 16 ms of the wall clock the screencast runs on
    move: async (x, y, ms = 700) => {
      const from = { ...at }, steps = Math.max(1, Math.round(ms / 16)), t0 = Date.now();
      for (let i = 1; i <= steps; i++) {
        const k = ease(i / steps);
        at = { x: from.x + (x - from.x) * k, y: from.y + (y - from.y) * k };
        await mouse('mouseMoved', at.x, at.y);
        const due = t0 + (i * ms) / steps - Date.now();
        if (due > 0) await sleep(due);
      }
    },
    place: async (x, y) => { at = { x, y }; await mouse('mouseMoved', x, y); },
    down: async () => { pressed = true; await mouse('mousePressed', at.x, at.y, { clickCount: 1 }); },
    up: async () => { await mouse('mouseReleased', at.x, at.y, { clickCount: 1 }); pressed = false; },
    click: async (x, y, { ms = 700, hold = 90, count = 1 } = {}) => {
      if (x !== undefined) await h.move(x, y, ms);
      for (let c = 1; c <= count; c++) {
        pressed = true; await mouse('mousePressed', at.x, at.y, { clickCount: c });
        await sleep(hold);
        await mouse('mouseReleased', at.x, at.y, { clickCount: c }); pressed = false;
        if (c < count) await sleep(60);
      }
    },
    clickOn: async (sel, opts = {}) => {
      const b = await h.box(sel);
      if (!b) throw new Error(`nothing to click: ${sel}`);
      await h.click(b.cx + (opts.dx || 0), b.cy + (opts.dy || 0), opts);
    },
    // press, a short pause, the move, a short pause, release, as a hand drags
    drag: async (x, y, { ms = 1100, settle = 160, mods = 0 } = {}) => {
      pressed = true; await mouse('mousePressed', at.x, at.y, { clickCount: 1, modifiers: mods });
      await sleep(settle);
      // a few pixels first, so a drag threshold is passed as a hand passes it
      await mouse('mouseMoved', at.x + 3, at.y + 2, { modifiers: mods });
      await h.move(x, y, ms);
      await sleep(settle);
      await mouse('mouseReleased', at.x, at.y, { clickCount: 1, modifiers: mods }); pressed = false;
    },
    // a drag the page makes with the browser's own drag and drop (draggable="true"), which a headless page starts
    // but never carries on: Chrome hands it over (Input.setInterceptDrags) and it is carried to x, y and dropped
    // there through the drag's own events, the pointer drawn along the way
    dragNative: async (x, y, { ms = 1100, settle = 160 } = {}) => {
      await page.cdp('Input.setInterceptDrags', { enabled: true });
      let data = null;
      const got = new Promise((ok) => page.on('Input.dragIntercepted', (p) => { data = p.data; ok(); }));
      pressed = true;
      await mouse('mousePressed', at.x, at.y, { clickCount: 1 });
      await page.evaluate(([px, py]) => window.__clipMove && window.__clipMove(px, py, true), [at.x, at.y]);
      await sleep(settle);
      for (let i = 1; i <= 4 && !data; i++) { await mouse('mouseMoved', at.x + i * 2, at.y + i); await sleep(30); }
      await Promise.race([got, sleep(1500)]);
      if (!data) throw new Error('the page started no drag here');
      const from = { ...at }, steps = Math.max(1, Math.round(ms / 16)), t0 = Date.now();
      await page.cdp('Input.dispatchDragEvent', { type: 'dragEnter', x: from.x, y: from.y, data });
      for (let i = 1; i <= steps; i++) {
        const k = ease(i / steps);
        at = { x: from.x + (x - from.x) * k, y: from.y + (y - from.y) * k };
        await page.cdp('Input.dispatchDragEvent', { type: 'dragOver', x: at.x, y: at.y, data });
        await page.evaluate(([px, py]) => window.__clipMove && window.__clipMove(px, py, true), [at.x, at.y]);
        const due = t0 + (i * ms) / steps - Date.now();
        if (due > 0) await sleep(due);
      }
      await sleep(settle);
      await page.cdp('Input.dispatchDragEvent', { type: 'drop', x: at.x, y: at.y, data });
      await mouse('mouseReleased', at.x, at.y, { clickCount: 1 });
      pressed = false;
      await page.evaluate(([px, py]) => window.__clipMove && window.__clipMove(px, py, false), [at.x, at.y]);
      await page.cdp('Input.setInterceptDrags', { enabled: false });
    },
    key: async (name, mods = []) => {
      const m = mods.reduce((a, k) => a | MODS[k], 0);
      const k = KEYS[name] || { key: name, code: name.length === 1 ? `Key${name.toUpperCase()}` : name, vk: name.length === 1 ? name.toUpperCase().charCodeAt(0) : 0, text: name.length === 1 ? name : undefined };
      const key = k.key || name;
      const text = m & (MODS.meta | MODS.ctrl) ? undefined : k.text;
      await page.cdp('Input.dispatchKeyEvent', { type: text ? 'keyDown' : 'rawKeyDown', key, code: k.code, windowsVirtualKeyCode: k.vk, modifiers: m, text, unmodifiedText: text });
      await page.cdp('Input.dispatchKeyEvent', { type: 'keyUp', key, code: k.code, windowsVirtualKeyCode: k.vk, modifiers: m });
    },
    // typed a letter at a time at about cps a second, as a person types
    type: async (text, { cps = 14 } = {}) => {
      for (const ch of text) {
        if (ch === '\n') await h.key('Enter');
        else {
          await page.cdp('Input.dispatchKeyEvent', { type: 'keyDown', key: ch, text: ch, unmodifiedText: ch });
          await page.cdp('Input.dispatchKeyEvent', { type: 'keyUp', key: ch });
        }
        await sleep(1000 / cps * (0.7 + Math.random() * 0.6));
      }
    },
    wheel: async (dy, dx = 0) => { await mouse('mouseWheel', at.x, at.y, { deltaX: dx, deltaY: dy }); },
    shot: (path, clipBox) => page.shot(path, clipBox),
    style: (css) => page.style(css),
    // the next file chooser the page opens answered with these files, as a person picks them in the system's
    // dialog, which a headless page never draws
    chooseFiles: async (paths) => {
      await page.cdp('Page.setInterceptFileChooserDialog', { enabled: true });
      chooser = paths;
    },
    files: async (sel, paths) => {
      const { root } = await page.cdp('DOM.getDocument', { depth: 0 });
      const { nodeId } = await page.cdp('DOM.querySelector', { nodeId: root.nodeId, selector: sel });
      if (!nodeId) throw new Error(`no file input ${sel}`);
      await page.cdp('DOM.setFileInputFiles', { nodeId, files: paths });
    },
  };

  mkdirSync(o.out, { recursive: true });
  await page.goto(base);
  if (clip.setup) await clip.setup(h);
  if (o.probe) {
    await h.shot(`${o.out}/probe.png`);
    console.log('probe', `${o.out}/probe.png`, page.errors.length ? 'errors: ' + page.errors.join(' | ') : 'no page errors');
  } else {
    // a recording before this one in the folder goes first
    for (const f of readdirSync(o.out)) if (/^f\d{5}\.jpg$|^frames\.json$/.test(f)) rmSync(`${o.out}/${f}`);
    const frames = [];
    let n = 0, t0 = null;
    page.on('Page.screencastFrame', (p) => {
      const t = p.metadata.timestamp;
      if (t0 === null) t0 = t;
      const file = `f${String(n++).padStart(5, '0')}.jpg`;
      writeFileSync(`${o.out}/${file}`, Buffer.from(p.data, 'base64'));
      frames.push({ file, t: +(t - t0).toFixed(4) });
      page.cdp('Page.screencastFrameAck', { sessionId: p.sessionId }).catch(() => {});
    });
    await page.cdp('Page.startScreencast', { format: 'jpeg', quality: o.quality, everyNthFrame: 1, maxWidth: o.width * o.scale, maxHeight: o.height * o.scale });
    // a nudge so the first frame comes at once, then the action
    await page.evaluate(() => { document.documentElement.style.outline = '0 solid transparent'; });
    await sleep(300);
    const began = Date.now();
    try { await clip.act(h); } catch (err) { failed = err; }
    const wall = (Date.now() - began) / 1000;
    await sleep(200);
    await page.cdp('Page.stopScreencast');
    await sleep(200);
    const end = frames.length ? Math.max(frames[frames.length - 1].t, wall + 0.3) : 0;
    writeFileSync(`${o.out}/frames.json`, JSON.stringify({ width: o.width, height: o.height, scale: o.scale, scheme: o.scheme, end: +end.toFixed(3), frames, errors: page.errors }));
    const gaps = frames.slice(1).map((f, i) => f.t - frames[i].t);
    console.log(o.out, frames.length, 'frames over', end.toFixed(1), 's, longest gap', gaps.length ? Math.max(...gaps).toFixed(2) : 0, 's,',
      page.errors.length ? 'errors: ' + page.errors.join(' | ') : 'no page errors');
  }
} catch (err) { failed = err; } finally { await browser.close(); }
if (failed) { console.error(failed.stack || failed.message); process.exit(1); }
