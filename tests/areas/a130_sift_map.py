from __future__ import annotations

import contextlib
import csv
import io
import json
import shutil

from . import support
from .support import check, sift_words_js, skip


def test_sift_map(scratch):
    print("\n130. The filters by their counts and Country on a map, 13 October, later: every group of names by its counts, "
          "the most first and the noughts last, a tie in the group's own order, a scale kept in its order, the group "
          "being ticked held, Show on map beside Country, the map from static/world.json on Equal Earth, its counts the "
          "Country group's, the records with no country under it, and the map saved in the light appearance on white")
    import subprocess
    import sift
    import sift_search as ss
    import make_world
    import sys
    sys.path.insert(0, str(support.source("packaging")))
    import build_mac as build_mac_mod

    app_src = support.text("family/static/shell.js", "apps/idiograph/static/distil.js")
    sift_src = support.text("apps/sift/static/sift.js")
    notice = support.source("NOTICE.md").read_text(encoding="utf-8")
    build_src = support.source("packaging/build_mac.py").read_text(encoding="utf-8")
    maker_src = support.source("apps/sift/make_world.py").read_text(encoding="utf-8")
    world_path = support.source("apps/sift/static/world.json")
    world_text = world_path.read_text(encoding="utf-8")
    world = json.loads(world_text)
    fn = lambda src, name: src.split(f"function {name}(", 1)[1].split("\n}", 1)[0] if f"function {name}(" in src else ""
    whole = lambda src, name: f"function {name}(" + fn(src, name) + "\n}"
    node = shutil.which("node")
    base = scratch / "sift-map-130"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)

    # ── A. world.json: what it holds, its size, nothing of the web in it
    inside = lambda p: isinstance(p, list) and 0 <= p[0] <= world["width"] and 0 <= p[1] <= world["height"]
    check("130: world.json loads, Equal Earth in a frame 1000 wide, with GB, US, FR, NO, SG and MT among its label "
          "points, each inside the frame, under 150 KB, and no Antarctica",
          world["projection"] == "Equal Earth" and world["width"] == 1000 and 300 < world["height"] < 600
          and all(inside(world["points"].get(c)) for c in ("GB", "US", "FR", "NO", "SG", "MT", "HK"))
          and len(world_text.encode("utf-8")) < 150_000 and "AQ" not in world["points"]
          and "AQ" not in [s["code"] for s in world["shapes"]] and len(world["shapes"]) > 170,
          f"{len(world_text.encode('utf-8'))} bytes, {len(world['points'])} points")
    check("130: every country of world.json is named as Sift's Country column names it, and nothing in it is fetched",
          all(world["names"].get(c) == sift.country_name(c) for c in world["points"]) and set(world["names"]) == set(world["points"])
          and "http" not in world_text and world["sphere"].startswith("M") and "Natural Earth 5.1.2" in world["source"])

    # ── B. make_world.py on two invented files, given by path, fetching nothing
    def feature(props, ring):
        return {"type": "Feature", "properties": props, "geometry": {"type": "Polygon", "coordinates": [ring]}}
    square = lambda x, y, s: [[x, y], [x + s, y], [x + s, y + s], [x, y + s], [x, y]]
    outlines = {"type": "FeatureCollection", "features": [
        feature({"ISO_A2": "-99", "ISO_A2_EH": "FR", "LABEL_X": 2, "LABEL_Y": 46}, square(0, 40, 8)),
        feature({"ISO_A2": "AQ", "ISO_A2_EH": "AQ", "LABEL_X": 0, "LABEL_Y": -80}, square(-20, -85, 30)),
        feature({"ISO_A2": "-99", "ISO_A2_EH": "-99", "LABEL_X": 30, "LABEL_Y": 10}, square(28, 5, 6))]}
    labels = {"type": "FeatureCollection", "features": [
        feature({"ISO_A2": "-99", "ISO_A2_EH": "FR", "LABEL_X": 2.5, "LABEL_Y": 46.5}, square(0, 40, 8)),
        feature({"ISO_A2": "SG", "ISO_A2_EH": "SG", "LABEL_X": 103.8, "LABEL_Y": 1.35}, square(103.6, 1.2, 0.4)),
        feature({"ISO_A2": "AQ", "ISO_A2_EH": "AQ", "LABEL_X": 0, "LABEL_Y": -80}, square(-20, -85, 30))]}
    (base / "outlines.geojson").write_text(json.dumps(outlines), encoding="utf-8")
    (base / "points.geojson").write_text(json.dumps(labels), encoding="utf-8")
    made = make_world.build(base / "outlines.geojson", base / "points.geojson")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = make_world.main([str(base / "outlines.geojson"), str(base / "points.geojson"), "--out", str(base / "w.json")])
    x0, y0 = make_world.project(0, 0)
    half = make_world.project(180, 0)[0]
    north = make_world.project(0, 90)[1]
    check("130: make_world.py takes ISO_A2_EH, so France with -99 in ISO_A2 is France, leaves Antarctica out, keeps a "
          "shape with no code unnamed, and takes every label point from the second file",
          [s["code"] for s in made["shapes"]] == ["FR", ""] and sorted(made["points"]) == ["FR", "SG"]
          and made["names"] == {"FR": "France", "SG": "Singapore"} and all(0 <= p[0] <= 1000 for p in made["points"].values())
          and code == 0 and (base / "w.json").is_file() and "written to" in out.getvalue(), str(made["points"]))
    check("130: its projection is Equal Earth, nought at nought, the equator's half width about 2.7066 and the pole "
          "about 1.3173",
          (x0, y0) == (0.0, 0.0) and abs(half - 2.7066) < 1e-3 and abs(north - 1.3173) < 1e-3, f"{half} {north}")
    check("130: make_world.py reads its two files by path, under python3 -I, and asks nothing of the web",
          "ISO_A2_EH" in maker_src and "LABEL_X" in maker_src and "LABEL_Y" in maker_src and "python3 -I" in maker_src
          and not any(w in maker_src for w in ("urllib", "http", "requests", "socket"))
          and "add_argument(\"outlines\"" in maker_src and "add_argument(\"points\"" in maker_src)

    # ── C. an invented screening on lighthouse keepers, its filters in node
    review = base / "light-review"
    review.mkdir()
    ss.new_plan(review, "Lighthouse keepers", "How do keepers live with the light?")
    ss.save(review, {"databases": ["psycinfo"], "blocks": [{"name": "Lights", "terms": ["lamp*", "beacon", "lens", "fog*"]}]})
    run = review / "runs" / "2031-06-01"
    run.mkdir(parents=True)
    rows = [("L1", "A beacon on the rock", "Keepers spoke of the night.", "Index A; Index B", "GB; IE", "green"),
            ("L2", "The beacon and the lamp", "Lamps at night.", "Index B", "GB", "closed"),
            ("L3", "Beacon nights", "Long watches.", "Index B; Index C", "US", "gold"),
            ("L4", "In the lens room", "Polishing glass.", "Index B; Index C", "GB; FR", "closed"),
            ("L5", "Keepers alone", "Solitude at sea.", "Index C", "", ""),
            ("L6", "Supply boats", "Boats came weekly.", "Index C", "", "closed"),
            ("L7", "Island postings", "The lens and the lamp abroad.", "Index A", "GI", ""),
            ("L8", "Signals by day", "Flags, horns and a beacon.", "Index C", "MT", "closed")]
    with open(run / sift.CSV_NAME, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["rec_id", "title", "authors", "year", "journal", "doi", "sources", "abstract", "countries", "open_access"])
        for i, (rec, title, abstract, sources, countries, oa) in enumerate(rows, 1):
            w.writerow([rec, title, "Gale, Ina", str(2010 + i), "Invented Light Journal", f"10.5555/light.{i}", sources,
                        abstract, countries, oa])
    sift.column(run, "add", name="Lamp kind", kind="choice", options="Oil\nElectric")
    for rec, v in (("L1", "Electric"), ("L2", "Electric"), ("L3", "Oil")):
        sift.set_field(run, rec, "col_lamp_kind", v)
    view = sift.screen(run)

    if not node:
        skip("130: the filters' order and the map in node", "node is not installed")
    else:
        lead = app_src[app_src.index("const esc = "):app_src.index("// a line from the server with a command in backticks")]
        block = sift_src.split("/* ── the table's rows: its columns, sort and filter, worked out with no page ── */", 1)[-1].split(
            "/* ── the table, drawn ── */", 1)[0]
        block = support.table_js() + "\n" + block
        drawn = [whole(sift_src, n) for n in ("sfRangeEnds", "sfBarsHtml", "sfRangeHtml",
                                              "sfBarTipHide", "sfFacetsMark", "sfFacetsData", "sfFacetsHoldAt", "sfFacetsDraw")]
        harness = r"""
const els = {};
const mk = () => ({ hidden: false, innerHTML: '', textContent: '', title: '', dataset: {}, style: {}, setAttribute() {},
  contains: () => false, querySelectorAll: () => [], querySelector: () => null });
const $ = (id) => els[id] || (els[id] = mk());
const document = { activeElement: null };
$('sf-map').hidden = true;
const WORLD = __WORLD__;
const VIEW = __VIEW__;
const codes = [{ code: 'E1', meaning: 'Not keepers' }, { code: 'E2', meaning: 'Not lights' }, { code: 'E3', meaning: 'Not lived' }];
const SF = { stage: 'ta', filters: {}, table: VIEW.table, records: VIEW.records, blocks: VIEW.blocks, keyWorks: [],
  reasons: { ta: codes, ft: [] }, roundIds: VIEW.records.map((r) => r.rec_id), form: false, formBench: new Set(), formInc: new Set(),
  facetsMore: new Set(), facetsFind: {}, facetsHtml: '', facetsOrder: {}, facetsHold: null };
SF.byId = new Map(SF.records.map((r) => [r.rec_id, r]));
// three left out at title and abstract, two for E3 and one for E1, none for E2
[['L5', 'E3'], ['L6', 'E3'], ['L7', 'E1']].forEach(([id, reason]) => { SF.byId.get(id).stages.ta = { decision: 'exclude', reason }; });
const sfCodes = () => SF.reasons[SF.stage] || [];
const sfRoundRows = () => sfBaseIds().map((id) => SF.byId.get(id)).filter(Boolean);
const order = (k) => (SF.facetsOrder[k] || []).slice();
const out = {};
sfFacetsDraw();
const html1 = $('sf-groups').innerHTML;
const own = sfAllCols().find((c) => c.own);
out.zeroBox = [tbChoiceHtml({ value: 'a', label: 'A' }, 0, false), tbChoiceHtml({ value: 'b', label: 'B' }, 0, true),
  tbChoiceHtml({ value: 'c', label: 'C' }, 3, false)].map((h) => h.includes(' disabled'));
out.first = { terms: order('term:0'), country: order('country'), found: order('found'), oa: order('oa'),
  decision: order('decision'), own: order(own ? own.key : ''), year: (sfGroups(sfRoundRows(), SF.records, sfAllCols(), 'ta', codes, {}).find((g) => g.key === 'year') || {}).range };
const chunk = html1.split('data-g="country"')[1].split(/<div class="sf-group[" ]/)[0];
out.countryHtml = [...chunk.matchAll(/data-v="([^"]*)"/g)].map((m) => m[1]);
out.link = [html1.split('data-act="map"').length - 1, chunk.includes('data-act="map"'), chunk.includes('>Show on map</button>')];
out.shown = [...html1.split('data-g="found"')[1].split(/<div class="sf-group[" ]/)[0].matchAll(/data-v="([^"]*)"/g)].map((m) => m[1]);
// he ticks in Country, its order held, and the counts change under another filter: Country keeps its order
sfFacetsHoldAt('country');
SF.filters = { country: ['france'], oa: ['closed'] };
sfFacetsDraw();
out.held = order('country');
// then he ticks in Open access: Country takes its new order
sfFacetsHoldAt('oa');
sfFacetsDraw();
out.after = order('country');
out.oaHeld = order('oa');
// the map's counts, exactly the Country group's, with another filter ticked
const data = sfFacetsData();
const m = sfMapFrom(WORLD, data.rows, data.groups, data.counts, SF.filters, 'ta');
out.map = { circles: m.circles.map((c) => [c.code, c.name, c.n, c.r]), total: m.total, blank: m.blank,
  unplaced: m.unplaced, line: sfMapLine(m), group: data.counts.country };
SF.filters = {};
const d0 = sfFacetsData();
const m0 = sfMapFrom(WORLD, d0.rows, d0.groups, d0.counts, {}, 'ta');
out.map0 = { circles: m0.circles.map((c) => [c.code, c.n, c.r]), line: sfMapLine(m0), group: d0.counts.country, total: m0.total };
const screen = sfMapSvg(WORLD, m0, null);
const paper = sfMapSvg(WORLD, m0, SF_MAP_PAPER);
out.svg = { screenVar: screen.includes('class="sf-map-dot"') && screen.includes('tabindex="0"') && !screen.includes('fill="#'),
  texts: (paper.split('<g class="sf-map-names"')[0].match(/<text /g) || []).length, nums: m0.circles.map((c) => paper.includes(`>${c.n}</text>`)),
  paperHead: paper.slice(0, 160), rectFirst: paper.indexOf('<rect') < paper.indexOf('sf-map-sea'),
  paperTab: paper.includes('tabindex'), paperFills: ['#FFFFFF', '#EAEFF1', '#D8D2C6', '#D65A4E'].every((f) => paper.includes(`fill="${f}"`)),
  titles: (paper.match(/<title>/g) || []).length, label: (screen.match(/aria-label="([^"]*)"/g) || []).slice(0, 3) };
// a big count beside a small one: the largest at SF_MAP_MOST, a small one held at SF_MAP_LEAST with its number
const big = sfMapModel(WORLD, [{ value: 'united states', label: 'United States' }, { value: 'malta', label: 'Malta' }, { value: 'xx', label: 'XX' }],
  { 'united states': 400, malta: 2, xx: 3 }, 405);
out.big = { circles: big.circles.map((c) => [c.code, c.n, c.r]), unplaced: big.unplaced, line: sfMapLine(big),
  nums: (sfMapSvg(WORLD, big, null).match(/<text [^>]*font-size[^>]*>\d+<\/text>/g) || []).length };
out.file = [sfMapFile('2031-06-01', 'png'), sfMapFile('Run: a/b', 'svg'), sfMapFile('', 'png')];
// with no record holding a country, no Country group and no link
SF.records.forEach((r) => { r.countries = []; });
SF.facetsHtml = '';
sfFacetsDraw();
out.noLink = $('sf-groups').innerHTML.includes('data-act="map"') || $('sf-groups').innerHTML.includes('data-g="country"');
console.log(JSON.stringify(out));
"""
        harness = harness.replace("__WORLD__", world_text).replace("__VIEW__", json.dumps(view))
        script = base / "map-130.js"
        script.write_text("\n".join([lead, sift_words_js(sift_src), block, *drawn, harness]), encoding="utf-8")
        ran = subprocess.run([node, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        out = json.loads(ran.stdout) if ran.returncode == 0 and ran.stdout.strip() else {}
        first = out.get("first", {})
        why = (ran.stderr or json.dumps(out))[:500]
        # updated 14 October, later (137): the terms by their counts among themselves, then More than one, then
        # the block's lines, a field Sift cannot name among them where None of its terms stood
        check("130: in node, a block's terms by their counts, beacon 4 first, then lamp* and lens at 2 each in the plan's "
              "order and fog* at nought last among the terms, then More than one, then the block's lines",
              first.get("terms") == ["beacon", "lamp*", "lens", "fog*", "|many", "|none"], why)
        check("130: in node, Country, the databases and Open access by their counts, Unknown among them, More than one "
              "among the databases, a tie in the group's own order",
              first.get("country") == ["united kingdom", "|none", "france", "gibraltar", "ireland", "malta", "united states"]
              and first.get("found") == ["index c", "index b", "|many", "index a"]
              and first.get("oa") == ["closed", "open", "|none"], why)
        check("130: in node, the decision keeps To screen, Yes, Maybe and No in order, its reasons by their counts under No, "
              "E3 at 2, E1 at 1, then E2 at nought",
              first.get("decision", [])[:7] == ["undecided", "include", "maybe", "exclude", "exclude:E3", "exclude:E1", "exclude:E2"],
              str(first.get("decision")))
        check("130: in node, a scale keeps its own order, his own column's choices as he set them though Electric holds "
              "more, and the year a slider",
              first.get("own", [])[:2] == ["Oil", "Electric"] and first.get("year") is True, str(first.get("own")))
        check("130, updated 17 October, later (115): in node, a choice with no records is there to read and cannot be "
              "ticked, unless it is ticked already, so it can be unticked (14 October, Adam), faint only while its box is off",
              out.get("zeroBox") == [True, False, False], str(out.get("zeroBox")))
        check("130: in node, the group being ticked keeps its order as its counts change, and takes its new order once "
              "he ticks in another group, which then holds its own",
              out.get("held") == first.get("country")
              and out.get("after") == ["united kingdom", "france", "malta", "|none", "gibraltar", "ireland", "united states"]
              and out.get("oaHeld") == first.get("oa"), f"{out.get('held')} {out.get('after')}")
        mp = out.get("map", {})
        placed = {c[1].lower(): c[2] for c in mp.get("circles", [])}
        group = mp.get("group", {})
        check("130: in node, with Open access ticked and France ticked under Country, the map's counts are the Country "
              "group's, its own tick set aside, over the 4 records the other filters leave",
              placed == {k: v for k, v in group.items() if k != "|none" and v and k != "gibraltar"}
              and placed == {"united kingdom": 2, "france": 1, "malta": 1} and mp.get("total") == 4 and mp.get("blank") == 1
              and mp.get("line") == "No country for 1 of 4 records.", json.dumps(mp)[:400])
        check("130: in node, the records with no country are one line under the map, a country it has no point for "
              "counted there by name",
              (m0 := out.get("map0", {})).get("line") == "No country for 2 of 8 records. Not on the map: Gibraltar (1)."
              and m0.get("total") == 8 and "GI" not in {c[0] for c in m0.get("circles", [])}, str(out.get("map0", {}).get("line")))
        check("130: in node, a saved file is named countries after the run's name, kept to what a file name can hold",
              out.get("file") == ["2031-06-01 countries.png", "Run- a-b countries.svg", "countries.png"], str(out.get("file")))

    # ── D. the page: nothing fetched, and the data the build carries
    map_code = "".join(whole(sift_src, n) for n in ("sfMapModel", "sfMapFrom", "sfMapLine", "sfMapSvg", "sfMapOpen", "sfMapClose",
                                                     "sfMapDraw", "sfMapTip", "sfSaveBlob", "sfMapSave", "sfMapBoot"))
    map_consts = "\n".join(ln for ln in sift_src.splitlines() if ln.startswith(("const SF_MAP", "  file: 'countries'", "const sfMap")))
    check("130: nothing is fetched from the web: the map's code names no http, and reads world.json from the app itself "
          "through the app's own api, sift.js still making no request of its own",
          len(map_code) > 3000 and "http" not in map_code + map_consts
          and "SF.world = await api('/world.json');" in fn(sift_src, "sfMapOpen") and "fetch(" not in sift_src)
    check("130: the Mac app carries all of static/, world.json with it, and NOTICE.md credits Natural Earth",
          {p.relative_to(world_path.parent).as_posix() for p in world_path.parent.rglob("*") if p.is_file()} <= set(build_mac_mod.static_files("sift"))
          and "world.json" in build_mac_mod.static_files("sift") and "world.json" not in build_mac_mod.static_files("idiograph") and world_path.parent == support.source("apps/sift/static")
          and "Natural Earth 5.1.2" in notice and "public domain" in notice)

