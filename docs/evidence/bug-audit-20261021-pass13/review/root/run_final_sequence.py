"""All final PASS13 checks serially in one unprivileged development container."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import xml.etree.ElementTree as E

os.umask(0o022)
r=Path(__file__).parent
repo=Path('/workspace/beamo-wipe')
freeze=json.loads((r/'final-freeze.json').read_text())
source=json.loads((r/'final-source-sha256.json').read_text())
assert 'BEAMO_DESKTOP_NATIVE_INVENTORY_TEST' not in os.environ

def frozen():
    assert all(hashlib.sha256((repo/name).read_bytes()).hexdigest()==digest for name,digest in source.items())

def group(name,*command,cwd=repo):
    subprocess.run(['python3',str(r/'run_group.py'),name,*command],cwd=cwd,check=True)

def green(name,count):
    cases=list(E.parse(r/(name+'.xml')).iter('testcase'))
    assert len(cases)==len({(c.get('classname'),c.get('name')) for c in cases})==count
    assert all(c.find(kind) is None for c in cases for kind in ('failure','error','skipped'))

x11=['env','BEAMO_ISOLATED_X11_TEST=1','BEAMO_WIPE_DRY_RUN=1','dbus-run-session','--',
 'xvfb-run','-a','-n','1351','-s','-screen 0 1600x1000x24 -dpi 72']
pytest=['python3','-m','pytest','-W','error','-p','no:cacheprovider','-o','addopts=',
 '-o','pythonpath=src tests developer_tests','-q']
frozen()
group('final-new-regressions',*x11,*pytest,*freeze['new_case_breakdown'],
 '--junitxml='+str(r/'final-new-regressions.xml'))
green('final-new-regressions',170)
group('final-independent-probes',*x11,*pytest,str(r/'test_gate_log_probe.py'),
 str(r/'test_remaining_probes.py'),str(r/'test_gtk_independent_probe.py'),
 '--junitxml='+str(r/'final-independent-probes.xml'))
green('final-independent-probes',18)
for name in ['probe_typed_source_ownership.py','audio_queue_model.py',
 'terminal_provenance_model.py','shutdown_overlay_epoch_model.py']:
    group('final-model-'+name.removesuffix('.py'),'env',
     'PYTHONPATH='+str(repo/'src')+':'+str(repo/'tests'),
     'BEAMO_WIPE_DRY_RUN=1','BEAMO_WIPE_DEMO=1','python3','-W','error',str(r/'model-replays'/name))
for phase in ['lint','preview','negative']:
    group('final-'+phase,'env','BEAMO_GATE_CHILD=1','bash','scripts/ci-hosted.sh',phase)
for operation in ['test','desktop']:
    group('doctor-'+operation,'python3','dev.py','doctor','--for',operation)
group('final-go-new','go','test','-count=1','-race','-run='+freeze['new_go_test_pattern'],'-json','./...',cwd=repo/'desktop')
group('final-go-independent-probe','go','test','-count=1','-race',
 '-overlay',str(r/'media-hash-overlay.json'),'-run=^TestRootMediaDigestFreshnessPass13$','-json','./...',cwd=repo/'desktop')
group('final-go-media-model','go','test','-count=1','-race',
 '-overlay',str(r/'model-replays/media-epoch-overlay.json'),'-run=^TestMediaEpochModelPass13$','-json','./...',cwd=repo/'desktop')
group('final-go-race','go','test','-count=1','-race','-json','./...',cwd=repo/'desktop')
group('final-go-vet','go','vet','./...',cwd=repo/'desktop')
group('final-go-fuzz','go','test','-run=^$','-fuzz=FuzzBootOption','-fuzztime=350000x','-parallel=2',cwd=repo/'desktop')
group('final-windows-test-build','env','GOOS=windows','GOARCH=amd64','go','test','-c','-o',str(r/'desktop-windows.test.exe'),cwd=repo/'desktop')
frozen()
group('final-desktop-build','python3','scripts/build_desktop.py')
group('actual-preview-inspect',*x11,'python3',str(r/'inspect_live_preview.py'))
group('artifact-inspection','python3',str(r/'review_artifacts.py'))
group('system-browser-tests','python3',str(r/'system_browser_check.py'))
green('system-browser-tests',9)
frozen()
group('final-tests','env','BEAMO_GATE_CHILD=1','BEAMO_GATE_JUNIT='+str(r/'final-tests.xml'),
 'bash','scripts/ci-hosted.sh','tests')
frozen()
print('All final PASS13 serial phases exited 0',flush=True)
