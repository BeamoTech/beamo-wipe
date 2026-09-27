"""Check QEMU marker responsiveness without booting a guest."""

import os
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _function(source: str, name: str) -> str:
    return name + "() {" + source.split(name + "() {", 1)[1].split("\n}", 1)[0] + "\n}"


@pytest.mark.parametrize(
    ("name", "prior", "ready_after", "expected_code", "expected_ticks"),
    [
        ("wait_for_marker", 0, 1, 0, 1),
        ("wait_for_new_marker", 1, 1, 0, 1),
        ("wait_for_marker", 0, 4, 0, 4),
        ("wait_for_new_marker", 1, 5, 1, 4),
    ],
)
def test_marker_polling_keeps_one_second_budget_and_final_recheck(
    tmp_path, name, prior, ready_after, expected_code, expected_ticks
):
    source = (ROOT / "scripts/qemu-verify.sh").read_text(encoding="utf-8")
    sleeps = tmp_path / "sleeps"
    sleeps.touch()
    script = "\n".join(
        (
            _function(source, name),
            'guest_pid() { printf "123\\n"; }',
            "kill() { return 0; }",
            "report_marker_summary() { :; }",
            "wait() { :; }",
            'sleep() { printf "%s\\n" "$1" >> "$MOCK_SLEEPS"; }',
            """marker_count() {
  local ticks
  ticks=$(wc -l < "$MOCK_SLEEPS")
  if (( ticks >= READY_AFTER )); then
    printf '%s\\n' "$((PRIOR + 1))"
  else
    printf '%s\\n' "$PRIOR"
  fi
}""",
            (
                'wait_for_marker bios-marker BEAMO_TEST 1'
                if name == "wait_for_marker"
                else 'wait_for_new_marker bios-marker BEAMO_TEST "$PRIOR" 1'
            ),
        )
    )
    result = subprocess.run(
        ["bash", "-c", script],
        env=dict(
            os.environ,
            MOCK_SLEEPS=str(sleeps),
            PRIOR=str(prior),
            READY_AFTER=str(ready_after),
        ),
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == expected_code, result.stderr
    assert sleeps.read_text().splitlines() == ["0.25"] * expected_ticks


def test_report_completion_uses_the_same_short_poll(tmp_path):
    source = (ROOT / "scripts/qemu-verify.sh").read_text(encoding="utf-8")
    sleeps = tmp_path / "sleeps"
    sleeps.touch()
    script = "\n".join(
        (
            _function(source, "wait_for_report_saved"),
            'guest_pid() { printf "123\\n"; }',
            "kill() { return 0; }",
            "report_marker_summary() { :; }",
            "wait() { :; }",
            'sleep() { printf "%s\\n" "$1" >> "$MOCK_SLEEPS"; }',
            """marker_count() {
  if [[ "$2" == BEAMO_WIPE_REPORT_SAVED && $(wc -l < "$MOCK_SLEEPS") -ge 1 ]]; then
    printf '1\\n'
  else
    printf '0\\n'
  fi
}""",
            "wait_for_report_saved bios-marker",
        )
    )
    result = subprocess.run(
        ["bash", "-c", script],
        env=dict(os.environ, MOCK_SLEEPS=str(sleeps)),
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr
    assert sleeps.read_text().splitlines() == ["0.25"]


@pytest.mark.parametrize(
    ("ready_after", "expected_code", "expected_ticks", "expected_key_ups"),
    [(1, 0, 1, [0]), (81, 1, 80, [0, 16, 36])],
)
def test_key_release_ack_keeps_retry_timing_and_twenty_second_budget(
    tmp_path, ready_after, expected_code, expected_ticks, expected_key_ups
):
    source = (ROOT / "scripts/qemu-verify.sh").read_text(encoding="utf-8")
    sleeps = tmp_path / "sleeps"
    events = tmp_path / "events"
    sleeps.touch()
    script = "\n".join(
        (
            _function(source, "send_key_for_marker"),
            'sleep() { printf "%s\\n" "$1" >> "$MOCK_SLEEPS"; }',
            """marker_count() {
  if [[ "$2" == BEAMO_WIPE_KEY_RETURN_RELEASED &&
        $(wc -l < "$MOCK_SLEEPS") -ge $READY_AFTER ]]; then
    printf '1\\n'
  else
    printf '0\\n'
  fi
}""",
            """qmp_request() {
  if [[ "$2" == key-up ]]; then
    printf '%s\\n' "$(wc -l < "$MOCK_SLEEPS")" >> "$MOCK_EVENTS"
  fi
}""",
            """wait_for_new_marker() {
  [[ "$2" != BEAMO_WIPE_KEY_RETURN_RELEASED ]]
}""",
            "send_key_for_marker bios-marker /tmp/mock-qmp ret BEAMO_TEST 1",
        )
    )
    result = subprocess.run(
        ["bash", "-c", script],
        env=dict(
            os.environ,
            MOCK_SLEEPS=str(sleeps),
            MOCK_EVENTS=str(events),
            READY_AFTER=str(ready_after),
        ),
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == expected_code, result.stderr
    assert sleeps.read_text().splitlines() == ["0.25"] * expected_ticks
    assert [int(value) for value in events.read_text().splitlines()] == expected_key_ups
