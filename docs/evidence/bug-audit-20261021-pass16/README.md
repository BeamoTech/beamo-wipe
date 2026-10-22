# Beamo Wipe: sixteenth comprehensive local audit

Two related file-boundary defects are repaired from baseline
`f3ff0b52b6d83f8b52e76b46e9293552d6fb003c` on branch
`fix/safety-audit-20261019`. Audit date: 2026-10-21 UTC.

## Repairs

- Release-signing CLI inputs previously protected only the final path
  component. A linked parent could redirect the manifest, key, signature, or
  registry read outside the requested directory, and replacing the leaf after
  it opened went undetected. Inputs now walk and hold every POSIX parent through
  no-follow directory descriptors, reject multiply linked files, read the
  opened descriptor twice within its size bound, compare complete metadata to
  the final named entry, and verify that the requested parent still names the
  opened directory.
- Key and detached-signature outputs had the same linked-parent weakness and
  did not verify the bytes or inode that remained at the requested name after
  synchronization. New outputs are created through the held directory,
  written completely, synchronized, read back repeatedly, checked for exact
  mode, size, link count, metadata, and payload, then checked again after
  directory synchronization and parent-path rebinding. Evidence CLI inputs
  now use this reader; its receipt and package-inventory outputs use the same
  exclusive, verified writer instead of following or truncating an existing
  link.

The failure path deliberately leaves an output that was changed concurrently.
Deleting by pathname after detecting replacement could remove another
writer's file. An existing output remains an explicit `FileExistsError`, so
receipts, keys, and sidecars retain their immutable-output contract.

## Reproduction and regression evidence

The two final regression modules were replayed against an archived exact
baseline tree. Baseline produced **17 intended failures and 2 positive
controls**; the current tree passes all 19. The failures cover linked parents,
hard-linked inputs, leaf and parent replacement, same-size in-place rewrite,
post-sync rewrite, truncation, permission change, extra hard link, symlink
replacement, and evidence output redirection. Only ordinary temporary files
and directories were used.

The final focused run passes **229 tests**: all 19 new cases plus 210 adjacent
signing, publisher, download-verification, receipt, JUnit, package-inventory,
and release-metadata checks. Its JUnit SHA-256 is
`63d58cd6aa65c564b9dc2da64d1011d6cca054ac05838146a9c68d15a3b44721`.
The archived-baseline JUnit SHA-256 is
`5291b0e76fc9f4fad4a5bb275f2f8b397877f2d27f9034a313f5b60d5541aa74`.

The source suite ran as UID 1000 in a network-disabled container with fake
disks, dry-run/demo mode, the native inventory override unset, an executable
tmpfs, a private D-Bus session, and Xvfb display `:200` at 1600×1000/72 DPI.
Warnings were errors. Result: **12,093 passed, 27 skipped, 0 failed, 0
errors** from 12,120 selected tests in 1,263.781 seconds. Two live-config tests
were deselected because the gitignored
`packaging/live/config/{bootstrap,binary}` outputs are absent. The JUnit
SHA-256 is
`27f44f5976da186c1136fdbfc857a095fccf4e0fd09c620c1b4502480e0f63bb`.

The 27 skips retain the prior environment boundaries: 12 manufacturing-ISO
cases, nine unavailable pinned-browser cases, four unreachable Microsoft
source checks, one unavailable gcloud check, and one missing live-build config
case. All isolated-X11 tests executed.

Compilation, Ruff and security selections, formatting, mypy over 52 modules,
ShellCheck, and the private fail-open mutation gate pass. The existing
TODO-pattern message remains informational. Go 1.26.8 race tests and vet pass;
the firmware parser completes 350,000 fuzz executions; Windows and both macOS
architectures cross-compile.

Fresh Windows and Linux desktop launchers were built and verified against
their manifest. Both are executable, the Windows artifact begins with `MZ`,
and the Linux artifact begins with ELF magic. The Linux `--version` path exits
0 and reports version 0.2.13, baseline commit `f3ff0b52...`, and `dirty=true`.
Observed artifact SHA-256 values were:

- Linux: `e05df5df3cd169db2e946cfab29efd71c309b6f9bd75ed94be353a705eccb12d`
- Windows: `b3c04fee3947d6eeb05d2a5ce2e2cdb63c9b737405694f9d5320d53b8714022f`

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
