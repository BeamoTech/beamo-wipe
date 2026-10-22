"""All final checks serially in one unprivileged development container."""
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
       'xvfb-run', '-a', '-n', '1151', '-s', '-screen 0 1600x1000x24 -dpi 72']
pytest = ['python3', '-m', 'pytest', '-W', 'error', '-p', 'no:cacheprovider',
          '-o', 'addopts=', '-o', 'pythonpath=src tests', '-q']
group('final-new-regressions', *x11, *pytest, *freeze['new_case_breakdown'],
      '--junitxml=' + str(r / 'final-new-regressions.xml'))
green('final-new-regressions', freeze['new_python_cases'])
group('final-original-probes', *x11, *pytest, str(r / 'test_inhibit_optional_probe.py'),
      str(w / 'runner/test_inhibitor_diagnostic_retirement_probe.py'),
      '--junitxml=' + str(r / 'final-original-probes.xml'))
green('final-original-probes', 16)
for script in ['protected_alias_capacity_matrix.py', 'cancellation_ownership_matrix.py',
               'review_detour_layout_matrix.py', 'volatile_transaction_matrix.py']:
    group('final-model-' + script.removesuffix('.py'), 'env', 'PYTHONPATH=' + str(repo / 'src') + ':' + str(repo / 'tests'),
          'BEAMO_WIPE_DRY_RUN=1', 'python3', '-W', 'error', str(r / 'model-replays' / script))
for phase in ('lint', 'preview', 'negative'):
    group('final-' + phase, 'env', 'BEAMO_GATE_CHILD=1', 'bash', 'scripts/ci-hosted.sh', phase)
for operation in ('test', 'desktop'):
    group('doctor-' + operation, 'python3', 'dev.py', 'doctor', '--for', operation)
group('final-go-new', 'go', 'test', '-count=1', '-race', '-run=' + freeze['new_go_test_pattern'],
      '-json', './...', cwd=repo / 'desktop')
group('final-go-original-probes', 'go', 'test', '-count=1', '-race', '-overlay',
      str(r / 'go-originals-overlay.json'),
      '-run=^(TestPass11RootOutputDrainDeadline|TestPass11RootOutputCaptureLimit|TestPass11OutputCancellationProbe)$',
      '-json', './...', cwd=repo / 'desktop')
group('final-plan-model', 'go', 'test', '-count=1', '-race', '-overlay',
      str(r / 'plan-model-overlay.json'), '-run=^TestPass11PlanFreshnessMatrix$',
      '-json', './...', cwd=repo / 'desktop')
group('final-go-race', 'go', 'test', '-count=1', '-race', '-json', './...', cwd=repo / 'desktop')
group('final-go-vet', 'go', 'vet', './...', cwd=repo / 'desktop')
group('final-go-fuzz', 'go', 'test', '-run=^$', '-fuzz=FuzzBootOption',
      '-fuzztime=350000x', '-parallel=2', cwd=repo / 'desktop')
group('final-windows-test-build', 'env', 'GOOS=windows', 'GOARCH=amd64', 'go', 'test',
      '-c', '-o', str(r / 'desktop-windows.test.exe'), cwd=repo / 'desktop')
group('final-desktop-build', 'python3', 'scripts/build_desktop.py')
group('actual-preview-inspect', *x11, 'python3', str(r / 'inspect_live_preview.py'))
group('artifact-inspection', 'python3', str(r / 'review_artifacts.py'))
group('system-browser-tests', 'python3', str(r / 'system_browser_check.py'))
green('system-browser-tests', 9)
group('final-tests', 'env', 'BEAMO_GATE_CHILD=1', 'BEAMO_GATE_JUNIT=' + str(r / 'final-tests.xml'),
      'bash', 'scripts/ci-hosted.sh', 'tests')
print('All final serial phases exited 0', flush=True)
