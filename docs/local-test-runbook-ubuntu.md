# Clean local test run on the Ubuntu 26.04 / Python 3.14 host

This page explains how to run the full local suite on the Linux development
host (Ubuntu 26.04.1, Python 3.14.4) so that its result is comparable with
CI's Debian bookworm / Python 3.11 gate. It is based on the 2026-11-25
baseline in
[`decisions/local-test-baseline-ubuntu-26-04.md`](decisions/local-test-baseline-ubuntu-26-04.md)
(BW-HOST-RUNBOOK). A local run is never hosted CI and never qualification
evidence; see [development.md](development.md) and [ci.md](ci.md).

## 1. Before you start

- Work in your own worktree, and record `git rev-parse HEAD`. Each worktree
  needs its own venv; do not reuse one from another checkout or OS.
- Check `/tmp` headroom: `df -h /tmp`. On this host, `/tmp` is a 7.5 GB
  tmpfs with a **per-user quota** (`usrquota`), shared by every agent running
  as the same user. One full suite uses about **2.1 GB** of pytest temp under
  `/tmp/pytest-of-$USER/`. Two suites side by side need about 4.2 GB.
- If space is short, remove only `/tmp/pytest-of-$USER/pytest-N` folders that
  you can show are yours and idle: match the test names, the timestamps and
  `lsof +D`. Another project's pytest may be using the same parent folder.
  Never delete a folder that is in use.
- Keep logs off `/tmp` (for example under `~/.cache/…`). On 2026-11-25 a
  quota hit truncated logs kept in `/tmp`, and that run had to be repeated.

## 2. Keep pytest's temp folder on `/tmp` (do not use `--basetemp`)

The product refuses log and recovery folders that are not on the `/tmp`
filesystem (AGENTS.md: logs under `/tmp/beamo-wipe/`). Many fixtures derive
those folders from `tmp_path`. With `--basetemp` on `/home`, 22 tests fail
by design:
- plain-console EOF (6);
- cancel/observed exit (10);
- recovery boot alias (3);
- `test_discover`, `test_evidence` and `test_session_tmpfs`.

Use pytest's default temp location.

## 3. Use CI's pins, first on `PATH`, without `PYTHONPATH`

CI installs `pytest==9.0.3`, `cryptography==50.0.1` and `qrcode` (Debian
`python3-qrcode`) into the system `python3`, which also has `python3-gi` and
`python3-tk`. Two rules follow on this host:

- **Pin pytest to 9.0.3.** Unpinned pip gives 9.2.x. On 9.2, pytest's output
  capture reads `os.fstat(fd).st_size`, and eight tests replace `os.fstat`
  process-wide, giving 6 errors and 2 failures. This is fixed by `e7f80384`
  (`test/host-pytest-fstat-20261125`, not yet on main); until it lands, use
  9.0.3.
- **Put the venv's `bin` first on `PATH`.** Some tests spawn bare `python3` or
  `ci-hosted.sh`. The system `python3` here has no pytest or qrcode, so
  `test_ci_preview_js_gate_pass5` and `test_iso_bundle_ownership_pass8` fail.
  `dev.py test` already adds its venv to the child `PATH`.
- **Do not set `PYTHONPATH=/usr/lib/python3/dist-packages`** to reach system
  GTK. It defeats the missing-GTK simulation in `test_gtk_dependency_handling`
  (2 failures). Give the venv system site packages instead (§4).

## 4. Recommended commands

Standard route (GTK runtime tests skip, because a plain venv cannot see
`gi`):

```bash
python3 dev.py setup        # .venv-linux with the CI pins (pip install)
python3 dev.py doctor --for test
python3 dev.py test         # dbus-run-session + xvfb-run at 72 DPI, venv first on PATH
```

GTK-inclusive route (also runs the GTK popover and runtime tests). Create
the venv with system site packages before `setup`; `setup` then reuses it.
Use it only when `.venv-linux` does not already exist:

```bash
python3 -m venv --system-site-packages .venv-linux
python3 dev.py setup
python3 dev.py test
```

This needs the system packages `python3-gi`, `gir1.2-gtk-3.0`, `xvfb` and
`python3-tk`; they were installed on this host on 2026-11-25. With system
site packages visible, pip reports that the system `pyopenssl` 25.3.0 wants
`cryptography<47`. The suite pins 50.0.1. This was seen as a warning only;
the affected tests were not re-checked against it.

Equivalent manual form (the form used for the 2026-11-25 checks):

```bash
python3 -m venv --system-site-packages ~/.cache/beamo-wipe-venv-ci
~/.cache/beamo-wipe-venv-ci/bin/pip install 'pytest==9.0.3' 'cryptography==50.0.1' 'qrcode==8.2'
PATH=~/.cache/beamo-wipe-venv-ci/bin:$PATH BEAMO_WIPE_DRY_RUN=1 \
  dbus-run-session -- xvfb-run -a -s "-screen 0 1600x1000x24 -dpi 72" \
  python3 -m pytest -q -rA
```

Do not run two full suites side by side unless `/tmp` has room for both.
Under load, the plain-console flush timing tests can fail once; rerun them
alone before treating that as a regression. On 2026-11-25 they passed 3/3 in
isolation.

## 5. Results to expect on this host (main `9ae7f8cf`)

| Remaining failure | Why | Status |
|---|---|---|
| `test_accessible_runtime::test_orca_announces_every_result` | Needs `xdpyinfo` (`x11-utils`) and the Orca/AT-SPI/speech stack that CI installs | Not installed; installing it needs the owner's OK (BW-HOST-A11Y-PKGS) |
| `developer_tests/test_doctor_decode_depth_pass12_20261021.py::…[deep-object-desktop]` | Python 3.14 `json.loads` decodes 20,000-deep JSON without `RecursionError`; the test expects 3.11's blocked result | Fixed by `b17b77c6` (`test/host-json-depth-20261125`, not yet on main) |
| A `FAILED …/test_pipeline_rejects_broken_s0/test_safe_fixture.py` line | Output of a deliberately broken nested test; the outer `test_blacksmith_ci.py::test_pipeline_rejects_broken_safe_test_then_accepts_repaired_test` must show PASSED | Not a failure: check the outer test |

Any other failure is a real lead: keep the log and the exact SHA, and rerun
the case alone before editing (development.md, Troubleshooting).

**Verified / not verified.**
- Verified on 2026-11-25: each rule above was checked by a rerun that
  changed only that factor (design record §3), and the two fixes pass on
  this host.
- Not yet verified: a complete full-suite run with the recommended commands.
  The expected-result table is derived from those targeted reruns.

## 6. Reading the summary

- With `-rA`, also count per-test `PASSED`/`FAILED`/`ERROR` lines. A nested
  pytest run inside a test can print its own summary line last.
- Skips are not passes. On this host, Orca and the native/physical checks
  stay skipped or failing, and hosted CI remains the qualification gate.
