"""A hidden-capacity PASS requires the complete pinned positive record."""
from dataclasses import replace
import hashlib
import importlib

import pytest

from beamo_wipe.demo import discovery_for_scenario
from beamo_wipe.engine_checks import check_payloads
from beamo_wipe.evidence import build_evidence
from beamo_wipe.models import MethodId, WipeRequest

runner_module = importlib.import_module('beamo_wipe.nwipe_runner')
STAMP = '[2026/10/16 12:00:00] info: '
DEVICES = ['/dev/sda', '/dev/nvme0n1', '/dev/mmcblk0']
SUFFIXES = ['', ' ', '\t', '/part', '/../../sdb', ' uncertain', ' (indeterminate)',
            ': unknown', '\x00', '\u2028foreign', '/part mentions /dev/sda',
            ' -- HIDDEN SECTORS INDETERMINATE!', ', except an unknown HPA',
            ' ; hdparm reports invalid output, sector information may be invalid']


@pytest.mark.parametrize('device', DEVICES)
@pytest.mark.parametrize('suffix', SUFFIXES)
def test_hidden_positive_requires_complete_target_record(device, suffix):
    text = STAMP + 'No hidden sectors on ' + device + suffix + '\n'
    check = check_payloads(text, device)[0]
    assert check['status'] == ('pass' if suffix in {'', ' ', '\t'} else 'unavailable')
    if check['status'] == 'pass':
        assert check['provenance']['engine_version'] == '0.42'


@pytest.mark.parametrize('device', DEVICES)
@pytest.mark.parametrize('placement', ['only', 'before', 'after', 'foreign'])
def test_separate_negative_record_keeps_conservative_precedence(device, placement):
    positive = STAMP + 'No hidden sectors on ' + device + '\n'
    negative_device = '/dev/sdz' if placement == 'foreign' else device
    negative = STAMP + 'HIDDEN SECTORS INDETERMINATE! on ' + negative_device + ', Some USB adapters & memory sticks do not support ATA pass through\n'
    text = negative if placement == 'only' else negative + positive if placement == 'before' else positive + negative
    assert check_payloads(text, device)[0]['status'] == ('pass' if placement == 'foreign' else 'unavailable')


@pytest.mark.parametrize('device', DEVICES)
@pytest.mark.parametrize('method', list(MethodId))
@pytest.mark.parametrize('large', [False, True])
def test_malformed_positive_is_unavailable_in_runner_evidence(monkeypatch, tmp_path, device, method, large):
    def forbidden(*_a, **_k):
        raise AssertionError('Native process/inventory reached')
    for name in ('subprocess.run', 'subprocess.Popen',
                 'beamo_wipe.nwipe_runner.pinned_nwipe_already_running',
                 'beamo_wipe.nwipe_runner._recheck_identity_under_lock'):
        monkeypatch.setattr(name, forbidden)
    monkeypatch.setattr(runner_module, '_try_log_diag', lambda *_a, **_k: None)
    monkeypatch.setattr('beamo_wipe.evidence.evidence_identity', lambda: {
        'source_commit': 'a' * 40, 'build_id': 'pass15', 'build_status': 'development', 'source_dirty': True,
    })
    discovery = discovery_for_scenario('happy')
    disk = replace(discovery.selectable[0], path=device, name=device.rsplit('/', 1)[-1])
    discovery = replace(discovery, disks=(discovery.boot, disk), selectable=(disk,))
    positive = STAMP + 'No hidden sectors on ' + device + ' -- HIDDEN SECTORS INDETERMINATE!\n'
    padding = ('x' * 65535 + '\n') * 17 if large else ''
    text = positive + padding + runner_module.NWIPE_DRIVE_STATUS_HEADER + '\n' + runner_module.nwipe_status_device_field(device) + ' | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n'
    log = tmp_path / 'fake.log'
    raw = text.encode()
    log.write_bytes(raw)

    class Exited:
        def poll(self):
            return 0

    runner = runner_module.NwipeRunner()
    runner._proc = Exited()
    request = WipeRequest(device, method, discovery.boot.path, str(log))
    result = runner.poll(request)
    assert result is not None and result.ok
    evidence = build_evidence(disk=disk, discovery=discovery, method=method, request=request,
        result=result, started_at_wall=None, ended_at_wall=None, started_mono=0, ended_mono=1,
        argv=[], log_text=runner._log_tail, assessment_log_text=runner._assessment_log_text)
    assert evidence['checks'][0]['status'] == 'unavailable'
    assert evidence['checks'] == check_payloads(text, device, disk)
    assert evidence['verification']['verified'] is (method != MethodId.QUICK_ZERO)
    assert evidence['log_checksum_sha256'] == hashlib.sha256(runner._log_tail.encode()).hexdigest()
    assert log.read_bytes() == raw
