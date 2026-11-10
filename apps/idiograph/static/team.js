/* Working together in Project settings (wtkeys, 8 November 2026, the first build of the design Adam chose that
   evening): one tick, off in every project until turned on, and someone working alone sees nothing else. On, the
   route, the people, Invite, Add a computer of mine and Join, who works on each participant and on the GETs board,
   and whether the recordings go, each change saved at once through /api/team, the route the agents' `team` ops
   call too (idiograph_routes.api_team, team.py). The invite's card shows the link and the twelve words, then the
   six digits once someone has answered, read on a call before They match. Members and computers (wtdevices,
   9 November 2026): Make lead and Remove on each other person's row for the lead, each computer of a person with
   more than one listed under them with Remove this computer, Add a computer of mine for every member, and on
   opening, what has come for the list of people taken in (`take`). */

const WT = { p: null, view: null, yourName: '', poll: null, invite: null, joining: null };
const WT_POLL_MS = 2000;

function wtSaid(text, failed = false) {
  saidIn('wt-said', text || '', failed);
  $('wt-said').hidden = !text;
}

function wtBody(extra) {
  return { ...projectBody(WT.p), ...extra };
}

/* the section for the project Project settings opened for: hidden for a demo, else as the server has it */
async function wtOpen(p) {
  WT.p = p;
  WT.view = null;
  wtStop();
  const block = $('wt-block');
  if (!block) return;
  block.hidden = !p || !!p.demo || !p.id;
  if (block.hidden) return;
  wtSaid('');
  $('wt-on').checked = false;
  $('wt-fields').hidden = true;
  $('wt-name-row').hidden = true;
  let got;
  try {
    got = await api('/api/team', wtBody({ op: 'show' }));
  } catch (err) {
    block.hidden = true;
    return;
  }
  if (WT.p !== p) return;
  WT.yourName = got.your_name || '';
  wtDraw(got.team || { on: false });
  if (!got.team || !got.team.on) return;
  // what has come for the list of people since it was last open: a newer list, a computer added or removed
  try {
    const took = await api('/api/team', wtBody({ op: 'take' }));
    if (WT.p === p && took.team) wtDraw(took.team);
  } catch (err) { /* no connection now: the list stays as it was, and the next opening tries again */ }
}

/* the section drawn from the server's view of it */
function wtDraw(view) {
  WT.view = view;
  const on = !!view.on;
  $('wt-on').checked = on;
  $('wt-fields').hidden = !on;
  if (on) $('wt-name-row').hidden = true;
  if (!on) return;
  document.querySelectorAll('#wt-route .th-from-opt').forEach((b) => {
    const here = b.dataset.route === view.route;
    b.classList.toggle('on', here);
    b.setAttribute('aria-checked', here ? 'true' : 'false');
    // Send through is the lead's choice: a member sees the team's route as it is, not as a choice
    b.hidden = !view.you_lead && !here;
    b.disabled = !view.you_lead;
  });
  $('wt-path').hidden = view.route !== 'folder';
  // the relay code, the lead's alone, while the relay is chosen and the project is not on it yet (relaywire)
  $('wt-code-row').hidden = !view.needs_code;
  $('wt-code-line').hidden = !view.needs_code;
  if (!view.needs_code) $('wt-relay-code').value = '';
  if (view.folder) $('wt-folder').innerHTML = pathHtml(view.folder);
  else $('wt-folder').textContent = t('team.page.no_folder');
  wtFolderSaid(view);
  wtPeople(view);
  wtWho(view);
  $('wt-recordings').checked = !!view.recordings;
  $('wt-invite').hidden = !view.you_lead;
  $('wt-own').hidden = !!view.removed;
  $('wt-join').hidden = !view.alone;
  wtAsked(view);
  if (view.removed) wtSaid(t('team.page.removed'));
}

/* a change to his own computers waiting for the lead's Idiograph, a line each */
function wtAsked(view) {
  const box = $('wt-asked');
  if (!box) return;
  box.textContent = '';
  const lead = (view.people.find((p) => p.lead) || {}).name || '';
  for (const a of view.asked || []) {
    const line = document.createElement('p');
    line.className = 'fineprint';
    line.textContent = t(a.add ? 'team.page.asked_add' : 'team.page.asked_remove', { computer: a.name || t('team.page.a_computer'), lead });
    box.appendChild(line);
  }
  box.hidden = !box.childElementCount;
}

function wtButton(text, onclick, label) {
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'ghost small';
  b.textContent = text;
  if (label) b.setAttribute('aria-label', label);
  b.onclick = onclick;
  return b;
}

/* each computer of a person with more than one, under their row: Remove this computer on any but the one he is on,
   for the lead on anyone's and for a member on his own */
function wtComputers(view, person) {
  const list = document.createElement('ul');
  list.className = 'wt-computers';
  for (const d of person.devices) {
    const li = document.createElement('li');
    const name = document.createElement('span');
    const said = d.name || t('team.page.a_computer');
    name.textContent = d.this ? `${said} · ${t('team.page.this_computer')}` : said;
    li.appendChild(name);
    if (!d.this) li.appendChild(wtButton(t('team.page.remove_computer'), () => wtRemoveComputer(d), `${t('team.page.remove_computer')}: ${said}`));
    list.appendChild(li);
  }
  return list;
}

/* the shared folder's state in plain words (wtfolder): not there, or files in it that will not open yet, a
   placeholder a sync app has not brought down */
function wtFolderSaid(view) {
  let text = '';
  if (view.route === 'folder' && view.folder_state === 'missing') text = t('team.page.folder_missing');
  else if (view.route === 'folder' && view.folder_state === 'unopened') text = t('team.page.folder_unopened', { n: view.unopened });
  saidIn('wt-folder-said', text, view.folder_state === 'missing');
  $('wt-folder-said').hidden = !text;
}

function wtPeople(view) {
  const list = $('wt-people');
  list.textContent = '';
  for (const person of view.people) {
    const li = document.createElement('li');
    const who = document.createElement('span');
    who.className = 'wt-who';
    const name = document.createElement('b');
    name.textContent = person.name;
    const sub = document.createElement('span');
    sub.className = 'wt-sub';
    const parts = [];
    if (person.lead) parts.push(t('team.page.lead'));
    parts.push(person.this_computer && person.computers === 1 ? t('team.page.this_computer') : t('team.page.computers', { n: person.computers }));
    sub.textContent = parts.join(' · ');
    who.append(name, sub);
    li.appendChild(who);
    if (view.you_lead && !person.lead) {
      const acts = document.createElement('span');
      acts.className = 'wt-btns';
      acts.append(wtButton(t('team.page.make_lead'), () => wtMakeLead(person), `${t('team.page.make_lead')}: ${person.name}`),
        wtButton(t('team.page.remove'), () => wtRemove(person), `${t('team.page.remove')}: ${person.name}`));
      li.appendChild(acts);
    } else {
      li.appendChild(document.createElement('span'));
    }
    const devices = person.devices || [];
    if (devices.length > 1 && (person.you || view.you_lead) && !view.removed) li.appendChild(wtComputers(view, person));
    list.appendChild(li);
  }
}

/* Who works on each: a participant's owner picked from the people, the lead's to change, and the GETs board's with
   Hand over, in an IPA project alone */
function wtWho(view) {
  const list = $('wt-who');
  list.textContent = '';
  const names = Object.fromEntries(view.people.map((p) => [p.id, p.name]));
  for (const row of view.participants) {
    const li = document.createElement('li');
    const label = document.createElement('span');
    label.textContent = row.label;
    const pick = document.createElement('select');
    pick.setAttribute('aria-label', row.label);
    for (const person of view.people) {
      const o = document.createElement('option');
      o.value = person.id;
      o.textContent = person.name;
      o.selected = person.id === row.owner;
      pick.appendChild(o);
    }
    pick.disabled = !view.you_lead;
    pick.onchange = () => wtSet({ owners: { [row.folder]: pick.value } });
    li.append(label, pick);
    list.appendChild(li);
  }
  if (WT.p && WT.p.method === 'ta') return;
  const li = document.createElement('li');
  const label = document.createElement('span');
  label.textContent = t('team.page.gets_board');
  const right = document.createElement('span');
  right.className = 'wt-gets';
  const owner = document.createElement('span');
  owner.textContent = names[view.gets_owner] || '';
  right.appendChild(owner);
  const others = view.people.filter((p) => p.id !== view.gets_owner);
  if (view.you_lead && others.length) {
    const hand = document.createElement('button');
    hand.type = 'button';
    hand.className = 'ghost small';
    hand.textContent = t('team.page.hand_over');
    hand.onclick = () => wtHandOver(others, right, hand);
    right.appendChild(hand);
  }
  li.append(label, right);
  list.appendChild(li);
}

/* Hand over the GETs board: to the one other person after a line to confirm, or with several, to the one picked */
function wtHandOver(others, right, hand) {
  const give = async (person) => {
    if (await askSure(t('team.page.hand_over_ask', { name: person.name }))) wtSet({ gets_owner: person.id });
  };
  if (others.length === 1) { give(others[0]); return; }
  const pick = document.createElement('select');
  pick.setAttribute('aria-label', t('team.page.hand_over'));
  pick.appendChild(document.createElement('option'));
  for (const person of others) {
    const o = document.createElement('option');
    o.value = person.id;
    o.textContent = person.name;
    pick.appendChild(o);
  }
  pick.onchange = () => { const person = others.find((p) => p.id === pick.value); if (person) give(person); };
  hand.replaceWith(pick);
  pick.focus();
}

async function wtCall(body) {
  try {
    const got = await api('/api/team', wtBody(body));
    wtSaid('');
    if (got.team) wtDraw(got.team);
    return got;
  } catch (err) {
    wtSaid(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err));
    return null;
  }
}

const wtSet = (changes) => wtCall({ op: 'set', ...changes });

/* Connect: the relay code to the relay once, through the server, and the field emptied whatever the answer, so the
   code stays nowhere on the page */
async function wtCode() {
  const code = $('wt-relay-code').value.trim();
  $('wt-relay-code').value = '';
  if (!code) { $('wt-relay-code').focus(); return; }
  $('wt-code-go').disabled = true;
  try { await wtSet({ code }); } finally { $('wt-code-go').disabled = false; }
}

/* the tick: on, with his name the first time when Settings holds none, or off */
async function wtTick() {
  if (!$('wt-on').checked) {
    $('wt-name-row').hidden = true;
    if (WT.view && WT.view.on) await wtCall({ op: 'off' });
    else wtDraw({ on: false });
    return;
  }
  const typed = $('wt-name').value.trim();
  if (!WT.yourName && !typed) {
    $('wt-name-row').hidden = false;
    $('wt-name').focus();
    return;
  }
  const got = await wtCall({ op: 'on', name: typed || WT.yourName, route: 'relay' });
  if (!got) $('wt-on').checked = false;
}

async function wtRemove(person) {
  if (!await askSure(t('team.page.remove_ask', { name: person.name }))) return;
  await wtCall({ op: 'remove', member: person.id });
}

async function wtRemoveComputer(d) {
  if (!await askSure(t('team.page.remove_computer_ask', { computer: d.name || t('team.page.a_computer') }))) return;
  await wtCall({ op: 'remove', computer: d.id });
}

async function wtMakeLead(person) {
  if (!await askSure(t('team.page.make_lead_ask', { name: person.name }))) return;
  await wtCall({ op: 'lead', member: person.id });
}

/* Choose beside the shared folder: the system's dialog on the app's own window (Mac and Windows), the folder
   going to the server as if typed, or the Mac's dialog from the server on the browser path */
async function wtChoose() {
  await picking((path) => wtCall(path ? { op: 'set', folder: path } : { op: 'choose' }), $('wt-choose'),
    t('team.page.folder'));
}

/* ── the invite's card ── */

function wtStop() {
  clearInterval(WT.poll);
  WT.poll = null;
}

function wtInviteSaid(text, failed = false) {
  saidIn('wt-invite-said', text || '', failed);
  $('wt-invite-said').hidden = !text;
}

async function wtInvite(own) {
  const got = await wtCall({ op: 'invite', own });
  if (!got) return;
  WT.invite = got.invite;
  $('wt-invite-kicker').textContent = WT.p.name || '';
  $('wt-invite-title').textContent = own ? t('team.invite.heading_own') : t('team.invite.heading');
  $('wt-link').textContent = got.link;
  $('wt-words').textContent = got.words;
  $('wt-answered').hidden = true;
  $('wt-invite-acts').hidden = true;
  wtInviteSaid('');
  show('wt-invite-card');
  wtStop();
  WT.poll = setInterval(wtAnswers, WT_POLL_MS);
}

/* whether someone has answered: the six digits, and They differ and They match */
async function wtAnswers() {
  if (!WT.invite || $('wt-invite-card').hidden) { wtStop(); return; }
  let got;
  try {
    got = await api('/api/team', wtBody({ op: 'answers', invite: WT.invite }));
  } catch (err) { wtStop(); wtInviteSaid(err.message, true); return; }
  if (!got.answered) return;
  wtStop();
  $('wt-code').textContent = got.code;
  $('wt-answer-line').textContent = t('team.invite.answered', { name: got.name });
  $('wt-answered').hidden = false;
  $('wt-invite-acts').hidden = false;
}

async function wtAnswer(match) {
  try {
    const got = await api('/api/team', wtBody({ op: 'admit', invite: WT.invite, match }));
    if (got.team) wtDraw(got.team);
  } catch (err) { wtInviteSaid(err.message, true); return; }
  if (match) { WT.invite = null; hide('wt-invite-card'); return; }
  // They differ: the answer thrown away, the invite still open for the right answer
  $('wt-answered').hidden = true;
  $('wt-invite-acts').hidden = true;
  WT.poll = setInterval(wtAnswers, WT_POLL_MS);
}

async function wtCopy(from) {
  try {
    await navigator.clipboard.writeText($(from).textContent);
    wtInviteSaid(t('team.invite.copied'));
  } catch (err) { wtInviteSaid(err.message, true); }
}

/* ── joining another's project, from this one while it is shared with nobody ── */

function wtJoinSaid(text, failed = false) {
  saidIn('wt-join-said', text || '', failed);
  $('wt-join-said').hidden = !text;
}

function wtJoinOpen() {
  $('wt-join-kicker').textContent = WT.p.name || '';
  $('wt-join-words').value = '';
  $('wt-join-words').disabled = false;
  $('wt-join-answered').hidden = true;
  $('wt-join-acts').hidden = false;
  wtJoinSaid('');
  show('wt-join-card');
}

async function wtJoin() {
  let got;
  try {
    got = await api('/api/team', wtBody({ op: 'join', words: $('wt-join-words').value }));
  } catch (err) { wtJoinSaid(err.message, true); return; }
  WT.joining = { invite: got.invite, from: got.from || '' };
  $('wt-join-words').disabled = true;
  $('wt-join-acts').hidden = true;
  $('wt-join-code').textContent = got.code;
  $('wt-join-line').textContent = t('team.join.read_code', { name: got.from || '' });
  $('wt-join-answered').hidden = false;
  wtJoinSaid(t('team.join.waiting', { name: got.from || '' }));
  wtStop();
  WT.poll = setInterval(wtJoined, WT_POLL_MS);
}

async function wtJoined() {
  if (!WT.joining || $('wt-join-card').hidden) { wtStop(); return; }
  let got;
  try {
    got = await api('/api/team', wtBody({ op: 'joined', invite: WT.joining.invite }));
  } catch (err) { wtStop(); wtJoinSaid(err.message, true); return; }
  if (!got.joined) return;
  wtStop();
  wtJoinSaid(t('team.join.joined', { name: WT.joining.from }));
  WT.joining = null;
  if (got.team) wtDraw(got.team);
}

function wtWire() {
  if (!$('wt-block')) return;
  $('wt-on').addEventListener('change', wtTick);
  $('wt-name').addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); wtTick(); } });
  $('wt-name').addEventListener('change', () => { if ($('wt-name').value.trim()) wtTick(); });
  document.querySelectorAll('#wt-route .th-from-opt').forEach((b) => {
    b.onclick = () => { if (!b.classList.contains('on')) wtSet({ route: b.dataset.route }); };
  });
  $('wt-choose').onclick = wtChoose;
  $('wt-code-go').onclick = wtCode;
  $('wt-relay-code').addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); wtCode(); } });
  $('wt-recordings').addEventListener('change', () => wtSet({ recordings: $('wt-recordings').checked }));
  $('wt-invite').onclick = () => wtInvite(false);
  $('wt-own').onclick = () => wtInvite(true);
  $('wt-join').onclick = wtJoinOpen;
  $('wt-copy-link').onclick = () => wtCopy('wt-link');
  $('wt-copy-words').onclick = () => wtCopy('wt-words');
  $('wt-match').onclick = () => wtAnswer(true);
  $('wt-differ').onclick = () => wtAnswer(false);
  $('wt-invite-close').onclick = () => { wtStop(); hide('wt-invite-card'); };
  $('wt-join-close').onclick = () => { wtStop(); hide('wt-join-card'); };
  $('wt-join-go').onclick = wtJoin;
}

wtWire();

/* ── the project's page (wtowners, 8 November 2026, shot 05, option A) ── */

const WT_DOWN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 4v12M7 11l5 5 5-5M5 20h14"/></svg>';
const WT_UP = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 15V4M7 9l5-5 5 5M5 20h14"/></svg>';

/* A project worked on together: on each participant another works on a tag with their name, on one of his out for
   review "With Curt for review", and under the question what came in today, newest first, and how many of his
   changes wait to send when the last try found no connection. `team` null, Working together off or a demo, draws
   nothing and takes away what was drawn. */
function wtPageDraw(team) {
  const lines = $('wt-team');
  if (!lines) return;
  lines.textContent = '';
  lines.hidden = true;
  $('hp-list').querySelectorAll('.tag.wt-own, .tag.wt-rev').forEach((e) => e.remove());
  if (!team) return;
  const tags = team.tags || {};
  $('hp-list').querySelectorAll(':scope > li.prow').forEach((li) => {
    const tag = tags[li.dataset.case];
    const dots = li.querySelector('.pc-dots');
    if (!tag || !dots) return;
    const span = document.createElement('span');
    span.className = tag.owner ? 'tag wt-own' : 'tag wt-rev';
    span.textContent = tag.owner ? t('team.page.tag_owner', { name: tag.owner }) : t('team.page.tag_review', { name: tag.review });
    dots.before(span);
  });
  const said = [];
  for (const came of team.arrivals || []) {
    const at = tTime(came.at);
    said.push(['', WT_DOWN, came.gets ? t('team.page.came_in_gets', { name: came.name, time: at })
      : t('team.page.came_in', { name: came.name, participant: came.participant, time: at })]);
  }
  if (team.offline && team.waiting > 0) said.push(['wt-wait', WT_UP, t('team.page.waiting', { n: team.waiting })]);
  for (const [cls, icon, text] of said) {
    const span = document.createElement('span');
    if (cls) span.className = cls;
    span.innerHTML = icon;
    span.append(text);
    lines.appendChild(span);
  }
  lines.hidden = !said.length;
}