import contextlib
import importlib.util
import io
import json
from pathlib import Path
from unittest.mock import patch
root=Path('/workspace/beamo-wipe')
spec=importlib.util.spec_from_file_location('beamo_pass12_dev',root/'dev.py')
dev=importlib.util.module_from_spec(spec)
spec.loader.exec_module(dev)
cases={
 'valid': ('{"version":[3,12,0],"modules":{"venv":true,"pip":true}}', 0),
 'wrong-type': ('{"version":"x","modules":{}}', 2),
 'deep-json': ('['*20000 + ']'*20000, 2),
 'deep-modules': ('{"version":[3,12,0],"modules":'+'['*20000+']'*20000+'}', 2),
}
results=[]
for name,(payload,expected) in cases.items():
 stream=io.StringIO()
 with patch.object(dev,'live_environment',return_value=False), patch.object(dev,'doctor_probe',return_value=(payload,None)), patch.object(dev.shutil,'which',return_value='/fake/git'), contextlib.redirect_stdout(stream):
  try:
   status=dev.doctor()
   parsed=json.loads(stream.getvalue())
   results.append({'name':name,'expected_status':expected,'status':status,'structured':isinstance(parsed,dict),'pass':status==expected})
  except BaseException as exc:
   results.append({'name':name,'expected_status':expected,'exception':type(exc).__name__,'stdout':stream.getvalue(),'pass':False})
print(json.dumps({'results':results},indent=2))
raise SystemExit(0 if all(row['pass'] for row in results) else 1)
