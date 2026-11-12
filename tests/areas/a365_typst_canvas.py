"""Area 365: the canvas drawn by Typst from the board's saved layout alone (typst4, 9 November 2026, Adam, 9 November
about 18:10: Typst, no fallback). `canvas_out.typst_data` reads a board as the screen's own answer gives it and the
template `typst/canvas-main.typ` measures every card itself and lays the board out by the canvas's own rule, so no
window is needed. Checked on an invented board with every part (a long title, a description, a note and picks, a
sub-PET holding a group holding a group, a frame of many cards, statements that run past four lines, a stack of six,
a missing, a changed and a second sheet's card, loose cards with an AI's reason, sticky notes, a label with nothing
in it), and on the demo's PETs and GETs boards: the frames the template sizes against the app's own rule run in node
on the same sizes, every card's and label's words on the page, and the picture's size following the board. The
invented board is about a beekeeping course, every word made up."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import support
from .support import check, skip

SHEET = "Initial"
LATER = "Later"
LONG = ("Opening the hive for the first time alone and finding the whole frame covered, every bee moving at once, "
        "and standing there long enough to notice my own breathing slow down to match them")
LONGER = ("Learning that the smoke is not a weapon but a message, a way of saying I am here and I mean no harm, "
          "and that the bees answer it by going quiet, which is more than most people do when you say the same")


def _card(key: str, x: int, y: int, text: str, time: str = "", **more) -> dict:
    sheet, row, line = key.split(":")
    return {"key": key, "sheet": sheet, "row": int(row), "line": int(line), "text": text, "seconds": None,
            "time": time, "x": x, "y": y, **more}


def fixture_state() -> dict:
    """An invented PETs board in the shape themes.state answers, every part the canvas draws on it."""
    cards = [
        # the first PET, two rows of cards, one running far past four lines
        _card("Initial:3:0", 0, 0, "Bees as a lesson in patience", "01:10"),
        _card("Initial:3:1", 210, 0, "A veil that never quite feels like enough", "01:10"),
        _card("Initial:5:0", 0, 140, LONG, "02:45"),
        _card("Initial:5:1", 210, 140, "Counting the stings as a kind of tuition", "02:45"),
        # its sub-PET, which holds a group, which holds a group
        _card("Initial:7:0", 0, 380, "The teacher who never wore gloves", "03:30"),
        _card("Initial:7:1", 210, 380, LONGER, "03:30"),
        _card("Initial:9:0", 28, 600, "A hum that changes when something is wrong", "04:05"),
        _card("Initial:11:0", 56, 790, "Hearing the queen before seeing her", "05:12"),
        # a PET of many cards, four across and three down
        *[_card(f"Initial:{13 + 2 * i}:0", 700 + 210 * (i % 4), 140 * (i // 4),
                [LONG, "Honey that tastes of the lime trees", "Being trusted with the extractor",
                 "The weight of a full super", LONGER, "Wax on everything I own", "A swarm on the neighbour's fence",
                 "Getting it wrong in front of the group", "The quiet after closing up", "Labels written by hand",
                 "Sharing the first jar", "Wanting another season"][i], f"{6 + i:02d}:00")
          for i in range(12)],
        # a PET with a stack's top, a line gone from the workbook, a reworded one and a second sheet's
        _card("Initial:41:0", 1700, 0, "Feeling responsible for thirty thousand lives", "19:40"),
        *[_card(f"Initial:41:{n}", 0, 0, f"Responsible again, put another way {n}", "19:40") for n in range(1, 7)],
        _card("Initial:43:0", 1910, 0, "The hive tool lost in the long grass", "", missing=True),
        _card("Initial:45:0", 1700, 140, "Trusting the bees more than the book", "21:15", changed=True,
              stored="Trusting the bees"),
        _card("Later:4:0", 1910, 140, "A year on, still nervous at the first lift", "02:20"),
        # loose on the canvas, one with an AI's reason for leaving it out, and one set aside
        _card("Initial:47:0", 0, 1150, "Buying a second-hand smoker", "22:30", loose=True),
        _card("Initial:49:0", 210, 1150, "The drive to the apiary", "23:05", loose=True),
        _card("Initial:51:0", 420, 1150, "Coffee in a flask", "23:40"),
    ]
    groups = [
        {"id": "g1", "label": "Learning to stand still in front of the hive, and what it asks of the body and the "
                              "nerve before any of the craft", "members": ["Initial:3:0", "Initial:3:1", "Initial:5:0",
                                                                         "Initial:5:1", "g2"],
         "x": 0, "y": -80, "note": "The stillness comes first, then the skill.",
         "description": "Calm learned through the body before the hands know what to do"},
        {"id": "g2", "label": "The teacher's example", "members": ["Initial:7:0", "Initial:7:1", "g3"], "x": 0, "y": 300},
        {"id": "g3", "label": "Listening", "members": ["Initial:9:0", "g4"], "x": 28, "y": 560},
        {"id": "g4", "label": "The queen", "members": ["Initial:11:0"], "x": 56, "y": 750},
        {"id": "g5", "label": "What a season gives back", "members": [f"Initial:{13 + 2 * i}:0" for i in range(12)],
         "x": 700, "y": -40},
        {"id": "g6", "label": "Care as weight", "members": ["Initial:41:0", "Initial:43:0", "Initial:45:0", "Later:4:0"],
         "x": 1700, "y": -40},
        {"id": "g7", "label": "Untitled", "members": [], "x": 1700, "y": 600},
    ]
    stickies = [
        {"id": "n1", "x": 420, "y": 0, "text": "ask about varroa", "colour": "yellow", "in": "g1"},
        {"id": "n2", "x": 700, "y": 600, "text": "Second visit:\nbring the notebook\nand gloves", "colour": "pink"},
        {"id": "n3", "x": 1540, "y": 300, "text": "busiest frame", "colour": "blue", "in": "g5"},
    ]
    return {"schema": 2, "case": "P4 - Quill", "workbook": "P4 - Quill.xlsx", "sheets": [SHEET, LATER],
            "current": "v1", "chosen": None, "complete": None, "versions": [{"id": "v1", "name": "Board 1"}],
            "version": {"id": "v1", "name": "Board 1"}, "saved": True, "quotes": {}, "history": [], "sids": {},
            "cards": cards, "groups": groups, "discarded": ["Initial:51:0"], "picks": {"g1": ["Initial:3:0"]},
            "discard_reasons": {"Initial:47:0": "A purchase, not an experience of the course"},
            "review": None, "stickies": stickies, "revise": [], "stacks": {"Initial:41:0": [f"Initial:41:{n}"
                                                                                           for n in range(1, 7)]},
            "not_same": []}


def typst_query(template: Path, data: dict, fonts: Path):
    """The template's own record of its layout, through typst-py, the engine a run from source uses."""
    import typst
    got = typst.query(str(template), "<canvas-layout>", root=str(template.parent), font_paths=[str(fonts)],
                      ignore_system_fonts=True, sys_inputs={"data": json.dumps(data, ensure_ascii=False)})
    return json.loads(got)[0]["value"]


# the app's own rule in node: the board as thLoad makes it, the screen's sizes as the template measured them, the
# labels laid at rest, then thCanvasWhole with the whole sizes, every frame of the layout it comes to
NODE_RULE = r"""
const data = JSON.parse(DATA);
const got = JSON.parse(GOT);
TH.mode = 'pets';
const cards = {};
for (const c of data.cards) cards[c.key] = Object.assign({}, c);
TH.v = { cards, groups: data.groups.map((g) => Object.assign({}, g, { members: g.members.slice() })),
  discarded: data.discarded.slice(), picks: data.picks, ai: { discarded: data.discard_reasons },
  stickies: data.stickies.map((n) => Object.assign({}, n)), stacks: data.stacks, not_same: [], waits: true };
thWaitsRead(TH.v);
TH.sizes = got.screen;
thLayout(TH.v, thSize, null);
thMakeRoom(TH.v, thSize);
thLayout(TH.v, thSize, null);
const board = thSnap(TH.v);
const whole = {};
for (const [k, s] of Object.entries(got.whole)) whole[k] = s;
const laid = thCanvasWhole(board, whole, thSize);
const frames = {};
for (const [id, l] of Object.entries(laid.layout)) if (l.body) frames[id] = l.frame;
const cardsAt = {};
for (const k of Object.keys(got.whole)) cardsAt[k] = { x: board.cards[k].x, y: board.cards[k].y };
console.log(JSON.stringify({ frames, cards: cardsAt }));
"""


def test_typst_canvas(scratch: Path):
    print("\n365. The canvas drawn by Typst from the board's saved layout: the frame rule, the words and the picture")
    try:
        import typst  # noqa: F401
    except ImportError:
        return skip("the canvas in Typst", "typst-py is not installed")
    import canvas_out
    import typeset
    import pdftext
    fonts = support.source("family/static/fonts")
    if not fonts.is_dir():
        fonts = Path(getattr(typeset, "FONTS", fonts))
    root = scratch / "typst_canvas"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    state = fixture_state()
    data = canvas_out.typst_data(state, canvas_out.heading_of(state["case"], "Board 1"))

    # ── A. what the data carries: on the canvas only what the canvas draws there
    keys = [c["key"] for c in data["cards"]]
    check("the cards set aside, stacked under a top or waiting in Not placed stay off the canvas",
          "Initial:51:0" not in keys and not any(k.startswith("Initial:41:") and k != "Initial:41:0" for k in keys)
          and "Initial:47:0" in keys and len(keys) == 26, str(len(keys)))
    top = next(c for c in data["cards"] if c["key"] == "Initial:41:0")
    check("a stack's top carries four paper edges and the plus past four, and the marks say missing and changed",
          top["edges"] == 4 and top["more"] is True
          and next(c for c in data["cards"] if c["key"] == "Initial:43:0")["mark"]
          and next(c for c in data["cards"] if c["key"] == "Initial:45:0")["mark"]
          and next(c for c in data["cards"] if c["key"] == "Later:4:0")["sheet"] == LATER, str(top))
    check("the title names the case by its pseudonym and the board", data["heading"] == "P4 Quill · Board 1",
          data["heading"])

    # ── B. the frames sized without a window, against the app's own rule in node on the same sizes
    got = typst_query(canvas_out.TEMPLATE, data, fonts)
    taller = [k for k, s in got["whole"].items() if s["h"] > got["screen"][k]["h"]]
    check("the long statements run taller whole than on screen, so the board has to make way",
          {"Initial:5:0", "Initial:7:1"} <= set(taller), str(taller))
    if not shutil.which("node"):
        skip("the frames against the app's rule in node", "no node on this machine")
    else:
        script = (support.i18n_js() + support.source("apps/idiograph/static/themes.js").read_text(encoding="utf-8")
                  + f"\nconst DATA = {json.dumps(json.dumps(state))};\nconst GOT = {json.dumps(json.dumps(got))};\n"
                  + NODE_RULE)
        run = support.run_node(script, root, "rule.js", timeout=60)
        if run.returncode != 0:
            check("the app's rule runs in node", False, run.stderr.strip()[:300])
        else:
            app = json.loads(run.stdout.strip().splitlines()[-1])
            mine = got["frames"]
            off = {gid: [round(abs(mine[gid][k] - f[k]), 2) for k in "xywh"] for gid, f in app["frames"].items()
                   if gid not in mine or max(abs(mine[gid][k] - f[k]) for k in "xywh") > 0.5}
            check("every frame the template sizes is the app's own, a board never opened in a window as one that was",
                  set(mine) == set(app["frames"]) and not off, str(off or (set(mine) ^ set(app["frames"]))))
            moved = {k: (got["pos"][k], at) for k, at in app["cards"].items()
                     if abs(got["pos"][k]["x"] - at["x"]) > 0.5 or abs(got["pos"][k]["y"] - at["y"]) > 0.5}
            check("every card stands where the app's rule puts it once the long ones take their whole height",
                  not moved, str(list(moved.items())[:3]))

    # ── C. every card's and label's words on the page
    pdf = canvas_out.typeset_canvas(data, "pdf")
    flat = lambda s: "".join(str(s).split())
    page = flat("".join(pdftext.pages_text(pdf)))
    missing = [c["text"][:30] for c in data["cards"] if c["drawn"] and flat(c["text"]) not in page]
    missing += [g["label"][:30] for g in data["groups"] if flat(g["label"]) not in page]
    missing += [n["text"][:30] for n in data["stickies"] if flat(n["text"]) not in page]
    check("every card's, label's and note's words are on the page, the title too",
          not missing and flat(data["heading"]) in page and len(pdftext.pages_text(pdf)) == 1, str(missing[:4]))

    # ── D. the picture: two pixels a canvas pixel, its width the board's and its margins'
    png = canvas_out.typeset_canvas(data, "png")
    w, h = canvas_out.png_size(png)
    box = got["box"]
    check("the picture is the board at twice its size with its margins, under its title",
          w == 2 * (box["w"] + 48) and h > 2 * (box["h"] + 48), f"{w}x{h} for {box}")
    wider = json.loads(json.dumps(state))
    next(c for c in wider["cards"] if c["key"] == "Initial:49:0")["x"] += 2500
    png2 = canvas_out.typeset_canvas(canvas_out.typst_data(wider, "P4 Quill · Board 1"), "png")
    w2, h2 = canvas_out.png_size(png2)
    check("a card moved further out makes the picture wider by as much, twice over", w2 - w == 2 * (
        typst_query(canvas_out.TEMPLATE, canvas_out.typst_data(wider, "x"), fonts)["box"]["w"] - box["w"])
          and w2 > w and h2 == h, f"{w}->{w2}, {h}->{h2}")

    # ── E. the demo's boards, read without a window: a PETs board and the GETs board
    import make_demo
    demo = root / "demo"
    shutil.copytree(support.source("demo"), demo, ignore=shutil.ignore_patterns("ta", "source"))
    make_demo.fill(pristine=demo / "pristine", demo=demo)
    juno = canvas_out.pets_data(demo / "Juno" / "Juno - EN & ES.xlsx", "Juno")
    pdf = canvas_out.typeset_canvas(juno, "pdf")
    page = flat("".join(pdftext.pages_text(pdf)))
    lost = [c["text"][:30] for c in juno["cards"] if flat(c["text"]) not in page]
    check("Juno's board on one page, every statement on it whole", len(juno["cards"]) > 30 and not lost,
          str(lost[:3]))
    gets_data = canvas_out.gets_data(demo, make_demo.gets_books(demo), "Demo")
    png = canvas_out.typeset_canvas(gets_data, "png")
    pdf = canvas_out.typeset_canvas(gets_data, "pdf")
    page = flat("".join(pdftext.pages_text(pdf)))
    check("the GETs board carries each card's case badge and kicker, and each GET's count of the cases",
          all(c["badge"] and c["kicker"] for c in gets_data["cards"])
          and all(" of " in g["badge"] for g in gets_data["groups"])
          and all(flat(c["text"]) in page for c in gets_data["cards"] if c["drawn"])
          and canvas_out.png_size(png)[0] > 0, str(gets_data["groups"][0]["badge"]))
    # nothing was written beside the demo's boards
    check("making the canvas writes nothing", not list(demo.glob("**/*.pdf")) and not list(demo.glob("**/*.png")))
