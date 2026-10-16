"""Fake two-scan controller, normalized request and helper receipt roundtrip."""
import copy, json, os, subprocess, sys, tempfile
os.environ["BEAMO_WIPE_DRY_RUN"]="1"
os.environ.pop("BEAMO_WIPE_LIVE",None)
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=['src','tests']
from beamo_wipe import support_export as export
from beamo_wipe.discover import node_to_disk
from beamo_wipe.models import DiscoveryResult
from beamo_wipe.safety import SafetyError
from test_usb_report_workflow import _payload,_terminal_evidence,_worker_success_stdout
rdevs={'/dev/sdb':201,'/dev/nvme0n1':202,'/dev/sdc':301,'/dev/sdc1':302}
success=refused=0
with tempfile.TemporaryDirectory(prefix='beamo-pass7-controller-') as directory:
    evidence=_terminal_evidence(Path(directory))
    with patch.object(export,'_block_rdev',side_effect=lambda path:rdevs[path]), patch.object(export,'_emit_export_marker'), patch.object(export,'_emit_export_failure'):
        for index in range(3):
            for field in ('model','serial','wwn'):
                for padding in (' ','   ','\u00a0'):
                    first,_=_payload();first['blockdevices'][index][field]=padding+first['blockdevices'][index][field]+padding
                    disks=tuple(node_to_disk(node,is_boot=i==0) for i,node in enumerate(first['blockdevices'][:2]))
                    discovery=DiscoveryResult(disks=disks,boot=disks[0],boot_identified=True)
                    second=copy.deepcopy(first);second['blockdevices'][index][field]=' '+second['blockdevices'][index][field].strip()+' '
                    for changed in (False,True):
                        scan2=copy.deepcopy(second)
                        if changed:scan2['blockdevices'][index][field]=' changed '
                        scans=iter((first,scan2));calls=[]
                        def run(command,**kwargs):
                            calls.append(command)
                            request=json.loads(kwargs['input'])
                            decoded=export._decode_worker_request(kwargs['input'].encode())
                            assert decoded[1].parent.serial=='REPORT-1'
                            return subprocess.CompletedProcess(command,0,stdout=_worker_success_stdout(request),stderr='')
                        try:
                            receipt=export.export_to_new_usb(evidence_path=evidence,discovery=discovery,target_path='/dev/nvme0n1',scan=lambda:next(scans),run=run)
                            assert not changed and receipt.ok and receipt.safe_to_remove and len(calls)==1
                            success+=1
                        except SafetyError:
                            assert changed and not calls
                            refused+=1
assert (success,refused)==(27,27)
print('PASS27 padded hardware two-scan controller/request/helper-receipt roundtrips;27 second-scan hardware replacements refused before helper. All block/process/marker boundaries fake; regular-file evidence only.')
