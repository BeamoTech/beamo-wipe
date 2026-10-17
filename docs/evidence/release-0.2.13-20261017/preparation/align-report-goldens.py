"""Change only release metadata in fake report snapshots; preserve all wording."""
import ast,hashlib,json,os,sys
from pathlib import Path
root=Path.cwd();base=Path('/tmp/beamo-release-20261017')
sys.path[:0]=[str(root/'src'),str(root/'tests')]
from beamo_wipe import __version__,lang,nwipe_runner
assert __version__=='0.2.13'
def forbidden(*a,**k):raise AssertionError('Unexpected native application operation')
nwipe_runner.subprocess.run=nwipe_runner.subprocess.Popen=forbidden
nwipe_runner.pinned_nwipe_already_running=nwipe_runner._recheck_identity_under_lock=forbidden
from test_result_presentations import CASES,case_evidence
from beamo_wipe.support_export import _bundle_files
lang.set_language('en');_,ev,_=case_evidence(CASES[0])
bundle=_bundle_files(json.dumps(ev).encode(),b'','unavailable',privacy_reduced=True)
share=bundle['SHARE.json'];assert share.count(b'0.2.13')==1
old_share=share.replace(b'0.2.13',b'0.2.12');old_digest=hashlib.sha256(old_share).hexdigest();new_digest=hashlib.sha256(share).hexdigest()
goldens=root/'tests/goldens/result_summary';old_header='Application: Beamo Wipe 0.2.12';new_header='Application: Beamo Wipe 0.2.13'
original={};changed={}
for p in sorted(goldens.glob('*.txt')):
 before=p.read_text()
 if old_header not in before:continue
 assert before.count(old_header)==1
 after=before.replace(old_header,new_header)
 if p.name=='share.txt':
  assert 'Report checksum: '+old_digest in before
  after=after.replace('Report checksum: '+old_digest,'Report checksum: '+new_digest)
 assert after.replace(new_header,old_header).replace('Report checksum: '+new_digest,'Report checksum: '+old_digest)==before
 original[str(p.relative_to(root))]=before
 changed[str(p.relative_to(root))]={'before_sha256':hashlib.sha256(before.encode()).hexdigest(),'after_sha256':hashlib.sha256(after.encode()).hexdigest()}
 p.write_text(after)
assert len(changed)==13
(base/'report-goldens-before.json').write_text(json.dumps(original,indent=2)+'\n')
receipt={'changed_files':changed,'change_only':'Application version line in13fake report goldens; share checksum changes only because the same SHARE.json contains the new version. All other bytes unchanged.','old_share_checksum':old_digest,'new_share_checksum':new_digest,'old_version_replacement_recovers_original_share_checksum':True,'native_application_operations':0}
(base/'report-golden-version-review.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='changed_files'},indent=2))
