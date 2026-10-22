"""Fresh seeded fake-only graph and ancestry observations, not native acceptance."""
from pathlib import Path
import builtins
import copy
import hashlib
import io
import json
import os
import random
import sys
import tempfile

sys.path.insert(0, '/workspace/beamo-wipe/src')
from pytest import MonkeyPatch
from beamo_wipe import discover as D, safety as S
import beamo_wipe.app as A
import beamo_wipe.nwipe_runner as R

ROOT=Path(__file__).parent
COUNTS={'contexts':0,'discovery_calls':0,'order_representation_checks':0,
        'protected_target_observations':0,'positive_selectable_observations':0,
        'ambiguous_boot_refusals':0,'duplicate_identity_refusals':0}
effects=[]

def key(value):
    value=value.strip().casefold()
    if value.startswith('0x'):value=value[2:]
    return '' if not value or set(value)<={'0'} else value

def expected_closure(anchor, rows):
    # Independently compute the ID relation to a fixed protected anchor.
    protected={anchor}; changed=True;fixed=key(rows[anchor]['wwn'])
    while changed:
        changed=False
        for i,candidate in enumerate(rows):
            if i in protected:continue
            cw=key(candidate['wwn'])
            if fixed and cw and fixed!=cw:continue
            for j in tuple(protected):
                source=rows[j];sw=key(source['wwn'])
                linked=(sw==cw) if sw and cw else bool(key(source['serial']) and key(source['serial'])==key(candidate['serial']))
                if linked:protected.add(i);changed=True;break
    return protected

def fake_disk(name,serial,wwn):
    return dict(name=name,path='/dev/'+name,type='disk',size=256_000_000_000,
                tran='sata',rota=False,ro=False,serial=serial,wwn=wwn,
                model='Fake '+name,vendor='Fake vendor',mountpoints=[])

def scan(rows,sources):
    COUNTS['discovery_calls']+=1
    return D.discover(lsblk_payload={'blockdevices':copy.deepcopy(rows)},mount_sources=sources,
                      cmdline='',env={'BEAMO_WIPE_DRY_RUN':'1'})

with MonkeyPatch.context() as patch, tempfile.TemporaryDirectory(prefix='beamo-pass9-graph-') as folder:
    patch.setenv('BEAMO_WIPE_DRY_RUN','1');patch.delenv('BEAMO_WIPE_LIVE',raising=False)
    def forbidden(*args,**kwargs):effects.append('native');raise AssertionError('native acquisition/action forbidden')
    for name in ('subprocess.run','subprocess.Popen','beamo_wipe.discover.run_lsblk',
                 'beamo_wipe.discover._run_findmnt','beamo_wipe.discover.read_cmdline',
                 'beamo_wipe.discover.read_mount_sources'):
        patch.setattr(name,forbidden)
    patch.setattr(A,'_shutdown',forbidden);patch.setattr(R.NwipeRunner,'start',forbidden)
    patch.setattr('beamo_wipe.diagnostics.log_diag',lambda *a,**kw:None)
    patch.setattr('beamo_wipe.diagnostics.emit_serial_marker',lambda *a,**kw:None)
    patch.setattr(S,'default_log_dir',lambda:Path(folder))
    realpath=os.path.realpath
    patch.setattr(os.path,'realpath',lambda path,*a,**kw:os.fspath(path) if os.fspath(path).startswith(('/dev/','/sys/')) else realpath(path,*a,**kw))
    def guarded(fn):
        def wrapped(path,*a,**kw):
            if not isinstance(path,int):
                p=os.fsdecode(path)
                if p in {'/dev','/proc','/sys'} or p.startswith(('/dev/','/proc/','/sys/')):
                    effects.append(p);raise AssertionError('native path forbidden: '+p)
            return fn(path,*a,**kw)
        return wrapped
    for obj,name in ((builtins,'open'),(io,'open'),(os,'open'),(os,'lstat')):
        patch.setattr(obj,name,guarded(getattr(obj,name)))
    for seed in range(512):
        COUNTS['contexts']+=1;rng=random.Random(9082026+seed)
        rows=[fake_disk(name,rng.choice(('', '0000','FAKE-A','FAKE-B','FAKE-C')),
                        rng.choice(('', '0x0000','0x500001','500002','500003')))
              for name in ('sdz','sda','sdb','sdc','sdd')]
        rows[0].update(tran='usb',size=16_000_000_000,mountpoints=['/run/live/medium'])
        mounted=rng.choice((None,1,2));hidden=rng.choice((None,3,4))
        if hidden is not None:
            rows[hidden].update(name='sr'+str(hidden),path='/dev/sr'+str(hidden),type='rom',ro=True)
        for i in range(1,5):rows[i]['ro']=bool(rows[i]['ro'] or rng.randrange(5)==0)
        protected=expected_closure(0,rows)
        if mounted is not None:protected|=expected_closure(mounted,rows)
        expected={row['path'] for i,row in enumerate(rows) if i not in protected and not row['ro'] and row['type']=='disk'}
        expected_boot={rows[i]['path'] for i in expected_closure(0,rows)}
        baseline=None
        for shape in ('tree','flat'):
            inventory=copy.deepcopy(rows)
            if mounted is not None:
                parent=inventory[mounted]
                child=dict(name=parent['name']+'1',path=parent['path']+'1',type='part',
                           pkname=parent['name'],size=128_000_000_000,
                           mountpoints=['/media/fake-data'],fstype='ext4',uuid='FAKE-FS-'+str(seed))
                if shape=='tree':parent['children']=[child]
                else:inventory.append(child)
            for order in range(4):
                shuffled=copy.deepcopy(inventory);rng.shuffle(shuffled)
                result=scan(shuffled,['/dev/sdz'])
                assert result.boot_identified and result.boot.path=='/dev/sdz' and not result.error,(seed,result)
                actual={d.path for d in result.selectable}
                assert actual==expected,(seed,shape,order,expected,actual)
                assert all(d.is_boot for d in result.disks if d.path in expected_boot)
                S.assert_boot_excluded(result)
                snapshot=({d.path:S.disk_identity(d) for d in result.disks},actual)
                if baseline is None:baseline=snapshot
                else:assert snapshot==baseline,(seed,shape,order)
                COUNTS['order_representation_checks']+=1
                COUNTS['positive_selectable_observations']+=len(actual)
                COUNTS['protected_target_observations']+=sum(row['path'] not in actual for row in rows)
        # A second contradictory live source must retire all targets, even if
        # that path aliases the boot hardware through serial/WWN metadata.
        refused=scan(rows,['/dev/sdz','/dev/sda'])
        assert not refused.boot_identified and not refused.selectable
        COUNTS['ambiguous_boot_refusals']+=1
        # A same-path physical contradiction cannot disappear under display
        # filtering or row order; untouched controls above remain selectable.
        duplicated=copy.deepcopy(rows)
        conflict=copy.deepcopy(rows[1]);conflict['size']+=512;duplicated.append(conflict)
        refused=scan(duplicated,['/dev/sdz'])
        assert refused.error and not refused.selectable
        COUNTS['duplicate_identity_refusals']+=1
assert COUNTS['positive_selectable_observations']>500
assert not effects
source={n:hashlib.sha256((Path('/workspace/beamo-wipe')/n).read_bytes()).hexdigest() for n in ('src/beamo_wipe/discover.py','src/beamo_wipe/safety.py','src/beamo_wipe/models.py')}
report={'seed_base':9082026,'counts':COUNTS,'native_callbacks':len(effects),'failures':[],
        'source_sha256':source,'scope':'Fresh fake protected graph/order/tree-flat/contradiction checks; no native acceptance'}
(ROOT/'protected-graph-matrix.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
