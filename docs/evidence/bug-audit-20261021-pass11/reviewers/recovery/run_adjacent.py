from pathlib import Path
import datetime,json,subprocess,time
repo=Path('/workspace/beamo-wipe');r=Path(__file__).parent
modules=['tests/test_release_signing.py','tests/test_release_signing_pass8.py','tests/test_signing_metadata.py','tests/test_support_contact.py','tests/test_support_code.py','tests/test_result_presentations.py','tests/test_result_elapsed_conflict_pass12.py','tests/test_separate_report_status.py']
command=['env','BEAMO_ISOLATED_X11_TEST=1','dbus-run-session','--','xvfb-run','-a','-n','221','-s','-screen 0 1600x1000x24 -dpi 72','python3','-m','pytest','-W','error','-p','no:cacheprovider','-o','addopts=','-q',*modules,'--junitxml='+str(r/'adjacent.xml')]
t=time.monotonic(); start=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (r/'adjacent.log').open('wb') as log:p=subprocess.run(command,cwd=repo,stdout=log,stderr=subprocess.STDOUT)
status={'command':command,'started_utc':start,'elapsed_seconds':round(time.monotonic()-t,2),'exit_code':p.returncode,'umask':'022','native_actions':False}
(r/'adjacent.status.json').write_text(json.dumps(status,indent=2)+'\n');print(json.dumps(status));raise SystemExit(p.returncode)
