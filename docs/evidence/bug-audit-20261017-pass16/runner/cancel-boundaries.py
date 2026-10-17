"""Event-free fake cancellation ownership and retry probes; never signals an OS PID."""
import hashlib
import fcntl
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import time
REPO=Path('/root/dev/Beamo Wipe'); sys.path.insert(0,str(REPO/'src'))
os.environ['BEAMO_WIPE_DRY_RUN'] = '1'
os.environ['BEAMO_WIPE_LIVE'] = '0'
from beamo_wipe import nwipe_runner as m
from beamo_wipe.models import MethodId,WipeRequest
from beamo_wipe.methods import METHODS
BASE=Path('/tmp/pass16-runner'); forbidden_calls=[]
def forbidden(*a,**k): forbidden_calls.append(repr(a[:1])); raise AssertionError('native acquisition')
m.subprocess.Popen=forbidden; m.subprocess.run=forbidden
m.pinned_nwipe_already_running=forbidden; m._recheck_identity_under_lock=forbidden
m._try_log_diag=lambda *a,**k: None
real_open=os.open
def ordinary_open(path,*a,**k):
    if os.fsdecode(path).startswith(('/dev/','/sys/','/proc/')): forbidden(path)
    return real_open(path,*a,**k)
os.open=ordinary_open
real_realpath=os.path.realpath
os.path.realpath=lambda path,*a,**k: os.fspath(path) if os.fsdecode(path).startswith('/dev/') else real_realpath(path,*a,**k)
source={p:hashlib.sha256((REPO/'src/beamo_wipe'/p).read_bytes()).hexdigest() for p in ['nwipe_runner.py','sleep_inhibit.py','methods.py']}

class Fake:
    def __init__(self,mode,complete):
        self.mode=mode; self.returncode=0 if mode=='already_exited' else None
        self.actions=[]; self.complete=complete; self.waits=0; self.polls=0
    def poll(self):
        self.actions.append('poll'); self.polls+=1
        if self.mode=='status_error_once' and self.polls==1: raise OSError('fake status unavailable')
        if self.mode=='natural_on_probe': self.returncode=0
        return self.returncode
    def terminate(self):
        self.actions.append('terminate')
        if self.mode=='lookup_gone': self.returncode=0; raise ProcessLookupError('fake gone')
        if self.mode=='timeout_kill': return
        if self.mode=='wait_error_once': self.returncode=-15; return
        if self.mode=='never_exits': return
        self.returncode=0 if self.mode=='natural_on_terminate' else -15
    def wait(self,timeout):
        self.actions.append('wait'); self.waits+=1
        if self.mode=='wait_error_once' and self.waits==1: raise OSError('fake wait unavailable')
        if self.mode in {'timeout_kill','never_exits'} and self.returncode is None:
            raise subprocess.TimeoutExpired('fake',timeout)
        return self.returncode
    def kill(self):
        self.actions.append('kill')
        if self.mode!='never_exits': self.returncode=-9

rows=[]; start=time.monotonic()
for index,(target,method,complete,mode) in enumerate(itertools.product(['/dev/sda','/dev/nvme0n100','/dev/mmcblk100'],list(MethodId),[False,True],['already_exited','natural_on_probe','natural_on_terminate','lookup_gone','status_error_once','timeout_kill','wait_error_once','never_exits'])):
    col=m.nwipe_status_device_field(target); spec=METHODS[method]
    text=(m.NWIPE_DRIVE_STATUS_HEADER+'\n'+col+' | Erased | 1MB/s | 00:00:01 | FAKE\n') if complete else target+': 050.00%, round 1 of 1, pass 1 of '+str(spec.overwrite_passes)+', eta 00:00:01, [writing]\n'
    log=BASE/'cancel.log'; raw=text.encode(); log.write_bytes(raw)
    request=WipeRequest(target,method,'/dev/sr0',str(log)); proc=Fake(mode,complete)
    runner=m.NwipeRunner(); runner._proc=proc; runner._active_request=request; runner._last_logfile=str(log)
    lock=BASE/'cancel.lock'; lock_fd=os.open(lock,os.O_CREAT|os.O_RDWR,0o600); fcntl.flock(lock_fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    log_fd=os.open(log,os.O_RDONLY); st=os.fstat(log_fd)
    runner._lock_fd=lock_fd; runner._lock_path=str(lock); runner._log_fd=log_fd; runner._active_log_identity=(str(log),st.st_dev,st.st_ino)
    raised=None
    try: runner.cancel()
    except (OSError,m.SafetyError) as exc: raised=type(exc).__name__
    if mode=='never_exits':
        assert raised=='SafetyError' and runner._proc is proc and runner.result is None and runner._cancelling is None
        assert os.fstat(lock_fd) and os.fstat(log_fd)
        proc.mode='retry'; runner.cancel()
        assert runner.result is not None and runner.result.reason=='cancelled'
        retried=True
    elif mode=='wait_error_once':
        assert raised=='OSError' and runner._proc is proc and runner.result is None and runner._cancelling is None
        assert os.fstat(lock_fd) and os.fstat(log_fd)
        runner.cancel(); retried=True
        assert runner.result is not None and runner.result.reason=='process_failed'
    else:
        assert raised is None; retried=False
        assert runner.result is not None
        natural=mode in {'already_exited','natural_on_probe','lookup_gone'} or mode=='natural_on_terminate' and complete
        want_ok=natural and complete
        want_reason='completed' if want_ok else 'completion_missing' if natural else 'cancelled'
        assert (runner.result.ok,runner.result.reason)==(want_ok,want_reason)
        if mode in {'already_exited','natural_on_probe'}: assert 'terminate' not in proc.actions
        if mode=='timeout_kill': assert 'kill' in proc.actions
    assert runner._proc is None and runner._active_request is None and runner._lock_fd is None and runner._log_fd is None and runner._cancelling is None and runner._status_polling is None
    for retired_fd in (lock_fd,log_fd):
        try: os.fstat(retired_fd)
        except OSError: pass
        else: raise AssertionError('owned descriptor not retired')
    assert log.read_bytes()==raw
    rows.append({'index':index,'target':target,'method':method.value,'complete':complete,'mode':mode,'actions':proc.actions,'initial_error':raised,'retried':retried,'result_ok':runner.result.ok,'reason':runner.result.reason})
(BASE/'cancel-results.json').write_text(json.dumps(rows,indent=2)+'\n')
summary={'cases':len(rows),'source':source,'source_unchanged':source=={p:hashlib.sha256((REPO/'src/beamo_wipe'/p).read_bytes()).hexdigest() for p in source},'native_acquisitions':len(forbidden_calls),'elapsed_s':time.monotonic()-start}
(BASE/'cancel-summary.json').write_text(json.dumps(summary,indent=2)+'\n'); print(json.dumps(summary))
assert not forbidden_calls and summary['source_unchanged']
