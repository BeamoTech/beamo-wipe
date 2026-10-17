"""Fake completed processes -> runner -> evidence -> result across log sizes."""
import hashlib,json,tempfile
from pathlib import Path
from beamo_wipe.demo import discovery_for_scenario
from beamo_wipe.models import MethodId,WipeRequest
from beamo_wipe.evidence import build_evidence
from beamo_wipe.outcomes import present_evidence
from beamo_wipe import lang
import beamo_wipe.nwipe_runner as runner_module
runner_module._try_log_diag=lambda *a,**k:None
class Exited:
    def poll(self):return 0
rows=[]
discovery=discovery_for_scenario('happy');disk=discovery.selectable[0]
with tempfile.TemporaryDirectory(prefix='beamo-pass10-report-provenance-') as directory:
    for locale in ('en','fr','de'):
        lang.set_language(locale)
        for method in MethodId:
            for ending in ('\n','\r\n','\r\r\n'):
                for large in (False,True):
                    prefix=('ordinary note '+'x'*65500+'\n')*17 if large else ''
                    text=prefix+runner_module.NWIPE_DRIVE_STATUS_HEADER+ending+f'{runner_module.nwipe_status_device_field(disk.path)} | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n'
                    log=Path(directory)/'fake.log';log.write_bytes(text.encode())
                    request=WipeRequest(disk.path,method,discovery.boot.path,str(log))
                    runner=runner_module.NwipeRunner();runner._proc=Exited()
                    result=runner.poll(request)
                    evidence=build_evidence(disk=disk,discovery=discovery,method=method,request=request,result=result,started_at_wall=None,ended_at_wall=None,started_mono=0,ended_mono=1,argv=[],log_text=runner._log_tail,assessment_log_text=runner._assessment_log_text,language=locale)
                    view=present_evidence(evidence)
                    expected=ending=='\n'
                    assert result.ok is expected and view.success is expected
                    assert evidence['verification']['verified'] is (expected and method!=MethodId.QUICK_ZERO)
                    assert evidence['log_checksum_sha256']==hashlib.sha256(runner._log_tail.encode()).hexdigest()
                    assert log.read_bytes()==text.encode()
                    rows.append({'language':locale,'method':method.value,'ending':repr(ending),'large':large,'result':result.reason,'view':view.code,'outcome':evidence['outcome']})
print(json.dumps({'cases':len(rows),'rows':rows},indent=2))
