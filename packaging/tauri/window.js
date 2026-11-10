/* Idiograph's window, the page's side. `src-tauri/src/main.rs` runs this in every window before the
   page's own scripts, with `window.__IDIOGRAPH_OS__` set first to "macos" or "windows". Served to a
   browser the page never has it: the server knows nothing of it, and without the window's bridge,
   `window.__TAURI_INTERNALS__`, it does nothing at all.

   What a browser gives a page and a window does not, it asks of the window:
   - Print, on a Mac, where window.print does nothing in the window's web view: the window's own print
     panel, Save as PDF among it, on the window that asked, a print view's own (19 October). Windows's
     web view prints by itself.
   - Ctrl+N, or Cmd+N where the Mac's menu has not taken it: a new window on what this one shows.
   - Cmd or Ctrl and a click, or a middle click, on a link: the link in a new window, as a browser
     opens a tab, since the web view would follow it in place.
   - A download, a link with `download` clicked as the PRISMA map's Save clicks one: the file's bytes
     read here and handed to the window, which opens the system's save panel with the file's name in
     it and writes the file where it is put, or says it could not.

   And since the second build (17 October, later):
   - The settings the page keeps in the browser, its folds, filters and Sift's step, every key that
     begins idiograph-, kept by the app, so a window on another port starts with them all. The window
     hands them over in `window.__IDIOGRAPH_SEED__` as the window opens, and every change goes back.
   - The place the page was on, which a Restart returns to, handed back by the window when it opens
     after a relaunch, and the home screen's own place with it.
   - Closing a window: what is typed and not saved is saved first, as any move saves it, the page is
     told it is going as a browser tells it, and the window keeps where it was.
   - The menus' items that act on the page, Settings, Shortcuts, Send feedback, Reload, Status Bar,
     which turns the PETs and GETs boards' status bar on or off, and on a Mac Undo and Redo, which reach
     the app's own undo on a board and the field's in a text field.
   - Cmd or Ctrl with 0, + and -, the window's zoom, the text size that Settings' Small, Medium and Large set
     too (`idiographTextSize`, 20 October).
   - A mouse's back and forward buttons on a Mac, the history's Back and Forward, as Safari has them.
   - Choose, the system's own folder dialog on the window, and the home screen's projects for Open
     Recent.

   And since the fourth build (18 October):
   - Idiograph's own updates, which the window checks and installs through Tauri's updater: the page
     asks with `idiographUpdate`, and hears each change as the event `idiograph-update`. A browser's
     page has neither, so it shows nothing of them.
   - Help, What's New, which opens the page's sheet of the version's notes.

   And since 21 October:
   - Send, a whole project: the save panel alone, through `idiographSavePath`, and the server writes
     the file to the path chosen, so a project with recordings is never read into the page.

   Export as PDF and Save as an image are the server's since 9 November 2026 (typst5, Adam: Typst for every PDF and
   picture, no fallback): the server makes the file with Typst and writes it, so the window prints nothing to a
   file and pictures no page. Print, on paper, is the window's as before.

   And since 6 November (fileassoc):
   - A shared copy opened from the Finder or Explorer, by a double click, a drop on the app's icon or Open With:
     the window keeps the file, the page takes it once its own scripts are there, and hands it to its Open a
     shared copy, `idiographOpenFile`.

   And since 9 November (removefix):
   - A line to confirm, Remove from Idiograph's and every other, in the window's own message box through
     `idiographConfirm`, since the Mac's web view answers window.confirm with Cancel and shows nothing.

   And since 9 November (linuxfix4), on Linux alone:
   - Ctrl+Z, Ctrl+Y and Shift+Ctrl+Z in a text field, WebKitGTK's own Undo and Redo where the page leaves the key.
   - The line at the foot said to Orca, `idiographSay`, which the window announces. */

/* The paper a page asks for, read from the size of its own @page rules as a browser reads them, the
   last that says one winning (28 October, printland): { orientation: 'landscape' or 'portrait', paper:
   'a4', 'letter' and the like, or null }, or {} when no rule says a size. A Mac's print panel takes no
   paper from the page, so the window sets the panel's orientation and paper from this before it opens
   (main.rs, print). A named paper with no orientation is portrait, as CSS has it. `css` is the text of
   the page's style elements. */
function idiographPagePaper(css) {
  var text = String(css || '').replace(/\/\*[\s\S]*?\*\//g, '');
  var at = /@page\b[^{;]*\{/g;
  var said = '';
  var m;
  while ((m = at.exec(text))) {
    // the rule's own declarations, its margin boxes (@top-right and the like) left out
    var depth = 1;
    var own = '';
    var i = at.lastIndex;
    for (; i < text.length && depth; i++) {
      var c = text.charAt(i);
      if (c === '{') depth++;
      else if (c === '}') depth--;
      else if (depth === 1) own += c;
    }
    at.lastIndex = i;
    var size = /(?:^|[;\s])size\s*:\s*([^;]+)/i.exec(own);
    if (size) said = size[1].replace(/!important/i, '').trim().toLowerCase();
  }
  if (!said || said === 'auto') return {};
  var words = said.split(/\s+/);
  var papers = ['a3', 'a4', 'a5', 'b4', 'b5', 'letter', 'legal', 'ledger'];
  var paper = null;
  var orientation = null;
  for (var k = 0; k < words.length; k++) {
    if (words[k] === 'landscape' || words[k] === 'portrait') orientation = words[k];
    else if (papers.indexOf(words[k]) >= 0) paper = words[k];
  }
  if (!orientation && paper) orientation = 'portrait';
  return orientation ? { orientation: orientation, paper: paper } : {};
}

/* The foot a page asks for on paper, read from its own @page rules' bottom margin boxes as Chrome reads
   them (31 October 2026, exportpdf2): the Mac's web view draws no margin box, so the window draws the
   foot itself from what this finds (main.rs, `mac::print`). { left, center, right }, each a list of
   parts, a string or { counter: 'page' } or { counter: 'pages' }, with the box's `size` in points,
   `color` and `family`, `margins`, the page's own in millimetres, top, right, bottom and left, and `fit`,
   the index of the left box's part that may be shortened, its `--idiograph-fit`, or -1 (1 November). A
   later declaration of a box wins over an earlier one unless the earlier is !important and the later
   is not, as CSS has it, so the empty box the server adds after the page's own takes nothing away.
   null when no box says anything. `css` is the text of the page's style elements. */
function idiographPageFoot(css) {
  var text = String(css || '').replace(/\/\*[\s\S]*?\*\//g, '');
  var boxes = {};
  var margins = null;
  var at = /@page\b[^{;]*\{/g;
  var m;
  var mm = function (v) {
    var n = /^(-?[\d.]+)(mm|cm|in|pt|px)?$/i.exec(v);
    if (!n) return null;
    var k = { mm: 1, cm: 10, in: 25.4, pt: 25.4 / 72, px: 25.4 / 96 }[(n[2] || 'px').toLowerCase()];
    return parseFloat(n[1]) * k;
  };
  var parts = function (value) {
    var out = [];
    var re = /"((?:[^"\\]|\\[\s\S])*)"|'((?:[^'\\]|\\[\s\S])*)'|counter\(\s*(pages?)\s*\)/g;
    var t;
    while ((t = re.exec(value))) {
      if (t[3]) { out.push({ counter: t[3] }); continue; }
      var s = (t[1] !== undefined ? t[1] : t[2]).replace(/\\([0-9a-fA-F]{1,6})\s?|\\([\s\S])/g, function (_, hex, ch) {
        return hex ? String.fromCodePoint(parseInt(hex, 16)) : ch;
      });
      if (s) out.push(s);
    }
    return out;
  };
  while ((m = at.exec(text))) {
    var depth = 1;
    var own = '';
    var i = at.lastIndex;
    for (; i < text.length && depth; i++) {
      var c = text.charAt(i);
      if (c === '{') depth++;
      else if (c === '}') depth--;
      else if (depth === 1) own += c;
      if (c === '@' && depth === 1) {
        // a margin box: its name and its own declarations
        var box = /^@(bottom-left|bottom-center|bottom-right)\s*\{([^}]*)\}/.exec(text.slice(i));
        if (box) {
          var said = {};
          box[2].split(';').forEach(function (decl) {
            var k = decl.indexOf(':');
            if (k > 0) said[decl.slice(0, k).trim().toLowerCase()] = decl.slice(k + 1).trim();
          });
          if (said.content !== undefined) {
            var important = /!important\s*$/i.test(said.content);
            var name = box[1].replace('bottom-', '');
            var was = boxes[name];
            if (!was || important || !was.important) {
              var face = String(said['font-family'] || '').split(',')[0].replace(/["']/g, '').trim();
              var fit = parseInt(said['--idiograph-fit'], 10);
              boxes[name] = { important: important, parts: parts(said.content.replace(/!important\s*$/i, '')),
                size: parseFloat(said['font-size']) || null, color: said.color || null, family: face || null,
                fit: isNaN(fit) ? -1 : fit };
            }
          }
          own = own.slice(0, -1);
          i += box[0].length - 1;
        }
      }
    }
    at.lastIndex = i;
    var margin = /(?:^|[;\s])margin\s*:\s*([^;]+)/i.exec(own);
    if (margin) {
      var v = margin[1].replace(/!important/i, '').trim().split(/\s+/).map(mm);
      if (v.length && v.every(function (x) { return x !== null; })) {
        if (v.length === 1) v = [v[0], v[0], v[0], v[0]];
        else if (v.length === 2) v = [v[0], v[1], v[0], v[1]];
        else if (v.length === 3) v = [v[0], v[1], v[2], v[1]];
        margins = v.slice(0, 4);
      }
    }
  }
  var foot = { margins: margins || [0, 0, 0, 0], fit: -1 };
  var any = false;
  ['left', 'center', 'right'].forEach(function (name) {
    var box = boxes[name];
    foot[name] = box ? box.parts : [];
    // the left box's piece that may be shortened, the project (1 November 2026)
    if (name === 'left' && box && box.fit >= 0 && box.fit < box.parts.length) foot.fit = box.fit;
    if (box && box.parts.length) {
      any = true;
      foot.size = foot.size || box.size;
      foot.color = foot.color || box.color;
      foot.family = foot.family || box.family;
    }
  });
  return any ? foot : null;
}

/* Undo or Redo pressed in a text field on Linux (linuxfix4, 9 November 2026): 'undo' for Ctrl+Z, 'redo' for Ctrl+Y and
   Shift+Ctrl+Z, when `field` is a field one types in, else null. WebKitGTK on GTK 3 gives these keys no undo of its own,
   so the window runs its Undo or Redo where the page leaves the key (`edit` in main.rs). */
var IDIOGRAPH_TYPED = /^(text|search|url|tel|email|password|number)$/;
function idiographFieldUndo(e, field) {
  if (!e || !e.ctrlKey || e.altKey || e.metaKey || e.isComposing || !field) return null;
  var tag = String(field.tagName || '').toLowerCase();
  var typed = tag === 'textarea' || field.isContentEditable === true
    || (tag === 'input' && IDIOGRAPH_TYPED.test(String(field.type || 'text').toLowerCase()));
  if (!typed || field.readOnly || field.disabled) return null;
  // the letter the layout gives, else the key's place where the layout gives no Latin letter
  var key = String(e.key || '').toLowerCase();
  if (!/^[a-z]$/.test(key)) key = /^Key[A-Z]$/.test(String(e.code || '')) ? e.code.charAt(3).toLowerCase() : '';
  if (key === 'z') return e.shiftKey ? 'redo' : 'undo';
  if (key === 'y' && !e.shiftKey) return 'redo';
  return null;
}

(function () {
  var win = window;
  var ipc = win.__TAURI_INTERNALS__;
  if (!ipc) return;
  /* Run again, it takes hold once, but Print is set again. On a Mac every window shares the scripts of
     the windows it opened and was opened by, so Tauri's own script runs after this one, and its
     print, which the window refuses, took the page's Print (19 October). */
  if (win.__idiographWindow) {
    if (typeof win.__idiographPrint === 'function') win.print = win.__idiographPrint;
    return;
  }
  win.__idiographWindow = true;
  var os = String(win.__IDIOGRAPH_OS__ || '');
  var ask = function (cmd, args) {
    return Promise.resolve(ipc.invoke(cmd, args || {})).catch(function () { return null; });
  };
  var wait = function (ms) { return new Promise(function (done) { setTimeout(done, ms); }); };

  /* ── what the page keeps in the browser, kept by the app ── */
  var PREFIX = 'idiograph-';
  var SEEDED = 'idiograph-window-seeded';
  var PLACES = ['idiograph-return', 'idiograph-home'];
  var seed = win.__IDIOGRAPH_SEED__ || {};
  var local = null;
  var session = null;
  try { local = win.localStorage; session = win.sessionStorage; } catch (err) { /* no storage at all */ }
  var Store = win.Storage && win.Storage.prototype;
  if (local && session && Store && Store.setItem) {
    var setItem = Store.setItem;
    var removeItem = Store.removeItem;
    var clear = Store.clear;
    var own = function (key) { return String(key).indexOf(PREFIX) === 0; };
    try {
      // once in each window, before the page's own scripts read anything: a reload keeps its own
      if (!session.getItem(SEEDED)) {
        setItem.call(session, SEEDED, '1');
        if (seed.local && typeof seed.local === 'object') {
          for (var i = local.length - 1; i >= 0; i -= 1) {
            var gone = local.key(i);
            if (gone && own(gone) && !Object.prototype.hasOwnProperty.call(seed.local, gone)) removeItem.call(local, gone);
          }
          Object.keys(seed.local).forEach(function (key) { setItem.call(local, key, String(seed.local[key])); });
        } else {
          // the app keeps nothing yet, so it takes what this port's storage holds
          var held = {};
          for (var j = 0; j < local.length; j += 1) {
            var key = local.key(j);
            if (key && own(key)) held[key] = local.getItem(key);
          }
          ask('keep', { all: held });
        }
        var given = seed.session || {};
        Object.keys(given).forEach(function (key) {
          if (typeof given[key] === 'string') setItem.call(session, key, given[key]);
        });
      }
    } catch (err) { /* the page starts with what the port holds */ }
    Store.setItem = function (key, value) {
      var done = setItem.apply(this, arguments);
      if (this === local && own(key)) ask('keep', { key: String(key), value: String(value) });
      return done;
    };
    Store.removeItem = function (key) {
      var done = removeItem.apply(this, arguments);
      if (this === local && own(key)) ask('keep', { key: String(key), value: null });
      return done;
    };
    Store.clear = function () {
      var done = clear.apply(this, arguments);
      if (this === local) ask('keep', { all: {} });
      return done;
    };
  }

  /* ── closing a window, and a reload ── */
  /* whether the page has typed words not yet saved, asked as a browser asks it before a page goes */
  function unsaved() {
    var e = new Event('beforeunload', { cancelable: true });
    win.dispatchEvent(e);
    return e.defaultPrevented;
  }

  /* what is typed and not saved saved first, as any move saves it, given ten seconds. The answer is
     whether nothing is left unsaved */
  function keepTyped() {
    if (!unsaved()) return Promise.resolve(true);
    var save = typeof win.savePending === 'function' ? win.savePending : null;
    if (!save) return Promise.resolve(false);
    return Promise.race([Promise.resolve().then(save).catch(function () { return false; }), wait(10000)])
      .then(function () { return !unsaved(); });
  }

  /* The window asks this as it is closed, by its close button, Close Window or Quit: the typed words
     saved, or the window asked whether to close without them, then the page told it is going, so it
     keeps its place and sends what it still holds, and the place handed to the window. */
  var closing = false;
  win.__idiographClosing = function () {
    if (closing) return false;
    closing = true;
    ask('closing', { step: 'begun' });
    keepTyped()
      .then(function (kept) { return kept ? true : ask('closing', { step: 'unsaved' }); })
      .then(function (go) {
        if (!go) { closing = false; ask('closing', { step: 'kept' }); return null; }
        try { win.dispatchEvent(new PageTransitionEvent('pagehide', { persisted: false })); }
        catch (err) { win.dispatchEvent(new Event('pagehide')); }
        var place = {};
        try {
          PLACES.forEach(function (key) { var v = session.getItem(key); if (v !== null) place[key] = v; });
        } catch (err) { /* no place to keep */ }
        return ask('closing', { step: 'done', place: place });
      });
    return true;
  };

  /* ── the menus' items that act on the page ── */
  function shown(id) {
    var el = document.getElementById(id);
    return el && !el.disabled && el.offsetParent !== null && !el.closest('[hidden]') ? el : null;
  }
  /* the button of the bar in view that does it, as its own click does it there */
  function press(ids) {
    for (var i = 0; i < ids.length; i += 1) {
      var button = shown(ids[i]);
      if (button) { button.click(); return true; }
    }
    return false;
  }
  var SETTINGS = ['btn-settings', 'lib-settings', 'th-settings', 'sf-settings', 'sfs-settings', 'tr-settings'];
  var SHORTCUTS = ['btn-help', 'th-help', 'sf-help', 'tr-help'];
  var FEEDBACK = ['btn-feedback', 'lib-feedback', 'th-feedback', 'sf-feedback', 'sfs-feedback', 'tr-feedback'];

  /* Undo or Redo from the Mac's Edit menu: the page's own key first, Cmd+Z or Shift+Cmd+Z, which a
     board or a list takes for the app's undo, and when the page leaves it, as it leaves it in a text
     field, the field's own undo */
  function edit(back) {
    var target = document.activeElement || document.body;
    var e = new KeyboardEvent('keydown', { key: 'z', code: 'KeyZ', metaKey: os === 'macos', ctrlKey: os !== 'macos',
      shiftKey: !back, bubbles: true, cancelable: true });
    target.dispatchEvent(e);
    if (!e.defaultPrevented) ask('edit', { action: back ? 'undo' : 'redo' });
  }

  /* Find and Find and Replace from the Edit menu (barsD, 6 November 2026): the page's own keys pressed where the focus
     is, Cmd+F or Ctrl+F for Search and with Shift for the statements screen's Find and replace card, so each does just
     what its key does on the screen in front */
  function find(replace) {
    var target = document.activeElement || document.body;
    target.dispatchEvent(new KeyboardEvent('keydown', { key: 'f', code: 'KeyF', metaKey: os === 'macos', ctrlKey: os !== 'macos',
      shiftKey: !!replace, bubbles: true, cancelable: true }));
  }

  var MENU = {
    settings: function () {
      if (!press(SETTINGS) && typeof win.openSettings === 'function') win.openSettings();
    },
    shortcuts: function () {
      if (!press(SHORTCUTS) && typeof win.openHelp === 'function') win.openHelp();
    },
    feedback: function () { press(FEEDBACK); },
    whatsnew: function () { if (typeof win.openWhatsNew === 'function') win.openWhatsNew(); },
    // the app's own About card, from the Mac's Idiograph menu and Windows's Help (20 October)
    about: function () { if (typeof win.openAbout === 'function') win.openAbout(); },
    undo: function () { edit(true); },
    redo: function () { edit(false); },
    reload: function () { keepTyped().then(function () { win.location.reload(); }); },
    'status-bar': function () { if (typeof win.thStatusToggle === 'function') win.thStatusToggle(); },
    // View, Home, the page's Home from any screen (20 October)
    home: function () { if (typeof win.idiographHome === 'function') win.idiographHome(); },
    // File, Project History: the open project's record, as Home's project menu opens it (4 November)
    'project-history': function () { if (typeof win.idiographProjectHistory === 'function') win.idiographProjectHistory(); },
    // File, Project Settings: the open project's own settings sheet, a demo's read-only (settingsplit, 5 November)
    'project-settings': function () { if (typeof win.idiographProjectSettings === 'function') win.idiographProjectSettings(); },
    // Edit, Find and Find and Replace, as their keys (barsD, 6 November)
    find: function () { find(false); },
    'find-replace': function () { find(true); },
  };
  /* File, Project History is on while a project is open in this window, Project Settings while any project is,
     a demo's included, and Edit, Find and Replace while the statements screen is in front (barsD): the page says so,
     asked twice a second and told to the app when any changes or the window comes to the front, since a menu bar is
     shared by every window */
  var projectOn = null;
  var projectTell = function () {
    var on = typeof win.idiographProjectNow === 'function' && !!win.idiographProjectNow();
    var settings = typeof win.idiographProjectSettingsNow === 'function' ? !!win.idiographProjectSettingsNow() : on;
    var replace = typeof win.idiographReplaceNow === 'function' && !!win.idiographReplaceNow();
    var now = on + ',' + settings + ',' + replace;
    if (now !== projectOn) { projectOn = now; ask('project_now', { on: on, settings: settings, replace: replace }); }
  };
  if (typeof win.setInterval === 'function') win.setInterval(projectTell, 500);
  if (typeof win.addEventListener === 'function') win.addEventListener('focus', function () { projectOn = null; projectTell(); });
  win.__idiographMenu = function (name) {
    var act = MENU[name];
    if (act) act();
    return !!act;
  };

  /* File, New Window, Cmd or Ctrl+N (20 October, Adam's drawing of two windows in step): a second
     window on what this one shows, the participant on its passage, a board, a Sift or Trace project,
     or the home screen's own place, as a restart comes back to it. The place goes over as the window's
     start, and in its address after #open=, the form Open in a new window gives, so both open the same
     way. A print view or the manual opens the home screen. */
  var OPEN_HASH = '#open=';
  win.__idiographNewWindow = function () {
    var place = {};
    var hash = '';
    try {
      if (win.location.pathname === '/') {
        var spot = typeof win.spotNow === 'function' ? win.spotNow() : null;
        if (spot && typeof spot === 'object' && spot.path) {
          place[PLACES[0]] = JSON.stringify(Object.assign({ at: Date.now() }, spot));
          hash = OPEN_HASH + encodeURIComponent(JSON.stringify(spot));
        }
        var home = session ? session.getItem(PLACES[1]) : null;
        if (home !== null && home !== undefined) place[PLACES[1]] = home;
      }
    } catch (err) { /* the home screen, as before */ }
    ask('new_window', { place: place, hash: hash });
    return true;
  };

  /* Open in a new window, from the participant switcher or a board's menu (20 October): the place the page
     hands over, as the new window's start and in its address after #open=, through the app's own window
     command, since a window that window.open makes shares this one's handler and closing it could close
     this one. It needs the command's place and hash (printwin's new_window). */
  win.__idiographOpenWindow = function (spot, hash) {
    var place = {};
    try { place[PLACES[0]] = JSON.stringify(Object.assign({ at: Date.now() }, spot)); } catch (err) { /* the home screen */ }
    ask('new_window', { place: place, hash: String(hash || '') });
    return true;
  };

  /* ── Choose, and Open Recent ── */
  /* a folder, or with `files` a file, chosen in the system's own dialog on the window: its path, or
     null for none */
  win.idiographPick = function (prompt, files) {
    return ask('pick', { prompt: String(prompt || ''), files: !!files });
  };
  /* where to save a file the server writes itself, Share a copy's whole project: the system's save
     panel alone, `name` in it and `message` its line, and its path, or null for Cancel. Nothing passes
     through the page (21 October) */
  win.idiographSavePath = function (name, message) {
    return ask('save_path', { name: String(name || ''), message: String(message || '') });
  };
  /* a line to confirm, OK or Cancel, in the window's own message box on the window: true for OK. The Mac's web view
     shows nothing for window.confirm and answers Cancel at once, so the page asks here (removefix, 9 November 2026) */
  win.idiographConfirm = function (message) {
    return ask('confirm', { message: String(message || '') }).then(function (ok) { return ok === true; });
  };
  /* the home screen's projects for File, Open Recent, and whether Send feedback is there */
  win.idiographRecent = function (list, feedback) {
    ask('recent', { list: Array.isArray(list) ? list : [], feedback: !!feedback });
  };

  /* ── a shared copy opened from outside the app (fileassoc) ── */
  /* The files the app was asked to open, a .idiograph file double-clicked in the Finder or Explorer, dropped on
     the app's icon or opened with Open With, taken from the window, each once, and each handed to the page's own
     Open a shared copy. A page without it, a print view's or the manual's, takes nothing, so they wait for one
     that has it. The page takes them as it loads, and again whenever the window says more are waiting. */
  win.__idiographOpened = function () {
    if (typeof win.idiographOpenFile !== 'function') return false;
    ask('opened', {}).then(function (files) {
      (Array.isArray(files) ? files : []).forEach(function (file) {
        if (typeof file === 'string' && file) win.idiographOpenFile(file);
      });
    });
    return true;
  };
  if (typeof win.addEventListener === 'function') win.addEventListener('load', function () { win.__idiographOpened(); });

  /* ── Idiograph's own updates ── */
  /* one ask of the window's updates, `op` read, choose, set, check, download, later, seen or relaunch:
     the answer is how they stand now, or null */
  win.idiographUpdate = function (op, more) {
    var args = { op: String(op || 'read') };
    var given = more || {};
    ['check', 'download'].forEach(function (key) { if (typeof given[key] === 'boolean') args[key] = given[key]; });
    if (given.place && typeof given.place === 'object') args.place = given.place;
    return ask('updates', args);
  };
  /* the window tells the page of every change, which the page hears as an event */
  win.__idiographUpdate = function (view) {
    try { win.dispatchEvent(new CustomEvent('idiograph-update', { detail: view })); }
    catch (err) { /* a page going */ }
  };

  /* Print on a Mac. A window the page opens, a print view or a table, shares its opener's web view
     setup there, so what it asks reaches the app as its opener's, and Print printed the window behind
     it, its panel out of sight (Adam, 18 October). So each window names its own address and title,
     and the app prints the window they name. A window opened on about:blank and written in, as the canvas's print is,
     gets the same Print from the page that opened it, which it may never get from this file. Tauri's
     own print, which a run of its script after this one sets, the window refuses, so this file's is
     set again on every run (above). The page's own @page size goes with it, so the panel opens on the
     orientation and paper the page asks for, a print view's landscape A4 (28 October). Linux's window prints the
     same way, since WebKitGTK's print dialog too takes its page from the window and never from @page, so a canvas
     printed portrait (linuxfix, 9 November 2026). Windows's web view reads @page itself and keeps its own print. */
  var printer = function (target) {
    return function () {
      var href = '';
      var title = '';
      var paper = {};
      var foot = null;
      try {
        href = String(target.location.href || '');
        title = String((target.document && target.document.title) || '');
        var css = '';
        // the page's own fitted foot, set for Chrome's margin boxes (themes_print, FOOT_FIT), left out: the window
        // lays the foot out itself from the server's boxes
        var styles = target.document.querySelectorAll('style:not([data-foot-fitted])');
        for (var i = 0; i < styles.length; i++) css += styles[i].textContent + '\n';
        paper = idiographPagePaper(css);
        foot = idiographPageFoot(css);
      } catch (err) { /* a page going */ }
      var asked = { href: href, title: title };
      // a page that says no size asks for none, and its print is as it was
      if (paper.orientation) asked.orientation = paper.orientation;
      if (paper.paper) asked.paper = paper.paper;
      // the foot the page asks for on paper, which the Mac's window draws itself (31 October)
      if (foot) asked.foot = foot;
      ask('print', asked);
    };
  };
  if (os !== 'windows') {
    win.__idiographPrint = printer(win);
    win.print = win.__idiographPrint;
    var opened = win.open;
    if (typeof opened === 'function') {
      win.open = function () {
        var tab = opened.apply(this, arguments);
        try { if (tab) tab.print = printer(tab); } catch (err) { /* a window of another site */ }
        var url = arguments.length ? String(arguments[0] || '') : '';
        if (tab && (url === '' || url === 'about:blank')) keysFor(tab);
        return tab;
      };
    }
  }

  /* A print view's own page, a board's or the GETs' print or a table served, or a window the page
     opened on about:blank to write in, the canvas's print, which then has its opener's address. */
  var PRINTS = ['/themes/print', '/gets/print'];
  var WRITTEN = '__idiographWritten';
  function printView(target) {
    try {
      return PRINTS.indexOf(target.location.pathname) >= 0 || target[WRITTEN] === true;
    } catch (err) { return false; }
  }

  /* The keys a window keeps for itself, `target` the window they were pressed in (20 October, the
     backlog: on a Mac a print view's zoom and save reached the window behind it). Cmd on a Mac and
     Ctrl elsewhere, with 0, + (or =) and -, the zoom of the window named by its own address and title,
     and in a Mac's print view S its print panel, where Save as PDF is, the print view's save. */
  function viewKey(target, e) {
    var mod = os === 'macos' ? e.metaKey : e.ctrlKey;
    // once for a key, which a written window's own listener may have taken already
    if (!mod || e.altKey || e.defaultPrevented) return false;
    if (os === 'macos' && !e.shiftKey && (e.key === 's' || e.key === 'S' || e.code === 'KeyS') && printView(target)) {
      e.preventDefault();
      e.stopPropagation();
      if (typeof target.print === 'function') target.print();
      return true;
    }
    var by = e.key === '=' || e.key === '+' ? 1 : e.key === '-' || e.key === '_' ? -1 : e.key === '0' ? 0 : null;
    if (by === null) return false;
    e.preventDefault();
    e.stopPropagation();
    var href = '';
    var title = '';
    try {
      href = String(target.location.href || '');
      title = String((target.document && target.document.title) || '');
    } catch (err) { /* a page going */ }
    ask('zoom', { by: by, href: href, title: title }).then(told);
    return true;
  }

  /* The text size, Settings' Small, Medium and Large (20 October, Settled 12), the windows' zoom as View's
     Bigger Text, Smaller Text and Actual Size move it: `to` sets it, and with none it is read. Either
     answers the zoom as it stands, and every change is told to the page as the event idiograph-zoom, so
     Settings' rows stay in step with the keys. */
  function told(zoom) {
    if (typeof zoom === 'number' && win.dispatchEvent && typeof win.CustomEvent === 'function') {
      win.dispatchEvent(new win.CustomEvent('idiograph-zoom', { detail: zoom }));
    }
    return zoom;
  }
  win.idiographTextSize = function (to) {
    return ask('zoom', typeof to === 'number' ? { to: to } : {}).then(told);
  };

  /* A window the page opens on about:blank and writes in, the canvas's print, loses the keys this file
     gave it as it is written, so they are given again once its page is there, looked for a minute at
     most, its root marked. A window that goes on to a page of the server's has this file of its own,
     which takes each key first. */
  var KEYS_MARK = 'data-idiograph-keys';
  function keysFor(tab) {
    try { tab[WRITTEN] = true; } catch (err) { return; }
    var tries = 0;
    var look = function () {
      tries += 1;
      try {
        if (tab.closed) return;
        var doc = tab.document;
        var root = doc && doc.documentElement;
        if (!root) return;
        if (doc.readyState === 'complete' && doc.body && doc.body.childNodes.length) {
          if (!root.hasAttribute(KEYS_MARK)) {
            root.setAttribute(KEYS_MARK, '');
            tab.addEventListener('keydown', function (e) { viewKey(tab, e); }, true);
          }
          return;
        }
      } catch (err) { return; }
      if (tries < 120) setTimeout(look, 500);
    };
    setTimeout(look, 200);
  }

  win.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && !e.altKey && !e.shiftKey && (e.key === 'n' || e.key === 'N')) {
      e.preventDefault();
      e.stopPropagation();
      win.__idiographNewWindow();
      return;
    }
    // Back and Forward on a Mac, Cmd + [ and Cmd + ], as Safari and Finder have them, which the Mac's
    // web view leaves to its app (19 October). Windows's web view takes Alt and the arrows by itself.
    if (os === 'macos' && e.metaKey && !e.ctrlKey && !e.altKey && !e.shiftKey
        && (e.key === '[' || e.key === ']' || e.code === 'BracketLeft' || e.code === 'BracketRight')) {
      e.preventDefault();
      e.stopPropagation();
      if (e.key === '[' || (e.key !== ']' && e.code === 'BracketLeft')) win.history.back();
      else win.history.forward();
      return;
    }
    viewKey(win, e);
  }, true);

  /* Ctrl+Z, Ctrl+Y and Shift+Ctrl+Z in a text field on Linux (linuxfix4, 9 November 2026): once the page has had the
     key, and only where it left it, as a field leaves it, the window runs WebKitGTK's own Undo or Redo on the field,
     since WebKitGTK on GTK 3 binds no key to them. Off a field the page's own undo takes the key, as before. */
  if (os !== 'macos' && os !== 'windows') {
    /* The line at the foot said to Orca by the window (linuxfix4, 9 November 2026), since WebKitGTK tells Orca nothing
       of the page's live region: shell.js's say hands its words here, and the window announces them. */
    win.idiographSay = function (words) { ask('announce', { words: String(words || '') }); };
    win.addEventListener('keydown', function (e) {
      var action = idiographFieldUndo(e, e.target);
      if (!action) return;
      setTimeout(function () { if (!e.defaultPrevented) ask('edit', { action: action }); }, 0);
    }, true);
  }

  /* A mouse's back and forward buttons on a Mac, as Safari has them, which the Mac's web view leaves to its
     app (20 October, Adam's call: Back from a project returns to Home and Forward goes in again). Windows's
     web view takes them by itself. */
  win.addEventListener('mouseup', function (e) {
    if (os !== 'macos' || (e.button !== 3 && e.button !== 4)) return;
    e.preventDefault();
    e.stopPropagation();
    if (e.button === 3) win.history.back();
    else win.history.forward();
  }, true);

  /* the file's name: the link's own `download`, else the last part of its address */
  function fileName(a) {
    var named = a.getAttribute('download');
    if (named) return named;
    var path = String(a.href || '').split(/[?#]/)[0].split('/').pop();
    try { path = decodeURIComponent(path); } catch (err) { /* the name as it is written */ }
    return path && !/^blob:/.test(a.href) ? path : 'download';
  }

  function base64(buffer) {
    var bytes = new Uint8Array(buffer);
    var parts = [];
    for (var i = 0; i < bytes.length; i += 0x8000) {
      parts.push(String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000)));
    }
    return win.btoa(parts.join(''));
  }

  /* the file read and handed to the window. When it cannot be read the window is told, with no bytes,
     so it says the file was not saved */
  function save(a) {
    var name = fileName(a);
    return Promise.resolve()
      .then(function () { return win.fetch(a.href); })
      .then(function (res) {
        if (!res.ok) throw new Error(String(res.status));
        return res.arrayBuffer();
      })
      .then(function (buffer) { return base64(buffer); }, function () { return null; })
      .then(function (data) { return ask('save_download', { name: name, data: data }); });
  }
  win.__idiographSave = save;

  function downloadOf(target) {
    var a = target && target.closest ? target.closest('a[href]') : null;
    return a && a.hasAttribute('download') ? a : null;
  }

  function apart(e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
    if (!a || a.hasAttribute('download') || a.getAttribute('href').charAt(0) === '#') return;
    if (!(e.metaKey || e.ctrlKey || e.button === 1)) return;
    e.preventDefault();
    e.stopPropagation();
    win.open(a.href, '_blank');
  }

  win.addEventListener('click', function (e) {
    var a = downloadOf(e.target);
    if (a) {
      e.preventDefault();
      save(a);
      return;
    }
    apart(e);
  }, true);
  win.addEventListener('auxclick', function (e) { if (e.button === 1) apart(e); }, true);

  /* a link clicked while it is in no page, which no listener here hears */
  var Anchor = win.HTMLAnchorElement;
  if (Anchor && Anchor.prototype && Anchor.prototype.click) {
    var click = Anchor.prototype.click;
    Anchor.prototype.click = function () {
      if (!this.isConnected && this.hasAttribute('download') && this.getAttribute('href')) {
        save(this);
        return;
      }
      return click.apply(this, arguments);
    };
  }
})();
