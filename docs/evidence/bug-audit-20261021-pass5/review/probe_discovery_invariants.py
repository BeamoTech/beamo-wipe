"""Compare equivalent fake inventories and independent token-ownership properties."""
import copy
import importlib
import json
from pathlib import Path
import random
import sys

repo = Path('/workspace/beamo-wipe')
out = Path(__file__).resolve().parent
sys.path[:0] = [str(repo/'tests'), str(repo/'src')]
import pytest
fixture = importlib.import_module('test_discovery_observation_fallback_pass16')
from beamo_wipe.safety import SafetyError, confirm_spec, disk_identity, listed_disks, token_matches

equivalence = []
token_stats = {'inventories': 0, 'views': 0, 'confirmable': 0, 'ambiguous_refused': 0}
rng = random.Random(2026102105)
with pytest.MonkeyPatch.context() as patch:
    guard = fixture.fake_machine.__wrapped__(patch)
    scan = next(guard)
    try:
        for route in fixture.ROUTES:
            for kind in ('part', 'crypt', 'lvm', 'unknown'):
                for mounted in (False, True):
                    for label in ('Owner Data', ' Owner Data', 'Owner Data ', 'Données', 'A|B', '[data]', 'EFI', ''):
                        part = {'name':'sda1', 'path':'/dev/sda1', 'type':'part', 'pkname':'sda',
                                'size':120_000_000_000, 'ro':False, 'mountpoints':[],
                                'fstype':'ext4' if kind=='part' else 'crypto_LUKS',
                                'uuid':'PARTITION-UUID', 'label':label}
                        flat_target = fixture._disk('sda')
                        nested_target = copy.deepcopy(flat_target)
                        if kind == 'part':
                            part['mountpoints'] = ['/mnt/fake-data'] if mounted else []
                            flat_rows = [copy.deepcopy(part)]
                            nested_target['children'] = [copy.deepcopy(part)]
                        else:
                            mapper = {'name':'dm-0', 'path':'/dev/dm-0', 'type':kind,
                                      'pkname':'sda1', 'size':119_000_000_000, 'ro':False,
                                      'mountpoints':['/mnt/fake-data'] if mounted else [],
                                      'fstype':'ext4', 'uuid':'OPENED-UUID', 'label':label}
                            flat_rows = [copy.deepcopy(part), copy.deepcopy(mapper)]
                            nested_part = copy.deepcopy(part)
                            nested_part['children'] = [copy.deepcopy(mapper)]
                            nested_target['children'] = [nested_part]
                        flat = {'blockdevices':[fixture._boot(), flat_target, *flat_rows]}
                        nested = {'blockdevices':[fixture._boot(), nested_target]}
                        results = []
                        for payload in (flat, nested):
                            try:
                                result = scan(payload, route)
                            except ValueError:
                                assert route == 'direct'
                                results.append(('refused',))
                                continue
                            if result.error:
                                assert not result.selectable and not result.boot_identified
                                results.append(('refused',))
                            else:
                                results.append((tuple(sorted((disk_identity(d),d.contents,d.mountpoints) for d in result.disks)),
                                                tuple(sorted(d.path for d in result.selectable))))
                        assert results[0] == results[1], (route,kind,mounted,label,results)
                        if kind == 'lvm' and mounted:
                            assert results[0] == ('refused',)
                        else:
                            assert results[0] != ('refused',)
                            assert results[0][1] == (() if mounted else ('/dev/sda',))
                        equivalence.append({'route':route,'kind':kind,'mounted':mounted,'label':label,'equivalent':True})

        serials = ('', '0000', 'unknown', 'sda', '128', 'ABCD', 'disk-ABCD', 'other-ABCD', 'FULL-XY12', 'XY12')
        for case in range(3000):
            rows = []
            for index in range(rng.randrange(1,7)):
                name = 'sd'+chr(ord('a')+index)
                row = fixture._disk('sda')
                row.update(name=name,path='/dev/'+name,
                           size=rng.choice((500_000_000,1_000_000_000,128_000_000_000,128_500_000_000,512_000_000_000)),
                           serial=rng.choice(serials),
                           wwn=rng.choice(('', '0x0000', '50014ee2'+str(index), 'shared-ABCD')))
                rows.append(row)
            result = scan({'blockdevices':[fixture._boot(),*rows]}, 'injected')
            assert result.boot_identified and not result.error
            peers = listed_disks(result)
            token_stats['inventories'] += 1
            specs = []
            for disk in result.selectable:
                token_stats['views'] += 1
                try:
                    spec = confirm_spec(disk,peers)
                except SafetyError:
                    token_stats['ambiguous_refused'] += 1
                else:
                    token_stats['confirmable'] += 1
                    assert spec.token.casefold() not in {d.name.casefold() for d in peers}
                    assert token_matches(spec.token,spec) and token_matches(spec.token.swapcase(),spec)
                    specs.append((disk.path,spec))
            for path,spec in specs:
                assert all(path==other_path or not token_matches(spec.token,other_spec)
                           for other_path,other_spec in specs), (case,specs)
    finally:
        try:
            next(guard)
        except StopIteration:
            pass
record = {'seed':2026102105,'equivalent_flat_nested_scenarios':len(equivalence),
          'token_ownership':token_stats,'cross_disk_token_collisions':0,
          'native_acquisition_guard':'PASS','equivalence':equivalence}
(out/'discovery-invariants.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='equivalence'},indent=2))
