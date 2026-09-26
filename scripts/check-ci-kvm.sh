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
