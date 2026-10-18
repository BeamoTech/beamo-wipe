"""An Erase line queued before the visible review expires is stale input."""

import json
import os
import sys
import termios
from types import SimpleNamespace

import pytest

from beamo_wipe import copy as C
from beamo_wipe.methods import MethodId
from beamo_wipe.models import Screen
from beamo_wipe.ui import console_wizard as console
from test_plain_review_visible_pass16_ui import _last_chance


@pytest.fixture(autouse=True)
def fake_application_effects(monkeypatch):
    effects = []

    def forbidden(*_args, **_kwargs):
        effects.append("native application effect")
        raise AssertionError("Native application effect reached")

    for target in (
        "subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk",
        "beamo_wipe.discover.read_cmdline", "beamo_wipe.discover.read_mount_sources",
        "beamo_wipe.nwipe_runner.NwipeRunner.start", "beamo_wipe.nwipe_runner.DryRunRunner.start",
        "beamo_wipe.app._shutdown", "beamo_wipe.sound._run", "beamo_wipe.sound._popen",
    ):
        monkeypatch.setattr(target, forbidden)
    yield
    assert not effects


@pytest.mark.parametrize("method", list(MethodId))
@pytest.mark.parametrize("arrival", ["early", "middle", "late", "fresh", "cancel", "eof", "partial"])
def test_plain_erase_requires_new_input_after_countdown(monkeypatch, tmp_path, request, method, arrival):
    if not hasattr(os, "openpty"):
        pytest.skip("Requires an ordinary local pseudoterminal fixture")
    wizard, clock = _last_chance()
    wizard.back()
    wizard.set_method(method)
    wizard.back()
    assert wizard.screen is Screen.CONFIRM
    wizard.set_confirm_input(wizard.confirm.token)
    wizard.continue_confirm()
    wizard.continue_method()
    assert wizard.screen is Screen.LAST_CHANCE
    master, slave = os.openpty()
    terminal = os.fdopen(os.dup(slave), "r", encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", terminal)
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    monkeypatch.setattr(wizard, "_write_evidence", lambda **_kwargs: None)
    inputs, starts, answers = [], [], []
    queued = False
    real_answer = console._answer

    def enqueue(text):
        os.write(master, text)
        inputs.append({"at": clock.value, "bytes": repr(text), "enabled": wizard.erase_enabled})

    def sleep(seconds):
        nonlocal queued
        cutoff = {"early": 0.0, "middle": 2.0, "late": 4.7,
                  "cancel": 0.0, "eof": 0.0, "partial": 0.0}.get(arrival)
        if cutoff is not None and not queued and clock.value >= cutoff:
            enqueue(b"BACK\n" if arrival == "cancel" else b"\x04" if arrival == "eof"
                    else b"ER" if arrival == "partial" else b"ERASE\n")
            queued = True
        clock.add(seconds)

    def answer(w, prompt):
        assert prompt == C.CON_ERASE_PROMPT
        assert w.erase_enabled and clock.value >= 5.0
        # This is the first action after expiry. An early completed ERASE line
        # must already have been discarded before this prompt becomes usable.
        enqueue(b"ERASE\n" if arrival == "fresh" else b"ASE\n" if arrival == "partial" else b"BACK\n")
        value = real_answer(w, prompt)
        answers.append({"at": clock.value, "value": value})
        if value.strip().upper() != "ERASE":
            wizard.wants_shutdown = True  # bound the fake controller loop
        return value

    def fake_start(wipe_request):
        starts.append({"at": clock.value, "method": wipe_request.method.value})
        wizard.wants_shutdown = True  # no process or raw disk opened

    monkeypatch.setattr(console.time, "sleep", sleep)
    monkeypatch.setattr(console, "_answer", answer)
    monkeypatch.setattr(wizard.runner, "start", fake_start)
    try:
        assert console._plain_loop(wizard) == 0
        if arrival != "fresh":
            assert queued and inputs[0]["at"] < 5.0 and not inputs[0]["enabled"]
        request.node.user_properties.append(("pty_typeahead_trace", json.dumps({
            "arrival": arrival, "method": method.value, "inputs": inputs,
            "answers": answers, "fake_engine_starts": starts,
        })))
        assert len(starts) == (1 if arrival == "fresh" else 0), starts
        if arrival == "fresh":
            assert starts[0]["at"] >= 5.0
    finally:
        terminal.close()
        os.close(slave)
        os.close(master)


def test_canonical_method_read_does_not_hide_the_next_line_from_retirement(monkeypatch):
    wizard, _clock = _last_chance()
    master, slave = os.openpty()
    terminal = os.fdopen(os.dup(slave), "r", encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", terminal)
    try:
        assert terminal.isatty()
        assert termios.tcgetattr(slave)[3] & termios.ICANON
        os.write(master, b"METHOD\nERASE\n")
        assert terminal.readline() == "METHOD\n"
        console._retire_erase_typeahead(wizard)
        os.write(master, b"BACK\n")
        assert terminal.readline() == "BACK\n"
    finally:
        terminal.close()
        os.close(slave)
        os.close(master)


@pytest.mark.parametrize(("dry_run", "preview", "allowed"), [
    (True, False, True), (False, True, True), (True, True, True), (False, False, False),
])
def test_nonterminal_input_is_only_usable_for_fake_sessions(monkeypatch, dry_run, preview, allowed):
    wizard = SimpleNamespace(dry_run=dry_run, preview=preview)
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=lambda: False))
    if allowed:
        assert console._retire_erase_typeahead(wizard) is None
    else:
        with pytest.raises(EOFError):
            console._retire_erase_typeahead(wizard)


@pytest.mark.parametrize("failure", ["isatty", "fileno", "negative-fd", "bool-fd", "raw", "getattr", "flush"])
def test_unusable_terminal_retirement_refuses_a_fresh_erase_prompt(monkeypatch, failure):
    wizard = SimpleNamespace(dry_run=True, preview=True)
    calls = []

    def broken():
        raise OSError("fake private terminal unavailable")

    terminal = SimpleNamespace(isatty=broken if failure == "isatty" else lambda: True,
                               fileno=broken if failure == "fileno" else lambda: -1 if failure == "negative-fd"
                               else True if failure == "bool-fd" else 17)
    monkeypatch.setattr(sys, "stdin", terminal)

    def attributes(descriptor):
        assert descriptor == 17
        if failure == "getattr":
            raise termios.error("fake terminal attributes unavailable")
        return [0, 0, 0, 0 if failure == "raw" else termios.ICANON]

    def flush(descriptor, mode):
        calls.append((descriptor, mode))
        if failure == "flush":
            raise termios.error("fake terminal flush denied")

    monkeypatch.setattr(termios, "tcgetattr", attributes)
    monkeypatch.setattr(termios, "tcflush", flush)
    with pytest.raises(EOFError):
        console._retire_erase_typeahead(wizard)
    assert calls == ([(17, termios.TCIFLUSH)] if failure == "flush" else [])
