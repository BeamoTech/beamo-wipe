# SPDX-License-Identifier: GPL-3.0-or-later
"""#170: "Saving or checking a report does not change the erase result."
appears only after a failed save, where it reassures.

It was always shown. Now the report panel keeps it out of the ready,
saving, saved and unavailable views, shows it when a report or evidence
save failed (unless the failure text already says it), and keeps the
unsaved-report warning whenever the report is not saved. The erase result
and the report panel stay separate (Ref #96). Fake data only.
"""

from __future__ import annotations

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe.recovery import MEANING_REPORT_ONLY
from beamo_wipe.report_panel import build_report_panel


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def report(status="idle", *, can_save=True, message="", saving_evidence=False,
           evidence_error=False):
    from beamo_wipe.wizard import ReportView

    return ReportView(
        0, status, message, "", status == "saving", can_save,
        "evidence write failed" if evidence_error else None,
        saving_evidence=saving_evidence, can_retry_evidence=True,
    )


def usb():
    return None  # no live detection: Save is offered and checks the USB itself


@pytest.mark.parametrize("kwargs,kind", [
    ({}, "ready"),
    ({"status": "saving"}, "saving"),
    ({"status": "saved", "message": "Saved."}, "saved"),
    ({"can_save": False}, "unavailable"),
])
def test_not_in_the_default_views(kwargs, kind):
    panel = build_report_panel(report(**kwargs), preview=False, usb=usb())
    assert panel.kind == kind
    assert C.REPORT_STATUS_NOTICE not in panel.notice
    assert C.REPORT_STATUS_NOTICE not in " ".join(panel.lines)
    # The unsaved-report warning stays unless the report was saved.
    assert (C.REPORT_VOLATILE in panel.notice) is (kind != "saved")


@pytest.mark.parametrize("kwargs", [
    {"status": "error", "message": "copy_failed"},
    {"status": "error", "message": "copy_failed", "can_save": False},
    {"evidence_error": True},
])
def test_shown_once_after_a_failed_save(kwargs):
    panel = build_report_panel(report(**kwargs), preview=False, usb=usb())
    text = " ".join(panel.lines)
    assert C.REPORT_STATUS_NOTICE in text or MEANING_REPORT_ONLY in text
    # Never twice: either the panel's notice or the failure text says it.
    said = text.count(C.REPORT_STATUS_NOTICE) + text.count(MEANING_REPORT_ONLY)
    assert said == 1
    assert C.REPORT_VOLATILE in panel.notice


def test_preview_panel_has_no_notice():
    panel = build_report_panel(report(), preview=True, usb=usb())
    assert panel.kind == "preview" and not panel.notice
    from beamo_wipe.gallery import gallery_html

    assert C.REPORT_STATUS_NOTICE not in gallery_html()


def test_every_surface_reads_the_panel_notice():
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[1] / "src" / "beamo_wipe" / "ui"
    for name in ("tk_wizard.py", "accessible_wizard.py", "console_wizard.py"):
        src = (root / name).read_text(encoding="utf-8")
        assert "panel.notice" in src and "REPORT_STATUS_NOTICE" not in src, name
