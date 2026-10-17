"""Pure parser trace; fake log strings, no processes, inventory or device I/O."""
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd() / 'src'))
from beamo_wipe.engine_checks import check_payloads
from beamo_wipe import nwipe_runner

BASE = Path('/tmp/pass15-runner')
paths = ['/dev/sda', '/dev/nvme0n1', '/dev/mmcblk0']
stamp = '[2026/10/16 12:00:00] info: '
suffixes = ['', ' ', '\t', '/part', '/../../sdb', ' uncertain', ' (indeterminate)', ': unknown', '\x00', '\u2028foreign', '/part mentions /dev/sda', ' -- HIDDEN SECTORS INDETERMINATE!', ', except an unknown HPA', ' ; hdparm reports invalid output, sector information may be invalid']
rows = []
for device in paths:
    for suffix in suffixes:
        text = stamp + 'No hidden sectors on ' + device + suffix + '\n'
        full = check_payloads(text, device)[0]
        rows.append({'device': device, 'suffix': suffix, 'line': text, 'status': full['status'], 'detail': full['detail']})
for device in paths:
    positive = stamp + 'No hidden sectors on ' + device + '\n'
    negative = stamp + 'HIDDEN SECTORS INDETERMINATE! on ' + device + ', Some USB adapters & memory sticks do not support ATA pass through\n'
    foreign = stamp + 'HIDDEN SECTORS INDETERMINATE! on /dev/sdz, Some USB adapters & memory sticks do not support ATA pass through\n'
    for label, text in [('negative_only', negative), ('negative_before', negative + positive), ('negative_after', positive + negative), ('foreign_negative_after', positive + foreign)]:
        full = check_payloads(text, device)[0]
        rows.append({'device': device, 'suffix': label, 'line': text, 'status': full['status'], 'detail': full['detail']})
checks = {'source': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path('src/beamo_wipe/engine_checks.py'), Path('src/beamo_wipe/nwipe_runner.py')]}, 'rows': rows, 'native_effects': 0}
(BASE / 'hidden-record-probe.json').write_text(json.dumps(checks, indent=2) + '\n')
print(json.dumps({'cases': len(rows), 'results': {suffix: [r['status'] for r in rows if r['suffix'] == suffix] for suffix in suffixes}, 'native_effects': 0}))
