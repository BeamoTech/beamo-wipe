# SPDX-License-Identifier: GPL-3.0-or-later
"""#147: Pick a disk names partitions by label and file system. Display only.

A disk card says what is on it, for example "Windows (NTFS) 237 GB ·
Recovery 1 GB · +2 more", from the lsblk JSON discovery already reads
(LABEL, PARTLABEL, FSTYPE, FSVER, PARTTYPE, PARTTYPENAME). Nothing is
mounted. Labels are untrusted: cleaned, capped, quoted and escaped. The
facts never reach eligibility, exclusion or identity comparison. Fake lsblk
data only; nothing is erased.
"""

from __future__ import annotations

import copy
import subprocess
from pathlib import Path

import pytest

from beamo_wipe import inventory
from beamo_wipe import lang
from beamo_wipe.discover import discover
from beamo_wipe.models import Screen, VolumeFacts
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.wizard import Wizard

ROOT = Path(__file__).resolve().parents[1]
ENV = {"BEAMO_WIPE_DRY_RUN": "1", "BEAMO_WIPE_BOOT_DEVICE": "/dev/sdb"}
EFI = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"
MSR = "e3c9e316-0b5c-4db8-817d-f92df00215ae"
WINRE = "de94bba4-06d1-4d40-a16a-bfd50179d6ac"
BASIC = "ebd0a0a2-b9e5-4433-87c0-68b6b72699c7"
LINUX = "0fc63daf-8483-4772-8e79-3d69ed7de477"


def _part(name, size, **fields):
    return {"name": name, "path": f"/dev/{name}", "size": size, "type": "part", **fields}


def _disk(name, size, model, serial, tran, children):
    return {
        "name": name, "path": f"/dev/{name}", "size": size, "type": "disk",
        "tran": tran, "rota": tran == "sata", "model": model, "serial": serial,
        "children": children,
    }


def _payload(sda_children=None):
    """Boot USB plus four eligible disks: Windows, BitLocker, Linux, blank."""
    return {"blockdevices": [
        _disk("sdb", 16_000_000_000, "Beamo Wipe", "BEAMOUSB001", "usb", [
            _part("sdb1", 15_500_000_000, label="BEAMO_WIPE", fstype="vfat", fsver="FAT32"),
        ]),
        _disk("nvme0n1", 256_060_514_304, "Samsung SSD 970 EVO", "S4EVNX0N123456", "nvme", [
            _part("nvme0n1p1", 104_857_600, fstype="vfat", fsver="FAT32", parttype=EFI,
                  parttypename="EFI System", partlabel="EFI system partition"),
            _part("nvme0n1p2", 16_777_216, parttype=MSR, parttypename="Microsoft reserved",
                  partlabel="Microsoft reserved partition"),
            _part("nvme0n1p3", 236_975_000_000, fstype="ntfs", parttype=BASIC,
                  parttypename="Microsoft basic data", partlabel="Basic data partition"),
            _part("nvme0n1p4", 1_000_000_000, fstype="ntfs", parttype=WINRE,
                  parttypename="Windows recovery environment"),
        ]),
        _disk("sda", 1_000_204_886_016, "WDC WD10EZEX-00WN4A0", "WD-WCC6Y1234567", "sata",
              sda_children if sda_children is not None else [
                  _part("sda1", 500_000_000_000, fstype="BitLocker", parttype=BASIC,
                        parttypename="Microsoft basic data", label="Backup"),
                  _part("sda2", 500_000_000_000, fstype="crypto_LUKS", parttype=LINUX,
                        parttypename="Linux filesystem"),
              ]),
        _disk("sdd", 256_060_514_304, "Crucial MX500", "MX500AABBCC11", "sata", [
            _part("sdd1", 536_870_912, fstype="vfat", fsver="FAT32", parttype=EFI,
                  parttypename="EFI System"),
            _part("sdd2", 247_000_000_000, fstype="ext4", parttype=LINUX,
                  parttypename="Linux filesystem", label="home"),
            _part("sdd3", 8_000_000_000, fstype="swap", parttypename="Linux swap"),
        ]),
        _disk("sde", 32_017_047_552, "SanDisk Ultra", "USBDATA001", "usb", [
            _part("sde1", 32_017_047_552),
        ]),
    ]}


def _discover(payload):
    return discover(lsblk_payload=payload, boot_path="/dev/sdb", mount_sources=[],
                    cmdline="", env=ENV)


@pytest.fixture(autouse=True)
def _preview_env(monkeypatch):
    monkeypatch.setenv("BEAMO_WIPE_DEMO", "1")
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    yield
    lang.set_language("en")


def _summary(result, path):
    return inventory.contents_summary(inventory.nested_under(path, result.excluded))


def _eligibility(result):
    """Everything safety decides, without display text."""
    return (
        result.error, result.boot_identified, result.boot.path if result.boot else None,
        tuple(sorted(d.path for d in result.selectable)),
        tuple(sorted((d.path, d.serial, d.size_bytes, d.wwn, d.is_boot) for d in result.disks)),
        tuple(sorted((e.path, e.reasons, e.parent_path) for e in result.excluded)),
    )


# --- Rendering of realistic disks ---------------------------------------------------------


def test_windows_disk_reads_as_windows_recovery_and_more():
    result = _discover(_payload())
    assert _summary(result, "/dev/nvme0n1") == "Windows (NTFS) 237 GB · Recovery 1 GB · +2 more"


def test_bitlocker_and_luks_are_named_as_encrypted():
    result = _discover(_payload())
    assert _summary(result, "/dev/sda") == (
        '"Backup" (BitLocker encrypted) 500 GB · LUKS encrypted 500 GB'
    )


def test_linux_disk_names_label_format_and_roles():
    result = _discover(_payload())
    # Three components fit; none is folded into "+1 more".
    assert _summary(result, "/dev/sdd") == '"home" (ext4) 247 GB · Swap 8 GB · EFI system 1 GB'


def test_unlabeled_partition_without_a_format_reads_unknown():
    result = _discover(_payload())
    assert _summary(result, "/dev/sde") == "Unknown format 32 GB"


def test_boot_usb_keeps_its_name():
    result = _discover(_payload())
    assert _summary(result, "/dev/sdb") == '"BEAMO_WIPE" (FAT32) 16 GB'


def test_every_role_is_recognised_without_a_label():
    def item(**fields):
        volume = VolumeFacts(node_type="part", size_bytes=1_000_000_000, size_gb_label="1", **fields)
        return inventory._volume_item(inventory.ExcludedDevice("x", (), volume=volume))

    assert item(parttype=EFI) == "EFI system 1 GB"
    assert item(parttype="0xef") == "EFI system 1 GB"
    assert item(parttype=MSR) == "Microsoft reserved 1 GB"
    assert item(parttypename="Windows recovery environment") == "Recovery 1 GB"
    assert item(parttype="0x27") == "Recovery 1 GB"
    # PARTLABEL is owner text: it never makes a role.
    assert item(partlabel="Windows recovery environment", fstype="ntfs") == (
        '"Windows recovery environment" (NTFS) 1 GB'
    )
    # Default GPT names say nothing an owner would recognise.
    assert item(partlabel="Basic data partition", fstype="ntfs") == "NTFS 1 GB"
    for fstype, fsver, name in (
        ("ntfs", "", "NTFS"), ("vfat", "fat32", "FAT32"), ("vfat", "fat16", "FAT16"),
        ("vfat", "", "FAT"), ("exfat", "", "exFAT"), ("ext4", "", "ext4"),
        ("apfs", "", "APFS"), ("hfsplus", "", "HFS+"), ("swap", "", "Swap"),
        ("bitlocker", "", "BitLocker encrypted"), ("crypto_luks", "", "LUKS encrypted"),
        ("", "", "Unknown format"), ("made_up_fs", "", "Unknown format"),
    ):
        assert inventory.format_name(VolumeFacts(fstype=fstype, fsver=fsver)) == name


def test_windows_is_named_only_with_evidence_and_one_candidate():
    two = _payload()
    nvme = two["blockdevices"][1]["children"]
    nvme.append(_part("nvme0n1p5", 10_000_000_000, fstype="ntfs", parttype=BASIC))
    result = _discover(two)
    assert "Windows" not in _summary(result, "/dev/nvme0n1")  # two candidates: no guess
    alone = _payload(sda_children=[_part("sda1", 1_000_204_886_016, fstype="ntfs")])
    assert _summary(_discover(alone), "/dev/sda") == "NTFS 1 TB (1000 GB)"  # no Windows marks


def test_a_component_with_a_reason_is_never_folded():
    def child(name, size, reasons=()):
        volume = VolumeFacts(node_type="part", fstype="ntfs", label=name,
                             size_bytes=size, size_gb_label=str(size // 10**9))
        return inventory.ExcludedDevice(name, tuple(reasons), volume=volume)

    kids = (child("A", 9 * 10**9), child("B", 8 * 10**9), child("C", 7 * 10**9),
            child("D", 1 * 10**9, [inventory.REASON_MOUNTED]))
    assert inventory.contents_summary(kids) == (
        '"A" (NTFS) 9 GB · "B" (NTFS) 8 GB · "D" (NTFS) 1 GB (mounted or in use) · +1 more'
    )


def test_summary_reads_in_the_chosen_language():
    result = _discover(_payload())  # discovered in English
    lang.set_language("fr")
    assert _summary(result, "/dev/nvme0n1") == "Windows (NTFS) 237 GB · Récupération 1 GB · +2 autres"
    assert _summary(result, "/dev/sda").startswith("« Backup » (chiffrée BitLocker)")
    lang.set_language("de")
    assert _summary(result, "/dev/sde") == "Unbekanntes Format 32 GB"


# --- Untrusted labels ---------------------------------------------------------------------


@pytest.mark.parametrize("raw, shown", [
    ("Beamo USB (protected)", "Beamo USB (protected)"),
    ("Ｂｅａｍｏ", "Beamo"),                       # fullwidth, NFKC
    ("A" * 60, "A" * 23 + "…"),                                    # capped
    ('He said "erase"', "He said 'erase'"),                             # cannot close quotes
    ("«q» “q” „q‟", "'q' 'q' 'q'"),
    ("‮evil‬", "evil"),                                       # bidi override
    ("a​b⁦c⁩", "abc"),                                   # zero-width, isolates
    ("one\ntwo\r\tthree four", "one two three four"),              # line breaks
    ("\x1b[31mred\x1b[0m", "[31mred[0m"),                               # terminal escapes
    ("é́́́́", "é́́"),          # stacked marks
    ("   ", ""),
    (None, ""),
    (42, ""),
])
def test_clean_volume_text(raw, shown):
    assert inventory.clean_volume_text(raw) == shown


def _hostile(label):
    payload = _payload(sda_children=[_part("sda1", 1_000_204_886_016, fstype="ntfs", label=label)])
    return payload


@pytest.mark.parametrize("label", [
    "Beamo USB (protected)", "BEAMO_WIPE", "EFI system", "Recovery",
    "Cannot erase: mounted", '"; <script>alert(1)</script>', "Ｂｅａｍｏ",
    "A" * 128,
])
def test_hostile_label_is_quoted_and_cannot_pass_for_ui_text(label):
    result = _discover(_hostile(label))
    summary = _summary(result, "/dev/sda")
    name = inventory.clean_volume_text(label)
    assert summary == f'"{name}" (NTFS) 1 TB (1000 GB)'
    assert summary.count('"') == 2  # only the quotes we added
    assert "/dev/sda" in {d.path for d in result.selectable}  # still a normal target


@pytest.mark.parametrize("label", ["‮evil", "a​b", "x\ny", "\x1b[2J"])
def test_label_with_control_characters_still_fails_closed_as_before(label):
    """Discovery already refuses control/format characters in labels; the
    disk is not offered. #147 does not change that."""
    result = _discover(_hostile(label))
    assert "/dev/sda" not in {d.path for d in result.selectable}
    assert _summary(result, "/dev/sda") == ""


def test_web_preview_escapes_the_summary():
    from beamo_wipe import gallery

    page = gallery.gallery_html()
    script = page.split("<script>", 1)[1].split("</script>", 1)[0]
    start = script.index("function nestedComponents(")
    body = script[start:script.index("\nfunction ", start + 1)]
    assert "esc(d.contentsSummary)" in body and "esc(P.nestedIntro)" in body
    # The payload is embedded with "<" escaped, so a label cannot end the script.
    assert "<script>alert" not in page


def test_gtk_summary_is_plain_text():
    """The summary goes through label(): Gtk.Label(label=...), never markup."""
    src = (ROOT / "src/beamo_wipe/ui/accessible_wizard.py").read_text(encoding="utf-8")
    helper = src[src.index("    def label(self, text: str"):]
    helper = helper[:helper.index("\n    def ", 10)]
    assert "widget = Gtk.Label(label=text)" in helper and "markup" not in helper
    pick = src[src.index("summary = inventory.contents_summary(children)"):]
    pick = pick[:pick.index("expander = Gtk.Expander.new(inventory.COMPARE_TITLE)")]
    assert "self.label(nested, focusable=True)" in pick and "markup" not in pick


# --- Display only ---------------------------------------------------------------------------


@pytest.mark.parametrize("payload", [_payload(), _hostile("Beamo USB (protected)"),
                                     _hostile("A" * 128)], ids=["mixed", "imitation", "long"])
def test_volume_facts_cannot_change_eligibility(monkeypatch, payload):
    real = _discover(copy.deepcopy(payload))
    monkeypatch.setattr(inventory, "volume_facts", lambda *_a, **_k: VolumeFacts())
    blank = _discover(copy.deepcopy(payload))
    assert _eligibility(real) == _eligibility(blank)


def test_removing_labels_and_formats_keeps_the_same_targets():
    payload = _payload()
    bare = copy.deepcopy(payload)
    for disk in bare["blockdevices"]:
        for child in disk.get("children") or []:
            for key in ("label", "partlabel", "fstype", "fsver", "parttypename"):
                child.pop(key, None)
    with_names, without = _discover(payload), _discover(bare)
    assert sorted(d.path for d in with_names.selectable) == sorted(d.path for d in without.selectable)
    assert [(e.path, e.reasons) for e in with_names.excluded] == [
        (e.path, e.reasons) for e in without.excluded
    ]


def test_safety_and_identity_never_read_the_display_facts():
    for name in ("safety.py", "identity.py", "nwipe_runner.py", "wizard.py"):
        src = (ROOT / "src/beamo_wipe" / name).read_text(encoding="utf-8")
        assert "contents_summary" not in src and "volume_facts" not in src, name
        assert ".volume" not in src, name


def test_nested_components_are_never_selectable():
    result = _discover(_payload())
    wiz = Wizard(result, DryRunRunner(), dry_run=True)
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    assert wiz.screen == Screen.PICK
    for path in ("/dev/nvme0n1p3", "/dev/nvme0n1p4", "/dev/sda1", "/dev/sdb1", "/dev/sdb"):
        wiz.select_disk(path)
        assert wiz.selected is None
    wiz.select_disk("/dev/nvme0n1")
    assert wiz.selected is not None and wiz.selected.path == "/dev/nvme0n1"
    assert not wiz.runner.started


def test_rendering_never_runs_a_command(monkeypatch):
    """No mount, blkid or other probe: the summary is built from lsblk JSON."""
    result = _discover(_payload())

    def refuse(*_a, **_k):
        raise AssertionError("no command may run while rendering partition names")

    for name in ("run", "Popen", "check_output", "call"):
        monkeypatch.setattr(subprocess, name, refuse)
    monkeypatch.setattr("os.system", refuse)
    for disk in result.disks:
        inventory.card_nesting_text(inventory.nested_under(disk.path, result.excluded))
    src = (ROOT / "src/beamo_wipe/inventory.py").read_text(encoding="utf-8")
    assert "import subprocess" not in src and "blkid" not in src
    assert '"mount"' not in src and "os.mount" not in src


# --- Surfaces ---------------------------------------------------------------------------------


def _pick_wizard():
    wiz = Wizard(_discover(_payload()), DryRunRunner(), dry_run=True)
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    assert wiz.screen == Screen.PICK
    return wiz


def test_curses_shows_the_summary():
    from beamo_wipe.ui import console_wizard as console

    blocks = console._pick_blocks(_pick_wizard(), 80)
    nvme = next(block for disk, block in blocks if disk is not None and disk.path == "/dev/nvme0n1")
    flat = " ".join(line.strip() for line in nvme)
    assert "Windows (NTFS) 237 GB · Recovery 1 GB · +2 more" in flat
    assert all(len(line) <= 80 for line in nvme)


def test_plain_console_shows_the_summary(monkeypatch, capsys):
    from beamo_wipe.ui import console_wizard as console

    wiz = _pick_wizard()
    monkeypatch.setattr("builtins.input", lambda _: (_ for _ in ()).throw(EOFError()))
    console._plain_loop(wiz)
    out = capsys.readouterr().out
    assert "Windows (NTFS) 237 GB · Recovery 1 GB · +2 more" in out
    assert '"Backup" (BitLocker encrypted) 500 GB' in out


def test_gtk_speaks_the_summary_with_the_disk_button():
    src = (ROOT / "src/beamo_wipe/ui/accessible_wizard.py").read_text(encoding="utf-8")
    assert "summary = inventory.contents_summary(children)" in src
    assert 'spoken = ". ".join(part for part in (text, hint, summary) if part)' in src
    assert "select.get_accessible().set_name(spoken)" in src


def test_web_preview_payload_carries_the_summary():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    assert '"contentsSummary": "\\"Work\\" (NTFS) 256 GB \\u00b7 FAT32 1 GB"' in html
    assert '"contents": "data"' in html  # the classification key is untouched


# --- Rendered Tk ------------------------------------------------------------------------------


@pytest.fixture
def tk_pick():
    from beamo_wipe.ui.tk_wizard import TkWizard
    from test_tk_runtime import _needs_display

    created = []

    def build(text_size="standard", size=(800, 600)):
        _needs_display()
        wiz = _pick_wizard()
        wiz.preview = False
        wiz.text_size = text_size
        app = TkWizard(wiz)
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app._draw()
        app.root.update()
        created.append(app)
        return wiz, app

    yield build
    for app in created:
        app._teardown()


def _texts(app):
    out = []

    def walk(widget):
        try:
            out.append(" ".join(str(widget.cget("text")).split()))
        except Exception:
            pass
        for child in widget.winfo_children():
            walk(child)

    walk(app._body)
    return "\n".join(out)


@pytest.mark.parametrize("size", [(800, 600), (1280, 820)])
def test_tk_cards_show_the_summary(tk_pick, size):
    wiz, app = tk_pick(size=size)
    shown = _texts(app)
    assert "Windows (NTFS) 237 GB · Recovery 1 GB · +2 more" in shown
    assert '"home" (ext4) 247 GB' in shown
    assert wiz.selected is None and not wiz.runner.started


@pytest.mark.parametrize("text_size", ["standard", "large", "extra"])
def test_tk_pick_fits_800x600(tk_pick, text_size):
    from test_tk_runtime import _clipping_problems

    _wiz, app = tk_pick(text_size)
    assert _clipping_problems(app) == []
