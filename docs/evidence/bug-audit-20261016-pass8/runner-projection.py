import hashlib, itertools, json, random, tempfile
from pathlib import Path
from beamo_wipe.models import MethodId
from beamo_wipe.nwipe_runner import NwipeRunner, _log_signature, completion_for_method, NWIPE_DRIVE_STATUS_HEADER
from beamo_wipe.engine_checks import check_payloads
rng=random.Random(2026101608)
lines=[
'noise',
'[2026/10/16 00:00:00] info: No hidden sectors on /dev/sda',
'[2026/10/16 00:00:00] warning: *** HIDDEN SECTORS DETECTED ! *** on /dev/sda',
'[2026/10/16 00:00:00] warning: HIDDEN SECTORS INDETERMINATE! on /dev/sda',
'[2026/10/16 00:00:00] error: hdparm reports invalid output, sector information may be invalid /dev/sda',
'Error Summary','******************************** Error Summary *********************************',
' sda | 0 | 0 | 0',' sda | 1 | 0 | 0',' sda | unknown | 0 | 0',' sdb | 0 | 0 | 0',
'Erasure Summary',' sda | 100 | 100 | 100.00%',' sda | 50 | 100 | 50.00%',
'***',NWIPE_DRIVE_STATUS_HEADER,
' sda | Erased | 100MB/s | 00:01:00 | FAKE',
' sda |-FAILED-| 100MB/s | 00:01:00 | FAKE',
'/dev/sda: >>> FAILURE! <<<','Verification mismatch on /dev/sda',
'/dev/sda is IN USE but --force is not set, not wiping it',
"Unable to open device '/dev/sda'.",'No sane device geometry for /dev/sda',
'Nwipe was aborted by the user',
]
for phase,pct,passes in itertools.product(['writing','verifying','retrying','syncing','???'],['0.00','99.99','100.00','100.00000000001'],[1,3]):
 lines.append(f'/dev/sda: {pct}%, round 1 of 1, pass {passes} of {passes}, eta 00:00:00, [{phase}]')
count=0
conservative=0
with tempfile.TemporaryDirectory(prefix='beamo-pass8-runner-projection-') as directory:
 path=Path(directory)/'fake.log'
 runner=NwipeRunner()
 for case in range(5000):
  text='\n'.join(rng.choices(lines,k=rng.randrange(1,14)))+'\n'
  path.write_text(text)
  projected=runner._scan_completion_log(str(path),'/dev/sda',_log_signature(path.stat()))
  assert projected is not None
  for method in MethodId:
   for code in [0,1,-15]:
    expected=completion_for_method(code,text,'/dev/sda',method)
    observed=completion_for_method(code,projected,'/dev/sda',method)
    assert expected==observed,(case,method,code,expected,observed,text,projected)
    count+=1
  a=check_payloads(text,'/dev/sda')
  b=check_payloads(projected,'/dev/sda')
  for checks in (a,b):
   for check in checks:
    if 'matched' not in check['provenance']:
     check['provenance'].pop('source',None)
  assert a==b,(case,a,b,text,projected)
print(json.dumps({'seed':2026101608,'logs':5000,'completion_comparisons':count,'engine_checks':5000,'conservative_malformed_summary_differences':conservative,'result':'PASS'}))
