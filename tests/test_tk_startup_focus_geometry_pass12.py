"""Bare X11 startup must fit its screen and accept the first real Escape."""

import os
import threading

import pytest

pytest.importorskip("gi")
from beamo_wipe import lang  # noqa: E402
from beamo_wipe.ui import tk_wizard  # noqa: E402
from beamo_wipe.ui.accessible_wizard import Gdk  # noqa: E402
from test_accessible_focus_input_pass11 import native  # noqa: E402, F401


@pytest.fixture(autouse=True)
def isolated_startup(monkeypatch):
    if os.environ.get("BEAMO_ISOLATED_X11_TEST") != "1":
        pytest.skip("Native startup input requires an explicitly isolated display")

    def forbidden(*_args, **_kwargs):
        raise AssertionError("Native application operation reached")

    monkeypatch.setattr(tk_wizard, "_ensure_tk_display", lambda: None)
    for target in ("subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk", "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources", "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start", "beamo_wipe.app._shutdown", "beamo_wipe.sound._run", "beamo_wipe.sound._popen"):
        monkeypatch.setattr(target, forbidden)


@pytest.mark.parametrize("pointer", ["corner", "inside"])
@pytest.mark.parametrize("fullscreen", [False, True])
def test_first_tk_startup_accepts_native_escape(native, monkeypatch, pointer, fullscreen):  # noqa: F811
    native.root_focus()
    native.pointer(0, 0)
    release, finished = threading.Event(), threading.Event()
    real_tk = tk_wizard.tk.Tk
    rescued, seen, errors = [], [], []

    def factory():
        root = real_tk()

        def position():
            x, y = root.winfo_rootx(), root.winfo_rooty()
            width, height = root.winfo_width(), root.winfo_height()
            point = (x + width // 2, y + height // 2) if pointer == "inside" else (0, 0)
            native.pointer(*point)
            seen.append((x, y, width, height, point))

        def escape():
            try:
                native.key(Gdk.KEY_Escape, True)
                native.key(Gdk.KEY_Escape, False)
            except BaseException as error:
                errors.append(error)
                root.destroy()

        def rescue():
            rescued.append(True)
            root.destroy()

        root.after(100, position)
        root.after(180, escape)
        root.after(450, rescue)
        return root

    def build(_report):
        try:
            assert release.wait(timeout=2)
            return object()
        finally:
            finished.set()

    monkeypatch.setattr(tk_wizard.tk, "Tk", factory)
    try:
        assert tk_wizard.run_tk_startup(build, fullscreen=fullscreen) == ("abandoned", None)
        assert not errors
        assert seen
        assert not rescued, seen
    finally:
        release.set()
        assert finished.wait(timeout=1)


@pytest.mark.parametrize("language", ["en", "fr", "de", "es", "it"])
@pytest.mark.parametrize("fullscreen", [False, True])
def test_mapped_tk_startup_uses_its_configured_screen_bounds(monkeypatch, language, fullscreen):
    lang.set_language(language)
    release, finished = threading.Event(), threading.Event()
    real_tk = tk_wizard.tk.Tk
    seen = []

    def factory():
        root = real_tk()

        def inspect():
            seen.append((root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height(), root.winfo_screenwidth(), root.winfo_screenheight()))
            root.destroy()

        root.after(100, inspect)
        return root

    def build(_report):
        try:
            assert release.wait(timeout=2)
            return object()
        finally:
            finished.set()

    monkeypatch.setattr(tk_wizard.tk, "Tk", factory)
    try:
        assert tk_wizard.run_tk_startup(build, fullscreen=fullscreen) == ("abandoned", None)
        assert len(seen) == 1
        x, y, width, height, screen_width, screen_height = seen[0]
        expected = ((0, 0, screen_width, screen_height) if fullscreen else
                    ((screen_width - min(640, screen_width)) // 2,
                     (screen_height - min(440, screen_height)) // 2,
                     min(640, screen_width), min(440, screen_height)))
        assert (x, y, width, height) == expected
    finally:
        release.set()
        assert finished.wait(timeout=1)
