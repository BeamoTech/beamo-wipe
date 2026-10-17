"""Bounded focused tests, with external machine acquisition prohibited."""
import builtins, io, json, os, pathlib, subprocess, sys
os.environ['BEAMO_WIPE_DRY_RUN']='1'
original_open=builtins.open
original_run=subprocess.run
observed={}
def guarded_open(path,*args,**kwargs):
    text=str(path)
    if text in {'/proc/cmdline','/proc/self/mountinfo'}:
        observed[text]=observed.get(text,0)+1
        return io.StringIO('')
    return original_open(path,*args,**kwargs)
def guarded_run(argv,*args,**kwargs):
    if isinstance(argv,(list,tuple)) and argv:
        name=pathlib.Path(str(argv[0])).name
        if name=='findmnt':
            observed['fake_findmnt']=observed.get('fake_findmnt',0)+1
            return subprocess.CompletedProcess(argv,1,stdout='',stderr='')
        if name in {'lsblk','nwipe'}:
            raise AssertionError('Forbidden native acquisition: '+str(argv[0]))
    return original_run(argv,*args,**kwargs)
builtins.open=guarded_open
subprocess.run=guarded_run
import pytest
files=json.loads(pathlib.Path('/tmp/pass10-discovery/selected-files.json').read_text())
rc=pytest.main(['-q',*files,'--junitxml=/tmp/pass10-discovery/focused.xml'])
print('fake_host_boundary_reads',observed,flush=True)
sys.exit(rc)
