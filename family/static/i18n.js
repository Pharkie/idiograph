/* The text layer's script side (i18ncore, 28 October 2026), loaded before every other script. Every word a script
   puts on the screen comes through t(key, values) from the catalogue the server writes into the page as I18N (see
   family/i18n.py, where the files and their shape are): the language, its locale and every message, English under
   any key the language lacks. A message is a whole sentence with named slots, "{app} {version} is ready.", or for a
   count an object of plural forms picked by the slot n through Intl.PluralRules. A key no catalogue has shows as
   itself and is named once in the console. Dates and lists go through Intl in the catalogue's locale (tDate,
   tList), never through hand-written month names. A page from a server before the catalogue has none, and every
   key shows as itself. */

'use strict';

const I18N_DATA = (typeof I18N !== 'undefined' && I18N && I18N.messages) ? I18N
  : { language: 'en', locale: 'en-GB', messages: {} };
const I18N_MISSED = new Set();
const I18N_RULES = new Map();

/* the plural category of n in the catalogue's locale, `other` where Intl cannot say */
function tPlural(n) {
  try {
    if (!I18N_RULES.has(I18N_DATA.locale)) I18N_RULES.set(I18N_DATA.locale, new Intl.PluralRules(I18N_DATA.locale));
    return I18N_RULES.get(I18N_DATA.locale).select(Number(n) || 0);
  } catch { return Number(n) === 1 ? 'one' : 'other'; }
}

/* The method of the project in front (tadraw, 31 October 2026): 'ipa', whose words are the catalogue's own, or
   'ta', thematic analysis, whose sentences I18N.methods.ta holds by key where it says them otherwise. A screen
   sets it as it opens a project's participant or board (tMethod), and Home words each project's card in its own
   (tIn). */
let I18N_METHOD = 'ipa';
let I18N_MARKED = null;

/* the markup's words a method says otherwise, found once: each text or attribute the server filled from a key
   in I18N.marked, as IPA wrote it, so tMethod can word it again */
function tMarked() {
  if (I18N_MARKED) return I18N_MARKED;
  I18N_MARKED = [];
  const marked = I18N_DATA.marked || {};
  const want = new Map();
  for (const key of Object.keys(marked)) {
    const text = tBase(key, marked[key]);
    if (text && !want.has(text)) want.set(text, key);
  }
  if (!want.size || typeof document === 'undefined') return I18N_MARKED;
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
  for (let node = walk.currentNode; node; node = walk.nextNode()) {
    if (node.nodeType === 3) {
      const text = node.nodeValue.trim();
      if (want.has(text)) I18N_MARKED.push({ node, attr: null, key: want.get(text), was: text });
      continue;
    }
    if (node.tagName === 'SCRIPT' || node.tagName === 'STYLE') continue;
    // and a tab's hidden bold copy of its words (barsD, 6 November 2026), so a tab worded again keeps its width
    for (const attr of ['title', 'aria-label', 'placeholder', 'data-bold']) {
      const text = node.getAttribute(attr);
      if (text && want.has(text)) I18N_MARKED.push({ node, attr, key: want.get(text), was: text });
    }
  }
  return I18N_MARKED;
}

/* the project in front's method set, and the markup's words it says otherwise worded again in it */
function tMethod(method) {
  const next = method === 'ta' && I18N_DATA.methods && I18N_DATA.methods.ta ? 'ta' : 'ipa';
  if (next === I18N_METHOD && I18N_MARKED) return;
  I18N_METHOD = next;
  // the page's own parts a method has no use for hide by it, html[data-method="ta"]
  if (typeof document !== 'undefined') document.documentElement.dataset.method = next;
  if (next === 'ipa' && !I18N_MARKED) return;
  for (const one of tMarked()) {
    const text = t(one.key, (I18N_DATA.marked || {})[one.key]);
    if (one.attr) one.node.setAttribute(one.attr, text);
    else one.node.nodeValue = one.node.nodeValue.replace(one.was, text);
    one.was = text;
  }
}

/* fn run with `method` the method in front, as a project's card on Home is drawn in its own words, the method
   before it put back after */
function tIn(method, fn) {
  const was = I18N_METHOD;
  I18N_METHOD = method === 'ta' ? 'ta' : 'ipa';
  try { return fn(); } finally { I18N_METHOD = was; }
}

/* the project in front's method, for a screen that hides what its method has no use for */
function tMethodNow() { return I18N_METHOD; }

/* a message in the catalogue's own words, IPA's, whatever the method in front */
function tBase(key, values) { return tIn('ipa', () => t(key, values)); }

/* A message by its key with its slots filled: `{name}` takes values.name, a slot with no value stays as it
   stands, and a message with plural forms takes the form for values.n, or `other`. In a method other than
   IPA, that method's sentence where it has one. */
function t(key, values) {
  const own = I18N_METHOD !== 'ipa' && I18N_DATA.methods && I18N_DATA.methods[I18N_METHOD];
  let m = own && own[key] !== undefined ? own[key] : I18N_DATA.messages[key];
  if (m === undefined || m === null) {
    if (!I18N_MISSED.has(key)) { I18N_MISSED.add(key); console.warn(`i18n: no message for ${key}`); }
    return key;
  }
  if (typeof m === 'object') m = m[tPlural(values && values.n)] ?? m.other ?? '';
  m = String(m);
  return values ? m.replace(/\{(\w+)\}/g, (all, name) => (name in values ? String(values[name]) : all)) : m;
}

/* Corrections to Intl's output where the app's own language says it otherwise: since 2020 CLDR's British English
   writes September short as "Sept", and Idiograph's English has always said "Sep" */
const I18N_DATE_FIX = { 'en-GB': [[/\bSept\b/g, 'Sep']] };
const I18N_FORMATS = new Map();

/* Formats apart from the language (fmtcore, 28 October 2026): the order of a date's day, month and year, the
   clock a time of day is written by and the marks in a number, each chosen under Settings, Language and formats
   (I18N.formats) or else the computer's own as the window reads it (I18N.computer_formats), and with neither, as
   in a browser, the language's own. The month's name, am and pm and the digits stay the language's. */
const FORMAT_CHOICES = { dates: ['dmy', 'mdy', 'ymd'], time: ['24', '12'], numbers: ['comma', 'point', 'space', 'apostrophe'] };
// each number choice's mark between the thousands and its decimal mark: 1,234.5, 1.234,5, 1 234,5 and 1'234.5
const FORMAT_MARKS = { comma: [',', '.'], point: ['.', ','], space: [' ', ','], apostrophe: ['’', '.'] };

/* the format in force for `kind`, `given`'s where it names that kind ("" there the language's own), else the
   settings', else the computer's, else "" */
function tFormat(kind, given) {
  if (given && kind in given) return FORMAT_CHOICES[kind].includes(given[kind]) ? given[kind] : '';
  const held = (I18N_DATA.formats || {})[kind] || (I18N_DATA.computer_formats || {})[kind] || '';
  return FORMAT_CHOICES[kind].includes(held) ? held : '';
}

function tIntl(options) {
  const id = `${I18N_DATA.locale}|${JSON.stringify(options || {})}`;
  if (!I18N_FORMATS.has(id)) I18N_FORMATS.set(id, new Intl.DateTimeFormat(I18N_DATA.locale, options));
  return I18N_FORMATS.get(id);
}

/* A date as the catalogue's locale writes it, from a Date, an ISO time or milliseconds, with Intl's own options:
   { day: 'numeric', month: 'long', year: 'numeric' } is 12 October 2026 in English. timeZone: 'UTC' reads a
   time as written, with no time zone brought into it. The order is the dates format's (tFormat, or `formats`'
   own): where the language writes it in that order its own writing stands ("28 de octubre de 2026"), else its
   parts are put in that order, 28 October 2026 or October 28, 2026, and 2026-10-28 is all numbers, 10-28
   with no year. An hour follows the clock the time format chooses. */
function tDate(when, options, formats) {
  const d = when instanceof Date ? when : new Date(when);
  if (Number.isNaN(d.getTime())) return '';
  const opts = { ...(options || {}) };
  const clock = tFormat('time', formats);
  if (clock && opts.hour !== undefined) { delete opts.hour12; opts.hourCycle = clock === '12' ? 'h12' : 'h23'; }
  const order = tFormat('dates', formats);
  let out = order && (opts.month || opts.year) && opts.day ? tDateIn(d, opts, order) : tIntl(opts).format(d);
  for (const [from, to] of I18N_DATE_FIX[I18N_DATA.locale] || []) out = out.replace(from, to);
  return out;
}

/* a date with a day and a month in `order`, the language's own words for each part */
function tDateIn(d, opts, order) {
  const dateOpts = {};
  for (const k of ['weekday', 'day', 'month', 'year', 'era', 'timeZone']) if (opts[k] !== undefined) dateOpts[k] = opts[k];
  const timeOpts = {};
  for (const k of ['hour', 'minute', 'second', 'hourCycle', 'hour12', 'timeZone']) if (opts[k] !== undefined) timeOpts[k] = opts[k];
  const time = timeOpts.hour !== undefined || timeOpts.minute !== undefined ? tIntl(timeOpts).format(d) : '';
  const parts = tIntl(dateOpts).formatToParts(d);
  const part = (type) => (parts.find((p) => p.type === type) || {}).value || '';
  const has = (type) => parts.some((p) => p.type === type);
  const natural = parts.filter((p) => ['day', 'month', 'year'].includes(p.type)).map((p) => p.type[0]).join('');
  const wanted = order.split('').filter((c) => has({ d: 'day', m: 'month', y: 'year' }[c])).join('');
  let date;
  if (order === 'ymd') {
    const nums = tIntl({ year: 'numeric', month: '2-digit', day: '2-digit', timeZone: dateOpts.timeZone }).formatToParts(d);
    const num = (type) => (nums.find((p) => p.type === type) || {}).value || '';
    date = (has('year') ? [num('year'), num('month'), num('day')] : [num('month'), num('day')]).join('-');
    if (has('weekday')) date = `${part('weekday')} ${date}`;
  } else if (natural === wanted) {
    date = tIntl(dateOpts).format(d);
  } else {
    const numeric = /^\d+$/.test(part('month'));
    const [day, month, year] = [part('day'), part('month'), has('year') ? part('year') : ''];
    if (numeric) {
      date = (order === 'mdy' ? [month, day, year] : [day, month, year]).filter(Boolean).join('/');
    } else if (order === 'mdy') {
      date = `${month} ${day}${year ? `, ${year}` : ''}`;
    } else {
      date = `${day} ${month}${year ? ` ${year}` : ''}`;
    }
    if (has('weekday')) date = `${part('weekday')}${order === 'mdy' ? ',' : ''} ${date}`;
  }
  return time ? `${date} ${time}` : date;
}

/* A time of day, hours and minutes, by the clock the time format chooses (`options.time` in its place, "" the
   language's own): 14:05, or 2:05 pm with no leading zero and am and pm the language's way. options.timeZone as
   tDate takes it. */
function tTime(when, options = {}) {
  const d = when instanceof Date ? when : new Date(when);
  if (Number.isNaN(d.getTime())) return '';
  let clock = tFormat('time', 'time' in options ? { time: options.time } : null);
  if (!clock) {
    try { clock = /h1[12]/.test(tIntl({ hour: 'numeric' }).resolvedOptions().hourCycle || '') ? '12' : '24'; } catch { clock = '24'; }
  }
  const opts = { hour: clock === '12' ? 'numeric' : '2-digit', minute: '2-digit', hourCycle: clock === '12' ? 'h12' : 'h23' };
  if (options.timeZone) opts.timeZone = options.timeZone;
  return tIntl(opts).format(d);
}

/* A number as the numbers format writes it (`formats`' own in its place): Intl's options in the language's
   locale, its digits the language's, the marks between the thousands and before the decimals the format's. */
function tNum(n, options, formats) {
  const marks = FORMAT_MARKS[tFormat('numbers', formats)];
  let nf;
  try { nf = new Intl.NumberFormat(I18N_DATA.locale, options); } catch { return String(n); }
  if (!marks) return nf.format(n);
  return nf.formatToParts(n).map((p) => (p.type === 'group' ? marks[0] : p.type === 'decimal' ? marks[1] : p.value)).join('');
}

/* A day written as YYYY-MM-DD, at the start of an ISO time, as a Date at that day's midnight in UTC, or null, so
   tDate(tDay(iso), { ..., timeZone: 'UTC' }) says the day as it is written */
function tDay(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso || ''));
  if (!m || Number(m[2]) < 1 || Number(m[2]) > 12) return null;
  return new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3])));
}

/* items joined as the locale joins a list, "a, b and c" in English (type `conjunction`) or "a, b or c"
   (`disjunction`) */
function tList(items, type = 'conjunction') {
  const list = (items || []).map(String);
  try { return new Intl.ListFormat(I18N_DATA.locale, { type }).format(list); } catch { return list.join(', '); }
}

/* the markup's words a method says otherwise found as the page loads, this script running after the markup and
   before any other script draws a word */
try { if (typeof document !== 'undefined' && document.body) tMarked(); } catch { /* a harness that declares its own document further on */ }
