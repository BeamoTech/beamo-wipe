# SPDX-License-Identifier: GPL-3.0-or-later
"""#135: a guided Save a report panel; the result footer keeps two actions.

Fake lsblk payloads, fake exporters and fake probes only: nothing here scans,
mounts, opens or writes a real device. The real FAT32 export stays covered by
tests/test_usb_report_workflow.py and the isolated QEMU gate.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import threading
import time

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe import support_export as X
from beamo_wipe.models import Screen, WipeResult
from beamo_wipe.report_panel import build_report_panel, usb_status
from beamo_wipe.safety import SafetyError
from beamo_wipe.wizard import ReportView, Wizard, make_demo_wizard
from test_result_presentations import CASES, case_evidence
from test_usb_report_workflow import (
    _discovery,
    _partition,
    _payload,
    _root,
    _success_receipt,
)

FOUND = X.ReportUsbProbe(X.PROBE_FOUND, label="SanDisk Ultra, 16 GB", filesystem="FAT32")
NONE = X.ReportUsbProbe(X.PROBE_NONE)
MANY = X.ReportUsbProbe(X.PROBE_MANY)
NTFS = X.ReportUsbProbe(X.PROBE_FORMAT, filesystem="NTFS", detail=X.USB_FAT32_ONLY)


def _case(code):
    return next(c for c in CASES if c[0] == code)


# --- Read-only detection (support_export.probe_report_usb) -------------------


def _probe(payload, disks, **kw):
    return X.probe_report_usb(
        discovery=_discovery(disks), target_path="/dev/nvme0n1",
        scan=lambda: payload, **kw,
    )


def _big_candidate(payload):
    stick = payload["blockdevices"][2]
    stick["size"] = 16_000_000_000
    stick["model"] = "SanDisk Ultra"
    return stick


def test_one_new_fat32_stick_is_found_with_its_name_size_and_format():
    payload, disks = _payload()
    _big_candidate(payload)
    result = _probe(payload, disks)
    assert result.state == X.PROBE_FOUND
    assert result.label == X.destination_label_for("SanDisk Ultra", 16_000_000_000)
    assert result.filesystem == "FAT32"
    # The owner sees a name and size, never a device path or serial.
    shown = usb_status(result)
    assert shown == C.REPORT_USB_FOUND.format(label=result.label, filesystem="FAT32")
    assert "/dev/" not in shown and "REPORT-1" not in shown


def test_exfat_is_accepted_as_implemented():
    payload, disks = _payload()
    payload["blockdevices"][2]["children"][0].update(fstype="exfat", fsver="1.0")
    result = _probe(payload, disks)
    assert (result.state, result.filesystem) == (X.PROBE_FOUND, "exFAT")


def test_no_new_stick_is_looking():
    payload, disks = _payload()
    payload["blockdevices"].pop()
    assert _probe(payload, disks).state == X.PROBE_NONE
    assert usb_status(_probe(payload, disks)) == C.REPORT_USB_NONE


def test_two_new_sticks_are_named_as_two():
    another = _root(
        "/dev/sdd", size=64_000_000, tran="usb", model="Another", serial="REPORT-2",
        rm=1, hotplug=1, children=[_partition("/dev/sdd1", uuid="EEEE-FFFF", pkname="sdd")],
    )
    payload, disks = _payload(another)
    result = _probe(payload, disks)
    assert result.state == X.PROBE_MANY
    assert usb_status(result) == C.REPORT_USB_MANY


@pytest.mark.parametrize(
    ("fstype", "fsver", "name"),
    [("ntfs", "", "NTFS"), ("vfat", "FAT16", "FAT16"), ("ext4", "1.0", "ext4"),
     ("hfsplus", "", "Mac OS Extended (HFS+)"), ("zfs_member", "5000", "")],
)
def test_ineligible_format_is_explained_by_name(fstype, fsver, name):
    payload, disks = _payload()
    payload["blockdevices"][2]["children"][0].update(fstype=fstype, fsver=fsver)
    result = _probe(payload, disks)
    assert result.state == X.PROBE_FORMAT
    assert result.filesystem == name
    expected = (C.REPORT_USB_FORMAT.format(filesystem=name) if name
                else C.REPORT_USB_FORMAT_UNKNOWN)
    assert usb_status(result) == expected
    if name == "NTFS":
        assert usb_status(result) == (
            "This USB is formatted NTFS — use a FAT32 or exFAT stick."
        )


@pytest.mark.parametrize(
    ("mutate", "detail"),
    [
        (lambda p: p["blockdevices"][2]["children"][0].update(
            mountpoints=["/media/x"], mountpoint="/media/x"), X.USB_MUST_BE_WRITABLE),
        (lambda p: p["blockdevices"][2].update(ro=1), X.USB_MUST_BE_WRITABLE),
        (lambda p: p["blockdevices"][2]["children"][0].update(ro=1), X.USB_VOLUME_WRITABLE),
        (lambda p: p["blockdevices"][2]["children"].append(
            _partition("/dev/sdc2", uuid="1111-2222")), X.USB_NEED_ONE_VOLUME),
    ],
)
def test_other_unusable_sticks_say_why_and_what_to_do(mutate, detail):
    payload, disks = _payload()
    mutate(payload)
    result = _probe(payload, disks)
    assert (result.state, result.detail) == (X.PROBE_REFUSED, detail)
    assert usb_status(result) == f"{detail} {X.next_step_for(detail)}"


def test_the_boot_usb_and_erased_disk_are_never_found():
    # Only the protected disks: nothing new, so nothing to save to.
    payload, disks = _payload()
    payload["blockdevices"].pop()
    assert _probe(payload, disks).state == X.PROBE_NONE
    # A stick claiming the boot USB's hardware ID is refused, never found.
    payload, disks = _payload()
    payload["blockdevices"][2]["wwn"] = "boot-wwn"
    assert _probe(payload, disks).state == X.PROBE_REFUSED
    # A changed boot USB or target blocks the panel the same way Save would.
    payload, disks = _payload()
    payload["blockdevices"][0]["serial"] = "changed"
    result = _probe(payload, disks)
    assert (result.state, result.detail) == (X.PROBE_REFUSED, X.BASELINE_KEEP_CONNECTED)


def test_a_failed_scan_is_could_not_check():
    def broken():
        raise OSError("lsblk failed")

    payload, disks = _payload()
    result = X.probe_report_usb(
        discovery=_discovery(disks), target_path="/dev/nvme0n1", scan=broken,
    )
    assert result.state == X.PROBE_UNAVAILABLE
    assert usb_status(result) == C.REPORT_USB_UNAVAILABLE


def test_detection_only_reads_one_scan_and_never_mounts_opens_or_runs(monkeypatch):
    import os
    import subprocess

    def forbidden(*_a, **_k):
        raise AssertionError("detection must not touch a device or start a process")

    for module, name in ((subprocess, "run"), (subprocess, "Popen"), (os, "open"),
                         (os, "mkdir"), (X, "_run_command"), (X, "write_report_bundle")):
        monkeypatch.setattr(module, name, forbidden)
    calls = []
    payload, disks = _payload()
    _big_candidate(payload)

    def scan():
        calls.append(1)
        return payload

    result = X.probe_report_usb(discovery=_discovery(disks), target_path="/dev/nvme0n1", scan=scan)
    assert result.state == X.PROBE_FOUND
    assert calls == [1]


def test_detection_and_export_use_the_same_selector():
    """Found here means the export's own first check accepts the stick."""
    payload, disks = _payload()
    baseline = X.baseline_fingerprints(
        _discovery(disks).disks, required_paths={"/dev/nvme0n1", "/dev/sdb"}
    )
    volume = X.select_export_volume(payload, baseline)
    result = _probe(payload, disks)
    assert result.state == X.PROBE_FOUND
    assert result.filesystem == X.filesystem_name(volume.fstype, volume.fsver)


# --- Panel states (report_panel.build_report_panel) ------------------------------


def _view(**kw):
    base = dict(revision=1, status="idle", message="", session="", exporting=False,
                can_save=True, evidence_error=None)
    base.update(kw)
    return ReportView(**base)


def _panel(view, usb):
    return build_report_panel(view, preview=False, usb=usb, evidence_warning="Evidence warning.")


def test_no_usb_yet_waits_with_save_greyed_and_a_reason():
    for usb in (X.ReportUsbProbe("looking"), NONE):
        panel = _panel(_view(), usb)
        assert panel.kind == "ready"
        assert panel.show_save and not panel.save_enabled
        assert panel.save_reason == C.REPORT_SAVE_WAIT
        assert panel.steps[0].text == C.REPORT_STEP_INSERT
        assert panel.steps[0].state == "now"
    assert _panel(_view(), X.ReportUsbProbe("looking")).steps[1].text == C.REPORT_USB_LOOKING
    assert _panel(_view(), NONE).steps[1].text == C.REPORT_USB_NONE


def test_found_usb_enables_save_and_marks_the_first_steps_done():
    panel = _panel(_view(), FOUND)
    assert panel.show_save and panel.save_enabled and not panel.save_reason
    assert [s.state for s in panel.steps] == ["done", "done", "now", "todo", "todo"]
    assert panel.step_lines[1] == "2. Found: SanDisk Ultra, 16 GB (FAT32)" + " (done)"
    assert panel.steps[2].text == C.REPORT_STEP_SAVE


@pytest.mark.parametrize("usb", [MANY, NTFS, X.ReportUsbProbe(X.PROBE_UNAVAILABLE)])
def test_ineligible_or_ambiguous_sticks_keep_save_greyed_with_the_reason(usb):
    panel = _panel(_view(), usb)
    assert panel.show_save and not panel.save_enabled
    assert panel.steps[1].text == usb_status(usb)
    assert C.REPORT_SAVE_WAIT in panel.lines


def test_saving_shows_progress_and_no_save():
    panel = _panel(_view(status="saving", exporting=True, can_save=False), None)
    assert panel.kind == "saving"
    assert not panel.show_save
    assert panel.step_lines[2] == "3. " + C.REPORT_STEP_SAVING + " (now)"
    assert C.EXPORT_GUIDE_WORKING in panel.lines


def test_saved_shows_location_files_then_remove():
    receipt = "Saved to SanDisk Ultra, 16 GB.\nFolder: BEAMO-WIPE-REPORTS/report-x\nOriginal report: RESULT.txt"
    panel = _panel(_view(status="saved", can_save=False, message=receipt), FOUND)
    assert panel.kind == "saved" and panel.tone == "ok"
    assert not panel.show_save
    assert panel.steps[3].text == receipt
    assert panel.steps[4].text == C.REPORT_STEP_REMOVE_NOW
    assert panel.steps[4].state == "now"
    assert C.REPORT_VOLATILE not in panel.notice


def test_failed_save_says_what_happened_and_offers_save_again_once_found():
    failed = _view(status="error", message=X.USB_GONE)
    panel = _panel(failed, NONE)
    assert panel.kind == "failed" and panel.tone == "warn"
    assert X.USB_GONE in panel.detail
    assert X.next_step_for(X.USB_GONE) in panel.detail
    assert not panel.save_enabled and panel.save_reason == C.REPORT_SAVE_WAIT
    assert _panel(failed, FOUND).save_enabled


def test_evidence_failure_is_a_warning_with_retry():
    view = _view(can_save=False, evidence_error="disk full", can_retry_evidence=True)
    panel = _panel(view, FOUND)
    assert panel.kind == "evidence" and panel.tone == "warn"
    assert panel.show_retry and panel.retry_enabled
    assert not panel.show_save
    assert panel.detail == "Evidence warning."
    # Ref #153: no retries left keeps Retry visible, greyed, with its reason.
    spent = _panel(dataclasses.replace(view, can_retry_evidence=False), FOUND)
    assert spent.show_retry and not spent.retry_enabled
    assert spent.retry_reason == C.RETRY_UNAVAILABLE and C.RETRY_UNAVAILABLE in spent.lines


def test_preparing_and_unavailable_show_no_controls():
    preparing = _panel(_view(can_save=False, saving_evidence=True), FOUND)
    assert preparing.kind == "preparing" and not preparing.show_save
    unavailable = _panel(_view(can_save=False), FOUND)
    assert unavailable.kind == "unavailable" and not unavailable.show_save
    assert unavailable.detail == C.REPORT_NOT_OFFERED
    preview = build_report_panel(_view(), preview=True, usb=FOUND)
    assert preview.kind == "preview" and preview.lines == (C.REPORT_PREVIEW,)


def test_no_greyed_control_without_a_reason_in_any_state():
    views = [
        _view(), _view(status="error", message=X.USB_GONE), _view(status="saving", exporting=True, can_save=False),
        _view(status="saved", can_save=False, message="Saved."),
        _view(can_save=False, evidence_error="x", can_retry_evidence=False),
        _view(can_save=False, evidence_error="x", can_retry_evidence=True),
        _view(can_save=False, saving_evidence=True), _view(can_save=False),
    ]
    usbs = [None, X.ReportUsbProbe("looking"), NONE, FOUND, MANY, NTFS,
            X.ReportUsbProbe(X.PROBE_REFUSED, detail=X.USB_VOLUME_WRITABLE),
            X.ReportUsbProbe(X.PROBE_UNAVAILABLE)]
    for view in views:
        for usb in usbs:
            panel = _panel(view, usb)
            if panel.show_save and not panel.save_enabled:
                assert panel.save_reason and panel.save_reason in panel.lines
            if panel.show_retry and not panel.retry_enabled:
                assert panel.retry_reason and panel.retry_reason in panel.lines


@pytest.mark.parametrize("code", ["fr", "de", "es", "it"])
def test_every_language_translates_the_panel(code):
    english = {name: getattr(C, name) for name in (
        "REPORT_STATUS_TITLE", "REPORT_STEP_INSERT", "REPORT_USB_LOOKING", "REPORT_USB_FOUND",
        "REPORT_USB_FORMAT", "REPORT_SAVE_WAIT", "DONE_WAIT_SAVING", "CON_PANEL_SAVE",
    )}
    try:
        lang.set_language(code)
        for name, value in english.items():
            assert getattr(C, name) != value, (code, name)
        assert "{label}" in C.REPORT_USB_FOUND and "{filesystem}" in C.REPORT_USB_FOUND
        assert "{filesystem}" in C.REPORT_USB_FORMAT
        panel = _panel(_view(), FOUND)
        assert C.REPORT_USB_FOUND.format(label=FOUND.label, filesystem="FAT32") in panel.step_lines[1]
    finally:
        lang.set_language("en")


def test_panel_copy_stays_within_the_claims():
    words = " ".join(str(getattr(C, n)) for n in dir(C)
                     if n.startswith(("REPORT_STEP_", "REPORT_USB_", "DONE_WAIT", "DONE_ANOTHER")))
    lowered = words.lower()
    for banned in ("certif", "dod", "guarantee", "unrecoverable", "plug and play"):
        assert banned not in lowered


# --- Wizard: live detection --------------------------------------------------------


class _Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def _ready_wizard(monkeypatch, *, probe=None, exporter=None, clock=None):
    """A Done wizard whose evidence gate passes without writing a file."""
    base = make_demo_wizard()
    wiz = Wizard(base.discovery, base.runner, clock=clock, dry_run=False,
                 report_exporter=exporter, report_usb_probe=probe)
    wiz.preview = False
    wiz.screen = Screen.DONE
    wiz.selected = wiz.discovery.selectable[0]
    wiz.wipe_result = WipeResult(False, 1, "failed", "/tmp/beamo-wipe/nwipe.log")
    # A bare name round-trips through Path() on every host; nothing is read.
    path = "evidence.json"
    payload = {
        "schema_version": 1, "outcome": "failed",
        "device": {"path": wiz.selected.path},
        "exit_evidence": {"exit_code": 1, "signal": None},
        "logfile": wiz.wipe_result.logfile,
        "provenance": {"evidence_file": path},
    }
    data = json.dumps(payload).encode("utf-8")
    wiz.evidence_path = path
    wiz.evidence = json.loads(data)
    wiz.evidence["provenance"]["verified"] = True
    wiz._evidence_written_for = wiz._result_evidence_key(wiz.wipe_result)
    wiz._evidence_write_seq = 1
    verified = X.VerifiedEvidence(data, hashlib.sha256(data).hexdigest(), "failed",
                                  wiz.wipe_result.logfile, "", 0)
    monkeypatch.setattr(X, "prepare_terminal_evidence", lambda *_a, **_k: verified)
    return wiz


def _wait_idle(wiz, timeout=5.0):
    end = time.monotonic() + timeout
    while wiz._report_usb_busy and time.monotonic() < end:
        time.sleep(0.01)
    assert not wiz._report_usb_busy


def test_live_detection_is_on_only_for_the_real_kiosk():
    base = make_demo_wizard()
    real = Wizard(base.discovery, base.runner, dry_run=False)
    assert real._report_usb_probe is X.probe_report_usb
    assert Wizard(base.discovery, base.runner, dry_run=True)._report_usb_probe is None
    injected = Wizard(base.discovery, base.runner, dry_run=False, report_exporter=lambda **_k: None)
    assert injected._report_usb_probe is None and injected.report_usb is None


def test_tick_scans_in_the_background_and_redraws_only_on_change(monkeypatch):
    clock = _Clock()
    calls, gate = [], threading.Event()

    def probe(**kw):
        calls.append(kw["target_path"])
        gate.wait(5)
        return FOUND

    wiz = _ready_wizard(monkeypatch, probe=probe, clock=clock)
    assert wiz.report_usb.state == "looking"
    revision = wiz.report_view.revision
    started = time.monotonic()
    wiz.tick()
    # The scan runs on a worker: tick returns while the probe still waits.
    assert time.monotonic() - started < 1.0 and wiz._report_usb_busy
    gate.set()
    _wait_idle(wiz)
    assert calls == [wiz.selected.path]
    assert wiz.report_usb == FOUND
    assert wiz.report_view.revision == revision + 1
    assert wiz.report_panel.save_enabled
    wiz.tick()  # not due yet
    _wait_idle(wiz)
    assert len(calls) == 1
    clock.t += 2.0
    wiz.tick()
    _wait_idle(wiz)
    assert len(calls) == 2
    assert wiz.report_view.revision == revision + 1  # same answer, no redraw


@pytest.mark.parametrize("state", ["not_done", "preview", "saved", "exporting"])
def test_no_scan_unless_a_report_can_be_saved(monkeypatch, state):
    calls = []
    wiz = _ready_wizard(monkeypatch, probe=lambda **_k: calls.append(1) or FOUND)
    if state == "not_done":
        wiz.screen = Screen.PICK
    elif state == "preview":
        wiz.preview = True
    elif state == "saved":
        wiz.report_status = "saved"
    else:
        wiz._report_exporting = True
    wiz.tick()
    wiz.refresh_report_usb()
    _wait_idle(wiz)
    assert calls == []


def test_a_probe_error_reads_could_not_check(monkeypatch):
    def broken(**_k):
        raise RuntimeError("boom")

    wiz = _ready_wizard(monkeypatch, probe=broken)
    wiz.refresh_report_usb()
    assert wiz.report_usb.state == X.PROBE_UNAVAILABLE
    assert wiz.report_panel.steps[1].text == C.REPORT_USB_UNAVAILABLE


# --- Wizard: save flow through the panel ---------------------------------------------


def test_stick_removed_mid_save_fails_visibly_and_looks_again(monkeypatch):
    def exporter(**_k):
        raise SafetyError(X.USB_GONE)

    wiz = _ready_wizard(monkeypatch, probe=lambda **_k: NONE, exporter=exporter)
    wiz._report_usb = FOUND
    wiz.save_report_to_usb()
    panel = wiz.report_panel
    assert wiz.report_status == "error"
    assert panel.kind == "failed" and X.USB_GONE in panel.detail
    # The old "found" answer is gone: Save waits for a fresh check.
    assert wiz.report_usb.state == "looking" and not panel.save_enabled
    wiz.refresh_report_usb()
    assert wiz.report_panel.steps[1].text == C.REPORT_USB_NONE


def test_saving_disables_both_footer_actions_with_a_reason(monkeypatch):
    release, entered = threading.Event(), threading.Event()

    def exporter(**kw):
        entered.set()
        release.wait(5)
        return _success_receipt(**kw)

    probes = []
    wiz = _ready_wizard(monkeypatch, probe=lambda **_k: probes.append(1) or FOUND, exporter=exporter)
    wiz._report_usb = FOUND
    assert wiz.begin_report_export()
    assert entered.wait(5)
    try:
        panel = wiz.report_panel
        assert panel.kind == "saving" and not panel.show_save
        assert not wiz.can_erase_another
        assert wiz.done_actions_reason == C.DONE_WAIT_SAVING
        wiz.tick()  # no detection scan while the export runs
        assert probes == []
    finally:
        release.set()
    end = time.monotonic() + 5
    while wiz.report_view.exporting and time.monotonic() < end:
        time.sleep(0.01)
    assert wiz.report_status == "saved"
    panel = wiz.report_panel
    assert panel.kind == "saved" and wiz.report_message == panel.steps[3].text
    assert "BEAMO-WIPE-REPORTS" in panel.steps[3].text
    assert wiz.done_actions_reason == ""
    wiz.tick()
    _wait_idle(wiz)
    assert probes == []  # saved: no more scanning


def test_save_still_runs_the_export_checks_even_when_found(monkeypatch):
    """Detection is advice: the exporter's own checks decide, unchanged."""
    seen = []

    def exporter(**kw):
        seen.append(kw)
        raise SafetyError(X.USB_NOT_SINGLE.format(detail=X.USB_MANY_FOUND))

    wiz = _ready_wizard(monkeypatch, probe=lambda **_k: FOUND, exporter=exporter)
    wiz._report_usb = FOUND
    wiz.save_report_to_usb()
    assert len(seen) == 1
    assert seen[0]["target_path"] == wiz.selected.path
    assert wiz.report_status == "error"


# --- Rendered Tk ------------------------------------------------------------------------


@pytest.fixture
def done_ui():
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


def _walk(widget):
    yield widget
    for child in widget.winfo_children():
        yield from _walk(child)


def _buttons(app, root=None):
    from beamo_wipe.ui.tk_wizard import _Button

    return [w for w in _walk(root or app.root) if isinstance(w, _Button) and w.winfo_ismapped()]


def _text(button):
    return str(button.itemcget(button._label, "text"))


def _mapped_labels(app):
    return [str(w.cget("text")) for w in _walk(app.root)
            if w.winfo_class() == "Label" and w.winfo_ismapped()]


def _tk_case(code="verified", *, usb=None, status=None, message=None, exporting=None,
             evidence_error=None, probe=True):
    from unittest.mock import patch

    wiz, _evidence, _ = case_evidence(_case(code))
    wiz._audio_probe_at = wiz.now + 3600
    wiz._report_usb_probe = (lambda **_k: usb) if probe and usb is not None else None
    wiz._report_usb = usb
    with wiz._lock:
        wiz._set_report_state_locked(status=status, message=message, exporting=exporting)
    if evidence_error:
        wiz.evidence_error = evidence_error
    busy = status in ("saving", "saved")
    patches = [
        patch.object(Wizard, "_can_save_report_locked",
                     lambda self: not busy and not self.evidence_error and self.screen == Screen.DONE),
        patch.object(Wizard, "_can_retry_evidence_locked", lambda self: bool(self.evidence_error)),
    ]
    for p in patches:
        p.start()
    return wiz, patches


@pytest.fixture
def tk_case():
    started = []

    def make(*a, **kw):
        wiz, patches = _tk_case(*a, **kw)
        started.extend(patches)
        return wiz

    yield make
    for p in started:
        p.stop()


STATES = {
    "looking": dict(usb=X.ReportUsbProbe("looking")),
    "nousb": dict(usb=NONE),
    "found": dict(usb=FOUND),
    "ntfs": dict(usb=NTFS),
    "twousb": dict(usb=MANY),
    "saving": dict(usb=FOUND, status="saving", exporting=True),
    "saved": dict(status="saved", message="Saved to SanDisk Ultra, 16 GB."),
    "failed": dict(usb=NONE, status="error", message=X.USB_GONE),
    "evidence": dict(evidence_error="The evidence file could not be written."),
}


@pytest.mark.parametrize("state", list(STATES))
def test_tk_footer_has_two_actions_in_every_result_state(done_ui, tk_case, state):
    wiz = tk_case(**STATES[state])
    app = done_ui(wiz)
    footer = [b for b in _buttons(app, app._footer) if b._variant != "quiet"]
    assert [_text(b) for b in footer] == [C.BTN_ERASE_ANOTHER, C.BTN_SHUTDOWN]
    texts = [_text(b) for b in _buttons(app, app._footer)]
    assert C.BTN_SAVE_REPORT not in texts and C.RETRY_SAVE not in texts
    # Sounds live with the footer's settings utilities, not as actions.
    utilities = [b for b in _buttons(app, app._footer) if b._variant == "quiet"]
    assert [_text(b) for b in utilities] == [wiz.sound_toggle_text, C.SOUND_HEAR_AGAIN]
    # Every greyed control has its reason on screen.
    labels = _mapped_labels(app)
    for button in _buttons(app):
        if not button._enabled:
            reason = {C.BTN_SAVE_REPORT: C.REPORT_SAVE_WAIT,
                      C.RETRY_SAVE: C.RETRY_UNAVAILABLE}.get(_text(button), wiz.done_actions_reason)
            assert reason and reason in labels, (state, _text(button))


def test_tk_preview_footer_has_two_actions(done_ui, tk_case):
    wiz = tk_case()
    wiz.preview = True
    app = done_ui(wiz)
    footer = [b for b in _buttons(app, app._footer) if b._variant != "quiet"]
    assert [_text(b) for b in footer] == [C.BTN_CLOSE_PREVIEW, C.BTN_RUN_AGAIN]


@pytest.mark.parametrize("state", ["looking", "found", "ntfs", "twousb", "failed", "saved"])
def test_tk_panel_shows_steps_status_and_save(done_ui, tk_case, state):
    wiz = tk_case(**STATES[state])
    app = done_ui(wiz)
    labels = _mapped_labels(app)
    panel = wiz.report_panel
    assert C.REPORT_STATUS_TITLE in labels
    for line in panel.step_lines:
        assert line in labels, (state, line)
    saves = [b for b in _buttons(app, app._body) if _text(b) == C.BTN_SAVE_REPORT]
    if state == "saved":
        assert saves == []
    else:
        assert len(saves) == 1 and saves[0]._enabled is (state == "found")


def test_tk_found_save_is_two_tabs_from_shut_down(done_ui, tk_case):
    """QEMU: from Shut down, Tab reaches Show more, then Save report."""
    wiz = tk_case(**STATES["found"])
    app = done_ui(wiz)
    calls = []
    app._click_save_report = lambda: calls.append(1)
    app._draw()  # rebuild so the panel's Save calls the stand-in
    app.root.update()
    assert app.root.focus_lastfor() is app._primary
    current = app._primary
    for title in (C.BTN_MORE, C.BTN_SAVE_REPORT):
        current = current.tk_focusNext()
        current.focus_force()
        app.root.update()
        assert _text(current) == title
    current._key()
    assert calls == [1]
    assert not wiz.wants_shutdown


def test_tk_evidence_retry_is_in_the_first_view(done_ui, tk_case):
    wiz = tk_case(**STATES["evidence"])
    app = done_ui(wiz)
    retry = next(b for b in _buttons(app, app._body) if _text(b) == C.RETRY_SAVE)
    assert retry._enabled
    footer_top = app._footer.winfo_rooty()
    assert retry.winfo_rooty() + retry.winfo_height() <= footer_top


def test_tk_sounds_are_reachable_by_tab_and_keep_focus_when_toggled(done_ui, tk_case):
    wiz = tk_case(**STATES["found"])
    app = done_ui(wiz)
    current, seen = app._primary, []
    for _ in range(40):
        current = current.tk_focusNext()
        if current is app._primary:
            break
        if hasattr(current, "_label"):
            seen.append(_text(current))
    assert wiz.sound_toggle_text in seen and C.SOUND_HEAR_AGAIN in seen
    toggle = next(b for b in _buttons(app, app._footer) if _text(b) == wiz.sound_toggle_text)
    toggle.focus_force()
    app.root.update()
    before = wiz.sounds_enabled
    toggle._command()
    app.root.update()
    assert wiz.sounds_enabled is not before
    assert _text(app.root.focus_lastfor()) == wiz.sound_toggle_text


def test_tk_live_status_change_redraws_and_keeps_focus(done_ui, tk_case):
    wiz = tk_case(**STATES["found"])
    app = done_ui(wiz)
    save = next(b for b in _buttons(app, app._body) if _text(b) == C.BTN_SAVE_REPORT)
    save.focus_force()
    app.root.update()
    other = X.ReportUsbProbe(X.PROBE_FOUND, label="Kingston, 32 GB", filesystem="exFAT")
    wiz._report_usb_probe = lambda **_k: other
    with wiz._lock:
        wiz._report_usb = other
        wiz._report_revision += 1
    app._draw()
    app.root.update()
    assert "2. " + C.REPORT_USB_FOUND.format(label="Kingston, 32 GB", filesystem="exFAT") + " (done)" in _mapped_labels(app)
    assert _text(app.root.focus_lastfor()) == C.BTN_SAVE_REPORT


@pytest.mark.parametrize("text_size", ["standard", "large", "extra"])
def test_tk_panel_fits_every_text_size(done_ui, tk_case, text_size):
    from test_tk_runtime import _clipping_problems

    wiz = tk_case(**STATES["found"])
    wiz.text_size = text_size
    app = done_ui(wiz)
    assert _clipping_problems(app) == []
    assert app._primary.winfo_ismapped()


# --- Consoles ---------------------------------------------------------------------------


def _curses_rows(monkeypatch, wiz, h=60):
    from test_plain_result_134 import _curses_lines

    return _curses_lines(monkeypatch, wiz, h=h)


@pytest.mark.parametrize("state", ["nousb", "found", "ntfs", "failed", "evidence", "saved"])
def test_curses_panel_and_two_action_footer(monkeypatch, tk_case, state):
    wiz = tk_case(**STATES[state])
    rows = _curses_rows(monkeypatch, wiz)
    text = "\n".join(rows)
    panel = wiz.report_panel
    assert C.REPORT_STATUS_TITLE in rows
    for line in panel.step_lines:
        assert line[:40] in text, (state, line)
    assert (C.CON_PANEL_SAVE in text) is (state == "found")
    assert (C.CON_PANEL_RETRY in text) is (state == "evidence")
    if not panel.save_enabled and panel.show_save:
        assert C.REPORT_SAVE_WAIT in text
    assert C.CON_DONE_ANOTHER.format(action=C.CON_DONE_SHUTDOWN) in text
    assert "R: save report to one" not in text


def test_curses_first_page_keeps_the_panel_heading(monkeypatch, tk_case):
    wiz = tk_case(**STATES["found"])
    first = _curses_rows(monkeypatch, wiz, h=24)
    assert any(C.REPORT_STATUS_TITLE in row for row in first)


def test_plain_console_checks_again_and_offers_save_only_when_found(monkeypatch, capsys, tk_case):
    from beamo_wipe.ui import console_wizard as console

    wiz = tk_case(**STATES["nousb"])
    answers = iter(["SAVE", "SHUTDOWN"])
    saved = []
    monkeypatch.setattr(wiz, "save_report_to_usb", lambda: saved.append(1))
    monkeypatch.setattr("builtins.input", lambda *_a: next(answers))
    monkeypatch.setattr(wiz, "shutdown", lambda *a, **k: setattr(wiz, "wants_shutdown", True))
    refreshed = []
    real_refresh = wiz.refresh_report_usb
    monkeypatch.setattr(wiz, "refresh_report_usb", lambda: refreshed.append(1) or real_refresh())
    console._plain_loop(wiz)
    out = capsys.readouterr().out
    assert saved == []  # SAVE is not accepted until one suitable USB is found
    assert len(refreshed) >= 2  # a fresh read-only check each time it prints
    assert C.REPORT_USB_NONE in out and C.REPORT_SAVE_WAIT in out
    assert C.CON_PLAIN_RECHECK in out
    assert C.CON_DONE_SAVE_PROMPT not in out


def test_plain_console_saves_when_found(monkeypatch, capsys, tk_case):
    from beamo_wipe.ui import console_wizard as console

    wiz = tk_case(**STATES["found"])
    answers = iter(["SAVE", "SHUTDOWN"])
    saved = []
    monkeypatch.setattr(wiz, "save_report_to_usb", lambda: saved.append(1))
    monkeypatch.setattr("builtins.input", lambda *_a: next(answers))
    monkeypatch.setattr(wiz, "shutdown", lambda *a, **k: setattr(wiz, "wants_shutdown", True))
    console._plain_loop(wiz)
    out = capsys.readouterr().out
    assert saved == [1]
    assert C.REPORT_USB_FOUND.format(label=FOUND.label, filesystem="FAT32") in out


# --- Isolated QEMU gate ----------------------------------------------------------------


def test_tk_emits_only_the_fixed_usb_state_marker(done_ui, tk_case, monkeypatch):
    from beamo_wipe.ui import tk_wizard

    markers = []
    monkeypatch.setattr(tk_wizard, "emit_serial_marker", lambda m: markers.append(m) or True)
    wiz = tk_case(**STATES["found"])
    done_ui(wiz)
    assert "BEAMO_WIPE_REPORT_USB_FOUND" in markers
    usb = [m for m in markers if m.startswith("BEAMO_WIPE_REPORT_USB_")]
    assert all(m.removeprefix("BEAMO_WIPE_REPORT_USB_").isupper() for m in usb)
    assert not any("SANDISK" in m or "16" in m for m in usb)


def test_qemu_waits_for_detection_before_the_two_tab_save():
    from pathlib import Path

    script = (Path(__file__).resolve().parents[1] / "scripts/qemu-verify.sh").read_text(encoding="utf-8")
    hotplug = script.index('qmp_request "$qmp_socket" hotplug-report "$report_img"')
    wait = script.index('wait_for_marker "$label" BEAMO_WIPE_REPORT_USB_FOUND', hotplug)
    first_tab = script.index('send_key "$qmp_socket" tab', hotplug)
    assert hotplug < wait < first_tab
