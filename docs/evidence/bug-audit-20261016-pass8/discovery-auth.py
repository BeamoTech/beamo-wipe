import copy,itertools,json,os,pathlib,sys
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path.cwd()/'src'))
os.environ['BEAMO_WIPE_DRY_RUN']='1'
from beamo_wipe import discover as d,safety as s
from beamo_wipe.models import MethodId
base={'blockdevices':[dict(name='sdz',path='/dev/sdz',type='disk',size=16000000000,serial='BOOT',tran='usb',model='USB',mountpoints=['/run/live/medium']),dict(name='sda',path='/dev/sda',type='disk',size=256000000000,serial='TARGET',tran='sata',model='SSD')]}
r=d.discover(lsblk_payload=base,boot_path='/dev/sdz',mount_sources=['/dev/sdz'],cmdline='boot=live',env={'BEAMO_WIPE_DRY_RUN':'1'})
disk=r.selectable[0]
spec=s.confirm_spec(disk,s.listed_disks(r))
counts={'accepted':0,'refused':0}
with patch.object(s,'logfile_for',return_value='/tmp/beamo-wipe/not-opened.log'),patch.object(s,'assert_not_boot',return_value=None),patch.object(s,'assert_existing_is_block_device',return_value=None),patch.object(s,'block_rdev',return_value=None):
    for owner,countdown,typed,method,selected in itertools.product([True,False,None,1,'true'],[True,False,None,1,'true'],[spec.token,' '+spec.token+' ','wrong',''],list(MethodId),[disk,None,r.boot]):
        expected=owner is True and countdown is True and typed.strip()==spec.token and selected is disk
        try:req=s.assert_ready_to_wipe(owner_ok=owner,disk=selected,discovery=r,typed_token=typed,countdown_complete=countdown,method=method)
        except s.SafetyError:
            assert not expected
            counts['refused']+=1
        else:
            assert expected
            assert req.device=='/dev/sda' and req.boot_device=='/dev/sdz'
            counts['accepted']+=1
print(json.dumps({'cases':sum(counts.values()),'outcomes':counts,'all_physical_and_log_creation_boundaries_stubbed':True},indent=2))
