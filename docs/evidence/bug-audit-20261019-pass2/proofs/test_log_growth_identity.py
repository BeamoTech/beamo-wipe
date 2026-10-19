"""Growth between end-position capture and fstat cannot authenticate a prefix."""
import os
from unittest.mock import patch
import pytest
from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.nwipe_runner import NwipeRunner, NWIPE_COMPLETION_LOG_BYTES

COMPLETE=(
 '********************************* Drive Status *********************************\n'
 '      sda | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n'
).encode()
FAILURE=b'[2026/10/19 04:00:00] error: /dev/sda: >>> FAILURE! <<<\n'

class Exited:
 returncode=0
 def poll(self):return 0

@pytest.mark.parametrize('grow',(False,True))
def test_growth_before_identity_capture_cannot_hide_failure(tmp_path,grow):
 p=tmp_path/'fake.log'
 p.write_bytes(COMPLETE+b'p'*(NWIPE_COMPLETION_LOG_BYTES-len(COMPLETE)-1)+b'\n')
 r=NwipeRunner(); r._proc=Exited()
 req=WipeRequest('/dev/sda',MethodId.EVERYDAY,'/dev/sr0',str(p)); r._active_request=req
 original=os.fdopen
 calls=0
 class Growing:
  def __init__(self,stream):self.stream=stream
  def __enter__(self):self.stream.__enter__();return self
  def __exit__(self,*args):return self.stream.__exit__(*args)
  def fileno(self):return self.stream.fileno()
  def seek(self,*args):return self.stream.seek(*args)
  def read(self,*args):return self.stream.read(*args)
  def readline(self,*args):return self.stream.readline(*args)
  def tell(self):
   nonlocal calls
   n=self.stream.tell(); calls+=1
   # First call is the progress tail; second is terminal evidence capture.
   if grow and calls==2:
    with p.open('ab') as writer:writer.write(FAILURE)
   return n
 with patch.object(os,'fdopen',lambda *a,**kw:Growing(original(*a,**kw))):
  result=r.poll(req)
 assert result is not None
 if grow:
  assert not result.ok, (result, 'full fake log ends with explicit target failure')
 else:
  assert result.ok
