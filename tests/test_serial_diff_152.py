# SPDX-License-Identifier: GPL-3.0-or-later
"""#152: the characters that tell look-alike serials apart are bold and underlined.

Each disk is compared with every other disk of the same displayed capacity,
one pair at a time: the shared beginning and ending are stripped; the rest is
marked character by character when both remaining parts have the same length,
and wholly when they do not. A same-size serial that shares nothing adds no
mark. Works for 2, 3 or more similar disks and serials of different lengths.
Tk and the web preview draw the marks bold and underlined, GTK uses Pango
<b><u> on the disk button, curses and the plain console keep [brackets] (a
shape on any terminal). Orca hears where it differs, e.g. "Differs from the
other 256 GB disk at characters 11 to 14". Display only. Fake disks only.
"""

from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import string
import subprocess
import sys

import pytest

from beamo_wipe import inventory, lang
from beamo_wipe.discover import discover
from beamo_wipe.identity import present_disk
from beamo_wipe.models import Disk, DiskKind, Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.safety import confirm_spec
from beamo_wipe.wizard import Wizard

ROOT = Path(__file__).resolve().parents[1]
GB = 1_000_000_000
ENV = {"BEAMO_WIPE_DRY_RUN": "1", "BEAMO_WIPE_BOOT_DEVICE": "/dev/sdz"}
LONG_A = "ZX9000LONGSERIALNUMBERTHATNEEDSWRAPPING0123456789ABC1EF"
LONG_B = "ZX9000LONGSERIALNUMBERTHATNEEDSWRAPPINX0123456789ABC2EF"


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def disks(*serials, size="500"):
    return tuple(Disk(path=f"/dev/sd{chr(97 + i)}", name=f"sd{chr(97 + i)}", model="Same model",
                      serial=serial, size_bytes=int(size) * GB, size_gb_label=size,
                      kind=DiskKind.HDD, bus="SATA", label="")
                 for i, serial in enumerate(serials))


def view(disk, peers):
    return present_disk(disk, peers, compare_serials=True)


# -- what is marked ----------------------------------------------------------


@pytest.mark.parametrize(
    "serials,expected",
    [
        # Two similar disks.
        (("ABC123XYZ", "ABC124XYZ"), [((5, 6),), ((5, 6),)]),
        # Two separate differing characters: only those, not the span.
        (("MX500A1B2C3", "MX500A7B2C9"), [((6, 7), (10, 11)), ((6, 7), (10, 11))]),
        # Three similar disks: what tells each apart from both others.
        (("S4EVNX0N123456", "S4EVNX0N123999", "S4EVNX0N129456"),
         [((10, 14),), ((10, 14),), ((10, 14),)]),
        (("ABC123XYZ", "ABC124XYZ", "ABC923XYZ"),
         [((3, 4), (5, 6)), ((3, 4), (5, 6)), ((3, 4), (5, 6))]),
        # Four similar disks.
        # (each differs from some other at characters 4 to 6)
        (("SN0001", "SN0002", "SN0010", "SN0100"),
         [((3, 6),), ((3, 6),), ((3, 6),), ((3, 6),)]),
        # Different lengths: the longer one marks what the shorter lacks.
        (("WD-WCC6Y1234567", "WD-WCC6Y123456"), [((14, 15),), ()]),
        (("ABC", "ABXC"), [(), ((2, 3),)]),
        (("AB12CD", "AB345CD"), [((2, 4),), ((2, 5),)]),
        # Case-only differences never establish identity.
        (("aBC1", "AbC2"), [((3, 4),), ((3, 4),)]),
        # Nothing shared: not look-alikes, nothing to mark.
        (("ABCD", "WXYZ"), [(), ()]),
    ],
)
def test_marks(serials, expected):
    peers = disks(*serials)
    for disk, want in zip(peers, expected):
        got = view(disk, peers)
        # Runs merge adjacent offsets.
        flat = sorted(i for a, b in got.comparison_marks for i in range(a, b))
        assert flat == sorted(i for a, b in want for i in range(a, b)), disk.serial
        assert all(b > a for a, b in got.comparison_marks)
        assert "".join(text for text, _ in got.comparison_segments) == disk.serial
        assert got.marked_id.replace("[", "").replace("]", "") == disk.serial


def test_an_unrelated_same_size_serial_no_longer_hides_the_look_alikes():
    # The #148 follow-up: a third serial sharing nothing removed every mark.
    peers = disks("ZFL0ABCD", "ZFL0ABXD", "Y7Q9KLMN", size="2000")
    a, b, c = (view(d, peers) for d in peers)
    assert a.comparison_marks == ((6, 7),) and b.comparison_marks == ((6, 7),)
    assert c.comparison_marks == () and c.comparison_note == ""
    assert a.comparison_note == (
        "Differs from the similar 2 TB (2000 GB) disk at character 7. Check the full ID before choosing."
    )


@pytest.mark.parametrize(
    "serials,index,note",
    [
        (("ABC123XYZ", "ABC124XYZ"), 0,
         "Differs from the other 500 GB disk at character 6. Check the full ID before choosing."),
        (("MX500A1B2C3", "MX500A7B2C9"), 0,
         "Differs from the other 500 GB disk at characters 7 and 11. Check the full ID before choosing."),
        (("S4EVNX0N123456", "S4EVNX0N123999", "S4EVNX0N129456"), 0,
         "Differs from the similar 500 GB disks at characters 11 to 14. Check the full ID before choosing."),
        (("A1B2C3D4", "A9B2C3D8", "A1B2C3D4X"), 0,
         "Differs from the similar 500 GB disks at characters 2 and 8. Check the full ID before choosing."),
        # Against a serial of another length the whole remaining part counts.
        (("A1B2C3D4", "A9B2C3D8", "A1B2C3D4X"), 1,
         "Differs from the similar 500 GB disks at characters 2 to 8. Check the full ID before choosing."),
        (("SN0001", "SN0002", "SN0010", "SN0100"), 3,
         "Differs from the similar 500 GB disks at characters 4 to 6. Check the full ID before choosing."),
        (("WD-WCC6Y1234567", "WD-WCC6Y123456"), 1,
         "Serial number has 14 characters; other serials are longer. Check the full ID before choosing."),
    ],
)
def test_note_says_where_it_differs_never_the_characters(serials, index, note):
    peers = disks(*serials)
    got = view(peers[index], peers)
    assert got.comparison_note == note
    assert peers[index].serial not in got.comparison_note
    # Orca: the disk's spoken name carries the note, once.
    assert got.announcement.count(note) == 1


def test_positions_with_runs_and_single_characters():
    peers = disks("A1BCDEF2G", "A9BCDXY8G")
    got = view(peers[0], peers)
    assert got.comparison_marks == ((1, 2), (5, 8))
    assert "at characters 2 and 6 to 8." in got.comparison_note
    assert got.marked_id == "A[1]BCD[EF2]G"


@pytest.mark.parametrize("serials", [("ABC", "ABC"), ("ABC", "abc"), ("ABC", ""), ("", "")])
def test_duplicates_and_missing_serials_get_no_marks(serials):
    peers = disks(*serials)
    for disk in peers:
        got = view(disk, peers)
        assert got.comparison_marks == () and got.comparison_note == ""
        assert got.marked_id == got.id_value


def test_boot_and_different_sizes_are_not_compared():
    a, b = disks("ABC1", "ABC2")
    assert view(a, (a, replace(b, size_gb_label="501"))).comparison_marks == ()
    assert view(replace(a, is_boot=True), (a, b)).comparison_marks == ()


# -- display only ------------------------------------------------------------


def test_marks_never_change_tokens_identity_or_eligibility():
    peers = disks("S4EVNX0N123456", "S4EVNX0N123999", "S4EVNX0N129456")
    for disk in peers:
        plain = present_disk(disk, peers)
        compared = view(disk, peers)
        assert plain.comparison_marks == () and plain.comparison_note == ""
        assert compared.id_value == plain.id_value == disk.serial
        assert (compared.token_start, compared.token_end) == (plain.token_start, plain.token_end)
        assert compared.confirmable == plain.confirmable
    assert [confirm_spec(d, peers) for d in peers] == [confirm_spec(d, peers) for d in peers]


def test_only_pick_compares_and_confirm_keeps_its_token_marks():
    wiz = _wizard()
    disk = next(d for d in wiz.selectable if d.path == "/dev/sda")
    assert wiz.disk_view(disk).comparison_marks
    wiz.select_disk(disk.path)
    wiz.continue_pick()
    assert wiz.screen == Screen.CONFIRM
    shown = wiz.disk_view(disk)
    assert shown.comparison_marks == () and shown.token_end > shown.token_start
    assert wiz.confirm_input == "" and not wiz.runner.started


# -- translations --------------------------------------------------------------


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_every_language_has_the_new_templates(code):
    def get(key):
        return getattr(inventory, key) if code == "en" else lang.translated(code, "inventory", key)

    for key in ("COMPARE_SERIAL_OTHER", "COMPARE_SERIAL_SIMILAR_ONE", "COMPARE_SERIAL_SIMILAR_MANY"):
        fields = {n for _, n, _, _ in string.Formatter().parse(get(key)) if n}
        assert fields == {"size", "position", "reminder"}, (code, key)
    assert {n for _, n, _, _ in string.Formatter().parse(get("POSITION_MANY")) if n} == {"items"}
    assert {n for _, n, _, _ in string.Formatter().parse(get("POSITION_ITEM_RANGE")) if n} == {"a", "b"}
    assert get("POSITION_AND").strip()
    lang.set_language(code)
    peers = disks("MX500A1B2C3", "MX500A7B2C9")
    note = view(peers[0], peers).comparison_note
    assert "7" in note and "11" in note and get("POSITION_AND") in note
    assert "MX500A1B2C3" not in note


# -- views ---------------------------------------------------------------------


def _nodes():
    def d(name, size, tran, model, serial):
        return {"name": name, "path": f"/dev/{name}", "size": size, "type": "disk", "tran": tran,
                "rota": False, "rm": False, "hotplug": tran == "usb", "model": model, "serial": serial}

    return [
        {**d("sdz", 16 * GB, "usb", "Beamo Wipe", "BEAMOUSB001"), "rm": True,
         "children": [{"name": "sdz1", "path": "/dev/sdz1", "type": "part", "size": 15_500_000_000,
                       "fstype": "vfat", "label": "BEAMO_WIPE"}]},
        d("sda", 512_110_190_592, "sata", "Crucial MX500", "MX500A1B2C3"),
        d("sdb", 512_110_190_592, "sata", "Crucial MX500", "MX500A7B2C9"),
        d("sdc", 1_000_204_886_016, "sata", "Generic Long Serial", LONG_A),
        d("sdd", 1_000_204_886_016, "sata", "Generic Long Serial", LONG_B),
        d("sde", 2_000_398_934_016, "sata", "Seagate ST2000DM008", "ZFL0ABCD"),
        d("sdf", 2_000_398_934_016, "sata", "Seagate ST2000DM008", "ZFL0ABXD"),
        d("sdg", 2_000_398_934_016, "sata", "Toshiba DT01ACA200", "Y7Q9KLMN"),
    ]


def _wizard():
    res = discover(lsblk_payload={"blockdevices": _nodes()}, boot_path="/dev/sdz",
                   mount_sources=[], cmdline="", env=ENV)
    wiz = Wizard(res, DryRunRunner(), dry_run=True)
    wiz.preview = False
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    assert wiz.screen == Screen.PICK
    return wiz


def test_curses_and_plain_console_bracket_each_run(monkeypatch):
    from beamo_wipe.ui import console_wizard as console

    wiz = _wizard()
    text = "\n".join(line for _, block in console._pick_blocks(wiz, 80) for line in block)
    assert "Serial number: MX500A[1]B2C[3]" in text
    assert "Serial number: ZFL0AB[C]D" in text
    assert "Serial number: Y7Q9KLMN" in text
    assert "Differs from the other 512 GB disk at characters 7 and 11." in text
    printed = []
    monkeypatch.setattr("builtins.print", lambda *a, **_k: printed.append(" ".join(map(str, a))))

    def fake_input(_prompt=""):
        wiz.shutdown()
        return ""

    monkeypatch.setattr("builtins.input", fake_input)
    console._plain_loop(wiz)
    assert any("Serial number: MX500A[7]B2C[9]" in line for line in printed)


def test_preview_payload_and_page_mark_bold_and_underlined(monkeypatch):
    from beamo_wipe import gallery

    wiz = _wizard()
    monkeypatch.setattr(gallery, "discovery_for_scenario", lambda _: wiz.discovery)
    payload = {d["path"]: d for d in gallery._disks_payload()}
    assert payload["/dev/sda"]["serialMarks"] == [[6, 7], [10, 11]]
    assert payload["/dev/sdg"]["serialMarks"] == []
    html = gallery.gallery_html()
    assert ".card .meta .mono.ser b.diff { font-weight: 700; text-decoration: underline;" in html
    assert ".card .meta .mono.ser.compared { font-weight: 400; }" in html
    assert '<b class="diff">' in html


_GTK = r'''
import json, sys
from types import ModuleType, SimpleNamespace
repo = ModuleType("gi.repository")
for name in ("Gtk", "Gdk", "GLib", "Pango", "Atk"):
    setattr(repo, name, SimpleNamespace())
gi = ModuleType("gi"); gi.require_version = lambda *_a: None; gi.repository = repo
sys.modules["gi"] = gi; sys.modules["gi.repository"] = repo
from beamo_wipe import copy as C
from beamo_wipe.identity import present_disk
from beamo_wipe.models import Disk, DiskKind
from beamo_wipe.ui import accessible_wizard as accessible

def disk(path, serial):
    return Disk(path=path, name=path[5:], model="M & <Co>", serial=serial, size_bytes=500_000_000_000,
                size_gb_label="500", kind=DiskKind.HDD, bus="SATA", label="")

class Child:
    markup = None
    def set_markup(self, value): self.markup = value
class Button:
    def __init__(self): self.child = Child()
    def get_child(self): return self.child

peers = (disk("/dev/sda", "MX500A1B2C3"), disk("/dev/sdb", "MX500A7B2C9"), disk("/dev/sdc", "WXYZ"))
ui = object.__new__(accessible.AccessibleWizard)
out = {}
for d in peers:
    v = present_disk(d, peers, compare_serials=True)
    text = C.ACCESSIBLE_SELECT_DISK.format(disk=v.announcement)
    b = Button()
    ui._mark_serial(b, text, v)
    out[d.path] = {"markup": b.child.markup, "text": text}
print(json.dumps(out))
'''


def test_gtk_disk_button_marks_bold_underline_and_reads_where_it_differs():
    import html as _html
    import re

    result = subprocess.run(
        [sys.executable, "-c", _GTK], cwd=ROOT,
        env={**os.environ, "PYTHONPATH": os.pathsep.join(filter(None, [str(ROOT / "src"), os.environ.get("PYTHONPATH", "")]))},
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout.strip().splitlines()[-1])
    a = out["/dev/sda"]
    assert "Serial number: MX500A<b><u>1</u></b>B2C<b><u>3</u></b>" in a["markup"]
    assert "M &amp; &lt;Co&gt;" in a["markup"]  # everything else escaped
    assert _html.unescape(re.sub(r"</?[bu]>", "", a["markup"])) == a["text"]
    assert "Differs from the other 500 GB disk at characters 7 and 11." not in a["text"]
    assert "Differs from the similar 500 GB disk at characters 7 and 11." in a["text"]
    assert out["/dev/sdc"]["markup"] is None  # nothing to mark: plain label


# -- Tk ------------------------------------------------------------------------


def _marks(app):
    found = []

    def walk(widget):
        if getattr(widget, "_beamo_serial_mark", False) and widget.winfo_ismapped():
            found.append(widget)
        for child in widget.winfo_children():
            walk(child)

    walk(app.root)
    return sorted(found, key=lambda w: (w.winfo_rooty(), w.winfo_rootx()))


def _serial_label(app):
    found = []

    def walk(widget):
        if getattr(widget, "_beamo_serial_marked", False):
            found.append(widget)
        for child in widget.winfo_children():
            walk(child)

    walk(app.root)
    assert len(found) == 1
    return found[0]


@pytest.mark.parametrize("size,text_size", [((800, 600), "standard"), ((800, 600), "large"),
                                            ((800, 600), "extra"), ((1280, 820), "standard")])
@pytest.mark.parametrize("path,serial,chars",
                         [("/dev/sda", "MX500A1B2C3", ["1", "3"]),
                          ("/dev/sde", "ZFL0ABCD", ["C"]),
                          ("/dev/sdd", LONG_B, ["X", "2"])])
def test_tk_marks_sit_on_the_differing_characters(size, text_size, path, serial, chars):
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    wiz = _wizard()
    wiz.text_size = text_size
    wiz.select_disk(path)
    app = TkWizard(wiz)
    try:
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app._draw()
        app._pick_ensure_visible = True
        app._draw()
        for _ in range(8):
            app.root.update()
        label = _serial_label(app)
        shown = str(label.cget("text"))
        assert shown.replace("\n", "") == serial  # the plain serial, no brackets
        assert str(label.cget("font")) == str(app.font_mono)
        marks = _marks(app)
        assert [str(m._beamo_mark_text) for m in marks] == chars
        # Each mark covers exactly its characters on the shown line.
        lines = shown.split("\n")
        flat = 0
        starts = {}
        for row, line in enumerate(lines):
            for col in range(len(line)):
                starts[flat + col] = (row, col)
            flat += len(line)
        view = wiz.disk_view(wiz.selected)
        offsets = [a for a, b in view.comparison_marks for _ in [0]]
        for mark, offset in zip(marks, offsets):
            row, col = starts[offset]
            dx = mark.winfo_rootx() - label.winfo_rootx()
            expect = app.font_mono.measure(lines[row][:col])
            assert abs(dx - expect) <= 4, (dx, expect)
            assert label.winfo_rootx() <= mark.winfo_rootx()
            assert mark.winfo_rootx() + mark.winfo_width() <= label.winfo_rootx() + label.winfo_width() + 1
        # A changed label text never leaves a mark on other characters.
        label.configure(text="SOMETHING ELSE")
        label.event_generate("<Configure>")
        for _ in range(4):
            app.root.update()
        assert _marks(app) == []
    finally:
        app._teardown()


def test_tk_unmarked_serials_keep_the_bold_label_and_confirm_has_no_compare_marks():
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    wiz = _wizard()
    wiz.select_disk("/dev/sdg")
    app = TkWizard(wiz)
    try:
        app.root.geometry("800x600+40+40")
        app._draw()
        for _ in range(6):
            app.root.update()
        assert _marks(app) == []
        wiz.select_disk("/dev/sda")
        wiz.continue_pick()
        app._draw()
        for _ in range(6):
            app.root.update()
        assert wiz.screen == Screen.CONFIRM
        assert _marks(app) == []
    finally:
        app._teardown()
