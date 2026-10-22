"""Replay final regression bytes with archived pre-repair sources."""
from pathlib import Path
import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile

repo = Path('/workspace/beamo-wipe')
r = Path(__file__).parent
baseline = r / 'baseline-replay'
baseline.mkdir(exist_ok=False)
archive = subprocess.check_output([
    'git','archive','7fcd706b44c0d63cf5f2959bcd235968e8300274',
    'src','scripts/build_desktop.py','dev.py','pyproject.toml',
], cwd=repo)
with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
    stream.extractall(baseline, filter='data')
tests = [
    'tests/test_ci_log_snapshot_pass13_20261021.py',
    'tests/test_evidence_publication_pass13_20261021.py',
    'tests/test_sound_cancelled_spawn_pass13_20261021.py',
    'tests/test_accessible_main_lifetime_pass13.py',
    'developer_tests/test_desktop_manifest_interrupt_pass13_20261021.py',
]
paths = []
for name in tests:
    target = baseline/name
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(repo/name,target)
    # The CI probe needs the actual repository for harmless git rev-parse.
    paths.append(str(repo/name) if name.startswith('tests/test_ci_') else str(target))
receipt = {'baseline_commit':'7fcd706b44c0d63cf5f2959bcd235968e8300274',
           'final_tests':{name:hashlib.sha256((repo/name).read_bytes()).hexdigest() for name in tests},
           'baseline_sources':{str(p.relative_to(baseline)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted((baseline/'src').rglob('*.py'))}}
(r/'exact-baseline-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
env = os.environ.copy()
env.update(PYTHONPATH=str(baseline/'src'),BEAMO_WIPE_DRY_RUN='1',BEAMO_WIPE_DEMO='1')
command = ['python3',str(r/'run_group.py'),'exact-python-baseline',
    'dbus-run-session','--','xvfb-run','-a','-n','1352','-s',
    '-screen 0 1600x1000x24 -dpi 72','env','BEAMO_ISOLATED_X11_TEST=1',
    'python3','-m','pytest','-W','error','-p','no:cacheprovider','-c','/dev/null',
    '-o','addopts=','-o','pythonpath=','-q',*paths,
    '--junitxml='+str(r/'exact-python-baseline.xml')]
result = subprocess.run(command,cwd=repo,env=env)
assert result.returncode==1, result.returncode
print('Expected baseline failure replay completed')
