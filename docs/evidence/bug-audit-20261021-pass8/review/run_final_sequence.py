"""One unprivileged development container, serial phases, exact actual exits."""
from pathlib import Path
import json,subprocess,xml.etree.ElementTree as E
r=Path(__file__).parent;w=r.parent;repo=Path('/workspace/beamo-wipe')
def group(name,*command,cwd=repo):
 subprocess.run(['python3',str(r/'run_group.py'),name,*command],cwd=cwd,check=True)
def passed(name,count):
 cs=list(E.parse(r/(name+'.xml')).iter('testcase'))
 assert len(cs)==count and len({(c.get('classname'),c.get('name'))for c in cs})==count
 assert all(c.find(t)is None for c in cs for t in ('failure','error','skipped')),name
x11=['env','BEAMO_ISOLATED_X11_TEST=1','BEAMO_WIPE_DRY_RUN=1','dbus-run-session','--','xvfb-run','-a','-n','931','-s','-screen 0 1600x1000x24 -dpi 72']
pytest=['python3','-m','pytest','-W','error','-p','no:cacheprovider','-o','addopts=','-o','pythonpath=src tests','-q']
new=list(json.loads((r/'final-freeze.json').read_text())['new_case_breakdown'])
group('final-new-regressions',*x11,*pytest,*new,'--junitxml='+str(r/'final-new-regressions.xml'));passed('final-new-regressions',87)
original=[r/'test_power_acceptance_probe.py',w/'discovery/test_live_decode_startup_probe.py',w/'runner/test_cancel_diagnostic_interruption_probe.py']
group('final-original-probes',*x11,*pytest,*map(str,original),'--junitxml='+str(r/'final-original-probes.xml'));passed('final-original-probes',12)
for name,script in [('inventory-model','probe_inventory_equivalence.py'),('completion-model','completion_contract_matrix.py'),('semantic-export-model','semantic_export_matrix.py')]:
 group('final-'+name,'env','PYTHONPATH='+str(repo/'src'),'python3','-W','error',str(r/'model-replays'/script))
for phase in ('lint','preview','negative'):
 group('final-'+phase,'env','BEAMO_GATE_CHILD=1','bash','scripts/ci-hosted.sh',phase)
for operation in ('test','desktop'):
 group('doctor-'+operation,'python3','dev.py','doctor','--for',operation)
group('final-go-race','go','test','-count=1','-race','-json','./...',cwd=repo/'desktop')
group('final-go-vet','go','vet','./...',cwd=repo/'desktop')
group('final-go-fuzz','go','test','-run=^$','-fuzz=FuzzBootOption','-fuzztime=350000x','-parallel=2',cwd=repo/'desktop')
group('final-readiness-model','go','test','-count=1','-race','-overlay',str(r/'readiness-overlay.json'),'-run=^TestPass8ReadinessActionModel$','-json','./...',cwd=repo/'desktop')
group('final-windows-test-build','env','GOOS=windows','GOARCH=amd64','go','test','-c','-o',str(r/'desktop-windows.test.exe'),cwd=repo/'desktop')
group('final-desktop-build','python3','scripts/build_desktop.py')
group('actual-preview-inspect',*x11,'python3',str(r/'inspect_live_preview.py'))
group('system-browser-tests','python3',str(r/'system_browser_check.py'));passed('system-browser-tests',9)
group('final-tests','env','BEAMO_GATE_CHILD=1','BEAMO_GATE_JUNIT='+str(r/'final-tests.xml'),'bash','scripts/ci-hosted.sh','tests')
print('All serial final phases exited0',flush=True)
