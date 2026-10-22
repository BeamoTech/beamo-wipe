"""PASS7 independent record-boundary matrix, with ordinary-file/fake actions."""
from pathlib import Path
import hashlib,json,os,random,tempfile
from unittest.mock import patch
from beamo_wipe import nwipe_runner as m
from beamo_wipe.engine_checks import check_payloads
from beamo_wipe.models import MethodId
SEED=0x2026102107
rng=random.Random(SEED)
stamp='[2026/10/21 13:14:15] info: '
N=3000
mismatches=[]; comparisons=0
native_realpath=os.path.realpath

def fake_realpath(path,*a,**kw):
    if os.fsdecode(path).startswith('/dev/'):return os.fspath(path)
    return native_realpath(path,*a,**kw)

def forbidden(*a,**kw):raise AssertionError('External process/device/signal action forbidden')
with tempfile.TemporaryDirectory(prefix='beamo-pass7-runner-matrix-') as scratch:
 logfile=Path(scratch)/'fake.log'
 with patch.object(m.subprocess,'Popen',forbidden),patch.object(m.subprocess,'run',forbidden),patch.object(os,'kill',forbidden),patch.object(os.path,'realpath',fake_realpath),patch.object(m,'_try_log_diag',lambda*a:None):
  for case in range(N):
   target=('/dev/sda','/dev/nvme0n100','/dev/sdabcdef')[case%3]
   column=m.nwipe_status_device_field(target).strip()
   foreign='/dev/x-'+column
   progress=[]
   for p in ('001.25','099.99','100.00','100.00000000000000000001'):
    for phase in ('writing','verifying','syncing','retrying','blanking','unknown'):
     progress.append(f'{target}: {p}%, round 1 of 1, pass 1 of 1, eta 00:00:01, [{phase}]')
   record_pool=[
    'ordinary', '', ' '*3, '-'*80, '*'*80, '  '+'*'*80,
    m.NWIPE_DRIVE_STATUS_HEADER,m.NWIPE_ERROR_SUMMARY_HEADER,
    'Error Summary','info: Error Summary','Erasure Summary',
    stamp+'Erasure Summary',stamp+m.NWIPE_ERROR_SUMMARY_HEADER,
    f' {column} | 0 | 0 | 0',f' {column} | 1 | 0 | 0',
    f' {column} | 0 | 0 | 1',f' {column} | malformed | 0 | 0',
    f' {column} | 100 | 100 | 100.00%',f' {column} | 99 | 100 | 99.00%',
    f' {column} | Erased | 120MB/s | 00:01:00 | FAKE/DISK',
    f'! {column} |-FAILED-| 120MB/s | 00:01:00 | FAKE/DISK',
    stamp+target+' is reported as IN USE',
    stamp+f"Unable to open device '{target}'.",
    stamp+target+': No sane device geometry',
    stamp+'Nwipe was aborted by the user',
    stamp+target+': >>> FAILURE! <<<',
    stamp+f"Verification mismatch on '{target}'",
    stamp+'No hidden sectors on '+target,
    stamp+'*** HIDDEN SECTORS DETECTED ! *** on '+target,
    stamp+'HIDDEN SECTORS INDETERMINATE! on '+target,
    stamp+'[UNKNOWN] We can\'t find the HPA line, has hdparm ouput unknown/changed? '+target,
    stamp+'hpa_dco_status: Failed to create stream to hdparm',
    stamp+'SG_IO bad/missing sense data '+target,
    stamp+target+', ATA, MODEL\u2028TEXT',
    'observed '+foreign,'observed /dev/sdb',
   ]+progress+[stamp+x for x in progress]
   chosen=[]
   for i in range(rng.randrange(2,24)):
    line=rng.choice(record_pool)
    ending=rng.choice(('\n','\n','\n','\r\n'))
    chosen.append(line+ending)
   text=stamp+'Program options are set as follows\n'+''.join(chosen)
   logfile.write_bytes(text.encode())
   projected=m.NwipeRunner()._scan_completion_log(str(logfile),target,m._log_signature(logfile.stat()))
   if projected is None:
    mismatches.append({'case':case,'kind':'unexpected-none','text':text});continue
   for method in MethodId:
    for code in (0,1,-15,143):
     expected=m.completion_for_method(code,text,target,method)
     actual=m.completion_for_method(code,projected,target,method)
     comparisons+=1
     if actual!=expected:mismatches.append({'case':case,'kind':'completion','method':method.value,'code':code,'target':target,'expected':expected,'actual':actual,'text':text,'projection':projected})
   expected=check_payloads(text,target);actual=check_payloads(projected,target);comparisons+=1
   if expected!=actual:mismatches.append({'case':case,'kind':'checks','target':target,'expected':expected,'actual':actual,'text':text,'projection':projected})
result={'seed':SEED,'sequences':N,'comparisons':comparisons,'targets':3,'mismatch_count':len(mismatches),'mismatches':mismatches[:20],'source_sha256':{'runner':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()},'native_or_device_actions':0}
Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items()if k!='mismatches'}))
raise SystemExit(bool(mismatches))
