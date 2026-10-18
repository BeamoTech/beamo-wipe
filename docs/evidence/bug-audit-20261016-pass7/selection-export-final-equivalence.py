import ast,json,subprocess,unicodedata
from typing import Mapping,Any
from beamo_wipe import support_export as E
base=subprocess.check_output(['git','show','f102dfb:src/beamo_wipe/support_export.py'],text=True)
helper=next(n for n in ast.parse(base).body if isinstance(n,ast.FunctionDef) and n.name=='_strict_text')
ns={'Mapping':Mapping,'Any':Any,'SafetyError':E.SafetyError,'USB_META_INCOMPLETE':E.USB_META_INCOMPLETE,'USB_META_MALFORMED':E.USB_META_MALFORMED,'SAFE_ID_RE':E.SAFE_ID_RE,'unicodedata':unicodedata}
exec(compile(ast.Module(body=[helper],type_ignores=[]),'baseline_strict_text','exec'),ns)
def run(f,value,required=False,**kw):
 try:return ('ok',f({'field':value},'field',required=required,**kw))
 except E.SafetyError as exc:return ('refused',str(exc))
values=[None,123,True,[],{},'', 'word','A'*127,'A'*128,'A'*129]
chars=[chr(i) for i in range(33)]+['\x7f','\x85','\u00a0','\u2000','\u2001','\u2002','\u2003','\u2004','\u2005','\u2006','\u2007','\u2008','\u2009','\u200a','\u200e','\u2028','\u2029','\u202f','\u205f','\u2066','\u3000']
for c in chars:values.extend([c,c+'word','word'+c,'A'+c+'B',c+'A'*128+c])
count=0
for required in [False,True]:
 for v in values:
  assert run(E._strict_text,v,required)==run(ns['_strict_text'],v,required)
  expected=v
  if isinstance(v,str) and not any(unicodedata.category(c).startswith('C') or unicodedata.category(c) in {'Zl','Zp'} for c in v):expected=v.strip()
  assert run(E._strict_text,v,required,hardware_padding=True)==run(ns['_strict_text'],expected,required),(repr(v),required)
  count+=2
print(json.dumps({'result':'PASS','helper_equivalence_cases':count,'default_exact_original':True,'hardware_matches_original_after_safe_padding_only':True,'fake_only':True},indent=2))
