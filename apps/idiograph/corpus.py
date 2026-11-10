#!/usr/bin/env python3
"""The examples panel: three statements of the researcher's own, drawn at random on every turn.

Two pools, both named in `config.json`. `corpus` is a markdown file of statements, one `- ` line
each under a `## Source` heading, and `corpus_exclude` names any source to leave out of it, a
learner pass for one. `gravity_reference` is a finished workbook whose statement column is the
register anchor for this project, and the panel can be narrowed to it alone. With neither file on
the machine, a shared copy for one, both draw on the statements the demo case ships with. No
statement is written into this module.
"""
from __future__ import annotations

import random
import re
from pathlib import Path

HEADING = re.compile(r"^##\s+(.+?)\s*(?:\(\d+\))?\s*$")
ITEM = re.compile(r"^-\s+(.*\S)\s*$")

_cache: dict[str, list[dict]] = {}


def is_file(path) -> bool:
    """A configured path that names a file. An empty setting, or a folder, is no pool at all."""
    return bool(path) and Path(path).is_file()


def load_corpus(path: Path, exclude=()) -> list[dict]:
    """Statements from the corpus markdown, tagged with their source heading.

    A source whose heading contains any entry of `exclude` is left out.
    """
    skip = tuple(str(x) for x in exclude or () if str(x).strip())
    key = f"corpus:{path}:{'|'.join(skip)}"
    if key in _cache:
        return _cache[key]
    items: list[dict] = []
    source = ""
    if is_file(path):
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            h = HEADING.match(line)
            if h:
                source = h.group(1).strip()
                continue
            m = ITEM.match(line)
            if m and source and not any(x in source for x in skip):
                text = m.group(1).strip()
                if len(text) > 3:
                    items.append({"text": text, "source": source, "pool": "corpus"})
    _cache[key] = items
    return items


def load_gravity(path: Path) -> list[dict]:
    """The statement column of a finished workbook, every sheet of it."""
    key = f"gravity:{path}"
    if key in _cache:
        return _cache[key]
    items: list[dict] = []
    if is_file(path):
        try:
            import openpyxl
            from workbook import detect_columns, split_entries
            wb = openpyxl.load_workbook(path, read_only=False, data_only=True)
            label = Path(path).stem.replace(" - EN & ES", "")
            for ws in wb.worksheets:
                cols = detect_columns(ws)
                if "es" not in cols:
                    continue
                for r in range(2, ws.max_row + 1):
                    for text in split_entries(ws.cell(r, cols["es"]).value):
                        items.append({"text": text, "source": f"{label}, {ws.title}", "pool": "gravity"})
            wb.close()
        except Exception:
            items = []
    _cache[key] = items
    return items


def load_demo(path: Path) -> list[dict]:
    """The demo's own statements, the ones Juno's workbook ships with, for a machine with no pool."""
    return [dict(item, pool="demo") for item in load_gravity(path)]


def sample(corpus_path: Path, gravity_path: Path, n: int = 3, gravity_only: bool = False,
           exclude=(), demo_path: Path | None = None) -> list[dict]:
    """`n` statements from the pools, or from the demo's when the pools are empty, or none."""
    pool = load_gravity(gravity_path)
    if not gravity_only:
        pool = pool + load_corpus(corpus_path, exclude)
    if not pool and demo_path is not None:
        pool = load_demo(demo_path)
    if not pool:
        return []
    return random.sample(pool, min(n, len(pool)))


def counts(corpus_path: Path, gravity_path: Path, exclude=()) -> dict:
    return {"corpus": len(load_corpus(corpus_path, exclude)), "gravity": len(load_gravity(gravity_path))}
