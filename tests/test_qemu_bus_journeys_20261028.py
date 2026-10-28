# SPDX-License-Identifier: GPL-3.0-or-later
"""QEMU gate erases SATA (AHCI) and NVMe targets from a writable USB stick.

Source-level and fake-shell checks only; the hosted QEMU gate runs the
journeys. Most owners' disks are SATA or NVMe, and real sticks are writable,
so the boot USB must be excluded by its identity, not a read-only flag.
"""

from __future__ import annotations

from pathlib import Path
import re
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
QEMU = ROOT / "scripts/qemu-verify.sh"
PUBLISHER = ROOT / "scripts/publish_release_gcs.py"


def _function(name: str) -> str:
    source = QEMU.read_text(encoding="utf-8")
    return f"{name}() {{" + source.split(f"{name}() {{", 1)[1].split("\n}\n", 1)[0] + "\n}\n"


def _record(tmp_path, devices: str):
    script = tmp_path / "check.sh"
    script.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        + _function("record_qemu_cmdline")
        + 'record_qemu_cmdline "$1" qemu-system-x86_64 -nic none '
        "-device qemu-xhci,id=beamo-xhci "
        "-device usb-storage,drive=beamo-boot-media,serial=BEAMOBOOT,bootindex=1 "
        + devices + "\n"
    )
    return subprocess.run(
        ["bash", str(script), str(tmp_path / "argv.txt")],
        capture_output=True, text=True, check=False, timeout=30,
    )


@pytest.mark.parametrize("devices", [
    "-device nvme,drive=beamo-target,serial=0005",
    "-device ahci,id=beamo-ahci -device ide-hd,drive=beamo-target,bus=beamo-ahci.0,serial=0004",
])
def test_cmdline_allowlist_accepts_the_nvme_and_sata_targets(tmp_path, devices):
    result = _record(tmp_path, devices)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("devices", [
    "-device nvme,drive=other,serial=0005",
    "-device ide-hd,drive=beamo-target,bus=ide.0,serial=0004",
    "-device ahci,id=beamo-ahci -device e1000",
])
def test_cmdline_allowlist_still_rejects_other_devices(tmp_path, devices):
    assert _record(tmp_path, devices).returncode != 0


def _target_devices(bus: str, writable: str) -> tuple[int, str]:
    """Run boot_probe's media/target selection block with fake inputs."""
    boot = _function("boot_probe")
    start = boot.index('  boot_media="$ISO"\n')
    end = boot.index("  confirmation_token=")
    block = boot[start:end]
    script = (
        "set -euo pipefail\n"
        f'ISO=/fake.iso USB_IMAGE=/fake.img QEMU_TARGET_BUS={bus} QEMU_BOOT_WRITABLE={writable}\n'
        'label=bios-sata-usb token=0004\n'
        "probe() {\n" + block + '  printf "%s\\n" "${media_args[@]}" "${target_devices[@]}"\n}\n'
        "probe\n"
    )
    result = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=30)
    return result.returncode, result.stdout + result.stderr


def test_writable_flag_attaches_the_stick_as_a_discarded_snapshot():
    code, out = _target_devices("sata", "1")
    assert code == 0, out
    assert "if=none,id=beamo-boot-media,format=raw,snapshot=on,file=/fake.img" in out
    assert "readonly=on" not in out
    assert "ahci,id=beamo-ahci" in out
    assert "ide-hd,drive=beamo-target,bus=beamo-ahci.0,serial=0004" in out
    code, out = _target_devices("virtio", "0")
    assert code == 0, out
    assert "format=raw,readonly=on,file=/fake.img" in out
    assert "virtio-blk-pci,drive=beamo-target,serial=0004" in out
    code, out = _target_devices("nvme", "1")
    assert code == 0 and "nvme,drive=beamo-target,serial=0004" in out, out
    code, out = _target_devices("scsi", "0")
    assert code != 0 and "unknown QEMU target bus" in out


def test_gate_runs_both_journeys_with_the_default_method_and_a_saved_report():
    source = QEMU.read_text(encoding="utf-8")
    journey = _function("run_bus_journey")
    assert "grep '^everyday|' <<<\"$METHOD_CASES\"" in journey
    assert 'boot_probe "$label" yes "$key"' in journey
    for call in ("assert_guest_phases", "assert_guest_overwrite", "verify_guest_report"):
        assert call in journey
    assert "QEMU_BOOT_WRITABLE=1" in journey
    # Reset so later probes keep the read-only stick and virtio target.
    assert journey.index("QEMU_TARGET_BUS=virtio") > journey.index('boot_probe "$label"')
    assert re.search(r"^run_bus_journey bios-sata-usb sata 0004$", source, re.M)
    assert "run_bus_journey uefi-nvme-usb nvme 0005" in source
    serials = re.findall(r"\|(\d{4})$", source.split("METHOD_CASES=$(cat <<'EOF'\n", 1)[1]
                         .split("\nEOF\n", 1)[0], re.M)
    assert not {"0004", "0005"} & set(serials)
    # The USB image's bytes are rechecked after every probe.
    assert "USB image changed during QEMU verification" in source
    for key in ("sata_bios_usb=pass", "nvme_uefi_usb=pass", "writable_boot_usb=pass"):
        assert key in source


def test_publisher_requires_the_new_journey_evidence():
    import importlib.util

    spec = importlib.util.spec_from_file_location("publish_release_gcs", PUBLISHER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    names = set(module._qemu_evidence_names())
    for label in ("bios-sata-usb", "uefi-nvme-usb"):
        for suffix in ("serial", "qemu", "cmdline"):
            assert f"{label}-{suffix}.txt" in names
        for suffix in ("readback", "bundle", "fsck", "mount"):
            assert f"guest-{label}-{suffix}.txt" in names
