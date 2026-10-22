"""Spawn-safe baseline replay in a copied regular-file package and test root."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys


def main():
    repo = Path('/workspace/beamo-wipe')
    folder = Path(__file__).resolve().parent
    copied = folder / 'spawn-baseline'
    assert not copied.exists(), 'Preserve prior baseline witness; choose a new root'
    shutil.copytree(repo / 'src', copied / 'src',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    test = 'tests/test_log_fifo_open_pass5_20261021.py'
    (copied / 'tests').mkdir()
    shutil.copyfile(repo / test, copied / test)
    shutil.copyfile(folder / 'safety-original.py', copied / 'src/beamo_wipe/safety.py')
    (copied / 'pytest.ini').write_text('[pytest]\npythonpath = src\ntestpaths = tests\n')
    for path in copied.rglob('*'):
        assert not path.is_symlink(), path
        assert path.is_file() or path.is_dir(), path
    env = dict(os.environ)
    env['PYTHONPATH'] = str(copied / 'src')
    provenance = subprocess.check_output(
        [sys.executable, '-c', 'import beamo_wipe; print(beamo_wipe.__file__)'],
        cwd=copied, env=env, text=True,
    ).strip()
    assert provenance == str(copied / 'src/beamo_wipe/__init__.py'), provenance
    record = {'copied_package': provenance,
              'test_sha256': hashlib.sha256((copied / test).read_bytes()).hexdigest(),
              'source_test_sha256': hashlib.sha256((repo / test).read_bytes()).hexdigest(),
              'original_safety_sha256': hashlib.sha256((copied / 'src/beamo_wipe/safety.py').read_bytes()).hexdigest(),
              'all_copied_paths_regular_or_directory': True}
    assert record['test_sha256'] == record['source_test_sha256']
    (folder / 'spawn-baseline-receipt.json').write_text(json.dumps(record, indent=2)+'\n')
    return subprocess.run(
        [sys.executable, '-W', 'error', '-m', 'pytest', '-o', 'addopts=', '-q', test,
         '--junitxml='+str(folder / 'spawn-expanded-before.xml')],
        cwd=copied, env=env, check=False,
    ).returncode


if __name__ == '__main__':
    raise SystemExit(main())
