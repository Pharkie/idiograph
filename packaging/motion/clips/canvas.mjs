// PETs on a canvas: on a new board of Juno's, three statements dragged from the sidebar onto the canvas, grouped and
// named, a PET's label added over them, and a sub-PET made before dragged in. The words are the demo's own analysis
// (her PET "Caught" going soft and two of its sub-PETs)
import { home, openParticipant, clickText, label, sidebarTo, bring } from './app.mjs';

export async function setup(h) {
  await home(h);
  await openParticipant(h, 'Juno', 'pets');
  await clickText(h, 'Board 1');
  await h.sleep(400);
  await clickText(h, 'New board, empty');
  await h.sleep(700);
  await h.key('Enter');
  await h.sleep(400);
  // the board menu closed by a click on the empty canvas
  await h.click(700, 600, { ms: 10 });
  await h.sleep(800);
  // the walk's sub-PET made first, at the right, as he might have made it a minute before
  for (const [key, y] of [['Initial:17:0', 380], ['Initial:17:1', 490], ['Initial:19:0', 600]]) {
    await bring(h, key, 900, y, { reach: 100, ms: 400 });
    await h.sleep(400);
  }
  const placed = await h.eval(() => document.querySelectorAll('#th-stage .th-card').length);
  if (placed !== 3) throw new Error(`the walk's three statements did not reach the canvas (${placed})`);
  await h.place(840, 300);
  await h.drag(1200, 720, { ms: 400, settle: 100 });
  await h.sleep(300);
  await h.key('g');
  await h.sleep(300);
  await h.type('A walk once resented, now “the bit of the day that is mine”', { cps: 400 });
  await h.key('Enter');
  await h.sleep(500);
  await h.click(700, 740, { ms: 10 });
  await sidebarTo(h, 'Initial:21:0', 6);
  await h.place(700, 520);
  await h.sleep(1200);
}

export async function act(h) {
  await h.sleep(600);
  // three statements of her first year's regret, each row sliding up into the last one's place
  await bring(h, 'Initial:23:0', 460, 400, { reach: 800, ms: 900 });
  await h.sleep(200);
  await bring(h, 'Initial:25:0', 460, 510, { reach: 500, ms: 900 });
  await h.sleep(200);
  await bring(h, 'Initial:25:1', 460, 620, { reach: 500, ms: 900 });
  await h.sleep(300);
  // a lasso round them, then Group, and the title typed
  await h.move(405, 345, 500);
  await h.drag(700, 740, { ms: 700, settle: 100 });
  await h.sleep(250);
  await clickText(h, 'Group', { ms: 700 });
  await h.sleep(350);
  await h.type('A first year’s regret, too terrible to say and never quite gone', { cps: 24 });
  await h.sleep(200);
  await h.key('Enter');
  await h.sleep(600);
  // the sub-PET selected, and a PET's label added over it
  const sub = await label(h, 'regret');
  await h.click(sub.x + 70, sub.y + 14, { ms: 600 });
  await h.sleep(200);
  await clickText(h, 'Group', { ms: 700 });
  await h.sleep(350);
  await h.type('“Caught” going soft for the dog she said no to', { cps: 24 });
  await h.sleep(200);
  await h.key('Enter');
  await h.sleep(700);
  // the walk's sub-PET dragged onto the PET's title, where it goes in under it. It stays where it is let go and the
  // PET gathers round it, so it is let go near the title's right end, which leaves the whole PET in view
  const walk = await label(h, 'walk');
  const pet = await label(h, 'Caught');
  await h.move(walk.x + 14, walk.y + 16, 700);
  await h.sleep(100);
  await h.drag(pet.x + Math.min(330, pet.w - 10), pet.y + 37, { ms: 1300, settle: 220 });
  await h.sleep(500);
  await h.click(1200, 748, { ms: 700 });
  await h.sleep(500);
}
