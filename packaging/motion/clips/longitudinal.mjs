// Longitudinal IPA: an invented study of three people's first year on an allotment, interviewed before the season,
// at midsummer and after the harvest (make_lipa.py makes it through the command line). On LGETs, Nell's LPET of the
// children's plot is dragged into the LGET it belongs to, then on Trajectories Nell is placed in Letting go, her
// LPETs read across the three timepoints in their key quotes
import { home, clickText, label } from './app.mjs';

export async function setup(h) {
  await home(h);
  const row = await h.eval(() => {
    const e = [...document.querySelectorAll('button')].filter((x) => x.innerText && x.innerText.trim().startsWith('LGETs, across all participants') && x.getBoundingClientRect().width > 0).pop();
    e.scrollIntoView({ block: 'center' });
    const r = e.getBoundingClientRect();
    return { cx: r.x + 80, cy: r.y + r.height / 2 };
  });
  await h.click(row.cx, row.cy, { ms: 10 });
  await h.visible('#th-status');
  await h.sleep(1500);
  // the board fitted to the window, as Fit all fits it
  await clickText(h, 'Fit all', { within: 'button', ms: 10 });
  await h.sleep(900);
  await h.place(1150, 420);
  await h.sleep(800);
}

export async function act(h) {
  await h.sleep(900);
  // Nell's unplaced LPET into the LGET of a plot shared with others, let go in its body beside the two there
  const card = await h.eval(() => {
    const e = [...document.querySelectorAll('#th-stage .th-card')].find((x) => x.innerText.includes('A plot for the children'));
    const r = e.getBoundingClientRect();
    return { x: r.x, y: r.y, w: r.width, h: r.height };
  });
  const get = await label(h, 'Shared with others');
  const body = await h.eval((t) => {
    const e = [...document.querySelectorAll('#th-stage .th-label')].find((x) => x.innerText.includes(t));
    const f = [...document.querySelectorAll('#th-stage .th-frame, #th-stage [class*=frame]')].map((x) => x.getBoundingClientRect())
      .filter((r) => r.width > 0 && r.top < e.getBoundingClientRect().top + 4 && r.bottom > e.getBoundingClientRect().bottom && r.left <= e.getBoundingClientRect().left + 20)
      .sort((p, q) => p.width * p.height - q.width * q.height)[0];
    return f ? { x: f.x, y: f.y, w: f.width, h: f.height } : null;
  }, 'Shared with others');
  await h.move(card.x + card.w * 0.5, card.y + 22, 900);
  await h.sleep(150);
  const to = body ? { x: body.x + body.w - 60, y: body.y + body.h - 50 } : { x: get.x + get.w - 40, y: get.y + get.h + 120 };
  await h.drag(to.x, to.y, { ms: 1500, settle: 220 });
  await h.sleep(1500);
  // Trajectories: Nell from Not placed into Letting go
  await clickText(h, 'Trajectories', { ms: 1000, within: '.ds-tab-name' });
  await h.visible('#traj .tf-band');
  await h.sleep(1500);
  const nell = await h.eval(() => {
    const e = document.querySelector('.tf-pcell[data-case$="Nell"]');
    const r = e.getBoundingClientRect();
    return { cx: r.x + r.width / 2, cy: r.y + Math.min(60, r.height / 2) };
  });
  const band = await h.eval(() => {
    // its title is a field, so found by the field's words as well as the band's
    const e = [...document.querySelectorAll('.tf-band[data-col]')].find((x) => x.innerText.includes('Letting go')
      || [...x.querySelectorAll('input, textarea')].some((i) => i.value === 'Letting go'));
    const r = e.getBoundingClientRect();
    return { x: r.x, y: r.y, w: r.width, h: r.height };
  });
  await h.move(nell.cx, nell.cy, 900);
  await h.sleep(150);
  await h.dragNative(band.x + 140, band.y + band.h - 30, { ms: 1300, settle: 200 });
  await h.sleep(1200);
  await h.move(900, 525, 900);
  await h.sleep(2200);
}
