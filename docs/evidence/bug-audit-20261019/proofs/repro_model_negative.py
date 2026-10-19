from beamo_wipe.models import MethodId
from beamo_wipe.nwipe_runner import completion_for_method

STAMP = '[2026/10/19 00:30:00]    info: '
HEADER = '********************************* Drive Status *********************************\n'
ROW = '      sda | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n'
for payload in ('Nwipe was aborted by the user', '/dev/sda: >>> FAILURE! <<<', "Verification mismatch on '/dev/sda'"):
    model = 'X\n' + payload
    assert len(model.encode()) <= 40
    fake = STAMP + '/dev/sda, ATA, ' + model + ', serial FAKE\n' + HEADER + ROW
    real = STAMP + '/dev/sda, ATA, ordinary model, serial FAKE\n' + STAMP + payload + '\n' + HEADER + ROW
    clean = STAMP + '/dev/sda, ATA, ordinary model, serial FAKE\n' + HEADER + ROW
    print(repr(payload), 'model_bytes=', len(model.encode()), 'forged=', completion_for_method(0, fake, '/dev/sda', MethodId.EVERYDAY), 'authentic=', completion_for_method(0, real, '/dev/sda', MethodId.EVERYDAY), 'clean=', completion_for_method(0, clean, '/dev/sda', MethodId.EVERYDAY))
