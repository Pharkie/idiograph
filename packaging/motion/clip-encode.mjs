// Makes one clip.mjs recording a looping clip for the website (siteclips, 12 November 2026): the frames laid on a
// steady 30 a second by their screencast times, cut to --crop when given, scaled to --width, then the last frame held
// --hold seconds and faded over --fade seconds into the first, so the loop comes round without a jump. Writes
// <out>.mp4 (H.264, muted, its index at the front), <out>.webm (VP9) and <out>.jpg, the poster, the frame at
// --poster seconds (the held end when left out), and prints each one's length and size.
// usage: node packaging/motion/clip-encode.mjs --raw <recording folder> --out <site/holding/clips/name>
//   [--width 1920] [--crop x,y,w,h in CSS pixels] [--from 0] [--to <end>] [--hold 1.8] [--fade 0.7] [--crf 27]
//   [--vp9 40] [--poster <seconds>] [--work <folder>]
//   [--then <second raw folder>] [--join 0.6]: a second recording after the first, crossfaded in over --join
import { readFileSync, writeFileSync, mkdirSync, statSync, rmSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join, dirname, resolve } from 'node:path';

import { args } from './chrome.mjs';

const USAGE = 'node packaging/motion/clip-encode.mjs --raw <recording> --out <path without extension> [--width 1920] [--crop x,y,w,h] [--from s] [--to s] [--hold 1.8] [--fade 0.7] [--crf 27] [--vp9 40] [--poster s] [--then <recording>] [--join 0.6] [--strip <png>] [--work <folder>]';
const o = args({ raw: '', out: '', width: 1920, crop: '', from: 0, to: 0, hold: 1.8, fade: 0.7, crf: 27, vp9: 40, poster: -1, then: '', join: 0.6, work: '', strip: '' }, USAGE);
if (!o.raw || !o.out) { console.error(USAGE); process.exit(2); }
const FPS = 30;
const ff = (a) => execFileSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', ...a], { stdio: ['ignore', 'inherit', 'inherit'] });
const probe = (f) => Number(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]).toString().trim());
const work = o.work || `${resolve(o.raw)}.work`;
mkdirSync(work, { recursive: true });
mkdirSync(dirname(resolve(o.out)), { recursive: true });

// one recording on a steady 30 a second, cut and scaled, as a near-lossless intermediate
function steady(raw, tag, { from = 0, to = 0 } = {}) {
  const meta = JSON.parse(readFileSync(join(raw, 'frames.json'), 'utf8'));
  const end = to || meta.end;
  const frames = meta.frames;
  const list = [];
  // for each tick of the output, the last frame painted at or before it
  let k = 0;
  const ticks = Math.round((end - from) * FPS);
  let last = null, run = 0;
  for (let i = 0; i < ticks; i++) {
    const t = from + i / FPS;
    while (k + 1 < frames.length && frames[k + 1].t <= t) k++;
    const f = frames[k].file;
    if (f === last) run++;
    else { if (last) list.push(`file '${join(resolve(raw), last)}'\nduration ${(run / FPS).toFixed(6)}`); last = f; run = 1; }
  }
  list.push(`file '${join(resolve(raw), last)}'\nduration ${(run / FPS).toFixed(6)}`, `file '${join(resolve(raw), last)}'`);
  const txt = join(work, `${tag}.txt`);
  writeFileSync(txt, list.join('\n') + '\n');
  const s = meta.scale;
  const crop = o.crop ? o.crop.split(',').map(Number).map((v) => Math.round(v * s)) : null;
  const vf = [crop ? `crop=${crop[2]}:${crop[3]}:${crop[0]}:${crop[1]}` : null, `scale=${o.width}:-2:flags=lanczos`, `fps=${FPS}`, 'format=yuv420p'].filter(Boolean).join(',');
  const out = join(work, `${tag}.mkv`);
  ff(['-f', 'concat', '-safe', '0', '-i', txt, '-vf', vf, '-r', String(FPS), '-c:v', 'libx264', '-crf', '8', '-preset', 'veryfast', '-t', (end - from).toFixed(3), out]);
  return { file: out, length: probe(out) };
}

const a = steady(o.raw, 'a', { from: o.from, to: o.to });
let body = a;
if (o.then) {
  const b = steady(o.then, 'b');
  const joined = join(work, 'ab.mkv');
  ff(['-i', a.file, '-i', b.file, '-filter_complex', `[0:v]fps=${FPS},settb=AVTB[p];[1:v]fps=${FPS},settb=AVTB[q];[p][q]xfade=transition=fade:duration=${o.join}:offset=${(a.length - o.join).toFixed(3)},format=yuv420p[v]`, '-map', '[v]', '-c:v', 'libx264', '-crf', '8', '-preset', 'veryfast', joined]);
  body = { file: joined, length: probe(joined) };
}
// the first frame, which the end fades into
const first = join(work, 'first.png');
ff(['-i', body.file, '-frames:v', '1', first]);
const loop = join(work, 'loop.mkv');
const D = body.length;
ff(['-i', body.file, '-loop', '1', '-t', String(o.fade + 0.2), '-framerate', String(FPS), '-i', first, '-filter_complex',
  `[0:v]fps=${FPS},settb=AVTB,tpad=stop_mode=clone:stop_duration=${o.hold + o.fade}[a];[1:v]format=yuv420p,fps=${FPS},settb=AVTB[b];[a][b]xfade=transition=fade:duration=${o.fade}:offset=${(D + o.hold).toFixed(3)},format=yuv420p[v]`,
  '-map', '[v]', '-t', (D + o.hold + o.fade).toFixed(3), '-c:v', 'libx264', '-crf', '8', '-preset', 'veryfast', loop]);

const mp4 = `${o.out}.mp4`, webm = `${o.out}.webm`, jpg = `${o.out}.jpg`;
ff(['-i', loop, '-an', '-c:v', 'libx264', '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-crf', String(o.crf), '-preset', 'veryslow', '-tune', 'animation',
  '-g', String(FPS * 10), '-movflags', '+faststart', '-map_metadata', '-1', mp4]);
ff(['-i', loop, '-an', '-c:v', 'libvpx-vp9', '-crf', String(o.vp9), '-b:v', '0', '-row-mt', '1', '-deadline', 'good', '-cpu-used', '2', '-g', String(FPS * 10), '-map_metadata', '-1', webm]);
const at = o.poster >= 0 ? o.poster : D + o.hold * 0.5;
ff(['-ss', at.toFixed(3), '-i', loop, '-frames:v', '1', '-vf', 'scale=1600:-2:flags=lanczos', '-q:v', '4', jpg]);
// --strip: a contact strip of the clip's frames a second apart, five to a row, read left to right from 0 s
if (o.strip) {
  const n = Math.ceil(probe(mp4)), rows = Math.ceil(n / 5);
  ff(['-i', mp4, '-vf', `fps=1,scale=480:-2,tile=5x${rows}:padding=6:margin=6:color=0x888888`, '-frames:v', '1', o.strip]);
  console.log(`${o.strip} ${n} frames`);
}
const kb = (f) => (statSync(f).size / 1024).toFixed(0) + ' KB';
console.log(`${mp4} ${probe(mp4).toFixed(2)} s ${kb(mp4)}`);
console.log(`${webm} ${probe(webm).toFixed(2)} s ${kb(webm)}`);
console.log(`${jpg} at ${at.toFixed(2)} s ${kb(jpg)}`);
if (!o.work) rmSync(work, { recursive: true, force: true });
