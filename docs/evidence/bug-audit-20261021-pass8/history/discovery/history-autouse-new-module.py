"""Undecodable proc metadata blocks public startup before preview or recovery."""

import builtins
import json
from types import SimpleNamespace

import pytest

from beamo_wipe import app, discover, safety, session_recovery
from beamo_wipe.nwipe_runner import NwipeRunner


@pytest.fixture
def machine(tmp_path, monkeypatch):
    monkeypatch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    monkeypatch.delenv("BEAMO_WIPE_LIVE", raising=False)
    monkeypatch.setattr(safety.sys, "platform", "linux")
    command = tmp_path / "cmdline"
    command.write_bytes(b"quiet")
    mounts = tmp_path / "mountinfo"
    normal_mounts = (
        b"1 0 0:1 / / rw - overlay overlay rw\n"
        b"2 1 8:241 / /run/live/medium rw - iso9660 /dev/sdz1 rw\n"
    )
    mounts.write_bytes(normal_mounts)
    monkeypatch.setattr(discover, "MOUNTINFO_PATH", str(mounts))
    real_open = builtins.open
    reads, calls, effects = [], [], []

    def proc_file(path, *args, **kwargs):
        if str(path) == "/proc/cmdline":
            reads.append("cmdline")
            return real_open(command, *args, **kwargs)
        if str(path) == str(mounts):
            reads.append("mountinfo")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", proc_file)

    def forbidden(*_args, **_kwargs):
        effects.append(True)
        raise AssertionError("Native inventory, engine, process or power action forbidden")

    for boundary in (
        "subprocess.run", "subprocess.Popen", "beamo_wipe.discover.run_lsblk",
        "beamo_wipe.discover._run_findmnt", "beamo_wipe.discover.read_mount_sources",
        "beamo_wipe.diagnostics.emit_serial_marker",
    ):
        monkeypatch.setattr(boundary, forbidden)
    monkeypatch.setattr(NwipeRunner, "start", forbidden)
    monkeypatch.setattr(app, "_shutdown", forbidden)

    class Store:
        def __init__(self):
            calls.append("store-created")

        def open(self):
            calls.append("store-open")

        def close(self):
            calls.append("store-close")

    monkeypatch.setattr(session_recovery, "SessionStore", Store)

    def main(*_args, **_kwargs):
        calls.append("main")
        return 17

    monkeypatch.setattr(app, "_main", main)
    monkeypatch.setattr(app, "version_report", lambda: "Beamo Wipe fixture version\n")
    yield SimpleNamespace(command=command, mounts=mounts, normal_mounts=normal_mounts,
                          reads=reads, calls=calls, effects=effects)
    assert effects == []


def corrupt(machine, location, bad_bytes):
    machine.command.write_bytes(b"boot=live quiet")
    if location == "cmdline":
        machine.command.write_bytes(b"boot=live label=" + bad_bytes)
    else:
        # Linux mount paths are byte strings. Unrelated filenames need not be
        # UTF-8, even though the valid live medium and its source are ASCII.
        machine.mounts.write_bytes(
            machine.normal_mounts
            + b"3 1 8:33 / /media/" + bad_bytes + b" rw - ext4 /dev/sdc1 rw\n"
        )


@pytest.mark.parametrize("location", ["cmdline", "unrelated-mountpoint"])
@pytest.mark.parametrize("bad_bytes", [b"\xff", b"\xc3"], ids=["invalid-byte", "truncated-sequence"])
@pytest.mark.parametrize("argv", [(), ("--demo",), ("--dry-run",), ("--web",)],
                         ids=["normal", "preview", "dry-run", "web"])
def test_undecodable_live_classification_refuses_every_startup_route(
    machine, capsys, request, location, bad_bytes, argv,
):
    corrupt(machine, location, bad_bytes)
    escaped = None
    code = None
    try:
        code = app.main(list(argv))
    except BaseException as error:
        escaped = type(error).__name__
    output = capsys.readouterr()
    request.node.user_properties.append(("startup_refusal_trace", json.dumps({
        "location": location, "argv": argv, "code": code, "escaped": escaped,
        "reads": machine.reads, "calls": machine.calls,
        "native_callbacks": len(machine.effects),
    })))
    assert escaped is None
    assert code == 3
    assert output.err.strip() == app.RECOVERY_UNAVAILABLE
    assert machine.calls == []
    assert machine.reads == (["cmdline"] if location == "cmdline" else ["cmdline", "mountinfo"])


@pytest.mark.parametrize("live", [False, True], ids=["desktop", "live"])
@pytest.mark.parametrize("suffix", [b"", " label=caf\u00e9".encode()], ids=["ascii", "unicode"])
@pytest.mark.parametrize("argv", [(), ("--demo",), ("--web",)], ids=["normal", "preview", "web"])
def test_readable_metadata_preserves_existing_live_and_desktop_dispatch(machine, live, suffix, argv):
    machine.command.write_bytes((b"boot=live" if live else b"quiet") + suffix)
    assert app.main(list(argv)) == 17
    assert machine.calls == (["store-created", "store-open", "main", "store-close"] if live else ["main"])
    assert machine.reads == (["cmdline", "mountinfo"] if live else ["cmdline"])


@pytest.mark.parametrize("location", ["cmdline", "unrelated-mountpoint"])
@pytest.mark.parametrize("argv,status", [(("--help",), 0), (("--version",), 0), (("--invalid-option",), 2)],
                         ids=["help", "version", "invalid-arguments"])
def test_argument_exit_does_not_read_live_metadata_or_create_recovery(machine, location, argv, status):
    corrupt(machine, location, b"\xff")
    with pytest.raises(SystemExit) as error:
        app.main(list(argv))
    assert error.value.code == status
    assert machine.reads == []
    assert machine.calls == []
