"""Preference ownership regressions with exact source and inert I/O boundaries.

These tests never open a production preference directory or real descriptor.
Existing report-intent tests retain actual-module file/snapshot coverage.
"""
from __future__ import annotations

import ast
from pathlib import Path
import stat
import sys
import types
from types import SimpleNamespace

import pytest


SOURCE = Path(__file__).resolve().parents[1] / 'src/beamo_wipe/report_intent.py'


class PreferenceRefusal(RuntimeError):
    pass


class Handles:
    def __init__(self, monkeypatch, *, payload=b'wanted\n'):
        self.payload = payload
        self.opened = []
        self.closed = []
        self.live = set()
        self.unlinked = []
        self.diagnostics = []
        self.faults = {}
        self.close_faults = {}
        self.member_present = True
        self.temporary_present = True
        self.foreign_temporary = False
        self.published = False
        self.written = b''
        self.read_offset = 0
        self.os = SimpleNamespace(
            open=self.open, close=self.close, fstat=self.fstat, stat=self.stat,
            read=self.read, pread=lambda *args:b'', write=self.write,
            fsync=lambda *args:None, replace=self.replace, unlink=self.unlink,
            getuid=lambda:1000,
        )
        for name in ('O_RDONLY', 'O_DIRECTORY', 'O_NOFOLLOW', 'O_NONBLOCK',
                     'O_RDWR', 'O_CREAT', 'O_EXCL'):
            setattr(self.os, name, 1)
        diagnostics = types.ModuleType('beamo_wipe.diagnostics')
        diagnostics.log_diag = lambda *args:self.diagnostics.append(args)
        if 'beamo_wipe' not in sys.modules:
            package = types.ModuleType('beamo_wipe')
            package.__path__ = []
            monkeypatch.setitem(sys.modules, 'beamo_wipe', package)
        monkeypatch.setitem(sys.modules, 'beamo_wipe.diagnostics', diagnostics)
        tree = ast.parse(SOURCE.read_bytes())
        selected = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))]
        future = ast.parse('from __future__ import annotations').body
        namespace = dict(os=self.os, stat=stat, Path=Path, SafetyError=PreferenceRefusal,
                         default_log_dir=lambda:Path('/inert/preference'),
                         secrets=SimpleNamespace(token_hex=self.token))
        module = ast.fix_missing_locations(ast.Module(body=future + selected, type_ignores=[]))
        # Execute only checked-in AST definitions with fake descriptor operations.
        exec(compile(module, str(SOURCE), 'exec'), namespace)  # noqa: S102 - checked-in AST, inert preference I/O
        self.store = namespace['ReportIntentStore'](Path('/inert/preference'))
        self.store._verify_directory = lambda fd:self.fail('verify_directory')
        self.store._verify_publication = lambda *args:self.fail('verify_publication')
        self.factory = self.store._directory_fd
        self.store._directory_fd = self.acquire_directory

    def fail(self, stage):
        if stage in self.faults:
            raise self.faults[stage]

    def invoke(self, method):
        if method == 'factory':
            return self.factory()
        if method == 'save':
            return self.store.save(True)
        return self.store.load()

    def acquire(self, fd):
        self.opened.append(fd)
        self.live.add(fd)
        return fd

    def acquire_directory(self):
        self.fail('directory_open')
        return self.acquire(17)

    def open(self, name, flags, *args, **kwargs):
        if isinstance(name, Path):
            return self.acquire_directory()
        self.fail('file_open')
        if name == 'report-intent' and not self.member_present:
            raise FileNotFoundError(name)
        return self.acquire(18)

    def close(self, fd):
        assert fd in self.live, 'cleanup retried or closed an unowned handle'
        self.closed.append(fd)
        # A close failure models the attempted boundary; real kernel state after
        # close errors is deliberately not inferred or tested by this adapter.
        self.live.remove(fd)
        if fd in self.close_faults:
            raise self.close_faults[fd]

    def fstat(self, fd):
        assert fd in self.live
        self.fail('fstat')
        return SimpleNamespace(st_mode=(stat.S_IFDIR | 0o700) if fd == 17 else (stat.S_IFREG | 0o600),
            st_uid=1000, st_nlink=1, st_dev=1, st_ino=fd, st_size=len(self.payload),
            st_mtime_ns=11, st_ctime_ns=12)

    def stat(self, name, **kwargs):
        self.fail('stat')
        if name.startswith('.report-intent-') and not self.temporary_present:
            raise FileNotFoundError(name)
        snapshot = self.fstat(18)
        if name.startswith('.report-intent-') and self.foreign_temporary:
            snapshot.st_ino = 99
        return snapshot

    def token(self, count):
        assert count == 12
        self.fail('token')
        return 'opaque'

    def read(self, fd, count):
        assert fd in self.live
        self.fail('read')
        chunk = self.payload[self.read_offset:self.read_offset + count]
        self.read_offset += len(chunk)
        return chunk

    def write(self, fd, data):
        assert fd in self.live
        self.fail('write')
        self.written += data
        return len(data)

    def replace(self, source, target, **kwargs):
        self.fail('replace')
        assert source.startswith('.report-intent-') and target == 'report-intent'
        self.temporary_present = False
        self.published = True

    def unlink(self, name, **kwargs):
        self.fail('unlink')
        assert 18 in self.live, 'temporary identity must remain pinned'
        self.unlinked.append(name)
        self.temporary_present = False


PRIMARY_TYPES = (OSError, PreferenceRefusal, ValueError, KeyboardInterrupt, SystemExit)


@pytest.mark.parametrize('method,stage', [('factory', 'fstat'), ('load', 'read'), ('save', 'write')])
@pytest.mark.parametrize('error_type', PRIMARY_TYPES)
@pytest.mark.parametrize('close_type', [OSError, KeyboardInterrupt, SystemExit])
def test_primary_error_survives_every_owned_close(monkeypatch, method, stage, error_type, close_type):
    handles = Handles(monkeypatch)
    primary = error_type('inert primary with private details')
    handles.faults[stage] = primary
    handles.close_faults = {17:close_type('directory detail'), 18:close_type('file detail')}
    with pytest.raises(error_type) as captured:
        handles.invoke(method)
    assert captured.value is primary
    assert handles.closed == ([17] if method == 'factory' else [18, 17])
    assert not handles.live
    assert all('detail' not in word for row in handles.diagnostics for word in row)


@pytest.mark.parametrize('error_type', [OSError, ValueError, KeyboardInterrupt, SystemExit])
def test_token_failure_releases_directory(monkeypatch, error_type):
    handles = Handles(monkeypatch)
    primary = error_type('token source failed')
    handles.faults['token'] = primary
    with pytest.raises(error_type) as captured:
        handles.store.save(True)
    assert captured.value is primary
    assert handles.opened == handles.closed == [17]
    assert not handles.live and not handles.unlinked


@pytest.mark.parametrize('method,slot,value', [
    ('factory', 'fd', 17), ('load', 'directory', 17), ('load', 'fd', 18),
    ('save', 'directory', 17), ('save', 'fd', 18),
])
def test_post_acquisition_interrupt_releases_owned_handles(monkeypatch, method, slot, value):
    handles = Handles(monkeypatch)
    fn = handles.factory if method == 'factory' else getattr(handles.store, method)
    code = fn.__func__.__code__
    primary = KeyboardInterrupt('line-event interruption')
    injected = []
    previous = sys.gettrace()

    def trace(frame, event, _arg):
        if frame.f_code is code and event == 'line' and frame.f_locals.get(slot) == value and not injected:
            injected.append(frame.f_lineno)
            raise primary
        return trace

    try:
        sys.settrace(trace)
        with pytest.raises(KeyboardInterrupt) as captured:
            fn(True) if method == 'save' else fn()
        assert captured.value is primary
    finally:
        sys.settrace(previous)
    assert sys.gettrace() is previous and len(injected) == 1
    assert handles.opened == list(reversed(handles.closed))
    assert not handles.live
    if method == 'save' and slot == 'fd':
        assert handles.unlinked == ['.report-intent-opaque']


@pytest.mark.parametrize('failed_fd', [17, 18])
@pytest.mark.parametrize('error_type', [OSError, KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize('method', ['load', 'save'])
def test_standalone_close_failure_is_visible_after_other_closes(monkeypatch, failed_fd, error_type, method):
    handles = Handles(monkeypatch)
    error = error_type('inert close failure')
    handles.close_faults[failed_fd] = error
    with pytest.raises(error_type) as captured:
        handles.store.save(False) if method == 'save' else handles.store.load()
    assert captured.value is error
    assert handles.closed == [18, 17] and not handles.live


@pytest.mark.parametrize('wanted', [True, False])
def test_normal_load_and_save_keep_preference_semantics(monkeypatch, wanted):
    payload = b'wanted\n' if wanted else b'not-wanted\n'
    handles = Handles(monkeypatch, payload=payload)
    assert handles.store.load() is wanted
    assert handles.closed == [18, 17] and not handles.live
    handles = Handles(monkeypatch, payload=payload)
    handles.store.save(wanted)
    assert handles.written == payload and handles.published
    assert handles.closed == [18, 17] and not handles.live
    assert not handles.unlinked


def test_missing_preference_is_false_but_missing_directory_is_an_error(monkeypatch):
    handles = Handles(monkeypatch)
    handles.member_present = False
    assert handles.store.load() is False
    assert handles.closed == [17]
    handles = Handles(monkeypatch)
    error = FileNotFoundError('missing private directory')
    handles.faults['directory_open'] = error
    with pytest.raises(FileNotFoundError) as captured:
        handles.store.load()
    assert captured.value is error
    assert not handles.closed and not handles.opened


@pytest.mark.parametrize('payload', [b'', b'yes\n', b'wanted\ntrailing', b'x' * 40])
def test_invalid_preference_still_refuses_and_closes(monkeypatch, payload):
    handles = Handles(monkeypatch, payload=payload)
    with pytest.raises(PreferenceRefusal):
        handles.store.load()
    assert handles.closed == [18, 17] and not handles.live


@pytest.mark.parametrize('foreign,missing', [(True, False), (False, True)])
def test_failed_save_preserves_foreign_or_missing_temporary(monkeypatch, foreign, missing):
    handles = Handles(monkeypatch)
    error = OSError('body failure')
    handles.faults['write'] = error
    handles.foreign_temporary = foreign
    handles.temporary_present = not missing
    with pytest.raises(OSError) as captured:
        handles.store.save(True)
    assert captured.value is error
    assert not handles.unlinked
    assert handles.closed == [18, 17] and not handles.live


def test_temporary_cleanup_failure_cannot_skip_both_closes(monkeypatch):
    handles = Handles(monkeypatch)
    error = KeyboardInterrupt('operation interrupted')
    handles.faults.update(write=error, unlink=OSError('cleanup failed'))
    handles.close_faults = {18:OSError('file close'), 17:SystemExit('directory close')}
    with pytest.raises(KeyboardInterrupt) as captured:
        handles.store.save(True)
    assert captured.value is error
    assert handles.closed == [18, 17] and not handles.live
