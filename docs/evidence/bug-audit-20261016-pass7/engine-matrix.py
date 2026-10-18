from itertools import product
from pathlib import Path
import os, random, tempfile
from beamo_wipe.models import MethodId
from beamo_wipe.nwipe_runner import NwipeRunner, completion_for_method, _log_signature, NWIPE_DRIVE_STATUS_HEADER, nwipe_accepts_sigusr1
rng=random.Random(728031)
records=[
'irrelevant engine prose\n',
NWIPE_DRIVE_STATUS_HEADER+'\n',
'sda | Erased | 120MB/s | 01:25:04 | FAKE\n',
'*** End table ***\n',
'/dev/sda: >>> FAILURE! <<<\n',
'/dev/sdb: >>> FAILURE! <<<\n',
'Verification mismatch on /dev/sda\n',
'/dev/sda is reported as IN USE\n',
"Unable to open device '/dev/sda'.\n",
'Nwipe was aborted by the user\n',
'******** Error Summary ********\n',
'sda | 0 | 0 | 0\n',
'sda | 1 | 0 | 0\n',
'/dev/sda: 100.00%, round 1 of 1, pass 1 of 1, eta 00:00:00, [verifying]\n',
'/dev/sda: 100.00%, round 1 of 1, pass 3 of 3, eta 00:00:00, [verifying]\n',
'/dev/sda: 100.00%, round 1 of 1, pass 1 of 1, eta 00:00:00, [writing]\n',
'/dev/sda: 080.00%, round 1 of 1, pass 1 of 1, eta 00:00:01, [writing]\n',
'/dev/sda: 100.00%, round 2 of 2, pass 1 of 1, eta 00:00:00, [verifying]\n',
]
count=0
with tempfile.TemporaryDirectory(prefix='beamo-pass7-engine-') as d:
 p=Path(d)/'fixture.log'; runner=NwipeRunner()
 for i in range(1800):
  log=''.join(rng.choices(records,k=rng.randint(1,18)))
  p.write_text(log)
  projected=runner._scan_completion_log(str(p),'/dev/sda',_log_signature(p.stat()))
  assert projected is not None
  for method,code in product(MethodId,(0,1,-15,None)):
   actual=completion_for_method(code,log,'/dev/sda',method)
   scanned=completion_for_method(code,projected,'/dev/sda',method)
   assert actual==scanned,(i,method,code,actual,scanned,log,projected)
   count+=1
print(f'PASS {count} completion full-log/projection comparisons, 1800 seeded record-order fixtures')
readiness=0
for prefix,phrase,newline in product(('', 'info: ', '[2026/10/16 00:00:00] info: '),('Using direct I/O','Using cached I/O','Program options are set as follows','do not show GUI interface'),('', '\n')):
 observed=nwipe_accepts_sigusr1(prefix+phrase+newline)
 expected=prefix.startswith('[') and newline=='\n'
 assert observed==expected,(prefix,phrase,newline,observed)
 readiness+=1
print(f'PASS {readiness} exact readiness provenance/partial-record checks')
