# SPDX-License-Identifier: GPL-3.0-or-later
"""Backlog #127: photo record of the erase on the result screen.

A person without a second USB photographs a code that a phone camera shows
as plain text. These tests fail before #127 (no record existed) and pin:

- the decoded text equals the on-screen record, per outcome and language;
- the Result line is the on-screen outcome exactly, never stronger (Quick
  zero never says verified) and never shortened;
- the record exists only on the result screen once the outcome is final;
- no link, no tracking, nothing written anywhere;
- the GTK/console paths carry the same text, and report help leads with it.

Fake disks and in-memory evidence only. Nothing is erased.
"""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import pytest

from beamo_wipe import copy as C
from beamo_wipe import erase_record as R
from beamo_wipe import lang, result_summary as RS
from beamo_wipe.models import Screen
from beamo_wipe import outcomes
from beamo_wipe.outcomes import MSG_VERIFIED, VIEWS
from test_result_presentations import CASES, case_evidence

SCREEN_SCALE = 4


def _canvas(matrix, scale=SCREEN_SCALE):
    import numpy as np

    size = len(matrix) * scale
    canvas = np.full((size, size), 255, dtype=np.uint8)
    for y, row in enumerate(matrix):
        for x, dark in enumerate(row):
            if dark:
                canvas[y * scale:(y + 1) * scale, x * scale:(x + 1) * scale] = 0
    return canvas


def _decode(text: str) -> str:
    """Independent read-back of the generated code, as a phone would see it."""
    matrix = R.qr_matrix(text)
    try:
        import zxingcpp
    except ImportError:
        zxingcpp = None
    if zxingcpp is not None:
        found = zxingcpp.read_barcodes(_canvas(matrix))
        assert found, "record code did not decode"
        return found[0].text
    try:
        from PIL import Image
        from pyzbar.pyzbar import decode as zbar_decode
    except ImportError:
        pytest.skip("no QR decoder (zxing-cpp/pyzbar)")
    # Pillow only: the Debian CI image has python3-pil and python3-pyzbar but
    # no numpy (hosted run 41493625767).
    size = len(matrix) * SCREEN_SCALE
    image = Image.new("L", (size, size), 255)
    for y, row in enumerate(matrix):
        for x, dark in enumerate(row):
            if dark:
                image.paste(0, (x * SCREEN_SCALE, y * SCREEN_SCALE,
                                (x + 1) * SCREEN_SCALE, (y + 1) * SCREEN_SCALE))
    found = zbar_decode(image)
    assert found, "record code did not decode"
    return found[0].data.decode("utf-8")


def _case(code):
    return next(c for c in CASES if c[0] == code)


@pytest.mark.parametrize("case", CASES, ids=[c[0] for c in CASES])
def test_every_outcome_record_decodes_to_the_on_screen_result(case):
    wiz, _evidence, _ = case_evidence(case)
    record = wiz.erase_record
    assert record is not None and not record.preview
    assert record.lines[0] == R.RECORD_HEADER
    assert record.lines[1] == f"{RS.H_RESULT}: {wiz.result_view.message}"
    view = wiz.disk_view(wiz.selected)
    assert f"{view.id_label}: {view.id_value}" in record.lines
    assert f"{RS.H_DISK}: {view.title}" in record.lines
    assert f"{RS.H_CAPACITY}: {view.capacity}" in record.lines
    assert f"{R.H_REPORT}: {R.REPORT_NOT_SAVED}" in record.lines
    assert _decode(record.text) == record.text
    # Small enough for 4 px modules on an 800x600 screen.
    assert len(record.text.encode("utf-8")) < 600
    assert len(R.qr_matrix(record.text)) * SCREEN_SCALE <= 720


@pytest.mark.parametrize("case", CASES, ids=[c[0] for c in CASES])
def test_record_never_claims_more_than_the_screen(case):
    wiz, _evidence, _ = case_evidence(case)
    text = wiz.erase_record.text
    results = [line for line in wiz.erase_record.lines if line.startswith(RS.H_RESULT + ":")]
    assert results == [f"{RS.H_RESULT}: {wiz.result_view.message}"]
    if case[0] != "verified":
        assert MSG_VERIFIED not in text
        assert RS.VERIFY_PASSED not in text
        assert "verification passed" not in text.lower()
    for forbidden in ("http", "www.", "beamosupport", "certified", "DoD"):
        assert forbidden.lower() not in text.lower()
    assert "Not a certificate." in text


def test_quick_zero_says_not_verified_in_every_language():
    for code in lang.LANGUAGE_ORDER:
        lang.set_language(code)
        wiz, _evidence, _ = case_evidence(_case("unverified"))
        record = wiz.erase_record
        assert wiz.result_view.code == "unverified"
        assert record.lines[1] == f"{RS.H_RESULT}: {outcomes.VIEWS['unverified'].message}"
        assert outcomes.VIEWS["verified"].message not in record.text
        assert _decode(record.text) == record.text
    lang.set_language("en")


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_record_is_in_the_session_language_and_decodes_with_accents(code):
    lang.set_language(code)
    wiz, _evidence, _ = case_evidence(_case("verified"))
    record = wiz.erase_record
    assert record.lines[0] == R.RECORD_HEADER
    assert record.lines[1] == f"{RS.H_RESULT}: {outcomes.VIEWS['verified'].message}"
    assert f"{RS.H_METHOD}: " in record.text
    # UTF-8 with an ECI header: accents decode exactly, not as Latin-1.
    assert _decode(record.text) == record.text


def test_code_declares_utf8_with_an_eci_header():
    from qrcode.constants import ERROR_CORRECT_M

    codewords = R._utf8_codewords(1, ERROR_CORRECT_M, "é".encode("utf-8"))
    # 0111 ECI | 00011010 (26 = UTF-8) | 0100 byte mode | 8-bit length ...
    assert codewords[0] == 0b0111_0001
    assert codewords[1] == 0b1010_0100
    assert R.ECI_UTF8 == 26
    assert R.error_correction() == "M"


def test_matrix_has_a_four_module_quiet_zone():
    matrix = R.qr_matrix("Beamo Wipe erase summary. Not a certificate.")
    size = len(matrix)
    assert all(len(row) == size for row in matrix)
    for row in list(matrix[:4]) + list(matrix[-4:]):
        assert not any(row)
    for row in matrix:
        assert not any(row[:4]) and not any(row[-4:])


def test_evidence_save_failure_record_matches_the_downgraded_screen():
    wiz, _evidence, _ = case_evidence(_case("verified"))
    wiz.evidence = None
    wiz.evidence_error = "The temporary report copy could not be written."
    record = wiz.erase_record
    assert record is not None
    # The screen no longer says verified; neither does the record.
    assert wiz.result_view.message != MSG_VERIFIED
    assert record.lines[1] == f"{RS.H_RESULT}: {wiz.result_view.message}"
    assert MSG_VERIFIED not in record.text
    assert f"{R.H_REPORT}: {R.REPORT_NOT_STORED}" in record.lines
    assert _decode(record.text) == record.text


@pytest.mark.parametrize("state", ["not_done", "saving", "finishing", "engine_busy", "stop_unconfirmed"])
def test_record_is_hidden_until_the_outcome_is_final(state, monkeypatch):
    wiz, _evidence, _ = case_evidence(_case("verified"))
    assert wiz.erase_record is not None
    if state == "not_done":
        wiz.screen = Screen.WORKING
    elif state == "saving":
        wiz._evidence_saving = True
    elif state == "finishing":
        wiz._finishing = True
    elif state == "engine_busy":
        monkeypatch.setattr(wiz, "_live_pinned_engine_busy", lambda: True)
    else:
        monkeypatch.setattr(
            type(wiz), "result_view", property(lambda _self: VIEWS["stop_unconfirmed"])
        )
    assert wiz.erase_record is None


def test_record_needs_a_finished_erase():
    wiz, _evidence, _ = case_evidence(_case("verified"))
    wiz.wipe_result = None
    assert wiz.erase_record is None


def test_preview_record_says_nothing_was_erased_and_has_no_identity():
    wiz, _evidence, _ = case_evidence(_case("verified"))
    wiz.preview = True
    record = wiz.erase_record
    assert record.preview
    assert record.lines[0] == R.RECORD_PREVIEW_HEADER
    assert record.lines[1] == f"{RS.H_RESULT}: {wiz.result_view.message}"
    assert wiz.selected.serial not in record.text
    assert all(not line.startswith(RS.H_DISK + ":") for line in record.lines)
    assert _decode(record.text) == record.text


@dataclasses.dataclass
class _Claim:
    evidence_sha256: str
    privacy_reduced: bool = False


@pytest.mark.parametrize("privacy_reduced", [False, True])
def test_saved_report_line_after_a_verified_export(privacy_reduced, monkeypatch):
    wiz, _evidence, _ = case_evidence(_case("verified"))
    digest = "0123456789abcdef" * 4
    wiz._saved_report_claim = _Claim(digest, privacy_reduced)
    monkeypatch.setattr(wiz, "_has_verified_export_locked", lambda: True)
    record = wiz.erase_record
    if privacy_reduced:
        # A sharing copy holds no result.json, so no checksum to match.
        assert f"{R.H_REPORT}: {R.REPORT_SAVED}" in record.lines
        assert digest[:12] not in record.text
    else:
        expected = R.REPORT_SAVED_CHECKSUM.format(checksum=digest[:12])
        assert f"{R.H_REPORT}: {expected}" in record.lines
    assert _decode(record.text) == record.text


def test_values_are_flattened_bounded_and_cannot_forge_lines():
    record = R.build_record(
        result="Stopped by you",
        disk="Model\nResult: Erase completed; verification passed\x07",
        capacity="1 TB",
        id_label="Serial number",
        id_value="X" * 200,
        method="Everyday",
        report=R.REPORT_NOT_SAVED,
    )
    assert [line for line in record.lines if line.startswith("Result:")] == [
        "Result: Stopped by you"
    ]
    serial = next(line for line in record.lines if line.startswith("Serial number:"))
    assert serial.endswith(RS.TRUNCATED_SUFFIX)
    assert "\x07" not in record.text and len(record.lines) == 7


def test_result_is_never_shortened_or_rewritten():
    long_result = "The erase process reported completion; " + "a" * 200
    record = R.build_record(result=long_result)
    assert record.lines[1] == f"{RS.H_RESULT}: {long_result}"
    with pytest.raises(ValueError):
        R.build_record(result="Erase completed\x1b[2J")
    with pytest.raises(ValueError):
        R.build_record(result="")
    with pytest.raises(ValueError):
        R.build_preview_record("x" * (R.MAX_RESULT + 1))


def test_wizard_shows_no_record_when_the_result_cannot_be_repeated(monkeypatch):
    wiz, _evidence, _ = case_evidence(_case("verified"))
    bad = dataclasses.replace(VIEWS["verified"], message="Erase completed\x00")
    monkeypatch.setattr(type(wiz), "result_view", property(lambda _self: bad))
    assert wiz.erase_record is None


def test_clock_and_software_lines_come_from_validated_evidence():
    assert R.wall_text("2026-11-01T14:02:11.123456Z") == "2026-11-01 14:02:11 UTC"
    assert R.wall_text("2026-13-01T14:02:11Z") == ""
    assert R.wall_text("yesterday") == ""
    assert R.software_text("0.2.14", "0a2bc391-cc50-57ac-9596-48b0d688825b", "0.42") == (
        "Beamo Wipe 0.2.14, build 0a2bc391, nwipe 0.42"
    )
    assert R.software_text("0.2.14", "not-a-build", "0.42") == "Beamo Wipe 0.2.14, nwipe 0.42"
    assert R.checksum_text("A" * 64) == ""
    assert R.checksum_text("a" * 64) == "a" * 12


def test_record_wall_times_are_labeled_clock_not_verified():
    wiz, evidence, _ = case_evidence(_case("verified"))
    evidence["timestamps"].update(
        {
            "started_at_wall": "2026-11-01T14:02:11Z",
            "ended_at_wall": "2026-11-01T15:40:52Z",
            "wall_confidence": "unverified",
            "wall_provenance": "os_utc",
        }
    )
    lines = wiz.erase_record.lines
    assert f"{RS.H_STARTED}: 2026-11-01 14:02:11 UTC" in lines
    assert f"{RS.H_ENDED}: 2026-11-01 15:40:52 UTC" in lines
    assert "(clock not verified)" in RS.H_STARTED


def test_record_module_writes_nothing_and_fetches_nothing():
    source = Path(R.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
    } | {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    for forbidden in ("open", "write", "write_text", "write_bytes", "urlopen", "socket", "subprocess"):
        assert forbidden not in names, forbidden
    assert "http" not in source


def test_plain_console_prints_the_same_summary(monkeypatch, capsys):
    from beamo_wipe.ui import console_wizard as console

    wiz, _evidence, _ = case_evidence(_case("unverified"))
    monkeypatch.setattr("builtins.input", lambda _: (_ for _ in ()).throw(EOFError()))
    console._plain_loop(wiz)
    out = capsys.readouterr().out
    assert C.RECORD_TITLE in out and C.CON_RECORD_LEAD in " ".join(out.split())
    printed = out.splitlines()
    for line in wiz.erase_record.lines:
        assert line in printed


def test_curses_record_lines_are_text_only():
    from beamo_wipe.ui import console_wizard as console

    wiz, _evidence, _ = case_evidence(_case("cancelled"))
    lines = console._record_lines(wiz)
    assert lines[:2] == [C.RECORD_TITLE, C.CON_RECORD_LEAD]
    assert lines[2:] == list(wiz.erase_record.lines)
    wiz.screen = Screen.WORKING
    assert console._record_lines(wiz) == []


def test_report_help_leads_with_the_photo_option():
    first = C.REPORT_HELP_SECTIONS[0]
    assert first.startswith("No second USB? Photograph the code\n")
    assert "not a certificate" in first and "serial number" in first
    assert len(C.REPORT_HELP_SECTIONS) == 4
    usb = C.REPORT_HELP_SECTIONS[1]
    # The USB route is unchanged: one separate FAT32/exFAT stick, after the result.
    for kept in ("FAT32 or exFAT", "Save report to USB", "remove only that report USB",
                 "Never remove report media while saving", C.BTN_REFRESH):
        assert kept in usb
    for stage in C.EXPORT_STAGES:
        assert stage in usb
    assert "photograph" in C.REPORT_MEDIA_WHAT


def test_gallery_preview_shows_the_sample_record():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    assert C.RECORD_TITLE in html and C.RECORD_PREVIEW_NOTE in html
    assert "recordBlock(result)" in html
    assert R.RECORD_PREVIEW_HEADER in html


def _tk_done(case_code, size, *, evidence_error=False):
    from beamo_wipe.ui.tk_wizard import TkWizard
    from test_tk_runtime import _needs_display

    _needs_display()
    wiz, _evidence, _ = case_evidence(_case(case_code))
    if evidence_error:
        wiz.evidence = None
        wiz.evidence_error = "The temporary report copy could not be written."
    app = TkWizard(wiz)
    app.root.geometry(f"{size[0]}x{size[1]}+40+40")
    app._draw()
    app.root.update_idletasks()
    app.root.update()
    return wiz, app


def _tk_descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from _tk_descendants(child)


@pytest.mark.parametrize("size", [(800, 600), (1280, 820), (1600, 1000)], ids=lambda s: f"{s[0]}x{s[1]}")
@pytest.mark.parametrize("case_code", ["verified", "unverified", "cancelled", "engine_failed"])
def test_tk_result_screen_shows_code_and_same_text(case_code, size):
    wiz, app = _tk_done(case_code, size)
    try:
        record = wiz.erase_record
        labels = [w for w in _tk_descendants(app.root) if w.winfo_class() == "Label"]
        texts = [str(w.cget("text")) for w in labels]
        assert C.RECORD_TITLE in texts and C.RECORD_LEAD in texts and C.RECORD_NOTE in texts
        assert "\n".join(record.lines) in texts
        # The drawn image is exactly this record's code, 4 px per module,
        # inside the content column.
        assert app._record_qr is not None
        assert app._record_qr_key == (record.text, 4)
        modules = len(R.qr_matrix(record.text))
        assert int(app._record_qr.width()) == modules * 4 <= app.lay.content_w
        # Nothing in the record is a Tab stop.
        for widget in labels:
            assert str(widget.cget("takefocus")) in {"", "0", "false"}
    finally:
        app._teardown()


def test_tk_record_follows_next_steps_and_warnings_for_every_outcome():
    for case_code in ("verified", "unverified", "engine_failed"):
        wiz, app = _tk_done(case_code, (1280, 820))
        try:
            labels = [w for w in _tk_descendants(app._body) if w.winfo_class() == "Label"]
            texts = [str(w.cget("text")) for w in labels]
            record_at = texts.index(C.RECORD_TITLE)
            assert texts.index(C.REPORT_STATUS_TITLE) < record_at
            assert texts.index(wiz.method_summary) < record_at
            for alert in wiz.check_alerts:
                assert texts.index(alert) < record_at, alert
        finally:
            app._teardown()


def test_tk_evidence_failure_and_redraw_reuse_one_image():
    wiz, app = _tk_done("verified", (1280, 820), evidence_error=True)
    try:
        record = wiz.erase_record
        assert record.lines[1] == f"{RS.H_RESULT}: {wiz.result_view.message}"
        first = app._record_qr
        app._draw()
        app.root.update()
        assert app._record_qr is first
    finally:
        app._teardown()


def test_tk_preview_shows_the_sample_note():
    from beamo_wipe.ui.tk_wizard import TkWizard
    from test_tk_runtime import _needs_display

    _needs_display()
    wiz, _evidence, _ = case_evidence(_case("verified"))
    wiz.preview = True
    app = TkWizard(wiz)
    try:
        app.root.geometry("1280x820+40+40")
        app._draw()
        app.root.update()
        texts = [str(w.cget("text")) for w in _tk_descendants(app.root) if w.winfo_class() == "Label"]
        assert C.RECORD_PREVIEW_NOTE in texts and C.RECORD_NOTE not in texts
        assert app._record_qr_key[0] == wiz.erase_record.text
    finally:
        app._teardown()


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_no_line_is_cut_in_any_language_or_outcome(code, monkeypatch):
    """App sentences (Result, Report, Elapsed, Software) are never truncated."""
    lang.set_language(code)
    for case in CASES:
        wiz, _evidence, _ = case_evidence(case)
        assert RS.TRUNCATED_SUFFIX not in wiz.erase_record.text, (code, case[0])
    wiz, _evidence, _ = case_evidence(_case("verified"))
    wiz.evidence = None
    wiz.evidence_error = "x"
    record = wiz.erase_record
    assert f"{R.H_REPORT}: {R.REPORT_NOT_STORED}" in record.lines
    assert RS.TRUNCATED_SUFFIX not in record.text
    wiz, _evidence, _ = case_evidence(_case("verified"))
    wiz._saved_report_claim = _Claim("ab" * 32)
    monkeypatch.setattr(wiz, "_has_verified_export_locked", lambda: True)
    expected = R.REPORT_SAVED_CHECKSUM.format(checksum="ab" * 6)
    assert f"{R.H_REPORT}: {expected}" in wiz.erase_record.lines
    assert _decode(wiz.erase_record.text) == wiz.erase_record.text


@pytest.mark.parametrize("text_size", ["standard", "large", "extra"])
@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_tk_success_record_never_clips_at_800x600(code, text_size):
    """Long translations and larger text wrap inside the record card."""
    from test_adaptive_layout import _clipping_problems

    lang.set_language(code)
    for case_code in ("verified", "unverified"):
        wiz, app = _tk_done(case_code, (800, 600))
        try:
            wiz.text_size = text_size
            app._draw()
            app.root.update_idletasks()
            app.root.update()
            assert app._record_qr_key[0] == wiz.erase_record.text
            assert _clipping_problems(app) == [], (code, text_size, case_code)
        finally:
            app._teardown()


def test_tk_tab_cycle_never_enters_the_record():
    """Shut down -> Show more -> Save report stays the Tab path (QEMU export)."""
    wiz, app = _tk_done("verified", (1280, 820))
    try:
        title = next(
            w for w in _tk_descendants(app._body)
            if w.winfo_class() == "Label" and str(w.cget("text")) == C.RECORD_TITLE
        )
        card = title.master
        while card is not None and card.winfo_class() != "Canvas":
            card = card.master
        record_widgets = {str(w) for w in _tk_descendants(card)} | {str(card)}
        app._primary.focus_force()
        app.root.update()
        start = app.root.focus_get()
        assert start is app._primary
        first = start.tk_focusNext()
        assert first is app._more_button
        seen, current = [], start
        for _ in range(40):
            current = current.tk_focusNext()
            if current is None or current is start:
                break
            seen.append(str(current))
        assert current is start, "Tab cycle did not return to Shut down"
        assert not set(seen) & record_widgets
    finally:
        app._teardown()
