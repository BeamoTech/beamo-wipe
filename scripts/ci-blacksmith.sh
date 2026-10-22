#!/usr/bin/env bash
# Secret-free verification on a disposable Blacksmith x86_64 worker.
set -euo pipefail
ROOT="$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
IMAGE=debian:bookworm@sha256:6ebd97fa83deb272194a2cf015b3d26a4d538e9ad3a7a79d544c8af5b0a01443

if [[ "${GITHUB_ACTIONS:-}" != true || "$(uname -sm)" != 'Linux x86_64' ]]; then
  echo 'Requires an isolated Blacksmith x86_64 GitHub Actions worker.' >&2
  exit 2
fi
: "${GITHUB_RUN_ID:?}" "${GITHUB_RUN_ATTEMPT:?}" "${GITHUB_REPOSITORY:?}"
export BUILD_ID
BUILD_ID="$(python3 - <<'PY'
import os, uuid
identity = '/'.join(os.environ[k] for k in ('GITHUB_REPOSITORY', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT'))
print(uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/' + identity))
PY
)"

phase() {
  local gate="$1"
  local options=()
  local private_sources=0
  # Same absolute checkout path inside/outside the container is essential:
  # the ISO builder talks to the sibling Docker daemon using bind mounts.
  if [[ "$gate" == iso ]]; then
    options+=(-v /var/run/docker.sock:/var/run/docker.sock)
  elif [[ "$gate" == qemu ]]; then
    bash scripts/check-ci-kvm.sh
    # Needed for private file-backed loop mounts. Never bind host /dev;
    # qemu-verify.sh independently refuses /dev/ in every guest drive argv.
    options+=(--privileged)
  else
    # A bind-mounted checkout keeps the runner's uid and host filesystem
    # timestamp behavior inside this root container.  Security tests must
    # exercise ordinary, container-owned files so ownership and change-time
    # checks describe production semantics instead of the Docker mount.
    private_sources=1
  fi
  docker run --rm --platform linux/amd64 \
    -v "$ROOT:$ROOT" -w "$ROOT" "${options[@]}" \
    -e BUILD_ID -e GITHUB_RUN_ID -e GITHUB_RUN_ATTEMPT -e GITHUB_REPOSITORY \
    -e BEAMO_CI_RUNNER=blacksmith -e BEAMO_WIPE_DRY_RUN=1 \
    -e SKIP_ISO=false -e SKIP_QEMU=false -e ALLOW_DIRTY=0 \
    -e PIP_CACHE_DIR="$ROOT/.ci-cache/pip/$gate" \
    -e GIT_CONFIG_COUNT=1 -e GIT_CONFIG_KEY_0=safe.directory -e GIT_CONFIG_VALUE_0="$ROOT" \
    "$IMAGE" bash -ceu '
      mounted_root="$1"
      private_sources="$2"
      gate="$3"
      if [[ "$private_sources" == 1 ]]; then
        private_root="$(mktemp -d /tmp/beamo-wipe-source.XXXXXX)"
        tar -C "$mounted_root" \
          --exclude=./.ci-cache --exclude=./dist --exclude=./qemu-evidence \
          --exclude=./.venv --exclude=./.venv-linux \
          -cf - . | tar --no-same-owner -C "$private_root" -xf -
        cd "$private_root"
        export PIP_CACHE_DIR="$private_root/.ci-cache/pip/$gate"
        code=0
        bash scripts/ci-hosted.sh "$gate" || code=$?
        if [[ -d "$private_root/dist/evidence" ]]; then
          mkdir -p "$mounted_root/dist/evidence"
          for artifact in "$private_root/dist/evidence/$gate".*; do
            if [[ -f "$artifact" ]]; then
              cp "$artifact" "$mounted_root/dist/evidence/"
            fi
          done
        fi
        exit "$code"
      fi
      if [[ "$gate" == iso ]]; then
        apt-get update -qq
        apt-get install -y -qq --no-install-recommends ca-certificates docker.io git python3
      fi
      exec bash scripts/ci-hosted.sh "$gate"
    ' -- "$ROOT" "$private_sources" "$gate"
}

case "${1:-}" in
  sources)
    # Each process has its own Debian filesystem/apt lock. Only download
    # caches and ignored outputs are shared; no gate results are cached.
    pids=()
    for gate in lint tests preview desktop-launchers negative; do
      phase "$gate" &
      pids+=("$!")
    done
    failed=0
    for pid in "${pids[@]}"; do
      wait "$pid" || failed=1
    done
    exit "$failed"
    ;;
  iso|qemu) phase "$1" ;;
  *) echo "usage: $0 {sources|iso|qemu}" >&2; exit 2 ;;
esac
