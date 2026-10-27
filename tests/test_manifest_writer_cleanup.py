"""Exact transaction AST with memory-only filesystem and fault boundaries.

These regressions exercise ownership and exception identity, not Linux syscalls.
No product module is imported and no transaction touches a real file descriptor.
"""
from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]


def load_ast(source, names, namespace):
    tree = ast.parse((ROOT / source).read_bytes())
    selected = [node for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
    assert {node.name for node in selected} == set(names)
    future = ast.parse('from __future__ import annotations').body
    tree = ast.fix_missing_locations(ast.Module(body=future + selected, type_ignores=[]))
    exec(compile(tree, source, 'exec'), namespace)  # noqa: S102 - exact checked-in AST, memory I/O


class MemoryNode:
    def __init__(self, inode, data, mode):
        self.inode, self.data, self.mode = inode, bytes(data), mode

    def info(self):
        return SimpleNamespace(st_dev=1, st_ino=self.inode, st_mode=self.mode,
                               st_uid=7, st_nlink=1, st_size=len(self.data),
                               st_mtime_ns=10, st_ctime_ns=11)


class MemoryPath(PurePosixPath):
    store = None

    def mkdir(self, **kwargs):
        self.store.directories.add(str(self))

    def lstat(self):
        return self.store.node(self).info()

    def is_symlink(self):
        return str(self) in self.store.files and stat.S_ISLNK(self.store.node(self).mode)


class MemoryFS:
    O_RDONLY, O_RDWR, O_CREAT, O_EXCL = 1, 2, 4, 8
    O_NOFOLLOW, O_DIRECTORY = 16, 32

    def __init__(self):
        self.files, self.fds, self.roles = {}, {}, {}
        self.directories = {'/root', '/root/dist'}
        self.opened, self.closed, self.events = [], [], []
        self.faults, self.close_faults = {}, {}
        self.next_inode, self.next_fd, self.token_number = 100, 10, 0
        self.before_rename = None
        self.environ = {}
        self.path = SimpleNamespace(basename=lambda value: MemoryPath(value).name)
        MemoryPath.store = self

    def fail(self, stage):
        if stage in self.faults:
            raise self.faults[stage]

    def key(self, path, dir_fd=None):
        text = str(path)
        if text.startswith('/'):
            return text
        assert dir_fd in self.fds
        return str(MemoryPath(self.fds[dir_fd]) / text)

    def node(self, path):
        if str(path) not in self.files:
            raise FileNotFoundError(str(path))
        return self.files[str(path)]

    def put(self, path, data, mode=stat.S_IFREG | 0o600):
        self.next_inode += 1
        node = MemoryNode(self.next_inode, data, mode)
        self.files[str(path)] = node
        return node

    def open(self, path, flags, mode=0o600, *, dir_fd=None):
        key = self.key(path, dir_fd)
        if flags & self.O_DIRECTORY:
            self.fail('directory_open')
            assert key in self.directories
            node, role = key, 'directory'
        elif flags & self.O_CREAT:
            self.fail('stage_open')
            if key in self.files and flags & self.O_EXCL:
                raise FileExistsError(key)
            node, role = self.put(key, b'', stat.S_IFREG | mode), 'stage'
        else:
            node, role = self.node(key), 'read'
            assert not flags & self.O_NOFOLLOW or not stat.S_ISLNK(node.mode)
        self.next_fd += 1
        self.fds[self.next_fd], self.roles[self.next_fd] = node, role
        self.opened.append(self.next_fd)
        self.events.append(('open', self.next_fd, role))
        return self.next_fd

    def close(self, fd):
        assert fd in self.fds, ('unowned/retried close', fd)
        self.closed.append(fd)
        del self.fds[fd]
        self.events.append(('close', fd, self.roles[fd]))
        # Model one attempted close that releases its number before a delayed
        # error. This makes retries unsafe; no kernel guarantee is inferred.
        if self.roles[fd] in self.close_faults:
            raise self.close_faults[self.roles[fd]]

    def token(self, count):
        assert count == 16
        self.fail('token')
        self.token_number += 1
        return f'{self.token_number:032x}'

    def write(self, fd, value):
        self.fail('write')
        self.fds[fd].data += bytes(value)
        return len(value)

    def pread(self, fd, count, offset):
        return self.fds[fd].data[offset:offset + count]

    def fstat(self, fd):
        return self.fds[fd].info()

    def fsync(self, fd):
        assert fd in self.fds
        self.fail('fsync_' + self.roles[fd])

    def getuid(self):
        return 7

    def readlink(self, path):
        return self.node(path).data.decode('ascii')

    def rename(self, source_fd, source, target_fd, target, flags):
        first, second = self.key(source, source_fd), self.key(target, target_fd)
        if self.before_rename is not None:
            callback, self.before_rename = self.before_rename, None
            callback(second)
        if flags == 1:
            if second in self.files:
                raise FileExistsError(second)
            self.files[second] = self.files.pop(first)
        elif flags == 2:
            assert first in self.files and second in self.files
            self.files[first], self.files[second] = self.files[second], self.files[first]
        else:
            raise AssertionError(flags)
        self.events.append(('rename', flags, first, second))


def make_rm(fs):
    namespace = dict(Path=MemoryPath, os=fs, stat=stat, hashlib=hashlib,
                     dataclass=dataclasses.dataclass, json=json, re=re,
                     secrets=SimpleNamespace(token_hex=fs.token), _CAPTURE_CURRENT=object(),
                     _SNAPSHOT_FIELDS=('st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_nlink',
                                       'st_size', 'st_mtime_ns', 'st_ctime_ns'),
                     MAX_MANIFEST_BYTES=16 * 1024 * 1024, _RENAME_NOREPLACE=1,
                     _RENAME_EXCHANGE=2, _renameat2=fs.rename, SCHEMA_VERSION=2,
                     __version__='0.2.14',
                     MANIFEST_NAME_TEMPLATE='beamo-wipe-{version}-amd64.manifest.json')
    namespace['_open_regular_nofollow'] = lambda path: fs.open(path, fs.O_RDONLY | fs.O_NOFOLLOW)
    namespace['sha256_file_with_stat'] = lambda path: (
        hashlib.sha256(fs.node(path).data).hexdigest(), len(fs.node(path).data))
    namespace['sha256_file'] = lambda path: hashlib.sha256(fs.node(path).data).hexdigest()
    load_ast('src/beamo_wipe/release_manifest.py', (
        '_close_reader_fds',
        '_OutputSnapshot', '_stat_fields', '_regular_fd_snapshot', '_regular_output_snapshot',
        '_regular_snapshot_bytes', '_path_snapshot', '_snapshot_matches', '_snapshot_digest',
        '_atomic_write', '_prior_output_bytes', '_sidecar_blob', '_unique_manifest_fields',
        'require_verified_prior_checksum_list'), namespace)
    return namespace


def capture(call):
    try:
        call()
    except BaseException as error:
        return error
    return None


def writer_case(*, existing=False, identical=False):
    fs = MemoryFS()
    rm = make_rm(fs)
    path = MemoryPath('/root/dist/output')
    if existing:
        fs.put(path, b'new' if identical else b'old')
    expected = rm['_path_snapshot'](path, 16)
    return fs, rm, path, expected


def assert_closed(fs):
    assert not fs.fds
    assert sorted(fs.opened) == sorted(fs.closed)
    assert len(fs.closed) == len(set(fs.closed)), 'descriptor close retried'


def test_writer_acquisition_failures_release_every_owned_handle():
    for stage in ('directory_open', 'token', 'stage_open'):
        for error_type in (OSError, KeyboardInterrupt, SystemExit):
            fs, rm, path, expected = writer_case()
            primary = error_type(stage)
            fs.faults[stage] = primary
            fs.close_faults['directory'] = SystemExit('secondary directory close')
            error = capture(lambda: rm['_atomic_write'](path, b'new', expected=expected))
            assert error is primary
            assert_closed(fs)


def test_writer_preserves_primary_error_through_all_owned_closes():
    for fast in (False, True):
        for error_type in (OSError, KeyboardInterrupt, SystemExit):
            for close_type in (OSError, KeyboardInterrupt, SystemExit):
                fs, rm, path, expected = writer_case(existing=fast, identical=fast)
                primary = error_type('primary operation')
                fs.faults['fsync_directory' if fast else 'write'] = primary
                fs.close_faults = {'stage': close_type('file close'),
                                   'directory': close_type('directory close')}
                error = capture(lambda: rm['_atomic_write'](path, b'new', expected=expected))
                assert error is primary
                assert_closed(fs)
                assert fs.roles[fs.closed[-1]] == 'directory'
                if not fast:
                    assert fs.roles[fs.closed[-2]] == 'stage'


def test_writer_standalone_cleanup_errors_remain_visible():
    for fast, role in ((False, 'stage'), (False, 'directory'), (True, 'directory')):
        for error_type in (OSError, KeyboardInterrupt, SystemExit):
            fs, rm, path, expected = writer_case(existing=fast, identical=fast)
            error = error_type('standalone close')
            fs.close_faults[role] = error
            assert capture(lambda: rm['_atomic_write'](path, b'new', expected=expected)) is error
            assert fs.node(path).data == b'new'
            assert_closed(fs)


def test_writer_first_cleanup_error_visible_after_both_attempts():
    fs, rm, path, expected = writer_case()
    first = KeyboardInterrupt('first close')
    fs.close_faults = {'stage': first, 'directory': SystemExit('second close')}
    assert capture(lambda: rm['_atomic_write'](path, b'new', expected=expected)) is first
    assert_closed(fs)
    assert [fs.roles[fd] for fd in fs.closed[-2:]] == ['stage', 'directory']


def test_writer_uses_operation_local_primary_inside_an_outer_exception():
    fs, rm, path, expected = writer_case()
    error = OSError('standalone close inside an outer handler')
    fs.close_faults['directory'] = error
    try:
        raise ValueError('unrelated active exception')
    except ValueError:
        assert capture(lambda: rm['_atomic_write'](path, b'new', expected=expected)) is error
    assert_closed(fs)


def test_writer_post_acquisition_interrupts_close_once():
    for slot in ('dirfd', 'fd'):
        fs, rm, path, expected = writer_case()
        writer = rm['_atomic_write']
        primary = KeyboardInterrupt('after owned acquisition')
        injected = []
        previous_trace = sys.gettrace()

        def trace(frame, event, _arg):
            if (frame.f_code is writer.__code__ and event == 'line'
                    and frame.f_locals.get(slot, -1) >= 0 and not injected):
                injected.append(frame.f_lineno)
                raise primary
            return trace

        try:
            sys.settrace(trace)
            error = capture(lambda: writer(path, b'new', expected=expected))
        finally:
            sys.settrace(previous_trace)
        assert error is primary and len(injected) == 1
        assert_closed(fs)


def test_writer_normal_absent_replacement_and_identical_controls():
    for existing, identical in ((False, False), (True, False), (True, True)):
        fs, rm, path, expected = writer_case(existing=existing, identical=identical)
        prior = fs.files.get(str(path))
        rm['_atomic_write'](path, b'new', expected=expected)
        assert fs.node(path).data == b'new'
        if existing and not identical:
            assert any(node is prior and name != str(path) for name, node in fs.files.items())
        if identical:
            assert not any(event[0] == 'rename' for event in fs.events)
        assert_closed(fs)


def test_writer_collision_restores_foreign_entry_and_retains_staging():
    for existing in (False, True):
        for link in (False, True):
            fs, rm, path, expected = writer_case(existing=existing)
            foreign = []

            def collide(name):
                foreign.append(fs.put(name, b'/root/sentinel' if link else b'foreign',
                                      stat.S_IFLNK | 0o777 if link else stat.S_IFREG | 0o600))

            fs.before_rename = collide
            error = capture(lambda: rm['_atomic_write'](path, b'new', expected=expected))
            assert isinstance(error, RuntimeError if existing else FileExistsError)
            assert fs.node(path) is foreign[0]
            retained = [name for name, node in fs.files.items() if node.data == b'new']
            assert len(retained) == 1 and retained[0] != str(path)
            assert hashlib.sha256(b'new').hexdigest() in retained[0]
            if existing:
                assert len([event for event in fs.events if event[0] == 'rename']) == 2
            assert_closed(fs)


def test_writer_initial_symlink_replacement_retains_link_and_target():
    fs, rm, path, _expected = writer_case()
    target = fs.put('/root/sentinel', b'preserve target')
    link = fs.put(path, b'/root/sentinel', stat.S_IFLNK | 0o777)
    expected = rm['_path_snapshot'](path, 16, allow_symlink=True)
    rm['_atomic_write'](path, b'new', expected=expected)
    assert fs.node('/root/sentinel') is target and target.data == b'preserve target'
    assert fs.node(path).data == b'new' and stat.S_ISREG(fs.node(path).mode)
    assert len([node for node in fs.files.values() if node is link]) == 1
    assert_closed(fs)
