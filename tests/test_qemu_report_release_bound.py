# SPDX-License-Identifier: GPL-3.0-or-later
"""The report export may delay Tk's deferred Space-release callback."""

import os
from pathlib import Path
import subprocess

import pytest


QEMU = Path(__file__).resolve().parents[1] / "scripts/qemu-verify.sh"


def test_report_export_uses_its_save_budget_for_space_release():
    source = QEMU.read_text(encoding="utf-8")
    export = source.split("drive_report_export() {", 1)[1].split("\n}", 1)[0]
    assert (
        'send_key_for_marker "$label" "$qmp_socket" spc '
        "BEAMO_WIPE_REPORT_SAVING 20 120"
    ) in export


@pytest.mark.parametrize(
    ("release_limit", "expected_status", "expected_sleeps"),
    [(None, 1, 20), (120, 0, 22)],
)
def test_slow_report_export_keeps_release_ack_mandatory_without_repressing(
    tmp_path, release_limit, expected_status, expected_sleeps
):
    source = QEMU.read_text(encoding="utf-8")
    function = "send_key_for_marker() {" + source.split(
        "send_key_for_marker() {", 1
    )[1].split("\n}", 1)[0] + "\n}"
    sleeps = tmp_path / "sleeps"
    events = tmp_path / "events"
    sleeps.touch()
    script = "\n".join(
        (
            function,
            'sleep() { printf "%s\\n" "$1" >> "$MOCK_SLEEPS"; }',
            """marker_count() {
  if [[ "$2" == BEAMO_WIPE_KEY_SPACE_RELEASED &&
        $(wc -l < "$MOCK_SLEEPS") -ge 22 ]]; then
    printf '1\\n'
  else
    printf '0\\n'
  fi
}""",
            'qmp_request() { printf "%s\\n" "$2" >> "$MOCK_EVENTS"; }',
            'wait_for_new_marker() { [[ "$2" != BEAMO_WIPE_KEY_SPACE_RELEASED ]]; }',
            "send_key_for_marker bios-report /tmp/qmp spc BEAMO_WIPE_REPORT_SAVING 20"
            + (f" {release_limit}" if release_limit is not None else ""),
        )
    )
    result = subprocess.run(
        ["bash", "-ceu", script],
        env=dict(os.environ, MOCK_SLEEPS=str(sleeps), MOCK_EVENTS=str(events)),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == expected_status, result.stderr
    assert sleeps.read_text().splitlines() == ["1"] * expected_sleeps
    assert events.read_text().splitlines() == [
        "key-down", "key-up", "key-up", "key-up"
    ]
