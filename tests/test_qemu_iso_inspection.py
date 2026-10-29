"""ISO inspection consumes a hash-bound private snapshot without kernel mounts."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]

# A fake xorriso: extracted directories get a few regular files, the GRUB
# menu is a single file. PLANT_SYMLINK adds a symlink inside /isolinux.
FAKE_XORRISO = '''
import os, pathlib, sys
args = sys.argv[1:]
assert args[:3] == ['-osirrox', 'on', '-indev']
snapshot = pathlib.Path(args[3])
assert snapshot.name == 'inspection.iso'
# A source change during extraction must not affect the inspected bytes.
pathlib.Path(os.environ['SOURCE_ISO']).write_bytes(b'later source change')
trees = {
    '/live': ('filesystem.squashfs', 'vmlinuz-6.12.113+deb12-amd64', 'initrd.img-6.12.113+deb12-amd64'),
    '/isolinux': ('live.cfg', 'isolinux.bin', 'ldlinux.c32'),
    '/EFI/boot': ('bootx64.efi', 'grubx64.efi'),
}
for index in range(4, len(args), 3):
    assert args[index] == '-extract'
    source, target = args[index + 1], pathlib.Path(args[index + 2])
    if source in trees:
        target.mkdir()
        for name in trees[source]:
            (target / name).write_bytes(snapshot.read_bytes())
        if os.environ.get('PLANT_SYMLINK') and source == '/isolinux':
            (target / 'planted.c32').symlink_to('/etc/passwd')
    else:
        assert source == '/boot/grub/grub.cfg'
        target.write_bytes(snapshot.read_bytes())
'''


def _inspection_code() -> str:
    shell = (ROOT / "scripts/qemu-verify.sh").read_text()
    return shell.split("<<'PYISO'\n", 1)[1].split("\nPYISO", 1)[0]


def _run_with_fake(tmp_path, source, payload, **env):
    tools = tmp_path / "bin"
    tools.mkdir()
    extractor = tools / "xorriso"
    extractor.write_text(f"#!{sys.executable}\n" + FAKE_XORRISO)
    extractor.chmod(0o755)
    destination = tmp_path / "extracted"
    destination.mkdir()
    result = subprocess.run(
        [sys.executable, "-c", _inspection_code(), str(source), str(tmp_path / "inspection.iso"),
         str(destination), hashlib.sha256(payload).hexdigest()],
        env=dict(os.environ, PATH=str(tools) + os.pathsep + os.environ["PATH"],
                 SOURCE_ISO=str(source), **env),
        capture_output=True, text=True, timeout=10,
    )
    return result, destination


@pytest.mark.parametrize("source_kind", ["regular", "changed", "symlink", "fifo"])
def test_iso_inspection_uses_only_verified_regular_snapshot(tmp_path, source_kind):
    source = tmp_path / "source.iso"
    payload = b"verified ISO fixture"
    source.write_bytes(payload)
    if source_kind == "changed":
        source.write_bytes(b"changed after manifest verification")
    elif source_kind == "symlink":
        original = tmp_path / "original.iso"
        source.rename(original)
        source.symlink_to(original)
    elif source_kind == "fifo":
        source.unlink()
        os.mkfifo(source)
    result, destination = _run_with_fake(tmp_path, source, payload)
    if source_kind != "regular":
        assert result.returncode != 0
        assert list(destination.iterdir()) == []
        return
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "inspection.iso").exists()
    assert source.read_bytes() != payload
    # Kernel, initramfs, BIOS loader and EFI loaders are inspected too.
    for name in ('live/filesystem.squashfs', 'live/initrd.img-6.12.113+deb12-amd64',
                 'isolinux/live.cfg', 'isolinux/isolinux.bin', 'isolinux/ldlinux.c32',
                 'EFI/boot/bootx64.efi', 'EFI/boot/grubx64.efi', 'boot/grub/grub.cfg'):
        output = destination / name
        assert output.read_bytes() == payload
        assert output.stat().st_mode & 0o222 == 0


def test_iso_inspection_refuses_a_symlink_inside_an_extracted_directory(tmp_path):
    source = tmp_path / "source.iso"
    payload = b"verified ISO fixture"
    source.write_bytes(payload)
    result, _ = _run_with_fake(tmp_path, source, payload, PLANT_SYMLINK="1")
    assert result.returncode != 0
    assert "not a regular file" in result.stderr


def test_every_iso_path_the_gate_reads_is_extracted():
    # Checks after extraction read the initramfs, BIOS modules and loaders;
    # an unextracted path would fail every hosted run.
    gate = (ROOT / "scripts/qemu-verify.sh").read_text()
    code = _inspection_code()
    assert "extracted = ('live', 'isolinux', 'EFI/boot', 'boot/grub/grub.cfg')" in code
    for reader in ('python3 - "$ISO_MOUNT/live" <<', 'python3 - "$ISO_MOUNT/isolinux" <<'):
        assert reader in gate


@pytest.mark.skipif(shutil.which("xorriso") is None, reason="xorriso is unavailable")
def test_iso_inspection_extracts_expected_files_from_real_iso(tmp_path):
    tree = tmp_path / "tree"
    names = ('live/filesystem.squashfs', 'live/vmlinuz-6.12.113+deb12-amd64',
             'live/initrd.img-6.12.113+deb12-amd64', 'isolinux/live.cfg',
             'isolinux/isolinux.bin', 'isolinux/vesamenu.c32', 'EFI/boot/bootx64.efi',
             'EFI/boot/grubx64.efi', 'boot/grub/grub.cfg')
    for name in names:
        target = tree / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b'regular-file fixture: ' + name.encode())
    iso = tmp_path / "source.iso"
    made = subprocess.run(
        ['xorriso', '-as', 'mkisofs', '-R', '-o', str(iso), str(tree)],
        capture_output=True, text=True, timeout=30,
    )
    assert made.returncode == 0, made.stderr
    destination = tmp_path / "extracted"
    destination.mkdir()
    result = subprocess.run(
        [sys.executable, "-c", _inspection_code(), str(iso), str(tmp_path / 'inspection.iso'),
         str(destination), hashlib.sha256(iso.read_bytes()).hexdigest()],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    for name in names:
        assert (destination / name).read_bytes() == (tree / name).read_bytes()
