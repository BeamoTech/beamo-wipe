"""Reproduce all final regressions on exact starting dirty application bytes."""
import hashlib,json,os,shutil,subprocess,tempfile,xml.etree.ElementTree as ET
from pathlib import Path
root=Path.cwd();scratch=Path(tempfile.mkdtemp(prefix='beamo-pass10-original-'))
shutil.copytree(root/'src',scratch/'src',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
shutil.copytree(root/'tests',scratch/'tests',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
(scratch/'src/beamo_wipe/nwipe_runner.py').write_bytes(Path('/tmp/pass10-runner/nwipe_runner-before.py').read_bytes())
for name in ('ui/console_wizard.py','ui/sound_dialog.py'):
    (scratch/'src/beamo_wipe'/name).write_bytes(subprocess.check_output(['git','show','HEAD:src/beamo_wipe/'+name],cwd=root))
frozen=json.loads((root/'docs/evidence/bug-audit-20261016-pass9/source-freeze.json').read_text())
original_source={n:h for n,h in frozen.items() if n.startswith('src/')}
assert all(hashlib.sha256((scratch/n).read_bytes()).hexdigest()==h for n,h in original_source.items())
tests=['test_console_inventory_diagnostic_pass10.py','test_runner_projection_record_endings_pass10.py','test_sound_output_selection_pass10.py']
runtime=scratch/'runtime';runtime.mkdir(mode=0o700)
env=dict(os.environ,PYTHONPATH=str(scratch/'src'),XDG_RUNTIME_DIR=str(runtime),PULSE_RUNTIME_PATH=str(runtime/'pulse'),BEAMO_ISOLATED_X11_TEST='1')
for key in ('AT_SPI_BUS_ADDRESS','PULSE_SERVER'):env.pop(key,None)
command=['dbus-run-session','--','xvfb-run','-a','-s','-screen 0 1600x1000x24 -dpi 72','/tmp/beamo-wipe-audit-python/bin/python3','-m','pytest','-c',str(root/'pyproject.toml'),'-o','pythonpath='+str(scratch/'src'),'--rootdir='+str(scratch),*[str(scratch/'tests'/name) for name in tests],'--junitxml=/tmp/pass10-primary/original.xml']
with Path('/tmp/pass10-primary/original.txt').open('wb') as log:
    result=subprocess.run(command,cwd=scratch,env=env,stdout=log,stderr=subprocess.STDOUT)
cases=ET.parse('/tmp/pass10-primary/original.xml').findall('.//testcase')
summary={'starting_application_files_hash_verified':len(original_source),'test_cases':len(cases),'failures':sum(c.find('failure') is not None for c in cases),'errors':sum(c.find('error') is not None for c in cases),'skipped':sum(c.find('skipped') is not None for c in cases),'pytest_exit':result.returncode}
print(json.dumps(summary,indent=2));Path('/tmp/pass10-primary/original-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
assert result.returncode==1 and len(cases)==78 and summary['failures']==32 and summary['errors']==summary['skipped']==0
