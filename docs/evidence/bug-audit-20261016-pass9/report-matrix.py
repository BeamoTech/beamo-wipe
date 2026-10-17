import copy, json, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()/'src'))
sys.path.insert(0, str(Path.cwd()/'tests'))
from test_result_presentations import CASES,case_evidence
from beamo_wipe import lang
from beamo_wipe.outcomes import present_evidence
from beamo_wipe.privacy import make_sharing_copy
from beamo_wipe.result_summary import build_result_summary,build_result_report_html,encode_summary
from beamo_wipe.support_export import _bundle_files
values=[None,True,False,0,-1,10**500,1.5,float('nan'),float('inf'),'','\x00\n<script>disksecret</script>','\ud800',[],{},['disksecret'],{'serial':'disksecret'}]
def paths(d,p=()):
    for k,v in d.items():
        yield p+(k,)
        if isinstance(v,dict):yield from paths(v,p+(k,))
count=0
errors=[]
for language in ('en','fr','de'):
    lang.set_language(language)
    for case in CASES:
        _,original,log=case_evidence(case)
        for path in paths(original):
            for value in values:
                ev=copy.deepcopy(original)
                at=ev
                for key in path[:-1]:at=at[key]
                at[path[-1]]=value
                for name,fn in [('view',present_evidence),('share',make_sharing_copy),('text',lambda e:encode_summary(build_result_summary(e))),('html',build_result_report_html)]:
                    count+=1
                    try:fn(ev)
                    except Exception as exc:errors.append((language,case[0],'.'.join(path),type(value).__name__,name,type(exc).__name__,str(exc)))
print(json.dumps({'calls':count,'errors':errors},ensure_ascii=True,indent=2))
assert not errors
