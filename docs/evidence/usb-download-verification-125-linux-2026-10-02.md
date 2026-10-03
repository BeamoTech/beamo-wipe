# USB download verification — Linux follow-up (#125)

2026-10-02. Base source: `be26f24ac08aefa708cf9dd5a0045eb915abd7c0`.
The original implementation, `d5edff22c406e08fba3a60ac07faea97e99068a0`,
is already included in main. This follow-up closes the complete-public-download
and Linux-execution gaps in the [earlier receipt](usb-download-verification-125.md).
The commit containing this receipt identifies the follow-up source; use
`git log -1 --format=%H -- docs/evidence/usb-download-verification-125-linux-2026-10-02.md`.

## Changes and metadata source

The [canonical procedure](../release-verification.md#usb-image-download-verification)
already authenticates the inventory and manifest, verifies compressed bytes
before extraction, bounds extraction to the signed raw size, and publishes a
verified regular file without overwrite. Its verifier is unchanged.

This follow-up adds the actual `.img.gz`, its sidecar, signed inventory and
manifest signature to the artifact table; links the procedure from the README
and support runbook; distinguishes the current verification-tool checkout from
the older image source; and links separately authorized safe writing/readback.
The consumer section's links are absolute and version-pinned where appropriate
so they also work when quoted in a public release context. The download
destination guard now uses an explicit `if`, with the same refusal behavior.

Read-only inspection covered `prepare_release_assets.py`,
`publish-release-blacksmith.sh`, `build-usb-image.sh`, the signing/manifest
modules, release workflow, key registry/custody policy, public release filenames
and verification instructions. **There is no compressed/raw metadata gap:**
the signed public inventory and its generation source already contain both
sizes and hashes. The safe generator fixture tests confirm both records;
no generator schema change or invented release value was needed.

## Observed public bytes and trust

[Public v0.2.12](https://github.com/BeamoTech/beamo-wipe/releases/tag/v0.2.12)
is still the latest public release: ID `398337215`, published
`2026-09-28T14:37:13Z`. The public annotated tag object
`c9d880cb7b9809fab0d93bcfcd1e4cdb2ed3c1bc` and the local peeled tag both
identify source **`e986419379f512f8088f5982ee02a51dc91a9dae`**. The tag itself
is unsigned; the authenticated release documents use separate Ed25519
detached signatures. Both documents bind build
**`625971a4-afef-5398-9bec-d96455192ab3`**.

The independently maintained checkout registry is active for key
`93caaf7ca93eff4d`, fingerprint
`93caaf7ca93eff4d7fa1c16e360f9d6aa17ced0155a56d4cf89d8f6d429e66f7`.
Its approval/distribution path is the existing first-key record and operator's
independent announcement; no new human key ceremony was performed here. The
registry was not taken from the release's adjacent `keys.json` asset.
The CLI recomputed/bound that fingerprint and verified both exact downloaded
documents before using their hashes, with acceptance floor `0.2.12`.

| Actually measured regular file | Bytes | SHA-256 matching authenticated inventory |
| --- | ---: | --- |
| `beamo-wipe-0.2.12-amd64.img.gz` | 601441384 | `a3d2a65d8941facbd30b794b083419dc694511903281e57cd028db565bdc1972` |
| `beamo-wipe-0.2.12-amd64.img` | 2147483648 | `1e807895ee643a35d90a0c2302143f02b01de91aec564a3972d86740c55ae10b` |

The inventory's measured SHA-256 is
`2023d3aa84a84f406a1d0f0b230d38293eb1b74275cf068088408209a296511c`;
the manifest's is
`0bb56538500330086f507538e94ec68846ff5ab39ddf491dbeaf467a50cfd5b8`.
The image metadata also matched the signed inventory and manifest's ISO
identity. The ISO bytes were **not downloaded or verified in this USB walkthrough**.

The whole Markdown command block ran from an unrelated directory into a new
private empty directory, with only the absolute trusted-checkout path replaced.
Actual HTTPS fetches, signature checks, compressed verification, extraction,
raw verification and independent `verify` all exited **0**. This public run
took 347 seconds. After the guard's readability change, the final exact block
also passed in another empty directory using the already-downloaded public
bytes through a test-only curl adapter (20 seconds). That second run is cached
public-fixture validation, not a second HTTP transfer. Both runs verified the
full compressed and raw files; no partial was reused as a completed image.

## Checks, platforms and limitations

Linux: Ubuntu 24.04 x86_64 in WSL2, Python 3.12.3, cryptography **50.0.1**,
pytest 9.0.3, curl 8.5.0. Native Windows Python 3.13 executed the three
dependency-free documentation assertions; native Windows pytest was unavailable
in that interpreter. No native Windows USB-verification commands are documented.
macOS was unavailable this session: its earlier fixture execution remains the
[dated Mac result](usb-download-verification-125.md#executed-verification-and-limitations),
not a fresh execution with the current pinned dependency.

These local commands ran in isolated source copies, with the verification venv
on PATH. The full suite used a private XDG runtime directory and fake-device
mode; its controller and environment are preserved in the audit.

```sh
python3 -m pytest -o addopts='' \
  tests/test_usb_download_verification.py tests/test_usb_verification_docs.py \
  tests/test_blacksmith_release.py tests/test_release_signing.py \
  tests/test_signing_metadata.py
dbus-run-session -- xvfb-run -a -s '-screen 0 1600x1000x24 -dpi 72' \
  ./scripts/test-all.sh -rs
python3 scripts/verify-usb-download.py --help
```

The initial follow-up's focused tests: **67 passed**, including 25 USB fixture cases and
three cross-platform documentation checks. Negative cases reject inventory
tampering, missing/invalid signatures, wrong/revoked keys, compressed/raw
corruption, missing records/sizes, inconsistent source/build, traversal,
invalid gzip/DEFLATE, expansion beyond authenticated size, wrong/relative
directories, symlinks and stale final/partial files. The copied shell block
also rejects altered inventory before downloading the image, corrupt compressed
downloads before extraction, and an interrupted transfer with exit 22 while
retaining only a clearly named `.part`.

Full local suite: **5635 passed, 57 skipped**, zero failures/errors, 814.73 seconds.
Its frozen snapshot predates the final link/guard
readability changes; the final command block, links and assertions were checked
separately by the focused tests and full-size cached public fixture.
Ruff, CLI help, `sh -n`, unfiltered ShellCheck and `git diff --check` passed.
All five consumer-section links returned HTTP 200; each pinned fragment matched
its target heading. Checkout entry/handoff links resolved locally.

Initial validation-run issues are retained in the private audit: a new test's
overbroad wildcard assertion caught the shell's absolute-path `case` pattern;
the first fixture runner omitted the verification venv from PATH; and
ShellCheck reported SC2015 on the original equivalent guard shorthand. The
assertion/runner were corrected and the guard clarified, followed by the
recorded successful checks. No signature/hash check was bypassed.

### PR review follow-up

[PR #86](https://github.com/BeamoTech/beamo-wipe/pull/86) identified that the
linked setup installs dependencies in a platform-specific venv. The copyable
block now selects `.venv-linux/bin/python` or `.venv-darwin/bin/python`
explicitly, and stops before creating a download directory if setup is missing.
The fixture poisons default `python3` and exercises both environment selections,
including missing setup and the existing download failures. Darwin selection
is simulated on Linux; this does not claim fresh macOS execution.

Post-review focused validation: **73 passed**, including 31 USB cases; Ruff,
`sh -n`, ShellCheck with the documented `sh` dialect, and the three standalone
Windows documentation assertions passed. The revised exact shell block also
verified the complete cached public Q12 compressed/raw files in a fresh private
directory while default Python was blocked. Only the absolute source path was
substituted. It used the selected setup interpreter and stopped before media
writing. The first review validator invocation omitted ShellCheck's dialect
argument for the extracted block; the diagnostic and corrected run are retained.

The link test now labels `urljoin` as a portability assertion and also checks
commit-pinned links' paths and headings against the checkout. Actual HTTP status
and pinned historical headings remain separate observations in the dated
receipt, rather than claims made by the deterministic test.

## Handoff and publication boundary

The [machine-readable receipt](usb-download-verification-125-linux-2026-10-02.json)
records measured identities, tools, commands, link results, source hashes and
log hashes. Full logs/JUnit and API snapshots are in the task-owned local audit
`%LOCALAPPDATA%\BeamoWipe\usb-download-125\20261002-validation`.

Read-only before/after API comparison found the same release ID, tag,
description and every asset ID, size, digest and update timestamp. Published
release bytes, detached signatures, checksums, tags and historical release notes
were left unchanged, including Q12's [historical signing wording](signing-metadata-122/README.md).
No production signing, publication, firmware change, raw-device write or USB
flash occurred. This proves publisher-bound file identities and declared
provenance, not reproducibility, runtime safety, physical-media readback, boot
compatibility or erasure.

The operator authorized PR, required Blacksmith CI and merge. PR #86 is open;
its final required CI and merge/main-push results are pending at this receipt
update and must be observed before reporting completion. Review validation and
remote snapshots are preserved separately under
`%LOCALAPPDATA%\BeamoWipe\usb-download-125\20261002-hosted`; the original
local receipt and sealed audit remain unchanged.
No release republishing or historical description edit is needed for #125.
