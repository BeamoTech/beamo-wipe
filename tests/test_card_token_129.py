# SPDX-License-Identifier: GPL-3.0-or-later
"""#129: the confirmation is the end of the identifier the disk card shows.

Rule (safety.confirm_spec, documented in docs/screens.md "Confirmation
characters"): the last 4 characters of the serial number the card shows, or
of the hardware ID when the disk reports no serial. More characters when
another listed disk shows the same ending. ASCII letters and digits only;
a missing or short identifier, or an ending with spaces, punctuation or
non-ASCII characters, keeps the older rule, whose prompt prints the token.
The prompt never contains a card token; the card marks it.

Comparison (decided with #156): outer whitespace is ignored and case does not
matter; nothing else is relaxed. No partial match, no auto-fill, and never
another disk's token.

Fake disks only (make_demo_wizard, DryRunRunner, SpyRunner); nothing is erased.
"""

from __future__ import annotations

import itertools
from dataclasses import replace

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.identity import present_disk
from beamo_wipe.models import DiscoveryResult, Disk, DiskKind, Screen
from beamo_wipe.safety import (
    CARD_TOKEN_MIN,
    SafetyError,
    card_identifier,
    confirm_spec,
    token_matches,
)
from beamo_wipe.ui import console_wizard as console


def _disk(name: str, serial: str = "", *, size: int = 500, wwn: str = "",
          boot: bool = False) -> Disk:
    return Disk(
        path=f"/dev/{name}",
        name=name,
        model=f"Model {name.upper()}",
        serial=serial,
        size_bytes=size * 1_000_000_000,
        size_gb_label=str(size),
        kind=DiskKind.HDD,
        bus="SATA",
        label="",
        wwn=wwn,
        is_boot=boot,
    )


def _spec(disk: Disk, *peers: Disk):
    return confirm_spec(disk, (disk, *peers))


# --- the rule --------------------------------------------------------------------


def test_normal_serial_asks_for_its_last_4_characters_without_showing_them():
    disk = _disk("sda", "S4EVNX0N123456", size=256)
    spec = _spec(disk, _disk("sdb", "WD-WCC6Y1234567", size=1000))
    assert spec.in_card and spec.identity_field == "serial"
    assert spec.token == "3456"
    assert spec.prompt == "Type the last 4 characters of the serial number shown above."
    assert spec.token not in spec.prompt
    assert spec.token not in C.confirm_prompt(spec)
    assert spec.token not in C.confirm_prompt(spec, console=True)
    view = present_disk(disk, (disk,))
    assert view.id_value[view.token_start:view.token_end] == "3456"
    assert view.token_marked_id == "S4EVNX0N12[3456]"
    # The size is no longer the token for a disk with a usable serial.
    assert not token_matches(disk.size_gb_label, spec)


def test_dash_inside_the_serial_is_fine_when_the_ending_is_plain():
    disk = _disk("sda", "WD-WCC6Y1234567")
    spec = _spec(disk)
    assert spec.in_card and spec.token == "4567"


@pytest.mark.parametrize("serial", [
    "ABC-12-3",      # dash inside the last 4
    "ABCD12 34",     # space inside the last 4
    "ABCD12.34",     # dot inside the last 4
    "ABCD1234:",     # colon at the end
    "SN-ÄÖÜ1",       # non-ASCII inside the last 4
    "シリアル番号",    # non-ASCII serial
])
def test_unusable_ending_keeps_the_older_rule_never_a_weaker_token(serial):
    disk = _disk("sda", serial, size=750)
    spec = _spec(disk)
    assert not spec.in_card
    assert spec.identity_field == "size" and spec.token == "750"
    assert spec.token in spec.prompt  # older prompt, unchanged
    view = present_disk(disk, (disk,))
    assert view.token_end == view.token_start == 0
    assert view.token_marked_id == view.id_value


@pytest.mark.parametrize("serial", ["", "   ", "0000000", "N/A", "ABC", "A1"])
def test_missing_or_short_serial_without_hardware_id_keeps_the_older_rule(serial):
    disk = _disk("sda", serial, size=750)
    spec = _spec(disk)
    assert not spec.in_card
    assert spec.token == "750"


def test_missing_serial_uses_the_hardware_id_the_card_shows():
    disk = _disk("sda", "", wwn="0x5000c500a1b2c3d4")
    assert card_identifier(disk) == ("wwn", "0x5000c500a1b2c3d4")
    spec = _spec(disk)
    assert spec.in_card and spec.identity_field == "wwn"
    assert spec.token == "c3d4"
    assert spec.prompt == "Type the last 4 characters of the hardware ID shown above."
    view = present_disk(disk, (disk,))
    assert view.id_label == "Hardware ID"
    assert view.token_marked_id == "0x5000c500a1b2[c3d4]"


def test_serial_of_exactly_4_characters_is_typed_whole():
    disk = _disk("vda", "0001", size=0)
    spec = _spec(disk, _disk("sr0", "", size=0, boot=True))
    assert spec.in_card and spec.token == "0001"
    assert "last 4 characters" in spec.prompt


def test_duplicate_ending_requires_more_characters_and_says_so():
    first = _disk("sda", "AAAA1234")
    second = _disk("sdb", "BBBB1234")
    one, two = _spec(first, second), _spec(second, first)
    assert (one.token, two.token) == ("A1234", "B1234")
    for spec in (one, two):
        assert spec.in_card
        assert spec.prompt.startswith("Type the last 5 characters of the serial number shown above.")
        assert C.CONFIRM_LONGER in spec.prompt
        assert spec.token not in spec.prompt
    assert not token_matches("1234", one)
    assert not token_matches(two.token, one)
    assert present_disk(first, (first, second)).token_marked_id == "AAA[A1234]"


def test_whole_identifier_is_asked_for_when_only_all_of_it_differs():
    first = _disk("sda", "X1234")
    second = _disk("sdb", "Y1234")
    spec = _spec(first, second)
    assert spec.token == "X1234"
    assert spec.prompt.startswith(C.CONFIRM_SERIAL_ALL)


def test_ending_shared_with_the_protected_boot_usb_is_not_enough():
    target = _disk("sda", "HDDSERIAL0001", size=16)
    boot = _disk("sdb", "BEAMOUSB0001", size=16, boot=True)
    spec = _spec(target, boot)
    assert spec.token == "L0001"
    assert not token_matches("0001", spec)


def test_ending_equal_to_another_disks_size_is_not_used():
    target = _disk("sda", "SERIAL1000", size=500)
    other = _disk("sdb", "OTHERDISK9", size=1000)
    spec = _spec(target, other)
    assert spec.token == "L1000"
    assert not token_matches("1000", spec)


def test_duplicate_serials_fall_back_to_the_older_rule():
    first = _disk("sda", "SAMESERIAL", size=500)
    second = _disk("sdb", "SAMESERIAL", size=1000)
    assert not _spec(first, second).in_card
    assert _spec(first, second).token == "500"


def test_duplicate_serials_of_the_same_size_cannot_be_confirmed():
    first = _disk("sda", "SAMESERIAL")
    second = _disk("sdb", "SAMESERIAL")
    with pytest.raises(SafetyError):
        _spec(first, second)


# --- never another disk's token, never partial ----------------------------------

SERIALS = ("AAAA1234", "BBBB1234", "CCCC5678", "1234", "X0001", "", "WD-1A2B", "ZZ:9999")
WWNS = ("", "0x5000c500a1b21234", "5000c500a1b25678")


def _fleet():
    disks = []
    for i, (serial, wwn) in enumerate(itertools.product(SERIALS, WWNS)):
        disks.append(_disk(f"sd{chr(97 + i % 26)}{i}", serial, size=(500, 1000, 256)[i % 3], wwn=wwn))
    return disks


@pytest.mark.parametrize("size", [3, 4, 5])
def test_no_disk_accepts_another_listed_disks_token(size):
    """Every pair from many mixed sets: a token binds exactly one disk."""
    fleet = _fleet()
    checked = 0
    for group in itertools.combinations(fleet, size):
        specs = {}
        for disk in group:
            try:
                specs[disk.path] = confirm_spec(disk, group)
            except SafetyError:
                continue
        for a, b in itertools.permutations(specs, 2):
            assert not token_matches(specs[b].token, specs[a]), (group, a, b)
            checked += 1
        if checked > 4000:
            break
    assert checked > 100


@pytest.mark.parametrize("typed", ["", "345", "456", "23456", "3 456", "34 56", "3456x", "x3456", "S4EVNX0N123456"])
def test_partial_padded_or_longer_input_is_rejected(typed):
    spec = _spec(_disk("sda", "S4EVNX0N123456"))
    assert not token_matches(typed, spec)


@pytest.mark.parametrize("typed", ["3456", " 3456", "3456 ", "\t3456\n"])
def test_outer_whitespace_is_ignored_156(typed):
    assert token_matches(typed, _spec(_disk("sda", "S4EVNX0N123456")))


def test_case_does_not_matter_156():
    spec = _spec(_disk("sda", "MX500AABBCC11"))
    assert spec.token == "CC11"
    assert token_matches("cc11", spec) and token_matches("Cc11", spec)


def test_confirm_never_starts_filled_in():
    wiz = make_demo_wizard()
    wiz.skip_intro()
    wiz.accept_what()
    wiz.set_owner(True)
    wiz.continue_owner()
    wiz.select_disk(sorted(wiz.selectable, key=lambda d: d.path)[0].path)
    wiz.continue_pick()
    assert wiz.screen == Screen.CONFIRM
    assert wiz.confirm_input == "" and not wiz.token_ok
    wiz.continue_confirm()
    assert wiz.screen == Screen.CONFIRM


# --- bound to the rediscovered identity -------------------------------------------


def _ready(tmp_path, monkeypatch):
    from test_boot_exclusion_fails_closed import _make_wizard_ready_for_erase

    return _make_wizard_ready_for_erase(tmp_path, monkeypatch)


def _rediscover_with(wiz, *changed: Disk):
    by_path = {d.path: d for d in changed}
    fresh = DiscoveryResult(
        disks=tuple(by_path.get(d.path, d) for d in wiz.discovery.disks)
        + tuple(d for d in changed if d.path not in {x.path for x in wiz.discovery.disks}),
        selectable=tuple(by_path.get(d.path, d) for d in wiz.discovery.selectable)
        + tuple(d for d in changed if d.path not in {x.path for x in wiz.discovery.selectable}),
        boot=wiz.discovery.boot,
        boot_identified=True,
    )
    wiz._rediscover = lambda: fresh  # type: ignore[attr-defined]


def test_serial_change_that_keeps_the_same_ending_is_still_rejected(tmp_path, monkeypatch):
    wiz, spy, _, target = _ready(tmp_path, monkeypatch)
    spec = confirm_spec(target, wiz.listed_disks)
    assert spec.in_card
    changed = replace(target, serial="DIFFERENT" + target.serial[-CARD_TOKEN_MIN:])
    assert changed.serial.endswith(spec.token)
    _rediscover_with(wiz, changed)
    wiz.confirm_erase()
    assert wiz.error is not None
    assert spy.start_calls == []


@pytest.mark.parametrize("field,value", [("size_bytes", 1), ("wwn", "0x5000c500deadbeef"), ("path", "/dev/sdz")])
def test_other_identity_changes_are_rejected(tmp_path, monkeypatch, field, value):
    wiz, spy, _, target = _ready(tmp_path, monkeypatch)
    if field == "size_bytes":
        changed = replace(target, size_bytes=target.size_bytes + value)
    else:
        changed = replace(target, **{field: value})
    _rediscover_with(wiz, changed)
    wiz.confirm_erase()
    assert wiz.error is not None
    assert spy.start_calls == []


def test_a_new_disk_sharing_the_ending_makes_the_typed_token_insufficient(tmp_path, monkeypatch):
    """The token is recomputed from the rediscovered list at launch."""
    from beamo_wipe import safety

    wiz, spy, _, target = _ready(tmp_path, monkeypatch)
    typed = wiz.confirm_input
    lookalike = _disk("sdq", "LOOKALIKE" + target.serial[-CARD_TOKEN_MIN:], size=int(target.size_gb_label) + 1)
    fresh = DiscoveryResult(
        disks=wiz.discovery.disks + (lookalike,),
        selectable=wiz.discovery.selectable + (lookalike,),
        boot=wiz.discovery.boot,
        boot_identified=True,
    )
    assert len(confirm_spec(target, safety.listed_disks(fresh)).token) > len(typed)
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    with pytest.raises(SafetyError, match=safety.TOKEN_MISMATCH):
        safety.assert_ready_to_wipe(
            owner_ok=True,
            disk=target,
            discovery=fresh,
            typed_token=typed,
            countdown_complete=True,
            method=wiz.method,
        )
    assert spy.start_calls == []


# --- every surface shows the same instruction and mark ----------------------------


def _at_confirm(serial: str = "") -> object:
    wiz = make_demo_wizard()
    wiz.skip_intro()
    wiz.accept_what()
    wiz.set_owner(True)
    wiz.continue_owner()
    disk = sorted(wiz.selectable, key=lambda d: d.path)[0]
    wiz.select_disk(disk.path)
    if serial:
        wiz.selected = replace(wiz.selected, serial=serial)
    wiz.continue_pick()
    assert wiz.screen == Screen.CONFIRM
    return wiz


class _Tall:
    def __init__(self, wizard):
        self.wizard, self.h, self.w = wizard, 300, 80
        self.rows, self.frames = {}, []

    def getmaxyx(self):
        return self.h, self.w

    def addstr(self, y, x, text, attr=0):
        self.rows[y] = text if x == 0 else (" " * x + text)

    def erase(self):
        if self.rows:
            self.frames.append(dict(self.rows))
        self.rows = {}

    def getch(self):
        self.frames.append(dict(self.rows))
        self.wizard.wants_shutdown = True
        return -1

    def __getattr__(self, name):
        return lambda *a, **k: None


def test_curses_brackets_the_characters_and_never_prints_them_alone(monkeypatch):
    wiz = _at_confirm()
    spec = wiz.confirm
    for name in ("curs_set", "use_default_colors", "echo", "noecho"):
        monkeypatch.setattr(console.curses, name, lambda *a, **k: None)
    term = _Tall(wiz)
    console._loop(term, wiz)
    frame = term.frames[-1]
    shown = " ".join(" ".join(frame[y] for y in sorted(frame)).split())
    view = wiz.disk_view(wiz.selected)
    assert f"{view.id_label}: {view.token_marked_id}" in shown
    assert C.confirm_prompt(spec, console=True) in shown
    # The characters appear only inside the identifier, bracketed.
    assert shown.count(spec.token) == 1
    assert not wiz.runner.started


def test_plain_console_brackets_the_characters(monkeypatch, capsys):
    wiz = _at_confirm()
    spec = wiz.confirm
    monkeypatch.setattr("builtins.input", lambda *_: (_ for _ in ()).throw(EOFError()))
    console._plain_loop(wiz)
    shown = " ".join(capsys.readouterr().out.split())
    view = wiz.disk_view(wiz.selected)
    assert f"{view.id_label}: {view.token_marked_id}" in shown
    assert C.confirm_prompt(spec, console=True) in shown
    assert shown.count(spec.token) == 1


def test_gallery_marks_the_characters_and_prompt_omits_them():
    import json
    import re

    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    payload = json.loads(re.search(r"const P = (\{.*?\});\n", html, re.S).group(1))
    for disk in payload["disks"]:
        if disk["isBoot"] or not disk["eligible"]:
            continue
        assert disk["tokenEnd"] > disk["tokenStart"]
        assert disk["serial"][disk["tokenStart"]:disk["tokenEnd"]] == disk["token"]
        assert disk["token"] not in disk["prompt"]
        assert C.CONFIRM_MARKED in disk["prompt"]
    assert '<mark class="token-mark">' in html
    assert ".token-mark {" in html and "text-decoration: underline" in html


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_every_language_names_the_field_and_never_the_characters(code):
    lang.set_language(code)
    try:
        for field in ("serial", "wwn"):
            for count, whole, longer in ((4, False, False), (5, False, True), (6, True, True)):
                text = C.confirm_type_card(field, count, whole=whole, longer=longer)
                if not whole:
                    assert str(count) in text
                assert "{" not in text
        assert C.CONFIRM_MARKED and C.CONFIRM_MARKED_CONSOLE
        assert "[" in C.CONFIRM_MARKED_CONSOLE
    finally:
        lang.set_language("en")


# --- Tk: the box and underline sit on the characters ----------------------------


@pytest.mark.parametrize("text_size", ["standard", "large"])
@pytest.mark.parametrize("size", [(800, 600), (1280, 820)], ids=lambda s: f"{s[0]}x{s[1]}")
def test_tk_boxes_and_underlines_the_characters_in_place(tk_app, size, text_size):  # noqa: F811
    from test_tk_runtime import _drive_to
    from test_ui_fit_20261027 import _descendants, _settle

    wiz, app = tk_app(size=size)
    if text_size != "standard":
        assert wiz.set_text_size(text_size)
        app._sync_layout()
    _drive_to(wiz, app, Screen.PICK, size=size)
    wiz.select_disk(sorted(wiz.selectable, key=lambda d: d.path)[0].path)
    wiz.continue_pick()
    app._draw()
    _settle(app, 80)
    spec, view = wiz.confirm, wiz.disk_view(wiz.selected)
    labels = [w for w in _descendants(app._body) if w.winfo_class() == "Label" and w.winfo_ismapped()]
    texts = [str(w.cget("text")) for w in labels]
    # The whole identifier stays one label; the prompt names, never shows, the characters.
    ident = next(w for w in labels if str(w.cget("text")) == view.id_value)
    assert C.confirm_prompt(spec) in texts
    assert not any(spec.token in t for t in texts if t not in (view.id_value, spec.token))
    marks = [w for w in _descendants(app._body) if getattr(w, "_beamo_token_mark", False)]
    frame = next(w for w in marks if w.winfo_class() == "Frame")
    chars = next(w for w in marks if w.winfo_class() == "Label")
    assert chars.cget("text") == spec.token and frame.winfo_ismapped()
    # A box (dark frame around the characters) plus an underline bar: not colour only.
    from beamo_wipe.ui import tk_wizard as tkui

    assert frame.cget("bg") == tkui.INK
    bar = [w for w in frame.winfo_children() if w is not chars]
    assert len(bar) == 1 and int(bar[0].cget("height")) == 2
    assert chars.cget("bg") == tkui.CONFIRM_MARK_BG
    # Placed over the identifier's last characters.
    font = app.font_mono_bold
    head = view.id_value[: view.token_start]
    x = chars.winfo_rootx() - ident.winfo_rootx()
    start = int(ident.cget("bd")) + int(ident.cget("highlightthickness")) + int(ident.cget("padx"))
    assert abs(x - (start + font.measure(head))) <= 1
    assert ident.winfo_rooty() <= chars.winfo_rooty() <= ident.winfo_rooty() + ident.winfo_height()
    assert not wiz.runner.started


from test_ui_fit_20261027 import tk_app  # noqa: E402,F401  (fixture)
