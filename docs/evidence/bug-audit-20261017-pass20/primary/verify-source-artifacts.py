"""Read back exact starting/final bytes and canonical regression proof lineage."""
import collections,difflib,gzip,hashlib,json,subprocess,tarfile,xml.etree.ElementTree as E
from pathlib import Path
root=Path.cwd();out=Path('/tmp/pass20-primary');sha=lambda b:hashlib.sha256(b).hexdigest()
start=json.loads((out/'starting-freeze.json').read_text());freeze=json.loads((out/'source-freeze.json').read_text())
assert len(start)==771 and len(freeze)==779
assert start==json.loads((root/'docs/evidence/bug-audit-20261017-pass19/primary/source-freeze.json').read_text())
with tarfile.open(out/'starting-inputs.tar.gz','r:gz')as a:
 assert len(a.getnames())==len(start) and set(a.getnames())==set(start)
 before={m.name:a.extractfile(m).read() for m in a if m.isfile()}
assert {n:sha(b) for n,b in before.items()}==start
with tarfile.open(out/'final-source-inputs.tar.gz','r:gz')as a:
 assert len(a.getnames())==len(freeze) and set(a.getnames())==set(freeze)
 assert all(m.isfile() and sha(a.extractfile(m).read())==freeze[m.name]==sha((root/m.name).read_bytes()) for m in a)
changed=sorted(n for n in start if start[n]!=freeze[n]);added=sorted(set(freeze)-set(start))
assert changed==['src/beamo_wipe/audio_jobs.py','src/beamo_wipe/discover.py','src/beamo_wipe/ui/tk_wizard.py']
assert len(added)==8 and all(n.startswith('tests/') and n.endswith('_pass20.py') for n in added)
patch=''.join(line for n in changed for line in difflib.unified_diff(before[n].decode().splitlines(True),(root/n).read_text().splitlines(True),fromfile='starting/'+n,tofile='final/'+n))
assert patch==(out/'pass20-source.diff').read_text()
for group,path in [('source','src'),('tracked-tests','tests')]:assert gzip.decompress((out/(group+'.diff.gz')).read_bytes())==subprocess.check_output(['git','diff','--',path])
new=json.loads((out/'new-tests-sha256.json').read_text());assert len(new)==50
with tarfile.open(out/'new-tests.tar.gz','r:gz')as a:
 assert len(a.getnames())==len(new) and set(a.getnames())==set(new)
 assert all(m.isfile() and sha(a.extractfile(m).read())==new[m.name]==freeze[m.name] for m in a)
proof=E.parse(out/'final149-canonical-original.xml').getroot();cases=list(proof.iter('testcase'))
assert len(cases)==len({(c.get('classname'),c.get('name'))for c in cases})==149
assert sum(c.find('failure')is not None for c in cases)==88
assert not any(c.find('error')is not None or c.find('skipped')is not None for c in cases)
original=out/'original-replay'
assert all(sha((original/n).read_bytes())==start[n] for n in start if n.startswith('src/'))
assert sum(n.startswith('src/')for n in start)==58
modules=collections.Counter('tests/'+c.get('classname').split('.')[-1]+'.py'for c in cases)
assert set(modules)==set(added)
assert not subprocess.check_output(['git','diff','--cached','--name-only'])
subprocess.run(['git','diff','--check'],check=True)
guidance={n:sha((root/n).read_bytes()) for n in ['AGENTS.md','docs/ci.md','docs/remote-development.md','docs/claims.md','README.md','docs/runbook.md','.ai/memory/product-constraints.md'] if(root/n).is_file()}
receipt=dict(starting_inputs=771,starting_matches_prior_final=True,final_inputs=779,unchanged_starting_inputs=768,changed_inputs=changed,new_test_inputs=8,retained_regression_modules=50,source_and_test_archives_readback=True,exact_incremental_and_cumulative_patches=True,original_final_proof_cases=149,original_failures=88,original_passing_controls=61,original_errors=0,original_skips=0,original_source_files_authenticated=58,canonical_modules=dict(modules),index_empty=True,guidance_sha256=guidance,shared_parent_guide_present=Path('/root/dev/AGENTS.md').exists())
(out/'source-artifact-verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
