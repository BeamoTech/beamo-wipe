# SPDX-License-Identifier: GPL-3.0-or-later
"""Method time guide in the screen-reader (GTK) and console views.

Fake disks only. GTK cases need gi and a private display; console cases use
fake terminals and never start the engine.
"""

from __future__ import annotations

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.methods import METHODS
from beamo_wipe.models import MethodId, Screen
from beamo_wipe.ui import console_wizard


@pytest.fixture(autouse=True)
def _english_after():
    yield
    lang.set_language("en")


def _method_wizard(path="/dev/sda", code="en"):
    wiz = make_demo_wizard()
    wiz.set_language(code)
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    wiz.select_disk(path)
    wiz.continue_pick()
    wiz.set_confirm_input(wiz.confirm.token)
    wiz.continue_confirm()
    assert wiz.screen == Screen.METHOD
    return wiz


@pytest.mark.parametrize("code", ["en", "de"])
def test_plain_console_prints_each_guide_with_its_method(monkeypatch, capsys, code):
    wiz = _method_wizard(code=code)

    def stop(_prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", stop)
    console_wizard._plain_loop(wiz)
    out = capsys.readouterr().out
    lines = out.splitlines()
    for method, spec in METHODS.items():
        guide = C.method_time_guide(method, wiz.selected)
        assert guide
        (line,) = [ln for ln in lines if ln.startswith(f"{C.METHOD_CARDS[method]['key']} {spec.title}")]
        assert spec.description in line and guide in line


def _curses_text(wiz, rows, cols):
    seen = {}

    class Terminal:
        def getmaxyx(self):
            return (rows, cols)

        def addstr(self, y, x, text, attr=0):
            assert y < rows and len(text) < cols
            seen[y] = text

        def getch(self):
            wiz.wants_shutdown = True
            return ord("q")

        def __getattr__(self, name):
            return lambda *args: None

    console_wizard._loop(Terminal(), wiz)
    return " ".join(seen[y] for y in sorted(seen))


def test_curses_shows_guides_after_the_methods(monkeypatch):
    monkeypatch.setattr(console_wizard.curses, "curs_set", lambda *a: None, raising=False)
    monkeypatch.setattr(console_wizard.curses, "use_default_colors", lambda: None, raising=False)
    wiz = _method_wizard()
    text = " ".join(_curses_text(wiz, 60, 120).split())
    for method, spec in METHODS.items():
        assert spec.description in text
        guide = C.method_time_guide(method, wiz.selected)
        assert f"{spec.title}: {guide}" in text
    # The 80x25 first page still shows every method description first.
    wiz.wants_shutdown = False
    small = " ".join(_curses_text(wiz, 25, 80).split())
    for spec in METHODS.values():
        assert spec.description in small


@pytest.mark.parametrize(
    "code,path",
    [("en", "/dev/nvme0n1"), ("en", "/dev/sda"), ("de", "/dev/sda")],
)
def test_gtk_radio_names_carry_the_guide_for_orca(code, path):
    pytest.importorskip("gi")
    from test_accessible_runtime import drain, text, wait_for_window_size, widgets

    from beamo_wipe.ui.accessible_wizard import AccessibleWizard, Gtk

    wiz = _method_wizard(path, code=code)
    app = AccessibleWizard(wiz)
    try:
        app.window.resize(800, 600)
        wait_for_window_size(app.window, (800, 600))
        choices = [w for w in widgets(app.body) if isinstance(w, Gtk.RadioButton)]
        assert len(choices) == len(METHODS)
        shown = text(app)
        last_choice = max(
            c.translate_coordinates(app.window, 0, 0)[1] + c.get_allocated_height()
            for c in choices
        )
        for choice, (method, spec) in zip(choices, METHODS.items()):
            name = choice.get_accessible().get_name() or ""
            guide = C.method_time_guide(method, wiz.selected)
            # Label in name: the visible label starts the spoken name.
            assert guide and name.startswith(choice.get_label())
            assert spec.summary in name and name.endswith(guide)
            assert guide not in choice.get_label()
            assert (choice.get_accessible().get_description() or "") == spec.plain_lead
            # The visible guide follows the choices; it never pushes them down.
            visible = f"{spec.title}: {guide}"
            assert visible in shown
            (label,) = [
                w for w in widgets(app.body)
                if isinstance(w, Gtk.Label) and w.get_text() == visible
            ]
            assert label.translate_coordinates(app.window, 0, 0)[1] >= last_choice
        if (code, path) == ("en", "/dev/nvme0n1"):
            # Same 800x600 guarantee as the existing method-screen test.
            footer_y = app.footer.translate_coordinates(app.window, 0, 0)[1]
            assert last_choice <= footer_y
    finally:
        app.close()
        drain()


def test_guide_follows_the_selected_disk():
    hdd = _method_wizard("/dev/sda")
    nvme = _method_wizard("/dev/nvme0n1")
    assert "hard disk" in C.method_time_guide(MethodId.EVERYDAY, hdd.selected)
    assert "SSD" in C.method_time_guide(MethodId.EVERYDAY, nvme.selected)
