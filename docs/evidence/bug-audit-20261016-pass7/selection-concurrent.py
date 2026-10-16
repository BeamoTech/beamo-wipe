import concurrent.futures
import copy
import json
import os
from pathlib import Path
from beamo_wipe.discover import discover, load_lsblk_json_text
from beamo_wipe.safety import assert_boot_excluded, selectable_disks
os.environ['BEAMO_WIPE_DRY_RUN']='1'
payload=load_lsblk_json_text(Path('tests/fixtures/lsblk_same_size.json').read_text())
def check(index):
    fixture=copy.deepcopy(payload)
    mode=index%4
    source=['/dev/sdb']
    if mode==1: source=['/dev/missing']
    if mode==2: fixture['blockdevices']='invalid'
    if mode==3: source=['/dev/sdb','/dev/nvme0n1']
    r=discover(lsblk_payload=fixture,mount_sources=source,cmdline='boot=live')
    if mode==0:
        assert r.boot_identified and r.boot.path=='/dev/sdb' and selectable_disks(r)
        assert_boot_excluded(r)
    else: assert not r.boot_identified and not selectable_disks(r)
    return mode
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    modes=list(pool.map(check,range(160)))
assert all(modes.count(m)==40 for m in range(4))
print(json.dumps({'result':'PASS','concurrent_discoveries':160,'workers':8,'healthy':40,'unresolved_source':40,'malformed_topology':40,'conflicting_sources':40,'fake_only':True},indent=2))
