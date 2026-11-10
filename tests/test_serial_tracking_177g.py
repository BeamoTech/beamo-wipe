# SPDX-License-Identifier: GPL-3.0-or-later
"""#177g: slight letter spacing for serial numbers in the Tk wizard.

Tk fonts have no tracking, and inserting (thin) spaces would change the
serial. The Tk wizard draws each character of a serial or hardware ID as its
own canvas text item, one cell apart plus a small gap (1 px at standard
text, 2 px at large and extra large). The #129 confirmation characters and
the #152 differing characters are bold on those same items, so a mark can
only ever sit on its own character.

Safety-adjacent (Confirm tells the owner which disk is erased): these tests
read the drawn characters back in order and require exactly the serial, no
character changed, added, dropped or reordered; the highlighted indices are
exactly the ones the identity view reports; the plain Label under the
canvas (layout checks, tests, readers) keeps the exact text; and any
mismatch falls back to the plain serial with no marks. Fake disks only.
"""

from __future__ import annotations

import itertools
import random

import pytest

from beamo_wipe import lang
from beamo_wipe.discover import discover
from beamo_wipe.models import Screen
from beamo_wipe.nwipe_runner import DryRunRunner
from beamo_wipe.wizard import Wizard

GB = 1_000_000_000
ENV = {"BEAMO_WIPE_DRY_RUN": "1", "BEAMO_WIPE_BOOT_DEVICE": "/dev/sdz"}
LONG_A = "ZX9000LONGSERIALNUMBERTHATNEEDSWRAPPING0123456789ABC1EF"
LONG_B = "ZX9000LONGSERIALNUMBERTHATNEEDSWRAPPINX0123456789ABC2EF"
# Look-alike characters next to each other: 0/O, 1/l/I, 5/S, 8/B.
TRICKY_A = "O0O0l1I1S5B8"
TRICKY_B = "O0O0l1I1S5B9"

SIZES = [((800, 600), "standard"), ((800, 600), "large"), ((800, 600), "extra"),
         ((1280, 820), "standard"), ((1280, 820), "large"), ((1280, 820), "extra")]


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _nodes():
    def d(name, size, model, serial):
        return {"name": name, "path": f"/dev/{name}", "size": size, "type": "disk", "tran": "sata",
                "rota": False, "rm": False, "hotplug": False, "model": model, "serial": serial}

    return [
        {"name": "sdz", "path": "/dev/sdz", "size": 16 * GB, "type": "disk", "tran": "usb",
         "rota": False, "rm": True, "hotplug": True, "model": "Beamo Wipe", "serial": "BEAMOUSB001",
         "children": [{"name": "sdz1", "path": "/dev/sdz1", "type": "part", "size": 15_500_000_000,
                       "fstype": "vfat", "label": "BEAMO_WIPE"}]},
        d("sda", 512_110_190_592, "Crucial MX500", "MX500A1B2C3"),
        d("sdb", 512_110_190_592, "Crucial MX500", "MX500A7B2C9"),
        d("sdc", 1_000_204_886_016, "Generic Long Serial", LONG_A),
        d("sdd", 1_000_204_886_016, "Generic Long Serial", LONG_B),
        d("sde", 2_000_398_934_016, "Seagate ST2000DM008", "ZFL0ABCD"),
        d("sdf", 2_000_398_934_016, "Seagate ST2000DM008", "ZFL0ABXD"),
        d("sdg", 2_000_398_934_016, "Toshiba DT01ACA200", "Y7Q9KLMN"),
        d("sdh", 256_060_514_304, "Tricky", TRICKY_A),
        d("sdi", 256_060_514_304, "Tricky", TRICKY_B),
    ]


def _wizard(text_size="standard"):
    res = discover(lsblk_payload={"blockdevices": _nodes()}, boot_path="/dev/sdz",
                   mount_sources=[], cmdline="", env=ENV)
    wiz = Wizard(res, DryRunRunner(), dry_run=True)
    wiz.preview = False
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    assert wiz.set_text_size(text_size) or wiz.text_size == text_size
    assert wiz.screen == Screen.PICK
    return wiz


# -- pure helpers ----------------------------------------------------------------


def test_rows_cover_every_character_once_in_order():
    from beamo_wipe.ui.tk_wizard import _serial_rows

    rng = random.Random(177)
    for _ in range(3000):
        count = rng.randint(0, 70)
        cols = rng.randint(1, 30)
        # Disjoint, ordered runs, like #152 marks (the token is never combined).
        cuts = sorted(rng.sample(range(count + 1), min(count + 1, 2 * rng.randint(0, 3))))
        keep = list(zip(cuts[::2], cuts[1::2]))
        keep = [(a, b) for a, b in keep if a < b]
        if rng.random() < 0.1:
            keep.append((count, count + 3))  # out of range: ignored, still covers all
        rows = _serial_rows(count, cols, keep)
        flat = list(itertools.chain.from_iterable(range(a, b) for a, b in rows))
        assert flat == list(range(count)), (count, cols, keep, rows)
        assert all(0 < b - a <= cols for a, b in rows) or count == 0
        # A run that fits on a row is never split by a row end.
        for a, b in keep:
            if b <= count and b - a <= cols:
                assert any(s <= a and b <= e for s, e in rows), (count, cols, keep, rows)


def test_tracking_scales_with_text_size():
    from beamo_wipe.ui.tk_wizard import _serial_tracking

    assert _serial_tracking(-12) == _serial_tracking(14) == 1
    assert _serial_tracking(15) == _serial_tracking(-20) == 2
    assert _serial_tracking(25) == 3
    assert all(_serial_tracking(px) >= 1 for px in range(1, 60))


# -- Tk ----------------------------------------------------------------------------


def _faces(app):
    out = []

    def walk(widget):
        face = getattr(widget, "_beamo_serial_face", None)
        if face is not None and widget.winfo_ismapped():
            out.append((widget, face))
        for child in widget.winfo_children():
            walk(child)

    walk(app.root)
    return out


def _face_for(app, serial):
    found = [(label, face) for label, face in _faces(app) if face.text == serial]
    assert len(found) == 1, [face.text for _l, face in _faces(app)]
    return found[0]


def _bold_indices(face):
    bold = str(face.bold)
    return [i for i in range(len(face.text))
            if str(face.itemcget(face.find_withtag(f"ch{i}")[0], "font")) == bold]


def _check_geometry(app, face, label):
    """Every character in its own cell, in reading order, inside the canvas."""
    items = face.find_withtag("ch")
    assert len(items) == len(face.text)
    pitch = None
    previous = None
    width, height = face.winfo_width(), face.winfo_height()
    for index, item in enumerate(items):
        x0, y0, x1, y1 = face.bbox(item)
        assert x0 >= 0 and y0 >= 0 and x1 <= width + 1 and y1 <= height + 1, (index, face.bbox(item))
        cx, cy = face.coords(item)
        if previous is not None:
            pcx, pcy = previous
            if cy == pcy:
                step = cx - pcx
                pitch = step if pitch is None else pitch
                assert step == pitch  # one consistent cell per character
            else:
                assert cy > pcy  # the next row, below
        previous = (cx, cy)
    if pitch is not None:
        assert pitch >= max(face.font.measure(ch) for ch in face.text) + 1  # visible gap
    # Nothing past the allocated width: the face never asks for more than it has.
    assert face.winfo_reqwidth() <= face.master.winfo_width() + 2
    # The plain label underneath carries the exact text (row breaks only).
    assert str(label.cget("text")).replace("\n", "") == face.text
    assert [str(label.cget("text")).split("\n")] == [[face.text[a:b] for a, b in face.rows]]


@pytest.mark.parametrize("size,text_size", SIZES, ids=lambda v: v if isinstance(v, str) else f"{v[0]}x{v[1]}")
@pytest.mark.parametrize("path,serial,expected", [
    ("/dev/sda", "MX500A1B2C3", [6, 10]),
    ("/dev/sde", "ZFL0ABCD", [6]),
    ("/dev/sdd", LONG_B, [38, 52]),
    ("/dev/sdh", TRICKY_A, [11]),
])
def test_pick_draws_the_exact_serial_with_marks_on_the_differing_characters(
        size, text_size, path, serial, expected):
    from test_tk_runtime import _clipping_problems, _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    wiz = _wizard(text_size)
    wiz.select_disk(path)
    view = wiz.disk_view(wiz.selected)
    marked = [i for a, b in view.comparison_marks for i in range(a, b)]
    assert marked == expected  # #152 offsets unchanged by #177g
    app = TkWizard(wiz)
    try:
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app._draw()
        app._pick_ensure_visible = True
        app._draw()
        for _ in range(8):
            app.root.update()
        label, face = _face_for(app, serial)
        assert getattr(label, "_beamo_serial_marked", False)
        assert not face.plain
        assert face.drawn_text() == serial
        assert _bold_indices(face) == expected
        assert face.tracking == (1 if text_size == "standard" else 2)
        _check_geometry(app, face, label)
        # Each underline spans exactly its run's cells, on the run's row.
        for a, b in view.comparison_marks:
            bars = face.find_withtag(f"diff{a}")
            assert bars
            cell = face._metrics()[2]
            # One bar per row the run is on; together exactly the run's cells.
            covered = []
            for bar in bars:
                x0, _y0, x1, _y1 = face.coords(bar)
                on = [i for i in range(a, b)
                      if x0 <= face.coords(face.find_withtag(f"ch{i}")[0])[0] <= x1
                      and face.coords(face.find_withtag(f"ch{i}")[0])[1] == _y1 - face._metrics()[3]]
                assert on, (a, b)
                assert x0 == face.coords(face.find_withtag(f"ch{on[0]}")[0])[0] - cell / 2
                assert x1 == face.coords(face.find_withtag(f"ch{on[-1]}")[0])[0] + cell / 2
                covered.extend(on)
            assert covered == list(range(a, b))
        # Every other serial on Pick is drawn exactly too.
        for other_label, other in _faces(app):
            assert other.drawn_text() == other.text
            assert str(other_label.cget("text")).replace("\n", "") == other.text
        assert not [p for p in _clipping_problems(app) if serial[:12] in p]
    finally:
        app._teardown()


@pytest.mark.parametrize("size,text_size", SIZES, ids=lambda v: v if isinstance(v, str) else f"{v[0]}x{v[1]}")
@pytest.mark.parametrize("path,serial", [("/dev/sda", "MX500A1B2C3"), ("/dev/sdd", LONG_B),
                                         ("/dev/sdh", TRICKY_A)])
def test_confirm_draws_the_exact_serial_with_the_token_boxed_in_place(size, text_size, path, serial):
    from test_tk_runtime import _clipping_problems, _needs_display
    from beamo_wipe.ui import tk_wizard as tkui

    _needs_display()
    wiz = _wizard(text_size)
    wiz.select_disk(path)
    wiz.continue_pick()
    assert wiz.screen == Screen.CONFIRM
    view = wiz.disk_view(wiz.selected)
    spec = wiz.confirm
    assert view.token_end == len(serial) and view.token_end > view.token_start
    assert serial[view.token_start:].casefold() == spec.token.casefold()
    app = tkui.TkWizard(wiz)
    try:
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app._draw()
        for _ in range(8):
            app.root.update()
        label, face = _face_for(app, serial)
        assert getattr(label, "_beamo_serial", False)
        assert not face.plain
        assert face.drawn_text() == serial
        token = list(range(view.token_start, view.token_end))
        assert _bold_indices(face) == token  # no #152 marks on Confirm
        assert not face.find_withtag("diff")
        _check_geometry(app, face, label)
        # The box: a 1 px INK outline on the mark tint around exactly the
        # token's cells, with a 2 px underline (a shape, not only colour).
        boxes = face.find_withtag("token_box")
        bars = face.find_withtag("token_bar")
        assert boxes and len(boxes) == len(bars)
        for box in boxes:
            assert face.itemcget(box, "outline") == tkui.INK
            assert face.itemcget(box, "fill") == tkui.CONFIRM_MARK_BG
            x0, y0, x1, y1 = face.coords(box)
            assert x0 >= 0 and y0 >= 0 and x1 <= face.winfo_width() and y1 <= face.winfo_height()
        for bar in bars:
            x0, y0, x1, y1 = face.coords(bar)
            assert y1 - y0 == 2 and face.itemcget(bar, "fill") == tkui.INK
        inside = set()
        for box in boxes:
            x0, y0, x1, y1 = face.coords(box)
            for i, item in enumerate(face.find_withtag("ch")):
                bx0, by0, bx1, by1 = face.bbox(item)
                cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
                if x0 <= cx <= x1 and y0 <= cy <= y1:
                    inside.add(i)
        assert sorted(inside) == token
        # The prompt names the characters; the plain identifier label is one string.
        assert not wiz.runner.started
        assert not [p for p in _clipping_problems(app) if serial[:12] in p]
    finally:
        app._teardown()


def _bare_face(**kw):
    import tkinter as tk
    import tkinter.font as tkfont

    from test_tk_runtime import _needs_display
    from beamo_wipe.ui import tk_wizard as tkui

    _needs_display()
    root = tk.Tk()
    font = tkfont.Font(root=root, family="Courier", size=-14)
    bold = tkfont.Font(root=root, family="Courier", size=-14, weight="bold")
    frame = tk.Frame(root, width=400)
    frame.pack(fill=tk.X)
    face = tkui._SerialFace(frame, kw.pop("text"), font=font, bold=bold, fg="#000000",
                            bg="#FFFFFF", width=400, **kw)
    face.pack(fill=tk.X)
    face.layout(400)
    root.update()
    return root, face


def test_offsets_outside_the_serial_show_it_plain_with_no_marks():
    root, face = _bare_face(text="ABC123", token=(3, 9))
    try:
        assert face.plain
        assert face.find_all() == ()
        assert str(face.label.cget("text")) == "ABC123"
        assert face.label.winfo_ismapped()
    finally:
        root.destroy()


def test_a_drawing_that_does_not_read_back_falls_back_to_the_plain_serial(monkeypatch):
    import tkinter as tk

    real = tk.Canvas.create_text

    def drop_one(self, *args, **kw):
        if kw.get("text") == "3":
            kw["text"] = "8"  # a wrong character must never be shown
        return real(self, *args, **kw)

    monkeypatch.setattr(tk.Canvas, "create_text", drop_one)
    root, face = _bare_face(text="ABC123", token=(4, 6))
    try:
        assert face.plain
        assert face.find_all() == ()  # no marks, no partial drawing
        assert str(face.label.cget("text")).replace("\n", "") == "ABC123"
    finally:
        root.destroy()


@pytest.mark.parametrize("text", ["O0Il1|", "A B-C_D.E/F", "ÄÖÜ-1234-éè", "W" * 80])
def test_any_identifier_is_drawn_exactly(text):
    root, face = _bare_face(text=text, token=(len(text) - 3, len(text)))
    try:
        assert not face.plain
        assert face.drawn_text() == text
        assert str(face.label.cget("text")).replace("\n", "") == text
        assert _bold_indices(face) == list(range(len(text) - 3, len(text)))
        # The token fits on one row, so it is never split.
        rows = [r for r in face.rows if r[0] < len(text) and r[1] > len(text) - 3]
        assert len(rows) == 1
    finally:
        root.destroy()


def test_spoken_and_copied_identity_text_is_unchanged():
    """The identity view's text (Orca, consoles, evidence) has no spacing characters."""
    wiz = _wizard()
    for disk in wiz.selectable:
        view = wiz.disk_view(disk)
        assert view.id_value == (disk.serial or view.id_value)
        assert f"{view.id_label}: {view.id_value}" in view.announcement
        for ch in (" ", " ", " ", " "):
            assert ch not in view.announcement and ch not in view.marked_id
