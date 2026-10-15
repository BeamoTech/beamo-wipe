import hashlib
import itertools
import json
from pathlib import Path
from beamo_wipe.methods import METHODS
from beamo_wipe.nwipe_runner import completion_for_method

status = '********************************* Drive Status *********************************\n      sda | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n'
percentages = ('0.00', '99.99', '99.99999999999999999999', '100', '100.00', '100.00000000000000000001', '101')
phases = ('writing', 'verifying', 'syncing', 'retrying', 'blanking', 'unknown', '')
cases = 0
for method, spec in METHODS.items():
    wanted_phase = 'writing' if spec.verify == 'off' else 'verifying'
    for pct, phase, wrong_round, wrong_pass, table in itertools.product(percentages, phases, (False, True), (False, True), (False, True)):
        rounds = 2 if wrong_round else 1
        passes = spec.overwrite_passes + wrong_pass
        line = f'/dev/sda: {pct}%, round {rounds} of {rounds}, pass {passes} of {passes}, eta 00:00:00, [{phase}]\n'
        valid_range = pct not in ('100.00000000000000000001', '101')
        if table:
            known_phase = phase in ('writing', 'verifying', 'syncing', 'retrying', 'blanking')
            expected = not (valid_range and known_phase and (wrong_round or wrong_pass))
        else:
            expected = pct in ('100', '100.00') and phase == wanted_phase and not wrong_round and not wrong_pass
        actual = completion_for_method(0, line + (status if table else ''), '/dev/sda', method)[0]
        assert actual == expected, (method, pct, phase, wrong_round, wrong_pass, table, actual, expected)
        cases += 1
source = Path('src/beamo_wipe/nwipe_runner.py')
print(json.dumps({'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'matrix_cases': cases, 'failures': 0}, indent=2))
