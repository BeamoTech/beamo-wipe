# SPDX-License-Identifier: GPL-3.0-or-later
"""#156: show which typed character is wrong; the gate itself is unchanged.

Comparison (safety.token_matches, decided with #129/#156 and documented in
docs/screens.md): leading/trailing whitespace is ignored and letter case does
not matter. Inner spaces count, so do wrong, missing or extra characters, and
another disk's token never matches. After a wrong entry Confirm shows what
was typed with the wrong characters in [brackets] and which positions are
wrong, missing or extra; it never prints an expected character. The
five-second review and the separate Erase now are unchanged. Fake disks only.
"""

from __future__ import annotations

from dataclasses import replace
import re
import string

import pytest

from beamo_wipe import copy as C, lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Disk, DiskKind, Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.safety import confirm_spec, token_matches
from beamo_wipe.token_feedback import SPACE_GLYPH, feedback
from beamo_wipe.wizard import Wizard


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _disk(path, serial, size="500"):
    return Disk(path=path, name=path[5:], model="Same model", serial=serial, size_bytes=int(size) * 10**9,
                size_gb_label=size, kind=DiskKind.HDD, bus="SATA", label="")


# -- the gate (unchanged) ----------------------------------------------------------


@pytest.mark.parametrize("typed", ["3456", " 3456", "3456 ", "\t3456\n", "  3456  "])
def test_leading_and_trailing_spaces_are_accepted(typed):
    spec = confirm_spec(_disk("/dev/sda", "S4EVNX0N123456"), [_disk("/dev/sda", "S4EVNX0N123456")])
    assert token_matches(typed, spec)


@pytest.mark.parametrize("typed", ["34 56", "3 456", "345 6", "3\t456"])
def test_inner_spaces_are_not_ignored(typed):
    spec = confirm_spec(_disk("/dev/sda", "S4EVNX0N123456"), [_disk("/dev/sda", "S4EVNX0N123456")])
    assert not token_matches(typed, spec)


def test_case_rule_letters_match_in_any_case_and_nothing_else_is_relaxed():
    disk = _disk("/dev/sda", "MX500AABBCC11")
    spec = confirm_spec(disk, [disk])
    assert spec.token == "CC11"
    for typed in ("CC11", "cc11", "Cc11", "cC11"):
        assert token_matches(typed, spec)
    for typed in ("CC1", "CC111", "CO11", "C C11", "CCl1", "0C11"):
        assert not token_matches(typed, spec)


def test_another_disks_token_never_matches():
    a, b = _disk("/dev/sda", "S4EVNX0N123456"), _disk("/dev/sdb", "S4EVNX0N987654")
    sa, sb = confirm_spec(a, [a, b]), confirm_spec(b, [a, b])
    assert sa.token != sb.token
    assert not token_matches(sb.token, sa) and not token_matches(sa.token, sb)
    # Feedback for the other disk's token marks every differing character.
    fb = feedback(sb.token, sa.token)
    assert fb is not None and fb.wrong


# -- the feedback --------------------------------------------------------------------


@pytest.mark.parametrize("position", range(4))
def test_each_wrong_position_is_reported(position):
    token = "3456"
    typed = token[:position] + "9" + token[position + 1:]
    fb = feedback(typed, token)
    assert fb.wrong == (position,)
    assert fb.message == f"Character {position + 1} doesn't match."
    cells = fb.display.removeprefix("You typed: ").split(" ")
    assert cells[position] == "[9]"
    assert [c for i, c in enumerate(cells) if i != position] == [ch for i, ch in enumerate(token) if i != position]


def test_several_wrong_positions_missing_and_extra():
    assert feedback("9459", "3456").message == "Characters 1 and 4 don't match."
    assert feedback("9999", "3456").message == "Characters 1, 2, 3 and 4 don't match."
    assert feedback("345", "3456").message == "1 character is missing."
    assert feedback("3", "3456").message == "3 characters are missing."
    assert feedback("34567", "3456").display == "You typed: 3 4 5 6 [7]"
    assert feedback("3456789", "3456").message == "3 characters too many."
    assert feedback("x", "3456").message == "Character 1 doesn't match. 3 characters are missing."


def test_a_stray_inner_space_is_marked_on_its_own():
    fb = feedback("34 56", "3456")
    assert fb.display == f"You typed: 3 4 [{SPACE_GLYPH}] 5 6"
    assert fb.message == "Spaces between characters count; remove them."
    fb = feedback("34 76", "3456")
    assert fb.wrong == (2,) and "Character 3 doesn't match." in fb.message


def test_matching_or_empty_entries_have_no_feedback():
    for typed in ("3456", " 3456 ", "", "   "):
        assert feedback(typed, "3456") is None
    assert feedback("cc11", "CC11") is None  # the case rule, as in the gate


@pytest.mark.parametrize("typed", ["QZXX", "Q", "QZXJA", "Q ZXJ", "qzxj ", "AZXJ"])
def test_feedback_never_reveals_expected_characters(typed):
    token = "QZXJ"
    fb = feedback(typed, token)
    if fb is None:
        assert token_matches(typed, replace(_spec_stub(), token=token))
        return
    shown = fb.display.removeprefix("You typed: ").replace("[", "").replace("]", "").replace(" ", "")
    assert shown == typed.strip().replace(" ", SPACE_GLYPH)  # only what was typed
    for ch in set(token) - set(typed.upper()):
        assert ch not in fb.message and ch not in fb.display and ch not in fb.spoken


def _spec_stub():
    disk = _disk("/dev/sda", "AAAAQZXJ")
    return confirm_spec(disk, [disk])


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_every_language_has_the_feedback_copy(code):
    def get(key):
        return getattr(C, key) if code == "en" else lang.translated(code, "copy", key)

    expected = {"TOKEN_TYPED": {"typed"}, "TOKEN_WRONG_ONE": {"n"}, "TOKEN_WRONG_MANY": {"list"},
                "TOKEN_MISSING_ONE": set(), "TOKEN_MISSING_MANY": {"count"}, "TOKEN_EXTRA_ONE": set(),
                "TOKEN_EXTRA_MANY": {"count"}, "TOKEN_SPACE_NOTE": set(), "TOKEN_SPACE_WORD": set()}
    for key, fields in expected.items():
        assert {n for _, n, _, _ in string.Formatter().parse(get(key)) if n} == fields, (code, key)


# -- wizard: timing and gates --------------------------------------------------------


class _Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def _confirm(clock=None):
    base = make_demo_wizard()
    wiz = Wizard(base.discovery, DryRunRunner(clock=clock) if clock else DryRunRunner(),
                 clock=clock, dry_run=True) if clock else base
    wiz.preview = False
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    wiz.select_disk(sorted(d.path for d in wiz.selectable)[0])
    wiz.continue_pick()
    assert wiz.screen == Screen.CONFIRM
    return wiz


def test_feedback_appears_with_the_wrong_entry_and_goes_on_a_match():
    wiz = _confirm()
    token = wiz.confirm.token
    assert wiz.confirm_feedback is None
    wiz.set_confirm_input(token[:2])  # still typing
    assert wiz.confirm_feedback is None
    wrong = token[:2] + ("Z" if token[2].upper() != "Z" else "Y") + token[3:]
    wiz.set_confirm_input(wrong)
    fb = wiz.confirm_feedback
    assert fb is not None and fb.wrong == (2,) and wiz.screen == Screen.CONFIRM
    wiz.set_confirm_input(token[:2])
    assert wiz.confirm_feedback.message.endswith("missing.")
    wiz.set_confirm_input(f"  {token.lower()} ")
    assert wiz.token_ok and wiz.confirm_feedback is None


def test_enter_on_a_short_wrong_entry_explains_and_never_advances():
    wiz = _confirm()
    wiz.set_confirm_input("Z")
    wiz.continue_confirm()
    assert wiz.screen == Screen.CONFIRM
    assert wiz.confirm_feedback is not None
    assert wiz._authorized_operation is None


def test_feedback_is_display_only_and_the_review_gates_are_unchanged():
    clock = _Clock()
    wiz = _confirm(clock)
    token = wiz.confirm.token
    wiz.set_confirm_input(token + "X")
    assert wiz.confirm_feedback is not None
    wiz.continue_confirm()
    assert wiz.screen == Screen.CONFIRM  # wrong: no way forward
    wiz.set_confirm_input(f" {token} ")
    wiz.continue_confirm()
    assert wiz.screen == Screen.METHOD
    wiz.continue_method()
    assert wiz.screen == Screen.LAST_CHANCE
    assert not wiz.erase_enabled and wiz.countdown_display == 5
    wiz.confirm_erase()
    assert not wiz.runner.started  # the countdown still governs
    clock.t += 5.0
    assert wiz.erase_enabled
    assert wiz.screen == Screen.LAST_CHANCE and not wiz.runner.started  # Erase now is separate


def test_only_presentation_code_reads_the_feedback():
    from pathlib import Path

    src = Path(__file__).resolve().parents[1] / "src" / "beamo_wipe"
    importer = re.compile(r"^\s*(from beamo_wipe\.token_feedback import|from beamo_wipe import .*\btoken_feedback\b"
                          r"|import beamo_wipe\.token_feedback)", re.M)
    users = sorted(p.relative_to(src).as_posix() for p in src.rglob("*.py")
                   if importer.search(p.read_text(encoding="utf-8")))
    # Only the wizard's display property imports it; views read that property.
    assert users == ["wizard.py"], users
    wizard_src = (src / "wizard.py").read_text(encoding="utf-8")
    gate = wizard_src[wizard_src.index("    def token_ok(self) -> bool:"):]
    gate = gate[:gate.index("\n    @property", 10)]
    assert "token_matches(self.confirm_input, spec)" in gate and "feedback" not in gate
    for name in ("safety.py", "nwipe_runner.py", "discover.py"):
        assert "token_feedback" not in (src / name).read_text(encoding="utf-8")


# -- views ---------------------------------------------------------------------------


def test_plain_console_prints_the_feedback(monkeypatch):
    from beamo_wipe.ui.console_wizard import _plain_loop

    wiz = _confirm()
    token = wiz.confirm.token
    wrong = token[:-1] + ("Z" if token[-1].upper() != "Z" else "Y")
    answers = iter([wrong])
    printed, rounds = [], []

    def fake_input(_prompt=""):
        rounds.append("\n".join(printed))
        try:
            return next(answers)
        except StopIteration:
            wiz.shutdown()
            return ""

    monkeypatch.setattr("builtins.print", lambda *a, **_k: printed.append(" ".join(map(str, a))))
    monkeypatch.setattr("builtins.input", fake_input)
    _plain_loop(wiz)
    assert "You typed:" not in rounds[0]
    assert f"[{wrong[-1]}]" in rounds[1] and f"Character {len(token)} doesn't match." in rounds[1]


def test_curses_confirm_shows_the_feedback(monkeypatch):
    from beamo_wipe.ui import console_wizard as console

    wiz = _confirm()
    token = wiz.confirm.token
    painted = []
    keys = iter([*(ord(c) for c in token[:-1]), ord("#"), -1, -1])

    class Terminal:
        def getmaxyx(self):
            return 24, 80

        def keypad(self, *_a):
            pass

        def nodelay(self, *_a):
            pass

        def timeout(self, *_a):
            pass

        def erase(self):
            pass

        def addstr(self, *args):
            painted.append(str(args[2]) if len(args) > 2 else "")

        def refresh(self):
            pass

        def getch(self):
            try:
                return next(keys)
            except StopIteration:
                wiz.wants_shutdown = True
                return -1

    now = [0.0]

    def monotonic():
        now[0] += 1.0
        return now[0]

    monkeypatch.setattr("beamo_wipe.startup_stages._emit", lambda *_a: None)
    monkeypatch.setattr(console, "_curses_opt", lambda *_a: None)
    monkeypatch.setattr(console.time, "sleep", lambda *_a: None)
    monkeypatch.setattr(console.time, "monotonic", monotonic)
    assert console._loop(Terminal(), wiz) == 0
    text = "\n".join(painted)
    assert "[#]" in text and f"Character {len(token)} doesn't match." in text
    assert wiz.screen == Screen.CONFIRM


def test_gtk_source_shows_and_speaks_the_feedback():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "src/beamo_wipe/ui/accessible_wizard.py").read_text(
        encoding="utf-8")
    assert 'self.token_feedback = self.label("", focusable=True)' in source
    sync = source[source.index("    def _sync_layout_hint(self) -> None:"):]
    sync = sync[:sync.index("\n    def ", 10)]
    assert "fb = self.w.confirm_feedback" in sync
    assert 'label.set_text(f"{fb.display}\\n{fb.message}")' in sync
    assert "label.get_accessible().set_name(fb.spoken)" in sync


def test_preview_payload_and_source():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    assert "function tokenFeedback(typed, wantRaw)" in html
    assert 'const fb = confirmMismatch && !tokenOk() ? tokenFeedback(token, d.token) : null;' in html
    assert '<p class="mono token-typed" id="token-typed"></p>' in html
    assert '"spaceNote": ' in html and C.TOKEN_SPACE_NOTE in html


@pytest.mark.parametrize("size,text_size", [((800, 600), "standard"), ((800, 600), "extra"),
                                            ((1280, 820), "standard")])
def test_tk_shows_the_typed_value_and_problem_after_a_wrong_entry(size, text_size):
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    wiz = _confirm()
    wiz.text_size = text_size
    app = TkWizard(wiz)
    try:
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app._draw()
        for _ in range(6):
            app.root.update()
        # #157: the status line under the entry carries the feedback.
        status = app._match_label
        assert "You typed:" not in str(status.cget("text"))
        token = wiz.confirm.token
        wrong = ("Z" if token[0].upper() != "Z" else "Y") + token[1:]
        app._confirm_var.set(wrong)
        for _ in range(6):
            app.root.update()
        typed_line, problem_line = str(status.cget("text")).split("\n")
        assert typed_line == "You typed: " + " ".join([f"[{wrong[0]}]", *token[1:]])
        assert problem_line == "Character 1 doesn't match."
        assert status.winfo_ismapped()
        # Order: the status (typed value, problem), then the #155 keyboard sentence.
        assert app._match_pill.winfo_y() < app._layout_hint.winfo_y()
        app._confirm_var.set(token)
        for _ in range(4):
            app.root.update()
        assert wiz.token_ok
        assert not app._layout_hint.winfo_manager()
    finally:
        app._teardown()
