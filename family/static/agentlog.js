/* The agent log (agentlog, 3 November 2026, Adam's option B by dialog that morning, on refusaldraw's drawings), the
   family's since siftlog the same day (Adam, about 16:00: Sift and Trace too), each app showing its own log.
   Under Settings, AI features, Using your own AI agents: one line, how many entries and the latest, and Open, or
   "Nothing yet." Open shows the log in a sheet over Settings, in the pattern of the card for several held actions:
   each entry newest first on one line, what was asked and in which project, why it was refused, when, and Details
   opening the agent, the project, the command, the refusal and what the agent says he asked, with Copy. The actions
   that waited for his yes, dropped when approvals were removed (noholds, 13 November 2026), are an entry of their
   own, a note with no Details. It keeps the last 7 days and nothing clears it (Adam, 3 November 2026, agent_log.py). Read from /api/agent-log each time Settings
   opens (shell.js, openSettings) and each time the sheet does. */

const AGENT_LOG = { entries: [], open: -1 };
/* each command's name for people, by its words, an MCP tool's by its command: the family's own here, and each app's
   added from its own script (agentlog_idiograph.js, sift_settings.js, trace.js), which come after this one */
const AL_OPS = {
  'agents log': 'agentlog.op_agents_log',
};
const AL_CHEV = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M6 9l6 6 6-6"/></svg>';

/* When, as a row says it: Today 19:42, Yesterday 15:00, or 31 Oct 09:51 */
function alWhen(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  const time = tTime(d);
  const now = new Date();
  const day = (x) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
  const days = Math.round((day(now) - day(d)) / 86400000);
  if (days === 0) return t('agentlog.today', { time });
  if (days === 1) return t('agentlog.yesterday', { time });
  const opts = d.getFullYear() === now.getFullYear() ? { day: 'numeric', month: 'short' }
    : { day: 'numeric', month: 'short', year: 'numeric' };
  return t('agentlog.on_day', { day: tDate(d, opts), time });
}

/* The agent by the name it gave, else "The agent" */
const alAgent = (e) => e.agent || t('agentlog.the_agent');

/* What was asked, in plain words, by its command, or a command the app does not have */
const alTitle = (e) => (AL_OPS[e.op] ? t(AL_OPS[e.op]) : t('agentlog.op_unknown', { app: APP_NAME }));

/* The refusal as the window says it to him, else as the agent was told */
const alSaid = (e) => e.said || e.line || '';

/* A refusal's line escaped, each flag it names, --dry-run, kept whole on one line so it never breaks at a hyphen */
const alFlags = (text) => esc(text).replace(/(^|\s)(--?[A-Za-z][\w-]*)/g, '$1<span class="al-word">$2</span>');

/* The project, by name, or a count of those agents may not read, never named */
function alWhere(e) {
  if (e.closed) return t('agentlog.in_closed', { n: e.closed });
  return e.project ? t('agentlog.in', { project: e.project }) : '';
}

async function agentLogLine() {
  if (!$('agent-log')) return;
  try {
    const data = await api('/api/agent-log');
    AGENT_LOG.entries = Array.isArray(data.entries) ? data.entries : [];
  } catch {
    AGENT_LOG.entries = [];
  }
  alLineDraw();
  if (!$('agent-log-sheet').hidden) alDraw();
}

function alLineDraw() {
  const list = AGENT_LOG.entries;
  $('agent-log-none').hidden = list.length > 0;
  $('agent-log-sum').hidden = !list.length;
  if (list.length) $('agent-log-line').textContent = t('agentlog.summary', { n: list.length });
}

function alRow(e, i) {
  const open = i === AGENT_LOG.open;
  let what;
  if (e.kind === 'note') {
    const where = alWhere(e);
    what = `<span class="al-what">${esc(t('agentlog.cleared'))}${where ? ` <span class="al-in">${esc(where)}</span>` : ''}</span>`
      + `<span class="al-why">${esc(e.line || '')}</span>`;
  } else {
    const where = alWhere(e);
    what = `<span class="al-what">${esc(alTitle(e))}${where ? ` <span class="al-in">${esc(where)}</span>` : ''}</span>`
      + `<span class="al-why">${alFlags(alSaid(e))}</span>`;
  }
  const more = e.kind === 'note' ? '<span></span>'
    : `<button type="button" class="ghost small al-more" data-i="${i}" aria-expanded="${open}">${esc(t('agentlog.details'))} ${AL_CHEV}</button>`;
  let li = `<li class="al-item"><div class="al-row"><div>${what}</div><span class="al-when">${esc(alWhen(e.time))}</span>${more}</div>`;
  if (open && e.kind !== 'note') {
    const words = String(e.call || '').split(' ').map((w) => `<span class="al-word">${esc(w)}</span>`).join(' ');
    const where = e.closed ? alWhere(e) : (e.project || t('agentlog.not_known'));
    li += `<div class="al-detail"><dl>`
      + `<dt>${esc(t('agentlog.agent'))}</dt><dd>${esc(alAgent(e))}</dd>`
      + `<dt>${esc(t('agentlog.project'))}</dt><dd>${esc(where)}</dd>`
      + `<dt>${esc(t('agentlog.command'))}</dt><dd class="al-cmd">${words}</dd>`
      + `<dt>${esc(t('agentlog.refused'))}</dt><dd>${alFlags(alSaid(e))}</dd>`
      + (e.count > 1 ? `<dt>${esc(t('agentlog.repeated'))}</dt><dd>${esc(t('agentlog.times', { n: e.count, when: alWhen(e.at) }))}</dd>` : '')
      + (e.request ? `<dt>${esc(t('agentlog.says_asked', { agent: alAgent(e) }))}</dt><dd>“${esc(e.request)}”</dd>` : '')
      + `</dl><button type="button" class="ghost small al-copy" data-i="${i}">${esc(t('agentlog.copy'))}</button></div>`;
  }
  return `${li}</li>`;
}

function alDraw() {
  const list = AGENT_LOG.entries;
  $('al-list').innerHTML = list.length ? `<ul class="al-rows">${list.map(alRow).join('')}</ul>` : '';
}

async function agentLogOpen() {
  AGENT_LOG.open = -1;
  $('al-said').hidden = true;
  alDraw();
  show('agent-log-sheet');
  $('al-list').scrollTop = 0;
  $('al-done').focus();
  await agentLogLine();
}

function agentLogClose() {
  hide('agent-log-sheet');
  if ($('agent-log-open') && !$('agent-log-sum').hidden) $('agent-log-open').focus();
}

/* the text Copy puts on the clipboard: the rows Details shows, each a line */
function alCopyText(e) {
  const rows = [[t('agentlog.agent'), alAgent(e)], [t('agentlog.project'), e.closed ? alWhere(e) : (e.project || t('agentlog.not_known'))],
    [t('agentlog.command'), e.call || ''], [t('agentlog.refused'), alSaid(e)]];
  if (e.request) rows.push([t('agentlog.says_asked', { agent: alAgent(e) }), `“${e.request}”`]);
  return rows.map(([k, v]) => `${k}: ${v}`).join('\n');
}

async function alClick(ev) {
  const more = ev.target.closest('.al-more');
  if (more) {
    const i = Number(more.dataset.i);
    AGENT_LOG.open = AGENT_LOG.open === i ? -1 : i;
    const top = $('al-list').scrollTop;
    alDraw();
    $('al-list').scrollTop = top;
    const again = $('al-list').querySelector(`.al-more[data-i="${i}"]`);
    if (again) again.focus();
    return;
  }
  const copy = ev.target.closest('.al-copy');
  if (copy) {
    const e = AGENT_LOG.entries[Number(copy.dataset.i)];
    if (!e) return;
    try {
      await navigator.clipboard.writeText(alCopyText(e));
      copy.textContent = t('shell.agent.copied');
      setTimeout(() => { copy.textContent = t('agentlog.copy'); }, 1600);
    } catch {
      saidIn('al-said', t('shell.agent.clipboard_refused'), true);
      $('al-said').hidden = false;
    }
  }
}

/* Esc on the sheet closes it as Done does */
function agentLogKeys(e) {
  if ($('agent-log-sheet') && !$('agent-log-sheet').hidden && e.key === 'Escape') {
    e.preventDefault(); agentLogClose(); return true;
  }
  return false;
}

function agentLogBoot() {
  if (!$('agent-log')) return;
  $('agent-log-open').onclick = () => agentLogOpen();
  $('al-done').onclick = () => agentLogClose();
  $('al-close').onclick = () => agentLogClose();
  $('al-list').addEventListener('click', alClick);
}

// the page's markup is in place by now, this script at its foot after distil.js, and a page without the log, a piece of
// it run alone in the suite's harness, has nothing to boot
if (typeof document !== 'undefined' && document.getElementById) agentLogBoot();
