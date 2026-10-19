"""A staged live image needs an executable supervisor for its recovery UI."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

from test_iso_live_assets_pass20 import _fixture


ROOT = Path(__file__).resolve().parents[1]
KIOSK = "config/includes.chroot/usr/local/sbin/beamo-wipe-kiosk"


@pytest.mark.parametrize(
    "case", ["normal", "nonexecutable", "missing", "link", "directory", "linked-parent"]
)
def test_live_asset_staging_requires_executable_kiosk(tmp_path: Path, case: str) -> None:
    project, live, _source = _fixture(tmp_path)
    kiosk = live / KIOSK
    # Cross-platform checkouts may deliberately ignore working-tree mode
    # changes. A clean source status must not replace the runtime mode check.
    subprocess.run(["git", "config", "core.filemode", "false"], cwd=project, check=True)
    if case == "nonexecutable":
        kiosk.chmod(0o644)
        assert subprocess.check_output(
            ["git", "diff", "--raw", "--", str(kiosk.relative_to(project))], cwd=project
        ) == b""
    elif case == "missing":
        kiosk.unlink()
    elif case == "link":
        outside = tmp_path / "outside-kiosk"
        outside.write_bytes(kiosk.read_bytes())
        outside.chmod(0o755)
        kiosk.unlink()
        kiosk.symlink_to(outside)
    elif case == "directory":
        kiosk.unlink()
        kiosk.mkdir()
    elif case == "linked-parent":
        outside = tmp_path / "outside-sbin"
        kiosk.parent.rename(outside)
        kiosk.parent.symlink_to(outside, target_is_directory=True)

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/stage_live_assets.py"), str(project), str(live)],
        cwd=project,
        env={**os.environ, "BUILD_ID": "local"},
        capture_output=True,
        text=True,
        timeout=10,
    )

    if case == "normal":
        assert result.returncode == 0, result.stderr
        assert kiosk.stat().st_mode & 0o111
    else:
        assert result.returncode != 0, "unsafe kiosk path was accepted for the live image"
        if case == "nonexecutable":
            assert kiosk.stat().st_mode & 0o777 == 0o644
        elif case in {"link", "linked-parent"}:
            assert outside.exists()
            assert (kiosk if case == "link" else kiosk.parent).is_symlink()
