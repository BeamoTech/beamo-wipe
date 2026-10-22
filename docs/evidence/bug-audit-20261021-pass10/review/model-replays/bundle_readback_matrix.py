"""Fresh bundle readback, tampering, duplicate-allocation and retry matrix.

All output lives in owned temporary regular files/FIFOs. This exercises content
integrity and safe marker wording, not physical FAT32/remount acceptance.
"""
from pathlib import Path
import hashlib
import itertools
import json
import os
import sys
import tempfile

sys.path[:0] = ['/workspace/beamo-wipe/src', '/workspace/beamo-wipe/tests']
from pytest import MonkeyPatch
from beamo_wipe import app, diagnostic_report, discover, lang, support_export as export
from beamo_wipe.nwipe_runner import NwipeRunner
from beamo_wipe.safety import SafetyError
from test_result_presentations import CASES, case_evidence
from beamo_wipe.demo import make_demo_wizard


ROOT = Path(__file__).parent
metrics = {'contexts': 0, 'positive_bundles': 0, 'content_manifest_checks': 0,
           'duplicate_session_refusals': 0, 'tamper_refusals': 0,
           'restored_positive_rechecks': 0, 'extra_file_refusals': 0,
           'native_callbacks': 0, 'mismatches': []}
mutations = ['truncate', 'append', 'flip', 'remove', 'symlink', 'directory', 'fifo']
outcomes = [CASES[0], CASES[1], CASES[6]]


def forbidden(*args, **kwargs):
    metrics['native_callbacks'] += 1
    raise AssertionError('Native inventory, process, engine, mount or power forbidden')


def verify_refusal(folder, name, expected):
    try:
        export.verify_report_bundle(folder, name, expected)
    except (SafetyError, OSError):
        return
    raise AssertionError('Changed report bundle passed readback')


with MonkeyPatch.context() as patch, tempfile.TemporaryDirectory(prefix='beamo-pass10-readback-') as temporary:
    patch.setenv('BEAMO_WIPE_DRY_RUN', '1')
    patch.delenv('BEAMO_WIPE_LIVE', raising=False)
    for boundary in ['subprocess.run', 'subprocess.Popen', 'beamo_wipe.discover.run_lsblk',
                     'beamo_wipe.discover._run_findmnt', 'beamo_wipe.discover.read_cmdline',
                     'beamo_wipe.discover.read_mount_sources', 'beamo_wipe.support_export._run_command',
                     'beamo_wipe.support_export._ordinary_unmount', 'beamo_wipe.app._shutdown']:
        patch.setattr(boundary, forbidden)
    patch.setattr(NwipeRunner, 'start', forbidden)
    patch.setattr('beamo_wipe.diagnostics.emit_serial_marker', forbidden)
    original_realpath = os.path.realpath
    patch.setattr(os.path, 'realpath', lambda p, *a, **kw: os.fspath(p)
                  if os.fspath(p).startswith('/dev/') else original_realpath(p, *a, **kw))
    try:
        for language, private, index in itertools.product(['en', 'fr', 'de'], [False, True], range(4)):
            lang.set_language(language)
            metrics['contexts'] += 1
            mount = Path(temporary) / str(metrics['contexts'])
            mount.mkdir(mode=0o700)
            if index == 3:
                raw = diagnostic_report.create_report(
                    'boot_unidentified', make_demo_wizard().discovery,
                    ui='console', session_started=0,
                )
                log, status = b'', 'unavailable'
            else:
                _, payload, log_text = case_evidence(outcomes[index])
                raw = json.dumps(payload, sort_keys=True).encode()
                log, status = log_text.encode(), 'complete'
            name = 'report-' + format(metrics['contexts'], '024x')
            name, expected = export.write_report_bundle(
                mount, raw, log, status, session_name=name, privacy_reduced=private,
            )
            export.verify_report_bundle(mount, name, expected)
            metrics['positive_bundles'] += 1
            directory = mount / export.REPORTS_DIR / name
            marker = json.loads(expected['COMPLETE'])
            assert marker['manifest_scope'] == 'content_only'
            assert marker['safe_to_remove'] is False
            assert set(marker['files']) == set(expected) - {'COMPLETE'}
            assert all(hashlib.sha256(expected[file]).hexdigest() == digest
                       for file, digest in marker['files'].items())
            metrics['content_manifest_checks'] += 1
            assert ('SHARE.json' in expected) == (private and index != 3)
            assert ('REPORT.html' in expected) == (index != 3)
            try:
                export.write_report_bundle(mount, raw, log, status,
                                           session_name=name, privacy_reduced=private)
            except SafetyError:
                metrics['duplicate_session_refusals'] += 1
            else:
                raise AssertionError('Duplicate session allocation succeeded')
            export.verify_report_bundle(mount, name, expected)
            for filename, mutation in itertools.product(expected, mutations):
                path = directory / filename
                data = expected[filename]
                path.unlink()
                linked = None
                if mutation == 'truncate':
                    path.write_bytes(data[:-1])
                elif mutation == 'append':
                    path.write_bytes(data + b'x')
                elif mutation == 'flip':
                    assert data
                    path.write_bytes(bytes([data[0] ^ 1]) + data[1:])
                elif mutation == 'symlink':
                    linked = mount / 'owned-link-target'
                    linked.write_bytes(data)
                    path.symlink_to(linked)
                elif mutation == 'directory':
                    path.mkdir(mode=0o700)
                elif mutation == 'fifo':
                    os.mkfifo(path, 0o600)
                else:
                    assert mutation == 'remove'
                verify_refusal(mount, name, expected)
                metrics['tamper_refusals'] += 1
                if mutation == 'directory':
                    path.rmdir()
                elif path.exists() or path.is_symlink():
                    path.unlink()
                if linked is not None:
                    linked.unlink()
                path.write_bytes(data)
                path.chmod(0o600)
                export.verify_report_bundle(mount, name, expected)
                metrics['restored_positive_rechecks'] += 1
            extra = directory / 'unexpected.txt'
            extra.write_bytes(b'owned extra fixture')
            verify_refusal(mount, name, expected)
            metrics['extra_file_refusals'] += 1
            extra.unlink()
            export.verify_report_bundle(mount, name, expected)
    finally:
        lang.set_language('en')

assert metrics['contexts'] == metrics['positive_bundles'] == metrics['content_manifest_checks'] == 24
assert metrics['duplicate_session_refusals'] == metrics['extra_file_refusals'] == 24
assert metrics['tamper_refusals'] == metrics['restored_positive_rechecks'] > 1000
assert metrics['native_callbacks'] == 0 and not metrics['mismatches']
metrics['source_sha256'] = {name: hashlib.sha256((Path('/workspace/beamo-wipe') / name).read_bytes()).hexdigest()
                            for name in ['src/beamo_wipe/support_export.py', 'src/beamo_wipe/diagnostic_report.py',
                                         'src/beamo_wipe/evidence.py', 'src/beamo_wipe/result_summary.py',
                                         'src/beamo_wipe/privacy.py', 'src/beamo_wipe/lang.py',
                                         'tests/test_result_presentations.py']}
(ROOT / 'bundle-readback-matrix.json').write_text(json.dumps(metrics, indent=2) + '\n')
print(json.dumps({key: value for key, value in metrics.items() if key != 'source_sha256'}))
