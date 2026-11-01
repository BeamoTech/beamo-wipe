# SPDX-License-Identifier: GPL-3.0-or-later
"""Rendered GTK screen-reader view at 800x600: method choices, pick-row
contents hints and the preview notice. Fake disks only, never nwipe."""

from __future__ import annotations

from dataclasses import replace

import pytest

pytest.importorskip("gi")
from beamo_wipe import copy as C  # noqa: E402
from beamo_wipe import lang  # noqa: E402
from beamo_wipe.demo import make_demo_wizard  # noqa: E402
from beamo_wipe.lang import LANGUAGE_NAMES  # noqa: E402
from beamo_wipe.models import (  # noqa: E402
    CONTENTS_DATA,
    CONTENTS_SYSTEM,
    CONTENTS_UNKNOWN,
    CONTENTS_WINDOWS,
    Screen,
)
from beamo_wipe.ui.accessible_wizard import AccessibleWizard, Gtk  # noqa: E402
from test_accessible_runtime import drain, wait_for_window_size, widgets  # noqa: E402

CONTENTS = {
    "/dev/nvme0n1": CONTENTS_WINDOWS,
    "/dev/sda": CONTENTS_DATA,
    "/dev/sdd": CONTENTS_SYSTEM,
}


@pytest.fixture(autouse=True)
def _english_after():
    yield
    lang.set_language("en")


@pytest.fixture
def gtk():
    apps = []

    def build(wizard, size=(800, 600)):
        app = AccessibleWizard(wizard)
        apps.append(app)
        app.window.resize(*size)
        wait_for_window_size(app.window, size)
        drain()
        return app

    yield build
    for app in apps:
        app.close()
    drain()


def _wizard(code="en", *, preview=True, contents=None, text_size="standard"):
    lang.set_language("en")
    wizard = make_demo_wizard()
    wizard.preview = preview
    wizard.set_language(code)
    wizard.set_text_size(text_size)
    if contents:
        def tag(disk):
            if disk.is_boot:
                return disk
            return replace(disk, contents=contents.get(disk.path, disk.contents))

        wizard.discovery = replace(
            wizard.discovery,
            disks=tuple(map(tag, wizard.discovery.disks)),
            selectable=tuple(map(tag, wizard.discovery.selectable)),
        )
    return wizard


def _to_method(wizard, path):
    wizard.skip_intro()
    wizard.set_owner(True)
    wizard.continue_owner()
    wizard.select_disk(path)
    wizard.continue_pick()
    wizard.set_confirm_input(wizard.confirm.token)
    wizard.continue_confirm()
    assert wizard.screen == Screen.METHOD


def _window_y(app, widget):
    return widget.translate_coordinates(app.window, 0, 0)[1]


@pytest.mark.parametrize("preview", [False, True], ids=["live", "preview"])
@pytest.mark.parametrize("path", ["/dev/nvme0n1", "/dev/sda"])
@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_every_method_choice_is_above_the_footer_at_800x600(gtk, code, path, preview):
    wizard = _wizard(code, preview=preview)
    _to_method(wizard, path)
    app = gtk(wizard)
    footer = _window_y(app, app.footer)
    radios = [w for w in widgets(app.body) if isinstance(w, Gtk.RadioButton)]
    assert len(radios) == 3
    for radio in radios:
        top = _window_y(app, radio)
        assert top >= 0
        assert top + radio.get_allocated_height() <= footer, (code, path, top, footer)
    # The general limits remain on the screen as the next Tab stop.
    notice = f"{C.SEVERITY_LIMITS}: {wizard.storage_notice}"
    labels = [w for w in widgets(app.body) if isinstance(w, Gtk.Label) and w.get_text() == notice]
    assert len(labels) == 1 and labels[0].get_can_focus()
    assert not wizard.runner.started


@pytest.mark.parametrize("code", ["en", "de"])
def test_focused_method_choice_scrolls_into_view_with_extra_large_text(gtk, code):
    wizard = _wizard(code, text_size="extra")
    _to_method(wizard, "/dev/sda")
    app = gtk(wizard)
    radios = [w for w in widgets(app.body) if isinstance(w, Gtk.RadioButton)]
    for radio in radios:
        radio.grab_focus()
        for _ in range(20):
            drain()
        top = _window_y(app, radio)
        assert top >= 0
        assert top + radio.get_allocated_height() <= _window_y(app, app.footer)
    assert not wizard.runner.started


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_pick_rows_speak_and_show_what_each_disk_holds(gtk, code):
    wizard = _wizard(code, contents=CONTENTS)
    wizard.skip_intro()
    wizard.set_owner(True)
    wizard.continue_owner()
    assert wizard.screen == Screen.PICK
    app = gtk(wizard)
    shown = [w.get_text() for w in widgets(app.body) if isinstance(w, Gtk.Label)]
    expected = {
        CONTENTS_WINDOWS: C.CONTENTS_HINT_WINDOWS,
        CONTENTS_SYSTEM: C.CONTENTS_HINT_SYSTEM,
        CONTENTS_DATA: "",
    }
    for disk in wizard.selectable:
        key = C.ACCESSIBLE_SELECT_DISK.format(disk=wizard.disk_view(disk).announcement)
        # The action word is the owner's language too, not English "Select".
        assert key.startswith("Select ") == (code == "en")
        hint = expected[CONTENTS[disk.path]]
        name = app.actions[key].get_accessible().get_name()
        if hint:
            assert name == f"{key}. {hint}"
            assert shown.count(hint) == 1
        else:  # no recognised system: nothing is claimed, by ear either
            assert name == key
    # One label per recognised disk; the data disk adds none.
    assert sum(shown.count(hint) for hint in set(expected.values()) - {""}) == 2
    assert wizard.selected is None and not wizard.runner.started


def test_unknown_contents_keep_the_plain_select_name(gtk):
    wizard = _wizard(contents={path: CONTENTS_UNKNOWN for path in CONTENTS})
    wizard.skip_intro()
    wizard.set_owner(True)
    wizard.continue_owner()
    app = gtk(wizard)
    for disk in wizard.selectable:
        key = C.ACCESSIBLE_SELECT_DISK.format(disk=wizard.disk_view(disk).announcement)
        assert app.actions[key].get_accessible().get_name() == key


@pytest.mark.parametrize("code", [c for c in lang.LANGUAGE_ORDER if c != "en"])
def test_preview_notice_follows_the_language_choice(gtk, code):
    wizard = _wizard(preview=True)
    wizard.skip_splash()
    assert wizard.screen == Screen.KEYBOARD
    app = gtk(wizard)
    app.actions[f"{LANGUAGE_NAMES[code]} ({C.ACCESSIBLE_NOT_SELECTED})"].clicked()
    drain()
    assert wizard.language == code
    notices = [
        w.get_text() for w in widgets(app.body)
        if isinstance(w, Gtk.Label) and w.get_style_context().has_class("preview-notice")
    ]
    assert notices == [C.PREVIEW_BANNER]
    # Orca reads the window title: it follows the language too.
    assert app.window.get_title() == C.ACCESSIBLE_TITLE
    assert app.window.get_title() != lang.english("copy", "ACCESSIBLE_TITLE")
