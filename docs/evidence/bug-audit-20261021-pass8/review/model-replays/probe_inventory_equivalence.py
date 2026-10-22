"""Seeded physical eligibility and tree/flat/order equivalence on fake inventory."""
from pathlib import Path
import copy
import hashlib
import json
import random
import sys
import tempfile

sys.path.insert(0, '/workspace/beamo-wipe/src')
from pytest import MonkeyPatch
import beamo_wipe.app as app
import beamo_wipe.nwipe_runner as runner
from beamo_wipe import discover as D
from beamo_wipe import safety as S

root=Path(__file__).parent
stats={'contexts':0,'discovery_calls':0,'representation_permutation_checks':0,'layout_mutations_checked':0}
effects=[]

def disk(name, *, ro=False, usb=False):
    return {'name':name,'path':'/dev/'+name,'type':'disk','size':128_000_000_000 if name=='sda' else 256_000_000_000,
            'tran':'usb' if usb else 'sata','ro':ro,'rota':False,'rm':usb,'hotplug':usb,
            'serial':'FAKE-'+name,'model':'Fake model '+name,'wwn':'fake-'+name+'-wwn','mountpoints':[]}

def scan(rows):
    stats['discovery_calls']+=1
    result=D.discover(lsblk_payload={'blockdevices':rows},boot_path='/dev/sdz',mount_sources=[],cmdline='',env={'BEAMO_WIPE_DRY_RUN':'1'})
    assert result.boot_identified and result.boot is not None and result.boot.path=='/dev/sdz',result
    assert not result.error
    assert all(d.path!='/dev/sdz' for d in result.selectable)
    return result

def snapshot(result):
    return ({d.path:S.disk_identity(d) for d in result.disks},
            {d.path:d.contents for d in result.disks},
            set(d.path for d in result.selectable))

with MonkeyPatch.context()as patch, tempfile.TemporaryDirectory(prefix='beamo-pass8-inventory-model-')as directory:
    patch.setenv('BEAMO_WIPE_DRY_RUN','1');patch.delenv('BEAMO_WIPE_LIVE',raising=False)
    def forbidden(*_args,**_kwargs):effects.append(True);raise AssertionError('Native callback forbidden')
    for name in ('subprocess.run','subprocess.Popen','beamo_wipe.discover.run_lsblk','beamo_wipe.discover._run_findmnt','beamo_wipe.discover.read_cmdline','beamo_wipe.discover.read_mount_sources'):
        patch.setattr(name,forbidden)
    patch.setattr(app,'_shutdown',forbidden);patch.setattr(runner.NwipeRunner,'start',forbidden)
    patch.setattr('beamo_wipe.diagnostics.log_diag',lambda *_args,**_kwargs:None)
    patch.setattr(S,'default_log_dir',lambda:Path(directory))
    realpath=D.os.path.realpath
    patch.setattr(D.os.path,'realpath',lambda path,*a,**kw:str(path)if str(path).startswith('/dev/')else realpath(path,*a,**kw))
    for seed in range(256):
        stats['contexts']+=1;rng=random.Random(7082026+seed)
        roots=[disk('sdz',usb=True),disk('sda',ro=rng.choice((False,True))),disk('sdb',ro=rng.choice((False,True)))]
        roots[0]['mountpoints']=['/run/live/medium']
        parts=[];expected=set()
        for parent in roots[1:]:
            mounted=False
            for number in range(1,rng.randrange(3)+1):
                mp=['/data/'+parent['name']]if number==1 and rng.choice((False,True))else[]
                mounted=mounted or bool(mp)
                parts.append({'name':parent['name']+str(number),'path':'/dev/'+parent['name']+str(number),'type':'part',
                              'pkname':parent['name'],'size':50_000_000_000+number*512,'ro':False,'mountpoints':mp,
                              'fstype':rng.choice(('ext4','ntfs','vfat')),'uuid':'FAKE-'+parent['name']+'-PART'+str(number),
                              'partuuid':'FAKE-'+parent['name']+'-GUID'+str(number),'partlabel':'Windows Recovery'if rng.randrange(4)==0 else 'Data'})
            if not parent['ro'] and not mounted:expected.add(parent['path'])
        canonical=None
        for shape in ('tree','flat'):
            rows=copy.deepcopy(roots)
            if shape=='tree':
                for parent in rows:
                    children=[copy.deepcopy(p)for p in parts if p['pkname']==parent['name']]
                    if children:parent['children']=children
            else:rows+=copy.deepcopy(parts)
            for perm in range(6):
                shuffled=copy.deepcopy(rows);rng.shuffle(shuffled)
                for parent in shuffled:
                    if parent.get('children'):rng.shuffle(parent['children'])
                result=scan(shuffled);got=snapshot(result)
                assert got[2]==expected,(seed,shape,perm,expected,got[2])
                if canonical is None:canonical=got
                else:assert got==canonical,(seed,shape,perm,got,canonical)
                stats['representation_permutation_checks']+=1
            if parts:
                mutated=copy.deepcopy(rows)
                changed=False
                for parent in mutated:
                    candidates=[parent,*parent.get('children',[])]
                    for candidate in candidates:
                        if candidate.get('type')=='part'and not changed:
                            owner=candidate['pkname'];candidate['uuid']+='-CHANGED';changed=True
                result=scan(mutated)
                by_path={d.path:d for d in result.disks}
                assert S.disk_identity(by_path['/dev/'+owner])!=canonical[0]['/dev/'+owner]
                assert by_path['/dev/'+owner].layout_id
                stats['layout_mutations_checked']+=1
assert not effects
source={n:hashlib.sha256((Path('/workspace/beamo-wipe')/n).read_bytes()).hexdigest()for n in ('src/beamo_wipe/discover.py','src/beamo_wipe/safety.py','src/beamo_wipe/models.py')}
result={'seed_base':7082026,'counts':stats,'native_callbacks':len(effects),'failures':[],'source_sha256':source,'scope':'Fake physical eligibility/order/tree-flat/layout-change model; no native hardware acceptance'}
(root/'inventory-equivalence.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
