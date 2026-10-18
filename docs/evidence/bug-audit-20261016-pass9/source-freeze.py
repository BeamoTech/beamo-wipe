from pathlib import Path
import hashlib,json
files=sorted([*Path('src/beamo_wipe').rglob('*.py'),*Path('tests').glob('*.py'),*Path('developer_tests').glob('*.py')])
print(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},sort_keys=True,indent=2))
