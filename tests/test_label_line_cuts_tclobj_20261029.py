# SPDX-License-Identifier: GPL-3.0-or-later
"""Line-cut geometry survives Tk options returned as Tcl objects.

On Debian 12 (Python 3.11, Tk 8.6.13) a Label's ``cget("pady")`` returns a
``_tkinter.Tcl_Obj``; ``float()`` rejects it with TypeError. The focus
reveal on short screens called ``_label_line_cuts`` from an idle callback,
so the TypeError retired the whole wizard (CI run 40814724934: 282 Tk
tests on the keyboard screen and every screen after it). Fake widget only.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from beamo_wipe.ui import tk_wizard as tkui

LINE = 15.0


class TclObjLike:
    """Like _tkinter.Tcl_Obj: str() gives the value, float() refuses it."""

    def __init__(self, text: str) -> None:
        self._text = text

    def __str__(self) -> str:
        return self._text


class FakeLabel:
    def __init__(self, lines: int, *, anchor: str = "w", pady: str = "1") -> None:
        self.options = {
            "text": "a wrapped label",
            "font": "TkDefaultFont",
            "borderwidth": TclObjLike("2"),
            "highlightthickness": TclObjLike("0"),
            "pady": TclObjLike(pady),
            "anchor": anchor,
        }
        self.inset = 2.0 + 0.0 + float(pady.rstrip("p"))
        self.lines = lines
        self.tk = SimpleNamespace(call=lambda *args: int(LINE))

    def winfo_class(self) -> str:
        return "Label"

    def cget(self, option: str):
        return self.options[option]

    def winfo_fpixels(self, value: str) -> float:
        return float(str(value).rstrip("p"))

    def winfo_reqheight(self) -> int:
        return int(2 * self.inset + self.lines * LINE)


def test_tcl_object_options_are_what_broke_the_old_conversion():
    with pytest.raises(TypeError):
        float(TclObjLike("1"))  # type: ignore[arg-type]


@pytest.mark.parametrize("anchor,first", [("w", 100.0 + 3.0), ("nw", 100.0 + 3.0)])
def test_three_line_label_has_two_cuts_with_tcl_object_options(anchor, first):
    label = FakeLabel(3, anchor=anchor)
    height = float(label.winfo_reqheight())
    cuts = tkui._label_line_cuts(label, 100.0, height)
    assert cuts == pytest.approx((first + LINE, first + 2 * LINE))


def test_single_line_label_has_no_cut():
    label = FakeLabel(1)
    assert tkui._label_line_cuts(label, 0.0, float(label.winfo_reqheight())) == ()


def test_unconvertible_distance_means_no_cut_not_a_crash():
    label = FakeLabel(3)
    label.options["pady"] = TclObjLike("bogus")

    def refuse(value):
        raise tkui.tk.TclError(f'bad screen distance "{value}"')

    label.winfo_fpixels = refuse  # type: ignore[method-assign]
    assert tkui._label_line_cuts(label, 0.0, 60.0) == ()
