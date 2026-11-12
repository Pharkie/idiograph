// IPA's own steps: on Juno's passage at 13:00 the quote is selected in the passage and taken, the experiential
// statement written beside it, then PETs, where that statement sits in its PET, then GETs across the three. The
// statement and its quote are the demo's own, emptied before the recording and written again as they were
import { home, openParticipant, clickText, wordsAt, empty } from './app.mjs';

const QUOTE = ['It is being wanted.', 'it is just a fact.'];
const STATEMENT = 'Wanted as by nobody else';

export async function setup(h) {
  await home(h);
  await openParticipant(h, 'Juno', 'es');
  const path = await h.eval(() => S.data.path);
  await h.goto('/#open=' + encodeURIComponent(JSON.stringify({ screen: 'work', path, sheet: 'Initial', row: 35 })));
  await h.visible('#es-status');
  await h.sleep(1200);
  await empty(h, '#kq-p1');
  await empty(h, '#es-p1');
  await h.sleep(300);
  // nothing left in focus, the pointer resting over the passage
  await h.eval(() => document.activeElement && document.activeElement.blur());
  await h.place(800, 600);
  await h.sleep(1000);
}

export async function act(h) {
  await h.sleep(700);
  // the words selected in the passage, then taken as the quote with the arrow beside it
  const at = await wordsAt(h, '#work .turn-text', ...QUOTE);
  await h.move(at.x1, at.y1, 800);
  await h.sleep(150);
  await h.drag(at.x2, at.y2, { ms: 1300, settle: 120 });
  await h.sleep(400);
  const take = await h.box('.pair[data-pid="p1"] .pair-take');
  await h.click(take.cx, take.cy, { ms: 800 });
  await h.sleep(500);
  // the statement written in the participant's terms
  const es = await h.box('#es-p1');
  await h.click(es.x + 40, es.cy, { ms: 700 });
  await h.sleep(200);
  await h.type(STATEMENT, { cps: 15 });
  await h.sleep(900);
  // PETs: the statement on its card, in the PET it sits in
  await clickText(h, 'PETs', { ms: 900, within: '.ds-tab-name' });
  await h.visible('#th-status');
  await h.sleep(1300);
  const card = await h.box('#th-stage .th-card[data-key="Initial:35:0"]');
  if (card) {
    await h.move(card.cx, card.cy, 900);
    for (let i = 0; i < 16; i++) { await h.wheel(-60); await h.sleep(55); }
  }
  await h.sleep(1800);
  // GETs, across the three participants
  await clickText(h, 'GETs', { ms: 900, within: '.ds-tab-name' });
  await h.visible('#th-status');
  await h.sleep(1200);
  // a little nearer, so the GETs' titles read
  const stage = await h.box('#th-stage');
  await h.move(stage.x + stage.w * 0.5, stage.y + stage.h * 0.42, 900);
  for (let i = 0; i < 6; i++) { await h.wheel(-60); await h.sleep(70); }
  await h.sleep(2000);
}
