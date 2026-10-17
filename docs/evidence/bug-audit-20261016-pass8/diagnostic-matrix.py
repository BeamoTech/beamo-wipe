"""Bounded JSON leaf mutations at the diagnostic validation boundary."""
import copy,json,os,sys
sys.path[:0]=['src']
os.environ['BEAMO_WIPE_DRY_RUN']='1'
from beamo_wipe import diagnostic_report as d
from beamo_wipe.models import DiscoveryResult
from beamo_wipe.safety import SafetyError
from unittest.mock import patch
original=json.loads(d.create_report('discovery_failed',DiscoveryResult(error='fixture'),ui='console',session_started=0))
paths=[]
def walk(value,path=()):
    if isinstance(value,dict):
        for k,v in value.items():paths.append(path+(k,));walk(v,path+(k,))
walk(original)
values=[None,True,False,-1,0,1,1.25,float('nan'),float('inf'),10**400,-(10**400),'','unknown',[],{},[{}],{'PRIVATE-FIXTURE':'x'}]
accepted=refused=0
with patch.object(d,'application_identity',return_value=original['application']):
    for path in paths:
        for value in values:
            payload=copy.deepcopy(original);parent=payload
            for k in path[:-1]:parent=parent[k]
            parent[path[-1]]=value
            encoded=json.dumps(payload).encode()
            try:result=d.validate_report(encoded)
            except SafetyError:refused+=1
            else:assert result==payload;accepted+=1
assert accepted+refused==len(paths)*len(values)
print(json.dumps({'result':'PASS','leaf_paths':len(paths),'cases':accepted+refused,'accepted_valid':accepted,'safely_refused':refused,'unhandled_exceptions':0},indent=2))
