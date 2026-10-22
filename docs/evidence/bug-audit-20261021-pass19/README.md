# Beamo Wipe: nineteenth comprehensive local audit

GitHub release-asset authentication defects are repaired from baseline
`e5ba1f3cb817f706035c03eff043e39d291b0309` on branch
`fix/safety-audit-20261019`. Audit date: 2026-10-21 UTC.

## Repairs

- Draft promotion previously accepted an uploaded asset that was absent from
  the signed download inventory. Every uploaded asset must now have an exact
  authenticated hash-and-size record. The only exemptions are the literal
  `release-downloads.json` and `release-downloads.json.sig` bootstrap pair,
  which cannot recursively list themselves; the CLI requires their upload
  paths to be the exact files whose signature it verified.
- `RELEASE_COMPLETE.txt` is now included in the signed download inventory, so
  the protected-publisher completion marker is authenticated before GitHub
  promotion.
- Local upload verification now opens every parent without following links,
  hashes one regular-file snapshot, binds the opened descriptor to its final
  requested name, and revalidates every retained file and parent identity
  before acceptance. Linked leaves, linked parents, and same-byte inode
  replacement fail closed.
- GitHub asset records and signed inventory records now require exact field
  types and normalized SHA-256 values. Boolean byte counts no longer compare
  equal to integer sizes, duplicate/malformed records return false, and the
  draft flag must be the JSON boolean `true`.
- The command-line verifier uses bounded, repeated, link-free reads for the
  GitHub response, signed inventory, detached signature, and trusted key
  registry. It rejects duplicate JSON fields and an unknown inventory schema,
  then verifies the detached signature over the exact parsed inventory bytes.

## Reproduction and regression evidence

The final 19-case focused set was replayed against an archived exact baseline
tree. Baseline produced **10 intended failures and 9 positive controls**;
the repaired tree passes all 19. Cases cover missing authenticated records,
linked leaves and parents, same-byte path replacement, boolean sizes,
malformed GitHub records, strict bootstrap names and paths, a real ephemeral
Ed25519 CLI flow, and signed coverage of `RELEASE_COMPLETE.txt`. Only ordinary
temporary files were used. Baseline JUnit SHA-256 is
`f2eb4e22e41161dc7173f877567ac3dcff37efc56db9d50c5603da223243a073`;
fixed JUnit SHA-256 is
`bdfb32ef95a7d273a972f62c32b220b8a24e36fe9ab125e59e9bfef62bdf2cfb`.

The broader release, manifest, signing, publisher, artifact, GitHub and
transfer boundary selected 362 cases: **293 passed, 69 existing environment
skips, zero failed or errored**. Its JUnit SHA-256 is
`1136f45057729b207043e61c8c01580050b66a379d26ca4e5731f450ee3638df`.

The exact-source suite ran as UID 1000 in network-disabled containers with all
capabilities dropped, `no-new-privileges`, fake disks, dry-run/demo mode, the
native inventory override unset, private D-Bus sessions, and Xvfb display
`:200` at 1600×1000/72 DPI. Warnings were errors. The complete selected set
contains 12,149 cases: **12,122 unique cases passed and 27 retained their
documented environment skips**, with two generated-live-config tests
deselected because `packaging/live/config/{bootstrap,binary}` are absent.

The accepted evidence consists of a zero-failure full run with 12,098 passes
and 51 skips plus a 25-case Go-path supplement that executed all 24 cases
skipped only because Go was initially absent from `PATH`. Their JUnit hashes
are `8fe21b160330ae10bfea1f17a1ed3fd10f93263ee082db53170e696d6eb7fd60`
and `1d5e23b1725db049942729b0588638990755ff6bd2997b815918b8698f0fd282`.
The remaining 27 skips match PASS18: 12 missing manufacturing-ISO cases, nine
unavailable pinned-browser cases, four network-disabled Microsoft source
checks, one unavailable gcloud case, and one missing live-build config case.

Two attempted evidence consolidations were rejected rather than counted. A
2-GiB tmpfs run exhausted space after adding the Go cache. Moving all of
`TMPDIR` outside `/tmp` avoided that limit but correctly triggered four
session-recovery safety refusals because production recovery state must be on
the volatile filesystem. Those exact four cases pass under the supported
`/tmp` layout (JUnit SHA-256
`b65fcad60969e89b363c246a2feae8f898adf4028c4a3a00d549f24e198c0cef`).
No product assertion failure is hidden by either rejected attempt.

Compilation, Ruff and security selections, formatting, mypy over 52 product
modules plus both changed scripts, ShellCheck, and the private fail-open
mutation gate pass. The existing `PLACEHOLDER_RE` TODO-pattern message remains
informational. Go 1.26.8 race tests and vet pass; the boot-option fuzzer
completed 350,000 executions. Windows test compilation and Windows, macOS
amd64, and macOS arm64 launcher cross-builds pass.

Fresh Windows and Linux desktop launchers were built outside the repository
and verified against their manifest. The Windows artifact begins with `MZ`,
the Linux artifact begins with ELF magic and is executable, and Linux
`--version` exits 0 with version 0.2.13, baseline commit `e5ba1f3c…`, and
`dirty=true`. Observed SHA-256 values were:

- Linux: `35b8293a76406b3441e83463364185dfeaa1f7801709ce9446220d19c219aa3d`
- Windows: `dc9b8cf8ceb671e51505eb6d6420ec60552cd5b9e334238536686b31c708173e`
- Manifest: `6e2b563316542148e88b011427ba688d5171f30d41746ddf0f2b3718005c9a0d`

Web, embedded JavaScript, console, and helper previews pass. The actual fake
Tk preview was captured on private display `:250` at 72 DPI, visually
inspected for clipping, warning/guidance content, branding and focus, and
closed with an actual `WM_DELETE_WINDOW` event. See the
[unedited preview](preview/actual-preview-72dpi.png) and
[capture receipt](preview/actual-preview.json).

The detailed local receipts and JUnit files remain outside Git at
`/workspace/beamo-tools/audit-pass19-20261021/root/` to avoid committing large
runtime artifacts.

## Limits

No actual nwipe engine, block device, mount, firmware, power, physical USB,
guest, hosted CI, ISO/QEMU, or native Windows execution occurred. Cross-builds
do not establish native acceptance. Exact-source ISO/KVM, native Windows,
firmware, physical-media, and reconnect qualification remain open for an
authorized isolated worker or eligible physical session.

No remote write, pull request, merge, deployment, or release occurred.
Publication remains blocked by the earlier automatic approval review that
rejected exporting operational-backlog metadata as internal data.
