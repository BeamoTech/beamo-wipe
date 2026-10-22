# Beamo Wipe: seventeenth comprehensive local audit

CI evidence path and file-identity defects are repaired from baseline
`f994e2cf2c1db5365e9cfc4c05ac893e003884bc` on branch
`fix/safety-audit-20261019`. Audit date: 2026-10-21 UTC.

## Repairs

- The CI gate validated its evidence directory once, closed that descriptor,
  and later created its log, JUnit files, and receipt through the pathname. A
  directory replacement after validation could redirect evidence to a new
  directory. The gate now holds one no-follow directory descriptor for its
  full lifetime, creates and reads files relative to it, verifies the pathname
  still names that directory, and gives the child a descriptor-bound JUnit
  path. Explicit pytest JUnit arguments are rebound to the same location.
- Receipt loading, timing summaries, package inventory collection, and final
  manifest evidence now operate on stable regular inodes under a pinned
  directory. Reads are bounded and repeated, complete metadata and the final
  name are checked, hard links are rejected, output creation is exclusive and
  verified after synchronization, and directory listings must remain stable.
  Finalization preserves its public receipt-verifier contract and then repeats
  the verification on the descriptor-bound snapshot before consuming the
  package inventory.
- Mounted-image inventory and copied QEMU evidence no longer accept a linked
  parent or multiply linked file. Mounted inputs use no-follow directory walks
  and stable bounded reads; QEMU evidence retains its directory and file
  identity checks while also requiring single-link regular files.

No detected replacement is deleted on failure. That avoids removing a file
owned by a concurrent writer. Existing evidence remains a hard failure, so the
immutable evidence-output contract is unchanged.

## Reproduction and regression evidence

The new regression module was replayed against an archived exact baseline
tree. Baseline produced **13 intended failures and zero errors/skips**; the
current tree passes all 13. Cases cover linked output parents, evidence
directory replacement after validation and during the child process,
descriptor-bound JUnit output, hard-linked logs, JUnit reports, receipts,
mounted-image inputs and QEMU files, plus linked QEMU and inventory parents.
Only ordinary temporary files and directories were used. The baseline JUnit
SHA-256 is
`fbdc04a1881aaa316d2c0f611596c4655be43ce33d95558bc585bfa018a07d4e`.

The final focused run passes **224 tests**: 13 new regressions and 211 adjacent
CI runner, receipt, JUnit, inventory, QEMU evidence, manifest, and publisher
checks. Its JUnit SHA-256 is
`dcd0aca615e9a6635b8638f1bf538d23bb6b288aac53e1895bf970535a57934c`.

The exact-source suite ran as UID 1000 in a network-disabled container with
fake disks, dry-run/demo mode, the native inventory override unset, an
executable tmpfs, a private D-Bus session, and Xvfb display `:200` at
1600×1000/72 DPI. Warnings were errors. Result: **12,106 passed, 27 skipped,
0 failed, 0 errors** from 12,133 selected tests in 1,287.312 seconds. Two
live-config tests were deselected because the gitignored
`packaging/live/config/{bootstrap,binary}` outputs are absent. The JUnit
SHA-256 is
`3fda8bd29c925007e6bf27c1a604c235d686964e861a8940e8dd0cb6d2d43388`.

The 27 skips retain the prior environment boundaries: 12 manufacturing-ISO
cases, nine unavailable pinned-browser cases, four unreachable Microsoft
source checks, one unavailable gcloud check, and one missing live-build config
case. All isolated-X11 tests executed.

An earlier broad run exposed one compatibility issue in the finalizer's public
receipt-verifier checkpoint. The final implementation preserves that call,
then independently compares it with the pinned snapshot. The 12 affected
finalization tests passed before the final complete run above.

Compilation, Ruff and security selections, formatting, mypy over 52 modules,
ShellCheck, and the private fail-open mutation gate pass. The existing
TODO-pattern message remains informational. Go 1.26.8 race tests and vet pass;
the firmware parser completes 350,000 fuzz executions; Windows and both macOS
architectures cross-compile.

Fresh Windows and Linux desktop launchers were built and verified against
their manifest. Both are executable, the Windows artifact begins with `MZ`,
and the Linux artifact begins with ELF magic. The Linux `--version` path exits
0 and reports version 0.2.13, baseline commit `f994e2cf...`, and `dirty=true`.
Observed artifact SHA-256 values were:

- Linux: `7eaa49684fd58d5bbb1349530ef2b088a2fc633984e0738fc8c8eaecf40b97d4`
- Windows: `02aaef6cdd65d13da5bf20cea547c0fbb48dab7d9ccc18b2e416b34364c38928`
- Manifest: `d2645c5cf945c363dce451fee9c2188fd7e1413e35767c7e406d5ce3db9451b5`

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
