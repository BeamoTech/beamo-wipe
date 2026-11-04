# SPDX-License-Identifier: GPL-3.0-or-later
"""#149: compact one-line disk rows on Pick a disk; the selected one expands.

Unselected eligible disks are one line (model, kind and connection, contents
summary, capacity). The selected disk keeps the full card: serial with the
#148 marks, notes, contents hint, partitions and, when another eligible disk
has the same size, a Compare disks link. The protected Beamo USB keeps its
full card. Selection is by disk (path), never by list position. Fake lsblk
data only; nothing is erased.
"""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from beamo_wipe import inventory, lang
from beamo_wipe.discover import discover
from beamo_wipe.models import Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.wizard import Wizard

GB = 1_000_000_000
ENV = {"BEAMO_WIPE_DRY_RUN": "1", "BEAMO_WIPE_BOOT_DEVICE": "/dev/sdb"}
LONG_MODEL = "Generic Ultra Long Model Name Enclosure SuperSpeedPlusBridgeControllerX9000"


def _d(name, size, model, serial, tran="sata", children=None):
    out = {"name": name, "path": f"/dev/{name}", "size": size, "type": "disk", "tran": tran,
           "rota": False, "model": model, "serial": serial}
    if children:
        out["children"] = children
    return out


def _p(name, size, fstype, label=None):
    part = {"name": name, "path": f"/dev/{name}", "type": "part", "size": size, "fstype": fstype}
    if label:
        part["label"] = label
    return part


def _payload(long_model=False):
    return {"blockdevices": [
        _d("sdb", 16 * GB, "Beamo Wipe", "BEAMOUSB001", "usb",
           [_p("sdb1", 15_500_000_000, "vfat", "BEAMO_WIPE")]),
        _d("nvme0n1", 256_060_514_304, "Samsung SSD 970 EVO", "S4EVNX0N111111", "nvme",
           [_p("nvme0n1p1", 1 * GB, "vfat"), _p("nvme0n1p2", 255 * GB, "ntfs", "Windows")]),
        _d("nvme1n1", 256_060_514_304, "Samsung SSD 980", "S4EVNX0N222222", "nvme"),
        _d("sda", 1_000_204_886_016, "WDC WD10EZEX-00WN4A0", "WD-WCC6Y1234567", "sata",
           [_p("sda1", 1_000_000_000_000, "ntfs", "Photos")]),
        _d("sdc", 512_110_190_592, "Crucial MX500", "MX500AABBCC11", "sata",
           [_p("sdc1", 512 * GB, "ext4")]),
        _d("sdd", 2_000_398_934_016, LONG_MODEL if long_model else "Seagate ST2000DM008",
           "ZFL0ABCD", "sata"),
        _d("sde", 32 * GB, "SanDisk Ultra Fit", "4C530001230508116423", "usb",
           [_p("sde1", 32 * GB, "exfat", "STUFF")]),
    ]}


def _discover(long_model=False):
    return discover(lsblk_payload=_payload(long_model), boot_path="/dev/sdb",
                    mount_sources=[], cmdline="", env=ENV)


def _pick_wizard(long_model=False, discovery=None):
    wiz = Wizard(discovery or _discover(long_model), DryRunRunner(), dry_run=True)
    wiz.preview = False
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    assert wiz.screen == Screen.PICK
    return wiz


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


@pytest.fixture
def tk_pick():
    from beamo_wipe.ui.tk_wizard import TkWizard
    from test_tk_runtime import _needs_display

    created = []

    def build(wiz=None, *, text_size="standard", size=(800, 600), select=None):
        _needs_display()
        wiz = wiz or _pick_wizard()
        wiz.text_size = text_size
        if select:
            wiz.select_disk(select)
        app = TkWizard(wiz)
        created.append(app)
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app._draw()
        _settle(app)
        return wiz, app

    yield build
    for app in created:
        app._teardown()


def _settle(app):
    for _ in range(6):
        app.root.update()


def _texts(widget):
    out = []

    def walk(node):
        try:
            text = node.cget("text")
        except Exception:
            text = None
        if isinstance(text, str) and text:
            out.append(" ".join(text.split()))
        for child in node.winfo_children():
            walk(child)

    walk(widget)
    return out


def _flat(widget):
    return " ".join(_texts(widget)).replace(" ", "")


def _visible_rows(app):
    canvas = app._pick_canvas
    app.root.update_idletasks()
    bbox = canvas.bbox("all")
    top = canvas.yview()[0] * float(bbox[3]) if bbox else 0.0
    bottom = top + canvas.winfo_height()
    return sum(
        1 for card in app._pick_cards.values()
        if card.winfo_y() >= top - 1 and card.winfo_y() + card.winfo_height() <= bottom + 1
    )


def _compact(card):
    return bool(getattr(card, "_beamo_compact_row", False))


# --- Collapsed and expanded rows ----------------------------------------------------------


def test_unselected_disks_are_one_line_rows_without_the_serial(tk_pick):
    from beamo_wipe import copy as C

    wiz, app = tk_pick()
    assert wiz.selected is None
    assert len(app._pick_cards) == 6
    for disk in wiz.selectable:
        card = app._pick_cards[disk.path]
        view = wiz.disk_view(disk)
        assert _compact(card), disk.path
        shown = " ".join(_texts(card))
        assert view.title in shown and view.capacity in shown
        assert f"{view.kind_chip} · {view.connection}" in shown
        summary = inventory.contents_summary(wiz.nested_components(disk))
        if summary:
            assert summary in shown
        hint = C.contents_hint(disk)
        if hint:
            assert hint in shown
        assert disk.serial not in _flat(card)
        # One line: the row is no taller than a line of bold text plus pads.
        assert card.winfo_height() <= app.font_bold.metrics("linespace") + 24


def test_selected_disk_expands_with_serial_partitions_and_notes(tk_pick):
    wiz, app = tk_pick(select="/dev/nvme0n1")
    disk = wiz.selected
    view = wiz.disk_view(disk)
    card = app._pick_cards[disk.path]
    assert not _compact(card)
    flat = _flat(card)
    assert view.marked_id.replace(" ", "") in flat  # S4EVNX0N[111111], once
    assert flat.count(disk.serial[:8]) == 1
    assert view.comparison_note.replace(" ", "") in flat
    nesting = inventory.card_nesting_text(wiz.nested_components(disk))
    assert nesting.replace("\n", "").replace(" ", "") in flat
    for other in wiz.selectable:
        if other.path != disk.path:
            assert _compact(app._pick_cards[other.path])


def test_protected_usb_keeps_its_full_card(tk_pick):
    from beamo_wipe import copy as C

    wiz, app = tk_pick()
    protected = [w for w in app.root.winfo_children()]
    boxes = []

    def walk(node):
        if getattr(node, "_beamo_protected_boot", False):
            boxes.append(node)
        for child in node.winfo_children():
            walk(child)

    for widget in protected:
        walk(widget)
    assert len(boxes) == 1
    card = boxes[0]
    assert not _compact(card)
    shown = " ".join(_texts(card))
    assert C.BOOT_USB_BANNER in shown
    assert "BEAMOUSB001" in _flat(card)
    assert wiz.discovery.boot.path not in app._pick_cards


# --- Keyboard and identity ---------------------------------------------------------------


def test_down_and_up_move_the_selection_and_expand(tk_pick):
    wiz, app = tk_pick()
    order = sorted(d.path for d in wiz.selectable)
    app._on_key(SimpleNamespace(keysym="Down", char=""))
    _settle(app)
    assert wiz.selected.path == order[0]
    assert not _compact(app._pick_cards[order[0]])
    app._on_key(SimpleNamespace(keysym="Down", char=""))
    _settle(app)
    assert wiz.selected.path == order[1]
    assert not _compact(app._pick_cards[order[1]])
    assert _compact(app._pick_cards[order[0]])
    app._on_key(SimpleNamespace(keysym="Up", char=""))
    _settle(app)
    assert wiz.selected.path == order[0]
    # The expanded row stays in view and is the only expanded row.
    assert [p for p, c in app._pick_cards.items() if not _compact(c)] == [order[0]]
    assert not wiz.runner.started and wiz.screen == Screen.PICK


def test_selection_follows_the_disk_not_its_list_position(tk_pick):
    wiz, app = tk_pick(select="/dev/sdc")
    chosen = wiz.selected
    # The same snapshot in a different order (e.g. a re-sorted list).
    shuffled = replace(
        wiz.discovery,
        selectable=tuple(reversed(wiz.discovery.selectable)),
        disks=tuple(reversed(wiz.discovery.disks)),
    )
    wiz.discovery = shuffled
    app._draw()
    _settle(app)
    assert wiz.selected is chosen and wiz.selected.serial == "MX500AABBCC11"
    assert [p for p, c in app._pick_cards.items() if not _compact(c)] == ["/dev/sdc"]
    # Rows are always in the same (path) order, whatever order discovery used.
    assert list(app._pick_cards) == sorted(app._pick_cards)
    # Down goes to the next disk in that order, not to "index + 1" of the
    # reversed tuple.
    app._on_key(SimpleNamespace(keysym="Down", char=""))
    _settle(app)
    assert wiz.selected.path == "/dev/sdd"


def test_clicking_a_row_selects_that_disk(tk_pick):
    wiz, app = tk_pick()
    app._click_disk("/dev/sda")
    _settle(app)
    assert wiz.selected.path == "/dev/sda" and wiz.selected.serial == "WD-WCC6Y1234567"
    assert not _compact(app._pick_cards["/dev/sda"])
    assert not wiz.runner.started


def test_boot_usb_cannot_be_chosen_from_a_row_or_the_keyboard(tk_pick):
    wiz, app = tk_pick()
    app._click_disk(wiz.discovery.boot.path)
    assert wiz.selected is None
    for _ in range(10):
        app._on_key(SimpleNamespace(keysym="Down", char=""))
        assert wiz.selected is not None and not wiz.selected.is_boot
    _settle(app)


# --- Similar disks ---------------------------------------------------------------------------


def _links(card):
    found = []

    def walk(node):
        if getattr(node, "_beamo_compare_link", False):
            found.append(node)
        for child in node.winfo_children():
            walk(child)

    walk(card)
    return found


def test_compare_link_only_on_a_selected_disk_with_a_same_size_peer(tk_pick):
    wiz, app = tk_pick(select="/dev/nvme0n1")
    assert len(_links(app._pick_cards["/dev/nvme0n1"])) == 1
    assert all(not _links(c) for p, c in app._pick_cards.items() if p != "/dev/nvme0n1")
    wiz.select_disk("/dev/sdc")  # 512 GB: no other disk that size
    app._draw()
    _settle(app)
    assert not any(_links(c) for c in app._pick_cards.values())


def test_compare_link_opens_the_read_only_comparison(tk_pick):
    wiz, app = tk_pick(select="/dev/nvme0n1")
    chosen = wiz.selected
    link = _links(app._pick_cards["/dev/nvme0n1"])[0]
    link.focus_set()
    link._key()  # Space or Enter on the focused link
    _settle(app)
    # focus_lastfor: the widget that holds focus once the window has it
    # (the test window may not own the desktop focus).
    focused = app.root.focus_lastfor()
    assert getattr(focused, "_beamo_comparison", False)
    assert focused.winfo_ismapped()
    assert wiz.selected is chosen and wiz.screen == Screen.PICK
    assert not wiz.runner.started


# --- Fit -----------------------------------------------------------------------------------


def test_at_least_four_rows_visible_at_800x600(tk_pick):
    # Six eligible disks plus the same-size warning above the list.
    _wiz, app = tk_pick()
    assert _visible_rows(app) == 6
    # A typical selected disk (serial and one partition line) still leaves
    # four whole rows in view.
    _wiz, app = tk_pick(select="/dev/sda")
    assert _visible_rows(app) >= 4
    # The fullest card (same-size note, contents hint, partitions, Compare
    # link) still leaves three whole rows (documented in docs/screens.md).
    _wiz, app = tk_pick(select="/dev/nvme0n1")
    assert _visible_rows(app) >= 3


@pytest.mark.parametrize("size, text_size", [
    ((800, 600), "standard"), ((800, 600), "large"), ((800, 600), "extra"),
    ((1280, 820), "standard"), ((1280, 820), "extra"),
])
def test_rows_wrap_and_never_clip(tk_pick, size, text_size):
    from test_tk_runtime import _clipping_problems, _off_window_problems

    wiz, app = tk_pick(_pick_wizard(long_model=True), text_size=text_size, size=size,
                       select="/dev/sda")
    for label in _rows_labels(app):
        assert label.winfo_reqwidth() <= label.winfo_width() + 2, label.cget("text")
    flat = _flat(app._pick_cards["/dev/sdd"])
    assert LONG_MODEL.replace(" ", "") in flat
    assert _clipping_problems(app) == []
    assert not _off_window_problems(app)
    assert wiz.selected.path == "/dev/sda"


def _rows_labels(app):
    import tkinter as tk

    out = []

    def walk(node):
        if isinstance(node, tk.Label):
            out.append(node)
        for child in node.winfo_children():
            walk(child)

    for card in app._pick_cards.values():
        walk(card)
    return out


# --- Web preview -----------------------------------------------------------------------------


def test_web_preview_mirrors_compact_rows_and_arrow_keys():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    assert "function compactDiskRow(d)" in html
    assert 'if (screen === "pick" && !d.isBoot && !sel) return compactDiskRow(d);' in html
    # Every value is escaped; the boot USB never takes the compact form.
    row = html[html.index("function compactDiskRow(d)"):html.index("function diskCard(d)")]
    for field in ("d.path", "d.name", "details", "d.size"):
        assert f"${{esc({field})}}" in row
    # Up/Down select by path from the rendered (path-sorted) list.
    keys = html[html.index('if (screen === "pick" && ["ArrowUp", "ArrowDown"]'):]
    keys = keys[:keys.index("return;\n  }")]
    assert "selectable().map(d => d.path)" in keys
    assert "selectable().find(d => d.path === list[next])" in keys
