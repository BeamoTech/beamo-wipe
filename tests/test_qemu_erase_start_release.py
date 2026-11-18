# SPDX-License-Identifier: GPL-3.0-or-later
"""Erase now's Return is released as soon as the guest accepts the press.

Hosted runs 41528619370 and 43920534790 (attempts 1 and 2) lost the release
of this one press: the key-up was sent only after the 1 s serial poll saw
Working, which on slow runners landed after Working's own redraw. The driver
now releases on the guest's acceptance marker, before Working, and still
requires a fresh release acknowledgement without ever pressing again.

The guest may report the accepted press as RETURN_RESULT_WORKING instead of
RETURN_RESULT_CHECKING when the pre-erase check finishes inside the Return
handler (main run 44068634926 attempt 1); either new marker is acceptance.
"""

import os
from pathlib import Path
import subprocess

import pytest


QEMU = Path(__file__).resolve().parents[1] / "scripts/qemu-verify.sh"


def _function(source: str, name: str) -> str:
    return f"{name}() {{" + source.split(f"{name}() {{", 1)[1].split("\n}", 1)[0] + "\n}"


MOCKS = r"""
sleep() { printf '%s\n' "$1" >> "$MOCK_SLEEPS"; }
qmp_request() { printf '%s\n' "$2" >> "$MOCK_EVENTS"; }
report_marker_summary() { printf 'summary\n' >> "$MOCK_EVENTS"; }
capture_guest_screen() { printf 'screen\n' >> "$MOCK_EVENTS"; }
polls() { grep -c '^0\.1$' "$MOCK_SLEEPS" || true; }
released() { grep -q '^key-up$' "$MOCK_EVENTS"; }
accepted() { [[ "$MOCK_ACCEPT_AFTER" -ge 0 && "$(polls)" -ge "$MOCK_ACCEPT_AFTER" ]]; }
marker_count() {
  case "$2" in
    BEAMO_WIPE_RETURN_RESULT_CHECKING|BEAMO_WIPE_RETURN_RESULT_WORKING)
      # MOCK_WORKING_BEFORE: RETURN_RESULT_WORKING results from earlier
      # journeys, which must never count as acceptance of this press.
      local base=0
      if [[ "$2" == BEAMO_WIPE_RETURN_RESULT_WORKING ]]; then base="$MOCK_WORKING_BEFORE"; fi
      if [[ "$2" == "$MOCK_ACCEPT_MARKER" ]] && accepted; then
        printf '%s\n' "$((base + 1))"; else printf '%s\n' "$base"; fi ;;
    BEAMO_WIPE_KEY_RETURN_RELEASED)
      # Before the press there were two older releases; the guest adds one
      # only for a key-up that it actually received.
      if [[ "$MOCK_RELEASE_ACK" == 1 ]] && released; then
        printf '3\n'; else printf '2\n'; fi ;;
    BEAMO_WIPE_SCREEN_WORKING)
      # Working only appears after the key-up: the driver must not wait for
      # Working while the key is still held.
      if released; then printf '1\n'; else printf '0\n'; fi ;;
    BEAMO_WIPE_SCREEN_DONE)
      # MOCK_DONE_AFTER_RELEASE: the erase reaches Done although the guest
      # never acknowledged the release (the BW-QEMU-FLAKES part a shape).
      if [[ "$MOCK_DONE_AFTER_RELEASE" == 1 ]] && released; then
        printf '1\n'; else printf '0\n'; fi ;;
    *) printf '0\n' ;;
  esac
}
wait_for_new_marker() {
  printf 'await-new %s\n' "$2" >> "$MOCK_EVENTS"
  [[ "$(marker_count "$1" "$2")" -gt "$3" ]]
}
"""


def _run(
    tmp_path,
    accept_after: int,
    release_ack: bool,
    accept_marker: str = "BEAMO_WIPE_RETURN_RESULT_CHECKING",
    working_before: int = 0,
    done_after_release: bool = False,
):
    source = QEMU.read_text(encoding="utf-8")
    sleeps = tmp_path / "sleeps"
    events = tmp_path / "events"
    sleeps.touch()
    events.touch()
    script = "\n".join(
        (
            MOCKS,
            _function(source, "start_erase_with_return"),
            "start_erase_with_return bios-everyday /tmp/qmp 20",
        )
    )
    result = subprocess.run(
        ["bash", "-ceu", script],
        env=dict(
            os.environ,
            MOCK_SLEEPS=str(sleeps),
            MOCK_EVENTS=str(events),
            MOCK_ACCEPT_AFTER=str(accept_after),
            MOCK_RELEASE_ACK="1" if release_ack else "0",
            MOCK_ACCEPT_MARKER=accept_marker,
            MOCK_WORKING_BEFORE=str(working_before),
            MOCK_DONE_AFTER_RELEASE="1" if done_after_release else "0",
        ),
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result, sleeps.read_text().splitlines(), events.read_text().splitlines()


def test_release_follows_acceptance_before_working(tmp_path):
    result, sleeps, events = _run(tmp_path, accept_after=3, release_ack=True)
    assert result.returncode == 0, result.stderr
    # Released on the third 0.1 s poll, with no 1 s wait for Working first.
    assert sleeps == ["0.1"] * 3
    assert events == [
        "key-down",
        "key-up",
        "await-new BEAMO_WIPE_SCREEN_WORKING",
    ]


def test_lost_release_stays_a_failure_and_is_never_repressed(tmp_path):
    result, sleeps, events = _run(tmp_path, accept_after=1, release_ack=False)
    assert result.returncode == 1
    # 20 release polls, then at most 60 s for Done (diagnostics only).
    assert sleeps == ["0.1"] + ["1"] * 20 + ["1"] * 60
    assert events == [
        "key-down",
        "key-up",
        "key-up",
        "key-up",
        "await-new BEAMO_WIPE_KEY_RETURN_RELEASED",
        "screen",
    ]
    assert events.count("key-down") == 1


def test_lost_release_waits_for_done_diagnostics_and_still_fails(tmp_path):
    """The bounded wait ends one second after Done so the guest's focus and
    X input markers land in the summary. Nothing is pressed and the journey
    still fails without a fresh release acknowledgement."""
    result, sleeps, events = _run(
        tmp_path, accept_after=1, release_ack=False, done_after_release=True
    )
    assert result.returncode == 1
    assert sleeps == ["0.1"] + ["1"] * 20 + ["1"]
    assert events.count("key-down") == 1
    assert events[-2:] == ["await-new BEAMO_WIPE_KEY_RETURN_RELEASED", "screen"]


def test_unaccepted_press_is_released_and_fails_closed(tmp_path):
    result, sleeps, events = _run(tmp_path, accept_after=-1, release_ack=True)
    assert result.returncode == 1
    assert (
        "never emitted a new exact marker BEAMO_WIPE_RETURN_RESULT_CHECKING"
        " or BEAMO_WIPE_RETURN_RESULT_WORKING" in result.stderr
    )
    assert sleeps == ["0.1"] * 200
    assert events == ["key-down", "key-up", "summary", "screen"]


def test_working_result_is_accepted_when_the_check_finishes_in_the_handler(tmp_path):
    # Main run 44068634926 attempt 1: the guest drew Checking, then reported
    # RETURN_RESULT_WORKING for the one press. That is acceptance.
    result, sleeps, events = _run(
        tmp_path,
        accept_after=2,
        release_ack=True,
        accept_marker="BEAMO_WIPE_RETURN_RESULT_WORKING",
        working_before=1,
    )
    assert result.returncode == 0, result.stderr
    assert "reached new marker BEAMO_WIPE_RETURN_RESULT_WORKING" in result.stderr
    assert sleeps == ["0.1"] * 2
    assert events == [
        "key-down",
        "key-up",
        "await-new BEAMO_WIPE_SCREEN_WORKING",
    ]


def test_earlier_working_results_are_not_acceptance(tmp_path):
    # An older RETURN_RESULT_WORKING count must not release the key early.
    result, sleeps, events = _run(
        tmp_path,
        accept_after=-1,
        release_ack=True,
        accept_marker="BEAMO_WIPE_RETURN_RESULT_WORKING",
        working_before=3,
    )
    assert result.returncode == 1
    assert sleeps == ["0.1"] * 200
    assert events == ["key-down", "key-up", "summary", "screen"]


@pytest.mark.parametrize("marker", ["BEAMO_WIPE_RETURN_RESULT_CHECKING", "BEAMO_WIPE_KEY_RETURN_RELEASED"])
def test_guest_still_emits_the_markers_the_driver_waits_for(marker):
    tk_source = (QEMU.parents[1] / "src/beamo_wipe/ui/tk_wizard.py").read_text(encoding="utf-8")
    if marker == "BEAMO_WIPE_RETURN_RESULT_CHECKING":
        assert 'emit_serial_marker(f"BEAMO_WIPE_RETURN_RESULT_{self.w.screen.name}")' in tk_source
    else:
        assert f'emit_serial_marker("{marker}")' in tk_source


def test_report_journey_starts_the_erase_through_the_release_safe_driver():
    source = QEMU.read_text(encoding="utf-8")
    export = source.split("drive_report_export() {", 1)[1].split("\n}", 1)[0]
    assert 'start_erase_with_return "$label" "$qmp_socket" 20' in export
    assert "ret BEAMO_WIPE_SCREEN_WORKING" not in export
    driver = _function(source, "start_erase_with_return")
    assert driver.count("key-down") == 1
    assert "key-tap" not in driver
