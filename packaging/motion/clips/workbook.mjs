// Your Excel workbook, on your computer, its first part: on the project's page, Juno's row's menu, Show files, and
// her workbook under her row, "Juno - EN & ES", its sheet and where it stands. workbook-sheet.mjs is its second
// part, the workbook's own rows, and clip-encode.mjs joins the two with --then
import { home, clickText } from './app.mjs';

export async function setup(h) {
  await home(h);
  await h.eval(() => {
    const rows = document.querySelector('#hp-list');
    window.scrollTo(0, window.scrollY + rows.getBoundingClientRect().top - 130);
  });
  await h.place(760, 560);
  await h.sleep(900);
}

export async function act(h) {
  await h.sleep(800);
  const dots = await h.box('#hp-list .pcard:first-child button[aria-label^="Files of"]');
  await h.click(dots.cx, dots.cy, { ms: 1100 });
  await h.sleep(700);
  await clickText(h, 'Show files', { ms: 700, within: 'button, [role=menuitem], li, a' });
  await h.sleep(900);
  const book = await h.eval(() => {
    const e = [...document.querySelectorAll('#hp-list .pcard:first-child *')].find((x) => x.children.length === 0 && x.textContent.trim() === 'Juno - EN & ES');
    const r = e.getBoundingClientRect();
    return { cx: r.x + r.width / 2, cy: r.y + r.height / 2 };
  });
  await h.move(book.cx + 20, book.cy + 4, 900);
  await h.sleep(1800);
}
