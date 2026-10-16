from itertools import product
from beamo_wipe.verification_evidence import build_gate_receipt,verify_gate_receipt
n=0;accepted=0
for length in range(6):
 for kinds in product(('skip','xfail'),repeat=length):
  for skipped in range(6):
   for xfailed in range(6):
    expected=skipped==kinds.count('skip') and xfailed==kinds.count('xfail')
    try:
     record=build_gate_receipt(gate='tests',status='pass',command='fixture command',source_commit='a'*40,build_id='fixture',environment={'platform':'linux'},measured={'passed':1,'failed':0,'errors':0,'skipped':skipped,'xfailed':xfailed,'deselected':0,'total':1+skipped+xfailed},skips=[{'id':f'case-{i}','kind':kind,'reason':'fixture'} for i,kind in enumerate(kinds)],log_sha256='b'*64,started_at='2026-10-16T00:00:00Z',ended_at='2026-10-16T00:00:01Z')
    except RuntimeError:
     assert not expected,(kinds,skipped,xfailed)
    else:
     assert expected,(kinds,skipped,xfailed)
     assert verify_gate_receipt(record)==record
     accepted+=1
    n+=1
print(n,'independent kind/count combinations:',accepted,'valid accepted/revalidated;',n-accepted,'inconsistent rejected')
