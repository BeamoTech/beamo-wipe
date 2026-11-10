# SPDX-License-Identifier: GPL-3.0-or-later
"""#148: Pick a disk shows each serial number once.

The card shows the serial once, with the part that differs from other
same-size disks in [brackets]. The note names only the character positions;
it never prints the characters again. When nothing is shared at either end,
there is nothing to mark and no note. Display only: confirmation tokens,
eligibility and identity checks are unchanged. Fake lsblk data only.
"""

from __future__ import annotations

import string
from pathlib import Path

import pytest

from beamo_wipe import copy as C
from beamo_wipe import inventory, lang
from beamo_wipe.discover import discover
from beamo_wipe.identity import present_disk
from beamo_wipe.models import Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.safety import confirm_spec, selectable_disks
from beamo_wipe.wizard import Wizard

ROOT = Path(__file__).resolve().parents[1]
GB = 1_000_000_000
LONG_A = "ZX9000LONGSERIALNUMBERTHATNEEDSWRAPPING0123456789ABCDEF"
LONG_B = "ZX9000LONGSERIALNUMBERTHATNEEDSWRAPPINX0123456789ABCDEF"


def _disk(name, size, model, serial, tran="sata"):
    return {"name": name, "path": f"/dev/{name}", "size": size, "type": "disk",
            "tran": tran, "rota": False, "model": model, "serial": serial}


def _payload():
    boot = _disk("sdb", 16 * GB, "Beamo Wipe", "BEAMOUSB001", tran="usb")
    boot["children"] = [{"name": "sdb1", "path": "/dev/sdb1", "type": "part",
                         "label": "BEAMO_WIPE", "fstype": "vfat", "size": 15_500_000_000}]
    return {"blockdevices": [
        boot,
        # Same size, shared prefix: only the ending differs.
        _disk("sda", 500_107_862_016, "Samsung SSD 870 EVO", "S4EVNX0N123456"),
        _disk("sdc", 500_107_862_016, "Samsung SSD 870 EVO", "S4EVNX0N123999"),
        # Same size, nothing shared at either end (the review's demo case).
        _disk("sdd", 256_060_514_304, "Crucial MX500", "MX500AABBCC11"),
        _disk("nvme0n1", 256_060_514_304, "Samsung SSD 970 EVO", "S4EVNX0N555555", tran="nvme"),
        # Same size, long serials that must wrap, differing in the middle.
        _disk("sde", 1_000_204_886_016, "Generic bridge disk", LONG_A),
        _disk("sdf", 1_000_204_886_016, "Generic bridge disk", LONG_B),
    ]}


ENV = {"BEAMO_WIPE_DRY_RUN": "1", "BEAMO_WIPE_BOOT_DEVICE": "/dev/sdb"}


def _discover():
    return discover(lsblk_payload=_payload(), boot_path="/dev/sdb", mount_sources=[],
                    cmdline="", env=ENV)


def _pick_wizard():
    wiz = Wizard(_discover(), DryRunRunner(), dry_run=True)
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    assert wiz.screen == Screen.PICK
    return wiz


def _serial_count(text: str, serial: str) -> int:
    """Occurrences of ``serial`` once marks and wrapping are removed."""
    flat = text.replace("[", "").replace("]", "").replace("\n", "")
    return flat.count(serial)


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


# --- Identity view --------------------------------------------------------------------------


def test_fixture_has_every_case():
    wiz = _pick_wizard()
    views = {d.path: wiz.disk_view(d) for d in wiz.selectable}
    assert len(views) == 6
    assert views["/dev/sda"].marked_id == "S4EVNX0N123[456]"
    assert views["/dev/sdc"].marked_id == "S4EVNX0N123[999]"
    assert views["/dev/sdd"].marked_id == "MX500AABBCC11"
    assert views["/dev/nvme0n1"].marked_id == "S4EVNX0N555555"
    assert views["/dev/sde"].marked_id == LONG_A[:38] + "[G]" + LONG_A[39:]


def test_note_names_positions_never_the_characters():
    wiz = _pick_wizard()
    for disk in wiz.selectable:
        view = wiz.disk_view(disk)
        assert view.id_value == disk.serial  # never shortened
        for note in view.notes:
            assert _serial_count(note, disk.serial) == 0
            if view.comparison_end > view.comparison_start:
                assert disk.serial[view.comparison_start:view.comparison_end] not in note.split()
    note = wiz.disk_view(next(d for d in wiz.selectable if d.path == "/dev/sda")).comparison_note
    # #152 wording: where it differs from the other disk of that size.
    assert note == (
        "Differs from the other 500 GB disk at characters 12 to 14. "
        "Check the full ID before choosing."
    )
    one = wiz.disk_view(next(d for d in wiz.selectable if d.path == "/dev/sde")).comparison_note
    assert one.startswith("Differs from the other 1 TB (1000 GB) disk at character 39.")


def test_nothing_shared_means_no_brackets_and_no_note():
    wiz = _pick_wizard()
    for path in ("/dev/sdd", "/dev/nvme0n1"):
        disk = next(d for d in wiz.selectable if d.path == path)
        view = wiz.disk_view(disk)
        assert (view.comparison_start, view.comparison_end, view.comparison_note) == (0, 0, "")
        assert view.marked_id == view.id_value == disk.serial
        assert view.notes == ()


def test_announcement_reads_the_serial_once():
    wiz = _pick_wizard()
    for disk in wiz.selectable:
        view = wiz.disk_view(disk)
        spoken = C.ACCESSIBLE_SELECT_DISK.format(disk=view.announcement)
        assert _serial_count(spoken, disk.serial) == 1
        # Orca hears the plain serial, not bracket characters.
        assert "[" not in spoken and f"{view.id_label}: {disk.serial}" in spoken


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_every_language_drops_the_repeated_characters(code):
    # #152 split the note into three templates; none prints the serial.
    for key in ("COMPARE_SERIAL_OTHER", "COMPARE_SERIAL_SIMILAR_ONE", "COMPARE_SERIAL_SIMILAR_MANY"):
        template = (getattr(inventory, key) if code == "en"
                    else lang.translated(code, "inventory", key))
        fields = {name for _, name, _, _ in string.Formatter().parse(template) if name}
        assert fields == {"size", "position", "reminder"}
    lang.set_language(code)
    wiz = _pick_wizard()
    for disk in wiz.selectable:
        view = wiz.disk_view(disk)
        assert _serial_count(C.ACCESSIBLE_SELECT_DISK.format(disk=view.announcement), disk.serial) == 1


# --- Display only -----------------------------------------------------------------------------


def test_marks_never_change_tokens_targets_or_identity():
    result = _discover()
    listed = (*result.selectable, result.boot)
    assert {d.path for d in selectable_disks(result)} == {
        "/dev/sda", "/dev/sdc", "/dev/sdd", "/dev/nvme0n1", "/dev/sde", "/dev/sdf"}
    for disk in result.selectable:
        plain = present_disk(disk, listed)
        picker = present_disk(disk, listed, compare_serials=True)
        for field in ("id_label", "id_value", "confirmable", "token_start", "token_end",
                      "duplicate_note", "ambiguous_note", "missing_note"):
            assert getattr(plain, field) == getattr(picker, field), field
        spec = confirm_spec(disk, listed)
        assert spec == confirm_spec(disk, listed)
        assert disk.serial.casefold().endswith(spec.token.casefold())


def test_only_presentation_reads_the_comparison():
    users = sorted(
        path.relative_to(ROOT / "src").as_posix()
        for path in (ROOT / "src/beamo_wipe").rglob("*.py")
        if "serial_differences(" in path.read_text(encoding="utf-8")  # #152 name
    )
    assert users == ["beamo_wipe/identity.py", "beamo_wipe/inventory.py"]
    for name in ("safety.py", "wizard.py", "nwipe_runner.py", "discover.py"):
        src = (ROOT / "src/beamo_wipe" / name).read_text(encoding="utf-8")
        assert "comparison_start" not in src and "marked_id" not in src


def test_choosing_a_marked_disk_still_needs_token_and_countdown():
    wiz = _pick_wizard()
    disk = next(d for d in wiz.selectable if d.path == "/dev/sda")
    view = wiz.disk_view(disk)
    wiz.select_disk(disk.path)
    wiz.continue_pick()
    assert wiz.screen == Screen.CONFIRM
    for typed in (view.marked_id, view.id_value[view.comparison_start:view.comparison_end], "[456]"):
        wiz.set_confirm_input(typed)
        assert not wiz.token_ok
        wiz.continue_confirm()
        assert wiz.screen == Screen.CONFIRM and not wiz.erase_enabled
    wiz.set_confirm_input(wiz.confirm.token)
    assert wiz.token_ok and not wiz.runner.started
    assert wiz.countdown_left == 5


# --- Curses, plain console, web preview, GTK -------------------------------------------------


def test_curses_cards_show_each_serial_once():
    from beamo_wipe.ui import console_wizard as console

    wiz = _pick_wizard()
    for width in (40, 80):
        for disk, block in console._pick_blocks(wiz, width):
            if disk is None:
                continue
            assert _serial_count("".join(block), disk.serial) == 1, (width, disk.path)
            assert all(console._display_cols(line) <= width for line in block)
    flat = "\n".join(line for d, b in console._pick_blocks(wiz, 80) if d for line in b)
    assert "Serial number: S4EVNX0N123[456]" in flat
    assert "Serial number: MX500AABBCC11" in flat


def _plain(monkeypatch, capsys, answers):
    from beamo_wipe.ui import console_wizard as console

    wiz = _pick_wizard()
    feed = iter(answers)

    def answer(_prompt=""):
        try:
            return next(feed)
        except StopIteration:
            raise EOFError() from None

    monkeypatch.setattr("builtins.input", answer)
    console._plain_loop(wiz)
    return wiz, capsys.readouterr().out


def test_plain_console_prints_each_serial_once(monkeypatch, capsys):
    wiz, out = _plain(monkeypatch, capsys, [])
    for disk in wiz.selectable:
        assert _serial_count(out, disk.serial) == 1, disk.path
    assert "Serial number: S4EVNX0N123[456]" in out
    assert C.CON_COMPARE in out
    assert inventory.COMPARE_INTRO not in out


def test_plain_console_comparison_on_request(monkeypatch, capsys):
    wiz, out = _plain(monkeypatch, capsys, ["C", ""])
    assert inventory.COMPARE_TITLE in out and inventory.COMPARE_INTRO in out
    assert wiz.screen == Screen.PICK and wiz.selected is None
    assert not wiz.runner.started


def test_web_preview_payload_shows_serial_once(monkeypatch):
    from beamo_wipe import gallery

    discovery = _discover()
    monkeypatch.setattr(gallery, "discovery_for_scenario", lambda _: discovery)
    for item in gallery._disks_payload():
        if item.get("isBoot"):
            continue
        serial = item["serial"]
        assert _serial_count(item["markedSerial"], serial) == 1
        assert _serial_count(item["comparisonNote"], serial) == 0


def test_gtk_pick_names_the_disk_from_one_announcement():
    src = (ROOT / "src/beamo_wipe/ui/accessible_wizard.py").read_text(encoding="utf-8")
    pick = src[src.index("elif screen == Screen.PICK:"):src.index("elif screen in (Screen.PICK_EMPTY")]
    assert "C.ACCESSIBLE_SELECT_DISK.format(disk=self.w.disk_view(disk).announcement)" in pick
    # The character-by-character reader stays in the Compare disks expander.
    assert "reader.set_selectable(True)" in pick and "reader.set_can_focus(True)" in pick


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


def _labels(widget):
    import tkinter as tk

    out = []

    def walk(node):
        if isinstance(node, tk.Label):
            out.append(node)
        for child in node.winfo_children():
            walk(child)

    walk(widget)
    return out


@pytest.mark.parametrize("size, text_size", [
    ((800, 600), "standard"), ((800, 600), "large"), ((800, 600), "extra"),
    ((1280, 820), "standard"),
])
def test_tk_cards_show_each_serial_once_unclipped(tk_pick, size, text_size):
    from test_tk_runtime import _clipping_problems, _off_window_problems

    wiz, app = tk_pick(text_size, size)
    # #149: unselected rows are one line without the serial; the selected
    # disk's card shows it once. Check the long, wrapping serial expanded.
    wiz.select_disk("/dev/sde")
    app._draw()
    app.root.update()
    for disk in wiz.selectable:
        view = wiz.disk_view(disk)
        labels = _labels(app._pick_cards[disk.path])
        texts = [str(label.cget("text")) for label in labels]
        expected = 1 if disk.path == "/dev/sde" else 0
        assert sum(_serial_count(text, disk.serial) for text in texts) == expected, disk.path
        if expected:
            # #152: Tk shows the plain serial and draws the differing
            # characters bold and underlined over it (no brackets).
            shown = view.id_value if view.comparison_marks else view.marked_id
            assert any(text.replace("\n", "") == shown for text in texts)
        for label in labels:
            assert label.winfo_reqwidth() <= label.winfo_width() + 2
    assert _clipping_problems(app) == []
    assert not _off_window_problems(app)
    assert wiz.selected.path == "/dev/sde" and not wiz.runner.started
