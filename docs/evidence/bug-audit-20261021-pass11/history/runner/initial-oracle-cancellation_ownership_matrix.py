"""Actual runner Stop/terminal ownership with scripted fake processes; no spawn/signals."""
from pathlib import Path
import hashlib,itertools,json,subprocess,tempfile
from beamo_wipe.models import MethodId,WipeRequest
from beamo_wipe.methods import METHODS
from beamo_wipe.nwipe_runner import NwipeRunner,ProcessStatusError,SafetyError

ROOT=Path(__file__).resolve().parent
REPO=Path('/workspace/beamo-wipe')
MODES=('exited0','exited1','natural_on_stop','stopped','clean0_after_stop','gone_on_stop','denied_then_exit','kill_after_timeout','wait_error','unstoppable')
KINDS=('progress','status','missing','partial','foreign','wrong_method','verify_failure','truncated')
COUNTS={'states':0,'initial_positive_completions':0,'initial_negative_terminal_results':0,'cancelled_results':0,'uncertain_ownership_preserved':0,'recovery_terminal_classifications':0,'duplicate_terminal_calls':0,'native_callbacks':0,'mismatches':[]}

class Proc:
 def __init__(self,mode):self.mode=mode;self.returncode=None;self.calls=[]
 def poll(self):
  self.calls.append('poll')
  if self.returncode is None and self.mode in ('exited0','exited1'):self.returncode=int(self.mode[-1])
  return self.returncode
 def terminate(self):
  self.calls.append('terminate')
  if self.mode in ('natural_on_stop','clean0_after_stop'):self.returncode=0
  elif self.mode=='stopped':self.returncode=-15
  elif self.mode=='gone_on_stop':self.returncode=0;raise ProcessLookupError('fake gone')
  elif self.mode=='denied_then_exit':self.returncode=0;raise PermissionError('fake denied')
  elif self.mode in ('kill_after_timeout','unstoppable'):raise PermissionError('fake denied')
 def kill(self):
  self.calls.append('kill')
  if self.mode=='unstoppable':raise PermissionError('fake kill denied')
  self.returncode=-9
 def wait(self,timeout):
  self.calls.append('wait:'+str(timeout))
  if self.mode=='wait_error':raise OSError('fake wait unreadable')
  if self.returncode is None:raise subprocess.TimeoutExpired('fake',timeout)
  return self.returncode

def evidence(method,kind):
 spec=METHODS[method];n=spec.overwrite_passes;phase='writing' if spec.verify=='off' else 'verifying'
 progress=f'/dev/vda: 100.00%, round 1 of 1, pass {n} of {n}, eta 00:00:00, [{phase}]\n'
 status='********************************* Drive Status *********************************\n      vda | Erased | 120MB/s | 00:01:00 | OWNED FAKE\n'
 return {'progress':progress,'status':status,'missing':'ordinary diagnostic\n','partial':f'/dev/vda: 050.00%, round 1 of 1, pass 1 of {n}, eta 00:00:10, [writing]\n','foreign':progress.replace('/dev/vda','/dev/vdb'),'wrong_method':f'/dev/vda: 100.00%, round 1 of 1, pass {n+1} of {n+1}, eta 00:00:00, [{phase}]\n'+status,'verify_failure':'[2026/10/21 06:00:00] error: Verification mismatch on /dev/vda\n','truncated':progress.rstrip('\n')}[kind]

def natural(kind,code):
 if kind=='verify_failure':return False,'verification_failed'
 if code!=0:return False,'process_failed'
 if kind in ('progress','status'):return True,'completed'
 if kind in ('wrong_method','truncated'):return False,'indeterminate'
 return False,'completion_missing'

with tempfile.TemporaryDirectory(prefix='beamo-pass11-cancel-') as temp:
 for method,kind,mode in itertools.product(MethodId,KINDS,MODES):
  COUNTS['states']+=1
  logfile=Path(temp)/'owned.log';logfile.write_text(evidence(method,kind))
  request=WipeRequest('/dev/vda',method,'/dev/sr0',str(logfile))
  runner=NwipeRunner();proc=Proc(mode);runner._proc=proc;runner._active_request=request;runner._last_logfile=str(logfile)
  initial_error=None
  try:runner.cancel()
  except (SafetyError,OSError) as exc:initial_error=exc
  try:
   if mode in ('wait_error','unstoppable'):
    assert initial_error is not None,(mode,'expected error')
    assert runner._proc is proc and runner._active_request==request and runner.result is None
    assert runner._cancelling is None and runner._status_polling is None
    COUNTS['uncertain_ownership_preserved']+=1
    proc.returncode=0
    runner.cancel()
    expected=natural(kind,0);COUNTS['recovery_terminal_classifications']+=1
   else:
    assert initial_error is None,(mode,type(initial_error).__name__)
    if mode=='exited1':expected=natural(kind,1)
    elif mode in ('stopped','kill_after_timeout'):expected=(False,'cancelled')
    elif mode=='clean0_after_stop' and kind not in ('progress','status'):expected=(False,'cancelled')
    else:expected=natural(kind,0)
    if expected[0]:COUNTS['initial_positive_completions']+=1
    elif expected[1]=='cancelled':COUNTS['cancelled_results']+=1
    else:COUNTS['initial_negative_terminal_results']+=1
   result=runner.result
   assert result is not None and (result.ok,result.reason)==expected,(expected,result)
   assert runner._proc is None and runner._active_request is None
   assert runner._lock_fd is None and runner._log_fd is None and not runner._cleanup_failed
   if result.ok:assert runner.progress==100.0
   else:assert runner.progress is None or runner.progress<100.0
   calls=list(proc.calls);same=result;runner.cancel()
   assert runner.result is same and proc.calls==calls
   assert runner.poll(request) is same
   COUNTS['duplicate_terminal_calls']+=1
   if mode.startswith('exited'):assert not any(x in proc.calls for x in ('terminate','kill'))
  except AssertionError as exc:COUNTS['mismatches'].append({'method':method.value,'kind':kind,'mode':mode,'error':str(exc)})
COUNTS['source_sha256']={n:hashlib.sha256((REPO/n).read_bytes()).hexdigest() for n in ('src/beamo_wipe/nwipe_runner.py','src/beamo_wipe/methods.py','src/beamo_wipe/models.py','src/beamo_wipe/sleep_inhibit.py')}
COUNTS['scope']='Supporting scripted-fake process state-space through actual cancel/poll APIs. No actual subprocess, signal, engine, device or physical qualification. Not extra canonical tests.'
(ROOT/'cancellation-ownership-matrix.json').write_text(json.dumps(COUNTS,indent=2)+'\n')
print(json.dumps(COUNTS));assert not COUNTS['mismatches']
