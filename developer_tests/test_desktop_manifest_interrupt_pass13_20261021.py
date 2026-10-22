"""Interrupted publication retires only the build's own unchanged receipt."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from beamo_wipe import __version__


ROOT = Path(__file__).resolve().parents[1]


def _builder_fixture(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "desktop_manifest_interrupt_pass13", ROOT / "scripts/build_desktop.py"
    )
    assert spec and spec.loader
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    desktop = tmp_path / "desktop"
    desktop.mkdir()
    (desktop / "go.mod").write_text("module fixture\n")
    (desktop / "main.go").write_text("package main\n")
    output = tmp_path / "output"

    def fake_output(argv, **_kwargs):
        if argv[1:] == ["version"]:
            return "go version go1.26.8 linux/amd64\n"
        if argv[1:] == ["rev-parse", "HEAD"]:
            return "a" * 40 + "\n"
        if argv[1:] == ["status", "--porcelain"]:
            return ""
        raise AssertionError(argv)

    def fake_build(argv, **_kwargs):
        Path(argv[argv.index("-o") + 1]).write_bytes(b"mock compiler output")

    monkeypatch.setattr(builder, "ROOT", tmp_path)
    monkeypatch.setattr(builder.subprocess, "check_output", fake_output)
    monkeypatch.setattr(builder.subprocess, "check_call", fake_build)
    return builder, output


@pytest.mark.parametrize("failure", [RuntimeError, KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("receipt_change", ["unchanged", "rewritten", "replaced"])
@pytest.mark.parametrize("launcher_change", [False, True])
def test_interrupted_final_verification_preserves_only_foreign_receipts(
    tmp_path, monkeypatch, failure, receipt_change, launcher_change
):
    builder, output = _builder_fixture(tmp_path, monkeypatch)
    original = builder._require_unchanged_launcher_outputs
    manifest = output / "desktop-build.json"
    interruption = failure("injected final-verification interruption")

    def interrupt_after_validation(*args):
        original(*args)
        if not manifest.exists():
            return
        if launcher_change:
            (output / builder.LAUNCHERS[0]).write_bytes(b"replacement launcher")
        if receipt_change == "rewritten":
            manifest.write_bytes(b"foreign receipt bytes\n")
        elif receipt_change == "replaced":
            replacement = output / "foreign-receipt"
            replacement.write_bytes(b"foreign receipt bytes\n")
            replacement.replace(manifest)
        raise interruption

    monkeypatch.setattr(
        builder, "_require_unchanged_launcher_outputs", interrupt_after_validation
    )
    with pytest.raises(failure) as caught:
        builder.build(output)
    assert caught.value is interruption
    assert not (output / ".build.lock").exists()
    if receipt_change == "unchanged":
        assert not manifest.exists()
    else:
        assert manifest.read_bytes() == b"foreign receipt bytes\n"
    assert (output / builder.LAUNCHERS[0]).read_bytes() == (
        b"replacement launcher" if launcher_change else b"mock compiler output"
    )
    assert (output / builder.LAUNCHERS[1]).read_bytes() == b"mock compiler output"


def test_completed_final_verification_retains_success_receipt(tmp_path, monkeypatch):
    builder, output = _builder_fixture(tmp_path, monkeypatch)
    builder.build(output)
    assert not (output / ".build.lock").exists()
    builder.verify_desktop_bundle(tmp_path, output, "a" * 40, __version__, False)
