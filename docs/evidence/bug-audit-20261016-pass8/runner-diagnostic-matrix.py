import base64,hashlib,json
from unittest.mock import patch
from beamo_wipe import diagnostic_report as d, support_export as e
from beamo_wipe.models import DiscoveryResult
from beamo_wipe.safety import SafetyError
from test_usb_report_workflow import _payload
original=d.create_report('discovery_failed',DiscoveryResult(error='fixture'),ui='console',session_started=0)
payload,existing=_payload()
baseline=e.baseline_fingerprints(existing)
volume=e.select_export_volume(payload,baseline)
request=e._request_dict(d.verified_report(original),volume,baseline,(11,12),b'','unavailable')
checked=0
for value in [10**400,-10**400,float('inf'),float('-inf'),float('nan'),True,False,-1,'private',[],{}]:
 p=json.loads(original)
 p['time']['session_elapsed_seconds']=value
 blob=json.dumps(p).encode()
 def worker():
  req=dict(request,evidence=base64.b64encode(blob).decode(),evidence_sha256=hashlib.sha256(blob).hexdigest())
  return e._decode_worker_request(json.dumps(req).encode())
 for run in [lambda:d.validate_report(blob),lambda:d.verified_report(blob),lambda:e._bundle_files(blob,b'','unavailable'),worker]:
  try:run()
  except SafetyError as exc:assert str(exc)==d.INVALID_REPORT
  else:raise AssertionError(('accepted',value,run))
  checked+=1
for value in [None,0,1,1.25,10**100]:
 p=json.loads(original)
 p['time']['session_elapsed_seconds']=value
 blob=json.dumps(p).encode()
 assert d.validate_report(blob)==p
 assert d.verified_report(blob).data==blob
 assert e._bundle_files(blob,b'','unavailable')['diagnostic.json']==blob
 req=dict(request,evidence=base64.b64encode(blob).decode(),evidence_sha256=hashlib.sha256(blob).hexdigest())
 assert e._decode_worker_request(json.dumps(req).encode())[0].data==blob
 checked+=4
print(json.dumps({'refusals':44,'normal_controls':20,'entrypoints':4,'result':'PASS'}))
