# SPDX-License-Identifier: GPL-3.0-or-later
"""#128: each screen carries exactly one destructive-action warning.

Owner says once what the tool does. Confirm has one box naming the selected
disk ("Everything on <model, size> will be erased. You cannot get it back.").
Review keeps only its red callout, which adds the serial or hardware ID and
stays above the fold. The sentences are shared copy strings, so Tk, the
GTK/Orca view, both console modes and the --web gallery cannot drift.

The rendered counts use English phrase patterns that also match the
pre-#128 wording, so a reintroduced duplicate line fails here.

Fake disks only (make_demo_wizard, DryRunRunner); nothing is erased.
"""

from __future__ import annotations

import json
import re
from dataclasses import replace

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.gallery import gallery_html
from beamo_wipe.identity import display_title, present_disk
from beamo_wipe.models import (
    CONTENTS_DATA,
    CONTENTS_SYSTEM,
    CONTENTS_UNKNOWN,
    CONTENTS_WINDOWS,
    Screen,
)
from beamo_wipe.ui import console_wizard as console
from beamo_wipe.wizard import Wizard
from test_ui_fit_20261027 import tk_app  # noqa: F401  (fixture)

# Sentences that say data on the target will be destroyed, old and new.
DESTROY = re.compile(
    r"will be erased|\bwill erase\b|erases everything|removes every file"
    r"|erasing (?:it|this selected disk) (?:also |still )?removes",
    re.IGNORECASE,
)
UNDO = re.compile(r"cannot get (?:it|them|the files) back", re.IGNORECASE)
# (destroy sentences, irreversibility sentences) on each screen.
EXPECTED = {
    Screen.OWNER: (1, 0),
    Screen.CONFIRM: (1, 1),
    Screen.LAST_CHANCE: (1, 1),
}
SCREENS = tuple(EXPECTED)
CONTENTS = (CONTENTS_WINDOWS, CONTENTS_SYSTEM, CONTENTS_DATA, CONTENTS_UNKNOWN)
RETIRED = (
    "PREPARE_WINDOWS",
    "PREPARE_SYSTEM",
    "PREPARE_DATA",
    "PREPARE_UNKNOWN",
    "CONFIRM_WARNING_TEXT",
    "ERASE_NOW_TEXT",
)


def warning_counts(text: str) -> tuple[int, int]:
    flat = " ".join(text.split())
    return len(DESTROY.findall(flat)), len(UNDO.findall(flat))


def _wizard_at(screen: Screen, contents: str = CONTENTS_WINDOWS) -> Wizard:
    wiz = make_demo_wizard()
    wiz.skip_intro()
    if screen == Screen.OWNER:
        return wiz
    wiz.accept_what()
    wiz.set_owner(True)
    wiz.continue_owner()
    disk = sorted(wiz.selectable, key=lambda d: d.path)[0]
    wiz.select_disk(disk.path)
    wiz.selected = replace(wiz.selected, contents=contents)
    wiz.continue_pick()
    wiz.set_confirm_input(wiz.confirm.token)
    if screen == Screen.CONFIRM:
        return wiz
    wiz.continue_confirm()
    wiz.continue_method()
    assert wiz.screen == Screen.LAST_CHANCE
    return wiz


@pytest.fixture
def english():
    lang.set_language("en")
    yield
    lang.set_language("en")


# --- one shared source -----------------------------------------------------


def test_retired_duplicate_strings_are_gone_everywhere():
    for name in RETIRED:
        assert not hasattr(C, name), name
        for code in lang.LANGUAGE_ORDER:
            if code != "en":
                assert name not in set(lang.keys(code, "copy")), (code, name)
    assert not hasattr(C, "prepare_selected")
    assert not hasattr(Wizard, "prepare_text")


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
@pytest.mark.parametrize("contents", CONTENTS)
def test_confirm_and_review_share_one_sentence_in_every_language(code, contents):
    lang.set_language(code)
    try:
        wiz = make_demo_wizard()
        disk = replace(sorted(wiz.selectable, key=lambda d: d.path)[0], contents=contents)
        view = present_disk(disk, wiz.listed_disks)
        template = {
            CONTENTS_WINDOWS: C.ERASE_EVERYTHING_WINDOWS,
            CONTENTS_SYSTEM: C.ERASE_EVERYTHING_SYSTEM,
        }.get(contents, C.ERASE_EVERYTHING)
        assert template.count("{disk}") == 1
        confirm = C.confirm_warning(disk)
        review = C.erase_now_label(disk, wiz.listed_disks)
        assert confirm == (
            template.format(disk=f"{display_title(disk)}, {disk.size_phrase}")
            + " " + C.ERASE_CANNOT_UNDO
        )
        assert review == (
            template.format(disk=f"{view.title}, {view.capacity}, {view.id_value}")
            + " " + C.ERASE_CANNOT_UNDO
        )
        for text in (confirm, review):
            # Said once: one erase sentence, one "cannot get it back".
            assert text.count(C.ERASE_CANNOT_UNDO) == 1
            fixed = max(template.split("{disk}"), key=len)
            assert text.count(fixed) == 1
        assert disk.serial in review and disk.serial not in confirm
    finally:
        lang.set_language("en")


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_owner_says_what_the_tool_does_once(code):
    lang.set_language(code)
    try:
        assert len(C.WHAT_BULLETS) == 3
        assert all(C.ERASE_CANNOT_UNDO not in b for b in C.WHAT_BULLETS)
        assert C.WHAT_BULLETS[0].startswith("Beamo Wipe ")
        assert "Windows" in C.WHAT_BULLETS[0] and "Linux" in C.WHAT_BULLETS[0]
    finally:
        lang.set_language("en")


def test_english_owner_bullets_carry_one_erase_sentence(english):
    assert warning_counts(" ".join(C.WHAT_BULLETS)) == EXPECTED[Screen.OWNER]


@pytest.mark.parametrize("contents", CONTENTS)
def test_english_confirm_box_names_the_disk_and_keeps_cannot_get_it_back(english, contents):
    wiz = _wizard_at(Screen.CONFIRM, contents)
    text = wiz.warning_text()
    assert text.startswith(f"Everything on {display_title(wiz.selected)}, {wiz.selected.size_phrase} will be erased")
    assert text.endswith("You cannot get it back.")
    assert warning_counts(text) == (1, 1)
    assert ("including Windows" in text) == (contents == CONTENTS_WINDOWS)
    assert ("including its operating system" in text) == (contents == CONTENTS_SYSTEM)


# --- curses and plain console ------------------------------------------------


class _TallTerminal:
    """A fake curses screen tall enough to hold a whole screen in one frame."""

    def __init__(self, wizard):
        self.wizard = wizard
        self.h, self.w = 300, 80
        self.rows: dict[int, str] = {}
        self.frames: list[dict[int, str]] = []

    def getmaxyx(self):
        return self.h, self.w

    def addstr(self, y, x, text, attr=0):
        self.rows[y] = text if x == 0 else (" " * x + text)

    def erase(self):
        if self.rows:
            self.frames.append(dict(self.rows))
        self.rows = {}

    def getch(self):
        self.frames.append(dict(self.rows))
        self.wizard.wants_shutdown = True
        return -1

    def __getattr__(self, name):
        return lambda *a, **k: None


@pytest.mark.parametrize("contents", (CONTENTS_WINDOWS, CONTENTS_DATA))
@pytest.mark.parametrize("screen", SCREENS, ids=lambda s: s.name)
def test_curses_screen_shows_exactly_one_erase_warning(english, monkeypatch, screen, contents):
    wiz = _wizard_at(screen, contents)
    for name in ("curs_set", "use_default_colors", "echo", "noecho"):
        monkeypatch.setattr(console.curses, name, lambda *a, **k: None)
    term = _TallTerminal(wiz)
    console._loop(term, wiz)
    frame = term.frames[-1]
    shown = " ".join(frame[y] for y in sorted(frame))
    assert warning_counts(shown) == EXPECTED[screen], shown
    if screen != Screen.OWNER:
        # The warning is the only place the system on the disk is named.
        assert ("including Windows" in shown) == (contents == CONTENTS_WINDOWS)
    assert not wiz.runner.started


@pytest.mark.parametrize("screen", SCREENS, ids=lambda s: s.name)
def test_plain_console_screen_shows_exactly_one_erase_warning(english, monkeypatch, capsys, screen):
    wiz = _wizard_at(screen)
    monkeypatch.setattr("builtins.input", lambda *_: (_ for _ in ()).throw(EOFError()))
    console._plain_loop(wiz)
    shown = capsys.readouterr().out
    assert warning_counts(shown) == EXPECTED[screen], shown
    if screen != Screen.OWNER:
        flat = " ".join(shown.split())
        warning = wiz.warning_text() if screen == Screen.CONFIRM else wiz.erase_label()
        assert f"{C.SEVERITY_WARNING}: {warning}" in flat
    assert not wiz.runner.started


# --- --web gallery ---------------------------------------------------------------


def _gallery_payload() -> dict:
    html = gallery_html()
    match = re.search(r"const P = (\{.*?\});\n", html, re.S)
    assert match, "gallery payload"
    return json.loads(match.group(1))


def test_gallery_uses_the_shared_warnings_once_per_screen(english):
    html = gallery_html()
    payload = _gallery_payload()
    assert warning_counts(" ".join(payload["what"])) == EXPECTED[Screen.OWNER]
    disks = [d for d in payload["disks"] if not d["isBoot"]]
    assert disks
    for disk in disks:
        assert "prepare" not in disk
        assert warning_counts(disk["warning"]) == (1, 1)
        assert warning_counts(disk["eraseLabel"]) == (1, 1)
    # Confirm renders one warn panel; Review renders the red callout only.
    assert html.count("panel(\"warn\", d.warning)") == 1
    assert html.count("selected.eraseLabel") == 1
    assert "d.prepare" not in html and "selected.prepare" not in html


# --- Tk, the live graphical wizard -------------------------------------------------


def _tk_labels(app):
    from test_ui_fit_20261027 import _descendants

    return [
        w for w in _descendants(app._body)
        if w.winfo_class() == "Label" and w.winfo_ismapped() and str(w.cget("text")).strip()
    ]


@pytest.mark.parametrize("text_size", ("standard", "large", "extra"))
@pytest.mark.parametrize("size", ((800, 600), (1280, 820)), ids=lambda s: f"{s[0]}x{s[1]}")
@pytest.mark.parametrize("screen", SCREENS, ids=lambda s: s.name)
def test_tk_screen_shows_exactly_one_erase_warning(tk_app, screen, size, text_size):  # noqa: F811
    from test_tk_runtime import _drive_to
    from test_ui_fit_20261027 import _settle

    wiz, app = tk_app(size=size)
    first = sorted(wiz.selectable, key=lambda d: d.path)[0].path
    wiz.discovery = replace(
        wiz.discovery,
        disks=tuple(replace(d, contents=CONTENTS_WINDOWS) if d.path == first else d
                    for d in wiz.discovery.disks),
        selectable=tuple(replace(d, contents=CONTENTS_WINDOWS) if d.path == first else d
                         for d in wiz.discovery.selectable),
    )
    if text_size != "standard":
        assert wiz.set_text_size(text_size)
        app._sync_layout()
    _drive_to(wiz, app, screen, size=size)
    _settle(app, 50)
    shown = "\n".join(str(w.cget("text")) for w in _tk_labels(app))
    assert warning_counts(shown) == EXPECTED[screen], shown
    assert not wiz.runner.started


def _review_callout_is_above_the_fold(app, wiz):
    from beamo_wipe.ui import tk_wizard as tkui
    from test_ui_fit_20261027 import _extent

    text = f"{C.SEVERITY_WARNING}: {wiz.erase_label()}"
    labels = _tk_labels(app)
    warnings = [w for w in labels if str(w.cget("text")) == text]
    assert len(warnings) == 1
    warning = warnings[0]
    # The most prominent element: bold red text in the red callout, and no
    # other red text competes with it while there is no error.
    assert warning.cget("fg") == tkui.DANGER
    assert "bold" in str(app.root.tk.call("font", "actual", warning.cget("font"), "-weight"))
    assert [w for w in labels if w.cget("fg") == tkui.DANGER] == [warning]
    view = app._body_canvas
    if view is not None:
        assert view.canvasy(0) == 0
    else:
        view = app._body
    top, bottom = _extent(warning, view)
    assert 0 <= top and bottom <= view.winfo_height(), (top, bottom, view.winfo_height())
    # It precedes the countdown, and Erase now is still not available.
    assert app._countdown_ring.winfo_rooty() >= warning.winfo_rooty() + warning.winfo_height()
    assert not wiz.erase_enabled


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
@pytest.mark.parametrize("text_size", ("standard", "large", "extra"))
def test_tk_review_callout_stays_above_the_fold_at_800x600(tk_app, code, text_size):  # noqa: F811
    from test_tk_runtime import _drive_to
    from test_ui_fit_20261027 import _settle

    # The Windows sentence is the longest form of the warning.
    first = sorted(make_demo_wizard().selectable, key=lambda d: d.path)[0].path
    wiz, app = tk_app(size=(800, 600), code=code, contents={first: CONTENTS_WINDOWS})
    if text_size != "standard":
        assert wiz.set_text_size(text_size)
        app._sync_layout()
    _drive_to(wiz, app, Screen.LAST_CHANCE, size=(800, 600))
    _settle(app, 50)
    _review_callout_is_above_the_fold(app, wiz)
    assert not wiz.runner.started
