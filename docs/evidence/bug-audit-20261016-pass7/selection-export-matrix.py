import copy,json,os
from beamo_wipe.discover import node_to_disk
from beamo_wipe.support_export import baseline_fingerprints,select_export_volume
from beamo_wipe.safety import SafetyError
from test_usb_report_workflow import _payload
os.environ['BEAMO_WIPE_DRY_RUN']='1'
count=0
pads=[' ','\u00a0','\u2002','\u2003','\u3000']
for index in range(3):
 for field in ['model','serial','wwn']:
  for pad in pads:
   for length in [1,127,128]:
    p,_=_payload();p['blockdevices'][index][field]=pad+'A'*length+pad
    baseline=baseline_fingerprints(tuple(node_to_disk(n,i==0) for i,n in enumerate(p['blockdevices'][:2])))
    snapshot=copy.deepcopy(p)
    assert select_export_volume(p,baseline).path=='/dev/sdc1'
    assert p==snapshot
    count+=1
for index in range(3):
 for field in ['model','serial','wwn']:
  for bad in ['\t','\r','\n','\x00','\x7f','\u0085','\u2028','\u2029','\u200e','\u2066', 'A'*129]:
   p,d=_payload();p['blockdevices'][index][field]=' '+bad+' '
   try: select_export_volume(p,baseline_fingerprints(d))
   except SafetyError: pass
   else: raise AssertionError((index,field,repr(bad)))
   count+=1
for index in [0,1]:
 for field in ['model','serial','wwn']:
  p,d=_payload();p['blockdevices'][index][field]=' changed '
  try:select_export_volume(p,baseline_fingerprints(d))
  except SafetyError:pass
  else:raise AssertionError((index,field))
  count+=1
print(json.dumps({'result':'PASS','independent_cases':count,'valid_padding_length_cases':135,'malformed_control_overlength_cases':99,'protected_change_cases':6,'fake_only':True},indent=2))
