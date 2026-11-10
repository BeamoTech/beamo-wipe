# SPDX-License-Identifier: GPL-3.0-or-later
"""Header texts never overlap: a long sub-page caption yields to the stages.

At 1000-1100 px the right-aligned caption ("Límites de almacenamiento
admitidos") ran over the third stage name. Fake disks only."""

from __future__ import annotations

import pytest

from beamo_wipe import lang
from beamo_wipe.models import Screen

from test_tk_runtime import _drive_to
from test_ui_fit_20261027 import _settle, tk_app  # noqa: F401 - fixture

SCREENS = (Screen.LIMITS, Screen.ADVANCED, Screen.DISK_HELP, Screen.PICK, Screen.METHOD)


def _header_texts(app):
    canvas = app._header
    items = [item for item in canvas.find_all() if canvas.type(item) == "text"]
    return [(canvas.itemcget(item, "text"), canvas.bbox(item)) for item in items]


def _open(wiz, app, screen):
    if screen in (Screen.LIMITS, Screen.METHOD):
        _drive_to(wiz, app, Screen.METHOD)
        if screen == Screen.LIMITS:
            wiz.open_limits()
    elif screen == Screen.DISK_HELP:
        _drive_to(wiz, app, Screen.PICK)
        wiz.open_disk_help()
    else:
        _drive_to(wiz, app, screen)


@pytest.mark.parametrize("width", [1000, 1024, 1100, 1280])
@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
@pytest.mark.parametrize("screen", SCREENS, ids=lambda s: s.value)
def test_header_texts_never_overlap(tk_app, code, width, screen):  # noqa: F811
    wiz, app = tk_app(size=(width, 740), code=code)
    _open(wiz, app, screen)
    assert wiz.screen == screen
    app._draw()
    _settle(app, 50)
    texts = _header_texts(app)
    assert texts
    for index, (text_a, (ax0, ay0, ax1, ay1)) in enumerate(texts):
        assert ax1 <= app._header.winfo_width(), (text_a, width)
        for text_b, (bx0, by0, bx1, by1) in texts[index + 1:]:
            overlap = ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1
            assert not overlap, (code, width, screen, text_a, text_b)
