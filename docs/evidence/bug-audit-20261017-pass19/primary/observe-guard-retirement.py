import json
from pathlib import Path
import subprocess
import pytest

out = Path('/tmp/pass19-primary')
rows = []

class Retirement:
    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        result = yield
        report = result.get_result()
        native = subprocess.Popen
        code = getattr(native, '__code__', None)
        patch = item.funcargs.get('monkeypatch')
        rows.append(dict(nodeid=item.nodeid, when=report.when, outcome=report.outcome,
                         popen_source=code.co_filename if code is not None else 'native class',
                         patch_attributes=[name for _obj, name, _old in patch._setattr] if patch else []))

targets = [
    '/tmp/pass19-primary/fixture_release_probe.py',
    'tests/test_tk_owner_trace_lifetime_pass19.py',
    'tests/test_checkrow_trace_lifetime_pass18.py',
    'tests/test_accessible_runtime.py::test_sound_check_dialog_plays_test_and_switches_output',
    'tests/test_accessible_runtime.py::test_sound_check_dialog_reports_no_audio_and_orca_failure',
    'tests/test_accessible_runtime.py::test_sound_check_dialog_toggles_and_hears_outcome_sounds',
    'tests/test_accessible_runtime.py::test_slow_sound_discovery_does_not_block_gtk_or_update_closed_dialog',
    'tests/test_tk_runtime.py::test_isolated_x11_physical_return_release_after_start',
]
code = pytest.main(['-q', *targets, '--junitxml=' + str(out / 'guard-retirement.xml')], plugins=[Retirement()])
(out / 'guard-retirement-observations.json').write_text(json.dumps(dict(exit_code=code, rows=rows), indent=2) + '\n')
raise SystemExit(code)
