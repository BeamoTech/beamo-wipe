# SPDX-License-Identifier: GPL-3.0-or-later
"""#159: method cards show a title, one sentence and a time line.

Every card, in every view, carries a time line for this disk: the cautious
range from the existing estimator, or "Time depends on the disk" when no
range can be given. The counts, checks and limits move under each card's
own Show more, which never chooses a method. The method mapping is
unchanged. Fake disks only; nothing starts the engine.
"""

from __future__ import annotations

import json
import re
from dataclasses import replace

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang, progress
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.methods import METHODS
from beamo_wipe.models import Disk, DiskKind, MethodId, Screen
from beamo_wipe.ui import console_wizard

ORDER = (MethodId.EVERYDAY, MethodId.EXTRA, MethodId.QUICK_ZERO)
UNKNOWN_SIZE = [
    {"size_gb_label": ""},
    {"size_gb_label": "unknown"},
    {"size_gb_label": "0"},
    {"size_bytes": 0},
]


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _disk(**changes) -> Disk:
    disk = Disk(
        path="/dev/sdx", name="sdx", model="Fake", serial="FAKE1",
        size_bytes=1_000_000_000_000, size_gb_label="1000", kind=DiskKind.HDD,
        bus="SATA", label="",
    )
    return replace(disk, **changes)


def _method_wizard(path="/dev/sda"):
    wiz = make_demo_wizard()
    wiz.preview = False
    wiz.skip_intro()
    wiz.set_owner(True)
    wiz.continue_owner()
    wiz.select_disk(path)
    wiz.continue_pick()
    wiz.set_confirm_input(wiz.confirm.token)
    wiz.continue_confirm()
    assert wiz.screen == Screen.METHOD
    return wiz


# --- the time line -----------------------------------------------------


def test_time_line_is_the_existing_cautious_guide_when_the_size_is_known():
    disk = _disk()
    for method in METHODS:
        guide = C.method_time_guide(method, disk)
        assert guide and C.method_time_line(method, disk) == guide
        assert "not promised" in guide and ("–" in guide or " to " in guide)


@pytest.mark.parametrize("changes", UNKNOWN_SIZE)
def test_time_line_says_it_depends_when_the_size_is_unknown(changes):
    disk = _disk(**changes)
    for method in METHODS:
        assert C.method_time_guide(method, disk) == ""
        assert C.method_time_line(method, disk) == "Time depends on the disk."


def test_time_line_without_a_disk_or_estimate(monkeypatch):
    assert C.method_time_line(MethodId.EVERYDAY, None) == C.TIME_GUIDE_UNKNOWN
    monkeypatch.setattr(progress, "time_guide", lambda *a: None)
    assert C.method_time_line(MethodId.EXTRA, _disk()) == C.TIME_GUIDE_UNKNOWN


def test_unknown_time_line_is_translated_and_promises_nothing():
    seen = set()
    for code in lang.LANGUAGE_ORDER:
        lang.set_language(code)
        text = C.method_time_line(MethodId.EVERYDAY, _disk(size_bytes=0))
        assert text == C.TIME_GUIDE_UNKNOWN and text.endswith(".")
        assert not re.search(r"\d", text)
        seen.add(text)
    assert len(seen) == len(lang.LANGUAGE_ORDER)


def test_method_mapping_is_unchanged():
    spec = {m: (METHODS[m].nwipe_method, METHODS[m].verify) for m in ORDER}
    assert spec == {
        MethodId.EVERYDAY: ("prng", "last"),
        MethodId.EXTRA: ("dodshort", "last"),
        MethodId.QUICK_ZERO: ("zero", "off"),
    }
    assert METHODS[MethodId.QUICK_ZERO].verification_passes == 0
    assert C.METHOD_CARDS[MethodId.QUICK_ZERO]["mark"] == "No check"


# --- Tk -----------------------------------------------------------------


@pytest.fixture
def method_app(monkeypatch):
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard

    created = []

    def build(size=(800, 600), *, kind="hdd", text_size="standard"):
        _needs_display()
        if kind == "unknown":
            monkeypatch.setattr(progress, "time_guide", lambda *a: None)
        wiz = _method_wizard("/dev/nvme0n1" if kind == "ssd" else "/dev/sda")
        wiz.text_size = text_size
        app = TkWizard(wiz)
        created.append(app)
        app.root.geometry(f"{size[0]}x{size[1]}+20+20")
        app._draw()
        _settle(app)
        return wiz, app

    yield build
    for app in created:
        app._teardown()


def _settle(app, n=8):
    for _ in range(n):
        app.root.update()


def _walk(widget):
    out = [widget]
    for child in widget.winfo_children():
        out.extend(_walk(child))
    return out


def _cards(app):
    """{method: card box} found by each card's time line."""
    out = {}
    for w in _walk(app._body):
        method = getattr(w, "_beamo_method_time", None)
        if method is not None:
            box = w
            while not hasattr(box, "inner"):
                box = box.master
            out[method] = box
    return out


def _texts(widget):
    return [str(w.cget("text")) for w in _walk(widget)
            if w.winfo_class() == "Label" and w.winfo_ismapped() and str(w.cget("text")).strip()]


@pytest.mark.parametrize("kind", ["hdd", "ssd", "unknown"])
def test_tk_every_card_is_title_sentence_and_time(method_app, kind):
    wiz, app = method_app(kind=kind)
    cards = _cards(app)
    assert list(cards) == list(ORDER)
    for method, box in cards.items():
        spec = METHODS[method]
        texts = _texts(box)
        time = C.method_time_line(method, wiz.selected)
        if kind == "unknown":
            assert time == C.TIME_GUIDE_UNKNOWN
        assert spec.title in texts and spec.plain_lead in texts and time in texts
        for hidden in (spec.overwrite_description, spec.verification_description,
                       spec.extra_work, C.EVERYDAY_LIMITS):
            assert not hidden or hidden not in texts, (method, hidden)
        more = app._method_more_buttons[method]
        assert more.winfo_ismapped()


def test_tk_cards_are_shorter(method_app):
    """Before #159 the cards were 140–180 px at 800x600 (five or more lines)."""
    _wiz, app = method_app()
    for method, box in _cards(app).items():
        assert box.winfo_height() <= 120, (method, box.winfo_height())


def test_tk_show_more_opens_only_that_card_and_never_chooses(method_app):
    wiz, app = method_app(size=(1280, 820))
    assert wiz.method == MethodId.EVERYDAY
    app._method_more_buttons[MethodId.QUICK_ZERO]._command()
    _settle(app)
    assert wiz.method == MethodId.EVERYDAY
    cards = _cards(app)
    quick = _texts(cards[MethodId.QUICK_ZERO])
    spec = METHODS[MethodId.QUICK_ZERO]
    assert spec.overwrite_description in quick and spec.verification_description in quick
    toggle = app._method_more_buttons[MethodId.QUICK_ZERO]
    assert toggle.itemcget(toggle._label, "text") == C.BTN_LESS
    for other in (MethodId.EVERYDAY, MethodId.EXTRA):
        assert METHODS[other].overwrite_description not in _texts(cards[other])
    # focus_lastfor: the widget that holds focus once the window has it.
    assert app.root.focus_lastfor() is app._method_more_buttons[MethodId.QUICK_ZERO]
    # Everyday's details include its limits note.
    app._method_more_buttons[MethodId.EVERYDAY]._command()
    _settle(app)
    assert C.EVERYDAY_LIMITS in _texts(_cards(app)[MethodId.EVERYDAY])
    # Show less closes it again.
    app._method_more_buttons[MethodId.QUICK_ZERO]._command()
    _settle(app)
    assert spec.overwrite_description not in _texts(_cards(app)[MethodId.QUICK_ZERO])
    assert wiz.method == MethodId.EVERYDAY


def test_tk_keyboard_tab_and_enter_on_show_more_toggle_without_advancing(method_app):
    wiz, app = method_app(size=(1280, 820))
    app.root.focus_force()
    _settle(app)
    toggle = app._method_more_buttons[MethodId.EXTRA]
    assert int(toggle.cget("takefocus") or 1)  # reachable with Tab
    toggle.focus_set()
    _settle(app)
    (app.root.focus_get() or toggle).event_generate("<Return>", time=70_000)
    _settle(app)
    assert wiz.screen == Screen.METHOD and wiz.method == MethodId.EVERYDAY
    assert MethodId.EXTRA in app._method_more
    assert METHODS[MethodId.EXTRA].extra_work in _texts(_cards(app)[MethodId.EXTRA])
    # Space on the rebuilt toggle closes it again; still no method change.
    again = app._method_more_buttons[MethodId.EXTRA]
    assert app.root.focus_lastfor() is again
    app.root.event_generate("<KeyRelease-Return>", time=70_100)
    _settle(app)
    again.event_generate("<space>", time=71_000)
    _settle(app)
    assert MethodId.EXTRA not in app._method_more
    assert wiz.screen == Screen.METHOD and wiz.method == MethodId.EVERYDAY


@pytest.mark.parametrize("text_size", ["standard", "extra"])
def test_tk_opened_details_scroll_into_view_with_the_card(method_app, text_size):
    _wiz, app = method_app((800, 600), text_size=text_size)
    app.root.focus_force()
    _settle(app)
    app._method_more_buttons[MethodId.QUICK_ZERO]._command()
    _settle(app, 12)
    toggle = app._method_more_buttons[MethodId.QUICK_ZERO]
    top, bottom = app._body.winfo_rooty() - 1, app._footer.winfo_rooty() + 1

    def in_view(w):
        return w.winfo_rooty() >= top and w.winfo_rooty() + w.winfo_height() <= bottom

    assert in_view(toggle) and in_view(toggle._beamo_details)
    assert toggle._beamo_card.winfo_rooty() >= top


def test_tk_card_click_still_chooses_and_gates_are_unchanged(method_app):
    wiz, app = method_app(size=(1280, 820))
    box = _cards(app)[MethodId.EXTRA]
    box.event_generate("<Button-1>", x=10, y=10)
    _settle(app)
    assert wiz.method == MethodId.EXTRA
    app._draw()
    _settle(app)
    wiz.continue_method()
    assert wiz.screen == Screen.LAST_CHANCE
    assert not wiz.erase_enabled and not wiz.runner.started
    assert METHODS[MethodId.EXTRA].operation_summary  # exact counts still on Last chance


@pytest.mark.parametrize("size,text_size", [((800, 600), "standard"), ((800, 600), "extra"),
                                            ((1280, 820), "large")])
def test_tk_cards_do_not_clip(method_app, size, text_size):
    from test_tk_runtime import _clipping_problems, _off_window_problems

    _wiz, app = method_app(size, text_size=text_size)
    assert _clipping_problems(app) == []
    assert not _off_window_problems(app)
    for method in ORDER:
        app._method_more_buttons[method]._command()
        _settle(app)
    assert _clipping_problems(app) == []


# --- consoles -----------------------------------------------------------


def test_plain_console_prints_a_time_line_for_an_unknown_size(monkeypatch, capsys):
    monkeypatch.setattr(progress, "time_guide", lambda *a: None)
    wiz = _method_wizard()

    def stop(_prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", stop)
    console_wizard._plain_loop(wiz)
    lines = capsys.readouterr().out.splitlines()
    for method, spec in METHODS.items():
        (line,) = [ln for ln in lines if ln.startswith(f"{C.METHOD_CARDS[method]['key']} {spec.title}")]
        assert C.TIME_GUIDE_UNKNOWN in line


def test_curses_lists_a_time_line_for_an_unknown_size(monkeypatch):
    from test_time_guide_other_views import _curses_text

    monkeypatch.setattr(console_wizard.curses, "curs_set", lambda *a: None, raising=False)
    monkeypatch.setattr(console_wizard.curses, "use_default_colors", lambda: None, raising=False)
    monkeypatch.setattr(progress, "time_guide", lambda *a: None)
    wiz = _method_wizard()
    text = " ".join(_curses_text(wiz, 60, 120).split())
    for spec in METHODS.values():
        assert f"{spec.title}: {C.TIME_GUIDE_UNKNOWN}" in text


# --- web preview --------------------------------------------------------


def _payload():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    match = re.search(r"const P = (\{.*?\});\n", html, re.S)
    assert match, "payload not found"
    return html, json.loads(match.group(1))


def test_preview_cards_carry_time_lines_and_a_view_only_toggle():
    html, data = _payload()
    assert data["timeUnknown"] == C.TIME_GUIDE_UNKNOWN
    eligible = [d for d in data["disks"] if d["eligible"]]
    assert eligible
    for disk in eligible:
        assert set(disk["methodTimes"]) == {m.value for m in ORDER}
        for value in disk["methodTimes"].values():
            assert value and ("not promised" in value or value == C.TIME_GUIDE_UNKNOWN)
    (script,) = re.findall(r"<script>(.*?)</script>", html, re.S)
    method = script[script.index('} else if (screen === "method")'):]
    method = method[: method.index("renderHint(P.hints.method)")]
    # Title, sentence and time line on the card; details only when opened.
    assert "${m.lead}" in method and "${time}" in method
    assert re.search(r"\$\{open \? `<div class=\"methodblurb\">", method)
    # The toggle is a sibling of the choice (role=button), never inside it,
    # and its handler never touches the chosen method.
    pick = method.index('class="card pickable methodpick')
    assert method.index('class="linkbtn methodmore"') > method.index("</div>\n        </div>", pick)
    handler = method[method.index('querySelectorAll(".methodmore")'):]
    handler = handler[: handler.index("// Clicking elsewhere")]
    assert "method =" not in handler
