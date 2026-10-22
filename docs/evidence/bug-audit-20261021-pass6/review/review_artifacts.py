"""Inspect local cross-build bytes without executing native launchers."""
from pathlib import Path
import hashlib
import importlib.util
import json
import stat
import struct
import subprocess
import sys

repo = Path('/workspace/beamo-wipe')
root = Path(__file__).resolve().parent
manifest = json.loads((repo / 'dist/desktop/desktop-build.json').read_text())
spec = importlib.util.spec_from_file_location('pass4_artifact_builder', repo / 'scripts/build_desktop.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=repo))
builder.verify_desktop_bundle(repo, repo / 'dist/desktop', head, '0.2.13', dirty)
review = {'build_receipt': manifest, 'native_platform_or_image_acceptance': False,
          'independent_bundle_verifier': 'PASS: current HEAD/dirty/version/source digest and launcher hashes',
          'outputs': {}, 'source_manifest_sha256': hashlib.sha256(
              (root / 'final-source-sha256.json').read_bytes()).hexdigest()}

def inspect(path, pe):
    raw = path.read_bytes()
    if pe:
        assert raw[:2] == b'MZ'
        offset = struct.unpack_from('<I', raw, 0x3c)[0]
        assert raw[offset:offset+4] == b'PE\0\0'
        assert struct.unpack_from('<H', raw, offset+4)[0] == 0x8664
        assert struct.unpack_from('<H', raw, offset+24)[0] == 0x20b
        kind = 'PE32+ x86_64'
    else:
        assert raw[:6] == b'\x7fELF\x02\x01'
        assert struct.unpack_from('<H', raw, 18)[0] == 62
        kind = 'ELF64 little-endian x86_64'
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
            'format': kind, 'executed': False,
            'mode': oct(stat.S_IMODE(path.stat().st_mode))}

for name, digest in manifest['files'].items():
    record = inspect(repo / 'dist/desktop' / name, name.endswith('.exe'))
    assert record['sha256'] == digest
    review['outputs'][name] = record
review['windows_test_cross_compile'] = inspect(root / 'desktop-windows.test.exe', True)
review['critical_executable_modes'] = {}
for name in ['preview', 'scripts/test-all.sh', 'scripts/build-iso.sh',
             'scripts/ci-hosted.sh',
             'packaging/live/config/includes.chroot/usr/local/sbin/beamo-wipe-kiosk',
             'packaging/live/config/includes.chroot/usr/local/bin/beamo-wipe',
             'packaging/live/config/hooks/normal/0500-build-nwipe.hook.chroot']:
    mode = stat.S_IMODE((repo / name).stat().st_mode)
    assert mode & 0o111, name
    review['critical_executable_modes'][name] = oct(mode)
review['preview_normal_close'] = json.loads((root / 'actual-preview.json').read_text())
image = root / 'actual-preview-72dpi.png'
review['preview_image'] = {'sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                          'bytes': image.stat().st_size,
                          'visually_inspected': True,
                          'included_in_public_artifacts': False,
                          'local_path': str(image)}
target = root / (sys.argv[1] if len(sys.argv) > 1 else 'artifact-review.json')
target.write_text(json.dumps(review, indent=2) + '\n')
print(json.dumps({'artifact_review': 'PASS', 'receipt_commit': manifest['source_commit'],
                  'source_dirty': manifest['source_dirty']}))
