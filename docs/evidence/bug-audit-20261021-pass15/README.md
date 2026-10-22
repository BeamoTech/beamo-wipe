# Beamo Wipe: fifteenth comprehensive local audit

Two defects are repaired from baseline
`0163594b71bf57ca7be82b0c9b65605bd3c3fc79` on branch
`fix/safety-audit-20261019`. Audit date: 2026-10-21 UTC.

## Repairs

- Startup discovery now waits behind an admission gate until
  `threading.Thread.start()` has returned successfully. If native thread start
  creates the worker and then raises `KeyboardInterrupt`, `SystemExit`, or
  another exception, the rejected worker wakes only to retire; it cannot run
  discovery behind a closed splash or a blocked support route. The synchronous
  builder hook used by the GTK presenter tests remains synchronous.
- Build-identity test publication now walks every parent through no-follow
  directory descriptors, writes to a cryptographically named regular file,
  verifies exact bytes and complete metadata twice, atomically replaces only
  the destination directory entry, synchronizes it, and verifies that the
  parent pathname still names the opened directory. A planted leaf link is
  replaced without touching its target, while a linked parent is refused.
  Failed exact staging files are retained because POSIX has no atomic
  unlink-if-same-inode operation; cleanup therefore cannot delete a concurrent
  replacement.

During adjacent validation, the first startup-gate placement made the private
synchronous builder hook wait for thread admission. That interaction was
caught by the existing GTK cleanup suite before final validation. Admission
was moved into a dedicated native-thread entry point; all 47 combined startup
lifecycle cases then passed.

## Reproduction and regression evidence

The two final regression modules were replayed against an archived baseline
tree. Baseline produced **8 intended failures and 1 positive control**; the
current tree passes all 9. The failures cover post-start launch interruption,
an acceptance wake interrupted after releasing the worker, leaf and parent
symlinks, in-place overwrite, post-rename replacement, and unsafe failure
cleanup. Only fake callbacks and regular temporary files were used.

The final source suite ran as UID 1000 in a network-disabled container with
fake disks, dry-run/demo mode, the native inventory override unset, an
executable tmpfs, a private D-Bus session, and Xvfb display `:200` at
1600×1000/72 DPI. Warnings were errors. Result: **12,074 passed, 27 skipped,
0 failed, 0 errors** from 12,101 selected tests in 1,252.603 seconds. Two
live-config tests were deselected because the gitignored
`packaging/live/config/{bootstrap,binary}` outputs are absent. The JUnit
SHA-256 is
`2d9c58eb3603f078afedaa659d17fc78ae5ac7d2267f4792075ff1ead24edbbc`;
the mandatory GTK result guard passes.

The 27 skips retain the prior environment boundaries: 12 manufacturing-ISO
cases, nine unavailable pinned-browser cases, four unreachable Microsoft
source checks, one unavailable gcloud check, and one missing live-build config
case. All isolated-X11 tests executed.

Compilation, full Ruff and security selections, formatting, mypy over 52
modules, ShellCheck, and the private fail-open mutation gate pass. The existing
TODO-pattern message remains informational. Go 1.26.8 race tests and vet pass;
the firmware parser completes 350,000 fuzz executions; Windows and macOS test
binaries cross-compile.

Fresh Windows and Linux desktop launchers were built and verified against
their manifest. Both are executable, the Windows artifact begins with `MZ`,
and the Linux artifact begins with ELF magic. The Linux `--version` path exits
0 and reports version 0.2.13, baseline commit `0163594b...`, and `dirty=true`.
Observed artifact SHA-256 values were:

- Linux: `800c423ae7d7c023a8ca33b7e18666ab4911622a853a976e0a52a66087ac7837`
- Windows: `c261361a74bc2d05b33567bee321c945ffc9e78d27a3a802b498502e2cd4fc64`

Web, embedded JavaScript, console, and helper previews pass. The actual fake
Tk preview was captured on private display `:250` at 72 DPI, visually inspected
for clipping, warning/guidance content, and focus, and closed through its
registered `WM_DELETE_WINDOW` callback with exit 0. See the
[unedited preview](preview/actual-preview-72dpi.png) and
[capture receipt](preview/actual-preview.json).

## Limits

No actual nwipe engine, block device, mount, firmware, power, physical USB,
guest, hosted CI, ISO/QEMU, or native Windows execution occurred. Cross-builds
do not establish native acceptance. Exact-source ISO/KVM, native Windows,
firmware, physical-media, and reconnect qualification remain open for an
authorized isolated worker or eligible physical session.

No remote write, pull request, merge, deployment, or release occurred.
Publication remains blocked by the earlier automatic approval review that
rejected exporting operational-backlog metadata as internal data.
