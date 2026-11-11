#!/usr/bin/env python3
"""Runnable checks for Idiograph. Every fixture is a copy in a scratch folder, so nothing under
Main Data or Participant Data is ever opened for writing. In a build, once, at the end:

    .venv/bin/python Tools/idiograph/tests/test_idiograph.py --changed

which runs the areas the change touches, or pass `--area 158`, or `--area 157,158`, to run chosen
areas alone, and `--app sift` (or idiograph, or trace) to run one app's areas and the shared ones. The full suite runs in the coordinator's train, by ./verify, which sets IDIOGRAPH_TRAIN=1
for its run, and on GitHub. `--train` asks for one. Anywhere else a run with no `--area` or
`--changed` says so in one line and runs nothing.

The fixture is the demo case that ships with the app, Juno's, as its head start built from the demo's
own sources (see areas/support.py), so the whole suite runs on a machine with no real study data on it
at all. A reference workbook and a raw source workbook, which the local gate
file names (see areas/support.py), add coverage when they are there, and report SKIP when they are not.

Each area of checks is a file of its own under `areas/`, run in the order of `AREAS` below, and
`areas/support.py` holds what more than one area uses (see tests/README.md).

Pass `--scratch <folder>` to keep the copies somewhere you can look at afterwards, and
`--main-data <folder>` (or set `IDIOGRAPH_MAIN_DATA`) to point the reference fixtures elsewhere,
which is how a run with no live data is proved.
"""
from __future__ import annotations

import argparse
import contextlib
import importlib
import inspect
import io
import os
import re
import subprocess
import sys
import tempfile
import time
import traceback
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent
sys.path.insert(0, str(TOOL))
import boot  # noqa: E402  the family's folders on the path, as every entry puts them (boot.py)

boot.setup()
if str(HERE) not in sys.path:
    sys.path.insert(1, str(HERE))
# the runner answers to its own name when it runs as a script too, so an area that reads `run_all`
# finds this one
sys.modules.setdefault("test_idiograph", sys.modules[__name__])

from areas import support
from areas.support import (
    DEMO_WORKBOOK, FAILED, PASSED, REPO, SKIPPED, areas_listed, check, oldest_python_compiles, set_main_data,
)

# Every area in the order the suite runs them, each the file areas/<name>.py, which holds the function
# test_ and the name after its number, with the app it checks: idiograph, sift, trace, or shared for
# what every app holds (the split, 20 October 2026). `--app sift` runs Sift's areas and the shared ones,
# and the gate runs them all. A new area is a new file there and its line at the end here, its app
# beside it (see tests/README.md).
AREA_APPS = ("idiograph", "sift", "trace", "shared")
AREAS = {
    "a001_roundtrip": "idiograph",
    "a002_reference_roundtrip": "idiograph",
    "a003_create_from_source": "idiograph",
    "a005_rounds": "idiograph",
    "a006_lock_guard": "idiograph",
    "a007_nudges": "idiograph",
    "a008_corpus": "idiograph",
    "a009_export": "idiograph",
    "a010_progress": "idiograph",
    "a011_wipe": "idiograph",
    "a012_entries": "idiograph",
    "a013_no_case_folder_names": "shared",
    "a015_flags": "idiograph",
    "a016_audio": "idiograph",
    "a017_key_and_suggest": "shared",
    "a018_quote_assembly": "idiograph",
    "a019_trim": "idiograph",
    "a020_new_surface": "idiograph",
    "a021_root_guard": "idiograph",
    "a022_round_two": "idiograph",
    "a023_three_columns": "idiograph",
    "a024_ai_surface": "idiograph",
    "a025_edit_turn": "idiograph",
    "a026_crux_ops": "idiograph",
    "a027_polish": "idiograph",
    "a028_player_and_rail": "idiograph",
    "a029_demo": "idiograph",
    "a030_assign": "idiograph",
    "a031_row_menu": "idiograph",
    "a032_launcher": "shared",
    "a033_passed_and_bars": "idiograph",
    "a034_library_and_sheets": "idiograph",
    "a035_untrim": "idiograph",
    "a036_ai_settings": "shared",
    "a037_project": "idiograph",
    "a038_polish_items": "idiograph",
    "a039_themes": "idiograph",
    "a040_themes_versions": "idiograph",
    "a041_themes_ai": "idiograph",
    "a042_themes_feedback": "idiograph",
    "a043_themes_feedback_two": "idiograph",
    "a044_themes_boards": "idiograph",
    "a045_themes_feedback_three": "idiograph",
    "a046_themes_review_print": "idiograph",
    "a047_theme_notes": "idiograph",
    "a048_themes_follow": "idiograph",
    "a049_themes_panels": "idiograph",
    "a050_themes_guidance": "idiograph",
    "a052_pets_bar": "idiograph",
    "a053_phase_complete_and_settings": "idiograph",
    "a054_turn_bar": "idiograph",
    "a055_frames": "idiograph",
    "a056_feedback": "shared",
    "a057_titles_and_edit": "idiograph",
    "a058_sheet_rounds_and_confetti": "idiograph",
    "a059_interviewer_notes": "idiograph",
    "a060_sticky_notes": "idiograph",
    "a061_canvas_fits": "idiograph",
    "a062_docs": "shared",
    "a063_round_markers": "idiograph",
    "a064_make_way": "idiograph",
    "a065_settings_and_quotes": "idiograph",
    "a066_find_replace": "idiograph",
    "a068_pets_phases": "idiograph",
    "a069_momentum": "idiograph",
    "a070_review_rounds": "idiograph",
    "a071_polish_batch": "idiograph",
    "a072_transcript_import": "idiograph",
    "a073_mac_app": "shared",
    "a074_demo_cases": "idiograph",
    "a075_gets": "idiograph",
    "a076_picked_top": "idiograph",
    "a077_ai_revise": "idiograph",
    "a078_gets_table": "idiograph",
    "a079_agent_cli": "idiograph",
    "a080_title_box": "idiograph",
    "a081_pet_print": "idiograph",
    "a082_sidebar": "idiograph",
    "a083_gets_ai": "idiograph",
    "a084_mcp_server": "idiograph",
    "a085_home_screen": "idiograph",
    "a086_gets_sub_cards": "idiograph",
    "a087_word_export": "idiograph",
    "a088_quote_pairs": "idiograph",
    "a089_projects": "idiograph",
    "a090_pet_table": "idiograph",
    "a091_print_table": "idiograph",
    "a092_groups": "idiograph",
    "a093_pet_labels": "idiograph",
    "a094_canvas_print": "idiograph",
    "a095_loose_ends": "idiograph",
    "a096_quotes_safe": "idiograph",
    "a097_loose_ends_two": "idiograph",
    "a098_sift": "sift",
    "a099_sift_two": "sift",
    "a100_ai_switch": "shared",
    "a101_no_continue": "shared",
    "a102_new_project": "idiograph",
    "a103_sift_table": "sift",
    "a104_sift_search": "sift",
    "a105_sift_layout": "sift",
    "a106_sift_databases": "sift",
    "a107_sift_follow": "sift",
    "a108_add_transcripts": "idiograph",
    "a109_sift_reviews": "sift",
    "a110_home_and_settings": "shared",
    "a111_sift_screen": "sift",
    "a112_sift_strategy": "sift",
    "a113_sift_runs": "sift",
    "a114_sift_zotero": "sift",
    "a115_sift_facets": "sift",
    "a116_sift_polish": "sift",
    "a117_sift_ux_review": "sift",
    "a118_sift_review_two": "sift",
    "a119_sift_second": "sift",
    "a121_sift_from_use": "sift",
    "a122_sift_steps": "sift",
    "a123_sift_plan": "sift",
    "a124_sift_plan_two": "sift",
    "a125_sift_columns_drag": "sift",
    "a126_sift_words": "sift",
    "a127_sift_rows": "sift",
    "a128_sift_openalex": "sift",
    "a129_sift_form": "sift",
    "a130_sift_map": "sift",
    "a132_sift_map_layout": "sift",
    "a133_sift_match": "sift",
    "a134_sift_terms": "sift",
    "a135_es_numbers": "idiograph",
    "a136_es_quote": "idiograph",
    "a137_sift_plain_words": "sift",
    "a138_sift_suggestion": "sift",
    "a139_sift_excerpts": "sift",
    "a141_distclone": "shared",
    "a142_wininstaller": "shared",
    "a143_refcheck": "trace",
    "a144_windows_text": "shared",
    "a145_trace": "trace",
    "a146_distil_name": "shared",
    "a147_colour_problems": "shared",
    "a148_identity": "shared",
    "a149_part_order": "shared",
    "a150_rounds_and_passages": "idiograph",
    "a151_statement_views": "idiograph",
    "a152_statement_from_selection": "idiograph",
    "a153_key_quote_marks": "idiograph",
    "a154_minimap": "idiograph",
    "a155_on_screen_controls": "idiograph",
    "a156_rename_and_go_to_passage": "idiograph",
    "a157_case_colours_and_nesting": "idiograph",
    "a158_guidance_sheet": "idiograph",
    "a159_quit_after_last_tab": "shared",
    "a160_feedback_names_its_screen": "shared",
    "a163_sweep_cards": "sift",
    "a164_tauri_window": "shared",
    "a165_sift_trace_left": "shared",
    "a166_distil_left": "idiograph",
    "a167_window_menus": "shared",
    "a168_search": "idiograph",
    "a169_minimap_corner": "idiograph",
    "a170_one_tone": "shared",
    "a171_keys_and_orange": "shared",
    "a172_three_columns": "idiograph",
    "a173_release": "shared",
    "a174_rich_text_without_lxml": "idiograph",
    "a175_updates": "shared",
    "a176_polish_seven": "shared",
    "a177_distil_steps": "idiograph",
    "a178_search_sift_trace": "shared",
    "a179_board_map": "idiograph",
    "a180_tauri_words": "shared",
    "a181_minimap_box": "idiograph",
    "a182_polish_eight": "idiograph",
    "a183_review_shot": "shared",
    "a184_relaunch_again": "shared",
    "a185_polish_nine": "idiograph",
    "a186_columns_layout": "idiograph",
    "a187_quote_colours": "idiograph",
    "a188_drag_and_drop": "idiograph",
    "a189_train_rule": "shared",
    "a191_board_table": "idiograph",
    "a192_two_windows": "idiograph",
    "a193_polish_ten": "shared",
    "a194_export_ticks": "idiograph",
    "a195_mac_print": "shared",
    "a196_agent_api": "idiograph",
    "a197_agent_api_two": "idiograph",
    "a198_stale_saves": "idiograph",
    "a199_stacks": "idiograph",
    "a200_send_tick": "idiograph",
    "a201_status_bar_and_palette": "idiograph",
    "a202_reorder_gap_and_status_menu": "idiograph",
    "a203_back_and_forward": "idiograph",
    "a204_word_table_notes": "idiograph",
    "a205_card_quotes_and_by_participant": "idiograph",
    "a206_mcp_prompts": "idiograph",
    "a207_agent_import": "idiograph",
    "a208_table_parity": "idiograph",
    "a209_import_marked_up": "idiograph",
    "a212_search_cases": "idiograph",
    "a213_loose_ends": "idiograph",
    "a214_close_pairs": "idiograph",
    "a215_timepoints": "idiograph",
    "a216_quote_inserts": "idiograph",
    "a217_boards_feedback": "idiograph",
    "a218_board_cap": "idiograph",
    "a219_app_identity": "shared",
    "a220_column_widths": "idiograph",
    "a221_sidebar_not_bin": "idiograph",
    "a222_routes": "shared",
    "a223_pages": "shared",
    "a224_agent_pdf": "idiograph",
    "a225_print_view_keys": "idiograph",
    "a226_app_commands": "shared",
    "a227_stage_tabs": "idiograph",
    "a228_words": "shared",
    "a229_pack": "shared",
    "a230_rekey": "idiograph",
    "a231_statement_guidance": "idiograph",
    "a232_send_project": "idiograph",
    "a233_unfold": "idiograph",
    "a234_home_batch": "idiograph",
    "a235_timepoint_boards": "idiograph",
    "a236_panels": "idiograph",
    "a237_lgets_trajectories": "idiograph",
    "a238_check_key": "shared",
    "a239_toolbar": "idiograph",
    "a240_share_menu": "idiograph",
    "a241_quote_first": "idiograph",
    "a242_descriptions": "idiograph",
    "a243_quote_link": "idiograph",
    "a244_qdpx": "idiograph",
    "a245_qdpx_card": "idiograph",
    "a246_agent_start": "shared",
    "a247_description_kept": "idiograph",
    "a249_take_makes_room": "idiograph",
    "a250_quote_header": "idiograph",
    "a252_title_enter": "idiograph",
    "a253_boundaries": "shared",
    "a254_trace_sift_pdfs": "trace",
    "a255_home_mark_order": "idiograph",
    "a256_sift_fixes": "sift",
    "a257_quote_heading": "idiograph",
    "a258_send_chosen": "idiograph",
    "a259_quotes_keep_places": "idiograph",
    "a260_boards_come_back": "idiograph",
    "a261_passage_replace": "idiograph",
    "a262_subpet_rests_close": "idiograph",
    "a263_send_boards_row": "idiograph",
    "a264_status_counts_add_up": "idiograph",
    "a265_statements_ops": "idiograph",
    "a266_project_ops": "idiograph",
    "a267_board_ops": "idiograph",
    "a268_export_op": "idiograph",
    "a269_bars_option_c": "shared",
    "a270_pets_complete_op": "idiograph",
    "a271_loose_ends": "shared",
    "a272_copy_back_card": "idiograph",
    "a273_gets_steps_last_opened": "idiograph",
    "a274_agent_words_marked": "shared",
    "a275_settings_opens_alone": "shared",
    "a276_agent_holds": "idiograph",
    "a277_drive_stops_server": "shared",
    "a278_text_layer": "shared",
    "a279_page_words": "idiograph",
    "a280_distil_words": "idiograph",
    "a281_boards_words": "idiograph",
    "a282_server_words": "idiograph",
    "a283_us_english": "shared",
    "a284_long_texts": "idiograph",
    "a285_formats": "shared",
    "a286_timecodes": "idiograph",
    "a287_print_landscape": "idiograph",
    "a288_format_places": "shared",
    "a289_support": "shared",
    "a291_whats_new_span": "shared",
    "a292_text_size_said": "shared",
    "a294_board_gaps": "idiograph",
    "a295_frame_styles": "shared",
    "a297_card_edit": "idiograph",
    "a298_gets_edit": "idiograph",
    "a299_count_steady": "idiograph",
    "a300_history_replace": "idiograph",
    "a301_quote_span": "idiograph",
    "a302_subpet_under_two": "idiograph",
    "a303_history_dates": "idiograph",
    "a304_quotes_three_ways": "idiograph",
    "a305_board_view": "idiograph",
    "a306_project_method": "idiograph",
    "a307_refusal_codes": "shared",
    "a309_agent_board_room": "idiograph",
    "a311_print_pages": "idiograph",
    "a312_drag_design_a": "idiograph",
    "a313_canvas_out": "idiograph",
    "a314_holds_together": "idiograph",
    "a315_passage_way_back": "idiograph",
    "a316_code_list": "idiograph",
    "a317_window_key": "idiograph",
    "a318_sift_trace_words_marked": "shared",
    "a319_project_history": "idiograph",
    "a320_themes_map": "idiograph",
    "a321_agent_log": "idiograph",
    "a322_project_history_ui": "idiograph",
    "a323_sift_trace_agent_log": "shared",
    "a324_ta_guidance": "idiograph",
    "a325_demo_projects": "idiograph",
    "a326_ta_ai": "idiograph",
    "a327_ai_prompt_op": "idiograph",
    "a328_project_settings": "idiograph",
    "a329_search_modifiers": "shared",
    "a330_bars_option_d": "shared",
    "a331_column_edge_handle": "idiograph",
    "a332_shared_copy_file": "idiograph",
    "a333_lockup_headroom": "shared",
    "a334_copy_back_whole": "idiograph",
    "a335_copy_back_as_sent": "idiograph",
    "a336_player_jump_buttons": "idiograph",
    "a337_band_table_link": "shared",
    "a338_search_forms_and_small_faults": "idiograph",
    "a339_keyboard_and_reader": "shared",
    "a340_qdpx_export": "idiograph",
    "a341_team_keys": "idiograph",
    "a342_relay": "shared",
    "a343_team_review": "idiograph",
    "a344_openai_providers": "shared",
    "a345_names_rules": "idiograph",
    "a346_linux_folders": "shared",
    "a347_ai_provider_page": "idiograph",
    "a348_linux_server_build": "shared",
    "a349_team_owners": "idiograph",
    "a350_linux_window_build": "shared",
    "a351_team_board": "idiograph",
    "a352_team_devices": "idiograph",
    "a353_team_folder": "idiograph",
    "a354_linux_pdf_and_image": "idiograph",
    "a355_linux_release": "shared",
    "a356_linux_three_apps": "shared",
    "a357_relay_project": "idiograph",
    "a358_quotes_and_recordings": "idiograph",
    "a359_quick_keys": "idiograph",
    "a360_linux_desktop_fixes": "shared",
    "a361_mac_daily": "shared",
    "a362_typesetter": "shared",
    "a363_pets_table_typst": "idiograph",
    "a364_gets_typst": "idiograph",
    "a365_typst_canvas": "idiograph",
    "a366_tables_of_pets": "idiograph",
    "a367_exports_typst": "idiograph",
    "a368_team_suggestions": "idiograph",
    "a369_trajectories_f": "idiograph",
    "a371_agent_order_kept": "idiograph",
    "a372_participant_words": "shared",
    "a373_participant_set": "idiograph",
}


def area(name: str, scratch: Path):
    """One area of checks, its file under areas/ loaded and its function run, with the scratch folder
    when it takes one. An error inside it, or in loading it, is one failed check with its reason, and
    the areas after it still run, so a first run on another system, Windows on GitHub's machines,
    lists every area that fails rather than the first alone (14 October)."""
    fn_name = "test_" + name.split("_", 1)[1]
    try:
        fn = getattr(importlib.import_module(f"areas.{name}"), fn_name)
        fn(*([scratch] if inspect.signature(fn).parameters else []))
    except Exception as exc:
        traceback.print_exc(file=sys.stdout)
        check(f"{fn_name} ran to its end", False, f"{type(exc).__name__}: {exc}")


def chosen(spec: str) -> list[str]:
    """The areas `--area` names, in the suite's order: by number, 158, 157,158 or 150-152, or by a word
    of a file's name, guidance. One that names no area is an error."""
    picked = set()
    for part in (p.strip() for p in spec.split(",") if p.strip()):
        if re.fullmatch(r"\d+", part):
            hit = [n for n in AREAS if int(n[1:4]) == int(part)]
        elif re.fullmatch(r"\d+-\d+", part):
            low, high = (int(x) for x in part.split("-"))
            hit = [n for n in AREAS if low <= int(n[1:4]) <= high]
        else:
            hit = [n for n in AREAS if part.lower() in n[5:]]
        if not hit:
            raise ValueError(part)
        picked.update(hit)
    return [n for n in AREAS if n in picked]


def of_app(app: str) -> list[str]:
    """The areas `--app` runs, in the suite's order: the app's own and the shared ones. An app that is
    none of the three is an error."""
    if app not in AREA_APPS or app == "shared":
        raise ValueError(app)
    return [n for n, tag in AREAS.items() if tag in (app, "shared")]


def areas_tagged(areas: dict) -> list[str]:
    """Each area whose app is none of AREA_APPS."""
    return [n for n, tag in areas.items() if tag not in AREA_APPS]


def run_all(scratch: Path, only=None):
    """Run every check against fixtures copied into `scratch`, or the areas `only` names, then the
    suite's own checks. Returns the three name lists. Each area's seconds and count of checks go to
    TIMINGS as it ends, so a run can say which areas take longest."""
    PASSED.clear()
    FAILED.clear()
    SKIPPED.clear()
    TIMINGS.clear()
    scratch.mkdir(parents=True, exist_ok=True)
    # The recent list the app keeps in state.json, pointed at the scratch folder for the whole run,
    # since a check that opens a case through the API adds it to the list. A check that points it
    # elsewhere puts it back as it found it.
    import server as server_mod
    real_state = server_mod.STATE_PATH
    server_mod.STATE_PATH = scratch / "suite-state.json"
    # and the settings, a file in the scratch folder that is not there, as a downloaded copy and the
    # gate's snapshot have none, so no check reads this machine's own config.json (14 October)
    real_config = server_mod.CONFIG_PATH
    server_mod.CONFIG_PATH = scratch / "suite-config.json"
    # and no server the suite starts quits by itself a few minutes after its last tab closes, in this
    # process or a child, whatever its settings say, so no check is cut short (16 October)
    os.environ[server_mod.STAY_OPEN] = "1"
    # and the computer's language British English, in this process and a child, so a check reading the page or a
    # server's line reads it on a computer in American English or any other (i18nus, 28 October 2026)
    import i18n as i18n_mod
    os.environ[i18n_mod.COMPUTER_STANDIN] = "en-GB"
    i18n_mod._COMPUTER.clear()
    # and the computer's own formats British too, as the window hands them a server (fmtcore, 28 October 2026)
    os.environ[i18n_mod.COMPUTER_FORMATS] = '{"date": "28/10/2026", "time": "14:05", "number": "1,234.5"}'
    # and every script a check runs in node with the text layer in front, as the page has it (siftlang, 1 November 2026)
    support.node_text_layer(scratch)
    # and an agent's action that would wait for his yes in the app runs at once in this process, as with
    # Dangerously skip permissions on, so each op's own checks run it: area 276 checks the holds themselves
    # (27 October 2026)
    import holds as holds_mod
    holds_mod.RUN_AT_ONCE = True
    # and the agent log a file in the scratch folder, in this process and a child, so no check's refusal of an agent
    # lands in this machine's own log (agentlog, 3 November 2026)
    import agent_log
    os.environ[agent_log.PLACE] = str(scratch / "suite-agent-log.json")
    for name in AREAS if only is None else only:
        began, counted = time.monotonic(), len(PASSED) + len(FAILED) + len(SKIPPED)
        area(name, scratch)
        TIMINGS.append((name, time.monotonic() - began, len(PASSED) + len(FAILED) + len(SKIPPED) - counted))
    left = server_mod.STATE_PATH
    server_mod.STATE_PATH = real_state
    server_mod.CONFIG_PATH = real_config
    check("the suite keeps its recent list in the scratch folder to the end", left == scratch / "suite-state.json",
          str(left))
    recent = server_mod.load_json(real_state, {"recent": []}).get("recent", []) if real_state.exists() else []
    stray = [r for r in recent if str(scratch) in str(r.get("path", ""))]
    check("the app's own state.json holds no case from the suite's scratch folder", not stray, f"{len(stray)} entries")
    # the suite's own, after every run, a chosen area's too (17 October)
    areas_listed(AREAS)
    untagged = areas_tagged(AREAS)
    check("the suite's areas: each tagged idiograph, sift, trace or shared", not untagged, str(untagged[:5]))
    oldest_python_compiles()
    return list(PASSED), list(FAILED), list(SKIPPED)


# (area, seconds, checks) for each area the last run_all ran, in the order it ran them
TIMINGS: list[tuple[str, float, int]] = []


def slowest(count: int = 15) -> list[tuple[str, float, int]]:
    """The areas of the last run that took longest, slowest first."""
    return sorted(TIMINGS, key=lambda t: -t[1])[:count]


def write_timings(path) -> None:
    """Every area of the last run as a line of its name, seconds and checks, slowest first."""
    rows = ["area\tseconds\tchecks"] + [f"{n}\t{sec:.2f}\t{c}" for n, sec, c in slowest(len(TIMINGS))]
    Path(path).write_text("\n".join(rows) + "\n", encoding="utf-8")


# The variable ./verify sets for its own run of the suite, which makes that run a train's.
TRAIN_ENV = "IDIOGRAPH_TRAIN"

REFUSAL = ("The full suite runs in the coordinator's train, by ./verify. In a build, run "
           "tests/test_idiograph.py --changed (or --area with the areas your change touches) once, at the end.")


def train_reason(train: bool = False, env=None):
    """Why a run of every area may go ahead here, or None when it may not: `--train`, the gate's own
    run (./verify sets IDIOGRAPH_TRAIN=1 for it) or GitHub's (GITHUB_ACTIONS=true). Anywhere else the
    full suite is the coordinator's train's (Adam, 18 October)."""
    env = os.environ if env is None else env
    if train:
        return "--train"
    if env.get(TRAIN_ENV, "").strip() == "1":
        return "the gate"
    if env.get("GITHUB_ACTIONS", "").strip().lower() == "true":
        return "GitHub"
    return None


# ─────────────────────────────────────────── --changed, the areas a change touches ──
#
# A build checks the areas its change touches, once, at the end (Adam, 18 October). The change is
# every file of the app that differs from main, committed, staged, in the working tree or new. An
# area is chosen when its source names one of those files, or a top-level name the change touches in
# one: a Python or script file's functions, classes and constants whose lines changed, a style
# sheet's classes, ids and custom properties in the rules that changed, a page's ids and classes on
# the lines that changed. Every new area and every area whose own file changed is chosen too, and
# the suite's own checks run after them as after every run. A name more than COMMON areas carry,
# app.js or a class called card, is a word in common use there, not a pointer, and chooses nothing.

COMMON = 20
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
TOP_LEVEL = {
    ".js": re.compile(r"^(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)|^(?:const|let|var|class)\s+([A-Za-z_$][\w$]*)"),
    ".py": re.compile(r"^(?:async\s+)?(?:def|class)\s+([A-Za-z_]\w*)|^([A-Za-z_]\w*)\s*(?::[^=\n]*)?=(?!=)"),
}
HEX_COLOUR = re.compile(r"^[0-9a-fA-F]{3,8}$")
NAMED_SUFFIXES = (".js", ".py", ".css", ".html", ".htm")


def git_text(tool: Path, *args: str):
    """What git prints for the app's folder `tool`, or None where there is no git or no repository."""
    try:
        ran = subprocess.run(["git", "-c", "core.quotepath=off", "-C", str(tool), *args], capture_output=True,
                             encoding="utf-8", errors="replace", timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    return ran.stdout if ran.returncode == 0 else None


def touched_lines(diff: str):
    """The lines a diff made with -U0 changes, in the old file and in the new. Where a side has none,
    a pure addition or a deletion, the lines either side of the place are marked instead."""
    old, new = set(), set()
    for line in diff.splitlines():
        hunk = HUNK.match(line)
        if hunk:
            a, b, c, d = (int(hunk[1]), int(hunk[2] or 1), int(hunk[3]), int(hunk[4] or 1))
            old.update(range(a, a + b) if b else (a, a + 1))
            new.update(range(c, c + d) if d else (c, c + 1))
    return old, new


def top_level(text: str, rx) -> list:
    """Each top-level definition in a script or a Python file, its name and its first and last line,
    a definition running to the line before the next one."""
    lines = text.splitlines()
    starts = [(i, next(g for g in m.groups() if g)) for i, line in enumerate(lines, 1) if (m := rx.match(line))]
    return [(name, at, starts[k + 1][0] - 1 if k + 1 < len(starts) else len(lines))
            for k, (at, name) in enumerate(starts)]


def css_names(text: str, touched) -> set:
    """The classes and ids of the rules a change touches in a style sheet, each touched line's own
    selector and the selector of the rule it sits in, and the custom properties on its lines."""
    text = re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m[0]), text, flags=re.S)
    lines, inside, stack, pending, names = text.splitlines(), {}, [], "", set()
    for i, line in enumerate(lines, 1):
        inside[i] = stack[-1] if stack else ""
        for part in re.split(r"([{}])", line):
            if part == "{":
                stack.append(pending)
                pending = ""
            elif part == "}":
                stack = stack[:-1]
                pending = ""
            else:
                pending = "" if ";" in part else pending + " " + part
    for i in (n for n in touched if 1 <= n <= len(lines)):
        line = lines[i - 1]
        names.update(re.findall(r"(?<![\w-])(--[A-Za-z][\w-]*)\s*:", line))
        own = line.split("{", 1)[0] if ("{" in line or ":" not in line) else ""
        names.update(n for n in re.findall(r"[.#]([A-Za-z_][\w-]*)", own + " " + inside[i]) if not HEX_COLOUR.match(n))
    return names


def html_names(text: str, touched) -> set:
    """The ids and classes on the lines a change touches in a page."""
    lines, names = text.splitlines(), set()
    for line in (lines[n - 1] for n in touched if 1 <= n <= len(lines)):
        names.update(re.findall(r'\bid="([^"]+)"', line))
        for classes in re.findall(r'\bclass="([^"]+)"', line):
            names.update(classes.split())
    return names


def names_touched(path: str, old: str, new: str, old_lines, new_lines) -> set:
    """The top-level names a change to one file touches, on either side of it."""
    suffix = Path(path).suffix.lower()
    if suffix in TOP_LEVEL:
        return {name for text, lines in ((old, old_lines), (new, new_lines))
                for name, a, b in top_level(text, TOP_LEVEL[suffix]) if any(a <= n <= b for n in lines)}
    if suffix == ".css":
        return css_names(old, old_lines) | css_names(new, new_lines)
    if suffix in (".html", ".htm"):
        return html_names(old, old_lines) | html_names(new, new_lines)
    return set()


def naming(name: str):
    """A name as a whole word in an area's source, a hyphen or a dollar sign counting as part of it."""
    return re.compile(r"(?<![\w$-])" + re.escape(name) + r"(?![\w$-])")


def choose_changed(changes, sources: dict, own_areas: dict):
    """The areas a change touches, in the suite's order where it has them: (area, why) each, and the
    names too common to choose by. `changes` holds (path, old text, new text, diff) for each changed
    file of the app, `sources` each area's name and source, and `own_areas` each area whose own file
    changed, with the word for how ("a new area", "its own file changed")."""
    why = dict(own_areas)
    common = []
    words = {a: set(re.findall(r"[\w$-]+", source)) for a, source in sources.items()}
    for path, old, new, diff in changes:
        if path.startswith("tests/areas/a"):
            continue
        old_lines, new_lines = touched_lines(diff)
        # a file's own name, by which the areas name it by its path as it is now (the family codebase's sixth
        # build, 23 October 2026, retired the alias table that knew it by its old one)
        own = [Path(path).name] + ([Path(path).stem] if path.endswith(".py") else [])
        for name in own + sorted(names_touched(path, old, new, old_lines, new_lines) - set(own)):
            if re.fullmatch(r"[\w$-]+", name):
                hits = [a for a in sources if name in words[a]]
            else:
                rx = naming(name)
                hits = [a for a, source in sources.items() if rx.search(source)]
            if len(hits) > COMMON:
                common.append(f"{name} ({len(hits)} areas)")
                continue
            for a in hits:
                why.setdefault(a, f"names {name} ({path})")
    order = {name: i for i, name in enumerate(AREAS)}
    return sorted(why.items(), key=lambda item: (order.get(item[0], len(order)), item[0])), list(dict.fromkeys(common))


def changed_areas(tool: Path = TOOL, base: str = "main"):
    """The areas the change in `tool` touches against `base`, from git: every file that differs from
    where this branch left `base`, committed, staged or in the working tree, and every new one.
    Returns (base commit, [(area, why)], too common names), or None where git cannot say."""
    fork = None
    for ref in (base, f"origin/{base}"):
        fork = (git_text(tool, "merge-base", ref, "HEAD") or "").strip()
        if fork:
            break
    if not fork:
        return None
    listed = git_text(tool, "diff", "--no-ext-diff", "--no-renames", "--name-only", "--relative", fork, "--", ".")
    untracked = git_text(tool, "ls-files", "--others", "--exclude-standard")
    if listed is None or untracked is None:
        return None
    new_files = [p for p in untracked.splitlines() if p]
    paths = sorted({p for p in listed.splitlines() if p} | set(new_files))
    areas_dir = tool / "tests" / "areas"
    sources = {p.stem: p.read_text(encoding="utf-8", errors="replace")
               for p in sorted(areas_dir.glob("a[0-9][0-9][0-9]_*.py"))}
    at_base = {Path(p).stem for p in (git_text(tool, "ls-tree", "--name-only", fork, "tests/areas/") or "").splitlines()}
    own_areas, changes = {}, []
    for path in paths:
        stem = Path(path).stem
        if path.startswith("tests/areas/a") and stem in sources:
            own_areas[stem] = "a new area" if stem not in at_base else "its own file changed"
            continue
        file = tool / path
        if Path(path).suffix.lower() not in NAMED_SUFFIXES:
            changes.append((path, "", "", ""))  # chosen by its own name alone, so nothing more is read
            continue
        new = file.read_text(encoding="utf-8", errors="replace") if file.is_file() else ""
        if path in new_files:
            old, diff = "", f"@@ -0,0 +1,{max(1, len(new.splitlines()))} @@"
        else:
            old = git_text(tool, "show", f"{fork}:./{path}") or ""
            diff = git_text(tool, "diff", "--no-ext-diff", "--no-renames", "-U0", "--relative", fork, "--", path) or ""
        changes.append((path, old, new, diff))
    chosen_, common = choose_changed(changes, sources, own_areas)
    return fork, chosen_, common


class ESHelperChecks(unittest.TestCase):
    """The same checks, wrapped so `python -m unittest discover` collects them.

    One test method on purpose: the checks share fixture copies and run in sequence, and splitting
    them into methods would copy the demo workbook once per area for no gain. On a failure the whole
    transcript is printed and the assertion names every check that failed. It runs in a train alone,
    as the file run as a script does, and the gate's run is one, since ./verify sets IDIOGRAPH_TRAIN.
    """

    maxDiff = None

    def test_every_check_passes(self):
        if train_reason() is None:
            self.skipTest(REFUSAL)
        transcript = io.StringIO()
        with tempfile.TemporaryDirectory(prefix="idiograph-tests-") as tmp:
            with contextlib.redirect_stdout(transcript):
                passed, failed, skipped = run_all(Path(tmp))
        print(f"{len(passed)} passed, {len(failed)} failed, {len(skipped)} skipped")
        if failed:
            print(transcript.getvalue())
            self.fail(f"{len(failed)} of {len(passed) + len(failed)} checks failed:\n  "
                      + "\n  ".join(failed))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch")
    ap.add_argument("--main-data", help="where the GRAVITY cases are, for a run with none of them")
    ap.add_argument("--area", help="run these areas alone, by number or a word of the name: 158, 157,158, "
                                   "150-152 or guidance")
    ap.add_argument("--changed", action="store_true",
                    help="run the areas a change touches, from the files that differ from main")
    ap.add_argument("--train", action="store_true", help="run every area, as the coordinator's train does")
    ap.add_argument("--app", help="run the areas of one app, idiograph, sift or trace, and the shared ones, "
                                  "narrowing --area or --changed when given with them")
    ap.add_argument("--timings", help="write each area's seconds and checks to this file, slowest first")
    args = ap.parse_args()
    try:
        only = chosen(args.area) if args.area else None
    except ValueError as exc:
        ap.error(f"no area {exc}, the areas are 1 to {len(AREAS)} under tests/areas")
    try:
        own = of_app(args.app) if args.app else None
    except ValueError as exc:
        ap.error(f"no app {exc}, the apps are idiograph, sift and trace")
    if args.changed:
        got = changed_areas()
        if got is None:
            print("--changed needs git and a main branch to compare with. Run --area with the areas your "
                  "change touches.")
            return 2
        fork, picked, common = got
        print(f"--changed chose {len(picked)} areas for the change since main at {fork[:7]}:")
        for name, why in picked:
            print(f"  {name}: {why}")
        if common:
            print(f"  Too common to choose by: {', '.join(common)}")
        print("  The suite's own checks run after them, as after every run.")
        order = {name: i for i, name in enumerate(AREAS)}
        only = sorted(set(only or []) | {name for name, _ in picked}, key=lambda n: (order.get(n, len(order)), n))
    if own is not None:
        only = own if only is None else [n for n in only if n in own]
    if only is None and train_reason(args.train) is None:
        print(REFUSAL)
        return 2
    if args.main_data:
        set_main_data(args.main_data)
    scratch = Path(args.scratch) if args.scratch else Path(tempfile.mkdtemp(prefix="idiograph-tests-"))
    print(f"Idiograph tests. Fixtures copied into {scratch}")
    print(f"Real data folder: {REPO}{'' if REPO.exists() else ' (not on this machine)'}")
    print(f"Demo fixture: Juno's head start, built from demo/source into {DEMO_WORKBOOK.parent.parent}")
    print(f"Reference cases: {support.MAIN}{'' if support.MAIN.exists() else ' (not on this machine)'}")

    began = time.monotonic()
    passed, failed, skipped = run_all(scratch, only)

    if only is None:
        print("\nThe slowest areas:")
        for name, seconds, count in slowest():
            print(f"  {seconds:7.1f}s  {count:4d} checks  {name}")
    if args.timings:
        write_timings(args.timings)
    print(f"\n{len(TIMINGS)} areas in {time.monotonic() - began:.0f}s")
    print(f"{len(passed)} passed, {len(failed)} failed, {len(skipped)} skipped")
    for name in failed:
        print(f"  FAILED: {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
