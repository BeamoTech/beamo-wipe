import ast
import difflib
import hashlib
import json
from pathlib import Path
base=Path('/tmp/pass20-primary/private-candidate5-agent.py')
raw=base.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='6b5be8d70416318a83b24e3ce6bc9dc212ab63293d2498889810401ecccbfdbe'
s=raw.decode()
marker='''def _collect_retired_interpreters() -> None:
    gc.collect()
    _drain_retired_native()
'''
replacement='''def _drain_retired_native_after_gc(phase: str, _info: dict) -> None:
    if phase == "stop" and (_RETIRED_NATIVE_ASSETS or _RETIRED_INTERPRETERS):
        # Collection can run on any thread. Each drain releases only this
        # thread's sole-owned records; it never starts another collection.
        _drain_retired_native()


gc.callbacks.append(_drain_retired_native_after_gc)


def _collect_retired_interpreters() -> None:
    gc.collect()
    _drain_retired_native()
'''
assert s.count(marker)==1
s=s.replace(marker,replacement)
ast.parse(s,filename='private-candidate6-agent.py')
out=Path('/tmp/pass20-primary/private-candidate6-agent.py')
assert not out.exists()
out.write_text(s)
Path('/tmp/pass20-primary/private-candidate6-agent.patch').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(keepends=True),s.splitlines(keepends=True),fromfile='candidate5/tk_wizard.py',tofile='candidate6/tk_wizard.py')))
receipt={'base':str(base),'base_sha256':hashlib.sha256(raw).hexdigest(),'candidate':str(out),'candidate_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'ast_parse':'PASS','runtime':'NOT RUN by author; no product imports/Tk/tests/threads/gc callbacks executed','changes':'One gc.callbacks stop-phase hook invoking the existing owner-thread lightweight drain only when pools are nonempty. No recursive collection, GC mode/threshold change, destructor/handle/traceback mutation.','shared_and_active_private_edits':'NONE','unqualified':'Await exact old failure IDs/JUnit and root independent candidate6 verification.'}
Path('/tmp/pass20-primary/private-candidate6-agent.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
