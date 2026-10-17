import json
import os
from pathlib import Path
import re
import subprocess
root=Path('/root/dev/Beamo Wipe')
pattern=re.compile(r'^test_(?:tk|console|startup|kiosk|refresh_confirm|bug_audit_tk|audit_20260907_console)')
selection=[str(p.relative_to(root)) for p in sorted((root/'tests').glob('test_*.py')) if pattern.search(p.name) and p.name!='test_tk_input_scroll_pass13.py']
command=['dbus-run-session','--','xvfb-run','-a','-s','-screen 0 1600x1000x24 -dpi 72','/tmp/beamo-wipe-audit-python/bin/python','-m','pytest',*selection,'-q','-ra','--junitxml=/tmp/pass13-ui/fixed-adjacent.xml']
Path('/tmp/pass13-ui/fixed-adjacent-command.json').write_text(json.dumps(command,indent=2)+'\n')
with Path('/tmp/pass13-ui/fixed-adjacent.txt').open('w') as log:
 result=subprocess.run(command,cwd=root,env=dict(os.environ,BEAMO_ISOLATED_X11_TEST='1'),stdout=log,stderr=subprocess.STDOUT)
print(json.dumps({'modules':len(selection),'returncode':result.returncode}))
raise SystemExit(result.returncode)
