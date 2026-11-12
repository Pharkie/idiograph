// The screens the pixel check shoots (i18ncore, 28 October 2026), by group. A build that moves words into the
// catalogue adds the screens its words show on to a group of its own, and shoots that group before and after: the
// shots must come out identical, pixel for pixel. Each screen starts from Home freshly loaded and puts itself up with
// `open`, a function run in the page (no closure, since it is sent as text). `panes: true` shoots each Settings
// category the page holds, at its top and, where it scrolls, at its end. `wait` is a selector shown before the shot.
// Nothing here presses an AI control or writes a project.

// The zoom groups' steps, each a line of the page's own code, joined into one function by `opener` since a
// screen's function is sent alone. PICKER is Home's list of projects, PAGE the first project's page, WORK its
// first participant on the statements screen, PLAYER the player shown as a recording would show it
const NAP = (ms) => `await new Promise((r) => setTimeout(r, ${ms}));`;
const UNTIL = (test) => `for (let i = 0; i < 100 && !(${test}); i += 1) await new Promise((r) => setTimeout(r, 100));`;
const PICKER = `${UNTIL("document.getElementById('home-project')")}
  if (!document.getElementById('home-project').hidden) document.getElementById('hp-back').click();
  ${UNTIL("document.querySelector('#projects .home-card')")}`;
const PAGE = `${UNTIL("document.querySelector('#projects .home-card') || !document.getElementById('home-project').hidden")}
  if (document.getElementById('home-project').hidden) document.querySelector('#projects .home-card').click();
  ${UNTIL("document.querySelector('#hp-list .pc-dots')")}`;
const WORK = `document.querySelector('#hp-list .pc-es, #hp-list .pc-tp').click();
  ${UNTIL("document.querySelector('#work .turn')")} ${NAP(600)}`;
const PLAYER = `document.getElementById('player-wrap').hidden = false; document.getElementById('player-bar').hidden = false;
  document.getElementById('player-note').textContent = 'Juno - Initial.m4a'; document.getElementById('player-total').textContent = '42:10';`;
const BOARD = (fn) => `await ${fn}(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true; ${NAP(400)}`;
const TRAJ = `for (const id of ['library', 'work', 'themes']) document.getElementById(id).hidden = true;
  document.getElementById('traj').hidden = false;
  trajLoad({ project: S.lib.projects[0].project, demo: false, unplaced: ['a'],
    columns: [{ id: 'c1', title: 'Settling in', participants: ['b'] }, { id: 'c2', title: 'Finding a rhythm', participants: ['c'] }],
    participants: [{ case: 'a', who: 'Wren', colour: 1, lpets: [] },
      { case: 'b', who: 'Finch', colour: 2, lpets: ['A walk at dawn', 'The lead by the door'], column: 'c1', note: '' },
      { case: 'c', who: 'Linnet', colour: 3, lpets: ['Rain on the window'], column: 'c2', note: '' }] });`;
// a review and a Trace project kept in the app's list, as Open project folder keeps one, then opened
const SIFT = "await api('/api/sift-review', { op: 'open', folder: SWEEP.sift }); await siftOpen(SWEEP.sift);";
const TRACE = "await api('/api/trace-project', { op: 'open', folder: SWEEP.trace }); await trOpen(SWEEP.trace);";
const opener = (...lines) => new Function(`return (async () => {\n${lines.join('\n')}\n})();`);

export const SCREENS = {
  // the shell's own screens (shell.js and page.html): Home, every Settings category, About and What's new
  shell: [
    { name: 'home', open: () => {}, wait: '#library' },
    { name: 'settings', open: () => document.getElementById('lib-settings').click(), wait: '#settings', panes: true },
    { name: 'about', open: () => { document.getElementById('lib-settings').click(); document.getElementById('settings-about').click(); }, wait: '#about' },
    { name: 'whatsnew', open: () => window.openWhatsNew(), wait: '#whatsnew' },
  ],
  // Idiograph's own markup (i18npage, apps/idiograph/static/idiograph.html): the project's page, Experiential
  // statements with its menus, guidance, Find and the cards over it, PETs and GETs with theirs, and each card of
  // the page shown as it is drawn. A run with --root opens the project's first participant, never a Demo row
  idiograph: [
    { name: 'project', wait: '#home-project', open: async () => {
      const d = await (await fetch('/api/cases')).json(); await openPage(d.projects[0].id); } },
    { name: 'work', wait: '#work', open: async () => {
      const d = await (await fetch('/api/cases')).json(); await openCase(d.projects[0].cases[0].path); await new Promise((ok) => setTimeout(ok, 800)); } },
    { name: 'work-view', wait: '#view-menu', open: async () => {
      const d = await (await fetch('/api/cases')).json(); await openCase(d.projects[0].cases[0].path); await new Promise((ok) => setTimeout(ok, 800));
      document.getElementById('btn-view').click(); } },
    { name: 'work-columns', wait: '#cols-menu', open: async () => {
      const d = await (await fetch('/api/cases')).json(); await openCase(d.projects[0].cases[0].path); await new Promise((ok) => setTimeout(ok, 800));
      document.getElementById('cols-pick').click(); } },
    { name: 'work-guide', wait: '#guide.open', open: async () => {
      const d = await (await fetch('/api/cases')).json(); await openCase(d.projects[0].cases[0].path); await new Promise((ok) => setTimeout(ok, 800));
      guide(true, {}); } },
    { name: 'work-find', wait: '#find', open: async () => {
      const d = await (await fetch('/api/cases')).json(); await openCase(d.projects[0].cases[0].path); await new Promise((ok) => setTimeout(ok, 800));
      document.getElementById('find').hidden = false; } },
    { name: 'work-help', wait: '#help', open: async () => {
      const d = await (await fetch('/api/cases')).json(); await openCase(d.projects[0].cases[0].path); await new Promise((ok) => setTimeout(ok, 800));
      document.getElementById('btn-help').click(); } },
    { name: 'work-complete', wait: '#complete', open: async () => {
      const d = await (await fetch('/api/cases')).json(); await openCase(d.projects[0].cases[0].path); await new Promise((ok) => setTimeout(ok, 800));
      document.getElementById('complete').hidden = false; } },
    { name: 'work-round', wait: '#round-done', open: async () => {
      const d = await (await fetch('/api/cases')).json(); await openCase(d.projects[0].cases[0].path); await new Promise((ok) => setTimeout(ok, 800));
      document.getElementById('round-done').hidden = false; } },
    { name: 'pets', wait: '#themes', open: async () => {
      const d = await (await fetch('/api/cases')).json(); await openThemes(d.projects[0].cases[0].path, 'home'); await new Promise((ok) => setTimeout(ok, 800)); } },
    { name: 'pets-export', wait: '#th-xmenu', open: async () => {
      const d = await (await fetch('/api/cases')).json(); await openThemes(d.projects[0].cases[0].path, 'home'); await new Promise((ok) => setTimeout(ok, 800));
      document.getElementById('th-export').click(); } },
    { name: 'gets', wait: '#themes', open: async () => {
      const d = await (await fetch('/api/cases')).json(); await openGets(d.projects[0].cases[0].path); } },
    ...['skip-confirm', 'hold-card', 'create', 'rename', 'share-card', 'copy-back', 'offset', 'import', 'newproject',
      'trim', 'gt-trail', 'gt-print', 'th-confirm', 'assign', 'traj'].map((id) => ({
      name: `card-${id}`, wait: `#${id}`,
      open: new Function(`const c = document.getElementById(${JSON.stringify(id)}); c.hidden = false;`),
    })),
  ],
  // the server's words the page shows (i18nserver): a refusal of Idiograph's own on Home's line, Open project folder
  // in a run of one project, and one of the family server's, a request it has no endpoint for
  server: [
    { name: 'refusal-app', open: () => { addProject('/no/such/folder'); }, wait: '#toast:not([hidden])' },
    { name: 'refusal-family', open: () => { api('/api/no-such-endpoint', {}).catch((err) => say(err.message, 60000)); }, wait: '#toast:not([hidden])' },
  ],
  // Idiograph's own words (distil.js, i18ndistil): a project card's menu, Share a copy, a project's page with its
  // rows, a row's menu and Files, New project and Add transcripts, the statements screen and its menus, a passage's
  // menu, Find, and Settings from Home and from the statements screen. A run of one project opens Home
  // on its page: each goes back to the picker for the project card's menu, else stays on the page, never the demo's,
  // and opens the first participant on it, the steps written out in each since a screen's function is sent alone
  distil: [
    { name: 'd-home-menu', wait: '#projects .hc-menu:not([hidden])', open: async () => {
      if (!document.getElementById('home-project').hidden) document.getElementById('hp-back').click();
      for (let i = 0; i < 100 && !document.querySelector('#projects .hc-dots'); i += 1) await new Promise((r) => setTimeout(r, 100));
      document.querySelector('#projects .hc-dots').click();
    } },
    { name: 'd-share', wait: '#share-card', open: async () => {
      if (!document.getElementById('home-project').hidden) document.getElementById('hp-back').click();
      for (let i = 0; i < 100 && !document.querySelector('#projects .hc-dots'); i += 1) await new Promise((r) => setTimeout(r, 100));
      document.querySelector('#projects .hc-dots').click();
      document.querySelector('#projects .hc-menu [data-act="share"]').click();
    } },
    { name: 'd-share-rows', wait: '#sc-rows-below', open: async () => {
      if (!document.getElementById('home-project').hidden) document.getElementById('hp-back').click();
      for (let i = 0; i < 100 && !document.querySelector('#projects .hc-dots'); i += 1) await new Promise((r) => setTimeout(r, 100));
      document.querySelector('#projects .hc-dots').click();
      document.querySelector('#projects .hc-menu [data-act="share"]').click();
      for (let i = 0; i < 100 && document.getElementById('share-card').hidden; i += 1) await new Promise((r) => setTimeout(r, 100));
      document.getElementById('sc-choose').click();
    } },
    { name: 'd-newproject', wait: '#newproject', open: async () => {
      window.openNewProject();
    } },
    { name: 'd-page', wait: '#hp-list .pcard', open: async () => {
      if (document.getElementById('home-project').hidden) document.querySelector('#projects .home-card').click();
      for (let i = 0; i < 100 && !document.querySelector('#hp-list .pc-dots'); i += 1) await new Promise((r) => setTimeout(r, 100));
    } },
    { name: 'd-page-menu', wait: '#hp-list .pc-menu:not([hidden])', open: async () => {
      if (document.getElementById('home-project').hidden) document.querySelector('#projects .home-card').click();
      for (let i = 0; i < 100 && !document.querySelector('#hp-list .pc-dots'); i += 1) await new Promise((r) => setTimeout(r, 100));
      document.querySelector('#hp-list .pc-dots').click();
    } },
    { name: 'd-page-files', wait: '#hp-list .pc-files:not([hidden])', open: async () => {
      if (document.getElementById('home-project').hidden) document.querySelector('#projects .home-card').click();
      for (let i = 0; i < 100 && !document.querySelector('#hp-list .pc-dots'); i += 1) await new Promise((r) => setTimeout(r, 100));
      document.querySelector('#hp-list .pc-dots').click();
      document.querySelector('#hp-list .pc-menu [data-act="files"]').click();
    } },
    // A row's fields hold Rename... only for a participant in a folder of its own, as in a copy of demo/, and the rows of
    // demo/pristine, the root every group shares, have none, so there the card opens as the fields would open it and
    // shows the server's refusal where a copy of demo/ shows the list of what will change (loose31, 31 October 2026:
    // the click on a Rename that was not there stopped the group at this screen). The participant is opened first, as
    // d-work opens it, so that list names the recent list whatever the server showed before
    { name: 'd-page-rename', wait: '#rename', open: async () => {
      if (document.getElementById('home-project').hidden) document.querySelector('#projects .home-card').click();
      for (let i = 0; i < 100 && !document.querySelector('#hp-list .pc-dots'); i += 1) await new Promise((r) => setTimeout(r, 100));
      const row = document.querySelector('#hp-list .pcard');
      const cases = S.lib.projects[0].cases;
      await api('/api/open', { path: (cases.find((c) => c.case === row.dataset.case) || cases[0]).path });
      row.querySelector('.pc-dots').click();
      const edit = row.querySelector('.pc-menu [data-act="edit"]');
      if (edit) edit.click();
      const item = row.querySelector('[data-pp="rename"]');
      if (item) item.click(); else openRename(S.lib.projects[0].id, { case: row.dataset.case });
    } },
    { name: 'd-add', wait: '#newproject', open: async () => {
      if (document.getElementById('home-project').hidden) document.querySelector('#projects .home-card').click();
      for (let i = 0; i < 100 && !document.querySelector('#hp-list .pc-dots'); i += 1) await new Promise((r) => setTimeout(r, 100));
      document.getElementById('hp-transcripts').click();
    } },
    { name: 'd-work', wait: '#work .turn', open: async () => {
      if (document.getElementById('home-project').hidden) document.querySelector('#projects .home-card').click();
      for (let i = 0; i < 100 && !document.querySelector('#hp-list .pc-dots'); i += 1) await new Promise((r) => setTimeout(r, 100));
      document.querySelector('#hp-list .pc-es, #hp-list .pc-tp').click();
      for (let i = 0; i < 100 && !document.querySelector('#work .turn'); i += 1) await new Promise((r) => setTimeout(r, 100));
      await new Promise((r) => setTimeout(r, 600));
    } },
    { name: 'd-work-cols', wait: '#cols-menu:not([hidden])', open: async () => {
      if (document.getElementById('home-project').hidden) document.querySelector('#projects .home-card').click();
      for (let i = 0; i < 100 && !document.querySelector('#hp-list .pc-dots'); i += 1) await new Promise((r) => setTimeout(r, 100));
      document.querySelector('#hp-list .pc-es, #hp-list .pc-tp').click();
      for (let i = 0; i < 100 && !document.querySelector('#work .turn'); i += 1) await new Promise((r) => setTimeout(r, 100));
      await new Promise((r) => setTimeout(r, 600));
      document.getElementById('cols-pick').click();
    } },
    { name: 'd-work-view', wait: '#view-menu:not([hidden])', open: async () => {
      if (document.getElementById('home-project').hidden) document.querySelector('#projects .home-card').click();
      for (let i = 0; i < 100 && !document.querySelector('#hp-list .pc-dots'); i += 1) await new Promise((r) => setTimeout(r, 100));
      document.querySelector('#hp-list .pc-es, #hp-list .pc-tp').click();
      for (let i = 0; i < 100 && !document.querySelector('#work .turn'); i += 1) await new Promise((r) => setTimeout(r, 100));
      await new Promise((r) => setTimeout(r, 600));
      document.getElementById('btn-view').click();
    } },
    { name: 'd-work-who', wait: '#es-whomenu .ds-who-row', open: async () => {
      if (document.getElementById('home-project').hidden) document.querySelector('#projects .home-card').click();
      for (let i = 0; i < 100 && !document.querySelector('#hp-list .pc-dots'); i += 1) await new Promise((r) => setTimeout(r, 100));
      document.querySelector('#hp-list .pc-es, #hp-list .pc-tp').click();
      for (let i = 0; i < 100 && !document.querySelector('#work .turn'); i += 1) await new Promise((r) => setTimeout(r, 100));
      await new Promise((r) => setTimeout(r, 600));
      document.getElementById('es-who').click();
    } },
    { name: 'd-work-row', wait: '#transcript-rows .row-menu', open: async () => {
      if (document.getElementById('home-project').hidden) document.querySelector('#projects .home-card').click();
      for (let i = 0; i < 100 && !document.querySelector('#hp-list .pc-dots'); i += 1) await new Promise((r) => setTimeout(r, 100));
      document.querySelector('#hp-list .pc-es, #hp-list .pc-tp').click();
      for (let i = 0; i < 100 && !document.querySelector('#work .turn'); i += 1) await new Promise((r) => setTimeout(r, 100));
      await new Promise((r) => setTimeout(r, 600));
      window.openRowMenu(current());
    } },
    { name: 'd-work-edit', wait: '#transcript-rows .turn-edit', open: async () => {
      if (document.getElementById('home-project').hidden) document.querySelector('#projects .home-card').click();
      for (let i = 0; i < 100 && !document.querySelector('#hp-list .pc-dots'); i += 1) await new Promise((r) => setTimeout(r, 100));
      document.querySelector('#hp-list .pc-es, #hp-list .pc-tp').click();
      for (let i = 0; i < 100 && !document.querySelector('#work .turn'); i += 1) await new Promise((r) => setTimeout(r, 100));
      await new Promise((r) => setTimeout(r, 600));
      window.openEditor(current());
    } },
    { name: 'd-work-time', wait: '#transcript-rows .time-edit', open: async () => {
      if (document.getElementById('home-project').hidden) document.querySelector('#projects .home-card').click();
      for (let i = 0; i < 100 && !document.querySelector('#hp-list .pc-dots'); i += 1) await new Promise((r) => setTimeout(r, 100));
      document.querySelector('#hp-list .pc-es, #hp-list .pc-tp').click();
      for (let i = 0; i < 100 && !document.querySelector('#work .turn'); i += 1) await new Promise((r) => setTimeout(r, 100));
      await new Promise((r) => setTimeout(r, 600));
      window.openTimeEdit(current());
    } },
    { name: 'd-work-find', wait: '#find', open: async () => {
      if (document.getElementById('home-project').hidden) document.querySelector('#projects .home-card').click();
      for (let i = 0; i < 100 && !document.querySelector('#hp-list .pc-dots'); i += 1) await new Promise((r) => setTimeout(r, 100));
      document.querySelector('#hp-list .pc-es, #hp-list .pc-tp').click();
      for (let i = 0; i < 100 && !document.querySelector('#work .turn'); i += 1) await new Promise((r) => setTimeout(r, 100));
      await new Promise((r) => setTimeout(r, 600));
      window.openFind();
      const box = document.getElementById('find-text');
      box.value = 'the';
      box.dispatchEvent(new Event('input', { bubbles: true }));
      await new Promise((r) => setTimeout(r, 800));
    } },
    { name: 'd-settings', wait: '#settings', panes: true, open: async () => {
      document.getElementById('lib-settings').click();
    } },
    { name: 'd-work-settings', wait: '#settings', panes: true, open: async () => {
      if (document.getElementById('home-project').hidden) document.querySelector('#projects .home-card').click();
      for (let i = 0; i < 100 && !document.querySelector('#hp-list .pc-dots'); i += 1) await new Promise((r) => setTimeout(r, 100));
      document.querySelector('#hp-list .pc-es, #hp-list .pc-tp').click();
      for (let i = 0; i < 100 && !document.querySelector('#work .turn'); i += 1) await new Promise((r) => setTimeout(r, 100));
      await new Promise((r) => setTimeout(r, 600));
      document.getElementById('btn-settings').click();
    } },
  ],
  // the boards' screens (i18nthemes, 28 October 2026: themes.js, trajectories.js and table.js): the PETs and GETs
  // boards of the first participant of the first project, on a copy of demo/pristine as --root, each screen opened
  // through the board's own functions with nothing kept in the browser. Each starts with the board loaded, a card on
  // the canvas `k` and the first label `g`. Trajectories show only in a project of two timepoints, which the demo
  // is not, so its words are shot as the board would draw them on an invented column.
  boards: [
    { name: 'pets', open: async () => { await themesOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true; }, wait: '#themes .th-label' },
    { name: 'pets-inspector-card', wait: '#th-side', open: async () => {
      await themesOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true;
      const k = Object.keys(TH.v.cards).find((x) => thOnCanvas(TH.v, x));
      thSelectOnly({ kind: 'card', id: k }); thInspectorOpen({ kind: 'card', id: k }, false); } },
    { name: 'pets-inspector-label', wait: '#th-side', open: async () => {
      await themesOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true;
      const g = TH.v.groups[0].id;
      thSelectOnly({ kind: 'group', id: g }); thInspectorOpen({ kind: 'group', id: g }, false); } },
    { name: 'pets-menu-card', wait: '.th-cmenu', open: async () => {
      await themesOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true;
      const k = Object.keys(TH.v.cards).find((x) => thOnCanvas(TH.v, x) && TH.v.groups.some((g) => g.members.includes(x)));
      thMenuOpen({ kind: 'card', id: k }, 420, 260); } },
    { name: 'pets-menu-label', wait: '.th-cmenu', open: async () => {
      await themesOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true;
      thMenuOpen({ kind: 'group', id: TH.v.groups[0].id }, 420, 260); } },
    { name: 'pets-menu-canvas', wait: '.th-cmenu', open: async () => {
      await themesOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true;
      thMenuOpen({ kind: 'canvas', x: 0, y: 0 }, 640, 420); } },
    { name: 'pets-boards', wait: '#th-vmenu', open: async () => { await themesOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true; thVmenu(true); } },
    { name: 'pets-boards-last', wait: '#th-vmenu', open: async () => {
      await themesOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true; thVmenu(true); thAskDelete(); } },
    { name: 'pets-table', wait: '#th-table', open: async () => { await themesOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true; thFace('table', false); } },
    { name: 'pets-history', wait: '#th-side', open: async () => {
      await themesOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true; thSideOpen('history', undefined, false); } },
    { name: 'pets-guidance', wait: '#th-side', open: async () => {
      await themesOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true; thSideOpen('guidance', undefined, false); } },
    { name: 'pets-sidebar', wait: '#th-cpanel', open: async () => { await themesOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true; thListOpenAt('aside'); } },
    { name: 'pets-status', wait: '#th-smenu', open: async () => { await themesOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true; thStatusMenu(true, 300, 760); } },
    { name: 'pets-cases', wait: '#th-casemenu', open: async () => { await themesOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true; await thCasemenu(true); } },
    { name: 'gets', open: async () => { await getsOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true; }, wait: '#themes .th-label' },
    { name: 'gets-inspector-label', wait: '#th-side', open: async () => {
      await getsOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true;
      const g = TH.v.groups[0].id;
      thSelectOnly({ kind: 'group', id: g }); thInspectorOpen({ kind: 'group', id: g }, false); } },
    { name: 'gets-inspector-card', wait: '#th-side', open: async () => {
      await getsOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true;
      const k = Object.keys(TH.v.cards).find((x) => thOnCanvas(TH.v, x));
      thSelectOnly({ kind: 'card', id: k }); thInspectorOpen({ kind: 'card', id: k }, false); } },
    { name: 'gets-menu-card', wait: '.th-cmenu', open: async () => {
      await getsOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true;
      thMenuOpen({ kind: 'card', id: Object.keys(TH.v.cards).find((x) => thOnCanvas(TH.v, x)) }, 420, 260); } },
    { name: 'gets-boards', wait: '#th-vmenu', open: async () => { await getsOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true; thVmenu(true); } },
    { name: 'gets-table', wait: '#th-table', open: async () => { await getsOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true; thFace('table', false); } },
    { name: 'gets-cases', wait: '#th-cpanel', open: async () => { await getsOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true; gtCasesOpen(false); } },
    { name: 'gets-colours', wait: '.gt-colours', open: async () => {
      await getsOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true; gtCasesOpen(false); gtColourMenu(0, 300, 200); } },
    { name: 'gets-trail', wait: '#gt-trail', open: async () => { await getsOpen(S.lib.projects[0].cases[0].path, {}); document.getElementById('library').hidden = true; await gtTrailOpen(TH.v.groups[0].id); } },
    { name: 'trajectories', wait: '#tj-board', open: async () => {
      for (const id of ['library', 'work', 'themes']) document.getElementById(id).hidden = true;
      document.getElementById('traj').hidden = false;
      trajLoad({ project: S.lib.projects[0].project, demo: false, unplaced: ['a'],
        columns: [{ id: 'c1', title: 'Settling in', participants: ['b'] }],
        participants: [{ case: 'a', who: 'Wren', colour: 1, lpets: [] }, { case: 'b', who: 'Finch', colour: 2, lpets: ['A walk at dawn'], column: 'c1', note: '' }] });
    } },
  ],
  // Every screen at Large (zoomsweep, 30 October 2026, for packaging/pixels/zoom_sweep.mjs, which shoots a group in the
  // Mac's own engine at each zoom): Home, the project's page, the statements screen with its player, the PETs board
  // on Canvas and Table, GETs, Trajectories, every Settings category from Home and from the statements screen, and
  // the cards, on a --root copy of demo/pristine. Sift's and Trace's main screens are in zoom-sift and zoom-trace,
  // each on a server of its own app, the folder from the sweep's --sift or --trace (SWEEP in the page)
  zoom: [
    { name: 'home', wait: '#projects .home-card', open: opener(PICKER) },
    { name: 'project', wait: '#hp-list .pcard', open: opener(PAGE) },
    // a row of demo/pristine has no folder of its own, so no Rename in its menu: the card as the menu opens it,
    // a new name typed, which asks the server what would change and writes nothing
    { name: 'rename', wait: '#rename', open: opener(PAGE, "openRename(S.lib.projects[0].id, { case: 'Juno' });",
      "document.getElementById('rn-name').value = 'Juno Two'; rnPlan();", NAP(600)) },
    { name: 'statements', wait: '#player-wrap', open: opener(PAGE, WORK, PLAYER) },
    { name: 'statements-notes', wait: '#player-wrap', open: opener(PAGE, WORK, PLAYER, "if (typeof openNote === 'function') openNote(current());") },
    { name: 'shortcuts', wait: '#help', open: opener(PAGE, WORK, "document.getElementById('btn-help').click();") },
    { name: 'trim', wait: '#trim', open: opener(PAGE, WORK, "confirmTrim(current(), 'before', true);") },
    { name: 'settings-work', wait: '#settings', panes: true, open: opener(PAGE, WORK, "document.getElementById('btn-settings').click();") },
    { name: 'pets', wait: '#themes .th-label', open: opener(BOARD('themesOpen')) },
    { name: 'pets-table', wait: '#th-table', open: opener(BOARD('themesOpen'), "thFace('table', false);") },
    { name: 'gets', wait: '#themes .th-label', open: opener(BOARD('getsOpen')) },
    { name: 'gets-table', wait: '#th-table', open: opener(BOARD('getsOpen'), "thFace('table', false);") },
    { name: 'trajectories', wait: '#tj-board', open: opener(TRAJ) },
    { name: 'settings', wait: '#settings', panes: true, open: opener(PICKER, "document.getElementById('lib-settings').click();") },
    { name: 'feedback', wait: '#feedback', open: opener(PICKER, "document.getElementById('lib-feedback').click();") },
    { name: 'support', wait: '#support', open: opener(PICKER, "document.getElementById('lib-support').click();") },
    { name: 'about', wait: '#about', open: opener(PICKER, "document.getElementById('lib-settings').click();",
      "document.getElementById('settings-about').click();") },
    { name: 'whatsnew', wait: '#whatsnew', open: opener(PICKER, 'window.openWhatsNew();') },
  ],
  'zoom-sift': [
    { name: 'sift', wait: '#sift', open: opener(SIFT, NAP(1200)) },
    { name: 'sift-record', wait: '#sift', open: opener(SIFT, NAP(1200), 'sfOpenRecord();', NAP(800)) },
  ],
  'zoom-trace': [
    { name: 'trace', wait: '#trace', open: opener(TRACE, NAP(1200)) },
    { name: 'trace-record', wait: '#trace', open: opener(TRACE, NAP(1200), 'trOpenRecord();', NAP(800)) },
  ],
  // Sift's and Trace's own apps (tracestyle, 30 October 2026, after Trace's own app showed its screen unstyled for a
  // week, its page no longer loading the frame it shares with Sift): each on a server of its own app, `--app sift`
  // or `--app trace`, with `--sift <screening folder>` or `--trace <Trace project folder>` of invented records, which
  // the server's list keeps (its state file beside --config). Home with the project's row, the card that opens a
  // project, the table, the table with its filters, a record, and Trace's two cards, the filters opened without
  // being kept so each screen starts the same
  sift: [
    { name: 'sift-home', wait: '#sift-list .sf-row-open', open: () => {} },
    { name: 'sift-card', wait: '#rv-card', open: () => openReviewCard('new', 'sift') },
    { name: 'sift-table', wait: '#sf-tbl tbody tr', open: opener(SIFT, NAP(1200)) },
    { name: 'sift-filters', wait: '#sf-facets .sf-group', open: opener(SIFT, NAP(1200), 'sfFacetsOpen(true, false);', NAP(400)) },
    { name: 'sift-record', wait: '#sf-record', open: opener(SIFT, NAP(1200), 'sfOpenRecord();', NAP(800)) },
  ],
  // Sift's Search strategy (siftlang, 1 November 2026, when its words moved into the catalogue): the screen
  // sift_search.js builds, of a project with searches named by --sift, at its top, its end and its question card
  'sift-strategy': [
    { name: 'sift-strategy', wait: '#sfs-h-plan', open: opener('await rvOpen(SWEEP.sift);', NAP(1200)) },
    { name: 'sift-strategy-end', wait: '#sfs-run', open: opener('await rvOpen(SWEEP.sift);', NAP(1200),
      "document.getElementById('sfs-run').scrollIntoView({ block: 'end' });", NAP(400)) },
    { name: 'sift-strategy-mark', wait: '#sfs-mark-card', open: opener('await rvOpen(SWEEP.sift);', NAP(1200),
      "document.getElementById('sfs-mark-card').hidden = false;", NAP(400)) },
  ],
  trace: [
    { name: 'trace-home', wait: '#trace-list .sf-row-open', open: () => {} },
    { name: 'trace-card', wait: '#rv-card', open: () => openReviewCard('new', 'trace') },
    { name: 'trace-table', wait: '#tr-tbl tbody tr', open: opener(TRACE, NAP(1200)) },
    { name: 'trace-filters', wait: '#tr-facets .sf-group', open: opener(TRACE, NAP(1200), 'trFacetsOpen(true, false);', NAP(400)) },
    { name: 'trace-record', wait: '#tr-record', open: opener(TRACE, NAP(1200), 'trOpenRecord();', NAP(800)) },
    { name: 'trace-keys', wait: '#tr-keys', open: opener(TRACE, NAP(1200), "document.getElementById('tr-keys').hidden = false;") },
    { name: 'trace-ask', wait: '#tr-ask', open: opener(TRACE, NAP(1200), "document.getElementById('tr-ask').hidden = false;") },
  ],
};

// What differs between two copies of the app for reasons that are not the change: the box to paste into an agent
// names this install's own folder, so its words are made transparent in both runs and its box still compared, and
// the round's clock, which counts the seconds a screen has been open, and the statements screen's, which
// counts the seconds since the case opened
export const MASKS = ['#agent-text', '#rail-clock'];
