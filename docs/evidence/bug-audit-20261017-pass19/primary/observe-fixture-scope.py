import json
from pathlib import Path
import sys
import pytest

out = Path('/tmp/pass19-primary')
route = sys.argv[1]
probe = str(out / 'fixture_release_probe.py') if route == 'external' else 'docs/evidence/bug-audit-20261017-pass19/primary/fixture_release_probe.py'
target = 'tests/test_tk_runtime.py::test_isolated_x11_physical_return_release_after_start'
rows = []

class Scope:
    def pytest_collection_modifyitems(self, session, items):
        for item in items:
            if item.nodeid.endswith('test_isolated_x11_physical_return_release_after_start'):
                definitions = session._fixturemanager.getfixturedefs('reject_native_effects', item) or ()
                rows.append(dict(target=item.nodeid, autouse='reject_native_effects' in item.fixturenames,
                                 applicable_fixture_baseids=[definition.baseid for definition in definitions]))

command = json.loads((out / 'fixture-fixed-status.json').read_text())['command']
targets = [n for n in command[command.index('-q') + 1:] if not n.startswith('--junitxml=')]
targets[0] = probe
code = pytest.main(['--collect-only', '-q', *targets], plugins=[Scope()])
assert code == 0 and len(rows) == 1
(out / ('fixture-scope-exact-' + route + '.json')).write_text(json.dumps(rows, indent=2) + '\n')
assert rows[0]['autouse'] is (route == 'external')
print(json.dumps(rows))
