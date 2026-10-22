# Beamo Wipe: twentieth comprehensive local audit

Release-asset assembly defects are repaired from baseline
`229fe387be9ccb406c317e1ebf3e142ee81d3de1` on branch
`fix/safety-audit-20261019`. Work began 2026-10-21 and completed
2026-10-22 UTC.

## Repairs

- `prepare_release_assets.py` previously followed linked parent directories
  while reading release inputs and creating the receipt and signed inventory.
  It now opens every parent component without following links and retains the
  owned staging directory descriptor through the entire assembly.
- Input hashes and records now bind one stable regular inode to its final
  requested path. Hard-linked inputs, linked parents, same-byte inode
  replacements, whole-stage replacement, and late replacement while signing
  fail closed.
- The signed manifest, signature, key registry, image metadata, completion
  marker, checksum sidecar, compressed image, and every public asset use
  bounded or streaming descriptor reads. JSON rejects duplicate fields and
  non-finite values.
- Gzip validation reads the already-bound compressed descriptor, limits output
  to the tested raw-image size, and requires both the decompressed digest and
  exact size to match.
- The build receipt and download inventory share one retained set of public
  asset records. All source and generated-file bindings are revalidated before
  inventory signing, before signature publication, and after publication.
- Generated JSON is created exclusively through the retained staging
  descriptor, synchronized, reread twice, checked for the exact mode and
  single-link regular-file identity, and then bound to the final path.

## Reproduction and regression evidence

The completed 13-case PASS20 module was copied into an external archive of the
exact baseline commit. It produced **12 intended failures and one positive
control**. Eleven attacks were accepted directly; the final stage-replacement
case also failed because the baseline lacked the new bound-output helper. The
earlier ten-case baseline replay separately exercised that same late stage
replacement and failed because the old assembler returned success. On the
final tree all **13 cases pass**. The cases cover linked and hard-linked
inputs, linked output parents, same-byte inode replacement, linked staging
ancestors, duplicate metadata and signed-manifest fields, replacement while
recording and signing, late whole-stage replacement, and a complete positive
signed-inventory flow.

The archived baseline transcript SHA-256 is
`3e217f50c855eb12eafede6ed8ee6549e773ebbea57b21e230d84da1d079f2ae`;
the final regression transcript SHA-256 is
`cfc14fd2dc11c362cccf5421245ca5ab0e9d286b54a604a80bd2dd5522f6feb9`.

The broader release, manifest, signing, publisher, GitHub, transfer, FIFO,
path-binding, and USB-download boundary selected 206 cases: **194 passed and
12 existing manufacturing-ISO cases skipped**, with zero failures or errors.
Its transcript SHA-256 is
`f620c8acf54611de11f74c529ffb95d459c0b77f4a5da48675a689e41a769494`.

The final exact-source suite ran as UID 1000 in a network-disabled container,
with dry-run mode, a private D-Bus session, and private Xvfb display `:200` at
1600×1000/72 DPI. Warnings were errors. Two tests for absent generated
`packaging/live/config/{bootstrap,binary}` inputs were explicitly deselected.
The JUnit contains **12,163 selected cases: 12,137 passed, 26 documented
environment skips, zero failures and zero errors**. The skips are 12 absent
manufacturing-ISO cases, nine unavailable pinned-browser cases, four
network-disabled Microsoft-source checks, and one unavailable gcloud case.
JUnit SHA-256 is
`c48ca550130668aea8cad21be13560c84db118be3c50632e139953659d2e703e`.

Ruff, the blocking security selections, formatting, compileall, whitespace
validation, and mypy over 53 product/script modules pass. Mypy's existing
untyped-body notes remain informational. The static transcript SHA-256 is
`79a9164c464c7b89222589d9d8a92063e73ea115373b4591a83c250f940e0871`.

The repository-pinned, checksum-verified Go 1.26.8 toolchain was installed
under `/workspace/beamo-tools`, outside Git. Uncached race tests, vet, and the
boot-option fuzzer pass; the fuzzer completed 350,000 executions. Windows test
compilation and Linux amd64, Windows amd64, macOS amd64, and macOS arm64
cross-builds pass. Their transcript SHA-256 values are
`7a745e9230c3087cce047c3a95a15b8fe3d11ab005d8d5e8b423737afcba7539`
and `ce08e8231ea11801345f5b7955527ddc16ca2b9244737a0db6bfe45e72c93958`.

The accepted product/test bytes were frozen before the final suite and matched
afterward:

- `scripts/prepare_release_assets.py`:
  `9613571cfd2369947a799c78ed6ab16ec63368b9550b519333a55437639b7757`
- `tests/test_release_asset_assembly_binding_pass20_20261021.py`:
  `4a737d582ade16cada74b75d571e538a6a153c6338c5d7b35675a03db81551e7`

Detailed local receipts remain outside Git at
`/workspace/beamo-tools/audit-pass20-20261021/root/` to avoid committing large
runtime artifacts.

## Rejected attempts

The native system Python lacked pytest, so it was not used. A container run
without Xvfb was rejected after GTK initialization failures. A later native-X11
run was rejected because auto-selected display `:99` is explicitly forbidden
by the private-display fixtures. The accepted run uses `:200`. A clean full run
that preceded a type-only local-variable rename is retained as history but is
not counted as the final source-bound gate.

## Limits

No actual nwipe engine, block device, mount, firmware, power, physical USB,
guest, hosted CI, ISO/QEMU, or native Windows execution occurred. Cross-builds
do not establish native acceptance. Exact-source ISO/KVM, native Windows,
firmware, physical-media, and reconnect qualification remain open for an
authorized isolated worker or eligible physical session.

No remote write, pull request, merge, deployment, or release occurred.
Publication remains blocked by the earlier automatic approval review that
rejected exporting operational-backlog metadata as internal data.
