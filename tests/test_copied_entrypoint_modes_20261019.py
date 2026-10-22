"""The private live-build copy must retain executable startup entrypoints."""

from __future__ import annotations

from pathlib import Path
import shutil

import pytest

from test_iso_copy_binding_pass37_build import (
    _container_check,
    _digest,
    _fixture,
    _run_check,
)


ENTRYPOINTS = (
    "includes.chroot/usr/local/bin/beamo-wipe",
    "includes.chroot/usr/local/sbin/beamo-wipe-kiosk",
    "hooks/normal/0500-build-nwipe.hook.chroot",
)


def _plant_copied_helper(copied: Path, body: str) -> None:
    helper = copied / "scripts/stage_wrapper_sources.py"
    helper.parent.mkdir(parents=True)
    helper.write_text(f"def require_executable(path):\n    {body}\n")


def test_copy_check_uses_trusted_executable_helper(tmp_path, monkeypatch):
    source, copied, _helper = _fixture(tmp_path)
    expected = _digest(source, monkeypatch)
    shutil.copytree(source, copied, dirs_exist_ok=True)
    _plant_copied_helper(copied, "raise AssertionError('copied helper must not run')")

    result = _run_check(_container_check(), expected, copied)

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("relative", ENTRYPOINTS)
def test_copy_check_refuses_nonexecutable_entrypoint(tmp_path, monkeypatch, relative):
    source, copied, _helper = _fixture(tmp_path)
    expected = _digest(source, monkeypatch)
    shutil.copytree(source, copied, dirs_exist_ok=True)
    source_entrypoint = source / "packaging/live/config" / relative
    copied_entrypoint = copied / "packaging/live/config" / relative
    copied_entrypoint.chmod(0o644)
    # A copied implementation must not be able to waive the mode check.
    _plant_copied_helper(copied, "pass")
    assert source_entrypoint.stat().st_mode & 0o777 == 0o755
    assert _digest(source, monkeypatch) == expected
    assert _digest(copied, monkeypatch) == expected

    result = _run_check(_container_check(), expected, copied)

    assert result.returncode != 0, "a copied non-executable entrypoint was accepted"
    assert "live entrypoint is missing or not executable" in result.stderr
    assert copied_entrypoint.stat().st_mode & 0o777 == 0o644
