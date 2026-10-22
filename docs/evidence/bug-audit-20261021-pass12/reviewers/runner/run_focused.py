from pathlib import Path
import datetime, hashlib, json, os, subprocess, time, xml.etree.ElementTree as ET

root = Path(__file__).parent
paths = json.loads(Path('/workspace/beamo-tools/audit-pass11-20261021/runner/selected-tests.json').read_text())
(root / 'selected-tests.json').write_text(json.dumps(paths, indent=2) + '\n')
hashes = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}
command = ['python3', '-m', 'pytest', '-q', '-W', 'error', '--junitxml=' + str(root / 'focused.xml'), *paths]
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
start = time.monotonic()
with (root / 'focused.log').open('wb') as stream:
    process = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, umask=0o022)
cases = list(ET.parse(root / 'focused.xml').iter('testcase'))
ids = [case.attrib['classname'] + '::' + case.attrib['name'] for case in cases]
summary = dict(command=command, started_utc=started, elapsed_seconds=round(time.monotonic()-start, 2),
               exit_code=process.returncode, cases=len(cases), unique_ids=len(set(ids)),
               failures=sum(case.find('failure') is not None for case in cases),
               errors=sum(case.find('error') is not None for case in cases),
               skips=[case.attrib for case in cases if case.find('skipped') is not None],
               child_umask='022', private_72dpi_x11=True,
               test_sha256=hashes, tests_byte_identical=all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p,h in hashes.items()))
(root / 'focused-nodeids.json').write_text(json.dumps(ids, indent=2) + '\n')
(root / 'focused.status.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ('command', 'test_sha256')}, indent=2))
raise SystemExit(process.returncode)
