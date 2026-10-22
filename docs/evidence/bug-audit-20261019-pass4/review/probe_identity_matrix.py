from __future__ import annotations
import copy
import importlib
import json
from pathlib import Path
import sys

ROOT=Path('/workspace/beamo-wipe')
OUT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'src'),str(ROOT)]
import pytest
fixtures=importlib.import_module('test_discovery_observation_fallback_pass16')
from beamo_wipe.models import MethodId,WipeRequest
from beamo_wipe.safety import SafetyError,assert_disk_identity,assert_rediscovered_identity,disk_identity,listed_disks

fields=('unchanged','serial','wwn','model','vendor','size','tran','rota','uuid','path')
results=[]
with pytest.MonkeyPatch.context() as patch:
    guard=fixtures.fake_machine.__wrapped__(patch)
    scan=next(guard)
    try:
        for route in fixtures.ROUTES:
            for subject in ('target','boot'):
                for field in fields:
                    boot=fixtures._disk('sdz',tran='usb',size=16_000_000_000,mountpoints=['/run/live/medium'])
                    target=fixtures._disk('sda')
                    changed=target if subject=='target' else boot
                    part_name=changed['name']+'1'
                    changed['children']=[{'name':part_name,'path':'/dev/'+part_name,'type':'part','pkname':changed['name'],'size':8_000_000_000,'fstype':'ntfs','uuid':'ORIGINAL-UUID','ro':False,'mountpoints':[]}]
                    before_payload={'blockdevices':[boot,target]}
                    after_payload=copy.deepcopy(before_payload)
                    after_changed=after_payload['blockdevices'][1 if subject=='target' else 0]
                    if field=='uuid':after_changed['children'][0]['uuid']='CHANGED-UUID'
                    elif field=='path':
                        after_changed['name']='sdc';after_changed['path']='/dev/sdc'
                        after_changed['children'][0].update(name='sdc1',path='/dev/sdc1',pkname='sdc')
                    elif field!='unchanged':
                        after_changed[field]={'serial':'CHANGED-SERIAL','wwn':'5000ffffffffffff','model':'Changed model','vendor':'Changed vendor','size':changed['size']+512,'tran':'sas','rota':True}[field]
                    before=scan(before_payload,route)
                    after=scan(after_payload,route,boot='/dev/sdc' if field=='path' and subject=='boot' else '/dev/sdz')
                    assert len(before.selectable)==1 and before.boot_identified
                    request=WipeRequest(device=before.selectable[0].path,method=MethodId.EVERYDAY,boot_device=before.boot.path,logfile='/tmp/beamo-wipe/fake.log',device_identity=disk_identity(before.selectable[0]),boot_identity=disk_identity(before.boot),inventory_identity=tuple(sorted(disk_identity(item) for item in listed_disks(before))))
                    try:assert_rediscovered_identity(request,after)
                    except SafetyError:accepted=False
                    else:accepted=True
                    assert accepted==(field=='unchanged'),(route,subject,field,accepted)
                    if subject=='target':
                        try:assert_disk_identity(before.selectable[0],after)
                        except SafetyError:direct=False
                        else:direct=True
                        assert direct==accepted
                    results.append({'route':route,'subject':subject,'field':field,'accepted':accepted})
    finally:
        try:next(guard)
        except StopIteration:pass
summary={'cases':len(results),'unchanged_accepted':sum(row['accepted'] for row in results),'mutations_rejected':sum(not row['accepted'] for row in results),'native_acquisition_guard':'passed','results':results}
(OUT/'identity-matrix.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({key:value for key,value in summary.items() if key!='results'},indent=2))
