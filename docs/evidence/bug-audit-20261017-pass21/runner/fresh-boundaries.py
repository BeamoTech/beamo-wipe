"""Pass21 semantic matrix: inert devices, fake processes, ordinary files only."""
import builtins
import hashlib
import io
import itertools
import json
import os
from pathlib import Path
import socket
import stat
import sys
import time

REPO = Path('/root/dev/Beamo Wipe')
assert sys.executable == '/tmp/beamo-pass21-python/bin/python3', sys.executable
GUARD = Path('/tmp/beamo-pass21-fallback-guard')
assert str(GUARD) in os.environ['PATH'].split(os.pathsep)
guard_manifest = json.loads(Path('/tmp/pass21-primary/guard-manifest.json').read_text())
assert len(guard_manifest) == 8
assert all(Path(path).parent == GUARD and hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest for path,digest in guard_manifest.items())
sys.path.insert(0, str(REPO / 'src'))
os.environ['BEAMO_WIPE_DRY_RUN'] = '1'
os.environ['BEAMO_WIPE_LIVE'] = '0'
from beamo_wipe import evidence as em, nwipe_runner as m
from beamo_wipe.engine_checks import check_payloads
from beamo_wipe.evidence import build_evidence, recover_result, write_evidence_atomic
from beamo_wipe.methods import METHODS
from beamo_wipe.models import Disk, DiskKind, DiscoveryResult, MethodId, WipeRequest
from beamo_wipe.outcomes import present_evidence
from beamo_wipe.support_export import prepare_terminal_evidence, read_export_log

BASE = Path('/tmp/pass21-runner')
BASE.mkdir(mode=0o700)
assert BASE.stat().st_uid == os.getuid() and stat.S_IMODE(BASE.stat().st_mode) == 0o700
PATHS = ['nwipe_runner.py','engine_checks.py','evidence.py','outcomes.py','support_export.py','session_recovery.py','methods.py','models.py']
source = {p: hashlib.sha256((REPO/'src/beamo_wipe'/p).read_bytes()).hexdigest() for p in PATHS}
forbidden_calls = []
def forbidden(*args, **kwargs):
    forbidden_calls.append(repr(args[:1]))
    raise AssertionError('forbidden native acquisition')
m.subprocess.Popen = forbidden
m.subprocess.run = forbidden
m.os.system = forbidden
m.os.kill = forbidden
m.os.killpg = forbidden
socket.socket = forbidden
socket.create_connection = forbidden
m.pinned_nwipe_already_running = forbidden
m._recheck_identity_under_lock = forbidden
m._try_log_diag = lambda *_a, **_k: None
em.evidence_identity = lambda: {'source_commit':'a'*40,'build_id':'local','build_status':'development','source_dirty':True}
def native_path(path):
    return isinstance(path,(str,bytes,os.PathLike)) and os.fsdecode(path).startswith(('/dev/', '/sys/', '/proc/'))
original_open = os.open
def ordinary_open(path, *args, **kwargs):
    if native_path(path):
        forbidden(path)
    return original_open(path, *args, **kwargs)
os.open = ordinary_open
original_builtin_open, original_io_open = builtins.open, io.open
def ordinary_builtin_open(path,*args,**kwargs):
    if native_path(path): forbidden(path)
    return original_builtin_open(path,*args,**kwargs)
def ordinary_io_open(path,*args,**kwargs):
    if native_path(path): forbidden(path)
    return original_io_open(path,*args,**kwargs)
builtins.open, io.open = ordinary_builtin_open, ordinary_io_open
original_realpath = os.path.realpath
def ordinary_realpath(path, *args, **kwargs):
    return os.fspath(path) if os.fsdecode(path).startswith('/dev/') else original_realpath(path,*args,**kwargs)
os.path.realpath = ordinary_realpath

STAMP = '[2026/10/17 12:00:00] info: '
EH = '******************************** Error Summary *********************************\n'
CLOSE = '*'*80+'\n'
PAD = ('p'*65535+'\n')*17

def table(target):
    return m.NWIPE_DRIVE_STATUS_HEADER+'\n'+m.nwipe_status_device_field(target)+' | Erased | 1MB/s | 00:00:01 | FAKE/DISK\n'+CLOSE

def progress(target, total, phase, pct='100.00', pass_i=None):
    return f'{target}: {pct}%, round 1 of 1, pass {total if pass_i is None else pass_i} of {total}, eta 00:00:00, [{phase}]\n'

class Process:
    def __init__(self, code=0): self.returncode=code; self.actions=[]
    def poll(self): self.actions.append('poll'); return self.returncode
    def terminate(self): self.actions.append('terminate'); self.returncode=-15
    def wait(self, timeout): self.actions.append('wait'); return self.returncode
    def kill(self): raise AssertionError('bounded fake should not require kill')

def fixture(target, method, raw, index):
    directory=BASE/'fixtures'/f'{index:04d}'
    directory.mkdir(mode=0o700,parents=True)
    logfile=directory/'fake.log'; logfile.write_bytes(raw); logfile.chmod(0o600)
    req=WipeRequest(target,method,'/dev/sr0',str(logfile))
    runner=m.NwipeRunner(); runner._proc=Process(); runner._active_request=req; runner._last_logfile=str(logfile)
    result=runner.poll(req)
    assert result is not None
    assert runner._proc is None and runner._log_fd is None and runner._lock_fd is None
    assert logfile.read_bytes()==raw
    return directory,logfile,req,runner,result

rows=[]; mismatches=[]; semantic_errors=[]; actual=[]; roundtrips=[]; mixed=[]
start=time.monotonic(); index=0
for target,method in itertools.product(['/dev/sda','/dev/nvme0n100','/dev/mmcblk100'],list(MethodId)):
    spec=METHODS[method]; col=m.nwipe_status_device_field(target).strip()
    phase='writing' if spec.verify=='off' else 'verifying'
    final=progress(target,spec.overwrite_passes,phase)
    partial=progress(target,spec.overwrite_passes,phase,'050.00',1)
    wrong=progress(target,spec.overwrite_passes+1,phase)
    positive=STAMP+'No hidden sectors on '+target+'\n'
    err0=EH+f' {col} | 0 | 0 | 0\n'
    err1=EH+f' {col} | 0 | 1 | 0\n'
    variants=[
        ('table',table(target),True,'completed',None),
        ('final_sample',final,True,'completed',None),
        ('final_then_partial',final+partial,False,'completion_missing',None),
        ('table_then_partial',table(target)+partial,True,'completed',None),
        ('wrong_then_table',wrong+table(target),False,'indeterminate',None),
        ('table_then_wrong',table(target)+wrong,False,'indeterminate',None),
        ('nonzero_then_table',err1+CLOSE+table(target),False,'engine_failed','fail'),
        ('table_then_nonzero',table(target)+err1+CLOSE,False,'engine_failed','fail'),
        ('zero_then_table',err0+CLOSE+table(target),True,'completed','pass'),
        ('zero_duplicate_then_table',err0+f' {col} | 0 | 0 | 0\n'+CLOSE+table(target),True,'completed','pass'),
        ('zero_then_malformed_foreign',err0+' malformed foreign summary row\n'+CLOSE+table(target),True,'completed','unavailable'),
        ('headerless_nonzero',f' {col} | 0 | 1 | 0\n'+table(target),False,'indeterminate','unavailable'),
        ('busy_contradiction',STAMP+target+' is reported as IN USE\n'+table(target),False,'indeterminate',None),
        ('model_failure',STAMP+'Model: '+target+': >>> FAILURE! <<<\n'+table(target),True,'completed',None),
        ('foreign_failure','/dev/sdz: >>> FAILURE! <<<\n'+table(target),True,'completed',None),
        ('positive_with_foreign_unknown',positive+STAMP+'HIDDEN SECTORS INDETERMINATE! on /dev/sdz\n'+table(target),True,'completed',None),
        ('positive_with_target_unknown',positive+STAMP+'HIDDEN SECTORS INDETERMINATE! on '+target+'\n'+table(target),True,'completed',None),
    ]
    for name,text,want_ok,want_reason,want_io in variants:
        index+=1
        logfile=BASE/'projection.log'; raw=text.encode(); logfile.write_bytes(raw)
        projection=m.NwipeRunner()._scan_completion_log(str(logfile),target,m._log_signature(logfile.stat()))
        assert projection is not None
        full=m.completion_for_method(0,text,target,method); projected=m.completion_for_method(0,projection,target,method)
        checks=check_payloads(text,target)
        same=full==projected and checks==check_payloads(projection,target)
        semantic=(full[0]==want_ok and full[2]==want_reason and (want_io is None or checks[1]['status']==want_io))
        if name=='positive_with_foreign_unknown': semantic=semantic and checks[0]['status']=='pass'
        if name=='positive_with_target_unknown': semantic=semantic and checks[0]['status']=='unavailable'
        row={'target':target,'method':method.value,'variant':name,'full':full,'projection':projected,'checks':[c['status'] for c in checks],'same':same,'semantic':semantic,'input_sha256':hashlib.sha256(raw).hexdigest()}
        rows.append(row)
        if not same: mismatches.append({**row,'input':text,'projected_text':projection})
        if not semantic: semantic_errors.append(row)
        cut=text.rfind(m.NWIPE_DRIVE_STATUS_HEADER)
        big=(text[:cut]+PAD+text[cut:] if cut>0 else PAD+text).encode()
        directory,logfile,req,runner,result=fixture(target,method,big,index)
        assert (result.ok,result.reason)==(full[0],full[2])
        assert runner._assessment_log_text is not None
        assert check_payloads(runner._assessment_log_text,target)==checks
        actual.append({'target':target,'method':method.value,'variant':name,'bytes':len(big),'sha256':hashlib.sha256(big).hexdigest(),'ok':result.ok,'reason':result.reason})
        # Successful records with markers inside the exact snapshot must roundtrip.
        if result.ok:
            disk=Disk(target,target.rsplit('/',1)[-1],'FAKE','FAKE-SERIAL',1_000_000_000,'1',DiskKind.HDD,'sata','')
            boot=Disk('/dev/sr0','sr0','FAKE BOOT','FAKE-BOOT',2_000_000_000,'2',DiskKind.UNKNOWN,'usb','BEAMO_WIPE',is_boot=True)
            evidence=build_evidence(disk=disk,discovery=DiscoveryResult(disks=(disk,boot),selectable=(disk,),boot=boot,boot_identified=True),method=method,request=req,result=result,started_at_wall='',ended_at_wall='',started_mono=0,ended_mono=1,argv=[],log_text=runner._log_tail,assessment_log_text=runner._assessment_log_text)
            code='unverified' if method==MethodId.QUICK_ZERO else 'verified'
            assert present_evidence(evidence).code==code
            snapshot,status=read_export_log(str(logfile),expected_sha256=evidence['log_checksum_sha256'],expected_size_bytes=evidence['log_snapshot_size_bytes'])
            assert status=='tail' and snapshot==runner._log_tail.encode()
            path=write_evidence_atomic(evidence,log_dir=directory,device_path=target,target_device=target)
            assert recover_result(path).code==code
            assert prepare_terminal_evidence(path,target).data==path.read_bytes()
            # A changed authenticated suffix cannot be recovered as success.
            logfile.write_bytes(big+b'changed\n')
            assert recover_result(path).code=='indeterminate'
            logfile.write_bytes(big)
            assert recover_result(path).code==code
            roundtrips.append({'target':target,'method':method.value,'variant':name,'code':code,'tamper_refused':True})

# Separate malformed-positive records are traced, not automatically labeled bugs.
for target,suffix,order in itertools.product(['/dev/sda','/dev/nvme0n100','/dev/mmcblk100'],[' uncertain',' (indeterminate)',' -- HIDDEN SECTORS INDETERMINATE!','\x00','\u2028foreign','/part mentions /dev/sda'],['before','after','foreign']):
    positive=STAMP+'No hidden sectors on '+target+'\n'
    other='/dev/sdz' if order=='foreign' else target
    malformed=STAMP+'No hidden sectors on '+other+suffix+'\n'
    text=malformed+positive if order=='before' else positive+malformed
    mixed.append({'target':target,'suffix':suffix,'order':order,'status':check_payloads(text,target)[0]['status']})

for filename,data in [('fresh-rows.json',rows),('fresh-mismatches.json',mismatches),('fresh-semantic-errors.json',semantic_errors),('fresh-actual.json',actual),('fresh-roundtrips.json',roundtrips),('mixed-positive-traces.json',mixed)]:
    (BASE/filename).write_text(json.dumps(data,indent=2)+'\n')
summary={'source':source,'guard_manifest':guard_manifest,'interpreter':sys.executable,'short_cases':len(rows),'actual_large_cases':len(actual),'successful_roundtrips':len(roundtrips),'mixed_advisory_traces':len(mixed),'mismatches':len(mismatches),'semantic_errors':len(semantic_errors),'native_acquisitions':len(forbidden_calls),'elapsed_s':time.monotonic()-start,'source_unchanged':source=={p:hashlib.sha256((REPO/'src/beamo_wipe'/p).read_bytes()).hexdigest() for p in PATHS}}
(BASE/'fresh-summary.json').write_text(json.dumps(summary,indent=2)+'\n'); print(json.dumps(summary))
assert not mismatches and not semantic_errors and not forbidden_calls and summary['source_unchanged']
