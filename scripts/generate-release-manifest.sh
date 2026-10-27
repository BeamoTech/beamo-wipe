#!/bin/sh
# Generate machine-readable release manifest. Fails closed on dirty/placeholder.
set -eu
ROOT="$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
VERSION="${BEAMO_WIPE_VERSION:-0.2.14}"
DEST="${1:-dist/beamo-wipe-${VERSION}-amd64.manifest.json}"
EXPECTED_DEST="dist/beamo-wipe-${VERSION}-amd64.manifest.json"
case "$VERSION" in
  ''|*[!0-9.]*|.*|*..*|*.) echo "ERROR: invalid BEAMO_WIPE_VERSION" >&2; exit 2 ;;
esac
if [ "$(printf '%s' "$VERSION" | awk -F. '{print NF}')" -ne 3 ] || [ "$DEST" != "$EXPECTED_DEST" ]; then
  echo "ERROR: invalid version or out-of-tree manifest destination" >&2
  exit 2
fi

# Fail on uncommitted state unless explicitly allowed for local dev
if [ "${ALLOW_DIRTY:-0}" != "1" ]; then
  if ! source_status="$(git status --porcelain)"; then
    echo "ERROR: could not determine source checkout state" >&2
    exit 2
  fi
  if [ -n "$source_status" ]; then
    echo "ERROR: uncommitted source state (git status --porcelain not empty)" >&2
    echo "Commit the audited paths, or set ALLOW_DIRTY=1 for a local non-release build" >&2
    exit 2
  fi
fi

# Generate via Python. Values cross the shell->Python boundary through the
# environment, never through source interpolation: the heredoc is quoted so
# a crafted BEAMO_WIPE_VERSION cannot break out into Python exec.
BEAMO_WIPE_MANIFEST_VERSION="$VERSION" BEAMO_WIPE_MANIFEST_DEST="$DEST" python3 - <<'PY'
import json, os, pathlib, sys
sys.path.insert(0, "src")
from beamo_wipe.release_manifest import generate_manifest, write_manifest, require_verified_prior_checksum_list, _open_regular_nofollow, _atomic_write, sha256_file
from beamo_wipe.ci_evidence import load_receipts
strict = os.environ.get("ALLOW_DIRTY") != "1"
build_only = os.environ.get("BEAMO_BUILD_PROVENANCE_ONLY") == "1"
inputs = {}
if not build_only:
    evidence = pathlib.Path("dist/evidence")
    inputs["gate_receipts"] = load_receipts(evidence)
    with os.fdopen(_open_regular_nofollow(evidence / "packages.json"), "rb") as stream:
        raw_inventory = stream.read(32 * 1024 * 1024 + 1)
    if len(raw_inventory) > 32 * 1024 * 1024:
        raise RuntimeError("package inventory exceeds the safety limit")
    inputs["package_inventory"] = json.loads(raw_inventory)
manifest = generate_manifest(version=os.environ["BEAMO_WIPE_MANIFEST_VERSION"], strict=strict,
                             build_only=build_only, **inputs)
dest = pathlib.Path(os.environ["BEAMO_WIPE_MANIFEST_DEST"])
# Bind the verified prior list (or absence) before rewriting the manifest it
# authenticates. Keep that snapshot in this transaction through publication.
checksum_snapshot = require_verified_prior_checksum_list(dest.parent)
out = write_manifest(manifest, dest)
# Always verify: with ALLOW_DIRTY only the dirty-state check is skipped, every
# other structural check (checksum, placeholders, nwipe pin, ISO checksum)
# still runs so a dirty-tree manifest cannot pass as clean provenance.
from beamo_wipe.release_manifest import verify_manifest, verify_build_manifest
if build_only:
    verified_manifest = verify_build_manifest(out, allow_dirty=not strict)
else:
    verified_manifest = verify_manifest(out, allow_dirty=not strict)
print(f"Verified {out} (strict={strict})")
import hashlib
manifest_sha = hashlib.sha256(verified_manifest).hexdigest()
print(f"Manifest SHA256: {manifest_sha}")
sidecar = pathlib.Path(str(out) + ".sha256")
print(f"Sidecar written: {sidecar.name}")
iso = dest.parent / manifest["artifact"]["iso_name"]
_atomic_write(
    dest.parent / "SHA256SUMS",
    f"{sha256_file(iso)}  {iso.name}\n{manifest_sha}  {out.name}\n".encode("ascii"),
    expected=checksum_snapshot,
)
PY

echo "Manifest written: $DEST (verifying checksums below)"
ls -lh "$DEST" "${DEST}.sha256"
# Verify checksum publication (from dist/ directory so sidecar's bare filename resolves).
# No `| head` on verify lines: under set -eu without pipefail the pipeline's
# status would be head's, and a mismatch would still print success and exit 0.
( cd "$(dirname "$DEST")" && sha256sum -c "$(basename "${DEST}.sha256")" )
# Also ensure ISO sidecar exists and verifies
ISO="dist/beamo-wipe-${VERSION}-amd64.iso"
if [ -f "$ISO" ]; then
  if [ ! -f "${ISO}.sha256" ]; then
    ISO_SUM_TMP="$(mktemp "$ROOT/dist/.iso-sha.XXXXXX")"
    trap 'rm -f -- "$ISO_SUM_TMP"' EXIT
    trap 'exit 130' HUP INT TERM
    ( cd "$(dirname "$ISO")" && sha256sum "$(basename "$ISO")" > "$ISO_SUM_TMP" )
    python3 -c '
import os, stat, sys
source, destination = sys.argv[1:]
directory_fd = os.open(os.path.dirname(destination), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
try:
    source_name = os.path.basename(source)
    staged = os.stat(source_name, dir_fd=directory_fd, follow_symlinks=False)
    if not stat.S_ISREG(staged.st_mode) or staged.st_uid != os.getuid():
        raise SystemExit("unsafe staged ISO checksum")
    try:
        os.link(source_name, os.path.basename(destination),
                src_dir_fd=directory_fd, dst_dir_fd=directory_fd, follow_symlinks=False)
    except FileExistsError as exc:
        raise SystemExit("unsafe existing ISO checksum sidecar") from exc
    os.fsync(directory_fd)
finally:
    os.close(directory_fd)
' "$ISO_SUM_TMP" "$ROOT/${ISO}.sha256"
    rm -f -- "$ISO_SUM_TMP"
    trap - EXIT HUP INT TERM
  fi
  ( cd "$(dirname "$ISO")" && sha256sum -c "$(basename "${ISO}.sha256")" )
  # The Python transaction published against its verified pre-rewrite snapshot.
  ( cd dist && sha256sum -c SHA256SUMS )
  echo "Manifest generation does not sign: authenticate the publisher key and verify detached signatures first (docs/release-verification.md)."
  echo "Then compare downloaded artifact hashes with the authenticated manifest/inventory; checksum sidecars alone do not authenticate them."
  echo "Additional checksum check: sha256sum -c SHA256SUMS (from dist/)"
else
  # Fail closed: a manifest that links to an ISO that was not produced must
  # never exit 0 (normally unreachable — iso_info already fails above — but
  # must stay fail-closed if generation semantics ever change).
  echo "ERROR: ISO $ISO not found but the manifest links to it; refusing to publish" >&2
  exit 2
fi
