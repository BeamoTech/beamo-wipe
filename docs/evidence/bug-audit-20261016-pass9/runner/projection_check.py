import itertools, pathlib
from beamo_wipe.nwipe_runner import NwipeRunner,_log_signature,completion_for_method,NWIPE_DRIVE_STATUS_HEADER
from beamo_wipe.models import MethodId
from beamo_wipe.engine_checks import check_payloads
parts=[
'/dev/sda: 50.00%, round 1 of 1, pass 1 of 1, eta 00:00:00, [writing]',
'/dev/sda: 100.00%, round 1 of 1, pass 1 of 1, eta 00:00:00, [verifying]',
'/dev/sda: 100.00%, round 1 of 1, pass 1 of 3, eta 00:00:00, [writing]',
'******************************** Error Summary *********************************',
' sda | 1 | 0 | 0',' sda | 0 | 0 | 0',
'********************************************************************************',NWIPE_DRIVE_STATUS_HEADER,
' sda | Erased | 120MB/s | 01:25:04 | TEST/DISK',
' sda | -FAILED- | 120MB/s | 01:25:04 | TEST/DISK',
'info: Verification mismatch on /dev/sda',
'info: /dev/sda is reported as IN USE',
'info: No hidden sectors on /dev/sda',
'info: /dev/sda: >>> FAILURE! <<<',
]
f=pathlib.Path('/tmp/pass9-runner/projection.log'); runner=NwipeRunner(); mismatches=[]; tested=0
for n in range(1,5):
 for chosen in itertools.product(parts,repeat=n):
  text='\n'.join(chosen)+'\n'; f.write_text(text)
  projection=runner._scan_completion_log(str(f),'/dev/sda',_log_signature(f.stat()))
  assert projection is not None
  a=[completion_for_method(0,text,'/dev/sda',m) for m in MethodId],check_payloads(text,'/dev/sda')
  b=[completion_for_method(0,projection,'/dev/sda',m) for m in MethodId],check_payloads(projection,'/dev/sda')
  tested+=1
  if a!=b:
   mismatches.append((text,projection,repr(a),repr(b)))
   if len(mismatches)>=5: break
 if mismatches:break
print('cases',tested,'mismatches',mismatches)
