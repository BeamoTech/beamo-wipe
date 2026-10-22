"""A short Error Summary supplied by a 36-byte ATA model is not native proof."""
import pytest
from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.nwipe_runner import NwipeRunner, NWIPE_COMPLETION_LOG_BYTES, completion_for_method
from beamo_wipe.engine_checks import evaluate_engine_checks

STAMP='[2026/10/19 04:00:00] info: '
STATUS='********************************* Drive Status *********************************\n'
ROW='      sda | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n'
ERRORS='******************************** Error Summary *********************************\n'
PADDING=('p'*65535+'\n')*18

def io_status(log):
 return {c.id:c.status for c in evaluate_engine_checks(log,'/dev/sda')}['io_media']

@pytest.mark.parametrize('method',tuple(MethodId))
@pytest.mark.parametrize('large',(False,True))
@pytest.mark.parametrize('column',(0,1,2))
def test_model_summary_is_ambiguous(tmp_path,method,large,column):
 counts=['0','0','0']; counts[column]='1'
 model='X\nError Summary\n sda | '+' | '.join(counts)+'\n***'
 assert len(model.encode('ascii')) <=40
 raw=STAMP+'/dev/sda, ATA, '+model+', serial FAKE\n'+(PADDING if large else '')+STATUS+ROW
 if large:
  p=tmp_path/'fake.log'; p.write_text(raw)
  class Exited:
   returncode=0
   def poll(self):return 0
  r=NwipeRunner(); r._proc=Exited()
  req=WipeRequest('/dev/sda',method,'/dev/sr0',str(p)); r._active_request=req
  result=r.poll(req)
  assert not result.ok and result.reason=='indeterminate',result
  assessed=r._assessment_log_text
 else:
  result=completion_for_method(0,raw,'/dev/sda',method)
  assert not result[0] and result[2]=='indeterminate',result
  assessed=raw
 assert io_status(assessed)=='unavailable'

@pytest.mark.parametrize('method',tuple(MethodId))
@pytest.mark.parametrize('errors',(False,True))
def test_native_and_legacy_summary_controls(method,errors):
 counts='1 | 0 | 0' if errors else '0 | 0 | 0'
 native=STAMP+'Ordinary record\n'+ERRORS+' sda | '+counts+'\n***\n'+STATUS+ROW
 assert completion_for_method(0,native,'/dev/sda',method)[2]==('engine_failed' if errors else 'completed')
 assert io_status(native)==('fail' if errors else 'pass')
 if errors:
  legacy='Error Summary\n sda | '+counts+'\n***\n'+STATUS+ROW
  assert completion_for_method(0,legacy,'/dev/sda',method)[2]=='engine_failed'
  assert io_status(legacy)=='fail'
