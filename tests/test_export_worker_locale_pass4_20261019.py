# SPDX-License-Identifier: GPL-3.0-or-later
"""The private report worker keeps the controller's allowlisted UI language."""

import hashlib
import io
import json
from pathlib import Path
import time
from types import SimpleNamespace

import pytest

from beamo_wipe import diagnostic_report, lang, privacy, result_summary
from beamo_wipe import support_export as export
from beamo_wipe.models import DiscoveryResult
from beamo_wipe.outcomes import present_evidence
from beamo_wipe.safety import SafetyError
from test_result_presentations import CASES, case_evidence


@pytest.fixture
def worker(tmp_path, monkeypatch):
    """Real decode/write/readback, ordinary file handles and fake mount commands."""
    previous = lang.current()
    effects, commands = [], []

    def forbidden(*_args, **_kwargs):
        effects.append(True)
        raise AssertionError("Real device, inventory, process, mount or power action reached")

    for target in (
        "subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk",
        "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources",
        "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start",
        "beamo_wipe.app._shutdown",
    ):
        monkeypatch.setattr(target, forbidden)
    monkeypatch.setattr(export, "_emit_export_marker", lambda *_args: None)
    parent, child = tmp_path / "fake-parent", tmp_path / "fake-child"
    parent.write_bytes(b"ordinary parent fixture")
    child.write_bytes(b"ordinary volume fixture")
    volume = export.ExportVolume(
        export.DeviceFingerprint(str(parent), 2_000_000_000, "Fake USB", "fake-serial", ""),
        str(child), 1_000_000_000, "vfat", "FAT32", "FAKE-UUID",
    )
    # Inventory/identity acceptance has separate safety tests. These injected
    # values route only ordinary fixture files into the actual bundle writer.
    monkeypatch.setattr(export, "run_lsblk", lambda: {})
    monkeypatch.setattr(export, "select_export_volume", lambda *_args: volume)
    monkeypatch.setattr(export, "_protected_rdevs", lambda *_args: ())
    monkeypatch.setattr(export, "_volume_with_rdev", lambda value: value)
    monkeypatch.setattr(export, "_assert_partition_parent", lambda *_args: None)
    monkeypatch.setattr(export, "MOUNT_ROOT", tmp_path / "mount-root")

    def fake_command(argv, **_kwargs):
        commands.append(argv)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(export, "_run_command", fake_command)
    monkeypatch.setattr(export, "_mounted_exact", lambda *_args: True)
    monkeypatch.setattr(export, "_verify_mount", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(export, "_ordinary_unmount", lambda *_args: True)
    monkeypatch.setattr(export, "_mount_record", lambda *_args: None)

    def request(kind):
        if kind == "diagnostic":
            data = diagnostic_report.create_report(
                "discovery_failed", DiscoveryResult(error="controlled failure"),
                ui="accessible", session_started=time.monotonic(),
            )
            evidence = diagnostic_report.verified_report(data)
        else:
            _wizard, record, _log = case_evidence(
                next(case for case in CASES if case[0] == "process_failed")
            )
            path = tmp_path / "result-sda-123.json"
            record["provenance"]["evidence_file"] = str(path)
            data = (json.dumps(record) + "\n").encode()
            path.write_bytes(data)
            Path(str(path) + ".sha256").write_text(
                hashlib.sha256(data).hexdigest() + "  " + path.name + "\n"
            )
            evidence = export.prepare_terminal_evidence(path, record["device"]["path"])
        wire = export._request_dict(
            evidence, volume, [], [], b"", "unavailable", kind == "sharing"
        )
        return wire, data

    def submit(wire):
        raw = wire if isinstance(wire, bytes) else json.dumps(wire).encode()
        monkeypatch.setattr(export.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(raw)))
        return export._worker()

    def folder(receipt):
        candidates = list(export.MOUNT_ROOT.glob("mount-*/" + receipt.report_folder))
        assert len(candidates) == 1
        return candidates[0]

    yield SimpleNamespace(request=request, submit=submit, folder=folder, commands=commands)
    lang.set_language(previous)
    assert not effects


@pytest.mark.parametrize("controller_language", ["en", "fr", "de", "es"])
@pytest.mark.parametrize("worker_language", ["en", "fr", "de", "es"])
@pytest.mark.parametrize("kind", ["diagnostic", "owner", "sharing"])
def test_worker_exports_controller_language(worker, controller_language, worker_language, kind):
    lang.set_language(controller_language)
    wire, original = worker.request(kind)
    expected_header = result_summary.HEADER_RESULT
    expected_notice = privacy.NOTICE
    lang.set_language(worker_language)  # Models a fresh or differently initialized process.
    receipt = worker.submit(wire)
    assert receipt.ok and receipt.safe_to_remove
    folder = worker.folder(receipt)
    original_name = "diagnostic.json" if kind == "diagnostic" else "result.json"
    assert (folder / original_name).read_bytes() == original
    if kind == "diagnostic":
        assert json.loads(original)["title"] in (folder / "README.txt").read_text()
    else:
        assert (folder / "RESULT.txt").read_text().splitlines()[0] == expected_header
        assert '<html lang="' + controller_language + '">' in (folder / "REPORT.html").read_text()
    if kind == "sharing":
        sharing = json.loads((folder / "SHARE.json").read_bytes())
        assert (folder / "SHARE.txt").read_text().splitlines()[0] == expected_notice
        assert present_evidence(sharing).code == "process_failed"
        assert sharing["locale"]["language"] == controller_language
        assert "serial" not in sharing["device"] and "path" not in sharing["device"]
        owner = json.loads(original)
        assert owner["device"]["serial"] not in (folder / "SHARE.json").read_text()
    assert len(worker.commands) == 3  # Fake rw mount, sync, then ro remount.


@pytest.mark.parametrize("bad_language", [None, True, 1, [], {}, "it", "ES", "FR", " fr", "es ", "en\x00"])
def test_unknown_or_malformed_language_fails_before_inventory_and_allows_retry(
    worker, monkeypatch, bad_language
):
    lang.set_language("fr")
    good, _original = worker.request("diagnostic")
    bad = dict(good, language=bad_language)
    lang.set_language("en")
    scans = []
    real_scan = export.run_lsblk
    monkeypatch.setattr(export, "run_lsblk", lambda: scans.append(True) or real_scan())
    with pytest.raises(SafetyError):
        worker.submit(bad)
    assert not scans and not worker.commands
    assert lang.current() == "en"
    receipt = worker.submit(good)
    assert receipt.ok and receipt.owner_file == "diagnostic.json"
    assert scans == [True, True]
    assert lang.current() == "fr"


@pytest.mark.parametrize("startup_language", ["en", "fr", "de", "es"])
def test_legacy_request_without_language_is_english(worker, startup_language):
    lang.set_language("en")
    wire, original = worker.request("diagnostic")
    wire.pop("language", None)
    lang.set_language(startup_language)
    receipt = worker.submit(wire)
    assert receipt.ok
    assert (worker.folder(receipt) / "diagnostic.json").read_bytes() == original
    assert lang.current() == "en"


def test_duplicate_language_is_rejected_before_inventory(worker, monkeypatch):
    lang.set_language("en")
    wire, _original = worker.request("diagnostic")
    wire["language"] = "en"
    raw = json.dumps(wire, separators=(",", ":")).encode()
    raw = raw.replace(b'"language":"en"', b'"language":"fr","language":"en"')
    scans = []
    monkeypatch.setattr(export, "run_lsblk", lambda: scans.append(True))
    with pytest.raises(SafetyError):
        worker.submit(raw)
    assert not scans and not worker.commands
