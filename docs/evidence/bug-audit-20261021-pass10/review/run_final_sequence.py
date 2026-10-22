"""Fresh serial phases in one unprivileged container, with actual receipts."""
from pathlib import Path
import json
import os
import subprocess
import xml.etree.ElementTree as E

os.umask(0o022)
r = Path(__file__).parent
w = r.parent
repo = Path('/workspace/beamo-wipe')
freeze = json.loads((r / 'final-freeze.json').read_text())


def group(name, *command, cwd=repo):
    subprocess.run(['python3', str(r / 'run_group.py'), name, *command], cwd=cwd, check=True)


def green(name, count):
    cases = list(E.parse(r / (name + '.xml')).iter('testcase'))
    assert len(cases) == len({(c.get('classname'), c.get('name')) for c in cases}) == count
    assert all(c.find(t) is None for c in cases for t in ('failure', 'error', 'skipped'))


x11 = ['env', 'BEAMO_ISOLATED_X11_TEST=1', 'BEAMO_WIPE_DRY_RUN=1', 'dbus-run-session', '--',
       'xvfb-run', '-a', '-n', '951', '-s', '-screen 0 1600x1000x24 -dpi 72']
pytest = ['python3', '-m', 'pytest', '-W', 'error', '-p', 'no:cacheprovider',
          '-o', 'addopts=', '-o', 'pythonpath=src tests', '-q']
group('final-new-regressions', *x11, *pytest, *freeze['new_case_breakdown'],
      '--junitxml=' + str(r / 'final-new-regressions.xml'))
green('final-new-regressions', 38)
group('final-original-probes', *x11, *pytest, str(r / 'test_late_decode_probe.py'),
      str(w / 'ui/test_late_decode_independent.py'), '--junitxml=' + str(r / 'final-original-probes.xml'))
green('final-original-probes', 8)
for script in ['typed_source_contract_matrix.py', 'log_snapshot_epoch_matrix.py',
               'refresh_generation_matrix.py', 'bundle_readback_matrix.py']:
    group('final-model-' + script.removesuffix('.py'), 'env', 'PYTHONPATH=' + str(repo / 'src'),
          'BEAMO_WIPE_DRY_RUN=1', 'python3', '-W', 'error', str(r / 'model-replays' / script))
for phase in ('lint', 'preview', 'negative'):
    group('final-' + phase, 'env', 'BEAMO_GATE_CHILD=1', 'bash', 'scripts/ci-hosted.sh', phase)
for operation in ('test', 'desktop'):
    group('doctor-' + operation, 'python3', 'dev.py', 'doctor', '--for', operation)
group('final-go-new', 'go', 'test', '-count=1', '-race', '-run=' + freeze['new_go_test_pattern'],
      '-json', './...', cwd=repo / 'desktop')
group('final-go-original-probes', 'go', 'test', '-count=1', '-race', '-overlay',
      str(r / 'close-originals-overlay.json'),
      '-run=^(TestPass10RootCloseAuthority|TestPass10CloseAdmissionProbe|TestPass10CloseInflightAdmissionProbe)$',
      '-json', './...', cwd=repo / 'desktop')
group('final-retirement-model', 'go', 'test', '-count=1', '-race', '-overlay',
      str(r / 'retirement-overlay.json'), '-run=' + freeze['go_model_test_pattern'],
      '-json', './...', cwd=repo / 'desktop')
group('final-go-race', 'go', 'test', '-count=1', '-race', '-json', './...', cwd=repo / 'desktop')
group('final-go-vet', 'go', 'vet', './...', cwd=repo / 'desktop')
group('final-go-fuzz', 'go', 'test', '-run=^$', '-fuzz=FuzzBootOption',
      '-fuzztime=350000x', '-parallel=2', cwd=repo / 'desktop')
group('final-windows-test-build', 'env', 'GOOS=windows', 'GOARCH=amd64', 'go', 'test',
      '-c', '-o', str(r / 'desktop-windows.test.exe'), cwd=repo / 'desktop')
group('final-desktop-build', 'python3', 'scripts/build_desktop.py')
group('actual-preview-inspect', *x11, 'python3', str(r / 'inspect_live_preview.py'))
group('system-browser-tests', 'python3', str(r / 'system_browser_check.py'))
green('system-browser-tests', 9)
group('final-tests', 'env', 'BEAMO_GATE_CHILD=1', 'BEAMO_GATE_JUNIT=' + str(r / 'final-tests.xml'),
      'bash', 'scripts/ci-hosted.sh', 'tests')
print('All final serial phases exited 0', flush=True)
