from __future__ import annotations
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT=Path('/workspace/beamo-wipe')
OUT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
import pytest
from beamo_wipe import nwipe_runner as runner
from beamo_wipe.models import MethodId,WipeRequest
from beamo_wipe.safety import SafetyError

mutations={
    'extra-target':lambda argv:argv.insert(-1,'/dev/sdc'),
    'extra-file':lambda argv:argv.insert(-1,'/etc/fake'),
    'force':lambda argv:argv.insert(-1,'--force'),
    'force-value':lambda argv:argv.insert(-1,'--force=1'),
    'unknown':lambda argv:argv.insert(-1,'--fake-mode'),
    'missing-target':lambda argv:argv.pop(),
    'changed-target':lambda argv:argv.__setitem__(-1,'/dev/sdc'),
    'partition-target':lambda argv:argv.__setitem__(-1,'/dev/sda1'),
    'duplicate-autonuke':lambda argv:argv.insert(-1,'--autonuke'),
    'duplicate-method':lambda argv:argv.insert(-1,next(a for a in argv if a.startswith('--method='))),
    'duplicate-exclude':lambda argv:argv.insert(-1,'--exclude=/dev/sdc'),
    'missing-exclude':lambda argv:argv.remove('--exclude=/dev/sdz'),
    'changed-exclude':lambda argv:argv.__setitem__(argv.index('--exclude=/dev/sdz'),'--exclude=/dev/sdc'),
    'changed-log':lambda argv:argv.__setitem__(next(i for i,a in enumerate(argv) if a.startswith('--logfile=')),'--logfile=/dev/sdc'),
    'PDF-enabled':lambda argv:argv.remove('--PDFreportpath=noPDF'),
    'changed-rounds':lambda argv:argv.__setitem__(next(i for i,a in enumerate(argv) if a.startswith('--rounds=')),'--rounds=2'),
}
realpath=os.path.realpath
lstat=os.lstat
counts={'normal_methods':0,'malformed_argv_rejected':0,'native_device_operations':0}
with tempfile.TemporaryDirectory(prefix='argv-',dir=OUT) as tmp, pytest.MonkeyPatch.context() as patch, contextlib.redirect_stderr(io.StringIO()):
    patch.setenv('BEAMO_WIPE_DRY_RUN','1')
    patch.setattr('beamo_wipe.safety.default_log_dir',lambda:Path(tmp))
    patch.setattr('beamo_wipe.diagnostics.log_diag',lambda *a,**kw:None)
    patch.setattr(os.path,'realpath',lambda path,*a,**kw:os.fspath(path) if os.fspath(path).startswith('/dev/') else realpath(path,*a,**kw))
    def fake_device_stat(path,*args,**kwargs):
        if os.fsdecode(path).startswith('/dev/'):raise FileNotFoundError(path)
        return lstat(path,*args,**kwargs)
    patch.setattr(os,'lstat',fake_device_stat)
    for method in MethodId:
        request=WipeRequest(device='/dev/sda',boot_device='/dev/sdz',method=method,logfile=str(Path(tmp)/'fake.log'))
        argv=runner.build_nwipe_argv(request)
        runner.validate_argv(argv,request)
        assert argv[-1]=='/dev/sda' and argv.count('/dev/sda')==1
        assert argv.count('--exclude=/dev/sdz')==1
        counts['normal_methods']+=1
        for name,mutate in mutations.items():
            changed=copy.copy(argv)
            mutate(changed)
            try:runner.validate_argv(changed,request)
            except SafetyError:counts['malformed_argv_rejected']+=1
            else:raise AssertionError((method,name,changed))
(OUT/'argv-matrix.json').write_text(json.dumps(counts,indent=2)+'\n')
print(json.dumps(counts,indent=2))
