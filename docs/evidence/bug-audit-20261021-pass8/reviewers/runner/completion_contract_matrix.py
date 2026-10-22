"""Fresh PASS8 completion laws: exact method/counters/phase/percentage/newline."""
from pathlib import Path
import hashlib,itertools,json,os
from unittest.mock import patch
from beamo_wipe import nwipe_runner as m
from beamo_wipe.models import MethodId
from beamo_wipe.methods import METHODS
root=Path(__file__).parent
prefixes=('', '[2026/10/21 12:34:56] info: ')
percentages=('0.00','50.00','99.99','100','100.00','100.000000000000000000001','101.00','-1.00','NaN')
phases=('writing','verifying','retrying')
endings=('\n','\r\n','')
# Named configurations, independently expected to match/contradict the selected plan.
configs=('correct','wrong-pass-total','not-final-pass','wrong-round-total','zero-pass','missing-pass')
failures=[];n=0;positive=0
realpath=os.path.realpath
native=[]
def fake_realpath(path,*a,**kw):
 if os.fsdecode(path).startswith('/dev/'):return os.fspath(path)
 return realpath(path,*a,**kw)
def forbidden(*a,**kw):native.append(True);raise AssertionError('Native callback forbidden')
with patch.object(os.path,'realpath',fake_realpath),patch.object(m.subprocess,'run',forbidden),patch.object(m.subprocess,'Popen',forbidden),patch.object(os,'kill',forbidden):
 for method,prefix,pct,phase,ending,config,code in itertools.product(MethodId,prefixes,percentages,phases,endings,configs,(0,1)):
  passes=METHODS[method].overwrite_passes
  round_i=round_n=1;pass_i=pass_n=passes
  if config=='wrong-pass-total':pass_i=pass_n=passes+1
  elif config=='not-final-pass':pass_i=0 if passes==1 else passes-1
  elif config=='wrong-round-total':round_i=round_n=2
  elif config=='zero-pass':pass_i=0
  counters=f', pass {pass_i} of {pass_n}' if config!='missing-pass' else ''
  text=f'{prefix}/dev/FAKE-DATA: {pct}%, round {round_i} of {round_n}{counters}, eta 00:00:00, [{phase}]{ending}'
  expected=(code==0 and config=='correct' and pct in {'100','100.00'} and ending!='' and phase==('writing'if method is MethodId.QUICK_ZERO else'verifying'))
  actual=m.completion_for_method(code,text,'/dev/FAKE-DATA',method)
  n+=1;positive+=expected
  if actual[0]!=expected:failures.append({'case':n,'method':method.value,'text':text,'code':code,'expected_completed':expected,'actual':actual})
result={'cases':n,'expected_completed_controls':positive,'expected_refusal_controls':n-positive,'failure_count':len(failures),'failures':failures[:20],'native_callbacks':len(native),'source_sha256':{str(Path(m.__file__).relative_to(Path('/workspace/beamo-wipe'))):hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()},'scope':'Pure completion law matrix, not native acceptance; separate from pytest totals'}
(root/'completion-contract-matrix.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='failures'}));raise SystemExit(bool(failures))
