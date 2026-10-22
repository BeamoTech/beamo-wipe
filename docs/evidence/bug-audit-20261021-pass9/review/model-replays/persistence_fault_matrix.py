"""Fresh regular-file persistence fault/retry model; never opens a device.

This checks published bytes, private modes, checksum truth and retry/reopen
behavior. Injected asynchronous errors do not claim atomic compare/swap.
"""
from pathlib import Path
import errno, hashlib, itertools, json, os, sys, tempfile
from pytest import MonkeyPatch
sys.path.insert(0,'/workspace/beamo-wipe/src')
from beamo_wipe.report_intent import ReportIntentStore
from beamo_wipe.session_recovery import SessionStore,NAME,_bytes
from beamo_wipe.safety import SafetyError
from beamo_wipe import nwipe_runner,app  # import before replacing process boundaries

ROOT=Path(__file__).parent
metrics={'cases':0,'successful_operations':0,'injected_refusals':0,'clean_retries':0,'reopens':0,'post_error_visible_new_records':0,'native_callbacks':0,'unexpected':[]}
BOOT='00000000-0000-0000-0000-000000000001';BUILD='a'*64
fields=('write','fsync','replace','pread','close')

def forbidden(*args,**kwargs):
 metrics['native_callbacks']+=1;raise AssertionError('native callback forbidden')

def checked_journal(path):
 env=json.loads(path.read_bytes());assert set(env)=={'payload','sha256'}
 assert hashlib.sha256(_bytes(env['payload'])).hexdigest()==env['sha256']
 assert env['payload']['phase']=='preflight' and env['payload']['context'] is None and env['payload']['terminal'] is None
 assert path.stat().st_mode&0o777==0o600
 return env['payload']

with MonkeyPatch.context()as global_patch,tempfile.TemporaryDirectory(prefix='beamo-pass9-persistence-')as folder:
 global_patch.setenv('BEAMO_WIPE_DRY_RUN','1');global_patch.delenv('BEAMO_WIPE_LIVE',raising=False)
 for name in ('subprocess.run','subprocess.Popen','beamo_wipe.discover.run_lsblk','beamo_wipe.discover.read_cmdline','beamo_wipe.discover.read_mount_sources','beamo_wipe.nwipe_runner.NwipeRunner.start','beamo_wipe.app._shutdown'):
  global_patch.setattr(name,forbidden)
 for kind,short,field,index,error_kind,after in itertools.product(('preference','journal'),(1,3,65536),fields,(1,2,3),('io','interrupt'),(False,True)):
  metrics['cases']+=1; directory=Path(folder)/str(metrics['cases']);directory.mkdir(mode=0o700)
  if kind=='preference':
   store=ReportIntentStore(directory);store.save(False);path=directory/store.NAME
   def operation():store.save(True)
   def read():return store.load()
   old=False;new=True
  else:
   store=SessionStore(directory,boot=BOOT,build=BUILD).open();path=directory/NAME
   old=store.record['session'];new='b'*32
   def operation():store.save({'session':new})
   def read():return checked_journal(path)['session']
  initial=path.read_bytes();triggered=[];observed=[];counter=[0]
  real={name:getattr(os,name)for name in fields}
  def injected(*args,**kwargs):
   counter[0]+=1;selected=counter[0]==index
   # close is modeled as already-retired even when its result is an error;
   # Python callers must never retry this descriptor number.
   do_real=(after or field=='close')if selected else True
   result=real[field](*args,**kwargs)if do_real else None
   if selected:
    triggered.append(True)
    if error_kind=='interrupt':raise KeyboardInterrupt('fake persistence interruption')
    raise OSError(errno.EIO,'fake persistence I/O error')
   return result
  try:
   with MonkeyPatch.context()as fault:
    fault.setattr(os,'write',lambda fd,data:real['write'](fd,data[:short]))
    fault.setattr(os,'pread',lambda fd,size,offset:real['pread'](fd,min(size,short),offset))
    # Preserve short-I/O behavior inside the fault target too.
    if field=='write':
     underlying=real['write'];real[field]=lambda fd,data:underlying(fd,data[:short])
    elif field=='pread':
     underlying=real['pread'];real[field]=lambda fd,size,offset:underlying(fd,min(size,short),offset)
    fault.setattr(os,field,injected)
    operation()
   metrics['successful_operations']+=1
   assert not triggered
   assert read()==new
  except (OSError,SafetyError,KeyboardInterrupt):
   metrics['injected_refusals']+=1;assert triggered
   actual=read();assert actual in (old,new)
   if actual==new:metrics['post_error_visible_new_records']+=1
   # A recorded invalid journal cannot be reused until reopened. All other
   # ordinary retries may complete; old/new bytes alone never authorize erase.
   if kind=='journal' and store.invalid:
    try:operation()
    except SafetyError:pass
    else:raise AssertionError('invalid journal accepted another write')
   else:
    operation();assert read()==new;metrics['clean_retries']+=1
  finally:
   if kind=='journal':store.close()
  if kind=='journal':
   reopened=SessionStore(directory,boot=BOOT,build=BUILD).open()
   assert not reopened.invalid and reopened.previous
   assert reopened.record==checked_journal(path)
   reopened.close()
  else:assert ReportIntentStore(directory).load()in(False,True)
  metrics['reopens']+=1
assert metrics['successful_operations']>0 and metrics['injected_refusals']>0 and metrics['clean_retries']>0 and not metrics['native_callbacks']
metrics['source_sha256']={str(p.relative_to('/workspace/beamo-wipe')):hashlib.sha256(p.read_bytes()).hexdigest()for p in(Path('/workspace/beamo-wipe/src/beamo_wipe')/n for n in('report_intent.py','session_recovery.py'))}
(ROOT/'persistence-fault-matrix.json').write_text(json.dumps(metrics,indent=2)+'\n')
print(json.dumps({k:v for k,v in metrics.items()if k!='source_sha256'}))
