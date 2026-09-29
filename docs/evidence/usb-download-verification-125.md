# Downloaded USB-image verification — #125

2026-09-29, Codex. Base `cd5e771b1e28f184979bdfab792828614a71df38`;
branch `codex/usb-download-verification-125`. The commit containing this
receipt identifies the exact implementation (`git log -1 --format=%H --
docs/evidence/usb-download-verification-125.md`). Prior task commits and
unrelated primary-checkout edits remain preserved.

## Change and trust boundary

The consumer guide previously explained signed inventory verification but
gave executable artifact-verification commands for the ISO. It did not give
an end-to-end compressed USB-download procedure. The new versioned example
in [release verification](../release-verification.md#usb-image-download-verification)
uses the actual v0.2.12 filenames and source identity. It creates a fresh
private directory, authenticates metadata before trusting hashes, verifies
the compressed size/hash, extracts to a regular file, verifies raw size/hash,
and stops before any media write. ISO verification remains separate.

`scripts/verify-usb-download.py` reuses the existing Ed25519 registry and
detached-signature verifier. Both inventory and manifest signatures must
verify under an active key whose full fingerprint matches the independently
authenticated fingerprint argument. The current registry must come from a
trusted reviewed checkout/update channel; the approved first-key record and
operator's independent announcement establish the intended trust procedure.
This task verified against the existing checkout registry, not a newly
performed human key ceremony. Downloading a registry with the artifacts is
not independent authentication.

The helper binds the exact version, clean source commit/tag, canonical remote
and build UUID across signed documents. It also authenticates `.img.json`
through the inventory and checks its raw-image and source-ISO identities.
It does not claim to execute release evidence, download the ISO, prove runtime
safety, validate firmware, select a disk, or prove an erase result.

All input filenames used for I/O are constructed from the explicit version,
never from metadata paths. Metadata reads use the existing bounded regular-file
reader. Image inputs must be regular files opened without following symlinks;
nonblocking open permits rejecting a FIFO rather than waiting on its writer.
Extraction refuses existing final/partial output, creates a private exclusive
partial file, caps output at the authenticated raw size, fsyncs and hashes the
written bytes, then publishes with a no-overwrite hard link. Failure cannot
publish a new verified `.img`; partial files stay clearly named. The directory
must not be concurrently modified. This is not protection against another
malicious process already running as the same user.

Downloads require HTTPS including redirects, have 15-second connection and
900-second transfer limits, and use noclobber `.part` files. The instructions
say to start over in a new empty directory after failure. The helper performs
no network operation, signing operation, raw-device write, or media flashing.

## Public release evidence

Read-only GitHub API inspection identified release **398337215**,
[v0.2.12](https://github.com/BeamoTech/beamo-wipe/releases/tag/v0.2.12),
published `2026-09-28T14:37:13Z`. The peeled local tag and authenticated
manifest agree on source **e986419379f512f8088f5982ee02a51dc91a9dae**;
the signed inventory/manifest agree on build
**625971a4-afef-5398-9bec-d96455192ab3**.

Public inventory and manifest signatures successfully verified with active
key `93caaf7ca93eff4d`, full fingerprint
`93caaf7ca93eff4d7fa1c16e360f9d6aa17ced0155a56d4cf89d8f6d429e66f7`.
The freshly downloaded inventory, signature, manifest, manifest signature,
and image metadata passed the new helper's `metadata` mode.

| Artifact | Authenticated bytes | Authenticated SHA-256 |
| --- | ---: | --- |
| `beamo-wipe-0.2.12-amd64.img.gz` | 601441384 | `a3d2a65d8941facbd30b794b083419dc694511903281e57cd028db565bdc1972` |
| `beamo-wipe-0.2.12-amd64.img` | 2147483648 | `1e807895ee643a35d90a0c2302143f02b01de91aec564a3972d86740c55ae10b` |
| `beamo-wipe-0.2.12-amd64.img.json` | 356 | `e1ad82cf060b9d1a1424e19ff989e7ad2db10c2c5f414f8dbf3697107c155d37` |

These image identities were read from authenticated metadata; they are **not
a claim of hashing the complete public image locally**. The public compressed
asset's GitHub ID is `595626632`; its API size and SHA-256 digest agree with
the signed inventory. All smaller downloaded metadata bytes were measured.
The adjacent [result receipt](usb-download-verification-125-results.json)
records their identities and the separate test-fixture identities.

There is **no missing compressed/raw metadata field** in this release.
Inspection of `scripts/prepare_release_assets.py`, the USB-image builder,
Blacksmith publisher and release workflow confirms both records are generated
before inventory signing. The existing generator test now explicitly asserts
both sizes as well as both hashes. No invented identity or generator schema
change was necessary.

## Executed verification and limitations

Host: macOS 26.6.2 arm64, Python 3.10.0, cryptography 49.0.0. The repository
pins cryptography 50.0.1; this is local functional evidence, not execution of
the pinned hosted environment. Linux execution is **NOT TESTED** here; native
Windows commands are intentionally not documented. No real disk was written.

```sh
python3 -m pytest -p no:cacheprovider -o addopts='' \
  tests/test_usb_download_verification.py tests/test_blacksmith_release.py \
  tests/test_release_signing.py
BEAMO_WIPE_DRY_RUN=1 PYTEST_ADDOPTS='-p no:cacheprovider' \
  ./scripts/test-all.sh -o addopts='' \
  --basetemp=/private/tmp/beamo-wipe-125-full-isolated \
  --junitxml=/private/tmp/beamo-wipe-125-full-isolated.xml
```

- Focused tests: **50 passed** (22 new USB cases); final run 9.76 seconds.
- The exact Markdown shell block ran from an unrelated directory against
  disposable signed non-production fixtures, including a trusted checkout
  path containing spaces. It authenticated metadata, verified the 80-byte
  compressed fixture, extracted/verified the 3600-byte regular image, then
  independently rechecked both files. No private test key was written.
- Negative coverage: changed inventory bytes, invalid/missing signatures,
  wrong/revoked key, compressed corruption, raw corruption, missing raw
  record/size, inconsistent build/source, traversal metadata, wrong raw hash,
  expansion beyond authenticated size, bad gzip/DEFLATE data, stale final or
  partial output, symlink input, and wrong/relative working directory.
- The first full run had **4684 passed, 703 skipped, 3 failed** in 687.14 s.
  The failures were unchanged fake-nwipe tests reaching their short startup/
  progress deadlines. A module rerun still had two timeouts; the same complete
  module then passed **53 tests in 4.41 s** using an isolated `/private/tmp`
  base. No production runner or its test assertions were changed. Both failed
  runs remain recorded rather than being hidden by the rerun.
- Final isolated full suite: **4687 passed, 703 skipped, zero failures or
  errors, 990.42 s**. All 22 USB cases executed. The 703 skips are local
  platform/dependency/environment checks; this is not hosted qualification.
- Prescribed compileall, Ruff/full security selections, developer-tool format
  checks, mypy (50 source files), ShellCheck, actionlint and diff checks passed.
  The new helper's help command and Ruff checks passed; the exact copied shell
  block passed `sh -n` and ShellCheck as POSIX sh.
- Local CommonMark rendering confirmed the new section's two links are
  absolute, with the same destinations under repository and release base
  URLs. Both returned HTTP 200 without changing destination. The key ceremony
  link is pinned to the release source commit; neither link has an anchor.

The complete public-image walkthrough is **NOT TESTED**: a direct download
failed with curl HTTP/2 error 92 after 42,022,497 bytes. Bounded HTTP/1.1 and
public API probes also timed out. Bounded range attempts checked response
ranges/lengths but remained incomplete and were stopped. No partial download
was accepted, renamed to a verified image or decompressed. Task-owned partials
and range staging were removed after recording failure evidence. This network
limitation must not be described as successful full public-artifact validation.

Read-only before/after release comparison found identical release ID, tag,
description, and every asset's ID, size, digest and update timestamp. Historical
release notes, signed bytes, checksums, signatures, tags and public assets were
not modified. No hosted CI, push, tag, merge, publication or production signing
was performed. Remaining checks: complete the public `.img.gz`/raw walkthrough
when transport is reliable and execute the documented Linux path. Publishing
the source/docs requires the normal reviewed merge and separately authorized
remote actions; no public release-description patch is needed for this task.

Required storage reports ran before and after the large-download attempt.
After recording logs/JUnit and source hashes, the two completed task-owned
pytest base directories were removed through normal temporary-fixture cleanup.
No unrelated storage was removed. Compact evidence remains in this receipt;
full logs/JUnit remain disposable under `/private/tmp/beamo-wipe-125-*`.
