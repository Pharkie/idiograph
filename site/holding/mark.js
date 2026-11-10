(() => {
'use strict';
const visit = () => {
  const held = new Map();
  return { getItem: (k) => (held.has(k) ? held.get(k) : null), setItem: (k, v) => { held.set(k, String(v)); } };
};
const sessionStorage = visit(), localStorage = visit();
const APP = 'idiograph';
const $ = () => ({ hidden: false });

const HOME_MARK_KEY = 'idiograph.homeMark';
const HOME_MARK_BOUNCE = (() => {
  const top = -26, ground = 18.8, rest = 12, tFirst = 0.526, squash = 0.22, squashTime = 0.05;
  const h0 = ground - top, h2 = ground - rest;
  const e = Math.pow(h2 / h0, 0.25), h1 = e * e * h0;
  const g = 8 * h1 / (tFirst * tFirst);
  const v1 = e * Math.sqrt(2 * g * h0), v2 = e * v1;
  return { top, ground, rest, tFirst, squash, squashTime, g, v1, v2,
    tFall: Math.sqrt(2 * h0 / g), tRise: Math.sqrt(2 * h2 / g) };
})();

function homeMarkDot(s) {
  const { top, ground, rest, g, tFall, tFirst, tRise, v1, v2, squash, squashTime } = HOME_MARK_BOUNCE;
  let y, shown = true;
  if (s < -tFall) { y = top; shown = false; }
  else if (s < 0) { const u = s + tFall; y = top + 0.5 * g * u * u; }
  else if (s < tFirst) y = ground - (v1 * s - 0.5 * g * s * s);
  else if (s < tFirst + tRise) { const u = s - tFirst; y = ground - (v2 * u - 0.5 * g * u * u); }
  else y = rest;
  let sq = 0;
  for (const [at, amt] of [[0, squash], [tFirst, squash * v2 / v1]]) {
    const d = Math.abs(s - at);
    if (d < squashTime) sq = Math.max(sq, amt * (1 - d / squashTime));
  }
  return { y, sx: 1 + sq, sy: 1 - sq, shown };
}

const HOME_MARK_ORDER_KEY = 'idiograph.homeMarkOrder';
const HOME_MARK_WAYS = ['spin', 'pong', 'pinball', 'anagram', 'football', 'kiss', 'race'];

function homeMarkNext(ways = HOME_MARK_WAYS, store = null, rand = Math.random) {
  try {
    const keep = store || localStorage;
    const held = JSON.parse(keep.getItem(HOME_MARK_ORDER_KEY) || 'null') || {};
    const last = ways.includes(held.last) ? held.last : null;
    let left = Array.isArray(held.left) ? held.left.filter((w, i, all) => ways.includes(w) && all.indexOf(w) === i) : [];
    if (!left.length) {
      left = ways.slice();
      for (let i = left.length - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [left[i], left[j]] = [left[j], left[i]]; }
      if (left[0] === last && left.length > 1) { const j = 1 + Math.floor(rand() * (left.length - 1)); [left[0], left[j]] = [left[j], left[0]]; }
    }
    const way = left.shift();
    keep.setItem(HOME_MARK_ORDER_KEY, JSON.stringify({ left, last: way }));
    return way;
  } catch { return ways[Math.floor(Math.random() * ways.length)]; }
}

function homeMarkPlay(which) {
  const root = document.documentElement;
  if (typeof which === 'string') {
    const old = document.querySelector('.wordmark .home-mark');
    if (old) { old.remove(); requestAnimationFrame(() => homeMarkPlay(which)); return; }
    root.classList.add('home-mark-due');
  }
  const due = root.classList.contains('home-mark-due');
  const still = () => root.classList.remove('home-mark-due');
  try { sessionStorage.setItem(HOME_MARK_KEY, '1'); } catch { }
  if (!due || APP !== 'idiograph' || window.matchMedia('(prefers-reduced-motion: reduce)').matches) { still(); return; }
  const box = document.querySelector('.wordmark .pe');
  const use = box && box.querySelector('.lockup use');
  const name = box && box.querySelector('.lockup > path');
  const stamp = box && box.querySelector('.pe-stamp');
  if (!use || !name || $('library').hidden) { still(); return; }
  const way = HOME_MARK_WAYS.includes(which) ? which : homeMarkNext();
  if (way === 'spin') homeMarkSpin(box, use, name, stamp, still);
  else homeMarkScene(way, box, use, name, stamp, still);
}

function homeMarkSpin(box, use, name, stamp, still) {
  const ctm = use.getScreenCTM(), from = box.getBoundingClientRect();
  const size = ctm ? ctm.a * Number(use.getAttribute('width') || 15) : 0;
  if (!size) { still(); return; }
  const k = size / 24, P = size * 16;
  const cx = ctm.e + size / 2, cy = ctm.f + size / 2, lock = use.ownerSVGElement.getBoundingClientRect();
  let under = box.closest('.wordmark');
  under = under && under.nextElementSibling;
  while (under && !under.getBoundingClientRect().height) under = under.nextElementSibling;
  const floor = under ? under.getBoundingClientRect().top : innerHeight;
  const room = { l: cx - 8, r: Math.min(innerWidth - 8, lock.right + 20) - cx, t: cy - 4, b: floor - cy - 6 };
  const D0 = 2;
  const at = (e, S0, R0, C, side) => {
    const S = 1 + (S0 - 1) * (1 - e), R = 5.5 + (R0 - 5.5) * (1 - e), phi = 1.5 * 2 * Math.PI * (1 - e);
    const x = C.x * (1 - e) + side * R * Math.cos(phi) * k * S, z = -side * R * Math.sin(phi) * k * S;
    return { S, phi, x, y: C.y * (1 - e) + 0.18 * z, z, tilt: -0.3 * (1 - e) * (1 - e) };
  };
  const reach = (S0, R0, C) => {
    const out = { l: 0, r: 0, t: 0, b: 0 };
    for (let i = 0; i <= 60; i++) {
      for (const side of [-1, 1]) {
        const p = at(i / 60, S0, R0, C, side), cp = Math.cos(p.phi), sp = Math.sin(p.phi), ct = Math.cos(p.tilt), st = Math.sin(p.tilt);
        for (const [u, v, w] of [[-3, -9.5, -1], [3, -9.5, -1], [-3, 9.5, -1], [3, 9.5, -1], [-3, -9.5, 1], [3, -9.5, 1], [-3, 9.5, 1], [3, 9.5, 1]]) {
          const X = u * k * p.S, Y = v * k * p.S, Z = w * D0 / 2 * k * p.S;
          const x1 = X * cp + Z * sp, z1 = -X * sp + Z * cp, y2 = Y * ct - z1 * st, z2 = Y * st + z1 * ct;
          const f = P / (P - (p.z + z2)), sx = (p.x + x1) * f, sy = (p.y + y2) * f;
          out.l = Math.max(out.l, -sx); out.r = Math.max(out.r, sx); out.t = Math.max(out.t, -sy); out.b = Math.max(out.b, sy);
        }
      }
    }
    return out;
  };
  const toward = (lo, hi) => Math.min(Math.max(0, lo), hi);
  const fit = (q) => {
    const S0 = 1.5 + 5.5 * q, R0 = 8 + 14 * q, o = reach(S0, R0, { x: 0, y: 0 });
    const C = { x: toward(o.l - room.l, room.r - o.r), y: toward(o.t - room.t, room.b - o.b) };
    const m = reach(S0, R0, C);
    return { S0, R0, C, fits: m.l <= room.l && m.r <= room.r && m.t <= room.t && m.b <= room.b };
  };
  let lo = 0, hi = 1;
  if (fit(1).fits) lo = 1;
  else for (let i = 0; i < 12; i++) { const q = (lo + hi) / 2; if (fit(q).fits) lo = q; else hi = q; }
  const { S0, R0, C: C0 } = fit(lo);
  const Z = Math.ceil(S0), kz = k * Z;
  const piece = (inner) => `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" style="position:absolute;left:0;top:0;overflow:visible">${inner}</svg>`;
  const FACES = { front: '--c-front', back: '--c-back', left: '--c-left', right: '--c-right', top: '--c-top', bottom: '--c-bottom' };
  const block = ([x0, y0, x1, y1]) => {
    const w = (x1 - x0) * kz, h = (y1 - y0) * kz, f = 'position:absolute;display:block;backface-visibility:hidden;';
    const face = (name, css) => `<span style="${f}background:var(${FACES[name]});box-shadow:0 0 0 0.6px var(${FACES[name]});opacity:var(--o, 1);${css}"></span>`;
    return `<span style="position:absolute;display:block;left:${x0 * kz}px;top:${y0 * kz}px;width:${w}px;height:${h}px;transform-style:preserve-3d">`
      + face('front', `left:0;top:0;width:${w}px;height:${h}px;transform:translateZ(calc(var(--d) / 2))`)
      + face('back', `left:0;top:0;width:${w}px;height:${h}px;transform:rotateY(180deg) translateZ(calc(var(--d) / 2))`)
      + face('right', `left:calc(${w / 2}px - var(--d) / 2);top:0;width:var(--d);height:${h}px;transform:rotateY(90deg) translateZ(${w / 2}px)`)
      + face('left', `left:calc(${w / 2}px - var(--d) / 2);top:0;width:var(--d);height:${h}px;transform:rotateY(-90deg) translateZ(${w / 2}px)`)
      + face('top', `left:0;top:calc(${h / 2}px - var(--d) / 2);width:${w}px;height:var(--d);transform:rotateX(90deg) translateZ(${h / 2}px)`)
      + face('bottom', `left:0;top:calc(${h / 2}px - var(--d) / 2);width:${w}px;height:var(--d);transform:rotateX(-90deg) translateZ(${h / 2}px)`)
      + '</span>';
  };
  const solid = (blocks) => `<span style="position:absolute;display:block;left:0;top:0;width:${24 * kz}px;height:${24 * kz}px;transform-style:preserve-3d">${blocks.map(block).join('')}</span>`;
  const cover = document.createElement('span');
  cover.className = 'home-mark';
  cover.setAttribute('aria-hidden', 'true');
  cover.style.cssText = `position:absolute;left:${ctm.e - from.left}px;top:${ctm.f - from.top}px;width:${size}px;height:${size}px;`
    + `perspective:${P}px;pointer-events:none;line-height:0`;
  cover.innerHTML = '<span class="spin" style="position:absolute;inset:0;transform-style:preserve-3d">'
    + solid([[3.5, 2.5, 5.5, 21.5], [5.5, 2.5, 9.5, 4.5], [5.5, 19.5, 9.5, 21.5]])
    + solid([[18.5, 2.5, 20.5, 21.5], [14.5, 2.5, 18.5, 4.5], [14.5, 19.5, 18.5, 21.5]]) + '</span>'
    + piece('<circle cx="12" cy="12" r="2.7" stroke="none" style="fill: var(--mark-dot, currentColor)"/>');
  const spin = cover.firstChild, [lb, rb] = spin.children, dot = cover.lastChild;
  let paper = 'transparent';
  for (let el = box; el && paper === 'transparent'; el = el.parentElement) {
    const c = getComputedStyle(el).backgroundColor;
    if (c && c !== 'transparent' && !/rgba\(.*,\s*0\)$/.test(c)) paper = c;
  }
  if (paper === 'transparent') paper = getComputedStyle(document.body).backgroundColor || 'white';
  const paint = (el, phi, tilt, ink) => {
    const cp = Math.cos(phi), sp = Math.sin(phi), ct = Math.cos(tilt), st = Math.sin(tilt);
    const normals = { front: [0, 0, 1], back: [0, 0, -1], left: [-1, 0, 0], right: [1, 0, 0], top: [0, -1, 0], bottom: [0, 1, 0] };
    for (const f of Object.keys(FACES)) {
      const [x, y, z] = normals[f];
      const z1 = -x * sp + z * cp, y2 = y * ct - z1 * st, z2 = y * st + z1 * ct;
      const lean = (1 - Math.max(0, z2)) * (0.5 + 0.16 * -y2), mix = 1 - ink * (1 - lean);
      el.style.setProperty(FACES[f], `color-mix(in srgb, currentColor ${(100 * (1 - mix)).toFixed(1)}%, ${paper})`);
    }
  };
  lb.style.transformOrigin = `${6.5 * kz}px ${12 * kz}px`;
  rb.style.transformOrigin = `${17.5 * kz}px ${12 * kz}px`;
  dot.style.transformOrigin = `${size / 2}px ${size / 2}px`;
  const land = 1.25, still2 = land + 0.15;
  const hit = still2 - HOME_MARK_BOUNCE.tFirst - HOME_MARK_BOUNCE.tRise;
  const stampAt = still2 + 0.1, stampFor = 0.35, end = stampAt + stampFor;
  const span = (t, a, b) => Math.min(1, Math.max(0, (t - a) / (b - a)));
  const place = (el, side, rest, e, depth, thud, fade) => {
    const { S, phi, x, y, z, tilt } = at(e, S0, R0, C0, side);
    el.style.transform = `translate3d(${12 * k + x - rest * kz}px, ${12 * k + y - 12 * kz}px, ${z}px) rotateX(${tilt * 180 / Math.PI}deg) rotateY(${phi * 180 / Math.PI}deg) scale3d(${S * thud / Z}, ${S * thud / Z}, ${S / Z})`;
    el.style.setProperty('--d', `${depth * kz}px`);
    el.style.setProperty('--o', fade.toFixed(3));
    paint(el, phi, tilt, 1);
  };
  const frame = (t) => {
    const kk = span(t, 0, land), e = 1 - Math.pow(1 - kk, 1.7);
    const th = span(t, land, still2), thud = th > 0 && th < 1 ? 1 - 0.06 * Math.sin(Math.PI * th) : 1;
    const depth = D0 * (1 - span(t, land - 0.4, land) ** 2 * (3 - 2 * span(t, land - 0.4, land)));
    const fade = 1 - Math.cos(kk * Math.PI / 2);
    place(lb, -1, 6.5, e, depth, thud, fade);
    place(rb, 1, 17.5, e, depth, thud, fade);
    const n = span(t, 0.85, land);
    name.style.opacity = String(n * n * (3 - 2 * n));
    if (stamp) {
      const s = span(t, stampAt, end);
      const down = 0.55, over = 0.93;
      const sc = s <= 0 ? 1.45 : s < down ? 1.45 - (1.45 - over) * Math.pow(s / down, 2)
        : over + (1 - over) * Math.sin(((s - down) / (1 - down)) * Math.PI / 2);
      stamp.style.opacity = String(Math.min(1, s / 0.15));
      stamp.style.scale = String(sc);
    }
    const d = homeMarkDot(t - hit);
    dot.style.opacity = d.shown ? fade.toFixed(3) : '0';
    dot.style.transform = `translateY(${(d.y - 12) * k}px) scale(${d.sx}, ${d.sy})`;
  };
  try { frame(0); box.appendChild(cover); } catch { cover.remove(); still(); return; }
  const done = () => {
    cover.remove(); name.style.opacity = '';
    if (stamp) { stamp.style.opacity = ''; stamp.style.scale = ''; }
    still();
  };
  let t0 = null;
  const step = (now) => {
    if (t0 === null) t0 = now;
    const t = (now - t0) / 1000;
    if (t >= end || !cover.isConnected) { done(); return; }
    try { frame(t); } catch { done(); return; }
    requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

const HM = (() => {
  const m = 15 / 24;
  return { m, g: HOME_MARK_BOUNCE.g * m, ground: HOME_MARK_BOUNCE.ground * m, mid: 7.5, r: 2.7 * m,
    lb: { x: 6.5 * m }, rb: { x: 17.5 * m }, nameX: 19.2, nameY: 12.5 };
})();
const hmSpan = (t, a, b) => Math.min(1, Math.max(0, (t - a) / (b - a)));
const hmSmooth = (k) => k * k * (3 - 2 * k);
const hmOut = (k) => 1 - Math.pow(1 - k, 3);
const hmInOut = (k) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2);
const hmLerp = (a, b, k) => a + (b - a) * k;
const hmArc = (k) => Math.sin(Math.PI * Math.min(1, Math.max(0, k)));
const hmBump = (t, a, b) => (t > a && t < b ? Math.sin(Math.PI * (t - a) / (b - a)) : 0);
const hmSpring = (k) => (k <= 0 ? 1 : k >= 1 ? 0 : Math.exp(-4 * k) * Math.cos(2.5 * Math.PI * k) * (1 - k));

function hmHome(x0, y0, vx = 0, vy = 0, w = 14, z = 0.8) {
  const wd = w * Math.sqrt(1 - z * z), zw = z * w;
  const off = (d0, v0, s) => Math.exp(-zw * s) * (d0 * Math.cos(wd * s) + ((v0 + zw * d0) / wd) * Math.sin(wd * s));
  const pos = (s) => (s <= 0 ? [x0, y0] : [HM.mid + off(x0 - HM.mid, vx, s), HM.mid + off(y0 - HM.mid, vy, s)]);
  let rest = 0;
  while (rest < 3 && Math.hypot(...pos(rest).map((v) => v - HM.mid)) + Math.hypot(...pos(rest + 0.05).map((v) => v - HM.mid)) > 0.1) rest += 0.01;
  return { rest, at(s) {
    const [x, y] = pos(s), [x1, y1] = pos(s + 0.01), v = Math.hypot(x1 - x, y1 - y) / 0.01;
    const st = Math.min(0.14, v / 600);
    return { x, y, a: v > 1 ? Math.atan2(y1 - y, x1 - x) * 180 / Math.PI : 0, sx: 1 + st, sy: 1 - st * 0.6 };
  } };
}
const hmKeys = (t, keys) => {
  if (t <= keys[0][0]) return keys[0][1];
  for (let j = 0; j < keys.length - 1; j++) {
    if (t < keys[j + 1][0]) return hmLerp(keys[j][1], keys[j + 1][1], hmInOut(hmSpan(t, keys[j][0], keys[j + 1][0])));
  }
  return keys[keys.length - 1][1];
};
const hmLob = (x0, y0, x1, y1, T, s) => {
  const vy = (y1 - y0 - 0.5 * HM.g * T * T) / T, u = Math.min(T, Math.max(0, s));
  return { x: hmLerp(x0, x1, u / T), y: y0 + vy * u + 0.5 * HM.g * u * u };
};
const hmTouch = (t, at, amt = 0.22) => {
  let q = 0;
  for (const a of at) { const d = Math.abs(t - a); if (d < 0.06) q = Math.max(q, amt * (1 - d / 0.06)); }
  return q;
};
const HM_STAMP = { for: 0.35, down: 0.55 };
const HM_PAUSE = 1.0;
function hmStamp(stamp, t, land) {
  if (!stamp) return;
  const { down } = HM_STAMP, over = 0.93, q = hmSpan(t, land - down * HM_STAMP.for, land + (1 - down) * HM_STAMP.for);
  const sc = q <= 0 ? 1.45 : q < down ? 1.45 - (1.45 - over) * Math.pow(q / down, 2)
    : over + (1 - over) * Math.sin(((q - down) / (1 - down)) * Math.PI / 2);
  stamp.style.opacity = String(Math.min(1, q / 0.15));
  stamp.style.scale = String(sc);
}

const HOME_MARK_SCENES = {
  pong: { stamp: 2.7, frame(t, S, K) {
    const { lb, rb, dot } = S;
    lb.o = rb.o = dot.o = hmSpan(t, 0, 0.12);
    S.name = hmSmooth(hmSpan(t, 1.85, 2.45));
    const L = Math.max(-11, 6.4 - K.room), R = 14, cL = L + 1.06, cR = R - 1.06;
    const top = -4, bottom = 19;
    const shots = [[0.38, HM.mid, HM.mid], [0.62, cR, 3, bottom], [0.9, cL, 9], [1.14, cR, 17, top], [1.4, cL, 2, bottom],
      [1.64, cR, 6], [1.88, cL, 16]];
    const last = shots[shots.length - 1], home = 2.5;
    if (t < shots[0][0]) { dot.x = HM.mid; dot.y = HM.mid; }
    else if (t >= last[0]) {
      const k = 1 - Math.pow(1 - hmSpan(t, last[0], home), 3);
      dot.x = hmLerp(last[1], HM.mid, k); dot.y = hmLerp(last[2], HM.mid, k);
    } else {
      const i = shots.findIndex((s, j) => t >= s[0] && t < shots[j + 1][0]);
      const [a, x0, y0, wall] = shots[i], [b, x1, y1] = shots[i + 1], k = (t - a) / (b - a);
      dot.x = hmLerp(x0, x1, k);
      if (wall === undefined) dot.y = hmLerp(y0, y1, k);
      else { const y = hmLerp(y0, 2 * wall - y1, k); dot.y = (wall > HM.mid ? y > wall : y < wall) ? 2 * wall - y : y; }
    }
    const LK = [[0.62, HM.mid], [0.79, 13.5], [0.89, 9.5], [0.95, 9.5], [1.3, 2.5], [1.4, 2], [1.66, 2], [1.74, 3],
      [1.87, 14.5], [1.92, 14.5], [2.15, HM.mid]];
    const RK = [[0.38, HM.mid], [0.58, 3.5], [0.62, 3], [0.75, 3], [0.95, 2], [1.02, 2.5], [1.13, 15.5], [1.18, 15.5],
      [1.5, 6.5], [1.64, 6], [1.8, 9], [2.1, HM.mid]];
    lb.x = t < 1.9 ? hmLerp(HM.lb.x, L, hmOut(hmSpan(t, 0.12, 0.32))) : hmLerp(L, HM.lb.x, hmInOut(hmSpan(t, 2.15, 2.5)));
    rb.x = t < 1.9 ? hmLerp(HM.rb.x, R, hmOut(hmSpan(t, 0.12, 0.32))) : hmLerp(R, HM.rb.x, hmInOut(hmSpan(t, 2.1, 2.45)));
    lb.y = hmKeys(t, LK); rb.y = hmKeys(t, RK);
  } },

  pinball: { letters: true, stamp: 3.28,
    extra: '<g stroke="currentColor" stroke-width="0.55"><circle r="1.7"/><circle r="1.7"/><circle r="1.7"/></g>',
    init(K) {
      const wide = K.room >= 10, A0 = wide ? 38 : 58, D = 5.5, off = HM.r + 0.625, py = 6, cx = 5.5, len = 10.625;
      const reach = len * Math.cos(A0 * Math.PI / 180);
      K.A0 = A0; K.py = py;
      K.pl = wide ? cx - 3.8 - reach : cx - 1.6 - reach; K.pr = wide ? cx + 1.7 + reach : cx + 3.9 + reach;
      K.on = (side, a, d = D) => {
        const c = Math.cos(a * Math.PI / 180), s = Math.sin(a * Math.PI / 180);
        return side < 0 ? [K.pl + d * c + off * s, py + d * s - off * c] : [K.pr - d * c - off * s, py + d * s - off * c];
      };
      K.bumpers = [[-2.25, -3.5], [13.25, -3.5], [6.5, -9.5]];
      const touch = 1.7 + 0.275 + HM.r + 0.35;
      const meet = ([x, y], [bx, by]) => { const d = Math.hypot(bx - x, by - y); return [bx - (bx - x) / d * touch, by - (by - y) / d * touch]; };
      K.roll = { d0: 1.4, d1: len - HM.r - 0.3, from: 0.3 };
      K.roll.a = (5 / 7) * HM.g * Math.sin(A0 * Math.PI / 180);
      K.roll.to = K.roll.from + Math.sqrt(2 * (K.roll.d1 - K.roll.d0) / K.roll.a);
      const up = -20, shot = 0.13, down = 0.23;
      const launchL = K.on(-1, up), launchR = K.on(1, up), restL = K.on(-1, A0), restR = K.on(1, A0);
      const hitR = meet(launchL, K.bumpers[1]), hitL = meet(launchR, K.bumpers[0]);
      const launch0 = K.on(-1, up, K.roll.d1), hit0 = meet(launch0, K.bumpers[1]);
      const top = [K.bumpers[2][0], K.bumpers[2][1] + touch];
      const l0 = K.roll.to - 0.13, t1 = l0 + 0.19, h1 = t1 + shot, land2 = h1 + down, t2 = land2 + 0.19, h2 = t2 + shot, land3 = h2 + down;
      K.nodip = l0;
      const t3 = land3 + 0.19, h3 = t3 + shot, land4 = h3 + down, t4 = land4 + 0.19;
      const h4 = t4 + Math.sqrt(2 * (launchR[1] - top[1]) / HM.g);
      K.lands = { left: [l0, land3], right: [land2, land4] };
      K.hits = [h1, h2, h3, h4];
      K.struck = [1, 0, 1, 2];
      K.lamps = [[5, 6], [0, 1], [7, 8], [2, 3, 4]];
      K.legs = [[t1, h1, launch0, hit0, 'shot'], [h1, land2, hit0, restR, 'fall'], [t2, h2, launchR, hitL, 'shot'],
        [h2, land3, hitL, restL, 'fall'], [t3, h3, launchL, hitR, 'shot'], [h3, land4, hitR, restR, 'fall'],
        [t4, h4, launchR, top, 'shot']];
      K.up = up;
      K.home = h4;
      K.glide = hmHome(top[0], top[1]);
      K.bumperEls = [...K.extra.querySelectorAll('circle')];
    },
    frame(t, S, K) {
      const { lb, rb, dot } = S, A0 = K.A0;
      const turn = (lands) => {
        let a = A0;
        for (const l of lands) {
          const s = t - l;
          if (s < 0) break;
          const dip = l === K.nodip ? 0 : 8;
          a = s < 0.11 ? hmLerp(A0, A0 + dip, hmOut(s / 0.11)) : s < 0.13 ? A0 + dip
            : s < 0.19 ? hmLerp(A0 + dip, K.up, hmOut((s - 0.13) / 0.06)) : s < 0.27 ? K.up
            : s < 0.5 ? hmLerp(K.up, A0, hmInOut((s - 0.27) / 0.23)) : A0;
        }
        return a;
      };
      const aL = turn(K.lands.left), aR = turn(K.lands.right);
      S.letters.forEach((l, i) => {
        const n = K.lamps.findIndex((set) => set.includes(i));
        l.o = t >= K.hits[n] ? 1 : 0.26 * hmSmooth(hmSpan(t, 0, 0.3));
      });
      const go = hmSpan(t, K.home + 0.05, K.home + 0.3);
      K.bumperEls.forEach((c, i) => {
        let p = 0;
        K.struck.forEach((b, j) => { const s = t - K.hits[j]; if (b === i && s >= 0 && s < 0.4) p = Math.max(p, Math.exp(-s / 0.07)); });
        const [x, y] = K.bumpers[i];
        c.setAttribute('transform', `translate(${x} ${y}) scale(${(1 + 0.15 * p) * (1 - 0.4 * go)})`);
        c.setAttribute('opacity', String(Math.min(1, 0.35 + 0.6 * p) * hmSmooth(hmSpan(t, 0.25, 0.5)) * (1 - go)));
      });
      const inAt = K.home + 0.12, inBy = K.home + 0.27;
      const pose = (b, side, a, last) => {
        const early = t < K.home;
        const go = early ? 1 : 1 - hmInOut(hmSpan(t, inAt, inBy));
        const lie = early ? 1 : 1 - hmInOut(hmSpan(t, K.home - 0.08 + last, K.home + 0.06 + last));
        const far = (side < 0 ? K.pl : K.pr) - 1.25 * side;
        const lean = 6 * hmBump(t, inBy - 0.05, inBy + 0.13), thud = 1 - 0.05 * hmBump(t, inBy, inBy + 0.14);
        Object.assign(b, { px: 1.25 * side, py: 5.3125, r: -side * ((90 + a) * lie - lean), o: hmSpan(t, 0, 0.15),
          x: hmLerp(side < 0 ? HM.lb.x : HM.rb.x, hmLerp(side > 0 ? Math.min(far, 13.4) : far, far, lie), go),
          y: hmLerp(HM.mid, K.py - 5.3125, lie), sx: thud, sy: thud });
      };
      pose(lb, -1, aL, 0);
      pose(rb, 1, aR, 0.06);
      dot.o = hmSpan(t, 0, 0.15);
      if (t >= K.home) {
        const d = K.glide.at(t - K.home), q = hmTouch(t, [K.home], 0.18);
        Object.assign(dot, { x: d.x, y: d.y, a: q ? 0 : d.a, sx: d.sx - q, sy: d.sy + q });
        return;
      }
      const leg = K.legs.find(([a, b]) => t >= a && t < b);
      if (leg) {
        const [a, b, p0, p1, kind] = leg, p = hmLob(p0[0], p0[1], p1[0], p1[1], b - a, t - a);
        const v = hmLob(p0[0], p0[1], p1[0], p1[1], b - a, t - a + 0.01);
        Object.assign(dot, { x: p.x, y: p.y, a: Math.atan2(v.y - p.y, v.x - p.x) * 180 / Math.PI });
        if (kind === 'shot') {
          const s = 0.1 * hmArc((t - a) / (b - a)), q = hmTouch(t, [a], 0.22) + hmTouch(t, [b], 0.24);
          dot.sx = 1 + s - q; dot.sy = 1 - s * 0.6 + q;
        } else {
          const land = hmTouch(t, [b], 0.22);
          dot.a = K.lands.right.includes(b) ? -A0 : A0; dot.sx = 1 + land; dot.sy = 1 - land;
        }
        return;
      }
      if (t < K.roll.to) {
        const u = Math.max(0, t - K.roll.from), [x, y] = K.on(-1, A0, K.roll.d0 + 0.5 * K.roll.a * u * u);
        Object.assign(dot, { x, y, a: A0, sx: 1, sy: 1 });
        return;
      }
      const onRight = K.lands.right.some((x) => t >= x && t < x + 0.19);
      const l = (onRight ? K.lands.right : K.lands.left).find((x) => t >= x && t < x + 0.19);
      const [x, y] = K.on(onRight ? 1 : -1, onRight ? aR : aL, !onRight && l === K.nodip ? K.roll.d1 : undefined);
      const q = l === undefined ? 0 : (l > K.lands.left[0] ? hmTouch(t, [l], 0.22) : 0) + 0.2 * hmBump(t, l + 0.12, l + 0.2);
      Object.assign(dot, { x, y, a: onRight ? -aR : aL, sx: 1 + q, sy: 1 - q });
    } },

  anagram: { letters: true, stamp: 5.25,
    init(K) {
      const order = [4, 3, ' ', 5, 6, 7, 0, 1, ' ', 8, 2], at = {};
      K.space = K.room < 10 ? 8 : 10;
      let x = K.L[1].x1 + K.space, prev = null;
      for (const c of order) {
        if (c === ' ') x += K.space;
        else { if (typeof prev === 'number') x += c === prev + 1 ? K.L[c].x0 - K.L[prev].x1 : 3; at[c] = x; x += K.L[c].x1 - K.L[c].x0; }
        prev = c;
      }
      K.start = K.L.map((l, i) => at[i]);
      K.mid = K.start.slice();
      K.mid[4] = K.start[3] + (K.L[3].x1 - K.L[3].x0) + (K.L[4].x0 - K.L[3].x1);
      const rShift = K.mid[4] + (K.L[4].x1 - K.L[4].x0) + (K.L[5].x0 - K.L[4].x1) - K.start[5];
      for (const i of [5, 6, 7]) K.mid[i] = K.start[i] + rShift;
      K.glide = hmHome(HM.mid, -6);
    },
    frame(real, S, K) {
      const P0 = 0.37, P1 = P0 + HM_PAUSE, t = real < P0 ? real : real < P1 ? P0 : real - HM_PAUSE;
      const under = K.room < 10, side = under ? 1 : -1;
      const { lb, rb, dot } = S, Ls = S.letters, g = HM.g, HOLD = 4.6, LIFT = 15 * side, LET = 12.8 * side;
      const along = (i, keys) => { Ls[i].dx = hmKeys(t, keys) - K.L[i].x0; };
      const fin = (i) => K.L[i].x0;
      Ls.forEach((l) => { l.o = hmSmooth(hmSpan(t, 0, 0.25)); });
      const toss = Math.sqrt(2 * Math.abs(LET) / g), dropAt = under ? toss : (-40 + Math.sqrt(1600 - 2 * g * LET)) / g;
      const fall = (at) => (under ? LET * Math.pow(1 - Math.min(1, (t - at) / toss), 2)
        : Math.min(0, LET + 40 * (t - at) + 0.5 * g * (t - at) * (t - at)));
      for (const i of [0, 1]) {
        along(i, [[1.0, K.start[i]], [1.5, fin(i)]]);
        Ls[i].dy = hmKeys(t, [[0.86, 0], [1.0, LIFT], [1.5, LIFT], [1.62, 0]]);
        Ls[i].sy = 1 - 0.06 * hmBump(t, 0.78, 0.9) - 0.1 * hmBump(t, 1.6, 1.72);
      }
      along(4, [[2.12, K.start[4]], [2.4, K.mid[4]], [2.8, K.mid[4]], [3.1, fin(4)]]);
      Ls[4].dy = t < 2.5 ? hmKeys(t, [[2.0, 0], [2.12, LIFT], [2.4, LIFT], [2.5, LET]]) : fall(2.5);
      Ls[4].sy = 1 - 0.06 * hmBump(t, 1.9, 2.02) - 0.06 * hmBump(t, 2.48 + dropAt, 2.6 + dropAt);
      for (const i of [5, 6, 7]) along(i, [[2.12, K.start[i]], [2.38, K.mid[i]], [2.8, K.mid[i]], [3.1, fin(i)]]);
      along(3, [[2.8, K.start[3]], [3.1, fin(3)]]);
      along(8, [[2.8, K.start[8]], [3.1, fin(8)]]);
      along(2, [[2.77, K.start[2]], [3.17, fin(2)]]);
      Ls[2].dy = t < 3.25 ? hmKeys(t, [[2.65, 0], [2.77, LIFT], [3.17, LIFT], [3.25, LET]]) : fall(3.25);
      Ls[2].sy = 1 - 0.06 * hmBump(t, 2.55, 2.67) - 0.08 * hmBump(t, 3.23 + dropAt, 3.35 + dropAt);
      const grip = (i) => HM.nameX + K.L[i].x0 + Ls[i].dx - HOLD, gripR = (i) => HM.nameX + K.L[i].x1 + Ls[i].dx + HOLD;
      const at = (pos) => HM.nameX + pos, w = (i) => K.L[i].x1 - K.L[i].x0;
      const hop = (k, x0, y0, x1, y1, top) => [hmLerp(x0, x1, hmInOut(hmSpan(k, 0.2, 0.8))),
        k < 0.5 ? hmLerp(y0, top, hmSmooth(hmSpan(k, 0, 0.3))) : hmLerp(top, y1, hmSmooth(hmSpan(k, 0.7, 1)))];
      const over = HM.mid + 15 * side;
      const tight = (a, b) => 0.4 * (hmSmooth(hmSpan(t, a, a + 0.06)) - hmSmooth(hmSpan(t, b, b + 0.06)));
      lb.o = rb.o = hmSpan(t, 0.05, 0.15);
      lb.py = rb.py = 5.3125;
      const rise = Math.sqrt(2 * 14 / g), landed = under ? 0.05 + rise : 0.05 + Math.sqrt(2 * (HM.mid + 6) / g);
      const fallIn = under ? HM.mid + 14 * Math.pow(1 - hmSpan(t, 0.05, 0.05 + rise), 2)
        : Math.min(HM.mid, -6 + 0.5 * g * Math.pow(Math.max(0, t - 0.05), 2));
      const shake = t > 0.38 && t < 0.56 ? 6 * Math.sin(4 * Math.PI * (t - 0.38) / 0.18) * (1 - (t - 0.38) / 0.18) : 0;
      const gStart = at(K.start[4]) - HOLD;
      if (t < 0.6) { lb.x = gStart; lb.y = fallIn; lb.r = -Math.abs(shake); }
      else if (t < 0.85) { const k = hmSpan(t, 0.6, 0.85); [lb.x, lb.y] = hop(k, gStart, HM.mid, HM.lb.x, HM.mid, HM.mid - 5); lb.r = -6 * hmArc(k); }
      else if (t < 1.75) { lb.x = HM.lb.x; lb.y = HM.mid; }
      else if (t < 1.95) { const k = hmSpan(t, 1.75, 1.95); [lb.x, lb.y] = hop(k, HM.lb.x, HM.mid, gStart, HM.mid, over); lb.r = 6 * hmArc(k); }
      else if (t < 2.5) { lb.x = grip(4) + tight(1.94, 2.44); lb.y = HM.mid + Ls[4].dy; lb.r = 5 * hmArc(hmSpan(t, 2.12, 2.4)); }
      else { const k = hmSpan(t, 2.5, 2.9); [lb.x, lb.y] = hop(k, at(K.mid[4]) - HOLD, HM.mid + LET, HM.lb.x, HM.mid, over); lb.r = -7 * hmArc(k); }
      const iStart = at(K.start[2] + w(2)) + HOLD, dStart = at(K.start[1] + w(1)) + HOLD, dEnd = at(K.L[1].x1) + HOLD;
      if (t < 0.6) { rb.x = iStart; rb.y = fallIn; rb.r = Math.abs(shake); }
      else if (t < 0.8) { const k = hmSpan(t, 0.6, 0.8); [rb.x, rb.y] = hop(k, iStart, HM.mid, dStart, HM.mid, over); rb.r = -6 * hmArc(k); }
      else if (t < 1.68) { rb.x = gripR(1) - tight(0.8, 1.62); rb.y = HM.mid + Ls[1].dy; rb.r = -5 * hmArc(hmSpan(t, 1.0, 1.5)); }
      else if (t < 1.98) { const k = hmSpan(t, 1.68, 1.98); [rb.x, rb.y] = hop(k, dEnd, HM.mid, iStart, HM.mid, over); rb.r = 6 * hmArc(k); }
      else if (t < 3.3) {
        rb.x = gripR(2) - tight(2.58, 3.19); rb.y = HM.mid + (t < 3.25 ? Ls[2].dy : LET) - (t < 2.6 ? 0.6 * hmBump(t, 2.2, 2.5) : 0);
        rb.r = -5 * hmArc(hmSpan(t, 2.77, 3.17));
      } else { const k = hmSpan(t, 3.3, 3.7); [rb.x, rb.y] = hop(k, at(K.L[2].x1) + HOLD, HM.mid + LET, HM.rb.x, HM.mid, over); rb.r = -7 * hmArc(k); }
      const drop0 = 0.16 * hmBump(real, landed, landed + 0.14);
      const homeL = t > 2.9 ? 0.12 * hmSpring(hmSpan(t, 2.9, 3.15)) : 0, homeR = t > 3.7 ? 0.12 * hmSpring(hmSpan(t, 3.7, 3.95)) : 0;
      lb.sy = 1 - drop0 - 0.1 * hmBump(t, 0.52, 0.62) - 0.1 * hmBump(t, 0.83, 0.93) - 0.1 * hmBump(t, 1.67, 1.77)
        - 0.1 * hmBump(t, 1.93, 2.03) - 0.12 * hmBump(t, 2.88, 2.98) + homeL;
      lb.sx = 1 - homeL;
      rb.sy = 1 - drop0 - 0.12 * hmBump(t, 0.52, 0.62) - 0.1 * hmBump(t, 0.78, 0.86) - 0.1 * hmBump(t, 1.6, 1.7)
        - 0.1 * hmBump(t, 1.96, 2.06) - 0.12 * hmBump(t, 3.68, 3.78) + homeR;
      rb.sx = 1 - homeR;
      const readL = hmBump(real, P0 + 0.1, P1 - 0.15), readR = hmBump(real, P0 + 0.22, P1 - 0.05);
      lb.r += 4 * readL * readL; rb.r -= 4 * readR * readR;
      lb.sy -= 0.04 * readL; rb.sy -= 0.04 * readR;
      dot.o = hmSpan(t, 3.55, 3.63);
      Object.assign(dot, K.glide.at(t - 3.55));
    } },

  football: { stamp: 3.45,
    init(K) {
      K.Lp = Math.max(-14, 9.2 - K.room); K.Rp = 13; K.footL = K.Lp + 1.06; K.footR = K.Rp - 1.06;
      K.b = { k1: 0.55, t1: 1.0, k2: 1.25, head: 1.75, t2: 2.2, back: [2.3, 2.48], k3: 2.6, mid: 3.15 };
      K.chipX = K.footR - 2.4;
      K.jump = 1.4;
      K.headAt = [K.Lp, HM.mid + 5.3125 - K.jump - 11.25 - HM.r];
      const T = K.b.mid - K.b.k3, a = hmLob(0, HM.ground, 0, HM.mid, T, T - 0.01), b = hmLob(0, HM.ground, 0, HM.mid, T, T);
      K.trap = hmHome(HM.mid, HM.mid, 0, (b.y - a.y) / 0.01, 40, 0.9);
    },
    frame(t, S, K) {
      const { lb, rb, dot } = S, { Lp, Rp, footL, footR, b: B } = K, G = HM.ground;
      lb.o = rb.o = dot.o = hmSpan(t, 0, 0.25);
      S.name = hmSmooth(hmSpan(t, 0.2, 3.0));
      const kick = (k, w = 20) => (t < k - 0.22 || t > k + 0.3 ? 0 : t < k - 0.04 ? -w * hmSmooth(hmSpan(t, k - 0.22, k - 0.04))
        : t < k ? hmLerp(-w, 12, hmSpan(t, k - 0.04, k)) : 12 * hmSpring(hmSpan(t, k, k + 0.3)));
      const h = B.head, nod = t < h - 0.24 || t > h + 0.4 ? 0 : t < h - 0.04 ? -12 * hmSmooth(hmSpan(t, h - 0.24, h - 0.04))
        : t < h + 0.04 ? hmLerp(-12, 10, hmSpan(t, h - 0.04, h + 0.04)) : 10 * hmSpring(hmSpan(t, h + 0.04, h + 0.4));
      lb.py = rb.py = 5.3125;
      lb.r = kick(B.k1) + nod; rb.r = -kick(B.k2, 12) - kick(B.k3, 12);
      const lift = t > h - 0.16 && t < h + 0.16 ? -K.jump * Math.sin(Math.PI * (t - h + 0.16) / 0.32) : 0;
      const ready = -1.1 * (hmArc(hmSpan(t, 0.12, 0.27)) + hmArc(hmSpan(t, 0.27, 0.42)));
      const take = (k) => 0.1 * hmBump(t, k, k + 0.16);
      const tap = 6 * hmBump(t, B.back[0] - 0.08, B.back[0] + 0.08);
      rb.r -= tap;
      const homeL = hmSpan(t, 2.65, 3.2), homeR = hmSpan(t, 2.75, 3.3);
      lb.x = hmLerp(Lp, HM.lb.x, hmInOut(homeL)); rb.x = hmLerp(Rp, HM.rb.x, hmInOut(homeR));
      lb.y = HM.mid + lift - 1.2 * Math.abs(Math.sin(2 * Math.PI * homeL));
      rb.y = HM.mid + ready - 1.2 * Math.abs(Math.sin(2 * Math.PI * homeR));
      const thudL = 0.05 * hmBump(t, 3.2, 3.35), thudR = 0.05 * hmBump(t, 3.3, 3.45);
      lb.sy = 1 - 0.12 * hmBump(t, h - 0.26, h - 0.14) - 0.08 * hmBump(t, h + 0.14, h + 0.28) - thudL; lb.sx = 1 - thudL;
      rb.sy = 1 - take(B.t1) - take(B.t2) - thudR; rb.sx = 1 - thudR;
      let q = 0;
      if (t < B.k1) { dot.x = footL; dot.y = G; }
      else if (t < B.k2) { const p = hmLob(footL, G, footR, G, B.t1 - B.k1, t - B.k1); dot.x = p.x; dot.y = p.y; }
      else if (t < B.head) { const p = hmLob(footR, G, K.headAt[0], K.headAt[1], B.head - B.k2, t - B.k2); dot.x = p.x; dot.y = p.y; }
      else if (t < B.back[0]) { const p = hmLob(K.headAt[0], K.headAt[1], footR, G, B.t2 - B.head, t - B.head); dot.x = p.x; dot.y = p.y; }
      else if (t < B.k3) {
        dot.x = hmLerp(footR, K.chipX, hmOut(hmSpan(t, B.back[0], B.back[1]))); dot.y = G;
      } else if (t < B.mid) {
        dot.x = hmLerp(K.chipX, HM.mid, Math.sin(hmSpan(t, B.k3, B.mid) * Math.PI / 2));
        dot.y = hmLob(K.chipX, G, HM.mid, HM.mid, B.mid - B.k3, t - B.k3).y;
      } else { const d = K.trap.at(t - B.mid); dot.x = d.x; dot.y = d.y; }
      q += hmTouch(t, [B.k1, B.t1, B.k2, B.head, B.t2, B.back[0], B.k3], 0.2) + hmTouch(t, [B.mid], 0.14);
      dot.sx = 1 + q; dot.sy = 1 - q;
    } },

  kiss: { stamp: 2.9,
    init(K) {
      K.tip = (r) => { const a = r * Math.PI / 180; return [1.875 * Math.cos(a) + 10.625 * Math.sin(a), 1.875 * Math.sin(a) - 10.625 * Math.cos(a)]; };
      K.lean = 10;
      K.base = HM.mid - HM.r + 0.15 - K.tip(K.lean)[0];
      K.lips = HM.mid + 5.3125 + K.tip(K.lean)[1];
      K.glide = hmHome(HM.mid, -4); K.up = Math.sqrt(2 * (K.lips + 4) / HM.g);
    },
    frame(t, S, K) {
      const { lb, rb, dot } = S, pull = 1.4;
      lb.o = rb.o = dot.o = hmSpan(t, 0, 0.2);
      S.name = hmSmooth(hmSpan(t, 0.2, 2.6));
      let d;
      if (t < 0.55) d = -0.3 * hmBump(t, 0.25, 0.5);
      else if (t < 0.65) d = -0.25 * hmSmooth(hmSpan(t, 0.55, 0.65));
      else if (t < 0.9) d = hmLerp(-0.25, 0.8, hmOut(hmSpan(t, 0.65, 0.9)));
      else if (t < 1.0) d = 0.8 + 0.06 * Math.sin(2 * Math.PI * 14 * (t - 0.9));
      else if (t < 1.5) d = 0.8 * hmSpring(hmSpan(t, 1.0, 1.35));
      else if (t < 1.6) d = -0.3 * hmSmooth(hmSpan(t, 1.5, 1.6));
      else if (t < 1.95) { const k = hmSpan(t, 1.6, 1.95); d = hmLerp(-0.3, pull, hmInOut(k)) + 0.12 * k * Math.sin(2 * Math.PI * 16 * (t - 1.6)); }
      else d = null;
      lb.py = rb.py = 5.3125;
      if (d !== null) {
        lb.x = K.base - d; rb.x = 2 * HM.mid - lb.x;
        lb.r = K.lean * (1 - 0.5 * Math.max(0, d) / pull) + 2 * hmBump(t, 0.25, 0.5); rb.r = -lb.r;
        lb.sy = rb.sy = 1 - 0.08 * hmBump(t, 1.5, 1.66);
        const [tx, ty] = K.tip(lb.r), gap = 2 * (HM.mid - (lb.x + tx));
        dot.y = HM.mid + 5.3125 + ty;
        dot.sx = Math.max(0.7, (gap + 0.3) / (2 * HM.r)); dot.sy = 1 / Math.sqrt(dot.sx);
      } else {
        const k = hmSpan(t, 1.95, 2.4), from = K.base - pull, spring = hmSpring(k);
        lb.x = HM.lb.x + (from - HM.lb.x) * spring; rb.x = 2 * HM.mid - lb.x;
        lb.r = K.lean * 0.5 * spring; rb.r = -lb.r;
        const top = 1.95 + K.up;
        if (t < top) {
          const u = top - t, s = 1 - hmSpan(t, 1.95, 2.08);
          dot.y = -4 + 0.5 * HM.g * u * u; dot.sx = 1 - 0.2 * s; dot.sy = 1 + 0.3 * s;
        } else { const p = K.glide.at(t - top); dot.y = p.y; dot.a = p.a; dot.sx = p.sx; dot.sy = p.sy; }
      }
    } },

  race: { letters: true,
    init(K) {
      const g = HM.g, shelf = 2.5 - 5.3125 - 0.625, half = 1.875;
      const H = 106.67, R = 68.8, O = 45.2, D = 26.3, G = 57.9, I2 = 36.15;
      const V = Math.max(260, (K.winR + half + 0.6 - 118) / 0.65), from = K.winR + 2.4 + V / 30, take = 118;
      const run = (from - take) / V, T0 = run + 0.34, lag = 0.3;
      const over = K.bars.filter((b) => b[2] > take - 4).reduce((y, b) => Math.max(y, b[3]), -Infinity);
      const low = HM.mid + Math.max(0, over + 8.5 / K.unit + 6.8 - HM.mid);
      const leg = (kind, a, b, x0, y0, x1, y1) => [kind, a, b, x0, y0, x1, y1];
      K.right = { lean: 9, legs: [leg('run', 0, run, from, low, take, low), leg('leap', run, T0, take, low, H, shelf),
        leg('leap', T0 + 0.03, T0 + 0.35, H, shelf, R, shelf), leg('leap', T0 + 0.38, T0 + 0.64, R, shelf, O, shelf),
        leg('leap', T0 + 0.67, T0 + 0.91, O, shelf, D, shelf), leg('home', T0 + 0.94, T0 + 1.28, D, shelf, HM.rb.x, HM.mid)],
      stones: [8, 5, 3, 1] };
      K.left = { lean: 13, legs: [leg('run', lag, lag + run, from, low, take, low), leg('leap', lag + run, T0 + lag, take, low, H, shelf),
        leg('leap', T0 + lag + 0.03, T0 + 0.7, H, shelf, G, shelf), leg('leap', T0 + 0.73, T0 + 0.97, G, shelf, I2, shelf),
        leg('home', T0 + 1.0, T0 + 1.4, I2, shelf, HM.lb.x, HM.mid)], stones: [8, 4, 2] };
      const e = 0.84, gb = 1.75 * 1.75 * g, arm = 2.5 * HM.m - HM.r, band = 3.5 * HM.m, xG = 57.6, yG = 0.837, xA = 9.8, top = -10.5;
      const upA = Math.sqrt(2 * gb * (arm - top)), upG = Math.sqrt(2 * gb * (yG - arm) + (upA / e) ** 2);
      const hits = [[xG, yG, upG], [xA, arm, upA]];
      const fall = (up, y0, y1) => (up + Math.sqrt(up * up + 2 * gb * (y1 - y0))) / gb;
      const tO = T0 + 1.48 - fall(upG, yG, arm), arcs = [];
      let t = tO;
      hits.forEach(([x0, y0, up], i) => {
        const T = i < hits.length - 1 ? fall(up, y0, hits[i + 1][1]) : fall(up, y0, HM.mid);
        const vx = i < hits.length - 1 ? (x0 - hits[i + 1][0]) / T : (x0 - HM.mid) / fall(up, y0, band);
        arcs.push({ t0: t, t1: t + T, x0, y0, up, vx });
        t += T;
      });
      const vyT = hits[0][2] / e, edge = K.winR + HM.r + 0.5, pad = 8.5 / K.unit;
      const at = (vx, s) => [xG + vx * s, yG - vyT * s + 0.5 * gb * s * s];
      const clear = (vx) => {
        const te = (edge - xG) / vx;
        for (let s = 0.004; s <= te; s += 0.002) {
          const [x, y] = at(vx, s);
          if (x + HM.r <= K.winR && y - HM.r < K.winT + 0.8) return false;
          if (K.bars.some((b) => x > b[0] - HM.r - pad && x < b[2] + HM.r + pad && y > b[1] - HM.r - pad && y < b[3] + HM.r + pad)) return false;
          if (x > 19.2 - HM.r && x < 107.4 + HM.r && Math.abs(x - xG) > HM.r && y + HM.r > 2.2) return false;
        }
        return true;
      };
      const want = (edge - xG) * gb / (2 * vyT);
      let vx = 0;
      for (let v = 60; v <= 2000; v += 2) if (clear(v) && (!vx || Math.abs(v - want) < Math.abs(vx - want))) vx = v;
      if (!vx) vx = want;
      const throwAt = tO - (edge - xG) / vx;
      K.ball = { e, gb, vyT, vx, tO, throwAt, arcs, band, end: t };
      const L = arcs[arcs.length - 1], tl = L.t1 - L.t0;
      K.catch = hmHome(L.x0 - L.vx * tl, HM.mid, -L.vx, -L.up + gb * tl, 60, 0.9);
      K.stamp = t + 0.2;
    },
    frame(t, S, K) {
      const { lb, rb, dot } = S, Ls = S.letters, B = K.ball, g = B.gb;
      Ls.forEach((l) => { l.o = hmSmooth(hmSpan(t, 0, 0.25)); });
      const dent = (i, at, amt) => { Ls[i].sy = Math.min(Ls[i].sy, 1 - amt * hmBump(t, at - 0.02, at + 0.18)); };
      const way = (p, w) => {
        const legs = w.legs, home = legs[legs.length - 1];
        if (t >= home[2]) return;
        p.py = 5.3125;
        const i = legs.findIndex((l) => t < l[2]);
        const [kind, a, b, x0, y0, x1, y1] = legs[i];
        let air = 0;
        if (t < a) { p.x = x0; p.y = y0; }
        else if (kind === 'run') {
          const s = t - a, k = s / (b - a);
          p.x = hmLerp(x0, x1, k); p.y = y0 - 0.45 * Math.abs(Math.sin(Math.PI * s / 0.1));
          p.r = -w.lean; p.sy = 1 + 0.04 * Math.cos(2 * Math.PI * s / 0.1); p.sx = 1 - 0.03 * Math.cos(2 * Math.PI * s / 0.1);
          return;
        } else {
          const k = (t - a) / (b - a), q = hmLob(x0, y0, x1, y1, b - a, t - a);
          p.x = kind === 'home' ? hmLerp(x0, x1, 1 - (1 - k) * (1 - k)) : q.x; p.y = q.y; air = hmArc(k);
          p.r = -w.lean * (i === 1 ? Math.max(air, 1 - k) : air) * (kind === 'home' ? 1 - k : 1);
        }
        let sq = 0;
        legs.forEach((l, j) => { if (j && l[0] !== 'home') sq += 0.16 * hmBump(t, l[2] - 0.01, l[2] + 0.06); });
        p.sx = 1 + sq * 0.6 - air * 0.04; p.sy = 1 - sq + air * 0.06;
      };
      way(rb, K.right);
      way(lb, K.left);
      [K.right, K.left].forEach((w) => w.legs.slice(1, -1).forEach((l, j) => dent(w.stones[j], l[2], 0.08)));
      const fly = (x, y, vx, vy) => {
        const v = Math.hypot(vx, vy), st = Math.min(0.16, v / 500);
        Object.assign(dot, { x, y, a: Math.atan2(vy, vx) * 180 / Math.PI, sx: 1 + st, sy: 1 - st * 0.6 });
      };
      dot.o = t >= B.throwAt ? 1 : 0;
      const A = B.arcs, last = A[A.length - 1];
      if (t < B.tO) {
        const s = B.tO - Math.max(t, B.throwAt);
        fly(A[0].x0 + B.vx * s, A[0].y0 - B.vyT * s + 0.5 * g * s * s, -B.vx, B.vyT - g * s);
      } else if (t < last.t1) {
        const c = A.find((r) => t < r.t1), s = t - c.t0;
        fly(c.x0 - c.vx * s, c.y0 - c.up * s + 0.5 * g * s * s, -c.vx, -c.up + g * s);
        if (c === last) {
          const y = dot.y, n = hmSmooth(hmSpan(y, HM.m * 2.5 - 2.6, HM.m * 2.5 - 1.4)) * (1 - hmSmooth(hmSpan(y, HM.m * 4.5 + 1.2, HM.m * 4.5 + 2.4)));
          dot.sx = 1 + 0.2 * n + (dot.sx - 1) * (1 - n); dot.sy = 1 - 0.2 * n + (dot.sy - 1) * (1 - n);
        }
      } else {
        const d = K.catch.at(t - last.t1);
        Object.assign(dot, { x: d.x, y: d.y, a: d.a, sx: d.sx, sy: d.sy });
      }
      const touches = A.map((r) => r.t0);
      dent(4, A[0].t0, 0.06);
      const q = hmTouch(t, touches, 0.24);
      if (q) { dot.a = 0; dot.sx = 1 + q; dot.sy = 1 - q; }
    } },
};

function homeMarkScene(way, box, use, name, stamp, still) {
  const scene = HOME_MARK_SCENES[way], lock = use.ownerSVGElement;
  const at = lock.getBoundingClientRect(), from = box.getBoundingClientRect();
  if (!at.width) { still(); return; }
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', lock.getAttribute('viewBox'));
  svg.setAttribute('class', 'home-mark');
  svg.setAttribute('aria-hidden', 'true');
  svg.setAttribute('fill', 'none');
  svg.style.cssText = `position:absolute;left:${at.left - from.left}px;top:${at.top - from.top}px;width:${at.width}px;`
    + `height:${at.height}px;overflow:visible;pointer-events:none`;
  const parts = (name.getAttribute('d') || '').split(/(?=M)/), letterD = [];
  let n = 0;
  for (const c of [1, 1, 1, 1, 1, 2, 2, 1, 3]) { letterD.push(parts.slice(n, n + c).join('')); n += c; }
  const bracket = (d, cx) => `<g><path transform="scale(${HM.m}) translate(${-cx} -12)" d="${d}" stroke="currentColor" stroke-width="2" stroke-linecap="square" stroke-linejoin="miter"/></g>`;
  svg.innerHTML = (scene.letters ? `<g stroke="currentColor" stroke-width="1.3" stroke-linecap="square" stroke-linejoin="miter">${letterD.map((d) => `<path d="${d}"/>`).join('')}</g>` : '')
    + `<g>${scene.extra || ''}</g>`
    + bracket('M8.5 3.5H4.5V20.5H8.5', 6.5) + bracket('M15.5 3.5H19.5V20.5H15.5', 17.5)
    + `<circle r="${HM.r}" stroke="none" style="fill: var(--mark-dot, currentColor)"/>`;
  const kids = [...svg.children], dotEl = kids.pop(), rbEl = kids.pop(), lbEl = kids.pop(), extra = kids.pop();
  const letterEls = scene.letters ? [...kids[0].children] : [];
  const unit = at.width / Number(lock.viewBox.baseVal.width || 107.33);
  const K = { extra: extra.firstElementChild, unit, room: at.left / unit, winR: (innerWidth - at.left) / unit, winT: -at.top / unit,
    bars: [...document.querySelectorAll('.lib-tools .bar-tool > *')].map((el) => el.getBoundingClientRect()).filter((r) => r.width)
      .map((r) => [(r.left - at.left) / unit, (r.top - at.top) / unit, (r.right - at.left) / unit, (r.bottom - at.top) / unit]),
    stamp: scene.stamp };
  const ending = () => K.stamp + (1 - HM_STAMP.down) * HM_STAMP.for + 0.01;
  const rest = () => ({
    lb: { x: HM.lb.x, y: HM.mid, r: 0, sx: 1, sy: 1, px: 0, py: 0, o: 1 },
    rb: { x: HM.rb.x, y: HM.mid, r: 0, sx: 1, sy: 1, px: 0, py: 0, o: 1 },
    dot: { x: HM.mid, y: HM.mid, a: 0, sx: 1, sy: 1, o: 1 },
    letters: letterEls.map(() => ({ dx: 0, dy: 0, r: 0, sx: 1, sy: 1, o: 1 })), name: 1 });
  const put = (el, p) => {
    el.setAttribute('transform', `translate(${p.x + p.px} ${p.y + p.py}) rotate(${p.r}) scale(${p.sx} ${p.sy}) translate(${-p.px} ${-p.py})`);
    el.setAttribute('opacity', String(p.o));
  };
  const frame = (t) => {
    const S = rest();
    scene.frame(t, S, K);
    put(lbEl, S.lb); put(rbEl, S.rb);
    const d = S.dot;
    dotEl.setAttribute('transform', `translate(${d.x} ${d.y}) rotate(${d.a}) scale(${d.sx} ${d.sy}) rotate(${-d.a})`);
    dotEl.setAttribute('opacity', String(d.o));
    letterEls.forEach((el, i) => {
      const l = S.letters[i], cx = K.L[i].cx;
      el.setAttribute('transform', `translate(${HM.nameX + l.dx} ${HM.nameY + l.dy}) translate(${cx} -0.65) rotate(${l.r}) scale(${l.sx} ${l.sy}) translate(${-cx} 0.65)`);
      el.setAttribute('opacity', String(l.o));
    });
    name.style.opacity = scene.letters ? '0' : String(S.name);
    hmStamp(stamp, t, K.stamp);
  };
  try {
    box.appendChild(svg);
    K.L = letterEls.map((el) => { const b = el.getBBox(); return { x0: b.x - 0.65, x1: b.x + b.width + 0.65, cx: b.x + b.width / 2 }; });
    if (scene.init) scene.init(K);
    frame(0);
  } catch { svg.remove(); still(); return; }
  const end = ending();
  const done = () => {
    svg.remove(); name.style.opacity = '';
    if (stamp) { stamp.style.opacity = ''; stamp.style.scale = ''; }
    still();
  };
  let t0 = null;
  const step = (now) => {
    if (t0 === null) t0 = now;
    const t = (now - t0) / 1000;
    if (t >= end || !svg.isConnected) { done(); return; }
    try { frame(t); } catch { done(); return; }
    requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

const ANAGRAM_REACH = 152;
const wayRoom = () => {
  const lock = document.querySelector('.wordmark .pe .lockup').getBoundingClientRect();
  const fits = lock.left + ANAGRAM_REACH * lock.width / 107.33 <= innerWidth - 6;
  return fits ? HOME_MARK_WAYS : HOME_MARK_WAYS.filter((w) => w !== 'anagram');
};
window.homeMarkPlay = homeMarkPlay;
try {
  if (document.documentElement.classList.contains('home-mark-due')) homeMarkPlay(homeMarkNext(wayRoom()));
  else homeMarkPlay();
} catch (e) { document.documentElement.classList.remove('home-mark-due'); }
})();
