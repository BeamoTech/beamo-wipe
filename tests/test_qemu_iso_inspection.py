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
    tools = tmp_path / "bin"
    tools.mkdir()
    extractor = tools / "xorriso"
    extractor.write_text(f"#!{sys.executable}\n" + '''
import os, pathlib, sys
args = sys.argv[1:]
assert args[:3] == ['-osirrox', 'on', '-indev']
snapshot = pathlib.Path(args[3])
assert snapshot.name == 'inspection.iso'
# A source change during extraction must not affect the inspected bytes.
pathlib.Path(os.environ['SOURCE_ISO']).write_bytes(b'later source change')
for index in range(4, len(args), 3):
    assert args[index] == '-extract'
    assert args[index + 1] in ('/live/filesystem.squashfs', '/isolinux/live.cfg', '/boot/grub/grub.cfg')
    pathlib.Path(args[index + 2]).write_bytes(snapshot.read_bytes())
''')
    extractor.chmod(0o755)
    snapshot = tmp_path / "inspection.iso"
    destination = tmp_path / "extracted"
    destination.mkdir()
    shell = (ROOT / "scripts/qemu-verify.sh").read_text()
    code = shell.split("<<'PYISO'\n", 1)[1].split("\nPYISO", 1)[0]
    result = subprocess.run(
        [sys.executable, "-c", code, str(source), str(snapshot), str(destination),
         hashlib.sha256(payload).hexdigest()],
        env=dict(os.environ, PATH=str(tools) + os.pathsep + os.environ["PATH"],
                 SOURCE_ISO=str(source)),
        capture_output=True, text=True, timeout=10,
    )
    if source_kind != "regular":
        assert result.returncode != 0
        assert list(destination.iterdir()) == []
        return
    assert result.returncode == 0, result.stderr
    assert not snapshot.exists()
    assert source.read_bytes() != payload
    for name in ('live/filesystem.squashfs', 'isolinux/live.cfg', 'boot/grub/grub.cfg'):
        output = destination / name
        assert output.read_bytes() == payload
        assert output.stat().st_mode & 0o222 == 0


@pytest.mark.skipif(shutil.which("xorriso") is None, reason="xorriso is unavailable")
def test_iso_inspection_extracts_expected_files_from_real_iso(tmp_path):
    tree = tmp_path / "tree"
    names = ('live/filesystem.squashfs', 'isolinux/live.cfg', 'boot/grub/grub.cfg')
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
    shell = (ROOT / "scripts/qemu-verify.sh").read_text()
    code = shell.split("<<'PYISO'\n", 1)[1].split("\nPYISO", 1)[0]
    result = subprocess.run(
        [sys.executable, "-c", code, str(iso), str(tmp_path / 'inspection.iso'),
         str(destination), hashlib.sha256(iso.read_bytes()).hexdigest()],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    for name in names:
        assert (destination / name).read_bytes() == (tree / name).read_bytes()
