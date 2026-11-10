from __future__ import annotations

import csv
import json
import re
import shutil

from . import support
from .support import check, sift_words_js, skip


@support.as_app("sift")
def test_sift_facets(scratch):
    print("\n115. Sift's filters, 12 October: a sidebar at the left of the table, a group for each column a pick can filter "
          "in the columns' order, live counts with each group's own filter set aside, a nought muted and a tick kept, Found by "
          "one tick a database and the publication type one a type, the filter row gone and the headings sorting, the toggle "
          "kept in this browser, a record's PDF a red pill, and Abstract hidden at first, then in a second round sliders with "
          "two handles and a chart for Year, No. of participants and Rating, four shown and Show more, a find box in a long "
          "group, the journal and the publication type always a group, each database a pill in its colour, the categories "
          "as pills, and the names he chose")
    import subprocess
    import sift

    flat = lambda text: " ".join(str(text).split())
    page = support.page_text()
    app = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    sjs = support.text("apps/sift/static/sift.js")
    # Sift's styles as its page loads them, the frame it shares with Trace first (tracestyle, 30 October 2026)
    scss = support.text("family/static/frame.css", "apps/sift/static/sift.css")
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    node = shutil.which("node")
    screen_html = page.split('<section id="sift"', 1)[1].split("</section>", 1)[0]
    rail = screen_html.split('<div class="rail sf-rail">', 1)[1].split('<div class="sf-main"', 1)[0]

    # ── A. an invented screening on village choirs, eight records, every count below counted by hand
    base = scratch / "sift-facets"
    shutil.rmtree(base, ignore_errors=True)
    folder = base / "choirs"
    folder.mkdir(parents=True)
    head = ["rec_id", "title", "authors", "year", "journal", "doi", "pub_type", "sources", "abstract", "place", "access",
            "abstract_from"]
    rows = [
        ["R1", "The first rehearsal", "Alto, A.", "2021", "Invented Voice", "", "Journal Article", "Scopus; PsycInfo",
         "Singers spoke of the first rehearsal.", "Hall", "open", "OpenAlex"],
        ["R2", "Choirs and towns", "Bass, B.", "2021", "Invented Voice", "", "journal article", "scopus",
         "A count of choirs by town.", "Hall", "closed", "Scopus"],
        ["R3", "Singing after loss", "Cantor, C.", "2019", "", "", "Journal Article; Review", "PsycInfo",
         "Bereaved singers kept diaries.", "Hall", "open", "PsycInfo"],
        ["R4", "A choir of one's own", "Descant, D.", "2019", "Invented Song", "", "Thesis", "Web of Science",
         "Members described joining.", "Hall", "open", ""],
        ["R5", "Harmony at work", "Echo, E.", "2018", "Invented Song", "", "  Journal   Article ", "Scopus | Web of Science",
         "Office choirs met at lunch.", "Hall", "closed", ""],
        ["R6", "Voices in the ward", "Falsetto, F.", "", "", "", "", "PsycInfo", "Patients sang on the ward.", "Hall", "", ""],
        ["R7", "Learning to read music", "Glee, G.", "2017", "Invented Voice", "", "Thesis", "Web of Science",
         "Adults learnt to read a score.", "Hall", "open", ""],
        ["R8", "The last concert", "Hymn, H.", "2021", "Invented Hum", "", "Journal Article", "Scopus",
         "A choir's final concert was recalled.", "Hall", "closed", ""],
    ]
    with open(folder / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(head)
        w.writerows(rows)
    (folder / sift.REASONS_NAME).write_text("stage,code,meaning\nta,E1,Not about singing\nta,E2,No accounts of experience\n",
                                            encoding="utf-8")
    sift.decide(folder, "R1", "ta", "include")
    sift.decide(folder, "R2", "ta", "exclude", "E1")
    sift.decide(folder, "R4", "ta", "maybe")
    sift.decide(folder, "R6", "ta", "exclude", "E2")
    for rec, n in (("R1", "4"), ("R4", "2"), ("R6", "5")):
        sift.set_field(folder, rec, "rating", n)
    for rec, n in (("R3", "8"), ("R4", "30"), ("R6", "3")):
        sift.set_field(folder, rec, "participants", n)
    sift.column(folder, "add", name="Method", kind="choice", options="IPA\nThematic")
    sift.set_field(folder, "R1", "col_method", "IPA")
    sift.set_field(folder, "R3", "col_method", "Thematic")
    view = sift.screen(folder)

    # ── B. Abstract hidden at first, and a saved list of his columns kept
    fresh = [(c["key"], c["shown"]) for c in view["table"]["columns"]][:6]
    check("115: Abstract is hidden at first in sift.py and the page alike, still offered in Columns, so the columns fit a "
          "narrower window",
          dict(sift.TABLE_COLUMNS)["abstract"] is False and ("abstract", False) in fresh
          and "abstract: { label: 'Abstract', kind: 'text' }," in sjs
          and "abstract: { label: 'Abstract', kind: 'text', on: true }" not in sjs
          and any(c["key"] == "abstract" for c in view["table"]["columns"]), str(fresh))
    other = base / "kept"
    other.mkdir()
    shutil.copy(folder / sift.CSV_NAME, other / sift.CSV_NAME)
    (other / sift.SETTINGS_NAME).write_text(json.dumps({"table": {"view": "table", "first": sift.FIRST, "columns": [
        {"key": "title", "shown": True}, {"key": "abstract", "shown": True}, {"key": "year", "shown": False}]}}), encoding="utf-8")
    kept_cols = {c["key"]: c["shown"] for c in sift.table_settings(other)["columns"]}
    saved_cols = [c["key"] for c in sift.table_settings(other)["columns"]]
    check("115, updated 12 October (121): a project whose sift.json holds his columns, placed since the first columns of 12 "
          "October, keeps them, Abstract shown where he showed it",
          kept_cols["abstract"] is True and kept_cols["year"] is False
          and saved_cols.index("title") < saved_cols.index("abstract") < saved_cols.index("year"), str(saved_cols[:5]))

    # ── C. the groups, their choices, sliders and live counts, in node, on the records as the server gives them
    block = sjs.split("/* ── the table's rows: its columns, sort and filter, worked out with no page ── */", 1)[-1].split(
        "/* ── the table, drawn ── */", 1)[0]
    block = support.table_js() + "\n" + block
    lead = app[app.index("const esc = "):app.index("// a line from the server with a command in backticks")]
    long_dir = base / "long"
    long_dir.mkdir()
    with open(long_dir / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["rec_id", "title", "year", "journal", "pub_type", "sources", "abstract", "place", "room", "lang"])
        for i in range(1, 33):
            w.writerow([f"L{i:02d}", f"Long record {i}", str(1950 + 2 * i), "Revue Émue" if i == 32 else f"Journal of Song {i}",
                        {1: "article", 2: " ARTICLE "}.get(i, "Article"), "Index A",
                        "Members sang.", f"Hall {min(i, 31)}", f"Room {min(i, 30)}", "en"])
    long_view = sift.screen(long_dir)
    drawn = [f"function {name}(" + fn(sjs, name) + "\n}" for name in ("sfRangeEnds", "sfBarsHtml",
                                                                        "sfRangeHtml", "sfPillHtml", "sfLinked")]
    if node and "function sfGroups(" in block and "function sfRangeHtml(" in sjs:
        probe = scratch / "sift-facets.js"
        probe.write_text("\n".join([block, lead, "const SF = { filters: {}, facetsMore: new Set(), facetsFind: {} };",
                                    sift_words_js(sjs),
                                    "function sfMeaning(code) { return code === 'E1' ? 'Not about singing' : ''; }"] + drawn)
                         + "\nconst data = " + json.dumps({"records": view["records"], "table": view["table"],
                                                           "codes": view["reasons"]["ta"], "long": long_view["records"],
                                                           "longTable": long_view["table"]}) + ";\n" + r"""
data.records.forEach((r) => { r.pdf = ['R1', 'R3', 'R6'].includes(r.rec_id); r.new = ['R7', 'R8'].includes(r.rec_id); });
const rows = data.records;
const byId = new Map(rows.map((r) => [r.rec_id, r]));
const ids = rows.map((r) => r.rec_id);
const cols = [SF_ID, ...sfColumns(data.table)];
const groupsOf = (f, list = cols) => sfGroups(rows, rows, list, 'ta', data.codes, f);
const choices = (g) => g.choices.map((c) => [c.value, c.label]);
const plain = (o) => JSON.parse(JSON.stringify(o));
const g0 = groupsOf({});
const by = (gs, key) => gs.find((g) => g.key === key);
const kept = (f) => tbFilterRows(ids, byId, f, cols, sfRead('ta'));
const ticks = { decision: ['undecided'], pdf: ['no'] };
const wide = { decision: ['undecided', 'maybe'], pdf: ['no'] };
const ranged = { year: { from: 2019, to: null }, pdf: ['no'] };
const moved = sfColumns(Object.assign({}, data.table, { columns: [{ key: 'decision', shown: true }, { key: 'rating', shown: false },
  ...data.table.columns.filter((c) => !['decision', 'rating'].includes(c.key))] }));
const muted = Object.assign({}, ticks, { found: ['psycinfo'] });
SF.filters = muted;
const foundHtml = tbGroupHtml(by(groupsOf(muted), 'found'), tbFacetCounts(rows, groupsOf(muted), muted, sfRead('ta')).found, 0, SF);
SF.filters = ranged;
const rangedCounts = tbFacetCounts(rows, groupsOf(ranged), ranged, sfRead('ta'));
const rangedBars = sfRangeBars(rows, groupsOf(ranged), ranged, 'ta');
const yearHtml = sfRangeHtml(by(groupsOf(ranged), 'year'), rangedCounts.year, 1, rangedBars.year);
const ratingHtml = sfRangeHtml(by(g0, 'rating'), tbFacetCounts(rows, g0, {}, sfRead('ta')).rating, 5, sfRangeBars(rows, g0, {}, 'ta').rating);
SF.filters = {};
const plainHtml = tbGroupHtml(by(g0, 'found'), tbFacetCounts(rows, g0, {}, sfRead('ta')).found, 0, SF);
SF.facetsMore = new Set(['found']);
const wholeHtml = tbGroupHtml(by(g0, 'found'), tbFacetCounts(rows, g0, {}, sfRead('ta')).found, 0, SF);
SF.facetsMore = new Set();
SF.filters = { found: ['|new'] };
const tickedHtml = tbGroupHtml(by(groupsOf(SF.filters), 'found'), {}, 0, SF);
SF.filters = {};
SF.facetsMore = new Set(['decision']);
const decisionHtml = tbGroupHtml(by(g0, 'decision'), tbFacetCounts(rows, g0, {}, sfRead('ta')).decision, 2, SF);
SF.facetsMore = new Set();
const aboutHtml = tbGroupHtml(by(g0, 'csv:abstract_from'), tbFacetCounts(rows, g0, {}, sfRead('ta'))['csv:abstract_from'], 9, SF);
const pdfHead = by(g0, 'pdf').label;
const lrows = data.long;
const lcols = [SF_ID, ...sfColumns(data.longTable)];
const lg = sfGroups(lrows, lrows, lcols, 'ta', [], {});
const lcounts = tbFacetCounts(lrows, lg, {}, sfRead('ta'));
const ljournal = by(lg, 'journal');
const findBox = tbGroupHtml(ljournal, lcounts.journal, 3, SF);
SF.facetsFind = { journal: 'song 1' };
const found1 = tbGroupHtml(ljournal, lcounts.journal, 3, SF);
SF.facetsFind = { journal: 'EMUE' };
const foundAccent = tbGroupHtml(ljournal, lcounts.journal, 3, SF);
SF.facetsFind = {};
const read = sfTicksRead({ found: 'Scopus', decision: 'exclude:E1', pdf: 'yes', year: { from: '2019', to: '2021' },
  rating: ['4', '5'], participants: ['11-20', '21-50', '|none'], title: 'choir', n: '1-3', 'csv:pub_type': 'art',
  col_method: 'IPA', 'csv:gone': ['x'], 'csv:access': 7, journal: ['invented voice'] }, g0);
const readMore = sfTicksRead({ rating: { none: true }, pdf: ['maybe'], year: { from: 2030, to: 2010 } }, g0);
const dbs = ['Scopus', 'PsycInfo', 'APA PsycInfo', 'Web of Science', 'PubMed', 'Europe PMC', 'OpenAlex', 'citation chasing',
  'CINAHL', 'cinahl', 'Embase'];
console.log(JSON.stringify({
  keys: g0.map((g) => g.key),
  movedKeys: sfGroups(rows, rows, moved, 'ta', data.codes, {}).map((g) => g.key),
  found: by(g0, 'found').choices.map((c) => [c.value, c.label, c.db || '']),
  pubType: choices(by(g0, 'csv:pub_type')),
  sliders: ['year', 'participants', 'rating'].map((k) => by(g0, k)).map((g) => [g.range, g.low, g.high, choices(g)]),
  decision: by(g0, 'decision').choices.map((c) => [c.value, c.label, !!c.sub]),
  journal: choices(by(g0, 'journal')),
  access: choices(by(g0, 'csv:access')),
  sourced: by(g0, 'csv:abstract_from').choices.map((c) => [c.value, c.db || '']),
  method: choices(by(g0, 'col_method')),
  counts: plain(tbFacetCounts(rows, g0, {}, sfRead('ta'))),
  live: plain(tbFacetCounts(rows, groupsOf(ticks), ticks, sfRead('ta'))),
  liveWide: plain(tbFacetCounts(rows, groupsOf(wide), wide, sfRead('ta'))),
  liveRanged: plain(rangedCounts),
  bars: plain(rangedBars.year),
  shown: kept(ticks),
  shownWide: kept(wide),
  oneDb: kept({ found: ['scopus'] }),
  twoDbs: kept({ found: ['scopus', 'psycinfo'] }),
  review: kept({ 'csv:pub_type': ['review'] }),
  articleThesis: kept({ 'csv:pub_type': ['journal article', 'dissertation or thesis'], 'csv:access': ['open'] }),
  slides: [kept({ year: { from: 2019, to: null } }), kept({ year: { from: null, to: 2018, none: true } }),
    kept({ participants: { from: null, to: 10 } }), kept({ participants: { from: 11, to: null } }),
    kept({ participants: { from: null, to: null, none: true } }), kept({ rating: { from: 4, to: null } }),
    kept({ rating: { from: null, to: 2 } }), kept({ rating: { from: 1, to: null } }), kept({ year: { from: null, to: null } }).length,
    kept({ rating: { from: null, to: null, none: true } }).length],
  yearHtml, ratingHtml, foundHtml, plainHtml, wholeHtml, tickedHtml, decisionHtml, aboutHtml, pdfHead,
  longKeys: lg.map((g) => g.key),
  longPub: choices(by(lg, 'csv:pub_type')),
  longPubCounts: plain(lcounts['csv:pub_type']),
  longJournal: ljournal.choices.length,
  longBars: plain(sfRangeBars(lrows, lg, {}, 'ta').year),
  findBox, found1, foundAccent,
  read: plain(read),
  readMore: plain(readMore),
  readRows: kept(read),
  dbKeys: dbs.map(sfDbKey),
  dbPill: sfDbPill('Web of Science'),
  sourceCell: sfReviewCell('abstract_from', 'OpenAlex'),
  typeCell: sfReviewCell('pub_type', 'Journal Article; Review'),
  linkCell: sfReviewCell('url', 'https://example.org/choir'),
  pills: [sfPillHtml('exclude', 'E1'), sfPillHtml('include'), sfReasonPill('E1')],
}));
""", encoding="utf-8")
        ran = subprocess.run([node, str(probe)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        why = (ran.stderr or ran.stdout)[:400]
        check("115, updated 12 October (121): in node, a group for each column a pick can filter in the columns' order: "
              "Database, Year, Cited by, No. of participants, PDF, Decision, My rating, the journal and the publication type "
              "always, the review's other columns within the limit, then his choice column, and no group for the number, the "
              "words or his text column",
              out.get("keys") == ["found", "year", "cited", "participants", "pdf", "decision", "rating", "journal", "csv:pub_type",
                                  "csv:access", "csv:abstract_from", "col_method"], why or str(out.get("keys")))
        check("115: in node, the groups follow the columns as he moves them, and a hidden column keeps its group",
              (out.get("movedKeys") or [])[:2] == ["decision", "rating"] and "found" in (out.get("movedKeys") or []),
              str(out.get("movedKeys")))
        check("115, 12 October: Found by is one tick a database, each named once however many records or lists carry it, the "
              "one most records carry first, in the words most records write it with its colour, never a list of two as one "
              "choice, then More than one and New in this run",
              out.get("found") == [["scopus", "Scopus", "scopus"], ["psycinfo", "PsycInfo", "psycinfo"],
                                   ["web of science", "Web of Science", "wos"], ["|many", "More than one", ""],
                                   ["|new", "New in this run", ""]]
              and not any(";" in label or "|" in label.lstrip("|") for _, label, _d in out.get("found") or [])
              and (out.get("counts") or {}).get("found") == {"scopus": 4, "psycinfo": 3, "web of science": 3, "|many": 2, "|new": 2},
              str(out.get("found")))
        check("115, 12 October, updated (118): Publication type is tick boxes of the types the round's records carry in "
              "plain words, the most carried first, article and Article and a spaced one one choice, a thesis Dissertation or "
              "thesis, a list of two types parted, and a record with none under None",
              out.get("pubType") == [["journal article", "Journal article"], ["dissertation or thesis", "Dissertation or thesis"],
                                     ["review", "Review"], ["|none", "None"]]
              and (out.get("counts") or {}).get("csv:pub_type") == {"journal article": 5, "review": 1, "dissertation or thesis": 2,
                                                                     "|none": 1}
              and out.get("review") == ["R3"], str(out.get("pubType")))
        check("115, 12 October, round 2: the journal and the publication type are groups whatever they hold, 32 journals or "
              "one type written three ways, where another review column with one value, or with 31, has none, and one with "
              "30 has its group",
              out.get("longPub") == [["journal article", "Journal article"]] and out.get("longPubCounts") == {"journal article": 32}
              and out.get("longJournal") == 32 and "journal" in (out.get("longKeys") or [])
              and "csv:pub_type" in (out.get("longKeys") or []) and "csv:room" in (out.get("longKeys") or [])
              and "csv:place" not in (out.get("longKeys") or []) and "csv:lang" not in (out.get("longKeys") or [])
              and "csv:place" not in (out.get("keys") or [])
              and "const SF_PICK_ALWAYS = ['journal', 'csv:pub_type'];" in sjs, str(out.get("longKeys")))
        check("115, round 2, updated 12 October (121): Year and No. of participants are sliders over the whole numbers the "
              "round's rows carry, No year and Unknown under them, My rating one from one star to five with Not rated under "
              "it, and the star ticks and the bands gone",
              out.get("sliders") == [[True, 2017, 2021, [["|none", "No year"]]], [True, 3, 30, [["|none", "Unknown"]]],
                                     [True, 1, 5, [["|none", "Not rated"]]]]
              and "SF_BANDS" not in sjs and "sf-cstars" not in sjs + scss, str(out.get("sliders")))
        check("115, updated 12 October (117, 126): Decision To screen, Yes, Maybe and No with each reason under it, his choices in his order, a "
              "review column's values the most carried first, a tie by its words, the databases an abstract came from with "
              "their colours, and PDF's group headed Full text PDF",
              out.get("decision") == [["undecided", "To screen", False], ["include", "Yes", False], ["maybe", "Maybe", False],
                                      ["exclude", "No", False], ["exclude:E1", "E1", True], ["exclude:E2", "E2", True]]
              and out.get("method") == [["IPA", "IPA"], ["Thematic", "Thematic"], ["|none", "None"]]
              and out.get("journal") == [["invented voice", "Invented Voice"], ["invented song", "Invented Song"],
                                         ["invented hum", "Invented Hum"], ["|none", "None"]]
              and out.get("access") == [["open", "open"], ["closed", "closed"], ["|none", "None"]]
              and out.get("sourced") == [["openalex", "openalex"], ["psycinfo", "psycinfo"], ["scopus", "scopus"], ["|none", ""]]
              and out.get("pdfHead") == "Full text PDF" and "pdf: { label: 'PDF', kind: 'pdf', on: true }," in sjs,
              json.dumps(out.get("decision")))
        counts = out.get("counts") or {}
        check("115, updated 12 October (121): with nothing set each count is the round's records under the choice, a slider "
              "counting every row with a number in range and the records with none the rest, a record with no stars Not rated",
              counts.get("decision") == {"undecided": 4, "include": 1, "maybe": 1, "exclude": 2, "exclude:E1": 1, "exclude:E2": 1}
              and counts.get("pdf") == {"yes": 3, "no": 5} and counts.get("rating") == {"|range": 3, "|none": 5}
              and counts.get("participants") == {"|range": 3, "|none": 5}
              and counts.get("year") == {"|range": 7, "|none": 1}, json.dumps(counts)[:300])
        live = out.get("live") or {}
        check("115: each count sets its own group's filter aside and takes every other's: with Undecided and No PDF ticked, "
              "Decision counts the records with no PDF, PDF the undecided ones, and Found by both",
              live.get("decision") == {"undecided": 3, "maybe": 1, "exclude": 1, "exclude:E1": 1}
              and live.get("pdf") == {"yes": 1, "no": 3}
              and live.get("found") == {"scopus": 2, "web of science": 2, "|many": 1, "|new": 2}
              and out.get("shown") == ["R5", "R7", "R8"], json.dumps(live)[:300])
        check("115: ticks in one group widen, any of them, groups narrow each other, all of them, and the counts move as a "
              "tick changes",
              out.get("shownWide") == ["R4", "R5", "R7", "R8"] and (out.get("liveWide") or {}).get("pdf") == {"yes": 1, "no": 4}
              and out.get("oneDb") == ["R1", "R2", "R5", "R8"] and out.get("twoDbs") == ["R1", "R2", "R3", "R5", "R6", "R8"]
              and out.get("articleThesis") == ["R1", "R3", "R4", "R7"], json.dumps(out.get("liveWide"))[:200])
        check("115, round 2, updated 12 October (121): a slider keeps the rows between its two ends, either end open, None the "
              "rows with no number alone or beside the range, 10 and under, 11 and over, 4 or 5 stars, up to 2 stars the rated "
              "alone, 1 to 5 stars, Not rated the five with no stars, and with neither end moved every row",
              out.get("slides") == [["R1", "R2", "R3", "R4", "R8"], ["R5", "R6", "R7"], ["R3", "R6"], ["R4"],
                                    ["R1", "R2", "R5", "R7", "R8"], ["R1", "R6"], ["R4"],
                                    ["R1", "R4", "R6"], 8, 5], str(out.get("slides")))
        ranged = out.get("liveRanged") or {}
        check("115, round 2: a slider's count is the rows between its ends with every other filter taken, and the other groups "
              "count with the slider's range taken",
              ranged.get("year") == {"|range": 3} and ranged.get("pdf") == {"yes": 2, "no": 3}, json.dumps(ranged)[:200])
        check("115, round 2, updated 12 October (116): over each slider a small chart counted with the other filters taken, "
              "the year's a bar for each five years from a year that ends in 0 or 5, its ends kept to the round's lowest "
              "and highest, every row in one bar",
              out.get("bars") == [{"from": 2017, "to": 2019, "label": "2015–2019", "n": 3},
                                  {"from": 2020, "to": 2021, "label": "2020–2024", "n": 2}]
              and len(out.get("longBars") or []) == 13 and sum(b["n"] for b in out.get("longBars") or []) == 32
              and (out.get("longBars") or [{}])[0] == {"from": 1952, "to": 1954, "label": "1950–1954", "n": 2}
              and (out.get("longBars") or [{}])[-1] == {"from": 2010, "to": 2014, "label": "2010–2014", "n": 3},
              json.dumps(out.get("bars")))
        year_html, rating_html = out.get("yearHtml", ""), out.get("ratingHtml", "")
        check("115, round 2, updated 12 October (116, 117, 122): the year's slider drawn: its chart's bars whose whole run "
              "is in range in the accent and the rest muted, each run in words with its count of records for the tip, two "
              "handles on a track laid out by its "
              "bars, each at its place and its number said, two boxes at its ends, the count at the right, None a tick "
              "under it, and Clear while it is set",
              re.findall(r'<span class="sf-bar( in)?" data-from="(\d+)"', year_html) == [("", "2017"), (" in", "2020")]
              and 'style="height: 100%" data-tip="2015 to 2019: 3 records"' in year_html
              and 'style="height: 67%" data-tip="2020 to 2024: 2 records"' in year_html
              and '<input type="range" class="sf-handle sf-from" data-end="from" min="0" max="2" step="any" value="0.6667" '
                  'aria-valuetext="2019"' in year_html
              and '<input type="range" class="sf-handle sf-to" data-end="to" min="0" max="2" step="any" value="2" '
                  'aria-valuetext="2021"' in year_html
              and 'style="--lo: 0.3333; --hi: 1"' in year_html and 'data-runs="2017-2019 2020-2021"' in year_html
              and '<input type="number" class="sf-rnum" data-end="from" min="2017" max="2021" step="1" value="2019"' in year_html
              and '<span class="sf-rto">to</span>' in year_html and '<span class="sf-cn">3</span></div>' in year_html
              and 'data-v="|none"' in year_html and ">Clear</button>" in year_html and 'data-low="2017" data-high="2021"' in year_html,
              year_html[:400])
        check("115, round 2, updated 12 October (121): My rating's slider runs from one star to five, its unit stars, with "
              "Not rated under it and no Clear until it is set",
              'min="1" max="5"' in rating_html and '<span class="sf-runit">stars</span>' in rating_html
              and rating_html.count('type="checkbox"') == 1 and ">Not rated<" in rating_html and ">Clear</button>" not in rating_html
              and rating_html.count('class="sf-bar in"') == 5, rating_html[:300])
        found_html, plain_html, whole_html = out.get("foundHtml", ""), out.get("plainHtml", ""), out.get("wholeHtml", "")
        check("115, updated 12 October (121) and 17 October, later: a choice at nought is shown, muted while its box is off, "
              "never hidden, and a ticked one is kept and ticked though nothing would show, in the ink as any ticked choice, "
              "where it stood faint though its box still worked, each database with its dot, its name whole on hover",
              '<label class="sf-choice zero" title="PsycInfo"><input type="checkbox" data-v="psycinfo" checked><span class="sf-dbdot" '
              'data-db="psycinfo" aria-hidden="true"></span><span class="sf-cw">PsycInfo</span><span class="sf-cn">0</span></label>'
              in found_html, found_html[:300])
        check("115, round 2: a group of more than four shows its first four and Show more, the whole and Show less once more is "
              "pressed, a ticked one past the four always shown, and no rule that shows a group whole when it would hide few",
              plain_html.count('type="checkbox"') == 4 and 'data-act="more">Show more</button>' in plain_html
              and whole_html.count('type="checkbox"') == 5 and 'data-act="more">Show less</button>' in whole_html
              and 'data-v="|new" checked' in out.get("tickedHtml", "") and out.get("tickedHtml", "").count('type="checkbox"') == 5
              and "const TB_FACET_SHOW = 4;" in support.table_js() and "FACET_SPARE" not in sjs + support.table_js(), plain_html[-200:])
        find_box, found1, accent = out.get("findBox", ""), out.get("found1", ""), out.get("foundAccent", "")
        check("115, round 2: a group of more than ten has a find box at its head that narrows its choices as he types, every "
              "word typed matched in any case and with accents set aside, all it leaves shown, and a short group has none",
              '<input type="search" class="sf-gfind" data-act="find" value="" placeholder="Find" aria-label="Find in Journal"' in find_box
              and find_box.count('type="checkbox"') == 4
              and found1.count('type="checkbox"') == len([i for i in range(1, 32) if "1" in str(i)])
              and 'data-act="more"' not in found1 and accent.count('type="checkbox"') == 1 and ">Revue Émue<" in accent
              and 'type="search"' not in plain_html and "const TB_FACET_FIND = 10;" in support.table_js(), found1[:300])
        check("115: a group under its name in small capitals, Clear only while it holds a tick, each reason under Reject with its "
              "meaning, and Abstract source with an ⓘ that says its line on hover and on focus",
              ">Clear</button>" not in plain_html and 'role="group" aria-labelledby="sf-g-0" data-g="found"' in plain_html
              and '<label class="sf-choice sub" title="E1 Not about singing">' in out.get("decisionHtml", "")
              and '<span class="sf-cw"><span class="mono">E1</span> Not about singing</span>' in out.get("decisionHtml", "")
              and '<h3 class="sf-group-head" id="sf-g-9" title="Abstract source">Abstract source</h3><span class="sf-about" tabindex="0" role="note" '
              'aria-label="When more than one database found a record, the one whose abstract Sift kept." data-tip="When more '
              'than one database found a record, the one whose abstract Sift kept.">ⓘ</span>' in out.get("aboutHtml", ""),
              out.get("aboutHtml", "")[:300])
        check("115, round 2: filters kept from before in whatever form are read without error: one pick as a tick, a search by "
              "its key, an older range as a slider's ends, older ticks of stars and bands of participants as the ends they "
              "span with None, ends given the wrong way round put right, None on the rating kept as Not rated (121), and "
              "words, a number searched, a column gone and a value a fixed group never offers let go",
              out.get("read") == {"found": ["scopus"], "year": {"from": 2019, "to": 2021, "none": False},
                                  "participants": {"from": 11, "to": 50, "none": True}, "decision": ["exclude:E1"],
                                  "pdf": ["yes"], "rating": {"from": 4, "to": 5, "none": False}, "journal": ["invented voice"],
                                  "col_method": ["IPA"]}
              and out.get("readMore") == {"rating": {"from": None, "to": None, "none": True},
                                          "year": {"from": 2010, "to": 2030, "none": False}} and out.get("readRows") == [],
              json.dumps(out.get("read")))
        check("115, round 2: each database Sift knows has its own colour, any other one of six by its name, the same name the "
              "same colour whatever its case, a database a pill, the abstract's source a database's pill and a publication "
              "type pills, one a type",
              out.get("dbKeys", [])[:8] == ["scopus", "psycinfo", "psycinfo", "wos", "pubmed", "epmc", "openalex", "chasing"]
              and re.fullmatch(r"p[0-5]", (out.get("dbKeys") or ["", "", "", "", "", "", "", "", "x"])[8] or "")
              and out.get("dbKeys", [None] * 10)[8] == out.get("dbKeys", [None] * 10)[9]
              and out.get("dbPill") == '<span class="sf-db" data-db="wos">Web of Science</span>'
              and out.get("sourceCell") == '<span class="sf-db" data-db="openalex">OpenAlex</span>'
              and out.get("typeCell") == '<span class="sf-cat">Journal article</span><span class="sf-cat">Review</span>'
              and out.get("linkCell", "").startswith('<a href="https://example.org/choir"'), str(out.get("dbKeys")))
        check("115, round 2, updated 12 October (117, 126): a reason is a pill of its own after the decision's, "
              "No, its code inside and its meaning from reasons.csv on hover",
              out.get("pills") == ['<span class="sf-pill" data-decision="exclude">No</span><span class="sf-pill sf-rpill" '
                                   'title="Not about singing">E1</span>', '<span class="sf-pill" data-decision="include">Yes</span>',
                                   '<span class="sf-pill sf-rpill" title="Not about singing">E1</span>'], str(out.get("pills")))
    else:
        skip("115: the groups and their counts in node", "no node on this machine")

    # ── D. the page: the sidebar, its toggle and its state, the headings, the sliders, the pills
    # the headings' markup from the family's tbTvHeadHtml since the family codebase's third build, sfTvHeadHtml's
    # since 14 October (143), which sfTvHeadDraw puts in place
    head_fn = fn(sjs, "sfTvHeadDraw") + fn(support.table_js(), "tbTvHeadHtml")
    boot = fn(sjs, "sfTvBoot")
    check("115, updated 12 October (125): the filter row under the headings is gone with its number search and words "
          "contained, and a click on a heading sorts, Shift adding a key, a drag of it moving its column",
          "sf-filters" not in sjs + scss + page and "sf-filter" not in sjs + scss and "sfFilterControl" not in sjs
          and "sfNumbersWanted" not in sjs and "return `<tr class=\"sf-heads\">${heads}</tr>`;" in head_fn
          and "$('sf-thead').innerHTML = tbTvHeadHtml(cols, SF.sort, sfHeadKind);" in head_fn
          and "sfSortBy(btn.dataset.sort, e.shiftKey)" in fn(sjs, "sfThClick") and "$('sf-thead').addEventListener('click', sfThClick);" in boot
          and "'input'" not in boot.split("$('sf-thead')", 1)[1].split("const groups", 1)[0]
          and "'change'" not in boot.split("$('sf-thead')", 1)[1].split("const groups", 1)[0])
    facets = screen_html.split('<aside class="sf-facets"', 1)[1].split("</aside>", 1)[0] if 'class="sf-facets"' in screen_html else ""
    check("115, updated 12 October (121): the sidebar stands at the left of the table, inside its view, the groups alone, "
          "its heading and close gone since its toggle stands over it with Clear all beside it",
          'id="sf-facets" aria-label="Filters" hidden>' in screen_html and '<h2 class="sf-side-head">Filters</h2>' not in facets
          and 'id="sf-facets-clear" hidden>Clear all</button>' in flat(screen_html.split('<div class="sf-tv-top"', 1)[-1].split("</div>", 1)[0])
          and 'id="sf-facets-close"' not in screen_html
          and 'id="sf-groups"' in facets and 'type="search"' not in facets
          and screen_html.index('id="sf-tv"') < screen_html.index('id="sf-facets"') < screen_html.index('id="sf-tv-box"')
          and "if (key) {" in fn(sjs, "sfClear") and "delete SF.filters[key];" in fn(sjs, "sfClear")
          and "SF.filters = {};\n    SF.facetsFind = {};" in fn(sjs, "sfClear")
          and "$('sf-facets-clear').onclick = () => sfClear(null);" in boot)
    check("115, updated 12 October (116, 121): its toggle at the top left of the table, over the sidebar, Filters, pressed "
          "while it is open, saying how many filters are on, there in the table alone, never on the title bar, and the "
          "toggle opens and shuts it",
          'id="sf-facets-toggle" type="button" title="Filters" aria-label="Filters" aria-pressed="false"' in screen_html
          and 'id="sf-facets-toggle"' not in rail
          and "sfFacetsMark();" in fn(sjs, "sfBar") and "dataset.ticked" not in sjs
          and '#sf-facets-toggle[data-count="true"]' in scss and "data-ticked" not in scss
          and "$('sf-facets-toggle').onclick = () => sfFacetsOpen($('sf-facets').hidden);" in boot
          and "sf-facets-close" not in sjs)
    check("115: its state kept in this browser as the PDF pane's is, open at first on a wide screen and shut under 900 pixels, "
          "an overlay from the left at phone width that Esc shuts",
          "const SF_FACETS_KEY = 'idiograph-sift-filters';" in sjs and "const SF_FACETS_NARROW = '(max-width: 899px)';" in sjs
          and "localStorage.setItem(SF_FACETS_KEY, open ? 'open' : 'shut');" in fn(sjs, "sfFacetsOpen")
          and "return held === null ? null : held === 'open';" in fn(sjs, "sfFacetsStored")
          and "sfFacetsOpen(!sfFacetsNarrow() && sfFacetsStored() !== false, false);" in fn(sjs, "siftOpen")
          and "sfFacetsOpen(false);" in fn(sjs, "sfKeyDown")
          and ".sf-facets {\n    position: absolute; top: 0; left: 0;" in scss.split("@media (max-width: 759px)", 1)[1])
    check("115: a tick lays the rows out again, its group's ticks a list, the counts and charts drawn with the table, the "
          "sidebar built again only when it changed, the control he was on given its focus back and a find box its caret, "
          "and a tick box never takes Sift's keys",
          "sfRefilter();" in fn(sjs, "sfTick") and "if (now.size) SF.filters[key] = [...now];" in fn(sjs, "sfTick")
          and "sfFacetsDraw();" in fn(sjs, "sfTvDraw") and "if (html === SF.facetsHtml) return;" in fn(sjs, "sfFacetsDraw")
          and "back.focus();" in fn(sjs, "sfFacetsDraw") and "back.setSelectionRange(caret[0], caret[1]);" in fn(sjs, "sfFacetsDraw")
          and "const bars = sfRangeBars(rows, groups, SF.filters, SF.stage);" in fn(sjs, "sfFacetsDraw")
          and "SF.filters = sfTicksRead(SF.filters, sfGroups(" in fn(sjs, "sfApply")
          and "closest('textarea, input:not([type=\"checkbox\"]), select')" in fn(sjs, "sfKeyDown")
          and "and its filter kept" in sjs.split("function sfColsSave(", 1)[0][-300:]
          and "delete SF.filters[k]" not in fn(sjs, "sfColsSave"))
    move = fn(sjs, "sfRangeMove")
    check("115, round 2: while a handle moves its numbers, the stretch between the handles, the count and the chart's bars "
          "follow at once, the lower never past the upper, and when it is let go or a box is left the rows are laid out "
          "again, a slider at its full range held open so it filters nothing, and Esc empties a find box",
          "if (el.type === 'range' && el.dataset.end) sfRangeMove(el, false);" in boot
          and "if (e.target.dataset && e.target.dataset.end) { sfRangeMove(e.target, true); return; }" in boot
          and "if (el.dataset.end === 'from') from = to;" in move and "count.textContent = String(n);" in move
          and "b.classList.toggle('in'" in move and "sfRangeSet(key, Object.assign(sfRangeHeld(SF.filters[key]), { from, to }));" in move
          and "if (held.from !== null && held.from <= g.low) held.from = null;" in fn(sjs, "sfRangeSet")
          and "if (held.to !== null && held.to >= g.high) held.to = null;" in fn(sjs, "sfRangeSet")
          and "sfFind(e.target, '')" in fn(sjs, "sfKeyDown"))
