# SPDX-License-Identifier: GPL-3.0-or-later
"""The curses result page keeps its first-page landmarks at 80x24.

The stacked UI tasks (#134 plain result, #135 report panel, #171 result card,
#175 F10 footer line) each added rows to the Done page. Together they pushed
the support destination for failed results and, after a report was saved,
the "you can remove the report USB" step below the first 80x24 page. Both
were on the first page before (872d38c, fd199de). Fake devices only.
"""

from __future__ import annotations

import pytest

from beamo_wipe import copy as C
from beamo_wipe import support_contact as SC
from beamo_wipe.ui import console_wizard as console
from test_console_parity import _draw
from test_result_presentations import CASES, case_evidence
from test_usb_report_workflow import _done_wizard, _success_receipt


def _first_page(term):
    first = term.frames[0]
    assert max(first) < 24
    assert all(console._display_cols(row) < 80 for row in first.values())
    return " ".join(first[y] for y in sorted(first))


@pytest.mark.parametrize("case", CASES, ids=[case[0] for case in CASES])
def test_first_page_shows_help_destination_exactly_when_needed(monkeypatch, case):
    wiz, _, _ = case_evidence(case)
    _, _, term = _draw(monkeypatch, wiz, sizes=[(24, 80)] * 2)
    first = _first_page(term)
    assert (SC.SUPPORT_SHORT in first) is wiz.done_support_needed, case[0]
    # The report panel heading stays on the first page as well (#135).
    assert C.REPORT_STATUS_TITLE in first, case[0]
    # The step that sends the owner to support comes before the destination.
    if wiz.done_support_needed and "contact support" in wiz.result_view.next_step:
        assert first.index("contact support") < first.index(SC.SUPPORT_SHORT)


def test_first_page_says_report_usb_can_be_removed_once_saved(monkeypatch, tmp_path):
    wiz = _done_wizard(lambda **kw: _success_receipt(**kw), tmp_path)
    _, _, term = _draw(monkeypatch, wiz, sizes=[(24, 80)] * 2)
    assert C.REPORT_STEP_REMOVE_NOW not in _first_page(term)

    wiz = _done_wizard(lambda **kw: _success_receipt(**kw), tmp_path)
    wiz.save_report_to_usb()
    assert wiz.report_panel.kind == "saved"
    _, _, term = _draw(monkeypatch, wiz, sizes=[(24, 80)] * 2)
    first = _first_page(term)
    assert C.REPORT_STEP_REMOVE_NOW in first
    assert first.index(C.REPORT_STATUS_TITLE) < first.index(C.REPORT_STEP_REMOVE_NOW)
