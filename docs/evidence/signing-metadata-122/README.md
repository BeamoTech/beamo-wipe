# Accurate detached-signing metadata — #122

2026-09-29, Codex. Local implementation and verification only. No production
key was accessed, no production signing occurred, and no published document,
signature, checksum, asset, tag or release description was changed.

## Public baseline verified before editing

The current public release was [v0.2.12](https://github.com/BeamoTech/beamo-wipe/releases/tag/v0.2.12),
release ID `398337215`, source `e986419379f512f8088f5982ee02a51dc91a9dae`.
Only the small manifest, download inventory, detached signatures and public
registry were downloaded. No ISO/USB image was downloaded or exercised.

| Public document | SHA256 of exact signed bytes |
| --- | --- |
| `beamo-wipe-0.2.12-amd64.manifest.json` | `0bb56538500330086f507538e94ec68846ff5ab39ddf491dbeaf467a50cfd5b8` |
| `release-downloads.json` | `2023d3aa84a84f406a1d0f0b230d38293eb1b74275cf068088408209a296511c` |

Both detached signatures verified with `verify_release_acceptance`, minimum
version 0.2.12, against the repository's current public registry. The active
key ID is `93caaf7ca93eff4d`, full public fingerprint
`93caaf7ca93eff4d7fa1c16e360f9d6aa17ced0155a56d4cf89d8f6d429e66f7`.
The trust path was the approved first-key record in
[KEYS.md](../../../packaging/release-keys/KEYS.md), its documented independent
announcement to the owner, and the trusted checkout's active public registry.
The downloaded registry matched that registry byte-for-byte; it was not used
as a self-authenticating trust anchor. No new independent human identity
ceremony was conducted by this task.

After authenticating the inventory, its manifest/signature hashes were also
matched against the downloaded files. This establishes authentication of
those documents, **not verification of the large image bytes or runtime
safety**. [Public verification receipt](public-verification.json) records
exact URLs, hashes, source identity and successful key/version results.
[The second read](historical-invariance.json) confirmed the public description
and all 16 asset metadata records stayed unchanged; downloaded historical
bytes still match their original hashes.

## Root cause and correction

`release_manifest.generate_manifest()` unconditionally emitted:

> not configured; SHA256 detects corruption but does not authenticate the publisher

This was not a configuration probe. The real publisher subsequently signs
the exact manifest bytes and verifies the detached sidecar before uploading.
Consequently the inaccurate prose itself became part of a valid signature.
The prior consumer-instructions test even allowed the obsolete phrase and
was skipped when a historical manufacturing ISO was absent.

One shared `release_signing.detached_verification_metadata()` now generates
guidance for both the manifest and `release-downloads.json`, before either
document is signed. It supplies `signing`, `signature_file`,
`signature_algorithm`, `verification_order` and `signature_command`.
Existing string fields and schema versions remain compatible; these are
additive descriptive fields, not new authentication or signed-status flags.

The exact new `signing` wording for a generated manifest is:

> Published releases require a detached Ed25519 signature in beamo-wipe-0.2.12-amd64.manifest.json.sig over the exact bytes of this document; no signature is embedded here. Generation alone does not sign or authenticate a build. Without a successfully verified sidecar, including when signing is skipped, treat it as unauthenticated. SHA256 checksums alone do not authenticate the publisher. A valid signature authenticates these bytes to the trusted publisher key; it does not prove runtime safety, firmware compatibility or successful erasure.

The filename/version are generated, not fixed at 0.2.12. Inventory guidance
names `release-downloads.json.sig`. The generated verification command uses
the trusted checkout's public registry and an explicit version floor.
Metadata never asserts that a signature exists or that signing ran: this
avoids falsely labeling a build signed before the publisher has completed.
Unsigned/signing-skipped builds have no verified sidecar and fail the same
signature command. Existing publisher refusal without a key, with a revoked
key, with skipped gates, or with a stale sidecar remains unchanged.

[Consumer verification](../../release-verification.md#consumer-verification)
and the shell generator's printed guidance now order the steps explicitly:
obtain documents/sidecars → authenticate the key identity and current status →
verify detached signatures → verify actual artifact sizes/hashes. The copyable
commands stop on error. `verify_manifest()` remains structural/artifact
verification, not a replacement for publisher-signature verification.

Release notes are supplied directly by `docs/release-<version>.md`; the
existing v0.2.11/v0.2.12 wording about a signed manifest/inventory is already
consistent. Neither those historical notes nor the signing workflow or public
key registry needed alteration. Already-published signed bytes retain their
historical inconsistent sentence; the current verification guide documents
that separately instead of repairing or re-signing old files.

## Tests and generated sample

Tests use regular files and freshly generated in-memory Ed25519 test keys.
No private test material is committed, written by the new fixtures or printed.
Public test key IDs/fingerprints are safe diagnostic identities.
Local execution used macOS arm64, Python 3.10 and cryptography 49.0.0; this is
not the pinned production signing environment (cryptography 50.0.1).

- New regression run against the **original generator in memory**: expected
  failure on `not configured`. No working-tree implementation was replaced.
- Focused generator/signing/manifest/Blacksmith/publisher/sidecar-parent
  suites: **85 passed, 12 skipped in 1.78 s**. The 12 skips require an absent
  historical manufacturing ISO. All new cases execute without that ISO.
- New tests cover unsigned and build-only output, actual sidecar writing
  without manifest mutation, generated CLI verification, missing signature,
  invalid signature, stale source/manifest bytes, harmless whitespace
  tampering, revoked key, signing-skipped publication and safe command inputs.
- The existing signed-inventory fixture now checks the shared metadata and
  verifies its signature, including the added guidance bytes.
- [Generated sample identity](generated-sample.json): manifest SHA256
  `0d1154ef0ce9d1d620d61fdffcdc9d2a50fabfe3b0a07c26feb623163e3edf54`,
  test public fingerprint
  `5c6fc4d5890855048dd83ced99b4158ad717957240a80f94a686f04f427cd794`.
  Its source is deliberately the fake `aaaa…` fixture identity, not a qualified
  build. Verification succeeded; appending one space was rejected with
  `signature sidecar is for different manifest bytes`. The sample's temporary
  directory was removed normally; the public identities and guidance remain
  in the receipt.
- Full local fake-device suite: **4,629 passed, 701 skipped, 2 failed in
  461.52 s**. Both failures are unavailable macOS `gi`/ATK imports:
  `test_what_screen_keeps_title_and_shows_this_usb_line` and
  `test_assist_nav_names_do_not_rewrite_result_heading`. All ten new metadata
  cases present at that run passed. The eleventh case (signing-skipped
  publication) was added afterward and passed in the final focused run.
  [Test receipt](test-results.json) preserves counts, failures and log hashes.
- Ruff source/tests/tooling and security selections, prescribed formatting,
  mypy (50 files), compileall, ShellCheck, actionlint and final diff checks pass.
- Both updated guidance documents rendered locally with markdown-it; relative
  file/anchor checks passed. No public documentation edit was made.

Commands included `BEAMO_WIPE_DRY_RUN=1 python3 -m pytest` on the named
focused suites, `./scripts/test-all.sh`, public-only
`verify_release_acceptance`, generated `release_signing verify` commands,
`python3 -m ruff check`, `ruff format --check`, `mypy --ignore-missing-imports`,
`compileall`, `shellcheck` and `actionlint`. Logs and JUnit are disposable
under `/private/tmp/beamo-wipe-122`; durable identities/results are recorded
here. No hosted workflow, publisher upload or physical hardware test ran.

## Source and remaining release work

Base: `7e8603d588502fedce9206a735f924398d59b260`.
Local branch: `codex/signing-metadata-122`. The commit containing this receipt
identifies the final change (`git log -1 --format=%H --
docs/evidence/signing-metadata-122/README.md`). Unrelated primary-checkout
edits and the separate #119/#120/#121 work remain preserved.

The next authorized release must be built and qualified from its own reviewed
source revision, generate new manifests/inventory, then sign those exact new
bytes through the existing protected publisher. Hosted qualification, tagging,
production signing and publication remain separate consequential steps, none
performed by this task. No historical release repair is needed or authorized.
