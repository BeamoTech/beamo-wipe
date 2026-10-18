"""Freeze the final application, tests and build inputs before local gates."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

root = Path.cwd()
out = Path('/tmp/pass16-primary')
sys.path.insert(0, str(root / 'src'))
from beamo_wipe.build_identity import runtime_source_sha256

prefixes = ('src/', 'tests/', 'developer_tests/', 'scripts/', 'packaging/', 'desktop/', 'helper/', '.github/')
names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z']).decode().split('\0')
selected = sorted({n for n in names if n.startswith(prefixes) or n in {'dev.py', 'preview', 'pyproject.toml'}})
frozen = {n: hashlib.sha256((root / n).read_bytes()).hexdigest() for n in selected}
(out / 'source-freeze.json').write_text(json.dumps(frozen, sort_keys=True, indent=2) + '\n')
diff = subprocess.check_output(['git', 'diff', '--', 'src'])
(out / 'source.diff.gz').write_bytes(gzip.compress(diff, mtime=0))
fixture_diff=subprocess.check_output(['git','diff','--','tests'])
(out/'tracked-test-fixture.diff.gz').write_bytes(gzip.compress(fixture_diff,mtime=0))
new_tests = sorted(n for n in selected if n.startswith('tests/') and subprocess.run(['git', 'ls-files', '--error-unmatch', n], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0)
assert len(new_tests) > 9, new_tests
data = io.BytesIO()
with tarfile.open(fileobj=data, mode='w') as archive:
    for name in new_tests:
        blob = (root / name).read_bytes()
        info = tarfile.TarInfo(name)
        info.size = len(blob)
        info.mtime = 0
        archive.addfile(info, io.BytesIO(blob))
(out / 'new-tests.tar.gz').write_bytes(gzip.compress(data.getvalue(), mtime=0))
(out / 'new-tests-sha256.json').write_text(json.dumps({n: frozen[n] for n in new_tests}, indent=2) + '\n')
receipt = {'frozen_input_files': len(frozen), 'changed_after_freeze': [], 'runtime_source_sha256': runtime_source_sha256(), 'head': subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip(), 'branch': subprocess.check_output(['git', 'branch', '--show-current']).decode().strip(), 'source_diff_sha256': hashlib.sha256(diff).hexdigest()}
import difflib
parts=[]
with tarfile.open(out/'starting-source.tar.gz','r:gz') as archive:
    for member in archive.getmembers():
        old=archive.extractfile(member).read();new=(root/member.name).read_bytes()
        if old!=new:
            parts.extend(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile='starting/'+member.name,tofile='final/'+member.name))
(out/'pass16-source.diff').write_text(''.join(parts))
receipt['pass16_source_diff_sha256']=hashlib.sha256(''.join(parts).encode()).hexdigest()
receipt['new_untracked_test_modules']=new_tests
(out / 'source-review.json').write_text(json.dumps(receipt, indent=2) + '\n')
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'])
print(json.dumps(receipt, indent=2))
