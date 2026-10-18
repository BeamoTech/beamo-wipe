import copy,os
os.environ['BEAMO_WIPE_DRY_RUN']='1'
from beamo_wipe import privacy,outcomes
from test_result_presentations import CASES,case_evidence
secret='PRIVATE-NESTED-IDENTIFIER'
sections={'device':privacy._KEEP_DEVICE,'device_presentation':privacy._KEEP_DEVICE_PRESENTATION,'method':privacy._KEEP_METHOD,'timestamps':privacy._KEEP_TIMESTAMPS,'nwipe':privacy._KEEP_NWIPE,'exit_evidence':privacy._KEEP_EXIT,'verification':privacy._KEEP_VERIFICATION,'completion':privacy._KEEP_COMPLETION,'interruption':privacy._KEEP_INTERRUPTION,'presentation':privacy._KEEP_PRESENTATION,'locale':privacy._KEEP_LOCALE}
placements=[(None,key) for key in privacy._KEEP_ROOT if key not in sections and key!='warnings']+[(section,key) for section,keys in sections.items() for key in keys]+[(None,'warnings')]
count=0
for section,key in placements:
 for malformed in ({secret:'nested'},[{secret:'nested'}]):
  _,evidence,_=case_evidence(CASES[0])
  evidence['device']['serial']=secret
  evidence['device_presentation']['id_value']=secret
  target=evidence if section is None else evidence[section]
  target[key]=copy.deepcopy(malformed)
  before=copy.deepcopy(evidence)
  original=outcomes.present_evidence(evidence).code
  shared=privacy.make_sharing_copy(evidence)
  assert secret not in privacy.encode_sharing_copy(shared).decode(),(section,key)
  assert evidence==before
  assert outcomes.present_evidence(shared).code==original,(section,key)
  count+=1
print(f'{count} malformed nested-container placements across all retained fields: no key leak, verdict change or original mutation')
