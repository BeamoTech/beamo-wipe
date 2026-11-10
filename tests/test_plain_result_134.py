# SPDX-License-Identifier: GPL-3.0-or-later
"""#134: plain result headline and a short What next list.

The headline, note and list are screen copy only. Each outcome's technical
``message`` stays in evidence, the saved report, the photo record and under
Show more (failures: What happened). Quick zero never says checked or
verified; nothing promises more than docs/claims.md. Fake disks only.
"""

from __future__ import annotations

import dataclasses
from unittest.mock import PropertyMock, patch

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe import outcomes as O
from beamo_wipe import recovery as Rec
from beamo_wipe import wizard as W
from beamo_wipe.wizard import Wizard
from test_result_presentations import CASES, case_evidence

APPROVED_HEADLINES = {
    "verified": "Done — this disk was erased and checked",
    "unverified": "Done — this disk was overwritten with zeros (not checked)",
    "verification_failed": "Not confirmed — the check after the erase failed",
    "engine_failed": "Not finished — the disk reported an error",
    "process_failed": "Not finished — the erase ended with an error",
    "completion_missing": "Not confirmed — the erase may not have finished",
    "indeterminate": "Not confirmed — the result is unknown",
    "interrupted": "Not finished — the erase was interrupted",
    "cancelled": "Stopped — you stopped the erase before it finished",
    "occupied": "Not finished — the disk was in use",
    "open_failed": "Nothing erased — the disk could not be opened",
    "geometry_unusable": "Nothing erased — the disk could not be used safely",
    "start_failed": "Nothing erased — the erase could not start",
    "stop_unconfirmed": "Not confirmed — the erase may still be running",
}
APPROVED_LIST = (
    "Shut down when you have finished.",
    "When the computer is off, remove the Beamo USB.",
    "Keeping this computer? If this was its main disk, install an operating "
    "system before you use it again.",
)
GIVE_VERIFIED = "Giving it away or selling it? This disk is ready to pass on."
GIVE_QUICK_ZERO = "Giving it away or selling it? Erase it again with Everyday first — it checks its work."
# docs/claims.md forbidden promises, in every language's likely spelling.
FORBIDDEN = (
    "certif", "zertifi", "dod", "nist", "nsa", "blancco", "unrecoverable",
    "impossible", "guarantee", "garanti", "permanent", "sanitiz", "irrécup",
    "irrecuper", "nicht wiederherstellbar", "for good", "forever",
)


@pytest.fixture(autouse=True)
def _english_after():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _case(code):
    return next(c for c in CASES if c[0] == code)


def _all_text(plain):
    return " ".join((plain.headline, plain.note, *plain.checklist))


# --- Model -----------------------------------------------------------------------


def test_every_outcome_has_its_approved_plain_headline():
    for code, view in O.VIEWS.items():
        assert O.plain_result(view).headline == APPROVED_HEADLINES[code], code
    assert set(APPROVED_HEADLINES) == set(O.VIEWS)


@pytest.mark.parametrize("case", CASES, ids=[c[0] for c in CASES])
def test_each_rendered_outcome_gets_its_headline_and_only_finished_ones_a_list(case):
    wiz, _evidence, _ = case_evidence(case)
    plain = wiz.result_plain
    assert plain.headline == APPROVED_HEADLINES[case[0]]
    if case[0] == "verified":
        assert plain.checklist == APPROVED_LIST + (GIVE_VERIFIED,)
    elif case[0] == "unverified":
        assert plain.checklist == APPROVED_LIST + (GIVE_QUICK_ZERO,)
    else:
        assert plain.checklist == () and plain.note == ""
    assert 3 <= len(plain.checklist) <= 4 or not plain.checklist


def test_three_overwrites_verified_reads_the_same_as_everyday():
    from beamo_wipe.models import MethodId

    case = list(_case("verified"))
    case[1] = MethodId.EXTRA
    wiz, _evidence, _ = case_evidence(tuple(case))
    assert wiz.result_view.code == "verified"
    assert wiz.result_plain.headline == APPROVED_HEADLINES["verified"]
    assert wiz.result_plain.checklist[-1] == GIVE_VERIFIED


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_quick_zero_never_says_checked_or_verified(code):
    lang.set_language(code)
    wiz, _evidence, _ = case_evidence(_case("unverified"))
    plain = wiz.result_plain
    text = _all_text(plain)
    assert O.HEADLINE_VERIFIED not in text
    assert O.VIEWS["verified"].message not in text
    assert plain.headline != O.HEADLINE_VERIFIED
    assert wiz.result_view.tone == "warn" and wiz.result_view.icon == "warn"
    if code == "en":
        assert "(not checked)" in plain.headline
        for word in ("verified", "verification passed"):
            assert word not in text.lower()
        # "checked" only ever as "not checked"; the Everyday item says it checks.
        assert text.lower().count("checked") == text.lower().count("not checked")


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_plain_copy_stays_within_the_claims(code):
    lang.set_language(code)
    for view in O.VIEWS.values():
        text = _all_text(O.plain_result(view)).lower()
        for word in FORBIDDEN:
            assert word not in text, (code, view.code, word)
    # Both finished notes keep the SSD limit; neither promises more.
    for key in ("verified", "unverified"):
        assert "SSD" in O.plain_result(O.VIEWS[key]).note


def test_technical_status_line_is_unchanged_and_kept_for_support():
    assert O.MSG_VERIFIED == "Erase completed; verification passed"
    assert O.MSG_UNVERIFIED == "Erase completed; verification was not performed"
    wiz, evidence, _ = case_evidence(_case("verified"))
    assert wiz.result_technical == "Erase completed; verification passed. Result code: verified"
    # Evidence, the photo record and the report keep the technical message.
    assert evidence["presentation"]["message"] == O.MSG_VERIFIED
    assert wiz.method_result == O.MSG_VERIFIED
    assert any(line.endswith(O.MSG_VERIFIED) for line in wiz.erase_record.lines)
    assert O.HEADLINE_VERIFIED not in wiz.erase_record.text


def test_result_view_and_evidence_payload_are_unchanged():
    fields = {f.name for f in dataclasses.fields(O.ResultView)}
    assert fields == {"code", "message", "next_step", "tone", "icon", "success"}


@pytest.mark.parametrize(
    "message,code",
    [
        ("ERASE_STOPPED_BY_YOU", "cancelled"),
        ("ERASE_INTERRUPTED_MSG", "interrupted"),
        ("ERASE_COMPLETION_UNCONFIRMED", "completion_missing"),
        ("ERASE_UNFINISHED", "process_failed"),
    ],
)
def test_unsaved_evidence_headline_follows_the_shown_message(message, code):
    wiz, _evidence, _ = case_evidence(_case("verified"))
    view = dataclasses.replace(O.VIEWS["indeterminate"], message=getattr(W, message))
    with patch.object(Wizard, "result_view", new_callable=PropertyMock, return_value=view):
        plain = wiz.result_plain
    assert plain.headline == APPROVED_HEADLINES[code]
    assert plain.checklist == ()


def test_recovered_session_notice_leads_the_finished_note():
    from beamo_wipe.session_recovery import NOTICE

    wiz, _evidence, _ = case_evidence(_case("verified"))
    wiz._recovered = True
    plain = wiz.result_plain
    assert plain.note.startswith(NOTICE) and plain.note.endswith(O.NOTE_VERIFIED)


def test_preview_keeps_its_own_words():
    for ok in (True, False):
        view = O.preview_view(ok)
        plain = O.plain_result(view)
        assert plain.headline == view.message and plain.checklist == ()


def test_announcement_reads_headline_note_then_numbered_list():
    plain = O.plain_result(O.VIEWS["verified"])
    spoken = plain.announcement
    assert spoken.startswith(O.HEADLINE_VERIFIED + ". " + O.NOTE_VERIFIED)
    assert O.WHAT_NEXT + ": 1. " + APPROVED_LIST[0] in spoken
    assert spoken.endswith("4. " + GIVE_VERIFIED)


@pytest.mark.parametrize("code", [c for c in lang.LANGUAGE_ORDER if c != "en"])
def test_every_language_translates_the_plain_result(code):
    english = {k: lang.english("outcomes", k) for k in lang.keys("en", "outcomes")}
    names = [k for k in english if k.startswith(("HEADLINE_", "NOTE_", "NEXT_ITEM_")) or k == "WHAT_NEXT"]
    assert len(names) == 22
    for name in names:
        value = lang.translated(code, "outcomes", name)
        assert value and value != english[name], (code, name)
        assert ("{method}" in value) == ("{method}" in english[name]), (code, name)
    lang.set_language(code)
    from beamo_wipe import methods

    give = O.plain_result(O.VIEWS["unverified"]).checklist[-1]
    assert methods.TITLE_PRNG in give and "{" not in give


def test_web_preview_stop_screens_use_the_plain_headline():
    from beamo_wipe.gallery import gallery_html
    from test_preview_parity import _payload

    html = gallery_html()
    stop = _payload(html)["stop"]
    assert stop["stopped"]["headline"] == APPROVED_HEADLINES["cancelled"]
    assert stop["unconfirmed"]["headline"] == APPROVED_HEADLINES["stop_unconfirmed"]
    # The exact status stays as What happened.
    assert stop["stoppedRecovery"]["happened"] == O.MSG_CANCELLED
    assert "P.stop.stopped.headline" in html and "P.stop.stopped.message" not in html
    assert ": result.headline;" in html


# --- Consoles ---------------------------------------------------------------------


def _curses_lines(monkeypatch, wiz, h=60):
    from beamo_wipe.ui import console_wizard as console
    from test_console_parity import Terminal

    class Stop(BaseException):
        pass

    class Once(Terminal):
        def getch(self):
            self.frames.append(dict(self.rows))
            raise Stop

    for name in ("curs_set", "use_default_colors", "echo", "noecho", "beep"):
        monkeypatch.setattr(console.curses, name, lambda *a, **k: None)
    term = Once(wiz, h=h, w=80)
    with pytest.raises(Stop):
        console._loop(term, wiz)
    last = term.frames[-1]
    return [last.get(y, "") for y in range(h)]


@pytest.mark.parametrize("code", ["verified", "unverified"])
def test_curses_finished_result_shows_headline_list_and_technical_line(monkeypatch, code):
    wiz, _evidence, _ = case_evidence(_case(code))
    rows = _curses_lines(monkeypatch, wiz)
    text = "\n".join(rows)
    plain = wiz.result_plain
    assert plain.headline in rows[0]
    assert O.WHAT_NEXT in rows
    for item in plain.numbered:
        assert item[:30] in text
    assert C.POST_ERASE_BOOT[:40] not in text
    assert f"{Rec.RECOVERY_TECHNICAL}: {wiz.result_view.message}" in text
    # 80x24: the list and Report status stay on the first page.
    first = "\n".join(_curses_lines(monkeypatch, wiz, h=24))
    assert plain.numbered[-1][:30] in first and C.REPORT_STATUS_TITLE in first


def test_curses_failure_keeps_the_exact_status_under_the_plain_title(monkeypatch):
    wiz, _evidence, _ = case_evidence(_case("cancelled"))
    rows = _curses_lines(monkeypatch, wiz)
    assert APPROVED_HEADLINES["cancelled"] in rows[0]
    assert O.MSG_CANCELLED in rows
    assert O.WHAT_NEXT not in rows


def _plain_done(monkeypatch, capsys, code):
    from beamo_wipe.ui import console_wizard as console

    wiz, _evidence, _ = case_evidence(_case(code))

    def no_input(*_a, **_k):
        raise EOFError  # the result is printed before the first prompt

    monkeypatch.setattr("builtins.input", no_input)
    monkeypatch.setattr(wiz, "shutdown", lambda *a, **k: setattr(wiz, "wants_shutdown", True))
    console._plain_loop(wiz)
    return wiz, capsys.readouterr().out


def test_plain_console_prints_headline_list_and_technical_line(monkeypatch, capsys):
    wiz, out = _plain_done(monkeypatch, capsys, "verified")
    lines = out.splitlines()
    assert O.HEADLINE_VERIFIED in lines
    assert lines.index(O.WHAT_NEXT) < lines.index("4. " + GIVE_VERIFIED)
    assert f"{Rec.RECOVERY_TECHNICAL}: {wiz.result_technical}" in lines
    assert C.POST_ERASE_BOOT not in lines


def test_plain_console_failure_says_what_happened(monkeypatch, capsys):
    _wiz, out = _plain_done(monkeypatch, capsys, "verification_failed")
    assert APPROVED_HEADLINES["verification_failed"] in out
    assert Rec.RECOVERY_HAPPENED in out and O.MSG_VERIFICATION_FAILED in out
    assert O.WHAT_NEXT not in out.splitlines()


# --- Rendered Tk -----------------------------------------------------------------


@pytest.fixture
def live_ui():
    from beamo_wipe.ui.tk_wizard import TkWizard
    from test_tk_runtime import _needs_display

    created = []

    def build(wiz, size=(800, 600)):
        _needs_display()
        app = TkWizard(wiz)
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app._draw()
        app.root.update_idletasks()
        app.root.update()
        created.append(app)
        return app

    yield build
    for app in created:
        app._teardown()


def _labels(app):
    def walk(widget):
        yield widget
        for child in widget.winfo_children():
            yield from walk(child)

    return [str(w.cget("text")) for w in walk(app.root)
            if w.winfo_class() == "Label" and w.winfo_ismapped()]


@pytest.mark.parametrize("code", ["verified", "unverified"])
@pytest.mark.parametrize("text_size", ["standard", "large", "extra"])
def test_tk_finished_result_shows_headline_and_list(live_ui, code, text_size):
    wiz, _evidence, _ = case_evidence(_case(code))
    if text_size != "standard":
        wiz.text_size = text_size
    app = live_ui(wiz)
    texts = _labels(app)
    plain = wiz.result_plain
    assert plain.headline in texts
    assert wiz.result_view.message not in texts  # technical line is under Show more
    assert O.WHAT_NEXT in texts and plain.note in texts
    assert list(plain.numbered) == [t for t in texts if t[:3] in {"1. ", "2. ", "3. ", "4. "}]
    assert C.POST_ERASE_BOOT not in texts
    technical = f"{Rec.RECOVERY_TECHNICAL}: {wiz.result_technical}"
    assert technical not in texts
    app._more_button._command()
    app.root.update_idletasks()
    assert technical in _labels(app)


def test_tk_verified_list_is_in_the_first_view_at_800x600(live_ui):
    wiz, _evidence, _ = case_evidence(_case("verified"))
    app = live_ui(wiz)

    def walk(widget):
        yield widget
        for child in widget.winfo_children():
            yield from walk(child)

    last = next(w for w in walk(app.root) if w.winfo_class() == "Label"
                and str(w.cget("text")).startswith("4. "))
    footer_top = app._footer.winfo_rooty()
    assert last.winfo_rooty() + last.winfo_height() <= footer_top


@pytest.mark.parametrize("code", ["cancelled", "verification_failed", "engine_failed"])
def test_tk_failure_keeps_three_sections_with_the_exact_status(live_ui, code):
    wiz, _evidence, _ = case_evidence(_case(code))
    app = live_ui(wiz)
    texts = _labels(app)
    joined = "\n".join(texts)
    assert APPROVED_HEADLINES[code] in texts
    assert wiz.result_view.message in joined  # What happened, exact
    assert Rec.RECOVERY_MEANING in joined and Rec.RECOVERY_NEXT in joined
    assert O.WHAT_NEXT not in texts
