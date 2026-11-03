# SPDX-License-Identifier: GPL-3.0-or-later
"""Preparation sub-steps in the step bar (#130, names shared with #138/#166).

Before: the header said "Preparation" on six screens in a row (keyboard,
ownership, pick, confirm, method, review), so it felt stuck. Now each of
those screens shows "Step N of 6 · <name>", derived from the wizard's own
Back table, and the strip fills step by step. Fake demo disks only.
"""

from __future__ import annotations

import json
import re
import sys

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.wizard import (
    BACK_SCREENS,
    PREPARATION_PATH,
    STEP_VARIANTS,
    journey_step_for,
)

MAIN = (Screen.KEYBOARD, Screen.OWNER, Screen.PICK, Screen.CONFIRM, Screen.METHOD,
        Screen.LAST_CHANCE)
NO_STEP = {
    Screen.SPLASH, Screen.STOPPING, Screen.WORKING, Screen.DONE, Screen.SHUTDOWN_CONFIRM,
    Screen.REFRESHING, Screen.REFRESH_CONFIRM, Screen.DIAGNOSTIC,
}


@pytest.fixture(autouse=True)
def _english_after():
    yield
    lang.set_language("en")


# --- One source: the wizard's Back table ---------------------------------------


def test_steps_are_the_back_chain_ending_at_review():
    assert PREPARATION_PATH == MAIN
    # Walk Back from Review by hand: the same screens, in the same order.
    walked = [Screen.LAST_CHANCE]
    while walked[-1] in BACK_SCREENS:
        walked.append(BACK_SCREENS[walked[-1]])
    assert tuple(reversed(walked)) == PREPARATION_PATH
    # Review is the last step before Erase (#166).
    assert PREPARATION_PATH[-1] == Screen.LAST_CHANCE


def test_back_still_follows_the_same_table_on_the_real_wizard():
    wiz = make_demo_wizard()
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    wiz.select_disk(sorted(wiz.selectable, key=lambda d: d.path)[0].path)
    wiz.continue_pick()
    wiz.set_confirm_input(wiz.confirm.token)
    wiz.continue_confirm()
    wiz.continue_method()
    seen = [wiz.screen]
    while wiz.screen != Screen.KEYBOARD:
        wiz.back()
        seen.append(wiz.screen)
    assert tuple(reversed(seen)) == PREPARATION_PATH
    assert not wiz.runner.started


def test_every_screen_has_exactly_one_kind_of_step():
    for screen in Screen:
        kinds = [
            screen in PREPARATION_PATH,
            screen in STEP_VARIANTS,
            screen in BACK_SCREENS and screen not in PREPARATION_PATH and screen not in STEP_VARIANTS,
            screen in NO_STEP,
            screen == Screen.REPORT_HELP,  # detour that remembers where it was opened
        ]
        assert sum(kinds) == 1, screen
    assert set(STEP_VARIANTS.values()) <= set(PREPARATION_PATH)


def test_each_step_has_a_name_and_numbers_count_up_without_gaps():
    labels = []
    for number, screen in enumerate(PREPARATION_PATH, 1):
        assert journey_step_for(screen) == (number, len(PREPARATION_PATH), screen)
        labels.append(C.STEP_CAPTION.format(n=number, total=len(PREPARATION_PATH),
                                            name=C.step_name(screen)))
    assert len(set(labels)) == len(labels)
    assert labels[2] == "Step 3 of 6 · Choose a disk"
    assert labels[5] == "Step 6 of 6 · Review and erase"


@pytest.mark.parametrize("screen,parent", [
    (Screen.WHAT, Screen.OWNER),
    (Screen.PICK_EMPTY, Screen.PICK),
    (Screen.PICK_BLOCKED, Screen.PICK),
    (Screen.DISK_HELP, Screen.PICK),
    (Screen.ADVANCED, Screen.METHOD),
    (Screen.LIMITS, Screen.METHOD),
    (Screen.CHECKING, Screen.LAST_CHANCE),
])
def test_variants_and_detours_show_the_step_they_belong_to(screen, parent):
    assert journey_step_for(screen) == journey_step_for(parent)


@pytest.mark.parametrize("screen", sorted(NO_STEP, key=lambda s: s.value))
def test_busy_erase_result_and_recovery_screens_have_no_step(screen):
    assert journey_step_for(screen) is None


# --- The real wizard, including conditional screens ------------------------------


def _at(screen):
    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.skip_splash()
    if screen == Screen.KEYBOARD:
        return wiz
    wiz.accept_keyboard()
    if screen == Screen.OWNER:
        return wiz
    wiz.set_owner(True)
    wiz.continue_owner()
    if screen == Screen.PICK:
        return wiz
    wiz.select_disk(sorted(wiz.selectable, key=lambda d: d.path)[0].path)
    wiz.continue_pick()
    if screen == Screen.CONFIRM:
        return wiz
    wiz.set_confirm_input(wiz.confirm.token)
    wiz.continue_confirm()
    if screen == Screen.METHOD:
        return wiz
    wiz.continue_method()
    assert screen == Screen.LAST_CHANCE
    return wiz


def test_every_preparation_screen_shows_a_distinct_correct_label():
    seen = {}
    for number, screen in enumerate(MAIN, 1):
        wiz = _at(screen)
        assert wiz.screen == screen
        caption = C.journey_step_caption(wiz)
        assert caption == f"Step {number} of 6 · {C.step_name(screen)}"
        assert C.journey_step_announcement(wiz) == (
            f"Preparation, step {number} of 6: {C.step_name(screen)}.")
        seen[screen] = caption
    assert len(set(seen.values())) == len(MAIN)


def test_detours_opened_from_a_step_show_that_step():
    wiz = _at(Screen.CONFIRM)
    wiz.open_keyboard()
    assert wiz.screen == Screen.KEYBOARD
    assert C.journey_step_caption(wiz) == "Step 4 of 6 · Confirm its identity"
    wiz.back()
    assert wiz.screen == Screen.CONFIRM

    wiz = _at(Screen.OWNER)
    wiz.open_report_help()
    assert wiz.screen == Screen.REPORT_HELP
    assert C.journey_step_caption(wiz) == "Step 2 of 6 · Confirm ownership"

    wiz = _at(Screen.METHOD)
    wiz.open_advanced()
    assert wiz.screen == Screen.ADVANCED
    assert C.journey_step_caption(wiz) == "Step 5 of 6 · Choose a method"
    wiz.open_report_help()
    assert C.journey_step_caption(wiz) == "Step 5 of 6 · Choose a method"

    wiz = _at(Screen.PICK)
    wiz.open_disk_help()
    assert wiz.screen == Screen.DISK_HELP
    assert C.journey_step_caption(wiz) == "Step 3 of 6 · Choose a disk"


@pytest.mark.parametrize("scenario,screen", [("empty", Screen.PICK_EMPTY), ("blocked", Screen.PICK_BLOCKED)])
def test_no_disk_variants_count_as_the_choose_a_disk_step(scenario, screen):
    wiz = make_demo_wizard(scenario=scenario)
    wiz.skip_intro()
    if wiz.screen == Screen.OWNER:
        wiz.set_owner(True)
        wiz.continue_owner()
    assert wiz.screen == screen
    assert C.journey_step_caption(wiz) == "Step 3 of 6 · Choose a disk"


def test_erase_and_result_keep_their_stage_names():
    wiz = make_demo_wizard()
    wiz.screen = Screen.WORKING
    assert C.journey_step_caption(wiz) == "Erase"
    assert C.journey_step_announcement(wiz) == "Erase."
    wiz.screen = Screen.DONE
    assert C.journey_step_caption(wiz) == "Result"
    assert C.journey_step_announcement(wiz) == "Result."
    wiz.screen = Screen.SPLASH
    assert C.journey_step_caption(wiz) == ""


# --- One set of names: roadmap (#138) and step bar -----------------------------


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_roadmap_and_step_bar_share_the_same_names(code):
    lang.set_language(code)
    names = [C.step_name(screen) for screen in PREPARATION_PATH]
    assert len(set(names)) == len(names) and all(names)
    roadmap = C.splash_roadmap(PREPARATION_PATH)
    assert roadmap.split(C._ROADMAP_ARROW) == names[2:]
    for number, screen in enumerate(PREPARATION_PATH, 1):
        caption = C.STEP_CAPTION.format(n=number, total=6, name=C.step_name(screen))
        assert str(number) in caption and "6" in caption and C.step_name(screen) in caption
        spoken = C.STEP_SPOKEN.format(stage=C.JOURNEY_LABELS[0], n=number, total=6,
                                      name=C.step_name(screen))
        assert spoken.startswith(C.JOURNEY_LABELS[0]) and C.step_name(screen) in spoken
    if code != "en":
        assert C.step_name(Screen.PICK) != "Choose a disk"


def test_english_roadmap_keeps_the_start_screen_wording_and_adds_method():
    assert C.splash_roadmap(PREPARATION_PATH) == (
        "Choose a disk  →  Confirm its identity  →  Choose a method  →  Review and erase")


# --- Console and web preview show the same text -----------------------------------


def test_console_header_shows_the_same_step_line():
    from beamo_wipe.ui import console_wizard as console

    for screen in MAIN:
        wiz = _at(screen)
        line = " ".join(console._chrome_lines(wiz, 100))
        assert C.journey_step_caption(wiz) in line
        # Narrow terminals keep "Step N of 6" before dropping the step.
        short = console._chrome_lines(wiz, len(f"{C.APP_NAME} — Step 1 of 6 — {console._screen_title(wiz)}") + 2)
        assert C.journey_step_short(wiz) in " ".join(short)


def test_web_preview_uses_the_wizard_step_captions():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    payload = json.loads(re.search(r"const P = (\{.*?\});\n", html, re.S).group(1))
    captions = payload["stepCaptions"]
    assert captions["pick"] == captions["empty"] == captions["blocked"] == captions["disk_help"]
    assert captions["method"] == captions["advanced"] == captions["limits"]
    assert captions["last"] == "Step 6 of 6 · Review and erase"
    assert [captions[k] for k in ("keyboard", "owner", "pick", "confirm", "method", "last")] == [
        C.STEP_CAPTION.format(n=n, total=6, name=C.step_name(s)) for n, s in enumerate(MAIN, 1)]
    assert payload["stepParts"]["pick"] == pytest.approx(0.5)
    assert payload["splashRoadmap"] == C.splash_roadmap(PREPARATION_PATH)
    assert 'const stepKey = screen === "report_help" ? reportHelpFrom : screen;' in html


# --- Rendered Tk header ---------------------------------------------------------


def _header_texts(app):
    header = app._header
    return [(str(header.itemcget(item, "text")), header.bbox(item))
            for item in header.find_all() if header.type(item) == "text"]


@pytest.mark.parametrize("text_size", ["standard", "large", "extra"])
@pytest.mark.parametrize("size", [(800, 600), (1280, 820)], ids=lambda s: f"{s[0]}x{s[1]}")
def test_tk_header_names_each_step_whole(ui, size, text_size):  # noqa: F811
    from test_tk_runtime import _drive_to

    shown = []
    screens = [Screen.KEYBOARD, Screen.OWNER, Screen.PICK, Screen.CONFIRM,
               Screen.METHOD, Screen.ADVANCED, Screen.LAST_CHANCE]
    if _windows_review_loop(size, text_size):
        screens.remove(Screen.LAST_CHANCE)
    for screen in screens:
        wiz, app = ui(size=size)
        if text_size != "standard":
            assert wiz.set_text_size(text_size)
            app._sync_layout()
        _drive_to(wiz, app, screen, size=size)
        assert wiz.screen == screen
        app._draw_header()
        texts = _header_texts(app)
        caption = C.journey_step_caption(wiz)
        boxes = [box for text, box in texts if text == caption]
        assert len(boxes) == 1, (screen, [text for text, _ in texts])
        x0, y0, x1, y1 = boxes[0]
        assert 0 <= x0 < x1 <= app._header.winfo_width()
        assert 0 <= y0 < y1 <= app._header.winfo_height()
        # Clear of the brand and of every stage name beside it.
        for text, (bx0, _by0, bx1, _by1) in texts:
            if text != caption:
                assert bx1 <= x0 or bx0 >= x1, (screen, text, caption)
        shown.append(caption)
        assert not wiz.runner.started
    # Keyboard, ownership, pick, confirm, method and review each read
    # differently; Advanced is a detour that names the Method step.
    main = shown[:5] + shown[6:]
    assert len(set(main)) == len(main)
    assert shown[5] == shown[4]


def _windows_review_loop(size, text_size) -> bool:
    # Windows Tk only: Review's idle layout pass never settles at 800x600
    # with the extra text size (pre-existing, also on the #128 baseline).
    # Linux CI runs this case.
    return sys.platform == "win32" and size[0] < 1000 and text_size == "extra"


@pytest.mark.parametrize("code", ["fr", "de", "es", "it"])
@pytest.mark.parametrize("text_size", ["standard", "extra"])
def test_tk_long_translations_fit_at_800x600(ui, code, text_size):  # noqa: F811
    from test_tk_runtime import _drive_to

    screens = [Screen.CONFIRM, Screen.LAST_CHANCE]
    if _windows_review_loop((800, 600), text_size):
        screens.remove(Screen.LAST_CHANCE)
    for screen in screens:
        wiz, app = ui(size=(800, 600))
        wiz.set_language(code)
        if text_size != "standard":
            assert wiz.set_text_size(text_size)
            app._sync_layout()
        _drive_to(wiz, app, screen, size=(800, 600))
        app._draw_header()
        texts = [text for text, _ in _header_texts(app)]
        full, short = C.journey_step_caption(wiz), C.journey_step_short(wiz)
        # The whole caption, or the shortened "Step N of 6"; never a cut word.
        assert full in texts or short in texts, texts
        for text in texts:
            assert text in (C.APP_NAME, full, short) or text in C.JOURNEY_LABELS, text
        lang.set_language("en")


def test_tk_strip_fills_the_preparation_segment_step_by_step(ui):  # noqa: F811
    from test_tk_runtime import _drive_to

    fills = []
    for screen in MAIN[:-1]:
        wiz, app = ui(size=(1280, 820))
        _drive_to(wiz, app, screen, size=(1280, 820))
        app._draw_strip()
        strip = app._strip
        accent = [strip.bbox(item) for item in strip.find_all()
                  if strip.itemcget(item, "fill") == C_ACCENT()]
        assert len(accent) == 1
        fills.append(accent[0][2] - accent[0][0])
    assert fills == sorted(fills) and len(set(fills)) == len(fills)


def C_ACCENT():
    from beamo_wipe.ui import tk_wizard as tkui

    return tkui.ACCENT


from test_tk_runtime import ui  # noqa: E402,F401  (fixture)
