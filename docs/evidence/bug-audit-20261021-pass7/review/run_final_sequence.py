from pathlib import Path
import json,subprocess,xml.etree.ElementTree as E
r=Path(__file__).parent;w=r.parent
wrapper='/workspace/beamo-tools/beamo-dev'
def group(name,*command):
 subprocess.run(['python3',str(r/'run_group.py'),name,wrapper,*command],check=True)
def passed(name,expected):
 cases=list(E.parse(r/(name+'.xml')).iter('testcase'))
 assert len(cases)==expected,(name,len(cases),expected)
 assert all(c.find(t)is None for c in cases for t in ('failure','error','skipped')),name
new=list(json.loads((r/'independent-review.json').read_text())['new_case_breakdown'])
x11=['env','BEAMO_ISOLATED_X11_TEST=1','BEAMO_WIPE_DRY_RUN=1','dbus-run-session','--','xvfb-run','-a','-n','881','-s','-screen 0 1600x1000x24 -dpi 72']
pytest=['python3','-m','pytest','-W','error','-p','no:cacheprovider','-o','addopts=','-o','pythonpath=src tests','-q']
group('final-new-regressions',*x11,*pytest,*new,'--junitxml='+str(r/'final-new-regressions.xml'));passed('final-new-regressions',170)
original=[w/'ui/test_refresh_diagnostic_interruption_probe.py',w/'recovery/test_report_intent_publish_probe.py',w/'recovery/test_report_intent_restart_probe.py',w/'recovery/test_journal_publish_probe.py',w/'discovery/test_live_filesystem_source_probe.py',w/'ui/test_plain_buffered_visibility_probe.py',w/'ui/test_plain_real_buffered_visibility_probe.py',w/'boot/test_dev_cmdline_decode_probe.py']
assert all(p.is_file()for p in original)
group('final-original-probes',*x11,*pytest,*map(str,original),'--junitxml='+str(r/'final-original-probes.xml'));passed('final-original-probes',39)
for phase in ('lint','preview','negative'):
 group('final-'+phase,'env','BEAMO_GATE_CHILD=1','bash','scripts/ci-hosted.sh',phase)
for operation in ('test','desktop'):
 group('doctor-'+operation,'python3','dev.py','doctor','--for',operation)
group('actual-preview-inspect',*x11,'python3',str(r/'inspect_live_preview.py'))
group('system-browser-tests','python3',str(r/'system_browser_check.py'));passed('system-browser-tests',9)
group('final-tests','env','BEAMO_GATE_CHILD=1','BEAMO_GATE_JUNIT='+str(r/'final-tests.xml'),'bash','scripts/ci-hosted.sh','tests')
print('All final sequence actual exits 0',flush=True)
