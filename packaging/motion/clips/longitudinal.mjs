// Screens: apps/idiograph/static/trajectories.js, apps/idiograph/static/themes.js, apps/idiograph/static/themes.css, apps/idiograph/static/i18n/en/trajectories.json, apps/idiograph/static/i18n/en/themes.json, demo/lipa/
// Longitudinal IPA, on the app's own longitudinal demo (demo/lipa, "First year on an allotment": Hollis, Nell and
// Arlo interviewed before the season, at midsummer and after the harvest), as it ships and is filled as the server
// starts. On LGETs the three participants' LPETs stand in their LGETs; one LPET is opened to the statements it
// gathers, then Trajectories reads each participant's LPETs across the three timepoints in their key quotes, Hollis
// first and the page carried down to Nell. Nothing on the screens is changed, so a recording leaves the demo as it was
import { clickText, glideTo, glideBy } from './app.mjs';

// the project's page opened from Home's third demo, then its GETs row and the LGETs tab
export async function setup(h) {
  await h.eval(() => sessionStorage.setItem('idiograph.homeMark', '1'));
  await h.goto('');
  await h.visible('#demo-projects .home-card.is-demo');
  await h.sleep(800);
  const card = await h.eval(() => {
    const e = [...document.querySelectorAll('#demo-projects button.home-card.is-demo')].find((x) => x.innerText.includes('First year on an allotment'));
    // the card is taller than the window now (its pictures and rings), so its title is pressed
    e.scrollIntoView({ block: 'start' });
    const r = e.getBoundingClientRect();
    return { cx: r.x + 100, cy: r.y + 30 };
  });
  await h.click(card.cx, card.cy, { ms: 10 });
  await h.visible('#hp-list .pcard');
  await h.sleep(900);
  const row = await h.eval(() => {
    const e = document.querySelector('button.gets-wide');
    e.scrollIntoView({ block: 'center' });
    const r = e.getBoundingClientRect();
    return { cx: r.x + 80, cy: r.y + r.height / 2 };
  });
  await h.click(row.cx, row.cy, { ms: 10 });
  await h.visible('#th-status');
  await h.sleep(1200);
  await clickText(h, 'LGETs', { within: '.ds-tab-name', ms: 10 });
  await h.sleep(1800);
  // the board fitted to the window, as Fit all fits it, and the participants' list put away
  await h.clickOn('#th-cpanel-close', { ms: 10 });
  await h.sleep(500);
  await clickText(h, 'Fit all', { within: 'button', ms: 10 });
  await h.sleep(900);
  await h.place(1150, 150);
  await h.sleep(800);
}

export async function act(h) {
  await h.sleep(1000);
  // the statements Nell's LPET after the harvest gathers, opened from its card and put away
  const open = () => h.eval(() => {
    const card = [...document.querySelectorAll('#th-stage .th-card')].find((x) => x.innerText.includes('From taking too much to half given away'));
    const r = card.querySelector('button.gt-unfold').getBoundingClientRect();
    return { cx: r.x + 30, cy: r.y + r.height / 2 };
  });
  let at = await open();
  await h.click(at.cx, at.cy, { ms: 1100 });
  await h.sleep(2200);
  at = await open();
  await h.click(at.cx, at.cy, { ms: 700 });
  await h.sleep(1000);
  // Trajectories, Hollis's three LPETs across the timepoints, then the page carried down to Nell's
  await clickText(h, 'Trajectories', { ms: 1000, within: '.ds-tab-name' });
  await h.visible('#traj .tf-band');
  await h.sleep(2200);
  await h.move(1100, 700, 800);
  await glideTo(h, '.tf-pcell[data-case$="Nell"]', 0.12, 2200);
  await h.sleep(2800);
  await h.move(900, 560, 900);
  await h.sleep(800);
}
