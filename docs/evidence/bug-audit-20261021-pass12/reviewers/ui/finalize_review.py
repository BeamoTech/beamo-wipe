from pathlib import Path
import datetime
import hashlib
import json
import subprocess

root = Path('/workspace/beamo-wipe')
out = Path(__file__).parent
baseline = 'b462e62005a752b0e5f2a066bda19bd9c79bbd8b'
products = [
 'src/beamo_wipe/wizard.py', 'src/beamo_wipe/app.py',
 'src/beamo_wipe/ui/tk_wizard.py', 'src/beamo_wipe/ui/accessible_wizard.py',
 'src/beamo_wipe/ui/console_wizard.py', 'src/beamo_wipe/ui/sound_dialog.py',
 'src/beamo_wipe/startup_stages.py', 'src/beamo_wipe/models.py',
 'src/beamo_wipe/outcomes.py', 'src/beamo_wipe/result_summary.py',
 'src/beamo_wipe/demo.py', 'src/beamo_wipe/gallery.py',
 'src/beamo_wipe/copy.py', 'src/beamo_wipe/lang.py',
 'helper/index.html', 'helper/fr.html', 'helper/de.html',
 'desktop/web/app.js', 'docs/screens.md',
 'tests/test_result_presentations.py', 'tests/test_erase_another.py',
]
files = sorted(set(products + json.loads((out/'focused-modules.json').read_text())))
manifest = {}
for name in files:
 data = (root/name).read_bytes()
 old = subprocess.run(['git','show',baseline+':'+name],cwd=root,check=True,capture_output=True).stdout
 manifest[name] = {'sha256': hashlib.sha256(data).hexdigest(), 'same_as_baseline': data == old}
(out/'reviewed-source-sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
focused = json.loads((out/'focused-summary.json').read_text())
model = json.loads((out/'terminal_handoff_model.json').read_text())
assert all(v['same_as_baseline'] for v in manifest.values())
assert focused['passed'] == focused['unique_ids'] == 665
assert not focused['skips'] and not focused['failures'] and not focused['errors']
assert model['mismatches'] == model['native_callbacks'] == 0
log = (out/'focused-ui.log').read_text()
assert not any(word in log.lower() for word in ('warning', 'traceback', 'critical', 'error'))
report = {'baseline':baseline,'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'scope':['terminal result/new-session/shutdown/report handoffs',
          'stale/duplicate/concurrent action admission and busy restoration',
          'Tk/GTK/curses/plain interface failure and close/startup cleanup',
          'result/report copy and helper/gallery non-erasing boundaries'],
 'verified_new_product_defects':0,'repository_edits':[],
 'reviewed_input_count':len(manifest),'all_reviewed_inputs_equal_baseline':True,
 'focused_tests':focused,
 'focused_junit_sha256':hashlib.sha256((out/'focused-ui.xml').read_bytes()).hexdigest(),
 'focused_log_warning_error_critical_matches':0,
 'model':model,
 'interpretation':'Focused tests overlap the canonical suite. Model event/scenario/race counts are supporting evidence, not extra canonical pytest IDs.',
 'limits':['no actual Orca screen-reader acceptance in this bounded task',
           'no pinned browser, native OS, engine, real device, image, firmware, power or physical/reconnect qualification',
           'the model checks finite terminal actions and cannot establish absence of every defect',
           'independent root validation and final full gate remain root-owned'],
 'ownership_released':True}
(out/'review-report.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'model.status.json').write_text(json.dumps({'command':['python',str(out/'terminal_handoff_model.py')],
 'exit_code':0,'child_umask':'022','fake_only':True,'no_gui':True,'native_callbacks':0},indent=2)+'\n')
print(json.dumps({'reviewed_inputs':len(manifest),'junit_sha256':report['focused_junit_sha256'],
 'model_sha256':model['model_sha256'],'review_sha256':hashlib.sha256((out/'review-report.json').read_bytes()).hexdigest()}))
