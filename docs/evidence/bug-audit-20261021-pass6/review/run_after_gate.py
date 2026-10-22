from pathlib import Path
import json,subprocess,time,xml.etree.ElementTree as E
r=Path(__file__).parent
status=r/'final-tests.status.json'
while not status.exists():time.sleep(5)
assert json.loads(status.read_text())['exit_code']==0,'Canonical gate failed; stop here'
for n in ('final-ui-adjacent.log','final-ui-adjacent.xml','final-ui-adjacent.status.json'):
 p=r/n
 if p.exists():p.rename(r/('history-integration-ui-native-flag-'+n))
cmd=['/workspace/beamo-tools/beamo-dev','env','BEAMO_ISOLATED_X11_TEST=1','dbus-run-session','--','xvfb-run','-a','-n','767','-s','-screen 0 1600x1000x24 -dpi 72','python3','-m','pytest','-W','error','-p','no:cacheprovider','-q']
cmd+=json.loads((r/'ui-adjacent-selection.json').read_text())
cmd+=['--junitxml='+str(r/'final-ui-adjacent.xml')]
subprocess.run(['python3',str(r/'run_group.py'),'final-ui-adjacent',*cmd],check=True)
cases=list(E.parse(r/'final-ui-adjacent.xml').iter('testcase'))
assert len(cases)==263 and all(c.find(t)is None for c in cases for t in ('failure','error','skipped'))
for operation in ('test','desktop'):
 subprocess.run(['python3',str(r/'run_group.py'),'doctor-'+operation,'/workspace/beamo-tools/beamo-dev','python3','dev.py','doctor','--for',operation],check=True)
print('Final affected UI263 and test/desktop development doctors pass',flush=True)
