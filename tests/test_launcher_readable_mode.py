# SPDX-License-Identifier: GPL-3.0-or-later
"""Live launcher: readable mode on very dense panels, from fake xrandr only.

The shipped shell functions run under /bin/sh with a fake ``xrandr`` first on
PATH and DISPLAY unset. No real X server, display or device is touched; the
fake records the exact argv of every call that is not ``--query``.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "packaging/live/config/includes.chroot/usr/local/bin/beamo-wipe"
PACKAGES = ROOT / "packaging/live/config/package-lists/beamo.list.chroot"

pytestmark = pytest.mark.skipif(
    not Path("/bin/sh").exists() or shutil.which("timeout") is None,
    reason="needs a POSIX /bin/sh and coreutils timeout",
)

ROT = "(normal left inverted right x axis y axis)"

LAPTOP_4K = f"""Screen 0: minimum 320 x 200, current 3840 x 2160, maximum 16384 x 16384
eDP-1 connected primary 3840x2160+0+0 {ROT} 344mm x 194mm
   3840x2160     60.00*+  59.97    59.96    59.93
   3200x1800     59.96    59.94
   2880x1620     59.96    59.97
   2560x1600     59.99    59.97
   2560x1440     59.99    59.99    59.96    59.95
   2048x1536     60.00
   1920x1440     60.00
   2048x1152     59.99    59.98    59.90    59.91
   1920x1200     59.88    59.95
   1920x1080     60.01    59.97    59.96    59.93
   1920x1080i    60.00    50.00
   1600x1200     60.00
   1680x1050     59.95    59.88
   1600x900      59.99    59.94    59.95    59.82
   1280x720      60.00    59.99    59.86    59.74
   1024x768      60.04    60.00
   800x600       60.32    56.25
   640x480       59.94
DP-1 disconnected {ROT}
HDMI-1 disconnected {ROT}
"""

LAPTOP_2560X1600 = f"""Screen 0: minimum 320 x 200, current 2560 x 1600, maximum 16384 x 16384
eDP connected primary 2560x1600+0+0 {ROT} 345mm x 215mm
   2560x1600    165.00*+  60.00
   1920x1200    165.00
   1920x1080    165.00
   1600x1200    165.00
   1680x1050    165.00
   1280x1024    165.00
   1440x900     165.00
   1280x800     165.00
   1280x720     165.00
   1024x768     165.00
   800x600      165.00
HDMI-A-0 disconnected {ROT}
"""

DESKTOP_1440P = f"""Screen 0: minimum 320 x 200, current 2560 x 1440, maximum 16384 x 16384
DP-1 connected primary 2560x1440+0+0 {ROT} 597mm x 336mm
   2560x1440     59.95*+
   1920x1080     60.00    59.94
   1280x720      60.00
"""

CLONE_4K_AND_FHD = f"""Screen 0: minimum 320 x 200, current 3840 x 2160, maximum 16384 x 16384
eDP-1 connected primary 3840x2160+0+0 {ROT} 344mm x 194mm
   3840x2160     60.00*+
   1920x1080     60.01
HDMI-1 connected 1920x1080+0+0 {ROT} 531mm x 299mm
   1920x1080     60.00*+  50.00
   1280x720      60.00
"""

CLONE_TWO_4K = f"""Screen 0: minimum 320 x 200, current 3840 x 2160, maximum 16384 x 16384
DP-1 connected primary 3840x2160+0+0 {ROT} 600mm x 340mm
   3840x2160     60.00*+
   2560x1440     59.95
   1920x1080     60.00
DP-2 connected 3840x2160+0+0 {ROT} 600mm x 340mm
   3840x2160     60.00*+
   1920x1200     59.95
   1920x1080     60.00
"""

SPAN_4K_AND_FHD = f"""Screen 0: minimum 320 x 200, current 5760 x 2160, maximum 16384 x 16384
eDP-1 connected primary 3840x2160+0+0 {ROT} 344mm x 194mm
   3840x2160     60.00*+
   1920x1080     60.01
HDMI-1 connected 1920x1080+3840+0 {ROT} 531mm x 299mm
   1920x1080     60.00*+
"""

SIMPLEDRM_4K = f"""Screen 0: minimum 320 x 200, current 3840 x 2160, maximum 3840 x 2160
None-1 connected primary 3840x2160+0+0 {ROT} 0mm x 0mm
   3840x2160     60.00*+
"""

FHD = f"""Screen 0: minimum 320 x 200, current 1920 x 1080, maximum 16384 x 16384
eDP-1 connected primary 1920x1080+0+0 {ROT} 309mm x 174mm
   1920x1080     60.02*+  59.93
   1680x1050     59.88
   1280x720      60.00
"""

VGA_800 = f"""Screen 0: minimum 320 x 200, current 800 x 600, maximum 8192 x 8192
Virtual-1 connected primary 800x600+0+0 {ROT} 0mm x 0mm
   800x600       60.00*+  56.25
   640x480       59.94
"""

MALFORMED = [
    "",
    "xrandr: Failed to get size of gamma for output default\n",
    "garbage without structure\n   3840x2160 60.00*\n   1920x1080 60.00\n",
    f"eDP-1 connected primary 3840x2160+0 {ROT} 344mm x 194mm\n   1920x1080  60.00\n",
    f"eDP-1 connected primary 3840x2160+0+0 {ROT} 344mm x 194mm\n"
    "   1920x1080i 60.00\n   abcxdef\n   99999999x1080 60.00\n   1920 60.00\n"
    "   01920x1080 60.00\n   1920x01080 60.00\n",
    # Rotated panels report swapped geometry; leave them alone.
    f"eDP-1 connected primary 2160x3840+0+0 left {ROT} 344mm x 194mm\n"
    "   3840x2160 60.00*+\n   1920x1080 60.00\n",
    # Output names that are not plain identifiers are never passed on.
    f"eDP;1 connected primary 3840x2160+0+0 {ROT} 344mm x 194mm\n"
    "   3840x2160 60.00*+\n   1920x1080 60.00\n",
    f"-x connected primary 3840x2160+0+0 {ROT} 344mm x 194mm\n"
    "   3840x2160 60.00*+\n   1920x1080 60.00\n",
    # Negative positions, unknown connection, connected but not lit.
    f"eDP-1 connected primary 3840x2160+-10+0 {ROT} 344mm x 194mm\n"
    "   3840x2160 60.00*+\n   1920x1080 60.00\n",
    f"eDP-1 unknown connection 3840x2160+0+0 {ROT} 344mm x 194mm\n"
    "   3840x2160 60.00*+\n   1920x1080 60.00\n",
    f"eDP-1 connected {ROT}\n   3840x2160 60.00+\n   1920x1080 60.00\n",
]


def _functions() -> str:
    text = LAUNCHER.read_text(encoding="utf-8")
    found = []
    for name in ("beamo_uint", "beamo_mode_flush", "beamo_readable_mode"):
        match = re.search(rf"(?ms)^{name}\(\) {{\n.*?^}}\n", text)
        assert match, name
        found.append(match.group(0))
    return "\n".join(found)


def _run(tmp_path: Path, query: str | None, *, query_rc: int = 0, set_rc: int = 0):
    """Run the shipped functions; return (exit code, list of xrandr argv)."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    (bin_dir / "timeout").symlink_to(shutil.which("timeout"))
    log = tmp_path / "calls"
    fixture = tmp_path / "query"
    if query is not None:
        fixture.write_text(query, encoding="utf-8")
        fake = bin_dir / "xrandr"
        fake.write_text(
            "#!/bin/sh\n"
            'if [ "$#" -eq 1 ] && [ "$1" = --query ]; then\n'
            f'  while IFS= read -r l || [ -n "$l" ]; do printf "%s\\n" "$l"; done < "{fixture}"\n'
            f"  exit {query_rc}\n"
            "fi\n"
            f'for a in "$@"; do printf "%s\\n" "$a"; done >> "{log}"\n'
            f'printf "%s\\n" --end-- >> "{log}"\n'
            f"exit {set_rc}\n",
            encoding="utf-8",
        )
        fake.chmod(0o755)
    script = tmp_path / "run.sh"
    script.write_text("set -eu\n" + _functions() + "\nbeamo_readable_mode\n", encoding="utf-8")
    env = {"PATH": str(bin_dir), "HOME": str(tmp_path), "LC_ALL": "C"}
    result = subprocess.run(
        ["/bin/sh", str(script)], env=env, capture_output=True, text=True, timeout=30
    )
    calls = []
    if log.exists():
        current: list[str] = []
        for line in log.read_text(encoding="utf-8").splitlines():
            if line == "--end--":
                calls.append(current)
                current = []
            else:
                current.append(line)
    return result.returncode, calls


@pytest.mark.parametrize(
    "query,want",
    [
        (LAPTOP_4K, ["--output", "eDP-1", "--mode", "1920x1080"]),
        (LAPTOP_2560X1600, ["--output", "eDP", "--mode", "1920x1200"]),
        (CLONE_4K_AND_FHD, ["--output", "eDP-1", "--mode", "1920x1080"]),
        (
            CLONE_TWO_4K,
            ["--output", "DP-1", "--mode", "1920x1080",
             "--output", "DP-2", "--mode", "1920x1080"],
        ),
    ],
    ids=["4k-laptop-edp", "2560x1600-laptop", "clone-4k-and-fhd", "clone-two-4k"],
)
def test_dense_panels_get_one_exact_mode_switch(tmp_path, query, want):
    rc, calls = _run(tmp_path, query)
    assert rc == 0
    assert calls == [want]


@pytest.mark.parametrize(
    "query",
    [SPAN_4K_AND_FHD, SIMPLEDRM_4K, FHD, VGA_800, DESKTOP_1440P],
    ids=["dual-side-by-side", "simpledrm-one-mode", "1920x1080", "800x600", "27in-1440p"],
)
def test_no_switch_when_not_needed_or_not_safe(tmp_path, query):
    rc, calls = _run(tmp_path, query)
    assert rc == 0
    assert calls == []


def test_2560_wide_panel_without_physical_size_is_left_alone(tmp_path):
    query = LAPTOP_2560X1600.replace("345mm x 215mm", "0mm x 0mm")
    rc, calls = _run(tmp_path, query)
    assert (rc, calls) == (0, [])


def test_aspect_must_match_the_panel(tmp_path):
    # A 3:2 4K-class panel offers only 16:9 and 16:10 modes up to 1920x1200.
    query = (
        f"eDP-1 connected primary 3000x2000+0+0 {ROT} 293mm x 196mm\n"
        "   3000x2000 60.00*+\n   1920x1200 60.00\n   1920x1080 60.00\n"
    )
    assert _run(tmp_path, query) == (0, [])


@pytest.mark.parametrize("index", range(len(MALFORMED)))
def test_malformed_or_unusual_output_never_switches(tmp_path, index):
    rc, calls = _run(tmp_path, MALFORMED[index])
    assert rc == 0
    assert calls == []


def test_missing_xrandr_is_a_quiet_no_op(tmp_path):
    assert _run(tmp_path, None) == (0, [])


def test_failed_query_is_a_quiet_no_op(tmp_path):
    assert _run(tmp_path, LAPTOP_4K, query_rc=1) == (0, [])


def test_failed_mode_switch_never_fails_the_session(tmp_path):
    rc, calls = _run(tmp_path, LAPTOP_4K, set_rc=1)
    assert rc == 0
    assert calls == [["--output", "eDP-1", "--mode", "1920x1080"]]


def test_launcher_calls_it_guarded_contained_and_before_the_wizard():
    text = LAUNCHER.read_text(encoding="utf-8")
    guard = 'if [ -n "${DISPLAY:-}" ]; then'
    call = "  (beamo_readable_mode) 2>/dev/null || true"
    assert call in text.splitlines()
    assert text.index(guard) < text.index(call) < text.index("exec python3")
    assert "x11-xserver-utils" in PACKAGES.read_text(encoding="utf-8")
    # xrandr is only probed with command -v or run under a timeout.
    body = _functions()
    uses = [body[max(0, m.start() - 12):m.start()] for m in re.finditer(r"xrandr\b", body)]
    assert len(uses) == 3
    for before in uses:
        assert before.endswith("command -v ") or re.search(r"timeout \d+ $", before)
    for word in ("eval", "`", "exec ", "sudo", "/dev/sd", "/dev/nvme", "rm -", "/sys"):
        assert word not in body


@pytest.mark.skipif(shutil.which("shellcheck") is None, reason="shellcheck not installed")
def test_launcher_is_shellcheck_clean(tmp_path):
    # Read through Python so a CRLF checkout cannot fake a failure.
    copy = tmp_path / "beamo-wipe"
    copy.write_text(LAUNCHER.read_text(encoding="utf-8"), encoding="utf-8")
    result = subprocess.run(
        ["shellcheck", "-s", "sh", str(copy)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout
