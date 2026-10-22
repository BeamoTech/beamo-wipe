"""Later metadata decoding errors preserve the public blocked startup exit."""

import builtins
import json
from types import SimpleNamespace

import pytest

from beamo_wipe import app, discover, safety, session_recovery
from beamo_wipe.nwipe_runner import NwipeRunner


@pytest.fixture
def machine(monkeypatch, tmp_path):
    mode = {"owned": False, "fault": 2, "location": "cmdline", "bad": b"\xff", "suffix": b""}
    reads, calls, sessions, effects = [], [], [], []
    command, table = tmp_path / "command", tmp_path / "mounts"
    live_table = b"1 0 8:241 / /run/live/medium ro - iso9660 /dev/sdz1 ro\n"
    original_open = builtins.open
    monkeypatch.setattr(safety.sys, "platform", "linux")
    monkeypatch.setattr(app, "running_on_live_usb", safety.running_on_live_usb)
    monkeypatch.delenv("BEAMO_WIPE_DEMO", raising=False)
    monkeypatch.delenv("BEAMO_WIPE_UI", raising=False)

    def proc_file(path, *args, **kwargs):
        if str(path) == "/proc/cmdline":
            reads.append("cmdline")
            if mode["fault"] and not mode["owned"] and len(reads) == 1:
                raise OSError("Injected first metadata read failure")
            live = mode["owned"] or bool(mode["fault"])
            text = (b"boot=live quiet" if live else b"quiet") + mode["suffix"]
            if len(reads) == mode["fault"] and mode["location"] == "cmdline":
                text += b" label=" + mode["bad"]
            command.write_bytes(text)
            return original_open(command, *args, **kwargs)
        if str(path) == discover.MOUNTINFO_PATH:
            text = live_table
            if len(reads) == mode["fault"] and mode["location"] == "mountinfo":
                text += b"2 0 8:1 / /media/" + mode["bad"] + b" rw - ext4 /dev/sda1 rw\n"
            table.write_bytes(text)
            return original_open(table, *args, **kwargs)
        if str(path).startswith(("/dev/", "/proc/", "/sys/")):
            effects.append(str(path))
            raise AssertionError("Native path forbidden")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", proc_file)

    def forbidden(*_args, **_kwargs):
        effects.append("native callback")
        raise AssertionError("Native inventory, process, engine or power action forbidden")

    for boundary in (
        "subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk",
        "beamo_wipe.discover._run_findmnt", "beamo_wipe.discover.read_mount_sources",
    ):
        monkeypatch.setattr(boundary, forbidden)
    monkeypatch.setattr(NwipeRunner, "start", forbidden)
    monkeypatch.setattr(app, "_shutdown", forbidden)
    monkeypatch.setattr(app.signal, "signal", lambda *_args: None)
    monkeypatch.setattr("beamo_wipe.diagnostics.log_diag", lambda *_a, **_k: None)
    monkeypatch.setattr("beamo_wipe.diagnostics.emit_serial_marker", lambda *_a, **_k: None)

    class Store:
        def open(self):
            calls.append("open")

        def close(self):
            calls.append("close")

    monkeypatch.setattr(session_recovery, "SessionStore", Store)

    def session(_args, **kwargs):
        sessions.append(kwargs["session_store"] is not None)
        return 17

    monkeypatch.setattr(app, "_run_session", session)
    monkeypatch.setattr(app, "version_report", lambda: "Beamo Wipe fixture version\n")
    yield SimpleNamespace(mode=mode, reads=reads, calls=calls, sessions=sessions, effects=effects)
    assert effects == []


@pytest.mark.parametrize("owned,fault", [(False, 2), (False, 3), (True, 2)],
                         ids=["unowned-override", "unowned-admission", "owned-control"])
@pytest.mark.parametrize("location", ["cmdline", "mountinfo"])
@pytest.mark.parametrize("bad", [b"\xff", b"\xc3"], ids=["invalid-byte", "truncated-sequence"])
@pytest.mark.parametrize("argv", [("--demo",), ("--web",)], ids=["preview", "web"])
def test_late_decode_failure_refuses_without_dispatch(
    machine, capsys, request, owned, fault, location, bad, argv,
):
    machine.mode.update(owned=owned, fault=fault, location=location, bad=bad)
    escaped = None
    code = None
    try:
        code = app.main(list(argv))
    except UnicodeError as error:
        escaped = type(error).__name__
    output = capsys.readouterr()
    request.node.user_properties.append(("late_decode_trace", json.dumps({
        "owned": owned, "classification": fault, "location": location, "argv": argv,
        "code": code, "escaped": escaped, "reads": machine.reads, "store": machine.calls,
        "session_dispatch": machine.sessions, "native_callbacks": len(machine.effects),
    })))
    assert escaped is None
    assert code == 3
    assert output.err.strip() == app.RECOVERY_UNAVAILABLE
    assert machine.sessions == []
    assert machine.calls == (["open", "close"] if owned else [])


@pytest.mark.parametrize("owned", [False, True], ids=["desktop", "owned-live"])
@pytest.mark.parametrize("suffix", [b"", " label=caf\u00e9".encode()], ids=["ascii", "unicode"])
@pytest.mark.parametrize("argv", [("--demo",), ("--dry-run", "--console")], ids=["preview", "console"])
def test_readable_metadata_keeps_existing_session_dispatch(machine, owned, suffix, argv):
    machine.mode.update(owned=owned, fault=0, suffix=suffix)
    assert app.main(list(argv)) == 17
    assert machine.sessions == [owned]
    assert machine.calls == (["open", "close"] if owned else [])


@pytest.mark.parametrize("owned", [False, True], ids=["desktop", "live"])
@pytest.mark.parametrize("argv,status", [(("--help",), 0), (("--version",), 0), (("--invalid-option",), 2)],
                         ids=["help", "version", "invalid-arguments"])
def test_argument_exit_still_avoids_metadata_and_recovery(machine, owned, argv, status):
    machine.mode.update(owned=owned)
    with pytest.raises(SystemExit) as error:
        app.main(list(argv))
    assert error.value.code == status
    assert machine.reads == machine.calls == machine.sessions == []
