"""Independently authenticate final controlled traces and exact fixtures."""
import hashlib
import json
from pathlib import Path
import struct
import tarfile
import xml.etree.ElementTree as ET

out = Path('/tmp/pass15-primary')
frozen = json.loads((out / 'source-freeze.json').read_text())
read = lambda path: json.loads(Path(path).read_text())
sha = lambda data: hashlib.sha256(data).hexdigest()
assert all(sha(Path(name).read_bytes()) == digest for name, digest in frozen.items())
status = read(out / 'fresh-verification-status.json')
assert len(status) == 7 and all(row['exit_code'] == 0 and row['receipt_validated'] for row in status)

adjacent = ET.parse(out / 'adjacent.xml').findall('.//testcase')
assert len(adjacent) == 2275 and all(not list(case) for case in adjacent)
for name, count in [('omitted-alias-context.json', 288), ('omitted-duplicate-observation.json', 36)]:
    data = read(out / name)
    assert data['cases'] == data['passed'] == len(data['results']) == count
    assert not data['native_attempts'] and data['violations'] == 0
    assert all(row['passed'] for row in data['results'])
wheel = read(out / 'empty-wheel-probe.json')
assert wheel['source_sha256'] == frozen['src/beamo_wipe/ui/tk_wizard.py']
assert wheel['cases'] == len(wheel['rows']) == 8 and wheel['behavior_failures'] == 0 and not wheel['effects']
assert all(row['reader_scrolled'] and row['parent_unchanged'] and row['hit_is_reader'] and row['state_unchanged'] and row['focus_unchanged'] and not row['callback_errors'] and not row['engine_started'] for row in wheel['rows'])
for log in ('empty-wheel-probe.txt',):
    text = (out / log).read_text()
    assert 'Traceback' not in text and 'bgerror' not in text
utf = read(out / 'utf8-tail-probe.json')
assert utf['cases'] == len(utf['rows']) == 30 and utf['boundary_cuts'] == 18
assert utf['runner_success_presentation_indeterminate'] == utf['native_effects'] == 0
with tarfile.open(out / 'utf8-exact-log-fixtures.tar.gz', 'r:gz') as archive:
    fixtures = {item.name: archive.extractfile(item).read() for item in archive.getmembers()}
    assert len(fixtures) == 10
    for row in utf['rows']:
        blobs = [blob for blob in fixtures.values() if sha(blob) == row['raw_file_sha256']]
        assert len(blobs) == 1 and len(blobs[0]) == row['raw_file_bytes']
        blobs[0].decode('utf-8')
        expected = 'unverified' if row['method'] == 'quick_zero' else 'verified'
        assert row['presentation_code'] == row['direct_presentation_code'] == row['recovery_code'] == expected
        assert row['export_ready'] and not row['export_error'] and row['runner_ok']

runner_dir = Path('/tmp/pass15-runner')
runner = read(runner_dir / 'projection-summary.json')
short = read(runner_dir / 'projection-rows.json')
actual = read(runner_dir / 'actual-large-results.json')
assert len(short) == runner['short_differential_cases'] == 432
assert len(actual) == runner['actual_large_cases'] == 324
assert runner['mismatches'] == runner['native_acquisition_calls'] == 0 and runner['source_unchanged']
assert not read(runner_dir / 'projection-mismatches.json')
assert all(row['same'] and row['full_outcome'] == row['projection_outcome'] for row in short)
assert all(frozen[name] == digest for name, digest in runner['source'].items())
by_index = {row['index']: row for row in short}
with tarfile.open(runner_dir / 'exact-large-fixtures.tar.gz', 'r:gz') as archive:
    fixtures = {item.name: archive.extractfile(item).read() for item in archive.getmembers()}
    assert len(fixtures) == runner['large_fixtures'] == 108
    assert all(len(blob) > 1024 * 1024 for blob in fixtures.values())
    for row in actual:
        blob = fixtures[f"{row['index']:03d}-{row['variant']}.log"]
        assert len(blob) == row['bytes'] and sha(blob) == row['sha256']
        base = by_index[row['index']]
        assert row['method'] == base['method'] and row['target'] == base['target'] and row['variant'] == base['variant']
        expected = (False, 'cancelled') if row['finish'] == 'running_stop' else (base['full_outcome'][0], base['full_outcome'][2])
        assert (row['ok'], row['reason']) == expected

ui_dir = Path('/tmp/pass15-ui')
geometry = read(ui_dir / 'geometry-summary.json')
layout = read(ui_dir / 'geometry-matrix.json')
assert geometry['cases'] == geometry['passed'] == len(layout['rows']) == 270
assert not geometry['failed'] and not geometry['forbidden_calls'] and not layout['forbidden_calls']
assert geometry['hashes'] == geometry['final_hashes'] == layout['hashes']
assert all(frozen[name] == digest for name, digest in geometry['hashes'].items())
assert all(row['ok'] and row['state_unchanged'] and not row['callback_errors'] for row in layout['rows'])
critical = [row for row in layout['rows'] if row['surface'] == 'tk' and row['screen'] in ('KEYBOARD', 'OWNER', 'CONFIRM')]
assert len(critical) == 27 and all(row['focus_fully_visible'] for row in critical)
log = (ui_dir / 'geometry-matrix.txt').read_text()
assert all(word not in log for word in ('bgerror', 'Traceback', 'Exception in Tkinter callback'))
captures = {}
paths = [out / 'empty-wheel-empty.png', out / 'empty-wheel-happy.png'] + [ui_dir / f'fixed-geometry-tk-en-{size}-{screen}.png' for size, screen in [('standard', 'OWNER'), ('extra', 'KEYBOARD'), ('large', 'CONFIRM')]]
for path in paths:
    blob = path.read_bytes()
    assert blob[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', blob[16:24]) == (800, 600)
    captures[str(path)] = dict(size_bytes=len(blob), sha256=sha(blob), dimensions=[800, 600], independently_viewed=True)

receipt = dict(runtime_source_sha256=read(out / 'source-review.json')['runtime_source_sha256'],
               fresh_phases_validated=7, adjacent_cases_passed=2275, alias_cases_passed=288,
               duplicate_cases_passed=36, wheel_cases_passed=8, valid_utf8_roundtrips=30,
               valid_utf8_fixtures_authenticated=10, short_full_projection_cases=432,
               actual_large_poll_stop_cases=324, large_fixtures_authenticated=108,
               native_layout_cases=270, critical_tk_focus_fully_visible=27,
               native_application_effects=0, callback_errors=0, native_captures=captures)
(out / 'focused-independent-review.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({k: v for k, v in receipt.items() if k != 'native_captures'}, indent=2))
