import copy,os
os.environ['BEAMO_WIPE_DRY_RUN']='1'
from beamo_wipe import privacy,outcomes,lang
from test_result_presentations import CASES,case_evidence
count=0
for language in lang.LANGUAGE_ORDER:
 lang.set_language(language)
 for case in CASES:
  _,base,_=case_evidence(case)
  word=base['method']['operation_summary'].split()[0].strip('.,')
  pairs=[(word,letter) for letter in set('withheld')]+[('overwrite','over'),('over','overwrite'),('OVERWRITE','over')]
  for serial,wwn in pairs:
   evidence=copy.deepcopy(base)
   evidence['device']['serial']=serial;evidence['device']['wwn']=wwn
   evidence['device_presentation']['id_value']=serial
   before=copy.deepcopy(evidence)
   expected=outcomes.present_evidence(evidence).code
   shared=privacy.make_sharing_copy(evidence)
   observed=outcomes.present_evidence(shared).code
   assert observed==expected,(language,case[0],serial,wwn,expected,observed,shared['method'])
   assert evidence==before
   count+=1
lang.set_language('en')
print(f'{count} multiple-secret/placeholder/prefix/case collision cases across EN/FR/DE and all11outcomes preserve original verdict/input')
