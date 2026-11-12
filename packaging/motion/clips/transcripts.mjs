// Transcripts in the shapes you have: a transcript kept as a CSV, Add transcripts on the project's page, the file
// chosen, its Margin column set to Exploratory notes, the participant's pseudonym typed and Add, then the new
// participant's Experiential statements, the transcript with its notes beside it. The interview is invented
// (files/Ellis - interview.csv), and its participant is new to the demo
import { fileURLToPath } from 'node:url';
import { home, clickText, glideTo } from './app.mjs';

const FILE = fileURLToPath(new URL('./files/Ellis - interview.csv', import.meta.url));

export async function setup(h) {
  await home(h);
  // the project's rows in view, Add transcripts under them
  await h.eval(() => {
    const rows = document.querySelector('#hp-list');
    window.scrollTo(0, window.scrollY + rows.getBoundingClientRect().top - 130);
  });
  await h.place(900, 330);
  await h.sleep(900);
}

export async function act(h) {
  await h.sleep(800);
  await clickText(h, 'Add transcripts', { ms: 1000, within: 'button, a' });
  await h.sleep(800);
  await h.chooseFiles([FILE]);
  await clickText(h, 'Choose files', { ms: 900, within: 'button, label' });
  await h.sleep(1700);
  // the Margin column, left out, set to Exploratory notes: its chooser clicked, then E and Enter, as the keyboard
  // sets a chooser (the system draws the open list, which a headless page never shows)
  const margin = await h.eval(() => {
    const s = [...document.querySelectorAll('select')].filter((e) => e.getBoundingClientRect().width > 0 && e.value === '')[0];
    s.id = s.id || 'clip-margin';
    const r = s.getBoundingClientRect();
    return { cx: r.x + r.width / 2, cy: r.y + r.height / 2 };
  });
  await h.click(margin.cx, margin.cy, { ms: 1000 });
  await h.sleep(500);
  await h.key('E');
  await h.sleep(150);
  await h.key('Enter');
  await h.sleep(2200);
  // down to the participant's fields, the pseudonym typed, and Add
  await h.eval(() => {
    const l = [...document.querySelectorAll('label')].find((x) => x.textContent.trim() === 'Pseudonym');
    const i = l.control || l.parentElement.querySelector('input');
    i.id = i.id || 'clip-pseudonym';
  });
  const id = await h.eval(() => { const l = [...document.querySelectorAll('label')].find((x) => x.textContent.trim() === 'Pseudonym'); return (l.control || l.parentElement.querySelector('input')).id; });
  await glideTo(h, `#${id}`, 0.55, 1300);
  await h.sleep(300);
  const ps = await h.box(`#${id}`);
  await h.click(ps.x + 30, ps.cy, { ms: 900 });
  await h.type('Ellis', { cps: 9 });
  await h.sleep(700);
  await clickText(h, 'Add', { ms: 900, within: 'button' });
  await h.visible('#hp-list .pcard');
  await h.sleep(1600);
  // the new participant's transcript on Experiential statements, the notes beside their passages
  const es = await h.eval(() => {
    const row = [...document.querySelectorAll('#hp-list .pcard')].find((r) => r.innerText.includes('Ellis'));
    const r = row.querySelector('.pc-es').getBoundingClientRect();
    return { cx: r.x + 80, cy: r.y + r.height / 2 };
  });
  await h.click(es.cx, es.cy, { ms: 1000 });
  await h.visible('#es-status');
  await h.sleep(800);
  await h.move(760, 690, 900);
  await h.sleep(2000);
}
