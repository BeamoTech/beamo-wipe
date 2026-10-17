import builtins, io, os, pathlib, subprocess, sys
os.environ['BEAMO_WIPE_DRY_RUN']='1'
real_open=builtins.open
real_run=subprocess.run
counts={}
def guarded_open(path,*a,**kw):
    text=str(path)
    if text in {'/proc/cmdline','/proc/self/mountinfo'}:
        counts[text]=counts.get(text,0)+1
        return io.StringIO('')
    return real_open(path,*a,**kw)
def guarded_run(argv,*a,**kw):
    if isinstance(argv,(list,tuple)) and argv:
        name=pathlib.Path(str(argv[0])).name
        if name=='findmnt':
            counts['fake_findmnt']=counts.get('fake_findmnt',0)+1
            return subprocess.CompletedProcess(argv,1,stdout='',stderr='')
        if name in {'lsblk','nwipe'}:raise AssertionError('Forbidden native acquisition '+str(argv[0]))
    return real_run(argv,*a,**kw)
builtins.open=guarded_open
subprocess.run=guarded_run
import pytest
names=[]
for f in sorted(pathlib.Path('tests').glob('test*.py')):
    if any(t in f.name for t in ['completion','engine_checks','engine_check_record','progress','write_vs_completion','stale_progress','runner_projection_progress_order']):names.append(str(f))
print('MODULES',len(names),names,flush=True)
rc=pytest.main(['-q','--junitxml=/tmp/beamo-pass8-discovery-projection-suite.xml',*names])
print('FAKE_HOST_READS',counts,flush=True)
sys.exit(rc)
