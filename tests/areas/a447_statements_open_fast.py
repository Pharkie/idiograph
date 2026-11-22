"""Area 447: the statements screen's open laid out once (statementsfast, 22 November 2026).

Opening a participant on Experiential statements while another's rows were on screen laid out the screen's bars and
columns over the rows going, before the new ones were drawn: `startCase` now puts the card, the notes field and an
interviewer's note back where they wait and empties the rows before it draws anything. A window's first open took its
first frame 80 to 100 ms later than the opens after it in WebKit, so the screen is laid out once out of sight a few
seconds after Home first has its answer (`esWarm`): fixed over the window and hidden from sight for one layout, put
away again in the same task with its own inline styles as they were, when the window is idle, only with Home in front
and no card over it, never while it or a participant is open, once a window.

What is checked, in node on distil.js's own `startCase`, `esWarmSoon` and `esWarm` with every call they make
recorded: an open over another participant parks the card, the notes field and the note (`clearRows`), drawing no cell
again, and empties the rows before
the screen's tabs, its view and its passage are drawn, and a first open touches nothing; the warm-up stands the screen
shown, fixed and hidden from sight at its layout, ends with it hidden and its inline styles back (one it had kept),
runs once however often Home answers, never while the screen is shown or a participant is open, nor while Home is
not in front or a card is open over it, Home's next answer trying again then."""
from __future__ import annotations

import json
import re
import shutil

from . import support
from .support import check, skip


def whole(src: str, head: str) -> str:
    at = src.index(head)
    return src[at:src.index("\n}\n", at) + 3]


def line_of(js: str, start: str) -> str:
    at = js.index(start)
    return js[at:js.index("\n", at) + 1]


HARNESS = r"""
const log = [];
function el(id) {
  const props = {};
  const e = {
    id, hidden: true, textContent: '', title: '', classList: { toggle() {}, contains() { return false; }, add() {}, remove() {} },
    style: {
      setProperty(p, v, pri) { props[p] = [v, pri || '']; log.push(`style ${id} ${p}=${v}`); },
      getPropertyValue(p) { return props[p] ? props[p][0] : ''; },
      getPropertyPriority(p) { return props[p] ? props[p][1] : ''; },
      removeProperty(p) { delete props[p]; },
    },
    props,
    parentElement: null,
    prepend(x) { x.parentElement = e; log.push(`park ${x.id}`); },
    appendChild(x) { x.parentElement = e; log.push(`park ${x.id}`); },
    setAttribute() {},
  };
  Object.defineProperty(e, 'innerHTML', { set(v) { log.push(v ? `draw ${id}` : `empty ${id}`); } });
  Object.defineProperty(e, 'offsetWidth', { get() {
    log.push(`layout ${id} hidden=${e.hidden} position=${e.style.getPropertyValue('position')} visibility=${e.style.getPropertyValue('visibility')}`);
    return 100;
  } });
  return e;
}
const ELS = {};
const $ = (id) => (ELS[id] = ELS[id] || el(id));
const t = (k) => k;
const S = { data: null, flat: [], stops: [], at: 0 };
const timers = [];
const setTimeout = (fn, ms) => { timers.push([fn, ms]); return timers.length; };
const ES_TOOLS = {}, OPENING_LINE = '';
let CARD = null;
const cardTop = () => CARD;
"""

TAIL = r"""
const out = {};
const data = { path: '/p/b.xlsx', project: {}, config: {}, sheets: [{ rows: [] }], rounds: [], progress: { states: {} }, case: 'P1' };
// a first open: nothing put away, nothing emptied
startCase(data, {});
out.first = log.splice(0);
// an open over another participant
S.data = { path: '/p/a.xlsx' };
startCase(data, {});
out.again = log.splice(0);
// the warm-up: Home's answer twice, one timer
S.data = null;
$('library').hidden = false;
const work = $('work');
work.hidden = true;
work.style.setProperty('visibility', 'visible', 'important');
log.splice(0);
esWarmSoon(); esWarmSoon();
out.timers = timers.length;
out.after = timers[0] && timers[0][1];
timers[0][0]();
out.warm = log.splice(0);
out.hiddenAfter = work.hidden;
out.propsAfter = JSON.parse(JSON.stringify(work.props));
esWarmSoon();
out.timersAgain = timers.length;
// never while a participant is open or the screen shown
ES_WARM.done = false; S.data = { path: '/p/a.xlsx' }; esWarm();
out.withData = log.splice(0).filter((l) => l.startsWith('layout'));
ES_WARM.done = false; S.data = null; work.hidden = false; esWarm();
out.shown = log.splice(0).filter((l) => l.startsWith('layout'));
// nor while Home is not in front or a card stands over it, and Home's next answer tries again
work.hidden = true;
ES_WARM.done = false; $('library').hidden = true; esWarm();
out.homeHidden = log.splice(0).filter((l) => l.startsWith('layout'));
out.doneAfterHidden = ES_WARM.done;
$('library').hidden = false; CARD = { id: 'settings' }; esWarm();
out.carded = log.splice(0).filter((l) => l.startsWith('layout'));
CARD = null; $('home-project').hidden = false; esWarm();
out.projectPage = log.splice(0).filter((l) => l.startsWith('layout'));
out.doneAfterPage = ES_WARM.done;
$('home-project').hidden = true; esWarm();
out.retried = log.splice(0).filter((l) => l.startsWith('layout'));
console.log(JSON.stringify(out));
"""

BUILTINS = {"if", "for", "while", "return", "function", "typeof", "Array", "Number", "Math", "Object", "String",
            "Boolean", "JSON", "catch", "switch", "Set", "Map", "Promise", "isArray", "min", "max", "find", "findIndex",
            "push", "trim", "toLowerCase", "forEach", "assign", "keys", "entries", "includes", "join", "map", "filter",
            "setProperty", "getPropertyValue", "getPropertyPriority", "removeProperty", "replaceChildren",
            "$", "t", "setTimeout", "esWarm", "esWarmSoon", "startCase", "clearRows", "cardTop",
            "requestIdleCallback", "prepend", "appendChild"}


def test_statements_open_fast(scratch):
    print("\n447. The statements screen's open: the rows going emptied before anything is drawn, and the screen laid "
          "out once out of sight on Home")
    if not shutil.which("node"):
        skip("447: the statements screen's open, under node", "node is not on this machine")
        return
    js = support.text("apps/idiograph/static/distil.js")
    start = whole(js, "function startCase(")
    warm = whole(js, "function esWarmSoon(") + whole(js, "function esWarm(") + whole(js, "function clearRows(")
    # every other function the two call, each a recorder of its own name
    names = sorted({m for m in re.findall(r"(?<![.\w$])([A-Za-z_][\w$]*)\s*\(", start + warm)} - BUILTINS)
    stubs = "\n".join(f"function {n}(...a) {{ log.push('{n}'); return undefined; }}" for n in names)
    script = "\n".join([HARNESS, stubs, line_of(js, "const ES_WARM = "), line_of(js, "const ES_WARM_AFTER = "),
                        start, warm, TAIL])
    run = support.run_node(script, scratch, "a447.js")
    try:
        out = json.loads(run.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        check("447: the harness ran", False, (run.stderr or run.stdout)[:600])
        return
    first, again = out["first"], out["again"]
    check("447: a first open puts nothing away and empties nothing",
          not any(x in first for x in ("park es-card", "park en", "parkNote", "empty transcript-rows")), str(first[:12]))
    at = {name: (again.index(name) if name in again else -1)
          for name in ("park es-card", "park en", "parkNote", "empty transcript-rows", "dsTabsDraw", "drawView", "drawTurn")}
    check("447: an open over another participant parks the card, the notes field and the note, then empties the rows",
          0 <= at["park es-card"] < at["empty transcript-rows"] and 0 <= at["park en"] < at["empty transcript-rows"]
          and 0 <= at["parkNote"] < at["empty transcript-rows"], str(at))
    check("447: ... drawing no cell again from what is saved, the cells going with the rows",
          "parkCard" not in again and "parkNotes" not in again and "statementsHtml" not in again
          and "notesHtml" not in again, str(again[:10]))
    check("447: ... before the tabs, the view and the passage are drawn",
          0 <= at["empty transcript-rows"] < min(at["dsTabsDraw"], at["drawView"], at["drawTurn"]), str(at))
    check("447: Home answering twice sets one warm-up, a few seconds on", out["timers"] == 1 and out["after"] >= 1000,
          f"{out['timers']} timer, {out['after']} ms")
    layouts = [line for line in out["warm"] if line.startswith("layout")]
    check("447: the warm-up lays the screen out once, shown, fixed and hidden from sight",
          layouts == ["layout work hidden=false position=fixed visibility=hidden"], str(out["warm"]))
    check("447: ... and puts it away with its own inline styles as they were",
          out["hiddenAfter"] is True and out["propsAfter"] == {"visibility": ["visible", "important"]},
          str(out["propsAfter"]))
    check("447: a later answer from Home sets no second warm-up", out["timersAgain"] == 1, str(out["timersAgain"]))
    check("447: never while a participant is open or the screen shown", out["withData"] == [] and out["shown"] == [],
          str([out["withData"], out["shown"]]))
    check("447: never while Home is not in front, nor with a card open over it",
          out["homeHidden"] == [] and out["carded"] == [], str([out["homeHidden"], out["carded"]]))
    check("447: ... and Home's next answer tries again, once Home is in front with nothing over it",
          out["doneAfterHidden"] is False and len(out["retried"]) == 1, str([out["doneAfterHidden"], out["retried"]]))
    check("447: never while a project's page is in front, and Home's list coming back runs it once",
          out["projectPage"] == [] and out["doneAfterPage"] is False, str([out["projectPage"], out["doneAfterPage"]]))
