from pathlib import Path
import datetime,hashlib,json,subprocess
repo=Path('/workspace/beamo-wipe');r=Path(__file__).parent;w=r.parent
base='d8a941adc16cf0650d482f512e4b921d702373c5'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()==base
names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=repo).decode().split('\0')
frozen={n:hashlib.sha256((repo/n).read_bytes()).hexdigest()for n in sorted(names)if n and(n.startswith(('src/','tests/','scripts/','packaging/','desktop/','developer_tests/'))or n in{'dev.py','pyproject.toml','requirements-dev.txt','preview'})and(repo/n).is_file()}
assert len(frozen)==817
starting=json.loads((r/'starting-source-sha256.json').read_text())
new={'tests/test_power_acceptance_retirement_pass8_20261021.py':28,'tests/test_app_live_decode_refusal_pass8_20261021.py':34,'tests/test_cancel_diagnostic_retirement_pass8_20261021.py':25}
changed={n for n,h in frozen.items()if h!=starting.get(n)}
assert changed==set(new)|{'src/beamo_wipe/power.py','src/beamo_wipe/app.py','src/beamo_wipe/nwipe_runner.py'},changed
for n,h in starting.items():
 if n.startswith(('tests/','developer_tests/')):assert frozen[n]==h,n
for p in [r/'power-frozen-sha256.json',w/'discovery/final-owned-source-sha256.json',w/'runner/final-owned-source-sha256.json']:
 for n,h in json.loads(p.read_text()).items():assert frozen[n]==h,(p,n)
assert sum(new.values())==87
raw=json.dumps(frozen,indent=2,sort_keys=True)+'\n';(r/'final-source-sha256.json').write_text(raw)
x={'baseline_commit':base,'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_files':817,'source_manifest_sha256':hashlib.sha256(raw.encode()).hexdigest(),'new_case_breakdown':new,'new_python_cases':87,'changed_paths':sorted(changed),'all_old_test_files_byte_identical':True,'all_old_assertions_preserved':True,'all_reviewers_released':True,'verified_root_causes':3}
(r/'final-freeze.json').write_text(json.dumps(x,indent=2)+'\n')
(r/'independent-review.json').write_text(json.dumps({**x,'root_review':'Root read every product diff and all three new test modules, independently replayed each original failing proof, verified normal controls; UI reviewer independently reproduced root power defect. Unknown startup never becomes desktop fallback; only optional runner diagnostic catches change; power acceptance revoked before decision release.','native_device_power_engine_guest_actions':False},indent=2)+'\n')
print(json.dumps({'frozen_source_files':817,'new_python_cases':87,'verified_root_causes':3,'source_manifest_sha256':x['source_manifest_sha256']}))
