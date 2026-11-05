# SPDX-License-Identifier: GPL-3.0-or-later
"""#168: the screen stays lit while an erase runs, then blanking is restored.

SleepInhibit (the existing power-management helper, Ref #39) now also runs
`xset s off` when the erase starts and restores the kiosk policy the
launcher sets (`xset s 600 s blank s on`) when it stops. Only on the live
USB, never in a dry run or preview, never without an X display. DPMS, lid,
suspend and power handling are untouched; a failed xset never blocks the
erase. The "screen may go dark" note leaves Tk, GTK and the web preview and
stays in the console fallbacks. All subprocesses here are fakes.
"""

from __future__ import annotations

import pathlib
import subprocess

import pytest

from beamo_wipe import copy as C
from beamo_wipe import sleep_inhibit as S

ROOT = pathlib.Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "packaging/live/config/includes.chroot/usr/local/bin/beamo-wipe"


class FakeInhibitor:
    def poll(self):
        return None

    def terminate(self):
        pass

    def kill(self):
        pass

    def wait(self, timeout=None):
        return 0


@pytest.fixture
def live(monkeypatch):
    calls = []

    def run(argv, **kwargs):
        calls.append((list(argv), kwargs.get("env", {}).get("DISPLAY")))
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setenv("BEAMO_WIPE_LIVE", "1")
    monkeypatch.delenv("BEAMO_WIPE_DRY_RUN", raising=False)
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setattr(S.os.path, "isfile", lambda p: p == S.XSET_BIN)
    monkeypatch.setattr(S.subprocess, "run", run)
    monkeypatch.setattr(S.subprocess, "Popen", lambda *a, **k: FakeInhibitor())
    return calls


def test_erase_keeps_the_screen_on_and_restores_the_kiosk_policy(live):
    inhibit = S.SleepInhibit()
    inhibit.start()
    assert live == [([S.XSET_BIN, "s", "off"], ":0")]
    inhibit.stop()
    assert live[-1] == ([S.XSET_BIN, "s", "600", "s", "blank", "s", "on"], ":0")
    inhibit.stop()  # a second stop does not restore twice
    assert len(live) == 2


def test_restore_matches_the_launcher_and_touches_only_the_screensaver():
    text = LAUNCHER.read_text(encoding="utf-8")
    assert "xset s 600 s blank s on" in text
    assert " ".join(S.display_restore_argv()[1:]) == "s 600 s blank s on"
    for argv in (S.display_awake_argv(), S.display_restore_argv()):
        assert argv[0] == S.XSET_BIN and argv[1] == "s"
        assert not {"dpms", "-dpms", "+dpms", "suspend", "standby"} & set(argv)


@pytest.mark.parametrize("setting", ["not-live", "dry-run", "no-display", "no-xset"])
def test_never_runs_outside_a_live_x_session(live, monkeypatch, setting):
    if setting == "not-live":
        monkeypatch.delenv("BEAMO_WIPE_LIVE")
    elif setting == "dry-run":
        monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    elif setting == "no-display":
        monkeypatch.delenv("DISPLAY")
    else:
        monkeypatch.setattr(S.os.path, "isfile", lambda p: False)
    inhibit = S.SleepInhibit()
    inhibit.start()
    inhibit.stop()
    assert live == []


@pytest.mark.parametrize("failure", ["oserror", "timeout", "nonzero"])
def test_xset_failure_never_blocks_the_erase(live, monkeypatch, failure):
    def run(argv, **kwargs):
        live.append((list(argv), None))
        if failure == "oserror":
            raise OSError("no xset")
        if failure == "timeout":
            raise subprocess.TimeoutExpired(argv, 5)
        return subprocess.CompletedProcess(argv, 1)

    monkeypatch.setattr(S.subprocess, "run", run)
    inhibit = S.SleepInhibit()
    inhibit.start()  # no exception: the erase goes ahead
    assert inhibit.active  # the sleep inhibitor still holds
    inhibit.stop()
    # Nothing was changed, so nothing is restored.
    assert [argv for argv, _ in live] == [[S.XSET_BIN, "s", "off"]]


def test_note_only_in_the_console_fallbacks():
    tk = (ROOT / "src/beamo_wipe/ui/tk_wizard.py").read_text(encoding="utf-8")
    gtk = (ROOT / "src/beamo_wipe/ui/accessible_wizard.py").read_text(encoding="utf-8")
    console = (ROOT / "src/beamo_wipe/ui/console_wizard.py").read_text(encoding="utf-8")
    assert "POWER_BLANKING" not in tk and "POWER_BLANKING" not in gtk
    assert console.count("C.POWER_BLANKING") == 2  # curses and plain console
    from beamo_wipe.gallery import gallery_html

    assert C.POWER_BLANKING not in gallery_html()


def test_tk_owner_screen_has_no_dark_screen_note():
    from test_tk_runtime import _needs_display
    from beamo_wipe.demo import make_demo_wizard
    from beamo_wipe.ui.tk_wizard import TkWizard

    _needs_display()
    wiz = make_demo_wizard()
    wiz.skip_intro()
    app = TkWizard(wiz)
    try:
        app.root.geometry("800x600+20+20")
        app._draw()
        for _ in range(6):
            app.root.update()
        texts = []

        def visit(w):
            if w.winfo_class() == "Label" and w.winfo_ismapped():
                texts.append(str(w.cget("text")))
            for child in w.winfo_children():
                visit(child)

        visit(app._body)
        joined = " ".join(texts)
        assert C.POWER_REMINDER in joined and C.POWER_BLANKING not in joined
    finally:
        app._teardown()
