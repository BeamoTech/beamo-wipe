"""Independently verify final frozen source, gates, cases and platform limits."""
import collections
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

root = Path.cwd()
out = Path('/tmp/pass16-primary')
sys.path.insert(0, str(root / 'src'))
from beamo_wipe.build_identity import runtime_source_sha256
from beamo_wipe.verification_evidence import parse_junit_xml

prior = json.loads((root / 'docs/evidence/bug-audit-20261016-pass15/primary/final-summary.json').read_text())
freeze = json.loads((out / 'source-freeze.json').read_text())
starting = json.loads((out / 'starting-inputs.json').read_text())
assert len(freeze) == 754 and len(starting) == 751
assert all(hashlib.sha256((root / n).read_bytes()).hexdigest() == h for n, h in freeze.items())
allowed = {'src/beamo_wipe/discover.py', 'src/beamo_wipe/ui/accessible_wizard.py',
           'src/beamo_wipe/ui/tk_wizard.py', 'tests/test_tk_input_scroll_pass13.py',
           'tests/test_accessible_key_repeat.py', 'tests/test_accessible_last_chance_actions_pass12_ui.py',
           'tests/test_pick_scroll_restore.py'}
changed = {n for n, h in starting.items() if hashlib.sha256((root / n).read_bytes()).hexdigest() != h}
assert changed == allowed
reports = {name: parse_junit_xml((out / name).read_text()) for name in ('final.xml', 'final.xml.orca.xml')}
assert all(r['failed'] == r['errors'] == r['xfailed'] == 0 for r in reports.values())
cases = [c for name in reports for c in ET.parse(out / name).findall('.//testcase')]
ids = [(c.get('classname'), c.get('name')) for c in cases]
assert len(ids) == len(set(ids))
assert reports['final.xml']['skips'] == prior['reports']['final.xml']['skips']
passed = sum(r['passed'] for r in reports.values())
skipped = sum(r['skipped'] for r in reports.values())
original = json.loads((out / 'original-summary.json').read_text())
assert original['cases'] == 398 and original['failures'] == 203
assert original['errors'] == original['skipped'] == 0 and original['pytest_exit'] == 1
assert passed == prior['combined_passed'] + original['cases'] == 7966 and skipped == 14
new_stems = {Path(n).stem for n in json.loads((out / 'original-files.json').read_text())}
old_stems = {Path(n).stem for n in json.loads((root / 'docs/evidence/bug-audit-20261016-pass15/primary/new-tests-sha256.json').read_text())}
new_cases = [c for c in cases if c.get('classname', '').rsplit('.', 1)[-1] in new_stems]
old_cases = [c for c in cases if c.get('classname', '').rsplit('.', 1)[-1] in old_stems]
assert len(new_cases) == 398 and all(not list(c) for c in new_cases)
assert len(old_cases) == 1365 and all(not list(c) for c in old_cases)
original_cases = ET.parse(out / 'original.xml').findall('.//testcase')
original_modules = {}
for stem in new_stems:
    group = [c for c in original_cases if c.get('classname', '').rsplit('.', 1)[-1] == stem]
    failures = [c for c in group if c.find('failure') is not None]
    assert all(c.find('failure').get('type') == 'AssertionError' for c in failures)
    if 'callback_lifetime' in stem:
        assert len(failures) == 26 and all('Tcl bgerror' in c.find('failure').get('message', '') for c in failures)
    original_modules[stem] = dict(cases=len(group), failures=len(failures), controls=len(group)-len(failures))
status = json.loads((out / 'local-gate-status.json').read_text())
assert len(status) == 9 and all(p['exit_code'] == 0 for p in status)
started=datetime.datetime.fromisoformat(status[-1]['started_utc']).timestamp()
assert all((out/name).stat().st_mtime>=started for name in reports)
config=json.loads((out/'source-review.json').read_text())['local_runtime_config']
assert hashlib.sha256((out/'run-gates.py').read_bytes()).hexdigest()==config['run_gates_sha256']
assert hashlib.sha256((out/'fallback-guard-manifest.json').read_bytes()).hexdigest()==config['fallback_guard_manifest_sha256']
assert str(Path(config['python']).resolve())==config['resolved_python']
assert not (out/'forbidden-fallback-attempts.txt').exists()
allowed_cli=[json.loads(row) for row in (out/'permitted-offline-gcloud.jsonl').read_text().splitlines()]
assert len(allowed_cli)==1 and allowed_cli[0]['command'][:2]==['meta','list-files-for-upload']
assert allowed_cli[0]['test']=='tests/test_ci_hosted.py::test_cloud_upload_excludes_local_captures_and_env_files (call)'
assert 'go1.26.8' in (out / 'go-version.txt').read_text()
assert 'execs: 350000' in (out / 'go-fuzz.txt').read_text() and 'PASS' in (out / 'go-fuzz.txt').read_text()
binary = (out / 'desktop-windows.test.exe').read_bytes()
pe = int.from_bytes(binary[60:64], 'little')
assert binary[:2] == b'MZ' and binary[pe:pe+4] == b'PE\x00\x00'
assert int.from_bytes(binary[pe+4:pe+6], 'little') == 0x8664
assert int.from_bytes(binary[pe+24:pe+26], 'little') == 0x20b
runtime = runtime_source_sha256()
assert runtime == json.loads((out / 'source-review.json').read_text())['runtime_source_sha256']
timing = [c for c in cases if c.get('name') == 'test_slow_sound_discovery_does_not_block_gtk_or_update_closed_dialog']
assert len(timing) == 1 and not list(timing[0])
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'])
subprocess.run(['git', 'diff', '--check'], check=True)
summary = dict(reports=reports, combined_passed=passed, combined_skipped=skipped,
               duplicate_ids=[], new_regression_cases_passed=398,
               retained_prior_regressions_passed=1365, original_modules=original_modules,
               runtime_source_sha256=runtime, frozen_input_files_matched=754,
               starting_input_files_unchanged=744, changed_starting_paths=sorted(changed),
               local_phase_exit_codes={p['phase']: p['exit_code'] for p in status},
               unchanged_sound_timing_case='passed',
               fresh_junit_reports=True, forbidden_fallback_attempts=0,
               permitted_offline_cli_calls=allowed_cli,
               windows_crossbuild=dict(format='PE32+ AMD64', size_bytes=len(binary),
                   sha256=hashlib.sha256(binary).hexdigest(), native_acceptance=False))
(out / 'final-summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
print(json.dumps({k:v for k,v in summary.items() if k != 'reports'}, indent=2))
