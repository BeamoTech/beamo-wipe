"""Inspect failure provenance; no test result is treated as a gate pass."""
import collections
import re
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
out=Path('/tmp/pass14-primary')
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
        assert failure.get('type') in (None, 'AssertionError') and re.search(r': AssertionError(?:[:\n]|$)', failure.text or '') is not None, (case.get('name'),failure.attrib)
    elif case.find('error') is not None:
        row['errors']+=1
    elif case.find('skipped') is not None:
        row['skipped']+=1
    else:
        row['passed']+=1
expected={
 'test_protected_alias_chains_pass14':(168,72,96,{'test_composed_protection_preserves_stronger_contrary_wwns':48,'test_final_boot_guard_rechecks_complete_alias_context':24}),
 'test_audio_launch_ownership_pass14':(10,8,2,{'test_start_error_after_spawn_never_leaves_a_competing_worker':8}),
 'test_tk_focus_reveal_pass14':(29,28,1,{'test_initial_typing_and_consent_focus_is_visible':26,'test_manual_scroll_is_preserved_until_focus_changes':1,'test_stale_focus_callback_cannot_scroll_replacement_screen':1}),
}
assert set(rows)==set(expected)
for name,(total,failed,passed,functions) in expected.items():
    row=rows[name]
    assert (row['cases'],row['failed'],row['passed'],row['errors'],row['skipped'])==(total,failed,passed,0,0),row
    assert dict(row['failure_functions'])==functions,row
summary={'exact_starting_source_files':58,'shared_source_reverted':False,'modules':rows,'junit_sha256':hashlib.sha256((out/'original.xml').read_bytes()).hexdigest(),'disposition':'Intended original product assertion failures with adjacent passing controls; not a passing product gate.'}
(out/'original-independent-review.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
