# SPDX-License-Identifier: GPL-3.0-or-later
"""#151: disks are listed internal first, then external, in a stable order.

Proven internal transports (NVMe, SATA, SAS, virtio) that are not hot-plug
come first; the same transports reported removable/hot-plug (dock, enclosure,
hot-swap bay) next; other eligible transports; USB last. Within a group: bus,
model, serial, WWN, capacity, path. The order depends only on the disks, so a
re-scan of the same disks gives the same list. Selection, confirmation and
authorization stay bound to the disk (path + identity), never to a position.
The protected Beamo USB keeps its place. Fake lsblk data only.
"""

from __future__ import annotations

import itertools
import os
from pathlib import Path
import subprocess
import sys

import pytest

from beamo_wipe import disk_order, inventory, lang
from beamo_wipe.discover import discover
from beamo_wipe.disk_order import (
    GROUP_EXTERNAL, GROUP_HOTPLUG, GROUP_INTERNAL, GROUP_OTHER, location_group, pick_order,
)
from beamo_wipe.models import Disk, DiskKind, Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.wizard import Wizard

ROOT = Path(__file__).resolve().parents[1]
ENV = {"BEAMO_WIPE_DRY_RUN": "1", "BEAMO_WIPE_BOOT_DEVICE": "/dev/sdc"}
TB = 1_000_000_000_000

# Path order puts the USB backup drive (sda) second; the internal SATA SSD
# (sdb), a hot-plug SATA dock (sdd), the NVMe and a USB stick (sde) follow.
EXPECTED = ["/dev/nvme0n1", "/dev/sdb", "/dev/sdd", "/dev/sde", "/dev/sda"]


def _node(name, size, tran, rota, model, serial, *, hotplug=False, rm=False, children=None):
    out = {"name": name, "path": f"/dev/{name}", "size": size, "type": "disk", "tran": tran,
           "rota": rota, "rm": rm, "hotplug": hotplug, "model": model, "serial": serial}
    if children:
        out["children"] = children
    return out


def _part(name, size, fstype, label=None):
    part = {"name": name, "path": f"/dev/{name}", "type": "part", "size": size, "fstype": fstype}
    if label:
        part["label"] = label
    return part


def _nodes():
    return [
        _node("sda", 2_000_398_934_016, "usb", True, "WD Elements 25A3", "WX12A3456789", hotplug=True,
              children=[_part("sda1", 2_000_397_795_328, "exfat", "Backup")]),
        _node("sdb", 500_107_862_016, "sata", False, "Samsung SSD 860 EVO 500GB", "S3Z1NB0K123456A",
              children=[_part("sdb1", 500_000_000_000, "ext4")]),
        _node("sdc", 16_000_000_000, "usb", False, "Beamo Wipe", "BEAMOUSB001", hotplug=True, rm=True,
              children=[_part("sdc1", 15_500_000_000, "vfat", "BEAMO_WIPE")]),
        _node("sdd", 1_000_204_886_016, "sata", True, "TOSHIBA HDWD110", "X8ABCD12EFG", hotplug=True),
        _node("nvme0n1", 512_110_190_592, "nvme", False, "SK hynix PC611 512GB", "CN0ABC123DEF456",
              children=[_part("nvme0n1p1", 268_435_456, "vfat"),
                        _part("nvme0n1p2", 511_000_000_000, "ntfs", "Windows")]),
        _node("sde", 64_000_000_000, "usb", False, "SanDisk Ultra", "4C530001110508116423",
              hotplug=True, rm=True),
    ]


def _discover(nodes=None):
    return discover(lsblk_payload={"blockdevices": nodes if nodes is not None else _nodes()},
                    boot_path="/dev/sdc", mount_sources=[], cmdline="", env=ENV)


def _pick(nodes=None, rediscover=None):
    wiz = Wizard(_discover(nodes), DryRunRunner(), dry_run=True, rediscover=rediscover)
    wiz.preview = False
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    assert wiz.screen == Screen.PICK
    return wiz


def _down_order(wiz):
    seen = []
    for _ in range(len(wiz.selectable)):
        wiz.move_selection(1)
        seen.append(wiz.selected.path)
    return seen


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _disk(path, bus, *, hotplug=False, model="M", serial="S", wwn="", size=TB):
    return Disk(path=path, name=path.rsplit("/", 1)[-1], model=model, serial=serial, size_bytes=size,
                size_gb_label=str(size // 1_000_000_000), kind=DiskKind.SSD, bus=bus, label="",
                wwn=wwn, hotplug=hotplug)


# -- the order ---------------------------------------------------------------


def test_mixed_fixture_lists_internal_first_then_external():
    wiz = _pick()
    assert [d.path for d in pick_order(wiz.selectable)] == EXPECTED
    assert [d.path for d in wiz.selectable] != EXPECTED  # discovery order differs
    assert wiz.protected_boot.path == "/dev/sdc"
    assert "/dev/sdc" not in EXPECTED


@pytest.mark.parametrize(
    "bus,hotplug,group",
    [
        ("NVMe", False, GROUP_INTERNAL), ("SATA", False, GROUP_INTERNAL),
        ("SAS", False, GROUP_INTERNAL), ("virtio", False, GROUP_INTERNAL),
        ("NVMe", True, GROUP_HOTPLUG), ("SATA", True, GROUP_HOTPLUG), ("SAS", True, GROUP_HOTPLUG),
        ("MMC", False, GROUP_OTHER), ("other", False, GROUP_OTHER), ("", False, GROUP_OTHER),
        ("USB", False, GROUP_EXTERNAL), ("USB", True, GROUP_EXTERNAL),
    ],
)
def test_location_groups(bus, hotplug, group):
    assert location_group(_disk("/dev/x", bus, hotplug=hotplug)) == group


def test_within_a_group_bus_then_model_then_serial_then_path():
    disks = [
        _disk("/dev/sda", "SATA", model="b", serial="1"),
        _disk("/dev/nvme1n1", "NVMe", model="z", serial="9"),
        _disk("/dev/sdb", "SATA", model="A", serial="2"),
        _disk("/dev/sdc", "SATA", model="a", serial="1"),
        _disk("/dev/sde", "SATA", model="a", serial="1", wwn="0x2"),
        _disk("/dev/sdd", "SATA", model="a", serial="1", wwn="0x1"),
        _disk("/dev/sdg", "SATA", model="b", serial="1"),
        _disk("/dev/sdf", "SATA", model="b", serial="1"),
    ]
    got = [d.path for d in pick_order(disks)]
    assert got == ["/dev/nvme1n1", "/dev/sdc", "/dev/sdd", "/dev/sde", "/dev/sdb",
                   "/dev/sda", "/dev/sdf", "/dev/sdg"]


def test_order_does_not_depend_on_discovery_order():
    base = _nodes()
    for perm in itertools.permutations(base):
        wiz = Wizard(_discover(list(perm)), DryRunRunner(), dry_run=True)
        assert [d.path for d in pick_order(wiz.selectable)] == EXPECTED


def test_pick_order_never_adds_or_drops_a_disk():
    wiz = _pick()
    ordered = pick_order(wiz.selectable)
    assert sorted(d.path for d in ordered) == sorted(d.path for d in wiz.selectable)
    assert all(not d.is_boot for d in ordered)
    assert pick_order(()) == ()


# -- stable across Check disks again ----------------------------------------


def test_check_disks_again_keeps_the_same_order():
    reversed_nodes = list(reversed(_nodes()))
    wiz = _pick(rediscover=lambda: _discover(reversed_nodes))
    before = _down_order(wiz)
    assert before == EXPECTED
    assert wiz.open_refresh_confirm()
    assert wiz.confirm_refresh()
    assert wiz.screen == Screen.OWNER  # a re-scan asks again and clears the choice
    assert wiz.selected is None
    wiz.set_owner(True)
    wiz.continue_owner()
    assert [d.path for d in wiz.selectable] == [n["path"] for n in reversed_nodes if n["name"] != "sdc"]
    assert _down_order(wiz) == before


# -- selection is bound to the disk, not to a list position -----------------


def test_re_sorting_cannot_change_the_chosen_disk(monkeypatch):
    from beamo_wipe.safety import confirm_spec

    wiz = _pick()
    wiz.select_disk("/dev/sdd")
    expected = confirm_spec(wiz.selected, wiz.listed_disks).token
    # Re-sort the list (here: reverse path order). The choice, its
    # confirmation characters and its target do not move with the rows.
    monkeypatch.setattr(disk_order, "pick_order",
                        lambda disks: tuple(sorted(disks, key=lambda d: d.path, reverse=True)))
    assert wiz.selected.path == "/dev/sdd"
    wiz.continue_pick()
    assert wiz.screen == Screen.CONFIRM
    assert wiz.operation_disk.path == "/dev/sdd"
    assert wiz.confirm.token == expected
    assert wiz.confirm_input == "" and not wiz.token_ok


def test_up_down_steps_from_the_chosen_disk_in_the_shown_order():
    wiz = _pick()
    wiz.select_disk("/dev/sdd")  # third in the list
    wiz.move_selection(1)
    assert wiz.selected.path == "/dev/sde"
    wiz.move_selection(-1)
    wiz.move_selection(-1)
    assert wiz.selected.path == "/dev/sdb"
    wiz.move_selection(1000)
    assert wiz.selected.path == "/dev/sda"  # stays at the end
    wiz.move_selection(-1000)
    assert wiz.selected.path == "/dev/nvme0n1"


def test_a_rescan_in_another_order_keeps_the_target_and_authorization_key():
    from beamo_wipe.safety import confirm_spec

    wiz = _pick()
    wiz.select_disk("/dev/sda")  # the last row
    spec = confirm_spec(wiz.selected, wiz.listed_disks)
    wiz.continue_pick()
    wiz.set_confirm_input(wiz.confirm.token)
    assert wiz.confirm.token == spec.token
    wiz.continue_confirm()
    wiz.continue_method()
    assert wiz.screen == Screen.LAST_CHANCE
    key = wiz._operation_key()
    # The same disks in another order: same target, same authorization key.
    wiz.discovery = _discover(list(reversed(_nodes())))
    assert wiz._operation_key() == key
    assert wiz._authorization_matches()
    assert wiz.selected.path == "/dev/sda"
    assert not wiz.erase_enabled  # the countdown still governs Erase now
    assert not wiz.runner.started


# -- every view uses the same order -----------------------------------------


def test_comparison_numbers_follow_the_list():
    wiz = _pick()
    entries = inventory.comparison_entries(wiz.selectable, peers=wiz.listed_disks)
    numbers = {}
    for entry in entries:
        first, model = entry.splitlines()[:2]
        numbers[model.split(": ", 1)[1]] = int(first.rsplit(" ", 1)[-1])
    by_path = {d.path: wiz.disk_view(d).title for d in wiz.selectable}
    assert [numbers[by_path[p]] for p in EXPECTED] == [1, 2, 3, 4, 5]


def test_curses_lists_protected_usb_first_then_the_same_order():
    from beamo_wipe.ui import console_wizard as console

    wiz = _pick()
    blocks = console._pick_blocks(wiz, 80)
    assert blocks[0][0] is None  # protected Beamo USB, unchanged position
    assert [disk.path for disk, _ in blocks[1:]] == EXPECTED


def test_plain_console_numbers_follow_the_list_and_choose_that_disk(monkeypatch):
    from beamo_wipe.ui.console_wizard import _plain_loop

    wiz = _pick()
    printed = []
    answers = iter(["5"])

    def fake_input(_prompt=""):
        try:
            return next(answers)
        except StopIteration:
            wiz.shutdown()
            return ""

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr("builtins.print", lambda *a, **_k: printed.append(" ".join(map(str, a))))
    _plain_loop(wiz)
    numbered = [line for line in printed if line.startswith("[")]
    titles = {d.path: wiz.disk_view(d).title for d in wiz.selectable}
    assert numbered[:5] == [f"[{i}] {titles[p]}" for i, p in enumerate(EXPECTED, 1)]
    assert wiz.operation_disk is not None and wiz.operation_disk.path == "/dev/sda"
    assert wiz.confirm_input == "" and not wiz.runner.started


def test_gtk_and_tk_sources_use_the_shared_order():
    for name in ("ui/accessible_wizard.py", "ui/tk_wizard.py", "ui/console_wizard.py", "wizard.py",
                 "inventory.py", "gallery.py"):
        source = (ROOT / "src" / "beamo_wipe" / name).read_text(encoding="utf-8")
        assert "key=lambda d: d.path" not in source, name
        assert "pick_order(" in source, name


def test_gtk_lists_disk_buttons_in_the_shared_order():
    script = r'''
import json, sys
from types import ModuleType, SimpleNamespace
repo = ModuleType("gi.repository")
for name in ("Gtk", "Gdk", "GLib", "Pango", "Atk"):
    setattr(repo, name, SimpleNamespace())
gi = ModuleType("gi"); gi.require_version = lambda *_a: None; gi.repository = repo
sys.modules["gi"] = gi; sys.modules["gi.repository"] = repo
from beamo_wipe.ui import accessible_wizard as accessible
src = open(accessible.__file__, encoding="utf-8").read()
block = src[src.index("elif screen == Screen.PICK:"):]
block = block[:block.index("elif screen in (Screen.PICK_EMPTY, Screen.PICK_BLOCKED):")]
print(json.dumps({"loop": "for disk in pick_order(self.w.selectable):" in block,
                  "same": accessible.pick_order is __import__("beamo_wipe.disk_order", fromlist=["x"]).pick_order}))
'''
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=ROOT,
        env={**os.environ, "PYTHONPATH": os.pathsep.join(filter(None, [str(ROOT / "src"), os.environ.get("PYTHONPATH", "")]))},
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().endswith('{"loop": true, "same": true}')


def test_preview_payload_carries_the_order_and_the_page_sorts_by_it():
    from beamo_wipe import gallery
    from beamo_wipe.demo import discovery_for_scenario

    payload = gallery._disks_payload("happy")
    result = discovery_for_scenario("happy")
    expected = [d.path for d in pick_order(result.disks)]
    assert [d["path"] for d in sorted(payload, key=lambda d: d["order"])] == expected
    html = gallery.gallery_html()
    assert "list.sort((a, b) => (a.isBoot - b.isBoot) || (a.order - b.order));" in html
    assert "a.path.localeCompare(b.path)" not in html


# -- Tk ----------------------------------------------------------------------


@pytest.mark.parametrize("size", [(800, 600), (1280, 820)])
def test_tk_rows_top_down_follow_the_list_and_selection_by_disk(size):
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    wiz = _pick()
    app = TkWizard(wiz)
    try:
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app._draw()
        for _ in range(6):
            app.root.update()
        rows = sorted(app._pick_cards.items(), key=lambda kv: kv[1].winfo_y())
        assert [p for p, _ in rows] == EXPECTED
        # Down from nothing chooses the first row; the chosen disk is the
        # one whose card is expanded, whatever its position.
        app.root.focus_force()
        app.root.update()
        app.root.event_generate("<Down>")
        for _ in range(4):
            app.root.update()
        assert wiz.selected.path == EXPECTED[0]
        app._click_disk("/dev/sda")
        for _ in range(4):
            app.root.update()
        assert wiz.selected.path == "/dev/sda"
        assert not getattr(app._pick_cards["/dev/sda"], "_beamo_compact_row", False)
        assert all(getattr(app._pick_cards[p], "_beamo_compact_row", False) for p in EXPECTED[:-1])
        # The protected Beamo USB card keeps its place after the list.
        found = []

        def walk(widget):
            if getattr(widget, "_beamo_protected_boot", False):
                found.append(widget)
            for child in widget.winfo_children():
                walk(child)

        walk(app.root)
        assert len(found) == 1
        last = max(card.winfo_y() for card in app._pick_cards.values())
        assert found[0].winfo_rooty() > app._pick_cards[EXPECTED[-1]].winfo_rooty()
        assert last >= 0
    finally:
        app._teardown()
