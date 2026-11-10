/* A reviewer's board sent straight in (wtboard, 9 November 2026, Working together's sixth build, see team_board.py).
   On the PETs screen of a participant someone else works on, his own boards are marked Yours in the board menu, and
   Send board in the menu of one of them sends the board on the canvas to them, sealed (ownboards, 9 November 2026).
   What has come is taken in as the screen opens and every so often while it is open: a teammate's board waits,
   nothing written, on the owner's review line and card (review.js) for Add as next board or Decline (wtreview2,
   9 November 2026), and an answer to a board he sent is said once. Nothing shows while Working together is off.
   Every call goes through /api/team-board, the route the agents' `team board-*` ops call. */

const TMB = { view: null, path: '', tp: null, busy: false, last: 0, timer: null };
const TMB_EVERY = 20 * 1000;
const TMB_LOOK = 2 * 1000;

function tmbScreen() {
  return !!($('themes') && !$('themes').hidden && TH.mode === 'pets' && TH.path && TH.live);
}

function tmbBody(extra) {
  return Object.assign({ workbook: TH.path }, TH.tp ? { timepoint: TH.tp } : {}, extra);
}

/* "Yours" after the name of his own board of a participant someone else works on, in the board menu (ownboards,
   9 November 2026: his own boards are kept apart in his copy, and the owner's stay the owner's) */
function tmbOwnMark() {
  const v = TMB.view;
  const tip = t('team_board.page.own_tip', { name: (v && v.owner) || '' });
  return `<span class="th-vown" title="${escAttr(tip)}">${esc(t('team_board.page.own'))}</span>`;
}

/* On a participant someone else works on, the tooltip of the board menu's items he cannot use on the board on the
   canvas, one of theirs, or '' when he can (the one writer refuses them all the same). With `all`, the participant's
   own items, the PETs mark, which he cannot use on any board of it */
function tmbTheirsTip(all = false) {
  const v = TMB.view;
  if (!tmbScreen() || !v || !v.on || TMB.path !== TH.path || !Array.isArray(v.own) || !TH.meta) return '';
  if (all) return t('team_board.refused.not_own', { board: v.participant || '', name: v.owner || '' });
  const here = (TH.boards || []).find((b) => b.id === TH.meta.id);
  if ((here && here.own) || TH.meta.own) return '';
  return t('team_board.refused.not_own', { board: TH.meta.name || '', name: v.owner || '' });
}

/* the board menu's item, under the board's own name: there only on a board of his own while someone else works on
   this participant */
function tmbMenuItem() {
  const v = TMB.view;
  if (!tmbScreen() || !v || !v.on || !v.can_send || TMB.path !== TH.path) return '';
  const here = (TH.boards || []).find((b) => TH.meta && b.id === TH.meta.id);
  if (!(here && here.own) && !(TH.meta && TH.meta.own)) return '';
  const tip = t('team_board.page.send_tip', { name: v.owner || '', participant: v.participant || '' });
  return `<button type="button" class="ghost" tabindex="-1" data-vop="send-board" title="${escAttr(tip)}">${esc(t('team_board.page.send'))}</button>`;
}

/* Send board: the board on the canvas, saved first, sent to whoever works on the participant */
async function tmbSend() {
  if (!tmbScreen() || TMB.busy || !TH.meta) return;
  TMB.busy = true;
  try {
    await thFlush();
    const data = await api('/api/team-board', tmbBody({ op: 'send', board: TH.meta.id }));
    thVmenu(false);
    say(t('team_board.page.sent', { name: data.to || '' }), 4200);
  } catch (err) {
    thVsaid(err.message);
  } finally {
    TMB.busy = false;
  }
}

/* what has come, taken in, and the answers to his boards said */
async function tmbTake() {
  if (!tmbScreen() || TMB.busy) return;
  const path = TH.path;
  TMB.busy = true;
  TMB.last = Date.now();
  let data;
  try {
    data = await api('/api/team-board', tmbBody({ op: 'take' }));
  } catch {
    data = null;
  } finally {
    TMB.busy = false;
  }
  if (!data || TH.path !== path) return;
  TMB.view = data.board || { on: false };
  TMB.path = path;
  // an answer to a board he sent, said once
  for (const a of data.answers || []) {
    say(t(a.accept ? 'team_board.history.accepted' : 'team_board.history.declined',
      { name: a.name, board: a.board, participant: a.participant }), 6000);
  }
  // a teammate's board come in shows on the review line at once (review.js)
  if ((data.came || []).length && typeof rvwTick === 'function') rvwTick();
}

/* after a board loads on the canvas: taken in when the participant is new to it or a while has passed */
function tmbAfterLoad() {
  if (!tmbScreen()) return;
  if (TMB.path !== TH.path || TMB.tp !== TH.tp || Date.now() - TMB.last > TMB_EVERY) {
    TMB.tp = TH.tp;
    tmbTake();
  }
}

function tmbWire() {
  // while the PETs screen is open what has come is taken in every so often
  TMB.timer = setInterval(() => {
    if (!tmbScreen()) return;
    if (TMB.view && TMB.view.on && !document.hidden && Date.now() - TMB.last > TMB_EVERY) tmbTake();
  }, TMB_LOOK);
}

tmbWire();
