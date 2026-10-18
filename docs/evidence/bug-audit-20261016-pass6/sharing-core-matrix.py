import copy,os
os.environ['BEAMO_WIPE_DRY_RUN']='1'
from beamo_wipe import lang,privacy,outcomes
from test_result_presentations import CASES,case_evidence
fields=[(None,'schema_version'),(None,'outcome'),('method','id'),('method','nwipe_method'),('method','rounds'),('method','verify'),('method','overwrite_passes'),('method','verification_passes'),('method','description'),('locale','language'),('completion','validated'),('completion','reason'),('verification','verified'),('verification','requested'),('exit_evidence','exit_code'),('interruption','origin')]
values=[None,True,False,0,1,'PRIVATE-MARKER',{},[]]
count=0
for case in CASES:
 for section,key in fields:
  for value in values:
   _,evidence,_=case_evidence(case)
   target=evidence if section is None else evidence[section]
   target[key]=copy.deepcopy(value)
   evidence['device']['serial']='PRIVATE-MARKER'
   evidence['device_presentation']['id_value']='PRIVATE-MARKER'
   before=copy.deepcopy(evidence)
   original=outcomes.present_evidence(evidence).code
   shared=privacy.make_sharing_copy(evidence)
   assert before==evidence
   assert 'PRIVATE-MARKER' not in privacy.encode_sharing_copy(shared).decode()
   derived=outcomes.present_evidence(shared).code
   assert derived==original,(case[0],section,key,value,original,derived)
   count+=1
lang.set_language('en')
print(f'{count} malformed-core mutations across all existing outcome fixtures: no semantic upgrade, private marker leak, or input mutation')
