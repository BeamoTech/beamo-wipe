# SPDX-License-Identifier: GPL-3.0-or-later
"""The QEMU report check accepts the SATA journey's own disk, and only it.

Greptile (PR #94): verify_guest_report hard-coded the method journeys'
virtio /dev/vda and serial 0001, so a correct report from the AHCI SATA
journey (sd* disk, serial 0004) would have failed the hosted gate. The
journey now passes its name pattern and serial. Fake report files only.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from beamo_wipe.methods import METHODS
from beamo_wipe.models import MethodId
from beamo_wipe.support_export import _bundle_files
from test_qemu_complete_log_pass28_build import _engine_log, _status_row, _verifier_source
from test_result_presentations import STATUS, case_evidence

ROOT = Path(__file__).resolve().parents[1]
QEMU = ROOT / "scripts/qemu-verify.sh"


def _report(tmp_path, path: str, serial: str) -> Path:
    spec = METHODS[MethodId.EVERYDAY]
    _, evidence, _ = case_evidence(
        ("completed", MethodId.EVERYDAY, 0, STATUS + _status_row("{name}").rstrip("\n"), False, False)
    )
    evidence.update(source_commit="a" * 40, build_id="fixture")
    name = path.rsplit("/", 1)[-1]
    evidence["device"].update(
        path=path, realpath=path, name=name, serial=serial,
        size_bytes=67108864, size_gb_label="0",
    )
    evidence["boot_device"] = "/dev/sdb" if name != "sdb" else "/dev/sda"
    evidence["logfile"] = "/tmp/beamo-wipe/nwipe.log"
    evidence["nwipe"]["argv_redacted"] = [
        "nwipe", "--autonuke", "--nogui", "--nowait", "--quiet",
        f"--method={spec.nwipe_method}", f"--verify={spec.verify}",
        "--rounds=1", "--logfile=/tmp/beamo-wipe/nwipe.log",
        "--PDFreportpath=noPDF", f"--exclude={evidence['boot_device']}",
        "--noblank", path,
    ]
    engine_log = _engine_log(spec, path)
    evidence["log_checksum_sha256"] = hashlib.sha256(engine_log).hexdigest()
    evidence["log_snapshot_size_bytes"] = len(engine_log)
    files = _bundle_files(json.dumps(evidence).encode(), engine_log, "complete")
    session = tmp_path / "BEAMO-WIPE-REPORTS" / ("report-" + "a" * 24)
    session.mkdir(parents=True)
    for file_name, content in files.items():
        (session / file_name).write_bytes(content)
    return tmp_path


def _check(mount: Path, *identity: str):
    spec = METHODS[MethodId.EVERYDAY]
    command = [
        sys.executable, "-c", _verifier_source(), str(mount), "verified", "everyday",
        spec.nwipe_method, spec.title, "fixture", "a" * 40, *identity,
    ]
    return subprocess.run(command, capture_output=True, text=True, timeout=60)


def test_sata_report_passes_with_the_journeys_identity(tmp_path):
    mount = _report(tmp_path, "/dev/sda", "0004")
    checked = _check(mount, "sd[a-z]+", "0004")
    assert checked.returncode == 0, checked.stderr


@pytest.mark.parametrize("identity,why", [
    ((), "default virtio identity"),
    (("vda", "0004"), "wrong name pattern"),
    (("sd[a-z]+", "0001"), "wrong serial"),
    (("sd[a-z]+", ""), "method serial default"),
])
def test_sata_report_fails_with_any_other_identity(tmp_path, identity, why):
    mount = _report(tmp_path, "/dev/sda", "0004")
    checked = _check(mount, *identity)
    assert checked.returncode != 0, why
    assert "target identity differs" in checked.stderr, (why, checked.stderr)


def test_method_journey_default_identity_is_unchanged(tmp_path):
    mount = _report(tmp_path, "/dev/vda", "0001")
    assert _check(mount).returncode == 0
    # A virtio report never passes as the SATA journey's disk.
    assert _check(mount, "sd[a-z]+", "0004").returncode != 0


def test_sata_journey_passes_its_identity_and_exfat_keeps_its_own_check():
    source = QEMU.read_text(encoding="utf-8")
    journey = source.split("run_bus_journey() {", 1)[1].split("\n}\n", 1)[0]
    assert "\"$(method_title everyday)\" 'sd[a-z]+' \"$serial\"" in journey
    wrapper = source.split("verify_guest_report() {", 1)[1].split("<<'PY'", 1)[0]
    assert 'local expected_name="${7:-vda}" expected_serial="${8:-}"' in wrapper
    assert '"$expected_name" "$expected_serial"' in wrapper
