# Beamo Wipe: fourteenth comprehensive local audit

Eight related integrity and lifecycle defects are repaired from baseline
`30e91206af8d176e7c8881dd0d5ed91c52f11168` on branch
`fix/safety-audit-20261019`. Audit date: 2026-10-21 UTC.

## Repairs

- Production `/dev/disk/by-*` boot evidence now requires a stable symlink,
  repeated full resolution, and matching block-device metadata snapshots.
- The exact nwipe ELF descriptor accepted by the version probe is retained
  through launch. Active logs must remain owner-only mode `0600`, single-link,
  and bound to their launch inode through progress and terminal reads.
- Cached desktop artifacts and release inputs are read twice and bound to
  complete descriptor and pathname metadata. The Linux desktop media digest
  also includes change time in its final handoff snapshot.
- Evidence uses cryptographic staging names and Linux
  `renameat2(RENAME_NOREPLACE)`. Interrupted exact sidecar/data states are
  resumable; cleanup never removes a concurrently replaced final pathname.
- Report readback verifies each private member twice against its named inode.
  VFAT report mounts synthesize files as `0600` and directories as `0700` on
  both write and readback mounts.
- Release outputs use Linux no-replace/exchange publication. A verified prior
  output is retained under a cryptographic hidden name, and a concurrent
  foreign replacement is atomically restored to its original pathname.
- The embedded ISO prior-bundle reader now performs repeated reads and full
  metadata checks.
- Audio readiness restarts PulseAudio before probing. Cancellation during
  `Popen` construction terminates and reaps the newly owned child.

The existing syscall-coupled tests were migrated to the new atomic contracts.
Their refusal and ownership guarantees remain; a separate warning-gate fix
closes one test source file correctly.

## Reproduction and regression evidence

The exact final Python regression modules were replayed against an archived,
read-only baseline tree. The baseline produced **83 intended failures and 15
positive controls** across 98 cases. The current tree passes all 98. The Go
media handoff regression produced one failing mutation leaf and one passing
control on baseline; both pass after repair.

The final frozen-source parent suite used an unprivileged, network-disabled
container; fake disks; `BEAMO_WIPE_DRY_RUN=1`; native inventory unset; an
executable tmpfs; a dedicated Xvfb display `:200` at 1600×1000/72 DPI; and
warnings as errors. Result: **12,065 passed, 27 skipped, 0 failed, 0 errors**
from 12,092 selected cases. Two live-config tests were deselected because the
gitignored `packaging/live/config/{bootstrap,binary}` outputs are absent.

The 27 skips are explicit environment limits: 12 manufacturing-ISO cases,
nine unavailable pinned-browser cases, four unreachable Microsoft-source
checks, one unavailable gcloud check, and one missing live-build config case.
All 405 isolated-X11 tests executed rather than skipping.

Compilation, full Ruff and security selections, formatting, mypy over 52
modules, ShellCheck, and shell syntax pass. Go race tests and vet pass; Windows
and macOS test binaries cross-compile. Focused release publication tests pass
after the final typing fix.

Fresh Windows and Linux desktop launchers were built with Go 1.26.8 and
verified against their manifest. The Linux artifact executed its `--version`
path and reported version 0.2.13, the baseline commit, and `dirty=true`.
Observed artifact SHA-256 values were:

- Linux: `29af764ea12e5e22db5bb52b1dc0f25cc00301bfff8c742824774e6d54a72b02`
- Windows: `e74d00004331ce20363a1949dae00235fe1f79916cd31fe24eac5f4a7b00212f`

Web, embedded JavaScript, console, and helper previews pass. The actual fake
Tk preview was captured on the private 72-DPI display, visually inspected for
clipping and required warning/guidance/focus content, and closed through its
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
