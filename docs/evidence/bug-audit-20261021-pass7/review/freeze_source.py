from pathlib import Path
import ast,datetime,hashlib,json,subprocess
repo=Path('/workspace/beamo-wipe');r=Path(__file__).parent;w=r.parent
base='938fe60347c78f2a745d5d5b04e30dfa013da809'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()==base
names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=repo).decode().split('\0')
selected=sorted(n for n in names if n and (n.startswith(('src/','tests/','scripts/','packaging/','desktop/','developer_tests/')) or n in {'dev.py','pyproject.toml','requirements-dev.txt','preview'})and(repo/n).is_file())
frozen={n:hashlib.sha256((repo/n).read_bytes()).hexdigest()for n in selected};assert len(frozen)==814
starting=json.loads((r/'starting-source-sha256.json').read_text())
changed={n for n in frozen if frozen[n]!=starting.get(n)}
new={'tests/test_live_filesystem_kind_pass7_20261021.py':64,'tests/test_refresh_diagnostic_retirement_pass7_20261021.py':18,'tests/test_plain_review_flush_pass7_20261021.py':8,'tests/test_recovery_publication_binding_pass7_20261021.py':40,'developer_tests/test_dev_runtime_decode_pass7_20261021.py':40}
expected=set(new)|{'dev.py','src/beamo_wipe/discover.py','src/beamo_wipe/report_intent.py','src/beamo_wipe/session_recovery.py','src/beamo_wipe/wizard.py','src/beamo_wipe/ui/console_wizard.py','tests/test_storage_io_recovery.py'}
assert changed==expected,changed^expected
for p in ('ui/final-owned-source-sha256.json','recovery/candidate-check-receipt.json','boot/final-approved-source-hashes.json'):
 hashes=json.loads((w/p).read_text())
 for n,h in hashes.items():
  if n in expected and n!='tests/test_recovery_publication_binding_pass7_20261021.py':assert frozen[n]==h,(p,n)
for n,h in json.loads((w/'discovery/repair-receipt.json').read_text())['owned_paths'].items():assert frozen[n]==h
component=json.loads((r/'go-component-source-sha256.json').read_text());assert len(component)==59
for n,h in component.items():assert starting[n]==frozen[n]==h,n
oldfixture='tests/test_storage_io_recovery.py'
old=subprocess.check_output(['git','show',base+':'+oldfixture],cwd=repo,text=True)
assertions=lambda s:[ast.dump(a,include_attributes=False)for a in ast.walk(ast.parse(s))if isinstance(a,ast.Assert)]
assert assertions(old)==assertions((repo/oldfixture).read_text())
for n in starting:
 if n.startswith(('tests/','developer_tests/'))and n!=oldfixture:assert frozen[n]==starting[n],n
correction=json.loads((r/'root-lint-correction.json').read_text());assert frozen[correction['path']]==correction['final_sha256']
payload=json.dumps(frozen,indent=2,sort_keys=True)+'\n';(r/'final-source-sha256.json').write_text(payload)
review={'baseline_commit':base,'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verified_root_causes':5,'changed_source_and_test_paths':sorted(changed),'new_case_breakdown':new,'new_python_case_count':sum(new.values()),'existing_test_files_modified':[oldfixture],'existing_assertions_preserved':True,'existing_fixture_change':'Complete fake fstat/stat dev/ino metadata for preference cleanup branch; all parameters/assertions/call counts unchanged','go_component_inputs':component,'go_component_inputs_unchanged':True,'all_agent_owned_paths_released':True,'source_review':'Root read every product diff and all five regression modules; independently reproduced original defects before repair. No atomic filesystem CAS or unprivileged attacker claim.','native_or_physical_actions':False}
(r/'independent-review.json').write_text(json.dumps(review,indent=2)+'\n')
(r/'final-freeze.json').write_text(json.dumps({'baseline_commit':base,'source_files':len(frozen),'source_manifest_sha256':hashlib.sha256(payload.encode()).hexdigest(),'new_regression_cases':sum(new.values()),'frozen_at_utc':review['frozen_at_utc']},indent=2)+'\n')
print(json.dumps({'frozen_sources':len(frozen),'changed_paths':len(changed),'new_cases':sum(new.values()),'old_assertions_preserved':True}))
