"""Area 337: the way back to the table from a record in Sift and Trace (sifttable, Adam, 8 November 2026, who chose
option C of the drawings). Since the project's name opens its menu the name was no way back, so a small link before it,
a left chevron and the table's name, Records in Sift and Claims in Trace, stands on a record alone and goes back to the
table as the name did, sfToTable and trToTable. What matters is that it shows only on a record, that a press on it goes
to the table and shuts the project's menu, that it is a button before the name in the page's order so the keyboard
reaches it, that its tooltip and name read Back to the table's name, and that the drawings' switch is gone. Its look
goes to Adam as review shots. Nothing here uses a participant's words."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from . import support
from .support import check, skip


def whole(src: str, head: str) -> str:
    at = src.index(head)
    return src[at:src.index("\n}\n", at) + 3]


def line_of(src: str, start: str) -> str:
    return next(ln for ln in src.splitlines() if ln.startswith(start))


def test_band_table_link(scratch: Path):
    print("\n337. The way back to the table from a record, a link before the project's name in Sift and Trace (sifttable)")
    js = support.text("family/static/shell.js")
    sift = support.text("apps/sift/static/sift.js")
    trace = support.text("apps/trace/static/trace.js")
    css = support.text("family/static/style.css")

    check("337: Sift's and Trace's names are wired to their own steps back to the table, drawn again on every view, and "
          "the drawings' switch and its other two ways are gone",
          "bandTableWire('sf-name', { word: 'Records', away: () => SF.view === 'record', go: () => sfToTable() });" in sift
          and "bandTableDraw('sf-name');" in sift
          and "bandTableWire('tr-name', { word: t('trace.band.table'), away: () => TR.view === 'record', go: () => trToTable() });" in trace
          and "bandTableDraw('tr-name');" in trace
          and "BAND_TABLE_WAY" not in js + css and "tableway" not in js + css and "ds-chev" not in js + css.replace("ds-chevron", "")
          and ".ds-path .ds-back" in css)

    node = shutil.which("node")
    if not node:
        skip("337: the link in node", "node is not installed")
        return
    pieces = [line_of(js, "const BAND_TABLE = "), whole(js, "function bandTableWire("), whole(js, "function bandTableDraw(")]
    harness = support.i18n_js() + r"""
const els = {};
const calls = [];
const mk = (id) => ({ id, hidden: false, attrs: {}, children: [], className: '', title: '', _kids: {},
  setAttribute(k, v) { this.attrs[k] = v; }, getAttribute(k) { return this.attrs[k]; },
  querySelector(q) { return this._kids[q] || (this._kids[q] = { textContent: '' }); } });
const nav = { children: [], insertBefore(node, ref) { this.children.splice(this.children.indexOf(ref), 0, node); } };
for (const id of ['sf-name', 'tr-name']) { const b = mk(id); b.parentNode = nav; els[id] = b; nav.children.push(b); }
const $ = (id) => els[id] || null;
const document = { createElement: () => mk('') };
const bandMenuShut = () => calls.push('shut');
""" + "\n".join(pieces) + r"""
const out = {};
for (const [id, table] of [['sf-name', 'Records'], ['tr-name', 'Claims']]) {
  let view = 'table';
  let went = 0;
  bandTableWire(id, { word: table, away: () => view === 'record', go: () => { went += 1; view = 'table'; } });
  const link = nav.children.find((c) => c.id === `${id}-back`);
  els[`${id}-back`] = link;
  const r = { before: link.hidden, ahead: nav.children.indexOf(link) < nav.children.indexOf(els[id]) };
  view = 'record'; bandTableDraw(id);
  r.onRecord = link.hidden; r.word = link._kids['.ds-back-word'].textContent; r.title = link.title; r.label = link.attrs['aria-label'];
  r.type = link.type; r.cls = link.className;
  link.onclick({ stopPropagation() {} });
  r.went = went; r.view = view; r.shut = calls.includes('shut');
  bandTableDraw(id); r.after = link.hidden;
  out[id] = r;
}
console.log(JSON.stringify(out));
"""
    harness_file = scratch / "link-337.js"
    harness_file.write_text(harness, encoding="utf-8")
    ran = subprocess.run([node, str(harness_file)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    got = json.loads(ran.stdout.strip().splitlines()[-1]) if ran.returncode == 0 and ran.stdout.strip() else {}
    for id_, table in (("sf-name", "Records"), ("tr-name", "Claims")):
        r = got.get(id_) or {}
        check(f"337: in node, {id_}'s link ({table}) is hidden on the table, shows on a record, stands before the name as a "
              "button, reads Back to the table's name in its tooltip and name, and a press goes to the table, shuts the "
              "project's menu and hides the link again",
              r.get("before") is True and r.get("onRecord") is False and r.get("ahead") is True and r.get("type") == "button"
              and r.get("word") == table and r.get("title") == f"Back to {table}" and r.get("label") == f"Back to {table}"
              and r.get("went") == 1 and r.get("view") == "table" and r.get("shut") is True and r.get("after") is True,
              json.dumps(r) + ran.stderr[:500])
