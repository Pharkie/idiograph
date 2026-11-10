/* The rule for building one quote out of several pieces of a turn, and where a quote goes among
   the turn's pairs, each statement with its own quote.

   Pieces are held as character offsets into the turn text, so they sort back into transcript order
   however they were picked and no word order is ever rearranged. Overlapping pieces, and pieces
   separated by nothing but space, become one piece. What is left is joined with an ellipsis.

   No DOM in here, which is what lets the suite check it on its own. */

'use strict';

function mergePieces(pieces, text) {
  const sorted = (pieces || [])
    .map((p) => ({ start: Math.max(0, p.start), end: Math.min(text.length, p.end) }))
    .filter((p) => p.end > p.start)
    .sort((a, b) => a.start - b.start || a.end - b.end);
  const out = [];
  for (const piece of sorted) {
    const last = out[out.length - 1];
    if (last && (piece.start <= last.end || !text.slice(last.end, piece.start).trim())) {
      last.end = Math.max(last.end, piece.end);
    } else {
      out.push({ start: piece.start, end: piece.end });
    }
  }
  return out;
}

function assembleQuote(pieces, text) {
  const parts = mergePieces(pieces, text)
    .map((p) => text.slice(p.start, p.end).replace(/\s+/g, ' ').trim())
    .filter(Boolean);
  return parts.length ? `"${parts.join(' … ')}"` : '';
}

/* The pairs. Each experiential statement has its own quote, by place, the first quote the
   first statement's (item 198). A pair is {es, kq}. */

const NO_QUOTE = '(no quote)';
const noQuote = (text) => String(text || '').trim().toLowerCase() === NO_QUOTE;

/* A turn's two fields paired by order, as a turn saved before the pairs reads: a statement past
   the last quote has an empty one, a quote past the last statement is a pair with an empty
   statement, and "(no quote)" is an empty quote that keeps its place. */
function pairsByOrder(statements, quotes) {
  const es = (statements || []).filter((s) => String(s).trim());
  const kq = (quotes || []).map((q) => (noQuote(q) ? '' : String(q)));
  return es.map((s, i) => ({ es: s, kq: kq[i] || '' }))
    .concat(kq.slice(es.length).filter((q) => q.trim()).map((q) => ({ es: '', kq: q })));
}

/* The two cells the pairs make, as the server writes them: the statements in order, and once any
   quote is there one quote a statement, "(no quote)" for one with none, a quote whose statement is
   empty kept after them. With no quote at all the quotes cell is empty. */
function pairsToCells(pairs) {
  const line = (t) => String(t || '').replace(/\s*\n\s*/g, ' ').trim();
  const all = (pairs || []).map((p) => ({ es: line(p.es), kq: noQuote(p.kq) ? '' : line(p.kq) }));
  const kept = all.filter((p) => p.es);
  const loose = all.filter((p) => !p.es && p.kq).map((p) => p.kq);
  const es = kept.map((p) => p.es).join('\n');
  if (!loose.length && !kept.some((p) => p.kq)) return { es, kq: '' };
  return { es, kq: kept.map((p) => p.kq || NO_QUOTE).concat(loose).join('\n') };
}

/* Where `q` puts the selection, the key or the Quote button (16 October): the quote of the pair
   being worked on, `at`, an `at` that names no pair being the last pair, while that quote is
   empty, "(no quote)" holding none, and else a pair of its own under the last, as Add another puts
   one, `added` saying which. `old` is the quote field as it read, for undo. A quote is changed by
   clearing it first, so `q` never writes over one. Until 16 October `q` replaced a quote there and a
   second key, `s`, made the new pair. */
function quoteTarget(pairs, at) {
  const list = pairs || [];
  const i = Number.isInteger(at) && at >= 0 && at < list.length ? at : list.length - 1;
  const kq = i >= 0 ? String(list[i].kq || '') : '';
  if (i >= 0 && (!kq.trim() || noQuote(kq))) return { place: i, added: false, old: kq };
  return { place: list.length, added: true, old: '' };
}

/* Where a candidate from the AI goes: the statement of the pair being worked on while it is empty,
   and else a pair of its own under the last. */
function candidateTarget(pairs, at) {
  const list = pairs || [];
  const i = Number.isInteger(at) && at >= 0 && at < list.length ? at : list.length - 1;
  if (i >= 0 && !String(list[i].es || '').trim()) return { place: i, added: false };
  return { place: list.length, added: true };
}

/* Undo of a quote taken with `q`: the pair holding exactly those words, the one it went into first
   and else the last that holds them, whose quote takes back what it held before, or which goes
   when `q` added it and its statement is still empty. Null when no pair holds them. */
function quoteOut(pairs, place, quote) {
  const list = pairs || [];
  const holds = (p) => !!p && p.kq === quote;
  let i = holds(list[place]) ? place : -1;
  for (let k = list.length - 1; i < 0 && k >= 0; k -= 1) if (holds(list[k])) i = k;
  return i < 0 ? null : { place: i };
}

/* Where a quote stands in its passage (16 October), one span a piece, so a quote put together
   from pieces with an ellipsis is marked piece by piece. The inverted commas round the whole quote
   are set aside, double or single, straight or curly, and each piece is found after the one before
   it, any run of spaces reading as one, case set aside, and curly and straight inverted commas and
   apostrophes matching each other. A quote any piece of which the passage no longer holds, its text
   corrected since, finds nothing at all and goes unmarked. */
function quoteSpans(quote, text) {
  return quoteReach(quote, [text], 0).map((p) => ({ start: p.start, end: p.end }));
}

/* A quote's pieces as they are looked for: the inverted commas round the whole set aside, cut at an
   ellipsis, three dots or a clarifying insert in square brackets, "my rational [mind] tells me", the
   analyst's word and not the passage's, which is never looked for, and a piece with no letter or digit
   dropped. */
function quotePieces(quote) {
  let body = String(quote || '').trim();
  if (!body || noQuote(body)) return [];
  if (/^["\u201c\u201d]|["\u201c\u201d]$/.test(body)) body = body.replace(/^["\u201c\u201d]+/, '').replace(/["\u201c\u201d]+$/, '');
  else if (body.length > 1 && /['\u2018\u2019]/.test(body[0]) && /['\u2018\u2019]/.test(body[body.length - 1])) body = body.slice(1, -1);
  return body.split(/\s*(?:\u2026|\.\.\.|\[[^\]]*\])\s*/).map((p) => p.trim())
    .filter((p) => /[\p{L}\p{N}]/u.test(p));
}

const quoteFold = (c) => {
  if (/[\u2018\u2019]/.test(c)) return "'";
  if (/[\u201c\u201d]/.test(c)) return '"';
  const low = c.toLowerCase();
  return low.length === 1 ? low : c;
};

/* a passage with each run of spaces as one space and every character folded, and where each of its
   characters stands in the passage itself */
function quoteFlat(text) {
  const src = String(text || '');
  let flat = '';
  const at = [];
  for (let i = 0; i < src.length; i += 1) {
    if (/\s/.test(src[i])) {
      if (flat[flat.length - 1] === ' ') continue;
      flat += ' ';
    } else flat += quoteFold(src[i]);
    at.push(i);
  }
  return { flat, at };
}

/* Where a quote stands among one speaker's adjacent passages (quotespan, 30 October 2026, Adam: a quote
   may take in the same speaker's passages next to its own, still one quote), `texts` in transcript order
   and `home` the place of its statement's own passage among them: one `{turn, start, end}` a piece, or
   none when its words are not there. Each piece is found after the one before, in the same passage or the
   next, so the passages it takes in run unbroken, each holding a piece, its own among them. Its own
   passage is tried alone first, which is where a quote of one passage was always found, then running on
   into the passages after it, then starting in those before. workbook.py's `quote_reach` holds the same
   rule for print and the command line. */
function quoteReach(quote, texts, home) {
  const pieces = quotePieces(quote);
  const list = texts || [];
  const own = Number.isInteger(home) ? home : 0;
  if (!pieces.length || own < 0 || own >= list.length) return [];
  const wants = pieces.map((p) => p.replace(/\s+/g, ' ').split('').map(quoteFold).join(''));
  const flats = [];
  const flat = (t) => (flats[t] || (flats[t] = quoteFlat(list[t])));
  const failed = new Set();
  const find = (i, t, from) => {
    if (i === wants.length) return t >= own ? [] : null;
    const key = `${i},${t},${from}`;
    if (failed.has(key)) return null;
    for (const [turn, start] of [[t, from], [t + 1, 0]]) {
      // a new passage only once this one holds a piece, and never past the texts
      if ((turn !== t && i === 0) || turn >= list.length) continue;
      const { flat: words, at } = flat(turn);
      const k = words.indexOf(wants[i], start);
      if (k < 0) continue;
      const rest = find(i + 1, turn, k + wants[i].length);
      if (rest) return [{ turn, start: at[k], end: at[k + wants[i].length - 1] + 1 }].concat(rest);
    }
    failed.add(key);
    return null;
  };
  // each passage before its own holds a piece at least, so a quote of n pieces starts no further back
  // than n - 1
  for (let first = own; first > own - pieces.length && first >= 0; first -= 1) {
    const found = find(0, first, 0);
    if (found) return found;
  }
  return [];
}

/* One quote from pieces held in more than one passage, `groups` in transcript order, each `{pieces,
   text}`: each passage's pieces put together as `assembleQuote` puts them, and every gap, inside a
   passage or between two, an ellipsis. The interviewer's words between two passages are never in it. */
function assembleAcross(groups) {
  const parts = [];
  for (const g of groups || []) {
    for (const p of mergePieces(g.pieces, g.text)) {
      const words = g.text.slice(p.start, p.end).replace(/\s+/g, ' ').trim();
      if (words) parts.push(words);
    }
  }
  return parts.length ? `"${parts.join(' \u2026 ')}"` : '';
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    mergePieces, assembleQuote, pairsByOrder, pairsToCells, quoteTarget, candidateTarget, quoteOut,
    quoteSpans, quotePieces, quoteReach, assembleAcross,
  };
}
