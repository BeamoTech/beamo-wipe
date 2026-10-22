"""One unprivileged container; serial fresh checks with actual exit receipts."""
from pathlib import Path
import json
import subprocess
import xml.etree.ElementTree as E

r = Path(__file__).parent
w = r.parent
repo = Path('/workspace/beamo-wipe')


def group(name, *command, cwd=repo):
    subprocess.run(['python3', str(r / 'run_group.py'), name, *command], cwd=cwd, check=True)


def passed(name, count):
    cases = list(E.parse(r / (name + '.xml')).iter('testcase'))
    assert len(cases) == len({(c.get('classname'), c.get('name')) for c in cases}) == count
    assert all(c.find(t) is None for c in cases for t in ('failure', 'error', 'skipped'))


freeze = json.loads((r / 'final-freeze.json').read_text())
x11 = ['env', 'BEAMO_ISOLATED_X11_TEST=1', 'BEAMO_WIPE_DRY_RUN=1', 'dbus-run-session', '--',
       'xvfb-run', '-a', '-n', '941', '-s', '-screen 0 1600x1000x24 -dpi 72']
pytest = ['python3', '-m', 'pytest', '-W', 'error', '-p', 'no:cacheprovider',
          '-o', 'addopts=', '-o', 'pythonpath=src tests', '-q']
group('final-new-regressions', *x11, *pytest, *freeze['new_case_breakdown'],
      '--junitxml=' + str(r / 'final-new-regressions.xml'))
passed('final-new-regressions', freeze['new_python_cases'])
group('final-original-probes', *x11, *pytest, str(r / 'test_live_ownership_probe.py'),
      str(w / 'discovery/test_transient_live_ownership.py'),
      '--junitxml=' + str(r / 'final-original-probes.xml'))
passed('final-original-probes', 7)
for name in ['protected_graph_matrix.py', 'contradiction_projection_matrix.py',
             'persistence_fault_matrix.py', 'visible_consent_sequence_model.py']:
    group('final-model-' + name.removesuffix('.py'), 'env', 'PYTHONPATH=' + str(repo / 'src'),
          'BEAMO_WIPE_DRY_RUN=1', 'python3', '-W', 'error', str(r / 'model-replays' / name))
for phase in ('lint', 'preview', 'negative'):
    group('final-' + phase, 'env', 'BEAMO_GATE_CHILD=1', 'bash', 'scripts/ci-hosted.sh', phase)
for operation in ('test', 'desktop'):
    group('doctor-' + operation, 'python3', 'dev.py', 'doctor', '--for', operation)
group('final-go-race', 'go', 'test', '-count=1', '-race', '-json', './...', cwd=repo / 'desktop')
group('final-go-vet', 'go', 'vet', './...', cwd=repo / 'desktop')
group('final-go-fuzz', 'go', 'test', '-run=^$', '-fuzz=FuzzBootOption',
      '-fuzztime=350000x', '-parallel=2', cwd=repo / 'desktop')
group('final-firmware-model', 'go', 'test', '-count=1', '-race', '-overlay',
      str(r / 'firmware-overlay.json'), '-run=^TestPass9FirmwareContractMatrix$',
      '-json', './...', cwd=repo / 'desktop')
group('final-windows-test-build', 'env', 'GOOS=windows', 'GOARCH=amd64', 'go', 'test',
      '-c', '-o', str(r / 'desktop-windows.test.exe'), cwd=repo / 'desktop')
group('final-desktop-build', 'python3', 'scripts/build_desktop.py')
group('actual-preview-inspect', *x11, 'python3', str(r / 'inspect_live_preview.py'))
group('system-browser-tests', 'python3', str(r / 'system_browser_check.py'))
passed('system-browser-tests', 9)
group('final-tests', 'env', 'BEAMO_GATE_CHILD=1', 'BEAMO_GATE_JUNIT=' + str(r / 'final-tests.xml'),
      'bash', 'scripts/ci-hosted.sh', 'tests')
print('All final serial phases exited 0', flush=True)
