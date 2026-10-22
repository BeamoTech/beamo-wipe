# Beamo Wipe: twenty-second comprehensive local audit

Date: 2026-10-22 UTC  
Branch: `fix/safety-audit-20261019`  
Baseline: `3accb9cd944f0195b23b70476712454cb5820bd7`

## Result

This pass repaired the protected GCS release publisher's remaining path and
byte-identity gaps. Every release input is captured as an owned, single-link
regular inode beneath a link-free retained parent before verification. The
publisher reopens that same identity for hashing and upload, measures the exact
bytes consumed by the upload, revalidates the descriptor, requested name and
parent afterward, and requires the remote object to have the exact expected
length and digest before it can contribute to `RELEASE_COMPLETE.txt`.

The signing key and committed key registry now use the same bounded,
descriptor-relative input path. Linked parents and hard links are rejected.
Generated signatures use exclusive creation, flush and file/directory sync,
and final descriptor/name/parent validation. Failure cleanup removes only the
inode created by the publisher and preserves a concurrent replacement.

The publisher also rejects duplicate input paths or object names, duplicate
JSON fields in metadata responses, boolean or negative upload sizes, and short
or overlong remote readback. Existing publisher tests were adjusted only where
their mocks needed to represent the strengthened upload and remote-size
interfaces.

## Reproduction evidence

The 19-case PASS22 regression module was replayed against an exact checkout of
the baseline commit. It produced **18 intended failures and one passing legacy
control**, with no errors or skips. The failures cover hard-linked inputs;
same-byte leaf and parent-directory replacement; linked-parent and hard-linked
signing keys and registries; generated-signature replacement; bound-upload
replacement and in-place mutation; duplicate metadata token fields; negative
and boolean sizes at both upload entry points; and short, overlong and exact
remote readback. On the repaired tree all **19 cases pass**.

- Baseline JUnit SHA-256:
  `dce3b0b37e31951c467d2101bb3cc5e6d6d15d1a0487b37188b20fdc41ad8813`
- Final regression JUnit SHA-256:
  `8514344dcbb6f32d4c9e7b512d951d51aae74f928d39c8253739033d4ea8a4b3`

The broader release-focused selection contains 282 cases: **270 passed and 12
manufacturing-ISO cases skipped**, with zero failures or errors. It ran before
a formatting-only edit to the new regression module; product bytes were
unchanged, and both the final regression replay and final full suite exercised
the exact final source. Focused JUnit SHA-256:
`5f818fe1c3257fc8eb5559d129f9f44236850b6096a13b0b39153070fb4c84d6`.

## Exact-source full suite

The final full suite ran as UID 1000 in one unprivileged,
network-disabled `beamo-wipe-dev:20261017` container. It used dry-run mode, a
private D-Bus session and a private Xvfb display `:200` at 1600x1000/72 DPI.
Warnings were errors and pytest's cache provider was disabled. Two tests for
absent generated `packaging/live/config/{bootstrap,binary}` inputs were
explicitly deselected.

The JUnit contains **12,204 selected cases: 12,178 passed, 26 skipped, zero
failures and zero errors**. The skips are 12 unavailable manufacturing-ISO
cases, nine unavailable pinned-browser cases, four network-disabled Microsoft
source checks and one unavailable gcloud case. JUnit SHA-256:
`488c2fe4c16194c6f4adf5ddd139eb1ea6faab2aea61857b8c56f12d82ed773b`.

## Static and cross-platform checks

Compileall, Ruff, the blocking Ruff security selections, Ruff formatting,
whitespace validation, ShellCheck and Actionlint pass. Mypy reports no issues
over 52 product modules or the publisher module; its existing untyped-body
notes remain informational. Static transcript SHA-256:
`623ade206f2790781373037754cf2ba7503a228764bfc41d2ce7f4eae74c5c14`.

The checksum-verified Go 1.26.8 toolchain remains outside Git under
`/workspace/beamo-tools`. Uncached race tests and vet pass. The boot-option
fuzzer target was 350,000 executions and completed 350,021. Windows test
compilation and Linux amd64, Windows amd64, macOS amd64 and macOS arm64 builds
pass. The Linux build is a static ELF and its `--version` command exits zero;
the other file formats match their targets. Go transcript SHA-256:
`4a3f15f39b5c90ae71ee31f6fa9ab27089d66106ef009c8a54e40655cd550830`.

The functional source and regression bytes were frozen before the accepted
full suite and matched afterward:

- `scripts/publish_release_gcs.py`:
  `026f1fb336673627441387c2c6f096600d12b50ef2b3cdb466e3d04c6e174415`
- `tests/test_release_publisher_binding_pass22_20261022.py`:
  `5d8d2fd29c3c742b089ee47756ac629da3676981d2cc7dbbbf01b5a47d20ba0d`
- `tests/test_release_publisher_pass9.py`:
  `403b26838eb6c8c69d51604b10f953807b6d2d9951030bc15bcb7d708b7f877b`
- `tests/test_release_qemu_evidence_pass10.py`:
  `c4035dc80cad879123aeba275cc36bb40e4564773dd1538a4d32e497557cb24c`

The source-freeze manifest SHA-256 is
`59ecd8726bbae072a62645f779403465c968e65b53c639d256655ef396b6b43a`.
Detailed local receipts remain outside Git at
`/workspace/beamo-tools/audit-pass22-20261022/root/` to avoid committing large
runtime artifacts.

## Discarded setup attempts

Three full-suite setup attempts were excluded from acceptance:

1. Xvfb cookie authentication was unavailable to child processes after their
   environment was rebuilt, causing display-dependent skips. The run was
   stopped.
2. `BEAMO_ISOLATED_X11_TEST=1` was initially absent, causing native GUI skips.
   The run was stopped.
3. A read-only repository mount produced one failure in
   `test_hosted_preview_rejects_a_javascript_syntax_failure` because that gate
   intentionally generates the ignored `web-preview/` tree before invoking
   its fake parser. The same test passed with the otherwise identical writable
   mount. The discarded JUnit has 12,177 passes, 26 skips and one failure, with
   SHA-256
   `c9130b7c5ccf0eb9fbf4fad45b9e8cba79cf24d5ebadb71847c5ca81f6727214`.

After the first green full run, Ruff formatting found one assertion layout in
the new test module. That formatting-only change was applied, the source was
refrozen, and the complete accepted full suite above was rerun from the exact
final bytes.

## Limits

No actual nwipe engine, block device, mount, firmware, power, physical USB,
guest, hosted CI, ISO/QEMU or native Windows execution occurred. Cross-builds
do not establish native acceptance. Exact-source ISO/KVM, native Windows,
firmware, physical-media and reconnect qualification remain open for an
authorized isolated worker or eligible physical session.

No remote write, pull request, merge, deployment or release occurred.
Publication remains blocked by the earlier automatic approval review that
rejected exporting operational-backlog metadata as internal data.
