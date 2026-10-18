import hashlib,json,subprocess,sys,types
from beamo_wipe import diagnostic_report as fixed
from beamo_wipe.models import DiscoveryResult
from beamo_wipe.safety import SafetyError
assert sys.getrecursionlimit()==1000
old=types.ModuleType('pass8_baseline_diagnostic')
exec(compile(subprocess.check_output(['git','show','35107a8:src/beamo_wipe/diagnostic_report.py']),'baseline-diagnostic','exec'),old.__dict__)
base=json.loads(fixed.create_report('discovery_failed',DiscoveryResult(error='fake'),ui='console',session_started=0))
counts={'original_unhandled':0,'fixed_refused':0,'finite_controls':0,'malformed_controls':0}
for value in (10**400,-(10**400)):
 p=json.loads(json.dumps(base));p['time']['session_elapsed_seconds']=value;raw=json.dumps(p).encode()
 try:old.validate_report(raw)
 except OverflowError:counts['original_unhandled']+=1
 else:raise AssertionError('original overflow not reproduced')
 try:fixed.validate_report(raw)
 except SafetyError as e:assert str(e)==fixed.INVALID_REPORT;counts['fixed_refused']+=1
 else:raise AssertionError('fixed accepted invalid elapsed')
# CPython3.12's C parser accepts byte-bounded depth7500. That remains a
# baseline safe schema refusal; bookworm's decoder failure is modeled below.
raw=b'['*7500+b'0'+b']'*7500
assert len(raw)<=fixed.MAX_BYTES
for module in (old,fixed):
 try:module.validate_report(raw)
 except SafetyError:pass
 else:raise AssertionError('accepted deeply nested JSON')
counts['malformed_controls']+=1
original_loads=json.loads
def exhausted(*a,**kw):raise RecursionError('fake decoder boundary')
try:
 json.loads=exhausted
 try:old.validate_report(b'{}')
 except RecursionError:counts['original_unhandled']+=1
 else:raise AssertionError('original did not expose injected recursion')
 try:fixed.validate_report(b'{}')
 except SafetyError as e:assert str(e)==fixed.INVALID_REPORT;counts['fixed_refused']+=1
 else:raise AssertionError('fixed did not wrap decoder recursion')
finally:json.loads=original_loads
for value in (None,0,1,1.25,10**100,2**1023):
 p=json.loads(json.dumps(base));p['time']['session_elapsed_seconds']=value;raw=json.dumps(p).encode()
 assert old.validate_report(raw)==fixed.validate_report(raw)==p;counts['finite_controls']+=1
for raw in (b'',b'null',b'[]',b'{}',b'{',b'0',b'"x"',b'NaN',b'\xff',b' '*16385):
 for module in (old,fixed):
  try:module.validate_report(raw)
  except SafetyError:pass
  else:raise AssertionError('accepted malformed raw')
 counts['malformed_controls']+=1
print(json.dumps(counts,indent=2))
print('diagnostic_report.py SHA256',hashlib.sha256(open(fixed.__file__,'rb').read()).hexdigest())
