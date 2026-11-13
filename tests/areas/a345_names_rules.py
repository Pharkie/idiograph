"""Area 345: names replaced as a transcript comes in (namesrule and namesui, 8 November 2026).

A project holds a list of real names and what each is written as. Every road a transcript comes in by applies it, and
nothing of the list is written anywhere in the project but its own file. Checked here: each rule's edge cases on
invented text, the store (since namesui one file in the project's folder, `idiograph-names.json`, mode 600, moving
with the folder, a list namesrule kept in the app's own folder moved there once), each road (Add transcripts with a
VTT, SRT, text, CSV, Word and Excel file, a REFI-QDA project, an import into a case), the preview and a skip, a Real
name typed on a row making its entry, the transcripts already in checked and then reviewed and replaced, the archive
keeping the original, the list and that archive left out of a shared copy, and the command line's and MCP server's
answers holding no real name. Every name here is invented, a keeper of hens and her neighbours."""
from __future__ import annotations

import base64
import io
import json
import os
import shutil
import stat
import zipfile
from pathlib import Path

import openpyxl

from . import support
from .a244_qdpx import at, code, package, selection
from .support import check
import idiograph_routes as routes

# every real name the fixtures hold, lower case, which must be found nowhere in the project after an Add
REAL = ["odette", "varnham", "gareth", "okafor", "piers", "lowther", "rosalind", "marlow", "jose", "tm. "]

VTT = ("WEBVTT\n\n00:00:01.000 --> 00:00:04.000\n<v Kit>How are the hens this spring?</v>\n\n"
       "00:00:05.000 --> 00:00:12.000\n<v Odette Varnham>Better since Gareth built the run. Gareth's shed is where "
       "they roost, and Dr  Okafor says the eggs are good for me. Annabel next door says the same, and her annual "
       "show is soon.</v>\n\n"
       "00:00:13.000 --> 00:00:16.000\n<v Kit>Does Rose help?</v>\n\n"
       "00:00:17.000 --> 00:00:23.000\n<v Odette Varnham>Rose, my sister, comes on Sundays. Will you come too, "
       "she asks. ODETTE, she says, you work too hard. I told Odette-Mae the same.</v>\n")
SRT = ("1\n00:00:02,000 --> 00:00:06,000\nKit: A week later, what changed?\n\n"
       "2\n00:00:07,000 --> 00:00:12,000\nPiers Lowther: Gareth and I split the feed bill, and T. M. kept the "
       "books. Rose from the pub came by.\n\n"
       "3\n00:00:13,000 --> 00:00:15,000\nKit: And José?\n\n"
       "4\n00:00:16,000 --> 00:00:21,000\nPiers Lowther: José sold us the cockerel. Piers, that is me, never "
       "thought it would crow.\n")
TXT = ("Kit: [00:00:03] Who else keeps birds?\nRosalind Marlow: [00:00:08] Gareth does, and the school. "
       "Rosalind is what everyone calls me.\n"
       "Kit: [00:00:40] Do you talk to them?\nRosalind Marlow: [00:00:44] Over the fence, mostly. Marlow is my "
       "married name, and the annual count is in May.\n")
CSV = ("Speaker,Start,Text\nKit,0:04,When do you go down?\nOdette Varnham,0:09,Before work. Gareth lets them "
       "out first.\nKit,0:15,Every day?\nOdette Varnham,0:19,Most days in summer.\n")

# the list, in the app's words: a name, its spellings, what it is written as, whom it is for, Match case
LIST = [
    {"real": ["Odette Varnham", "Odette"], "to": "Wren"},
    {"real": ["Piers Lowther", "Piers"], "to": "Ash", "for": "Ash"},
    {"real": ["Rosalind Marlow", "Rosalind", "Marlow"], "to": "Rook", "for": "Rook"},
    {"real": ["Gareth"], "to": "[partner]"},
    {"real": ["Dr Okafor"], "to": "[doctor]"},
    {"real": ["Will"], "to": "[friend]", "case": True},
    {"real": ["Rose"], "to": "[sister]", "for": "Wren"},
    {"real": ["T.M."], "to": "[treasurer]"},
    {"real": ["José"], "to": "[cousin]"},
    {"real": ["Ann"], "to": "[Ann]"},
]
WORDS_LEFT = ["Annabel", "annual", "Rose from the pub"]


def b64(data) -> str:
    return base64.b64encode(data if isinstance(data, bytes) else data.encode("utf-8")).decode("ascii")


def docx(lines) -> bytes:
    body = "".join(f'<w:p><w:r><w:t xml:space="preserve">{line}</w:t></w:r></w:p>' for line in lines)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types '
                   'xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr("word/document.xml", '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w='
                   '"http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' + body
                   + "<w:sectPr/></w:body></w:document>")
    return out.getvalue()


def xlsx(rows) -> bytes:
    wb = openpyxl.Workbook()
    for r in rows:
        wb.active.append(r)
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def leaks(folder: Path, words, skip_under=()) -> list:
    """(namesui) The list's own file is the one place the names stand, so it is passed over here."""
    import names as names_mod
    skip_under = tuple(skip_under) + (names_mod.FILE,)
    """Every file under `folder`, and every member of an archive among them (a workbook, a Word file, a sent copy),
    that holds one of the words, any case."""
    found = []

    def holds(blob: bytes) -> list:
        low = blob.decode("utf-8", errors="replace").lower()
        return [w for w in words if w in low]

    for p in sorted(Path(folder).rglob("*")):
        if not p.is_file() or any(part in skip_under for part in p.relative_to(folder).parts):
            continue
        data = p.read_bytes()
        for w in holds(data):
            found.append((p.relative_to(folder).as_posix(), w))
        if zipfile.is_zipfile(p):
            with zipfile.ZipFile(p) as z:
                for m in z.namelist():
                    for w in holds(m.encode("utf-8") + z.read(m)):
                        found.append((p.relative_to(folder).as_posix() + "!" + m, w))
    return found


def test_names_rules(scratch):
    print("\n345. Names replaced as a transcript comes in: each rule, the store outside the project, each road a "
          "transcript comes in by, the preview and a skip, the transcripts already in, and the agents told counts only "
          "(8 November)")
    import cli
    import mcp_server
    import names as names_mod
    import server as server_mod
    import workbook as wb_mod

    # ── A. the rules, on invented text
    def put(text, entries, who=None):
        return names_mod.plain(text, [names_mod.clean_entry(e) for e in entries], who)

    ann = [{"real": ["Ann"], "to": "[A]"}]
    check("345: a name is found as a whole word by Unicode letters, never inside a longer one",
          put("Ann, Annabel and annual, Ann's hen, ann.", ann) == "[A], Annabel and annual, [A]'s hen, [A]."
          and put("Zoë and Zoëlle", [{"real": ["Zoë"], "to": "Z"}]) == "Z and Zoëlle"
          and put("José, Joséphine", [{"real": ["José"], "to": "J"}]) == "J, Joséphine"
          and put("Ann2 and 2Ann and Ann_x", ann) == "Ann2 and 2Ann and [A]_x", put("Ann2 and 2Ann and Ann_x", ann))
    check("345: case is ignored and the list's spelling is written, unless the entry is ticked Match case",
          put("TILDA tilda Tilda", [{"real": ["Tilda"], "to": "Wren"}]) == "Wren Wren Wren"
          and put("Will you? will you? WILL", [{"real": ["Will"], "to": "[W]", "case": True}]) == "[W] you? will you? WILL")
    check("345: an apostrophe, a hyphen or a full stop ends a word, so a possessive keeps its ending",
          put("Tilda's hen, Tilda-Mae, Tilda.", [{"real": ["Tilda"], "to": "Wren"}]) == "Wren's hen, Wren-Mae, Wren."
          and put("Tilda-Mae and Tilda", [{"real": ["Tilda-Mae", "Tilda"], "to": "Wren"}]) == "Wren and Wren")
    check("345: a run of spaces or a line break inside a name matches",
          put("Dr  Okafor, Dr\nOkafor, Dr \t Okafor", [{"real": ["Dr Okafor"], "to": "[D]"}]) == "[D], [D], [D]")
    ini = [{"real": ["T.M."], "to": "[T]"}]
    check("345: initials match with or without dots and the space between, always by case",
          put("T.M. said, T. M. said, TM said, T.M said, tm said, T.M.", ini) == "[T] said, [T] said, [T] said, [T] said, tm said, [T]"
          and put("Item, ATM, T.M.s", ini) == "Item, ATM, [T].s")
    check("345: the longest name goes first, in one pass, so no replacement is replaced again",
          put("Tilda Marsh and Tilda", [{"real": ["Tilda"], "to": "Wren"}, {"real": ["Tilda Marsh"], "to": "Ash"}])
          == "Ash and Wren"
          and put("A and B", [{"real": ["A"], "to": "B"}, {"real": ["B"], "to": "C"}]) == "B and C")
    check("345: several spellings an entry, a misspelling not guessed",
          put("Tilda Marsh, Tilda, Tills, Tilly", [{"real": ["Tilda Marsh", "Tilda", "Tills"], "to": "Wren"}])
          == "Wren, Wren, Wren, Tilly")
    check("345: a name with a dot or a bracket in it is matched as written, never as a pattern",
          put("a.b and axb, [x] and x", [{"real": ["a.b"], "to": "1"}, {"real": ["[x]"], "to": "2"}]) == "1 and axb, 2 and x")
    entries = [names_mod.clean_entry(e) for e in [{"real": ["Ruth"], "to": "[sister]", "for": "Wren"},
                                                  {"real": ["Ruth"], "to": "[friend]", "for": "Ash"},
                                                  {"real": ["Kit"], "to": "[I]"}]]
    check("345: an entry for one participant applies to that participant's transcripts alone, one for everyone to all",
          names_mod.plain("Ruth and Kit", entries, "Wren") == "[sister] and [I]"
          and names_mod.plain("Ruth and Kit", entries, "Ash") == "[friend] and [I]"
          and names_mod.plain("Ruth and Kit", entries, None) == "Ruth and [I]")
    run = names_mod.Run(entries, names_mod.read_skip("1:2, 3:1"))
    out = run.text("Ruth, Ruth, Ruth, Kit, Kit", "Wren", {"participant": "Wren"})
    check("345: a skip leaves one find as written, an entry's number and its place among that entry's finds",
          out == "[sister], Ruth, [sister], Kit, [I]" and run.replaced() == 3
          and [f["skipped"] for f in run.finds] == [False, True, False, True, False], out)
    check("345: a skip is read from strings, pairs and objects, and refused in one line when it is none of them",
          names_mod.read_skip(["3:1", [4, 2], {"entry": 5, "nth": 1}]) == {(3, 1), (4, 2), (5, 1)}
          and all(_refused(lambda v=v: names_mod.read_skip(v)) for v in ("x", "0:1", "3", [1, 0])))
    counts = run.counts()
    check("345: the counts say how many were replaced and left, by entry and place, with no name in them",
          counts["replaced"] == 3 and counts["left"] == 2 and "Ruth" not in json.dumps(counts)
          and "Kit" not in json.dumps(counts) and counts["by_entry"][0]["to"] == "[sister]"
          and names_mod.lines(counts)[0].startswith("entry 1, [sister]:"), json.dumps(counts)[:300])
    check("345: an entry needs a name and what to write, and spellings may be given as one line with commas",
          _refused(lambda: names_mod.clean_entry({"real": [], "to": "x"}))
          and _refused(lambda: names_mod.clean_entry({"real": ["x"], "to": ""}))
          and names_mod.clean_entry({"real": "A, B ,a", "to": "x", "for": "everyone"}) == {"real": ["A", "B"], "to": "x", "for": None, "case": False})
    key_csv = "Real name,Pseudonym\n\"Odette Varnham, Odette\",Wren\nGareth,[partner]\n,orphan\n"
    key_xlsx = xlsx([["Real", "Replace with"], ["Gareth", "[partner]"], ["Piers Lowther", "Ash"]])
    read_csv, read_xlsx = names_mod.read_key("key.csv", key_csv.encode()), names_mod.read_key("key.xlsx", key_xlsx)
    check("345: Add from a file reads a two-column CSV or Excel key, a heading row passed over, and Save as a file writes one",
          [e["real"] for e in read_csv] == [["Odette Varnham", "Odette"], ["Gareth"]] and read_csv[0]["to"] == "Wren"
          and [e["to"] for e in read_xlsx] == ["[partner]", "Ash"]
          and names_mod.write_key(read_csv).splitlines()[1] == '"Odette Varnham, Odette",Wren')

    # ── B. a project, its list kept outside it
    store = scratch / "names-345-store"
    base = scratch / "names-345"
    for folder in (store, base):
        shutil.rmtree(folder, ignore_errors=True)
    inputs = base / "inputs"
    inputs.mkdir(parents=True)
    folder = base / "Hens"
    folder.mkdir()
    cfg = base / "config.json"
    cfg.write_text(json.dumps({"projects": [], "interviewer": "Researcher"}), encoding="utf-8")
    kept = (server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY,
            names_mod.OVERRIDE)
    try:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE = cfg, None
        server_mod.STATE_PATH, server_mod.STATE_MEMORY = base / "state.json", {"recent": []}
        names_mod.OVERRIDE = store
        (folder / server_mod.PROJECT_FILE).write_text(json.dumps(
            {"name": "Keeping hens", "agents": {"allowed": True, "at": "2026-11-08T10:00:00+00:00"}}), encoding="utf-8")
        routes.add_project(folder)
        rid = routes.project_id(folder)
        first = routes.api_add_transcripts({"op": "add", "root": rid, "files": [
            {"name": "early.txt", "data": b64("Kit: [00:00:02] Tell me about the coop.\nMoss: [00:00:05] Gareth built it "
                                               "and Rose painted it.\n"), "pseudonym": "Moss", "interview": "Early",
             "speakers": {"Kit": "interviewer", "Moss": "participant"}}]})
        early_book = folder / "P1 - Moss" / "P1 Moss - EN & ES.xlsx"
        check("345: a project with no list adds a transcript as it always did",
              first["cases"] == ["P1 - Moss"] and "names" not in first and early_book.exists()
              and "Gareth" in json.dumps(routes.api_open({"path": str(early_book)})["sheets"][0]["rows"]))
        stored = folder / names_mod.FILE
        check("345: no list is made, and none is kept, until the app sets one",
              not store.exists() and not stored.exists() and not routes.pseudo_list(folder)
              and routes.api_names({"op": "list", "root": rid}) == {"entries": [], "count": 0, "participants": ["Moss"]})

        listed = routes.api_names({"op": "set", "root": rid, "entries": LIST})
        project_json = json.loads((folder / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
        mode = stat.S_IMODE(stored.stat().st_mode) if stored.exists() else 0
        check("345: Set keeps the list in one file in the project's folder, idiograph-names.json, mode 600, and nothing "
              "in the app's own folder or the project file",
              listed["count"] == len(LIST) and stored.is_file() and (mode == 0o600 or os.name == "nt") and not store.exists()
              and routes.pseudo_list(folder) == names_mod.clean_entries(LIST) and "names_key" not in project_json
              and json.dumps(project_json).lower().count("odette") == 0, oct(mode))
        check("345: the list is in no other file of the project's folder, nor any archive",
              not leaks(folder, REAL[:5], skip_under=("P1 - Moss",)), str(leaks(folder, REAL[:5])[:4]))
        moved = base / "Hens moved"
        shutil.copytree(folder, moved)
        check("345: a moved project keeps its list, since the list's file moves with its folder",
              routes.pseudo_list(moved) == routes.pseudo_list(folder) and (moved / names_mod.FILE).is_file())
        shutil.rmtree(moved)

        # a list namesrule kept in the app's own folder, by a key in the project file, is moved into the folder once
        older = base / "Older"
        older.mkdir()
        old_key = "0123456789abcdef0123456789abcdef"
        (older / server_mod.PROJECT_FILE).write_text(json.dumps({"name": "Older hens", "names_key": old_key}), encoding="utf-8")
        store.mkdir(parents=True)
        (store / f"{old_key}.json").write_text(json.dumps({"entries": LIST[:2]}), encoding="utf-8")
        moved_list = routes.pseudo_list(older)
        older_json = json.loads((older / server_mod.PROJECT_FILE).read_text(encoding="utf-8"))
        check("345: a list from before is moved into the project's folder the first time it is read, the old file and the "
              "key gone, and read from there after",
              moved_list == names_mod.clean_entries(LIST[:2]) and (older / names_mod.FILE).is_file()
              and not (store / f"{old_key}.json").exists() and "names_key" not in older_json
              and older_json["name"] == "Older hens" and routes.pseudo_list(older) == moved_list)
        shutil.rmtree(older)
        shutil.rmtree(store)
        check("345: a list is refused with no name or no replacement, and an agent cannot set one",
              _refused(lambda: routes.api_names({"op": "set", "root": rid, "entries": [{"real": [], "to": "x"}]}))
              and _refused(lambda: routes.api_names({"op": "set", "root": rid, "entries": LIST, "tool": "Claude Code"}))
              and _refused(lambda: routes.api_names({"op": "read-key", "root": rid, "tool": "Claude Code", "name": "k.csv",
                                                     "data": b64(key_csv)}))
              and routes.pseudo_list(folder) == names_mod.clean_entries(LIST))
        csv_back = routes.api_names({"op": "key-file", "root": rid})["csv"]
        read_back = routes.api_names({"op": "read-key", "root": rid, "name": "key.csv", "data": b64(key_csv)})
        check("345: the app can write the list as a key file and read a key file, the real names for the app alone",
              "Odette Varnham" in csv_back and [e["to"] for e in read_back["entries"]] == ["Wren", "[partner]"])

        # ── C. each road in: Add transcripts, a file of each kind, the real names in the file's name too
        files = [
            ("Odette Varnham hens.vtt", VTT.encode(), "Wren", {"Kit": "interviewer", "Odette Varnham": "participant"}),
            ("Piers Lowther sheep.srt", SRT.encode(), "Ash", {"Kit": "interviewer", "Piers Lowther": "participant"}),
            ("Rosalind Marlow bees.txt", TXT.encode(), "Rook", {"Kit": "interviewer", "Rosalind Marlow": "participant"}),
            ("ducks.csv", CSV.encode(), "Oak", {"Kit": "interviewer", "Odette Varnham": "participant"}),
            ("goats.docx", docx(["Kit: How is the herd?", "Odette Varnham: Gareth milks at six. Dr Okafor visits."]),
             "Pip", {"Kit": "interviewer", "Odette Varnham": "participant"}),
            ("geese.xlsx", xlsx([["Speaker", "Start", "Text"], ["Kit", "0:03", "Any trouble?"],
                                ["Odette Varnham", "0:08", "Gareth chased them, and José laughed."]]),
             "Reed", {"Kit": "interviewer", "Odette Varnham": "participant"}),
        ]

        def rows_for(items, interviews=None):
            return [{"name": n, "data": b64(d), "pseudonym": who, "interview": (interviews or {}).get(n, n.rsplit(".", 1)[0]),
                     "speakers": roles} for n, d, who, roles in items]

        dry = routes.api_add_transcripts({"op": "add", "root": rid, "dry_run": True, "names_preview": True,
                                          "files": rows_for(files)})
        before = sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*"))
        finds = dry["names"]["finds"]
        seen = {(f["entry"], f["found"]) for f in finds}
        check("345: the dry run writes nothing and the preview lists each find with the words found, where and which entry",
              dry["dry_run"] is True and sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*")) == before
              and finds and (4, "Gareth") in seen and (5, "Dr Okafor") in seen and (8, "T. M.") in seen
              and (2, "José") not in seen and (9, "José") in seen
              and all({"entry", "nth", "found", "to", "skipped", "where"} <= set(f) for f in finds)
              and {"participant", "part"} <= set(finds[0]["where"]) and "interview" in finds[-1]["where"], str(sorted(seen))[:500])
        # the one counted across every file, in order, which is how a skip names it
        garethed = [f for f in finds if f["entry"] == 4]
        check("345: an entry's finds are numbered across the files in the order they come, 1 to n",
              [f["nth"] for f in garethed] == list(range(1, len(garethed) + 1)) and len(garethed) >= 6)
        check("345: the answer's counts say each entry's replaced and left, and the names are the app's alone",
              dry["names"]["replaced"] == len(finds) and dry["names"]["left"] == 0
              and all(set(e) >= {"entry", "to", "replaced", "left", "in", "parts"} for e in dry["names"]["by_entry"])
              and "Gareth" not in json.dumps({k: v for k, v in dry["names"].items() if k != "finds"}))

        # the interview's name and the file's name go through the list too
        done = routes.api_add_transcripts({"op": "add", "root": rid, "files": rows_for(
            files, {"Odette Varnham hens.vtt": "Odette hens", "Piers Lowther sheep.srt": "Piers sheep"})})
        wren_book = folder / "P2 - Wren" / "P2 Wren - EN & ES.xlsx"
        raw_book = folder / "P2 - Wren" / "Source" / "P2 Wren - transcript.xlsx"
        shown = routes.api_open({"path": str(wren_book)})["sheets"][0]
        text_of = " ".join(r["text"] for r in shown["rows"])
        speakers = {r["name"] for r in shown["rows"]}
        check("345: a transcript added has its names replaced in its words and its speakers' names, a whole word only",
              done["added"] is True and done["names"]["left"] == 0 and done["names"]["replaced"] == len(finds)
              and "Better since [partner] built the run" in text_of and "[partner]'s shed" in text_of
              and "[doctor] says" in text_of and "Annabel" in text_of and "annual" in text_of
              and "Wren-Mae" in text_of and "[sister], my sister" in text_of and "[friend] you come" in text_of
              and "Wren, she says" in text_of and speakers == {"Wren", "Researcher"}, text_of[:400] + str(speakers))
        check("345: the interview's name goes through the list, and the sheet is named for what it became",
              shown["name"] == "Wren hens" if "name" in shown else "Wren hens" in json.dumps(shown)[:300])
        check("345: in Ash's transcript Rose, whose entry is for Wren alone, stays, and José, initials and a Match case name follow the list",
              (lambda t: "Rose from the pub" in t and "[treasurer] kept" in t and "[cousin] sold" in t
               and "Ash, that is me" in t and "Gareth" not in t)(
                  " ".join(r["text"] for r in routes.api_open({"path": str(folder / "P3 - Ash" / "P3 Ash - EN & ES.xlsx")})
                           ["sheets"][0]["rows"])))
        for n, label in ((4, "Rook"), (5, "Oak"), (6, "Pip"), (7, "Reed")):
            book = folder / f"P{n} - {label}" / f"P{n} {label} - EN & ES.xlsx"
            t = " ".join(r["text"] for r in routes.api_open({"path": str(book)})["sheets"][0]["rows"])
            check(f"345: a {['text', 'CSV', 'Word', 'Excel'][n - 4]} file's names are replaced as well",
                  "Gareth" not in t and ("[partner]" in t) and "Odette" not in t and "Marlow" not in t, t[:200])
        # the early one is untouched, the transcript already in, which the list does not reach back for
        mine = leaks(folder, REAL, skip_under=("P1 - Moss", "_Archive"))
        check("345: no listed name is in any file of the new participants, any workbook, Source copy, progress file or the "
              "project file, however deep in an archive", not mine, str(mine[:6]))
        copy = folder / "P2 - Wren" / "Source" / "Wren hens" / "P2-Wren hens.txt"
        check("345: Source's copy is the replaced text, in the name already made for it, the original not kept",
              copy.is_file() and "Gareth" not in copy.read_text(encoding="utf-8") and "Dr  Okafor" not in copy.read_text(encoding="utf-8")
              and "[doctor]" in copy.read_text(encoding="utf-8")
              and not list((folder / "P2 - Wren").rglob("*.vtt")) and raw_book.exists())
        check("345: the descriptions and History of a workbook made from a file named for a person carry the replaced name",
              "Odette" not in (openpyxl.load_workbook(wren_book, read_only=True).properties.description or ""))

        # ── D. the transcripts already in, checked with counts only
        before_tree = {p.relative_to(folder).as_posix(): p.read_bytes() for p in folder.rglob("*") if p.is_file()}
        checked = routes.api_names({"op": "check", "root": rid, "tool": "Claude Code"})
        found = {e["entry"]: e for e in checked["names"]["by_entry"]}
        check("345: Check finds the names in the transcripts already in, counts only, and writes nothing",
              checked["names"]["replaced"] == 1 and found.get(4, {}).get("replaced") == 1
              and found[4]["in"][0]["participant"] == "Moss"
              and "Gareth" not in json.dumps(checked) and "Rose" not in json.dumps(checked)
              and {p.relative_to(folder).as_posix(): p.read_bytes() for p in folder.rglob("*") if p.is_file()} == before_tree,
              json.dumps(checked)[:400])

        # ── E. a REFI-QDA project: code names, groups, comments, memos, the package not copied
        t = ("Kit: What happened in March?\nOdette Varnham: Gareth's fox got in, and Dr Okafor had to calm me down. "
             "Annabel brought flour.\nKit: And now?\nOdette Varnham: Dr Okafor says the run is safe.\n")
        sels = (selection("q1", at(t, "Gareth's fox got in"), ["k1"], comment="Odette Varnham on the fox")
                + selection("q2", at(t, "Dr Okafor says the run is safe"), ["k2"], notes=["n1"]))
        codes = code("k1", "Gareth's fox") + code("k2", "Safe with Dr Okafor")
        sets = '<Sets><Set guid="s1" name="Odette\'s year"><MemberCode targetGUID="k1"/><MemberCode targetGUID="k2"/></Set></Sets>'
        notes = '<Note guid="n1" name="Odette Varnham memo"><PlainTextContent>Odette Varnham was calm about Gareth.</PlainTextContent></Note>'
        src = (f'<TextSource guid="t1" name="Odette Varnham interview" plainTextPath="internal://t1.txt">{sels}'
               f'<NoteRef targetGUID="n1"/></TextSource>')
        pkg_bytes = package("ATLAS.ti 23.2", codes, src, {"Sources/t1.txt": t.encode("utf-8")}, extra=sets, notes=notes)
        (inputs / "fox.qdpx").write_bytes(pkg_bytes)
        asked = {"sources": [{"source": 1, "pseudonym": "Lark"}], "pets": True, "names_preview": True}
        preview = routes.qdpx_import(folder, inputs / "fox.qdpx", dict(asked))
        view = json.dumps({k: v for k, v in preview.items() if k != "names"})
        check("345: a REFI-QDA dry run shows the source, its speakers, code groups and first passages with the names replaced",
              preview["said"] is None and "Odette" not in view and "Gareth" not in view and "Okafor" not in view
              and "[partner]'s fox" in view and preview["names"]["replaced"] >= 6, view[:500])
        routes.qdpx_import(folder, inputs / "fox.qdpx", dict(asked), make=True)
        lark = folder / "P8 - Lark"
        qdpx_hits = leaks(lark, REAL)
        lark_rows = routes.api_open({"path": str(lark / "P8 Lark - EN & ES.xlsx")})["sheets"][0]["rows"]
        memo = next((p for p in (lark / "Source").glob("*memos*.txt")), None)
        check("345: a REFI-QDA import writes no listed name: not in the workbooks, the notes, the statements, the quotes, "
              "the memos or the board, and the package is not copied into Source",
              not qdpx_hits and memo is not None and "Gareth" not in memo.read_text(encoding="utf-8")
              and not list(lark.rglob("*.qdpx")) and any("[partner]'s fox" in (r["text"] or "") for r in lark_rows)
              and any("[partner]'s fox" in (r.get("es") or "") for r in lark_rows), str(qdpx_hits[:6]))
        check("345: the REFI-QDA import keeps its copy as the replaced text, .txt, in Source",
              any(p.suffix == ".txt" and "P8-" in p.name for p in (lark / "Source").rglob("*.txt"))
              and not any("Gareth" in p.read_text(encoding="utf-8") for p in (lark / "Source").rglob("P8-*.txt")))

        # ── F. an import into a case, the card's make
        extra = folder / "P2 - Wren" / "Extra.vtt"
        extra.write_text(VTT, encoding="utf-8")
        routes.api_import({"op": "make", "path": str(extra), "speakers": {"Kit": "Interviewer", "Odette Varnham": "Participant"}})
        made_raw = folder / "P2 - Wren" / "Extra.xlsx"
        wb = openpyxl.load_workbook(made_raw)
        dump = " ".join(str(c.value) for ws in wb.worksheets for row in ws.iter_rows() for c in row if c.value is not None)
        wb.close()
        check("345: an import into a case applies the list to the raw source it makes",
              made_raw.exists() and "Gareth" not in dump and "Odette" not in dump and "[partner]" in dump and "Wren" in dump, dump[:200])
        extra.unlink()
        made_raw.unlink()

        # ── G. a shared copy, History, the progress files and the agent log carry nothing of the list
        sent = base / "Hens.idiograph"
        routes.api_send_project({"root": rid, "to": str(sent)})
        sent_hits = []
        with zipfile.ZipFile(sent) as z:
            sent_names = z.namelist()
            for m in sent_names:
                body = z.read(m)
                if "P1 - Moss" in m or m.endswith(".xlsx") or "_Archive" in m:
                    continue
                if any(w in body.decode("utf-8", errors="replace").lower() for w in REAL[:5]):
                    sent_hits.append(m)
        check("345: a shared copy holds no list, and no file of it names one",
              not any(names_mod.FILE in m for m in sent_names) and not sent_hits, str(sent_hits[:4]))
        check("345: nothing of the list is in the project's History, its progress files or the settings files",
              not [h for h in leaks(folder, ["varnham", "lowther", "marlow"])]
              and "varnham" not in cfg.read_text(encoding="utf-8").lower()
              and "varnham" not in (base / "state.json").read_text(encoding="utf-8").lower()
              if (base / "state.json").exists() else True)

        # ── H. the agents: the command line and the MCP server, counts only
        config = base / "agent-config.json"
        config.write_text(json.dumps({"root": str(folder), "interviewer": "Researcher"}), encoding="utf-8")

        def run(*argv):
            code_, out, err = cli.run(["--root", str(folder), "--config", str(config), "--json", *argv])
            return code_, (support.plain(json.loads(out)) if out.strip() and code_ == 0 else out), err

        spec = base / "spec.json"
        agent_file = inputs / "birds.vtt"
        agent_file.write_text(VTT, encoding="utf-8")
        spec.write_text(json.dumps([{"file": str(agent_file), "pseudonym": "Quill", "interview": "Birds",
                                     "speakers": {"Kit": "Interviewer", "Odette Varnham": "Participant"}}]), encoding="utf-8")
        code_, listed_a, err = run("names", "list")
        check("345: names list tells an agent each entry by number, replacement and whom it is for, never a real name",
              code_ == 0 and listed_a["count"] == len(LIST) and listed_a["entries"][0] == {
                  "entry": 1, "to": "Wren", "for": None, "spellings": 2, "case": False}
              and not any(w in json.dumps(listed_a).lower() for w in REAL[:5]), err or json.dumps(listed_a)[:300])
        code_, dry_a, err = run("project", "add-transcripts", "--from", str(spec), "--dry-run")
        every = json.dumps(dry_a).lower() + err.lower()
        check("345: an agent's dry run Add says how many names would be replaced, by entry and place, and no real name",
              code_ == 0 and dry_a["names"]["replaced"] >= 6 and "finds" not in dry_a["names"]
              and not any(w in every for w in REAL[:5]), str([w for w in REAL[:5] if w in every]) + (err or every[:600]))
        code_, done_a, err = run("project", "add-transcripts", "--from", str(spec), "--skip", "4:1", "--note", "Add Quill's birds",
                                 "--tool", "Claude Code")
        quill_book = folder / "P9 - Quill" / "P9 Quill - EN & ES.xlsx"
        birds = routes.api_open({"path": str(quill_book)})["sheets"] if code_ == 0 else []
        birds_text = " ".join(r["text"] for s in birds for r in s["rows"]) if code_ == 0 else ""
        check("345: an agent's Add applies the list by default, a skip leaving one find, and the answer holds no real name",
              code_ == 0 and done_a["names"]["left"] == 1 and "Better since Gareth built" in birds_text
              and "[partner]'s shed" in birds_text and not any(w in json.dumps(done_a).lower() for w in REAL[:5]),
              err or birds_text[:200] + json.dumps(done_a)[:200])
        code_, bad_skip, err = run("project", "add-transcripts", "--from", str(spec), "--skip", "nonsense", "--dry-run")
        check("345: a skip that is no skip is refused in one line", code_ != 0 and "3:1" in (err + str(bad_skip)))
        code_, check_a, err = run("names", "check")
        check("345: names check gives an agent counts only, and the project's files are as they were",
              code_ == 0 and found.get(4) is not None and check_a["names"]["replaced"] >= 2
              and not any(w in json.dumps(check_a).lower() for w in REAL[:5]), err or json.dumps(check_a)[:300])
        code_, plain_a, err = cli.run(["--root", str(folder), "--config", str(config), "names", "list"])
        check("345: the command line's plain words hold no real name either",
              code_ == 0 and "entry 1, Wren" in plain_a and not any(w in plain_a.lower() for w in REAL[:5]), plain_a[:300])
        code_, no_set, err = cli.run(["--root", str(folder), "--config", str(config), "names", "set"])
        check("345: the command line has no way to add a name", code_ != 0)

        srv = mcp_server.Server(str(folder), config=str(config))
        srv.receive(json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))

        def call(name, args, n):
            return srv.receive(json.dumps({"jsonrpc": "2.0", "id": n, "method": "tools/call",
                                           "params": {"name": name, "arguments": args}}))["result"]

        tools = {t["name"]: t for t in srv.receive(json.dumps({"jsonrpc": "2.0", "id": 9, "method": "tools/list"}))["result"]["tools"]}
        check("345: the MCP server lists names_list, names_check, names_replace and names_remove, and no tool that adds a name",
              {"names_list", "names_check", "names_replace", "names_remove"} <= set(tools)
              and not any(n.startswith("names_") and n not in ("names_list", "names_check", "names_replace", "names_remove")
                          for n in tools)
              and tools["names_list"]["annotations"]["readOnlyHint"] is True
              and tools["names_remove"]["annotations"]["readOnlyHint"] is False
              and "skip" in tools["project_add_transcripts"]["inputSchema"]["properties"]
              and "skip" in tools["import_qdpx"]["inputSchema"]["properties"])
        got_list, got_check = call("names_list", {}, 1), call("names_check", {}, 2)
        got_dry = call("project_add_transcripts", {"files": [{"file": str(agent_file), "pseudonym": "Quill", "interview": "Birds 2",
                                                                "speakers": {"Kit": "Interviewer", "Odette Varnham": "Participant"}}],
                                                   "dry_run": True, "request": "x"}, 3)
        every = json.dumps([got_list, got_check, got_dry]).lower()
        check("345: the MCP server's answers hold counts and numbers and no real name",
              not got_list.get("isError") and not got_check.get("isError") and not got_dry.get("isError")
              and not any(w in every for w in REAL[:5]) and got_check["structuredContent"]["names"]["replaced"] >= 2
              and got_dry["structuredContent"]["names"]["replaced"] >= 6, every[:400])
        gone = call("names_remove", {"entries": [10], "request": "Drop the Ann entry", "dry_run": True}, 4)
        removed = call("names_remove", {"entries": [10], "request": "Drop the Ann entry"}, 5)
        check("345: an agent may take an entry off the list by its number, its dry run first, and sees no name",
              gone["structuredContent"]["removed"] == 1 and len(routes.pseudo_list(folder)) == len(LIST) - 1
              and removed["structuredContent"]["count"] == len(LIST) - 1
              and not any(w in json.dumps(removed).lower() for w in REAL[:5]))

        # the whole project once more, the agents' Adds included, and the agent log beside the settings
        # the copies kept before a write, an _Archive's and since noholds (13 November 2026) an agent run's restore
        # point's, hold the transcript as it was, as an archive does
        final = leaks(folder, REAL, skip_under=("P1 - Moss", "P9 - Quill", "_Archive", ".idiograph-restore"))
        log_text = " ".join(p.read_text(encoding="utf-8", errors="replace") for p in base.glob("*agent-log*.json")).lower()
        check("345: after every road and every agent call no listed name is in the project, and none in the agent log",
              not final and not any(w in log_text for w in REAL[:5]), str(final[:6]))
        check("345: the list itself is the one place the names stand",
              all(w in stored.read_text(encoding="utf-8") for w in ("Odette Varnham", "Gareth")))

        namesui_checks(base, folder, rid, routes, names_mod, server_mod, cli, mcp_server, config)
    finally:
        server_mod.CONFIG_PATH, server_mod.ROOT_OVERRIDE, server_mod.STATE_PATH, server_mod.STATE_MEMORY, names_mod.OVERRIDE = kept


def _refused(fn) -> bool:
    try:
        fn()
    except Exception as exc:
        return bool(str(exc).strip())
    return False


def namesui_checks(base, folder, rid, routes, names_mod, server_mod, cli, mcp_server, config):
    """namesui (Adam, 8 November 2026 about 22:50): a Real name on a row makes its entry, the card's preview numbers
    each find as the Add will, so a find unticked there is the one the Add leaves, and the transcripts already in are
    checked, then reviewed and replaced, each workbook as it was kept in its participant's _Archive, which a shared
    copy leaves out with the list."""
    kites = ("Kit: [00:00:01] Tell me about the kites.\nMirabel Thorne: [00:00:04] Mirabel flies them with Gareth "
             "on the moor, and Gareth mends the lines.\n")
    files = [{"name": "kites.txt", "data": b64(kites), "pseudonym": "Finch", "interview": "Kites", "real": "Mirabel Thorne",
              "speakers": {"Kit": "interviewer", "Mirabel Thorne": "participant"}}]
    before = len(routes.pseudo_list(folder))

    # ── I. the card's preview, and a Real name typed on a row
    shown = routes.api_names({"op": "preview", "root": rid, "files": files})
    finds = shown["files"][0]["finds"]
    garethed = [f for f in finds if f["found"] == "Gareth"]
    made = [f for f in finds if f["to"] == "Finch"]
    segs = [s for t in shown["files"][0]["turns"] for s in t["text"] if isinstance(s, dict)]
    check("345: the card's preview runs a row through the list with its Real name's entry, the speaker and the words "
          "found, each with the words either side, and its passages as segments to tint",
          shown["entries"] == before + 1 and shown["list"][-1]["real"] == ["Mirabel Thorne", "Mirabel"]
          and shown["list"][-1]["for"] == "Finch" and len(garethed) == 2 and len(made) >= 2
          and any(f["where"]["part"] == "speaker" and f["speaks"] == 1 for f in made)
          and garethed[0]["before"].endswith("flies them with ") and {"to": "Finch", "was": "Mirabel", "kept": False} in segs
          and shown["files"][0]["speakers"][1]["segments"][0]["to"] == "Finch", json.dumps(shown)[:600])
    check("345: the preview writes nothing, and the list stays as it was until the Add",
          len(routes.pseudo_list(folder)) == before and not (folder / "P10 - Finch").exists())
    check("345: an agent cannot preview, nor give a Real name",
          _refused(lambda: routes.api_names({"op": "preview", "root": rid, "files": files, "tool": "Claude Code"}))
          and _refused(lambda: routes.api_add_transcripts({"op": "add", "root": rid, "files": files, "dry_run": True,
                                                          "tool": "Claude Code", "request": "x"})))
    nowhere = base / "Not yet a project"
    nowhere.mkdir()
    fresh = routes.api_names({"op": "preview", "folder": str(nowhere), "files": files})
    check("345: New project's preview, with no project yet, has the Real name's entry alone",
          fresh["entries"] == 1 and all(f["to"] == "Finch" for f in fresh["files"][0]["finds"]) and not list(nowhere.iterdir()))

    skip = f"{garethed[1]['entry']}:{garethed[1]['nth']}"
    done = routes.api_add_transcripts({"op": "add", "root": rid, "files": files, "skip": [skip]})
    finch = folder / "P10 - Finch" / "P10 Finch - EN & ES.xlsx"
    text = " ".join(r["text"] for r in routes.api_open({"path": str(finch)})["sheets"][0]["rows"])
    speakers = {r["name"] for r in routes.api_open({"path": str(finch)})["sheets"][0]["rows"]}
    entry = routes.pseudo_list(folder)[-1]
    check("345: the Add with a find unticked in the review writes what the review showed: that one left, every other "
          "replaced, the Real name's entry kept in the list for that participant",
          done["added"] and "Finch flies them with [partner] on the moor, and Gareth mends" in text
          and "Mirabel" not in text and "Thorne" not in " ".join(speakers) and done["names"]["left"] == 1
          and entry == {"real": ["Mirabel Thorne", "Mirabel"], "to": "Finch", "for": "Finch", "case": False}
          and (stat.S_IMODE((folder / names_mod.FILE).stat().st_mode) == 0o600 or os.name == "nt"), text[:300])

    # ── J. the transcripts already in: Check, then Review and replace
    moss = folder / "P1 - Moss"
    moss_book = moss / "P1 Moss - EN & ES.xlsx"
    moss_raw = moss / "Source" / "P1 Moss - transcript.xlsx"
    moss_copy = moss / "Source" / "Early" / "P1-Early.txt"
    checked = routes.api_names({"op": "check", "root": rid, "names_preview": True})
    found = checked["names"]["finds"]
    by_who = {}
    for f in found:
        by_who.setdefault(f["where"]["participant"], []).append(f)
    check("345: Check finds the names left in the transcripts already in, by participant, sheet and passage, the app's "
          "call with each find and the list, an agent's with counts alone",
          sorted(by_who) == ["Finch", "Moss", "Quill"] and all(f["found"] == "Gareth" for f in found)
          and by_who["Moss"][0]["where"]["part"] == "words" and by_who["Moss"][0]["where"]["turn"] == 2
          and checked["participants"] == 3 and len(checked["list"]) == len(routes.pseudo_list(folder))
          and moss_copy.is_file() and "Gareth" in moss_copy.read_text(encoding="utf-8")
          and "finds" not in routes.api_names({"op": "check", "root": rid, "names_preview": True, "tool": "Claude Code"})["names"],
          json.dumps(checked)[:500])
    quill = by_who["Quill"][0]
    replaced = routes.api_names({"op": "replace", "root": rid, "skip": [f"{quill['entry']}:{quill['nth']}"]})
    rows_of = lambda book: " ".join(str(c.value) for ws in openpyxl.load_workbook(book).worksheets
                                    for row in ws.iter_rows() for c in row if c.value is not None)
    archive = sorted((moss / "_Archive").glob("*(pre-names *"))
    check("345: Review and replace replaces the finds ticked and leaves the one unticked",
          replaced["replaced"] is True and replaced["names"]["replaced"] == len(found) - 1 and replaced["names"]["left"] == 1
          and replaced["participants"] == 2 and "Gareth" not in rows_of(moss_book) and "[partner] built it" in rows_of(moss_book)
          and "Gareth" in rows_of(folder / "P9 - Quill" / "P9 Quill - EN & ES.xlsx")
          and "Gareth" not in rows_of(finch), json.dumps(replaced)[:300])
    check("345: the workbook and its raw source as they were are kept first in the participant's _Archive, the real "
          "names in them, and the raw source and Source's copy now hold the pseudonyms",
          len([p for p in archive if p.suffix == ".xlsx"]) == 2 and all("Gareth" in rows_of(p) for p in archive if p.suffix == ".xlsx")
          and any(p.suffix == ".txt" and "Gareth" in p.read_text(encoding="utf-8") for p in archive)
          and "Gareth" not in rows_of(moss_raw) and "[partner]" in rows_of(moss_raw)
          and "Gareth" not in moss_copy.read_text(encoding="utf-8") and "[partner]" in moss_copy.read_text(encoding="utf-8"),
          str([p.name for p in archive]))
    history = json.loads((folder / "idiograph-history.json").read_text(encoding="utf-8"))["history"]
    check("345: the project's History says what was replaced in counts alone, no name",
          history[-1]["op"] == "names replace" and "Gareth" not in json.dumps(history) and "Mirabel" not in json.dumps(history)
          and "_Archive" in history[-1]["changes"][0])
    again = routes.api_names({"op": "check", "root": rid})
    check("345: checked again, only the find left as written is there", again["names"]["replaced"] == 1)

    # ── K. a shared copy leaves out the list and the archive that keeps the real names
    sent = base / "Hens again.idiograph"
    routes.api_send_project({"root": rid, "to": str(sent)})
    with zipfile.ZipFile(sent) as z:
        members = z.namelist()
        holds = [m for m in members if not m.endswith("/") and "P9 - Quill" not in m
                 and any(w in z.read(m).decode("utf-8", errors="replace").lower() for w in ("gareth", "mirabel"))
                 and not m.endswith(".xlsx")]
        books = [m for m in members if m.endswith(".xlsx") and "P9 - Quill" not in m and "gareth" in
                 " ".join(str(c.value) for ws in openpyxl.load_workbook(io.BytesIO(z.read(m))).worksheets
                          for row in ws.iter_rows() for c in row if c.value is not None).lower()]
    check("345: a shared copy holds neither the list's file nor an archive kept before the names were replaced",
          not any(names_mod.FILE in m or "(pre-names " in m for m in members) and not holds and not books,
          str(holds[:4] + books[:4]))

    # ── L. the agents: replace by the command line and the MCP server, counts only
    code_, out, err = cli.run(["--root", str(folder), "--config", str(config), "--json", "names", "replace", "--dry-run"])
    dry = json.loads(out) if code_ == 0 else {}
    check("345: names replace's dry run tells an agent the counts, no name, and writes nothing",
          code_ == 0 and dry.get("dry_run") is True and dry["names"]["replaced"] == 1
          and "gareth" not in out.lower() and "finds" not in dry["names"], err or out[:300])
    srv = mcp_server.Server(str(folder), config=str(config))
    srv.receive(json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                            "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "claude-code"}}}))
    got = srv.receive(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                  "params": {"name": "names_replace", "arguments": {"dry_run": True, "request": "x"}}}))["result"]
    check("345: MCP's names_replace answers counts only",
          not got.get("isError") and got["structuredContent"]["names"]["replaced"] == 1 and "gareth" not in json.dumps(got).lower(),
          json.dumps(got)[:300])
