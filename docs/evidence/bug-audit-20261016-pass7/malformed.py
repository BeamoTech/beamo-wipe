import copy, sys
sys.path[:0]=['src','tests']
from test_result_presentations import CASES, case_evidence
from beamo_wipe.outcomes import present_evidence
from beamo_wipe.privacy import make_sharing_copy,encode_sharing_copy
from beamo_wipe.result_summary import build_result_summary,build_result_report_html
_,original,_=case_evidence(CASES[0])
values=[None,False,True,0,-1,1.5,float('nan'),float('inf'),10**400,'','unknown',[],{},['secret'],{'secret':'data'}]
paths=[]
def visit(node,path=()):
    if isinstance(node,dict):
        for key,value in node.items():
            paths.append(path+(key,));visit(value,path+(key,))
visit(original)
functions=[present_evidence,make_sharing_copy,build_result_summary,build_result_report_html]
failures=[];total=0
for path in paths:
    for value in values:
        ev=copy.deepcopy(original);parent=ev
        for key in path[:-1]:parent=parent[key]
        parent[path[-1]]=value
        for fn in functions:
            total+=1
            try:fn(ev)
            except Exception as exc:failures.append((fn.__name__,'.'.join(path),repr(value)[:55],type(exc).__name__,str(exc)[:90]))
print('Calls:',total,'unhandled:',len(failures))
for entry in failures:print(entry)
