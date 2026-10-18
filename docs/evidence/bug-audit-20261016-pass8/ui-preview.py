import os,subprocess,time
from PIL import ImageGrab
proc=subprocess.Popen(['./preview'],env={**os.environ,'BEAMO_WIPE_PREVIEW_PYTHON':'/tmp/beamo-wipe-audit-python/bin/python'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
try:
 time.sleep(5)
 assert proc.poll() is None,'preview exited early'
 ImageGrab.grab().save('/tmp/beamo-pass8-ui-preview.png')
 print('Actual ./preview screenshot captured on private72DPI Xvfb; PID',proc.pid)
finally:
 proc.terminate()
 try:output,_=proc.communicate(timeout=5)
 except subprocess.TimeoutExpired:
  proc.kill();output,_=proc.communicate(timeout=5)
 print('Owned preview child retired,returncode',proc.returncode)
 print(output)
