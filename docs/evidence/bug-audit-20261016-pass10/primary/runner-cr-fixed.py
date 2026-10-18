from pathlib import Path
import json,tempfile
from beamo_wipe.models import MethodId,WipeRequest
import beamo_wipe.nwipe_runner as nr
nr._try_log_diag=lambda *args,**kwargs:None
class Exited:
    def poll(self):return 0
header=nr.NWIPE_DRIVE_STATUS_HEADER
records=[]
with tempfile.TemporaryDirectory(prefix='beamo-pass10-cr-proof-') as tmp:
    for name,suffix in [('lf',''),('cr','\r'),('double-cr','\r\r')]:
        log=f'{header}{suffix}\n sda | Erased | 120MB/s | 01:00:00 | FAKE/DISK\n'
        for large in (False,True):
            prefix=('ordinary message\n'*(nr.NWIPE_COMPLETION_LOG_BYTES//17+2)) if large else ''
            path=Path(tmp)/(name+str(large)+'.log');path.write_bytes((prefix+log).encode())
            runner=nr.NwipeRunner();runner._proc=Exited()
            result=runner.poll(WipeRequest(device='/dev/sda',method=MethodId.EVERYDAY,boot_device='/dev/sdb',logfile=str(path)))
            records.append({'ending':name,'large':large,'size':path.stat().st_size,'ok':result.ok,'reason':result.reason})
print(json.dumps(records,indent=2))
Path('/tmp/pass10-primary/runner-cr-fixed.json').write_text(json.dumps(records,indent=2)+'\n')
assert all(not r['ok'] for r in records if r['ending']!='lf'),'Malformed completion provenance gained success when projected'
