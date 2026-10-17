"""Verify final local receipts, exact inputs, new regressions and skip scope."""
import collections,hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'src'))
from beamo_wipe.verification_evidence import parse_junit_xml
from beamo_wipe.build_identity import runtime_source_sha256
out=Path('/tmp/pass14-primary')
reports=[out/'final.xml',out/'final.xml.orca.xml']
summary={'baseline_head':'35107a8d1a701093eac876a58ab4efd50e291673','runtime_source_sha256':runtime_source_sha256(),'reports':{}}
ids=[]
for p in reports:
    parsed=parse_junit_xml(p.read_text());summary['reports'][p.name]=parsed
    assert parsed['failed']==parsed['errors']==0
    ids.extend((c.get('classname'),c.get('name')) for c in ET.parse(p).findall('.//testcase'))
summary['combined_passed']=sum(v['passed'] for v in summary['reports'].values())
summary['combined_skipped']=sum(v['skipped'] for v in summary['reports'].values())
summary['combined_xfailed']=sum(v['xfailed'] for v in summary['reports'].values())
summary['duplicate_ids']=[list(k) for k,v in collections.Counter(ids).items() if v>1]
original=json.loads((out/'original-summary.json').read_text())
assert summary['combined_passed']==6783+original['cases'] and summary['combined_skipped']==14 and summary['combined_xfailed']==0 and not summary['duplicate_ids']
starting=json.loads((out/'starting-inputs.json').read_text())
new_stems={p.stem for p in (Path.cwd()/'tests').glob('test_*pass14*.py') if str(p.relative_to(Path.cwd())) not in starting}
main=ET.parse(reports[0]).findall('.//testcase')
new_cases=[c for c in main if (c.get('classname') or '').rsplit('.',1)[-1] in new_stems]
assert len(new_cases)==original['cases'] and all(not list(c) for c in new_cases)
summary['new_regression_cases_passed']=len(new_cases)
old_stems={'test_contents_efi_token_pass13','test_tk_input_scroll_pass13','test_runner_prefixed_error_context_pass12','test_sound_dialog_state_pass12','test_startup_notice_state_pass12','test_tk_startup_focus_geometry_pass12','test_accessible_focus_input_pass11','test_accessible_fullscreen_geometry_pass11','test_runner_projection_summary_context_pass11','test_diagnostic_malformed_bounds_pass8','test_runner_projection_progress_order_pass8','test_console_inventory_diagnostic_pass10','test_runner_projection_record_endings_pass10','test_sound_output_selection_pass10','test_accessible_sound_modal_pass10'}
old_cases=[c for c in main if (c.get('classname') or '').rsplit('.',1)[-1] in old_stems]
assert len(old_cases)==580 and all(not list(c) for c in old_cases)
summary['retained_prior_regressions_passed']=len(old_cases)
initial=json.loads((Path.cwd()/'docs/evidence/bug-audit-20261016-pass13/primary/final-summary.json').read_text())
assert summary['reports']['final.xml']['skips']==initial['reports']['final.xml']['skips']
assert summary['runtime_source_sha256']==json.loads((out/'source-review.json').read_text())['runtime_source_sha256']
sound=[c for c in main if c.get('name')=='test_slow_sound_discovery_does_not_block_gtk_or_update_closed_dialog']
assert len(sound)==1 and not list(sound[0]);summary['unchanged_sound_timing_case']='passed'
frozen=json.loads((out/'source-freeze.json').read_text())
assert len(frozen)==744+len(new_stems)
assert all(hashlib.sha256(Path(n).read_bytes()).hexdigest()==h for n,h in frozen.items())
summary['frozen_input_files_matched']=len(frozen)
status=json.loads((out/'local-gate-status.json').read_text())
assert len(status)==9 and all(p['exit_code']==0 for p in status)
summary['local_phase_exit_codes']={p['phase']:p['exit_code'] for p in status}
assert 'go1.26.8' in (out/'go-version.txt').read_text()
assert 'execs: 350000' in (out/'go-fuzz.txt').read_text() and 'PASS' in (out/'go-fuzz.txt').read_text()
import subprocess
exe=out/'desktop-windows.test.exe'
binary=exe.read_bytes()
assert binary.startswith(b'MZ')
pe=int.from_bytes(binary[60:64],'little')
assert binary[pe:pe+4]==b'PE\x00\x00'
assert int.from_bytes(binary[pe+4:pe+6],'little')==0x8664
assert int.from_bytes(binary[pe+24:pe+26],'little')==0x20b
summary['windows_crossbuild']={'size_bytes':exe.stat().st_size,'sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'format':'PE32+ AMD64','native_acceptance':False}
summary['all_prior_starting_inputs_preserved_except_authorized_sources']=all(hashlib.sha256(Path(n).read_bytes()).hexdigest()==h for n,h in starting.items() if n not in {'src/beamo_wipe/audio_jobs.py','src/beamo_wipe/discover.py','src/beamo_wipe/safety.py','src/beamo_wipe/ui/tk_wizard.py','tests/test_tk_input_scroll_pass13.py'})
assert summary['all_prior_starting_inputs_preserved_except_authorized_sources']
assert not subprocess.check_output(['git','diff','--cached','--name-only'])
(out/'final-summary.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='reports'},indent=2))
