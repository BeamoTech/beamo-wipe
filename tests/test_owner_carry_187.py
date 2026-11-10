# SPDX-License-Identifier: GPL-3.0-or-later
"""#187: the ownership tick carries over to the next erase in the same app run.

Owner-approved policy (2026-11-06): option A — the Owner screen is skipped
after Erase another disk while the fresh discovery lists no erasable disk the
owner did not confirm; a new or unmatched disk asks again; each report says
whether ownership was confirmed on screen or carried over. Every per-disk gate
(fresh discovery, selection, exact token, five-second review, separate Erase
now) is unchanged. All disks are fake.
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from beamo_wipe import app
from beamo_wipe import copy as C
from beamo_wipe import owner_carry as oc
from beamo_wipe.evidence import build_evidence
from beamo_wipe.models import DiscoveryResult, MethodId, Screen, WipeResult
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.safety import SafetyError, assert_ready_to_wipe
from beamo_wipe.wizard import Wizard, make_demo_wizard


class Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def add(self, s: float) -> None:
        self.t += s


def _wiz(discovery=None):
    base = make_demo_wizard()
    clock = Clock()
    runner = DryRunRunner(duration_s=1.0, clock=clock)
    wiz = Wizard(discovery or base.discovery, runner, clock=clock, dry_run=True)
    return wiz, clock


def _to_owner(wiz):
    wiz.skip_splash()
    assert wiz.screen == Screen.KEYBOARD
    wiz.accept_keyboard()  # the real exit from Keyboard in every UI


def _tick_and_continue(wiz):
    _to_owner(wiz)
    assert wiz.screen == Screen.OWNER and not wiz.owner_ok
    wiz.set_owner(True)
    wiz.continue_owner()
    assert wiz.screen == Screen.PICK


def _finished(wiz, code="verified"):
    """Pretend this session's erase finished with the given result code."""
    wiz.selected = wiz.selectable[0]
    wiz.screen = Screen.DONE
    wiz.wipe_result = WipeResult(code in {"verified", "unverified"}, 0, "done", "")
    wiz._result_code_for_test = code


def _handoff_after(wiz, monkeypatch, code="verified"):
    """Erase another disk from DONE; returns what the app loop would carry."""
    _finished(wiz, code)
    monkeypatch.setattr(type(wiz), "result_view", property(
        lambda self: type("V", (), {"code": getattr(self, "_result_code_for_test", "")})()))
    monkeypatch.setattr(Wizard, "can_erase_another", property(lambda self: self.screen == Screen.DONE))
    monkeypatch.setattr(Wizard, "_has_verified_export_locked", lambda self: True)
    wiz.erase_another_disk()
    assert wiz.wants_new_session
    return wiz.take_handoff()


def _without(discovery, path):
    keep = tuple(d for d in discovery.selectable if d.path != path)
    return dataclasses.replace(discovery, selectable=keep,
                               disks=tuple(d for d in discovery.disks if d.path != path))


# --- identity binding ------------------------------------------------------------


def test_capture_and_cover_by_identity_not_path():
    wiz, _ = _wiz()
    disks = list(wiz.selectable)
    carry = oc.capture(disks)
    assert carry is not None and len(carry.covered) == len(disks)
    assert carry.covers(disks)
    assert carry.covers(disks[:1])  # fewer disks (one was erased and removed)
    moved = [dataclasses.replace(d, path=d.path + "x", name=d.name + "x") for d in disks]
    assert carry.covers(moved)  # /dev names can change between starts
    resized = [dataclasses.replace(disks[0], size_bytes=disks[0].size_bytes + 512)]
    assert not carry.covers(resized)
    other_serial = [dataclasses.replace(disks[0], serial="NEWSERIAL1", wwn="")]
    assert not carry.covers(other_serial)


def test_unidentifiable_or_duplicate_disks_never_carry():
    wiz, _ = _wiz()
    disk = wiz.selectable[0]
    blank = dataclasses.replace(disk, serial="", wwn="")
    assert oc.disk_key(blank) is None
    assert oc.capture([blank]) is None
    assert oc.capture([disk, dataclasses.replace(disk, path="/dev/sdq")]) is None  # same identity twice
    carry = oc.capture([disk])
    assert not carry.covers([disk, blank])
    assert not carry.covers([])
    assert oc.disk_key(wiz.discovery.boot) is None  # the Beamo USB is never a key


# --- one app run only -----------------------------------------------------------


def test_a_fresh_wizard_always_starts_unticked():
    wiz, _ = _wiz()
    _to_owner(wiz)
    assert wiz.screen == Screen.OWNER
    assert not wiz.owner_ok and wiz.owner_source == "" and not wiz.owner_carried


def test_only_erase_another_disk_hands_the_tick_over(monkeypatch):
    wiz, _ = _wiz()
    _tick_and_continue(wiz)
    assert wiz.owner_source == oc.SOURCE_ON_SCREEN
    # Nothing to hand over unless the session ends with Erase another disk.
    assert wiz.take_handoff() == (None, ())
    carry, history = _handoff_after(wiz, monkeypatch)
    assert isinstance(carry, oc.OwnerCarry)
    assert carry.covers(_wiz()[0].selectable)
    assert [m.state for m in history] == [oc.ERASED_CHECKED]
    # The ending session itself is unticked, and the hand-off is read once.
    assert not wiz.owner_ok and wiz.owner_source == ""
    assert wiz.take_handoff() == (None, ())


def test_a_tick_set_directly_or_cleared_never_carries(monkeypatch):
    wiz, _ = _wiz()
    _tick_and_continue(wiz)
    wiz.screen = Screen.OWNER
    wiz.set_owner(False)
    wiz.set_owner(True)  # ticked again but not continued: covers nothing yet
    carry, _history = _handoff_after(wiz, monkeypatch)
    assert carry is None


def test_carried_tick_skips_owner_and_is_shown_on_pick(monkeypatch):
    first, _ = _wiz()
    _tick_and_continue(first)
    carry, history = _handoff_after(first, monkeypatch)
    second, _ = _wiz()
    second.offer_owner_carry(carry, history)
    assert not second.owner_ok  # offering alone never ticks the box
    _to_owner(second)
    assert second.screen == Screen.PICK
    assert second.owner_ok and second.owner_carried
    assert second.owner_source == oc.SOURCE_CARRIED
    # Used once: Back to Owner and on again keeps the same source and set.
    assert second._owner_carry_in is None


def test_offer_is_refused_after_the_session_moved_on(monkeypatch):
    first, _ = _wiz()
    _tick_and_continue(first)
    carry, history = _handoff_after(first, monkeypatch)
    late, _ = _wiz()
    _tick_and_continue(late)
    late.screen = Screen.OWNER
    late.set_owner(False)
    late.offer_owner_carry(carry, history)  # not at Splash/Keyboard: ignored
    assert late._owner_carry_in is None and not late.owner_ok


def test_new_disk_asks_again(monkeypatch):
    base = make_demo_wizard().discovery
    removed = base.selectable[-1].path
    first, _ = _wiz(_without(base, removed))
    _tick_and_continue(first)
    carry, history = _handoff_after(first, monkeypatch)
    second, _ = _wiz(base)  # the disk was connected after the tick
    second.offer_owner_carry(carry, history)
    _to_owner(second)
    assert second.screen == Screen.OWNER
    assert not second.owner_ok and second.owner_source == ""
    assert second.owner_carry_note == C.OWNER_CARRY_NEW_DISK
    second.set_owner(True)
    second.continue_owner()
    assert second.owner_source == oc.SOURCE_ON_SCREEN and second.owner_carry_note == ""


def test_unmatched_disk_asks_again(monkeypatch):
    base = make_demo_wizard().discovery
    first, _ = _wiz(base)
    _tick_and_continue(first)
    carry, history = _handoff_after(first, monkeypatch)
    blank = dataclasses.replace(base.selectable[0], serial="", wwn="")
    changed = dataclasses.replace(base, selectable=(blank,) + base.selectable[1:])
    second, _ = _wiz(changed)
    second.offer_owner_carry(carry, history)
    _to_owner(second)
    assert second.screen == Screen.OWNER and not second.owner_ok
    assert second.owner_carry_note == C.OWNER_CARRY_UNSURE


def test_blocked_or_empty_discovery_never_ticks(monkeypatch):
    first, _ = _wiz()
    _tick_and_continue(first)
    carry, history = _handoff_after(first, monkeypatch)
    for discovery in (DiscoveryResult(error="x", boot_identified=False),
                      dataclasses.replace(make_demo_wizard().discovery, selectable=())):
        second, _ = _wiz(discovery)
        second.offer_owner_carry(carry, history)
        _to_owner(second)
        assert not second.owner_ok and second.screen == Screen.OWNER


def test_change_returns_to_owner_unticked_and_stops_the_carry(monkeypatch):
    first, _ = _wiz()
    _tick_and_continue(first)
    carry, history = _handoff_after(first, monkeypatch)
    second, _ = _wiz()
    second.offer_owner_carry(carry, history)
    _to_owner(second)
    second.select_disk(second.selectable[0].path)
    second.change_ownership()
    assert second.screen == Screen.OWNER
    assert not second.owner_ok and second.selected is None and second._owner_carry_out is None
    second.continue_owner()
    assert second.screen == Screen.OWNER  # cannot continue unticked


def test_check_disks_again_drops_a_carried_tick(monkeypatch):
    first, _ = _wiz()
    _tick_and_continue(first)
    carry, history = _handoff_after(first, monkeypatch)
    second, _ = _wiz()
    second.offer_owner_carry(carry, history)
    _to_owner(second)
    assert second.owner_carried
    assert second.begin_refresh() is not None
    assert not second.owner_ok and second.owner_source == "" and second._owner_carry_out is None


def test_keyboard_layout_change_drops_a_carried_tick(monkeypatch):
    first, _ = _wiz()
    _tick_and_continue(first)
    carry, history = _handoff_after(first, monkeypatch)
    second, _ = _wiz()
    second.offer_owner_carry(carry, history)
    _to_owner(second)
    second.screen = Screen.OWNER
    second._keyboard_from = None
    second._invalidate_after_layout_change_locked()
    assert not second.owner_ok and second._owner_carry_out is None


# --- every per-disk gate still applies ----------------------------------------


def test_per_disk_gates_still_required_with_a_carried_tick(monkeypatch, tmp_path):
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    first, _ = _wiz()
    _tick_and_continue(first)
    carry, history = _handoff_after(first, monkeypatch)
    wiz, clock = _wiz()
    wiz.offer_owner_carry(carry, history)
    _to_owner(wiz)
    assert wiz.owner_carried and wiz.selected is None
    wiz.continue_pick()  # no disk chosen
    assert wiz.screen == Screen.PICK
    wiz.confirm_erase()
    assert not getattr(wiz.runner, "started", False)
    wiz.select_disk(wiz.selectable[0].path)
    wiz.continue_pick()
    assert wiz.screen == Screen.CONFIRM
    wiz.set_confirm_input("WRONG")
    wiz.continue_confirm()
    assert wiz.screen == Screen.CONFIRM  # exact token
    wiz.set_confirm_input(wiz.confirm.token)
    wiz.continue_confirm()
    wiz.continue_method()
    assert wiz.screen == Screen.LAST_CHANCE
    wiz.confirm_erase()  # before the five-second review: only enables Erase now later
    assert wiz.screen == Screen.LAST_CHANCE
    assert not getattr(wiz.runner, "started", False)
    assert wiz._wipe_request is None


def test_the_safety_gate_itself_is_unchanged():
    wiz, _ = _wiz()
    disk = wiz.selectable[0]
    from beamo_wipe.safety import confirm_spec, listed_disks

    token = confirm_spec(disk, listed_disks(wiz.discovery)).token
    common = dict(disk=disk, discovery=wiz.discovery, method=MethodId.EVERYDAY)
    with pytest.raises(SafetyError):
        assert_ready_to_wipe(owner_ok=False, typed_token=token, countdown_complete=True, **common)
    with pytest.raises(SafetyError):
        assert_ready_to_wipe(owner_ok=True, typed_token="WRONG", countdown_complete=True, **common)
    with pytest.raises(SafetyError):
        assert_ready_to_wipe(owner_ok=True, typed_token=token, countdown_complete=False, **common)
    with pytest.raises(SafetyError):
        assert_ready_to_wipe(owner_ok=True, typed_token=token, countdown_complete=True,
                             disk=wiz.discovery.boot, discovery=wiz.discovery, method=MethodId.EVERYDAY)


# --- erased disks are marked --------------------------------------------------------


@pytest.mark.parametrize("code, tag", [
    ("verified", "TAG_ERASED_CHECKED"),
    ("unverified", "TAG_ERASED_UNCHECKED"),
    ("failed", "TAG_ERASED_UNCONFIRMED"),
    ("interrupted", "TAG_ERASED_UNCONFIRMED"),
])
def test_disks_erased_earlier_are_marked(monkeypatch, code, tag):
    first, _ = _wiz()
    _tick_and_continue(first)
    carry, history = _handoff_after(first, monkeypatch, code)
    second, _ = _wiz()
    second.offer_owner_carry(carry, history)
    erased, others = second.selectable[0], second.selectable[1:]
    assert getattr(C, tag) in second.disk_tags(erased)
    assert all(not second.erased_tag(d) for d in others)
    assert second.disk_tags(second.discovery.boot) == ()  # Beamo USB: never marked
    # Still selectable: a failed erase may be retried.
    assert erased in second.selectable


def test_nothing_erased_is_not_marked_and_latest_erase_wins():
    wiz, _ = _wiz()
    disk = wiz.selectable[0]
    for code in ("start_failed", "occupied", "open_failed", "geometry_unusable", "preview"):
        assert oc.add_mark((), disk, code) == ()  # proven nothing erased: no mark
    history = oc.add_mark((), disk, "failed")
    history = oc.add_mark(history, disk, "verified")
    assert oc.mark_for(history, disk) == oc.ERASED_CHECKED and len(history) == 1
    assert oc.add_mark(history, dataclasses.replace(disk, serial="", wwn=""), "verified") == history


# --- evidence per erase -------------------------------------------------------------


def _evidence(wiz, source):
    return build_evidence(
        disk=wiz.selectable[0], discovery=wiz.discovery, method=MethodId.QUICK_ZERO,
        request=None, result=None, started_at_wall=None, ended_at_wall=None,
        started_mono=None, ended_mono=None, argv=[], log_text="",
        owner_confirmation=source,
    )


def test_evidence_records_how_ownership_was_confirmed():
    wiz, _ = _wiz()
    assert _evidence(wiz, "on_screen")["authorization"] == {"owner_confirmation": "on_screen"}
    assert _evidence(wiz, "carried_over")["authorization"] == {"owner_confirmation": "carried_over"}
    assert "authorization" not in _evidence(wiz, None)
    assert "authorization" not in _evidence(wiz, "anything else")


def test_reports_and_sharing_copy_show_the_ownership_line():
    from beamo_wipe.privacy import make_sharing_copy
    from beamo_wipe.result_summary import build_result_report_html, build_result_summary

    wiz, _ = _wiz()
    carried = _evidence(wiz, "carried_over")
    assert make_sharing_copy(carried)["authorization"] == {"owner_confirmation": "carried_over"}
    forged = dict(carried, authorization={"owner_confirmation": "Serial ABC123"})
    assert "ABC123" not in json.dumps(make_sharing_copy(forged))  # never free text
    assert "ABC123" not in build_result_summary(forged)
    text = build_result_summary(carried)
    assert "Ownership" in text and "Carried over from an earlier erase in this session" in text
    assert "Confirmed on screen for this erase" in build_result_summary(_evidence(wiz, "on_screen"))
    assert "Ownership" not in build_result_summary(_evidence(wiz, None))
    assert "Carried over from an earlier erase" in build_result_report_html(carried)


@pytest.mark.parametrize("carried", [False, True])
def test_the_wizard_passes_its_own_source_to_evidence(monkeypatch, tmp_path, carried):
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    if carried:
        wiz = _carried(monkeypatch)
        expected = "carried_over"
    else:
        wiz, _ = _wiz()
        _tick_and_continue(wiz)
        expected = "on_screen"
    wiz.preview = False
    wiz.selected = wiz.selectable[0]
    wiz._finish(WipeResult(ok=False, exit_code=1, summary="The erase did not finish.", logfile=""))
    assert wiz.screen == Screen.DONE
    pending = wiz._pending_evidence
    inputs = pending[0] if pending is not None else None
    if inputs is not None:
        assert inputs["owner_confirmation"] == expected
    if wiz.evidence is not None:
        assert wiz.evidence["authorization"]["owner_confirmation"] == expected
    assert inputs is not None or wiz.evidence is not None


def test_each_session_is_a_new_wizard_with_its_own_evidence(monkeypatch, tmp_path):
    """App loop: the tick carries, nothing else from the old erase does."""
    monkeypatch.setattr(app, "running_on_live_usb", lambda: False)
    monkeypatch.delenv("BEAMO_WIPE_BOOT_DEVICE", raising=False)
    source = tmp_path / "disks.json"
    payload = json.loads((Path(__file__).parent / "fixtures/lsblk_same_size.json").read_text())
    source.write_text(json.dumps(payload))
    args = app._parser().parse_args([
        "--lsblk-json", str(source), "--boot-device", "/dev/sdb", "--plain-console",
    ])
    from test_result_presentations import CASES, case_evidence

    seen = []

    def ui(w, **kwargs):
        seen.append(w)
        assert w.screen == Screen.SPLASH and not w.owner_ok
        assert w.evidence is None and w.wipe_result is None and w._wipe_request is None
        assert all(w is not old and w.runner is not old.runner for old in seen[:-1])
        w.skip_splash()
        w.accept_keyboard()
        if len(seen) == 1:
            assert w.screen == Screen.OWNER
            w.set_owner(True)
            w.continue_owner()
        elif len(seen) == 2:
            assert w.screen == Screen.PICK and w.owner_carried
            assert any(C.TAG_ERASED_CHECKED in w.disk_tags(d) for d in w.selectable)
        else:
            w.shutdown()
            return 0
        completed, evidence, _ = case_evidence(CASES[0])
        w.screen = Screen.DONE
        w.selected = w.selectable[0]
        w.wipe_result = completed.wipe_result
        w.evidence = evidence
        w.erase_another_disk()
        w.confirm_shutdown_without_saving(w.shutdown_generation)
        return 0

    monkeypatch.setattr("beamo_wipe.ui.console_wizard._plain_loop", ui)
    app._run_session(args, session_store=None, use_console=True, want_accessible=False,
                     fullscreen=False, reader=None)
    assert len(seen) == 3
    # A new app run (crash, kiosk restart, reboot) starts with nothing carried.
    seen.clear()

    def fresh(w, **kwargs):
        seen.append(w)
        w.skip_splash()
        w.accept_keyboard()
        assert w.screen == Screen.OWNER and not w.owner_ok and w.erased_history == ()
        w.shutdown()
        return 0

    monkeypatch.setattr("beamo_wipe.ui.console_wizard._plain_loop", fresh)
    app._run_session(args, session_store=None, use_console=True, want_accessible=False,
                     fullscreen=False, reader=None)
    assert len(seen) == 1


# --- every interface ---------------------------------------------------------------


def _carried(monkeypatch, code="verified"):
    first, _ = _wiz()
    _tick_and_continue(first)
    carry, history = _handoff_after(first, monkeypatch, code)
    second, _ = _wiz()
    second.offer_owner_carry(carry, history)
    _to_owner(second)
    return second


def test_curses_and_plain_console_parity(monkeypatch):
    from beamo_wipe.ui import console_wizard as cw
    import inspect

    wiz = _carried(monkeypatch)
    assert C.CON_OWNER_CARRY_KEY in cw._assist_footer(wiz, False)
    blocks = cw._pick_blocks(wiz, 100)
    assert any(C.TAG_ERASED_CHECKED in line for _d, block in blocks for line in block)
    src = inspect.getsource(cw)
    assert 'ch in (ord("w"), ord("W")) and wizard.owner_carried' in src
    assert 'choice.upper() == "OWNER"' in src and "print(C.OWNER_CARRY_LINE)" in src
    assert "_lines(C.OWNER_CARRY_LINE, w) if wizard.owner_carried" in src
    assert "wizard.owner_carry_note" in src


def test_gtk_parity_source():
    # GTK is not importable everywhere; the source is (runtime: Linux CI).
    src = (Path(__file__).resolve().parents[1] / "src/beamo_wipe/ui/accessible_wizard.py").read_text(
        encoding="utf-8")
    assert "self.label(C.OWNER_CARRY_LINE, focusable=True)" in src
    assert "self.button(C.OWNER_CARRY_CHANGE, self.w.change_ownership, in_body=True)" in src
    assert "self.w.disk_tags(disk)" in src and "self.w.owner_carry_note" in src


def _tk_walk(widget):
    yield widget
    for child in widget.winfo_children():
        yield from _tk_walk(child)


@pytest.mark.parametrize("size", [(800, 600), (1280, 820)])
def test_tk_pick_shows_the_carried_line_change_and_erased_tag(monkeypatch, size):
    tkui = pytest.importorskip("beamo_wipe.ui.tk_wizard")
    wiz = _carried(monkeypatch)
    try:
        app_ = tkui.TkWizard(wiz)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Tk unavailable: {exc}")
    try:
        app_.root.geometry(f"{size[0]}x{size[1]}+10+10")
        app_._draw()
        for _ in range(6):
            app_.root.update()
        widgets = list(_tk_walk(app_._body))
        rows = [w for w in widgets if getattr(w, "_beamo_owner_carry", False)]
        assert len(rows) == 1 and rows[0].winfo_ismapped()
        texts = [str(w.cget("text")) for w in _tk_walk(rows[0]) if w.winfo_class() == "Label"]
        assert C.OWNER_CARRY_LINE in texts
        change = [w for w in widgets if getattr(w, "_beamo_owner_carry_change", False)]
        assert len(change) == 1
        details = " ".join(str(w.cget("text")) for w in widgets if w.winfo_class() == "Label")
        assert C.TAG_ERASED_CHECKED in details
        change[0]._command()
        for _ in range(4):
            app_.root.update()
        assert wiz.screen == Screen.OWNER and not wiz.owner_ok
    finally:
        app_._teardown()


def test_tk_owner_note_when_the_tick_did_not_carry(monkeypatch):
    tkui = pytest.importorskip("beamo_wipe.ui.tk_wizard")
    base = make_demo_wizard().discovery
    first, _ = _wiz(_without(base, base.selectable[-1].path))
    _tick_and_continue(first)
    carry, history = _handoff_after(first, monkeypatch)
    wiz, _ = _wiz(base)
    wiz.offer_owner_carry(carry, history)
    _to_owner(wiz)
    try:
        app_ = tkui.TkWizard(wiz)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Tk unavailable: {exc}")
    try:
        app_.root.geometry("800x600+10+10")
        app_._draw()
        for _ in range(6):
            app_.root.update()
        notes = [w for w in _tk_walk(app_._body) if getattr(w, "_beamo_owner_carry_note", False)]
        assert len(notes) == 1 and str(notes[0].cget("text")) == C.OWNER_CARRY_NEW_DISK
    finally:
        app_._teardown()


def test_every_language_has_the_new_words():
    from beamo_wipe import lang
    from beamo_wipe import result_summary as rs

    keys = ("OWNER_CARRY_LINE", "OWNER_CARRY_CHANGE", "OWNER_CARRY_NEW_DISK", "OWNER_CARRY_UNSURE",
            "CON_OWNER_CARRY_KEY", "CON_OWNER_CARRY_HINT", "TAG_ERASED_CHECKED",
            "TAG_ERASED_UNCHECKED", "TAG_ERASED_UNCONFIRMED")
    english = {k: getattr(C, k) for k in keys}
    try:
        for code in lang.LANGUAGE_ORDER:
            lang.set_language(code)
            for key in keys:
                value = getattr(C, key)
                assert value and (code == "en" or value != english[key]), (code, key)
            assert C.CON_OWNER_CARRY_KEY.startswith("W"), code  # key names stay English
            assert rs.H_OWNERSHIP and rs.OWNERSHIP_CARRIED and rs.OWNERSHIP_ON_SCREEN
    finally:
        lang.set_language("en")
