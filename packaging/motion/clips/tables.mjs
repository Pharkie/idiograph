// Tables for your supervisor and thesis: Juno's PETs board turned to its Table view, then its print view, the
// table of PETs in the book's layout, read down slowly. The print view opens in a window of its own in the app and a
// tab of its own in a browser: here it opens in the same tab, without its print dialog, so the recording follows it
import { home, openParticipant, clickText, glideBy } from './app.mjs';

export async function setup(h) {
  await home(h);
  await openParticipant(h, 'Juno', 'pets');
  await h.eval(() => {
    window.open = (u) => {
      if (u && u !== 'about:blank') setTimeout(() => location.assign(String(u).replace('auto=1', 'auto=0')), 0);
      return { close() {}, location: {} };
    };
  });
  await h.place(760, 470);
  await h.sleep(800);
}

export async function act(h) {
  await h.sleep(900);
  await clickText(h, 'Table', { ms: 1000, within: 'button' });
  await h.sleep(1300);
  await h.move(700, 470, 900);
  await h.sleep(1200);
  await clickText(h, 'Print', { ms: 1000, within: 'button' });
  await h.visible('h1, .pp-head, table, main');
  await h.sleep(1600);
  await h.move(110, 560, 700);
  await glideBy(h, 470, 3000);
  await h.sleep(1100);
  await glideBy(h, 470, 3000);
  await h.sleep(1300);
}
