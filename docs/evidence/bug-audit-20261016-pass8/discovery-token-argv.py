import copy, itertools, json, os, pathlib, random, sys
from dataclasses import replace
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path.cwd()/'src'))
os.environ['BEAMO_WIPE_DRY_RUN']='1'
from beamo_wipe.discover import node_to_disk
from beamo_wipe import safety as s,nwipe_runner as nr
from beamo_wipe.models import MethodId,WipeRequest
rng=random.Random(381871)
count=0;confirmed=0;rejected=0
ids=['ABCD','XABCD','xabcd','0000','UNKNOWN','sda','sdb','sdz','256','1024','a','serial:3','0x1234','.', '..','é123','WW1234','ww1234','1234']
for _ in range(5000):
    disks=[]
    for name in ['sda','sdb','sdc','sdd'][:rng.randrange(2,5)]:
        disk=node_to_disk(dict(name=name,path='/dev/'+name,type='disk',size=rng.choice([255999999999,256000000000,1024000000000]),serial=rng.choice(ids),wwn=rng.choice(ids),tran='sata'),False)
        disks.append(disk)
    specs=[]
    for disk in disks:
        try:spec=s.confirm_spec(disk,disks)
        except s.SafetyError:rejected+=1;continue
        confirmed+=1
        assert s.token_matches(spec.token,spec)
        assert not s.token_matches('',spec)
        assert spec.token.casefold() not in [x.name.casefold() for x in disks]
        specs.append((disk,spec))
    assert len({x.token.casefold() for _,x in specs})==len(specs)
    count+=1
# Pure argv boundary: replace all physical/log probes, preserve constructor and validator.
argv_count=0
with patch.object(nr,'assert_not_boot',side_effect=lambda target,boot,**k: (_ for _ in ()).throw(s.SafetyError('boot')) if target==boot else None),patch.object(nr,'assert_log_not_on_target',return_value=None),patch.object(nr,'assert_existing_is_block_device',return_value=None):
    for method in MethodId:
        request=WipeRequest('/dev/sda',method,'/dev/sdz','/tmp/beamo-wipe/fake.log')
        good=nr.build_nwipe_argv(request)
        assert good[-1]=='/dev/sda' and good.count('--exclude=/dev/sdz')==1
        assert sum(x.startswith('/dev/') for x in good)==1
        assert '--force' not in good
        argv_count+=1
        mutations=[]
        for i in range(1,len(good)-1):
            mutations.append(good[:i]+good[i+1:])
            mutations.append(good[:i]+[good[i]]+good[i:])
        for x in ['--force','--force=1','/dev/sdb','--','--autonuke\n','--method=zero','--verify=off','--exclude=/dev/sda','--exclude=/dev/sdb','--unknown','--logfile=/dev/sda']:
            mutations.append(good[:-1]+[x]+good[-1:])
        for changed in mutations:
            try:nr.validate_argv(changed,request)
            except s.SafetyError:pass
            else:raise AssertionError(('accepted malformed argv',changed))
            argv_count+=1
print(json.dumps({'seed':381871,'token_inventories':count,'token_specs_accepted':confirmed,'ambiguous_specs_refused':rejected,'argv_cases':argv_count},indent=2))
