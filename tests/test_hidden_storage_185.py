# SPDX-License-Identifier: GPL-3.0-or-later
"""#185: Intel VMD / RST hint on the empty disk list. Fake PCI data only.

The hint is display-only. These tests pin that it appears only for a
certain Intel VMD or RST RAID case, that anything else keeps the generic
empty text byte for byte, and that the selectable list and the Beamo USB
exclusion never change.
"""

from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from beamo_wipe import copy as C
from beamo_wipe import hidden_storage as H
from beamo_wipe import recovery as Rec
from beamo_wipe.demo import DEMO_LSPCI_VMD, demo_pci_functions, make_demo_wizard
from beamo_wipe.discover import discover, load_lsblk_json_text
from beamo_wipe.models import ExcludedDevice, Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.safety import selectable_disks
from beamo_wipe.wizard import Wizard

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"
PCI = FIX / "pci_185"

APPROVED_HEADING = "This computer's disk may be hidden by Intel VMD (RST)."
APPROVED_STEPS = (
    "1. Restart and open the BIOS/UEFI setup.",
    "2. Find the storage setting (often called SATA mode, RST or VMD). "
    "Change it to AHCI, or turn VMD off.",
    "3. Save, then start from the Beamo USB again.",
)
APPROVED_WARNING = (
    "Windows may not start until you change this setting back. "
    "If BitLocker is on, Windows may ask for its recovery key."
)


def _lspci(name: str):
    return H.parse_lspci((PCI / f"lspci_{name}.txt").read_text(encoding="utf-8"))


def _discovery(fixture: str, boot: str = "/dev/sdb"):
    payload = load_lsblk_json_text((FIX / fixture).read_text(encoding="utf-8"))
    return discover(lsblk_payload=payload, boot_path=boot)


def _only_boot():
    return _discovery("lsblk_only_boot.json")


def _generic():
    return Rec.RecoverySections(C.EMPTY_DISKS, Rec.MEANING_EMPTY, Rec.NEXT_EMPTY, "")


def _at_empty(wizard):
    wizard.skip_intro()
    wizard.accept_what()
    wizard.set_owner(True)
    wizard.continue_owner()
    return wizard


# --- kernel tables -----------------------------------------------------------


def test_device_tables_match_the_cited_kernel_sources():
    # drivers/pci/controller/vmd.c vmd_ids[]: v6.12 plus mainline a41e364995bb.
    assert H.VMD_DEVICE_IDS == frozenset({
        0x201D, 0x28C0, 0x467F, 0x4C3D, 0xA77F, 0x7D0B, 0xAD0B, 0x9A0B,
        0x28C1, 0xB60B, 0xB06F, 0xB07F, 0xD70B, 0xD73B,
    })
    # drivers/ata/ahci.c ahci_pci_tbl[]: every Intel entry (163 IDs).
    assert len(H.AHCI_INTEL_DEVICE_IDS) == 163
    assert {0x282A, 0x2822, 0x9DD3, 0xA102, 0x02D7, 0x43D6} <= H.AHCI_INTEL_DEVICE_IDS
    assert not (H.VMD_DEVICE_IDS & H.AHCI_INTEL_DEVICE_IDS)
    assert (H.INTEL_VENDOR, H.PCI_CLASS_STORAGE_RAID, H.PCI_CLASS_STORAGE_EXPRESS) == (
        0x8086, 0x0104, 0x0108,
    )
    source = (ROOT / "src" / "beamo_wipe" / "hidden_storage.py").read_text(encoding="utf-8")
    for citation in ("drivers/pci/controller/vmd.c", "drivers/ata/ahci.c", "pci_ids.h"):
        assert citation in source


# --- classification from lspci fixtures ---------------------------------------


@pytest.mark.parametrize(
    ("name", "kind", "reason"),
    [
        ("vmd_enabled", H.HINT_VMD, ""),
        ("vmd_unbound", H.HINT_VMD, ""),
        ("rst_raid", H.HINT_RST, ""),
        ("ahci_normal", H.HINT_NONE, "nvme_visible"),
        ("nonintel_raid", H.HINT_NONE, "other_raid"),
        ("vmd_with_nvme", H.HINT_NONE, "nvme_visible"),
    ],
)
def test_lspci_fixtures_classify_only_intel_vmd_and_rst(name, kind, reason):
    hint = H.classify(_lspci(name), _only_boot())
    assert hint.kind == kind
    assert hint.reason == reason


def test_driver_state_is_recorded_for_the_log_only():
    assert H.classify(_lspci("vmd_enabled"), _only_boot()).log_detail() == "kind=vmd driver=vmd"
    assert H.classify(_lspci("vmd_unbound"), _only_boot()).log_detail() == "kind=vmd driver=unbound"
    assert H.classify(_lspci("rst_raid"), _only_boot()).log_detail() == "kind=rst driver=ahci"
    assert H.classify(None, _only_boot()).log_detail() == "kind=generic reason=unreadable"


def test_malformed_or_odd_lspci_is_unreadable():
    assert _lspci("malformed") is None
    assert H.parse_lspci(None) is None  # type: ignore[arg-type]
    # A driver line before any device, or two driver lines for one device.
    assert H.parse_lspci("\tKernel driver in use: vmd\n") is None
    twice = (PCI / "lspci_vmd_enabled.txt").read_text(encoding="utf-8").replace(
        "\tKernel driver in use: vmd\n", "\tKernel driver in use: vmd\n\tKernel driver in use: ahci\n"
    )
    assert H.parse_lspci(twice) is None
    assert H.classify(_lspci("malformed"), _only_boot()).kind == ""


def test_intel_raid_device_not_in_the_kernel_tables_stays_generic():
    unknown = H.PciFunction("00:17.0", 0x8086, 0x1234, H.PCI_CLASS_STORAGE_RAID, "")
    assert H.classify((unknown,), _only_boot()).reason == "other_raid"
    # Intel SATA in plain AHCI class with nothing else: not a VMD/RST case.
    ahci = H.PciFunction("00:17.0", 0x8086, 0x9DD3, 0x0106, "ahci")
    assert H.classify((ahci,), _only_boot()).reason == "no_vmd_rst"
    assert H.classify((), _only_boot()).reason == "no_pci"


def test_vmd_alongside_another_raid_controller_stays_generic():
    functions = _lspci("vmd_enabled") + _lspci("nonintel_raid")
    assert H.classify(functions, _only_boot()).kind == ""


# --- discovery gating (fail closed) -------------------------------------------


def test_vmd_present_but_disks_visible_gives_no_message():
    happy = _discovery("lsblk_multi_mixed.json")
    assert selectable_disks(happy)
    hint = H.classify(_lspci("vmd_enabled"), happy)
    assert (hint.kind, hint.reason) == ("", "disk_observed")


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: replace(d, boot_identified=False),
        lambda d: replace(d, boot=None),
        lambda d: replace(d, error="fake discovery", error_code="discovery_failed"),
        # Another disk was seen but not listed (read-only, mounted, ...).
        lambda d: replace(d, excluded=d.excluded + (
            ExcludedDevice("Fake internal disk", ("mounted",), path="/dev/nvme0n1"),
        )),
        # An entry without a path cannot be tied to the Beamo USB.
        lambda d: replace(d, excluded=d.excluded + (ExcludedDevice("Unknown", ("unknown",)),)),
        lambda d: replace(d, physical_observations=d.physical_observations + (
            replace(d.boot, path="/dev/sda", is_boot=False),
        )),
        lambda d: replace(d, disks=d.disks + (replace(d.boot, path="/dev/sda", is_boot=False),)),
    ],
)
def test_any_doubt_about_discovery_keeps_the_generic_text(mutate):
    base = _only_boot()
    assert H.classify(_lspci("vmd_enabled"), base).kind == H.HINT_VMD
    assert H.classify(_lspci("vmd_enabled"), mutate(base)).kind == ""


def test_no_boot_identity_keeps_the_generic_text():
    blocked = _discovery("lsblk_no_boot.json", boot="")
    assert H.classify(_lspci("vmd_enabled"), blocked).kind == ""


def test_partitions_nested_under_the_beamo_usb_are_accepted():
    base = _only_boot()
    child = ExcludedDevice("Beamo partition", ("unsupported device",), path="/dev/sdb2",
                           parent_path="/dev/sdb")
    grandchild = ExcludedDevice("Nested", ("unsupported device",), path="/dev/mapper/x",
                                parent_path="/dev/sdb2")
    nested = replace(base, excluded=base.excluded + (replace(child, children=(grandchild,)),))
    assert H.classify(_lspci("vmd_enabled"), nested).kind == H.HINT_VMD


# --- sysfs reader ------------------------------------------------------------


def _symlinks_work(tmp_path) -> bool:
    try:
        os.symlink("target", tmp_path / "probe-link")
    except (OSError, NotImplementedError):
        return False
    os.unlink(tmp_path / "probe-link")
    return True


def _build_sysfs(tmp_path, case: str) -> str:
    spec = json.loads((PCI / "sysfs_cases.json").read_text(encoding="utf-8"))[case]
    root = tmp_path / case
    devices = root / "bus" / "pci" / "devices"
    devices.mkdir(parents=True)
    for address, (vendor, device, pci_class, driver) in spec.items():
        entry = devices / address
        try:
            entry.mkdir()
        except OSError:
            pytest.skip("this host cannot name directories like sysfs PCI addresses")
        (entry / "vendor").write_text(vendor + "\n", encoding="ascii")
        (entry / "device").write_text(device + "\n", encoding="ascii")
        (entry / "class").write_text(pci_class + "\n", encoding="ascii")
        if driver:
            os.symlink(f"../../../bus/pci/drivers/{driver}", entry / "driver")
    return str(root)


@pytest.mark.parametrize(
    ("case", "kind"),
    [
        ("vmd_bound", H.HINT_VMD),
        ("vmd_unbound", H.HINT_VMD),
        ("rst_raid", H.HINT_RST),
        ("ahci_normal", ""),
        ("nonintel_raid", ""),
        ("vmd_with_nvme", ""),
    ],
)
def test_sysfs_fixtures_classify_like_lspci(tmp_path, case, kind):
    if not _symlinks_work(tmp_path) and case != "vmd_unbound":
        pytest.skip("this host cannot create the fake driver symlinks")
    functions = H.read_sysfs(_build_sysfs(tmp_path, case))
    assert functions is not None
    assert H.classify(functions, _only_boot()).kind == kind


def test_sysfs_reads_driver_state(tmp_path):
    if not _symlinks_work(tmp_path):
        pytest.skip("this host cannot create the fake driver symlinks")
    functions = H.read_sysfs(_build_sysfs(tmp_path, "vmd_bound"))
    assert functions is not None
    by_address = {fn.address: fn for fn in functions}
    assert by_address["0000:00:0e.0"] == H.PciFunction("0000:00:0e.0", 0x8086, 0x9A0B, 0x0104, "vmd")
    assert by_address["0000:00:00.0"].driver == ""


def test_unreadable_sysfs_fails_closed(tmp_path):
    # No sysfs at all.
    assert H.read_sysfs(str(tmp_path / "missing")) is None
    root = _build_sysfs(tmp_path, "vmd_unbound")
    entry = Path(root) / "bus" / "pci" / "devices" / "0000:00:0e.0"
    # A malformed value.
    (entry / "vendor").write_text("intel\n", encoding="ascii")
    assert H.read_sysfs(root) is None
    # An unreadable value (a directory where a file belongs).
    (entry / "vendor").unlink()
    (entry / "vendor").mkdir()
    assert H.read_sysfs(root) is None
    (entry / "vendor").rmdir()
    # A missing value.
    assert H.read_sysfs(root) is None
    (entry / "vendor").write_text("0x8086\n", encoding="ascii")
    assert H.read_sysfs(root) is not None
    # An unexpected entry name.
    (Path(root) / "bus" / "pci" / "devices" / "not-a-pci-address").mkdir()
    assert H.read_sysfs(root) is None
    assert H.classify(H.read_sysfs(root), _only_boot()).reason == "unreadable"


def test_sysfs_errors_fail_closed_on_any_host(monkeypatch):
    """Fake directory listing and reads, so this runs where ':' is not a valid name."""
    files = {
        "0000:00:0e.0": {"vendor": "0x8086\n", "device": "0x9a0b\n", "class": "0x010400\n"},
    }

    def listdir(path):
        if path.replace("\\", "/").endswith("bus/pci/devices"):
            return list(files)
        raise FileNotFoundError(path)

    def read_text(path):
        parts = path.replace("\\", "/").split("/")
        value = files.get(parts[-2], {}).get(parts[-1])
        if value is None:
            raise FileNotFoundError(path)
        if isinstance(value, BaseException):
            raise value
        return value

    monkeypatch.setattr(H.os, "listdir", listdir)
    monkeypatch.setattr(H, "_read_text", read_text)
    monkeypatch.setattr(H.os.path, "lexists", lambda _p: False)
    functions = H.read_sysfs("/fake-sys")
    assert functions == (H.PciFunction("0000:00:0e.0", 0x8086, 0x9A0B, 0x0104, ""),)
    assert H.classify(functions, _only_boot()).kind == H.HINT_VMD
    for bad in (PermissionError("denied"), UnicodeDecodeError("ascii", b"\xff", 0, 1, "bad"),
                "0x8086 0x1\n", "", "0x\n", "0x10000\n", "8086\n"):
        files["0000:00:0e.0"]["vendor"] = bad
        assert H.read_sysfs("/fake-sys") is None, bad
    files["0000:00:0e.0"]["vendor"] = "0x8086\n"
    # A driver link that cannot be read, or names something odd.
    monkeypatch.setattr(H.os.path, "lexists", lambda _p: True)
    monkeypatch.setattr(H.os, "readlink", lambda _p: (_ for _ in ()).throw(PermissionError()))
    assert H.read_sysfs("/fake-sys") is None
    monkeypatch.setattr(H.os, "readlink", lambda _p: "../../drivers/v md")
    assert H.read_sysfs("/fake-sys") is None
    monkeypatch.setattr(H.os, "readlink", lambda _p: "../../../bus/pci/drivers/vmd")
    assert H.read_sysfs("/fake-sys")[0].driver == "vmd"
    # Too many functions is not a shape this check understands.
    many = {f"0000:{i // 256:02x}:{(i // 8) % 32:02x}.{i % 8}": files["0000:00:0e.0"]
            for i in range(H.MAX_FUNCTIONS + 1)}
    files.clear()
    files.update(many)
    assert H.read_sysfs("/fake-sys") is None


def test_sysfs_reader_only_opens_files_for_reading(tmp_path, monkeypatch):
    import builtins

    root = _build_sysfs(tmp_path, "vmd_unbound")
    modes = []
    real_open = builtins.open

    def spy(path, mode="r", *args, **kwargs):
        modes.append(mode)
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", spy)
    assert H.read_sysfs(root) is not None
    assert modes and set(modes) == {"r"}


# --- recovery text -------------------------------------------------------------


def test_owner_approved_wording_is_exact():
    assert Rec.HIDDEN_STORAGE_HAPPENED == APPROVED_HEADING
    assert Rec.HIDDEN_STORAGE_STEPS == APPROVED_STEPS
    assert Rec.HIDDEN_STORAGE_WARNING == APPROVED_WARNING
    for kind in (H.HINT_VMD, H.HINT_RST):
        sections = Rec.recovery_for_empty(kind)
        assert sections.happened == APPROVED_HEADING
        assert sections.meaning == Rec.MEANING_EMPTY
        assert sections.next_step == "\n".join((*APPROVED_STEPS, APPROVED_WARNING))
        assert sections.technical == ""


@pytest.mark.parametrize("hint", ["", "generic", "VMD", None, 0, "vmd "])
def test_anything_else_keeps_the_generic_text_byte_for_byte(hint):
    assert Rec.recovery_for_empty(hint) == _generic()  # type: ignore[arg-type]
    assert Rec.recovery_for_empty() == _generic()


# --- wizard: display only -------------------------------------------------------


def test_demo_hidden_scenario_shows_the_specific_text():
    wiz = _at_empty(make_demo_wizard(scenario="hidden"))
    assert wiz.screen == Screen.PICK_EMPTY
    assert wiz.empty_storage_hint == H.HINT_VMD
    assert demo_pci_functions() == H.parse_lspci(DEMO_LSPCI_VMD)


def test_demo_empty_scenario_stays_generic():
    wiz = _at_empty(make_demo_wizard(scenario="empty"))
    assert wiz.screen == Screen.PICK_EMPTY
    assert wiz.hidden_storage_probe is None
    assert wiz.empty_storage_hint == ""


def test_selectable_list_and_boot_exclusion_are_unchanged():
    for fixture in sorted(p.name for p in FIX.glob("lsblk_*.json")):
        plain = _discovery(fixture)
        probed = _discovery(fixture)
        before = (repr(probed), selectable_disks(probed), probed.boot)
        wiz = Wizard(probed, DryRunRunner(), dry_run=True)
        wiz.hidden_storage_probe = lambda: _lspci("vmd_enabled")
        _ = wiz.empty_storage_hint
        assert wiz.discovery is probed
        assert (repr(probed), selectable_disks(probed), probed.boot) == before
        assert repr(probed) == repr(plain), fixture
        assert wiz.selectable == selectable_disks(plain), fixture
        # The Beamo USB is never selectable, hint or not.
        if probed.boot is not None:
            assert probed.boot.path not in {d.path for d in wiz.selectable}


def test_hidden_scenario_lists_exactly_the_empty_scenarios_disks():
    hidden = _at_empty(make_demo_wizard(scenario="hidden"))
    empty = _at_empty(make_demo_wizard(scenario="empty"))
    assert hidden.empty_storage_hint == H.HINT_VMD
    assert repr(hidden.discovery) == repr(empty.discovery)
    assert hidden.selectable == empty.selectable == ()
    assert hidden.listed_disks == empty.listed_disks
    assert hidden.protected_boot_text == empty.protected_boot_text
    assert hidden.inventory_count == empty.inventory_count


def test_probe_is_never_called_while_disks_are_selectable():
    wiz = Wizard(_discovery("lsblk_multi_mixed.json"), DryRunRunner(), dry_run=True)

    def boom():
        raise AssertionError("probe must not run")

    wiz.hidden_storage_probe = boom
    assert wiz.selectable
    assert wiz.empty_storage_hint == ""


def test_probe_failure_keeps_the_generic_text():
    wiz = _at_empty(make_demo_wizard(scenario="empty"))

    def broken():
        raise OSError("sysfs went away")

    wiz.hidden_storage_probe = broken
    assert wiz.empty_storage_hint == ""
    wiz.hidden_storage_probe = lambda: ["not a PCI function"]
    wiz.discovery = replace(wiz.discovery)  # a new discovery recomputes
    assert wiz.empty_storage_hint == ""


def test_hint_is_computed_once_per_discovery():
    wiz = _at_empty(make_demo_wizard(scenario="empty"))
    calls = []

    def probe():
        calls.append(1)
        return _lspci("vmd_enabled")

    wiz.hidden_storage_probe = probe
    assert wiz.empty_storage_hint == H.HINT_VMD
    assert wiz.empty_storage_hint == H.HINT_VMD
    assert len(calls) == 1
    # A rediscovery that finds a disk drops the hint.
    wiz.discovery = _discovery("lsblk_multi_mixed.json")
    assert wiz.empty_storage_hint == ""
    assert len(calls) == 1


def test_hint_is_logged_without_disk_identity(monkeypatch):
    from beamo_wipe import diagnostics

    lines = []
    monkeypatch.setattr(diagnostics, "log_diag", lambda *a: lines.append(a))
    wiz = _at_empty(make_demo_wizard(scenario="hidden"))
    assert wiz.empty_storage_hint == H.HINT_VMD
    assert lines == [("wizard", "empty_storage_hint", "kind=vmd driver=vmd")]


def test_live_wizard_reads_sysfs_and_previews_cannot_reach_it():
    from beamo_wipe import app

    source = (ROOT / "src" / "beamo_wipe" / "app.py").read_text(encoding="utf-8")
    assert "wizard.hidden_storage_probe = hidden_storage.read_sysfs" in source
    assert app._parser().parse_args(["--scenario", "hidden"]).scenario == "hidden"


# --- rendered surfaces ---------------------------------------------------------


def test_plain_console_shows_the_steps(monkeypatch, capsys):
    from beamo_wipe.ui import console_wizard as console

    wiz = _at_empty(make_demo_wizard(scenario="hidden"))
    wiz.preview = False
    monkeypatch.setattr("builtins.input", lambda *_: (_ for _ in ()).throw(EOFError()))
    console._plain_loop(wiz)
    out = capsys.readouterr().out
    assert C.TITLE_EMPTY in out
    assert APPROVED_HEADING in out
    for line in (*APPROVED_STEPS, APPROVED_WARNING):
        assert line in out
    assert C.EMPTY_DISKS not in out


def test_plain_console_empty_scenario_is_unchanged(monkeypatch, capsys):
    from beamo_wipe.ui import console_wizard as console

    wiz = _at_empty(make_demo_wizard(scenario="empty"))
    wiz.preview = False
    monkeypatch.setattr("builtins.input", lambda *_: (_ for _ in ()).throw(EOFError()))
    console._plain_loop(wiz)
    out = capsys.readouterr().out
    assert Rec.format_recovery_text(_generic(), include_technical=True) in out
    assert APPROVED_HEADING not in out


def test_curses_shows_the_steps(monkeypatch):
    from beamo_wipe.ui import console_wizard as console
    from test_console_parity import _draw

    wiz = _at_empty(make_demo_wizard(scenario="hidden"))
    wiz.preview = False
    _shown, _packed, term = _draw(
        monkeypatch, wiz, keys=[console.curses.KEY_DOWN] * 12, h=24, w=80
    )
    seen = " ".join(" ".join(frame[y] for y in sorted(frame)) for frame in term.frames)
    flat = " ".join(seen.split())
    for text in (APPROVED_HEADING, "1. Restart and open the BIOS/UEFI setup.", "turn VMD off.",
                 "3. Save, then start from the Beamo USB again.", "recovery key."):
        assert text in flat, text
    assert all(console._display_cols(row) < 80 for frame in term.frames for row in frame.values())


def test_web_preview_has_the_hidden_scenario():
    import re

    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    assert "boot('hidden')" in html
    assert C.GALLERY_HIDDEN in html
    payload = json.loads(re.search(r"const P = (\{.*?\});\n", html, re.S).group(1))
    assert payload["hiddenRecovery"]["happened"] == APPROVED_HEADING
    assert payload["hiddenRecovery"]["next"] == "\n".join((*APPROVED_STEPS, APPROVED_WARNING))
    assert payload["emptyRecovery"]["happened"] == C.EMPTY_DISKS
    assert payload["emptyRecovery"]["next"] == Rec.NEXT_EMPTY
    assert 'mode === "empty" || mode === "hidden"' in html
    assert '.replace(/\\n/g, "<br>")' in html


def test_every_language_translates_the_hint():
    from beamo_wipe import lang

    try:
        for code in ("fr", "de", "es", "it"):
            lang.set_language(code)
            sections = Rec.recovery_for_empty(H.HINT_VMD)
            assert sections.happened != APPROVED_HEADING
            assert "Intel VMD (RST)" in sections.happened
            assert len(Rec.HIDDEN_STORAGE_STEPS) == 3
            assert [s[:3] for s in Rec.HIDDEN_STORAGE_STEPS] == ["1. ", "2. ", "3. "]
            assert "BitLocker" in sections.next_step
            assert "AHCI" in sections.next_step and "VMD" in sections.next_step
            assert C.GALLERY_HIDDEN != "Disk hidden by Intel VMD"
    finally:
        lang.set_language("en")
    assert Rec.recovery_for_empty(H.HINT_VMD).happened == APPROVED_HEADING
