"""#182: the launcher signing script refuses unsafe input and its dry run signs nothing.

No network, no Java, no real certificate: every run uses fake files and a
runner that fails the test if it is called.
"""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import struct
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "sign_windows_launcher_182", ROOT / "scripts" / "sign_windows_launcher.py"
)
sign = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = sign
_SPEC.loader.exec_module(sign)

TOKEN = "fake-token-value-that-must-never-print"


def fake_pe(cert_offset: int = 0, cert_size: int = 0) -> bytes:
    """A minimal PE32+ header with a certificate table entry."""
    data = bytearray(0x400)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0x80)
    data[0x80:0x84] = b"PE\0\0"
    optional = 0x80 + 24
    struct.pack_into("<H", data, optional, 0x20B)
    struct.pack_into("<I", data, optional + 108, 16)
    struct.pack_into("<II", data, optional + 112 + 4 * 8, cert_offset, cert_size)
    return bytes(data)


def never_run(*args, **kwargs):
    raise AssertionError("dry run or refusal must not start a process")


@pytest.fixture
def setup(tmp_path, monkeypatch):
    jar = tmp_path / "jsign.jar"
    jar.write_bytes(b"fake jsign jar")
    monkeypatch.setattr(
        sign, "JSIGN_SHA256", hashlib.sha256(b"fake jsign jar").hexdigest()
    )
    ca = tmp_path / "roots.pem"
    ca.write_text("fake roots\n")
    out = tmp_path / "out"
    out.mkdir()
    launcher = out / sign.LAUNCHER_NAME
    launcher.write_bytes(fake_pe())
    env = {
        "BEAMO_SIGN_ENDPOINT": "https://eus.codesigning.azure.net/",
        "BEAMO_SIGN_ACCOUNT": "beamowipesign",
        "BEAMO_SIGN_PROFILE": "beamowipe-public",
        "BEAMO_SIGN_PUBLISHER": "Example Publisher",
        "BEAMO_SIGN_JSIGN_JAR": str(jar),
        "BEAMO_SIGN_CA_FILE": str(ca),
    }
    return env, launcher


def test_dry_run_prints_commands_and_signs_nothing(setup, capsys):
    env, launcher = setup
    before = launcher.read_bytes()
    assert sign.main(["--dry-run", str(launcher)], env=env, run=never_run) == 0
    out = capsys.readouterr().out
    assert "DRY RUN: nothing was signed." in out
    assert "access token (BEAMO_SIGN_ACCESS_TOKEN): not set" in out
    assert "TRUSTEDSIGNING" in out and "env:BEAMO_SIGN_ACCESS_TOKEN" in out
    assert sign.TIMESTAMP_URL in out and "RFC3161" in out
    assert "beamowipesign/beamowipe-public" in out
    assert launcher.read_bytes() == before


def test_dry_run_never_prints_the_token(setup, capsys):
    env, launcher = setup
    env = {**env, sign.TOKEN_ENV: TOKEN}
    assert sign.main(["--dry-run", str(launcher)], env=env, run=never_run) == 0
    captured = capsys.readouterr()
    assert "access token (BEAMO_SIGN_ACCESS_TOKEN): set" in captured.out
    assert TOKEN not in captured.out + captured.err


@pytest.mark.parametrize("missing", sign.SETTINGS)
def test_refuses_without_each_setting(setup, capsys, missing):
    env, launcher = setup
    env = {k: v for k, v in env.items() if k != missing}
    assert sign.main(["--dry-run", str(launcher)], env=env, run=never_run) == 2
    assert missing in capsys.readouterr().err


def test_real_run_refuses_without_token(setup, capsys):
    env, launcher = setup
    assert sign.main([str(launcher)], env=env, run=never_run) == 2
    assert "BEAMO_SIGN_ACCESS_TOKEN" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("BEAMO_SIGN_ENDPOINT", "http://eus.codesigning.azure.net"),
        ("BEAMO_SIGN_ENDPOINT", "https://evil.example.com"),
        ("BEAMO_SIGN_ACCOUNT", "a"),
        ("BEAMO_SIGN_ACCOUNT", "bad--name"),
        ("BEAMO_SIGN_PROFILE", "x/y"),
        ("BEAMO_SIGN_PUBLISHER", "bad\nname"),
    ],
)
def test_refuses_bad_settings(setup, name, value):
    env, launcher = setup
    env = {**env, name: value}
    assert sign.main(["--dry-run", str(launcher)], env=env, run=never_run) == 2


def test_refuses_other_file_names(setup, capsys):
    env, launcher = setup
    other = launcher.with_name("Start Beamo Wipe Linux")
    other.write_bytes(fake_pe())
    assert sign.main(["--dry-run", str(other)], env=env, run=never_run) == 2
    assert "only 'Start Beamo Wipe.exe' is signed" in capsys.readouterr().err


def test_refuses_missing_and_directory_paths(setup, tmp_path):
    env, _ = setup
    missing = tmp_path / "gone" / sign.LAUNCHER_NAME
    assert sign.main(["--dry-run", str(missing)], env=env, run=never_run) == 2
    folder = tmp_path / "dir" / sign.LAUNCHER_NAME
    folder.mkdir(parents=True)
    assert sign.main(["--dry-run", str(folder)], env=env, run=never_run) == 2


def test_refuses_the_same_path_twice(setup):
    env, launcher = setup
    assert (
        sign.main(["--dry-run", str(launcher), str(launcher)], env=env, run=never_run)
        == 2
    )


def test_refuses_non_pe_and_already_signed(setup, capsys):
    env, launcher = setup
    launcher.write_bytes(b"#!/bin/sh\n" + bytes(100))
    assert sign.main(["--dry-run", str(launcher)], env=env, run=never_run) == 2
    assert "no MZ header" in capsys.readouterr().err
    launcher.write_bytes(fake_pe(cert_offset=0x300, cert_size=0x100))
    assert sign.main(["--dry-run", str(launcher)], env=env, run=never_run) == 2
    assert "already signed" in capsys.readouterr().err


def test_refuses_an_unpinned_jsign_jar(setup, capsys, monkeypatch):
    env, launcher = setup
    monkeypatch.setattr(sign, "JSIGN_SHA256", "0" * 64)
    assert sign.main(["--dry-run", str(launcher)], env=env, run=never_run) == 2
    assert "not the pinned jsign" in capsys.readouterr().err


def test_failed_signing_hides_the_token(setup, capsys):
    env, launcher = setup
    env = {**env, sign.TOKEN_ENV: TOKEN}

    class Result:
        returncode = 1
        stdout = f"error: rejected token {TOKEN}"

    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        assert TOKEN not in " ".join(command)
        return Result()

    assert sign.main([str(launcher)], env=env, run=fake_run) == 2
    err = capsys.readouterr().err
    assert len(calls) == 1 and "jsign sign failed with exit 1" in err
    assert TOKEN not in err and "[hidden]" in err


def test_real_run_requires_a_written_signature(setup, capsys):
    env, launcher = setup
    env = {**env, sign.TOKEN_ENV: TOKEN}

    class Result:
        returncode = 0
        stdout = ""

    assert sign.main([str(launcher)], env=env, run=lambda *a, **k: Result()) == 2
    assert "wrote no signature" in capsys.readouterr().err


def test_real_run_checks_publisher_and_timestamp(setup, capsys):
    env, launcher = setup
    env = {**env, sign.TOKEN_ENV: TOKEN}
    verify_output = {"text": "Signature verification: ok\nSubject: CN=Someone Else\n"}

    class Result:
        def __init__(self, stdout):
            self.returncode = 0
            self.stdout = stdout

    def fake_run(command, **kwargs):
        if "TRUSTEDSIGNING" in command:
            launcher.write_bytes(fake_pe(cert_offset=0x300, cert_size=0x100))
            return Result("")
        return Result(verify_output["text"])

    assert sign.main([str(launcher)], env=env, run=fake_run) == 2
    assert "signer is not 'Example Publisher'" in capsys.readouterr().err

    launcher.write_bytes(fake_pe())
    verify_output["text"] = (
        "Signature verification: ok\nSubject: CN=Example Publisher\n"
    )
    assert sign.main([str(launcher)], env=env, run=fake_run) == 2
    assert "no timestamp found" in capsys.readouterr().err

    launcher.write_bytes(fake_pe())
    verify_output["text"] += "Timestamp Verification: ok\n"
    assert sign.main([str(launcher)], env=env, run=fake_run) == 0
    out = capsys.readouterr().out
    assert '"publisher": "Example Publisher"' in out and TOKEN not in out
