"""Fresh same-language evidence -> sharing -> real bundle semantic matrix.

All inventory, build identity and OS process boundaries are fake. No file export,
mount, native device or engine operation occurs. This is supporting model coverage.
"""
from dataclasses import replace
from pathlib import Path
import hashlib,itertools,json,sys

sys.path.insert(0,'/workspace/beamo-wipe/src')
from pytest import MonkeyPatch
from beamo_wipe import evidence as E,lang
from beamo_wipe.demo import discovery_for_scenario
from beamo_wipe.models import MethodId,WipeResult
from beamo_wipe.nwipe_runner import completion_for_method
from beamo_wipe import nwipe_runner
from beamo_wipe.outcomes import present_evidence
from beamo_wipe.privacy import make_sharing_copy
from beamo_wipe.support_export import _bundle_files

root=Path(__file__).parent;effects=[];failures=[];cases=0;successes=0;bundles=0
status='********************************* Drive Status *********************************\n'
logs=[
 '', status+'sda | Erased | 120MB/s | 01:25:04 | QEMU/DISK\n',
 status+'sdb | Erased | 120MB/s | 01:25:04 | QEMU/DISK\n',
 '/dev/sda is reported as IN USE\n',"Unable to open device '/dev/sda'.\n",
 "No sane device geometry for '/dev/sda'.\n",
 "Verification mismatch on '/dev/sda' at offset 4096\n",'/dev/sda: >>> FAILURE! <<<\n',
 '[2026/09/07 12:00:00] info: nwipe: /dev/sda: pass 1/1 (write) 100%\n',
 status+'sda | Erased | 120MB/s | 01:25:04 | QEMU/DISK\n/dev/sda: >>> FAILURE! <<<\n',
]
identifiers=['FAKE-MATRIX-ID','verified','last','completed','en','withheld']
original_language=lang.current()
with MonkeyPatch.context()as patch:
 patch.setenv('BEAMO_WIPE_DRY_RUN','1');patch.delenv('BEAMO_WIPE_LIVE',raising=False)
 def forbidden(*args,**kwargs):effects.append(True);raise AssertionError('Native boundary forbidden')
 for n in ('subprocess.run','subprocess.Popen','beamo_wipe.discover.run_lsblk','beamo_wipe.discover.read_cmdline','beamo_wipe.discover.read_mount_sources','beamo_wipe.nwipe_runner.NwipeRunner.start','beamo_wipe.app._shutdown'):
  patch.setattr(n,forbidden)
 patch.setattr(E.os.path,'realpath',lambda p:str(p))
 patch.setattr(E,'evidence_identity',lambda:{'source_commit':'','build_id':'','build_status':'unavailable','source_dirty':None})
 for language in ('en','fr','de'):
  lang.set_language(language)
  for method,exit_code,result_ok,flags,log,identifier in itertools.product(MethodId,(0,1,2,-2,None),(False,True),((False,False),(True,False),(True,True)),logs,identifiers):
   cases+=1;interrupted,cancelled=flags
   discovery=discovery_for_scenario('happy');disk=replace(discovery.selectable[0],serial=identifier)
   discovery=replace(discovery,disks=tuple(disk if d.path==disk.path else d for d in discovery.disks))
   okay,detail,reason=completion_for_method(exit_code,log,disk.path,method)
   result=WipeResult(result_ok,exit_code,detail,'/tmp/FAKE-nwipe.log',reason)
   e=E.build_evidence(disk=disk,discovery=discovery,method=method,request=None,result=result,
      started_at_wall='',ended_at_wall='',started_mono=0,ended_mono=1,argv=[],log_text=log,
      interrupted=interrupted,cancelled=cancelled,language=language)
   view=present_evidence(e)
   if view.success:
    successes+=1
    assert okay and result_ok and exit_code==0 and not interrupted and not cancelled
    assert view.code==('unverified'if method==MethodId.QUICK_ZERO else'verified')
   shared=make_sharing_copy(e);copy_view=present_evidence(shared)
   if (copy_view.code,copy_view.success)!=(view.code,view.success):
    failures.append({'language':language,'method':method.value,'exit_code':exit_code,'result_ok':result_ok,
       'flags':flags,'log_index':logs.index(log),'identifier':identifier,'original':view.code,'sharing':copy_view.code})
   # Exercise the actual bundle consumer on a deterministic eighth of cases.
   if cases%8==0:
    bundles+=1;raw=json.dumps(e,sort_keys=True).encode()
    b=_bundle_files(raw,log.encode(),'complete'if log else'unavailable',privacy_reduced=True)
    exported=json.loads(b['SHARE.json']);export_view=present_evidence(exported)
    assert (export_view.code,export_view.success)==(view.code,view.success)
    assert view.message in b['RESULT.txt'].decode()
    assert b['result.json']==raw
lang.set_language(original_language)
result={'cases':cases,'original_successes':successes,'actual_bundles':bundles,'same_language_readers':True,
 'identifier_cases':identifiers,'native_callbacks':len(effects),'semantic_failures':failures,
 'source_sha256':{str(p.relative_to('/workspace/beamo-wipe')):hashlib.sha256(p.read_bytes()).hexdigest()for p in (Path('/workspace/beamo-wipe/src/beamo_wipe')/n for n in ['evidence.py','privacy.py','outcomes.py','result_summary.py','support_export.py'])}}
(root/'semantic-export-matrix.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items()if k!='source_sha256'}))
assert not failures and not effects
