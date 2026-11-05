# SPDX-License-Identifier: GPL-3.0-or-later
"""#167: Working says when it started and when to come back, in large text.

The live USB's wall clock is not trusted (evidence records it as
"unverified"), so the line normally reads "Started 12 minutes ago · about 50
minutes left". Clock times ("Started 2:02 PM · expected around 3:05 PM")
appear only when the view's clock is trusted. The second part is the
validated, cautious estimate (finish rounded up to 5 minutes) and is left
out when there is none. Fake data only; nothing starts.
"""

from __future__ import annotations

import datetime
import json
import re

import pytest

from beamo_wipe import lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.progress import ProgressView

NOW = datetime.datetime(2026, 11, 5, 14, 14, 0).timestamp()  # local 2:14 PM


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def view(elapsed=720.0, remaining=3000.0, trusted=False, wall=NOW):
    return ProgressView("Writing", 19.0, elapsed, remaining, wall_now=wall, wall_trusted=trusted)


def test_untrusted_clock_uses_elapsed_and_time_left():
    assert view().glance_time == "Started 12 minutes ago · about 50 minutes left"
    assert view(remaining=None).glance_time == "Started 12 minutes ago"
    assert view(remaining=30).glance_time == "Started 12 minutes ago · less than 1 minute left"
    assert view(elapsed=30, remaining=None).glance_time == "Started less than 1 minute ago"


def test_trusted_clock_uses_times_of_day_and_a_cautious_finish():
    assert view(trusted=True).glance_time == "Started 2:02 PM · expected around 3:05 PM"
    assert view(trusted=True, remaining=None).glance_time == "Started 2:02 PM"
    # A finish exactly on a 5-minute mark stays there; anything after rounds up.
    assert view(trusted=True, remaining=46 * 60).glance_time.endswith("around 3:00 PM")
    assert view(trusted=True, remaining=46 * 60 + 1).glance_time.endswith("around 3:05 PM")


def test_unknown_or_broken_clock_hides_what_it_cannot_say():
    assert view(elapsed=None, remaining=None).glance_time == ""
    assert view(elapsed=None).glance_time == "About 50 minutes left"
    # Trusted but no usable wall time: fall back to the relative wording.
    assert view(trusted=True, wall=None).glance_time.startswith("Started 12 minutes ago")
    assert view(trusted=True, wall=float("nan")).glance_time.startswith("Started 12 minutes ago")


def test_no_elapsed_note_beside_the_new_line():
    assert not any(n.startswith("Elapsed") for n in view().glance_notes)


def test_language_formats():
    lang.set_language("de")
    assert view().glance_time == "Vor 12 Minuten gestartet · noch etwa 50 Minuten"
    assert view(trusted=True).glance_time == "Gestartet um 14:02 · voraussichtlich fertig gegen 15:05"
    lang.set_language("fr")
    assert view(trusted=True).glance_time == "Commencé à 14:02 · fin prévue vers 15:05"
    for code in lang.LANGUAGE_ORDER:
        lang.set_language(code)
        for v in (view(), view(trusted=True), view(remaining=None), view(remaining=30)):
            assert "{" not in v.glance_time and v.glance_time


def test_live_wizard_never_claims_a_trusted_clock():
    from beamo_wipe.evidence import wall_timestamps  # the existing confidence logic

    wiz = make_demo_wizard()
    assert wiz.wall_clock_trusted is False
    assert wiz.progress_view.wall_trusted is False
    stamps = wall_timestamps("2026-11-05T14:02:00Z", "", "os_utc")
    assert stamps["wall_confidence"] == "unverified"
    # Only an explicit True turns clock times on.
    wiz.wall_clock_trusted = "yes"  # type: ignore[assignment]
    assert wiz.progress_view.wall_trusted is False
    wiz.wall_clock_trusted = True
    assert wiz.progress_view.wall_trusted is True


def test_preview_payload_uses_the_new_line():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    payload = json.loads(re.search(r"const P = (\{.*?\});\n", html, re.S).group(1))
    lines = json.dumps(payload["progress"], ensure_ascii=False)
    assert "Running for" not in lines
    assert "Started " in lines


@pytest.mark.parametrize("trusted", [False, True])
def test_tk_shows_the_line_in_large_text(trusted):
    from unittest.mock import PropertyMock, patch

    from test_tk_runtime import _needs_display
    from beamo_wipe.models import Screen
    from beamo_wipe.ui.tk_wizard import TkWizard
    from beamo_wipe.wizard import Wizard

    _needs_display()
    wiz = make_demo_wizard()
    wiz.screen = Screen.WORKING
    wiz.selected = wiz.selectable[0]
    shown = view(trusted=trusted)
    app = TkWizard(wiz)
    try:
        with patch.object(Wizard, "progress_view", new_callable=PropertyMock, return_value=shown):
            app.root.geometry("1280x820+20+20")
            app._draw()
            for _ in range(6):
                app.root.update()
            label = app._progress_time
            assert label.cget("text") == shown.glance_time
            assert str(label.cget("font")) == str(app.font_size_big)
            assert label.winfo_ismapped()
    finally:
        app._teardown()
