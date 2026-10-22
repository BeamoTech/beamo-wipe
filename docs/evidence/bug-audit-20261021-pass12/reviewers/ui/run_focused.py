from pathlib import Path
import datetime
import json
import os
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET

r = Path(__file__).parent
modules = [
 'tests/test_erase_another.py',
 'tests/test_new_session_pinned_engine_regression.py',
 'tests/test_report_shutdown.py',
 'tests/test_finish_evidence_shutdown_regression.py',
 'tests/test_report_media_notice.py',
 'tests/test_result_presentations.py',
 'tests/test_separate_report_status.py',
 'tests/test_screens_report_actions.py',
 'tests/test_tk_callback_ownership_pass6_20261021.py',
 'tests/test_tk_interpreter_callback_retirement.py',
 'tests/test_tk_retired_pool_threads.py',
 'tests/test_accessible_runtime_failure_pass6_regression.py',
 'tests/test_accessible_close_cleanup_pass21.py',
 'tests/test_accessible_startup_cleanup_20261019.py',
 'tests/test_accessible_cleanup_compat_20261019.py',
 'tests/test_startup_presenter_runtime_pass37_ui.py',
 'tests/test_startup_callback_retirement_pass17.py',
 'tests/test_graphical_interface_loss_pass5_regression.py',
 'tests/test_console_interface_loss_regression.py',
 'tests/test_reader_new_session_regression.py',
 'tests/test_text_size_new_session_pass17_ui.py',
 'tests/test_language_new_session_pass16_ui.py',
 'tests/test_console_fallback_complete.py',
 'tests/test_ui_console_overlay_escape_pass10.py',
 'tests/test_helper_open_pass17_ui.py',
 'tests/test_helper_localized_landmarks_pass21_ui.py',
 'tests/test_helper_locale_guidance_pass5.py',
 'tests/test_gallery_run_again_report_pass26_ui.py',
 'tests/test_gallery_localized_copy_pass5.py',
 'tests/test_method_copy_evidence_pass37.py',
 'tests/test_method_operation_copy.py',
 'tests/test_privacy_sharing_copy.py',
 'tests/test_copy.py',
]
(r/'focused-modules.json').write_text(json.dumps(modules, indent=2)+'\n')
command = ['env','BEAMO_ISOLATED_X11_TEST=1','BEAMO_WIPE_DRY_RUN=1',
 'dbus-run-session','--','xvfb-run','-a','-n','241','-s',
 '-screen 0 1600x1000x24 -dpi 72',
 '/workspace/beamo-wipe/.venv-linux/bin/python3','-m','pytest','-q','-W','error',
 '-p','no:cacheprovider','-o','addopts=','--strict-markers',
 '--junitxml='+str(r/'focused-ui.xml'),*modules]
t = time.monotonic()
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
with tempfile.TemporaryDirectory(prefix='pass12-ui-', dir=r) as private:
 env = os.environ.copy()
 for name in ('AT_SPI_BUS_ADDRESS','DBUS_SESSION_BUS_ADDRESS'):
  env.pop(name,None)
 for name,subdir in [('XDG_RUNTIME_DIR','runtime'),('XDG_CACHE_HOME','cache')]:
  p = Path(private)/subdir; p.mkdir(mode=0o700); env[name] = str(p)
 with (r/'focused-ui.log').open('wb') as output:
  p = subprocess.run(command,cwd='/workspace/beamo-wipe',stdout=output,
    stderr=subprocess.STDOUT,umask=0o022,env=env)
receipt = {'command':command,'started_utc':started,'elapsed_seconds':round(time.monotonic()-t,2),
 'exit_code':p.returncode,'private_72dpi':True,'private_xdg_runtime_cache':True,
 'inherited_atspi_dbus_selectors_cleared':True,'child_umask':'022','fake_devices_only':True}
(r/'focused-ui.status.json').write_text(json.dumps(receipt,indent=2)+'\n')
if (r/'focused-ui.xml').exists():
 cases = list(ET.parse(r/'focused-ui.xml').iter('testcase'))
 ids = [c.get('classname','')+'::'+c.get('name','') for c in cases]
 summary = {'module_count':len(modules),'case_count':len(cases),'unique_ids':len(set(ids)),
  'failures':sum(c.find('failure') is not None for c in cases),
  'errors':sum(c.find('error') is not None for c in cases),
  'skips':[{'id':ids[i],'reason':c.find('skipped').get('message','')} for i,c in enumerate(cases) if c.find('skipped') is not None]}
 summary['passed'] = len(cases)-summary['failures']-summary['errors']-len(summary['skips'])
 (r/'focused-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps(summary))
print(json.dumps(receipt))
raise SystemExit(p.returncode)
