import os, subprocess, time
from PIL import ImageGrab
p=subprocess.Popen(['./preview'],env={**os.environ,'BEAMO_WIPE_PREVIEW_PYTHON':'/tmp/beamo-wipe-audit-python/bin/python','BEAMO_WIPE_NO_OPEN':'1'},stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
try:
 time.sleep(3)
 assert p.poll() is None, p.communicate()
 ImageGrab.grab().save('/tmp/beamo-pass7-surfaces-preview.png')
 print('Owned ./preview fake Tk process remained running; 72-DPI screenshot saved.')
finally:
 p.terminate()
 try: out,err=p.communicate(timeout=5)
 except subprocess.TimeoutExpired:
  p.kill();out,err=p.communicate(timeout=5)
 print('Owned fake preview teardown returncode',p.returncode)
 print(err)
