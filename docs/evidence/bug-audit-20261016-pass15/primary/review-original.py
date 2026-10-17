"""Attribute each original-source failure to the proved bug assertion."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import xml.etree.ElementTree as ET

out = Path('/tmp/pass15-primary')
cases = ET.parse(out / 'original.xml').findall('.//testcase')
expected = {
    'test_inventory_wheel_scrolls_only_its_reader': (24, 'reader.yview()[0] - before[0]'),
    'test_empty_inventory_scrollbar_keeps_its_own_wheel_command': (8, 'reader.yview()[0]-before[0]'),
    'test_hidden_positive_requires_complete_target_record': (22, "assert check['status']"),
    'test_malformed_positive_is_unavailable_in_runner_evidence': (18, "assert evidence['checks'][0]['status'] == 'unavailable'"),
    'test_omitted_physical_bridge_keeps_boot_and_mount_protection': (120, 'assert (leaf.path in {disk.path for disk in result.selectable}) is not protected'),
    'test_final_boot_guard_rechecks_retained_physical_evidence': (60, 'DID NOT RAISE'),
    'test_display_error_cannot_hide_conflicting_physical_observation': (20, 'assert "/dev/sda" not in {disk.path for disk in result.selectable}'),
    'test_conflicting_observation_refusal_can_recover_on_clean_retry': (1, 'assert not first.selectable'),
    'test_unusable_duplicate_id_cannot_compare_equal_to_missing': (4, 'assert "/dev/sda" not in {disk.path for disk in result.selectable}'),
    'test_valid_utf8_tail_boundaries_preserve_terminal_roundtrip': (18, 'assert payload["presentation"]["code"] == code'),
    'test_bounded_invalid_utf8_capture_preserves_terminal_roundtrip': (3, 'assert payload["presentation"]["code"] == code'),
}
counts = Counter()
modules = defaultdict(Counter)
reviewed = []
for case in cases:
    assert case.find('error') is None and case.find('skipped') is None
    failure = case.find('failure')
    modules[case.get('classname')]['failed' if failure is not None else 'passed'] += 1
    if failure is None:
        assert not list(case)
        continue
    function = case.get('name').split('[')[0]
    assert function in expected
    text = failure.text or ''
    assert expected[function][1] in text, (function, text)
    guard = function == 'test_final_boot_guard_rechecks_retained_physical_evidence'
    assert ('DID NOT RAISE' in failure.get('message', '') and 'beamo_wipe.safety.SafetyError' in failure.get('message', '')) if guard else 'AssertionError' in text
    if function == 'test_inventory_wheel_scrolls_only_its_reader':
        assert '-empty-' in case.get('name')
    counts[function] += 1
    reviewed.append(dict(id=case.get('classname') + '::' + case.get('name'),
                         kind='expected missing SafetyError' if guard else 'intended AssertionError'))
assert len(cases) == 578 and len(reviewed) == 298
assert counts == {name: count for name, (count, _) in expected.items()}
receipt = dict(cases=578, intended_failures=298, passing_controls=280, errors=0, skips=0,
               exact_missing_SafetyError_failures=60, intended_AssertionErrors=238,
               per_module=modules, per_function=counts, reviewed_failures=reviewed)
(out / 'original-independent-review.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({k: v for k, v in receipt.items() if k != 'reviewed_failures'}, indent=2))
