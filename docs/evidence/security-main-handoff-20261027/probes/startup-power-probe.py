"""Exact startup/power guards with fake runner types, probes and power action."""
from pathlib import Path
import ast,hashlib,json,sys,types
out=Path(__import__('os').environ['BEAMO_SECURITY_OUTPUT']);root=Path(__import__('os').environ['BEAMO_SECURITY_ROOT']);phase=sys.argv[1]
bound=[]
def selected(path,names,cls=None):
 raw=(root/path).read_bytes();tree=ast.parse(raw)
 if cls:tree=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls)
 nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
 for n in nodes:bound.append({'path':path,'file_sha256':hashlib.sha256(raw).hexdigest(),'name':n.name,'line':n.lineno,'end':n.end_lineno,'ast_sha256':hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest()})
 return nodes
class Lock:
 def __enter__(self):return self
 def __exit__(self,*a):return False
class RealRunner:pass
class DryRunner:pass
state={'probe':False,'probe_calls':0,'power_calls':0}
def probe():
 state['probe_calls']+=1
 if state['probe']=='error':raise OSError('fake probe failure')
 return state['probe']
def import_fake(name,*a,**k):
 if name=='__future__':return __import__(name)
 if name=='beamo_wipe.nwipe_runner':return types.SimpleNamespace(pinned_nwipe_already_running=probe)
 if name=='beamo_wipe.diagnostic_report':return types.SimpleNamespace(exception_code=lambda exc:'startup')
 if name=='beamo_wipe.models':return types.SimpleNamespace(DiscoveryResult=lambda **kw:types.SimpleNamespace(**kw))
 raise AssertionError('unexpected import '+name)
g={'__builtins__':{**vars(__import__('builtins')),'__import__':import_fake,'print':lambda *a,**k:None},'NwipeRunner':RealRunner,'DryRunRunner':DryRunner,'running_on_live_usb':lambda:True,'STARTUP_BLOCKED':'startup blocked','STARTUP_BLOCKED_LOG':'startup {code}','POWER_REQUEST_BLOCKED':'blocked','Screen':types.SimpleNamespace(PICK_BLOCKED='blocked'),'sys':types.SimpleNamespace(stderr=None)}
methods=selected('src/beamo_wipe/wizard.py',{'_live_pinned_engine_busy','shutdown_still_safe','_session_store_busy'},'Wizard')
wrapper=ast.ClassDef(name='Wizard',bases=[],keywords=[],body=methods,decorator_list=[])
nodes=ast.parse('from __future__ import annotations').body+[wrapper]+selected('src/beamo_wipe/app.py',{'_blocked_wizard','_shutdown_if_still_safe'})
exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'<exact-source-guards>','exec'),g)
W=g['Wizard']
def init(self,discovery,runner,*,dry_run):
 self._session_store=None;self.runner=runner;self.dry_run=dry_run;self.preview=False;self._lock=Lock();self.wants_shutdown=True;self.wants_new_session=False
 for name in ('_runner_is_active','_recovery_busy','_new_session_store_blocked'):setattr(self,name,lambda:False)
 for name in ('_finishing','_evidence_saving','_report_exporting','_diagnostic_busy'):setattr(self,name,False)
W.__init__=init
def power():state['power_calls']+=1;return True
g['_shutdown']=power;rows=[]
for runner in ('fallback','real'):
 for status in (False,True,None,'error'):
  state.update(probe=status,probe_calls=0,power_calls=0)
  w=g['_blocked_wizard'](OSError('fake startup error'))
  assert w.dry_run is False and w._startup_blocked
  if runner=='real':w.runner=RealRunner()
  allowed=g['_shutdown_if_still_safe'](w);expected=status is False
  actual={'allowed':allowed,'power_calls':state['power_calls'],'probe_calls':state['probe_calls']}
  want={'allowed':expected,'power_calls':int(expected),'probe_calls':1}
  rows.append({'case':runner+'-'+str(status),'actual':actual,'expected':want,'match':actual==want})
for exclusion in ('dry_run','preview'):
 for status in (False,True,None,'error'):
  state.update(probe=status,probe_calls=0,power_calls=0);w=g['_blocked_wizard'](OSError());setattr(w,exclusion,True)
  actual=w._live_pinned_engine_busy();rows.append({'case':exclusion+'-'+str(status),'actual':[actual,state['probe_calls']],'expected':[False,0],'match':actual is False and state['probe_calls']==0})
record={'phase':phase,'cases':len(rows),'matching':sum(x['match'] for x in rows),'rows':rows,'bindings':bound,'scope':'Exact startup/controller/app guard AST; all imports, process queries and power calls fake. No real shutdown, signals, threads, services or device operations.'}
with (out/f'power-{phase}-results.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2);f.write('\n')
if phase=='before':
 with (out/'wizard-before.py').open('xb') as f:f.write((root/'src/beamo_wipe/wizard.py').read_bytes())
print(json.dumps({k:v for k,v in record.items() if k not in ('rows','bindings')},indent=2));print(json.dumps([x for x in rows if not x['match']],indent=2));raise SystemExit(0 if all(x['match'] for x in rows) else 1)
