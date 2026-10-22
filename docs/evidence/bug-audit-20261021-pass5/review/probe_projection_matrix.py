"""Seeded fake-log comparison at terminal scan/projection boundaries."""
from pathlib import Path
import json
import random
import tempfile

from beamo_wipe import nwipe_runner as module
from beamo_wipe.engine_checks import check_payloads
from beamo_wipe.models import MethodId

root = Path(__file__).resolve().parent
randomizer = random.Random(2026102105)
stamp = '[2026/10/21 01:00:00] info: '
blocks = [
    stamp + 'No hidden sectors on /dev/sda\n',
    stamp + 'HIDDEN SECTORS INDETERMINATE! on /dev/sda\n',
    stamp + "Verification mismatch on '/dev/sda'\n",
    stamp + '/dev/sda: >>> FAILURE! <<<\n',
    stamp + '/dev/sdb: >>> FAILURE! <<<\n',
    stamp + '/dev/sda is reported as IN USE (it could be mounted)\n',
    module.NWIPE_DRIVE_STATUS_HEADER + '\n sda | Erased | 12MB/s | 00:01:00 | FAKE/DISK\n',
    module.NWIPE_DRIVE_STATUS_HEADER + '\n! sda |-FAILED-| 12MB/s | 00:01:00 | FAKE/DISK\n',
    module.NWIPE_ERROR_SUMMARY_HEADER + '\n sda | 0 | 0 | 0\n',
    module.NWIPE_ERROR_SUMMARY_HEADER + '\n! sda | 1 | 0 | 0\n',
    module.NWIPE_ERROR_SUMMARY_HEADER + '\n sda | invalid | 0 | 0\n',
    '******************************* Erasure Summary ********************************\n sda | 1 | 2 | 50.00%\n',
    '******************************* Erasure Summary ********************************\n sda | 2 | 2 | 100.00%\n',
    '********************************************************************************\n',
    stamp + '********************************************************************************\n',
    stamp + '/dev/sda: 100.00%, round 1 of 1, pass 1 of 1, eta 00:00:00, [verifying]\n',
    stamp + '/dev/sda: 100.00%, round 1 of 1, pass 3 of 3, eta 00:00:00, [verifying]\n',
    stamp + '/dev/sda: 100.00%, round 1 of 1, pass 1 of 1, eta 00:00:00, [writing]\n',
    stamp + '/dev/sda: 50.00%, round 1 of 1, pass 1 of 1, eta 00:00:10, [retrying]\n',
    stamp + '/dev/sda: 0.01%, round 1 of 1, pass 1 of 1, eta 00:00:10, [writing]\n',
    stamp + 'unrelated harmless text\n',
    stamp + '/dev/sdb selected\n',
]
differences = []
case_count = 2000
with tempfile.TemporaryDirectory(prefix='pass5-log-matrix-') as temp:
    path = Path(temp) / 'ordinary.log'
    runner = module.NwipeRunner()
    for case in range(case_count):
        chosen = randomizer.choices(blocks, k=randomizer.randrange(1, 9))
        text = stamp + 'Program options are set as follows\n' + ''.join(chosen)
        path.write_text(text)
        projected = runner._scan_completion_log(str(path), '/dev/sda', module._log_signature(path.stat()))
        assert projected is not None
        changes = []
        for method in MethodId:
            full = module.completion_for_method(0, text, '/dev/sda', method)
            compact = module.completion_for_method(0, projected, '/dev/sda', method)
            if full != compact:
                changes.append({'method':method.value, 'full':full, 'projected':compact})
        full_checks, compact_checks = check_payloads(text, '/dev/sda'), check_payloads(projected, '/dev/sda')
        if full_checks != compact_checks:
            changes.append({'full_checks':full_checks, 'projected_checks':compact_checks})
        if changes:
            differences.append({'case':case, 'text':text, 'projected':projected, 'differences':changes})
record = {'seed':2026102105,'fake_logs':case_count,'methods_per_log':3,
          'differences':differences,'actual_native_actions':False}
(root/'projection-matrix.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'fake_logs':case_count,'methods_per_log':3,'differences':len(differences)}))
assert not differences
