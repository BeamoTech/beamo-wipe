"""Seeded fake-log comparison of full parsers and bounded terminal projections."""
from pathlib import Path
import hashlib
import json
import random
import tempfile

from beamo_wipe import nwipe_runner as runner
from beamo_wipe.engine_checks import check_payloads
from beamo_wipe.models import MethodId

root = Path(__file__).resolve().parent
repo = Path('/workspace/beamo-wipe')
source = {name: hashlib.sha256((repo / name).read_bytes()).hexdigest() for name in
          ('src/beamo_wipe/nwipe_runner.py', 'src/beamo_wipe/engine_checks.py')}
runner._try_log_diag = lambda *_args: None
stamp = '[2026/10/19 06:00:00] info: '
close = '*' * 80
corpus = [
    stamp + 'Options initialized',
    stamp + 'No hidden sectors on /dev/sda',
    stamp + '/dev/sda: >>> FAILURE! <<<',
    stamp + "Verification mismatch on '/dev/sda'",
    stamp + "Unable to open device '/dev/sda'.",
    stamp + '/dev/sda is reported as IN USE',
    stamp + 'Nwipe was aborted by the user',
    stamp + 'No sane device geometry for /dev/sda',
    runner.NWIPE_DRIVE_STATUS_HEADER,
    ' sda | Erased | 120MB/s | 00:01:00 | FAKE/DISK',
    ' sda |-FAILED-| 120MB/s | 00:01:00 | FAKE/DISK',
    ' sdb |-FAILED-| 120MB/s | 00:01:00 | FAKE/DISK',
    runner.NWIPE_ERROR_SUMMARY_HEADER,
    'Error Summary',
    stamp + runner.NWIPE_ERROR_SUMMARY_HEADER,
    ' sda | 0 | 0 | 0',
    ' sda | 1 | 0 | 0',
    ' sda | 0 | 1 | 0',
    ' sda | 0 | 0 | 1',
    ' sda | invalid | 0 | 0',
    stamp + '! sda | 0 | 0 | 1',
    ' sdb | 0 | 0 | 0',
    '******************************* Erasure Summary ********************************',
    ' sda | 2 | 2 | 100.00%',
    ' sda | 1 | 2 | 50.00%',
    ' sda | invalid | 2 | 50.00%',
    close, stamp + close, 'info: ' + close,
    'Model with embedded phrase and random text', '', ' ',
]
for passes in (1, 3):
    for phase in ('writing', 'verifying', 'retrying', 'syncing', 'bogus'):
        for value in ('25.00', '100.00', '99.99999999999999999'):
            corpus.append(f'/dev/sda: {value}%, round 1 of 1, pass {passes} of {passes}, eta 00:00:10, [{phase}]')
corpus += ['/dev/sda: 99.00%, round 1 of 1, pass 1 of 3, eta 00:00:10, [writing]',
           '/dev/sda: 100.00%, round 1 of 1, pass 1 of 1, eta 00:00:00, [writing] trailing',
           '/dev/sda: 100.00%, round 1 of 1, pass 1 of 1, eta 00:00:00, <[verifying]>']
rng = random.Random(2026101904)
differences = []
cases = 5000
with tempfile.TemporaryDirectory(prefix='projection-pass4-', dir=root) as tmp:
    logfile = Path(tmp) / 'fake.log'
    for case in range(cases):
        chosen = rng.choices(corpus, k=rng.randint(1, 24))
        if case % 3 == 0:
            chosen.extend((runner.NWIPE_DRIVE_STATUS_HEADER,
                           ' sda | Erased | 120MB/s | 00:01:00 | FAKE/DISK', close))
        text = '\n'.join(chosen) + '\n'
        logfile.write_bytes(text.encode())
        projected = runner.NwipeRunner()._scan_completion_log(str(logfile), '/dev/sda', runner._log_signature(logfile.stat()))
        assert projected is not None
        full_checks = check_payloads(text, '/dev/sda')
        projected_checks = check_payloads(projected, '/dev/sda')
        for method in MethodId:
            if (runner.completion_for_method(0, text, '/dev/sda', method)
                    != runner.completion_for_method(0, projected, '/dev/sda', method)
                    or full_checks != projected_checks):
                differences.append({'case': case, 'method': method.value,
                                    'full': text, 'projection': projected,
                                    'full_checks': full_checks, 'projected_checks': projected_checks})
                break
assert all(hashlib.sha256((repo / name).read_bytes()).hexdigest() == h for name, h in source.items())
record = {'seed': 2026101904, 'cases': cases, 'methods_per_case': 3,
          'source_sha256': source, 'mismatches': len(differences), 'examples': differences[:4],
          'fake_files_only': True}
(root / 'projection-review.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({k: v for k, v in record.items() if k != 'examples'}))
assert not differences
