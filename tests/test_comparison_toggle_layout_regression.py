"""The collapsed comparison control stays readable when its title fits."""

import pytest

from beamo_wipe import inventory, lang
from beamo_wipe.models import Screen
from beamo_wipe.ui.tk_wizard import _CheckRow
from test_tk_runtime import descendants
from test_tk_runtime import ui as ui


@pytest.mark.parametrize("code", ["en", "fr", "de", "es", "it"])
@pytest.mark.parametrize("size", [(800, 600), (1280, 820), (1600, 1000)])
def test_comparison_title_uses_available_width_without_midword_breaks(request, code, size):
    try:
        wizard, app = request.getfixturevalue("ui")(size=size)
        wizard.set_language(code)
        wizard.screen = Screen.PICK
        app._draw()
        app.root.update_idletasks()
        row = next(
            widget for widget in descendants(app.root)
            if isinstance(widget, _CheckRow) and widget.cget("text") == inventory.COMPARE_TITLE
        )
        label = row._label
        text_width = app.font_s_bold.measure(inventory.COMPARE_TITLE)
        assert row.master.winfo_width() > text_width + 60
        assert label.winfo_width() >= text_width
        assert label.winfo_height() <= app.font_s_bold.metrics("linespace") + 8
    finally:
        lang.set_language("en")
