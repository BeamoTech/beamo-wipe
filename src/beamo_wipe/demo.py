# SPDX-License-Identifier: GPL-3.0-or-later
"""Load fake lsblk JSON for --demo / --preview scenarios."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from beamo_wipe.discover import discover, load_lsblk_json_text
from beamo_wipe.models import DiscoveryResult
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.wizard import Wizard

Scenario = Literal["happy", "empty", "hidden", "blocked", "fail"]
HERE = Path(__file__).resolve().parent
DEMO_DURATION_S = 8.0
# #185 "hidden" preview: only the Beamo USB is listed and this fake lspci
# -nnk capture shows an Intel VMD controller (Tiger Lake 8086:9a0b) and no
# NVMe controller. The empty screen then shows the Intel VMD / RST steps.
DEMO_LSPCI_VMD = (
    "00:00.0 Host bridge [0600]: Intel Corporation 11th Gen Core Processor "
    "Host Bridge/DRAM Registers [8086:9a14] (rev 01)\n"
    "00:02.0 VGA compatible controller [0300]: Intel Corporation TigerLake-LP "
    "GT2 [Iris Xe Graphics] [8086:9a49] (rev 01)\n"
    "\tKernel driver in use: i915\n"
    "00:0e.0 RAID bus controller [0104]: Intel Corporation Volume Management "
    "Device NVMe RAID Controller [8086:9a0b]\n"
    "\tKernel driver in use: vmd\n"
    "00:14.0 USB controller [0c03]: Intel Corporation Tiger Lake-LP USB 3.2 "
    "Gen 2x1 xHCI Host Controller [8086:a0ed] (rev 20)\n"
    "\tKernel driver in use: xhci_hcd\n"
    "00:1f.0 ISA bridge [0601]: Intel Corporation Tiger Lake-LP LPC "
    "Controller [8086:a082] (rev 20)\n"
)


def demo_pci_functions():
    """The fake PCI functions of the "hidden" preview (never real sysfs)."""
    from beamo_wipe.hidden_storage import parse_lspci

    return parse_lspci(DEMO_LSPCI_VMD)


def _payload(name: str) -> dict:
    return load_lsblk_json_text((HERE / name).read_text(encoding="utf-8"))


def discovery_for_scenario(scenario: Scenario) -> DiscoveryResult:
    if scenario == "fail":
        scenario = "happy"
    if scenario == "blocked":
        return discover(
            lsblk_payload=_payload("demo_blocked.json"),
            boot_path=None,
            mount_sources=[],
            cmdline="",
            env={"BEAMO_WIPE_DRY_RUN": "1"},
        )
    if scenario in ("empty", "hidden"):
        return discover(
            lsblk_payload=_payload("demo_empty.json"),
            boot_path="/dev/sdb",
            mount_sources=[],
            cmdline="",
            env={"BEAMO_WIPE_DRY_RUN": "1", "BEAMO_WIPE_BOOT_DEVICE": "/dev/sdb"},
        )
    return discover(
        lsblk_payload=_payload("demo_lsblk.json"),
        boot_path="/dev/sdb",
        mount_sources=[],
        cmdline="",
        env={"BEAMO_WIPE_DRY_RUN": "1", "BEAMO_WIPE_BOOT_DEVICE": "/dev/sdb"},
    )


def make_demo_wizard(
    fail: bool = False,
    scenario: Scenario = "happy",
    synthesize_stages: bool = False,
) -> Wizard:
    import os

    os.environ["BEAMO_WIPE_DRY_RUN"] = "1"
    os.environ["BEAMO_WIPE_DEMO"] = "1"
    if scenario == "fail":
        fail = True
        scenario = "happy"
    discovery = discovery_for_scenario(scenario)
    runner = DryRunRunner(
        duration_s=DEMO_DURATION_S, fail=fail, synthesize_stages=synthesize_stages
    )
    wiz = Wizard(discovery, runner, dry_run=True, rediscover=lambda: discovery_for_scenario(scenario))
    wiz.preview = True
    if scenario == "hidden":
        wiz.hidden_storage_probe = demo_pci_functions
    return wiz
