# Release verification

Each release publishes a machine-readable manifest that links the ISO to its source, inputs, and evidence.

## Artifacts (per release)

| File | Purpose | Retention | Location |
| --- | --- | --- | --- |
| `beamo-wipe-0.2.12-amd64.iso` | Bootable live image (hybrid BIOS+UEFI) | Operator-defined after authorization | local `dist/` until separately published |
| `beamo-wipe-0.2.12-amd64.iso.sha256` | SHA256 sidecar (`<sha>  <name>`) | same | `dist/` alongside ISO |
| `beamo-wipe-0.2.12-amd64.manifest.json` | Release provenance (this doc) | same | `dist/` |
| `beamo-wipe-0.2.12-amd64.manifest.json.sha256` | Manifest checksum | same | `dist/` |
| `SHA256SUMS` | `sha256sum` of ISO + manifest | same | `dist/` |
| `beamo-wipe-0.2.12-amd64.img` | Desktop-readable FAT32 USB image with BIOS/UEFI boot | same | `dist/` after the USB-image builder |
| `beamo-wipe-0.2.12-amd64.img.sha256` | USB image checksum | same | alongside image |
| `beamo-wipe-0.2.12-amd64.img.json` | USB image size, layout, checksum, and source ISO checksum | same | alongside image |

The ISO artifacts are under `dist/` after `./scripts/build-iso.sh`. The hosted
QEMU phase also runs `./scripts/build-usb-image.sh` on its isolated amd64 Linux
worker. It boots the resulting `.img` through BIOS, UEFI, and enrolled Secure
Boot firmware. The publisher requires these USB boot logs and verifies the
image metadata against the actual image and source ISO before any upload.
These new image artifacts are development additions; they do not retroactively
change the previously published v0.2.5 release.

Current CI uses **Blacksmith** and retains evidence for seven days without
publishing binaries. See [CI](ci.md). The separately authorized manual
`.github/workflows/release.yml` reruns the full Linux gate on the exact tagged
main commit after its native Windows CI gate has passed. Its credential free
verification job transfers only hash checked image bytes and evidence to a
separate protected publisher job. That job obtains short lived credentials
for the dedicated GCP publisher only after transfer validation, signs the
manifest with the existing Secret Manager key, verifies each immutable GCS
object, and writes `RELEASE_COMPLETE.txt` last. It then checks every GitHub
draft asset's server SHA-256 before public promotion. GCP supplies the key and
storage, not CI compute.

## What the manifest contains

`dist/beamo-wipe-*.manifest.json` (`schema_version: 2`):

- `source`: `commit` (40-hex), `tag`, `dirty`/redacted `dirty_count`, `branch`, canonical `remote_url`
- `build`: content-addressed `debian:bookworm@sha256:…`, runner, `build_commands`, `built_at` UTC, `release_build_id` (UUID bound to the Blacksmith repository/run/attempt, historical Cloud Build UUID, or explicit `local` for development)
- Live image identity is the same payload written once to `/usr/share/beamo-wipe/build-identity.json` (`source_commit`, `source_sha256`, `build_id`, `source_dirty`). Runtime never infers commit from git. Missing or invalid identity is `unavailable`; dirty trees are `dirty`; `local` is `development`; a matching UUID is `production`. ISO format never implies a trusted wall clock.
- `dependencies`: `pyproject.toml`/`THIRD_PARTY.md`/`NOTICE` hashes, `live_build_inputs` (bootstrap/binary/package-lists/hooks/src hashes), `nwipe` (`version` `0.42`, `commit` `6082bde…`, `pinned_path`)
- `artifact`: `iso_name`, `iso_size_bytes`, `iso_sha256`, `iso_sha256_sidecar`
- `test_evidence`: measured gate results (see below), never script paths
- `installed_packages`: deterministic inventory of the image (see below)
- `hardware_limits`: supported/unsupported/degraded (from `docs/compatibility-matrix.md`), `known_issues`, `license` (wrapper GPL-3.0+, nwipe GPL-2.0), `prior_stable` (`0.2.11`, ISO SHA-256 `9694068e…`), `rollback`, `verification`

## Measured release evidence

`src/beamo_wipe/verification_evidence.py` is the schema owner. Every release
manifest records what was *executed*:

- **Gate receipts** (`beamo-wipe-gate-receipt/1`), one per gate: the executed
  command, status (`pass`/`fail`/`skip`), measured counts
  (`passed`/`failed`/`errors`/`skipped`/`xfailed`/`deselected`/`total`, with
  `total` equal to the sum of its parts), the sorted skip/xfail list with a
  reason per entry, the environment (stable facts only: platform, arch,
  toolchain versions, runner — never hostnames, users, paths, or secrets),
  second-precision UTC timestamps, the source commit and build identity, the
  SHA-256 of the immutable execution log, and a receipt digest over the
  canonical JSON. Receipts whose counts, digests, timestamps, or secrets
  checks fail are rejected as tampered.
- **Required vs optional gates.** Required: `lint`, `tests`, `preview`,
  `desktop-launchers`, `negative`, `iso`, `qemu` — all must be present with
  status `pass`, or verification fails (a skipped or failed required gate
  fails; a missing one fails as partial evidence). There are currently no
  optional gates. Unknown gate names are rejected so a renamed step cannot
  silently leave the record.
- **Installed-package inventory** (`beamo-wipe-package-inventory/1`): every
  installed package with name, version, architecture, and source-package
  provenance, sorted by name with a canonical digest, plus the image-level
  apt-source mirrors. dpkg status carries no per-package repository origin,
  so provenance is the source-package name plus the configured sources,
  stated as such. Two images compare by inventory digest first, source
  inputs second.
- **Fail-closed verification.** `verify_manifest` rejects manifests with
  unmeasured evidence, missing/failed/tampered receipts, evidence bound to
  another commit or build identity, or a missing/tampered package inventory.
  Generation in strict mode refuses to run without gate receipts and an
  inventory (`missing release evidence: …`).

The hosted gate automatically records execution through
`beamo_wipe.ci_evidence` into `dist/evidence/`. The test receipt counts actual
pytest JUnit outcomes; other required receipts count one executed phase,
not individual assertions. Every phase receives the same build ID; Blacksmith receipts also record the GitHub run and attempt.
The collector rejects stale files and binds receipts to retained log bytes.
The QEMU phase reads package provenance directly from the mounted ISO squashfs.

ISO construction first creates preliminary artifact provenance using
`verify_build_manifest`. It validates source identity and actual artifact
bytes but cannot claim future QEMU success. After QEMU passes, the collector
requires all seven passing receipts and the package inventory, finalizes the
manifest, and runs the strict `verify_manifest`. Preliminary provenance is
never accepted by that release verifier or by the publisher.

For individual evidence inspection, use the module CLI (run where each gate executes; the
JUnit XML comes from `pytest --junitxml`, whose hostname/timestamps/paths
are stripped by the parser and never enter the receipt):

```sh
python3 -m beamo_wipe.verification_evidence parse-junit \
  --gate tests --status pass --exec-command "python3 -m pytest" \
  --commit "$(git rev-parse HEAD)" --build-id "${BUILD_ID:-local}" \
  --xml tests.xml --log-sha256 "$(sha256sum tests.log | awk '{print $1}')" \
  --env platform=linux --env arch=x86_64 --env runner=blacksmith \
  --started-at 2026-09-11T00:00:00Z --ended-at 2026-09-11T00:05:00Z \
  --out receipts/tests.receipt.json
python3 -m beamo_wipe.verification_evidence parse-dpkg-status \
  --status-file "$SQUASH/var/lib/dpkg/status" \
  --collected-from "squashfs var/lib/dpkg/status" \
  --apt-source https://deb.debian.org/debian/ \
  --apt-source https://security.debian.org/ \
  --commit "$(git rev-parse HEAD)" --generated-at 2026-09-11T00:00:00Z \
  --out dist/beamo-wipe-0.2.12-amd64.packages.json
python3 -m beamo_wipe.verification_evidence verify-receipts \
  --receipt receipts/lint.receipt.json --receipt receipts/tests.receipt.json
```

Top-level `_manifest_sha256` is the SHA256 of the canonical JSON (sorted keys, no whitespace).

## Consumer verification

Use this order; a checksum match alone is not publisher authentication:

1. Obtain the release's `release-downloads.json` and `.sig`, the versioned
   `beamo-wipe-<version>-amd64.manifest.json` and `.sig`, and the artifacts
   you intend to use. Keep each document's exact downloaded bytes.
2. Authenticate the signing identity **before trusting those documents**.
   Use the current public registry from an independently trusted source
   checkout, confirm the full public-key fingerprint against the operator's
   independent announcement, and check its active/revoked/retired status.
   See [key distribution and custody](../packaging/release-keys/KEYS.md).
   A `keys.json` downloaded beside a signature cannot authenticate itself;
   neither can a key ID or fingerprint supplied only by that same download.
3. Verify each detached signature with that trusted registry and an explicit
   minimum accepted version. Missing, invalid or mismatched signatures stop
   verification. A successful result authenticates the exact signed bytes to
   that publisher key; it does not prove runtime safety or a wipe outcome.
4. Only then compare the actual downloaded sizes and SHA256 hashes with the
   authenticated inventory and manifest. The inventory covers the compressed
   USB download and other listed files; its raw `.img` entry applies after
   decompression. The manifest verifier below checks the sibling ISO and its
   recorded evidence. Checking an unauthenticated `.sha256` file alone is not
   a substitute for comparison with the authenticated documents.

### USB image download verification

Use this procedure for the **`.img.gz` download**, not the ISO. It checks the
compressed bytes before decompression, then the actual decompressed file's
size and hash. The signed inventory already lists both identities; the raw
`.img` need not be a separate downloadable asset.

This is a **versioned v0.2.12 example**, using the
[public release](https://github.com/BeamoTech/beamo-wipe/releases/tag/v0.2.12)
and source `e986419379f512f8088f5982ee02a51dc91a9dae`. For another release,
independently establish its tag/source commit and approved current signing
key before changing the three identity variables. Do not lower an acceptance
floor or substitute ISO hashes to make USB verification pass.

Prerequisites: Linux or macOS, a POSIX shell, `curl`, Python 3.10+ with the
repository's `cryptography` verification dependency, and an independently
trusted reviewed checkout containing `scripts/verify-usb-download.py`.
These commands verify files on macOS; they make no claim that the live image
boots an Apple Silicon Mac. Native Windows commands are not provided here.
Keep enough free space for both listed sizes (about 2.6 GiB for v0.2.12), plus
working headroom. No administrator privilege or raw device is needed.

**Authenticate the trust material first.** Obtain the current public registry
through the approved trusted checkout/update channel and confirm its full key
fingerprint with the operator's independent announcement. The
[versioned first-key ceremony record](https://github.com/BeamoTech/beamo-wipe/blob/e986419379f512f8088f5982ee02a51dc91a9dae/packaging/release-keys/KEYS.md)
explains this key's approval; an old record does not establish its current
revocation status. The verifier requires an active key in the current trusted
registry. A registry/fingerprint downloaded alongside the image cannot
authenticate itself. If you cannot establish that trust path, stop; a matching
hash alone does not establish publisher provenance.

After that independent check, edit only `BEAMO_SOURCE` to the **absolute** path
of your trusted checkout. Copy the whole block. It creates its own empty,
private working directory and uses explicit paths throughout; it does not
depend on the caller's current directory. The subprocess shell stops on any
failed command. Do not share or modify the working directory during verification.

<!-- USB-VERIFY-WALKTHROUGH-BEGIN -->
```sh
(
set -euC
BEAMO_SOURCE='/absolute/path/to/trusted/beamo-wipe'
BEAMO_VERSION='0.2.12'
BEAMO_COMMIT='e986419379f512f8088f5982ee02a51dc91a9dae'
BEAMO_KEY_SHA256='93caaf7ca93eff4d7fa1c16e360f9d6aa17ced0155a56d4cf89d8f6d429e66f7'
case "$BEAMO_SOURCE" in /*) ;; *) echo 'STOP: checkout path must be absolute' >&2; exit 1;; esac
test -f "$BEAMO_SOURCE/scripts/verify-usb-download.py" || {
  echo 'STOP: select the trusted checkout containing the USB verifier' >&2; exit 1;
}
BEAMO_USB_WORK="$(mktemp -d "${TMPDIR:-/tmp}/beamo-usb-verify.XXXXXXXX")"
BEAMO_USB_WORK="$(cd "$BEAMO_USB_WORK" && pwd -P)"
BEAMO_STEM="beamo-wipe-${BEAMO_VERSION}-amd64"
BEAMO_RELEASE_URL="https://github.com/BeamoTech/beamo-wipe/releases/download/v${BEAMO_VERSION}"
cd "$BEAMO_USB_WORK"
printf 'Private verification directory: %s\n' "$BEAMO_USB_WORK"

fetch_usb_file() {
  test ! -e "$BEAMO_USB_WORK/$1" && test ! -L "$BEAMO_USB_WORK/$1" || {
    echo 'STOP: download destination already exists' >&2; exit 1;
  }
  curl --fail --location --proto '=https' --proto-redir '=https' \
    --connect-timeout 15 --max-time 900 --silent --show-error \
    "$BEAMO_RELEASE_URL/$1" > "$BEAMO_USB_WORK/$1.part"
  ln "$BEAMO_USB_WORK/$1.part" "$BEAMO_USB_WORK/$1"
  rm "$BEAMO_USB_WORK/$1.part"
}
verify_usb_files() {
  python3 "$BEAMO_SOURCE/scripts/verify-usb-download.py" "$1" \
    --directory "$BEAMO_USB_WORK" \
    --registry "$BEAMO_SOURCE/packaging/release-keys/keys.json" \
    --trusted-key-sha256 "$BEAMO_KEY_SHA256" \
    --version "$BEAMO_VERSION" --expected-source "$BEAMO_COMMIT"
}

fetch_usb_file 'release-downloads.json'
fetch_usb_file 'release-downloads.json.sig'
fetch_usb_file "$BEAMO_STEM.manifest.json"
fetch_usb_file "$BEAMO_STEM.manifest.json.sig"
fetch_usb_file "$BEAMO_STEM.img.json"
verify_usb_files metadata
fetch_usb_file "$BEAMO_STEM.img.gz"
verify_usb_files extract
verify_usb_files verify
printf 'Verified regular file, not yet written to media: %s/%s.img\n' "$BEAMO_USB_WORK" "$BEAMO_STEM"
)
```
<!-- USB-VERIFY-WALKTHROUGH-END -->

Expected sequence: `AUTHENTICATED metadata` identifies the exact tag, source
commit and build; `EXPECTED` lists the compressed/raw filenames, sizes and
SHA256 values; `VERIFIED compressed USB download` precedes decompression;
`VERIFIED raw USB image` appears only after the raw file matches. The separate
final `verify` rechecks both regular files without extracting again. Every
stage authenticates the inventory and manifest signatures before using their
hashes. The image metadata must itself match the signed inventory and bind
the raw image to the ISO identity recorded by the signed manifest. This does
not claim that the ISO bytes were downloaded or verified by this procedure.

Missing/invalid signatures, altered metadata, wrong source/version/build,
missing size/hash fields, or mismatched compressed/raw bytes produce `STOP`
and a nonzero exit. Wrong directories and symlink/special-file inputs are
rejected. Extraction refuses any existing `.img` or `.img.partial`, bounds
decompression by the authenticated raw size, and publishes `.img` without
overwriting only after successful verification. Interrupted/failed downloads
retain `.part`; failed extraction may retain `.img.partial`. Neither is a
verified image. Start over in a new empty directory after a failure; never
rename a partial file or bypass a failed check. `verify` is the mode for
rechecking an already complete image, not `extract`.

**Stop before writing media.** Successful verification authenticates these
exact bytes to the approved publisher key and ties them to one signed release
source/build identity. It does not prove runtime safety, firmware compatibility,
successful erasure, or that a selected physical disk is safe to overwrite.
The printed `.img` is a regular file; this procedure performs no media write.

### ISO verification

The following checks concern the separate `.iso`, not the USB `.img.gz` or
`.img`. An ISO hash must never stand in for either USB-image hash.
Run these commands from a trusted source checkout with release files together
under `dist/`. The examples use 0.2.12; choose the intended release and an
appropriate acceptance floor, rather than lowering it to make a check pass.

```sh
# After independently authenticating the current registry:
set -eu
PYTHONPATH=src python3 -m beamo_wipe.release_signing verify \
  --manifest dist/release-downloads.json \
  --signature dist/release-downloads.json.sig \
  --registry packaging/release-keys/keys.json --min-version 0.2.12
PYTHONPATH=src python3 -m beamo_wipe.release_signing verify \
  --manifest dist/beamo-wipe-0.2.12-amd64.manifest.json \
  --signature dist/beamo-wipe-0.2.12-amd64.manifest.json.sig \
  --registry packaging/release-keys/keys.json --min-version 0.2.12

# STOP if either signature check fails. After comparing the actual downloads
# with the authenticated inventory, these are additional corruption checks.
# Each checksum sidecar uses a bare filename, so run from dist/:
(cd dist && sha256sum -c beamo-wipe-0.2.12-amd64.iso.sha256)
(cd dist && sha256sum -c beamo-wipe-0.2.12-amd64.manifest.json.sha256)
(cd dist && sha256sum -c SHA256SUMS)

# From a checked-out v0.2.12 source tree, place the downloaded release files
# together under dist/, then verify the manifest and sibling ISO (fails closed
# on dirty/placeholder, path escape, size, content, or sidecar mismatch):
python3 - <<'PY'
import pathlib, sys
sys.path.insert(0, "src")
from beamo_wipe.release_manifest import verify_manifest
verify_manifest(pathlib.Path("dist/beamo-wipe-0.2.12-amd64.manifest.json"))
print("manifest OK")
PY

# Inspect provenance without trusting ISO:
python3 -m json.tool dist/beamo-wipe-0.2.12-amd64.manifest.json | head -n 60
# Check source commit matches tag:
git rev-parse HEAD  # should equal manifest source.commit
git status --porcelain  # should be clean for a release
```

`verify_manifest` requires the manifest to record only the canonical bare ISO filename, resolves that file beside the manifest, hashes the actual bytes, checks its size, and validates both exact sidecar lines. This makes the release directory relocatable without accepting an embedded absolute path or traversal. If any check fails, do not use the ISO.
It does not verify a publisher signature; the preceding detached-signature
checks are required for authentication.

## Build failure (fail-closed)

`scripts/generate-release-manifest.sh` and `src/beamo_wipe/release_manifest.py` abort (exit 2) on:

- `git status --porcelain` not empty (unless `ALLOW_DIRTY=1`)
- `git rev-parse HEAD` not 40-hex
- `PLACEHOLDER`/`TODO`/`CHANGEME` in `src/beamo_wipe/__init__.py` or live-build `binary`
- Missing ISO or `sha256_file` empty
- `NWIPE_PINNED_VERSION != "0.42"` or `commit` not 40-hex
- `pyproject.toml` version drift vs `__version__`
- Manifest/ISO sidecar mismatch, ISO path traversal, ISO byte/size mismatch, or unexpected origin URL

## Immutability and publisher signatures

- **Immutability:** Verification output is ephemeral by default. Explicit publication uses a unique build UUID path, generation-match-zero uploads, remote byte verification, and a completion marker written last. The bucket also provides seven-day soft deletion; release paths are never reused.
- **Signing:** New publication through this publisher requires a detached Ed25519 sidecar
  (`beamo-wipe-<version>-amd64.manifest.json.sig`) over the exact manifest
  bytes, so one signature covers the artifact hashes, build identity,
  evidence/receipt hashes, and version metadata together. The publisher
  signs after manifest verification and verifies the sidecar before upload;
  without signing material, or against a retired/revoked key, publication
  refuses instead of publishing unsigned. SHA256 alone detects corruption
  but does not authenticate the publisher: do not treat an unsigned image
  as an authenticated release. This publisher has no unsigned-publication
  override.

The manifest generator and download-inventory generator share the same
detached-verification guidance: `signing`, `signature_file`,
`signature_algorithm`, `verification_order` and `signature_command`.
These fields describe a verification contract, **not a signed-status flag**.
The manifest is generated before signing; local or signing-skipped builds
remain unauthenticated without a valid external sidecar. The publisher signs
and verifies the exact completed bytes without rewriting them afterward.
The inventory likewise uses `release-downloads.json.sig` over its exact bytes.
No signature is embedded in either document. Verification commands assume a
trusted checkout and downloaded documents in `dist/`.

The published v0.2.12 manifest contains an obsolete generated
"not configured" sentence even though its detached signature verifies.
Those signed bytes are a historical record and must not be edited or re-signed
to repair prose. See the [#122 verification receipt](evidence/signing-metadata-122/README.md).

### What release signing is not (Secure Boot distinction)

Release signing is **not Secure Boot**. It proves *who published this file*
(the Beamo release key held by the operator). It does not prove what a
machine may boot, confer firmware trust, bless image contents beyond their
hashes, or say anything about a wiped disk. The inspected 0.2.12 x64 path uses
Microsoft-signed Debian shim and Debian-signed GRUB/kernel; it does not use
the Beamo release key for firmware trust. Its initrd and live filesystem are
outside that PE signature chain. Reinspect every new candidate's actual boot
components and apply [the physical trust/revocation cases](secure-boot-acceptance.md).
We ship no circumvention tools (see `docs/claims.md`). A valid
publisher signature never means "safe to boot without checking firmware",
and a Secure Boot refusal never means "the download was tampered with".

### Threat model and limitations

- **Stops:** silent substitution of ISO/manifest bytes in transit or at
  rest (digest mismatch fails), publication by anyone without the release
  key, replay of an older signed release as current (acceptance floor),
  use of a retired or compromised key after revocation.
- **Does not stop:** compromise of the release key *before* revocation
  (mitigated by custody rules and fast revocation), a malicious publisher
  with legitimate access (mitigated by clean-tree/tag/record review, never
  by cryptography), attacks on the downloader's machine, or weak
  out-of-band fingerprint checks. Signatures authenticate the publisher,
  not the wipe result.

### Key custody, rotation, revocation (summary)

Full ceremony lives in `packaging/release-keys/KEYS.md`. In short: private
material exists only in the operator's offline ceremony record and one
Secret Manager secret readable by the release identity alone; it is never
committed, printed, or attached to pull-request builds. Current `ci.yml` and
the retained legacy `cloudbuild.yaml` stay secret-free by policy (pinned by
tests); neither is the protected `release.yml` publisher. A pull request can
rewrite build configuration. Rotation keeps both keys active for at most one release,
then retires the predecessor. Revocation is a committed status change that
fails verification even for cryptographically valid signatures; never
delete a revoked entry. Production key creation and rotation need separate
operator authorization — code and tests only ever use ephemeral keys.

### Verify a release signature (copyable)

Use the ordered, copyable commands in [Consumer verification](#consumer-verification).
Expected success for each document: `accepted version 0.2.12 key <16-hex-key-id>`.
Expected failures (each raises `RuntimeError`, never a partial pass):

- altered manifest or sidecar bytes → `digest mismatch` / `different manifest bytes` / `signature is invalid`
- wrong verification key → `not a known publisher key` / `different key`
- missing sidecar or registry entry → `not a known publisher key` / `cannot be read`
- retired key → `is not active (retired)`; compromised key → `is revoked`
- older signed release against the floor → `below the acceptance floor`

Or use the CLI: `python3 -m beamo_wipe.release_signing verify --manifest … --signature … --registry … --min-version 0.2.12`.

## Reproducibility

Live-build is not bit-reproducible due to `apt` timestamps and `squashfs` ordering; the manifest records `live_build_inputs` hashes and `container_image` for traceability, not for `diff` equality. Use `iso_sha256` + `source.commit` as the release identity.

## Prior stable and rollback

Prior stable: `beamo-wipe-0.2.11-amd64.iso` `9694068e4d70824b316f12da9bd4c0ee964809d15ce5ad4d406333f710176305` commit `662cf470f9fcedf710d897591560267575745fea` tag `v0.2.11`. Rollback: use the signed `v0.2.11` release or `git checkout 662cf470f9fcedf710d897591560267575745fea`. The 0.2.0 ISO (`62437ec…` / `5b3b7afa…`) remains a historical GitHub artifact; it is not the branded rollback target.

Never publish or promote the ISO without explicit operator authorization after the full Blacksmith `CI gate` passes for the exact source commit and artifact hashes.
