"""Area 320: a thematic analysis project's Themes board as its thematic map (themesbuild, 2 November 2026, Adam's
choices of the drawings that evening): the status bar counting the codes from the code list, so a code that never
reached the board counts as not placed, Compact on the status bar kept in the settings across a restart, the table of
themes listing each theme with its codes and their extracts in the order the board reads them, and an IPA project's
board counting, tabbing and tabulating as before. The page's script runs in node with the text layer in front of it,
on an invented project about allotment gardens."""
from __future__ import annotations

import json
import shutil

from . import support
from .support import check

# an invented study: two participants, four codes in the list, three of them on the board, one never there
FIXTURE = {
    "cases": [
        {"case": "P1 - Wren", "who": "Wren", "in": True, "lines": {
            "Wren:2:0": {"text": "Soil as a slow friend", "sheet": "Wren", "row": 2, "time": "01:10", "seconds": 70,
                         "quotes": ["\"It takes years to know it.\""]},
            "Wren:5:0": {"text": "Sharing the shed", "sheet": "Wren", "row": 5, "time": "04:02", "seconds": 242,
                         "quotes": ["\"Nobody locks it.\""]},
            "Wren:9:0": {"text": "Rain as permission to stop", "sheet": "Wren", "row": 9, "time": "08:30", "seconds": 510,
                         "quotes": ["\"When it rains I go home and I don't feel bad.\""]}}},
        {"case": "P2 - Moss", "who": "Moss", "in": True, "lines": {
            "Moss:3:0": {"text": "soil as a slow friend", "sheet": "Moss", "row": 3, "time": "02:00", "seconds": 120,
                         "quotes": ["\"You learn its moods.\""]},
            "Moss:7:0": {"text": "Seeds swapped at the gate", "sheet": "Moss", "row": 7, "time": "06:45", "seconds": 405,
                         "quotes": ["\"Every spring a bag of them turns up.\""]}}},
    ],
    "board": {
        "cards": {
            "P1 - Wren/es/Wren:2:0": {"kind": "es", "case": "P1 - Wren", "x": 100, "y": 100, "text": "Soil as a slow friend"},
            "P1 - Wren/es/Wren:5:0": {"kind": "es", "case": "P1 - Wren", "x": 100, "y": 300, "text": "Sharing the shed"},
            "P2 - Moss/es/Moss:7:0": {"kind": "es", "case": "P2 - Moss", "x": 600, "y": 100, "text": "Seeds swapped at the gate"},
        },
        "groups": [
            {"id": "G2", "label": "Giving without counting", "x": 0, "y": 0, "members": ["P1 - Wren/es/Wren:5:0"]},
            {"id": "G1", "label": "The plot as a patient teacher", "x": 0, "y": 0, "description": "What the ground teaches by taking its time",
             "members": ["P1 - Wren/es/Wren:2:0", "G2"]},
        ],
        "discarded": [],
    },
    "list": ["Rain as permission to stop", "Seeds swapped at the gate", "Sharing the shed", "Soil as a slow friend"],
}

HARNESS = r"""
const F = JSON.parse(process.argv[2] || 'null') || FIX;
const out = {};
function setUp(method, listed) {
  TH.project = { method };
  TH.mode = 'gets';
  TH.lpets = false;
  TH.lgets = false;
  TH.gets = { cases: JSON.parse(JSON.stringify(F.cases)), study: {}, settings: {}, minimum: 0, total: 2 };
  TH.v = JSON.parse(JSON.stringify(F.board));
  TH.layout = {};
  TH.codesFrom = null;
  TH.codeList = listed ? { codes: F.list.map((name, i) => ({ id: `c${i + 1}`, name, description: '' })), v: 'x' } : null;
}
setUp('ta', true);
out.ta = thStatusNumbers(TH.v, true);
out.taSaid = tIn('ta', () => thStatusSumText(thStatusSum(out.ta, true)));
// before the list has come the board counts its cards, as it did
setUp('ta', false);
out.taCards = thStatusNumbers(TH.v, true);
// a code set aside counts as set aside, its card in the board's set aside
setUp('ta', true);
TH.v.discarded = ['P2 - Moss/es/Moss:7:0'];
out.taAside = thStatusNumbers(TH.v, true);
// the table's rows: each theme, its codes, its subthemes inside it, then the codes in no theme
setUp('ta', true);
out.flat = thTableFlat(TH.v);
out.table = tIn('ta', () => gtTableTa(TH.v));
out.tabsTa = thTabsOf('gets');
out.ptabsTa = gtPtabsOn();
TH.config = { card_compact: true };
out.compactTa = thCompactOn();
out.cardTa = gtCodeCardHtml(TH.v, 'P1 - Wren/es/Wren:2:0', TH.v.cards['P1 - Wren/es/Wren:2:0'], thParents(TH.v));
// a participant's key extract under a theme: the first of theirs in the theme's order until one is ticked, the tick
// kept as the theme's row for them, the field IPA's board keeps its row quotes in
TH.config = {};
out.keyAuto = gtTaKeyExtract(TH.v, 'G1', 'P2 - Moss');
out.ticks = (tIn('ta', () => gtCodePanelHtml(TH.v, 'P1 - Wren/es/Wren:2:0', 'G1')).match(/data-gtick="[^"]+" data-gget="G1"/g) || []).length;
gtRowSet(TH.v, 'G1', 'P2 - Moss', { quote: 'Moss:3:0' });
out.keyChosen = gtTaKeyExtract(TH.v, 'G1', 'P2 - Moss');
out.rows = TH.v.rows;
out.statusSubs = tIn('ta', () => thStatusSumText(thStatusSum(thStatusNumbers(TH.v, true), true)));
// an IPA project's board on the same cards: its cards counted, its Guidance tab, no panel tabs, no Compact
setUp('ipa', true);
out.ipa = thStatusNumbers(TH.v, true);
out.ipaFlat = thTableFlat(TH.v);
out.tabsIpa = thTabsOf('gets');
out.ptabsIpa = gtPtabsOn();
out.compactIpa = thCompactOn();
console.log(JSON.stringify(out));
"""


def test_themes_map(scratch):
    print("\n320. A thematic analysis project's Themes board as its thematic map: the codes counted from the code "
          "list, Compact kept, the table of themes by its codes, an IPA project's board as before")
    import server as server_mod

    # ── the page's script in node
    support.node_text_layer(scratch)
    js = support.text("apps/idiograph/static/themes.js")
    stubs = ("const $ = () => null; const say = () => {}; const api = async () => ({});\n"
             "const tList = (xs) => xs.join(', ');\n")
    script = stubs + js + f"\nconst FIX = {json.dumps(FIXTURE)};\n" + HARNESS
    run = support.run_node(script, scratch, "themes-map-320.js", timeout=60)
    try:
        out = json.loads(run.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        out = {}
    why = (run.stdout + run.stderr)[-600:]

    ta = out.get("ta") or {}
    check("320: the status bar counts the code list's codes, a code that never reached the board not placed and one "
          "loose on the canvas not placed, two themes counted as one with its subtheme inside",
          (ta.get("placed"), ta.get("unplaced"), ta.get("binned"), ta.get("pets")) == (2, 2, 0, 1), why)
    check("320: the bar says it as codes, \"4 codes: 2 in themes, 2 not placed\" with the themes after it",
          out.get("taSaid", [""])[0].startswith("4 ") and " in themes" in out.get("taSaid", [""])[0]
          and "2 not placed" in out.get("taSaid", [""])[0], str(out.get("taSaid")))
    check("320: the bar counts the themes and their subthemes, \"1 theme, 1 subtheme\"",
          (out.get("statusSubs") or ["", ""])[-1] == "1 theme, 1 subtheme", str(out.get("statusSubs")))
    check("320: under a theme each extract of a code carries a tick, a participant's key extract the first of theirs in "
          "the theme until one is ticked, and the tick kept as the theme's row for them in the board's rows",
          out.get("ticks") == 2 and out.get("keyAuto") == {"key": "Moss:3:0", "chosen": False}
          and out.get("keyChosen") == {"key": "Moss:3:0", "chosen": True}
          and (out.get("rows") or {}).get("G1", {}).get("P2 - Moss", {}).get("quote") == "Moss:3:0",
          f"{out.get('ticks')} {out.get('keyAuto')} {out.get('keyChosen')} {out.get('rows')}")
    cards = out.get("taCards") or {}
    check("320: before the list has come the board counts its cards, three of them",
          (cards.get("placed"), cards.get("unplaced")) == (2, 1), str(cards))
    aside = out.get("taAside") or {}
    check("320: a code whose card is set aside counts as set aside",
          (aside.get("placed"), aside.get("binned"), aside.get("unplaced")) == (2, 1, 1), str(aside))

    flat = [(r["kind"], r["id"]) for r in out.get("flat") or []]
    check("320: the table of themes reads each theme, its own codes, then its subthemes with theirs, then the codes in no theme",
          flat == [("label", "G1"), ("statement", "P1 - Wren/es/Wren:2:0"), ("label", "G2"),
                   ("statement", "P1 - Wren/es/Wren:5:0"), ("statement", "P2 - Moss/es/Moss:7:0")], str(flat))
    table = out.get("table") or ""
    check("320: each code in the table once, with its extracts counted from every participant and each extract under it, "
          "and the code that never reached the board under Not placed",
          table.count(">Soil as a slow friend <") == 1 and "2 extracts" in table
          and "It takes years to know it." in table and "You learn its moods." in table
          and "Rain as permission to stop" in table and "Not placed (2)" in table, table[:300])
    check("320: the table says nothing of PETs or GETs, and lists no participant with nothing under a theme",
          "PET" not in table and "GET" not in table and "Nothing under" not in table and "No codes, so" not in table)

    check("320: a thematic analysis project's board has the Codes and Participants tabs, no Guidance tab, and Compact "
          "draws a code's card as its name alone",
          out.get("ptabsTa") is True and "guidance" not in (out.get("tabsTa") or []) and out.get("compactTa") is True
          and "gt-kicker" not in (out.get("cardTa") or "x") and "Soil as a slow friend" in (out.get("cardTa") or ""),
          str(out.get("tabsTa")))

    ipa = out.get("ipa") or {}
    check("320: an IPA project's board on the same cards counts its cards as before, the code list never read",
          (ipa.get("placed"), ipa.get("unplaced"), ipa.get("binned")) == (2, 1, 0), str(ipa))
    check("320: an IPA project's board keeps its Guidance tab and its table's rows, with no panel tabs and no Compact",
          "guidance" in (out.get("tabsIpa") or []) and out.get("ptabsIpa") is False and out.get("compactIpa") is False
          and [r["id"] for r in out.get("ipaFlat") or []][:1] == ["G1"], str(out.get("tabsIpa")))

    # ── Compact kept across a restart: off on a new install, his choice written to the settings and read back
    cfg = scratch / "map-config.json"
    root = scratch / "map-root"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Adam"}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = cfg, None, {"recent": []}
        fresh = server_mod.config().get("card_compact")
        server_mod.api_settings({"card_compact": True})
        written = json.loads(cfg.read_text(encoding="utf-8")).get("card_compact")
        again = server_mod.config().get("card_compact")
        server_mod.api_settings({"card_compact": False})
        off = server_mod.config().get("card_compact")
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_MEMORY = kept
    check("320: Compact is off on a new install, kept in the settings file when pressed and read back on the next start, "
          "and off again when pressed again",
          fresh is False and written is True and again is True and off is False, f"{fresh} {written} {again} {off}")
