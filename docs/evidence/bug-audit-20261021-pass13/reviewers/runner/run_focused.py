from pathlib import Path
import hashlib, json, os, subprocess, sys, time
import xml.etree.ElementTree as ET
repo = Path('/workspace/beamo-wipe')
out = Path(__file__).parent
names = '''test_cancel_after_exit_regression.py test_cancel_signal_delivery_pass3_20261019.py test_cancel_delivery_receipt_pass6_20261021.py test_cancel_diagnostic_retirement_pass8_20261021.py test_sleep_inhibit_diagnostic_retirement_pass11_20261021.py test_runner_status_regressions.py test_runner_request_binding_pass14_runner.py test_runner_concurrent_progress_order.py test_runner_signal_readiness_pass8.py test_runner_readiness_record_provenance.py test_engine_checks.py test_engine_checks_incomplete_records.py test_engine_checks_spoof_pass11.py test_progress_timing.py test_progress_finish_clock_pass13.py test_progress_unknown_final_stage_pass10.py test_stale_progress.py test_audio_launch_ownership_pass14.py test_audio_launch_interruptions_pass20.py test_audio_launch_acceptance_pass20.py test_sound_reaper_pass8.py test_sound_cancelled_spawn_pass13_20261021.py'''.split()
files = [repo / 'tests' / name for name in names]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
inputs = {str(p.relative_to(repo)): sha(p) for p in files}
(out / 'selected-tests.json').write_text(json.dumps(inputs, indent=2) + '\n')
env = dict(os.environ)
env['BEAMO_WIPE_DRY_RUN'] = '1'
env.pop('BEAMO_WIPE_LIVE', None)
start = time.monotonic()
with (out / 'focused.log').open('w') as log:
    result = subprocess.run([sys.executable, '-m', 'pytest', '-W', 'error', '-q', *map(str,files), '--junitxml=' + str(out/'focused.xml')], cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT, umask=0o022)
root = ET.parse(out / 'focused.xml').getroot()
cases = root.findall('.//testcase')
summary = dict(exit_code=result.returncode, elapsed_seconds=round(time.monotonic()-start,3), cases=len(cases), failures=len(root.findall('.//failure')), errors=len(root.findall('.//error')), skips=len(root.findall('.//skipped')), unchanged_tests=all(sha(repo/p)==s for p,s in inputs.items()), strict_warnings=True, child_umask='022', private_display_required=False)
(out / 'focused.status.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, sort_keys=True))
sys.exit(result.returncode)
