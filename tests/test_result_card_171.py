# SPDX-License-Identifier: GPL-3.0-or-later
"""#171: one compact result card instead of the repeated method line.

The card holds disk (model, size, serial), method, check result and the
start and end times, taken from the photo record's own facts (#127), so the
card, the QR summary and RESULT.txt cannot disagree. The check result
follows the on-screen outcome: Verified / Not checked (Quick zero) /
Stopped / Not confirmed / Failed, never stronger. Fake disks and fake
nwipe logs only.
"""

from __future__ import annotations

import pathlib

import pytest

from beamo_wipe import erase_record as R
from beamo_wipe import lang
from beamo_wipe import result_summary as RS
from beamo_wipe.methods import METHODS
from beamo_wipe.models import MethodId
from beamo_wipe.ui import console_wizard
from test_result_presentations import CASES, case_evidence

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPECTED_CHECK = {
    "verified": "Verified",
    "unverified": "Not checked (Quick zero)",
    "cancelled": "Stopped",
    "interrupted": "Stopped",
    "completion_missing": "Not confirmed",
    "indeterminate": "Not confirmed",
}


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


@pytest.mark.parametrize("case", CASES, ids=[c[0] for c in CASES])
def test_card_matches_the_record_and_the_report(case):
    wiz, evidence, _log = case_evidence(case)
    card = wiz.result_card
    record = wiz.erase_record
    assert card is not None
    code = wiz.result_view.code
    rows = dict(card.rows)
    # Disk, method and times are the record's facts, value for value.
    if record is not None:
        shared = {label: value for label, value in record.fields
                  if label in (RS.H_DISK, RS.H_CAPACITY, RS.H_METHOD, RS.H_STARTED, RS.H_ENDED)}
        for label, value in shared.items():
            assert rows[label] == value, label
    assert rows[RS.H_METHOD] == METHODS[case[1]].title
    # The saved report names the same method.
    report = RS.build_result_summary(evidence)
    assert METHODS[case[1]].title in report
    # The check result follows the outcome and never says more.
    check = rows[R.CHECK_LABEL]
    assert check == EXPECTED_CHECK.get(code, "Failed"), code
    if code != "verified":
        assert "Verified" not in check
    # Order: disk identity first, then method, then the check result.
    labels = [label for label, _ in card.rows]
    assert labels.index(RS.H_METHOD) + 1 == labels.index(R.CHECK_LABEL)


def test_quick_zero_never_reads_verified():
    case = next(c for c in CASES if c[1] == MethodId.QUICK_ZERO)
    wiz, _ev, _log = case_evidence(case)
    text = " ".join(wiz.result_card.lines).lower()
    assert "not checked" in text and " verified" not in text


def test_preview_card_says_nothing_was_erased_and_has_no_times():
    case = next(c for c in CASES if c[0] == "verified")
    wiz, _ev, _log = case_evidence(case)
    wiz.preview = True
    rows = dict(wiz.result_card.rows)
    assert rows[R.CHECK_LABEL] == R.CHECK_PREVIEW
    assert RS.H_STARTED not in rows and RS.H_ENDED not in rows


def test_check_text_rules():
    assert R.check_text("unverified", quick_zero=False, method="Everyday", preview=False) == "Not checked"
    assert R.check_text("stop_unconfirmed", quick_zero=False, method="", preview=False) == "Not confirmed"
    assert R.check_text("engine_failed", quick_zero=False, method="", preview=False) == "Failed"
    assert R.check_text("verified", quick_zero=False, method="", preview=True) == R.CHECK_PREVIEW


def test_every_language_has_the_card_words():
    for code in lang.LANGUAGE_ORDER:
        lang.set_language(code)
        text = R.check_text("unverified", quick_zero=True, method=METHODS[MethodId.QUICK_ZERO].title,
                            preview=False)
        assert METHODS[MethodId.QUICK_ZERO].title in text and "{" not in text
        for word in (R.CARD_TITLE, R.CHECK_LABEL, R.CHECK_VERIFIED, R.CHECK_FAILED):
            assert word


def test_consoles_show_the_card_not_the_method_line(monkeypatch, capsys):
    case = next(c for c in CASES if c[0] == "verified")
    wiz, _ev, _log = case_evidence(case)
    lines = console_wizard._result_card_lines(wiz, 120)
    assert f"{R.CHECK_LABEL}: Verified" in " ".join(lines)
    src = (ROOT / "src/beamo_wipe/ui/console_wizard.py").read_text(encoding="utf-8")
    done = src[src.index("elif wizard.screen == Screen.DONE:"):]
    done = done[: done.index("limits_offset = _paint_paged", 10)]
    assert "method_summary" not in done
    monkeypatch.setattr("builtins.input", lambda _p: (_ for _ in ()).throw(EOFError()))
    console_wizard._plain_loop(wiz)
    out = capsys.readouterr().out
    assert f"{R.CHECK_LABEL}: Verified" in out
    assert METHODS[case[1]].summary not in out


def test_gtk_source_lists_the_card_for_orca():
    src = (ROOT / "src/beamo_wipe/ui/accessible_wizard.py").read_text(encoding="utf-8")
    block = src[src.index("def result_card_list"):src.index("def label(self, text")]
    assert "Atk.Role.LIST" in block and "Atk.Role.LIST_ITEM" in block
    assert "set_can_focus(True)" in block
    assert "self.result_card_list()" in src and "self.label(self.w.method_summary)\n            self.label(self.w.elapsed_text)" not in src


def test_preview_payload_card():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    assert R.CHECK_PREVIEW in html and 'class="factrows"' in html


@pytest.mark.parametrize("size", [(800, 600), (1280, 820)])
def test_tk_result_card(size):
    from test_tk_runtime import _clipping_problems, _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    case = next(c for c in CASES if c[0] == "verified")
    wiz, _ev, _log = case_evidence(case)
    app = TkWizard(wiz)
    try:
        app.root.geometry(f"{size[0]}x{size[1]}+20+20")
        app._draw()
        for _ in range(8):
            app.root.update()
        texts = []
        facts = []

        def visit(w):
            if w.winfo_class() == "Label" and w.winfo_ismapped():
                texts.append(str(w.cget("text")))
            if getattr(w, "_beamo_fact_rows", None):
                facts.append(w._beamo_fact_rows)
            for child in w.winfo_children():
                visit(child)

        visit(app._body)
        assert R.CARD_TITLE in texts
        (rows,) = facts
        assert rows == wiz.result_card.detail_rows
        assert "Verified" in texts and f"{R.CHECK_LABEL}:" in texts
        assert METHODS[case[1]].summary not in texts  # the repeated method line is gone
        assert not _clipping_problems(app)
    finally:
        app._teardown()
