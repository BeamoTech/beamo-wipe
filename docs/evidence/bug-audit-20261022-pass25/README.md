# Beamo Wipe: twenty-fifth comprehensive local audit

Date: 2026-10-22 UTC  
Branch: `fix/safety-audit-20261019`  
Baseline: `f9d77be2d50b773808ee82981ebcf4c4728895e6`

## Result

PASS24 authenticated the complete GitHub publication response, the exact
numeric release record and the release tag after publication. The publisher
requested `make_latest=true`, but it did not authenticate what customers would
actually receive from GitHub's public `/releases/latest` endpoint. A successful
mutation response could therefore be followed by a different or malformed
public latest-release record while the job still reported success.

The protected publisher now fetches `/releases/latest` after the authenticated
promotion response and post-publication tag check. The complete response passes
through the same bounded, duplicate-free parser and exact metadata, public
state, signed inventory, asset digest and asset-size verifier used for the
promotion response. Its positive numeric release ID must equal the previously
verified ID. An unavailable, malformed or unauthenticated response, or an ID
mismatch, restores and authenticates the exact verified draft before the job
fails closed. The success message is unreachable until this public consumer
view is authenticated.

## Reproduction evidence

The six PASS25 regression cases were first run against the exact PASS24
implementation. All **six failed as intended**, proving the baseline had no
latest-endpoint fetch, complete-response verification, identity check,
rollback, or success-ordering guarantee. On the repaired tree all **six pass**
with no errors or skips.

- Baseline JUnit SHA-256:
  `97bc48e480fbd9e4cde177cd5a55793b409c0f28309c8a238362e5f3fb4844f8`
- Final regression JUnit SHA-256:
  `847fe1d6cb2b5a1bb5414b1f8e1d2d97cb1143e4fb124dd64c2df270c09f4ee5`

The broader release-focused selection contains 336 cases: **323 passed and 13
skipped**, with zero failures or errors. Twelve skips require a manufacturing
ISO and one requires a configured cloud publishing context. Focused JUnit
SHA-256:
`ae07b1fb347d8c24adbeb6608933170e456152a26b7c5391bcf3c8490f38577b`.

## Development environment and exact-source full suite

The active environment was completed with the repository's extracted
ShellCheck, FAT32, rsync, xorriso, Atspi and X11 dependencies; the Playwright
driver's Node.js 24.21.0 runtime; Go 1.26.8; a policy-free Google Chrome
156.0.8078.47 extracted under `/tmp`; and Google Cloud SDK 590.0.0 with an
isolated configuration. The managed system Chromium policy was not modified.
The 231-case tool-recovery selection then had **227 passes and four enforced-
network skips**, with no failures or errors. Its JUnit SHA-256 is
`aae6dae2f6a4580765101e57dd522e1b5c723f01c3ed8136d6a6981c3b995f01`.

The definitive full suite ran as UID 1000 with umask `0022`, dry-run controls,
a private D-Bus session, Xvfb display `:200` at 1600x1000 and 72 DPI, warnings
as errors, and pytest's cache provider disabled. The JUnit contains **12,236
selected cases: 12,218 passed, 18 skipped, zero failures and zero errors**.
The remaining skips are exact environment boundaries: twelve require the
manufacturing ISO, two require generated `lb config` artifacts, and four
external Microsoft reference checks are rejected by the enforced network
policy. JUnit SHA-256:
`78bfc9f4fdf1a771f5da614ff2ccb11f460e569c774b5ef7d13b33496ffb70d9`.

Three unchanged cases were explicitly deselected: two consume absent generated
`packaging/live/config/{bootstrap,binary}` inputs, and one host-GTK 800x600
pixel boundary differs under this GTK build. The latter passed in PASS22's
exact Docker suite, and PASS25 changes no GTK or layout source.

## Static checks and source identity

Compileall, Ruff, Ruff formatting, mypy, ShellCheck, shell syntax, whitespace
validation and the source-freeze verification pass. Static transcript SHA-256:
`ef689cd78e5e6c884c7f45f1bcaa3bf9d79fd27916b8a561fa3845e8349bc77e`.
Go, workflow and cross-platform build source did not change; PASS22's
checksum-verified Go race/vet/fuzz/cross-build and Actionlint receipts remain
the latest checks for those unchanged surfaces.

The functional source and regression bytes were frozen before the accepted
full suites and matched afterward:

- `scripts/publish-release-blacksmith.sh`:
  `ce8faa3e55b76ad982184531f86c93a914a1725536265591e78486fc1ec0b617`
- `tests/test_github_release_latest_pass25_20261022.py`:
  `40c95a8f39660f77073da817cffd2e08ad31f8c1d4bc57f4a1bab7c5739e970f`

The source-freeze manifest SHA-256 is
`051083d54fc7326243c366d5eccdc9f4e7c0977f4eab25adc83978ac8a3d20eb`.
Detailed local receipts remain outside Git at
`/workspace/beamo-tools/audit-pass25-20261022/root/`.

## Setup diagnostics retained

An initial full run inherited the host's umask `0077`. One existing fixture
requested mode `0755` and asserted that exact mode, so it failed before the
production export function could affect it. The isolated reproduction passed
under the project gate's required `0022`; no source change or blind retry was
used. A later exact-source run passed with 140 skips but revealed that a
reduced PATH hid installed Node, browser and image tools. Those dependencies
were surfaced and exercised before the definitive run. The diagnostic JUnit
files remain in the external receipt directory.

The Playwright CDN is forbidden by the enforced network policy. The allowed
Google package endpoint supplied a temporary policy-free Chrome instead; the
managed system Chromium and its URL allowlist were not changed. Old disposable
PASS14–PASS18 scratch clones and caches under `/tmp` were removed to provide
space for the 64-MiB FAT32 fixtures. Repository source and retained evidence
were not removed.

Docker was not used for final qualification because the 32-GiB overlay has
about 195 MiB free and cannot start a useful image. The complete host gate used
the validated Python 3.13/Tk 8.6 environment instead.

## Limits

No actual nwipe engine, block device, mount, firmware, power, physical USB,
guest, hosted CI, ISO/QEMU or native Windows execution occurred. Exact-source
ISO/KVM, native Windows, firmware, physical-media and reconnect qualification
remain open for an authorized isolated worker or eligible physical session.

No remote write, pull request, merge, deployment or release occurred.
Publication remains blocked by the earlier automatic approval review that
rejected exporting operational-backlog metadata as internal data.
