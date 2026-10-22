"""Finite same-boot terminal provenance model; fake inventory, owned files only."""
import copy
import hashlib
import itertools
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

from beamo_wipe import evidence
from beamo_wipe.models import Disk, DiskKind, DiscoveryResult, MethodId, WipeRequest, WipeResult
from beamo_wipe.safety import SafetyError
from beamo_wipe.session_recovery import SessionStore

BOOT = '00000000-0000-0000-0000-000000000001'
BUILD = 'a' * 64
MUTATIONS = ('normal', 'json_bytes', 'sidecar_bytes', 'json_mode', 'json_link', 'sidecar_mode', 'sidecar_link', 'log_bytes', 'log_mode', 'log_link', 'method_context', 'target_context')
COUNTS = dict(scenarios=0, accepted=0, refused=0, restored=0, native_callbacks=0)


def denied_native(*args, **kwargs):
    COUNTS['native_callbacks'] += 1
    raise AssertionError('native callback forbidden')


def run(root):
    for method, identity, mutation in itertools.product(MethodId, ('hdd','nvme'), MUTATIONS):
        COUNTS['scenarios'] += 1
        directory = root / str(COUNTS['scenarios'])
        directory.mkdir(mode=0o700)
        boot = Disk('/dev/sdb','sdb','Fake boot','BOOT-1',16000000000,'16',DiskKind.UNKNOWN,'USB','',is_boot=True)
        target_path = '/dev/sda' if identity == 'hdd' else '/dev/nvme0n1'
        target = Disk(target_path, Path(target_path).name,'Fake target','TARGET-1',256000000000,'256',DiskKind.HDD if identity == 'hdd' else DiskKind.NVME,'SATA' if identity == 'hdd' else 'NVMe','')
        discovery = DiscoveryResult(disks=(boot,target),selectable=(target,),boot=boot,boot_identified=True)
        with patch('beamo_wipe.safety.DEFAULT_LOG_DIR', directory):
            first = SessionStore(directory,boot=BOOT,build=BUILD).open()
            request = WipeRequest(target.path, method, boot.path, str(directory/'nwipe-owned.log'))
            first.arm(discovery,request)
            text = '********************************* Drive Status *********************************\n' + f'{target.name} | Erased | 120MB/s | 01:25:04 | FAKE/DISK\n'
            logfile = Path(request.logfile)
            logfile.write_text(text)
            logfile.chmod(0o600)
            record = evidence.build_evidence(disk=target,discovery=discovery,method=method,request=request,result=WipeResult(True,0,'done',request.logfile),started_at_wall='',ended_at_wall='',started_mono=first.record['created'],ended_mono=first.record['created'],argv=[],log_text=text)
            path = evidence.write_evidence_atomic(record,log_dir=directory,device_path=target.path,target_device=target.path)
            first.finish(path)
            first.close()
            second = SessionStore(directory,boot=BOOT,build=BUILD).open()
            sidecar = Path(str(path)+'.sha256')
            saved = {p:p.read_bytes() for p in (path,sidecar,logfile)}
            context = copy.deepcopy(second.record['context'])
            links = []
            if mutation == 'method_context':
                second.record['context']['method'] = next(item.value for item in MethodId if item != method)
            elif mutation == 'target_context':
                second.record['context']['target'] = boot.path
            elif mutation != 'normal':
                name, change = mutation.split('_')
                changed = {'json':path,'sidecar':sidecar,'log':logfile}[name]
                if change == 'bytes': changed.write_bytes(b'changed')
                elif change == 'mode': changed.chmod(0o644)
                else:
                    link = directory / ('exposed-'+name)
                    os.link(changed,link)
                    links.append(link)
            try:
                try:
                    result = second.terminal()
                except (SafetyError, ValueError, KeyError, TypeError, AttributeError):
                    assert mutation != 'normal', (method,identity,mutation)
                    COUNTS['refused'] += 1
                else:
                    assert mutation == 'normal', (method,identity,mutation,result)
                    COUNTS['accepted'] += 1
                for link in links: link.unlink()
                for p, data in saved.items():
                    p.write_bytes(data)
                    p.chmod(0o600)
                second.record['context'] = context
                restored_path, restored_record = second.terminal()
                assert restored_path == path
                assert restored_record['method']['id'] == method.value
                COUNTS['restored'] += 1
            finally:
                second.close()
            assert all(getattr(second,field)==-1 for field in ('fd','owner','quiescent'))

with tempfile.TemporaryDirectory(prefix='pass13-provenance-') as temporary:
    with patch.dict(os.environ, {'BEAMO_WIPE_DRY_RUN':'1'}), patch('beamo_wipe.nwipe_runner.pinned_nwipe_already_running',return_value=False), patch('beamo_wipe.discover.run_lsblk',denied_native), patch('beamo_wipe.nwipe_runner.NwipeRunner.start',denied_native):
        run(Path(temporary))
assert COUNTS == dict(scenarios=72,accepted=6,refused=66,restored=72,native_callbacks=0), COUNTS
print(json.dumps(dict(status='pass', **COUNTS), sort_keys=True))
