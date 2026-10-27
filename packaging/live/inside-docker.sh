#!/bin/bash
# Runs as root inside debian:bookworm. Invoked by scripts/build-iso.sh.
# Builds on the container's own disk so debootstrap can mknod.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
ISO_NAME="${BEAMO_WIPE_ISO_NAME:-beamo-wipe-${BEAMO_WIPE_VERSION:-0.2.14}-amd64.iso}"
if [[ ! "$ISO_NAME" =~ ^beamo-wipe-[0-9]+\.[0-9]+\.[0-9]+-amd64\.iso$ ]]; then
  echo "invalid ISO output name" >&2
  exit 2
fi

apt-get update
apt-get install -y \
  live-build \
  xorriso \
  isolinux \
  syslinux-common \
  squashfs-tools \
  ca-certificates \
  cpio \
  rsync \
  file \
  xz-utils \
  bzip2 \
  python3

mkdir -p /build
# Do not copy previous failed chroots or git objects; we need config + sources.
rsync -a \
  --exclude '.git/' \
  --exclude 'dist/' \
  --exclude '/.ci-cache/' \
  --exclude '/.pytest_cache/' \
  --exclude '/.mypy_cache/' \
  --exclude '/.ruff_cache/' \
  --exclude '/.venv/' \
  --exclude '/.venv-*/' \
  --exclude '/web-preview/' \
  --exclude '/docs/' \
  --exclude '/tests/' \
  --exclude '/developer_tests/' \
  --exclude 'packaging/live/chroot/' \
  --exclude 'packaging/live/cache/' \
  --exclude 'packaging/live/.build/' \
  --exclude 'packaging/live/.stage/' \
  --exclude '/packaging/live/auto' \
  --exclude 'packaging/live/binary/' \
  --exclude 'packaging/live/tmp/' \
  --exclude '*.iso' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '*.pyo' \
  /src/ /build/

# BEGIN LIVE INPUT COPY CHECK
# Use the implementation mounted from the host, not the just-copied source:
# a changed wrapper module in /build must not be able to bless itself.
PYTHONPATH=/src/src python3 - "$BEAMO_WIPE_LIVE_INPUTS_SHA" /build <<'PYCHECK'
import hashlib
import json
from pathlib import Path
import re
import sys

from beamo_wipe import release_manifest

expected, copied_root = sys.argv[1:]
if not re.fullmatch(r'[0-9a-f]{64}', expected):
    raise SystemExit('missing or invalid staged live-input digest')
release_manifest.ROOT = Path(copied_root)
inventory = release_manifest.live_build_inputs()
raw = json.dumps(inventory, sort_keys=True, separators=(',', ':')).encode('ascii')
if hashlib.sha256(raw).hexdigest() != expected:
    raise SystemExit('copied live inputs differ from the staged checkout')
# The byte inventory cannot detect lost executable bits. Use the trusted
# source helper, never an implementation from the copied build tree.
sys.path.insert(0, str(Path(release_manifest.__file__).resolve().parents[2] / 'scripts'))
from stage_wrapper_sources import require_executable

for relative in (
    'includes.chroot/usr/local/bin/beamo-wipe',
    'includes.chroot/usr/local/sbin/beamo-wipe-kiosk',
    'hooks/normal/0500-build-nwipe.hook.chroot',
):
    require_executable(Path(copied_root) / 'packaging/live/config' / relative)
PYCHECK
# END LIVE INPUT COPY CHECK

cd /build/packaging/live

lb clean --all || true

# The troubleshoot entry means safe video: nomodeset keeps the firmware
# framebuffer (X then uses fbdev or vesa) instead of a GPU driver that can
# leave a black screen. It omits live-build's legacy failsafe flags
# (noapic, nolapic, nosmp, memtest), which can hang or stall modern UEFI PCs.
# It also stays verbose (no quiet) so a hang shows its last kernel message.
#
# Hardware support: non-free-firmware supplies only the graphics, audio,
# USB-controller and CPU microcode firmware listed in the package list
# (--firmware-chroot stays false: no Wi-Fi or Bluetooth blobs). Backports are
# enabled only so config/archives/backports.pref.chroot can pin the
# Debian-signed 6.12 kernel and matching firmware; userland stays bookworm.
lb config \
  --ignore-system-defaults \
  --mode debian \
  --distribution bookworm \
  --architectures amd64 \
  --debootstrap-options "--variant=minbase" \
  --binary-images iso-hybrid \
  --bootloaders syslinux,grub-efi \
  --uefi-secure-boot enable \
  --debian-installer none \
  --memtest none \
  --win32-loader false \
  --iso-application "Beamo Wipe" \
  --iso-preparer "Beamo" \
  --iso-publisher "Beamo https://github.com/BeamoTech/beamo-wipe" \
  --iso-volume "BEAMO_WIPE" \
  --archive-areas "main non-free-firmware" \
  --parent-archive-areas "main non-free-firmware" \
  --backports true \
  --apt-recommends false \
  --firmware-binary false \
  --firmware-chroot false \
  --initsystem systemd \
  --bootappend-live "boot=live components hostname=beamo-wipe username=root noeject nopersistence noswap ip=frommedia nox11autologin quiet loglevel=3" \
  --bootappend-live-failsafe "boot=live components hostname=beamo-wipe username=root noeject nopersistence noswap ip=frommedia nox11autologin nomodeset nosplash vga=788" \
  --mirror-bootstrap "https://deb.debian.org/debian/" \
  --mirror-chroot "https://deb.debian.org/debian/" \
  --mirror-binary "https://deb.debian.org/debian/" \
  --parent-mirror-bootstrap "https://deb.debian.org/debian/" \
  --parent-mirror-chroot "https://deb.debian.org/debian/" \
  --parent-mirror-binary "https://deb.debian.org/debian/" \
  --mirror-chroot-security "https://security.debian.org/" \
  --mirror-binary-security "https://security.debian.org/" \
  --parent-mirror-chroot-security "https://security.debian.org/" \
  --parent-mirror-binary-security "https://security.debian.org/"

lb build

mapfile -t images < <(find /build/packaging/live -maxdepth 2 -type f -name '*.iso' -print)
if [ "${#images[@]}" -ne 1 ]; then
  echo "live-build must produce exactly one ISO (found ${#images[@]})" >&2
  printf '%s\n' "${images[@]}" >&2
  exit 1
fi
found="${images[0]}"
if [ ! -f "$found" ]; then
  echo "live-build produced no ISO" >&2
  ls -la /build/packaging/live || true
  exit 1
fi
cp -v "$found" "/out/${ISO_NAME}"
ls -lh "/out/${ISO_NAME}"
