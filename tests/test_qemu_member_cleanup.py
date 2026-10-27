"""QEMU member ownership; fake descriptors and exact reader source only."""
from __future__ import annotations

from collections import Counter
import hashlib
import sys

from test_build_reader_cleanup import ReaderOS, load_reader_ast


def _capture(call):
    try:
        return call(), None
    except BaseException as exc:
        return None, exc


def _retired(fs):
    assert not fs.live, fs.live
    attempts = Counter(e['fd'] for e in fs.events if e['op'] == 'close-attempt')
    assert attempts == Counter({fd: 1 for fd in fs.acquired}), fs.events


def _primary_case(primary_type, cleanup_type):
    fs = ReaderOS()
    env = load_reader_ast('ci_evidence', fs)
    primary = primary_type('inert member read refusal')
    cleanup = cleanup_type('inert member close refusal')
    fs.fault('read', '/a/b/item', primary)
    fs.fault('close', '/a/b/item', cleanup, after=('read', '/a/b/item'))
    value, error = _capture(lambda: env['qemu_evidence_hashes'](fs.Path('/a/b')))
    assert value is None
    assert error is primary or (error is not None and error.__cause__ is primary)
    _retired(fs)


def test_qemu_member_cleanup_preserves_the_read_failure():
    for primary in (RuntimeError, OSError, KeyboardInterrupt, SystemExit):
        for cleanup in (OSError, KeyboardInterrupt, SystemExit):
            _primary_case(primary, cleanup)


def _acquisition_case(error_type):
    fs = ReaderOS()
    env = load_reader_ast('ci_evidence', fs)
    primary = error_type('inert post-open cancellation')
    owners = {env['qemu_evidence_hashes'].__code__, env['_hash_regular_at'].__code__}
    previous = sys.gettrace()
    injected = []

    def trace(frame, event, arg):
        if previous:
            previous(frame, event, arg)
        if (frame.f_code in owners and event == 'line' and not injected
                and any(path == '/a/b/item' for path, _offset in fs.live.values())):
            injected.append(frame.f_lineno)
            raise primary
        return trace

    try:
        sys.settrace(trace)
        value, error = _capture(lambda: env['qemu_evidence_hashes'](fs.Path('/a/b')))
    finally:
        sys.settrace(previous)
    assert injected
    assert value is None and error is primary
    _retired(fs)


def test_qemu_member_acquisition_is_inside_its_cleanup_scope():
    for error_type in (KeyboardInterrupt, SystemExit):
        _acquisition_case(error_type)


def _close_case(cleanup_type):
    fs = ReaderOS()
    env = load_reader_ast('ci_evidence', fs)
    cleanup = cleanup_type('inert close-only refusal') if cleanup_type else None
    if cleanup is not None:
        fs.fault('close', '/a/b/item', cleanup)
    value, error = _capture(lambda: env['qemu_evidence_hashes'](fs.Path('/a/b')))
    if cleanup is None:
        assert error is None and value == {'item': hashlib.sha256(b'abc\n').hexdigest()}
    else:
        assert value is None
        assert error is cleanup or (error is not None and error.__cause__ is cleanup)
    _retired(fs)


def test_qemu_member_digest_and_standalone_close_controls():
    for cleanup_type in (None, OSError, KeyboardInterrupt, SystemExit):
        _close_case(cleanup_type)


def _aba_case():
    fs = ReaderOS()
    env = load_reader_ast('ci_evidence', fs)
    original = dict(fs.nodes['/a/b/item'])
    replacement = {**original, 'st_ino': original['st_ino'] + 1, 'data': b'xyz\n'}
    real_open, real_close = fs.open, fs.close

    def open_member(path, flags, mode=0o644, *, dir_fd=None):
        if fs.key(path, dir_fd) == '/a/b/item':
            fs.nodes['/a/b/item'] = dict(replacement)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    def close_member(fd):
        member = fs.live[fd][0] == '/a/b/item'
        real_close(fd)
        if member:
            fs.nodes['/a/b/item'] = dict(original)

    fs.open, fs.close = open_member, close_member
    value, error = _capture(lambda: env['qemu_evidence_hashes'](fs.Path('/a/b')))
    assert value is None and isinstance(error, RuntimeError)
    assert 'QEMU evidence' in str(error)
    _retired(fs)


def test_qemu_member_directory_recheck_uses_the_hashed_inode():
    # A -> B at open, then A again at close, with unchanged directory clocks.
    # A pathname stat taken before opening must not authenticate B's digest.
    _aba_case()
