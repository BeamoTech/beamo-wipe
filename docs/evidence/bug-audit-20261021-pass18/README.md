# Beamo Wipe: eighteenth comprehensive local audit

Release-bundle path and snapshot defects are repaired from baseline
`7d261c6f1167de6a10f8d7d8b11c4d664af5be68` on branch
`fix/safety-audit-20261019`. Audit date: 2026-10-21 UTC.

## Repairs

- Release manifest, ISO, and checksum-sidecar reads rejected a linked final
  filename but still followed a linked ancestor. A caller could therefore
  verify a release bundle through a redirected parent. Every parent component
  is now opened without following links; the leaf is opened relative to that
  pinned directory and matched to its final requested name.
- Manifest and checksum-sidecar reads are now bounded, repeated, and compared
  across their complete metadata snapshots. ISO hashing checks the opened
  descriptor, the pinned directory entry, and the requested pathname against
  the same metadata. The existing build-time ISO hardlink remains supported,
  while its link count is included in the stable identity.
- Verification retains identities for the manifest, ISO, ISO checksum, and
  manifest checksum. Before returning the exact accepted manifest bytes, it
  reopens all four through link-free parents and requires their file and parent
  identities to match the verified snapshots. Same-byte pathname replacement
  and whole-directory replacement now fail closed.

The generic regular-file opener used by package-inventory loading and prior
manifest-output checks also inherits the link-free parent walk. No detected
replacement is removed or overwritten.

## Reproduction and regression evidence

The seven new regressions were replayed against an archived exact baseline
tree. Baseline produced **7 intended failures and zero errors/skips**; the
current tree passes all seven. Cases cover linked parents, same-byte
replacement of the manifest and ISO after use, replacement of both checksum
sidecars after use, and replacement of the complete release directory. Only
ordinary temporary files and directories were used. The baseline JUnit
SHA-256 is
`9168808aa06dc5867fa0603640aae64e1a9e1c0e0542d945f7df46f58249dd08`;
the fixed-regression JUnit SHA-256 is
`ae3e54d0fc0a2a76dbfc2e5fe859ea682715db1cc9dd46f9555d3152b8d8b6c4`.

The focused release boundary selected 209 tests: **197 passed, 12 existing
manufacturing-ISO cases skipped, zero failed or errored**. It covers manifest
generation and verification, publication, signing, ISO mutation, finalization,
checksums, CI evidence, package inventory, and the new snapshot regressions.
Its JUnit SHA-256 is
`78424a9a33b91fa05869143a9cc44df8ad5f273ad16b7c7c105397867175e1ac`.

The exact-source suite ran as UID 1000 in a network-disabled container with
fake disks, dry-run/demo mode, the native inventory override unset, an
executable tmpfs, a private D-Bus session, and Xvfb display `:200` at
1600×1000/72 DPI. Warnings were errors. Result: **12,113 passed, 27 skipped,
0 failed, 0 errors** from 12,140 selected tests in 1,267.825 seconds. Two
live-config tests were deselected because the gitignored
`packaging/live/config/{bootstrap,binary}` outputs are absent. The JUnit
SHA-256 is
`a9e2b1342b60a698992c036b94dfc7edf1e5f641afda9a5cc229ea2e2d2aa470`.

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
0 and reports version 0.2.13, baseline commit `7d261c6f...`, and `dirty=true`.
Observed artifact SHA-256 values were:

- Linux: `56548a195cbdb243e8e75bd61152ace0f562544c71c02c1793f7a98b4649197e`
- Windows: `7c1a635feebb68411261eb058dc606d3531570e20cdee3bc22d52e7299782dd2`
- Manifest: `17c11bc8831ec687d9b92e92ced524e4f5bf9a9404dec30169b55b7d0eea634f`

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
