"""Read back all final canonical native-child results, including hidden stderr."""
import collections,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as E
root=Path.cwd();out=Path('/tmp/beamo-release-20261017/tk-pool-review/local-gates-v2');source=root/'src/beamo_wipe/ui/tk_wizard.py';h=hashlib.sha256(source.read_bytes()).hexdigest()
expected={'tests.test_tk_native_boundary_pass20':24,'tests.test_tk_native_collector_pass20':4,'tests.test_tk_native_constructor_pass20':22,'tests.test_tk_native_image_pass20':3,'tests.test_tk_variable_interpreter_pass21':7,'tests.test_tk_trace_adoption_pass21':4,'tests.test_tk_retired_pool_threads':1}
actual=collections.Counter();rows=[];direct=0
for c in E.parse(out/'final.xml').iter('testcase'):
 module=c.get('classname')
 if module not in expected:continue
 if module=='tests.test_tk_retired_pool_threads' and c.get('name')!='test_native_finalizers_stay_on_creator_during_foreign_gc':continue
 assert not any(c.find(k)is not None for k in ('failure','error','skipped'))
 properties=[]
 for p in c.iter('property'):
  try:d=json.loads(p.get('value'))
  except (ValueError,TypeError):continue
  if isinstance(d,dict)and'returncode'in d:properties.append(d)
 assert len(properties)==1,(module,c.get('name'))
 d=properties[0];assert d['returncode']==0 and not d['timed_out'] and not d['stderr'],d
 assert '"event": "child-complete"' in d['stdout']
 if module in {'tests.test_tk_native_constructor_pass20','tests.test_tk_native_image_pass20','tests.test_tk_variable_interpreter_pass21','tests.test_tk_trace_adoption_pass21','tests.test_tk_retired_pool_threads'}:
  assert d['provenance']==dict(source=str(source),sha256=h);direct+=1
 for line in d['stdout'].splitlines():
  try:event=json.loads(line)
  except ValueError:continue
  assert event.get('event')!='unraisable'
  if 'unraisables'in event:assert not event['unraisables']
 actual[module]+=1;rows.append(dict(module=module,name=c.get('name'),exit_code=0,stderr_bytes=0,timed_out=False,stdout_sha256=hashlib.sha256(d['stdout'].encode()).hexdigest()))
assert dict(actual)==expected and len(rows)==65
receipt=dict(source_sha256=h,final_junit_sha256=hashlib.sha256((out/'final.xml').read_bytes()).hexdigest(),canonical_child_results=65,direct_child_source_provenance=direct,other_children_source='Canonical source/runtime inherited from admitted full-gate environment; no per-child hash emitted',all_zero_exit=True,all_empty_stderr=True,parent_timeouts=0,nonempty_unraisables=0,modules=dict(actual),rows=rows)
with(out/'native-final-readback.json').open('x')as f:f.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items()if k!='rows'},indent=2))
