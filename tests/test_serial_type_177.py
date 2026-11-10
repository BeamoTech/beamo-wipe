# SPDX-License-Identifier: GPL-3.0-or-later
"""#177: serial numbers in regular weight; highlights stay bold.

The bold monospace serial looked heavy. Serials are now regular weight in
DejaVu Sans Mono (the live image's monospace: dotted 0, flagged and
footed 1, tailed l, serifed I). The #129 confirmation characters and the
#152 differing characters are still drawn bold over it, so they stand out
more than before. GTK and the web preview add slight letter spacing (Pango
letter_spacing, CSS letter-spacing); Tk has no letter-spacing option, so
Tk draws each character in its own cell with a small gap (#177g,
test_serial_tracking_177g). Fake disks only.
"""

from __future__ import annotations

import pathlib

import pytest

from beamo_wipe import lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import MethodId

ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _wizard(name):
    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    wiz.select_disk("/dev/sda")
    if name == "pick":
        return wiz
    wiz.continue_pick()
    if name == "confirm":
        return wiz
    wiz.set_confirm_input(wiz.confirm.token)
    wiz.continue_confirm()
    wiz.set_method(MethodId.EXTRA)
    return wiz


def _walk(widget):
    yield widget
    for child in widget.winfo_children():
        yield from _walk(child)


def _tk(wiz, size, text_size="standard"):
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    wiz.text_size = text_size
    app = TkWizard(wiz)
    app.root.geometry(f"{size[0]}x{size[1]}+20+20")
    app._draw()
    for _ in range(8):
        app.root.update()
    return app


def _weight(app, widget):
    import tkinter.font as tkfont

    return tkfont.Font(root=app.root, font=widget.cget("font")).actual("weight")


@pytest.mark.parametrize("size,text_size", [((800, 600), "standard"), ((1280, 820), "extra")])
def test_serial_is_regular_and_fits(size, text_size):
    from test_tk_runtime import _clipping_problems

    wiz = _wizard("method")
    app = _tk(wiz, size, text_size)
    try:
        serials = [w for w in _walk(app._body) if getattr(w, "_beamo_serial", False)]
        assert serials
        for label in serials:
            assert _weight(app, label) == "normal"
            assert wiz.selected.serial in str(label.cget("text")).replace("\n", "")
        assert not _clipping_problems(app)
    finally:
        app._teardown()


def test_confirmation_characters_stay_bold_over_the_regular_serial():
    import tkinter.font as tkfont

    wiz = _wizard("confirm")
    app = _tk(wiz, (1280, 820))
    try:
        (serial,) = [w for w in _walk(app._body) if getattr(w, "_beamo_serial", False)]
        assert _weight(app, serial) == "normal"
        face = serial._beamo_serial_face  # #177g: one canvas item per character
        view = wiz.disk_view(wiz.selected)
        assert face.drawn_text() == view.id_value
        for i in range(len(view.id_value)):
            item = face.find_withtag(f"ch{i}")[0]
            font = tkfont.Font(root=app.root, font=face.itemcget(item, "font"))
            want = "bold" if view.token_start <= i < view.token_end else "normal"
            assert font.actual("weight") == want
    finally:
        app._teardown()


def test_live_font_is_dejavu_sans_mono_first():
    import inspect

    from beamo_wipe.ui import tk_wizard as tkui

    source = inspect.getsource(tkui._mono_family)
    assert source.index('"DejaVu Sans Mono"') < source.index('"Liberation Mono"')
    lists = (ROOT / "packaging/live/config/package-lists").glob("*.list*")
    assert any("fonts-dejavu-core" in p.read_text(encoding="utf-8") for p in lists)


def test_gtk_serial_is_monospace_regular_and_spaced():
    src = (ROOT / "src/beamo_wipe/ui/accessible_wizard.py").read_text(encoding="utf-8")
    assert 'SERIAL_SPAN = \'<span font_family="monospace" weight="normal" letter_spacing="768">\'' in src
    assert "self._mark_token(widget, view, token=marked)" in src
    block = src[src.index("    def _mark_token(self, widget, view"):src.index("    def reader(self")]
    # The confirmation characters stay bold and double-underlined inside it.
    assert 'underline="double" weight="bold"' in block and "SERIAL_SPAN + value" in block


def test_web_preview_serial_is_regular_and_spaced():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    assert ".card .meta .mono.ser { font-weight: 400; letter-spacing: .06em; }" in html
    assert "b.diff { font-weight: 700" in html  # #152 marks stay bold
