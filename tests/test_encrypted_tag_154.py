# SPDX-License-Identifier: GPL-3.0-or-later
"""#154: tag disks 'BitLocker (Windows encryption)' / 'Encrypted (LUKS)'.

From the FSTYPE lsblk already reported for the disk's partitions and opened
volumes (no new probing). A recognition cue on the pick list in every view;
display only: eligibility, identity and confirmation are unchanged, and the
copy never suggests unlocking or recovery. Fake lsblk data only.
"""

from __future__ import annotations

from pathlib import Path
import re

import pytest

from beamo_wipe import inventory, lang
from beamo_wipe.discover import discover
from beamo_wipe.models import Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.safety import confirm_spec
from beamo_wipe.wizard import Wizard

ROOT = Path(__file__).resolve().parents[1]
GB = 1_000_000_000
ENV = {"BEAMO_WIPE_DRY_RUN": "1", "BEAMO_WIPE_BOOT_DEVICE": "/dev/sdz"}
EFI = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"
MSR = "e3c9e316-0b5c-4db8-817d-f92df00215ae"
BASIC = "ebd0a0a2-b9e5-4433-87c0-68b6b72699c7"
BITLOCKER = "BitLocker (Windows encryption)"
LUKS = "Encrypted (LUKS)"


def _disk(name, size, tran, model, serial, children=None, fstype=None):
    node = {"name": name, "path": f"/dev/{name}", "size": size, "type": "disk", "tran": tran,
            "rota": False, "rm": tran == "usb", "hotplug": tran == "usb", "model": model, "serial": serial}
    if fstype:
        node["fstype"] = fstype
    if children:
        node["children"] = children
    return node


def _part(name, size, fstype=None, label=None, parttype=None, children=None):
    node = {"name": name, "path": f"/dev/{name}", "type": "part", "size": size}
    for key, value in (("fstype", fstype), ("label", label), ("parttype", parttype), ("children", children)):
        if value:
            node[key] = value
    return node


def _nodes():
    return [
        _disk("sdz", 16 * GB, "usb", "Beamo Wipe", "BEAMOUSB001",
              [_part("sdz1", 15_500_000_000, "vfat", "BEAMO_WIPE")]),
        _disk("nvme0n1", 512_110_190_592, "nvme", "SK hynix PC611", "CN0ABC123DEF456", [
            _part("nvme0n1p1", 268_435_456, "vfat", parttype=EFI),
            _part("nvme0n1p2", 16_777_216, parttype=MSR),
            _part("nvme0n1p3", 510 * GB, "BitLocker", parttype=BASIC),
        ]),
        _disk("nvme1n1", 1_000_204_886_016, "nvme", "Samsung SSD 980", "S64ANS0R123456X", [
            _part("nvme1n1p1", 536_870_912, "vfat", parttype=EFI),
            _part("nvme1n1p2", 1 * GB, "ext4"),
            _part("nvme1n1p3", 998 * GB, "crypto_LUKS"),
        ]),
        _disk("sda", 2_000_398_934_016, "sata", "WDC WD20EZRZ", "WD-WCC4M1234567",
              [_part("sda1", 2000 * GB, "ntfs", "Backup")]),
        _disk("sdb", 500_107_862_016, "sata", "Samsung SSD 860", "S3Z1NB0K123456A",
              [_part("sdb1", 500 * GB, "ext4")]),
        # Whole-disk LUKS, no partition table: no nested component, no tag.
        _disk("sdc", 250_059_350_016, "sata", "Crucial MX500", "MX500WHOLE01", fstype="crypto_LUKS"),
        _disk("sdd", 64 * GB, "usb", "SanDisk Ultra", "4C530001110508116423",
              [_part("sdd1", 64 * GB, "BitLocker")]),
        # An opened LUKS volume (crypt child) and a BitLocker partition on one disk.
        _disk("sde", 1_000_204_886_016, "sata", "Seagate ST1000", "ZN1ABCDE", [
            _part("sde1", 400 * GB, "crypto_LUKS",
                  children=[{"name": "luks-1", "path": "/dev/mapper/luks-1", "type": "crypt",
                             "size": 399 * GB, "fstype": "ext4"}]),
            _part("sde2", 600 * GB, "bitlocker"),
        ]),
    ]


EXPECTED = {
    "/dev/nvme0n1": (BITLOCKER,), "/dev/nvme1n1": (LUKS,), "/dev/sda": (), "/dev/sdb": (),
    "/dev/sdc": (), "/dev/sdd": (BITLOCKER,), "/dev/sde": (BITLOCKER, LUKS),
}


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _wizard(nodes=None):
    res = discover(lsblk_payload={"blockdevices": nodes or _nodes()}, boot_path="/dev/sdz",
                   mount_sources=[], cmdline="", env=ENV)
    wiz = Wizard(res, DryRunRunner(), dry_run=True)
    wiz.preview = False
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    assert wiz.screen == Screen.PICK
    return wiz


def _tags(wiz, path):
    disk = next(d for d in wiz.selectable if d.path == path)
    return inventory.encryption_tags(wiz.nested_components(disk))


def test_bitlocker_and_luks_partitions_are_tagged_and_others_are_not():
    wiz = _wizard()
    assert {d.path for d in wiz.selectable} == set(EXPECTED)
    for path, tags in EXPECTED.items():
        assert _tags(wiz, path) == tags, path


def test_tags_are_display_only():
    wiz = _wizard()
    # Every disk stays eligible and confirmable exactly as without tags.
    plain = _wizard([{**n, "children": [{k: v for k, v in c.items() if k != "fstype"}
                                        for c in n.get("children", [])]}
                     if n["name"] != "sdz" else n for n in _nodes()])
    assert [d.path for d in wiz.selectable] == [d.path for d in plain.selectable]
    for disk in wiz.selectable:
        other = next(d for d in plain.selectable if d.path == disk.path)
        assert confirm_spec(disk, wiz.listed_disks).token == confirm_spec(other, plain.listed_disks).token
    # Only presentation code reads the tags. #187: the screens get them
    # through Wizard.disk_tags (encryption tags plus an earlier erase).
    users = sorted(p.relative_to(ROOT / "src").as_posix()
                   for p in (ROOT / "src/beamo_wipe").rglob("*.py")
                   if re.search(r"(?<![\w.])encryption_tags\(|inventory\.encryption_tags\(",
                                p.read_text(encoding="utf-8")))
    assert users == ["beamo_wipe/gallery.py", "beamo_wipe/inventory.py", "beamo_wipe/wizard.py"]
    readers = sorted(p.relative_to(ROOT / "src").as_posix()
                     for p in (ROOT / "src/beamo_wipe").rglob("*.py")
                     if "disk_tags(" in p.read_text(encoding="utf-8"))
    assert readers == ["beamo_wipe/ui/accessible_wizard.py", "beamo_wipe/ui/console_wizard.py",
                       "beamo_wipe/ui/tk_wizard.py", "beamo_wipe/wizard.py"]


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_tag_copy_never_suggests_unlocking(code):
    def get(key):
        return getattr(inventory, key) if code == "en" else lang.translated(code, "inventory", key)

    bitlocker, luks = get("TAG_BITLOCKER"), get("TAG_LUKS")
    assert "BitLocker" in bitlocker and "LUKS" in luks
    # Whole words: German "Verschlüsselung" (encryption) is not "Schlüssel" (key).
    banned = r"\b(unlock|recover|key|password|déverrou|récupér|clé|mot de passe|entsperr|schlüssel|" \
             r"wiederherst|passwort|desbloq|recuper|clave|contraseña|sblocc|chiave|ripristin)"
    for text in (bitlocker, luks):
        assert not re.search(banned, text, re.I), (code, text)
    if code == "en":
        assert (bitlocker, luks) == (BITLOCKER, LUKS)


def test_curses_and_plain_console_show_the_tag(monkeypatch):
    from beamo_wipe.ui import console_wizard as console

    wiz = _wizard()
    blocks = {disk.path: "\n".join(block) for disk, block in console._pick_blocks(wiz, 80) if disk}
    for path, tags in EXPECTED.items():
        for tag in (BITLOCKER, LUKS):
            assert (tag in blocks[path]) == (tag in tags), (path, tag)
    printed = []
    monkeypatch.setattr("builtins.print", lambda *a, **_k: printed.append(" ".join(map(str, a))))

    def fake_input(_prompt=""):
        wiz.shutdown()
        return ""

    monkeypatch.setattr("builtins.input", fake_input)
    console._plain_loop(wiz)
    text = "\n".join(printed)
    assert text.count(BITLOCKER) == 2 + 1  # nvme0n1, sdd, and sde (with LUKS)
    assert BITLOCKER + " · " + LUKS in text.splitlines()  # its own line under sde


def test_gtk_speaks_and_shows_the_tag():
    source = (ROOT / "src/beamo_wipe/ui/accessible_wizard.py").read_text(encoding="utf-8")
    block = source[source.index("elif screen == Screen.PICK:"):]
    block = block[:block.index("elif screen in (Screen.PICK_EMPTY, Screen.PICK_BLOCKED):")]
    assert 'tags = " · ".join(self.w.disk_tags(disk))' in block  # #187: same tags + erased
    assert "for part in (text, tags, hint, summary) if part" in block
    assert "self.label(tags)" in block


def test_preview_payload_and_markup(monkeypatch):
    from beamo_wipe import gallery

    wiz = _wizard()
    monkeypatch.setattr(gallery, "discovery_for_scenario", lambda _: wiz.discovery)
    payload = {d["path"]: d for d in gallery._disks_payload()}
    for path, tags in EXPECTED.items():
        assert payload[path]["encryptionTags"] == list(tags)
    assert payload["/dev/sdz"]["encryptionTags"] == []
    html = gallery.gallery_html()
    assert "...(d.encryptionTags || []), d.contentsHint, d.contentsSummary" in html
    assert '<span class="enc-tag">${esc(t)}</span>' in html
    assert ".enc-tag { border: 1px solid var(--border-strong);" in html


# -- Tk ------------------------------------------------------------------------


@pytest.mark.parametrize("size,text_size,code", [((800, 600), "standard", "en"), ((800, 600), "extra", "en"),
                                                 ((800, 600), "extra", "fr"), ((1280, 820), "standard", "en")])
def test_tk_rows_and_card_show_the_tag_without_clipping(size, text_size, code):
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    lang.set_language(code)
    wiz = _wizard()
    wiz.text_size = text_size
    bitlocker, luks = inventory.TAG_BITLOCKER, inventory.TAG_LUKS
    app = TkWizard(wiz)
    try:
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app._draw()
        for _ in range(6):
            app.root.update()
        for path, tags in EXPECTED.items():
            details = next(w for w in _walk(app._pick_cards[path])
                           if getattr(w, "_beamo_compact_details", False))
            shown = str(details.cget("text")).replace("\n", " ")
            for tag in (bitlocker, luks):
                expected = tag in [inventory.TAG_BITLOCKER if t == BITLOCKER else inventory.TAG_LUKS
                                   for t in tags]
                assert (tag in shown) == expected, (path, tag, shown)
        wiz.select_disk("/dev/sde")
        app._pick_ensure_visible = True
        app._draw()
        for _ in range(8):
            app.root.update()
        card = app._pick_cards["/dev/sde"]
        tags = [w for w in _walk(card) if getattr(w, "_beamo_encryption_tag", "")]
        assert [w.cget("text") for w in tags] == [bitlocker, luks]
        for tag in tags:
            assert tag.winfo_width() >= tag.winfo_reqwidth() - 1
            assert tag.winfo_rootx() + tag.winfo_width() <= card.winfo_rootx() + card.winfo_width()
        # Untagged disk: no tag row on its card.
        wiz.select_disk("/dev/sda")
        app._draw()
        for _ in range(6):
            app.root.update()
        assert not [w for w in _walk(app._pick_cards["/dev/sda"]) if getattr(w, "_beamo_encryption_tag", "")]
    finally:
        app._teardown()


def _walk(widget):
    out = [widget]
    for child in widget.winfo_children():
        out.extend(_walk(child))
    return out
