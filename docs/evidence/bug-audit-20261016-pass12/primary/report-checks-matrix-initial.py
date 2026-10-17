"""Fake process→runner→owner/sharing evidence across three methods/languages."""
import hashlib
import json
from pathlib import Path
import tempfile

from beamo_wipe import lang
from beamo_wipe.demo import discovery_for_scenario
from beamo_wipe.engine_checks import check_payloads
from beamo_wipe.evidence import build_evidence
from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.outcomes import present_evidence
from beamo_wipe.privacy import make_sharing_copy
from beamo_wipe.result_summary import build_result_summary, build_result_report_html
import beamo_wipe.nwipe_runner as module

module._try_log_diag = lambda *a, **k: None
class Exited:
    def poll(self): return 0

discovery = discovery_for_scenario('happy')
disk = discovery.selectable[0]
target = module.nwipe_status_device_field(disk.path).strip()
stamp = '[2026/10/16 12:00:00] info: '
none = stamp + 'No hidden sectors on ' + disk.path + '\n'
header = '******************************** Error Summary *********************************\n'
close = '********************************************************************************\n'
status = module.NWIPE_DRIVE_STATUS_HEADER + '\n' + module.nwipe_status_device_field(disk.path) + ' | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n'
cases = {
    'write-error': ('1 | 0 | 0', 'engine_failed', 'fail'),
    'read-error': ('0 | 1 | 0', 'engine_failed', 'fail'),
    'verify-error': ('0 | 0 | 1', 'engine_failed', 'fail'),
    'unknown-count': ('unknown | 0 | 0', 'indeterminate', 'unavailable'),
    'clean': ('0 | 0 | 0', 'completed', 'pass'),
}
rows = []
with tempfile.TemporaryDirectory(prefix='beamo-pass12-report-checks-') as directory:
    for locale in ('en', 'fr', 'de'):
        lang.set_language(locale)
        for method in MethodId:
            for name, (counts, reason, expected) in cases.items():
                for large in (False, True):
                    records = stamp + '! ' + target + ' | ' + counts + '\n' + stamp + close
                    padding = ('x' * 65535 + '\n') * 17 if large else ''
                    text = none + stamp + header + records + padding + status
                    log = Path(directory) / 'fake.log'
                    log.write_bytes(text.encode())
                    request = WipeRequest(disk.path, method, discovery.boot.path, str(log))
                    runner = module.NwipeRunner()
                    runner._proc = Exited()
                    result = runner.poll(request)
                    evidence = build_evidence(disk=disk, discovery=discovery, method=method, request=request, result=result, started_at_wall=None, ended_at_wall=None, started_mono=0, ended_mono=1, argv=[], log_text=runner._log_tail, assessment_log_text=runner._assessment_log_text, language=locale)
                    checks = check_payloads(text, disk.path, disk)
                    assert checks[1]['status'] == expected
                    assert evidence['checks'] == checks
                    assert result.reason == reason
                    assert result.ok is (reason == 'completed')
                    assert present_evidence(evidence).success is result.ok
                    assert evidence['verification']['verified'] is (result.ok and method != MethodId.QUICK_ZERO)
                    assert evidence['log_checksum_sha256'] == hashlib.sha256(runner._log_tail.encode()).hexdigest()
                    assert log.read_bytes() == text.encode()
                    assert build_result_summary(evidence)
                    assert build_result_report_html(evidence)
                    shared = make_sharing_copy(evidence)
                    assert present_evidence(shared).success is result.ok
                    rows.append({'language': locale, 'method': method.value, 'case': name, 'large': large, 'io_media': expected, 'reason': result.reason, 'outcome': evidence['outcome'], 'checks_and_log_bytes_match': True})
assert len(rows) == 90
print(json.dumps({'cases': len(rows), 'rows': rows}, indent=2))
