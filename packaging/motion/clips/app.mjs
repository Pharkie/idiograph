// What the Screenshots page's clip scripts share: the app's screens opened as a person opens them, from Home's
// rows, and the places on them a pointer goes to. Each runs on the page clip.mjs drives (`h`)

// a visible element whose own words are `text`, the last of them, its box in CSS pixels, or null
export const byText = (h, text, within = 'button, a, [role=menuitem], li, label, span, div, p, h1, h2, h3, td, th') => h.eval(([t, r]) => {
  const all = [...document.querySelectorAll(r)].filter((e) => {
    const s = e.getBoundingClientRect();
    return s.width > 0 && s.height > 0 && e.textContent.trim() === t;
  });
  const e = all[all.length - 1];
  if (!e) return null;
  const s = e.getBoundingClientRect();
  return { x: s.x, y: s.y, w: s.width, h: s.height, cx: s.x + s.width / 2, cy: s.y + s.height / 2 };
}, [text, within]);

export async function clickText(h, text, opts = {}) {
  const b = await byText(h, text, opts.within);
  if (!b) throw new Error(`nothing reads "${text}"`);
  await h.click(b.cx + (opts.dx || 0), b.cy + (opts.dy || 0), { ms: 10, ...opts });
  return b;
}

// Home without the mark coming in, so a setup starts on a still page
export async function home(h) {
  await h.eval(() => sessionStorage.setItem('idiograph.homeMark', '1'));
  await h.goto('');
  await h.visible('#hp-list .pcard');
  await h.sleep(600);
}

// a participant's row on the project's page, by its pseudonym, and its Experiential statements or PETs half
export async function openParticipant(h, who, half = 'pets') {
  const b = await h.eval(([w, part]) => {
    const row = [...document.querySelectorAll('#hp-list .pcard')].find((r) => r.innerText.split('\n')[0].trim() === w);
    const e = row && row.querySelector(part === 'pets' ? '.pc-pets' : '.pc-es, .pc-half:not(.pc-pets)');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { cx: r.x + r.width / 2, cy: r.y + r.height / 2 };
  }, [who, half]);
  if (!b) throw new Error(`no row for ${who}`);
  await h.click(b.cx, b.cy, { ms: 10 });
  await h.visible(half === 'pets' ? '#th-status' : '#es-status');
  await h.sleep(1200);
}

// a label on the board whose title holds `words`, its box
export const label = (h, words) => h.eval((w) => {
  const e = [...document.querySelectorAll('#th-stage .th-label')].find((x) => x.innerText.includes(w));
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return { x: r.x, y: r.y, w: r.width, h: r.height, cx: r.x + r.width / 2, cy: r.y + r.height / 2 };
}, words);

// a statement's row in the sidebar's Not placed, by its key
export const waiting = (h, key) => h.eval((k) => {
  const e = document.querySelector(`li.ts-row[data-tskey="${k}"]`);
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return { x: r.x, y: r.y, w: r.width, h: r.height, cx: r.x + r.width / 2, cy: r.y + r.height / 2 };
}, key);

// the sidebar's list scrolled so the row of `key` stands `gap` pixels under its top
export const sidebarTo = (h, key, gap = 8) => h.eval(([k, g]) => {
  const e = document.querySelector(`li.ts-row[data-tskey="${k}"]`);
  const list = e.closest('.th-panel-body');
  list.scrollTop += e.getBoundingClientRect().top - list.getBoundingClientRect().top - g;
}, [key, gap]);

// a statement dragged from the sidebar to x, y on the canvas, picked up by its words
export async function bring(h, key, x, y, { reach = 700, ms = 1000 } = {}) {
  const r = await waiting(h, key);
  if (!r) throw new Error(`${key} is not waiting in the sidebar`);
  await h.move(r.x + 110, r.y + Math.min(r.h / 2, 22), reach);
  await h.sleep(120);
  await h.drag(x, y, { ms });
}

// where words stand on the screen: the left edge of the first letter of `from` and the right edge of the last of
// `to`, in the first element of `within` whose text holds both, for a drag that selects them as a hand would
export const wordsAt = (h, within, from, to) => h.eval(([q, a, b]) => {
  const roots = [...document.querySelectorAll(q)].filter((e) => e.getBoundingClientRect().width > 0);
  for (const root of roots) {
    const walk = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    let text = '';
    for (let n = walk.nextNode(); n; n = walk.nextNode()) { nodes.push([n, text.length]); text += n.data; }
    const i = text.indexOf(a), j = text.indexOf(b, Math.max(0, i));
    if (i < 0 || j < 0) continue;
    const spot = (k) => { let at = nodes[0]; for (const nd of nodes) if (nd[1] <= k) at = nd; return [at[0], k - at[1]]; };
    const r = document.createRange();
    const [n1, o1] = spot(i); r.setStart(n1, o1); r.setEnd(n1, Math.min(n1.data.length, o1 + 1));
    const s = r.getClientRects()[0];
    const [n2, o2] = spot(j + b.length - 1); r.setStart(n2, o2); r.setEnd(n2, o2 + 1);
    const e = r.getClientRects()[0];
    return { x1: s.left + 1, y1: s.top + s.height / 2, x2: e.right - 1, y2: e.top + e.height / 2 };
  }
  return null;
}, [within, from, to]);

// the scrolling box round `sel` (the page itself when none is) scrolled with an ease over `ms` until `sel` stands
// `at` of the way down the window, as a trackpad's glide scrolls it, frame by frame
export const glideTo = (h, sel, at = 0.5, ms = 1200) => h.eval(([q, a, t]) => new Promise((done) => {
  const e = document.querySelector(q);
  let box = e.parentElement;
  while (box && box !== document.body && !(box.scrollHeight > box.clientHeight + 1 && /auto|scroll/.test(getComputedStyle(box).overflowY))) box = box.parentElement;
  const page = !box || box === document.body;
  const get = () => (page ? window.scrollY : box.scrollTop);
  const set = (y) => (page ? window.scrollTo(0, y) : (box.scrollTop = y));
  const view = page ? { top: 0, height: window.innerHeight } : box.getBoundingClientRect();
  const from = get(), d = e.getBoundingClientRect().top - view.top - view.height * a, t0 = performance.now();
  const step = (now) => {
    const k = Math.min(1, (now - t0) / t);
    set(from + d * (k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2));
    if (k < 1) requestAnimationFrame(step); else done();
  };
  requestAnimationFrame(step);
}), [sel, at, ms]);

// the page scrolled by `px` with the same ease
export const glideBy = (h, px, ms = 1200) => h.eval(([d, t]) => new Promise((done) => {
  const from = window.scrollY, t0 = performance.now();
  const step = (now) => {
    const k = Math.min(1, (now - t0) / t);
    window.scrollTo(0, from + d * (k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2));
    if (k < 1) requestAnimationFrame(step); else done();
  };
  requestAnimationFrame(step);
}), [px, ms]);

// a field emptied as a person empties one: clicked into, everything selected, deleted
export async function empty(h, sel) {
  const b = await h.box(sel);
  await h.click(b.x + 20, b.y + 14, { ms: 10 });
  // Cmd + A reaches no field over the DevTools protocol on a Mac, so the field's own select() stands in for it
  await h.eval((q) => document.querySelector(q).select(), sel);
  await h.key('Backspace');
}
