/* Working together in Project settings (wtkeys, 8 November 2026, the first build of the design Adam chose that
   evening): one tick, off in every project until turned on, and someone working alone sees nothing else. On, the
   route, the people, Invite, Add a computer of mine and Join, who works on each participant and on the GETs board,
   and whether the recordings go, each change saved at once through /api/team, the route the agents' `team` ops
   call too (idiograph_routes.api_team, team.py). The invite's card shows the link and the twelve words, then the
   six digits once someone has answered, read on a call before They match. Members and computers (wtdevices,
   9 November 2026): Make lead and Remove on each other person's row for the lead, each computer of a person with
   more than one listed under them with Remove this computer, Add a computer of mine for every member, and on
   opening, what has come for the list of people taken in (`take`). How it starts (teambuild, 19 November 2026,
   teammock's option B, Adam's yes that night): off, Invite others to work on this project, which turns it on with
   this computer as lead as the tick did, and Join a project you were invited to, which opens the Join card at once
   and turns nothing on until the lead's They match comes in, so a joiner never leads a team of one first. A team
   kept from before with others on it shows Start working together again in their place, and on, the section
   starts with who leads and Stop working together. */

const WT = { p: null, view: null, yourName: '', poll: null, invite: null, joining: null, start: null, joinFolder: '', pending: null,
  answered: {}, rowPoll: null, pageTimer: null, pageTeam: null, pageAnswered: {}, starting: false };
// the invite and join cards ask about every 10 seconds, well inside the relay's 30 invite calls a minute from one address
const WT_POLL_MS = 10000;
// open invites in People and on the project's page ask about their answers every 30 seconds, a call for each invite
const WT_ROWS_MS = 30000;

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
  WT.answered = {};
  wtStop();
  wtRowsStop();
  const block = $('wt-block');
  if (!block) return;
  block.hidden = !p || !!p.demo || !p.id;
  if (block.hidden) return;
  wtSaid('');
  $('wt-start').hidden = true;
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
  WT.start = got.start || null;
  wtDraw(got.team || { on: false });
  if (!got.team || !got.team.on || got.team.unlisted) return;
  wtRowsWatch();
  // what has come for the list of people since it was last open: a newer list, a computer added or removed
  try {
    const took = await api('/api/team', wtBody({ op: 'take' }));
    if (WT.p === p && took.team) wtDraw(took.team);
  } catch (err) { /* no connection now: the list stays as it was, and the next opening tries again */ }
}

/* the section drawn from the server's view of it */
function wtDraw(view) {
  WT.view = view;
  // a roster that names the person but not this computer shows the start rows with Join alone, and the line why
  const unlisted = !!view.unlisted || !!(WT.start && WT.start.unlisted);
  const on = !!view.on && !view.unlisted;
  $('wt-fields').hidden = !on;
  wtStartDraw(on, unlisted);
  if (on) $('wt-name-row').hidden = true;
  if (unlisted) wtSaid(t('team.page.unlisted'));
  if (!on) return;
  const lead = (view.people.find((p) => p.lead) || {}).name || '';
  $('wt-leads').textContent = view.you_lead ? t('team.page.you_lead') : t('team.page.they_lead', { name: lead });
  document.querySelectorAll('#wt-route .th-from-opt').forEach((b) => {
    const here = b.dataset.route === view.route;
    b.classList.toggle('on', here);
    b.setAttribute('aria-checked', here ? 'true' : 'false');
    // Send through is the lead's choice: a member sees the team's route as it is, not as a choice
    b.hidden = !view.you_lead && !here;
    b.disabled = !view.you_lead;
  });
  $('wt-path').hidden = view.route !== 'folder';
  if (view.folder) $('wt-folder').innerHTML = pathHtml(view.folder);
  else $('wt-folder').textContent = t('team.page.no_folder');
  wtFolderSaid(view);
  if (WT.scrollTo) { const go = WT.scrollTo; WT.scrollTo = null; go(); }
  wtPeople(view);
  wtWho(view);
  $('wt-recordings').checked = !!view.recordings;
  $('wt-invite').hidden = !view.you_lead;
  $('wt-own').hidden = !!view.removed;
  wtAsked(view);
  if (view.removed) wtSaid(t('team.page.removed'));
}

/* off: Invite others and Join a project, or Start working together again for a team kept with others on it */
function wtStartDraw(on, unlisted = false) {
  $('wt-start').hidden = on;
  const kept = !!(WT.start && WT.start.kept);
  // a join begun here and not finished, its card closed or the app quit since: Finish it or Stop joining
  const pending = ((WT.start && WT.start.joining) || [])[0] || null;
  WT.pending = pending;
  $('wt-start-new').hidden = kept || unlisted || !!pending;
  $('wt-start-join-row').hidden = (kept && !unlisted) || !!pending;
  $('wt-again-row').hidden = !kept || !!pending;
  $('wt-finish-row').hidden = !pending;
  if (pending) {
    // an asking kept by 0.9.32 has no name for the lead: the plain words without one
    // an invite for the researcher's own other computer is finished as adding this computer, not as joining a project
    if (pending.own) {
      $('wt-finish').textContent = t('team.page.finish_own');
      $('wt-finish-line').textContent = t('team.join.waiting_own');
    } else {
      $('wt-finish').textContent = pending.from ? t('team.page.finish', { name: pending.from })
        : t('team.page.finish_unnamed');
      $('wt-finish-line').textContent = pending.from ? t('team.join.waiting', { name: pending.from })
        : t('team.join.waiting_unnamed');
    }
  }
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
    // a member who stopped working together, told to the lead, who then removes them (teamsmall)
    if (person.stopped && view.you_lead) parts.push(t('team.page.stopped'));
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
  // each open invite this computer made, a row of its own: once answered, Check the six digits, and Cancel the invite
  if (!view.removed) for (const inv of view.invites || []) list.appendChild(wtInviteRow(inv));
}

function wtInviteRow(inv) {
  const got = WT.answered[inv.invite];
  const li = document.createElement('li');
  li.className = 'wt-invite-row';
  const who = document.createElement('span');
  who.className = 'wt-who';
  const name = document.createElement('b');
  if (got) name.textContent = inv.own ? t('team.page.invite_answered_own') : t('team.page.invite_answered', { name: got.name });
  else name.textContent = inv.own ? t('team.page.invite_row_own') : t('team.page.invite_row');
  who.appendChild(name);
  const acts = document.createElement('span');
  acts.className = 'wt-btns';
  if (got) acts.appendChild(wtButton(t('team.page.check_digits'), () => wtReopen(inv, got)));
  acts.appendChild(wtButton(t('team.page.cancel_invite'), () => wtCancelInvite(inv)));
  li.append(who, acts);
  return li;
}

/* Cancel the invite: asked first, then given up, so an answer to it is never taken in */
async function wtCancelInvite(inv) {
  if (!await askSure(t('team.page.cancel_invite_ask'))) return;
  const got = await wtCall({ op: 'cancel', invite: inv.invite });
  if (!got) return;
  delete WT.answered[inv.invite];
  if (WT.invite === inv.invite) { wtStop(); WT.invite = null; hide('wt-invite-card'); }
  if (WT.view) wtPeople(WT.view);
  wtPageLook();
}

/* Check the six digits: the invite's card again at the digits and They match, for an invite whose card was closed */
function wtReopen(inv, got) {
  WT.invite = inv.invite;
  $('wt-invite-kicker').textContent = (WT.p && WT.p.name) || '';
  $('wt-invite-title').textContent = inv.own ? t('team.invite.heading_own') : t('team.invite.heading');
  wtInviteParts(false);
  wtInviteSaid('');
  $('wt-rs').hidden = true;
  $('wt-route-now').hidden = true;
  wtStop();
  wtInviteDigits(got);
  show('wt-invite-card');
}

/* the invite's link and words, shown on a new invite and put away on one come back to for its digits */
function wtInviteParts(shown) {
  ['wt-link-h', 'wt-link', 'wt-words-h', 'wt-words'].forEach((id) => { $(id).hidden = !shown; });
  ['wt-copy-link', 'wt-copy-words'].forEach((id) => { $(id).parentNode.hidden = !shown; });
}

/* the six digits, and who answered, with They differ and They match */
function wtInviteDigits(got) {
  $('wt-code').textContent = got.code;
  const own = !!got.own || !!((WT.view && WT.view.invites) || []).find((i) => i.invite === WT.invite && i.own);
  $('wt-answer-line').textContent = own ? t('team.invite.answered_own') : t('team.invite.answered', { name: got.name });
  $('wt-answered').hidden = false;
  $('wt-invite-acts').hidden = false;
}

/* open invites asked about for their answers while Project settings is open, a row each */
function wtRowsStop() {
  clearInterval(WT.rowPoll);
  WT.rowPoll = null;
}

function wtRowsWatch() {
  wtRowsStop();
  const look = async () => {
    if ($('projset').hidden || !WT.view || !WT.view.on || !(WT.view.invites || []).length) return;
    const p = WT.p;
    const got = await wtLookAnswers(p, WT.view);
    if (!got || WT.p !== p) return;
    WT.answered = got;
    if (WT.view) wtPeople(WT.view);
  };
  look();
  WT.rowPoll = setInterval(look, WT_ROWS_MS);
}

/* which of a project's open invites have been answered: {invite id: {name, code, own}}. One that cannot be asked about
   just now, or has lapsed, is left out. Null when the project cannot be reached. */
async function wtLookAnswers(p, view) {
  let shown = view;
  if (!shown) {
    try {
      shown = (await api('/api/team', { ...projectBody(p), op: 'show' })).team || {};
    } catch (err) { return null; }
  }
  const out = {};
  for (const inv of (shown.invites || [])) {
    try {
      const a = await api('/api/team', { ...projectBody(p), op: 'answers', invite: inv.invite });
      if (a.answered) out[inv.invite] = { name: a.name, code: a.code, own: !!a.own };
    } catch (err) { /* lapsed, or no connection just now: no answer shown */ }
  }
  return out;
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

/* Invite others to work on this project: on with this computer as lead, as the tick did, with the researcher's name
   the first time when Settings holds none. Start working together again picks the kept team up as it was, its
   names its own, so it asks for none. */
async function wtStartInvite() {
  if (WT.start && WT.start.kept) {
    await wtCall({ op: 'on' });
    return;
  }
  const typed = $('wt-name').value.trim();
  if (!WT.yourName && !typed) {
    $('wt-name-row').hidden = false;
    $('wt-name').focus();
    return;
  }
  // the name field's change and its OK button can both fire for one press: once is enough
  if (WT.starting) return;
  WT.starting = true;
  try {
    await wtCall({ op: 'on', name: typed || WT.yourName, route: 'relay' });
  } finally { WT.starting = false; }
}

/* Stop working together: asked first in one plain question, then nothing more sent or taken in, the team kept for
   starting again. A member who stops tells the lead, whose People then marks them as having stopped (teamsmall). */
async function wtStopTogether() {
  const view = WT.view || {};
  const lead = (((view.people || []).find((p) => p.lead)) || {}).name || '';
  let ask = t('team.page.stop_ask_alone');
  if (!view.alone) ask = view.you_lead ? t('team.page.stop_ask_lead') : t('team.page.stop_ask_member', { lead });
  if (!await askSure(ask)) return;
  const got = await wtCall({ op: 'off' });
  if (got && WT.p) await wtOpen(WT.p);
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

/* The project's first invite asks how its updates travel before it makes the link: the same two choices as Project
   settings' Send through, opened at the project's own route and folder, and for the folder its path, typed or Choose.
   What is chosen is the project's Send through, written as Project settings writes it (the set op), and only when it
   differs from what the project has. Nothing is turned on, written or sent to the relay before Make the invite. While
   `go` runs the card is locked: no second press, no Cancel, no close, no Escape. A refusal shows its line in the card,
   which stays open. `go(pick, changed)` answers true when the invite is made. (inviteroute, 20 November 2026) */
const wtRouteBody = (pick) => (pick.route === 'folder'
  ? { route: 'folder', folder: pick.folder, folder_must_exist: true } : { route: 'relay' });

/* a call made from the invite's card: its refusal said in the card's own line, never thrown */
async function wtCardCall(body) {
  try {
    const got = await api('/api/team', wtBody(body));
    if (got.team) wtDraw(got.team);
    return got;
  } catch (err) {
    wtInviteSaid(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err));
    return null;
  }
}

function wtStep(own, initial, go) {
  WT.invite = null;
  wtStop();
  WT.busy = false;
  $('wt-invite-kicker').textContent = (WT.p && WT.p.name) || '';
  $('wt-invite-title').textContent = own ? t('team.invite.heading_own') : t('team.invite.heading');
  wtInviteParts(false);
  wtInviteSaid('');
  $('wt-answered').hidden = true;
  $('wt-invite-acts').hidden = true;
  $('wt-route-now').hidden = true;
  const opts = document.querySelectorAll('#wt-rs-route .th-from-opt');
  const choose = (route) => {
    opts.forEach((b) => {
      const here = b.dataset.route === route;
      b.classList.toggle('on', here);
      b.setAttribute('aria-checked', here ? 'true' : 'false');
    });
    $('wt-rs-path').hidden = route !== 'folder';
  };
  const current = () => document.querySelector('#wt-rs-route .th-from-opt.on').dataset.route;
  const lock = (on) => {
    WT.busy = on;
    ['wt-rs-go', 'wt-rs-cancel', 'wt-rs-choose', 'wt-invite-close', 'wt-rs-folder'].forEach((id) => { $(id).disabled = on; });
    opts.forEach((b) => { b.disabled = on; });
  };
  opts.forEach((b) => { b.onclick = () => { if (!WT.busy) choose(b.dataset.route); }; });
  const first = initial.route === 'folder' ? 'folder' : 'relay';
  $('wt-rs-folder').value = initial.folder || '';
  lock(false);
  choose(first);
  $('wt-rs-cancel').onclick = () => { if (!WT.busy) hide('wt-invite-card'); };
  $('wt-rs-choose').onclick = async () => {
    if (WT.busy) return;
    try {
      await picking(async (path) => {
        const folder = path || (await api('/api/team', wtBody({ op: 'pick' }))).folder;
        if (folder) $('wt-rs-folder').value = folder;
        return { chosen: !!folder };
      }, $('wt-rs-choose'), t('team.page.folder'));
    } catch (err) { wtInviteSaid(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err)); }
  };
  $('wt-rs-go').onclick = async () => {
    if (WT.busy) return;
    const route = current();
    const folder = $('wt-rs-folder').value.trim();
    if (route === 'folder' && !folder) { wtInviteSaid(t('team.refused.no_folder'), true); return; }
    wtInviteSaid('');
    const pick = { route, folder: route === 'folder' ? folder : '' };
    const changed = route !== first || (route === 'folder' && folder !== (initial.folder || ''));
    lock(true);
    let ok = false;
    try { ok = await go(pick, changed); } finally { lock(false); }
  };
  $('wt-rs').hidden = false;
  show('wt-invite-card');
}

/* the link and words shown on the card once an invite is made */
function wtInviteShow(got, own) {
  WT.invite = got.invite;
  $('wt-invite-kicker').textContent = (WT.p && WT.p.name) || '';
  $('wt-invite-title').textContent = own ? t('team.invite.heading_own') : t('team.invite.heading');
  $('wt-link').textContent = got.link;
  $('wt-words').textContent = got.words;
  $('wt-answered').hidden = true;
  $('wt-invite-acts').hidden = true;
  $('wt-rs').hidden = true;
  wtInviteParts(true);
  wtInviteSaid('');
  wtRouteNow(got.team || WT.view);
  show('wt-invite-card');
  wtStop();
  WT.poll = setInterval(wtAnswers, WT_POLL_MS);
}

async function wtMakeInvite(own) {
  const got = await wtCardCall({ op: 'invite', own });
  if (!got) return false;
  wtInviteShow(got, own);
  return true;
}

/* the one line a later invite carries: the project's route, and for the lead the way to change it */
function wtRouteNow(view) {
  const v = view || WT.view || {};
  const lead = ((v.people || []).find((x) => x.lead) || {}).name || '';
  const folder = v.folder || '';
  const text = v.you_lead
    ? (v.route === 'folder' ? t('team.invite.route_folder', { folder }) : t('team.invite.route_relay'))
    : (v.route === 'folder' ? t('team.invite.route_folder_lead', { folder, name: lead })
      : t('team.invite.route_relay_lead', { name: lead }));
  $('wt-route-now-text').textContent = text;
  $('wt-route-change').hidden = !v.you_lead;
  $('wt-route-now').hidden = false;
}

/* Change in Project settings: the card put away and Project settings opened at Send through, scrolled there once the
   section is drawn */
function wtRouteChange() {
  const p = WT.p;
  if (WT.busy) return;
  wtStop();
  hide('wt-invite-card');
  if (!p) return;
  WT.scrollTo = () => { const at = $('wt-route'); if (at && at.scrollIntoView) at.scrollIntoView({ block: 'center' }); };
  openProjectSettings(p);
}

/* an invite from Project settings, Working together on: the first one asks the route first */
async function wtInvite(own) {
  const v = WT.view || {};
  if (v.first_invite) {
    wtStep(own, { route: v.route, folder: v.folder }, async (pick, changed) => {
      if (changed && !await wtCardCall({ op: 'set', ...wtRouteBody(pick) })) return false;
      return wtMakeInvite(own);
    });
    return;
  }
  const got = await wtCall({ op: 'invite', own });
  if (!got) return;
  wtInviteShow(got, own);
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
  wtInviteDigits(got);
}

async function wtAnswer(match) {
  try {
    const got = await api('/api/team', wtBody({ op: 'admit', invite: WT.invite, match }));
    if (got.team) wtDraw(got.team);
  } catch (err) { wtInviteSaid(err.message, true); return; }
  if (match) { delete WT.answered[WT.invite]; WT.invite = null; hide('wt-invite-card'); wtPageLook(); return; }
  // They differ: the answer thrown away, the invite still open for the right answer
  delete WT.answered[WT.invite];
  wtPageLook();
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

/* ── joining another's project, from this one while Working together is off ── */

function wtJoinSaid(text, failed = false) {
  saidIn('wt-join-said', text || '', failed);
  $('wt-join-said').hidden = !text;
}

/* Join a project you were invited to: the card at once, nothing turned on until They match. A project holding a
   participant the invite does not list is refused in the card's line, since it would become the lead's. */
function wtJoinOpen() {
  wtSaid('');
  $('wt-join-kicker').textContent = WT.p.name || '';
  $('wt-join-words').value = '';
  $('wt-join-words').disabled = false;
  $('wt-join-name').value = '';
  $('wt-join-name').disabled = false;
  $('wt-join-name-row').hidden = !!WT.yourName;
  $('wt-join-folder-on').checked = false;
  $('wt-join-folder-on').disabled = false;
  WT.joinFolder = '';
  wtJoinFolderDraw();
  wtJoinAsking(true);
  $('wt-join-answered').hidden = true;
  $('wt-join-acts').hidden = false;
  wtJoinSaid('');
  show('wt-join-card');
}

/* the shared folder the invite came through, ticked in the Join card, with its own Choose */
function wtJoinFolderDraw() {
  // a link that says its route asks no tick: the shared folder only for a folder invite (teamjoin)
  const via = hjVia($('wt-join-words').value);
  document.querySelector('#wt-join-card .wt-join-by').hidden = !!via || $('wt-join-words').hidden;
  const by = via ? via === 'folder' : $('wt-join-folder-on').checked;
  $('wt-join-path').hidden = !by;
  if (WT.joinFolder) $('wt-join-folder').innerHTML = pathHtml(WT.joinFolder);
  else $('wt-join-folder').textContent = t('team.page.no_folder');
}

/* Choose in the Join card: the system's dialog on the app's own window, or the Mac's from the server, its folder
   kept in the card and nothing written until the join */
async function wtJoinChoose() {
  const keep = (folder) => { if (folder) WT.joinFolder = folder; wtJoinFolderDraw(); return { chosen: !!folder }; };
  try {
    await picking(async (path) => keep(path || (await api('/api/team', wtBody({ op: 'pick' }))).folder),
      $('wt-join-choose'), t('team.page.folder'));
  } catch (err) { wtJoinSaid(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err)); }
}

async function wtJoin() {
  const asked = { op: 'join', words: $('wt-join-words').value };
  const typed = $('wt-join-name').value.trim();
  if (typed) asked.name = typed;
  // Join beside "This computer is not on this project's list" says the project is a copy
  if ((WT.view && WT.view.unlisted) || (WT.start && WT.start.unlisted)) asked.copy = true;
  const via = hjVia(asked.words);
  Object.assign(asked, (via ? via === 'folder' : $('wt-join-folder-on').checked)
    ? { route: 'folder', folder: WT.joinFolder } : { route: 'relay' });
  let got;
  try {
    try {
      got = await api('/api/team', wtBody(asked));
    } catch (err) {
      // the invite is another team's and this project's list names others: asked once, and the join goes ahead only on yes
      if (!refusedAs(err, 'replace_team')) throw err;
      if (!await askSure(err.message.split('\n')[0])) { wtJoinSaid(''); return; }
      got = await api('/api/team', wtBody(Object.assign(asked, { replace: true })));
    }
  } catch (err) { wtJoinSaid(err.message, true); return; }
  if (typed) WT.yourName = typed;
  wtJoinWaiting(got);
}

/* the card as it stands once the answer is sent: the six digits to read out, then waiting for They match */
function wtJoinWaiting(got) {
  WT.joining = { invite: got.invite, from: got.from || '', own: !!got.own, project: got.project || '' };
  $('wt-join-words').disabled = true;
  $('wt-join-name').disabled = true;
  $('wt-join-folder-on').disabled = true;
  $('wt-join-acts').hidden = true;
  $('wt-join-code').textContent = got.code;
  // an invite for the researcher's own other computer: the digits are checked against that computer, not read out
  // to someone on a call (teamsmall, friction 8)
  if (got.own) $('wt-join-line').textContent = t('team.join.read_code_own');
  else $('wt-join-line').textContent = t('team.join.read_code', { name: got.from || '' });
  $('wt-join-answered').hidden = false;
  if (got.own) wtJoinSaid(t('team.join.waiting_own'));
  else wtJoinSaid(got.from ? t('team.join.waiting', { name: got.from }) : t('team.join.waiting_unnamed'));
  wtStop();
  WT.poll = setInterval(wtJoined, WT_POLL_MS);
}

/* Finish joining: the card again for a join begun here and left, at the six digits, waiting */
function wtFinish() {
  const pending = WT.pending;
  if (!pending) return;
  wtJoinOpen();
  wtJoinWaiting({ invite: pending.invite, from: pending.from, own: pending.own, project: pending.project, code: pending.code });
  // what was typed is not asked for again: the card holds the six digits and the waiting alone
  wtJoinAsking(false);
}

/* the card's asking part, the words, the name and the shared folder, shown or put away */
function wtJoinAsking(shown) {
  document.querySelectorAll('#wt-join-card label[for="wt-join-words"], #wt-join-words, #wt-join-card .wt-join-by,'
    + ' #wt-join-path').forEach((el) => { el.hidden = !shown; });
  $('wt-join-name-row').hidden = true;
  if (shown) { $('wt-join-name-row').hidden = !!WT.yourName; wtJoinFolderDraw(); }
}

/* Stop joining: the asking and its keys dropped on this computer, the section as it was before the join */
async function wtFinishStop() {
  const pending = WT.pending;
  if (!pending) return;
  try {
    await api('/api/team', wtBody({ op: 'unjoin', invite: pending.invite }));
  } catch (err) { wtSaid(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err)); return; }
  wtOpen(WT.p);
}

async function wtJoined() {
  if (!WT.joining || $('wt-join-card').hidden) { wtStop(); return; }
  let got;
  try {
    got = await api('/api/team', wtBody({ op: 'joined', invite: WT.joining.invite }));
  } catch (err) { wtStop(); wtJoinSaid(err.message, true); return; }
  if (!got.joined) return;
  wtStop();
  // on a second computer's join the line names the project, not the one whose invite it was (teamsmall, friction 8)
  if (WT.joining.own) wtJoinSaid(t('team.join.joined_own', { project: WT.joining.project || (WT.p && WT.p.name) || '' }));
  else wtJoinSaid(t('team.join.joined', { name: WT.joining.from }));
  WT.joining = null;
  if (got.team) wtDraw(got.team);
}

function wtWire() {
  if (!$('wt-block')) return;
  $('wt-start-invite').onclick = wtStartInvite;
  $('wt-again').onclick = wtStartInvite;
  $('wt-start-join').onclick = wtJoinOpen;
  $('wt-finish').onclick = wtFinish;
  $('wt-finish-stop').onclick = wtFinishStop;
  $('wt-stop').onclick = wtStopTogether;
  $('wt-name-ok').onclick = wtStartInvite;
  $('wt-name').addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); wtStartInvite(); } });
  $('wt-name').addEventListener('change', () => { if ($('wt-name').value.trim()) wtStartInvite(); });
  $('wt-join-folder-on').addEventListener('change', wtJoinFolderDraw);
  $('wt-join-words').addEventListener('input', wtJoinFolderDraw);
  $('wt-join-choose').onclick = wtJoinChoose;
  document.querySelectorAll('#wt-route .th-from-opt').forEach((b) => {
    b.onclick = () => { if (!b.classList.contains('on')) wtSet({ route: b.dataset.route }); };
  });
  $('wt-choose').onclick = wtChoose;
  $('wt-recordings').addEventListener('change', () => wtSet({ recordings: $('wt-recordings').checked }));
  $('wt-invite').onclick = () => wtInvite(false);
  $('wt-own').onclick = () => wtInvite(true);
  $('wt-copy-link').onclick = () => wtCopy('wt-link');
  $('wt-copy-words').onclick = () => wtCopy('wt-words');
  $('wt-match').onclick = () => wtAnswer(true);
  $('wt-differ').onclick = () => wtAnswer(false);
  $('wt-invite-close').onclick = () => { if (WT.busy) return; wtStop(); hide('wt-invite-card'); };
  // while the first invite's step is at work the card cannot be put away
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && WT.busy) { e.preventDefault(); e.stopImmediatePropagation(); }
  }, true);
  $('wt-route-change').onclick = wtRouteChange;
  $('wt-join-close').onclick = () => {
    wtStop();
    hide('wt-join-card');
    // a join left waiting is offered again in the section, to finish or to stop
    if (WT.joining) { WT.joining = null; wtOpen(WT.p); }
  };
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
  WT.pageTeam = team;
  // the lead's page asks about the answers to its open invites; Invite others is the lead's, or anyone's before a team
  // is on, never a member's
  if (!team || !team.lead) { clearInterval(WT.pageTimer); WT.pageTimer = null; WT.pageAnswered = {}; }
  if (team && !team.lead && $('hp-invite')) $('hp-invite').hidden = true;
  if (!team) return;
  if (team.lead && !WT.pageTimer) wtPageWatch();
  const tags = team.tags || {};
  $('hp-list').querySelectorAll(':scope > li.prow').forEach((li) => {
    const tag = tags[li.dataset.case];
    // at the end of the row's head, after its other tags (homecardbuild took the dots away)
    const head = li.querySelector('.pc-head');
    if (!tag || !head) return;
    const span = document.createElement('span');
    span.className = tag.owner ? 'tag wt-own' : 'tag wt-rev';
    span.textContent = tag.owner ? t('team.page.tag_owner', { name: tag.owner }) : t('team.page.tag_review', { name: tag.review });
    head.appendChild(span);
  });
  const said = [];
  for (const came of team.arrivals || []) {
    const at = tTime(came.at);
    said.push(['', WT_DOWN, came.gets ? t('team.page.came_in_gets', { name: came.name, time: at })
      : t('team.page.came_in', { name: came.name, participant: came.participant, time: at })]);
  }
  // what was handed to this member today, and the invites that have been answered (teamsmall)
  for (const gave of team.gave || []) {
    said.push(['', WT_DOWN, gave.gets ? t('team.page.gave_gets', { name: gave.name })
      : t('team.page.gave', { name: gave.name, participant: gave.participant })]);
  }
  for (const [inv, got] of Object.entries(WT.pageAnswered || {})) {
    said.push(['wt-answered-line', WT_DOWN, got.own ? t('team.page.answered_line_own') : t('team.page.answered_line', { name: got.name }),
      { label: t('team.page.check_digits'), run: () => wtPageReopen(inv, got) }]);
  }
  // why what waits has not gone: the relay's own reason in its line (relayopen), else no connection. The lead's line
  // for a project the relay no longer has carries Start it again, and says its refusal in its place (relayrestart)
  if (!team.restart && !WT.pageRestartNote) WT.pageRestartSaid = '';
  if (team.held) said.push(['wt-wait', WT_UP, (team.restart && WT.pageRestartSaid) || team.held,
    team.restart ? { label: t('team.page.restart'), run: (e) => wtPageRestart(e && e.currentTarget) } : null]);
  else if (WT.pageRestartNote && WT.pageRestartSaid) said.push(['wt-wait', WT_UP, WT.pageRestartSaid]);
  else if (team.offline && team.waiting > 0) said.push(['wt-wait', WT_UP, t('team.page.waiting', { n: team.waiting })]);
  WT.pageRestartNote = false;
  if (team.too_large) said.push(['wt-wait', WT_UP, team.too_large]);
  for (const [cls, icon, text, action] of said) {
    const span = document.createElement('span');
    if (cls) span.className = cls;
    span.innerHTML = icon;
    span.append(text);
    if (action) {
      span.append(' ');
      span.appendChild(wtButton(action.label, action.run));
    }
    lines.appendChild(span);
  }
  lines.hidden = !said.length;
}

/* ── Join a project on Home (teamjoin, 20 November 2026, Adam's rulings after teamflow's drawings p1, p2 and p5) ──
   Beside New project, with no project of his made first: the link or the words, read as soon as they are twelve
   (`offer`) for who sent it and the project's name, which names the folder offered, ~/Documents/Idiograph/<project>.
   A link says the route its invite went by, so the shared folder is asked only for a folder invite, and the tick
   "The invite came through a shared folder" shows only for words with no link saying it. His name only when
   Settings has none and the invite is not for another computer of his. Join makes the folder and the project and
   joins into it (`join` with `into`), then the six digits and the wait, and at the end Open <the project>. */
const HJ = { offer: null, read: '', timer: null, poll: null, joining: null, root: '', project: '', yourName: '',
  intoTyped: false };

function hjSaid(text, failed = false) {
  saidIn('hj-said', text || '', failed);
  $('hj-said').hidden = !text;
}

/* the route a link says its invite went by, '' for typed words or a link made before links said it */
function hjVia(text) {
  const head = String(text || '').trim().split('#')[0];
  const at = head.indexOf('?');
  if (at < 0) return '';
  const via = new URLSearchParams(head.slice(at + 1)).get('via') || '';
  return via === 'relay' || via === 'folder' ? via : '';
}

/* twelve words, after a link's # or typed */
function hjWhole(text) {
  const words = String(text || '').split('#').pop().split(/[\s,-]+/).filter(Boolean);
  return words.length === 12;
}

function hjRoute() {
  const via = hjVia($('hj-words').value);
  return via || ($('hj-folder-on').checked ? 'folder' : 'relay');
}

/* the rows the words ask for: the tick only with no route said, the shared folder only for a folder invite, the
   name only when Settings has none and the invite is not for another computer of his */
function hjDraw() {
  const via = hjVia($('hj-words').value);
  $('hj-by-row').hidden = !!via;
  $('hj-folder-row').hidden = hjRoute() !== 'folder';
  const own = !!(HJ.offer && HJ.offer.own);
  $('hj-own').hidden = !own;
  // who invites you, once the invite is read: not for another computer of his own, which has its own line
  const offer = HJ.offer && !own ? HJ.offer : null;
  $('hj-offer').textContent = !offer ? '' : offer.project
    ? t('team.home.offer', { name: offer.from || '', project: offer.project })
    : t('team.home.offer_unnamed', { name: offer.from || '' });
  $('hj-offer').hidden = !offer || !offer.from;
  $('hj-name-row').hidden = !!HJ.yourName || own;
}

async function hjOpen() {
  hjStop();
  Object.assign(HJ, { offer: null, read: '', joining: null, root: '', project: '', intoTyped: false });
  for (const id of ['hj-words', 'hj-folder', 'hj-name', 'hj-into']) { $(id).value = ''; $(id).disabled = false; }
  for (const id of ['hj-folder-on', 'hj-folder-choose', 'hj-into-choose']) $(id).disabled = false;
  $('hj-folder-on').checked = false;
  $('hj-answered').hidden = true;
  $('hj-acts').hidden = false;
  $('hj-done').hidden = true;
  hjSaid('');
  hjDraw();
  show('hj-card');
  try {
    const got = await api('/api/team', { op: 'offer' });
    HJ.yourName = got.your_name || '';
    if (!HJ.intoTyped && !$('hj-into').value) $('hj-into').value = got.into || '';
  } catch (err) { hjSaid(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err)); }
  hjDraw();
}

/* the invite read once its words are whole, for the project's name and whether it is for a computer of his */
function hjChanged() {
  hjDraw();
  clearTimeout(HJ.timer);
  HJ.timer = setTimeout(hjRead, 400);
}

async function hjRead() {
  const words = $('hj-words').value.trim();
  const route = hjRoute();
  const folder = $('hj-folder').value.trim();
  const key = `${words}\n${route}\n${folder}`;
  if (!hjWhole(words) || (route === 'folder' && !folder) || key === HJ.read || HJ.joining) return;
  HJ.read = key;
  let got;
  try {
    got = await api('/api/team', { op: 'offer', words, route, ...(folder ? { folder } : {}) });
  } catch (err) {
    // a read overtaken by other words or by Join says nothing
    if (HJ.read === key) { HJ.offer = null; hjDraw(); hjSaid(err.message, true); }
    return;
  }
  if (HJ.read !== key) return;
  HJ.offer = got;
  HJ.yourName = got.your_name || HJ.yourName;
  if (!HJ.intoTyped) $('hj-into').value = got.into || $('hj-into').value;
  hjSaid('');
  hjDraw();
}

/* Choose beside a path: the system's dialog on the app's own window, or the Mac's from the server, its folder put in
   the field and nothing written. For where to keep the project, the project's own folder goes inside the one chosen */
async function hjChoose(field, btn, inside) {
  const keep = (folder) => {
    if (folder) {
      const leaf = inside ? $(field).value.trim().replace(/[\\/]+$/, '').split(/[\\/]/).pop() : '';
      $(field).value = leaf ? `${folder.replace(/[\\/]+$/, '')}/${leaf}` : folder;
      if (inside) HJ.intoTyped = true;
      else hjChanged();
    }
    return { chosen: !!folder };
  };
  try {
    await picking(async (path) => keep(path || (await api('/api/team', { op: 'pick', home: true })).folder),
      $(btn), t('team.home.keep_in'));
  } catch (err) { hjSaid(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err)); }
}

async function hjGo() {
  clearTimeout(HJ.timer);
  HJ.read = '';
  const route = hjRoute();
  const asked = { op: 'join', words: $('hj-words').value, into: $('hj-into').value.trim(), route };
  const typed = $('hj-name').value.trim();
  if (typed && !$('hj-name-row').hidden) asked.name = typed;
  if (route === 'folder') asked.folder = $('hj-folder').value.trim();
  $('hj-go').disabled = true;
  let got;
  try {
    got = await api('/api/team', asked);
  } catch (err) { hjSaid(needsRestart(err) ? RESTART_LINE : err.message, !needsRestart(err)); return; } finally {
    $('hj-go').disabled = false;
  }
  HJ.root = (got.project && got.project.id) || '';
  HJ.project = (got.project && got.project.name) || '';
  HJ.joining = { invite: got.invite, from: got.from || '', own: !!got.own };
  for (const id of ['hj-words', 'hj-folder', 'hj-name', 'hj-into', 'hj-folder-on', 'hj-folder-choose', 'hj-into-choose']) {
    $(id).disabled = true;
  }
  $('hj-acts').hidden = true;
  $('hj-code').textContent = got.code;
  $('hj-line').textContent = got.own ? t('team.join.read_code_own') : t('team.join.read_code', { name: got.from || '' });
  $('hj-answered').hidden = false;
  if (got.own) hjSaid(t('team.join.waiting_own'));
  else hjSaid(got.from ? t('team.join.waiting', { name: got.from }) : t('team.join.waiting_unnamed'));
  // the project is on Home now, behind the card
  loadLibrary(false).catch(() => {});
  hjStop();
  HJ.poll = setInterval(hjJoined, WT_POLL_MS);
}

function hjStop() {
  if (HJ.poll) clearInterval(HJ.poll);
  HJ.poll = null;
}

async function hjJoined() {
  if (!HJ.joining || $('hj-card').hidden) { hjStop(); return; }
  let got;
  try {
    got = await api('/api/team', { root: HJ.root, op: 'joined', invite: HJ.joining.invite });
  } catch (err) {
    hjStop(); hjSaid(err.message, true);
    // a join that has ended takes the empty project it made away again: Home lists what is left
    loadLibrary(false).catch(() => {});
    return;
  }
  if (!got.joined) return;
  hjStop();
  const project = HJ.project || t('team.home.default_project');
  if (HJ.joining.own) hjSaid(t('team.home.joined_own', { project }));
  else if (HJ.joining.from) hjSaid(t('team.home.joined', { project, name: HJ.joining.from }));
  else hjSaid(t('team.home.joined_unnamed', { project }));
  HJ.joining = null;
  $('hj-answered').hidden = true;
  $('hj-project').textContent = t('team.home.open', { project });
  $('hj-done').hidden = false;
}

/* Open <the project>: its page, as New project opens the one it made */
function hjOpenProject() {
  hjStop();
  hide('hj-card');
  if (HJ.root) homeKeep(HJ.root);
  loadLibrary().catch((err) => say(err.message, 9000));
}

function hjWire() {
  if (!$('hj-open') || !$('hj-card')) return;
  $('hj-open').onclick = hjOpen;
  $('hj-words').addEventListener('input', hjChanged);
  $('hj-folder').addEventListener('input', hjChanged);
  $('hj-folder-on').addEventListener('change', hjChanged);
  $('hj-into').addEventListener('input', () => { HJ.intoTyped = true; });
  $('hj-folder-choose').onclick = () => hjChoose('hj-folder', 'hj-folder-choose', false);
  $('hj-into-choose').onclick = () => hjChoose('hj-into', 'hj-into-choose', true);
  $('hj-go').onclick = hjGo;
  $('hj-project').onclick = hjOpenProject;
  $('hj-close').onclick = () => {
    hjStop();
    hide('hj-card');
    // a join left waiting is offered again in its project's settings, to finish or to stop
    if (HJ.root) loadLibrary(false).catch(() => {});
  };
}

hjWire();

/* ── Invite others on the project's page (teamsmall, friction 5, p3) ── */

/* The project the page shows: its id and name as Project settings takes it */
function wtPageProject() {
  return (typeof HOME_PROJECTS !== 'undefined' && typeof S !== 'undefined' && HOME_PROJECTS.get(S.home))
    || ((typeof homeProject === 'function' ? homeProject() : null) || {}).project || null;
}

/* the page asks about the answers to its open invites now and every 30 seconds while it is open: "Bo has answered
   your invite", with Check the six digits */
function wtPageWatch() {
  clearInterval(WT.pageTimer);
  WT.pageTimer = setInterval(wtPageLook, WT_ROWS_MS);
  wtPageLook();
}

async function wtPageLook() {
  const team = WT.pageTeam;
  const box = $('home-project');
  if (!team || !team.lead || !box || box.hidden) { clearInterval(WT.pageTimer); WT.pageTimer = null; return; }
  const p = wtPageProject();
  if (!p || !p.id) return;
  const got = await wtLookAnswers(p);
  if (!got || WT.pageTeam !== team) return;
  const was = Object.keys(WT.pageAnswered || {}).sort().join();
  WT.pageAnswered = got;
  if (Object.keys(got).sort().join() !== was) wtPageDraw(team);
}

/* Start it again, on the lead's line for a project the relay no longer has (relayrestart, 21 November 2026): the
   project made there again under its id, with the same people, then the page's lines as they now stand. A refusal
   is said in the line's place, the button kept for another try. */
async function wtPageRestart(button) {
  const p = wtPageProject();
  if (!p || !p.id || WT.pageRestarting) return;
  WT.p = p;
  WT.pageRestarting = true;
  if (button) button.disabled = true;
  try {
    const got = await api('/api/team', wtBody({ op: 'restart' }));
    // a project the relay kept no record of: its line says what to do next, shown once in the line's place
    WT.pageRestartSaid = got.said || '';
    WT.pageRestartNote = !!got.said;
  } catch (err) {
    WT.pageRestartSaid = needsRestart(err) ? RESTART_LINE : err.message;
  } finally {
    WT.pageRestarting = false;
    if (button) button.disabled = false;
  }
  try {
    wtPageDraw((await api('/api/team', wtBody({ op: 'show' }))).sync || null);
  } catch (err) { wtPageDraw(WT.pageTeam); }
}

/* Check the six digits from the page's line: the invite's card at the digits, for this project */
function wtPageReopen(inv, got) {
  const p = wtPageProject();
  if (!p) return;
  WT.p = p;
  wtReopen({ invite: inv, own: !!got.own }, got);
}

/* Invite others: one press turns Working together on with this computer as lead if it is off, asks for a name only
   when Settings holds none, and opens the invite's card. A project that cannot start that way here (a join begun
   and not finished, a computer the list does not name) opens Project settings, where the section says why. */
async function wtPageInvite(p) {
  if (!p || p.demo || !p.id) return;
  WT.p = p;
  let got;
  try {
    got = await api('/api/team', wtBody({ op: 'show' }));
  } catch (err) { openProjectSettings(p); return; }
  WT.yourName = got.your_name || '';
  WT.start = got.start || null;
  const team = got.team || { on: false };
  if (team.on && !team.unlisted) {
    if (!team.you_lead) { openProjectSettings(p); return; }
    WT.view = team;
    await wtInvite(false);
    return;
  }
  if (team.unlisted || ((WT.start && WT.start.joining) || []).length) { openProjectSettings(p); return; }
  const kept = !!(WT.start && WT.start.kept);
  let name = WT.yourName;
  if (!kept && !name) {
    name = await wtAskName(p.name || '');
    if (!name) return;
  }
  const refresh = async () => {
    // the page's own lines and tags as they now stand
    try {
      wtPageDraw((await api('/api/team', wtBody({ op: 'show' }))).sync || null);
    } catch (err) { /* the page keeps its lines until it is opened again */ }
  };
  if (kept) {
    // a team kept with others is picked up as it was: its route is its own, nothing asked
    const on = await wtCall({ op: 'on' });
    if (!on) { openProjectSettings(p); return; }
    await refresh();
    await wtInvite(false);
    return;
  }
  // the first invite is where the project's way of sending updates is chosen: before anything is turned on or
  // written, and turned back off if the press cannot finish (inviteroute)
  const start = WT.start || {};
  wtStep(false, { route: start.route, folder: start.folder }, async (pick) => {
    const on = await wtCardCall({ op: 'on', name, ...wtRouteBody(pick) });
    if (!on) return false;
    if (name) WT.yourName = name;
    // a team kept alone keeps its own route, which `on` leaves as it was: the choice is then set as Project settings sets it
    const view = on.team || {};
    const differs = pick.route !== (view.route || 'relay') || (pick.route === 'folder' && pick.folder !== view.folder);
    let ok = !differs || !!await wtCardCall({ op: 'set', ...wtRouteBody(pick) });
    if (ok) ok = await wtMakeInvite(false);
    if (!ok) {
      const said = $('wt-invite-said').textContent;
      const failed = !$('wt-invite-said').hidden;
      await wtCardCall({ op: 'off' });
      if (failed) wtInviteSaid(said, true);
    }
    await refresh();
    return ok;
  });
}

/* Your name, once, in a small card with OK: Return does the same */
function wtAskName(kicker) {
  return new Promise((resolve) => {
    $('wt-name-kicker').textContent = kicker || '';
    $('wt-name-page').value = '';
    const done = (name) => { hide('wt-name-card'); resolve(name); };
    $('wt-name-go').onclick = () => { const name = $('wt-name-page').value.trim(); if (name) done(name); };
    $('wt-name-cancel').onclick = () => done('');
    $('wt-name-page').onkeydown = (e) => {
      if (e.key === 'Enter') { e.preventDefault(); $('wt-name-go').click(); }
      if (e.key === 'Escape') { e.preventDefault(); done(''); }
    };
    show('wt-name-card');
    $('wt-name-page').focus();
  });
}
