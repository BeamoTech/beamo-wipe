from __future__ import annotations
from dataclasses import replace
import json
import os
from pathlib import Path
import random
import sys

ROOT=Path('/workspace/beamo-wipe')
OUT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
import pytest
from beamo_wipe.models import Disk,DiskKind
from beamo_wipe.safety import SafetyError,confirm_spec,token_matches
rng=random.Random(20261019)
values=('','UNKNOWN','00000000','NONE','SERIAL-1000','SERIAL-ABCD','OTHER-ABCD','1000','2000','sda','sdb','ID-0x500','0x5000c500aabbccdd','5000c500aabbccdd','abcde','ABCDE')
counts={'inventories':500,'disk_views':0,'confirmable':0,'ambiguous':0,'cross_disk_token_collisions':0}
realpath=os.path.realpath
with pytest.MonkeyPatch.context() as patch:
    patch.setattr(os.path,'realpath',lambda path,*a,**kw:os.fspath(path) if os.fspath(path).startswith('/dev/') else realpath(path,*a,**kw))
    for _ in range(500):
        disks=[]
        for index in range(rng.randint(2,5)):
            size=rng.choice((128,256,1000,2000))
            disks.append(Disk(path='/dev/sd'+chr(97+index),name='sd'+chr(97+index),model='Fake',serial=rng.choice(values),wwn=rng.choice(values),size_bytes=size*1_000_000_000,size_gb_label=str(size),kind=DiskKind.SSD,bus='SATA',label=''))
        tokens={}
        for disk in disks:
            counts['disk_views']+=1
            try:spec=confirm_spec(disk,disks)
            except SafetyError:counts['ambiguous']+=1;continue
            assert token_matches(spec.token,spec)
            assert token_matches(spec.token.swapcase(),spec)
            key=spec.token.casefold()
            assert key not in tokens,(disks,tokens,disk.path,spec)
            tokens[key]=disk.path
            counts['confirmable']+=1
(OUT/'token-matrix.json').write_text(json.dumps(counts,indent=2)+'\n')
print(json.dumps(counts,indent=2))
