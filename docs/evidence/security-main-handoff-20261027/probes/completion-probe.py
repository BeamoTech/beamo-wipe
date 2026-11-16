"""Exact-source parser/scanner models. Never import application or open devices."""
from pathlib import Path
import ast,dataclasses,enum,hashlib,io,json,math,posixpath,re,stat,sys,types
out=Path(__import__('os').environ['BEAMO_SECURITY_OUTPUT']);root=Path(__import__('os').environ['BEAMO_SECURITY_ROOT'])
phase=sys.argv[1];assert phase in {'before','before-corrected','after'}
def compiled(nodes,path,env):
 future=ast.parse('from __future__ import annotations').body
 exec(compile(ast.fix_missing_locations(ast.Module(body=future+nodes,type_ignores=[])),str(path),'exec'),env)
mod=types.ModuleType('security_review_method_specs');sys.modules[mod.__name__]=mod;env=mod.__dict__;env.update(Enum=enum.Enum,dataclass=dataclasses.dataclass)
models=root/'src/beamo_wipe/models.py';methods=root/'src/beamo_wipe/methods.py';source=root/'src/beamo_wipe/nwipe_runner.py'
compiled([n for n in ast.parse(models.read_bytes()).body if isinstance(n,ast.ClassDef) and n.name=='MethodId'],models,env)
compiled([n for n in ast.parse(methods.read_bytes()).body if isinstance(n,ast.ClassDef) and n.name=='NwipeMethodSpec' or isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='METHODS' for x in n.targets)],methods,env)
data=source.read_bytes();tree=ast.parse(data)
first=next(n.lineno for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='target_skipped_busy')
last=next(n.lineno for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='NwipeRunner')
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and first<=n.lineno<last or isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and (x.id.startswith('NWIPE_') or x.id=='_LOG_DEVICE_RE') for x in n.targets)]
fake_os=types.SimpleNamespace(path=posixpath)
env.update(re=re,math=math,os=fake_os,CLEAN_SUBPROCESS_ENV={},NWIPE_PINNED_VERSION='0.42')
compiled(nodes,source,env)
runner=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='NwipeRunner')
scan=next(n for n in runner.body if isinstance(n,ast.FunctionDef) and n.name=='_scan_completion_log')
compiled([scan],source,env)
def project(log):
 raw=log.encode();closed=[];snap=types.SimpleNamespace(st_mode=stat.S_IFREG|0o600,st_uid=0,st_dev=1,st_ino=2,st_size=len(raw),st_mtime_ns=3,st_ctime_ns=4)
 class Stream(io.BytesIO):
  def fileno(self):return 17
  def __exit__(self,*args):closed.append('wrapper');return super().__exit__(*args)
 env.update(stat=stat,_try_log_diag=lambda *a:None)
 fake_os.open=lambda *a:17;fake_os.close=closed.append;fake_os.fdopen=lambda *a,**kw:Stream(raw);fake_os.fstat=lambda *a:snap;fake_os.getuid=lambda:0
 fake_os.O_RDONLY=0;fake_os.O_NOFOLLOW=1;fake_os.O_NONBLOCK=2
 text=env['_scan_completion_log'](types.SimpleNamespace(_active_log_identity=None),'/fixture/log','/dev/sda',env['_log_signature'](snap))
 assert closed==['wrapper',17] and text is not None
 return text
rows=[]
def check(case,method,log,expected,large=False):
 text=project(log) if large else log
 result=env['completion_for_method'](0,text,'/dev/sda',method)
 rows.append({'case':case,'method':method.value,'large_projection':large,'expected':expected,'actual':result[0],'reason':result[2],'match':result[0] is expected})
for method,spec in env['METHODS'].items():
 stage='writing' if spec.verify=='off' else 'verifying';passes=spec.overwrite_passes
 good=f'/dev/sda: 100.00%, round 1 of 1, pass {passes} of {passes}, eta 00:00:00, [{stage}]\n'
 damaged='/dev/sda: 010.00%, round 1 of 1, pass 1 of\n'
 padding=('diagnostic '+'.'*100+'\n')*10000
 check('later-damaged',method,good+damaged,False)
 check('later-damaged-projected',method,good+damaged+padding,False,True)
 check('valid-control',method,good,True)
 check('other-device-control',method,good+damaged.replace('/dev/sda','/dev/sdb'),True)
 erased=env['NWIPE_DRIVE_STATUS_HEADER']+'\n     sda | Erased | 100 MB/s | 00:01:00 | fixture\n'
 check('independent-erased-control',method,good+damaged+erased,True)
 check('decimal-overflow',method,good.replace('100.00%','100.00000000000000001%'),False)
 check('later-decimal-overflow',method,good+good.replace('100.00%','100.00000000000000001%'),False)
for label,skip in [('busy','/dev/sda is reported as IN USE\n'),('open',"Unable to open device '/dev/sda'.\n"),('geometry',"/dev/sda: No sane device geometry\n")]:
 log=skip+'/dev/sda: 010.00%, round 1 of 1, pass 1 of\n'
 actual=env['evaluate_nwipe_outcome'](0,log,'/dev/sda')[2]
 rows.append({'case':'damaged-activity-'+label,'expected':'indeterminate','actual':actual,'match':actual=='indeterminate'})
record={'phase':phase,'cases':len(rows),'matching':sum(x['match'] for x in rows),'rows':rows,'source':{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()},'scope':'Exact parser/scanner AST, actual selected method specs, lexical POSIX paths, synthetic metadata and BytesIO only. No product imports, device/process operations or native acceptance.','bindings':[{'name':getattr(n,'name',','.join(t.id for t in n.targets if isinstance(t,ast.Name)) if isinstance(n,ast.Assign) else '?'),'line':n.lineno,'end':n.end_lineno,'ast_sha256':hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest()} for n in nodes+[scan]]}
with (out/f'completion-{phase}-results.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2);f.write('\n')
if phase=='before':
 with (out/'nwipe_runner-before.py').open('xb') as f:f.write(data)
print(json.dumps({k:v for k,v in record.items() if k not in ('rows','bindings')},indent=2))
print(json.dumps([x for x in rows if not x['match']],indent=2))
raise SystemExit(0 if all(x['match'] for x in rows) else 1)
