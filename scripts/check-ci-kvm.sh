#!/usr/bin/env bash
# Probe virtualization on the disposable hosted worker; never opens a disk.
set -euo pipefail
if [[ "${GITHUB_ACTIONS:-}" != true || "$(uname -sm)" != 'Linux x86_64' ]]; then
  echo 'KVM preflight requires an isolated x86_64 Actions worker.' >&2
  exit 2
fi

# QEMU runs as root in its privileged container. The runner user's group
# membership must not reject a device that is available to that container.
if ! sudo test -c /dev/kvm; then
  if grep -qw vmx /proc/cpuinfo; then
    sudo modprobe kvm_intel
  elif grep -qw svm /proc/cpuinfo; then
    sudo modprobe kvm_amd
  else
    echo 'Blacksmith worker does not expose x86 virtualization CPU flags; KVM runner support is required.' >&2
    exit 2
  fi
fi
sudo python3 - <<'PY'
import fcntl
import os

try:
    descriptor = os.open('/dev/kvm', os.O_RDWR | os.O_CLOEXEC)
    try:
        # KVM_GET_API_VERSION does not create a VM or access a block device.
        version = fcntl.ioctl(descriptor, 0xAE00, 0)
        if version != 12:
            raise RuntimeError('unsupported KVM API version')
    finally:
        os.close(descriptor)
except (OSError, RuntimeError) as exc:
    raise SystemExit(f'Blacksmith KVM API is unavailable: {exc}') from None
print('Blacksmith KVM API version 12 is available to the privileged image gate.')
PY

# Docker enumerates available devices when the privileged container starts.
# Load file-backed loop support on the worker first, so its device nodes are
# present in the image-validation container as well as in the host namespace.
if ! sudo test -c /dev/loop-control; then
  sudo modprobe loop
  sudo udevadm settle
fi
# The Debian validation container has no copy of the worker's kernel modules,
# so mount cannot rely on loading filesystem drivers from inside it.
for mapping in squashfs:squashfs vfat:vfat; do
  filesystem="${mapping%%:*}"
  module="${mapping#*:}"
  if ! grep -qw "$filesystem" /proc/filesystems; then
    sudo modprobe "$module"
  fi
  grep -qw "$filesystem" /proc/filesystems || {
    echo "Image worker filesystem is unavailable: $filesystem" >&2
    exit 2
  }
done
sudo python3 - <<'PY'
import os
from pathlib import Path
import subprocess
import tempfile

directory = Path(tempfile.mkdtemp(prefix='beamo-wipe-loop-probe.'))
backings = []
loops = []
try:
    # Devices are allocated lazily by this kernel. Keep eight attached at
    # once so Docker sees enough nodes for concurrent SquashFS, report, boot
    # exclusion and target checks. Every attachment is a private regular file.
    for index in range(8):
        backing = directory / f'probe-{index}.img'
        backings.append(backing)
        with backing.open('xb') as stream:
            stream.truncate(1024 * 1024)
        loop = subprocess.check_output(
            ['losetup', '--find', '--show', '--read-only', str(backing)], text=True,
        ).strip()
        loops.append((loop, backing))
    print('Eight private regular-file loop attachments succeeded.')
finally:
    safe_cleanup = True
    for loop, backing in reversed(loops):
        try:
            attached = subprocess.check_output(
                ['losetup', '--list', '--noheadings', '--raw', '--output', 'BACK-FILE', loop],
                text=True,
            ).strip()
            if attached != str(backing):
                safe_cleanup = False
                continue
            subprocess.run(['losetup', '--detach', loop], check=True)
        except subprocess.CalledProcessError:
            safe_cleanup = False
    if not safe_cleanup:
        raise SystemExit('Loop probe ownership or detach failed; backing files preserved.')
    for backing in backings:
        backing.unlink(missing_ok=True)
    os.rmdir(directory)
print('Private loop probes detached and removed; squashfs and FAT support are available.')
PY
