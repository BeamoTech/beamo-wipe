"""Harmless exact-interpreter/shebang probe; no installations or product edits."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

out=Path('/tmp/pass19-primary')
root=Path.cwd()
original=root/'.venv-linux/bin/python3'
alias=Path('/tmp/beamo-pass19-python')
if os.path.lexists(alias):
    assert alias.is_symlink() and alias.resolve()==(root/'.venv-linux').resolve()
else:
    alias.symlink_to(root/'.venv-linux',target_is_directory=True)
plain=alias/'bin/python3'
assert original.resolve()==plain.resolve()
query='import json,sys,pytest,ruff,mypy; print(json.dumps(dict(version=sys.version,executable=sys.executable,prefix=sys.prefix,base_prefix=sys.base_prefix,pytest=pytest.__version__,pytest_file=pytest.__file__)))'
info={}
with tempfile.TemporaryDirectory(prefix='beamo-pass19-shebang-') as private:
    for name,executable in [('space',original),('plain',plain)]:
        row=json.loads(subprocess.check_output([str(executable),'-c',query],text=True))
        fixture=Path(private)/name
        fixture.write_text('#!'+row['executable']+'\nprint("PASS19_SHEBANG_OK")\n')
        fixture.chmod(0o700)
        try:
            result=subprocess.run([str(fixture)],capture_output=True,text=True)
            row.update(returncode=result.returncode,stdout=result.stdout,stderr=result.stderr)
        except OSError as error:
            row.update(error_type=type(error).__name__,errno=error.errno)
        info[name]=row
assert info['space'].get('errno')==2 and info['plain']['returncode']==0
assert info['plain']['stdout']=='PASS19_SHEBANG_OK\n'
assert info['space']['version']==info['plain']['version']
assert info['space']['pytest']==info['plain']['pytest']
assert Path(info['space']['pytest_file']).resolve()==Path(info['plain']['pytest_file']).resolve()
assert Path(info['space']['prefix']).resolve()==Path(info['plain']['prefix']).resolve()
(out/'interpreter-path-probe.json').write_text(json.dumps(info,indent=2)+'\n')
print(json.dumps(info,indent=2))
