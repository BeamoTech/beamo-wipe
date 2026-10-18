"""Inspect failure provenance; no test result is treated as a gate pass."""
import collections
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
out=Path('/tmp/pass13-primary')
cases=ET.parse(out/'original.xml').findall('.//testcase')
rows={}
for case in cases:
    module=(case.get('classname') or '').rsplit('.',1)[-1]
    row=rows.setdefault(module,{'cases':0,'failed':0,'passed':0,'errors':0,'skipped':0,'failure_functions':collections.Counter()})
    row['cases']+=1
    failure=case.find('failure')
    if failure is not None:
        row['failed']+=1
        row['failure_functions'][(case.get('name') or '').split('[',1)[0]]+=1
        assert failure.get('type') in (None, 'AssertionError') and failure.get('message', '').startswith('AssertionError:'), (case.get('name'),failure.attrib)
    elif case.find('error') is not None:
        row['errors']+=1
    elif case.find('skipped') is not None:
        row['skipped']+=1
    else:
        row['passed']+=1
assert set(rows)=={'test_contents_efi_token_pass13','test_tk_input_scroll_pass13'}
classifier=rows['test_contents_efi_token_pass13']
assert classifier['cases']==104 and classifier['failed']==32 and classifier['passed']==72
assert dict(classifier['failure_functions'])=={'test_efi_letters_inside_ordinary_names_remain_data':32}
assert all(v['errors']==v['skipped']==0 for v in rows.values())
ui=rows['test_tk_input_scroll_pass13']
assert ui['failed']>0 and ui['passed']>0
allowed={'test_first_run_restores_each_screen_focus_without_changing_state','test_first_native_key_works_with_pointer_outside_window','test_initial_focus_is_claimed_once_and_held_return_keeps_gate','test_body_wheel_over_prose_scrolls_once_without_changing_focus_or_consent','test_wheel_uses_current_body_after_redraw_and_leaves_picker_controls_intact','test_native_wheel_over_hit_tested_prose_works'}
assert set(ui['failure_functions']).issubset(allowed), ui['failure_functions']
summary={'exact_starting_source_files':58,'shared_source_reverted':False,'modules':rows,'junit_sha256':hashlib.sha256((out/'original.xml').read_bytes()).hexdigest(),'disposition':'Intended original product assertion failures with adjacent passing controls; not a passing product gate.'}
(out/'original-independent-review.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
