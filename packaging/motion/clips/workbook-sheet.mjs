// Your Excel workbook, on your computer, its second part: Juno's workbook's first sheet drawn from the file itself by
// sheet.py (its cells, column widths, fonts and frozen header as the file sets them), read down, then across from
// her statements to her transcript, notes and quotes. It is never a capture of a spreadsheet program's window.
// CLIP_WORKBOOK names another workbook, and IDIOGRAPH_PYTHON a python with openpyxl (python3 when left out)
import { execFileSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { join } from 'node:path';

const BOOK = process.env.CLIP_WORKBOOK || fileURLToPath(new URL('../../../demo/Juno/Juno - EN & ES.xlsx', import.meta.url));
const SHEET = fileURLToPath(new URL('./sheet.py', import.meta.url));

// the grid scrolled `dx`, `dy` with an ease over `ms`, as a trackpad's glide scrolls it
const glide = (h, dx, dy, ms) => h.eval(([x, y, t]) => new Promise((done) => {
  const g = document.querySelector('.grid'), fx = g.scrollLeft, fy = g.scrollTop, t0 = performance.now();
  const step = (now) => {
    const k = Math.min(1, (now - t0) / t), e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
    g.scrollLeft = fx + x * e; g.scrollTop = fy + y * e;
    if (k < 1) requestAnimationFrame(step); else done();
  };
  requestAnimationFrame(step);
}), [dx, dy, ms]);

export async function setup(h) {
  const out = join(h.out, 'sheet.html');
  execFileSync(process.env.IDIOGRAPH_PYTHON || 'python3', [SHEET, BOOK, out], { stdio: 'ignore' });
  await h.goto(pathToFileURL(out).href);
  await h.sleep(800);
}

export async function act(h) {
  await h.sleep(1300);
  await glide(h, 0, 460, 3200);
  await h.sleep(800);
  // across by the statements' column, so the transcript's stands at the frozen columns' edge, as a sheet scrolls
  const across = await h.eval(() => document.querySelectorAll('thead th')[3].getBoundingClientRect().width);
  await glide(h, across, 0, 2600);
  await h.sleep(1800);
}
