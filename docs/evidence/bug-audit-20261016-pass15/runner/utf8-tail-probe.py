"""Trace raw-tail vs normalized snapshot bounds. Only regular temporary log/evidence files."""
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tarfile
sys.path.insert(0, str(Path.cwd() / 'src'))
from beamo_wipe import nwipe_runner as m
from beamo_wipe import evidence as e
from beamo_wipe import support_export as x
from beamo_wipe.models import Disk, DiskKind, DiscoveryResult, MethodId, WipeRequest
from beamo_wipe.outcomes import present_evidence

BASE = Path('/tmp/pass15-runner/utf8-tail-probe')
BASE.mkdir(mode=0o700, exist_ok=True)
os.environ['BEAMO_WIPE_DRY_RUN'] = '1'
os.environ.pop('BEAMO_WIPE_LIVE', None)
notes = []
m._try_log_diag = lambda *args: notes.append(args)
def forbidden(*args, **kwargs):
    raise AssertionError('native effect forbidden')
m.subprocess.Popen = forbidden
m.subprocess.run = forbidden
m.pinned_nwipe_already_running = forbidden
m._recheck_identity_under_lock = forbidden
original_realpath = os.path.realpath
os.path.realpath = lambda p, *args, **kw: str(p) if str(p).startswith('/dev/') else original_realpath(p, *args, **kw)
e.evidence_identity = lambda: {'source_commit': 'a'*40, 'build_id': 'pass15-utf8-probe', 'build_status': 'development', 'source_dirty': True}

class Exited:
    returncode = 0
    def poll(self):
        return 0

def padding(size):
    whole, part = divmod(size, 65536)
    assert part != 1
    return (b'x'*65535+b'\n')*whole + (b'x'*(part-1)+b'\n' if part else b'')

status = (m.NWIPE_DRIVE_STATUS_HEADER+'\n sda | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n').encode()
disk = Disk('/dev/sda','sda','FAKE DISK','FAKE-SERIAL',1_000_000_000,'1',DiskKind.HDD,'sata','')
boot = Disk('/dev/sr0','sr0','FAKE BOOT','FAKE-BOOT',2_000_000_000,'2',DiskKind.UNKNOWN,'usb','BEAMO_WIPE',is_boot=True)
discovery = DiscoveryResult(disks=(disk,boot),selectable=(disk,),boot=boot,boot_identified=True)
rows, fixtures = [], {}
for char in ['A','é','€','😀']:
    encoded = char.encode()
    for cut in range(len(encoded)):
        first = encoded+b'\n'
        raw = first+padding(m.NWIPE_COMPLETION_LOG_BYTES+cut-len(first)-len(status))+status
        assert len(raw) == m.NWIPE_COMPLETION_LOG_BYTES+cut
        raw.decode('utf-8')  # All original files are complete valid UTF-8.
        name = f'utf8-{ord(char):x}-cut{cut}.log'
        fixtures[name] = raw
        logfile = BASE/name
        logfile.write_bytes(raw)
        logfile.chmod(0o600)
        for method in MethodId:
            runner = m.NwipeRunner()
            runner._proc = Exited()
            request = WipeRequest('/dev/sda',method,'/dev/sr0',str(logfile))
            runner._active_request=request
            result=runner.poll(request)
            assert result is not None and result.ok
            payload=e.build_evidence(disk=disk,discovery=discovery,method=method,request=request,result=result,
                started_at_wall='',ended_at_wall='',started_mono=0,ended_mono=1,argv=[],
                log_text=runner._log_tail,assessment_log_text=runner._assessment_log_text)
            path=BASE/f'result-{ord(char):x}-{cut}-{method.value}.json'
            payload['provenance']['evidence_file']=str(path)
            data=(json.dumps(payload,sort_keys=True,ensure_ascii=False)+'\n').encode()
            path.write_bytes(data)
            path.chmod(0o600)
            sidecar=Path(str(path)+'.sha256')
            sidecar.write_text(f'{hashlib.sha256(data).hexdigest()}  {path.name}\n')
            sidecar.chmod(0o600)
            try:
                x.prepare_terminal_evidence(path,'/dev/sda')
                export_ready=True
                export_error=''
            except Exception as exc:
                export_ready=False
                export_error=type(exc).__name__+': '+str(exc)
            snapshot,read_status=x.read_export_log(str(logfile),expected_sha256=payload['log_checksum_sha256'],expected_size_bytes=payload['log_snapshot_size_bytes'])
            assert snapshot == runner._log_tail.encode()
            assert logfile.read_bytes()==raw
            rows.append({'char':char,'cut':cut,'method':method.value,'raw_file_bytes':len(raw),
                'raw_file_sha256':hashlib.sha256(raw).hexdigest(),'raw_utf8_valid':True,
                'tail_normalized_bytes':len(runner._log_tail.encode()),'runner_ok':result.ok,
                'evidence_outcome':payload['outcome'],'presentation_code':payload['presentation']['code'],
                'direct_presentation_code':present_evidence(payload).code,
                'recovery_code':e.recover_result(path).code,'export_ready':export_ready,'export_error':export_error,
                'snapshot_read_status':read_status,'native_effects':0})
with tarfile.open(BASE.parent/'utf8-exact-log-fixtures.tar.gz','w:gz') as archive:
    for name,data in fixtures.items():
        info=tarfile.TarInfo(name); info.size=len(data);info.mode=0o600;info.mtime=0
        archive.addfile(info,io.BytesIO(data))
source={p:hashlib.sha256(Path('src/beamo_wipe',p).read_bytes()).hexdigest() for p in ['nwipe_runner.py','evidence.py','outcomes.py','support_export.py']}
summary={'cases':len(rows),'boundary_cuts':sum(r['cut']>0 for r in rows),
    'runner_success_presentation_indeterminate':sum(r['runner_ok'] and r['presentation_code']=='indeterminate' for r in rows),
    'controls_success':sum(r['cut']==0 and r['presentation_code'] in {'verified','unverified'} for r in rows),
    'native_effects':0,'source':source,'rows':rows}
(BASE.parent/'utf8-tail-probe.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in {'rows','source'}}))
