"""Fresh owned-file completion snapshot/epoch matrix; no engine or devices."""
from pathlib import Path
import hashlib
import itertools
import json
import os
import tempfile
from unittest.mock import patch

from beamo_wipe import nwipe_runner as m
from beamo_wipe.methods import METHODS
from beamo_wipe.models import MethodId


ROOT = Path(__file__).parent
TARGET = '/dev/FAKEDATA'
PREFIX = '[2026/10/21 00:30:00] info: '
counts = {'cases': 0, 'positive_completed_controls': 0, 'refusal_controls': 0,
          'cut_tail_cases': 0, 'concurrent_append_scans': 0, 'bounded_scan_bytes': 0,
          'native_callbacks': 0, 'mismatches': []}
original_realpath = os.path.realpath
original_open = os.open
original_fdopen = os.fdopen


def forbidden(*args, **kwargs):
    counts['native_callbacks'] += 1
    raise AssertionError('Native process, signal or device action forbidden')


def fake_realpath(path, *args, **kwargs):
    if os.fsdecode(path).startswith('/dev/'):
        return os.fspath(path)
    return original_realpath(path, *args, **kwargs)


def guarded_open(path, *args, **kwargs):
    if not isinstance(path, int) and os.fsdecode(path).startswith(('/dev/', '/proc/', '/sys/')):
        return forbidden(path)
    return original_open(path, *args, **kwargs)


def proof(method, style, native):
    count = METHODS[method].overwrite_passes
    phase = 'writing' if method == MethodId.QUICK_ZERO else 'verifying'
    if style == 'progress':
        line = f'{TARGET}: 100.00%, round 1 of 1, pass {count} of {count}, eta 00:00:00, [{phase}]\n'
        terminal = (PREFIX if native else '') + line
    else:
        terminal = m.NWIPE_DRIVE_STATUS_HEADER + '\nFAKEDATA | Erased | 120MB/s | 01:25:04 | fake model\n'
    return ((PREFIX + 'Program options are set as follows\n') if native else '') + terminal


class GrowingScan:
    def __init__(self, stream, path):
        self.stream, self.path = stream, path
        self.grew = False
        self.bytes = 0

    def __enter__(self):
        self.stream.__enter__()
        return self

    def __exit__(self, *args):
        return self.stream.__exit__(*args)

    def fileno(self):
        return self.stream.fileno()

    def readline(self, limit):
        if not self.grew:
            self.grew = True
            with self.path.open('ab') as writer:
                writer.write(b'concurrent fake append\n')
        data = self.stream.readline(limit)
        self.bytes += len(data)
        return data


epochs = ('stable', 'replacement-before-tail', 'replacement-before-scan',
          'append-before-scan', 'truncate-before-scan', 'symlink-before-tail',
          'fifo-before-tail', 'append-during-scan')
with patch.object(os.path, 'realpath', fake_realpath), patch.object(os, 'open', guarded_open), \
     patch.object(m.subprocess, 'run', forbidden), patch.object(m.subprocess, 'Popen', forbidden), \
     patch.object(os, 'kill', forbidden), patch('beamo_wipe.diagnostics.log_diag', lambda *a, **kw: None):
    for method, style, native, payload_width, epoch in itertools.product(
            list(MethodId), ('progress', 'status'), (False, True),
            (0, 65534, 65535, 65536), epochs):
        counts['cases'] += 1
        with tempfile.TemporaryDirectory(prefix='pass10-snapshot-', dir=ROOT) as folder:
            directory = Path(folder)
            logfile = directory / 'owned.log'
            # Complete proof lies beyond the ordinary 1MiB tail. Every ordinary
            # filler record is exactly within the per-record scanner budget.
            data = (proof(method, style, native).encode()
                    + b'p' * payload_width + b'\n'
                    + (b'q' * 65535 + b'\n') * 18)
            assert len(data) > m.NWIPE_COMPLETION_LOG_BYTES
            logfile.write_bytes(data)
            logfile.chmod(0o600)
            before = logfile.stat()
            runner = m.NwipeRunner()
            runner._active_log_identity = (str(logfile), before.st_dev, before.st_ino)

            def replace():
                replacement = directory / 'replacement'
                replacement.write_bytes(data)
                logfile.rename(directory / 'retained-original')
                replacement.rename(logfile)

            if epoch == 'replacement-before-tail':
                replace()
            elif epoch in {'symlink-before-tail', 'fifo-before-tail'}:
                logfile.rename(directory / 'retained-original')
                if epoch == 'symlink-before-tail':
                    logfile.symlink_to(directory / 'retained-original')
                else:
                    os.mkfifo(logfile, 0o600)
            tail = runner._read_log_tail(str(logfile), m.NWIPE_COMPLETION_LOG_BYTES)
            identity = runner._log_read_state.identity
            counts['cut_tail_cases'] += bool(tail and runner._log_read_state.head_fragment)
            if epoch == 'replacement-before-scan':
                replace()
            elif epoch == 'append-before-scan':
                with logfile.open('ab') as writer:
                    writer.write(b'changed snapshot\n')
            elif epoch == 'truncate-before-scan':
                logfile.write_bytes(b'')
            scans = []
            if epoch == 'append-during-scan':
                def growing_fdopen(fd, *args, **kwargs):
                    stream = GrowingScan(original_fdopen(fd, *args, **kwargs), logfile)
                    scans.append(stream)
                    return stream
                with patch.object(os, 'fdopen', growing_fdopen):
                    projected = runner._scan_completion_log(str(logfile), TARGET, identity)
                assert len(scans) == 1 and scans[0].bytes <= before.st_size
                counts['concurrent_append_scans'] += 1
                counts['bounded_scan_bytes'] += scans[0].bytes
            else:
                projected = runner._scan_completion_log(str(logfile), TARGET, identity)
            expected = epoch == 'stable' and payload_width + 1 <= m.NWIPE_COMPLETION_SCAN_LINE_BYTES
            verdict = projected is not None and m.completion_for_method(0, projected, TARGET, method)[0]
            if verdict != expected:
                counts['mismatches'].append({'method': method.value, 'style': style,
                                             'native': native, 'payload_width': payload_width,
                                             'epoch': epoch, 'expected': expected,
                                             'projection_present': projected is not None,
                                             'actual': verdict})
            counts['positive_completed_controls'] += expected
            counts['refusal_controls'] += not expected

assert counts['cases'] == 384
assert counts['positive_completed_controls'] == 36 and counts['refusal_controls'] == 348
assert counts['native_callbacks'] == 0 and not counts['mismatches'], counts['mismatches'][:3]
counts['source_sha256'] = {name: hashlib.sha256((Path('/workspace/beamo-wipe') / name).read_bytes()).hexdigest()
                           for name in ('src/beamo_wipe/nwipe_runner.py', 'src/beamo_wipe/methods.py', 'src/beamo_wipe/models.py')}
counts['scope'] = 'Owned-file reader/scanner snapshot and epoch controls, separate from canonical tests and real-device acceptance.'
(ROOT / 'log-snapshot-epoch-matrix.json').write_text(json.dumps(counts, indent=2) + '\n')
print(json.dumps(counts))
