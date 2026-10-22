# Beamo Wipe: twenty-first comprehensive local audit

Release-transfer boundary defects are repaired from baseline
`65a79d03c86c88fe1730d076ac88e446f9c4a50d` on branch
`fix/safety-audit-20261019`. Work completed 2026-10-22 UTC.

## Repairs

- Transfer source names are now unique, lexical paths beneath the checkout's
  fixed `dist` or `qemu-evidence` trees. Every source and staged file is opened
  relative to link-free pinned parents and must remain an owned, single-link
  regular inode through its last use. Linked checkout/source parents, hard
  links, same-byte inode replacements and whole-transfer replacement fail
  closed.
- Qualification copies are created exclusively, synchronized and rebound to
  their requested paths. Each ordinary transferred file's final hash and size
  must equal its measured source, rather than merely becoming a new manifest
  record. The raw image stays bound while deterministic gzip output is made.
- The transfer manifest is limited to 4 MiB, read once as stable bytes, rejects
  duplicate fields and non-finite numbers, and requires exact top-level and
  record fields. Byte counts reject booleans, hashes require lowercase SHA-256,
  the raw image has an explicit upper bound, and the expected file set must be
  exact.
- Descriptor-relative tree enumeration rejects links, special objects,
  additions, omissions and directory changes. Restore retains the manifest and
  all transfer-file bindings while it builds a complete private staging tree,
  decompresses the image with an exact size/hash bound, and revalidates every
  input and output.
- Complete `dist` and `qemu-evidence` directories are published by rename
  relative to retained checkout/staging descriptors. If the second publication
  or final verification fails, the first directory is rolled back; an invalid
  gzip or unexpected staged file leaves no public partial output. Cleanup only
  runs while the private directory remains bound to the object this process
  created.
- The qualification workflow no longer reopens the manifest with a separate
  `sha256sum` command. The validating pack process retains and prints the digest
  of its bound manifest; the shell captures it in a failure-propagating
  assignment before exporting the job output. Any later artifact replacement
  must still match that original digest in the publisher job.

## Reproduction and regression evidence

The final 22-case PASS21 module was copied into an external archive of the
exact baseline commit. It produced **21 intended failures and one positive
control**. The failures demonstrate accepted linked parents and hard links,
duplicate sources and JSON fields, boolean byte counts, extra/oversized
manifest data, same-byte file and whole-tree replacement, copy corruption,
linked output escape, partial bad-gzip output, unexpected staged content,
non-transactional two-directory publication, and the cross-process workflow
digest gap. On the final tree all **22 cases pass**.

The archived baseline transcript SHA-256 is
`6d06daa1a1742b5f6716a5d785abff5858446f8df55cda2e67d3023c4b765a29`;
the final regression transcript SHA-256 is
`b7456fe1c73277ed8a41d0de67f445660ef54ae8186642ae68ec93519cc7ba5b`.

The broader release, manifest, signing, publisher, GitHub, transfer, FIFO,
path-binding and USB-download selection contains 469 cases: **388 passed and
81 explicitly skipped** because that focused run intentionally had no isolated
display or manufacturing ISO. It had zero failures and errors. Its transcript
SHA-256 is
`825272052d8c787ef08ac704d78976e022e380351e7609b11b825fc22eae3fc0`.

The final exact-source suite ran as UID 1000 in one network-disabled container,
with dry-run mode, a private D-Bus session and private Xvfb display `:200` at
1600x1000/72 DPI. Warnings were errors. Two tests for absent generated
`packaging/live/config/{bootstrap,binary}` inputs were explicitly deselected.
The JUnit contains **12,185 selected cases: 12,159 passed, 26 documented
environment skips, zero failures and zero errors**. The skips are 12 absent
manufacturing-ISO cases, nine unavailable pinned-browser cases, four
network-disabled Microsoft-source checks and one unavailable gcloud case.
JUnit SHA-256 is
`ea6b910bb4d677de5e6f40e7b7523815c6e667e1bb060ea587a291357713fcb0`.

Ruff, the blocking security selections, formatting, compileall, whitespace
validation and mypy over 54 product/script modules pass. Mypy's existing
untyped-body notes remain informational. ShellCheck and Actionlint pass. The
static transcript SHA-256 is
`31b22a790ef1c1c2204ee85fec33d96cde0b337bd183db762f0b8e17cb389731`.

The checksum-verified Go 1.26.8 toolchain remains outside Git under
`/workspace/beamo-tools`. Uncached race tests, vet and the boot-option fuzzer
pass; the fuzzer completed exactly 350,000 executions. Windows test compilation
and Linux amd64, Windows amd64, macOS amd64 and macOS arm64 cross-builds pass.
Their transcript SHA-256 values are
`2f7839b78b918fa3829032046ba62423a0da9356803eb90a71969e0667e7b40a`
and
`0434da0397eb399971ecfbd77c2e2aee857a2ecce90e20dd831ae9216262e0dc`.

The functional source and regression bytes were frozen before the full suite
and matched afterward:

- `.github/workflows/release.yml`:
  `9ea706daab022179231911c921ab0801f13dfac9aa67935e9790718dbeb88e0c`
- `scripts/release_transfer.py`:
  `1a760110711f23980187e6059c4187f36bcbf6bb7cb208af8c89114bff3de5aa`
- `tests/test_release_transfer_binding_pass21_20261022.py`:
  `9f55ba6db795b8afe43ea2a6a0c906a910bb8dae232d0a6d1ae0658eacfe9562`

Detailed local receipts remain outside Git at
`/workspace/beamo-tools/audit-pass21-20261022/root/` to avoid committing large
runtime artifacts.

## Rejected attempt

The first full-suite launch did not collect tests: a login shell replaced the
container image's configured Python environment, and unprivileged Xvfb lacked a
private socket directory. That attempt is not counted. The accepted run kept
the image PATH and mounted an empty private mode-1777 socket directory into the
same UID-1000, network-disabled container; it did not add privilege or expose
the display.

## Limits

No actual nwipe engine, block device, mount, firmware, power, physical USB,
guest, hosted CI, ISO/QEMU or native Windows execution occurred. Cross-builds
do not establish native acceptance. Exact-source ISO/KVM, native Windows,
firmware, physical-media and reconnect qualification remain open for an
authorized isolated worker or eligible physical session.

No remote write, pull request, merge, deployment or release occurred.
Publication remains blocked by the earlier automatic approval review that
rejected exporting operational-backlog metadata as internal data.
