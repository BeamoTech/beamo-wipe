# Design record: why 37 tests fail on the Ubuntu 26.04 development host

> **Status: FINDINGS — no product or test change made or proposed for
> adoption here.** Prepared 2026-11-25 by Claude (Opus 5.5) on the Linux host
> `/home/beamo/dev/BeamoTech/beamo-wipe` (Ubuntu 26.04.1, kernel
> 7.0.0-30, Python 3.14.4). Inputs:
> - the full local suite of 2026-11-25 on main `9ae7f8cf` and on
>   `safety/gtk-help-review-hold-20261124` `4e07d7ef` (BW-138-GTK-HOLD);
> - focused reruns of every failing test;
> - `scripts/ci-hosted.sh` (`install_test_deps`).
>
> **Scope.** The 31 failed and 6 errored test results that were identical on
> both trees. Nothing here touches disk selection, nwipe flags or any safety
> rule.

## 1. Summary for the owner (plain English)

1. None of the 37 is a product defect, and none is caused by the GTK
   review-hold change: every one fails on unmodified main too.
2. 24 came from how I ran the suite on this machine. I moved pytest's
   temporary folder off `/tmp` to avoid a disk quota, and I exposed the
   system Python packages to a private environment. Undone, all 24 pass.
3. 10 came from tools that differ from what CI installs: a newer pytest
   than CI pins, and tools missing from the system `python3`. With CI's
   pinned tools all 10 pass. One more (the Orca speech test) needs packages
   that were not installed here.
4. 1 is a real difference in Python 3.14. A developer-tool test assumes
   Python 3.11's JSON behaviour. Developer tooling only; it never runs on a
   customer PC.
5. 1 is not a failure at all: a test deliberately runs a broken nested test
   and its output reached the log.

## 2. How the suite was run (facts)

| Item | Value |
|---|---|
| Command | `dbus-run-session -- xvfb-run -a -s "-screen 0 1600x1000x24 -dpi 72" python -m pytest -q -rA --continue-on-collection-errors` |
| Python environment | Scratch venv (pytest 9.2.0, cryptography 50.0.1, qrcode 8.2) plus `PYTHONPATH=/usr/lib/python3/dist-packages` for system `gi` and `tkinter` |
| System packages | `python3-gi`, `gir1.2-gtk-3.0`, `xvfb`, `python3-tk` (installed 2026-11-25 with the owner's OK); no `x11-utils`, Orca, `python3-pyatspi`, `python3-qrcode` or system pytest |
| Temp folders | `--basetemp=/home/beamo/.cache/beamo-wipe-fullsuite-20261125/tmp-{branch,main}`, after an earlier run's logs were cut off by the `/tmp` tmpfs per-user quota |
| Result, both trees | 31 failed + 6 errors, identical test IDs; branch +9 passed (the new GTK-hold tests) |
| CI for comparison | Debian bookworm image; `install_test_deps` apt-installs the test packages (including `x11-utils`, Orca, `python3-pyatspi`, `python3-qrcode`) and pip-installs `pytest==9.0.3`, `cryptography==50.0.1` and `playwright==1.63.0` into the **system** `python3`; default pytest temp under `/tmp` |

## 3. Findings by cause

| # | Cause | Count | Tests | Mechanism | Evidence |
|---|---|---|---|---|---|
| A | **Harness: temp folder on `/home`** | 22 | `test_audit_20260905_wizard::test_working_plain_console_eof_cancels_before_leaving` (6), `test_cancel_observed_exit::test_cancel_preserves_observed_exit_and_persisted_signal` (10), `test_recovery_boot_alias_pass3_20261019::test_fake_kiosk_confirmation_can_arm_only_unrelated_target` (3), `test_discover::test_discovery_boot_is_the_identified_usb_not_a_protected_mount`, `test_evidence::test_schema_covers_required_fields`, `test_session_tmpfs_pass17_ui::test_production_journal_accepts_genuine_tmpfs` | The product requires logs and recovery state on the `/tmp` filesystem (AGENTS.md: logs under `/tmp/beamo-wipe/`). Fixtures build these paths from `tmp_path`. Under `/home` the safety layer refuses: "Log directory must be on the /tmp filesystem", "Recovery directory is not on the volatile filesystem". The erase never starts, so the screen stays Last chance instead of Working; the evidence test finds `/home/` in its output | All 22 pass when rerun with the default `/tmp` temp folder. With `--basetemp` on `/home` they fail again. This is the safety rule working, not a defect |
| A′ | **Harness: `PYTHONPATH` override** | 2 | `test_gtk_dependency_handling::test_dependency_boundary_preserves_non_dependency_failures[missing]`, `[missing-reversed]` | The test simulates missing GTK bindings in a child Python (`sys.executable`). `PYTHONPATH=/usr/lib/python3/dist-packages` puts the real `gi` ahead of the simulation, so the child reports a failure instead of the expected skip | Both pass in the same venv without the override, and in a `--system-site-packages` venv (the CI-like layout) |
| B | **Tooling: pytest 9.2.0 vs CI pin 9.0.3** | 8 | `test_serial_marker_drops` (6 setup errors), `test_accountable_audit_2026_09_03::test_serial_marker_is_bounded_and_written_to_character_device`, `test_external_boundaries::test_default_log_dir_wrong_owner_or_perms` | These tests monkeypatch the process-wide `os.fstat` with stand-ins that have no `st_size`. pytest 9.2.0's output capture (`_pytest/capture.py`, `snap()`) now calls `os.fstat(fd).st_size`, so it hits the stand-in | Same 8 tests: pytest 9.2.0 errors; pytest 9.0.3 (CI pin) 8/8 pass, nothing else changed |
| C | **Tooling: system `python3` without CI's packages** | 2 | `test_ci_preview_js_gate_pass5::test_hosted_preview_rejects_a_javascript_syntax_failure`, `test_iso_bundle_ownership_pass8::test_iso_success_survives_backup_cleanup_failure` | They spawn `bash scripts/ci-hosted.sh preview` or `sh`, which call bare `python3`. On this host that is the system Python, without `qrcode` / `pytest` (`ModuleNotFoundError`). CI installs both into the system `python3` | Both pass when a venv holding the CI pins comes first on `PATH` |
| D | **Missing packages: screen-reader stack** | 1 | `test_accessible_runtime::test_orca_announces_every_result` | "The Linux accessibility tests require xdpyinfo (install xvfb and x11-utils)". CI also installs Orca, `python3-pyatspi`, `at-spi2-core` and speech-dispatcher | Not rerun with those packages; installing them needs the owner's OK |
| E | **Python 3.14 behaviour** | 1 | `developer_tests/test_doctor_decode_depth_pass12_20261021::test_doctor_probe_json_decode_depth[deep-object-desktop]` | The test feeds `dev.py doctor` probe JSON nested 20,000 deep and expects "blocked" via `RecursionError`. On Python 3.14.4, `json.loads` decodes that depth without `RecursionError`, measured here for both the array and object payloads. For `desktop` the doctor checks no modules, so a valid version plus a dict is "ok" (exit 0). The other 19 cases still block because the payload has the wrong type or lacks required module flags | Reproduced in both venvs. Python 3.11 (bookworm) raises `RecursionError` at this depth, which is why CI passes. The cause is attributed to 3.14's change in C-level recursion protection; that attribution is inferred, not traced in CPython source |
| F | **Not a failure** | 1 | Nested `…/test_pipeline_rejects_broken_s0/test_safe_fixture.py::test_safe_fixture` | `tests/test_blacksmith_ci.py::test_pipeline_rejects_broken_safe_test_then_accepts_repaired_test` deliberately runs a broken nested test; with `-rA` the inner `FAILED` line reached the outer log | The outer test PASSED on both trees |

Total: 22 + 2 + 8 + 2 + 1 + 1 + 1 = 37.

## 4. What this means

- **The GTK review-hold result stands.** The branch adds no failure, and all
  nine new tests pass. See BW-138-GTK-HOLD in
  `.ai/memory/unfinished-work.md`.
- **A host run needs CI-like conditions to be clean:**
  - pytest's default temp folder under `/tmp`, with quota headroom: about
    2.1 GB per full run;
  - the CI pins in a `--system-site-packages` venv, first on `PATH`, and no
    `PYTHONPATH` override;
  - `x11-utils` and the Orca stack, for the accessibility test.
- **Latent fragility (B):** raising the pinned pytest to 9.2 would break
  eight tests in CI as well. The stand-ins should carry `st_size`, or the
  tests should patch `diagnostics.os` without replacing the process-wide
  `os.fstat`.
- **Portability (E):** the decode-depth test assumes Python ≤3.13
  behaviour. `pyproject.toml` allows Python ≥3.10, so a developer on 3.14
  sees one failing developer test. The doctor's own behaviour on 3.14 is
  arguably correct: the input is valid JSON.

## 5. Follow-ups (none started; none Jack-gated unless marked)

| ID | Item | Next action |
|---|---|---|
| BW-HOST-PYTEST-FSTAT | Make the eight `os.fstat` stand-ins pytest-9.2-safe | **DONE LOCALLY 2026-11-25** as `e7f80384` on `test/host-pytest-fstat-20261125` (not pushed). Each stand-in now fakes only the test's own fd, or returns a real `os.stat_result` with only `st_uid` changed. A fake `st_size` was rejected: pytest would read its capture file as empty and drop captured output. 8/8 pass on pytest 9.2.0 and 9.0.3, and all 8 fail on both when the product checks they guard are broken. Remaining: push, PR and the hosted gate (Jack) |
| BW-HOST-JSON-DEPTH | Make the decode-depth test version-aware | **DONE LOCALLY 2026-11-25** as `b17b77c6` on `test/host-json-depth-20261125` (not pushed; test only, `dev.py` unchanged). The deep-payload expectation follows this interpreter's `json.loads`, and Python ≤3.11 must still raise and block. A new forced-recursion case covers the doctor's `RecursionError` handling on every version. 24/24 pass on 3.14.4 (pytest 9.2.0 and 9.0.3) and under a simulated-3.11 decoder; removing the `RecursionError` handling fails 4 cases. A real 3.11–3.13 run is not done (none on this host). Remaining: push, PR and the hosted gate (Jack) |
| BW-HOST-RUNBOOK | Document a clean local run on this host | **DONE LOCALLY 2026-11-25** on `docs/records-20261124` (not pushed): `docs/local-test-runbook-ubuntu.md`, linked from `docs/development.md` (Troubleshooting). It covers the `/tmp` quota and temp folder, the CI pins on `PATH`, no `PYTHONPATH`, a `--system-site-packages` `.venv-linux` for GTK, and the expected host-only failures. A complete full-suite run with its commands has not been done yet |
| BW-HOST-A11Y-PKGS | Run the Orca test locally | **Owner OK needed:** install `x11-utils orca python3-pyatspi at-spi2-core speech-dispatcher speech-dispatcher-espeak-ng` |

## 6. Evidence

- Logs: `/home/beamo/.cache/beamo-wipe-fullsuite-20261125/`:
  - `branch.txt`, `main.txt` and the per-test `branch-res.txt`,
    `main-res.txt`;
  - `diag/rerun.txt` (failing set, `/home` temp);
  - `diag/rerun-tmp.txt` (default `/tmp` temp);
  - `diag/rerun-ci.txt` (CI pins first on `PATH`).
- These files are local to this host and not committed.
